# blender -b --factory-startup --python sky_map.py -> Skyrise Simulator (sky_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: floating sky islands + zone strip (no ground plane).
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import sky_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, voronoi_cells, shrink, ccw, ngon_prism, MB, box

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

# ------------------------------------------------------------------ layout: a rising chain of islands
#           name      cx    cz    R    y    biome    top colour
ISL = [('Spawn',     0,     0,  72,   0, 'spawn',  'grass'),
       ('Meadow',    0,  -230,  86,  14, 'meadow', 'grass'),
       ('Dune',   -230,  -380,  84,  34, 'dune',   'sand'),
       ('Frost',     0,  -540,  82,  58, 'frost',  'snow'),
       ('Ember',   230,  -400,  84,  86, 'ember',  'basalt'),
       ('Summit',  230,  -640,  58, 130, 'summit', 'grass')]
SPAWN = (0, 24)

def rim(i, a):
    s = i * 1.7 + .4; R = ISL[i][3]
    return R * (1 + .07 * math.sin(3 * a + s) + .04 * math.sin(5 * a + 2 * s))

def island_at(x, z, m=0.0):
    """index of the island whose rim (minus margin m) contains (x, z), else None"""
    for i, (_, cx, cz, R, y, *_r) in enumerate(ISL):
        dx, dz = x - cx, z - cz; d = math.hypot(dx, dz)
        if d < R * 1.2 and d < rim(i, math.atan2(dz, dx)) - m: return i
    return None

def H(x, z):
    i = island_at(x, z)
    if i is None: return None
    _, cx, cz, R, y, biome, _c = ISL[i]
    d = math.hypot(x - cx, z - cz) / R
    bump = (nz(x, 0, z, 26, 11 + i) - .5) * 2.0 * smooth(clamp((d - .35) / .4))      # flat middle, gentle bumps outward
    if biome in ('spawn', 'summit'): bump *= .3
    return y + bump

# bridges: (from, to, kind) -> deck from rim to rim, 3 studs into each island
BR = [(0, 1, 'wood'), (1, 2, 'wood'), (2, 3, 'stone'), (3, 4, 'stone'), (4, 5, 'stone')]
def bridge_ends(a, b):
    A, B = ISL[a], ISL[b]
    d = Vector((B[1] - A[1], 0, B[2] - A[2])); ang = math.atan2(d.z, d.x); d.normalize()
    p0 = Vector((A[1], A[4], A[2])) + d * (rim(a, ang) - 3)
    p1 = Vector((B[1], B[4], B[2])) - d * (rim(b, ang + math.pi) - 3)
    p0.y = H(p0.x, p0.z) or A[4]; p1.y = H(p1.x, p1.z) or B[4]
    return p0, p1
ENDS = {(a, b): bridge_ends(a, b) for a, b, _k in BR}

def segd(px, pz, a, b):
    dx, dz = b.x - a.x, b.z - a.z; L = dx * dx + dz * dz
    t = clamp(((px - a.x) * dx + (pz - a.z) * dz) / L) if L else 0
    return math.hypot(px - a.x - dx * t, pz - a.z - dz * t)

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
        FOOT[key] = min(r, 7.0)
    return FOOT[key]
TB = [None]
def Hm(x, z):
    """height of the built island top MESH (what players stand on); H before the tops exist"""
    if TB[0] is None:
        obs = [o for o in bpy.data.objects if o.name.startswith('Top_')]
        if not obs: return H(x, z)
        from mathutils.bvhtree import BVHTree
        bm = bmesh.new()
        for o in obs:
            me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
        TB[0] = BVHTree.FromBMesh(bm)
    if H(x, z) is None: return None
    hit = TB[0].ray_cast(r2b((x, 400, z)), Vector((0, 0, -1)), 800)
    return hit[0].z if hit[0] is not None else H(x, z)
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    meshes = kit(key, fn)
    if y is None:
        fr = foot(key) * s
        hs = [Hm(x, z)] + [Hm(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        hs = [h for h in hs if h is not None]
        y = (min(hs) if hs else 0) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
EXT = {}
def ext(key):
    """widest horizontal reach of a kit prop (all parts)"""
    if key not in EXT: EXT[key] = max((math.hypot(v.co.x, v.co.y) for me in LIB[key][0].values() for v in me.vertices), default=1.0)
    return EXT[key]
def spread(x, z, r):
    hs = [h for h in [Hm(x, z)] + [Hm(x + math.cos(a) * r, z + math.sin(a) * r) for a in [k * math.tau / 8 for k in range(8)]] if h is not None]
    return max(hs) - min(hs) if hs else 99.0
def on_bridge_line(x, z, m=8.0):
    return any(segd(x, z, p0, p1) < m for p0, p1 in ENDS.values())

# ------------------------------------------------------------------ island surfaces + undersides
def path_dist(i, x, z):
    return min([math.hypot(x - a, z - b) for a, b in PATHPTS.get(i, [])] or [1e9])

def island_mesh(i):
    name, cx, cz, R, y, biome, top = ISL[i]
    NR, NA = 18, 96
    bm = bmesh.new(); V = [[None] * NA for _ in range(NR + 1)]
    centre = bm.verts.new((cx, H(cx, cz), cz))
    for r in range(1, NR + 1):
        t = r / NR
        for k in range(NA):
            a = k * math.tau / NA; rr = rim(i, a) * t
            x, z = cx + math.cos(a) * rr, cz + math.sin(a) * rr
            h = H(x, z) if r < NR else y + (H(cx + math.cos(a) * rr * .97, cz + math.sin(a) * rr * .97) or y) - y
            V[r][k] = bm.verts.new((x, h, z))
    for k in range(NA): bm.faces.new((centre, V[1][(k + 1) % NA], V[1][k]))
    for r in range(1, NR):
        for k in range(NA): bm.faces.new((V[r][k], V[r][(k + 1) % NA], V[r + 1][(k + 1) % NA], V[r + 1][k]))
    lip = [bm.verts.new((v.co.x, y - .6, v.co.z)) for v in V[NR]]                      # rim lip down to the underside
    for k in range(NA): bm.faces.new((V[NR][k], V[NR][(k + 1) % NA], lip[(k + 1) % NA], lip[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.y) > .3 and f.normal.y < 0: f.normal_flip()
        elif abs(f.normal.y) <= .3 and f.normal.dot(Vector((c.x - cx, 0, c.z - cz))) < 0: f.normal_flip()
    uT, uD = F.PAL.u(top), F.PAL.u('dirt')
    def shade(f):
        c = f.calc_center_median()
        if f.normal.y < .5: return [(uD, .5)] * len(f.loops)                          # the lip
        d = math.hypot(c.x - cx, c.z - cz) / R
        v = .55 + (nz(c.x, 0, c.z, 14, 5 + i) - .5) * .16 + f.normal.y * .08 - smooth(clamp((d - .8) / .2)) * .08
        if biome == 'spawn' or biome == 'meadow': v += ((int(math.atan2(c.z - cz, c.x - cx) / .26) % 2) * .04)   # mowed rays
        patch = nz(c.x, 3, c.z, 24, 30 + i)                                   # two-tone patches
        if patch > .6: v -= .1 * smooth((patch - .6) / .12)
        elif patch < .32: v += .07 * smooth((.32 - patch) / .1)
        return [(uT, clamp(v, .1, .92))] * len(f.loops)
    mb = MB(); mb.add(bm, shade)
    me = F.mesh_from('Top_' + name, mb, F.materials()['pal']); sub('Islands').objects.link(bpy.data.objects.new('Top_' + name, me))
    U = FP.island_under(i + 1, R, R * .9, lambda a: rim(i, a), top_y=0.0, n=48, top_col=top)   # 48 segments: 450k map budget
    meshes = F.to_kit(U, KIT); LIB['under%d' % i] = (meshes, U.tris)
    place('under%d' % i, None, cx, cz, 0, y=y, group='Islands')

def paving(i, R, seed=4, col='stone', cx=None, cz=None):
    _, icx, icz, _R, y, *_r = ISL[i]
    cx = icx if cx is None else cx; cz = icz if cz is None else cz
    rng = random.Random(seed); mb = MB()
    base = F.at(F.cyl(R + .5, .5, sides=48, y0=-.35), (cx, y, cz)); mb.add(base, F.S('dirt', base=.4, up=.1, jit=0))
    for site, poly in voronoi_cells(cx - R, cx + R, cz - R, cz + R, 3.8, seed=seed):
        if max(math.hypot(x - cx, z - cz) for x, z in poly) > R: continue
        ring = math.hypot(site[0] - cx, site[1] - cz) / R
        c = 'gold' if (.46 < ring < .56) else col
        mb.add(ngon_prism(ccw(shrink(poly, .9)), y - .2, y + .3 + rng.uniform(-.04, .04), .1),
               F.S(c, base=(.6 if c != 'gold' else .55) + rng.uniform(-.07, .07), up=.15, jit=0))
    me = F.mesh_from('Paving_%s' % ISL[i][0], mb, F.materials()['pal']); sub('Islands').objects.link(bpy.data.objects.new('Paving_%s' % ISL[i][0], me))

PATHPTS = {}
def winding_path(i, pin, pout, rng):
    """stepping-stone path from the entry bridge end through the island middle to the exit end"""
    _, cx, cz, R, y, *_r = ISL[i]
    mid = Vector((cx + rng.uniform(-.15, .15) * R, 0, cz + rng.uniform(-.15, .15) * R))
    pts = []
    for a, b in ((pin, mid), (mid, pout)):
        a = Vector((a.x, 0, a.z)); b = Vector((b.x, 0, b.z)); n = int((b - a).length / 3.4)
        perp = Vector((-(b - a).z, 0, (b - a).x)).normalized()
        for k in range(n):
            t = k / n; p = a.lerp(b, t) + perp * math.sin(t * math.pi * 2) * 6
            pts.append(p)
    for k, p in enumerate(pts):
        if island_at(p.x, p.z, 4) is None: continue
        place('stone%d' % (k % 3), lambda k=k: FP.path_stone(k % 3), p.x, p.z, rng.uniform(0, 360), sink=.1, group=ISL[i][0])
        reserve(p.x, p.z, 2.6); PATHPTS.setdefault(i, []).append((p.x, p.z))
    return pts

# ------------------------------------------------------------------ build
def build():
    rng = random.Random(21)
    # bridges + zone gates (front faces the island you come from)
    for z_i, (a, b, kind) in enumerate(BR, 1):
        p0, p1 = ENDS[(a, b)]
        L = math.hypot(p1.x - p0.x, p1.z - p0.z); rise = p1.y - p0.y
        yaw = face(p0.x, p0.z, p1.x, p1.z)
        place('bridge%d' % z_i, lambda L=L, rise=rise, kind=kind, z_i=z_i: FP.bridge(L, rise, 9.0, kind, z_i), p0.x, p0.z, yaw, y=p0.y + .2, group='Bridges')
        A = ISL[a]; d = Vector((p1.x - p0.x, 0, p1.z - p0.z)).normalized()
        g = p0 - d * 5
        place('gate%d' % z_i, lambda z_i=z_i: FP.zone_gate(z_i), g.x, g.z, face(g.x, g.z, A[1], A[2]), group='Gates')
        reserve(g.x, g.z, 13)
        for s in (-1, 1):                                                   # lamps at both bridge heads
            for p, dd in ((g, d),):                                           # gate side only (450k map budget)
                q = p + Vector((-dd.z, 0, dd.x)) * s * 13.5                       # outside the gate pillars
                place('lamp', FP.lamp_post, q.x, q.z, face(q.x, q.z, p.x, p.z) + 90, group='Bridges'); reserve(q.x, q.z, 2)
        reserve(p1.x, p1.z, 10); reserve(p0.x, p0.z, 10)
    for i in range(len(ISL)): island_mesh(i)                              # first: props sit on the built top mesh (Hm)
    spawn_island(rng)
    for i in (1, 2, 3, 4): zone_island(i, rng)
    summit(rng)
    sky_dressing(rng)
    for i in range(len(ISL)): micro_detail(i, rng)
    for i in range(len(ISL)): path_track(i)

def spawn_island(rng):
    paving(0, 34)
    place('spawnpad', FP.spawn_pad, *SPAWN, 0, y=.25, group='Spawn'); reserve(*SPAWN, 8)
    place('fountain', FP.plaza_fountain, 0, 0, 0, y=.25, group='Spawn'); reserve(0, 0, 12)
    for key, fn, x, z, r in (('egg', FP.egg_shrine, -38, 6, 12), ('sell', FP.sell_pad, 38, 6, 9),
                             ('upgrade', FP.upgrade_stand, 34, -34, 9), ('board', FP.leaderboard, -34, -36, 9)):
        place(key, fn, x, z, face(x, z, 0, 0), group='Spawn'); reserve(x, z, r)
    for k in range(5):                                                       # teleport arc behind spawn, one per zone
        a = math.radians(50 + k * 20); x, z = math.cos(a) * 50, math.sin(a) * 50
        place('tp%d' % (k + 1), lambda k=k: FP.teleport_pad('z%d' % (k + 1)), x, z, 0, group='Spawn'); reserve(x, z, 6)
    for k in range(8):
        a = k * math.tau / 8 + math.tau / 16; x, z = math.cos(a) * 36.5, math.sin(a) * 36.5
        if abs(x) < 10 and z < 0: continue
        if free(x, z, 1.5): place('lamp', FP.lamp_post, x, z, face(x, z, 0, 0) + 180, group='Spawn'); reserve(x, z, 2)
    rim_dress(0, rng, [('puffy%d' % k, (lambda k=k: FP.puffy_tree(k, rng.choice((11, 13, 15)), ('leaf', 'pink')[k % 2])), 7, 6) for k in range(4)] +
              [('blossom%d' % k, (lambda k=k: FP.blossom_tree(k + 20, 13 + k)), 7, 2) for k in range(2)] +
              [('bush%d' % k, (lambda k=k: FP.bush(k, ('leaf', 'pink')[k % 2])), 3, 6) for k in range(2)] +
              [('flowers%d' % k, (lambda k=k: FP.flower_bed(k)), 3.5, 4) for k in range(2)], inner=.62)   # counts trimmed: 450k map budget

def rim_dress(i, rng, items, inner=.55, outer=.92):
    """dress the outer ring of island i, keeping bridge heads, gates and stations clear"""
    _, cx, cz, R, y, *_r = ISL[i]
    for key, fn, r, n in items:
        done = 0
        for _ in range(n * 60):
            if done >= n: break
            a = rng.uniform(0, math.tau); t = rng.uniform(inner, outer); d = rim(i, a) * t
            x, z = cx + math.cos(a) * d, cz + math.sin(a) * d
            if island_at(x, z, r + 1.5) is None or on_bridge_line(x, z, 12) or not free(x, z, r): continue
            reserve(x, z, r); place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(.85, 1.15), group=ISL[i][0]); done += 1

BIOME = {
    'meadow': dict(rim=[('puffy%d' % k, k, 'puffy', 7, 3) for k in range(4)] + [('blossom%d' % k, k, 'blossom', 7, 2) for k in range(2)] +
                       [('bush%d' % k, k, 'bush', 3, 4) for k in range(2)] +
                       [('flowers%d' % k, k, 'flowers', 3.5, 2) for k in range(2)],
                   nodes=[('coin%d' % k, k, 'coin', 3) for k in range(3)] + [('chest1', 1, 'chest', 3)]),
    'dune':   dict(rim=[('cactus%d' % k, k, 'cactus', 3, 4) for k in range(3)] + [('mesa%d' % k, k, 'mesa', 8, 3) for k in range(2)],
                   nodes=[('coin%d' % k, k, 'coin', 3) for k in range(3)] + [('chest2', 2, 'chest', 3)]),
    'frost':  dict(rim=[('snowtree%d' % k, k, 'snowtree', 6, 6) for k in range(3)] + [('icespike%d' % k, k, 'icespike', 3.5, 4) for k in range(2)],
                   nodes=[('crys%d' % k, k, 'crystal', 3) for k in range(3)] + [('chest3', 3, 'chest', 3)]),
    'ember':  dict(rim=[('basalt%d' % k, k, 'basalt', 4, 5) for k in range(3)] + [('charred%d' % k, k, 'charred', 4, 4) for k in range(2)] +
                       [('lava%d' % k, k, 'lava', 7, 2) for k in range(2)],
                   nodes=[('gem%d' % k, k, 'gem', 3) for k in range(3)] + [('chest4', 4, 'chest', 3)]),
}
def maker(kind, k):
    return {'puffy': lambda: FP.puffy_tree(k + 10, 12 + k, ('leaf', 'leaf', 'pink', 'leaf')[k % 4]), 'bush': lambda: FP.bush(k + 10),
            'blossom': lambda: FP.blossom_tree(k + 20, 13 + k),
            'flowers': lambda: FP.flower_bed(k + 10), 'cactus': lambda: FP.cactus(k, 6 + k), 'mesa': lambda: FP.mesa_rock(k, 7 + k),
            'snowtree': lambda: FP.snow_tree(k, 13 + k * 2), 'icespike': lambda: FP.ice_spike(k), 'basalt': lambda: FP.basalt_rocks(k),
            'charred': lambda: FP.charred_tree(k), 'lava': lambda: FP.lava_pool(k, 5 + k),
            'coin': lambda: FP.coin_pile(k), 'chest': lambda: FP.chest(k), 'crystal': lambda: FP.crystal_node(k, 'crystal', 'ice'),
            'gem': lambda: FP.crystal_node(k + 5, 'gem', 'violet')}[kind]

def zone_island(i, rng):
    name, cx, cz, R, y, biome, top = ISL[i]
    pin = [ENDS[k][1] for k in ENDS if k[1] == i][0]; pout = [ENDS[k][0] for k in ENDS if k[0] == i]
    pout = pout[0] if pout else Vector((cx, y, cz))
    winding_path(i, pin, pout, rng)
    d = Vector((cx - pin.x, 0, cz - pin.z)).normalized(); side = Vector((-d.z, 0, d.x))
    sp = pin + d * 14 + side * 11; place('sign%d' % i, lambda i=i: FP.signpost(i), sp.x, sp.z, face(sp.x, sp.z, pin.x, pin.z), group=name); reserve(sp.x, sp.z, 3)
    tp = pin + d * 22 - side * 14; place('tp%d' % i, lambda i=i: FP.teleport_pad('z%d' % i), tp.x, tp.z, 0, group=name); reserve(tp.x, tp.z, 6)
    B = BIOME[biome]
    for c in range(4):                                                        # resource clusters (4: 450k map budget)
        for _ in range(80):
            a = rng.uniform(0, math.tau); t = rng.uniform(.2, .62); x, z = cx + math.cos(a) * rim(i, a) * t, cz + math.sin(a) * rim(i, a) * t
            if free(x, z, 9) and not on_bridge_line(x, z, 12): break
        n = rng.randint(2, 4)
        for k in range(n):
            key, kk, kind, r = rng.choice(B['nodes']) if k else B['nodes'][c % (len(B['nodes']) - 1)]
            for _ in range(30):
                px, pz = x + rng.uniform(-7, 7), z + rng.uniform(-7, 7)
                if island_at(px, pz, 4) is not None and free(px, pz, r) and spread(px, pz, 2.5) < .35: break   # not on a bump
            else: continue
            reserve(px, pz, r); place(key, maker(kind, kk), px, pz, rng.uniform(0, 360), s=rng.uniform(.9, 1.2), sink=.1, group=name)
    rim_dress(i, rng, [(key, maker(kind, kk), r, n) for key, kk, kind, r, n in B['rim']])
    if biome == 'ember':                                                      # lava cracks across the ground
        for k in range(12):
            for _ in range(60):
                a = rng.uniform(0, math.tau); t = rng.uniform(.15, .8); x, z = cx + math.cos(a) * rim(i, a) * t, cz + math.sin(a) * rim(i, a) * t
                if free(x, z, 3) and not on_bridge_line(x, z, 10): break
            place('crack%d' % (k % 3), lambda k=k: FP.lava_crack(k % 3), x, z, rng.uniform(0, 360), sink=.05, group=name)

MICRO = {
    'spawn':  ([('tuft%d', lambda k: FP.grass_tuft(k), 3), ('wflow%d', lambda k: FP.wildflowers(k), 3), ('peb%d', lambda k: FP.pebbles(k), 2)], 20),
    'meadow': ([('tuft%d', lambda k: FP.grass_tuft(k), 3), ('wflow%d', lambda k: FP.wildflowers(k), 3), ('mush%d', lambda k: FP.mushrooms(k), 2),
                ('peb%d', lambda k: FP.pebbles(k), 2)], 32),
    'dune':   ([('dgrass%d', lambda k: FP.dune_grass(k), 3), ('shrub%d', lambda k: FP.dry_shrub(k), 2), ('speb%d', lambda k: FP.pebbles(k + 10, 'sand'), 2)], 28),
    'frost':  ([('smound%d', lambda k: FP.snow_mound(k), 3), ('ishard%d', lambda k: FP.ice_shards(k), 3), ('peb%d', lambda k: FP.pebbles(k), 2)], 40),
    'ember':  ([('ash%d', lambda k: FP.ash_pile(k), 3), ('erock%d', lambda k: FP.ember_rocks(k), 3)], 34),
    'summit': ([('tuft%d', lambda k: FP.grass_tuft(k), 3), ('wflow%d', lambda k: FP.wildflowers(k), 3)], 10),
}
def path_track(i):
    """trodden track under the stepping stones: overlapping irregular flat blobs following H (organic edges)"""
    name, cx, cz, R, y, biome, top = ISL[i]
    if i not in PATHPTS or biome == 'ember': return
    rng = random.Random(77 + i); mb = MB()
    col, base = ('snow', .42) if biome == 'frost' else ('dirt', .6)
    pts = PATHPTS[i]; dense = []
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        for t in (0, .5): dense.append((ax + (bx - ax) * t, az + (bz - az) * t))
    for x, z in dense:
        h = H(x, z)
        if h is None: continue
        r = rng.uniform(2.3, 3.2)
        poly = [(math.cos(a) * r * rng.uniform(.75, 1.1), math.sin(a) * r * rng.uniform(.75, 1.1)) for a in [k * math.tau / 9 for k in range(9)]]
        mb.add(F.at(ngon_prism(poly, h - .35, h + .04 + rng.uniform(0, .02)), (x, 0, z)), F.S(col, base=base + rng.uniform(-.06, .04), up=.05, jit=0))
    me = F.mesh_from('Track_' + name, mb, F.materials()['pal']); sub('Islands').objects.link(bpy.data.objects.new('Track_' + name, me))

def micro_detail(i, rng):
    """clumps of small ground detail: off paths, bridge heads, stations (free()), and the spawn plaza"""
    name, cx, cz, R, y, biome, top = ISL[i]
    items, nclumps = MICRO[biome]
    made = 0
    for _ in range(nclumps * 40):
        if made >= nclumps: break
        a = rng.uniform(0, math.tau); t = rng.uniform(.1, .93); x, z = cx + math.cos(a) * rim(i, a) * t, cz + math.sin(a) * rim(i, a) * t
        if island_at(x, z, 2.5) is None or on_bridge_line(x, z, 9) or path_dist(i, x, z) < 4 or not free(x, z, 1.4): continue
        if biome == 'spawn' and math.hypot(x, z) < 37: continue
        if biome == 'summit' and math.hypot(x - cx, z - cz) < 46: continue
        made += 1
        for k in range(rng.randint(3, 6)):
            key, fn, nv = rng.choice(items); kk = rng.randrange(nv)
            px, pz = x + rng.uniform(-3, 3), z + rng.uniform(-3, 3)
            k_ = key % kk; kit(k_, lambda fn=fn, kk=kk: fn(kk)); sc = rng.uniform(.85, 1.25); r_ = ext(k_) * sc   # its real footprint
            if island_at(px, pz, 1.5) is None or path_dist(i, px, pz) < 3.2 or not free(px, pz, r_) or spread(px, pz, r_) > .15: continue
            reserve(px, pz, r_)
            place(k_, None, px, pz, rng.uniform(0, 360), s=sc, sink=-.05, group=name + '_Detail')   # mounds are half-sunk blobs: no extra sink

def summit(rng):
    i = 5; name, cx, cz, R, y, *_r = ISL[i]
    paving(i, 44, seed=9, col='cloud')
    place('trophy', FP.trophy, cx, cz, face(cx, cz, ENDS[(4, 5)][1].x, ENDS[(4, 5)][1].z), y=y + .3, group='Summit')
    reserve(cx, cz, 20)
    for k in range(8):
        a = k * math.tau / 8 + math.tau / 16; x, z = cx + math.cos(a) * 30, cz + math.sin(a) * 30
        if on_bridge_line(x, z, 10): continue
        place('gemS%d' % (k % 2), lambda k=k: FP.crystal_node(20 + k % 2, 'gem' if k % 2 else 'crystal', 'violet' if k % 2 else 'ice', 1.3),
              x, z, rng.uniform(0, 360), y=y + .3, group='Summit'); reserve(x, z, 4)   # on the paving top (y + .3)
    for k in range(10):
        a = k * math.tau / 10; x, z = cx + math.cos(a) * 46, cz + math.sin(a) * 46
        if island_at(x, z, 4) is None or on_bridge_line(x, z, 10): continue
        place('lamp', FP.lamp_post, x, z, face(x, z, cx, cz) + 180, group='Summit'); reserve(x, z, 2)

def sky_dressing(rng):
    n = 0
    for _ in range(400):                                                      # floating rocks between the islands
        if n >= 16: break
        x, z = rng.uniform(-360, 380), rng.uniform(-760, 120)
        if island_at(x, z, -30) is not None or on_bridge_line(x, z, 30): continue
        y = rng.uniform(-30, 150); s = rng.uniform(.8, 2.0)
        place('rock%d' % (n % 4), lambda n=n: FP.floating_rock(n % 4, 6.0), x, z, rng.uniform(0, 360), s=s, y=y, group='Sky'); n += 1
    CL = []                                                                   # clouds never merge into each other
    def cloud(k, x, z, s, y):
        key = 'cloud%d' % (k % 4); kit(key, lambda k=k: FP.cloud(k % 4, 2.6)); r = ext(key) * s
        if any(math.hypot(x - a, z - b) < r + c for a, b, c in CL): return
        CL.append((x, z, r)); place(key, None, x, z, rng.uniform(0, 360), s=s, y=y, group='Sky')
    for k in range(26):                                                       # the cloud sea (26: 450k map budget)
        x, z = rng.uniform(-700, 900), rng.uniform(-1200, 520)
        cloud(k, x, z, rng.uniform(.8, 1.5), rng.uniform(-140, -105))
    for k in range(6):                                                        # a few high clouds
        a = rng.uniform(0, math.tau); d = rng.uniform(950, 1400)
        cloud(k, 80 + math.cos(a) * d, -300 + math.sin(a) * d, 1.6, rng.uniform(170, 260))

# ------------------------------------------------------------------ look: bright early morning, low sun from the east
def look():
    w = bpy.data.worlds.new('Sky'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.5; mr.inputs['From Max'].default_value = .5
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp                    # below horizon stays sky blue
    cr.elements[0].color = (.55, .74, .98, 1); cr.elements[1].color = (.18, .45, .95, 1)
    e = cr.elements.new(.5); e.color = (1.0, .86, .7, 1)
    e = cr.elements.new(.62); e.color = (.66, .87, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .7
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .15; b.inputs['Roughness'].default_value = .92
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.6; sun.data.color = (1, .9, .76); sun.data.angle = math.radians(3)
    el = math.radians(24); to_sun = r2b((math.cos(el) * .92, math.sin(el), math.cos(el) * .38)) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (2600, 2600, 700); hz.location = r2b((100, 60, -300)); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); nt = vm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00018; pv.inputs['Color'].default_value = (.86, .93, 1, 1)
    nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

# Roblox material per palette ramp (each object gets the material that fits it; no textures in Roblox)
MATERIALS = {'grass': 'Grass', 'dirt': 'Ground', 'rock': 'Rock', 'stone': 'Slate', 'sand': 'Sand', 'snow': 'Snow',
             'ice': 'Ice', 'basalt': 'Basalt', 'wood': 'WoodPlanks', 'leaf': 'LeafyGrass', 'gold': 'Foil',
             'cloud': 'Marble', 'red': 'SmoothPlastic', 'violet': 'SmoothPlastic', 'pink': 'SmoothPlastic', 'white': 'SmoothPlastic'}
MAT_OVERRIDES = {'Cloud': 'SmoothPlastic', 'Horizon': 'SmoothPlastic',
                 'Puffy': {'wood': 'Wood', 'pink': 'LeafyGrass'}, 'SnowTree': {'wood': 'Wood'}, 'Charred': {'basalt': 'Wood'},
                 'Bush': {'pink': 'LeafyGrass'}, 'Cactus': {'leaf': 'Grass'}, 'IslandUnder': {'wood': 'Wood', 'leaf': 'LeafyGrass'},
                 'Gumdrop': 'SmoothPlastic'}
def material_skin():
    import roblox_materials as RM
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Cloud', 'Horizon'), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'sky_map.blend'))
if 'norender' not in ARGS:
    shot('map_spawn.png', (0, 9, 46), (40, 60, -560), 24)
    shot('map_overview.png', (520, 300, 260), (20, 40, -330), 26)
    shot('map_spawnplaza.png', (26, 16, 52), (-10, 4, -6), 30)
    shot('map_meadow.png', (60, 40, -150), (-10, 14, -250), 30)
    shot('map_dune.png', (-150, 60, -300), (-240, 34, -390), 30)
    shot('map_frost.png', (70, 80, -470), (0, 58, -550), 30)
    shot('map_ember.png', (300, 110, -330), (225, 86, -410), 30)
    shot('map_summit.png', (190, 150, -560), (230, 152, -640), 30)
    shot('map_under.png', (150, -60, -120), (0, -20, -240), 26)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
