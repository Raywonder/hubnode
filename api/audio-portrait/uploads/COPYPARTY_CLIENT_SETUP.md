# CopyParty Client Setup Guide
**Universal Configuration for Mac & Windows**

## 🌐 Server Information

**Primary Server**: `dvc.raywonderis.me` (64.20.46.178)
**CopyParty Port**: 3923
**Web Interface**: https://files.devinecreations.net/

## 📁 Available Directories & Access

### User-Specific Access
| Directory | Username | Password | Local Mount Point |
|-----------|----------|----------|------------------|
| **Admin Access** | `admin` | `hub-node-api-2024` | `/CopyParty-Server/` |
| **TappedIn** | `tappedin` | `tappedin-uploads-2024` | `/TappedIn/` |
| **Ray Wonder** | `dom` | `composr-import-2024` | `/RayWonder/` |
| **Devine Creations** | `devinecr` | `devinecreat-files-2024` | `/DevineCreations/` |
| **TetoeeHoward** | `tetoeehoward` | `tetoee-files-2024` | `/TetoeeHoward/` |
| **Walter Harper** | `wharper` | `walter-files-2024` | `/WalterHarper/` |
| **Audio Portrait** | `audioportrait` | `audio-portrait-api-2025` | `/AudioPortrait/` |

### Directory Mappings
| Server Path | CopyParty Volume | Description |
|-------------|------------------|-------------|
| `/home/devinecr/apps/hubnode/backend/uploads` | `/` (root) | Main uploads |
| `/home/tappedin/public_html/wp-content/uploads/podcast-submissions` | `/tappedin` | Podcast submissions |
| `/home/dom/public_html/uploads/incoming` | `/raywonderis` | Ray Wonder uploads |
| `/home/devinecr/downloads` | `/devine-creations-downloads` | Downloads |
| `/home/devinecr/attachments` | `/devine-creations-attachments` | Email attachments |
| `/home/devinecr/devinecreations.net/uploads/incoming` | `/devinecreations` | Website uploads |
| `/home/tetoeehoward/public_html` | `/tetoeehoward` | TetoeeHoward files |
| `/home/wharper/public_html/wp-content/uploads` | `/walterharper` | Walter Harper files |
| `/home/devinecr/shared` | `/shared` | Shared resources |
| `/home/devinecr/apps/hubnode/api/audio-portrait/uploads` | `/audio-portrait` | Audio Portrait builds |
| `/home/tappedin/apps` | `/tappedin-apps` | TappedIn applications |
| `/home/devinecr/apps` | `/devinecr-apps` | Devine Creations applications |
| `/home/dom/apps` | `/dom-apps` | Dom applications |

## 🖥️ Mac Setup Instructions

### Option 1: CopyParty Desktop Client (Recommended)

1. **Download CopyParty for Mac**:
   ```bash
   # If you already installed via brew:
   brew install copyparty
   
   # Or download from: https://github.com/9001/copyparty/releases
   ```

2. **Create Configuration File**:
   ```bash
   mkdir -p ~/CopyParty-Config
   cat > ~/CopyParty-Config/server-config.conf << 'EOF'
   # CopyParty Client Configuration
   # Server: dvc.raywonderis.me
   
   [DEFAULT]
   server = dvc.raywonderis.me
   port = 3923
   ssl = false
   
   [Admin]
   username = admin
   password = hub-node-api-2024
   local_path = ~/CopyParty-Server/Admin
   remote_path = /
   
   [AudioPortrait]
   username = audioportrait
   password = audio-portrait-api-2025
   local_path = ~/CopyParty-Server/AudioPortrait
   remote_path = /audio-portrait
   
   [DevineCreations]
   username = devinecr
   password = devinecreat-files-2024
   local_path = ~/CopyParty-Server/DevineCreations
   remote_path = /devine-creations-downloads
   
   [Shared]
   username = admin
   password = hub-node-api-2024
   local_path = ~/CopyParty-Server/Shared
   remote_path = /shared
   
   [TappedInApps]
   username = tappedin
   password = tappedin-uploads-2024
   local_path = ~/CopyParty-Server/TappedInApps
   remote_path = /tappedin-apps
   
   [DevineCreationsApps]
   username = devinecr
   password = devinecreat-files-2024
   local_path = ~/CopyParty-Server/DevineCreationsApps
   remote_path = /devinecr-apps
   
   [DomApps]
   username = dom
   password = composr-import-2024
   local_path = ~/CopyParty-Server/DomApps
   remote_path = /dom-apps
   EOF
   ```

3. **Create Mount Points**:
   ```bash
   mkdir -p ~/CopyParty-Server/{Admin,AudioPortrait,DevineCreations,TappedIn,RayWonder,Shared,TappedInApps,DevineCreationsApps,DomApps}
   ```

4. **Launch CopyParty Client**:
   ```bash
   # Option A: Command line sync
   copyparty --sync-config ~/CopyParty-Config/server-config.conf
   
   # Option B: Mount as network drive (if supported)
   copyparty --mount ~/CopyParty-Server/Admin dvc.raywonderis.me:3923/ -u admin:hub-node-api-2024
   ```

### Option 2: Web Interface Bookmarks

Create browser bookmarks for quick access:

```
Admin Access:          http://dvc.raywonderis.me:3923/
Audio Portrait:        http://dvc.raywonderis.me:3923/audio-portrait/
Devine Creations:      http://dvc.raywonderis.me:3923/devine-creations-downloads/
TappedIn:             http://dvc.raywonderis.me:3923/tappedin/
Shared Files:         http://dvc.raywonderis.me:3923/shared/
TappedIn Apps:        http://dvc.raywonderis.me:3923/tappedin-apps/
Devine Creations Apps: http://dvc.raywonderis.me:3923/devinecr-apps/
Dom Apps:             http://dvc.raywonderis.me:3923/dom-apps/
```

### Option 3: WebDAV Mount (macOS Finder)

1. **Open Finder** → **Go** → **Connect to Server** (⌘K)
2. **Enter URL**: `http://dvc.raywonderis.me:3923/audio-portrait/`
3. **Username**: `audioportrait`
4. **Password**: `audio-portrait-api-2025`
5. **Save to Keychain** for automatic reconnection

## 🪟 Windows Setup Instructions

### Option 1: CopyParty Windows Client

1. **Download CopyParty**:
   ```powershell
   # Download from: https://github.com/9001/copyparty/releases
   # Or via Python:
   pip install copyparty
   ```

2. **Create Batch File** (`CopyParty-Sync.bat`):
   ```batch
   @echo off
   echo Starting CopyParty Sync...
   
   REM Create directories
   mkdir "%USERPROFILE%\CopyParty-Server\Admin" 2>nul
   mkdir "%USERPROFILE%\CopyParty-Server\AudioPortrait" 2>nul
   mkdir "%USERPROFILE%\CopyParty-Server\DevineCreations" 2>nul
   mkdir "%USERPROFILE%\CopyParty-Server\Shared" 2>nul
   
   REM Start sync processes
   start "Admin Sync" copyparty --sync-up "%USERPROFILE%\CopyParty-Server\Admin" http://admin:hub-node-api-2024@dvc.raywonderis.me:3923/
   start "Audio Portrait Sync" copyparty --sync-up "%USERPROFILE%\CopyParty-Server\AudioPortrait" http://audioportrait:audio-portrait-api-2025@dvc.raywonderis.me:3923/audio-portrait/
   start "Devine Creations Sync" copyparty --sync-up "%USERPROFILE%\CopyParty-Server\DevineCreations" http://devinecr:devinecreat-files-2024@dvc.raywonderis.me:3923/devine-creations-downloads/
   
   echo CopyParty sync started. Check system tray for status.
   pause
   ```

3. **Run Batch File** to start automatic syncing

### Option 2: Network Drive Mapping (Windows)

1. **Open File Explorer**
2. **Right-click "This PC"** → **Map Network Drive**
3. **Drive Letter**: Choose available letter (e.g., Z:)
4. **Folder**: `\\dvc.raywonderis.me@3923\audio-portrait`
5. **Username**: `audioportrait`
6. **Password**: `audio-portrait-api-2025`
7. **Check "Reconnect at sign-in"**

## 🔄 Synchronization Scripts

### Mac Auto-Sync Script

Save as `~/CopyParty-AutoSync.sh`:

```bash
#!/bin/bash
# CopyParty Auto-Sync Script for Mac

SERVER="dvc.raywonderis.me:3923"
BASE_DIR="$HOME/CopyParty-Server"

# Function to sync directory
sync_directory() {
    local local_dir="$1"
    local remote_path="$2"
    local username="$3"
    local password="$4"
    
    echo "Syncing $local_dir..."
    mkdir -p "$local_dir"
    
    # Bi-directional sync
    copyparty --sync-both "$local_dir" "http://$username:$password@$SERVER$remote_path"
}

# Sync all directories
sync_directory "$BASE_DIR/AudioPortrait" "/audio-portrait/" "audioportrait" "audio-portrait-api-2025"
sync_directory "$BASE_DIR/DevineCreations" "/devine-creations-downloads/" "devinecr" "devinecreat-files-2024"
sync_directory "$BASE_DIR/Shared" "/shared/" "admin" "hub-node-api-2024"
sync_directory "$BASE_DIR/TappedIn" "/tappedin/" "tappedin" "tappedin-uploads-2024"

echo "Sync completed!"
```

Make executable: `chmod +x ~/CopyParty-AutoSync.sh`

### Windows Auto-Sync PowerShell

Save as `CopyParty-AutoSync.ps1`:

```powershell
# CopyParty Auto-Sync Script for Windows
$SERVER = "dvc.raywonderis.me:3923"
$BASE_DIR = "$env:USERPROFILE\CopyParty-Server"

function Sync-Directory {
    param(
        [string]$LocalDir,
        [string]$RemotePath,
        [string]$Username,
        [string]$Password
    )
    
    Write-Host "Syncing $LocalDir..."
    New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
    
    $url = "http://${Username}:${Password}@${SERVER}${RemotePath}"
    & copyparty --sync-both $LocalDir $url
}

# Sync all directories
Sync-Directory "$BASE_DIR\AudioPortrait" "/audio-portrait/" "audioportrait" "audio-portrait-api-2025"
Sync-Directory "$BASE_DIR\DevineCreations" "/devine-creations-downloads/" "devinecr" "devinecreat-files-2024"
Sync-Directory "$BASE_DIR\Shared" "/shared/" "admin" "hub-node-api-2024"
Sync-Directory "$BASE_DIR\TappedIn" "/tappedin/" "tappedin" "tappedin-uploads-2024"

Write-Host "Sync completed!"
```

## 📱 Mobile Access

### iOS/Android Web Access
- **URL**: `http://dvc.raywonderis.me:3923/`
- **Bookmark** specific directories with credentials in URL
- **Example**: `http://audioportrait:audio-portrait-api-2025@dvc.raywonderis.me:3923/audio-portrait/`

## ⚙️ Advanced Configuration

### Custom Sync Intervals

Add to crontab (Mac) or Task Scheduler (Windows):

**Mac crontab** (`crontab -e`):
```bash
# Sync every 15 minutes
*/15 * * * * /Users/yourusername/CopyParty-AutoSync.sh >> /Users/yourusername/copyparty-sync.log 2>&1
```

**Windows Task Scheduler**:
- **Action**: Start a program
- **Program**: `powershell.exe`
- **Arguments**: `-File "C:\Users\YourUser\CopyParty-AutoSync.ps1"`
- **Triggers**: Every 15 minutes

### Directory Watching (Real-time Sync)

**Mac** (using fswatch):
```bash
brew install fswatch
fswatch -o ~/CopyParty-Server/AudioPortrait | xargs -n1 -I{} ~/CopyParty-AutoSync.sh
```

**Windows** (using PowerShell):
```powershell
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "$env:USERPROFILE\CopyParty-Server\AudioPortrait"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action {
    & "C:\Users\YourUser\CopyParty-AutoSync.ps1"
}
```

## 🔐 Security Notes

- **Passwords** are stored in plain text in config files - secure your local machine
- **Network Traffic** is unencrypted (HTTP) - use only on trusted networks
- **VPN Access** recommended when accessing from external networks
- **Regular Backups** of local CopyParty-Server directory recommended

## 🛠️ Troubleshooting

### Connection Issues
1. **Test server connectivity**: `ping dvc.raywonderis.me`
2. **Test port access**: `telnet dvc.raywonderis.me 3923`
3. **Check firewall settings** on local machine
4. **Verify credentials** via web browser first

### Sync Issues
1. **Check disk space** on both local and server
2. **Review sync logs** for error messages
3. **Restart CopyParty service** if needed
4. **Clear local cache** and re-sync

### Performance Optimization
1. **Exclude large binary files** from auto-sync
2. **Use compression** for text files
3. **Schedule heavy syncs** during off-peak hours
4. **Monitor bandwidth usage**

## 📞 Support

- **Server Admin**: devinecr@tappedin.fm
- **CopyParty Docs**: https://github.com/9001/copyparty
- **Server Status**: https://api.devinecreations.net/api/audio-portrait/health

---

**This configuration provides seamless access to all server directories across Mac and Windows machines with automatic synchronization capabilities.**