"""Landing phase: composite the Meshy infrastructure renders onto an uploaded lunar photo."""
from pathlib import Path
import cv2, numpy as np

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"

# Anchor = point where the structure touches the ground (relative x, y), width as a fraction
# of the photo width. Layout mirrors the reference "Post-Landing" figure in the idealization doc.
LAYOUT = {
    "LUNAR HABITAT":         dict(sprite="habitat",       anchor=(0.30, 0.47), w=0.25, color=(85, 184, 244)),
    "SOLAR POWER STATION":   dict(sprite="solar",         anchor=(0.76, 0.40), w=0.24, color=(80, 220, 255)),
    "COMMUNICATION STATION": dict(sprite="communication", anchor=(0.11, 0.66), w=0.10, color=(255, 150, 220)),
    "AGRICULTURAL LAB":      dict(sprite="greenhouse",    anchor=(0.73, 0.77), w=0.21, color=(120, 255, 130)),
    "LANDING ZONE":          dict(sprite=None,            anchor=(0.36, 0.89), w=0.16, color=(255, 255, 255)),
    "RESOURCE ZONE":         dict(sprite=None,            anchor=(0.52, 0.64), w=0.10, color=(255, 216, 79)),
}
LINKS = [("LANDING ZONE", "LUNAR HABITAT"), ("LUNAR HABITAT", "SOLAR POWER STATION"),
         ("LUNAR HABITAT", "COMMUNICATION STATION"), ("LUNAR HABITAT", "AGRICULTURAL LAB"),
         ("LUNAR HABITAT", "RESOURCE ZONE")]

_cache = {}
def sprite(name):
    if name not in _cache:
        im = cv2.imread(str(SPRITE_DIR / f"{name}.png"), cv2.IMREAD_UNCHANGED)
        if im is None: raise FileNotFoundError(f"Missing sprite assets/sprites/{name}.png")
        _cache[name] = im
    return _cache[name]

def roughness_map(img):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (0, 0), 2).astype(np.float32)
    m = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    return cv2.GaussianBlur(m, (0, 0), 12)

def snap_to_smooth(anchor, rough, radius=0.07):
    """Nudge an anchor to the smoothest nearby patch (image-texture proxy only)."""
    h, w = rough.shape; cx, cy = int(anchor[0] * w), int(anchor[1] * h)
    r = int(radius * w); best, bp = 1e18, (cx, cy)
    for dy in range(-r, r + 1, max(4, r // 8)):
        for dx in range(-r, r + 1, max(4, r // 8)):
            x, y = cx + dx, cy + dy
            if 0.05 * w < x < 0.95 * w and 0.12 * h < y < 0.95 * h:
                v = rough[y, x] + 0.002 * np.hypot(dx, dy)
                if v < best: best, bp = v, (x, y)
    return bp[0] / w, bp[1] / h

def _dashed(img, p, q, col, th=2, dash=14, gap=10):
    L = int(np.hypot(q[0] - p[0], q[1] - p[1]));
    if L == 0: return
    for s in range(0, L, dash + gap):
        a = (int(p[0] + (q[0] - p[0]) * s / L), int(p[1] + (q[1] - p[1]) * s / L))
        e = min(s + dash, L); b = (int(p[0] + (q[0] - p[0]) * e / L), int(p[1] + (q[1] - p[1]) * e / L))
        cv2.line(img, a, b, col, th, cv2.LINE_AA)

def _label(img, text, cx, y, col, fs):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
    x0, y0 = int(cx - tw / 2 - 8), int(y - th - 6)
    x0 = max(6, min(img.shape[1] - tw - 22, x0)); y0 = max(6, min(img.shape[0] - th - 20, y0))
    ov = img.copy(); cv2.rectangle(ov, (x0, y0), (x0 + tw + 16, y0 + th + 14), (25, 13, 8), -1)
    cv2.addWeighted(ov, .78, img, .22, 0, img)
    cv2.rectangle(img, (x0, y0), (x0 + tw + 16, y0 + th + 14), col, 1, cv2.LINE_AA)
    cv2.putText(img, text, (x0 + 8, y0 + th + 4), cv2.FONT_HERSHEY_SIMPLEX, fs, (245, 240, 235), 2, cv2.LINE_AA)

def _paste(base, spr, x, y):
    """Alpha-blend BGRA sprite with top-left (x, y); handles clipping."""
    h, w = spr.shape[:2]; H, W = base.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]; a = (s[:, :, 3:4].astype(np.float32) / 255)
    roi = base[y0:y1, x0:x1].astype(np.float32)
    base[y0:y1, x0:x1] = (s[:, :, :3] * a + roi * (1 - a)).astype(np.uint8)

def compose(terrain_bgr, show=None, scale=1.0, snap=True, labels=True, links=True):
    img = terrain_bgr.copy(); H, W = img.shape[:2]
    show = set(show or LAYOUT); rough = roughness_map(img) if snap else None
    lum = float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()) / 255
    k = 0.70 + 0.30 * min(1, lum * 1.6)                       # tone sprites toward scene brightness
    pos = {}
    for n, c in LAYOUT.items():
        if n in show:
            a = snap_to_smooth(c["anchor"], rough) if snap and c["sprite"] else c["anchor"]
            pos[n] = (int(a[0] * W), int(a[1] * H))
    scl = lambda y: 0.78 + 0.45 * (y / H)                     # depth: lower in frame = nearer = larger
    if links:
        for a, b in LINKS:
            if a in pos and b in pos:
                _dashed(img, pos[a], pos[b], (235, 235, 235), max(2, W // 500))
    for n in sorted(pos, key=lambda n: pos[n][1]):            # painter's order
        c, (x, y) = LAYOUT[n], pos[n]; wpx = int(c["w"] * W * scale * scl(y))
        if c["sprite"] is None:
            ov = img.copy(); axes = (wpx // 2, int(wpx * .27))
            if n == "LANDING ZONE":
                cv2.ellipse(ov, (x, y), axes, 0, 0, 360, (200, 205, 215), -1); cv2.addWeighted(ov, .30, img, .70, 0, img)
                cv2.ellipse(img, (x, y), axes, 0, 0, 360, (240, 240, 240), max(2, W // 400), cv2.LINE_AA)
                cv2.ellipse(img, (x, y), (axes[0] * 2 // 3, axes[1] * 2 // 3), 0, 0, 360, (240, 240, 240), 1, cv2.LINE_AA)
                cv2.putText(img, "H", (x - wpx // 14, y + wpx // 14), cv2.FONT_HERSHEY_SIMPLEX, wpx / 90, (245, 245, 245), max(2, W // 350), cv2.LINE_AA)
            else:
                cv2.ellipse(ov, (x, y), axes, 0, 0, 360, (255, 216, 79), -1); cv2.addWeighted(ov, .22, img, .78, 0, img)
                for i in range(-axes[0], axes[0], max(8, wpx // 7)):
                    cv2.line(img, (x + i, y - axes[1] // 2), (x + i + axes[1], y + axes[1] // 2), (255, 216, 79), 1, cv2.LINE_AA)
                cv2.ellipse(img, (x, y), axes, 0, 0, 360, (255, 216, 79), max(2, W // 450), cv2.LINE_AA)
            top = y - axes[1]
        else:
            s = sprite(c["sprite"]); hpx = int(s.shape[0] * wpx / s.shape[1])
            sp = cv2.resize(s, (wpx, hpx), interpolation=cv2.INTER_AREA)
            sp[:, :, :3] = np.clip(sp[:, :, :3].astype(np.float32) * k, 0, 255).astype(np.uint8)
            fade = int(hpx * 0.05); sp[hpx - fade:, :, 3] = (sp[hpx - fade:, :, 3] * np.linspace(1, .35, fade)[:, None]).astype(np.uint8)
            sh = np.zeros((H, W), np.float32)                  # soft contact shadow
            cv2.ellipse(sh, (x + wpx // 12, y), (int(wpx * .46), max(4, int(wpx * .10))), 0, 0, 360, 1, -1)
            sh = cv2.GaussianBlur(sh, (0, 0), max(3, wpx // 22))
            img = (img.astype(np.float32) * (1 - .55 * sh[..., None])).astype(np.uint8)
            _paste(img, sp, x - wpx // 2, y - int(hpx * .92)); top = y - hpx
        if labels:
            fs = max(0.45, W / 2300); _label(img, n, x, y + int(fs * 38) + (wpx // 12 if c["sprite"] else wpx // 5), c["color"], fs)
    return img, pos
