# blender -b --factory-startup --python moon_map.py [-- norender] -> Moon Sweepers (moon_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: terraced crater descent (shelf rings stepping down
# to a central peak). Hub on the north rim plateau, spawn looks south (+Z) over the crater at the rocket.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import moon_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, cyl

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

# ------------------------------------------------------------------ the crater
HUB = (0.0, -338.0); HUB_R = 62.0; HUB_Y = 8.0
SPAWN = (0.0, -318.0)
#        riser centre r, upper y, lower y        (riser k drops into zone k)
RISER = [(255.0, HUB_Y, -12.0), (202.0, -12.0, -34.0), (142.0, -34.0, -58.0), (89.0, -58.0, -84.0)]
RW = 3.2                                          # riser half width (steep wall)
ZONES = {1: (205.4, 251.0, -12.0), 2: (145.4, 198.6, -34.0), 3: (92.4, 138.6, -58.0), 4: (52.0, 85.6, -84.0)}
ZNAME = {1: 'DustyPlains', 2: 'CraterField', 3: 'Junkyard', 4: 'DarkIce'}
PEAK_R, PEAK_TOP, PEAK_Y = 30.0, 48.0, -40.0     # flat top radius, cone foot radius, top height
RAMP_A = [math.radians(a) for a in (-90.0, -20.0, 65.0, 150.0)]   # ramp k angle (atan2(z, x)), spiral clockwise from the hub
RAMP_HW = 9.0                                     # ramp half width (studs)
def ramp_half_len(k): return .75 * (RISER[k][1] - RISER[k][2])
TRACK_R = {1: 229.0, 2: 172.0, 3: 116.0, 4: 63.0}  # trodden ring path mid radius per zone

CRATERS = [(155 * math.cos(math.radians(a)), 155 * math.sin(math.radians(a)), R, d) for a, R, d in []]
rng0 = random.Random(7)
for k in range(15):                               # zone 2: the crater field (avoid its ramps and the track)
    for _t in range(40):
        a = rng0.uniform(0, math.tau); r = rng0.uniform(151, 194)
        if min(abs((a - RAMP_A[i] + math.pi) % math.tau - math.pi) * r for i in (1, 2)) < 26: continue
        R = rng0.uniform(5.0, 11.0)
        if abs(r - TRACK_R[2]) < R + 3: continue
        x, z = math.cos(a) * r, math.sin(a) * r
        if all(math.hypot(x - c[0], z - c[1]) > R + c[2] + 4 for c in CRATERS):
            CRATERS.append((x, z, R, R * rng0.uniform(.22, .32))); break
for k in range(6):                                # a few in zone 1 and zone 3
    for _t in range(40):
        zk = 1 if k < 3 else 3
        a = rng0.uniform(0, math.tau); lo, hi, _y = ZONES[zk]; r = rng0.uniform(lo + 9, hi - 9)
        if min(abs((a - RAMP_A[i] + math.pi) % math.tau - math.pi) * r for i in range(4)) < 26: continue
        R = rng0.uniform(4.0, 7.0)
        if abs(r - TRACK_R[zk]) < R + 3: continue
        x, z = math.cos(a) * r, math.sin(a) * r
        if all(math.hypot(x - c[0], z - c[1]) > R + c[2] + 4 for c in CRATERS):
            CRATERS.append((x, z, R, R * .25)); break

def adiff(a, b): return abs((a - b + math.pi) % math.tau - math.pi)
POCKS = []                                        # small impact pocks: regolith roughing everywhere on the shelves
rngp = random.Random(11)
for _t in range(2600):
    zk = rngp.choice((1, 1, 2, 2, 3, 4)); lo, hi, _y = ZONES[zk]
    a = rngp.uniform(0, math.tau); r = rngp.uniform(lo + 4, hi - 4); R = rngp.uniform(2.2, 5.5)
    if abs(r - TRACK_R[zk]) < R + 4.5: continue
    if min(adiff(a, RAMP_A[i]) * r for i in range(4)) < RAMP_HW + R + 6: continue
    x, z = math.cos(a) * r, math.sin(a) * r
    if any(math.hypot(x - c[0], z - c[1]) < R + c[2] * 1.6 for c in CRATERS): continue
    if any(math.hypot(x - c[0], z - c[1]) < R + c[2] for c in POCKS): continue
    POCKS.append((x, z, R, R * rngp.uniform(.16, .26)))
    if len(POCKS) >= 150: break

def profile(r, a):
    """crater height before ramps / sub-craters"""
    if r >= RISER[0][0] + RW:                                                   # outside: rim crest, hub plateau, plains
        hubw = smooth(1 - (math.hypot(math.cos(a) * r - HUB[0], math.sin(a) * r - HUB[1]) - HUB_R) / 26)
        crest = 9.0 * math.exp(-((r - 270) / 14) ** 2) + 6.0 - 6.0 * smooth((r - 300) / 220)
        crest += ((nz(math.cos(a) * r, 0, math.sin(a) * r, 40, 3) - .5) * 9 + (nz(math.cos(a) * r, 0, math.sin(a) * r, 11, 4) - .5) * 3) * smooth((r - 260) / 14)
        return lerp(crest, HUB_Y, hubw)
    if r <= PEAK_TOP: return PEAK_Y if r <= PEAK_R else lerp(PEAK_Y, -84.0, smooth((r - PEAK_R) / (PEAK_TOP - PEAK_R)) ** .8)
    for rc, yu, yl in RISER:
        if r > rc - RW:
            if r >= rc + RW: return yu
            return lerp(yl, yu, smooth((r - (rc - RW)) / (2 * RW)))
    return -84.0

def _crater_ok(c):
    """the crater prop's skirt (1.8 R) must stay on its shelf, off the trodden path and the ramps"""
    x, z, R, _d = c; r = math.hypot(x, z); a = math.atan2(z, x); k = zone_of(r)
    if not k: return False
    lo, hi, _y = ZONES[k]
    if r - 1.8 * R < lo + 2 or r + 1.8 * R > hi - 2 or abs(r - TRACK_R[k]) < 1.8 * R + 3.5: return False
    return min(adiff(a, RAMP_A[i]) * r for i in range(4)) > RAMP_HW + 1.8 * R + 6

def ramp_w(r, a, k):
    """weight 0..1 of ramp k at (r, a) and the ramp height there"""
    rc, yu, yl = RISER[k]; L = ramp_half_len(k)
    if abs(r - rc) > L + 4: return 0.0, 0.0
    t = adiff(a, RAMP_A[k]) * r
    w = smooth((RAMP_HW + 4 - t) / 4)
    if w <= 0: return 0.0, 0.0
    w *= smooth((L + 4 - abs(r - rc)) / 4) if abs(r - rc) > L else 1.0
    y = lerp(yl, yu, clamp((r - (rc - L)) / (2 * L)))
    return w, y

def H(x, z):
    r = math.hypot(x, z); a = math.atan2(z, x)
    y = profile(r, a)
    flat = r < RISER[0][0] - RW or r > RISER[0][0] + RW
    if r < RISER[0][0] + RW and r > PEAK_TOP:                                   # shelf micro relief (not on risers)
        near = min(abs(r - rc) for rc, *_ in RISER)
        k = zone_of(r); trk = smooth((abs(r - TRACK_R[k]) - 3.5) / 3) if k else 1.0   # trodden path stays smoother
        e = smooth((near - RW - 1) / 6)
        q = pock_at(x, z); cal = 1.0 if q is None else smooth((q - 1.9) / .4)    # calm ground under modelled craters
        y += ((nz(x, 0, z, 18, 5) - .5) * 1.8 + (nz(x, 0, z, 5.5, 6) - .5) * .9 * trk * cal) * e
    c = crater_at(x, z)
    if c:                                                                        # shallow flat dish the crater prop sits in
        cx, cz, R, d = c; q = math.hypot(x - cx, z - cz) / R
        y -= .12 * R * (1 - smooth((q - .95) / .35))
    for k in range(4):
        w, yr = ramp_w(r, a, k)
        if w > 0: y = lerp(y, yr, w)
    return y

def zone_of(r):
    for k, (lo, hi, _y) in ZONES.items():
        if lo <= r <= hi: return k
    return 0
CRATERS[:] = [c for c in CRATERS if _crater_ok(c)]
POCKS[:] = [c for c in POCKS if _crater_ok(c)]
_keep = []
for c in CRATERS + POCKS:                         # crater props (skirt 1.8 R) never overlap each other
    if all(math.hypot(c[0] - o[0], c[1] - o[1]) > 1.8 * (c[2] + o[2]) + 1 for o in _keep): _keep.append(c)
CRATERS[:] = [c for c in CRATERS if c in _keep]; POCKS[:] = [c for c in POCKS if c in _keep]

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
GB = [None]
def Hm(x, z):
    """height of the built ground MESH (coarser than H): props sit on what players see"""
    if GB[0] is None:
        ob = bpy.data.objects.get('Ground_Crater')
        if ob is None: return H(x, z)
        from mathutils.bvhtree import BVHTree
        me = ob.data.copy(); me.transform(ob.matrix_world); bm = bmesh.new(); bm.from_mesh(me); GB[0] = BVHTree.FromBMesh(bm); bpy.data.meshes.remove(me)
    hit = GB[0].ray_cast(r2b((x, 600, z)), Vector((0, 0, -1)), 1200)
    return hit[0].z if hit[0] is not None else H(x, z)
def spread(x, z, r):
    hs = [Hm(x, z)] + [Hm(x + math.cos(a) * r, z + math.sin(a) * r) for a in [k * math.tau / 8 for k in range(8)]]
    return max(hs) - min(hs)
def top_of(key, fn, x, z, s=1.0):
    """highest mesh point under a prop's footprint: low flat props sit on it so no bump pokes through them"""
    kit(key, fn); fr = foot(key) * s
    return max([Hm(x, z)] + [Hm(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]])
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
def tang_yaw(a): return math.degrees(math.atan2(math.sin(a), -math.cos(a))) * -1 + 0.0
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def polar(r, a): return math.cos(a) * r, math.sin(a) * r
def on_ramp(x, z, m=6.0):
    r = math.hypot(x, z); a = math.atan2(z, x)
    for k in range(4):
        rc = RISER[k][0]; L = ramp_half_len(k)
        if abs(r - rc) < L + 14 + m and adiff(a, RAMP_A[k]) * r < RAMP_HW + m: return True
    return False
def near_riser(r, m): return any(abs(r - rc) < RW + m for rc, *_ in RISER) or r < PEAK_TOP + m

# ------------------------------------------------------------------ ground (polar grid, fine at risers) + horizon skirt
def radial_samples(r0, r1):
    out = [r0]; r = r0
    while r < r1:
        fine = any(abs(r - rc) < 10 for rc, *_ in RISER) or abs(r - PEAK_TOP) < 10 or abs(r - PEAK_R) < 6 or 262 < r < 300
        r = min(r1, r + (1.6 if fine else 3.2 if r < 262 else 5.0)); out.append(r)   # 150k static budget
    return out

PGRID = {}
def crater_at(x, z):
    best = None; bq = 9
    pock_at(x, z)
    for c in PGRID.get((int(x // 12), int(z // 12)), ()):
        q = math.hypot(x - c[0], z - c[1]) / c[2]
        if q < 1.3 and q < bq: best, bq = c, q
    return best

def pock_at(x, z):
    """(q, depth) of the nearest pock / crater under (x, z), q = dist / radius; None outside 1.5 R"""
    if not PGRID:
        for c in POCKS + CRATERS:
            for i in range(int((c[0] - c[2] * 1.5) // 12), int((c[0] + c[2] * 1.5) // 12) + 1):
                for j in range(int((c[1] - c[2] * 1.5) // 12), int((c[1] + c[2] * 1.5) // 12) + 1):
                    PGRID.setdefault((i, j), []).append(c)
    best = None
    for cx, cz, R, d in PGRID.get((int(x // 12), int(z // 12)), ()):
        q = math.hypot(x - cx, z - cz) / R
        if q < 1.5 and (best is None or q < best): best = q
    return best

def ground_shade(f):
    c = f.calc_center_median(); n = f.normal; r = math.hypot(c.x, c.z); a = math.atan2(c.z, c.x)
    col, v = 'regA', .56
    k = zone_of(r)
    if r > RISER[0][0] + RW:
        col, v = 'regA', .6 + (nz(c.x, 0, c.z, 30, 2) - .5) * .12
    elif k == 1: col, v = 'regA', .66 + (nz(c.x, 0, c.z, 14, 2) - .5) * .14
    elif k == 2: col, v = 'regB', .62 + (nz(c.x, 0, c.z, 12, 3) - .5) * .14
    elif k == 3: col, v = 'mare', .58 + (nz(c.x, 0, c.z, 12, 4) - .5) * .16
    elif k == 4:
        col, v = 'mare', .42
        if nz(c.x, 0, c.z, 26, 8) > .56: col, v = 'frost', .22 + (nz(c.x, 0, c.z, 12, 9) - .5) * .1
    elif r <= PEAK_TOP: col, v = 'regB', .45
    if k and abs(r - TRACK_R[k]) < 3.6 + (nz(c.x, 0, c.z, 6, 1) - .5) * 1.5:    # trodden ring path, lighter
        col, v = ('regA', .82) if k < 3 else ('regB', .74) if k == 3 else ('frost', .62)
    for kk in range(4):                                                          # ramp treads
        w, _y = ramp_w(r, a, kk)
        if w > .9:
            col = 'steel'; v = .62 if int((r - RISER[kk][0]) / 2.0) % 2 else .48
    if n.y < .55:                                                                 # riser walls: strata bands
        band = int((c.y + 200) / 3.2) % 3
        col, v = ('regB', (.46, .56, .50)[band]) if c.y > -60 else ('mare', (.58, .68, .62)[band])
    if n.y >= .55 and col != 'steel':                                            # regolith mottle + crater floors / bright rims
        v += (nz(c.x, 0, c.z, 14, 7) - .5) * .06
    u = FP.PAL.u(col)
    return [(u, clamp(v + n.y * .06, .04, .96))] * len(f.loops)

def ground():
    rs = radial_samples(0.6, 420.0); NA = 400                                 # 150k static budget
    bm = bmesh.new(); V = []
    centre = bm.verts.new((0, H(0, 0), 0))
    for r in rs:
        ring = []
        for a in [k * math.tau / NA for k in range(NA)]:
            x, z = math.cos(a) * r, math.sin(a) * r; y = H(x, z); rr = r
            for rc, yu, yl in RISER:
                if abs(r - rc) < RW and min(adiff(a, RAMP_A[i]) * r for i in range(4)) > RAMP_HW + 5:
                    t = clamp((y - yl) / (yu - yl)); w = 4 * t * (1 - t)
                    rr = r + w * ((nz(math.cos(a) * 60, y * .6, math.sin(a) * 60, 7, 3) - .5) * 5.0 + (nz(x, y, z, 2.5, 4) - .5) * 1.4)
            ring.append(bm.verts.new((math.cos(a) * rr, y, math.sin(a) * rr)))
        V.append(ring)
    for k in range(NA): bm.faces.new((centre, V[0][(k + 1) % NA], V[0][k]))
    for i in range(len(V) - 1):
        for k in range(NA): bm.faces.new((V[i][k], V[i][(k + 1) % NA], V[i + 1][(k + 1) % NA], V[i + 1][k]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); mb.add(bm, ground_shade)
    me = F.mesh_from('Ground_Crater', mb, F.materials()['pal'])
    ob = bpy.data.objects.new('Ground_Crater', me); sub('Ground').objects.link(ob)
    # horizon skirt: rolling plains + distant crater rims out to r 2600, coarse
    bm = bmesh.new(); NA2 = 128; rs2 = [420.0 * (1.12 ** i) for i in range(0, 17)]
    def Hs(x, z):
        r = math.hypot(x, z); base = lerp(H(x * 420 / r, z * 420 / r), 0.0, smooth((r - 420) / 300))
        rim = 0.0
        for cx, cz, R in ((900, -500, 260), (-1100, 300, 380), (300, 1300, 420), (-600, -1500, 300), (1500, 700, 340)):
            d = math.hypot(x - cx, z - cz) / R
            rim += 40 * math.exp(-((d - 1) / .18) ** 2) - 25 * smooth(1 - d)
        return base + rim + (nz(x, 0, z, 260, 6) - .5) * 30 * smooth((r - 500) / 400)
    V = [[bm.verts.new((math.cos(a) * r, Hs(math.cos(a) * r, math.sin(a) * r), math.sin(a) * r)) for a in [k * math.tau / NA2 for k in range(NA2)]] for r in rs2]
    for i in range(len(V) - 1):
        for k in range(NA2): bm.faces.new((V[i][k], V[i][(k + 1) % NA2], V[i + 1][(k + 1) % NA2], V[i + 1][k]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    mb = MB(); u = FP.PAL.u('regB')
    mb.add(bm, lambda f: [(u, clamp(.48 + f.normal.y * .1 + (nz(*f.calc_center_median(), 120, 4) - .5) * .2, .05, .95))] * len(f.loops))
    me = F.mesh_from('Horizon_Plains', mb, F.materials()['pal'])
    ob = bpy.data.objects.new('Horizon_Plains', me); sub('Horizon').objects.link(ob)

# ------------------------------------------------------------------ hub deck (hex tiles), static
def hub_deck():
    mb = MB(); rng = random.Random(3); s = 4.2; hw = s * math.sqrt(3) / 2
    for i in range(-20, 21):
        for j in range(-20, 21):
            x = HUB[0] + i * s * 1.5; z = HUB[1] + j * hw * 2 + (hw if i % 2 else 0)
            d = math.hypot(x - HUB[0], z - HUB[1])
            if d > HUB_R - 3: continue
            col = 'panel' if (i + j) % 3 else 'steel'
            v = .5 + rng.uniform(-.04, .04) if col == 'panel' else .58
            if math.hypot(x - SPAWN[0], z - SPAWN[1]) < 9: col, v = 'orange', .55
            mb.add(F.at(cyl(s * .96, .55, sides=6, bev=.12), (x, HUB_Y - .2, z)), F.S(col, base=v, up=.1, jit=0))
    for k in range(48):                                                         # steel rim ring
        a0, a1 = k * math.tau / 48, (k + 1) * math.tau / 48
        p0 = Vector((HUB[0] + math.cos(a0) * (HUB_R - 1), HUB_Y - .1, HUB[1] + math.sin(a0) * (HUB_R - 1)))
        p1 = Vector((HUB[0] + math.cos(a1) * (HUB_R - 1), HUB_Y - .1, HUB[1] + math.sin(a1) * (HUB_R - 1)))
        mb.add(FP.tube([p0, p1], 1.1, sides=6, flat=(1, .5)), F.S('steel', base=.35, jit=0))
    me = F.mesh_from('Hardscape_HubDeck', mb, F.materials()['pal'])
    ob = bpy.data.objects.new('Hardscape_HubDeck', me); sub('Hub').objects.link(ob)

# ------------------------------------------------------------------ build
def rail_ring(r, y_fn, skip, key, group, step=12.0):
    """the signature beacon rail along a lip: posts every `step`, cable to the next; gaps at ramps"""
    n = int(r * math.tau / step); da = math.tau / n
    for i in range(n):
        a = i * da
        if skip(a) or skip(a + da): continue
        x, z = polar(r, a); x2, z2 = polar(r, a + da)
        L = math.hypot(x2 - x, z2 - z)
        yaw = math.degrees(math.atan2(-(z2 - z), x2 - x))
        place('rail_%s_%d' % (key, int(L * 10)), lambda L=L: FP.beacon_rail(L, key), x, z, yaw, y=y_fn(x, z) - .1, group=group)

def build():
    ground(); hub_deck(); rng = random.Random(11)
    hub(rng)
    for k in range(4): crater_ramp(k)
    craters()
    for k in (1, 2, 3, 4): zone(k, rng)
    peak(rng)
    sky()

GTONE = {1: ('regA', .72), 2: ('regB', .68), 3: ('mare', .64), 4: ('mare', .48)}   # = ground_shade tone + flat-face lift
def craters():
    """modelled crater props on every pock / crater (the ground only carries a shallow dish under them)"""
    for i, (cx, cz, R, d) in enumerate(POCKS + CRATERS):
        k = zone_of(math.hypot(cx, cz)) or 1; col, vg = GTONE[k]; v = i % 3
        place('crater_%d_%d' % (k, v), lambda v=v, col=col, vg=vg: FP.crater(v + 1, col, vg), cx, cz, (i * 47) % 360,
              s=R, y=Hm(cx, cz), group='Craters'); reserve(cx, cz, 1.6 * R)

def hub(rng):
    G = 'Hub'
    place('sell', FP.dust_exchange, -30, -298, face(-30, -298, 0, -318), y=HUB_Y, group=G); reserve(-30, -298, 14)
    place('shop', FP.gear_locker, 30, -298, face(30, -298, 0, -318), y=HUB_Y, group=G); reserve(30, -298, 14)
    place('rebirth', FP.reentry_pod, -38, -350, face(-38, -350, 0, -330), y=HUB_Y, group=G); reserve(-38, -350, 14)
    place('eggs', FP.egg_incubator, 38, -350, face(38, -350, 0, -330), y=HUB_Y, group=G); reserve(38, -350, 14)
    place('lander', FP.lunar_lander, 0, -378, face(0, -378, 0, -330), s=1.6, y=HUB_Y, group=G); reserve(0, -378, 20)
    place('jump_c', lambda: FP.jump_pad('cyan'), 0, -318, 0, y=HUB_Y + .1, group=G)          # the spawn pad, on the deck tiles
    for x, z in ((-52, -308), (52, -308), (-40, -386), (40, -386)):
        d = math.hypot(x - HUB[0], z - HUB[1]); x, z = HUB[0] + (x - HUB[0]) * 52 / d, HUB[1] + (z - HUB[1]) * 52 / d   # inside the deck rail (r 60)
        place('flood', FP.floodlight, x, z, face(x, z, HUB[0], HUB[1]), y=HUB_Y, group=G); reserve(x, z, 4)
    place('dish', FP.comms_dish, -24, -390, face(-24, -390, -60, -300), y=HUB_Y, group=G); reserve(-24, -390, 8)
    for x, z, s in ((-48, -330, 1), (48, -330, 2), (18, -392, 3)):
        place('crates%d' % s, lambda s=s: FP.supply_crates(s), x, z, rng.uniform(0, 360), y=HUB_Y, group=G); reserve(x, z, 5)
    place('tanks', FP.fuel_tanks, 22, -378, 90, y=HUB_Y - .3, group=G); reserve(22, -378, 7)
    # deck rail around the hub, open toward the crater (gate) and the back stairs
    for i in range(36):                                                         # 36 segments: 450k map budget
        a0 = i * math.tau / 36; a1 = (i + 1) * math.tau / 36
        if adiff(a0, math.pi / 2) < .32 or adiff(a1, math.pi / 2) < .32: continue
        x, z = HUB[0] + math.cos(a0) * (HUB_R - 2), HUB[1] + math.sin(a0) * (HUB_R - 2)
        x2, z2 = HUB[0] + math.cos(a1) * (HUB_R - 2), HUB[1] + math.sin(a1) * (HUB_R - 2)
        L = math.hypot(x2 - x, z2 - z)
        place('rail_hub', lambda L=L: FP.beacon_rail(L, 'beacon'), x, z, math.degrees(math.atan2(-(z2 - z), x2 - x)), y=HUB_Y + .3, group=G)

def crater_ramp(k):
    """airlock gate at the head of ramp k (k = 0 is the free zone-1 entry), rails down both ramp edges, return pad"""
    rc, yu, yl = RISER[k]; L = ramp_half_len(k); a = RAMP_A[k]
    gr = rc + L + 6 if k else HUB_R + 0.0
    if k == 0: gx, gz = 0.0, HUB[1] + HUB_R - 6
    else: gx, gz = polar(gr, a)
    place('gate%d' % (k + 1), lambda k=k: FP.airlock_gate(k + 1), gx, gz, face(gx, gz, 0, 0), y=(HUB_Y + .3 if k == 0 else yu - .1), group='Gates'); reserve(gx, gz, 16)
    for sd in (-1, 1):                                                            # beacon rails along both ramp edges
        steps = 6
        for i in range(steps):
            r0 = rc + L - 2 * L * i / steps; r1 = rc + L - 2 * L * (i + 1) / steps
            off = (RAMP_HW + 1.2) * sd
            x0, z0 = polar(r0, a); x1, z1 = polar(r1, a)
            tx, tz = -math.sin(a), math.cos(a)
            x0 += tx * off; z0 += tz * off; x1 += tx * off; z1 += tz * off
            L2 = math.hypot(x1 - x0, z1 - z0)
            yaw = math.degrees(math.atan2(-(z1 - z0), x1 - x0))
            place('rail_z%d_%d' % (k + 1, int(L2 * 10)), lambda L2=L2, k=k: FP.beacon_rail(L2, 'z%d' % (k + 1)), x0, z0, yaw, y=Hm(x0, z0), group='Gates')
    # return jump pad on the lower shelf, beside the ramp foot
    pr = rc - RW - 12; pa = a + (RAMP_HW + 12) / pr                             # 12 off the riser: its slope stays out of the pad
    px, pz = polar(pr, pa)
    fn = lambda k=k: FP.jump_pad('z%d' % (k + 1))
    place('pad_z%d' % (k + 1), fn, px, pz, 0, y=top_of('pad_z%d' % (k + 1), fn, px, pz) - .05, group='Gates'); reserve(px, pz, 7)
    # keep the ramp and its landing clear
    for t in range(-3, 4):
        x, z = polar(rc + t * L / 3, a); reserve(x, z, RAMP_HW + 3)

def lip_rails():
    for k, (rc, yu, yl) in enumerate(RISER):
        r = rc + RW + 1.5
        skip = lambda a, k=k, r=r: adiff(a, RAMP_A[k]) * r < RAMP_HW + 3 or (k == 0 and math.hypot(*polar(r, a)) and math.hypot(polar(r, a)[0] - HUB[0], polar(r, a)[1] - HUB[1]) < HUB_R + 4)
        rail_ring(r, Hm, skip, 'beacon', 'Rails', step=20.0)                  # 20-stud spans: 450k map budget

def scatter(k, rng, items, n, group, rmin=None, rmax=None, gap=1.0, mess=False):
    """mess=True (low dust / junk / meteor pieces): only on calm ground, sat on the mesh at the centre, so the micro
    relief never buries part of a flat drift"""
    lo, hi, _y = ZONES[k]; rmin = rmin or lo + 7; rmax = rmax or hi - 6; placed = 0
    for _t in range(n * 40):
        if placed >= n: break
        a = rng.uniform(0, math.tau); r = math.sqrt(rng.uniform(rmin ** 2, rmax ** 2))
        x, z = polar(r, a)
        key, fn, rad, s = items[rng.randrange(len(items))]
        if abs(r - TRACK_R[k]) < rad + 4 or on_ramp(x, z, rad) or not free(x, z, rad * gap) or near_riser(r, rad + 2) or spread(x, z, rad) > (.3 if mess else .6): continue
        place(key, fn, x, z, rng.uniform(0, 360), s=s, y=(top_of(key, fn, x, z, s) + (.18 if key.startswith('junk') else .02)) if mess else None, group=group); reserve(x, z, rad); placed += 1
    return placed

def zone(k, rng):
    G = 'Z%d_%s' % (k, ZNAME[k]); M = 'Mess_Z%d' % k
    rk = random.Random(100 + k)
    if k == 1:
        # story group: abandoned rover + crates + dust trail, beside the track
        a = math.radians(-60); x, z = polar(222, a)
        place('rover', FP.moon_rover, x, z, face(x, z, 0, 0) + 70, group=G); reserve(x, z, 9)
        x2, z2 = polar(214, a - .045); place('crates2', lambda: FP.supply_crates(2), x2, z2, 30, group=G); reserve(x2, z2, 5)
        rocks = [('rockA%d' % i, lambda i=i: FP.moon_rock(i, 3.4, 'regA'), 7, 1.3) for i in range(3)] + \
                [('rockAb%d' % i, lambda i=i: FP.moon_rock(10 + i, 6.0, 'regB'), 9, 1.0) for i in range(2)]
        scatter(k, rk, rocks, 34, G)
        mess = [('dpatch%d' % i, lambda i=i: FP.dust_patch(i, 6.0, 'regA'), 9, 1.5) for i in range(4)] + \
               [('dpile%d' % i, lambda i=i: FP.dust_pile(i, 'regA'), 5, 1.6) for i in range(3)]
        scatter(k, rk, mess, 70, M, gap=.9, mess=True)
    if k == 2:
        for i, (cx, cz, R, d) in enumerate(CRATERS):                           # meteorites sit in some craters
            if zone_of(math.hypot(cx, cz)) == 2 and i % 3 == 0:
                place('meteor%d' % (i % 2), lambda i=i: FP.meteorite(i % 2 + 1, 2.4), cx, cz, rk.uniform(0, 360), y=Hm(cx, cz) - .6, group=G)
            reserve(cx, cz, R * .9)
        rocks = [('rockB%d' % i, lambda i=i: FP.moon_rock(20 + i, 3.6, 'regB'), 7, 1.3) for i in range(3)]
        scatter(k, rk, rocks, 26, G)
        mess = [('mchunk%d' % i, lambda i=i: FP.meteor_chunk(i), 5, 1.7) for i in range(3)] + \
               [('dpatchB%d' % i, lambda i=i: FP.dust_patch(10 + i, 5.0, 'regB'), 8, 1.5) for i in range(3)]
        scatter(k, rk, mess, 60, M, gap=.9, mess=True)
    if k == 3:
        big = [('wreck%d' % i, lambda i=i: FP.satellite_wreck(i), 12, 1.0) for i in (1, 2)] + [('tanks', FP.fuel_tanks, 9, 1.0),
               ('crates1', lambda: FP.supply_crates(1), 6, 1.0)]
        scatter(k, rk, big, 16, G, gap=1.3)
        rocks = [('rockM%d' % i, lambda i=i: FP.moon_rock(30 + i, 3.0, 'mare'), 5, 1.0) for i in range(2)]
        scatter(k, rk, rocks, 16, G)
        mess = [('junk%d' % i, lambda i=i: FP.junk_heap(i), 6, 1.5) for i in range(4)]
        scatter(k, rk, mess, 55, M, gap=.9, mess=True)
    if k == 4:
        ice = [('ice%d' % i, lambda i=i: FP.ice_crystal(i, 1.3), 8, 1.5) for i in range(3)]
        scatter(k, rk, ice, 26, G, gap=1.2)
        rocks = [('rockI%d' % i, lambda i=i: FP.moon_rock(40 + i, 3.2, 'mare'), 5, 1.0) for i in range(2)]
        scatter(k, rk, rocks, 12, G)
        mess = [('ishard%d' % i, lambda i=i: FP.ice_shards(i), 5, 1.7) for i in range(3)] + [('junk0', lambda: FP.junk_heap(0), 6, 1.5)]
        scatter(k, rk, mess, 45, M, gap=.9, mess=True)
    if k == 1:                                                                  # ejecta boulders on the rim crest
        for i in range(70):
            a = rk.uniform(0, math.tau); r = rk.uniform(264, 296); sc = rk.uniform(.8, 1.6)
            x, z = polar(r, a)
            if math.hypot(x - HUB[0], z - HUB[1]) < HUB_R + 10 or not free(x, z, 6) or r - (4.0 + (i % 4) * 1.5) * sc < 262 or spread(x, z, 6) > 2.5: continue   # clear of the lip rail (r 260)
            place('crest%d' % (i % 4), lambda i=i: FP.moon_rock(60 + i % 4, 4.0 + (i % 4) * 1.5, 'regA'), x, z, rk.uniform(0, 360), s=sc, group='Rocks'); reserve(x, z, 6)
    for i in range(8):                                                          # lamp masts on the ring path (rhythm + light)
        a = (i + .5) * math.tau / 8 + k * .3
        x, z = polar(TRACK_R[k] + 5.5, a)
        if on_ramp(x, z, 6) or not free(x, z, 3): continue
        place('flood', FP.floodlight, x, z, face(x, z, 0, 0) + 180, s=.8, group=G); reserve(x, z, 3)
    if k == 2:
        a = math.radians(110); x, z = polar(186, a)
        fn = lambda: FP.meteorite(7, 3.2); place('meteorBig', fn, x, z, 40, s=2.2, y=top_of('meteorBig', fn, x, z, 2.2) - .3, group=G); reserve(x, z, 22)
    # riser foot boulders (containment + breaks the step line), sparse
    rc = RISER[k - 1][0]
    for i in range(int(rc * math.tau / 26)):
        a = i * math.tau / int(rc * math.tau / 26) + rk.uniform(-.02, .02)
        x, z = polar(rc - RW - 2.5, a)
        if on_ramp(x, z, 4) or not free(x, z, 3): continue
        if rk.random() < .45 and spread(x, z, 3) < 1.5:
            place('rbould%d' % (i % 3), lambda i=i: FP.moon_rock(50 + i % 3, 2.6, 'regB'), x, z, rk.uniform(0, 360), s=rk.uniform(.8, 1.3), group='Rocks')

def peak(rng):
    G = 'Peak'
    place('rocket', FP.moon_rocket, -8.0, 0.0, 0.0, s=1.25, y=PEAK_Y - .2, group=G)
    place('tower', FP.launch_tower, 17.6, 0.0, 0.0, s=1.25, y=PEAK_Y - .2, group=G)
    for i in range(10):                                                           # rail round the peak top
        pass
    rail_ring(PEAK_R - 1.2, Hm, lambda a: adiff(a, 0.0) < .55, 'beacon', 'Peak', step=14.0)

def sky():
    place('earth', FP.earth, 182.0, 1680.0, 30.0, s=126.0, y=396.0, group='Horizon')

# ------------------------------------------------------------------ look: black starry sky, hard low white sun
def look():
    w = bpy.data.worlds.new('Space'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 220
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = .045
    mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
    nt.links.new(tc.outputs['Generated'], vor.inputs['Vector']); nt.links.new(vor.outputs['Distance'], mr.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (.012, .015, .03, 1); mix.inputs['B'].default_value = (2.2, 2.2, 2.5, 1)
    nt.links.new(mr.outputs['Result'], mix.inputs['Factor']); nt.links.new(mix.outputs['Result'], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .12; b.inputs['Roughness'].default_value = .95
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 5.0; sun.data.color = (1, .97, .92); sun.data.angle = math.radians(1.2)
    el = math.radians(40); to_sun = r2b((math.cos(el) * .9, math.sin(el), math.cos(el) * -.44)) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    # ambient so shadows are not pitch black (Roblox: Ambient / OutdoorAmbient): a soft blue-grey world light probe
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    # shadowless earthshine fill from the opposite side (Roblox: OutdoorAmbient / Ambient do this job)
    fill = bpy.data.objects.new('ZFill', bpy.data.lights.new('ZFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = 1.1; fill.data.color = (.6, .7, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.5, .8, .35)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()

MATERIALS = {'regA': 'Sand', 'regB': 'Slate', 'mare': 'Basalt', 'frost': 'Snow', 'ice': 'Ice', 'steel': 'Metal',
             'foil': 'SmoothPlastic', 'rust': 'Metal', 'char': 'Basalt', 'panel': 'SmoothPlastic', 'orange': 'SmoothPlastic',
             'red': 'SmoothPlastic', 'navy': 'SmoothPlastic', 'ocean': 'SmoothPlastic', 'land': 'SmoothPlastic'}
MAT_OVERRIDES = {'Horizon_Earth': 'SmoothPlastic'}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Sand'] = ('noise', 16.0, .9, .98, 0, .06)          # powdery regolith, matte
    RM.LOOK['Slate'] = ('voronoi', .5, .8, .92, 0, .1)
    RM.LOOK['Basalt'] = ('voronoi', .4, .5, .9, 0, .1)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon_Earth',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 8000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

build(); lip_rails()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'moon_map.blend'))
SHOTS = {
    'map_spawn.png': ((0, HUB_Y + 5.5, -334), (0, -4, 0), 22),
    'map_overview.png': ((380, 260, -420), (0, -50, -20), 26),
    'map_hub.png': ((70, 40, -250), (0, HUB_Y, -340), 28),
    'map_z1.png': ((160, 10, -200), (215, -12, -40), 30),
    'map_z2.png': ((190, 2, 30), (110, -34, 135), 30),
    'map_z3.png': ((-40, -20, 175), (-110, -58, 60), 30),
    'map_z4.png': ((-35, -44, -112), (35, -84, -45), 30),
    'map_peak.png': ((-70, -30, -90), (0, 0, 0), 30),
    'map_top.png': ((0, 1100, 1), (0, 0, 0), 30),
    'map_player_z1.png': ((150, -6.5, -168), (60, -40, -20), 24),
    'map_player_z3.png': ((-72, -52.5, -92), (0, -25, 0), 24),
}
_c = max(CRATERS, key=lambda c: c[2]); _d = math.hypot(_c[0], _c[1])
SHOTS['map_crater.png'] = ((_c[0] * (1 - 20 / _d), H(_c[0], _c[1]) + 8.5, _c[1] * (1 - 20 / _d)), (_c[0], H(_c[0], _c[1]), _c[1]), 26)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, lens) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, lens)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
