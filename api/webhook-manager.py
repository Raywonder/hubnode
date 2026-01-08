#!/usr/bin/env python3
"""
Webhook and External API Integration Manager
Allows external services (YouTube, other APIs) to hook into HubNode services
Supports: YouTube API, GitHub webhooks, Discord, Slack, custom webhooks
"""

import os
import json
import hmac
import hashlib
import sqlite3
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from functools import wraps
import logging

app = Flask(__name__)

# Configuration
DB_PATH = "/home/devinecr/apps/hubnode/api/webhooks.db"
WEBHOOKS_CONFIG = "/home/devinecr/apps/hubnode/api/webhooks_config.json"
LOG_FILE = "/var/log/webhooks.log"

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
    """Initialize webhooks database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Registered webhooks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            webhook_type TEXT NOT NULL,
            endpoint TEXT UNIQUE NOT NULL,
            secret TEXT,
            target_service TEXT,
            target_action TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Webhook events log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            webhook_id INTEGER,
            event_type TEXT,
            payload TEXT,
            source_ip TEXT,
            processed BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (webhook_id) REFERENCES webhooks(id)
        )
    ''')

    # External API integrations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS external_apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            api_key TEXT,
            api_secret TEXT,
            config TEXT,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def load_webhooks_config():
    """Load webhooks configuration"""
    if os.path.exists(WEBHOOKS_CONFIG):
        with open(WEBHOOKS_CONFIG, 'r') as f:
            return json.load(f)

    # Default configuration
    default_config = {
        "youtube": {
            "enabled": True,
            "api_key": "YOUR_YOUTUBE_API_KEY",
            "channel_ids": [],
            "actions": ["video_upload", "comment", "livestream_start"]
        },
        "github": {
            "enabled": True,
            "webhook_secret": "YOUR_GITHUB_WEBHOOK_SECRET",
            "actions": ["push", "pull_request", "release"]
        },
        "discord": {
            "enabled": True,
            "webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
            "actions": ["message", "alert"]
        },
        "slack": {
            "enabled": True,
            "webhook_url": "YOUR_SLACK_WEBHOOK_URL",
            "actions": ["message", "alert"]
        },
        "custom": {
            "enabled": True,
            "webhooks": []
        }
    }

    with open(WEBHOOKS_CONFIG, 'w') as f:
        json.dump(default_config, f, indent=2)

    os.chmod(WEBHOOKS_CONFIG, 0o600)
    return default_config

def verify_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

# Webhook Routes

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """GitHub webhook handler"""
    signature = request.headers.get('X-Hub-Signature-256')
    event_type = request.headers.get('X-GitHub-Event')

    config = load_webhooks_config()
    if not config.get('github', {}).get('enabled'):
        return jsonify({"error": "GitHub webhooks disabled"}), 403

    # Verify signature
    secret = config['github'].get('webhook_secret')
    if secret and signature:
        if not verify_signature(request.data, signature, secret):
            return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json()

    # Log event
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO webhook_events (webhook_id, event_type, payload, source_ip)
        VALUES ((SELECT id FROM webhooks WHERE webhook_type='github' LIMIT 1), ?, ?, ?)
    ''', (event_type, json.dumps(payload), request.remote_addr))
    conn.commit()
    conn.close()

    logger.info(f"GitHub webhook received: {event_type}")

    # Process based on event type
    if event_type == 'push':
        # Trigger deployment or sync
        return jsonify({"status": "push event processed"})
    elif event_type == 'release':
        # Trigger release workflow
        return jsonify({"status": "release event processed"})

    return jsonify({"status": "event received"})

@app.route('/webhook/youtube', methods=['POST'])
def youtube_webhook():
    """YouTube notifications webhook (PubSubHubbub)"""
    # YouTube uses XML for notifications
    from xml.etree import ElementTree as ET

    config = load_webhooks_config()
    if not config.get('youtube', {}).get('enabled'):
        return jsonify({"error": "YouTube webhooks disabled"}), 403

    try:
        xml_data = request.data.decode('utf-8')
        root = ET.fromstring(xml_data)

        # Extract video info
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry:
            video_id = entry.find('{http://www.youtube.com/xml/schemas/2015}videoId')
            channel_id = entry.find('{http://www.youtube.com/xml/schemas/2015}channelId')

            event_data = {
                'video_id': video_id.text if video_id is not None else None,
                'channel_id': channel_id.text if channel_id is not None else None
            }

            # Log event
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO webhook_events (webhook_id, event_type, payload, source_ip)
                VALUES ((SELECT id FROM webhooks WHERE webhook_type='youtube' LIMIT 1), ?, ?, ?)
            ''', ('video_upload', json.dumps(event_data), request.remote_addr))
            conn.commit()
            conn.close()

            logger.info(f"YouTube webhook: new video {event_data['video_id']}")

            return '', 204

    except Exception as e:
        logger.error(f"YouTube webhook error: {e}")
        return jsonify({"error": "Processing failed"}), 500

    return '', 204

@app.route('/webhook/youtube/verify', methods=['GET'])
def youtube_webhook_verify():
    """YouTube webhook verification"""
    mode = request.args.get('hub.mode')
    topic = request.args.get('hub.topic')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe':
        logger.info(f"YouTube webhook subscription verified for {topic}")
        return challenge, 200

    return '', 404

@app.route('/webhook/discord', methods=['POST'])
def discord_webhook():
    """Discord incoming webhook handler"""
    config = load_webhooks_config()
    if not config.get('discord', {}).get('enabled'):
        return jsonify({"error": "Discord webhooks disabled"}), 403

    payload = request.get_json()

    # Log event
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO webhook_events (webhook_id, event_type, payload, source_ip)
        VALUES ((SELECT id FROM webhooks WHERE webhook_type='discord' LIMIT 1), ?, ?, ?)
    ''', ('message', json.dumps(payload), request.remote_addr))
    conn.commit()
    conn.close()

    logger.info("Discord webhook received")
    return jsonify({"status": "received"})

@app.route('/webhook/custom/<webhook_name>', methods=['POST'])
def custom_webhook(webhook_name):
    """Custom webhook handler"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get webhook config
    cursor.execute('''
        SELECT id, secret, target_service, target_action
        FROM webhooks
        WHERE name = ? AND active = 1
    ''', (webhook_name,))

    webhook = cursor.fetchone()
    if not webhook:
        conn.close()
        return jsonify({"error": "Webhook not found"}), 404

    webhook_id, secret, target_service, target_action = webhook

    # Verify signature if secret is set
    if secret:
        signature = request.headers.get('X-Webhook-Signature')
        if not signature or not verify_signature(request.data, signature, secret):
            conn.close()
            return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json() or {}

    # Log event
    cursor.execute('''
        INSERT INTO webhook_events (webhook_id, event_type, payload, source_ip)
        VALUES (?, ?, ?, ?)
    ''', (webhook_id, 'custom', json.dumps(payload), request.remote_addr))
    conn.commit()
    conn.close()

    logger.info(f"Custom webhook '{webhook_name}' received")

    # Execute target action
    if target_service and target_action:
        # Trigger action on target service
        # This can be expanded to call HubNode services
        pass

    return jsonify({"status": "webhook processed"})

# Outgoing webhook triggers
def send_discord_notification(message, webhook_url=None):
    """Send notification to Discord"""
    config = load_webhooks_config()
    url = webhook_url or config.get('discord', {}).get('webhook_url')

    if not url:
        return False

    payload = {"content": message}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 204
    except Exception as e:
        logger.error(f"Discord notification failed: {e}")
        return False

def send_slack_notification(message, webhook_url=None):
    """Send notification to Slack"""
    config = load_webhooks_config()
    url = webhook_url or config.get('slack', {}).get('webhook_url')

    if not url:
        return False

    payload = {"text": message}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False

# YouTube API Integration
def get_youtube_channel_videos(channel_id, api_key=None):
    """Get latest videos from YouTube channel"""
    config = load_webhooks_config()
    key = api_key or config.get('youtube', {}).get('api_key')

    if not key:
        return None

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'key': key,
        'channelId': channel_id,
        'part': 'snippet',
        'order': 'date',
        'maxResults': 10
    }

    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        logger.error(f"YouTube API error: {e}")
        return None

# Management Routes
@app.route('/webhooks', methods=['GET'])
def list_webhooks():
    """List all registered webhooks"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, webhook_type, endpoint, active, created_at
        FROM webhooks
    ''')

    webhooks = []
    for row in cursor.fetchall():
        webhooks.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'endpoint': row[3],
            'active': bool(row[4]),
            'created_at': row[5]
        })

    conn.close()
    return jsonify({"webhooks": webhooks})

@app.route('/webhooks/events', methods=['GET'])
def list_webhook_events():
    """List recent webhook events"""
    limit = request.args.get('limit', 50, type=int)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT e.id, w.name, e.event_type, e.timestamp, e.processed
        FROM webhook_events e
        LEFT JOIN webhooks w ON e.webhook_id = w.id
        ORDER BY e.timestamp DESC
        LIMIT ?
    ''', (limit,))

    events = []
    for row in cursor.fetchall():
        events.append({
            'id': row[0],
            'webhook_name': row[1],
            'event_type': row[2],
            'timestamp': row[3],
            'processed': bool(row[4])
        })

    conn.close()
    return jsonify({"events": events})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "webhook-manager"
    })

if __name__ == '__main__':
    init_database()
    logger.info("Webhook Manager starting on port 5004...")
    app.run(host='0.0.0.0', port=5004, debug=False)
