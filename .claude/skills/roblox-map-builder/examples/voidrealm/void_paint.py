# Shattered Void painted atlas: reuses valleylake/paint.py (FFT strokes, stamps, cracks, UV remap, install) and swaps
# in void-specific painted blocks. Same contract: column -> 256 block, shade -> block row, planar projection -> block x.
import os, sys, math
import numpy as np
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'examples', 'valleylake')
sys.path.insert(0, SK)
import paint as P
from paint import fnoise, stamps, cracks, N

P.PERIOD = {'obsid': 14.0, 'crust': 16.0, 'turf': 9.0, 'pave': 8.0, 'stone': 7.0, 'trim': 6.0, 'crystal': 5.0,
            'cyanc': 5.0, 'flora': 4.0, 'stem': 5.0, 'metal': 6.0, 'far': 40.0, 'dark': 20.0, 'white': 10.0}

def block(name, ramp, seed):
    rng = np.random.default_rng(seed)
    d, m, l = (P._hex(c) for c in ramp)
    shade = np.linspace(0, 1, N)[:, None] * np.ones((1, N))
    off = np.zeros((N, N)); tint = np.zeros((N, N, 3))
    if name == 'white': return np.ones((N, N, 3))
    if name == 'obsid':                                   # glassy black rock: long violet sheen strokes, sharp chips, cyan glints
        off += .10 * fnoise(rng, 9, 9, 1, 5.0) + .05 * fnoise(rng, 3, 3, 1, 2)
        c = cracks(rng, 5, .02) * (fnoise(rng, 3, 3) > .2); off -= .28 * c
        sheen = np.clip(fnoise(rng, 14, 14, 1, 8.0), 0, 1) ** 2 * np.clip((shade - .45) / .4, 0, 1); off += .34 * sheen
        glint = (rng.random((N, N)) > .996).astype(float); off += .5 * glint
        tint[..., 2] += .06 * sheen; tint[..., 0] += .03 * sheen
    elif name == 'crust':                                 # island ground: grainy dusk soil, fine crack web, pale dabs
        off += .07 * fnoise(rng, 5, 5, 1, 1.4) + .05 * fnoise(rng, 40, 40)
        off -= .18 * cracks(rng, 9, .025) * (fnoise(rng, 4, 4) > 0)
        v, rim = stamps(rng, 200, 2, 5, 1.6); off += .07 * v + .12 * rim
    elif name == 'turf':                                  # void moss: dense dabs with lit rims
        v, rim = stamps(rng, 360, 3, 6, 2.2, rot=-.4); off += .15 * v + .25 * rim * np.clip((shade - .3) / .4, 0, 1)
        off += .05 * fnoise(rng, 5, 5)
    elif name == 'pave':                                  # rune paving: slab grid with chipped edges
        y, x = np.mgrid[0:N, 0:N]
        gx = (x % 64) / 64; gy = ((y + (x // 64 % 2) * 21) % 42) / 42
        seam = (gx < .05) | (gy < .07)
        off += .06 * fnoise(rng, 10, 10, 1, 2) - .3 * seam + .04 * fnoise(rng, 30, 30)
        off -= .14 * cracks(rng, 6, .03) * (fnoise(rng, 3, 3) > .4)
    elif name == 'stone':                                 # ancient lilac stone: soft blocks, weathering, chips
        off += .07 * fnoise(rng, 6, 6, 1, 1.2) + .05 * fnoise(rng, 2, 2, 1, 1) - .22 * cracks(rng, 6, .04) + .05 * fnoise(rng, 26, 26, 1, 1.3)
        off += .1 * cracks(rng, 12, .03) * (fnoise(rng, 5, 5) > .5)
    elif name == 'trim':
        off += .05 * fnoise(rng, 12, 12, 1, 6) + .04 * fnoise(rng, 3, 3)
    elif name in ('crystal', 'cyanc'):                    # faceted bands + bright internal streaks
        off += .12 * fnoise(rng, 6, 6, 1, 7.0) + .2 * np.clip(fnoise(rng, 18, 18, 1, 9.0), 0, 1) ** 2
        off -= .12 * cracks(rng, 5, .02)
    elif name == 'flora':
        v, rim = stamps(rng, 300, 3, 7, 3.0, rot=1.3); off += .14 * v + .22 * rim
    elif name == 'stem':
        off += .14 * fnoise(rng, 12, 12, 1, 9.0) + .05 * fnoise(rng, 3, 3)
    elif name == 'metal':
        off += .05 * fnoise(rng, 20, 20, 1, 6) + .08 * np.clip(fnoise(rng, 8, 8, 1, 4), 0, 1)
    elif name == 'far':
        off += .06 * fnoise(rng, 4, 4, 1, 3)
    elif name == 'dark':
        off += .02 * fnoise(rng, 6, 6)
    else:
        off += .06 * fnoise(rng, 8, 8, 1, 3)
    s = np.clip(shade + off, 0, 1)[..., None]
    col = np.where(s < .5, d + (m - d) * (s / .5), m + (l - m) * ((s - .5) / .5))
    return np.clip(col + tint, 0, 1)

P.paint_block = block
install = P.install
