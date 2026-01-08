# CopyParty Complete Access Guide
## Full Upload Management for Mac/Windows Clients

### Overview
Complete file management system with access to all Composr uploads, WordPress uploads, and application directories across all domains.

### Access URLs
- **Primary**: https://files.devinecreations.net
- **Alternative**: http://64.20.46.178:3923

### Authentication Credentials

#### Full Admin Access
- **Username**: `admin`
- **Password**: `hub-node-api-2024`
- **Access**: All directories with read/write/modify

#### Site-Specific Users
| User | Password | Primary Access |
|------|----------|----------------|
| `composer` | `composr-manage-2025` | All Composr uploads |
| `wordpress` | `wp-manage-2025` | All WordPress uploads |
| `tappedin` | `tappedin-uploads-2024` | TappedIn.fm files |
| `dom` | `composr-import-2024` | RayWonderIs.Me files |
| `devinecr` | `devinecreat-files-2024` | DevineCreations files |
| `audioportrait` | `audio-portrait-api-2025` | Audio Portrait distribution |
| `public` | `public-download-2025` | Read-only public access |

### Directory Structure

#### Composr Uploads (Public Downloads & Website Management)
```
/composr-raywonderis/            # /home/dom/public_html/uploads/
├── uploads/                     # Main uploads directory
├── website_specific/            # Site-specific files and apps
├── filedump/                   # Private member file shares
├── attachments/                # Forum and content attachments
└── galleries/                  # Photo galleries

/composr-devinecreations/        # /home/devinecr/devinecreations.net/uploads/
├── uploads/                     # Main uploads directory
├── website_specific/            # Site-specific files and apps
├── filedump/                   # Private member file shares
├── attachments/                # Forum and content attachments
├── galleries/                  # Photo galleries
└── audio-portrait/             # Audio Portrait downloads

/whmcs-devinecr/                # /home/devinecr/public_html/ (WHMCS frontend)
```

#### WordPress Uploads
```
/wp-tappedin/
├── uploads/             # All media uploads
└── podcast-submissions/ # Podcast submission files

/wp-tetoeehoward/uploads/
/wp-walterharper/uploads/
```

#### Application Directories
```
/apps-tappedin/          # TappedIn applications
/apps-devinecr/          # DevineCreations applications
/apps-dom/               # Dom's applications

/hubnode-clients/        # HubNode client apps
/hubnode-api/           # API services
/hubnode-backend/       # Backend services
```

#### Special Project Directories
```
/audio-portrait-dist/    # Distribution files (.dmg, .exe)
/audio-portrait-dev/     # Development workspace
/shared/                 # Shared resources
/downloads-devinecr/     # Download archive
/attachments-devinecr/   # Email attachments
```

#### Incoming/Staging Areas
```
/incoming-raywonderis/
/incoming-devinecreations/
/incoming-tappedin/
```

#### Root Access (Admin Only)
```
/root-tappedin/
/root-devinecr/
/root-dom/
/root-tetoeehoward/
/root-wharper/
```

### Mac Setup (Mountain Duck / CyberDuck)

#### Mountain Duck Configuration
1. **New Bookmark**:
   - Protocol: `WebDAV (HTTPS)`
   - Server: `files.devinecreations.net`
   - Port: `443`
   - Username: (use credentials above)
   - Path: `/` (or specific directory)

2. **Mount as Drive**:
   - Enable: "Save Password"
   - Enable: "Mount on Login"
   - Cache: "Minimal" for real-time updates

#### Sync Script for Mac
```bash
#!/bin/bash
# sync-to-copyparty.sh

COPYPARTY_URL="https://files.devinecreations.net"
USERNAME="composer"  # or your username
PASSWORD="composr-manage-2025"

# Upload to Composr website_specific
curl -u "$USERNAME:$PASSWORD" \
     -X PUT \
     -T "local-file.zip" \
     "$COPYPARTY_URL/composr-raywonderis/website_specific/"

# Upload to WordPress uploads
curl -u "$USERNAME:$PASSWORD" \
     -X PUT \
     -T "image.jpg" \
     "$COPYPARTY_URL/wp-tappedin/uploads/2025/09/"

# Upload Audio Portrait build
curl -u "audioportrait:audio-portrait-api-2025" \
     -X PUT \
     -T "Audio Portrait-0.1.0.dmg" \
     "$COPYPARTY_URL/audio-portrait-dist/"
```

### Windows Setup

#### Windows Network Drive
1. Open File Explorer
2. Right-click "This PC" → "Map network drive"
3. Folder: `\\files.devinecreations.net@SSL\DavWWWRoot`
4. Check "Connect using different credentials"
5. Enter username and password

#### Windows PowerShell Upload
```powershell
# Upload to CopyParty
$user = "composer"
$pass = "composr-manage-2025"
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${user}:${pass}"))

# Upload file
Invoke-WebRequest -Uri "https://files.devinecreations.net/composr-devinecreations/uploads/" `
                  -Method PUT `
                  -Headers @{Authorization="Basic $auth"} `
                  -InFile "C:\local\file.zip"
```

### Direct Web Upload
1. Navigate to: https://files.devinecreations.net
2. Login with credentials
3. Browse to desired directory
4. Click "Upload" or drag & drop files

### Use Cases

#### 1. Composr Downloads Management
- Upload to `/composr-*/uploads/` for public downloads
- Use `/composr-*/website_specific/` for site-specific modules
- Private member files in `/composr-*/filedump/`

#### 2. WordPress Media Management
- Direct upload to `/wp-*/uploads/YYYY/MM/` structure
- Podcast submissions to `/wp-tappedin/podcast-submissions/`

#### 3. Application Distribution
- Production builds to `/audio-portrait-dist/`
- Development files to `/apps-*/`
- Client apps to `/hubnode-clients/`

#### 4. Collaborative Development
- Shared resources in `/shared/`
- Incoming files in `/incoming-*/`
- Direct app access via `/apps-*/`

### Security Notes
- All transfers use HTTPS encryption
- Each user has specific directory permissions
- Public user has read-only access
- Admin has full access to all directories

### Troubleshooting
- If connection fails, try http://64.20.46.178:3923
- For large files (>100MB), use chunked upload
- Clear browser cache if directories don't update
- Check firewall settings for port 3923

### API Integration
Files uploaded via CopyParty are immediately available through:
- Composr: `https://[domain]/uploads/[path]`
- WordPress: `https://[domain]/wp-content/uploads/[path]`
- Direct API: `https://api.devinecreations.net/api/[service]/download/[file]`

This complete integration allows seamless file management across all platforms from any Mac or Windows machine!