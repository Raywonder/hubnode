#!/usr/bin/env python3
"""
FlexPBX Service API
Routes FlexPBX API requests through the HubNode API Gateway
Provides external access to master FlexPBX server
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# FlexPBX API base URL (local)
FLEXPBX_BASE = 'http://flexpbx.devinecreations.net/api'
FLEXPBX_LOCAL = 'http://localhost/api'

# Authentication
ADMIN_USERS = ['devinecr', 'dom', 'tappedin', 'admin', 'flexpbxuser']
GENERAL_USERS = ['tetoeehoward', 'wharper', 'flexpbx']

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from header or query param
        user = request.headers.get('X-User') or request.args.get('user')

        if not user:
            return jsonify({'error': 'Authentication required', 'hint': 'Add X-User header or ?user= parameter'}), 401

        # Check if user is authorized
        if user not in ADMIN_USERS and user not in GENERAL_USERS:
            return jsonify({'error': 'Unauthorized user'}), 403

        # Add user to request context
        request.user = user
        request.is_admin = user in ADMIN_USERS

        return f(*args, **kwargs)

    return decorated_function

def require_admin(f):
    """Admin-only decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'is_admin') or not request.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def proxy_to_flexpbx(endpoint, method='GET', data=None, params=None):
    """Proxy request to FlexPBX API"""
    url = f"{FLEXPBX_LOCAL}/{endpoint}"

    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, params=params, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, params=params, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, params=params, timeout=10)
        else:
            return {'error': 'Invalid method'}, 400

        # Return response with original status code
        return response.json(), response.status_code

    except requests.exceptions.Timeout:
        return {'error': 'FlexPBX API timeout'}, 504
    except requests.exceptions.ConnectionError:
        return {'error': 'Cannot connect to FlexPBX'}, 503
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/')
def index():
    """Service information"""
    return jsonify({
        'service': 'FlexPBX API',
        'version': '1.0.0',
        'description': 'Master FlexPBX Server API Access',
        'base_url': '/flexpbx',
        'endpoints': {
            'extensions': '/flexpbx/extensions',
            'trunks': '/flexpbx/trunks',
            'call_logs': '/flexpbx/call-logs',
            'voicemail': '/flexpbx/voicemail',
            'system': '/flexpbx/system'
        },
        'authentication': 'X-User header or ?user= parameter required',
        'documentation': '/flexpbx/docs'
    })

@app.route('/health')
def health():
    """Health check"""
    try:
        # Test connection to FlexPBX
        response = requests.get(f"{FLEXPBX_LOCAL}/system.php?path=health", timeout=5)
        flexpbx_healthy = response.status_code == 200 or response.status_code == 401
    except:
        flexpbx_healthy = False

    return jsonify({
        'status': 'healthy' if flexpbx_healthy else 'degraded',
        'flexpbx_connection': 'online' if flexpbx_healthy else 'offline',
        'timestamp': requests.get('http://worldtimeapi.org/api/timezone/America/Chicago').json().get('datetime', '')
    })

@app.route('/docs')
def documentation():
    """API documentation"""
    return jsonify({
        'title': 'FlexPBX API Documentation',
        'description': 'Master FlexPBX Server API for external access',
        'authentication': {
            'method': 'User-based',
            'header': 'X-User: username',
            'query': '?user=username',
            'admin_users': ADMIN_USERS,
            'general_users': GENERAL_USERS
        },
        'endpoints': {
            'Extensions API': {
                'base': '/flexpbx/extensions',
                'methods': {
                    'GET /': 'List all extensions',
                    'GET /:id': 'Get extension details',
                    'GET /status/:id': 'Get registration status',
                    'POST /': 'Create extension (admin)',
                    'PUT /:id': 'Update extension (admin)',
                    'DELETE /:id': 'Delete extension (admin)'
                }
            },
            'Trunks API': {
                'base': '/flexpbx/trunks',
                'methods': {
                    'GET /': 'List all trunks',
                    'GET /:id': 'Get trunk details',
                    'GET /status/:id': 'Get trunk status',
                    'POST /': 'Create trunk (admin)',
                    'DELETE /:id': 'Delete trunk (admin)',
                    'POST /test/:id': 'Test trunk connectivity'
                }
            },
            'Call Logs API': {
                'base': '/flexpbx/call-logs',
                'methods': {
                    'GET /': 'List call logs',
                    'GET /recent': 'Get recent calls',
                    'GET /statistics': 'Get call statistics',
                    'POST /search': 'Search calls',
                    'GET /export': 'Export calls (CSV/JSON)'
                }
            },
            'Voicemail API': {
                'base': '/flexpbx/voicemail',
                'methods': {
                    'GET /': 'List mailboxes',
                    'GET /messages/:mailbox': 'List messages',
                    'GET /statistics/:mailbox': 'Mailbox statistics',
                    'POST /': 'Create mailbox (admin)',
                    'DELETE /:mailbox': 'Delete mailbox (admin)'
                }
            },
            'System API': {
                'base': '/flexpbx/system',
                'methods': {
                    'GET /health': 'System health',
                    'GET /version': 'Version info',
                    'GET /services': 'Service status',
                    'GET /resources': 'Resource usage',
                    'GET /logs': 'System logs',
                    'POST /backup': 'Create backup (admin)',
                    'POST /restore': 'Restore backup (admin)'
                }
            }
        }
    })

# Extensions API Routes
@app.route('/extensions', methods=['GET', 'POST'])
@require_auth
def extensions():
    """Extensions list/create"""
    if request.method == 'POST' and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['path'] = params.get('path', 'list')

    data = request.get_json() if request.method == 'POST' else None
    return proxy_to_flexpbx('extensions.php', request.method, data, params)

@app.route('/extensions/<extension_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def extension_details(extension_id):
    """Extension details/update/delete"""
    if request.method in ['PUT', 'DELETE'] and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['id'] = extension_id
    params['path'] = 'details' if request.method == 'GET' else request.method.lower()

    data = request.get_json() if request.method == 'PUT' else None
    return proxy_to_flexpbx('extensions.php', request.method, data, params)

@app.route('/extensions/status/<extension_id>')
@require_auth
def extension_status(extension_id):
    """Extension registration status"""
    params = {'path': 'status', 'id': extension_id}
    return proxy_to_flexpbx('extensions.php', 'GET', None, params)

# Trunks API Routes
@app.route('/trunks', methods=['GET', 'POST'])
@require_auth
def trunks():
    """Trunks list/create"""
    if request.method == 'POST' and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['path'] = params.get('path', 'list')

    data = request.get_json() if request.method == 'POST' else None
    return proxy_to_flexpbx('trunks.php', request.method, data, params)

@app.route('/trunks/<trunk_id>', methods=['GET', 'DELETE'])
@require_auth
def trunk_details(trunk_id):
    """Trunk details/delete"""
    if request.method == 'DELETE' and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['id'] = trunk_id
    params['path'] = 'details' if request.method == 'GET' else 'delete'

    return proxy_to_flexpbx('trunks.php', request.method, None, params)

@app.route('/trunks/status/<trunk_id>')
@require_auth
def trunk_status(trunk_id):
    """Trunk registration status"""
    params = {'path': 'status', 'id': trunk_id}
    return proxy_to_flexpbx('trunks.php', 'GET', None, params)

@app.route('/trunks/test/<trunk_id>', methods=['POST'])
@require_auth
def trunk_test(trunk_id):
    """Test trunk connectivity"""
    params = {'path': 'test', 'id': trunk_id}
    return proxy_to_flexpbx('trunks.php', 'POST', None, params)

# Call Logs API Routes
@app.route('/call-logs', methods=['GET', 'POST'])
@require_auth
def call_logs():
    """Call logs list/search"""
    params = dict(request.args)
    params['path'] = params.get('path', 'list')

    data = request.get_json() if request.method == 'POST' else None
    return proxy_to_flexpbx('call-logs.php', request.method, data, params)

@app.route('/call-logs/recent')
@require_auth
def call_logs_recent():
    """Recent calls"""
    params = dict(request.args)
    params['path'] = 'recent'
    return proxy_to_flexpbx('call-logs.php', 'GET', None, params)

@app.route('/call-logs/statistics')
@require_auth
def call_logs_statistics():
    """Call statistics"""
    params = dict(request.args)
    params['path'] = 'statistics'
    return proxy_to_flexpbx('call-logs.php', 'GET', None, params)

@app.route('/call-logs/export')
@require_auth
def call_logs_export():
    """Export call logs"""
    params = dict(request.args)
    params['path'] = 'export'
    return proxy_to_flexpbx('call-logs.php', 'GET', None, params)

# Voicemail API Routes
@app.route('/voicemail', methods=['GET', 'POST'])
@require_auth
def voicemail():
    """Voicemail boxes list/create"""
    if request.method == 'POST' and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['path'] = params.get('path', 'list')

    data = request.get_json() if request.method == 'POST' else None
    return proxy_to_flexpbx('voicemail.php', request.method, data, params)

@app.route('/voicemail/<mailbox>', methods=['GET', 'DELETE'])
@require_auth
def voicemail_mailbox(mailbox):
    """Mailbox details/delete"""
    if request.method == 'DELETE' and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['mailbox'] = mailbox
    params['path'] = params.get('path', 'settings')

    return proxy_to_flexpbx('voicemail.php', request.method, None, params)

@app.route('/voicemail/messages/<mailbox>')
@require_auth
def voicemail_messages(mailbox):
    """Mailbox messages"""
    params = dict(request.args)
    params['mailbox'] = mailbox
    params['path'] = 'messages'
    return proxy_to_flexpbx('voicemail.php', 'GET', None, params)

@app.route('/voicemail/statistics/<mailbox>')
@require_auth
def voicemail_statistics(mailbox):
    """Mailbox statistics"""
    params = dict(request.args)
    params['mailbox'] = mailbox
    params['path'] = 'statistics'
    return proxy_to_flexpbx('voicemail.php', 'GET', None, params)

# System API Routes
@app.route('/system/<path>')
@require_auth
def system_info(path):
    """System information"""
    if path in ['backup', 'restore'] and not request.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    params = dict(request.args)
    params['path'] = path

    method = 'POST' if path in ['backup', 'restore'] else 'GET'
    data = request.get_json() if method == 'POST' else None

    return proxy_to_flexpbx('system.php', method, data, params)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5018))
    app.run(host='0.0.0.0', port=port, debug=False)
