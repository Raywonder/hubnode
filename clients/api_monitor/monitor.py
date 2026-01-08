#!/usr/bin/env python3
"""
CopyParty Hub Node API Monitor Client
Real-time monitoring and analytics for the backend server
Location: /home/devinecr/apps/hubnode/clients/api_monitor/
"""

import requests
import time
import json
import os
import sys
from datetime import datetime
import threading
import sqlite3
from pathlib import Path

class HubNodeMonitor:
    def __init__(self, api_base="http://localhost:3923", api_key="hub-node-api-2024"):
        self.api_base = api_base
        self.api_key = api_key
        self.db_path = "monitor.db"
        self.running = False
        self.backend_path = "../../backend"  # Relative path to backend
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for monitoring data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Server status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                response_time REAL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                active_connections INTEGER,
                backend_path TEXT
            )
        ''')

        # API requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                response_time REAL,
                file_size INTEGER,
                user_ip TEXT
            )
        ''')

        # File operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                operation TEXT,
                filename TEXT,
                file_size INTEGER,
                user_id TEXT,
                success BOOLEAN
            )
        ''')

        # Backend health table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backend_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service_status TEXT,
                log_size INTEGER,
                upload_count INTEGER,
                download_count INTEGER,
                error_count INTEGER
            )
        ''')

        conn.commit()
        conn.close()
        print(f"✓ Database initialized: {self.db_path}")

    def check_backend_files(self):
        """Check if backend files are accessible"""
        backend_status = {
            "copyparty_sfx": False,
            "start_script": False,
            "config_file": False,
            "log_dir": False,
            "upload_dir": False,
            "download_dir": False
        }

        try:
            backend_full_path = os.path.abspath(self.backend_path)

            # Check main files
            if os.path.exists(f"{backend_full_path}/copyparty-sfx.py"):
                backend_status["copyparty_sfx"] = True

            if os.path.exists(f"{backend_full_path}/start-copyparty.sh"):
                backend_status["start_script"] = True

            if os.path.exists(f"{backend_full_path}/copyparty-config.py"):
                backend_status["config_file"] = True

            # Check directories
            for dir_name in ["logs", "uploads", "downloads"]:
                if os.path.exists(f"{backend_full_path}/{dir_name}"):
                    backend_status[f"{dir_name[:-1]}_dir"] = True

            return backend_status, backend_full_path

        except Exception as e:
            return {"error": str(e)}, None

    def check_server_health(self):
        """Check if CopyParty server is responding"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base}/api/status",
                                  params={"api_key": self.api_key},
                                  timeout=5)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return True, response_time, response.json()
            else:
                return False, response_time, {"error": f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return False, None, {"error": str(e)}

    def get_backend_stats(self):
        """Get backend-specific statistics"""
        stats = {"backend_accessible": False}

        try:
            backend_status, backend_path = self.check_backend_files()
            stats["backend_status"] = backend_status
            stats["backend_path"] = backend_path
            stats["backend_accessible"] = not ("error" in backend_status)

            if stats["backend_accessible"]:
                # Count files in directories
                try:
                    upload_count = len(os.listdir(f"{backend_path}/uploads")) if os.path.exists(f"{backend_path}/uploads") else 0
                    download_count = len(os.listdir(f"{backend_path}/downloads")) if os.path.exists(f"{backend_path}/downloads") else 0
                    log_size = os.path.getsize(f"{backend_path}/logs/copyparty.log") if os.path.exists(f"{backend_path}/logs/copyparty.log") else 0

                    stats.update({
                        "upload_count": upload_count,
                        "download_count": download_count,
                        "log_size": log_size
                    })
                except Exception as e:
                    stats["stats_error"] = str(e)

            return stats

        except Exception as e:
            return {"error": str(e), "backend_accessible": False}

    def get_system_stats(self):
        """Get system statistics"""
        try:
            # Try to import psutil for system stats
            import psutil

            stats = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict(),
                "network": psutil.net_io_counters()._asdict(),
                "processes": len(psutil.pids())
            }

            return stats
        except ImportError:
            # Fallback using basic system commands
            try:
                import subprocess

                # Basic CPU info
                cpu_info = subprocess.run(['top', '-l', '1', '-n', '0'],
                                        capture_output=True, text=True, timeout=5)

                return {"system_info": "basic", "cpu_available": "top" in cpu_info.stdout}
            except:
                return {"error": "No system monitoring available"}

    def log_monitoring_data(self, status, response_time, backend_stats, system_stats):
        """Log all monitoring data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Log server status
        cpu_usage = system_stats.get('cpu_percent', 0) if isinstance(system_stats, dict) else 0
        memory_usage = system_stats.get('memory', {}).get('percent', 0) if isinstance(system_stats, dict) else 0
        disk_usage = system_stats.get('disk', {}).get('percent', 0) if isinstance(system_stats, dict) else 0

        cursor.execute('''
            INSERT INTO server_status
            (status, response_time, cpu_usage, memory_usage, disk_usage, active_connections, backend_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (status, response_time, cpu_usage, memory_usage, disk_usage, 0, backend_stats.get('backend_path', '')))

        # Log backend health
        if backend_stats.get('backend_accessible'):
            cursor.execute('''
                INSERT INTO backend_health
                (service_status, log_size, upload_count, download_count, error_count)
                VALUES (?, ?, ?, ?, ?)
            ''', ('accessible',
                  backend_stats.get('log_size', 0),
                  backend_stats.get('upload_count', 0),
                  backend_stats.get('download_count', 0),
                  0))

        conn.commit()
        conn.close()

    def monitor_api_endpoints(self):
        """Test various API endpoints"""
        endpoints = {
            "status": "/api/status",
            "list": "/api/list",
            "upload": "/api/upload"  # GET to check if endpoint exists
        }

        results = {}
        for name, endpoint in endpoints.items():
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}{endpoint}",
                                      params={"api_key": self.api_key},
                                      timeout=3)
                response_time = time.time() - start_time

                results[name] = {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "accessible": response.status_code in [200, 405]  # 405 = Method Not Allowed is OK for POST endpoints
                }
            except Exception as e:
                results[name] = {
                    "error": str(e),
                    "accessible": False
                }

        return results

    def generate_comprehensive_report(self):
        """Generate comprehensive monitoring report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent status
        cursor.execute('''
            SELECT * FROM server_status
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        recent_status = cursor.fetchall()

        # Get uptime percentage
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online
            FROM server_status
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        uptime_data = cursor.fetchone()

        # Get backend health
        cursor.execute('''
            SELECT * FROM backend_health
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        backend_health = cursor.fetchall()

        conn.close()

        if uptime_data and uptime_data[0] > 0:
            uptime_percent = (uptime_data[1] / uptime_data[0]) * 100
        else:
            uptime_percent = 0

        # Current status checks
        backend_stats = self.get_backend_stats()
        api_endpoints = self.monitor_api_endpoints()

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_24h": f"{uptime_percent:.2f}%",
            "recent_checks": len(recent_status),
            "last_check": recent_status[0][1] if recent_status else "Never",
            "backend_accessible": backend_stats.get('backend_accessible', False),
            "backend_path": backend_stats.get('backend_path', ''),
            "api_endpoints": api_endpoints,
            "backend_files": backend_stats.get('backend_status', {}),
            "file_counts": {
                "uploads": backend_stats.get('upload_count', 0),
                "downloads": backend_stats.get('download_count', 0)
            },
            "log_size_bytes": backend_stats.get('log_size', 0)
        }

    def start_monitoring(self, interval=30):
        """Start continuous monitoring with backend integration"""
        self.running = True
        print(f"🔍 Starting HubNode API Monitor Client")
        print(f"📊 Monitoring: {self.api_base}")
        print(f"📁 Backend path: {os.path.abspath(self.backend_path)}")
        print(f"⏱️  Check interval: {interval} seconds")
        print("─" * 50)

        while self.running:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Check server health
            is_healthy, response_time, status_data = self.check_server_health()
            status = "online" if is_healthy else "offline"

            # Get backend stats
            backend_stats = self.get_backend_stats()

            # Get system stats
            system_stats = self.get_system_stats()

            # Log all data
            self.log_monitoring_data(status, response_time, backend_stats, system_stats)

            # Display real-time status
            print(f"[{timestamp}] Server: {status}")
            if response_time:
                print(f"   Response time: {response_time:.3f}s")

            print(f"   Backend accessible: {'✅' if backend_stats.get('backend_accessible') else '❌'}")

            if backend_stats.get('backend_accessible'):
                print(f"   Uploads: {backend_stats.get('upload_count', 0)}")
                print(f"   Downloads: {backend_stats.get('download_count', 0)}")
                if backend_stats.get('log_size', 0) > 0:
                    print(f"   Log size: {backend_stats.get('log_size', 0)} bytes")

            if isinstance(system_stats, dict) and 'cpu_percent' in system_stats:
                print(f"   CPU: {system_stats['cpu_percent']:.1f}%")
                print(f"   Memory: {system_stats.get('memory', {}).get('percent', 0):.1f}%")

            print("─" * 30)
            time.sleep(interval)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        print("🛑 Monitoring stopped")

    def web_dashboard(self, port=8080):
        """Enhanced web dashboard with backend integration"""
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_dashboard_html()
                elif self.path == '/api/stats':
                    self.send_stats_json()
                elif self.path == '/api/backend':
                    self.send_backend_stats()
                else:
                    self.send_error(404)

            def send_dashboard_html(self):
                monitor = HubNodeMonitor()
                report = monitor.generate_comprehensive_report()

                backend_status = "🟢 Accessible" if report['backend_accessible'] else "🔴 Not Accessible"

                html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>HubNode Monitor Dashboard</title>
                    <meta charset="utf-8">
                    <meta http-equiv="refresh" content="30">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                        .container {{ max-width: 1200px; margin: 0 auto; }}
                        .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        .status-online {{ color: #28a745; }}
                        .status-offline {{ color: #dc3545; }}
                        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                        .metric-value {{ font-size: 24px; font-weight: bold; }}
                        .metric-label {{ font-size: 12px; color: #666; }}
                        .file-status {{ background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 5px 0; }}
                        h1 {{ color: #333; text-align: center; }}
                        h2 {{ color: #666; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                        .path {{ font-family: monospace; background: #f1f1f1; padding: 5px; border-radius: 3px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🔍 HubNode API Monitor Dashboard</h1>
                        <p><strong>Client Location:</strong> <span class="path">/home/devinecr/apps/hubnode/clients/api_monitor/</span></p>

                        <div class="card">
                            <h2>Server Status</h2>
                            <div class="metric">
                                <div class="metric-value">{report['uptime_24h']}</div>
                                <div class="metric-label">Uptime 24h</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{report['recent_checks']}</div>
                                <div class="metric-label">Recent Checks</div>
                            </div>
                        </div>

                        <div class="card">
                            <h2>Backend Integration</h2>
                            <p><strong>Status:</strong> {backend_status}</p>
                            <p><strong>Backend Path:</strong> <span class="path">{report['backend_path']}</span></p>

                            <h3>Backend Files Status:</h3>
                            <div class="file-status">
                                CopyParty Executable: {'✅' if report['backend_files'].get('copyparty_sfx') else '❌'} copyparty-sfx.py
                            </div>
                            <div class="file-status">
                                Start Script: {'✅' if report['backend_files'].get('start_script') else '❌'} start-copyparty.sh
                            </div>
                            <div class="file-status">
                                Configuration: {'✅' if report['backend_files'].get('config_file') else '❌'} copyparty-config.py
                            </div>
                            <div class="file-status">
                                Upload Directory: {'✅' if report['backend_files'].get('upload_dir') else '❌'} uploads/
                            </div>
                            <div class="file-status">
                                Download Directory: {'✅' if report['backend_files'].get('download_dir') else '❌'} downloads/
                            </div>
                            <div class="file-status">
                                Log Directory: {'✅' if report['backend_files'].get('log_dir') else '❌'} logs/
                            </div>
                        </div>

                        <div class="card">
                            <h2>File Activity</h2>
                            <div class="metric">
                                <div class="metric-value">{report['file_counts']['uploads']}</div>
                                <div class="metric-label">Upload Files</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{report['file_counts']['downloads']}</div>
                                <div class="metric-label">Download Files</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{report['log_size_bytes']}</div>
                                <div class="metric-label">Log Size (bytes)</div>
                            </div>
                        </div>

                        <div class="card">
                            <h2>API Endpoints</h2>
                            {self._format_api_endpoints(report['api_endpoints'])}
                        </div>

                        <div class="card">
                            <h2>Quick Actions</h2>
                            <p>
                                <a href="{monitor.api_base}" target="_blank">📁 CopyParty Web Interface</a> |
                                <a href="/api/stats" target="_blank">📊 Full Stats JSON</a> |
                                <a href="/api/backend" target="_blank">🔧 Backend Details</a>
                            </p>
                        </div>

                        <div class="card">
                            <small>Last updated: {report['timestamp']} | Auto-refresh: 30s</small>
                        </div>
                    </div>
                </body>
                </html>
                '''

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())

            def _format_api_endpoints(self, endpoints):
                html = ""
                for name, data in endpoints.items():
                    status = "✅" if data.get('accessible') else "❌"
                    response_time = f"{data.get('response_time', 0):.3f}s" if 'response_time' in data else "N/A"
                    html += f'<div class="file-status">{status} {name}: {response_time}</div>'
                return html

            def send_stats_json(self):
                monitor = HubNodeMonitor()
                report = monitor.generate_comprehensive_report()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(report, indent=2).encode())

            def send_backend_stats(self):
                monitor = HubNodeMonitor()
                backend_stats = monitor.get_backend_stats()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(backend_stats, indent=2).encode())

        server = HTTPServer(('localhost', port), DashboardHandler)
        print(f"🌐 Web dashboard available at: http://localhost:{port}")
        print(f"📊 API stats: http://localhost:{port}/api/stats")
        print(f"🔧 Backend details: http://localhost:{port}/api/backend")
        server.serve_forever()

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("HubNode API Monitor Client")
        print("Location: /home/devinecr/apps/hubnode/clients/api_monitor/")
        print("")
        print("Usage:")
        print("  python3 monitor.py start [interval_seconds]")
        print("  python3 monitor.py dashboard [port]")
        print("  python3 monitor.py report")
        print("  python3 monitor.py status")
        print("  python3 monitor.py backend")
        print("")
        print("Examples:")
        print("  python3 monitor.py start 30        # Monitor every 30 seconds")
        print("  python3 monitor.py dashboard 8080  # Web dashboard on port 8080")
        print("  python3 monitor.py backend         # Check backend file status")
        return

    command = sys.argv[1]
    monitor = HubNodeMonitor()

    if command == "start":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        try:
            monitor.start_monitoring(interval)
        except KeyboardInterrupt:
            monitor.stop_monitoring()

    elif command == "dashboard":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        monitor.web_dashboard(port)

    elif command == "report":
        report = monitor.generate_comprehensive_report()
        print(json.dumps(report, indent=2))

    elif command == "status":
        is_healthy, response_time, status_data = monitor.check_server_health()
        print(f"Server: {'Online' if is_healthy else 'Offline'}")
        if response_time:
            print(f"Response time: {response_time:.3f}s")
        print(f"Status data: {json.dumps(status_data, indent=2)}")

    elif command == "backend":
        backend_stats = monitor.get_backend_stats()
        print("Backend Status:")
        print(json.dumps(backend_stats, indent=2))

    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()