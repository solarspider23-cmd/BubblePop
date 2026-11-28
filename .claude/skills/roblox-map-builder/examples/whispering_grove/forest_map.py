# blender -b --python forest_map.py -> Whispering Grove map (grove_map.blend) + preview renders in previews\
# Roblox space throughout (X east, Y up, Z south; 1 unit = 1 stud). Kit meshes are shared by every instance.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import forest_props as F
from pro_lib import (clean, KM, r2b, nz, clamp, lerp, smooth, grid, ribbon, voronoi_cells, shrink, ccw, ngon_prism, MB, cyl, rock)

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ------------------------------------------------------------------ layout
def chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        out.append(pts[-1]); pts = out
    return pts

PATHS = {   # name: (width, polyline x, z)
    'north': (16, chaikin([(0, -20), (0, -38), (7, -55), (2, -68), (-6, -84), (-2, -100), (0, -114), (0, -126)])),
    'south': (16, chaikin([(0, 22), (-3, 45), (4, 68), (0, 92), (-2, 118)])),
    'west':  (12, chaikin([(-22, 8), (-42, 16), (-58, 13), (-72, 18)])),
    'east':  (12, chaikin([(22, -6), (42, -14), (60, -10), (74, -18)])),
}
STREAM = chaikin([(-104, -46), (-80, -52), (-52, -62), (-24, -58), (0, -66), (28, -72), (56, -66), (84, -74), (104, -70)])
POND = (-108, -42, 15)
HERO = (0, -140)
CAMP = (-90, 20, 24)
GROVE = (92, -24, 22)

def segd(px, pz, pts):
    best = 1e9
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz
        t = clamp(((px - ax) * dx + (pz - az) * dz) / L) if L else 0
        cx, cz = ax + dx * t, az + dz * t
        d = (px - cx) ** 2 + (pz - cz) ** 2
        if d < best: best = d
    return best ** .5

def path_info(x, z):
    """(signed distance past the path edge, path width) for the nearest path"""
    best = (1e9, 0)
    for w, pts in PATHS.values():
        d = segd(x, z, pts) - w / 2
        if d < best[0]: best = (d, w)
    return best

def stream_d(x, z):
    d = segd(x, z, STREAM)
    return min(d, math.hypot(x - POND[0], z - POND[1]) - POND[2] + 4.5)

def H(x, z):
    r = math.hypot(x, z)
    h = (nz(x, 0, z, 46, 1) - .5) * 7 + (nz(x, 0, z, 14, 2) - .5) * 1.6
    rim = smooth((r - 108) / 62) * (1 - .85 * smooth(1 - stream_d(x, z) / 26))   # the stream cuts a valley through the rim
    h += rim * 26 + (nz(x, 3, z, 22, 4) - .5) * 10 * rim
    dh = math.hypot(x - HERO[0], z - HERO[1]); h += 5 * smooth(1 - dh / 48)
    for cx, cz, R in (CAMP, GROVE):
        f = smooth(1 - (math.hypot(x - cx, z - cz) - R * .6) / (R * .6)); h = lerp(h, h * .25, f)
    d, w = path_info(x, z)
    f = smooth(1 - d / 7); h = lerp(h, h * .3 - .12, f)
    h = lerp(h, ELDER_Y, smooth(1 - (dh - 27) / 14))                 # level plateau round the Elder Tree
    fp = smooth(1 - (r - 30) / 14); h = lerp(h, 0, fp)
    ds = stream_d(x, z); h -= 4.4 * smooth(1 - ds / 9.5)
    h = lerp(h, min(h, WATER_Y - 1.4), smooth(1 - (ds - 3.5) / 2.5))   # a bed under the whole water surface
    return h
WATER_Y = -2.9
ELDER_Y = 4.0
CAMS = [(-46, 26), (60, -2), (6, -30)]

def keepout(x, z, m=0.0):
    if abs(x) > 218 or abs(z) > 218: return True
    if path_info(x, z)[0] < m: return True
    if math.hypot(x, z) < 34 + m: return True
    if stream_d(x, z) < 7 + m: return True
    for cx, cz, R in ((HERO[0], HERO[1], 36), CAMP, GROVE):
        if math.hypot(x - cx, z - cz) < R * .75 + m: return True
    return False

# ------------------------------------------------------------------ ground
def ground():
    E = 222; N = 222
    bm = grid(-E, E, -E, E, N, N, H)
    uG, uD, uM = F.PAL.u('grass'), F.PAL.u('dirt'), F.PAL.u('moss')
    def shade(f):
        c = f.calc_center_median(); x, z = c.x, c.z
        d, w = path_info(x, z); ds = stream_d(x, z); r = math.hypot(x, z)
        n = nz(x, 0, z, 6, 7)
        if d < (n - .5) * 3.0 or r < 31 + (n - .5) * 4:
            edge = smooth(1 - abs(d) / 2.2) if r > 31 else 0          # darker, packed rim along each path edge
            return [(uD, clamp(.46 + (nz(x, 1, z, 3, 8) - .5) * .25 + f.normal.y * .1 - edge * .14))] * len(f.loops)
        if ds < 7.5 + (n - .5) * 2:
            return [(uM, clamp(.3 + f.normal.y * .2))] * len(f.loops)
        v = .4 + (nz(x, 2, z, 18, 9) - .5) * .32 + f.normal.y * .14 - smooth((r - 112) / 50) * .1 + (n - .5) * .06
        v -= canopy_shade(x, z) * .2                                   # fake ambient occlusion under tree canopies
        v += smooth(1 - d / 2.0) * .06 if d > 0 else 0                 # trodden lighter grass beside paths
        return [(uG, clamp(v, .06, .92))] * len(f.loops)
    mb = MB(); mb.add(bm, shade)
    me = F.mesh_from('Ground', mb, F.materials()['pal']); ob = bpy.data.objects.new('Ground', me); sub('Ground').objects.link(ob)
    # water: stream ribbon + pond disc
    wm = bpy.data.materials.new('Water'); wm.use_nodes = True
    b = wm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (.05, .3, .55, 1); b.inputs['Roughness'].default_value = .08
    wmb = MB()
    wmb.add(ribbon([(x, WATER_Y, z) for x, z in STREAM], 12.5), lambda f: [(0, 0)] * len(f.loops))
    pond = cyl(POND[2] + 1, .05, sides=24, y0=WATER_Y - .05)
    bmesh.ops.translate(pond, vec=Vector((POND[0], 0, POND[1])), verts=pond.verts)
    pmb = MB(); pmb.add(pond, lambda f: [(0, 0)] * len(f.loops))
    me = F.mesh_from('Stream_Water', wmb, wm); ob = bpy.data.objects.new('Stream_Water', me); sub('Ground').objects.link(ob)
    me = F.mesh_from('Pool_Water', pmb, wm); sub('Ground').objects.link(bpy.data.objects.new('Pool_Water', me))
    return ob

def plaza():
    mb = MB(); rng = random.Random(5)
    for site, poly in voronoi_cells(-30, 30, -30, 30, 3.4, seed=4):
        if max(math.hypot(x, z) for x, z in poly) > 28.5: continue
        p = ccw(shrink(poly, .86))
        bm = ngon_prism(p, -.4, .32 + rng.uniform(-.05, .05), .1)
        mb.add(bm, F.S('stonew', base=.5 + rng.uniform(-.12, .1), up=.15, jit=.02, seed=rng.randint(0, 999)))
    me = F.mesh_from('PlazaPaving', mb, F.materials()['pal']); ob = bpy.data.objects.new('PlazaPaving', me); sub('Ground').objects.link(ob)

# ------------------------------------------------------------------ instancing
LIB = {}
def kit(key, P):
    if key not in LIB: LIB[key] = (F.to_kit(P, KIT), P.tris)
    return LIB[key][0]

COUNT = {}; TRIS = [0]
FOOT = {}
def foot(key):
    """footprint radius = widest point of the prop's geometry within 1 stud of its base"""
    if key not in FOOT:
        r = 0.0
        for me in LIB[key][0].values():
            for v in me.vertices:
                if v.co.z < 1.0: r = max(r, math.hypot(v.co.x, v.co.y))
        FOOT[key] = min(r, 6.0)
    return FOOT[key]
def place(key, P_fn, x, z, yaw=None, s=1.0, sink=.25, y=None, group='Props', rng=None, centre=False):
    """centre=True (soft foliage): sit on the ground at the origin, so a slope never buries the uphill side"""
    meshes = kit(key, P_fn() if callable(P_fn) else P_fn)
    yaw = (rng or random).uniform(0, 360) if yaw is None else yaw
    if y is None and centre: y = H(x, z) - sink * s
    elif y is None:
        fr = foot(key) * s
        y = min([H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [i * math.tau / 8 for i in range(8)]]) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    if key[:3] in ('oak', 'pin', 'bir') or key == 'elder':
        rr = (34 if key == 'elder' else 7.5 * s); TREES.setdefault((int(x // 20), int(z // 20)), []).append((x, z, rr))

def face(x, z, tx, tz):
    """yaw (deg) that turns a prop's -Z front toward (tx, tz)"""
    return math.degrees(math.atan2(-(tx - x), -(tz - z)))

def spread(x, z, r):
    """terrain height range over a footprint: big = a slope that would bury the prop's uphill side"""
    hs = [H(x, z)] + [H(x + math.cos(a) * r, z + math.sin(a) * r) for a in [i * math.tau / 8 for i in range(8)]]
    return max(hs) - min(hs)

PTS = []
def free(x, z, r):
    return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)

def scatter(n, region, r, fn, rng, tries=40, m=0.0):
    done = 0
    for _ in range(n * tries):
        if done >= n: break
        x, z = region(rng)
        if keepout(x, z, m) or not free(x, z, r): continue
        PTS.append((x, z, r)); fn(x, z); done += 1
    return done

# ------------------------------------------------------------------ build
def build():
    rng = random.Random(42)
    def flat(fn, r=2.0, lim=.5):
        return lambda x, z: None if spread(x, z, r) > lim else fn(x, z)      # slopes would bury the uphill side
    plaza()
    for cx_, cz_ in CAMS: PTS.append((cx_, cz_, 7))
    OAK = [lambda s=s: F.oak(s, h=rng.uniform(22, 28), col=('leaf' if s % 2 else 'leaf2')) for s in (101, 102, 103, 104)]
    PINE = [lambda s=s: F.pine(s, h=rng.uniform(28, 34)) for s in (201, 202, 203)]
    BIRCH = [lambda s=s: F.birch(s, h=rng.uniform(22, 27)) for s in (251, 252)]

    # heroes
    place('altar', F.altar, 0, 0, yaw=0, y=0, sink=0, group='Hero')
    place('elder', F.elder_tree, HERO[0], HERO[1], yaw=0, y=ELDER_Y, group='Hero'); PTS.append((HERO[0], HERO[1], 30))
    # bridge across the stream on the north path
    bz = min(((segd(x, z, STREAM), z) for x, z in [(px, pz) for px, pz in PATHS['north'][1]]))[1]
    bx = [p for p in PATHS['north'][1] if abs(p[1] - bz) < 4][0][0]
    by = max(H(bx, bz - 14), H(bx, bz + 14)) - .3
    place('bridge', F.bridge, bx, bz, yaw=-8, y=by, group='Hero')

    # quest camp (west)
    cx, cz, _ = CAMP
    place('board', F.quest_board, -66, 4, yaw=face(-66, 4, -20, 10), sink=.2, group='Camp')
    place('tent1', lambda: F.tent(1), cx - 12, cz + 12, yaw=face(cx - 12, cz + 12, cx, cz), group='Camp')
    place('tent2', lambda: F.tent(2, w=6, d=7, h=5), cx - 14, cz - 9, yaw=face(cx - 14, cz - 9, cx, cz), group='Camp')
    place('fire', F.campfire, cx + 1, cz + 1, group='Camp', sink=.1)
    for k, a in enumerate((.3, 2.0, 3.9)):
        place('logseat', lambda: F.log(301, L=6, r=.75), cx + 1 + math.cos(a) * 5.2, cz + 1 + math.sin(a) * 5.2,
              yaw=-math.degrees(a) + 90, group='Camp', sink=.3)
    for k, (dx, dz, key, fn) in enumerate(((-2, 18, 'crate', F.crate), (1, 19, 'crate', F.crate), (-5, 21, 'barrel', F.barrel),
                                          (-22, 2, 'barrel', F.barrel), (-21, -2, 'crate', F.crate))):
        place(key, fn, cx + dx, cz + dz, rng=rng, group='Camp', sink=.1); PTS.append((cx + dx, cz + dz, 2))
    for k, (x, z) in enumerate(CAMP_PTS()): PTS.append((x, z, 7 if k < 2 else 3))   # tents are big
    place('sign', F.signpost, -30, -4, yaw=face(-30, -4, 0, 30), group='Camp', sink=.3)

    # glowshroom grove (east)
    gx, gz, _ = GROVE
    place('crystal', lambda: F.crystal_cluster(3, 1.5), gx, gz, group='Grove', sink=.6)
    for k in range(9):
        a = k * math.tau / 9 + .2; d = 11 + rng.uniform(-1.2, 1.2)
        place('gshroom%d' % (k % 2), (lambda k=k: F.mushroom(400 + k % 2, 1.0, glow=True)), gx + math.cos(a) * d, gz + math.sin(a) * d,
              s=rng.uniform(2.1, 2.9), group='Grove', rng=rng, sink=.2)
    for k in range(10):
        a = rng.uniform(0, math.tau); d = rng.uniform(15, 22); x, z = gx + math.cos(a) * d, gz + math.sin(a) * d
        if not free(x, z, 2.6): continue                                    # mushrooms never grow into each other
        PTS.append((x, z, 2.6))
        place('rshroom%d' % (k % 2), (lambda k=k: F.mushroom(410 + k % 2, 1.0)), x, z,
              s=rng.uniform(1.2, 2.2), group='Grove', rng=rng, sink=.2)
    PTS.append((gx, gz, 14))

    # lanterns + fences along paths
    for name, side0 in (('south', 1), ('north', -1), ('west', 1), ('east', -1)):
        w, pts = PATHS[name]; L = 0; nxt = 10; side = side0
        for (ax, az), (bx_, bz_) in zip(pts, pts[1:]):
            seg = math.hypot(bx_ - ax, bz_ - az); L += seg
            if L >= nxt:
                tx, tz = (bx_ - ax) / seg, (bz_ - az) / seg; nx_, nz_ = -tz, tx
                px, pz = bx_ + nx_ * side * (w / 2 + 2.2), bz_ + nz_ * side * (w / 2 + 2.2)
                if stream_d(px, pz) > 9 and math.hypot(px, pz) > 31:
                    place('lantern', F.lantern_post, px, pz, yaw=math.degrees(math.atan2(nx_ * side, nz_ * side)) + 90, group='Paths', sink=.3)
                    PTS.append((px, pz, 2))
                side = -side; nxt += 26
    for name in ('west', 'east'):
        w, pts = PATHS[name]
        for i in range(3, len(pts) - 3, 4):
            (ax, az), (bx_, bz_) = pts[i], pts[i + 1]
            tx, tz = bx_ - ax, bz_ - az; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
            for sd in (1, -1):
                px, pz = ax - tz * sd * (w / 2 + 1.2), az + tx * sd * (w / 2 + 1.2)
                if free(px, pz, 4) and spread(px, pz, 4) < .5:                 # one fence per spot; a slope buries the uphill rail
                    PTS.append((px, pz, 4))
                    place('fence', F.fence, px, pz, yaw=math.degrees(math.atan2(-tz, tx)) * -1, group='Paths', sink=.2)

    # forest: dense wall on the rim, clustered groves inside
    def rim_pt(r):
        while True:
            x, z = r.uniform(-218, 218), r.uniform(-218, 218)
            if math.hypot(x, z) > 106: return x, z
    def tree(x, z):
        if abs(x) < 30 and -152 < z < -18: return          # keep the plaza -> Elder Tree vista open
        roll = rng.random()
        if roll < .14: place('birch%d' % rng.randint(0, 1), BIRCH[rng.randint(0, 1)], x, z, s=rng.uniform(.9, 1.25), group='Forest', rng=rng, sink=.5)
        elif roll < .6: place('pine%d' % rng.randint(0, 2), PINE[rng.randint(0, 2)], x, z, s=rng.uniform(.85, 1.35), group='Forest', rng=rng, sink=.6)
        else: place('oak%d' % rng.randint(0, 3), OAK[rng.randint(0, 3)], x, z, s=rng.uniform(.9, 1.4), group='Forest', rng=rng, sink=.6)
    scatter(280, rim_pt, 6.5, tree, rng)                                 # 450k map budget
    centres = []
    for _ in range(400):
        x, z = rng.uniform(-104, 104), rng.uniform(-104, 104)
        if 46 < math.hypot(x, z) < 104 and not keepout(x, z, 8) and all(math.hypot(x - a, z - b) > 30 for a, b in centres): centres.append((x, z))
    for cx_, cz_ in centres:
        k = rng.choice((1, 3, 3, 5))
        scatter(k, lambda r, cx_=cx_, cz_=cz_: (cx_ + r.gauss(0, 7), cz_ + r.gauss(0, 7)), 6, tree, rng, m=4)
        scatter(rng.randint(2, 4), lambda r, cx_=cx_, cz_=cz_: (cx_ + r.gauss(0, 10), cz_ + r.gauss(0, 10)), 2.4,
                flat(lambda x, z: place('bush%d' % rng.randint(0, 2), [lambda: F.bush(501), lambda: F.bush(502, col='leaf2'), lambda: F.bush(503, r=1.8)][rng.randint(0, 2)],
                                   x, z, s=rng.uniform(.8, 1.3), group='Forest', rng=rng, sink=.1, centre=True), 3.0, 1.2), rng, m=1)
    # forest edge: bushes + ferns where the wall meets the clearing
    edge = lambda r: (lambda a, d: (math.cos(a) * d, math.sin(a) * d))(r.uniform(0, math.tau), r.uniform(96, 114))
    scatter(70, edge, 2.6, flat(lambda x, z: place('bush%d' % rng.randint(0, 2), [lambda: F.bush(501), lambda: F.bush(502, col='leaf2'), lambda: F.bush(503, r=1.8)][rng.randint(0, 2)],
                                                x, z, s=rng.uniform(.9, 1.5), group='Forest', rng=rng, sink=.1, centre=True), 3.0, 1.2), rng)
    anywhere = lambda r: (r.uniform(-120, 120), r.uniform(-120, 120))
    scatter(45, edge, 1.8, flat(lambda x, z: place('fern%d' % rng.randint(0, 1), [lambda: F.fern(601), lambda: F.fern(602, s=1.25)][rng.randint(0, 1)], x, z,
                                               s=rng.uniform(.9, 1.4), group='Detail', rng=rng, sink=.1, centre=True), 3.0, 1.0), rng)
    scatter(10, anywhere, 1.8, flat(lambda x, z: place('fern%d' % rng.randint(0, 1), [lambda: F.fern(601), lambda: F.fern(602, s=1.25)][rng.randint(0, 1)], x, z,
                                                  s=rng.uniform(.9, 1.3), group='Detail', rng=rng, sink=.1, centre=True), 3.0, 1.0), rng, m=2)
    # rocks: big near the rim and the stream, small elsewhere
    scatter(30, edge, 7, lambda x, z: place('rock%d' % rng.randint(0, 3), (lambda s=rng.randint(0, 3): F.mossy_rock(700 + s, 3.2)), x, z,
                                            s=rng.uniform(1, 2.2), group='Detail', rng=rng, sink=.5), rng)
    def bank(r):                                                        # rock (r <= 3.8) clear of the 12.5-wide water: no rock over it
        while True:
            x, z = STREAM[r.randint(0, len(STREAM) - 1)]; a = r.uniform(0, math.tau); x, z = x + math.cos(a) * 11, z + math.sin(a) * 11
            if segd(x, z, STREAM) > 10.6 and math.hypot(x - POND[0], z - POND[1]) > POND[2] + 5: return x, z
    scatter(22, bank, 2.5, lambda x, z: place('rock%d' % rng.randint(0, 3), (lambda s=rng.randint(0, 3): F.mossy_rock(700 + s, 3.2)), x, z,
                                              s=rng.uniform(.6, 1.2), group='Detail', rng=rng, sink=.4, centre=True), rng, tries=80, m=-3)   # centre: the ring would reach the stream bed
    scatter(18, anywhere, 2, lambda x, z: place('rock%d' % rng.randint(0, 3), (lambda s=rng.randint(0, 3): F.mossy_rock(700 + s, 3.2)), x, z,
                                                s=rng.uniform(.35, .7), group='Detail', rng=rng, sink=.3), rng, m=2)
    # story groups at path bends: stump + log + mushrooms
    for (x, z) in ((-30, 52), (32, 40), (-40, -40), (42, -42)):
        if keepout(x, z): continue
        place('stump', lambda: F.stump(801), x, z, rng=rng, group='Detail', sink=.3)
        place('log', lambda: F.log(802), x + 6.5, z + 4.5, rng=rng, group='Detail', sink=.3)        # any yaw clears the stump
        for k in range(3):                                                  # ring round the stump, away from the log
            a = math.radians(200 + 50 * k)
            place('rshroom%d' % (k % 2), (lambda k=k: F.mushroom(410 + k % 2, 1.0)), x + math.cos(a) * 3.6, z + math.sin(a) * 3.6, s=rng.uniform(.8, 1.2), group='Detail', rng=rng)
        PTS.append((x, z, 6))
    # meadow flowers along path edges, grass tufts in clumps
    def verge(r):
        name = r.choice(list(PATHS)); w, pts = PATHS[name]; x, z = pts[r.randint(0, len(pts) - 1)]
        a = r.uniform(0, math.tau); d = w / 2 + r.uniform(3, 9); return x + math.cos(a) * d, z + math.sin(a) * d
    scatter(46, verge, 1.4, lambda x, z: place('flower%d' % rng.randint(0, 2), [lambda: F.flower_patch(901, 'red'), lambda: F.flower_patch(902, 'cream'),
                                                                                lambda: F.flower_patch(903, 'cloth')][rng.randint(0, 2)], x, z,
                                               s=rng.uniform(.9, 1.3), group='Detail', rng=rng, sink=0), rng, m=1)
    for _ in range(70):
        cx_, cz_ = rng.uniform(-150, 150), rng.uniform(-150, 150)
        scatter(rng.randint(3, 7), lambda r, cx_=cx_, cz_=cz_: (cx_ + r.gauss(0, 3.5), cz_ + r.gauss(0, 3.5)), .6,
                flat(lambda x, z: place('tuft%d' % rng.randint(0, 1), [lambda: F.grass_tuft(1001), lambda: F.grass_tuft(1002, h=2.4)][rng.randint(0, 1)], x, z,
                                   s=rng.uniform(.8, 1.4), group='Detail', rng=rng, sink=.1, centre=True), 1.5, .8), rng, tries=6, m=.5)
    for _ in range(26):
        x, z = rng.uniform(-110, 110), rng.uniform(-110, 110)
        if not keepout(x, z, 1) and free(x, z, 1.5): PTS.append((x, z, 1.5)); place('rshroom%d' % rng.randint(0, 1), (lambda: F.mushroom(410, 1.0)), x, z, s=rng.uniform(.7, 1.2), group='Detail', rng=rng)
    # water edge: reeds on the banks, lily pads on the pond and slow bends, stepping stones on a side crossing
    for i in range(2, len(STREAM) - 2, 3):
        (ax, az), (bx_, bz_) = STREAM[i], STREAM[i + 1]
        tx, tz = bx_ - ax, bz_ - az; l = math.hypot(tx, tz) or 1; nx_, nz_ = -tz / l, tx / l
        for sd in (1, -1):
            if rng.random() < .55:
                x, z = ax + nx_ * sd * 6.4, az + nz_ * sd * 6.4
                if path_info(x, z)[0] > 2 and free(x, z, 1.5) and spread(x, z, 1.5) < .6:   # steep bank would bury the clump
                    place('reeds%d' % rng.randint(0, 1), [lambda: F.reeds(1101), lambda: F.reeds(1102, n=8)][rng.randint(0, 1)], x, z, group='Water', rng=rng, sink=.4)
                    PTS.append((x, z, 1.5))
    for k in range(9):
        a = k * math.tau / 9 + rng.uniform(-.2, .2)
        x, z = POND[0] + math.cos(a) * (POND[2] + 2), POND[1] + math.sin(a) * (POND[2] + 2)
        if spread(x, z, 1.5) > .6: continue                                # steep bank would bury the clump
        place('reeds%d' % (k % 2), [lambda: F.reeds(1101), lambda: F.reeds(1102, n=8)][k % 2], x, z, group='Water', rng=rng, sink=.4)
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(3, POND[2] - 3)
        place('lily%d' % (k % 2), [lambda: F.lily(1201), lambda: F.lily(1202, n=3)][k % 2], POND[0] + math.cos(a) * d, POND[1] + math.sin(a) * d,
              y=WATER_Y + .02, group='Water', rng=rng)
    for i in (5, 20, 26):
        x, z = STREAM[i]; place('lily%d' % (i % 2), [lambda: F.lily(1201), lambda: F.lily(1202, n=3)][i % 2], x, z, y=WATER_Y + .02, group='Water', rng=rng)
    sx, sz = STREAM[8]
    place('steps', lambda: F.stepping_stones(1301, n=6, gap=2.5), sx, sz, yaw=-12, y=WATER_Y - .1, group='Water')
    # pebbles along the path verges
    for name, (w, pts) in PATHS.items():
        for i in range(0, len(pts) - 1, 2):
            if rng.random() < .5: continue
            (ax, az), (bx_, bz_) = pts[i], pts[i + 1]
            tx, tz = bx_ - ax, bz_ - az; l = math.hypot(tx, tz) or 1; sd = rng.choice((1, -1))
            x, z = ax - tz / l * sd * (w / 2 + .6), az + tx / l * sd * (w / 2 + .6)
            if math.hypot(x, z) > 30 and stream_d(x, z) > 8 and free(x, z, .8):
                place('rock%d' % rng.randint(0, 3), (lambda s=rng.randint(0, 3): F.mossy_rock(700 + s, 3.2)), x, z, s=rng.uniform(.14, .26),
                      group='Detail', rng=rng, sink=.15)

    ground()                                                       # last: it shades under the placed trees

TREES = {}
def canopy_shade(x, z):
    best = 0.0; gx, gz = int(x // 20), int(z // 20)
    for i in (-2, -1, 0, 1, 2):
        for j in (-2, -1, 0, 1, 2):
            for tx, tz, rr in TREES.get((gx + i, gz + j), ()):
                k = 1 - math.hypot(x - tx, z - tz) / rr
                if k > best: best = k
    return smooth(best)

def CAMP_PTS():
    cx, cz, _ = CAMP
    return [(cx - 12, cz + 12), (cx - 14, cz - 9), (cx + 1, cz + 1), (cx - 2, cz + 18), (cx - 22, cz)]

# ------------------------------------------------------------------ look + renders
def look():
    w = bpy.data.worlds.new('Sky'); SC.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    # gradient sky: warm pale horizon -> clear blue zenith
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.05; mr.inputs['From Max'].default_value = .55
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (.86, .86, .78, 1); cr.elements[1].color = (.22, .48, .9, 1)
    e = cr.elements.new(.35); e.color = (.55, .74, .95, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 1.15
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 3.6; sun.data.color = (1, .91, .78); sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(57), math.radians(6), math.radians(-38)); sun.data.color = (1, .87, .7); sun.data.energy = 3.9
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    # haze: a large low-density volume (aerial perspective)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (1300, 1300, 260); hz.location = (0, 0, 110); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; nt = vm.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .0005
    pv.inputs['Color'].default_value = (.82, .92, 1, 1)
    nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 4000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

def horizon():
    """distant faceted mountains + a dark forest-floor skirt so the map never ends in sky"""
    mb = MB(); rng = random.Random(77)
    for k in range(26):
        a = k * math.tau / 26 + rng.uniform(-.08, .08); d = rng.uniform(340, 470); h = rng.uniform(55, 150)
        bm = F.hull(F.rock_pts((rng.uniform(70, 120), h, rng.uniform(60, 100)), n=34, seed=k, flat=.0))
        mb.add(F.at(bm, (math.cos(a) * d, 0, math.sin(a) * d), (0, -math.degrees(a), 0)),
               F.S('pine', grad=(0, h, .18, .5), up=.15, jit=.05, top='stone', thr=.8, topbase=.6, seed=k))
    for cx, cz, sx, sz in ((0, 436, 1300, 428), (0, -436, 1300, 428), (436, 0, 428, 444), (-436, 0, 428, 444)):   # ring outside +-222
        sk = F.box((sx, 1, sz)); F.at(sk, (cx, 14, cz)); mb.add(sk, F.S('pine', base=.2, up=0, jit=0))
    me = F.mesh_from('Horizon', mb, F.materials()['pal']); ob = bpy.data.objects.new('Horizon', me); sub('Ground').objects.link(ob)

build()
horizon()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'grove_map.blend'))
if 'norender' not in ARGS:
    shot('map_spawn.png', (0, 16, 46), (0, 16, -110), 28)
    shot('map_overview.png', (175, 185, 190), (0, -5, -25), 30)
    shot('map_camp.png', (-46, 11, 26), (-90, 4, 16), 30)
    shot('map_grove.png', (60, 11, -2), (92, 4, -24), 30)
    shot('map_elder.png', (6, 12, -30), (0, 30, -140), 26)
    shot('map_door.png', (5, 11, -104), (0, 9, -129), 32)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
