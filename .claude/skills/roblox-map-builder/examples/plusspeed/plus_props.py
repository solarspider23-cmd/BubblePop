# +1 Speed Run kit: every prop is a BlockProp (Parts: block / wedge / cyl / ball) in Roblox space, front = -Z.
# Low-poly stud style: chunky blocks, two-tone faces, stacked cubes, neon lanterns.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts')
sys.path.insert(0, SK)
from pro_lib import Palette
from blocks import BlockProp

PAL = Palette({
    'grass': ('#3a8f2e', '#62c84a', '#b8f07a'),
    'dirt':  ('#6b4325', '#a9703f', '#e3b07a'),
    'sand':  ('#b98a4a', '#e8c886', '#fff1c8'),
    'rock':  ('#5e3a2a', '#a0603e', '#d99a6e'),
    'stone': ('#5a5f70', '#a2a8b8', '#e6e9f0'),
    'wood':  ('#4d2c16', '#8a5530', '#cf945e'),
    'leaf':  ('#1d6b34', '#3faa52', '#9ee07a'),
    'pink':  ('#a8306a', '#ff6fae', '#ffc4e0'),
    'mint':  ('#0f7f73', '#2fd3b8', '#a8fff0'),
    'snow':  ('#7fa6cf', '#cfe6ff', '#ffffff'),
    'basalt': ('#231e2a', '#4a4058', '#8f86a8'),
    'fire':  ('#c43d00', '#ff8a1f', '#ffd27a'),
    'navy':  ('#0e1236', '#2a2f6e', '#6b74c8'),
    'gold':  ('#a35f00', '#ffc21a', '#fff2a0'),
    'red':   ('#9e1530', '#ff3b4f', '#ffa0aa'),
})

# ------------------------------------------------------------------ vegetation / theme dressing
def voxel_tree(seed, h=14.0, leaf='leaf', trunk='wood'):
    rng = random.Random(seed); P = BlockProp('Tree')
    tw = max(2.0, h * .16); th = h * .45
    P.b((tw, th, tw), (0, th / 2 - .5, 0), trunk, .45)
    P.b((tw + 1.2, 1.2, tw + 1.2), (0, .1, 0), trunk, .35)                                      # root collar
    cy = th + h * .12
    cubes = [((h * .55, h * .42, h * .55), (0, cy + h * .12, 0))]
    for k in range(rng.randint(3, 4)):
        a = k * math.tau / 4 + rng.uniform(-.4, .4); s = h * rng.uniform(.3, .4)
        cubes.append(((s, s * .85, s), (math.cos(a) * h * .26, cy + rng.uniform(-.04, .14) * h, math.sin(a) * h * .26)))
    cubes.append(((h * .3, h * .26, h * .3), (rng.uniform(-1, 1), cy + h * .42, rng.uniform(-1, 1))))
    for i, (s, p) in enumerate(cubes):
        P.b(s, p, leaf, .42 + .08 * (p[1] - cy) / h + rng.uniform(-.04, .04), rot=(0, rng.uniform(-15, 15), 0))
    return P

def pine(seed, h=16.0, snow=False):
    rng = random.Random(seed); P = BlockProp('Pine')
    P.b((2.0, h * .3, 2.0), (0, h * .15 - .5, 0), 'wood', .4)
    for i in range(4):
        w = h * (.62 - i * .13); y = h * (.22 + i * .17)
        P.b((w, h * .16, w), (0, y, 0), 'leaf', .32 + i * .06, rot=(0, 45 * (i % 2), 0))
        if snow: P.b((w * .72, h * .05, w * .72), (0, y + h * .1, 0), 'snow', .9, rot=(0, 45 * (i % 2), 0))
    P.b((h * .12, h * .12, h * .12), (0, h * .92, 0), 'snow' if snow else 'leaf', .9 if snow else .55)
    return P

def palm(seed, h=18.0):
    rng = random.Random(seed); P = BlockProp('Palm')
    lean = rng.uniform(-1, 1); y = 0; x = 0
    for i in range(6):
        seg = h / 6; x += lean * i * .25
        P.b((2.0 - i * .1, seg + .2, 2.0 - i * .1), (x, y + seg / 2, 0), 'wood', .45 + (i % 2) * .1, rot=(0, 0, -lean * i * 2.5))
        y += seg
    top = (x, y, 0)
    for k in range(6):
        a = k * 60 + rng.uniform(-10, 10)
        P.b((1.4, .5, 8.5), (top[0] + math.sin(math.radians(a)) * 3.6, top[1] - .6, math.cos(math.radians(a)) * 3.6), 'leaf', .45 + (k % 2) * .08, rot=(18, a, 0))
    for k in range(3):
        a = k * 120 + 30; P.b((1.3, 1.3, 1.3), (top[0] + math.sin(math.radians(a)) * 1.1, top[1] - 1.2, math.cos(math.radians(a)) * 1.1), 'dirt', .35, shape='ball')
    return P

def bush(seed, col='leaf', s=1.0):
    rng = random.Random(seed); P = BlockProp('Bush')
    for k in range(rng.randint(3, 5)):
        c = rng.uniform(2.2, 3.4) * s; a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(1, 2) * s
        P.b((c, c * .8, c), (math.cos(a) * d, c * .38, math.sin(a) * d), col, rng.uniform(.4, .62), rot=(0, rng.uniform(0, 45), 0))
    for k in range(3):
        a = rng.uniform(0, math.tau); P.b((.7, .7, .7), (math.cos(a) * 1.6 * s, 2.2 * s, math.sin(a) * 1.6 * s), ['red', 'pink', 'gold'][k], .6)
    return P

def flowers(seed):
    rng = random.Random(seed); P = BlockProp('Flowers')
    for k in range(7):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 3); x, z = math.cos(a) * d, math.sin(a) * d; h = rng.uniform(1.2, 2.2)
        P.b((.3, h, .3), (x, h / 2, z), 'leaf', .45)
        P.b((1.0, .5, 1.0), (x, h + .2, z), ['red', 'pink', 'gold', 'snow'][k % 4], .6, rot=(0, 45, 0))
        P.b((.45, .55, .45), (x, h + .3, z), 'gold', .7)
    return P

def cactus(seed, h=10.0):
    rng = random.Random(seed); P = BlockProp('Cactus')
    P.b((2.4, h, 2.4), (0, h / 2 - .5, 0), 'leaf', .5)
    P.b((2.0, 1.0, 2.0), (0, h - .2, 0), 'leaf', .62)
    for sx in (-1, 1):
        y = h * rng.uniform(.35, .55); L = rng.uniform(2.4, 3.2); up = rng.uniform(2.5, 4)
        P.b((L, 1.8, 1.8), (sx * (1.2 + L / 2), y, 0), 'leaf', .45)
        P.b((1.8, up, 1.8), (sx * (1.2 + L - .9), y + up / 2, 0), 'leaf', .5)
    P.b((1.0, 1.0, 1.0), (0, h + .4, 0), 'pink', .65, rot=(0, 45, 0))
    return P

def mesa(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('Mesa'); y = 0
    for k in range(3):
        w = (16 - k * 4) * s * rng.uniform(.9, 1.1); hh = rng.uniform(3, 5) * s
        P.b((w, hh, w * rng.uniform(.8, 1.0)), (rng.uniform(-1, 1), y + hh / 2 - .3, rng.uniform(-1, 1)), 'rock' if k % 2 == 0 else 'sand', .5 + k * .06)
        y += hh
    return P

def lollipop(seed, h=12.0):
    rng = random.Random(seed); P = BlockProp('Lollipop'); a, b = [('pink', 'snow'), ('mint', 'snow'), ('red', 'snow'), ('gold', 'pink')][seed % 4]
    P.b((h, .9, .9), (0, h / 2 - .5, 0), 'snow', .9, rot=(0, 0, 90), shape='cyl')
    for k, r in enumerate((8.0, 6.0, 4.0, 2.0)):
        P.b((1.2 + k * .05, r, r), (0, h + 3.4, 0), a if k % 2 == 0 else b, .6, shape='cyl', rot=(0, 90, 0))
    return P

def candy_cane(seed, h=12.0):
    P = BlockProp('CandyCane'); y = 0; n = int(h / 1.5)
    for k in range(n): P.b((1.4, 1.5, 1.4), (0, y + .75, 0), 'red' if k % 2 else 'snow', .6 if k % 2 else .9); y += 1.5
    for k, (dx, dy) in enumerate(((.9, .9), (2.2, 1.3), (3.4, .9), (4.0, -.2), (4.0, -1.5))):
        P.b((1.4, 1.4, 1.4), (dx, y + dy, 0), 'snow' if k % 2 else 'red', .9 if k % 2 else .6, rot=(0, 0, -30 * k))
    return P

def gumdrop(seed, col='pink'):
    P = BlockProp('Gumdrop')
    P.b((5, 3, 5), (0, 1.2, 0), col, .55, shape='ball'); P.b((4, 2.4, 4), (0, 2.4, 0), col, .7, shape='ball')
    return P

def snowman(seed):
    P = BlockProp('Snowman')
    for r, y in ((5, 2.2), (3.8, 5.8), (2.8, 8.6)): P.b((r, r, r), (0, y, 0), 'snow', .9, shape='ball')
    P.b((.6, .6, 1.8), (0, 8.6, -1.9), 'fire', .6)
    for sx in (-1, 1): P.b((.5, .5, .4), (sx * .6, 9.1, -1.3), 'basalt', .2)
    P.b((3.2, .4, 3.2), (0, 10.0, 0), 'basalt', .25, shape='cyl', rot=(0, 0, 90)); P.b((2.2, 2.0, 2.2), (0, 11.0, 0), 'basalt', .25, shape='cyl', rot=(0, 0, 90))
    P.b((4.2, .7, 4.2), (0, 7.2, 0), 'red', .6, shape='cyl', rot=(0, 0, 90))
    return P

def ice_crystal(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('IceCrystal')
    for k in range(4):
        h = rng.uniform(5, 10) * s; a = rng.uniform(0, math.tau)
        P.b((1.6 * s, h, 1.6 * s), (math.cos(a) * 1.2 * s, h / 2 - .5, math.sin(a) * 1.2 * s), 'snow' if k % 2 else 'mint', .75, rot=(rng.uniform(-15, 15), rng.uniform(0, 45), rng.uniform(-15, 15)), mat='neon' if k == 0 else 'stud')
    return P

def lava_rock(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('LavaRock')
    for k in range(5):
        c = rng.uniform(3, 6) * s; a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.5) * s
        P.b((c, c * rng.uniform(.6, 1.2), c), (math.cos(a) * d, c * .4, math.sin(a) * d), 'basalt', rng.uniform(.3, .5), rot=(rng.uniform(-10, 10), rng.uniform(0, 45), rng.uniform(-10, 10)))
    for k in range(3):
        a = rng.uniform(0, math.tau); P.b((.5, .4, rng.uniform(3, 5) * s), (math.cos(a) * 1.5 * s, .2, math.sin(a) * 1.5 * s), 'fire', .6, rot=(0, math.degrees(a), 0), mat='neon')
    return P

def mini_volcano(seed):
    P = BlockProp('Volcano'); y = 0
    for k, w in enumerate((22, 17, 12, 8)):
        P.b((w, 4, w), (0, y + 2, 0), 'basalt', .32 + k * .05, rot=(0, 15 * k, 0)); y += 4
    P.b((6, 1, 6), (0, y, 0), 'fire', .65, mat='neon')
    for k in range(4):
        a = k * 90 + 20; P.b((1.2, .4, 10), (math.sin(math.radians(a)) * 6, y - 5, math.cos(math.radians(a)) * 6), 'fire', .6, rot=(-28, a, 0), mat='neon')
    return P

def city_tower(seed, h=40.0):
    rng = random.Random(seed); P = BlockProp('Tower'); w = rng.uniform(12, 16); col = rng.choice(['navy', 'stone'])
    P.b((w, h, w), (0, h / 2 - .5, 0), col, .32 if col == 'navy' else .35)
    nc = rng.choice(['pink', 'mint', 'gold'])
    for k in range(int(h / 6)):
        y = 4 + k * 6
        for side in (-1, 1): P.b((w * .78, 1.0, .3), (0, y, side * (w / 2 + .1)), nc, .7, mat='neon')
    P.b((w + 1, 1.2, w + 1), (0, h, 0), 'navy', .5)
    P.b((.6, 8, .6), (w * .25, h + 4, 0), 'stone', .6); P.b((1.2, 1.2, 1.2), (w * .25, h + 8.4, 0), 'red', .6, mat='neon')
    return P

def neon_sign(seed):
    P = BlockProp('NeonSign'); c = ['pink', 'mint', 'gold'][seed % 3]
    for sx in (-1, 1): P.b((.8, 12, .8), (sx * 5, 6, 0), 'stone', .4)
    P.b((12, 6, 1), (0, 12, 0), 'navy', .25)
    for (w, h, x, y) in ((12.4, .5, 0, 15.1), (12.4, .5, 0, 8.9), (.5, 6.5, 6.1, 12), (.5, 6.5, -6.1, 12)): P.b((w, h, .4), (x, y, -.6), c, .7, mat='neon')
    P.b((7, 1.2, .4), (0, 12.8, -.6), 'snow', .9, mat='neon'); P.b((5, 1.0, .4), (0, 10.9, -.6), c, .7, mat='neon')
    return P

def planet(seed, r=10.0):
    rng = random.Random(seed); P = BlockProp('Planet'); col = ['pink', 'mint', 'fire', 'gold'][seed % 4]
    P.b((r, r, r), (0, 0, 0), col, .55, shape='ball')
    P.b((r * .2, r * 1.8, r * 1.8), (0, 0, 0), 'snow', .85, shape='cyl', rot=(20, 0, 70))
    return P

def asteroid(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('Asteroid')
    for k in range(4):
        c = rng.uniform(2, 4.5) * s; P.b((c, c, c), (rng.uniform(-2, 2) * s, rng.uniform(-1.5, 1.5) * s, rng.uniform(-2, 2) * s), 'basalt', rng.uniform(.4, .6), rot=(rng.uniform(0, 45), rng.uniform(0, 45), rng.uniform(0, 45)))
    return P

def star(seed, s=1.0):
    P = BlockProp('Star'); c = ['snow', 'gold', 'mint'][seed % 3]
    P.b((s, s, s), (0, 0, 0), c, .9, mat='neon', rot=(45, 45, 0)); return P

def cloud(seed, s=1.0):
    rng = random.Random(seed); P = BlockProp('Cloud')
    for k in range(rng.randint(5, 8)):
        c = rng.uniform(8, 14) * s; P.b((c * 1.4, c * .7, c), (rng.uniform(-14, 14) * s, rng.uniform(-1, 3) * s, rng.uniform(-6, 6) * s), 'snow', rng.uniform(.88, 1.0))
    return P

def crate(seed, s=3.0):
    P = BlockProp('Crate'); P.b((s, s, s), (0, s / 2, 0), 'wood', .55)
    for y in (.35, s - .35): P.b((s + .15, .5, s + .15), (0, y, 0), 'wood', .35)
    P.b((s + .15, s * .7, .5), (0, s / 2, 0), 'wood', .4, rot=(0, 0, 45)); return P

def fence(L=10.0, col='wood'):
    P = BlockProp('Fence')
    for x in (-L / 2, L / 2): P.b((1, 4, 1), (x, 1.6, 0), col, .45); P.b((1.4, .6, 1.4), (x, 3.8, 0), col, .6)
    for y in (1.6, 2.9): P.b((L, .6, .5), (0, y, 0), col, .55)
    return P

# ------------------------------------------------------------------ track furniture
def lamp_pillar(base_col='rock', pillar_col='fire', lantern='gold'):
    """the stacked-cube lamp pillar from the reference game"""
    P = BlockProp('LampPillar')
    P.b((10, 3, 10), (0, 1.0, 0), base_col, .4); P.b((8, 2, 8), (0, 3.5, 0), base_col, .48)
    for k in range(3): P.b((6, 6, 6), (0, 7.5 + k * 6, 0), pillar_col, .5 + (k % 2) * .08)
    P.b((7, 1, 7), (0, 23.0, 0), lantern, .6); P.b((9, 2, 9), (0, 24.5, 0), base_col, .48)
    P.b((4, 4, 4), (0, 27.5, 0), lantern, .7, mat='neon'); P.b((6, 1, 6), (0, 30.0, 0), 'basalt', .25)
    for sx in (-1, 1):
        for sz in (-1, 1): P.b((.6, 4, .6), (sx * 2.2, 27.5, sz * 2.2), 'basalt', .3)
    return P

def zone_gate(base_col, pillar_col, lantern, w=156.0):
    """two lamp pillars at the track edges, a top beam with a sign board (name / price via SurfaceGui later), a veil"""
    P = BlockProp('ZoneGate')
    for sx in (-1, 1): P.put(lamp_pillar(base_col, pillar_col, lantern), (sx * w / 2, 0, 0))
    P.b((w, 4, 6), (0, 34, 0), base_col, .45)
    P.b((w + 4, 1.4, 7), (0, 36.6, 0), lantern, .6)
    P.b((40, 12, 2), (0, 42, -1), 'basalt', .3); P.b((42, 1.2, 2.4), (0, 48.4, -1), lantern, .6); P.b((42, 1.2, 2.4), (0, 35.6, -1), lantern, .6)
    for sx in (-1, 1): P.b((1.2, 12, 2.4), (sx * 20.6, 42, -1), lantern, .6)
    P.b((36, 2.4, .4), (0, 44, -2.2), 'snow', .95, mat='neon'); P.b((22, 1.6, .4), (0, 40.2, -2.2), lantern, .7, mat='neon')
    P.b((w - 10, 32, .3), (0, 16, 0), lantern, .8, tr=.82, name='Veil')
    return P

def wins_pad(col='gold', r=12.0):
    P = BlockProp('WinsPad')
    P.b((1.0, r + 2, r + 2), (0, .1, 0), 'basalt', .3, shape='cyl', rot=(0, 0, 90))
    P.b((1.0, r + 1, r + 1), (0, .3, 0), col, .7, shape='cyl', rot=(0, 0, 90), mat='neon')
    P.b((1.0, r - 1.5, r - 1.5), (0, .5, 0), col, .55, shape='cyl', rot=(0, 0, 90))
    cup = BlockProp('Cup')                                                     # blocky trophy icon floating above
    cup.b((2.4, .6, 2.4), (0, 0, 0), 'gold', .5); cup.b((.8, 1.6, .8), (0, 1.1, 0), 'gold', .6)
    cup.b((3.2, 2.6, 3.2), (0, 3.0, 0), 'gold', .7)
    for sx in (-1, 1): cup.b((.6, 1.6, .6), (sx * 2.0, 3.2, 0), 'gold', .65)
    P.put(cup, (0, 6, 0))
    return P

def dist_board(col='stone'):
    P = BlockProp('DistBoard')
    P.b((1, 6, 1), (0, 3, 0), col, .45); P.b((7, 3, .6), (0, 7.2, 0), 'basalt', .3)
    P.b((7.6, .4, .8), (0, 8.9, 0), 'gold', .6); P.b((5, 1, .3), (0, 7.2, -.4), 'snow', .95, mat='neon')
    return P

# ------------------------------------------------------------------ hub stations
def treadmill(tier=0):
    cols = ['grass', 'stone', 'mint', 'gold', 'pink', 'fire']; c = cols[tier % len(cols)]
    P = BlockProp('Treadmill')
    P.b((10, 1.6, 22), (0, .8, 0), 'stone', .35)
    P.b((7.4, .4, 20), (0, 1.8, 0), 'basalt', .2)
    for k in range(5): P.b((4, .2, 1.2), (0, 2.05, -7 + k * 3.5), c, .7, mat='neon', rot=(0, 0, 0))
    for sx in (-1, 1):
        P.b((1, 1.4, 21), (sx * 4.4, 2.4, 0), c, .55); P.b((.8, 6, .8), (sx * 4.4, 4, -9.4), 'stone', .55)
    P.b((9.6, .8, 1.2), (0, 7.2, -9.4), 'stone', .6)
    P.b((6, 3.6, .8), (0, 8.8, -9.8), 'basalt', .25, rot=(-15, 0, 0)); P.b((5, 2.6, .3), (0, 8.8, -10.3), c, .7, mat='neon', rot=(-15, 0, 0))
    return P

def hatchery():
    P = BlockProp('Hatchery')
    P.b((30, 2, 30), (0, .5, 0), 'stone', .55); P.b((24, 1.5, 24), (0, 2.2, 0), 'stone', .65)
    for k in range(3): P.b((8 - k * 2, 1, 2.5), (0, .2 + k, -15.5 + k * 1.2), 'stone', .6)
    P.b((8, 2, 8), (0, 4, 0), 'gold', .55)
    P.b((9, 11, 9), (0, 10.4, 0), 'snow', .95, shape='ball'); P.b((7.6, 4.5, 7.6), (0, 15.4, 0), 'snow', .95, shape='ball')
    for k, (y, c) in enumerate(((9.0, 'pink'), (12.0, 'mint'))):
        for a in range(0, 360, 45):
            P.b((1.6, 1.6, .6), (math.sin(math.radians(a)) * 4.4, y, math.cos(math.radians(a)) * 4.4), c, .6, rot=(0, a, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.b((2.4, 18, 2.4), (sx * 10, 11, sz * 10), 'stone', .62); P.b((3.2, 1.2, 3.2), (sx * 10, 20.4, sz * 10), 'gold', .6)
            P.b((1.6, 1.6, 1.6), (sx * 10, 22, sz * 10), 'pink', .7, mat='neon', rot=(45, 45, 0))
    P.b((26, 1.6, 26), (0, 21.6, 0), 'pink', .5)
    for k, w in enumerate((22, 16, 10, 4)): P.b((w, 2.2, w), (0, 23.4 + k * 2.2, 0), 'pink' if k % 2 == 0 else 'snow', .55 if k % 2 == 0 else .9)
    P.b((12, 4, 1), (0, 26, -13.8), 'basalt', .3); P.b((10, 2, .3), (0, 26, -14.4), 'pink', .7, mat='neon')
    return P

def shop_stall():
    P = BlockProp('Shop'); w, d = 18, 10
    P.b((w + 2, 1, d + 2), (0, 0, 0), 'stone', .55)
    P.b((w, 4, 3), (0, 2.5, -d / 2 + 1.5), 'wood', .55); P.b((w + .6, .8, 3.6), (0, 4.8, -d / 2 + 1.5), 'gold', .6)
    for sx in (-1, 1):
        for sz in (-1, 1): P.b((1, 12, 1), (sx * (w / 2 - .5), 6, sz * (d / 2 - .5)), 'wood', .4)
    P.b((w - 1, 10, 1), (0, 5.5, d / 2 - .5), 'wood', .48)
    for k in range(8):
        x = -w / 2 + w * (k + .5) / 8; P.b((w / 8, .6, d + 3), (x, 12.6, -.8), 'red' if k % 2 else 'snow', .6 if k % 2 else .92, rot=(-14, 0, 0))
    for k in range(4): P.b((1.6, 1.6, 1.6), (-6 + k * 4, 5.9, -d / 2 + 1.5), ['pink', 'mint', 'gold', 'red'][k], .6, rot=(0, 45, 0))
    P.b((14, 4, 1), (0, 16.5, 0), 'basalt', .3); P.b((12, 2, .3), (0, 16.5, -.6), 'gold', .7, mat='neon')
    return P

def rebirth_altar():
    P = BlockProp('Rebirth')
    for k, w in enumerate((24, 19, 14)): P.b((w, 1.6, w), (0, .5 + k * 1.6, 0), 'stone', .5 + k * .07, rot=(0, 45 * (k % 2), 0))
    for a in range(45, 360, 90):
        x, z = math.sin(math.radians(a)) * 9, math.cos(math.radians(a)) * 9
        P.b((2, 12, 2), (x, 9, z), 'navy', .5); P.b((2.8, 1, 2.8), (x, 15.5, z), 'gold', .6); P.b((1.4, 1.4, 1.4), (x, 17, z), 'mint', .7, mat='neon', rot=(45, 45, 0))
    P.b((6, 6, 6), (0, 12, 0), 'pink', .7, mat='neon', rot=(35, 45, 0))
    P.b((9, .8, 9), (0, 5.2, 0), 'gold', .6, rot=(0, 45, 0))
    return P

def leaderboard():
    P = BlockProp('Leaderboard')
    for sx in (-1, 1): P.b((3, 26, 3), (sx * 13, 12, 0), 'stone', .55); P.b((4, 2, 4), (sx * 13, 26, 0), 'gold', .6)
    P.b((24, 18, 2), (0, 15, 0), 'basalt', .3)
    for k, c in enumerate(('gold', 'stone', 'dirt', 'navy', 'navy', 'navy')):
        P.b((19, 1.8, .4), (1, 21.5 - k * 2.6, -1.2), c, .7 if k < 3 else .55, mat='neon' if k < 3 else 'stud')
        P.b((1.6, 1.6, .4), (-10, 21.5 - k * 2.6, -1.2), 'snow', .95)
    P.b((26, 2, 3), (0, 25, 0), 'gold', .55)
    for k in range(5): P.b((1.4, 2.4 if k % 2 == 0 else 1.6, 1.4), (-4 + k * 2, 27 + (.4 if k % 2 == 0 else 0), 0), 'gold', .7)
    return P

def spawn_pad():
    P = BlockProp('SpawnPad')
    P.b((1, 18, 18), (0, .2, 0), 'stone', .65, shape='cyl', rot=(0, 0, 90))
    P.b((1, 16, 16), (0, .4, 0), 'mint', .7, shape='cyl', rot=(0, 0, 90), mat='neon')
    P.b((1, 14, 14), (0, .6, 0), 'stone', .8, shape='cyl', rot=(0, 0, 90))
    P.b((1.6, .3, 4.0), (0, 1.15, -2.6), 'gold', .75); P.b((4.4, .3, 1.6), (0, 1.15, -4.6), 'gold', .75, rot=(0, 45, 0))   # arrow toward the track
    return P

def big_arch(text_col='gold', w=176.0, checker=True):
    """START / FINISH arch: two chunky towers, a deep beam with a black/white checker band, a sign board"""
    P = BlockProp('Arch')
    for sx in (-1, 1):
        x = sx * (w / 2 + 6)
        P.b((14, 4, 14), (x, 1.5, 0), 'stone', .5)
        for k in range(5): P.b((11 - (k % 2), 8, 11 - (k % 2)), (x, 7.5 + k * 8, 0), 'stone' if k % 2 else text_col, .6 if k % 2 else .55)
        P.b((14, 3, 14), (x, 48, 0), 'stone', .5); P.b((6, 6, 6), (x, 53, 0), text_col, .7, mat='neon', rot=(0, 45, 0))
    P.b((w + 26, 10, 8), (0, 44, 0), 'stone', .55)
    if checker:
        n = int((w + 24) / 4)
        for k in range(n):
            for row in range(2): P.b((4, 2, .6), (-(w + 24) / 2 + 2 + k * 4, 41 + row * 2, -4.2), 'basalt' if (k + row) % 2 else 'snow', .15 if (k + row) % 2 else .95)
    P.b((60, 14, 3), (0, 57, -1), 'basalt', .3); P.b((56, 3, .4), (0, 59, -2.8), 'snow', .95, mat='neon'); P.b((40, 2, .4), (0, 54.5, -2.8), text_col, .7, mat='neon')
    for y in (49.6, 64.4): P.b((62, 1.4, 3.6), (0, y, -1), text_col, .6)
    return P

def trophy():
    """finish hero: 1-2-3 podium with a giant blocky trophy on the top step"""
    P = BlockProp('Trophy')
    for x, h, c in ((0, 10, 'gold'), (-20, 7, 'stone'), (20, 5, 'dirt')):
        P.b((18, h, 16), (x, h / 2 - .5, 0), 'stone', .62); P.b((18.6, 1, 16.6), (x, h, 0), c, .65)
        P.b((6, 5, .4), (x, h / 2, -8.3), c, .7, mat='neon')
    y = 10.5
    P.b((14, 3, 14), (0, y + 1.5, 0), 'basalt', .3); P.b((10, 2, 10), (0, y + 4, 0), 'gold', .55)
    P.b((3, 8, 3), (0, y + 9, 0), 'gold', .6); P.b((8, 2, 8), (0, y + 13.5, 0), 'gold', .55)
    for k, w in enumerate((10, 14, 18, 20, 20)): P.b((w, 3.4, w), (0, y + 16 + k * 3.4, 0), 'gold', .62 + k * .04, rot=(0, 45 * (k % 2), 0))
    P.b((21.4, 1.4, 21.4), (0, y + 33.4, 0), 'gold', .85)
    for sx in (-1, 1):
        for dy, dx in ((20, 13), (25, 15), (30, 13)): P.b((3, 3, 3), (sx * dx, y + dy, 0), 'gold', .7)
    P.b((8, 8, 1.2), (0, y + 24, -10.6), 'red', .6, rot=(0, 0, 45))
    P.b((5, 5, 5), (0, y + 39, 0), 'gold', .9, mat='neon', rot=(45, 45, 0))
    return P


from plus_props_fix import *  # noqa  (v2 overrides)
from plus_props_v3 import *  # noqa  (v3 detailed builds)
