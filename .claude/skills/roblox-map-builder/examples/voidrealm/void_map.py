# blender -b --factory-startup --python void_map.py [-- norender] [-- name.png ...] -> The Shattered Void (void_map.blend)
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: ORBITAL RING. Six obsidian shards float on one orbit
# round a singularity hanging at the centre (0, 50, -5); a ring road of rune bridges (and one run of floating stepping
# stones) joins them, a gravity lift climbs from the spawn shard to a high Starwatch shard. No ground, no sea: void below.
#   S  spawn shard (0, 130)  - spawn dais, overlook promontory pointing at the singularity, lift up to Starwatch
#   SW Merchant shard        - Void Merchant (shop)          SE Altar shard   - Ascension Altar (upgrades)
#   W  Seer shard            - Seer's Lectern (quests)        E  Rift shard    - the Rift Gate (portal, hero 2)
#   N  Arena shard (0, -140) - walled PvP / boss arena on the far side of the singularity, framed by it from spawn
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import void_props as VP
F = VP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, ribbon, hull

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

# ------------------------------------------------------------------ layout
SING = (0.0, 50.0, -5.0)
#            key       x      z     y     R   seed  promontory (angle deg in Roblox xz: 0 = +X, -90 = north), length
ISL = {
    'Spawn':  (0.0, 130.0, 0.0, 32.0, 1, (-90, 16)),
    'Shop':   (-110.0, 72.0, 5.0, 25.0, 2, None),
    'Altar':  (110.0, 72.0, 5.0, 25.0, 3, None),
    'Seer':   (-130.0, -48.0, 12.0, 26.0, 4, None),
    'Rift':   (132.0, -48.0, 12.0, 31.0, 5, (180, 6)),
    'Arena':  (0.0, -142.0, 20.0, 46.0, 6, None),
    'Star':   (-40.0, 140.0, 60.0, 19.0, 7, None),
}
def ang(a, b): return math.atan2(b[1] - a[1], b[0] - a[0])
def Rfun(k, th):
    x, z, y, R, seed, prom = ISL[k]
    r = R * (1 + .09 * math.sin(3 * th + seed) + .06 * math.sin(5 * th + seed * 2.3) + .035 * math.sin(11 * th + seed))
    if prom:
        d = (th - math.radians(prom[0]) + math.pi) % math.tau - math.pi
        r += prom[1] * math.exp(-(d / .28) ** 2)
    return r
def island_of(x, z, m=0.0):
    for k, (cx, cz, y, R, s, p) in ISL.items():
        d = math.hypot(x - cx, z - cz)
        if d < Rfun(k, math.atan2(z - cz, x - cx)) - m: return k
    return None
def top_y(k, x, z):
    return ISL[k][2] + (nz(x, 0, z, 14, ISL[k][4]) - .5) * .5
def H(x, z):
    k = island_of(x, z)
    return top_y(k, x, z) if k else None

# ------------------------------------------------------------------ instancing
KIT_NAMES = set(); NAME2KEY = {}
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; STATIC_TRIS = {}; LOG = []
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
        FOOT[key] = min(r, 14.0)
    return FOOT[key]
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props', need=True, rot=None, bed=None):
    """ground on the LOWEST footprint point (all footprint samples must be on the island, else skip); rot = optional
    3x3 Roblox-space rotation instead of the yaw"""
    meshes = kit(key, fn)
    if y is None:
        fr = foot(key) * s
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        if any(h is None for h in hs):
            if need: print('SKIP off-island', key, round(x), round(z))
            return None
        y = min(hs) - sink * s
        if bed is not None: y = min(hs) - LOWZ(key) * s - bed                 # lowest point just `bed` under the ground
    R = rot if rot is not None else Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]; LOG.append((key, x, y, z, s))
    NAME2KEY[next(iter(meshes.values())).name.split('_Glow_')[0].split('.')[0]] = key
    return y
def LOWZ(key): return min(v.co.z for me in LIB[key][0].values() for v in me.vertices)
DIRS6 = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
def clip_frac(key, M, bvh):
    """share of a placed kit prop's body (above its lowest 15%) inside the solid in bvh (the exporter's test)"""
    pts = [M @ v.co for me in LIB[key][0].values() for v in me.vertices]; pts = pts[::max(1, len(pts) // 160)]
    lo = min(q.z for q in pts); hi = max(q.z for q in pts)
    body = [q for q in pts if q.z > lo + max(.6, .15 * (hi - lo))]
    def ins(q):
        n = 0
        for d in DIRS6:
            h = bvh.ray_cast(q, d, 400)
            if h[0] is not None and h[1].dot(d) > 0: n += 1
        return n >= 5
    return sum(1 for q in body if ins(q)) / max(1, len(body))
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def placed_mb(src, x, y, z, yaw):
    """copy a prop part (Roblox-space MB) to its world placement, for walkable pieces kept as static ground"""
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y'); out = MB()
    out.V = [tuple(R @ Vector(v) + Vector((x, y, z))) for v in src.V]; out.F = list(src.F); out.UV = list(src.UV); out.SM = list(src.SM)
    return out
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris
    return ob
ANCHORS = []
def anchor(name, kind, p, yaw=0.0, size=(4, 1, 4), group=None, attrs=None):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group or kind, 'pos': [round(p[0], 2), round(p[1], 2), round(p[2], 2)],
                    'yaw': round(yaw % 360, 1), 'size': [round(v, 2) for v in size], 'attrs': attrs or {}})

# ------------------------------------------------------------------ the shards (static: walkable top + faceted keel)
NS = 96; NR = 10
def keel_profile(t):
    """underside depth (fraction of R) at ring t (0 = rim, 1 = tip)"""
    return .12 + 1.15 * t ** 1.35
def island(k):
    cx, cz, y0, R, seed, prom = ISL[k]
    rng = random.Random(seed * 7)
    bm = bmesh.new(); top = []
    for i in range(NR + 1):
        t = (i / NR) ** .8; ring = []
        for j in range(NS):
            th = j * math.tau / NS; r = Rfun(k, th) * t
            x, z = cx + math.cos(th) * r, cz + math.sin(th) * r
            y = top_y(k, x, z) if i < NR else y0 + .25
            ring.append(bm.verts.new((x, y, z)) if i else None)
        top.append(ring)
    ctr = bm.verts.new((cx, top_y(k, cx, cz), cz))
    for j in range(NS):
        bm.faces.new((ctr, top[1][(j + 1) % NS], top[1][j]))
    for i in range(1, NR):
        for j in range(NS):
            bm.faces.new((top[i][j], top[i][(j + 1) % NS], top[i + 1][(j + 1) % NS], top[i + 1][j]))
    U = {c: VP.PAL.u(c) for c in ('crust', 'turf', 'obsid')}
    def tsh(f):
        c = f.calc_center_median(); n = nz(c.x, 0, c.z, 22, seed); n2 = nz(c.x, 0, c.z, 6, seed + 3)
        col = 'turf' if n > .62 else 'crust'; u = U[col]
        return [(u, clamp(.42 + (nz(l.vert.co.x, 0, l.vert.co.z, 9, seed) - .5) * .3 + (n2 - .5) * .12)) for l in f.loops]
    mb = MB(); mb.add(bm, tsh, smooth=False)
    # keel: lip ring then rings shrinking to a tip, strong radial jag = shattered facets
    kb = bmesh.new(); rings = []
    NK = 7; NSK = NS // 2
    for i in range(NK + 1):
        ring = []
        for j in range(NSK):
            th = j * math.tau / NSK
            if i == 0: r = Rfun(k, th); y = y0 + .25
            else:
                t = i / NK
                jag = 1 + .22 * (nz(math.cos(th) * 3, i * .9, math.sin(th) * 3, .6, seed) - .5) * 2 + (.12 if (j + i) % 3 == 0 else 0)
                r = Rfun(k, th) * (1 - t ** .9) * jag * (1.04 if i == 1 else 1)
                y = y0 - R * keel_profile(t) * (1 + .25 * (nz(math.cos(th) * 2, 0, math.sin(th) * 2, .7, seed + 9) - .5))
                if i == 1: y = y0 - 1.3 - rng.uniform(0, .8)
            ring.append(kb.verts.new((cx + math.cos(th) * r, y, cz + math.sin(th) * r)))
        rings.append(ring)
    tip = kb.verts.new((cx + rng.uniform(-2, 2), y0 - R * 1.5, cz + rng.uniform(-2, 2)))
    for i in range(NK):
        for j in range(NSK):
            kb.faces.new((rings[i][(j + 1) % NSK], rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % NSK]))
    for j in range(NSK): kb.faces.new((rings[NK][(j + 1) % NSK], rings[NK][j], tip))
    bmesh.ops.recalc_face_normals(kb, faces=list(kb.faces))
    for f in kb.faces:                                                     # outward normals
        c = f.calc_center_median(); d = Vector((c.x - cx, 0, c.z - cz))
        if f.normal.dot(d) < 0 and f.normal.y < .5: f.normal_flip()
    mb.add(kb, VP.V('obsid', y0 - R * 1.4, y0, .08, .62, nk=.14, ns=6, seed=seed))
    for s_ in range(4 + int(R / 10)):                                      # stalactite spikes under the keel
        th = rng.uniform(0, math.tau); r = R * rng.uniform(.15, .55); x, z = cx + math.cos(th) * r, cz + math.sin(th) * r
        tt = 1 - r / R; yb = y0 - R * keel_profile(min(1, tt)) * .9 + 1.0
        L = R * rng.uniform(.35, .7); w = R * rng.uniform(.08, .14)
        pts = [Vector((x + math.cos(a) * w, yb, z + math.sin(a) * w)) for a in [q * math.tau / 5 + th for q in range(5)]] + [Vector((x + rng.uniform(-1, 1), yb - L, z + rng.uniform(-1, 1)))]
        mb.add(hull(pts), VP.FS('obsid', .25, .3, .1, s_))
    static('Ground_Shard%s' % k, mb, 'Shards')
    return R

# ------------------------------------------------------------------ paths (rune paving ribbons on the shards)
PATHS = []
def path(pts, w=6.0):
    PATHS.append((pts, w))
def build_paths():
    u = VP.PAL.u('pave'); mb = MB()
    for pts, w in PATHS:
        dense = []
        for a, b in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.5))
            for i in range(n): dense.append((lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)))
        dense.append(pts[-1])
        P3 = []
        for x, z in dense:
            h = H(x, z)
            if h is None: continue
            P3.append((x, h + .14, z))
        if len(P3) < 2: continue
        bm = ribbon(P3, w)
        mb.add(bm, lambda f: [(u, clamp(.5 + (nz(l.vert.co.x, 0, l.vert.co.z, 5, 2) - .5) * .2)) for l in f.loops])
        for x, z in dense: reserve(x, z, w / 2 + .5)
    static('Paving_Paths', mb, 'Paths')

def edge_pt(k, toward, inset=4.0):
    cx, cz = ISL[k][0], ISL[k][1]; th = math.atan2(toward[1] - cz, toward[0] - cx)
    r = Rfun(k, th) - inset
    return (cx + math.cos(th) * r, cz + math.sin(th) * r)

def inner(k, p, f):
    cx, cz = ISL[k][0], ISL[k][1]; return (cx + (p[0] - cx) * f, cz + (p[1] - cz) * f)

STEPS = MB()
BRIDGES = [('Spawn', 'Shop'), ('Spawn', 'Altar'), ('Shop', 'Seer'), ('Seer', 'Arena'), ('Rift', 'Arena')]
def bridges():
    for i, (a, b) in enumerate(BRIDGES):
        A = edge_pt(a, ISL[b][:2]); Bp = edge_pt(b, ISL[a][:2])
        ya, yb = H(*A), H(*Bp)
        L = math.hypot(Bp[0] - A[0], Bp[1] - A[1]); mx, mz = (A[0] + Bp[0]) / 2, (A[1] + Bp[1]) / 2
        key = 'RuneBridge%s%s' % (a, b)
        yaw_, yy = face(A[0], A[1], Bp[0], Bp[1]), (ya + yb) / 2 + .05
        place(key, lambda L=L, d=yb - ya, i=i: VP.rune_bridge(L, d, 9.0, 10 + i, key), mx, mz, yaw_, y=yy, group='Bridges')
        # the walkable deck (slabs + curbs) is static ground like the shards it joins; keels / posts / runes stay the prop
        static(key.replace('RuneBridge', 'RuneBridgeDeck'), placed_mb(VP.rune_bridge(L, yb - ya, 9.0, 10 + i, key, part='deck').solid, mx, yy, mz, yaw_), 'Bridges')
        for p, k in ((A, a), (Bp, b)): path([p, inner(k, p, .42)], 7.0)
        if a == 'Spawn' and b == 'Altar':                                                   # ruined gateway arch over each spawn bridge head
            q = inner('Spawn', A, .86); place('VoidArch', VP.void_arch, q[0], q[1], face(q[0], q[1], Bp[0], Bp[1]), y=H(*q) - .3, group='Spawn'); reserve(q[0], q[1], 9)
        SPANS.append((A, Bp, (ya + yb) / 2))
        anchor('Bridge_%s_%s' % (a, b), 'bridge', (mx, (ya + yb) / 2 + 3, mz), face(A[0], A[1], Bp[0], Bp[1]), (9, 6, L), 'Paths')
    # Altar -> Rift: floating stepping stones (jump run, gaps ~2 studs, rises 7)
    A = edge_pt('Altar', ISL['Rift'][:2], 2.5); Bp = edge_pt('Rift', ISL['Altar'][:2], 2.5)
    ya, yb = H(*A), H(*Bp); L = math.hypot(Bp[0] - A[0], Bp[1] - A[1]); n = int(L / 8.2); SPANS.append((A, Bp, (ya + yb) / 2))
    for i in range(1, n):
        t = i / n; x, z = lerp(A[0], Bp[0], t), lerp(A[1], Bp[1], t)
        dx, dz = (Bp[1] - A[1]) / L, -(Bp[0] - A[0]) / L; off = math.sin(i * 1.7) * 2.2
        x += dx * off; z += dz * off; y = lerp(ya, yb, t) + math.sin(t * math.pi) * 2.0
        place('StepStone%d' % (i % 3), lambda s=i % 3: VP.step_stone(s + 1, 3.4), x, z, i * 37, y=y, group='Bridges')
        STEPS.merge(placed_mb(VP.step_stone(i % 3 + 1, 3.4, part='top').solid, x, y, z, i * 37))      # walkable top = static ground
        anchor('Step%02d' % i, 'stepstone', (x, y + .5, z), 0, (6.5, 1, 6.5), 'Paths', {'Order': i})
    path([A, inner('Altar', A, .42)], 6.0); path([Bp, inner('Rift', Bp, .5)], 6.0)
    static('Ground_ShardSteps', STEPS, 'Bridges')

# ------------------------------------------------------------------ stations + set pieces
def stations():
    # spawn shard
    sx, sz = 0.0, 140.0
    place('SpawnDais', VP.spawn_dais, sx, sz, 0, group='Spawn'); reserve(sx, sz, 13)
    anchor('SpawnLocation', 'spawn', (sx, H(sx, sz) + 1.2, sz), 0, (10, 1, 10), 'Spawn')
    path([(sx, sz - 12), (0, 104)], 7.0)
    ox, oz = 0.0, 100.0                                                  # overlook at the promontory tip
    place('OverlookCircle', lambda: VP.rune_circle(6.5, 'OverlookCircle', 4), ox, oz, 0, y=H(ox, oz) + .05, group='Spawn'); reserve(ox, oz, 7)
    for i in range(5):
        a = math.radians(-90 + (i - 2) * 22); r = Rfun('Spawn', a) - 3.2
        x, z = math.cos(a) * r, 130 + math.sin(a) * r
        place('VoidRail', VP.rail_segment, x, z, -math.degrees(a) - 90, y=H(x, z) - .1, group='Spawn'); reserve(x, z, 5)   # rim chunks keep off
    anchor('Overlook', 'viewpoint', (ox, H(ox, oz) + 3, oz), 0, (12, 6, 12), 'Spawn')
    lx, lz = -12.0, 112.0                                                # clear of the Spawn -> Shop bridge walkway + the main path
    place('LiftPad', VP.lift_pad, lx, lz, 0, sink=-.4, group='Lift'); reserve(lx, lz, 7)   # dais sits on the shard (base .3 in)
    ly = H(lx, lz)
    place('LiftBeam', VP.lift_beam, lx, lz, 0, y=ly + .1, group='Lift')
    anchor('LiftBottom', 'lift', (lx, ly + 30, lz), 0, (7, 60, 7), 'Lift', {'TargetY': 62, 'Speed': 60})
    path([(lx + .3, lz + 7.5), (sx - 11, sz)], 5.0)                       # starts past the pad rim (r 6.3)
    # starwatch shard (top of the lift)
    tx, tz = ISL['Star'][0], ISL['Star'][1]
    px, pz = tx + (lx - tx) * .33, tz + (lz - tz) * .33
    pty = min(top_y('Star', px + math.cos(a) * 6.3, pz + math.sin(a) * 6.3) for a in [k * math.tau / 8 for k in range(8)])   # Star top (Spawn lies under it)
    place('LiftPadTop', lambda: VP.lift_pad('LiftPadTop'), px, pz, 0, y=pty + .4, group='Lift'); reserve(px, pz, 7)
    anchor('LiftTop', 'lift', (px, top_y('Star', px, pz) + 2, pz), 0, (8, 4, 8), 'Lift', {'Exit': True})
    place('HeartCrystal', VP.heart_crystal, tx - 4, tz + 2, 30, group='Starwatch'); reserve(tx - 4, tz + 2, 8)
    anchor('HeartCrystal', 'secret', (tx - 4, H(tx - 4, tz + 2) + 4, tz + 2), 0, (10, 8, 10), 'Starwatch')
    # merchant (shop), altar (upgrades)
    for k, key, fn, nm in (('Shop', 'VoidMerchant', VP.shop_kiosk, 'Shop'), ('Altar', 'AscensionAltar', VP.upgrade_altar, 'Upgrades')):
        cx, cz = ISL[k][0], ISL[k][1]; yaw = face(cx, cz, 0, 120)
        place(key, fn, cx, cz, yaw, group='Stations'); reserve(cx, cz, 15)
        y = H(cx, cz); fwd = Vector((-math.sin(math.radians(yaw)), 0, -math.cos(math.radians(yaw))))
        anchor(nm + 'Sign', 'station', (cx + fwd.x * 5.6, y + 11.6, cz + fwd.z * 5.6) if k == 'Shop' else (cx, y + 20, cz), yaw, (7, 1.8, .4), 'Stations')
        anchor(nm + 'Prompt', 'prompt', (cx + fwd.x * 6, y + 3, cz + fwd.z * 6), yaw, (8, 6, 4), 'Stations', {'Station': nm})
    # seer (quests)
    cx, cz = ISL['Seer'][0], ISL['Seer'][1]; yaw = face(cx, cz, 0, -5)
    place('SeersLectern', VP.quest_stand, cx, cz, yaw, group='Stations'); reserve(cx, cz, 14)
    y = H(cx, cz); fwd = Vector((-math.sin(math.radians(yaw)), 0, -math.cos(math.radians(yaw))))
    anchor('QuestsSign', 'station', (cx - fwd.x * 5.5, y + 6.2, cz - fwd.z * 5.5), yaw, (6.4, 3.4, .4), 'Stations')
    anchor('QuestsPrompt', 'prompt', (cx + fwd.x * 3, y + 3, cz + fwd.z * 3), yaw, (6, 6, 4), 'Stations', {'Station': 'Quests'})
    # rift gate (portal, hero 2), facing the ring road / singularity
    cx, cz = ISL['Rift'][0] + 3, ISL['Rift'][1]; yaw = face(cx, cz, 0, -20)
    place('RiftGate', VP.rift_gate, cx, cz, yaw, group='Hero'); reserve(cx, cz, 22)
    y = H(cx, cz); fwd = Vector((-math.sin(math.radians(yaw)), 0, -math.cos(math.radians(yaw))))
    anchor('RiftGateSign', 'station', (cx, y + 38, cz), yaw, (10, 2, .4), 'Stations')
    anchor('PortalTrigger', 'portal', (cx, y + 17.6, cz), yaw, (22, 24, 3), 'Stations', {'Destination': ''})
    path([(cx + fwd.x * 10, cz + fwd.z * 10), (cx + fwd.x * 22, cz + fwd.z * 22)], 7.0)
    # arena
    cx, cz = ISL['Arena'][0], ISL['Arena'][1]; y = ISL['Arena'][2]
    gW = math.degrees(ang((cx, cz), ISL['Seer'][:2])); gE = math.degrees(ang((cx, cz), ISL['Rift'][:2]))
    place('ArenaRim', lambda: VP.arena_rim(34.0, (gW, gE, 90)), cx, cz, 0, y=y - .1, group='Arena'); reserve(cx, cz, 36)
    place('ArenaCircle', lambda: VP.rune_circle(20.0, 'ArenaCircle', 6), cx, cz, 0, y=H(cx, cz) + .06, group='Arena')
    anchor('ArenaBounds', 'arena', (cx, y + 10, cz), 0, (66, 20, 66), 'Arena')
    for i in range(4):
        a = i * math.tau / 4 + math.pi / 4
        anchor('ArenaSpawn%d' % (i + 1), 'arenaspawn', (cx + math.cos(a) * 24, y + 1, cz + math.sin(a) * 24), face(cx + math.cos(a) * 24, cz + math.sin(a) * 24, cx, cz), (4, 1, 4), 'Arena')
        place('VoidBrazier', VP.brazier, cx + math.cos(a) * 29, cz + math.sin(a) * 29, 0, group='Arena')
    anchor('ArenaSign', 'station', (cx, y + 14, cz + 34), 0, (10, 2, .4), 'Stations')
    for i, a in enumerate((200, 235, 305, 340, 270)):                      # pillar colonnade outside the rim (north half)
        r = min(39.5, Rfun('Arena', math.radians(a)) - 5.5); x, z = cx + math.cos(math.radians(a)) * r, cz + math.sin(math.radians(a)) * r
        if i % 2: place('Pillar1', lambda: VP.pillar(1, 18, False), x, z, a, group='Arena')
        else: place('PillarBroken%d' % (i % 3 + 1), lambda i=i: VP.pillar(i % 3 + 1), x, z, a, group='Arena')
        reserve(x, z, 4.5)
    # singularity (hero 1)
    place('OrbitSingularity', VP.singularity, SING[0], SING[2], 0, y=SING[1], group='Hero')
    anchor('SingularityCore', 'hazard', SING, 0, (44, 44, 44), 'Hero', {'Note': 'pull / damage zone around the core'})

# ------------------------------------------------------------------ dressing
def ring_scatter(k, items, rng, rmin=.35, rmax=.86, tries=60):
    cx, cz = ISL[k][0], ISL[k][1]
    for key, fn, fr, s in items:
        for _ in range(tries):
            th = rng.uniform(0, math.tau); r = Rfun(k, th) * rng.uniform(rmin, rmax)
            x, z = cx + math.cos(th) * r, cz + math.sin(th) * r
            if not free(x, z, fr): continue
            lo_ = key.startswith(('CrystalChips', 'VoidGrass', 'Rubble'))                  # low ground cover: only its base in the ground
            if place(key, fn, x, z, rng.uniform(0, 360), s, bed=.3 if lo_ else None, group='Dressing', need=False) is None: continue
            reserve(x, z, fr); break

def dressing(rng):
    CV = [('CrystalViolet%d' % i, (lambda i=i: VP.crystal_cluster(i, 1.0, 'violet')), 6.5) for i in (1, 3)]   # seat + rubble reach ~6
    CC = [('CrystalCyan%d' % i, (lambda i=i: VP.crystal_cluster(i, 1.0, 'cyan')), 6.5) for i in (2, 4)]
    TE = [('VoidTendril%d' % i, (lambda i=i: VP.tendril(i)), 3.5) for i in (1, 2)]
    SP = [('SporePods%d' % i, (lambda i=i: VP.spore_pods(i)), 3.5) for i in (1, 2)]
    RU = [('Rubble%d' % i, (lambda i=i: VP.rubble(i)), 3.5) for i in (1, 2)]
    PB = [('PillarBroken%d' % i, (lambda i=i: VP.pillar(i)), 4.5) for i in (1, 2)]
    LN = ('CrystalLantern', VP.crystal_lantern, 1.5)
    def pick(lst, i): return lst[i % len(lst)]
    plan = {   # per shard: (crystals, flora, ruins, arches)
        'Spawn': (6, 9, 3, 0), 'Shop': (5, 8, 3, 0), 'Altar': (5, 8, 3, 0), 'Seer': (5, 8, 3, 1), 'Rift': (6, 8, 3, 0),
        'Arena': (0, 0, 0, 0), 'Star': (2, 5, 1, 1)}
    for k, (nc, nf, nr, na) in plan.items():
        items = []
        for i in range(nc):
            key, fn, fr = pick(CV if i % 2 == 0 else CC, i // 2 + ISL[k][4]); items.append((key, fn, fr, rng.uniform(.8, 1.3)))
        for i in range(nf):
            key, fn, fr = pick(TE if i % 2 else SP, i + ISL[k][4]); items.append((key, fn, fr, rng.uniform(.8, 1.2)))
        for i in range(nr):
            key, fn, fr = pick(RU if i % 2 else PB, i + ISL[k][4]); items.append((key, fn, fr, 1.0))
        for i in range(na): items.append(('VoidArch', VP.void_arch, 11, 1.0))
        ring_scatter(k, items, rng, .45 if k != 'Star' else .2, .86)
    # arena outer ring: crystals + flora between rim (34) and edge
    ring_scatter('Arena', [(pick(CV + CC, i)[0], pick(CV + CC, i)[1], 4, 1.1) for i in range(5)] + [(pick(SP + TE, i)[0], pick(SP + TE, i)[1], 3, 1.0) for i in range(4)], rng, .8, .92, 120)
    # ground cover: crystal chips + void grass tufts, small footprints, many
    for k in ISL:
        if k == 'Arena': continue
        nn = int(ISL[k][3] * .9)
        ring_scatter(k, [(('CrystalChips%d' % (i % 3)), (lambda i=i: VP.crystal_chips(i % 3 + 1)), 1.4, rng.uniform(.8, 1.3)) if i % 2 else
                         (('VoidGrass%d' % (i % 3)), (lambda i=i: VP.void_grass(i % 3 + 1)), 1.0, rng.uniform(.9, 1.4)) for i in range(nn)], rng, .25, .9, 30)
    ring_scatter('Arena', [('VoidGrass%d' % (i % 3), (lambda i=i: VP.void_grass(i % 3 + 1)), 1.0, 1.1) for i in range(16)], rng, .8, .93, 40)
    # crystal spires: big clusters set on shard edges as landmarks (never on paths)
    for k, th in (('Shop', 200), ('Seer', 160), ('Rift', 20), ('Altar', 330), ('Arena', 250), ('Arena', 300), ('Spawn', 150), ('Spawn', 35)):
        cx, cz = ISL[k][0], ISL[k][1]; a = math.radians(th); r = Rfun(k, a) - 9
        x, z = cx + math.cos(a) * r, cz + math.sin(a) * r
        if free(x, z, 6):
            key = 'CrystalSpire%d' % (len([1 for q in COUNT if q.startswith('CrystalSpire')]) % 2)
            if place(key, (lambda: VP.crystal_cluster(31, 2.0, 'violet', 'CrystalSpire0')) if key.endswith('0') else (lambda: VP.crystal_cluster(32, 2.0, 'cyan', 'CrystalSpire1')), x, z, th, 1.0, group='Dressing', need=False):
                reserve(x, z, 8)
    # lanterns along every path, every ~14 studs, offset to the side
    for pts, w in PATHS:
        acc = 0.0
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 14)
            for i in range(1, n + 1):
                t = i / (n + 1); x, z = lerp(a[0], b[0], t), lerp(a[1], b[1], t)
                nx, nz_ = -(b[1] - a[1]) / L, (b[0] - a[0]) / L; sd = 1 if (i % 2) else -1
                px, pz = x + nx * sd * (w / 2 + 1.6), z + nz_ * sd * (w / 2 + 1.6)
                if island_of(px, pz, 3) and free(px, pz, 1.5):
                    place(LN[0], LN[1], px, pz, face(px, pz, x, z), group='Lanterns'); reserve(px, pz, 2)
    # rim chunks: broken obsidian blocks embedded on the shard edges (grounded, sunk)
    for k in ISL:
        cx, cz, y0, R, seed, prom = ISL[k]; n = int(R / 4)
        for i in range(n):
            th = i * math.tau / n + rng.uniform(-.2, .2); r = Rfun(k, th) - 3.2; x, z = cx + math.cos(th) * r, cz + math.sin(th) * r
            if not free(x, z, 3): continue
            key = 'RimChunk%d' % (i % 3)
            place(key, lambda i=i: rim_chunk(i % 3), x, z, -math.degrees(th), rng.uniform(.8, 1.3), sink=.6, group='Rims', need=False)
    # crystals hanging under the shards (origin = top, set into the keel underside)
    for k in ISL:
        cx, cz, y0, R, seed, prom = ISL[k]
        gm = bpy.data.objects['Ground_Shard%s' % k].data
        bvh = BVHTree.FromPolygons([v.co.copy() for v in gm.vertices], [p.vertices[:] for p in gm.polygons])
        for i in range(2 if R < 20 else 3):
            key = 'CrystalHang%d' % (i % 2)
            fn = lambda i=i: VP.crystal_cluster(20 + i, 1.4, 'violet' if i % 2 else 'cyan', 'CrystalHang%d' % i, hang=True)
            top = max(v.co.z for me in kit(key, fn).values() for v in me.vertices)                # seat top above the origin
            for _t in range(16):
                th = rng.uniform(0, math.tau); r = R * rng.uniform(.2, .55)
                yw = rng.uniform(0, 360); s_ = rng.uniform(1.0, 1.6)
                x, z = cx + math.cos(th) * r, cz + math.sin(th) * r
                hit, nb, _i, _d = bvh.ray_cast(r2b((x, y0 - 3 * R, z)), Vector((0, 0, 1)), 4 * R)   # keel underside from below
                if hit is None: continue
                n = (KM.inverted() @ nb).normalized(); p = KM.inverted() @ hit                    # Roblox space, n points out of the keel
                if n.y > 0: n = -n
                rot = Vector((0, 1, 0)).rotation_difference(-n).to_matrix() @ Matrix.Rotation(math.radians(yw), 3, 'Y')
                q = p + n * (top * s_ + .3)                                                        # seat flush under the facet, grows out of it
                M = Matrix.Translation(r2b(q)) @ (KM @ rot @ KM.inverted()).to_4x4() @ Matrix.Scale(s_, 4)
                if clip_frac(key, M, bvh) > .02: continue                                          # cuts into a jag / spike: try another spot
                place(key, fn, q.x, q.z, s=s_, y=q.y, rot=rot, group='Undersides'); break

def rim_chunk(seed):
    P = VP.Prop('RimChunk%d' % seed); rng = random.Random(seed)
    P.add(VP.T(VP.shard_rock(2.6, 300 + seed, 16, flat=.2, elong=(1.3, .9, 1.0)), (0, .9, 0)), VP.FS('obsid', .36, .35, .08, seed))
    P.add(VP.T(VP.shard_rock(1.3, 310 + seed, 10, flat=.3), (2.0, .3, 1.0)), VP.FS('obsid', .4, .35, .08, seed))
    P.gadd(VP.T(VP.shaft(.32, 1.8, seed + 5, 5, base=-.2), (-.8, 1.8, -.4), pitch=24, yaw=rng.uniform(0, 360)), 'violet' if seed % 2 else 'cyan')
    return P

FAR = []
SPANS = []                                                                  # (a, b, y) bridge + step-run lines
def seg_d(x, z, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dz * dz or 1.0
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (z - a[1]) * dz) / L2))
    return math.hypot(x - a[0] - t * dx, z - a[1] - t * dz)
def void_debris(rng):
    """intentional floaters: chips drifting near the shards and between them, far silhouettes on the horizon"""
    n = 0
    while n < 42:
        a = rng.uniform(0, math.tau); r = rng.uniform(70, 230); x, z = math.cos(a) * r, math.sin(a) * r - 5
        y = rng.uniform(-40, 70)
        if island_of(x, z, -22): continue
        if math.hypot(x - SING[0], z - SING[2]) < 85 and abs(y - SING[1]) < 40: continue
        if any(seg_d(x, z, a_, b_) < 16 and abs(y - ya_) < 22 for a_, b_, ya_ in SPANS): continue   # not through a bridge / step run
        place('DebrisShard%d' % (n % 4), lambda s=n % 4: VP.float_shard(s + 1, 1.0), x, z, rng.uniform(0, 360), rng.uniform(.8, 2.4), y=y, group='Debris')
        n += 1
    for i in range(9):                                                     # under-tier: big broken chunks far below the ring
        a = i * math.tau / 9 + rng.uniform(-.2, .2); r = rng.uniform(90, 210)
        place('DebrisShard%d' % (i % 4), lambda s=i % 4: VP.float_shard(s + 1, 1.0), math.cos(a) * r, math.sin(a) * r - 5, rng.uniform(0, 360), rng.uniform(3.5, 6.0), y=rng.uniform(-260, -180), group='Debris')
    for i in range(40):
        a = i * math.tau / 40 + rng.uniform(-.08, .08); r = rng.uniform(380, 820)
        yw, sc, yy = rng.uniform(0, 360), rng.uniform(4, 9), rng.uniform(-220, 180)
        x, z = math.cos(a) * r, math.sin(a) * r
        if any((x - qx) ** 2 + (yy - qy) ** 2 + (z - qz) ** 2 < (14 * (sc + qs)) ** 2 for qx, qy, qz, qs in FAR): continue   # silhouettes never overlap
        FAR.append((x, yy, z, sc))
        place('FarDebris%d' % (i % 3), lambda s=i % 3: VP.far_rock(s + 1), x, z, yw, sc, y=yy, group='Backdrop')

# ------------------------------------------------------------------ look: endless starry void, violet nebula, glow
HAZE = (.00018, .0)
def look():
    w = bpy.data.worlds.new('Void'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']; L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.004, .002, .012, 1)
    cr.elements[1].position = .62; cr.elements[1].color = (.006, .004, .02, 1)
    e = cr.elements.new(.47); e.color = (.03, .012, .07, 1)                  # faint violet band at the horizon
    L.new(sep.outputs['Z'], ramp.inputs['Fac'])
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 220; L.new(tc.outputs['Generated'], vor.inputs['Vector'])
    st = nt.nodes.new('ShaderNodeMapRange'); st.inputs['From Min'].default_value = .0; st.inputs['From Max'].default_value = .06
    st.inputs['To Min'].default_value = 1.0; st.inputs['To Max'].default_value = 0.0; st.clamp = True
    L.new(vor.outputs['Distance'], st.inputs['Value'])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 6; L.new(st.outputs[0], pw.inputs[0])
    stc = nt.nodes.new('ShaderNodeMath'); stc.operation = 'MULTIPLY'; stc.inputs[1].default_value = 3.0; L.new(pw.outputs[0], stc.inputs[0])
    neb = nt.nodes.new('ShaderNodeTexNoise'); neb.inputs['Scale'].default_value = 2.2; neb.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Generated'], neb.inputs['Vector'])
    nr = nt.nodes.new('ShaderNodeValToRGB'); c2 = nr.color_ramp
    c2.elements[0].position = .5; c2.elements[0].color = (0, 0, 0, 1); c2.elements[1].position = .78; c2.elements[1].color = (.16, .02, .2, 1)
    e2 = c2.elements.new(.66); e2.color = (.03, .02, .14, 1)
    L.new(neb.outputs['Fac'], nr.inputs['Fac'])
    a1 = nt.nodes.new('ShaderNodeMixRGB'); a1.blend_type = 'ADD'; a1.inputs['Fac'].default_value = 1; L.new(ramp.outputs['Color'], a1.inputs[1]); L.new(nr.outputs['Color'], a1.inputs[2])
    a2 = nt.nodes.new('ShaderNodeMixRGB'); a2.blend_type = 'ADD'; a2.inputs['Fac'].default_value = 1; L.new(a1.outputs['Color'], a2.inputs[1])
    cv = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(stc.outputs[0], cv.inputs[0]); L.new(stc.outputs[0], cv.inputs[1]); L.new(stc.outputs[0], cv.inputs[2])
    L.new(cv.outputs[0], a2.inputs[2]); L.new(a2.outputs['Color'], bg.inputs[0]); bg.inputs[1].default_value = 1.0
    # ambient fill as its own light (world stays dark for the stars)
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .25; b.inputs['Roughness'].default_value = .7
    def sun(name, el, az, e, col, shadow=True, ang_=4):
        s = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); SC.collection.objects.link(s)
        s.data.energy = e; s.data.color = col; s.data.angle = math.radians(ang_); s.data.use_shadow = shadow
        el, az = math.radians(el), math.radians(az)
        to = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
        s.rotation_euler = (-to).to_track_quat('-Z', 'Y').to_euler()
    sun('Key', 38, 215, 2.6, (.78, .72, 1.0))                               # cool lavender key from the south-west
    sun('Rim', 22, 20, 3.0, (.35, .9, 1.0), shadow=False)                   # cyan rim from the north-east (behind the hero)
    sun('Fill', 70, 120, .9, (.55, .35, .9), shadow=False)                  # violet top fill
    pl = bpy.data.objects.new('SingLight', bpy.data.lights.new('SingLight', 'POINT')); SC.collection.objects.link(pl)
    pl.data.energy = 6.0e6; pl.data.color = (1.0, .35, .9); pl.data.shadow_soft_size = 30; pl.location = r2b(SING); pl.data.use_shadow = False; pl.data.volume_factor = 0.0
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    SC.view_settings.exposure = .3
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    for k, v in (('volumetric_tile_size', '8'), ('volumetric_end', 1400.0), ('volumetric_start', 1.0), ('volumetric_samples', 48)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (2400, 2400, 900); hz.location = (0, 0, 0); FXC.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = HAZE[0]
    pv.inputs['Color'].default_value = (.35, .18, .9, 1); pv.inputs['Absorption Color'].default_value = (.85, .8, 1.0, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False
    # spore motes (preview; Roblox = ParticleEmitter, see SETUP.md)
    mm = bpy.data.materials.new('Mote'); mm.use_nodes = True; mb_ = mm.node_tree.nodes['Principled BSDF']
    mb_.inputs['Emission Color'].default_value = (1.0, .5, 1.0, 1); mb_.inputs['Emission Strength'].default_value = 40
    rng = random.Random(77)
    for k_ in range(120):
        x, z = rng.uniform(-170, 170), rng.uniform(-190, 170); y = rng.uniform(-10, 70)
        me = bpy.data.meshes.new('Mote'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(.25, .5)); bm.to_mesh(me); bm.free()
        me.materials.append(mm); ob = bpy.data.objects.new('Mote', me); ob.location = r2b((x, y, z)); FXC.objects.link(ob); ob.visible_shadow = False

def shot(name, loc, tgt, fov=50, res=(1920, 1032)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SHOTS = {
    'map_beauty.png': ((46, 34, 214), (0, 34, -30), 56),
    'map_overview.png': ((-300, 250, 300), (0, 0, -15), 44),
    'map_top.png': ((0, 900, 1), (0, 0, -5), 32),
    'map_spawn.png': ((0, 8.5, 152), (0, 36, -10), 64),
    'map_arena.png': ((-60, 46, -70), (0, 18, -142), 55),
    'map_rift.png': ((60, 24, -30), (132, 26, -48), 58),
    'map_shop.png': ((-80, 14, 100), (-110, 10, 72), 55),
    'map_altar.png': ((80, 14, 100), (110, 12, 72), 55),
    'map_seer.png': ((-100, 20, -30), (-130, 16, -48), 55),
    'map_under.png': ((-40, -30, 110), (-110, -10, 70), 60),
    'map_star.png': ((-6, 70, 118), (-40, 64, 142), 60),
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

def build():
    for k in ISL: island(k)
    for loc, _t, _f in SHOTS.values(): reserve(loc[0], loc[2], 3)
    for z in range(88, 152, 4): reserve(0, z, 6)                          # spawn -> singularity sightline stays clear
    bridges(); stations(); build_paths()
    rng = random.Random(11)
    dressing(rng); void_debris(random.Random(5))
    KIT_NAMES.update(me.name for ms, _t in LIB.values() for me in ms.values())
    for nm in validate({'Dressing', 'Lanterns', 'Rims', 'Undersides', 'Debris', 'Backdrop'}):
        k_ = NAME2KEY[nm]; COUNT[k_] -= 1; TRIS[0] -= LIB[k_][1]
    anchor('VoidKill', 'killzone', (0, -160, -5), 0, (2000, 20, 2000), 'Spawn')

build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
STATS = {'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
         'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()}}
json.dump(STATS, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'singularity': SING, 'islands': {k: v[:4] for k, v in ISL.items()}}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
json.dump(LOG, open(os.path.join(PREV, 'placements.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'void_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATS['tris_total'])
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
