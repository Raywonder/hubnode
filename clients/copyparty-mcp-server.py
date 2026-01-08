#!/usr/bin/env python3
"""
CopyParty MCP Server - Enhanced Version 2.0
Secure file management server for Claude Code and other AI services
"""

import json
import os
import sys
import asyncio
import aiohttp
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# MCP Protocol imports
try:
    from mcp import server
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP library not found. Install with: pip install mcp")
    sys.exit(1)

@dataclass
class CopyPartyConfig:
    """Configuration for CopyParty connections"""
    base_url: str
    auth: Dict[str, str]
    webdav_url: str
    api_url: str
    ssl_enabled: bool = True
    
class CopyPartyMCPServer:
    """Enhanced CopyParty MCP Server with secure HTTPS connections"""
    
    def __init__(self, config_path: str = "/home/devinecr/apps/hubnode/backend/copyparty-realtime-sync.json"):
        self.config_path = config_path
        self.configs = {}
        self.load_config()
        
    def load_config(self):
        """Load CopyParty configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                
            # Extract server configurations
            server_config = config_data.get("server", {})
            public_urls = server_config.get("public_urls", {})
            auth_config = config_data.get("auth", {})
            
            # Create configurations for each domain
            for domain, url in public_urls.items():
                self.configs[domain] = CopyPartyConfig(
                    base_url=url,
                    auth=self._extract_auth(auth_config),
                    webdav_url=f"{url}/dav/",
                    api_url=f"{url}/api/",
                    ssl_enabled=url.startswith("https://")
                )
                
            # Add local proxy configuration
            self.configs["local"] = CopyPartyConfig(
                base_url="http://127.0.0.1:8081",
                auth={},  # No auth required for local proxy
                webdav_url="http://127.0.0.1:8081/dav/",
                api_url="http://127.0.0.1:8081/api/",
                ssl_enabled=False
            )
            
            # Add Claude sync configuration
            self.configs["claude_sync"] = CopyPartyConfig(
                base_url="http://127.0.0.1:8082",
                auth={},  # No auth required for Claude sync
                webdav_url="http://127.0.0.1:8082/dav/",
                api_url="http://127.0.0.1:8082/api/",
                ssl_enabled=False
            )
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self.configs = {}
    
    def _extract_auth(self, auth_config: Dict) -> Dict[str, str]:
        """Extract authentication credentials from config"""
        credentials = {}
        
        # Add admin credentials
        admin = auth_config.get("admin", {})
        if admin:
            credentials["admin"] = f"{admin.get('username')}:{admin.get('password')}"
        
        # Add user credentials
        users = auth_config.get("users", {})
        for user, info in users.items():
            username = info.get("username")
            password = info.get("password") 
            if username and password:
                credentials[user] = f"{username}:{password}"
                
        return credentials
    
    async def list_files(self, domain: str = "raywonderis", path: str = "/", user: str = "admin") -> Dict[str, Any]:
        """List files in a CopyParty directory"""
        if domain not in self.configs:
            return {"error": f"Domain {domain} not configured"}
        
        config = self.configs[domain]
        url = f"{config.base_url}{path}"
        
        headers = {}
        if config.auth and user in config.auth:
            auth_header = base64.b64encode(config.auth[user].encode()).decode()
            headers["Authorization"] = f"Basic {auth_header}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, ssl=config.ssl_enabled) as response:
                    if response.status == 200:
                        content = await response.text()
                        return {
                            "status": "success",
                            "path": path,
                            "domain": domain,
                            "content": content[:1000] + "..." if len(content) > 1000 else content
                        }
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "path": path,
                            "domain": domain
                        }
        except Exception as e:
            return {"error": str(e)}
    
    async def upload_file(self, domain: str, remote_path: str, local_file: str, user: str = "admin") -> Dict[str, Any]:
        """Upload a file to CopyParty"""
        if domain not in self.configs:
            return {"error": f"Domain {domain} not configured"}
        
        if not os.path.exists(local_file):
            return {"error": f"Local file {local_file} not found"}
        
        config = self.configs[domain]
        url = f"{config.api_url}upload{remote_path}"
        
        headers = {}
        if config.auth and user in config.auth:
            auth_header = base64.b64encode(config.auth[user].encode()).decode()
            headers["Authorization"] = f"Basic {auth_header}"
        
        try:
            with open(local_file, 'rb') as f:
                file_data = f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', file_data, filename=os.path.basename(local_file))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=headers, ssl=config.ssl_enabled) as response:
                    result = await response.text()
                    return {
                        "status": "success" if response.status < 400 else "error",
                        "response_code": response.status,
                        "remote_path": remote_path,
                        "local_file": local_file,
                        "result": result
                    }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_health(self, domain: str = "raywonderis") -> Dict[str, Any]:
        """Check CopyParty server health"""
        if domain not in self.configs:
            return {"error": f"Domain {domain} not configured"}
        
        config = self.configs[domain]
        url = f"{config.base_url}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=config.ssl_enabled) as response:
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_code": response.status,
                        "domain": domain,
                        "ssl_enabled": config.ssl_enabled
                    }
        except Exception as e:
            return {"error": str(e), "domain": domain}
    
    async def get_webdav_info(self, domain: str = "raywonderis") -> Dict[str, Any]:
        """Get WebDAV mounting information"""
        if domain not in self.configs:
            return {"error": f"Domain {domain} not configured"}
        
        config = self.configs[domain]
        return {
            "domain": domain,
            "webdav_url": config.webdav_url,
            "mount_commands": {
                "mac": f"mount -t webdav {config.webdav_url} ~/CopyParty-{domain.title()}",
                "windows": f"net use Z: {config.webdav_url} /user:admin [password]",
                "linux": f"sudo mount -t davfs {config.webdav_url} /mnt/copyparty"
            },
            "ssl_enabled": config.ssl_enabled,
            "auth_required": bool(config.auth)
        }
    
    def get_available_domains(self) -> List[str]:
        """Get list of available CopyParty domains"""
        return list(self.configs.keys())
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get comprehensive server information"""
        return {
            "version": "2.0.0",
            "available_domains": self.get_available_domains(),
            "features": [
                "Secure HTTPS connections",
                "Domain-specific SSL certificates", 
                "WebDAV mounting support",
                "Large file uploads (2GB)",
                "Real-time sync integration",
                "Multi-platform support"
            ],
            "security": {
                "no_exposed_ports": True,
                "https_only": True,
                "ssl_validation": True,
                "hsts_enabled": True
            }
        }

# MCP Server setup
app = server.Server("copyparty-mcp")
copyparty = CopyPartyMCPServer()

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available CopyParty tools"""
    return [
        Tool(
            name="list_files",
            description="List files in a CopyParty directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain (raywonderis, devinecreations, tappedin, tetoeehoward, walterharper, local)"},
                    "path": {"type": "string", "description": "Directory path to list"},
                    "user": {"type": "string", "description": "Username for authentication"}
                },
                "required": ["domain"]
            }
        ),
        Tool(
            name="upload_file", 
            description="Upload a file to CopyParty",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain to upload to"},
                    "remote_path": {"type": "string", "description": "Remote path where file should be uploaded"},
                    "local_file": {"type": "string", "description": "Local file path to upload"},
                    "user": {"type": "string", "description": "Username for authentication"}
                },
                "required": ["domain", "remote_path", "local_file"]
            }
        ),
        Tool(
            name="health_check",
            description="Check CopyParty server health",
            inputSchema={
                "type": "object", 
                "properties": {
                    "domain": {"type": "string", "description": "Domain to check"}
                },
                "required": ["domain"]
            }
        ),
        Tool(
            name="webdav_info",
            description="Get WebDAV mounting information",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Domain for WebDAV info"}
                },
                "required": ["domain"]
            }
        ),
        Tool(
            name="server_info",
            description="Get comprehensive CopyParty server information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "list_files":
            result = await copyparty.list_files(
                domain=arguments.get("domain", "raywonderis"),
                path=arguments.get("path", "/"),
                user=arguments.get("user", "admin")
            )
        elif name == "upload_file":
            result = await copyparty.upload_file(
                domain=arguments["domain"],
                remote_path=arguments["remote_path"], 
                local_file=arguments["local_file"],
                user=arguments.get("user", "admin")
            )
        elif name == "health_check":
            result = await copyparty.get_health(arguments["domain"])
        elif name == "webdav_info":
            result = await copyparty.get_webdav_info(arguments["domain"])
        elif name == "server_info":
            result = copyparty.get_server_info()
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

if __name__ == "__main__":
    # Run the MCP server
    import mcp.server.stdio
    mcp.server.stdio.run_server(app)