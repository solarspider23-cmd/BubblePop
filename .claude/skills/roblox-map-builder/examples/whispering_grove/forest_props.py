# Whispering Grove prop library (background Blender 5.2). Built in ROBLOX space (X east, Y up, Z south; 1 unit = 1 stud),
# origin = bottom centre of each prop, front = -Z... converted to Blender by pro_lib.KM on output.
# Reuses scripts/pro_lib.py (palette strips, bmesh primitives, Sh shading).
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from pro_lib import (Palette, Sh, MB, xf, box, hull, rock_pts, rock, ngon_prism, cyl, spike, tube, ribbon, KM, nz, bevel,
                     clamp, lerp, smooth)

PAL = Palette({
    'bark':   ('#3d2a1f', '#6b4a32', '#9c7350'),
    'leaf':   ('#1d5527', '#3f9440', '#9ad866'),
    'leaf2':  ('#2f6a1e', '#6aa832', '#cfe86e'),
    'pine':   ('#123d2c', '#23674a', '#5aa878'),
    'grass':  ('#2d6b2a', '#4fa23c', '#8fd05a'),
    'moss':   ('#2f5d22', '#5a9a34', '#a4d45e'),
    'dirt':   ('#5a3f2a', '#8b6a45', '#c09c70'),
    'stone':  ('#4a4d55', '#7e828c', '#bcc0c8'),
    'stonew': ('#5b5148', '#938776', '#d0c4b0'),
    'wood':   ('#4a2f1c', '#7d5434', '#b8885e'),
    'wooddk': ('#2e1d12', '#4f3322', '#7a543c'),
    'red':    ('#6e1515', '#c8392a', '#f47a5c'),
    'cream':  ('#b8a888', '#e8dcc0', '#fff8e6'),
    'gold':   ('#8a5a10', '#dca222', '#ffe680'),
    'cloth':  ('#2a3f7a', '#4c70c4', '#94b4f2'),
})
GLOW = {'crystal': '#9a5cff', 'lamp': '#ffb347', 'shroom': '#1fc8ff', 'fire': '#ff6a1a', 'fire2': '#ffd23c', 'rune': '#3fe6ff',
        'gold': '#ffc61a', 'door': '#4ff5df'}
GLOW_E = {'lamp': 4.0, 'fire': 3.2, 'fire2': 4.5, 'door': 2.6, 'shroom': .8, 'crystal': 1.0, 'rune': 1.4}     # emission strength (default 1.8)

def S(col, base=.5, up=.25, jit=.08, seed=0, **k): return Sh(PAL, col, base=base, up=up, jit=jit, seed=seed, **k)

class Prop:
    """one kit prop: a solid mesh on the palette + optional glow meshes (Neon in Roblox, emission in previews)"""
    def __init__(self, name):
        self.name = name; self.solid = MB(); self.glow = {}
    def add(self, bm, sh, smooth=False): self.solid.add(bm, sh, smooth)
    def gadd(self, bm, key):
        u = PAL.u('white')
        self.glow.setdefault(key, MB()).add(bm, lambda f: [(u, .5)] * len(f.loops))
    @property
    def tris(self): return self.solid.tris + sum(m.tris for m in self.glow.values())

# ------------------------------------------------------------------ helpers
def blob(r, seed, n=42, sq=.82):
    return hull(rock_pts((r, r * sq, r), n=n, seed=seed))

def at(bm, loc=(0, 0, 0), rot=(0, 0, 0), s=None): return xf(bm, loc, rot, s)

def ring_pts(c, r, n, y=0.0, a0=0.0):
    return [Vector((c[0] + math.cos(a0 + i * math.tau / n) * r, y, c[2] + math.sin(a0 + i * math.tau / n) * r)) for i in range(n)]

def curve(a, b, lift, n=6):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / (n - 1)) + Vector((0, math.sin(i / (n - 1) * math.pi) * lift, 0)) for i in range(n)]

def leafy(P, centres, col, h0, h1, seed, sq=.8):
    """faceted canopy blobs with a height gradient (dark under, light on top)"""
    sh = S(col, grad=(h0, h1, .22, .86), up=.18, vn=(9, seed, .12))
    for i, (c, r) in enumerate(centres):
        P.add(at(blob(r, seed * 31 + i, sq=sq), c), sh)

# ------------------------------------------------------------------ trees
def oak(seed, h=24.0, col='leaf'):
    rng = random.Random(seed); P = Prop('Oak%d' % seed)
    bend = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * h * .05
    pts = [Vector((0, -.4, 0)) + bend * (t * t) + Vector((0, h * .58 * t, 0)) for t in [i / 6 for i in range(7)]]
    top = pts[-1]
    bark = S('bark', grad=(0, h * .6, .25, .7), jit=.06)
    P.add(tube(pts, [h * .068 * (1 - .45 * i / 6) for i in range(7)], sides=9, rough=.07, seed=seed), bark)
    for k in range(5):                                          # root flares
        a = k * math.tau / 5 + rng.uniform(-.3, .3); R = h * .065
        P.add(tube([Vector((0, R * 1.4, 0)), Vector((math.cos(a) * R * 1.6, R * .5, math.sin(a) * R * 1.6)),
                    Vector((math.cos(a) * R * 2.6, -.3, math.sin(a) * R * 2.6))], [R * .55, R * .4, R * .12], sides=6), bark)
    cs = [(top + Vector((0, h * .14, 0)), h * .27)]
    for k in range(rng.randint(4, 6)):
        a = k * math.tau / 5 + rng.uniform(-.4, .4); d = h * rng.uniform(.18, .27)
        c = top + Vector((math.cos(a) * d, h * rng.uniform(-.04, .14), math.sin(a) * d))
        cs.append((c, h * rng.uniform(.16, .22)))
        P.add(tube(curve(pts[4], c - (c - pts[4]).normalized() * h * .1, h * .03, 4), [h * .035, h * .022, h * .014, h * .01], sides=6), bark)
    leafy(P, cs, col, top.y - h * .25, top.y + h * .42, seed)
    return P

def pine(seed, h=30.0):
    rng = random.Random(seed); P = Prop('Pine%d' % seed)
    P.add(tube([Vector((0, -.4, 0)), Vector((0, h * .5, 0)), Vector((0, h * .96, 0))], [h * .042, h * .028, h * .01], sides=8, rough=.05),
          S('bark', grad=(0, h * .5, .2, .55)))
    tiers = 5
    for i in range(tiers):
        y = h * (.22 + .145 * i); R = h * .3 * (1 - i * .17); ht = h * .27
        bm = bmesh.new(); n = 14; yaw = rng.uniform(0, math.tau)
        tip = bm.verts.new((0, y + ht, 0))
        rim = []
        for k in range(n):
            a = yaw + k * math.tau / n; rr = R * (1 if k % 2 == 0 else .74)
            rim.append(bm.verts.new((math.cos(a) * rr, y - (.55 if k % 2 == 0 else 0) * h * .03, math.sin(a) * rr)))
        inner = [bm.verts.new((math.cos(yaw + k * math.tau / 7) * R * .3, y + h * .045, math.sin(yaw + k * math.tau / 7) * R * .3)) for k in range(7)]
        for k in range(n): bm.faces.new((tip, rim[(k + 1) % n], rim[k]))
        # underside: rim -> inner ring
        for k in range(n):
            j = int(k / n * 7) % 7; j2 = int((k + 1) / n * 7) % 7
            if j == j2: bm.faces.new((rim[k], rim[(k + 1) % n], inner[j]))
            else: bm.faces.new((rim[k], rim[(k + 1) % n], inner[j2], inner[j]))
        bm.faces.new(inner)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, S('pine', grad=(y - h * .02, y + ht, .2 + i * .05, .62 + i * .06), up=.2, jit=.05, seed=seed + i))
    return P

def arch_outline(hw, spring, n=14):
    """door outline in the XY plane, open at the bottom: left foot -> up -> semicircle -> down -> right foot"""
    pts = [(-hw, 0.0), (-hw, spring)]
    pts += [(-math.cos(math.pi * i / n) * hw, spring + math.sin(math.pi * i / n) * hw) for i in range(1, n)]
    return pts + [(hw, spring), (hw, 0.0)]

def arch_frame(hw, spring, t, z0, z1):
    """solid stone frame between the inner outline and one t wider, extruded z0..z1 (z1 = front)"""
    bm = bmesh.new(); I, O = arch_outline(hw, spring), arch_outline(hw + t, spring)
    v = {(k, i, z): bm.verts.new((p[0], p[1], z)) for k, L in (('i', I), ('o', O)) for i, p in enumerate(L) for z in (z0, z1)}
    n = len(I)
    for i in range(n - 1):
        bm.faces.new((v['i', i, z1], v['o', i, z1], v['o', i + 1, z1], v['i', i + 1, z1]))    # front
        bm.faces.new((v['i', i + 1, z0], v['o', i + 1, z0], v['o', i, z0], v['i', i, z0]))    # back
        bm.faces.new((v['i', i, z0], v['i', i, z1], v['i', i + 1, z1], v['i', i + 1, z0]))    # inner (soffit)
        bm.faces.new((v['o', i + 1, z0], v['o', i + 1, z1], v['o', i, z1], v['o', i, z0]))    # outer
    for i in (0, n - 1):                                                                     # feet
        bm.faces.new((v['i', i, z0], v['o', i, z0], v['o', i, z1], v['i', i, z1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bevel(bm, .12, 1, [e for e in bm.edges if all(abs(x.co.z - z1) < 1e-4 for x in e.verts)])
    return bm

def arch_prism(hw, spring, z0, z1, y0=0.0):
    """closed solid of the door opening (boolean cutter)"""
    L = [(x, y if y > 0 else y0) for x, y in arch_outline(hw, spring)]
    bm = bmesh.new(); F = [bm.verts.new((x, y, z1)) for x, y in L]; B = [bm.verts.new((x, y, z0)) for x, y in L]
    bm.faces.new(F); bm.faces.new(list(reversed(B)))
    n = len(L)
    for i in range(n): j = (i + 1) % n; bm.faces.new((F[j], F[i], B[i], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def bool_diff(bm, cut):
    """exact boolean A - B through a throwaway modifier (background-safe)"""
    sc = bpy.context.scene; objs = []
    for b in (bm, cut):
        me = bpy.data.meshes.new('_bool'); b.to_mesh(me); b.free()
        o = bpy.data.objects.new('_bool', me); sc.collection.objects.link(o); objs.append(o)
    m = objs[0].modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = objs[1]; m.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(objs[0].evaluated_get(dg))
    out = bmesh.new(); out.from_mesh(res)
    for o in objs:
        me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(res)
    return out

def arch_tunnel(hw, spring, z_front, z_back):
    """the dark passage behind the frame: walls + floor only, faces pointing inward"""
    bm = bmesh.new(); L = arch_outline(hw, spring)
    F = [bm.verts.new((x, y, z_front)) for x, y in L]; B = [bm.verts.new((x, y, z_back)) for x, y in L]
    for i in range(len(L) - 1): bm.faces.new((F[i + 1], F[i], B[i], B[i + 1]))
    bm.faces.new((F[0], F[-1], B[-1], B[0]))                                                 # floor
    bm.normal_update()
    c = Vector((0, spring * .6, (z_front + z_back) / 2))
    for f in bm.faces:
        if f.normal.dot(c - f.calc_center_median()) < 0: f.normal_flip()
    return bm

def arch_cap(hw, spring, z):
    bm = bmesh.new(); f = bm.faces.new([bm.verts.new((x, y, z)) for x, y in arch_outline(hw, spring)])
    f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    return bm

def birch(seed, h=24.0):
    rng = random.Random(seed); P = Prop('Birch%d' % seed)
    lean = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * h * .03
    pts = [Vector((0, -.4, 0)) + lean * t * t + Vector((0, h * .78 * t, 0)) for t in [i / 6 for i in range(7)]]
    P.add(tube(pts, [h * .035 * (1 - .4 * i / 6) for i in range(7)], sides=8, rough=.04, seed=seed), S('cream', grad=(0, h, .55, .85), jit=.03))
    for k in range(14):                                        # dark bark marks
        t = rng.uniform(.05, .9); p = pts[0].lerp(pts[-1], t); a = rng.uniform(0, math.tau); rr = h * .035 * (1 - .4 * t)
        P.add(at(box((rr * rng.uniform(.6, 1.1), .18, .14)), p + Vector((math.cos(a) * rr * .92, 0, math.sin(a) * rr * .92)), (0, -math.degrees(a) + 90, 0)),
              S('wooddk', base=.25, jit=.04))
    top = pts[-1]; cs = []
    for k in range(5):
        a = rng.uniform(0, math.tau); d = h * rng.uniform(.04, .12)
        cs.append((top + Vector((math.cos(a) * d, h * (.0 + .12 * k / 4) - h * .12, math.sin(a) * d)), h * rng.uniform(.12, .16)))
    leafy(P, cs, 'leaf2', top.y - h * .25, top.y + h * .2, seed, sq=1.15)
    return P

def bush(seed, r=2.4, col='leaf'):
    rng = random.Random(seed); P = Prop('Bush%d' % seed)
    cs = [(Vector((0, r * .55, 0)), r)]
    for k in range(rng.randint(2, 4)):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(.6, .9)
        cs.append((Vector((math.cos(a) * d, r * .42, math.sin(a) * d)), r * rng.uniform(.55, .8)))
    leafy(P, cs, col, -r * .2, r * 1.5, seed, sq=.78)
    if rng.random() < .5:                                       # berries
        for k in range(6):
            a = rng.uniform(0, math.tau); e = rng.uniform(.3, .9)
            p = Vector((math.cos(a) * r * .95 * math.cos(e), r * .55 + r * .7 * math.sin(e), math.sin(a) * r * .95 * math.cos(e)))
            P.add(at(blob(.22, seed + k, n=14), p), S('red', base=.6, jit=.1))
    return P

def frond(P, a, L, lift, w, seed, col='leaf2'):
    """one modelled fern frond: a serrated, thickened strip arching up then down"""
    d = Vector((math.cos(a), 0, math.sin(a))); side = Vector((-d.z, 0, d.x))
    n = 10; top, bot = [], []
    bm = bmesh.new()
    for i in range(n + 1):
        t = i / n
        c = d * L * t + Vector((0, math.sin(t * math.pi * .85) * lift - t * t * lift * .4 + .1, 0))
        ww = w * math.sin(math.pi * min(t * 1.1, 1)) ** .7 * (1 if i % 2 else .6)
        top.append((bm.verts.new(c + side * ww), bm.verts.new(c + Vector((0, .06, 0))), bm.verts.new(c - side * ww)))
        bot.append([bm.verts.new(v.co - Vector((0, .07, 0))) for v in top[-1]])
    for i in range(n):
        for k in range(2):
            bm.faces.new((top[i][k], top[i][k + 1], top[i + 1][k + 1], top[i + 1][k]))
            bm.faces.new((bot[i + 1][k], bot[i + 1][k + 1], bot[i][k + 1], bot[i][k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, S(col, grad=(0, lift, .3, .78), up=.1, jit=.04))

def fern(seed, s=1.0):
    rng = random.Random(seed); P = Prop('Fern%d' % seed)
    for k in range(rng.randint(7, 9)):
        frond(P, k * math.tau / 8 + rng.uniform(-.25, .25), 3.4 * s * rng.uniform(.8, 1.15), 1.8 * s, .55 * s, seed + k)
    return P

def mushroom(seed, s=1.0, glow=False, n_spots=6):
    rng = random.Random(seed); P = Prop(('GlowShroom%d' if glow else 'Shroom%d') % seed)
    hs = 1.5 * s * rng.uniform(.85, 1.2); lean = rng.uniform(-8, 8)
    stem = tube([Vector((0, 0, 0)), Vector((0, hs * .5, 0)), Vector((0, hs, 0))], [.38 * s, .3 * s, .34 * s], sides=10)
    P.add(at(stem, rot=(lean, 0, 0)), S('cream', grad=(0, hs, .45, .85), jit=.03))
    R = 1.15 * s; pts = []
    for i in range(70):
        u = rng.random(); a = rng.uniform(0, math.tau); e = math.asin(u)            # upper hemisphere
        pts.append(Vector((math.cos(a) * math.cos(e) * R, math.sin(e) * R * .62, math.sin(a) * math.cos(e) * R)))
    for p in ring_pts((0, 0, 0), R * .98, 12, y=-.08 * s): pts.append(p)
    for p in ring_pts((0, 0, 0), R * .3, 6, y=-.25 * s): pts.append(p)
    cap = at(hull(pts), (0, hs * .96, 0), (lean, 0, 0))
    if glow: P.gadd(cap, 'shroom')
    else: P.add(cap, S('red', grad=(hs, hs + R * .6, .35, .8), jit=.03))
    if not glow:
        for k in range(n_spots):
            a = rng.uniform(0, math.tau); e = rng.uniform(.35, 1.2)
            p = Vector((math.cos(a) * math.cos(e) * R, math.sin(e) * R * .62 + .02, math.sin(a) * math.cos(e) * R))
            sp = hull(rock_pts((.2 * s, .07 * s, .2 * s), n=12, seed=seed + k))
            nrm = Vector((p.x / R, p.y / (R * .62 * .62), p.z / R)).normalized()
            q = nrm.to_track_quat('Y', 'Z')
            bmesh.ops.rotate(sp, cent=Vector(), matrix=q.to_matrix(), verts=sp.verts)
            P.add(at(at(sp, p + Vector((0, hs * .96, 0))), rot=(0, 0, 0)), S('cream', base=.75, jit=.04))
    return P

def mossy_rock(seed, r=3.0):
    P = Prop('Rock%d' % seed)
    P.add(rock((r, r * .62, r * .85), seed=seed, n=30, flat=.45), S('stone', base=.45, up=.3, jit=.1, top='moss', thr=.62, topbase=.5, seed=seed))
    rng = random.Random(seed)
    for k in range(rng.randint(0, 2)):
        a = rng.uniform(0, math.tau)
        P.add(at(rock((r * .35, r * .25, r * .3), seed=seed + 9 + k, n=16), (math.cos(a) * r * 1.05, 0, math.sin(a) * r * 1.05)),
              S('stone', base=.4, top='moss', thr=.6, seed=seed + k))
    return P

def log(seed, L=9.0, r=1.0):
    rng = random.Random(seed); P = Prop('Log%d' % seed)
    pts = [Vector((-L / 2 + L * i / 5, r * .92, rng.uniform(-.1, .1))) for i in range(6)]
    P.add(tube(pts, r, sides=10, rough=.06, seed=seed, cap0=False, cap1=False), S('bark', base=.45, up=.15))
    for sgn in (-1, 1):
        cap = at(cyl(r * 1.04, .25, sides=10), rot=(0, 0, 90))
        P.add(at(cap, (sgn * (L / 2 + .02) - (.25 if sgn > 0 else 0) * 0, r * .92, 0)), S('wood', base=.72, jit=.02))
        inner = at(cyl(r * .5, .3, sides=10), rot=(0, 0, 90))
        P.add(at(inner, (sgn * (L / 2 + .05) - (.3 if sgn > 0 else 0) * 0, r * .92, 0)), S('wood', base=.5, jit=.02))
    P.add(at(blob(r * .7, seed, n=20, sq=.4), (rng.uniform(-L / 4, L / 4), r * 1.75, 0)), S('moss', base=.55))
    for k in range(3):
        m = mushroom(seed + 50 + k, s=.35)
        for f_mb in (m.solid,): P.solid.merge(shift(f_mb, (rng.uniform(-L / 3, L / 3), r * 1.6, r * .5)))
    return P

def shift(mb, d):
    o = MB(); o.V = [(v[0] + d[0], v[1] + d[1], v[2] + d[2]) for v in mb.V]; o.F = list(mb.F); o.UV = list(mb.UV); o.SM = list(mb.SM)
    return o

def stump(seed, r=1.6):
    rng = random.Random(seed); P = Prop('Stump%d' % seed)
    P.add(cyl(r, 1.8, sides=11, r2=r * .9, y0=-.3), S('bark', grad=(0, 1.8, .3, .6)))
    P.add(cyl(r * .86, .12, sides=11, y0=1.5), S('wood', base=.72, jit=.01))
    P.add(cyl(r * .45, .14, sides=11, y0=1.52), S('wood', base=.5, jit=.01))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(-.3, .3)
        P.add(tube([Vector((math.cos(a) * r * .7, .9, math.sin(a) * r * .7)), Vector((math.cos(a) * r * 1.5, -.2, math.sin(a) * r * 1.5))],
                   [r * .3, r * .12], sides=6), S('bark', base=.45))
    return P

def flower_patch(seed, col='red', n=7, rad=1.6):
    rng = random.Random(seed); P = Prop('Flowers%s%d' % (col, seed))
    for i in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, rad); c = Vector((math.cos(a) * d, 0, math.sin(a) * d))
        h = rng.uniform(.9, 1.6)
        P.add(at(cyl(.06, h, sides=4), c), S('leaf', base=.4))
        for k in range(5):
            pet = box((.34, .06, .2), 0)
            P.add(at(pet, c + Vector((math.cos(k * 1.257) * .22, h, math.sin(k * 1.257) * .22)), (12, -math.degrees(k * 1.257), 0)),
                  S(col, base=.62, jit=.08, seed=seed + i))
        P.add(at(blob(.12, seed + i, n=10), c + Vector((0, h + .04, 0))), S('gold', base=.7))
        for k in range(2):
            lf = box((.4, .04, .16))
            P.add(at(lf, c + Vector((0, h * .4, 0)), (20, rng.uniform(0, 360), 0)), S('leaf', base=.55))
    return P

def grass_tuft(seed, n=9, h=1.8):
    rng = random.Random(seed); P = Prop('Tuft%d' % seed)
    for i in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .5)
        bl = spike(.13, h * rng.uniform(.6, 1.1), sides=3, shoulder=.3)
        P.add(at(bl, (math.cos(a) * d, -.1, math.sin(a) * d), (rng.uniform(-25, 25), rng.uniform(0, 360), rng.uniform(-25, 25))),
              S('grass', grad=(0, h, .3, .85), jit=.04))
    return P

# ------------------------------------------------------------------ made things
def lantern_post(seed=1, h=7.0):
    P = Prop('LanternPost')
    P.add(cyl(.32, h, sides=6, r2=.26), S('wooddk', grad=(0, h, .3, .6)))
    P.add(cyl(.55, .5, sides=6, y0=0), S('stone', base=.5))
    P.add(at(box((2.0, .3, .3), .05), (.8, h - .3, 0)), S('wooddk', base=.5))
    cx = 1.6; cy = h - 1.6
    P.add(at(box((.9, .12, .9), .03), (cx, cy + .65, 0)), S('wooddk', base=.4))
    P.add(at(spike(.62, .55, sides=4, shoulder=.05, rot0=math.pi / 4), (cx, cy + .7, 0)), S('wooddk', base=.5))
    P.add(at(box((.9, .12, .9), .03), (cx, cy - .65, 0)), S('wooddk', base=.4))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(at(box((.1, 1.3, .1)), (cx + sx * .4, cy, sz * .4)), S('wooddk', base=.4))
    P.gadd(at(box((.55, .95, .55), .08), (cx, cy, 0)), 'lamp')
    P.add(at(cyl(.05, 1.0, sides=4), (cx, cy + .9, 0)), S('stone', base=.3))
    return P

def fence(seed=1, L=8.0):
    rng = random.Random(seed); P = Prop('Fence%d' % seed)
    for x in (-L / 2, L / 2):
        P.add(at(cyl(.28, 3.2, sides=6, r2=.22), (x, -.3, 0), (rng.uniform(-3, 3), 0, rng.uniform(-3, 3))), S('wood', grad=(0, 3, .3, .6)))
        P.add(at(spike(.3, .4, sides=6, shoulder=.1), (x, 2.9, 0)), S('wood', base=.55))
    for y in (1.0, 2.2):
        P.add(at(box((L + .8, .32, .2), .06), (0, y + rng.uniform(-.1, .1), 0), (0, 0, rng.uniform(-2, 2))), S('wood', base=.55, jit=.06, seed=seed))
    return P

def crate(seed=1, s=2.4):
    P = Prop('Crate%d' % seed)
    P.add(at(box((s, s, s), .08), (0, s / 2, 0)), S('wood', base=.55, jit=.04, seed=seed))
    for y in (.15, s - .15):
        for z in (-1, 1):
            P.add(at(box((s + .08, .28, .12)), (0, y, z * (s / 2 + .02))), S('wooddk', base=.5))
            P.add(at(box((.12, .28, s + .08)), (z * (s / 2 + .02), y, 0)), S('wooddk', base=.5))
    for z in (-1, 1):
        P.add(at(box((s * 1.2, .26, .1)), (0, s / 2, z * (s / 2 + .04)), (0, 0, 45)), S('wooddk', base=.5))
    return P

def barrel(seed=1, h=3.0, r=1.1):
    P = Prop('Barrel%d' % seed)
    pts = [Vector((0, h * i / 6, 0)) for i in range(7)]
    rad = [r * (.86 + .14 * math.sin(math.pi * i / 6)) for i in range(7)]
    P.add(tube(pts, rad, sides=14), S('wood', grad=(0, h, .35, .7), jit=.05))
    for y in (h * .14, h * .5, h * .86):
        k = .86 + .14 * math.sin(math.pi * y / h)
        P.add(cyl(r * k + .06, .2, sides=14, y0=y - .1), S('stone', base=.35, up=.1))
    P.add(cyl(r * .86 - .05, .08, sides=14, y0=h - .02), S('wooddk', base=.5))
    return P

def tent(seed=1, w=7.0, d=8.0, h=5.5):
    P = Prop('Tent%d' % seed)
    tri = [(-w / 2, 0), (w / 2, 0), (0, h)]
    bm = bmesh.new()
    F = [bm.verts.new((x, y, -d / 2)) for x, y in tri]; B = [bm.verts.new((x, y, d / 2)) for x, y in tri]
    bm.faces.new(B); bm.faces.new(list(reversed(F)))
    for i in range(3):
        j = (i + 1) % 3
        if i == 0: continue
        bm.faces.new((F[i], F[j], B[j], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, S('cloth', grad=(0, h, .3, .72), jit=.02))
    door = bmesh.new()
    dv = [door.verts.new((x, y, -d / 2 - .05)) for x, y in [(-w * .22, 0), (w * .22, 0), (0, h * .62)]]
    door.faces.new(dv); bmesh.ops.recalc_face_normals(door, faces=list(door.faces))
    for f in door.faces:
        if f.normal.z > 0: f.normal_flip()
    P.add(door, S('wooddk', base=.15, jit=0))
    P.add(at(tube([Vector((0, h + .3, -d / 2 - .6)), Vector((0, h + .3, d / 2 + .6))], .16, sides=6)), S('wood', base=.55))
    for z in (-d / 2 - .4, d / 2 + .4):
        for x in (-1, 1):
            P.add(tube([Vector((x * w * .52, -.2, z)), Vector((x * .1, h + .45, z))], .14, sides=5), S('wood', base=.5))
    P.add(at(box((w + 1.2, .14, d + 1.2), .05), (0, .05, 0)), S('wood', base=.35, jit=.02))
    return P

def campfire(seed=1):
    rng = random.Random(seed); P = Prop('Campfire')
    for k in range(10):
        a = k * math.tau / 10
        P.add(at(rock((.55, .4, .45), seed=seed + k, n=14), (math.cos(a) * 2.1, .1, math.sin(a) * 2.1), (0, -math.degrees(a), 0)), S('stone', base=.45, jit=.1, seed=k))
    for k in range(4):
        a = k * math.tau / 4 + .4
        P.add(tube([Vector((math.cos(a) * 1.7, .2, math.sin(a) * 1.7)), Vector((math.cos(a) * .2, 1.4, math.sin(a) * .2))], .26, sides=6), S('bark', base=.4))
    P.add(cyl(1.4, .1, sides=10, y0=0), S('wooddk', base=.1, jit=.02))
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.3, .3)
        P.gadd(flame_tongue(Vector((math.cos(a) * .55, .25, math.sin(a) * .55)), rng.uniform(2.2, 3.4), .62, a, seed + k), 'fire')
    for k in range(3):
        a = k * math.tau / 3 + .5
        P.gadd(flame_tongue(Vector((math.cos(a) * .2, .3, math.sin(a) * .2)), rng.uniform(1.4, 2.0), .38, a + 1, seed + 9 + k), 'fire2')
    for k in range(7):
        a = rng.uniform(0, math.tau); d = rng.uniform(.3, 1.2)
        P.gadd(at(blob(.13, seed + 30 + k, n=8, sq=1), (math.cos(a) * d, rng.uniform(3, 5.5), math.sin(a) * d)), 'fire2')
    return P

def flame_tongue(base, h, r, a, seed):
    '''a licking flame: a tapering tube that sways and twists to a point'''
    rng = random.Random(seed); sway = Vector((math.cos(a + 1.6), 0, math.sin(a + 1.6)))
    ts = [i / 6 for i in range(7)]
    pts = [base + Vector((0, h * t, 0)) + sway * math.sin(t * math.pi * 1.3 + rng.random()) * r * .7 * t for t in ts]
    return tube(pts, [r * (1 - t) ** .8 * (1 + .25 * math.sin(t * 9)) + .02 for t in ts], sides=6, rot0=a)

def quest_board(seed=1):
    P = Prop('QuestBoard')
    for x in (-4.2, 4.2):
        P.add(at(cyl(.42, 10.0, sides=6, r2=.34), (x, -.3, 0)), S('wood', grad=(0, 10, .3, .6)))
        P.add(at(cyl(.7, .6, sides=6), (x, -.1, 0)), S('stone', base=.5))
    P.add(at(box((8.6, 5.2, .4), .1), (0, 5.4, 0)), S('wood', base=.6, jit=.06, seed=3))
    for y in (2.75, 8.05):
        P.add(at(box((9.2, .45, .6), .1), (0, y, 0)), S('wooddk', base=.5))
    for x in (-4.2, 4.2):
        pass
    for sgn in (-1, 1):
        P.add(at(box((5.6, .3, 2.6), .08), (sgn * 2.4, 9.55, 0), (0, 0, -sgn * 24)), S('wooddk', base=.55, jit=.05, seed=sgn + 5))
    rng = random.Random(seed)
    for k in range(7):
        x = -3.2 + (k % 4) * 2.1 + rng.uniform(-.3, .3); y = 4.0 + (k // 4) * 2.2 + rng.uniform(-.3, .3)
        P.add(at(box((1.5, 1.8, .08)), (x, y, -.24), (0, 0, rng.uniform(-8, 8))), S('cream', base=.7, jit=.08, seed=k))
        P.add(at(cyl(.1, .1, sides=6), (x, y + .75, -.3), (90, 0, 0)), S('red', base=.5))
    # floating quest marker "!"
    P.gadd(at(box((.9, 2.6, .9), .2), (0, 14.4, 0)), 'gold')
    P.gadd(at(blob(.6, 5, n=16, sq=1), (0, 12.2, 0)), 'gold')
    return P

def signpost(seed=1):
    P = Prop('Signpost')
    P.add(cyl(.3, 6.5, sides=6, r2=.25, y0=-.3), S('wood', grad=(0, 6, .3, .6)))
    for y, yaw, L in ((5.2, 20, 3.6), (4.0, -150, 3.2), (2.9, 80, 3.0)):
        bm = ngon_prism([(0, -.45), (L, -.45), (L + .6, 0), (L, .45), (0, .45)][::-1], -.12, .12)
        bm = at(bm, rot=(90, 0, 0))
        P.add(at(bm, (0, y, 0), (0, yaw, 0)), S('wood', base=.62, jit=.04, seed=int(y * 10)))
    return P

def bridge(seed=1, L=26.0, w=8.0, arch=2.6):
    rng = random.Random(seed); P = Prop('Bridge')
    n = 22
    for i in range(n):
        z = -L / 2 + L * (i + .5) / n; t = z / (L / 2); y = arch * (1 - t * t)
        tilt = -math.degrees(math.atan(-2 * arch * t / (L / 2))) * 1
        P.add(at(box((w + rng.uniform(-.3, .3), .35, L / n * .9), .05), (rng.uniform(-.15, .15), y + .2, z), (tilt, rng.uniform(-1.5, 1.5), 0)),
              S('wood', base=.55, jit=.08, seed=i))
    for sx in (-1, 1):
        beam = [Vector((sx * (w / 2 - .5), arch * (1 - (z / (L / 2)) ** 2) - .25, z)) for z in [-L / 2 + L * i / 10 for i in range(11)]]
        P.add(tube(beam, .35, sides=6), S('wooddk', base=.45))
        tops = []
        for i in range(7):
            z = -L / 2 + 1 + (L - 2) * i / 6; y = arch * (1 - (z / (L / 2)) ** 2)
            P.add(at(cyl(.25, 3.0, sides=6), (sx * (w / 2 + .1), y - .2, z)), S('wood', grad=(0, 3, .3, .6)))
            tops.append(Vector((sx * (w / 2 + .1), y + 2.6, z)))
        P.add(tube(tops, .2, sides=6), S('wood', base=.6))
    for sz in (-1, 1):
        for sx in (-1, 1):
            P.add(at(rock((1.4, 1.0, 1.4), seed=seed + sx + 3 * sz, n=18), (sx * (w / 2 + .8), -.2, sz * (L / 2 - .5))), S('stone', base=.45, top='moss', thr=.6))
    return P

# ------------------------------------------------------------------ hero pieces
def altar(seed=7):
    P = Prop('RngAltar')
    oct8 = lambda r: [(math.cos(a * math.tau / 8 + math.pi / 8) * r, math.sin(a * math.tau / 8 + math.pi / 8) * r) for a in range(8)][::-1]
    for i, (r, y0, y1) in enumerate(((11.5, -.3, 1.0), (9.0, 1.0, 2.1), (6.4, 2.1, 3.2))):
        P.add(ngon_prism(oct8(r), y0, y1, .18), S('stonew', base=.45 + i * .07, up=.25, jit=.05, seed=i))
        P.add(ngon_prism(oct8(r + .12), y1 - .32, y1 - .12, 0), S('gold', base=.6, jit=.02))
    for a in range(8):
        ang = a * math.tau / 8 + math.pi / 8; c = Vector((math.cos(ang) * 10.2, 1.0, math.sin(ang) * 10.2))
        P.add(at(cyl(.55, 1.6, sides=6, bev=.1), c), S('stonew', base=.5))
        P.gadd(at(spike(.38, 1.6, sides=6, shoulder=.55), c + Vector((0, 1.6, 0))), 'crystal')
    for i in range(3):                                         # front steps (+Z, toward spawn)
        P.add(at(box((6.5, .9, 1.4), .12), (0, -.3 + i * 1.08 + .45, 12.1 - i * 2.4)), S('stonew', base=.55 + i * .04, jit=.03, seed=20 + i))
    for k in range(16):                                        # rune inlay ring on the top tier
        ang = k * math.tau / 16
        P.gadd(at(box((.5, .06, 1.1 if k % 2 else .6), .05), (math.cos(ang) * 4.6, 3.22, math.sin(ang) * 4.6), (0, -math.degrees(ang), 0)), 'rune')
    for k in range(3):                                         # small shards orbiting the main crystal
        ang = k * math.tau / 3 + .4
        P.gadd(at(spike(.42, 1.4, sides=5, shoulder=.5), (math.cos(ang) * 3.6, 9.6 + k * .9, math.sin(ang) * 3.6), (25, k * 40, 15)), 'crystal')
    P.add(cyl(2.4, 3.2, sides=8, r2=1.7, y0=3.2, bev=.15), S('stonew', grad=(3, 6.4, .4, .7)))
    P.add(cyl(2.7, .6, sides=8, r2=2.9, y0=6.4, bev=.1), S('gold', base=.55))
    # floating crystal (faceted icosahedron) + rune rings
    phi = (1 + 5 ** .5) / 2
    ico = [Vector(p).normalized() * 2.6 for p in [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0), (0, -1, phi), (0, 1, phi),
                                                 (0, -1, -phi), (0, 1, -phi), (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]]
    for p in ico: p.y *= 1.35
    P.gadd(at(hull(ico), (0, 11.2, 0), (20, 30, 0)), 'crystal')
    for r, tilt, yaw in ((4.6, 72, 0), (5.6, 64, 60)):
        circ = [Vector((math.cos(a * math.tau / 40) * r, 0, math.sin(a * math.tau / 40) * r)) for a in range(41)]
        P.gadd(at(tube(circ, .14, sides=5, cap0=False, cap1=False), (0, 11.2, 0), (tilt, yaw, 0)), 'rune')
    for k in range(4):                                         # standing rune stones
        ang = k * math.tau / 4 + math.pi / 4; c = Vector((math.cos(ang) * 16.5, -.4, math.sin(ang) * 16.5))
        yaw = -math.degrees(ang) + 90
        st = rock((1.6, 5.5, 1.0), seed=seed + k * 7, n=22, flat=.95)
        P.add(at(st, c + Vector((0, 5.0, 0)), (0, yaw, 0)), S('stone', base=.45, up=.2, jit=.07, top='moss', thr=.7, seed=k))
        for j in range(3):
            P.gadd(at(box((.6, .6, .12), .05), c + Vector((0, 3.3 + j * 1.6, 0)) + Vector((math.cos(ang), 0, math.sin(ang))) * -1.05,
                      (0, yaw, 45)), 'rune')
    return P

def elder_tree(seed=11, H=86.0):
    rng = random.Random(seed); P = Prop('ElderTree')
    bark = S('bark', grad=(0, 52, .2, .62), jit=.05, vn=(6, seed, .1))
    pts = [Vector((math.sin(t * 2.2) * 2.2, -7 + 58 * t, math.cos(t * 1.7) * 1.5 - 1.5)) for t in [i / 9 for i in range(10)]]
    zf, hw, spring, t = 11.0, 3.4, 6.2, 1.15         # door: front face z, half width, spring height, frame thickness
    trunk = tube(pts, [10.5 - 4.2 * (i / 9) ** .8 for i in range(10)], sides=16, rough=.07, seed=seed)
    P.add(bool_diff(trunk, arch_prism(hw - .05, spring, zf - 5.0, zf + 6, y0=-3)), bark)        # real opening
    for k in range(8):                                         # buttress roots
        a = k * math.tau / 8 + rng.uniform(-.2, .2)
        da = (a - math.pi / 2 + math.pi) % math.tau - math.pi
        if abs(da) < .75: a = math.pi / 2 + math.copysign(.8, da or 1)   # keep the door front (+Z) clear
        d = rng.uniform(19, 25)
        rp = [Vector((math.cos(a) * 6, 13, math.sin(a) * 6)), Vector((math.cos(a) * 11, 6, math.sin(a) * 11)),
              Vector((math.cos(a) * (d - 5), 1.2, math.sin(a) * (d - 5))), Vector((math.cos(a) * d, -2.6, math.sin(a) * d))]
        P.add(tube(rp, [4.6, 3.2, 1.6, .5], sides=9, rough=.08, seed=seed + k), bark)
    top = pts[-1]; cs = [(top + Vector((0, 20, 0)), 22)]
    for k in range(9):
        a = k * math.tau / 9 + rng.uniform(-.25, .25); d = rng.uniform(22, 31)
        c = Vector((math.cos(a) * d, rng.uniform(56, 72), math.sin(a) * d))
        cs.append((c, rng.uniform(12.5, 16.5)))
        bp = [pts[rng.randint(6, 8)], (pts[7] + c) * .5 + Vector((0, 4, 0)), c - (c - pts[7]).normalized() * 9]
        P.add(tube(bp, [4.0, 2.4, 1.2], sides=8, rough=.06), bark)
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(8, 18)
        cs.append((Vector((math.cos(a) * d, rng.uniform(74, 84), math.sin(a) * d)), rng.uniform(10, 13)))
    leafy(P, cs, 'leaf2', 44, 100, seed, sq=.78)
    # glowing door in the trunk front (+Z = toward the plaza)
    P.add(arch_frame(hw, spring, t, zf - 3.4, zf + .35), S('stone', base=.55, up=.2, jit=.04, seed=3))
    P.add(at(box((1.5, 1.7, 1.2), .12), (0, spring + hw + t * .55, zf - .1)), S('stone', base=.68, jit=.02))      # keystone
    for sx in (-1, 1):                                                                                     # plinth blocks
        P.add(at(box((t + .5, 1.0, 1.6), .1), (sx * (hw + t / 2), .5, zf - .4)), S('stone', base=.45, jit=.02))
    P.add(arch_tunnel(hw - .02, spring, zf - .1, zf - 5.0), S('wooddk', base=.08, up=0, jit=0))
    P.gadd(arch_cap(hw - .02, spring, zf - 4.95), 'door')
    P.add(at(box((2 * (hw + t) + 1.2, .6, 3.0), .12), (0, .0, zf + 1.3)), S('stone', base=.5, up=.25, jit=.03, seed=5))   # threshold
    P.add(at(box((2 * (hw + t) - .4, .6, 2.2), .12), (0, -.45, zf + 3.6)), S('stone', base=.46, up=.25, jit=.03, seed=6))  # step
    for k in range(9):                                         # lanterns hanging from the canopy
        a = k * math.tau / 9 + rng.uniform(-.2, .2); d = rng.uniform(17, 27); top_y = rng.uniform(50, 54); L = rng.uniform(6, 13)
        c = Vector((math.cos(a) * d, top_y - L, math.sin(a) * d))
        P.add(tube([c + Vector((0, 1.1, 0)), Vector((c.x, top_y, c.z))], .07, sides=4), S('stone', base=.25))
        P.add(at(box((1.5, .22, 1.5), .05), c + Vector((0, 1.0, 0))), S('wooddk', base=.4))
        P.add(at(spike(1.05, .7, sides=4, shoulder=.05, rot0=math.pi / 4), c + Vector((0, 1.05, 0))), S('wooddk', base=.5))
        P.add(at(box((1.5, .22, 1.5), .05), c + Vector((0, -1.0, 0))), S('wooddk', base=.4))
        for sx in (-1, 1):
            for sz in (-1, 1): P.add(at(box((.14, 2.0, .14)), c + Vector((sx * .66, 0, sz * .66))), S('wooddk', base=.4))
        P.gadd(at(box((1.0, 1.7, 1.0), .12), c), 'lamp')
    for k in range(8):                                         # moss caps on the buttress roots
        a = k * math.tau / 8 + .3
        if abs((a - math.pi / 2 + math.pi) % math.tau - math.pi) < .75: continue
        P.add(at(blob(2.6, seed + 60 + k, n=20, sq=.35), (math.cos(a) * 12, 6.2, math.sin(a) * 12)), S('moss', base=.6, up=.2))
    return P

# ------------------------------------------------------------------ water edge
def reeds(seed, n=11):
    rng = random.Random(seed); P = Prop('Reeds%d' % seed)
    for i in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.2); h = rng.uniform(3, 5.2)
        b = Vector((math.cos(a) * d, -.2, math.sin(a) * d)); lean = Vector((rng.uniform(-.4, .4), 0, rng.uniform(-.4, .4)))
        P.add(tube([b, b + Vector((0, h * .5, 0)) + lean * .4, b + Vector((0, h, 0)) + lean], [.09, .07, .02], sides=4), S('leaf2', grad=(0, h, .3, .7)))
        if i % 3 == 0:
            P.add(at(cyl(.2, .9, sides=6), b + lean * .8 + Vector((0, h * .78, 0))), S('wood', base=.35))
    for k in range(5):
        a = rng.uniform(0, math.tau)
        bl = spike(.18, rng.uniform(1.6, 2.6), sides=3, shoulder=.3)
        P.add(at(bl, (math.cos(a) * .6, -.1, math.sin(a) * .6), (rng.uniform(-30, 30), rng.uniform(0, 360), rng.uniform(-30, 30))), S('grass', base=.55))
    return P

def lily(seed, n=4):
    rng = random.Random(seed); P = Prop('Lily%d' % seed)
    for i in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.4); c = Vector((math.cos(a) * d, 0, math.sin(a) * d)); r = rng.uniform(.7, 1.2)
        notch = rng.uniform(0, math.tau)
        poly = [(math.cos(notch + .35 + t * (math.tau - .7) / 10) * r, math.sin(notch + .35 + t * (math.tau - .7) / 10) * r) for t in range(11)] + [(0, 0)]
        P.add(at(ngon_prism(poly[::-1], 0, .08), c), S('leaf', base=.55, jit=.05, seed=i))
        if i == 0:
            for k in range(6):
                pet = spike(.22, .6, sides=3, shoulder=.4)
                P.add(at(pet, c + Vector((math.cos(k) * .2, .05, math.sin(k) * .2)), (35, -math.degrees(k), 0)), S('cream', base=.75))
            P.add(at(blob(.14, seed, n=8), c + Vector((0, .3, 0))), S('gold', base=.7))
    return P

def stepping_stones(seed, n=5, gap=2.4):
    rng = random.Random(seed); P = Prop('Steps%d' % seed)
    for i in range(n):
        P.add(at(rock((1.1, .45, .9), seed=seed + i, n=16, flat=.6), (rng.uniform(-.3, .3), 0, (i - (n - 1) / 2) * gap), (0, rng.uniform(0, 180), 0)),
              S('stone', base=.55, top='moss', thr=.85, topbase=.45, seed=i))
    return P

def crystal_cluster(seed=3, s=1.0):
    rng = random.Random(seed); P = Prop('CrystalCluster')
    P.add(rock((3.2 * s, 1.4 * s, 3.0 * s), seed=seed, n=26), S('stone', base=.4, top='moss', thr=.6))
    for k in range(7):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.8) * s; h = rng.uniform(3, 8) * s * (1.4 if k == 0 else 1)
        P.gadd(at(spike(rng.uniform(.5, .9) * s, h, sides=6, shoulder=.7), (math.cos(a) * d, .6 * s, math.sin(a) * d),
                  (rng.uniform(-22, 22), rng.uniform(0, 360), rng.uniform(-22, 22)) if k else (0, 0, 0)), 'crystal')
    return P

# ------------------------------------------------------------------ to Blender
MATS = {}
def materials():
    if MATS: return MATS
    MATS['pal'] = PAL.material('Grove')
    for k, h in GLOW.items():
        m = bpy.data.materials.new('Glow_' + k); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        from pro_lib import hexrgb
        lin = [x ** 2.2 for x in hexrgb(h)]                                    # sRGB hex -> linear
        b.inputs['Base Color'].default_value = (*[x * .45 for x in lin], 1)
        b.inputs['Emission Color'].default_value = (*lin, 1)
        # faceted glow: facets facing the camera glow hot, grazing facets fall back -> the shape reads
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .45
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = GLOW_E.get(k, 1.8)
        mr.inputs['To Max'].default_value = GLOW_E.get(k, 1.8) * .3
        nt.links.new(lw.outputs['Facing'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Emission Strength'])
        MATS[k] = m
    return MATS

def mesh_from(name, mb, mat):
    vb = [tuple(KM @ Vector(v)) for v in mb.V]
    me = bpy.data.meshes.new(name); me.from_pydata(vb, [], mb.F)
    uvl = me.uv_layers.new(name='UVMap')
    for fi, poly in enumerate(me.polygons):
        for k, l in enumerate(poly.loop_indices): uvl.data[l].uv = mb.UV[fi][k]
    me.polygons.foreach_set('use_smooth', mb.SM)
    me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free(); me.validate(); me.update()
    return me

def to_kit(P, coll):
    """kit meshes: <Prop> (solid) + <Prop>_Glow_<key>. Origin = bottom centre (prop built at y=0)."""
    M = materials(); out = {}
    if P.solid.F: out['solid'] = mesh_from(P.name, P.solid, M['pal'])
    for k, mb in P.glow.items(): out[k] = mesh_from('%s_Glow_%s' % (P.name, k), mb, M[k])
    for k, me in out.items():
        ob = bpy.data.objects.new(me.name, me); coll.objects.link(ob)
    return out
