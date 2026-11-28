# blender -b --factory-startup --python valley_map.py [-- norender] [-- name.png ...] -> Mistvale Lake (valley_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: hidden valley BOWL around a lake (flat natural floor,
# a ring of tiered rounded-rock cliffs wraps it completely). Camera / spawn side = south (+Z), waterfall = north (-Z).
#   lake (turquoise, centre ~(15, 35)) with a curving pale beach on its west + north shores, a grassy islet with the big
#   leaning tree in the south-east of the lake, the fishing dock off the west beach, the stream from the waterfall cleft
#   (north, x ~48) to the lake with a footbridge, a raised stone-walled terrace in the north-east with houses, the
#   village of dark gable-roofed timber houses on the west shore and the north-west back paths, market stalls, lantern
#   rope lines on tall poles, painterly trees everywhere, the rock bowl rising in tiers to ~150 studs at the back.
import sys, os, math, random, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import valley_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB
sys.path.insert(0, os.path.join(HERE, '..', 'oaktrees'))
import gen_trees as GT                                     # realistic alpha-card trees (Trunk / Branches / Leaves)

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
FXC = bpy.data.collections.new('PreviewFX'); SC.collection.children.link(FXC)        # preview water, motes: not exported
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ------------------------------------------------------------------ layout
WATER = 0.0
LAKE_C = (15.0, 35.0)
RIM_C = (0.0, 15.0); RIM_X = 166.0; RIM_Z = 188.0; RIM_N = 2.6           # superellipse bowl rim
FALLS_X = 48.0; FALLS_Z = -192.0                                                             # waterfall cleft at the back
TERR = (60.0, 200.0, -260.0, -70.0, 8.0)                                  # NE terrace: x0, x1, z0, z1, top (runs on under the cliff foot)
STREAM = [(48, -196), (46, -178), (38, -156), (42, -128), (33, -98), (24, -74), (30, -46), (24, -22), (22, -8)]   # ends inside the lake
PATHS = [   # (points, width) dirt paths (shade + keepout)
    ([(-70, 92), (-62, 60), (-60, 25), (-58, -10), (-48, -45), (-30, -72), (0, -88), (20, -96), (33, -98), (48, -100), (70, -101), (92, -96)], 6.0),
    ([(-112, 60), (-86, 52), (-62, 46)], 5.0),
    ([(-108, -14), (-82, -12), (-58, -10)], 5.0),
    ([(-62, -90), (-48, -70), (-48, -45)], 5.0),
    ([(96, -60), (110, -30), (126, -20)], 5.0),
]

def lake_R(th):
    """shore radius around LAKE_C by angle (th = atan2(z, x)): big lobe toward the camera-right (SE) where the islet is"""
    r = 64 + 34 * math.exp(-((math.atan2(math.sin(th - .72), math.cos(th - .72))) / .7) ** 2)
    r -= 10 * math.exp(-((math.atan2(math.sin(th + 1.6), math.cos(th + 1.6))) / .5) ** 2)        # north shore pulled in
    return r + 6 * (nz(math.cos(th) * 3, 0, math.sin(th) * 3, 1.3, 2) - .5)

def lake_d(x, z):
    """signed distance-ish to the shore (negative = in the water)"""
    dx, dz = x - LAKE_C[0], z - LAKE_C[1]
    return math.hypot(dx, dz) - lake_R(math.atan2(dz, dx))

def sand_w(x, z):
    th = math.atan2(z - LAKE_C[1], x - LAKE_C[0])
    west = math.exp(-((math.atan2(math.sin(th - math.pi), math.cos(th - math.pi))) / 1.1) ** 2)
    north = math.exp(-((math.atan2(math.sin(th + 1.75), math.cos(th + 1.75))) / .8) ** 2)
    return 4 + 18 * max(west, north)

ISLET = (62.0, 76.0, 14.0)
def islet(x, z):
    d = math.hypot((x - ISLET[0]) / 1.2, z - ISLET[1]) - ISLET[2]
    return d

def rim_s(x, z):
    """bowl coordinate: < 1 inside the rim; the waterfall cleft pushes the rim back"""
    dx, dz = (x - RIM_C[0]) / RIM_X, (z - RIM_C[1]) / RIM_Z
    s = (abs(dx) ** RIM_N + abs(dz) ** RIM_N) ** (1 / RIM_N)
    if z < 0: s -= .16 * math.exp(-((x - FALLS_X) / 20) ** 2) * smooth((-z - 90) / 60)
    return s + (nz(x, 0, z, 40, 3) - .5) * .03

def seg_d(p, a, b):
    ax, az = a; bx, bz = b; px, pz = p
    vx, vz = bx - ax, bz - az; L2 = vx * vx + vz * vz
    t = clamp(((px - ax) * vx + (pz - az) * vz) / L2) if L2 else 0
    return math.hypot(px - ax - vx * t, pz - az - vz * t)
def poly_d(p, pts): return min(seg_d(p, a, b) for a, b in zip(pts, pts[1:]))
def stream_d(x, z): return poly_d((x, z), STREAM)
def path_d(x, z): return min(poly_d((x, z), pts) - w / 2 for pts, w in PATHS)

def in_terr(x, z):
    x0, x1, z0, z1, _ = TERR
    return x0 <= x <= x1 and z0 <= z <= z1

def H0(x, z):
    """natural floor: lake bed, beach, grass floor, islet, NE terrace (no stream / pool carve)"""
    d = lake_d(x, z)
    if d < 0:
        y = -6.0 * smooth(-d / 18) - .35
    else:
        sw = sand_w(x, z)
        y = .8 * smooth(d / sw) + 1.0 * smooth((d - sw) / 25) + (nz(x, 0, z, 30, 1) - .5) * .8 * smooth((d - sw) / 30)
    di = islet(x, z)
    if di < 6: y = max(y, lerp(-1.5, 2.6, smooth((6 - di) / 9)) + (nz(x, 3, z, 6, 2) - .5) * .5 * smooth(-di / 4))
    if in_terr(x, z) and stream_d(x, z) > 14: y = TERR[4]
    return y
def stream_near(x, z):
    best = (1e9, 0, 0)
    for (ax, az), (bx, bz) in zip(STREAM, STREAM[1:]):
        vx, vz = bx - ax, bz - az; t = clamp(((x - ax) * vx + (z - az) * vz) / (vx * vx + vz * vz))
        cx, cz = ax + vx * t, az + vz * t; d = math.hypot(x - cx, z - cz)
        if d < best[0]: best = (d, cx, cz)
    return best
STREAM_W = 3.6                                                            # ribbon half width (edges under the banks)
def wlevel(cx, cz):
    """stream water level at a centreline point: 0.4 up the valley, dropping with the banks to just over the lake"""
    return clamp(H0(cx, cz) - .6, .02, .4)
def H(x, z):
    """one height function: natural floor + the stream channel + the plunge pool basin"""
    y = H0(x, z)
    sd, cx, cz = stream_near(x, z)
    if sd < STREAM_W - .2:
        y = min(y, lerp(wlevel(cx, cz) - 1.4, y, smooth((sd - 1.0) / (STREAM_W - 1.2))))
    q = math.hypot((x - FALLS_X) / 19, (z - FALLS_Z - 6) / 12.5)
    if q < .96: y = min(y, lerp(-1.6, y, smooth((q - .55) / .4)))
    return y

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; STATIC_TRIS = {}
VTEX = {'oak': 'oak_v', 'young': 'young_v', 'fir': 'fir_v', 'blossom': 'blossom_v'}   # leaf atlases re-graded for the cyan light
def kit(key, fn):
    if key not in LIB:
        if isinstance(fn, str):                                          # realistic tree species from gen_trees
            objs, tr, _ = GT.make_tree(fn, KIT, prefix='Tree', tex=VTEX); LIB[key] = ({o.name: o.data for o in objs}, tr['total'])
            return LIB[key][0]
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
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant')
DEFER = []; DEFER_ON = [True]; PLACED_OBS = []; REJECT = []
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props', top=False):
    """solid props are placed at once; soft ones (foliage, same regex as the exporter's clip check) are DEFERRED until
    every rock / wall / building exists, then placed with the geometry check (place_soft)"""
    meshes = kit(key, fn)
    pname = next(iter(meshes.values())).name
    if DEFER_ON[0] and SOFT_RE.search(pname):
        DEFER.append((key, fn, x, z, yaw, s, y, sink, group, top)); return y
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

# ---- geometry check = the exporter's hard placement check (roblox_export.py 6c), run while placing
from mathutils.bvhtree import BVHTree
SOLID = [None]
def build_solid():
    bm = bmesh.new()
    for c in SUB.values():
        for ob in c.objects:
            if SOFT_RE.search(ob.data.name): continue
            m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    SOLID[0] = BVHTree.FromBMesh(bm); bm.free()
DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
def inside(p):
    back = 0
    for d in DIRS:
        hit, nrm, i, dist = SOLID[0].ray_cast(p, d, 400)
        if hit is not None and nrm.dot(d) > 0: back += 1
    return back >= 5
def clip_fail(obs, pname):
    """True if a placed soft prop clips into solids (> 4%, the exporter allows 8) or floats (> 0.8, exporter 1.0)"""
    for ob in obs:
        if ob.data.name.endswith('_Trunk'):                                 # trunks keep CLEAR studs from the cliff
            t = ob.matrix_world.translation
            if not cliff_clear(-t.x, t.y, 4.5, t.z + .6): return 'cliff'
        M = ob.matrix_world; vs = ob.data.vertices; step = max(1, len(vs) // 160)
        pts = [M @ vs[i].co for i in range(0, len(vs), step)]
        lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
        body = [q for q in pts if q.z > lo_z + .15 * (hi_z - lo_z)]
        if body and sum(1 for q in body if inside(q)) / len(body) > .04: return 'inside'
        o = M.translation; lowest = min(q.z for q in pts)
        hit = SOLID[0].ray_cast(Vector((o.x, o.y, lowest + 3)), Vector((0, 0, -1)), 80)
        if hit[0] is not None and lowest - hit[0].z > .8 and not re.search(r'(?i)canopy|vine|ivy|lily|_leaves|_branches', ob.data.name): return 'floats'
    return None

def surface_y(x, z, flat=.85):
    """top surface under (x, z) by raycast onto everything solid (rock tops, ground); None if it is not a flat ledge"""
    o = r2b((x, 600, z)); hit, nrm, i, d = SOLID[0].ray_cast(o, Vector((0, 0, -1)), 2000)
    if hit is None or nrm.z < flat: return None
    return hit.z                                                              # Blender z = Roblox y

def place_soft(rng):
    """deferred foliage: try the asked spot, then up to 8 jittered spots nearby; keep the first that passes the check"""
    DEFER_ON[0] = False
    for key, fn, x, z, yaw, s, y, sink, group, top in DEFER:
        ok = False
        for t in range(1 if key in ('rOakHero', 'rOakPink') else 9):
            jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (3 + t * 1.5), rng.uniform(-1, 1) * (3 + t * 1.5))
            xx, zz = x + jx, z + jz; yy = y
            if top:                                                           # cliff-top: must stand on a flat ledge
                sy = surface_y(xx, zz)
                if sy is None: continue
                yy = sy - .6 * s
            n0 = len(PLACED_OBS)
            place(key, fn, xx, zz, yaw, s, yy, sink, group)
            obs, k = PLACED_OBS.pop()
            why = clip_fail(obs, obs[0].data.name)
            if why: unplace(obs, k); continue
            ok = True; break
        if not ok: REJECT.append((key, round(x), round(z)))
    DEFER_ON[0] = True
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))       # yaw so the -Z front looks at (tx, tz)
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris
    return ob

ANCHORS = []
def anchor(name, kind, x, y, z, yaw=0.0, size=(4, 1, 4)):
    ANCHORS.append({'name': name, 'kind': kind, 'pos': [round(x, 2), round(y, 2), round(z, 2)], 'yaw': round(yaw % 360, 1), 'size': list(size)})

# ------------------------------------------------------------------ ground, water
def ground():
    xs = [x for x in range(-420, -190, 12)] + [x * 5.0 for x in range(-38, 39)] + [x for x in range(196, 421, 12)]
    zs = [z for z in range(-470, -232, 12)] + [z * 5.0 for z in range(-46, 48)] + [z for z in range(244, 361, 12)]
    bm = bmesh.new(); VV = {}
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            VV[i, j] = bm.verts.new((x, H(x, z), z))
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if rim_s(cx, cz) > 2.35: continue
            th_, e_ = polar(cx, cz); d_ = CL[int(th_ / math.tau * NTH) % NTH]
            if e_ > d_['O'][0] + 4:                                       # under the cliff wall (or past it): no ground
                if e_ > d_['eout'] - 2: continue
                p_ = prof(cx, cz)
                if p_ is not None and p_ > H(cx, cz) - 1: continue
            f = bm.faces.new((VV[i, j], VV[i, j + 1], VV[i + 1, j + 1], VV[i + 1, j])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
    U = {k: FP.PAL.u(k) for k in ('grass', 'sand', 'rock', 'moss', 'stone')}
    def cv(p, ny):
        x, z = p.x, p.z
        n = nz(x, 0, z, 18, 3); n2 = nz(x, 0, z, 5, 4)
        d = lake_d(x, z); s = rim_s(x, z)
        if s > 1.0 and math.hypot(x - FALLS_X, z - FALLS_Z) > 30:
            if ny > .88: return 'moss', .4 + .15 * n2                      # flat shelves: one even moss cap (no checker)
            return 'rock', .12 + .12 * smooth((p.y - 10) / 120) + (n2 - .5) * .08
        if islet(x, z) < -1.5 and p.y > .3:
            return 'grass', .52 + (n - .5) * .2 + (n2 - .5) * .08
        if d < 0 or (z < -20 and stream_d(x, z) < 3.5) or math.hypot(x - FALLS_X, (z - FALLS_Z - 6) * 1.3) < 12:
            return 'sand', .5 - .25 * smooth(-p.y / 5) + (n2 - .5) * .08
        sw = sand_w(x, z) + (n2 - .5) * 3
        if d < sw - 3.5 and islet(x, z) > 2 or (islet(x, z) < -.5 and islet(x, z) > -3):
            return 'sand', .52 + (n - .5) * .1 + .08 * smooth((sw - d) / sw)
        return 'grass', .5 + (n - .5) * .26 + (n2 - .5) * .08 + .08 * smooth((d - sw) / 10) - .08 * smooth((s - .9) / .1)
    def sh(f):
        """ONE palette column per face (a face spanning two columns would interpolate through the strips between)"""
        c = f.calc_center_median(); col, _ = cv(c, f.normal.y); u = U[col]; out = []
        for l in f.loops:
            cc, v = cv(l.vert.co, l.vert.normal.y)
            if cc != col: v = .5
            out.append((u, clamp(v, .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_Valley', mb, 'Ground')

def paths():
    """dirt paths = draped ribbons 0.12 over the ground (3 verts across, ragged width), not a ground tint"""
    bm = bmesh.new(); u = FP.PAL.u('sand')
    for pts, w in PATHS:
        dense = []
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a, b) / 2.5))
            dense += [(lerp(a[0], b[0], t / n), lerp(a[1], b[1], t / n)) for t in range(n)]
        dense.append(pts[-1]); rows = []
        for i, (x, z) in enumerate(dense):
            a = dense[max(i - 1, 0)]; b = dense[min(i + 1, len(dense) - 1)]
            tx, tz = b[0] - a[0], b[1] - a[1]; ln = math.hypot(tx, tz) or 1; nx_, nz_ = -tz / ln, tx / ln
            ww = w / 2 * (1 + (nz(x, 0, z, 6, 5) - .5) * .5)
            row = []
            for k in (-1, -.5, 0, .5, 1):
                px, pz = x + nx_ * ww * k, z + nz_ * ww * k
                row.append(bm.verts.new((px, H(px, pz) + .14, pz)))
            rows.append(row)
        for A, B in zip(rows, rows[1:]):
            for k in range(4):
                f = bm.faces.new((A[k], A[k + 1], B[k + 1], B[k])); f.normal_update()
                if f.normal.y < 0: f.normal_flip()
    def sh(f):
        return [(u, clamp(.44 + (nz(l.vert.co.x, 0, l.vert.co.z, 4, 6) - .5) * .12, .04, .96)) for l in f.loops]
    mb = MB(); mb.add(bm, sh, smooth=True); static('Path_Dirt', mb, 'Ground')

def beach():
    """the curving pale beach as a draped ring mesh: smooth outer edge (the ground grid would stair-step it), from
    just under the water out to the sand width, plus the islet's sand ring"""
    bm = bmesh.new(); u = FP.PAL.u('sand'); NA = 220
    def ring_mesh(pt, ds):
        R = [[bm.verts.new(pt(k, d)) for k in range(NA)] for d in ds]
        for A, B in zip(R, R[1:]):
            for k in range(NA):
                f = bm.faces.new((A[k], A[(k + 1) % NA], B[(k + 1) % NA], B[k])); f.normal_update()
                if f.normal.y < 0: f.normal_flip()
    def lake_pt(k, d):
        th = k * math.tau / NA; r = lake_R(th)
        x, z = LAKE_C[0] + math.cos(th) * r, LAKE_C[1] + math.sin(th) * r
        sw = sand_w(x, z) + (nz(x, 0, z, 5, 4) - .5) * 3
        dd = d * sw if d > 0 else d
        x, z = LAKE_C[0] + math.cos(th) * (r + dd), LAKE_C[1] + math.sin(th) * (r + dd)
        return (x, max(H(x, z), -1.0) + .12, z)
    ring_mesh(lake_pt, (-3.0, 0.0, .25, .5, .75, 1.0))
    def isl_pt(k, d):
        th = k * math.tau / NA; r = ISLET[2] + d
        x, z = ISLET[0] + math.cos(th) * r * 1.2, ISLET[1] + math.sin(th) * r
        return (x, max(H(x, z), -1.0) + .12, z)
    ring_mesh(isl_pt, (-4.0, -2.0, 0.0, 1.5, 2.6))
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co
            out.append((u, clamp(.54 + (nz(p.x, 0, p.z, 14, 3) - .5) * .1 - .22 * smooth(-p.y / 2.5), .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_Beach', mb, 'Ground')

def lake_poly(R_extra=0.0, n=96):
    return [(LAKE_C[0] + math.cos(t) * (lake_R(t) + R_extra), LAKE_C[1] + math.sin(t) * (lake_R(t) + R_extra)) for t in [k * math.tau / n for k in range(n)]]

WATER_OBS = []
def water():
    """lake = fan disc a little past the shore (hidden under the sand), stream ribbon at 0.4, plunge pool"""
    bm = bmesh.new(); c = bm.verts.new((LAKE_C[0], WATER, LAKE_C[1]))
    rings = []
    for k, f in enumerate((.35, .7, 1.0)):
        rings.append([bm.verts.new((LAKE_C[0] + (x - LAKE_C[0]) * f, WATER, LAKE_C[1] + (z - LAKE_C[1]) * f)) for x, z in lake_poly(4.0)])
    n = len(rings[0])
    for i in range(n): bm.faces.new((c, rings[0][(i + 1) % n], rings[0][i]))
    for A, B in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    u = FP.PAL.u('water')
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co; d = lake_d(p.x, p.z)
            out.append((u, clamp(.42 + .25 * smooth((d + 14) / 14), .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True)
    ob = static('Lake_Water', mb, 'Water'); ob.hide_render = True; WATER_OBS.append(ob)
    # stream ribbon from the pool to inside the lake, level = wlevel (edges sit under the banks), + plunge pool disc
    bm = bmesh.new(); pts = []
    for a, b in zip(STREAM, STREAM[1:]):
        n = max(2, int(math.dist(a, b) / 3))
        for t in range(n): pts.append((lerp(a[0], b[0], t / n), lerp(a[1], b[1], t / n)))
    pts.append(STREAM[-1])
    L = []; R = []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]; ln = math.hypot(tx, tz); nx_, nz_ = -tz / ln, tx / ln
        y = wlevel(x, z)
        L.append(bm.verts.new((x + nx_ * STREAM_W, y, z + nz_ * STREAM_W))); R.append(bm.verts.new((x - nx_ * STREAM_W, y, z - nz_ * STREAM_W)))
    for i in range(len(pts) - 1):
        f = bm.faces.new((L[i], R[i], R[i + 1], L[i + 1])); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); mb.add(bm, lambda f: [(u, .62) for l in f.loops], smooth=True)
    ob = static('Stream_Water', mb, 'Water'); ob.hide_render = True; WATER_OBS.append(ob)
    bm = bmesh.new()                                                     # plunge pool: its own still water
    pc = bm.verts.new((FALLS_X, .4, FALLS_Z + 6)); ring = [bm.verts.new((FALLS_X + math.cos(t) * 19, .4, FALLS_Z + 6 + math.sin(t) * 11)) for t in [k * math.tau / 24 for k in range(24)]]
    for i in range(24):
        f = bm.faces.new((pc, ring[(i + 1) % 24], ring[i])); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); mb.add(bm, lambda f: [(u, .62) for l in f.loops], smooth=True)
    ob = static('Pool_Water', mb, 'Water'); ob.hide_render = True; WATER_OBS.append(ob)

def preview_water():
    """preview-only water look (the exported Lake_Water stays palette + Glass in Roblox): saturated turquoise, lighter
    over the shallows (vertex colour from the shore distance), glossy with a small-scale ripple bump for sparkle"""
    for src in WATER_OBS: _preview_water(src)
def _preview_water(src):
    me = src.data.copy(); me.name = 'PreviewWater'
    ca = me.color_attributes.new('shallow', 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        p = KM.inverted() @ v.co; d = lake_d(p.x, p.z)
        s = smooth((d + 16) / 16) if p.z > -25 else .7
        ca.data[v.index].color = (s, s, s, 1)
    ob = bpy.data.objects.new('PreviewWater', me); FXC.objects.link(ob); ob.location = (0, 0, .02)
    m = bpy.data.materials.new('PreviewWaterMat'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'shallow'
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (0.0, .3, .95, 1); cr.elements[1].position = 1.0; cr.elements[1].color = (.3, .92, 1.0, 1)
    e = cr.elements.new(.45); e.color = (0.0, .66, 1.0, 1)
    nt.links.new(at.outputs['Color'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = .16; b.inputs['Specular IOR Level'].default_value = .5
    nt.links.new(ramp.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = .3
    tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = .35
    ns.inputs['Detail'].default_value = 4
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = .1
    nt.links.new(tc.outputs['Object'], ns.inputs['Vector']); nt.links.new(ns.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    me.materials.clear(); me.materials.append(m)

# ------------------------------------------------------------------ the rock bowl (signature): ONE continuous cliff wall
# A closed ring solid round the rim (static Cliff_Wall): tiers of fused rounded rock masses (each tier = a row of
# pillow slabs with creased seams, seams never line up between tiers), moss ledges between tiers, a buried foot and
# talus, a lumpy skyline of big boulders on the top ledge. The foot is pushed back wherever a building, path, stall or
# tree would come within CLEAR studs of it (FOOT_NEED), so nothing sits in or against the rock.
ROCK_KEYS = list(FP.ROCKS)
def rim_r(th):
    c, s_ = math.cos(th), math.sin(th)
    return 1 / ((abs(c / RIM_X) ** RIM_N + abs(s_ / RIM_Z) ** RIM_N) ** (1 / RIM_N))
def rim_point(th, extra=0.0):
    """point on the rim superellipse at angle th (+ extra studs outward)"""
    r = rim_r(th)
    return RIM_C[0] + math.cos(th) * (r + extra), RIM_C[1] + math.sin(th) * (r + extra)
def polar(x, z):
    th = math.atan2(z - RIM_C[1], x - RIM_C[0])
    return th % math.tau, math.hypot(x - RIM_C[0], z - RIM_C[1]) - rim_r(th)

ROCK_DIM = {'RockPillow1': (30, 18, 26), 'RockPillow2': (26, 15, 24), 'RockTower1': (18, 34, 18), 'RockTower2': (22, 42, 20),
            'RockSlab1': (34, 12, 22), 'RockKnob1': (14, 12, 13), 'RockKnob2': (11, 8, 12), 'RockBare1': (9, 6, 8), 'RockMassive': (46, 30, 38),
            'RockTalus': (8, 5, 7)}
def rock_dim(key): return ROCK_DIM[key.replace('VLo', '').replace('Lo', '')]
ROCK_LOG = []
FP.ROCKS['RockTalus'] = lambda: FP.boulder(10, 8, 5, 7, n=2.7, k=4, mthr=.5, cuts=3, name='RockTalus')
def ground_rock(key, x, z, s):
    w, h, d = rock_dim(key); r = .4 * min(w, d) * s
    hs = [H(x, z)] + [H(x + math.cos(a) * r, z + math.sin(a) * r) for a in [k * math.tau / 10 for k in range(10)]]
    return min(hs) + .1 * h * s
def put_rock(key, x, z, yaw, s, group='Cliffs', y=None):
    yb = ground_rock(key, x, z, s) if y is None else y
    place(key, FP.ROCKS[key], x, z, yaw, s=s, y=yb, group=group)
    ROCK_LOG.append((key, x, z, yb, s))
    return yb

NTH = 480                      # samples round the ring
NT = 6                         # tiers
TIER_S = 34.0                  # radial step per tier (face + ledge)
FACE_W = 6.0                   # horizontal run of a face (steep, rounded lip)
TIER_Y = [22, 46, 72, 98, 124, 150]
FT = [0, .15, .45, .8, 1.0]; FH = [0, .5, .86, .97, 1.0]      # face profile (rounded lip, steep foot)
CLEAR = 9.0                    # studs kept clear between the cliff foot and anything built / walked / planted
BULGE0 = 5.0
FALLS_TH, FALLS_E = polar(FALLS_X, FALLS_Z - 5.5)              # cleft back wall just behind the falls sheet
CL = {}                        # per sample: O, Y, yf, eout, sh (slab shape per tier)
FOOT_NEED = [None]

def foot_need():
    """minimum foot offset per sample so every reserved spot / path keeps CLEAR studs (+ the tier-0 bulge)"""
    need = [-1e9] * NTH; keep = list(PTS)
    for pts, w in PATHS:
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a, b) / 3))
            keep += [(lerp(a[0], b[0], t / n), lerp(a[1], b[1], t / n), w / 2) for t in range(n + 1)]
    for x, z, r in keep:
        th, e = polar(x, z); R = rim_r(th) + e
        half = (r + CLEAR + BULGE0) / max(R, 30)
        i0 = int(th / math.tau * NTH)
        for di in range(-int(half * NTH / math.tau) - 1, int(half * NTH / math.tau) + 2):
            i = (i0 + di) % NTH
            need[i] = max(need[i], e + r + CLEAR + BULGE0 + 1)
    FOOT_NEED[0] = need

def slabs(seed, k):
    """slab boundaries round the ring for tier k: random arc lengths, each slab a rounded pillow"""
    rng = random.Random(seed); th = rng.uniform(0, .1); out = []
    R = 190 + k * TIER_S
    while th < math.tau + .2:
        # (start, end, bulge, top add, offset jitter, ledge depth x, top tilt): ledges run narrow / wide, tops wave
        L = rng.uniform(14, 40) * (1 + .3 * k)
        out.append((th, th + L / R, rng.uniform(.6, 1.0), rng.uniform(-5, 8), rng.uniform(-3, 3), rng.choice((.35, .6, 1.0, 1.0, 1.3, 1.6)), rng.uniform(-3, 3)))
        th += L / R
    return out

def build_profile():
    foot_need()
    need = FOOT_NEED[0]
    f = []
    for i in range(NTH):
        th = i * math.tau / NTH
        f.append(max(2 + 6 * (nz(math.cos(th) * 4, 0, math.sin(th) * 4, 1.5, 11) - .5), need[i]))
    f = [max(f[(i + d) % NTH] for d in range(-5, 6)) for i in range(NTH)]                     # widen pushes
    f = [sum(f[(i + d) % NTH] for d in range(-3, 4)) / 7 for i in range(NTH)]                 # then soften
    f = [max(f[i], need[i]) for i in range(NTH)]
    SL = [slabs(31 + k, k) for k in range(NT)]
    for i in range(NTH):
        th = i * math.tau / NTH
        x0, z0 = rim_point(th, 0)
        back = smooth(((RIM_C[1] - 40) - z0) / 60); side = smooth((150 - abs(x0)) / 30)
        maxH = 48 + 30 * smooth((150 - z0) / 120) + 72 * back * side + 8 * (nz(math.cos(th) * 3, 1, math.sin(th) * 3, 1.1, 4) - .5)
        da = math.atan2(math.sin(th - FALLS_TH), math.cos(th - FALLS_TH)) * (rim_r(th) + FALLS_E)
        c = 1 - smooth((abs(da) - 24) / 6)
        O = []; Y = []; SH = []; base = f[i]; tnoise = 9 * (nz(math.cos(th) * 5, 2, math.sin(th) * 5, 1.0, 8) - .5)
        for k in range(NT):
            sl = next((s for s in SL[k] if s[0] <= th < s[1] or s[0] <= th + math.tau < s[1]), SL[k][0])
            t0 = th if sl[0] <= th < sl[1] else th + math.tau
            u = (t0 - sl[0]) / (sl[1] - sl[0]); shp = math.sin(math.pi * u) ** .6
            bul = (BULGE0 if k == 0 else 4.5) * sl[2] * (1 - c)
            if k: base += TIER_S * lerp(prev_dm, 1.0, c)
            prev_dm = sl[5]
            o = base + sl[4] * (1 - c) * (k > 0) - bul * shp
            y = TIER_Y[k] + (sl[3] + sl[6] * (u - .5) * 2) * shp + tnoise * (k > 0) - 2.5 * (1 - shp)
            SH.append(shp)
            if k < 2: o = lerp(o, FALLS_E - 20 + 10 * k, c); y = lerp(y, -6, c)
            if k == 2: o = lerp(o, FALLS_E, c); y = lerp(y, 68, c)
            if k > 0: o = max(o, O[-1] + FACE_W + 3)
            # a tier exists over a whole slab or not at all (decided at the slab centre): the wall drops in steps
            # with rock end faces where it gets lower, never in sloping ramps
            if k:
                tc = (sl[0] + sl[1]) / 2; xc, zc = rim_point(tc, 0)
                bc = smooth(((RIM_C[1] - 40) - zc) / 60); scc = smooth((150 - abs(xc)) / 30)
                mc = 48 + 30 * smooth((150 - zc) / 120) + 72 * bc * scc + 8 * (nz(math.cos(tc) * 3, 1, math.sin(tc) * 3, 1.1, 4) - .5)
                if TIER_Y[k] + sl[3] > mc + 4 and c < .5: y = -1e9
            O.append(o); Y.append(y)
        for k in range(1, NT): Y[k] = max(Y[k], Y[k - 1])
        hx, hz = rim_point(th, O[0])
        yf = lerp(H(hx, hz) - 2.5, -6, c)
        if Y[0] < yf: Y[0] = yf
        CL[i] = {'O': O, 'Y': Y, 'yf': yf, 'eout': O[-1] + FACE_W + 26, 'sh': SH, 'c': c}

def _prof_i(i, e, x, z):
    d = CL[i]; O, Y = d['O'], d['Y']
    if e < O[0]: return None
    prev = d['yf']
    for k in range(NT):
        if e < O[k]:                                                   # ledge of tier k-1
            return prev + ledge_n(x, z)
        if e < O[k] + FACE_W:
            t = (e - O[k]) / FACE_W; j = max(q for q in range(len(FT)) if FT[q] <= t)
            j = min(j, len(FT) - 2); a = (t - FT[j]) / (FT[j + 1] - FT[j])
            return prev + (Y[k] - prev) * lerp(FH[j], FH[j + 1], a) + (ledge_n(x, z) * lerp(FH[j], FH[j + 1], a) if k else 0)
        prev = Y[k]
    if e <= d['eout']: return prev + ledge_n(x, z)
    return None
def ledge_n(x, z): return 2.4 * (nz(x, 0, z, 22, 5) - .5)
def prof(x, z):
    """cliff surface height at (x, z) (None = no cliff there: valley floor or past the outer edge)"""
    th, e = polar(x, z); fi = th / math.tau * NTH; i0 = int(fi) % NTH; i1 = (i0 + 1) % NTH; a = fi - int(fi)
    y0 = _prof_i(i0, e, x, z); y1 = _prof_i(i1, e, x, z)
    if y0 is None and y1 is None: return None
    if y0 is None or y1 is None: return y0 if y1 is None else y1
    return lerp(y0, y1, a)
def cliff_clear(x, z, r, y=None):
    """True if no cliff rises above y (default: the floor) within r + CLEAR of (x, z)"""
    y = H(x, z) if y is None else y; R = r + CLEAR
    for k in range(32):
        a = k * math.tau / 32
        for d in (R * .25, R * .5, R * .75, R):
            p = prof(x + math.cos(a) * d, z + math.sin(a) * d)
            if p is not None and p > y + .5: return False
    p = prof(x, z)
    return p is None or p <= y + .5

def cliff_mesh():
    bm = bmesh.new(); rows = []; meta = {}
    for i in range(NTH):
        th = i * math.tau / NTH; d = CL[i]; O, Y = d['O'], d['Y']
        es = [(O[0] - .3, -14.0, 'skirt', 0)]
        prev = d['yf']
        for k in range(NT):
            for t, hh in zip(FT, FH):
                e = O[k] + FACE_W * t; x, z = rim_point(th, e)
                es.append((e, prev + (Y[k] - prev) * hh + (ledge_n(x, z) * hh if k else 0), 'face', (k, t, d['sh'][k], (Y[k] - prev))))
            prev = Y[k]
            e1 = O[k + 1] if k + 1 < NT else d['eout']
            e = lerp(O[k] + FACE_W, e1, .5); x, z = rim_point(th, e)
            es.append((e, prev + ledge_n(x, z), 'ledge', k))
        x, z = rim_point(th, d['eout']); es.append((d['eout'], prev + ledge_n(x, z), 'ledge', NT))
        es.append((d['eout'] + .3, -14.0, 'skirt', 0))
        row = []
        for e, y, kind, info in es:
            x, z = rim_point(th, e); v = bm.verts.new((x, y, z)); row.append(v); meta[v] = (kind, info)
        rows.append(row)
    n = len(rows[0])
    for i in range(NTH):
        A, B = rows[i], rows[(i + 1) % NTH]
        for j in range(n):                                             # j = n-1 closes the ring bottom (skirt -> skirt)
            bm.faces.new((A[j], B[j], B[(j + 1) % n], A[(j + 1) % n]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    U = {k: FP.PAL.u(k) for k in ('rock', 'moss')}
    def vv(v, col):
        kind, info = meta[v]; p = v.co; n2 = nz(p.x, p.y, p.z, 7, 4) - .5
        if col == 'moss': return .46 + .16 * (nz(p.x, 0, p.z, 14, 2) - .5) + n2 * .08
        if kind == 'face':
            k, t, shp, hgt = info
            v_ = .2 + .42 * t + (.14 if t >= .8 else 0) - .14 * (1 - shp) + .06 * min(1, p.y / 150)
        elif kind == 'ledge': v_ = .66
        else: v_ = .1
        return v_ + n2 * .1
    def sh(f):
        col = 'moss' if f.normal.y > .6 else 'rock'
        return [(U[col], clamp(vv(l.vert, col), .04, .96)) for l in f.loops]
    mb = MB(); mb.add(bm, sh, smooth=True)
    static('Cliff_Wall', mb, 'Cliffs')

def cliffs(rng):
    G = 'Cliffs'
    cliff_mesh()
    # talus at the foot: small bedded rocks in front of the face (never in the cleft, never near anything reserved)
    for q in range(70):
        th = rng.uniform(0, math.tau); i = int(th / math.tau * NTH) % NTH; d = CL[i]
        if d['c'] > .05: continue
        e = d['O'][0] - BULGE0 * d['sh'][0] * .9 - rng.uniform(.5, 2.5); x, z = rim_point(th, e)
        if not free(x, z, 4): continue
        s = rng.uniform(.6, 1.3)
        put_rock('RockTalus', x, z, rng.uniform(0, 360), s, G, y=H(x, z) - .25 * 5 * s)
    # lumpy rocky skyline: big boulders overlapping along the top ledge where the wall is tall
    th = rng.uniform(0, .1)
    while th < math.tau:
        i = int(th / math.tau * NTH) % NTH; d = CL[i]; top = d['Y'][-1]
        if top > 60 and d['c'] < .05:
            key = rng.choice(('RockMassiveVLo', 'RockTower1VLo', 'RockPillow1VLo'))
            s = rng.uniform(1.2, 1.9); w, h, dd = rock_dim(key)
            e = lerp(d['O'][-1] + FACE_W, d['eout'], rng.uniform(.25, .7)); x, z = rim_point(th, e)
            ys = [prof(x + math.cos(a) * .35 * w * s, z + math.sin(a) * .35 * w * s) for a in [k * math.tau / 8 for k in range(8)]]
            ys = [y for y in ys if y is not None]
            if ys:
                put_rock(key, x, z, rng.uniform(0, 360), s, G, y=min(ys) - .05 * h * s)
            th += .55 * min(w, dd) * s / (rim_r(th) + e)
        else: th += .05
    for q in range(60):                                                  # masses on the ledges, leaning on the next face
        th = rng.uniform(0, math.tau); i = int(th / math.tau * NTH) % NTH; d = CL[i]
        k = rng.randint(0, NT - 2)
        if d['c'] > .01 or d['Y'][k + 1] < d['Y'][k] + 8: continue
        key = rng.choice(('RockMassiveVLo', 'RockPillow1VLo', 'RockTower1VLo', 'RockPillow2VLo')); s = rng.uniform(.8, 1.3)
        w, h, dd = rock_dim(key); e = d['O'][k + 1] - .15 * min(w, dd) * s; x, z = rim_point(th, e)
        if not free(x, z, .5 * max(w, dd) * s): continue
        ys = [prof(x + math.cos(a) * .35 * w * s, z + math.sin(a) * .35 * w * s) for a in [j * math.tau / 8 for j in range(8)]]
        ys = [y for y in ys if y is not None]
        if ys: put_rock(key, x, z, face(x, z, RIM_C[0], RIM_C[1]) + rng.uniform(-40, 40), s, G, y=min(ys) - .05 * h * s); reserve(x, z, .4 * max(w, dd) * s)
    # cliff-top pines on the tier ledges (back and sides), each on a ledge with CLEAR studs to the next face
    n = 0
    for q in range(200):
        if n >= 5: break
        th = rng.uniform(math.pi * 1.05, math.pi * 1.95); i = int(th / math.tau * NTH) % NTH; d = CL[i]
        k = rng.randint(1, 3)
        if d['c'] > .01 or d['Y'][k] >= d['Y'][k + 1] - 8: continue
        e = lerp(d['O'][k] + FACE_W, d['O'][k + 1], .4); x, z = rim_point(th, e)
        y = prof(x, z)
        if y is None or not cliff_clear(x, z, 4.5, y) or not free(x, z, 10): continue
        place('rPineC', 'PineC', x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.2), group='CliffTrees', top=True)
        reserve(x, z, 10); n += 1

# ------------------------------------------------------------------ village
def stations_and_village(rng):
    G = 'Village'
    houses = [   # key, fn, x, z, look-at
        ('long1', lambda: FP.house('long', 1), -98, 100, (-40, 75)),
        ('town2', lambda: FP.house('town', 2), -122, 38, (-60, 38)),
        ('long3', lambda: FP.house('long', 3), -112, -22, (-60, -2)),
        ('kura3', lambda: FP.house('kura', 3), -132, 72, (-80, 72)),
        ('town2', lambda: FP.house('town', 2), -70, -112, (-60, -60)),
        ('long3', lambda: FP.house('long', 3), -22, -128, (-15, -80)),
        ('kura3', lambda: FP.house('kura', 3), 4, -150, (10, -100)),
        ('long1', lambda: FP.house('long', 1), 98, -122, (98, -60)),
        ('town4', lambda: FP.house('town', 4), 138, -112, (100, -60)),
        ('kura3', lambda: FP.house('kura', 3), 74, -152, (80, -100)),
        ('town4', lambda: FP.house('town', 4), 140, -32, (90, -10)),
        ('town4', lambda: FP.house('town', 4), -98, 2, (-50, 10)),
        ('kura3', lambda: FP.house('kura', 3), -92, -80, (-50, -60)),
        ('long3', lambda: FP.house('long', 3), 122, 18, (60, 30)),
        ('town2', lambda: FP.house('town', 2), -86, -48, (-40, -30)),
        ('long1', lambda: FP.house('long', 1), -44, -98, (-20, -40)),
        ('town4', lambda: FP.house('town', 4), 18, -118, (20, -60)),
        ('kura3', lambda: FP.house('kura', 3), 112, -56, (60, -20)),
        ('town2', lambda: FP.house('town', 2), -124, 96, (-60, 80)),
    ]
    for key, fn, x, z, tg in houses:
        yaw = face(x, z, *tg)
        place(key, fn, x, z, yaw, group=G, sink=.6 if not in_terr(x, z) else .0, y=TERR[4] - .2 if in_terr(x, z) else None)
        reserve(x, z, 15)
    # stalls on the back path (market square north-west of the beach) + sign stands = STATIONS
    stalls = [('stall1', 1, -46, -58, 'FishShop'), ('stall2', 2, -24, -76, 'BaitStall'), ('stall3', 3, -64, -40, 'RodShop'), ('stall1', 1, 4, -86, 'Market')]
    for key, sd, x, z, nm in stalls:
        yaw = face(x, z, -30, -40)
        y = place(key, (lambda sd=sd: FP.market_stall(sd)), x, z, yaw, group='Stalls')
        reserve(x, z, 7)
        fx, fz = -math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))
        anchor(nm, 'station', x + fx * 2.55, y + 4.5, z + fz * 2.55, yaw, (4, 1.2, .4))
    # inn sign by the big foreground longhouse
    x, z = -76, 90; yaw = face(x, z, -40, 80)
    y = place('sign1', FP.sign_stand, x, z, yaw, group='Stalls'); reserve(x, z, 3)
    anchor('Inn', 'station', x, y + 3.4, z, yaw, (3.3, 2, .4))
    for (x, z, sd) in ((-56, -66, 1), (-14, -70, 2), (-72, -50, 3), (20, -84, 1), (-36, -50, 2)):
        place('crates%d' % sd, (lambda sd=sd: FP.crates(sd)), x, z, rng.uniform(0, 360), group='Stalls'); reserve(x, z, 3)
    for (x, z, sd) in ((-104, 78, 1), (-128, 10, 2), (-94, -40, 3), (122, -78, 1)):
        place('crates%d' % sd, (lambda sd=sd: FP.crates(sd)), x, z, rng.uniform(0, 360), group='Village'); reserve(x, z, 3)

def terrace():
    """NE terrace: stone retaining walls (8-stud modules) along its south and west faces, a stair gap at x 95"""
    x0, x1, z0, z1, top = TERR
    place('stair', lambda: FP.stone_stair(6.0, top + .6, 11.0), 96, z1 + 5.5, 180, y=-.4, group='Terrace')
    reserve(96, z1 + 6, 6)
    for x in (91, 101):
        place('lpost', FP.lantern_post, x, z1 + 12, 180, group='Terrace')

def terrace_walls():
    """retaining walls along the terrace's south and west faces, running until the cliff foot takes over"""
    x0, x1, z0, z1, top = TERR; h = top + 1.0
    def open_(x, z): p = prof(x, z); return p is None or p < top - 1
    x = x0 + 4
    while x < x1:
        if abs(x - 96) > 6 and open_(x, z1): place('wall8', lambda: FP.stone_wall(1, 8.0, h), x, z1 + .1, 180, y=-.6, group='Terrace')
        x += 8
    z = z1 - 4
    while z > z0:
        if stream_d(x0, z) > 6 and open_(x0, z): place('wall8', lambda: FP.stone_wall(1, 8.0, h), x0 - .1, z, 90, y=-.6, group='Terrace')
        z -= 8

def rope_lines():
    """lantern rope lines: tall poles in a chain, two ropes per span (from both arm tips) sagging between them"""
    chains = [[(-150, 128), (-108, 94), (-90, 64), (-82, 22), (-74, -18), (-58, -52), (-30, -92)],
              [(-12, -100), (22, -112), (50, -108)]]
    hgt = 13.0
    for ch in chains:
        tips = []
        for i, (x, z) in enumerate(ch):
            a = ch[max(i - 1, 0)]; b = ch[min(i + 1, len(ch) - 1)]
            ry = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
            py = ry + 90
            yb = place('pole', FP.rope_pole, x, z, py, group='Ropes'); reserve(x, z, 2)
            c, s = math.cos(math.radians(py)), math.sin(math.radians(py))
            tips.append([(x + sx * 2.0 * c, yb + hgt - 1.0, z - sx * 2.0 * s) for sx in (-1, 1)])
        for i in range(len(ch) - 1):
            for k in range(2):
                A = tips[i][k]; Bp = tips[i + 1][k]
                if k == 1:                                                  # pair tips by the nearer one
                    if math.dist(tips[i][1], tips[i + 1][0]) < math.dist(tips[i][1], tips[i + 1][1]): Bp = tips[i + 1][0]
                else:
                    if math.dist(tips[i][0], tips[i + 1][1]) < math.dist(tips[i][0], tips[i + 1][0]): Bp = tips[i + 1][1]
                dx, dy, dz = Bp[0] - A[0], Bp[1] - A[1], Bp[2] - A[2]
                L = math.hypot(dx, dz); Lr = round(L); dyr = round(dy, 1)
                key = 'rope_%d_%s' % (Lr, str(dyr).replace('-', 'm').replace('.', 'p'))
                def fn(Lr=Lr, dyr=dyr, key=key):
                    P = FP.lantern_rope(1, Lr, 2.4 + Lr * .04, max(3, int(Lr / 11)))
                    P.name = 'LanternRope_%s' % key[5:]
                    # tilt: shear y along x so the far end meets the next arm
                    for mb in [P.solid] + list(P.glow.values()):
                        mb.V = [(vx, vy + dyr * vx / Lr, vz) for vx, vy, vz in mb.V]
                    return P
                place(key, fn, A[0], A[2], math.degrees(math.atan2(-dz, dx)), y=A[1], group='Ropes')

def shore():
    """dock off the west beach, footbridge over the stream, stepping stones, lily pads, reeds, shore rocks, islet"""
    G = 'Shore'
    dx_, dz_ = -50.0, 46.0
    place('dock', FP.dock, dx_, dz_, -90, y=0.0, group=G); reserve(dx_ + 15, dz_, 18)
    # dock end platform spots (deck y 2.2): walkway runs +X, platform x 26..33 local -Z -> world +X
    # yaw -90: local -Z (walkway) -> world +X, local +X -> world +Z
    for k, (lz, lx, yaw) in enumerate(((-32.6, -1.0, 270), (-32.6, 4.6, 270), (-29.5, 6.6, 180))):
        anchor('DockSpot%d' % (k + 1), 'fishing', dx_ - lz, 2.6, dz_ + lx, yaw, (3, 1, 3))
    anchor('DockSpot4', 'fishing', dx_ + 16, 2.6, dz_ - 1.8, 0, (3, 1, 3))
    for k, (x, z) in enumerate(((5, 40), (40, 20), (-5, 5), (38, 58))):
        anchor('LakeZone%d' % (k + 1), 'fishzone', x, WATER, z, 0, (30, 1, 30))
    place('bridge', FP.footbridge, 33, -98, 90 + 8, y=-.2, group=G); reserve(33, -98, 9)
    place('stones', lambda: FP.rock_steps(1), 30, -50, -8, y=-.6, group=G)
    rng = random.Random(5)
    # lily pads clusters
    for (x, z, sd) in ((60, 100, 1), (72, 72, 2), (-30, 30, 1), (-24, 62, 2), (40, 8, 1), (100, 70, 2), (10, 90, 1), (68, 118, 2)):
        place('lily%d' % sd, (lambda sd=sd: FP.lily_pads(sd, 5, 4.0)), x, z, rng.uniform(0, 360), y=WATER - .05, group=G)
    # reeds + rocks at the waterline
    for k in range(34):
        th = rng.uniform(0, math.tau); r = lake_R(th) + rng.uniform(-3, 1)
        x, z = LAKE_C[0] + math.cos(th) * r, LAKE_C[1] + math.sin(th) * r
        if not free(x, z, 3) or abs(z - 46) < 6 and x < -30: continue
        if k % 3 == 0:
            key = rng.choice(('RockKnob1', 'RockKnob2', 'RockBare1'))
            place(key, FP.ROCKS[key], x, z, rng.uniform(0, 360), s=rng.uniform(.35, .7), y=H(x, z) - 1.2, group=G)
        else:
            place('reeds%d' % (k % 2 + 1), (lambda k=k: FP.reeds(k % 2 + 1)), x, z, rng.uniform(0, 360), y=H(x, z) - .2, group=G)
        reserve(x, z, 2)
    # the islet: hero tree + mossy rocks + bush + tufts
    hx, hz = ISLET[0] + 2, ISLET[1] + 3
    place('rOakHero', 'OakHero', hx, hz, hero_yaw(hx, hz, -10, 20), s=1.2, group='Islet', y=H(hx, hz) - .3); reserve(ISLET[0], ISLET[1], 10)
    for k, a in enumerate((.3, 1.4, 2.6, 3.7, 4.8, 5.6)):
        x = ISLET[0] + math.cos(a) * ISLET[2] * 1.15; z = ISLET[1] + math.sin(a) * ISLET[2] * .95
        key = ('RockKnob1', 'RockPillow2', 'RockKnob2')[k % 3]
        place(key, FP.ROCKS[key], x, z, rng.uniform(0, 360), s=rng.uniform(.35, .55), y=-1.5, group='Islet')
    place('bush1', lambda: FP.bush(1, 2.4), ISLET[0] - 7, ISLET[1] - 4, 0, group='Islet')
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(3, 11)
        place('tuft%d' % (k % 2 + 1), (lambda k=k: FP.grass_tuft(k % 2 + 1)), ISLET[0] + math.cos(a) * d, ISLET[1] + math.sin(a) * d * .8, rng.uniform(0, 360), group='Islet')
    # waterfall (hero)
    place('falls', lambda: FP.waterfall(64.0, 30.0), FALLS_X, FALLS_Z - 4, 180, y=-.6, group='Waterfall')
    anchor('Waterfall', 'waterfall', FALLS_X, 2.0, FALLS_Z + 6, 0, (20, 4, 10))
    # shore lantern posts along the west beach
    for (x, z) in ((-60, 16), (-62, 70), (-50, -28), (-20, -50)):
        place('lpost', FP.lantern_post, x, z, face(x, z, 15, 35), group=G); reserve(x, z, 2)

def hero_yaw(x, z, tx, tz):
    """yaw that swings the hero oak's leaning crown (its leaves' centroid) toward (tx, tz) = out over the lake"""
    meshes = kit('rOakHero', 'OakHero'); me = [m for n, m in meshes.items() if n.endswith('_Leaves')][0]
    c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices); c.z = 0
    want = Vector((tx - x, tz - z)).normalized(); best = (-2, 0)
    for yaw in range(0, 360, 5):
        R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
        w = KM.inverted() @ ((KM @ R @ KM.inverted()) @ c)                # Blender local -> Roblox world offset
        d = Vector((w.x, w.z)).normalized().dot(want)
        if d > best[0]: best = (d, yaw)
    return best[1]

# realistic trees (gen_trees species): ~tris each: OakA 8.4k, OakB 6.5k, YoungTree 1.6k, PineA 7.5k, PineB 7.4k,
# PineC 3.1k (background fir), OakPink 5.5k, OakHero 15.7k. Fewer, better-placed trees than the stylised set.
TREES = {'rOakA': 'OakA', 'rOakB': 'OakB', 'rYoung': 'YoungTree', 'rPineA': 'PineA', 'rPineB': 'PineB', 'rPineC': 'PineC'}
REACH = {'rOakA': 12, 'rOakB': 9, 'rYoung': 4, 'rPineA': 8, 'rPineB': 8, 'rPineC': 7}
def nature(rng):
    G = 'Nature'
    place('rOakPink', 'OakPink', -74, 66, 30, s=.95, group='Accent'); reserve(-74, 66, 8)
    # (x, z, species): foreground framing near the lake gets the full trees, the back village / terrace the cheap fir
    spots = [(-150, 126, 'rOakA'), (-160, 44, 'rPineA'), (-118, 66, 'rYoung'), (-96, 32, 'rOakB'), (-142, 0, 'rPineC'),
             (-140, -52, 'rPineC'), (-104, -66, 'rPineB'), (-86, -96, 'rPineC'), (-46, -110, 'rPineC'), (-40, -140, 'rPineC'),
             (-2, -122, 'rYoung'), (24, -140, 'rPineC'), (66, -96, 'rPineB'), (66, -140, 'rPineC'), (120, -150, 'rPineC'),
             (150, -140, 'rPineC'), (122, -60, 'rPineC'), (156, -70, 'rPineC'), (150, 10, 'rOakB'), (128, 32, 'rYoung'),
             (152, 60, 'rPineC'), (130, 108, 'rOakA'), (110, 140, 'rYoung'), (60, -30, 'rYoung'),
             (104, -34, 'rPineC'), (-36, -28, 'rYoung'), (-12, -150, 'rPineC'), (92, -120, 'rPineC'), (100, 8, 'rPineC')]
    for k, (x, z, key) in enumerate(spots):
        for _ in range(8):
            if free(x, z, 5) and cliff_clear(x, z, 5): break
            x += rng.uniform(-8, 8); z += rng.uniform(-8, 8)
        else: continue
        place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(1.0, 1.25) if 'Pine' in key else rng.uniform(.95, 1.15), y=TERR[4] - .5 if in_terr(x, z) else None, group=G)
        reserve(x, z, REACH[key])
        a = rng.uniform(0, math.tau); bx, bz = x + math.cos(a) * 6, z + math.sin(a) * 6         # one bush at the foot
        if free(bx, bz, 2): place('bush1', (lambda: FP.bush(1, 2.4)), bx, bz, rng.uniform(0, 360), s=rng.uniform(.8, 1.3), group=G); reserve(bx, bz, 2.5)
    # bush drifts along the back of the beach (clusters of 2-3)
    for k in range(8):
        th = rng.uniform(0, math.tau); r = lake_R(th)
        x0, z0 = LAKE_C[0] + math.cos(th) * r, LAKE_C[1] + math.sin(th) * r
        sw = sand_w(x0, z0) + 5
        for q in range(rng.randint(2, 3)):
            x = LAKE_C[0] + math.cos(th + q * .03) * (r + sw + q * 2.5); z = LAKE_C[1] + math.sin(th + q * .03) * (r + sw + q * 2.5)
            if not free(x, z, 2.5) or not cliff_clear(x, z, 1) or path_d(x, z) < 2: continue
            place('bush%d' % (q % 2 + 1), (lambda q=q: FP.bush(q % 2 + 1, 2.4)), x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.4), group=G); reserve(x, z, 3)
    # undergrowth: tufts + flower patches in clusters on the grass (not on paths/sand)
    n = 0
    for k in range(900):
        if n > 22: break                                                     # halved: tris go to the realistic trees
        x, z = rng.uniform(-165, 165), rng.uniform(-180, 190)
        if not cliff_clear(x, z, 1) or lake_d(x, z) < sand_w(x, z) + 2 or path_d(x, z) < 2 or not free(x, z, 1.5): continue
        if nz(x, 0, z, 30, 9) < .45: continue
        r = rng.random()
        if r < .55: place('tuft%d' % (k % 2 + 1), (lambda k=k: FP.grass_tuft(k % 2 + 1)), x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.5), group='Grass')
        elif r < .8: place('flowers%d' % (k % 2 + 1), (lambda k=k: FP.flower_patch(k % 2 + 1)), x, z, rng.uniform(0, 360), group='Grass')
        else: place('bushs%d' % (k % 2 + 1), (lambda k=k: FP.bush(k % 2 + 3, 2.0)), x, z, rng.uniform(0, 360), group='Grass')
        n += 1


# ------------------------------------------------------------------ look: bright cyan daylight, blue haze, motes
def look():
    w = bpy.data.worlds.new('Cyan'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.45, .85, 1.0, 1)          # pale cyan horizon
    cr.elements[1].position = .6; cr.elements[1].color = (.02, .16, .85, 1)           # deep blue zenith
    e = cr.elements.new(.18); e.color = (.2, .6, 1.0, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 1.1
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .08; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 5.0; sun.data.color = (1.0, .97, .9); sun.data.angle = math.radians(6)
    el = math.radians(52); az = math.radians(205)                                    # high, from the south-west (behind-left of the camera)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = 1.4; fill.data.color = (.55, .8, 1.0); fill.data.use_shadow = False
    to_f = r2b((.3, .8, -.5)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = VIEW[0]
    try: SC.view_settings.look = VIEW[1]
    except Exception: pass
    SC.view_settings.exposure = VIEW[2]
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    try: SC.eevee.shadow_pool_size = '1024'
    except Exception: pass
    for k, v in (('volumetric_tile_size', '8'), ('volumetric_end', 2000.0), ('volumetric_start', 1.0), ('volumetric_distribution', .9), ('volumetric_samples', 64)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (3000, 3000, 700); hz.location = (0, 0, 330); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = HAZE[0]
    pv.inputs['Color'].default_value = (.3, .8, 1.0, 1); pv.inputs['Absorption Color'].default_value = (.7, .88, 1.0, 1)
    pv.inputs['Emission Color'].default_value = (.25, .75, 1.0, 1); pv.inputs['Emission Strength'].default_value = HAZE[1]
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False
    # glowing motes floating over the lake and village (preview; Roblox = ParticleEmitter, see SETUP.md)
    mm = bpy.data.materials.new('Mote'); mm.use_nodes = True; mb_ = mm.node_tree.nodes['Principled BSDF']
    mb_.inputs['Emission Color'].default_value = (.75, 1.0, 1.0, 1); mb_.inputs['Emission Strength'].default_value = 60
    rng = random.Random(77)
    for k in range(80):
        x, z = rng.uniform(-140, 140), rng.uniform(-160, 150); y = rng.uniform(6, 55) + max(0, H(x, z))
        me = bpy.data.meshes.new('Mote'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(.3, .6)); bm.to_mesh(me); bm.free()
        me.materials.append(mm); ob = bpy.data.objects.new('Mote', me); ob.location = r2b((x, y, z)); FXC.objects.link(ob); ob.visible_shadow = False
        MOTES.append((round(x, 1), round(y, 1), round(z, 1)))
    # soft misty sun glare on the water off the dock: an emissive disc fading out radially (blended) + a low mist volume
    gm = bpy.data.materials.new('Glare'); gm.use_nodes = True; nt = gm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.85, 1.0, 1.0, 1); em.inputs['Strength'].default_value = .22
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord'); gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 1.6
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'POWER'; m2.inputs[1].default_value = 2.6
    nt.links.new(tc.outputs['Object'], gr.inputs['Vector']); nt.links.new(tc.outputs['Object'], ns.inputs['Vector'])
    nt.links.new(gr.outputs['Fac'], m2.inputs[0]); nt.links.new(m2.outputs[0], m1.inputs[0]); nt.links.new(ns.outputs['Fac'], m1.inputs[1])
    nt.links.new(m1.outputs[0], mx.inputs['Fac']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    try: gm.surface_render_method = 'BLENDED'
    except Exception: gm.blend_method = 'BLEND'
    for (gx, gz, rr, k) in ():
        me = bpy.data.meshes.new('Glare'); bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=1.0); bm.to_mesh(me); bm.free()
        me.materials.append(gm); ob = bpy.data.objects.new('Glare', me); ob.location = r2b((gx, .15, gz)); ob.scale = (rr * 1.3, rr, 1); FXC.objects.link(ob)
        ob.visible_shadow = False
    vm = bpy.data.materials.new('LakeMist'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (.85, 1.0, 1.0, 1)
    pv.inputs['Emission Color'].default_value = (.8, .98, 1.0, 1); pv.inputs['Emission Strength'].default_value = .12
    tc = vt.nodes.new('ShaderNodeTexCoord'); gr = vt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    mm2 = vt.nodes.new('ShaderNodeMath'); mm2.operation = 'MULTIPLY'; mm2.inputs[1].default_value = .018
    vt.links.new(tc.outputs['Object'], gr.inputs['Vector']); vt.links.new(gr.outputs['Fac'], mm2.inputs[0]); vt.links.new(mm2.outputs[0], pv.inputs['Density'])
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume'])
    for (mx_, my_, mz_, sx_, sy_, sz_) in ((-4, 3, 54, 22, 4, 14), (FALLS_X, 6, FALLS_Z + 8, 24, 10, 14)):
        me = bpy.data.meshes.new('Mist'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0); bm.to_mesh(me); bm.free()
        me.materials.append(vm); ob = bpy.data.objects.new('Mist', me); ob.location = r2b((mx_, my_, mz_)); ob.scale = (sx_, sz_, sy_); FXC.objects.link(ob); ob.visible_shadow = False

HAZE = (.0011, .0001)       # matches Roblox Atmosphere Density ~0.28 (see SETUP.md); never hide geometry with haze
VIEW = ('Standard', 'None', -1.1)
MOTES = []
MATERIALS = {'rock': 'SmoothPlastic', 'moss': 'Grass', 'grass': 'Grass', 'leaf': 'LeafyGrass', 'pine': 'LeafyGrass', 'blossom': 'LeafyGrass',
             'sand': 'Sand', 'water': 'Glass', 'wood': 'Wood', 'wooddk': 'Wood', 'shoji': 'SmoothPlastic', 'roof': 'Slate',
             'stone': 'Cobblestone', 'flower': 'SmoothPlastic', 'red': 'SmoothPlastic'}
MAT_OVERRIDES = {'FishingDock': {'wood': 'WoodPlanks'}, 'FootBridge': {'wood': 'WoodPlanks'}, 'Waterfall': {'water': 'Glass', 'rock': 'SmoothPlastic'},
                 'StoneStair': 'Slate', 'Ground_Valley': {'rock': 'SmoothPlastic', 'sand': 'Sand'}}
def write_materials():
    import roblox_materials as RM
    RM.write_map(FP.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, fov=35, res=(1920, 1032)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 8000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SPAWN = (-60.0, 0.0, 66.0)
SHOTS = {   # vertical FOV (Roblox-style)
    'map_beauty.png': ((8, 68, 152), (36, 10, -90), 58),
    'map_overview.png': ((-260, 260, 300), (0, 10, -10), 42),
    'map_top.png': ((0, 760, 1), (0, 0, 0), 50),
    'map_spawn.png': ((SPAWN[0] - 2, 8, SPAWN[2] + 6), (20, 14, 0), 62),
    'map_village.png': ((-30, 22, 40), (-100, 10, 40), 55),
    'map_market.png': ((-10, 18, -30), (-40, 6, -70), 55),
    'map_falls.png': ((40, 20, -110), (48, 40, -210), 60),
    'map_terrace.png': ((60, 26, -40), (110, 10, -110), 55),
    'map_islet.png': ((30, 14, 108), (64, 14, 76), 50),
    'map_cliffs_w.png': ((-100, 7, 14), (-175, 30, -6), 62),
    'map_cliffs_e.png': ((118, 7, -10), (180, 24, -30), 62),
    'map_cliffs_back.png': ((0, 40, -60), (0, 60, -230), 62),
    'map_backwall.png': ((20, 6, 40), (30, 80, -250), 64),
    'map_terrace_corner.png': ((70, 55, 40), (135, 12, -100), 60),
}

def build():
    for loc, _t, _f in SHOTS.values(): reserve(loc[0], loc[2], 3)
    reserve(SPAWN[0], SPAWN[2], 6)
    rng = random.Random(11)
    terrace(); shore(); stations_and_village(rng); rope_lines()
    build_profile()                                                          # cliff foot fitted round everything above
    nature(random.Random(21)); cliffs(rng); terrace_walls()
    ground(); water(); beach(); paths()
    build_solid(); place_soft(random.Random(5))                              # foliage last, against the real geometry
    print('SOFT_REJECTED', len(REJECT), REJECT[:12])
    sx, sz = SPAWN[0], SPAWN[2]
    anchor('SpawnLocation', 'spawn', sx, H(sx, sz) + .5, sz, face(sx, sz, -30, 46), (10, 1, 10))

build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look(); preview_water(); write_materials()
STATS = {'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
         'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()}}
json.dump(STATS, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'water_y': WATER, 'motes': MOTES}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'valley_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATS['tris_total'])
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
