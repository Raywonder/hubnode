# Complete Access URLs and Integration Guide

## Public Web Access URLs

### Audio Portrait Downloads
**Primary Distribution:**
- `https://devinecreations.net/uploads/website_specific/apps/audio-portrait/`
- `https://raywonderis.me/uploads/website_specific/apps/audio-portrait/`

**Direct API Downloads:**
- `https://api.devinecreations.net/api/audio-portrait/download/mac`
- `https://api.devinecreations.net/api/audio-portrait/download/mac-arm64`
- `https://api.devinecreations.net/api/audio-portrait/download/windows`

### Composr Site URLs (Public Access)

#### DevineCreations.net (Composr)
- **Main Site**: `https://devinecreations.net/`
- **Downloads**: `https://devinecreations.net/uploads/`
- **Apps**: `https://devinecreations.net/uploads/website_specific/apps/`
- **Attachments**: `https://devinecreations.net/uploads/attachments/`
- **Galleries**: `https://devinecreations.net/uploads/galleries/`
- **File Sharing**: `https://devinecreations.net/uploads/filedump/`

#### RayWonderIs.Me (Composr)
- **Main Site**: `https://raywonderis.me/`
- **Downloads**: `https://raywonderis.me/uploads/`
- **Apps**: `https://raywonderis.me/uploads/website_specific/apps/`
- **Attachments**: `https://raywonderis.me/uploads/attachments/`
- **Galleries**: `https://raywonderis.me/uploads/galleries/`
- **File Sharing**: `https://raywonderis.me/uploads/filedump/`

#### DevineCreations.com (WHMCS)
- **Main Site**: `https://devinecreations.com/`
- **Client Area**: `https://devinecreations.com/clientarea.php`
- **Downloads**: `https://devinecreations.com/downloads/`

### WordPress Sites

#### TappedIn.fm
- **Main Site**: `https://tappedin.fm/`
- **Media**: `https://tappedin.fm/wp-content/uploads/`
- **Podcasts**: `https://tappedin.fm/wp-content/uploads/podcast-submissions/`

#### TetoeeHoward.com
- **Main Site**: `https://tetoeehoward.com/`
- **Media**: `https://tetoeehoward.com/wp-content/uploads/`

#### WalterHarper.com
- **Main Site**: `https://walterharper.com/`
- **Media**: `https://walterharper.com/wp-content/uploads/`

## CopyParty Direct Access

### Primary Access
- **URL**: `http://64.20.46.178:3923`
- **Alternative**: `https://files.devinecreations.net`

### CopyParty Directory Structure

#### Composr Sites
```
/composr-devinecreations/         # DevineCreations.net Composr
├── uploads/                      # Main public downloads
├── website_specific/apps/        # All applications
├── apps/audio-portrait/          # Audio Portrait distribution
├── filedump/                     # Private file sharing
│   ├── updates/                  # App updates
│   ├── licenses/                 # License files
│   └── shared/files/             # User shared files
├── attachments/                  # Forum attachments
└── galleries/                    # Photo galleries

/composr-raywonderis/             # RayWonderIs.Me Composr
├── uploads/                      # Main public downloads
├── website_specific/apps/        # All applications
├── apps/audio-portrait/          # Audio Portrait distribution
├── filedump/                     # Private file sharing
├── attachments/                  # Forum attachments
└── galleries/                    # Photo galleries

/whmcs-devinecr/                  # WHMCS frontend files
```

#### WordPress Sites
```
/wp-tappedin/
├── uploads/                      # All media uploads
└── podcast-submissions/          # Podcast files

/wp-tetoeehoward/uploads/         # TetoeeHoward media
/wp-walterharper/uploads/         # WalterHarper media
```

#### Application Development
```
/apps-tappedin/                   # TappedIn applications
/apps-devinecr/                   # DevineCreations applications
/apps-dom/                        # Dom's applications

/hubnode-clients/                 # HubNode client apps
/hubnode-api/                     # API services
/hubnode-backend/                 # Backend services

/audio-portrait-dist/             # Official distribution
/audio-portrait-dev/              # Development workspace
```

#### File Management
```
/downloads-devinecr/              # Downloads (lowercase)
/Downloads-devinecr/              # Downloads (capitalized)
/attachments-devinecr/            # Attachments (lowercase)
/Attachments-devinecr/            # Attachments (capitalized)
/shared/                          # Shared resources
```

#### Staging Areas
```
/incoming-raywonderis/            # RayWonderIs.Me staging
/incoming-devinecreations/        # DevineCreations.net staging
/incoming-tappedin/               # TappedIn.fm staging
```

#### Full System Access (Admin Only)
```
/root-tappedin/                   # Full TappedIn access
/root-devinecr/                   # Full DevineCreations access
/root-dom/                        # Full Dom access
/root-tetoeehoward/               # Full TetoeeHoward access
/root-wharper/                    # Full WalterHarper access
```

## API Endpoints

### Audio Portrait API
- **Health**: `https://api.devinecreations.net/api/audio-portrait/health`
- **Version**: `https://api.devinecreations.net/api/audio-portrait/version`
- **Config**: `https://api.devinecreations.net/api/audio-portrait/config`
- **License**: `https://api.devinecreations.net/api/audio-portrait/license/validate`

### HubNode API
- **Health**: `http://127.0.0.1:5001/api/audio-portrait/health`
- **Local API**: `http://127.0.0.1:5001/*`

## File Flow Architecture

### Distribution Flow
1. **Development**: `/home/tappedin/apps/audio-portrait/` (Build workspace)
2. **API Distribution**: `/home/devinecr/apps/hubnode/api/audio-portrait/uploads/` (Primary)
3. **Composr Apps**: `/home/devinecr/devinecreations.net/uploads/website_specific/apps/audio-portrait/` (Public)
4. **CopyParty Access**: Available via all configured paths

### Update Flow
1. **Filedump Updates**: `/composr-*/filedump/updates/` (Pull updates)
2. **License Management**: `/composr-*/filedump/licenses/` (License validation)
3. **User Files**: `/composr-*/filedump/shared/files/` (Future: User-generated content)

### Backup Access
- **Primary**: API endpoints
- **Secondary**: Composr public URLs  
- **Tertiary**: CopyParty direct access
- **Admin**: Full root access via CopyParty

## Security & Permissions

### CopyParty Authentication
- **admin**: `hub-node-api-2024` (Full access)
- **composer**: `composr-manage-2025` (Composr management)
- **wordpress**: `wp-manage-2025` (WordPress management)
- **audioportrait**: `audio-portrait-api-2025` (Audio Portrait specific)
- **public**: `public-download-2025` (Read-only)

### Web Security
- All HTTPS endpoints with proper SSL certificates
- Composr built-in permission system
- WHMCS integrated authentication
- WordPress user role management

This architecture provides multiple redundant access paths while maintaining proper Composr folder structure and security.