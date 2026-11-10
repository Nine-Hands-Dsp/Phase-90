#include "PluginEditor.h"
#include "BinaryData.h"
#include "WigaWindowSize.h"
#include "NineHandsGlow.h"

using namespace juce;

namespace
{
    const Colour inkLight (0xffd4d4d8);            // SPEED, petites graduations, SYNC (panneau noir)
    const Colour inkDark (0xff180a04);             // OUTPUT, INPUT, 90 (sur l'orange)
    const Colour phaseOrange (0xffec701c);         // PHASE, en relief dans le cartouche
    const Colour ringOrange (0xffff8024), ringCoreCol (0xffffd6a0);   // anneau du footswitch (dessin d'Octopus)
    const Colour syncLit (0xffff963c);
    const Colour barFill (0xff0a0a0b), barEdge (0xff606064), barInk (0xffe8e8ec);
    const Colour menuAccent (0xffff8a2a);          // pastille des en-tetes de menu (orange de la pedale)
    constexpr float arrowW = 34.0f;
}

static Image png (const void* d, int n) { return ImageCache::getFromMemory (d, n); }

//==============================================================================
Phase90Editor::Phase90Editor (Phase90Processor& p)
    : AudioProcessorEditor (p), proc (p)
{
    background = png (BinaryData::background_png, BinaryData::background_pngSize);
    ticksCore  = png (BinaryData::ticks_core_png, BinaryData::ticks_core_pngSize);
    ticksGlow  = png (BinaryData::ticks_glow_png, BinaryData::ticks_glow_pngSize);
    syncCore   = png (BinaryData::sync_core_png, BinaryData::sync_core_pngSize);
    syncGlow   = png (BinaryData::sync_glow_png, BinaryData::sync_glow_pngSize);
    fsRefl     = png (BinaryData::fs_refl_png, BinaryData::fs_refl_pngSize);
    mediumFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace    = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    lightFace   = Typeface::createSystemTypefaceFor (BinaryData::PoppinsLight_ttf, BinaryData::PoppinsLight_ttfSize);
    regularFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    menuLnf.f = { regularFace, mediumFace, boldFace };
    // logo officiel NINE HANDS | DSP v003, version noire (facade orange)
    if (auto xml = XmlDocument::parse (String::fromUTF8 (BinaryData::NineHandsLogoBlack_svg, BinaryData::NineHandsLogoBlack_svgSize)))
        logo = Drawable::createFromSVG (*xml);
    buildPrint();
    glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;

    // potard SPEED : calques qui tournent ensemble avec flou de mouvement (lumiere en haut a gauche a 45 deg)
    {
        nh::Knob::Layers L;
        L.shadow    = png (BinaryData::knob_shadow_png, BinaryData::knob_shadow_pngSize);
        L.crown     = png (BinaryData::knob_crown_png, BinaryData::knob_crown_pngSize);
        L.cap       = png (BinaryData::knob_cap_png, BinaryData::knob_cap_pngSize);
        L.marker    = png (BinaryData::knob_marker_png, BinaryData::knob_marker_pngSize);
        L.highlight = png (BinaryData::knob_highlight_png, BinaryData::knob_highlight_pngSize);
        nh::Knob::Style st;
        st.startAngle = degreesToRadians (-150.0f);            // graduations de la serigraphie : +/- 150 deg
        st.endAngle   = degreesToRadians ( 150.0f);
        st.dragPixels = 400.0f;                                // course complete = 400 px de souris (v1.1.1)
        knob = std::make_unique<nh::Knob> (*proc.apvts.getParameter ("speed"), std::move (L), st);
        knob->onRightClick = [this] (const MouseEvent&) { showContextMenu (1); };
        addAndMakeVisible (*knob);
    }

    // taille : 493 px par defaut (« 60 % ») = taille minimale, proportions bloquees
    const double aspect = (double) baseW / (double) baseH;
    const int saved = proc.uiHeight.load();
    const int h0 = saved > 0 ? jlimit (p9ui::heightDefault, p9ui::heightMax, saved)
                             : sizeHeight (WigaWindowSize::defaultIndex (JucePlugin_Name, p9ui::numSizes));
    setResizable (true, true);
    setResizeLimits (roundToInt (p9ui::heightDefault * aspect), p9ui::heightDefault,
                     roundToInt (p9ui::heightMax * aspect), p9ui::heightMax);
    getConstrainer()->setFixedAspectRatio (aspect);
    setOpaque (true);
    openHeight = h0;
    setSize (roundToInt (h0 * aspect), h0);
    rebuildCaches();

    const bool on = proc.isOn();
    tickLevel = footLevel = on ? 1.0f : 0.0f;
    syncLevel = proc.syncState() > 0 ? 1.0f : 0.0f;
    lastSpeed = proc.getSpeed(); lastBlock = proc.isBlock(); lastOn = on; lastSync = proc.syncState();
    lastPresetCounter = proc.presetCounter.load();
    presetText = presetLine();
    startTimerHz (30);
}

Phase90Editor::~Phase90Editor()
{
    PopupMenu::dismissAllActiveMenus();
    stopTimer();
}

//==============================================================================
// Anti-gel v2 (NINE HANDS | DSP) : moteur logiciel sous Windows, caches refaits par le timer seulement,
// chien de garde des redessins, aucun appel a l'hote depuis le thread audio (voir PluginProcessor).
void Phase90Editor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer != lastPeer) { lastPeer = peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw)
            peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void Phase90Editor::parentHierarchyChanged() { useSoftwareRenderer(); }
void Phase90Editor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

float Phase90Editor::physicalScale() const
{
    if (forcedScale > 0.0f) return forcedScale;
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

void Phase90Editor::askRepaint (Rectangle<float> u)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (u.transformedBy (AffineTransform::scale (k())).getSmallestIntegerContainer().expanded (2));
}

void Phase90Editor::resized()
{
    // jamais de setSize ici ; taille de l'instance enregistree seulement si elle a ete changee
    if (proc.uiHeight.load() > 0 || (openHeight > 0 && std::abs (getHeight() - openHeight) > 2))
        proc.uiHeight.store (jlimit (p9ui::heightDefault, p9ui::heightMax, getHeight()));
    if (knob != nullptr)
        knob->setBounds (layout::knobBox.transformedBy (AffineTransform::scale (k())).toNearestInt());
    resizeSettle = 4;
}

void Phase90Editor::setWindowHeight (int h)
{
    h = jlimit (p9ui::heightDefault, p9ui::heightMax, h);
    setSize (roundToInt ((double) h * baseW / baseH), h);
}

void Phase90Editor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;
    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    bgScaled = (pw >= background.getWidth()) ? background : background.rescaled (pw, ph, Graphics::highResamplingQuality);
    repaint();
}

void Phase90Editor::setGlowPercent (int pc)
{
    NineHandsGlow::setPercent (JucePlugin_Name, pc);
    glow = (float) jlimit (25, 100, pc) / 100.0f;
    repaint();
}

void Phase90Editor::settleForCapture()
{
    const bool on = proc.isOn();
    const bool follow = proc.apvts.getRawParameterValue ("ticklfo")->load() > 0.5f;
    tickLevel = on ? (follow ? 0.40f + 0.60f * (1.0f - proc.lfoVisual.load()) : 1.0f) : 0.0f;
    footLevel = on ? 1.0f : 0.0f;
    syncLevel = proc.syncState() > 0 ? 1.0f : 0.0f;
    presetText = presetLine();
    statusAlpha = Time::getMillisecondCounterHiRes() < statusUntil ? 1.0f : 0.0f;
    repaint();
}

//==============================================================================
// Serigraphie vectorielle (Layout.h) : construite une fois en chemins (unites du plugin).
// Chaque texte est centre sur (x, y) = milieu de ses capitales, avec l'approche (track) entre les lettres.
//==============================================================================
static Path textPath (const String& s, const Typeface::Ptr& face, float capH, float track, float x, float y, float rot)
{
    float capRatio = 0.7f;
    {
        GlyphArrangement h; h.addLineOfText (Font (FontOptions (face).withHeight (100.0f)), "H", 0.0f, 0.0f);
        Path hp; h.createPath (hp);
        if (hp.getBounds().getHeight() > 1.0f) capRatio = hp.getBounds().getHeight() / 100.0f;
    }
    const Font font (FontOptions (face).withHeight (capH / capRatio));
    float total = 0.0f;
    for (int i = 0; i < s.length(); ++i)
        total += GlyphArrangement::getStringWidth (font, String::charToString (s[i])) + (i > 0 ? track : 0.0f);
    GlyphArrangement ga;
    float cx = -total * 0.5f;
    for (int i = 0; i < s.length(); ++i)
    {
        const String ch = String::charToString (s[i]);
        ga.addLineOfText (font, ch, cx, capH * 0.5f);        // ligne de base : capitales centrees sur 0
        cx += GlyphArrangement::getStringWidth (font, ch) + track;
    }
    Path p; ga.createPath (p);
    p.applyTransform (AffineTransform::rotation (rot * MathConstants<float>::pi / 180.0f).translated (x, y));
    return p;
}

void Phase90Editor::buildPrint()
{
    speedPath.clear(); darkPath.clear(); phasePath.clear(); ticksPath.clear();
    auto faceOf = [this] (int f) { return f == 1 ? boldFace : f == 2 ? lightFace : f == 3 ? regularFace : mediumFace; };
    for (const auto& t : layout::texts)
    {
        const String s (t.s);
        const auto p = textPath (s, faceOf (t.font), t.capH, t.track, t.x, t.y, t.rot);
        if (s == "SPEED")      speedPath.addPath (p);
        else if (s == "PHASE") phasePath = p;
        else                   darkPath.addPath (p);
    }
    for (const auto& tk : layout::ticks)
    {
        Path seg; seg.startNewSubPath (tk.x0, tk.y0); seg.lineTo (tk.x1, tk.y1);
        Path stroked;
        PathStrokeType (tk.w, PathStrokeType::curved, PathStrokeType::rounded).createStrokedPath (stroked, seg);
        ticksPath.addPath (stroked);
    }
    syncHit = Rectangle<float> (layout::syncPos.x - layout::syncR, layout::syncPos.y - layout::syncR, layout::syncR * 2.0f, layout::syncR * 2.0f);
    for (int i = 0; i < Phase90Processor::numSyncStates; ++i)
    {
        const String s = i == 0 ? String ("SYNC") : "SYNC " + Phase90Processor::syncDivisionName (i);
        syncLabels[i] = textPath (s, regularFace, layout::syncLabelCapH, 1.0f, layout::syncLabelPos.x, layout::syncLabelPos.y, 0.0f);
        syncHit = syncHit.getUnion (syncLabels[i].getBounds().expanded (4.0f, 5.0f));
    }
}

//==============================================================================
String Phase90Editor::speedText() const
{
    if (proc.syncState() > 0)
        return "Sync " + Phase90Processor::syncDivisionName (proc.syncState()) + " @ " + String (roundToInt (proc.hostBpm.load())) + " BPM";
    const double hz = proc.speedHz();
    return String (hz, hz < 1.0 ? 2 : 1) + " Hz";
}

String Phase90Editor::presetLine() const
{
    return proc.presetName.isNotEmpty() ? proc.presetName : String ("Edited");
}

void Phase90Editor::flash (const String& t, double seconds)
{
    statusText = t;
    statusUntil = Time::getMillisecondCounterHiRes() + seconds * 1000.0;
}

void Phase90Editor::setParam (const String& id, float plain)
{
    if (auto* p = proc.apvts.getParameter (id))
    {
        p->beginChangeGesture();
        p->setValueNotifyingHost (p->convertTo0to1 (plain));
        p->endChangeGesture();
    }
}

//==============================================================================
void Phase90Editor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }
    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches();
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }
    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0; lastPeer = nullptr;
        useSoftwareRenderer(); repaint();
    }

    // ---- reglages qui changent (souris, automation, MIDI) -> ligne d'etat ; chargement de preset -> barre seulement
    const float sp = proc.getSpeed();
    const bool block = proc.isBlock(), on = proc.isOn();
    const int sd = proc.syncState();
    const int pc = proc.presetCounter.load();
    const bool presetLoaded = pc != lastPresetCounter;
    lastPresetCounter = pc;
    if (! presetLoaded)
    {
        if (std::abs (sp - lastSpeed) > 1.0e-5f)
        {
            flash (sd > 0 ? "Speed inactive  (" + speedText() + ")" : "Speed  " + speedText());
            proc.presetName = {};
        }
        if (block != lastBlock) flash (block ? "Block  (R28 on)" : "Script '74  (R28 off)");
        if (on != lastOn)       flash (on ? "Effect on" : "Bypass", 1.6);
        if (sd != lastSync)     flash (sd > 0 ? "Tempo sync  " + speedText().fromFirstOccurrenceOf ("Sync ", false, false)
                                              : "Tempo sync off  " + speedText());
    }
    lastSpeed = sp; lastBlock = block; lastOn = on; lastSync = sd;

    if (const int lt = proc.learnTarget.load(); lt >= 0)
        flash ("MIDI LEARN  " + String (Phase90Processor::learnName (lt)), 0.25);
    if (const int learned = proc.lastLearned.exchange (-1); learned >= 0)
        flash (String (Phase90Processor::learnName (learned)) + " = CC " + String (proc.ccOf (learned).load()));

    const float st = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (st - statusAlpha) * (st > statusAlpha ? 0.45f : 0.30f);      // ~120 ms a l'apparition, ~300 ms au retour
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;
    presetText = presetLine();

    // ---- lumieres
    const bool follow = proc.apvts.getRawParameterValue ("ticklfo")->load() > 0.5f;
    const float lfo = proc.lfoVisual.load();                     // 0 = haut du balayage, 1 = bas
    const float tickTarget = on ? (follow ? 0.40f + 0.60f * (1.0f - lfo) : 1.0f) : 0.0f;
    tickLevel += (tickTarget - tickLevel) * (tickTarget > tickLevel ? 0.45f : 0.28f);
    footLevel += ((on ? 1.0f : 0.0f) - footLevel) * (on ? 0.45f : 0.28f);
    // bouton SYNC : l'anneau s'allume et pulse une fois par division (plein sur le temps, attenue entre deux)
    const float ph = proc.lfoPhaseVisual.load();
    const float syncTarget = sd > 0 ? 0.30f + 0.70f * std::pow (1.0f - ph, 2.2f) : 0.0f;
    syncLevel += (syncTarget - syncLevel) * 0.75f;
    for (auto* v : { &tickLevel, &footLevel, &syncLevel })
    {
        if (*v < 0.003f) *v = 0.0f;
        if (*v > 0.997f) *v = 1.0f;
    }
    if (now - lastGlowReadMs > 3000.0 && resizeSettle == 0)
    {
        lastGlowReadMs = now;
        glow = (float) NineHandsGlow::percent (JucePlugin_Name) / 100.0f;   // reglage commun a toutes les fenetres
    }

    // ---- redessins limites a ce qui change
    auto changed = [] (float& drawn, float v) { if (std::abs (drawn - v) < 0.003f) return false; drawn = v; return true; };
    if (changed (dTick, tickLevel)) askRepaint (layout::ticksGlow);
    if (changed (dFoot, footLevel) || footDown != dFootDown)
    {
        dFootDown = footDown;
        const float r = layout::fsRingR + 20.0f * layout::fsRingR / 33.2f;
        askRepaint (Rectangle<float> (r * 2.0f, r * 2.0f).withCentre (layout::fsPos).getUnion (layout::fsRefl));
    }
    if (changed (dSync, syncLevel) || sd != dSyncState)
    {
        dSyncState = sd;
        askRepaint (layout::syncGlow.getUnion (syncHit));
    }
    if (changed (dStatus, statusAlpha) || statusText != dStatusText || presetText != dPresetText || hover != dHover)
    {
        dStatusText = statusText; dPresetText = presetText; dHover = hover;
        askRepaint (layout::presetRect.expanded (3.0f));
    }
}

//==============================================================================
void Phase90Editor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff0e0e0f));          // derriere les jacks : le fond de l'image est transparent
    const Image& bg = bgScaled.isValid() ? bgScaled : background;
    g.setImageResamplingQuality (&bg == &background ? Graphics::highResamplingQuality : Graphics::lowResamplingQuality);
    if (bg.isValid()) g.drawImage (bg, getLocalBounds().toFloat());

    g.addTransform (AffineTransform::scale (k()));
    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
    drawLights (g);
    drawFootRing (g);
    drawPrint (g);
    drawBar (g);
}

void Phase90Editor::drawLights (Graphics& g)
{
    // sources toujours a fond, halos doses par le reglage Glow (25 a 100 %), sous la serigraphie
    auto layer = [&] (const Image& im, Rectangle<float> r, float level)
    {
        if (level <= 0.003f || ! im.isValid()) return;
        g.setOpacity (jmin (1.0f, level)); g.drawImage (im, r);
        g.setOpacity (1.0f);
    };
    layer (ticksGlow, layout::ticksGlow, tickLevel * glow);
    layer (ticksCore, layout::ticksCore, tickLevel);
    layer (syncGlow, layout::syncGlow, syncLevel * glow);
    layer (syncCore, layout::syncCore, syncLevel);
    layer (fsRefl, layout::fsRefl, footLevel * 0.5f);
}

void Phase90Editor::drawFootRing (Graphics& g)
{
    // anneau lumineux dans la gorge du footswitch (dessin d'Octopus) : halo dose par Glow, trait net, coeur clair
    const auto c = layout::fsPos;
    const float lvl = footLevel;
    if (lvl > 0.003f)
    {
        Path ring;
        ring.addEllipse (c.x - layout::fsRingR, c.y - layout::fsRingR, layout::fsRingR * 2.0f, layout::fsRingR * 2.0f);
        const float kr = layout::fsRingR / 33.2f;
        if (glow > 0.0f)
            for (float hw = 20.0f; hw > 3.0f; hw -= 1.5f)
            {
                g.setColour (ringOrange.withAlpha (jmin (1.0f, 0.075f * glow) * lvl));
                g.strokePath (ring, PathStrokeType (hw * kr));
            }
        g.setColour (ringOrange.withAlpha (0.85f * lvl));
        g.strokePath (ring, PathStrokeType (layout::fsRingW));
        g.setColour (ringCoreCol.withAlpha (0.9f * lvl));
        g.strokePath (ring, PathStrokeType (layout::fsRingW * 0.42f));
    }
    if (footDown)       // bouton enfonce (fonctionnement d'Echoflex)
    {
        const float r = layout::footR * 0.98f;
        g.setColour (Colours::black.withAlpha (0.25f));
        g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
    }
}

void Phase90Editor::drawPrint (Graphics& g)
{
    g.setColour (inkLight.withAlpha (0.94f));
    g.fillPath (speedPath);
    g.setColour (Colour (0xffe2e2e6).withAlpha (0.92f));
    g.fillPath (ticksPath);
    g.setColour (inkDark.withAlpha (0.93f));
    g.fillPath (darkPath);
    // PHASE : orange en relief (ombre en bas a droite, liseré clair en haut a gauche : lumiere a 45 deg)
    g.setColour (Colours::black.withAlpha (0.78f));
    g.fillPath (phasePath, AffineTransform::translation (0.8f, 1.2f));
    g.setColour (Colour (0xffffbe8c).withAlpha (0.63f));
    g.fillPath (phasePath, AffineTransform::translation (-0.35f, -0.45f));
    g.setColour (phaseOrange);
    g.fillPath (phasePath);
    // SYNC : gris, orange quand la synchro tempo est active (avec la division)
    const int sd = proc.syncState();
    g.setColour (sd > 0 ? syncLit : inkLight.withAlpha (0.92f));
    g.fillPath (syncLabels[sd]);
    if (logo != nullptr)
    {
        const auto vb = logo->getDrawableBounds();
        const float w = layout::logoW, h = w * vb.getHeight() / jmax (1.0f, vb.getWidth());
        logo->drawWithin (g, { layout::logoPos.x - w * 0.5f, layout::logoPos.y - h * 0.5f, w, h }, RectanglePlacement::centred, 1.0f);
    }
}

void Phase90Editor::drawBar (Graphics& g)
{
    // pastille unique (400 x 38, reference Strong Pickle) : barre de presets au repos, ligne d'etat pendant les reglages
    const auto r = layout::presetRect;
    const bool barHot = hover == Hit::presetPrev || hover == Hit::presetName || hover == Hit::presetNext;
    g.setColour (Colours::black.withAlpha (0.9f));
    g.fillRoundedRectangle (r.expanded (1.2f), r.getHeight() * 0.5f + 1.2f);
    g.setColour (barFill);
    g.fillRoundedRectangle (r, r.getHeight() * 0.5f);
    g.setColour (barEdge.brighter (barHot && statusAlpha <= 0.0f ? 0.5f : 0.0f));
    g.drawRoundedRectangle (r.reduced (0.25f), r.getHeight() * 0.5f, 0.5f);
    g.setFont (Font (FontOptions (mediumFace).withHeight (layout::presetFont)));
    if (statusAlpha > 0.0f)
    {
        g.setColour (barInk.withAlpha (statusAlpha));
        g.drawFittedText (statusText, r.reduced (r.getHeight() * 0.5f, 0.0f).toNearestInt(), Justification::centred, 1, 0.6f);
    }
    const float a = 1.0f - statusAlpha;
    if (a <= 0.0f) return;
    auto arrow = [&] (Rectangle<float> ar, bool left, bool hot)
    {
        Path p; const auto c = ar.getCentre(); const float sz = 5.5f;
        if (left) p.addTriangle (c.x + sz * 0.6f, c.y - sz, c.x + sz * 0.6f, c.y + sz, c.x - sz * 0.8f, c.y);
        else      p.addTriangle (c.x - sz * 0.6f, c.y - sz, c.x - sz * 0.6f, c.y + sz, c.x + sz * 0.8f, c.y);
        g.setColour (barInk.withAlpha ((hot ? 1.0f : 0.6f) * a));
        g.fillPath (p);
    };
    arrow (r.withWidth (arrowW), true, hover == Hit::presetPrev);
    arrow (r.withTrimmedLeft (r.getWidth() - arrowW), false, hover == Hit::presetNext);
    g.setColour (barInk.withAlpha ((hover == Hit::presetName ? 1.0f : 0.92f) * a));
    g.drawFittedText (presetText, r.reduced (arrowW, 0.0f).toNearestInt(), Justification::centred, 1, 0.7f);
}

//==============================================================================
// Souris (le potard SPEED est un composant nh::Knob : glisser, molette, double-clic, clic droit)
//==============================================================================
Phase90Editor::Hit Phase90Editor::hitAt (Point<float> u) const
{
    if (syncHit.contains (u) || u.getDistanceFrom (layout::syncPos) <= layout::syncR * 1.3f) return Hit::sync;
    if (layout::phaseBox.contains (u)) return Hit::phase;
    if (u.getDistanceFrom (layout::fsPos) <= layout::footR * 1.35f) return Hit::foot;
    const auto r = layout::presetRect;
    if (r.contains (u))
        return u.x < r.getX() + arrowW ? Hit::presetPrev : (u.x > r.getRight() - arrowW ? Hit::presetNext : Hit::presetName);
    return Hit::none;
}

void Phase90Editor::mouseMove (const MouseEvent& e)
{
    hover = hitAt (toUnits (e.position));
    setMouseCursor (hover == Hit::none ? MouseCursor::NormalCursor : MouseCursor::PointingHandCursor);
}

void Phase90Editor::mouseExit (const MouseEvent&) { hover = Hit::none; }

void Phase90Editor::mouseDown (const MouseEvent& e)
{
    const auto h = hitAt (toUnits (e.position));
    if (e.mods.isPopupMenu())
    {
        // clic droit sur une commande : son MIDI Learn en tete du menu
        showContextMenu (h == Hit::foot ? 0 : h == Hit::phase ? 2 : h == Hit::sync ? 3 : -1);
        return;
    }
    if (statusAlpha > 0.0f && layout::presetRect.contains (toUnits (e.position)))
    {   // la ligne d'etat ne bloque pas : un clic fait revenir la barre de presets
        statusUntil = 0.0;
        return;
    }
    switch (h)
    {
        case Hit::phase:
            setParam ("block", proc.isBlock() ? 0.0f : 1.0f);
            proc.presetName = {};
            break;
        case Hit::sync:                       // OFF -> 1/4 -> 1/8 -> 1/2 -> OFF
            proc.cycleSync();
            proc.presetName = {};
            break;
        case Hit::foot:
            footDown = true;
            setParam ("on", proc.isOn() ? 0.0f : 1.0f);
            break;
        case Hit::presetPrev: stepPreset (-1); break;
        case Hit::presetNext: stepPreset (1); break;
        case Hit::presetName: showPresetMenu(); break;
        case Hit::none: break;
    }
}

void Phase90Editor::mouseUp (const MouseEvent&)
{
    footDown = false;
}

void Phase90Editor::mouseWheelMove (const MouseEvent& e, const MouseWheelDetails& w)
{
    const auto h = hitAt (toUnits (e.position));
    const float step = (std::abs (w.deltaY) > 1.0e-6f ? w.deltaY : w.deltaX) * (w.isReversed ? -1.0f : 1.0f);
    if (h == Hit::phase && std::abs (step) > 0.0f) { setParam ("block", step > 0 ? 1.0f : 0.0f); proc.presetName = {}; }
}

//==============================================================================
// Presets
//==============================================================================
void Phase90Editor::stepPreset (int delta)
{
    const int n = (int) Phase90Processor::factoryPresets().size();
    int cp = proc.getCurrentProgram();
    if (proc.presetName != Phase90Processor::factoryPresets()[(size_t) jlimit (0, n - 1, cp)].name)
        cp = delta > 0 ? -1 : 0;
    proc.setCurrentProgram ((cp + delta + n) % n);
    proc.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
}

void Phase90Editor::askUserPresetName (int slot)
{
    nameDialog = std::make_unique<AlertWindow> ("Save user preset " + String (slot), "Preset name:", MessageBoxIconType::NoIcon, this);
    nameDialog->addTextEditor ("name", proc.presetName.isNotEmpty() ? proc.presetName : "User " + String (slot));
    nameDialog->addButton ("Save", 1, KeyPress (KeyPress::returnKey));
    nameDialog->addButton ("Cancel", 0, KeyPress (KeyPress::escapeKey));
    nameDialog->enterModalState (true, ModalCallbackFunction::create ([this, slot] (int r)
    {
        if (r == 1 && nameDialog != nullptr)
        {
            auto n = nameDialog->getTextEditorContents ("name").trim();
            if (n.isEmpty()) n = "User " + String (slot);
            proc.saveUserPreset (slot, n);
            flash ("Saved  " + n);
        }
        nameDialog.reset();
    }), false);
}

void Phase90Editor::showPresetMenu()
{
    PopupMenu m;
    m.setLookAndFeel (&menuLnf);
    NineHandsMenu::addHeader (m, menuLnf.f, NineHandsMenu::icoPreset, menuAccent, "Presets", presetLine());
    m.addSectionHeader ("Factory presets");
    const auto& fp = Phase90Processor::factoryPresets();
    for (int i = 0; i < (int) fp.size(); ++i)
        m.addItem (100 + i, String (i + 1) + ". " + fp[(size_t) i].name, true, proc.presetName == fp[(size_t) i].name);
    m.addSeparator();
    PopupMenu load, save;
    for (int s = 1; s <= 9; ++s)
    {
        const auto n = proc.userPresetName (s);
        load.addItem (200 + s, "User " + String (s) + (n.isNotEmpty() ? "  " + n : String ("  (empty)")), n.isNotEmpty());
        save.addItem (300 + s, "User " + String (s) + (n.isNotEmpty() ? "  " + n + "  (overwrite)" : String()));
    }
    m.addSubMenu ("Load user preset", load);
    m.addSubMenu ("Save user preset", save);
    m.showMenuAsync (PopupMenu::Options().withMousePosition(),          // toujours la ou l'on clique
        [safe = Component::SafePointer<Phase90Editor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& pr = safe->proc;
            if (r >= 100 && r < 200)
            {
                pr.setCurrentProgram (r - 100);
                pr.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
            }
            else if (r > 200 && r < 300) pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400) safe->askUserPresetName (r - 300);
        });
}

//==============================================================================
// Menu clic droit (design d'Octopus, NineHandsMenu.h), toujours ouvert a l'endroit du clic
//==============================================================================
void Phase90Editor::showContextMenu (int learnIdx)
{
    using namespace NineHandsMenu;
    PopupMenu menu;
    menu.setLookAndFeel (&menuLnf);
    auto ccText = [this] (int i) { const int cc = proc.ccOf (i).load(); return cc >= 0 ? "CC " + String (cc) : String ("not assigned"); };
    const int lt = proc.learnTarget.load();
    if (learnIdx >= 0)
    {
        const String name = Phase90Processor::learnName (learnIdx);
        const int ico = learnIdx == 0 ? icoPedal : learnIdx == 1 ? icoKnob : learnIdx == 2 ? icoSwitch : icoSettings;
        addHeader (menu, menuLnf.f, ico, menuAccent, name, "MIDI: " + ccText (learnIdx));
        menu.addItem (1000 + learnIdx, "MIDI Learn: " + name, true, lt == learnIdx);
        menu.addItem (1100 + learnIdx, "Clear MIDI: " + name, proc.ccOf (learnIdx).load() >= 0);
        if (lt >= 0) menu.addItem (1200, "Cancel MIDI learn");
        menu.addSeparator();
    }
    else
        addHeader (menu, menuLnf.f, icoPedal, menuAccent, "Phase 90", "Phaser  v" + String (JucePlugin_VersionString));

    PopupMenu sizes, defSizes;
    {
        const char* names[p9ui::numSizes] = { "60 %", "75 %", "100 %" };
        const int def = WigaWindowSize::defaultIndex (JucePlugin_Name, p9ui::numSizes);
        for (int i = 0; i < p9ui::numSizes; ++i)
        {
            sizes.addItem (1 + i, String (names[i]) + (i == def ? "  (default)" : ""), true, std::abs (getHeight() - sizeHeight (i)) <= 2);
            defSizes.addItem (20 + i, names[i], true, i == def);
        }
        sizes.addSeparator();
        sizes.addSubMenu ("Default size (new windows)", defSizes);
    }
    menu.addSubMenu ("Plugin size", sizes);
    PopupMenu glowM;                   // intensite du halo des lumieres (regle des skills, nov. 2026)
    {
        const int now = roundToInt (glow * 100.0f);
        for (int i = 0; i < NineHandsGlow::numSteps; ++i)
        {
            const int pc = NineHandsGlow::steps[i];
            glowM.addItem (60 + i, "Glow " + String (pc) + " %" + (pc == 100 ? "  (default)" : ""), true, now == pc);
        }
    }
    menu.addSubMenu ("Glow (halo of the lights)", glowM);
    menu.addSeparator();

    PopupMenu factory;
    const auto& fp = Phase90Processor::factoryPresets();
    for (int i = 0; i < (int) fp.size(); ++i)
        factory.addItem (100 + i, String (i + 1) + ". " + fp[(size_t) i].name, true, proc.presetName == fp[(size_t) i].name);
    menu.addSubMenu ("Factory presets", factory);
    PopupMenu load, save;
    for (int s = 1; s <= 9; ++s)
    {
        const auto n = proc.userPresetName (s);
        load.addItem (200 + s, "User " + String (s) + (n.isNotEmpty() ? "  " + n : String ("  (empty)")), n.isNotEmpty());
        save.addItem (300 + s, "User " + String (s) + (n.isNotEmpty() ? "  " + n + "  (overwrite)" : String()));
    }
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();

    auto flag = [this] (const char* id) { return proc.apvts.getRawParameterValue (id)->load() > 0.5f; };
    PopupMenu settings, syncM;
    settings.addItem (520, "Voicing: Script '74 (no R28, smooth)", true, ! proc.isBlock());
    settings.addItem (521, "Voicing: Block '77 (R28, more mids)", true, proc.isBlock());
    settings.addSeparator();
    for (int i = 0; i < Phase90Processor::numSyncStates; ++i)
        syncM.addItem (530 + i, i == 0 ? String ("Off (SPEED in Hz)") : "Sync " + Phase90Processor::syncDivisionName (i), true, proc.syncState() == i);
    settings.addSubMenu ("Tempo sync (" + String (proc.hostBpm.load(), 1) + " BPM)", syncM);
    settings.addItem (502, "Stereo spread (right channel LFO inverted)", true, flag ("stereo"));
    settings.addItem (504, "Speed ring pulses with the LFO", true, flag ("ticklfo"));
    menu.addSubMenu ("Settings", settings);

    PopupMenu midi, chan;
    const int ch = (int) proc.apvts.getRawParameterValue ("midichan")->load();
    chan.addItem (600, "MIDI channel omni", true, ch == 0);
    for (int c = 1; c <= 16; ++c) chan.addItem (600 + c, "MIDI channel " + String (c), true, ch == c);
    midi.addSubMenu ("MIDI channel", chan);
    midi.addSectionHeader ("MIDI Learn");
    for (int i = 0; i < Phase90Processor::numLearn; ++i)
        midi.addItem (1000 + i, "Learn: " + String (Phase90Processor::learnName (i)) + "  (" + ccText (i) + ")", true, lt == i);
    midi.addSeparator();
    if (lt >= 0) midi.addItem (1200, "Cancel MIDI learn");
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    const bool mom = flag ("ccmomentary");
    midi.addItem (710, "MIDI footswitch latching (127 = on / 0 = off)", true, ! mom);
    midi.addItem (711, "MIDI footswitch momentary (toggle each press)", true, mom);
    midi.addItem (911, "Program Change 1-" + String ((int) fp.size()) + "  Factory presets", false);
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();
    menu.addItem (999, "Phase 90 v" + String (JucePlugin_VersionString) + "  NINE HANDS | DSP", false);

    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // toujours la ou l'on clique
        [safe = Component::SafePointer<Phase90Editor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& ed = *safe;
            auto& pr = ed.proc;
            auto toggleFlag = [&] (const char* id) { ed.setParam (id, pr.apvts.getRawParameterValue (id)->load() > 0.5f ? 0.0f : 1.0f); };
            if      (r >= 1 && r < 1 + p9ui::numSizes) ed.setWindowHeight (sizeHeight (r - 1));
            else if (r >= 20 && r < 20 + p9ui::numSizes)
            {
                WigaWindowSize::setDefaultIndex (JucePlugin_Name, r - 20);
                ed.setWindowHeight (sizeHeight (r - 20));
            }
            else if (r >= 60 && r < 60 + NineHandsGlow::numSteps)
            {
                ed.setGlowPercent (NineHandsGlow::steps[r - 60]);
                ed.flash ("Glow  " + String (NineHandsGlow::steps[r - 60]) + " %");
            }
            else if (r >= 100 && r < 200)
            {
                pr.setCurrentProgram (r - 100);
                pr.updateHostDisplay (AudioProcessor::ChangeDetails().withProgramChanged (true));
            }
            else if (r > 200 && r < 300) pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400) ed.askUserPresetName (r - 300);
            else if (r == 520 || r == 521) { ed.setParam ("block", r == 521 ? 1.0f : 0.0f); pr.presetName = {}; }
            else if (r >= 530 && r < 530 + Phase90Processor::numSyncStates) { ed.setParam ("syncdiv", (float) (r - 530)); pr.presetName = {}; }
            else if (r == 502) { toggleFlag ("stereo"); ed.flash (pr.apvts.getRawParameterValue ("stereo")->load() > 0.5f ? "Stereo spread" : "Mono (original)"); }
            else if (r == 504) toggleFlag ("ticklfo");
            else if (r >= 600 && r <= 616) ed.setParam ("midichan", (float) (r - 600));
            else if (r == 710 || r == 711) ed.setParam ("ccmomentary", r == 711 ? 1.0f : 0.0f);
            else if (r >= 1000 && r < 1000 + Phase90Processor::numLearn)
            {
                const int t = r - 1000;
                pr.learnTarget.store (pr.learnTarget.load() == t ? -1 : t);       // re-cliquer annule
            }
            else if (r >= 1100 && r < 1100 + Phase90Processor::numLearn)
            {
                pr.ccOf (r - 1100).store (-1);
                ed.flash (String (Phase90Processor::learnName (r - 1100)) + "  MIDI cleared");
            }
            else if (r == 1200) pr.learnTarget.store (-1);
            else if (r == 1201) { pr.learnTarget.store (-1); pr.clearMidi(); ed.flash ("All MIDI cleared"); }
        });
}
