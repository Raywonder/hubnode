#!/usr/bin/env python3
"""
Service Monitor API
Monitors all critical services including CopyParty servers
"""

import subprocess
import json
import socket
import os
import requests
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Discord webhook configuration. Keep secrets in env/config, not source.
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# Mastodon configuration
MASTODON_INSTANCE = os.getenv('MASTODON_INSTANCE', 'https://md.tappedin.fm')
MASTODON_ACCESS_TOKEN = os.getenv('MASTODON_ACCESS_TOKEN', '')

# Rate limiting for notifications (prevent spam)
discord_rate_limit = {}
mastodon_rate_limit = {}
RATE_LIMIT_SECONDS = 60  # Max 1 notification per minute per event type

# VoiceLink admin notification configuration
VOICELINK_ENABLED = os.getenv('VOICELINK_ENABLED', '0').lower() in ('1', 'true', 'yes', 'on')
VOICELINK_NOTIFY_URL = os.getenv('VOICELINK_NOTIFY_URL', '').strip()
VOICELINK_API_KEY = os.getenv('VOICELINK_API_KEY', '').strip()
VOICELINK_BEARER_TOKEN = os.getenv('VOICELINK_BEARER_TOKEN', '').strip()
VOICELINK_ROOM_ID = os.getenv('VOICELINK_ROOM_ID', '').strip() or None

# Optional config file to allow turnkey setup from hubnode config directory
VOICELINK_PLUGIN_CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / 'config' / 'clawx-voicelink-plugin.json'
)

# API services monitored for VoiceLink admin notifications
API_PORT_SERVICES = {
    '5001': {'name': 'Audio Portrait API', 'process': 'python'},
    '5002': {'name': 'User Logs Collector API', 'process': 'python'},
    '5003': {'name': 'Service Monitor API', 'process': 'python'},
    '5004': {'name': 'Webhook Manager API', 'process': 'python'},
    '5016': {'name': 'CopyParty Admin API', 'process': 'python'}
}

BACKEND_HTTP_SERVICES = [
    {
        'id': 'hubnode-service-monitor',
        'name': 'Hubnode Service Monitor API',
        'category': 'monitoring',
        'url': 'http://127.0.0.1:5003/health',
        'expected_status': [200]
    },
    {
        'id': 'openlink-signaling',
        'name': 'OpenLink Signaling',
        'category': 'openlink',
        'url': 'https://openlink.raywonderis.me/health',
        'expected_status': [200]
    },
    {
        'id': 'openclaw-gateway',
        'name': 'OpenClaw Gateway',
        'category': 'gateway',
        'url': 'http://127.0.0.1:18789/health',
        'expected_status': [200]
    },
    {
        'id': 'voicelink-local',
        'name': 'VoiceLink Local API',
        'category': 'voicelink',
        'url': 'http://127.0.0.1:3010/health',
        'expected_status': [200]
    },
    {
        'id': 'ollama',
        'name': 'Ollama AI Backend',
        'category': 'ai',
        'url': 'http://127.0.0.1:11434/api/tags',
        'expected_status': [200]
    },
    {
        'id': 'authelia',
        'name': 'Authelia Auth Backend',
        'category': 'auth',
        'url': 'http://127.0.0.1:9092/api/health',
        'expected_status': [200]
    }
]

PM2_BACKEND_SERVICES = [
    'openclaw-bugkeeper',
    'openclaw-flexpbx-keeper',
    'voicelink-local',
    'voicelink-node2'
]

# Keep in-memory state to notify only on status transitions
api_service_state_cache = {}

class ServiceMonitor:
    """Monitor various system and custom services"""

    SYSTEMD_SERVICES = [
        'httpd',
        'nginx',
        'mariadb',
        'php-fpm',
        'ea-php81-php-fpm',
        'docker',
        'lfd',
        'sshd',
        'asterisk'
    ]

    PORT_SERVICES = {
        '3923': {'name': 'CopyParty Complete (3923)', 'process': 'python3'},
        '3924': {'name': 'CopyParty Public (3924)', 'process': 'python3'},
        '5001': {'name': 'Audio Portrait API', 'process': 'python'},
        '80': {'name': 'HTTP', 'process': 'httpd'},
        '443': {'name': 'HTTPS', 'process': 'httpd'},
        '3306': {'name': 'MySQL/MariaDB', 'process': 'mariadbd'},
        '5060': {'name': 'FlexPBX SIP', 'process': 'asterisk'},
        '5061': {'name': 'FlexPBX SIPS (TLS)', 'process': 'asterisk'},
    }

    @staticmethod
    def check_systemd_service(service_name):
        """Check if systemd service is active"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                'name': service_name,
                'type': 'systemd',
                'status': 'running' if result.returncode == 0 else 'stopped',
                'active': result.returncode == 0
            }
        except Exception as e:
            return {
                'name': service_name,
                'type': 'systemd',
                'status': 'error',
                'active': False,
                'error': str(e)
            }

    @staticmethod
    def check_port(port, process_name=None):
        """Check if port is listening"""
        try:
            # Check if port is listening
            result = subprocess.run(
                ['netstat', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if f':{port} ' in line:
                    active = True
                    if process_name:
                        active = process_name in line

                    return {
                        'port': port,
                        'active': active,
                        'status': 'listening' if active else 'port_occupied'
                    }

            return {
                'port': port,
                'active': False,
                'status': 'not_listening'
            }
        except Exception as e:
            return {
                'port': port,
                'active': False,
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    def check_process(process_name):
        """Check if process is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', process_name],
                capture_output=True,
                text=True,
                timeout=5
            )

            pids = [pid.strip() for pid in result.stdout.split('\n') if pid.strip()]

            return {
                'process': process_name,
                'active': len(pids) > 0,
                'status': 'running' if pids else 'stopped',
                'pids': pids,
                'count': len(pids)
            }
        except Exception as e:
            return {
                'process': process_name,
                'active': False,
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    def check_http_service(service):
        """Check an HTTP health endpoint without returning secrets."""
        started = time.time()
        expected = service.get('expected_status', [200])
        try:
            response = requests.get(service['url'], timeout=5)
            latency_ms = int((time.time() - started) * 1000)
            active = response.status_code in expected
            return {
                'id': service['id'],
                'name': service['name'],
                'category': service.get('category', 'backend'),
                'type': 'http',
                'url': service['url'],
                'status_code': response.status_code,
                'latency_ms': latency_ms,
                'active': active,
                'status': 'online' if active else 'down'
            }
        except Exception as e:
            latency_ms = int((time.time() - started) * 1000)
            return {
                'id': service['id'],
                'name': service['name'],
                'category': service.get('category', 'backend'),
                'type': 'http',
                'url': service['url'],
                'latency_ms': latency_ms,
                'active': False,
                'status': 'down',
                'error': str(e)
            }

    @staticmethod
    def get_pm2_processes():
        """Return PM2 process state for backend services."""
        try:
            result = subprocess.run(
                ['pm2', 'jlist'],
                capture_output=True,
                text=True,
                timeout=8
            )
            if result.returncode != 0:
                return []
            processes = json.loads(result.stdout or '[]')
            monitored = []
            for item in processes:
                name = item.get('name', '')
                if name not in PM2_BACKEND_SERVICES:
                    continue
                env = item.get('pm2_env', {})
                status = env.get('status', 'unknown')
                monitored.append({
                    'id': name,
                    'name': name,
                    'type': 'pm2',
                    'category': 'process',
                    'active': status == 'online',
                    'status': 'online' if status == 'online' else status,
                    'pid': item.get('pid'),
                    'restart_count': env.get('restart_time', 0),
                    'uptime_ms': int(time.time() * 1000) - env.get('pm_uptime', int(time.time() * 1000))
                })
            return monitored
        except Exception as e:
            return [{
                'id': 'pm2',
                'name': 'PM2 backend process list',
                'type': 'pm2',
                'category': 'process',
                'active': False,
                'status': 'error',
                'error': str(e)
            }]

    @classmethod
    def get_backend_services_status(cls):
        """Get AI/backend and application service health for trays and dashboards."""
        http_services = [cls.check_http_service(service) for service in BACKEND_HTTP_SERVICES]
        pm2_services = cls.get_pm2_processes()
        services = http_services + pm2_services
        online = sum(1 for service in services if service.get('active'))
        down = sum(1 for service in services if not service.get('active'))
        overall = 'online' if down == 0 else 'degraded' if online > 0 else 'down'
        return {
            'timestamp': datetime.now().isoformat(),
            'overall': overall,
            'summary': {
                'total': len(services),
                'online': online,
                'down': down
            },
            'services': services
        }

    @classmethod
    def get_all_services_status(cls):
        """Get status of all monitored services"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'systemd_services': [],
            'port_services': [],
            'custom_processes': [],
            'backend_services': {},
            'summary': {
                'total': 0,
                'running': 0,
                'stopped': 0,
                'error': 0
            }
        }

        # Check systemd services
        for service in cls.SYSTEMD_SERVICES:
            svc_status = cls.check_systemd_service(service)
            status['systemd_services'].append(svc_status)
            status['summary']['total'] += 1
            if svc_status['active']:
                status['summary']['running'] += 1
            elif svc_status['status'] == 'error':
                status['summary']['error'] += 1
            else:
                status['summary']['stopped'] += 1

        # Check port-based services
        for port, info in cls.PORT_SERVICES.items():
            port_status = cls.check_port(port, info.get('process'))
            port_status['name'] = info['name']
            status['port_services'].append(port_status)
            status['summary']['total'] += 1
            if port_status['active']:
                status['summary']['running'] += 1
            elif port_status['status'] == 'error':
                status['summary']['error'] += 1
            else:
                status['summary']['stopped'] += 1

        # Check CSF firewall
        csf_status = cls.check_process('lfd - sleeping')
        csf_status['name'] = 'CSF/LFD Firewall'
        status['custom_processes'].append(csf_status)
        status['summary']['total'] += 1
        if csf_status['active']:
            status['summary']['running'] += 1
        elif csf_status['status'] == 'error':
            status['summary']['error'] += 1
        else:
            status['summary']['stopped'] += 1

        backend_status = cls.get_backend_services_status()
        status['backend_services'] = backend_status
        for service in backend_status.get('services', []):
            status['summary']['total'] += 1
            if service.get('active'):
                status['summary']['running'] += 1
            else:
                status['summary']['stopped'] += 1

        return status

    @classmethod
    def get_copyparty_servers(cls):
        """Get detailed status of all CopyParty servers"""
        servers = []

        for port in ['3923', '3924']:
            port_status = cls.check_port(port, 'python3')

            # Get process details
            process_info = cls.check_process(f'copyparty.*{port}')

            server = {
                'port': port,
                'name': cls.PORT_SERVICES[port]['name'],
                'active': port_status['active'],
                'status': port_status['status'],
                'process_count': process_info.get('count', 0),
                'pids': process_info.get('pids', [])
            }

            servers.append(server)

        return {
            'timestamp': datetime.now().isoformat(),
            'servers': servers,
            'total': len(servers),
            'active': sum(1 for s in servers if s['active'])
        }


def load_voicelink_plugin_config():
    """Load ClawX/OpenClaw VoiceLink plugin config (with sane defaults)."""
    default_config = {
        'pluginId': 'voicelink-admin-monitor',
        'name': 'VoiceLink Admin Monitor',
        'enabled': VOICELINK_ENABLED,
        'clients': ['clawx', 'openclaw'],
        'compatibleClients': {
            'clawx': True,
            'openclaw': True
        },
        'apiMonitor': {
            'baseUrl': os.getenv('HUBNODE_SERVICE_MONITOR_URL', 'http://localhost:5003'),
            'statusEndpoint': '/status/api',
            'testEndpoint': '/notify/voicelink/test'
        },
        'voicelink': {
            'notifyUrl': VOICELINK_NOTIFY_URL,
            'roomId': VOICELINK_ROOM_ID,
            'auth': {
                'usesApiKey': bool(VOICELINK_API_KEY),
                'usesBearerToken': bool(VOICELINK_BEARER_TOKEN)
            }
        },
        'features': [
            {
                'id': 'api_status_alerts',
                'label': 'API Status Alerts',
                'description': 'Sends up/down alerts for monitored api/* services to VoiceLink admins.',
                'enabledByDefault': True
            },
            {
                'id': 'manual_test_ping',
                'label': 'Manual Test Ping',
                'description': 'Allows test notifications to validate VoiceLink delivery and auth.',
                'enabledByDefault': True
            },
            {
                'id': 'severity_metadata',
                'label': 'Severity + Metadata',
                'description': 'Includes severity, service name, port, and source metadata for admin triage.',
                'enabledByDefault': True
            }
        ]
    }

    try:
        if VOICELINK_PLUGIN_CONFIG_PATH.exists():
            with open(VOICELINK_PLUGIN_CONFIG_PATH, 'r') as f:
                configured = json.load(f)
            if isinstance(configured, dict):
                # Shallow merge keeps deployment-specific overrides simple.
                merged = {**default_config, **configured}
                merged['apiMonitor'] = {**default_config['apiMonitor'], **configured.get('apiMonitor', {})}
                merged['voicelink'] = {**default_config['voicelink'], **configured.get('voicelink', {})}
                return merged
    except Exception as e:
        print(f"Failed to load VoiceLink plugin config: {e}")

    return default_config


def send_voicelink_notification(title, message, severity='info', metadata=None):
    """Send an admin notification to VoiceLink if configured."""
    plugin_config = load_voicelink_plugin_config()
    notify_url = (plugin_config.get('voicelink', {}) or {}).get('notifyUrl') or VOICELINK_NOTIFY_URL
    enabled = bool(plugin_config.get('enabled', False))
    if not enabled or not notify_url:
        return False, 'voicelink notifier disabled or notify URL missing'

    payload = {
        'type': 'system_action',
        'title': title,
        'message': message,
        'severity': severity,
        'roomId': (plugin_config.get('voicelink', {}) or {}).get('roomId') or VOICELINK_ROOM_ID,
        'metadata': {
            'source': 'hubnode-api-monitor',
            'timestamp': datetime.now().isoformat(),
            **(metadata or {})
        }
    }

    headers = {'Content-Type': 'application/json'}
    if VOICELINK_API_KEY:
        headers['x-api-key'] = VOICELINK_API_KEY
    if VOICELINK_BEARER_TOKEN:
        headers['Authorization'] = f'Bearer {VOICELINK_BEARER_TOKEN}'

    try:
        response = requests.post(notify_url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201, 202, 204):
            return True, 'notification sent'
        return False, f'voicelink returned {response.status_code}'
    except Exception as e:
        return False, str(e)


def monitor_api_services_and_notify():
    """Check API service states and emit VoiceLink notifications on transitions."""
    transitions = []
    for port, info in API_PORT_SERVICES.items():
        port_status = ServiceMonitor.check_port(port, info.get('process'))
        active = bool(port_status.get('active', False))
        current_state = 'running' if active else 'down'
        previous_state = api_service_state_cache.get(port)
        api_service_state_cache[port] = current_state

        if previous_state is None or previous_state == current_state:
            continue

        severity = 'warning' if current_state == 'down' else 'info'
        title = f"API Service {current_state.upper()}: {info['name']}"
        message = (
            f"{info['name']} on port {port} changed state "
            f"from {previous_state} to {current_state}."
        )
        sent, detail = send_voicelink_notification(
            title=title,
            message=message,
            severity=severity,
            metadata={
                'service': info['name'],
                'port': port,
                'previousState': previous_state,
                'currentState': current_state
            }
        )
        transitions.append({
            'service': info['name'],
            'port': port,
            'previous': previous_state,
            'current': current_state,
            'voicelinkNotified': sent,
            'detail': detail
        })

    return transitions

# API Routes

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'name': 'Service Monitor API',
        'version': '1.0.0',
        'endpoints': {
            '/status': 'Get all services status',
            '/status/backend': 'Get AI/backend, OpenLink, VoiceLink, gateway, auth, and PM2 health',
            '/status/api': 'Get api/* service status + VoiceLink admin transitions',
            '/status/systemd': 'Get systemd services only',
            '/status/ports': 'Get port-based services only',
            '/status/copyparty': 'Get CopyParty servers status',
            '/service/<name>': 'Get specific service status',
            '/integrations/plugins/voicelink': 'VoiceLink plugin manifest (ClawX/OpenClaw compatible)',
            '/integrations/plugins/voicelink/<client_id>': 'Client-specific plugin manifest',
            '/notify/voicelink/test': 'Send a test VoiceLink admin notification',
            '/health': 'API health check'
        }
    })

@app.route('/status')
def get_status():
    """Get status of all services"""
    return jsonify(ServiceMonitor.get_all_services_status())

@app.route('/status/backend')
def get_backend_status():
    """Get AI/backend and application service health."""
    return jsonify(ServiceMonitor.get_backend_services_status())

@app.route('/status/systemd')
def get_systemd_status():
    """Get systemd services status"""
    services = []
    for service in ServiceMonitor.SYSTEMD_SERVICES:
        services.append(ServiceMonitor.check_systemd_service(service))

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'services': services,
        'total': len(services),
        'active': sum(1 for s in services if s['active'])
    })

@app.route('/status/ports')
def get_ports_status():
    """Get port-based services status"""
    services = []
    for port, info in ServiceMonitor.PORT_SERVICES.items():
        port_status = ServiceMonitor.check_port(port, info.get('process'))
        port_status['name'] = info['name']
        services.append(port_status)

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'services': services,
        'total': len(services),
        'active': sum(1 for s in services if s['active'])
    })

@app.route('/status/api')
def get_api_services_status():
    """Get status for api/* services and trigger VoiceLink alerts on transitions."""
    services = []
    for port, info in API_PORT_SERVICES.items():
        port_status = ServiceMonitor.check_port(port, info.get('process'))
        port_status['name'] = info['name']
        services.append(port_status)

    transitions = monitor_api_services_and_notify()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'services': services,
        'total': len(services),
        'active': sum(1 for s in services if s.get('active')),
        'transitions': transitions
    })

@app.route('/status/copyparty')
def get_copyparty_status():
    """Get CopyParty servers status"""
    return jsonify(ServiceMonitor.get_copyparty_servers())

@app.route('/service/<service_name>')
def get_service_status(service_name):
    """Get specific service status"""
    # Check if it's a systemd service
    if service_name in ServiceMonitor.SYSTEMD_SERVICES:
        return jsonify(ServiceMonitor.check_systemd_service(service_name))

    # Check if it's a port
    if service_name in ServiceMonitor.PORT_SERVICES:
        info = ServiceMonitor.PORT_SERVICES[service_name]
        status = ServiceMonitor.check_port(service_name, info.get('process'))
        status['name'] = info['name']
        return jsonify(status)

    backend_status = ServiceMonitor.get_backend_services_status()
    for service in backend_status.get('services', []):
        if service_name in (service.get('id'), service.get('name')):
            return jsonify(service)

    # Try as a process name
    return jsonify(ServiceMonitor.check_process(service_name))

@app.route('/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/integrations/plugins/voicelink')
@app.route('/integrations/plugins/voicelink/<client_id>')
def get_voicelink_plugin_manifest(client_id=None):
    """
    Return VoiceLink plugin manifest for ClawX/OpenClaw clients.
    client_id can be "clawx" or "openclaw".
    """
    manifest = load_voicelink_plugin_config()
    requested = (client_id or '').strip().lower()
    if requested and requested not in ('clawx', 'openclaw'):
        return jsonify({
            'success': False,
            'error': f'Unsupported client "{requested}". Use clawx or openclaw.'
        }), 400

    if requested:
        compat = manifest.get('compatibleClients', {}).get(requested, False)
        manifest['requestedClient'] = requested
        manifest['compatible'] = bool(compat)

    return jsonify({
        'success': True,
        'plugin': manifest
    })

@app.route('/status/flexpbx')
def get_flexpbx_status():
    """Get FlexPBX-specific status"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'asterisk': ServiceMonitor.check_systemd_service('asterisk'),
        'sip_port': ServiceMonitor.check_port('5060', 'asterisk'),
        'sips_port': ServiceMonitor.check_port('5061', 'asterisk')
    }

    # Check for active channels
    try:
        result = subprocess.run(
            ['sudo', '-u', 'asterisk', '/usr/sbin/asterisk', '-rx', 'core show channels count'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'active channel' in line.lower():
                    status['active_channels'] = line.strip()
                    break
    except:
        status['active_channels'] = 'Unable to query'

    return jsonify(status)

# FlexPBX Event Logging
EVENTS_FILE = '/home/devinecr/apps/hubnode/clients/api_monitor/flexpbx_events.json'

def send_discord_notification(event_type, action, success, data=None):
    """
    Send event notification to Discord webhook

    Args:
        event_type: Type of event (backup, module, system)
        action: Action performed (create, delete, install, etc.)
        success: Boolean indicating success/failure
        data: Additional event data

    Returns:
        Boolean indicating if notification was sent successfully
    """
    try:
        # Check rate limit
        rate_key = f"{event_type}:{action}"
        current_time = time.time()

        if rate_key in discord_rate_limit:
            last_sent = discord_rate_limit[rate_key]
            if current_time - last_sent < RATE_LIMIT_SECONDS:
                print(f"Rate limit: Skipping Discord notification for {rate_key}")
                return False

        # Update rate limit
        discord_rate_limit[rate_key] = current_time

        # Event type icons and colors
        event_icons = {
            'backup': '📦',
            'module': '🔌',
            'system': '⚙️',
            'notification': '📢'
        }

        event_colors = {
            'backup': 0x3b82f6,  # Blue
            'module': 0x10b981,  # Green
            'system': 0xf59e0b,  # Orange
            'notification': 0x667eea  # Purple
        }

        # Status color override
        color = 0x10b981 if success else 0xef4444  # Green for success, Red for failure
        if event_type in event_colors and success:
            color = event_colors[event_type]

        # Build description
        description = f"**Action:** {action.title()}\n"
        description += f"**Status:** {'✅ Success' if success else '❌ Failed'}\n"

        if data:
            if 'backup_type' in data:
                description += f"**Backup Type:** {data['backup_type']}\n"
            if 'compressed' in data:
                description += f"**Compressed:** {'Yes' if data['compressed'] else 'No'}\n"
            if 'request_id' in data:
                description += f"**Request ID:** {data['request_id']}\n"
            if 'module' in data:
                description += f"**Module:** {data['module']}\n"
            if 'version' in data:
                description += f"**Version:** {data['version']}\n"
            if 'message' in data:
                description += f"\n{data['message']}\n"
            if 'target' in data:
                description += f"**Target:** {data['target']}\n"
            if 'priority' in data:
                description += f"**Priority:** {data['priority'].title()}\n"

        # Build Discord embed
        icon = event_icons.get(event_type, '📝')
        title = f"{icon} FlexPBX {event_type.title()} Event"

        embed = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "footer": {
                    "text": "FlexPBX HubNode Monitor",
                    "icon_url": "https://flexpbx.devinecreations.net/favicon.ico"
                },
                "timestamp": datetime.now().isoformat()
            }]
        }

        # Send to Discord
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed, timeout=10)

        if response.status_code in [200, 204]:
            print(f"✅ Discord notification sent: {event_type}/{action}")
            return True
        else:
            print(f"❌ Discord webhook failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False

def send_mastodon_notification(event_type, action, success, data=None, visibility='unlisted'):
    """
    Send event notification to Mastodon

    Args:
        event_type: Type of event (backup, module, system, notification)
        action: Action performed (create, delete, install, etc.)
        success: Boolean indicating success/failure
        data: Additional event data
        visibility: Mastodon visibility (public, unlisted, private, direct)

    Returns:
        Boolean indicating if notification was sent successfully
    """
    try:
        # Check rate limit
        rate_key = f"{event_type}:{action}"
        current_time = time.time()

        if rate_key in mastodon_rate_limit:
            last_sent = mastodon_rate_limit[rate_key]
            if current_time - last_sent < RATE_LIMIT_SECONDS:
                print(f"Rate limit: Skipping Mastodon notification for {rate_key}")
                return False

        # Update rate limit
        mastodon_rate_limit[rate_key] = current_time

        # Import mastodon library
        try:
            from mastodon import Mastodon
        except ImportError:
            print("Mastodon.py library not installed, skipping Mastodon notification")
            return False

        # Initialize Mastodon client
        mastodon = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url=MASTODON_INSTANCE
        )

        # Event type icons
        event_icons = {
            'backup': '📦',
            'module': '🔌',
            'system': '⚙️',
            'notification': '📢'
        }

        icon = event_icons.get(event_type, '📝')
        status_icon = '✅' if success else '❌'

        # Build message
        message = f"{icon} FlexPBX {event_type.title()} Event\n\n"
        message += f"Action: {action.title()}\n"
        message += f"Status: {status_icon} {'Success' if success else 'Failed'}\n"

        if data:
            message += "\n"
            if 'backup_type' in data:
                message += f"Backup Type: {data['backup_type']}\n"
            if 'module' in data:
                message += f"Module: {data['module']}\n"
            if 'version' in data:
                message += f"Version: {data['version']}\n"
            if 'message' in data:
                message += f"\n{data['message']}\n"
            if 'target' in data:
                message += f"Target: {data['target']}\n"

        message += f"\n#FlexPBX #Monitoring"

        # Post to Mastodon
        toot = mastodon.status_post(message, visibility=visibility)

        print(f"✅ Mastodon notification sent: {toot.get('url', 'unknown URL')}")
        return True

    except Exception as e:
        print(f"Error sending Mastodon notification: {e}")
        return False

def send_mastodon_dm(recipient_handle, message):
    """
    Send a direct message via Mastodon

    Args:
        recipient_handle: Mastodon username (e.g., 'raywonder')
        message: Message text

    Returns:
        Boolean indicating success
    """
    try:
        from mastodon import Mastodon

        mastodon = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url=MASTODON_INSTANCE
        )

        # Search for the user
        results = mastodon.account_search(recipient_handle, limit=1)

        if not results:
            print(f"Mastodon user not found: {recipient_handle}")
            return False

        recipient = results[0]

        # Send DM
        status = mastodon.status_post(
            f"@{recipient['acct']} {message}",
            visibility='direct'
        )

        print(f"✅ Mastodon DM sent to @{recipient['acct']}")
        return True

    except Exception as e:
        print(f"Error sending Mastodon DM: {e}")
        return False

@app.route('/events', methods=['POST'])
def log_event():
    """Log an event from FlexPBX"""
    try:
        event_data = request.get_json()
        if not event_data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Add timestamp if not present
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.now().isoformat()

        # Read existing events
        try:
            with open(EVENTS_FILE, 'r') as f:
                events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            events = []

        # Add new event
        events.append(event_data)

        # Keep only last 1000 events
        if len(events) > 1000:
            events = events[-1000:]

        # Write back
        with open(EVENTS_FILE, 'w') as f:
            json.dump(events, f, indent=2)

        # Send Discord notification for important events
        event_type = event_data.get('type', 'unknown')
        action = event_data.get('action', 'unknown')
        success = event_data.get('success', True)
        data = event_data.get('data', {})

        # Send notifications for completed actions (not queued)
        if action != 'queued':
            send_discord_notification(event_type, action, success, data)

        return jsonify({
            'success': True,
            'message': 'Event logged',
            'event_id': len(events)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/events')
def list_events():
    """List recent FlexPBX events"""
    try:
        limit = int(request.args.get('limit', 50))
        event_type = request.args.get('type', None)

        with open(EVENTS_FILE, 'r') as f:
            events = json.load(f)

        # Filter by type if specified
        if event_type:
            events = [e for e in events if e.get('type') == event_type]

        # Return most recent events
        recent_events = events[-limit:]
        recent_events.reverse()

        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'events': recent_events,
            'total': len(recent_events),
            'total_stored': len(events)
        })

    except FileNotFoundError:
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'events': [],
            'total': 0,
            'message': 'No events logged yet'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_discord', methods=['POST'])
def test_discord():
    """Test Discord webhook with a test message"""
    try:
        success = send_discord_notification(
            event_type='system',
            action='test',
            success=True,
            data={'message': 'This is a test notification from FlexPBX HubNode Monitor'}
        )

        return jsonify({
            'success': success,
            'message': 'Discord test notification sent' if success else 'Failed to send Discord notification'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/notify/voicelink/test', methods=['POST'])
def test_voicelink_notification():
    """Send a test admin notification to VoiceLink."""
    try:
        data = request.get_json() or {}
        severity = data.get('severity', 'info')
        title = data.get('title', 'HubNode API Monitor Test')
        message = data.get(
            'message',
            'Test notification from HubNode API Monitor to VoiceLink admins.'
        )
        sent, detail = send_voicelink_notification(
            title=title,
            message=message,
            severity=severity,
            metadata={'test': True}
        )

        return jsonify({
            'success': sent,
            'detail': detail,
            'voicelinkEnabled': load_voicelink_plugin_config().get('enabled', False)
        }), (200 if sent else 502)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/send_mastodon', methods=['POST'])
def send_mastodon():
    """Send a Mastodon notification (called by push notification API)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        event_type = data.get('event_type', 'notification')
        action = data.get('action', 'push')
        success_flag = data.get('success', True)
        event_data = data.get('data', {})
        visibility = data.get('visibility', 'unlisted')

        success = send_mastodon_notification(
            event_type=event_type,
            action=action,
            success=success_flag,
            data=event_data,
            visibility=visibility
        )

        return jsonify({
            'success': success,
            'message': f'Mastodon notification sent ({visibility} visibility)' if success else 'Failed to send Mastodon notification'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_mastodon', methods=['POST'])
def test_mastodon():
    """Test Mastodon posting with a test message"""
    try:
        # Get visibility from request (default to unlisted)
        data = request.get_json() or {}
        visibility = data.get('visibility', 'unlisted')

        success = send_mastodon_notification(
            event_type='system',
            action='test',
            success=True,
            data={'message': 'This is a test notification from FlexPBX HubNode Monitor'},
            visibility=visibility
        )

        return jsonify({
            'success': success,
            'message': f'Mastodon test post sent ({visibility} visibility)' if success else 'Failed to send Mastodon notification'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Service Monitor API on port 5003...")
    print(f"Discord webhook configured: {bool(DISCORD_WEBHOOK_URL)}")
    print(f"Mastodon instance: {MASTODON_INSTANCE}")
    print(f"Mastodon token configured: {bool(MASTODON_ACCESS_TOKEN)}")
    app.run(host='0.0.0.0', port=5003, debug=False)
