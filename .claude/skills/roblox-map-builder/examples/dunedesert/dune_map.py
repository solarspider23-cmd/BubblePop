# blender -b --factory-startup --python dune_map.py [-- norender] [-- name.png ...] -> The Gilded Dunes
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: OPEN-WORLD RADIAL DUNE SEA. A sandstone ruin city
# with a gilded step pyramid (hero) in the middle of rolling dunes; six points of interest on spokes 200-330 studs out
# (caravan camp = shop, palm oasis, obelisk field, colossus head, sand-wyrm skeleton, sunken temple = dungeon portal),
# linked by sand paths with waystones; treasure dig mounds (tiers 1-3, richer further out); a ring of high dune ridges
# (r ~430-560) frames the playable sea, distant mesas beyond. High midday sun, deep blue sky, light heat haze.
import sys, os, math, random, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'oaktrees'))
import bpy, bmesh
from mathutils import Vector, Matrix
import dune_props as FP
import gen_trees as GT                                    # realistic alpha-card palms (Trunk / Branches / Leaves)
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, ngon_prism, ccw

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
CITY = (0.0, -20.0); PYR = (0.0, -30.0); GATE = (0.0, 108.0); SPAWN = (0.0, 0.0, 200.0)
CAMP = (140.0, 196.0); OASIS = (-150.0, 172.0); OBEL = (245.0, 5.0); COLO = (178.0, -196.0)
SKULL = (-160.0, -172.0); TEMPLE = (-245.0, 10.0)                  # temple facade plane x, faces +X (toward the city)
SPINE = [(x + 40, z + 33) for x, z in [(-214, -190), (-229, -172), (-241, -152), (-248, -130), (-250, -107), (-246, -84), (-238, -63), (-226, -44), (-211, -28)]]
PADS = [  # (x, z, radius, blend, height) flat play areas
    (CITY[0], CITY[1], 130, 70, 0.0), (SPAWN[0], SPAWN[2], 34, 30, 0.0), (CAMP[0], CAMP[1], 46, 40, 0.0),
    (OASIS[0], OASIS[1], 36, 36, 0.0), (OBEL[0], OBEL[1], 52, 40, 0.0), (COLO[0], COLO[1], 40, 40, 0.0),
    (TEMPLE[0] + 20, TEMPLE[1], 46, 40, 0.0), (SKULL[0], SKULL[1], 12, 18, 0.0),     # the skull rests on a level patch
]
PATHS = [  # (polyline, half width) sand paths; flattened + compacted shade, waystones along them
    ([(10, 196), (55, 212), (98, 214), (118, 202)], 5.0),
    ([(-10, 196), (-60, 207), (-102, 197), (-126, 182)], 5.0),
    ([(60, 25), (120, 34), (175, 22), (205, 10)], 5.0),
    ([(50, -70), (95, -115), (135, -155), (158, -176)], 5.0),
    ([(-50, -72), (-92, -112), (-122, -140), (-146, -156)], 5.0),
    ([(-62, 12), (-118, 22), (-170, 14), (-206, 10)], 5.0),
    ([(156, 172), (200, 108), (232, 46)], 4.5),
    ([(-164, 146), (-196, 92), (-212, 38)], 4.5),
]
AVENUE = ((0, 200), (0, 34), 7.0)
SKEL_PATH = (SPINE, 14.0)

def _seg_d(px, pz, a, b):
    ax, az = a; bx, bz = b; dx, dz = bx - ax, bz - az
    t = clamp(((px - ax) * dx + (pz - az) * dz) / max(1e-9, dx * dx + dz * dz))
    return math.hypot(px - ax - dx * t, pz - az - dz * t)
def pl_d(x, z, pl): return min(_seg_d(x, z, a, b) for a, b in zip(pl, pl[1:]))

def dunes(x, z):
    """transverse dunes (crests ~N-S, wind from the west): gentle windward rise, steeper lee, wandering crests,
    amplitude patches + broad swells"""
    w = x * .94 + z * .34
    ph = w / 92.0 + 1.1 * nz(x, 0, z, 210, 3) + .3 * nz(x, 0, z, 70, 4)
    t = ph % 1.0
    prof = smooth(t / .72) if t < .72 else smooth(1 - (t - .72) / .28)
    amp = 5.0 + 11.0 * nz(x, 0, z, 260, 5)
    return amp * prof + 12.0 * (nz(x, 0, z, 380, 6) - .3)

def ring(x, z):
    """frame: high dune ridges on a ring r ~430-560 round the city, lower beyond so the mesas show"""
    r = math.hypot(x - CITY[0], z - CITY[1]) * (1 + .08 * math.sin(math.atan2(z, x) * 3 + 1))
    up = smooth((r - 345) / 115); down = smooth((r - 560) / 240)
    return up * (1 - .6 * down), r

def T_local(x, z):
    """temple-local (lx across the trench, lz along it: -Z toward the city, facade at 0, body +Z)"""
    return z - TEMPLE[1], TEMPLE[0] - x

def H(x, z):
    """ONE height function for the ground mesh and all placement"""
    rk, r = ring(x, z)
    h = dunes(x, z) * (1 + 2.6 * rk) + 46 * rk
    # sand paths: flatten toward a gentle version of the dunes
    fp = 0.0
    for pl, hw in PATHS:
        fp = max(fp, smooth((hw + 22 - pl_d(x, z, pl)) / 22))
    fs = smooth((26 - pl_d(x, z, SPINE)) / 26)
    h = lerp(h, .25 * dunes(x, z), max(fp, fs * .85))
    # flat play areas (pads)
    fpad = 0.0
    for px, pz, R, bl, ph in PADS:
        fpad = max(fpad, smooth((R + bl - math.hypot(x - px, z - pz)) / bl))
    if abs(x - AVENUE[0][0]) < AVENUE[2] + 24 and AVENUE[1][1] - 20 < z < AVENUE[0][1] + 20:
        fpad = max(fpad, smooth((AVENUE[2] + 24 - abs(x)) / 24))
    flat = 0.0
    cn = nz(x, 0, z, 34, 8)                                           # sand drifts over the city paving
    if math.hypot(x - CITY[0], z - CITY[1]) < 140: flat = 1.4 * smooth((cn - .58) / .14)
    h = lerp(h, flat, fpad)
    # sunken temple: walled trench + buried body mound
    lx, lz = T_local(x, z)
    if abs(lx) < 8.0 and -38.6 < lz < 3.5:
        st = 12.0 * clamp((-lz - 6.0) / 32.0)
        return -12.0 + st - 1.6
    if lz > -2.0 and abs(lx) < 34:
        bx = max(0.0, abs(lx) - 13.0); bz = max(0.0, lz - 20.0) + max(0.0, -lz)
        h = max(h, 6.5 * (1 - smooth(math.hypot(bx, bz) / 16.0)))
    return h

def on_path(x, z, m=0.0):
    for pl, hw in PATHS:
        if pl_d(x, z, pl) < hw + m: return True
    if abs(x) < AVENUE[2] + m and AVENUE[1][1] < z < AVENUE[0][1]: return True
    return False

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; ANCHORS = []; PLACED = []; DEFER = []; REJECT = []; STATIC_TRIS = {}
def kit(key, fn):
    if key not in LIB:
        if isinstance(fn, str):
            objs, tr, _ = GT.make_tree(fn, KIT, prefix='Tree', tex={'palm': 'palm_d'})
            LIB[key] = ({o.name: o.data for o in objs}, tr['total'])
        else:
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
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.3, group='Props'):
    """auto-grounded hard props (y None) are fitted: raised / nudged until the exporter's clip + float rules pass"""
    meshes = kit(key, fn)
    def y_at(x, z):
        fr = foot(key) * s
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        return min(hs) - sink * s
    auto = y is None
    if auto: y = y_at(x, z)
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    Mr = (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    obs = []
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = Matrix.Translation(r2b((x, y, z))) @ Mr; sub(group).objects.link(ob); obs.append(ob)
    names = [me.name for me in meshes.values()]
    soft_ = any(SOFT_RE.search(n) for n in names)
    if not soft_ and not WATER_RE.search(names[0]):
        if auto and not ROCK_RE.search(names[0]):
            y = fit(obs, Mr, x, y, z, y_at)
            if y is None:
                print('FIT_REJECT', key, round(x), round(z))
                for ob in obs: bpy.data.objects.remove(ob)
                return None
        add_owner(obs)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    PLACED.append((obs, key))
    return y
def unplace(obs, key):
    for ob in obs: bpy.data.objects.remove(ob)
    COUNT[key] -= 1; TRIS[0] -= LIB[key][1]
def soft(key, fn, x, z, yaw=0.0, s=1.0, group='Nature', sink=.35):
    """foliage: deferred, placed last against a BVH of every solid (the exporter's hard placement check)"""
    DEFER.append((key, fn, x, z, yaw, s, sink, group))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = len(me.polygons); TRIS[0] += len(me.polygons)
    add_owner([ob])
def world(lx, ly, lz, x, y, z, yaw):
    a = math.radians(yaw); c, s = math.cos(a), math.sin(a)
    return (x + c * lx + s * lz, y + ly, z - s * lx + c * lz)
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def anchor(name, kind, x, y, z, yaw=0.0, size=(4, 1, 4), attrs=None):
    ANCHORS.append({'name': name, 'kind': kind, 'pos': [round(x, 2), round(y, 2), round(z, 2)], 'yaw': round(yaw % 360, 1),
                    'size': list(size), 'attrs': attrs or {}})

# ---- placement check = the exporter's hard check (roblox_export.py 6c), run while placing foliage
from mathutils.bvhtree import BVHTree
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant')
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
def clip_fail(obs):
    for ob in obs:
        M = ob.matrix_world; vs = ob.data.vertices; step = max(1, len(vs) // 160)
        pts = [M @ vs[i].co for i in range(0, len(vs), step)]
        if not pts: continue
        lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
        body = [q for q in pts if q.z > lo_z + .15 * (hi_z - lo_z)]
        if body and sum(1 for q in body if inside(q)) / len(body) > .04: return 'inside'
        if re.search(r'(?i)_leaves|_branches', ob.data.name): continue
        o = M.translation; lowest = min(q.z for q in pts)
        hit = SOLID[0].ray_cast(Vector((o.x, o.y, lowest + 3)), Vector((0, 0, -1)), 80)
        if hit[0] is not None and lowest - hit[0].z > .8: return 'floats'
    return None
# ---- hard props: the exporter's clip (> 5% of the body inside one solid) + float (> 0.5 over the footprint) rules
ROCK_RE = re.compile(r'(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|outcrop')
WATER_RE = re.compile(r'(?i)water|lake|river|stream|pond|pool|falls|moat')
OWN = []                                                  # [(BVHTree, lo, hi)] statics + placed hard props
def add_owner(obs):
    bm = bmesh.new()
    for ob in obs:
        m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    vs = [v.co for v in bm.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    OWN.append((BVHTree.FromBMesh(bm), lo, hi)); bm.free()
def _inb(p, lo, hi, m=.1): return lo.x - m <= p.x <= hi.x + m and lo.y - m <= p.y <= hi.y + m and lo.z - m <= p.z <= hi.z + m
def _inside_one(p):
    for t, lo, hi in OWN:
        if not _inb(p, lo, hi): continue
        back = 0
        for d in DIRS:
            h = t.ray_cast(p, d, 400)
            if h[0] is not None and h[1].dot(d) > 0: back += 1
        if back >= 5: return True
    return False
def fit_bad(obs):
    pts = []; nv = sum(len(ob.data.vertices) for ob in obs); step = max(1, nv // 160)
    for ob in obs:
        vs = ob.data.vertices; pts += [ob.matrix_world @ vs[i].co for i in range(0, len(vs), step)]
    lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
    body = [q for q in pts if q.z > lo_z + max(.6, .15 * (hi_z - lo_z))]
    if body and sum(1 for q in body if _inside_one(q)) > .035 * len(body): return 'clip'
    cs = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))); hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
    c = (lo + hi) / 2; sx, sy = (hi.x - lo.x) * .35, (hi.y - lo.y) * .35; top = -1e9
    for dx, dy in ((0, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)):
        o = Vector((c.x + dx * sx, c.y + dy * sy, hi.z + .5))
        for t, a, b in OWN:
            if a.x <= o.x <= b.x and a.y <= o.y <= b.y:
                h = t.ray_cast(o, Vector((0, 0, -1)), hi.z - lo.z + 200)
                if h[0] is not None: top = max(top, h[0].z)
    return 'float' if lo.z - top > .4 else None
def fit(obs, Mr, x, y, z, y_at):
    """raise the prop in 0.25 steps (its base stays bedded), then try nearby spots; None = nowhere fits"""
    rng = random.Random(int(x * 7 + z * 13))
    for t in range(10):
        jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (1 + t), rng.uniform(-1, 1) * (1 + t))
        y0 = y if t == 0 else y_at(x + jx, z + jz)
        for k in range(16):
            M = Matrix.Translation(r2b((x + jx, y0 + k * .25, z + jz))) @ Mr
            for ob in obs: ob.matrix_world = M
            r = fit_bad(obs)
            if r is None: return y0 + k * .25
            if r == 'float': break
    return None

def place_soft(rng):
    build_solid()
    for key, fn, x, z, yaw, s, sink, group in DEFER:
        ok = False
        for t in range(9):
            jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (2 + t * 1.5), rng.uniform(-1, 1) * (2 + t * 1.5))
            place(key, fn, x + jx, z + jz, yaw, s, None, sink, group)
            obs, k = PLACED.pop()
            if clip_fail(obs): unplace(obs, k); continue
            PLACED.append((obs, k)); ok = True; break
        if not ok: REJECT.append((key, round(x), round(z)))

# ------------------------------------------------------------------ ground: one smooth sand mesh (detail in the atlas)
def ground():
    xs = sorted(set([-1700, -1200, -900] + list(range(-700, -440, 20)) + list(range(-440, 441, 8)) + list(range(460, 701, 20)) + [900, 1200, 1700]
                    + [TEMPLE[0] - 3.0, TEMPLE[0] - 4.0, TEMPLE[0] + 38.4, TEMPLE[0] + 39.0]))
    zs = sorted(set([-1700, -1200, -900] + list(range(-700, -440, 20)) + list(range(-440, 441, 8)) + list(range(460, 701, 20)) + [900, 1200, 1700]
                    + [TEMPLE[1] + d for d in (-8.6, -7.6, 7.6, 8.6)]))
    bm = bmesh.new(); VV = {}
    for i, x in enumerate(xs):
        for j, z in enumerate(zs): VV[i, j] = bm.verts.new((x, H(x, z), z))
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            f = bm.faces.new((VV[i, j], VV[i, j + 1], VV[i + 1, j + 1], VV[i + 1, j])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    u = FP.PAL.u('sand')
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co
            v = .58 + (nz(p.x, 0, p.z, 60, 3) - .5) * .12 + (nz(p.x, 0, p.z, 9, 4) - .5) * .05
            v += .05 * clamp((p.y - 20) / 60)                                   # paler wind-scoured crests
            if on_path(p.x, p.z, 0.5): v -= .24                                # compacted path sand reads darker
            elif on_path(p.x, p.z, 3.0): v -= .12
            out.append((u, clamp(v, .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_Dunes', mb, 'Ground')

def horizon():
    """distant tiered mesas + buttes far outside the frame ring (cheap prisms, rust strata by tier)"""
    rng = random.Random(9); mb = MB()
    for k in range(30):
        a = rng.uniform(0, math.tau); r = rng.uniform(1150, 1650)
        x, z = math.cos(a) * r, math.sin(a) * r
        w = rng.uniform(60, 170); h = rng.uniform(55, 140) * (r / 1000)
        g = H(x, z) - 10
        tiers = rng.randint(2, 3); y0 = g - 10
        for t in range(tiers):
            k2 = 1 - t * .22; yt = g + h * (t + 1) / tiers
            poly = [(x + math.cos(i * math.tau / 8 + rng.uniform(-.15, .15)) * w * k2 * rng.uniform(.75, 1.05),
                     z + math.sin(i * math.tau / 8 + rng.uniform(-.15, .15)) * w * k2 * rng.uniform(.5, .85)) for i in range(8)]
            bm = ngon_prism(ccw(poly), y0, yt)
            for v in bm.verts:
                if v.co.y > yt - 1: v.co.x = x + (v.co.x - x) * .9; v.co.z = z + (v.co.z - z) * .9
            col = 'rock' if t % 2 == 0 else 'stone2'
            mb.add(bm, lambda f, col=col: [(FP.PAL.u(col), clamp(.48 + .22 * f.normal.y, .04, .96))] * len(f.loops))
            y0 = yt - 1
    static('Horizon_Mesas', mb, 'Horizon')

def paving():
    """worn flagstone slabs over the city + the avenue, missing where the sand has drifted over (H drift > 0)"""
    bm = bmesh.new(); rng = random.Random(5); n = 0
    def slab(x0, z0, w, d):
        y = .12
        bm.faces.new([bm.verts.new(p) for p in ((x0, y, z0), (x0 + w, y, z0), (x0 + w, y, z0 + d), (x0, y, z0 + d))])
    cell = 6.0
    for i in range(-24, 25):
        for j in range(-24, 40):
            x0, z0 = i * cell, CITY[1] + j * cell
            cxx, czz = x0 + cell / 2, z0 + cell / 2
            inside_city = math.hypot(cxx - CITY[0], czz - CITY[1]) < 112
            on_av = abs(cxx) < AVENUE[2] and AVENUE[1][1] - 6 < czz < AVENUE[0][1] - 12
            if not (inside_city or on_av): continue
            if abs(cxx - PYR[0]) < 55 and abs(czz - PYR[1]) < 55: continue
            if abs(cxx) < 9 and PYR[1] + 50 < czz < PYR[1] + 66: continue
            if H(cxx, czz) > .05 or any(H(cxx + dx, czz + dz) > .3 for dx in (-2.6, 2.6) for dz in (-2.6, 2.6)): continue
            if not on_av and rng.random() < .08: continue                    # a few missing slabs
            if (i + j) % 2 and rng.random() < .5:
                slab(x0 + .1, z0 + .1, cell / 2 - .2, cell - .2); slab(x0 + cell / 2 + .1, z0 + .1, cell / 2 - .2, cell - .2)
            else: slab(x0 + .1, z0 + .1, cell - .2, cell - .2)
            n += 1
    fs = list(bm.faces)
    for f in fs:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.inset_individual(bm, faces=fs, thickness=.12, depth=.1, use_even_offset=True)
    bm.normal_update()
    def sh(f):
        c = f.calc_center_median()
        if f.normal.y < .99: return [(FP.PAL.u('stone'), .32)] * len(f.loops)
        return [(FP.PAL.u('stone'), clamp(.56 + (FP.h01(round(c.x, 1), 0, round(c.z, 1)) - .5) * .14, .04, .96))] * len(f.loops)
    mb = MB(); mb.add(bm, sh); static('Paving_City', mb, 'Paving')

# ------------------------------------------------------------------ set pieces + stations
def set_pieces():
    sx, sy, sz = SPAWN
    place('dais', FP.spawn_dais, sx, sz, 0, y=0.0, group='Spawn'); reserve(sx, sz, 15)
    anchor('Spawn', 'spawn', sx, 1.6, sz, 0, (8, 1, 8), {'note': 'SpawnLocation on the sun dais, facing -Z: pylon gate frames the pyramid'})
    qx, qz = -27.0, 188.0; qy = face(qx, qz, sx, sz)
    place('quest', FP.quest_stele, qx, qz, qy, y=0.0, group='Spawn'); reserve(qx, qz, 8)
    anchor('QuestStele', 'station', *world(0, 5.0, -1.0, qx, 0, qz, qy), qy, (6, 7, 1), {'prompt': 'Quests', 'note': 'three blank panels take quest SurfaceGuis'})
    ux, uz = 28.0, 186.0; uy = face(ux, uz, sx, sz)
    place('astro', FP.sun_astrolabe, ux, uz, uy, y=0.0, group='Spawn'); reserve(ux, uz, 9)
    anchor('Upgrades', 'station', *world(0, 3.0, -5.0, ux, 0, uz, uy), uy, (6, 6, 4), {'prompt': 'Upgrade', 'note': 'ProximityPrompt at the armillary pedestal'})
    # city: pyramid (hero), pylon gate, avenue columns, ruins
    place('pyramid', FP.step_pyramid, PYR[0], PYR[1], 180, y=0.0, group='Hero'); reserve(PYR[0], PYR[1], 60)
    anchor('PyramidSummit', 'poi', PYR[0], 52.0, PYR[1], 180, (16, 10, 16), {'note': 'summit shrine: sun disc / leaderboard / rebirth spot'})
    place('gate', FP.pylon_gate, GATE[0], GATE[1], 180, y=0.0, group='City'); reserve(GATE[0], GATE[1], 26)
    rng = random.Random(3); k = 0
    for z in range(46, 184, 17):
        if abs(z - GATE[1]) < 12: continue
        for side in (-1, 1):
            x = side * 14.0; kind = (0, 0, 1, 0, 2, 0, 1)[(k * 3 + (side > 0)) % 7]; k += 1
            key = ('colT', 'colB', 'colF')[kind]
            place(key, (lambda kd=kind: FP.column_set(kd, kd + 1)), x, float(z), rng.uniform(-6, 6) + (90 if kind == 2 else 0) * side, y=0.0, group='City')
            reserve(x, z, 3)
    ruins = [  # (key, fn, x, z, yaw)
        ('wall1', lambda: FP.ruin_wall(1, 16, 7, True), -62, 18, 20), ('wall2', lambda: FP.ruin_wall(2, 18, 6), 70, 30, -15),
        ('wall3', lambda: FP.ruin_wall(3, 14, 8), -88, -40, 80), ('wall2', lambda: FP.ruin_wall(2, 18, 6), 92, -70, 100),
        ('wall1', lambda: FP.ruin_wall(1, 16, 7, True), 40, -110, 170), ('wall3', lambda: FP.ruin_wall(3, 14, 8), -55, -112, 200),
        ('house1', lambda: FP.ruin_house(1), -80, 60, 30), ('house2', lambda: FP.ruin_house(2), 84, 50, -40),
        ('house1', lambda: FP.ruin_house(1), 96, -18, -95), ('house2', lambda: FP.ruin_house(2), -100, -78, 120),
        ('arch1', lambda: FP.ruin_arch(1), -42, 62, 10), ('arch2', lambda: FP.ruin_arch(2), 48, 70, -10),
        ('arch1', lambda: FP.ruin_arch(1), 0, -100, 180), ('colT', None, -70, -8, 0), ('colB', None, 66, -2, 0), ('colF', None, -30, -100, 40),
        ('colB', None, 30, -98, 0), ('colT', None, 75, -48, 0),
    ]
    fns = {'colT': lambda: FP.column_set(0, 1), 'colB': lambda: FP.column_set(1, 2), 'colF': lambda: FP.column_set(2, 3)}
    for key, fn, x, z, yaw in ruins:
        place(key, fn or fns[key], x, z, yaw, group='City'); reserve(x, z, 9)
    for x, z, yaw, s in ((-58, -40, 30, 1.0), (60, -30, -20, 1.1), (35, 10, 90, .8), (-35, 12, 80, .8), (0, -92, 0, 1.3)):
        place('drift1', lambda: FP.sand_drift(1), x, z, yaw, s, group='City')
    # caravan camp (SHOP)
    cx, cz = CAMP
    ty = face(cx - 12, cz - 6, sx, sz)
    place('trader', FP.trader_tent, cx - 12, cz - 6, ty, group='Camp'); reserve(cx - 12, cz - 6, 11)
    anchor('CaravanTrader', 'station', *world(0, 3.4, -4.6, cx - 12, 0, cz - 6, ty), ty, (10, 4, 2), {'prompt': 'Shop', 'note': 'counter front; trader NPC stands behind the counter'})
    for (x, z, yaw, key, fn) in ((cx + 14, cz - 18, 210, 'tentR', lambda: FP.sleep_tent(1, 'red', 'cloth')), (cx + 22, cz + 6, 250, 'tentI', lambda: FP.sleep_tent(2, 'indigo', 'saffron')),
                                 (cx + 2, cz + 22, 170, 'tentR', lambda: FP.sleep_tent(1, 'red', 'cloth'))):
        place(key, fn, x, z, yaw, group='Camp'); reserve(x, z, 6)
    place('fire', FP.campfire, cx + 6, cz + 4, 0, group='Camp'); reserve(cx + 6, cz + 4, 3)
    place('rug1', lambda: FP.rug_spread(1), cx + 6, cz - 4, 10, sink=.05, group='Camp'); reserve(cx + 6, cz - 4, 3)
    for (x, z, yaw, key, fn) in ((cx - 26, cz + 12, 120, 'camelK1', lambda: FP.camel('kneel', 1, 'red')), (cx - 20, cz + 22, 160, 'camelK2', lambda: FP.camel('kneel', 2, 'indigo')),
                                 (cx + 30, cz - 22, 40, 'camelS1', lambda: FP.camel('stand', 1, 'red')), (cx - 4, cz - 26, -60, 'camelS2', lambda: FP.camel('stand', 2, 'indigo'))):
        place(key, fn, x, z, yaw, s=1.15, group='Camp'); reserve(x, z, 5)
    for (x, z, yaw) in ((cx - 30, cz - 6, 30), (cx + 18, cz + 22, -40)):
        place('cargo1', lambda: FP.cargo_pile(1), x, z, yaw, group='Camp'); reserve(x, z, 4)
    anchor('CampZone', 'zone', cx, 4, cz, 0, (70, 10, 70), {'poi': 'Caravan Camp'})
    # oasis
    ox, oz = OASIS
    place('pool', FP.oasis_pool, ox, oz, 20, y=.7, group='Oasis'); reserve(ox, oz, 16)
    place('poolw', lambda: FP.oasis_pool('water'), ox, oz, 20, y=.7, group='Oasis')
    anchor('OasisWell', 'poi', *world(14.0, 2.5, 0, ox, .7, oz, 20), 20, (5, 5, 5), {'note': 'well head: heal / refill prompt'})
    anchor('OasisZone', 'zone', ox, 4, oz, 0, (60, 10, 60), {'poi': 'Palm Oasis'})
    # obelisk field: three standing in a row (one fallen out of line), toppled pieces, stumps
    bx, bz = OBEL
    for k, (dx, dz) in enumerate(((-26, -24), (0, -30), (26, -24))):
        place('obelisk', lambda: FP.obelisk(1), bx + dx, bz + dz, 180, s=1.3, y=0.0, group='Obelisks'); reserve(bx + dx, bz + dz, 6)
    for (dx, dz, yaw, key, fn) in ((-30, 18, 20, 'obTop', lambda: FP.obelisk_fallen(1, 'top')), (-14, 14, 20, 'obMid', lambda: FP.obelisk_fallen(2, 'mid')),
                                   (18, 22, -35, 'obTop', lambda: FP.obelisk_fallen(1, 'top')), (32, 6, 70, 'obMid', lambda: FP.obelisk_fallen(2, 'mid'))):
        place(key, fn, bx + dx, bz + dz, yaw, sink=.9, group='Obelisks'); reserve(bx + dx, bz + dz, 7)
    for (dx, dz) in ((-40, -4), (14, 2), (40, -6)):
        place('obStump', lambda: FP.obelisk_stump(1), bx + dx, bz + dz, 180, y=0.0, group='Obelisks'); reserve(bx + dx, bz + dz, 6)
    anchor('ObeliskZone', 'zone', bx, 4, bz, 0, (90, 10, 70), {'poi': 'Obelisk Field'})
    # colossus head
    hx, hz = COLO; hy = face(hx, hz, CITY[0], CITY[1])
    place('head', FP.colossus_head, hx, hz, hy, s=1.55, y=-1.8, group='Colossus'); reserve(hx, hz, 22)
    for k in range(6):
        a = math.radians(hy) + k * math.tau / 6 + .4
        place('drift1', lambda: FP.sand_drift(1), hx + math.sin(a) * 12, hz + math.cos(a) * 12, math.degrees(a) + 90, 1.4, group='Colossus')
    anchor('ColossusZone', 'zone', hx, 6, hz, hy, (60, 12, 60), {'poi': 'Colossus Head'})
    # sand-wyrm skeleton: skull + ribs (big -> small) along the spine curve
    kx, kz = SKULL; ky = face(kx, kz, SPINE[0][0], SPINE[0][1]) + 180
    place('skull', FP.wyrm_skull, kx, kz, ky, s=1.5, sink=.8, group='Skeleton'); reserve(kx, kz, 14)
    for i, (x, z) in enumerate(SPINE):
        a, b = SPINE[max(i - 1, 0)], SPINE[min(i + 1, len(SPINE) - 1)]
        yaw = face(0, 0, b[0] - a[0], b[1] - a[1]) + 90
        s = lerp(1.45, .6, i / (len(SPINE) - 1))
        place('rib%d' % (1 + i % 3), (lambda k=1 + i % 3: FP.wyrm_rib(k)), x, z, yaw, s=s, sink=2.2, group='Skeleton'); reserve(x, z, 5)
    anchor('SkeletonZone', 'zone', -195, 6, -90, 0, (60, 14, 170), {'poi': 'Wyrm Skeleton'})
    # sunken temple (DUNGEON PORTAL)
    tx, tz = TEMPLE
    place('temple', FP.sunken_temple, tx, tz, -90, y=-12.0, group='SunkenTemple'); reserve(tx + 10, tz, 30)
    anchor('DungeonPortal', 'portal', tx + 1.2, -6.5, tz, -90, (7, 11, 2), {'prompt': 'Enter Dungeon', 'note': 'glowing doorway at the foot of the trench stair'})
    anchor('TempleZone', 'zone', tx + 20, 0, tz, 0, (60, 30, 40), {'poi': 'Sunken Temple'})

def waystones():
    """path markers every ~30 studs along each sand path, alternating sides"""
    k = 0
    for pl, hw in PATHS:
        for a, b in zip(pl, pl[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L / 30))
            for i in range(n):
                t = (i + .5) / n; x = lerp(a[0], b[0], t); z = lerp(a[1], b[1], t)
                dx, dz = (b[0] - a[0]) / L, (b[1] - a[1]) / L; side = 1 if k % 2 else -1
                px, pz = x - dz * side * (hw + 3.0), z + dx * side * (hw + 3.0)
                if not free(px, pz, 2.5): continue
                place('way%d' % (k % 2 + 1), (lambda q=k % 2 + 1: FP.waystone(q)), px, pz, face(px, pz, x, z), group='Waystones')
                reserve(px, pz, 2.5); k += 1

DIG = [  # (x, z, tier) richer further out
    (60, 150, 1), (-58, 150, 1), (110, 80, 1), (-115, 70, 1), (-100, -150, 1), (85, -150, 1),
    (200, 150, 2), (-215, 210, 2), (285, 110, 2), (-300, -40, 2), (120, -245, 2), (-95, -255, 2), (285, -100, 2),
    (325, -40, 3), (-140, -310, 3), (250, -255, 3), (-320, 125, 3), (55, -330, 3),
]
def dig_spots():
    for i, (x, z, t) in enumerate(DIG):
        yaw = (i * 47) % 360
        y = place('dig%d' % t, (lambda t=t: FP.treasure_mound(t)), x, z, yaw, sink=.15, group='DigSpots'); reserve(x, z, 6)
        anchor('DigSpot%02d' % (i + 1), 'dig', x, y + 1.0, z, yaw, (6, 3, 6), {'tier': t})

def nature(rng):
    # palms: oasis grove + two at the camp (realistic alpha-card species)
    ox, oz = OASIS
    for k in range(9):
        a = k * math.tau / 9 + rng.uniform(-.2, .2); r = rng.uniform(20, 27)
        x, z = ox + math.cos(a) * r, oz + math.sin(a) * r
        if on_path(x, z, 2) or not free(x, z, 3): continue
        sp = ('PalmA', 'PalmB', 'PalmA', 'PalmC')[k % 4]
        soft('r' + sp, sp, x, z, rng.uniform(0, 360), rng.uniform(.9, 1.1), 'Oasis')
    for x, z in ((CAMP[0] - 34, CAMP[1] - 22), (CAMP[0] + 32, CAMP[1] + 8)):
        soft('rPalmC', 'PalmC', x, z, rng.uniform(0, 360), 1.0, 'Camp')
    soft('rPalmB', 'PalmB', OBEL[0] + 46, OBEL[1] + 28, 40, 1.0, 'Obelisks')
    for k in range(22):                                                # oasis rim planting
        a = rng.uniform(0, math.tau); r = rng.uniform(13.5, 21)
        x, z = ox + math.cos(a) * r, oz + math.sin(a) * r
        if on_path(x, z, 1): continue
        if rng.random() < .55: soft('grass%d' % (k % 2 + 1), (lambda q=k % 2 + 1: FP.dune_grass(q, 13, 2.2)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.3), 'Oasis')
        else: soft('shrub%d' % (k % 2 + 1), (lambda q=k % 2 + 1: FP.dry_shrub(q)), x, z, rng.uniform(0, 360), rng.uniform(.9, 1.2), 'Oasis')
    # rock stacks + outcrops: clusters in the dune sea (never on paths / pads)
    n = 0
    for _t in range(600):
        if n >= 34: break
        x, z = rng.uniform(-370, 370), rng.uniform(-370, 370)
        if math.hypot(x - CITY[0], z - CITY[1]) < 150 or on_path(x, z, 14) or not free(x, z, 14): continue
        if any(math.hypot(x - px, z - pz) < R + 10 for px, pz, R, bl, ph in PADS): continue
        if ring(x, z)[0] > .5: continue
        key = rng.choice(('stack1', 'stack2', 'out1', 'out2'))
        fn = {'stack1': lambda: FP.rock_stack(1), 'stack2': lambda: FP.rock_stack(2, 5), 'out1': lambda: FP.outcrop(1), 'out2': lambda: FP.outcrop(2)}[key]
        place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.8), group='Rocks'); reserve(x, z, 8); n += 1
        for j in range(rng.randint(1, 3)):                              # scrub at the rock foot
            a = rng.uniform(0, math.tau); xx, zz = x + math.cos(a) * 7, z + math.sin(a) * 7
            if free(xx, zz, 1.5) and not on_path(xx, zz, 2):
                soft('shrub%d' % (j % 2 + 1), (lambda q=j % 2 + 1: FP.dry_shrub(q)), xx, zz, rng.uniform(0, 360), rng.uniform(.8, 1.3))
    # scattered scrub + grass in dune troughs, and along path verges
    n = 0
    for _t in range(1600):
        if n >= 120: break
        x, z = rng.uniform(-380, 380), rng.uniform(-380, 380)
        if math.hypot(x - CITY[0], z - CITY[1]) < 100 or on_path(x, z, 2.5) or not free(x, z, 2): continue
        if ring(x, z)[0] > .6: continue
        for j in range(rng.randint(1, 3)):
            xx, zz = x + rng.uniform(-3, 3), z + rng.uniform(-3, 3)
            if rng.random() < .5: soft('shrub%d' % (j % 2 + 1), (lambda q=j % 2 + 1: FP.dry_shrub(q)), xx, zz, rng.uniform(0, 360), rng.uniform(.7, 1.2))
            else: soft('grass%d' % (j % 2 + 1), (lambda q=j % 2 + 1: FP.dune_grass(q)), xx, zz, rng.uniform(0, 360), rng.uniform(.8, 1.3))
        reserve(x, z, 2); n += 1

def fragments(rng):
    """half-buried relics of the old kingdom between the points of interest: broken columns, fallen drums, obelisk
    stumps, short wall stubs and drifts, in loose groups of 2-3 beside the paths (never on them)"""
    opts = [('colB', lambda: FP.column_set(1, 2)), ('colF', lambda: FP.column_set(2, 3)), ('obStump', lambda: FP.obelisk_stump(1)),
            ('wall3', lambda: FP.ruin_wall(3, 14, 8)), ('drift1', lambda: FP.sand_drift(1))]
    n = 0
    for pl, hw in PATHS:
        for a, b in zip(pl, pl[1:]):
            if rng.random() < .35: continue
            t = rng.uniform(.3, .7); x = lerp(a[0], b[0], t); z = lerp(a[1], b[1], t)
            L = math.hypot(b[0] - a[0], b[1] - a[1]); dx, dz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            side = rng.choice((-1, 1)); cx_, cz_ = x - dz * side * rng.uniform(14, 22), z + dx * side * rng.uniform(14, 22)
            for j in range(rng.randint(2, 3)):
                xx, zz = cx_ + rng.uniform(-6, 6), cz_ + rng.uniform(-6, 6)
                if on_path(xx, zz, 4) or not free(xx, zz, 4): continue
                key, fn = opts[(n + j) % len(opts)] if j else opts[rng.randrange(4)]
                place(key, fn, xx, zz, rng.uniform(0, 360), s=rng.uniform(.8, 1.1), sink=.9, group='Relics'); reserve(xx, zz, 4)
            n += 1

def build():
    for loc, tgt, _f in SHOTS.values(): reserve(loc[0], loc[2], 3)
    ground(); horizon(); paving()
    set_pieces(); waystones(); dig_spots(); fragments(random.Random(17)); nature(random.Random(21))
    place_soft(random.Random(7))

# ------------------------------------------------------------------ look: high midday sun, deep blue sky, light heat haze
SUN_EL, SUN_AZ = 64.0, 205.0
def look():
    w = bpy.data.worlds.new('Noon'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.82, .84, .82, 1)          # bleached horizon (heat haze)
    cr.elements[1].position = .5; cr.elements[1].color = (.012, .07, .42, 1)          # deep blue zenith
    e = cr.elements.new(.04); e.color = (.5, .66, .9, 1)
    e = cr.elements.new(.16); e.color = (.1, .3, .78, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .9
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .12; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 5.2; sun.data.color = (1.0, .95, .86); sun.data.angle = math.radians(1.2)
    el = math.radians(SUN_EL); az = math.radians(SUN_AZ)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .9; fill.data.color = (.55, .7, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.4, .5, .6)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    bounce = bpy.data.objects.new('SandBounce', bpy.data.lights.new('SandBounce', 'SUN')); SC.collection.objects.link(bounce)
    bounce.data.energy = .55; bounce.data.color = (1.0, .82, .55); bounce.data.use_shadow = False
    bounce.rotation_euler = (-(r2b((0, -1, 0)) - r2b((0, 0, 0)))).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    for k, v in (('volumetric_tile_size', '4'), ('volumetric_end', 3000.0), ('volumetric_start', 1.0), ('volumetric_distribution', .9), ('volumetric_samples', 48)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (3600, 3600, 360); hz.location = (0, 0, 150); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00006
    pv.inputs['Color'].default_value = (1.0, .9, .74, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 9000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SHOTS = {   # vertical FOV (Roblox-style)
    'map_beauty.png': ((110, 42, 285), (-15, 24, -40), 40),
    'map_overview.png': ((300, 330, 440), (-10, 0, -20), 50),
    'map_top.png': ((0, 1500, 1), (0, 0, 0), 38),
    'map_spawn.png': ((SPAWN[0], 7.5, SPAWN[2] + 6), (0, 30, -30), 60),
    'map_camp.png': ((CAMP[0] - 40, 14, CAMP[1] + 40), (CAMP[0], 3, CAMP[1] - 6), 55),
    'map_oasis.png': ((OASIS[0] + 34, 14, OASIS[1] + 30), (OASIS[0], 4, OASIS[1]), 55),
    'map_obelisks.png': ((OBEL[0] - 70, 14, OBEL[1] + 40), (OBEL[0], 10, OBEL[1] - 10), 55),
    'map_colossus.png': ((COLO[0] - 50, 14, COLO[1] + 50), (COLO[0], 16, COLO[1]), 55),
    'map_skeleton.png': ((-180, 16, -60), (-235, 6, -150), 58),
    'map_temple.png': ((TEMPLE[0] + 64, 16, TEMPLE[1] + 22), (TEMPLE[0], -2, TEMPLE[1]), 55),
    'map_city.png': ((60, 26, 90), (0, 22, -30), 55),
}
if __name__ == '__main__':
    build()
    bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
    look()
    st = sum(STATIC_TRIS.values())
    json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0], 'static_tris': STATIC_TRIS, 'static_total': st,
               'kit_tris': {k: v[1] for k, v in LIB.items()}, 'rejected_soft': REJECT}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
    json.dump({'spawn': SPAWN, 'anchors': ANCHORS, 'sun': {'elevation': SUN_EL, 'azimuth': SUN_AZ}}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'dune_map.blend'))
    print('MAP_STATS', sum(COUNT.values()), TRIS[0], 'static', st, 'rejected', len(REJECT))
    if 'norender' not in ARGS:
        only = [a for a in ARGS if a.endswith('.png')]
        for n, (l, t, fov) in SHOTS.items():
            if only and n not in only: continue
            shot(n, l, t, fov)
    print('MAP_OK', sum(COUNT.values()), TRIS[0])
