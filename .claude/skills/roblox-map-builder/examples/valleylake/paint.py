# Mistvale Lake painted atlas: ONE 1024 px hand-painted-look texture shared by every solid mesh (rocks, foliage, timber,
# roofs, ground ...). It replaces the flat palette strip but keeps its contract:
#   every face loop still gets (u = palette column, v = shade 0..1) from the shading rules;
#   install() turns that into atlas UVs: column -> a 256 x 256 BLOCK (4 x 4 blocks), shade -> block row (dark at the
#   bottom, light at the top), and a planar (triplanar by face normal) projection of the vertex -> block x. Each block is
#   painted so it tiles in x, and every face is shifted by a whole period so its UVs stay inside one period: strokes run
#   continuously over the forms with no per-prop textures. A small ping-pong offset on v from the second projected axis
#   makes flat-shaded faces sample a 2D patch of strokes instead of one row.
# Painting = numpy: FFT-filtered noise (periodic, anisotropic = brush strokes), ridged cracks, leaf / dab stamps with
# highlight rims, timber grain, roof ribs, cobbles; colour = the ramp at (row shade + paint offset).
import math, random
import numpy as np
from mathutils import Vector

N = 256; ATLAS = 1024; PAD = 3
PERIOD = {'rock': 18.0, 'moss': 10.0, 'grass': 22.0, 'leaf': 5.0, 'pine': 5.0, 'blossom': 5.0, 'sand': 26.0, 'water': 30.0,
          'wood': 7.0, 'wooddk': 6.0, 'shoji': 6.0, 'roof': 9.0, 'stone': 9.0, 'flower': 4.0, 'red': 4.0, 'white': 10.0}

def _hex(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])

def fnoise(rng, fx, fy, power=1.0, aniso=1.0):
    """periodic FFT noise in [-1, 1]; aniso > 1 stretches features along x (brush strokes)"""
    w = rng.standard_normal((N, N)) + 1j * rng.standard_normal((N, N))
    ky = np.fft.fftfreq(N)[:, None] * N; kx = np.fft.fftfreq(N)[None, :] * N
    k = np.sqrt((kx * aniso) ** 2 + ky ** 2) + 1e-6
    band = np.exp(-((np.log(k) - np.log(fx)) ** 2) / (2 * .55 ** 2)) / k ** (power * .2)
    f = np.real(np.fft.ifft2(w * band))
    f -= f.mean(); return f / (np.abs(f).max() + 1e-9)

def stamps(rng, n, rmin, rmax, elong=2.0, rot=None):
    """leaf / dab stamps: (value field, rim-highlight field) both periodic, rotated pointed ellipses"""
    val = np.zeros((N, N)); rim = np.zeros((N, N))
    yy, xx = np.mgrid[0:N, 0:N]
    for _ in range(n):
        cx, cy = rng.uniform(0, N), rng.uniform(0, N); r = rng.uniform(rmin, rmax)
        a = rng.uniform(0, math.pi) if rot is None else rot + rng.uniform(-.5, .5)
        dx = (xx - cx + N / 2) % N - N / 2; dy = (yy - cy + N / 2) % N - N / 2
        u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
        d = np.sqrt((u / (r * elong)) ** 2 + (v / r) ** 2) + .35 * np.abs(u / (r * elong)) ** 2    # pointed tips
        m = d < 1
        s = rng.uniform(-1, 1)
        val[m] = s * (1 - d[m] * .4)
        rim[m] = np.clip(1 - np.abs(d[m] - .86) / .14, 0, 1) * (v[m] < 0) + rim[m] * 0       # lit top edge
    return val, rim

def cracks(rng, f=6, width=.04):
    n = fnoise(rng, f, f, 1.0, 1.0)
    return np.clip(1 - np.abs(n) / width, 0, 1)

def paint_block(name, ramp, seed):
    rng = np.random.default_rng(seed)
    d, m, l = (_hex(c) for c in ramp)
    shade = np.linspace(0, 1, N)[:, None] * np.ones((1, N))                  # row = shade (0 dark .. 1 light)
    off = np.zeros((N, N)); add = np.zeros((N, N, 3)); tint = np.zeros((N, N))
    if name == 'white':
        return np.ones((N, N, 3))
    if name == 'rock':
        off += .10 * fnoise(rng, 10, 10, 1, 4.0) + .06 * fnoise(rng, 3, 3, 1, 1.5) + .04 * fnoise(rng, 30, 30, 1, 3)
        c = cracks(rng, 4, .022) * (fnoise(rng, 3, 3) > .3)
        off -= .26 * c                                                       # dark painted cracks
        chips = cracks(rng, 10, .03) * (fnoise(rng, 6, 6) > .5); off += .12 * chips   # light chips
        streak = np.clip(fnoise(rng, 12, 12, 1, 6.0), 0, 1) * np.clip((shade - .55) / .3, 0, 1)
        off += .22 * streak                                                  # light streaks along the top edges
        tint = -.5 * c                                                       # crevices go bluer
    elif name in ('moss', 'grass'):
        off += .08 * fnoise(rng, 4, 4, 1, 1.2)
        v, rim = stamps(rng, 260 if name == 'moss' else 340, 3, 7, 1.8, rot=-.3)
        off += .12 * v + .2 * rim * np.clip((shade - .3) / .4, 0, 1)
    elif name in ('leaf', 'pine', 'blossom'):
        v, rim = stamps(rng, 420, 5, 11, 2.0 if name != 'pine' else 3.2, rot=None if name != 'pine' else 1.2)
        off += .16 * v + .26 * rim * np.clip((shade - .25) / .45, 0, 1) + .05 * fnoise(rng, 5, 5)
        off -= .08 * (v == 0)                                                # gaps between leaf shapes read darker
    elif name == 'sand':
        off += .05 * fnoise(rng, 6, 6, 1, 2.5) + .04 * fnoise(rng, 40, 40) + .05 * (rng.random((N, N)) > .985)
    elif name == 'water':
        off += .08 * fnoise(rng, 6, 6, 1, 5) + .06 * np.clip(fnoise(rng, 16, 16, 1, 3), 0, 1)
    elif name in ('wood', 'wooddk'):
        off += .07 * fnoise(rng, 14, 14, 1, 9.0) + .04 * fnoise(rng, 3, 3, 1, 4)
        off -= .12 * cracks(rng, 18, .02) * (fnoise(rng, 4, 4) > .4)
    elif name == 'roof':
        x = np.arange(N)[None, :] * np.ones((N, 1)); ph = (x % 32) / 32
        off += .14 * np.cos(ph * math.tau) - .18 * (ph > .92) + .05 * fnoise(rng, 8, 8, 1, 3)
    elif name == 'stone':
        off += .07 * fnoise(rng, 8, 8, 1, 2); off -= .28 * cracks(rng, 7, .06); off += .06 * fnoise(rng, 26, 26)
    elif name == 'shoji':
        off += .03 * fnoise(rng, 30, 30, 1, 6) + .03 * fnoise(rng, 4, 4)
    else:
        off += .06 * fnoise(rng, 8, 8, 1, 3)
    s = np.clip(shade + off, 0, 1)[..., None]
    col = np.where(s < .5, d + (m - d) * (s / .5), m + (l - m) * ((s - .5) / .5))
    if tint.any():                                                           # tint < 0: crevices lose red / green = bluer
        col = col * (1 + tint[..., None] * np.array([.45, .2, -.05]))
    return np.clip(col + add, 0, 1)

def atlas(pal, tag, out_png=None):
    """the 1024 px atlas image for a pro_lib Palette (column order = pal.names)"""
    import bpy
    px = np.zeros((ATLAS, ATLAS, 4), np.float32); px[..., 3] = 1
    for i, nm in enumerate(pal.names):
        bx, by = (i % 4) * N, (i // 4) * N
        px[by:by + N, bx:bx + N, :3] = paint_block(nm, pal.ramps[nm], 1000 + i)
    img = bpy.data.images.new(tag + '_Pal', ATLAS, ATLAS, alpha=False)
    img.pixels.foreach_set(px.ravel())
    if out_png:
        img.filepath_raw = out_png; img.file_format = 'PNG'; img.save()
    img.pack()
    return img

def tri(x): return abs((x / 2) % 1 * 2 - 1) * 2 - 1                         # ping-pong -1..1, continuous

def remap(mb, pal):
    """palette UVs (u column, v shade) -> atlas UVs, in place on an MB (Roblox-space verts)"""
    names = pal.names; NC = 16
    for fi, face in enumerate(mb.F):
        uvs = mb.UV[fi]
        ci = min(len(names) - 1, int(uvs[0][0] * NC)); nm = names[ci]; P = PERIOD.get(nm, 10.0)
        a = Vector(mb.V[face[0]]); b = Vector(mb.V[face[1]]); c = Vector(mb.V[face[-1]])
        n = (b - a).cross(c - a); ax = max(range(3), key=lambda k: abs(n[k])) if n.length > 1e-9 else 1
        a2, b2 = [k for k in range(3) if k != ax]
        if ax == 1: a2, b2 = 0, 2
        A = [mb.V[i][a2] / P for i in face]; Bv = [mb.V[i][b2] / P for i in face]
        o = math.floor(min(A)); span = max(A) - o
        k = 1.0 if span <= 1 else 1 / span
        bx, by = (ci % 4) * N, (ci // 4) * N
        new = []
        for j, (uu, vv) in enumerate(uvs):
            x = (A[j] - o) * k; v = min(.98, max(.02, vv + .045 * tri(Bv[j])))
            new.append(((bx + PAD + x * (N - 2 * PAD)) / ATLAS, (by + PAD + v * (N - 2 * PAD)) / ATLAS))
        mb.UV[fi] = new

def install(G, pal):
    """patch the grove machinery: atlas instead of the strip, UV remap in mesh_from"""
    orig = G.mesh_from
    def mesh_from(name, mb, mat):
        if '_Glow_' not in name: remap(mb, pal)
        return orig(name, mb, mat)
    G.mesh_from = mesh_from
    pal.image = lambda tag: atlas(pal, tag)
    def material(tag):
        import bpy
        img = atlas(pal, tag)
        m = bpy.data.materials.new(tag + '_Mat'); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'; tex.extension = 'EXTEND'
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .9
        return m
    pal.material = material
