# Phase 90 — NINE HANDS | DSP

Phaser analogique **VST3** (Windows 64 bits + macOS universel Apple Silicon/Intel) au format pédale simple,
modélisé composant par composant sur le **MXR Phase 90** : 4 cellules passe-tout à JFET 2N5952,
LFO triangle (trigger de Schmitt + intégrateur), mélange sec/traité 50/50, résistance de réinjection R28
(versions *Block*), plus une LED **SYNC** au tempo du DAW. Version 2.0.0 : pédale entièrement redessinée selon les règles NINE HANDS | DSP.

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/Phase-90/releases/latest/download/Phase90-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/Phase-90/releases/latest/download/Phase90-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Phase-90/releases/latest/download/Phase90-Notice.pdf"><img alt="Télécharger la notice (PDF)" src="https://img.shields.io/badge/%F0%9F%93%96%20Notice-PDF-919496?style=for-the-badge"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Phase-90/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/Phase-90?label=derni%C3%A8re%20version&color=919496"></a>
</p>

## Compiler avec GitHub
1. Mets **tous les fichiers à la racine du dépôt** (avec le dossier `.github/workflows`).
2. Un push lance l'onglet **Actions** → workflow *Build Phase 90 VST3 (Windows + macOS)*.
3. À la fin, télécharge les artefacts :
   - `Phase90-VST3-Windows` → copie `Phase 90.vst3` dans `C:\Program Files\Common Files\VST3\`
   - `Phase90-VST3-macOS` → copie `Phase 90.vst3` dans `~/Library/Audio/Plug-Ins/VST3/` puis lance une fois
     `xattr -cr ~/Library/Audio/Plug-Ins/VST3/"Phase 90.vst3"`
4. Dans Reaper : re-scanne les plug-ins. Le plugin apparaît comme **Phase 90 (NINE HANDS | DSP)**.

Le job *Test du moteur phaser* compile `dsp_test.cpp` (plage du SPEED, position et profondeur des encoches,
effet de R28, niveaux, bypass, stabilité de 44,1 à 192 kHz). S'il échoue, le build est signalé en rouge.

## Commandes
| Commande | Rôle |
|---|---|
| **SPEED** | vitesse du LFO, ≈ 0,10 Hz → 4,4 Hz (Script) / 5,2 Hz (Block), potard 470k log comme l'original (midi ≈ 0,9 Hz). Tirer haut / bas (course complète ≈ 400 px), molette, **Maj** = réglage fin, double-clic = midi. Potard en calques (chapeau, couronne, ombre) qui tournent ensemble avec flou de mouvement |
| Cartouche **PHASE** | clic (ou molette) = bascule **SCRIPT '74** (sans R28, doux) / **BLOCK** (R28, plus de médiums, le M101 actuel) |
| LED **SYNC** (en bas à droite du SPEED) | chaque clic : OFF → **1/4** → **1/8** → **1/2** → OFF. En SYNC, le balayage suit le tempo du DAW (calé sur la grille pendant la lecture), la LED orange pulse à chaque division, l'inscription passe en blanc et le SPEED est inactif |
| Footswitch | effet / bypass (vrai bypass, fondu de 8 ms) — anneau lumineux dans la gorge (dessin d'Octopus), graduations orange allumées |
| Barre de presets / ligne d'état | une seule pastille : ◀ preset ▶ au repos (clic sur le nom = menu), valeur en direct pendant un réglage, puis retour à la barre |

Les 11 graduations orange « respirent » avec le balayage (40 → 100 % de luminosité) — désactivable. Halos réglables : **Glow** 25 / 50 / 75 / 100 %.

## Presets
Menu des presets de la fenêtre du DAW (programmes VST3) : Classic Block, Script '74, Eruption, Brown Sound,
Slow Jet, Funk Rhythm, Fast Warble, Rotary Fast, Bass Swirl, Tempo 1/4, Tempo 1/8 Funk, Tempo 1/2 Swell. Clic droit → 9 presets utilisateur
communs à toutes les instances (`%APPDATA%\Nine Hands DSP\Phase 90\user_presets.xml`).

## Clic droit (menus au style Octopus, ouverts là où l'on clique)
- Sur une commande (SPEED, PHASE, SYNC, footswitch) : **MIDI Learn** / **Clear MIDI** de cette commande en tête du menu.
- **Plugin size** : 60 % (défaut = taille minimale), 75 %, 100 % — ou tirer le coin jusqu'à 150 %. Sous-menu **Default size (new windows)**.
- **Glow (halo of the lights)** : 25 / 50 / 75 / 100 %.
- **Factory presets**, **Load / Save user preset**.
- **Settings** : Voicing Script '74 / Block '77, Tempo sync (Off / 1/4 / 1/8 / 1/2), stéréo élargie (LFO du canal droit en opposition ; l'original est mono), graduations qui pulsent avec le LFO.
- **MIDI** : canal, *Learn* — aucun CC assigné par défaut (Footswitch, Speed, Script/Block, Sync button : chaque appui = état suivant) ; *Clear all MIDI assignments* ;
  pédale à verrouillage ou momentanée ; Program Change n = preset n+1.

## Fonctionnement (résumé)
- **Cellules** : ampli-op inverseur 10k/10k, 47 nF + (24k // rDS du JFET) sur l'entrée + :
  H(s) = −(1 − sRC)/(1 + sRC). 4 cellules = 720° → 2 encoches à 0,414·fc et 2,414·fc.
- **JFET** : rDS ≈ Ron / (1 − VGS/VP) (Ron ≈ 400 Ω, VP ≈ −2,4 V, 4 JFET légèrement différents comme sur une vraie
  pédale). JFET coupé : fc = 141 Hz (encoches 58 / 340 Hz, valeurs ElectroSmash).
- **Balayage** : 1re encoche ≈ 2,4 kHz → 80 Hz. rDS étant hyperbolique, la descente dans les graves est rapide
  et le passage dans les aigus plus long : le « swoosh » asymétrique du Phase 90.
- **R28 (Block)** : 24k de la 4e cellule vers l'entrée de la 2e → bosse de ~ +4 dB dans les médiums, encoches moins
  creuses, son plus « agressif ». Le Script n'a pas cette résistance.
- **Entrée / sortie** : passe-haut 34 Hz (0,01 µF / 470k) et 22 Hz, saturation douce des TL062 bien au-dessus du niveau guitare.

Polices Poppins et Barlow Condensed (licence SIL OFL). Logo : `NineHandsLogoBlack.svg` (NineHands_LogoPP_v003_FullBlack).

## Versions

- v2.0.0 : refonte complète selon les règles NINE HANDS | DSP : visuel 1235 x 1800, potard nh::Knob (calques + flou de mouvement, lumière à 45°), footswitch et jacks photo, anneau du footswitch façon Octopus, LED SYNC, sérigraphie vectorielle Poppins, logo v003, Glow, barre de presets / ligne d'état, menus Octopus
- v1.4.1 : plus aucun CC MIDI assigné par défaut (tout passe par le MIDI Learn)
- v1.4.0 : clic droit > Plugin size > Default size (new windows) : taille par défaut des nouvelles fenêtres au choix, comme dans Octopus
- v1.3.0 : MIDI Learn au clic droit sur chaque commande (potard SPEED, SCRIPT/BLOCK, SYNC, footswitch) + « Clear MIDI » ; menu de taille : 60 % (default), 75 %, 100 %
- v1.2.0 : anti-gel v2 (JUCE 8.0.15, caches refaits par le timer, chien de garde, aucun appel à l'hôte depuis le thread audio)

## Notice
- `docs/Phase90_Notice_FR_v2.0.0.pdf` (français). Générateur : `python3 tools/manual.py <captures tools/render> <sortie.pdf>`.
- Captures de la vraie fenêtre : `tools/render` (outil Linux, voir `tools/render/CMakeLists.txt`) ; visuel : `python3 tools/make_art.py build`.
