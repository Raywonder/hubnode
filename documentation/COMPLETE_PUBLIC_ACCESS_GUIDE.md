# Complete Public Access Guide - All Applications
## File Server Authentication & Public URLs

### 🌐 Primary Access Portal
**Main Files Server:** `https://files.devinecreations.net:3924/`

---

## 🔐 Authentication Accounts & Passwords

### Core User Accounts
| Username | Password | Access Level | Owner |
|----------|----------|-------------|-------|
| `admin` | `hub-node-api-2024` | Full System Access | System Administrator |
| `public` | `public-download-2025` | Read-Only Public | Public Downloads |

### Individual User Accounts
| Username | Password | Access Level | Owner/Contact |
|----------|----------|-------------|---------------|
| `devinecr` | `devinecreat-files-2024` | Full Access to DevineCreations | Devon (devinecr@gmail.com) |
| `dom` | `composr-import-2024` | Full Access to Composr/RayWonderIs | Dom (dom@raywonderis.me) |
| `tappedin` | `tappedin-uploads-2024` | Full Access to TappedIn | TappedIn Team |
| `wharper` | `walter-files-2024` | Full Access to WalterHarper | Walter Harper |
| `tetoeehoward` | `tetoee-files-2024` | Full Access to TetoeeHoward | Tetoee Howard |

### Application-Specific Accounts
| Username | Password | Access Level | Application/Owner |
|----------|----------|-------------|------------------|
| `patchmate` | `patchmate-app-2025` | PatchMate App Access | **Matthew Whitaker** |
| `audioportrait` | `audio-portrait-api-2025` | Audio Portrait API | Audio Portrait Team |
| `bema` | `bema-media-2025` | BEMA Media Player | BEMA Development |
| `context7` | `context7-api-2025` | Context7 API | Context7 Team |
| `ufm` | `ufm-manager-2025` | UFM License Manager | UFM Team |
| `socketio` | `socket-server-2025` | Socket Server | Socket Development |
| `jellyfin` | `jellyfin-media-2025` | Jellyfin Media | Media Server |
| `openlink` | `openlink-api-2025` | OpenLink API | OpenLink Team |
| `chatterbox` | `chatterbox-chat-2025` | Chatterbox Chat | Chatterbox Team |
| `claude` | `claude-ext-2025` | Claude Extensions | Claude Development |
| `mastodon` | `mastodon-social-2025` | Mastodon Social | Social Media |
| `sonobus` | `sonobus-audio-2025` | SonoBus Audio | Audio Streaming |
| `composer` | `composr-manage-2025` | Composr Management | Composr CMS |
| `wordpress` | `wp-manage-2025` | WordPress Management | WordPress Sites |

---

## 📂 Directory Access Map

### Public Directories (No Authentication Required)
```
🌐 Public Upload Access:
├── /public/dom-uploads/ → https://files.devinecreations.net:3924/public/dom-uploads/
├── /public/devinecr-uploads/ → https://files.devinecreations.net:3924/public/devinecr-uploads/
├── /public/tappedin-uploads/ → https://files.devinecreations.net:3924/public/tappedin-uploads/
├── /public/wharper-uploads/ → https://files.devinecreations.net:3924/public/wharper-uploads/
└── /public/tetoeehoward-uploads/ → https://files.devinecreations.net:3924/public/tetoeehoward-uploads/
```

### Shared Access Directory
```
🤝 Shared Directory Access (All app accounts have access):
/shared/ → https://files.devinecreations.net:3924/shared/
  - Available to: All authenticated application accounts
  - Permissions: Read, Write, Move
```

### Individual User Directories
```
🏠 User Home Directories:
├── /dom-home/ → https://files.devinecreations.net:3924/dom-home/
├── /devinecr-home/ → https://files.devinecreations.net:3924/devinecr-home/
├── /tappedin-home/ → https://files.devinecreations.net:3924/tappedin-home/
├── /wharper-home/ → https://files.devinecreations.net:3924/wharper-home/
└── /tetoeehoward-home/ → https://files.devinecreations.net:3924/tetoeehoward-home/
```

### Application Directories
```
🚀 Application Access:
├── /apps-devinecr/ → https://files.devinecreations.net:3924/apps-devinecr/
├── /apps-tappedin/ → https://files.devinecreations.net:3924/apps-tappedin/
├── /apps-dom/ → https://files.devinecreations.net:3924/apps-dom/
├── /hubnode-clients/ → https://files.devinecreations.net:3924/hubnode-clients/
├── /hubnode-api/ → https://files.devinecreations.net:3924/hubnode-api/
├── /hubnode-backend/ → https://files.devinecreations.net:3924/hubnode-backend/
└── /audio-portrait-dist/ → https://files.devinecreations.net:3924/audio-portrait-dist/
```

---

## 🎯 Application-Specific Access

### PatchMate (Matthew Whitaker)
- **CopyParty Account:** `patchmate` / `patchmate-app-2025`
- **Direct Access:** `https://files.devinecreations.net:3924/patchmate/`
- **API Endpoint:** `https://files.devinecreations.net:3924/patchmate/api/`
- **Private Documentation:** `/home/devinecr/apps/MATTHEW_WHITAKER_PRIVATE_ACCESS.md`
- **Setup Script:** `/home/devinecr/apps/claude-code-setup.sh`

### Audio Portrait
- **Account:** `audioportrait` / `audio-portrait-api-2025`
- **Direct Access:** `https://files.devinecreations.net:3924/audio-portrait-dist/`
- **API Endpoint:** `https://files.devinecreations.net:3924/audio-portrait/api/`

### BEMA Media Player
- **Account:** `bema` / `bema-media-2025`
- **Direct Access:** `https://files.devinecreations.net:3924/bema/`
- **API Endpoint:** `https://files.devinecreations.net:3924/bema/api/`

### Context7
- **Account:** `context7` / `context7-api-2025`
- **Direct Access:** `https://files.devinecreations.net:3924/context7/`
- **API Endpoint:** `https://files.devinecreations.net:3924/context7/api/`

---

## 🔗 OpenLink Integration

### OpenLink Portal Access
- **Main Portal:** `https://openlink.devinecreations.net/`
- **API Access:** `https://openlink.devinecreations.net/api/`
- **Application APIs:** `https://openlink.devinecreations.net/api/{app-name}/`

### Per-Application OpenLink URLs
```
🔗 Application-Specific OpenLink Access:
├── PatchMate: https://openlink.devinecreations.net/api/patchmate/
├── Audio Portrait: https://openlink.devinecreations.net/api/audioportrait/
├── BEMA: https://openlink.devinecreations.net/api/bema/
├── Context7: https://openlink.devinecreations.net/api/context7/
├── UFM: https://openlink.devinecreations.net/api/ufm/
├── Socket Server: https://openlink.devinecreations.net/api/socketio/
├── Jellyfin: https://openlink.devinecreations.net/api/jellyfin/
├── Chatterbox: https://openlink.devinecreations.net/api/chatterbox/
├── Claude Extensions: https://openlink.devinecreations.net/api/claude/
├── Mastodon: https://openlink.devinecreations.net/api/mastodon/
└── SonoBus: https://openlink.devinecreations.net/api/sonobus/
```

---

## 🚀 API Endpoints & WebSocket Connections

### Socket Server Endpoints
- **Main Socket:** `wss://files.devinecreations.net:3924/socket/`
- **Public WebSocket:** `wss://files.devinecreations.net:3924/ws/`
- **Health Check:** `https://files.devinecreations.net:3924/socket/health`

### HubNode API Endpoints
- **Main API:** `https://files.devinecreations.net:3924/hubnode-api/`
- **Health Check:** `https://files.devinecreations.net:3924/hubnode-api/health`
- **Sync Endpoint:** `https://files.devinecreations.net:3924/hubnode-api/sync`

---

## 📱 How to Access

### Web Browser Access
1. Navigate to: `https://files.devinecreations.net:3924/`
2. Login with your assigned username/password
3. Browse to your designated directories

### Command Line Access
```bash
# Download file using curl with authentication
curl -u username:password https://files.devinecreations.net:3924/path/to/file

# Upload file using curl
curl -u username:password -T file.txt https://files.devinecreations.net:3924/upload/path/

# WebDAV access (if supported)
# Configure WebDAV client with: https://files.devinecreations.net:3924/
```

### Application Integration
```javascript
// JavaScript example for application integration
const fileServerUrl = 'https://files.devinecreations.net:3924/';
const openLinkUrl = 'https://openlink.devinecreations.net/api/';
const socketUrl = 'wss://files.devinecreations.net:3924/socket/';

// Authenticated request
fetch(fileServerUrl + 'api/endpoint', {
  headers: {
    'Authorization': 'Basic ' + btoa('username:password')
  }
});
```

---

## 🛡️ Security Notes

### Important Security Information
- **Never share credentials** - Each account is application-specific
- **HTTPS Only** - All connections are encrypted
- **IP Monitoring** - Access is logged and monitored
- **Rate Limiting** - API endpoints have rate limits applied
- **CORS Protection** - Cross-origin requests are restricted

### Backup Access Methods
- **Admin Override:** Contact system administrator for emergency access
- **Public Fallback:** Use public directories if authentication fails
- **OpenLink Alternative:** Use OpenLink portal for temporary access

---

**Generated:** $(date)
**Server Version:** CopyParty v1.19.11
**Port:** 3924 (HTTPS)
**Total Authenticated Accounts:** 20+
**Public Directories:** 5
**Application Accounts:** 11