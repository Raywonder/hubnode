# Audio Portrait Distribution Center

## Current Version: v0.2.0

This directory contains the latest Audio Portrait application builds and distribution files accessible via CopyParty at `/audio-portrait-dist/`.

### Version Status

- **Current Version**: 0.2.0 (Released: September 27, 2025)
- **Previous Version**: 0.1.0 (Deprecated and removed)

### Available Downloads

**Ready for Upload - v0.2.0 Files:**
- `Audio Portrait-0.2.0.dmg` (119,800,372 bytes) - macOS Intel
- `Audio Portrait-0.2.0-arm64.dmg` (119,563,767 bytes) - macOS Apple Silicon
- `Audio Portrait Setup 0.2.0.exe` (198,293,530 bytes) - Windows Installer
- `Audio Portrait-0.2.0.AppImage` (~120MB) - Linux AppImage
- `audio-portrait_0.2.0_amd64.deb` (~84MB) - Linux Debian Package

### Release Notes - v0.2.0

**Enhanced Audio Features & Bug Fixes**

- Fixed ffplay detection and audio backend initialization
- Enhanced test sound playback with multiple fallback paths
- High-quality audio format support (16-32bit, 44.1-192kHz)
- Professional recording with pause/resume/playback
- Audio test integration with real-time monitoring
- Full transport controls for audio playback
- System event sounds throughout the application
- Audio conversion with FFmpeg support
- Welcome screen audio testing
- Comprehensive audio backend with VLC/ffplay support
- Support for professional formats: AIFF, DSD, APE, FLAC, etc.

### Directory Structure

```
/home/devinecr/apps/hubnode/api/audio-portrait/uploads/
├── README.md                           # This file
├── updates.json                        # Auto-updater configuration
├── COPYPARTY_CLIENT_SETUP.md          # CopyParty access instructions
├── audio-portrait-mac-build-complete.tar.gz  # Build artifacts
└── audio-portrait-mac-build-files.tar.gz     # Build artifacts
```

### CopyParty Access

**Web Interface**: https://files.raywonderis.me/audio-portrait-dist/

**Upload Method (Confirmed Working)**:
```bash
curl -k -u admin:hub-node-api-2024 -X PUT \
  --data-binary "@filename" \
  "https://files.raywonderis.me/audio-portrait-dist/filename"
```

**Access Credentials**:
- Username: `audioportrait`
- Password: `audio-portrait-api-2025`
- Admin Access: `admin` / `hub-node-api-2024`

### File Permissions

All files should have proper permissions set:
- Executable files (.exe, .dmg, .AppImage): `755`
- Archive files (.tar.gz, .zip): `644`
- Documentation (.md, .json): `644`

### Cleanup History

- **September 28, 2025**: Removed all v0.1.0 files (~970MB freed)
  - Audio Portrait 0.1.0.exe (189M)
  - Audio Portrait-0.1.0-arm64.dmg (114M)
  - Audio Portrait-0.1.0.dmg (114M)
  - Audio-Portrait-0.1.0-arm64.dmg (113M)
  - Audio-Portrait-0.1.0-intel.dmg (114M)
  - Audio-Portrait-Portable-0.1.0.exe (188M)
  - Audio-Portrait-Setup-0.1.0.exe (189M)

### Support

- **Developer**: devinecr@tappedin.fm
- **Server Status**: https://api.devinecreations.net/api/audio-portrait/health
- **CopyParty Documentation**: See COPYPARTY_CLIENT_SETUP.md

---

**Last Updated**: September 28, 2025
**Maintained By**: Devine Creations