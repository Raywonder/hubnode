#!/usr/bin/env python3
"""
CopyParty Backend Configuration
Enhanced file server with upload/download, API, and hub-node capabilities
"""

import os
import sys

# CopyParty configuration settings
COPYPARTY_CONFIG = {
    # Server settings
    'host': '0.0.0.0',
    'port': 3923,
    'name': 'CopyParty Hub Node',

    # File handling
    'upload_dir': './uploads',
    'download_dir': './downloads',
    'temp_dir': './temp',

    # API settings
    'enable_api': True,
    'api_key': 'hub-node-api-2024',

    # Features
    'enable_uploads': True,
    'enable_downloads': True,
    'enable_webdav': True,
    'enable_ftp': False,
    'enable_search': True,
    'enable_thumbs': True,

    # Security
    'auth_users': {
        'admin': 'admin123',
        'user': 'user123'
    },

    # Hub node specific
    'node_id': 'hub-001',
    'cluster_mode': True
}

def setup_directories():
    """Create necessary directories"""
    dirs = [
        COPYPARTY_CONFIG['upload_dir'],
        COPYPARTY_CONFIG['download_dir'],
        COPYPARTY_CONFIG['temp_dir'],
        './logs',
        './data'
    ]

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

def generate_startup_script():
    """Generate CopyParty startup script"""
    script_content = f'''#!/bin/bash
# CopyParty Hub Node Startup Script

echo "Starting CopyParty Hub Node..."

# Create directories
mkdir -p uploads downloads temp logs data

# Start CopyParty with hub-node configuration
python3 copyparty-sfx.py \\
    --host {COPYPARTY_CONFIG['host']} \\
    --port {COPYPARTY_CONFIG['port']} \\
    --name "{COPYPARTY_CONFIG['name']}" \\
    --upload-dir {COPYPARTY_CONFIG['upload_dir']} \\
    --download-dir {COPYPARTY_CONFIG['download_dir']} \\
    --enable-uploads \\
    --enable-downloads \\
    --enable-webdav \\
    --enable-search \\
    --enable-thumbs \\
    --log-file ./logs/copyparty.log \\
    --verbose \\
    $@

echo "CopyParty Hub Node stopped."
'''

    with open('start-copyparty.sh', 'w') as f:
        f.write(script_content)

    os.chmod('start-copyparty.sh', 0o755)
    print("✓ Generated startup script: start-copyparty.sh")

def generate_api_examples():
    """Generate API usage examples"""
    api_examples = f'''#!/usr/bin/env python3
"""
CopyParty Hub Node API Examples
Upload/Download operations via REST API
"""

import requests
import json

# API Configuration
API_BASE = "http://localhost:{COPYPARTY_CONFIG['port']}"
API_KEY = "{COPYPARTY_CONFIG['api_key']}"

def upload_file(file_path, remote_path=""):
    """Upload file via API"""
    url = f"{{API_BASE}}/api/upload"

    with open(file_path, 'rb') as f:
        files = {{'file': f}}
        data = {{'path': remote_path, 'api_key': API_KEY}}

        response = requests.post(url, files=files, data=data)
        return response.json()

def download_file(remote_path, local_path):
    """Download file via API"""
    url = f"{{API_BASE}}/api/download/{{remote_path}}"
    params = {{'api_key': API_KEY}}

    response = requests.get(url, params=params, stream=True)

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return response.status_code == 200

def list_files(path=""):
    """List files via API"""
    url = f"{{API_BASE}}/api/list"
    params = {{'path': path, 'api_key': API_KEY}}

    response = requests.get(url, params=params)
    return response.json()

def get_node_status():
    """Get hub node status"""
    url = f"{{API_BASE}}/api/status"
    params = {{'api_key': API_KEY}}

    response = requests.get(url, params=params)
    return response.json()

# Example usage
if __name__ == "__main__":
    print("CopyParty Hub Node API Examples")
    print("================================")

    # Example calls (uncomment to use)
    # print("Node Status:", get_node_status())
    # print("File List:", list_files())
    # upload_result = upload_file("example.txt")
    # download_result = download_file("example.txt", "downloaded_example.txt")
'''

    with open('api-examples.py', 'w') as f:
        f.write(api_examples)

    os.chmod('api-examples.py', 0o755)
    print("✓ Generated API examples: api-examples.py")

def generate_docker_config():
    """Generate Docker configuration for Linux deployment"""
    dockerfile = f'''FROM python:3.9-slim

WORKDIR /app

# Install CopyParty
RUN pip install copyparty

# Copy configuration
COPY copyparty-sfx.py .
COPY start-copyparty.sh .
COPY copyparty-config.py .

# Create directories
RUN mkdir -p uploads downloads temp logs data

# Expose port
EXPOSE {COPYPARTY_CONFIG['port']}

# Start CopyParty
CMD ["./start-copyparty.sh"]
'''

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)

    docker_compose = f'''version: '3.8'

services:
  copyparty-hub:
    build: .
    container_name: copyparty-hub-node
    ports:
      - "{COPYPARTY_CONFIG['port']}:{COPYPARTY_CONFIG['port']}"
    volumes:
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - COPYPARTY_HOST={COPYPARTY_CONFIG['host']}
      - COPYPARTY_PORT={COPYPARTY_CONFIG['port']}
      - COPYPARTY_NAME={COPYPARTY_CONFIG['name']}
    restart: unless-stopped
    networks:
      - copyparty-network

networks:
  copyparty-network:
    driver: bridge
'''

    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)

    print("✓ Generated Docker configuration")

if __name__ == "__main__":
    print("Setting up CopyParty Hub Node Backend...")
    print("=" * 50)

    setup_directories()
    generate_startup_script()
    generate_api_examples()
    generate_docker_config()

    print("=" * 50)
    print("CopyParty Hub Node setup complete!")
    print(f"Server will run on: http://localhost:{COPYPARTY_CONFIG['port']}")
    print("Start with: ./start-copyparty.sh")
    print("API examples: python3 api-examples.py")