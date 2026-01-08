# Audio Portrait Client Integration

## Overview
Audio Portrait client integration with HubNode backend system, providing license management, auto-updates, and API monitoring capabilities.

## Architecture
- **Main Distribution**: `/home/devinecr/apps/hubnode/api/audio-portrait/uploads/`
- **Client Monitor**: `/home/devinecr/apps/hubnode/clients/audio-portrait/`
- **Public Downloads**: `https://devinecreations.net/uploads/audio-portrait/`
- **API Endpoints**: `https://api.devinecreations.net/api/audio-portrait/`

## Download Links
- **Universal Mac DMG**: [Audio Portrait-0.1.0.dmg](https://api.devinecreations.net/api/audio-portrait/download/mac)
- **ARM64 Mac DMG**: [Audio Portrait-0.1.0-arm64.dmg](https://api.devinecreations.net/api/audio-portrait/download/mac-arm64)
- **Windows EXE**: [Audio Portrait 0.1.0.exe](https://api.devinecreations.net/api/audio-portrait/download/windows)

## Integration Features
✅ UFM License Manager integration  
✅ Auto-update system with API endpoints  
✅ CopyParty file access integration  
✅ API monitoring and health checks  
✅ Multi-platform builds (Mac Universal/ARM64, Windows)  

## API Monitor Integration
The Audio Portrait client can be monitored using the existing API Monitor system:
- **Health endpoint**: `https://api.devinecreations.net/api/audio-portrait/health`
- **Version endpoint**: `https://api.devinecreations.net/api/audio-portrait/version`
- **License validation**: `https://api.devinecreations.net/api/audio-portrait/license/validate`

## Composr Downloads Integration
Files are automatically synced to Composr downloads system at:
- **Main downloads**: `https://devinecreations.net/uploads/audio-portrait/`
- **Backup mirror**: `https://files.devinecreations.net/audio-portrait/`