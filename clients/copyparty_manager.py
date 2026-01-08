#!/usr/bin/env python3
"""
CopyParty Management Suite
Full management tool for CopyParty server with directory control, user management, and configuration
"""

import os
import sys
import json
import sqlite3
import requests
import subprocess
import platform
import time
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import secrets

class CopyPartyManager:
    def __init__(self, server_url="http://localhost:3923", api_key="hub-node-api-2024"):
        self.server_url = server_url
        self.api_key = api_key
        self.config_file = "copyparty_manager_config.json"
        self.db_file = "copyparty_manager.db"
        self.platform = platform.system().lower()

        self.init_database()
        self.load_config()

    def init_database(self):
        """Initialize management database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Directory access table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS directory_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                directory_path TEXT UNIQUE,
                alias TEXT,
                permissions TEXT,
                users TEXT,
                groups TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Volume mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS volume_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                local_path TEXT,
                remote_path TEXT,
                volume_type TEXT,
                permissions TEXT,
                active BOOLEAN DEFAULT 1,
                auto_mount BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User management table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managed_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT,
                password_hash TEXT,
                permissions TEXT,
                directories TEXT,
                api_key TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_access TIMESTAMP
            )
        ''')

        # Configuration history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_type TEXT,
                config_data TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def load_config(self):
        """Load manager configuration"""
        default_config = {
            "server": {
                "url": self.server_url,
                "api_key": self.api_key,
                "timeout": 30
            },
            "directories": {
                "managed_paths": [],
                "restricted_paths": ["/etc", "/var", "/usr", "/bin", "/sbin"],
                "default_permissions": "r"
            },
            "users": {
                "default_quota": "1GB",
                "max_api_keys_per_user": 5,
                "session_timeout": 24
            },
            "platform_specific": {
                "windows": {
                    "drive_mapping": True,
                    "service_management": True
                },
                "darwin": {
                    "finder_integration": True,
                    "launchd_management": True
                },
                "linux": {
                    "systemd_management": True,
                    "fuse_mounting": True
                }
            }
        }

        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def add_directory(self, directory_path, alias=None, permissions="r", users=None, groups=None):
        """Add directory to CopyParty access"""
        if not os.path.exists(directory_path):
            return {"success": False, "error": "Directory does not exist"}

        # Check if path is restricted
        abs_path = os.path.abspath(directory_path)
        for restricted in self.config["directories"]["restricted_paths"]:
            if abs_path.startswith(restricted):
                return {"success": False, "error": f"Path {abs_path} is restricted"}

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Check if directory already exists
        cursor.execute("SELECT id FROM directory_access WHERE directory_path = ?", (abs_path,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Directory already managed"}

        # Add directory
        if not alias:
            alias = os.path.basename(abs_path) or abs_path.replace('/', '_')

        users_str = json.dumps(users) if users else "[]"
        groups_str = json.dumps(groups) if groups else "[]"

        cursor.execute('''
            INSERT INTO directory_access (directory_path, alias, permissions, users, groups)
            VALUES (?, ?, ?, ?, ?)
        ''', (abs_path, alias, permissions, users_str, groups_str))

        conn.commit()
        conn.close()

        # Update CopyParty configuration
        self.regenerate_copyparty_config()

        return {"success": True, "directory_id": cursor.lastrowid, "alias": alias}

    def remove_directory(self, directory_path_or_alias):
        """Remove directory from CopyParty access"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Try to find by path or alias
        cursor.execute('''
            SELECT id, directory_path, alias FROM directory_access
            WHERE directory_path = ? OR alias = ?
        ''', (directory_path_or_alias, directory_path_or_alias))

        directory = cursor.fetchone()
        if not directory:
            conn.close()
            return {"success": False, "error": "Directory not found"}

        # Deactivate directory
        cursor.execute('''
            UPDATE directory_access SET active = 0, updated_at = datetime('now')
            WHERE id = ?
        ''', (directory[0],))

        conn.commit()
        conn.close()

        # Update CopyParty configuration
        self.regenerate_copyparty_config()

        return {"success": True, "removed": {"path": directory[1], "alias": directory[2]}}

    def list_directories(self):
        """List all managed directories"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT directory_path, alias, permissions, users, groups, active, created_at
            FROM directory_access
            ORDER BY created_at DESC
        ''')

        directories = []
        for row in cursor.fetchall():
            directories.append({
                "path": row[0],
                "alias": row[1],
                "permissions": row[2],
                "users": json.loads(row[3]) if row[3] else [],
                "groups": json.loads(row[4]) if row[4] else [],
                "active": bool(row[5]),
                "created_at": row[6]
            })

        conn.close()
        return directories

    def update_directory_permissions(self, directory_path_or_alias, permissions=None, users=None, groups=None):
        """Update directory permissions"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id FROM directory_access
            WHERE (directory_path = ? OR alias = ?) AND active = 1
        ''', (directory_path_or_alias, directory_path_or_alias))

        directory = cursor.fetchone()
        if not directory:
            conn.close()
            return {"success": False, "error": "Directory not found"}

        # Build update query
        updates = []
        params = []

        if permissions:
            updates.append("permissions = ?")
            params.append(permissions)

        if users is not None:
            updates.append("users = ?")
            params.append(json.dumps(users))

        if groups is not None:
            updates.append("groups = ?")
            params.append(json.dumps(groups))

        if updates:
            updates.append("updated_at = datetime('now')")
            params.append(directory[0])

            query = f"UPDATE directory_access SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

            conn.commit()
            conn.close()

            # Update CopyParty configuration
            self.regenerate_copyparty_config()

            return {"success": True, "updated": True}

        conn.close()
        return {"success": False, "error": "No updates specified"}

    def create_user(self, username, email, password, permissions="r", directories=None):
        """Create new CopyParty user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM managed_users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": "User already exists"}

        # Hash password
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Generate API key
        api_key = secrets.token_urlsafe(32)

        directories_str = json.dumps(directories) if directories else "[]"

        cursor.execute('''
            INSERT INTO managed_users (username, email, password_hash, permissions, directories, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, permissions, directories_str, api_key))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update CopyParty configuration
        self.regenerate_copyparty_config()

        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "api_key": api_key
        }

    def delete_user(self, username):
        """Delete CopyParty user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM managed_users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return {"success": False, "error": "User not found"}

        cursor.execute("UPDATE managed_users SET active = 0 WHERE username = ?", (username,))
        conn.commit()
        conn.close()

        # Update CopyParty configuration
        self.regenerate_copyparty_config()

        return {"success": True, "deleted": username}

    def list_users(self):
        """List all managed users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT username, email, permissions, directories, api_key, active, created_at, last_access
            FROM managed_users
            ORDER BY created_at DESC
        ''')

        users = []
        for row in cursor.fetchall():
            users.append({
                "username": row[0],
                "email": row[1],
                "permissions": row[2],
                "directories": json.loads(row[3]) if row[3] else [],
                "api_key": row[4],
                "active": bool(row[5]),
                "created_at": row[6],
                "last_access": row[7]
            })

        conn.close()
        return users

    def regenerate_copyparty_config(self):
        """Regenerate CopyParty configuration file"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Get active directories
        cursor.execute('''
            SELECT directory_path, alias, permissions, users, groups
            FROM directory_access WHERE active = 1
        ''')
        directories = cursor.fetchall()

        # Get active users
        cursor.execute('''
            SELECT username, password_hash, permissions, directories
            FROM managed_users WHERE active = 1
        ''')
        users = cursor.fetchall()

        conn.close()

        # Generate auth file
        auth_lines = []

        for username, password_hash, permissions, user_dirs in users:
            # For demo purposes, using simplified password (in production, implement proper auth)
            temp_password = "temp123"

            # Add user access to assigned directories
            user_directories = json.loads(user_dirs) if user_dirs else []

            for dir_path, alias, dir_permissions, dir_users, dir_groups in directories:
                dir_users_list = json.loads(dir_users) if dir_users else []

                if not dir_users_list or username in dir_users_list:
                    # User has access to this directory
                    auth_lines.append(f"{username}:{temp_password}:{alias}::{dir_permissions}")

            # Add general access
            auth_lines.append(f"{username}:{temp_password}:uploads::{permissions}")
            auth_lines.append(f"{username}:{temp_password}:downloads::{permissions}")

        # Write auth file
        with open("copyparty_auth_managed.txt", "w") as f:
            for line in auth_lines:
                f.write(line + "\n")

        # Generate volume mappings
        volume_args = []

        for dir_path, alias, permissions, users, groups in directories:
            volume_args.append(f'--volume "{dir_path}:{alias}:{permissions}"')

        # Generate startup script
        startup_script = f'''#!/bin/bash
# CopyParty Managed Configuration
# Generated by CopyParty Manager at {datetime.now()}

python3 copyparty-sfx.py \\
    --host 0.0.0.0 \\
    --port 3923 \\
    --name "CopyParty Managed Server" \\
    \\
    --accounts-file copyparty_auth_managed.txt \\
    \\
    {' \\\n    '.join(volume_args)} \\
    \\
    --enable-uploads \\
    --enable-downloads \\
    --enable-webdav \\
    --enable-search \\
    --enable-thumbs \\
    --cors \\
    \\
    --log-file ./logs/copyparty-managed.log \\
    --access-log ./logs/access-managed.log \\
    \\
    --verbose \\
    $@
'''

        with open("start-copyparty-managed.sh", "w") as f:
            f.write(startup_script)

        os.chmod("start-copyparty-managed.sh", 0o755)

        # Save configuration to history
        self.save_config_history("volumes", json.dumps([dict(zip(
            ["path", "alias", "permissions", "users", "groups"], dir_data
        )) for dir_data in directories]))

        return {
            "success": True,
            "auth_file": "copyparty_auth_managed.txt",
            "startup_script": "start-copyparty-managed.sh",
            "directories_count": len(directories),
            "users_count": len(users)
        }

    def save_config_history(self, config_type, config_data, description=None):
        """Save configuration change to history"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO config_history (config_type, config_data, description)
            VALUES (?, ?, ?)
        ''', (config_type, config_data, description or f"Configuration update at {datetime.now()}"))

        conn.commit()
        conn.close()

    def get_server_status(self):
        """Get CopyParty server status"""
        try:
            response = requests.get(f"{self.server_url}/api/status",
                                  headers={"Authorization": f"Bearer {self.api_key}"},
                                  timeout=5)

            if response.status_code == 200:
                return {"online": True, "data": response.json()}
            else:
                return {"online": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {"online": False, "error": str(e)}

    def restart_server(self):
        """Restart CopyParty server"""
        if self.platform == "linux":
            try:
                subprocess.run(["sudo", "systemctl", "restart", "copyparty-hubnode"], check=True)
                return {"success": True, "method": "systemctl"}
            except subprocess.CalledProcessError:
                return {"success": False, "error": "Failed to restart via systemctl"}

        elif self.platform == "darwin":
            try:
                subprocess.run(["sudo", "launchctl", "unload", "/Library/LaunchDaemons/copyparty.plist"], check=True)
                time.sleep(2)
                subprocess.run(["sudo", "launchctl", "load", "/Library/LaunchDaemons/copyparty.plist"], check=True)
                return {"success": True, "method": "launchctl"}
            except subprocess.CalledProcessError:
                return {"success": False, "error": "Failed to restart via launchctl"}

        elif self.platform == "windows":
            try:
                subprocess.run(["net", "stop", "CopyParty"], check=True)
                time.sleep(2)
                subprocess.run(["net", "start", "CopyParty"], check=True)
                return {"success": True, "method": "net"}
            except subprocess.CalledProcessError:
                return {"success": False, "error": "Failed to restart via net command"}

        return {"success": False, "error": f"Restart not supported on {self.platform}"}

    def backup_configuration(self, backup_path=None):
        """Backup CopyParty configuration"""
        if not backup_path:
            backup_path = f"copyparty_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"

        try:
            import tarfile

            with tarfile.open(backup_path, "w:gz") as tar:
                # Add database
                tar.add(self.db_file, arcname="manager_database.db")

                # Add configuration
                tar.add(self.config_file, arcname="manager_config.json")

                # Add generated files
                if os.path.exists("copyparty_auth_managed.txt"):
                    tar.add("copyparty_auth_managed.txt", arcname="auth_file.txt")

                if os.path.exists("start-copyparty-managed.sh"):
                    tar.add("start-copyparty-managed.sh", arcname="startup_script.sh")

            return {"success": True, "backup_file": backup_path}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_configuration(self, backup_path):
        """Restore CopyParty configuration from backup"""
        if not os.path.exists(backup_path):
            return {"success": False, "error": "Backup file not found"}

        try:
            import tarfile

            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall()

            # Reload configuration
            self.load_config()

            return {"success": True, "restored_from": backup_path}

        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("CopyParty Manager - Full Management Suite")
        print("=" * 50)
        print("Usage: python3 copyparty_manager.py <command> [options]")
        print("")
        print("Directory Management:")
        print("  add-dir <path> [alias] [permissions]     Add directory to CopyParty")
        print("  remove-dir <path|alias>                  Remove directory access")
        print("  list-dirs                                List all managed directories")
        print("  update-dir <path|alias> [permissions]    Update directory permissions")
        print("")
        print("User Management:")
        print("  create-user <username> <email> <password>  Create new user")
        print("  delete-user <username>                     Delete user")
        print("  list-users                                 List all users")
        print("")
        print("Server Management:")
        print("  status                                    Check server status")
        print("  restart                                   Restart CopyParty server")
        print("  regenerate                                Regenerate configuration")
        print("")
        print("Backup & Restore:")
        print("  backup [path]                             Backup configuration")
        print("  restore <backup_path>                     Restore from backup")
        print("")
        print("Examples:")
        print("  python3 copyparty_manager.py add-dir /home/user/documents docs rw")
        print("  python3 copyparty_manager.py create-user john john@example.com pass123")
        print("  python3 copyparty_manager.py list-dirs")
        return

    manager = CopyPartyManager()
    command = sys.argv[1]

    if command == "add-dir":
        if len(sys.argv) < 3:
            print("❌ Usage: add-dir <path> [alias] [permissions]")
            return

        path = sys.argv[2]
        alias = sys.argv[3] if len(sys.argv) > 3 else None
        permissions = sys.argv[4] if len(sys.argv) > 4 else "r"

        result = manager.add_directory(path, alias, permissions)
        if result["success"]:
            print(f"✅ Directory added: {path} as '{result['alias']}'")
        else:
            print(f"❌ Error: {result['error']}")

    elif command == "remove-dir":
        if len(sys.argv) < 3:
            print("❌ Usage: remove-dir <path|alias>")
            return

        path_or_alias = sys.argv[2]
        result = manager.remove_directory(path_or_alias)

        if result["success"]:
            print(f"✅ Directory removed: {result['removed']['path']}")
        else:
            print(f"❌ Error: {result['error']}")

    elif command == "list-dirs":
        directories = manager.list_directories()

        if directories:
            print(f"📁 Managed Directories ({len(directories)}):")
            print("-" * 80)
            for dir_info in directories:
                status = "✅" if dir_info["active"] else "❌"
                print(f"{status} {dir_info['alias']} -> {dir_info['path']}")
                print(f"   Permissions: {dir_info['permissions']}")
                print(f"   Users: {', '.join(dir_info['users']) if dir_info['users'] else 'All'}")
                print()
        else:
            print("📁 No directories managed")

    elif command == "create-user":
        if len(sys.argv) < 5:
            print("❌ Usage: create-user <username> <email> <password>")
            return

        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]

        result = manager.create_user(username, email, password)

        if result["success"]:
            print(f"✅ User created: {username}")
            print(f"   API Key: {result['api_key']}")
        else:
            print(f"❌ Error: {result['error']}")

    elif command == "delete-user":
        if len(sys.argv) < 3:
            print("❌ Usage: delete-user <username>")
            return

        username = sys.argv[2]
        result = manager.delete_user(username)

        if result["success"]:
            print(f"✅ User deleted: {username}")
        else:
            print(f"❌ Error: {result['error']}")

    elif command == "list-users":
        users = manager.list_users()

        if users:
            print(f"👥 Managed Users ({len(users)}):")
            print("-" * 80)
            for user in users:
                status = "✅" if user["active"] else "❌"
                print(f"{status} {user['username']} ({user['email']})")
                print(f"   Permissions: {user['permissions']}")
                print(f"   Directories: {len(user['directories'])}")
                print(f"   Created: {user['created_at']}")
                print()
        else:
            print("👥 No users managed")

    elif command == "status":
        status = manager.get_server_status()

        if status["online"]:
            print("✅ CopyParty server is online")
            if "data" in status:
                print(f"   Data: {json.dumps(status['data'], indent=2)}")
        else:
            print(f"❌ CopyParty server is offline: {status['error']}")

    elif command == "restart":
        print("🔄 Restarting CopyParty server...")
        result = manager.restart_server()

        if result["success"]:
            print(f"✅ Server restarted via {result['method']}")
        else:
            print(f"❌ Restart failed: {result['error']}")

    elif command == "regenerate":
        print("⚙️ Regenerating CopyParty configuration...")
        result = manager.regenerate_copyparty_config()

        if result["success"]:
            print("✅ Configuration regenerated:")
            print(f"   Auth file: {result['auth_file']}")
            print(f"   Startup script: {result['startup_script']}")
            print(f"   Directories: {result['directories_count']}")
            print(f"   Users: {result['users_count']}")
        else:
            print("❌ Failed to regenerate configuration")

    elif command == "backup":
        backup_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = manager.backup_configuration(backup_path)

        if result["success"]:
            print(f"✅ Configuration backed up to: {result['backup_file']}")
        else:
            print(f"❌ Backup failed: {result['error']}")

    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Usage: restore <backup_path>")
            return

        backup_path = sys.argv[2]
        result = manager.restore_configuration(backup_path)

        if result["success"]:
            print(f"✅ Configuration restored from: {backup_path}")
        else:
            print(f"❌ Restore failed: {result['error']}")

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()