# Maple Junction street furniture, trees, alley clutter. Same conventions as town_props (origin bottom centre, front -Z).
import math, random
import bmesh
from town_props import *          # noqa: F401,F403  (Prop, S, add, slab, blob, ball, T, bar, lathe, torus, tube, cyl, box, V3 ...)
from town_props import ac_unit, flower

def street_lamp(seed=1):
    """town lantern post: two-step octagonal plinth, tapered shaft with collars, scroll bracket holding a planted
    hanging basket, 4-sided lantern (iron frame, glowing glass, crown roof, finial)"""
    P = Prop('StreetLamp')
    add(P, cyl(.95, .9, sides=8, y0=-.5), 'metal', .32)
    add(P, cyl(.75, .6, sides=8, y0=.4, r2=.6), 'metal', .38)
    add(P, cyl(.32, 10.2, sides=8, y0=1.0, r2=.22), 'metal', .42, smooth=True)
    for y in (1.2, 10.6): add(P, cyl(.42, .35, sides=8, y0=y), 'metal', .5)
    arm = [V3((0, 9.2, 0)), V3((.9, 9.5, 0)), V3((1.8, 9.4, 0)), V3((2.3, 9.0, 0))]
    add(P, tube(arm, .08, sides=4), 'metal', .45)
    add(P, tube([V3((2.3, 9.0, 0)), V3((2.3, 8.1, 0))], .04, sides=3), 'metal', .5)
    add(P, T(cyl(.75, .6, sides=8, r2=.95), (2.3, 7.5, 0)), 'metal', .35)
    add(P, T(blob(.75, seed, n=10, sq=.7), (2.3, 8.2, 0)), 'leaf', .55)
    for k in range(3):
        a = k * math.tau / 3
        flower(P, (2.3 + math.cos(a) * .55, 8.55, math.sin(a) * .55), ('red', 'yellow', 'red')[k], .34, n=(math.cos(a), 1, math.sin(a)))
    add(P, cyl(.5, .4, sides=4, y0=11.0, r2=.75, rot0=math.pi / 4), 'metal', .4)
    P.gadd(cyl(.62, 1.9, sides=4, y0=11.4, r2=.82, rot0=math.pi / 4), 'lamp')
    for k in range(4):
        a = math.pi / 4 + k * math.tau / 4
        add(P, bar((math.cos(a) * .64, 11.4, math.sin(a) * .64), (math.cos(a) * .86, 13.3, math.sin(a) * .86), .1, .1, 0), 'metal', .38)
    add(P, cyl(1.15, .25, sides=4, y0=13.3, rot0=math.pi / 4), 'metal', .45)
    add(P, cyl(1.0, .9, sides=4, y0=13.55, r2=.2, rot0=math.pi / 4), 'metal', .4)
    add(P, T(ball(.18, 6, 4), (0, 14.6, 0)), 'yellow', .7)
    return P

def _hood(x, y, z, r=.62, L=.85):
    hood = bmesh.new(); pts = [(math.cos(math.pi * a / 6) * r, math.sin(math.pi * a / 6) * r) for a in range(7)]
    Fv = [hood.verts.new((x + px, y + py, z)) for px, py in pts]; Bv = [hood.verts.new((x + px, y + py, z - L)) for px, py in pts]
    for i in range(6): hood.faces.new((Fv[i], Fv[i + 1], Bv[i + 1], Bv[i]))
    hood.normal_update()
    for f in hood.faces:
        c = f.calc_center_median()
        if f.normal.dot(V3((c.x - x, c.y - y, 0))) < 0: f.normal_flip()
    return hood

def traffic_light(seed=1, lit='red'):
    """mast-arm signal: base + yellow pole, arm over the road along +X, two 3-lens heads facing -Z with hoods and
    back plates, pedestrian signal (faces +Z) + push button on the pole"""
    P = Prop('TrafficLight_%s' % lit)
    add(P, cyl(.8, .7, sides=10, y0=-.4), 'metal', .3)
    add(P, cyl(.38, 15.6, sides=10, y0=.3, r2=.3), 'yellow', .45, smooth=True)
    add(P, cyl(.5, .5, sides=10, y0=.3), 'yellow', .4)
    arm = [V3((0, 14.4, 0)), V3((5, 14.9, 0)), V3((10, 15.1, 0)), V3((13.6, 15.1, 0))]
    add(P, tube(arm, [.24, .2, .17, .15], sides=8), 'yellow', .5, smooth=True)
    add(P, bar((0, 12.0, 0), (4.0, 14.75, 0), .12, .12, 0), 'yellow', .45)
    add(P, T(ball(.42, 8, 5), (0, 15.9, 0)), 'yellow', .55)
    def head(x, y, z):
        add(P, T(box((1.5, 4.4, 1.3), .1), (x, y, z)), 'metal', .3)
        add(P, T(box((2.4, 5.2, .12)), (x, y, z + .7)), 'metal', .22)
        for key, yy in (('sigred', 1.35), ('sigamber', 0), ('siggreen', -1.35)):
            lens = T(cyl(.52, .1, sides=10), (x, y + yy, z - .7), 0, 90)
            if (lit == 'red' and key == 'sigred') or (lit == 'green' and key == 'siggreen'): P.gadd(lens, key)
            else: add(P, lens, {'sigred': 'red', 'sigamber': 'yellow', 'siggreen': 'teal'}[key], .16, up=0)
            add(P, _hood(x, y + yy, z - .72), 'metal', .3, up=0)
    head(12.6, 12.5, 0)
    add(P, bar((12.6, 15.0, 0), (12.6, 14.7, 0), .2, .2, 0), 'metal', .3)
    head(0, 9.6, -.95)
    add(P, T(box((1.4, 1.6, 1.2), .08), (0, 6.8, .9)), 'metal', .3)
    P.gadd(T(box((1.0, 1.0, .1)), (0, 6.8, 1.52)), 'walk')
    add(P, T(box((.8, 1.2, .5), .06), (.45, 3.6, -.3)), 'yellow', .65)
    add(P, T(cyl(.22, .14, sides=8), (.45, 3.6, -.6), 0, 90), 'metal', .7)
    return P

def bench(seed=1):
    """park bench: cast-iron scroll ends (profile prism), 4 seat slats + 3 back slats, armrests"""
    P = Prop('Bench'); L = 6.0
    end = [(-.9, 0), (-.7, 1.7), (-1.05, 1.75), (-1.15, 1.9), (.95, 1.9), (1.0, 1.75), (.75, 1.6), (1.15, 3.9), (1.35, 4.1), (1.2, 4.2), (.9, 3.95), (.45, 1.7), (.75, 0)]
    for sx in (-1, 1):
        x = sx * (L / 2 - .4)
        bm = bmesh.new()
        Fv = [bm.verts.new((x - .14, py - .3, pz)) for pz, py in end]; Bv = [bm.verts.new((x + .14, py - .3, pz)) for pz, py in end]
        bm.faces.new(Fv); bm.faces.new(Bv[::-1])
        for i in range(len(end)): j = (i + 1) % len(end); bm.faces.new((Fv[i], Fv[j], Bv[j], Bv[i]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        add(P, bm, 'metal', .35, up=.1)
        add(P, T(box((.5, .2, 1.8)), (x, 2.75, -.4)), 'wood', .55)
        add(P, bar((x, 2.75, .45), (x, 1.6, .2), .14, .14, 0), 'metal', .4)
    for k in range(4): add(P, T(box((L, .22, .55)), (0, 1.75, -.85 + k * .6)), 'wood', .58 + k * .02)
    for k in range(3):
        t = .8 + k * .65; add(P, T(box((L, .5, .2)), (0, 1.7 + t * .95, 1.15 + t * .2), 0, -12), 'wood', .62)
    return P

def planter(seed=1, w=5.0):
    """stone planter box: plinth, panelled body, coping, soil, layered shrub + flowers"""
    P = Prop('Planter%d' % seed); rng = random.Random(seed)
    add(P, slab(-w / 2 - .2, w / 2 + .2, -.4, .3, -w / 2 - .2, w / 2 + .2), 'cream', .5)
    add(P, slab(-w / 2, w / 2, .3, 2.2, -w / 2, w / 2), 'cream', .66)
    for sx in (-1, 1):
        add(P, slab(-w / 2 + .5, w / 2 - .5, .7, 1.8, sx * w / 2 - .05, sx * w / 2 + .05), 'cream', .52, up=0)
        add(P, slab(sx * w / 2 - .05, sx * w / 2 + .05, .7, 1.8, -w / 2 + .5, w / 2 - .5), 'cream', .52, up=0)
    add(P, slab(-w / 2 - .3, w / 2 + .3, 2.2, 2.6, -w / 2 - .3, w / 2 + .3), 'cream', .84)
    add(P, slab(-w / 2 + .3, w / 2 - .3, 2.4, 2.5, -w / 2 + .3, w / 2 - .3), 'wood', .2)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(0, .5); r = w * .22
        add(P, T(blob(w * .3, seed * 7 + k, n=12), (math.cos(a) * r, 3.4, math.sin(a) * r)), 'leaf', .5, smooth=True)
    add(P, T(blob(w * .36, seed + 40, n=16), (0, 4.4, 0)), 'leaf', .62, smooth=True)
    for k in range(8):
        a = k * math.tau / 8 + .3; r = w * .42
        dvec = V3((math.cos(a), .9 - (k % 2) * .5, math.sin(a))).normalized(); c0 = V3((0, 4.4, 0))
        flower(P, tuple(c0 + dvec * w * .33), ('red', 'yellow', 'blue')[(k + seed) % 3], .6, n=tuple(dvec))
    return P

def litter_bin(seed=1):
    """municipal bin: base, ribbed teal body, yellow band, dome lid with a dark mouth"""
    P = Prop('Bin')
    add(P, cyl(1.2, .4, sides=12, y0=-.3), 'metal', .3)
    add(P, cyl(1.1, 3.2, sides=12, y0=.1), 'teal', .32, smooth=True)
    for k in range(12):
        a = k * math.tau / 12
        add(P, T(box((.22, 2.0, .2)), (math.cos(a) * 1.12, 1.2, math.sin(a) * 1.12), math.degrees(-a)), 'teal', .45)
    add(P, cyl(1.24, .35, sides=12, y0=2.4), 'yellow', .6)
    add(P, lathe([(1.2, 3.3), (1.15, 3.6), (.9, 4.1), (.4, 4.35), (0, 4.4)], n=12), 'teal', .45, smooth=True)
    add(P, T(box((1.1, .55, .4)), (0, 3.65, -1.0)), 'metal', .1)
    return P

def hydrant(seed=1):
    """fire hydrant: lathed red body, bonnet + yellow nut, 3 hose outlets with yellow caps, collar"""
    P = Prop('Hydrant')
    add(P, cyl(.8, .4, sides=10, y0=-.3), 'red', .35)
    add(P, lathe([(.62, .1), (.55, .4), (.5, 2.0), (.62, 2.1), (.62, 2.3), (.5, 2.4), (.45, 2.8), (.2, 3.05), (0, 3.1)], n=10), 'red', .55, smooth=True)
    add(P, cyl(.16, .25, sides=6, y0=3.05), 'yellow', .6)
    for a in (0, 180, 90):
        add(P, T(T(cyl(.24, .5, sides=8), (0, 0, 0), 0, 90), (0, 1.5, 0), a), 'red', .6)
        add(P, T(T(cyl(.22, .16, sides=6, y0=.5), (0, 0, 0), 0, 90), (0, 1.5, 0), a), 'yellow', .65)
    add(P, cyl(.65, .12, sides=10, y0=1.95), 'yellow', .7)
    return P

def dumpster(seed=1, col='teal'):
    """commercial dumpster: tapered body, rim, two lids (one propped open on a trash bag), fork pockets, casters, ribs"""
    P = Prop('Dumpster_%s' % col)
    W, D, Hh = 7.0, 4.4, 4.2
    bm = bmesh.new()
    lo = [(-W / 2 + .3, .5, -D / 2 + .5), (W / 2 - .3, .5, -D / 2 + .5), (W / 2 - .3, .5, D / 2), (-W / 2 + .3, .5, D / 2)]
    hi = [(-W / 2, Hh, -D / 2), (W / 2, Hh, -D / 2), (W / 2, Hh, D / 2), (-W / 2, Hh, D / 2)]
    A = [bm.verts.new(p) for p in lo]; Bq = [bm.verts.new(p) for p in hi]
    bm.faces.new(A[::-1]); bm.faces.new(Bq)
    for k in range(4): j = (k + 1) % 4; bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, col, .45, up=.1)
    add(P, slab(-W / 2 - .15, W / 2 + .15, Hh - .3, Hh, -D / 2 - .15, D / 2 + .15), col, .6)
    for sx in (-1, 1):
        add(P, slab(sx * W / 2 - .6, sx * W / 2 + .6, 1.6, 2.4, -D / 2 - .2, D / 2 + .2), 'metal', .35)
        for sz in (-1, 1):
            add(P, T(cyl(.35, .3, sides=8), (sx * (W / 2 - .7), .35, sz * (D / 2 - .7)), 0, 90), 'metal', .2)
            add(P, slab(sx * (W / 2 - .7) - .3, sx * (W / 2 - .7) + .3, .55, .7, sz * (D / 2 - .7) - .3, sz * (D / 2 - .7) + .3), 'metal', .4)
    add(P, T(box((W / 2 - .1, .25, D + .2), .05), (-W / 4, Hh + .15, 0)), 'metal', .28)
    add(P, T(T(box((W / 2 - .1, .25, D + .2), .05), (0, 0, D / 2)), (W / 4, Hh + .1, -D / 2), 0, -18), 'metal', .28)
    add(P, T(blob(1.0, seed + 4, n=10, sq=.9), (W / 4, Hh + .2, 0)), 'metal', .12)
    for k in range(3): add(P, slab(-W / 2 + 1.2 + k * 2.2, -W / 2 + 1.5 + k * 2.2, 1.0, Hh - .5, -D / 2 - .05, -D / 2 + .3), col, .38, up=0)
    return P

def trash_bags(seed=1):
    """heap of bin bags + two cardboard boxes"""
    P = Prop('TrashBags'); rng = random.Random(seed)
    for k in range(4):
        x, z = rng.uniform(-1.4, 1.4), rng.uniform(-1, 1)
        add(P, T(blob(rng.uniform(.8, 1.1), seed * 5 + k, n=12, sq=.85), (x, .6, z)), 'metal', .15 + .05 * k, smooth=True)
        add(P, T(blob(.25, k, n=6), (x, 1.5, z)), 'metal', .2)
    add(P, T(box((1.6, 1.4, 1.6)), (1.8, .7, .8), 18), 'wood', .6)
    add(P, T(box((1.4, 1.2, 1.4)), (1.9, 2.0, .7), 36), 'wood', .7)
    return P

def pallets(seed=1):
    """3 stacked shipping pallets (deck boards over stringers) + a box on top"""
    P = Prop('Pallets')
    for k in range(3):
        y = k * .65
        for i in range(5): add(P, slab(-2, 2, y + .4, y + .55, -2 + i * .95, -1.6 + i * .95), 'wood', .55 + .04 * (i % 2))
        for sx in (-1, 0, 1): add(P, slab(sx * 1.7 - .25, sx * 1.7 + .25, y, y + .4, -2, 2), 'wood', .42)
    add(P, T(box((2.2, 2.0, 2.2)), (.3, 2.95, .2), 12), 'wood', .66)
    return P

def wall_pipes(seed=1, H=30.0):
    """alley wall services (stands against a wall whose face is at z = 0, pieces toward -Z): drain pipe with clamps
    and shoe, vent duct, wall AC on a bracket"""
    P = Prop('WallPipes')
    add(P, tube([V3((0, -.3, -.6)), V3((0, H, -.6))], .35, sides=8), 'metal', .45)
    for y in range(2, int(H), 6): add(P, slab(-.5, .5, y, y + .3, -1.1, 0), 'metal', .3)
    add(P, tube([V3((0, .6, -.6)), V3((0, .3, -1.5)), V3((0, -.3, -2.0))], .35, sides=8), 'metal', .45)
    add(P, slab(2.0, 3.6, 3, H * .7, -1.6, 0), 'metal', .5)
    add(P, slab(1.8, 3.8, 3, 3.4, -1.8, 0), 'metal', .4)
    ac_unit(P, (-3.6, 8.0, -2.2), 0, .8)
    add(P, slab(-5.4, -1.8, 7.6, 8.0, -3.6, 0), 'metal', .3)
    return P

def street_tree(seed=1, h=20.0, grate=True):
    """tree: flared trunk with roots, 4 limbs, 6 overlapping smooth leaf masses as one crown (stylised_trees.md);
    street version has a stone-kerbed pit with an iron grate"""
    rng = random.Random(seed); P = Prop(('StreetTree%d' if grate else 'ParkTree%d') % seed)
    bark = S('wood', grad=(0, h * .5, .3, .62), up=.05, jit=.02)
    lean = V3((rng.uniform(-.6, .6), 0, rng.uniform(-.6, .6)))
    th = .48 if not grate else .6                                    # street trees: crown lifted over awnings
    pts = [V3((0, -.6, 0)) + lean * (t * t) + V3((0, h * th * t, 0)) for t in [i / 5 for i in range(6)]]
    P.add(tube(pts, [h * .055, h * .042, h * .036, h * .032, h * .028, h * .022], sides=8, rough=.05, seed=seed), bark, smooth=True)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); R = h * .05
        P.add(tube([V3((0, R * 1.6, 0)), V3((math.cos(a) * R * 1.6, R * .5, math.sin(a) * R * 1.6)), V3((math.cos(a) * R * 2.6, -.5, math.sin(a) * R * 2.6))],
                   [R * .55, R * .38, R * .12], sides=5), bark, smooth=True)
    top = pts[-1]; cs = []
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(-.4, .4); d = h * (rng.uniform(.17, .23) if not grate else rng.uniform(.11, .14))
        c = top + V3((math.cos(a) * d, h * rng.uniform(.04, .14), math.sin(a) * d))
        P.add(tube([pts[3], (pts[3] + c) / 2 + V3((0, h * .04, 0)), c], [h * .024, h * .016, h * .01], sides=5), bark, smooth=True)
        cs.append((c + V3((0, h * .04, 0)), h * (rng.uniform(.16, .2) if not grate else rng.uniform(.13, .15))))
    cs.append((top + V3((0, h * .2, 0)), h * (.22 if not grate else .17)))
    cs.append((top + V3((rng.uniform(-1, 1), h * .1, rng.uniform(-1, 1))), h * (.2 if not grate else .16)))
    for i, (c, r) in enumerate(cs):
        P.add(T(blob(r, seed * 13 + i, n=24, sq=.82), tuple(c)), S('leaf', grad=(top.y - h * .15, top.y + h * .42, .25, .82), up=.12, vn=(6, seed + i, .1)), smooth=True)
    if grate:
        for (x0, x1, z0, z1) in ((-3.2, 3.2, -3.2, -2.7), (-3.2, 3.2, 2.7, 3.2), (-3.2, -2.7, -2.7, 2.7), (2.7, 3.2, -2.7, 2.7)):
            add(P, slab(x0, x1, -.3, .75, z0, z1), 'cream', .62)
        add(P, slab(-2.7, 2.7, .52, .62, -2.7, 2.7), 'metal', .3)
        for k in range(-2, 3): add(P, slab(k - .08, k + .08, .62, .7, -2.7, 2.7), 'metal', .45, up=0)
        add(P, T(torus(1.15, .12, n=10, sides=3), (0, .66, 0)), 'metal', .5)
    return P

def hedge(seed=1, L=10.0):
    P = Prop('Hedge%d' % seed); rng = random.Random(seed)
    n = int(L / 2.2)
    for k in range(n):
        x = -L / 2 + (k + .5) * L / n
        add(P, T(blob(1.7, seed * 9 + k, n=14, sq=.9), (x, 1.3, rng.uniform(-.2, .2))), 'leaf', .5, smooth=True)
    add(P, slab(-L / 2, L / 2, -.3, .4, -1.3, 1.3), 'wood', .25)
    return P

def flower_bed(seed=1, L=10.0, W=3.0):
    """low stone-edged bed with a row of leaf clumps and flowers in alternating colours"""
    P = Prop('FlowerBed%d' % seed); rng = random.Random(seed)
    for sz in (-1, 1): add(P, slab(-L / 2, L / 2, -.3, .9, sz * W / 2 - .3, sz * W / 2 + .3), 'cream', .7)
    for sx in (-1, 1): add(P, slab(sx * L / 2 - .3, sx * L / 2 + .3, -.3, .9, -W / 2, W / 2), 'cream', .7)
    add(P, slab(-L / 2 + .3, L / 2 - .3, .3, .6, -W / 2 + .3, W / 2 - .3), 'wood', .18, up=0)
    cols = ('red', 'yellow', 'blue', 'red')
    n = int(L / 1.1)
    for k in range(n):
        x = -L / 2 + .8 + k * (L - 1.6) / max(1, n - 1)
        add(P, T(blob(.65, seed * 3 + k, n=9), (x, .9, rng.uniform(-.4, .4))), 'leaf', .5)
        flower(P, (x + .2, 1.5, rng.uniform(-.5, .5)), cols[(k // 2 + seed) % 4], .4, rng.uniform(-.4, .4))
        flower(P, (x - .3, 1.25, rng.uniform(-.6, .6)), cols[(k // 2 + seed + 1) % 4], .32, rng.uniform(-.4, .4))
    return P

def street_grate():
    """the street tree pit alone (stone kerb + iron grate + trunk ring): the realistic gen_trees tree stands in it"""
    P = Prop('StreetGrate')
    for (x0, x1, z0, z1) in ((-3.2, 3.2, -3.2, -2.7), (-3.2, 3.2, 2.7, 3.2), (-3.2, -2.7, -2.7, 2.7), (2.7, 3.2, -2.7, 2.7)):
        add(P, slab(x0, x1, -.3, .75, z0, z1), 'cream', .62)
    add(P, slab(-2.7, 2.7, .52, .62, -2.7, 2.7), 'metal', .3)
    for k in range(-2, 3): add(P, slab(k - .08, k + .08, .62, .7, -2.7, 2.7), 'metal', .45, up=0)
    add(P, T(torus(1.15, .12, n=10, sides=3), (0, .66, 0)), 'metal', .5)
    return P
