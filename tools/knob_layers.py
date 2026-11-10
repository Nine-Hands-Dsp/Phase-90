"""
Potard SPEED (nh::Knob) : calques 1024 x 1024 a partir des calques ChatGPT fournis par l'utilisateur (nov. 2026),
assets/knob_speed/speed_*.png.

Controle a reception : les calques separes ne retombaient pas exactement les uns sur les autres (centres decales de
3 a 8 px, chapeau sans index avec une bande verticale de retouche, liseré chrome absent des calques). Le potard complet
(speed_full.png), lui, est propre et concentrique (centre 512 / 512, chapeau r 366, couronne r 396, liseré r 438) :
c'est lui qui sert de reference, decompose comme suit (coordonnees polaires autour de l'axe) :
  - index : calque index fourni (speed_marker.png), recentre exactement sur l'axe ;
  - eclairage fixe (reflets coniques du metal tourne, liseré chrome) = moyenne angulaire glissante (9 deg) du potard
    complet sans index -> calque "highlight" (reste fixe : la lumiere ne tourne pas) ;
  - matiere (moletage de la couronne, stries du metal tourne) = detail fin, amplitude normalisee -> "crown" et "cap"
    (tournent avec l'index) ;
  - ombre portee : calque ombre fourni (centre, sans decalage ; le code la decale a 45 deg vers le bas a droite).
Lumiere des potards : en haut a gauche a 45 deg (regle NINE HANDS | DSP). Le lobe principal du liseré du potard fourni
est mesure a -139,5 deg (0 = droite, sens horaire, y vers le bas) : l'eclairage fixe est tourne de +4,5 deg -> -135 deg.
Sorties (racine du depot) : knob_shadow.png, knob_crown.png, knob_cap.png, knob_marker.png, knob_highlight.png
(rayon du potard dans les calques : 412 px, comme le reste du Layout).
Usage : python3 tools/knob_layers.py
"""
import os, math
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'assets', 'knob_speed')
N = 1024
C = (512.0, 512.0)                 # axe du potard complet
R_FULL = 438.4                     # rayon exterieur du potard complet (liseré chrome)
R_OUT = 412.0                      # rayon dans les calques du plugin (Layout.h : KNOB_LR)
R_CAP = 368.0                      # limite chapeau / couronne
LIGHT_TARGET, LIGHT_MEASURED = -135.0, -139.54
NT, NR = 4096, 460

def load(n): return np.asarray(Image.open(os.path.join(SRC, 'speed_%s.png' % n)).convert('RGBA')).astype(np.float32)
def save(n, a): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'knob_%s.png' % n), optimize=True)

def unpremul(rgb, a):
    return np.where(a[..., None] > 1e-3, rgb / np.maximum(a, 1e-3)[..., None], 0)

def to_polar(img):
    rr = np.linspace(0, NR - 1, NR).astype(np.float32)
    th = (np.arange(NT) / NT * 2 * np.pi).astype(np.float32)               # 0 = haut, sens horaire
    X = C[0] + rr[:, None] * np.sin(th)[None, :]; Y = C[1] - rr[:, None] * np.cos(th)[None, :]
    return np.dstack([cv2.remap(img[..., c], X, Y, cv2.INTER_CUBIC) for c in range(img.shape[2])])

def from_polar(P, scale):
    """image 1024 (rayon R_FULL -> R_OUT) a partir d'une image polaire"""
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) + 0.5
    dx, dy = (xx - N / 2) / scale, (yy - N / 2) / scale
    r = np.hypot(dx, dy); th = np.mod(np.arctan2(dx, -dy), 2 * np.pi)
    Pw = np.concatenate([P, P[:, :8]], 1)
    return np.dstack([cv2.remap(Pw[..., c], (th / (2 * np.pi) * NT).astype(np.float32), r.astype(np.float32), cv2.INTER_LINEAR)
                      for c in range(P.shape[2])]), r

def blur_wrap(a, sx, sy):
    pad = int(3 * sx) + 2
    ext = np.concatenate([a[:, -pad:], a, a[:, :pad]], 1)
    return cv2.GaussianBlur(ext, (0, 0), sigmaX=sx, sigmaY=sy, borderType=cv2.BORDER_REFLECT)[:, pad:-pad]

def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def build():
    full = load('full'); mk = load('marker'); sh = load('shadow')
    a_full = full[..., 3] / 255.0
    # --- index : centre exact sur l'axe (le calque fourni est decale de 7,5 px a droite)
    ys, xs = np.where(mk[..., 3] > 128)
    mk = cv2.warpAffine(mk, np.float32([[1, 0, C[0] - xs.mean()], [0, 1, 0]]), (N, N), flags=cv2.INTER_LINEAR)
    # --- potard complet sans index : interpolation angulaire de part et d'autre de l'index
    rgb = unpremul(full[..., :3] * a_full[..., None], a_full)
    P = to_polar(np.dstack([rgb, a_full * 255]))
    w0 = math.radians(11.0)
    i0 = int(round((2 * np.pi - w0) / (2 * np.pi) * NT)); i1 = int(round(w0 / (2 * np.pi) * NT))
    left, right = P[:, i0 - 8:i0].mean(1), P[:, i1:i1 + 8].mean(1)
    rows = np.arange(NR)
    zone = (rows > 20) & (rows < 352)                                       # index (r 191-330) et sa lueur sur le chapeau
    idx = list(range(i0, NT)) + list(range(0, i1))
    clean = P.copy()
    for j in idx:
        a = (np.arange(NT)[j] / NT * 2 * np.pi); a = a - 2 * np.pi if j >= i0 else a
        t = (a + w0) / (2 * w0)
        clean[zone, j] = (left * (1 - t) + right * t)[zone]
    # detail fin (stries) repris juste a cote
    src = P[:, i1 + 60:i1 + 60 + len(idx)]
    det_src = src - blur_wrap(src, 6, 0.5)
    clean[zone][:, idx] = clean[zone][:, idx]
    tmp = clean[:, idx]; tmp[zone] += det_src[zone]; clean[:, idx] = tmp
    # raccord doux aux bords de la fenetre (aucune ligne visible)
    angs = np.array([(j / NT * 2 * np.pi) - (2 * np.pi if j >= i0 else 0.0) for j in idx])
    f = sstep(0.0, math.radians(3.5), w0 - np.abs(angs))[None, :, None] * zone[:, None, None]
    clean[:, idx] = clean[:, idx] * f + P[:, idx] * (1 - f)
    # l'index reste efface au centre de la fenetre (largeur de l'index ~ 2 deg a r 190)
    # --- eclairage fixe / matiere
    sig = 9.0 / 360.0 * NT
    rgbP = clean[..., :3]
    lf = blur_wrap(rgbP, sig, 0.6)
    det = rgbP - lf
    base = np.percentile(lf, 8, axis=1)                                      # niveau du rayon dans l'ombre
    base = cv2.GaussianBlur(base.reshape(NR, 1, 3), (0, 0), sigmaX=0.01, sigmaY=1.2).reshape(NR, 3)
    amp = blur_wrap(np.abs(det).mean(2), sig, 2)
    ampm = np.median(amp, axis=1, keepdims=True)
    det_n = det * (ampm / np.maximum(amp, 0.3))[..., None].clip(0, 2.5)
    det_n = np.repeat(det_n.mean(2, keepdims=True), 3, 2)
    mat = np.clip(base[:, None, :] + det_n, 0, 255)
    # eclairage : tourne de +4,5 deg pour mettre la lumiere exactement en haut a gauche a 45 deg
    shift = int(round((LIGHT_TARGET - LIGHT_MEASURED) / 360.0 * NT))
    lf = np.roll(lf, shift, axis=1)
    lum_lf = lf.mean(2); lum_b = base.mean(1)[:, None]
    a_hl = np.clip((lum_lf - lum_b) / np.maximum(255 - lum_b, 1), 0, 1)
    hl_col = np.clip((lf - base[:, None, :] * (1 - a_hl[..., None])) / np.maximum(a_hl, 1e-3)[..., None], 0, 255)
    alphaP = clean[..., 3:4]
    scale = R_OUT / R_FULL
    matI, r = from_polar(np.concatenate([mat, alphaP], 2), scale)
    hlI, _ = from_polar(np.concatenate([hl_col, (a_hl[..., None] * alphaP / 255.0) * 255], 2), scale)
    cap = matI.copy(); cap[..., 3] *= 1 - sstep(R_CAP - 0.8, R_CAP + 0.8, r)
    crown = matI.copy(); crown[..., 3] *= sstep(R_CAP - 0.8, R_CAP + 0.8, r)
    # index et ombre : meme mise a l'echelle autour du centre
    M = np.float32([[scale, 0, N / 2 - C[0] * scale], [0, scale, N / 2 - C[1] * scale]])
    def sc(im):
        pm = im.copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
        o = cv2.warpAffine(pm, M, (N, N), flags=cv2.INTER_AREA)
        o[..., :3] = unpremul(o[..., :3], o[..., 3] / 255.0); return o
    marker = sc(mk)
    ys, xs = np.where(sh[..., 3] > 4)
    shadow = sc(sh); shadow[..., :3] = 0
    for n, a in (('shadow', shadow), ('crown', crown), ('cap', cap), ('marker', marker), ('highlight', hlI)):
        save(n, a)
    return dict(shadow=shadow, crown=crown, cap=cap, marker=marker, highlight=hlI)

if __name__ == '__main__':
    L = build()
    def over(d, s):
        a = s[..., 3:4] / 255.0; return np.concatenate([d[..., :3] * (1 - a) + s[..., :3] * a, d[..., 3:4] * (1 - a) + s[..., 3:4]], 2)
    def rot(im, ang, dx=0, dy=0):
        M = cv2.getRotationMatrix2D((N / 2, N / 2), -ang, 1.0); M[0, 2] += dx; M[1, 2] += dy
        return cv2.warpAffine(im, M, (N, N), flags=cv2.INTER_LINEAR)
    row = []
    for ang in (0, -150, 90):
        o = np.zeros((N, N, 4), np.float32); o[..., :3] = 40; o[..., 3] = 255
        o = over(o, rot(L['shadow'], ang, 0.025 * N, 0.025 * N))
        for n in ('crown', 'cap', 'marker'): o = over(o, rot(L[n], ang))
        o = over(o, L['highlight']); row.append(o[..., :3])
    full = load('full'); bg = np.full((N, N, 3), 40.0); a = full[..., 3:4] / 255
    ref = cv2.resize(bg * (1 - a) + full[..., :3] * a, (N, N))
    Image.fromarray(np.clip(np.concatenate([ref] + row, 1), 0, 255).astype(np.uint8)).resize((2048, 512)).save('/tmp/claude-0/kn/check.png')
