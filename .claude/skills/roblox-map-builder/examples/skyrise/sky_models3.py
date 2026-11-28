# Skyrise v2 models, part 3: the remaining dressing (mesa, lava pool, charred tree, bush, lamp, signpost).
import math, random
import bmesh
from mathutils import Vector, Matrix
from sky_props import G, Prop, S, at, lathe, sphere, torus, gem, box, cyl, spike, tube, hull, ngon_prism, rock_pts, nz
from sky_models import lumpy

def mesa_rock(seed, r=7.0):
    """sandstone butte: 3 eroded faceted tiers (lumpy hull rings, each narrower), darker banding between tiers,
    scree at the foot, a dry shrub on top"""
    rng = random.Random(seed); P = Prop('Mesa%d' % seed); y = -.6
    for k in range(3):
        rr = r * (1 - k * .24); hh = rng.uniform(2.2, 3.2) * (1.1 - k * .12)
        pts = []
        for i in range(14):
            a = i * math.tau / 14; rad = rr * rng.uniform(.82, 1.05)
            for yy in (y, y + hh):
                pts.append(Vector((math.cos(a) * rad * (1 if yy == y else rng.uniform(.8, .95)), yy + rng.uniform(-.45, .45), math.sin(a) * rad * (1 if yy == y else rng.uniform(.8, .95)))))
        P.add(hull(pts), S('sand' if k != 1 else 'dirt', grad=(y, y + hh, .4, .72), up=.25, jit=.04, seed=k))
        y += hh
    for k in range(9):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(.95, 1.25)
        P.add(at(hull(rock_pts((rng.uniform(.4, 1.0),) * 3, n=9, seed=seed * 11 + k)), (math.cos(a) * d, -.1, math.sin(a) * d)), S('sand', base=.45))
    for k in range(3):
        a = k * 2.1; P.add(at(lumpy(.6, seed + k, 1, .25), (math.cos(a) * r * .25, y + .3, math.sin(a) * r * .25)), S('leaf', base=.35))
    return P

def lava_pool(seed, r=6.0):
    """molten pool: ring of basalt boulders, glowing surface with dark crust plates floating on it, a lava drip"""
    rng = random.Random(seed); P = Prop('LavaPool%d' % seed)
    pts = [(math.cos(a) * r * rng.uniform(.85, 1.05), math.sin(a) * r * rng.uniform(.85, 1.05)) for a in [i * math.tau / 14 for i in range(14)]]
    P.add(ngon_prism(pts, -.6, .2, .2), S('basalt', base=.35))
    P.gadd(ngon_prism([(x * .86, z * .86) for x, z in pts], .15, .38), 'lava')
    for k in range(4):                                                         # crust plates
        a = rng.uniform(0, math.tau); d = r * rng.uniform(.15, .55); pr = rng.uniform(.8, 1.6)
        plate = [(math.cos(b) * pr * rng.uniform(.7, 1.1), math.sin(b) * pr * rng.uniform(.7, 1.1)) for b in [i * math.tau / 6 for i in range(6)]]
        P.add(at(ngon_prism(plate, .32, .52, .08), (math.cos(a) * d, 0, math.sin(a) * d)), S('basalt', base=.3, up=.2))
    for k in range(12):                                                        # rim boulders
        a = k * math.tau / 12 + rng.uniform(-.15, .15); d = r * rng.uniform(.92, 1.08); s = rng.uniform(.8, 1.7)
        P.add(at(hull(rock_pts((s, s * .75, s * .9), n=10, seed=seed * 20 + k)), (math.cos(a) * d, .2, math.sin(a) * d)), S('basalt', grad=(-.5, 1.8, .3, .62), jit=.03))
    return P

def charred_tree(seed, h=10.0):
    """burnt tree: thick twisting trunk with 4 forked branches, glowing ember cracks, ash mound at the foot"""
    rng = random.Random(seed); P = Prop('Charred%d' % seed)
    lean = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * h * .06
    trunk = [Vector((0, -.6, 0)), Vector((0, h * .25, 0)) + lean * .3, Vector((0, h * .55, 0)) + lean, Vector((0, h * .8, 0)) + lean * 1.4]
    P.add(tube(trunk, [h * .1, h * .075, h * .055, h * .03], sides=8, rough=.08, seed=seed), S('basalt', grad=(0, h, .3, .55), jit=.03))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(-.3, .3); y = h * rng.uniform(.4, .75); base = Vector((0, y, 0)) + lean * (y / h) * 1.6
        L = h * rng.uniform(.25, .38); mid = base + Vector((math.cos(a) * L * .55, L * .45, math.sin(a) * L * .55))
        end = mid + Vector((math.cos(a + .5) * L * .45, L * .35, math.sin(a + .5) * L * .45))
        P.add(tube([base, mid, end], [h * .035, h * .022, h * .008], sides=6), S('basalt', base=.4))
        P.add(tube([mid, mid + Vector((math.cos(a - .7) * L * .3, L * .3, math.sin(a - .7) * L * .3))], [h * .016, h * .006], sides=5), S('basalt', base=.4))
    for k in range(3):                                                         # ember cracks running up the trunk
        a = k * math.tau / 3 + .4; r = h * .085
        crack = [Vector((math.cos(a) * r, h * (.05 + .12 * j), math.sin(a) * r)) + Vector((rng.uniform(-.15, .15), 0, rng.uniform(-.15, .15))) for j in range(4)]
        P.gadd(tube(crack, .14, sides=4), 'lava')
    P.add(at(lumpy(h * .2, seed, 1, .2, .35), (0, -.2, 0)), S('basalt', base=.55))
    return P

def bush(seed, col='leaf', r=2.2):
    """lumpy faceted bush: 4-6 clumps, lighter on top, with a few berries or flowers"""
    rng = random.Random(seed); P = Prop('Bush%d_%s' % (seed, col)); clumps = []
    for k in range(rng.randint(4, 6)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(.8, 1.5); rr = r * (1.0 if k == 0 else rng.uniform(.6, .82))
        clumps.append((Vector((math.cos(a) * d, rr * .62, math.sin(a) * d)), rr))
    for i, (c, rr) in enumerate(clumps): P.add(at(lumpy(rr, seed * 7 + i, 2, .13, .85), c), S(col, grad=(0, r * 1.8, .25, .9), up=.1, jit=.02, seed=i))
    bc = ['red', 'pink', 'gold'][seed % 3]
    for k in range(6):
        c, rr = clumps[k % len(clumps)]; a = rng.uniform(0, math.tau); el = rng.uniform(.1, .9)
        p = c + Vector((math.cos(a) * math.cos(el), math.sin(el), math.sin(a) * math.cos(el))) * rr * .95
        P.add(at(sphere(.24, 8, 6), p), S(bc, base=.62, jit=0), smooth=True)
    return P

def lamp_post(seed=1):
    """iron street lantern: stepped stone base, fluted post with collars, curled bracket, caged glowing lantern"""
    P = Prop('SkyLamp')
    P.add(lathe([(1.1, -.4), (1.1, .4), (.8, .6), (.8, 1.0), (.55, 1.2), (0, 1.2)], n=8), S('stone', base=.6))
    P.add(at(lathe([(.32, 0), (.28, 7.6), (.42, 7.8), (.42, 8.2), (0, 8.2)], n=8), (0, 1.2, 0)), S('basalt', grad=(1, 9.5, .45, .7)))
    for y in (2.4, 6.0): P.add(at(cyl(.42, .3, sides=8), (0, y, 0)), S('gold', base=.55))
    curl = [Vector((0, 9.2, 0)), Vector((0, 10.0, -.6)), Vector((0, 10.1, -1.5)), Vector((0, 9.7, -2.1)), Vector((0, 9.2, -2.1))]
    P.add(tube(curl, .14, sides=5), S('basalt', base=.45))
    lz = -2.1
    P.add(at(lathe([(.25, 0), (.85, .3), (.85, .45), (0, .7)], n=6), (0, 9.0, lz)), S('basalt', base=.45))          # cap
    P.gadd(at(lathe([(.5, 0), (.62, .4), (.62, 1.3), (.45, 1.6), (0, 1.6)], n=6), (0, 7.4, lz)), 'lamp')
    for k in range(6):
        a = k * math.tau / 6; P.add(at(box((.1, 1.7, .1)), (math.cos(a) * .66, 8.25, lz + math.sin(a) * .66)), S('basalt', base=.4))
    P.add(at(lathe([(.7, 0), (.7, .2), (0, .25)], n=6), (0, 7.2, lz)), S('basalt', base=.45))
    return P

def signpost(z):
    """zone signpost: planked arrow board with a gold border, the zone gem, a post with a stone footing"""
    P = Prop('Sign%d' % z)
    P.add(lathe([(.9, -.3), (.9, .4), (.6, .6), (0, .6)], n=8), S('stone', base=.6))
    P.add(at(box((.55, 7.0, .55), .1), (0, 3.6, 0)), S('wood', base=.42))

    for k in range(3):                                                         # three planks, arrow tip added below
        P.add(at(box((6.0, .8, .4), .06), (-.2, 4.85 + k * .86, -.4)), S('wood', base=.5 + (k % 2) * .08, jit=.02, seed=k))
    P.add(at(ngon_prism([(2.8, -1.3), (4.0, 0), (2.8, 1.3)], -.2, .2), (0, 5.7, -.4), (90, 0, 0)), S('wood', base=.55))
    border = [Vector((-3.25, 4.4, -.66)), Vector((2.85, 4.4, -.66)), Vector((4.05, 5.7, -.66)), Vector((2.85, 7.0, -.66)), Vector((-3.25, 7.0, -.66)), Vector((-3.25, 4.4, -.66))]
    P.add(tube(border, .12, sides=4), S('gold', base=.55))
    P.gadd(at(gem(.6, 1.4), (-2.2, 5.7, -.72), (90, 0, 0)), 'z%d' % z)
    P.add(at(torus(.75, .14, n=12, sides=4), (-2.2, 5.7, -.7), (90, 0, 0)), S('gold', base=.6))
    for k in range(2): P.add(at(box((3.2 - k, .3, .1)), (.6, 6.0 - k * .6, -.7)), S('cloud', base=.85, jit=0))
    return P
