# HubNode API Documentation

Complete API documentation for all Devine Creations services management APIs.

## Overview

The HubNode API ecosystem consists of three main components:

1. **Unified API Gateway** (Port 5015) - Central routing and authentication
2. **CopyParty Admin API** (Port 5016) - File management and CopyParty control
3. **Services Manager API** (Port 5017) - Docker, Jellyfin, Icecast, TeamTalk, and system services

## Access URLs

- **Primary Gateway**: `https://api.devine-creations.com`
- **Alternate Gateway**: `https://api.devinecreations.net`
- **Direct IP Access**: `http://64.20.46.178:5015`

## Authentication

### Role-Based Access

**Admin Users** (Full Access):
- `devinecr`
- `dom`
- `tappedin`
- `admin`

**General Users** (Read-only + Personal Services):
- `tetoeehoward`
- `wharper`
- `flexpbx`

### Authentication Methods

#### Method 1: HTTP Header
```http
X-User: your-username
```

#### Method 2: Query Parameter
```http
?user=your-username
```

#### Method 3: API Keys (for Gateway)
```http
X-API-Key: your-api-key
```

---

## 1. Unified API Gateway

**Base URL**: `http://64.20.46.178:5015`

### Gateway Endpoints

#### GET /
Get gateway information and available services

**Response**:
```json
{
  "name": "HubNode Unified API Gateway",
  "version": "1.0.0",
  "services": {
    "monitor": {...},
    "logs": {...},
    "copyparty": {...},
    "services": {...}
  }
}
```

#### GET /health
Check gateway health

**Response**:
```json
{
  "status": "healthy",
  "gateway": "online",
  "timestamp": "2025-10-03T08:39:36.000Z"
}
```

#### GET /services
List all backend services and their health (requires API key)

**Response**:
```json
{
  "timestamp": "2025-10-03T08:39:36.000Z",
  "services": {
    "monitor": {
      "name": "Service Monitor",
      "health": {
        "status": "healthy",
        "response_time": 0.023
      }
    }
  }
}
```

#### GET /keys
List all API keys (requires master key)

#### GET /stats
Get gateway statistics (requires API key)

**Response**:
```json
{
  "timestamp": "2025-10-03T08:39:36.000Z",
  "service_stats": [
    {
      "service": "copyparty",
      "requests": 142,
      "avg_response_time": 0.034
    }
  ],
  "recent_errors": []
}
```

---

## 2. CopyParty Admin API

**Base URL**: `http://64.20.46.178:5016/api/copyparty`

### File Management

#### GET /files/list
List files in a directory

**Parameters**:
- `path` (string): Directory path (default: `/`)
- `format` (string): json|text|verbose (default: `json`)

**Example**:
```bash
curl "http://64.20.46.178:5016/api/copyparty/files/list?path=/shared&format=json" \
  -H "X-User: devinecr"
```

**Response**:
```json
{
  "files": [
    {"name": "file1.txt", "size": 1024, "modified": "2025-10-03T08:00:00Z"},
    {"name": "folder1", "type": "directory"}
  ]
}
```

#### GET /files/tree
List directory tree recursively

**Parameters**:
- `path` (string): Root path (default: `/`)

#### GET /files/download
Download a file

**Parameters**:
- `path` (string, required): File path

**Example**:
```bash
curl "http://64.20.46.178:5016/api/copyparty/files/download?path=/shared/file.txt" \
  -H "X-User: devinecr" \
  -O
```

#### POST /files/upload
Upload a file

**Form Data**:
- `file`: File to upload
- `path`: Destination path (default: `/`)
- `overwrite`: true|false (default: `false`)

**Example**:
```bash
curl -X POST "http://64.20.46.178:5016/api/copyparty/files/upload" \
  -H "X-User: devinecr" \
  -F "file=@/path/to/local/file.txt" \
  -F "path=/shared/"
```

**Response**:
```json
{
  "status": "success",
  "path": "/shared/file.txt",
  "message": "Upload successful"
}
```

#### POST /files/delete
Delete file or directory

**JSON Body**:
```json
{
  "path": "/shared/file.txt"
}
```

**Example**:
```bash
curl -X POST "http://64.20.46.178:5016/api/copyparty/files/delete" \
  -H "X-User: devinecr" \
  -H "Content-Type: application/json" \
  -d '{"path": "/shared/file.txt"}'
```

#### POST /files/move
Move/rename file or directory

**JSON Body**:
```json
{
  "source": "/shared/old.txt",
  "destination": "/shared/new.txt"
}
```

#### POST /files/copy
Copy file or directory

**JSON Body**:
```json
{
  "source": "/shared/file.txt",
  "destination": "/backup/file.txt"
}
```

#### POST /files/mkdir
Create directory

**JSON Body**:
```json
{
  "path": "/shared/new-folder"
}
```

### Search

#### GET /search/recent
Get recent uploads

**Parameters**:
- `path` (string): Root path (default: `/`)

#### POST /search
Search for files

**JSON Body**:
```json
{
  "query": "*.pdf",
  "path": "/shared"
}
```

### Admin Operations (Admin Only)

#### POST /admin/reload
Reload CopyParty configuration

**Example**:
```bash
curl -X POST "http://64.20.46.178:5016/api/copyparty/admin/reload" \
  -H "X-User: devinecr"
```

#### POST /admin/scan
Rescan all volumes

#### GET /admin/stats
Get CopyParty statistics (Prometheus/OpenMetrics format)

### Management

#### GET /users/list
List all configured users

**Response**:
```json
{
  "users": [
    {
      "username": "admin",
      "permissions": "rwm",
      "groups": ["all"]
    }
  ]
}
```

#### GET /volumes/list
List all configured volumes

**Response**:
```json
{
  "volumes": [
    {
      "name": "dom-home",
      "path": "/home/dom",
      "permissions": "rwm",
      "users": ["dom", "admin"]
    }
  ]
}
```

#### GET /health
Check CopyParty health

#### GET /info
Get API information

---

## 3. Services Manager API

**Base URL**: `http://64.20.46.178:5017/api/services`

### Docker Management

#### GET /docker/containers/list
List all Docker containers

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/docker/containers/list" \
  -H "X-User: devinecr"
```

**Response**:
```json
{
  "containers": [
    {
      "Names": "mattermost-mattermost-1",
      "State": "running",
      "Image": "mattermost/mattermost:latest",
      "Status": "Up 2 days"
    }
  ]
}
```

#### POST /docker/containers/<name>/start
Start a Docker container (admin only)

**Example**:
```bash
curl -X POST "http://64.20.46.178:5017/api/services/docker/containers/portainer/start" \
  -H "X-User: devinecr"
```

#### POST /docker/containers/<name>/stop
Stop a Docker container (admin only)

#### POST /docker/containers/<name>/restart
Restart a Docker container (admin only)

#### GET /docker/containers/<name>/logs
Get container logs

**Parameters**:
- `lines` (number): Number of log lines (default: 100)

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/docker/containers/portainer/logs?lines=50" \
  -H "X-User: devinecr"
```

#### GET /docker/containers/<name>/stats
Get container resource statistics

#### POST /docker/system/prune
Clean up Docker system (admin only)

**Parameters**:
- `force` (boolean): Force cleanup (default: false)

### Jellyfin Management

#### GET /jellyfin/status
Get Jellyfin server status

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/jellyfin/status" \
  -H "X-User: devinecr"
```

**Response**:
```json
{
  "service": "jellyfin",
  "running": true,
  "process_info": "dom 2636 /home/dom/apps/jellyfin/jellyfin/jellyfin",
  "system_info": {
    "ServerName": "Jellyfin",
    "Version": "10.8.0"
  }
}
```

#### POST /jellyfin/restart
Restart Jellyfin server (admin only)

### Icecast Management

#### GET /icecast/list
List all Icecast instances

**Response**:
```json
{
  "instances": [
    {
      "user": "dom",
      "pid": "2434",
      "config": "/home/linuxbrew/.linuxbrew/etc/icecast.xml"
    },
    {
      "user": "wharper",
      "pid": "2489",
      "config": "/home/wharper/icecast_config/icecast.xml"
    }
  ]
}
```

#### GET /icecast/<username>/status
Get Icecast status for specific user

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/icecast/wharper/status" \
  -H "X-User: wharper"
```

**Response**:
```json
{
  "user": "wharper",
  "running": true,
  "process_info": "wharper 2489 /home/linuxbrew/.linuxbrew/bin/icecast",
  "stats": {}
}
```

#### POST /icecast/<username>/restart
Restart Icecast for specific user (admins or owner only)

### TeamTalk Management

#### GET /teamtalk/servers/list
List all TeamTalk servers

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/teamtalk/servers/list" \
  -H "X-User: devinecr"
```

**Response**:
```json
{
  "servers": [
    "dom 1144 Home is where the heart is",
    "Server2 10340 Leetha's Lounge",
    "tappedin 1144 Welcome to tappedin.fm!",
    "WaltersPlace 10333 WalterHarpers"
  ],
  "raw_output": "..."
}
```

#### GET /teamtalk/servers/<name>/status
Get TeamTalk server status

#### POST /teamtalk/servers/<name>/start
Start TeamTalk server (admin only)

**Example**:
```bash
curl -X POST "http://64.20.46.178:5017/api/services/teamtalk/servers/tappedin/start" \
  -H "X-User: devinecr"
```

#### POST /teamtalk/servers/<name>/stop
Stop TeamTalk server (admin only)

#### POST /teamtalk/servers/<name>/restart
Restart TeamTalk server (admin only)

#### GET /teamtalk/servers/<name>/logs
Get TeamTalk server logs

**Parameters**:
- `lines` (number): Number of log lines (default: 100)

#### GET /teamtalk/commands
Get available TeamTalk commands and help

### System Services

#### GET /system/status
Get overall system status

**Example**:
```bash
curl "http://64.20.46.178:5017/api/services/system/status" \
  -H "X-User: devinecr"
```

**Response**:
```json
{
  "services": {
    "apache2": {
      "active": false,
      "status": "inactive"
    },
    "nginx": {
      "active": true,
      "status": "active"
    },
    "mysql": {
      "active": true,
      "status": "active"
    }
  },
  "load_average": "load average: 0.52, 0.58, 0.59",
  "disk_usage": "Filesystem Size Used Avail Use% Mounted on\n/dev/sda3 1.8T 400G 1.3T 24% /",
  "timestamp": "2025-10-03T08:39:36.000Z"
}
```

#### GET /health
Check Services Manager API health

#### GET /info
Get API information and available endpoints

---

## Web Management Interface

A comprehensive web-based management interface is available at:

**URL**: `http://devinecreations.net/pages/custom/services.php`

### Features:

1. **API Key Generation** - Generate user-specific access keys
2. **Docker Management** - Start, stop, restart containers
3. **CopyParty Control** - Manage volumes and files
4. **Jellyfin Management** - Monitor and restart media server
5. **Icecast Servers** - Control streaming servers
6. **TeamTalk Servers** - Manage voice servers
7. **System Monitoring** - View system status and resources

### Usage:

1. Enter your username (e.g., `devinecr`, `dom`, `tappedin`)
2. Click "Generate API Key"
3. Use the tabs to manage different services
4. Admin users can start/stop/restart services
5. General users can view status and manage their own services

---

## API Examples

### Python

```python
import requests

API_BASE = "http://64.20.46.178:5017/api/services"
headers = {"X-User": "devinecr"}

# List Docker containers
response = requests.get(f"{API_BASE}/docker/containers/list", headers=headers)
containers = response.json()
print(containers)

# Restart a container
response = requests.post(
    f"{API_BASE}/docker/containers/portainer/restart",
    headers=headers
)
print(response.json())
```

### JavaScript

```javascript
const API_BASE = "http://64.20.46.178:5017/api/services";
const headers = {"X-User": "devinecr"};

// List Docker containers
fetch(`${API_BASE}/docker/containers/list`, {headers})
  .then(res => res.json())
  .then(data => console.log(data));

// Restart a container
fetch(`${API_BASE}/docker/containers/portainer/restart`, {
  method: "POST",
  headers
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### Bash/cURL

```bash
# Set your username
USER="devinecr"

# List Docker containers
curl "http://64.20.46.178:5017/api/services/docker/containers/list" \
  -H "X-User: $USER"

# Restart a container
curl -X POST "http://64.20.46.178:5017/api/services/docker/containers/portainer/restart" \
  -H "X-User: $USER"

# Upload a file to CopyParty
curl -X POST "http://64.20.46.178:5016/api/copyparty/files/upload" \
  -H "X-User: $USER" \
  -F "file=@/path/to/file.txt" \
  -F "path=/shared/"

# Get system status
curl "http://64.20.46.178:5017/api/services/system/status" \
  -H "X-User: $USER"
```

---

## Systemd Services

All APIs are configured as systemd services for automatic startup:

### CopyParty Admin API
```bash
systemctl status copyparty-admin-api.service
systemctl restart copyparty-admin-api.service
journalctl -u copyparty-admin-api.service -f
```

### Services Manager API
```bash
systemctl status services-manager-api.service
systemctl restart services-manager-api.service
journalctl -u services-manager-api.service -f
```

### Unified API Gateway
```bash
systemctl status api-gateway.service
systemctl restart api-gateway.service
journalctl -u api-gateway.service -f
```

---

## Error Handling

All APIs return standardized error responses:

```json
{
  "error": "Error description",
  "details": "Additional details if available"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (missing parameters)
- `401` - Unauthorized (invalid API key or user)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Security Notes

1. **Authentication Required**: All administrative operations require proper user authentication
2. **Role-Based Access**: Admin users have full access, general users have limited access
3. **Service Isolation**: Each service runs with appropriate user permissions
4. **API Keys**: Generate unique API keys for external access
5. **Firewall**: Configure CSF/firewall rules to restrict API access if needed

---

## Support and Troubleshooting

### Check Service Status
```bash
systemctl status copyparty-admin-api.service services-manager-api.service api-gateway.service
```

### View Logs
```bash
tail -f /var/log/copyparty-admin-api.log
tail -f /var/log/services-manager-api.log
tail -f /var/log/api-gateway.log
```

### Test Endpoints
```bash
# Test CopyParty API
curl http://localhost:5016/api/copyparty/health

# Test Services Manager API
curl http://localhost:5017/api/services/health

# Test Gateway
curl http://localhost:5015/health
```

### Common Issues

1. **Module not found errors**: Ensure virtual environment is activated
2. **Permission denied**: Check file permissions and user ownership
3. **Port already in use**: Check for conflicting services on ports 5015-5017
4. **Authentication failed**: Verify username is in allowed users list

---

## Future Enhancements

Planned features:
- [ ] API rate limiting
- [ ] Request logging and analytics
- [ ] Webhook notifications for service events
- [ ] OAuth integration
- [ ] Additional service integrations
- [ ] Enhanced monitoring and alerting

---

Last Updated: 2025-10-03
Version: 1.0.0
