# HubNode Shared Components

This directory contains reusable components extracted from various projects for use across the HubNode ecosystem.

## Components

### Audio Processing
- **PluginHostManager** - VST/AU plugin hosting and management system
  - `PluginHostManager.h/cpp` - Full-featured plugin host with chain management, bypass controls, and editor hosting
  - Features: Plugin scanning, loading, real-time processing, state management
  - Usage: Integrate into JUCE-based audio applications for VST/AU plugin support

### Audio Measurement & Analysis  
- **JitterBufferMeter** - Network jitter buffer monitoring
  - `JitterBufferMeter.h/cpp` - Real-time jitter buffer visualization
  - Features: Buffer level tracking, visual meter component

- **LatencyMeasurer** - Audio latency measurement tools
  - `LatencyMeasurer.h/cpp` - Round-trip latency measurement
  - Features: Ping-based latency testing, statistical analysis

- **RunCumulantor** - Running statistical analysis
  - `RunCumulantor.h/cpp` - Real-time statistical computations
  - Features: Mean, variance, standard deviation calculation

- **MTDM** - Multi-Tone Delay Measurement
  - `mtdm.h/cc` - Professional audio delay measurement
  - Features: High-precision delay measurement using multi-tone signals

### UI Components (JUCE-based with Accessibility)
- **SonoDrawableButton** - Enhanced drawable button with accessibility support
  - `SonoDrawableButton.h/cpp` - Custom drawable button with proper AccessibilityHandler
  - Features: Screen reader support, keyboard navigation, custom graphics

- **SonoChoiceButton** - Accessible choice/dropdown button
  - `SonoChoiceButton.h/cpp` - Dropdown button with accessibility announcements
  - Features: VoiceOver/screen reader support, keyboard navigation

- **SonoTextButton** - Accessible text button component
  - `SonoTextButton.h/cpp` - Enhanced text button with accessibility features
  - Features: Screen reader support, keyboard navigation

- **SonoCallOutBox** - Accessible callout/tooltip component
  - `SonoCallOutBox.h/cpp` - Enhanced callout box with proper ARIA support
  - Features: Screen reader announcements, keyboard navigation

- **GenericItemChooser** - Generic item selection component
  - `GenericItemChooser.h/cpp` - Flexible item picker with accessibility
  - Features: List/grid selection, keyboard navigation, screen reader support

### Look and Feel
- **SonoLookAndFeel** - Custom JUCE look and feel implementation
  - `SonoLookAndFeel.h/cpp` - Professional audio application styling
  - Features: Custom rendering, theming support, high DPI support

- **SonoUtility** - UI utility functions and helpers
  - `SonoUtility.h` - Common UI helper functions and utilities
  - Features: Color helpers, drawing utilities, layout helpers

### Effect Parameters
- **EffectParams** - Audio effect parameter management
  - `EffectParams.h/cpp` - Structured parameter handling for audio effects
  - Features: Parameter validation, automation, preset management

### System Utilities
- **CrossPlatformUtils** - Cross-platform system utilities
  - `CrossPlatformUtils.h` - Platform abstraction layer for system operations
  - Features: File operations, system info, platform-specific functionality

- **AutoUpdater** - Application auto-update system
  - `AutoUpdater.h/cpp` - Automatic update checking and installation
  - Features: Version checking, download management, update notifications

## Integration Notes

### Prerequisites
- JUCE framework (6.0+)
- For PluginHostManager: VST SDK (optional for VST2 support)

### Usage
1. Copy needed components to your project
2. Add to CMakeLists.txt or .jucer project file
3. Include appropriate headers
4. Link against JUCE modules:
   - juce_audio_processors
   - juce_gui_basics
   - juce_audio_devices (for PluginHostManager)

### Example Integration
```cpp
// Plugin hosting example
#include "PluginHostManager.h"

class MyAudioProcessor : public AudioProcessor {
    std::unique_ptr<PluginHostManager> pluginHost;
    
    void prepareToPlay(double sr, int samples) override {
        pluginHost = std::make_unique<PluginHostManager>();
        pluginHost->prepareToPlay(sr, samples);
    }
    
    void processBlock(AudioBuffer<float>& buffer, MidiBuffer& midi) override {
        pluginHost->processBlock(buffer, midi);
    }
};
```

## License
Components are derived from SonoBus (GPLv3-or-later WITH Appstore-exception).
See individual source files for specific licensing information.

## Contributing
When adding new components:
1. Ensure cross-platform compatibility
2. Include accessibility features for UI components  
3. Add comprehensive documentation
4. Test on multiple platforms/architectures