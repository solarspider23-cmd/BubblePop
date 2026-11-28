# Glowroot Caverns - prop kit part 2: mining kit, stations, hero, falls (star-imports part 1)
from cave_props import *

from mathutils import Vector, Matrix
import math, random, bmesh

def plank(a, b, w=.9, t=.3, bev=.06): return B.bar(a, b, w, t, bev)
def logp(a, b, r=.5, sides=8, r2=None): return tube([Vector(a), Vector(b)], [r, r if r2 is None else r2], sides=sides)
def blob(r, seed, sq=.8, n=14): return hull(rock_pts((r, r * sq, r), n=n, seed=seed))
def W(col='wood', base=.5, seed=0): return FS(col, base, .18, .07, seed)

def oil_lantern(P, c, s=1.0):
    """hanging oil lantern: ring hook, vented cap, 4 cage bars round a GLOWING glass, base dish"""
    c = Vector(c)
    P.add(T(torus(.18 * s, .05 * s, 8, 4), c + Vector((0, .1 * s, 0)), roll=90), FS('iron', .4))
    P.add(T(lathe([(.42 * s, -.35 * s), (.34 * s, -.1 * s), (.12 * s, 0), (0, .05 * s)], n=8), c), FS('iron', .45, .2))
    P.add(T(lathe([(.36 * s, -1.55 * s), (.42 * s, -1.42 * s), (.3 * s, -1.3 * s), (0, -1.3 * s)], n=8), c), FS('iron', .4, .2))
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        P.add(T(box((.07 * s, 1.0 * s, .07 * s)), c + Vector((math.cos(a) * .33 * s, -.82 * s, math.sin(a) * .33 * s))), FS('iron', .35))
    P.gadd(T(lathe([(.22 * s, -1.3 * s), (.28 * s, -.95 * s), (.24 * s, -.55 * s), (.1 * s, -.38 * s)], n=8), c), 'lamp')

def mine_frame(seed=1, hw=10.0, H=16.0):
    """tunnel timber set: two splayed round posts on footing stones, a cap log, knee braces, blocking wedges, a run of
    lagging planks over the cap, iron straps at the joints, a lantern on a chain under the middle. Clear 20 x 15."""
    rng = random.Random(seed); P = Prop('MineFrame')
    for sx in (-1, 1):
        P.add(logp((sx * (hw + .4), -.6, 0), (sx * hw, H, 0), .62, 8, .55), V('wood', 0, H, .35, .6, ns=2, seed=sx))
        P.add(T(blob(1.0, seed + sx, .45), (sx * (hw + .4), -.1, 0)), FS('rock', .4, .3))
        P.add(logp((sx * (hw - .2), H - 4.2, 0), (sx * (hw - 4.2), H - .2, 0), .32, 6), W('wood', .45))
        P.add(T(box((.9, .5, 1.5), .06), (sx * (hw - .1), H - 1.5, 0)), FS('iron', .4))
        for k in range(2):
            P.add(T(box((.18, 1.4, 1.42)), (sx * hw + sx * .55, H - .6 - k * 2.5, 0), roll=sx * 3), FS('iron', .35))
    P.add(logp((-hw - 1.6, H + .55, 0), (hw + 1.6, H + .55, 0), .7, 8), V('wood', H, H + 1, .4, .6, ns=2))
    for k in range(-2, 3):                                                  # lagging planks run along the tunnel
        x = k * 4.4 + rng.uniform(-.1, .1)
        P.add(T(box((3.0, .3, 5.5 + rng.uniform(-.4, .4)), .05), (x, H + 1.4, rng.uniform(-.2, .2)), yaw=rng.uniform(-2, 2)), W('wood', rng.uniform(.4, .58), k))
    for sx in (-1, 1):
        P.add(T(box((1.0, .55, .9), .06), (sx * 3.0, H + 1.05, 0)), W('wooddk', .5))
    for k in range(4):
        P.add(T(torus(.16, .05, 6, 4), (0, H - .1 - k * .34, 0), roll=90 if k % 2 else 0, yaw=90 if k % 2 else 0), FS('iron', .45))
    oil_lantern(P, (0, H - 1.35, 0), 1.1)
    return P

def rail_seg(L=6.0):
    """6-stud track: two I-profile rails on 3 bevelled sleepers with spike heads, on a gravel bed. Rail top y .92"""
    P = Prop('RailSeg'); g = 1.5
    bed = lathe([(2.9, .1), (2.5, .2), (0, .26)], n=8); T(bed, s=(1, 1, L / 5.6))   # low gravel bed laid ON the floor (the map drapes it)
    bmesh.ops.delete(bed, geom=[f for f in bed.faces if f.calc_center_median().y < .105], context='FACES_ONLY')   # no bottom cap
    P.add(bed, FS('floor', .32, .1, .04))
    for k, z in enumerate((-L / 3, 0, L / 3)):
        P.add(T(box((4.4, .34, .78), .07), (0, .32, z), yaw=(k - 1) * 1.5), W('wooddk', .5 + k * .04, k))
    for sx in (-1, 1):
        P.add(T(box((.52, .1, L)), (sx * g, .53, 0)), FS('iron', .3))
        P.add(T(box((.13, .32, L)), (sx * g, .74, 0)), FS('iron', .35))
        P.add(T(box((.32, .2, L), .04), (sx * g, .91, 0)), FS('iron', .72, .15))
    return P

def rail_buffer():
    """end-of-track stop: two posts with back struts, a cross beam with iron bumper pads, a red signal lamp"""
    P = Prop('RailBuffer')
    for sx in (-1, 1):
        P.add(T(box((.8, 3.4, .8), .1), (sx * 1.9, 1.3, .6)), W('wood', .5, sx))
        P.add(logp((sx * 1.9, 2.2, .6), (sx * 1.9, -.4, 3.6), .32, 6), W('wood', .45))
        P.add(T(cyl(.38, .5, 8, .06), (sx * 1.5, 1.6, -.1), pitch=90), FS('iron', .45))
    P.add(T(box((5.0, 1.0, .9), .1), (0, 2.6, .6)), FS('red', .5, .2))
    P.add(T(box((5.2, .14, 1.0)), (0, 3.18, .6)), FS('iron', .4))
    P.add(T(box((.25, 1.8, .25)), (0, 4.0, .6)), FS('iron', .35))
    P.gadd(T(lathe([(.3, 0), (.36, .3), (.2, .55), (0, .6)], n=8), (0, 4.9, .6)), 'lamp')
    P.add(T(lathe([(.42, -.05), (.42, .05)], n=8), (0, 4.9, .6)), FS('iron', .4))
    return P

def wheel(P, c, r=.62, w=.3):
    c = Vector(c); inner = Vector((-.12 if c.x > 0 else .12, 0, 0))
    P.add(T(cyl(r, w, 10, .05, y0=-w / 2), c, roll=90), FS('iron', .42, .1, .03))
    P.add(T(cyl(r * 1.13, .08, 10, y0=-.04), c + inner * 1.6, roll=90), FS('iron', .3, .1, .03))
    P.add(T(cyl(r * .3, w + .1, 6, y0=-(w + .1) / 2), c, roll=90), FS('iron', .6, .1, .03))

def mine_cart(load='amber', name=None):
    """riveted tub on a timber chassis, 4 flanged wheels on axles, couplers, rolled rim, strap bands; heaped with ore
    lumps and glowing crystal chunks. Origin = wheel bottoms (place on the rail top)."""
    P = Prop(name or 'MineCart%s' % load.capitalize()); rng = random.Random(len(load))
    tub = box((3.4, 2.3, 4.6), .25)
    for v in tub.verts:
        if v.co.y > 0: v.co.x *= 1.16; v.co.z *= 1.1
    T(tub, (0, 2.45, 0)); P.add(tub, V('red', 1.3, 3.6, .35, .62, nk=.05))
    rim = [Vector((x, 3.62, z)) for x, z in ((-1.98, -2.53), (1.98, -2.53), (1.98, 2.53), (-1.98, 2.53), (-1.98, -2.53))]
    P.add(tube(rim, .13, 6, cap0=False, cap1=False), FS('iron', .5))
    for z in (-1.3, 1.3):
        b = box((3.5, 2.36, .22))
        for v in b.verts:
            if v.co.y > 0: v.co.x *= 1.16
        P.add(T(b, (0, 2.45, z)), FS('iron', .4))
        for y in (1.7, 2.5, 3.3):
            for sx in (-1, 1): P.add(T(box((.14, .14, .14)), (sx * (1.74 + (y - 1.3) * .12), y, z - .14)), FS('iron', .7))
    for sx in (-.9, .9): P.add(T(box((.5, .45, 5.0), .06), (sx, 1.18, 0)), W('wooddk', .5))
    for z in (-1.55, 1.55):
        P.add(logp((-1.75, .62, z), (1.75, .62, z), .11, 6), FS('iron', .4))
        for sx in (-1, 1): wheel(P, (sx * 1.5, .62, z))
    for z in (-1, 1):
        P.add(T(box((.3, .3, .9)), (0, 1.2, z * 2.8)), FS('iron', .4)); P.add(T(torus(.24, .07, 8, 4), (0, 1.2, z * 3.35), pitch=90), FS('iron', .5))
    cart_load(P, load, rng)
    return P

def cart_load(P, load, rng):
    """ore heaped in the tub (cave_ores replaces this with the v2 load)"""
    for k in range(9):                                                      # ore heap
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.0)
        P.add(T(blob(rng.uniform(.6, .9), k, .7), (math.cos(a) * d * 1.1, 3.5 + rng.uniform(0, .35), math.sin(a) * d * 1.5)), FS('rock', .45, .3, .1, k))
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.0)
        add_crystal(P, (math.cos(a) * d, 3.7, math.sin(a) * d * 1.4), rng.uniform(.3, .45), rng.uniform(1.2, 2.0), k + 3, load, lean=rng.uniform(15, 50), yaw=rng.uniform(0, 360), glow_from=.2)

def mine_lantern_post(seed=1):
    """square chamfered post on a cairn footing, crossarm with angle brace, hanging lantern"""
    P = Prop('MineLantern')
    for k in range(5):
        a = k * math.tau / 5; P.add(T(blob(.6, seed + k, .6), (math.cos(a) * .9, .1, math.sin(a) * .9)), FS('rock', .42, .3, .08, k))
    P.add(T(box((.55, 8.0, .55), .1), (0, 3.6, 0)), V('wood', 0, 8, .38, .6))
    P.add(T(box((2.6, .45, .45), .08), (.9, 7.3, 0)), W('wood', .5))
    P.add(logp((.15, 5.7, 0), (1.6, 7.1, 0), .14, 5), W('wood', .45))
    P.add(T(box((.62, .3, .62), .05), (0, 7.7, 0)), FS('iron', .4))
    for k in range(2): P.add(T(torus(.13, .04, 6, 4), (1.9, 7.0 - k * .26, 0), roll=90 if k % 2 else 0), FS('iron', .45))
    oil_lantern(P, (1.9, 6.6, 0), 1.0)
    return P

def scaffold(seed=1):
    """3-storey mining scaffold against a wall (back = +Z): round posts, plank decks with gaps, beams, X braces on the
    back and sides, ladders between decks, railings on the front, a pulley arm with rope + bucket, crates on decks."""
    rng = random.Random(seed); P = Prop('Scaffold')
    X = (-8, 0, 8); Z = (-5, 5); levels = (9.0, 18.0, 27.0)
    for x in X:
        for z in Z: P.add(logp((x, -.6, z), (x, 29.5, z), .5, 7), V('wood', 0, 30, .35, .6, ns=3, seed=x + z))
    for y in levels:
        for z in Z: P.add(T(box((17.4, .55, .55), .06), (0, y - .45, z)), W('wood', .45))
        for x in X: P.add(T(box((.55, .55, 11), .06), (x, y - .45, 0)), W('wood', .45))
        x = -8.2
        while x < 8.2:
            w = rng.uniform(1.4, 1.7); P.add(T(box((w, .3, 11.4), .05), (x + w / 2, y, rng.uniform(-.15, .15)), yaw=rng.uniform(-.8, .8)), W('wood', rng.uniform(.42, .6), int(x * 7)))
            x += w + .14
        for x in X: P.add(T(box((.35, 3.4, .35), .05), (x, y + 1.9, -5.0)), W('wood', .5))
        P.add(T(box((17, .3, .3), .04), (0, y + 3.4, -5.0)), W('wood', .55)); P.add(T(box((17, .25, .25), .04), (0, y + 1.8, -5.0)), W('wood', .5))
    for y0, y1 in ((0, 9), (9, 18), (18, 27)):                                # X braces back + sides
        for x0, x1 in ((-8, 0), (0, 8)):
            P.add(logp((x0, y0 + .4, 5.25), (x1, y1 - .6, 5.25), .2, 5), W('wooddk', .45)); P.add(logp((x1, y0 + .4, 5.25), (x0, y1 - .6, 5.25), .2, 5), W('wooddk', .45))
        for x in (-8.25, 8.25):
            P.add(logp((x, y0 + .4, -5), (x, y1 - .6, 5), .2, 5), W('wooddk', .45))
    for k, (x, y0) in enumerate(((5.0, 0), (-5.0, 9), (5.0, 18))):            # ladders
        for sx in (-.5, .5): P.add(T(box((.18, 10.4, .2)), (x + sx, y0 + 5.0, -4.2), pitch=-8), W('wood', .5))
        for r in range(12):
            yy = y0 + .6 + r * .82; P.add(T(box((1.0, .12, .14)), (x, yy, -4.2 - math.sin(math.radians(8)) * (yy - y0 - 5))), W('wood', .6))
    P.add(logp((-6, 29.0, -1), (-6, 29.0, -9.5), .4, 7), W('wood', .5))       # pulley arm
    P.add(T(torus(.65, .14, 10, 5), (-6, 28.4, -9.0), roll=90), FS('iron', .45))
    P.add(logp((-6, 27.8, -9.6), (-6, 4.5, -9.6), .07, 4), FS('canvas', .5))
    P.add(T(lathe([(.55, 0), (.75, 1.3), (.8, 1.4), (0, .05)], n=8), (-6, 3.3, -9.6)), W('wood', .45))
    P.add(T(torus(.78, .07, 8, 4), (-6, 4.7, -9.6)), FS('iron', .5))
    for k, (x, y, z) in enumerate(((3.5, 9.15, 2.5), (-4, 18.15, 3), (-2.5, 27.15, 2.6))):
        P.add(T(box((2.2, 2.0, 2.2), .12), (x, y + 1.0, z), yaw=rng.uniform(-20, 20)), W('wood', .5, k))
    oil_lantern(P, (0, 26.0, -5.0), 1.0); oil_lantern(P, (-7.5, 17.0, -5.2), .9)
    return P

def rope_bridge(L=34.0, drop=1.8):
    """chasm rope bridge (span along Z): end post pairs with rope wraps and stakes, irregular planks along a sag,
    rope stringers under the plank ends, sagging hand ropes, vertical suspenders every other plank"""
    rng = random.Random(7); P = Prop('RopeBridge'); n = 30
    def yat(z): return -drop * (1 - (2 * z / L) ** 2)
    def hy(z): return 4.2 + yat(z) * .6 - 1.0 * (1 - (2 * z / L) ** 2)
    for sz in (-1, 1):
        for sx in (-1, 1):
            b = Vector((sx * 2.8, 0, sz * (L / 2 + 1.2)))
            P.add(logp(b + Vector((0, -1.8, 0)), b + Vector((0, 4.6, 0)), .45, 8), V('wood', 0, 4.6, .35, .6))
            for k in range(3): P.add(T(torus(.5, .09, 8, 4), b + Vector((0, 3.4 + k * .25, 0))), FS('canvas', .5))
            P.add(logp(b + Vector((0, 4.4, 0)), b + Vector((0, .2, sz * 3.2)), .08, 4), FS('canvas', .45))
            P.add(T(box((.4, 1.2, .4), .05), b + Vector((0, -.1, sz * 3.3)), pitch=sz * 15), W('wooddk', .45))
    for i in range(n):
        z = -L / 2 + (i + .5) * L / n; y = yat(z); slope = math.degrees(math.atan2(yat(z + .5) - yat(z - .5), 1))
        P.add(T(box((5.2 + rng.uniform(-.3, .2), .28, L / n * .82), .06), (rng.uniform(-.1, .1), y, z), yaw=rng.uniform(-3, 3), pitch=-slope), W('wood', rng.uniform(.4, .6), i))
    zs = [-L / 2 - 1.2 + k * (L + 2.4) / 16 for k in range(17)]
    for sx in (-1, 1):
        P.add(tube([Vector((sx * 2.5, yat(z) - .2, z)) for z in zs], .1, 5), FS('canvas', .45))
        P.add(tube([Vector((sx * 2.8, hy(z), z)) for z in zs], .12, 5), FS('canvas', .55))
        for i in range(0, n, 2):
            z = -L / 2 + (i + .5) * L / n
            P.add(tube([Vector((sx * 2.6, yat(z), z)), Vector((sx * 2.75, hy(z), z))], .05, 4), FS('canvas', .45))
    return P

def plank_bridge(L=18.0):
    """low boardwalk to the islet (span along Z): log piles with iron bands, stringers, plank deck, log hand rails"""
    rng = random.Random(3); P = Prop('PlankBridge'); y = 1.2
    for k in range(5):
        z = -L / 2 + k * L / 4
        for sx in (-1, 1):
            P.add(logp((sx * 2.6, -5, z), (sx * 2.6, 3.8, z), .38, 7), V('wood', -5, 4, .25, .55))
            P.add(T(torus(.42, .08, 8, 4), (sx * 2.6, 1.0, z)), FS('iron', .4))
    for sx in (-1.6, 1.6): P.add(T(box((.5, .5, L + 1), .05), (sx, y - .45, 0)), W('wooddk', .45))
    z = -L / 2 - .5
    while z < L / 2 + .5:
        w = rng.uniform(.8, 1.0); P.add(T(box((5.6, .26, w), .05), (rng.uniform(-.12, .12), y, z + w / 2), yaw=rng.uniform(-1.5, 1.5)), W('wood', rng.uniform(.42, .6), int(z * 9)))
        z += w + .1
    for sx in (-1, 1): P.add(logp((sx * 2.6, 3.4, -L / 2 - .3), (sx * 2.6, 3.4, L / 2 + .3), .2, 6), W('wood', .55))
    return P

def crates(seed=1):
    """stack of 3 braced crates (frame battens + diagonal brace on the faces) with a pickaxe leaning on it"""
    P = Prop('Crates%d' % seed)
    def crate(c, s, yaw):
        c = Vector(c); P.add(T(box((s, s, s), .08), c, yaw=yaw), W('wood', .5, int(s * 10)))
        M = Matrix.Rotation(math.radians(yaw), 3, 'Y')
        for f in range(4):
            a = f * math.pi / 2; n = Vector((math.sin(a), 0, -math.cos(a)))
            o = c + M @ (n * (s / 2 + .04)); fy = yaw - math.degrees(a)
            for sy in (-1, 1): P.add(T(box((s, .22, .1)), o + Vector((0, sy * (s / 2 - .11), 0)), yaw=fy), W('wooddk', .45))
            P.add(T(box((s * 1.2, .2, .1)), o, yaw=fy, roll=45), W('wooddk', .4))
    crate((0, 1.2, 0), 2.4, 4); crate((2.3, 1.0, .4), 2.0, -12); crate((.8, 3.3, .1), 1.8, 25)
    P.add(logp((-1.5, -.1, -1.9), (-1.65, 3.1, -1.35), .1, 5), W('wood', .6))
    P.add(hull([Vector(p) for p in ((-2.6, 3.0, -1.4), (-.7, 3.0, -1.3), (-2.6, 3.22, -1.4), (-.7, 3.22, -1.3), (-1.65, 3.4, -1.35), (-1.65, 2.85, -1.35))]), FS('iron', .5, .2))
    return P

def barrels(seed=2):
    """three staved barrels (bulged lathe, iron hoops, lid), one lying on its side"""
    P = Prop('Barrels%d' % seed)
    def barrel(c, pitch=0.0, yaw=0.0):
        b = lathe([(1.0, 0), (1.18, 1.0), (1.22, 1.6), (1.18, 2.2), (1.0, 3.2), (.92, 3.2), (.92, 3.05), (0, 3.05)], n=12)
        T(b, (0, -1.6, 0)); T(b, c, yaw=yaw, pitch=pitch); P.add(b, V('wood', -2, 4, .35, .6))
        for y in (.35, 1.0, 2.2, 2.85):
            r = 1.0 + .22 * math.sin(math.pi * y / 3.2); h = torus(r + .03, .06, 12, 4); T(h, (0, y - 1.6, 0)); T(h, c, yaw=yaw, pitch=pitch); P.add(h, FS('iron', .45))
    barrel((0, 1.6, 0)); barrel((2.3, 1.6, .6), yaw=40); barrel((1.0, 1.2, -2.6), pitch=90, yaw=70)
    return P

def ore_pile(kind='amber', seed=3):
    """heap of broken ore with glowing crystal chunks and a shovel stuck in it"""
    rng = random.Random(seed); P = Prop('OrePile%s' % kind.capitalize())
    for k in range(16):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.6); h = (2.8 - d) * .7
        P.add(T(blob(rng.uniform(.5, 1.0), seed * 9 + k, .7), (math.cos(a) * d, max(.1, h * rng.uniform(.5, 1)), math.sin(a) * d)), FS('rock', .44, .3, .1, k))
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(.3, 2.2)
        add_crystal(P, (math.cos(a) * d, (2.8 - d) * .55, math.sin(a) * d), rng.uniform(.3, .5), rng.uniform(1.2, 2.4), seed * 5 + k, kind, lean=rng.uniform(20, 60), yaw=rng.uniform(0, 360), glow_from=.2)
    P.add(logp((.4, 1.2, .3), (1.6, 5.2, 1.0), .11, 6), W('wood', .6))
    P.add(T(box((.9, 1.2, .1), .05), (.15, .6, .15), roll=-16, yaw=30), FS('iron', .5))
    return P

def tool_rack():
    """timber rack with hung pickaxes and shovels, a coil of rope and a lantern"""
    P = Prop('ToolRack')
    for sx in (-1, 1): P.add(T(box((.45, 6.5, .45), .06), (sx * 3, 2.9, 0)), W('wood', .5))
    for y in (2.0, 5.0): P.add(T(box((6.6, .4, .35), .05), (0, y, 0)), W('wood', .45))
    for k, x in enumerate((-2.0, -.7, .7, 2.0)):
        P.add(logp((x, 5.3, -.3), (x + .2, 1.2, -.4), .1, 5), W('wood', .62))
        if k % 2 == 0: P.add(tube([Vector((x - 1.2, 4.8, -.32)), Vector((x - .5, 5.45, -.32)), Vector((x, 5.6, -.32)), Vector((x + .5, 5.45, -.32)), Vector((x + 1.2, 4.8, -.32))], [.04, .13, .17, .13, .04], sides=6), FS('iron', .5))
        else: P.add(T(box((.9, 1.2, .1), .05), (x + .2, .9, -.45)), FS('iron', .5))
    P.add(T(torus(.7, .18, 12, 5), (2.9, 4.0, -.6), pitch=90), FS('canvas', .5))
    oil_lantern(P, (-3.0, 6.0, -.5), .9)
    return P
