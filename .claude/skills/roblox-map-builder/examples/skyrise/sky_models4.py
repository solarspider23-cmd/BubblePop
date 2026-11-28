# Skyrise v3 detail pass: ground micro-detail per biome, bridges v2, plaza fountain.
import math, random
import bmesh
from mathutils import Vector, Matrix
from sky_props import G, Prop, S, at, lathe, sphere, torus, gem, box, cyl, spike, tube, hull, ngon_prism, rock_pts, nz
from sky_models import lumpy

# ======================================================================== micro helpers
def blade(base, h, w, lean, yaw):
    """one grass blade: thin tapered wedge (4 verts, 4 tris) leaning outward, tip bent"""
    bm = bmesh.new(); c, s = math.cos(yaw), math.sin(yaw)
    side = Vector((-s, 0, c)) * w / 2; out = Vector((c, 0, s))
    v = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(base - out * w * .4),
         bm.verts.new(base + out * h * lean + Vector((0, h, 0)))]
    for f in ((v[0], v[1], v[3]), (v[1], v[2], v[3]), (v[2], v[0], v[3]), (v[0], v[2], v[1])): bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); return bm

def star(r_out, r_in, n=5):
    return [(math.cos(a) * (r_out if i % 2 == 0 else r_in), math.sin(a) * (r_out if i % 2 == 0 else r_in))
            for i, a in enumerate([k * math.pi / n for k in range(2 * n)])]

# ======================================================================== meadow
def grass_tuft(seed, col='grass', h=1.6, n=9):
    """modelled blade cluster, dark at the root, light at the tips"""
    rng = random.Random(seed); P = Prop('Tuft%d_%s' % (seed, col))
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-.3, .3); d = rng.uniform(0, .45)
        base = Vector((math.cos(a) * d, -.15, math.sin(a) * d)); hh = h * rng.uniform(.6, 1.15)
        P.add(blade(base, hh, rng.uniform(.22, .32), rng.uniform(.25, .55), a), S(col, grad=(-.1, h, .32, .82), jit=.03, seed=k))
    return P

def pebbles(seed, col='stone', n=4):
    rng = random.Random(seed); P = Prop('Pebbles%d_%s' % (seed, col))
    for k in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .9); s = rng.uniform(.22, .5)
        P.add(at(hull(rock_pts((s, s * .55, s * .8), n=7, seed=seed * 9 + k)), (math.cos(a) * d, -.04, math.sin(a) * d)),
              S(col, base=rng.uniform(.45, .7), up=.2, jit=.03))
    return P

def wildflowers(seed, n=4):
    """small flower clump: stems + 5-petal star heads + gold centres, one or two colours"""
    rng = random.Random(seed); P = Prop('Flowers%d' % seed); cols = [('pink', 'violet', 'red', 'cloud')[(seed + k) % 4] for k in range(2)]
    for k in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .6); h = rng.uniform(.7, 1.3)
        x, z = math.cos(a) * d, math.sin(a) * d
        P.add(tube([Vector((x, -.1, z)), Vector((x + rng.uniform(-.1, .1), h, z + rng.uniform(-.1, .1)))], [.06, .04], sides=4), S('leaf', base=.45))
        P.add(at(ngon_prism(star(.32, .14), -.04, .04), (x, h, z), (rng.uniform(-15, 15), rng.uniform(0, 72), rng.uniform(-15, 15))), S(cols[k % 2], base=.62, jit=0))
    P.add(blade(Vector((0, -.1, 0)), .6, .25, .5, rng.uniform(0, 6)), S('leaf', base=.5))
    return P

def mushrooms(seed):
    """two or three toadstools: lathe stems, red caps with white spots"""
    rng = random.Random(seed); P = Prop('Mushrooms%d' % seed)
    for k in range(rng.randint(2, 3)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(.4, .7); s = (1.0 if k == 0 else rng.uniform(.5, .75))
        x, z = math.cos(a) * d, math.sin(a) * d
        P.add(at(lathe([(.16 * s, -.1), (.13 * s, .55 * s), (.18 * s, .62 * s), (0, .64 * s)], n=6), (x, 0, z)), S('cloud', base=.75, jit=0))
        P.add(at(lathe([(.5 * s, .55 * s), (.52 * s, .66 * s), (.38 * s, .86 * s), (0, .94 * s)], n=8), (x, 0, z)), S('red', grad=(.5 * s, .95 * s, .5, .7), jit=0))
        for j in range(3):
            b = j * math.tau / 3 + k
            P.add(at(lathe([(.07 * s, 0), (0, .03)], n=5), (x + math.cos(b) * .3 * s, .79 * s, z + math.sin(b) * .3 * s), (math.cos(b) * 35, 0, -math.sin(b) * 35)), S('cloud', base=.9, jit=0))
    return P

# ======================================================================== dune
def dune_grass(seed):
    return grass_tuft(seed + 50, 'sand', h=2.0, n=8)

def dry_shrub(seed):
    """twiggy desert shrub: forked twigs from a root knot"""
    rng = random.Random(seed); P = Prop('DryShrub%d' % seed)
    P.add(at(lumpy(.35, seed, 1, .2, .7), (0, 0, 0)), S('dirt', base=.4))
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-.2, .2); L = rng.uniform(.9, 1.6)
        p1 = Vector((math.cos(a) * L * .5, L * .7, math.sin(a) * L * .5)); p2 = p1 + Vector((math.cos(a + .6) * L * .4, L * .4, math.sin(a + .6) * L * .4))
        P.add(tube([Vector((0, .1, 0)), p1, p2], [.07, .04, .015], sides=4), S('dirt', base=.55))
        P.add(tube([p1, p1 + Vector((math.cos(a - .7) * L * .3, L * .3, math.sin(a - .7) * L * .3))], [.03, .012], sides=3), S('dirt', base=.55))
    return P

# ======================================================================== frost
def snow_mound(seed):
    rng = random.Random(seed); P = Prop('SnowMound%d' % seed)
    for k in range(rng.randint(2, 3)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(.8, 1.4); r = rng.uniform(.8, 1.4)
        P.add(at(lumpy(r, seed * 5 + k, 1, .14, .45), (math.cos(a) * d, -.15, math.sin(a) * d)), S('snow', grad=(-.4, .7, .6, .95), jit=.02))
    return P

def ice_shards(seed):
    rng = random.Random(seed); P = Prop('IceShards%d' % seed)
    for k in range(3):
        h = rng.uniform(.8, 1.8); a = rng.uniform(0, math.tau); d = rng.uniform(0, .5)
        g = lathe([(0, -.2), (.28, .15 * h), (.24, .7 * h), (0, h)], n=5)
        P.add(at(g, (math.cos(a) * d, 0, math.sin(a) * d), (rng.uniform(-20, 20), rng.uniform(0, 72), rng.uniform(-20, 20))), S('ice', grad=(0, h, .45, .92)))
    return P

# ======================================================================== ember
def ash_pile(seed):
    rng = random.Random(seed); P = Prop('AshPile%d' % seed)
    P.add(at(lumpy(1.1, seed, 1, .18, .35), (0, -.15, 0)), S('basalt', grad=(-.3, .5, .55, .8), jit=.03))
    for k in range(2):
        a = rng.uniform(0, math.tau)
        P.gadd(at(hull(rock_pts((.22, .16, .2), n=7, seed=seed + k)), (math.cos(a) * .55, .2, math.sin(a) * .55)), 'lava')
    return P

def ember_rocks(seed):
    rng = random.Random(seed); P = Prop('EmberRocks%d' % seed)
    for k in range(3):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .8); s = rng.uniform(.35, .7)
        P.add(at(hull(rock_pts((s, s * .6, s * .8), n=8, seed=seed * 3 + k)), (math.cos(a) * d, -.05, math.sin(a) * d)), S('basalt', base=.4, up=.2))
        if k == 0: P.gadd(at(box((.08, .05, s * 1.4)), (math.cos(a) * d, s * .3, math.sin(a) * d), (0, rng.uniform(0, 180), 0)), 'lava')
    return P

# ======================================================================== bridges v2
def bridge(L, rise=0.0, w=9.0, kind='wood', seed=1):
    """bridge from z=0 to z=-L rising by `rise`.
    wood: irregular planks with nail heads, stringers + X braces, posts with caps, sagging rope rails with rope wraps,
          small lanterns on every other post.
    stone: bevelled slabs, kerbs, balusters under a top rail, posts with gold ball caps."""
    rng = random.Random(seed); P = Prop('Bridge_%s_%d_%d' % (kind, round(L), round(rise)))
    pitch = math.degrees(math.atan2(rise, L))
    def at_t(t): return Vector((0, rise * t, -L * t))
    if kind == 'wood':
        t = 0.0
        while t < 1.0:
            seg = rng.uniform(1.1, 1.6) / L; t1 = min(1.0, t + seg); tm = (t + t1) / 2; c = at_t(tm)
            pw = w + rng.uniform(-.4, .3); depth = (t1 - t) * L * .88
            P.add(at(box((pw, .45, depth), .06), (rng.uniform(-.15, .15), c.y - .22, c.z), (pitch + rng.uniform(-1, 1), rng.uniform(-1.5, 1.5), rng.uniform(-.6, .6))),
                  S('wood', base=.48 + rng.uniform(-.09, .09), up=.25, jit=0))
            for sx in (-1, 1): P.add(at(box((.14, .08, .14)), (sx * (w / 2 - .6), c.y + .02, c.z)), S('basalt', base=.3, jit=0))     # nail heads
            t = t1
        for sx in (-1, 1):
            P.add(tube([Vector((sx * (w / 2 - .8), -.9, 1)), Vector((sx * (w / 2 - .8), rise - .9, -L - 1))], .5, sides=6), S('wood', base=.35))
        nb = max(2, int(L / 9))
        for k in range(nb):                                                     # X braces under the deck
            a = at_t(k / nb) + Vector((0, -1.0, 0)); b = at_t((k + 1) / nb) + Vector((0, -1.0, 0))
            P.add(tube([a + Vector((-(w / 2 - .8), 0, 0)), b + Vector((w / 2 - .8, 0, 0))], .22, sides=4), S('wood', base=.32))
            P.add(tube([a + Vector((w / 2 - .8, 0, 0)), b + Vector((-(w / 2 - .8), 0, 0))], .22, sides=4), S('wood', base=.32))
    else:
        n = max(4, int(L / 4.0))
        for k in range(n):
            c = at_t((k + .5) / n)
            P.add(at(box((w, .9, L / n * .96), .15), (0, c.y - .45, c.z), (pitch, 0, 0)), S('stone', base=.55 + (k % 2) * .06, up=.25, jit=0))
        for sx in (-1, 1):
            a = at_t(0); b = at_t(1)
            P.add(tube([a + Vector((sx * (w / 2 - .3), .15, 0)), b + Vector((sx * (w / 2 - .3), .15, 0))], .35, sides=4), S('stone', base=.68))
            P.add(tube([Vector((sx * (w / 2 - .6), -1.1, 1)), Vector((sx * (w / 2 - .6), rise - 1.1, -L - 1))], .55, sides=6), S('stone', base=.4))
    nposts = max(2, int(L / 9)) + 1; tops = {-1: [], 1: []}
    for k in range(nposts):
        t = k / (nposts - 1); c = at_t(t)
        for sx in (-1, 1):
            x = sx * (w / 2 + .1)
            if kind == 'wood':
                P.add(at(box((.75, 4.6, .75), .12), (x, c.y + 1.4, c.z)), S('wood', base=.42))
                P.add(at(lathe([(.55, 0), (.6, .25), (0, .7)], n=4), (x, c.y + 3.7, c.z), (0, 45, 0)), S('wood', base=.6))
                P.add(at(torus(.48, .14, n=10, sides=4), (x, c.y + 2.9, c.z)), S('dirt', base=.65))          # rope wrap
                if k % 2 == 1:                                                                                  # lantern
                    P.add(at(box((.12, .7, .12)), (x + sx * .45, c.y + 3.5, c.z)), S('basalt', base=.3))
                    P.add(at(lathe([(.25, 0), (.32, .1), (.32, .6), (0, .8)], n=6), (x + sx * .45, c.y + 2.55, c.z)), S('basalt', base=.4))
                    P.gadd(at(lathe([(.24, 0), (.24, .45), (0, .45)], n=6), (x + sx * .45, c.y + 2.65, c.z)), 'lamp')
                tops[sx].append(Vector((x, c.y + 2.9, c.z)))
            else:
                P.add(at(box((1.3, 3.8, 1.3), .2), (x, c.y + 1.3, c.z)), S('stone', base=.62))
                P.add(at(box((1.6, .4, 1.6), .1), (x, c.y + 3.2, c.z)), S('stone', base=.72))
                P.add(at(sphere(.65, 10, 6), (x, c.y + 3.9, c.z)), S('gold', base=.62), smooth=True)
                tops[sx].append(Vector((x, c.y + 2.6, c.z)))
    for sx in (-1, 1):
        T = tops[sx]
        for a, b in zip(T, T[1:]):
            if kind == 'wood':
                mid = a.lerp(b, .5) + Vector((0, -.8, 0))
                P.add(tube([a, mid, b], .17, sides=5), S('dirt', base=.65))
                P.add(tube([a + Vector((0, -1.2, 0)), a.lerp(b, .5) + Vector((0, -1.7, 0)), b + Vector((0, -1.2, 0))], .12, sides=4), S('dirt', base=.6))
            else:
                P.add(tube([a + Vector((0, .2, 0)), b + Vector((0, .2, 0))], .32, sides=6), S('stone', base=.72))
                nbal = max(2, int((b - a).length / 2.4))
                for j in range(1, nbal):
                    q = a.lerp(b, j / nbal)
                    P.add(at(lathe([(.3, 0), (.2, .3), (.32, 1.0), (.2, 1.6), (.3, 2.0), (0, 2.05)], n=6), (q.x, q.y - 2.0, q.z)), S('stone', base=.66))
    return P

# ======================================================================== plaza fountain (kept low: spawn looks over it)
def plaza_fountain():
    """low tiered fountain: octagonal stone basin with a lip, water surface, gold trim, a short column with a second
    bowl, glowing water streams falling into the basin, a gem finial"""
    P = Prop('PlazaFountain')
    P.add(lathe([(8.0, -.5), (8.0, 1.4), (8.4, 1.6), (8.4, 1.9), (7.4, 1.9), (7.4, .6), (0, .6)], n=8), S('stone', base=.6, up=.25))
    P.add(at(torus(8.2, .2, n=8, sides=4), (0, 1.25, 0)), S('gold', base=.55))
    P.add(at(lathe([(7.4, 0), (7.4, .12), (0, .12)], n=24), (0, 1.25, 0)), S('ice', base=.62, up=.1, jit=0))
    P.add(lathe([(1.6, .6), (1.3, 1.2), (1.0, 1.4), (1.0, 3.0), (1.4, 3.2), (0, 3.2)], n=12), S('stone', base=.68))
    P.add(at(lathe([(1.2, 0), (3.4, .5), (3.6, .9), (3.3, .9), (1.0, .4), (0, .4)], n=16), (0, 3.0, 0)), S('stone', base=.64, up=.2))
    P.add(at(lathe([(3.3, 0), (3.3, .1), (0, .1)], n=16), (0, 3.75, 0)), S('ice', base=.7, jit=0))
    P.add(at(torus(3.55, .14, n=16, sides=4), (0, 3.9, 0)), S('gold', base=.6))
    P.add(at(lathe([(.5, 0), (.4, .6), (.6, 1.0), (0, 1.1)], n=8), (0, 3.85, 0)), S('stone', base=.72))
    P.gadd(at(gem(.6, 1.4), (0, 4.95, 0)), 'crystal')
    for k in range(16):                                                    # thin water streams spilling over the bowl lip
        a = k * math.tau / 16
        p0 = Vector((math.cos(a) * 3.6, 3.95, math.sin(a) * 3.6)); p1 = Vector((math.cos(a) * 4.05, 3.3, math.sin(a) * 4.05))
        p2 = Vector((math.cos(a) * 4.25, 1.35, math.sin(a) * 4.25))
        P.gadd(tube([p0, p1, p2], [.16, .12, .08], sides=4), 'crystal')
        if k % 2 == 0: P.add(at(lumpy(.42, k, 1, .2, .4), p2), S('cloud', base=.9, jit=0))    # splash foam
    P.gadd(tube([Vector((0, 5.9, 0)), Vector((0, 7.4, 0))], [.22, .06], sides=5), 'crystal')     # central jet
    for k in range(8):                                                     # stone benches round the basin
        a = k * math.tau / 8 + math.tau / 16
        if abs(math.cos(a)) < .5 and math.sin(a) < 0: continue            # keep the north side open
        P.add(at(box((3.0, .5, 1.2), .15), (math.cos(a) * 10.2, .8, math.sin(a) * 10.2), (0, -math.degrees(a) + 90, 0)), S('stone', base=.6))
        for s in (-1, 1):
            q = Vector((math.cos(a), 0, math.sin(a))) * 10.2 + Vector((-math.sin(a), 0, math.cos(a))) * s * 1.1
            P.add(at(box((.5, .7, .9), .1), (q.x, .3, q.z), (0, -math.degrees(a) + 90, 0)), S('stone', base=.5))
    return P
