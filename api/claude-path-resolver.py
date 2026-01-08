#!/usr/bin/env python3
"""
Claude Path Resolver
Automatically detects and maps local file paths to proper CopyParty paths
Handles authentication and path resolution for all platforms
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudePathResolver:
    """Resolves local file paths to CopyParty paths with automatic detection"""
    
    def __init__(self, config_file: str = "/home/devinecr/apps/hubnode/backend/copyparty-realtime-sync.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.path_mappings = self.build_path_mappings()
        self.auth_cache = {}
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
            
    def build_path_mappings(self) -> Dict[str, Dict]:
        """Build comprehensive path mappings from config"""
        mappings = {}
        
        if not self.config:
            return mappings
            
        # Extract all sync paths
        sync_paths = self.config.get("sync_paths", {})
        
        for category, paths in sync_paths.items():
            for name, copyparty_path in paths.items():
                # Map CopyParty path back to local filesystem
                local_path = self.resolve_copyparty_to_local(copyparty_path)
                if local_path:
                    mappings[local_path] = {
                        "copyparty_path": copyparty_path,
                        "category": category,
                        "name": name,
                        "auth_required": self.get_auth_for_path(copyparty_path)
                    }
                    
        return mappings
        
    def resolve_copyparty_to_local(self, copyparty_path: str) -> Optional[str]:
        """Convert CopyParty path to local filesystem path"""
        path_map = {
            # Composr sites
            "/composr-raywonderis/uploads": "/home/dom/public_html/uploads",
            "/composr-raywonderis/website_specific": "/home/dom/public_html/uploads/website_specific",
            "/composr-raywonderis/website_specific/apps": "/home/dom/public_html/uploads/website_specific/apps",
            "/composr-raywonderis/apps/audio-portrait": "/home/dom/public_html/uploads/website_specific/apps/audio-portrait",
            "/composr-raywonderis/filedump": "/home/dom/public_html/uploads/filedump",
            "/composr-raywonderis/attachments": "/home/dom/public_html/uploads/attachments",
            "/composr-raywonderis/galleries": "/home/dom/public_html/uploads/galleries",
            "/incoming-raywonderis": "/home/dom/public_html/uploads/incoming",
            
            "/composr-devinecreations/uploads": "/home/devinecr/devinecreations.net/uploads",
            "/composr-devinecreations/website_specific": "/home/devinecr/devinecreations.net/uploads/website_specific",
            "/composr-devinecreations/website_specific/apps": "/home/devinecr/devinecreations.net/uploads/website_specific/apps",
            "/composr-devinecreations/apps/audio-portrait": "/home/devinecr/devinecreations.net/uploads/website_specific/apps/audio-portrait",
            "/composr-devinecreations/filedump": "/home/devinecr/devinecreations.net/uploads/filedump",
            "/composr-devinecreations/attachments": "/home/devinecr/devinecreations.net/uploads/attachments",
            "/composr-devinecreations/galleries": "/home/devinecr/devinecreations.net/uploads/galleries",
            "/incoming-devinecreations": "/home/devinecr/devinecreations.net/uploads/incoming",
            
            # WordPress sites
            "/wp-tappedin/uploads": "/home/tappedin/public_html/wp-content/uploads",
            "/wp-tappedin/podcast-submissions": "/home/tappedin/public_html/wp-content/uploads/podcast-submissions",
            "/incoming-tappedin": "/home/tappedin/public_html/wp-content/uploads/incoming",
            "/wp-tetoeehoward/uploads": "/home/tetoeehoward/public_html/wp-content/uploads",
            "/wp-walterharper/uploads": "/home/wharper/public_html/wp-content/uploads",
            
            # Application directories
            "/apps-tappedin": "/home/tappedin/apps",
            "/apps-devinecr": "/home/devinecr/apps",
            "/apps-dom": "/home/dom/apps",
            "/audio-portrait-dev": "/home/tappedin/apps/audio-portrait",
            "/audio-portrait-dist": "/home/devinecr/apps/hubnode/api/audio-portrait/uploads",
            
            # API system
            "/hubnode-clients": "/home/devinecr/apps/hubnode/clients",
            "/hubnode-api": "/home/devinecr/apps/hubnode/api",
            "/hubnode-backend": "/home/devinecr/apps/hubnode/backend",
            
            # WHMCS
            "/whmcs-devinecr": "/home/devinecr/public_html",
            
            # User directories
            "/root-tappedin": "/home/tappedin",
            "/root-devinecr": "/home/devinecr",
            "/root-dom": "/home/dom",
            "/root-tetoeehoward": "/home/tetoeehoward",
            "/root-wharper": "/home/wharper",
            
            # Shared storage
            "/shared": "/home/devinecr/shared",
            "/downloads-devinecr": "/home/devinecr/downloads",
            "/Downloads-devinecr": "/home/devinecr/Downloads",
            "/attachments-devinecr": "/home/devinecr/attachments",
            "/Attachments-devinecr": "/home/devinecr/Attachments"
        }
        
        return path_map.get(copyparty_path)
        
    def get_auth_for_path(self, copyparty_path: str) -> Dict[str, str]:
        """Get authentication credentials for a specific path"""
        # Default to admin credentials for most paths
        auth = {
            "username": "admin",
            "password": "hub-node-api-2024"
        }
        
        # Specific user credentials for their own directories
        if "/root-tappedin" in copyparty_path or "/apps-tappedin" in copyparty_path or "/wp-tappedin" in copyparty_path:
            auth = {"username": "tappedin", "password": "tappedin-uploads-2024"}
        elif "/root-dom" in copyparty_path or "/apps-dom" in copyparty_path or "/composr-raywonderis" in copyparty_path:
            auth = {"username": "dom", "password": "composr-import-2024"}
        elif "/root-wharper" in copyparty_path or "/wp-walterharper" in copyparty_path:
            auth = {"username": "wharper", "password": "walter-files-2024"}
        elif "/root-tetoeehoward" in copyparty_path or "/wp-tetoeehoward" in copyparty_path:
            auth = {"username": "tetoeehoward", "password": "tetoee-files-2024"}
        elif "/audio-portrait" in copyparty_path:
            auth = {"username": "audioportrait", "password": "audio-portrait-api-2025"}
            
        return auth
        
    def resolve_local_to_copyparty(self, local_path: str) -> Optional[Tuple[str, Dict]]:
        """Resolve local file path to CopyParty path and auth"""
        local_path = os.path.abspath(local_path)
        
        # Find the best matching path
        best_match = None
        best_length = 0
        
        for mapped_local_path, mapping_info in self.path_mappings.items():
            if local_path.startswith(mapped_local_path):
                if len(mapped_local_path) > best_length:
                    best_match = mapping_info
                    best_length = len(mapped_local_path)
                    
        if best_match:
            # Calculate relative path and build full CopyParty path
            relative_path = local_path[best_length:].lstrip('/')
            copyparty_path = best_match["copyparty_path"]
            if relative_path:
                copyparty_path = f"{copyparty_path.rstrip('/')}/{relative_path}"
                
            return copyparty_path, best_match["auth_required"]
            
        return None, {}
        
    def get_public_url(self, local_path: str, domain: str = "raywonderis") -> Optional[str]:
        """Get public URL for a file based on domain"""
        copyparty_path, _ = self.resolve_local_to_copyparty(local_path)
        if not copyparty_path:
            return None
            
        public_urls = self.config.get("server", {}).get("public_urls", {})
        base_url = public_urls.get(domain, "https://files.raywonderis.me")
        
        return f"{base_url}{copyparty_path}"
        
    def get_webdav_url(self, local_path: str, domain: str = "local") -> Optional[str]:
        """Get WebDAV URL for mounting"""
        copyparty_path, _ = self.resolve_local_to_copyparty(local_path)
        if not copyparty_path:
            return None
            
        webdav_urls = self.config.get("client_config", {}).get("sync_methods", {}).get("webdav", {}).get("urls", {})
        base_url = webdav_urls.get(domain, "http://127.0.0.1:8081")
        
        # Remove /dav/ from base_url if it exists to avoid duplication
        if base_url.endswith("/dav/"):
            base_url = base_url[:-5]
        
        return f"{base_url}/dav{copyparty_path}"
        
    def list_available_paths(self) -> List[Dict]:
        """List all available CopyParty paths with metadata"""
        paths = []
        
        for local_path, mapping_info in self.path_mappings.items():
            paths.append({
                "local_path": local_path,
                "copyparty_path": mapping_info["copyparty_path"],
                "category": mapping_info["category"],
                "name": mapping_info["name"],
                "exists": os.path.exists(local_path),
                "readable": os.access(local_path, os.R_OK) if os.path.exists(local_path) else False,
                "writable": os.access(local_path, os.W_OK) if os.path.exists(local_path) else False
            })
            
        return sorted(paths, key=lambda x: x["local_path"])
        
    def auto_detect_file_category(self, local_path: str) -> str:
        """Automatically detect what category a file belongs to"""
        local_path = local_path.lower()
        
        if any(x in local_path for x in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            return "image"
        elif any(x in local_path for x in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
            return "video"
        elif any(x in local_path for x in ['.mp3', '.wav', '.flac', '.aac', '.ogg']):
            return "audio"
        elif any(x in local_path for x in ['.pdf', '.doc', '.docx', '.txt', '.md']):
            return "document"
        elif any(x in local_path for x in ['.zip', '.tar', '.gz', '.rar', '.7z']):
            return "archive"
        elif 'audio-portrait' in local_path:
            return "application"
        elif any(x in local_path for x in ['/uploads/', '/wp-content/']):
            return "upload"
        else:
            return "file"
            
def main():
    """Test the path resolver"""
    resolver = ClaudePathResolver()
    
    # Test some paths
    test_paths = [
        "/home/dom/public_html/uploads/test.jpg",
        "/home/devinecr/apps/hubnode/api/audio-portrait/app.py",
        "/home/tappedin/public_html/wp-content/uploads/podcast.mp3"
    ]
    
    for path in test_paths:
        copyparty_path, auth = resolver.resolve_local_to_copyparty(path)
        public_url = resolver.get_public_url(path)
        webdav_url = resolver.get_webdav_url(path)
        category = resolver.auto_detect_file_category(path)
        
        print(f"\nLocal: {path}")
        print(f"CopyParty: {copyparty_path}")
        print(f"Auth: {auth.get('username', 'none')}")
        print(f"Public URL: {public_url}")
        print(f"WebDAV URL: {webdav_url}")
        print(f"Category: {category}")

if __name__ == "__main__":
    main()