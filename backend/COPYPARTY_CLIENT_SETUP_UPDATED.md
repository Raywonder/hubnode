# CopyParty Client Setup - No Exposed Ports (Updated)
**Date:** 2025-09-27 - **Version:** 2.0

## 🔒 Secure Access via HTTPS Domain Names

CopyParty now runs behind nginx reverse proxy without exposing ports directly. All access is through secure HTTPS domains.

## 📍 Access URLs

### Public HTTPS URLs (Recommended):
- **RayWonderIs.Me**: `https://files.raywonderis.me`
- **DevineCreations.net**: `https://files.devinecreations.net`
- **TappedIn.fm**: `https://files.tappedin.fm`
- **TetoeeHoward.com**: `https://files.tetoeehoward.com`
- **WalterHarper.com**: `https://files.walterharper.com`

### Local Access (Internal):
- **Local Proxy**: `http://127.0.0.1:8081` (no authentication required)
- **Direct Access**: `http://127.0.0.1:3924` (authentication required)

## 🔐 Authentication Credentials

All credentials remain the same:

| Username | Password | Access Level |
|----------|----------|--------------|
| **admin** | hub-node-api-2024 | Full system access |
| **tappedin** | tappedin-uploads-2024 | TappedIn.fm files |
| **dom** | composr-import-2024 | RayWonderIs.Me files |
| **devinecr** | devinecreat-files-2024 | DevineCreations files |
| **tetoeehoward** | tetoee-files-2024 | TetoeeHoward files |
| **wharper** | walter-files-2024 | WalterHarper files |
| **audioportrait** | audio-portrait-api-2025 | Audio Portrait app |
| **composer** | composr-manage-2025 | Composr management |
| **wordpress** | wp-manage-2025 | WordPress management |
| **public** | public-download-2025 | Read-only access |

## 💻 Platform Setup

### Mac Setup:
```bash
# WebDAV mounting (choose your preferred domain)
mkdir -p ~/CopyParty
open "https://files.raywonderis.me"  # Web interface

# Terminal WebDAV mount
mount -t webdav https://files.raywonderis.me/dav/ ~/CopyParty

# Or use Finder: Go > Connect to Server > https://files.raywonderis.me/dav/
```

### Windows Setup:
```cmd
# Map network drive
net use Z: https://files.raywonderis.me/dav/ /user:admin hub-node-api-2024

# Or via Windows Explorer:
# This PC > Map Network Drive > https://files.raywonderis.me/dav/
```

### Linux Setup:
```bash
# Install davfs2
sudo apt install davfs2  # Ubuntu/Debian
sudo yum install davfs2  # CentOS/RHEL

# Mount WebDAV
sudo mkdir -p /mnt/copyparty
sudo mount -t davfs https://files.raywonderis.me/dav/ /mnt/copyparty

# Add to /etc/fstab for permanent mounting
echo "https://files.raywonderis.me/dav/ /mnt/copyparty davfs defaults 0 0" | sudo tee -a /etc/fstab
```

## 🔄 Claude Local Sync Integration

### Automatic Path Resolution:
The Claude Local Sync API now automatically detects and maps file paths:

```bash
# Test path resolution
cd /home/devinecr/apps/hubnode/api
python3 claude-path-resolver.py

# Example mappings:
# /home/dom/public_html/uploads/test.jpg → /composr-raywonderis/uploads/test.jpg
# /home/devinecr/apps/hubnode/api/app.py → /hubnode-api/app.py
# /home/tappedin/apps/audio-portrait/file.mp3 → /audio-portrait-dev/file.mp3
```

### Real-time Sync Features:
- ✅ **Automatic path detection** - Files placed anywhere are automatically mapped to correct CopyParty paths
- ✅ **Bidirectional sync** - Changes on server instantly sync to local Claude
- ✅ **Multi-platform support** - Works on Mac, Windows, Linux
- ✅ **Conflict resolution** - Server changes take priority
- ✅ **Authentication handling** - Automatically uses correct credentials per path

## 📂 Directory Structure

### Available Paths:
```
Composr Sites:
├── /composr-raywonderis/uploads/          → https://files.raywonderis.me/composr-raywonderis/uploads/
├── /composr-raywonderis/website_specific/ → https://files.raywonderis.me/composr-raywonderis/website_specific/
├── /composr-devinecreations/uploads/      → https://files.devinecreations.net/composr-devinecreations/uploads/
└── /composr-devinecreations/filedump/     → https://files.devinecreations.net/composr-devinecreations/filedump/

WordPress Sites:
├── /wp-tappedin/uploads/                  → https://files.tappedin.fm/wp-tappedin/uploads/
├── /wp-tetoeehoward/uploads/              → https://files.tetoeehoward.com/wp-tetoeehoward/uploads/
└── /wp-walterharper/uploads/              → https://files.walterharper.com/wp-walterharper/uploads/

Applications:
├── /audio-portrait-dev/                   → https://files.raywonderis.me/audio-portrait-dev/
├── /audio-portrait-dist/                  → https://files.raywonderis.me/audio-portrait-dist/
├── /hubnode-api/                          → https://files.raywonderis.me/hubnode-api/
└── /apps-tappedin/                        → https://files.tappedin.fm/apps-tappedin/

User Directories:
├── /root-devinecr/                        → https://files.devinecreations.net/root-devinecr/
├── /root-tappedin/                        → https://files.tappedin.fm/root-tappedin/
└── /root-dom/                             → https://files.raywonderis.me/root-dom/
```

## 🚀 API Integration

### RESTful API Access:
```bash
# Upload file
curl -u admin:hub-node-api-2024 \
  -X POST \
  -F "file=@localfile.txt" \
  https://files.raywonderis.me/api/upload/hubnode-api/

# Download file
curl -u admin:hub-node-api-2024 \
  -o downloaded.txt \
  https://files.raywonderis.me/api/download/hubnode-api/file.txt

# List directory
curl -u admin:hub-node-api-2024 \
  https://files.raywonderis.me/api/ls/hubnode-api/
```

### Claude Sync Status:
```bash
# Check sync status
curl http://localhost:3923/sync/status

# Force sync directory
curl -X POST http://localhost:3923/sync/force \
  -H "Content-Type: application/json" \
  -d '{"directory": "/home/devinecr/apps/hubnode/api"}'

# Test CopyParty direct access
curl -u admin:hub-node-api-2024 http://localhost:3924/

# Test specific user access
curl -u dom:composr-import-2024 http://localhost:3924/composr-raywonderis/uploads/
```

## 📊 Monitoring

### Health Checks:
```bash
# Service health
curl https://files.raywonderis.me/health

# Claude sync health
curl http://localhost:3923/health

# Audio Portrait API
curl http://localhost:5001/health
```

### Log Monitoring:
```bash
# CopyParty logs
tail -f /var/log/copyparty.log

# Claude sync logs
tail -f /var/log/claude-sync.log

# Nginx access logs
tail -f /var/log/nginx/access.log | grep files.
```

## 🔧 Troubleshooting

### Connection Issues:
1. **Check service status**: `systemctl status copyparty claude-sync nginx`
2. **Verify DNS**: `nslookup files.raywonderis.me`
3. **Test local access**: `curl http://127.0.0.1:8080/health`
4. **Check SSL certificates**: `openssl s_client -connect files.raywonderis.me:443`

### Authentication Problems:
1. **Verify credentials** in configuration files
2. **Check user permissions** on local directories
3. **Test with admin account** first
4. **Ensure proper path mapping** using claude-path-resolver.py

### Sync Issues:
1. **Check Claude sync service**: `systemctl status claude-sync`
2. **Monitor sync queue**: `curl http://localhost:3923/sync/status`
3. **Force manual sync**: Use POST to `/sync/force` endpoint
4. **Verify file permissions** on local directories

## 📁 File Organization

Files are automatically organized by Claude based on:
- **File location** - Determines which CopyParty path to use
- **File type** - Images, videos, documents automatically categorized
- **User ownership** - Files sync to appropriate user directories
- **Application context** - Audio Portrait files go to application paths

**All login methods preserved and enhanced with secure HTTPS access through domain names.**

---
Generated: 2025-09-27 19:50 EDT
Status: PRODUCTION READY - NO EXPOSED PORTS