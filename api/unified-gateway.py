#!/usr/bin/env python3
"""
Unified API Gateway for HubNode Services
Centralized API gateway for all services - accessible via api.* domains and IP
Provides routing, authentication, and health monitoring
"""

import os
import json
import time
import sqlite3
import hashlib
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from functools import wraps
import logging

app = Flask(__name__)
CORS(app)

# Configuration
GATEWAY_PORT = 5015
DB_PATH = "/home/devinecr/apps/hubnode/api/gateway.db"
LOG_FILE = "/var/log/api-gateway.log"
API_KEYS_FILE = "/home/devinecr/apps/hubnode/api/api_keys.json"

# Service Registry
SERVICES = {
    "monitor": {
        "name": "Service Monitor",
        "url": "http://localhost:5003",
        "prefix": "/monitor",
        "health_endpoint": "/health",
        "description": "System service monitoring",
        "admin_only": False
    },
    "logs": {
        "name": "User Logs Collector",
        "url": "http://localhost:5002",
        "prefix": "/logs",
        "health_endpoint": "/health",
        "description": "App logs and analytics",
        "admin_only": False
    },
    "audio-portrait": {
        "name": "Audio Portrait API",
        "url": "http://localhost:5001",
        "prefix": "/audio-portrait",
        "health_endpoint": "/api/audio-portrait/health",
        "description": "Audio Portrait app services",
        "admin_only": False
    },
    "copyparty": {
        "name": "CopyParty Management API",
        "url": "http://localhost:5016",
        "prefix": "/copyparty",
        "health_endpoint": "/api/copyparty/health",
        "description": "CopyParty file server management with admin controls",
        "admin_only": False
    },
    "services": {
        "name": "Services Manager",
        "url": "http://localhost:5017",
        "prefix": "/services",
        "health_endpoint": "/api/services/health",
        "description": "Docker, Jellyfin, Icecast, TeamTalk, and system services management",
        "admin_only": False
    },
    "webhooks": {
        "name": "Webhook Manager",
        "url": "http://localhost:5004",
        "prefix": "/webhooks",
        "health_endpoint": "/health",
        "description": "External webhook integrations",
        "admin_only": True
    },
    "mastodon": {
        "name": "Mastodon Social Network",
        "url": "http://localhost:3001",
        "prefix": "/mastodon",
        "health_endpoint": "/health",
        "description": "Mastodon federated social network instance (md.tappedin.fm)",
        "admin_only": False
    },
    "mattermost": {
        "name": "Mattermost Team Chat",
        "url": "http://localhost:8065",
        "prefix": "/mattermost",
        "health_endpoint": "/api/v4/system/ping",
        "description": "Mattermost team collaboration platform (chat.tappedin.fm)",
        "admin_only": False
    },
    "mastodon-bridge": {
        "name": "Mastodon Bridge Bot",
        "url": "http://localhost:5019",
        "prefix": "/mastodon-bridge",
        "health_endpoint": "/health",
        "description": "Mastodon to Discord/Mattermost announcement bridge bot",
        "admin_only": False
    },
    "flexpbx": {
        "name": "FlexPBX Master API",
        "url": "http://localhost:5018",
        "prefix": "/flexpbx",
        "health_endpoint": "/health",
        "description": "Master FlexPBX Server API - Extensions, Trunks, Call Logs, Voicemail, System",
        "admin_only": False
    },
    "headscale": {
        "name": "Headscale Control Server",
        "url": "http://localhost:8080",
        "prefix": "/headscale",
        "health_endpoint": "/health",
        "description": "Headscale VPN control server and API (headscale.tappedin.fm)",
        "admin_only": False
    },
    "tailscale": {
        "name": "Tailscale UI",
        "url": "https://tailscale.tappedin.fm",
        "prefix": "/tailscale",
        "health_endpoint": "/api/nodes",
        "description": "Tailscale VPN dashboard and management UI",
        "admin_only": False
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize gateway database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # API Keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            key_name TEXT NOT NULL,
            app_name TEXT,
            permissions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            active BOOLEAN DEFAULT 1
        )
    ''')

    # Request logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            api_key_id INTEGER,
            service TEXT,
            endpoint TEXT,
            method TEXT,
            ip_address TEXT,
            user_agent TEXT,
            status_code INTEGER,
            response_time REAL
        )
    ''')

    # Service health table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            service_name TEXT,
            status TEXT,
            response_time REAL,
            error_message TEXT
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized")

def load_api_keys():
    """Load API keys from file or generate default"""
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)

    # Generate default keys
    default_keys = {
        "master": {
            "key": "gateway-master-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
            "permissions": ["all"],
            "description": "Master API key with full access"
        },
        "pbx": {
            "key": "pbx-access-" + hashlib.sha256(str(time.time() + 1).encode()).hexdigest()[:16],
            "permissions": ["monitor", "logs", "audio-portrait", "services"],
            "description": "FlexPBX and external apps key - read access to services"
        },
        "admin": {
            "key": "admin-services-" + hashlib.sha256(str(time.time() + 2).encode()).hexdigest()[:16],
            "permissions": ["all"],
            "description": "Admin key for service management"
        },
        "copyparty": {
            "key": "copyparty-mgmt-" + hashlib.sha256(str(time.time() + 3).encode()).hexdigest()[:16],
            "permissions": ["copyparty", "monitor", "logs"],
            "description": "CopyParty management access"
        }
    }

    with open(API_KEYS_FILE, 'w') as f:
        json.dump(default_keys, f, indent=2)

    os.chmod(API_KEYS_FILE, 0o600)
    logger.info(f"Generated default API keys: {API_KEYS_FILE}")
    return default_keys

def verify_api_key(api_key):
    """Verify API key and return permissions"""
    keys = load_api_keys()

    for key_name, key_data in keys.items():
        if key_data["key"] == api_key:
            # Update last used timestamp in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            cursor.execute('''
                INSERT OR IGNORE INTO api_keys (key_hash, key_name, permissions)
                VALUES (?, ?, ?)
            ''', (key_hash, key_name, json.dumps(key_data["permissions"])))

            cursor.execute('''
                UPDATE api_keys SET last_used = CURRENT_TIMESTAMP
                WHERE key_hash = ?
            ''', (key_hash,))

            conn.commit()
            conn.close()

            return key_data["permissions"]

    return None

def require_api_key(allowed_services=None):
    """Decorator to require API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

            if not api_key:
                return jsonify({"error": "API key required"}), 401

            permissions = verify_api_key(api_key)
            if not permissions:
                return jsonify({"error": "Invalid API key"}), 401

            # Check permissions
            if allowed_services and "all" not in permissions:
                if not any(service in permissions for service in allowed_services):
                    return jsonify({"error": "Insufficient permissions"}), 403

            request.api_permissions = permissions
            return f(*args, **kwargs)

        return decorated_function
    return decorator

def log_request(service, endpoint, status_code, response_time):
    """Log API request"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO request_logs
            (service, endpoint, method, ip_address, user_agent, status_code, response_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            service, endpoint, request.method,
            request.remote_addr, request.headers.get('User-Agent', ''),
            status_code, response_time
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging request: {e}")

def check_service_health(service_name, service_config):
    """Check health of a backend service"""
    try:
        url = service_config["url"] + service_config["health_endpoint"]
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = time.time() - start_time

        status = "healthy" if response.status_code == 200 else "unhealthy"

        # Log to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO service_health (service_name, status, response_time)
            VALUES (?, ?, ?)
        ''', (service_name, status, response_time))
        conn.commit()
        conn.close()

        return {
            "status": status,
            "response_time": response_time,
            "http_status": response.status_code
        }
    except Exception as e:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO service_health (service_name, status, error_message)
            VALUES (?, ?, ?)
        ''', (service_name, "error", str(e)))
        conn.commit()
        conn.close()

        return {
            "status": "error",
            "error": str(e)
        }

def proxy_request(service_config, path):
    """Proxy request to backend service"""
    try:
        # Build target URL
        target_url = service_config["url"] + path

        # Prepare headers (remove host header)
        headers = {k: v for k, v in request.headers if k.lower() != 'host'}

        # Make request to backend
        start_time = time.time()

        if request.method == 'GET':
            resp = requests.get(target_url, headers=headers, params=request.args, timeout=30)
        elif request.method == 'POST':
            resp = requests.post(target_url, headers=headers, data=request.get_data(),
                               params=request.args, timeout=30)
        elif request.method == 'PUT':
            resp = requests.put(target_url, headers=headers, data=request.get_data(),
                              params=request.args, timeout=30)
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, params=request.args, timeout=30)
        else:
            return jsonify({"error": "Method not supported"}), 405

        response_time = time.time() - start_time

        # Log request
        log_request(service_config["name"], path, resp.status_code, response_time)

        # Return proxied response
        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers)
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Service timeout"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({"error": "Internal gateway error"}), 500

# Routes

@app.route('/')
def index():
    """Gateway documentation"""
    return jsonify({
        "name": "HubNode Unified API Gateway",
        "version": "1.0.0",
        "server_ip": "64.20.46.178",
        "gateway_port": GATEWAY_PORT,
        "access": [
            f"https://api.devinecreations.net",
            f"https://api.devine-creations.net",
            f"http://64.20.46.178:{GATEWAY_PORT}"
        ],
        "services": {
            name: {
                "name": config["name"],
                "prefix": config["prefix"],
                "description": config["description"]
            } for name, config in SERVICES.items()
        },
        "authentication": {
            "method": "API Key",
            "header": "X-API-Key: your-api-key",
            "query_param": "?api_key=your-api-key"
        },
        "endpoints": {
            "/": "This documentation",
            "/health": "Gateway health check",
            "/services": "List all services and their health",
            "/keys": "Manage API keys (requires master key)",
            "/stats": "Gateway statistics (requires API key)",
            "/restart": "Restart API Gateway (requires master key)",
            "/<service_prefix>/*": "Proxy to backend service"
        }
    })

@app.route('/health')
def health():
    """Gateway health check"""
    return jsonify({
        "status": "healthy",
        "gateway": "online",
        "timestamp": datetime.now().isoformat(),
        "uptime": "N/A"
    })

@app.route('/services')
@require_api_key()
def list_services():
    """List all services and their health status"""
    services_status = {}

    for name, config in SERVICES.items():
        services_status[name] = {
            **config,
            "health": check_service_health(name, config)
        }

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "services": services_status
    })

@app.route('/keys', methods=['GET'])
@require_api_key(["all"])
def list_keys():
    """List all API keys (requires master key)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT key_name, permissions, created_at, last_used, active
        FROM api_keys
        ORDER BY created_at DESC
    ''')

    keys = []
    for row in cursor.fetchall():
        keys.append({
            "name": row[0],
            "permissions": json.loads(row[1]) if row[1] else [],
            "created_at": row[2],
            "last_used": row[3],
            "active": bool(row[4])
        })

    conn.close()

    return jsonify({"keys": keys})

@app.route('/stats')
@require_api_key()
def gateway_stats():
    """Get gateway statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Request counts by service
    cursor.execute('''
        SELECT service, COUNT(*) as count, AVG(response_time) as avg_time
        FROM request_logs
        WHERE timestamp > datetime('now', '-24 hours')
        GROUP BY service
    ''')
    service_stats = [{"service": r[0], "requests": r[1], "avg_response_time": r[2]}
                     for r in cursor.fetchall()]

    # Recent errors
    cursor.execute('''
        SELECT service_name, error_message, timestamp
        FROM service_health
        WHERE status = 'error' AND timestamp > datetime('now', '-1 hour')
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    recent_errors = [{"service": r[0], "error": r[1], "timestamp": r[2]}
                     for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "service_stats": service_stats,
        "recent_errors": recent_errors
    })

@app.route('/restart', methods=['POST'])
@require_api_key(["all"])
def restart_gateway():
    """Restart the API Gateway service (requires master key)"""
    import subprocess

    try:
        # Restart the systemd service
        result = subprocess.run(
            ['systemctl', 'restart', 'api-gateway.service'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "API Gateway service restart initiated",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to restart service",
                "error": result.stderr
            }), 500
    except Exception as e:
        logger.error(f"Restart error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Dynamic service routing
@app.route('/monitor', defaults={'path': ''})
@app.route('/monitor/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["monitor", "all"])
def route_monitor(path):
    """Route to service monitor API"""
    return proxy_request(SERVICES["monitor"], '/' + path)

@app.route('/logs', defaults={'path': ''})
@app.route('/logs/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["logs", "all"])
def route_logs(path):
    """Route to user logs collector"""
    return proxy_request(SERVICES["logs"], '/api/logs/' + path)

@app.route('/audio-portrait', defaults={'path': ''})
@app.route('/audio-portrait/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["audio-portrait", "all"])
def route_audio_portrait(path):
    """Route to audio portrait API"""
    return proxy_request(SERVICES["audio-portrait"], '/api/audio-portrait/' + path)

@app.route('/copyparty', defaults={'path': ''})
@app.route('/copyparty/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["copyparty", "all"])
def route_copyparty(path):
    """Route to CopyParty Management API"""
    return proxy_request(SERVICES["copyparty"], '/' + path)

@app.route('/services', defaults={'path': ''})
@app.route('/services/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["services", "all"])
def route_services(path):
    """Route to Services Manager API"""
    return proxy_request(SERVICES["services"], '/' + path)

@app.route('/webhooks', defaults={'path': ''})
@app.route('/webhooks/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_api_key(["all"])
def route_webhooks(path):
    """Route to Webhook Manager (admin only)"""
    return proxy_request(SERVICES["webhooks"], '/' + path)

@app.route('/mastodon', defaults={'path': ''})
@app.route('/mastodon/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def route_mastodon(path):
    """Route to Mastodon Social Network - no API key required (has own auth)"""
    return proxy_request(SERVICES["mastodon"], '/' + path)

@app.route('/mattermost', defaults={'path': ''})
@app.route('/mattermost/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def route_mattermost(path):
    """Route to Mattermost Team Chat - no API key required (has own auth)"""
    return proxy_request(SERVICES["mattermost"], '/' + path)

@app.route('/mastodon-bridge', defaults={'path': ''})
@app.route('/mastodon-bridge/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_mastodon_bridge(path):
    """Route to Mastodon Bridge Bot - no API key required"""
    return proxy_request(SERVICES["mastodon-bridge"], '/' + path)

@app.route('/headscale', defaults={'path': ''})
@app.route('/headscale/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_headscale(path):
    """Route to Headscale Control Server - no API key required"""
    return proxy_request(SERVICES["headscale"], '/' + path)

@app.route('/tailscale', defaults={'path': ''})
@app.route('/tailscale/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_tailscale(path):
    """Route to Tailscale UI - no API key required"""
    return proxy_request(SERVICES["tailscale"], '/' + path)

if __name__ == '__main__':
    # Initialize
    init_database()
    api_keys = load_api_keys()

    logger.info("="*60)
    logger.info("HubNode Unified API Gateway Starting")
    logger.info("="*60)
    logger.info(f"Gateway Port: {GATEWAY_PORT}")
    logger.info(f"Server IP: 64.20.46.178")
    logger.info(f"API Keys file: {API_KEYS_FILE}")
    logger.info("")
    logger.info("Access URLs:")
    logger.info("  - https://api.devinecreations.net")
    logger.info("  - https://api.devine-creations.net")
    logger.info(f"  - http://64.20.46.178:{GATEWAY_PORT}")
    logger.info("")
    logger.info("Services registered:")
    for name, config in SERVICES.items():
        logger.info(f"  - {config['name']} -> {config['prefix']}")
    logger.info("")
    logger.info("API Keys:")
    for key_name, key_data in api_keys.items():
        logger.info(f"  - {key_name}: {key_data['key'][:20]}...")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=GATEWAY_PORT, debug=False)
