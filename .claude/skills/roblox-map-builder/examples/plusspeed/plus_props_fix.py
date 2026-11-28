# v2 replacements for weak first-pass blocks (imported at the end of plus_props.py)
import math, random
from blocks import BlockProp
import plus_props as K

def pine(seed, h=16.0, snow=False):
    P = BlockProp('Pine')
    P.b((2.2, h * .32, 2.2), (0, h * .16 - .5, 0), 'wood', .4)
    for i in range(4):
        w = h * (.66 - i * .14); y = h * (.24 + i * .155)
        P.b((w, h * .2, w), (0, y, 0), 'leaf', .32 + i * .06, rot=(0, 45 * (i % 2), 0))
        if snow: P.b((w * .78, h * .06, w * .78), (0, y + h * .11, 0), 'snow', .92, rot=(0, 45 * (i % 2), 0))
    P.b((h * .14, h * .14, h * .14), (0, h * .86, 0), 'snow' if snow else 'leaf', .92 if snow else .55, rot=(0, 45, 0))
    return P

def palm(seed, h=18.0):
    rng = random.Random(seed); P = BlockProp('Palm')
    lean = rng.choice((-1, 1)) * rng.uniform(.4, 1.0); y = 0; x = 0
    for i in range(6):
        seg = h / 6; x += lean * i * .22
        P.b((2.4 - i * .12, seg + .3, 2.4 - i * .12), (x, y + seg / 2, 0), 'wood', .42 + (i % 2) * .12, rot=(0, 0, -lean * i * 2.4))
        y += seg
    top = (x, y, 0)
    P.b((3.0, 2.0, 3.0), (top[0], top[1], 0), 'leaf', .4)
    for k in range(8):
        a = k * 45 + rng.uniform(-8, 8)
        for j, (dist, dy, tilt, w) in enumerate(((3.0, .2, 12, 3.0), (6.6, -1.2, 32, 2.4))):         # two-segment drooping leaf
            P.b((w, .9, 4.4), (top[0] + math.sin(math.radians(a)) * dist, top[1] + dy, math.cos(math.radians(a)) * dist), 'leaf', .48 + (k % 2) * .08 - j * .05, rot=(tilt, a, 0))
    for k in range(3):
        a = k * 120 + 30; P.b((1.5, 1.5, 1.5), (top[0] + math.sin(math.radians(a)) * 1.5, top[1] - 1.4, math.cos(math.radians(a)) * 1.5), 'dirt', .35, shape='ball')
    return P

def lava_rock(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('LavaRock'); tops = []
    for k in range(5):
        c = rng.uniform(2.4, 5.2) * s; a = k * math.tau / 5 + rng.uniform(-.4, .4); d = (0 if k == 0 else rng.uniform(2.8, 4.6)) * s
        hh = (c * 1.6 if k == 0 else c * rng.uniform(.5, 1.0))
        P.b((c, hh, c), (math.cos(a) * d, hh / 2 - .3, math.sin(a) * d), 'basalt', rng.uniform(.3, .5), rot=(0, rng.uniform(0, 45), 0))
        tops.append((math.cos(a) * d, hh - .3, math.sin(a) * d, c))
    for x, y, z, c in tops[:3]:                                               # glowing seams on the tops + down one side
        P.b((c * .7, .3, .6), (x, y + .1, z), 'fire', .62, mat='neon', rot=(0, rng.uniform(0, 90), 0))
        P.b((.6, y * .8, .4), (x + c / 2 + .05, y * .45, z), 'fire', .62, mat='neon')
    return P

def planet(seed, r=10.0):
    P = BlockProp('Planet'); col = ['pink', 'mint', 'fire', 'gold'][seed % 4]
    P.b((r, r, r), (0, 0, 0), col, .55, shape='ball')
    P.b((r * .45, r * .45, r * .45), (r * .2, r * .25, -r * .22), col, .7, shape='ball')          # a bulge / spot
    P.b((.5, r * 1.75, r * 1.75), (0, 0, 0), 'snow', .82, shape='cyl', rot=(0, 0, 72))
    P.b((.6, r * 1.35, r * 1.35), (0, 0, 0), col, .4, shape='cyl', rot=(0, 0, 72))
    return P

def candy_cane(seed, h=12.0):
    P = BlockProp('CandyCane'); y = 0; n = int(h / 1.5)
    for k in range(n): P.b((1.6, 1.6, 1.6), (0, y + .8, 0), 'red' if k % 2 else 'snow', .6 if k % 2 else .9); y += 1.5
    R = 2.4; cx = R
    for k in range(7):                                                         # hook: blocks along a half circle
        a = math.radians(180 - k * 30); px, py = cx + math.cos(a) * R, y + math.sin(a) * R
        P.b((1.6, 1.7, 1.6), (px, py, 0), 'red' if k % 2 == 0 else 'snow', .6 if k % 2 == 0 else .9, rot=(0, 0, -(90 - math.degrees(a))))
    return P

def zone_gate(base_col, pillar_col, lantern, w=156.0):
    P = BlockProp('ZoneGate')
    for sx in (-1, 1):
        P.put(K.lamp_pillar(base_col, pillar_col, lantern), (sx * w / 2, 0, 0))
        P.b((12, 6, 10), (sx * (w / 2 - 6), 36, 0), base_col, .4)                  # chunky beam ends
        P.b((6, 6, 6), (sx * (w / 2 - 6), 41, 0), lantern, .7, mat='neon', rot=(0, 45, 0))
    P.b((w - 10, 5, 6), (0, 36, 0), base_col, .48)
    P.b((w - 6, 1.4, 7), (0, 39.2, 0), lantern, .6); P.b((w - 6, 1.4, 7), (0, 33.2, 0), lantern, .55)
    for k in range(9):                                                         # truss blocks under the beam
        x = -w / 2 + 14 + k * (w - 28) / 8; P.b((2, 2, 4), (x, 31.6, 0), base_col, .36)
    P.b((46, 14, 2.4), (0, 46, -1), 'basalt', .28)
    for (sw, sh, x, y) in ((48, 1.4, 0, 53.4), (48, 1.4, 0, 38.6), (1.4, 14, 23.6, 46), (1.4, 14, -23.6, 46)): P.b((sw, sh, 2.8), (x, y, -1), lantern, .6)
    P.b((40, 2.8, .4), (0, 48.2, -2.4), 'snow', .95, mat='neon'); P.b((26, 1.8, .4), (0, 43.6, -2.4), lantern, .7, mat='neon')
    P.b((w - 10, 30, .3), (0, 15.5, 0), lantern, .8, tr=.82, name='Veil')
    return P

def big_arch(text_col='gold', w=176.0, checker=True):
    P = BlockProp('Arch'); tw = 20
    for sx in (-1, 1):
        x = sx * (w / 2 + tw / 2)
        P.b((tw + 4, 4, tw + 4), (x, 1.5, 0), 'stone', .48)
        for k in range(6): P.b((tw - (k % 2) * 1.5, 8, tw - (k % 2) * 1.5), (x, 7.5 + k * 8, 0), 'stone' if k % 2 else text_col, .62 if k % 2 else .55)
        P.b((tw + 4, 3, tw + 4), (x, 56, 0), 'stone', .5)
        for dx in (-1, 1):
            for dz in (-1, 1): P.b((4, 4, 4), (x + dx * (tw / 2), 59.5, dz * (tw / 2)), 'stone', .58)   # battlements
        P.b((7, 7, 7), (x, 62, 0), text_col, .75, mat='neon', rot=(0, 45, 0))
    P.b((w + 4, 12, 10), (0, 49, 0), 'stone', .55)
    if checker:
        n = int((w + 4) / 4)
        for k in range(n):
            for row in range(3): P.b((4, 3, .6), (-(w + 4) / 2 + 2 + k * 4, 45.5 + row * 3, -5.2), 'basalt' if (k + row) % 2 else 'snow', .12 if (k + row) % 2 else .95)
    P.b((70, 16, 3), (0, 64, -1), 'basalt', .28); P.b((64, 3.4, .4), (0, 66.6, -2.8), 'snow', .95, mat='neon'); P.b((44, 2.2, .4), (0, 61.4, -2.8), text_col, .7, mat='neon')
    for y in (55.6, 72.4): P.b((72, 1.6, 3.6), (0, y, -1), text_col, .6)
    return P

def trophy():
    """finish hero: 1-2-3 podium + a giant cylinder-built trophy (base, stem, flared cup, handles, star)"""
    P = BlockProp('Trophy')
    for x, h, c in ((0, 10, 'gold'), (-20, 7, 'stone'), (20, 5, 'dirt')):
        P.b((18, h, 16), (x, h / 2 - .5, 0), 'stone', .62); P.b((18.6, 1, 16.6), (x, h, 0), c, .65)
        P.b((6, 5, .4), (x, h / 2, -8.3), c, .7, mat='neon')
    y = 10.5
    def disc(d, hh, yy, col='gold', v=.6): P.b((hh, d, d), (0, yy, 0), col, v, shape='cyl', rot=(0, 0, 90))
    disc(15, 2.4, y + 1.2, 'basalt', .3); disc(12, 2.0, y + 3.4, 'gold', .5); disc(9, 1.6, y + 5.2, 'gold', .62)
    disc(3.6, 7, y + 9.5, 'gold', .58); disc(7, 1.4, y + 13.4, 'gold', .7)
    for k, d in enumerate((8, 11, 14, 16, 17, 17.6)): disc(d, 2.4, y + 15.4 + k * 2.3, 'gold', .6 + k * .04)
    disc(19, 1.2, y + 29.6, 'gold', .85)
    for sx in (-1, 1):                                                         # C-shaped handles from blocks
        for k in range(6):
            a = math.radians(90 - k * 36); px, py = sx * (9.0 + math.cos(a) * 4.4), y + 22.0 + math.sin(a) * 4.8
            P.b((2.6, 2.6, 2.6), (px, py, 0), 'gold', .68, rot=(0, 0, sx * (90 - math.degrees(a))))
    P.b((7, 7, 1.4), (0, y + 21, -8.1), 'red', .6, rot=(0, 0, 45)); P.b((4, 4, 1.6), (0, y + 21, -8.4), 'gold', .85, rot=(0, 0, 45))
    P.b((5, 5, 5), (0, y + 34, 0), 'gold', .9, mat='neon', rot=(45, 45, 0))
    return P
