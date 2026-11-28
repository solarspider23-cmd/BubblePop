# blender -b --factory-startup --python cave_map.py [-- norender] [-- name.png ...] -> Glowroot Caverns (cave_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: UNDERGROUND hub = branching rooms: one vaulted
# central cavern (the Great Hollow) round a glowing lake, five tunnels to station grottos, all enclosed by a carved
# rock shell (air volume = union of ellipsoids, voxel-remeshed, displaced into layered strata) with ONE opening: the
# sun shaft over the lake. Spawn south, looking north at the sunbeam, the islet and the Glowroot.
import sys, os, math, random, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix, noise as MN
from mathutils.bvhtree import BVHTree
import cave_props3 as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
FXC = bpy.data.collections.new('PreviewFX'); SC.collection.children.link(FXC)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ------------------------------------------------------------------ the plan (air volumes)
SPAWN = (0.0, 60.0)
BEAM_FOOT = (2.0, -30.0)                              # where the sunbeam lands (the Glowroot heart)
SUN_EL = 68.0; SUN_DIR = (0.52, 0.854)                # elevation, horizontal direction TOWARD the sun (south-east)
def sky_at(y):
    k = y / math.tan(math.radians(SUN_EL)); return BEAM_FOOT[0] + SUN_DIR[0] * k, BEAM_FOOT[1] + SUN_DIR[1] * k
SKY = sky_at(95)                                      # where the shaft meets the vault
ISLET = (2.0, -37.0, 9.5)
WATER = -0.4
LAKE = [(2, -36, 30), (-30, -62, 24), (-56, -90, 14), (26, -50, 16)]
FALLS = (-57.0, -99.0)
TUN = {   # name: polyline (centre line at floor level), elliptic section rx 13 / ry 17 centred y 4
    'W': [(-80, -6), (-110, -4), (-140, -2)],
    'E': [(84, 14), (112, 16), (142, 20)],
    'NE': [(58, -56), (76, -84), (94, -116)],
    'N': [(-20, -86), (-22, -120), (-24, -164)],
    'SW': [(-60, 48), (-82, 66), (-104, 86)],
}
GROT = {   # station grottos: centre, radii
    'Camp':  ((-174, 6, 0), (42, 36, 38)),
    'Shop':  ((178, 6, 24), (44, 38, 40)),
    'Forge': ((114, 6, -148), (40, 40, 36)),
    'Lift':  ((-26, 6, -198), (38, 42, 34)),
    'Brew':  ((-124, 6, 104), (34, 32, 32)),
}
CHASM = ((-24, 0, -132), (36, 60, 9))
PIT = (-26.0, -202.0, 5.4)

def shapes():
    """list of ellipsoids (centre, radii) whose union is the cave air"""
    S = [((0, 6, -15), (100, 92, 82)), ((-55, 8, -62), (50, 66, 42)), ((62, 4, 6), (46, 52, 46)), ((0, 4, 58), (40, 34, 30)),
         CHASM]
    for k, y in enumerate((88, 104, 120, 136, 152, 168, 182)):               # sun shaft: slants along the sun line
        r = 18 - k * .6; sx_, sz_ = sky_at(y); S.append(((sx_, y, sz_), (r, 13, r)))
    for (c, r) in GROT.values(): S.append((c, r))
    for pts in TUN.values():
        for a, b in zip(pts, pts[1:]):
            n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 5) + 1
            for i in range(n + 1):
                t = i / n; S.append(((lerp(a[0], b[0], t), 4, lerp(a[1], b[1], t)), (13, 17, 13)))
    for y in (6, -6, -18, -30, -42, -54):                                   # lift shaft
        S.append(((PIT[0], y, PIT[1]), (6.2, 9, 6.2)))
    return S
SHAPES = shapes()
def air(x, y, z, grow=0.0):
    for (cx, cy, cz), (rx, ry, rz) in SHAPES:
        if ((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 + ((z - cz) / (rz + grow)) ** 2 < 1: return True
    return False

# ---- 2D helpers
def seg_d(p, a, b):
    ax, az = a; bx, bz = b; px, pz = p
    vx, vz = bx - ax, bz - az; L2 = vx * vx + vz * vz
    t = clamp(((px - ax) * vx + (pz - az) * vz) / L2) if L2 else 0
    return math.hypot(px - ax - vx * t, pz - az - vz * t)
def poly_d(p, pts): return min(seg_d(p, a, b) for a, b in zip(pts, pts[1:]))
def lake_d(x, z): return min(math.hypot(x - a, z - b) - r for a, b, r in LAKE)
def islet_d(x, z): return math.hypot(x - ISLET[0], z - ISLET[1]) - ISLET[2]
def tunnel_d(x, z): return min(poly_d((x, z), p) for p in TUN.values())
def in_hole(x, z):
    (cx, _, cz), (rx, _, rz) = CHASM
    if ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 < 1: return True
    return math.hypot(x - PIT[0], z - PIT[1]) < PIT[2]

PATHS = [   # (points, width) packed walkways (floor shade + keepout)
    ([(0, 52), (1, 20), (2, -4)], 9.0),
    ([(-6, 44), (-46, 22), (-80, -6), (-140, -2), (-160, 0)], 9.0),
    ([(-14, 50), (-60, 48), (-104, 86), (-118, 98)], 8.0),
    ([(10, 46), (46, 30), (84, 14), (142, 20), (162, 24)], 9.0),
    ([(40, 26), (52, -14), (54, -48), (58, -56), (94, -116), (106, -134)], 9.0),
    ([(54, -48), (34, -74), (2, -82), (-20, -86), (-24, -164), (-26, -184)], 8.0),
]
def path_d(x, z): return min(poly_d((x, z), pts) - w / 2 for pts, w in PATHS)
RAIL = [[(16, 56), (40, 46), (70, 32), (96, 20), (142, 24), (168, 32)],
        [(70, 32), (66, -8), (64, -40), (74, -70), (90, -104), (104, -128)]]

def H(x, z):
    """floor height: gentle cave earth, lake bed carved in, islet raised, nothing in the holes"""
    y = (nz(x, 0, z, 30, 1) - .5) * .7 + (nz(x, 0, z, 8, 2) - .5) * .25
    if path_d(x, z) < 0: y *= .3
    d = lake_d(x, z)
    if d < 6:
        if d < 0: y = -.9 - 4.5 * smooth(-d / 12)
        else: y = lerp(-.9, y, smooth(d / 6))
    elif d < 10: y = max(y, WATER + .15)                                    # shore lip: the water's edge runs under a bank
    di = islet_d(x, z)
    if di < 5: y = max(y, lerp(-1.2, 1.5 + (nz(x, 2, z, 5, 3) - .5) * .4, smooth((5 - di) / 7)))
    return y

# ------------------------------------------------------------------ wall-distance raster (placement)
GX0, GX1, GZ0, GZ1, GS = -236, 240, -250, 150, 2.0
NX, NZ = int((GX1 - GX0) / GS) + 1, int((GZ1 - GZ0) / GS) + 1
DIST = {}
def build_dist():
    """signed distance (studs) to the cave wall at floor level: + inside the air, - inside rock (two-pass chamfer)"""
    INF = 1e9; inside = [[air(GX0 + i * GS, 2.0, GZ0 + j * GS) for j in range(NZ)] for i in range(NX)]
    for sgn in (1, -1):
        d = [[0.0 if inside[i][j] != (sgn > 0) else INF for j in range(NZ)] for i in range(NX)]
        for i in range(NX):
            for j in range(NZ):
                v = d[i][j]
                if i: v = min(v, d[i - 1][j] + GS, (d[i - 1][j - 1] + GS * 1.414) if j else INF)
                if j: v = min(v, d[i][j - 1] + GS)
                if i and j < NZ - 1: v = min(v, d[i - 1][j + 1] + GS * 1.414)
                d[i][j] = v
        for i in range(NX - 1, -1, -1):
            for j in range(NZ - 1, -1, -1):
                v = d[i][j]
                if i < NX - 1: v = min(v, d[i + 1][j] + GS, (d[i + 1][j + 1] + GS * 1.414) if j < NZ - 1 else INF)
                if j < NZ - 1: v = min(v, d[i][j + 1] + GS)
                if i < NX - 1 and j: v = min(v, d[i + 1][j - 1] + GS * 1.414)
                d[i][j] = v
        DIST[sgn] = d
    DIST['in'] = inside
def wd(x, z):
    i = int(round((x - GX0) / GS)); j = int(round((z - GZ0) / GS))
    if not (0 <= i < NX and 0 <= j < NZ): return -50
    return DIST[1][i][j] if DIST['in'][i][j] else -DIST[-1][i][j]
def wgrad(x, z):
    g = Vector((wd(x + 2, z) - wd(x - 2, z), 0, wd(x, z + 2) - wd(x, z - 2)))
    return g.normalized() if g.length > 1e-6 else Vector((1, 0, 0))

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; STATIC_TRIS = {}
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
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant|shroom|fung|spore')
DBG = []; WHY = {}; DEFER = []; DEFER_ON = [True]; PLACED_OBS = []; REJECT = []
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props', mode=None):
    """solid props at once; soft ones (foliage / fungi / vines) deferred and placed against the real geometry"""
    meshes = kit(key, fn)
    pname = next(iter(meshes.values())).name
    if DEFER_ON[0] and SOFT_RE.search(pname):
        DEFER.append((key, fn, x, z, yaw, s, y, sink, group, mode)); return y
    if y is None:
        fr = foot(key) * s
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    obs = []
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob); obs.append(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    PLACED_OBS.append((obs, key))
    return y
def unplace(obs, key):
    for ob in obs: bpy.data.objects.remove(ob)
    COUNT[key] -= 1; TRIS[0] -= LIB[key][1]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def placed_mb(src, x, y, z, yaw):
    """copy a prop part (Roblox-space MB) to its world placement (pieces built into static geometry)"""
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y'); out = MB()
    out.V = [tuple(R @ Vector(v) + Vector((x, y, z))) for v in src.V]; out.F = list(src.F); out.UV = list(src.UV); out.SM = list(src.SM)
    return out
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris
    return ob
ANCHORS = []
def anchor(name, kind, group, x, y, z, yaw=0.0, size=(4, 1, 4), **attrs):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group, 'pos': [round(x, 2), round(y, 2), round(z, 2)], 'yaw': round(yaw % 360, 1),
                    'size': [round(v, 2) for v in size], 'attrs': attrs})
LIGHTS = []                                            # preview point lights = the Roblox PointLights in SETUP.md
def light(x, y, z, col, w, r=1.0): LIGHTS.append((x, y, z, col, w, r))

# ---- geometry check (the exporter's hard placement check, run while placing)
SOLID = [None]; SHELL = [None]
def bvh_of(objs):
    bm = bmesh.new()
    for ob in objs:
        m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    t = BVHTree.FromBMesh(bm); bm.free(); return t
def build_solid():
    SOLID[0] = bvh_of([ob for c in SUB.values() for ob in c.objects if not SOFT_RE.search(ob.data.name)])
DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
def inside(p):
    back = 0
    for d in DIRS:
        hit, nrm, i, dist = SOLID[0].ray_cast(p, d, 400)
        if hit is not None and nrm.dot(d) > 0: back += 1
    return back >= 5
def clip_fail(obs, pname):
    for ob in obs:
        M = ob.matrix_world; vs = ob.data.vertices; step = max(1, len(vs) // 160)
        pts = [M @ vs[i].co for i in range(0, len(vs), step)]
        lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
        body = [q for q in pts if q.z > lo_z + .15 * (hi_z - lo_z)]
        if body and sum(1 for q in body if inside(q)) / len(body) > .015:
            if 'Vine' in pname and len(DBG) < 3: DBG.append([(round(q.z - hi_z, 1)) for q in body if inside(q)][:20])
            return 'inside'
        o = M.translation; lowest = min(q.z for q in pts)
        hit = SOLID[0].ray_cast(Vector((o.x, o.y, lowest + 3)), Vector((0, 0, -1)), 80)
        if hit[0] is not None and lowest - hit[0].z > .8 and not re.search(r'(?i)canopy|vine|ivy|lily', pname): return 'floats'
    return None
def ceil_y(x, z, y0=None):
    """inner shell height above (x, z) by raycast up from the floor (Roblox y)"""
    o = r2b((x, (H(x, z) + 6) if y0 is None else y0, z)); hit, nrm, i, d = SHELL[0].ray_cast(o, Vector((0, 0, 1)), 400)
    return None if hit is None else hit.z
def place_soft(rng):
    DEFER_ON[0] = False
    for key, fn, x, z, yaw, s, y, sink, group, mode in DEFER:
        ok = False
        for t in range(9):
            jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (2 + t * 1.2), rng.uniform(-1, 1) * (2 + t * 1.2))
            xx, zz = x + jx, z + jz; yy = y
            if wd(xx, zz) < 1 or in_hole(xx, zz): continue
            if mode == 'hang':                                                # just under the LOWEST ceiling over the knot
                cs = [ceil_y(xx + math.cos(a) * 1.3, zz + math.sin(a) * 1.3) for a in [k * math.tau / 6 for k in range(6)]] + [ceil_y(xx, zz)]
                if None in cs: continue
                yy = min(cs) - .45
            place(key, fn, xx, zz, yaw, s, yy, sink, group)
            obs, k = PLACED_OBS.pop()
            why = clip_fail(obs, obs[0].data.name)
            if why: WHY[key + ':' + why] = WHY.get(key + ':' + why, 0) + 1; unplace(obs, k); continue
            ok = True; break
        if not ok: REJECT.append((key, round(x), round(z)))
    DEFER_ON[0] = True

# ------------------------------------------------------------------ the rock shell (static)
def union_mesh(grow=0.0, seg=(40, 20)):
    bm = bmesh.new()
    for c, r in SHAPES:
        t = bmesh.new(); bmesh.ops.create_uvsphere(t, u_segments=seg[0], v_segments=seg[1], radius=1)
        bmesh.ops.scale(t, vec=Vector([v + grow for v in r]), verts=t.verts); bmesh.ops.translate(t, vec=Vector(c), verts=t.verts)
        me = bpy.data.meshes.new('t'); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    return bm
def remesh(bm, voxel):
    me = bpy.data.meshes.new('U'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('U', me); SC.collection.objects.link(ob)
    m = ob.modifiers.new('R', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = voxel; m.adaptivity = 0
    sm = ob.modifiers.new('S', 'SMOOTH'); sm.factor = .6; sm.iterations = 3
    dg = bpy.context.evaluated_depsgraph_get(); out = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)
    res = bmesh.new(); res.from_mesh(out); bpy.data.meshes.remove(out); return res

SHELL_OBS = []
def shell():
    """inner cave surface: union of the air ellipsoids, voxel-remeshed (3 studs), displaced along the normal by
    low-frequency noise + horizontal strata ribs (layered limestone), normals flipped INTO the air; faces under the
    floor are dropped (the floor covers them), the shaft is cut open at y 172. Split at y 30: Terrain_Walls
    (reachable, precise collision) and Horizon_Vault (ceiling, no collision)."""
    bm = remesh(union_mesh(), 3.2)
    bm.normal_update()
    for v in bm.verts:
        p = v.co; n = v.normal
        d = MN.noise(p / 22.0) * 3.2 + MN.noise(p / 7.0 + Vector((5, 1, 3))) * 1.0
        d += .9 * math.sin(p.y * math.tau / 5.5 + MN.noise(p / 30) * 2) * (1 - abs(n.y))     # strata ribs on walls
        if p.y < 2: d *= .4
        v.co = p + n * d
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces)); bm.normal_update()
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > 172: kill.append(f); continue
        if not in_hole(c.x, c.z) and c.y < H(c.x, c.z) - 1.5: kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    conv = FP.rim_shade(bm); bm.normal_update()
    U = {k: FP.PAL.u(k) for k in ('rock', 'moss')}
    def col_of(p, n):
        if n.y > .5 and p.y < 50 and nz(p.x, p.y, p.z, 14, 5) > .42: return 'moss'
        return 'rock'
    def sh(f):
        c = f.calc_center_median(); col = col_of(c, f.normal); out = []
        for l in f.loops:
            p = l.vert.co; n = l.vert.normal
            h = p.y - max(H(p.x, p.z), -5)
            v = .4 - .14 * smooth(h / 70) + (nz(p.x, p.y, p.z, 9, 2) - .5) * .16 + .05 * n.y
            cc = conv.get(l.vert, 0)
            if cc > 0: v += .38 * min(1, cc * 5)                                # rim tone on every convex rib
            else: v -= .2 * min(1, -cc * 5)
            if col == 'moss': v = .45 + (nz(p.x, p.y, p.z, 4, 3) - .5) * .3
            out.append((U[col], clamp(v, .05, .95)))
        return out
    lo = bm.copy(); hi = bm
    bmesh.ops.delete(lo, geom=[f for f in lo.faces if f.calc_center_median().y >= 30], context='FACES')
    bmesh.ops.delete(hi, geom=[f for f in hi.faces if f.calc_center_median().y < 30], context='FACES')
    for nm, b, grp in (('Terrain_Walls', lo, 'Shell'), ('Horizon_Vault', hi, 'Vault')):
        loose = [v for v in b.verts if not v.link_faces]; bmesh.ops.delete(b, geom=loose, context='VERTS')
        c2 = b.copy() if nm == 'Terrain_Walls' else None
        mb = MB(); mb.add(b, sh, smooth=True); SHELL_OBS.append(static(nm, mb, grp))
        if c2 is not None:                                                    # preview-only cutaway copy (walls cut at y 12)
            c2.normal_update(); bmesh.ops.delete(c2, geom=[f for f in c2.faces if f.calc_center_median().y > 12], context='FACES')
            mb2 = MB(); mb2.add(c2, sh, smooth=True); me2 = F.mesh_from('CutawayWalls', mb2, F.materials()['pal'])
            CLIP[0] = bpy.data.objects.new('CutawayWalls', me2); FXC.objects.link(CLIP[0]); CLIP[0].hide_render = True
    SHELL[0] = bvh_of(SHELL_OBS)

def crust():
    """outer rock skin (coarse, normals OUT): closes the volume so the sun only enters through the shaft"""
    bm = remesh(union_mesh(9.0, (24, 12)), 10.0)
    kill = [f for f in bm.faces if f.calc_center_median().y > 168]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    mb = MB(); u = FP.PAL.u('rock'); mb.add(bm, lambda f: [(u, .2)] * len(f.loops)); static('Horizon_Crust', mb, 'Crust')

def floor():
    """walkable floor heightfield (3 studs) everywhere under the air + 6 studs into the rock; holes for the chasm and
    the lift shaft (a cell is cut only when all its corners are inside the hole: the rim overhangs, never gaps)"""
    S_ = 3.0
    def axis(a0, a1, f0, f1):                       # 3-stud grid, 1.5 over the lake + shore (smooth shoreline)
        out = [float(a0)]
        while out[-1] < a1: out.append(out[-1] + (1.5 if f0 <= out[-1] < f1 else S_))
        return out
    xs = axis(GX0, GX1, -86, 54); zs = axis(GZ0, GZ1, -112, 4)
    bm = bmesh.new(); VV = {}
    def vert(i, j):
        if (i, j) not in VV: VV[i, j] = bm.verts.new((xs[i], H(xs[i], zs[j]), zs[j]))
        return VV[i, j]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if wd(cx, cz) < -4.5: continue
            if all(in_hole(x, z) for x, z in ((xs[i], zs[j]), (xs[i + 1], zs[j]), (xs[i], zs[j + 1]), (xs[i + 1], zs[j + 1]))): continue
            f = bm.faces.new((vert(i, j), vert(i, j + 1), vert(i + 1, j + 1), vert(i + 1, j))); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    U = {k: FP.PAL.u(k) for k in ('floor', 'sand', 'moss', 'water', 'rock')}
    def cv(p):
        x, z = p.x, p.z; n = nz(x, 0, z, 16, 3); n2 = nz(x, 0, z, 5, 4)
        d = lake_d(x, z) + (nz(x, 0, z, 3, 6) - .5) * 2.4                    # noisy shoreline, never grid steps
        if islet_d(x, z) < -2 and p.y > .2: return 'moss', .5 + (n - .5) * .3
        if d < -6: return 'water', .62 + .2 * smooth(-d / 14) + (n2 - .5) * .1
        if d < 4: return 'sand', .5 + (n2 - .5) * .14 + .2 * smooth(-d / 6)
        if path_d(x, z) < 0: return 'floor', .66 + (n2 - .5) * .12
        if wd(x, z) < 9 and n > .5: return 'moss', .38 + (n2 - .5) * .2
        if wd(x, z) < 0: return 'rock', .16
        if wd(x, z) < 2: return 'rock', .35
        return 'floor', .5 + (n - .5) * .2 + (n2 - .5) * .1
    def sh(f):
        col, _ = cv(f.calc_center_median()); out = []
        for l in f.loops:
            cc, v = cv(l.vert.co)
            out.append((U[col], clamp(v if cc == col else .5, .05, .95)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_CaveFloor', mb, 'Ground')

WATER_OBS = []
def water():
    S_ = 3.0; bm = bmesh.new(); VV = {}
    for i in range(-40, 30):
        for j in range(-40, 6):
            x, z = i * S_, j * S_
            if lake_d(x + S_ / 2, z + S_ / 2) < 6.5 and islet_d(x + S_ / 2, z + S_ / 2) > -3 and wd(x + S_ / 2, z + S_ / 2) > -1.5:   # only over the floor
                vs = []
                for a, b in ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)):
                    if (a, b) not in VV: VV[a, b] = bm.verts.new((a * S_, WATER, b * S_))
                    vs.append(VV[a, b])
                f = bm.faces.new(vs); f.normal_update()
                if f.normal.y < 0: f.normal_flip()
    u = FP.PAL.u('water'); mb = MB(); mb.add(bm, lambda f: [(u, .7)] * len(f.loops))
    WATER_OBS.append(static('Lake_Water', mb, 'Water'))

# ------------------------------------------------------------------ dressing
ROCK_BIG = ['CaveRockA', 'CaveRockB', 'CaveRockF', 'CaveRockC']
ROCK_SMALL = ['CaveRockD', 'CaveRockE', 'CaveRockD']
def put_rock(key, x, z, yaw, s, group='Rocks', y=None):
    w, h, d = FP.rock_dim(key)
    if y is None:
        r = .35 * min(w, d) * s
        y = min([H(x, z)] + [H(x + math.cos(a) * r, z + math.sin(a) * r) for a in [k * math.tau / 8 for k in range(8)]]) + .1 * h * s
    place(key, FP.ROCKS[key], x, z, yaw, s, y, group=group)
    ROCKKEYS.add(key)

def rocks(rng):
    """layered rock masses along every wall foot (big in the hall, small in tunnels), half sunk into the wall,
    leaving tunnel mouths, paths, stations and the spawn clear; a capstone on some"""
    cand = []
    for i in range(0, NX, 2):
        for j in range(0, NZ, 2):
            x, z = GX0 + i * GS, GZ0 + j * GS
            if 1.5 < wd(x, z) < 2.5 and not in_hole(x, z): cand.append((x, z))   # first ring inside the air
    rng.shuffle(cand)
    for x, z in cand:
        small = tunnel_d(x, z) < 15 or any(math.hypot(x - c[0], z - c[2]) < r[0] + 8 for c, r in GROT.values())
        key = rng.choice(ROCK_SMALL if small else ROCK_BIG)
        s = rng.uniform(.6, .9) if small else rng.uniform(.85, 1.3)
        far = math.hypot(x - SPAWN[0], z - SPAWN[1]) > 140 or z < -110
        if far and key + 'Lo' in FP.ROCKS: key += 'Lo'
        w, h, d = FP.rock_dim(key)
        rad = .42 * min(w, d) * s
        g = wgrad(x, z); cx, cz = x + g.x * rad * .05, z + g.z * rad * .05
        if not free(cx, cz, rad * (.9 if small else .55)) or path_d(cx, cz) < rad * .3 or lake_d(cx, cz) < -2: continue
        if math.hypot(cx - SPAWN[0], cz - SPAWN[1]) < 22: continue
        put_rock(key, cx, cz, math.degrees(math.atan2(-g.x, -g.z)) + 180 + rng.uniform(-40, 40), s)
        reserve(cx, cz, rad * (.9 if small else .55))
    for k in range(10):                                                      # shore boulders round the lake
        a = rng.uniform(0, math.tau); c = LAKE[k % len(LAKE)]; r = c[2] + rng.uniform(-1, 2)
        x, z = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r
        if lake_d(x, z) < -3 or path_d(x, z) < 3 or not free(x, z, 4) or wd(x, z) < 6: continue
        put_rock('CaveRockD' if k % 2 else 'CaveRockE', x, z, rng.uniform(0, 360), rng.uniform(.6, 1.0)); reserve(x, z, 4)

def dripstone(rng):
    """stalactites over the whole vault (never low over paths), flowstone curtains near walls, stalagmites on floor"""
    n = 0
    for k in range(1600):
        if n >= 48: break
        x, z = rng.uniform(-150, 200), rng.uniform(-235, 130)
        if wd(x, z) < 4 or in_hole(x, z): continue
        c = ceil_y(x, z)
        if c is None or c > 165: continue
        clear = c - max(H(x, z), WATER)
        key = 'stal%d' % (k % 3)
        L = (16, 11, 7)[k % 3]; s = rng.uniform(.8, 1.3)
        if math.hypot(x - SKY[0], z - SKY[1]) < 24 or math.hypot(x - ISLET[0], z - ISLET[1]) < 20: continue
        if clear - L * s < (16 if path_d(x, z) < 6 else 11): continue
        place(key, (lambda k=k, L=L: FP.stalactite(k % 3 + 1, L, (1.8, 1.4, 1.0)[k % 3], (4, 3, 2)[k % 3])), x, z, rng.uniform(0, 360), s, c + .6, group='Hanging')
        n += 1
    n = 0
    for k in range(800):
        if n >= 7: break
        x, z = rng.uniform(-150, 200), rng.uniform(-235, 130)
        if not 4 < wd(x, z) < 10: continue
        c = ceil_y(x, z)
        if c is None or c - H(x, z) < 26 or c > 165: continue
        g = wgrad(x, z)
        place('curtain%d' % (n % 2), (lambda n=n: FP.flowstone_curtain(n % 2 + 1, 12, 9)), x, z, math.degrees(math.atan2(-g.x, -g.z)) + 90, rng.uniform(.9, 1.3), c + .5, group='Hanging')
        n += 1
    n = 0
    for k in range(1500):
        if n >= 22: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if not 3 < wd(x, z) < 14 or path_d(x, z) < 5 or lake_d(x, z) < 2 or not free(x, z, 4) or in_hole(x, z): continue
        if math.hypot(x - SPAWN[0], z - SPAWN[1]) < 26: continue
        key = 'mite%d' % (k % 3)
        place(key, (lambda k=k: FP.stalagmite(k % 3 + 1, (12, 8, 16)[k % 3], (2.4, 1.8, 2.8)[k % 3])), x, z, rng.uniform(0, 360), rng.uniform(.8, 1.2), group='Dripstone')
        reserve(x, z, 4); n += 1

CRYSTAL_SPOTS = []
def crystals(rng):
    """geodes at chosen spots (glow by district: amber by the camp + forge, cyan round the lake + lift, violet in the
    north + brew), crystal sprays at wall feet, shard scatter; each logged as a breakable anchor with a tier"""
    spots = [  # x, z, kind, scale, tier
        (-40, 12, 'cyan', 1.6, 1), (36, 6, 'cyan', 1.4, 1), (-34, -24, 'cyan', 2.4, 1), (44, -30, 'cyan', 1.5, 1),
        (-70, -40, 'cyan', 2.6, 1), (78, -6, 'cyan', 1.3, 1), (-72, 18, 'cyan', 1.2, 1), (20, 78, 'cyan', 1.1, 1),
        (-22, -82, 'cyan', 1.7, 2), (60, -86, 'cyan', 1.4, 2), (-128, -14, 'cyan', 1.3, 2), (122, 4, 'cyan', 1.2, 2),
        (-200, 16, 'amber', 1.8, 3), (196, 44, 'cyan', 1.6, 3), (134, -164, 'amber', 2.0, 3), (-48, -206, 'cyan', 2.2, 4),
        (-4, -214, 'cyan', 1.8, 4), (-140, 116, 'violet', 1.6, 3), (-160, -22, 'amber', 1.2, 3), (-106, 118, 'violet', 1.3, 3),
    ]
    for k, (x, z, kind, s, tier) in enumerate(spots):
        for t in range(10):
            if free(x, z, 3.5 * s) and path_d(x, z) > 2 and lake_d(x, z) > 1 and wd(x, z) > 3 * s: break
            x += rng.uniform(-6, 6); z += rng.uniform(-6, 6)
        else: continue
        place('geode_' + kind, (lambda kind=kind: FP.geode(kind, {'cyan': 1, 'violet': 2, 'amber': 3}[kind])), x, z, rng.uniform(0, 360), s, group='Crystals')
        reserve(x, z, 4 * s); CRYSTAL_SPOTS.append(('Geode%02d' % k, x, H(x, z), z, kind, tier, s))
        if s >= 1.7: light(x, 7 * s, z, kind, 5000 * s, 2.0)
    n = 0
    for k in range(900):
        if n >= 10: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if not 3.5 < wd(x, z) < 6 or path_d(x, z) < 4 or not free(x, z, 5) or lake_d(x, z) < 2: continue
        kind = 'violet' if math.hypot(x - GROT['Brew'][0][0], z - GROT['Brew'][0][2]) < 40 else 'amber' if math.hypot(x - GROT['Forge'][0][0], z - GROT['Forge'][0][2]) < 40 else 'cyan'; g = wgrad(x, z)
        place('spray_' + kind, (lambda kind=kind: FP.crystal_spray(kind, n + 3)), x, z, math.degrees(math.atan2(g.x, g.z)), rng.uniform(1.0, 1.5), group='Crystals')
        reserve(x, z, 5); CRYSTAL_SPOTS.append(('Spray%02d' % n, x, H(x, z), z, kind, 1 if z > -90 and abs(x) < 110 else 2, 1.0)); n += 1
    n = 0
    for k in range(1500):
        if n >= 26: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if wd(x, z) < 3 or path_d(x, z) < 1 or not free(x, z, 1.5) or lake_d(x, z) < 1.5 or in_hole(x, z): continue
        kind = 'cyan'
        place('shards_' + kind, (lambda kind=kind: FP.crystal_shards(kind, 4 + n % 2)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.4), group='Crystals')
        reserve(x, z, 1.5); n += 1

def clusters(rng):
    """story clusters on the open hall floor (no dead space between light pools): a mining stop (tipped cart, ore pile,
    crates, lantern), a crystal outcrop (spray, small geode, shards, a glowing puddle), a fungus patch (clusters,
    patches, puddle), a supply stack (barrels, crates, lantern); odd counts, each one a little lit island"""
    THEMES = ('mine', 'crystal', 'shroom', 'supply')
    cents = []
    for k in range(4000):
        if len(cents) >= 13: break
        x, z = rng.uniform(-95, 100), rng.uniform(-95, 80)
        if wd(x, z) < 13 or path_d(x, z) < 7 or lake_d(x, z) < 9 or not free(x, z, 9) or in_hole(x, z): continue
        if any(math.hypot(x - a, z - b) < 30 for a, b, _ in cents): continue
        cents.append((x, z, THEMES[len(cents) % 4]))
    def put(key, fn, x, z, r, yaw=None, s=1.0, y=None):
        for t in range(6):
            xx, zz = x + rng.uniform(-1, 1) * t, z + rng.uniform(-1, 1) * t
            if free(xx, zz, r) and path_d(xx, zz) > 1 and wd(xx, zz) > 3 and lake_d(xx, zz) > 1:
                place(key, fn, xx, zz, rng.uniform(0, 360) if yaw is None else yaw, s, y, group='Clusters'); reserve(xx, zz, r); return xx, zz
        return None
    for n, (x, z, th) in enumerate(cents):
        a = rng.uniform(0, math.tau); off = lambda d, da=0: (x + math.cos(a + da) * d, z + math.sin(a + da) * d)
        if th == 'mine':
            put('cart_cyan', lambda: FP.mine_cart('cyan'), *off(0), 3.5, s=1.0)
            put('ore_cyan', lambda: FP.ore_pile('cyan', 3), *off(6, 1.6), 3.5)
            put('crates1', lambda: FP.crates(1), *off(6, -1.4), 3.5)
            p = put('lpost', FP.mine_lantern_post, *off(7, 3.1), 2)
            if p and n % 2 == 0: light(p[0], 6.5, p[1], 'lamp', 2200, .4)
            CRYSTAL_SPOTS.append(('OreCart%02d' % n, x, H(x, z), z, 'cyan', 1, 1.0))
        elif th == 'crystal':
            put('spray_cyan', lambda: FP.crystal_spray('cyan', 5), *off(0), 5, s=1.3)
            put('geode_cyan', lambda: FP.geode('cyan', 1), *off(7, 2.0), 4, s=.9)
            for j in range(2): put('shards_cyan', lambda: FP.crystal_shards('cyan', 4), *off(5 + j * 2, -1 - j * 1.4), 1.5)
            put('puddle%d' % (n % 2), (lambda n=n: FP.glow_puddle(n % 2 + 1)), *off(6, 3.4), 3.5, y=H(x, z) - .02)
            CRYSTAL_SPOTS.append(('Outcrop%02d' % n, x, H(x, z), z, 'cyan', 1, 1.3))
        elif th == 'shroom':
            put('cluster0', lambda: FP.glowshroom_cluster(2), *off(0), 2.5, s=1.3)
            put('cluster1', lambda: FP.glowshroom_cluster(3), *off(4.5, 2.2), 2.5)
            for j in range(3): put('patch%d' % (j % 2), (lambda j=j: FP.shroom_patch(j % 2 + 3)), *off(3 + j * 1.5, -1.2 + j), 1.2)
            put('puddle%d' % (n % 2), (lambda n=n: FP.glow_puddle(n % 2 + 1)), *off(7, -2.6), 3.5, y=H(x, z) - .02)
        else:
            put('barrels', lambda: FP.barrels(2), *off(0), 3.5)
            put('crates1', lambda: FP.crates(1), *off(5.5, 2.0), 3.5)
            p = put('lpost', FP.mine_lantern_post, *off(5, -1.6), 2)
            if p and n % 2 == 1: light(p[0], 6.5, p[1], 'lamp', 2200, .4)
            put('puddle0', lambda: FP.glow_puddle(1), *off(7, 3.6), 3.5, y=H(x, z) - .02)
    for k in range(9):                                                           # loose puddles by the paths
        for t in range(40):
            x, z = rng.uniform(-90, 100), rng.uniform(-95, 80)
            if 1 < path_d(x, z) < 6 and wd(x, z) > 8 and lake_d(x, z) > 5 and free(x, z, 3.5): break
        else: continue
        place('puddle%d' % (k % 2), (lambda k=k: FP.glow_puddle(k % 2 + 1)), x, z, rng.uniform(0, 360), rng.uniform(.8, 1.3), H(x, z) - .02, group='Clusters'); reserve(x, z, 3.5)

def worms(rng):
    """glow-worm colonies on the vault + tunnel ceilings: faint teal specks so the ceiling reads"""
    n = 0
    for k in range(3000):
        if n >= 30: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if wd(x, z) < 4 or in_hole(x, z): continue
        c = ceil_y(x, z)
        if c is None or c > 150 or math.hypot(x - SKY[0], z - SKY[1]) < 22: continue
        place('worms%d' % (n % 2), (lambda n=n: FP.glow_worms(n % 2 + 1)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.4), c + .25, group='Hanging'); n += 1

def fungi(rng):
    """giant glowing mushrooms in the brew grotto and on the west hall floor, knee-high clusters along walls and
    path edges, ankle-high patches (all soft: placed against the real geometry)"""
    for k, (x, z, s) in enumerate(((-148, 96, 1.2), (-112, 124, 1.0), (-78, 18, 1.1), (-196, 18, .9), (166, 50, .9), (-80, -60, 1.0), (40, 72, .8))):
        mg = math.hypot(x - GROT['Brew'][0][0], z - GROT['Brew'][0][2]) < 40
        place('giant%d%s' % (k % 2, 'm' if mg else ''), (lambda k=k, mg=mg: FP.glowshroom_giant(k % 2 + 1, mg)), x, z, rng.uniform(0, 360), s, group='Fungi'); reserve(x, z, 7 * s)
        if s >= 1.0: light(x, 13 * s, z, 'brew' if mg else 'shroom', 3000 * s, 3.0)
    n = 0
    for k in range(1500):
        if n >= 9: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if not 3 < wd(x, z) < 12 or path_d(x, z) < 2 or lake_d(x, z) < 2 or not free(x, z, 2.5) or in_hole(x, z): continue
        place('cluster%d' % (n % 2), (lambda n=n: FP.glowshroom_cluster(n % 2 + 2)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.4), group='Fungi'); reserve(x, z, 2.5); n += 1
    n = 0
    for k in range(2000):
        if n >= 22: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if wd(x, z) < 2 or path_d(x, z) < .5 or lake_d(x, z) < 1 or not free(x, z, 1.2) or in_hole(x, z): continue
        if nz(x, 0, z, 25, 7) < .48: continue
        place('patch%d' % (n % 2), (lambda n=n: FP.shroom_patch(n % 2 + 3)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.5), group='Fungi'); reserve(x, z, 1.2); n += 1

def vines(rng):
    """glow-root vines hanging from the vault and tunnel ceilings (origin at the top, just under the rock)"""
    n = 0
    for k in range(2000):
        if n >= 26: break
        x, z = rng.uniform(-200, 220), rng.uniform(-235, 130)
        if wd(x, z) < 3 or in_hole(x, z) or not free(x, z, 2): continue
        c = ceil_y(x, z)
        if c is None or c > 150: continue
        L = (24, 16, 10)[n % 3]; clear = c - max(H(x, z), WATER)
        if clear - L < (15 if path_d(x, z) < 5 else 6): continue
        place('vine%d' % (n % 3), (lambda n=n, L=L: FP.glow_vine(n % 3 + 1, L, (3, 2, 2)[n % 3])), x, z, rng.uniform(0, 360), 1.0, c - .55, group='Vines', mode='hang')
        n += 1

def landmarks(rng):
    """hero, sun shaft lip, ceiling falls, spawn, the five stations + their dressing, bridges, scaffold"""
    cg = ceil_y(ISLET[0], ISLET[1], 10)
    hh = (cg or 94) - H(ISLET[0], ISLET[1])
    place('hero', lambda: FP.glowroot(hh, 11), ISLET[0], ISLET[1], 180, 1.0, H(ISLET[0], ISLET[1]) - .3, group='Hero')
    reserve(ISLET[0], ISLET[1], 12)
    light(ISLET[0], 4, ISLET[1] + 7, 'amber', 11000, 3.0); light(ISLET[0] + 4, 45, ISLET[1] + 4, 'root', 9000, 4.0)
    place('skylip', FP.skylight_lip, sky_at(168)[0], sky_at(168)[1], 0, 1.0, 168.0, group='Skylight')
    hf = (ceil_y(FALLS[0], FALLS[1], 4) or 46) - WATER - 1.5
    place('falls', lambda: FP.cave_falls(hf), FALLS[0], FALLS[1], face(FALLS[0], FALLS[1], 0, -40), 1.0, WATER, group='Falls')
    light(FALLS[0] + 3, 10, FALLS[1] + 9, 'falls', 8000, 3.0)
    sx, sz = SPAWN; place('dais', FP.spawn_dais, sx, sz, 0, 1.0, group='Spawn'); reserve(sx, sz, 12)
    anchor('SpawnLocation', 'spawn', 'Spawn', sx, H(sx, sz) + 1.4, sz, 0, (10, 1, 10))
    light(sx, 4, sz, 'amber', 1500, 3)
    place('pbridge', lambda: FP.plank_bridge(24.0), 2.0, -15.0, 0, 1.0, -.1, group='Bridges'); reserve(2, -15, 4)
    # stations: (key, fn, grotto, position, face target, label height)
    st = [('MineShop', FP.mine_shop, 'Shop', (186, 26), (150, 20), 9.0),
          ('CrystalForge', FP.crystal_forge, 'Forge', (120, -154), (94, -118), 10.0),
          ('QuestCamp', None, 'Camp', (-176, 0), (-140, -2), 0),
          ('DeepLift', FP.deep_lift, 'Lift', (PIT[0], PIT[1]), (-24, -164), 12.0),
          ('BrewStation', FP.brew_station, 'Brew', (-128, 108), (-104, 86), 9.0)]
    for name, fn, grp, (x, z), (tx, tz), lab in st:
        yaw = face(x, z, tx, tz)
        if fn: place(name, fn, x, z, yaw, 1.0, 0.0 if name == 'DeepLift' else None, group='Stations'); reserve(x, z, 12)
        M = Matrix.Rotation(math.radians(yaw), 3, 'Y'); fwd = M @ Vector((0, 0, -1))
        if name != 'QuestCamp':
            anchor(name + 'Label', 'station', 'Stations', x + fwd.x * 6, H(x, z) + lab + 3, z + fwd.z * 6, yaw, (10, 3, 1), Station=name)
            anchor(name + 'Prompt', 'prompt', 'Stations', x + fwd.x * 9, H(x, z) + 3, z + fwd.z * 9, yaw, (8, 6, 4), Station=name)
    cx, cz = -176, 0                                                          # quest camp
    place('tent', FP.camp_tent, cx - 10, cz - 8, face(cx - 10, cz - 8, cx + 4, cz), group='Stations'); reserve(cx - 10, cz - 8, 7)
    place('campfire', FP.campfire_pit, cx + 2, cz + 2, 0, sink=-.1, group='Stations'); reserve(cx + 2, cz + 2, 5)   # ring stones sit on the floor
    light(cx + 2, 3, cz + 2, 'fire', 5000, 1.5)
    for k, a in enumerate((.6, 2.2, 3.9)):
        x, z = cx + 2 + math.cos(a) * 6.5, cz + 2 + math.sin(a) * 6.5
        place('logseat', FP.log_seat, x, z, math.degrees(-a) + 90, group='Stations')
    qx, qz = cx + 16, cz - 16
    place('qboard', FP.quest_board, qx, qz, face(qx, qz, -140, -2), group='Stations'); reserve(qx, qz, 5)
    yaw = face(qx, qz, -140, -2); M = Matrix.Rotation(math.radians(yaw), 3, 'Y'); fwd = M @ Vector((0, 0, -1))
    anchor('QuestCampLabel', 'station', 'Stations', qx, H(qx, qz) + 4.4, qz, yaw, (6, 4.4, .4), Station='QuestCamp', Surface='Front')
    anchor('QuestCampPrompt', 'prompt', 'Stations', qx + fwd.x * 4, H(qx, qz) + 3, qz + fwd.z * 4, yaw, (8, 6, 4), Station='QuestCamp')
    for name, (x, y, z) in (('Shop', (186, 8, 30)), ('Forge', (120, 4, -160)), ('Lift', (PIT[0] - 5, 6, PIT[1] - 4)), ('Brew', (-128, 4, 107))):
        light(x, y, z, {'Forge': 'fire', 'Brew': 'brew', 'Lift': 'pale'}.get(name, 'lamp'), 8000, 2.0)
    light(PIT[0], -20, PIT[1], 'pale', 3000, 2.0)
    anchor('DeepDiveTrigger', 'elevator', 'Lift', PIT[0], 3.9, PIT[1], face(PIT[0], PIT[1], -24, -164), (5.6, 7.2, 5.6), Destination='DeepMine', TravelTime=4)
    anchor('ChasmKill', 'killzone', 'Hazard', CHASM[0][0], -45, CHASM[0][2], 0, (80, 10, 22))
    anchor('LiftShaftKill', 'killzone', 'Hazard', PIT[0], -50, PIT[1], 0, (12, 10, 12))
    # bridges + scaffold
    yaw = 0; place('rbridge', lambda: FP.rope_bridge(34.0), CHASM[0][0], CHASM[0][2], yaw, 1.0, 0.0, group='Bridges'); reserve(CHASM[0][0], CHASM[0][2], 6)
    anchor('ChasmBridge', 'bridge', 'Paths', CHASM[0][0], 0, CHASM[0][2], 0, (6, 2, 34))
    sx_, sz_ = 86.0, -38.0; g = wgrad(sx_, sz_)
    place('scaffold', FP.scaffold, sx_, sz_, math.degrees(math.atan2(-g.x, -g.z)) + 180 + 180, 1.0, group='MineWorks'); reserve(sx_, sz_, 11)
    light(sx_ - 3, 26, sz_, 'lamp', 2000, 1.5)
    for k, (x, z, kind) in enumerate(((78, -50, 'cyan'), (92, -22, 'cyan'))):
        place('ore_' + kind, (lambda kind=kind: FP.ore_pile(kind, 3)), x, z, rng.uniform(0, 360), group='MineWorks'); reserve(x, z, 3.5)
        CRYSTAL_SPOTS.append(('OrePile%02d' % k, x, H(x, z), z, kind, 1, 1.0))
    for k, (x, z) in enumerate(((-34, 40), (36, 52), (-52, -8), (58, 12), (-20, 22))):
        if free(x, z, 4) and path_d(x, z) > 2: place('mite%d' % (k % 3), (lambda k=k: FP.stalagmite(k % 3 + 1, (12, 8, 16)[k % 3], (2.4, 1.8, 2.8)[k % 3])), x, z, k * 70, 1.0, group='Dripstone'); reserve(x, z, 4)
    for (x, z, key, fn) in ((26, 40, 'barrels', lambda: FP.barrels(2)), (31, 66, 'toolrack', FP.tool_rack), (174, 42, 'crates1', lambda: FP.crates(1)), (196, 10, 'barrels', lambda: FP.barrels(2)), (104, -142, 'crates1', lambda: FP.crates(1)),
                            (-190, 14, 'barrels', lambda: FP.barrels(2)), (24, 66, 'crates1', lambda: FP.crates(1)), (-12, -184, 'crates1', lambda: FP.crates(1)),
                            (162, 6, 'toolrack', FP.tool_rack), (-40, -212, 'toolrack', FP.tool_rack), (100, -48, 'barrels', lambda: FP.barrels(2))):
        if free(x, z, 3): place(key, fn, x, z, rng.uniform(-30, 30) + face(x, z, 0, 0), group='MineWorks'); reserve(x, z, 3.5)

def rails(rng):
    """track along the two rail lines (8-stud segments), buffers at the ends, carts on the rails; path points -> hooks"""
    seg = 8.0
    for li, line in enumerate(RAIL):
        pts = []
        for a, b in zip(line, line[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, round(L / seg))
            for i in range(n): pts.append((lerp(a[0], b[0], (i + .5) / n), lerp(a[1], b[1], (i + .5) / n), math.degrees(math.atan2(-(b[0] - a[0]), -(b[1] - a[1]))), L / n))
        track = MB()
        for k, (x, z, yaw, L) in enumerate(pts):                            # a track is built along its line: static, cut to length
            piece = placed_mb(FP.rail_seg(L).solid, x, 0.0, z, yaw)
            piece.V = [(vx, H(vx, vz) + vy, vz) for vx, vy, vz in piece.V]           # draped on the floor: nothing sunk under it
            track.merge(piece); reserve(x, z, 2.5)
        static('Track_Rails%d' % (li + 1), track, 'Rails')
        for k, p in enumerate(line):
            anchor('Rail%d_%02d' % (li + 1, k + 1), 'cartpath', 'MineCart', p[0], H(*p) + 1.0, p[1], 0, (1, 1, 1), Line=li + 1, Order=k + 1)
        e = line[-1]; d = (line[-1][0] - line[-2][0], line[-1][1] - line[-2][1]); ln = math.hypot(*d)
        bx, bz = e[0] + d[0] / ln * 1.5, e[1] + d[1] / ln * 1.5
        place('buffer', FP.rail_buffer, bx, bz, math.degrees(math.atan2(d[0], d[1])), group='Rails'); reserve(bx, bz, 3)
        for k, (idx, load) in enumerate(((2, 'cyan'), (len(pts) - 3, 'amber' if li == 1 else 'cyan'))):
            x, z, yaw, L = pts[idx]
            place('cart_' + load, (lambda load=load: FP.mine_cart(load)), x, z, yaw, 1.0, H(x, z) + .92, group='Rails')   # on the draped rails (top H + 1.0)
            anchor('MineCart%d_%d' % (li + 1, k + 1), 'cartspawn', 'MineCart', x, H(x, z) + 2.5, z, yaw, (4, 4, 6), Line=li + 1)

def mine_sets(rng):
    """timber sets every ~16 studs along each tunnel (never across the chasm), lantern posts along the paths"""
    for name, pts in TUN.items():
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 16)
            for i in range(n + 1):
                x, z = lerp(a[0], b[0], i / max(n, 1)), lerp(a[1], b[1], i / max(n, 1))
                if in_hole(x, z) or abs(z - CHASM[0][2]) < 14 and name == 'N': continue
                if any(abs(x - px) < 6 and abs(z - pz) < 6 for px, pz, _ in PTS[-400:] if _ == 1.01): continue
                yaw = math.degrees(math.atan2(-(b[0] - a[0]), -(b[1] - a[1])))
                place('frame', FP.mine_frame, x, z, yaw, 1.0, H(x, z) - .2, group='MineSets'); PTS.append((x, z, 1.01))
    n = 0
    for pts, w in PATHS:
        acc = 12.0
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); dx, dz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            t = acc
            while t < L:
                side = 1 if n % 2 else -1; x, z = a[0] + dx * t - dz * (w / 2 + 2.5) * side, a[1] + dz * t + dx * (w / 2 + 2.5) * side
                if wd(x, z) > 4 and lake_d(x, z) > 3 and free(x, z, 2) and tunnel_d(x, z) > 10 and not in_hole(x, z):
                    place('lpost', FP.mine_lantern_post, x, z, face(x, z, a[0] + dx * t, a[1] + dz * t) + 90, group='Lanterns'); reserve(x, z, 2)
                    if n % 3 == 0: light(x, 6.5, z, 'lamp', 2200, .4)
                    n += 1
                t += 38
            acc = t - L

def under_lake(rng):
    for k in range(14):                                                    # on the flat deep bed (validated after)
        c = LAKE[k % 2]; a = rng.uniform(0, math.tau); r = rng.uniform(0, c[2] - 20)
        x, z = c[0] + math.cos(a) * r, c[1] + math.sin(a) * r
        if islet_d(x, z) < 3: continue
        place('bedglow', lambda: FP.lake_glow(1), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.3), H(x, z) - .1, group='LakeGlow')
    for (x, z) in ((2, -10), (-24, -62), (22, -48)): light(x, -3.5, z, 'lake', 8000, .5)
    anchor('LakeWater', 'water', 'Lake', 2, WATER - 3, -40, 0, (110, 6, 90))

# ------------------------------------------------------------------ look: dark cave, colour from the glow, warm sun shaft
GL_RGB = {k: tuple(int(v[i:i + 2], 16) / 255 for i in (1, 3, 5)) for k, v in FP.GLOW.items()}
def look(overview=False):
    w = bpy.data.worlds.new('Cave'); SC.world = w; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.07, .09, .16, 1); bg.inputs[1].default_value = .3      # low cool ambient (= Roblox Ambient)
    WORLD[0] = bg
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .18; b.inputs['Roughness'].default_value = .8
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 14.0; sun.data.color = (1.0, .82, .55); sun.data.angle = math.radians(1.2)
    v = Vector((SUN_DIR[0], 0, SUN_DIR[1])).normalized(); el = math.radians(SUN_EL)
    to_sun = r2b((v.x * math.cos(el), math.sin(el), v.z * math.cos(el))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    GF = {'Camp': (1.0, .6, .3), 'Shop': (1.0, .78, .5), 'Forge': (1.0, .55, .25), 'Lift': (.8, .9, 1.0), 'Brew': (1.0, .45, .85)}
    for x, z, col in ((0, -20, (.3, .9, 1.0)), (-60, -50, (.4, .8, .9)), (60, -10, (1.0, .7, .4)), (-30, 30, (.4, 1.0, .8)), (30, -70, (.4, .8, 1.0))) + tuple((GROT[g][0][0], GROT[g][0][2], c) for g, c in GF.items()):
        L = bpy.data.lights.new('Fill', 'POINT'); L.energy = 13000; L.color = col; L.shadow_soft_size = 20; L.use_shadow = False; L.volume_factor = 0; L.specular_factor = 0
        o = bpy.data.objects.new('Fill', L); o.location = r2b((x, 30, z)); FXC.objects.link(o)     # = Roblox Ambient / bounce
    for x, y, z, key, wt, r in LIGHTS:
        L = bpy.data.lights.new('L', 'POINT'); L.energy = wt; L.color = GL_RGB.get(key, (1, 1, 1)); L.shadow_soft_size = r
        L.use_shadow = False; L.volume_factor = .25; L.specular_factor = 0
        o = bpy.data.objects.new('L', L); o.location = r2b((x, y, z)); FXC.objects.link(o)
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    SC.view_settings.exposure = .6
    for k, v_ in (('taa_render_samples', 48), ('volumetric_tile_size', '4'), ('volumetric_end', 900.0), ('volumetric_start', .5),
                  ('volumetric_samples', 96), ('volumetric_shadow_samples', 32), ('use_volumetric_shadows', True), ('shadow_pool_size', '1024')):
        try: setattr(SC.eevee, k, v_)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hzo = bpy.data.objects.new('Haze', me); hzo.scale = (480, 420, 100); hzo.location = r2b((0, 49, -50)); FXC.objects.link(hzo)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = HAZE
    pv.inputs['Color'].default_value = (.9, .85, .75, 1); pv.inputs['Anisotropy'].default_value = .35
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hzo.visible_shadow = False; HAZE_OB[0] = hzo
    sky = bpy.data.materials.new('SkyDisc'); sky.use_nodes = True; st = sky.node_tree; st.nodes.remove(st.nodes['Principled BSDF'])
    em = st.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.6, .8, 1.0, 1); em.inputs['Strength'].default_value = 6
    st.links.new(em.outputs[0], st.nodes['Material Output'].inputs['Surface'])
    me = bpy.data.meshes.new('SkyDisc'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=40); bm.to_mesh(me); bm.free()
    me.materials.append(sky); so = bpy.data.objects.new('SkyDisc', me); so.location = r2b((sky_at(230)[0], 230, sky_at(230)[1])); FXC.objects.link(so); so.visible_shadow = False
    mm = bpy.data.materials.new('Mote'); mm.use_nodes = True; mb_ = mm.node_tree.nodes['Principled BSDF']
    mb_.inputs['Emission Color'].default_value = (.7, 1.0, .85, 1); mb_.inputs['Emission Strength'].default_value = 12
    rng = random.Random(77)
    for k in range(70):                                                      # spores / dust motes (preview only)
        x, z = rng.uniform(-90, 100), rng.uniform(-100, 70)
        if wd(x, z) < 5: continue
        y = rng.uniform(3, 50) + max(0, H(x, z))
        me = bpy.data.meshes.new('Mote'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(.08, .16)); bm.to_mesh(me); bm.free()
        me.materials.append(mm); ob = bpy.data.objects.new('Mote', me); ob.location = r2b((x, y, z)); FXC.objects.link(ob); ob.visible_shadow = False
    vm2 = bpy.data.materials.new('FallsMist'); vm2.use_nodes = True; vt2 = vm2.node_tree; vt2.nodes.remove(vt2.nodes['Principled BSDF'])
    pv2 = vt2.nodes.new('ShaderNodeVolumePrincipled'); pv2.inputs['Density'].default_value = .05; pv2.inputs['Color'].default_value = (.85, 1, 1, 1)
    pv2.inputs['Emission Color'].default_value = (.6, .95, 1, 1); pv2.inputs['Emission Strength'].default_value = .25
    vt2.links.new(pv2.outputs[0], vt2.nodes['Material Output'].inputs['Volume'])
    for (dx, dy, dz, sx_, sy_, sz_) in ((0, 3, 5, 14, 5, 9), (0, 9, 3, 9, 7, 6)):                  # falls mist (preview only)
        me = bpy.data.meshes.new('Mist'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0); bm.to_mesh(me); bm.free()
        me.materials.append(vm2); ob = bpy.data.objects.new('Mist', me); ob.location = r2b((FALLS[0] + dx, dy, FALLS[1] + dz)); ob.scale = (sx_, sz_, sy_)
        FXC.objects.link(ob); ob.visible_shadow = False
    pw = WATER_OBS[0].data.copy(); pw.name = 'PreviewWater'; pw.materials.clear()
    m = bpy.data.materials.new('PreviewWaterMat'); m.use_nodes = True; bw = m.node_tree.nodes['Principled BSDF']
    bw.inputs['Base Color'].default_value = (.02, .45, .5, 1); bw.inputs['Roughness'].default_value = .08
    bw.inputs['Emission Color'].default_value = (.05, .75, .7, 1); bw.inputs['Emission Strength'].default_value = .35
    bw.inputs['Alpha'].default_value = .55
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    pw.materials.append(m); o = bpy.data.objects.new('PreviewWater', pw); o.matrix_world = WATER_OBS[0].matrix_world; FXC.objects.link(o)
    WATER_OBS[0].hide_render = True

HAZE = .0045
CLIP = [None]
WORLD = [None]; HAZE_OB = [None]
def shot(name, loc, tgt, fov=55, res=(1920, 1032), hide=()):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 3000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    hid = []
    for g in hide:
        c = SUB.get(g) or bpy.data.collections.get(g)
        if c:
            for ob in c.all_objects:
                if not ob.hide_render: ob.hide_render = True; hid.append(ob)
    cut = bool(hide)
    WORLD[0].inputs[0].default_value = (.5, .6, .8, 1) if cut else (.07, .09, .16, 1); WORLD[0].inputs[1].default_value = .55 if cut else .3
    for o in SHELL_OBS[:1]: o.hide_render = cut
    CLIP[0].hide_render = not cut
    HAZE_OB[0].hide_render = cut; bpy.data.objects['SkyDisc'].hide_render = cut
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)
    for ob in hid: ob.hide_render = False

CUT = ('Vault', 'Crust', 'Hanging', 'Vines', 'Skylight')
SHOTS = {
    'map_beauty.png': ((-6, 24, 64), (-2, 30, -46), 62, ()),
    'map_spawn.png': ((0, 9, 66), (2, 12, -20), 66, ()),
    'map_falls.png': ((-16, 12, -40), (-58, 24, -100), 62, ()),
    'map_shop.png': ((150, 11, 20), (190, 9, 26), 64, ()),
    'map_forge.png': ((101, 11, -126), (122, 7, -156), 64, ()),
    'map_camp.png': ((-148, 10, 2), (-182, 5, -4), 64, ()),
    'map_lift.png': ((-24, 12, -168), (-26, 9, -205), 64, ()),
    'map_brew.png': ((-106, 10, 88), (-132, 7, 110), 64, ()),
    'map_hall_e.png': ((-40, 14, 20), (90, 20, -30), 62, ()),
    'map_overview.png': ((-40, 330, 300), (0, 0, -50), 48, CUT),
    'map_top.png': ((0, 700, -50.01), (0, 0, -50), 52, CUT),
}

# ------------------------------------------------------------------ placement validation (the exporter's clip / float test)
# Every dressing prop in `groups` is tested against the built map the way roblox_export.py's placement check tests it
# (same sampling, a little stricter); one that would clip into a solid or float is removed, latest first so the bigger
# earlier pieces stay. Props matching `keep` carry gameplay anchors and are never removed: when one fails, the dressing
# piece it clips into goes instead. Rule: dressing is placed loosely, then validated against the real geometry.
import re as _re
_SOFT = _re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant')
_ROCK = _re.compile(r'(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|stalac')
_FLOK = _re.compile(r'(?i)hang|vine|ivy|lamp-rope|rope|cloud|bird|lily|canopy|_leaves|_branches|glow|beam|debris|orbit')
_WATER = _re.compile(r'(?i)water|lake|river|stream|pond|pool|falls|moat')
def validate(groups, soft_re=_SOFT, keep=None):
    from mathutils.bvhtree import BVHTree
    keep = _re.compile(keep) if keep else None
    owners = []; own = []; bm = bmesh.new()
    def add(name, grp, obs, soft):
        w = len(owners); owners.append({'name': name, 'grp': grp, 'obs': obs, 'soft': soft, 'water': bool(_WATER.search(name))})
        if soft: return w
        for ob in obs:
            m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); own.extend([w] * len(m.polygons)); bpy.data.meshes.remove(m)
        return w
    props = {}
    for c in MAP.children_recursive:
        for ob in c.objects:
            if ob.type != 'MESH': continue
            if ob.data.name in KIT_NAMES:
                nm = ob.data.name.split('_Glow_')[0].split('.')[0]
                key = (nm, tuple(round(v, 3) for row in ob.matrix_world for v in row))
                props.setdefault(key, (nm, c.name, []))[2].append(ob)
            else: add(ob.name, c.name, [ob], False)
    plist = [add(nm, grp, obs, bool(soft_re.search(nm))) for (nm, grp, obs) in props.values()]
    bvh = BVHTree.FromBMesh(bm); bm.free(); gone = set()
    def cast(o, d, dist, ok):
        o = Vector(o); left = dist
        for _ in range(32):
            hit, nrm, i, dd = bvh.ray_cast(o, d, left)
            if hit is None: return None
            if own[i] not in gone and ok(own[i]): return hit, nrm, own[i]
            o = hit + d * 1e-3; left -= dd + 1e-3
            if left <= 0: return None
    D6 = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    def inside(p, me):
        back = {}
        for d in D6:
            h = cast(p, d, 400, lambda w: w != me and not owners[w]['water'])
            if h is not None and h[1].dot(d) > 0: back[h[2]] = back.get(h[2], 0) + 1
        w = max(back, key=back.get, default=None)
        return w if w is not None and back[w] >= 5 else None
    def test(me):
        o = owners[me]; nm, obs, soft = o['name'], o['obs'], o['soft']
        nv = sum(len(ob.data.vertices) for ob in obs); step = max(1, nv // 160); pts = []
        for ob in obs: pts += [ob.matrix_world @ ob.data.vertices[i].co for i in range(0, len(ob.data.vertices), step)]
        lo = min(q.z for q in pts); hi = max(q.z for q in pts)
        body = [q for q in pts if q.z > lo + max(.6, .15 * (hi - lo))]
        if body and not _ROCK.search(nm) and not _WATER.search(nm):
            ins = [w for w in (inside(q, me) for q in body) if w is not None]
            if len(ins) / len(body) > (.06 if soft else .035): return max(set(ins), key=ins.count)   # a margin under 8 / 5 %
        if _FLOK.search(nm) or _re.search(r'(?i)falls|waterfall|cascade', nm): return None
        if soft:
            p = obs[0].matrix_world.translation; h = cast(Vector((p.x, p.y, lo + 3)), Vector((0, 0, -1)), 80, lambda w: True)
            return -1 if h is not None and lo - h[0].z > .8 else None
        cs = [ob.matrix_world @ Vector(c_) for ob in obs for c_ in ob.bound_box]
        a = Vector((min(c_.x for c_ in cs), min(c_.y for c_ in cs), min(c_.z for c_ in cs))); b = Vector((max(c_.x for c_ in cs), max(c_.y for c_ in cs), max(c_.z for c_ in cs)))
        c = (a + b) / 2; sx, sy = (b.x - a.x) * .35, (b.y - a.y) * .35; surf = []
        for dx, dy in ((0, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)):
            h = cast(Vector((c.x + dx * sx, c.y + dy * sy, b.z + .5)), Vector((0, 0, -1)), b.z - a.z + 200, lambda w: w != me)
            if h is not None: surf.append(h[0].z)
        return -1 if not surf or a.z - max(surf) > .4 else None
    def drop(w):
        gone.add(w); removed.append(owners[w]['name'])
        for ob in owners[w]['obs']: bpy.data.objects.remove(ob)
    removable = lambda w: w in plist and owners[w]['grp'] in groups and not (keep and keep.search(owners[w]['name']))
    removed = []; warn = []
    for me in reversed(plist):
        if owners[me]['grp'] not in groups or me in gone: continue
        w = test(me)
        if w is None: continue
        if removable(me): drop(me); continue
        for _ in range(3):                                                   # anchored piece: drop what it clips into
            if w is None or w < 0 or not removable(w): break
            drop(w); w = test(me)
        if w is not None: warn.append(owners[me]['name'])
    print('VALIDATE removed', len(removed), sorted(set(removed)), 'still failing (anchored):', warn)
    return removed

ROCKKEYS = set(); KIT_NAMES = set()
def build():
    build_dist()
    shell(); crust(); floor(); water()
    for loc, tgt, f_, h_ in SHOTS.values(): reserve(loc[0], loc[2], 2)
    reserve(SPAWN[0], SPAWN[1], 12); reserve(FALLS[0] + 4, FALLS[1] + 10, 16)
    rng = random.Random(11)
    landmarks(rng); rails(rng); mine_sets(rng); under_lake(rng)
    crystals(rng); clusters(random.Random(41)); dripstone(rng); worms(random.Random(51)); rocks(rng)
    fungi(random.Random(21)); vines(random.Random(31))
    build_solid(); place_soft(random.Random(5))
    print('SOFT_REJECTED', len(REJECT), REJECT[:16]); print('WHY', WHY); print('DBG', DBG)
    KIT_NAMES.update(me.name for ms, _t in LIB.values() for me in ms.values())
    N2K = {next(iter(LIB[k][0].values())).name.split('_Glow_')[0].split('.')[0]: k for k in LIB}
    for nm in validate({'Crystals', 'Clusters', 'MineWorks', 'Dripstone', 'Rocks', 'Lanterns', 'LakeGlow', 'Hanging'}, SOFT_RE, keep=r'^(Geode|CrystalSpray|OrePile|MineCart)'):
        COUNT[N2K[nm]] -= 1; TRIS[0] -= LIB[N2K[nm]][1]
    for nm, x, y, z, kind, tier, s in CRYSTAL_SPOTS:
        anchor(nm, 'breakable', 'Crystals', x, y + 3 * s, z, 0, (7 * s, 7 * s, 7 * s), Kind=kind, Tier=tier, Ore=('Ore' in nm))
    anchor('SunShaftTop', 'sunshaft', 'Hero', sky_at(165)[0], 165, sky_at(165)[1], 0, (2, 2, 2))
    anchor('SunShaftBottom', 'sunshaft', 'Hero', BEAM_FOOT[0], H(*BEAM_FOOT) + .5, BEAM_FOOT[1], 0, (2, 2, 2))
    anchor('Waterfall', 'waterfall', 'Hero', FALLS[0], WATER, FALLS[1] + 3, 0, (16, 4, 10))
    anchor('GlowrootHeart', 'secret', 'Hero', ISLET[0], H(*ISLET[:2]) + 4, ISLET[1] + 7.5, 180, (8, 8, 8))

build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
STATS = {'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
         'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()},
         'placed_by_key': {k: COUNT[k] * LIB[k][1] for k in COUNT}}
json.dump(STATS, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'water_y': WATER, 'lights': LIGHTS}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'cave_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATS['tris_total'], STATIC_TRIS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov, hide) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov, hide=hide)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
