#!/usr/bin/env python3
"""
CopyParty Authentication Configuration
Supports local auth and WHMCS integration
"""

import hashlib
import hmac
import json
import requests
import time
from pathlib import Path

class CopyPartyAuth:
    def __init__(self):
        self.auth_file = "auth_users.json"
        self.whmcs_config = {
            "enabled": False,
            "api_url": "https://raywonderis.me/whmcs/includes/api.php",
            "api_identifier": "",
            "api_secret": "",
            "required_product_ids": [1, 2, 3]  # Product IDs that grant access
        }
        self.load_auth_config()

    def load_auth_config(self):
        """Load authentication configuration"""
        if Path(self.auth_file).exists():
            with open(self.auth_file, 'r') as f:
                self.users = json.load(f)
        else:
            # Default users
            self.users = {
                "admin": {
                    "password": "admin123",
                    "permissions": "r,rw,a",  # read, read-write, admin
                    "full_server_access": True,
                    "root_access": True,
                    "description": "Full system administrator"
                },
                "devinecr": {
                    "password": "devinecr123",
                    "permissions": "r,rw",
                    "full_server_access": True,
                    "root_access": False,
                    "description": "Developer account - Devine Creations"
                },
                "tappedin": {
                    "password": "tappedin123",
                    "permissions": "r,rw",
                    "full_server_access": False,
                    "root_access": False,
                    "description": "TappedIn.fm account"
                },
                "dom": {
                    "password": "dom123",
                    "permissions": "r,rw",
                    "full_server_access": False,
                    "root_access": False,
                    "description": "Dom's development account"
                },
                "guest": {
                    "password": "guest123",
                    "permissions": "r",
                    "full_server_access": False,
                    "root_access": False,
                    "description": "Guest read-only access"
                }
            }
            self.save_auth_config()

    def save_auth_config(self):
        """Save authentication configuration"""
        with open(self.auth_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def generate_copyparty_auth_file(self):
        """Generate CopyParty auth file format"""
        auth_lines = []

        for username, config in self.users.items():
            password = config["password"]
            permissions = config["permissions"]

            # Add volume-specific permissions for full server access users
            if config.get("full_server_access"):
                if config.get("root_access"):
                    # Full root filesystem access
                    auth_lines.append(f"{username}:{password}:/::r,rw")
                    auth_lines.append(f"{username}:{password}:/home::r,rw")
                    auth_lines.append(f"{username}:{password}:/var::r,rw")
                    auth_lines.append(f"{username}:{password}:/opt::r,rw")
                    auth_lines.append(f"{username}:{password}:/tmp::r,rw")
                else:
                    # Full home directories access
                    auth_lines.append(f"{username}:{password}:/home::r,rw")
                    auth_lines.append(f"{username}:{password}:/home/devinecr::r,rw")
                    auth_lines.append(f"{username}:{password}:/home/tappedin::r,rw")
                    auth_lines.append(f"{username}:{password}:/home/dom::r,rw")
            else:
                # Limited access to specific directories
                auth_lines.append(f"{username}:{password}:/home/{username}::{permissions}")
                auth_lines.append(f"{username}:{password}:/home/devinecr/apps/hubnode/shared::{permissions}")

            # Base access for all users
            auth_lines.append(f"{username}:{password}:uploads::{permissions}")
            auth_lines.append(f"{username}:{password}:downloads::{permissions}")
            auth_lines.append(f"{username}:{password}:shared::{permissions}")

        # Write auth file
        with open("copyparty_auth.txt", "w") as f:
            for line in auth_lines:
                f.write(line + "\n")

        return "copyparty_auth.txt"

    def verify_whmcs_user(self, email, password):
        """Verify user against WHMCS"""
        if not self.whmcs_config["enabled"]:
            return False, "WHMCS authentication disabled"

        try:
            # WHMCS API call to validate login
            api_data = {
                "action": "ValidateLogin",
                "email": email,
                "password2": password,
                "responsetype": "json"
            }

            # Add WHMCS API authentication
            api_data.update({
                "identifier": self.whmcs_config["api_identifier"],
                "secret": self.whmcs_config["api_secret"]
            })

            response = requests.post(
                self.whmcs_config["api_url"],
                data=api_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("result") == "success":
                    user_id = result.get("userid")

                    # Check if user has required products
                    if self.check_whmcs_products(user_id):
                        return True, {"user_id": user_id, "email": email}
                    else:
                        return False, "No valid products found"
                else:
                    return False, result.get("message", "Authentication failed")
            else:
                return False, f"WHMCS API error: {response.status_code}"

        except Exception as e:
            return False, f"WHMCS connection error: {str(e)}"

    def check_whmcs_products(self, user_id):
        """Check if user has required products in WHMCS"""
        try:
            api_data = {
                "action": "GetClientsProducts",
                "clientid": user_id,
                "responsetype": "json",
                "identifier": self.whmcs_config["api_identifier"],
                "secret": self.whmcs_config["api_secret"]
            }

            response = requests.post(
                self.whmcs_config["api_url"],
                data=api_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("result") == "success":
                    products = result.get("products", {}).get("product", [])

                    for product in products:
                        if (product.get("pid") in self.whmcs_config["required_product_ids"] and
                            product.get("status") == "Active"):
                            return True

                    return False
                else:
                    return False
            else:
                return False

        except Exception as e:
            print(f"WHMCS product check error: {e}")
            return False

    def add_whmcs_user(self, email, user_data):
        """Add WHMCS user to local auth"""
        username = email.split("@")[0]  # Use email prefix as username

        self.users[username] = {
            "password": f"whmcs_{int(time.time())}",  # Temporary password
            "permissions": "r,rw",
            "full_server_access": True,
            "root_access": False,
            "description": f"WHMCS User: {email}",
            "whmcs_user_id": user_data.get("user_id"),
            "email": email,
            "created": time.time()
        }

        self.save_auth_config()
        return username

    def setup_whmcs_integration(self, api_identifier, api_secret, api_url=None):
        """Setup WHMCS integration"""
        self.whmcs_config["enabled"] = True
        self.whmcs_config["api_identifier"] = api_identifier
        self.whmcs_config["api_secret"] = api_secret

        if api_url:
            self.whmcs_config["api_url"] = api_url

        # Save config
        with open("whmcs_config.json", "w") as f:
            json.dump(self.whmcs_config, f, indent=2)

        print("✅ WHMCS integration configured")

def generate_advanced_copyparty_config():
    """Generate advanced CopyParty configuration with full server access"""
    auth = CopyPartyAuth()
    auth_file = auth.generate_copyparty_auth_file()

    config_content = f'''#!/bin/bash
# Advanced CopyParty Configuration with Full Server Access
# Generated by auth_config.py

python3 copyparty-sfx.py \\
    --host 0.0.0.0 \\
    --port 3923 \\
    --name "CopyParty Hub Node - Full Server Access" \\
    \\
    --accounts-file {auth_file} \\
    \\
    --volume "./uploads:/uploads:rw" \\
    --volume "./downloads:/downloads:rw" \\
    --volume "./linked_apps:/apps:r" \\
    --volume "./shared_uploads:/shared/uploads:rw" \\
    --volume "./shared_downloads:/shared/downloads:rw" \\
    --volume "./client_access:/clients:r" \\
    \\
    --volume "/home:/home:r,rw" \\
    --volume "/home/devinecr:/devinecr:r,rw" \\
    --volume "/home/tappedin:/tappedin:r,rw" \\
    --volume "/home/dom:/dom:r,rw" \\
    \\
    --volume "/var/www:/www:r" \\
    --volume "/var/log:/logs:r" \\
    --volume "/tmp:/tmp:rw" \\
    --volume "/opt:/opt:r" \\
    \\
    --enable-uploads \\
    --enable-downloads \\
    --enable-webdav \\
    --enable-search \\
    --enable-thumbs \\
    --enable-zip \\
    --enable-markdown \\
    --enable-dotfiles \\
    \\
    --log-file ./logs/copyparty-full-access.log \\
    --access-log ./logs/access-full.log \\
    \\
    --html-head '<style>
        body {{ font-family: Arial, sans-serif; }}
        .server-warning {{ background: #ff9800; color: white; padding: 10px; text-align: center; }}
        .auth-info {{ background: #e3f2fd; padding: 15px; margin: 10px; border-radius: 5px; }}
        .volume-list {{ background: #f5f5f5; padding: 10px; border-left: 4px solid #2196f3; }}
    </style>' \\
    \\
    --html-top '<div class="server-warning">
        ⚠️ FULL SERVER ACCESS ENABLED - Authorized Users Only
    </div>
    <div class="auth-info">
        <h3>🔐 Available Access Levels:</h3>
        <ul>
            <li><strong>Admin:</strong> Full root filesystem access</li>
            <li><strong>Developers:</strong> Home directories + shared areas</li>
            <li><strong>Users:</strong> Own directories + shared uploads</li>
            <li><strong>Guest:</strong> Read-only access</li>
        </ul>
        <p><strong>WHMCS Integration:</strong> {'Enabled' if auth.whmcs_config.get('enabled') else 'Disabled'}</p>
    </div>' \\
    \\
    --cors \\
    --verbose \\
    $@
'''

    with open("start-copyparty-full-access.sh", "w") as f:
        f.write(config_content)

    # Make executable
    import os
    os.chmod("start-copyparty-full-access.sh", 0o755)

    return "start-copyparty-full-access.sh"

def main():
    """Main configuration setup"""
    print("CopyParty Authentication Setup")
    print("=" * 50)

    auth = CopyPartyAuth()

    print("Current users:")
    for username, config in auth.users.items():
        access_level = "Full Server" if config.get("full_server_access") else "Limited"
        root_access = "Root" if config.get("root_access") else "User"
        print(f"  {username:<12} - {access_level} ({root_access}) - {config['description']}")

    print("\nGenerating CopyParty configuration files...")

    # Generate auth file
    auth_file = auth.generate_copyparty_auth_file()
    print(f"✅ Generated: {auth_file}")

    # Generate advanced config
    config_file = generate_advanced_copyparty_config()
    print(f"✅ Generated: {config_file}")

    print("\nTo enable WHMCS integration:")
    print("  python3 auth_config.py --setup-whmcs API_ID API_SECRET")

    print("\nTo start with full server access:")
    print("  ./start-copyparty-full-access.sh")

    print("\nWeb access URLs:")
    print("  http://raywonderis.me:3923/home       - Full home directories")
    print("  http://raywonderis.me:3923/devinecr  - Devine's files")
    print("  http://raywonderis.me:3923/tappedin  - TappedIn files")
    print("  http://raywonderis.me:3923/dom       - Dom's files")
    print("  http://raywonderis.me:3923/www       - Web server files")
    print("  http://raywonderis.me:3923/logs      - System logs")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--setup-whmcs":
        if len(sys.argv) < 4:
            print("Usage: python3 auth_config.py --setup-whmcs API_ID API_SECRET [API_URL]")
        else:
            auth = CopyPartyAuth()
            api_url = sys.argv[4] if len(sys.argv) > 4 else None
            auth.setup_whmcs_integration(sys.argv[2], sys.argv[3], api_url)
    else:
        main()