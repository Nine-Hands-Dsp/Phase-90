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
def y_inv(yt): return np.asarray(yt) / S + BY0

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
FS_C = (613.5, 1332.0)                                       # footswitch et anneau lumineux
PHASE_BOX = (345.0, 752.0, 890.0, 962.0)                     # cartouche PHASE (contour orange, exterieur)
PRESET = (617.5 - 400.0, 1060.0 - 38.0, 800.0, 76.0)         # pastille presets / ligne d'etat (400 x 38 unites)
SYNC_C, SYNC_R = (902.0, 552.0), 30.0                        # bouton SYNC, en bas a droite du potard
JACK_Y = 852.0                                               # embases jack, a la hauteur de OUTPUT / INPUT
TEXTS = [  # texte, police (0 medium, 1 bold, 2 light, 3 regular), hauteur des capitales (px), espacement (px), x, y, rotation
    ('SPEED', 3, 40.0, 3.0, 617.5, 603.0, 0.0),
    ('PHASE', 1, 82.0, 6.0, 617.5, 857.0, 0.0),
    ('OUTPUT', 3, 40.0, 3.0, 122.0, 848.0, -90.0),
    ('INPUT', 3, 40.0, 3.0, 1108.0, 852.0, 90.0),
    ('90', 2, 84.0, 4.0, 617.5, 1597.0, 0.0),
]
LOGO_C, LOGO_W = (617.5, 1694.0), 300.0

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

def grain_fill(img, mask, src_box, seed=1):
    """remplit (zone orange) : teinte basse frequence par inpainting + grain repris d'une zone propre"""
    m8 = (mask * 255).astype(np.uint8)
    low = cv2.GaussianBlur(img, (0, 0), 3.0)
    inp = np.dstack([cv2.inpaint(np.clip(low[..., c], 0, 255).astype(np.uint8), m8, 9, cv2.INPAINT_TELEA) for c in range(3)]).astype(np.float32)
    inp = cv2.GaussianBlur(inp, (0, 0), 2.0)
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
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.2)
    soft = np.maximum(soft, mask.astype(np.float32))[..., None]
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
    # textes sombres sur l'orange : OUTPUT, INPUT, 90
    tm = np.zeros(B.shape[:2], bool)
    for x0, y0, x1, y1 in ((96, 728, 150, 995), (1080, 758, 1138, 952), (500, 1535, 740, 1665)):
        tm[y0:y1, x0:x1] = True
    return grain_fill(B, tm, (300, 1600, 460, 1700))

if __name__ == '__main__' and 'erase' in sys.argv:
    B = erase_all(warp_design())
    Image.fromarray(np.clip(B, 0, 255).astype(np.uint8)).save('/tmp/claude-0/p9/erased.png')


# ------------------------------------------------------------------ 3. lumieres, footswitch, jacks, detourage
RING_R0, RING_R1 = 113.0, 149.0                              # anneau lumineux du footswitch (diffuseur)
FS_FLATS = 206.0                                             # footswitch photo : distance entre plats (px)

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def ring_layers(D_lit, B, C=None, R0=None, R1=None, collar=True):
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
    off = off * (1 - band[..., None]) + dif * band[..., None]
    # creux sous le footswitch (cache par l'ecrou)
    hole = 1 - sstep(RING_R0 - 3, RING_R0 - 0.5, r)
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
    # lissage du bord (sauf aux extremites)
    ls = cv2.GaussianBlur(lefts.astype(np.float32).reshape(-1, 1), (0, 0), 3.0).ravel()
    rs = cv2.GaussianBlur(rights.astype(np.float32).reshape(-1, 1), (0, 0), 3.0).ravel()
    xx = np.arange(Ww)[None, :] + 0.5
    a = np.clip(xx - ls[:, None] + 0.5, 0, 1) * np.clip(rs[:, None] - xx + 0.5, 0, 1)
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

SYNC_R0, SYNC_R1 = 24.0, 31.0                                # anneau lumineux du bouton SYNC
SYNC_BTN = 21.0                                              # rayon du bouton (metal tourne, photo du footswitch du kit)

def sync_button():
    """petit bouton-poussoir : le bouton en metal tourne de la photo du footswitch, sans l'ecrou, avec ombre"""
    k = SYNC_BTN / PC.FS_BTN_PX
    n = int(round(SYNC_BTN * 2 * 1.9))
    rgb, a = PC._place(PC._load('footswitch_photo.png'), PC.FS_C, k, n)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rr = np.hypot(xx - n / 2 + 0.5, yy - n / 2 + 0.5)
    a = a * np.clip(SYNC_BTN - rr + 0.5, 0, 1)
    return PC._with_shadow(rgb, a, 2 * SYNC_BTN, 0.55)

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
    B, ring_src, ring_halo = ring_layers(W_, B)
    B, tick_src, tick_halo = bold_tick_layers(B)
    B, sync_src, sync_halo = ring_layers(W_, B, SYNC_C, SYNC_R0, SYNC_R1, collar=False)
    out_rgb = B.copy(); out_a = alpha.copy()
    # footswitch photo
    fs, fs_refl, btn = fs_layers()
    n = fs.shape[0]
    place(out_rgb, None, fs, FS_C[0] - n / 2, FS_C[1] - n / 2)
    sb = sync_button(); m_ = sb.shape[0]
    place(out_rgb, None, sb, SYNC_C[0] - m_ / 2, SYNC_C[1] - m_ / 2)
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
    layers = {'ring_core': ring_src, 'ring_glow': ring_halo, 'ticks_core': tick_src, 'ticks_glow': tick_halo,
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
        'sync': [u(SYNC_C[0]), u(SYNC_C[1]), u(SYNC_R1 + 4)],
        'phaseBox': [u(PHASE_BOX[0]), u(PHASE_BOX[1]), u(PHASE_BOX[2] - PHASE_BOX[0]), u(PHASE_BOX[3] - PHASE_BOX[1])],
        'preset': [u(PRESET[0]), u(PRESET[1]), u(PRESET[2]), u(PRESET[3])],
        'texts': [[t, f, u(ch), u(tr), u(x), u(y), rot] for (t, f, ch, tr, x, y, rot) in TEXTS],
        'syncLabel': [u(SYNC_C[0]), u(SYNC_C[1] + SYNC_R1 + 26), u(18.0)],
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
         '    const juce::Point<float> syncPos { %s, %s }; const float syncR = %s;' % (f(lay['sync'][0]), f(lay['sync'][1]), f(lay['sync'][2])),
         '    const juce::Rectangle<float> phaseBox %s;' % rect(lay['phaseBox']),
         '    const juce::Rectangle<float> presetRect %s;   // pastille presets / ligne d\'etat (400 x 38)' % rect(lay['preset']),
         '    const float presetFont = 23.0f;']
    for k in ('ring_core', 'ring_glow', 'ticks_core', 'ticks_glow', 'sync_core', 'sync_glow', 'fs_refl'):
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
    build_knob(warp_design())
    write_layout(info)
    print(info)
