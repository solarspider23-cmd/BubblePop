# blender -b --factory-startup --python fish_map.py [-- norender] [-- name.png ...] -> Tidehook Lagoon (fish_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: radial ring lagoon on stilts (fishing-sim hub).
# A flat tropical fishing resort on open water: ring boardwalk (r 58..70, deck y 4.5, water y 0) round a lagoon; four
# spokes to a central stone platform with the hero (lighthouse rising out of a glass aquarium dome); stations on deck
# pads OUTSIDE the ring (spawn plaza S, rod shop SW, bait shop SE, fish market E, boat dock W); fishing piers NE / N /
# NW into deep water; a broken reef ring of sand islets with palms frames the fishing water; open sea beyond.
# Bearings: theta 0 = south (+Z, spawn), 90 = east (+X), 180 = north, 270 = west. pos(theta, r) = (r sin, r cos).
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import fish_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box, cyl, hull, rock_pts

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

# ------------------------------------------------------------------ layout constants
WATER, DECK = 0.0, 4.5
R_IN, R_OUT = 58.0, 70.0          # ring boardwalk
R_PLAT = 32.0                     # central stone platform (hero)
SPOKE_W = 8.0
D2R = math.radians
def pos(th, r): return (r * math.sin(D2R(th)), r * math.cos(D2R(th)))
def outward(th): return Vector((math.sin(D2R(th)), 0, math.cos(D2R(th))))
def tangent(th): return Vector((math.cos(D2R(th)), 0, -math.sin(D2R(th))))
def lp(th, rc, lx, lz):
    """pad-local (lx tangential, lz radial outward from the pad centre rc) -> world (x, z)"""
    c = Vector((0, 0, 0)) + outward(th) * rc + tangent(th) * lx + outward(th) * lz
    return (c.x, c.z)

# pads outside the ring: name, theta, depth (radial), width (tangential)
PADS = {'Spawn': (0, 31.0, 44.0), 'Rod': (315, 24.0, 28.0), 'Bait': (45, 24.0, 26.0), 'Market': (90, 26.0, 34.0),
        'Dock': (270, 20.0, 30.0)}
PIERS = {'PierNE': (135, 128.0), 'PierN': (180, 150.0), 'PierNW': (225, 124.0)}   # theta, end radius
PIER_W = 7.0
END = {'PierNE': (18.0, 13.0), 'PierN': (30.0, 12.0), 'PierNW': (18.0, 13.0)}       # end platform width, depth
DOCK_END = 132.0
ISLETS = [  # theta, radius, half length (tangential), half width (radial), seed
    (35, 238, 44, 24, 1), (80, 254, 34, 20, 2), (120, 230, 40, 24, 3), (162, 248, 52, 26, 4),
    (205, 238, 36, 22, 5), (243, 254, 30, 18, 6), (302, 238, 40, 22, 7)]

# ------------------------------------------------------------------ seabed + islets (one height function)
def islet_e(x, z):
    """<= 1 inside an islet's ellipse (smallest over all islets)"""
    best = 9.0
    for th, r, a, b, _ in ISLETS:
        cx, cz = pos(th, r); t = tangent(th); u = outward(th)
        dx, dz = x - cx, z - cz
        lx = dx * t.x + dz * t.z; lz = dx * u.x + dz * u.z
        e = ((lx / a) ** 2 + (lz / b) ** 2) ** .5 * (1 + .12 * (nz(x, 0, z, 18, 3) - .5))
        best = min(best, e)
    return best

SEA_BED = -7.5          # the seabed never drops deeper than this (the export's water check: a bed within 8 under the sea)
def H(x, z):
    """seabed / islets; out at the world edge it rises to +1 so the sea plane's border sits against a bank"""
    y = max(H_raw(x, z), SEA_BED)
    return lerp(y, 1.0, smooth((max(abs(x), abs(z)) - 1380) / 100))
def H_raw(x, z):
    """the natural depth profile (deep blue past the reef): only the seabed COLOUR still follows it"""
    r = math.hypot(x, z)
    if r < 75: y = -3.6 - .8 * smooth((r - 35) / 25) + (nz(x, 0, z, 14, 1) - .5) * .8
    else:
        y = -4.4 - 13 * smooth((r - 75) / 80) - 6 * smooth((r - 150) / 50)
        reef = (1 - smooth(abs(r - 240) / 40)) * smooth((nz(x, 0, z, 60, 2) - .35) / .3)   # patchy shoals under the islets
        y = lerp(y, -5.0 + (nz(x, 0, z, 25, 5) - .5) * 3.0, reef)
        y -= 26 * smooth((r - 300) / 120)
    e = islet_e(x, z)
    if e < 1.6:
        top = 1.4 + 1.8 * smooth((.75 - e) / .55) + (nz(x, 0, z, 9, 4) - .5) * .5
        y = lerp(y, top, smooth((1.6 - e) / .9))
    return y

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
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
STATIC_TRIS = {}
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris; add_owner([ob], bool(WATER_RE.search(name)))

# ---- placement fit: the exporter's hard checks (roblox_export.py 6c) run while placing. Statics + every placed hard
# prop are owners; an auto-grounded prop (y None) is raised in 0.25 steps (its base stays bedded) or nudged until
# no more than 3.5% of its body (7% for foliage) is inside one owner and it does not float; None = nowhere fits
from mathutils.bvhtree import BVHTree
import re
SOFT_RE = re.compile(r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant(?!er)')
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

# ------------------------------------------------------------------ deck geometry (static)
def prism(mb, quad, y, th, sh):
    """plank / slab from a top quad [(x, z) x4] at height y, thickness th"""
    bm = bmesh.new()
    t = [bm.verts.new((x, y, z)) for x, z in quad]; b = [bm.verts.new((x, y - th, z)) for x, z in quad]
    bm.faces.new(t); bm.faces.new(b[::-1])
    for i in range(4):
        j = (i + 1) % 4; bm.faces.new((t[j], t[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mb.add(bm, sh)

U = lambda col: FP.PAL.u(col)
def sh_val(col, v): return lambda f: [(U(col), clamp(v + .1 * f.normal.y, .04, .96))] * len(f.loops)

PILES = []
def piling(mb, x, z, top=DECK - .5, r=.55):
    y0 = H(x, z) - 1.0
    bm = cyl(r, top - y0, 7, 0, r * .9, y0); bmesh.ops.translate(bm, vec=Vector((x, 0, z)), verts=bm.verts)
    mb.add(bm, lambda f: [(U('wood'), clamp(.3 + .15 * f.normal.y + (.1 if f.calc_center_median().y > WATER else -.05), .04, .96))] * len(f.loops))
    PILES.append((x, z))

def beam(mb, a, b, y, w=.6, h=.7, col='wood', v=.32):
    a, b = Vector((a[0], 0, a[1])), Vector((b[0], 0, b[1])); d = (b - a); L = d.length; d.normalize()
    n = Vector((-d.z, 0, d.x)) * w / 2
    q = [(p.x, p.z) for p in (a + n, b + n, b - n, a - n)]
    prism(mb, q, y, h, sh_val(col, v))

def deck_rect(mb, th, rc, lx0, lx1, lz0, lz1, y=DECK - .05, seed=0, piles=True):
    """plank deck in a pad-local frame: planks along local x (across the walk), gaps, two stringers + edge beams
    under it, pilings every ~6 studs round the edge and down the middle"""
    rng = random.Random(seed); pw = 1.2; n = max(1, int((lz1 - lz0) / pw)); step = (lz1 - lz0) / n
    for i in range(n):
        za, zb = lz0 + i * step + .06, lz0 + (i + 1) * step - .06
        q = [lp(th, rc, lx0, za), lp(th, rc, lx1, za), lp(th, rc, lx1, zb), lp(th, rc, lx0, zb)]
        v = .56 + rng.uniform(-.09, .07) - (.12 if rng.random() < .06 else 0)
        prism(mb, q, y, .45, sh_val('deck', v))
    for lx in (lx0 + .3, lx1 - .3):
        beam(mb, lp(th, rc, lx, lz0), lp(th, rc, lx, lz1), y - .4, .6, .8, 'wood', .3)
    for lz in (lz0 + .3, lz1 - .3):
        beam(mb, lp(th, rc, lx0, lz), lp(th, rc, lx1, lz), y - .45, .5, .7, 'wood', .36)
    if piles:
        nx = max(1, round((lx1 - lx0) / 6)); nzz = max(1, round((lz1 - lz0) / 6))
        for i in range(nx + 1):
            for j in range(nzz + 1):
                edge = i in (0, nx) or j in (0, nzz)
                if not edge and (i + j) % 2: continue
                x, z = lp(th, rc, lerp(lx0 + .5, lx1 - .5, i / nx), lerp(lz0 + .5, lz1 - .5, j / nzz))
                piling(mb, x, z)

def ring_deck(mb, r0, r1, y=DECK, seed=1):
    """the ring boardwalk: radial planks (across the walk), stringers along both edges + the middle, pilings"""
    rng = random.Random(seed); rm = (r0 + r1) / 2; n = int(math.tau * rm / 1.25); da = 360.0 / n
    for i in range(n):
        a0, a1 = i * da + .05 * da / 1, (i + 1) * da - .09 * da
        q = [pos(a0, r0), pos(a0, r1), pos(a1, r1), pos(a1, r0)]
        v = .56 + rng.uniform(-.09, .07) - (.12 if rng.random() < .06 else 0)
        prism(mb, q, y, .45, sh_val('deck', v))
    m = 120
    for rr in (r0 + .4, rm, r1 - .4):
        for i in range(m):
            beam(mb, pos(i * 360 / m, rr), pos((i + 1) * 360 / m, rr), y - .4, .6, .8, 'wood', .3)
    k = int(math.tau * r1 / 6.0)
    for i in range(k):
        a = i * 360 / k
        for rr in (r0 + .5, r1 - .5):
            x, z = pos(a + (180 / k if rr < rm else 0), rr); piling(mb, x, z)
        beam(mb, pos(a, r0), pos(a, r1), y - 1.2, .5, .6, 'wood', .26)

def platform(mb):
    """central coral-stone platform: polar flagstones (inset), coping course, ashlar foundation wall into the water"""
    rng = random.Random(5); r = 20.0
    bm = bmesh.new()
    while r < R_PLAT - 1.2:
        r1 = min(r + 2.4, R_PLAT - 1.2); C = math.tau * (r + r1) / 2; a = rng.uniform(0, 360); end = a + 360
        while a < end - .5:
            L = rng.uniform(2.4, 3.6) * 360 / C; b = min(a + L, end)
            n = max(1, int((b - a) / 6) + 1); angs = [lerp(a, b, k / n) for k in range(n + 1)]
            pts = [pos(t, r) for t in angs] + [pos(t, r1) for t in reversed(angs)]
            bm.faces.new([bm.verts.new((x, DECK, z)) for x, z in pts])
            a = b
        r = r1
    fs = list(bm.faces)
    for f in fs:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.inset_individual(bm, faces=fs, thickness=.1, depth=-.08, use_even_offset=True)
    bm.normal_update()
    mb.add(bm, lambda f: [(U('coral'), clamp((.46 + (FP.h01(*[round(c, 1) for c in f.calc_center_median()]) - .5) * .14) if f.normal.y > .99 else .4, .04, .96))] * len(f.loops))
    bm = FP.lathe([(19.6, DECK - .4), (19.6, DECK - .05), (0, DECK - .05)], n=48); mb.add(bm, sh_val('coral', .42))
    bm = FP.lathe([(R_PLAT - 1.3, DECK - .2), (R_PLAT + .25, DECK - .2), (R_PLAT + .3, DECK + .35), (R_PLAT - 1.3, DECK + .35)], n=64)
    mb.add(bm, sh_val('coral', .7))
    w = FP.ashlar_ring(R_PLAT, -5.0, DECK - .2, 3.0, 1.3, seed=2)
    mb.add(w, FP.ash_sh('coral', base=.6, var=.07, grime=.25))

def spoke(mb, th):
    r0, r1 = R_PLAT - 1.0, R_IN + 1.0; rc = (r0 + r1) / 2
    deck_rect(mb, th, rc, -SPOKE_W / 2, SPOKE_W / 2, r0 - rc, r1 - rc, seed=int(th) + 3)

def compass(mb, c, R=6.0):
    """compass-rose inlay in the spawn plaza deck: 8-point star of teal / yellow planks on a dark disc (no letters)"""
    x0, z0 = c
    bm = FP.lathe([(R + .5, DECK + .02), (R + .5, DECK + .1), (0, DECK + .1)], n=32); bmesh.ops.translate(bm, vec=Vector((x0, 0, z0)), verts=bm.verts)
    mb.add(bm, sh_val('wood', .38))
    for k in range(8):
        a = k * 45; L = R if k % 2 == 0 else R * .62; w = R * .2
        tip = pos(a, L); l = pos(a + 90, w); rr = pos(a - 90, w)
        for side, col in ((l, 'teal' if k % 2 == 0 else 'yellow'), (rr, 'paint')):
            bm = bmesh.new()
            vs = [bm.verts.new((x0 + p[0], DECK + .14, z0 + p[1])) for p in ((0, 0), side, tip)]
            f = bm.faces.new(vs); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
            ex = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=Vector((0, -.06, 0)), verts=[g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)])
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            mb.add(bm, sh_val(col, .6))
    bm = FP.lathe([(R * .14, DECK + .1), (R * .14, DECK + .24), (0, DECK + .24)], n=12); bmesh.ops.translate(bm, vec=Vector((x0, 0, z0)), verts=bm.verts)
    mb.add(bm, sh_val('metal', .6))

def hardscape():
    mb = MB(); ring_deck(mb, R_IN, R_OUT); static('Hardscape_Ring', mb, 'Boardwalk')
    mb = MB(); platform(mb)
    for th in (0, 90, 180, 270): spoke(mb, th)
    static('Hardscape_Centre', mb, 'Centre')
    for name, (th, D, W) in PADS.items():
        mb = MB(); r0 = R_OUT - 1.0; rc = r0 + D / 2
        deck_rect(mb, th, rc, -W / 2, W / 2, -D / 2, D / 2, seed=len(name))
        if name == 'Spawn': compass(mb, lp(th, rc, 0, 3.0))
        if name == 'Dock':                                                       # main pier + two finger slips
            deck_rect(mb, th, rc, -PIER_W / 2, PIER_W / 2, D / 2 - 1, DOCK_END - rc, seed=31)
            for lz in (16.0, 38.0):
                for sx in (-1, 1):
                    deck_rect(mb, th, rc, sx * PIER_W / 2 if sx > 0 else -PIER_W / 2 - 13, PIER_W / 2 + 13 if sx > 0 else -PIER_W / 2, lz, lz + 4, seed=int(lz) + sx)
        static('Hardscape_%s' % name, mb, 'Stations')
    for name, (th, rend) in PIERS.items():
        mb = MB(); r0 = R_OUT - 1.0; ew, ed = END[name]; rc = (r0 + rend) / 2
        deck_rect(mb, th, rc, -PIER_W / 2, PIER_W / 2, r0 - rc, rend - ed - rc + .5, seed=len(name) + 7)
        deck_rect(mb, th, rend - ed / 2, -ew / 2, ew / 2, -ed / 2, ed / 2, seed=len(name) + 9)
        static('Hardscape_%s' % name, mb, 'Piers')

def ground():
    """seabed + islets in one grid: fine inside the reef, coarse to the horizon; colour by depth (white sand ->
    turquoise-tinted sand -> deep blue), beaches, grass on islet tops"""
    fine = [x * 8.0 for x in range(-41, 42)]
    xs = [x for x in range(-1600, -330, 100)] + [-340] + fine + [340] + [x for x in range(400, 1601, 100)]   # past the sea plane's edge
    zs = list(xs)
    bm = bmesh.new(); VV = {}
    def v(i, j):
        if (i, j) not in VV: VV[i, j] = bm.verts.new((xs[i], H(xs[i], zs[j]), zs[j]))
        return VV[i, j]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            f = bm.faces.new((v(i, j), v(i, j + 1), v(i + 1, j + 1), v(i + 1, j))); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    rng = random.Random(4)
    def sh(f):
        c = f.calc_center_median(); n = f.normal
        under = min(v.co.y for v in f.verts) < .35                           # dry sand only where the whole face is dry
        out = []
        for l in f.loops:                                                    # value per VERTEX: smooth gradients, no facets
            p = l.vert.co; y = H_raw(p.x, p.z) if p.y < .35 else p.y
            if not under:
                v = .55 + .3 * smooth((y + .2) / 2.5) + (nz(p.x, 0, p.z, 8, 7) - .5) * .08
            else:                                                            # pale aqua sand -> turquoise -> deep blue
                v = .9 - .18 * smooth(-y / 3) - .26 * smooth(-y / 12) - .26 * smooth((-y - 9) / 22) + (nz(p.x, 0, p.z, 12, 7) - .5) * .04
            out.append((U('water' if under else 'sand'), clamp(v, .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_Seabed', mb, 'Ground')

def water():
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-1500, WATER, -1500), (1500, WATER, -1500), (1500, WATER, 1500), (-1500, WATER, 1500))]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    mb = MB(); mb.add(bm, lambda f: [(U('water'), .52)] * len(f.loops)); static('Sea_Water', mb, 'Water')

def islet_grass():
    """organic grass mounds sitting IN each islet top: irregular rounded outline, rim tucked into the sand with a darker
    band, a soft raised edge, slightly domed middle (natural tropical green from the palm ramp, not neon)"""
    mb = MB(); rng = random.Random(17)
    for th, r, a, b, sd in ISLETS:
        cx, cz = pos(th, r); t = tangent(th); u = outward(th)
        for m, (ox, k) in enumerate(((0.0, .5), (rng.choice((-1, 1)) * a * .42, .26))):
            N = 30; rings = [(1.0, -.08, .22), (.9, .34, .27), (.7, .4, .34), (.42, .5, .38), (.15, .56, .4)]
            bm = bmesh.new(); R = []
            for f_, lift, v in rings:
                ring = []
                for i in range(N):
                    ph = i * math.tau / N
                    e = k * (1 + .28 * (nz(math.cos(ph) * 3 + sd * 7, m, math.sin(ph) * 3, 1.3, sd) - .5) + .08 * math.sin(3 * ph + sd))
                    lx, lz = ox + math.cos(ph) * a * e * f_, math.sin(ph) * b * e * f_
                    x, z = cx + t.x * lx + u.x * lz, cz + t.z * lx + u.z * lz
                    ring.append(bm.verts.new((x, H(x, z) + lift, z)))
                R.append((ring, v))
            c = Vector((cx + t.x * ox, 0, cz + t.z * ox)); cv = bm.verts.new((c.x, H(c.x, c.z) + .6, c.z))
            for (A, va), (Bq, vb) in zip(R, R[1:]):
                for i in range(N):
                    j = (i + 1) % N; bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
            for i in range(N): bm.faces.new((R[-1][0][i], R[-1][0][(i + 1) % N], cv))
            for fc in bm.faces:
                fc.normal_update()
                if fc.normal.y < 0: fc.normal_flip()
            vals = {}
            for ring, v in R:
                for q in ring: vals[q.co.to_tuple(3)] = v
            vals[cv.co.to_tuple(3)] = .4
            mb.add(bm, lambda fc, vals=vals: [(U('palm'), clamp(vals.get(l.vert.co.to_tuple(3), .36) + (nz(l.vert.co.x, 0, l.vert.co.z, 4, 3) - .5) * .06, .04, .96)) for l in fc.loops], smooth=True)
    static('Islet_Grass', mb, 'Islets')

def horizon():
    """tropical volcanic islands in 3 overlapping depth layers. Each = a wide sand / rock shoreline sunk into the sea,
    a chunky volcano cone + a shoulder cone (faceted rock), jungle canopy lumps hugging the lower slopes; colours fade
    cooler + lighter with distance (near: deep green + dark rock, mid: muted, far: pale blue-grey silhouette)"""
    mb = MB(); rng = random.Random(11)
    ISL = [  # theta, distance, base radius, height, layer
        (138, 900, 95, 42, 0), (222, 930, 120, 55, 0),
        (160, 1150, 170, 78, 1), (205, 1180, 140, 64, 1), (110, 1180, 130, 52, 1), (255, 1150, 110, 46, 1),
        (180, 1420, 260, 120, 2), (128, 1440, 200, 92, 2), (232, 1430, 230, 105, 2), (70, 1420, 170, 70, 2), (300, 1420, 180, 64, 2)]
    TONE = {0: {'rock': ('rock', .4), 'palm': ('palm', .24), 'sand': ('sand', .4)},
            1: {'rock': ('rock', .58), 'palm': ('palm', .34), 'sand': ('sand', .5)},
            2: {'rock': ('rock', .76), 'palm': ('rock', .7), 'sand': ('rock', .8)}}
    def cone(cx, cz, R, h, sq, seed, n=34):
        r2 = random.Random(seed); pts = []
        for i in range(n):
            u = r2.random() ** .8; y = h * u; a_ = r2.uniform(0, math.tau)
            rr = R * (1 - u) ** .85 * r2.uniform(.82, 1.05) + R * .06
            pts.append(Vector((cx + math.cos(a_) * rr, y, cz + math.sin(a_) * rr * sq)))
        for i in range(10):
            a_ = i * math.tau / 10; pts.append(Vector((cx + math.cos(a_) * R * 1.02, -10, cz + math.sin(a_) * R * sq * 1.02)))
        pts.append(Vector((cx, h, cz)))
        return hull(pts)
    for k, (th, d, w, h, L) in enumerate(ISL):
        cx, cz = pos(th, d); sdk = k * 13 + 5; T_ = TONE[L]
        tng = tangent(th)
        ring = [Vector((cx + math.cos(i * math.tau / 16) * w * (1.0 + .05 * math.sin(3 * i + k)), y, cz + math.sin(i * math.tau / 16) * w * .55 * 1.03)) for y in (.6, -12) for i in range(16)]
        uS, vS = U(T_['sand'][0]), T_['sand'][1]
        if L == 0: mb.add(hull(ring), lambda f, uS=uS, vS=vS: [(uS, clamp(vS + .08 * f.normal.y, .04, .96))] * len(f.loops))
        uR, vR = U(T_['rock'][0]), T_['rock'][1]; uG, vG = U(T_['palm'][0]), T_['palm'][1]
        for j, (ox, sc, hs) in enumerate(((0.0, 1.0, 1.0), (rng.choice((-1, 1)) * .45, .6, .62))):
            c = Vector((cx, 0, cz)) + tng * (ox * w)
            bm = cone(c.x, c.z, w * sc, h * hs, .55, sdk + j)
            def sh(f, hh=h * hs, uR=uR, vR=vR, uG=uG, vG=vG):
                cc = f.calc_center_median(); n = f.normal
                if cc.y < hh * .62 and n.y > .25: return [(uG, clamp(vG + .06 * n.y + rng.uniform(-.03, .03), .04, .96))] * len(f.loops)
                return [(uR, clamp(vR + .16 * n.y + rng.uniform(-.03, .03), .04, .96))] * len(f.loops)
            mb.add(bm, sh)
        if L < 2:                                                            # jungle canopy lumps on the lower slopes
            for j in range(8):
                a_ = rng.uniform(0, math.tau); rr = rng.uniform(.45, .8)
                y = h * (1 - rr) ** .85 * .9 - 1.0
                x = cx + math.cos(a_) * w * rr; z = cz + math.sin(a_) * w * rr * .55
                bl = hull(rock_pts((w * .13, w * .06, w * .1), n=12, seed=sdk * 3 + j)); bmesh.ops.translate(bl, vec=Vector((x, max(y, 2.0), z)), verts=bl.verts)
                mb.add(bl, lambda f, uG=uG, vG=vG: [(uG, clamp(vG + .02 + .08 * f.normal.y + rng.uniform(-.04, .04), .04, .96))] * len(f.loops))
    static('Horizon_Islands', mb, 'Horizon')

# ------------------------------------------------------------------ rails (signature edge module)
def bay_key(L, buoy, post=True):
    Lr = round(L * 4) / 4
    k = 'rail%.2f%s%s' % (Lr, 'b' if buoy else '', '' if post else 'n')
    return k, (lambda: FP.rail_bay(Lr, buoy, post=post))
BAYS = [0]; RUNS = []
def rail_line(a, b, group, y=DECK, gaps=()):
    """straight run a->b (x, z) with gaps [(s0, s1)] in studs along it: bays ~6 long, a post closing every run"""
    a, b = Vector((a[0], 0, a[1])), Vector((b[0], 0, b[1])); L = (b - a).length; d = (b - a) / L
    cuts = [0.0]; segs = []
    for g0, g1 in sorted(gaps): segs.append((cuts[-1], g0)); cuts.append(g1)
    segs.append((cuts[-1], L))
    for s0, s1 in segs:
        if s1 - s0 < 1.5: continue
        n = max(1, round((s1 - s0) / 6)); bl = (s1 - s0) / n; bays = []
        for i in range(n):
            BAYS[0] += 1; bays.append((a + d * (s0 + bl * i), a + d * (s0 + bl * (i + 1)), BAYS[0] % 4 == 0))
        RUNS.append((bays, group, y))

def rail_arc(r, a0, a1, group, y=DECK):
    """arc run from angle a0 to a1 (degrees, increasing): chord bays + an end post"""
    if a1 <= a0: return
    arc = D2R(a1 - a0) * r; n = max(1, round(arc / 6)); da = (a1 - a0) / n; bays = []
    for i in range(n):
        p0, p1 = pos(a0 + i * da, r), pos(a0 + (i + 1) * da, r)
        BAYS[0] += 1; bays.append((Vector((p0[0], 0, p0[1])), Vector((p1[0], 0, p1[1])), BAYS[0] % 4 == 0))
    RUNS.append((bays, group, y))

def rails_flush():
    """place every collected run: each bay carries the post at its start, a post closes each run. Where two runs meet
    at a corner only ONE post stands there: a run whose start is already taken is laid backwards, and an end post is
    skipped where a post already stands (posts are 0.66 wide: spots closer than 0.9 count as the same)"""
    took = []
    def taken(p): return any((p.x - q.x) ** 2 + (p.z - q.z) ** 2 < .81 for q in took)
    ends = []
    for bays, group, y in RUNS:
        if taken(bays[0][0]): bays = [(p1, p0, bu) for p0, p1, bu in reversed(bays)]
        for p0, p1, bu in bays:
            post = not taken(p0)
            if post: took.append(p0)
            else: print('RAIL_POSTLESS', round(p0.x), round(p0.z))
            d = (p1 - p0).normalized(); c = (p0 + p1) / 2
            key, fn = bay_key((p1 - p0).length, bu, post); place(key, fn, c.x, c.z, math.degrees(math.atan2(-d.z, d.x)), y=y, group=group)
        ends.append((bays[-1][1], d, group, y))
    for e, d, group, y in ends:
        if not taken(e): took.append(e); place('railpost', FP.rail_post, e.x, e.z, math.degrees(math.atan2(-d.z, d.x)), y=y, group=group)
    RUNS.clear()

def arc_with_gaps(r, gaps, group):
    """full circle at radius r minus angular gaps [(centre, half width deg)]"""
    gs = sorted(((c - h) % 360, (c + h) % 360) for c, h in gaps)
    for k in range(len(gs)):
        a0 = gs[k][1]; a1 = gs[(k + 1) % len(gs)][0]
        if a1 < a0: a1 += 360
        rail_arc(r, a0, a1, group)

def halfang(w, r): return math.degrees(math.asin(w / 2 / r))

ANCHORS = []      # station name GUIs, fishing spots, spawn, boat spawns (written to anchors.json + Lua)
def anchor(name, kind, x, y, z, yaw=0.0, size=(4, 1, 4)):
    ANCHORS.append({'name': name, 'kind': kind, 'pos': [round(x, 2), round(y, 2), round(z, 2)], 'yaw': round(yaw, 1), 'size': list(size)})

TORCH = lambda: FP.tiki_torch(1, 7.0, 10.0)        # every torch stands in the water just off the deck edge: stilt pole to the seabed
def edges():
    G = 'Edges'
    # ring outer edge: gaps at every pad and pier mouth
    og = [(th, halfang(W + .4, R_OUT)) for th, D, W in PADS.values()] + [(th, halfang(PIER_W + .4, R_OUT)) for th, _ in PIERS.values()]
    arc_with_gaps(R_OUT - .35, og, G)
    arc_with_gaps(R_IN + .35, [(th, halfang(SPOKE_W + 1.0, R_IN)) for th in (0, 90, 180, 270)], G)
    arc_with_gaps(R_PLAT - .2, [(th, halfang(SPOKE_W + 1.0, R_PLAT)) for th in (0, 90, 180, 270)], 'Centre')
    for th in (0, 90, 180, 270):                                              # spokes: both sides
        for sx in (-1, 1):
            a = lp(th, 0, sx * (SPOKE_W / 2 - .35), R_PLAT + .2); b = lp(th, 0, sx * (SPOKE_W / 2 - .35), R_IN - .4)
            rail_line(a, b, G)
        for rr in (R_PLAT + 1.2, R_IN - 1.4):                                  # torches at both spoke ends
            for sx in (-1, 1):
                x, z = lp(th, 0, sx * (SPOKE_W / 2 + .9), rr)
                if rr > 40: place('torch', TORCH, x, z, th, y=DECK, group='Torches')
    # pads: two sides + outer front (gaps where piers leave)
    for name, (th, D, W) in PADS.items():
        r0 = R_OUT - 1.0; rc = r0 + D / 2; hw, hd = W / 2 - .35, D / 2 - .35
        for sx in (-1, 1):
            rail_line(lp(th, rc, sx * hw, -hd + 1.4), lp(th, rc, sx * hw, hd), G)
        gaps = [(hw - PIER_W / 2 - .3, hw + PIER_W / 2 + .3)] if name == 'Dock' else []
        if name == 'Spawn': gaps = []
        rail_line(lp(th, rc, -hw, hd), lp(th, rc, hw, hd), G, gaps=gaps)
        for sx in (-1, 1):                                                    # torches where the pad meets the ring
            x, z = lp(th, rc, sx * (W / 2 + 1.2), -hd + .6)
            place('torch', TORCH, x, z, th, y=DECK, group='Torches')
    # piers: sides, end platform with fishing gaps
    for name, (th, rend) in PIERS.items():
        r0 = R_OUT - 1.0; ew, ed = END[name]; re0 = rend - ed
        for sx in (-1, 1):
            rail_line(lp(th, 0, sx * (PIER_W / 2 - .35), R_OUT + .2), lp(th, 0, sx * (PIER_W / 2 - .35), re0 + .5), G)
            x, z = lp(th, 0, sx * (PIER_W / 2 + 1.0), R_OUT + 1.0); place('torch', TORCH, x, z, th, y=DECK, group='Torches')
        hw = ew / 2 - .35
        for sx in (-1, 1):                                                    # end platform: back edges, sides
            rail_line(lp(th, 0, sx * hw, re0 + .35), lp(th, 0, sx * (PIER_W / 2 + .3), re0 + .35), G)
            rail_line(lp(th, 0, sx * hw, re0 + .35), lp(th, 0, sx * hw, rend - .35), G, gaps=[(ed / 2 - 2.2, ed / 2 + 2.2)])
        rail_line(lp(th, 0, -hw, rend - .35), lp(th, 0, hw, rend - .35), G, gaps=[(hw - 3.2, hw + 3.2)] if ew < 24 else [(hw * .45 - 3, hw * .45 + 3), (hw * 1.55 - 3, hw * 1.55 + 3)])
    # dock pier: sides between the slips
    th = 270; rc = R_OUT - 1.0 + PADS['Dock'][1] / 2
    for sx in (-1, 1):
        rail_line(lp(th, rc, sx * (PIER_W / 2 - .35), PADS['Dock'][1] / 2), lp(th, rc, sx * (PIER_W / 2 - .35), DOCK_END - rc), G,
                  gaps=[(16 - PADS['Dock'][1] / 2 - 1, 20 - PADS['Dock'][1] / 2 + 1), (38 - PADS['Dock'][1] / 2 - 1, 42 - PADS['Dock'][1] / 2 + 1)])
    rails_flush()

# ------------------------------------------------------------------ stations + stories
def stations():
    T = DECK
    # ---- spawn plaza (S): arch on the axis, quest board, benches, planters, lifebuoy
    th = 0; rc = R_OUT - 1.0 + PADS['Spawn'][1] / 2
    x, z = lp(th, rc, 0, -PADS['Spawn'][1] / 2 + 3.5); place('arch', FP.welcome_arch, x, z, th, y=T, group='Spawn')
    x, z = lp(th, rc, -15.5, 1.0); place('quest', FP.quest_board, x, z, th - 90, y=T, group='Spawn')
    anchor('QuestBoard', 'station', x, T + 11.0, z, th - 90)
    for sx in (-1, 1):
        for lz in (-6.0, 10.5):
            x, z = lp(th, rc, sx * 18.5, lz); place('planter', lambda: FP.palm_planter(1), x, z, th, y=T, group='Spawn'); reserve(x, z, 3)
        x, z = lp(th, rc, sx * 9.5, 12.0); place('bench', FP.bench, x, z, th + 180, y=T, group='Spawn')
    x, z = lp(th, rc, 16.5, 4.0); place('lifebuoy', FP.lifebuoy_stand, x, z, th + 90, y=T, group='Spawn')
    x, z = lp(th, rc, 13.0, -3.5); place('buoys1', lambda: FP.buoy_stack(1), x, z, 30, y=T, group='Stories')
    sx_, sz_ = lp(th, rc, 0, 3.0)
    anchor('SpawnLocation', 'spawn', sx_, T + .5, sz_, 0, (12, 1, 12))
    # ---- rod shop (SW)
    th = 315; rc = R_OUT - 1.0 + PADS['Rod'][1] / 2
    x, z = lp(th, rc, 0, 2.5); place('rodshop', FP.rod_shop, x, z, th, y=T, group='RodShop')
    anchor('RodShop', 'station', *lp_y(th, rc, 0, 2.5, T + 23.0), th)
    x, z = lp(th, rc, -10.5, -5.0); place('rodrack', lambda: FP.rod_rack(1), x, z, th + 25, y=T, group='RodShop')
    x, z = lp(th, rc, 10.5, -6.5); place('rodrack', lambda: FP.rod_rack(1), x, z, th - 30, y=T, group='RodShop')
    x, z = lp(th, rc, 11.0, 6.0); place('barrels1', lambda: FP.barrels(1), x, z, th + 40, y=T, group='Stories')
    # ---- bait shop (SE)
    th = 45; rc = R_OUT - 1.0 + PADS['Bait'][1] / 2
    x, z = lp(th, rc, 0, 2.0); place('baitshop', FP.bait_shop, x, z, th, y=T, group='BaitShop')
    anchor('BaitShop', 'station', *lp_y(th, rc, 0, 2.0, T + 25.0), th)
    x, z = lp(th, rc, 9.5, -5.5); place('cooler', lambda: FP.cooler(1, 'lime'), x, z, th + 20, y=T, group='BaitShop')
    x, z = lp(th, rc, -10.0, 6.0); place('net1', lambda: FP.net_pile(1), x, z, th + 70, y=T, group='Stories')
    x, z = lp(th, rc, -10.5, -5.0); place('crates1', lambda: FP.crate_stack(1), x, z, th - 15, y=T, group='Stories')
    # ---- fish market / sell (E)
    th = 90; rc = R_OUT - 1.0 + PADS['Market'][1] / 2
    x, z = lp(th, rc, 0, 1.5); place('market', FP.fish_market, x, z, th, y=T, group='FishMarket')
    anchor('FishMarket', 'station', *lp_y(th, rc, 0, 1.5, T + 24.0), th)
    anchor('SellCounter', 'sell', *lp_y(th, rc, 0, -6.5, T + 3.0), th, (19, 4, 3))
    x, z = lp(th, rc, -14.4, 4.0); place('dryrack', lambda: FP.drying_rack(1), x, z, th + 90, y=T, group='FishMarket')
    x, z = lp(th, rc, 14.0, -8.0); place('crates1', lambda: FP.crate_stack(1), x, z, th + 200, y=T, group='Stories')
    x, z = lp(th, rc, 14.5, 9.0); place('barrels1', lambda: FP.barrels(1), x, z, th + 100, y=T, group='Stories')
    # ---- boat dock (W)
    th = 270; rc = R_OUT - 1.0 + PADS['Dock'][1] / 2
    x, z = lp(th, rc, -7.0, 1.5); place('boathouse', FP.boat_house, x, z, th + 90 - 90, y=T, group='BoatDock')
    anchor('BoatDock', 'station', *lp_y(th, rc, -7.0, 1.5, T + 26.0), th)
    x, z = lp(th, rc, 8.5, -4.0); place('buoys1', lambda: FP.buoy_stack(1), x, z, 10, y=T, group='Stories')
    x, z = lp(th, rc, 10.0, 5.5); place('net1', lambda: FP.net_pile(1), x, z, 100, y=T, group='Stories')
    for k, (lz, sx, key, fn) in enumerate(((29.0, -1, 'skiff', FP.skiff), (29.0, 1, 'mboat', FP.motor_boat))):
        x, z = lp(th, rc, sx * (PIER_W / 2 + 4.5), lz)
        place(key, fn, x, z, th + 180, y=WATER, group='Boats')
        anchor('BoatSpawn%d' % (k + 1), 'boat', x, WATER + 1, z, th + 180, (5, 2, 12))
    x, z = lp(th, rc, 0, DOCK_END - rc - 1.5); place('lifebuoy', FP.lifebuoy_stand, x, z, th + 180, y=T, group='BoatDock')
    # ---- centre: the hero + fish index wall
    place('dome', FP.aquarium_dome, 0, 0, 180, y=DECK, group='Hero')
    place('lighthouse', FP.lighthouse, 0, 0, 0, y=DECK, group='Hero')
    reserve(0, 0, 33)
    anchor('Aquarium', 'station', 0, DECK + 30.0, 24.0, 180)
    x, z = pos(318, 26.5); place('index', FP.fish_index_wall, x, z, 318 + 180, y=DECK, group='Hero')
    anchor('FishIndex', 'station', x, DECK + 13.5, z, 318 + 180)
    for a in (42, 138, 222):
        x, z = pos(a, 27.0); place('planterc', lambda: FP.palm_planter(2), x, z, a, y=DECK, group='Centre')
    # ---- fishing spots: pier ends (gaps in the end rails) + marker buoys out in the water
    for name, (th, rend) in PIERS.items():
        ew, ed = END[name]; re0 = rend - ed
        spots = [(0, rend)] if ew < 24 else [(-ew * .275, rend), (ew * .275, rend)]
        spots += [(-ew / 2, rend - ed / 2), (ew / 2, rend - ed / 2)]
        for i, (lx, lz) in enumerate(spots):
            x, z = lp(th, 0, lx, lz); anchor('%s_Spot%d' % (name, i + 1), 'fishing', x, DECK + .5, z, th, (6, 1, 3))
        for sx in (-1, 1):
            x, z = lp(th, 0, sx * (ew / 2 - 2.0), rend - 2.5); place('rodholder', lambda: FP.rod_holder(1), x, z, th + 180 + (20 * sx), y=DECK, group='FishingSpots')
        x, z = lp(th, 0, 0, re0 + 3.0)
        if ew >= 24:
            place('palapa', lambda: FP.umbrella(1), *lp(th, 0, -8.5, re0 + 6.0), y=DECK, group='FishingSpots')
            place('palapa', lambda: FP.umbrella(1), *lp(th, 0, 8.5, re0 + 6.0), y=DECK, group='FishingSpots')
            place('bench', FP.bench, *lp(th, 0, -8.5, re0 + 2.6), th + 180, y=DECK, group='FishingSpots')
            place('cooler2', lambda: FP.cooler(2, 'teal'), *lp(th, 0, 8.5, re0 + 2.4), th + 15, y=DECK, group='FishingSpots')
        else:
            place('palapa', lambda: FP.umbrella(1), *lp(th, 0, -5.0, re0 + 4.0), y=DECK, group='FishingSpots')
            place('bench', FP.bench, *lp(th, 0, 4.5, re0 + 3.2), th + 180, y=DECK, group='FishingSpots')
        for i, (lx, lz, col) in enumerate(((-14, rend + 16, 'yellow'), (16, rend + 24, 'red'))):
            x, z = lp(th, 0, lx, lz); place('buoy_' + col, (lambda c=col: FP.marker_buoy(1, c)), x, z, 0, y=WATER, group='FishingSpots')
            anchor('%s_Deep%d' % (name, i + 1), 'fishzone', x, WATER, z, 0, (24, 1, 24))
    # lagoon spots (beginners): beside the S and E spokes
    for th, sx in ((0, 1), (90, -1), (180, 1)):
        x, z = lp(th, 0, sx * 12, 45.0); place('buoy_yellow', lambda: FP.marker_buoy(1, 'yellow'), x, z, 0, y=WATER, s=.7, group='FishingSpots')
        anchor('Lagoon_%d' % th, 'fishzone', x, WATER, z, 0, (14, 1, 14))

def lp_y(th, rc, lx, lz, y):
    x, z = lp(th, rc, lx, lz); return (x, y, z)

PALMS = {'p1': (lambda: FP.palm(1, 18.0, 4.0), 5), 'p2': (lambda: FP.palm(2, 22.0, 6.0), 5), 'p3': (lambda: FP.palm(3, 15.0, 3.0), 4),
         'p4': (lambda: FP.palm(4, 20.0, 7.0), 5)}
def nature(rng):
    # inner lagoon: two tiny islets with a palm each + coral heads on the sand (seen through the water)
    for th, r in ((45, 45.5), (225, 46.0)):
        x, z = pos(th, r)
        place('reefrock2', lambda: FP.reef_rock(2, 3.4), x, z, rng.uniform(0, 360), y=-1.6, s=1.2, group='Lagoon')
        place('p3', PALMS['p3'][0], x + .5, z, rng.uniform(0, 360), y=1.2, group='Lagoon')
    for k in range(18):
        for _ in range(30):
            r = rng.uniform(36, 55) if k < 9 else rng.uniform(74, 140); a = rng.uniform(0, 360); x, z = pos(a, r)
            if r > 72 and any(abs(((a - th + 180) % 360) - 180) < 14 for th in [0, 45, 90, 135, 180, 225, 270, 315]): continue
            if not free(x, z, 3): continue
            c = rng.choice(('cr', 'cy', 'ct', 'bc', 'bc2'))
            fn = {'cr': lambda: FP.coral_branch(1, 'red', 1.0, 1), 'cy': lambda: FP.coral_branch(2, 'yellow', 1.0, 1), 'ct': lambda: FP.coral_branch(3, 'teal', 1.0, 1),
                  'bc': lambda: FP.brain_coral(1, 1.6, 'yellow'), 'bc2': lambda: FP.brain_coral(2, 1.4, 'lime')}[c]
            place('coral_' + c, fn, x, z, rng.uniform(0, 360), s=rng.uniform(1.0, 1.8), sink=.2, group='Coral'); reserve(x, z, 3); break
    # reef islets: palm groves (odd clusters), rocks at the waterline, shrubs, a hammock on one
    for i, (th, r, a, b, sd) in enumerate(ISLETS):
        cx, cz = pos(th, r); t = tangent(th); u = outward(th)
        n = 3 + (a > 38) * 2
        if i == 2: reserve(cx, cz, 9)                                         # the hammock grove: keep palms + shrubs out
        for k in range(n):
            lx = rng.uniform(-a * .55, a * .55); lz = rng.uniform(-b * .35, b * .35)
            x, z = cx + t.x * lx + u.x * lz, cz + t.z * lx + u.z * lz
            if not free(x, z, 3): continue
            key = rng.choice(list(PALMS)); place(key, PALMS[key][0], x, z, rng.uniform(0, 360), s=rng.uniform(.85, 1.2), group='Islets'); reserve(x, z, 3)
            for q in range(2):                                                # fern / grass tufts round the palm foot
                aa = rng.uniform(0, math.tau); dd = rng.uniform(1.6, 3.2)
                place('tuft%d' % (q % 2 + 1), (lambda q=q: FP.grass_tuft(q % 2 + 1)), x + math.cos(aa) * dd, z + math.sin(aa) * dd, rng.uniform(0, 360), s=rng.uniform(.8, 1.3), group='Islets')
        for k in range(2):
            lx = rng.uniform(-a * .6, a * .6); lz = rng.uniform(-b * .3, b * .3)
            x, z = cx + t.x * lx + u.x * lz, cz + t.z * lx + u.z * lz
            if free(x, z, 2): place('shrub%d' % (k % 2 + 1), (lambda k=k: FP.tropical_shrub(k % 2 + 1, 2.2)), x, z, rng.uniform(0, 360), group='Islets'); reserve(x, z, 2)
        for k in range(4):                                                    # rocks on the beach line
            ang = rng.uniform(0, math.tau); lx = math.cos(ang) * a * .95; lz = math.sin(ang) * b * .95
            x, z = cx + t.x * lx + u.x * lz, cz + t.z * lx + u.z * lz
            place('reefrock%d' % (k % 2 + 1), (lambda k=k: FP.reef_rock(k % 2 + 1, 2.6)), x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.5), sink=.6, group='Islets')
        if i == 2:
            x, z = cx, cz; place('hammock', lambda: FP.hammock_palms(1), x, z, th, group='Islets')
    for th, r, h, rr, sd in ((95, 300, 38, 9, 1), (182, 296, 46, 11, 2), (262, 292, 32, 8, 3), (20, 310, 28, 7, 4)):
        x, z = pos(th, r); place('stack%d' % sd, (lambda h=h, rr=rr, sd=sd: FP.sea_stack(sd, h, rr)), x, z, rng.uniform(0, 360), y=H(x, z) - 1.0, group='Islets')
    for k, (th, d, y, s) in enumerate(((150, 700, 120, 2.2), (200, 820, 150, 2.8), (240, 650, 110, 1.8), (110, 760, 135, 2.4), (60, 720, 125, 2.0), (300, 800, 140, 2.5), (340, 900, 160, 2.6))):
        x, z = pos(th, d); place('cloud%d' % (k % 3 + 1), (lambda k=k: FP.cloud(k % 3 + 1)), x, z, rng.uniform(0, 360), y=y, s=s, group='Sky')

def build():
    ground(); water(); horizon(); islet_grass(); hardscape()
    for loc, _t, _f in SHOTS.values(): reserve(loc[0], loc[2], 4)
    for th in (0, 45, 90, 135, 180, 225, 270, 315): reserve(*pos(th, 90), 18)
    edges(); stations(); nature(random.Random(21))

# ------------------------------------------------------------------ look: bright tropical morning
def look():
    w = bpy.data.worlds.new('Tropic'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.5, .82, 1.0, 1)            # pale cyan horizon
    cr.elements[1].position = .55; cr.elements[1].color = (.03, .2, .78, 1)           # azure zenith
    e = cr.elements.new(.1); e.color = (.32, .66, 1.0, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .9
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .12; b.inputs['Roughness'].default_value = .92
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.6; sun.data.color = (1.0, .95, .86); sun.data.angle = math.radians(1.5)
    el = math.radians(40); az = math.radians(112)                                     # from the east-south-east
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .9; fill.data.color = (.6, .8, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.4, .8, .3)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    try: SC.eevee.shadow_pool_size = '1024'
    except Exception: pass
    for k, v in (('volumetric_tile_size', '8'), ('volumetric_end', 2500.0), ('volumetric_start', .5), ('volumetric_samples', 48)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (3600, 3600, 600); hz.location = (0, 0, 250); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree
    vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .000035
    pv.inputs['Color'].default_value = (.5, .78, .95, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm)
    hz.visible_shadow = False

MATERIALS = {'deck': 'WoodPlanks', 'wood': 'Wood', 'bamboo': 'Wood', 'thatch': 'Fabric', 'sand': 'Sand', 'coral': 'Limestone',
             'rock': 'Basalt', 'palm': 'LeafyGrass', 'water': 'Glass', 'paint': 'SmoothPlastic', 'red': 'SmoothPlastic',
             'yellow': 'SmoothPlastic', 'teal': 'SmoothPlastic', 'lime': 'SmoothPlastic', 'metal': 'Metal'}
MAT_OVERRIDES = {'Horizon_Islands': 'SmoothPlastic', 'Cloud': 'SmoothPlastic', 'Ground_Seabed': {'water': 'Sand'}}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Glass'] = (None, 0, 0, .25, 0, .2)
    RM.LOOK['Sand'] = ('noise', 14.0, .12, .95, 0, .1)
    RM.LOOK['Fabric'] = ('wave', 2.5, .3, .95, 0, .05)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)
    m = bpy.data.materials.get('RBX_Glass')                                   # see-through glass + water in the preview
    if m:
        bsdf = m.node_tree.nodes['Principled BSDF']; bsdf.inputs['Alpha'].default_value = .42
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
        try: m.use_backface_culling = False
        except Exception: pass

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 8000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SPAWN = (0.0, DECK, 87.0)
SHOTS = {   # vertical FOV (Roblox-style)
    'map_beauty.png': ((-46, 24, 205), (0, 16, 0), 38),
    'map_overview.png': ((-230, 190, 250), (0, 0, 10), 40),
    'map_top.png': ((0, 620, 1), (0, 0, 0), 46),
    'map_spawn.png': ((SPAWN[0], SPAWN[1] + 5.5, SPAWN[2] + 6), (0, 16, 0), 60),
    'map_market.png': ((56, 13, 30), (92, 8, 0), 55),
    'map_shops.png': ((0, 16, 46), (-30, 8, 70), 60),
    'map_dock.png': ((-82, 16, -34), (-112, 2, 2), 55),
    'map_pier.png': ((14, 11, -120), (0, 5, -152), 55),
    'map_hero.png': ((18, 8, 46), (0, 22, 0), 60),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
           'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()}},
          open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'water_y': WATER, 'deck_y': DECK}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'fish_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATIC_TRIS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
