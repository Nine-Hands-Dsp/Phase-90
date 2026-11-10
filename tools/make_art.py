"""
PHASE 90 (NINE HANDS | DSP) - visuel du plugin, refonte nov. 2026 selon les regles NINE HANDS | DSP.

Base : le visuel de l'utilisateur (design/source/phase90_design.webp, 2048 x 2048), qui fait foi.
  1. Format des pedales simples : image 1235 x 1800 px, boitier plein cadre en hauteur, embases jack aux bords.
     Le visuel est plus etroit (910 x 1636 px, rapport 0,556) que le format (boitier 1149 x 1800, rapport 0,638) :
     rien n'est etire. Les elements gardent leur taille (echelle unique s) ; le boitier s'elargit dans deux bandes
     verticales sans element vertical (x 746-776 et 1284-1318 du visuel). Dans ces bandes, seule la partie basse
     frequence selon x (lignes horizontales, eclairage) est etiree ; la texture fine (brossage vertical du panneau
     noir, grain de l'orange) est refaite avec des colonnes prises au hasard dans le visuel voisin.
  2. Tout ce qui bouge, s'allume ou s'ecrit est efface du fond puis refait :
     potard SPEED (composant nh::Knob, calques extraits du visuel), graduations (blanches : vectoriel ; grasses :
     lentilles allumees / eteintes), footswitch (photo du kit NINE HANDS | DSP) et son anneau lumineux,
     textes SPEED / PHASE / 90 / OUTPUT / INPUT et logo (vectoriel Poppins + NineHandsLogo.svg, dessines par le plugin),
     jacks du visuel remplaces par les embases photo du kit (IN a droite, OUT a gauche).
  3. Lumieres : chaque lumiere a sa source (jamais dosee) et son halo (dose par le reglage Glow 25-100 %).
Une seule lumiere pour toute la pedale : en haut a gauche (ombres portees vers le bas a droite).
Usage : python3 tools/make_art.py   (sorties a la racine du depot + design/)
"""
import os, sys, math, json
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import photo_controls as PC

OUT_W, OUT_H = 1235, 1800
SRC = os.path.join(ROOT, 'design', 'source', 'phase90_design.webp')
D = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)

# ------------------------------------------------------------------ 1. geometrie : visuel -> image finale
BX0, BX1, BY0, BY1 = 570.0, 1479.5, 196.5, 1832.5          # boitier (arete chromee exterieure) dans le visuel
BY_RIM = 1862.0                                             # bas de la tranche sombre du boitier (sous l'orange) dans le visuel
S = OUT_H / (BY1 - BY0)                                     # echelle unique (x et y)
JACK_LEN_PX = 104.0 * 2 * S * 0.93                          # longueur des embases (le long de la tranche), px de l'image finale
JACK_PROT = PC.jack_sprite(JACK_LEN_PX / 2.0, 2, 1)[1] * 2 - 3.0   # saillie hors du boitier (px)
TX0, TX1 = JACK_PROT, OUT_W - JACK_PROT                     # boitier dans l'image finale
DCX = (BX0 + BX1) / 2
STRIPS = [(746.0, 776.0), (1284.0, 1318.0)]                 # bandes elargies (visuel)

def x_fwd(xd):
    """x du visuel -> x de l'image finale (continue, lineaire par morceaux)"""
    a0, a1 = STRIPS[0]; b0, b1 = STRIPS[1]
    tl = lambda x: TX0 + (x - BX0) * S
    tc = lambda x: OUT_W / 2 + (x - DCX) * S
    tr = lambda x: TX1 - (BX1 - x) * S
    if xd <= a0: return tl(xd)
    if xd <= a1: return tl(a0) + (xd - a0) / (a1 - a0) * (tc(a1) - tl(a0))
    if xd <= b0: return tc(xd)
    if xd <= b1: return tc(b0) + (xd - b0) / (b1 - b0) * (tr(b1) - tc(b0))
    return tr(xd)

def y_fwd(yd): return (yd - BY0) * S

# table inverse x (image finale -> visuel)
_xs_d = np.linspace(0, 2047, 40000)
_xs_t = np.array([x_fwd(x) for x in _xs_d])
def x_inv(xt): return np.interp(xt, _xs_t, _xs_d)
# bas de la pedale : la tranche du bas du visuel (BY1 -> BY_RIM) doit tenir dans l'image -> on retire une bande
# horizontale d'orange uni (entre la cuvette du footswitch et « 90 », seuls les traits verticaux du cadre la traversent)
Y_CUT = 1515.0                                              # image finale : debut de la bande retiree
CUT = (BY_RIM - BY1) * S                                    # hauteur retiree (px de l'image finale)
def y_inv(yt):
    yt = np.asarray(yt, dtype=np.float64)
    return np.where(yt < Y_CUT, yt, yt + CUT) / S + BY0

def P(xd, yd): return (x_fwd(xd), y_fwd(yd))

def warp_design():
    """visuel elargi : basse frequence selon x etiree, texture fine refaite dans les bandes"""
    lf = cv2.GaussianBlur(D, (0, 0), sigmaX=5.0, sigmaY=0.01)
    hf = D - lf
    xt = np.arange(OUT_W, dtype=np.float32) + 0.5
    yt = np.arange(OUT_H, dtype=np.float32) + 0.5
    mx = x_inv(xt).astype(np.float32); my = y_inv(yt).astype(np.float32)
    MX, MY = np.meshgrid(mx, my)
    out_lf = cv2.remap(lf, MX, MY, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    out_hf = cv2.remap(hf, MX, MY, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # dans les bandes elargies : texture fine = colonnes prises au hasard pres de la bande (meme hauteur)
    rng = np.random.default_rng(90)
    for (a0, a1), pool in zip(STRIPS, [(746.0, 768.0), (1290.0, 1318.0)]):
        t0, t1 = x_fwd(a0), x_fwd(a1)
        for xi in range(int(math.floor(t0)) - 1, int(math.ceil(t1)) + 2):
            if xi < 0 or xi >= OUT_W: continue
            # poids : 1 au coeur de la bande, fondu sur 4 px aux bords
            wgt = np.clip(min(xi - t0, t1 - xi) / 4.0 + 0.5, 0, 1)
            if wgt <= 0: continue
            xs = rng.uniform(*pool)
            col = cv2.remap(hf, np.full((OUT_H, 1), xs, np.float32), my.reshape(-1, 1), cv2.INTER_LINEAR)
            out_hf[:, xi] = out_hf[:, xi] * (1 - wgt) + col.reshape(OUT_H, 3) * wgt
    return np.clip(out_lf + out_hf, 0, 255)

if __name__ == '__main__' and 'warp' in sys.argv:
    w = warp_design()
    Image.fromarray(w.astype(np.uint8)).save('/tmp/claude-0/p9/warp.png')
    print('S', S, 'JACK_PROT', JACK_PROT, 'strips', [(x_fwd(a), x_fwd(b)) for a, b in STRIPS])


# ------------------------------------------------------------------ 2. reperes (image finale, px) mesures sur le visuel elargi
KNOB_C = (614.5, 344.5); KNOB_R = 215.5                     # potard SPEED : axe (sommet du cone de metal tourne) et silhouette
TICK_C = (615.0, 343.0)                                      # graduations : 41 traits tous les 7,5 deg de -150 a +150
TICK_SMALL = (231.0, 252.0, 2.2)                             # rayon int., rayon ext., demi-largeur (blancs)
TICK_BOLD = (232.0, 261.0, 6.0)                              # graduations grasses (lentilles orange) tous les 30 deg
FS_OLD = (613.5, 1332.0)                                     # footswitch du visuel (efface)
FS_C = (616.5, 1303.5)                                       # footswitch : centre du cercle orange de la collerette (mesure)
PHASE_BOX = (345.0, 752.0, 890.0, 962.0)                     # cartouche PHASE (contour orange, exterieur)
PRESET = (617.5 - 400.0, 1060.0 - 38.0, 800.0, 76.0)         # pastille presets / ligne d'etat (400 x 38 unites)
SYNC_C, SYNC_R = (902.0, 552.0), 30.0                        # bouton SYNC, en bas a droite du potard
JACK_Y = 852.0                                               # embases jack, a la hauteur de OUTPUT / INPUT
TEXTS = [  # texte, police (0 medium, 1 bold, 2 light, 3 regular), hauteur des capitales (px), espacement (px), x, y, rotation
    ('SPEED', 3, 40.0, 3.0, 617.5, 603.0, 0.0),
    ('PHASE', 1, 82.0, 6.0, 617.5, 857.0, 0.0),
    ('OUTPUT', 3, 28.0, 2.5, 122.0, 848.0, -90.0),
    ('INPUT', 3, 28.0, 2.5, 1108.0, 852.0, 90.0),
    ('90', 2, 84.0, 4.0, 617.5, 1575.0, 0.0),
]
LOGO_C, LOGO_W = (617.5, 1668.0), 300.0

def column_fill(img, mask):
    """remplit le masque colonne par colonne (brossage vertical) entre les pixels valides au-dessus et en dessous"""
    out = img.copy()
    H_, W_ = mask.shape
    for x in range(W_):
        col = mask[:, x]
        if not col.any(): continue
        ys = np.where(col)[0]
        # morceaux contigus
        breaks = np.where(np.diff(ys) > 1)[0]
        starts = np.r_[ys[0], ys[breaks + 1]]; ends = np.r_[ys[breaks], ys[-1]]
        for y0, y1 in zip(starts, ends):
            a = out[max(0, y0 - 9):max(1, y0 - 3), x].mean(0) if y0 > 9 else out[y1 + 4:y1 + 10, x].mean(0)
            b = out[y1 + 4:min(H_, y1 + 10), x].mean(0) if y1 < H_ - 10 else a
            t = ((np.arange(y0, y1 + 1) - y0 + 1) / (y1 - y0 + 2))[:, None]
            out[y0:y1 + 1, x] = a * (1 - t) + b * t
    return out

def grain_fill(img, mask, src_box, seed=1, base=None, feather=1.2):
    """remplit (zone orange) : teinte basse frequence par inpainting (ou base donnee) + grain repris d'une zone propre"""
    m8 = (mask * 255).astype(np.uint8)
    if base is None:
        low = cv2.GaussianBlur(img, (0, 0), 3.0)
        inp = np.dstack([cv2.inpaint(np.clip(low[..., c], 0, 255).astype(np.uint8), m8, 9, cv2.INPAINT_TELEA) for c in range(3)]).astype(np.float32)
        inp = cv2.GaussianBlur(inp, (0, 0), 2.0)
    else:
        inp = base
    x0, y0, x1, y1 = src_box
    patch = img[y0:y1, x0:x1]; patch = patch - cv2.GaussianBlur(patch, (0, 0), 3.0)
    ph, pw = patch.shape[:2]
    rng = np.random.default_rng(seed)
    H_, W_ = mask.shape
    tex = np.zeros_like(img)
    for ty in range(0, H_, ph // 2):
        for tx in range(0, W_, pw // 2):
            if not mask[ty:ty + ph, tx:tx + pw].any(): continue
            oy, ox = rng.integers(0, ph // 2), rng.integers(0, pw // 2)
            p = patch[oy:oy + ph // 2, ox:ox + pw // 2]
            tex[ty:ty + p.shape[0], tx:tx + p.shape[1]] = p[:H_ - ty, :W_ - tx]
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), feather)
    if feather <= 2.0: soft = np.maximum(soft, mask.astype(np.float32))
    soft = soft[..., None]
    return img * (1 - soft) + (inp + tex) * soft

def text_mask(img, box, kind):
    """masque des lettres d'un texte du visuel (sombres sur orange ou claires sur noir), un peu dilate"""
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1]
    if kind == 'dark':
        loc = cv2.GaussianBlur(reg, (0, 0), 6)
        m = (reg.mean(2) < loc.mean(2) - 9)
    elif kind == 'light':
        m = reg.min(2) > 70
    else:   # lettres orange
        m = (reg[..., 0] > 70) & (reg[..., 0] - reg[..., 2] > 30)
    m = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=3).astype(bool)
    full = np.zeros(img.shape[:2], bool); full[y0:y1, x0:x1] = m
    return full

def erase_all(W_):
    Hh, Ww = W_.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    # potard + graduations + leur halo + SPEED : panneau noir brosse refait colonne par colonne
    m = (np.hypot(xx - TICK_C[0], yy - TICK_C[1]) < 284.0) & (yy > 72)
    m |= (xx > 495) & (xx < 740) & (yy > 565) & (yy < 668)
    B = column_fill(W_, m)
    # lettres PHASE (interieur du cartouche, brosse vertical)
    B = column_fill(B, (xx > 382) & (xx < 853) & (yy > 791) & (yy < 927))
    # reflet orange a gauche du cartouche PHASE (visuel asymetrique) : panneau noir brosse refait
    B = column_fill(B, (xx > 290) & (xx < 347) & (yy > 740) & (yy < 970))
    # textes sombres sur l'orange : OUTPUT, INPUT, 90
    tm = np.zeros(B.shape[:2], bool)
    for x0, y0, x1, y1 in ((500, 1512, 740, 1640),):
        tm[y0:y1, x0:x1] = True
    # bandes orange des cotes (OUTPUT / INPUT) : tout l'orange de la zone, pour ne garder aucune trace des lettres
    Lw = W_.mean(2)
    panel = cv2.morphologyEx((Lw < 45).astype(np.uint8), cv2.MORPH_OPEN, np.ones((17, 17), np.uint8)).astype(bool)
    side = np.zeros_like(tm)
    for x0, y0, x1, y1 in ((74, 110, 178, 1190), (1056, 110, 1162, 1190)):
        side[y0:y1, x0:x1] = True
    letters = np.zeros_like(tm)
    for x0, y0, x1, y1 in ((74, 680, 178, 1025), (1056, 690, 1162, 1020)):
        letters[y0:y1, x0:x1] = True
    hue = (W_[..., 0] - W_[..., 2]) > 60
    side &= hue | (letters & ~panel)
    side &= ~cv2.dilate(panel.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & (Lw < 200)   # liseré clair du bord garde,   # ni le panneau noir ni le chrome
    side = cv2.erode(side.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    # teinte : profil horizontal de la bande, pris colonne par colonne sous la zone (bande droite et propre)
    lowB = cv2.GaussianBlur(B, (0, 0), 2.0)
    base = B.copy()
    for x0, x1 in ((74, 178), (1056, 1162)):
        prof = np.median(lowB[1035:1110, x0:x1], axis=0)
        base[:, x0:x1] = prof[None, :, :]
    base = cv2.GaussianBlur(base, (0, 0), 1.0)
    B = grain_fill(B, side, (300, 1570, 460, 1670), seed=4, base=base, feather=3.0)
    return grain_fill(B, tm, (300, 1570, 460, 1670), feather=7.0)

if __name__ == '__main__' and 'erase' in sys.argv:
    B = erase_all(warp_design())
    Image.fromarray(np.clip(B, 0, 255).astype(np.uint8)).save('/tmp/claude-0/p9/erased.png')


# ------------------------------------------------------------------ 3. lumieres, footswitch, jacks, detourage
RING_R0, RING_R1 = 113.0, 149.0                              # ancien anneau lumineux du visuel (efface)
GRAIN_BOX = (200, 1450, 360, 1570)                           # orange propre (grain repris pour la collerette du footswitch)
FS_FLATS = 206.0                                             # footswitch photo : distance entre plats (px)

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

DOME_R = 163.0                                               # cercle orange de la collerette (bord sur le panneau noir)
ARC_R, ARC_W = 172.5, 7.0                                    # arc grave autour de la collerette (visuel), rayon / largeur
ARC_SPANS = ((15.0, 86.0), (94.0, 165.5))                    # degres (0 = droite, 90 = bas) : coupe au milieu en bas
DASHES = ((392, 1295, 450, 1352), (782, 1295, 840, 1352))    # traits ||| de part et d'autre (gardes)

def engrave_arc(img, C):
    """arc grave sombre, net (sur-echantillonne x3), arete claire du cote oppose a la lumiere"""
    SS = 3
    x0, y0 = int(C[0] - ARC_R - 12), int(C[1] - 20)
    x1, y1 = int(C[0] + ARC_R + 12), int(C[1] + ARC_R + 12)
    yy, xx = np.mgrid[y0 * SS:y1 * SS, x0 * SS:x1 * SS].astype(np.float32) / SS + 0.5 / SS
    dx, dy = xx - C[0], yy - C[1]
    r = np.hypot(dx, dy); a = np.degrees(np.arctan2(dy, dx))
    a = np.where(a < -90, a + 360, a)
    def arc(rad, w):
        cov = np.zeros_like(r)
        for a0, a1 in ARC_SPANS:
            ang = np.clip(a, a0, a1)
            px = C[0] + rad * np.cos(np.radians(ang)); py = C[1] + rad * np.sin(np.radians(ang))
            d = np.hypot(xx - px, yy - py)
            cov = np.maximum(cov, np.clip(w / 2 - d + 0.5 / SS * SS * 0.5, 0, 1))
        return cov
    groove = arc(ARC_R, ARC_W)
    lip = arc(ARC_R + 2.3, 1.4) * (1 - groove)
    def down(m): return cv2.resize(m, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    g_, l_ = down(groove)[..., None], down(lip)[..., None]
    reg = img[y0:y1, x0:x1]
    reg = reg * (1 - 0.32 * l_) + np.minimum(reg * 1.25 + 18, 255) * 0.32 * l_
    reg = reg * (1 - 0.92 * g_) + np.array([24.0, 9.0, 3.0]) * 0.92 * g_
    out = img.copy(); out[y0:y1, x0:x1] = reg
    return out

FRAME_IN = (124.0, 1328.0, 1111.0, 1716.0, 74.0)             # interieur du cadre grave du bas (x0, y0, x1, y1, pan coupe)

def clean_bottom(B):
    """bas de la pedale : interieur du cadre grave + collerette refaits d'un seul tenant (eclairage doux ajuste,
    plus d'ombre portee ni de taches du visuel), grain repris d'une zone propre, puis arc grave redessine"""
    Hh, Ww = B.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    x0, y0, x1, y1, ch = FRAME_IN
    poly = (xx > x0) & (xx < x1) & (yy > y0) & (yy < y1)
    for cx_, cy_, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        poly &= (sx * (xx - cx_) + sy * (yy - cy_)) > ch                  # coins coupes (pans du cadre)
    r = np.hypot(xx - FS_C[0], yy - FS_C[1])
    dash = np.zeros_like(poly)
    for a0, b0, a1, b1 in DASHES:
        dash |= (xx > a0 - 6) & (xx < a1 + 6) & (yy > b0 - 6) & (yy < b1 + 6)
    dash &= B.mean(2) < 42.0                                             # seulement les traits ||| eux-memes
    dash = cv2.dilate(dash.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    region = (poly | (r < DOME_R - 5.0) | ((r < 205.0) & (yy > 1284.0))) & ~dash
    # eclairage : polynome de degre 2 ajuste sur l'orange propre (on ecarte les pixels trop sombres = ombres)
    low = cv2.GaussianBlur(B, (0, 0), 4.0)
    ys_, xs_ = np.where(poly & ~dash & (r > 200))
    sel = np.random.default_rng(3).choice(len(xs_), min(40000, len(xs_)), replace=False)
    X = xs_[sel].astype(np.float64) / Ww; Y = ys_[sel].astype(np.float64) / Hh
    A = np.c_[np.ones_like(X), X, Y, X * X, X * Y, Y * Y]
    V = low[ys_[sel], xs_[sel]].astype(np.float64)
    keep = np.ones(len(X), bool)
    for _ in range(3):
        coef = np.linalg.lstsq(A[keep], V[keep], rcond=None)[0]
        res = (V - A @ coef).mean(1)
        keep = res > -5.0
    Xg = xx / Ww; Yg = yy / Hh
    base = np.stack([coef[0, c] + coef[1, c] * Xg + coef[2, c] * Yg + coef[3, c] * Xg * Xg + coef[4, c] * Xg * Yg + coef[5, c] * Yg * Yg
                     for c in range(3)], -1).astype(np.float32)
    clean = grain_fill(B, region, GRAIN_BOX, seed=11, base=base, feather=0.01)
    w_ = cv2.GaussianBlur(region.astype(np.float32), (0, 0), 3.0)
    w_ = np.maximum(w_, cv2.erode(region.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32))
    out = B * (1 - w_[..., None]) + clean * w_[..., None]
    return out

def smooth_panel_edge(B, y0=1095.0, y1=1305.0):
    """bas du panneau noir (bords droits, arrondis, tour de la collerette) : bord et liseré clair redessines a partir
    d'un profil moyen pris sur une portion propre, en fonction de la distance au bord (plus de crenelage ni de points)"""
    Hh, Ww = B.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    L = cv2.GaussianBlur(B.mean(2), (0, 0), 1.0)
    m = cv2.GaussianBlur((L < 50).astype(np.float32), (0, 0), 3.5) > 0.5
    m8 = m.astype(np.uint8)
    sdf = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5) - cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    sdf = cv2.GaussianBlur(sdf, (0, 0), 1.2)                              # > 0 cote orange
    zone = (yy > y0) & (yy < y1) & (xx > 80) & (xx < Ww - 80)
    # bords des bandes OUTPUT / INPUT : liseré clair continu jusqu'au debut de la courbe du haut
    zone |= (yy > 735.0) & (yy < y1) & ((xx < 200) | (xx > Ww - 200)) & (xx > 60) & (xx < Ww - 60)
    ref = (xx > 185) & (xx < 380) & (yy > 1240) & (yy < 1305)
    bins = np.arange(-6.0, 12.01, 0.5)
    prof = []
    for b in bins:
        sel = ref & (np.abs(sdf - b) < 0.25)
        prof.append(np.median(B[sel], axis=0) if sel.sum() > 20 else np.array([np.nan] * 3))
    prof = np.array(prof)
    for c in range(3):
        ok = ~np.isnan(prof[:, c]); prof[:, c] = np.interp(bins, bins[ok], prof[ok, c])
    prof = np.stack([cv2.GaussianBlur(prof[:, c].reshape(-1, 1).astype(np.float32), (1, 0), 0.8).ravel() for c in range(3)], -1)
    band = zone & (sdf > -6) & (sdf < 12)
    new = np.stack([np.interp(sdf, bins, prof[:, c]) for c in range(3)], -1).astype(np.float32)
    grain = B - cv2.GaussianBlur(B, (0, 0), 1.5)
    new = new + grain * np.clip((sdf - 3.0) / 3.0, 0, 1)[..., None] * 0.8    # grain de l'orange garde loin du bord
    w_ = band * np.clip(1 - (np.abs(sdf - 3.0) - 6.0) / 2.5, 0, 1)
    w_ = cv2.GaussianBlur(w_.astype(np.float32), (0, 0), 0.8) * cv2.GaussianBlur(zone.astype(np.float32), (0, 0), 6.0)
    return B * (1 - w_[..., None]) + new * w_[..., None]

# traits ||| de part et d'autre de la collerette (mesures sur le visuel) : (x haut, y haut, x bas, y bas), largeur 7
BARS_L = [(399.0, 1315.0, 403.0, 1346.0), (414.5, 1315.0, 418.5, 1346.0), (430.0, 1315.0, 434.0, 1346.0), (445.5, 1315.0, 450.0, 1349.0)]
BARS_R = [(836.0 - k * 15.5, 1318.0, 831.5 - k * 15.5, 1349.0) for k in range(3)] + [(786.5, 1318.0, 782.0, 1351.0)]
# le dernier trait de chaque cote se termine exactement au depart de l'arc (meme ligne, sans decalage)
def _arc_pt(deg): return (616.5 + 172.5 * math.cos(math.radians(deg)), 1303.5 + 172.5 * math.sin(math.radians(deg)))
BARS_L[-1] = (BARS_L[-1][0] + 0.5, BARS_L[-1][1]) + _arc_pt(165.5)
BARS_R[-1] = (BARS_R[-1][0] + 1.0, BARS_R[-1][1]) + _arc_pt(15.0)
BAR_W = 7.0
INK = np.array([20.0, 2.0, 0.0]); LIP = np.array([224.0, 135.0, 86.0])

def engrave_details(B):
    """traits ||| et arc de la collerette redessines nets (sur-echantillonnes x4) : creux sombre et arete claire en bas
    a droite (lumiere en haut a gauche), meme rendu que les traits du cadre ; l'arc a l'epaisseur des traits"""
    Hh, Ww = B.shape[:2]
    # effacement des traits du visuel
    er = np.zeros((Hh, Ww), bool)
    for x0, y0, x1, y1 in ((388, 1306, 458, 1362), (774, 1308, 846, 1364)):
        er[y0:y1, x0:x1] = True
    B = grain_fill(B, er, GRAIN_BOX, seed=21, feather=1.2)
    SS = 4
    def render(x0, y0, x1, y1, cov_fn):
        yy, xx = np.mgrid[y0 * SS:y1 * SS, x0 * SS:x1 * SS].astype(np.float32) / SS + 0.5 / SS
        core = cov_fn(xx, yy)
        lip = cov_fn(xx - 1.1, yy - 1.4) * (1 - core)
        d = lambda m: cv2.resize(m, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)[..., None]
        reg = B[y0:y1, x0:x1]
        reg = reg * (1 - 0.75 * d(lip)) + LIP * 0.75 * d(lip)
        reg = reg * (1 - 0.95 * d(core)) + INK * 0.95 * d(core)
        B[y0:y1, x0:x1] = reg
    def seg_cov(segs, w):
        def f(xx, yy):
            cov = np.zeros_like(xx)
            for ax, ay, bx, by in segs:
                vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
                t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / L2, 0, 1)
                dd = np.hypot(xx - (ax + t * vx), yy - (ay + t * vy))
                cov = np.maximum(cov, np.clip(w / 2 - dd + 0.5 / SS, 0, 1))
            return cov
        return f
    def arc_cov(xx, yy):
        C = FS_C
        a = np.degrees(np.arctan2(yy - C[1], xx - C[0])); a = np.where(a < -90, a + 360, a)
        cov = np.zeros_like(xx)
        for a0, a1 in ARC_SPANS:
            ang = np.radians(np.clip(a, a0, a1))
            dd = np.hypot(xx - (C[0] + ARC_R * np.cos(ang)), yy - (C[1] + ARC_R * np.sin(ang)))
            cov = np.maximum(cov, np.clip(BAR_W / 2 - dd + 0.5 / SS, 0, 1))
        return cov
    def both(xx, yy):
        return np.maximum(np.maximum(seg_cov(BARS_L, BAR_W)(xx, yy), seg_cov(BARS_R, BAR_W)(xx, yy)), arc_cov(xx, yy))
    x0, y0 = int(FS_C[0] - ARC_R - 75), 1300
    x1, y1 = int(FS_C[0] + ARC_R + 75), int(FS_C[1] + ARC_R + 12)
    render(x0, y0, x1, y1, both)
    return B

def ring_layers(D_lit, B, C=None, R0=None, R1=None, collar=True, diffuser=True):
    """anneau du footswitch : fond eteint (dans B) + source allumee + halo (calques alpha)"""
    C = FS_C if C is None else C
    RING_R0 = globals()['RING_R0'] if R0 is None else R0
    RING_R1 = globals()['RING_R1'] if R1 is None else R1
    Hh, Ww = B.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    dx, dy = xx - C[0], yy - C[1]
    r = np.hypot(dx, dy)
    band = sstep(RING_R0 - 1.2, RING_R0 + 1.2, r) * (1 - sstep(RING_R1 - 1.2, RING_R1 + 1.2, r))
    # --- collerette (r > RING_R1) : le visuel est eclaire par l'anneau -> version eteinte
    near = (r > RING_R1 - 2) & (r < (260 if collar else RING_R1 + 40))
    lum = D_lit.mean(2)
    orange = (D_lit[..., 0] - D_lit[..., 2] > 70) & near
    fall = np.exp(-np.clip(r - RING_R1, 0, None) / 30.0)
    off = B.copy()
    if collar:
        # orange sans lumiere : teinte basse frequence reprise de l'orange non eclaire (inpainting), detail fin en rapport
        lowd = cv2.GaussianBlur(D_lit, (0, 0), 4.0)
        plain = (D_lit[..., 0] - D_lit[..., 2] > 120) & (D_lit[..., 1] < 105) & (D_lit[..., 1] > 55)
        glowzone = ((r < 215) | ~plain).astype(np.uint8) * 255
        inp = np.dstack([cv2.inpaint(np.clip(lowd[..., c], 0, 255).astype(np.uint8), glowzone, 15, cv2.INPAINT_TELEA)
                         for c in range(3)]).astype(np.float32)
        inp = cv2.GaussianBlur(inp, (0, 0), 6.0)
        ratio = np.clip(D_lit / np.maximum(lowd, 1.0), 0.6, 1.4)
        off_or = np.clip(inp * ratio, 0, 255)
        spill = (D_lit[..., 1] > 115) & (r < 185) & (r > RING_R1 - 2)    # lumiere de l'anneau du visuel
        w_or = ((orange | spill) & (r < 215)).astype(np.float32)
        w_or = cv2.GaussianBlur(w_or, (0, 0), 1.0)
        off = off * (1 - w_or[..., None]) + np.minimum(off_or, off) * w_or[..., None]
    # zones sombres (baie noire, gravures) : on retire la dominante chaude de la lumiere
    dark = (~orange) & near
    warm = np.clip((D_lit[..., 0] - D_lit[..., 2]) / 120.0, 0, 1) * fall
    neutral = np.repeat(lum[..., None], 3, 2) * np.array([1.0, 0.97, 0.98]) * 0.75
    wd = (dark * warm)[..., None] * (1.0 if collar else 0.0)
    off = off * (1 - wd) + np.minimum(neutral, off) * wd
    # --- diffuseur eteint : acrylique fume, eclaire en haut a gauche, bords plus sombres (siege)
    t = np.clip((r - RING_R0) / (RING_R1 - RING_R0), 0, 1)
    face = 1 - (2 * t - 1) ** 2                                   # bombe
    ang = np.arctan2(dy, dx)
    lite = 0.5 + 0.5 * np.cos(ang - math.radians(-135))           # cote de la lumiere (haut gauche)
    base = np.array([74.0, 64.0, 58.0])                           # acrylique opale fume, teinte chaude
    dif = base * (0.50 + 0.55 * face)[..., None] + (46.0 * lite * face ** 2)[..., None] * np.array([1.0, 0.96, 0.92])
    dif = dif * (1 - 0.35 * (1 - sstep(0.0, 0.12, t)) - 0.30 * sstep(0.86, 1.0, t))[..., None]   # sieges sombres
    spec = np.exp(-((t - 0.36) / 0.09) ** 2) * np.clip(np.cos(ang - math.radians(-135)), 0, 1) ** 5 * 85.0
    dif = dif + spec[..., None]
    rng = np.random.default_rng(7)
    dif = dif + rng.normal(0, 1.4, (Hh, Ww, 1))
    if diffuser:
        off = off * (1 - band[..., None]) + dif * band[..., None]
    else:
        # footswitch facon Octopus : plus de diffuseur ni de cuvette ; l'ecrou est pose sur l'orange uni de la
        # collerette (meme centre que le cercle orange). La lumiere est l'anneau fin dessine par le plugin dans la gorge.
        # Collerette et zone orange autour refaites en entier (plus d'ombres ni de taches du visuel), puis arc grave
        # concentrique redessine.
        inside = r < DOME_R - 5.0
        dash = np.zeros_like(r, bool)
        for x0, y0, x1, y1 in DASHES:
            dash |= (xx > x0 - 5) & (xx < x1 + 5) & (yy > y0 - 5) & (yy < y1 + 5)
        frame = (yy < 1368.0) & ((xx < 456.0) | (xx > 778.0))          # traits du cadre de part et d'autre (gardes)
        lower = (r < 265.0) & (yy > 1286.0) & ~dash & ~frame
        ob = inside | lower
        ring_ = (r > 270.0) & (r < 290.0) & (yy > 1380.0)
        flat = np.median(D_lit[ring_], axis=0)                           # orange uni de la facade autour
        src_ = cv2.GaussianBlur(off, (0, 0), 3.0)
        top_ring = (r >= DOME_R - 14.0) & (r < DOME_R + 10.0) & (yy < 1286.0)
        src_[top_ring] = flat                                            # bord de la collerette sur le noir : ignore
        q = 4
        sm = cv2.resize(src_, (Ww // q, Hh // q), interpolation=cv2.INTER_AREA)
        mm = cv2.resize(ob.astype(np.uint8) * 255, (Ww // q, Hh // q), interpolation=cv2.INTER_NEAREST)
        mm = cv2.dilate(mm, np.ones((3, 3), np.uint8))
        lo = np.dstack([cv2.inpaint(np.clip(sm[..., c], 0, 255).astype(np.uint8), mm, 12, cv2.INPAINT_TELEA) for c in range(3)]).astype(np.float32)
        lo = cv2.GaussianBlur(lo, (0, 0), 3.0)
        base = cv2.resize(lo, (Ww, Hh), interpolation=cv2.INTER_CUBIC)
        clean = grain_fill(off, ob, GRAIN_BOX, seed=5, base=base, feather=0.01)
        w_ = cv2.GaussianBlur(ob.astype(np.float32), (0, 0), 5.0)
        w_ = np.where(inside & (r < DOME_R - 12.0), 1.0, w_)
        off = off * (1 - w_[..., None]) + clean * w_[..., None]
    # creux sous le footswitch (cache par l'ecrou)
    hole = (1 - sstep(RING_R0 - 3, RING_R0 - 0.5, r)) * (1.0 if diffuser else 0.0)
    off = off * (1 - hole[..., None]) + np.array([8.0, 7.0, 7.0]) * hole[..., None]
    # --- source allumee : diffuseur blanc chaud au centre de la bande, orange vers les bords
    hot = np.array([255.0, 246.0, 222.0]); edge = np.array([255.0, 150.0, 60.0])
    core = edge * (1 - face[..., None] ** 1.6) + hot * face[..., None] ** 1.6
    core = core * (0.93 + 0.07 * lite)[..., None]
    src = np.dstack([core, band * 255])
    # --- halo : la facade recoit la lumiere de l'anneau (serre + large et faible), symetrique
    d_ = np.clip(r - RING_R1, 0, None)
    lim = 320.0 if collar else RING_R1 + 70.0
    outside = sstep(RING_R1 - 0.5, RING_R1 + 1.5, r) * (1 - sstep(lim * 0.6, lim, r))
    ks = (RING_R1 - RING_R0) / 36.0                               # echelle du halo (petit anneau = halo plus court)
    ks = 0.45 + 0.55 * ks
    a_h = np.clip(0.80 * np.exp(-d_ / (6.0 * ks)) + 0.42 * np.exp(-d_ / (26.0 * ks)) + 0.10 * np.exp(-d_ / (80.0 * ks)), 0, 0.95) * outside
    mixc = np.exp(-d_ / (14.0 * ks))[..., None]
    col = np.array([255.0, 214.0, 150.0]) * mixc + np.array([255.0, 128.0, 40.0]) * (1 - mixc)
    halo = np.dstack([col, a_h * 255])
    return off, src, halo

def bold_tick_layers(B):
    """graduations grasses : lentilles eteintes (dans le fond), source allumee et halo"""
    Hh, Ww = B.shape[:2]
    SS = 3
    yy, xx = np.mgrid[0:Hh * SS, 0:Ww * SS].astype(np.float32) / SS
    r0, r1, hw = TICK_BOLD
    pill = np.zeros((Hh * SS, Ww * SS), np.float32); along = np.zeros_like(pill); across = np.zeros_like(pill)
    lit_side = np.zeros_like(pill)
    for k in range(-5, 6):
        a = math.radians(30.0 * k)
        ux, uy = math.sin(a), -math.cos(a)                       # radial
        px, py = xx - TICK_C[0], yy - TICK_C[1]
        u = px * ux + py * uy; v = px * (-uy) + py * ux
        rc = (r0 + r1) / 2; hl = (r1 - r0) / 2
        q = np.hypot(np.maximum(np.abs(u - rc) - (hl - hw), 0), 0) 
        dd = np.hypot(np.maximum(np.abs(u - rc) - (hl - hw), 0), v) - hw        # capsule
        m = np.clip(0.5 - dd * SS, 0, 1)
        sel = m > pill
        pill = np.maximum(pill, m)
        along = np.where(sel, np.clip(1 - np.abs(u - rc) / hl, 0, 1), along)
        across = np.where(sel, np.clip(1 - np.abs(v) / hw, 0, 1), across)
        lit_side = np.where(sel, np.clip(-(v) / hw * 0.5 + 0.5, 0, 1) * 0 + np.clip((-u + rc) / hl * 0.5 + 0.5, 0, 1), lit_side)
    down = lambda a: cv2.resize(a, (Ww, Hh), interpolation=cv2.INTER_AREA)
    pill_s, along_s, across_s = down(pill), down(along * pill) / np.maximum(down(pill), 1e-4), down(across * pill) / np.maximum(down(pill), 1e-4)
    # eteinte : lentille fumee, reflet fin du cote de la lumiere
    yy1, xx1 = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    ang = np.arctan2(yy1 - TICK_C[1], xx1 - TICK_C[0])
    lite = 0.5 + 0.5 * np.cos(ang - math.radians(-135))
    offc = np.array([40.0, 33.0, 30.0]) * (0.75 + 0.45 * across_s)[..., None] + (26.0 * lite * across_s ** 2)[..., None]
    seat = cv2.GaussianBlur(pill_s, (0, 0), 1.6) * 0.55
    Bo = B * (1 - seat[..., None] * 0.6)
    Bo = Bo * (1 - pill_s[..., None]) + offc * pill_s[..., None]
    # allumee : coeur presque blanc, corps orange
    hotness = np.clip(across_s ** 0.6 * (0.7 + 0.3 * along_s ** 0.4) * 1.35, 0, 1)
    core = np.array([255.0, 120.0, 34.0]) * (1 - hotness[..., None]) + np.array([255.0, 244.0, 222.0]) * hotness[..., None]
    src = np.dstack([core, pill_s * 255])
    # halo : lueur orange sur le panneau noir (serree + large et faible)
    g1 = cv2.GaussianBlur(pill_s, (0, 0), 3.5) * 1.15
    g2 = cv2.GaussianBlur(pill_s, (0, 0), 11.0) * 1.1
    a_h = np.clip(g1 * 1.5 + g2 * 0.95, 0, 0.97) * (1 - pill_s)
    hc = np.clip(g1 * 1.4, 0, 1)[..., None]
    halo = np.dstack([np.array([255.0, 100.0, 22.0]) * (1 - hc) + np.array([255.0, 170.0, 90.0]) * hc, a_h * 255])
    return Bo, src, halo

CORNER_R = {'tl': 120.0, 'tr': 110.0, 'bl': 120.0, 'br': 120.0}  # rayons des coins du boitier (px), mesures sur le chrome du visuel

def box_alpha(W_):
    """canal alpha du boitier : contour de l'arete chromee du visuel, lisse"""
    L = W_.mean(2)
    Hh, Ww = L.shape
    lefts, rights = np.zeros(Hh), np.zeros(Hh)
    for y in range(Hh):
        xs = np.where(L[y, int(TX0) - 2:int(TX1) + 3] > 30)[0]
        if len(xs) == 0: lefts[y], rights[y] = Ww / 2, Ww / 2; continue
        lefts[y] = xs[0] + int(TX0) - 2; rights[y] = xs[-1] + int(TX0) - 2 + 1
    lefts = np.maximum(lefts, TX0 - 0.5); rights = np.minimum(rights, TX1 + 0.5)
    # silhouette geometrique : cotes droits (mediane mesuree) + coins arrondis propres (le visuel a une ombre
    # sombre collee au coin haut gauche qui faisait un defaut sur l'arrondi du chrome)
    XL = float(np.median(lefts[300:1500])); XR = float(np.median(rights[300:1500]))
    ys = np.arange(Hh) + 0.5
    def inset(y, Rc, y_edge, down):
        d = (y_edge + Rc - y) if down else (y - (y_edge - Rc))
        d = np.clip(d, 0, Rc)
        return Rc - np.sqrt(np.maximum(Rc * Rc - d * d, 0))
    # lissage du bord (sauf aux extremites)
    # couverture exacte d'un rectangle a coins arrondis (distance signee), anticrenelee
    yy_, xx_ = np.mgrid[0:Hh, 0:Ww].astype(np.float32) + 0.5
    top, left = yy_ < Hh / 2, xx_ < Ww / 2
    Rc = np.where(top, np.where(left, CORNER_R['tl'], CORNER_R['tr']), np.where(left, CORNER_R['bl'], CORNER_R['br']))
    cx_ = np.clip(xx_, XL + Rc, XR - Rc); cy_ = np.clip(yy_, Rc, Hh - Rc)
    inner = (xx_ > XL + Rc) & (xx_ < XR - Rc) | (yy_ > Rc) & (yy_ < Hh - Rc)
    dist = np.where(inner, np.minimum.reduce([xx_ - XL, XR - xx_, yy_ + 1e3, Hh + 1e3 - yy_]),
                    Rc - np.hypot(xx_ - cx_, yy_ - cy_))
    a = np.clip(dist + 0.5, 0, 1)
    return a.astype(np.float32)

def place(dst_rgb, dst_a, spr, x0, y0):
    h, w = spr.shape[:2]
    X0, Y0 = int(round(x0)), int(round(y0))
    sx0, sy0 = max(0, -X0), max(0, -Y0)
    ex, ey = min(w, dst_rgb.shape[1] - X0), min(h, dst_rgb.shape[0] - Y0)
    a = spr[sy0:ey, sx0:ex, 3:4] / 255.0
    reg = dst_rgb[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex]
    dst_rgb[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex] = reg * (1 - a) + spr[sy0:ey, sx0:ex, :3] * a
    if dst_a is not None:
        ra = dst_a[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex]
        dst_a[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex] = ra * (1 - a[..., 0]) + a[..., 0]

def crop_layer(rgba, pad=2):
    a = rgba[..., 3]
    ys, xs = np.where(a > 0.5)
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + pad + 1)
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + pad + 1)
    return rgba[y0:y1, x0:x1], (int(x0), int(y0))

def save_rgba(path, rgba):
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA').save(path, optimize=True)

LED_R = 19.0                                                 # LED SYNC (photo de l'utilisateur, assets/kit/led_red_lit.png) : rayon de la lentille
SYNC_R1 = LED_R + 3.0                                        # zone cliquable / position de l'inscription

def led_layers():
    """LED de l'utilisateur (teintee orange comme le footswitch) a la place du bouton SYNC : eteinte (fond), allumee (source) et halo (dose par Glow)"""
    src = np.asarray(Image.open(os.path.join(ROOT, 'assets', 'kit', 'led_red_lit.png')).convert('RGBA')).astype(np.float32)
    n0 = src.shape[0]; R0_ = 47.0                                # lentille : disque de 94 px centre dans 150 px
    k = LED_R / R0_
    n = int(round(n0 * k)) | 1
    lit = cv2.resize(src, (n, n), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    rr = np.hypot(xx - n / 2, yy - n / 2)
    lens = np.clip(LED_R - rr + 0.5, 0, 1)
    lit[..., 3] = lit[..., 3] * lens
    # LED orange comme l'anneau du footswitch : la photo rouge sert de carte d'intensite
    inten = np.clip((lit[..., 0] * 0.55 + lit[..., 1] * 0.9 + lit[..., 2] * 0.2) / 255.0, 0, 1)[..., None]
    c0, c1, c2 = np.array([70.0, 18.0, 0.0]), np.array([255.0, 118.0, 26.0]), np.array([255.0, 214.0, 160.0])
    t1 = np.clip(inten / 0.55, 0, 1); t2 = np.clip((inten - 0.55) / 0.45, 0, 1)
    lit[..., :3] = (c0 * (1 - t1) + c1 * t1) * (1 - t2) + c2 * t2
    # eteinte : verre rouge sombre (meme lentille, sans lumiere interne), petit reflet fixe en haut a gauche
    off = lit.copy()
    lum = off[..., :3].mean(2, keepdims=True) / 255.0
    off[..., :3] = np.array([74.0, 30.0, 6.0]) * (0.35 + 0.65 * lum) + 6.0
    ang = np.arctan2(yy - n / 2, xx - n / 2)
    spec = np.exp(-(((xx - n / 2 + LED_R * 0.38) ** 2 + (yy - n / 2 + LED_R * 0.42) ** 2) / (2 * (LED_R * 0.18) ** 2)))
    off[..., :3] = off[..., :3] + spec[..., None] * 120.0
    off[..., 3] = 255.0 * lens
    # siege noir autour de la lentille + ombre de contact (lumiere en haut a gauche)
    m = n + 16
    seat = np.zeros((m, m, 4), np.float32)
    y2, x2 = np.mgrid[0:m, 0:m].astype(np.float32) + 0.5
    r2 = np.hypot(x2 - m / 2, y2 - m / 2)
    rs = np.hypot(x2 - m / 2 - 1.6, y2 - m / 2 - 2.0)
    sh = np.clip((LED_R + 6.0 - rs) / 4.0, 0, 1) * 0.55
    ring = np.clip(LED_R + 2.2 - r2 + 0.5, 0, 1)
    seat[..., :3] = 10.0; seat[..., 3] = np.maximum(sh, ring) * 255.0
    def over(base, top, o):
        out = base.copy(); h = top.shape[0]
        a_ = top[..., 3:4] / 255.0
        reg = out[o:o + h, o:o + h]
        rgb = reg[..., :3] * (1 - a_) + top[..., :3] * a_
        al = reg[..., 3:4] + top[..., 3:4] * (1 - reg[..., 3:4] / 255.0)
        out[o:o + h, o:o + h] = np.concatenate([rgb, al], 2); return out
    off_s = over(seat, off, 8)
    lit_s = np.zeros_like(seat); lit_s = over(lit_s, lit, 8)
    # halo : la facade recoit la lumiere rouge (serre + large et faible), symetrique
    H = int(LED_R * 9) | 1
    y3, x3 = np.mgrid[0:H, 0:H].astype(np.float32) + 0.5
    d = np.clip(np.hypot(x3 - H / 2, y3 - H / 2) - LED_R, 0, None)
    a_h = np.clip(0.75 * np.exp(-d / 5.0) + 0.38 * np.exp(-d / 18.0) + 0.08 * np.exp(-d / 50.0), 0, 0.92)
    a_h = a_h * (1 - sstep(H / 2 - 16, H / 2 - 1, np.hypot(x3 - H / 2, y3 - H / 2)))
    mixc = np.exp(-d / 10.0)[..., None]
    col = np.array([255.0, 190.0, 120.0]) * mixc + np.array([255.0, 118.0, 30.0]) * (1 - mixc)
    halo = np.dstack([col, a_h * 255])
    return off_s, lit_s, halo

def fs_layers():
    """footswitch photo du kit + reflet orange de l'anneau sur l'ecrou (calque en fondu avec l'anneau)"""
    spr, _, S_, btn = PC.footswitch_sprite(FS_FLATS, 1, pad=1.5)
    n = spr.shape[0]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rr = np.hypot(xx - n / 2, yy - n / 2) / (FS_FLATS / 2)
    a = spr[..., 3] / 255.0
    nut = np.clip((rr * (FS_FLATS / 2) - btn - 2.0) / 6.0, 0, 1) * (rr > 0.0)
    body = (a > 0.98).astype(np.float32)
    lum = spr[..., :3].mean(2) / 255.0
    outer = np.clip((rr - 0.55) / 0.5, 0, 1)                      # surtout le flanc exterieur de l'ecrou, tourne vers l'anneau
    refl = body * nut * (0.25 + 0.75 * outer) * (0.35 + 0.65 * lum)
    refl_rgba = np.dstack([np.broadcast_to(np.array([255.0, 128.0, 48.0]), (n, n, 3)), np.clip(refl * 0.55, 0, 1) * 255])
    return spr, refl_rgba, btn

def build(write=True):
    W_ = warp_design()
    B = erase_all(W_)
    alpha = box_alpha(W_)
    B, ring_src, ring_halo = ring_layers(W_, B, diffuser=False)
    B = clean_bottom(B)
    B = smooth_panel_edge(B)
    B = engrave_details(B)
    B, tick_src, tick_halo = bold_tick_layers(B)
    out_rgb = B.copy(); out_a = alpha.copy()
    # footswitch photo
    fs, fs_refl, btn = fs_layers()
    n = fs.shape[0]
    place(out_rgb, None, fs, FS_C[0] - n / 2, FS_C[1] - n / 2)
    led_off, led_lit, led_halo = led_layers(); m_ = led_off.shape[0]
    place(out_rgb, None, led_off, SYNC_C[0] - m_ / 2, SYNC_C[1] - m_ / 2)
    Hh_, Ww_ = out_rgb.shape[:2]
    def full(spr):
        canvas = np.zeros((Hh_, Ww_, 4), np.float32); h = spr.shape[0]
        y0, x0 = int(round(SYNC_C[1] - h / 2)), int(round(SYNC_C[0] - h / 2))
        canvas[y0:y0 + h, x0:x0 + h] = spr; return canvas
    sync_src, sync_halo = full(led_lit), full(led_halo)
    # embases jack photo : IN a droite, OUT a gauche, sans ombre (tranches)
    jl = JACK_LEN_PX
    jr, jw, jh = PC.jack_sprite(jl, 1, 1)
    jo, ow, oh = PC.jack_sprite(jl, 1, -1)
    out_rgb[:, :int(TX0)] = 0; out_rgb[:, int(math.ceil(TX1)):] = 0
    place(out_rgb, out_a, jr, TX1 - 1.5, JACK_Y - jh / 2)
    place(out_rgb, out_a, jo, TX0 + 1.5 - ow, JACK_Y - oh / 2)
    bg = np.dstack([out_rgb * out_a[..., None], out_a * 255])
    # couleur premultipliee -> droite
    bg[..., :3] = np.where(out_a[..., None] > 1e-4, bg[..., :3] / np.maximum(out_a, 1e-4)[..., None], 0)
    layers = {'ticks_core': tick_src, 'ticks_glow': tick_halo,
              'sync_core': sync_src, 'sync_glow': sync_halo}
    info = {'fsBtnR': float(btn), 'fsSprite': float(n)}
    if write:
        save_rgba(os.path.join(ROOT, 'background.png'), bg)
        pos = {}
        for k, v in layers.items():
            c, o = crop_layer(v)
            save_rgba(os.path.join(ROOT, k + '.png'), c); pos[k] = o + c.shape[1::-1]
        c, o = crop_layer(fs_refl)
        save_rgba(os.path.join(ROOT, 'fs_refl.png'), c)
        pos['fs_refl'] = (o[0] + FS_C[0] - n / 2, o[1] + FS_C[1] - n / 2, c.shape[1], c.shape[0])
        info['layers'] = pos
    return bg, layers, (fs_refl, FS_C[0] - n / 2, FS_C[1] - n / 2), info

def small_ticks():
    """graduations blanches (vectorielles, dessinees par le plugin) : segments en unites du plugin"""
    out = []
    for i in range(41):
        a = -150.0 + 7.5 * i
        if abs(round(a / 30.0) * 30.0 - a) < 1e-6: continue          # emplacement d'une graduation grasse
        t = math.radians(a)
        r0, r1, hw = TICK_SMALL
        out.append([(TICK_C[0] + r0 * math.sin(t)) / 2, (TICK_C[1] - r0 * math.cos(t)) / 2,
                    (TICK_C[0] + r1 * math.sin(t)) / 2, (TICK_C[1] - r1 * math.cos(t)) / 2, hw])   # hw en unites (= 2 x demi-largeur px / 2)
    return out

def write_layout(info):
    u = lambda v: v / 2.0
    lay = {
        'frame': [OUT_W / 2, OUT_H / 2],
        'knob': [u(KNOB_SIL[0]), u(KNOB_SIL[1]), u(KNOB_RS)],
        'knobBox': [u(KNOB_SIL[0]) - u(KNOB_RS) * LAYER / 2 / KNOB_LR, u(KNOB_SIL[1]) - u(KNOB_RS) * LAYER / 2 / KNOB_LR,
                    u(KNOB_RS) * LAYER / KNOB_LR, u(KNOB_RS) * LAYER / KNOB_LR],
        'ticks': small_ticks(),
        'fs': [u(FS_C[0]), u(FS_C[1]), u(info['fsBtnR']), u(FS_FLATS / 2)],
        'fsRing': [u(info['fsBtnR']) * 40.45 / 37.54 - 3.0, u(info['fsBtnR']) * 2.53 / 37.54],   # resserre de 3 px vers l'interieur (demandes)
        'sync': [u(SYNC_C[0]), u(SYNC_C[1]), u(SYNC_R1 + 4)],
        'phaseBox': [u(PHASE_BOX[0]), u(PHASE_BOX[1]), u(PHASE_BOX[2] - PHASE_BOX[0]), u(PHASE_BOX[3] - PHASE_BOX[1])],
        'preset': [u(PRESET[0]), u(PRESET[1]), u(PRESET[2]), u(PRESET[3])],
        'texts': [[t, f, u(ch), u(tr), u(x), u(y), rot] for (t, f, ch, tr, x, y, rot) in TEXTS],
        'syncLabel': [u(SYNC_C[0]), u(SYNC_C[1] + SYNC_R1 + 24), u(18.0)],
        'logo': [u(LOGO_C[0]), u(LOGO_C[1]), u(LOGO_W)],
        'layers': {k: [u(v[0]), u(v[1]), u(v[2]), u(v[3])] for k, v in info['layers'].items()},
        'jackY': u(JACK_Y),
    }
    json.dump(lay, open(os.path.join(HERE, 'layout.json'), 'w'), indent=1)
    f = lambda v: '%.2ff' % v
    rect = lambda r: '{ %s, %s, %s, %s }' % tuple(f(x) for x in r)
    L_ = lay['layers']
    h = ['// genere par tools/make_art.py - ne pas modifier a la main (repere 617.5 x 900 = fond 1235 x 1800 px / 2)',
         '#pragma once', '#include <juce_graphics/juce_graphics.h>', 'namespace layout', '{',
         '    constexpr float frameW = 617.50f, frameH = 900.00f;',
         '    const juce::Point<float> knobPos { %s, %s }; const float knobR = %s;   // axe du potard SPEED' % (f(lay['knob'][0]), f(lay['knob'][1]), f(lay['knob'][2])),
         '    const juce::Rectangle<float> knobBox %s;   // composant nh::Knob (calques 1024 px)' % rect(lay['knobBox']),
         '    const juce::Point<float> fsPos { %s, %s }; const float footR = %s;' % (f(lay['fs'][0]), f(lay['fs'][1]), f(lay['fs'][2])),
         '    const float fsRingR = %s, fsRingW = %s;   // anneau lumineux dans la gorge du footswitch (dessin d\'Octopus)' % (f(lay['fsRing'][0]), f(lay['fsRing'][1])),
         '    const juce::Point<float> syncPos { %s, %s }; const float syncR = %s;' % (f(lay['sync'][0]), f(lay['sync'][1]), f(lay['sync'][2])),
         '    const juce::Rectangle<float> phaseBox %s;' % rect(lay['phaseBox']),
         '    const juce::Rectangle<float> presetRect %s;   // pastille presets / ligne d\'etat (400 x 38)' % rect(lay['preset']),
         '    const float presetFont = 23.0f;']
    for k in ('ticks_core', 'ticks_glow', 'sync_core', 'sync_glow', 'fs_refl'):
        h.append('    const juce::Rectangle<float> %s %s;' % (k.replace('_c', 'C').replace('_g', 'G').replace('_r', 'R'), rect(L_[k])))
    h.append('    struct Txt { const char* s; int font; float capH, track, x, y, rot; };   // font : 0 medium, 1 bold, 2 light, 3 regular')
    h.append('    const Txt texts[] = {')
    h.append(',\n'.join('        { "%s", %d, %s, %s, %s, %s, %s }' % (t[0], t[1], f(t[2]), f(t[3]), f(t[4]), f(t[5]), f(t[6])) for t in lay['texts']))
    h.append('    };')
    h.append('    struct Seg { float x0, y0, x1, y1, w; };')
    h.append('    const Seg ticks[] = { ' + ', '.join('{ %s, %s, %s, %s, %s }' % tuple(f(v) for v in t) for t in lay['ticks']) + ' };')
    h.append('    const juce::Point<float> syncLabelPos { %s, %s }; const float syncLabelCapH = %s;' % (f(lay['syncLabel'][0]), f(lay['syncLabel'][1]), f(lay['syncLabel'][2])))
    h.append('    const juce::Point<float> logoPos { %s, %s }; const float logoW = %s;' % (f(lay['logo'][0]), f(lay['logo'][1]), f(lay['logo'][2])))
    h.append('}')
    open(os.path.join(ROOT, 'Layout.h'), 'w').write('\n'.join(h) + '\n')
    return lay

# ------------------------------------------------------------------ 4. potard SPEED : calques nh::Knob extraits du visuel
# Le potard du visuel est vu tres legerement en perspective : le sommet du cone de metal tourne (axe) est un peu plus haut
# que le centre de la silhouette. On le redresse en vue de dessus : le cercle de rayon r est centre sur
# c(r) = sommet + (centre silhouette - sommet) * r / R. Puis, en coordonnees polaires :
#   eclairage fixe  = moyenne angulaire glissante (gaussienne 9 deg) -> calque "highlight" (reste fixe)
#   matiere         = detail fin (stries du metal tourne, moletage) + niveau de base du rayon -> calques qui tournent
#   index blanc + encoche de la jupe -> calque "marker" (effaces de la matiere par interpolation angulaire)
KNOB_APEX = (611.3, 325.0)
KNOB_SIL = (614.5, 344.5)
KNOB_RS = 215.5            # rayon de la silhouette (px de l'image finale)
KNOB_STEP = 158.0          # limite chapeau / couronne
LAYER = 1024
KNOB_LR = 412.0            # rayon du potard dans les calques 1024 px (marge pour l'ombre)
NT, NR = 4096, 940

def blur_wrap(a, sx, sy):
    """flou gaussien avec bouclage selon l'angle (axe 1)"""
    pad = int(3 * sx) + 2
    ext = np.concatenate([a[:, -pad:], a, a[:, :pad]], 1)
    return cv2.GaussianBlur(ext, (0, 0), sigmaX=sx, sigmaY=sy, borderType=cv2.BORDER_REFLECT)[:, pad:-pad]

def knob_polar(W_):
    rr = np.linspace(0, KNOB_RS + 4.0, NR).astype(np.float32)
    th = (np.arange(NT) / NT * 2 * np.pi).astype(np.float32)          # 0 = haut, sens horaire
    k = (rr / KNOB_RS).clip(0, 1)
    cx = KNOB_APEX[0] + (KNOB_SIL[0] - KNOB_APEX[0]) * k
    cy = KNOB_APEX[1] + (KNOB_SIL[1] - KNOB_APEX[1]) * k
    X = cx[:, None] + rr[:, None] * np.sin(th)[None, :]
    Y = cy[:, None] - rr[:, None] * np.cos(th)[None, :]
    return np.dstack([cv2.remap(W_[..., c], X, Y, cv2.INTER_CUBIC) for c in range(3)]), rr, th

def knob_layers(W_):
    Pp, rr, th = knob_polar(W_)                                      # (NR, NT, 3)
    # 1. index blanc (chapeau) et encoche (jupe) : a 0 deg ; masque = clair et proche du haut
    dth = np.minimum(th, 2 * np.pi - th)
    lumP = Pp.mean(2)
    win = (dth[None, :] < math.radians(9.0))
    ref = cv2.GaussianBlur(lumP, (0, 0), sigmaX=40, sigmaY=0.5)
    bright = (lumP - ref > 28) & win
    bright = cv2.dilate(bright.astype(np.uint8), np.ones((7, 31), np.uint8)).astype(bool) & win
    # marqueur = pixels clairs (couleur d'origine), alpha d'apres l'ecart au fond
    # fond sans marqueur : interpolation angulaire de part et d'autre de la fenetre
    clean = Pp.copy()
    w0 = math.radians(9.5)
    i0 = int(round((2 * np.pi - w0) / (2 * np.pi) * NT)); i1 = int(round(w0 / (2 * np.pi) * NT))
    left, right = Pp[:, i0 - 6:i0].mean(1), Pp[:, i1:i1 + 6].mean(1)
    for j in list(range(i0, NT)) + list(range(0, i1)):
        a = th[j] - (2 * np.pi) if j >= i0 else th[j]
        t = (a + w0) / (2 * w0)
        clean[:, j] = left * (1 - t) + right * t
    # garder le detail fin (stries) dans la zone interpolee : bruit angulaire repris a cote
    det_src = Pp[:, i1 + 40:i1 + 40 + (NT - i0 + i1)] - cv2.GaussianBlur(Pp[:, i1 + 40:i1 + 40 + (NT - i0 + i1)], (0, 0), sigmaX=6, sigmaY=0.5)
    idx = list(range(i0, NT)) + list(range(0, i1))
    clean[:, idx] += det_src[:, :len(idx)]
    lumC = clean.mean(2)
    diffm = np.clip((lumP - lumC) / 140.0, 0, 1) * bright
    marker = np.dstack([np.clip(Pp, 0, 255), diffm * 255])
    # 2. eclairage fixe / matiere qui tourne
    sig = 9.0 / 360.0 * NT
    lf = blur_wrap(clean, sig, 0.6)
    det = clean - lf
    base = np.percentile(lf, 6, axis=1)                               # (NR, 3) : rayon dans l'ombre
    base = cv2.GaussianBlur(base.reshape(NR, 1, 3), (0, 0), sigmaX=0.01, sigmaY=1.5).reshape(NR, 3)
    # amplitude du detail normalisee (le detail eclaire ne doit pas suivre la rotation)
    amp = blur_wrap(np.abs(det).mean(2), sig, 2)
    ampm = np.median(amp, axis=1, keepdims=True)
    det_n = det * (ampm / np.maximum(amp, 0.3))[..., None].clip(0, 2.5)
    det_n = np.repeat(det_n.mean(2, keepdims=True), 3, 2)                 # matiere neutre (pas de reflet orange qui tourne)
    base = np.repeat(base.mean(1, keepdims=True), 3, 1) * np.array([1.0, 1.0, 1.03])
    mat = np.clip(base[:, None, :] + det_n, 0, 255)
    lum_lf = lf.mean(2); lum_b = base.mean(1)[:, None]
    a_hl = np.clip((lum_lf - lum_b) / np.maximum(255 - lum_b, 1), 0, 1)
    hl_col = np.clip((lf - base[:, None, :] * (1 - a_hl[..., None])) / np.maximum(a_hl, 1e-3)[..., None], 0, 255)
    g_ = hl_col.mean(2, keepdims=True)
    hl_col = g_ + (hl_col - g_) * 0.25                                    # reflets fixes presque neutres
    hl = np.dstack([hl_col, a_hl * 255])
    return Pp, mat, marker, hl, rr

def polar_to_layer(P_, rr, r_lo, r_hi, feather=1.2):
    """calque 1024 x 1024 (potard centre, rayon KNOB_LR) a partir d'une image polaire (NR, NT, 4)"""
    n = LAYER
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    dx, dy = xx - n / 2, yy - n / 2
    r_px = np.hypot(dx, dy) * (KNOB_RS / KNOB_LR)                   # en px de l'image finale
    th = np.mod(np.arctan2(dx, -dy), 2 * np.pi)
    mi = (r_px / rr[-1] * (NR - 1)).astype(np.float32)
    mj = (th / (2 * np.pi) * NT).astype(np.float32)
    P_w = np.concatenate([P_, P_[:, :8]], 1)
    out = np.dstack([cv2.remap(P_w[..., c], mj, mi, cv2.INTER_LINEAR) for c in range(P_.shape[2])])
    sc = KNOB_LR / KNOB_RS
    m = sstep(r_lo - feather, r_lo + feather, r_px * 1.0) * (1 - sstep(r_hi - feather / sc * 2, r_hi + feather / sc * 0.5, r_px))
    if out.shape[2] == 4: out[..., 3] *= m
    else: out = np.dstack([out, m * 255])
    return out

def build_knob(W_, write=True):
    Pp, mat, marker, hl, rr = knob_layers(W_)
    Rk = KNOB_RS
    crown = polar_to_layer(mat, rr, KNOB_STEP, Rk)
    cap = polar_to_layer(mat, rr, -1.0, KNOB_STEP + 0.8)
    mk = polar_to_layer(marker, rr, -1.0, Rk)
    hlL = polar_to_layer(hl, rr, -1.0, Rk)
    # ombre portee centree (le code la decale vers le bas a droite)
    n = LAYER
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    rl = np.hypot(xx - n / 2, yy - n / 2)
    disk = np.clip(KNOB_LR - rl + 0.5, 0, 1)
    sh = np.clip(cv2.GaussianBlur(disk, (0, 0), 22) * 0.80 + cv2.GaussianBlur(disk, (0, 0), 6) * 0.35, 0, 0.9)
    shadow = np.dstack([np.zeros((n, n, 3)), sh * 255])
    L = {'shadow': shadow, 'crown': crown, 'cap': cap, 'marker': mk, 'highlight': hlL}
    if write:
        for k_, v in L.items():
            save_rgba(os.path.join(ROOT, 'knob_' + k_ + '.png'), v)
    return L

if __name__ == '__main__' and 'knob' in sys.argv:
    L = build_knob(warp_design())
    def stack(ang):
        n = LAYER
        M = cv2.getRotationMatrix2D((n / 2, n / 2), -ang, 1.0)
        rot = lambda im: cv2.warpAffine(im, M, (n, n), flags=cv2.INTER_LINEAR)
        out = np.full((n, n, 3), 20.0)
        def over(im):
            a = im[..., 3:4] / 255.0; return out * (1 - a) + im[..., :3] * a
        sh = rot(L['shadow']); Ms = np.float32([[1, 0, 0.025 * n], [0, 1, 0.025 * n]]); sh = cv2.warpAffine(sh, Ms, (n, n))
        out = over(sh)
        for k_ in ('crown', 'cap', 'marker'): out = over(rot(L[k_]))
        out = over(L['highlight'])
        return out
    row = np.concatenate([stack(a) for a in (-150, 0, 90)], 1)
    Image.fromarray(np.clip(row, 0, 255).astype(np.uint8)).resize((1536, 512)).save('/tmp/claude-0/p9/knob_test.png')
    W0 = warp_design()
    d = W0[int(KNOB_SIL[1] - 260):int(KNOB_SIL[1] + 260), int(KNOB_SIL[0] - 260):int(KNOB_SIL[0] + 260)]
    k0 = cv2.resize(stack(0), (int(1024 * KNOB_RS / KNOB_LR), int(1024 * KNOB_RS / KNOB_LR)), interpolation=cv2.INTER_AREA)
    pad = (k0.shape[0] - 520) // 2
    k0 = k0[pad:pad + 520, pad:pad + 520]
    Image.fromarray(np.clip(np.concatenate([d, k0], 1), 0, 255).astype(np.uint8)).save('/tmp/claude-0/p9/knob_cmp.png')


if __name__ == '__main__' and 'build' in sys.argv:
    bg, layers, refl, info = build()
    import knob_layers                      # potard SPEED : calques ChatGPT fournis par l'utilisateur (tools/knob_layers.py)
    knob_layers.build()
    write_layout(info)
    print(info)
