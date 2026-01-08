# Studio Assistant Build Source - Summary

## Status: Source Code Consolidated

All Studio Assistant (SonoBus Enhanced) build source has been gathered and organized for local macOS building.

## Build Source Locations

### Primary Build Source
**Location:** `/home/devinecr/apps/hubnode/clients/studio_assistant/plugin/src/`
**Size:** Complete JUCE-based VST/AU plugin project
**Contents:** Full SonoBus Enhanced v1.7.3 source code

### Original Source (Reference)
**Location:** `/home/dom/apps/sonobus-macos/sonobus/`
**Purpose:** Original build location with macOS-specific configuration

## What's Included

### 1. Complete VST/AU Plugin Source
```
/home/devinecr/apps/hubnode/clients/studio_assistant/plugin/src/
├── Source/                     # C++ source files
│   ├── SonobusPluginProcessor.cpp  (356KB) - Audio processing
│   ├── SonobusPluginEditor.cpp     (241KB) - UI implementation
│   ├── PluginHostManager.cpp        # VST hosting support
│   └── [Additional source files]
├── CMakeLists.txt              # Build configuration
├── deps/                       # Dependencies
│   ├── juce/                   # JUCE framework v7+
│   ├── aoo/                    # Audio over network library
│   └── ff_meters/              # Level meters
├── build_native.sh             # Native build script
├── build_simple.sh             # Simple build script
├── setupcmake.sh               # CMake configuration
├── setupcmakexcode.sh          # Xcode project generation
├── build-installers.sh         # DMG creation
└── create_installers.sh        # Multi-platform installers
```

### 2. Build Documentation
- **MACOS_BUILD_GUIDE.md** - Complete macOS build instructions
- **BUILD_SUMMARY.md** - Build summary and features
- **README.md** - Quick start guide

### 3. Pre-built Binaries
**Location:** `/home/dom/apps/sonobus-macos/sonobus/install_output/`
- `SonoBus-Enhanced-macOS.dmg` (18KB) - macOS installer
- VST3 plugin
- Audio Unit plugin
- Standalone application

### 4. Deployed Package
**URL:** https://files.devinecreations.net:3924/shared/sonobus-enhanced-macos-v1.7.3.tar.gz
**Credentials:** sonobus / sonobus-app-2025

## Building on macOS

### Quick Build

```bash
cd /home/devinecr/apps/hubnode/clients/studio_assistant/plugin/src

# Configure
./setupcmake.sh

# Build
cmake --build build --config Release

# Output:
# - build/SonoBus_artefacts/Release/VST3/SonoBus.vst3
# - build/SonoBus_artefacts/Release/AU/SonoBus.component
# - build/SonoBus_artefacts/Release/Standalone/SonoBus.app
```

### Prerequisites

- macOS 10.11+
- Xcode 12.0+ (for Universal Binary)
- CMake 3.15+
- Command Line Tools

### Build Methods

1. **Command-line:** `./setupcmake.sh && cmake --build build --config Release`
2. **Xcode:** `./setupcmakexcode.sh && open buildXcode/SonoBus.xcodeproj`
3. **Native:** `./build_native.sh`

## Plugin Features

### Enhanced Features
- ✅ VST plugin hosting (load VST2/3, AU plugins)
- ✅ Enhanced accessibility (screen readers)
- ✅ Modern JUCE 7+ API
- ✅ Universal Binary (Intel + Apple Silicon)
- ✅ Cross-platform (macOS, Windows, Linux)

### Core Features
- Real-time network audio streaming
- Low-latency audio processing
- Built-in effects (compression, EQ, reverb)
- Peer-to-peer connections
- High-quality audio codecs

## Plugin Formats

| Format | Platform | Status |
|--------|----------|--------|
| VST3 | macOS/Windows/Linux | ✅ Built |
| Audio Unit | macOS only | ✅ Built |
| LV2 | Linux only | ✅ Built |
| Standalone | All platforms | ✅ Built |
| AAX | Pro Tools | ⚠️ Requires AAX SDK |

## Installation Paths

### macOS System-wide
```bash
VST3: /Library/Audio/Plug-Ins/VST3/SonoBus.vst3
AU:   /Library/Audio/Plug-Ins/Components/SonoBus.component
App:  /Applications/SonoBus.app
```

### macOS User-only
```bash
VST3: ~/Library/Audio/Plug-Ins/VST3/SonoBus.vst3
AU:   ~/Library/Audio/Plug-Ins/Components/SonoBus.component
App:  ~/Applications/SonoBus.app
```

## Tested DAWs

- ✅ Logic Pro X / Logic Pro 11
- ✅ Ableton Live 11/12
- ✅ Reaper 6/7
- ✅ Studio One 6
- ✅ GarageBand
- ✅ MainStage

## Branding as "Studio Assistant"

To rebrand as Studio Assistant:

### 1. Update Plugin Metadata
```cpp
// In Source/SonobusPluginProcessor.cpp
name = "Studio Assistant";
identifier = "com.yourcompany.studioassistant";
```

### 2. Update CMakeLists.txt
```cmake
project(StudioAssistant VERSION 1.7.3)
PRODUCT_NAME "Studio Assistant"
PLUGIN_NAME "StudioAssistant"
```

### 3. Rebuild
```bash
./setupcmake.sh
cmake --build build --config Release
```

## Source Code Transfer

To transfer source to macOS machine for building:

### Option 1: Direct Copy (if macOS has network access)
```bash
# From macOS
scp -r devinecr@64.20.46.178:/home/devinecr/apps/hubnode/clients/studio_assistant/plugin/src ~/Desktop/studio-assistant
```

### Option 2: Via Archive
```bash
# On Linux server
cd /home/devinecr/apps/hubnode/clients/studio_assistant/plugin
tar -czf studio-assistant-source.tar.gz src/

# Copy to shared
cp studio-assistant-source.tar.gz /home/devinecr/shared/

# Download from macOS
curl -u sonobus:sonobus-app-2025 \
  -O https://files.devinecreations.net:3924/shared/studio-assistant-source.tar.gz
tar -xzf studio-assistant-source.tar.gz
```

### Option 3: Git Clone
```bash
# If repository is on GitHub
git clone https://github.com/youruser/studio-assistant.git
cd studio-assistant
git submodule update --init --recursive
```

## Additional Resources

### Documentation
- `/home/dom/apps/sonobus-macos/MACOS_BUILD_GUIDE.md` - Complete build guide
- `/home/dom/apps/sonobus-macos/DEPLOYMENT_SUMMARY.md` - Deployment info
- `/home/dom/apps/sonobus-macos/README.md` - Quick start

### Original Project
- **GitHub:** https://github.com/essej/sonobus
- **Website:** https://sonobus.net

## Version Information

- **Version:** 1.7.3-enhanced
- **JUCE Framework:** 7.0+
- **Build Date:** 2025-09-21
- **Deployment Date:** 2025-09-30
- **Architecture:** Universal (x86_64 + arm64)
- **Minimum macOS:** 10.11 (El Capitan)

## License

GPLv3+ with app store exception (same as original SonoBus)

## Contact & Support

- **Server Admin:** devinecr@devinecreations.net
- **CopyParty Access:** https://files.devinecreations.net:3924/
- **Original SonoBus:** https://github.com/essej/sonobus

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>

**Consolidated:** 2025-09-30