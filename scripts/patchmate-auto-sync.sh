#!/bin/bash
# PatchMate Auto-Sync Script
# Automatically syncs PatchMate repository with Matthew Whitaker's GitHub repo
# Runs every 5 minutes via cron job

set -e

# Configuration
GITHUB_TOKEN="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"
GITHUB_USER="Matthew2244"
GITHUB_REPO="PatchMate"
LOCAL_PATH="/home/devinecr/apps/patchmate-deployment"
BACKUP_PATH="/home/devinecr/apps/patchmate-deployment-backup"
LOG_FILE="/var/log/patchmate-sync.log"
LOCK_FILE="/tmp/patchmate-sync.lock"
REMOTE_URL="https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Check if script is already running
if [ -f "${LOCK_FILE}" ]; then
    log "SKIP: PatchMate sync already running (lock file exists)"
    exit 0
fi

# Create lock file
echo $$ > "${LOCK_FILE}"

# Cleanup function
cleanup() {
    rm -f "${LOCK_FILE}"
}
trap cleanup EXIT

log "Starting PatchMate auto-sync process..."

# Create backup of current deployment if it exists
if [ -d "${LOCAL_PATH}" ]; then
    log "Creating backup of current PatchMate deployment..."
    if [ -d "${BACKUP_PATH}" ]; then
        rm -rf "${BACKUP_PATH}"
    fi
    cp -r "${LOCAL_PATH}" "${BACKUP_PATH}"
    log "Backup created at: ${BACKUP_PATH}"
fi

# Clone or update repository
if [ -d "${LOCAL_PATH}/.git" ]; then
    log "Updating existing PatchMate repository..."
    cd "${LOCAL_PATH}"
    
    # Set remote URL with token
    git remote set-url origin "${REMOTE_URL}" 2>/dev/null || {
        log "Setting remote URL..."
        git remote add origin "${REMOTE_URL}"
    }
    
    # Fetch latest changes
    log "Fetching latest changes from GitHub..."
    git fetch origin main 2>&1 | tee -a "${LOG_FILE}"
    
    # Check if there are any changes
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "${LOCAL_COMMIT}" = "${REMOTE_COMMIT}" ]; then
        log "No changes detected - repository is up to date"
    else
        log "Changes detected - updating local repository..."
        
        # Stash any local changes
        if ! git diff-index --quiet HEAD --; then
            log "Stashing local changes..."
            git stash push -m "Auto-stash before sync $(date)"
        fi
        
        # Pull latest changes
        git reset --hard origin/main 2>&1 | tee -a "${LOG_FILE}"
        log "Repository updated successfully"
        
        # Trigger deployment if needed
        if [ -f "${LOCAL_PATH}/deploy.sh" ]; then
            log "Running deployment script..."
            cd "${LOCAL_PATH}"
            chmod +x deploy.sh
            ./deploy.sh 2>&1 | tee -a "${LOG_FILE}"
        fi
    fi
else
    log "Cloning PatchMate repository for the first time..."
    
    # Remove existing directory if it's not a git repo
    if [ -d "${LOCAL_PATH}" ]; then
        rm -rf "${LOCAL_PATH}"
    fi
    
    # Clone repository
    git clone "${REMOTE_URL}" "${LOCAL_PATH}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ -d "${LOCAL_PATH}" ]; then
        log "Repository cloned successfully"
        
        # Set up repository configuration
        cd "${LOCAL_PATH}"
        git config user.name "PatchMate Auto-Sync"
        git config user.email "sync@devinecreations.net"
        
        # Run initial setup if script exists
        if [ -f "${LOCAL_PATH}/setup.sh" ]; then
            log "Running initial setup script..."
            chmod +x setup.sh
            ./setup.sh 2>&1 | tee -a "${LOG_FILE}"
        fi
    else
        log "ERROR: Failed to clone repository"
        exit 1
    fi
fi

# Update file permissions for CopyParty access
log "Updating file permissions for CopyParty access..."
cd "${LOCAL_PATH}"

# Set ownership for patchmate user access
chown -R devinecr:devinecr "${LOCAL_PATH}"

# Set permissions: read/write for owner, read for group, no access for others
find "${LOCAL_PATH}" -type f -exec chmod 640 {} \;
find "${LOCAL_PATH}" -type d -exec chmod 750 {} \;

# Make scripts executable
find "${LOCAL_PATH}" -name "*.sh" -exec chmod 750 {} \;

# Update Matthew's auth keys if they exist in the repo
if [ -d "${LOCAL_PATH}/auth-keys" ]; then
    log "Updating Matthew's authentication keys..."
    if [ ! -d "${LOCAL_PATH}/matthew-auth-keys" ]; then
        mkdir -p "${LOCAL_PATH}/matthew-auth-keys"
    fi
    cp -r "${LOCAL_PATH}/auth-keys/"* "${LOCAL_PATH}/matthew-auth-keys/" 2>/dev/null || true
fi

# Create/update version info
VERSION_FILE="${LOCAL_PATH}/version.json"
LAST_COMMIT=$(cd "${LOCAL_PATH}" && git rev-parse HEAD)
LAST_COMMIT_DATE=$(cd "${LOCAL_PATH}" && git log -1 --format="%ai")
BRANCH=$(cd "${LOCAL_PATH}" && git branch --show-current)

cat > "${VERSION_FILE}" << EOF
{
  "version": "$(date +%Y.%m.%d.%H%M)",
  "commit": "${LAST_COMMIT}",
  "branch": "${BRANCH}",
  "sync_date": "$(date -Iseconds)",
  "last_commit_date": "${LAST_COMMIT_DATE}",
  "github_repo": "${GITHUB_USER}/${GITHUB_REPO}",
  "local_path": "${LOCAL_PATH}",
  "sync_status": "success"
}
EOF

log "Version information updated: ${VERSION_FILE}"

# Notify CopyParty of file changes (if running)
if pgrep -f "copyparty" > /dev/null; then
    log "Notifying CopyParty of file changes..."
    # Send SIGHUP to refresh file cache
    pkill -HUP -f "copyparty" 2>/dev/null || true
fi

# Create access documentation for this sync
SYNC_DOC="${LOCAL_PATH}/CURRENT_SYNC_STATUS.md"
cat > "${SYNC_DOC}" << EOF
# PatchMate Sync Status

## Latest Sync Information
- **Sync Date:** $(date)
- **Commit:** ${LAST_COMMIT}
- **Branch:** ${BRANCH}
- **Status:** Success

## Access Information
- **CopyParty URL:** https://files.devinecreations.net:3924/patchmate/
- **API Endpoint:** https://files.devinecreations.net:3924/patchmate/api/
- **OpenLink:** https://openlink.devinecreations.net/api/patchmate/

## Authentication
- **Username:** patchmate
- **Password:** patchmate-app-2025
- **GitHub Token:** ${GITHUB_TOKEN}

## File Locations
- **Local Path:** ${LOCAL_PATH}
- **Backup Path:** ${BACKUP_PATH}
- **Log File:** ${LOG_FILE}

Last updated: $(date)
EOF

log "PatchMate auto-sync completed successfully"
log "Access the latest version at: https://files.devinecreations.net:3924/patchmate/"

exit 0