"""Realistic alpha-card trees for Roblox (Trunk / Branches / Leaves MeshParts + SurfaceAppearance).

Run (headless only):
  blender -b --factory-startup \
      --python gen_trees.py -- [--out DIR] [--only OakA,Birch] [--norender] [--noexport]

1 Blender unit = 1 stud, Z up in Blender (glTF export turns it into Y up), origin = trunk base.
Everything (geometry + textures) is generated here: no photos, no downloaded assets.
Textures are painted with numpy inside Blender's Python (periodic FFT noise, signed-distance leaves),
saved as PNG and embedded in the GLBs.
"""
import bpy, math, os, sys, json, random
import numpy as np
from mathutils import Vector, noise

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = arg("--out", HERE)
ONLY = arg("--only")
ROBLOX = os.path.join(OUT, "roblox")
TEX = os.path.join(ROBLOX, "textures")
RENDERS = os.path.join(OUT, "renders")
REF = arg("--ref", os.path.join(OUT, "reference.jpg"))
for d in (ROBLOX, TEX, RENDERS):
    os.makedirs(d, exist_ok=True)
UP = Vector((0, 0, 1))

# ----------------------------------------------------------------------------- textures (numpy)
# Arrays are (H, W, C), row 0 = bottom of the image (V = 0), values sRGB 0..1.

def fft_noise(h, w, fx, fy, rng):
    """Periodic (tileable) gaussian-filtered noise, fx / fy = feature frequency in cycles per image."""
    white = rng.standard_normal((h, w))
    ky = np.fft.fftfreq(h)[:, None] * h
    kx = np.fft.fftfreq(w)[None, :] * w
    f = np.exp(-((kx / fx) ** 2 + (ky / fy) ** 2))
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * f))
    return (n - n.min()) / (n.max() - n.min() + 1e-9)

def normal_from_height(hgt, strength, periodic=True):
    if periodic:
        dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
        dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(hgt)
    n = np.dstack([-dx * strength, -dy * strength, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5          # OpenGL convention (+V = green up), which glTF expects

def save_png(name, arr, noncolor=False):
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.ones((h, w))])
    img = bpy.data.images.new(name, w, h, alpha=True)
    if noncolor:
        img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    path = os.path.join(TEX, name + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img

def ramp(t, stops):
    """t array -> colour from [(pos, (r,g,b)), ...]."""
    pos = np.array([s[0] for s in stops]); col = np.array([s[1] for s in stops])
    return np.dstack([np.interp(t, pos, col[:, i]) for i in range(3)])

def bark_oak(rng, n=1024):
    ridge = fft_noise(n, n, 22, 3.0, rng)
    ridge = 1 - np.abs(ridge * 2 - 1) ** 0.7          # sharp furrows, rounded ridges
    plates = fft_noise(n, n, 9, 5, rng)
    cracks = np.clip((fft_noise(n, n, 40, 9, rng) - 0.62) * 6, 0, 1)   # horizontal breaks in the ridges
    fine = fft_noise(n, n, 160, 90, rng)
    hgt = 0.62 * ridge + 0.2 * plates + 0.18 * fine - 0.35 * cracks * ridge
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    col = ramp(hgt, [(0, (0.10, 0.09, 0.08)), (0.35, (0.24, 0.21, 0.18)), (0.7, (0.40, 0.37, 0.33)),
                     (1, (0.55, 0.52, 0.47))])
    lichen = np.clip((fft_noise(n, n, 6, 6, rng) - 0.62) * 3, 0, 1) * (hgt > 0.45)
    col = col * (1 - 0.35 * lichen[..., None]) + np.array([0.42, 0.46, 0.33]) * 0.35 * lichen[..., None]
    col *= (0.9 + 0.2 * fine)[..., None]
    return col, normal_from_height(hgt, 7.0)

def bark_birch(rng, n=1024):
    base = fft_noise(n, n, 5, 14, rng)
    lent = fft_noise(n, n, 7, 110, rng)                 # long horizontal lenticel dashes
    lent = np.clip((lent - 0.72) * 6, 0, 1)
    patch = fft_noise(n, n, 7, 9, rng) + 0.25 * fft_noise(n, n, 40, 40, rng)
    patch = np.clip((patch - 0.86) * 9, 0, 1)
    fine = fft_noise(n, n, 120, 200, rng)
    col = ramp(base, [(0, (0.70, 0.68, 0.63)), (1, (0.90, 0.89, 0.85))])
    col *= (0.93 + 0.1 * fine)[..., None]
    dark = np.maximum(lent * 0.85, patch)
    col = col * (1 - dark[..., None]) + np.array([0.08, 0.07, 0.07]) * dark[..., None]
    hgt = 0.5 * base + 0.3 * fine - 0.6 * dark
    return col, normal_from_height(hgt, 5.0)

def bark_fir(rng, n=1024):
    """fir / spruce: scaly grey-brown plates with reddish fresh bark in the cracks, faint vertical grain"""
    plates = fft_noise(n, n, 16, 11, rng)
    plates = np.clip((plates - 0.5) * 2.2 + 0.5, 0, 1)
    edge = 1 - np.clip(np.abs(fft_noise(n, n, 18, 13, rng) - 0.5) * 9, 0, 1)        # crack lines between plates
    grain = fft_noise(n, n, 60, 6, rng)
    fine = fft_noise(n, n, 150, 110, rng)
    hgt = 0.55 * plates + 0.15 * grain + 0.15 * fine - 0.45 * edge
    hgt = (hgt - hgt.min()) / (hgt.max() - hgt.min())
    col = ramp(hgt, [(0, (0.12, 0.07, 0.05)), (0.35, (0.30, 0.19, 0.14)), (0.65, (0.40, 0.33, 0.28)),
                     (1, (0.55, 0.50, 0.45))])
    col *= (0.9 + 0.2 * fine)[..., None]
    return col, normal_from_height(hgt, 6.0)

class Canvas:
    """RGBA + height painter; shapes composited 'over' with soft edges."""
    def __init__(self, n):
        self.n = n
        self.rgb = np.zeros((n, n, 3)); self.a = np.zeros((n, n)); self.h = np.zeros((n, n))

    def over(self, x0, x1, y0, y1, alpha, rgb, hgt):
        sl = (slice(y0, y1), slice(x0, x1))
        a = alpha
        self.rgb[sl] = self.rgb[sl] * (1 - a[..., None]) + rgb * a[..., None]
        self.h[sl] = self.h[sl] * (1 - a) + hgt * a
        self.a[sl] = self.a[sl] + a * (1 - self.a[sl])

    def grid(self, cx0, cx1, cy0, cy1):
        ys, xs = np.mgrid[cy0:cy1, cx0:cx1]
        return xs + 0.5, ys + 0.5

    def capsule_path(self, pts, r0, r1, rgb, clip):
        """Tapered stroke along pts (px), clipped to the cell rect clip=(x0,x1,y0,y1)."""
        pts = np.array(pts, float)
        seg = len(pts) - 1
        for i in range(seg):
            p, q = pts[i], pts[i + 1]
            ra = r0 + (r1 - r0) * i / seg; rb = r0 + (r1 - r0) * (i + 1) / seg
            m = max(ra, rb) + 2
            x0 = int(max(clip[0], min(p[0], q[0]) - m)); x1 = int(min(clip[1], max(p[0], q[0]) + m + 1))
            y0 = int(max(clip[2], min(p[1], q[1]) - m)); y1 = int(min(clip[3], max(p[1], q[1]) + m + 1))
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = self.grid(x0, x1, y0, y1)
            d = q - p; L2 = max(d @ d, 1e-6)
            t = np.clip(((xs - p[0]) * d[0] + (ys - p[1]) * d[1]) / L2, 0, 1)
            dist = np.hypot(xs - (p[0] + t * d[0]), ys - (p[1] + t * d[1]))
            r = ra + (rb - ra) * t
            a = np.clip(r - dist + 0.5, 0, 1)
            across = np.clip(dist / np.maximum(r, 0.5), 0, 1)
            shade = (1.08 - 0.45 * across ** 2)[..., None]          # lit centre, darker sides
            self.over(x0, x1, y0, y1, a, np.array(rgb) * shade, np.sqrt(1 - across ** 2) * r * 0.3)

    def leaf(self, base, ang, L, W, kind, rgb, vein_rgb, clip, fine):
        ca, sa = math.cos(ang), math.sin(ang)
        corners = [base + np.array([ca, sa]) * L * u + np.array([-sa, ca]) * W * 0.6 * v
                   for u in (0, 1) for v in (-1, 1)]
        xs_ = [c[0] for c in corners]; ys_ = [c[1] for c in corners]
        x0 = int(max(clip[0], min(xs_) - 2)); x1 = int(min(clip[1], max(xs_) + 2))
        y0 = int(max(clip[2], min(ys_) - 2)); y1 = int(min(clip[3], max(ys_) + 2))
        if x1 <= x0 or y1 <= y0:
            return
        xs, ys = self.grid(x0, x1, y0, y1)
        dx, dy = xs - base[0], ys - base[1]
        a = dx * ca + dy * sa; b = -dx * sa + dy * ca
        u = a / L; uc = np.clip(u, 0, 1)
        if kind == "oak":   # rounded lobes with deep sinuses, narrow base
            hw = 0.5 * W * np.sin(np.pi * uc ** 0.9) ** 0.55 * (0.55 + 0.45 * np.abs(np.sin(np.pi * uc * 4.6 + 0.4)))
        else:               # ovate, pointed tip, fine serration (birch / young)
            hw = 0.5 * W * np.sin(np.pi * uc ** 0.72) ** 0.9 * (1 - 0.08 * np.abs(np.sin(uc * L / 1.8)))
        sd = hw - np.abs(b)
        alpha = np.clip(sd * 0.9 + 0.5, 0, 1) * np.clip(u * L * 0.6, 0, 1) * np.clip((1 - u) * L * 0.6 + 0.5, 0, 1)
        if alpha.max() <= 0:
            return
        rel = np.clip(np.abs(b) / np.maximum(hw, 0.6), 0, 1)
        mid = np.exp(-(b / 0.9) ** 2) * (u < 0.95)
        per = L / 6.5
        ph = (a - np.abs(b) * 1.2) / per
        side = np.exp(-(((ph - np.round(ph)) * per) / 0.75) ** 2) * (rel < 0.82) * (u > 0.08)
        vein = np.clip(mid + 0.55 * side, 0, 1)
        col = np.array(rgb) * (1.05 - 0.22 * rel ** 1.5)[..., None] * (0.88 + 0.12 * uc)[..., None]
        col = col * (1 - 0.45 * vein[..., None]) + np.array(vein_rgb) * 0.45 * vein[..., None]
        col *= (0.9 + 0.2 * fine[y0:y1, x0:x1])[..., None]
        hgt = np.sqrt(np.clip(1 - rel ** 2, 0, 1)) * 2.0 - 0.6 * vein
        self.over(x0, x1, y0, y1, alpha, col, hgt)

    def finish(self, fill_rgb):
        # colour bleed under transparent pixels so mips/filters don't fringe white or black
        empty = self.a < 0.02
        self.rgb[empty] = fill_rgb
        return np.dstack([self.rgb, self.a]), normal_from_height(self.h * 3.0, 1.0, periodic=False)

LEAF_STYLE = {
    "oak":   dict(kind="oak", n=(9, 15), L=(0.30, 0.42), W=0.55, greens=[(0.15, 0.24, 0.12), (0.11, 0.19, 0.10),
             (0.19, 0.27, 0.14), (0.13, 0.22, 0.15)], vein=(0.42, 0.48, 0.26), stem=(0.30, 0.27, 0.17)),
    "birch": dict(kind="ovate", n=(14, 22), L=(0.17, 0.26), W=0.62, greens=[(0.36, 0.47, 0.16), (0.30, 0.42, 0.14),
             (0.42, 0.52, 0.19), (0.33, 0.45, 0.20)], vein=(0.62, 0.66, 0.32), stem=(0.35, 0.22, 0.14)),
    "young": dict(kind="ovate", n=(10, 16), L=(0.24, 0.34), W=0.5, greens=[(0.25, 0.39, 0.14), (0.21, 0.34, 0.12),
             (0.30, 0.43, 0.16), (0.24, 0.36, 0.17)], vein=(0.52, 0.58, 0.28), stem=(0.30, 0.26, 0.16)),
    # the realistic oak recoloured as a flowering tree: rounder petal-like leaves in pinks, pale centres
    "blossom": dict(kind="ovate", n=(16, 24), L=(0.15, 0.24), W=0.78, greens=[(0.92, 0.52, 0.62), (0.84, 0.42, 0.55),
             (0.97, 0.68, 0.76), (0.88, 0.50, 0.60)], vein=(1.0, 0.86, 0.92), stem=(0.32, 0.20, 0.17)),
}

# needle sprays for conifers: (needle greens, new-growth tip colour, twig colour)
NEEDLE_STYLE = {
    "fir": dict(greens=[(0.08, 0.21, 0.17), (0.06, 0.18, 0.15), (0.10, 0.24, 0.19), (0.07, 0.20, 0.18)],
                tip=(0.24, 0.42, 0.33), twig=(0.26, 0.19, 0.13)),
}

def needle_atlas(style, rng, n=1024, grid=4):
    """4 x 4 fir sprays: a central twig with paired laterals (frond widest near the base), short needles on both
    sides of every twig, angled forward; dark old needles, lighter blue-green new growth at the twig tips"""
    st = NEEDLE_STYLE[style]; cv = Canvas(n); S = n // grid
    greens = [np.array(g) for g in st["greens"]]; tip = np.array(st["tip"])
    def needles(pts, nl, layer, clip, gap=3.4):
        pts = np.array(pts, float)
        segl = np.hypot(*(pts[1:] - pts[:-1]).T); total = segl.sum()
        s = rng.uniform(0, gap)
        while s < total:
            i = min(int(np.searchsorted(np.cumsum(segl), s)), len(segl) - 1)
            w = (s - (np.cumsum(segl)[i] - segl[i])) / max(segl[i], 1e-6)
            p = pts[i] + (pts[i + 1] - pts[i]) * w
            d = (pts[i + 1] - pts[i]) / max(segl[i], 1e-6)
            f = s / total                                                       # 0 base .. 1 twig tip
            for side in (-1, 1):
                if rng.random() < 0.12:
                    continue
                a = math.atan2(d[1], d[0]) + side * rng.uniform(0.45, 1.25) * (1 - 0.35 * f)
                L = nl * (1 - 0.45 * f ** 2) * rng.uniform(0.75, 1.15)
                q = p + np.array([math.cos(a), math.sin(a)]) * L
                g = greens[rng.integers(len(greens))] * rng.uniform(0.75, 1.25)
                if f > 0.72 and layer == 1:
                    g = g + (tip - g) * min(1.0, (f - 0.72) / 0.2) * rng.uniform(0.6, 1.0)
                if layer == 0:
                    g = g * 0.6                                                  # under layer: shadowed needles
                cv.capsule_path([p, q], 1.6, 0.6, g, clip)
            s += gap * rng.uniform(0.7, 1.2)
    for cj in range(grid):
        for ci in range(grid):
            x0, y0 = ci * S, cj * S
            clip = (x0 + 3, x0 + S - 3, y0 + 3, y0 + S - 3)
            bend = rng.uniform(-0.12, 0.12) * S
            top = S * rng.uniform(0.86, 0.93)
            stem = [np.array([x0 + S * 0.5 + bend * t * t, y0 + 5 + t * top]) for t in np.linspace(0, 1, 9)]
            twigs = [stem]
            m = rng.integers(7, 10)
            for k in range(m):
                t = 0.06 + 0.8 * k / (m - 1) + rng.uniform(-0.03, 0.03)
                i = min(int(t * 8), 7); w = t * 8 - i
                p = stem[i] + (stem[i + 1] - stem[i]) * w
                for side in (-1, 1):
                    if rng.random() < 0.1:
                        continue
                    a = math.pi / 2 + side * rng.uniform(1.0, 1.25)
                    L = S * (0.46 * (1 - t) ** 0.7 + 0.06) * rng.uniform(0.7, 1.15)
                    pts = [p]
                    for j in range(4):
                        a -= side * rng.uniform(0.0, 0.2)                       # laterals curve forward, irregularly
                        pts.append(pts[-1] + np.array([math.cos(a), math.sin(a)]) * L / 4)
                    twigs.append(pts)
            nl = S * 0.075
            for tw in twigs:
                needles(tw, nl, 0, clip, gap=3.6)
            for k, tw in enumerate(twigs):
                cv.capsule_path(tw, 2.6 if k == 0 else 1.5, 0.7, st["twig"], clip)
            for tw in twigs:
                needles(tw, nl, 1, clip, gap=2.9)
    return cv.finish(greens[0] * 0.8)

def leaf_atlas(style, rng, n=1024, grid=4):
    st = LEAF_STYLE[style]; cv = Canvas(n); S = n // grid
    fine = fft_noise(n, n, 90, 90, rng)
    for cj in range(grid):
        for ci in range(grid):
            x0, y0 = ci * S, cj * S
            clip = (x0 + 3, x0 + S - 3, y0 + 3, y0 + S - 3)
            # cluster stem from bottom centre curving up
            bend = rng.uniform(-0.18, 0.18) * S
            stem = [np.array([x0 + S * 0.5 + bend * (t ** 2), y0 + 6 + t * S * 0.72]) for t in np.linspace(0, 1, 7)]
            cv.capsule_path(stem, 2.6, 1.0, st["stem"], clip)
            cnt = rng.integers(*st["n"]) - (4 if (ci + cj) % 5 == 0 else 0)   # a few sparser cells
            leaves = []
            for k in range(cnt):
                t = 0.12 + 0.88 * (k / max(cnt - 1, 1)) ** 0.8
                p = stem[0] + (stem[-1] - stem[0]) * t + np.array([bend * t * t - bend * t, 0])
                side = 1 if k % 2 else -1
                up = math.pi / 2
                ang = up + side * rng.uniform(0.6, 1.5) * (1.05 - 0.6 * t) + rng.normal(0, 0.15)
                if rng.random() < 0.45:  # filler leaf anywhere in the upper cell (rounder clusters)
                    p = np.array([x0 + rng.uniform(0.18, 0.82) * S, y0 + rng.uniform(0.25, 0.75) * S])
                    ang = rng.uniform(0, 2 * math.pi)
                L = rng.uniform(*st["L"]) * S
                tip = p + np.array([math.cos(ang), math.sin(ang)]) * L
                for _ in range(6):     # keep the leaf inside the cell
                    if clip[0] + 4 < tip[0] < clip[1] - 4 and clip[2] + 4 < tip[1] < clip[3] - 4:
                        break
                    L *= 0.8; tip = p + np.array([math.cos(ang), math.sin(ang)]) * L
                g = np.array(st["greens"][rng.integers(len(st["greens"]))]) * rng.uniform(0.72, 1.18)
                leaves.append((rng.random(), p, ang, L, g))
            for _, p, ang, L, g in sorted(leaves, key=lambda x: x[0]):
                base = p + np.array([math.cos(ang), math.sin(ang)]) * L * 0.08
                cv.capsule_path([p, base], 1.2, 1.0, st["stem"], clip)
                cv.leaf(base, ang, L, L * st["W"], st["kind"], g, st["vein"], clip, fine)
    return cv.finish(np.array(st["greens"][0]) * 0.8)

TWIG_RGB = {"oak": (0.27, 0.24, 0.20), "birch": (0.22, 0.13, 0.10), "young": (0.30, 0.26, 0.20), "fir": (0.22, 0.17, 0.13)}

def twig_atlas(style, rng, n=512, grid=2):
    cv = Canvas(n); S = n // grid; rgb = TWIG_RGB[style]
    def twig(p, ang, L, r, depth, clip):
        pts = [p]; a = ang
        for i in range(5):
            a += rng.normal(0, 0.12)
            pts.append(pts[-1] + np.array([math.cos(a), math.sin(a)]) * L / 5)
        cv.capsule_path(pts, r, max(r * 0.3, 0.7), rgb, clip)
        if depth == 0:
            return
        for k in range(rng.integers(2, 5)):
            t = rng.uniform(0.2, 0.85); i = int(t * 5)
            side = 1 if k % 2 else -1
            twig(pts[i], a + side * rng.uniform(0.4, 0.8), L * rng.uniform(0.3, 0.5), r * 0.55, depth - 1, clip)
    for cj in range(grid):
        for ci in range(grid):
            x0, y0 = ci * S, cj * S
            clip = (x0 + 2, x0 + S - 2, y0 + 2, y0 + S - 2)
            twig(np.array([x0 + S * 0.5, y0 + 4.0]), math.pi / 2 + rng.normal(0, 0.08), S * 0.9, 5.5, 2, clip)
    return cv.finish(np.array(rgb))

# ----------------------------------------------------------------------------- skeleton

class Branch:
    def __init__(self, pts, rads, level):
        self.pts, self.rads, self.level = pts, rads, level
        self.children = []

    def at(self, t):
        f = t * (len(self.pts) - 1); i = min(int(f), len(self.pts) - 2); w = f - i
        p = self.pts[i].lerp(self.pts[i + 1], w)
        r = self.rads[i] * (1 - w) + self.rads[i + 1] * w
        d = (self.pts[i + 1] - self.pts[i]).normalized()
        return p, r, d

    def length(self):
        return sum((self.pts[i + 1] - self.pts[i]).length for i in range(len(self.pts) - 1))

def rand_unit(rng):
    v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
    return v.normalized() if v.length > 1e-6 else UP.copy()

class Tree:
    def __init__(self, P):
        self.P = P
        self.rng = random.Random(P["seed"])
        self.branches = []
        c = P["env"]["c"]; self.c = Vector(c); self.r = Vector(P["env"]["r"])

    def env(self, q):
        """<1 inside the lumpy crown envelope."""
        d = q - self.c
        e = Vector((d.x / self.r.x, d.y / self.r.y, d.z / self.r.z))
        lump = 1 + self.P["env"].get("lump", 0.15) * noise.noise(e.normalized() * 1.7 + Vector((self.P["seed"], 0, 0))
                                                                 if e.length > 1e-6 else Vector((0, 0, 0)))
        return e.length / lump

    def grow(self, p0, d, length, r0, level, rtip=None):
        L = self.P["levels"][level]
        segs = L["segs"]; step = length / segs
        pts, rads = [p0.copy()], [r0]
        rtip = rtip if rtip is not None else r0 * L.get("taper", 0.35)
        for i in range(segs):
            f = (i + 1) / segs
            d = (d + Vector((0, 0, -1)) * L["droop"] * f + UP * L["photo"] + rand_unit(self.rng) * L["wander"])
            d.normalize()
            pts.append(pts[-1] + d * step)
            rads.append(r0 + (rtip - r0) * f ** 0.9)
        b = Branch(pts, rads, level)
        self.branches.append(b)
        return b

    def children_of(self, b):
        lv = b.level + 1
        if lv >= len(self.P["levels"]):
            return
        L = self.P["levels"][lv]
        n = L["count"]
        if isinstance(n, (tuple, list)):
            n = self.rng.randint(*n)
        blen = b.length()
        phi0 = self.rng.uniform(0, 2 * math.pi)
        for k in range(n):
            t = L["t"][0] + (L["t"][1] - L["t"][0]) * (k + self.rng.uniform(0.2, 0.8)) / n
            p, r, d = b.at(t)
            a = d.orthogonal().normalized(); c = d.cross(a)
            phi = phi0 + (k * 2 * math.pi / n if lv == 1 else k * 2.4) + self.rng.uniform(-0.35, 0.35)
            perp = a * math.cos(phi) + c * math.sin(phi)
            if lv == 1 and self.P.get("spread_dir"):       # bias limbs to a side (asymmetric silhouettes)
                perp = (perp + Vector(self.P["spread_dir"]) * self.rng.uniform(0, 0.9)).normalized()
            ang = math.radians(L["angle"] + self.rng.uniform(-L["angle_j"], L["angle_j"]))
            cd = (d * math.cos(ang) + perp * math.sin(ang)).normalized()
            length = (L["len"] if lv == 1 else blen * L["len"] * (1 - L.get("shorten", 0.45) * t))
            length *= self.rng.uniform(0.75, 1.15)
            for _ in range(12):     # fit inside the crown envelope
                if self.env(p + cd * length) <= 1.0 or length < 0.4:
                    break
                length *= 0.88
            cr = max(r * L["rr"], L.get("rmin", 0.03))
            child = self.grow(p, cd, length, cr, lv)
            b.children.append(child)
            self.children_of(child)

    def build(self):
        if self.P.get("kind") == "conifer":
            return self.build_conifer()
        T = self.P["trunk"]
        d = (UP + Vector(T.get("lean", (0, 0, 0)))).normalized()
        trunk = self.grow(Vector((0, 0, -0.5)), d, T["h"], T["r"], 0, rtip=T["r"] * T.get("top", 0.45))
        self.children_of(trunk)
        if T.get("leader"):       # central leader continuing past the split
            p, r, dd = trunk.at(1.0)
            lead = self.grow(p, (dd + UP).normalized(), T["leader"], r * 0.8, 1)
            self.children_of(lead)
        if T.get("roots"):
            self.grow_roots(T)
        return self

    def grow_roots(self, T):
        """surface roots: leave the trunk foot outward and down, then snake along the ground (z ~ -0.3), tapering"""
        R = T["roots"]; rng = self.rng; n = R["n"]
        for k in range(n):
            a = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
            out = Vector((math.cos(a), math.sin(a), 0))
            p = out * T["r"] * 0.45 + Vector((0, 0, R.get("z0", 1.0) * rng.uniform(0.7, 1.25)))
            d = (out - UP * R.get("dip", 0.7)).normalized()
            L = R["len"] * rng.uniform(0.6, 1.2); segs = 7; step = L / segs
            r0 = T["r"] * R["r"] * rng.uniform(0.75, 1.15)
            pts, rads = [p.copy()], [r0]
            for i in range(segs):
                f = (i + 1) / segs
                d = (d + rand_unit(rng) * 0.3 - UP * 0.1 * f).normalized()
                q = pts[-1] + d * step
                floor = -0.3 + 0.25 * noise.noise(q * 0.6 + Vector((self.P["seed"], 1.7, 0)))
                if q.z < floor:
                    q.z = floor; d.z = max(d.z, 0.0); d.normalize()
                pts.append(q); rads.append(r0 * (1 - 0.85 * f ** 0.8) + 0.05)
            pts[-1].z = min(pts[-1].z, -0.7)                                # tip dives into the soil
            b = Branch(pts, rads, 1); b.root = True
            self.branches.append(b)

    # ---- conifer: straight tapered trunk, whorls of drooping branches, flat lateral sprays (atlas-drawn)
    def build_conifer(self):
        P = self.P; T = P["trunk"]; W = P["whorl"]; rng = self.rng
        trunk = self.grow(Vector((0, 0, -0.5)), UP.copy(), T["h"] + 0.5, T["r"], 0, rtip=T["r"] * 0.06)
        h = T["h"]; z = W["z0"]; phase = rng.uniform(0, 2 * math.pi); wk = 0
        while z < h * 0.985:
            t = (z - W["z0"]) / (h - W["z0"])                       # 0 lowest whorl .. 1 top
            n = rng.randint(*W["n"])
            Lw = W["Lmax"] * (1 - t) ** W["Lexp"] + W["Lmin"]
            elev = math.radians(W["elev"][0] + (W["elev"][1] - W["elev"][0]) * t)
            p, r, _ = trunk.at(min((z + 0.5) / (h + 0.5), 1.0))
            for k in range(n):
                phi = phase + wk * 2.39996 + k * 2 * math.pi / n + rng.uniform(-0.25, 0.25)
                out = Vector((math.cos(phi), math.sin(phi), 0))
                e = elev + math.radians(rng.uniform(-6, 6))
                d = (out * math.cos(e) + UP * math.sin(e)).normalized()
                L = Lw * rng.uniform(0.82, 1.12)
                b = self.grow(p + d * r * 0.6, d, L, max(r * W["rr"], 0.035), 1)
                b.wt = t
                self.laterals(b, t)
            z += W["dz"] * rng.uniform(0.75, 1.25) * (1 - 0.35 * t)
            wk += 1
        self.trunk = trunk
        return self

    def laterals(self, b, t):
        """paired side sprays in the (roughly horizontal) plane of the branch, shorter toward its tip"""
        A = self.P["lat"]; rng = self.rng; blen = b.length()
        if blen < A["min_len"]:
            return
        m = max(1, int(blen / A["spacing"]))
        for i in range(m):
            tt = 0.2 + 0.72 * (i + rng.uniform(0.2, 0.8)) / m
            p, r, d = b.at(tt)
            side = d.cross(UP)
            if side.length < 1e-3:
                continue
            side.normalize()
            for sg in ((-1, 1) if rng.random() < 0.75 else ((-1,) if i % 2 else (1,))):
                a = math.radians(A["angle"] + rng.uniform(-12, 12))
                cd = (d * math.cos(a) + side * sg * math.sin(a) + UP * rng.uniform(-0.25, 0.1)).normalized()
                L = blen * A["len"] * (1 - 0.6 * tt) * rng.uniform(0.75, 1.15)
                c = self.grow(p, cd, L, max(r * 0.6, 0.03), 2)
                c.wt = t

# ----------------------------------------------------------------------------- meshes

SIDES = [12, 8, 6, 4, 3]

def tube_mesh(tree, bark_tile):
    verts, uvs, faces = [], [], []
    flare = tree.P["trunk"].get("flare", 0.0)
    seed = tree.P["seed"]
    sides_t = tree.P.get("sides", SIDES)
    gnarl = tree.P["trunk"].get("gnarl", 0.07)
    for b in tree.branches:
        if b.level >= tree.P.get("tube_max", 99):
            continue                                           # thin sprays: drawn in the needle atlas only
        sides = sides_t[min(b.level, len(sides_t) - 1)]
        if b.rads[0] < 0.07:
            sides = 3
        pts = b.pts
        n = len(pts)
        Ts = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
        N = Ts[0].orthogonal().normalized()
        vacc = 0.0
        urep = max(1, round(2 * math.pi * b.rads[0] / bark_tile))
        base_idx = len(verts)
        for i in range(n):
            T = Ts[i]
            N = (N - T * N.dot(T)).normalized()
            B = T.cross(N)
            if i > 0:
                vacc += (pts[i] - pts[i - 1]).length / bark_tile
            for j in range(sides + 1):
                th = 2 * math.pi * j / sides
                r = b.rads[i]
                if b.level == 0:
                    z = pts[i].z
                    fl = flare * math.exp(-max(z + 0.5, 0) / 1.1)
                    r *= 1 + fl * (1 + 0.5 * math.sin(5 * th + seed))       # lobed root flare
                    r *= 1 + gnarl * noise.noise(Vector((math.cos(th) * 1.3, math.sin(th) * 1.3, z * 0.6 + seed)))
                off = N * math.cos(th) + B * math.sin(th)
                verts.append(pts[i] + off * r)
                uvs.append((urep * j / sides, vacc))
        for i in range(n - 1):
            for j in range(sides):
                a = base_idx + i * (sides + 1) + j
                bb = a + sides + 1
                faces.append((a, a + 1, bb + 1, bb))
    return verts, uvs, faces, None

def basis_card(n, up):
    up = (up - n * up.dot(n))
    if up.length < 1e-4:
        up = n.orthogonal()
    up.normalize()
    right = up.cross(n).normalized()
    return right, up

def card_quads(tree, leaves=True):
    """Leaf-cluster cards (folded, 4 tris) or crossed twig cards (2 x 2 tris)."""
    P = tree.P; rng = random.Random(P["seed"] * 7 + (1 if leaves else 2))
    LP = P["leaf"]
    verts, uvs, faces, norms = [], [], [], []
    grid = 4 if leaves else 2
    inset = 1.5 / (1024 if leaves else 512)
    def add_card(center_base, nrm, upv, w, h, cell, fold, crown_n):
        right, up = basis_card(nrm, upv)
        ci, cj = cell
        u0, v0 = ci / grid + inset, cj / grid + inset
        du, dv = 1 / grid - 2 * inset, 1 / grid - 2 * inset
        k = len(verts)
        for row, vy in ((0, 0.0), (1, 1.0)):
            for col, ux in ((0, -0.5), (1, 0.0), (2, 0.5)):
                p = center_base + right * (ux * w) + up * (vy * h)
                if col == 1:
                    p = p - nrm * fold * w
                verts.append(p)
                uvs.append((u0 + du * (ux + 0.5), v0 + dv * vy))
                bent = (nrm * 0.35 + crown_n * 0.65)
                norms.append(bent.normalized())
        faces.append((k, k + 1, k + 4, k + 3)); faces.append((k + 1, k + 2, k + 5, k + 4))
    def crown_normal(p):
        d = p - tree.c
        return Vector((d.x / tree.r.x ** 2, d.y / tree.r.y ** 2, d.z / tree.r.z ** 2 + 0.02)).normalized()
    count = 0
    for b in tree.branches:
        if leaves:
            if b.level < LP["min_level"]:
                continue
            blen = b.length()
            nstep = max(1, int(blen / LP["spacing"]))
            spots = [(LP["t0"] + (1 - LP["t0"]) * (s + rng.random()) / nstep) for s in range(nstep)]
            if not b.children:
                spots += [1.0] * LP["tip"]
            spots = [t for t in spots for _ in range(LP.get("per", 1))]
            for t in spots:
                p, r, d = b.at(min(t, 1.0))
                p = p + rand_unit(rng) * LP["jit"]
                if noise.noise(p * LP["gap_f"] + Vector((P["seed"], 3.1, 0))) < LP["gap_t"]:
                    continue                                    # sky holes
                if p.z < LP.get("zmin", -99):
                    continue
                cn = crown_normal(p)
                e = tree.env(p)
                if e < LP.get("inner", 0.0) and rng.random() < 0.6:
                    continue                                    # thin the hidden core
                nrm = (cn * LP["out"] + UP * LP["upw"] + rand_unit(rng) * LP["rnd"]).normalized()
                upv = (d + rand_unit(rng) * 0.6 + Vector((0, 0, -LP.get("hang", 0.0)))).normalized()
                s = rng.uniform(*LP["size"]) * (0.8 + 0.25 * min(e, 1.2))
                cell = (rng.randrange(grid), rng.randrange(grid))
                add_card(p - upv * s * 0.12, nrm, upv, s, s, cell, 0.12, cn)
                count += 1
        else:
            if b.level < LP["twig_level"] or (b.children and b.level < len(P["levels"]) - 1):
                continue
            for _ in range(LP.get("twigs_per_tip", 1)):
                p, r, d = b.at(rng.uniform(0.35, 0.85))
                s = rng.uniform(*LP["twig_size"])
                upv = (d + rand_unit(rng) * 0.35 + Vector((0, 0, -LP.get("twig_hang", 0.0)))).normalized()
                n1 = upv.orthogonal().normalized()
                rot = rng.uniform(0, math.pi)
                n1 = (n1 * math.cos(rot) + upv.cross(n1) * math.sin(rot)).normalized()
                cell = (rng.randrange(grid), rng.randrange(grid))
                for nn in (n1, upv.cross(n1).normalized()):
                    add_card(p - upv * s * 0.05, nn, upv, s * 0.7, s, cell, 0.0, nn)
                count += 1
    return verts, uvs, faces, norms

def conifer_cards(tree, leaves=True):
    """needle-spray cards along every branch / lateral: most lie in the spray plane (normal ~up, tilted out),
    some hang under the branch (pendulous spruce curtains); a spike of crossed cards forms the leader tip.
    Twig cards (Branches part): dead bare twigs on the inner lower branches."""
    P = tree.P; N = P["needle"]; rng = random.Random(P["seed"] * 7 + (1 if leaves else 2))
    verts, uvs, faces, norms = [], [], [], []
    grid = 4 if leaves else 2
    inset = 1.5 / (1024 if leaves else 512)
    h = P["trunk"]["h"]; z0 = P["whorl"]["z0"]; R0 = P["whorl"]["Lmax"] + P["whorl"]["Lmin"]
    def crown_n(p):
        """outward normal of the cone (lighting reads as one crown)"""
        rad = Vector((p.x, p.y, 0))
        rad = rad.normalized() if rad.length > 1e-4 else Vector((1, 0, 0))
        slope = R0 / max(h - z0, 1)
        return (rad + UP * slope).normalized()
    def add(base, nrm, upv, w, hh, fold, cn):
        right, up = basis_card(nrm, upv)
        ci, cj = rng.randrange(grid), rng.randrange(grid)
        u0, v0 = ci / grid + inset, cj / grid + inset
        du = dv = 1 / grid - 2 * inset
        k = len(verts)
        for vy in (0.0, 1.0):
            for ux in (-0.5, 0.0, 0.5):
                p = base + right * (ux * w) + up * (vy * hh)
                if ux == 0.0:
                    p = p + nrm * fold * w                     # ridge up: sprays arch like real fronds
                verts.append(p); uvs.append((u0 + du * (ux + 0.5), v0 + dv * vy))
                norms.append((nrm * N.get("own", 0.35) + cn * (1 - N.get("own", 0.35))).normalized())
        faces.append((k, k + 1, k + 4, k + 3)); faces.append((k + 1, k + 2, k + 5, k + 4))
    if not leaves:
        for b in tree.branches:
            if b.level != 1 or getattr(b, "wt", 1) > 0.45:
                continue
            if rng.random() > N.get("twig_p", 0.5):
                continue
            p, r, d = b.at(rng.uniform(0.15, 0.4))
            s = rng.uniform(*N["twig_size"])
            n1 = d.cross(UP).normalized() if d.cross(UP).length > 1e-3 else d.orthogonal().normalized()
            for nn in (n1, d.cross(n1).normalized()):
                add(p - d * s * 0.05, nn, d, s * 0.7, s, 0.0, nn)
        return verts, uvs, faces, norms
    for b in tree.branches:
        if b.level == 0:
            continue
        blen = b.length(); wt = getattr(b, "wt", 0.5)
        sz = N["size"][0] * (0.55 + 0.45 * min(1.0, (1 - wt) * 2.5)) + (N["size"][1] - N["size"][0]) * (1 - wt) ** 0.8
        sz = min(sz, blen * 1.25 + 0.4)
        step = N["spacing"] * (1.0 if b.level == 1 else 1.3)
        m = max(1, int(blen / step))
        spots = [N["t0"] + (1 - N["t0"]) * (i + rng.random()) / m for i in range(m)] + [1.0]
        for t in spots:
            p, r, d = b.at(min(t, 1.0))
            if noise.noise(p * N["gap_f"] + Vector((P["seed"], 3.1, 0))) < N["gap_t"]:
                continue
            cn = crown_n(p)
            s = sz * rng.uniform(0.75, 1.1) * ((0.5 + 0.35 * (1 - wt)) if t >= 1.0 else 1.0)
            if rng.random() < N["hang"] * (1 - 0.7 * wt):
                # pendulous curtain under the branch: card points down, faces out of the cone
                upv = (d * 0.35 - UP + rand_unit(rng) * 0.2).normalized()
                nrm = (cn * 0.8 + rand_unit(rng) * 0.3).normalized()
                add(p + UP * 0.1, nrm, upv, s * 0.75, s * 0.95, 0.06, cn)
            else:
                upv = (d + rand_unit(rng) * 0.25 - UP * N.get("droop", 0.15)).normalized()
                flat = (UP - upv * UP.dot(upv)).normalized()
                nrm = (flat * N["up"] + cn * N["out"] + rand_unit(rng) * N["rnd"]).normalized()
                add(p - upv * s * 0.1, nrm, upv, s * 0.85, s, 0.1, cn)
    # leader spike: crossed vertical cards on the top 9% of the trunk
    top = tree.trunk.pts[-1]
    for k in range(N.get("spike", 3)):
        a = k * math.pi / N.get("spike", 3)
        nn = Vector((math.cos(a), math.sin(a), 0))
        s = h * 0.07
        add(top - UP * s * 0.95, nn, UP, s * 0.32, s * 1.05, 0.0, (nn + UP).normalized())
    return verts, uvs, faces, norms

def make_object(name, data, mat, coll):
    verts, uvs, faces, norms = data
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    loop_uv = [c for f in faces for vi in f for c in uvs[vi]]
    uvl.data.foreach_set("uv", loop_uv)
    me.polygons.foreach_set("use_smooth", [True] * len(faces))
    if norms:
        me.normals_split_custom_set_from_vertices([tuple(n) for n in norms])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob

def material(name, color_img, normal_img, alpha, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexImage"); tc.image = color_img
    nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    m.use_backface_culling = True               # solid bark: single-sided
    if alpha:
        nt.links.new(tc.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.use_backface_culling = False          # -> glTF doubleSided
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
        if hasattr(m, "use_transparent_shadow"):
            m.use_transparent_shadow = True
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = normal_img
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = rough
    return m

# ----------------------------------------------------------------------------- species

def LV(count, t, angle, angle_j, ln, rr, segs, droop, photo, wander, **kw):
    d = dict(count=count, t=t, angle=angle, angle_j=angle_j, len=ln, rr=rr, segs=segs,
             droop=droop, photo=photo, wander=wander)
    d.update(kw); return d

LEAF_OAK = dict(min_level=2, spacing=0.38, per=1, t0=0.2, tip=4, jit=0.9, gap_f=0.22, gap_t=-0.2, inner=0.45,
                out=0.9, upw=0.22, rnd=0.38, size=(2.8, 4.0), twig_level=2, twig_size=(1.4, 2.2), twigs_per_tip=1)

TREES = {
    # 1: like the reference: short trunk, 5 spreading limbs, broad irregular dome ~30 x 24
    "OakA": dict(seed=11, tex="oak", bark_tile=3.5,
        trunk=dict(h=9.0, r=0.95, top=0.5, flare=0.9, lean=(0.04, 0.02, 0), leader=6.0),
        env=dict(c=(0, 0, 15.0), r=(14.5, 14.0, 10.0), lump=0.22),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 10, 0, 0.02, 0.04),
                LV(5, (0.5, 1.0), 52, 12, 14.0, 0.58, 8, 0.10, 0.08, 0.12),
                LV((4, 6), (0.22, 1.0), 42, 14, 0.55, 0.55, 5, 0.15, 0.12, 0.18, shorten=0.5),
                LV((3, 5), (0.3, 1.0), 40, 15, 0.55, 0.55, 3, 0.20, 0.08, 0.25, rmin=0.04)],
        leaf=dict(LEAF_OAK, zmin=9.5)),
    # 2: variant oak: two-leader fork low on the trunk, taller and narrower, leaning crown with one long side limb
    "OakB": dict(seed=29, tex="oak", bark_tile=3.5, spread_dir=(0.9, 0.3, 0),
        trunk=dict(h=6.5, r=1.1, top=0.6, flare=1.0, lean=(-0.08, 0, 0), leader=15.0),
        env=dict(c=(3.0, 0, 18.5), r=(13.0, 11.0, 13.5), lump=0.28),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 8, 0, 0.02, 0.04),
                LV(4, (0.55, 1.0), 38, 10, 17.0, 0.62, 8, 0.06, 0.14, 0.12),
                LV((4, 6), (0.2, 1.0), 38, 14, 0.5, 0.52, 5, 0.18, 0.14, 0.2, shorten=0.5),
                LV((3, 4), (0.3, 1.0), 40, 15, 0.55, 0.55, 3, 0.25, 0.08, 0.25, rmin=0.04)],
        leaf=dict(LEAF_OAK, gap_t=-0.05, size=(2.4, 3.4))),
    # 3: birch: slender white trunk with a leader, narrow oval crown, fine hanging twigs, small bright leaves
    "Birch": dict(seed=5, tex="birch", bark_tile=2.5,
        trunk=dict(h=11.0, r=0.5, top=0.5, flare=0.45, lean=(0.03, -0.02, 0), leader=12.0),
        env=dict(c=(0, 0, 16.5), r=(7.5, 7.5, 10.5), lump=0.18),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 10, 0, 0.02, 0.03),
                LV(7, (0.45, 1.0), 40, 12, 6.5, 0.5, 6, 0.12, 0.10, 0.12),
                LV((3, 5), (0.25, 1.0), 45, 15, 0.6, 0.55, 4, 0.40, 0.0, 0.18, shorten=0.4),
                LV((2, 4), (0.3, 1.0), 40, 15, 0.6, 0.6, 3, 0.65, 0.0, 0.2, rmin=0.03)],
        leaf=dict(LEAF_OAK, min_level=1, t0=0.4, spacing=0.4, size=(1.8, 2.6), jit=0.6, gap_f=0.28, gap_t=-0.3, inner=0.3,
                  upw=0.2, hang=0.6, twig_size=(1.5, 2.4), twig_hang=0.6)),
    # 4: young tree: thin trunk, 4 young limbs, small loose crown ~8 x 11
    "YoungTree": dict(seed=3, tex="young", bark_tile=2.5,
        trunk=dict(h=4.2, r=0.28, top=0.55, flare=0.35, lean=(0.05, 0.03, 0), leader=3.5),
        env=dict(c=(0, 0, 7.2), r=(4.0, 4.0, 4.2), lump=0.2),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 7, 0, 0.02, 0.05),
                LV(4, (0.55, 1.0), 40, 12, 4.0, 0.6, 5, 0.06, 0.12, 0.12),
                LV((3, 4), (0.3, 1.0), 42, 15, 0.55, 0.55, 3, 0.2, 0.06, 0.2, rmin=0.03)],
        leaf=dict(LEAF_OAK, min_level=1, spacing=0.55, t0=0.35, size=(1.5, 2.2), jit=0.35, gap_f=0.4,
                  gap_t=-0.2, inner=0.0, twig_level=1, twig_size=(1.0, 1.5))),
    # 5: hero: big leaning gnarled oak with surface roots (the valley islet tree); leans +X, crown reaches out over it
    "OakHero": dict(seed=41, tex="oak", bark_tile=4.0, spread_dir=(1.0, 0.1, 0),
        trunk=dict(h=15.0, r=1.7, top=0.5, flare=1.1, gnarl=0.2, lean=(1.05, 0.12, 0),
                   roots=dict(n=8, len=7.5, r=0.55, dip=0.8, z0=1.4)),
        env=dict(c=(10.0, 0.5, 18.5), r=(17.5, 15.0, 9.5), lump=0.18),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 12, 0, 0.075, 0.09),
                LV(6, (0.45, 1.0), 55, 14, 13.0, 0.55, 9, 0.12, 0.07, 0.16),
                LV((5, 7), (0.18, 1.0), 44, 15, 0.6, 0.55, 5, 0.14, 0.12, 0.2, shorten=0.45),
                LV((4, 6), (0.25, 1.0), 40, 15, 0.6, 0.55, 3, 0.18, 0.10, 0.25, rmin=0.04)],
        leaf=dict(LEAF_OAK, zmin=9.0, size=(3.0, 4.4), spacing=0.3, tip=5, gap_t=-0.3, inner=0.3)),
    # 6: flowering tree: OakB's habit, smaller, with the pink petal atlas (replaces the stylised cherry)
    "OakPink": dict(seed=17, tex="blossom", bark_tile=3.0, spread_dir=(0.5, 0.4, 0),
        trunk=dict(h=5.0, r=0.6, top=0.6, flare=0.8, lean=(0.1, 0.05, 0), leader=5.0),
        env=dict(c=(1.5, 0, 11.0), r=(8.5, 8.0, 6.5), lump=0.25),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 7, 0, 0.02, 0.05),
                LV(5, (0.5, 1.0), 48, 12, 8.5, 0.6, 7, 0.10, 0.10, 0.14),
                LV((3, 5), (0.22, 1.0), 42, 14, 0.55, 0.55, 4, 0.16, 0.10, 0.2, shorten=0.5),
                LV((2, 4), (0.3, 1.0), 40, 15, 0.55, 0.55, 3, 0.2, 0.06, 0.25, rmin=0.03)],
        leaf=dict(LEAF_OAK, zmin=6.0, size=(1.9, 2.8), spacing=0.36, gap_t=-0.3)),
    # 7-8: conifers (fir). Straight tapered trunk, whorls of drooping branches, flat needle sprays + hanging curtains
    "PineA": dict(seed=7, tex="fir", kind="conifer", bark_tile=2.5, tube_max=2, sides=[10, 3, 3],
        trunk=dict(h=32.0, r=0.75, flare=0.7),
        env=dict(c=(0, 0, 14.0), r=(7.0, 7.0, 18.0)),
        whorl=dict(z0=4.5, dz=1.75, n=(4, 6), Lmax=6.6, Lmin=0.8, Lexp=0.95, elev=(-12, 42), rr=0.4),
        lat=dict(spacing=1.3, len=0.42, angle=55, min_len=1.6),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 12, 0, 0.0, 0.012),
                LV(0, (0, 1), 0, 0, 0, 0.4, 3, 0.11, 0.035, 0.05, taper=0.3),
                LV(0, (0, 1), 0, 0, 0, 0.6, 2, 0.12, 0.0, 0.08, taper=0.4)],
        needle=dict(spacing=0.85, size=(2.8, 4.6), t0=0.12, gap_f=0.35, gap_t=-0.55, hang=0.38, up=0.75, out=0.45,
                    rnd=0.25, droop=0.2, own=0.4, spike=3, twig_p=0.5, twig_size=(1.2, 1.8))),
    "PineB": dict(seed=19, tex="fir", kind="conifer", bark_tile=2.5, tube_max=2, sides=[10, 3, 3],
        trunk=dict(h=21.0, r=0.62, flare=0.7),
        env=dict(c=(0, 0, 9.0), r=(7.0, 7.0, 12.0)),
        whorl=dict(z0=2.2, dz=1.35, n=(5, 6), Lmax=6.4, Lmin=0.7, Lexp=0.9, elev=(-14, 42), rr=0.42),
        lat=dict(spacing=1.15, len=0.45, angle=58, min_len=1.4),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 10, 0, 0.0, 0.012),
                LV(0, (0, 1), 0, 0, 0, 0.42, 3, 0.12, 0.03, 0.05, taper=0.3),
                LV(0, (0, 1), 0, 0, 0, 0.6, 2, 0.12, 0.0, 0.08, taper=0.4)],
        needle=dict(spacing=0.8, size=(2.8, 4.4), t0=0.12, gap_f=0.35, gap_t=-0.55, hang=0.4, up=0.75, out=0.45,
                    rnd=0.25, droop=0.2, own=0.4, spike=3, twig_p=0.5, twig_size=(1.1, 1.6))),
    # cheap background fir (cliff tops, far groves): same textures, fewer bigger sprays, ~3k tris
    "PineC": dict(seed=23, tex="fir", kind="conifer", bark_tile=2.5, tube_max=2, sides=[8, 3, 3],
        trunk=dict(h=24.0, r=0.6, flare=0.6),
        env=dict(c=(0, 0, 10.0), r=(6.5, 6.5, 13.0)),
        whorl=dict(z0=2.8, dz=2.3, n=(4, 5), Lmax=5.8, Lmin=0.8, Lexp=0.9, elev=(-12, 42), rr=0.42),
        lat=dict(spacing=1.7, len=0.45, angle=58, min_len=1.8),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 8, 0, 0.0, 0.012),
                LV(0, (0, 1), 0, 0, 0, 0.42, 3, 0.12, 0.03, 0.05, taper=0.3),
                LV(0, (0, 1), 0, 0, 0, 0.6, 2, 0.12, 0.0, 0.08, taper=0.4)],
        needle=dict(spacing=1.2, size=(3.4, 5.4), t0=0.12, gap_f=0.35, gap_t=-0.6, hang=0.35, up=0.75, out=0.45,
                    rnd=0.25, droop=0.2, own=0.4, spike=2, twig_p=0.3, twig_size=(1.1, 1.6))),
    # 9-10: street trees for a town (cheap, crown lifted over awnings / car roofs)
    "StreetOak": dict(seed=53, tex="oak", bark_tile=2.5, sides=[6, 4, 3, 3],
        trunk=dict(h=6.0, r=0.42, top=0.55, flare=0.5, lean=(0.03, 0.02, 0), leader=3.0),
        env=dict(c=(0, 0, 11.0), r=(6.0, 6.0, 5.0), lump=0.22),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 7, 0, 0.02, 0.03),
                LV(5, (0.6, 1.0), 48, 10, 6.0, 0.55, 5, 0.08, 0.10, 0.12),
                LV((4, 5), (0.2, 1.0), 42, 14, 0.6, 0.55, 3, 0.12, 0.10, 0.2, shorten=0.45, rmin=0.035)],
        leaf=dict(LEAF_OAK, min_level=1, t0=0.3, spacing=0.36, tip=5, size=(2.3, 3.2), jit=0.8, zmin=6.5, gap_t=-0.3, inner=0.2,
                  twig_level=1, twig_size=(1.2, 1.8))),
    "StreetBirch": dict(seed=61, tex="birch", bark_tile=2.2, sides=[8, 5, 4, 3],
        trunk=dict(h=8.0, r=0.36, top=0.5, flare=0.35, lean=(0.03, -0.02, 0), leader=6.5),
        env=dict(c=(0, 0, 12.5), r=(4.8, 4.8, 6.5), lump=0.18),
        levels=[LV(1, (0, 1), 0, 0, 0, 1, 8, 0, 0.02, 0.03),
                LV(6, (0.5, 1.0), 40, 12, 4.5, 0.5, 5, 0.12, 0.10, 0.12),
                LV((2, 4), (0.25, 1.0), 45, 15, 0.6, 0.55, 3, 0.40, 0.0, 0.18, shorten=0.4, rmin=0.03)],
        leaf=dict(LEAF_OAK, min_level=1, t0=0.3, spacing=0.34, size=(1.8, 2.6), jit=0.6, gap_f=0.28, gap_t=-0.35, inner=0.3,
                  upw=0.2, hang=0.6, zmin=7.0, twig_level=2, twig_size=(1.3, 2.0), twig_hang=0.6)),
}

# ----------------------------------------------------------------------------- scene / render / export

def setup_scene():
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng; break
        except TypeError:
            pass
    sc.render.resolution_x = sc.render.resolution_y = 560
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    if hasattr(sc, "eevee"):
        sc.eevee.taa_render_samples = 32
    w = bpy.data.worlds.new("Sky"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0.62, 0.76, 0.92, 1)
    cr.color_ramp.elements[1].position = 0.45; cr.color_ramp.elements[1].color = (0.06, 0.25, 0.70, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.8
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 2.6; sun.data.angle = math.radians(2)
    sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(35))
    sc.collection.objects.link(sun)
    gm = bpy.data.meshes.new("Ground")
    gm.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("Ground", gm); sc.collection.objects.link(g)
    gmat = bpy.data.materials.new("GroundMat"); gmat.use_nodes = True
    b = next(n for n in gmat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.30, 0.32, 0.38, 1); b.inputs["Roughness"].default_value = 1
    gm.materials.append(gmat)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); cam.data.lens = 45
    sc.collection.objects.link(cam); sc.camera = cam
    return sc, cam

def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def render_turntable(sc, cam, name, objs):
    pts = [ob.matrix_world @ Vector(v.co) for ob in objs for v in ob.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), 0)); hi = Vector((max(p.x for p in pts),
          max(p.y for p in pts), max(p.z for p in pts)))
    size = max(hi.x - lo.x, hi.y - lo.y, hi.z) * 1.05
    tgt = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z * 0.48))
    dist = size / (2 * math.tan(cam.data.angle / 2)) * 1.12
    paths = []
    for k, az in enumerate((30, 120, 210, 300)):
        a, el = math.radians(az), math.radians(9)
        cam.location = tgt + Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))) * dist
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        p = os.path.join(RENDERS, f"{name}_{k}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths

def load_px(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    return a

def resize(a, h):
    sh, sw = a.shape[:2]; w = int(sw * h / sh)
    ys = (np.arange(h) * sh / h).astype(int); xs = (np.arange(w) * sw / w).astype(int)
    return a[ys][:, xs]

def contact_sheet(name, paths):
    tiles = []
    if os.path.exists(REF):
        ref = load_px(REF)
        H = ref.shape[0]
        # tree crop in the 1159x753 reference screenshot (top-left px 380,205 -> 815,540); rows are bottom-up
        crop = ref[H - 540:H - 205, 380:815]
        tiles.append(resize(crop, 560))
    tiles += [load_px(p) for p in paths]
    sheet = np.concatenate([np.concatenate([t[..., :3], np.ones(t.shape[:2] + (1,))], 2) for t in tiles], 1)
    hgt, wid = sheet.shape[:2]
    img = bpy.data.images.new(name + "_sheet", wid, hgt)
    img.pixels.foreach_set(sheet.astype(np.float32).ravel())
    out = os.path.join(RENDERS, f"{name}_sheet.png")
    img.filepath_raw = out; img.file_format = "PNG"; img.save()
    return out

def export_glb(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_normals=True, export_texcoords=True,
                              export_materials="EXPORT", export_image_format="AUTO", export_animations=False)

# texture style -> (bark painter key, leaf atlas key, twig key); shared pieces are painted once
STYLES = {"oak": ("oak", "oak", "oak"), "birch": ("birch", "birch", "birch"), "young": ("young", "young", "young"),
          "blossom": ("oak", "blossom", "oak"), "fir": ("fir", "fir", "fir")}
SEEDS = {"oak": 17, "birch": 23, "young": 31, "blossom": 37, "fir": 43}
# map-tuned variants: same paint, leaf / needle atlas re-graded so the trees sit in that map's light.
# style: (base style, leaf rgb gain, saturation, bark rgb gain). Saved as <base>_<style suffix>_leaves_color.png etc.
TINTS = {
    "oak_v":   ("oak",   (1.55, 2.25, 1.35), 1.35, (1.15, 1.1, 1.05)),     # Mistvale Lake: bright saturated spring green
    "young_v": ("young", (1.35, 1.75, 1.15), 1.3,  (1.1, 1.05, 1.0)),
    "fir_v":   ("fir",   (1.25, 1.85, 1.6),  1.25, (1.15, 1.05, 1.0)),     # blue-green fir, lifted for the cyan haze
    "blossom_v": ("blossom", (1.18, 1.06, 1.0), 1.25, (1.15, 1.1, 1.05)),
    "oak_t":   ("oak",   (1.4, 1.75, 1.2),  1.2,  (1.1, 1.05, 1.0)),       # Maple Junction: sunny late-morning street green
    "birch_t": ("birch", (1.15, 1.25, 1.05), 1.1, (1.0, 1.0, 1.0)),
}
for _k, (_b, *_r) in TINTS.items():
    STYLES[_k] = STYLES[_b]
    SEEDS.setdefault(_k, SEEDS[_b])

def _grade(rgb, gain, sat):
    out = rgb * np.array(gain)
    g = out.mean(axis=2, keepdims=True)
    return np.clip(g + (out - g) * sat, 0, 1)
_IMG = {}; _MAT = {}

def _img(name, painter, noncolor=False, force=False):
    """paint + save the texture, or (maps) load it from roblox/textures when it already exists"""
    key = name
    if key in _IMG:
        return _IMG[key]
    path = os.path.join(TEX, name + ".png")
    if os.path.exists(path) and not force:
        img = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            img.colorspace_settings.name = "Non-Color"
    else:
        img = save_png(name, painter(), noncolor)
    _IMG[key] = img
    return img

def get_materials(style, force=False):
    """Trunk / Branches / Leaves materials for a texture style (cached per style)"""
    if style in _MAT:
        return _MAT[style]
    bk, lk, tk = STYLES[style]
    tint = TINTS.get(style); suf = "_" + style.split("_")[-1] if tint else ""
    cache = {}
    def paint(kind, k):
        if (kind, k) not in cache:
            rng = np.random.default_rng(SEEDS[k] + {"bark": 0, "leaves": 1, "twigs": 2}[kind])
            if kind == "bark":
                cache[kind, k] = {"birch": bark_birch, "fir": bark_fir}.get(k, bark_oak)(rng)
            elif kind == "leaves":
                cache[kind, k] = needle_atlas(k, rng) if k in NEEDLE_STYLE else leaf_atlas(k, rng)
            else:
                cache[kind, k] = twig_atlas(k, rng)
            if tint:
                c, n_ = cache[kind, k]
                gain, sat = (tint[3], 1.0) if kind != "leaves" else (tint[1], tint[2])
                rgb = _grade(c[..., :3], gain, sat)
                cache[kind, k] = (np.dstack([rgb, c[..., 3:]]) if c.shape[2] == 4 else rgb, n_)
        return cache[kind, k]
    I = {}
    for kind, k in (("bark", bk), ("leaves", lk), ("twigs", tk)):
        I[kind + "_c"] = _img(f"{k}{suf}_{kind}_color", lambda kind=kind, k=k: paint(kind, k)[0], False, force)
        I[kind + "_n"] = _img(f"{k}_{kind}_normal", lambda kind=kind, k=k: paint(kind, k)[1], True, force)
    _MAT[style] = dict(trunk=material(f"{style}_Bark", I["bark_c"], I["bark_n"], False, 0.92),
                       twig=material(f"{style}_Twigs", I["twigs_c"], I["twigs_n"], True, 0.85),
                       leaf=material(f"{style}_Leaves", I["leaves_c"], I["leaves_n"], True, 0.62))
    return _MAT[style]

def make_tree(name, coll, prefix="", force=False, tex=None):
    """build one species into coll: [<prefix><name>_Trunk, _Branches, _Leaves] (shared origin = trunk base),
    plus its triangle counts. Used by the map scripts (import gen_trees) and by main()."""
    P = TREES[name]
    M = get_materials((tex or {}).get(P["tex"], P["tex"]), force)       # tex: map override {"oak": "oak_v", ...}
    tree = Tree(P).build()
    cards = conifer_cards if P.get("kind") == "conifer" else card_quads
    nm = prefix + name
    objs = [make_object(f"{nm}_Trunk", tube_mesh(tree, P["bark_tile"]), M["trunk"], coll),
            make_object(f"{nm}_Branches", cards(tree, leaves=False), M["twig"], coll),
            make_object(f"{nm}_Leaves", cards(tree, leaves=True), M["leaf"], coll)]
    objs = [o for o in objs if len(o.data.polygons)]
    tris = {o.name: tri_count(o) for o in objs}
    tris["total"] = sum(tris.values())
    return objs, tris, tree

def main():
    sc, cam = setup_scene()
    rp = os.path.join(OUT, "report.json")
    report = json.load(open(rp)) if (ONLY and os.path.exists(rp)) else {}
    names = ONLY.split(",") if ONLY else list(TREES)
    for name in names:
        coll = bpy.data.collections.new(name); sc.collection.children.link(coll)
        objs, tris, tree = make_tree(name, coll, force=True)
        dims = [max(v.co[i] for o in objs for v in o.data.vertices) - min(v.co[i] for o in objs for v in o.data.vertices)
                for i in range(3)]
        report[name] = dict(tris=tris, size_studs=[round(dims[0], 1), round(dims[1], 1), round(dims[2], 1)],
                            branches=len(tree.branches))
        print("TREE", name, json.dumps(report[name]))
        for o in bpy.data.objects:      # only this tree visible for its renders
            if o.users_collection and o.users_collection[0].name in TREES:
                o.hide_render = o.users_collection[0] is not coll
        if "--noexport" not in ARGS:
            for o in objs:
                export_glb([o], os.path.join(ROBLOX, f"{o.name}.glb"))
            export_glb(objs, os.path.join(ROBLOX, f"{name}.glb"))
        if "--norender" not in ARGS:
            report[name]["sheet"] = os.path.relpath(contact_sheet(name, render_turntable(sc, cam, name, objs)), OUT).replace(os.sep, "/")
    with open(rp, "w") as f:
        json.dump(report, f, indent=1)

if __name__ == "__main__":
    main()
