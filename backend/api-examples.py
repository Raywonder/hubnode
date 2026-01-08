#!/usr/bin/env python3
"""
CopyParty Hub Node API Examples
Upload/Download operations via REST API
"""

import requests
import json

# API Configuration
API_BASE = "http://localhost:3923"
API_KEY = "hub-node-api-2024"

def upload_file(file_path, remote_path=""):
    """Upload file via API"""
    url = f"{API_BASE}/api/upload"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'path': remote_path, 'api_key': API_KEY}

        response = requests.post(url, files=files, data=data)
        return response.json()

def download_file(remote_path, local_path):
    """Download file via API"""
    url = f"{API_BASE}/api/download/{remote_path}"
    params = {'api_key': API_KEY}

    response = requests.get(url, params=params, stream=True)

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return response.status_code == 200

def list_files(path=""):
    """List files via API"""
    url = f"{API_BASE}/api/list"
    params = {'path': path, 'api_key': API_KEY}

    response = requests.get(url, params=params)
    return response.json()

def get_node_status():
    """Get hub node status"""
    url = f"{API_BASE}/api/status"
    params = {'api_key': API_KEY}

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
