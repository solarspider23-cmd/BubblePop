# blender -b --factory-startup --python battle_map.py [-- norender] [-- name.png ...] -> Riverfield Siege (battle_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: mirrored arena. Two keeps on plateaus (Crimson west,
# Azure east) face each other across a north-south river at x = 0; three lanes cross it: the Sundered Bridge (centre),
# Chapel Isle (north) and the Southern Ford (south, trench lines on both banks). Everything is mirror-symmetric about x = 0.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import battle_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, cyl, box

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

# ------------------------------------------------------------------ layout constants (west side; east mirrors x -> -x)
KX, K_Y, KH = 255.0, 16.0, 58.0          # keep centre |x|, plateau height, plateau half size
WALL = 48.0                               # wall centre-line half size (outer face 51, inner 45)
WATER = -1.2
ISLE = (0.0, -142.0)
FORD_Z = 130.0
BRIDGE_Z = 0.0
TEAM = {-1: 'red', 1: 'blue'}

def X(sg, x): return -sg * x               # positions are written for the WEST side (x < 0); sg = -1 west, +1 east
def Yw(sg, yaw): return -sg * yaw

def fordw(z): return smooth(1 - abs(z - FORD_Z) / 34)
def channels(z):
    """[(centre x, half width, bed y)] of the river at z"""
    if z < -76:
        c = 46.0 * smooth((-76 - z) / 40)
        if c < 4: return [(0.0, 19.0, -6.0)]
        w = lerp(19.0, 13.0, smooth((-76 - z) / 40))
        return [(-c, w, -5.5), (c, w, -5.5)]
    return [(0.0, 19.0 + 9.0 * fordw(z), lerp(-6.0, -2.3, fordw(z)))]

# trench lines (west; mirrored), with a crossing gap where the south road passes
TRENCH = [(-100, 42), (-93, 70), (-106, 98), (-94, 126), (-106, 154), (-99, 178)]
TR_GAP = (116.0, 134.0)
def seg_d(px, pz, a, b):
    ax, az = a; bx, bz = b; dx, dz = bx - ax, bz - az
    t = clamp(((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz))
    return math.hypot(px - ax - t * dx, pz - az - t * dz), az + t * dz
def trench_drop(x, z):
    x = -abs(x)
    if not (30 < z < 190 and -125 < x < -75): return 0.0
    d, zz = min(seg_d(x, z, a, b) for a, b in zip(TRENCH, TRENCH[1:]))
    if TR_GAP[0] < zz < TR_GAP[1]: return 0.0
    end = smooth((zz - 42) / 12) * smooth((178 - zz) / 12) * smooth(min(abs(zz - TR_GAP[0]), abs(zz - TR_GAP[1])) / 8)
    return 5.0 * end * (1 - smooth((d - 2.6) / 1.4))

ROADS = {   # west side polylines + width
    'main': ([(-199, 0), (-170, 6), (-130, 9), (-95, 3), (-66, -2), (-54, 0)], 9.0),
    'south': ([(-170, 6), (-170, 50), (-158, 92), (-128, 124), (-90, 126), (-60, 128), (-36, 130)], 7.0),
    'north': ([(-150, 7), (-142, -52), (-112, -104), (-82, -134), (-66, -140)], 6.0),
}
def road_d(x, z):
    x = -abs(x); best = 99.0
    for pts, w in ROADS.values():
        for a, b in zip(pts, pts[1:]):
            d, _ = seg_d(x, z, a, b); best = min(best, d - w / 2)
    return best

def keep_w(x, z):
    m = max(abs(abs(x) - KX), abs(z)); return smooth((KH + 18 - m) / 18)

def base(x, z):
    ax = abs(x)
    y = 2.6 + 11.0 * smooth((ax - 55) / 160)
    y += (nz(x, 0, z, 70, 1) - .5) * 6 * smooth((ax - 64) / 40) * (1 - keep_w(x, z))
    y += (nz(x, 0, z, 30, 2) - .5) * .8
    y += 36 * smooth((abs(z) - 192) / 70) + 32 * smooth((ax - 318) / 70)
    return y

def isle_y(x, z):
    e = math.sqrt((x / 22) ** 2 + ((z - ISLE[1]) / 29) ** 2)
    return 10.0 if e < 1 else 10.0 - 16.0 * smooth((e - 1) / .78)

def H(x, z):
    y = base(x, z)
    y = lerp(y, K_Y, keep_w(x, z))
    for sg in (-1, 1):                                                          # bridge landings
        d = math.hypot(x - sg * 59, (z - BRIDGE_Z) * 1.4)
        y = lerp(y, 3.0, smooth((14 - d) / 6))
    rd = road_d(x, z)
    if rd < 3: y -= .25 * smooth((3 - rd) / 3)                                   # roads sit a touch low (ruts)
    for c, w, bed in channels(z):
        d = abs(x - c); t = smooth((d - .45 * w) / (.55 * w + 10))
        y = min(y, lerp(bed, y, t)) if d < w + 10 else y
    if z < -70: y = max(y, isle_y(x, z))
    y = lerp(y, max(y, WATER + .6), smooth((abs(z) - 196) / 18))               # the river bed rises to a bank at the map ends
    y -= trench_drop(x, z)
    return y

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []
_DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
def cull_hidden(me):
    """drop faces buried inside the prop's own solid parts (block bases inside a wall, merlon feet in the parapet):
    a face whose outside point is enclosed by the mesh (>= 5 of 6 axis rays hit a back face) is never seen. 450k budget"""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); B = BVHTree.FromBMesh(bm); kill = []
    for f in bm.faces:
        if f.normal.z > .5: continue                                        # keep up faces: floors other checks stand on
        p = f.calc_center_median() + f.normal * .03
        if sum(1 for d in _DIRS for h in [B.ray_cast(p, d, 500)] if h[0] is not None and h[1].dot(d) > 0) >= 5: kill.append(f)
    if kill: bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); me.update()
    bm.free()
def kit(key, fn):
    if key not in LIB:
        P = fn(); ms = F.to_kit(P, KIT)
        for me in ms.values():
            if key.endswith('_M'): me.transform(Matrix.Scale(-1, 4, (1, 0, 0))); me.flip_normals()   # true mirror image
            cull_hidden(me)
        LIB[key] = (ms, P.tris)
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
GB = [None]
def Hm(x, z):
    """height of the built ground MESH (4-stud grid) at x, z: props sit on what the player sees, not on the finer H"""
    if GB[0] is None:
        ob = bpy.data.objects.get('Ground_Valley')
        if ob is None: return H(x, z)
        from mathutils.bvhtree import BVHTree
        me = ob.data.copy(); me.transform(ob.matrix_world); bm = bmesh.new(); bm.from_mesh(me); GB[0] = BVHTree.FromBMesh(bm); bpy.data.meshes.remove(me)
    hit = GB[0].ray_cast(r2b((x, 500, z)), Vector((0, 0, -1)), 1000)
    return hit[0].z if hit[0] is not None else H(x, z)
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    meshes = kit(key, fn)
    if y is None:
        fr = foot(key) * s
        hs = [Hm(x, z)] + [Hm(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def wet(x, z, m=0.0): return H(x, z) < WATER + .4 + m
def on_road(x, z, m=0.0): return road_d(x, z) < m

# ------------------------------------------------------------------ ground + water + horizon
def ground_shade(f):
    """column per face (grass / road dirt / ford gravel / under-water mud), value per VERTEX so tones blend smoothly
    (no checker on slopes: steep ground just gets darker grass, rocks are props)"""
    c = f.calc_center_median(); x, z = c.x, c.z
    col = 'grass'; dv = 0.0
    if trench_drop(x, z) > 3.6: col = 'dirt'
    if c.y < WATER - .9: col = 'dirt'
    if abs(z - FORD_Z) < 26 and abs(x) < 30 and c.y < WATER + .2: col = 'stoneg'
    u = FP.PAL.u(col); out = []
    for l in f.loops:
        p = l.vert.co; vx, vy, vz = p.x, p.y, p.z
        if col == 'grass':
            v = .53 + (nz(vx, 0, vz, 40, 3) - .5) * .1 + (nz(vx, 0, vz, 14, 4) - .5) * .03
            v -= .14 * (1 - smooth((vy - WATER) / 3.5))                      # damp, darker toward the water
            if keep_w(vx, vz) > .55 and max(abs(abs(vx) - KX), abs(vz)) > WALL + 3: v -= .04
            rr = road_d(vx, vz)
            if rr < 3: v -= .08 * (1 - rr / 3)                                  # trodden verge
        elif col == 'dirt': v = .48 + (nz(vx, 0, vz, 6, 7) - .5) * .1 - (.18 if vy < WATER else 0)
        else: v = .46 + (nz(vx, 0, vz, 3, 2) - .5) * .2
        out.append((u, clamp(v, .04, .96)))
    return out

def grid_mesh(x0, x1, z0, z1, step, name, group, shade, hf=H):
    nx_, nz_ = int((x1 - x0) / step), int((z1 - z0) / step)
    bm = bmesh.new(); V = [[bm.verts.new((x0 + i * step, hf(x0 + i * step, z0 + j * step), z0 + j * step)) for j in range(nz_ + 1)] for i in range(nx_ + 1)]
    for i in range(nx_):
        for j in range(nz_): bm.faces.new((V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); mb.add(bm, shade, smooth=True)
    me = F.mesh_from(name, mb, F.materials()['pal'])
    ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)

def ground():
    grid_mesh(-336, 336, -216, 216, 4.0, 'Ground_Valley', 'Ground', ground_shade)          # 4-stud grid: 450k map budget
    # horizon skirt: starts exactly on the ground's rectangular edge (same H), rises into ridges, coarse
    bm = bmesh.new(); NA = 128; fs = [1.0, 1.04, 1.1, 1.2, 1.35, 1.55, 1.8, 2.1, 2.5, 3.0, 3.7, 4.6, 5.8]
    def edge(a):
        c, s_ = math.cos(a), math.sin(a); t = min(336 / max(abs(c), 1e-6), 216 / max(abs(s_), 1e-6)); return c * t, s_ * t
    def Hs(x, z, f):
        if f == 1.0: return H(x, z)
        h0 = H(x / f, z / f)
        return h0 + (f - 1) * 40 + (nz(x, 0, z, 160, 3) - .5) * 90 * smooth((f - 1.1) / .8) + 70 * smooth((f - 2.0) / 2.5)
    V = []
    for f in fs:
        row = []
        for k in range(NA):
            ex, ez = edge(k * math.tau / NA); x, z = ex * f, ez * f
            row.append(bm.verts.new((x, Hs(x, z, f), z)))
        V.append(row)
    for i in range(len(V) - 1):
        for k in range(NA): bm.faces.new((V[i][k], V[i][(k + 1) % NA], V[i + 1][(k + 1) % NA], V[i + 1][k]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); ug, us = FP.PAL.u('pine'), FP.PAL.u('stoneg')
    def hs(f):
        c = f.calc_center_median()
        col = ug if c.y < 140 + (nz(c.x, 0, c.z, 90, 2) - .5) * 80 else us
        return [(col, clamp(.38 + (nz(l.vert.co.x, l.vert.co.y, l.vert.co.z, 90, 4) - .5) * .14, .05, .9)) for l in f.loops]
    mb.add(bm, hs, smooth=True)
    me = F.mesh_from('Horizon_Hills', mb, F.materials()['pal']); ob = bpy.data.objects.new('Horizon_Hills', me); sub('Horizon').objects.link(ob)

def roads():
    """roads as smooth ribbon meshes draped on H (+0.08): ragged soft edges and a lighter rut pair, so their
    outline never follows the ground grid (stair steps)"""
    mb = MB(); u = FP.PAL.u('dirt')
    for sg in (-1, 1):
        for name, (pts, w) in ROADS.items():
            P = [Vector((X(sg, x), 0, z)) for x, z in pts]; samp = []
            for a, b in zip(P, P[1:]):
                n = max(1, int((b - a).length / 2.0)); samp += [a.lerp(b, i / n) for i in range(n)]
            samp.append(P[-1])
            sm = [samp[0]] + [(samp[i - 1] + samp[i] * 2 + samp[i + 1]) / 4 for i in range(1, len(samp) - 1)] + [samp[-1]]
            bm = bmesh.new(); rows = []; across = (-1.0, -.6, -.25, .25, .6, 1.0)
            for i, c in enumerate(sm):
                d = (sm[min(i + 1, len(sm) - 1)] - sm[max(i - 1, 0)]); d.y = 0; d.normalize(); nrm = Vector((-d.z, 0, d.x))
                hw = w / 2 + (nz(c.x, 0, c.z, 6, 9) - .5) * 1.6
                row = []
                for t in across:
                    p = c + nrm * hw * t; row.append(bm.verts.new((p.x, H(p.x, p.z) + .1 + (.05 if abs(t) < .9 else 0), p.z)))
                rows.append(row)
            for i in range(len(rows) - 1):
                for j in range(len(across) - 1): bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
            for f in bm.faces:
                f.normal_update()
                if f.normal.y < 0: f.normal_flip()
            def sh(f):
                out = []
                for l in f.loops:
                    p = l.vert.co; v = .5 + (nz(p.x, 0, p.z, 5, 7) - .5) * .12
                    out.append((u, clamp(v, .04, .96)))
                return out
            mb.add(bm, sh, smooth=True)
    me = F.mesh_from('Path_Roads', mb, F.materials()['pal']); ob = bpy.data.objects.new('Path_Roads', me); sub('Ground').objects.link(ob)

def water():
    """4-stud water grid kept only where water shows: a cell needs a corner below the surface and no corner more
    than 5.5 under the bank (water buried deep under the isle / the far banks is cut away, its edge is the bank)"""
    bm = bmesh.new(); st = 4.0; nx_, nz_ = int(164 / st), int(432 / st)
    V = {}; gh = {}
    def v(i, j):
        if (i, j) not in V:
            x, z = -82 + i * st, -216 + j * st; V[i, j] = bm.verts.new((x, WATER, z)); gh[i, j] = Hm(x, z)
        return V[i, j]
    for i in range(nx_):
        for j in range(nz_):
            cs = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
            for c in cs: v(*c)
            hs = [gh[c] for c in cs]
            if min(hs) < WATER + .2 and max(hs) < WATER + 5.5: bm.faces.new([V[c] for c in cs])
    for vv in [vv for vv in bm.verts if not vv.link_faces]: bm.verts.remove(vv)
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); u = FP.PAL.u('water')
    mb.add(bm, lambda f: [(u, .5 + (nz(*f.calc_center_median(), 30, 3) - .5) * .1)] * len(f.loops))
    me = F.mesh_from('River_Water', mb, F.materials()['pal']); ob = bpy.data.objects.new('River_Water', me); sub('River').objects.link(ob)

def courtyard(sg):
    """flagstone courtyard inside a keep (static hardscape)"""
    mb = MB(); rng = random.Random(5 + sg); cx = X(sg, -KX); s = 4.2
    for i in range(-11, 11):
        for j in range(-11, 11):
            x = cx + (i + .5) * s; z = (j + .5) * s
            if max(abs(x - cx), abs(z)) > WALL - 3.4: continue
            mb.add(FP.T(box((s - .18, .3, s - .18)), (x, K_Y - .1, z), rng.uniform(-1.5, 1.5)), FP.S('stoneg', base=.52 + rng.uniform(-.06, .06), up=.08, jit=.01))
    me = F.mesh_from('Hardscape_Court_%s' % TEAM[sg], mb, F.materials()['pal'])
    ob = bpy.data.objects.new(me.name, me); sub('Keep_%s' % TEAM[sg]).objects.link(ob)

# ------------------------------------------------------------------ keeps
def keep(sg):
    team = TEAM[sg]; G = 'Keep_%s' % team
    kx = lambda lx: X(sg, -KX + lx)
    ky = lambda yaw: Yw(sg, yaw)
    for lx, lz in ((-WALL, -WALL), (WALL, -WALL), (WALL, WALL), (-WALL, WALL)):
        place('tower_' + team, lambda: FP.round_tower(team), kx(lx), lz, ky(0), y=K_Y - .3, group=G)
    segs = [(-27.3, 27), (0.0, 27), (27.3, 27)]
    for lc, L in segs:
        place('wall%d_%s' % (L, team), lambda L=L: FP.curtain_wall(float(L), team), kx(lc), -WALL, ky(0), y=K_Y - .2, group=G)
        place('wall%d_%s' % (L, team), lambda L=L: FP.curtain_wall(float(L), team), kx(lc), WALL, ky(180), y=K_Y - .2, group=G)
        place('wall%d_%s' % (L, team), lambda L=L: FP.curtain_wall(float(L), team), kx(-WALL), lc, ky(90), y=K_Y - .2, group=G)
    for lz in (-28.0, 28.0):
        place('wall26_' + team, lambda: FP.curtain_wall(26.0, team), kx(WALL), lz, ky(-90), y=K_Y - .2, group=G)
    place('gate_' + team, lambda: FP.gatehouse(team), kx(WALL), 0, ky(-90), y=K_Y - .2, group=G)
    place('donjon_' + team, lambda: FP.donjon(team), kx(-23), 6.0, ky(-90), y=K_Y - .2, group=G)
    place('donjontop_' + team, lambda: FP.donjon_top(team), kx(-23), 6.0, ky(-90), y=K_Y - .2, group=G)
    def stair():                                                                # east keep: mirrored kit (mirror of the west stair)
        P = FP.wall_stair()
        if sg > 0: P.name += 'M'
        return P
    sk = 'stair_M' if sg > 0 else 'stair'
    place(sk, stair, kx(22), -WALL + 5.5, ky(180), y=K_Y - .05, group=G)
    place(sk, stair, kx(-22), WALL - 5.5, ky(0), y=K_Y - .05, group=G)
    courtyard(sg)
    reserve(kx(0), 0, WALL + 10)
    # courtyard dressing
    place('rack_' + team, lambda: FP.weapon_rack(team), kx(30), -32, ky(90), y=K_Y, group=G)
    place('rack_' + team, lambda: FP.weapon_rack(team), kx(34), 33, ky(90), y=K_Y, group=G)
    for k, lz in enumerate((22.0, 28.0, 34.0)):
        place('dummy_' + team, lambda: FP.training_dummy(team), kx(8 + k * 5), lz - 3, ky(-90 + k * 10), y=K_Y, group=G)
    place('well', FP.well, kx(4), -22, ky(20), y=K_Y, group=G)
    place('supplies1', lambda: FP.supply_pile(1), kx(-40), 38, ky(10), y=K_Y, group=G)
    place('supplies2', lambda: FP.supply_pile(2), kx(38), -40, ky(-30), y=K_Y, group=G)
    place('hay1', lambda: FP.hay_bales(1), kx(-41), -39, ky(30), y=K_Y, group=G)
    place('cart1', lambda: FP.broken_cart(1), kx(-6), -38, ky(80), y=K_Y, group=G)
    for lz in (-8.5, 8.5):
        place('brazier', lambda: FP.brazier(1), kx(36), lz, ky(0), y=K_Y, group=G)
    # attackers' ladders against the outer walls (river side)
    for lz in (-24.0, 31.0):
        place('ladder16', lambda: FP.ladder(17.0, lean=24), kx(WALL + 3.0 + 7.0), lz, ky(90), y=Hm(kx(WALL + 10), lz) - .3, group=G)

# ------------------------------------------------------------------ the Sundered Bridge + Chapel Isle
def centre():
    G = 'Bridge'
    place('bridge', FP.sundered_bridge, 0, BRIDGE_Z, 0, y=0.0, group=G)
    place('bridgetower', FP.bridge_tower, 0, BRIDGE_Z, 0, y=FP.BR_DECK, group=G)
    reserve(0, BRIDGE_Z, 60)
    for sg in (-1, 1):
        place('brazier', lambda: FP.brazier(1), X(sg, -31), BRIDGE_Z + 3.4, 0, y=FP.BR_DECK, group=G)
        place('rubble1', lambda: FP.rubble(1), X(sg, -62), BRIDGE_Z + 15, Yw(sg, 30), group=G)
        place('rubble2', lambda: FP.rubble(2, .8), X(sg, -66), BRIDGE_Z - 14, Yw(sg, -20), group=G)
        place('debris1_' + TEAM[sg], lambda sg=sg: FP.battle_debris(TEAM[sg], 1), X(sg, -74), BRIDGE_Z + 8, Yw(sg, 40), group=G)
        for rx, rz, rr in ((-62, 15, 5), (-66, -14, 4), (-74, 8, 6)): reserve(X(sg, rx), BRIDGE_Z + rz, rr)
    G = 'ChapelIsle'
    place('chapel', FP.ruined_chapel, ISLE[0], ISLE[1] + 2, 180, y=10.0 - .1, group=G)
    reserve(ISLE[0], ISLE[1], 30)
    for sg in (-1, 1):
        place('footbridge', lambda: FP.footbridge(40.0), X(sg, -46), ISLE[1], 0, y=3.0, group=G)
        place('graves1', lambda: FP.gravestones(1), X(sg, -16), ISLE[1] + 17, Yw(sg, 200), group=G)
        place('graves2', lambda: FP.gravestones(2), X(sg, -14), ISLE[1] - 19, Yw(sg, -20), group=G)
        place('deadtree2', lambda: FP.dead_tree(2, 15.0), X(sg, -17), ISLE[1] + 8, Yw(sg, 40), group=G)
        place('boulder2', lambda: FP.boulder(2, 2.6), X(sg, -24), ISLE[1] - 14, Yw(sg, 10), group=G)
        place('rubble3', lambda: FP.rubble(3, .9), X(sg, -13), ISLE[1] - 4, Yw(sg, 60), group=G)

# ------------------------------------------------------------------ the field (west side, mirrored)
FIELD = [   # key, fn(team), x, z, yaw
    ('mantlet1', lambda t: FP.mantlet(t, 1), -92, -22, -90), ('mantlet2', lambda t: FP.mantlet(t, 2), -86, -12, -78),
    ('mantlet1', lambda t: FP.mantlet(t, 1), -60, -56, -96),
    ('cheval', lambda t: FP.cheval(10.0), -66, 52, 80),
    ('drywall14_1', lambda t: FP.drystone_wall(14.0, 1), -170, -92, 30), ('drywall12_2', lambda t: FP.drystone_wall(12.0, 2), -138, -118, 10),
    ('drywall14_3', lambda t: FP.drystone_wall(14.0, 3), -190, 64, -20), ('drywall12_4', lambda t: FP.drystone_wall(12.0, 4), -132, 66, 5),
    ('siegetower', lambda t: FP.siege_tower(t), -134, -36, -90),
    ('ram', lambda t: FP.battering_ram(), -114, -14, -94),                     # off the main road
    ('hay2', lambda t: FP.hay_bales(2), -160, -22, 20), ('hay1', lambda t: FP.hay_bales(1), -100, 46, -40),
    ('cart2', lambda t: FP.broken_cart(2), -124, 22, 40),
    ('debris1', lambda t: FP.battle_debris(t, 1), -98, -40, 0), ('debris2', lambda t: FP.battle_debris(t, 2), -64, 18, 120),
    ('debris3', lambda t: FP.battle_debris(t, 3), -108, 64, 60), ('debris2', lambda t: FP.battle_debris(t, 2), -140, -86, 200),
]
CAMP = [
    ('trebuchet', lambda t: FP.trebuchet(t), -172, 114, -90),               # off the south road ('ammo1', lambda t: FP.ammo_pile(1), -146, 126, 10),
    ('ammo2', lambda t: FP.ammo_pile(2), -164, 96, -30),
    ('tent', lambda t: FP.tent(t), -190, 150, -90), ('tent', lambda t: FP.tent(t), -176, 172, -60), ('tent', lambda t: FP.tent(t), -202, 128, -110),
    ('campfire1', lambda t: FP.campfire(1), -172, 146, 0),
    ('hay2', lambda t: FP.hay_bales(2), -158, 160, 70), ('rack', lambda t: FP.weapon_rack(t), -186, 104, -90),

]
def field(sg, rng):
    team = TEAM[sg]
    for key, fn, x, z, yaw in FIELD + CAMP:
        k = key + ('_' + team if key in ('siegetower', 'trebuchet', 'tent', 'rack') or key.startswith(('mantlet', 'debris')) else '')
        G = 'Camp_' + team if (key, x, z) in [(c[0], c[2], c[3]) for c in CAMP] else 'Field_' + team
        place(k, lambda fn=fn: fn(team), X(sg, x), z, Yw(sg, yaw), group=G)
        reserve(X(sg, x), z, 6.0 if 'tower' not in key else 9.0)
    # SIGNATURE: palisades on the camp-side lip of every trench + along the ford bank, gaps at the crossings
    for a, b in zip(TRENCH, TRENCH[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 11)); seg = L / n
        for i in range(n):
            t = (i + .5) / n; x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if TR_GAP[0] - 6 < z < TR_GAP[1] + 6: continue
            d = Vector((b[0] - a[0], 0, b[1] - a[1])).normalized(); nrm = Vector((-d.z, 0, d.x))
            if nrm.x > 0: nrm = -nrm                                           # camp side (west)
            px, pz = x + nrm.x * 5.6, z + nrm.z * 5.6
            yaw = face(px, pz, px - nrm.x, pz - nrm.z) + 180                     # stakes lean out toward the trench / river
            place('palisade%d' % int(seg), lambda seg=seg: FP.palisade(round(seg), 1), X(sg, px), pz, Yw(sg, yaw), group='Trench_' + team)
            for off, yy in ((2.9, 0.0),) if i % 2 == 0 else ():  # wattle revetment on every other segment + duckboards (450k budget)
                wx, wz = x + nrm.x * off, z + nrm.z * off
                place('wattle%d' % int(seg), lambda seg=seg: FP.wattle(round(seg)), X(sg, wx), wz, Yw(sg, face(wx, wz, x, z)), y=Hm(X(sg, x), z) - .1, group='Trench_' + team)
            place('duckboard', lambda: FP.duckboard(6.0), X(sg, x), z, Yw(sg, face(x, z, x + d.x, z + d.z) + 90), y=Hm(X(sg, x), z) - .05, group='Trench_' + team)
    for z in (96.0, 106.0, 154.0, 164.0):                                       # ford bank palisade
        x = -40.0 - (z - FORD_Z) ** 2 * .004
        place('palisade10', lambda: FP.palisade(10, 2), X(sg, x), z, Yw(sg, -90), group='Ford_' + team); reserve(X(sg, x), z, 6)
    place('cheval', lambda: FP.cheval(10.0), X(sg, -48), 116, Yw(sg, 100), group='Ford_' + team)
    place('cheval', lambda: FP.cheval(10.0), X(sg, -50), 146, Yw(sg, 80), group='Ford_' + team)
    for k, z in enumerate((112.0, 148.0)):
        place('mantlet%d_%s' % (k % 2 + 1, team), lambda k=k: FP.mantlet(team, k % 2 + 1), X(sg, -34), z, Yw(sg, -90), group='Ford_' + team)

TREES = [  # key, builder, footprint radius, weight: four pine forms + oaks, two seeds each, own heights
    ('pine_tall1', lambda: FP.pine(1, 34.0, 'tall'), 5.0, 14), ('pine_tall2', lambda: FP.pine(2, 30.0, 'tall'), 4.5, 10),
    ('pine_full1', lambda: FP.pine(3, 26.0, 'full'), 6.0, 14), ('pine_full2', lambda: FP.pine(4, 22.0, 'full'), 5.5, 12),
    ('pine_squat1', lambda: FP.pine(5, 16.0, 'squat'), 5.0, 8), ('pine_squat2', lambda: FP.pine(6, 13.0, 'squat'), 4.5, 6),
    ('pine_young1', lambda: FP.pine(7, 12.0, 'young'), 3.0, 8), ('pine_young2', lambda: FP.pine(8, 9.0, 'young'), 2.5, 6),
    ('oak1', lambda: FP.broadleaf(1, 18.0), 6.5, 8), ('oak2', lambda: FP.broadleaf(2, 15.0), 6.0, 7), ('oak3', lambda: FP.broadleaf(3, 21.0), 7.0, 6),
]
def tree_pick(rng):
    r = rng.uniform(0, sum(t[3] for t in TREES))
    for key, fn, rad, w in TREES:
        r -= w
        if r <= 0: return key, fn, rad
    return TREES[0][:3]

def scatter(sg, rng):
    team = TEAM[sg]
    def ok(x, z, r, m=4.0): return free(X(sg, x), z, r) and not wet(x, z, 1.0) and not on_road(x, z, m) and trench_drop(x, z) < .1 and keep_w(x, z) < .3
    trees = 0
    for _t in range(900):                                                       # forest belts at the valley rims + flank grove
        x = rng.uniform(-330, -40); z = rng.uniform(-214, 214)
        rim = abs(z) > 176 or x < -300 or (x < -150 and z < -118) or (-226 < x < -186 and abs(z) < 120 and abs(z) > 70)
        if not rim or not ok(x, z, 5, 6): continue
        key, fn, rad = tree_pick(rng); s = rng.uniform(.7, 1.35)
        place(key, fn, X(sg, x), z, rng.uniform(0, 360), s=s, group='Trees_' + team)
        reserve(X(sg, x), z, rad * s); trees += 1
        if trees >= 26: break                                                   # 450k map budget
    for k in range(4):                                                          # lone oaks in the field
        for _t in range(40):
            x = rng.uniform(-185, -55); z = rng.uniform(-160, 175)
            if ok(x, z, 8, 7):
                sd = k % 3 + 1; place('oak%d' % sd, lambda sd=sd: FP.broadleaf(sd, 18.0), X(sg, x), z, rng.uniform(0, 360), s=rng.uniform(.75, 1.3), group='Trees_' + team)
                reserve(X(sg, x), z, 7); break
    for k in range(9):                                                          # dead trees in the field
        for _t in range(40):
            x = rng.uniform(-180, -50); z = rng.uniform(-150, 175)
            if ok(x, z, 6, 6):
                place('deadtree%d' % (k % 3 + 1), lambda k=k: FP.dead_tree(k % 3 + 1, 16.0), X(sg, x), z, rng.uniform(0, 360), s=rng.uniform(.85, 1.2), group='Trees_' + team)
                reserve(X(sg, x), z, 4); break
    for k in range(26):                                                         # boulders (banks, rims, field)
        for _t in range(40):
            x = rng.uniform(-300, -26); z = rng.uniform(-205, 205)
            if ok(x, z, 4, 3):
                place('boulder%d' % (k % 3 + 1), lambda k=k: FP.boulder(k % 3 + 1, 3.0), X(sg, x), z, rng.uniform(0, 360), s=rng.uniform(.7, 1.4), group='Rocks_' + team)
                reserve(X(sg, x), z, 4); break
    for k in range(30):                                                         # bushes in clumps near walls, banks, rims
        for _t in range(40):
            x = rng.uniform(-300, -30); z = rng.uniform(-200, 200)
            if ok(x, z, 2.5, 2):
                place('bush%d' % (k % 3 + 1), lambda k=k: FP.bush(k % 3 + 1, 2.0), X(sg, x), z, rng.uniform(0, 360), s=rng.uniform(.7, 1.2), sink=.1, group='Plants_' + team)
                for j in range(1):
                    a = rng.uniform(0, math.tau); xx, zz = x + math.cos(a) * 3.2, z + math.sin(a) * 3.2
                    if ok(xx, zz, .5, 1): place('tuft%d' % (j + 1), lambda j=j: FP.grass_tuft(j + 1), X(sg, xx), zz, rng.uniform(0, 360), s=rng.uniform(.8, 1.3), group='Plants_' + team)
                reserve(X(sg, x), z, 3); break
    for k in range(15):                                                         # tufts along banks and wall feet
        for _t in range(30):
            x = rng.uniform(-90, -24); z = rng.uniform(-200, 200)
            if ok(x, z, .6, 1) and H(x, z) < 4.5:
                place('tuft%d' % (k % 3 + 1), lambda k=k: FP.grass_tuft(k % 3 + 1), X(sg, x), z, rng.uniform(0, 360), s=rng.uniform(.8, 1.4), group='Plants_' + team); break

def build():
    ground(); roads(); water()
    for sg in (-1, 1): keep(sg)
    centre()
    for loc, _t, _l in SHOTS.values(): reserve(loc[0], loc[2], 18)
    for sg in (-1, 1):
        field(sg, random.Random(31))
        scatter(sg, random.Random(77))

# ------------------------------------------------------------------ look: storm-break amber dusk
def look():
    w = bpy.data.worlds.new('Dusk'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.85, .58, .36, 1)          # warm amber horizon
    cr.elements[1].position = .5; cr.elements[1].color = (.16, .21, .31, 1)           # slate storm sky
    e = cr.elements.new(.14); e.color = (.5, .45, .44, 1)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .12; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.6; sun.data.color = (1.0, .74, .5); sun.data.angle = math.radians(2.5)
    el = math.radians(24); az = math.radians(215)                                     # from the south-west
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SunFill', bpy.data.lights.new('SunFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .9; fill.data.color = (.55, .65, .9); fill.data.use_shadow = False
    to_f = r2b((.4, .8, .45)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (1500, 1100, 280); hz.location = (0, 0, 120); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00022
    pv.inputs['Color'].default_value = (1.0, .88, .76, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False

MATERIALS = {'grass': 'Grass', 'dirt': 'Ground', 'stone': 'Limestone', 'stoneg': 'Slate', 'slate': 'Slate',
             'wood': 'WoodPlanks', 'wooddk': 'Wood', 'straw': 'Fabric', 'canvas': 'Fabric', 'iron': 'CorrodedMetal',
             'red': 'Fabric', 'blue': 'Fabric', 'brass': 'Metal', 'water': 'Glass', 'pine': 'LeafyGrass'}
MAT_OVERRIDES = {'Horizon_Hills': 'Grass'}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Limestone'] = ('noise', 7.0, .18, .9, 0, .1)
    RM.LOOK['CorrodedMetal'] = ('noise', 4.0, .25, .75, .5, .25)
    RM.LOOK['Glass'] = ('noise', 30.0, .02, .08, 0, .8)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SPAWN = (-238.0, K_Y, 0.0)
SHOTS = {
    'map_spawn.png': ((SPAWN[0], K_Y + 5.5, 0), (0, 30, 0), 26),
    'map_overview.png': ((-330, 210, 330), (0, 0, -10), 24),
    'map_top.png': ((0, 1000, 1), (0, 0, 0), 30),
    'map_bridge.png': ((-62, 16, 46), (0, 18, 0), 28),
    'map_hero.png': ((-58, 12, 40), (0, 34, 0), 26),
    'map_isle.png': ((-88, 22, -96), (0, 10, -142), 28),
    'map_ford.png': ((-150, 20, 180), (-60, 0, 120), 28),
    'map_trench.png': ((-104, 13, 186), (-97, 1, 116), 30),
    'map_keep.png': ((-120, 30, -70), (-240, 20, 0), 28),
    'map_court.png': ((-210, K_Y + 6, -36), (-255, K_Y + 8, 20), 24),
    'map_field.png': ((-170, K_Y + 5, -60), (-60, 4, 10), 26),
    'map_camp.png': ((-122, 14, 182), (-180, 8, 130), 26),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'battle_map.blend'))
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, lens) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, lens)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
