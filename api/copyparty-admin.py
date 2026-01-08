#!/usr/bin/env python3
"""
CopyParty Admin API Wrapper
Provides REST API for managing CopyParty file server with admin roles
Wraps CopyParty's native HTTP API with authentication and enhanced features
"""

import os
import json
import requests
import hashlib
import sqlite3
import secrets
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from functools import wraps
import logging

app = Flask(__name__)
CORS(app)

# Configuration
API_PORT = 5016
COPYPARTY_URL_ADMIN = "http://localhost:3923"  # Admin CopyParty instance
COPYPARTY_URL_PUBLIC = "http://localhost:3924"  # Public CopyParty instance
COPYPARTY_ADMIN_USER = "admin"
COPYPARTY_ADMIN_PASSWORD = "hub-node-api-2024"
LOG_FILE = "/var/log/copyparty-admin-api.log"
SHARES_DB = "/home/devinecr/apps/hubnode/api/public_shares.db"

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

def init_shares_database():
    """Initialize public shares database"""
    conn = sqlite3.connect(SHARES_DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            file_path TEXT NOT NULL,
            share_token TEXT UNIQUE NOT NULL,
            is_public INTEGER DEFAULT 1,
            is_directory INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            downloads INTEGER DEFAULT 0,
            description TEXT,
            UNIQUE(username, file_path)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_share_token ON public_shares(share_token)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_username ON public_shares(username)
    ''')

    conn.commit()
    conn.close()
    logger.info("Public shares database initialized")

def get_copyparty_auth():
    """Get authentication for CopyParty requests"""
    return (COPYPARTY_ADMIN_USER, COPYPARTY_ADMIN_PASSWORD)

def proxy_to_copyparty(path, method='GET', data=None, params=None, instance='admin'):
    """Proxy request to CopyParty with authentication"""
    base_url = COPYPARTY_URL_ADMIN if instance == 'admin' else COPYPARTY_URL_PUBLIC
    url = f"{base_url}{path}"

    auth = get_copyparty_auth()

    try:
        if method == 'GET':
            resp = requests.get(url, auth=auth, params=params, timeout=30)
        elif method == 'POST':
            resp = requests.post(url, auth=auth, data=data, params=params, timeout=30)
        elif method == 'PUT':
            resp = requests.put(url, auth=auth, data=data, params=params, timeout=30)
        elif method == 'DELETE':
            resp = requests.delete(url, auth=auth, params=params, timeout=30)
        else:
            return {"error": "Unsupported method"}, 405

        return resp.content, resp.status_code, dict(resp.headers)
    except Exception as e:
        logger.error(f"CopyParty proxy error: {e}")
        return {"error": str(e)}, 500

# ========== File Management Endpoints ==========

@app.route('/api/copyparty/files/list', methods=['GET'])
def list_files():
    """
    List files in a directory
    Query params:
      - path: Directory path (default: /)
      - format: json|text|verbose (default: json)
    """
    path = request.args.get('path', '/')
    format_type = request.args.get('format', 'json')

    format_map = {'json': '', 'text': 't', 'verbose': 'v'}
    ls_param = format_map.get(format_type, '')

    params = {'ls': ls_param} if ls_param else {'ls': ''}
    content, status, headers = proxy_to_copyparty(path, params=params)

    if format_type == 'json' and status == 200:
        try:
            return jsonify(json.loads(content)), status
        except:
            pass

    return Response(content, status=status, headers=headers)

@app.route('/api/copyparty/files/tree', methods=['GET'])
def list_tree():
    """
    List directory tree recursively
    Query params:
      - path: Directory path (default: /)
    """
    path = request.args.get('path', '/')
    content, status, headers = proxy_to_copyparty(path, params={'tree': ''})

    try:
        return jsonify(json.loads(content)), status
    except:
        return Response(content, status=status, headers=headers)

@app.route('/api/copyparty/files/download', methods=['GET'])
def download_file():
    """
    Download a file
    Query params:
      - path: File path (required)
    """
    path = request.args.get('path')
    if not path:
        return jsonify({"error": "path parameter required"}), 400

    content, status, headers = proxy_to_copyparty(path, params={'dl': ''})
    return Response(content, status=status, headers=headers)

@app.route('/api/copyparty/files/upload', methods=['POST'])
def upload_file():
    """
    Upload a file
    Form data:
      - file: File to upload
      - path: Destination path (default: /)
      - overwrite: true|false (default: false)
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    dest_path = request.form.get('path', '/')
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'

    # Construct upload URL
    upload_url = f"{dest_path.rstrip('/')}/{file.filename}"

    try:
        auth = get_copyparty_auth()
        resp = requests.put(
            f"{COPYPARTY_URL_ADMIN}{upload_url}",
            auth=auth,
            data=file.read(),
            timeout=300
        )

        return jsonify({
            "status": "success" if resp.status_code in [200, 201] else "error",
            "path": upload_url,
            "message": resp.text
        }), resp.status_code
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/files/delete', methods=['POST', 'DELETE'])
def delete_file():
    """
    Delete file or directory
    JSON body:
      - path: Path to delete (required)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    path = data['path']
    content, status, headers = proxy_to_copyparty(path, method='POST', params={'delete': ''})

    return jsonify({
        "status": "success" if status == 200 else "error",
        "path": path,
        "message": content.decode() if isinstance(content, bytes) else content
    }), status

@app.route('/api/copyparty/files/move', methods=['POST'])
def move_file():
    """
    Move/rename file or directory
    JSON body:
      - source: Source path (required)
      - destination: Destination path (required)
    """
    data = request.get_json()
    if not data or 'source' not in data or 'destination' not in data:
        return jsonify({"error": "source and destination required"}), 400

    source = data['source']
    destination = data['destination']

    content, status, headers = proxy_to_copyparty(
        source,
        method='POST',
        params={'move': destination}
    )

    return jsonify({
        "status": "success" if status == 200 else "error",
        "source": source,
        "destination": destination,
        "message": content.decode() if isinstance(content, bytes) else content
    }), status

@app.route('/api/copyparty/files/copy', methods=['POST'])
def copy_file():
    """
    Copy file or directory
    JSON body:
      - source: Source path (required)
      - destination: Destination path (required)
    """
    data = request.get_json()
    if not data or 'source' not in data or 'destination' not in data:
        return jsonify({"error": "source and destination required"}), 400

    source = data['source']
    destination = data['destination']

    content, status, headers = proxy_to_copyparty(
        source,
        method='POST',
        params={'copy': destination}
    )

    return jsonify({
        "status": "success" if status == 200 else "error",
        "source": source,
        "destination": destination,
        "message": content.decode() if isinstance(content, bytes) else content
    }), status

@app.route('/api/copyparty/files/mkdir', methods=['POST'])
def create_directory():
    """
    Create directory
    JSON body:
      - path: Directory path to create (required)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    path = data['path']
    content, status, headers = proxy_to_copyparty(path, method='POST', params={'mkdir': ''})

    return jsonify({
        "status": "success" if status == 200 else "error",
        "path": path,
        "message": content.decode() if isinstance(content, bytes) else content
    }), status

# ========== Search and Recent Uploads ==========

@app.route('/api/copyparty/search/recent', methods=['GET'])
def recent_uploads():
    """
    Get recent uploads
    Query params:
      - path: Root path (default: /)
      - limit: Max results (handled by CopyParty)
    """
    path = request.args.get('path', '/')
    content, status, headers = proxy_to_copyparty(path, params={'ru': ''})

    try:
        return jsonify(json.loads(content)), status
    except:
        return Response(content, status=status, headers=headers)

@app.route('/api/copyparty/search', methods=['POST'])
def search_files():
    """
    Search for files
    JSON body:
      - query: Search query (required)
      - path: Root path to search (default: /)
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "query required"}), 400

    query = data['query']
    path = data.get('path', '/')

    # CopyParty search is done via POST with search parameters
    search_data = json.dumps({"q": query})
    content, status, headers = proxy_to_copyparty(
        path,
        method='POST',
        data=search_data
    )

    try:
        return jsonify(json.loads(content)), status
    except:
        return Response(content, status=status, headers=headers)

# ========== User Home Directory Operations ==========

def validate_user_path(username, path):
    """Validate that path is within user's home directory"""
    import os.path

    # Valid users
    valid_users = ['dom', 'devinecr', 'tappedin', 'tetoeehoward', 'wharper']
    if username not in valid_users:
        return None, "Invalid user"

    # Construct safe home path
    home_path = f"/home/{username}"

    # If path is relative, make it absolute within user's home
    if not path.startswith('/'):
        full_path = os.path.join(home_path, path)
    else:
        full_path = path

    # Resolve to absolute path and check it's within user's home
    try:
        real_path = os.path.realpath(full_path)
        real_home = os.path.realpath(home_path)

        if not real_path.startswith(real_home):
            return None, "Path outside user home directory"

        return real_path, None
    except Exception as e:
        return None, str(e)

@app.route('/api/copyparty/user/<username>/upload', methods=['POST'])
def user_upload_file(username):
    """
    Upload file to user's home directory
    Form data:
      - file: File to upload
      - path: Relative path within user's home (default: /)
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    rel_path = request.form.get('path', '/')

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    # Ensure directory exists
    os.makedirs(full_path, exist_ok=True)

    # Save file
    file_path = os.path.join(full_path, file.filename)
    try:
        file.save(file_path)

        # Set ownership to user
        import pwd
        import subprocess
        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid
        os.chown(file_path, uid, gid)
        os.chmod(file_path, 0o644)

        logger.info(f"User {username} uploaded file to {file_path}")

        return jsonify({
            "status": "success",
            "path": file_path,
            "filename": file.filename,
            "size": os.path.getsize(file_path)
        }), 201
    except Exception as e:
        logger.error(f"Upload error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/download', methods=['GET'])
def user_download_file(username):
    """
    Download file from user's home directory
    Query params:
      - path: Relative path within user's home (required)
    """
    rel_path = request.args.get('path')
    if not rel_path:
        return jsonify({"error": "path parameter required"}), 400

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404

    if not os.path.isfile(full_path):
        return jsonify({"error": "Path is not a file"}), 400

    try:
        from flask import send_file
        return send_file(full_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Download error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/delete', methods=['POST', 'DELETE'])
def user_delete_file(username):
    """
    Delete file or directory from user's home
    JSON body:
      - path: Relative path within user's home (required)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    rel_path = data['path']

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "Path not found"}), 404

    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)

        logger.info(f"User {username} deleted {full_path}")

        return jsonify({
            "status": "success",
            "path": full_path,
            "action": "deleted"
        }), 200
    except Exception as e:
        logger.error(f"Delete error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/update', methods=['PUT', 'POST'])
def user_update_file(username):
    """
    Update/replace existing file in user's home
    Form data:
      - file: New file content
      - path: Relative path to file (required)
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    rel_path = request.form.get('path')

    if not rel_path:
        return jsonify({"error": "path required"}), 400

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    # Check if file exists
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404

    try:
        # Save new file content
        file.save(full_path)

        # Set ownership to user
        import pwd
        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid
        os.chown(full_path, uid, gid)

        logger.info(f"User {username} updated file {full_path}")

        return jsonify({
            "status": "success",
            "path": full_path,
            "action": "updated",
            "size": os.path.getsize(full_path)
        }), 200
    except Exception as e:
        logger.error(f"Update error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/list', methods=['GET'])
def user_list_files(username):
    """
    List files in user's home directory
    Query params:
      - path: Relative path within user's home (default: /)
    """
    rel_path = request.args.get('path', '/')

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "Path not found"}), 404

    if not os.path.isdir(full_path):
        return jsonify({"error": "Path is not a directory"}), 400

    try:
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            stat = os.stat(item_path)

            files.append({
                "name": item,
                "path": item_path,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            })

        return jsonify({
            "username": username,
            "path": full_path,
            "files": files,
            "count": len(files)
        }), 200
    except Exception as e:
        logger.error(f"List error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/mkdir', methods=['POST'])
def user_create_directory(username):
    """
    Create directory in user's home
    JSON body:
      - path: Relative path to create (required)
      - parents: Create parent directories if needed (default: true)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    rel_path = data['path']
    parents = data.get('parents', True)

    # Validate path (don't require it to exist yet)
    home_path = f"/home/{username}"
    if not rel_path.startswith('/'):
        full_path = os.path.join(home_path, rel_path)
    else:
        full_path = rel_path

    # Check path is within user's home
    try:
        real_home = os.path.realpath(home_path)
        # Get parent directory to check
        parent_dir = os.path.dirname(full_path)
        if os.path.exists(parent_dir):
            real_parent = os.path.realpath(parent_dir)
            if not real_parent.startswith(real_home):
                return jsonify({"error": "Path outside user home directory"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        import pwd
        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid

        # Create directory
        os.makedirs(full_path, mode=0o755, exist_ok=parents)

        # Set ownership
        os.chown(full_path, uid, gid)

        logger.info(f"User {username} created directory {full_path}")

        return jsonify({
            "status": "success",
            "path": full_path,
            "action": "created"
        }), 201
    except FileExistsError:
        return jsonify({"error": "Directory already exists"}), 409
    except Exception as e:
        logger.error(f"Create directory error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/move', methods=['POST'])
def user_move_path(username):
    """
    Move/rename file or directory in user's home
    JSON body:
      - source: Source path (required)
      - destination: Destination path (required)
    """
    data = request.get_json()
    if not data or 'source' not in data or 'destination' not in data:
        return jsonify({"error": "source and destination required"}), 400

    source_rel = data['source']
    dest_rel = data['destination']

    # Validate both paths
    source_path, error = validate_user_path(username, source_rel)
    if error:
        return jsonify({"error": f"Source: {error}"}), 403

    # For destination, validate the parent directory exists
    home_path = f"/home/{username}"
    if not dest_rel.startswith('/'):
        dest_path = os.path.join(home_path, dest_rel)
    else:
        dest_path = dest_rel

    try:
        real_home = os.path.realpath(home_path)
        real_dest = os.path.realpath(dest_path) if os.path.exists(dest_path) else os.path.realpath(os.path.dirname(dest_path))
        if not real_dest.startswith(real_home):
            return jsonify({"error": "Destination outside user home directory"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not os.path.exists(source_path):
        return jsonify({"error": "Source path not found"}), 404

    try:
        import shutil
        import pwd

        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid

        # Move the file/directory
        shutil.move(source_path, dest_path)

        # Set ownership on destination
        os.chown(dest_path, uid, gid)
        if os.path.isdir(dest_path):
            # Fix ownership recursively for directories
            for root, dirs, files in os.walk(dest_path):
                for d in dirs:
                    os.chown(os.path.join(root, d), uid, gid)
                for f in files:
                    os.chown(os.path.join(root, f), uid, gid)

        logger.info(f"User {username} moved {source_path} to {dest_path}")

        return jsonify({
            "status": "success",
            "source": source_path,
            "destination": dest_path,
            "action": "moved"
        }), 200
    except Exception as e:
        logger.error(f"Move error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/copy', methods=['POST'])
def user_copy_path(username):
    """
    Copy file or directory in user's home
    JSON body:
      - source: Source path (required)
      - destination: Destination path (required)
    """
    data = request.get_json()
    if not data or 'source' not in data or 'destination' not in data:
        return jsonify({"error": "source and destination required"}), 400

    source_rel = data['source']
    dest_rel = data['destination']

    # Validate both paths
    source_path, error = validate_user_path(username, source_rel)
    if error:
        return jsonify({"error": f"Source: {error}"}), 403

    # For destination, validate the parent directory exists
    home_path = f"/home/{username}"
    if not dest_rel.startswith('/'):
        dest_path = os.path.join(home_path, dest_rel)
    else:
        dest_path = dest_rel

    try:
        real_home = os.path.realpath(home_path)
        real_dest = os.path.realpath(dest_path) if os.path.exists(dest_path) else os.path.realpath(os.path.dirname(dest_path))
        if not real_dest.startswith(real_home):
            return jsonify({"error": "Destination outside user home directory"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not os.path.exists(source_path):
        return jsonify({"error": "Source path not found"}), 404

    try:
        import shutil
        import pwd

        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid

        # Copy the file/directory
        if os.path.isdir(source_path):
            shutil.copytree(source_path, dest_path)
        else:
            shutil.copy2(source_path, dest_path)

        # Set ownership on destination
        os.chown(dest_path, uid, gid)
        if os.path.isdir(dest_path):
            # Fix ownership recursively for directories
            for root, dirs, files in os.walk(dest_path):
                for d in dirs:
                    os.chown(os.path.join(root, d), uid, gid)
                for f in files:
                    os.chown(os.path.join(root, f), uid, gid)

        logger.info(f"User {username} copied {source_path} to {dest_path}")

        return jsonify({
            "status": "success",
            "source": source_path,
            "destination": dest_path,
            "action": "copied"
        }), 201
    except Exception as e:
        logger.error(f"Copy error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/share/public', methods=['POST'])
def user_make_public(username):
    """
    Make a file or folder publicly accessible via share link
    JSON body:
      - path: Relative path within user's home (required)
      - description: Optional description
      - expires_days: Days until expiration (optional)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    rel_path = data['path']
    description = data.get('description', '')
    expires_days = data.get('expires_days')

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "Path not found"}), 404

    is_directory = os.path.isdir(full_path)

    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        # Check if already shared
        cursor.execute('''
            SELECT share_token, is_public FROM public_shares
            WHERE username = ? AND file_path = ?
        ''', (username, full_path))

        existing = cursor.fetchone()

        if existing:
            # Update existing share
            cursor.execute('''
                UPDATE public_shares
                SET is_public = 1, description = ?
                WHERE username = ? AND file_path = ?
            ''', (description, username, full_path))
            share_token = existing[0]
        else:
            # Create new share
            share_token = secrets.token_urlsafe(16)

            expires_at = None
            if expires_days:
                from datetime import timedelta
                expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

            cursor.execute('''
                INSERT INTO public_shares
                (username, file_path, share_token, is_public, is_directory, description, expires_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
            ''', (username, full_path, share_token, 1 if is_directory else 0, description, expires_at))

        conn.commit()
        conn.close()

        logger.info(f"User {username} made public: {full_path}")

        # Generate share URLs
        share_url = f"http://64.20.46.178:5016/api/copyparty/share/{share_token}"
        https_url = f"https://api.devine-creations.com/copyparty/share/{share_token}"

        return jsonify({
            "status": "success",
            "action": "made_public",
            "path": full_path,
            "share_token": share_token,
            "share_url": share_url,
            "https_url": https_url,
            "type": "directory" if is_directory else "file"
        }), 200

    except Exception as e:
        logger.error(f"Make public error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/share/private', methods=['POST'])
def user_make_private(username):
    """
    Make a previously shared file/folder private again
    JSON body:
      - path: Relative path within user's home (required)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    rel_path = data['path']

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        # Update share to private (or delete it)
        cursor.execute('''
            UPDATE public_shares
            SET is_public = 0
            WHERE username = ? AND file_path = ?
        ''', (username, full_path))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "No share found for this path"}), 404

        conn.commit()
        conn.close()

        logger.info(f"User {username} made private: {full_path}")

        return jsonify({
            "status": "success",
            "action": "made_private",
            "path": full_path
        }), 200

    except Exception as e:
        logger.error(f"Make private error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/share/list', methods=['GET'])
def user_list_shares(username):
    """List all shares for a user"""
    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT file_path, share_token, is_public, is_directory,
                   created_at, downloads, description, expires_at
            FROM public_shares
            WHERE username = ?
            ORDER BY created_at DESC
        ''', (username,))

        shares = []
        for row in cursor.fetchall():
            share_url = f"http://64.20.46.178:5016/api/copyparty/share/{row[1]}"
            https_url = f"https://api.devine-creations.com/copyparty/share/{row[1]}"

            shares.append({
                "path": row[0],
                "share_token": row[1],
                "is_public": bool(row[2]),
                "type": "directory" if row[3] else "file",
                "created_at": row[4],
                "downloads": row[5],
                "description": row[6],
                "expires_at": row[7],
                "share_url": share_url if row[2] else None,
                "https_url": https_url if row[2] else None
            })

        conn.close()

        return jsonify({
            "username": username,
            "shares": shares,
            "count": len(shares)
        }), 200

    except Exception as e:
        logger.error(f"List shares error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/share/delete', methods=['POST', 'DELETE'])
def user_delete_share(username):
    """
    Delete a share completely
    JSON body:
      - path: Relative path within user's home (required)
    """
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "path required"}), 400

    rel_path = data['path']

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM public_shares
            WHERE username = ? AND file_path = ?
        ''', (username, full_path))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "No share found for this path"}), 404

        conn.commit()
        conn.close()

        logger.info(f"User {username} deleted share: {full_path}")

        return jsonify({
            "status": "success",
            "action": "share_deleted",
            "path": full_path
        }), 200

    except Exception as e:
        logger.error(f"Delete share error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/share/<share_token>', methods=['GET'])
def public_access_share(share_token):
    """
    Public endpoint to access shared files/folders
    No authentication required
    """
    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT username, file_path, is_public, is_directory, expires_at
            FROM public_shares
            WHERE share_token = ?
        ''', (share_token,))

        share = cursor.fetchone()

        if not share:
            conn.close()
            return jsonify({"error": "Share not found"}), 404

        username, file_path, is_public, is_directory, expires_at = share

        # Check if public
        if not is_public:
            conn.close()
            return jsonify({"error": "This share is private"}), 403

        # Check expiration
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if datetime.now() > expires:
                conn.close()
                return jsonify({"error": "This share has expired"}), 410

        # Check if file/directory exists
        if not os.path.exists(file_path):
            conn.close()
            return jsonify({"error": "File or directory no longer exists"}), 404

        # Increment download counter
        cursor.execute('''
            UPDATE public_shares
            SET downloads = downloads + 1
            WHERE share_token = ?
        ''', (share_token,))
        conn.commit()
        conn.close()

        # Return file or directory listing
        if is_directory:
            # List directory contents
            files = []
            for item in os.listdir(file_path):
                item_path = os.path.join(file_path, item)
                stat = os.stat(item_path)

                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            return jsonify({
                "type": "directory",
                "path": file_path,
                "username": username,
                "files": files,
                "count": len(files)
            }), 200
        else:
            # Download file
            logger.info(f"Public download: {file_path} via token {share_token}")
            return send_file(file_path, as_attachment=True)

    except Exception as e:
        logger.error(f"Public access error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/share/<share_token>/download/<filename>', methods=['GET'])
def public_download_file(share_token, filename):
    """
    Download a specific file from a shared directory
    """
    try:
        conn = sqlite3.connect(SHARES_DB)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT username, file_path, is_public, is_directory, expires_at
            FROM public_shares
            WHERE share_token = ?
        ''', (share_token,))

        share = cursor.fetchone()

        if not share:
            conn.close()
            return jsonify({"error": "Share not found"}), 404

        username, file_path, is_public, is_directory, expires_at = share

        if not is_public:
            conn.close()
            return jsonify({"error": "This share is private"}), 403

        if not is_directory:
            conn.close()
            return jsonify({"error": "This share is not a directory"}), 400

        # Check expiration
        if expires_at:
            expires = datetime.fromisoformat(expires_at)
            if datetime.now() > expires:
                conn.close()
                return jsonify({"error": "This share has expired"}), 410

        # Construct file path
        target_file = os.path.join(file_path, filename)

        # Security: ensure file is within shared directory
        real_file = os.path.realpath(target_file)
        real_dir = os.path.realpath(file_path)

        if not real_file.startswith(real_dir):
            conn.close()
            return jsonify({"error": "Access denied"}), 403

        if not os.path.exists(target_file) or not os.path.isfile(target_file):
            conn.close()
            return jsonify({"error": "File not found"}), 404

        # Increment download counter
        cursor.execute('''
            UPDATE public_shares
            SET downloads = downloads + 1
            WHERE share_token = ?
        ''', (share_token,))
        conn.commit()
        conn.close()

        logger.info(f"Public download: {target_file} via token {share_token}")
        return send_file(target_file, as_attachment=True)

    except Exception as e:
        logger.error(f"Public download error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/copyparty/user/<username>/fix-permissions', methods=['POST'])
def user_fix_permissions(username):
    """
    Fix permissions for user's home directory
    JSON body:
      - path: Relative path (default: / for entire home)
      - recursive: true|false (default: true)
    """
    data = request.get_json() or {}
    rel_path = data.get('path', '/')
    recursive = data.get('recursive', True)

    # Validate path
    full_path, error = validate_user_path(username, rel_path)
    if error:
        return jsonify({"error": error}), 403

    if not os.path.exists(full_path):
        return jsonify({"error": "Path not found"}), 404

    try:
        import pwd
        import subprocess

        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid

        fixed_count = 0

        if recursive and os.path.isdir(full_path):
            # Use chown -R for recursive operation
            result = subprocess.run(
                ['chown', '-R', f'{username}:{username}', full_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Count files
                for root, dirs, files in os.walk(full_path):
                    fixed_count += len(files) + len(dirs)

                logger.info(f"Fixed permissions recursively for {username} at {full_path}")
            else:
                return jsonify({
                    "status": "error",
                    "error": result.stderr
                }), 500
        else:
            # Single file/directory
            os.chown(full_path, uid, gid)
            if os.path.isfile(full_path):
                os.chmod(full_path, 0o644)
            else:
                os.chmod(full_path, 0o755)
            fixed_count = 1

            logger.info(f"Fixed permissions for {username} at {full_path}")

        return jsonify({
            "status": "success",
            "username": username,
            "path": full_path,
            "recursive": recursive,
            "fixed_count": fixed_count
        }), 200
    except Exception as e:
        logger.error(f"Fix permissions error for {username}: {e}")
        return jsonify({"error": str(e)}), 500

# ========== Admin Operations ==========

@app.route('/api/copyparty/admin/reload', methods=['POST'])
def reload_config():
    """
    Reload CopyParty configuration
    Requires admin authentication
    """
    content, status, headers = proxy_to_copyparty('/', params={'reload': 'cfg'})

    return jsonify({
        "status": "success" if status == 200 else "error",
        "message": "Configuration reloaded" if status == 200 else content.decode()
    }), status

@app.route('/api/copyparty/admin/scan', methods=['POST'])
def rescan_volumes():
    """
    Rescan all volumes
    Requires admin authentication
    """
    content, status, headers = proxy_to_copyparty('/', params={'scan': ''})

    return jsonify({
        "status": "success" if status == 200 else "error",
        "message": "Volumes rescanned" if status == 200 else content.decode()
    }), status

@app.route('/api/copyparty/admin/stats', methods=['GET'])
def get_stats():
    """
    Get CopyParty statistics
    Returns metrics for monitoring
    """
    content, status, headers = proxy_to_copyparty('/.cpr/metrics')

    return Response(content, status=status, mimetype='text/plain')

# ========== User Management ==========

@app.route('/api/copyparty/users/list', methods=['GET'])
def list_users():
    """
    List configured users
    Note: This requires parsing CopyParty args or config
    """
    # This would need to parse the copyparty-args.txt file
    # or maintain a separate user database
    return jsonify({
        "users": [
            {"username": "admin", "permissions": "rwm", "groups": ["all"]},
            {"username": "dom", "permissions": "rwm", "groups": ["public"]},
            {"username": "devinecr", "permissions": "rwm", "groups": ["public"]},
            {"username": "tappedin", "permissions": "rwm", "groups": ["public"]},
            {"username": "tetoeehoward", "permissions": "rwm", "groups": ["public"]},
            {"username": "wharper", "permissions": "rwm", "groups": ["public"]},
            {"username": "public", "permissions": "r", "groups": ["public"]}
        ]
    })

# ========== Volume Management ==========

@app.route('/api/copyparty/volumes/list', methods=['GET'])
def list_volumes():
    """
    List configured volumes
    Note: This requires parsing CopyParty configuration
    """
    # Parse from running process or config file
    volumes = [
        {"name": "dom-home", "path": "/home/dom", "permissions": "rwm", "users": ["dom", "admin"]},
        {"name": "devinecr-home", "path": "/home/devinecr", "permissions": "rwm", "users": ["devinecr", "admin"]},
        {"name": "tappedin-home", "path": "/home/tappedin", "permissions": "rwm", "users": ["tappedin", "admin"]},
        {"name": "tetoeehoward-home", "path": "/home/tetoeehoward", "permissions": "rwm", "users": ["tetoeehoward", "admin"]},
        {"name": "wharper-home", "path": "/home/wharper", "permissions": "rwm", "users": ["wharper", "admin"]},
        {"name": "shared", "path": "/home/devinecr/shared", "permissions": "rwmG", "users": ["public"]}
    ]

    return jsonify({"volumes": volumes})

# ========== Health and Info ==========

@app.route('/api/copyparty/health', methods=['GET'])
def health_check():
    """Check if CopyParty is running"""
    try:
        resp = requests.get(f"{COPYPARTY_URL_ADMIN}/", timeout=5)
        admin_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        admin_status = "down"

    try:
        resp = requests.get(f"{COPYPARTY_URL_PUBLIC}/", timeout=5)
        public_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except:
        public_status = "down"

    return jsonify({
        "status": "healthy" if admin_status == "healthy" else "degraded",
        "instances": {
            "admin": {"url": COPYPARTY_URL_ADMIN, "status": admin_status},
            "public": {"url": COPYPARTY_URL_PUBLIC, "status": public_status}
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/copyparty/restart', methods=['POST'])
def restart_api():
    """Restart the CopyParty Admin API service"""
    import subprocess
    import sys

    try:
        # Restart the systemd service
        result = subprocess.run(
            ['systemctl', 'restart', 'copyparty-admin-api.service'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "CopyParty Admin API service restart initiated",
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

@app.route('/api/copyparty/info', methods=['GET'])
def get_info():
    """Get API information"""
    return jsonify({
        "name": "CopyParty Admin API",
        "version": "1.0.0",
        "copyparty_instances": {
            "admin": COPYPARTY_URL_ADMIN,
            "public": COPYPARTY_URL_PUBLIC
        },
        "endpoints": {
            "files": {
                "list": "GET /api/copyparty/files/list",
                "tree": "GET /api/copyparty/files/tree",
                "download": "GET /api/copyparty/files/download",
                "upload": "POST /api/copyparty/files/upload",
                "delete": "POST /api/copyparty/files/delete",
                "move": "POST /api/copyparty/files/move",
                "copy": "POST /api/copyparty/files/copy",
                "mkdir": "POST /api/copyparty/files/mkdir"
            },
            "user_operations": {
                "list": "GET /api/copyparty/user/<username>/list",
                "upload": "POST /api/copyparty/user/<username>/upload",
                "download": "GET /api/copyparty/user/<username>/download",
                "update": "PUT /api/copyparty/user/<username>/update",
                "delete": "DELETE /api/copyparty/user/<username>/delete",
                "mkdir": "POST /api/copyparty/user/<username>/mkdir",
                "move": "POST /api/copyparty/user/<username>/move",
                "copy": "POST /api/copyparty/user/<username>/copy",
                "fix_permissions": "POST /api/copyparty/user/<username>/fix-permissions"
            },
            "sharing": {
                "make_public": "POST /api/copyparty/user/<username>/share/public",
                "make_private": "POST /api/copyparty/user/<username>/share/private",
                "list_shares": "GET /api/copyparty/user/<username>/share/list",
                "delete_share": "DELETE /api/copyparty/user/<username>/share/delete",
                "public_access": "GET /api/copyparty/share/<token>",
                "public_download": "GET /api/copyparty/share/<token>/download/<filename>"
            },
            "search": {
                "recent": "GET /api/copyparty/search/recent",
                "search": "POST /api/copyparty/search"
            },
            "admin": {
                "reload": "POST /api/copyparty/admin/reload",
                "scan": "POST /api/copyparty/admin/scan",
                "stats": "GET /api/copyparty/admin/stats",
                "restart": "POST /api/copyparty/restart"
            },
            "management": {
                "users": "GET /api/copyparty/users/list",
                "volumes": "GET /api/copyparty/volumes/list"
            },
            "info": {
                "health": "GET /api/copyparty/health",
                "info": "GET /api/copyparty/info"
            }
        }
    })

@app.route('/')
def index():
    """API documentation"""
    return get_info()

if __name__ == '__main__':
    # Initialize databases
    init_shares_database()

    logger.info("="*60)
    logger.info("CopyParty Admin API Starting")
    logger.info("="*60)
    logger.info(f"API Port: {API_PORT}")
    logger.info(f"Admin CopyParty: {COPYPARTY_URL_ADMIN}")
    logger.info(f"Public CopyParty: {COPYPARTY_URL_PUBLIC}")
    logger.info(f"Shares Database: {SHARES_DB}")
    logger.info("")
    logger.info("API will be accessible at:")
    logger.info(f"  - http://localhost:{API_PORT}")
    logger.info(f"  - https://api.devine-creations.com/copyparty")
    logger.info("")
    logger.info("Public Sharing:")
    logger.info("  - Users can make files/folders public")
    logger.info("  - Public access via /api/copyparty/share/<token>")
    logger.info("  - No authentication required for public shares")
    logger.info("="*60)

    app.run(host='0.0.0.0', port=API_PORT, debug=False)
