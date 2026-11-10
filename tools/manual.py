# PHASE 90 (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin (tools/render).
# Usage : python3 tools/manual.py [<dossier des captures (tools/render)>] <fichier PDF de sortie>
#   avec captures : recompose les images et les copie dans tools/manual_assets/ ;
#   sans captures : reprend les images composees de tools/manual_assets/.
# Version lue dans CMakeLists.txt. Couverture « minimale » (gabarit fixe commun a toutes les notices NINE HANDS | DSP).
import os, re, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = re.search(r"project\s*\(\s*\w+\s+VERSION\s+([0-9.]+)", open(os.path.join(ROOT, "CMakeLists.txt")).read()).group(1)
SHOTS = sys.argv[1] if len(sys.argv) > 2 else None
OUT = sys.argv[-1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "Phase90_Notice_FR_v" + VERSION + ".pdf")
TMP = os.environ.get("NOTICE_TMP", "/tmp"); os.makedirs(TMP, exist_ok=True)
FONTS = os.path.join(ROOT, "assets", "fonts")
ASSETS = os.path.join(ROOT, "tools", "manual_assets")
CHARTS = os.path.join(ROOT, "tools", "manual")
LOGO_PNG = os.path.join(ROOT, "assets", "nine_hands_logo_blanc.png")      # NineHands_LogoPP_v003_FullWhite.svg rendu (Chromium)

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))
pdfmetrics.registerFont(TTFont("DV", os.path.join(FONTS, "DejaVuSans.ttf")))       # glyphes absents de Poppins (fleche, ohm)

ACC = colors.HexColor("#E8641B"); ACC_L = colors.HexColor("#FF9A4A")      # orange de la pedale / lumieres allumees
DARK = colors.HexColor("#1E1E1E"); GREY = colors.HexColor("#6B6B6B"); LIGHT = colors.HexColor("#F7EFE8")
LAY = json.load(open(os.path.join(ROOT, "tools", "layout.json")))

NAMES = ["p9_annotated.png", "p9_onoff.png", "p9_phase.png", "p9_bar.png", "p9_glow.png", "p9_menus.png", "p9_cover.png", "p9_sync.png"]
if SHOTS:
    def shot(name): return Image.open(os.path.join(SHOTS, name)).convert("RGB")
    src = shot("p9_exact_on.png")
    k = src.height / 900.0                          # repere du plugin : 617,5 x 900 unites (fond 1235 x 1800 / 2)
    kx, ky, kr = LAY["knob"]; sx, sy = LAY["sync"][:2]; fx, fy = LAY["fs"][:2]
    bx, by, bw_, bh_ = LAY["phaseBox"]; px, py, pw, ph = LAY["preset"]; jy = LAY["jackY"]

    # ---------- capture annotee ----------
    marks = [(1, kx - kr - 22, ky - kr + 10), (2, sx + 30, sy - 22), (3, bx + bw_ + 22, by + 12), (4, px - 4, py - 16),
             (5, fx + 70, fy - 46), (6, 34, jy - 70), (7, 584, jy - 70)]
    ann = src.copy(); dr = ImageDraw.Draw(ann)
    fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 36)
    for n, x, y in marks:
        cx, cy, r = x * k, y * k, 29
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(232, 100, 27), width=5)
        dr.text((cx, cy + 1), str(n), font=fnt, fill=(30, 30, 30), anchor="mm")
    ann.save(os.path.join(TMP, NAMES[0]))

    def crop_u(im, box): return im.crop(tuple(int(round(v * k)) for v in box))
    gap = 18
    def strip(parts, path, bg=(255, 255, 255)):
        s = Image.new("RGB", (sum(p.width for p in parts) + gap * (len(parts) - 1), max(p.height for p in parts)), bg)
        x = 0
        for p in parts: s.paste(p, (x, 0)); x += p.width + gap
        s.save(path); return path

    byp = shot("p9_exact_bypass.png")
    strip([byp.resize((618, 900), Image.LANCZOS), src.resize((618, 900), Image.LANCZOS)], os.path.join(TMP, NAMES[1]))
    # cartouche PHASE
    crop_u(src, (bx - 14, by - 14, bx + bw_ + 14, by + bh_ + 14)).save(os.path.join(TMP, NAMES[2]))
    # pastille : barre de presets, ligne d'etat (SPEED), synchro tempo
    box_bar = (px - 8, py - 8, px + pw + 8, py + ph + 8)
    bars = [crop_u(shot(n), box_bar) for n in ("p9_exact_on.png", "p9_exact_status.png", "p9_exact_sync.png")]
    bw, bh = bars[0].size
    col = Image.new("RGB", (bw, bh * 3 + gap * 2), (255, 255, 255))
    for i, b in enumerate(bars): col.paste(b, (0, i * (bh + gap)))
    col.save(os.path.join(TMP, NAMES[3]))
    # reglage Glow : 25 / 50 / 75 / 100 % (zone du potard et de la LED SYNC)
    box_gl = (kx - 135, ky - 135, kx + 165, ky + 135)
    strip([crop_u(shot(n), box_gl) for n in ("p9_glow_25.png", "p9_glow_50.png", "p9_glow_75.png", "p9_exact_on.png")], os.path.join(TMP, NAMES[4]))
    # menus clic droit : menu principal et Settings
    m1, m2 = Image.open(os.path.join(SHOTS, "p9_menu.png")).convert("RGBA"), Image.open(os.path.join(SHOTS, "p9_menu_settings.png")).convert("RGBA")
    mm_ = Image.new("RGBA", (m1.width + m2.width + gap * 2, max(m1.height, m2.height + 60)), (255, 255, 255, 255))
    mm_.alpha_composite(m1, (0, 0)); mm_.alpha_composite(m2, (m1.width + gap * 2, 60))
    mm_.convert("RGB").save(os.path.join(TMP, NAMES[5]))
    # LED SYNC : eteinte puis allumee (1/4)
    box_sy = (sx - 50, sy - 30, sx + 50, sy + 36)
    strip([crop_u(src, box_sy), crop_u(shot("p9_exact_sync.png"), box_sy)], os.path.join(TMP, NAMES[7]))

    # ---------- couverture : pedale detouree (canal alpha du fond), reflet au sol, halo orange tres doux ----------
    bg_a = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(src.size, Image.LANCZOS)
    cut = Image.new("RGBA", src.size, (0, 0, 0, 0)); cut.paste(src, (0, 0), bg_a)
    cut = cut.crop(cut.getbbox())
    cw, ch = cut.size
    pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 30
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
    glow *= edge ** 2
    halo = np.dstack([glow * 1.0, glow * 0.45, glow * 0.12, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
    canvas.convert("RGB").save(os.path.join(TMP, NAMES[6]))
    os.makedirs(ASSETS, exist_ok=True)
    for n in NAMES: shutil.copy(os.path.join(TMP, n), os.path.join(ASSETS, n))
annotated, onoff, phase_img, bar_img, glow_img, menus_img, cover, sync_img = [os.path.join(ASSETS, n) for n in NAMES]

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

# ---------- styles ----------
st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "tip": ParagraphStyle("tip", fontName="Pop", fontSize=9.2, leading=13, textColor=DARK, spaceAfter=4),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.6, leading=11.4, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.6, leading=11.4, textColor=DARK),
}
def P(t, s="p"):
    for ch in "→Ω": t = t.replace(ch, '<font name="DV">' + ch + '</font>')
    return Paragraph(t, st[s])
def bullets(items, s="p"): return [P("&bull;&nbsp;&nbsp;" + i, s) for i in items]
def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and r == 0) else "cell") for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E8D9CC")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t
def side(left, right, wl):
    t = Table([[left, right]], colWidths=[wl, W - wl])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (-1, 0), (-1, 0), 0)]))
    return t

# ---------- donnees (identiques au code livre : PluginProcessor.cpp) ----------
FACTORY = [("Classic Block", "BLOCK", "0,92 Hz", "Potard à midi : le Phase 90 actuel (M101). Preset par défaut."),
           ("Script '74", "SCRIPT", "0,70 Hz", "Le son doux et rond des premiers modèles."),
           ("Eruption", "SCRIPT", "0,28 Hz", "Balayage lent sur un son saturé."),
           ("Brown Sound", "BLOCK", "0,40 Hz", "Rythmique crunch, R28 pour le mordant."),
           ("Slow Jet", "BLOCK", "0,12 Hz", "Effet « avion » très lent."),
           ("Funk Rhythm", "BLOCK", "2,20 Hz", "Rythmiques funk en son clair."),
           ("Fast Warble", "SCRIPT", "4,40 Hz", "Vitesse maxi Script, proche du vibrato."),
           ("Rotary Fast", "BLOCK", "5,10 Hz", "Vitesse maxi Block, façon haut-parleur tournant."),
           ("Bass Swirl", "SCRIPT", "0,50 Hz", "Pour la basse (le Script garde plus de graves)."),
           ("Tempo 1/4", "BLOCK", "SYNC 1/4", "Un balayage par temps, calé sur le DAW."),
           ("Tempo 1/8 Funk", "BLOCK", "SYNC 1/8", "Deux balayages par temps pour les rythmiques funk."),
           ("Tempo 1/2 Swell", "SCRIPT", "SYNC 1/2", "Un balayage lent tous les deux temps.")]

W = A4[0] - 36 * mm
f = [NextPageTemplate("p"), Spacer(1, 1), PageBreak()]     # page 1 = couverture dessinee a positions fixes (cover_bg)

f += [P("1. Présentation", "h1"),
      P("<b>PHASE 90</b> est un phaser VST3 NINE HANDS | DSP au format pédale, modélisé composant par composant sur le <b>MXR Phase 90</b>, "
        "la toute première pédale MXR (1972-74) et l'un des phasers les plus enregistrés de l'histoire : « Eruption » et « Ain't Talkin' 'bout Love » "
        "d'Eddie Van Halen, Jimmy Page, Brian May et d'innombrables rythmiques funk."),
      P("Comme l'original, il n'a qu'un seul potard, <b>SPEED</b>. À l'intérieur, quatre cellules passe-tout construites autour de JFET 2N5952 "
        "déphasent le signal jusqu'à 720°. Mélangé à parts égales avec le son direct, cela crée deux encoches mobiles dans le spectre : le « swoosh » "
        "classique, chaud et vocal, jamais maigre."),
      P("Deux versions historiques se choisissent d'un clic sur le cartouche <b>PHASE</b> : <b>Script</b> (1974-77, sans résistance de réinjection : "
        "doux, rond, encoches profondes) et <b>Block</b> (à partir de 1977 et l'actuel Dunlop M101 : la résistance R28 renvoie une partie de la sortie "
        "pour plus de médiums, plus de mordant et une vitesse maxi un peu plus élevée)."),
      P("La version 2 redessine entièrement la pédale selon les règles NINE HANDS | DSP : potard SPEED en calques qui tournent avec un flou de mouvement, "
        "footswitch et jacks photographiés, anneau lumineux du footswitch, LED <b>SYNC</b> de synchro tempo, sérigraphie vectorielle nette à toutes les tailles, "
        "halos réglables (<b>Glow</b>), barre de presets et menus du clic droit au style NINE HANDS | DSP, MIDI Learn sur toutes les commandes."),
      P("2. Installation", "h1")]
f += bullets(["<b>Windows</b> : téléchargez <b>Phase90-VST3-Windows.zip</b> (page Releases du dépôt GitHub Nine-Hands-Dsp/Phase-90), "
              "décompressez-le et copiez <b>Phase 90.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3\\</b>.",
              "<b>macOS</b> (universel, Apple Silicon et Intel) : téléchargez <b>Phase90-VST3-macOS.zip</b>, copiez <b>Phase 90.vst3</b> dans "
              "<b>~/Library/Audio/Plug-Ins/VST3/</b>, puis lancez une fois dans le Terminal : "
              "<i>xattr -cr ~/Library/Audio/Plug-Ins/VST3/\"Phase 90.vst3\"</i> (retire la quarantaine du téléchargement).",
              "<b>Reaper</b> : Options &gt; Préférences &gt; Plug-ins &gt; VST &gt; <i>Re-scan</i>. Le plugin apparaît sous le nom "
              "<b>Phase 90 (NINE HANDS | DSP)</b>, catégorie Fx | Modulation. Pistes mono ou stéréo ; une entrée mono donne une sortie stéréo. "
              "Pour le piloter en MIDI, la piste doit recevoir le MIDI du contrôleur (armement ou monitoring d'entrée, entrée MIDI réglée sur votre appareil)."])
f.append(PageBreak())

ov = [["N°", "Commande", "Rôle"],
      ["1", "SPEED", "Vitesse du balayage. Les graduations orange s'allument avec l'effet et respirent au rythme du balayage. Glisser, molette, double-clic, clic droit = MIDI Learn."],
      ["2", "LED SYNC", "Synchro tempo : chaque clic passe OFF → 1/4 → 1/8 → 1/2 → OFF. La LED s'allume en orange et clignote au tempo du DAW."],
      ["3", "Cartouche PHASE", "Clic : bascule SCRIPT '74 / BLOCK."],
      ["4", "Barre de presets / ligne d'état", "Au repos : flèches = preset précédent / suivant, clic sur le nom = menu des presets. Pendant un réglage : la valeur en direct."],
      ["5", "Footswitch", "Effet / bypass. L'anneau de sa gorge s'allume en orange avec l'effet."],
      ["6", "OUTPUT", "Jack de sortie (côté gauche, décoratif)."],
      ["7", "INPUT", "Jack d'entrée (côté droit, décoratif)."]]
f += [P("3. Vue d'ensemble de l'interface", "h1"),
      side([img(annotated, 84 * mm)], table(ov, [8 * mm, 27 * mm, W - 88 * mm - 35 * mm]), 88 * mm),
      Spacer(1, 4 * mm), KeepTogether([img(onoff, 104 * mm), P("À gauche : bypass (lumières éteintes) · À droite : effet actif (graduations, anneau du footswitch et halos allumés).", "small")]),
      PageBreak()]

f += [P("4. Les commandes en détail", "h1"), P("Potard SPEED", "h2")]
f += bullets(["Plage : <b>≈ 0,10 Hz → 4,4 Hz</b> en Script, <b>≈ 0,10 Hz → 5,2 Hz</b> en Block. Le potard d'origine est une piste logarithmique de 470 kΩ "
              "dans le courant de charge du condensateur du LFO : la moitié gauche de la course couvre les vitesses lentes (0,1 → 0,9 Hz), la moitié droite "
              "monte vite. À midi : ≈ 0,9 Hz. La ligne d'état affiche la vitesse en Hz.",
              "Souris : tirer vers le haut pour accélérer, vers le bas pour ralentir (toute la course demande environ 400 px de déplacement, quelle que soit la "
              "taille de la fenêtre), <b>Maj</b> = 5x plus fin, molette pour les petits pas, <b>double-clic</b> = retour à midi. Le potard tourne sur ±150°, "
              "comme la graduation ; chapeau, couronne et ombre tournent ensemble avec un léger flou de mouvement.",
              "À position égale, le Block est un peu plus rapide que le Script (résistances du LFO différentes).",
              "Quand la LED SYNC est allumée, c'est le tempo qui donne la vitesse : toucher le SPEED affiche <i>Speed inactive</i>. Il reprend la main dès que SYNC repasse sur OFF."])
gr = Table([[img(os.path.join(CHARTS, "chart_speed.png"), W / 2 - 3 * mm), img(os.path.join(CHARTS, "chart_notch.png"), W / 2 - 3 * mm)]], colWidths=[W / 2, W / 2])
gr.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
f += [KeepTogether([Spacer(1, 2 * mm), gr, P("À gauche : vitesse du LFO selon la position du SPEED · À droite : 1re encoche dans le temps (≈ 0,5 Hz) : "
                                            "long passage dans les aigus, plongée rapide dans les graves.", "small")]),
      P("<b>Le « swoosh ».</b> Le JFET se comporte comme une résistance hyperbolique : quand le triangle du LFO approche du pincement, la fréquence de coupure "
        "s'effondre. La 1re encoche descend de <b>≈ 2,4 kHz à ≈ 80 Hz</b>, en restant longtemps dans les aigus puis en plongeant vite dans les graves : "
        "l'asymétrie caractéristique du Phase 90."),
      P("Cartouche PHASE : SCRIPT / BLOCK", "h2"),
      side(bullets(["Cliquez sur le cartouche <b>PHASE</b> (ou molette dessus, ou clic droit &gt; Settings &gt; Voicing) pour changer de version. "
                    "La ligne d'état confirme <i>Script '74 (R28 off)</i> ou <i>Block (R28 on)</i>.",
                    "<b>SCRIPT '74</b> : sans réinjection, encoches profondes, son doux et vocal, idéal en clair et à la basse.",
                    "<b>BLOCK</b> : R28 (24 kΩ) renvoie la 4e cellule vers la 2e. Bosse d'environ +4 dB entre les encoches, encoches un peu moins creuses, "
                    "plus de présence et de mordant devant un ampli saturé, vitesse maxi un peu plus élevée. Block est la version par défaut (comme le M101)."]),
           [img(phase_img, 50 * mm), Spacer(1, 2 * mm), img(os.path.join(CHARTS, "chart_response.png"), 50 * mm),
            P("Réponse en fréquence à un instant donné : Script (gris) et Block (orange).", "small")], W - 54 * mm)]

f += [P("5. Footswitch, lumières, Glow et synchro tempo", "h1")]
f += bullets(["<b>Footswitch</b> : effet / bypass dès l'appui ; le bouton s'assombrit tant qu'on appuie. Le bypass est un vrai bypass : la sortie est exactement "
              "l'entrée, avec un fondu de 8 ms pour éviter les clics.",
              "<b>Lumières</b> : avec l'effet, l'anneau dans la gorge du footswitch et les 11 graduations orange autour du SPEED s'allument ; en bypass elles "
              "s'éteignent en fondu.",
              "<b>Graduations qui respirent</b> : par défaut, elles suivent le balayage du phaser, entre 40 et 100 % de leur luminosité (au plus clair quand le "
              "balayage est en haut). Elles respirent donc lentement quand le SPEED est bas, vite quand il est haut, et en mesure en SYNC. Pour les garder fixes : "
              "clic droit &gt; Settings &gt; <i>Speed ring pulses with the LFO</i>.",
              "<b>Glow</b> (clic droit &gt; <i>Glow (halo of the lights)</i>) : règle le halo autour des lumières, <b>25 %</b>, <b>50 %</b>, <b>75 %</b> "
              "ou <b>100 %</b> (par défaut). Seul le halo change ; les sources lumineuses gardent leur éclat. Réglage commun à toutes les instances, "
              "enregistré sur l'ordinateur."])
f += [KeepTogether([Spacer(1, 1 * mm), img(glow_img, W * 0.86), P("Glow 25 %, 50 %, 75 % et 100 %.", "small")]),
      P("Synchro tempo : LED SYNC", "h2"),
      side([P("La petite LED en bas à droite du SPEED cale le balayage sur le tempo du DAW. Chaque clic (sur la LED ou sur l'inscription) passe à l'état suivant : "
              "<b>OFF</b> → <b>1/4</b> (un balayage complet par temps) → <b>1/8</b> (deux balayages par temps) → <b>1/2</b> (un balayage tous les deux temps) → OFF. "
              "En synchro, la LED s'allume en orange et pulse à chaque division, l'inscription passe en blanc avec la division (<i>SYNC 1/4</i>) et la ligne d'état "
              "affiche brièvement la division et le tempo (<i>Tempo sync 1/4 @ 120 BPM</i>)."),
            P("La vitesse vaut <b>tempo du DAW ÷ division</b> (à 120 BPM : 1/4 = 2 Hz, 1/8 = 4 Hz, 1/2 = 1 Hz). Pendant la lecture, le balayage est en plus "
              "<b>calé sur la grille</b> : chaque cycle démarre sur le temps. Transport à l'arrêt, la vitesse suit quand même le tempo du projet. L'état est enregistré "
              "avec le projet et dans les presets, automatisable, et se pilote en MIDI (section 6) ou par clic droit &gt; Settings &gt; <i>Tempo sync</i>.")],
           [img(sync_img, 44 * mm), P("LED SYNC éteinte (OFF), puis allumée (1/4).", "small"), Spacer(1, 2 * mm),
            img(bar_img, 62 * mm), P("La pastille : barre de presets au repos, ligne d'état pendant un réglage du SPEED, puis en synchro tempo.", "small")], W - 66 * mm),
      P("<b>Stéréo élargie</b> : clic droit &gt; Settings &gt; <i>Stereo spread</i> fait tourner le LFO du canal droit en opposition pour un tourbillon stéréo large "
        "(la pédale d'origine est mono).")]

midi = [["Commande", "Type"],
        ["Footswitch", "À accrochage (défaut) : 64-127 = effet, 0-63 = bypass. Momentané : chaque appui bascule."],
        ["Speed", "Continu : 0-127 = toute la course du potard. Idéal sur une pédale d'expression."],
        ["Script / Block", "Bascule : 0-63 = Script, 64-127 = Block."],
        ["Sync button", "Bouton : chaque appui (valeur ≥ 64) passe à l'état suivant, OFF → 1/4 → 1/8 → 1/2 → OFF."],
        ["Program Change", "Non apprenable : le programme n charge le preset usine n+1 (programme 0 = Classic Block)."]]
f += [P("6. MIDI", "h1"),
      P("Chaque commande peut être pilotée par un footswitch, une pédale d'expression ou un contrôleur MIDI. <b>Aucun CC n'est assigné par défaut</b> : "
        "tout passe par le <b>MIDI Learn</b>, le plugin ne réagit donc jamais à un contrôleur que vous n'avez pas assigné vous-même.")]
f += bullets(["<b>Clic droit sur une commande</b> (potard SPEED, LED SYNC, cartouche PHASE ou footswitch) : le menu s'ouvre sur cette commande "
              "(son CC actuel ou <i>not assigned</i>), avec <b>MIDI Learn: &lt;commande&gt;</b> et <b>Clear MIDI: &lt;commande&gt;</b>.",
              "La ligne d'état affiche <b>MIDI LEARN</b> et le nom de la commande tant qu'elle attend. Bougez une pédale ou appuyez sur un bouton : le premier CC "
              "reçu est assigné et la ligne d'état le confirme (<i>Speed = CC 11</i>). <b>Cancel MIDI learn</b> arrête l'attente.",
              "<b>Clic droit ailleurs &gt; MIDI</b> : <b>MIDI channel</b> (omni par défaut ou 1 à 16), <b>Learn</b> de chaque commande avec son CC actuel, "
              "<b>Clear all MIDI assignments</b>, footswitch MIDI à accrochage ou momentané.",
              "Les assignations sont enregistrées avec le projet ; tous les paramètres sont aussi automatisables depuis le DAW."])
f += [KeepTogether([Spacer(1, 1 * mm), table(midi, [38 * mm, W - 38 * mm])])]

f += [P("7. Fenêtre et menus", "h1")]
f += bullets(["La fenêtre s'ouvre à la taille par défaut, <b>60 %</b> tant que vous n'en choisissez pas une autre, et ne peut jamais être plus petite que 60 %.",
              "Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b> ou <b>100 %</b> pour cette fenêtre (la taille actuelle est cochée, "
              "« (default) » marque la taille par défaut). On peut aussi agrandir la fenêtre par son coin, jusqu'à 150 % (proportions conservées).",
              "<b>Plugin size &gt; Default size (new windows)</b> : choisit la taille d'ouverture de toutes les nouvelles fenêtres de Phase 90 (réglage commun à "
              "toutes les instances, enregistré sur l'ordinateur) ; la fenêtre ouverte prend aussitôt cette taille. Une instance redimensionnée garde sa taille dans le projet.",
              "La <b>barre de presets</b> et la <b>ligne d'état</b> partagent la même pastille, sous le cartouche PHASE. Au repos, elle affiche le preset en cours "
              "(ou <i>Edited</i>). Dès qu'un réglage bouge (souris, molette, automation, MIDI), la ligne d'état prend sa place en fondu et affiche la valeur "
              "(<i>Speed 0.92 Hz</i>, <i>Block (R28 on)</i>, <i>Bypass</i>…), puis s'efface au bout de 2,5 s environ ; un clic sur la pastille fait revenir la barre "
              "de presets tout de suite. Le changement de preset, lui, ne fait pas apparaître la ligne d'état.",
              "Les menus du clic droit s'ouvrent toujours là où vous cliquez."])
menu = [["Entrée", "Contenu"],
        ["MIDI Learn (sur une commande)", "MIDI Learn / Clear MIDI / Cancel MIDI learn"],
        ["Plugin size", "60 % · 75 % · 100 % · Default size (new windows)"],
        ["Glow (halo of the lights)", "Glow 25 % · 50 % · 75 % · 100 % (default)"],
        ["Factory presets", "les 12 presets usine (section 8)"],
        ["Load / Save user preset", "User 1 … 9"],
        ["Settings", "Voicing Script '74 / Block '77 · Tempo sync (Off, 1/4, 1/8, 1/2) · Stereo spread · Speed ring pulses with the LFO"],
        ["MIDI", "MIDI channel · Learn x4 · Cancel / Clear all MIDI assignments · footswitch à accrochage / momentané · Program Change"]]
f += [Spacer(1, 1 * mm),
      side([table(menu, [36 * mm, W - 36 * mm - 76 * mm])], [img(menus_img, 72 * mm), P("Menu du clic droit et sous-menu Settings.", "small")], W - 76 * mm)]

pre = [["PC", "Preset", "Version", "SPEED", "Caractère"]] + [[str(i), "<b>" + n + "</b>", s, r, d] for i, (n, s, r, d) in enumerate(FACTORY)]
f += [P("8. Presets", "h1"),
      P("Les 12 presets usine sont des programmes VST3 : ils apparaissent dans le menu des presets du DAW (Reaper : champ preset de la fenêtre FX), "
        "sous les flèches et le nom de la barre de presets, et sous clic droit &gt; Factory presets. Ils mémorisent le SPEED, la version et l'état de la LED SYNC, "
        "et activent toujours l'effet. Clic droit &gt; <b>Save user preset</b> enregistre jusqu'à 9 presets personnels, communs à toutes les instances "
        "(%APPDATA%\\Nine Hands DSP\\Phase 90\\ ou ~/Library/Application Support/Nine Hands DSP/Phase 90/)."),
      KeepTogether([table(pre, [9 * mm, 30 * mm, 18 * mm, 18 * mm, W - 75 * mm])])]

f += [P("9. Conseils d'utilisation", "h1")]
f += bullets(["<b>Chaîne Reaper</b> : placez Phase 90 <b>avant la simulation d'ampli</b> (Ampire, Impulse…), comme une pédale devant un ampli, avec vos autres "
              "pédales NINE HANDS | DSP. Après l'ampli (ou après une fuzz), le swoosh devient plus marqué et plus aérien.",
              "<b>7 cordes / accordages graves</b> : le balayage descend jusqu'à ≈ 80 Hz, le Sol grave (≈ 49 Hz) et les cordes plus basses sont aussi déphasés. "
              "Pour les riffs lourds, le Script garde des graves plus fermes ; le Block ajoute du mordant dans les médiums. Les vitesses lentes (Slow Jet, Eruption) "
              "fonctionnent très bien sur les accords graves tenus.",
              "<b>Rythmique ou solo</b> : Funk Rhythm ou Classic Block pour les rythmiques en clair, Eruption ou Brown Sound pour les solos saturés. Apprenez Speed sur "
              "une pédale d'expression pour accélérer le balayage comme un haut-parleur tournant.",
              "<b>En rythme avec le morceau</b> : SYNC 1/4 sur un riff, 1/8 pour les rythmiques funk, 1/2 pour des montées lentes sur des accords tenus. Apprenez Sync button "
              "sur un footswitch MIDI pour changer de division en jouant.",
              "<b>Mix</b> : comme l'original, pas de réglage de profondeur ni de mix, c'est le mélange 50/50 qui crée les encoches profondes. En stéréo, essayez "
              "Stereo spread sur une guitare doublée."], "tip")

tech = [["Format", "VST3 - Windows 64 bits, macOS universel (Apple Silicon + Intel) - NINE HANDS | DSP, Fx | Modulation"],
        ["Pédale d'origine", "MXR Phase 90 (Script 1974-77, Block / Dunlop M101)"],
        ["Canaux", "mono vers stéréo, stéréo vers stéréo · latence 0 · 44,1 - 192 kHz"],
        ["Cellules", "4 passe-tout, 47 nF, 24 kΩ // JFET 2N5952 (Ron ≈ 400 Ω, Vp ≈ −2,4 V, quatre JFET légèrement différents)"],
        ["Encoches", "2, à 0,414·fc et 2,414·fc · 1re encoche ≈ 2,4 kHz → 80 Hz · JFET coupé : fc = 141 Hz (encoches 58 / 340 Hz)"],
        ["LFO", "trigger de Schmitt + intégrateur, potard 470 kΩ log · 0,10 → 4,4 Hz (Script) / 5,2 Hz (Block)"],
        ["R28 (Block)", "24 kΩ, 4e cellule → 2e · bosse de ≈ +4 dB dans les médiums"],
        ["Mix / bypass", "50 / 50 · passe-hauts 34 Hz en entrée et 22 Hz en sortie · vrai bypass avec fondu de 8 ms"],
        ["Synchro tempo", "LED SYNC : Off / 1/4 / 1/8 / 1/2 du tempo du DAW, calé sur la grille pendant la lecture"],
        ["Presets", "12 usine (programmes VST3) + 9 utilisateur communs à toutes les instances"],
        ["MIDI", "MIDI Learn sur Footswitch, Speed, Script / Block et Sync button, aucun CC assigné par défaut, canal omni / 1-16, footswitch à accrochage ou momentané, Program Change"],
        ["Fenêtre", "Plugin size 60 % / 75 % / 100 %, taille par défaut au choix (60 % au départ), jamais moins de 60 %, jusqu'à 150 % par le coin ; Glow 25 - 100 %"],
        ["Stabilité Windows", "anti-gel v2 : le thread audio n'appelle jamais l'hôte, rafraîchissement piloté par un timer avec chien de garde"]]
f += [KeepTogether([P("10. Caractéristiques techniques", "h1"), table(tech, [30 * mm, W - 30 * mm], header=False),
                    Spacer(1, 3 * mm),
                    P("Sources : ElectroSmash « MXR Phase 90 analysis » ; notice Dunlop MXR M101. MXR et Phase 90 sont des marques de Dunlop Manufacturing ; "
                      "ce plugin est un projet NINE HANDS | DSP sans lien avec Dunlop.", "small")])]

def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "Phase 90 (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="PHASE 90 - Notice v" + VERSION, author="NINE HANDS | DSP")
# ---- Couverture « minimale » (modele 6) : gabarit fixe commun a toutes les notices (mm depuis le HAUT, logo et bandeau depuis le bas) ----
COVER_NAME, COVER_SUB, COVER_LANG = "PHASE 90", "Phaser analogique", "FRANÇAIS"
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm
NAME_TOP, NAME_PT = 194 * mm, 30
SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm
BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        t = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); t.setFont(font, size); t.setCharSpace(cs)
        t.setFillColor(col); t.textOut(text); c.drawText(t)
    line(COVER_LANG, LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw = iw / 1.32; pad = int(cw * 0.16); ch = (ih - pad) / 1.2            # geometrie de p9_cover.png
    k = min(PEDAL_H / ch, PEDAL_MAXW / cw)
    dw, dh = iw * k, ih * k
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch * k) / 2) + pad * k
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line(COVER_NAME, NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line(COVER_SUB, SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
doc.build(f)
print(OUT)
