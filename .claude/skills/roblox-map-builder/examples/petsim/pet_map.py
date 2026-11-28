# blender -b --factory-startup --python pet_map.py [-- norender] [-- name.png ...] -> Puffpaw Isles (pet_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Pet-collecting sim map: an ISLAND CHAIN in a turquoise lagoon.
# Round "layer-cake" islands (grass top, cream icing lip with drips, sponge cliff with a jam stripe) linked by chunky
# bridges, each bridge behind a toll gate. The chain curls clockwise round the hub's north + east and climbs:
# hub y 5 > Meadow y 7 > Candy y 12 > Crystal y 18. Clouds on the water frame the whole chain.
import sys, os, math, random, json, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import pet_props as PP
F = PP.G
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
U = PP.PAL.u
V3 = Vector

# ------------------------------------------------------------------ islands
SEA_Y = -6.0
ISLES = [   # name, centre, base radius, top y, dome, ground col, sponge col, jam col, icing col, path col, seed
    dict(name='Hub',     c=(0.0, 0.0),      R=92.0,  top=5.0,  dome=.6,  ground='grass', sponge='wood',  jam='pink', icing='cream', path='cream', seed=1),
    dict(name='Meadow',  c=(8.0, -238.0),   R=86.0,  top=7.0,  dome=1.4, ground='grass', sponge='wood',  jam='red',  icing='cream', path='cream', seed=2),
    dict(name='Candy',   c=(210.0, -172.0), R=82.0,  top=12.0, dome=1.4, ground='mint',  sponge='pink',  jam='cream', icing='cloud', path='pink', seed=3),
    dict(name='Crystal', c=(222.0, 72.0),   R=82.0,  top=18.0, dome=1.4, ground='lilac', sponge='sky', jam='pink',  icing='cloud', path='cloud', seed=4),
]
def isle_R(I, a):
    s = I['seed']
    return I['R'] * (1 + .045 * math.sin(3 * a + s) + .03 * math.sin(5 * a + 2 * s) + .015 * math.sin(9 * a + s))
def polar(I, x, z):
    cx, cz = I['c']; dx, dz = x - cx, z - cz
    a = math.atan2(dz, dx); return math.hypot(dx, dz), a
def isle_at(x, z):
    for I in ISLES:
        r, a = polar(I, x, z)
        if r <= isle_R(I, a): return I
    return None
def top_y(I, x, z):
    r, a = polar(I, x, z); t = clamp(r / isle_R(I, a))
    return I['top'] + I['dome'] * (1 - t * t)
def H(x, z):
    I = isle_at(x, z)
    return top_y(I, x, z) if I else SEA_Y - 10

LIP = [(.9, -.18), (1.7, -.65), (2.25, -1.45), (2.5, -2.5), (2.55, -3.6), (2.6, -4.9), (2.75, -6.4), (3.0, -8.2), (3.4, -10.4),
       (3.9, -13.0), (4.6, -16.0)]
TOP_F = (0, .16, .32, .46, .58, .68, .77, .84, .9, .95, .985, 1.0)

def isle_mesh(I, NS=168):
    """polar top (dome) + rounded icing shoulder + sponge cliff down into the lagoon. Colour per FACE: top = ground,
    shoulder + drips = icing, cliff = sponge with one jam stripe"""
    cx, cz = I['c']; bm = bmesh.new(); rows = []
    for k, f in enumerate(TOP_F):
        if f == 0: rows.append([bm.verts.new((cx, I['top'] + I['dome'], cz))]); continue
        ring = []
        for i in range(NS):
            a = i * math.tau / NS; R = isle_R(I, a) * f
            x, z = cx + math.cos(a) * R, cz + math.sin(a) * R
            ring.append(bm.verts.new((x, top_y(I, x, z), z)))
        rows.append(ring)
    for dr, dy in LIP:
        ring = []
        for i in range(NS):
            a = i * math.tau / NS; R = isle_R(I, a) + dr
            ring.append(bm.verts.new((cx + math.cos(a) * R, I['top'] + dy, cz + math.sin(a) * R)))
        rows.append(ring)
    for A, Bq in zip(rows, rows[1:]):
        for i in range(NS):
            j = (i + 1) % NS
            if len(A) == 1: bm.faces.new((A[0], Bq[j], Bq[i]))
            else: bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < -.2 and f.calc_center_median().y > I['top'] - 1: f.normal_flip()
    for f in bm.faces:                                                  # cliff faces point outward
        c = f.calc_center_median()
        if c.y < I['top'] - .5:
            out = V3((c.x - cx, 0, c.z - cz))
            if f.normal.dot(out) < 0: f.normal_flip()
    s = I['seed']
    def drip(a):
        k = math.sin(a * 11 + s) * .5 + .5; k2 = math.sin(a * 23 + 2 * s) * .5 + .5
        return 1.4 + 2.6 * k ** 3 + 1.2 * k2 ** 6
    def sh(f):
        c = f.calc_center_median(); dy = c.y - I['top']; a = math.atan2(c.z - cz, c.x - cx)
        r = math.hypot(c.x - cx, c.z - cz); edge = isle_R(I, a)
        if r < edge - .05:
            col = I['ground']
            out = []
            for l in f.loops:
                p = l.vert.co
                v = (.48 if col == 'lilac' else .55) + (nz(p.x, 0, p.z, 30, s) - .5) * .16 + (nz(p.x, 0, p.z, 9, s + 3) - .5) * .06
                out.append((U(col), clamp(v, .05, .95)))
            return out
        if dy > -drip(a):
            v = .72 + .2 * f.normal.y + .06 * f.normal.dot(PP.SUN); col = I['icing']
        elif -9.2 < dy < -7.2:
            v = .55 + .1 * f.normal.dot(PP.SUN); col = I['jam']
        else:
            v = .55 + .12 * f.normal.dot(PP.SUN) + .1 * clamp((dy + 14) / 10); col = I['sponge']
        return [(U(col), clamp(v, .05, .95))] * len(f.loops)
    mb = MB(); mb.add(bm, sh, smooth=True)
    return mb

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; STATIC_TRIS = {}; GROUP_TRIS = {}
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
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant')
DEFER = []; DEFER_ON = [True]; PLACED_OBS = []; REJECT = []
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    meshes = kit(key, fn)
    pname = next(iter(meshes.values())).name
    if DEFER_ON[0] and SOFT_RE.search(pname):
        DEFER.append((key, fn, x, z, yaw, s, y, sink, group)); return
    if y is None:
        fr = foot(key) * s
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    obs = []
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob); obs.append(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]; GROUP_TRIS[group] = GROUP_TRIS.get(group, 0) + LIB[key][1]
    PLACED_OBS.append((obs, key, group))
    return y
def unplace(obs, key, group):
    for ob in obs: bpy.data.objects.remove(ob)
    COUNT[key] -= 1; TRIS[0] -= LIB[key][1]; GROUP_TRIS[group] -= LIB[key][1]
SOLID = [None]
def build_solid():
    bm = bmesh.new()
    for c in SUB.values():
        for ob in c.objects:
            if SOFT_RE.search(ob.data.name): continue
            m = ob.data.copy(); m.transform(ob.matrix_world); bm.from_mesh(m); bpy.data.meshes.remove(m)
    SOLID[0] = BVHTree.FromBMesh(bm); bm.free()
DIRS = [V3(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
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
        lo_z = min(q.z for q in pts); hi_z = max(q.z for q in pts)
        body = [q for q in pts if q.z > lo_z + .15 * (hi_z - lo_z)]
        if body and sum(1 for q in body if inside(q)) / len(body) > .04: return 'inside'
        o = M.translation; lowest = min(q.z for q in pts)
        hit = SOLID[0].ray_cast(V3((o.x, o.y, lowest + 3)), V3((0, 0, -1)), 80)
        if hit[0] is not None and lowest - hit[0].z > .8: return 'floats'
    return None
def place_soft(rng):
    DEFER_ON[0] = False
    for key, fn, x, z, yaw, s, y, sink, group in DEFER:
        ok = False
        for t in range(9):
            jx, jz = (0, 0) if t == 0 else (rng.uniform(-1, 1) * (2 + t * 1.5), rng.uniform(-1, 1) * (2 + t * 1.5))
            if not isle_at(x + jx, z + jz): continue
            place(key, fn, x + jx, z + jz, yaw, s, y, sink, group)
            obs, k, g = PLACED_OBS.pop()
            if clip_fail(obs): unplace(obs, k, g); continue
            ok = True; break
        if not ok: REJECT.append((key, round(x), round(z)))
    DEFER_ON[0] = True

def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))     # yaw so the -Z front looks at (tx, tz)
def local(cx, cz, yaw, lx, lz):
    a = math.radians(yaw); return (cx + lx * math.cos(a) + lz * math.sin(a), cz - lx * math.sin(a) + lz * math.cos(a))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris; return ob

ANCHORS = []
def anchor(name, kind, p, yaw=0.0, size=(4, 1, 4), group=None, attrs=None):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group or kind, 'pos': [round(p[0], 2), round(p[1], 2), round(p[2], 2)],
                    'yaw': round(yaw % 360, 1), 'size': [round(v, 2) for v in size], 'attrs': attrs or {}})

# ------------------------------------------------------------------ paths (draped ribbons with a darker kerb)
PATHS = []           # (isle, [(x, z)...], width)
def catmull(pts, n=6):
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [V3((p[0], 0, p[1])) for p in P[i - 1:i + 3]]
        for k in range(n):
            t = k / n
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(V3((pts[-1][0], 0, pts[-1][1])))
    return [(p.x, p.z) for p in out]
def path(I, pts, w=12.0):
    PATHS.append((I, catmull(pts), w))
def path_d(x, z):
    """distance to the nearest path edge (negative = on a path)"""
    best = 1e9
    for I, pts, w in PATHS:
        for a, b in zip(pts, pts[1:]):
            ax, az = a; bx, bz = b; dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz or 1
            t = clamp(((x - ax) * dx + (z - az) * dz) / L2)
            d = math.hypot(x - ax - dx * t, z - az - dz * t) - w / 2
            if d < best: best = d
    return best
def ribbon_mesh(pts, w, lift, col, v, edge=False):
    bm = bmesh.new(); L = []; Rr = []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        t = V3((b[0] - a[0], 0, b[1] - a[1])).normalized(); n = V3((-t.z, 0, t.x))
        pl = (x + n.x * w / 2, z + n.z * w / 2); pr = (x - n.x * w / 2, z - n.z * w / 2)
        L.append(bm.verts.new((pl[0], H(*pl) + lift, pl[1]))); Rr.append(bm.verts.new((pr[0], H(*pr) + lift, pr[1])))
    for i in range(len(pts) - 1):
        f = bm.faces.new((L[i], Rr[i], Rr[i + 1], L[i + 1])); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co
            out.append((U(col), clamp(v + (nz(p.x, 0, p.z, 14, 7) - .5) * .1, .05, .95)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=False); return mb
def path_meshes():
    mb = MB()
    for I, pts, w in PATHS:
        mb.merge(ribbon_mesh(pts, w + 2.4, .12, I['ground'], .3))                # darker kerb band
        mb.merge(ribbon_mesh(pts, w, .2, I['path'], {'cream': .44, 'cloud': .6}.get(I['path'], .62)))
        for (x, z) in (pts[0], pts[-1]):                                         # round end caps
            pass
    static('Path_All', mb, 'Paths')

def plaza(cx, cz, R, I):
    """polar tile disc: rings of soft tiles alternating cream / pink, inset grout, a sky ring at the edge"""
    bm = bmesh.new(); r = 0.0; ring = 0
    y = lambda x, z: H(x, z) + .3
    while r < R - .1:
        rb = min(r + 4.0, R); n = max(6, round(math.tau * (r + rb) / 2 / 4.6))
        for k in range(n):
            a0 = (k + .5 * (ring % 2)) * math.tau / n; a1 = a0 + math.tau / n
            if r == 0: pts = [(math.cos(a) * rb, math.sin(a) * rb) for a in (a0, (a0 + a1) / 2, a1)] + [(0, 0)]
            else: pts = [(math.cos(a) * rr, math.sin(a) * rr) for rr, a in ((r, a0), (r, a1), (rb, a1), (rb, (a0 + a1) / 2), (rb, a0))]
            f = bm.faces.new([bm.verts.new((cx + x, y(cx + x, cz + z), cz + z)) for x, z in pts]); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        r = rb; ring += 1
    bmesh.ops.inset_individual(bm, faces=list(bm.faces), thickness=.18, depth=.12, use_even_offset=True)
    bm.normal_update()
    def sh(f):
        c = f.calc_center_median(); rr = math.hypot(c.x - cx, c.z - cz)
        if f.normal.y < .95: return [(U('stone'), .55)] * len(f.loops)
        col = 'sky' if rr > R - 4 else ('pink' if int(rr / 4) % 2 else 'cream')
        h = PP.B.h01(round(c.x, 1), 0, round(c.z, 1))
        return [(U(col), clamp((.78 if col != 'sky' else .62) + (h - .5) * .08, .05, .95))] * len(f.loops)
    mb = MB(); mb.add(bm, sh); static('Paving_HubPlaza', mb, 'Paths')

# ------------------------------------------------------------------ build pieces
HUB, Z1, Z2, Z3 = ISLES
SPAWN = (0.0, 5.0, 70.0)
def edge_pt(I, toward, inset):
    cx, cz = I['c']; a = math.atan2(toward[1] - cz, toward[0] - cx); R = isle_R(I, a) - inset
    return (cx + math.cos(a) * R, cz + math.sin(a) * R)

BRIDGES = []   # (n, A, B, start, end)
def link(n, A, B, theme):
    s = edge_pt(A, B['c'], 7.0); e = edge_pt(B, A['c'], 7.0)
    L = math.hypot(e[0] - s[0], e[1] - s[1]); yaw = face(s[0], s[1], e[0], e[1])
    y0 = H(*s); y1 = H(*e)
    place('Bridge_%d' % n, lambda: PP.bridge(n, L, y1 - y0, theme, drop=y0 - SEA_Y + 3.0), s[0], s[1], yaw, 1.0, y0 - .05, group='Bridges')   # piers 3 into the lagoon
    BRIDGES.append((n, A, B, s, e))
    # gate on the near island, 12 studs before the bridge head, front facing back into island A
    gx, gz = edge_pt(A, B['c'], 19.0); gyaw = face(gx, gz, *A['c'])
    gate_theme = ('meadow', 'candy', 'crystal')[n - 1]
    place('ZoneGate_%s' % gate_theme, lambda: PP.zone_gate({'meadow': 'grass', 'candy': 'pink', 'crystal': 'lilac'}[gate_theme], True, gate_theme),
          gx, gz, gyaw, 1.0, group='Gates')
    gy = H(gx, gz)
    anchor('Gate%d' % n, 'gate', (gx, gy + 6.5, gz), gyaw, (18, 13, 2), 'Gates', {'ZoneIndex': n, 'Bridge': n})
    tx, tz = local(gx, gz, gyaw, -11.1, -4.6)
    anchor('Gate%d_Toll' % n, 'toll', (tx, gy + 4.6, tz), gyaw, (3, 2, 3), 'Gates', {'ZoneIndex': n})
    reserve(gx, gz, 15)
    for t in (.0, .5, 1.0):
        reserve(lerp(s[0], e[0], t), lerp(s[1], e[1], t), 9)
    return (gx, gz), s, e

def fence_ring(I, theme, gaps, inset=3.0, L=14.0):
    """chunky fence round the rim, a gap at every bridge head (gaps = world points)"""
    cx, cz = I['c']
    gaps = list(gaps) + [edge_pt(I, (B_ if A_ is I else A_)['c'], inset) for n_, A_, B_, s_, e_ in BRIDGES if I in (A_, B_)]   # every bridge head
    a = 0.0; pts = []
    def rim(a): R = isle_R(I, a) - inset; return (cx + math.cos(a) * R, cz + math.sin(a) * R)
    while a < math.tau - 1e-6:                                              # posts a full segment (chord >= L) apart: no overlaps
        p = rim(a); pts.append(p); a += L / (isle_R(I, a) - inset) * .9
        while a < math.tau and math.dist(p, rim(a)) < L: a += .002
    if math.dist(pts[-1], pts[0]) < L: pts.pop()                          # closing segment too short: leave a gap
    for p, q in zip(pts, pts[1:] + pts[:1]):
        mx, mz = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        if any(math.hypot(mx - g[0], mz - g[1]) < 18 for g in gaps): continue
        d = V3((q[0] - p[0], 0, q[1] - p[1])); yaw = math.degrees(math.atan2(-d.z, d.x))
        place('Fence_' + theme, lambda: PP.fence(theme), p[0], p[1], yaw, 1.0, H(*p) - .1, group='Fences')

def rim_points(I, frac0, frac1, n, rng):
    cx, cz = I['c']; out = []
    for k in range(n):
        a = rng.uniform(0, math.tau); f = rng.uniform(frac0, frac1); R = isle_R(I, a) * f
        out.append((cx + math.cos(a) * R, cz + math.sin(a) * R))
    return out

def scatter(I, items, n, r_clear, rng, frac=(.25, .9), path_clear=4.0, group='Dressing', yaw_rand=True):
    """items = [(key, fn, scale_range)], n tries; keeps clear of paths + reserved spots"""
    placed = 0
    for x, z in rim_points(I, frac[0], frac[1], n * 14, rng):
        if placed >= n: break
        if path_d(x, z) < path_clear or not free(x, z, r_clear): continue
        key, fn, sr = items[rng.randrange(len(items))]
        place(key, fn, x, z, rng.uniform(0, 360) if yaw_rand else 0, rng.uniform(*sr), group=group)
        reserve(x, z, r_clear * .8); placed += 1

BREAK = []
def breakables(I, zone, kinds, rng, n=40, entry=None):
    """clusters of 3-5 breakables off the paths; tier rises with distance from the zone entry"""
    cx, cz = I['c']; got = 0; tries = 0
    ex, ez = entry
    while got < n and tries < 1500:
        tries += 1
        a = rng.uniform(0, math.tau); f = rng.uniform(.18, .8); R = isle_R(I, a) * f
        x, z = cx + math.cos(a) * R, cz + math.sin(a) * R
        if path_d(x, z) < 5 or not free(x, z, 5): continue
        k = rng.randint(3, 5)
        for j in range(k):
            if got >= n: break
            for _t in range(6):
                px, pz = x + rng.uniform(-7, 7), z + rng.uniform(-7, 7)
                if isle_at(px, pz) and isle_R(I, polar(I, px, pz)[1]) - polar(I, px, pz)[0] > 8 and path_d(px, pz) > 3.5 and free(px, pz, 2.6): break
            else: continue
            d = math.hypot(px - ex, pz - ez) / (2 * I['R'])
            tier = 1 if d < .45 else (2 if d < .8 else 3)
            if rng.random() < .15: tier = min(3, tier + 1)
            key, fn = kinds[tier][rng.randrange(len(kinds[tier]))]
            y = place(key, fn, px, pz, rng.uniform(0, 360), 1.0, group='Breakables_Z%d' % zone)
            reserve(px, pz, 2.6); got += 1
            anchor('Breakable_Z%d_%02d' % (zone, got), 'breakable', (px, H(px, pz) + 1.2, pz), 0, (4, 3, 4), 'Breakables_Z%d' % zone,
                   {'Zone': zone, 'Tier': tier, 'Kind': key})
        reserve(x, z, 9)
    print('BREAKABLES', zone, got)

def egg_stand(I, zone, kind, x, z, tx, tz, idx):
    yaw = face(x, z, tx, tz)
    place('EggStand_' + kind, lambda: PP.egg_stand(kind), x, z, yaw, 1.0, group='Hatchery' if zone == 0 else 'Zone%d' % zone)
    reserve(x, z, 7)
    anchor('EggStand%d' % idx, 'eggstand', (x, H(x, z) + 9.3, z), yaw, (6, 8, 6), 'EggStands', {'Zone': zone, 'Egg': kind, 'Index': idx})
    px, pz = local(x, z, yaw, 0, -7.0)
    anchor('EggStand%d_Prompt' % idx, 'eggprompt', (px, H(px, pz) + 2.5, pz), yaw, (6, 5, 3), 'EggStands', {'Zone': zone, 'Index': idx})

def zone_bounds(I, zone):
    cx, cz = I['c']; R = I['R'] * 1.06
    anchor('Zone%d' % zone, 'zone', (cx, I['top'] + 20, cz), 0, (2 * R, 60, 2 * R), 'Zones', {'Zone': zone, 'Name': I['name']})

# ------------------------------------------------------------------ hub
def hub(rng):
    I = HUB
    plaza(0, 0, 32, I)
    reserve(0, 0, 33)
    place('PetFountain', PP.pet_fountain, 0, 0, face(0, 0, 0, 70), 1.0, H(0, 0) + .3, group='Hero')
    place('PetStatue', PP.pet_statue, 0, 0, face(0, 0, 0, 70), 1.0, H(0, 0) + .3, group='Hero')
    anchor('Fountain', 'station', (0, 30, 0), 0, (8, 8, 8), 'Stations', {'Station': 'Fountain'})
    # spawn
    for t in (.15, .3, .45, .6, .75):
        reserve(lerp(34, -6, t), lerp(78, 0, t), 6)
    place('SpawnPad', PP.spawn_pad, SPAWN[0], SPAWN[2], 0, 1.0, group='Spawn'); reserve(SPAWN[0], SPAWN[2], 10)
    anchor('SpawnLocation', 'spawn', (SPAWN[0], H(SPAWN[0], SPAWN[2]) + 1.4, SPAWN[2]), 0, (10, 1, 10), 'Spawn')
    # paths: spokes from the plaza ring
    g1 = edge_pt(I, Z1['c'], 19.0)
    path(I, [(0, 30), (0, 50), (0, 66)], 12)                                    # plaza -> spawn
    path(I, [(1, -30), (g1[0] * .5, (g1[1] - 30) / 2), g1, edge_pt(I, Z1['c'], 5.0)], 14)  # plaza -> gate 1 -> bridge
    path(I, [(-30, -4), (-40, -5), (-48, -5)], 12)                              # -> hatchery
    path(I, [(30, -6), (40, -8), (48, -8)], 11)                                 # -> shop
    path(I, [(22, -23), (32, -34), (38, -42)], 10)                              # -> upgrade machine
    path(I, [(-22, 22), (-30, 33), (-38, 42)], 10)                              # -> trading
    path(I, [(22, 22), (30, 32), (37, 40)], 10)                                 # -> leaderboard
    # hatchery: rainbow arch with 3 egg stands, facing the fountain
    hx, hz = -60.0, -5.0; hyaw = face(hx, hz, 0, 0)
    place('RainbowArch', PP.rainbow_arch, hx, hz, hyaw, 1.0, group='Hatchery'); reserve(hx, hz, 16)
    for i, (lx, kind) in enumerate(((-12.5, 'basic'), (0.0, 'spotted'), (12.5, 'golden'))):
        x, z = local(hx, hz, hyaw, lx, 2.0 + abs(lx) * .15)
        tx, tz = local(hx, hz, hyaw, lx * .4, -40)
        egg_stand(I, 0, kind, x, z, tx, tz, i + 1)
    anchor('Hatchery', 'station', (hx, H(hx, hz) + 30, hz), hyaw, (8, 4, 8), 'Stations', {'Station': 'Hatchery'})
    # pet shop
    sx, sz = 64.0, -9.0; syaw = face(sx, sz, 0, 0)
    place('PetShop', PP.pet_shop, sx, sz, syaw, 1.0, group='Stations'); reserve(sx, sz, 13)
    px, pz = local(sx, sz, syaw, 0, -7.5)
    anchor('PetShop', 'station', (px, H(px, pz) + 3, pz), syaw, (10, 6, 4), 'Stations', {'Station': 'PetShop'})
    # upgrade machine
    ux, uz = 45.0, -50.0; uyaw = face(ux, uz, 0, 0)
    place('UpgradeMachine', PP.upgrade_machine, ux, uz, uyaw, 1.15, group='Stations'); reserve(ux, uz, 9)
    px, pz = local(ux, uz, uyaw, 0, -8.0)
    anchor('UpgradeMachine', 'station', (px, H(px, pz) + 3, pz), uyaw, (8, 6, 4), 'Stations', {'Station': 'Upgrades'})
    # trading plaza
    tx, tz = -46.0, 49.0
    place('TradePad', PP.trade_pad, tx, tz, 0, 1.0, H(tx, tz) + .05, group='Trading'); reserve(tx, tz, 8)
    anchor('TradePad', 'station', (tx, H(tx, tz) + 2, tz), 0, (14, 4, 14), 'Stations', {'Station': 'Trading'})
    for k, (dx, dz, col) in enumerate(((-15, -4, 'sky'), (10, 12, 'pink'))):
        bx, bz = tx + dx, tz + dz
        place('TradeBooth_' + col, lambda col=col: PP.trade_booth(col), bx, bz, face(bx, bz, tx, tz), 1.0, group='Trading'); reserve(bx, bz, 7)
        anchor('TradeBooth%d' % (k + 1), 'station', (bx, H(bx, bz) + 4, bz), face(bx, bz, tx, tz), (8, 6, 8), 'Stations', {'Station': 'TradeBooth'})
    # leaderboard
    lx, lz = 48.0, 46.0; lyaw = face(lx, lz, 0, 30)
    place('LeaderboardFrame', PP.leaderboard, lx, lz, lyaw, 1.0, group='Stations'); reserve(lx, lz, 11)
    fx, fz = local(lx, lz, lyaw, 0, .2)
    anchor('LeaderboardFace', 'board', (fx, H(lx, lz) + 9.5, fz), lyaw, (18, 11, .4), 'Stations', {'Station': 'Leaderboard'})
    # lamps round the plaza + benches
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8
        x, z = math.cos(a) * 37, math.sin(a) * 37
        if path_d(x, z) < 1.5: continue
        place('LampPost_hub', lambda: PP.lamp_post('hub'), x, z, 0, 1.0, group='Hub'); reserve(x, z, 2)
    for a in (math.radians(120), math.radians(60), math.radians(240), math.radians(300)):
        x, z = math.cos(a) * 41, math.sin(a) * 41
        if path_d(x, z) < 2 or not free(x, z, 3): continue
        place('Bench_pink', lambda: PP.bench('pink'), x, z, face(x, z, 0, 0), 1.0, group='Hub'); reserve(x, z, 4)
    fence_ring(I, 'hub', [edge_pt(I, Z1['c'], 3)])
    # trees + bushes + flowers (deferred, placement-checked)
    trees = [('ptA', lambda: PP.puff_tree(1, 'leaf', 16), (1.1, 1.4)), ('ptB', lambda: PP.puff_tree(5, 'pink', 15), (1.1, 1.4)),
             ('ptC', lambda: PP.puff_tree(3, 'leaf', 18), (1.1, 1.3))]
    scatter(I, trees, 13, 8, rng, (.74, .9))
    scatter(I, [('pbA', lambda: PP.puff_bush(1, 'leaf'), (.9, 1.2)), ('pbB', lambda: PP.puff_bush(2, 'leaf'), (.8, 1.1))], 12, 4, rng, (.55, .92))
    scatter(I, [('fpA', lambda: PP.flower_patch(1), (1, 1.2)), ('fpB', lambda: PP.flower_patch(2, ('sky', 'cloud', 'yellow')), (1, 1.2))], 12, 3, rng, (.45, .9))
    scatter(I, [('gtA', lambda: PP.grass_tuft(1), (1, 1.4))], 14, 2, rng, (.4, .95))
    zone_bounds(I, 0)

# ------------------------------------------------------------------ zones
def zone(I, zone_i, entry, exit_gate, rng, theme):
    cx, cz = I['c']
    # main path entry -> centre -> exit (or a loop round the centre for the last zone)
    mid = (cx + (entry[0] - cx) * .1, cz + (entry[1] - cz) * .1)
    if exit_gate:
        k = (exit_gate[0] - cx, exit_gate[1] - cz)
        side = (-k[1] * .35, k[0] * .35)
        path(I, [entry, ((entry[0] + cx) / 2 + side[0] * .4, (entry[1] + cz) / 2 + side[1] * .4), (cx + side[0] * .2, cz + side[1] * .2),
                 ((exit_gate[0] + cx) / 2 - side[0] * .3, (exit_gate[1] + cz) / 2 - side[1] * .3), exit_gate], 12)
    else:
        path(I, [entry, ((entry[0] + cx) / 2, (entry[1] + cz) / 2), (cx, cz)], 12)
    # side loop
    R = I['R'] * .5; a0 = math.atan2(entry[1] - cz, entry[0] - cx)
    loop = [(cx + math.cos(a0 + math.pi * (.25 + k * .25)) * R, cz + math.sin(a0 + math.pi * (.25 + k * .25)) * R) for k in range(7)]
    path(I, loop, 8)
    # zone egg stand beside the entry, facing the path
    ea = math.atan2(entry[1] - cz, entry[0] - cx)
    ex, ez = cx + math.cos(ea + .32) * I['R'] * .66, cz + math.sin(ea + .32) * I['R'] * .66
    egg_stand(I, zone_i, theme, ex, ez, entry[0] * .5 + cx * .5, entry[1] * .5 + cz * .5, 3 + zone_i)
    return loop

def meadow(rng, entry, exit_gate):
    I = Z1
    zone(I, 1, entry, exit_gate, rng, 'meadow')
    cx, cz = I['c']
    px, pz = cx - 38, cz + 20
    if free(px, pz, 8) and path_d(px, pz) > 5: place('PicnicSet', PP.picnic_set, px, pz, 20, 1.3, group='Zone1'); reserve(px, pz, 8)
    kinds = {1: [('CoinPile_S', lambda: PP.coin_pile(False)), ('GiftBox_pink', lambda: PP.gift_box('pink'))],
             2: [('CoinPile_L', lambda: PP.coin_pile(True)), ('Chest_T2', lambda: PP.chest(False))],
             3: [('Chest_T3', lambda: PP.chest(True))]}
    scatter(I, [('msA', lambda: PP.mushroom(1, 'red', 4), (.8, 1.4)), ('msB', lambda: PP.mushroom(2, 'orange', 3), (.8, 1.3))], 10, 4, rng, (.3, .88), group='Zone1')
    scatter(I, [('stA', lambda: PP.stump(1), (.9, 1.2)), ('srA', lambda: PP.soft_rock(1, 3.0), (.8, 1.4)), ('srB', lambda: PP.soft_rock(2, 2.2), (.8, 1.3))], 7, 4, rng, (.4, .9), group='Zone1')
    scatter(I, [('lpM', lambda: PP.lamp_post('meadow'), (1, 1))], 0, 2, rng)
    fence_ring(I, 'meadow', [b for b in (entry, exit_gate)])
    scatter(I, [('ptA', lambda: PP.puff_tree(1, 'leaf', 16), (1.2, 1.6)), ('ptC', lambda: PP.puff_tree(3, 'leaf', 18), (1.2, 1.5)),
                ('ptD', lambda: PP.puff_tree(7, 'leaf', 14), (1.2, 1.5))], 18, 9, rng, (.3, .9), group='Zone1')
    breakables(I, 1, kinds, rng, 42, entry)
    scatter(I, [('pbA', lambda: PP.puff_bush(1, 'leaf'), (.9, 1.3)), ('pbC', lambda: PP.puff_bush(3, 'leaf'), (.8, 1.2))], 12, 4, rng, (.3, .92), group='Zone1')
    scatter(I, [('fpA', lambda: PP.flower_patch(1), (1, 1.3)), ('fpC', lambda: PP.flower_patch(3, ('red', 'cloud', 'pink')), (1, 1.3)),
                ('fpB', lambda: PP.flower_patch(2, ('sky', 'cloud', 'yellow')), (1, 1.2))], 22, 3, rng, (.2, .95), group='Zone1')
    scatter(I, [('gtA', lambda: PP.grass_tuft(1), (1, 1.5))], 16, 2, rng, (.2, .95), group='Zone1')
    zone_bounds(I, 1)

def candy(rng, entry, exit_gate):
    I = Z2
    zone(I, 2, entry, exit_gate, rng, 'candy')
    cx, cz = I['c']
    dx, dz = cx + 30, cz + 34
    if free(dx, dz, 8) and path_d(dx, dz) > 6: place('GiantDonut', PP.giant_donut, dx, dz, 30, 1.6, group='Zone2'); reserve(dx, dz, 9)
    kinds = {1: [('GiftBox_pink', lambda: PP.gift_box('pink')), ('GiftBox_sky', lambda: PP.gift_box('sky', 'pink'))],
             2: [('CoinPile_L', lambda: PP.coin_pile(True)), ('Chest_T2', lambda: PP.chest(False)), ('GiftBox_lilac', lambda: PP.gift_box('lilac', 'yellow'))],
             3: [('Chest_T3', lambda: PP.chest(True))]}
    scatter(I, [('lolA', lambda: PP.lollipop(1, 11, ('pink', 'cloud')), (.9, 1.3)), ('lolB', lambda: PP.lollipop(2, 9, ('sky', 'cloud')), (.9, 1.2)),
                ('lolC', lambda: PP.lollipop(3, 10, ('mint', 'yellow')), (.9, 1.2))], 9, 5, rng, (.3, .85), group='Zone2')
    scatter(I, [('ccA', lambda: PP.candy_cane(1), (.9, 1.3)), ('gdA', lambda: PP.gumdrops(1), (1, 1.3)), ('gdB', lambda: PP.gumdrops(2), (1, 1.3))], 12, 4, rng, (.3, .9), group='Zone2')
    fence_ring(I, 'candy', [entry, exit_gate])
    scatter(I, [('ctA', lambda: PP.cotton_tree(1), (1.2, 1.6)), ('ctB', lambda: PP.cotton_tree(2), (1.2, 1.5)), ('ctC', lambda: PP.cotton_tree(3), (1.2, 1.5))],
            17, 9, rng, (.35, .9), group='Zone2')
    breakables(I, 2, kinds, rng, 42, entry)
    scatter(I, [('pbP', lambda: PP.puff_bush(4, 'pink'), (.9, 1.2)), ('pbM', lambda: PP.puff_bush(5, 'mint'), (.9, 1.2))], 12, 4, rng, (.3, .92), group='Zone2')
    scatter(I, [('fpD', lambda: PP.flower_patch(4, ('pink', 'yellow', 'sky')), (1, 1.3))], 12, 3, rng, (.2, .95), group='Zone2')
    zone_bounds(I, 2)

def crystal(rng, entry):
    I = Z3
    zone(I, 3, entry, None, rng, 'crystal')
    kinds = {1: [('CrystalClump_T2', lambda: PP.crystal_clump(False)), ('CoinPile_L', lambda: PP.coin_pile(True))],
             2: [('CrystalClump_T2', lambda: PP.crystal_clump(False)), ('Chest_T2', lambda: PP.chest(False))],
             3: [('CrystalClump_T3', lambda: PP.crystal_clump(True)), ('Chest_T3', lambda: PP.chest(True))]}
    cx, cz = I['c']
    for k in range(5):                                                         # star lamps round the centre clearing
        a = k * math.tau / 5 + .3; x, z = cx + math.cos(a) * 15, cz + math.sin(a) * 15
        if path_d(x, z) > 1.5 and free(x, z, 2): place('StarLamp1', lambda: PP.star_lamp(1), x, z, face(x, z, cx, cz) + 90, 1.0, group='Zone3'); reserve(x, z, 3)
    scatter(I, [('csA', lambda: PP.crystal_spire(1), (.9, 1.4)), ('csB', lambda: PP.crystal_spire(2), (.9, 1.3)), ('csC', lambda: PP.crystal_spire(3, 1.2), (.9, 1.2))],
            10, 6, rng, (.3, .88), group='Zone3')
    scatter(I, [('gsA', lambda: PP.glow_shroom(1), (1, 1.5)), ('srC', lambda: PP.soft_rock(3, 2.6, 'stone'), (.8, 1.3))], 12, 4, rng, (.3, .92), group='Zone3')
    fence_ring(I, 'crystal', [entry])
    scatter(I, [('crA', lambda: PP.crystal_tree(1, 15, 'sky'), (1.2, 1.6)), ('crB', lambda: PP.crystal_tree(2, 15, 'pink'), (1.2, 1.5)), ('crC', lambda: PP.crystal_tree(4, 15, 'sky'), (1.2, 1.5))],
            17, 9, rng, (.35, .9), group='Zone3')
    breakables(I, 3, kinds, rng, 42, entry)
    scatter(I, [('pbL', lambda: PP.puff_bush(6, 'pink'), (.9, 1.2)), ('pbS', lambda: PP.puff_bush(7, 'sky'), (.9, 1.2))], 12, 4, rng, (.3, .92), group='Zone3')
    scatter(I, [('fpE', lambda: PP.flower_patch(5, ('cloud', 'sky', 'lilac')), (1, 1.3))], 10, 3, rng, (.2, .95), group='Zone3')
    zone_bounds(I, 3)

def frame(rng):
    """clouds + rocks on the lagoon round the chain (outside every island, off the bridge lines)"""
    cx, cz = 125.0, -90.0
    n = 0
    for k in range(40):
        a = k * math.tau / 40 + rng.uniform(-.05, .05); R = rng.uniform(330, 420) * (1.05 if math.sin(a) < 0 else 1.0)
        x, z = cx + math.cos(a) * R * 1.05, cz + math.sin(a) * R * 1.1
        if any(math.hypot(x - I['c'][0], z - I['c'][1]) < I['R'] + 40 for I in ISLES): continue
        if k % 3 == 0:
            place('Cloud%d' % (k % 4 + 1), lambda kk=k % 4 + 1: PP.cloud(kk, 1.8), x, z, rng.uniform(0, 360), rng.uniform(1.4, 2.2), SEA_Y - 2, group='Frame'); n += 1
    for k in range(10):
        a = rng.uniform(0, math.tau); R = rng.uniform(150, 300)
        x, z = cx + math.cos(a) * R, cz + math.sin(a) * R
        if any(math.hypot(x - I['c'][0], z - I['c'][1]) < I['R'] + 18 for I in ISLES): continue
        if any(seg_d(x, z, b[3], b[4]) < 20 for b in BRIDGES): continue
        place('SeaRock%d' % (k % 2 + 1), lambda kk=k % 2 + 1: PP.sea_rock(kk, 4.5), x, z, rng.uniform(0, 360), rng.uniform(1.0, 1.8), SEA_Y - 1.5, group='Frame')
    # a few high puffy clouds in the sky (beyond the play space)
    for k, (x, y, z, s) in enumerate(((-260, 120, -320, 3.0), (480, 140, -420, 3.4), (520, 110, 260, 2.8), (-280, 130, 240, 3.2))):
        place('Cloud%d' % (k % 4 + 1), lambda kk=k % 4 + 1: PP.cloud(kk, 1.8), x, z, k * 70, s, y, group='Frame')
def seg_d(x, z, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dz * dz or 1
    t = clamp(((x - a[0]) * dx + (z - a[1]) * dz) / L2)
    return math.hypot(x - a[0] - dx * t, z - a[1] - dz * t)

def sea():
    mb = MB(); bm = bmesh.new()
    for (x0, z0, x1, z1) in ((-1700, -1900, 1900, 1700),):
        f = bm.faces.new([bm.verts.new((x, SEA_Y, z)) for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))])
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb.add(bm, lambda f: [(U('water'), .33)] * len(f.loops)); static('Sea_LagoonWater', mb, 'Water')   # '...Water': the checks treat it as water
    # lagoon floor 6 under the water (players who swim out land on it); its outer ring rises to the waterline at the
    # sea's edge so the open edge meets a shore. 10 x 10 cells (> 64 tris: a mesh, not flat oversize Parts)
    xs = [x0 - 20, x0 + 1, x0 + 15] + [lerp(x0 + 15, x1 - 15, k / 6) for k in range(1, 6)] + [x1 - 15, x1 - 1, x1 + 20]
    zs = [z0 - 20, z0 + 1, z0 + 15] + [lerp(z0 + 15, z1 - 15, k / 6) for k in range(1, 6)] + [z1 - 15, z1 - 1, z1 + 20]
    gb = bmesh.new(); VV = {}
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            ring = min(i, j, len(xs) - 1 - i, len(zs) - 1 - j)                  # 0 = outside the sea, 1 = just inside its edge
            VV[i, j] = gb.verts.new((x, (SEA_Y + 2.0, SEA_Y + .05)[ring] if ring < 2 else SEA_Y - 6.0, z))
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            f = gb.faces.new((VV[i, j], VV[i, j + 1], VV[i + 1, j + 1], VV[i + 1, j])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    gm = MB(); gm.add(gb, lambda f: [(U('sky'), .3)] * len(f.loops)); static('Ground_SeaBed', gm, 'Water')
    # lighter shallows ring round each island (a flat annulus just under the waterline reads through as turquoise)
    sb = MB()
    for I in ISLES:
        cx, cz = I['c']; b2 = bmesh.new(); NS = 96; inner = []; outer = []
        for i in range(NS):
            a = i * math.tau / NS; R = isle_R(I, a)
            inner.append(b2.verts.new((cx + math.cos(a) * (R + 3.5), SEA_Y + .08, cz + math.sin(a) * (R + 3.5))))
            outer.append(b2.verts.new((cx + math.cos(a) * (R + 16), SEA_Y + .05, cz + math.sin(a) * (R + 16))))
        for i in range(NS):
            j = (i + 1) % NS; f = b2.faces.new((inner[i], inner[j], outer[j], outer[i])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        sb.add(b2, lambda f: [(U('water'), .72 if l.vert.co.y > SEA_Y + .07 else .42) for l in f.loops])
    static('Sea_ShallowsWater', sb, 'Water')

def build():
    rng = random.Random(7)
    for I in ISLES: static('Ground_' + I['name'], isle_mesh(I), 'Ground')
    g1, s1, e1 = link(1, HUB, Z1, 'meadow')
    g2, s2, e2 = link(2, Z1, Z2, 'candy')
    g3, s3, e3 = link(3, Z2, Z3, 'crystal')
    hub(rng)
    meadow(rng, edge_pt(Z1, HUB['c'], 5.0), (g2[0], g2[1])); path(Z1, [g2, edge_pt(Z1, Z2['c'], 5.0)], 12)
    candy(rng, edge_pt(Z2, Z1['c'], 5.0), (g3[0], g3[1])); path(Z2, [g3, edge_pt(Z2, Z3['c'], 5.0)], 12)
    crystal(rng, edge_pt(Z3, Z2['c'], 5.0))
    frame(rng)
    sea()
    path_meshes()
    build_solid(); place_soft(random.Random(5))
    print('SOFT_REJECTED', len(REJECT), REJECT[:12])

# ------------------------------------------------------------------ look: bright candy noon
def look():
    w = bpy.data.worlds.new('Noon'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.2; mr.inputs['From Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.62, .86, 1.0, 1)
    cr.elements[1].position = .6; cr.elements[1].color = (.04, .28, 1.0, 1)
    e = cr.elements.new(.22); e.color = (.25, .6, 1.0, 1)
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .85
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .3; b.inputs['Roughness'].default_value = .55
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.data.color = (1.0, .96, .9); sun.data.angle = math.radians(4)
    el = math.radians(55); az = math.radians(150)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .7; fill.data.color = (.75, .85, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.5, .6, .5)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    hz = bpy.data.meshes.new('Haze'); hb = bmesh.new(); bmesh.ops.create_cube(hb, size=1.0); hb.to_mesh(hz); hb.free()
    ho = bpy.data.objects.new('HazeVolume', hz); SC.collection.objects.link(ho); ho.scale = (2000, 2000, 400); ho.location = (0, 0, 150)
    hm = bpy.data.materials.new('HazeMat'); hm.use_nodes = True; hn = hm.node_tree
    for n in list(hn.nodes):
        if n.type != 'OUTPUT_MATERIAL': hn.nodes.remove(n)
    vol = hn.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = .000006
    vol.inputs['Color'].default_value = (.85, .93, 1.0, 1)
    hn.links.new(vol.outputs[0], hn.nodes['Material Output'].inputs['Volume']); hz.materials.append(hm)
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    for k, v in (('taa_render_samples', 32), ('shadow_pool_size', '1024'), ('use_raytracing', False), ('volumetric_end', 2000.0)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SHOTS = {
    'map_beauty.png': ((34, 17, 78), (-12, 15, -6), 50),
    'map_overview.png': ((-230, 360, 290), (110, 0, -70), 40),
    'map_spawn.png': ((0, 11, 84), (0, 14, 0), 60),
    'map_top.png': ((125, 900, -90.01), (125, 0, -90), 50),
    'map_hatchery.png': ((-20, 16, 12), (-60, 8, -6), 55),
    'map_meadow.png': ((-80, 60, -170), (8, 8, -238), 55),
    'map_candy.png': ((120, 60, -110), (210, 12, -172), 55),
    'map_crystal.png': ((150, 70, 40), (225, 18, 80), 55),
    'map_gate.png': ((14, 14, -40), (2, 10, -80), 55),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
           'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'tris_by_group': GROUP_TRIS, 'soft_rejected': REJECT,
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'islands': [{k: I[k] for k in ('name', 'c', 'R', 'top')} for I in ISLES]},
          open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'pet_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATIC_TRIS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
