#!/usr/bin/env python3
"""
Dynamic Gateway Service Loader
Loads services from service-registry.json at runtime
"""

import json
import os

def load_service_registry():
    """Load services from registry file"""
    registry_file = "/home/devinecr/apps/hubnode/api/service-registry.json"

    if not os.path.exists(registry_file):
        return {}

    with open(registry_file, 'r') as f:
        registry = json.load(f)

    # Flatten all services into single dict
    all_services = {}

    # Load core services
    if 'core' in registry.get('services', {}):
        for key, service in registry['services']['core'].items():
            if service.get('enabled', True):
                all_services[key] = {
                    "name": service['name'],
                    "url": service['url'],
                    "prefix": service['prefix'],
                    "health_endpoint": service['health_endpoint'],
                    "description": service['description']
                }

    # Load user apps
    if 'user_apps' in registry.get('services', {}):
        for key, service in registry['services']['user_apps'].items():
            if service.get('enabled', True):
                all_services[key] = {
                    "name": service['name'],
                    "url": service['url'],
                    "prefix": service['prefix'],
                    "health_endpoint": service['health_endpoint'],
                    "description": service['description']
                }

    # Load discovered services
    if 'discovered' in registry.get('services', {}):
        for key, service in registry['services']['discovered'].items():
            if key == 'note' or key == 'scan_paths':
                continue
            if service.get('enabled', True):
                all_services[key] = {
                    "name": service['name'],
                    "url": service['url'],
                    "prefix": service['prefix'],
                    "health_endpoint": service['health_endpoint'],
                    "description": service['description']
                }

    return all_services

def update_registry_with_discovered(discovered_services):
    """Update registry with newly discovered services"""
    registry_file = "/home/devinecr/apps/hubnode/api/service-registry.json"

    with open(registry_file, 'r') as f:
        registry = json.load(f)

    # Add discovered services
    if 'discovered' not in registry['services']:
        registry['services']['discovered'] = {}

    for service_key, service_data in discovered_services.items():
        # Skip if already exists
        if service_key in registry['services']['discovered']:
            continue

        registry['services']['discovered'][service_key] = {
            "name": service_data['name'],
            "url": service_data['url'],
            "port": service_data.get('port'),
            "prefix": service_data['prefix'],
            "health_endpoint": service_data['health_endpoint'],
            "description": service_data['description'],
            "user": service_data.get('user', 'unknown'),
            "path": service_data.get('path'),
            "type": service_data.get('type'),
            "enabled": True,
            "auto_start": False,
            "auto_discovered": True
        }

    # Update last scan time
    from datetime import datetime
    registry['discovery']['last_scan'] = datetime.now().isoformat()

    # Save updated registry
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)

    print(f"✓ Registry updated with {len(discovered_services)} services")

if __name__ == "__main__":
    services = load_service_registry()
    print(f"Loaded {len(services)} services from registry:")
    for key, service in services.items():
        print(f"  - {service['name']} ({key}) -> {service['prefix']}")
