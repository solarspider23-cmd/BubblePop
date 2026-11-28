# Glowroot Caverns - prop kit part 3: stations, hero (The Glowroot), ceiling falls, skylight lip, spawn dais
from cave_props2 import *
from mathutils import Vector, Matrix, noise as MN
import math, random, bmesh

def boards(P, x0, x1, y0, y1, z, t=.3, w=1.0, col='wood', seed=0, vertical=True, yaw=0.0, cx=0.0, cz=0.0):
    """a wall of vertical boards between x0..x1 (y0..y1) at depth z, rotated by yaw about (cx, cz)"""
    rng = random.Random(seed); x = x0
    while x < x1 - .05:
        ww = min(w * rng.uniform(.85, 1.1), x1 - x); h = y1 - y0 - rng.uniform(0, .3)
        b = box((ww - .08, h, t), .04); T(b, (x + ww / 2 - cx, y0 + h / 2, z - cz)); T(b, (cx, 0, cz), yaw=yaw)
        P.add(b, W(col, rng.uniform(.4, .58), int(x * 13) + seed)); x += ww

def shed_roof(P, w, d, y_back, y_front, z_back, z_front, seed=0, col='wooddk'):
    """overlapping board-and-batten shed roof falling to the front, with a fascia board"""
    rng = random.Random(seed); n = int(w / 1.2); dz = z_front - z_back; dy = y_front - y_back
    pitch = math.degrees(math.atan2(dy, abs(dz)))
    for i in range(n):
        x = -w / 2 + (i + .5) * w / n
        L = math.hypot(dz, dy) + rng.uniform(-.2, .3)
        b = box((w / n + .12, .28, L), .05); T(b, (0, 0, 0), pitch=pitch); T(b, (x, (y_back + y_front) / 2 + (i % 2) * .14, (z_back + z_front) / 2))
        P.add(b, W(col, rng.uniform(.38, .55), i + seed))
    P.add(T(box((w + .4, .9, .3), .05), (0, y_front - .2, z_front - .1)), W('wood', .5))

def mine_shop():
    """ORE EXCHANGE: a timber mine-office shed on a plank deck with log sills: board walls with corner logs, a deep
    shed roof on front posts, trade counter with an ore scale, back shelves of glowing ore samples, crates, a hanging
    lantern and a BLANK framed sign board over the counter (GUI label spot). Front = -Z, 16 x 13."""
    rng = random.Random(4); P = Prop('MineShop')
    for x in (-7.5, 7.5):
        for z in (-5.5, 5.5): P.add(logp((x, -1.0, z), (x, .3, z), .5, 7), W('wooddk', .45))
    for x in (-7.5, 0, 7.5): P.add(T(box((.5, .45, 12), .05), (x, .35, 0)), W('wooddk', .45))
    x = -8.0
    while x < 8.0:
        w = rng.uniform(1.0, 1.25); P.add(T(box((w - .06, .3, 12.6), .04), (x + w / 2, .75, 0)), W('wood', rng.uniform(.42, .6), int(x * 5))); x += w
    for x, z in ((-7.4, 5.9), (7.4, 5.9), (-7.4, -1.5), (7.4, -1.5)):
        P.add(logp((x, .6, z), (x, 11.8 if z > 0 else 10.6, z), .38, 7), V('wood', 0, 12, .35, .6))
    boards(P, -7.4, 7.4, .9, 11.6, 5.95, seed=1, col='wood')                  # back wall
    for sx in (-1, 1):                                                        # side walls (boards running along Z)
        z = -1.5
        while z < 5.9:
            w = rng.uniform(1.0, 1.2); top = lerp(10.6, 11.6, (z + 1.5) / 7.4)
            P.add(T(box((.3, top - .9, w - .06), .04), (sx * 7.45, (top + .9) / 2, z + w / 2)), W('wood', rng.uniform(.38, .55), int(z * 7)))
            z += w
        P.add(logp((sx * 7.6, 1.6, -1.2), (sx * 7.6, 9.6, 5.6), .16, 5), W('wooddk', .45))
    for x in (-7.6, 7.6): P.add(logp((x, .6, -7.2), (x, 9.7, -7.2), .36, 7), V('wood', 0, 10, .35, .6))
    P.add(T(box((16.4, .6, .6), .05), (0, 9.8, -7.2)), W('wood', .5))
    for x in (-7.6, 7.6): P.add(T(box((.4, .5, 13.5), .05), (x, 10.6 + .45, -.6), pitch=-5), W('wood', .45))
    shed_roof(P, 17.6, 15, 12.4, 10.0, 6.6, -8.3, 3)
    P.add(T(box((12.4, 3.0, .4), .06), (0, 2.4, -4.6)), W('wood', .5))      # counter
    for k in range(6): P.add(T(box((.2, 2.9, .12)), (-5.5 + k * 2.2, 2.4, -4.85)), W('wooddk', .4))
    P.add(T(box((13.0, .35, 1.6), .08), (0, 4.05, -4.4)), W('wood', .62))
    for sx in (-1, 1): P.add(T(box((.4, 3.4, 1.4), .05), (sx * 6.4, 2.4, -4.4)), W('wooddk', .45))
    sc = Vector((-3.2, 4.2, -4.4))                                              # ore scale on the counter
    P.add(T(cyl(.6, .2, 8, .05), sc), FS('iron', .45)); P.add(T(box((.16, 2.2, .16)), sc + Vector((0, 1.2, 0))), FS('iron', .5))
    P.add(T(box((2.6, .12, .14)), sc + Vector((0, 2.3, 0)), roll=6), FS('iron', .55))
    for sx, dy in ((-1, .13), (1, -.13)):
        c = sc + Vector((sx * 1.25, 2.3 + dy, 0))
        for k in range(3):
            a = k * math.tau / 3; P.add(logp(c, c + Vector((math.cos(a) * .5, -1.1, math.sin(a) * .5)), .025, 3), FS('iron', .5))
        P.add(T(lathe([(.55, 0), (.6, .1), (0, -.15)], n=8), c + Vector((0, -1.15, 0))), FS('iron', .55))
        add_crystal(P, tuple(c + Vector((0, -1.15, 0))), .2, .7, int(sx + 3), 'amber' if sx < 0 else 'cyan', lean=20)
    for k, (yy, kinds) in enumerate(((3.2, ('amber', 'cyan', 'violet')), (5.6, ('cyan', 'violet', 'amber')), (8.0, ('violet', 'amber', 'cyan')))):
        P.add(T(box((12.5, .25, 1.4), .04), (0, yy, 5.0)), W('wood', .55))
        for sx in (-1, 1): P.add(logp((sx * 5.8, yy - .1, 5.6), (sx * 5.8, yy - 1.1, 5.6), .1, 4), W('wooddk', .4))
        for j in range(5):
            xx = -5 + j * 2.5; kind = kinds[j % 3]
            if j % 2: P.add(T(blob(.45, k * 9 + j, .7), (xx, yy + .45, 5.0)), FS('rock', .5, .3))
            add_crystal(P, (xx + .4, yy + .1, 5.0), .22, rng.uniform(.8, 1.3), k * 13 + j, kind, lean=rng.uniform(5, 25), yaw=rng.uniform(0, 360), glow_from=.3)
    P.add(T(box((9.0, 2.2, .3), .06), (0, 8.5, -7.45)), W('wooddk', .35))   # blank sign board (GUI label goes here)
    for y in (7.3, 9.7): P.add(T(box((9.6, .3, .45), .05), (0, y, -7.5)), W('wood', .55))
    for x in (-4.7, 4.7): P.add(T(box((.3, 2.7, .45), .05), (x, 8.5, -7.5)), W('wood', .55))
    oil_lantern(P, (6.0, 9.4, -7.2), 1.2); oil_lantern(P, (-6.0, 9.4, -7.2), 1.2)
    for k, (x, z, s) in enumerate(((-6.3, -3.0, 1.6), (-6.4, -1.0, 1.3))):
        P.add(T(box((s, s, s), .08), (x, .9 + s / 2, z), yaw=k * 17), W('wood', .52, k))
    return P

def crystal_forge():
    """CRYSTAL FORGE: an ashlar beehive kiln with a glowing arched mouth and a banded stone chimney, an anvil on a
    stump, a timber crusher hopper full of crystals, a quench trough of glowing cyan liquid, bellows, a tool bench
    with glowing crystal ingots. Front = -Z, ~18 x 14."""
    rng = random.Random(6); P = Prop('CrystalForge')
    kz = 2.5
    P.add(T(B.ashlar_ring(5.2, -.5, 5.5, 2.4, 1.3, seed=3, skip=lambda a, y: abs(((a - 1.5 * math.pi) + math.pi) % math.tau - math.pi) < .42 and y < 3.6), (0, 0, kz)), B.ash_sh('rock', .55, .08, .1, .1))
    dome = lathe([(5.2, 5.4), (5.0, 6.6), (4.2, 7.9), (2.8, 8.9), (1.6, 9.3), (0, 9.4)], n=16); jitter(dome, .15, 1.5, 3)
    P.add(T(dome, (0, 0, kz)), V('rock', 5, 9.4, .45, .62, ns=1.5))
    P.add(T(cyl(5.4, .6, 16, .1), (0, 5.2, kz)), FS('rock', .62, .2))
    for k in range(9):                                                        # arch voussoirs round the mouth
        a = math.pi * k / 8; c = Vector((math.cos(a) * 2.4, 1.0 + math.sin(a) * 2.6, kz - 5.15))
        P.add(T(box((1.0, .95, 1.1), .1), c, roll=math.degrees(a) - 90), FS('rock', .6, .15, .06, k))
    for sx in (-1, 1): P.add(T(box((1.1, 1.6, 1.2), .1), (sx * 2.4, .3, kz - 5.15)), FS('rock', .55, .15))
    mouth = lathe([(2.0, 0), (2.0, 1.0), (1.4, 2.6), (0, 3.2)], n=12); T(mouth, s=(1, 1, .2)); T(mouth, (0, -.4, kz - 4.75), pitch=0)
    P.gadd(mouth, 'fire')
    for k in range(4): P.gadd(G.flame_tongue(Vector(((k - 1.5) * .8, .1, kz - 4.4)), rng.uniform(1.6, 2.4), .45, k, k), 'fire')
    for k in range(3): add_crystal(P, ((k - 1) * 1.1, .2, kz - 3.6), .35, 1.4, k + 9, 'amber', lean=15, glow_from=.2)
    P.add(T(B.ashlar_ring(1.7, 8.6, 16.5, 1.6, 1.1, seed=5), (1.2, 0, kz + 1.0)), B.ash_sh('rock', .5, .08, .1, .05))
    for y in (10.5, 13.5, 16.2): P.add(T(torus(1.78, .16, 12, 4), (1.2, y, kz + 1.0)), FS('iron', .4))
    P.add(T(lathe([(1.9, 16.4), (2.2, 16.9), (1.5, 17.3)], n=12), (1.2, 0, kz + 1.0)), FS('rock', .5, .15))
    av = Vector((-6.8, 0, -4.0))                                              # anvil on a stump
    P.add(T(lathe([(1.2, -.4), (1.25, 1.8), (1.05, 2.3), (0, 2.35)], n=10), av), V('wood', 0, 2.3, .35, .6))
    P.add(T(hull([Vector(p) for p in ((-.8, 2.3, -.45), (.8, 2.3, -.45), (-.8, 2.3, .45), (.8, 2.3, .45), (-.5, 2.9, -.35), (.5, 2.9, -.35),
                                     (-.5, 2.9, .35), (.5, 2.9, .35))]), av), FS('iron', .4))
    P.add(T(hull([Vector(p) for p in ((-1.3, 2.9, -.5), (1.1, 2.9, -.5), (-1.3, 2.9, .5), (1.1, 2.9, .5), (-1.3, 3.5, -.5), (1.1, 3.5, -.5),
                                     (-1.3, 3.5, .5), (1.1, 3.5, .5), (2.4, 3.4, 0), (2.0, 3.0, 0))]), av), FS('iron', .55, .2))
    P.add(T(logp((-.9, 3.55, .2), (.7, 3.75, .3), .12, 5), av), W('wood', .6)); P.add(T(box((.55, .5, .5), .05), av + Vector((-1.0, 3.75, .2))), FS('iron', .5))
    hp = Vector((7.0, 0, -1.0))                                               # crusher hopper
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(logp(hp + Vector((sx * 2.2, -.5, sz * 2.0)), hp + Vector((sx * 1.6, 8.0, sz * 1.5)), .3, 6), W('wood', .5))
    P.add(T(lathe([(.6, 4.0), (2.6, 7.4), (2.8, 8.4), (2.6, 8.4), (.45, 4.6)], n=4, a0=math.pi / 4), hp), FS('iron', .4, .2))
    for k in range(7):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.5)
        add_crystal(P, tuple(hp + Vector((math.cos(a) * d, 7.4, math.sin(a) * d))), .32, rng.uniform(1.4, 2.2), k + 20, rng.choice(('cyan', 'violet', 'amber')), lean=rng.uniform(5, 35), yaw=rng.uniform(0, 360))
    P.add(T(box((3.0, 1.2, 3.0), .1), hp + Vector((0, 1.6, 0))), W('wooddk', .45)); P.add(T(cyl(.9, 1.0, 10, .1), hp + Vector((0, 2.2, -1.5)), pitch=90), FS('iron', .5))
    tq = Vector((-1.0, 0, -7.6))                                              # quench trough
    P.add(T(box((5.6, 1.6, 2.2), .12), tq + Vector((0, .7, 0))), W('wood', .45))
    for x in (-2.4, 2.4): P.add(T(box((.3, 1.75, 2.35)), tq + Vector((x, .72, 0))), FS('iron', .4))
    P.gadd(T(box((5.0, .1, 1.7)), tq + Vector((0, 1.45, 0))), 'cyan')
    bl = Vector((4.6, 0, 3.0))                                                # bellows against the kiln
    P.add(T(box((1.6, .2, 3.0), .05), bl + Vector((0, 2.2, 0)), roll=-12), W('wood', .5)); P.add(T(box((1.6, .2, 3.0), .05), bl + Vector((0, 1.2, 0)), roll=10), W('wood', .5))
    P.add(T(hull([Vector(p) for p in ((-.7, 1.3, -1.3), (.7, 1.25, -1.3), (-.7, 2.1, -1.3), (.7, 2.15, -1.3), (-.7, 1.3, 1.3), (.7, 1.25, 1.3), (-.7, 2.1, 1.3), (.7, 2.15, 1.3), (0, 1.0, 0), (0, 2.5, 0))]), bl), FS('canvas', .35))
    P.add(logp(bl + Vector((-.8, 1.7, 0)), bl + Vector((-2.3, 1.4, -.6)), .18, 6, .1), FS('iron', .5))
    P.add(T(box((.5, 1.0, .5)), bl + Vector((0, .5, 0))), W('wooddk', .4))
    bn = Vector((-6.8, 0, 3.5))                                               # bench + ingots
    P.add(T(box((4.2, .35, 2.0), .06), bn + Vector((0, 3.0, 0))), W('wood', .55))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(T(box((.3, 3.0, .3)), bn + Vector((sx * 1.8, 1.4, sz * .8))), W('wooddk', .45))
    for k in range(4):
        P.gadd(T(box((.9, .35, .45), .08), bn + Vector((-1.2 + k * .8, 3.35, -.2 + (k % 2) * .5)), yaw=k * 8), ('cyan', 'amber', 'violet', 'cyan')[k])
    P.add(T(box((.25, .25, 1.6)), bn + Vector((1.3, 3.3, .2)), yaw=20), FS('iron', .5))
    return P

def camp_tent():
    """A-frame canvas tent: ridge log on X-poles, two canvas slopes sagging between the poles, a closed back
    triangle, rolled-back front flaps, guy ropes to pegs, bedroll inside. Front = -Z, 8 x 10 x 6.3."""
    P = Prop('CampTent'); H = 6.0; hw = 4.0; L = 10.0
    for z in (-L / 2, L / 2):
        for sx in (-1, 1): P.add(logp((sx * (hw + .2), -.4, z), (-sx * .3, H + .5, z), .17, 5), W('wood', .5))
    P.add(logp((0, H + .2, -L / 2 - .6), (0, H + .2, L / 2 + .6), .2, 6), W('wood', .55))
    for sx in (-1, 1):                                                       # canvas slope (sags between the poles)
        bm = bmesh.new(); nx, nz_ = 5, 8; vv = {}
        for i in range(nx + 1):
            for j in range(nz_ + 1):
                u, t = i / nx, j / nz_; z = -L / 2 + L * t
                sag_ = .35 * math.sin(math.pi * t) * math.sin(math.pi * u)
                vv[i, j] = bm.verts.new((sx * hw * u - sx * sag_ * .6, H - H * u + .1 - sag_, z))
        for i in range(nx):
            for j in range(nz_): bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.12)
        P.add(bm, V('canvas', 0, H, .45, .7, nk=.05, ns=3), smooth=True)
        for j in range(5): P.add(logp((sx * hw * .2, H - .7, -L / 2 + 1 + j * 2), (sx * hw * .98, .25, -L / 2 + 1 + j * 2), .05, 4), FS('canvas', .35))
    back = bmesh.new(); vs = [back.verts.new(p) for p in ((-hw, .1, L / 2), (hw, .1, L / 2), (0, H + .1, L / 2))]; back.faces.new(vs)
    bmesh.ops.solidify(back, geom=list(back.faces), thickness=.12); P.add(back, FS('canvas', .5, .1))
    for sx in (-1, 1):                                                       # rolled front flaps
        P.add(tube([Vector((sx * .6, H - .4, -L / 2 - .05)), Vector((sx * 2.2, H * .55, -L / 2 - .1)), Vector((sx * 3.4, 1.2, -L / 2 - .05))], .32, 7), FS('canvas', .55))
        for sz in (-1, 1):
            peg = Vector((sx * (hw + 2.6), 0, sz * (L / 2 + 1.0)))
            P.add(logp((sx * .2, H + .3, sz * (L / 2 + .5)), tuple(peg + Vector((0, .4, 0))), .04, 3), FS('canvas', .55))
            P.add(T(box((.2, .9, .2)), peg + Vector((0, .2, 0)), roll=sx * 20), W('wooddk', .5))
    P.add(T(cyl(.6, 3.2, 10, .1), (-1.6, .6, .5), pitch=90), FS('red', .45))
    P.add(T(box((2.4, .3, 4.6), .1), (1.2, .2, 1.5)), FS('canvas', .4))
    return P

def campfire_pit(seed=1):
    """stone ring, teepee logs, flame tongues + embers (glow), a spit on Y-sticks with a hanging pot"""
    rng = random.Random(seed); P = Prop('Campfire')
    for k in range(12):
        a = k * math.tau / 12; P.add(T(blob(.55, seed + k, .65), (math.cos(a) * 2.2, .1, math.sin(a) * 2.2)), FS('rock', .45, .3, .1, k))
    P.add(T(cyl(1.8, .12, 12, y0=-.05), (0, 0, 0)), FS('wooddk', .1, .05))
    for k in range(6):
        a = k * math.tau / 6 + .3; P.add(logp((math.cos(a) * 1.6, .1, math.sin(a) * 1.6), (math.cos(a) * .2, 1.6, math.sin(a) * .2), .22, 6), W('wooddk', .45))
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.3, .3)
        P.gadd(G.flame_tongue(Vector((math.cos(a) * .5, .3, math.sin(a) * .5)), rng.uniform(1.3, 2.0), .5, a, seed + k), 'fire')
    for k in range(8):
        a = rng.uniform(0, math.tau); d = rng.uniform(.3, 1.3); P.gadd(T(blob(.2, k, .6, 8), (math.cos(a) * d, .1, math.sin(a) * d)), 'amber')
    for sx in (-1, 1):
        P.add(logp((sx * 2.6, -.4, 0), (sx * 2.6, 3.6, 0), .12, 5), W('wood', .5))
        P.add(logp((sx * 2.6, 3.0, 0), (sx * 2.9, 3.9, 0), .09, 4), W('wood', .5)); P.add(logp((sx * 2.6, 3.0, 0), (sx * 2.3, 3.9, 0), .09, 4), W('wood', .5))
    P.add(logp((-3.0, 3.75, 0), (3.0, 3.75, 0), .1, 5), W('wood', .6))
    P.add(logp((0, 3.7, 0), (0, 3.25, 0), .03, 3), FS('iron', .5))
    P.add(T(lathe([(.35, 0), (.5, .3), (.44, .62), (.47, .7), (0, .6)], n=10), (0, 2.55, 0)), FS('iron', .35))
    return P

def quest_board():
    """notice board: two posts on stone feet, plank board with a frame, a little shingle roof, pinned blank papers
    (no text), nail heads, a lantern hook and a rope coil"""
    rng = random.Random(8); P = Prop('QuestBoard')
    for sx in (-1, 1):
        P.add(T(blob(.7, sx + 3, .5), (sx * 3.2, .1, 0)), FS('rock', .45))
        P.add(T(box((.5, 8.0, .5), .08), (sx * 3.2, 3.7, 0)), V('wood', 0, 8, .38, .6))
    boards(P, -3.0, 3.0, 2.2, 6.6, .05, t=.25, w=.9, seed=2)
    for y in (2.1, 6.7): P.add(T(box((6.6, .3, .4), .05), (0, y, -.05)), W('wooddk', .5))
    for sx in (-1, 1):
        P.add(T(box((4.8, .2, 2.2), .05), (sx * 1.6, 8.0, 0), roll=sx * -22), W('wooddk', .45))
    P.add(logp((-3.6, 8.9, 0), (3.6, 8.9, 0), .14, 5), W('wood', .5))
    for k in range(6):
        x = -2.2 + (k % 3) * 2.2 + rng.uniform(-.3, .3); y = 5.6 if k < 3 else 3.5
        P.add(T(box((1.4, 1.7, .05)), (x, y + rng.uniform(-.2, .2), -.15), roll=rng.uniform(-8, 8)), FS('canvas', rng.uniform(.6, .78), .05, .02, k))
        P.add(T(cyl(.09, .1, 6), (x, y + .7, -.25), pitch=90), FS('iron', .55))
    P.add(T(torus(.5, .15, 10, 5), (3.6, 4.0, -.3), pitch=90), FS('canvas', .5))
    oil_lantern(P, (-3.9, 7.4, -.6), .9); P.add(logp((-3.4, 7.6, 0), (-3.9, 7.6, -.6), .07, 4), FS('iron', .45))
    return P

def log_seat(seed=1):
    """split-log bench on two chunk feet"""
    P = Prop('LogSeat')
    b = lathe([(0, 0), (.62, 0), (.62, 4.6), (0, 4.6)], n=10); T(b, (0, 0, -2.3), pitch=90)
    for v in b.verts: v.co.y = max(v.co.y, 0)
    T(b, (0, .95, 0)); P.add(b, V('wood', .9, 1.6, .4, .6))
    for z in (-1.6, 1.6): P.add(T(cyl(.55, 1.0, 8, .06, y0=-.1), (0, 0, z)), W('wooddk', .45))
    return P

def deep_lift():
    """DEEP-DIVE ELEVATOR: timber headframe (two leaning A-frames with ties + braces) carrying a big spoked sheave,
    cable to an iron-barred cage with a lattice gate on the landing, a winch drum with lever behind, a plank deck with
    railings round the shaft collar, signal lamps (red / warm) on a post. Front = -Z, cage 6 x 7.5 x 6 at (0, 0, 0)."""
    rng = random.Random(5); P = Prop('DeepLift'); top = 24.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(logp((sx * 5.2, -.6, sz * 5.4), (sx * 4.2, top, sz * 1.2), .5, 8), V('wood', 0, top, .35, .6, ns=3))
        for y in (7.0, 14.0, 20.0):
            t = y / top; zz = 5.4 + (1.2 - 5.4) * t; xx = 5.2 + (4.2 - 5.2) * t
            P.add(T(box((.4, .45, 2 * zz + .8), .05), (sx * xx, y, 0)), W('wood', .45))
        P.add(logp((sx * 5.0, 1.0, -5.0), (sx * 4.5, 13.0, 3.8), .22, 5), W('wooddk', .45))
        P.add(logp((sx * 5.0, 1.0, 5.0), (sx * 4.5, 13.0, -3.8), .22, 5), W('wooddk', .45))
    for y in (14.0, top + .3): P.add(T(box((10.6, .6, .6), .06), (0, y, 0)), W('wood', .5))
    sh = Vector((0, top + 3.2, 0))                                            # sheave wheel (axis X)
    P.add(T(torus(3.0, .28, 20, 6), sh, roll=90), FS('iron', .45, .2))
    for k in range(8):
        a = k * math.tau / 8; P.add(logp(sh, sh + Vector((0, math.sin(a) * 2.9, math.cos(a) * 2.9)), .1, 4), FS('iron', .4))
    P.add(T(cyl(.55, 2.0, 8, y0=-1.0), sh, roll=90), FS('iron', .6))
    for sx in (-1, 1): P.add(T(box((.6, 3.4, 1.2), .08), (sx * 1.3, top + 1.6, 0)), W('wooddk', .45))
    P.add(logp((0, top + 3.2, -3.0), (0, 8.0, -0.0), .09, 4), FS('iron', .5))
    P.add(logp((0, top + 3.2, 3.0), (0, 2.6, 9.0), .09, 4), FS('iron', .5))
    for y in (0.0, 7.5):                                                       # cage
        P.add(T(box((6.2, .35, 6.2), .06), (0, y + .2, 0)), FS('iron', .4))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(T(box((.32, 7.5, .32)), (sx * 3.0, 3.95, sz * 3.0)), FS('iron', .45))
    for k in range(9):
        t = -2.6 + k * .65
        for s in (-1, 1): P.add(T(box((.09, 7.2, .09)), (s * 3.0, 3.95, t)), FS('iron', .35))
        P.add(T(box((.09, 7.2, .09)), (t, 3.95, 3.0)), FS('iron', .35))
    for k in range(6):
        y = .9 + k * 1.15; P.add(T(box((5.9, .1, .1)), (0, y, -3.05), roll=28), FS('iron', .4)); P.add(T(box((5.9, .1, .1)), (0, y, -3.05), roll=-28), FS('iron', .4))
    for y in (1.0, 4.0, 7.0):
        for s in (-1, 1): P.add(T(box((.16, .16, 6.0)), (s * 3.0, y, 0)), FS('iron', .45))
        P.add(T(box((6.0, .16, .16)), (0, y, 3.0)), FS('iron', .45))
    P.add(T(lathe([(.6, 7.7), (.35, 8.2), (0, 8.3)], n=8), (0, 0, 0)), FS('iron', .5))
    for sx in (-1, 1):                                                        # deck round the collar, opening at the front
        P.add(T(box((3.8, .4, 13.0), .06), (sx * 5.3, -.05, 1.0)), W('wood', .5))
        for z in (-3.5, 0, 3.5, 6.5): P.add(T(box((.3, 3.6, .3)), (sx * 7.0, 1.6, z)), W('wood', .5))
        P.add(T(box((.25, .3, 10.5)), (sx * 7.0, 3.3, 1.5)), W('wood', .55))
    P.add(T(box((6.8, .4, 3.8), .06), (0, -.05, 5.3)), W('wood', .5))
    for k in range(4):                                                       # timber collar cribbing visible round the cage
        P.add(T(box((7.4, .6, .6), .05), (0, -.4 - k * .65, 3.4)), W('wooddk', .4)); P.add(T(box((7.4, .6, .6), .05), (0, -.4 - k * .65, -3.4)), W('wooddk', .4))
        for sx in (-1, 1): P.add(T(box((.6, .6, 6.2), .05), (sx * 3.4, -.7 - k * .65, 0)), W('wooddk', .4))
    wd = Vector((0, 0, 9.0))                                                  # winch
    for sx in (-1, 1): P.add(T(box((.5, 3.6, 2.4), .08), wd + Vector((sx * 2.0, 1.4, 0))), W('wood', .45))
    P.add(T(cyl(1.0, 3.6, 12, .1, y0=-1.8), wd + Vector((0, 2.6, 0)), roll=90), FS('iron', .45))
    for s in (-1, 1): P.add(T(cyl(1.4, .2, 12, y0=-.1), wd + Vector((s * 1.75, 2.6, 0)), roll=90), FS('red', .5))
    P.add(logp(wd + Vector((2.4, 2.6, 0)), wd + Vector((3.2, 5.6, -1.2)), .12, 5), FS('iron', .5)); P.add(T(blob(.25, 1, 1, 8), wd + Vector((3.2, 5.7, -1.2))), FS('red', .6))
    sp = Vector((-5.0, 0, -4.4))                                              # signal post
    P.add(T(box((.4, 7.4, .4), .06), sp + Vector((0, 3.3, 0))), W('wood', .5))
    for k, gk in enumerate(('pale', 'pale')):
        c = sp + Vector((0, 5.6 + k * 1.2, -.4)); P.add(T(cyl(.45, .3, 8, .05), c, pitch=90), FS('iron', .35)); P.gadd(T(lathe([(.32, 0), (.3, .25), (0, .3)], n=8), c + Vector((0, 0, -.15)), pitch=-90), gk)
    return P

def brew_station():
    """SPORE BREWERY: a stone hearth under a fat iron cauldron of glowing brew, small flames, a paddle, a jar shelf
    (glowing jars), spore sacks, all under its own giant flat-cap fungus canopy (glowing gills). Front = -Z."""
    rng = random.Random(9); P = Prop('BrewStation')
    for k in range(10):
        a = k * math.tau / 10; P.add(T(box((1.4, 1.2, 1.0), .15), (math.cos(a) * 2.6, .45, math.sin(a) * 2.6 - 1), yaw=-math.degrees(a)), FS('rock', .5, .2, .08, k))
    cw = lathe([(1.2, .9), (2.2, 1.4), (2.6, 2.6), (2.3, 3.7), (2.1, 3.9), (2.25, 4.05), (2.0, 4.05), (1.9, 3.85), (0, 3.6)], n=16)
    T(cw, (0, 0, -1)); P.add(cw, FS('iron', .35, .2))
    P.gadd(T(cyl(1.92, .1, 16, y0=0), (0, 3.6, -1)), 'brew')
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(.3, 1.4); P.gadd(T(blob(.3, k, 1, 8), (math.cos(a) * d, 3.75, math.sin(a) * d - 1)), 'brew')
    for k in range(3):
        a = k * math.tau / 3; P.add(logp((math.cos(a) * 1.8, 1.4, math.sin(a) * 1.8 - 1), (math.cos(a) * 2.3, 0, math.sin(a) * 2.3 - 1), .2, 5), FS('iron', .4))
    for k in range(4): P.gadd(G.flame_tongue(Vector(((k - 1.5) * .6, .3, -1)), rng.uniform(.9, 1.4), .35, k, k + 4), 'fire')
    P.add(logp((.6, 3.4, -1.3), (2.2, 6.4, -2.4), .12, 5), W('wood', .6)); P.add(T(box((.5, 1.0, .12), .04), (.45, 3.3, -1.2), roll=-28, yaw=35), W('wood', .55))
    sh = Vector((5.0, 0, 2.0))
    for sx in (-1, 1): P.add(T(box((.35, 6.0, .35), .05), sh + Vector((sx * 2.0, 2.8, 0))), W('wood', .5))
    for y in (1.6, 3.4, 5.2):
        P.add(T(box((4.4, .25, 1.2), .04), sh + Vector((0, y, 0))), W('wood', .55))
        for j in range(3):
            gk = ('brew', 'violet', 'brew')[(j + int(y)) % 3]; c = sh + Vector((-1.3 + j * 1.3, y + .12, 0))
            P.gadd(T(lathe([(.35, 0), (.42, .5), (.2, .85), (.2, 1.0), (0, 1.0)], n=8), c), gk)
            P.add(T(cyl(.24, .2, 8, .04), c + Vector((0, 1.0, 0))), W('wooddk', .5))
    for k, (x, z) in enumerate(((-4.6, 1.5), (-5.4, -.2), (-4.0, 3.0))):
        sk = lathe([(0, 0), (.9, .05), (1.1, .8), (.9, 1.7), (.4, 2.1), (.5, 2.4), (0, 2.45)], n=10); jitter(sk, .1, .8, k)
        P.add(T(sk, (x, 0, z), roll=rng.uniform(-6, 6)), V('canvas', 0, 2.4, .35, .6))
    mushroom(P, (-3.5, .2, 4.0), 13.0, 7.0, 5, 'flat', lean=16, yaw=35, spots=10, stem_r=.9, gk='brew', sk='brew', capcol='crysV')
    return P

def spawn_dais():
    """spawn platform: layered round stone plinth (sloped lip, walkable), slab ring on top split into chamfered
    flagstones, an inlaid glowing amber ring, four crystal-topped stone bollards. r ~9.5, top y .9"""
    rng = random.Random(2); P = Prop('SpawnDais')
    base = lathe([(10.4, -.8), (10.2, .0), (9.6, .55), (9.2, .7), (0, .7)], n=36); jitter(base, .12, 2.5, 2)
    P.add(base, V('rock', -.8, .7, .3, .55, ns=3), smooth=True)
    for ring_, (r0, r1, n) in enumerate(((2.8, 5.6, 9), (5.8, 8.9, 15))):
        for k in range(n):
            a0 = k * math.tau / n + .02; a1 = (k + 1) * math.tau / n - .02 + ring_ * .1
            pts = [(math.cos(a0 + (a1 - a0) * t) * r, math.sin(a0 + (a1 - a0) * t) * r) for r, ts in ((r1, (0, .5, 1)), (r0, (1, .5, 0))) for t in ts]
            s = ngon_prism(pts, .65, .9 + rng.uniform(-.03, .03), .06); P.add(s, FS('rock', .6, .15, .06, k + ring_ * 20))
    P.add(T(cyl(2.6, .25, 16, .06), (0, .65, 0)), FS('rock', .66, .15))
    P.gadd(T(torus(2.7, .14, 32, 5), (0, .86, 0)), 'amber')
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4; c = Vector((math.cos(a) * 9.6, 0, math.sin(a) * 9.6))
        P.add(T(lathe([(.9, -.5), (.95, .8), (.7, 1.0), (.75, 2.6), (.95, 2.8), (.7, 3.0), (0, 3.0)], n=8), c), FS('rock', .55, .2, .05, k))
        add_crystal(P, tuple(c + Vector((0, 2.9, 0))), .42, 1.8, k + 40, 'amber', lean=6, yaw=k * 40)
    return P

# ================================================================== ceiling falls, skylight lip
def cave_falls(Hf=50.0, seed=3):
    """waterfall from a ceiling crack (origin = bottom centre at the lake surface, wall behind at +Z): a rock lip with
    drip spikes, then a LOOSE sheet of 10 ragged strands that fan apart as they fall (some break up into spray before the
    bottom), bright streak cores on a few, a heaped foam base with splash rings and rocks breaking the plunge"""
    rng = random.Random(seed); P = Prop('CaveFalls')
    lip = strata_mass(8.5, 3.0, 4.5, seed, k=6, layers=2, n=3.0); T(lip, (0, Hf + 2.4, 3.0))
    P.add(lip, RS('rock', Hf, Hf + 6, .35, .55, rim_shade(lip)), smooth=True)
    for k in range(6):
        a = (k - 2.5) * .4; s = lathe(drip_profile(rng.uniform(2, 4), .5, 2, k), n=6); P.add(T(s, (math.sin(a) * 7, Hf + .2, -1.2 + abs(k - 2.5) * .5)), V('rock', Hf - 4, Hf, .5, .35))
    def strand(x0, w0, spread, end, ph, z0, thick):
        n = 12; bm = bmesh.new(); L_, R_ = [], []; rr = random.Random(int(ph * 100))
        for i in range(n + 1):
            t = i / n * end; y = Hf + .6 - (Hf + .6) * t
            z = z0 - 3.2 * t ** 1.5 - .4 * math.sin(t * 7 + ph)
            x = x0 * (1 + spread * t) + math.sin(t * 4 + ph) * 1.2 * t
            w = w0 * (1 + .9 * t) * (1 + .25 * math.sin(t * 17 + ph)) * (1 - .6 * max(0, (t - end + .12) / .12))
            L_.append(bm.verts.new((x - w / 2, y, z))); R_.append(bm.verts.new((x + w / 2, y, z + rr.uniform(-.15, .15))))
        for i in range(n): bm.faces.new((L_[i], R_[i], R_[i + 1], L_[i + 1]))
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=thick); return bm, Vector(((L_[-1].co.x + R_[-1].co.x) / 2, L_[-1].co.y, L_[-1].co.z))
    for k in range(10):
        x0 = (k - 4.5) * 1.35 + rng.uniform(-.3, .3); end = 1.0 if k % 3 else rng.uniform(.62, .85)
        bm, tip = strand(x0, rng.uniform(.9, 1.7), .55, end, rng.uniform(0, 6), -.4 - (k % 2) * .5, .35)
        P.add(bm, V('water', 0, Hf, .82, .55, nk=0, ns=5, amp=.14), smooth=True)
        if k % 3 == 0: P.gadd(strand(x0, .3, .55, end * .98, k, -.8 - (k % 2) * .5, .1)[0], 'falls')
        if end < 1:                                                          # strand breaks into spray
            for j in range(4): P.gadd(dot(tip + Vector((rng.uniform(-1, 1), -rng.uniform(0, 3), rng.uniform(-.5, .5))), rng.uniform(.25, .5), .9, 5), 'falls')
    for k in range(18):                                                      # heaped foam base
        a = k * math.tau / 18 + rng.uniform(-.1, .1); d = rng.uniform(1.5, 6.5)
        f = strata_mass(rng.uniform(1.0, 2.0), rng.uniform(.5, 1.2), rng.uniform(.9, 1.6), k, k=4, layers=1, n=2.4)
        P.gadd(T(f, (math.cos(a) * d * 1.4, .25, -3.6 + math.sin(a) * d * .7)), 'falls')
    for k, r in enumerate((7.5, 11.0, 14.5)): P.gadd(T(torus(r, .2 - k * .04, 26, 4), (0, .05, -3.6), s=(1, 1, .65)), 'falls')
    for k in range(4):
        a = rng.uniform(0, math.tau); b = strata_mass(rng.uniform(1.4, 2.2), 1.2, 1.6, k + 40, k=5, layers=2)
        P.add(T(b, (math.cos(a) * 7.5, .3, -3.6 + math.sin(a) * 4)), RS('rock', -1, 2, .45, .7, rim_shade(b)), smooth=True)
    return P

def glow_puddle(seed=1):
    """shallow puddle on the floor: a flat irregular water film with a lit rim + a few glowing algae flecks (picks up
    the glow around it in Roblox as Glass / Reflectance)"""
    rng = random.Random(seed); P = Prop('GlowPuddle%d' % seed); n = 14
    pts = [(math.cos(a) * rng.uniform(2.2, 3.6), math.sin(a) * rng.uniform(1.6, 2.8)) for a in [k * math.tau / n for k in range(n)]]
    P.add(ngon_prism(pts, -.3, .06), flat('water', .78))
    P.add(ngon_prism([(x * 1.12, z * 1.12) for x, z in pts], -.35, .02), flat('sand', .35))
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(.5, 2); P.gadd(dot((math.cos(a) * d, .06, math.sin(a) * d * .7), .12, .3, 5), 'lake')
    return P

def glow_worms(seed=1, R=7.0, n=22):
    """glow-worm colony on the vault (origin at the top, hangs): fine silk threads of different lengths, each ending
    in a glowing droplet; faint teal specks that make the ceiling read"""
    rng = random.Random(seed); P = Prop('GlowWorms%d' % seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); d = R * math.sqrt(rng.random()); c = Vector((math.cos(a) * d, 0, math.sin(a) * d))
        L = rng.uniform(.6, 3.2)
        P.add(tube([c + Vector((0, .4, 0)), c - Vector((0, L, 0))], .03, 3, cap0=False), flat('canvas', .7))
        P.gadd(dot(c - Vector((0, L + .12, 0)), .13, 1.0, 4), 'root')
    return P

def skylight_lip(R=15.0, seed=4):
    """ring round the top of the sun shaft (origin = ring centre at the rim height): layered rocks with grassy turf
    tops, roots and grass strands dangling into the shaft"""
    rng = random.Random(seed); P = Prop('SkylightLip')
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-.1, .1); d = R + rng.uniform(1, 3)
        r = strata_mass(rng.uniform(5, 7), rng.uniform(2.5, 3.5), rng.uniform(4, 5.5), seed * 10 + k, k=5, layers=2)
        T(r, (math.cos(a) * d, rng.uniform(-.5, .5), math.sin(a) * d), yaw=-math.degrees(a)); cap = moss_cap(r, .7, thr=.3, seed=k, droop=2.0)
        P.add(r, RS('rock', -3, 3, .35, .6, rim_shade(r)), smooth=True); P.add(cap, V('moss', 0, 4, .5, .85), smooth=True)
    for k in range(16):
        a = k * math.tau / 16 + rng.uniform(-.1, .1); b = Vector((math.cos(a) * (R - .5), rng.uniform(-1, 1), math.sin(a) * (R - .5)))
        L = rng.uniform(5, 13); pts = [b + Vector((0, -L * t, 0)) - Vector((math.cos(a), 0, math.sin(a))) * math.sin(t * 2.5) * 1.2 for t in [i / 5 for i in range(6)]]
        P.add(tube(pts, [.3 - .045 * i for i in range(6)], 5, cap0=False), V('wooddk' if k % 2 else 'moss', b.y - L, b.y, .3, .6))
    return P

# ================================================================== the hero: THE GLOWROOT
def glowroot(Hh=86.0, seed=11):
    """THE GLOWROOT (hero): an ancient root mass that grew down from the vault to the lake islet. Nine thick roots
    leave the ceiling on a wide ring, twist into one braided pillar and flare at the foot into arching ground roots
    gripping the islet; glowing veins spiral up some roots; seed pods and tendrils hang off the braid; the HEART, a
    huge ribbed amber pod, sits in a cradle of husk petals between the foot roots. Origin = islet ground under the axis."""
    rng = random.Random(seed); P = Prop('Glowroot'); n = 9
    def root_path(k):
        """ceiling (t 0) -> ground (t 1): fans in straight from the vault, braids (twist only in the middle), flares"""
        a0 = k * math.tau / n + rng.uniform(-.15, .15); twist = .9 * math.tau; pts = []
        rt = rng.uniform(13, 19); rg = rng.uniform(11, 17); ytop = Hh + 7
        for i in range(25):
            t = i / 24
            y = ytop - (ytop + .6) * t
            if t < .28:                                                     # top fan: rises into the rock, no swirl
                u = t / .28; r = lerp(rt, 3.2, smooth(u)); y = lerp(ytop, Hh - 14, smooth(u) ** 1.3)
            elif t < .8: r = 3.0 + .45 * math.sin(t * 20 + k)
            else: r = lerp(3.0, rg, smooth((t - .8) / .2))
            if t > .86: y = lerp(y, .2 + 1.6 * math.sin(math.pi * (t - .86) / .14) ** .5 - 1.2 * ((t - .86) / .14) ** 3, .8)
            if .28 <= t < .4: y = lerp(Hh - 14, y, smooth((t - .28) / .12))
            a = a0 + twist * smooth(clamp((t - .28) / .52))
            pts.append(Vector((math.cos(a) * r, y, math.sin(a) * r)))
        return pts
    for k in range(n):
        pts = root_path(k); m = len(pts)
        rad = [lerp(.35, 1.9, smooth(i / (m * .2))) if i < m * .2 else (lerp(1.9, 1.25, smooth((i - m * .2) / (m * .15))) if i < m * .35 else (1.25 if i < m * .8 else lerp(1.25, .55, (i - m * .8) / (m * .2)))) for i in range(m)]
        rad = [r * rng.uniform(.85, 1.1) for r in rad]
        bm = tube(pts, rad, sides=9, rough=.08, seed=k); jitter(bm, .25, 2.0, k)
        P.add(bm, RS('wooddk', 0, Hh, .42, .6, rim_shade(bm), nk=.12, ns=3, seed=k, amp=.12, hi=.45, lo=.3), smooth=True)
        if True:                                                            # glow vein spiralling along every root
            T_, N_, B_ = __import__('pro_lib').frames(pts); vein = []
            for i in range(2, m - 2):
                ang = i * .9 + k; vein.append(pts[i] + (N_[i] * math.cos(ang) + B_[i] * math.sin(ang)) * rad[i] * .92)
            P.gadd(tube(vein, .16, 4), 'root')
        for j in range(2):                                                  # side rootlets at the foot
            i = m - 3 - j * 2; d = (pts[i] - Vector((0, pts[i].y, 0))).normalized()
            q = [pts[i], pts[i] + d * 3 + Vector((0, .6, 0)), pts[i] + d * 5.5 + Vector((rng.uniform(-1, 1), -1.2, rng.uniform(-1, 1)))]
            P.add(tube(q, [.55, .35, .12], 6), V('wooddk', 0, 3, .3, .5))
    for k in range(11):                                                      # hanging tendrils with pods off the braid
        y0 = rng.uniform(Hh * .35, Hh * .8); a = rng.uniform(0, math.tau)
        b = Vector((math.cos(a) * 3.6, y0, math.sin(a) * 3.6)); L = rng.uniform(6, 14)
        pts = [b + Vector((math.cos(a) * math.sin(t * 2) * 1.5, -L * t, math.sin(a) * math.sin(t * 2) * 1.5)) for t in [i / 6 for i in range(7)]]
        P.add(tube(pts, [.3 - .035 * i for i in range(7)], 5, cap0=False), V('wooddk', y0 - L, y0, .3, .5))
        pod = lathe([(0, .3), (.45, 0), (.6, -.6), (.42, -1.3), (0, -1.6)], n=7); P.gadd(T(pod, pts[-1]), 'root')
        for i in (2, 4):
            g = bmesh.new(); bmesh.ops.create_icosphere(g, subdivisions=1, radius=.3); bmesh.ops.translate(g, vec=pts[i] + Vector((.25, 0, 0)), verts=g.verts); P.gadd(g, 'root')
    for k in range(18):                                                      # glowing bulbs studding the braid
        y = rng.uniform(8, Hh * .75); a = rng.uniform(0, math.tau)
        g = bmesh.new(); bmesh.ops.create_icosphere(g, subdivisions=1, radius=1.0); bmesh.ops.scale(g, vec=Vector((.5, .65, .5)) * rng.uniform(.8, 1.4), verts=g.verts)
        bmesh.ops.translate(g, vec=Vector((math.cos(a) * 4.0, y, math.sin(a) * 4.0)), verts=g.verts); P.gadd(g, 'root')
    hc = Vector((0, .2, -6.4))                                               # the HEART pod, front side (sun lands here)
    heart = lathe([(0, 0), (1.6, .3), (2.5, 1.4), (2.7, 2.8), (2.2, 4.2), (1.2, 5.3), (.4, 5.9), (0, 6.1)], n=14)
    for v in heart.verts:
        a = math.atan2(v.co.z, v.co.x); k_ = 1 + .09 * math.cos(a * 7)
        v.co.x *= k_; v.co.z *= k_
    P.gadd(T(heart, hc, s=1.35), 'amber')
    for k in range(6):                                                       # husk petals cradling the heart
        a = k * math.tau / 6 + .3; d = Vector((math.cos(a), 0, math.sin(a)))
        pts = [hc + d * 1.9 + Vector((0, -.2, 0)), hc + d * 4.3 + Vector((0, 2.1, 0)), hc + d * 4.8 + Vector((0, 5.0, 0)), hc + d * 4.0 + Vector((0, 6.6 - (k % 2) * 1.6, 0))]
        pet = tube(pts, [1.3, 1.3, .9, .12], sides=6, flat=(1.0, .28), cap0=False); P.add(pet, V('wooddk', 0, 5, .35, .62, ns=1.5), smooth=True)
    mnd = strata_mass(7.0, 1.6, 6.5, seed, k=6, layers=2, n=2.6, flatb=.9); T(mnd, (0, .1, -1.0))
    P.add(mnd, V('moss', -1.5, 2, .35, .7, ns=3), smooth=True)
    return P

def glowroot_check():
    P = glowroot(); print('GLOWROOT parts', P.solid.tris, {k: v.tris for k, v in P.glow.items()}); return P

# ore v2: better ore piles + cart loads
from cave_ores import ore_pile, ore_lump, druse
