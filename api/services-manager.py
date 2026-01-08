#!/usr/bin/env python3
"""
Comprehensive Services Management API
Manages Docker, Jellyfin, Icecast, TeamTalk, CopyParty and all server services
Role-based permissions: admin (devinecr, dom, tappedin) get full access
FlexPBX users get read-only and general commands
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import logging
import pwd

app = Flask(__name__)
CORS(app)

# Configuration
API_PORT = 5017
LOG_FILE = "/var/log/services-manager-api.log"

# Role-based permissions
ADMIN_USERS = ['devinecr', 'dom', 'tappedin', 'admin']
GENERAL_USERS = ['tetoeehoward', 'wharper', 'flexpbx', 'tt']

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

def run_command(cmd, as_user=None, dry_run=False):
    """
    Execute shell command safely
    as_user: Run command as specific user (requires root)
    dry_run: Just return what would be executed
    """
    if dry_run:
        return {"command": cmd, "dry_run": True}

    try:
        if as_user:
            # Run as specific user
            cmd = f"sudo -u {as_user} {cmd}"

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {"success": False, "error": str(e)}

def require_role(allowed_roles=None):
    """Decorator to check user role permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user from API key or header
            user = request.headers.get('X-User') or request.args.get('user', 'anonymous')

            if allowed_roles:
                if user not in allowed_roles and user not in ADMIN_USERS:
                    return jsonify({
                        "error": "Insufficient permissions",
                        "required_roles": allowed_roles,
                        "your_role": user
                    }), 403

            request.current_user = user
            request.is_admin = user in ADMIN_USERS
            return f(*args, **kwargs)

        return decorated_function
    return decorator

# ========== Docker Management ==========

@app.route('/api/services/docker/containers/list', methods=['GET'])
@require_role()
def docker_list_containers():
    """List all Docker containers"""
    result = run_command('docker ps -a --format "{{json .}}"')

    if result.get('success'):
        containers = []
        for line in result['stdout'].strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass

        return jsonify({"containers": containers})

    return jsonify(result), 500

@app.route('/api/services/docker/containers/<container_name>/start', methods=['POST'])
@require_role(ADMIN_USERS)
def docker_start_container(container_name):
    """Start a Docker container (admin only)"""
    result = run_command(f'docker start {container_name}')

    return jsonify({
        "action": "start",
        "container": container_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/docker/containers/<container_name>/stop', methods=['POST'])
@require_role(ADMIN_USERS)
def docker_stop_container(container_name):
    """Stop a Docker container (admin only)"""
    result = run_command(f'docker stop {container_name}')

    return jsonify({
        "action": "stop",
        "container": container_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/docker/containers/<container_name>/restart', methods=['POST'])
@require_role(ADMIN_USERS)
def docker_restart_container(container_name):
    """Restart a Docker container (admin only)"""
    result = run_command(f'docker restart {container_name}')

    return jsonify({
        "action": "restart",
        "container": container_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/docker/containers/<container_name>/logs', methods=['GET'])
@require_role()
def docker_container_logs(container_name):
    """Get Docker container logs"""
    lines = request.args.get('lines', '100')
    result = run_command(f'docker logs --tail {lines} {container_name}')

    return jsonify({
        "container": container_name,
        "logs": result.get('stdout', '') + result.get('stderr', '')
    })

@app.route('/api/services/docker/containers/<container_name>/stats', methods=['GET'])
@require_role()
def docker_container_stats(container_name):
    """Get Docker container stats"""
    result = run_command(f'docker stats {container_name} --no-stream --format "{{{{json .}}}}"')

    if result.get('success'):
        try:
            stats = json.loads(result['stdout'])
            return jsonify(stats)
        except:
            pass

    return jsonify(result), 500

@app.route('/api/services/docker/system/prune', methods=['POST'])
@require_role(ADMIN_USERS)
def docker_system_prune():
    """Clean up Docker system (admin only)"""
    force = request.args.get('force', 'false').lower() == 'true'
    cmd = 'docker system prune -f' if force else 'docker system prune'

    result = run_command(cmd)

    return jsonify({
        "action": "system_prune",
        **result
    }), 200 if result.get('success') else 500

# ========== Jellyfin Management ==========

@app.route('/api/services/jellyfin/status', methods=['GET'])
@require_role()
def jellyfin_status():
    """Get Jellyfin server status"""
    # Check if Jellyfin process is running
    result = run_command('ps aux | grep "[j]ellyfin" | grep -v grep')

    running = result.get('success') and result.get('stdout', '').strip() != ''

    # Try to get Jellyfin info via HTTP
    jellyfin_info = {}
    if running:
        try:
            resp = requests.get('http://localhost:8096/System/Info', timeout=5)
            if resp.status_code == 200:
                jellyfin_info = resp.json()
        except:
            pass

    return jsonify({
        "service": "jellyfin",
        "running": running,
        "process_info": result.get('stdout', '').strip(),
        "system_info": jellyfin_info
    })

@app.route('/api/services/jellyfin/restart', methods=['POST'])
@require_role(ADMIN_USERS)
def jellyfin_restart():
    """Restart Jellyfin server (admin only)"""
    # Kill existing Jellyfin process
    kill_result = run_command('pkill -9 jellyfin')

    # Start Jellyfin as dom user
    start_cmd = '/home/dom/apps/jellyfin/jellyfin/jellyfin --datadir /home/dom/.config/jellyfin --cachedir /home/dom/.cache/jellyfin --webdir /home/dom/apps/jellyfin/jellyfin/jellyfin-web &'
    start_result = run_command(start_cmd, as_user='dom')

    return jsonify({
        "action": "restart",
        "service": "jellyfin",
        "kill_result": kill_result,
        "start_result": start_result
    })

# ========== Icecast Management ==========

@app.route('/api/services/icecast/list', methods=['GET'])
@require_role()
def icecast_list():
    """List all Icecast instances"""
    result = run_command('ps aux | grep "[i]cecast"')

    instances = []
    if result.get('success'):
        for line in result.get('stdout', '').split('\n'):
            if 'icecast' in line:
                parts = line.split()
                if len(parts) > 10:
                    instances.append({
                        'user': parts[0],
                        'pid': parts[1],
                        'config': next((p for p in parts if p.endswith('.xml')), None)
                    })

    return jsonify({"instances": instances})

@app.route('/api/services/icecast/<username>/status', methods=['GET'])
@require_role()
def icecast_user_status(username):
    """Get Icecast status for specific user"""
    if not request.is_admin and request.current_user != username:
        return jsonify({"error": "Can only check your own Icecast instance"}), 403

    result = run_command(f'ps aux | grep "[i]cecast" | grep {username}')

    running = result.get('success') and result.get('stdout', '').strip() != ''

    # Try to get Icecast stats
    stats = {}
    if running:
        try:
            # Try common Icecast admin ports
            for port in [8000, 8001, 8002]:
                try:
                    resp = requests.get(f'http://localhost:{port}/admin/stats', timeout=2)
                    if resp.status_code == 200:
                        stats[f'port_{port}'] = resp.text
                        break
                except:
                    continue
        except:
            pass

    return jsonify({
        "user": username,
        "running": running,
        "process_info": result.get('stdout', '').strip(),
        "stats": stats
    })

@app.route('/api/services/icecast/<username>/restart', methods=['POST'])
@require_role()
def icecast_user_restart(username):
    """Restart Icecast for specific user"""
    if not request.is_admin and request.current_user != username:
        return jsonify({"error": "Can only restart your own Icecast instance"}), 403

    # Kill user's Icecast process
    kill_result = run_command(f'pkill -9 -u {username} icecast')

    # Start Icecast based on user
    config_path = f'/home/{username}/icecast_config/icecast.xml'
    if username == 'dom':
        config_path = '/home/linuxbrew/.linuxbrew/etc/icecast.xml'

    start_cmd = f'/home/linuxbrew/.linuxbrew/bin/icecast -c {config_path} -b &'
    start_result = run_command(start_cmd, as_user=username)

    return jsonify({
        "action": "restart",
        "user": username,
        "kill_result": kill_result,
        "start_result": start_result
    })

# ========== TeamTalk Management ==========

@app.route('/api/services/teamtalk/servers/list', methods=['GET'])
@require_role()
def teamtalk_list_servers():
    """List all TeamTalk servers"""
    result = run_command('tt list')

    servers = []
    if result.get('success'):
        # Parse tt list output
        for line in result.get('stdout', '').split('\n'):
            if line.strip() and not line.startswith('tt -'):
                servers.append(line.strip())

    return jsonify({
        "servers": servers,
        "raw_output": result.get('stdout', '')
    })

@app.route('/api/services/teamtalk/servers/<server_name>/status', methods=['GET'])
@require_role()
def teamtalk_server_status(server_name):
    """Get TeamTalk server status"""
    result = run_command(f'tt rlist {server_name}')

    return jsonify({
        "server": server_name,
        "status": result.get('stdout', '').strip(),
        "running": 'running' in result.get('stdout', '').lower()
    })

@app.route('/api/services/teamtalk/servers/<server_name>/start', methods=['POST'])
@require_role(ADMIN_USERS)
def teamtalk_start_server(server_name):
    """Start TeamTalk server (admin only)"""
    result = run_command(f'tt start {server_name}')

    return jsonify({
        "action": "start",
        "server": server_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/teamtalk/servers/<server_name>/stop', methods=['POST'])
@require_role(ADMIN_USERS)
def teamtalk_stop_server(server_name):
    """Stop TeamTalk server (admin only)"""
    result = run_command(f'tt stop {server_name}')

    return jsonify({
        "action": "stop",
        "server": server_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/teamtalk/servers/<server_name>/restart', methods=['POST'])
@require_role(ADMIN_USERS)
def teamtalk_restart_server(server_name):
    """Restart TeamTalk server (admin only)"""
    result = run_command(f'tt restart {server_name}')

    return jsonify({
        "action": "restart",
        "server": server_name,
        **result
    }), 200 if result.get('success') else 500

@app.route('/api/services/teamtalk/servers/<server_name>/logs', methods=['GET'])
@require_role()
def teamtalk_server_logs(server_name):
    """Get TeamTalk server logs"""
    lines = request.args.get('lines', '100')
    result = run_command(f'tt logcat {server_name} | tail -n {lines}')

    return jsonify({
        "server": server_name,
        "logs": result.get('stdout', '')
    })

@app.route('/api/services/teamtalk/commands', methods=['GET'])
@require_role()
def teamtalk_commands():
    """Get available TeamTalk commands"""
    result = run_command('tt help')

    return jsonify({
        "help": result.get('stdout', ''),
        "note": "Admin users get full access, general users get read-only commands"
    })

# ========== CopyParty Integration ==========

@app.route('/api/services/copyparty/instances', methods=['GET'])
@require_role()
def copyparty_instances():
    """List CopyParty instances"""
    result = run_command('ps aux | grep "[c]opyparty"')

    instances = []
    if result.get('success'):
        for line in result.get('stdout', '').split('\n'):
            if 'copyparty' in line:
                # Parse port from command line
                port = None
                if '-p ' in line:
                    parts = line.split('-p ')
                    if len(parts) > 1:
                        port = parts[1].split()[0]

                instances.append({
                    'pid': line.split()[1] if len(line.split()) > 1 else None,
                    'port': port,
                    'command': ' '.join(line.split()[10:]) if len(line.split()) > 10 else line
                })

    return jsonify({"instances": instances})

@app.route('/api/services/copyparty/admin', methods=['GET'])
@require_role(ADMIN_USERS)
def copyparty_admin_access():
    """Get CopyParty admin access info (admin only)"""
    return jsonify({
        "admin_instance": "http://localhost:3923",
        "public_instance": "http://localhost:3924",
        "web_access": [
            "https://files.raywonderis.me",
            "https://files.devinecreations.net",
            "https://files.devine-creations.com"
        ],
        "credentials": {
            "admin": "Use credentials from /home/COPYPARTY_CREDENTIALS.json"
        }
    })

# ========== File Permissions Management ==========

@app.route('/api/services/fix-permissions/<username>', methods=['POST'])
@require_role()
def fix_user_permissions(username):
    """
    Fix file permissions for user's home directory
    JSON body:
      - path: Relative path (default: entire home)
      - recursive: true|false (default: true)
    """
    # Users can only fix their own permissions unless admin
    if not request.is_admin and request.current_user != username:
        return jsonify({"error": "Can only fix your own permissions"}), 403

    # Valid users
    valid_users = ['dom', 'devinecr', 'tappedin', 'tetoeehoward', 'wharper']
    if username not in valid_users:
        return jsonify({"error": "Invalid user"}), 400

    data = request.get_json() or {}
    rel_path = data.get('path', '')
    recursive = data.get('recursive', True)

    # Construct path
    home_path = f"/home/{username}"
    if rel_path:
        target_path = os.path.join(home_path, rel_path.lstrip('/'))
    else:
        target_path = home_path

    # Validate path exists
    if not os.path.exists(target_path):
        return jsonify({"error": "Path not found"}), 404

    try:
        fixed_count = 0

        if recursive:
            # Use chown -R for recursive operation
            result = run_command(f'chown -R {username}:{username} {target_path}')

            if result.get('success'):
                # Count files
                for root, dirs, files in os.walk(target_path):
                    fixed_count += len(files) + len(dirs)

                logger.info(f"Fixed permissions recursively for {username} at {target_path}")

                return jsonify({
                    "status": "success",
                    "username": username,
                    "path": target_path,
                    "recursive": True,
                    "fixed_count": fixed_count,
                    "message": f"Fixed permissions for {fixed_count} items"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "error": result.get('stderr', 'Unknown error')
                }), 500
        else:
            # Single file/directory
            result = run_command(f'chown {username}:{username} {target_path}')

            if result.get('success'):
                fixed_count = 1
                logger.info(f"Fixed permissions for {username} at {target_path}")

                return jsonify({
                    "status": "success",
                    "username": username,
                    "path": target_path,
                    "recursive": False,
                    "fixed_count": 1
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "error": result.get('stderr', 'Unknown error')
                }), 500

    except Exception as e:
        logger.error(f"Fix permissions error for {username}: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/services/fix-permissions/composr', methods=['POST'])
@require_role(ADMIN_USERS)
def fix_composr_permissions():
    """
    Fix Composr installation permissions (admin only)
    JSON body:
      - path: Composr path (default: /home/devinecr/devinecreations.net)
    """
    data = request.get_json() or {}
    composr_path = data.get('path', '/home/devinecr/devinecreations.net')

    if not os.path.exists(composr_path):
        return jsonify({"error": "Composr path not found"}), 404

    try:
        # Fix ownership
        result = run_command(f'chown -R devinecr:devinecr {composr_path}')

        if result.get('success'):
            # Count files
            fixed_count = 0
            for root, dirs, files in os.walk(composr_path):
                fixed_count += len(files) + len(dirs)

            logger.info(f"Fixed Composr permissions at {composr_path}")

            return jsonify({
                "status": "success",
                "path": composr_path,
                "owner": "devinecr:devinecr",
                "fixed_count": fixed_count,
                "message": f"Fixed permissions for {fixed_count} items"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "error": result.get('stderr', 'Unknown error')
            }), 500

    except Exception as e:
        logger.error(f"Fix Composr permissions error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ========== System Services ==========

@app.route('/api/services/system/status', methods=['GET'])
@require_role()
def system_status():
    """Get overall system status"""
    services = {}

    # Check key services
    for service in ['apache2', 'nginx', 'mysql', 'postgresql', 'redis']:
        result = run_command(f'systemctl is-active {service}')
        services[service] = {
            'active': result.get('stdout', '').strip() == 'active',
            'status': result.get('stdout', '').strip()
        }

    # Get load average
    load_result = run_command('uptime')

    # Get disk usage
    disk_result = run_command('df -h /')

    return jsonify({
        "services": services,
        "load_average": load_result.get('stdout', '').strip(),
        "disk_usage": disk_result.get('stdout', '').strip(),
        "timestamp": datetime.now().isoformat()
    })

# ========== Health and Info ==========

@app.route('/api/services/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "service": "services-manager-api",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/services/restart', methods=['POST'])
@require_role(ADMIN_USERS)
def restart_api():
    """Restart the Services Manager API service (admin only)"""
    try:
        # Restart the systemd service
        result = run_command('systemctl restart services-manager-api.service')

        if result.get('success'):
            return jsonify({
                "status": "success",
                "message": "Services Manager API service restart initiated",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to restart service",
                "error": result.get('stderr', '')
            }), 500
    except Exception as e:
        logger.error(f"Restart error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/services/info', methods=['GET'])
def info():
    """API information"""
    return jsonify({
        "name": "HubNode Services Management API",
        "version": "1.0.0",
        "port": API_PORT,
        "permissions": {
            "admin_users": ADMIN_USERS,
            "general_users": GENERAL_USERS
        },
        "services": {
            "docker": "Container management",
            "jellyfin": "Media server management",
            "icecast": "Streaming server management",
            "teamtalk": "TeamTalk server management",
            "copyparty": "File server information",
            "system": "System services status"
        },
        "endpoints": {
            "docker": {
                "list": "GET /api/services/docker/containers/list",
                "start": "POST /api/services/docker/containers/<name>/start (admin)",
                "stop": "POST /api/services/docker/containers/<name>/stop (admin)",
                "restart": "POST /api/services/docker/containers/<name>/restart (admin)",
                "logs": "GET /api/services/docker/containers/<name>/logs",
                "stats": "GET /api/services/docker/containers/<name>/stats"
            },
            "jellyfin": {
                "status": "GET /api/services/jellyfin/status",
                "restart": "POST /api/services/jellyfin/restart (admin)"
            },
            "icecast": {
                "list": "GET /api/services/icecast/list",
                "status": "GET /api/services/icecast/<user>/status",
                "restart": "POST /api/services/icecast/<user>/restart"
            },
            "teamtalk": {
                "list": "GET /api/services/teamtalk/servers/list",
                "status": "GET /api/services/teamtalk/servers/<name>/status",
                "start": "POST /api/services/teamtalk/servers/<name>/start (admin)",
                "stop": "POST /api/services/teamtalk/servers/<name>/stop (admin)",
                "restart": "POST /api/services/teamtalk/servers/<name>/restart (admin)",
                "logs": "GET /api/services/teamtalk/servers/<name>/logs"
            },
            "system": {
                "status": "GET /api/services/system/status",
                "restart_api": "POST /api/services/restart (admin)"
            },
            "permissions": {
                "fix_user": "POST /api/services/fix-permissions/<username>",
                "fix_composr": "POST /api/services/fix-permissions/composr (admin)"
            }
        },
        "authentication": {
            "header": "X-User: username",
            "query": "?user=username",
            "admin_users": "Full access to all operations",
            "general_users": "Read-only and user-specific operations"
        }
    })

@app.route('/')
def index():
    """Root endpoint"""
    return info()

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("HubNode Services Management API Starting")
    logger.info("="*60)
    logger.info(f"API Port: {API_PORT}")
    logger.info(f"Admin Users: {', '.join(ADMIN_USERS)}")
    logger.info(f"General Users: {', '.join(GENERAL_USERS)}")
    logger.info("")
    logger.info("Managed Services:")
    logger.info("  - Docker containers")
    logger.info("  - Jellyfin media server")
    logger.info("  - Icecast streaming servers")
    logger.info("  - TeamTalk servers")
    logger.info("  - CopyParty file servers")
    logger.info("  - System services")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=API_PORT, debug=False)
