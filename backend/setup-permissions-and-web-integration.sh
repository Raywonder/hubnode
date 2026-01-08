#!/bin/bash
# CopyParty Permissions & Web Integration Setup
# Configures proper user permissions and Composr API integration

set -e

echo "=== Setting up User Permissions & Web Integration ==="

# Define base directories
HUBNODE_ROOT="/home/devinecr/apps/hubnode"
SHARED_ROOT="/home/devinecr/shared"
DOM_WEB="/home/dom/public_html"
DEVINE_WEB="/home/devinecr/devinecreations.net"

# Create web integration directories
echo "Creating web integration directories..."

mkdir -p "$DOM_WEB/copyparty"
mkdir -p "$DOM_WEB/api"
mkdir -p "$DOM_WEB/uploads"
mkdir -p "$DOM_WEB/downloads"

mkdir -p "$DEVINE_WEB/copyparty"
mkdir -p "$DEVINE_WEB/api"
mkdir -p "$DEVINE_WEB/uploads"
mkdir -p "$DEVINE_WEB/downloads"

# Create user groups for proper permissions
echo "Setting up user groups..."

# Create copyparty group
groupadd -f copyparty
usermod -a -G copyparty devinecr
usermod -a -G copyparty tappedin
usermod -a -G copyparty dom

# Create web group
groupadd -f webusers
usermod -a -G webusers devinecr
usermod -a -G webusers dom

# Set proper ownership and permissions
echo "Configuring directory permissions..."

# HubNode backend - devinecr owns, copyparty group access
chown -R devinecr:copyparty "$HUBNODE_ROOT"
chmod -R 755 "$HUBNODE_ROOT"
chmod -R 775 "$HUBNODE_ROOT/backend/uploads"
chmod -R 775 "$HUBNODE_ROOT/backend/downloads"
chmod -R 775 "$HUBNODE_ROOT/backend/logs"

# Shared directories - devinecr owns, copyparty group read/write
chown -R devinecr:copyparty "$SHARED_ROOT"
chmod -R 755 "$SHARED_ROOT"
chmod -R 775 "$SHARED_ROOT/transfers"
chmod -R 775 "$SHARED_ROOT/platforms"
chmod -R 2775 "$SHARED_ROOT/sync"  # Set SGID for group inheritance

# Individual app directories - proper user ownership
chown -R devinecr:devinecr "/home/devinecr/apps/ufm-macos"
chown -R tappedin:tappedin "/home/tappedin/apps"
chown -R dom:dom "/home/dom/apps"

# Web directories - web group access
chown -R dom:webusers "$DOM_WEB"
chown -R devinecr:webusers "$DEVINE_WEB"
chmod -R 755 "$DOM_WEB"
chmod -R 755 "$DEVINE_WEB"
chmod -R 775 "$DOM_WEB/uploads"
chmod -R 775 "$DOM_WEB/downloads"
chmod -R 775 "$DEVINE_WEB/uploads"
chmod -R 775 "$DEVINE_WEB/downloads"

# Set ACLs for fine-grained permissions
echo "Setting up Access Control Lists (ACLs)..."

# Allow copyparty group to access all user directories
setfacl -R -m g:copyparty:rx /home/devinecr/apps
setfacl -R -m g:copyparty:rx /home/tappedin/apps
setfacl -R -m g:copyparty:rx /home/dom/apps

# Allow webusers group to access web directories
setfacl -R -m g:webusers:rwx "$DOM_WEB"
setfacl -R -m g:webusers:rwx "$DEVINE_WEB"

# Set default ACLs for new files
setfacl -R -d -m g:copyparty:rx /home/devinecr/apps
setfacl -R -d -m g:copyparty:rwx "$SHARED_ROOT"
setfacl -R -d -m g:webusers:rwx "$DOM_WEB"
setfacl -R -d -m g:webusers:rwx "$DEVINE_WEB"

echo "✅ Permissions configured successfully!"

# Create web integration symbolic links
echo "Creating web integration links..."

# Link shared directories to web accessible locations
ln -sfn "$SHARED_ROOT" "$DOM_WEB/copyparty/shared"
ln -sfn "$SHARED_ROOT" "$DEVINE_WEB/copyparty/shared"

# Link app directories
ln -sfn "/home/dom/apps" "$DOM_WEB/copyparty/apps"
ln -sfn "/home/devinecr/apps" "$DEVINE_WEB/copyparty/apps"

echo "✅ Web integration links created!"

echo ""
echo "Permission Summary:"
echo "=================="
echo "Groups created:"
echo "  - copyparty: devinecr, tappedin, dom"
echo "  - webusers: devinecr, dom"
echo ""
echo "Directory ownership:"
echo "  - /home/devinecr/apps/hubnode: devinecr:copyparty"
echo "  - /home/devinecr/shared: devinecr:copyparty"
echo "  - /home/dom/public_html: dom:webusers"
echo "  - /home/devinecr/devinecreations.net: devinecr:webusers"
echo ""
echo "Web accessible paths:"
echo "  - http://raywonderis.me/~dom/copyparty/"
echo "  - http://devinecreations.net/copyparty/"