# Mistvale Lake prop kit (hidden valley bowl, bright cyan daylight, painterly smooth shading).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Look: SOFT. Everything big is smooth-shaded with per-VERTEX gradients (no faceted flat faces): pillowy rounded rock
# masses with thick moss caps, chunky rounded canopy clumps, smooth water. Village = dark slate-blue gable roofs over
# dark timber frames with shoji panels (no upturned hip roofs: that was Yumori Springs).
# Machinery (Prop, materials, to_kit) from the skill's grove module, helpers (T, bar, log, lathe, torus, sag) from the
# medieval example; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix, noise as MN
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, hull, nz, clamp, ngon_prism, bevel

PAL = Palette({
    'rock':    ('#3c5878', '#8cb0d2', '#eaf6ff'),     # cool blue-grey rock masses
    'moss':    ('#1c7230', '#4fc23e', '#c6f872'),     # thick saturated moss caps
    'grass':   ('#2f7a30', '#5cc244', '#aef070'),     # valley floor
    'leaf':    ('#1c6a2c', '#4cb63c', '#c2f670'),     # broadleaf canopies
    'pine':    ('#0f4234', '#22704f', '#5cbc84'),     # pines
    'blossom': ('#a8507e', '#f29ccb', '#fff0f8'),     # the one cherry tree
    'sand':    ('#a88f6c', '#e6d3a8', '#fff6dc'),     # beach
    'water':   ('#0a5f9c', '#1fb2e2', '#b4f6ff'),     # turquoise lake + falls
    'wood':    ('#3a2418', '#6e4732', '#ad7c58'),     # docks, posts, trunks
    'wooddk':  ('#16110f', '#2f241e', '#56443a'),     # house timber frames
    'shoji':   ('#a9a594', '#ece6d0', '#fffcf0'),     # paper panels, plaster
    'roof':    ('#151c2a', '#2c3850', '#5e7096'),     # dark slate-blue roof tiles
    'stone':   ('#4d5566', '#8c94a4', '#cfd5de'),     # retaining walls, footings
    'flower':  ('#4a2a8a', '#9a62e0', '#e2c6ff'),     # violet flowers
    'red':     ('#7a1e16', '#d6493a', '#ffa286'),     # lantern paper, small accents
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
import paint as PAINT                                                         # painted 1024 atlas + UV remap (paint.py)
PAINT.install(G, PAL)
G.GLOW.clear(); G.GLOW.update({'lamp': '#ffcf6e', 'foam': '#e4fbff', 'falls': '#c4f4ff', 'shoji': '#ffe6b0'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 2.6, 'foam': 1.1, 'falls': 1.6, 'shoji': .55})
Prop, S = G.Prop, G.S
T, bar, log, lathe, torus, sag = B.T, B.bar, B.log, B.lathe, B.torus, B.sag
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ soft (per-vertex) shading
def V(col, y0, y1, a, b, nk=.12, ns=None, seed=0, amp=.1):
    """per-loop shade: height gradient y0..y1 (a -> b) + vertex-normal lift + low-freq noise: smooth painterly ramps"""
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

def flat(col, v): u = PAL.u(col); return lambda f: [(u, v)] * len(f.loops)

# ------------------------------------------------------------------ rounded rock kit (the signature)
def rounded_mass(sx, sy, sz, seed, k=8, n=3.4, lump=.15, taper=.12, lean=0.0, cuts=0, flatb=None):
    """pillowy rounded-box mass: a subdivided cube pushed onto a superellipsoid |x|^n+|y|^n+|z|^n = 1 (n 3-4 = soft
    box), then low-frequency lumps along the radial direction, a slight top taper and lean. Centre at (0, 0, 0)."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=k - 1, use_grid_fill=True)
    rng = random.Random(seed); off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    PL = []
    for c in range(cuts):
        if c == 0: pn = Vector((rng.uniform(-.35, .35), 1, rng.uniform(-.35, .35)))      # tilted top ledge
        else:
            a = rng.uniform(0, math.tau); pn = Vector((math.cos(a), rng.uniform(-.25, .45), math.sin(a)))
        PL.append((pn.normalized(), rng.uniform(.62, .82) if c else rng.uniform(.8, .92)))
    for v in bm.verts:
        p = v.co.copy()
        d = (abs(p.x) ** n + abs(p.y) ** n + abs(p.z) ** n) ** (1 / n)
        q = p / d
        r = q.normalized()
        lumpy = 1 + lump * (MN.noise(r * 1.2 + off) * 1.0 + MN.noise(r * 2.6 + off * .5) * .5)
        q = q * lumpy
        for pn, pd in PL:                                                    # carved cut planes (soft-flattened facets)
            dd = q.dot(pn) - pd
            if dd > 0: q = q - pn * dd * .9
        if flatb is not None: q.y = max(q.y, -flatb)
        t = (q.y + 1) / 2
        q.x *= 1 - taper * t; q.z *= 1 - taper * t
        v.co = Vector((q.x * sx + lean * t * sx, q.y * sy, q.z * sz))
    bm.normal_update()
    return bm

def moss_cap(bm, thick, thr=.42, seed=0, droop=1.0):
    """thick moss shell over the up-facing part of `bm`: faces whose verts all face up past a noisy threshold are copied,
    pushed out along the vertex normals by `thick`, and closed by a skirt that drops back to the rock (droopy rim)"""
    bm.normal_update(); bm.verts.index_update()
    rng = random.Random(seed); off = rng.uniform(0, 100)
    up = {v.index: v.normal.y > thr + (MN.noise(Vector((v.co.x * .09 + off, v.co.y * .09, v.co.z * .09))) * .32) for v in bm.verts}
    faces = [f for f in bm.faces if all(up[v.index] for v in f.verts)]
    out = bmesh.new(); NV = {}; IV = {}
    def nv(v):
        if v.index not in NV:
            NV[v.index] = out.verts.new(v.co + v.normal * thick)
        return NV[v.index]
    for f in faces: out.faces.new([nv(v) for v in f.verts])
    sel = set(faces)
    for f in faces:                                                        # skirt on boundary edges
        for e in f.edges:
            if sum(1 for g in e.link_faces if g in sel) != 1: continue
            a, b = e.verts
            for v in (a, b):
                if v.index not in IV:
                    IV[v.index] = out.verts.new(v.co + v.normal * (-.15 * thick) - Vector((0, thick * .9 * droop, 0)))
            # orient with the face loop order
            loop = [l for l in f.loops if l.edge == e][0]
            v0, v1 = loop.vert, loop.link_loop_next.vert
            out.faces.new((NV[v1.index], NV[v0.index], IV[v0.index], IV[v1.index]))
    rim = [NV[i] for i in IV] + list(IV.values())                           # round off the grid jaggies of the rim
    for _ in range(3): bmesh.ops.smooth_vert(out, verts=rim, factor=.5, use_axis_x=True, use_axis_y=False, use_axis_z=True)
    out.normal_update()
    return out

def rim_shade(bm):
    """per-vertex convexity -> painted rim highlight (convex top edges lighter) / crevice dark (concave)"""
    bm.normal_update(); out = {}
    for v in bm.verts:
        if not v.link_edges: out[v] = 0; continue
        c = sum(v.normal.dot((e.other_vert(v).co - v.co).normalized()) for e in v.link_edges) / len(v.link_edges)
        out[v] = -c
    return out

def RS(col, y0, y1, a, b, conv, nk=.16, ns=None, seed=0, amp=.07, hi=.3, lo=.32):
    u = PAL.u(col)
    def f(face):
        res = []
        for l in face.loops:
            p = l.vert.co; n = l.vert.normal; t = clamp((p.y - y0) / (y1 - y0))
            v = lerp(a, b, t) + nk * n.y
            c = conv.get(l.vert, 0)
            if c > 0 and n.y > -.25: v += hi * min(1, c * 4)                 # lit rim on convex edges
            elif c < 0: v -= lo * min(1, -c * 4)                             # dark crevice
            if n.y < -.3: v -= .12                                           # undersides darker
            if ns: v += (nz(p.x, p.y, p.z, ns, seed) - .5) * amp * 2
            res.append((u, clamp(v, .04, .96)))
        return res
    return f

def boulder(seed=1, w=12.0, h=9.0, d=10.0, n=3.4, moss=True, k=7, taper=.12, lean=0.0, mthr=.62, name=None, cuts=5):
    """one carved rounded rock: superellipsoid mass with soft-flattened cut planes (a flat top ledge + side facets), a
    flat bedded bottom, moss only on the top ledge draping a little over its edge; rim highlights on convex edges.
    Origin at the bottom-centre with ~28% of the height below it (bedded in)."""
    P = Prop(name or 'Rock%d' % seed)
    bm = rounded_mass(w / 2, h / 2, d / 2, seed, k=k, n=n, taper=taper, lean=lean, cuts=cuts, flatb=.78)
    bmesh.ops.translate(bm, vec=Vector((0, h / 2 - h * .28, 0)), verts=bm.verts)
    cap = moss_cap(bm, max(.3, min(w, d) * .05), thr=mthr, seed=seed, droop=1.4) if moss else None
    ytop = h * .72; conv = rim_shade(bm)
    P.add(bm, RS('rock', -h * .28, ytop, .22, .7, conv, ns=max(w, h) * .45, seed=seed), smooth=True)
    if cap: P.add(cap, V('moss', ytop * .6, ytop + 1, .45, .84, nk=.12, ns=max(w, h) * .3, seed=seed + 3, amp=.06), smooth=True)
    return P

# rock family used everywhere (cliff tiers + shore + islet), built at real size, reused at many scales/rotations
ROCKS = {
    'RockPillow1': lambda: boulder(1, 30, 18, 26, n=3.2, name='RockPillow1'),
    'RockPillow2': lambda: boulder(2, 26, 15, 24, n=3.8, lean=.08, name='RockPillow2'),
    'RockTower1':  lambda: boulder(3, 18, 34, 18, n=3.6, taper=.18, name='RockTower1'),
    'RockTower2':  lambda: boulder(4, 22, 42, 20, n=3.0, taper=.22, lean=-.1, name='RockTower2'),
    'RockMassive': lambda: boulder(9, 46, 30, 38, n=3.0, taper=.1, k=8, cuts=7, name='RockMassive'),
    'RockSlab1':   lambda: boulder(5, 34, 12, 22, n=4.0, name='RockSlab1'),
    'RockKnob1':   lambda: boulder(6, 14, 12, 13, n=2.8, name='RockKnob1'),
    'RockKnob2':   lambda: boulder(7, 11, 8, 12, n=3.0, mthr=.45, name='RockKnob2'),
    'RockBare1':   lambda: boulder(8, 9, 6, 8, n=2.8, moss=False, k=6, name='RockBare1'),
}
# far-tier versions (same shapes, coarser grid): the upper cliff tiers are small on screen and in haze
ROCKS_LO = {
    'RockPillow1Lo': lambda: boulder(1, 30, 18, 26, n=3.2, k=5, name='RockPillow1Lo'),
    'RockPillow2Lo': lambda: boulder(2, 26, 15, 24, n=3.8, lean=.08, k=5, name='RockPillow2Lo'),
    'RockSlab1Lo':   lambda: boulder(5, 34, 12, 22, n=4.0, k=5, name='RockSlab1Lo'),
    'RockTower1Lo':  lambda: boulder(3, 18, 34, 18, n=3.6, taper=.18, k=5, name='RockTower1Lo'),
    'RockMassiveLo': lambda: boulder(9, 46, 30, 38, n=3.0, taper=.1, k=6, cuts=7, name='RockMassiveLo'),
    'RockTower2Lo':  lambda: boulder(4, 22, 42, 20, n=3.0, taper=.22, lean=-.1, k=5, name='RockTower2Lo'),
    'RockPillow1VLo': lambda: boulder(1, 30, 18, 26, n=3.2, k=4, name='RockPillow1VLo'),
    'RockSlab1VLo':   lambda: boulder(5, 34, 12, 22, n=4.0, k=4, name='RockSlab1VLo'),
    'RockPillow2VLo': lambda: boulder(2, 26, 15, 24, n=3.8, lean=.08, k=4, name='RockPillow2VLo'),
    'RockTower1VLo':  lambda: boulder(3, 18, 34, 18, n=3.6, taper=.18, k=4, name='RockTower1VLo'),
    'RockMassiveVLo': lambda: boulder(9, 46, 30, 38, n=3.0, taper=.1, k=5, cuts=7, name='RockMassiveVLo'),
}
ROCKS.update(ROCKS_LO)

# ------------------------------------------------------------------ trees: chunky rounded canopy clumps
def clump(c, r, seed, sub=3, sq=.82, lump=.16):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = Vector((seed * 3.1, seed * 1.7, -seed * 2.3))
    for v in bm.verts:
        d = v.co.normalized()
        k = 1 + lump * MN.noise(d * 1.8 + off) + lump * .5 * MN.noise(d * 4.0 - off)
        v.co = Vector((d.x * r * k, d.y * r * sq * k, d.z * r * k)) + Vector(c)
    bm.normal_update(); return bm

def leaf_cluster(P, c, r, col, seed, n=None, sq=.8):
    """one painted leaf clump: a dark core lobe + n leaf cards (pointed diamonds, single-sided, facing out) laid over
    it like shingles, drooping, tips lighter. Top of the clump lighter (rim glow), underside dark."""
    rng = random.Random(seed); c = Vector(c)
    n = n or int(2.0 * r * r) + 46
    y0 = c.y - r * sq; y1 = c.y + r * sq
    P.add(clump(c, r * .84, seed, sub=2, sq=sq, lump=.14), V(col, y0, y1, .16, .6, nk=.12), smooth=True)
    bm = bmesh.new()
    for k in range(n):
        t = (k + .5) / n; ph = math.acos(1 - 2 * t * .72); th = k * 2.39996 + seed
        d = Vector((math.sin(ph) * math.cos(th), math.cos(ph), math.sin(ph) * math.sin(th)))
        base = c + Vector((d.x * r * .82, d.y * r * .82 * sq, d.z * r * .82))
        down = Vector((0, -1, 0)); tng = down - d * down.dot(d)
        tng = tng.normalized() if tng.length > 1e-4 else Vector((1, 0, 0))
        L = min(r * .42, 2.4) * rng.uniform(.8, 1.1); W = L * rng.uniform(.5, .62)
        dirv = (d * .42 + tng * .9).normalized()
        side = d.cross(dirv).normalized() * W / 2
        tip = base + dirv * L; mid = base + dirv * L * .45 + d * L * .12
        vs = [bm.verts.new(base), bm.verts.new(mid - side), bm.verts.new(tip), bm.verts.new(mid + side)]
        f = bm.faces.new(vs); f.normal_update()
        if f.normal.dot(d) < 0: f.normal_flip()
    bm.normal_update(); u = PAL.u(col)
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co; tt = clamp((p.y - y0) / (y1 - y0))
            tipk = .1 if (p - c).length > r * 1.05 else 0
            out.append((u, clamp(.26 + .6 * tt + tipk, .04, .96)))
        return out
    P.add(bm, sh)

def canopy(P, cs, col, y0, y1, seed, sub=None):
    for i, (c, r) in enumerate(cs): leaf_cluster(P, c, r, col, seed * 13 + i)

def trunk(P, pts, radii, sides=9, col='wood'):
    y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
    P.add(tube([Vector(p) for p in pts], radii, sides=sides), V(col, y0, y1, .22, .6, nk=.1, ns=3, amp=.05), smooth=True)

def limb(P, a, b, r0, r1, bend=.15, n=5, sides=7):
    """curved branch from a to b, arching up"""
    a, b = Vector(a), Vector(b); L = (b - a).length
    pts = [a.lerp(b, t) + Vector((0, math.sin(t * math.pi) * L * bend, 0)) for t in [i / (n - 1) for i in range(n)]]
    P.add(tube(pts, [lerp(r0, r1, i / (n - 1)) for i in range(n)], sides=sides), V('wood', a.y - 2, b.y + 2, .25, .6, nk=.12), smooth=True)

def broadleaf(seed=1, h=22.0, col='leaf', name=None):
    """stylised broadleaf: thick tapered trunk forking into 3-4 arching limbs, each carrying its own painted leaf clump
    (separate clumps, sky between them), plus a crown clump"""
    rng = random.Random(seed); P = Prop(name or 'Broadleaf%d' % seed)
    bx, bz = rng.uniform(-1, 1) * h * .05, rng.uniform(-1, 1) * h * .05
    pts = [(bx * t * t, -1.0 + h * .5 * t, bz * t * t) for t in [i / 5 for i in range(6)]]
    trunk(P, pts, [h * .07 * (1 - .45 * i / 5) for i in range(6)])
    for k in range(4):                                                         # root flares
        a = k * math.tau / 4 + rng.uniform(-.3, .3); R = h * .065
        trunk(P, [(0, R * 1.6, 0), (math.cos(a) * R * 1.5, R * .45, math.sin(a) * R * 1.5), (math.cos(a) * R * 2.6, -.6, math.sin(a) * R * 2.6)], [R * .55, R * .38, R * .12], sides=6)
    top = Vector(pts[-1]); cs = [(top + Vector((0, h * .3, 0)), h * .2)]
    limb(P, pts[4], cs[0][0] - Vector((0, h * .12, 0)), h * .035, h * .02)
    nl = rng.randint(3, 4)
    for k in range(nl):
        a = k * math.tau / nl + rng.uniform(-.4, .4); d = h * rng.uniform(.25, .31)
        c = top + Vector((math.cos(a) * d, h * rng.uniform(.0, .14), math.sin(a) * d))
        cs.append((c, h * rng.uniform(.15, .18)))
        limb(P, pts[3 + k % 2], c - (c - top).normalized() * h * .07 - Vector((0, h * .07, 0)), h * .04, h * .016)
    for i, (c, r) in enumerate(cs): leaf_cluster(P, c, r, col, seed * 13 + i)
    return P

def pine(seed=1, h=34.0, name=None):
    """tall stylised pine: straight trunk, 8 tiers of separate drooping branch sprays (flattened 4-sided spikes
    radiating out and down, shorter going up), offset tier to tier, a spike top"""
    rng = random.Random(seed); P = Prop(name or 'Pine%d' % seed)
    trunk(P, [(0, -1, 0), (0, h * .5, 0), (0, h * .97, 0)], [h * .035, h * .024, h * .008], sides=8)
    tiers = 9; u = PAL.u('pine')
    for i in range(tiers):
        t = i / (tiers - 1); y = h * (.14 + .76 * t); R = h * .3 * (1 - t * .8) + h * .025
        nb = 11 if i < 5 else 8; a0 = rng.uniform(0, math.tau)
        for k in range(nb):
            a = a0 + k * math.tau / nb + rng.uniform(-.15, .15); L = R * rng.uniform(.85, 1.1)
            d = Vector((math.cos(a), 0, math.sin(a)))
            root = Vector((0, y + h * .04, 0)); tip = root + d * L - Vector((0, L * .42, 0))
            side = Vector((-d.z, 0, d.x)) * L * .38; upv = Vector((0, L * .14, 0))
            mid = root + d * L * .45 - Vector((0, L * .1, 0))
            bm = bmesh.new()
            vs = [bm.verts.new(p) for p in (root, mid + side, tip, mid - side, mid + upv)]
            bm.faces.new((vs[0], vs[1], vs[4])); bm.faces.new((vs[1], vs[2], vs[4])); bm.faces.new((vs[2], vs[3], vs[4])); bm.faces.new((vs[3], vs[0], vs[4]))
            bm.faces.new((vs[0], vs[3], vs[2], vs[1]))
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            lo, hi = y - L * .5, y + h * .06
            P.add(bm, lambda f, lo=lo, hi=hi, i=i: [(u, clamp(.18 + .5 * clamp((l.vert.co.y - lo) / (hi - lo)) + .03 * i + (.12 if f.normal.y > .3 else -.05), .04, .96)) for l in f.loops])
    P.add(T(lathe([(h * .03, 0), (0, h * .08)], n=6), (0, h * .93, 0)), V('pine', h * .9, h, .4, .7))
    return P

def blossom_tree(seed=1, h=18.0):
    """the one cherry tree: dark crooked trunk with arching limbs, pink painted clumps, petal drifts"""
    rng = random.Random(seed); P = Prop('Blossom%d' % seed)
    pts = [(0, -1, 0), (h * .05, h * .16, 0), (-h * .04, h * .3, h * .03), (h * .04, h * .42, 0)]
    trunk(P, pts, [h * .08, h * .066, h * .052, h * .04], col='wood')
    top = Vector(pts[-1]); cs = [(top + Vector((0, h * .2, 0)), h * .22)]
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = h * rng.uniform(.26, .32)
        c = top + Vector((math.cos(a) * d, h * rng.uniform(-.04, .1), math.sin(a) * d)); cs.append((c, h * rng.uniform(.15, .19)))
        limb(P, pts[2], c - (c - Vector(pts[2])).normalized() * h * .08, h * .03, h * .012)
    for i, (c, r) in enumerate(cs): leaf_cluster(P, c, r, 'blossom', seed * 17 + i)
    for k in range(5):                                                        # fallen petal drifts
        a = rng.uniform(0, math.tau); d = rng.uniform(h * .1, h * .35)
        bm = clump((math.cos(a) * d, -.05, math.sin(a) * d), rng.uniform(1.2, 2.0), seed + k, sub=1, sq=.06, lump=.1)
        P.add(bm, flat('blossom', .7), smooth=True)
    return P

def gnarled_tree(seed=9, h=36.0):
    """HERO: the big leaning islet tree. Thick twisting trunk leaning out over the water, exposed roots arching over
    the islet, three heavy arching limbs, 6 big painted leaf clumps (dark under, light top)"""
    rng = random.Random(seed); P = Prop('GnarledTree')
    lean = Vector((-1, 0, -.35)).normalized()
    pts = []
    for i in range(10):
        t = i / 9
        pts.append(Vector((0, -1.5 + h * .74 * t, 0)) + lean * (h * .38 * t ** 1.6) + Vector((math.sin(t * 6) * 1.4, 0, math.cos(t * 5) * 1.1)))
    rad = [h * .12 * (1 - .52 * i / 9) for i in range(10)]
    P.add(tube(pts, rad, sides=14, rough=.07, seed=seed), V('wood', -1.5, h * .6, .2, .62, nk=.12, ns=2.5, amp=.07), smooth=True)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-.25, .25); R = h * .07
        o = Vector((math.cos(a), 0, math.sin(a)))
        trunk(P, [tuple(o * R * .6 + Vector((0, R * 2.4, 0))), tuple(o * R * 1.7 + Vector((0, R * 1.3, 0))), tuple(o * R * 2.7 + Vector((0, R * .6, 0))),
                  tuple(o * R * 3.5 + Vector((0, .1, 0))), tuple(o * R * 4.1 + Vector((0, -1.0, 0)))], [R * 1.0, R * .76, R * .52, R * .32, R * .16], sides=8)
    top = pts[-1]; cs = [(top + Vector((0, h * .14, 0)), h * .3)]
    for base_i, d, L in ((5, Vector((-.4, .55, .7)), h * .36), (6, Vector((.8, .5, -.15)), h * .3), (7, Vector((-.75, .45, -.6)), h * .34)):
        base = pts[base_i]; e = base + d.normalized() * L
        limb(P, base, e, h * .05, h * .02, bend=.12, n=6, sides=8)
        cs.append((e + Vector((0, h * .07, 0)), h * rng.uniform(.24, .27)))
    for q in range(2):
        a = q * math.pi + .8
        cs.append((top + Vector((math.cos(a) * h * .24, -h * .03, math.sin(a) * h * .24)), h * .21))
    for i, (c, r) in enumerate(cs): leaf_cluster(P, c, r, 'leaf', seed * 19 + i, n=int(2.4 * r * r) + 50)
    return P

def bush(seed=1, r=2.4, col='leaf', name=None):
    rng = random.Random(seed); P = Prop(name or 'Bush%d' % seed)
    cs = [((0, r * .55, 0), r * .85)]
    for k in range(2):
        a = k * math.pi + rng.uniform(-.4, .4); d = r * rng.uniform(.6, .8)
        cs.append(((math.cos(a) * d, r * .38, math.sin(a) * d), r * rng.uniform(.6, .72)))
    for i, (c, rr) in enumerate(cs): leaf_cluster(P, c, rr, col, seed * 7 + i, n=int(5 * rr) + 10, sq=.78)
    if col == 'leaf' and seed % 2:                                           # violet flower dots on the clumps
        for k in range(6):
            c, rr = cs[k % len(cs)]; a = rng.uniform(0, math.tau); e = rng.uniform(.25, 1.0)
            p = Vector(c) + Vector((math.cos(a) * math.cos(e), math.sin(e) * .78, math.sin(a) * math.cos(e))) * rr * 1.05
            P.add(T(lathe([(0, 0), (.32, .12), (.22, .3), (0, .34)], n=6), tuple(p)), flat('flower', .7))
    return P

def grass_tuft(seed=1, n=15, h=2.2, col='grass'):
    """blade clump: thin bent blades fanning out (no alpha cards)"""
    rng = random.Random(seed); P = Prop('Tuft%d' % seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); tilt = rng.uniform(.15, .6); hh = h * rng.uniform(.5, 1.1); w = rng.uniform(.12, .2)
        base = Vector((math.cos(a) * .25, -.3, math.sin(a) * .25)); d = Vector((math.cos(a), 0, math.sin(a)))
        side = Vector((-d.z, 0, d.x)) * w
        mid = base + Vector((0, hh * .55, 0)) + d * hh * tilt * .4; tip = base + Vector((0, hh, 0)) + d * hh * tilt
        bm = bmesh.new()
        vs = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(mid + side * .6), bm.verts.new(mid - side * .6), bm.verts.new(tip)]
        bm.faces.new(vs[:4]); bm.faces.new((vs[3], vs[2], vs[4]))
        P.add(bm, V(col, -.3, h, .3, .85, nk=0))
    return P

def flower_patch(seed=1, col='flower', n=5, rad=1.6):
    rng = random.Random(seed); P = Prop('Flowers%d' % seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, rad); x, z = math.cos(a) * d, math.sin(a) * d; hh = rng.uniform(.9, 1.6)
        P.add(log((x, -.3, z), (x, hh, z), .07, 4), flat('grass', .45))
        for q in range(2):                                                    # two leaves
            aa = rng.uniform(0, math.tau); bm = bmesh.new()
            p0 = Vector((x, hh * .2, z)); dd = Vector((math.cos(aa), .5, math.sin(aa))) * .7
            sd = Vector((-math.sin(aa), 0, math.cos(aa))) * .2
            bm.faces.new([bm.verts.new(p) for p in (p0, p0 + dd * .5 + sd, p0 + dd, p0 + dd * .5 - sd)])
            P.add(bm, flat('grass', .6))
        c = col if rng.random() < .7 else 'shoji'
        P.add(T(lathe([(0, 0), (.38, .1), (.46, .22), (.2, .3), (0, .26)], n=7), (x, hh, z)), V(c, hh, hh + .3, .55, .8, nk=0))
        P.add(T(lathe([(0, 0), (.12, .06), (0, .14)], n=5), (x, hh + .22, z)), flat('red', .9) if c == 'shoji' else flat('shoji', .9))
    return P

def lily_pads(seed=1, n=4, rad=3.0, flower=True):
    rng = random.Random(seed); P = Prop('LilyPads%d' % seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, rad); r = rng.uniform(.9, 1.6); x, z = math.cos(a) * d, math.sin(a) * d
        notch = rng.uniform(0, math.tau); pts = []
        for i in range(14):
            t = notch + .35 + i / 13 * (math.tau - .7)
            pts.append((x + math.cos(t) * r, z + math.sin(t) * r))
        pts.append((x, z))
        bm = ngon_prism(pts[::-1] if True else pts, .02, .14)
        P.add(bm, V('moss', 0, .14, .5, .72, nk=.05))
        if flower and k == 0:
            for q in range(6):
                t = q * math.tau / 6
                P.add(T(box((.25, .1, .7), .05), (x + math.cos(t) * .35, .3, z + math.sin(t) * .35), -math.degrees(t) + 90, 35), flat('blossom', .78))
            P.add(T(lathe([(0, 0), (.16, .05), (0, .12)], n=6), (x, .3, z)), flat('red', .95))
    return P

def reeds(seed=1, n=10):
    rng = random.Random(seed); P = Prop('Reeds%d' % seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.4); x, z = math.cos(a) * d, math.sin(a) * d
        hh = rng.uniform(3, 5); lx = rng.uniform(-.4, .4); lz = rng.uniform(-.4, .4)
        P.add(tube([Vector((x, -.6, z)), Vector((x + lx * .5, hh * .5, z + lz * .5)), Vector((x + lx, hh, z + lz))], [.09, .07, .03], sides=4), V('grass', 0, hh, .35, .7, nk=0))
        if k % 3 == 0:
            P.add(T(cyl(.16, .8, 6), (x + lx * .85, hh * .8, z + lz * .85)), flat('wood', .4))
    return P

# ------------------------------------------------------------------ houses: gable roofs, timber frames, shoji walls
def gable_roof(P, w, d, y0, rise, oh=1.6, ohg=1.4, sag_=.25, ridge_axis='x', col='roof'):
    """straight gable roof (ridge along X): two lofted tile slabs with a slight concave sag, tile ribs as raised ridges,
    thick eave lip, bargeboards on the gable ends, rounded ridge cap with end tiles. w, d = wall box (full)"""
    hw = w / 2 + ohg; hd = d / 2 + oh
    nx = max(4, int(hw * 2 / 1.1)); nz_ = 6
    def ypt(zz):                                                              # height across the slope, concave
        t = 1 - abs(zz) / hd
        return y0 - .3 + rise * t + (-sag_ * math.sin(t * math.pi))
    for side in (-1, 1):
        bm = bmesh.new(); TV = []; BV = []
        for j in range(nz_ + 1):
            zz = side * hd * (1 - j / nz_)
            row = []; brow = []
            for i in range(nx + 1):
                x = -hw + 2 * hw * i / nx
                corr = .12 * (1 if i % 2 else -1)
                row.append(bm.verts.new((x, ypt(zz) + corr, zz))); brow.append(bm.verts.new((x, ypt(zz) - .45, zz)))
            TV.append(row); BV.append(brow)
        for j in range(nz_):
            for i in range(nx):
                bm.faces.new((TV[j][i], TV[j][i + 1], TV[j + 1][i + 1], TV[j + 1][i]))
                bm.faces.new((BV[j][i + 1], BV[j][i], BV[j + 1][i], BV[j + 1][i + 1]))
        for i in range(nx):                                                   # eave lip + ridge edge
            bm.faces.new((BV[0][i], BV[0][i + 1], TV[0][i + 1], TV[0][i]))
        for j in range(nz_):
            bm.faces.new((TV[j][0], TV[j + 1][0], BV[j + 1][0], BV[j][0])); bm.faces.new((TV[j + 1][nx], TV[j][nx], BV[j][nx], BV[j + 1][nx]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        rng = random.Random(int(w * 10 + side))
        u = PAL.u(col); us = PAL.u('wooddk')
        def sh(f, rng=rng):
            n = f.normal
            if n.y < -.3: return [(us, .45)] * len(f.loops)
            return [(u, clamp(.42 + .22 * n.y + rng.uniform(-.03, .03) + (.08 if f.calc_center_median().y > y0 + rise * .8 else 0), .04, .96))] * len(f.loops)
        P.add(bm, sh)
        P.add(T(box((2 * hw + .2, .55, .6), .1), (0, ypt(side * hd) - .05, side * (hd - .1))), V(col, 0, 1, .3, .3, nk=.15))       # eave tile row
    top = y0 - .3 + rise
    P.add(T(tube([Vector((-hw - .3, 0, 0)), Vector((hw + .3, 0, 0))], .55, sides=8), (0, top + .15, 0)), V(col, top - 1, top + 1, .3, .55, nk=.1), smooth=True)
    for sx in (-1, 1):
        P.add(T(lathe([(0, 0), (.75, .05), (.85, .45), (.5, .9), (0, 1.0)], n=10), (sx * (hw + .3), top - .2, 0), 0, 0, sx * 90), V(col, top - 1, top + 1, .25, .5, nk=.1), smooth=True)
        for zs in (-1, 1):                                                   # bargeboards
            a = (sx * (hw - .05), y0 - .45, zs * hd); b = (sx * (hw - .05), top + .05, 0)
            P.add(bar(a, b, .7, .3), S('wooddk', base=.35, up=.1, jit=.02))
    return top

def quad(w, h):
    """flat rectangle in XY facing -Z (lattice ribs: only ever seen from the front)"""
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.z > 0: f.normal_flip()
    return bm

def timber_wall(P, L, H, pos, yaw, door=None, bays=None, seed=0, th=.5, low=1.2):
    """wall in XY facing -Z: dark timber posts + rails framing inset shoji panels (lattice ribs), a dark wainscot
    board at the bottom; door = (x0, x1, h) cut as an opening with a sliding shoji leaf pushed aside"""
    rng = random.Random(seed)
    bays = bays or max(2, round(L / 3.2)); bw = L / bays
    frame = S('wooddk', base=.38, up=.1, jit=.02)
    for i in range(bays + 1):
        x = -L / 2 + i * bw
        P.add(T(T(box((.5, H, .7)), (x, H / 2, 0)), pos, yaw), frame)
    for y in (low, H * .55, H - .3):
        P.add(T(T(box((L + .4, .38, .62)), (0, y, 0)), pos, yaw), frame)
    for i in range(bays):
        x0 = -L / 2 + i * bw + .25; x1 = x0 + bw - .5; xc = (x0 + x1) / 2
        if door and door[0] - .1 <= xc <= door[1] + .1:
            continue
        # wainscot under the low rail
        P.add(T(T(box((bw - .5, low, th * .6)), (xc, low / 2, .06)), pos, yaw), S('wooddk', base=.25, up=0, jit=.03))
        for ya, yb in ((low + .19, H * .55 - .19), (H * .55 + .19, H - .45)):
            hh = yb - ya
            if ya > H * .5: P.gadd(T(T(box((bw - .5, hh, th * .4)), (xc, (ya + yb) / 2, .12)), pos, yaw), 'shoji')
            else: P.add(T(T(box((bw - .5, hh, th * .4)), (xc, (ya + yb) / 2, .12)), pos, yaw), S('shoji', base=.72 + rng.uniform(-.03, .03), up=0, jit=.01))
            nb = max(2, round((bw - .5) / 1.15)); nv = max(2, round(hh / 1.3))
            for q in range(1, nb):
                xx = x0 + q * (bw - .5) / nb
                P.add(T(T(quad(.1, hh), (xx, (ya + yb) / 2, -.02)), pos, yaw), flat('wooddk', .4))
            for q in range(1, nv):
                yy = ya + q * hh / nv
                P.add(T(T(quad(bw - .5, .1), (xc, yy, -.02)), pos, yaw), flat('wooddk', .4))
    if door:
        x0, x1, dh = door; dw = x1 - x0
        P.add(T(T(box((dw + .6, .45, .75), .05), ((x0 + x1) / 2, dh, 0)), pos, yaw), frame)               # lintel
        P.add(T(T(box((dw, H - dh - .2, th * .4)), ((x0 + x1) / 2, (dh + H) / 2, .12)), pos, yaw), S('shoji', base=.7, up=0))
        P.add(T(T(box((dw * .55, dh - .2, .2)), (x0 + dw * .3, dh / 2, .5)), pos, yaw), S('shoji', base=.62, up=0))  # slid leaf inside
        P.add(T(T(box((dw, dh, .1)), ((x0 + x1) / 2, dh / 2, 1.6)), pos, yaw), flat('wooddk', .12))                   # dark interior

def footing(P, w, d, h=1.4, seed=0):
    """rounded fieldstone footing course under a house (the shared base, echoes the rock kit)"""
    rng = random.Random(seed)
    P.add(T(box((w + .8, h, d + .8), .3), (0, h / 2 - .6, 0)), V('stone', -.6, h, .3, .55, nk=.1))
    per = []
    for sx, sz, L, along in ((0, -1, w, 'x'), (0, 1, w, 'x'), (-1, 0, d, 'z'), (1, 0, d, 'z')):
        n = max(2, int(L / 2.6))
        for i in range(n):
            t = -L / 2 + (i + .5) * L / n
            x = t if along == 'x' else sx * (w / 2 + .5); z = t if along == 'z' else sz * (d / 2 + .5)
            bm = rounded_mass(L / n * .5, h * .42, .55, seed * 31 + i + int(L), k=2, n=2.4, lump=.08, taper=0)
            P.add(T(bm, (x, h * .42 - .4, z), 0 if along == 'x' else 90), V('stone', -.6, h, .3, .7, nk=.1, ns=1.5, amp=.06), smooth=True)

def engawa(P, w, z, depth=1.8, y=1.0, side=-1):
    """veranda deck along a wall (z = wall line, side -1 = in front, -Z)"""
    zc = z + side * depth / 2
    n = int(w / .8)
    for i in range(n):
        x = -w / 2 + (i + .5) * w / n
        P.add(T(box((w / n - .06, .25, depth), .04), (x, y, zc)), S('wood', base=.55, up=.12, jit=.04, seed=i))
    for i in range(int(w / 3.5) + 1):
        x = -w / 2 + .3 + i * (w - .6) / int(w / 3.5)
        P.add(log((x, -.5, z + side * (depth - .25)), (x, y - .1, z + side * (depth - .25)), .17, 6), S('wood', base=.35))
    P.add(T(box((w + .2, .25, .3), .05), (0, y - .2, z + side * (depth - .1))), S('wooddk', base=.35))

def house(kind='long', seed=1, roof='roof'):
    """village houses. long = single storey longhouse 24 x 11, gable to the sides, front engawa, pent canopy;
    town = two-storey 14 x 11, upper storey set back with a balcony rail, gable roof + lower pent roof;
    kura = small white-plaster storehouse 9 x 8 on a tall stone base, heavy roof"""
    P = Prop({'long': 'LongHouse', 'town': 'TownHouse', 'kura': 'Storehouse'}[kind] + str(seed)); rng = random.Random(seed)
    if kind == 'long':
        w, d, H = 24.0, 11.0, 7.0; fy = 1.0
        footing(P, w, d, 1.6, seed)
        P.add(T(box((w, .3, d)), (0, fy, 0)), flat('wood', .4))
        timber_wall(P, w, H, (0, fy, -d / 2), 0, door=(-2.2, 2.2, 4.8), seed=seed)
        timber_wall(P, w, H, (0, fy, d / 2), 180, seed=seed + 1)
        for sx in (-1, 1): timber_wall(P, d, H, (sx * w / 2, fy, 0), -sx * 90, seed=seed + 2)
        engawa(P, w + .8, -d / 2, 2.0, fy, -1)
        # pent canopy (hisashi) over the veranda on brackets
        for i in range(5):
            x = -w / 2 + i * w / 4
            P.add(bar((x, fy + H * .82, -d / 2), (x, fy + H * .76, -d / 2 - 2.6), .35, .35), S('wooddk', base=.35))
        P.add(T(box((w + 1.2, .35, 3.4), .1), (0, fy + H * .8, -d / 2 - 1.8), 0, -14), V('roof', fy, fy + H, .4, .5, nk=.2))
        gable_roof(P, w, d, fy + H, 5.6, oh=2.0, ohg=1.2)
    elif kind == 'town':
        w, d, H1, H2 = 14.0, 11.0, 6.5, 5.2; fy = 1.0
        footing(P, w, d, 1.6, seed)
        P.add(T(box((w, .3, d)), (0, fy, 0)), flat('wood', .4))
        timber_wall(P, w, H1, (0, fy, -d / 2), 0, door=(-4.5, -.5, 5.2), seed=seed)
        timber_wall(P, w, H1, (0, fy, d / 2), 180, seed=seed + 1)
        for sx in (-1, 1): timber_wall(P, d, H1, (sx * w / 2, fy, 0), -sx * 90, seed=seed + 2)
        y2 = fy + H1
        P.add(T(box((w + 3.2, .35, d + 3.2), .1), (0, y2 + .4, 0), 0, 0), flat('wooddk', .3))
        # lower pent roof all round (skirt)
        for (sx, sz, L, yaw) in ((0, -1, w + 3, 0), (0, 1, w + 3, 180), (-1, 0, d + 3, 90), (1, 0, d + 3, -90)):
            P.add(T(T(box((L, .35, 2.4), .1), (0, 0, -1.0), 0, -18), (sx * (w / 2 + .3), y2 - .2, sz * (d / 2 + .3)), yaw), V('roof', y2 - 2, y2, .4, .5, nk=.2))
        w2, d2 = w - 2.0, d - 2.0
        timber_wall(P, w2, H2, (0, y2 + .6, -d2 / 2), 0, bays=4, seed=seed + 3)
        timber_wall(P, w2, H2, (0, y2 + .6, d2 / 2), 180, bays=4, seed=seed + 4)
        for sx in (-1, 1): timber_wall(P, d2, H2, (sx * w2 / 2, y2 + .6, 0), -sx * 90, bays=3, seed=seed + 5)
        for i in range(9):                                                   # balcony rail (front)
            x = -w2 / 2 + i * w2 / 8
            P.add(log((x, y2 + .6, -d2 / 2 - 1.1), (x, y2 + 2.0, -d2 / 2 - 1.1), .1, 5), S('wood', base=.4))
        P.add(T(box((w2 + .3, .25, .3), .05), (0, y2 + 2.0, -d2 / 2 - 1.1)), S('wood', base=.5))
        gable_roof(P, w2, d2, y2 + .6 + H2, 4.6, oh=2.2, ohg=1.6)
        engawa(P, w + .4, -d / 2, 1.6, fy, -1)
    else:
        w, d, H = 9.0, 8.0, 6.5; fy = 2.2
        footing(P, w, d, 2.8, seed)
        P.add(T(box((w, H, d), .15), (0, fy + H / 2, 0)), V('shoji', fy, fy + H, .74, .82, nk=0))
        P.add(T(box((w + .25, 1.6, d + .25), .1), (0, fy + .8, 0)), V('wooddk', fy, fy + 2, .3, .35, nk=.1))
        for x in (-w / 2, w / 2):
            for z in (-d / 2, d / 2):
                P.add(T(box((.6, H, .6), .05), (x, fy + H / 2, z)), S('wooddk', base=.35))
        P.add(T(box((2.6, 3.6, .4), .08), (0, fy + 1.8 + .9, -d / 2 - .1)), S('wooddk', base=.4))       # heavy door
        P.add(T(box((1.4, 1.2, .3), .06), (2.6, fy + H - 1.6, -d / 2 - .05)), S('wooddk', base=.3))     # vent window
        gable_roof(P, w, d, fy + H, 4.2, oh=1.6, ohg=1.0)
        for i in range(4):                                                    # stone steps to the door
            P.add(T(box((3.2, .55, 1.0), .12), (0, fy - .5 - i * .55, -d / 2 - .8 - i * .9)), V('stone', 0, 3, .45, .6, nk=.15))
    return P

# ------------------------------------------------------------------ village props
def crate(P, c, s=1.6, yaw=0.0, seed=0):
    P.add(T(box((s, s, s), .08), (c[0], c[1] + s / 2, c[2]), yaw), S('wood', base=.5, up=.12, jit=.04, seed=seed))
    for y in (.15, .85):
        P.add(T(box((s + .1, .18, s + .1), .04), (c[0], c[1] + s * y, c[2]), yaw), S('wood', base=.32, up=.1, jit=.02))
    for sx in (-1, 1):
        P.add(T(bar((sx * s * .48, .15 * s, -s * .53), (-sx * s * .48, .85 * s, -s * .53), .18, .1, .02), (c[0], c[1], c[2]), yaw), S('wood', base=.3))

def basket(P, c, r=.9, h=.8, fill='leaf', seed=0):
    P.add(T(lathe([(0, 0), (r * .8, 0), (r, h * .7), (r * 1.05, h), (r * .9, h), (0, h * .8)], n=12), c), S('sand', base=.45, up=.1, jit=.03, seed=seed))
    P.add(T(torus(r * 1.0, .08, n=12, sides=4), (c[0], c[1] + h, c[2])), S('wood', base=.5, jit=0))
    rng = random.Random(seed)
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, r * .55)
        P.add(T(lathe([(0, 0), (.3, .1), (.32, .3), (0, .45)], n=7), (c[0] + math.cos(a) * d, c[1] + h * .7, c[2] + math.sin(a) * d)), S(fill, base=.6, up=.15, jit=.05, seed=k))

def barrel(P, c, h=2.4, r=.95, seed=0):
    prof = [(0, 0)] + [(r * (1 + .12 * math.sin(math.pi * k / 6)), h * k / 6) for k in range(7)] + [(0, h)]
    P.add(T(lathe(prof, n=12), c), V('wood', 0, h, .38, .62, nk=.1), smooth=True)
    for t in (.15, .5, .85):
        rr = r * (1 + .12 * math.sin(math.pi * t)) + .05
        P.add(T(torus(rr, .08, n=12, sides=4), (c[0], c[1] + h * t, c[2])), flat('wooddk', .35))

def crates(seed=1):
    P = Prop('Crates%d' % seed); rng = random.Random(seed)
    crate(P, (0, -.2, 0), 2.0, rng.uniform(-8, 8), seed)
    crate(P, (2.2, -.2, .4), 1.7, rng.uniform(10, 25), seed + 1)
    crate(P, (.3, 1.8, .1), 1.5, rng.uniform(-30, -10), seed + 2)
    barrel(P, (-2.0, -.2, .9), seed=seed)
    basket(P, (2.0, 1.5, .4), .7, .6, 'red' if seed % 2 else 'leaf', seed)
    return P

def market_stall(seed=1):
    """open stall: 4 posts on stone pads, a small dark gable roof, counter with baskets of produce + fish, a crate
    pile and two hanging lanterns; blank sign board on the front gable (GUI anchor)"""
    P = Prop('MarketStall%d' % seed); rng = random.Random(seed)
    w, d, h = 8.0, 5.0, 5.4
    for x in (-w / 2, w / 2):
        for z in (-d / 2, d / 2):
            P.add(T(cyl(.55, .6, 8, .1), (x, -.3, z)), V('stone', -.3, .3, .4, .6, nk=.1))
            P.add(T(box((.45, h, .45), .05), (x, h / 2, z)), S('wood', base=.42, up=.08))
    for z in (-d / 2, d / 2): P.add(T(box((w + .6, .4, .45), .05), (0, h, z)), S('wood', base=.38))
    gable_roof(P, w, d, h + .2, 2.6, oh=1.0, ohg=.8)
    P.add(T(box((w - .6, 1.0, 1.6), .08), (0, 1.9, -d / 2 + .9)), S('wood', base=.55, up=.12))          # counter
    for i, x in enumerate((-w * .3, -w * .1, w * .1, w * .3)):
        P.add(T(box((1.2, 1.2, 1.2), .05), (x, .7, -d / 2 + .9)), S('wood', base=.38))
    for i, x in enumerate((-2.6, -.8, 1.0, 2.7)):
        basket(P, (x, 2.4, -d / 2 + .9), .7, .55, ('red', 'leaf', 'sand', 'flower')[(i + seed) % 4], seed + i)
    crate(P, (w / 2 - 1.2, -.2, d / 2 - 1.0), 1.6, 12, seed)
    barrel(P, (-w / 2 + 1.1, -.2, d / 2 - 1.0), 2.0, .8, seed)
    P.add(T(box((3.8, 1.1, .25), .08), (0, h - .9, -d / 2 - .05)), S('wood', base=.62, up=.05))           # blank sign (GUI)
    P.add(T(box((4.1, .18, .3), .03), (0, h - .3, -d / 2 - .05)), flat('wooddk', .3))
    for x in (-1.6, 1.6): P.add(log((x, h - .35, -d / 2 - .05), (x, h - .1, -d / 2 - .05), .05, 4), flat('wooddk', .3))
    for x in (-w / 2 + .45, w / 2 - .45):
        paper_lantern(P, (x, h - .9, -d / 2 - .35), .5, .9)
    return P

def paper_lantern(P, c, r=.5, h=.9):
    """small red paper lantern: lathed ribbed body (red) + caps + a glow core inside"""
    x, y, z = c
    P.add(log((x, y + h / 2 + .45, z), (x, y + h / 2 + .05, z), .03, 4), flat('wooddk', .3))
    prof = [(r * .5, -h / 2)] + [(r * math.sin(math.pi * (k + .5) / 5) * (1.02 if k % 2 else .96), -h / 2 + h * (k + .5) / 5) for k in range(5)] + [(r * .5, h / 2)]
    bm = lathe(prof, n=7)
    P.add(T(bm, (x, y, z)), V('red', y - h / 2, y + h / 2, .5, .72, nk=0), smooth=True)
    for s in (-1, 1): P.add(T(cyl(r * .55, .14, 8), (x, y + s * h / 2 - (.14 if s > 0 else 0) + (0 if s > 0 else 0), z)), flat('wooddk', .3))
    P.gadd(T(lathe([(0, -h * .3), (r * .55, 0), (0, h * .3)], n=5), (x, y, z)), 'lamp')

def rope_pole(seed=1, h=13.0):
    """tall timber pole with a cross arm + strut, rope cleats; lantern ropes hang from its arm tips"""
    P = Prop('RopePole%d' % seed)
    P.add(T(cyl(.7, .8, 8, .15), (0, -.4, 0)), V('stone', -.4, .4, .4, .6, nk=.1))
    P.add(log((0, -1, 0), (0, h, 0), .35, 8, .28), V('wood', 0, h, .35, .55, nk=.05), smooth=True)
    P.add(bar((-2.0, h - 1.0, 0), (2.0, h - 1.0, 0), .45, .45), S('wooddk', base=.38))
    for s in (-1, 1): P.add(bar((s * .1, h - 3.2, 0), (s * 1.6, h - 1.1, 0), .25, .25), S('wooddk', base=.35))
    P.add(T(lathe([(0, 0), (.45, .05), (.4, .3), (0, .45)], n=8), (0, h, 0)), flat('wooddk', .3))
    for y in (2.0, 2.6): P.add(T(torus(.4, .07, n=10, sides=4), (0, y, 0)), S('sand', base=.5, jit=0))
    return P

def lantern_rope(seed=1, L=26.0, drop=2.6, n=7):
    """rope span along +X from x 0 (left arm tip) to L, catenary sag, with n small paper lanterns hanging off it.
    Origin = the left attachment point (placed at a pole arm tip, yaw toward the next pole)."""
    P = Prop('LanternRope%d' % seed); rng = random.Random(seed)
    pts = sag((0, 0, 0), (L, 0, 0), drop, 12)
    P.add(tube(pts, .12, sides=4), flat('wooddk', .35))
    for k in range(n):
        t = (k + 1) / (n + 1); x = L * t; y = -math.sin(t * math.pi) * drop
        paper_lantern(P, (x, y - .9, 0), .5, .85)
    return P

def lantern_post(seed=1, h=6.0):
    """low wooden lantern post for the shore path: post, small roof cap, a hanging paper box lantern"""
    P = Prop('LanternPost%d' % seed)
    P.add(T(cyl(.6, .5, 8, .12), (0, -.3, 0)), V('stone', -.3, .3, .45, .6, nk=.1))
    P.add(T(box((.5, h, .5), .06), (0, h / 2 - .3, 0)), S('wood', base=.45, up=.1))
    P.add(bar((0, h - .9, 0), (0, h - .9, -1.6), .3, .3), S('wooddk', base=.35))
    P.add(T(lathe([(0, 0), (1.0, .05), (.9, .3), (.3, .7), (0, .8)], n=4, a0=math.pi / 4), (0, h - .25, 0)), V('roof', h - .3, h + .6, .35, .55, nk=.2))
    x, y, z = 0, h - 2.1, -1.6
    P.add(log((x, y + 1.15, z), (x, y + .6, z), .03, 4), flat('wooddk', .3))
    P.add(T(box((.95, 1.15, .95), .06), (x, y, z)), flat('wooddk', .3))
    P.add(T(box((.8, .9, 1.0), .02), (x, y, z)), flat('shoji', .85))
    P.add(T(box((1.0, .9, .8), .02), (x, y, z)), flat('shoji', .85))
    P.gadd(T(box((.6, .7, .6)), (x, y, z)), 'lamp')
    return P

# ------------------------------------------------------------------ dock, bridge, wall, stair
def dock(seed=1):
    """L-shaped fishing dock: a 4-wide walkway (along -Z from the beach at z 0) with an 8 x 7 end platform, plank
    deck with gaps, posts sticking up with rope rails, a low bench, a fishing rod rack, a bucket. Origin = shore end."""
    P = Prop('FishingDock'); rng = random.Random(seed)
    deck = 2.2
    def planks(x0, x1, z0, z1, along='z'):
        if along == 'x':
            n = int((z1 - z0) / .9)
            for i in range(n):
                z = z0 + (i + .5) * (z1 - z0) / n
                P.add(T(box((x1 - x0 + rng.uniform(-.2, .2), .3, (z1 - z0) / n - .1), .05), ((x0 + x1) / 2, deck, z)), S('wood', base=.58, up=.1, jit=.05, seed=i))
        else:
            n = int((x1 - x0) / .9)
            for i in range(n):
                x = x0 + (i + .5) * (x1 - x0) / n
                P.add(T(box(((x1 - x0) / n - .1, .3, z1 - z0 + rng.uniform(-.2, .2)), .05), (x, deck, (z0 + z1) / 2)), S('wood', base=.58, up=.1, jit=.05, seed=i + 40))
    planks(-2.2, 2.2, -26.0, 0.0, 'x')
    planks(-2.2, 7.0, -33.0, -26.0, 'z')
    for (x0, x1, z0, z1) in ((-2.2, 2.2, -26, 0), (-2.2, 7, -33, -26)):        # stringers
        for x in (x0 + .3, x1 - .3): P.add(T(box((.4, .5, z1 - z0)), (x, deck - .4, (z0 + z1) / 2)), S('wood', base=.3))
    posts = [(-2.4, z) for z in (-1, -8, -15, -22)] + [(2.4, z) for z in (-1, -8, -15, -22)] + [(-2.4, -33.2), (2.6, -33.2), (7.2, -33.2), (7.2, -26), (-2.4, -27.5)]
    for x, z in posts:
        top = deck + (2.6 if abs(z) > 2 else 1.4)
        P.add(log((x, -4.5, z), (x, top, z), .38, 8), V('wood', -4, top, .28, .55, nk=.05), smooth=True)
        P.add(T(lathe([(0, 0), (.42, .05), (.3, .3), (0, .35)], n=8), (x, top, z)), flat('wooddk', .35))
    for side in (-2.4, 2.4):                                                  # rope rails along the walkway
        for z0, z1 in ((-1, -8), (-8, -15), (-15, -22)):
            P.add(tube(sag((side, deck + 1.9, z0), (side, deck + 1.9, z1), .35, 6), .07, sides=4), flat('sand', .45))
    P.add(tube(sag((-2.4, deck + 1.9, -33.2), (2.6, deck + 1.9, -33.2), .3, 6), .07, sides=4), flat('sand', .45))
    P.add(tube(sag((7.2, deck + 1.9, -33.2), (7.2, deck + 1.9, -26), .3, 6), .07, sides=4), flat('sand', .45))
    barrel(P, (5.6, deck + .15, -27.3), 1.6, .65, seed)
    crate(P, (5.6, deck + .15, -29.2), 1.3, 18, seed)
    P.add(T(box((3.2, .3, 1.0), .06), (-.8, deck + 1.2, -31.8)), S('wood', base=.55))                        # bench
    for x in (-2.0, .4): P.add(T(box((.3, 1.0, .8), .04), (x, deck + .65, -31.8)), S('wood', base=.35))
    for k, x in enumerate((1.0, 1.5, 2.0)):                                   # rods leaning on the rail
        P.add(log((x + 3.6, deck + .2, -26.4), (x + 2.6, deck + 6.5, -25.4), .05, 4), flat('wooddk', .4))
    P.add(T(lathe([(0, 0), (.5, 0), (.6, .8), (0, .7)], n=10), (3.6, deck + .15, -32.0)), S('stone', base=.6))  # bucket
    for (x, z, ax) in ((-2.4, -33.2, 1), (7.2, -33.2, -1)):                   # lantern hook poles at the end corners
        P.add(log((x, deck, z), (x, deck + 6.2, z), .2, 6), S('wood', base=.4))
        P.add(bar((x, deck + 6.0, z), (x + ax * 2.2, deck + 6.0, z), .25, .25), S('wooddk', base=.35))
        paper_lantern(P, (x + ax * 2.0, deck + 4.9, z), .45, .8)
    return P

def footbridge(L=16.0, w=4.4, arch=1.6):
    """small arched plank bridge over the stream (span along Z, origin = centre at bank height)"""
    P = Prop('FootBridge')
    n = 16
    for i in range(n):
        t = i / (n - 1); z = -L / 2 + L * t; y = arch * math.sin(t * math.pi) + .2
        P.add(T(box((w, .3, L / n + .05), .05), (0, y, z), 0, -math.degrees(math.atan(arch * math.pi / L * math.cos(t * math.pi)))), S('wood', base=.58, up=.1, jit=.05, seed=i))
    for sx in (-1, 1):
        pts = [Vector((sx * (w / 2 - .1), arch * math.sin(t * math.pi) - .2, -L / 2 + L * t)) for t in [k / 10 for k in range(11)]]
        P.add(tube(pts, .32, sides=6), S('wood', base=.35))
        rail = [p + Vector((0, 2.4, 0)) for p in pts]
        P.add(tube(rail, .2, sides=6), V('wood', 0, 6, .45, .6, nk=.1), smooth=True)
        for k in range(0, 11, 2):
            P.add(log(pts[k], rail[k] + Vector((0, .3, 0)), .2, 6), S('wood', base=.42))
        for z in (-L / 2, L / 2):
            P.add(log((sx * (w / 2 - .1), -2.5, z), (sx * (w / 2 - .1), 3.2, z), .32, 8), S('wood', base=.38))
            P.add(T(lathe([(0, 0), (.4, .05), (.3, .4), (0, .5)], n=8), (sx * (w / 2 - .1), 3.2, z)), flat('wooddk', .35))
    return P

def stone_wall(seed=1, L=16.0, h=7.0):
    """retaining wall module (front = -Z): coursed rounded fieldstones (soft, echoes the rock kit) bedded on a
    backing core, a flat coping course on top, moss drips. Origin = bottom centre of the front face."""
    P = Prop('StoneWall%d' % seed); rng = random.Random(seed)
    P.add(T(box((L, h, 2.0)), (0, h / 2 - .5, 1.1)), V('stone', 0, h, .25, .35, nk=0))
    y = -.5; row = 0
    while y < h - 1.2:
        bh = rng.uniform(1.8, 2.4); x = -L / 2 - rng.uniform(0, 1.2)
        while x < L / 2 - .3:
            bw = rng.uniform(3.4, 4.8); xa, xb = max(x, -L / 2), min(x + bw, L / 2); x += bw
            if xb - xa < .6: continue
            bm = rounded_mass((xb - xa) / 2 - .06, bh / 2 - .05, .5, seed * 97 + row * 13 + int(x * 3), k=2, n=2.4, lump=.07, taper=0)
            P.add(T(bm, ((xa + xb) / 2, y + bh / 2, .1)), V('stone', -.5, h, .3, .72, nk=.12, ns=4, seed=seed, amp=.06), smooth=True)
        y += bh; row += 1
    x = -L / 2
    while x < L / 2 - .2:
        bw = min(rng.uniform(2.2, 3.2), L / 2 - x)
        P.add(T(box((bw - .1, .6, 2.4), .15), (x + bw / 2, h - .3, .7)), V('stone', h - 1, h, .55, .7, nk=.12))
        x += bw
    for k in range(3):                                                        # moss drips over the coping
        xx = rng.uniform(-L / 2 + 1, L / 2 - 1)
        bm = rounded_mass(rng.uniform(1.0, 1.8), .5, .7, seed + k, k=3, n=2.4, lump=.1, taper=0)
        P.add(T(bm, (xx, h - .1, .2)), V('moss', h - 1, h + .5, .45, .75, nk=.1), smooth=True)
    return P

def stone_stair(w=6.0, rise=8.0, run=12.0):
    """stone flight up the retaining wall (front = -Z, climbs toward +Z), rounded cheek stones"""
    P = Prop('StoneStair'); n = int(rise / .8)
    for i in range(n):
        z = -run / 2 + (i + .5) * run / n
        P.add(T(box((w, (i + 1) * rise / n, run / n + .05), .1), (0, (i + 1) * rise / n / 2 - .3, z)), V('stone', 0, rise, .45, .68, nk=.15))
    for sx in (-1, 1):
        for i in range(0, n, 2):
            z = -run / 2 + (i + .5) * run / n
            bm = rounded_mass(.7, (i + 2) * rise / n / 2 + .3, run / n, 70 + i + sx, k=3, n=2.6, lump=.08, taper=0)
            P.add(T(bm, (sx * (w / 2 + .6), (i + 2) * rise / n / 2 - .5, z)), V('stone', 0, rise, .35, .65, nk=.12), smooth=True)
    return P

# ------------------------------------------------------------------ the waterfall (hero)
def waterfall(h=64.0, w=30.0):
    """HERO: a broad curved sheet spilling off a mossy carved lip, bowing out and widening as it falls; painted water
    on the sheet + 6 glowing streak ribbons down its face (Neon 'falls'), a wide glowing foam skirt + churn in the plunge
    pool and spray clumps climbing the foot. Origin = pool centre; front (-Z) faces the valley."""
    P = Prop('Waterfall')
    nx, ny = 16, 18
    def sheet_pt(s, t, dz=0.0):
        y = h * (1 - t); ww = w * (.78 + .38 * t)
        zz = -6 * math.sin(min(1, t * 1.6) * math.pi / 2) - 2.0 * t + 1.0
        return Vector((s * ww, y, zz - 1.6 * (1 - (2 * s) ** 2) + dz))
    for back in (False, True):
        bm = bmesh.new(); VV = [[bm.verts.new(sheet_pt(i / nx - .5, j / ny, .8 if back else 0)) for i in range(nx + 1)] for j in range(ny + 1)]
        for j in range(ny):
            for i in range(nx):
                q = (VV[j][i], VV[j][i + 1], VV[j + 1][i + 1], VV[j + 1][i])
                bm.faces.new(q[::-1] if back else q)
        bm.normal_update(); u = PAL.u('water')
        if back: P.add(bm, flat('water', .5), smooth=True)
        else: P.add(bm, lambda f: [(u, clamp(.66 + .14 * math.sin(l.vert.co.x * 1.3) + .2 * smooth((10 - l.vert.co.y) / 10), .3, .96)) for l in f.loops], smooth=True)
    for k in range(6):                                                         # glowing streak ribbons on the face
        s0 = -.38 + k * .15 + random.Random(k).uniform(-.03, .03); wd = .035 + .02 * (k % 2)
        bm = bmesh.new(); L = []; R = []
        for j in range(ny + 1):
            t = j / ny
            L.append(bm.verts.new(sheet_pt(s0 - wd, t, -.25))); R.append(bm.verts.new(sheet_pt(s0 + wd, t, -.25)))
        for j in range(ny): bm.faces.new((L[j], R[j], R[j + 1], L[j + 1]))
        P.gadd(bm, 'falls')
    for i, (x, sx, sy, sz) in enumerate(((-w * .62, 12, 9, 10), (w * .62, 13, 10, 11), (0, w * 1.05, 3.5, 7))):  # carved mossy lip
        b = rounded_mass(sx / 2, sy / 2, sz / 2, 200 + i, k=6, n=3.2, cuts=4, flatb=.8)
        bmesh.ops.translate(b, vec=Vector((x, h - sy * .25 + (1.5 if i == 2 else 0), 3.0 + (1.5 if i == 2 else 0))), verts=b.verts)
        cap = moss_cap(b, .55, thr=.55, seed=200 + i, droop=1.4); conv = rim_shade(b)
        P.add(b, RS('rock', h - 6, h + 6, .3, .72, conv, ns=5), smooth=True)
        P.add(cap, V('moss', h - 2, h + 6, .45, .85, nk=.1), smooth=True)
    for k in range(11):                                                        # wide glowing foam skirt
        a = k * math.tau / 11; r = w * .5
        P.gadd(clump((math.cos(a) * r, .7, math.sin(a) * r * .45 - 9.0), w * .17, 300 + k, sub=2, sq=.5, lump=.18), 'foam')
    P.gadd(clump((0, 1.4, -9.0), w * .36, 320, sub=2, sq=.42, lump=.15), 'foam')
    for k in range(5):                                                         # spray climbing the foot of the falls
        P.gadd(clump((math.sin(k * 2.1) * w * .28, 3 + k * 3.2, -8 - k * .3), w * (.24 - k * .03), 330 + k, sub=2, sq=.75, lump=.2), 'foam')
    return P

def rock_steps(seed=1):
    """rounded stepping stones across the stream (small, flat-topped, moss edges)"""
    P = Prop('SteppingStones%d' % seed); rng = random.Random(seed)
    for k in range(5):
        x = rng.uniform(-.6, .6); z = -6 + k * 3.0
        bm = rounded_mass(1.3, .7, 1.1, seed * 9 + k, k=4, n=2.6, lump=.1, taper=.1)
        bmesh.ops.translate(bm, vec=Vector((x, .2, z)), verts=bm.verts)
        P.add(bm, V('rock', -.6, 1, .35, .78, nk=.12), smooth=True)
    return P


def sign_stand(seed=1):
    """station sign: blank board (GUI goes on it, nothing written) in a timber frame on two posts with a small
    slate-blue cap roof and stone feet; front = -Z"""
    P = Prop('SignStand%d' % seed)
    for x in (-1.8, 1.8):
        P.add(T(cyl(.5, .5, 8, .1), (x, -.3, 0)), V('stone', -.3, .3, .4, .6, nk=.1))
        P.add(T(box((.4, 5.2, .4), .05), (x, 2.3, 0)), S('wood', base=.42, up=.08))
    P.add(T(box((3.3, 2.0, .22), .06), (0, 3.4, -.1)), S('wood', base=.66, up=.05))
    for y in (2.35, 4.45): P.add(T(box((3.9, .3, .4), .05), (0, y, -.1)), S('wooddk', base=.35))
    P.add(T(lathe([(0, 0), (2.9, .05), (2.7, .35), (0, .9)], n=4, a0=math.pi / 4), (0, 4.85, 0), 0, 0, 0, (1, 1, .32)), V('roof', 4.8, 5.8, .35, .55, nk=.2))
    return P

# ------------------------------------------------------------------ stylised trees v2: skinned skeleton + leaf masses
def skin_mesh(nodes, edges, sub=1):
    """branching skeleton -> one smooth closed trunk mesh: Blender Skin modifier (smooth junctions, per-node radius)
    + Subdivision, evaluated and returned as a bmesh (Roblox space in, Roblox space out)"""
    import bpy
    me = bpy.data.meshes.new('_skin'); me.from_pydata([n[0] for n in nodes], edges, []); me.update()
    ob = bpy.data.objects.new('_skin', me); bpy.context.scene.collection.objects.link(ob)
    sk = ob.modifiers.new('skin', 'SKIN'); sk.use_smooth_shade = True; sk.branch_smoothing = .6
    sv = me.skin_vertices[0].data
    for i, n in enumerate(nodes):
        sv[i].radius = (n[1], n[1]); sv[i].use_root = (i == 0)
    sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = sub; sd.render_levels = sub
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(res)
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me); bpy.data.meshes.remove(res)
    bm.normal_update()
    return bm

class Skel:
    """node list [(pos, radius)] + edges; helpers to grow curved, tapering limbs"""
    def __init__(self): self.N = []; self.E = []
    def add(self, p, r, parent=None):
        self.N.append((tuple(p), r)); i = len(self.N) - 1
        if parent is not None: self.E.append((parent, i))
        return i
    def grow(self, parent, d, L, r0, r1, n, rng, bend=(0, .08, 0), wob=.12):
        """limb from node `parent` along d (curving by bend per step, wobbling), n segments; returns tip index"""
        i = parent; p = Vector(self.N[parent][0]); d = Vector(d).normalized()
        for k in range(1, n + 1):
            d = (d + Vector(bend) + Vector((rng.uniform(-wob, wob), rng.uniform(-wob, wob) * .5, rng.uniform(-wob, wob)))).normalized()
            p = p + d * (L / n)
            i = self.add(p, lerp(r0, r1, k / n), i)
        return i

def bark(P, bm, y0, y1, seed=0, groove=.16):
    """bark grooves (noise stretched along the height = long vertical furrows) + shading: dark furrows, lit ridges"""
    G = {}
    for v in bm.verts:
        g = nz(v.co.x * 1.3, v.co.y * .16, v.co.z * 1.3, 1, seed) - .5
        G[v] = g; v.co = v.co + v.normal * g * groove * 2
    bm.normal_update(); u = PAL.u('wood')
    def sh(f):
        out = []
        for l in f.loops:
            p = l.vert.co; t = clamp((p.y - y0) / (y1 - y0))
            v = .2 + .32 * t + .12 * l.vert.normal.y + G[l.vert] * .55
            out.append((u, clamp(v, .04, .96)))
        return out
    P.add(bm, sh, smooth=True)

def leaf_mass(P, c, r, col, seed, density=1.0, sq=.78, leaf=1.5):
    """one soft canopy mass: a displaced dark core blob + many small leaf cards at random spots on it (no grid, random
    roll + size = no scale pattern), pointing out and drooping; shaded dark interior -> bright tips, lit top rim,
    darker underside"""
    rng = random.Random(seed); c = Vector(c)
    P.add(clump(c, r * .9, seed, sub=3 if r > 4.5 else 2, sq=sq, lump=.2), V(col, c.y - r * sq, c.y + r * sq, .06, .42, nk=.1), smooth=True)
    n = int(density * 4.6 * r * r) + 20
    bm = bmesh.new(); y0, y1 = c.y - r * sq, c.y + r * sq
    off = Vector((seed * 1.7, seed * .3, -seed * 2.1))
    for k in range(n):
        while True:
            d = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
            if d.y > -.35 or rng.random() < .25: break
        lump = 1 + .2 * MN.noise(d * 1.8 + off) + .1 * MN.noise(d * 4.0 - off)
        base = c + Vector((d.x, d.y * sq, d.z)) * r * .9 * lump * rng.uniform(.9, 1.02)
        nrm = Vector((d.x, d.y / max(sq, .3), d.z)).normalized()
        dn = Vector((0, -1, 0)) - nrm * (-nrm.y); dn = dn.normalized() if dn.length > 1e-3 else Vector((1, 0, 0))
        side0 = nrm.cross(dn).normalized()
        a = rng.uniform(-.9, .9); dirv = (nrm * rng.uniform(.35, .6) + dn * math.cos(a) * .8 + side0 * math.sin(a) * .8).normalized()
        L = leaf * rng.uniform(.75, 1.25); W = L * rng.uniform(.45, .6)
        side = nrm.cross(dirv).normalized() * W / 2
        mid = base + dirv * L * .45 + nrm * L * .1; tip = base + dirv * L
        f = bm.faces.new([bm.verts.new(p) for p in (base, mid - side, tip, mid + side)]); f.normal_update()
        if f.normal.dot(nrm) < 0: f.normal_flip()
    bm.normal_update(); u = PAL.u(col); rr = random.Random(seed + 3)
    def sh(f):
        cen = f.calc_center_median(); dd = (cen - c); up = dd.y / (r * sq + 1e-6)
        jit = rr.uniform(-.06, .06); out = []
        for i, l in enumerate(f.loops):
            t = clamp((l.vert.co.y - y0) / (y1 - y0))
            v = .2 + .5 * t + (.16 if i == 2 else 0) + .14 * smooth((up - .35) / .5) - .14 * smooth((-up - .1) / .5) + jit
            out.append((u, clamp(v, .04, .96)))
        return out
    P.add(bm, sh)

def roots(S, base, rng, n, R, reach, rad, lift=1.1, ground=None):
    """buttress roots gripping the ground: start high on the flare, run out low along the ground, dive in at the end"""
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-.3, .3); o = Vector((math.cos(a), 0, math.sin(a)))
        g = Vector(S.N[base][0]) if ground is None else Vector(ground)
        i = S.add(Vector(S.N[base][0]) + o * R * .55 + Vector((0, R * lift, 0)), rad, base)
        for t, (out, y, rk) in enumerate(((.35, R * .45, .8), (.6, R * .12, .58), (.82, -R * .02, .4), (1.0, -R * .3, .22))):
            p = Vector((g.x, g.y, g.z)) + o * reach * out + Vector((math.sin(a * 3 + t) * .6, y, math.cos(a * 2 + t) * .6))
            i = S.add(p, rad * rk, i)

def gnarled_tree(seed=9, h=34.0, part='all'):
    """HERO: the islet tree, rebuilt as a real tree. Skinned skeleton: thick flared base with 6 buttress roots hugging
    the islet, a twisting trunk leaning out over the lake (-X), forking into 4 limbs that split again under the
    canopy; bark furrows. Canopy: 8 overlapping leaf masses of varied size placed on the branch tips -> one irregular,
    asymmetric crown with gaps where limbs show."""
    rng = random.Random(seed); P = Prop('GnarledCanopy' if part == 'canopy' else 'GnarledTree'); S = Skel()
    b = S.add((0, -1.5, 0), h * .13)
    lean = Vector((-1, 0, -.3)).normalized()
    i = b; pts = []
    for k in range(1, 7):
        t = k / 6
        p = Vector((0, -1.5 + h * .52 * t, 0)) + lean * (h * .3 * t ** 1.5) + Vector((math.sin(t * 5) * 1.1, 0, math.cos(t * 4) * .9 - .9))
        i = S.add(p, lerp(h * .11, h * .062, t), i); pts.append(i)
    roots(S, b, rng, 7, h * .1, h * .38, h * .075)
    tips = []
    limbs = [(pts[5], (-.8, .5, .35), h * .46, 1), (pts[5], (.45, .7, -.5), h * .38, 1), (pts[4], (-.35, .55, -.8), h * .4, 1), (pts[4], (.8, .65, .35), h * .26, 0)]
    for base_i, d, L, sub in limbs:
        r0 = S.N[base_i][1] * .62
        mid = S.grow(base_i, d, L * .6, r0, r0 * .6, 3, rng, bend=(0, .06, 0))
        for q in range(2):
            dd = Vector(d) + Vector((rng.uniform(-.7, .7), rng.uniform(.1, .5), rng.uniform(-.7, .7)))
            tips.append(S.grow(mid, dd, L * .45, r0 * .5, r0 * .22, 2, rng, bend=(0, .05, 0)))
    tip_top = S.grow(pts[5], (-.2, 1, -.1), h * .2, h * .045, h * .02, 2, rng); tips.append(tip_top)
    if part != 'canopy':                                                     # split in two props: one MeshPart must be <= 20k tris
        bm = skin_mesh(S.N, S.E, 2)
        bark(P, bm, -1.5, h * .75, seed, groove=.22)
    if part == 'trunk': return P
    # canopy masses on the tips (varied size), plus fillers bridging them into one crown
    centres = []
    for k, ti in enumerate(tips):
        p = Vector(S.N[ti][0]); r = h * rng.uniform(.15, .26) * (1.3 if ti == tip_top else 1)
        centres.append((p + Vector((rng.uniform(-1, 1), r * rng.uniform(.1, .45), rng.uniform(-1, 1))), r))
    cy = sum(cc.y for cc, _ in centres) / len(centres) + h * .04          # pull masses toward one crown layer
    centres = [(Vector((cc.x, lerp(cc.y, cy, .55), cc.z)), r) for cc, r in centres]
    base_c = list(centres)
    for i, (ca, ra) in enumerate(base_c):                                   # bridge every mass to its nearest neighbour
        j = min((j for j in range(len(base_c)) if j != i), key=lambda j: (base_c[j][0] - ca).length)
        cb, rb = base_c[j]; dd = (cb - ca).length
        if dd > (ra + rb) * .7:
            centres.append(((ca + cb) / 2 + Vector((0, h * .03, 0)), max(ra, rb) * .75))
    hub = sum((cc for cc, _ in base_c), Vector()) / len(base_c)
    centres.append((hub + Vector((0, h * .06, 0)), h * .22))                 # one crown core so it reads as a single dome
    for k, (cc, r) in enumerate(centres):
        leaf_mass(P, cc, r, 'leaf', seed * 31 + k, density=.82, leaf=2.1, sq=.7)
    return P

def broadleaf(seed=1, h=22.0, col='leaf', name=None):
    """stylised broadleaf (same method, lighter): skinned trunk with a root flare forking into 3-4 limbs, a leaf mass
    on each limb tip + a crown mass -> asymmetric rounded crown with gaps"""
    rng = random.Random(seed); P = Prop(name or 'Broadleaf%d' % seed); S = Skel()
    b = S.add((0, -1.0, 0), h * .085)
    top = S.grow(b, (rng.uniform(-.1, .1), 1, rng.uniform(-.1, .1)), h * .48, h * .065, h * .045, 3, rng, bend=(0, 0, 0), wob=.06)
    roots(S, b + 1, rng, 4, h * .09, h * .22, h * .045, lift=-.6, ground=(0, -1.0, 0))
    tips = []
    nl = rng.randint(3, 4)
    for k in range(nl):
        a = k * math.tau / nl + rng.uniform(-.4, .4)
        tips.append(S.grow(top, (math.cos(a), rng.uniform(.5, 1.3), math.sin(a)), h * rng.uniform(.24, .34), h * .035, h * .014, 2, rng, bend=(0, .05, 0)))
    tips.append(S.grow(top, (0, 1, 0), h * .32, h * .03, h * .014, 2, rng))
    bm = skin_mesh(S.N, S.E, 1)
    bark(P, bm, -1, h * .7, seed, groove=.1)
    for k, ti in enumerate(tips):
        p = Vector(S.N[ti][0]); r = h * rng.uniform(.15, .19) * (1.15 if k == len(tips) - 1 else 1)
        leaf_mass(P, p + Vector((0, r * .3, 0)), r, col, seed * 13 + k, density=.9, leaf=1.45, sq=.8)
    return P


# ------------------------------------------------------------------ conifer v3 + fuller crowns (placement-check pass)
def pine(seed=1, h=34.0, name=None, tiers=9, cards=17):
    """soft full conifer: tapered skinned trunk; per tier a dark smooth drooping core skirt (lathe) carrying a ring of
    long needle-branch cards (pointed, slightly folded, drooping, bright tips) at random angles and lengths, tiers
    overlapping so the silhouette is one soft cone with a ragged scalloped edge (no flat slabs)"""
    rng = random.Random(seed); P = Prop(name or 'Pine%d' % seed)
    trunk(P, [(0, -1.2, 0), (0, h * .4, 0), (0, h * .92, 0)], [h * .045, h * .028, h * .008], sides=7)
    u = PAL.u('pine')
    for i in range(tiers):
        t = i / (tiers - 1); y = h * (.21 + .7 * t); R = h * (.28 * (1 - t) ** .9 + .035); dr = R * .95
        prof = [(h * .02, y + dr * .9), (R * .5, y + dr * .35), (R * .82, y - dr * .2), (h * .02, y - dr * .05)]
        core = lathe(prof, n=8, a0=rng.uniform(0, 1))
        P.add(core, lambda f, lo=y - dr * .3, hi=y + dr: [(u, clamp(.12 + .35 * clamp((l.vert.co.y - lo) / (hi - lo)), .04, .96)) for l in f.loops], smooth=True)
        bm = bmesh.new(); n = max(6, int(cards * (1 - t * .55)))
        for k in range(n):
            a = k * math.tau / n + rng.uniform(-.25, .25)
            d = Vector((math.cos(a), 0, math.sin(a)))
            L = R * rng.uniform(1.0, 1.3); W = L * rng.uniform(.3, .4)
            root = Vector((0, y + dr * rng.uniform(.3, .75), 0)) + d * R * .08
            dirv = (d + Vector((0, -rng.uniform(.38, .62), 0))).normalized()
            side = Vector((-d.z, 0, d.x)) * W / 2
            tip = root + dirv * L; mid = root + dirv * L * .5 + Vector((0, L * .1, 0))
            vs = [bm.verts.new(p) for p in (root, mid + side, tip, mid - side, mid + Vector((0, L * .06, 0)) + d * L * .02)]
            for f in ((vs[0], vs[1], vs[4]), (vs[1], vs[2], vs[4]), (vs[2], vs[3], vs[4]), (vs[3], vs[0], vs[4])): bm.faces.new(f)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        for f in bm.faces:
            if f.normal.y < 0: f.normal_flip()
        lo, hi = y - R * .6, y + dr
        P.add(bm, lambda f, lo=lo, hi=hi, R=R, i=i: [(u, clamp(.22 + .42 * clamp((l.vert.co.y - lo) / (hi - lo)) + .03 * i + (.16 if math.hypot(l.vert.co.x, l.vert.co.z) > R * .8 else 0), .04, .96)) for l in f.loops])
    tip = lathe([(h * .035, h * .9), (h * .02, h * .96), (0, h * 1.02)], n=8)
    P.add(tip, V('pine', h * .9, h, .45, .7), smooth=True)
    return P

def merged_crown(P, tips, col, seed, h, density, leaf, sq=.78, pull=.5, core=.24):
    """tip masses pulled toward one crown height, bridged to their nearest neighbour, plus one crown core over the hub
    -> one full, rounded, irregular crown (no stray separate balls)"""
    cy = sum(c.y for c, _ in tips) / len(tips) + h * .04
    cs = [(Vector((c.x, lerp(c.y, cy, pull), c.z)), r) for c, r in tips]
    base_c = list(cs)
    for i, (ca, ra) in enumerate(base_c):
        j = min((j for j in range(len(base_c)) if j != i), key=lambda j: (base_c[j][0] - ca).length)
        cb, rb = base_c[j]
        if (cb - ca).length > (ra + rb) * .7: cs.append(((ca + cb) / 2 + Vector((0, h * .03, 0)), max(ra, rb) * .75))
    hub = sum((c for c, _ in base_c), Vector()) / len(base_c)
    cs.append((hub + Vector((0, h * .07, 0)), h * core))
    for k, (c, r) in enumerate(cs): leaf_mass(P, c, r, col, seed * 13 + k, density=density, leaf=leaf, sq=sq)

def broadleaf(seed=1, h=22.0, col='leaf', name=None):
    """stylised broadleaf: skinned trunk with a root flare forking into 3-4 limbs; one merged, full, rounded crown"""
    rng = random.Random(seed); P = Prop(name or 'Broadleaf%d' % seed); S = Skel()
    b = S.add((0, -1.0, 0), h * .085)
    top = S.grow(b, (rng.uniform(-.1, .1), 1, rng.uniform(-.1, .1)), h * .48, h * .065, h * .045, 3, rng, bend=(0, 0, 0), wob=.06)
    roots(S, b + 1, rng, 4, h * .09, h * .22, h * .045, lift=-.6, ground=(0, -1.0, 0))
    tips = []; nl = rng.randint(3, 4)
    for k in range(nl):
        a = k * math.tau / nl + rng.uniform(-.4, .4)
        ti = S.grow(top, (math.cos(a), rng.uniform(.6, 1.2), math.sin(a)), h * rng.uniform(.22, .3), h * .035, h * .014, 2, rng, bend=(0, .05, 0))
        r = h * rng.uniform(.16, .2); tips.append((Vector(S.N[ti][0]) + Vector((0, r * .3, 0)), r))
    ti = S.grow(top, (0, 1, 0), h * .3, h * .03, h * .014, 2, rng); r = h * .21
    tips.append((Vector(S.N[ti][0]) + Vector((0, r * .25, 0)), r))
    bark(P, skin_mesh(S.N, S.E, 1), -1, h * .7, seed, groove=.1)
    merged_crown(P, tips, col, seed, h, density=.62, leaf=1.5, sq=.8, pull=.45, core=.26)
    return P
