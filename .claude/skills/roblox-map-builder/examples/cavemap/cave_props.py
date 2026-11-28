# Glowroot Caverns - prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Hanging props (stalactites, glow vines, falls lip) have their origin at the TOP and grow down (-Y).
# Theme: a mining hub carved into a huge cavern: layered plum-grey limestone, banded crystal columns erupting from
# cracked geodes (cyan / violet / amber), bioluminescent fungi, glowing root vines, timber mine sets, rails and carts.
# Machinery (Prop, materials, to_kit) from the skill's grove module, T / lathe / torus / sag from the medieval example,
# painted atlas via valleylake's paint.py (cave_paint.py). Every PROP here is new.
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix, noise as MN
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, hull, rock_pts, nz, clamp, ngon_prism, bevel

import cave_palette as CP
PAL = Palette(CP.BASE)
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
import cave_paint
cave_paint.install(G, PAL)
GLOW = {k: v[0] for k, v in CP.GLOW.items()}
G.GLOW.clear(); G.GLOW.update(GLOW)
G.GLOW_E.clear(); G.GLOW_E.update({k: v[1] for k, v in CP.GLOW.items()})
Prop, S = G.Prop, G.S
T, lathe, torus, sag = B.T, B.lathe, B.torus, B.sag
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
CRYS = {'cyan': ('crysC', 'cyan'), 'violet': ('crysV', 'violet'), 'amber': ('crysA', 'amber')}

# ------------------------------------------------------------------ shading
def V(col, y0, y1, a, b, nk=.12, ns=None, seed=0, amp=.08):
    """per-vertex height gradient (a low -> b high) + normal lift + noise: soft painterly ramps"""
    u = PAL.u(col)
    def f(face):
        out = []
        for l in face.loops:
            p = l.vert.co; n = l.vert.normal
            t = clamp((p.y - y0) / (y1 - y0)) if y1 != y0 else .5
            v = lerp(a, b, t) + nk * n.y
            if ns: v += (nz(p.x, p.y, p.z, ns, seed) - .5) * amp * 2
            out.append((u, clamp(v, .04, .96)))
        return out
    return f
def FS(col, base=.5, up=.25, jit=.06, seed=0): return S(col, base=base, up=up, jit=jit, seed=seed)
def flat(col, v): u = PAL.u(col); return lambda f: [(u, v)] * len(f.loops)

def rim_shade(bm):
    """per-vertex convexity: > 0 convex edge (lit rim), < 0 crevice"""
    bm.normal_update(); out = {}
    for v in bm.verts:
        if not v.link_edges: out[v] = 0; continue
        out[v] = -sum(v.normal.dot((e.other_vert(v).co - v.co).normalized()) for e in v.link_edges) / len(v.link_edges)
    return out

def RS(col, y0, y1, a, b, conv, nk=.16, ns=None, seed=0, amp=.07, hi=.3, lo=.3):
    u = PAL.u(col)
    def f(face):
        res = []
        for l in face.loops:
            p = l.vert.co; n = l.vert.normal; t = clamp((p.y - y0) / (y1 - y0)) if y1 != y0 else .5
            v = lerp(a, b, t) + nk * n.y
            c = conv.get(l.vert, 0)
            if c > 0 and n.y > -.3: v += hi * min(1, c * 4)
            elif c < 0: v -= lo * min(1, -c * 4)
            if n.y < -.3: v -= .1
            if ns: v += (nz(p.x, p.y, p.z, ns, seed) - .5) * amp * 2
            res.append((u, clamp(v, .04, .96)))
        return res
    return f

def dot(c, r, sq=.55, n=6):
    """cheap lens / bead (glow spots, bulbs, nodules): ~4n triangles"""
    return T(lathe([(0, -r * sq), (r, -r * sq * .2), (r * .7, r * sq * .6), (0, r * sq)], n=n), c)

def jitter(bm, amp, sc, seed=0):
    """low-frequency noise displacement along vertex normals (organic surfaces)"""
    bm.normal_update(); o = Vector((seed * 3.1, seed * 1.7, -seed * 2.3))
    for v in bm.verts: v.co += v.normal * (MN.noise(v.co / sc + o) * amp)
    bm.normal_update(); return bm

# ------------------------------------------------------------------ layered rock (the cave signature)
def strata_mass(sx, sy, sz, seed, k=8, n=3.2, layers=4, pinch=.13, shear=.06, lump=.14, taper=.1, flatb=.8, top_tilt=.25):
    """rounded rock built from stacked BEDS: a subdivided cube pushed onto a superellipsoid (|x|^n+|y|^n+|z|^n = 1),
    lumpy along the radial direction, then every bed bulges in its middle and pinches at its seams (smooth notch), each
    bed slightly sheared sideways and the top plane tilted: reads as layered sedimentary rock, never as a faceted
    lump. Centre at (0, 0, 0), flat bedded bottom at -flatb."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=k - 1, use_grid_fill=True)
    rng = random.Random(seed); off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    SH = [Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * shear for _ in range(layers + 1)]
    tilt = Vector((rng.uniform(-1, 1) * top_tilt, 1, rng.uniform(-1, 1) * top_tilt)).normalized()
    for v in bm.verts:
        p = v.co.copy()
        d = (abs(p.x) ** n + abs(p.y) ** n + abs(p.z) ** n) ** (1 / n); q = p / d
        r = q.normalized()
        q = q * (1 + lump * (MN.noise(r * 1.3 + off) + .5 * MN.noise(r * 2.8 - off)))
        dd = q.dot(tilt) - .86                                                  # soft-flattened tilted top
        if dd > 0: q = q - tilt * dd * .85
        q.y = max(q.y, -flatb)
        h = (q.y + 1) / 2 * layers; i = max(0, min(layers - 1, int(h))); f = min(1.0, max(0.0, h - i))
        notch = (1 - pinch * (1 - math.sin(f * math.pi) ** .6))
        sh = SH[i].lerp(SH[i + 1], smooth(f))
        t = (q.y + 1) / 2
        q.x = q.x * notch * (1 - taper * t) + sh.x; q.z = q.z * notch * (1 - taper * t) + sh.z
        v.co = Vector((q.x * sx, q.y * sy, q.z * sz))
    bm.normal_update()
    return bm

def moss_cap(bm, thick, thr=.5, seed=0, droop=1.0):
    """thick moss shell over the up-facing part of bm, closed by a drooping skirt"""
    bm.normal_update(); bm.verts.index_update()
    rng = random.Random(seed); off = rng.uniform(0, 100)
    up = {v.index: v.normal.y > thr + MN.noise(Vector((v.co.x * .09 + off, v.co.y * .09, v.co.z * .09))) * .3 for v in bm.verts}
    faces = [f for f in bm.faces if all(up[v.index] for v in f.verts)]
    out = bmesh.new(); NV = {}; IV = {}
    def nv(v):
        if v.index not in NV: NV[v.index] = out.verts.new(v.co + v.normal * thick)
        return NV[v.index]
    for f in faces: out.faces.new([nv(v) for v in f.verts])
    sel = set(faces)
    for f in faces:
        for e in f.edges:
            if sum(1 for g in e.link_faces if g in sel) != 1: continue
            for v in e.verts:
                if v.index not in IV: IV[v.index] = out.verts.new(v.co - v.normal * .15 * thick - Vector((0, thick * .9 * droop, 0)))
            loop = [l for l in f.loops if l.edge == e][0]; v0, v1 = loop.vert, loop.link_loop_next.vert
            out.faces.new((NV[v1.index], NV[v0.index], IV[v0.index], IV[v1.index]))
    rim = [NV[i] for i in IV] + list(IV.values())
    for _ in range(3): bmesh.ops.smooth_vert(out, verts=rim, factor=.5, use_axis_x=True, use_axis_y=False, use_axis_z=True)
    out.normal_update(); return out

def crystal(r, h, seed, sides=8, lean=0.0, yaw=0.0, base=-.6, glow_from=.42):
    """banded crystal column: chamfered octagon prism, a narrow dark band, then a GLOW upper section ending in a
    chamfered point (flat facet + pyramid). Returns (body bmesh, band bmesh, glow bmesh) in local space."""
    rng = random.Random(seed)
    R = [r * (1.0 if i % 2 == 0 else .82) * rng.uniform(.92, 1.06) for i in range(sides)]
    def ring(bm, k, y):
        return [bm.verts.new((math.cos(i * math.tau / sides + .2) * R[i] * k, y, math.sin(i * math.tau / sides + .2) * R[i] * k)) for i in range(sides)]
    def loft(bm, rings, tip=None):
        for A, Bq in zip(rings, rings[1:]):
            for i in range(sides): j = (i + 1) % sides; bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
        if tip is not None:
            for i in range(sides): j = (i + 1) % sides; bm.faces.new((rings[-1][i], rings[-1][j], tip))
        bm.faces.new(list(reversed(rings[0])))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); return bm
    y1 = h * glow_from
    body = bmesh.new(); loft(body, [ring(body, 1.0, base), ring(body, .98, y1 - .25 * r)])
    band = bmesh.new(); loft(band, [ring(band, 1.04, y1 - .3 * r), ring(band, 1.04, y1 + .08 * r)])
    gl = bmesh.new()
    tip = gl.verts.new((rng.uniform(-.15, .15) * r, h, rng.uniform(-.15, .15) * r))
    loft(gl, [ring(gl, .97, y1), ring(gl, .93, h * .8), ring(gl, .5, h * .93)], tip)
    for bm in (body, band, gl): T(bm, (0, 0, 0), yaw=yaw, pitch=lean)
    return body, band, gl

def add_crystal(P, pos, r, h, seed, kind, lean=0.0, yaw=0.0, glow_from=.42):
    col, gk = CRYS[kind]
    b, bd, g = crystal(r, h, seed, lean=lean, yaw=yaw, glow_from=glow_from)
    for bm in (b, bd, g): bmesh.ops.translate(bm, vec=Vector(pos), verts=bm.verts)
    P.add(b, V(col, pos[1], pos[1] + h * .45, .25, .7, nk=.1)); P.add(bd, FS(col, .14, .1, .03, seed)); P.gadd(g, gk)

def rock_layered(seed=1, w=30.0, h=22.0, d=26.0, k=8, n=3.2, layers=4, moss=True, mthr=.55, name=None, chips=None,
                 shear=.06, lean=0.0, taper=.1):
    """one carved, layered rock: strata_mass bedded 26% below its origin, moss on the top ledges, optional glowing
    crystal chips in the seams, rim highlights on convex edges."""
    P = Prop(name or 'CaveRock%d' % seed)
    bm = strata_mass(w / 2, h / 2, d / 2, seed, k=k, n=n, layers=layers, shear=shear, taper=taper)
    if lean: T(bm, roll=lean)
    bmesh.ops.translate(bm, vec=Vector((0, h / 2 - h * .26, 0)), verts=bm.verts)
    cap = moss_cap(bm, max(.3, min(w, d) * .035), thr=mthr, seed=seed, droop=1.3) if moss else None
    conv = rim_shade(bm)
    P.add(bm, RS('rock', -h * .26, h * .74, .2, .66, conv, ns=max(w, h) * .4, seed=seed), smooth=True)
    if cap: P.add(cap, V('moss', h * .4, h * .74 + 1, .4, .8, ns=max(w, h) * .3, seed=seed + 3), smooth=True)
    if chips:
        rng = random.Random(seed * 7)
        for c in range(6):
            a = rng.uniform(0, math.tau); yy = rng.uniform(.15, .5) * h
            add_crystal(P, (math.cos(a) * w * .42, yy, math.sin(a) * d * .42), rng.uniform(.3, .55), rng.uniform(1.4, 2.6),
                        seed * 11 + c, chips, lean=rng.uniform(30, 60), yaw=-math.degrees(a) - 90)
    return P

ROCK_SPEC = {   # name: (seed, w, h, d, kwargs)
    'CaveRockA': (1, 34, 24, 28, dict(layers=4)),
    'CaveRockB': (2, 22, 40, 20, dict(layers=6, taper=.2, n=3.0)),
    'CaveRockC': (3, 34, 13, 24, dict(layers=3, n=3.8, k=6)),
    'CaveRockD': (4, 15, 12, 14, dict(layers=3, n=2.9, k=5)),
    'CaveRockE': (5, 9, 6, 8, dict(layers=2, n=2.8, moss=False, k=4)),
    'CaveRockF': (6, 26, 30, 24, dict(layers=5, n=3.4, chips='cyan')),
}
ROCKS = {}
for _nm, (_s, _w, _h, _d, _kw) in ROCK_SPEC.items():
    ROCKS[_nm] = (lambda s=_s, w=_w, h=_h, d=_d, kw=_kw, nm=_nm: rock_layered(s, w, h, d, name=nm, **kw))
    if _nm in ('CaveRockA', 'CaveRockB', 'CaveRockC', 'CaveRockF'):          # far / high copies: coarser grid, no chips
        ROCKS[_nm + 'Lo'] = (lambda s=_s, w=_w, h=_h, d=_d, kw=_kw, nm=_nm: rock_layered(s, w, h, d, name=nm + 'Lo', **dict(kw, k=5, chips=None)))
ROCK_DIM = {k: (v[1], v[2], v[3]) for k, v in ROCK_SPEC.items()}
def rock_dim(key): return ROCK_DIM[key.replace('Lo', '')]

# ------------------------------------------------------------------ dripstone (hangs: origin at the TOP)
def drip_profile(L, r, rings, seed):
    """stalactite lathe profile (r, y) from the ceiling (y +.8, embedded) down to the tip at -L: root flare, drip rings"""
    rng = random.Random(seed); prof = [(r * 1.9, .8), (r * 1.7, 0.0), (r * 1.15, -L * .08)]
    for i in range(1, rings + 1):
        t = i / (rings + 1); y = -L * (.08 + .82 * t); rr = r * (1 - t) ** .8
        prof += [(rr * 1.12 * rng.uniform(.95, 1.08), y + L * .02), (rr * .9, y - L * .03)]
    prof += [(r * .08, -L * .97), (0, -L)]
    return prof

def stalactite(seed=1, L=14.0, r=1.6, n=4, name=None, drip=True):
    """hanging dripstone cluster: one long ringed spike + smaller ones off-centre, wet lighter tips, glowing drop"""
    rng = random.Random(seed); P = Prop(name or 'Stalactite%d' % seed)
    for k in range(n):
        if k == 0: x, z, LL, rr = 0, 0, L, r
        else:
            a = rng.uniform(0, math.tau); d = rng.uniform(1.2, 2.2) * r
            x, z, LL, rr = math.cos(a) * d, math.sin(a) * d, L * rng.uniform(.3, .6), r * rng.uniform(.45, .7)
        bm = lathe(drip_profile(LL, rr, 3 if k == 0 else 2, seed * 5 + k), n=9 if k == 0 else 7, a0=rng.uniform(0, 1))
        jitter(bm, rr * .14, rr * 1.4, seed + k)
        T(bm, (x, 0, z), roll=rng.uniform(-4, 4), pitch=rng.uniform(-4, 4))
        P.add(bm, V('rock', -LL, .8, .72, .3, nk=.1, ns=3, seed=seed + k, amp=.06), smooth=True)
        if drip and k == 0:
            g = lathe([(0, -L - .15), (.22, -L - .45), (.16, -L - .75), (0, -L - .95)], n=6); P.gadd(T(g, (x, 0, z)), 'cyan')
    return P

def flowstone_curtain(seed=1, W=12.0, L=10.0):
    """flowstone drapery hanging from the ceiling: a folded sheet with a scalloped lower edge and a rolled rim,
    thick enough to read from both sides. Origin = top centre."""
    rng = random.Random(seed); P = Prop('StalactiteCurtain%d' % seed)
    nx, ny = 22, 7; bm = bmesh.new(); grid_ = {}
    for i in range(nx + 1):
        u = i / nx; x = (u - .5) * W
        z0 = math.sin(u * math.tau * 2.2 + seed) * 1.2 + math.sin(u * math.tau * 5.1) * .35
        bottom = L * (.55 + .45 * (math.sin(u * math.pi) ** .7)) * (1 + .18 * math.sin(u * 27 + seed)) * (.9 if i % 3 else 1.05)
        for j in range(ny + 1):
            t = j / ny; y = .8 - (bottom + .8) * t
            z = z0 * (.4 + .6 * t)
            th = (.9 - .5 * t) * (1 + .25 * math.sin(u * 40))
            grid_[i, j, 0] = bm.verts.new((x, y, z - th / 2)); grid_[i, j, 1] = bm.verts.new((x, y, z + th / 2))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((grid_[i, j, 0], grid_[i + 1, j, 0], grid_[i + 1, j + 1, 0], grid_[i, j + 1, 0]))
            bm.faces.new((grid_[i, j + 1, 1], grid_[i + 1, j + 1, 1], grid_[i + 1, j, 1], grid_[i, j, 1]))
        bm.faces.new((grid_[i, ny, 0], grid_[i + 1, ny, 0], grid_[i + 1, ny, 1], grid_[i, ny, 1]))
    for j in range(ny):
        for i in (0, nx):
            bm.faces.new((grid_[i, j, 0], grid_[i, j + 1, 0], grid_[i, j + 1, 1], grid_[i, j, 1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, V('rock', -L, .8, .78, .34, nk=0, ns=2.5, seed=seed, amp=.08), smooth=True)
    for k in range(5):                                                       # tiny drip spikes along the hem
        u = (k + .5) / 5; x = (u - .5) * W * .9; y = -L * (.55 + .45 * math.sin(u * math.pi) ** .7) * .95
        s = lathe([(.3, .3), (.22, 0), (0, -1.6 - rng.random())], n=6); P.add(T(s, (x, y, math.sin(u * math.tau * 2.2 + seed) * 1.1)), V('rock', y - 2, y, .8, .5))
    return P

def stalagmite(seed=1, H=11.0, r=2.4, n=3, name=None):
    """grounded dripstone: flared, plate-ringed column with a rounded wet cap, plus 1-3 smaller ones, a flowstone foot"""
    rng = random.Random(seed); P = Prop(name or 'Stalagmite%d' % seed)
    foot = lathe([(r * 2.6, -.6), (r * 2.4, .1), (r * 1.6, .55), (r * 1.1, .9), (0, 1.0)], n=12)
    jitter(foot, .25, 2.0, seed); P.add(foot, V('rock', -.6, 1, .35, .55, ns=3, seed=seed), smooth=True)
    for k in range(n):
        if k == 0: x, z, HH, rr = 0, 0, H, r
        else:
            a = rng.uniform(0, math.tau); d = rng.uniform(1.4, 2.0) * r
            x, z, HH, rr = math.cos(a) * d, math.sin(a) * d, H * rng.uniform(.3, .6), r * rng.uniform(.45, .7)
        prof = [(rr * 1.35, -.5), (rr * 1.25, .4)]
        rings = 3 if k == 0 else 2
        for i in range(1, rings + 1):
            t = i / (rings + 1); y = HH * t * .9; w = rr * (1 - t * .75)
            prof += [(w * 1.13, y - HH * .04), (w * .93, y + HH * .03)]
        prof += [(rr * .32, HH * .93), (rr * .18, HH * .99), (0, HH)]
        bm = lathe(prof, n=9 if k == 0 else 7, a0=rng.uniform(0, 1)); jitter(bm, rr * .12, rr * 1.5, seed * 3 + k)
        T(bm, (x, 0, z), roll=rng.uniform(-5, 5), pitch=rng.uniform(-5, 5))
        P.add(bm, V('rock', 0, HH, .3, .74, nk=.12, ns=3, seed=seed + k), smooth=True)
    return P

# ------------------------------------------------------------------ crystals
def geode(kind='cyan', seed=1, name=None):
    """a cracked-open geode: a lumpy rock cup (outer layered rock, broken rim, inner wall lined with tiny painted
    crystal teeth) on a rubble seat, with banded crystal columns erupting from the opening. ~5 tall at scale 1."""
    rng = random.Random(seed); col, gk = CRYS[kind]; P = Prop(name or 'Geode%s' % kind.capitalize())
    R = 4.2
    outer = lathe([(R * .55, -.7), (R * .92, .4), (R * 1.0, 1.6), (R * .96, 2.6), (R * .9, 3.0), (R * .74, 3.1),
                   (R * .7, 2.8), (R * .62, 1.9), (R * .4, 1.3), (0, 1.15)], n=16)
    for v in outer.verts:                                                   # broken rim + lumps
        a = math.atan2(v.co.z, v.co.x)
        if v.co.y > 2.5: v.co.y -= (math.sin(a * 3 + seed) * .5 + .5) * 1.1 + max(0, math.sin(a * 7 - seed)) * .6
    jitter(outer, .35, 1.6, seed)
    conv = rim_shade(outer); P.add(outer, RS('rock', -.7, 3.1, .22, .58, conv, ns=3, seed=seed), smooth=True)
    inner = lathe([(R * .64, 2.2), (R * .55, 1.6), (R * .3, 1.25), (0, 1.2)], n=16)   # glittering inner lining
    T(inner, (0, .02, 0)); P.add(inner, V(col, 1.2, 2.4, .25, .62, ns=1.2, seed=seed, amp=.15), smooth=False)
    for k in range(14):                                                     # inner teeth
        a = k * math.tau / 14 + rng.uniform(-.2, .2); d = R * rng.uniform(.42, .58)
        t = cyl(.22, .9, 4, r2=.0, rot0=a); T(t, (math.cos(a) * d, 1.45 + rng.uniform(0, .5), math.sin(a) * d), pitch=40, yaw=90 - math.degrees(a) + 180)
        P.add(t, FS(col, .7, .2, .1, k))
    for k in range(5):                                                      # rubble seat
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = R * rng.uniform(.95, 1.15)
        b = strata_mass(rng.uniform(.9, 1.4), rng.uniform(.6, .9), rng.uniform(.9, 1.3), seed * 13 + k, k=4, layers=2)
        T(b, (math.cos(a) * d, .25, math.sin(a) * d), yaw=rng.uniform(0, 360)); P.add(b, V('rock', -.6, 1.2, .25, .55), smooth=True)
    add_crystal(P, (.3, 1.0, -.2), 1.15, 7.6, seed * 3, kind, lean=rng.uniform(8, 14), yaw=rng.uniform(0, 360), glow_from=.55)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = rng.uniform(1.1, 1.7)
        add_crystal(P, (math.cos(a) * d, 1.1, math.sin(a) * d), rng.uniform(.6, .9), rng.uniform(3.6, 6.4), seed * 7 + k, kind,
                    lean=rng.uniform(20, 38), yaw=-math.degrees(a) - 90, glow_from=.5)
    for k in range(3):
        a = rng.uniform(0, math.tau); d = rng.uniform(2.0, 2.6)
        add_crystal(P, (math.cos(a) * d, 1.6, math.sin(a) * d), .4, rng.uniform(2.0, 2.8), seed * 17 + k, kind, lean=rng.uniform(35, 50),
                    yaw=-math.degrees(a) - 90, glow_from=.3)
    return P

def crystal_spray(kind='violet', seed=3):
    """wall-foot crystal spray: a layered rock knuckle with a fan of columns all leaning one way (-Z, into the room)"""
    rng = random.Random(seed); P = Prop('CrystalSpray%s' % kind.capitalize())
    b = strata_mass(4.5, 2.6, 3.4, seed, k=6, layers=3); T(b, (0, 1.2, 1.2))
    conv = rim_shade(b); P.add(b, RS('rock', -1.5, 3.6, .22, .6, conv, ns=3, seed=seed), smooth=True)
    for k in range(6):
        x = (k - 2.5) * 1.3 + rng.uniform(-.3, .3)
        h = rng.uniform(5.5, 9.5) if k in (2, 3) else rng.uniform(3.2, 6.0)
        add_crystal(P, (x, 1.0, .6 + rng.uniform(-.4, .4)), rng.uniform(.65, 1.0) if k in (2, 3) else rng.uniform(.45, .7), h, seed * 5 + k, kind,
                    lean=rng.uniform(22, 40), yaw=180 + x * 6)
    return P

def crystal_shards(kind='cyan', seed=4):
    """ground scatter: a pebble bed with 3-5 small glowing points"""
    rng = random.Random(seed); P = Prop('CrystalShards%s' % kind.capitalize())
    for k in range(4):
        a = rng.uniform(0, math.tau); d = rng.uniform(.3, 1.4)
        b = hull(rock_pts((rng.uniform(.4, .7), rng.uniform(.25, .4), rng.uniform(.4, .7)), n=12, seed=seed + k, flat=.3)); T(b, (math.cos(a) * d, .05, math.sin(a) * d))
        P.add(b, FS('rock', .38, .3, .08, k))
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, math.tau); d = rng.uniform(.0, 1.0)
        add_crystal(P, (math.cos(a) * d, 0, math.sin(a) * d), rng.uniform(.18, .32), rng.uniform(.8, 1.8), seed * 3 + k, kind,
                    lean=rng.uniform(5, 35), yaw=rng.uniform(0, 360), glow_from=.25)
    return P

# ------------------------------------------------------------------ bioluminescent fungi
def cap_shape(r, h, seed, kind='dome'):
    nc = 14 if r > 2 else 9; ng = 28 if r > 2 else 12
    """mushroom cap (lathe): rolled rim lip, domed/bell top. Returns (top bmesh, gill bmesh) built at y = 0 rim level"""
    if kind == 'bell':
        top = lathe([(r * .98, -.18 * h), (r * 1.02, .05 * h), (r * .9, .45 * h), (r * .55, .85 * h), (0, h)], n=nc)
    elif kind == 'flat':
        top = lathe([(r * .97, -.12 * h), (r * 1.04, .1 * h), (r * .92, .38 * h), (r * .5, .58 * h), (0, .64 * h)], n=nc)
    else:
        top = lathe([(r * .96, -.2 * h), (r * 1.03, .02 * h), (r * .95, .4 * h), (r * .7, .78 * h), (r * .35, .97 * h), (0, h)], n=nc)
    gills = bmesh.new(); n = ng; rim = []; hub = []
    for i in range(n):
        a = i * math.tau / n; k = .9 if i % 2 else .94
        rim.append(gills.verts.new((math.cos(a) * r * k, -.16 * h + (.06 * h if i % 2 else 0), math.sin(a) * r * k)))
        hub.append(gills.verts.new((math.cos(a) * r * .22, .1 * h, math.sin(a) * r * .22)))
    for i in range(n):
        j = (i + 1) % n; gills.faces.new((rim[j], rim[i], hub[i], hub[j]))
    gills.faces.new(hub)
    bmesh.ops.recalc_face_normals(gills, faces=list(gills.faces))
    for f in gills.faces:
        f.normal_update()
        if f.normal.y > 0: f.normal_flip()
    return top, gills

def mushroom(P, base, H, r, seed, kind='dome', lean=10.0, yaw=0.0, spots=7, stem_r=None, gk='shroom', sk='spot', capcol='shroom'):
    """one fungus: S-bent tapering stem with a skirt ring, painted cap, GLOWING gills underneath + glowing cap spots"""
    rng = random.Random(seed); base = Vector(base); sr = stem_r or r * .22
    d = Vector((math.sin(math.radians(yaw)) * math.sin(math.radians(lean)), 0, -math.cos(math.radians(yaw)) * math.sin(math.radians(lean))))
    pts = [base + Vector((0, -.5, 0))]
    for i in range(1, 7):
        t = i / 6; pts.append(base + Vector((0, H * t, 0)) + d * H * (t ** 1.6) + Vector((math.sin(t * 3 + seed) * .08 * H, 0, 0)) * (1 - t))
    rad = [sr * (1.5 - .55 * (i / 6)) for i in range(7)]
    stem = tube(pts, rad, sides=8 if r > 2 else 5, cap0=False, cap1=False); P.add(stem, V('stem', base.y, base.y + H, .38, .72, nk=.1, ns=2, seed=seed), smooth=True)
    top_dir = (pts[-1] - pts[-2]).normalized()
    pitch = math.degrees(math.acos(max(-1, min(1, top_dir.y)))); yw = math.degrees(math.atan2(-top_dir.x, -top_dir.z)) if pitch > .5 else 0
    if r > 1.2: P.add(T(torus(sr * 1.25, sr * .28, 10 if r > 2 else 6, 4), pts[4] + Vector((0, -.1, 0))), FS('stem', .62, .2, .04, seed))
    capH = r * (.75 if kind == 'bell' else .55)
    top, gills = cap_shape(r, capH, seed, kind)
    for bm in (top, gills): T(bm, pts[-1], yaw=yw, pitch=pitch)
    P.add(top, V(capcol, pts[-1].y - capH * .2, pts[-1].y + capH, .3, .74, nk=.18, ns=r, seed=seed), smooth=True)
    P.gadd(gills, gk)
    Mx = Matrix.Rotation(math.radians(yw), 3, 'Y') @ Matrix.Rotation(math.radians(pitch), 3, 'X')
    for k in range(spots):                                                  # raised glowing spots on the cap
        a = rng.uniform(0, math.tau); t = rng.uniform(.25, .8)
        if kind == 'bell': local = Vector((math.cos(a) * r * (1 - t) * .9, capH * t * .95, math.sin(a) * r * (1 - t) * .9))
        else: local = Vector((math.cos(a) * r * (.95 - t * .7), capH * (.1 + .85 * t ** 1.4), math.sin(a) * r * (.95 - t * .7)))
        P.gadd(dot(pts[-1] + Mx @ local, rng.uniform(.1, .2) * r, .4, 5), sk)
    return pts[-1]

def mound(P, r, h, seed, col='moss', glow=('shroom', 'spot')):
    """mossy root mound; glowing spore nodules sit on its foot at ground level (one ring per glow key) so the glow
    parts are grounded too (the exporter tests every MeshPart of a fungus for floating)"""
    m = strata_mass(r, h, r * .9, seed, k=5, layers=2, n=2.6, flatb=.9); T(m, (0, h * .25, 0))
    P.add(m, V(col, -h, h * 1.2, .3, .7, ns=2, seed=seed), smooth=True)
    nodules(P, r * .95, seed, glow)

def nodules(P, r, seed, keys, n=4):
    rng = random.Random(seed * 7 + 1)
    for gk in keys:
        for k in range(n):
            a = rng.uniform(0, math.tau); d = r * rng.uniform(.8, 1.05)
            r_ = rng.uniform(.18, .3); P.gadd(dot((math.cos(a) * d, .3 + r_ * .3, math.sin(a) * d), r_, .55, 5), gk)

def glowshroom_giant(seed=1, magenta=False):
    """three giant cave mushrooms (16 / 11 / 7 tall) from one mossy root mound, caps leaning apart; magenta = the
    Spore Brewery variant (magenta caps, gills and spots)"""
    rng = random.Random(seed); P = Prop('GlowShroomGiant%d%s' % (seed, 'M' if magenta else ''))
    gk, sk, cc = ('brew', 'brew', 'crysV') if magenta else ('shroom', 'spot', 'shroom')
    mound(P, 4.2, 1.4, seed, glow=(gk, sk))
    for k, (H, r, kind, a, lean) in enumerate(((16, 6.2, 'dome', 0, 7), (11, 4.4, 'flat', 2.2, 18), (7, 3.0, 'bell', 4.1, 24))):
        dd = 0 if k == 0 else 2.2
        mushroom(P, (math.cos(a) * dd, .3, math.sin(a) * dd), H, r, seed * 9 + k, kind, lean=lean, yaw=math.degrees(a) + 90 + rng.uniform(-20, 20),
                 spots=9 if k == 0 else 6, stem_r=r * .17, gk=gk, sk=sk, capcol=cc)
    for k in range(5):                                                      # babies at the foot
        a = rng.uniform(0, math.tau); d = rng.uniform(2.8, 3.8)
        mushroom(P, (math.cos(a) * d, .2, math.sin(a) * d), rng.uniform(1.2, 2.2), rng.uniform(.5, .8), seed * 31 + k, 'bell',
                 lean=rng.uniform(5, 25), yaw=rng.uniform(0, 360), spots=0, gk=gk, capcol=cc)
    return P

def glowshroom_cluster(seed=2):
    """a knee-high cluster: 6-8 small mushrooms of mixed cap shapes on a mossy hump"""
    rng = random.Random(seed); P = Prop('GlowShroomCluster%d' % seed)
    mound(P, 1.8, .6, seed)
    for k in range(rng.randint(6, 8)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.5)
        H = rng.uniform(1.6, 4.2) if k < 3 else rng.uniform(.8, 1.8)
        mushroom(P, (math.cos(a) * d, .15, math.sin(a) * d), H, H * rng.uniform(.3, .42), seed * 13 + k, rng.choice(('dome', 'bell', 'flat')),
                 lean=rng.uniform(4, 22), yaw=-math.degrees(a) - 90, spots=3 if H > 2 else 0)
    return P

def shroom_patch(seed=3):
    """tiny scatter: thin-stalked glowing bell caps (all glow), ankle high"""
    rng = random.Random(seed); P = Prop('ShroomPatch%d' % seed)
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .9); b = Vector((math.cos(a) * d, 0, math.sin(a) * d))
        H = rng.uniform(.6, 1.4); lean = math.radians(rng.uniform(0, 18)); yw = rng.uniform(0, math.tau)
        top = b + Vector((math.cos(yw) * math.sin(lean) * H, H, math.sin(yw) * math.sin(lean) * H))
        P.add(tube([b - Vector((0, .2, 0)), (b + top) / 2, top], [.07, .06, .05], sides=5), V('stem', 0, H, .4, .8))
        c = lathe([(.26 * H + .05, -.05), (.24 * H, .12), (.12 * H, .3), (0, .36)], n=7); P.gadd(T(c, top), 'shroom')
    nodules(P, .9, seed, ('shroom',), 3)
    return P

# ------------------------------------------------------------------ glow-root vines (hang: origin at the TOP)
def glow_vine(seed=1, L=22.0, strands=3, name=None):
    """hanging glow-root: a small root knot under the ceiling, 2-4 twisting root strands swaying down, root hairs,
    glowing seed bulbs along them and a bigger glowing tip pod on each strand"""
    rng = random.Random(seed); P = Prop(name or 'GlowVine%d' % seed)
    knot = strata_mass(.9, .35, .8, seed, k=4, layers=1, n=2.4); T(knot, (0, .05, 0))
    P.add(knot, V('wooddk', -.4, .4, .35, .55), smooth=True)
    for s in range(strands):
        LL = L * (1 if s == 0 else rng.uniform(.45, .8)); a0 = rng.uniform(0, math.tau)
        sway = rng.uniform(1.6, 3.0); n = max(6, int(LL / 2.2))
        pts = []
        for i in range(n + 1):
            t = i / n
            pts.append(Vector((math.cos(a0) * .6 + math.sin(t * 5 + a0) * sway * t ** .7, -.1 - LL * t, math.sin(a0) * .6 + math.cos(t * 4.1 + a0) * sway * t ** .7 * .8)))
        rad = [.42 * (1 - .6 * (i / n)) for i in range(n + 1)]
        P.add(tube(pts, rad, sides=6, cap0=False), V('moss', -LL, 0, .32, .62, nk=.05, ns=2, seed=seed + s), smooth=True)
        for i in range(2, n, 2):                                            # glowing seed bulbs
            side = Vector((math.cos(i * 1.7), 0, math.sin(i * 1.7))) * rad[i] * .9
            P.gadd(dot(pts[i] + side, .24 * rng.uniform(.9, 1.3), 1.3, 5), 'root')
        for i in range(1, n, 3):                                            # root hairs
            d = Vector((math.cos(i * 2.3 + s), -.6, math.sin(i * 2.3 + s))).normalized()
            P.add(tube([pts[i], pts[i] + d * 1.2, pts[i] + d * 2.0 + Vector((0, -.6, 0))], [.08, .05, .02], sides=4, cap0=False), V('wooddk', -LL, 0, .3, .5))
        pod = lathe([(0, .2), (.32, 0), (.42, -.45), (.3, -.9), (0, -1.15)], n=7)
        T(pod, pts[-1]); P.gadd(pod, 'root')
        cup = lathe([(.18, .25), (.36, -.02), (.3, -.2)], n=7); T(cup, pts[-1]); P.add(cup, FS('wooddk', .45, .2))
    return P

# ------------------------------------------------------------------ lake bed glow (Neon under the water)
def lake_glow(seed=1):
    """flat rounded glowing stones for the lake bed: the turquoise 'glow from below' (Neon under see-through water)"""
    rng = random.Random(seed); P = Prop('BedGlow%d' % seed)        # glowing bed stones (not 'Lake*': that name means water)
    for k in range(7):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 7)
        b = strata_mass(rng.uniform(1.4, 2.8), .4, rng.uniform(1.2, 2.4), seed * 5 + k, k=3, layers=1, n=2.6, flatb=.9)
        T(b, (math.cos(a) * d, .2, math.sin(a) * d), yaw=rng.uniform(0, 360)); P.gadd(b, 'lake')
    return P
