#!/usr/bin/env python3
"""
User Logs Collection API for App Installers
Receives logs, crash reports, and usage data from installed apps
"""

import os
import json
import time
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Configuration
LOG_DIR = "/home/devinecr/apps/hubnode/api/user-logs"
DB_PATH = "/home/devinecr/apps/hubnode/api/user-logs.db"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB max per log file

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/user-logs-api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize SQLite database for log metadata"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            app_version TEXT,
            user_id TEXT,
            log_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            user_agent TEXT,
            ip_address TEXT,
            system_info TEXT,
            log_size INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            app_version TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            ip_address TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/logs/submit', methods=['POST'])
def submit_log():
    """Submit log files from installed apps"""
    try:
        # Get metadata
        app_name = request.form.get('app_name', 'unknown')
        app_version = request.form.get('app_version', 'unknown')
        user_id = request.form.get('user_id', 'anonymous')
        log_type = request.form.get('log_type', 'general')
        system_info = request.form.get('system_info', '{}')
        
        # Validate required fields
        if not app_name or app_name == 'unknown':
            return jsonify({"error": "app_name is required"}), 400
        
        # Handle file upload
        if 'log_file' in request.files:
            log_file = request.files['log_file']
            if log_file.filename and log_file.content_length <= MAX_LOG_SIZE:
                # Create secure filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{secure_filename(app_name)}_{app_version}_{log_type}_{timestamp}.log"
                filepath = os.path.join(LOG_DIR, filename)
                
                # Save file
                log_file.save(filepath)
                
                # Store metadata in database
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO log_entries 
                    (app_name, app_version, user_id, log_type, file_path, 
                     user_agent, ip_address, system_info, log_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app_name, app_version, user_id, log_type, filepath,
                    request.headers.get('User-Agent', ''),
                    request.remote_addr,
                    system_info,
                    log_file.content_length
                ))
                conn.commit()
                conn.close()
                
                logger.info(f"Log received: {app_name} v{app_version} from {request.remote_addr}")
                return jsonify({
                    "status": "success",
                    "message": "Log file received",
                    "log_id": cursor.lastrowid
                })
            else:
                return jsonify({"error": "File too large or empty"}), 400
        
        # Handle text log data
        elif 'log_data' in request.form:
            log_data = request.form.get('log_data')
            if len(log_data) > MAX_LOG_SIZE:
                return jsonify({"error": "Log data too large"}), 400
            
            # Save text data to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{secure_filename(app_name)}_{app_version}_{log_type}_{timestamp}.log"
            filepath = os.path.join(LOG_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_data)
            
            # Store metadata
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO log_entries 
                (app_name, app_version, user_id, log_type, file_path, 
                 user_agent, ip_address, system_info, log_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_name, app_version, user_id, log_type, filepath,
                request.headers.get('User-Agent', ''),
                request.remote_addr,
                system_info,
                len(log_data)
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"Log data received: {app_name} v{app_version} from {request.remote_addr}")
            return jsonify({
                "status": "success", 
                "message": "Log data received",
                "log_id": cursor.lastrowid
            })
        else:
            return jsonify({"error": "No log file or data provided"}), 400
            
    except Exception as e:
        logger.error(f"Error processing log submission: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/stats/event', methods=['POST'])
def log_event():
    """Log usage events and statistics"""
    try:
        data = request.get_json()
        
        app_name = data.get('app_name')
        app_version = data.get('app_version')
        event_type = data.get('event_type')
        event_data = json.dumps(data.get('event_data', {}))
        user_id = data.get('user_id', 'anonymous')
        
        if not all([app_name, event_type]):
            return jsonify({"error": "app_name and event_type are required"}), 400
        
        # Store event
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO app_stats 
            (app_name, app_version, event_type, event_data, user_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (app_name, app_version, event_type, event_data, user_id, request.remote_addr))
        conn.commit()
        conn.close()
        
        logger.info(f"Event logged: {app_name} - {event_type}")
        return jsonify({"status": "success", "message": "Event logged"})
        
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/logs/summary', methods=['GET'])
def get_logs_summary():
    """Get summary of collected logs (admin only)"""
    try:
        # Basic auth check (in production, use proper authentication)
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Basic '):
            return jsonify({"error": "Authentication required"}), 401
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get log counts by app
        cursor.execute('''
            SELECT app_name, app_version, log_type, COUNT(*) as count,
                   MAX(timestamp) as last_log
            FROM log_entries 
            GROUP BY app_name, app_version, log_type
            ORDER BY last_log DESC
        ''')
        logs = cursor.fetchall()
        
        # Get event stats
        cursor.execute('''
            SELECT app_name, event_type, COUNT(*) as count
            FROM app_stats 
            GROUP BY app_name, event_type
            ORDER BY count DESC
        ''')
        events = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "logs": [
                {
                    "app_name": row[0],
                    "app_version": row[1], 
                    "log_type": row[2],
                    "count": row[3],
                    "last_log": row[4]
                } for row in logs
            ],
            "events": [
                {
                    "app_name": row[0],
                    "event_type": row[1],
                    "count": row[2]
                } for row in events
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting logs summary: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "user-logs-collector",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    init_database()
    app.run(host='127.0.0.1', port=5002, debug=False)