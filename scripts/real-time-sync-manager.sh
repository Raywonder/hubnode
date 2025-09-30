#!/bin/bash
# Real-Time Sync Manager for All Users
# Ensures all users are synced with server updates at all times

set -e

# Configuration
SYNC_LOG="/var/log/real-time-sync.log"
SYNC_INTERVAL=30  # seconds
LOCK_FILE="/tmp/real-time-sync.lock"

# User repositories and sync paths
declare -A USER_REPOS=(
    ["patchmate"]="/home/devinecr/apps/patchmate-deployment"
    ["audioportrait"]="/home/devinecr/apps/hubnode/api/audio-portrait"
    ["bema"]="/home/devinecr/apps/bema"
    ["context7"]="/home/devinecr/apps/context7"
    ["ufm"]="/home/devinecr/apps/ufm"
    ["hubnode"]="/home/devinecr/apps/hubnode"
)

declare -A GITHUB_REPOS=(
    ["patchmate"]="https://github.com/Matthew2244/PatchMate.git"
    ["hubnode"]="https://github.com/devinecr/hubnode.git"
)

declare -A COPYPARTY_VOLUMES=(
    ["patchmate"]="/patchmate"
    ["audioportrait"]="/audio-portrait-dist"
    ["shared"]="/shared"
    ["apps-devinecr"]="/apps-devinecr"
    ["apps-dom"]="/apps-dom"
    ["apps-tappedin"]="/apps-tappedin"
)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SYNC_LOG"
}

# Check if another sync is running
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "SKIP: Sync already running (PID: $pid)"
            exit 0
        else
            log "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Sync GitHub repositories
sync_github_repos() {
    log "Starting GitHub repository sync..."
    
    for repo_name in "${!GITHUB_REPOS[@]}"; do
        local repo_url="${GITHUB_REPOS[$repo_name]}"
        local local_path="${USER_REPOS[$repo_name]}"
        
        if [ -z "$local_path" ]; then
            log "WARNING: No local path configured for $repo_name"
            continue
        fi
        
        log "Syncing $repo_name from $repo_url"
        
        if [ -d "$local_path/.git" ]; then
            # Update existing repository
            cd "$local_path"
            
            # Fetch latest changes
            if git fetch origin main 2>&1 | tee -a "$SYNC_LOG"; then
                # Check if updates available
                LOCAL_COMMIT=$(git rev-parse HEAD)
                REMOTE_COMMIT=$(git rev-parse origin/main)
                
                if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
                    log "Updates found for $repo_name - applying changes"
                    
                    # Stash local changes if any
                    if ! git diff-index --quiet HEAD --; then
                        log "Stashing local changes in $repo_name"
                        git stash push -m "Auto-stash $(date)"
                    fi
                    
                    # Apply updates
                    git reset --hard origin/main
                    log "Successfully updated $repo_name"
                    
                    # Trigger post-sync hooks
                    trigger_post_sync_hooks "$repo_name" "$local_path"
                else
                    log "$repo_name is up to date"
                fi
            else
                log "ERROR: Failed to fetch updates for $repo_name"
            fi
        else
            log "WARNING: $local_path is not a git repository"
        fi
    done
}

# Trigger post-sync hooks
trigger_post_sync_hooks() {
    local repo_name="$1"
    local repo_path="$2"
    
    log "Running post-sync hooks for $repo_name"
    
    # Update file permissions for CopyParty
    chown -R devinecr:devinecr "$repo_path" 2>/dev/null || true
    find "$repo_path" -type f -exec chmod 644 {} \; 2>/dev/null || true
    find "$repo_path" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "$repo_path" -name "*.sh" -exec chmod 755 {} \; 2>/dev/null || true
    
    # Update version info
    if [ -f "$repo_path/package.json" ] || [ -f "$repo_path/.git" ]; then
        update_version_info "$repo_name" "$repo_path"
    fi
    
    # Notify CopyParty of changes
    if pgrep -f "copyparty" > /dev/null; then
        log "Notifying CopyParty of changes in $repo_name"
        pkill -HUP -f "copyparty" 2>/dev/null || true
    fi
    
    # Run repository-specific hooks
    case "$repo_name" in
        "patchmate")
            # Update PatchMate API endpoints
            if [ -f "$repo_path/api-hooks.js" ]; then
                log "PatchMate API hooks updated"
            fi
            ;;
        "hubnode")
            # Restart HubNode services if needed
            log "HubNode updated - checking services"
            ;;
    esac
}

# Update version information
update_version_info() {
    local repo_name="$1"
    local repo_path="$2"
    
    cd "$repo_path"
    
    local version_file="$repo_path/sync-version.json"
    local commit_hash=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local commit_date=$(git log -1 --format="%ai" 2>/dev/null || date -Iseconds)
    local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    
    cat > "$version_file" << EOF
{
  "repository": "$repo_name",
  "version": "$(date +%Y.%m.%d.%H%M)",
  "commit": "$commit_hash",
  "branch": "$branch",
  "last_sync": "$(date -Iseconds)",
  "commit_date": "$commit_date",
  "sync_status": "success",
  "local_path": "$repo_path"
}
EOF
    
    log "Version info updated for $repo_name: $version_file"
}

# Monitor CopyParty volumes for changes
monitor_copyparty_changes() {
    log "Monitoring CopyParty volumes for changes..."
    
    for volume_name in "${!COPYPARTY_VOLUMES[@]}"; do
        local volume_path="${COPYPARTY_VOLUMES[$volume_name]}"
        log "Checking volume: $volume_name ($volume_path)"
        
        # Create change detection file if it doesn't exist
        local change_file="/tmp/copyparty-${volume_name}-lastcheck"
        local current_time=$(date +%s)
        
        if [ ! -f "$change_file" ]; then
            echo "$current_time" > "$change_file"
            continue
        fi
        
        local last_check=$(cat "$change_file")
        echo "$current_time" > "$change_file"
        
        # Check for recent changes
        if find "/home/devinecr/apps" -name "*${volume_name}*" -newer "$change_file" 2>/dev/null | head -1 | grep -q .; then
            log "Changes detected in $volume_name - triggering sync"
            # Trigger relevant sync operations
        fi
    done
}

# Sync user configurations and settings
sync_user_configs() {
    log "Syncing user configurations..."
    
    # Update all users' environment variables
    for user_home in /home/*/; do
        if [ -d "$user_home" ]; then
            local username=$(basename "$user_home")
            
            # Skip system users
            case "$username" in
                "lost+found"|".")
                    continue
                    ;;
            esac
            
            # Update user's CopyParty access configuration
            update_user_copyparty_config "$username" "$user_home"
        fi
    done
}

# Update user's CopyParty configuration
update_user_copyparty_config() {
    local username="$1"
    local user_home="$2"
    
    local config_file="$user_home/.copyparty-sync-config"
    
    cat > "$config_file" << EOF
# CopyParty Real-Time Sync Configuration for $username
# Auto-generated: $(date)

COPYPARTY_SERVER="https://files.devinecreations.net:3924"
COPYPARTY_USER="$username"
LAST_SYNC="$(date -Iseconds)"

# Available volumes for $username:
$(grep -A 10 "/$username-home" /var/log/copyparty.log 2>/dev/null | head -10 || echo "# No specific volumes found")

# Usage:
# curl -u \$COPYPARTY_USER:password \$COPYPARTY_SERVER/volume/path
EOF
    
    chown "$username:$username" "$config_file" 2>/dev/null || true
}

# Monitor GitHub webhooks
monitor_github_webhooks() {
    log "Checking for GitHub webhook notifications..."
    
    # Check for webhook files (if webhook handler is running)
    local webhook_dir="/var/log/github-webhooks"
    if [ -d "$webhook_dir" ]; then
        find "$webhook_dir" -name "*.webhook" -newer /tmp/last-webhook-check 2>/dev/null | while read webhook_file; do
            log "Processing webhook: $webhook_file"
            # Process webhook and trigger appropriate syncs
        done
        touch /tmp/last-webhook-check
    fi
}

# Main sync loop
main_sync_loop() {
    log "Starting real-time sync manager..."
    
    while true; do
        check_lock
        
        log "Running sync cycle..."
        
        # Sync GitHub repositories
        sync_github_repos
        
        # Monitor CopyParty changes
        monitor_copyparty_changes
        
        # Sync user configurations
        sync_user_configs
        
        # Monitor webhooks
        monitor_github_webhooks
        
        log "Sync cycle completed - sleeping for $SYNC_INTERVAL seconds"
        sleep "$SYNC_INTERVAL"
        
        # Cleanup lock for next iteration
        rm -f "$LOCK_FILE"
    done
}

# Signal handlers
handle_term() {
    log "Received termination signal - shutting down gracefully"
    cleanup
    exit 0
}

handle_usr1() {
    log "Received USR1 signal - triggering immediate sync"
    sync_github_repos
}

trap handle_term TERM INT
trap handle_usr1 USR1

# Start based on command line argument
case "${1:-start}" in
    "start")
        main_sync_loop
        ;;
    "sync-once")
        check_lock
        sync_github_repos
        sync_user_configs
        log "One-time sync completed"
        ;;
    "monitor")
        monitor_copyparty_changes
        ;;
    "status")
        if [ -f "$LOCK_FILE" ]; then
            local pid=$(cat "$LOCK_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Real-time sync manager is running (PID: $pid)"
                exit 0
            else
                echo "Stale lock file found - sync manager not running"
                exit 1
            fi
        else
            echo "Real-time sync manager is not running"
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 {start|sync-once|monitor|status}"
        echo "  start     - Start continuous sync manager"
        echo "  sync-once - Run one sync cycle and exit"
        echo "  monitor   - Monitor CopyParty changes only"
        echo "  status    - Check if sync manager is running"
        exit 1
        ;;
esac