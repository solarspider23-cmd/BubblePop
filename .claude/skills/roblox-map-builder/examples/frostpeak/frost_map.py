# blender -b --factory-startup --python frost_map.py -> Frostpeak village (frost_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Structure follows the skill's whispering_grove/forest_map.py.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import frost_props as FP
F = FP.G
from pro_lib import (clean, KM, r2b, nz, clamp, lerp, smooth, grid, voronoi_cells, shrink, ccw, ngon_prism, MB, cyl)

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

PATHS = {
    'north': (14, chaikin([(0, -22), (-3, -48), (3, -76), (0, -100), (0, -116)])),
    'south': (16, chaikin([(0, 24), (2, 50), (-2, 78), (0, 104), (0, 132)])),
    'west':  (12, chaikin([(-24, 4), (-50, 9), (-74, 4), (-96, 8)])),
    'east':  (12, chaikin([(24, -4), (48, -10), (66, -14), (80, -18)])),
}
SPIRE = (0, -138); SPIRE_Y = 6.0
POND = (104, -22, 24); POND_Y = -1.6
SPAWN = (0, 76)
CABINS = [(-24, 44), (25, 50), (-25, 76), (24, 84), (-42, -28), (42, -30), (-46, 30), (46, 26), (-64, -14), (-74, 26), (-92, -12), (62, 14)]
CAMS = [(0, 100), (26, 30), (66, 4), (8, -92), (14, 60)]

def segd(px, pz, pts):
    best = 1e9
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz
        t = clamp(((px - ax) * dx + (pz - az) * dz) / L) if L else 0
        d = (px - ax - dx * t) ** 2 + (pz - az - dz * t) ** 2
        if d < best: best = d
    return best ** .5

def path_info(x, z):
    best = (1e9, 0)
    for w, pts in PATHS.values():
        d = segd(x, z, pts) - w / 2
        if d < best[0]: best = (d, w)
    return best

def nearest_path_pt(x, z):
    best = (1e9, None)
    for w, pts in PATHS.values():
        for p in pts:
            d = (p[0] - x) ** 2 + (p[1] - z) ** 2
            if d < best[0]: best = (d, p)
    return best[1]

def H(x, z):
    r = math.hypot(x, z)
    h = (nz(x, 0, z, 50, 1) - .5) * 6 + (nz(x, 0, z, 16, 2) - .5) * 1.4
    rim = smooth((r - 112) / 58)
    h += rim * 34 + (nz(x, 3, z, 20, 4) - .5) * 14 * rim                   # the bowl rises into cliffs
    ds = math.hypot(x - SPIRE[0], z - SPIRE[1]); h += 7 * smooth(1 - ds / 50)
    for cx, cz in CABINS:                                                    # every cabin gets a level pad
        f = smooth(1 - (math.hypot(x - cx, z - cz) - 9) / 6); h = lerp(h, h * .2, f)
    d, w = path_info(x, z)
    h = lerp(h, h * .3 - .1, smooth(1 - d / 6))
    h = lerp(h, SPIRE_Y, smooth(1 - (ds - 20) / 14))                         # spire plateau, path ramps up
    h = lerp(h, 0, smooth(1 - (r - 30) / 12))                                # village square level
    dp = math.hypot(x - POND[0], z - POND[1])
    h = lerp(h, POND_Y - 1.2, smooth(1 - (dp - POND[2] + 2) / 8))           # pond basin
    return h

def keepout(x, z, m=0.0):
    if abs(x) > 218 or abs(z) > 218: return True
    if path_info(x, z)[0] < m: return True
    if math.hypot(x, z) < 32 + m: return True
    if math.hypot(x - POND[0], z - POND[1]) < POND[2] + 3 + m: return True
    if math.hypot(x - SPIRE[0], z - SPIRE[1]) < 26 + m: return True
    if any(math.hypot(x - cx, z - cz) < 12 + m for cx, cz in CABINS): return True
    return False

# ------------------------------------------------------------------ ground
def ground():
    E = 222; N = 222
    bm = grid(-E, E, -E, E, N, N, H)
    uS, uD, uR = F.PAL.u('grass'), F.PAL.u('dirt'), F.PAL.u('stone')
    def shade(f):
        c = f.calc_center_median(); x, z = c.x, c.z
        d, w = path_info(x, z); r = math.hypot(x, z); n = nz(x, 0, z, 6, 7)
        if f.normal.y < .72:                                                # steep faces show rock through the snow
            return [(uR, clamp(.38 + f.normal.y * .25 + (n - .5) * .1))] * len(f.loops)
        if d < (n - .5) * 2.6 or r < 29 + (n - .5) * 4:
            edge = smooth(1 - abs(d) / 2.0) if r > 30 else 0
            return [(uD, clamp(.6 + (nz(x, 1, z, 3, 8) - .5) * .2 + f.normal.y * .1 - edge * .12))] * len(f.loops)
        v = .62 + (nz(x, 2, z, 22, 9) - .5) * .22 + f.normal.y * .12 + (n - .5) * .05
        v -= canopy_shade(x, z) * .22
        v += smooth(1 - d / 2.0) * -.06 if d > 0 else 0                      # slush rim beside paths
        return [(uS, clamp(v, .1, .95))] * len(f.loops)
    mb = MB(); mb.add(bm, shade)
    me = F.mesh_from('Ground', mb, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new('Ground', me))
    ice = MB()
    pond = cyl(POND[2] + 1.5, .3, sides=32, y0=POND_Y - .3)
    bmesh.ops.translate(pond, vec=Vector((POND[0], 0, POND[1])), verts=pond.verts)
    ice.add(pond, F.S('leaf2', base=.55, up=.1, jit=.03, vn=(6, 3, .2)))
    me = F.mesh_from('IceSheet', ice, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new('IceSheet', me))   # solid frozen ice (walked on): not water

def square():
    mb = MB(); rng = random.Random(5)
    for site, poly in voronoi_cells(-30, 30, -30, 30, 3.2, seed=4):
        if max(math.hypot(x, z) for x, z in poly) > 27.5: continue
        bm = ngon_prism(ccw(shrink(poly, .86)), -.4, .3 + rng.uniform(-.05, .05), .1)
        snow = rng.random() < .22
        mb.add(bm, F.S('moss' if snow else 'stonew', base=(.7 if snow else .5 + rng.uniform(-.12, .1)), up=.15, jit=.02, seed=rng.randint(0, 999)))
    me = F.mesh_from('SquarePaving', mb, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new('SquarePaving', me))

# ------------------------------------------------------------------ instancing (same as the grove)
LIB = {}; COUNT = {}; TRIS = [0]; FOOT = {}; PTS = []; TREES = {}
def kit(key, P):
    if key not in LIB: LIB[key] = (F.to_kit(P, KIT), P.tris)
    return LIB[key][0]
def foot(key):
    if key not in FOOT:
        r = 0.0
        for me in LIB[key][0].values():
            for v in me.vertices:
                if v.co.z < 1.0: r = max(r, math.hypot(v.co.x, v.co.y))
        FOOT[key] = min(r, 8.0)
    return FOOT[key]
def place(key, P_fn, x, z, yaw=None, s=1.0, sink=.25, y=None, group='Props', rng=None):
    meshes = kit(key, P_fn() if callable(P_fn) else P_fn)
    yaw = (rng or random).uniform(0, 360) if yaw is None else yaw
    if y is None:
        fr = foot(key) * s
        y = min([H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [i * math.tau / 8 for i in range(8)]]) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    if key.startswith('pine'): TREES.setdefault((int(x // 20), int(z // 20)), []).append((x, z, 7 * s))
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def front_to(x, z, tx, tz):
    """yaw that turns a building's +Z front (its door) toward (tx, tz)"""
    return face(x, z, tx, tz) + 180
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def spread(x, z, r):
    """height range of the terrain over a footprint of radius r: big = a slope that would bury one side of a prop"""
    hs = [H(x, z)] + [H(x + math.cos(a) * r, z + math.sin(a) * r) for a in [i * math.tau / 8 for i in range(8)]]
    return max(hs) - min(hs)
HZ_BVH = [None]
def horizon_d(x, z, y):
    if HZ_BVH[0] is None:
        from mathutils.bvhtree import BVHTree
        ob = bpy.data.objects['Horizon']; HZ_BVH[0] = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    hit = HZ_BVH[0].find_nearest(r2b((x, y, z)))
    return hit[3] if hit[0] is not None else 1e9
def scatter(n, region, r, fn, rng, tries=40, m=0.0):
    done = 0
    for _ in range(n * tries):
        if done >= n: break
        x, z = region(rng)
        if keepout(x, z, m) or not free(x, z, r): continue
        PTS.append((x, z, r)); fn(x, z); done += 1
    return done
def canopy_shade(x, z):
    best = 0.0; gx, gz = int(x // 20), int(z // 20)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for tx, tz, rr in TREES.get((gx + i, gz + j), ()):
                best = max(best, 1 - math.hypot(x - tx, z - tz) / rr)
    return smooth(best)

# ------------------------------------------------------------------ build
def build():
    rng = random.Random(7)
    square()
    for cx_, cz_ in CAMS: PTS.append((cx_, cz_, 14))          # canopies reach ~9 studs: keep cameras clear
    PINE = [lambda s=s: FP.snow_pine(s, h=rng.uniform(26, 34)) for s in (31, 32, 33)]

    # heroes: the roll well in the square, the Frost Spire on its plateau, stalls round the square
    place('well', FP.roll_well, 0, 0, yaw=0, y=.3, group='Hero'); PTS.append((0, 0, 7))
    place('spire', FP.frost_spire, SPIRE[0], SPIRE[1], yaw=0, y=SPIRE_Y, group='Hero'); PTS.append((SPIRE[0], SPIRE[1], 24))
    for k in range(4):
        a = math.radians(45 + 90 * k); x, z = math.cos(a) * 19, math.sin(a) * 19
        place('stall%d' % (k % 2), [lambda: FP.market_stall(4), lambda: FP.market_stall(5, w=6)][k % 2], x, z,
              yaw=front_to(x, z, 0, 0), y=.3, group='Square'); PTS.append((x, z, 5))

    # cabins: on their level pads, doors facing the nearest street point; crates/barrels/lantern by each door
    for i, (cx, cz) in enumerate(CABINS):
        px, pz = nearest_path_pt(cx, cz)
        yaw = front_to(cx, cz, px, pz)
        place('cabin%d' % (i % 3), [lambda: FP.cabin(1), lambda: FP.cabin(2, w=11, d=9, wall_h=6.4), lambda: FP.cabin(3, w=16, d=12, wall_h=7.8)][i % 3],
              cx, cz, yaw=yaw, sink=.4, group='Cabins')
        PTS.append((cx, cz, 11))
        fx, fz = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))      # cabin front (+Z) in world
        rx, rz = math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))     # cabin right (+X) in world
        sx_ = -1 if i % 2 else 1                                  # props by the door corner, lantern on the other side
        ck = 'cabin%d' % (i % 3)
        front = max(v.co.y for me in LIB[ck][0].values() for v in me.vertices if v.co.z < 3.0)   # wall / porch line (+Z front)
        for dx, dfz, key, fn in ((5.4, 7.6, 'crate', F.crate), (8.9, 6.4, 'barrel', F.barrel)):
            if key not in LIB: kit(key, fn())
            dfz = max(dfz, front + foot(key) + .6)                   # never inside the wall / porch
            place(key, fn, cx + rx * dx * sx_ + fx * dfz, cz + rz * dx * sx_ + fz * dfz, rng=rng, group='Cabins', sink=.1)
        place('lantern', F.lantern_post, cx - rx * 6.8 * sx_ + fx * 8.2, cz - rz * 6.8 * sx_ + fz * 8.2,
              yaw=yaw + (180 if sx_ > 0 else 0), group='Cabins', sink=.3)

    # square + street life: benches facing the well, snowmen, sleds by doors
    for k in range(4):
        a = math.radians(90 * k); x, z = math.cos(a) * 10.5, math.sin(a) * 10.5
        if k == 1: continue                                   # keep the south approach to the well open
        place('bench', FP.bench, x, z, yaw=face(x, z, 0, 0) + 180, y=.3, group='Square'); PTS.append((x, z, 2.5))
    for k, (x, z) in enumerate(((14, 36), (-14, -40), (34, 6))):
        if free(x, z, 3) and not keepout(x, z, -8):
            place('snowman', FP.snowman, x, z, yaw=face(x, z, 0, 0) + 180, group='Square', sink=.3); PTS.append((x, z, 3))
    for i, (cx, cz) in enumerate(CABINS[::3]):
        px, pz = nearest_path_pt(cx, cz); yaw = front_to(cx, cz, px, pz)
        fx, fz = math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        place('sled', FP.sled, cx - fz * 12.5 + fx * 5, cz + fx * 12.5 + fz * 5, yaw=yaw + 70, group='Cabins', sink=.1)
    # frozen pond: ice-fishing huts + holes, snowy rocks on the shore
    for k, (dx, dz) in enumerate(((-8, -6), (7, 4), (-2, 12))):
        place('hut', FP.fishing_hut, POND[0] + dx, POND[1] + dz, yaw=rng.uniform(0, 360), y=POND_Y + .02, group='Pond')
    for k in range(9):                                        # snow drifts on the ice + a ring of drift along the shore
        a = rng.uniform(0, math.tau); d = rng.uniform(POND[2] * .5, POND[2] - 4)
        if not free(POND[0] + math.cos(a) * d, POND[1] + math.sin(a) * d, 3.5): continue   # drifts never merge
        PTS.append((POND[0] + math.cos(a) * d, POND[1] + math.sin(a) * d, 3.5))
        place('drift%d' % (k % 2), [lambda: _drift(1), lambda: _drift(2, 3.4)][k % 2], POND[0] + math.cos(a) * d, POND[1] + math.sin(a) * d,
              s=rng.uniform(.6, 1.1), y=POND_Y - .4, group='Pond', rng=rng)
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-.2, .2); d = POND[2] + 4
        place('rock%d' % (k % 3), (lambda s=k % 3: F.mossy_rock(700 + s, 2.6)), POND[0] + math.cos(a) * d, POND[1] + math.sin(a) * d,
              s=rng.uniform(.6, 1.2), group='Pond', rng=rng, sink=.4)

    # street lanterns + fences on the side streets
    for name, side0 in (('south', 1), ('north', -1), ('west', 1), ('east', -1)):
        w, pts = PATHS[name]; L = 0; nxt = 12; side = side0
        for (ax, az), (bx_, bz_) in zip(pts, pts[1:]):
            seg = math.hypot(bx_ - ax, bz_ - az); L += seg
            if L >= nxt:
                tx, tz = (bx_ - ax) / seg, (bz_ - az) / seg; nx_, nz_ = -tz, tx
                px, pz = bx_ + nx_ * side * (w / 2 + 2.0), bz_ + nz_ * side * (w / 2 + 2.0)
                if math.hypot(px, pz) > 30 and free(px, pz, 2):
                    place('lantern', F.lantern_post, px, pz, yaw=math.degrees(math.atan2(nx_ * side, nz_ * side)) + 90, group='Streets', sink=.3)
                    PTS.append((px, pz, 2))
                side = -side; nxt += 24
    for name in ('east', 'north'):
        w, pts = PATHS[name]
        for i in range(4, len(pts) - 4, 4):
            (ax, az), (bx_, bz_) = pts[i], pts[i + 1]
            tx, tz = bx_ - ax, bz_ - az; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
            for sd in (1, -1):
                px, pz = ax - tz * sd * (w / 2 + 1.2), az + tx * sd * (w / 2 + 1.2)
                if free(px, pz, 1.5) and not keepout(px, pz, -6) and spread(px, pz, 4) < .5:   # a slope buries the uphill rail
                    place('fence', F.fence, px, pz, yaw=-math.degrees(math.atan2(-tz, tx)), group='Streets', sink=.2)

    # forest: dense snowy pines on the rising rim, small stands between the houses
    def tree(x, z):
        if abs(x) < 22 and -150 < z < 100: return                          # spawn -> spire vista stays open
        if min(horizon_d(x, z, H(x, z) + h) for h in (2, 12, 24)) < 12: return   # crown would sit in a horizon rock
        place('pine%d' % rng.randint(0, 2), PINE[rng.randint(0, 2)], x, z, s=rng.uniform(.8, 1.35), group='Forest', rng=rng, sink=.6)
    def rim_pt(r):
        while True:
            x, z = r.uniform(-218, 218), r.uniform(-218, 218)
            if math.hypot(x, z) > 104: return x, z
    scatter(380, rim_pt, 7, tree, rng)
    for _ in range(26):
        cx_, cz_ = rng.uniform(-100, 100), rng.uniform(-100, 100)
        if math.hypot(cx_, cz_) > 40:
            scatter(rng.choice((1, 2, 3)), lambda r, cx_=cx_, cz_=cz_: (cx_ + r.gauss(0, 6), cz_ + r.gauss(0, 6)), 6.5, tree, rng, m=4)
    # set dressing: snow-capped rocks, snow drifts, small ice crystals
    edge = lambda r: (lambda a, d: (math.cos(a) * d, math.sin(a) * d))(r.uniform(0, math.tau), r.uniform(92, 116))
    anywhere = lambda r: (r.uniform(-115, 115), r.uniform(-115, 115))
    scatter(34, edge, 4, lambda x, z: place('rock%d' % rng.randint(0, 2), (lambda s=rng.randint(0, 2): F.mossy_rock(700 + s, 3.2)), x, z,
                                            s=rng.uniform(1, 2.3), group='Detail', rng=rng, sink=.5), rng)
    scatter(24, anywhere, 2, lambda x, z: place('rock%d' % rng.randint(0, 2), (lambda s=rng.randint(0, 2): F.mossy_rock(700 + s, 3.2)), x, z,
                                                s=rng.uniform(.35, .7), group='Detail', rng=rng, sink=.3), rng, m=2)
    def drift(x, z):
        if spread(x, z, 6) > .2: return                                   # a slope would bury the drift's uphill side
        place('drift%d' % rng.randint(0, 1), [lambda: _drift(1), lambda: _drift(2, 3.4)][rng.randint(0, 1)], x, z,
              s=rng.uniform(.8, 1.5), group='Detail', rng=rng, sink=.15)
    scatter(40, anywhere, 3, drift, rng, m=1)
    for k in range(7):
        a = k * math.tau / 7 + .4
        place('icec', lambda: F.crystal_cluster(9, .9), SPIRE[0] + math.cos(a) * 28, SPIRE[1] + math.sin(a) * 28, rng=rng, group='Detail', sink=1.6)   # deep: the plateau ramp is steep
    ground()

def _drift(seed=1, r=2.6):
    P = F.Prop('Drift%d' % seed)
    P.add(F.blob(r, seed, n=22, sq=.32), F.S('moss', base=.72, up=.2, jit=.03))
    return P

# ------------------------------------------------------------------ look + renders
def look():
    w = bpy.data.worlds.new('Sky'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.05; mr.inputs['From Max'].default_value = .6
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (.95, .82, .72, 1); cr.elements[1].color = (.2, .38, .78, 1)
    e = cr.elements.new(.3); e.color = (.6, .72, .92, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 3.6; sun.data.color = (1, .82, .62); sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(64), math.radians(4), math.radians(-30))    # low winter sun -> long blue shadows
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (1300, 1300, 260); hz.location = (0, 0, 110); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); nt = vm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .0007; pv.inputs['Color'].default_value = (.85, .9, 1, 1)
    nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False

def horizon():
    mb = MB(); rng = random.Random(77)
    for k in range(28):
        a = k * math.tau / 28 + rng.uniform(-.08, .08); d = rng.uniform(330, 470); h = rng.uniform(80, 190)
        bm = F.hull(F.rock_pts((rng.uniform(70, 120), h, rng.uniform(60, 100)), n=34, seed=k, flat=.0))
        mb.add(F.at(bm, (math.cos(a) * d, 0, math.sin(a) * d), (0, -math.degrees(a), 0)),
               F.S('stone', grad=(0, h, .25, .5), up=.15, jit=.05, top='moss', thr=.45, topbase=.75, seed=k))
    for cx, cz, sx, sz in ((0, 436, 1300, 428), (0, -436, 1300, 428), (436, 0, 428, 444), (-436, 0, 428, 444)):
        sk = F.box((sx, 1, sz)); F.at(sk, (cx, 22, cz)); mb.add(sk, F.S('grass', base=.5, up=0, jit=0))
    me = F.mesh_from('Horizon', mb, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new('Horizon', me))

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 4000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

horizon(); build()                                           # horizon first: the forest keeps clear of its rocks
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'frost_map.blend'))
if 'norender' not in ARGS:
    shot('map_spawn.png', (0, 15, 100), (0, 22, -130), 28)
    shot('map_overview.png', (170, 175, 185), (0, -5, -20), 30)
    shot('map_square.png', (26, 10, 30), (0, 4, 0), 30)
    shot('map_street.png', (14, 8, 60), (-24, 5, 44), 30)
    shot('map_pond.png', (74, 10, 6), (104, 1, -22), 32)
    shot('map_spire.png', (12, 16, -74), (0, 22, -138), 30)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
