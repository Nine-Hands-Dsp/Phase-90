# Outil hors plugin : compile le processeur + la fenetre de PHASE 90 sous Linux et exporte des captures PNG (apercu, notice)
#   cmake -B build-render -S tools/render -DJUCE_DIR=/chemin/vers/JUCE && cmake --build build-render -j4
#   build-render/Phase90Render_artefacts/Phase90Render <dossier de sortie>
cmake_minimum_required(VERSION 3.22)
project(Phase90Render VERSION 1.0.0)
set(CMAKE_CXX_STANDARD 17)
add_subdirectory(${JUCE_DIR} JUCE)
set(W ${CMAKE_CURRENT_SOURCE_DIR}/../..)
juce_add_binary_data(Phase90Assets SOURCES
  ${W}/background.png ${W}/ticks_core.png ${W}/ticks_glow.png ${W}/sync_core.png ${W}/sync_glow.png ${W}/fs_refl.png
  ${W}/knob_shadow.png ${W}/knob_crown.png ${W}/knob_cap.png ${W}/knob_marker.png ${W}/knob_highlight.png
  ${W}/Poppins-Regular.ttf ${W}/Poppins-Medium.ttf ${W}/Poppins-Bold.ttf ${W}/Poppins-Light.ttf ${W}/NineHandsLogoBlack.svg)
juce_add_console_app(Phase90Render PRODUCT_NAME "Phase90Render")
target_sources(Phase90Render PRIVATE main.cpp ${W}/PluginProcessor.cpp ${W}/PluginEditor.cpp)
target_include_directories(Phase90Render PRIVATE ${W})
target_compile_definitions(Phase90Render PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_ALSA=0 JUCE_JACK=0
  JUCE_USE_XRANDR=0 JUCE_USE_XINERAMA=0 JUCE_USE_XCURSOR=0 JUCE_USE_XSHM=0 JucePlugin_Name="Phase 90" JucePlugin_Build_VST3=0
  JucePlugin_VersionString="2.0.0" JUCE_STANDALONE_APPLICATION=1 JUCE_MODAL_LOOPS_PERMITTED=1)
target_link_libraries(Phase90Render PRIVATE Phase90Assets juce::juce_audio_utils juce::juce_recommended_config_flags)
