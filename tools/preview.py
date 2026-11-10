"""Apercu du plugin (avant code) : fond + lumieres (Glow) + potard nh::Knob + serigraphie vectorielle + pastille + logo.
Usage : python3 tools/preview.py sortie.png [on|off] [speed 0..1] [sync 0..3] [texte pastille] [glow 0.25..1] [status]"""
import os, sys, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LAY = json.load(open(os.path.join(HERE, 'layout.json')))
A = sys.argv
out = A[1] if len(A) > 1 else os.path.join(ROOT, 'design', 'preview.png')
ON = (A[2] if len(A) > 2 else 'on') == 'on'
SPEED = float(A[3]) if len(A) > 3 else 0.5
SYNC = int(A[4]) if len(A) > 4 else 0
PILL = A[5] if len(A) > 5 else 'Classic Block'
GLOW = float(A[6]) if len(A) > 6 else 1.0
STATUS = (A[7] if len(A) > 7 else '') == 'status'
LFO = float(os.environ.get('LFO', '0.25'))     # 0 = haut du balayage (graduations au plus clair)
K = 2.0
FONTS = {0: 'Poppins-Medium.ttf', 1: 'Poppins-Bold.ttf', 2: 'Poppins-Light.ttf', 3: 'Poppins-Regular.ttf'}
SYNC_NAMES = ['OFF', '1/4', '1/8', '1/2']

def load(fn): return Image.open(os.path.join(ROOT, fn)).convert('RGBA')
bg = load('background.png')
canvas = Image.new('RGBA', bg.size, (14, 14, 15, 255)); canvas.alpha_composite(bg)

def paste(fn, rect, op=1.0):
    if op <= 0.003: return
    im = load(fn)
    if op < 1: im.putalpha(im.getchannel('A').point(lambda v: int(v * op)))
    canvas.alpha_composite(im, (int(round(rect[0] * K)), int(round(rect[1] * K))))

Lr = LAY['layers']
tick = (0.40 + 0.60 * (1 - LFO)) if ON else 0.0
paste('ticks_glow.png', Lr['ticks_glow'], tick * GLOW); paste('ticks_core.png', Lr['ticks_core'], tick)
if ON:
    paste('fs_refl.png', Lr['fs_refl'], 0.5)
    # anneau du footswitch (dessin d'Octopus) : halo dose par Glow, trait net, coeur clair
    fx, fy, fR, fW = LAY['fs'][0], LAY['fs'][1], LAY['fsRing'][0], LAY['fsRing'][1]
    cv = np.asarray(canvas).astype(np.float32)
    yy, xx = np.mgrid[0:cv.shape[0], 0:cv.shape[1]].astype(np.float32)
    dd = np.abs(np.hypot(xx / K - fx, yy / K - fy) - fR) * K
    def stroke(col, a, w):
        cov = np.clip(w * K / 2 - dd + 0.5, 0, 1)[..., None] * a
        cv[..., :3] = cv[..., :3] * (1 - cov) + np.array(col, np.float32) * cov
    kr = fR / 33.2
    hw = 20.0
    while hw > 3.0:
        stroke((255, 128, 36), min(1.0, 0.075 * GLOW), hw * kr); hw -= 1.5
    stroke((255, 128, 36), 0.85, fW)
    stroke((255, 214, 160), 0.9, fW * 0.42)
    canvas = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8), 'RGBA')
if SYNC > 0:
    paste('sync_glow.png', Lr['sync_glow'], GLOW); paste('sync_core.png', Lr['sync_core'])

# ---- potard (calques nh::Knob, meme algorithme que le composant)
def knob_img(angle_deg, blur_deg=0.0):
    names = ['shadow', 'crown', 'cap', 'marker', 'highlight']
    Ls = {n: np.asarray(load('knob_%s.png' % n)).astype(np.float32) for n in names}
    n = 1024
    def rot(im, a, dx=0, dy=0):
        M = cv2.getRotationMatrix2D((n / 2, n / 2), -a, 1.0); M[0, 2] += dx; M[1, 2] += dy
        return cv2.warpAffine(im, M, (n, n), flags=cv2.INTER_LINEAR)
    def over(dst, src):
        a = src[..., 3:4] / 255.0
        rgb = dst[..., :3] * (1 - a) + src[..., :3] * a
        al = dst[..., 3:4] * (1 - a) + src[..., 3:4]
        return np.concatenate([rgb, al], 2)
    stack = np.zeros((n, n, 4), np.float32)
    for nm in ('crown', 'cap', 'marker'): stack = over(stack, Ls[nm])
    def blurred(img, a, dx=0, dy=0):
        if blur_deg <= 0: return rot(img, a, dx, dy)
        k = int(np.clip(math.ceil(blur_deg / 3.0) + 1, 4, 16)); acc = np.zeros_like(img)
        for i in range(k):
            acc += rot(img, a - blur_deg * i / (k - 1), dx, dy)
        return acc / k
    outk = np.zeros((n, n, 4), np.float32)
    outk = over(outk, blurred(Ls['shadow'], angle_deg, 0.025 * n, 0.025 * n))
    outk = over(outk, blurred(stack, angle_deg))
    outk = over(outk, Ls['highlight'])
    return Image.fromarray(np.clip(outk, 0, 255).astype(np.uint8), 'RGBA')

NOKNOB = os.environ.get('NOKNOB') == '1'
kb = LAY['knobBox']
if not NOKNOB:
  kimg = knob_img(-150 + 300 * SPEED).resize((int(round(kb[2] * K)), int(round(kb[3] * K))), Image.LANCZOS)
  canvas.alpha_composite(kimg, (int(round(kb[0] * K)), int(round(kb[1] * K))))

# ---- serigraphie vectorielle (sur-echantillonnee)
SS = 3
big = Image.new('RGBA', (canvas.width * SS, canvas.height * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
def cap_ratio(font):
    f = ImageFont.truetype(os.path.join(ROOT, FONTS[font]), 1000); b = f.getbbox('H'); return (b[3] - b[1]) / 1000.0
def text(s_, font, capH, track, x, y, rot, fill, layer=None):
    em = capH / cap_ratio(font)
    f = ImageFont.truetype(os.path.join(ROOT, FONTS[font]), int(em * K * SS))
    ws = [f.getlength(c) for c in s_]; tot = sum(ws) + track * K * SS * (len(s_) - 1)
    lay = Image.new('RGBA', (int(tot) + 40, int(em * K * SS * 1.6)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    hb = f.getbbox('H'); cy = lay.height / 2
    cx = 20
    for c, w in zip(s_, ws):
        ld.text((cx, cy - (hb[1] + hb[3]) / 2), c, font=f, fill=fill); cx += w + track * K * SS
    if rot: lay = lay.rotate(-rot, expand=True, resample=Image.BICUBIC)
    (layer or big).alpha_composite(lay, (int(x * K * SS - lay.width / 2), int(y * K * SS - lay.height / 2)))
COL = {'SPEED': (212, 212, 216, 240), 'PHASE': (236, 112, 28, 255), 'OUTPUT': (24, 10, 4, 235), 'INPUT': (24, 10, 4, 235), '90': (24, 10, 4, 240)}
for t in LAY['texts']:
    s_, font, capH, track, x, y, rot = t
    if s_ == 'PHASE':     # orange en relief : ombre sombre en bas a droite, liseré clair en haut a gauche
        text(s_, font, capH, track, x + 0.8, y + 1.2, rot, (0, 0, 0, 200))
        text(s_, font, capH, track, x - 0.35, y - 0.45, rot, (255, 190, 140, 160))
    text(s_, font, capH, track, x, y, rot, COL[s_])
for (x0, y0, x1, y1, w) in LAY['ticks']:
    d.line([(x0 * K * SS, y0 * K * SS), (x1 * K * SS, y1 * K * SS)], fill=(226, 226, 230, 236), width=max(1, int(2 * w * SS)))
# inscription du bouton SYNC
sx, sy, sch = LAY['syncLabel']
text('SYNC' if SYNC == 0 else 'SYNC ' + SYNC_NAMES[SYNC], 3, sch, 1.0, sx, sy, 0, (212, 212, 216, 235) if SYNC == 0 else (246, 246, 248, 255))
# pastille presets / ligne d'etat : face noire, contour sombre, liseré gris clair (comme le cartouche du visuel)
px, py, pw, ph = LAY['preset']
R = lambda v: v * K * SS
d.rounded_rectangle((R(px) - R(1.2), R(py) - R(1.2), R(px + pw) + R(1.2), R(py + ph) + R(1.2)), radius=R(ph / 2 + 1.2), fill=(0, 0, 0, 230))
d.rounded_rectangle((R(px), R(py), R(px + pw), R(py + ph)), radius=R(ph / 2), fill=(10, 10, 11, 255), outline=(96, 96, 100, 255), width=max(1, int(R(0.5))))
fm = ImageFont.truetype(os.path.join(ROOT, 'Poppins-Medium.ttf'), int(R(23)))
if STATUS:
    d.text((R(px + pw / 2), R(py + ph / 2 + 1)), 'SPEED  0.92 Hz  ·  BLOCK', font=fm, fill=(236, 236, 240, 255), anchor='mm')
else:
    d.text((R(px + pw / 2), R(py + ph / 2 + 1)), PILL, font=fm, fill=(232, 232, 236, 255), anchor='mm')
    for sgn in (-1, 1):
        cx = R(px + pw / 2 + sgn * (pw / 2 - 17)); cy = R(py + ph / 2); r = R(5.5)
        d.polygon([(cx + sgn * r, cy), (cx - sgn * r * 0.6, cy - r), (cx - sgn * r * 0.6, cy + r)], fill=(150, 150, 156, 255))
canvas.alpha_composite(big.resize(canvas.size, Image.LANCZOS))
# logo officiel NINE HANDS | DSP noir (NineHands_LogoPP_v003_FullBlack.svg) sur l'orange
lx, ly, lw = LAY['logo']
logo = load(os.path.join('assets', 'nine_hands_logo_noir.png'))
logo = logo.resize((int(lw * K), int(round(logo.height * lw * K / logo.width))), Image.LANCZOS)
canvas.alpha_composite(logo, (int(lx * K - logo.width / 2), int(ly * K - logo.height / 2)))
os.makedirs(os.path.dirname(out), exist_ok=True)
canvas.save(out); print(out)
