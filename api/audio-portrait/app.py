#!/usr/bin/env python3
"""
Audio Portrait App API Server
Handles update checking, file uploads, and client management
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import json
import hashlib
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_DIR = '/home/devinecr/apps/hubnode/api/audio-portrait/uploads'
VERSION_FILE = '/home/devinecr/apps/hubnode/api/audio-portrait/version.json'
LOG_FILE = '/home/devinecr/apps/hubnode/api/audio-portrait/access.log'

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_current_version():
    """Get current version from version.json"""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                return json.load(f)
        return {"version": "1.0.0", "build": 1, "release_date": "2025-01-01"}
    except Exception as e:
        logging.error(f"Error reading version file: {e}")
        return {"version": "1.0.0", "build": 1, "release_date": "2025-01-01"}

def update_version(version_data):
    """Update version.json file"""
    try:
        with open(VERSION_FILE, 'w') as f:
            json.dump(version_data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error updating version file: {e}")
        return False

@app.route('/api/audio-portrait/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "audio-portrait-api",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/audio-portrait/version', methods=['GET'])
def get_version():
    """Get current version for update checking"""
    client_version = request.args.get('client_version', '1.0.0')
    client_platform = request.args.get('platform', 'unknown')
    
    logging.info(f"Version check: client={client_version}, platform={client_platform}")
    
    current = get_current_version()
    
    return jsonify({
        "current_version": current["version"],
        "client_version": client_version,
        "update_available": current["version"] != client_version,
        "download_url": f"/api/audio-portrait/download/{client_platform}",
        "release_notes": current.get("release_notes", ""),
        "mandatory": current.get("mandatory", False)
    })

@app.route('/api/audio-portrait/upload', methods=['POST'])
def upload_file():
    """Handle file uploads from Mac development"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Generate secure filename
    filename = file.filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    secure_filename = f"{timestamp}_{filename}"
    
    file_path = os.path.join(UPLOAD_DIR, secure_filename)
    
    try:
        file.save(file_path)
        
        # Calculate file hash for integrity
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        logging.info(f"File uploaded: {secure_filename}, hash: {file_hash}")
        
        return jsonify({
            "success": True,
            "filename": secure_filename,
            "path": file_path,
            "hash": file_hash,
            "size": os.path.getsize(file_path)
        })
    
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return jsonify({"error": "Upload failed"}), 500

@app.route('/api/audio-portrait/download/<platform>', methods=['GET', 'HEAD'])
def download_app(platform):
    """Download app for specific platform"""
    platform_files = {
        'mac': 'Audio Portrait-0.1.0.dmg',
        'mac-arm64': 'Audio Portrait-0.1.0-arm64.dmg', 
        'windows': 'Audio Portrait 0.1.0.exe',
        'darwin': 'Audio Portrait-0.1.0.dmg',  # electron-updater uses 'darwin'
        'win32': 'Audio Portrait 0.1.0.exe'   # electron-updater uses 'win32'
    }
    
    if platform not in platform_files:
        return jsonify({"error": "Platform not supported"}), 404
    
    file_path = os.path.join(UPLOAD_DIR, platform_files[platform])
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not available"}), 404
    
    logging.info(f"Download requested: {platform} -> {platform_files[platform]}")
    return send_file(file_path, as_attachment=True)

@app.route('/api/audio-portrait/config', methods=['GET'])
def get_config():
    """Get client configuration"""
    return jsonify({
        "update_check_interval": 3600,  # 1 hour
        "server_url": "https://api.devinecreations.net",
        "copyparty_url": "https://files.devinecreations.net/audio-portrait/",
        "license_validate_url": "https://api.devinecreations.net/api/audio-portrait/license/validate",
        "support_email": "support@devinecreations.net"
    })

@app.route('/api/audio-portrait/license/validate', methods=['GET', 'POST'])
def validate_license():
    """Validate license key"""
    import subprocess
    import os
    
    # Get license key from request
    license_key = request.args.get('license_key') or request.json.get('license_key') if request.is_json else None
    app_version = request.args.get('app_version') or (request.json.get('app_version') if request.is_json else '')
    platform = request.args.get('platform') or (request.json.get('platform') if request.is_json else 'unknown')
    
    if not license_key:
        return jsonify({
            "status": "error",
            "message": "License key is required",
            "valid": False
        }), 400
    
    # Call PHP validation script
    php_script = os.path.join(os.path.dirname(__file__), 'license_validate.php')
    
    try:
        # Build query string
        query = f"license_key={license_key}&app_version={app_version}&platform={platform}"
        
        # Execute PHP script with query parameters
        result = subprocess.run([
            'php', php_script
        ], capture_output=True, text=True, env={**os.environ, 'QUERY_STRING': query, 'REQUEST_METHOD': 'GET'})
        
        if result.returncode == 0:
            # Parse JSON response from PHP
            import json
            response_data = json.loads(result.stdout)
            return jsonify(response_data)
        else:
            logging.error(f"PHP validation error: {result.stderr}")
            return jsonify({
                "status": "error", 
                "message": "License validation service unavailable",
                "valid": False
            }), 500
            
    except Exception as e:
        logging.error(f"License validation error: {e}")
        return jsonify({
            "status": "error",
            "message": "License validation failed",
            "valid": False
        }), 500

if __name__ == '__main__':
    # Create initial version file if it doesn't exist
    if not os.path.exists(VERSION_FILE):
        initial_version = {
            "version": "1.0.0",
            "build": 1,
            "release_date": datetime.now().isoformat(),
            "release_notes": "Initial release of Audio Portrait App",
            "mandatory": False
        }
        update_version(initial_version)
    
    app.run(host='0.0.0.0', port=5001, debug=False)