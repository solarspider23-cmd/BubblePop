# Maple Junction painted atlas: ONE 1024 px texture for every solid mesh, two kinds of 256 px block:
#   TILE blocks (brick, stucco, siding, slate, asphalt, paving): a true 2D tile (bricks, slabs, boards) painted twice,
#     dark band (rows 0-127) and light band (rows 128-255). Faces are projected on their dominant plane (walls: along
#     the wall x horizontal / world y vertical; floors: x / z), CLIPPED at the tile period so every piece maps into one
#     period: brick courses, slab joints and clapboards stay the same size on every wall and never stretch.
#   PAINT blocks (glass, metal, leaf, grass, wood, accents): valleylake's scheme, row = continuous shade, x = planar
#     projection with brush strokes (paint.py).
# Contract kept from pro_lib: faces carry (u = palette column, v = shade); remap() turns that into atlas UVs at mesh time.
import os, sys, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'valleylake'))
import paint as VP

N = 256; ATLAS = 1024; PAD = 3
WP, HP = N - 2 * PAD, N // 2 - 2 * PAD                    # tile period in px (250 x 122) = (P, P/2) studs
TILE = {'brick': 16.0, 'cream': 16.0, 'sage': 16.0, 'slate': 16.0, 'asph': 32.0, 'pave': 16.0}
VP.PERIOD.update({'glass': 9.0, 'metal': 7.0, 'red': 6.0, 'yellow': 6.0, 'teal': 8.0, 'blue': 6.0, 'wood': 6.0})
BAND_SHADE = (.36, .66)
STATS = {'clipped': 0}

def _hex(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])

def pnoise(rng, h, w, f, aniso=1.0):
    """periodic FFT noise h x w in [-1, 1], feature frequency ~f per period"""
    W = rng.standard_normal((h, w)) + 1j * rng.standard_normal((h, w))
    ky = np.fft.fftfreq(h)[:, None] * h; kx = np.fft.fftfreq(w)[None, :] * w
    k = np.sqrt((kx * aniso) ** 2 + ky ** 2) + 1e-6
    band = np.exp(-((np.log(k) - np.log(f)) ** 2) / (2 * .55 ** 2))
    o = np.real(np.fft.ifft2(W * band)); o -= o.mean(); return o / (np.abs(o).max() + 1e-9)

def edge(d, w):
    """1 inside a joint of half-width w (d = distance to the joint line in px), soft edge"""
    return np.clip(1 - (d - w) / 1.2, 0, 1)

def ramp(rmp, s):
    d, m, l = (_hex(c) for c in rmp); s = np.clip(s, 0, 1)[..., None]
    return np.where(s < .5, d + (m - d) * (s / .5), m + (l - m) * ((s - .5) / .5))

def hash2(a, b, seed):
    return ((np.sin(a * 12.9898 + b * 78.233 + seed * 3.17) * 43758.5453) % 1.0)

def tile(name, rmp, s0, seed):
    """one periodic WP x HP tile at base shade s0 -> rgb"""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:HP, 0:WP].astype(np.float64)
    off = np.zeros((HP, WP)); joint = np.zeros((HP, WP)); jcol = None
    if name == 'brick':                                       # 8 courses x 6 bricks per period, running bond
        rows, cols = 16, 12; rh, bw = HP / rows, WP / cols
        r = np.floor(yy / rh); xo = (xx + (r % 2) * bw / 2) % WP; c = np.floor(xo / bw)
        lx = xo - c * bw; ly = yy - r * rh
        joint = np.maximum(edge(np.minimum(lx, bw - lx), .45), edge(np.minimum(ly, rh - ly), .45))
        off += (hash2(r, c % cols, seed) - .5) * .2 + .04 * pnoise(rng, HP, WP, 30) + .05 * pnoise(rng, HP, WP, 4)
        off -= .07 * np.clip((ly / rh - .75) / .25, 0, 1)      # each brick a touch darker at its lower edge
        jcol = np.array([.86, .8, .7])
    elif name == 'cream':                                     # stucco with faint ashlar joints (2 x 4 blocks)
        rows, cols = 2, 4; rh, bw = HP / rows, WP / cols
        r = np.floor(yy / rh); xo = (xx + (r % 2) * bw / 2) % WP; c = np.floor(xo / bw)
        lx = xo - c * bw; ly = yy - r * rh
        joint = .55 * np.maximum(edge(np.minimum(lx, bw - lx), .5), edge(np.minimum(ly, rh - ly), .5))
        off += (hash2(r, c, seed) - .5) * .05 + .05 * pnoise(rng, HP, WP, 40) + .04 * pnoise(rng, HP, WP, 5)
        jcol = None
    elif name == 'sage':                                      # clapboard siding: 6 boards, shadow line under each
        rows = 12; rh = HP / rows; ly = yy % rh
        off += .12 * (ly / rh - .5) - .2 * np.clip(1 - ly / 1.3, 0, 1) + .04 * pnoise(rng, HP, WP, 20, 6) + .03 * pnoise(rng, HP, WP, 4)
    elif name == 'slate':                                     # shingles: 6 rows x 8, staggered, dark bottom edge
        rows, cols = 12, 16; rh, bw = HP / rows, WP / cols
        r = np.floor(yy / rh); xo = (xx + (r % 2) * bw / 2) % WP; c = np.floor(xo / bw)
        lx = xo - c * bw; ly = yy - r * rh
        joint = np.maximum(edge(np.minimum(lx, bw - lx), .6), edge(ly, .8) * 1.0)
        off += (hash2(r, c, seed) - .5) * .14 - .14 * (1 - ly / rh) + .03 * pnoise(rng, HP, WP, 25)
        jcol = 'dark'
    elif name == 'asph':                                      # asphalt: speckle, soft patches, hair cracks
        off += .05 * pnoise(rng, HP, WP, 3) + .06 * pnoise(rng, HP, WP, 40) + .09 * (rng.random((HP, WP)) > .975) - .07 * (rng.random((HP, WP)) > .985)
        cr = np.clip(1 - np.abs(pnoise(rng, HP, WP, 5)) / .02, 0, 1) * (pnoise(rng, HP, WP, 2) > .35)
        off -= .14 * cr
    elif name == 'pave':                                      # sidewalk slabs 4 x 2 per period (4 x 4 studs)
        rows, cols = 2, 4; rh, bw = HP / rows, WP / cols
        r = np.floor(yy / rh); c = np.floor(xx / bw); lx = xx - c * bw; ly = yy - r * rh
        joint = np.maximum(edge(np.minimum(lx, bw - lx), .8), edge(np.minimum(ly, rh - ly), .8))
        off += (hash2(r, c, seed) - .5) * .08 + .05 * pnoise(rng, HP, WP, 30) + .03 * pnoise(rng, HP, WP, 6)
        jcol = 'dark'
    col = ramp(rmp, s0 + off)
    if joint.any():
        if jcol is None: jc = ramp(rmp, np.full((HP, WP), s0 + .2))
        elif isinstance(jcol, str): jc = ramp(rmp, np.full((HP, WP), s0 - .22))
        else: jc = np.broadcast_to(jcol * (.75 + .35 * s0), (HP, WP, 3))
        col = col * (1 - joint[..., None]) + jc * joint[..., None]
    return np.clip(col, 0, 1)

def paint_glass(rmp, seed):
    rng = np.random.default_rng(seed)
    shade = np.linspace(0, 1, N)[:, None] * np.ones((1, N))
    yy, xx = np.mgrid[0:N, 0:N]
    streak = np.clip(np.sin((xx * 1.0 + yy * .6) / N * math.tau * 3) * 1.4 - .6, 0, 1)
    off = .14 * streak + .04 * VP.fnoise(rng, 6, 6, 1, 4)
    return np.clip(ramp(rmp, shade + off), 0, 1)

def block(name, rmp, seed):
    if name in TILE:
        out = np.zeros((N, N, 3))
        for b, s0 in enumerate(BAND_SHADE):
            t = tile(name, rmp, s0, seed + b * 7)
            t = np.pad(t, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='wrap')
            out[b * (N // 2):(b + 1) * (N // 2)] = t
        return out
    if name == 'glass': return paint_glass(rmp, seed)
    return VP.paint_block(name if name in ('leaf', 'grass', 'wood', 'rock', 'stone', 'water') else 'other', rmp, seed)

def atlas(pal, tag, out_png=None):
    import bpy
    px = np.zeros((ATLAS, ATLAS, 4), np.float32); px[..., 3] = 1
    for i, nm in enumerate(pal.names):
        bx, by = (i % 4) * N, (i // 4) * N
        px[by:by + N, bx:bx + N, :3] = block(nm, pal.ramps[nm], 1000 + i)
    img = bpy.data.images.new(tag + '_Pal', ATLAS, ATLAS, alpha=False)
    img.pixels.foreach_set(px.ravel())
    if out_png: img.filepath_raw = out_png; img.file_format = 'PNG'; img.save()
    img.pack(); return img

# ------------------------------------------------------------------ UV remap with period clipping
def axes_of(n):
    ax = max(range(3), key=lambda k: abs(n[k]))
    if ax == 1: return 0, 2          # floor / roof: x, z
    if ax == 0: return 2, 1          # wall facing x: along z, world y
    return 0, 1                      # wall facing z: along x, world y

def clip(poly, f, lo, hi):
    """polygon (list of Vector) clipped to lo <= f(p) <= hi"""
    for side in (1, -1):
        lim = lo if side == 1 else hi
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            da, db = (f(a) - lim) * side, (f(b) - lim) * side
            if da >= 0: out.append(a)
            if (da < 0) != (db < 0) and da != db: out.append(a.lerp(b, da / (da - db)))
        poly = out
        if len(poly) < 3: return []
    return poly

def area(poly):
    s = Vector()
    for i in range(1, len(poly) - 1): s += (poly[i] - poly[0]).cross(poly[i + 1] - poly[0])
    return s.length / 2

def remap(mb, pal):
    names = pal.names; NC = 16
    V2, F2, UV2, SM2 = list(mb.V), [], [], []
    for fi, face in enumerate(mb.F):
        uvs = mb.UV[fi]
        ci = min(len(names) - 1, int(uvs[0][0] * NC)); nm = names[ci]
        bx, by = (ci % 4) * N, (ci // 4) * N
        pts = [Vector(mb.V[i]) for i in face]
        n = (pts[1] - pts[0]).cross(pts[-1] - pts[0])
        if len(pts) > 3:
            n = Vector()
            for i in range(len(pts)): n += pts[i].cross(pts[(i + 1) % len(pts)])
        if nm not in TILE:
            P = VP.PERIOD.get(nm, 10.0)
            ax = max(range(3), key=lambda k: abs(n[k])) if n.length > 1e-9 else 1
            a2, b2 = [k for k in range(3) if k != ax]
            if ax == 1: a2, b2 = 0, 2
            A = [p[a2] / P for p in pts]; Bv = [p[b2] / P for p in pts]
            o = math.floor(min(A)); span = max(A) - o; k = 1.0 if span <= 1 else 1 / span
            new = []
            for j, (uu, vv) in enumerate(uvs):
                x = (A[j] - o) * k; v = min(.98, max(.02, vv + .045 * VP.tri(Bv[j])))
                new.append(((bx + PAD + x * (N - 2 * PAD)) / ATLAS, (by + PAD + v * (N - 2 * PAD)) / ATLAS))
            F2.append(face); UV2.append(new); SM2.append(mb.SM[fi]); continue
        PA = TILE[nm]; PB = PA / 2
        band = 1 if sum(v for _, v in uvs) / len(uvs) >= .5 else 0
        a2, b2 = axes_of(n)
        fa = lambda p: p[a2] / PA; fb = lambda p: p[b2] / PB
        pieces = [pts]
        A = [fa(p) for p in pts]; B = [fb(p) for p in pts]
        if max(A) - math.floor(min(A) + 1e-4) > 1 + 1e-4 or max(B) - math.floor(min(B) + 1e-4) > 1 + 1e-4:
            pieces = []
            for ka in range(math.floor(min(A) + 1e-4), math.ceil(max(A) - 1e-4)):
                pa = clip(pts, fa, ka, ka + 1)
                if not pa: continue
                Bs = [fb(p) for p in pa]
                for kb in range(math.floor(min(Bs) + 1e-4), math.ceil(max(Bs) - 1e-4)):
                    pb = clip(pa, fb, kb, kb + 1)
                    if pb and area(pb) > 1e-5: pieces.append(pb)
            STATS['clipped'] += 1
        for pc in pieces:
            A = [fa(p) for p in pc]; B = [fb(p) for p in pc]
            oa = math.floor(min(A) + 1e-4); ob = math.floor(min(B) + 1e-4)
            idx = []; new = []
            for p, a, b in zip(pc, A, B):
                idx.append(len(V2)); V2.append(tuple(p))
                x = min(1, max(0, a - oa)); y = min(1, max(0, b - ob))
                new.append(((bx + PAD + x * WP) / ATLAS, (by + band * (N // 2) + PAD + y * HP) / ATLAS))
            F2.append(tuple(idx)); UV2.append(new); SM2.append(False)
    mb.V, mb.F, mb.UV, mb.SM = V2, F2, UV2, SM2

def install(G, pal, tag='MapleJunction'):
    orig = G.mesh_from
    def mesh_from(name, mb, mat):
        if '_Glow_' not in name: remap(mb, pal)
        return orig(name, mb, mat)
    G.mesh_from = mesh_from
    cache = {}
    def material(t):
        import bpy
        try: cache['img'].name
        except Exception: cache.pop('img', None)
        if 'img' not in cache: cache['img'] = atlas(pal, tag, os.path.join(HERE, 'previews', tag + '_Atlas.png'))
        m = bpy.data.materials.new(t + '_Mat'); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = cache['img']; tex.interpolation = 'Linear'; tex.extension = 'EXTEND'
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .9
        b.inputs['Specular IOR Level'].default_value = .12
        return m
    pal.material = material
