# blender -b --factory-startup --python onsen_map.py [-- norender] [-- name.png ...] -> Yumori Springs (onsen_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: tiered diorama stage seen from one beauty camera.
# A mountain hot-spring village at golden hour, ~132 x 100 walkable, mirrored about x = 0, stacked in tiers that climb
# AWAY from the camera (front = +Z): front bank (y 1.6) > stream (water 0) > Bath Terrace (y 4.5, two steaming pools
# under teal pavilions) > Market Terrace (y 11, shops, noodle stall, koi pond) > Upper Terrace (y 19, inns + the
# five-tier pagoda on the axis). Footbridge over the stream, centre flight T1 -> T2, side flights T2 -> T3.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import onsen_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
FXC = bpy.data.collections.new('PreviewFX'); SC.collection.children.link(FXC)       # steam volumes: preview only
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ------------------------------------------------------------------ layout constants
WATER = 0.0; BED = -2.5; BANK = 1.6
TERR = [   # name, x half, z back, z front, top
    ('T1', 66.0, 14.0, 36.0, 4.5),
    ('T2', 66.0, -12.0, 14.0, 11.0),
    ('T3', 68.0, -50.0, -12.0, 19.0),
]
LAWN_Z = -44.0                       # T3 is paved from z -44 forward; behind it a sage lawn strip for the tree line
STREAM = (36.0, 53.0)
ISLET = (59.0, 57.0, 6.6)              # centre z, half x, half z: the low hot-spring islet the bridge lands on
PAGODA = (0.0, -30.0)

def terrace_at(x, z):
    for name, hx, zb, zf, top in TERR:
        if zb <= z < zf and abs(x) <= hx: return name, top
    return None, None

def mountains(x, z, base):
    ax = abs(x)
    dx = ax - 64.0
    side = 0.0
    if dx > 0:
        fade = 1 - smooth((z - 30) / 70)
        side = (9 * smooth(dx / 4) + 52 * smooth((dx - 3) / 48) + 16 * (nz(x, 0, z, 26, 3) - .5) * smooth(dx / 14)) * fade
    dz = -50.0 - z
    back = 0.0
    if dz > 0:
        notch = 1 - .45 * smooth(1 - ax / 60)                                  # saddle behind the pagoda: peaks show through
        back = (7 * smooth(dz / 3) + 58 * notch * smooth((dz - 2) / 75) + 14 * (nz(x, 0, z, 30, 5) - .5) * smooth(dz / 12))
        back += 30 * smooth((dz - 90) / 80) * notch - 40 * smooth((dz - 170) / 90)
    return max(side, back)

def H(x, z):
    """one height function for ground mesh AND placement (terrace tops are flat; risers are covered by ashlar walls)"""
    t, top = terrace_at(x, z)
    if t:
        y = top
        if t == 'T3' and z < LAWN_Z: y = top + .15 * smooth((LAWN_Z - z) / 6)
        return y + mountains(x, z, top)
    if z < STREAM[0]:
        base = 19.0 if z < -12 else 11.0 if z < 14 else 4.5
    else:                                                                      # stream + the islet + the wide pool in front
        e = ((abs(x) / ISLET[1]) ** 4 + ((z - ISLET[0]) / ISLET[2]) ** 4) ** .25
        base = lerp(BED - .6 * smooth((z - 70) / 30), BANK + (nz(x, 0, z, 9, 2) - .5) * .3, smooth((1.16 - e) / .2))
        base += 6 * smooth((z - 220) / 40) + 6 * smooth((abs(x) - 100) / 15)   # far + side banks hold the front pool's water
    return base + mountains(x, z, base)

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []
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
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    """auto-grounded props (y None) are fitted against everything built so far (see fit); returns y or None"""
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
    name = re.sub(r'_Glow_.*', '', obs[0].data.name)
    soft = any(SOFT_RE.search(ob.data.name) for ob in obs); water = bool(WATER_RE.search(name))
    if auto and not ROCK_RE.search(name) and not water:
        r = fit(obs, Mr, x, y, z, y_at, soft, name)
        if r is None:
            print('FIT_REJECT', key, round(x), round(z))
            for ob in obs: bpy.data.objects.remove(ob)
            return None
        x, y, z = r
    if not soft: add_owner(obs, water)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    return y
def mirror(key, fn, x, z, yaw=0.0, **k):
    """the village is mirrored about x = 0: west copy as written, east copy at -x with the yaw flipped"""
    place(key, fn, x, z, yaw, **k); place(key, fn, -x, z, -yaw, **k)
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    add_owner([ob], bool(WATER_RE.search(name)))

# ---- placement fit: the exporter's hard checks (roblox_export.py 6c) run while placing. Statics + every placed hard
# prop are owners; an auto-grounded prop (y None) is raised in 0.25 steps (its base stays bedded) or nudged until
# no more than 3.5% of its body (7% for foliage) is inside one owner and it does not float; None = nowhere fits
from mathutils.bvhtree import BVHTree
import re
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant|cedar')   # = the export's --soft for this map (cedars are trees)
ROCK_RE = re.compile(r'(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag')
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

# ------------------------------------------------------------------ ground, mountains, water, horizon
def ground():
    """stage ground (smooth: banks, stream bed, lawn) + mountains (flat faceted rock with jittered vertices) from one
    non-uniform grid; faces completely under a paved terrace are skipped"""
    xs = [x for x in range(-330, -92, 8)] + [x * 2.0 for x in range(-46, 47)] + [x for x in range(100, 331, 8)]
    zs = [z for z in range(-420, -62, 8)] + [z * 2.0 for z in range(-31, 71)] + [z for z in range(148, 285, 8)]   # ground under the whole front pool
    def jit(x, z):
        k = smooth((abs(x) - 70) / 10) if abs(x) > 70 else 0.0
        k = max(k, smooth((-56 - z) / 10) if z < -56 else 0.0)
        return (x + (nz(x, 3, z, 7, 1) - .5) * 4 * k, z + (nz(x, 7, z, 7, 2) - .5) * 4 * k)
    bS, bM = bmesh.new(), bmesh.new()
    VS, VM = {}, {}
    def vert(bm, VV, i, j):
        if (i, j) not in VV:
            x, z = xs[i], zs[j]; jx, jz = jit(x, z)
            VV[(i, j)] = bm.verts.new((jx, H(x, z), jz))
        return VV[(i, j)]
    def paved(x, z):
        t, _ = terrace_at(x, z)
        return t is not None and not (t == 'T3' and z < LAWN_Z - 1) and abs(x) < 64
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            x0, x1, z0, z1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            if all(paved(x, z) for x in (x0, x1) for z in (z0, z1)): continue
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            rock = abs(cx) > 66 or cz < -51 or mountains(cx, cz, 0) > 2.5
            bm, VV = (bM, VM) if rock else (bS, VS)
            q = [vert(bm, VV, i, j), vert(bm, VV, i, j + 1), vert(bm, VV, i + 1, j + 1), vert(bm, VV, i + 1, j)]
            f = bm.faces.new(q); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    def shade_stage(f):
        c = f.calc_center_median(); out = []
        if c.y < WATER - .3:
            u = FP.PAL.u('stone')
            return [(u, clamp(.32 + (nz(l.vert.co.x, 0, l.vert.co.z, 3, 5) - .5) * .12, .04, .96)) for l in f.loops]
        u = FP.PAL.u('grass')
        for l in f.loops:
            p = l.vert.co
            v = .5 + (nz(p.x, 0, p.z, 22, 3) - .5) * .12 + (nz(p.x, 0, p.z, 6, 4) - .5) * .05
            v -= .12 * (1 - smooth((p.y - WATER) / 2.5))
            out.append((u, clamp(v, .04, .96)))
        return out
    rng = random.Random(4)
    def shade_rock(f):
        c = f.calc_center_median(); n = f.normal
        if n.y > .82 and nz(c.x, 0, c.z, 14, 6) > .38:
            return [(FP.PAL.u('grass'), clamp(.38 + n.y * .12 + rng.uniform(-.04, .04), .04, .96))] * len(f.loops)
        v = .42 + .16 * n.y + (nz(0, c.y, 0, 9, 7) - .5) * .16 + rng.uniform(-.04, .04)                 # strata bands
        return [(FP.PAL.u('rock'), clamp(v, .04, .96))] * len(f.loops)
    mb = MB(); mb.add(bS, shade_stage, smooth=True); static('Ground_Stage', mb, 'Ground')
    mb = MB(); mb.add(bM, shade_rock, smooth=False); static('Cliff_Mountains', mb, 'Mountains')

def horizon():
    """distant peaks far behind the saddle (pale violet with snow caps) + low ridges at the sides"""
    bm = bmesh.new(); NX, NZ = 40, 12
    def hp(x, z):
        y = 40 + 150 * nz(x, 0, z, 260, 11) + 120 * nz(x, 0, z, 110, 12) * smooth((-z - 520) / 300)
        return y - 60 * smooth((abs(x) - 900) / 300)
    V = [[bm.verts.new((-1400 + i * 70, hp(-1400 + i * 70, -440 - j * 90), -440 - j * 90)) for j in range(NZ)] for i in range(NX + 1)]
    for i in range(NX):
        for j in range(NZ - 1):
            f = bm.faces.new((V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    rng = random.Random(9)
    def sh(f):
        c = f.calc_center_median()
        if c.y > 175 + rng.uniform(-15, 15) and f.normal.y > .3: return [(FP.PAL.u('cream'), clamp(.8 + f.normal.y * .1, 0, .96))] * len(f.loops)
        return [(FP.PAL.u('rock'), clamp(.55 + f.normal.y * .15 + rng.uniform(-.03, .03), .04, .96))] * len(f.loops)
    mb = MB(); mb.add(bm, sh, smooth=False); static('Horizon_Peaks', mb, 'Horizon')

def water():
    """stream + front pool surface: 4-stud cells kept only where the ground dips below the water and no corner is
    buried more than 5.7 under the bank, so every point has a bed under it and the edges run under the banks"""
    bm = bmesh.new(); VV = {}
    xs = [-120 + 4 * i for i in range(61)]; zs = [STREAM[0] - .3] + [36 + 4 * j for j in range(1, 54)]
    def v(i, j):
        if (i, j) not in VV: VV[i, j] = bm.verts.new((xs[i], WATER, zs[j]))
        return VV[i, j]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            hs = [H(xs[a], zs[b]) for a in (i, i + 1) for b in (j, j + 1)]
            if min(hs) >= WATER - .05 or max(hs) > WATER + 5.7: continue
            f = bm.faces.new((v(i, j), v(i, j + 1), v(i + 1, j + 1), v(i + 1, j))); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    mb = MB(); u = FP.PAL.u('water')
    mb.add(bm, lambda f: [(u, .44 + (nz(*f.calc_center_median(), 12, 3) - .5) * .12)] * len(f.loops))
    static('River_Water', mb, 'Stream')

# ------------------------------------------------------------------ terraces: paved tops, ashlar risers, coping
def terraces():
    """each terrace = running-bond flagstone top (inset stones, cream) + ashlar riser on its front face down to the next
    level + a chamfered coping course along the lip + ashlar end faces where it meets the rock"""
    rng = random.Random(3)
    for name, hx, zb, zf, top in TERR:
        mb = MB()
        z0 = LAWN_Z if name == 'T3' else zb
        bm = bmesh.new(); s = 3.2; row = 0; z = z0
        while z < zf - .9:
            z1 = min(z + 2.4, zf - .9); x = -hx - rng.uniform(0, s)
            while x < hx:
                ln = s * rng.uniform(.7, 1.3); xa, xb = max(x, -hx), min(x + ln, hx); x += ln
                if xb - xa < .4: continue
                bm.faces.new([bm.verts.new(p) for p in ((xa, top, z), (xa, top, z1), (xb, top, z1), (xb, top, z))])
            z = z1; row += 1
        fs = list(bm.faces)
        for f in fs: f.normal_update(); (f.normal_flip() if f.normal.y < 0 else None)
        bmesh.ops.inset_individual(bm, faces=fs, thickness=.08, depth=.06, use_even_offset=True)
        bm.normal_update()
        for f in bm.faces: f.material_index = 1 if f.normal.y > .99 else 0
        u = FP.PAL.u('cream')
        mb.add(bm, lambda f: [(u, clamp((.6 + (FP.h01(*[round(c, 1) for c in f.calc_center_median()]) - .5) * .1) if f.material_index else .38, .04, .96))] * len(f.loops))
        lo = {'T1': BED - 1.0, 'T2': 4.5 - .5, 'T3': 11.0 - .5}[name]
        hh = top - .35 - lo
        w = FP.ashlar(2 * hx, hh, 3.0, 1.45, seed=len(name) * 7 + int(top), depth=.1, ins=.08)       # front riser
        mb.add(FP.T(w, (0, lo, zf)), FP.ash_sh('stone', base=.6, var=.07, grime=.1 if name != 'T1' else .2))
        bk = box((2 * hx, hh, 1.0)); mb.add(FP.T(bk, (0, lo + hh / 2, zf - .55)), FP.S('stone', base=.4, jit=.01))
        for sx in (-1, 1):                                                       # end faces against the rock
            e = FP.ashlar(zf - zb, hh + (top - lo - hh), 3.0, 1.45, seed=int(top) + sx, depth=.1, ins=.08)
            mb.add(FP.T(e, (sx * hx, lo, (zf + zb) / 2), -90 * sx), FP.ash_sh('stone', base=.55, var=.06, grime=.15))
        gaps = {'T1': [(-5.5, 5.5)], 'T2': [(-6.5, 6.5)], 'T3': [(-43.0, -33.0), (33.0, 43.0)]}[name]
        for k in range(-6, 7):                                                    # pilasters every 11 studs on the riser
            px = k * 11.0 + 5.5
            if abs(px) > hx - 3 or any(a - 1.5 < px < b + 1.5 for a, b in gaps): continue
            mb.add(FP.T(box((2.2, hh, .9), .06), (px, lo + hh / 2, zf + .45)), FP.S('stone', base=.52, up=.05, jit=.02))
            mb.add(FP.T(box((2.8, .55, 1.4), .12), (px, top - .9, zf + .55)), FP.S('stone', base=.66, up=.12, jit=.02))
            mb.add(FP.T(box((2.7, 1.0, 1.3), .1), (px, lo + .5, zf + .5)), FP.S('stone', base=.46, up=.1, jit=.02))
        x = -hx
        while x < hx - .5:                                                        # coping course
            ln = min(rng.uniform(2.6, 3.4), hx - x)
            mb.add(FP.T(box((ln - .08, .4, 1.5), .12), (x + ln / 2, top - .15, zf - .55)), FP.S('stone', base=.7 + rng.uniform(-.04, .04), up=.12, jit=.01))
            x += ln
        static('Hardscape_%s' % name, mb, 'Terraces')

def bank_path():
    """flagstone path on the front bank from the bridge foot toward the camera, ragged edges"""
    rng = random.Random(8); mb = MB(); bm = bmesh.new(); z = 54.5
    while z < 96:
        w = 5.2 + rng.uniform(-.4, .4); n = 2 if rng.random() < .6 else 3; x = -w / 2
        for k in range(n):
            ln = w / n; zz = z + rng.uniform(-.1, .1)
            y = H(x + ln / 2, zz + 1) + .08
            bm.faces.new([bm.verts.new(p) for p in ((x + .06, y, zz), (x + .06, y, zz + 1.9), (x + ln - .06, y, zz + 1.9), (x + ln - .06, y, zz))])
            x += ln
        z += 2.05
    fs = list(bm.faces)
    for f in fs: f.normal_update(); (f.normal_flip() if f.normal.y < 0 else None)
    bmesh.ops.inset_individual(bm, faces=fs, thickness=.1, depth=-.18, use_even_offset=True)
    bm.normal_update(); u = FP.PAL.u('stone')
    mb.add(bm, lambda f: [(u, clamp(.6 + f.normal.y * .08 + (FP.h01(*f.calc_center_median()) - .5) * .12, .04, .96))] * len(f.loops))
    static('Path_Bank', mb, 'Ground')

# ------------------------------------------------------------------ the village
RAIL = 6.0
def rail_run(z, x0, x1, top, gaps, group, yaw=0.0):
    """SIGNATURE: railing bays along a terrace lip with gaps at stairs / bridge; stone lanterns at every gap"""
    x = x0; last = None
    while x + RAIL <= x1 + .01:
        xc = x + RAIL / 2
        if not any(a - RAIL / 2 < xc < b + RAIL / 2 for a, b in gaps):
            place('rail6', lambda: FP.railing(RAIL), xc, z, yaw, y=top, group=group); last = xc
        elif last is not None:                                                    # bays carry their left post only:
            place('railpost', FP.railing_post, last + RAIL / 2, z, yaw, y=top, group=group); last = None   # close the run
        x += RAIL
    if last is not None: place('railpost', FP.railing_post, last + RAIL / 2, z, yaw, y=top, group=group)

def village():
    T1, T2, T3 = 4.5, 11.0, 19.0
    # stream crossing + bank
    place('bridge', FP.footbridge, 0, 45.0, 0, y=0.0, group='Bridge')            # low end (bank) at +Z
    reserve(0, 45, 6)
    # ---------------- T1 bath terrace
    for sg in (-1, 1):
        x = sg * 30
        place('hotpool_%d' % (1 if sg < 0 else 2), (lambda s=sg: FP.hot_pool(8.0, 5.4, 1 if s < 0 else 2)), x, 24.5, 180 if sg < 0 else 0, y=T1, group='BathTerrace')
        place('pavilion', lambda: FP.bath_pavilion(19.0, 14.0, 6.6), x, 24.5, 0, y=T1, group='BathTerrace')
        reserve(x, 24.5, 11)
    rail_run(35.0, -63, 63, T1, [(-4.5, 4.5)], 'Edges_T1')
    place('torii', lambda: FP.torii(9.2, 8.5), 0, 32.6, 0, y=T1, group='Bridge')        # gate at the bridge head, framing the axis
    for sx in (-1, 1):
        place('toro', FP.toro, sx * 7.0, 33.4, 0, y=T1, group='Edges_T1')                 # bridge landing lanterns
        place('lpost', FP.paper_lantern_post, sx * 4.2, 55.5, 90 * sx, group='Bridge')
        place('toro', FP.toro, sx * 7.4, 27.8, 0, y=T1, group='Edges_T1')                 # centre flight foot lanterns
        place('planter4', lambda: FP.planter(4.0), sx * 52.0, 16.2, 0, y=T1, group='Edges_T1')
        place('planter4', lambda: FP.planter(4.0), sx * 15.5, 16.2, 0, y=T1, group='Edges_T1')
    # ---------------- centre flight T1 -> T2
    place('stair_c', lambda: FP.stair_flight(6.5, 12.0, 8.0, 1), 0, 20.0, 0, y=T1, group='Stairs')
    reserve(0, 20, 7)
    # ---------------- T2 market terrace
    rail_run(13.0, -63, 63, T2, [(-6.5, 6.5)], 'Edges_T2')
    for sx in (-1, 1):
        place('toro', FP.toro, sx * 7.4, 11.6, 0, y=T2, group='Edges_T2')
    mirror('shop', lambda: FP.house('ShopD', 13.0, 9.0, 2, 6.0, 'roofD', 'shop', 4), -52.0, 1.0, 180, y=T2, group='Market')
    for x in (-52, 52): reserve(x, 1, 10)
    place('koi', lambda: FP.koi_pond(1, 3.6), 0, -1.5, 0, y=T2, group='Market')
    mirror('bench', FP.bench, -8.5, -1.5, 90, y=T2, group='Market')
    mirror('lpostm', lambda: FP.paper_lantern_post(2, 5.6), -27.0, 9.5, 180, y=T2, group='Market')
    for x in (-62.0, 62.0):
        place('planter3', lambda: FP.planter(3.0, 2), x, -9.8, 90, y=T2, group='Edges_T2')
    # ---------------- side flights T2 -> T3
    for sx in (-1, 1):
        place('stair_s', lambda: FP.stair_flight(8.0, 13.0, 6.0, 2), sx * 38.0, -5.5, 0, y=T2, group='Stairs')
        reserve(sx * 38, -5.5, 6)
    # ---------------- T3 upper terrace
    rail_run(-13.0, -65, 65, T3, [(-41.5, -34.5), (34.5, 41.5)], 'Edges_T3')
    place('pagoda_base', lambda: FP.pagoda('base'), PAGODA[0], PAGODA[1], 180, y=T3, group='Pagoda')
    place('pagoda_top', lambda: FP.pagoda('top'), PAGODA[0], PAGODA[1], 180, y=T3, group='Pagoda')
    reserve(*PAGODA, 12)
    mirror('toro', FP.toro, -6.8, -18.3, 0, y=T3, group='Pagoda')
    mirror('inn', lambda: FP.house('InnB', 14.0, 10.0, 2, 6.5, 'roofB', 'inn', 2), -24.5, -31.0, 180, y=T3, group='Upper')
    mirror('tall', lambda: FP.house('TallC', 12.0, 10.0, 3, 6.0, 'roofC', 'inn', 3, rise=6.2), -51.5, -33.0, 180, y=T3, group='Upper')
    for x in (-24.5, 24.5, -51.5, 51.5): reserve(x, -32, 10)
    for sx in (-1, 1):
        place('toro', FP.toro, sx * 33.5, -15.2, 0, y=T3, group='Edges_T3')
        place('toro', FP.toro, sx * 42.5, -15.2, 0, y=T3, group='Edges_T3')
        place('planter4', lambda: FP.planter(4.0, 3), sx * 13.5, -19.5, 0, y=T3, group='Upper')

def stories():
    """clusters of 2-4 at the stairs and bridge; deliberately NOT mirrored (props break the symmetry)"""
    T1, T2, T3 = 4.5, 11.0, 19.0
    G = 'Stories'
    # bridge landing on T1: towels + buckets (west), crates (east)
    place('towels1', lambda: FP.towel_rack(1), -11.5, 29.0, 160, y=T1, group=G)
    place('bench', FP.bench, -14.0, 32.0, 0, y=T1, group=G)
    place('crates1', lambda: FP.crates(1), 12.5, 30.5, -20, y=T1, group=G)
    place('cart', lambda: FP.hand_cart(1), 16.5, 25.0, 200, y=T1, group=G)
    # pools: a bench and towels by each pool (different sides)
    place('bench', FP.bench, -44.5, 31.0, 90, y=T1, group=G)
    place('towels2', lambda: FP.towel_rack(2), 45.5, 18.5, 10, y=T1, group=G)
    # market: noodle stall at the stair top (west), sake casks + crates (east)
    place('noodle', FP.noodle_stall, -17.0, 3.0, 200, y=T2, group=G)
    place('sake1', lambda: FP.sake_barrels(1), 18.0, 5.5, -160, y=T2, group=G)
    place('crates2', lambda: FP.crates(2), 22.5, -5.0, 30, y=T2, group=G)
    place('cart', lambda: FP.hand_cart(1), -31.0, -6.0, 120, y=T2, group=G)
    place('crates2', lambda: FP.crates(2), -61.5, 9.6, 200, y=T2, group=G)
    # upper terrace: towels by the west stair top, a bench + crates by the east one
    place('towels1', lambda: FP.towel_rack(1), -29.0, -19.0, 190, y=T3, group=G)
    place('bench', FP.bench, 29.0, -18.0, 0, y=T3, group=G)
    place('crates1', lambda: FP.crates(1), 46.5, -20.5, 160, y=T3, group=G)
    # front bank: two natural rock pools by the stream, stepping stones, a fisherman's cart
    place('rockpool1', lambda: FP.hot_pool(4.6, 3.4, 3, False), -34.0, 59.5, 20, y=BANK - .2, group='Bank')
    place('rockpool2', lambda: FP.hot_pool(4.0, 3.0, 4, False), 38.0, 59.5, -30, y=BANK - .2, group='Bank')
    place('stones', lambda: FP.stepping_stones(1, 7, 13.0), -50.0, 44.5, 8, y=WATER - .4, group='Stream')
    place('stones2', lambda: FP.stepping_stones(2, 6, 11.0), 26.0, 44.5, -12, y=WATER - .4, group='Stream')
    for x, z in ((-34, 59.5), (38, 59.5), (-50, 44.5), (26, 44.5)): reserve(x, z, 6)

TREES = {
    'pine1': (lambda: FP.jp_pine(1, 16.0), 6), 'pine2': (lambda: FP.jp_pine(2, 13.0), 5), 'pine3': (lambda: FP.jp_pine(3, 19.0), 7),
    'cloud1': (lambda: FP.cloud_tree(1, 13.0), 5), 'cloud2': (lambda: FP.cloud_tree(3, 11.0), 4),
    'cedar1': (lambda: FP.cedar(1, 26.0), 5), 'cedar2': (lambda: FP.cedar(2, 32.0), 6), 'cedar3': (lambda: FP.cedar(3, 22.0), 4),
}
def nature(rng):
    G = 'Nature'
    # tree line behind the upper houses (T3 lawn strip + lower mountain slopes): cedars + cloud trees + pines
    for x in [-62 + k * 7.4 for k in range(18)]:
        if abs(x) < 9: continue
        z = rng.uniform(-49, -45); key = rng.choice(('cedar1', 'cedar2', 'cedar3', 'cloud1', 'cloud2', 'pine1'))
        place(key, TREES[key][0], x + rng.uniform(-1.5, 1.5), z, rng.uniform(0, 360), s=rng.uniform(.85, 1.15), group=G)
    for k in range(70):                                                          # cedars climbing the back + side slopes
        for _t in range(30):
            x = rng.uniform(-150, 150); z = rng.uniform(-150, 30)
            y = H(x, z); m = mountains(x, z, 0)
            if m < 6 or m > 60 or abs(x) < 64 and z > -54: continue
            if abs(x) < 26 and z > -110: continue                               # keep the saddle clear behind the pagoda
            key = rng.choice(('cedar1', 'cedar2', 'cedar3', 'cedar1', 'pine3'))
            place(key, TREES[key][0], x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.25), group=G); break
    # garden trees on the terraces (pruned pines + cloud trees), not mirrored exactly
    for x, z, key, y in ((-37.0, -24.0, 'pine2', 19.0), (35.5, -26.0, 'cloud2', 19.0), (-60.0, -22.0, 'cloud1', 19.0),
                         (61.0, -24.0, 'pine1', 19.0), (-60.0, 2.0, 'pine2', 11.0), (60.0, 6.0, 'cloud2', 11.0),
                         (-55.0, 19.0, 'pine1', 4.5), (12.0, 18.5, 'cloud2', 4.5)):
        place(key, TREES[key][0], x, z, rng.uniform(0, 360), y=y, group=G); reserve(x, z, 3)
    # the accent: three autumn maples only (bank by the bridge, upper terrace west, on the east cliff ledge)
    place('maple1', lambda: FP.cloud_tree(2, 12.0, 'maple'), 16.0, 58.0, 30, group='Accent')
    place('maple2', lambda: FP.cloud_tree(4, 10.5, 'maple'), -40.5, -44.0, 200, group='Accent')
    place('maple1', lambda: FP.cloud_tree(2, 12.0, 'maple'), 74.0, 6.0, 110, group='Accent')
    for x, z in ((16, 58), (-40.5, -44), (74, 6)): reserve(x, z, 4)
    # framing crags: front corners in the stream + flanks
    for x, z, h, r, sd in ((-71, 46, 34, 9, 1), (72, 49, 30, 8, 2), (-80, 18, 44, 10, 3), (82, 22, 40, 10, 4), (-68, 70, 18, 6, 5), (70, 76, 15, 5, 6), (-62, 128, 26, 8, 7), (60, 134, 22, 7, 8)):
        place('crag%d' % sd, lambda h=h, r=r, sd=sd: FP.crag(sd, h, r), x, z, rng.uniform(0, 360), group='Rocks')
    # boulders + ferns + shrubs along the stream banks and terrace feet (clusters, not even)
    for cx, cz, n in ((-52, 58, 4), (-20, 55, 3), (22, 55, 3), (52, 57, 4), (-9, 64, 3), (28, 64, 3), (-44, 64, 2), (8, 64, 2)):
        for k in range(n):
            x = cx + rng.uniform(-4, 4); z = cz + rng.uniform(-2.5, 2.5)
            if not free(x, z, 1.5) or abs(x) < 4.5: continue
            r = rng.choice(('b1', 'b2', 'shrub', 'tuft', 'tuft'))
            if r in ('shrub', 'tuft') and H(x, z) < BANK - .4: continue                # foliage only on the dry bank, never on the slope into the stream
            reserve(x, z, 2.4 if r in ('b1', 'b2') else 1.4)                         # nothing else grows inside this rock / shrub
            if r == 'b1': place('boulder1', lambda: FP.boulder(1, 2.2), x, z, rng.uniform(0, 360), s=rng.uniform(.6, 1.2), group='Rocks')
            elif r == 'b2': place('boulder2', lambda: FP.boulder(2, 1.6, False), x, z, rng.uniform(0, 360), s=rng.uniform(.7, 1.3), group='Rocks')
            elif r == 'shrub': place('shrub1', lambda: FP.shrub(1, 1.5), x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.2), group='Nature')
            else: place('tuft1', lambda: FP.fern_tuft(1), x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.4), group='Nature')
    for x, z, r, sd in ((-36, 96, 3.4, 1), (-42, 108, 2.6, 2), (40, 100, 3.0, 1), (46, 116, 3.6, 2), (-24, 78, 1.8, 2), (27, 80, 2.0, 1)):   # foreground rocks in the pool
        place('boulder%d' % sd, lambda sd=sd: FP.boulder(sd, 2.2 if sd == 1 else 1.6, sd == 1), x, z, rng.uniform(0, 360), s=r / 1.8, group='Rocks')
    for k in range(10):                                                          # boulders at the T1 riser foot in the water
        x = rng.uniform(-62, 62)
        if abs(x) < 6 or not free(x, 37.5, 2): continue
        place('boulder2', lambda: FP.boulder(2, 1.6, False), x, 37.4 + rng.uniform(0, 1.2), rng.uniform(0, 360), y=BED + .6, s=rng.uniform(.8, 1.4), group='Rocks')

STEAM = []
def steam():
    """preview-only steam volumes over the hot water (Roblox: ParticleEmitters at these points, see SETUP.md)"""
    for x, z, y, r, hh in ((-30, 24.5, 5.4, 6.0, 9), (30, 24.5, 5.4, 6.0, 9), (-34, 59.5, 2.2, 3.6, 6), (38, 59.5, 2.2, 3.2, 6), (-17 + 1.3, 3.0 - .4, 15.2, .8, 3.2)):
        STEAM.append({'pos': [x, y, z], 'radius': r, 'height': hh})
        me = bpy.data.meshes.new('Steam'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new('Steam', me); ob.location = r2b((x, y + hh * .45, z)); ob.scale = (r, r, hh * .55); FXC.objects.link(ob)
        m = bpy.data.materials.get('SteamMat')
        if not m:
            m = bpy.data.materials.new('SteamMat'); m.use_nodes = True; nt = m.node_tree
            nt.nodes.remove(nt.nodes['Principled BSDF'])
            pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (1, .95, .92, 1)
            tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 2.2
            gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
            mp = nt.nodes.new('ShaderNodeMath'); mp.operation = 'MULTIPLY'
            mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .38; mr.inputs['To Max'].default_value = 4.5
            nt.links.new(tc.outputs['Object'], ns.inputs['Vector']); nt.links.new(tc.outputs['Object'], gr.inputs['Vector'])
            nt.links.new(ns.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mp.inputs[0]); nt.links.new(gr.outputs['Fac'], mp.inputs[1])
            nt.links.new(mp.outputs[0], pv.inputs['Density']); nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume'])
        me.materials.append(m); ob.visible_shadow = False

def build():
    ground(); horizon(); water(); terraces()
    for loc, _t, _l in SHOTS.values(): reserve(loc[0], loc[2], 4)
    village(); stories(); nature(random.Random(21)); steam()

# ------------------------------------------------------------------ look: golden hour in the mountains
def look():
    w = bpy.data.worlds.new('Golden'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (1.0, .64, .42, 1)          # peach horizon
    cr.elements[1].position = .62; cr.elements[1].color = (.32, .36, .72, 1)          # violet-blue zenith
    e = cr.elements.new(.1); e.color = (1.0, .58, .58, 1)                               # pink band
    e = cr.elements.new(.3); e.color = (.72, .52, .78, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .85
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .1; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 5.2; sun.data.color = (1.0, .68, .42); sun.data.angle = math.radians(2.0)
    el = math.radians(17); az = math.radians(238)                                     # low, from the south-west
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .8; fill.data.color = (.55, .55, .95); fill.data.use_shadow = False
    to_f = r2b((.3, .85, -.4)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 64
    except Exception: pass
    for k, v in (('volumetric_tile_size', '4'), ('volumetric_end', 1500.0), ('volumetric_start', .5), ('volumetric_distribution', .92), ('volumetric_samples', 96)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (2800, 2400, 500); hz.location = (0, 0, 200); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .0004
    pv.inputs['Color'].default_value = (1.0, .78, .78, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False
    for x, y, z in LAMPS:                                                         # a few warm lamp lights (small, no shadow)
        L = bpy.data.objects.new('Lamp', bpy.data.lights.new('Lamp', 'POINT')); L.data.energy = 60; L.data.color = (1, .7, .4)
        L.data.shadow_soft_size = .4; L.data.use_shadow = False; L.location = r2b((x, y, z)); SC.collection.objects.link(L)

LAMPS = [(sx * 7.0, 8.0, 33.4) for sx in (-1, 1)] + [(sx * 7.4, 8.0, 27.8) for sx in (-1, 1)] + [(sx * 7.4, 14.5, 11.6) for sx in (-1, 1)] + [(sx * 2.9, 6.0, 55.5) for sx in (-1, 1)] + \
        [(sx * 3.4, 26.6, -23.1) for sx in (-1, 1)] + [(-17.0, 21.0, 3.0)]

MATERIALS = {'cream': 'Limestone', 'stone': 'Sandstone', 'rock': 'Rock', 'wood': 'Wood', 'woodlt': 'WoodPlanks',
             'leaf': 'LeafyGrass', 'pine': 'LeafyGrass', 'grass': 'Grass', 'water': 'Glass', 'roofA': 'SmoothPlastic',
             'roofB': 'SmoothPlastic', 'roofC': 'SmoothPlastic', 'roofD': 'SmoothPlastic', 'maple': 'LeafyGrass', 'iron': 'Metal'}
MAT_OVERRIDES = {'Horizon_Peaks': 'SmoothPlastic', 'Hardscape_T1': 'Limestone', 'Hardscape_T2': 'Limestone', 'Hardscape_T3': 'Limestone'}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Limestone'] = ('noise', 7.0, .12, .9, 0, .1)
    RM.LOOK['Sandstone'] = ('noise', 9.0, .16, .9, 0, .1)
    RM.LOOK['Glass'] = ('noise', 30.0, .02, .6, 0, .04)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SPAWN = (0.0, BANK, 60.0)
SHOTS = {   # vertical FOV (Roblox-style)
    'map_beauty.png': ((0, 9, 160), (0, 24, -18), 35),
    'map_overview.png': ((-110, 105, 160), (0, 12, -6), 38),
    'map_top.png': ((0, 330, 11), (0, 0, 10), 34),
    'map_spawn.png': ((SPAWN[0], SPAWN[1] + 5.5, SPAWN[2] + 4), (0, 18, 0), 60),
    'map_bath.png': ((-12, 10, 44), (-32, 7, 22), 50),
    'map_market.png': ((10, 15, 22), (-8, 13, -4), 55),
    'map_pagoda.png': ((14, 23, 2), (0, 36, -30), 60),
    'map_upper.png': ((40, 23, -2), (24, 24, -32), 55),
    'map_bridge.png': ((-24, 5, 66), (0, 4, 40), 45),
    'map_stair.png': ((-24, 16, 8), (-38, 18, -12), 55),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'steam': STEAM, 'spawn': SPAWN, 'lamps': LAMPS}, open(os.path.join(HERE, 'fx_points.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'onsen_map.blend'))
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
