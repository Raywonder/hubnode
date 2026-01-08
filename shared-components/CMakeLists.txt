# HubNode Shared Components CMake Configuration
cmake_minimum_required(VERSION 3.15)

project(HubNodeSharedComponents VERSION 1.0.0)

# Find JUCE
find_package(JUCE CONFIG REQUIRED)

# Create shared components library
add_library(HubNodeSharedComponents STATIC
    # Plugin hosting
    PluginHostManager.cpp
    PluginHostManager.h
    
    # UI Components  
    SonoDrawableButton.cpp
    SonoDrawableButton.h
    SonoChoiceButton.cpp
    SonoChoiceButton.h
    SonoTextButton.cpp
    SonoTextButton.h
    SonoCallOutBox.cpp
    SonoCallOutBox.h
    
    # Look and Feel
    SonoLookAndFeel.cpp
    SonoLookAndFeel.h
    SonoUtility.h
    
    # Audio Tools
    JitterBufferMeter.cpp
    JitterBufferMeter.h
    LatencyMeasurer.cpp
    LatencyMeasurer.h
    RunCumulantor.cpp
    RunCumulantor.h
    mtdm.cc
    mtdm.h
    
    # Effect Parameters
    EffectParams.cpp
    EffectParams.h
    
    # Generic Components
    GenericItemChooser.cpp
    GenericItemChooser.h
    
    # System utilities
    AutoUpdater.cpp
    AutoUpdater.h
    CrossPlatformUtils.h
)

# Link against JUCE modules
target_link_libraries(HubNodeSharedComponents PRIVATE
    juce::juce_audio_basics
    juce::juce_audio_devices
    juce::juce_audio_formats
    juce::juce_audio_processors
    juce::juce_gui_basics
    juce::juce_gui_extra
    juce::juce_core
    juce::juce_events
    juce::juce_graphics
    juce::juce_data_structures
)

# Set compile features
target_compile_features(HubNodeSharedComponents PRIVATE cxx_std_17)

# Include directories
target_include_directories(HubNodeSharedComponents PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Compiler definitions
target_compile_definitions(HubNodeSharedComponents PRIVATE
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_PLUGINHOST_VST3=1
    JUCE_PLUGINHOST_AU=1
)

# Platform-specific settings
if(WIN32)
    target_compile_definitions(HubNodeSharedComponents PRIVATE
        JUCE_PLUGINHOST_VST_LEGACY=1
    )
endif()

# Export target for other projects to use
install(TARGETS HubNodeSharedComponents
    EXPORT HubNodeSharedComponentsTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

# Export headers
install(FILES
    PluginHostManager.h
    SonoDrawableButton.h  
    SonoChoiceButton.h
    AutoUpdater.h
    CrossPlatformUtils.h
    DESTINATION include/HubNodeSharedComponents
)