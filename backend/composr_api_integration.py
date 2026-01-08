#!/usr/bin/env python3
"""
CopyParty - Composr API Integration
Integrates CopyParty with Composr CMS for user authentication and file management
"""

import requests
import json
import os
import hashlib
import time
from pathlib import Path
import sqlite3

class ComposrAPIIntegration:
    def __init__(self):
        self.composr_config = {
            "dom_site": {
                "url": "https://raywonderis.me",
                "api_endpoint": "/composr/api.php",
                "public_html": "/home/dom/public_html",
                "copyparty_path": "/home/dom/public_html/copyparty"
            },
            "devine_site": {
                "url": "https://devinecreations.net",
                "api_endpoint": "/api.php",
                "public_html": "/home/devinecr/devinecreations.net",
                "copyparty_path": "/home/devinecr/devinecreations.net/copyparty"
            }
        }

        self.api_keys = {
            "dom": "",  # Set from Composr admin panel
            "devine": ""  # Set from Composr admin panel
        }

        self.init_composr_integration()

    def init_composr_integration(self):
        """Initialize Composr integration database"""
        conn = sqlite3.connect("composr_integration.db")
        cursor = conn.cursor()

        # Composr users sync table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS composr_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                composr_site TEXT,
                composr_user_id INTEGER,
                composr_username TEXT,
                composr_email TEXT,
                copyparty_username TEXT,
                permissions TEXT,
                last_sync TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        ''')

        # File sync tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_sync (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                composr_site TEXT,
                copyparty_path TEXT,
                web_path TEXT,
                sync_type TEXT,
                last_sync TIMESTAMP,
                file_hash TEXT,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def verify_composr_user(self, site, username, password):
        """Verify user against Composr API"""
        config = self.composr_config[site]

        try:
            # Composr API authentication call
            api_url = f"{config['url']}{config['api_endpoint']}"

            auth_data = {
                "action": "authenticate_user",
                "username": username,
                "password": password,
                "api_key": self.api_keys.get(site, "")
            }

            response = requests.post(api_url, data=auth_data, timeout=10)

            if response.status_code == 200:
                result = response.json()

                if result.get("success"):
                    user_data = result.get("user_data", {})

                    # Sync user to local database
                    self.sync_composr_user(site, user_data)

                    return {
                        "user_id": user_data.get("id"),
                        "username": username,
                        "email": user_data.get("email"),
                        "groups": user_data.get("groups", []),
                        "permissions": self.get_copyparty_permissions(user_data.get("groups", []))
                    }
                else:
                    return None
            else:
                return None

        except Exception as e:
            print(f"Composr authentication error for {site}: {e}")
            return None

    def sync_composr_user(self, site, user_data):
        """Sync Composr user to local database"""
        conn = sqlite3.connect("composr_integration.db")
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute('''
            SELECT id FROM composr_users
            WHERE composr_site = ? AND composr_user_id = ?
        ''', (site, user_data.get("id")))

        existing_user = cursor.fetchone()

        # Determine CopyParty permissions based on Composr groups
        permissions = self.get_copyparty_permissions(user_data.get("groups", []))
        copyparty_username = f"{site}_{user_data.get('username')}"

        if existing_user:
            # Update existing user
            cursor.execute('''
                UPDATE composr_users SET
                    composr_username = ?,
                    composr_email = ?,
                    permissions = ?,
                    last_sync = datetime('now')
                WHERE id = ?
            ''', (user_data.get("username"), user_data.get("email"),
                  permissions, existing_user[0]))
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO composr_users
                (composr_site, composr_user_id, composr_username, composr_email,
                 copyparty_username, permissions, last_sync)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (site, user_data.get("id"), user_data.get("username"),
                  user_data.get("email"), copyparty_username, permissions))

        conn.commit()
        conn.close()

    def get_copyparty_permissions(self, groups):
        """Map Composr groups to CopyParty permissions"""
        permissions_map = {
            "administrators": "r,rw,a",
            "staff": "r,rw",
            "members": "r,rw",
            "guests": "r"
        }

        # Check for highest permission level
        for group in groups:
            group_name = group.lower()
            if group_name in permissions_map:
                return permissions_map[group_name]

        return "r"  # Default read-only

    def setup_web_file_sync(self):
        """Setup file synchronization between CopyParty and web directories"""

        for site_name, config in self.composr_config.items():
            public_html = config["public_html"]
            copyparty_path = config["copyparty_path"]

            # Create web-accessible CopyParty directories
            os.makedirs(f"{copyparty_path}/uploads", exist_ok=True)
            os.makedirs(f"{copyparty_path}/downloads", exist_ok=True)
            os.makedirs(f"{copyparty_path}/gallery", exist_ok=True)
            os.makedirs(f"{copyparty_path}/files", exist_ok=True)

            # Create PHP integration files
            self.create_php_integration(site_name, config)

    def create_php_integration(self, site_name, config):
        """Create PHP files for Composr-CopyParty integration"""

        # Main integration file
        php_integration = f'''<?php
/**
 * CopyParty - Composr Integration
 * Provides seamless file access between Composr and CopyParty
 */

require_once(dirname(__FILE__) . '/../composr/sources/global.php');

class CopyPartyComposrBridge {{

    private $copyparty_url = 'http://localhost:3923';
    private $api_key = 'hub-node-api-2024';

    public function authenticate_user($username, $password) {{
        // Authenticate against Composr
        $member_id = $GLOBALS['FORUM_DRIVER']->authenticate($username, $password);

        if ($member_id !== NULL) {{
            // Get user data
            $user_data = $GLOBALS['FORUM_DRIVER']->get_member($member_id);

            // Return user info for CopyParty
            return array(
                'success' => true,
                'user_data' => array(
                    'id' => $member_id,
                    'username' => $user_data['username'],
                    'email' => $user_data['email'],
                    'groups' => $this->get_user_groups($member_id)
                )
            );
        }}

        return array('success' => false);
    }}

    public function get_user_groups($member_id) {{
        // Get user groups from Composr
        $groups = $GLOBALS['FORUM_DRIVER']->get_members_groups($member_id);
        $group_names = array();

        foreach ($groups as $group_id) {{
            $group_info = $GLOBALS['FORUM_DRIVER']->get_usergroup_info($group_id);
            $group_names[] = $group_info['name'];
        }}

        return $group_names;
    }}

    public function proxy_to_copyparty($path) {{
        // Proxy requests to CopyParty server
        $copyparty_url = $this->copyparty_url . '/' . ltrim($path, '/');

        $headers = array(
            'Authorization: Bearer ' . $this->api_key
        );

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $copyparty_url);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        http_response_code($http_code);
        echo $response;
    }}

    public function handle_file_upload($file_data) {{
        // Handle file uploads to CopyParty
        $upload_url = $this->copyparty_url . '/shared/uploads/';

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $upload_url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $file_data);
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Authorization: Bearer ' . $this->api_key
        ));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

        $response = curl_exec($ch);
        curl_close($ch);

        return json_decode($response, true);
    }}
}}

// API endpoint handling
if (isset($_GET['action'])) {{
    $bridge = new CopyPartyComposrBridge();

    switch ($_GET['action']) {{
        case 'authenticate_user':
            $result = $bridge->authenticate_user($_POST['username'], $_POST['password']);
            header('Content-Type: application/json');
            echo json_encode($result);
            break;

        case 'proxy':
            $path = $_GET['path'] ?? '';
            $bridge->proxy_to_copyparty($path);
            break;

        case 'upload':
            $result = $bridge->handle_file_upload($_FILES);
            header('Content-Type: application/json');
            echo json_encode($result);
            break;
    }}
}}
?>'''

        # Write PHP integration file
        php_file_path = f"{config['copyparty_path']}/api.php"
        with open(php_file_path, 'w') as f:
            f.write(php_integration)

        # Create index.php for web interface
        index_php = f'''<?php
/**
 * CopyParty Web Interface for {site_name.title()}
 */

require_once('api.php');

$bridge = new CopyPartyComposrBridge();
?>
<!DOCTYPE html>
<html>
<head>
    <title>CopyParty - {site_name.title()} File Server</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        .header {{ background: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 5px; }}
        .button:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 CopyParty File Server</h1>
            <p>{site_name.title()} - Composr Integration</p>
        </div>

        <div class="section">
            <h3>📁 Quick Access</h3>
            <a href="http://raywonderis.me:3923/shared/" class="button">Shared Files</a>
            <a href="http://raywonderis.me:3923/shared/platforms/" class="button">Platform Sync</a>
            <a href="http://raywonderis.me:3923/shared/sync/" class="button">App Sync</a>
            <a href="http://raywonderis.me:3923/" class="button">Full CopyParty Interface</a>
        </div>

        <div class="section">
            <h3>📤 File Upload</h3>
            <form action="api.php?action=upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit" class="button">Upload File</button>
            </form>
        </div>

        <div class="section">
            <h3>🔗 Integration Features</h3>
            <ul>
                <li>✅ Composr User Authentication</li>
                <li>✅ Group-based Permissions</li>
                <li>✅ File Upload/Download</li>
                <li>✅ Cross-platform Sync</li>
                <li>✅ API Integration</li>
            </ul>
        </div>
    </div>
</body>
</html>'''

        # Write index.php
        index_file_path = f"{config['copyparty_path']}/index.php"
        with open(index_file_path, 'w') as f:
            f.write(index_php)

        print(f"✅ Created PHP integration for {site_name}: {config['copyparty_path']}/")

    def generate_copyparty_composr_config(self):
        """Generate CopyParty configuration with Composr integration"""

        config_content = f'''#!/bin/bash
# CopyParty with Composr API Integration
# Supports authentication via Composr CMS and web directory access

python3 copyparty-sfx.py \\
    --host 0.0.0.0 \\
    --port 3923 \\
    --name "CopyParty Hub Node - Composr Integrated" \\
    \\
    --accounts-file copyparty_auth_comprehensive.txt \\
    \\
    --volume "/home/devinecr/shared:/shared:rw" \\
    --volume "/home/devinecr/shared/platforms:/platforms:rw" \\
    --volume "/home/devinecr/shared/sync:/sync:rw" \\
    --volume "/home/devinecr/shared/transfers:/transfers:rw" \\
    \\
    --volume "/home/dom/public_html:/dom_web:r,rw" \\
    --volume "/home/devinecr/devinecreations.net:/devine_web:r,rw" \\
    \\
    --volume "/home/dom/public_html/copyparty:/dom_copyparty:rw" \\
    --volume "/home/devinecr/devinecreations.net/copyparty:/devine_copyparty:rw" \\
    \\
    --volume "/home/devinecr:/devinecr:r,rw" \\
    --volume "/home/tappedin:/tappedin:r,rw" \\
    --volume "/home/dom:/dom:r,rw" \\
    \\
    --enable-uploads \\
    --enable-downloads \\
    --enable-webdav \\
    --enable-search \\
    --enable-thumbs \\
    --enable-zip \\
    --enable-markdown \\
    --cors \\
    \\
    --log-file ./logs/copyparty-composr-integrated.log \\
    --access-log ./logs/access-composr.log \\
    \\
    --html-head '<style>
        .composr-integration {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .web-directories {{ background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }}
    </style>' \\
    \\
    --html-top '<div class="composr-integration">
        <h2>🌐 CopyParty + Composr CMS Integration</h2>
        <p>Unified file management across web properties</p>
    </div>

    <div class="web-directories">
        <h3>🌍 Web Directory Access:</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
            <div>
                <strong>Dom\\'s Site:</strong><br>
                <a href="/dom_web" style="color: #007bff;">raywonderis.me public_html</a><br>
                <a href="/dom_copyparty" style="color: #007bff;">CopyParty Integration</a>
            </div>
            <div>
                <strong>Devine Creations:</strong><br>
                <a href="/devine_web" style="color: #007bff;">devinecreations.net</a><br>
                <a href="/devine_copyparty" style="color: #007bff;">CopyParty Integration</a>
            </div>
        </div>
    </div>' \\
    \\
    --verbose \\
    $@
'''

        with open("start-copyparty-composr-integrated.sh", "w") as f:
            f.write(config_content)

        import os
        os.chmod("start-copyparty-composr-integrated.sh", 0o755)

        return "start-copyparty-composr-integrated.sh"

def main():
    print("CopyParty - Composr API Integration Setup")
    print("=" * 50)

    integration = ComposrAPIIntegration()

    print("🌍 Web Integration Sites:")
    for site_name, config in integration.composr_config.items():
        print(f"  {site_name.title()}:")
        print(f"    URL: {config['url']}")
        print(f"    Public HTML: {config['public_html']}")
        print(f"    CopyParty Path: {config['copyparty_path']}")

    print("\n📁 Setting up web file synchronization...")
    integration.setup_web_file_sync()

    print("\n⚙️ Generating CopyParty configuration...")
    config_file = integration.generate_copyparty_composr_config()
    print(f"✅ Generated: {config_file}")

    print("\n🔗 Web Access URLs:")
    print("  http://raywonderis.me/~dom/copyparty/")
    print("  http://devinecreations.net/copyparty/")

    print("\n📋 Next Steps:")
    print("1. Set Composr API keys in integration.api_keys")
    print("2. Run: ./start-copyparty-composr-integrated.sh")
    print("3. Test web integration via PHP files")

if __name__ == "__main__":
    main()