#!/bin/bash
# CopyParty Cross-Directory Linking Setup
# Creates symbolic links to all app directories for unified access

set -e

HUBNODE_ROOT="/home/devinecr/apps/hubnode"
BACKEND_DIR="$HUBNODE_ROOT/backend"

echo "=== Setting up CopyParty Cross-Directory Links ==="
echo "HubNode root: $HUBNODE_ROOT"
echo "Backend directory: $BACKEND_DIR"

# Create linked directories structure
mkdir -p "$BACKEND_DIR/linked_apps"
mkdir -p "$BACKEND_DIR/shared_uploads"
mkdir -p "$BACKEND_DIR/shared_downloads"

# Link all user app directories
echo "Creating symbolic links to all app directories..."

# Devine's apps (UFM)
if [ -d "/home/devinecr/apps/ufm-macos" ]; then
    ln -sfn "/home/devinecr/apps/ufm-macos" "$BACKEND_DIR/linked_apps/ufm-macos"
    echo "✓ Linked: UFM (Universal File Manager)"
fi

# TappedIn's apps (PatchMate, BEMA Mobile)
if [ -d "/home/tappedin/apps/patchmate-macos" ]; then
    ln -sfn "/home/tappedin/apps/patchmate-macos" "$BACKEND_DIR/linked_apps/patchmate-macos"
    echo "✓ Linked: PatchMate"
fi

if [ -d "/home/tappedin/apps/bema-mobile" ]; then
    ln -sfn "/home/tappedin/apps/bema-mobile" "$BACKEND_DIR/linked_apps/bema-mobile"
    echo "✓ Linked: BEMA Mobile"
fi

# Dom's apps (SonoBus variants)
if [ -d "/home/dom/apps/sonobus-macos" ]; then
    ln -sfn "/home/dom/apps/sonobus-macos" "$BACKEND_DIR/linked_apps/sonobus-enhanced"
    echo "✓ Linked: SonoBus Enhanced"
fi

if [ -d "/home/dom/apps/sonobus-original" ]; then
    ln -sfn "/home/dom/apps/sonobus-original" "$BACKEND_DIR/linked_apps/sonobus-original"
    echo "✓ Linked: SonoBus Original"
fi

# Create shared upload directories for each app
echo "Creating shared upload/download directories..."

for app in ufm-macos patchmate-macos bema-mobile sonobus-enhanced sonobus-original; do
    mkdir -p "$BACKEND_DIR/shared_uploads/$app"
    mkdir -p "$BACKEND_DIR/shared_downloads/$app"
    echo "✓ Created shared directories for: $app"
done

# Create client access directories
mkdir -p "$BACKEND_DIR/client_access"
mkdir -p "$BACKEND_DIR/client_access/mac_clients"
mkdir -p "$BACKEND_DIR/client_access/windows_clients"
mkdir -p "$BACKEND_DIR/client_access/mobile_clients"

# Copy CopyParty client to each access directory
if [ -f "$HUBNODE_ROOT/clients/copyparty/copyparty-sfx.py" ]; then
    cp "$HUBNODE_ROOT/clients/copyparty/copyparty-sfx.py" "$BACKEND_DIR/client_access/mac_clients/"
    cp "$HUBNODE_ROOT/clients/copyparty/copyparty-sfx.py" "$BACKEND_DIR/client_access/windows_clients/"
    cp "$HUBNODE_ROOT/clients/copyparty/api-examples.py" "$BACKEND_DIR/client_access/mac_clients/"
    cp "$HUBNODE_ROOT/clients/copyparty/api-examples.py" "$BACKEND_DIR/client_access/windows_clients/"
    echo "✓ Copied CopyParty clients to access directories"
fi

# Set proper permissions
chown -R devinecr:devinecr "$BACKEND_DIR/linked_apps"
chown -R devinecr:devinecr "$BACKEND_DIR/shared_uploads"
chown -R devinecr:devinecr "$BACKEND_DIR/shared_downloads"
chown -R devinecr:devinecr "$BACKEND_DIR/client_access"

# Make shared directories writable by all app users
chmod -R 755 "$BACKEND_DIR/shared_uploads"
chmod -R 755 "$BACKEND_DIR/shared_downloads"

echo "=== Cross-linking setup complete! ==="
echo ""
echo "Directory structure:"
echo "  $BACKEND_DIR/linked_apps/          - Links to all app directories"
echo "  $BACKEND_DIR/shared_uploads/       - Shared upload directories by app"
echo "  $BACKEND_DIR/shared_downloads/     - Shared download directories by app"
echo "  $BACKEND_DIR/client_access/        - Client tools for Mac/Windows"
echo ""
echo "Linked applications:"
ls -la "$BACKEND_DIR/linked_apps/" | grep "^l"