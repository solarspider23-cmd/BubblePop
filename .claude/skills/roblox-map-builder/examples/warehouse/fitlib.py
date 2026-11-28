import random, re, bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from pro_lib import r2b
WATER_RE = re.compile(r"(?i)water|lake|river|stream|pond|pool|falls|moat")
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
