# Skyrise v2 models, part 2: resource nodes, biome dressing, stations (override the first-pass kit, same names).
import math, random
import bmesh
from mathutils import Vector, Matrix
from sky_props import G, Prop, S, at, lathe, sphere, torus, gem, box, cyl, spike, tube, hull, ngon_prism, rock_pts, nz
from sky_models import lumpy

def coin(r=.7, t=.22):
    """coin with a raised rim (lathe), lying flat"""
    return lathe([(r, 0), (r, t), (r * .78, t * .8), (0, t * .8)], n=8)

def bottle(h=1.6):
    return lathe([(.45, 0), (.5, .1), (.5, h * .55), (.22, h * .75), (.2, h * .95), (.26, h), (0, h)], n=10)

def planks(w, h, d, seed, col='wood', n=4):
    """n separate bevelled planks side by side along x, alternating shade (reads as wood)"""
    pw = w / n
    return [(at(box((pw - .08, h, d), .06), (-w / 2 + pw * (k + .5), 0, 0)), S(col, base=.48 + (k % 2) * .08, jit=.03, seed=seed + k))
            for k in range(n)]

# ======================================================================== resource nodes
def coin_pile(seed, s=1.0):
    """a heap built only from coins (rings of tilted coins, smaller toward the top), two coin towers, a gem"""
    rng = random.Random(seed); P = Prop('CoinPile%d' % seed)
    goldS = lambda: S('gold', base=rng.uniform(.62, .82), up=.15, jit=0)
    for layer, (R, y) in enumerate(((2.4, 0), (1.8, .35), (1.2, .7), (.6, 1.0))):
        n = max(3, int(R * 3.6))
        for k in range(n):
            a = k * math.tau / n + rng.uniform(-.2, .2) + layer; d = R * rng.uniform(.55, 1.0)
            P.add(at(coin(.62 * s, .2 * s), (math.cos(a) * d * s, y * s, math.sin(a) * d * s),
                     (rng.uniform(-28, 28), rng.uniform(0, 360), rng.uniform(-28, 28))), goldS(), smooth=True)
    for t, (x, z) in enumerate(((1.9, -.4), (-1.6, 1.0))):
        for j in range(4 + t * 2):
            P.add(at(coin(.6 * s, .2 * s), (x * s + rng.uniform(-.05, .05), j * .21 * s, z * s), (0, rng.uniform(0, 360), 0)), goldS(), smooth=True)
    P.add(at(coin(.62 * s, .2 * s), (.4 * s, .9 * s, -1.4 * s), (72, 20, 0)), goldS(), smooth=True)
    P.gadd(at(gem(.42 * s, 1.0 * s), (-.3 * s, 1.15 * s, .2 * s), (12, 0, 8)), 'gem')
    return P

def chest(seed=1, s=1.0):
    """planked chest, curved lid held open, iron bands following the curve, corner caps, lock, overflowing coins"""
    rng = random.Random(seed); P = Prop('Chest%d' % seed); w, d, h = 4.8 * s, 3.2 * s, 2.4 * s
    for k in range(4):
        P.add(at(box((w - .1, h / 4 - .06, d), .05 * s), (0, h / 8 + k * h / 4, 0)), S('wood', base=.45 + (k % 2) * .08, jit=.02, seed=k))
    for x in (-w / 2 + .45 * s, 0, w / 2 - .45 * s):
        P.add(at(box((.4 * s, h + .08, d + .12), .05), (x, h / 2, 0)), S('gold', base=.5))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(at(box((.6 * s, .6 * s, .6 * s), .12 * s), (sx * (w / 2 - .1), h - .2 * s, sz * (d / 2 - .1))), S('gold', base=.62))
    r = d / 2; rot = Matrix.Rotation(math.radians(-105), 3, 'X'); hinge = Vector((0, h, d / 2))
    lid = bmesh.new()
    prof = [Vector((0, math.sin(a) * r, -math.cos(a) * r + r)) for a in [math.pi * i / 8 for i in range(9)]]
    L = [lid.verts.new(Vector((-w / 2, 0, 0)) + p) for p in prof]; Rr = [lid.verts.new(Vector((w / 2, 0, 0)) + p) for p in prof]
    for i in range(8): lid.faces.new((L[i], L[i + 1], Rr[i + 1], Rr[i]))
    lid.faces.new(L); lid.faces.new(list(reversed(Rr))); bmesh.ops.recalc_face_normals(lid, faces=list(lid.faces))
    bmesh.ops.translate(lid, vec=Vector((0, 0, -d)), verts=lid.verts)
    bmesh.ops.rotate(lid, cent=Vector(), matrix=rot, verts=lid.verts); bmesh.ops.translate(lid, vec=hinge, verts=lid.verts)
    P.add(lid, S('wood', base=.55, up=.15, jit=.02))
    for x in (-w / 2 + .45 * s, w / 2 - .45 * s):
        band = [hinge + rot @ Vector((x, math.sin(a) * (r + .06), -math.cos(a) * (r + .06) + r - d)) for a in [math.pi * i / 8 for i in range(9)]]
        P.add(tube(band, .16 * s, sides=4), S('gold', base=.5))
    P.add(at(box((1.0 * s, 1.1 * s, .3 * s), .1 * s), (0, h * .72, -d / 2 - .12)), S('gold', base=.6))
    P.add(at(cyl(.18 * s, .32 * s, sides=8), (0, h * .7, -d / 2 - .28), (90, 0, 0)), S('basalt', base=.2, jit=0))
    for k in range(14):
        a = rng.uniform(0, math.tau); dd = rng.uniform(0, 1.4) * s
        P.add(at(coin(.55 * s, .18 * s), (math.cos(a) * dd * 1.4, h + rng.uniform(-.1, .5) * s, math.sin(a) * dd * .7),
                 (rng.uniform(-30, 30), rng.uniform(0, 360), rng.uniform(-30, 30))), S('gold', base=rng.uniform(.65, .82), jit=0), smooth=True)
    for k in range(4):
        P.add(at(coin(.55 * s, .18 * s), (rng.uniform(-1.6, 1.6) * s, .05, -d / 2 - rng.uniform(.6, 1.6) * s), (rng.uniform(-6, 6), rng.uniform(0, 360), 0)),
              S('gold', base=.7, jit=0), smooth=True)
    P.gadd(at(gem(.5 * s, 1.2 * s), (.7 * s, h + .4 * s, .1 * s), (10, 0, -12)), 'gem')
    return P

def crystal_node(seed, key='crystal', col='ice', s=1.0):
    """6-9 hexagonal crystals with pointed tips radiating from a rock bed, a tall glowing core crystal, pebbles"""
    rng = random.Random(seed); P = Prop('Crystal%d_%s' % (seed, key))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(-.4, .4); d = rng.uniform(.6, 1.6) * s
        P.add(at(hull(rock_pts((rng.uniform(1.2, 1.9) * s, rng.uniform(.7, 1.1) * s, rng.uniform(1.0, 1.6) * s), n=12, seed=seed * 7 + k)),
                 (math.cos(a) * d, .2, math.sin(a) * d)), S('rock', base=rng.uniform(.38, .55), up=.2, jit=.03))
    n = rng.randint(6, 9)
    for k in range(n):
        h = (5.6 if k == 0 else rng.uniform(2.0, 4.4)) * s; r = (.8 if k == 0 else rng.uniform(.4, .65)) * s
        g = lathe([(0, -.3), (r, 0), (r, h * .72), (r * .55, h * .86), (0, h)], n=6)
        if k:
            a = k * math.tau / (n - 1) + rng.uniform(-.25, .25); tilt = math.radians(rng.uniform(18, 42))
            dirv = Vector((math.cos(a) * math.sin(tilt), math.cos(tilt), math.sin(a) * math.sin(tilt)))
            q = Vector((0, 1, 0)).rotation_difference(dirv); bmesh.ops.rotate(g, cent=Vector(), matrix=q.to_matrix(), verts=g.verts)
            pos = (math.cos(a) * .7 * s, .5, math.sin(a) * .7 * s)
        else: pos = (0, .4, 0)
        if k == 0 or k % 3 == 0: P.gadd(at(g, pos), key)
        else: P.add(at(g, pos), S(col, grad=(0, h, .4, .92), up=.2, jit=.02, seed=k))
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(2.0, 2.8) * s
        P.add(at(hull(rock_pts((.35 * s, .25 * s, .3 * s), n=8, seed=seed + 40 + k)), (math.cos(a) * d, 0, math.sin(a) * d)), S('rock', base=.5))
    return P

# ======================================================================== biome dressing
def _ribbed(a, b, r0, r1, n=16):
    """12-point star section swept along a straight segment a->b, domed cap"""
    d = b - a; L = d.length; bm = bmesh.new(); rings = []
    for t in (0, .25, .5, .75, 1):
        rr = r0 + (r1 - r0) * t
        rings.append([bm.verts.new((math.cos(i * math.tau / n) * rr * (1 if i % 2 == 0 else .86), L * t,
                                    math.sin(i * math.tau / n) * rr * (1 if i % 2 == 0 else .86))) for i in range(n)])
    for A, B in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    cap = bm.verts.new((0, L + r1 * .7, 0))
    for i in range(n): bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], cap))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    q = Vector((0, 1, 0)).rotation_difference(d.normalized()); bmesh.ops.rotate(bm, cent=Vector(), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=a, verts=bm.verts); return bm

def cactus(seed, h=7.0):
    """ribbed saguaro: star-section body, two elbowed arms, flowers, pebbles"""
    rng = random.Random(seed); P = Prop('Cactus%d' % seed)
    sh = lambda: S('leaf', grad=(0, h, .3, .72), up=.15, jit=.02)
    P.add(_ribbed(Vector((0, -.4, 0)), Vector((0, h, 0)), 1.05, .9), sh())
    for sx in (-1, 1):
        y0 = h * rng.uniform(.32, .5); L = rng.uniform(1.4, 2.0); up = rng.uniform(1.6, 2.8); x = sx * (L + .4)
        elbow = Vector((x, y0 + .45, 0))
        P.add(_ribbed(Vector((0, y0, 0)), elbow, .62, .62), sh())
        P.add(at(sphere(.66, 12, 8), elbow), sh(), smooth=True)                 # rounded elbow joint
        P.add(_ribbed(elbow, Vector((x, y0 + up, 0)), .62, .55), sh())
        P.add(at(lumpy(.42, seed + sx, 1, .2), (x, y0 + up + .45, 0)), S('pink', base=.62), smooth=True)
    for k in range(3):
        a = k * math.tau / 3
        P.add(at(lumpy(.4, seed * 3 + k, 1, .2), (math.cos(a) * .5, h + .7, math.sin(a) * .5)), S(['pink', 'gold', 'red'][k], base=.62), smooth=True)
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(1.4, 2.4)
        P.add(at(hull(rock_pts((.4, .25, .35), n=8, seed=seed * 9 + k)), (math.cos(a) * d, -.1, math.sin(a) * d)), S('sand', base=.4))
    return P

def basalt_rocks(seed, s=1.0):
    """hexagonal basalt columns of stepped heights, lighter bevelled tops, glowing lava seams at the base, rubble"""
    rng = random.Random(seed); P = Prop('Basalt%d' % seed); cols = []
    for k in range(rng.randint(6, 9)):
        a = rng.uniform(0, math.tau); d = (0 if k == 0 else rng.uniform(1.0, 2.6)) * s
        cols.append((math.cos(a) * d, math.sin(a) * d, (rng.uniform(4.5, 7.5) if k < 3 else rng.uniform(1.5, 4.0)) * s, rng.uniform(.8, 1.15) * s))
    for x, z, h, r in cols:
        yaw = rng.uniform(0, 60)
        P.add(at(lathe([(r, -.5), (r, h - .25), (r * .82, h), (0, h)], n=6), (x, 0, z), (0, yaw, 0)), S('basalt', grad=(0, h, .3, .55), up=.3, jit=.03))
        P.add(at(lathe([(r * .8, 0), (r * .8, .08), (0, .08)], n=6), (x, h - .02, z), (0, yaw, 0)), S('basalt', base=.7, jit=0))
    for k in range(3):
        a = rng.uniform(0, math.tau); d = rng.uniform(.6, 1.8) * s
        P.gadd(at(box((.35 * s, .2, rng.uniform(1.5, 3.0) * s)), (math.cos(a) * d, .05, math.sin(a) * d), (0, math.degrees(a), 0)), 'lava')
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(2.6, 3.6) * s
        P.add(at(hull(rock_pts((.5 * s, .35 * s, .45 * s), n=8, seed=seed * 5 + k)), (math.cos(a) * d, 0, math.sin(a) * d)), S('basalt', base=.42))
    return P

# ======================================================================== stations
def egg_shrine():
    """egg hatch altar: 3-tier dais with gold inlay + front steps, golden claw cradle on a column, banded and spotted
    giant egg, four crystal-topped pillars carrying a gem crown ring"""
    P = Prop('EggShrine')
    P.add(lathe([(11.5, -.8), (11.5, .5), (11.0, .8), (10.0, .8), (10.0, 1.7), (9.5, 2.0), (8.0, 2.0), (8.0, 2.9), (7.6, 3.1), (0, 3.1)], n=40),
          S('stone', base=.62, up=.25))
    for y, r in ((.62, 11.3), (1.85, 9.85), (3.0, 7.85)): P.add(at(torus(r, .26, n=48, sides=5), (0, y, 0)), S('gold', base=.6))
    for k in range(3): P.add(at(box((7.5 - k, .85, 2.0), .12), (0, k * .85 + .35, -11.8 + k * 1.2)), S('stone', base=.68 + k * .03))
    P.add(lathe([(2.6, 3.1), (2.2, 3.6), (1.6, 3.8), (1.6, 5.6), (2.4, 6.0), (2.8, 6.4), (0, 6.4)], n=16), S('stone', base=.7))
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        pts = [Vector((math.cos(a) * 2.2, 6.2, math.sin(a) * 2.2)), Vector((math.cos(a) * 4.4, 7.6, math.sin(a) * 4.4)),
               Vector((math.cos(a) * 4.6, 10.0, math.sin(a) * 4.6)), Vector((math.cos(a) * 3.6, 11.4, math.sin(a) * 3.6))]
        P.add(tube(pts, [.55, .5, .4, .2], sides=7), S('gold', base=.62), smooth=True)
    egg = [(0, 5.9), (2.0, 6.3), (3.5, 7.4), (4.3, 9.2), (4.4, 11.0), (3.9, 13.2), (2.9, 15.0), (1.5, 16.3), (0, 16.7)]
    P.add(lathe(egg, n=40), S('cloud', grad=(6, 16.7, .62, .96), up=.1), smooth=True)
    for k, (y0, y1, col, r0, r1) in enumerate(((9.6, 10.6, 'violet', 4.42, 4.36), (12.7, 13.3, 'pink', 4.0, 3.8))):
        P.add(lathe([(r0 + .02, y0), (r0 + .1, y0 + .1), (r1 + .1, y1 - .1), (r1 + .02, y1)], n=40), S(col, base=.58, jit=0), smooth=True)
    rng = random.Random(3)
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-.15, .15); y = (8.0, 11.8, 14.4)[k % 3]
        rr = {8.0: 4.0, 11.8: 4.25, 14.4: 3.25}[y]
        P.add(at(lathe([(.9, 0), (.85, .18), (0, .22)], n=10), (math.cos(a) * rr, y, math.sin(a) * rr), (90, -math.degrees(a) - 90, 0)),
              S('gold', base=.65, jit=0), smooth=True)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4; x, z = math.cos(a) * 9.0, math.sin(a) * 9.0
        P.add(at(lathe([(1.0, 0), (1.0, .5), (.7, .7), (.7, 9.5), (1.1, 9.9), (1.1, 10.5), (0, 10.5)], n=8), (x, 2.0, z)), S('stone', grad=(2, 12, .55, .72)))
        for y in (5.0, 9.0): P.add(at(cyl(.78, .3, sides=8), (x, y, z)), S('gold', base=.55))
        P.gadd(at(gem(.8, 2.6), (x, 12.5, z)), 'egg')
        P.add(tube([Vector((x, 12.5, z)), Vector((x, 15.3, z))], .22, sides=5), S('gold', base=.5))
    P.add(at(torus(9.0, .38, n=48, sides=6), (0, 15.6, 0)), S('gold', base=.6))
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8; P.gadd(at(gem(.55, 1.3), (math.cos(a) * 9.0, 15.3, math.sin(a) * 9.0)), 'egg' if k % 2 else 'gem')
    return P

DOLLAR = [(-.5, -1.6), (.5, -1.6), (.5, -1.1), (1.4, -.9), (1.4, .1), (-.4, .4), (-.4, .9), (1.3, .9), (1.3, 1.6), (.5, 1.6), (.5, 2.0),
          (-.5, 2.0), (-.5, 1.6), (-1.4, 1.4), (-1.4, .4), (.4, .0), (.4, -.6), (-1.3, -.6), (-1.3, -1.1), (-.5, -1.1)]

def sell_pad():
    """sell booth: glowing sell circle in front, planked counter with gold trim, a giant coin sign on two posts,
    coin sacks and coin towers around (front -Z)"""
    rng = random.Random(4); P = Prop('SellPad')
    P.add(lathe([(7.0, -.5), (7.0, .3), (6.6, .5), (0, .5)], n=40), S('stone', base=.68))
    P.add(at(torus(6.7, .3, n=48, sides=5), (0, .45, 0)), S('gold', base=.58))
    P.gadd(at(lathe([(5.6, 0), (5.6, .12), (0, .12)], n=40), (0, .5, 0)), 'sell')
    P.add(at(lathe([(3.4, 0), (3.4, .1), (0, .1)], n=40), (0, .6, 0)), S('gold', base=.7, jit=0))
    for part, sh in planks(10.0, 3.2, 3.0, 7): P.add(at(part, (0, 1.4, 8.4)), sh)
    P.add(at(box((10.6, .5, 3.6), .15), (0, 3.2, 8.4)), S('gold', base=.6))
    P.add(at(box((10.4, .4, 3.4), .1), (0, -.1, 8.4)), S('wood', base=.35))
    for sx in (-1, 1): P.add(at(lathe([(.55, 0), (.55, 11), (.8, 11.3), (0, 11.5)], n=8), (sx * 4.6, 0, 10.2)), S('wood', base=.45))
    P.add(at(box((9.8, .5, .5), .1), (0, 10.8, 10.2)), S('wood', base=.5))
    P.add(at(lathe([(3.4, 0), (3.6, .2), (3.6, .9), (3.4, 1.1), (0, 1.1)], n=40), (0, 14.3, 10.0), (90, 0, 0)), S('gold', base=.66, up=.2), smooth=True)
    P.add(at(torus(2.8, .3, n=32, sides=5), (0, 14.3, 8.95), (90, 0, 0)), S('gold', base=.4))
    P.add(at(ngon_prism([(x * .8, z * .8) for x, z in DOLLAR], -.25, .25), (0, 14.1, 8.85), (90, 0, 0)), S('gold', base=.38, jit=0))
    for k, (x, z) in enumerate(((-6.8, 6.0), (6.6, 5.4), (-7.6, 1.0))):
        P.add(at(lumpy(1.5, 20 + k, 2, .1, 1.1), (x, 1.3, z)), S('dirt', grad=(0, 3, .55, .8), jit=.02))
        P.add(at(lathe([(.6, 0), (.35, .4), (.7, .9), (0, 1.0)], n=8), (x, 2.6, z)), S('dirt', base=.65))
        P.add(at(cyl(.48, .25, sides=8), (x, 2.75, z)), S('red', base=.55))
        for j in range(3):
            P.add(at(coin(.5, .18), (x + rng.uniform(-1.2, 1.2), .05, z - 1.6 + rng.uniform(-.4, .4)), (rng.uniform(-8, 8), rng.uniform(0, 360), 0)),
                  S('gold', base=.72, jit=0), smooth=True)
    for k, (x, z, n) in enumerate(((6.2, 1.4, 6), (5.0, 2.4, 4), (-5.4, 4.4, 5))):
        for j in range(n): P.add(at(coin(.6, .2), (x, .5 + j * .21, z), (0, rng.uniform(0, 360), 0)), S('gold', base=.64 + (j % 2) * .1, jit=0), smooth=True)
    return P

def upgrade_stand():
    """upgrade shop: planked counter with gold trim, back wall with shelves of glowing potions, scalloped striped
    awning, hanging lanterns, triple up-arrow sign on the roof, crates beside (front -Z)"""
    P = Prop('UpgradeStand'); w, d = 13.0, 7.0
    P.add(at(box((w + 1.4, .8, d + 1.6), .2), (0, -.1, 0)), S('stone', base=.6))
    for part, sh in planks(w - 1, 3.4, 1.8, 3): P.add(at(part, (0, 2.0, -d / 2 + 1.2)), sh)
    P.add(at(box((w - .4, .45, 2.4), .12), (0, 3.85, -d / 2 + 1.2)), S('gold', base=.6))
    for part, sh in planks(w - 1, 8.0, .6, 9, n=6): P.add(at(part, (0, 4.3, d / 2 - .4)), sh)
    keys = ['egg', 'crystal', 'gem', 'sell', 'z5', 'lamp']
    for y in (3.2, 5.6):
        P.add(at(box((w - 2, .3, 1.4), .06), (0, y, d / 2 - 1.2)), S('wood', base=.6))
        for k in range(6):
            x = -w / 2 + 2.0 + k * (w - 4) / 5
            P.add(at(bottle(1.5), (x, y + .15, d / 2 - 1.2)), S('cloud', base=.75, jit=0), smooth=True)
            P.gadd(at(lathe([(.46, 0), (.5, .1), (.5, .72), (0, .72)], n=10), (x, y + .2, d / 2 - 1.2)), keys[(k + int(y)) % 6])
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(at(lathe([(.45, 0), (.45, 9.2), (.6, 9.4), (0, 9.5)], n=8), (sx * (w / 2 - .4), 0, sz * (d / 2 - .4))), S('wood', base=.45))
    nst = 9; sw = (w + 1) / nst
    for k in range(nst):
        xm = -(w + 1) / 2 + sw * (k + .5); col = 'violet' if k % 2 else 'cloud'
        P.add(at(box((sw, .3, d + 2.4), .04), (xm, 9.9, -.5), (-12, 0, 0)), S(col, base=.62, jit=0))
        P.add(at(lathe([(sw / 2, 0), (sw / 2, .25), (0, .25)], n=10), (xm, 9.3, -d / 2 - 1.6), (90, 0, 0)), S(col, base=.58, jit=0))
    for sx in (-1, 1):
        x = sx * (w / 2 - .4)
        P.add(at(cyl(.08, 1.4, sides=4), (x, 7.6, -d / 2 - .6)), S('basalt', base=.3))
        P.add(at(lathe([(.4, 0), (.55, .2), (.55, 1.0), (.3, 1.3), (0, 1.35)], n=8), (x, 6.3, -d / 2 - .6)), S('gold', base=.5))
        P.gadd(at(lathe([(.45, 0), (.45, .75), (0, .75)], n=8), (x, 6.5, -d / 2 - .6)), 'lamp')
    for sx in (-1, 1): P.add(at(box((.5, 3.6, .5), .08), (sx * 3.4, 12.0, 1.0)), S('wood', base=.45))
    P.add(at(box((8.4, 3.8, .6), .25), (0, 13.6, 1.0)), S('violet', base=.4))
    for y in (15.6, 11.6): P.add(at(box((8.8, .4, .8), .1), (0, y, 1.0)), S('gold', base=.6))
    arrow = [(-1.0, -1.4), (1.0, -1.4), (1.0, .1), (2.1, .1), (0, 2.0), (-2.1, .1), (-1.0, .1)]
    for x in (-2.6, 0, 2.6): P.gadd(at(ngon_prism(arrow, -.25, .25), (x, 13.4, .6), (-90, 0, 0), s=(.7, 1, .7)), 'z5')
    P.add(at(box((2.2, 2.2, 2.2), .15), (w / 2 + 1.7, 1.0, -1.2)), S('wood', base=.55))
    P.add(at(box((2.0, 2.0, 2.0), .15), (w / 2 + 1.5, 1.0, 1.4), (0, 20, 0)), S('wood', base=.6))
    P.add(at(box((1.7, 1.7, 1.7), .15), (w / 2 + 1.6, 3.0, -.9), (0, 12, 0)), S('wood', base=.65))
    return P

def leaderboard():
    """stone frame with side columns and a gem crown crest; screen with gold/silver/bronze rank rows and avatar
    dots; 1-2-3 podium in front (front -Z)"""
    P = Prop('Leaderboard')
    for sx in (-1, 1):
        x = sx * 8.2
        P.add(at(box((2.6, 1.0, 2.6), .2), (x, .2, 0)), S('stone', base=.55))
        P.add(at(lathe([(.95, 0), (.95, 16.5), (1.3, 16.9), (1.3, 17.5), (0, 17.5)], n=8), (x, .6, 0)), S('stone', grad=(0, 18, .55, .7)))
        for y in (5, 10, 15): P.add(at(cyl(1.05, .35, sides=8), (x, y, 0)), S('gold', base=.55))
    P.add(at(box((15.4, 12.4, 1.2), .3), (0, 10.8, .2)), S('stone', base=.62))
    P.add(at(box((13.6, 10.6, .4), .1), (0, 10.8, -.45)), S('basalt', base=.45, jit=0))
    for k, col in enumerate(('gold', 'cloud', 'dirt', 'violet', 'violet', 'violet')):
        y = 15.0 - k * 1.65
        P.add(at(box((11.2, 1.2, .2), .08), (.6, y, -.7)), S(col, base=.62 if k < 3 else .45, jit=0))
        P.add(at(cyl(.55, .2, sides=12), (-5.6, y, -.75), (90, 0, 0)), S(['gold', 'cloud', 'dirt', 'stone', 'stone', 'stone'][k], base=.75, jit=0))
    P.add(at(box((16.4, 1.0, 1.8), .25), (0, 17.4, .2)), S('gold', base=.6))
    P.add(at(lathe([(3.2, 0), (3.2, 1.2), (0, 1.2)], n=10), (0, 17.9, .2)), S('gold', base=.65))
    for k in range(5):
        a = k * math.tau / 5
        P.add(at(spike(.7, 2.2, sides=5, shoulder=.2), (math.cos(a) * 2.6, 19.0, .2 + math.sin(a) * 2.6)), S('gold', base=.7))
        P.gadd(at(gem(.45, 1.0), (math.cos(a) * 2.6, 21.2, .2 + math.sin(a) * 2.6)), 'gem')
    for k, (x, hh, col) in enumerate(((0, 2.2, 'gold'), (-4.2, 1.5, 'cloud'), (4.2, 1.0, 'dirt'))):
        P.add(at(box((4.0, hh, 3.4), .2), (x, hh / 2 - .2, -4.2)), S('stone', base=.62))
        P.add(at(box((4.1, .3, 3.5), .08), (x, hh - .2, -4.2)), S(col, base=.65, jit=0))
        P.add(at(cyl(.7, .2, sides=12), (x, hh * .45, -5.95), (90, 0, 0)), S(col, base=.75, jit=0))
    return P

def teleport_pad(key='pad'):
    """stepped round platform with inlaid glowing rune circles, two curved stone horns forming an arch with a
    floating crystal at the top, small floating stones"""
    P = Prop('Teleport_%s' % key)
    P.add(lathe([(6.2, -.6), (6.2, .3), (5.6, .5), (5.6, 1.0), (5.0, 1.2), (0, 1.2)], n=36), S('stone', base=.62, up=.22))
    P.add(at(torus(5.65, .2, n=40, sides=5), (0, .75, 0)), S('gold', base=.55))
    P.gadd(at(torus(3.8, .22, n=40, sides=5), (0, 1.22, 0)), key)
    P.gadd(at(torus(2.4, .16, n=36, sides=5), (0, 1.22, 0)), key)
    for k in range(6):
        a = k * math.tau / 6; P.gadd(at(box((.3, .1, 1.2)), (math.cos(a) * 3.1, 1.22, math.sin(a) * 3.1), (0, -math.degrees(a), 0)), key)
    for sx in (-1, 1):
        pts = [Vector((sx * 5.0, 1.0, 0)), Vector((sx * 5.6, 5.0, 0)), Vector((sx * 4.4, 9.0, 0)), Vector((sx * 1.6, 11.2, 0))]
        P.add(tube(pts, [.85, .7, .5, .25], sides=8), S('stone', grad=(1, 11, .55, .75)), smooth=True)
        P.add(at(cyl(.95, .35, sides=8), (sx * 5.3, 3.2, 0)), S('gold', base=.55))
    P.gadd(at(gem(1.0, 2.6), (0, 10.0, 0)), key)
    for k in range(3):
        a = k * math.tau / 3 + .5
        P.add(at(hull(rock_pts((.6, .45, .55), n=10, seed=k)), (math.cos(a) * 3.6, 5.0 + k * 1.2, math.sin(a) * 3.6)), S('stone', base=.6))
    return P
