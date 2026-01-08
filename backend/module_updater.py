#!/usr/bin/env python3
"""
CopyParty Module Updater
Automatically detects and updates existing modules/addons if they're already active
Handles WordPress, WHMCS, Composr, and other platform integrations
"""

import os
import sys
import json
import sqlite3
import subprocess
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import zipfile
import tempfile
import requests
from datetime import datetime

class ModuleUpdater:
    def __init__(self):
        self.logger = self.setup_logging()
        self.config = self.load_config()
        self.platforms = {
            'wordpress': {
                'path': '/home/tappedin/public_html/wp-content/plugins',
                'config_file': '/home/tappedin/public_html/wp-config.php',
                'active_plugins_query': self.get_wordpress_active_plugins,
                'updater': self.update_wordpress_plugin
            },
            'whmcs': {
                'path': '/home/devinecr/whmcs/modules',
                'config_file': '/home/devinecr/whmcs/configuration.php',
                'active_plugins_query': self.get_whmcs_active_modules,
                'updater': self.update_whmcs_module
            },
            'composr': {
                'path': '/home/dom/public_html/modules',
                'config_file': '/home/dom/public_html/info.php',
                'active_plugins_query': self.get_composr_active_modules,
                'updater': self.update_composr_module
            }
        }

        self.shared_sync_path = '/home/devinecr/shared'
        self.backup_path = '/home/devinecr/shared/backups/modules'
        self.modules_db = '/home/devinecr/apps/hubnode/backend/modules.db'

        # Ensure directories exist
        Path(self.backup_path).mkdir(parents=True, exist_ok=True)

        # Initialize module tracking database
        self.init_database()

    def setup_logging(self):
        """Setup logging for module updates"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/devinecr/apps/hubnode/backend/logs/module_updater.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)

    def load_config(self):
        """Load module updater configuration"""
        config_file = Path(__file__).parent / 'module_updater_config.json'

        default_config = {
            "auto_backup": True,
            "auto_update": False,
            "check_interval": 86400,  # 24 hours
            "notification_email": "admin@raywonderis.me",
            "platforms_enabled": {
                "wordpress": True,
                "whmcs": True,
                "composr": True
            },
            "modules": {
                "copyparty-manager": {
                    "version": "1.0.0",
                    "auto_update": True,
                    "platforms": ["wordpress", "whmcs", "composr"]
                }
            }
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")

        # Save default config
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def init_database(self):
        """Initialize SQLite database for module tracking"""
        conn = sqlite3.connect(self.modules_db)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                module_name TEXT NOT NULL,
                current_version TEXT NOT NULL,
                available_version TEXT,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                auto_update BOOLEAN DEFAULT 0,
                backup_path TEXT,
                UNIQUE(platform, module_name)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                module_name TEXT NOT NULL,
                old_version TEXT,
                new_version TEXT,
                update_status TEXT NOT NULL,
                error_message TEXT,
                backup_created TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def check_all_platforms(self) -> Dict[str, Dict]:
        """Check all platforms for active modules and available updates"""
        results = {}

        for platform_name, platform_config in self.platforms.items():
            if not self.config['platforms_enabled'].get(platform_name, True):
                continue

            self.logger.info(f"Checking platform: {platform_name}")

            try:
                # Check if platform exists
                if not Path(platform_config['path']).exists():
                    self.logger.warning(f"Platform path does not exist: {platform_config['path']}")
                    continue

                # Get active modules
                active_modules = platform_config['active_plugins_query']()

                # Check for updates
                platform_results = {
                    'active_modules': active_modules,
                    'updates_available': [],
                    'errors': []
                }

                for module in active_modules:
                    try:
                        update_info = self.check_module_updates(platform_name, module)
                        if update_info:
                            platform_results['updates_available'].append(update_info)
                    except Exception as e:
                        error = f"Error checking {module}: {str(e)}"
                        platform_results['errors'].append(error)
                        self.logger.error(error)

                results[platform_name] = platform_results

            except Exception as e:
                error = f"Error checking platform {platform_name}: {str(e)}"
                results[platform_name] = {'errors': [error]}
                self.logger.error(error)

        return results

    def get_wordpress_active_plugins(self) -> List[str]:
        """Get list of active WordPress plugins"""
        active_plugins = []

        try:
            # Check wp-config.php for database credentials
            config_file = '/home/tappedin/public_html/wp-config.php'
            if not Path(config_file).exists():
                return []

            # Read database config from wp-config.php
            db_config = self.parse_wordpress_config(config_file)

            # Connect to WordPress database
            import mysql.connector
            conn = mysql.connector.connect(
                host=db_config.get('DB_HOST', 'localhost'),
                user=db_config.get('DB_USER'),
                password=db_config.get('DB_PASSWORD'),
                database=db_config.get('DB_NAME')
            )

            cursor = conn.cursor()

            # Get active plugins from options table
            cursor.execute("""
                SELECT option_value FROM wp_options
                WHERE option_name = 'active_plugins'
            """)

            result = cursor.fetchone()
            if result:
                import pickle
                try:
                    # WordPress stores serialized PHP data, we'll parse it manually
                    plugins_data = result[0]
                    # Extract plugin directory names from the serialized data
                    import re
                    plugin_matches = re.findall(r'"([^"]+)/[^"]+\.php"', plugins_data)
                    active_plugins = list(set(plugin_matches))
                except:
                    # Fallback: check plugins directory for copyparty-manager
                    plugins_dir = Path('/home/tappedin/public_html/wp-content/plugins')
                    if (plugins_dir / 'copyparty-manager').exists():
                        active_plugins.append('copyparty-manager')

            conn.close()

        except Exception as e:
            self.logger.error(f"Error getting WordPress active plugins: {e}")
            # Fallback: check for our specific plugin
            plugins_dir = Path('/home/tappedin/public_html/wp-content/plugins')
            if (plugins_dir / 'copyparty-manager').exists():
                active_plugins.append('copyparty-manager')

        return active_plugins

    def parse_wordpress_config(self, config_file: str) -> Dict[str, str]:
        """Parse WordPress configuration file for database credentials"""
        config = {}

        try:
            with open(config_file, 'r') as f:
                content = f.read()

            # Extract database configuration
            import re

            patterns = {
                'DB_NAME': r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]",
                'DB_USER': r"define\s*\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]",
                'DB_PASSWORD': r"define\s*\(\s*['\"]DB_PASSWORD['\"]\s*,\s*['\"]([^'\"]+)['\"]",
                'DB_HOST': r"define\s*\(\s*['\"]DB_HOST['\"]\s*,\s*['\"]([^'\"]+)['\"]"
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    config[key] = match.group(1)

        except Exception as e:
            self.logger.error(f"Error parsing WordPress config: {e}")

        return config

    def get_whmcs_active_modules(self) -> List[str]:
        """Get list of active WHMCS modules"""
        active_modules = []

        try:
            # Check for WHMCS addon modules
            addons_path = Path('/home/devinecr/whmcs/modules/addons')
            if addons_path.exists():
                for module_dir in addons_path.iterdir():
                    if module_dir.is_dir() and 'copyparty' in module_dir.name.lower():
                        active_modules.append(module_dir.name)

            # Check for WHMCS gateway modules
            gateways_path = Path('/home/devinecr/whmcs/modules/gateways')
            if gateways_path.exists():
                for module_file in gateways_path.glob('*copyparty*.php'):
                    active_modules.append(module_file.stem)

        except Exception as e:
            self.logger.error(f"Error getting WHMCS active modules: {e}")

        return active_modules

    def get_composr_active_modules(self) -> List[str]:
        """Get list of active Composr modules"""
        active_modules = []

        try:
            # Check Composr modules directory
            modules_path = Path('/home/dom/public_html/modules')
            if modules_path.exists():
                for module_dir in modules_path.iterdir():
                    if module_dir.is_dir() and 'copyparty' in module_dir.name.lower():
                        active_modules.append(module_dir.name)

        except Exception as e:
            self.logger.error(f"Error getting Composr active modules: {e}")

        return active_modules

    def check_module_updates(self, platform: str, module_name: str) -> Optional[Dict]:
        """Check if a module has updates available"""
        try:
            # Get current version
            current_version = self.get_module_version(platform, module_name)

            # Get available version from shared sync
            available_version = self.get_available_version(platform, module_name)

            if current_version and available_version:
                if self.compare_versions(available_version, current_version) > 0:
                    return {
                        'module': module_name,
                        'current_version': current_version,
                        'available_version': available_version,
                        'platform': platform,
                        'auto_update': self.should_auto_update(platform, module_name)
                    }

            # Update database with check
            self.update_module_check(platform, module_name, current_version, available_version)

        except Exception as e:
            self.logger.error(f"Error checking updates for {platform}/{module_name}: {e}")

        return None

    def get_module_version(self, platform: str, module_name: str) -> Optional[str]:
        """Get current version of installed module"""
        try:
            if platform == 'wordpress':
                return self.get_wordpress_plugin_version(module_name)
            elif platform == 'whmcs':
                return self.get_whmcs_module_version(module_name)
            elif platform == 'composr':
                return self.get_composr_module_version(module_name)

        except Exception as e:
            self.logger.error(f"Error getting version for {platform}/{module_name}: {e}")

        return None

    def get_wordpress_plugin_version(self, plugin_name: str) -> Optional[str]:
        """Get WordPress plugin version from plugin file"""
        try:
            plugin_file = Path(f'/home/tappedin/public_html/wp-content/plugins/{plugin_name}/{plugin_name}.php')
            if plugin_file.exists():
                with open(plugin_file, 'r') as f:
                    content = f.read()

                # Look for version in plugin header
                import re
                match = re.search(r'Version:\s*([0-9.]+)', content)
                if match:
                    return match.group(1)

        except Exception as e:
            self.logger.error(f"Error getting WordPress plugin version for {plugin_name}: {e}")

        return None

    def get_whmcs_module_version(self, module_name: str) -> Optional[str]:
        """Get WHMCS module version"""
        try:
            # Check addon modules
            module_file = Path(f'/home/devinecr/whmcs/modules/addons/{module_name}.php')
            if not module_file.exists():
                module_file = Path(f'/home/devinecr/whmcs/modules/addons/{module_name}/{module_name}.php')

            if module_file.exists():
                with open(module_file, 'r') as f:
                    content = f.read()

                # Look for version in module config
                import re
                match = re.search(r'["\']version["\']\s*=>\s*["\']([0-9.]+)["\']', content)
                if match:
                    return match.group(1)

        except Exception as e:
            self.logger.error(f"Error getting WHMCS module version for {module_name}: {e}")

        return None

    def get_composr_module_version(self, module_name: str) -> Optional[str]:
        """Get Composr module version"""
        try:
            module_info = Path(f'/home/dom/public_html/modules/{module_name}/module.xml')
            if module_info.exists():
                import xml.etree.ElementTree as ET
                tree = ET.parse(module_info)
                root = tree.getroot()

                version_elem = root.find('.//version')
                if version_elem is not None:
                    return version_elem.text

        except Exception as e:
            self.logger.error(f"Error getting Composr module version for {module_name}: {e}")

        return None

    def get_available_version(self, platform: str, module_name: str) -> Optional[str]:
        """Get available version from shared sync directory"""
        try:
            version_file = Path(f'{self.shared_sync_path}/platforms/{platform}/modules/{module_name}/version.json')
            if version_file.exists():
                with open(version_file, 'r') as f:
                    version_info = json.load(f)
                    return version_info.get('version')

        except Exception as e:
            self.logger.error(f"Error getting available version for {platform}/{module_name}: {e}")

        return None

    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns 1 if version1 > version2, -1 if version1 < version2, 0 if equal"""
        try:
            from packaging import version
            v1 = version.parse(version1)
            v2 = version.parse(version2)

            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
            else:
                return 0

        except ImportError:
            # Fallback simple comparison
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]

            # Pad with zeros to same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1

            return 0

    def should_auto_update(self, platform: str, module_name: str) -> bool:
        """Check if module should be auto-updated"""
        return (
            self.config.get('auto_update', False) and
            self.config.get('modules', {}).get(module_name, {}).get('auto_update', False) and
            self.config.get('platforms_enabled', {}).get(platform, True)
        )

    def update_module_check(self, platform: str, module_name: str, current_version: str, available_version: str):
        """Update module check information in database"""
        conn = sqlite3.connect(self.modules_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO module_versions
            (platform, module_name, current_version, available_version, last_checked, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (platform, module_name, current_version, available_version, datetime.now()))

        conn.commit()
        conn.close()

    def perform_updates(self, updates_to_apply: List[Dict]) -> Dict[str, Dict]:
        """Perform module updates"""
        results = {}

        for update in updates_to_apply:
            platform = update['platform']
            module_name = update['module']

            self.logger.info(f"Updating {platform}/{module_name} from {update['current_version']} to {update['available_version']}")

            try:
                # Create backup if enabled
                backup_path = None
                if self.config.get('auto_backup', True):
                    backup_path = self.create_module_backup(platform, module_name)

                # Perform the update
                update_result = self.platforms[platform]['updater'](module_name, update['available_version'])

                if update_result['success']:
                    # Record successful update
                    self.record_update_history(
                        platform, module_name,
                        update['current_version'], update['available_version'],
                        'success', None, backup_path
                    )

                    results[f"{platform}/{module_name}"] = {
                        'success': True,
                        'old_version': update['current_version'],
                        'new_version': update['available_version'],
                        'backup_path': backup_path
                    }
                else:
                    # Record failed update
                    error_msg = update_result.get('error', 'Unknown error')
                    self.record_update_history(
                        platform, module_name,
                        update['current_version'], update['available_version'],
                        'failed', error_msg, backup_path
                    )

                    results[f"{platform}/{module_name}"] = {
                        'success': False,
                        'error': error_msg,
                        'backup_path': backup_path
                    }

            except Exception as e:
                error_msg = f"Update failed: {str(e)}"
                self.logger.error(f"Error updating {platform}/{module_name}: {e}")

                results[f"{platform}/{module_name}"] = {
                    'success': False,
                    'error': error_msg
                }

        return results

    def create_module_backup(self, platform: str, module_name: str) -> str:
        """Create backup of current module before update"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{platform}_{module_name}_{timestamp}"
        backup_dir = Path(self.backup_path) / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Get source path
        if platform == 'wordpress':
            source_path = Path(f'/home/tappedin/public_html/wp-content/plugins/{module_name}')
        elif platform == 'whmcs':
            source_path = Path(f'/home/devinecr/whmcs/modules/addons/{module_name}')
        elif platform == 'composr':
            source_path = Path(f'/home/dom/public_html/modules/{module_name}')
        else:
            raise ValueError(f"Unknown platform: {platform}")

        if source_path.exists():
            if source_path.is_dir():
                shutil.copytree(source_path, backup_dir / module_name)
            else:
                shutil.copy2(source_path, backup_dir)

        self.logger.info(f"Created backup: {backup_dir}")
        return str(backup_dir)

    def update_wordpress_plugin(self, plugin_name: str, new_version: str) -> Dict:
        """Update WordPress plugin"""
        try:
            source_path = Path(f'{self.shared_sync_path}/platforms/wordpress/modules/{plugin_name}')
            target_path = Path(f'/home/tappedin/public_html/wp-content/plugins/{plugin_name}')

            if not source_path.exists():
                return {'success': False, 'error': 'Source module not found'}

            # Remove existing plugin
            if target_path.exists():
                shutil.rmtree(target_path)

            # Copy new version
            shutil.copytree(source_path, target_path)

            # Set proper permissions
            subprocess.run(['chmod', '-R', '755', str(target_path)], check=True)
            subprocess.run(['chown', '-R', 'tappedin:tappedin', str(target_path)], check=True)

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_whmcs_module(self, module_name: str, new_version: str) -> Dict:
        """Update WHMCS module"""
        try:
            source_path = Path(f'{self.shared_sync_path}/platforms/whmcs/modules/{module_name}')
            target_path = Path(f'/home/devinecr/whmcs/modules/addons/{module_name}')

            if not source_path.exists():
                return {'success': False, 'error': 'Source module not found'}

            # Remove existing module
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

            # Copy new version
            if source_path.is_dir():
                shutil.copytree(source_path, target_path)
            else:
                shutil.copy2(source_path, target_path)

            # Set proper permissions
            subprocess.run(['chmod', '-R', '755', str(target_path)], check=True)
            subprocess.run(['chown', '-R', 'devinecr:devinecr', str(target_path)], check=True)

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_composr_module(self, module_name: str, new_version: str) -> Dict:
        """Update Composr module"""
        try:
            source_path = Path(f'{self.shared_sync_path}/platforms/composr/modules/{module_name}')
            target_path = Path(f'/home/dom/public_html/modules/{module_name}')

            if not source_path.exists():
                return {'success': False, 'error': 'Source module not found'}

            # Remove existing module
            if target_path.exists():
                shutil.rmtree(target_path)

            # Copy new version
            shutil.copytree(source_path, target_path)

            # Set proper permissions
            subprocess.run(['chmod', '-R', '755', str(target_path)], check=True)
            subprocess.run(['chown', '-R', 'dom:dom', str(target_path)], check=True)

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def record_update_history(self, platform: str, module_name: str, old_version: str,
                            new_version: str, status: str, error_message: str = None,
                            backup_path: str = None):
        """Record update history in database"""
        conn = sqlite3.connect(self.modules_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO update_history
            (platform, module_name, old_version, new_version, update_status, error_message, backup_created)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (platform, module_name, old_version, new_version, status, error_message, backup_path))

        conn.commit()
        conn.close()

    def sync_modules_to_shared(self):
        """Sync updated modules to shared directory for platform sync"""
        try:
            # WordPress modules
            wp_plugins_source = Path('/home/tappedin/public_html/wp-content/plugins')
            wp_plugins_target = Path(f'{self.shared_sync_path}/platforms/wordpress/modules')

            if wp_plugins_source.exists():
                wp_plugins_target.mkdir(parents=True, exist_ok=True)

                for plugin_dir in wp_plugins_source.iterdir():
                    if plugin_dir.is_dir() and 'copyparty' in plugin_dir.name.lower():
                        target_plugin = wp_plugins_target / plugin_dir.name
                        if target_plugin.exists():
                            shutil.rmtree(target_plugin)
                        shutil.copytree(plugin_dir, target_plugin)

                        # Create version info
                        version = self.get_wordpress_plugin_version(plugin_dir.name)
                        if version:
                            version_info = {
                                'version': version,
                                'platform': 'wordpress',
                                'updated': datetime.now().isoformat()
                            }
                            with open(target_plugin / 'version.json', 'w') as f:
                                json.dump(version_info, f, indent=2)

            # WHMCS modules
            whmcs_modules_source = Path('/home/devinecr/whmcs/modules/addons')
            whmcs_modules_target = Path(f'{self.shared_sync_path}/platforms/whmcs/modules')

            if whmcs_modules_source.exists():
                whmcs_modules_target.mkdir(parents=True, exist_ok=True)

                for module_item in whmcs_modules_source.iterdir():
                    if 'copyparty' in module_item.name.lower():
                        target_module = whmcs_modules_target / module_item.name
                        if target_module.exists():
                            if target_module.is_dir():
                                shutil.rmtree(target_module)
                            else:
                                target_module.unlink()

                        if module_item.is_dir():
                            shutil.copytree(module_item, target_module)
                        else:
                            shutil.copy2(module_item, target_module)

                        # Create version info
                        version = self.get_whmcs_module_version(module_item.name)
                        if version:
                            version_info = {
                                'version': version,
                                'platform': 'whmcs',
                                'updated': datetime.now().isoformat()
                            }
                            version_file = target_module / 'version.json' if target_module.is_dir() else target_module.parent / f'{module_item.stem}_version.json'
                            with open(version_file, 'w') as f:
                                json.dump(version_info, f, indent=2)

            # Composr modules
            composr_modules_source = Path('/home/dom/public_html/modules')
            composr_modules_target = Path(f'{self.shared_sync_path}/platforms/composr/modules')

            if composr_modules_source.exists():
                composr_modules_target.mkdir(parents=True, exist_ok=True)

                for module_dir in composr_modules_source.iterdir():
                    if module_dir.is_dir() and 'copyparty' in module_dir.name.lower():
                        target_module = composr_modules_target / module_dir.name
                        if target_module.exists():
                            shutil.rmtree(target_module)
                        shutil.copytree(module_dir, target_module)

                        # Create version info
                        version = self.get_composr_module_version(module_dir.name)
                        if version:
                            version_info = {
                                'version': version,
                                'platform': 'composr',
                                'updated': datetime.now().isoformat()
                            }
                            with open(target_module / 'version.json', 'w') as f:
                                json.dump(version_info, f, indent=2)

            self.logger.info("Modules synced to shared directory")

        except Exception as e:
            self.logger.error(f"Error syncing modules to shared: {e}")

    def generate_update_report(self) -> Dict:
        """Generate comprehensive update report"""
        conn = sqlite3.connect(self.modules_db)
        cursor = conn.cursor()

        # Get current module status
        cursor.execute('''
            SELECT platform, module_name, current_version, available_version,
                   is_active, last_checked, last_updated
            FROM module_versions
            ORDER BY platform, module_name
        ''')

        current_modules = cursor.fetchall()

        # Get recent update history
        cursor.execute('''
            SELECT platform, module_name, old_version, new_version,
                   update_status, error_message, updated_at
            FROM update_history
            WHERE updated_at > datetime('now', '-7 days')
            ORDER BY updated_at DESC
        ''')

        recent_updates = cursor.fetchall()

        conn.close()

        return {
            'current_modules': [
                {
                    'platform': row[0],
                    'module': row[1],
                    'current_version': row[2],
                    'available_version': row[3],
                    'is_active': bool(row[4]),
                    'last_checked': row[5],
                    'last_updated': row[6]
                }
                for row in current_modules
            ],
            'recent_updates': [
                {
                    'platform': row[0],
                    'module': row[1],
                    'old_version': row[2],
                    'new_version': row[3],
                    'status': row[4],
                    'error': row[5],
                    'updated_at': row[6]
                }
                for row in recent_updates
            ],
            'generated_at': datetime.now().isoformat()
        }

    def run_update_check(self):
        """Run complete update check and apply auto-updates"""
        self.logger.info("Starting module update check")

        try:
            # Check all platforms
            check_results = self.check_all_platforms()

            # Collect auto-updates
            auto_updates = []
            for platform, results in check_results.items():
                for update in results.get('updates_available', []):
                    if update.get('auto_update', False):
                        auto_updates.append(update)

            # Apply auto-updates
            if auto_updates:
                self.logger.info(f"Applying {len(auto_updates)} auto-updates")
                update_results = self.perform_updates(auto_updates)

                # Sync updated modules to shared directory
                self.sync_modules_to_shared()

                return {
                    'check_results': check_results,
                    'auto_updates_applied': update_results,
                    'success': True
                }
            else:
                self.logger.info("No auto-updates to apply")
                return {
                    'check_results': check_results,
                    'auto_updates_applied': {},
                    'success': True
                }

        except Exception as e:
            self.logger.error(f"Error during update check: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main function for command line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='CopyParty Module Updater')
    parser.add_argument('action', choices=['check', 'update', 'sync', 'report'],
                       help='Action to perform')
    parser.add_argument('--platform', help='Specific platform to check/update')
    parser.add_argument('--module', help='Specific module to check/update')
    parser.add_argument('--auto-update', action='store_true',
                       help='Enable auto-updates for this run')

    args = parser.parse_args()

    updater = ModuleUpdater()

    if args.action == 'check':
        results = updater.check_all_platforms()
        print(json.dumps(results, indent=2))

    elif args.action == 'update':
        if args.auto_update:
            updater.config['auto_update'] = True
        results = updater.run_update_check()
        print(json.dumps(results, indent=2))

    elif args.action == 'sync':
        updater.sync_modules_to_shared()
        print("Modules synced to shared directory")

    elif args.action == 'report':
        report = updater.generate_update_report()
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()