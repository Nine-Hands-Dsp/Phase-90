"""GIF de controle du potard SPEED (30 i/s) : calques nh::Knob, flou de mouvement = angle parcouru pendant l'image,
montee immediate, retombee x0,6 par image, positions du flou espacees de 3 deg au plus (comme NHKnob.h).
Usage : python3 tools/knob_gif.py design/speed_knob.gif"""
import os, sys, json, math
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
LAY = json.load(open(os.path.join(HERE, 'layout.json')))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'design', 'speed_knob.gif')
K = 2.0
base = Image.open(os.path.join(ROOT, 'design', 'preview_noknob.png')).convert('RGB')
kb = LAY['knobBox']; n = int(round(kb[2] * K)); x0, y0 = int(round(kb[0] * K)), int(round(kb[1] * K))
ld = lambda nm: cv2.resize(np.asarray(Image.open(os.path.join(ROOT, 'knob_%s.png' % nm)).convert('RGBA')).astype(np.float32), (n, n), interpolation=cv2.INTER_AREA)
Ls = {nm: ld(nm) for nm in ('shadow', 'crown', 'cap', 'marker', 'highlight')}
def over(dst, src):
    a = src[..., 3:4] / 255.0
    return np.concatenate([dst[..., :3] * (1 - a) + src[..., :3] * a, dst[..., 3:4] * (1 - a) + src[..., 3:4]], 2)
stack = np.zeros((n, n, 4), np.float32)
for nm in ('crown', 'cap', 'marker'): stack = over(stack, Ls[nm])
def rot(im, a, dx=0.0, dy=0.0):
    M = cv2.getRotationMatrix2D((n / 2, n / 2), -a, 1.0); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(im, M, (n, n), flags=cv2.INTER_LINEAR)
def blurred(img, a, span, sgn, dx=0.0, dy=0.0):
    if span <= 0: return rot(img, a, dx, dy)
    k = int(np.clip(math.ceil(span / 3.0) + 1, 4, 16)); acc = np.zeros_like(img)
    for i in range(k): acc += rot(img, a - sgn * span * i / (k - 1), dx, dy)
    return acc / k
crop = (x0 - 30, y0 - 20, x0 + n + 60, y0 + n + 30)
bgc = np.asarray(base).astype(np.float32)
# trajectoire : lent 0->1 (2 s), arret, rapide 1->0 (0,3 s), arret, tres rapide 0->1 (0,13 s), arret
vals = list(np.linspace(0.5, 1.0, 30)) + [1.0] * 10 + list(np.linspace(1.0, 0.0, 10)) + [0.0] * 10 + list(np.linspace(0.0, 1.0, 4)) + [1.0] * 12 + list(np.linspace(1.0, 0.5, 20)) + [0.5] * 8
frames = []; last = None; span = 0.0; sgn = 1.0
for v in vals:
    a = -150 + 300 * v
    if last is not None:
        dv = a - last
        if abs(dv) > 1e-5: sgn = 1.0 if dv > 0 else -1.0
        span = max(min(abs(dv), 40.0), span * 0.6)
        if span < 0.1: span = 0.0
    last = a
    k = np.zeros((n, n, 4), np.float32)
    k = over(k, blurred(Ls['shadow'], a, span, sgn, 0.025 * n, 0.025 * n))
    k = over(k, blurred(stack, a, span, sgn))
    k = over(k, Ls['highlight'])
    img = bgc.copy()
    al = k[..., 3:4] / 255.0
    img[y0:y0 + n, x0:x0 + n] = img[y0:y0 + n, x0:x0 + n] * (1 - al) + k[..., :3] * al
    fr = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).crop(crop)
    frames.append(fr.resize((fr.width * 3 // 4, fr.height * 3 // 4), Image.LANCZOS))
frames[0].save(out, save_all=True, append_images=frames[1:], duration=33, loop=0, optimize=False)
print(out, len(frames))
