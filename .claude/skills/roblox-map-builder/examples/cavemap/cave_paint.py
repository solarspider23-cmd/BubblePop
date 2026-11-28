# Glowroot Caverns painted atlas: reuses valleylake/paint.py (FFT strokes, stamps, cracks, UV remap, install) and swaps
# in cave blocks. Contract unchanged: palette column -> 256 block, shade -> block row, planar projection -> block x.
import os, sys
import numpy as np
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'examples', 'valleylake')
sys.path.insert(0, SK)
import paint as P
from paint import fnoise, stamps, cracks, N

P.PERIOD = {'rock': 16.0, 'moss': 8.0, 'floor': 12.0, 'sand': 14.0, 'water': 24.0, 'wood': 6.0, 'wooddk': 7.0,
            'iron': 5.0, 'canvas': 5.0, 'shroom': 5.0, 'stem': 5.0, 'crysA': 5.0, 'crysC': 5.0, 'crysV': 5.0,
            'red': 5.0, 'white': 10.0}

def block(name, ramp, seed):
    rng = np.random.default_rng(seed)
    d, m, l = (P._hex(c) for c in ramp)
    shade = np.linspace(0, 1, N)[:, None] * np.ones((1, N))
    off = np.zeros((N, N)); tint = np.zeros((N, N, 3))
    if name == 'white': return np.ones((N, N, 3))
    if name == 'rock':                                    # cave limestone: long strata streaks, cracks, mineral glints
        off += .08 * fnoise(rng, 8, 8, 1, 6.0) + .06 * fnoise(rng, 3, 3, 1, 2.0) + .04 * fnoise(rng, 28, 28, 1, 4)
        c = cracks(rng, 5, .022) * (fnoise(rng, 3, 3) > .25); off -= .28 * c
        chips = cracks(rng, 11, .03) * (fnoise(rng, 6, 6) > .5); off += .1 * chips
        wet = np.clip(fnoise(rng, 5, 5, 1, 1.5), 0, 1); off -= .08 * wet
        glint = (rng.random((N, N)) > .9975).astype(float); off += .45 * glint
        tint[..., 1] += .05 * glint; tint[..., 2] += .07 * glint
        tint[..., 2] += .05 * c; tint[..., 0] -= .03 * c                   # crevices go cold
    elif name == 'moss':                                  # cave moss: dense teal dabs with lit rims
        v, rim = stamps(rng, 340, 3, 6, 1.6); off += .14 * v + .22 * rim * np.clip((shade - .3) / .4, 0, 1)
        off += .05 * fnoise(rng, 5, 5)
    elif name == 'floor':                                 # packed cave earth: pebbles with rims, grit, faint cracks
        off += .06 * fnoise(rng, 5, 5, 1, 1.4) + .05 * fnoise(rng, 36, 36)
        v, rim = stamps(rng, 160, 3, 7, 1.3); off += .1 * v + .14 * rim
        off -= .14 * cracks(rng, 7, .025) * (fnoise(rng, 3, 3) > .2)
        off += .05 * (rng.random((N, N)) > .985)
    elif name == 'sand':
        off += .05 * fnoise(rng, 6, 6, 1, 3) + .04 * fnoise(rng, 40, 40) + .06 * (rng.random((N, N)) > .985)
    elif name == 'water':
        off += .08 * fnoise(rng, 6, 6, 1, 5) + .08 * np.clip(fnoise(rng, 16, 16, 1, 3), 0, 1)
    elif name in ('wood', 'wooddk'):                      # timber: grain, plank seams, nail dots
        off += .08 * fnoise(rng, 16, 16, 1, 10.0) + .04 * fnoise(rng, 3, 3, 1, 4)
        off -= .14 * cracks(rng, 18, .018) * (fnoise(rng, 4, 4) > .35)
        x = np.arange(N)[None, :] * np.ones((N, 1)); off -= .22 * ((x % 64) < 3)
        off -= .2 * ((rng.random((N, N)) > .9985))
    elif name == 'iron':                                  # dark iron: brushed, rivets, rust blooms
        off += .05 * fnoise(rng, 22, 22, 1, 8) + .05 * fnoise(rng, 4, 4)
        rust = np.clip(fnoise(rng, 6, 6, 1, 1.2), 0, 1) ** 2; tint[..., 0] += .12 * rust; tint[..., 1] += .04 * rust; tint[..., 2] -= .03 * rust
        x = np.arange(N)[None, :] * np.ones((N, 1)); y = np.arange(N)[:, None] * np.ones((1, N))
        riv = (((x % 32) - 16) ** 2 + ((y % 32) - 16) ** 2) < 7; off += .22 * riv
    elif name == 'canvas':                                # woven canvas / rope
        x = np.arange(N)[None, :] * np.ones((N, 1)); y = np.arange(N)[:, None] * np.ones((1, N))
        off += .05 * np.sin(x * .9) * np.sin(y * .9) + .06 * fnoise(rng, 6, 6, 1, 2) + .03 * fnoise(rng, 40, 40)
        off -= .1 * np.clip(fnoise(rng, 4, 4), 0, 1) ** 2
    elif name == 'shroom':                                # mushroom cap: soft spots and freckles
        v, rim = stamps(rng, 70, 5, 11, 1.1); off += .2 * np.clip(v, 0, 1) + .08 * rim
        off += .05 * fnoise(rng, 6, 6) + .08 * (rng.random((N, N)) > .99)
    elif name == 'stem':
        off += .1 * fnoise(rng, 20, 20, 1, 7) + .04 * fnoise(rng, 3, 3)
    elif name in ('crysA', 'crysC', 'crysV'):             # crystal: facet bands, bright inner streaks, frosty chips
        off += .12 * fnoise(rng, 6, 6, 1, 7.0) + .22 * np.clip(fnoise(rng, 18, 18, 1, 9.0), 0, 1) ** 2
        off -= .1 * cracks(rng, 5, .02); off += .2 * (rng.random((N, N)) > .996)
    elif name == 'red':                                   # painted iron: chips show dark metal
        off += .05 * fnoise(rng, 8, 8, 1, 3)
        off -= .35 * (fnoise(rng, 14, 14) > .62)
    else:
        off += .06 * fnoise(rng, 8, 8, 1, 3)
    s = np.clip(shade + off, 0, 1)[..., None]
    col = np.where(s < .5, d + (m - d) * (s / .5), m + (l - m) * ((s - .5) / .5))
    return np.clip(col + tint, 0, 1)

P.paint_block = block
install = P.install
