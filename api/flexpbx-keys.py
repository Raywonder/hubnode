#!/usr/bin/env python3
"""
FlexPBX API Key Management
Generates and manages API keys for FlexPBX users via HubNode gateway
"""

import sqlite3
import hashlib
import secrets
import time
from datetime import datetime, timedelta

DB_PATH = '/home/devinecr/apps/hubnode/api/flexpbx-keys.db'

def init_database():
    """Initialize API keys database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # API Keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            user_type TEXT NOT NULL,
            role TEXT NOT NULL,
            client_identifier TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            last_used DATETIME,
            is_active BOOLEAN DEFAULT 1,
            rate_limit INTEGER DEFAULT 60,
            permissions TEXT
        )
    ''')

    # API Key usage log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_key_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT NOT NULL,
            endpoint TEXT,
            method TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            response_code INTEGER
        )
    ''')

    # Revoked keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revoked_keys (
            api_key TEXT PRIMARY KEY,
            revoked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            revoked_by TEXT,
            reason TEXT
        )
    ''')

    conn.commit()
    conn.close()

def generate_api_key():
    """Generate a secure API key"""
    return 'fpbx_' + secrets.token_urlsafe(32)

def create_api_key(username, user_type='user', role='user', client_identifier=None,
                   expires_in_days=30, rate_limit=60, permissions=None):
    """
    Create a new API key for a user

    Args:
        username: Username
        user_type: Type of user (admin, user, etc.)
        role: User role (superadmin, admin, manager, user, etc.)
        client_identifier: Optional client/device identifier
        expires_in_days: Number of days until key expires (None for no expiration)
        rate_limit: Max requests per minute
        permissions: JSON string of permissions

    Returns:
        dict: API key info including the key
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    api_key = generate_api_key()
    user_id = hashlib.sha256(username.encode()).hexdigest()[:16]

    expires_at = None
    if expires_in_days:
        expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

    cursor.execute('''
        INSERT INTO api_keys
        (api_key, user_id, username, user_type, role, client_identifier,
         expires_at, rate_limit, permissions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (api_key, user_id, username, user_type, role, client_identifier,
          expires_at, rate_limit, permissions))

    conn.commit()

    # Get the created key info
    cursor.execute('SELECT * FROM api_keys WHERE api_key = ?', (api_key,))
    row = cursor.fetchone()
    conn.close()

    return {
        'api_key': api_key,
        'user_id': user_id,
        'username': username,
        'user_type': user_type,
        'role': role,
        'created_at': row[7],
        'expires_at': expires_at,
        'rate_limit': rate_limit
    }

def validate_api_key(api_key):
    """
    Validate an API key and return user info

    Returns:
        dict: User info if valid, None if invalid
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if key is revoked
    cursor.execute('SELECT * FROM revoked_keys WHERE api_key = ?', (api_key,))
    if cursor.fetchone():
        conn.close()
        return None

    # Get key info
    cursor.execute('''
        SELECT api_key, user_id, username, user_type, role, expires_at,
               is_active, rate_limit, permissions
        FROM api_keys
        WHERE api_key = ?
    ''', (api_key,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Check if active
    if not row[6]:  # is_active
        conn.close()
        return None

    # Check expiration
    if row[5]:  # expires_at
        expires_at = datetime.fromisoformat(row[5])
        if datetime.now() > expires_at:
            conn.close()
            return None

    # Update last used
    cursor.execute('''
        UPDATE api_keys
        SET last_used = CURRENT_TIMESTAMP
        WHERE api_key = ?
    ''', (api_key,))
    conn.commit()
    conn.close()

    return {
        'api_key': row[0],
        'user_id': row[1],
        'username': row[2],
        'user_type': row[3],
        'role': row[4],
        'rate_limit': row[7],
        'permissions': row[8]
    }

def revoke_api_key(api_key, revoked_by='system', reason='User requested'):
    """Revoke an API key"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO revoked_keys (api_key, revoked_by, reason)
        VALUES (?, ?, ?)
    ''', (api_key, revoked_by, reason))

    cursor.execute('''
        UPDATE api_keys
        SET is_active = 0
        WHERE api_key = ?
    ''', (api_key,))

    conn.commit()
    conn.close()

    return True

def list_user_keys(username):
    """List all API keys for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT api_key, client_identifier, created_at, expires_at,
               last_used, is_active, rate_limit
        FROM api_keys
        WHERE username = ?
        ORDER BY created_at DESC
    ''', (username,))

    keys = []
    for row in cursor.fetchall():
        keys.append({
            'api_key': row[0],
            'client_identifier': row[1],
            'created_at': row[2],
            'expires_at': row[3],
            'last_used': row[4],
            'is_active': bool(row[5]),
            'rate_limit': row[6]
        })

    conn.close()
    return keys

def log_api_usage(api_key, endpoint, method, ip_address, response_code):
    """Log API key usage"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO api_key_usage
        (api_key, endpoint, method, ip_address, response_code)
        VALUES (?, ?, ?, ?, ?)
    ''', (api_key, endpoint, method, ip_address, response_code))

    conn.commit()
    conn.close()

def check_rate_limit(api_key, window_seconds=60):
    """
    Check if API key is within rate limit

    Returns:
        tuple: (within_limit: bool, requests_count: int, limit: int)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get rate limit for this key
    cursor.execute('SELECT rate_limit FROM api_keys WHERE api_key = ?', (api_key,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, 0, 0

    rate_limit = row[0]

    # Count requests in the last window
    cutoff_time = (datetime.now() - timedelta(seconds=window_seconds)).isoformat()
    cursor.execute('''
        SELECT COUNT(*) FROM api_key_usage
        WHERE api_key = ? AND timestamp > ?
    ''', (api_key, cutoff_time))

    count = cursor.fetchone()[0]
    conn.close()

    return count < rate_limit, count, rate_limit

def cleanup_expired_keys():
    """Delete expired and inactive keys older than 90 days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Delete expired keys
    cursor.execute('''
        DELETE FROM api_keys
        WHERE expires_at IS NOT NULL
        AND datetime(expires_at) < datetime('now', '-90 days')
    ''')

    # Delete inactive keys older than 90 days
    cursor.execute('''
        DELETE FROM api_keys
        WHERE is_active = 0
        AND datetime(created_at) < datetime('now', '-90 days')
    ''')

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted

# Initialize database on import
init_database()

if __name__ == '__main__':
    # Test the system
    print("FlexPBX API Key Management System")
    print("=" * 50)

    # Create test key
    key_info = create_api_key(
        username='admin',
        user_type='admin',
        role='superadmin',
        client_identifier='test-client',
        expires_in_days=30
    )

    print(f"\nCreated API Key:")
    print(f"  Key: {key_info['api_key']}")
    print(f"  User: {key_info['username']}")
    print(f"  Role: {key_info['role']}")
    print(f"  Expires: {key_info['expires_at']}")

    # Validate key
    print(f"\nValidating key...")
    validated = validate_api_key(key_info['api_key'])
    if validated:
        print(f"  ✓ Valid key for user: {validated['username']}")

    # Check rate limit
    within_limit, count, limit = check_rate_limit(key_info['api_key'])
    print(f"\nRate Limit:")
    print(f"  Requests: {count}/{limit}")
    print(f"  Within limit: {within_limit}")

    # List user keys
    keys = list_user_keys('admin')
    print(f"\nUser 'admin' has {len(keys)} key(s)")

    print("\n" + "=" * 50)
    print("Database initialized at:", DB_PATH)
