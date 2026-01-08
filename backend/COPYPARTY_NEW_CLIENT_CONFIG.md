# 🔒 CopyParty Secure Client Configuration - NEW METHOD

**⚠️ IMPORTANT: NO MORE PORT NUMBERS!**

All CopyParty access now uses secure HTTPS domains without port numbers. If you're currently using `:3923` or any port numbers, **update immediately** to these new secure URLs.

## 🌐 New Secure Access URLs (NO PORTS)

### Public HTTPS URLs:
- **RayWonderIs.Me**: `https://files.raywonderis.me`
- **DevineCreations.net**: `https://files.devinecreations.net`
- **TappedIn.fm**: `https://files.tappedin.fm`
- **TetoeeHoward.com**: `https://files.tetoeehoward.com`
- **WalterHarper.com**: `https://files.walterharper.com`

### Local Internal Access:
- **Local Proxy**: `http://127.0.0.1:8080` (no auth required)

## 🔐 Same Authentication Credentials

| Username | Password | Access Level |
|----------|----------|-----------------|
| **admin** | hub-node-api-2024 | Full system access |
| **tappedin** | tappedin-uploads-2024 | TappedIn.fm files |
| **dom** | composr-import-2024 | RayWonderIs.Me files |
| **devinecr** | devinecreat-files-2024 | DevineCreations files |
| **tetoeehoward** | tetoee-files-2024 | TetoeeHoward files |
| **wharper** | walter-files-2024 | WalterHarper files |
| **audioportrait** | audio-portrait-api-2025 | Audio Portrait app |
| **public** | public-download-2025 | Read-only access |

## 💻 Update Your Local Connections

### Mac Users:
```bash
# OLD METHOD (STOP USING):
# mount -t webdav https://64.20.46.178:3923/dav/ ~/CopyParty

# NEW SECURE METHOD:
mount -t webdav https://files.raywonderis.me/dav/ ~/CopyParty

# Or via Finder: Go > Connect to Server
# https://files.raywonderis.me/dav/
```

### Windows Users:
```cmd
# OLD METHOD (STOP USING):
# net use Z: https://64.20.46.178:3923/dav/ /user:admin hub-node-api-2024

# NEW SECURE METHOD:
net use Z: https://files.raywonderis.me/dav/ /user:admin hub-node-api-2024

# Or via Windows Explorer:
# This PC > Map Network Drive > https://files.raywonderis.me/dav/
```

### Linux Users:
```bash
# OLD METHOD (STOP USING):
# sudo mount -t davfs https://64.20.46.178:3923/dav/ /mnt/copyparty

# NEW SECURE METHOD:
sudo mount -t davfs https://files.raywonderis.me/dav/ /mnt/copyparty

# Update /etc/fstab:
https://files.raywonderis.me/dav/ /mnt/copyparty davfs defaults 0 0
```

## 🔄 WebDAV Mounting (Choose Your Domain)

Based on which site you primarily work with:

```bash
# For RayWonderIs.me content:
https://files.raywonderis.me/dav/

# For DevineCreations.net content:
https://files.devinecreations.net/dav/

# For TappedIn.fm content:
https://files.tappedin.fm/dav/

# For TetoeeHoward.com content:
https://files.tetoeehoward.com/dav/

# For WalterHarper.com content:
https://files.walterharper.com/dav/
```

## 🔧 Update Existing Bookmarks/Scripts

### Browser Bookmarks:
- **OLD**: `https://64.20.46.178:3923/`
- **NEW**: `https://files.raywonderis.me/`

### API Scripts:
```bash
# OLD API calls:
curl -u admin:hub-node-api-2024 https://64.20.46.178:3923/api/ls/

# NEW API calls:
curl -u admin:hub-node-api-2024 https://files.raywonderis.me/api/ls/
```

## ⚠️ Important Migration Notes

1. **Remove all port numbers** (`:3923`, `:3924`) from your configurations
2. **Use domain-specific SSL** - each files.* subdomain has its own valid certificate
3. **Update WebDAV mounts** to use the new HTTPS URLs
4. **No more IP addresses** - use the domain names for proper SSL validation
5. **Same credentials** - all usernames and passwords remain unchanged

## 🛡️ Security Improvements

- ✅ **No exposed ports** - Everything goes through secure HTTPS
- ✅ **Valid SSL certificates** - Each domain uses its own certificate
- ✅ **Domain-based access** - Proper subdomain routing
- ✅ **Enhanced security headers** - HSTS, frame protection, content type protection
- ✅ **Large file uploads** - Support up to 2GB files
- ✅ **WebSocket support** - Real-time updates

## 📱 Mobile Access

All mobile apps and clients should now connect to:
- Primary: `https://files.raywonderis.me`
- Or your preferred domain from the list above

## 🔗 Quick Test Links

Test your new secure access:
- Web Interface: https://files.raywonderis.me/
- Health Check: https://files.raywonderis.me/health
- WebDAV: https://files.raywonderis.me/dav/

---
**Migration Date**: 2025-09-27  
**Status**: LIVE - All old port-based access will eventually be deprecated