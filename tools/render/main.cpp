// Captures PNG de la fenetre reelle de Phase 90 (meme code que le plugin), pour l'apercu et la notice.
#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"
using namespace juce;

int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    const String out = argc > 1 ? argv[1] : ".";
    Phase90Processor proc;
    proc.prepareToPlay (48000.0, 256);
    std::unique_ptr<AudioProcessorEditor> ed (proc.createEditor());
    auto* pe = static_cast<Phase90Editor*> (ed.get());
    std::printf ("taille par defaut : %d x %d\n", ed->getWidth(), ed->getHeight());

    auto pump = [] (int n) { for (int i = 0; i < n; ++i) MessageManager::getInstance()->runDispatchLoopUntil (35); };
    auto set = [&] (const char* id, float v) { if (auto* p = proc.apvts.getParameter (id)) p->setValueNotifyingHost (p->convertTo0to1 (v)); };
    auto run = [&] (int blocks) { AudioBuffer<float> b (2, 256); MidiBuffer m; for (int i = 0; i < blocks; ++i) { b.clear(); proc.processBlock (b, m); } };
    auto save = [&] (const String& name, float scale)
    {
        auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, scale);
        File f (out + "/" + name + ".png"); f.deleteFile();
        FileOutputStream os (f); PNGImageFormat().writeImageToStream (img, os);
        std::printf ("%s (%d x %d)\n", f.getFullPathName().toRawUTF8(), img.getWidth(), img.getHeight());
    };
    // etat : preset, effet, synchro ; status = texte de la ligne d'etat (vide = barre de presets)
    auto state = [&] (int preset, bool on, int sync, int glowPc, const String& status)
    {
        proc.setCurrentProgram (preset);
        set ("on", on ? 1.f : 0.f); set ("syncdiv", (float) sync);
        pe->setGlowPercent (glowPc);
        run (40); pump (8);
        pe->flash (status, status.isNotEmpty() ? 60.0 : 0.0);
        pe->settleForCapture();
        pump (3);
    };

    pe->forceRenderScale (2.0f);
    state (0, true, 0, 100, {});
    save ("p9_default", 2.0f);

    // rendu exact de la pedale seule (1235 x 1800)
    pe->setWindowHeight (900);
    pe->forceRenderScale (2.0f);
    pump (8);
    const float ex = 1800.0f / (float) ed->getHeight();
    state (0, true, 0, 100, {});                             save ("p9_exact_on", ex);
    state (1, false, 0, 100, {});                            save ("p9_exact_bypass", ex);
    state (0, true, 1, 100, "Tempo sync  1/4 @ 120 BPM");    save ("p9_exact_sync", ex);
    state (0, true, 0, 100, "Speed  0.92 Hz");               save ("p9_exact_status", ex);
    state (0, true, 0, 25, {});                              save ("p9_glow_25", ex);
    state (0, true, 0, 50, {});                              save ("p9_glow_50", ex);
    state (0, true, 0, 75, {});                              save ("p9_glow_75", ex);
    pe->setGlowPercent (100);

    // grande resolution : fenetre a 150 % rendue en 2x
    pe->setWindowHeight (p9ui::heightMax);
    pe->forceRenderScale (2.0f);
    pump (8);
    state (0, true, 0, 100, {});                             save ("p9_hires_on", 2.0f);

    // menus clic droit (design Octopus, NineHandsMenu.h) : rendu hors ecran avec le meme LookAndFeel que le plugin
    {
        auto& lnf = pe->menuLookAndFeel();
        struct It { String text; bool sep = false, sub = false, ticked = false, active = true; };
        auto render = [&] (const String& name, const String& title, const String& subtitle, int ico, const std::vector<It>& items, int hiIndex)
        {
            NineHandsMenu::Header hd (lnf.f, ico, Colour (0xffff8a2a), title, subtitle);
            int w = 0, h = 0; hd.getIdealSize (w, h);
            const int border = lnf.getPopupMenuBorderSize();
            int totalH = border * 2 + h + 11, maxW = w;
            for (auto& it : items) { int iw, ih; lnf.getIdealPopupMenuItemSize (it.text, it.sep, 0, iw, ih); totalH += ih; maxW = jmax (maxW, iw + (it.sub ? 20 : 0)); }
            maxW += border * 2;
            Image img (Image::ARGB, maxW * 2, totalH * 2, true);
            Graphics g (img); g.addTransform (AffineTransform::scale (2.0f));
            lnf.drawPopupMenuBackground (g, maxW, totalH);
            int y = border;
            hd.setSize (maxW - border * 2, h);
            { Graphics::ScopedSaveState ss (g); g.setOrigin (border, y); hd.paint (g); }
            y += h;
            lnf.drawPopupMenuItem (g, { border, y, maxW - border * 2, 11 }, true, true, false, false, false, {}, {}, nullptr, nullptr); y += 11;
            for (size_t i = 0; i < items.size(); ++i)
            {
                const auto& it = items[i]; int iw, ih; lnf.getIdealPopupMenuItemSize (it.text, it.sep, 0, iw, ih);
                lnf.drawPopupMenuItem (g, { border, y, maxW - border * 2, ih }, it.sep, it.active, (int) i == hiIndex, it.ticked, it.sub, it.text, {}, nullptr, nullptr);
                y += ih;
            }
            File f (out + "/" + name + ".png"); f.deleteFile();
            FileOutputStream os (f); PNGImageFormat().writeImageToStream (img, os);
            std::printf ("%s\n", f.getFullPathName().toRawUTF8());
        };
        render ("p9_menu", "Phase 90", "Phaser  v2.0.0", NineHandsMenu::icoPedal,
                { { "Plugin size", false, true }, { "Glow (halo of the lights)", false, true }, { "", true },
                  { "Factory presets", false, true }, { "Load user preset", false, true }, { "Save user preset", false, true }, { "", true },
                  { "Settings", false, true }, { "MIDI", false, true }, { "", true },
                  { "Phase 90 v2.0.0  NINE HANDS | DSP", false, false, false, false } }, 1);
        render ("p9_menu_settings", "Settings", "Phase 90", NineHandsMenu::icoSettings,
                { { "Voicing: Script '74 (no R28, smooth)" }, { "Voicing: Block '77 (R28, more mids)", false, false, true }, { "", true },
                  { "Tempo sync (120.0 BPM)", false, true }, { "Stereo spread (right channel LFO inverted)" },
                  { "Speed ring pulses with the LFO", false, false, true } }, 3);
        std::vector<It> g;
        for (int pc : { 25, 50, 75, 100 })
            g.push_back ({ "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), false, false, pc == 100 });
        render ("p9_menu_glow", "Glow", "Halo of the lights", NineHandsMenu::icoGlow, g, 1);
        render ("p9_menu_knob", "Speed", "MIDI: not assigned", NineHandsMenu::icoKnob,
                { { "MIDI Learn: Speed" }, { "Clear MIDI: Speed", false, false, false, false }, { "", true },
                  { "Plugin size", false, true }, { "Glow (halo of the lights)", false, true } }, 0);
    }
    ed.reset();
    return 0;
}
