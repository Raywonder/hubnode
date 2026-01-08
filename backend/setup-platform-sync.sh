#!/bin/bash
# Platform Sync Setup for /home/devinecr/shared/*
# Creates synchronized directories for cross-platform access

set -e

SHARED_ROOT="/home/devinecr/shared"
HUBNODE_ROOT="/home/devinecr/apps/hubnode"

echo "=== Setting up Platform Sync in /home/devinecr/shared/* ==="
echo "Shared root: $SHARED_ROOT"

# Create main shared directory structure
mkdir -p "$SHARED_ROOT"
mkdir -p "$SHARED_ROOT/platforms"
mkdir -p "$SHARED_ROOT/sync"
mkdir -p "$SHARED_ROOT/transfers"
mkdir -p "$SHARED_ROOT/builds"
mkdir -p "$SHARED_ROOT/clients"

# Platform-specific sync directories
echo "Creating platform sync directories..."

# macOS sync
mkdir -p "$SHARED_ROOT/platforms/macos"
mkdir -p "$SHARED_ROOT/platforms/macos/apps"
mkdir -p "$SHARED_ROOT/platforms/macos/builds"
mkdir -p "$SHARED_ROOT/platforms/macos/uploads"
mkdir -p "$SHARED_ROOT/platforms/macos/downloads"

# Windows sync
mkdir -p "$SHARED_ROOT/platforms/windows"
mkdir -p "$SHARED_ROOT/platforms/windows/apps"
mkdir -p "$SHARED_ROOT/platforms/windows/builds"
mkdir -p "$SHARED_ROOT/platforms/windows/uploads"
mkdir -p "$SHARED_ROOT/platforms/windows/downloads"

# Linux sync
mkdir -p "$SHARED_ROOT/platforms/linux"
mkdir -p "$SHARED_ROOT/platforms/linux/apps"
mkdir -p "$SHARED_ROOT/platforms/linux/builds"
mkdir -p "$SHARED_ROOT/platforms/linux/uploads"
mkdir -p "$SHARED_ROOT/platforms/linux/downloads"

# iOS sync
mkdir -p "$SHARED_ROOT/platforms/ios"
mkdir -p "$SHARED_ROOT/platforms/ios/projects"
mkdir -p "$SHARED_ROOT/platforms/ios/builds"
mkdir -p "$SHARED_ROOT/platforms/ios/uploads"
mkdir -p "$SHARED_ROOT/platforms/ios/downloads"

# Android sync
mkdir -p "$SHARED_ROOT/platforms/android"
mkdir -p "$SHARED_ROOT/platforms/android/projects"
mkdir -p "$SHARED_ROOT/platforms/android/builds"
mkdir -p "$SHARED_ROOT/platforms/android/uploads"
mkdir -p "$SHARED_ROOT/platforms/android/downloads"

# Application-specific sync directories
echo "Creating application sync directories..."

# UFM (Universal File Manager)
mkdir -p "$SHARED_ROOT/sync/ufm"
mkdir -p "$SHARED_ROOT/sync/ufm/source"
mkdir -p "$SHARED_ROOT/sync/ufm/builds"
mkdir -p "$SHARED_ROOT/sync/ufm/assets"
ln -sfn "/home/devinecr/apps/ufm-macos" "$SHARED_ROOT/sync/ufm/macos-source"

# PatchMate
mkdir -p "$SHARED_ROOT/sync/patchmate"
mkdir -p "$SHARED_ROOT/sync/patchmate/source"
mkdir -p "$SHARED_ROOT/sync/patchmate/builds"
mkdir -p "$SHARED_ROOT/sync/patchmate/assets"
ln -sfn "/home/tappedin/apps/patchmate-macos" "$SHARED_ROOT/sync/patchmate/macos-source"

# BEMA Mobile
mkdir -p "$SHARED_ROOT/sync/bema"
mkdir -p "$SHARED_ROOT/sync/bema/source"
mkdir -p "$SHARED_ROOT/sync/bema/builds"
mkdir -p "$SHARED_ROOT/sync/bema/assets"
ln -sfn "/home/tappedin/apps/bema-mobile" "$SHARED_ROOT/sync/bema/mobile-source"

# SonoBus
mkdir -p "$SHARED_ROOT/sync/sonobus"
mkdir -p "$SHARED_ROOT/sync/sonobus/enhanced"
mkdir -p "$SHARED_ROOT/sync/sonobus/original"
mkdir -p "$SHARED_ROOT/sync/sonobus/builds"
ln -sfn "/home/dom/apps/sonobus-macos" "$SHARED_ROOT/sync/sonobus/enhanced-source"
ln -sfn "/home/dom/apps/sonobus-original" "$SHARED_ROOT/sync/sonobus/original-source"

# Transfer directories for file exchange
echo "Setting up transfer directories..."

mkdir -p "$SHARED_ROOT/transfers/incoming"
mkdir -p "$SHARED_ROOT/transfers/outgoing"
mkdir -p "$SHARED_ROOT/transfers/processed"
mkdir -p "$SHARED_ROOT/transfers/archive"

# Client tools for each platform
echo "Setting up client tools..."

# Copy client tools to shared location
cp "$HUBNODE_ROOT/clients/copyparty/copyparty-sfx.py" "$SHARED_ROOT/clients/"
cp "$HUBNODE_ROOT/clients/copyparty/api-examples.py" "$SHARED_ROOT/clients/"
cp "$HUBNODE_ROOT/clients/mac_client.py" "$SHARED_ROOT/clients/"

# Create Windows client
cat > "$SHARED_ROOT/clients/windows_client.py" << 'EOF'
#!/usr/bin/env python3
"""
CopyParty Windows Client
Easy access to HubNode server from Windows
"""

import requests
import os
import sys
import json
import webbrowser
import subprocess

class WindowsCopyPartyClient:
    def __init__(self, server_url="http://raywonderis.me:3923", api_key="hub-node-api-2024"):
        self.server_url = server_url
        self.api_key = api_key
        self.downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "CopyParty")

        os.makedirs(self.downloads_dir, exist_ok=True)

    def mount_webdav(self):
        """Mount CopyParty as network drive on Windows"""
        try:
            webdav_url = f"{self.server_url}/"
            drive_letter = "Z:"

            print(f"🔗 Mounting WebDAV: {webdav_url} as {drive_letter}")

            # Use net use command to mount WebDAV
            cmd = f'net use {drive_letter} "{webdav_url}" /user:guest guest123'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ WebDAV mounted as {drive_letter}")
                print("Check 'This PC' in File Explorer")
            else:
                print(f"❌ Mount failed: {result.stderr}")

        except Exception as e:
            print(f"❌ WebDAV mount error: {e}")

    def open_shared_folder(self):
        """Open shared platform sync folder"""
        url = f"{self.server_url}/home/devinecr/shared"
        webbrowser.open(url)
        print(f"🌐 Opened shared folder: {url}")

if __name__ == "__main__":
    client = WindowsCopyPartyClient()

    if len(sys.argv) > 1:
        if sys.argv[1] == "mount":
            client.mount_webdav()
        elif sys.argv[1] == "shared":
            client.open_shared_folder()
    else:
        print("Windows CopyParty Client")
        print("Usage: python windows_client.py [mount|shared]")
EOF

# Create sync status tracking
cat > "$SHARED_ROOT/sync_status.json" << 'EOF'
{
  "last_sync": null,
  "platforms": {
    "macos": {"status": "ready", "last_update": null},
    "windows": {"status": "ready", "last_update": null},
    "linux": {"status": "ready", "last_update": null},
    "ios": {"status": "ready", "last_update": null},
    "android": {"status": "ready", "last_update": null}
  },
  "applications": {
    "ufm": {"status": "ready", "platforms": ["macos", "windows", "linux"]},
    "patchmate": {"status": "ready", "platforms": ["macos", "windows"]},
    "bema": {"status": "ready", "platforms": ["ios", "android"]},
    "sonobus": {"status": "ready", "platforms": ["macos", "windows", "linux"]}
  }
}
EOF

# Set permissions
chown -R devinecr:devinecr "$SHARED_ROOT"
chmod -R 755 "$SHARED_ROOT"

# Make transfer directories writable by all users
chmod -R 777 "$SHARED_ROOT/transfers"
chmod -R 777 "$SHARED_ROOT/platforms/*/uploads"
chmod -R 777 "$SHARED_ROOT/platforms/*/downloads"

echo "=== Platform sync setup complete! ==="
echo ""
echo "Shared directory structure:"
echo "  $SHARED_ROOT/platforms/          - Platform-specific directories"
echo "  $SHARED_ROOT/sync/               - Application sync directories"
echo "  $SHARED_ROOT/transfers/          - File transfer staging"
echo "  $SHARED_ROOT/clients/            - Client tools for all platforms"
echo ""
echo "Platform directories created for:"
echo "  - macOS, Windows, Linux, iOS, Android"
echo ""
echo "Application sync directories:"
ls -la "$SHARED_ROOT/sync/"