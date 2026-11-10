// genere par tools/make_art.py - ne pas modifier a la main (repere 617.5 x 900 = fond 1235 x 1800 px / 2)
#pragma once
#include <juce_graphics/juce_graphics.h>
namespace layout
{
    constexpr float frameW = 617.50f, frameH = 900.00f;
    const juce::Point<float> knobPos { 307.25f, 172.25f }; const float knobR = 107.75f;   // axe du potard SPEED
    const juce::Rectangle<float> knobBox { 173.35f, 38.35f, 267.81f, 267.81f };   // composant nh::Knob (calques 1024 px)
    const juce::Point<float> fsPos { 308.25f, 651.75f }; const float footR = 39.02f;
    const float fsRingR = 41.04f, fsRingW = 2.63f;   // anneau lumineux dans la gorge du footswitch (dessin d'Octopus)
    const juce::Point<float> syncPos { 451.00f, 276.00f }; const float syncR = 13.00f;
    const juce::Rectangle<float> phaseBox { 172.50f, 376.00f, 272.50f, 105.00f };
    const juce::Rectangle<float> presetRect { 108.75f, 511.00f, 400.00f, 38.00f };   // pastille presets / ligne d'etat (400 x 38)
    const float presetFont = 23.0f;
    const juce::Rectangle<float> ticksCore { 176.00f, 40.00f, 263.50f, 246.00f };
    const juce::Rectangle<float> ticksGlow { 162.50f, 26.50f, 290.50f, 273.50f };
    const juce::Rectangle<float> syncCore { 440.50f, 265.50f, 21.50f, 21.50f };
    const juce::Rectangle<float> syncGlow { 408.50f, 233.50f, 84.50f, 84.50f };
    const juce::Rectangle<float> fsRefl { 249.50f, 599.50f, 118.00f, 105.00f };
    struct Txt { const char* s; int font; float capH, track, x, y, rot; };   // font : 0 medium, 1 bold, 2 light, 3 regular
    const Txt texts[] = {
        { "SPEED", 3, 20.00f, 1.50f, 308.75f, 301.50f, 0.00f },
        { "PHASE", 1, 41.00f, 3.00f, 308.75f, 428.50f, 0.00f },
        { "OUTPUT", 3, 14.00f, 1.25f, 61.00f, 424.00f, -90.00f },
        { "INPUT", 3, 14.00f, 1.25f, 554.00f, 426.00f, 90.00f },
        { "90", 2, 42.00f, 2.00f, 308.75f, 787.50f, 0.00f }
    };
    struct Seg { float x0, y0, x1, y1, w; };
    const Seg ticks[] = { { 237.19f, 263.13f, 230.80f, 271.46f, 2.20f }, { 225.83f, 253.17f, 218.40f, 260.60f, 2.20f }, { 215.87f, 241.81f, 207.54f, 248.20f, 2.20f }, { 200.79f, 215.70f, 191.09f, 219.72f, 2.20f }, { 195.94f, 201.39f, 185.79f, 204.11f, 2.20f }, { 192.99f, 186.58f, 182.58f, 187.95f, 2.20f }, { 192.99f, 156.42f, 182.58f, 155.05f, 2.20f }, { 195.94f, 141.61f, 185.79f, 138.89f, 2.20f }, { 200.79f, 127.30f, 191.09f, 123.28f, 2.20f }, { 215.87f, 101.19f, 207.54f, 94.80f, 2.20f }, { 225.83f, 89.83f, 218.40f, 82.40f, 2.20f }, { 237.19f, 79.87f, 230.80f, 71.54f, 2.20f }, { 263.30f, 64.79f, 259.28f, 55.09f, 2.20f }, { 277.61f, 59.94f, 274.89f, 49.79f, 2.20f }, { 292.42f, 56.99f, 291.05f, 46.58f, 2.20f }, { 322.58f, 56.99f, 323.95f, 46.58f, 2.20f }, { 337.39f, 59.94f, 340.11f, 49.79f, 2.20f }, { 351.70f, 64.79f, 355.72f, 55.09f, 2.20f }, { 377.81f, 79.87f, 384.20f, 71.54f, 2.20f }, { 389.17f, 89.83f, 396.60f, 82.40f, 2.20f }, { 399.13f, 101.19f, 407.46f, 94.80f, 2.20f }, { 414.21f, 127.30f, 423.91f, 123.28f, 2.20f }, { 419.06f, 141.61f, 429.21f, 138.89f, 2.20f }, { 422.01f, 156.42f, 432.42f, 155.05f, 2.20f }, { 422.01f, 186.58f, 432.42f, 187.95f, 2.20f }, { 419.06f, 201.39f, 429.21f, 204.11f, 2.20f }, { 414.21f, 215.70f, 423.91f, 219.72f, 2.20f }, { 399.13f, 241.81f, 407.46f, 248.20f, 2.20f }, { 389.17f, 253.17f, 396.60f, 260.60f, 2.20f }, { 377.81f, 263.13f, 384.20f, 271.46f, 2.20f } };
    const juce::Point<float> syncLabelPos { 451.00f, 299.00f }; const float syncLabelCapH = 9.00f;
    const juce::Point<float> logoPos { 308.75f, 834.00f }; const float logoW = 150.00f;
}
