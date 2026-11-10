#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include "Layout.h"
#include "NineHandsMenu.h"
#include "NHKnob.h"

//==============================================================================
// PHASE 90 v2 (NINE HANDS | DSP) : pedale simple, fond 1235 x 1800 px plein cadre (repere 617,5 x 900, Layout.h).
// Le fond (tools/make_art.py, d'apres le visuel de l'utilisateur) contient boitier, panneau, lentilles eteintes,
// footswitch, bouton SYNC et jacks (pieces photo du kit). L'editeur dessine par-dessus : lumieres (sources + halos
// doses par le reglage Glow), anneau du footswitch (dessin d'Octopus), serigraphie vectorielle (Poppins), logo
// NINE HANDS | DSP (SVG officiel v003 noir), pastille presets / ligne d'etat ; le potard SPEED est un composant nh::Knob (calques qui tournent ensemble, flou de mouvement).
//==============================================================================
class Phase90Editor : public juce::AudioProcessorEditor,
                      private juce::Timer
{
public:
    explicit Phase90Editor (Phase90Processor&);
    ~Phase90Editor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;

    void mouseDown (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseDoubleClick (const juce::MouseEvent&) override {}
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;

    static constexpr float baseW = layout::frameW, baseH = layout::frameH;
    static int sizeHeight (int idx) { return p9ui::sizeHeights[juce::jlimit (0, p9ui::numSizes - 1, idx)]; }
    void setWindowHeight (int h);
    // outil de rendu (captures) : echelle forcee, etat lumineux immediat
    void forceRenderScale (float sc) { forcedScale = sc; rebuildCaches (sc); }
    void settleForCapture();
    void setGlowPercent (int pc);
    void flash (const juce::String& text, double seconds = 2.5);
    void showContextMenu (int learnIdx = -1);
    NineHandsMenu::MenuLnf& menuLookAndFeel() { return menuLnf; }

private:
    void timerCallback() override;
    void visibilityChanged() override;
    void useSoftwareRenderer();
    float physicalScale() const;
    void askRepaint (juce::Rectangle<float> unitsRect);
    void rebuildCaches (float sc = 0.0f);
    float k() const { return (float) getHeight() / baseH; }
    juce::Point<float> toUnits (juce::Point<float> p) const { return p / k(); }

    enum class Hit { none, phase, sync, foot, presetPrev, presetName, presetNext };
    Hit hitAt (juce::Point<float> u) const;

    void setParam (const juce::String& id, float plain);
    juce::String speedText() const;
    juce::String presetLine() const;
    void stepPreset (int delta);
    void showPresetMenu();
    void askUserPresetName (int slot);
    void buildPrint();

    void drawLights (juce::Graphics&);
    void drawFootRing (juce::Graphics&);
    void drawPrint (juce::Graphics&);
    void drawBar (juce::Graphics&);

    Phase90Processor& proc;
    NineHandsMenu::MenuLnf menuLnf;
    juce::Typeface::Ptr mediumFace, boldFace, lightFace, regularFace;
    std::unique_ptr<juce::Drawable> logo;
    juce::Path speedPath, darkPath, phasePath, ticksPath;      // serigraphie (unites du plugin)
    juce::Path syncLabels[Phase90Processor::numSyncStates];    // "SYNC", "SYNC 1/4", "SYNC 1/8", "SYNC 1/2"
    juce::Rectangle<float> syncHit;
    std::unique_ptr<nh::Knob> knob;

    juce::Image background, bgScaled, ticksCore, ticksGlow, syncCore, syncGlow, fsRefl;
    int cacheW = 0, cacheH = 0;
    float cacheScale = 0.0f, forcedScale = 0.0f;
    int resizeSettle = 0, openHeight = 0;
    void* lastPeer = nullptr;
    double lastPaintMs = 0.0, repaintAskedMs = 0.0, lastScaleCheckMs = 0.0, lastRendererCheckMs = 0.0, lastGlowReadMs = 0.0;

    // etat affiche
    float glow = 1.0f;                              // reglage Glow (1 = 100 %)
    float tickLevel = 1.0f, footLevel = 1.0f, syncLevel = 0.0f;
    bool footDown = false;
    Hit hover = Hit::none;

    // pastille unique : barre de presets au repos, ligne d'etat pendant les reglages (fondu croise)
    juce::String statusText, presetText;
    double statusUntil = 0.0;
    float statusAlpha = 0.0f;
    float lastSpeed = -1.0f; bool lastBlock = false, lastOn = false; int lastSync = 0;
    int lastPresetCounter = 0;

    // dernier etat dessine (on ne redessine une zone que si elle a change)
    float dTick = -1.0f, dFoot = -1.0f, dSync = -1.0f, dStatus = -1.0f;
    int dSyncState = -1;
    bool dFootDown = false;
    Hit dHover = Hit::none;
    juce::String dStatusText, dPresetText;

    std::unique_ptr<juce::AlertWindow> nameDialog;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (Phase90Editor)
};
