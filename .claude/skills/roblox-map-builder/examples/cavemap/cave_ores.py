# Glowroot Caverns ORE v2 (user: "make ores look way better"). Imported at the end of cave_props3; redefines ore_pile and
# mine_cart's load. Reference: real ore specimens (dark host rock with metallic patches, blocky crystal inclusions,
# druses of prisms radiating from one root). Build:
#   - angular host lumps packed into a real heap (graded: big at the core and foot, small on top, chips spilled round it)
#   - ore seams painted per face from a 3D noise (the kind's light colour = metallic patch) + an iron-dark rim tone
#   - blocky ore crystals (tiny rotated cubes) set into the lump faces, a few of them glowing
#   - 2 druse clusters: 7-9 banded crystals fanning from one root, graded tall-to-short
#   - a real shovel (D grip, shaft, dished blade) driven in, a pickaxe leaning on the heap
from cave_props2 import *
import cave_props2 as _P2
from mathutils import Vector, noise as MN
import math, random, bmesh

ORE_COL = {'amber': 'crysA', 'cyan': 'crysC', 'violet': 'crysV'}

def _lump(rng, r, flat=.82):
    """angular broken-rock lump: a hull of few points (big flat fracture faces), slightly squashed"""
    pts = []
    for k in range(rng.randint(12, 15)):
        u = rng.uniform(-1, 1); a = rng.uniform(0, math.tau); s = math.sqrt(1 - u * u)
        q = rng.uniform(.75, 1.0)
        pts.append(Vector((s * math.cos(a) * r * q, u * r * flat * q, s * math.sin(a) * r * q)))
    return hull(pts)

def mound(P, cx, cz, y0, rx, rz, h, seed, kind, n=18, rings=5):
    """the heap's hidden-gap filler: a lumpy dome of broken rock with ore-seam faces (bottom open, sits on y0)"""
    rng = random.Random(seed); bm = bmesh.new(); rows = []
    for j in range(rings + 1):
        t = j / rings; rr = math.cos(t * math.pi / 2); yy = math.sin(t * math.pi / 2) * h
        if j == rings: rows.append([bm.verts.new((cx, y0 + h, cz))]); break
        rows.append([bm.verts.new((cx + math.cos(a) * rx * rr * rng.uniform(.85, 1.08), y0 + yy + rng.uniform(-.12, .12) * h * (j > 0),
                                   cz + math.sin(a) * rz * rr * rng.uniform(.85, 1.08))) for a in [i * math.tau / n for i in range(n)]])
    for A, Bq in zip(rows, rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            if len(Bq) == 1: bm.faces.new((A[i], A[j], Bq[0]))
            else: bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.normal_update()
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    uR, uO = PAL.u('rock'), PAL.u(ORE_COL[kind])
    def sh(f):
        c = f.calc_center_median(); n_ = MN.noise(c * 1.6 + Vector((seed, 0, 0))) * .5 + .5
        return [(uO, .66)] * len(f.loops) if n_ > .68 else [(uR, .26 + .2 * f.normal.y)] * len(f.loops)
    P.add(bm, sh)

def ore_lump(P, pos, r, seed, kind, yaw=0.0, pitch=0.0, nugget=True, glow_share=.3, rich=.5):
    """one ore lump: host rock faces + metallic ore-seam faces (noise) + blocky ore crystals set into its faces"""
    rng = random.Random(seed); col = ORE_COL[kind]; gk = CRYS[kind][1]
    bm = _lump(rng, r); T(bm, (0, 0, 0), yaw=yaw, pitch=pitch); bmesh.ops.translate(bm, vec=Vector(pos), verts=bm.verts)
    bm.normal_update()
    off = Vector((seed * 1.7, seed * .3, -seed * 2.1)); thr = .62 - rich * .14
    seams = []
    uR, uO = PAL.u('rock'), PAL.u(col)
    def shade(f):
        c = f.calc_center_median(); n = MN.noise((c + off) * (1.3 / max(r, .3))) * .5 + .5
        if n > thr:
            seams.append(f); return [(uO, min(.94, .62 + (n - thr) * 1.2 + .1 * f.normal.y))] * len(f.loops)
        v = .3 + .22 * max(0, f.normal.y) + rng.uniform(-.05, .05)
        return [(uR, max(.06, v - (.08 if n > thr - .08 else 0)))] * len(f.loops)
    faces = list(bm.faces); sh = [shade(f) for f in faces]
    cands = [(f.calc_center_median().copy(), f.normal.copy(), f.calc_area()) for f in seams if f.calc_area() > (r * .3) ** 2]
    P.add(bm, lambda f, it=iter(sh): next(it))
    if not nugget: return
    for c, n, a in cands[:2]:
        for k in range(rng.randint(1, 2)):
            s = r * rng.uniform(.12, .22)
            cube = box((s, s, s), 0)
            T(cube, (0, 0, 0), yaw=rng.uniform(0, 90), pitch=rng.uniform(0, 45), roll=rng.uniform(0, 45))
            t = n.orthogonal().normalized(); b2 = n.cross(t)
            p = c + t * rng.uniform(-.3, .3) * math.sqrt(a) + b2 * rng.uniform(-.3, .3) * math.sqrt(a) + n * s * .15
            bmesh.ops.translate(cube, vec=p, verts=cube.verts)
            if rng.random() < glow_share: P.gadd(cube, gk)
            else: P.add(cube, FS(col, .78, .2, .08, k + seed))

def druse(P, root, kind, seed, n=8, scale=1.0, lean=(18, 46), toward=None):
    """crystal cluster: n banded crystals fanning from one root, tallest at the centre"""
    rng = random.Random(seed); base_yaw = rng.uniform(0, 360) if toward is None else toward
    add_crystal(P, root, .34 * scale, 2.4 * scale, seed, kind, lean=rng.uniform(4, 12), yaw=base_yaw, glow_from=.38)
    for k in range(n - 1):
        a = base_yaw + k * 360 / (n - 1) + rng.uniform(-18, 18)
        h = rng.uniform(.8, 1.8) * scale; rr = rng.uniform(.14, .26) * scale
        p = (root[0] + math.cos(math.radians(a)) * .25 * scale, root[1] - .05, root[2] + math.sin(math.radians(a)) * .25 * scale)
        add_crystal(P, p, rr, h, seed * 7 + k, kind, lean=rng.uniform(*lean), yaw=-a - 90, glow_from=.34)

def shovel(P, foot, yaw=30, tilt=-22):
    """square-mouth shovel: dished steel blade + socket, ash shaft, D grip; foot = blade tip (pushed into the heap)"""
    s = _P2  # namespace only
    L = 4.4; d = Vector((math.sin(math.radians(yaw)) * math.sin(math.radians(-tilt)), math.cos(math.radians(tilt)), math.cos(math.radians(yaw)) * math.sin(math.radians(-tilt))))
    f = Vector(foot); top = f + d * L
    blade = box((1.0, 1.25, .06), .02)
    for v in blade.verts: v.co.z += .12 * (v.co.x / .5) ** 2 - .06              # dish
    T(blade, (0, .62, 0), yaw=yaw, pitch=tilt); bmesh.ops.translate(blade, vec=f, verts=blade.verts); P.add(blade, FS('iron', .55, .25, .05))
    P.add(logp(f + d * 1.15, f + d * 1.75, .1, 8, .07), FS('iron', .42))
    P.add(logp(f + d * 1.7, top, .07, 8), W('wood', .62))
    side = Vector((math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw))))
    g = [top - side * .32, top + d * .5 - side * .32, top + d * .62, top + d * .5 + side * .32, top + side * .32]
    P.add(tube(g, .05, 6, cap0=False, cap1=False), FS('iron', .45))
    P.add(logp(top + d * .5 - side * .26, top + d * .5 + side * .26, .07, 6), W('wood', .55))

def pickaxe(P, head, yaw=0):
    """pick resting with its head on the ground and the haft leaning on the heap"""
    h = Vector(head); dy = Vector((math.sin(math.radians(yaw)) * .55, .82, math.cos(math.radians(yaw)) * .55)).normalized()
    top = h + dy * 3.3
    P.add(logp(h, top, .08, 8, .07), W('wood', .6))
    side = Vector((math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw))))
    tips = [h - side * 1.2 + Vector((0, -.25, 0)), h - side * .5 + Vector((0, .05, 0)), h, h + side * .5 + Vector((0, .05, 0)), h + side * 1.2 + Vector((0, -.2, 0))]
    P.add(tube(tips, [.03, .11, .15, .11, .05], 6), FS('iron', .5))
    P.add(logp(h - dy * .2, h + dy * .3, .15, 6), FS('iron', .4))

def ore_pile(kind='amber', seed=3):
    """heap of broken ore: graded angular host lumps with metallic seams and set-in ore crystals, two glowing druses,
    spilled chips, a shovel driven in and a pickaxe leaning on it. ~6 across, ~3 tall."""
    rng = random.Random(seed); P = Prop('OrePile%s' % kind.capitalize())
    R = 3.0
    mound(P, 0, 0, 0, R * .92, R * .92, 2.2, seed, kind)
    lumps = []
    for k in range(20):                                                  # heap: lumps packed on a mound profile
        a = rng.uniform(0, math.tau); d = R * math.sqrt(rng.uniform(0, 1))
        hgt = 2.2 * math.cos(min(1, d / (R * .92)) * math.pi / 2) + .1
        r = lerp(1.3, .65, d / R) * rng.uniform(.8, 1.1)
        lumps.append((hgt, a, d, r, k))
    for hgt, a, d, r, k in sorted(lumps):
        ore_lump(P, (math.cos(a) * d, max(r * .3, hgt - r * .2), math.sin(a) * d), r, seed * 31 + k, kind, yaw=rng.uniform(0, 360),
                 pitch=rng.uniform(-25, 25), nugget=k % 3 == 0, rich=.62 if hgt > 1.2 else .45)
    for k in range(6):                                                   # chips spilled round the foot
        a = rng.uniform(0, math.tau); d = R * rng.uniform(.95, 1.3); r = rng.uniform(.2, .36)
        ore_lump(P, (math.cos(a) * d, r * .25, math.sin(a) * d), r, seed * 53 + k, kind, yaw=rng.uniform(0, 360), nugget=False, rich=.3)
    druse(P, (.3, 2.5, -.4), kind, seed * 3, n=7, scale=.85)
    a = 2.4; druse(P, (math.cos(a) * 1.9, 1.15, math.sin(a) * 1.9), kind, seed * 5, n=4, scale=.6, lean=(30, 60), toward=-math.degrees(a) - 90)
    shovel(P, (-1.2, 1.9, .9), yaw=35, tilt=-24)
    pickaxe(P, (3.2, .25, 1.4), yaw=200)
    return P

def cart_load(P, load, rng):
    """v2 load: lumps packed into the tub mouth (heaped in the middle), seams + set-in crystals, a druse on top"""
    mound(P, 0, 0, 3.4, 1.85, 2.4, 1.0, 91 + len(load), load)
    for k in range(10):
        a = rng.uniform(0, math.tau); d = math.sqrt(rng.uniform(0, 1))
        x, z = math.cos(a) * d * 1.5, math.sin(a) * d * 2.0
        r = lerp(.9, .55, d) * rng.uniform(.85, 1.1)
        ore_lump(P, (x, 3.45 + math.cos(d * math.pi / 2) * 1.0, z), r * .85, 400 + k * 13 + len(load), load, yaw=rng.uniform(0, 360), pitch=rng.uniform(-20, 20), nugget=k % 2 == 0, rich=.6)
    druse(P, (.2, 4.4, .3), load, 77 + len(load), n=4, scale=.55, lean=(20, 50))
_P2.cart_load = cart_load
