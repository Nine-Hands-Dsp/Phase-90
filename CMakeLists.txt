cmake_minimum_required(VERSION 3.22)

# macOS : un seul binaire universel (Apple Silicon + Intel)
set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "")
set(CMAKE_OSX_DEPLOYMENT_TARGET "10.13" CACHE STRING "")

project(Phase90 VERSION 2.1.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(PHASE90_STANDALONE "Compile aussi une application autonome (test sans DAW)" OFF)

# Compilation locale avec un JUCE déjà présent :  cmake -B build -DJUCE_DIR=/chemin/vers/JUCE
if(DEFINED JUCE_DIR)
  add_subdirectory(${JUCE_DIR} juce)
else()
  include(FetchContent)
  FetchContent_Declare(JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG        8.0.15
    GIT_SHALLOW    ON)
  FetchContent_MakeAvailable(JUCE)
endif()

if(PHASE90_STANDALONE)
  set(PHASE90_FORMATS VST3 Standalone)
else()
  set(PHASE90_FORMATS VST3)
endif()

# visuel, calques lumineux, potard (calques nh::Knob), polices Poppins et logo integres au plugin
juce_add_binary_data(Phase90Assets SOURCES
  background.png
  ticks_core.png
  ticks_glow.png
  sync_core.png
  sync_glow.png
  fs_refl.png
  knob_shadow.png
  knob_crown.png
  knob_cap.png
  knob_marker.png
  knob_highlight.png
  Poppins-Regular.ttf
  Poppins-Medium.ttf
  Poppins-Bold.ttf
  Poppins-Light.ttf
  NineHandsLogoBlack.svg)

juce_add_plugin(Phase90
  COMPANY_NAME               "NINE HANDS | DSP"
  PLUGIN_MANUFACTURER_CODE   Wiga
  PLUGIN_CODE                Ph90
  FORMATS                    ${PHASE90_FORMATS}
  VST3_CATEGORIES            Fx Modulation
  BUNDLE_ID                  com.studiowiga.phase90
  IS_SYNTH                   FALSE
  NEEDS_MIDI_INPUT           TRUE
  NEEDS_MIDI_OUTPUT          FALSE
  IS_MIDI_EFFECT             FALSE
  EDITOR_WANTS_KEYBOARD_FOCUS FALSE
  PRODUCT_NAME               "Phase 90"
  COPY_PLUGIN_AFTER_BUILD    FALSE)

target_sources(Phase90 PRIVATE
  PluginProcessor.cpp
  PluginEditor.cpp)


# verrou de taille de la fenetre du DAW (jamais sous 60 %, jamais au-dela de 150 %)
if(APPLE)
  target_sources(Phase90 PRIVATE WindowMinSize.mm)
  target_link_libraries(Phase90 PRIVATE "-framework Cocoa")
else()
  target_sources(Phase90 PRIVATE WindowMinSize.cpp)
endif()
if(WIN32)
  target_link_libraries(Phase90 PRIVATE comctl32 user32)
endif()
if(MSVC)
  target_compile_options(Phase90 PRIVATE /utf-8)
endif()

target_compile_definitions(Phase90 PUBLIC
  JUCE_WEB_BROWSER=0
  JUCE_USE_CURL=0
  JUCE_VST3_CAN_REPLACE_VST2=0
  JUCE_DISPLAY_SPLASH_SCREEN=0
  JUCE_REPORT_APP_USAGE=0)

target_link_libraries(Phase90
  PRIVATE
    Phase90Assets
    juce::juce_audio_utils
  PUBLIC
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
    juce::juce_recommended_warning_flags)
