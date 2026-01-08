# HubNode API Services Registry
**Updated**: October 10, 2025
**API Gateway Version**: 1.0.0
**Location**: `/home/devinecr/apps/hubnode/api/unified-gateway.py`

---

## API Endpoints

All services are accessible via three domain aliases:
- **https://api.tappedin.fm**
- **https://api.devine-creations.com**
- **https://api.devinecreations.net** (currently offline)

**Gateway Port**: 5015
**Server IP**: 64.20.46.178

---

## Registered Services

### 1. Service Monitor
- **Prefix**: `/monitor`
- **URL**: http://localhost:5003
- **Health**: `/health`
- **Description**: System service monitoring
- **Admin Only**: No
- **Status**: ✅ Active

**Example**:
```bash
curl https://api.tappedin.fm/monitor/health
```

---

### 2. User Logs Collector
- **Prefix**: `/logs`
- **URL**: http://localhost:5002
- **Health**: `/health`
- **Description**: App logs and analytics
- **Admin Only**: No
- **Status**: ✅ Active

**Example**:
```bash
curl -H "X-API-Key: your-api-key" https://api.tappedin.fm/logs/health
```

---

### 3. Audio Portrait API
- **Prefix**: `/audio-portrait`
- **URL**: http://localhost:5001
- **Health**: `/api/audio-portrait/health`
- **Description**: Audio Portrait app services
- **Admin Only**: No
- **Status**: ✅ Active

**Example**:
```bash
curl https://api.tappedin.fm/audio-portrait/api/audio-portrait/health
```

---

### 4. CopyParty Management API
- **Prefix**: `/copyparty`
- **URL**: http://localhost:5016
- **Health**: `/api/copyparty/health`
- **Description**: CopyParty file server management with admin controls
- **Admin Only**: No
- **Status**: ✅ Active

**Example**:
```bash
curl https://api.tappedin.fm/copyparty/api/copyparty/health
```

---

### 5. Services Manager
- **Prefix**: `/services`
- **URL**: http://localhost:5017
- **Health**: `/api/services/health`
- **Description**: Docker, Jellyfin, Icecast, TeamTalk, and system services management
- **Admin Only**: No
- **Status**: ✅ Active

**Example**:
```bash
curl https://api.tappedin.fm/services/api/services/health
```

---

### 6. Webhook Manager
- **Prefix**: `/webhooks`
- **URL**: http://localhost:5004
- **Health**: `/health`
- **Description**: External webhook integrations
- **Admin Only**: Yes
- **Status**: ✅ Active

**Example**:
```bash
curl -H "X-API-Key: master-key" https://api.tappedin.fm/webhooks/health
```

---

### 7. Mastodon Social Network (NEW) ✨
- **Prefix**: `/mastodon`
- **URL**: http://localhost:3001
- **Health**: `/health`
- **Description**: Mastodon federated social network instance (md.tappedin.fm)
- **Admin Only**: No
- **Status**: ✅ Active
- **Web Interface**: https://md.tappedin.fm

**API Examples**:
```bash
# Public timeline
curl https://api.tappedin.fm/mastodon/api/v1/timelines/public

# Instance info
curl https://api.tappedin.fm/mastodon/api/v1/instance

# Health check
curl https://api.tappedin.fm/mastodon/health
```

---

### 8. Mattermost Team Chat (NEW) ✨
- **Prefix**: `/mattermost`
- **URL**: http://localhost:8065
- **Health**: `/api/v4/system/ping`
- **Description**: Mattermost team collaboration platform (chat.tappedin.fm)
- **Admin Only**: No
- **Status**: ✅ Active
- **Web Interface**: https://chat.tappedin.fm

**API Examples**:
```bash
# System ping
curl https://api.tappedin.fm/mattermost/api/v4/system/ping

# Get user (requires auth)
curl -H "Authorization: Bearer TOKEN" https://api.tappedin.fm/mattermost/api/v4/users/me
```

---

### 9. Mastodon Bridge Bot (NEW) ✨
- **Prefix**: `/mastodon-bridge`
- **URL**: http://localhost:5018
- **Health**: `/health`
- **Description**: Mastodon to Discord/Mattermost announcement bridge bot
- **Admin Only**: No
- **Status**: ⏸️ Pending API Implementation
- **Service Location**: `/home/tappedin/apps/mastodon-integrations/`

**Note**: Bridge bot currently runs as systemd service without HTTP API. Future implementation will add REST API for status and control.

---

## Authentication

### API Key Authentication

**Header**:
```http
X-API-Key: your-api-key
```

**Query Parameter**:
```
?api_key=your-api-key
```

### API Key Management

API keys are stored in:
- **File**: `/home/devinecr/apps/hubnode/api/api_keys.json`
- **Database**: `/home/devinecr/apps/hubnode/api/gateway.db`

---

## Gateway Endpoints

### Root (/)
```bash
curl https://api.tappedin.fm/
```

Returns gateway documentation and service list.

### Health Check (/health)
```bash
curl https://api.tappedin.fm/health
```

Returns gateway health status.

### Services List (/services)
```bash
curl -H "X-API-Key: your-key" https://api.tappedin.fm/services
```

Returns all registered services and their health status.

### Statistics (/stats)
```bash
curl -H "X-API-Key: your-key" https://api.tappedin.fm/stats
```

Returns gateway usage statistics.

---

## Service Registration Guide

### Adding a New Service

1. **Edit Gateway Configuration**:
   ```bash
   nano /home/devinecr/apps/hubnode/api/unified-gateway.py
   ```

2. **Add Service to SERVICES Dictionary**:
   ```python
   "service-name": {
       "name": "Service Display Name",
       "url": "http://localhost:PORT",
       "prefix": "/service-name",
       "health_endpoint": "/health",
       "description": "Service description",
       "admin_only": False
   }
   ```

3. **Restart Gateway**:
   ```bash
   systemctl restart api-gateway
   ```

4. **Verify Registration**:
   ```bash
   curl https://api.tappedin.fm/ | grep "service-name"
   ```

---

## Service Health Monitoring

All registered services are periodically health-checked by the gateway.

**Health Status Codes**:
- ✅ **healthy** - Service responding normally
- ⚠️ **degraded** - Service responding slowly
- ❌ **unhealthy** - Service not responding
- ⏸️ **unknown** - No health endpoint available

---

## Testing All Services

```bash
#!/bin/bash
# Test all API services

echo "Testing API Gateway Services..."
echo ""

services=("monitor" "logs" "audio-portrait" "copyparty" "services" "webhooks" "mastodon" "mattermost" "mastodon-bridge")

for service in "${services[@]}"; do
    echo "Testing: $service"
    response=$(curl -s -o /dev/null -w "%{http_code}" https://api.tappedin.fm/$service/health 2>&1)

    if [ "$response" == "200" ]; then
        echo "  ✅ $service: OK ($response)"
    else
        echo "  ⚠️ $service: $response"
    fi
    echo ""
done
```

---

## Port Assignments

| Service | Port | Protocol | Status |
|---------|------|----------|--------|
| Audio Portrait API | 5001 | HTTP | Active |
| User Logs | 5002 | HTTP | Active |
| Service Monitor | 5003 | HTTP | Active |
| Webhook Manager | 5004 | HTTP | Active |
| API Gateway | 5015 | HTTP | Active |
| CopyParty Admin | 5016 | HTTP | Active |
| Services Manager | 5017 | HTTP | Active |
| Mastodon Bridge | 5018 | HTTP | Pending |
| Mastodon Web | 3001 | HTTP | Active |
| Mattermost | 8065 | HTTP | Active |

---

## Nginx Reverse Proxy Configuration

All services are accessible through nginx reverse proxy:

```nginx
# /etc/nginx/conf.d/api-gateway.conf

server {
    listen 443 ssl http2;
    server_name api.tappedin.fm api.devine-creations.com api.devinecreations.net;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5015;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Database Schema

### API Keys Table
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    key_name TEXT NOT NULL,
    app_name TEXT,
    permissions TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME,
    active BOOLEAN DEFAULT 1
);
```

### Request Logs Table
```sql
CREATE TABLE request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    api_key_id INTEGER,
    service TEXT,
    endpoint TEXT,
    method TEXT,
    ip_address TEXT,
    user_agent TEXT,
    status_code INTEGER,
    response_time REAL
);
```

### Service Health Table
```sql
CREATE TABLE service_health (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    service_name TEXT,
    status TEXT,
    response_time REAL,
    error_message TEXT
);
```

---

## Troubleshooting

### Service Not Responding

1. **Check if service is running**:
   ```bash
   systemctl status [service-name]
   ```

2. **Check service port**:
   ```bash
   ss -tlnp | grep [PORT]
   ```

3. **Check gateway logs**:
   ```bash
   tail -f /var/log/api-gateway.log
   ```

4. **Restart gateway**:
   ```bash
   systemctl restart api-gateway
   ```

### API Key Issues

1. **Check API keys file**:
   ```bash
   cat /home/devinecr/apps/hubnode/api/api_keys.json
   ```

2. **Query database**:
   ```bash
   sqlite3 /home/devinecr/apps/hubnode/api/gateway.db "SELECT * FROM api_keys;"
   ```

---

## Related Documentation

- **API Gateway**: `/home/devinecr/apps/hubnode/api/API_DOCUMENTATION.md`
- **Mastodon**: `/home/tappedin/apps/mastodon-integrations/README.md`
- **Mattermost**: `/home/tappedin/apps/mattermost/MATTERMOST_ADMIN_CREDENTIALS.md`
- **Service Manager**: `/home/devinecr/apps/hubnode/api/services-manager.py`

---

## Service URLs Summary

### Production URLs
- **Mastodon**: https://md.tappedin.fm
- **Mattermost**: https://chat.tappedin.fm
- **API Gateway**: https://api.tappedin.fm
- **CopyParty**: https://files.devinecreations.net

### API Access
- **Mastodon API**: https://api.tappedin.fm/mastodon/api/v1/*
- **Mattermost API**: https://api.tappedin.fm/mattermost/api/v4/*
- **Services API**: https://api.tappedin.fm/services/api/services/*

---

## Changelog

### October 10, 2025
- ✅ Added Mastodon Social Network service
- ✅ Added Mattermost Team Chat service
- ✅ Added Mastodon Bridge Bot placeholder
- ✅ Updated service registry with 9 total services
- ✅ Verified all API endpoints
- ✅ Created comprehensive documentation

---

**Last Updated**: October 10, 2025 - 19:15 UTC
**Gateway Status**: ✅ Active
**Total Services**: 9 (7 active, 1 pending API, 1 admin-only)
