#!/usr/bin/env python3
"""
Claude Local Sync API
Provides local API endpoint for Claude Code to sync files with CopyParty server
Supports real-time bidirectional sync across all platforms (Mac, Windows, Linux)
"""

import os
import json
import time
import requests
import threading
from flask import Flask, request, jsonify, send_file
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "local_port": 8082,
    "server_host": "127.0.0.1",
    "server_port": 3924,
    "copyparty_username": "admin",
    "copyparty_password": "hub-node-api-2024",
    "sync_config_file": "/home/devinecr/apps/hubnode/backend/copyparty-realtime-sync.json",
    "log_file": "/var/log/claude-local-sync.log",
    "watch_directories": [
        "/home/devinecr/apps/hubnode/api/audio-portrait",
        "/home/tappedin/apps/audio-portrait",
        "/home/devinecr/apps/hubnode/clients",
        "/home/devinecr/apps/hubnode/backend"
    ]
}

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events for real-time sync"""
    
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        
    def on_modified(self, event):
        if not event.is_directory:
            self.sync_manager.queue_sync(event.src_path, 'modified')
            
    def on_created(self, event):
        if not event.is_directory:
            self.sync_manager.queue_sync(event.src_path, 'created')
            
    def on_deleted(self, event):
        if not event.is_directory:
            self.sync_manager.queue_sync(event.src_path, 'deleted')

class SyncManager:
    """Manage bidirectional sync with CopyParty server"""
    
    def __init__(self):
        self.sync_queue = []
        self.sync_lock = threading.Lock()
        self.load_config()
        
    def load_config(self):
        """Load sync configuration from JSON file"""
        try:
            with open(CONFIG["sync_config_file"], 'r') as f:
                self.sync_config = json.load(f)
                logger.info("Loaded sync configuration")
        except Exception as e:
            logger.error(f"Failed to load sync config: {e}")
            self.sync_config = {}
            
    def queue_sync(self, file_path, action):
        """Queue file for sync to server"""
        with self.sync_lock:
            sync_item = {
                "file_path": file_path,
                "action": action,
                "timestamp": time.time()
            }
            self.sync_queue.append(sync_item)
            logger.info(f"Queued {action}: {file_path}")
            
    def process_sync_queue(self):
        """Process queued sync items"""
        while True:
            try:
                if self.sync_queue:
                    with self.sync_lock:
                        item = self.sync_queue.pop(0)
                    self.sync_to_server(item)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Sync queue processing error: {e}")
                
    def sync_to_server(self, item):
        """Sync individual file to CopyParty server"""
        try:
            file_path = item["file_path"]
            action = item["action"]
            
            # Determine CopyParty path mapping
            copyparty_path = self.map_local_to_copyparty(file_path)
            if not copyparty_path:
                return
                
            server_url = f"http://{CONFIG['server_host']}:{CONFIG['server_port']}"
            
            if action in ['created', 'modified']:
                # Upload file to server
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        files = {'file': f}
                        response = requests.post(
                            f"{server_url}{copyparty_path}",
                            files=files,
                            auth=(CONFIG['copyparty_username'], CONFIG['copyparty_password']),
                            timeout=30
                        )
                        if response.status_code == 200:
                            logger.info(f"Synced {action}: {file_path}")
                        else:
                            logger.error(f"Sync failed: {response.status_code}")
                            
            elif action == 'deleted':
                # Delete file from server
                response = requests.delete(
                    f"{server_url}{copyparty_path}",
                    auth=(CONFIG['copyparty_username'], CONFIG['copyparty_password']),
                    timeout=30
                )
                if response.status_code in [200, 404]:
                    logger.info(f"Deleted from server: {file_path}")
                    
        except Exception as e:
            logger.error(f"Sync error for {item['file_path']}: {e}")
            
    def map_local_to_copyparty(self, local_path):
        """Map local file path to CopyParty server path"""
        mappings = {
            "/home/devinecr/apps/hubnode/api/audio-portrait": "/audio-portrait-dist",
            "/home/devinecr/apps/hubnode": "/apps-devinecr/hubnode",
            "/home/devinecr/apps": "/apps-devinecr",
            "/home/tappedin/apps": "/apps-tappedin",
            "/home/dom/apps": "/apps-dom",
            "/home/devinecr": "/devinecr-home",
            "/home/tappedin": "/tappedin-home",
            "/home/dom": "/dom-home",
            "/home/tetoeehoward": "/tetoeehoward-home",
            "/home/wharper": "/wharper-home"
        }
        
        for local_prefix, copyparty_prefix in mappings.items():
            if local_path.startswith(local_prefix):
                relative_path = local_path[len(local_prefix):]
                return f"{copyparty_prefix}{relative_path}"
                
        return None

# Initialize sync manager
sync_manager = SyncManager()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "claude-local-sync",
        "version": "1.0.0",
        "sync_queue_size": len(sync_manager.sync_queue)
    })

@app.route('/sync/status', methods=['GET'])
def sync_status():
    """Get sync status and statistics"""
    return jsonify({
        "sync_config_loaded": bool(sync_manager.sync_config),
        "watch_directories": CONFIG["watch_directories"],
        "queue_size": len(sync_manager.sync_queue),
        "server_url": f"http://{CONFIG['server_host']}:{CONFIG['server_port']}"
    })

@app.route('/sync/upload', methods=['POST'])
def upload_file():
    """Upload file and sync to server"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
            
        # Save file locally
        upload_path = request.form.get('path', '/tmp')
        local_path = os.path.join(upload_path, file.filename)
        file.save(local_path)
        
        # Queue for sync
        sync_manager.queue_sync(local_path, 'created')
        
        return jsonify({
            "message": "File uploaded and queued for sync",
            "local_path": local_path
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sync/force', methods=['POST'])
def force_sync():
    """Force sync of specific directory"""
    try:
        data = request.get_json()
        directory = data.get('directory')
        
        if not directory or not os.path.exists(directory):
            return jsonify({"error": "Invalid directory"}), 400
            
        # Queue all files in directory for sync
        count = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                sync_manager.queue_sync(file_path, 'modified')
                count += 1
                
        return jsonify({
            "message": f"Queued {count} files for sync",
            "directory": directory
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def start_file_watcher():
    """Start file system watcher for real-time sync"""
    observer = Observer()
    handler = FileChangeHandler(sync_manager)
    
    for directory in CONFIG["watch_directories"]:
        if os.path.exists(directory):
            observer.schedule(handler, directory, recursive=True)
            logger.info(f"Watching directory: {directory}")
            
    observer.start()
    logger.info("File watcher started")
    return observer

def main():
    """Main application entry point"""
    logger.info("Starting Claude Local Sync API")
    
    # Start file watcher
    observer = start_file_watcher()
    
    # Start sync queue processor
    sync_thread = threading.Thread(target=sync_manager.process_sync_queue, daemon=True)
    sync_thread.start()
    
    try:
        # Start Flask app
        app.run(
            host='127.0.0.1',
            port=CONFIG["local_port"],
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        observer.stop()
    finally:
        observer.join()

if __name__ == '__main__':
    main()