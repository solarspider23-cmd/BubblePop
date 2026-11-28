# Gilded Dunes painted atlas: re-skins the valleylake painted-atlas machinery (paint.py: 1024 px, 4 x 4 blocks of 256,
# column -> block, shade -> block row, planar projection -> block x) with desert blocks:
#   sand  = wind ripples (asymmetric sine crests, phase warped by periodic noise, amplitude patches) + grain speckle
#   stone / stone2 = sand-worn sandstone: chisel grain, pits, hairline cracks, pale wind-scoured streaks
#   cloth / indigo / red / saffron = woven canvas (fine warp + weft) with soft fold shading
#   gold  = burnished metal streaks, palm = long leaflet strokes, bone = porous, camel = fur strokes, rock = mesa strata
# remap() is replaced: the block-x axis is world X on +-Y and +-Z faces and world Z on +-X faces (paint.py used Y for
# X-facing faces, which turned patterns 90 deg between neighbouring walls); the ping-pong v offset is a bit wider.
import math, os, sys
import numpy as np
from mathutils import Vector
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'examples', 'valleylake')
sys.path.insert(0, SK)
import paint as P
N, ATLAS, PAD = P.N, P.ATLAS, P.PAD
fnoise, stamps, cracks = P.fnoise, P.stamps, P.cracks

P.PERIOD = {'sand': 24.0, 'stone': 10.0, 'stone2': 9.0, 'gold': 5.0, 'wood': 6.0, 'cloth': 5.0, 'indigo': 5.0, 'red': 5.0,
            'saffron': 5.0, 'water': 20.0, 'palm': 5.0, 'bone': 6.0, 'camel': 4.0, 'rock': 30.0, 'scrub': 4.0, 'white': 10.0}

def _hex(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
XX = np.arange(N)[None, :] * np.ones((N, 1)); YY = np.arange(N)[:, None] * np.ones((1, N))

def paint_block(name, ramp, seed):
    rng = np.random.default_rng(seed)
    d, m, l = (_hex(c) for c in ramp)
    shade = YY / (N - 1)
    off = np.zeros((N, N))
    if name == 'white': return np.ones((N, N, 3))
    if name == 'sand':
        ph = XX / N * 9 + .6 * fnoise(rng, 2, 2, 1, 1.0) + .2 * fnoise(rng, 5, 5, 1, 2.0)
        fr = ph % 1.0; rip = np.where(fr < .78, fr / .78, (1 - fr) / .22) * 2 - 1                    # sawtooth: long lit side, short lee
        amp = .03 + .02 * fnoise(rng, 2, 2, 1, 1)
        off += amp * rip + .02 * fnoise(rng, 5, 5, 1, 1.5) + .015 * fnoise(rng, 60, 60)
        off += .05 * (rng.random((N, N)) > .992) - .04 * (rng.random((N, N)) > .994)               # glints + dark grains
    elif name in ('stone', 'stone2'):
        off += .06 * fnoise(rng, 7, 7, 1, 1.6) + .05 * fnoise(rng, 24, 24, 1, 1.2) + .03 * fnoise(rng, 70, 70)
        off -= (.22 if name == 'stone' else .3) * cracks(rng, 5, .018) * (fnoise(rng, 3, 3) > .15)
        pits = (fnoise(rng, 40, 40) > .62); off -= .08 * pits
        off += .07 * np.clip(fnoise(rng, 10, 10, 1, 6.0), 0, 1) * np.clip((shade - .45) / .4, 0, 1)   # wind-scoured streaks
    elif name in ('cloth', 'indigo', 'red', 'saffron'):
        off += .035 * np.sin(XX * math.tau / 4) + .035 * np.sin(YY * math.tau / 4) + .05 * fnoise(rng, 3, 3, 1, 3.0)
        off += .03 * fnoise(rng, 30, 30, 1, 8.0)
        if name in ('indigo', 'red'):                                       # woven stripe bands across the cloth
            ph = (XX % 64) / 64; off += .12 * ((ph > .78) & (ph < .86)) - .08 * ((ph > .9) & (ph < .95))
    elif name == 'gold':
        off += .1 * fnoise(rng, 8, 8, 1, 7.0) + .05 * fnoise(rng, 30, 30, 1, 3) + .1 * np.clip(fnoise(rng, 5, 5, 1, 4), .5, 1)
    elif name == 'wood':
        off += .08 * fnoise(rng, 16, 16, 1, 10.0) + .04 * fnoise(rng, 3, 3, 1, 4); off -= .12 * cracks(rng, 16, .02) * (fnoise(rng, 4, 4) > .4)
    elif name == 'water':
        off += .08 * fnoise(rng, 6, 6, 1, 5) + .07 * np.clip(fnoise(rng, 18, 18, 1, 3), 0, 1)
    elif name in ('palm', 'scrub'):
        v, rim = stamps(rng, 380, 3, 8, 4.0 if name == 'palm' else 2.0, rot=.2 if name == 'palm' else None)
        off += .14 * v + .2 * rim * np.clip((shade - .25) / .45, 0, 1) + .04 * fnoise(rng, 5, 5); off -= .06 * (v == 0)
    elif name == 'bone':
        off += .05 * fnoise(rng, 10, 10, 1, 3) - .1 * (fnoise(rng, 50, 50) > .6) - .14 * cracks(rng, 8, .015)
    elif name == 'camel':
        off += .09 * fnoise(rng, 26, 26, 1, 6.0) + .05 * fnoise(rng, 4, 4, 1, 2)
    elif name == 'rock':
        off += .08 * fnoise(rng, 6, 6, 1, 3) + .05 * fnoise(rng, 30, 30, 1, 2) - .2 * cracks(rng, 4, .02)
    else:
        off += .05 * fnoise(rng, 8, 8, 1, 3)
    s = np.clip(shade + off, 0, 1)[..., None]
    col = np.where(s < .5, d + (m - d) * (s / .5), m + (l - m) * ((s - .5) / .5))
    return np.clip(col, 0, 1)
P.paint_block = paint_block

def remap(mb, pal):
    names = pal.names; NC = 16
    for fi, face in enumerate(mb.F):
        uvs = mb.UV[fi]
        ci = min(len(names) - 1, int(uvs[0][0] * NC)); nm = names[ci]; Pd = P.PERIOD.get(nm, 10.0)
        a = Vector(mb.V[face[0]]); b = Vector(mb.V[face[1]]); c = Vector(mb.V[face[-1]])
        n = (b - a).cross(c - a); ax = max(range(3), key=lambda k: abs(n[k])) if n.length > 1e-9 else 1
        a2, b2 = {0: (2, 1), 1: (0, 2), 2: (0, 1)}[ax]
        A = [mb.V[i][a2] / Pd for i in face]; Bv = [mb.V[i][b2] / Pd for i in face]
        o = math.floor(min(A)); span = max(A) - o
        k = 1.0 if span <= 1 else 1 / span
        bx, by = (ci % 4) * N, (ci // 4) * N
        new = []
        for j, (uu, vv) in enumerate(uvs):
            x = (A[j] - o) * k; v = min(.98, max(.02, vv + (.012 if nm == 'sand' else .06) * P.tri(Bv[j])))
            new.append(((bx + PAD + x * (N - 2 * PAD)) / ATLAS, (by + PAD + v * (N - 2 * PAD)) / ATLAS))
        mb.UV[fi] = new
P.remap = remap
install = P.install
