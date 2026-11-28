# blender -b --factory-startup --python canyon_map.py [-- norender] [-- name.png ...] -> Sunspire Canyon Bazaar
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: LINEAR canyon run (one meandering floor, walked
# from south to north), framed by stepped red-rock mesa walls with a walkable first ledge (y 24) on both sides.
#   Spawn Plaza (z 175..235) > Market Gate (z 172) > Market Street (z 70..165, stalls + shade sails) > Palm Oasis
#   (z -30..62, pool, east carved stair up to the ledge) > the Narrows (z -45..-160, rope bridge between the ledges at
#   z -95, west carved stair back down) > Temple Court (z -172..-280) > Temple of the Setting Sun carved in the end wall.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import canyon_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box

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

# ------------------------------------------------------------------ canyon shape
LEDGE = 24.0                     # first strata shelf = walkable ledge on both walls
Z_END = -282.0                   # canyon floor ends at the temple wall
def cx(z): return 9.0 * math.sin((200.0 - z) / 95.0)
def dcx(z): return (cx(z - .5) - cx(z + .5))          # dx per -1 z (walking north)
W_TAB = [(340, 95), (246, 74), (232, 46), (176, 46), (166, 30), (76, 30), (62, 54), (-30, 54), (-46, 26), (-160, 26), (-174, 50), (-400, 50)]
def hw(z):
    for (za, wa), (zb, wb) in zip(W_TAB, W_TAB[1:]):
        if zb <= z <= za: return lerp(wb, wa, smooth((z - zb) / (za - zb)))
    return W_TAB[0][1] if z > W_TAB[0][0] else W_TAB[-1][1]

def shelf1(z, side):
    """walkable ledge width (studs) per wall: wide under the relic kiosk (east, z -60) and at the stair landings"""
    s = 12.0 + 5.0 * nz(z, side * 40, 0, 40, 8)
    if side > 0 and -78 < z < -42: s = max(s, 19.0)
    return s

def levels(z, side):
    k2 = 1 + .14 * (nz(z, side * 7, 0, 70, 3) - .5) * 2
    return 24 + 28 * k2, 24 + 62 * k2 + 10 * (nz(z, side, 2, 90, 9) - .5)

def wall(t, z, side):
    """stepped mesa profile at t studs past the floor edge: riser to the ledge (24), ledge, riser to 52, shelf, riser to
    the mesa top (~86); upper heights wander along z so the skyline is not one ruler line"""
    if t <= 0: return 0.0
    if side == 0:                                                              # back wall: one sheer face (temple carved in it)
        y3 = levels(z, 0)[1] + 6
        return y3 * smooth(t / 9) + (6 * (nz(t, z, 0, 30, 11) - .5) if t > 9 else 0)
    r1, s1 = 3.0, shelf1(z, side)
    s2 = 8.0 + 8.0 * nz(z, side * 3, 1, 55, 5)
    y2, y3 = levels(z, side)
    if t < r1: return LEDGE * smooth(t / r1)
    t -= r1
    if t < s1: return LEDGE
    t -= s1
    if t < 4: return LEDGE + (y2 - LEDGE) * smooth(t / 4)
    t -= 4
    if t < s2: return y2
    t -= s2
    if t < 7: return y2 + (y3 - y2) * smooth(t / 7)
    t -= 7
    return y3 + 6 * (nz(t, z, side, 30, 11) - .5) - 10 * smooth((t - 120) / 60)

def tdist(x, z):
    """(signed distance past the canyon floor edge, side): side +1 east wall, -1 west wall, 0 back wall"""
    d = x - cx(z); ts = abs(d) - hw(z); tb = Z_END - z
    if tb > ts: return tb, 0
    return ts, (1 if d > 0 else -1)

def mouth(z): return 1 - smooth((z - 238) / 34)          # the walls end in open desert south of the spawn

def H(x, z):
    """ONE height function for the ground mesh and all placement"""
    t, side = tdist(x, z)
    floor = .35 * (nz(x, 0, z, 18, 2) - .5)
    if t > -5: floor += 1.2 * smooth((t + 5) / 5)                                  # sand drift at the wall foot
    if z > 236:                                                                    # open dunes past the mouth
        floor += 3.5 * smooth((z - 240) / 50) * nz(x, 0, z, 46, 4) * smooth((abs(x) - 18) / 20)
    if on_paving(x, z): floor = 0.0
    return floor + wall(t, z, side) * (mouth(z) if side != 0 else 1)

# ------------------------------------------------------------------ paths (polylines with widths)
def sight_x(z):
    """spawn -> temple door sightline x at z (kept clear of tall dressing)"""
    return SPAWN[0] + (cx(Z_END + 6) - SPAWN[0]) * (SPAWN[2] - z) / (SPAWN[2] - Z_END - 6)

def path_x(z):
    """main path centre: follows the canyon, swings east round the oasis pool"""
    return cx(z) + 16.0 * smooth((62 - z) / 18) * smooth((z + 40) / 18)
MAIN = [(path_x(z), z) for z in [236 - k * 2.0 for k in range(int((236 + 262) / 2.0) + 1)]]
def main_w(z):
    if z > 175: return 0
    if z > 70: return 14.0
    return 10.0
BRANCHES = [  # (polyline, width)
    ([(path_x(30.0), 30.0), (path_x(30.0) + 14, 26.0), (cx(22) + 44, 22.0)], 7.0),       # oasis -> east stair foot
    ([(path_x(52.0) - 2, 52.0), (cx(46) - 16, 46.0), (cx(40) - 28, 40.0)], 7.0),         # oasis -> trader pavilion
    ([(cx(-150), -150.0), (cx(-146) - 12, -146.0), (cx(-144) - 17, -144.0)], 6.0),       # narrows -> west stair foot
]
PLAZAS = [((0.0, 202.0), 28.0), ((cx(-232), -232.0), 38.0)]              # spawn plaza, temple court (round paving)
def _seg_d2(px, pz, a, b):
    ax, az = a; bx, bz = b; dx, dz = bx - ax, bz - az
    t = clamp(((px - ax) * dx + (pz - az) * dz) / max(1e-9, dx * dx + dz * dz))
    return (px - ax - dx * t) ** 2 + (pz - az - dz * t) ** 2
def on_paving(x, z, m=0.0):
    for (px, pz), r in PLAZAS:
        if (x - px) ** 2 + (z - pz) ** 2 < (r + m) ** 2: return True
    w = main_w(z)
    if w and abs(x - path_x(z)) < w / 2 + m: return True
    for pl, w in BRANCHES:
        for a, b in zip(pl, pl[1:]):
            if _seg_d2(x, z, a, b) < (w / 2 + m) ** 2: return True
    return False

# ------------------------------------------------------------------ instancing (same machinery as the examples)
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; LAMPS = []; HOOKS = []
def kit(key, fn):
    if key not in LIB:
        P = fn(); LIB[key] = (F.to_kit(P, KIT), P.tris)
    return LIB[key][0]
FOOT = {}
def foot(key):
    if key not in FOOT:
        r = 0.0
        for me in LIB[key][0].values():
            for v in me.vertices:
                if v.co.z < .8: r = max(r, math.hypot(v.co.x, v.co.y))
        FOOT[key] = min(r, 9.0)
    return FOOT[key]
WALL = [None]
def under_wall(x, z):
    """True where the built cliff mesh (vertices jittered off H) overhangs the spot: a prop there would stand inside
    the rock with no floor under it (the export's float / clip check)"""
    if WALL[0] is None:
        from mathutils.bvhtree import BVHTree
        ob = bpy.data.objects['Cliff_Walls']; m = ob.data.copy(); m.transform(ob.matrix_world)
        bm = bmesh.new(); bm.from_mesh(m); bpy.data.meshes.remove(m); WALL[0] = BVHTree.FromBMesh(bm); bm.free()
    h = WALL[0].ray_cast(r2b((x, 400, z)), Vector((0, 0, -1)), 800)
    return h[0] is not None and h[0].z > H(x, z) + .8
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props', wallcheck=True):
    meshes = kit(key, fn)
    if y is None:
        wallcheck = wallcheck and not key.startswith(('hoodoo', 'boulder'))       # rocks may bed into the cliff
        if wallcheck and under_wall(x, z): return None                            # never inside / under the cliff
        fr = foot(key) * s
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        if wallcheck and hs[0] - min(hs) > max(2.5, fr): return None              # centre up on the wall face itself: skip
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    return y
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    TRIS[0] += len(me.polygons)
def world(lx, ly, lz, x, y, z, yaw):
    """local prop point -> world (Roblox), same yaw convention as place()"""
    a = math.radians(yaw); c, s = math.cos(a), math.sin(a)
    return (x + c * lx + s * lz, y + ly, z - s * lx + c * lz)
def yaw_face(dx, dz):
    """yaw that turns a prop's -Z front to look along (dx, dz)"""
    return math.degrees(math.atan2(-dx, -dz))

# ------------------------------------------------------------------ ground: canyon floor (smooth sand) + walls (faceted rock)
def ground():
    far = [1600, 1150, 850, 640, 480, 370]
    xs = [-f for f in far] + [x for x in range(-280, -96, 12)] + [x * 2.5 for x in range(-38, 39)] + [x for x in range(100, 281, 12)] + far[::-1]
    zs = [-f for f in far] + [z * 3.0 for z in range(-100, 82)] + [z for z in range(250, 330, 10)] + [z for z in (360, 420, 520, 700, 950, 1300, 1600)]
    def jit(x, z):
        t, _ = tdist(x, z)
        k = smooth((t - .5) / 2.5)
        return (x + (nz(x, 3, z, 7, 1) - .5) * 2.4 * k, z + (nz(x, 7, z, 7, 2) - .5) * 2.4 * k)
    bS, bM = bmesh.new(), bmesh.new(); VS, VM = {}, {}
    def vert(bm, VV, i, j):
        if (i, j) not in VV:
            x, z = xs[i], zs[j]; jx, jz = jit(x, z)
            VV[(i, j)] = bm.verts.new((jx, H(x, z), jz))
        return VV[(i, j)]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            x0, x1, z0, z1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            cxx, czz = (x0 + x1) / 2, (z0 + z1) / 2
            if all(on_paving(x, z, -.3) for x in (x0, x1) for z in (z0, z1)): continue
            rock = max(H(x, z) for x in (x0, x1) for z in (z0, z1)) > 3.0
            bm, VV = (bM, VM) if rock else (bS, VS)
            f = bm.faces.new([vert(bm, VV, i, j), vert(bm, VV, i, j + 1), vert(bm, VV, i + 1, j + 1), vert(bm, VV, i + 1, j)]); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    def shade_floor(f):
        u = FP.PAL.u('sand'); out = []
        for l in f.loops:
            p = l.vert.co
            v = .55 + (nz(p.x, 0, p.z, 26, 3) - .5) * .14 + (nz(p.x, 0, p.z, 5, 4) - .5) * .06 + .05 * smooth(p.y / 2)
            out.append((u, clamp(v, .04, .96)))
        return out
    rng = random.Random(4)
    def shade_rock(f):
        """strata by STEP: riser 1 deep red, riser 2 orange, riser 3 red with a cream cap band; shelf and mesa tops
        warm sand; light gradient up each riser so the bands read horizontal"""
        c = f.calc_center_median(); n = f.normal
        if n.y > .8:
            col = 'cliff2' if c.y > 60 else 'sand'
            return [(FP.PAL.u(col), clamp((.62 if col == 'cliff2' else .46) + n.y * .08 + (nz(c.x, 0, c.z, 30, 6) - .5) * .12, .04, .96))] * len(f.loops)
        _t, side = tdist(c.x, c.z); y2, y3 = levels(c.z, side)
        if c.y < LEDGE - .5: col, a, b = 'cliff', 0.0, LEDGE
        elif c.y < y2 - .5: col, a, b = 'cliff2', LEDGE, y2
        elif c.y < y3 - 5: col, a, b = 'cliff', y2, y3 - 5
        else: col, a, b = 'stone', y3 - 5, y3
        fr = clamp((c.y - a) / max(1, b - a))
        v = (.36 if col == 'cliff' else .42 if col == 'cliff2' else .52) + .14 * fr + .1 * n.y + rng.uniform(-.015, .015)
        return [(FP.PAL.u(col), clamp(v, .04, .96))] * len(f.loops)
    mb = MB(); mb.add(bS, shade_floor, smooth=True); static('Ground_Canyon', mb, 'Ground')
    mb = MB(); mb.add(bM, shade_rock, smooth=False); static('Cliff_Walls', mb, 'Cliffs')

def horizon():
    """distant buttes and mesas all round (flat tops, banded), well outside the playable box: cheap prisms"""
    rng = random.Random(9); mb = MB()
    for k in range(26):
        a = rng.uniform(0, math.tau); r = rng.uniform(700, 1400)
        x, z = math.cos(a) * r, math.sin(a) * r - 40
        if abs(x) < 520 and z < 0: continue                              # keep the sky behind the temple clear
        w = rng.uniform(40, 140); h = rng.uniform(40, 130) * (r / 800)
        poly = [(x + math.cos(i * math.tau / 7 + rng.uniform(-.2, .2)) * w * rng.uniform(.7, 1.1),
                 z + math.sin(i * math.tau / 7 + rng.uniform(-.2, .2)) * w * rng.uniform(.5, .9)) for i in range(7)]
        from pro_lib import ngon_prism, ccw
        g = H(x, z); bm = ngon_prism(ccw(poly), g - 15, g + h)
        for v in bm.verts:
            if v.co.y > g: v.co.x = x + (v.co.x - x) * .78; v.co.z = z + (v.co.z - z) * .78
        u = FP.PAL.u('cliff2' if k % 2 else 'cliff')
        mb.add(bm, lambda f, u=u: [(u, clamp(.5 + .2 * f.normal.y, .04, .96))] * len(f.loops))
    static('Horizon_Buttes', mb, 'Horizon')

# ------------------------------------------------------------------ paving: running-bond flagstones along the paths
def _stones(bm, rows):
    """rows = [(left0, right0, left1, right1)] as Vectors; split each row into stones of random length"""
    rng = random.Random(len(rows))
    for L0, R0, L1, R1 in rows:
        u = 0.0; Wd = (R0 - L0).length
        while u < 1 - 1e-3:
            du = min(1 - u, rng.uniform(2.0, 3.6) / max(Wd, .1))
            if 1 - (u + du) < .08: du = 1 - u
            a0, a1 = L0.lerp(R0, u), L0.lerp(R0, u + du); b0, b1 = L1.lerp(R1, u), L1.lerp(R1, u + du)
            bm.faces.new([bm.verts.new(p) for p in (a0, a1, b1, b0)])
            u += du

def paving():
    bm = bmesh.new(); rows = []
    Y = .1
    pts = [(path_x(z), z) for z in [175 - k * 2.4 for k in range(int((175 + 262) / 2.4))]]
    def rows_of(pl, wf):
        out = []
        for (ax, az), (bx, bz) in zip(pl, pl[1:]):
            d = Vector((bx - ax, 0, bz - az)).normalized(); n = Vector((-d.z, 0, d.x))
            wa, wb = wf(az), wf(bz)
            A = Vector((ax, Y, az)); Bv = Vector((bx, Y, bz))
            out.append((A - n * wa / 2, A + n * wa / 2, Bv - n * wb / 2, Bv + n * wb / 2))
        return out
    rows += rows_of(pts, main_w)
    for pl, w in BRANCHES:
        dense = []
        for a, b in zip(pl, pl[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.4))
            dense += [(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)) for k in range(n)]
        dense.append(pl[-1]); rows += rows_of(dense, lambda z, w=w: w)
    _stones(bm, rows)
    for (px, pz), R in PLAZAS:                                                   # concentric flagstone rings
        r = 0.0; rng = random.Random(int(pz))
        while r < R - .5:
            r1 = min(R, r + 2.6 if r else 2.2)
            n = max(6, int(math.tau * r1 / 3.0)); a0 = rng.uniform(0, 1)
            for k in range(n):
                a, b = a0 + k * math.tau / n, a0 + (k + 1) * math.tau / n
                q = [(r, a), (r1, a), (r1, b), (r, b)] if r else [(0, a), (r1, a), (r1, b)]
                bm.faces.new([bm.verts.new((px + math.cos(aa) * rr, Y + .02, pz + math.sin(aa) * rr)) for rr, aa in q])
            r = r1
    fs = list(bm.faces)
    for f in fs:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.inset_individual(bm, faces=fs, thickness=.1, depth=.08, use_even_offset=True)
    bm.normal_update()
    for f in bm.faces: f.material_index = 1 if f.normal.y > .99 else 0
    rng = random.Random(5)
    def sh(f):
        if not f.material_index: return [(FP.PAL.u('stone'), .3)] * len(f.loops)
        c = f.calc_center_median()
        v = .5 + (FP.h01(round(c.x, 1), 0, round(c.z, 1)) - .5) * .12
        return [(FP.PAL.u('stone'), clamp(v, .04, .96))] * len(f.loops)
    mb = MB(); mb.add(bm, sh); static('Paving_Main', mb, 'Paving')

def medallion():
    """spawn medallion: an inlaid eight-point star of teal and saffron tiles in a cream ring (flush with the paving)"""
    bm = bmesh.new(); x0, z0 = SPAWN[0], SPAWN[2]; Y = .24
    for k in range(16):
        a, b = k * math.tau / 16, (k + 1) * math.tau / 16
        for r0, r1 in ((5.2, 6.4),):
            bm.faces.new([bm.verts.new((x0 + math.cos(aa) * rr, Y, z0 + math.sin(aa) * rr)) for rr, aa in ((r0, a), (r1, a), (r1, b), (r0, b))])
    fs_ring = list(bm.faces)
    for k in range(8):
        a = k * math.tau / 8; am, ap = a - math.pi / 8, a + math.pi / 8
        f = bm.faces.new([bm.verts.new(p) for p in ((x0, Y + .01, z0), (x0 + math.cos(am) * 2.2, Y + .01, z0 + math.sin(am) * 2.2),
                                                    (x0 + math.cos(a) * 4.8, Y + .01, z0 + math.sin(a) * 4.8), (x0 + math.cos(ap) * 2.2, Y + .01, z0 + math.sin(ap) * 2.2))])
        f.material_index = 1 + k % 2
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.12)
    def sh(f):
        c = f.calc_center_median(); r = math.hypot(c.x - x0, c.z - z0)
        if r > 5.0: return [(FP.PAL.u('saffron'), .5 + .1 * f.normal.y)] * len(f.loops)
        a = math.atan2(c.z - z0, c.x - x0) % math.tau
        k = int(((a + math.pi / 8) % math.tau) / (math.tau / 8))
        return [(FP.PAL.u('teal' if k % 2 == 0 else 'saffron'), .55 + .1 * f.normal.y)] * len(f.loops)
    mb = MB(); mb.add(bm, sh); static('Paving_SpawnStar', mb, 'Paving')

# ------------------------------------------------------------------ set pieces + stations
SPAWN = (0.0, 0.0, 226.0)
def hook(name, kind, x, y, z, yaw, note):
    HOOKS.append({'name': name, 'kind': kind, 'pos': [round(x, 2), round(y, 2), round(z, 2)], 'yaw': round(yaw, 1), 'note': note})

def set_pieces():
    # spawn plaza
    reserve(SPAWN[0], SPAWN[2], 7)
    hook('Spawn', 'spawn', SPAWN[0], .3, SPAWN[2], 0, 'SpawnLocation on the star medallion, facing -Z (north) up the canyon')
    place('fountain', FP.spawn_fountain, -17.0, 198.0, 0, y=0, group='SpawnPlaza'); reserve(-17, 198, 10)
    y = place('quest', FP.quest_board, 18.0, 200.0, 110, y=0, group='SpawnPlaza'); reserve(18, 200, 8)
    hook('QuestBoard', 'station', *world(0, 8.75, -.15, 18.0, 0, 200.0, 110), 110, 'blank sign above the board; the 3 cream panels take quest SurfaceGuis')
    LAMPS.append(world(2.5, 5.6, -2.2, 18.0, 0, 200.0, 110))
    for sx in (-1, 1):
        place('palm1', lambda: FP.palm(1, 18.0), sx * 24.0, 220.0, sx * 40, group='SpawnPlaza'); reserve(sx * 24, 220, 3)
    for x, z in ((-12.0, 214.0), (12.0, 214.0), (-26.0, 202.0)):
        yaw = 180 if abs(x) < 20 else -90
        place('lpost', FP.lantern_post, x, z, yaw, y=0, group='SpawnPlaza'); reserve(x, z, 1.5)
        LAMPS.append(world(0, 4.5, -2.0, x, 0, z, yaw))
    # market gate across the canyon + parapet wing walls to the cliffs
    gz = 172.0
    place('gate', FP.market_gate, cx(gz), gz, 0, y=0, group='MarketGate'); reserve(cx(gz), gz, 14)
    for sx in (-1, 1):
        for sz in (-1, 1): LAMPS.append((cx(gz) + sx * 10.0, 8.5, gz + sz * 3.7))
    for sx in (-1, 1):
        x = cx(gz) + sx * 17.0
        while abs(x - cx(gz)) < hw(gz) + 2:
            place('par7', lambda: FP.parapet_niche(7.6), x, gz, 180, group='MarketGate', wallcheck=False); LAMPS.append((x, 2.0, gz + .6))
            x += sx * 8.0                                                         # 7.6-stud niches on an 8 pitch: never overlapping, wing reaches the cliff
    # market street: stalls both sides facing the street, shade sails over it, lantern posts at the gaps
    cloths = ['teal', 'saffron', 'plum']; goods = ['pots', 'fruit', 'sacks']
    for k, z in enumerate((158.0, 138.0, 118.0, 98.0, 80.0)):
        for sx, dz in ((1, 0.0), (-1, -10.0)):
            zz = z + dz
            if zz < 76: continue
            i = (k * 2 + (sx > 0)) % 3; j = (k + (sx < 0)) % 3
            key = 'stall_%s_%s' % (cloths[i], goods[j])
            x = cx(zz) + sx * (hw(zz) - 7.0)
            place(key, lambda c=cloths[i], g=goods[j], s=i + 1: FP.stall(c, s, goods=g), x, zz, 90 * sx, y=None, group='Market')
            reserve(x, zz, 6)
    for z in (148.0, 118.0, 88.0):
        place('sail', lambda: FP.shade_sail(26.0, 12.0, 1), cx(z), z, -math.degrees(math.atan(dcx(z))), y=0, group='Market'); reserve(cx(z), z, 3)
    for z in (163.0, 128.0, 104.0, 72.0):
        for sx in (-1, 1):
            x = cx(z) + sx * 9.5
            place('lpost', FP.lantern_post, x, z, 90 * sx, y=0, group='Market'); reserve(x, z, 1.5)
            LAMPS.append(world(0, 4.5, -2.0, x, 0, z, 90 * sx))
    # oasis: pool, palm grove, trader pavilion (SELL), east carved stair up to the ledge
    px, pz = cx(10) - 8.0, 10.0
    place('pool', lambda: FP.oasis_pool(15.0, 10.0, 1), px, pz, 15, y=0, group='Oasis'); reserve(px, pz, 15)
    tx, tz = cx(40) - 38.0, 40.0
    place('trader', FP.trader_pavilion, tx, tz, -90, group='Oasis'); reserve(tx, tz, 10)
    hook('TraderPavilion', 'station', *world(0, 7.1, -4.6, tx, 0, tz, -90), -90, 'SELL: blank sign on the pavilion front, counter at the street')
    for lx in (-4.0, 4.0): LAMPS.append(world(lx, 7.0, -4.5, tx, 0, tz, -90))
    sz0 = 0.0; sx0 = cx(sz0) + hw(sz0) - 6.0
    place('stairE', lambda: FP.carved_stair(LEDGE, 40.0, 6.0, 10.0, 1), sx0, sz0, 0, y=0, group='Stairs'); reserve(sx0, sz0, 6)
    for zz in (sz0 + 19.5, sz0 - 20.5): LAMPS.append((sx0 - 2.5, (.5 if zz > 0 else LEDGE) + 3.8, zz))
    # the narrows: rope bridge between the ledges, relic kiosk on the east ledge, west stair down
    bz = -95.0
    place('bridge', lambda: FP.rope_bridge(60.0), cx(bz), bz, 90, y=LEDGE, group='Bridge'); reserve(cx(bz), bz, 4)
    kz = -60.0; kx = cx(kz) + hw(kz) + 3.0 + 10.0
    place('kiosk', FP.relic_kiosk, kx, kz, 90, y=LEDGE, group='Ledge'); reserve(kx, kz, 8)
    hook('RelicKiosk', 'station', *world(6.3, 2.6, -5.1, kx, LEDGE, kz, 90), 70, 'PETS / RELICS on the east ledge: blank sign on its stand; glowing relic = pet display spot')
    LAMPS.append((kx, LEDGE + 5.0, kz))
    wz = -124.0; wx0 = cx(wz) - hw(wz) + 6.0
    place('stairW', lambda: FP.carved_stair(LEDGE, 40.0, 6.0, 10.0, 2), wx0, wz, 180, y=0, group='Stairs'); reserve(wx0, wz, 6)
    # temple court: hero, braziers, forge (UPGRADE) on the west side
    tz0 = Z_END + 6.0
    place('temple', FP.sun_temple, cx(tz0), tz0, 180, s=TEMPLE_S, y=0, group='Temple'); reserve(cx(tz0), tz0, 44)
    hook('TempleDoor', 'station', cx(tz0), 4.5 * TEMPLE_S, tz0 + 3.6 * TEMPLE_S, 180, 'REBIRTH / TELEPORT trigger in the glowing doorway (12 x 19.5 opening)')
    for z in (-226.0, -244.0):
        for sx in (-1, 1):
            x = cx(z) + sx * 11.0
            place('brazier', FP.brazier, x, z, 0, y=0, group='Temple'); reserve(x, z, 2); LAMPS.append((x, 5.5, z))
    fx, fz = cx(-205) - 34.0, -205.0
    place('forge', FP.forge_station, fx, fz, -90, group='TempleCourt'); reserve(fx, fz, 10)
    hook('ForgeStation', 'station', *world(-6.0, 4.4, -4.9, fx, 0, fz, -90), -90, 'UPGRADE: blank sign on posts; anvil + glowing hearth')
    LAMPS.append(world(-3.0, 4.5, 2.0, fx, 0, fz, -90))

# ------------------------------------------------------------------ signature edge rhythm: parapet niches
def edge_rhythm():
    """parapet niches along the canyon foot round the plaza + court, and along the lip of both ledges (gaps at the
    stair landings, the bridge and the kiosk)"""
    def run(side, z0, z1, on_ledge, gaps, group):
        z = z0
        while z > z1:
            if not any(a > z > b for a, b in gaps):
                if on_ledge:
                    x = cx(z) + side * (hw(z) + 3.0 + 1.0); y = LEDGE
                else:
                    x = cx(z) + side * (hw(z) - 2.2); y = None
                yaw = 90 * side
                if free(x, z, 3.5):
                    place('par8', lambda: FP.parapet_niche(8.0), x, z, yaw, y=y, group=group)
                    LAMPS.append(world(0, 2.0, -.5, x, y or 0, z, yaw)); reserve(x, z, 3.5)
            z -= 8.4
    for side in (-1, 1):
        run(side, 230, 178, False, [], 'Edges_Plaza')
        run(side, -180, -268, False, [], 'Edges_Court')
        run(side, 60, -26, False, [(26, -26)] if side > 0 else [(52, 28)], 'Edges_Oasis')
    run(1, -24, -150, True, [(-29, -28.9), (-48, -72), (-88, -102), (-137, -146)], 'Edges_Ledge')   # -137..-146: the wall bends over the lip
    run(-1, -60, -160, True, [(-88, -102), (-98, -116)], 'Edges_Ledge')

# ------------------------------------------------------------------ story clusters (2-4, at gaps and bends)
def stories():
    G = 'Stories'
    for x, z, key, fn, yaw in ((cx(150) + 17, 150, 'pots1', lambda: FP.pottery_cluster(1), 200), (cx(128) - 17, 128, 'sacks1', lambda: FP.spice_sacks(1), 30),
                               (cx(108) + 17, 109, 'rugs1', lambda: FP.rug_rack(1), 90), (cx(90) - 17, 89, 'pots2', lambda: FP.pottery_cluster(2), -40),
                               (cx(70) + 16, 66, 'sacks2', lambda: FP.spice_sacks(2), 160), (cx(46) - 22, 48, 'rugs1', lambda: FP.rug_rack(1), -60),
                               (cx(34) - 26, 30, 'pots1', lambda: FP.pottery_cluster(1), 120), (14, 212, 'sacks1', lambda: FP.spice_sacks(1), -110),
                               (-26, 184, 'pots2', lambda: FP.pottery_cluster(2), 60), (cx(-60) + hw(-60) + 8, -44, 'pots1', lambda: FP.pottery_cluster(1), 90),
                               (cx(-80) + hw(-80) + 9, -78, 'rugs1', lambda: FP.rug_rack(1), 90), (cx(-205) - 22, -190, 'sacks2', lambda: FP.spice_sacks(2), -60),
                               (cx(-215) - 24, -222, 'pots2', lambda: FP.pottery_cluster(2), 20)):
        y = LEDGE if z in (-44, -78) else None
        if free(x, z, 2.5): place(key, fn, x, z, yaw, y=y, group=G); reserve(x, z, 3)

TREES = {'palm1': (lambda: FP.palm(1, 18.0)), 'palm2': (lambda: FP.palm(2, 14.0)), 'palm3': (lambda: FP.palm(3, 21.0))}
def nature(rng):
    # palm grove round the pool + along the oasis edge, two at the court entrance
    px, pz = cx(10) - 8.0, 10.0
    for k in range(11):
        for _t in range(20):
            a = rng.uniform(0, math.tau); r = rng.uniform(17, 26)
            x, z = px + math.cos(a) * r * 1.2, pz + math.sin(a) * r
            if free(x, z, 3) and not on_paving(x, z, 1.5) and tdist(x, z)[0] < -3 and abs(x - sight_x(z)) > 12: break
        else: continue
        key = rng.choice(list(TREES)); place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.15), group='Oasis'); reserve(x, z, 3)
    for k in range(16):                                                         # pool-side planting: agave, grass, scrub
        a = k * math.tau / 16 + rng.uniform(-.1, .1); r = rng.uniform(1.08, 1.3)
        x, z = px + math.cos(a) * 15 * r, pz + math.sin(a) * 10 * r
        if not free(x, z, 1.2) or on_paving(x, z, .8): continue
        key, fn = rng.choice((('agave1', lambda: FP.agave(1)), ('agave2', lambda: FP.agave(2)), ('grass1', lambda: FP.dry_grass(1)), ('scrub2', lambda: FP.scrub(2))))
        place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.2), group='Oasis'); reserve(x, z, 1.2)
    for sx in (-1, 1):
        x, z = cx(-176) + sx * 18, -178.0
        place('palm3', TREES['palm3'], x, z, sx * 70, group='TempleCourt'); reserve(x, z, 3)
    # hoodoos: a few on the floor at bends, many on the shelves / mesa tops for the skyline
    for x, z, h, sd in ((cx(66) + 42, 58, 16, 1), (cx(-34) - 40, -30, 13, 2), (cx(-176) + 36, -176, 18, 3), (cx(-172) - 38, -170, 15, 4)):
        place('hoodoo%d' % sd, lambda h=h, sd=sd: FP.hoodoo(sd, h), x, z, rng.uniform(0, 360), group='Rocks'); reserve(x, z, 4)
    n = 0
    for _t in range(900):
        if n >= 22: break
        z = rng.uniform(-300, 230); side = rng.choice((-1, 1))
        t = rng.uniform(22, 60); x = cx(z) + side * (hw(z) + t)
        if H(x, z) < 45: continue
        sd = rng.randint(1, 4)
        place('hoodoo%d' % sd, lambda sd=sd: FP.hoodoo(sd, 16.0), x, z, rng.uniform(0, 360), s=rng.uniform(1.3, 2.4), group='Mesas'); n += 1
    # wall-foot dressing: boulders, scrub, agave, dry grass in clusters of 2-4
    for k in range(60):
        z = rng.uniform(-270, 236); side = rng.choice((-1, 1))
        if 175 > z > 72 and k % 3: continue                                      # market foot is behind the stalls
        cxx = cx(z) + side * (hw(z) - rng.uniform(1.5, 5.0)); czz = z
        for j in range(rng.randint(2, 4)):
            x = cxx + rng.uniform(-2.5, 2.5); zz = czz + rng.uniform(-4, 4)
            if not free(x, zz, 1.2) or on_paving(x, zz, 1.0): continue
            r = rng.random()
            if r < .3: place('boulder%d' % (j % 2 + 1), lambda j=j: FP.boulder(j % 2 + 1, 2.4), x, zz, rng.uniform(0, 360), s=rng.uniform(.5, 1.3), group='Rocks')
            elif r < .55: place('scrub%d' % (j % 2 + 1), lambda j=j: FP.scrub(j % 2 + 1), x, zz, rng.uniform(0, 360), s=rng.uniform(.8, 1.3), group='Nature')
            elif r < .75: place('agave%d' % (j % 2 + 1), lambda j=j: FP.agave(j % 2 + 1), x, zz, rng.uniform(0, 360), s=rng.uniform(.8, 1.2), group='Nature')
            else: place('grass%d' % (j % 2 + 1), lambda j=j: FP.dry_grass(j % 2 + 1), x, zz, rng.uniform(0, 360), s=rng.uniform(.9, 1.4), group='Nature')
            reserve(x, zz, 1.2)
    # ledge dressing (east + west ledges): scrub and boulders against the upper riser
    for k in range(26):
        side = 1 if k % 2 else -1
        z = rng.uniform(-150, 20) if side > 0 else rng.uniform(-160, -80)
        x = cx(z) + side * (hw(z) + 3 + shelf1(z, side) - rng.uniform(1, 3))
        if not free(x, z, 2): continue
        if rng.random() < .5: place('boulder1', lambda: FP.boulder(1, 2.4), x, z, rng.uniform(0, 360), y=LEDGE - .3, s=rng.uniform(.6, 1.2), group='Rocks')
        else: place('scrub1', lambda: FP.scrub(1), x, z, rng.uniform(0, 360), y=LEDGE - .2, group='Nature')
        reserve(x, z, 2)
    # open desert past the mouth: agave + scrub on the dunes
    for k in range(18):
        x = rng.uniform(-90, 90); z = rng.uniform(240, 300)
        if abs(x) < 14 or not free(x, z, 2): continue
        key = rng.choice(('scrub1', 'scrub2', 'agave1', 'grass1'))
        fn = {'scrub1': lambda: FP.scrub(1), 'scrub2': lambda: FP.scrub(2), 'agave1': lambda: FP.agave(1), 'grass1': lambda: FP.dry_grass(1)}[key]
        place(key, fn, x, z, rng.uniform(0, 360), group='Desert'); reserve(x, z, 2)

def build():
    for loc, tgt, _f in SHOTS.values(): reserve(loc[0], loc[2], 3)
    ground(); horizon(); paving(); medallion()
    set_pieces(); edge_rhythm(); stories(); nature(random.Random(21))

# ------------------------------------------------------------------ look: dusk in the canyon
def look():
    w = bpy.data.worlds.new('Dusk'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (1.0, .74, .36, 1)          # warm gold horizon
    cr.elements[1].position = .75; cr.elements[1].color = (.14, .2, .55, 1)           # deep indigo zenith
    e = cr.elements.new(.07); e.color = (1.0, .6, .34, 1)                              # coral band
    e = cr.elements.new(.18); e.color = (.86, .62, .62, 1)
    e = cr.elements.new(.36); e.color = (.42, .48, .82, 1)                                # magenta-plum
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .55
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .1; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 6.5; sun.data.color = (1.0, .74, .46); sun.data.angle = math.radians(2.0)
    el = math.radians(SUN_EL); az = math.radians(SUN_AZ)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = 1.7; fill.data.color = (.42, .5, 1.0); fill.data.use_shadow = False
    to_f = r2b((.4, .65, -.65)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    for k, v in (('volumetric_tile_size', '4'), ('volumetric_end', 2500.0), ('volumetric_start', .5), ('volumetric_distribution', .9), ('volumetric_samples', 64)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (3200, 3200, 600); hz.location = (0, 0, 250); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .000045
    pv.inputs['Color'].default_value = (1.0, .86, .72, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False
    for x, y, z in LAMPS:
        L = bpy.data.objects.new('Lamp', bpy.data.lights.new('Lamp', 'POINT')); L.data.energy = 90; L.data.color = (1, .62, .3)
        L.data.shadow_soft_size = .4; L.data.use_shadow = False; L.location = r2b((x, y, z)); SC.collection.objects.link(L)
    for x, y, z in TEMPLE_LIGHTS:
        L = bpy.data.objects.new('TempleLight', bpy.data.lights.new('TempleLight', 'POINT')); L.data.energy = 9000; L.data.color = (1, .7, .3)
        L.data.shadow_soft_size = 2; L.data.use_shadow = False; L.location = r2b((x, y, z)); SC.collection.objects.link(L)
TEMPLE_S = 1.35                      # hero scaled up so it reads from the spawn through the gate arch
SUN_EL, SUN_AZ = 12.0, 198.0          # low dusk sun from the south-south-west, raking up the canyon onto the temple
TEMPLE_LIGHTS = []

MATERIALS = {'sand': 'Sand', 'stone': 'Sandstone', 'cliff': 'Sandstone', 'cliff2': 'Sandstone', 'terra': 'Slate',
             'wood': 'Wood', 'rope': 'Fabric', 'teal': 'Fabric', 'saffron': 'Fabric', 'plum': 'Fabric', 'water': 'Glass',
             'palm': 'LeafyGrass', 'scrub': 'Grass', 'brass': 'Metal'}
MAT_OVERRIDES = {'Horizon_Buttes': 'SmoothPlastic', 'Paving_Main': 'Limestone', 'Paving_SpawnStar': 'SmoothPlastic',
                 'Cliff_Walls': {'cliff': 'Sandstone', 'cliff2': 'Sandstone', 'stone': 'Sandstone', 'sand': 'Sand'},
                 'Palm': {'wood': 'Wood', 'rope': 'Wood', 'saffron': 'SmoothPlastic', 'terra': 'SmoothPlastic'},
                 'Hoodoo': 'Sandstone', 'Boulder': 'Sandstone', 'Pots': {'terra': 'SmoothPlastic'},
                 'Stall_': {'terra': 'SmoothPlastic', 'stone': 'Sandstone'}, 'SpawnFountain': {'teal': 'SmoothPlastic', 'saffron': 'SmoothPlastic'},
                 'MarketGate': {'teal': 'SmoothPlastic', 'saffron': 'SmoothPlastic', 'terra': 'Brick'},
                 'RelicKiosk': {'teal': 'SmoothPlastic', 'terra': 'Brick'}, 'SunTemple': {'terra': 'Brick', 'saffron': 'SmoothPlastic', 'cliff': 'Sandstone', 'cliff2': 'Sandstone'}}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Sandstone'] = ('noise', 9.0, .16, .9, 0, .1)
    RM.LOOK['Limestone'] = ('noise', 7.0, .12, .9, 0, .1)
    RM.LOOK['Glass'] = ('noise', 30.0, .02, .6, 0, .04)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 8000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SHOTS = {   # vertical FOV (Roblox-style)
    'map_beauty.png': ((16, 34, 268), (-6, 24, -230), 36),
    'map_overview.png': ((150, 230, 330), (0, 0, -40), 42),
    'map_top.png': ((0, 1100, -20), (0, 0, -21), 34),
    'map_spawn.png': ((SPAWN[0], 5.5, SPAWN[2] + 4), (cx(Z_END + 6), 22, Z_END + 6), 60),
    'map_market.png': ((cx(170) + 5, 9, 168), (cx(100), 6, 100), 55),
    'map_oasis.png': ((cx(60) + 22, 12, 58), (cx(5) - 6, 2, 5), 55),
    'map_ledge.png': ((cx(-30) + hw(-30) + 9, LEDGE + 6, -22), (cx(-95), LEDGE + 2, -100), 55),
    'map_bridge.png': ((cx(-60) - 6, 6, -52), (cx(-95), LEDGE, -95), 55),
    'map_temple.png': ((cx(-180) + 6, 7, -176), (cx(-276), 30, -276), 55),
}
TEMPLE_LIGHTS += [(cx(Z_END + 6), 12.0, Z_END + 16.0), (cx(Z_END + 6), 33.0, Z_END + 14.0)]
if __name__ == '__main__':
    build()
    bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
    look()
    if 'nomaterials' not in ARGS: material_skin()
    json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
               'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
    json.dump({'spawn': SPAWN, 'hooks': HOOKS, 'lamps': [[round(c, 2) for c in p] for p in LAMPS], 'sun': {'elevation': SUN_EL, 'azimuth': SUN_AZ}},
              open(os.path.join(HERE, 'hooks.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'canyon_map.blend'))
    print('MAP_STATS', sum(COUNT.values()), TRIS[0])
    if 'norender' not in ARGS:
        only = [a for a in ARGS if a.endswith('.png')]
        for n, (l, t, fov) in SHOTS.items():
            if only and n not in only: continue
            shot(n, l, t, fov)
    print('MAP_OK', sum(COUNT.values()), TRIS[0])
