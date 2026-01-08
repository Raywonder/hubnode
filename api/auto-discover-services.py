#!/usr/bin/env python3
"""
Auto-Discovery Service Scanner
Automatically discovers and registers services from /home/*/apps/*
Updates gateway configuration with discovered services
"""

import os
import json
import glob
import re
from pathlib import Path

# Paths to scan
SCAN_PATHS = [
    "/home/*/apps/*",
    "/home/*/apps/*/api",
    "/home/*/apps/*/backend",
    "/home/*/apps/*/server",
]

# Gateway config file
GATEWAY_CONFIG = "/home/devinecr/apps/hubnode/api/discovered_services.json"

# Common service indicators
SERVICE_INDICATORS = {
    "flask": {
        "files": ["app.py", "main.py", "server.py", "api.py"],
        "patterns": [r"Flask\(__name__\)", r"from flask import", r"app\.run\("]
    },
    "express": {
        "files": ["app.js", "server.js", "index.js", "main.js"],
        "patterns": [r"express\(\)", r"require\(['\"]express['\"\)]", r"app\.listen\("]
    },
    "fastapi": {
        "files": ["main.py", "app.py", "api.py"],
        "patterns": [r"FastAPI\(", r"from fastapi import", r"uvicorn\.run\("]
    },
    "django": {
        "files": ["manage.py", "wsgi.py"],
        "patterns": [r"DJANGO_SETTINGS_MODULE", r"django\.setup\(\)"]
    },
    "node_http": {
        "files": ["server.js", "app.js", "index.js"],
        "patterns": [r"http\.createServer", r"require\(['\"]http['\"\)]"]
    }
}

def find_port_in_file(file_path):
    """Extract port number from source file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

            # Common port patterns
            port_patterns = [
                r"port['\"]?\s*[:=]\s*(\d{4,5})",
                r"PORT\s*=\s*(\d{4,5})",
                r"listen\(\s*(\d{4,5})",
                r"run\([^)]*port\s*=\s*(\d{4,5})",
                r"\.env.*PORT['\"]?\s*[:=]\s*(\d{4,5})",
            ]

            for pattern in port_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    port = int(match.group(1))
                    if 1000 <= port <= 65535:
                        return port
    except:
        pass
    return None

def find_service_name(path):
    """Extract service name from path or package.json"""
    # Try package.json first
    package_json = os.path.join(path, "package.json")
    if os.path.exists(package_json):
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                if 'name' in data:
                    return data['name']
        except:
            pass

    # Try setup.py
    setup_py = os.path.join(path, "setup.py")
    if os.path.exists(setup_py):
        try:
            with open(setup_py, 'r') as f:
                content = f.read()
                match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
                if match:
                    return match.group(1)
        except:
            pass

    # Use directory name
    return os.path.basename(path)

def detect_service_type(path):
    """Detect what type of service this is"""
    for service_type, indicators in SERVICE_INDICATORS.items():
        # Check for indicator files
        for file in indicators['files']:
            file_path = os.path.join(path, file)
            if os.path.exists(file_path):
                # Verify with pattern matching
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in indicators['patterns']:
                            if re.search(pattern, content):
                                return service_type, file_path
                except:
                    pass
    return None, None

def find_health_endpoint(path, service_type):
    """Try to determine health check endpoint"""
    # Common health endpoint patterns
    health_endpoints = ["/health", "/api/health", "/ping", "/status", "/api/status", "/"]

    # Read route definitions
    route_files = []
    if service_type in ['flask', 'fastapi']:
        route_files = glob.glob(os.path.join(path, "*.py"))
    elif service_type in ['express', 'node_http']:
        route_files = glob.glob(os.path.join(path, "*.js"))

    for file_path in route_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for endpoint in health_endpoints:
                    # Python patterns
                    if re.search(rf"@app\.route\(['\"]({endpoint})['\"]", content):
                        return endpoint
                    # JavaScript patterns
                    if re.search(rf"app\.(get|use)\(['\"]({endpoint})['\"]", content):
                        return endpoint
        except:
            pass

    return "/health"  # Default

def scan_for_services():
    """Scan all paths for services"""
    discovered = []

    for scan_path in SCAN_PATHS:
        paths = glob.glob(scan_path)

        for path in paths:
            if not os.path.isdir(path):
                continue

            # Skip if it's a node_modules or venv
            if 'node_modules' in path or 'venv' in path or '__pycache__' in path:
                continue

            # Detect service
            service_type, main_file = detect_service_type(path)
            if not service_type:
                continue

            # Get service info
            service_name = find_service_name(path)
            port = find_port_in_file(main_file) if main_file else None
            health_endpoint = find_health_endpoint(path, service_type)

            # Extract user from path
            user_match = re.search(r'/home/([^/]+)/', path)
            user = user_match.group(1) if user_match else 'unknown'

            service_info = {
                "name": service_name,
                "type": service_type,
                "path": path,
                "main_file": main_file,
                "port": port,
                "health_endpoint": health_endpoint,
                "user": user,
                "url": f"http://localhost:{port}" if port else None,
                "prefix": f"/{user}/{service_name.replace('-', '_')}",
                "description": f"{service_type.upper()} service in {user}'s apps"
            }

            discovered.append(service_info)
            print(f"✓ Found: {service_name} ({service_type}) - Port {port or 'unknown'} - {path}")

    return discovered

def generate_gateway_config(services):
    """Generate gateway configuration for discovered services"""
    config = {
        "discovered_at": "2025-10-03",
        "total_services": len(services),
        "services": {}
    }

    for service in services:
        if not service['port']:
            continue

        service_key = f"{service['user']}_{service['name'].replace('-', '_')}"

        config['services'][service_key] = {
            "name": service['name'],
            "url": service['url'],
            "prefix": service['prefix'],
            "health_endpoint": service['health_endpoint'],
            "description": service['description'],
            "user": service['user'],
            "type": service['type'],
            "path": service['path'],
            "auto_discovered": True
        }

    return config

def save_config(config):
    """Save discovered services configuration"""
    with open(GATEWAY_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)

    os.chmod(GATEWAY_CONFIG, 0o644)
    print(f"\n✓ Configuration saved to: {GATEWAY_CONFIG}")

def generate_gateway_update():
    """Generate Python code to add to gateway"""
    with open(GATEWAY_CONFIG, 'r') as f:
        config = json.load(f)

    code = "\n# Auto-discovered services (generated by auto-discover-services.py)\n"
    code += "# Add these to SERVICES dict in unified-gateway.py\n\n"

    for service_key, service_data in config['services'].items():
        code += f'"{service_key}": {{\n'
        code += f'    "name": "{service_data["name"]}",\n'
        code += f'    "url": "{service_data["url"]}",\n'
        code += f'    "prefix": "{service_data["prefix"]}",\n'
        code += f'    "health_endpoint": "{service_data["health_endpoint"]}",\n'
        code += f'    "description": "{service_data["description"]}"\n'
        code += '},\n'

    update_file = "/home/devinecr/apps/hubnode/api/auto_discovered_services.py"
    with open(update_file, 'w') as f:
        f.write(code)

    print(f"✓ Gateway update code saved to: {update_file}")
    return update_file

def main():
    print("="*70)
    print("HubNode Service Auto-Discovery Scanner")
    print("="*70)
    print(f"\nScanning paths:")
    for path in SCAN_PATHS:
        print(f"  - {path}")
    print()

    # Scan for services
    services = scan_for_services()

    print(f"\n{'='*70}")
    print(f"Discovery Summary: Found {len(services)} services")
    print("="*70)

    if not services:
        print("No services discovered.")
        return

    # Generate and save config
    config = generate_gateway_config(services)
    save_config(config)

    # Generate gateway update
    update_file = generate_gateway_update()

    print("\n" + "="*70)
    print("Next Steps:")
    print("="*70)
    print("1. Review discovered services:")
    print(f"   cat {GATEWAY_CONFIG}")
    print()
    print("2. Update gateway with discovered services:")
    print(f"   cat {update_file}")
    print()
    print("3. Manually add services to gateway or use auto-load:")
    print("   /home/devinecr/apps/hubnode/api/load-discovered-services.sh")
    print()
    print("4. Restart gateway:")
    print("   systemctl restart api-gateway")
    print("="*70)

if __name__ == "__main__":
    main()
