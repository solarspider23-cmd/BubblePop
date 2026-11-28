# blender -b --factory-startup --python candy_map.py [-- norender] -> Sugarcrest Kingdom (candy_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud).
# Archetype: BOARD-GAME TRAIL. One straight Royal Road from the spawn plaza to the castle, plus a west and an east trail
# that wind round the kingdom as runs of coloured candy tiles (board-game squares) with "stops" (round tile plazas) at
# every station. A chocolate river from Fudge Falls cuts across: crossed by a waffle bridge (Royal Road), a biscuit
# bridge (west) and marshmallow stepping stones (east). The castle sits on a raised hill inside a jelly moat.
import sys, os, math, random, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import candy_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean(); F.MATS.clear(); FP._PM.clear()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ================================================================== layout data
SPAWN = (0, 142); PLAZA = (0, 168); PLAZA_R = 33
CASTLE = (0, -180); PLAT_R, MOAT_R, GLACIS_R = 58.0, 74.0, 84.0
PLAT_Y, MOAT_BED, JELLY_Y = 6.0, 0.0, 3.6
RIVER_Y = -2.5
RIVER = [(-226, -100), (-185, -80), (-140, -58), (-95, -38), (-50, -22), (0, -14), (50, -20), (100, -38), (145, -40),
         (185, -18), (215, 20), (240, 70), (262, 118), (285, 150)]
FALLS = (-262, -104)
# trails: (name, polyline, width). Bridges / stones link pieces across the river.
ROYAL_S = [(0, 136), (0, 11)]
ROYAL_N = [(0, -39), (0, -84)]
ROYAL_C = [(0, -124), (0, -148)]                     # castle court: plateau edge -> gate
WEST_S = [(-30, 162), (-62, 158), (-98, 152), (-128, 132), (-148, 100), (-156, 60), (-158, 22), (-160, -20), (-161, -40)]
WEST_N = [(-139, -86), (-140, -106), (-150, -124), (-120, -136), (-82, -126), (-48, -106), (-16, -92)]
EAST_S = [(30, 162), (62, 158), (98, 152), (130, 132), (158, 104), (176, 78), (182, 50), (184, 22)]
EAST_N = [(224, -16), (214, -48), (180, -74), (130, -94), (76, -102), (16, -92)]
TRAILS = [('Royal_S', ROYAL_S, 14), ('Royal_N', ROYAL_N, 14), ('Royal_C', ROYAL_C, 14), ('West_S', WEST_S, 12),
          ('West_N', WEST_N, 12), ('East_S', EAST_S, 12), ('East_N', EAST_N, 12)]
# stops: round tile plazas (centre, radius, colour)
STOPS = {'Shop': ((-98, 160), 13, 'berry'), 'Bakery': ((98, 160), 13, 'orange'), 'Gumball': ((176, 80), 12, 'cherry'),
         'Egg': ((-150, -124), 12, 'lime'), 'Forecourt': ((0, -92), 18, 'lemon')}
HILLS = [(-62, 92, 40, 22, 'vanilla'), (64, 96, 40, 20, 'pinkf'), (-58, 30, 28, 12, 'choc'), (70, 36, 30, 13, None),
         (-205, 160, 46, 26, 'pinkf'), (200, 186, 42, 22, 'vanilla'), (-212, 40, 40, 24, 'vanilla'), (-98, -170, 36, 18, 'pinkf'),
         (128, -150, 44, 24, 'vanilla'), (226, -96, 38, 26, 'pinkf'), (-150, 205, 32, 14, 'choc'), (120, 214, 28, 12, None),
         (-228, -170, 36, 22, 'vanilla'), (172, -194, 32, 18, 'choc')]

# ================================================================== geometry helpers
def seg_d(px, pz, a, b):
    ax, az = a; bx, bz = b; dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else clamp(((px - ax) * dx + (pz - az) * dz) / L2)
    return math.hypot(px - ax - t * dx, pz - az - t * dz)
def poly_d(px, pz, pl): return min(seg_d(px, pz, a, b) for a, b in zip(pl, pl[1:]))
def resample(pl, step):
    out = [Vector((pl[0][0], 0, pl[0][1]))]
    for a, b in zip(pl, pl[1:]):
        a, b = Vector((a[0], 0, a[1])), Vector((b[0], 0, b[1])); n = max(1, int((b - a).length / step))
        out += [a.lerp(b, k / n) for k in range(1, n + 1)]
    return out
def smooth_pl(pl, it=3):
    """Chaikin corner cutting (keeps the ends)"""
    for _ in range(it):
        q = [pl[0]]
        for a, b in zip(pl, pl[1:]):
            q += [(a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25), (a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75)]
        q.append(pl[-1]); pl = q
    return pl
RIVER_S = smooth_pl(RIVER)
TRAILS = [(n, smooth_pl(p, 2), w) for n, p, w in TRAILS]

def dist_castle(x, z): return math.hypot(x - CASTLE[0], z - CASTLE[1])

# ================================================================== height function (ground AND placement)
def bump(d, r): return 0.0 if d >= r else (math.cos(d / r * math.pi) * .5 + .5) ** 1.3
def path_mask(x, z):
    """0 on trails / plazas, 1 away from them (hills fade out near them)"""
    d = min(poly_d(x, z, p) - w / 2 for n, p, w in TRAILS)
    d = min(d, math.hypot(x - PLAZA[0], z - PLAZA[1]) - PLAZA_R)
    for (c, r, col) in STOPS.values(): d = min(d, math.hypot(x - c[0], z - c[1]) - r)
    return smooth((d - 4) / 22)
def H0(x, z):
    """frosting land before the river / castle carve"""
    y = (nz(x, 0, z, 70, 2) - .5) * 3.0 + (nz(x, 0, z, 23, 5) - .5) * .8
    pm = path_mask(x, z)
    for hx, hz, hr, hh, cap in HILLS:
        y += hh * bump(math.hypot(x - hx, z - hz), hr) * pm
    m = max(abs(x), abs(z) * 1.05)
    y += 34 * smooth((m - 245) / 110) * (.75 + .5 * nz(x, 0, z, 60, 9))       # rises behind the mountain ring
    return y
def castle_h(x, z, y):
    d = dist_castle(x, z)
    if d < PLAT_R - 2: return PLAT_Y
    if d < PLAT_R + 3: return lerp(PLAT_Y, MOAT_BED, smooth((d - PLAT_R + 2) / 5))
    if d < MOAT_R - 3: return MOAT_BED
    if d < MOAT_R + 2: return lerp(MOAT_BED, PLAT_Y, smooth((d - MOAT_R + 3) / 5))
    if d < GLACIS_R: return PLAT_Y
    return lerp(PLAT_Y, y, smooth((d - GLACIS_R) / 34))
def H(x, z):
    y = H0(x, z)
    y = castle_h(x, z, y) if dist_castle(x, z) < GLACIS_R + 34 else y
    dr = poly_d(x, z, RIVER_S)
    if dr < 26:
        y = lerp(RIVER_Y - 3.5, y, smooth((dr - 9) / 16))
    df = math.hypot(x - FALLS[0], z - FALLS[1])                                 # falls pool
    if df < 50: y = lerp(RIVER_Y - 3.5, y, smooth((df - 30) / 18))
    return y

# ================================================================== instancing + placement
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; PLACED = []; ANCHORS = []
def kit(key, fn):
    if key not in LIB:
        P = fn(); LIB[key] = (F.to_kit(P, KIT), P.tris, P.name)
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
DEFER = []; DEFER_ON = [True]; REJECT = []
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    meshes = kit(key, fn)
    if DEFER_ON[0] and SOFT_RE.search(LIB[key][2]):
        DEFER.append((key, fn, x, z, yaw, s, y, sink, group)); return None
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
    name = LIB[key][2]; water = bool(WATER_RE.search(name))
    if not SOFT_RE.search(name):                                                 # hard props: fitted (auto y) + owners
        if auto and not ROCK_RE.search(name) and not water:
            r = fit(obs, Mr, x, y, z, y_at, False, name)
            if r is None:
                print('FIT_REJECT', key, round(x), round(z))
                for ob in obs: bpy.data.objects.remove(ob)
                return None
            x, y, z = r
        add_owner(obs, water)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    PLACED.append((obs, key))
    return y
def unplace(obs, key):
    for ob in obs: bpy.data.objects.remove(ob)
    COUNT[key] -= 1; TRIS[0] -= LIB[key][1]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def to_world(x, z, yaw, lx, lz):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return x + lx * c + lz * s, z - lx * s + lz * c
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def on_hard(x, z, m=0.0):
    """trails, plazas, river, castle hill, falls: nothing scattered there"""
    if any(poly_d(x, z, p) < w / 2 + 2 + m for n, p, w in TRAILS): return True
    if math.hypot(x - PLAZA[0], z - PLAZA[1]) < PLAZA_R + 3 + m: return True
    for (c, r, col) in STOPS.values():
        if math.hypot(x - c[0], z - c[1]) < r + 3 + m: return True
    if poly_d(x, z, RIVER_S) < 21 + m: return True
    if dist_castle(x, z) < GLACIS_R + 4 + m: return True
    if math.hypot(x - FALLS[0], z - FALLS[1]) < 62 + m: return True
    return not (-262 < x < 262 and -262 < z < 248)

def anchor(name, kind, group, x, y, z, yaw, size, **attrs):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group, 'pos': [round(x, 2), round(y, 2), round(z, 2)],
                    'yaw': round(yaw % 360, 1), 'size': list(size), 'attrs': attrs})
def station(key, fn, prop_name, x, z, yaw, hook, attrs=None, y=None, group='Stations', s=1.0):
    yy = place(key, fn, x, z, yaw, s=s, y=y, group=group); PTS.append((x, z, 16 * s))
    for k, (lx, ly, lz, lyaw, w, h) in enumerate(FP.SIGNS.get(prop_name, [])):
        wx, wz = to_world(x, z, yaw, lx * s, (lz - .26) * s)
        anchor('%s_Sign%s' % (hook, '' if k == 0 else k + 1), 'sign', 'Signs', wx, yy + ly * s, wz, yaw + lyaw, (round(w * s, 2), round(h * s, 2), .1), Station=hook)
    return yy

# ================================================================== static surfaces
def mesh_obj(name, mb, group='Ground'):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    add_owner([ob], bool(WATER_RE.search(name))); return ob

# ---- placement fit: the exporter's hard checks (roblox_export.py 6c) run while placing. Statics + every placed hard
# prop are owners; an auto-grounded prop (y None) is raised in 0.25 steps (its base stays bedded) or nudged until
# no more than 3.5% of its body (7% for foliage) is inside one owner and it does not float; None = nowhere fits
from mathutils.bvhtree import BVHTree
import re
ROCK_RE = re.compile(r'(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|mountain')   # = the export's --rock for this map
WATER_RE = re.compile(r'(?i)water|lake|river|stream|pond|pool|falls|moat')
FLOAT_OK_RE = re.compile(r'(?i)hang|vine|ivy|lamp-rope|rope|cloud|bird|lily|canopy|_leaves|_branches|glow|beam|debris|orbit')
OWN = []; WOWN = []                                        # solid owners / water surfaces: [(BVHTree, lo, hi)]
DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
DOWN = Vector((0, 0, -1))
def add_owner(obs, water=False):
    bm = bmesh.new()
    for ob in obs:
        m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    if not bm.verts: bm.free(); return
    vs = [v.co for v in bm.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    (WOWN if water else OWN).append((BVHTree.FromBMesh(bm), lo, hi)); bm.free()
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
def _top(o, dist):
    top = None
    for t, a, b in OWN + WOWN:
        if a.x - .1 <= o.x <= b.x + .1 and a.y - .1 <= o.y <= b.y + .1:
            h = t.ray_cast(o, DOWN, dist)
            if h[0] is not None and (top is None or h[0].z > top): top = h[0].z
    return top
def fit_bad(obs, soft, name):
    pts = []; nv = sum(len(ob.data.vertices) for ob in obs); step = max(1, nv // 160)
    for ob in obs:
        vs = ob.data.vertices; pts += [ob.matrix_world @ vs[i].co for i in range(0, len(vs), step)]
    lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
    body = [q for q in pts if q.z > lo_z + max(.6, .15 * (hi_z - lo_z))]
    if body and sum(1 for q in body if _inside_one(q)) > (.07 if soft else .035) * len(body): return 'clip'
    if FLOAT_OK_RE.search(name): return None
    if soft:
        o = obs[0].matrix_world.translation; t = _top(Vector((o.x, o.y, lo_z + 3)), 80)
        return 'float' if t is not None and lo_z - t > .9 else None
    cs = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
    lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))); hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
    c = (lo + hi) / 2; sx, sy = (hi.x - lo.x) * .35, (hi.y - lo.y) * .35; top = None
    for dx, dy in ((0, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)):
        t = _top(Vector((c.x + dx * sx, c.y + dy * sy, hi.z + .5)), hi.z - lo.z + 200)
        if t is not None and (top is None or t > top): top = t
    return 'float' if top is None or lo.z - top > .4 else None
def fit(obs, Mr, x, y, z, y_at, soft, name):
    rng = random.Random(int(x * 7 + z * 13))
    for t in range(10):
        jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (1 + t), rng.uniform(-1, 1) * (1 + t))
        y0 = y if t == 0 else y_at(x + jx, z + jz)
        for k in range(16):
            M = Matrix.Translation(r2b((x + jx, y0 + k * .25, z + jz))) @ Mr
            for ob in obs: ob.matrix_world = M
            r = fit_bad(obs, soft, name)
            if r is None: return x + jx, y0 + k * .25, z + jz
            if r == 'float': break
    return None

def axis_coords(lo, hi, inner, fine, coarse):
    xs = []; x = lo
    while x < -inner: xs.append(x); x += coarse
    x = -inner
    while x < inner: xs.append(x); x += fine
    x = inner
    while x <= hi: xs.append(x); x += coarse
    return xs

def ground():
    xs = axis_coords(-420, 420, 268, 4.5, 30); zs = axis_coords(-420, 420, 268, 4.5, 30)
    bm = bmesh.new(); V = [[bm.verts.new((x, H(x, z), z)) for z in zs] for x in xs]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            bm.faces.new((V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    uF, uJ, uP = F.PAL.u('frost'), F.PAL.u('jelly'), F.PAL.u('pinkf')
    def shade(f):
        c = f.calc_center_median(); d = dist_castle(c.x, c.z)
        if PLAT_R + 2.5 < d < MOAT_R - 2.5: return [(uJ, .3)] * len(f.loops)              # moat floor
        if PLAT_R - 2.5 < d < MOAT_R + 2.5: return [(F.PAL.u('ginger'), .55 + f.normal.y * .1)] * len(f.loops)   # biscuit moat walls
        if poly_d(c.x, c.z, RIVER_S) < 17 and c.y < RIVER_Y + .5: return [(F.PAL.u('choc'), .2)] * len(f.loops)
        out = []
        for l in f.loops:
            p = l.vert.co
            v = .5 + (nz(p.x, 0, p.z, 26, 3) - .5) * .22 + clamp((p.y - 2) / 40) * .25 + f.normal.y * .05
            out.append((uF, clamp(v, .12, .9)))
        return out
    mb = MB(); mb.add(bm, shade, smooth=True)
    mesh_obj('Ground', mb)

def drape_strip(mb, pl, width, s0, s1, col, lift=.3, nu=3, nv=2, base=.6, skirt=.5):
    """one board tile: the polyline section s0..s1 (arc length) across `width`, draped on H, with side skirts"""
    def at_s(s):
        acc = 0.0
        for a, b in zip(pl, pl[1:]):
            L = (b - a).length
            if acc + L >= s:
                t = (s - acc) / L; p = a.lerp(b, t); d = (b - a).normalized(); return p, Vector((-d.z, 0, d.x))
            acc += L
        a, b = pl[-2], pl[-1]; d = (b - a).normalized(); return b, Vector((-d.z, 0, d.x))
    bm = bmesh.new(); grid_v = []
    for i in range(nv + 1):
        p, n = at_s(lerp(s0, s1, i / nv)); row = []
        for j in range(nu + 1):
            q = p + n * (-width / 2 + width * j / nu)
            row.append(bm.verts.new((q.x, H(q.x, q.z) + lift, q.z)))
        grid_v.append(row)
    for i in range(nv):
        for j in range(nu): bm.faces.new((grid_v[i][j], grid_v[i][j + 1], grid_v[i + 1][j + 1], grid_v[i + 1][j]))
    ring = [grid_v[0][j] for j in range(nu + 1)] + [grid_v[i][nu] for i in range(1, nv + 1)] + \
           [grid_v[nv][j] for j in range(nu - 1, -1, -1)] + [grid_v[i][0] for i in range(nv - 1, 0, -1)]
    low = [bm.verts.new(v.co - Vector((0, skirt + lift, 0))) for v in ring]
    for k in range(len(ring)):
        m = (k + 1) % len(ring); bm.faces.new((ring[k], low[k], low[m], ring[m]))
    for f in bm.faces:
        f.normal_update()
        if len(f.verts) == 4 and abs(f.normal.y) > .5 and f.normal.y < 0: f.normal_flip()
    bm.normal_update()
    cen = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    for f in bm.faces:
        if abs(f.normal.y) < .5 and f.normal.dot(f.calc_center_median() - cen) < 0: f.normal_flip()
    mb.add(bm, FP.S(col, base=base, up=.2, jit=0))

BOARD = ['cherry', 'blue', 'lemon', 'lime', 'grape', 'orange']
def trails():
    """board-game tile runs (TILE long, 0.7 gaps) + sprinkles on them; round stop plazas"""
    tiles = MB(); spr = MB(); rng = random.Random(7); k0 = 0; TILE = 8.0
    for name, pl, w in TRAILS:
        pts = resample(pl, 2.0); L = sum((b - a).length for a, b in zip(pts, pts[1:]))
        n = max(1, int(L / TILE)); step = L / n
        for i in range(n):
            col = BOARD[(k0 + i) % len(BOARD)]
            drape_strip(tiles, pts, w, i * step + .35, (i + 1) * step - .35, col)
            for q in range(int(w * step * .09)):                             # sprinkles on the tile
                s = rng.uniform(i * step + 1, (i + 1) * step - 1); u = rng.uniform(-w / 2 + 1, w / 2 - 1)
                acc = 0.0
                for a, b in zip(pts, pts[1:]):
                    Ls = (b - a).length
                    if acc + Ls >= s: p = a.lerp(b, (s - acc) / Ls); d = (b - a).normalized(); break
                    acc += Ls
                p = p + Vector((-d.z, 0, d.x)) * u
                bmr = FP.sprinkle(rng.uniform(.8, 1.2), .16)
                bmesh.ops.rotate(bmr, cent=Vector(), matrix=Matrix.Rotation(rng.uniform(0, math.tau), 3, 'Y'), verts=bmr.verts)
                bmesh.ops.translate(bmr, vec=Vector((p.x, H(p.x, p.z) + .45, p.z)), verts=bmr.verts)
                scol = 'vanilla' if rng.random() < .45 else rng.choice(['berry', 'lemon', 'blue', 'lime', 'cherry', 'grape'])
                if scol == col: scol = 'vanilla'
                spr.add(bmr, FP.S(scol, base=.7, up=.1, jit=0))
        k0 += n
    # spawn plaza: concentric rings of coloured segments round the fountain
    def disc_tiles(cx, cz, r0, r1, nseg, cols, lift=.3):
        for k in range(nseg):
            a0, a1 = k * math.tau / nseg + .02, (k + 1) * math.tau / nseg - .02
            bm = bmesh.new(); top = []; bot = []
            for rr in (r0 + .3, r1 - .3):
                for t in range(4):
                    a = lerp(a0, a1, t / 3); x, z = cx + math.cos(a) * rr, cz + math.sin(a) * rr
                    top.append(bm.verts.new((x, H(x, z) + lift, z)))
            vs = top
            for t in range(3):
                bm.faces.new((vs[t], vs[t + 1], vs[4 + t + 1], vs[4 + t]))
            ring = [vs[0], vs[1], vs[2], vs[3], vs[7], vs[6], vs[5], vs[4]]
            low = [bm.verts.new(v.co - Vector((0, .8, 0))) for v in ring]
            for i in range(8):
                j = (i + 1) % 8; bm.faces.new((ring[i], low[i], low[j], ring[j]))
            bm.normal_update()
            for f in bm.faces:
                c = f.calc_center_median()
                if abs(f.normal.y) > .5:
                    if f.normal.y < 0: f.normal_flip()
                else:
                    d = Vector((c.x - cx, 0, c.z - cz)); rmid = (r0 + r1) / 2
                    want = d if d.length > rmid else -d
                    if f.normal.dot(want) < 0: f.normal_flip()
            tiles.add(bm, FP.S(cols[k % len(cols)], base=.6, up=.2, jit=0))
    disc_tiles(PLAZA[0], PLAZA[1], 17.4, 24.5, 16, BOARD)
    disc_tiles(PLAZA[0], PLAZA[1], 24.5, PLAZA_R, 24, ['vanilla', 'pinkf'])
    for (c, r, col) in STOPS.values():
        disc_tiles(c[0], c[1], 0.0, r * .45, 6, [col])
        disc_tiles(c[0], c[1], r * .45, r, 12, [col, 'vanilla'])
    mesh_obj('Path_Tiles', tiles); mesh_obj('Sprinkles', spr)

def river():
    """chocolate river surface (glossy, streaked) + graham-crumb banks"""
    pts = resample(RIVER_S, 3.0); mb = MB(); bk = MB()
    bm = bmesh.new(); rows = []; W = 40.0; nu = 8
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]; d = (b - a).normalized(); n = Vector((-d.z, 0, d.x))
        rows.append([bm.verts.new((p + n * (-W / 2 + W * j / nu)).to_tuple()) for j in range(nu + 1)])
        for v in rows[-1]: v.co.y = RIVER_Y
    for i in range(len(rows) - 1):
        for j in range(nu): bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    u = F.PAL.u('choc')
    mb.add(bm, lambda f: [(u, clamp(.62 + .14 * math.sin(l.vert.co.x * .07 + l.vert.co.z * .11) + (nz(l.vert.co.x, 0, l.vert.co.z, 9, 4) - .5) * .25, .1, .85)) for l in f.loops], smooth=True)
    mesh_obj('River_Choc', mb)
    # crumb banks: a scalloped band on each shore, draped
    for side in (-1, 1):
        bm = bmesh.new(); prev = None
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]; d = (b - a).normalized(); n = Vector((-d.z, 0, d.x)) * side
            r_in = 15.5; r_out = 22.5 + 2.2 * math.sin(i * .9) + 1.2 * math.sin(i * 2.3)
            row = []
            for t in (0, .5, 1):
                q = p + n * lerp(r_in, r_out, t); row.append(bm.verts.new((q.x, max(H(q.x, q.z), RIVER_Y + .05) + .12, q.z)))
            if prev:
                for j in range(2): bm.faces.new((prev[j], prev[j + 1], row[j + 1], row[j]))
            prev = row
        for f in bm.faces:
            f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        uG = F.PAL.u('ginger')
        bk.add(bm, lambda f: [(uG, clamp(.62 + (nz(l.vert.co.x, 0, l.vert.co.z, 4, 6) - .5) * .3, .3, .85)) for l in f.loops])
    mesh_obj('Banks_Crumb', bk)

def moat():
    mb = MB()
    bm = FP.lathe([(MOAT_R + 3, JELLY_Y), (PLAT_R - 3, JELLY_Y)], sides=96, close_top=False)
    for v in bm.verts: v.co.x += CASTLE[0]; v.co.z += CASTLE[1]
    mb.add(bm, FP.S('jelly', base=.7, up=0, jit=0), smooth=True)
    mesh_obj('Moat_Jelly', mb); mb = MB()
    # piped icing rim round the plateau edge and the outer moat lip (one rope each, cheap): its own static, not water
    for R, y in ((PLAT_R - 2.2, PLAT_Y - .35), (MOAT_R + 2.2, PLAT_Y - .35)):         # on the flat lips (bedded a little), not over the moat slopes
        pts = [Vector((CASTLE[0] + math.cos(a) * R, y, CASTLE[1] + math.sin(a) * R)) for a in [k * math.tau / 72 for k in range(72)]]
        mb.add(FP.piping(pts, .6, beads=False, sides=6, closed=True), FP.S('vanilla', base=.86, jit=0), smooth=True)
    mesh_obj('IcingCaps_CastleRim', mb)

def icing_caps():
    """icing poured over the frosting hilltops: a draped sheet with a thick rounded lip, a scalloped edge and a few
    long drips running down the slope (gaussian lobes in r(angle), so every drip has a round tip)"""
    mb = MB(); rng = random.Random(4)
    for k, (hx, hz, hr, hh, cap) in enumerate(HILLS):
        if not cap or hh < 9: continue
        top = H(hx, hz); lv = top - hh * .36; NA = 112
        edge = []
        for a in range(NA):
            ang = a * math.tau / NA; r = .5
            while r < hr and H(hx + math.cos(ang) * r, hz + math.sin(ang) * r) > lv: r += .6
            edge.append(r)
        for _ in range(3): edge = [(edge[i - 1] + edge[i] * 2 + edge[(i + 1) % NA]) / 4 for i in range(NA)]
        lob = rng.randint(5, 8); ph = rng.uniform(0, 6)
        drips = [(rng.uniform(0, math.tau), rng.uniform(.12, .26), rng.uniform(.06, .09)) for _ in range(rng.randint(4, 6))]
        def ext(ang):
            e = .08 * (.5 + .5 * math.cos(ang * lob + ph))
            for a0, L, w in drips:
                d = math.atan2(math.sin(ang - a0), math.cos(ang - a0)); e += L * math.exp(-(d / w) ** 2)
            return e
        bm = bmesh.new(); rings = []; NR = 7
        for i in range(1, NR + 1):
            row = []
            for a in range(NA):
                ang = a * math.tau / NA; r = edge[a] * (1 + ext(ang)) * (i / NR) ** .85
                x, z = hx + math.cos(ang) * r, hz + math.sin(ang) * r
                row.append(bm.verts.new((x, H(x, z) + .5, z)))
            rings.append(row)
        lip = []
        for a in range(NA):                                                 # rounded lip: the edge rolls down into the ground
            v = rings[-1][a].co; ang = a * math.tau / NA; o = Vector((math.cos(ang), 0, math.sin(ang))) * .35
            lip.append(bm.verts.new((v.x + o.x, H(v.x + o.x, v.z + o.z) - .25, v.z + o.z)))
        rings.append(lip)
        c0 = bm.verts.new((hx, top + .6, hz))
        for a in range(NA):
            b = (a + 1) % NA
            bm.faces.new((c0, rings[0][a], rings[0][b]))
            for i in range(len(rings) - 1): bm.faces.new((rings[i][a], rings[i + 1][a], rings[i + 1][b], rings[i][b]))
        bm.normal_update()
        for f in bm.faces:
            c = f.calc_center_median(); want = Vector((0, 1, 0)) if abs(f.normal.y) > .35 else Vector((c.x - hx, 0, c.z - hz))
            if f.normal.dot(want) < 0: f.normal_flip()
        mb.add(bm, FP.S(cap, grad=(lv - hh * .3, top, .66, .93), up=.12), smooth=True)
    mesh_obj('IcingCaps', mb)

def horizon():
    """cotton-candy cloud ring beyond the mountains (soft subdivided puffs, pastel)"""
    mb = MB(); rng = random.Random(21)
    for k in range(12):
        a = k * math.tau / 12 + rng.uniform(-.12, .12); d = rng.uniform(580, 780); y = rng.uniform(40, 130)
        cx, cz = math.cos(a) * d, math.sin(a) * d; col = ['cotton', 'cloud', 'pinkf'][k % 3]
        for j in range(4):
            r = rng.uniform(32, 52); off = Vector((rng.uniform(-70, 70), rng.uniform(-8, 16), rng.uniform(-30, 30)))
            off.rotate(Matrix.Rotation(-a, 3, 'Y'))
            mb.add(F.at(FP.soft(r, k * 13 + j, sub=3, amp=.1, sq=(1.4, .62, 1)), (cx + off.x, y + off.y, cz + off.z)),
                   FP.S(col, grad=(y - 30, y + 35, .6, .97), up=.1), smooth=True)
    mesh_obj('Clouds_Horizon', mb)

# ================================================================== build
def soft_pass(rng):
    """deferred foliage: place, test against a BVH of every solid (the exporter's clip / float check), jitter or drop"""
    bm = bmesh.new()
    for c in SUB.values():
        for ob in c.objects:
            if SOFT_RE.search(ob.data.name): continue
            m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    SOLID = BVHTree.FromBMesh(bm); bm.free()
    DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    def inside(p):
        back = 0
        for d in DIRS:
            hit, nrm, i, dist = SOLID.ray_cast(p, d, 400)
            if hit is not None and nrm.dot(d) > 0: back += 1
        return back >= 5
    def fail(obs):
        for ob in obs:
            M = ob.matrix_world; vs = ob.data.vertices; step = max(1, len(vs) // 160)
            pts = [M @ vs[i].co for i in range(0, len(vs), step)]
            lo = min(q.z for q in pts); hi = max(q.z for q in pts)
            body = [q for q in pts if q.z > lo + .15 * (hi - lo)]
            if body and sum(1 for q in body if inside(q)) / len(body) > .04: return True
            o = M.translation
            hit = SOLID.ray_cast(Vector((o.x, o.y, lo + 3)), Vector((0, 0, -1)), 80)
            if hit[0] is not None and lo - hit[0].z > .8: return True
        return False
    DEFER_ON[0] = False
    for key, fn, x, z, yaw, s, y, sink, group in DEFER:
        ok = False
        for t in range(8):
            jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (2 + t * 1.5), rng.uniform(-1, 1) * (2 + t * 1.5))
            if t and on_hard(x + jx, z + jz): continue
            place(key, fn, x + jx, z + jz, yaw, s, y, sink, group)
            obs, k = PLACED.pop()
            if fail(obs): unplace(obs, k); continue
            PLACED.append((obs, k)); ok = True; break
        if not ok: REJECT.append((key, round(x), round(z)))
    DEFER_ON[0] = True

def build():
    rng = random.Random(11)
    # --- hero: castle on its hill + drawbridge; Fudge Falls at the river head
    place('castle', FP.candy_castle, CASTLE[0], CASTLE[1], 180, y=PLAT_Y - .3, group='Hero')
    place('drawbridge', FP.drawbridge, 0, CASTLE[1] + PLAT_R - 2.0, 0, y=PLAT_Y - .1, group='Hero')
    for part in ('mountain', 'falls', 'pool'):
        place('falls_' + part, lambda part=part: FP.choco_falls(part), FALLS[0], FALLS[1], face(*FALLS, -150, -64), y=RIVER_Y - .1, group='Hero')
    fyaw = face(*FALLS, -150, -64); sx_, sz_ = to_world(*FALLS, fyaw, 0, -35)
    anchor('FallsSplash', 'vfx', 'Landmarks', sx_, RIVER_Y + .5, sz_, fyaw, (14, 4, 10), Effect='ChocolateSplash')
    cx_, cz_ = to_world(*FALLS, fyaw, 0, -31)
    anchor('FallsCave', 'vfx', 'Landmarks', cx_, RIVER_Y + 28, cz_, fyaw, (12, 6, 4), Effect='ChocolateSpring')
    anchor('CastleGate', 'door', 'Landmarks', 0, PLAT_Y, CASTLE[1] + 26 + 3.5, 180, (12, 12, 2))
    # --- spawn plaza
    place('fountain', FP.cupcake_fountain, *PLAZA, 0, y=H(*PLAZA) + .1, group='Spawn'); PTS.append((*PLAZA, 18))
    place('spawncookie', FP.spawn_cookie, *SPAWN, 0, y=H(*SPAWN) + .2, group='Spawn')
    anchor('Spawn', 'spawn', 'Spawn', SPAWN[0], H(*SPAWN) + .9, SPAWN[1], 0, (10, 1, 10))
    anchor('CupcakeFountain', 'station', 'Stations', PLAZA[0], H(*PLAZA) + 3, PLAZA[1] - 17, 0, (8, 6, 4), Station='Fountain')
    # --- stations at their stops (front faces the stop)
    def at_stop(stop, prop_key, fn, pname, dx, dz, hook, attrs, s=1.0):
        (cx, cz), r, col = STOPS[stop]; x, z = cx + dx, cz + dz; yaw = face(x, z, cx, cz)
        y = station(prop_key, fn, pname, x, z, yaw, hook, s=s)
        fx, fz = to_world(x, z, yaw, 0, -9 * s)
        anchor(hook, 'station', 'Stations', fx, H(fx, fz) + 3, fz, yaw, (8, 6, 4), Station=hook, **attrs)
        return x, z, yaw, y
    at_stop('Shop', 'shop', FP.sweet_shop, 'SweetShop', 0, 28, 'SweetShop', {'Kind': 'shop'}, s=1.45)
    at_stop('Bakery', 'oven', FP.bakery_oven, 'BakeryOven', 0, 28, 'BakeryOven', {'Kind': 'upgrade'}, s=1.45)
    gx, gz, gyaw, gy = at_stop('Gumball', 'gumball', FP.gumball_machine, 'GumballMachine', 24, 18, 'GumballMachine', {'Kind': 'teleport'}, s=1.3)
    dx, dz = to_world(gx, gz, gyaw, 0, -6.6 * 1.3)
    anchor('GumballPortal', 'travel', 'Stations', dx, gy + 6.5, dz, gyaw, (8, 10, 3), Station='GumballMachine')
    at_stop('Egg', 'egg', FP.egg_machine, 'EggMachine', -24, -13, 'EggMachine', {'Kind': 'pets'}, s=1.45)
    at_stop('Forecourt', 'quest', FP.quest_stand, 'QuestStand', -26, 21, 'QuestStand', {'Kind': 'quests'}, s=1.3)
    # --- bridges, stepping stones, donut arches
    def bridge_on(key, fn, a, b):
        """bridge spanning trail end a -> trail end b; length = their distance, deck ends on the ground"""
        mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2; L = math.hypot(b[0] - a[0], b[1] - a[1]) + 1.0
        yaw = face(mx, mz, a[0], a[1]); y = (H(*a) + H(*b)) / 2 - .3
        place(key, lambda: fn(L=L), mx, mz, yaw, y=y, group='Bridges'); PTS.append((mx, mz, L / 2))
        return yaw
    bridge_on('waffle', FP.waffle_bridge, ROYAL_N[0], ROYAL_S[-1])
    bridge_on('biscuit', FP.biscuit_bridge, WEST_N[0], WEST_S[-1])
    a, b = Vector((EAST_S[-1][0], 0, EAST_S[-1][1])), Vector((EAST_N[0][0], 0, EAST_N[0][1]))
    n = 5
    for k in range(n):
        p = a.lerp(b, (k + 1) / (n + 1))
        place('mallow%d' % (k % 2), lambda k=k: FP.marshmallow(k % 2), p.x, p.z, rng.uniform(0, 360), y=-.2, group='Bridges')
        anchor('StepStone%d' % (k + 1), 'stepstone', 'Traversal', p.x, 1.2, p.z, 0, (6.8, 1, 6.8), Order=k + 1)
    def donut_on(pl, s, seed, glaze):
        pts = resample(pl, 2.0); acc = 0.0
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if acc + L >= s:
                p = a.lerp(b, (s - acc) / L); yaw = face(p.x, p.z, b.x, b.z)
                place('donut%d' % seed, lambda: FP.donut_arch(seed, glaze), p.x, p.z, yaw, y=H(p.x, p.z) - 1.0, group='Arches'); PTS.append((p.x, p.z, 26))
                return
            acc += L
    donut_on(TRAILS[0][1], 62, 0, 'pinkf')
    donut_on(TRAILS[3][1], 230, 1, 'choc')
    donut_on(TRAILS[5][1], 150, 2, 'lemon')
    # --- lamps along every trail (alternating sides), lollipops lining the Royal Road
    for name, pl, w in TRAILS:
        pts = resample(pl, 2.0); L = sum((b - a).length for a, b in zip(pts, pts[1:])); k = 0; s = 16.0
        while s < L - 8:
            acc = 0.0
            for a, b in zip(pts, pts[1:]):
                Ls = (b - a).length
                if acc + Ls >= s: p = a.lerp(b, (s - acc) / Ls); d = (b - a).normalized(); break
                acc += Ls
            side = 1 if k % 2 else -1; q = p + Vector((-d.z, 0, d.x)) * side * (w / 2 + 2.6)
            if free(q.x, q.z, 3) and poly_d(q.x, q.z, RIVER_S) > 20:
                if name.startswith('Royal_S'):
                    place('lolly%d' % (k % 4), lambda k=k: FP.lollipop_tree(k % 4), q.x, q.z, face(q.x, q.z, p.x, p.z) + 90, s=1.1, group='Royal')
                else:
                    place('lamp', FP.candy_lamp, q.x, q.z, face(q.x, q.z, p.x, p.z) + 90, group='Lamps')
                PTS.append((q.x, q.z, 3))
            k += 1; s += 26.0 if name.startswith('Royal') else 50.0
    # --- frame: gumdrop mountains round the edge (two depths), one hides where the river leaves
    mcols = ['grape', 'lime', 'berry', 'lemon', 'blue', 'orange']
    ring = [(-300, -300), (-170, -320), (-40, -340), (90, -330), (220, -315), (318, -230), (330, -110), (335, 20),
            (300, 152), (320, 270), (190, 320), (60, 330), (-80, 325), (-210, 320), (-330, 250), (-335, 120), (-330, -10), (-320, -160)]
    for k, (x, z) in enumerate(ring):
        col = mcols[k % 6]; s = rng.uniform(3.0, 4.4)
        place('mtn_%s' % col, lambda col=col, k=k: FP.gumdrop_mountain(mcols.index(col), col), x, z, rng.uniform(0, 360), s=s, sink=.4, group='Frame')
    for k, (x, z) in enumerate([(-250, -250), (250, -260), (-268, 210), (262, 236), (110, -262), (-120, -268)]):
        col = mcols[(k + 3) % 6]
        place('mtn_%s' % col, lambda col=col: FP.gumdrop_mountain(mcols.index(col), col), x, z, rng.uniform(0, 360), s=rng.uniform(1.8, 2.4), sink=.4, group='Frame')
    # --- set dressing near the stations (story clusters)
    for (x, z, yaw, key, fn) in ((-116, 176, 20, 'mac0', lambda: FP.macaron_stack(0)), (-80, 182, -10, 'mac1', lambda: FP.macaron_stack(1)),
                                 (118, 178, 15, 'mac2', lambda: FP.macaron_stack(2)), (80, 186, -25, 'mac1', lambda: FP.macaron_stack(1)),
                                 (-170, -140, 30, 'mac2', lambda: FP.macaron_stack(2))):
        if free(x, z, 3): place(key, fn, x, z, yaw, group='Dressing'); PTS.append((x, z, 3))
    for (x, z, yaw, sd) in ((46, 196, 40, 0), (-52, 120, -60, 1), (150, 210, 120, 2), (-196, 96, 200, 3)):
        if not on_hard(x, z): place('cone%d' % sd, lambda sd=sd: FP.giant_cone(sd), x, z, yaw, group='Dressing'); PTS.append((x, z, 9))
    # --- scatter (seeded): candy-cane forest (east), cotton-candy grove (north-west), meadows, river rocks
    def scatter(n, key, fn, r, s_rng, box_, pad=0.0, group='Scatter'):
        x0, x1, z0, z1 = box_; done = 0
        for _ in range(n * 80):
            if done >= n: break
            x, z = rng.uniform(x0, x1), rng.uniform(z0, z1)
            if on_hard(x, z, pad) or not free(x, z, r): continue
            PTS.append((x, z, r)); place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(*s_rng), group=group); done += 1
    for sd in range(4): scatter(10, 'cane%d' % sd, lambda sd=sd: FP.candy_cane(sd, 18), 4.5, (.7, 1.3), (110, 255, 20, 235), 2, 'CaneForest')
    for sd in range(4): scatter(3, 'cane%d' % sd, lambda sd=sd: FP.candy_cane(sd, 18), 4.5, (.7, 1.1), (20, 110, 30, 130), 2, 'CaneForest')
    for sd in range(4): scatter(4, 'cotton%d' % sd, lambda sd=sd: FP.cotton_candy_tree(sd), 7, (.9, 1.3), (-245, -40, -235, -70), 3, 'CottonGrove')
    for sd in range(4): scatter(2, 'cotton%d' % sd, lambda sd=sd: FP.cotton_candy_tree(sd), 7, (.9, 1.2), (-250, -40, 20, 235), 3, 'CottonGrove')
    for sd in range(4): scatter(2, 'lolly%d' % sd, lambda sd=sd: FP.lollipop_tree(sd), 5, (.9, 1.2), (-240, 240, -240, 240), 2, 'Lollipops')
    for sd in range(2): scatter(2, 'lolly%d' % sd, lambda sd=sd: FP.lollipop_tree(sd), 5, (1.0, 1.3), (90, 250, -250, -40), 2, 'Lollipops')
    for sd in range(4): scatter(1, 'gum%d' % sd, lambda sd=sd: FP.gumdrop_bush(sd), 3.5, (1.0, 1.4), (90, 250, -250, -40), 1, 'Gumdrops')
    for sd in range(4): scatter(7, 'gum%d' % sd, lambda sd=sd: FP.gumdrop_bush(sd), 3.5, (.9, 1.4), (-255, 255, -250, 240), 1, 'Gumdrops')
    for sd in range(3): scatter(4, 'beans%d' % sd, lambda sd=sd: FP.jelly_beans(sd), 3.5, (.9, 1.5), (-255, 255, -250, 240), 0, 'JellyBeans')
    for sd in range(3): scatter(7, 'flower%d' % sd, lambda sd=sd: FP.candy_flower(sd), 2.6, (.9, 1.3), (-255, 255, -250, 240), 0, 'Flowers')
    for (cx, cz) in ((-40, 112), (40, 120), (-110, 70), (110, 60), (-30, 60), (30, 74), (-100, 108), (150, 10), (-200, -40), (-60, -60),
                     (60, -66), (-190, 110), (190, 130), (-120, -90), (250, -140), (-30, 214), (40, 222)):
        for j in range(3):
            x, z = cx + rng.uniform(-9, 9), cz + rng.uniform(-9, 9)
            if on_hard(x, z) or not free(x, z, 2.6): continue
            PTS.append((x, z, 2.6))
            key, fn = [('gum%d' % (j % 4), lambda j=j: FP.gumdrop_bush(j % 4)), ('flower%d' % (j % 3), lambda j=j: FP.candy_flower(j % 3)),
                       ('beans%d' % (j % 3), lambda j=j: FP.jelly_beans(j % 3))][(j + int(cx)) % 3]
            place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.3), group='Meadows')
    # jelly-bean rocks along the river banks (outside the water line)
    pts = resample(RIVER_S, 3.0)
    for i in range(6, len(pts) - 6, 12):
        p = pts[i]; d = (pts[i + 1] - pts[i - 1]).normalized(); n = Vector((-d.z, 0, d.x)) * (1 if i % 2 else -1)
        q = p + n * rng.uniform(23, 27)
        if not any(poly_d(q.x, q.z, pl) < w / 2 + 3 for nm, pl, w in TRAILS) and free(q.x, q.z, 3) and dist_castle(q.x, q.z) > GLACIS_R + 4 and abs(q.x) < 262:
            PTS.append((q.x, q.z, 3)); place('beans%d' % (i % 3), lambda i=i: FP.jelly_beans(i % 3), q.x, q.z, rng.uniform(0, 360), s=rng.uniform(.9, 1.3), group='JellyBeans')
    # castle hill: lollipops flank the court path, gumdrops at the gate
    for sx in (-1, 1):
        place('lolly%d' % (sx + 1), lambda sx=sx: FP.lollipop_tree(sx + 1), sx * 20, -127, sx * 90, s=1.0, group='Hero')
        place('gum%d' % (sx + 1), lambda sx=sx: FP.gumdrop_bush(sx + 1), sx * 22, -146, 0, group='Hero')

# ================================================================== look: soft pastel late morning
def look():
    w = bpy.data.worlds.new('Sky'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.02; mr.inputs['From Max'].default_value = .4
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (1.0, .8, .72, 1); cr.elements[1].color = (.25, .5, 1.0, 1)
    e = cr.elements.new(.15); e.color = (1.0, .6, .82, 1)
    e = cr.elements.new(.4); e.color = (.6, .58, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.2; sun.data.color = (1, .93, .84); sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(52), 0, math.radians(-148))          # ~38 deg up, from the south-east (lights the castle front)
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (1700, 1700, 260); hz.location = (0, 0, 110); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00016; pv.inputs['Color'].default_value = (1, .9, .97, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False
    for me in bpy.data.meshes: FP.preview_mats(me)

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 5000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

ground(); trails(); river(); moat(); icing_caps(); horizon()
build()
soft_pass(random.Random(5))
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
static_tris = sum(len(ob.data.polygons) for ob in sub('Ground').objects)
look()
import roblox_materials as RM
RM.write_map(F.PAL, FP.roblox_materials(), os.path.join(HERE, 'material_map.json'),
             overrides={'Ground': {'frost': 'Snow'}, 'Clouds_Horizon': 'SmoothPlastic', 'GumdropBush': 'SmoothPlastic', 'GumdropMountain': {c: 'SmoothPlastic' for c in FP.CANDY},
                        'Path_Tiles': 'SmoothPlastic', 'IcingCaps': 'SmoothPlastic'})
json.dump({'anchors': ANCHORS, 'spawn': SPAWN}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': static_tris,
           'tris_total': TRIS[0] + static_tris, 'rejected_soft': REJECT, 'kit_tris': {k: v[1] for k, v in LIB.items()}},
          open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'candy_map.blend'))
print('STATS props', TRIS[0], 'static', static_tris, 'total', TRIS[0] + static_tris, 'rejected', len(REJECT))
if 'norender' not in ARGS:
    shot('map_beauty.png', (-150, 62, 214), (10, 6, -96), 30)
    shot('map_overview.png', (300, 250, 330), (0, -10, -40), 30)
    shot('map_spawn.png', (0, 7.5, 150), (0, 22, -180), 32)
    if 'more' in ARGS:
        shot('map_castle.png', (40, 22, -60), (0, 30, -180), 30)
        shot('map_falls.png', (-150, 20, -40), (-250, 26, -100), 30)
        shot('map_gumball.png', (148, 16, 128), (200, 14, 98), 30)
        shot('map_shop.png', (-62, 14, 132), (-98, 10, 186), 30)
        shot('map_bakery.png', (62, 14, 132), (98, 10, 186), 30)
        shot('map_egg.png', (-118, 14, -104), (-163, 10, -131), 30)
        shot('map_west.png', (-60, 30, 120), (-140, 8, 40), 30)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
