# Sugarcrest Kingdom prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Machinery (Prop, S, at, materials, to_kit, bool_diff, arch_*) comes from the skill's grove module; every PROP here is new.
# Style: smooth, soft, glossy candy. Organic shapes are lathes / subdivided blobs with smooth shading, never faceted hulls.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector, noise as mn
import forest_props as G
from pro_lib import Palette, box, cyl, spike, tube, ngon_prism, clamp, lerp

G.PAL = Palette({
    'frost':   ('#4fae8a', '#9fe6c2', '#e8fff4'),     # mint frosting ground
    'pinkf':   ('#d8668f', '#ffaecb', '#fff0f6'),     # strawberry frosting
    'vanilla': ('#cfae82', '#fff0d2', '#ffffff'),     # icing, wafer cream
    'choc':    ('#24100a', '#5a2c16', '#9c5c36'),     # chocolate
    'ginger':  ('#6e3410', '#c07636', '#f2bf80'),     # gingerbread, biscuit, waffle, donut dough
    'cherry':  ('#9a0626', '#ff2a52', '#ffa0b4'),     # hard candy red
    'berry':   ('#9a1276', '#ff4cc0', '#ffb6e8'),
    'lime':    ('#2a9010', '#6ee838', '#d8ffa0'),
    'lemon':   ('#c88400', '#ffd21c', '#fff6a8'),
    'grape':   ('#45189a', '#9a5aff', '#dfccff'),
    'blue':    ('#0c58c8', '#3caeff', '#c4ecff'),
    'orange':  ('#c04c00', '#ff8a1c', '#ffd49e'),
    'jelly':   ('#06608e', '#1ec2e6', '#a4f6ff'),     # blue-raspberry jelly + glass (transparent in Roblox)
    'cotton':  ('#c472d6', '#f4a6ea', '#ffe4fc'),     # cotton candy
    'cloud':   ('#a898e2', '#eadcff', '#ffffff'),     # clouds, sugar
})
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'lamp': '#ffd27a', 'oven': '#ff8a2a', 'portal': '#ff5cf0', 'window': '#ffe08a', 'ring': '#7af0ff'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 3.6, 'oven': 3.4, 'portal': 3.0, 'window': 2.4, 'ring': 2.6})
Prop, S, at = G.Prop, G.S, G.at
PAL = G.PAL
CANDY = ['cherry', 'berry', 'lime', 'lemon', 'grape', 'blue', 'orange']
SIGNS = {}          # prop name -> list of blank sign faces (local x, y, z, yaw, w, h); the map turns them into hooks

# ------------------------------------------------------------------ shading helpers
def MS(lay, cols, base=.55, up=.25, grad=None, jit=0.0, seed=0):
    """multi-colour shade: face int layer `lay` picks the palette column cols[i]; optional height gradient"""
    rng = random.Random(seed)
    def f(face):
        col = cols[face[lay] % len(cols)]; u = PAL.u(col); n = face.normal
        if grad:
            y0, y1, a, b = grad
            return [(u, clamp(lerp(a, b, clamp((l.vert.co.y - y0) / (y1 - y0))) + up * n.y * .3, .04, .96)) for l in face.loops]
        v = base + up * n.y + (rng.random() - .5) * 2 * jit
        return [(u, clamp(v, .04, .96))] * len(face.loops)
    return f

def sugar(col, y0, y1, a=.4, b=.86, amp=.16, sc=.9, seed=0):
    """sugar-coated: height gradient plus fine per-vertex sparkle"""
    return S(col, grad=(y0, y1, a, b), up=.2, vn=(sc, seed, amp))

def orient(bm, axis_y=True):
    """flip faces so normals point away from the vertical axis (lathe shells) / out of a centre"""
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); d = Vector((c.x, 0, c.z))
        if d.length < 1e-4: d = Vector((0, 1 if c.y > 0 else -1, 0))
        if f.normal.dot(d) < 0: f.normal_flip()
    return bm

# ------------------------------------------------------------------ primitives
def lathe(prof, sides=16, rot0=0.0, close_top=True, close_bot=False, lay_fn=None):
    """revolve a profile [(r, y)] (bottom -> top, solid on the left of travel) round the Y axis. Normals follow the
    profile: outward = (dy, -dr). lay_fn(ring_i, side_a) -> int colour index (face layer 'c')"""
    bm = bmesh.new(); lay = bm.faces.layers.int.new('c'); rings = []
    for r, y in prof:
        if r < 1e-4: rings.append([bm.verts.new((0, y, 0))])
        else: rings.append([bm.verts.new((math.cos(rot0 + a * math.tau / sides) * r, y, math.sin(rot0 + a * math.tau / sides) * r)) for a in range(sides)])
    def mk(vs, i, a, want):
        try: f = bm.faces.new(vs)
        except ValueError: return
        f.normal_update()
        if f.normal.dot(want) < 0: f.normal_flip()
        if lay_fn: f[lay] = lay_fn(i, a)
    for i in range(len(prof) - 1):
        A, B = rings[i], rings[i + 1]
        (r0, y0), (r1, y1) = prof[i], prof[i + 1]
        dr, dy = r1 - r0, y1 - y0
        for a in range(sides):
            ang = rot0 + (a + .5) * math.tau / sides
            want = Vector((math.cos(ang) * dy, -dr, math.sin(ang) * dy))
            if want.length < 1e-6: continue
            b = (a + 1) % sides
            if len(A) == 1 and len(B) == 1: break
            if len(A) == 1: mk((A[0], B[a], B[b]), i, a, want)
            elif len(B) == 1: mk((A[a], A[b], B[0]), i, a, want)
            else: mk((A[a], A[b], B[b], B[a]), i, a, want)
    for idx, flag, w in ((0, close_bot, Vector((0, -1, 0))), (-1, close_top, Vector((0, 1, 0)))):
        if flag and len(rings[idx]) > 1:
            f = bm.faces.new(rings[idx]); f.normal_update()
            if f.normal.dot(w) < 0: f.normal_flip()
    return bm

def round_prof(r, h, rr, n=3, y0=0.0, top=True, bot=False):
    """profile of a cylinder with rounded top (and bottom) edges, radius rr"""
    p = [(0, y0)] if bot else [(0, y0), (r, y0)]
    if bot:
        for k in range(n + 1):
            a = -math.pi / 2 + k / n * math.pi / 2
            p.append((r - rr + math.cos(a) * rr, y0 + rr + math.sin(a) * rr))
    if top:
        for k in range(n + 1):
            a = k / n * math.pi / 2
            p.append((r - rr + math.cos(a) * rr, y0 + h - rr + math.sin(a) * rr))
        p.append((0, y0 + h))
    else:
        p += [(r, y0 + h), (0, y0 + h)]
    return p

def soft(r, seed=0, sub=3, amp=.14, freq=1.2, sq=(1, 1, 1)):
    """smooth lumpy ball: icosphere (sub 2 = 80, 3 = 320 tris) displaced by low-frequency noise"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        k = 1 + amp * (mn.noise(d * freq + Vector((seed * 3.1, seed * 1.7, -seed * 2.3))))
        v.co = Vector((d.x * r * sq[0] * k, d.y * r * sq[1] * k, d.z * r * sq[2] * k))
    return bm

def ball(r, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); return bm

def closed_torus(R, r, n=32, sides=10, flat=None, plane='XZ'):
    """explicitly closed torus grid (no seam). plane XZ = ring axis Y (lying), XY = ring axis Z (standing)"""
    sx, sy = flat if flat else (1, 1)
    bm = bmesh.new(); V = []
    for i in range(n):
        u = i * math.tau / n; cu, su = math.cos(u), math.sin(u); row = []
        for j in range(sides):
            v = j * math.tau / sides; rr = R + math.cos(v) * r * sx; h = math.sin(v) * r * sy
            row.append(bm.verts.new((cu * rr, h, su * rr) if plane == 'XZ' else (cu * rr, su * rr, h)))
        V.append(row)
    for i in range(n):
        for j in range(sides):
            f = bm.faces.new((V[i][j], V[(i + 1) % n][j], V[(i + 1) % n][(j + 1) % sides], V[i][(j + 1) % sides]))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        q = Vector((c.x, 0, c.z)) if plane == 'XZ' else Vector((c.x, c.y, 0))
        d = c - (q.normalized() * R if q.length > 1e-6 else Vector())
        if f.normal.dot(d) < 0: f.normal_flip()
    return bm

def torus(R, r, n=32, sides=10, flat=None):
    """torus in the XZ plane (ring axis = Y)"""
    return closed_torus(R, r, n, sides, flat, 'XZ')

def striped_tube(pts, r, sides=10, stripes=2, twist=1.0, cap=True, step=.9):
    """tube with HELICAL stripes (face layer 'c' = 0/1): the stripe index shifts one face per ring step of ~1.1 r"""
    from pro_lib import frames
    pts = [Vector(p) for p in pts]
    dense = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / (r * step)))
        dense += [a.lerp(b, k / n) for k in range(1, n + 1)]
    T, N, B = frames(dense)
    bm = bmesh.new(); lay = bm.faces.layers.int.new('c'); rings = []
    cum = 0.0
    for i, p in enumerate(dense):
        if i: cum += (dense[i] - dense[i - 1]).length
        off = cum / (r * 9.0) * math.tau * twist                       # one stripe turn per ~6 r of length
        rings.append([bm.verts.new(p + (N[i] * math.cos(off + a * math.tau / sides) + B[i] * math.sin(off + a * math.tau / sides)) * r) for a in range(sides)])
    w = max(1, sides // (2 * stripes))
    for i in range(len(rings) - 1):
        for a in range(sides):
            b = (a + 1) % sides
            f = bm.faces.new((rings[i][a], rings[i][b], rings[i + 1][b], rings[i + 1][a]))
            f[lay] = (a // w) % 2
    if cap:
        f = bm.faces.new(list(reversed(rings[0]))); f[lay] = 1
        f = bm.faces.new(rings[-1]); f[lay] = 1
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); k = min(range(len(dense)), key=lambda j: (dense[j] - c).length_squared)
        d = c - dense[k]
        if len(f.verts) > 4: d = T[k] * (1 if k == len(dense) - 1 else -1)
        if f.normal.dot(d) < 0: f.normal_flip()
    return bm

def drip(length, r, sides=6):
    """a hanging icing drip: tapered neck from y 0 down to -length ending in a round bead"""
    prof = [(0, -length - r * .95), (r * .62, -length - r * .7), (r * .95, -length), (r * .8, -length * .55), (r * .7, -length * .2), (r * .78, .02), (0, .02)]
    return lathe(prof, sides=sides, close_top=False)

def drip_ring(P, R, y, col, n, seed, lmin=.8, lmax=2.6, r=.42, base=.85, skip=None):
    """drips hanging round a circle of radius R at height y, sitting on the surface"""
    rng = random.Random(seed)
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-.25, .25) * math.tau / n
        if skip and skip(a): continue
        L = rng.uniform(lmin, lmax)
        P.add(at(drip(L, r * rng.uniform(.8, 1.15)), (math.cos(a) * R, y, math.sin(a) * R)), S(col, base=base, up=.15, jit=0), smooth=True)

def sprinkle(L=.9, r=.14):
    """one rod sprinkle (open-ended 5-sided rod, 10 tris)"""
    return tube([Vector((-L / 2, 0, 0)), Vector((L / 2, 0, 0))], r, sides=5, cap0=False, cap1=False)

def sprinkles_on(P, pts_normals, seed, cols=('cherry', 'lemon', 'blue', 'lime', 'vanilla', 'berry'), L=.9, r=.14):
    """sprinkles lying on a surface: list of (point, normal)"""
    rng = random.Random(seed)
    for k, (p, n) in enumerate(pts_normals):
        n = Vector(n).normalized(); t = n.orthogonal().normalized()
        q = t.copy(); q.rotate(__import__('mathutils').Quaternion(n, rng.uniform(0, math.tau)))
        bm = sprinkle(L * rng.uniform(.8, 1.2), r)
        rot = Vector((1, 0, 0)).rotation_difference(q).to_matrix()
        bmesh.ops.rotate(bm, cent=Vector(), matrix=rot, verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(p) + n * r * .6, verts=bm.verts)
        P.add(bm, S(cols[(k + seed) % len(cols)], base=.62, up=.15, jit=0))

def piping(pts, r, beads=True, sides=5, closed=False):
    """icing piping along a polyline: beaded (radius pulses, short runs) or a smooth rope (long runs, cheap)"""
    pts = [Vector(p) for p in pts]
    if closed: pts = pts + [pts[0]]
    step = r * 1.15 if beads else 4.0
    dense = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        dense += [a.lerp(b, k / n) for k in range(1, n + 1)]
    radii = [r * (1.0 if k % 2 else .7) for k in range(len(dense))] if beads else r
    return tube(dense, radii, sides=sides, cap0=not closed, cap1=not closed)

def ring_pts(R, y, n, a0=0.0):
    return [Vector((math.cos(a0 + i * math.tau / n) * R, y, math.sin(a0 + i * math.tau / n) * R)) for i in range(n)]

def sign_plate(P, name, x, y, z, w, h, yaw=0.0, frame='vanilla'):
    """blank wafer sign: cream face in a beaded icing frame, facing -Z rotated by yaw. Recorded for hooks."""
    P.add(at(box((w, h, .5), .18), (0, 0, 0), (0, 0, 0)) if False else at(at(box((w, h, .5), .18), (0, 0, 0)), (x, y, z), (0, yaw, 0)),
          S('vanilla', base=.8, up=.1, jit=0))
    fr = [Vector((-w / 2 - .1, -h / 2 - .1, -.3)), Vector((w / 2 + .1, -h / 2 - .1, -.3)), Vector((w / 2 + .1, h / 2 + .1, -.3)),
          Vector((-w / 2 - .1, h / 2 + .1, -.3))]
    P.add(at(piping(fr, .32, closed=True), (x, y, z), (0, yaw, 0)), S(frame if frame != 'vanilla' else 'berry', base=.6, up=.15, jit=0), smooth=True)
    SIGNS.setdefault(P.name, []).append((x, y, z, yaw, w, h))

# ------------------------------------------------------------------ shapes reused by several props
def cupcake_liner(r0, r1, h, pleats=16, cols=('berry', 'vanilla'), y0=0.0):
    """pleated paper liner: frustum whose radius alternates in/out per pleat, two-colour pleats"""
    sides = pleats * 2
    bm = bmesh.new(); lay = bm.faces.layers.int.new('c')
    def ringv(r, y):
        return [bm.verts.new((math.cos(a * math.tau / sides) * r * (1 if a % 2 == 0 else .93), y, math.sin(a * math.tau / sides) * r * (1 if a % 2 == 0 else .93))) for a in range(sides)]
    A = ringv(r0, y0); B = ringv(r1, y0 + h)
    for a in range(sides):
        b = (a + 1) % sides
        f = bm.faces.new((A[a], A[b], B[b], B[a])); f[lay] = (a // 2) % 2
    f = bm.faces.new(list(reversed(A))); f[lay] = 0
    orient(bm)
    return bm, lay

def swirl(R, h, turns=3.2, r0=None, r1=None, n=60, sides=10):
    """soft-serve swirl: a tube coiling up and in"""
    r0 = r0 or R * .38; r1 = r1 or R * .12
    pts = []; radii = []
    for k in range(n + 1):
        t = k / n; a = t * turns * math.tau
        rad = R * (1 - t * .88) - r0 * (1 - t) * .55
        pts.append(Vector((math.cos(a) * rad, h * (t ** .9) + r0 * .6, math.sin(a) * rad)))
        radii.append(lerp(r0, r1, t))
    pts.append(pts[-1] + Vector((0, r1 * 2.4, 0))); radii.append(.02)
    return tube(pts, radii, sides=sides, cap0=True, cap1=False)

def waffle(lay_cols=('ginger',)):
    pass

def waffle_lathe(prof, sides=20, rot0=0.0, close_top=True):
    """waffle grid: diagonal diamond pattern by alternating face shades (0 = ridge, 1 = pocket)"""
    return lathe(prof, sides=sides, rot0=rot0, close_top=close_top, lay_fn=lambda i, a: (i + a) % 2)

def WAF(base=.62):
    """shade for waffle_lathe: ridges light, pockets darker (same column)"""
    u = PAL.u('ginger')
    def f(face):
        ridge = face[face_lay(face)] == 0 if False else None
        return [(u, base)] * len(face.loops)
    return f

def two_tone(lay, col, a=.72, b=.48, up=.15):
    u = PAL.u(col)
    return lambda f: [(u, clamp((a if f[lay] == 0 else b) + up * f.normal.y, .04, .96))] * len(f.loops)

# ================================================================== STATIONS
def cupcake_fountain():
    """SPAWN: giant cupcake in a cookie basin of strawberry milk; syrup arcs fall from the frosting rim into the pool"""
    P = Prop('CupcakeFountain')
    # cookie basin: rounded ring wall, icing lip with drips, strawberry-milk pool
    P.add(lathe([(0, -.4), (16.2, -.4), (16.6, .4), (16.6, 2.2), (16.2, 2.9), (15.4, 3.1), (14.6, 2.7), (14.6, 1.4), (0, 1.4)], sides=40),
          S('ginger', grad=(-.4, 3.1, .38, .7)), smooth=True)
    P.add(lathe([(14.5, 2.7), (15.0, 3.15), (15.8, 3.35), (16.6, 3.05), (16.8, 2.6), (16.7, 2.4), (14.4, 2.4)], sides=40, close_top=False),
          S('vanilla', base=.82, up=.1, jit=0), smooth=True)
    drip_ring(P, 16.75, 2.6, 'vanilla', 30, 3, .4, 1.4, .34)
    P.add(lathe([(0, 1.3), (14.7, 1.3), (14.7, 1.9), (0, 1.9)], sides=40), S('pinkf', grad=(1.3, 1.9, .5, .72), up=.1), smooth=True)
    # pedestal column + cookie saucer brimming with strawberry milk that overflows in curtains into the pool
    P.add(lathe(round_prof(3.6, 5.0, .5, y0=1.5), sides=24), S('vanilla', grad=(1.5, 6.5, .55, .82)), smooth=True)
    for y in (2.6, 4.4): P.add(at(torus(3.65, .3, n=24, sides=6), (0, y, 0)), S('berry', base=.6, jit=0), smooth=True)
    P.add(lathe([(0, 5.6), (3.4, 5.6), (9.6, 7.2), (10.4, 8.3), (10.0, 8.7), (9.2, 8.2), (0, 8.2)], sides=36), S('ginger', grad=(5.6, 8.7, .42, .72)), smooth=True)
    P.add(lathe([(0, 8.0), (9.4, 8.0), (9.6, 8.45), (0, 8.45)], sides=36), S('pinkf', grad=(8, 8.5, .55, .75), up=.1), smooth=True)
    curt = lathe([(11.75, 1.7), (11.6, 4.6), (11.2, 7.2), (10.6, 8.55), (9.9, 8.75), (10.25, 8.45), (10.8, 7.1), (11.15, 4.5), (11.3, 1.7)], sides=56, close_top=False)
    for v in curt.verts:                                          # flutes: the falling milk thins into ribs near the pool
        a = math.atan2(v.co.z, v.co.x); t = clamp((8.6 - v.co.y) / 7.0)
        k = 1 + .045 * t * math.cos(a * 14); v.co.x *= k; v.co.z *= k
    P.add(curt, S('pinkf', grad=(1.7, 8.8, .55, .86), up=.1), smooth=True)
    P.add(at(torus(11.6, .55, n=48, sides=7, flat=(1.0, .5)), (0, 1.75, 0)), S('pinkf', base=.9, jit=0), smooth=True)
    bm, lay = cupcake_liner(5.6, 6.9, 6.0, pleats=18, y0=8.4)
    P.add(bm, MS(lay, ('berry', 'vanilla'), grad=(8.4, 14.4, .45, .78)), smooth=False)
    P.add(at(torus(6.95, .38, n=36, sides=6), (0, 14.4, 0)), S('vanilla', base=.85, jit=0), smooth=True)
    # cake top + frosting swirl + cherry
    Y = 3.6
    P.add(lathe([(0, 10.6 + Y), (6.9, 10.6 + Y), (7.4, 11.4 + Y), (7.2, 12.2 + Y), (0, 12.2 + Y)], sides=32), S('ginger', grad=(10.6 + Y, 12.2 + Y, .55, .75)), smooth=True)
    P.add(at(swirl(7.6, 7.5, turns=3.0, r0=2.4, r1=.7, n=72, sides=12), (0, 11.4 + Y, 0)), S('pinkf', grad=(11.5 + Y, 21.5 + Y, .45, .9), up=.15), smooth=True)
    P.add(at(ball(1.55, 3), (0, 22.4 + Y, 0)), S('cherry', grad=(21 + Y, 24 + Y, .5, .85)), smooth=True)
    P.add(tube([Vector((0, 23.6 + Y, 0)), Vector((.4, 25.0 + Y, .2)), Vector((1.3, 26.0 + Y, .6))], [.17, .15, .12], sides=5), S('lime', base=.45, jit=0), smooth=True)
    rng = random.Random(5); pn = []
    for k in range(50):                                           # sprinkles on the swirl coils (outer face of the tube)
        t = rng.uniform(.03, .8); ang = t * 3.0 * math.tau
        rad = 7.6 * (1 - t * .88) - 2.4 * (1 - t) * .55; rt = lerp(2.4, .7, t)
        c = Vector((math.cos(ang) * rad, 11.4 + Y + 7.5 * (t ** .9) + 2.4 * .6, math.sin(ang) * rad))
        out = Vector((math.cos(ang), 0, math.sin(ang))); up = rng.uniform(-.2, 1.0)
        n = (out * (1 - abs(up) * .5) + Vector((0, up, 0))).normalized()
        pn.append((c + n * rt, n))
    sprinkles_on(P, pn, 2)
    # macarons on the rim
    for k in range(4):
        a = k * math.tau / 4 + math.tau / 8; p = Vector((math.cos(a) * 15.6, 3.2, math.sin(a) * 15.6))
        col = ['lime', 'lemon', 'grape', 'pinkf'][k]
        for y, h in ((0, .7), (1.1, .7)):
            P.add(at(lathe(round_prof(1.25, h, .3, bot=True), sides=14), p + Vector((0, y, 0))), S(col, base=.62, up=.2, jit=0), smooth=True)
        P.add(at(lathe([(0, .65), (1.05, .65), (1.05, 1.15), (0, 1.15)], sides=14), p), S('vanilla', base=.85, jit=0), smooth=True)
    return P

def gable_roof_bars(P, w, d, y0, rise, cols=('choc',), seed=0):
    """roof of chocolate-bar tiles on both slopes; ridge along X at y0 + rise"""
    L = math.hypot(rise, d / 2); slope = math.degrees(math.atan2(rise, d / 2))
    nx, nz = max(2, int(w / 2.6)), max(2, int(L / 2.4))
    for sz in (-1, 1):
        rot = (sz * slope, 0, 0); ridge = (0, y0 + rise, 0)
        P.add(at(at(box((w + 1.2, .45, L + .8), .12), (0, 0, sz * (L + .8) / 2)), ridge, rot), S('choc', base=.32, jit=0))
        for i in range(nx):
            for j in range(nz):
                x = -w / 2 + (i + .5) * w / nx; z = (j + .5) * L / nz
                P.add(at(at(box((w / nx - .3, .5, L / nz - .3), .16), (x, .42, sz * z)), ridge, rot),
                      S(cols[(i + j) % len(cols)], base=.55, up=.25, jit=.03, seed=i * 7 + j + seed))

def sweet_shop():
    """SWEET SHOP: gingerbread cottage, chocolate-bar roof, gumdrop ridge, icing piping, striped counter awning,
    candy jars on the counter, candy-cane door posts. Front = -Z. ~22 x 16, ~19 tall."""
    P = Prop('SweetShop'); W, D, H = 20.0, 13.0, 10.0
    P.add(at(box((W + 3, 1.2, D + 3), .4), (0, -.2, 0)), S('vanilla', base=.7, up=.2))                  # icing plinth
    shell = G.bool_diff(at(box((W, H, D), .25), (0, H / 2 + .4, 0)), at(box((W - 1.6, H, D - 1.6)), (0, H / 2 + 1.2, 0)))
    cut = G.arch_prism(2.4, 5.2, -D / 2 - 2, -D / 2 + 2, y0=.2)
    cut2 = bmesh.new()
    for x in (-6.2,):                                                       # counter window (square) left of the door
        b = at(box((6.0, 3.8, 3.0)), (x, 5.2, -D / 2)); m = __import__('bpy').data.meshes.new('_t'); b.to_mesh(m); cut2.from_mesh(m); __import__('bpy').data.meshes.remove(m)
    for sx in (-1, 1):                                                      # round side windows
        b = at(cyl(1.7, 4.0, sides=16, y0=-2.0), (sx * W / 2, 6.0, 0), (0, 0, 90))
        m = __import__('bpy').data.meshes.new('_t'); b.to_mesh(m); cut2.from_mesh(m); __import__('bpy').data.meshes.remove(m)
    m = __import__('bpy').data.meshes.new('_t'); cut.to_mesh(m); cut2.from_mesh(m); __import__('bpy').data.meshes.remove(m)
    walls = G.bool_diff(shell, cut2)
    P.add(walls, S('ginger', grad=(0, H, .5, .7), up=.15), smooth=False)
    P.add(at(G.arch_frame(2.4, 5.2, .9, -D / 2 - .5, -D / 2 + .4), (0, .4, 0)), S('vanilla', base=.85, jit=0))
    P.add(at(G.arch_cap(2.4, 5.2, -D / 2 + .6), (0, .4, 0)), S('choc', base=.42, jit=0))                # chocolate door
    for k in range(3): P.add(at(box((4.4, .25, .2)), (0, 1.6 + k * 1.6, -D / 2 + .45)), S('choc', base=.6, jit=0))
    P.add(at(ball(.5, 2), (1.5, 3.4, -D / 2 + .2)), S('lemon', base=.7, jit=0), smooth=True)
    # counter window: frame, sill counter, jars, awning
    P.add(at(box((6.8, .5, 3.6), .15), (-6.2, 3.3, -D / 2 - .6)), S('vanilla', base=.82, jit=0))
    for k, (x, col) in enumerate(((-8.0, 'cherry'), (-6.2, 'lime'), (-4.4, 'grape'))):
        P.add(at(lathe(round_prof(.75, 1.9, .3), sides=12), (x, 3.55, -D / 2 - 1.2)), S('jelly', base=.7, up=0, jit=0), smooth=True)
        for j in range(4):
            P.add(at(ball(.33, 1), (x + (j % 2 - .5) * .5, 3.95 + j * .32, -D / 2 - 1.2 + (j // 2 - .5) * .4)), S(col, base=.62, jit=0), smooth=True)
        P.add(at(lathe(round_prof(.8, .4, .15), sides=12), (x, 5.45, -D / 2 - 1.2)), S('berry', base=.6, jit=0), smooth=True)
    for k in range(8):                                                      # scalloped striped awning
        x = -9.0 + k * .8 + .4
        col = 'cherry' if k % 2 else 'vanilla'
        P.add(at(box((.82, .22, 3.0), .06), (x, 8.2, -D / 2 - 1.3), (-28, 0, 0)), S(col, base=.66, jit=0))
        P.add(at(cyl(.41, .22, sides=10), (x, 7.5, -D / 2 - 2.65), (90, 0, 0)), S(col, base=.66, jit=0), smooth=True)
    # piping on corners and eaves
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(piping([(sx * W / 2, .6, sz * D / 2), (sx * W / 2, H + .4, sz * D / 2)], .38), S('vanilla', base=.86, jit=0), smooth=True)
    for sz in (-1, 1): P.add(piping([(-W / 2, H + .4, sz * D / 2), (W / 2, H + .4, sz * D / 2)], .4), S('vanilla', base=.86, jit=0), smooth=True)
    # gable ends: gingerbread triangles + scallop drips
    rise = 6.0
    for sz in (-1, 1): pass
    for sx in (-1, 1):
        tri = ngon_prism([(-D / 2, 0), (0, rise), (D / 2, 0)], -.5, .5)          # in local x-z: x = along D, z = up -> rotate
        bm = bmesh.new()
        vs = [bm.verts.new((sx * (W / 2 - .3) + dx, H + .4 + y, z)) for dx in (-.5, .5) for (z, y) in ((-D / 2, 0), (0, rise), (D / 2, 0))]
        bm.faces.new(vs[0:3]); bm.faces.new(vs[3:6])
        for a in range(3):
            b = (a + 1) % 3; bm.faces.new((vs[a], vs[b], vs[3 + b], vs[3 + a]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, S('ginger', base=.55, up=.1))
        P.add(at(cyl(1.1, .5, sides=14), (sx * (W / 2 + .05), H + 3.0, 0), (0, 0, 90)), S('cherry', base=.6, jit=0), smooth=True)   # gable candy
        P.add(piping([(sx * (W / 2 + .25), H + .4, -D / 2 - .4), (sx * (W / 2 + .25), H + .4 + rise + .3, 0), (sx * (W / 2 + .25), H + .4, D / 2 + .4)], .36),
              S('vanilla', base=.86, jit=0), smooth=True)
    gable_roof_bars(P, W + 1.0, D, H + .4, rise, cols=('choc', 'choc'))
    P.add(piping([(-W / 2 - 1, H + .55 + rise, 0), (W / 2 + 1, H + .55 + rise, 0)], .55), S('vanilla', base=.86, jit=0), smooth=True)
    for k in range(7):                                                      # gumdrop ridge
        x = -W / 2 + 1.4 + k * (W - 2.8) / 6
        P.add(at(lathe([(0, 0), (1.0, 0), (1.0, .5), (.78, 1.25), (.3, 1.55), (0, 1.6)], sides=14), (x, H + .7 + rise, 0)),
              sugar(CANDY[k % 7], H + rise, H + rise + 2.4, seed=k), smooth=True)
    # candy-cane posts beside the door + sign above it
    for sx in (-1, 1):
        x = sx * 3.9
        hook = [Vector((x, -.3, -D / 2 - 1.0)), Vector((x, 6.8, -D / 2 - 1.0))] + [Vector((x + sx * (1 - math.cos(a)) * -.9, 6.8 + math.sin(a) * .9, -D / 2 - 1.0)) for a in [math.pi * k / 5 for k in range(1, 6)]]
        bm = striped_tube(hook, .32, sides=10, stripes=2)
        P.add(bm, MS(bm.faces.layers.int['c'], ('cherry', 'vanilla'), base=.62, up=.15), smooth=True)
    for x in (-5.0, 5.0):                                                  # back windows: glowing candy glass in piped frames
        P.gadd(at(box((3.0, 3.4, .3), .2), (x, 5.8, D / 2 + .05)), 'window')
        P.add(at(piping([(-1.8, -2.0, 0), (1.8, -2.0, 0), (1.8, 1.2, 0), (0, 2.5, 0), (-1.8, 1.2, 0)], .3, closed=True), (x, 5.8, D / 2 + .25)), S('vanilla', base=.86, jit=0), smooth=True)
        P.add(at(box((3.8, .4, .9), .15), (x, 3.7, D / 2 + .4)), S('vanilla', base=.82, jit=0))
    sign_plate(P, 'SweetShop', 6.9, 6.6, -D / 2 - .35, 4.6, 2.6)
    # chimney: striped stack
    bm = striped_tube([(6.0, H + 2.5, 3.0), (6.0, H + 9.5, 3.0)], .9, sides=12, stripes=3)
    P.add(bm, MS(bm.faces.layers.int['c'], ('berry', 'vanilla'), base=.6), smooth=True)
    P.add(at(lathe(round_prof(1.3, .8, .3), sides=12), (6.0, H + 9.3, 3.0)), S('vanilla', base=.85, jit=0), smooth=True)
    return P

def bakery_oven():
    """UPGRADE OVEN: cookie-brick hearth, gingerbread dome with icing cap and gumdrop studs, glowing arched mouth,
    striped chimney, side counter with a cookie tray and rolling pin, blank sign on two candy posts. Front = -Z."""
    P = Prop('BakeryOven')
    P.add(lathe(round_prof(9.6, 1.0, .4, y0=-.5), sides=36), S('vanilla', base=.72, up=.2), smooth=True)
    hearth = lathe([(0, .5), (8.6, .5), (8.6, 4.6), (0, 4.6)], sides=28)
    P.add(hearth, S('ginger', grad=(.5, 4.6, .45, .62)), smooth=False)
    for y in (1.8, 3.2, 4.6): P.add(at(torus(8.7, .26, n=36, sides=5), (0, y, 0)), S('vanilla', base=.86, jit=0), smooth=True)
    dome = lathe([(8.0, 4.4)] + [(math.cos(a) * 8.0, 4.4 + math.sin(a) * 9.0) for a in [k / 10 * math.pi / 2 for k in range(1, 11)]], sides=28, close_top=False)
    mouth = G.arch_prism(3.0, 3.2, -10, -4, y0=3.0)
    dome = G.bool_diff(dome, mouth) if False else dome
    P.add(dome, S('ginger', grad=(4.4, 13.4, .45, .72)), smooth=True)
    P.add(lathe([(math.cos(a) * 8.25, 4.4 + math.sin(a) * 9.25) for a in [math.pi / 2 * (.45 + .55 * k / 7) for k in range(8)]][::-1][::-1], sides=28, close_top=False) if False else
          lathe([(math.cos(a) * 8.25, 4.4 + math.sin(a) * 9.25) for a in [math.pi / 2 * (.45 + .55 * k / 7) for k in range(8)]], sides=28, close_top=False),
          S('vanilla', base=.84, up=.1, jit=0), smooth=True)
    yr = 4.4 + math.sin(math.pi / 2 * .45) * 9.25; rr = math.cos(math.pi / 2 * .45) * 8.25
    drip_ring(P, rr - .05, yr + .1, 'vanilla', 18, 7, .8, 2.4, .45, skip=lambda a: abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .45)
    for k in range(10):                                                     # gumdrop studs round the dome
        a = k * math.tau / 10 + .3
        if abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .5: continue
        e = math.radians(30); p = Vector((math.cos(a) * 8.0 * math.cos(e), 4.4 + 9.0 * math.sin(e), math.sin(a) * 8.0 * math.cos(e)))
        P.add(at(lathe([(0, 0), (.8, 0), (.8, .4), (.6, 1.0), (0, 1.25)], sides=12), p, (0, 0, 0)), sugar(CANDY[k % 7], p.y, p.y + 1.3, seed=k), smooth=True)
    # mouth: chocolate arch frame + glowing fire + dark interior
    P.add(at(G.arch_frame(3.0, 2.6, 1.0, -8.9, -7.4), (0, 4.6, 0)), S('choc', base=.5, up=.2))
    P.add(at(G.arch_cap(3.0, 2.6, -7.5), (0, 4.6, 0)), S('choc', base=.12, jit=0))
    P.gadd(at(G.arch_cap(2.4, 2.2, -7.6), (0, 4.6, 0)), 'oven')
    for k in range(3):
        P.gadd(at(spike(.9, 2.4 - k * .4, sides=6, shoulder=.3), (-1.2 + k * 1.2, 4.7, -7.75)), 'oven')
    P.add(at(box((7.0, .6, 2.0), .2), (0, 4.6, -8.6)), S('vanilla', base=.8, jit=0))                          # sill
    # chimney
    bm = striped_tube([(4.0, 10.0, 4.5), (4.6, 18.5, 5.2)], 1.05, sides=12, stripes=3)
    P.add(bm, MS(bm.faces.layers.int['c'], ('cherry', 'vanilla'), base=.6), smooth=True)
    P.add(at(lathe(round_prof(1.55, .9, .35), sides=12), (4.6, 18.2, 5.2)), S('choc', base=.5, jit=0), smooth=True)
    # side counter (wafer layers) with a cookie tray and a rolling pin
    cx = -11.6
    for k in range(5):
        P.add(at(box((5.2, .8, 4.2), .12), (cx, .2 + k * .8, -1.0)), S('ginger' if k % 2 == 0 else 'vanilla', base=.6 if k % 2 == 0 else .82, up=.15, jit=0))
    P.add(at(box((5.8, .35, 4.8), .12), (cx, 4.3, -1.0)), S('choc', base=.45, jit=0))
    P.add(at(box((4.4, .2, 3.4), .08), (cx, 4.6, -1.0)), S('vanilla', base=.85, jit=0))
    for i in range(3):
        for j in range(2):
            p = Vector((cx - 1.4 + i * 1.4, 4.7, -1.8 + j * 1.6))
            P.add(at(lathe(round_prof(.6, .3, .12), sides=12), p), S('ginger', base=.7, jit=0), smooth=True)
            for q in range(3): P.add(at(ball(.12, 1), p + Vector((math.cos(q * 2.1 + i) * .3, .32, math.sin(q * 2.1 + j) * .3))), S('choc', base=.3, jit=0))
    P.add(at(cyl(.38, 4.4, sides=10), (cx + .4, 4.85, .9), (0, 0, 90)), S('ginger', base=.78, jit=0), smooth=True)
    for sx in (-1, 1): P.add(at(cyl(.18, 1.2, sides=6), (cx + .4 + sx * 2.8, 4.85, .9), (0, 0, 90)), S('cherry', base=.6, jit=0), smooth=True)
    # sign on two candy posts at the right
    for sx in (-1, 1):
        bm = striped_tube([(9.6 + sx * 2.8, -.3, -5.0), (9.6 + sx * 2.8, 8.2, -5.0)], .3, sides=10, stripes=2)
        P.add(bm, MS(bm.faces.layers.int['c'], ('lime', 'vanilla'), base=.62), smooth=True)
        P.add(at(ball(.55, 2), (9.6 + sx * 2.8, 8.4, -5.0)), S('lemon', base=.7, jit=0), smooth=True)
    sign_plate(P, 'BakeryOven', 9.6, 6.2, -5.0, 5.0, 2.8)
    return P

def candy_egg(h, seed, cols):
    """decorated egg: lathe egg with horizontal colour bands (bands from cols)"""
    prof = []
    for k in range(13):
        t = k / 12; a = -math.pi / 2 + t * math.pi
        r = math.cos(a) * h * .36 * (1 - .14 * math.sin(a)); y = h * .5 + math.sin(a) * h * .5
        prof.append((max(r, 0) if 0 < k < 12 else 0, y))
    band = lambda i, a: (0 if i < 3 or i > 9 else (1 if i in (3, 4, 8, 9) else (2 if (a // 2) % 2 else 0)))
    bm = lathe(prof, sides=16, close_top=False, lay_fn=band)
    return bm, bm.faces.layers.int['c']

def egg_machine():
    """PET / EGG MACHINE: sugar-glass dome over a cotton-candy nest of three decorated eggs, striped pedestal, a
    lollipop crank wheel, coin slot, glowing ring. Front = -Z."""
    P = Prop('EggMachine')
    P.add(lathe(round_prof(7.6, 1.1, .4, y0=-.5), sides=32), S('vanilla', base=.72, up=.2), smooth=True)
    ped = lathe([(0, .6), (6.4, .6), (6.0, 2.0), (5.2, 2.6), (5.0, 6.6), (6.2, 7.2), (6.4, 8.0), (0, 8.0)], sides=32,
                lay_fn=lambda i, a: 1 if i == 3 else 0)
    P.add(ped, MS(ped.faces.layers.int['c'], ('berry', 'vanilla'), grad=(.6, 8, .45, .75)), smooth=True)
    for y in (3.4, 5.8): P.add(at(torus(5.1, .3, n=32, sides=6), (0, y, 0)), S('lemon', base=.65, jit=0), smooth=True)
    P.gadd(at(torus(6.3, .3, n=40, sides=6), (0, 8.0, 0)), 'ring')
    # nest + eggs
    rng = random.Random(9)
    for k in range(9):
        a = k * math.tau / 9; P.add(at(soft(1.9, k, sub=2, amp=.2), (math.cos(a) * 3.6, 8.9, math.sin(a) * 3.6)), S('cotton', grad=(7.5, 10.8, .5, .85)), smooth=True)
    for k, (x, z, h, cols) in enumerate(((-1.8, .6, 5.0, ('blue', 'vanilla', 'lemon')), (1.9, .4, 4.6, ('lime', 'berry', 'vanilla')), (0, -1.6, 5.6, ('grape', 'lemon', 'cherry')))):
        bm, lay = candy_egg(h, k, cols)
        P.add(at(bm, (x, 8.2, z), (rng.uniform(-8, 8), rng.uniform(0, 360), rng.uniform(-8, 8))), MS(lay, cols, grad=(8, 8 + h, .5, .85)), smooth=True)
    P.add(lathe([(0, 8.0)] + [(math.cos(a) * 6.0, 8.0 + math.sin(a) * 7.0) for a in [k / 10 * math.pi / 2 for k in range(11)]], sides=32, close_top=False),
          S('jelly', base=.7, up=0, jit=0), smooth=True)                        # glass dome (transparent in Roblox)
    P.add(at(torus(6.05, .5, n=40, sides=8), (0, 8.15, 0)), S('vanilla', base=.85, jit=0), smooth=True)
    P.add(at(lathe(round_prof(1.6, 1.2, .5), sides=16), (0, 14.7, 0)), S('berry', base=.6, jit=0), smooth=True)
    P.add(at(ball(.9, 2), (0, 16.4, 0)), S('lemon', grad=(15.5, 17.3, .55, .85)), smooth=True)
    # crank: lollipop swirl wheel on the +X side
    P.add(at(cyl(.4, 2.2, sides=8), (5.0, 4.6, 0), (0, 0, 90)), S('vanilla', base=.75, jit=0), smooth=True)
    sw = swirl_disc(2.6, seed=3, cols=('cherry', 'vanilla'))
    P.add(at(sw[0], (7.5, 4.6, 0), (0, 0, 90)), MS(sw[1], ('cherry', 'vanilla'), base=.66, up=.1), smooth=True)
    P.add(at(cyl(.3, 2.0, sides=8), (7.9, 6.2, 0)), S('choc', base=.55, jit=0), smooth=True)
    P.add(at(ball(.55, 2), (7.9, 8.3, 0)), S('lime', base=.65, jit=0), smooth=True)
    # coin slot + sign on the front of the pedestal
    P.add(at(box((1.8, 2.4, .6), .25), (2.2, 4.6, -5.05)), S('lemon', base=.55, jit=0))
    P.add(at(box((.3, 1.4, .3)), (2.2, 4.6, -5.4)), S('choc', base=.15, jit=0))
    sign_plate(P, 'EggMachine', -1.4, 4.6, -5.35, 3.6, 2.2)
    return P

def swirl_disc(R, seed=0, turns=3.4, th=.55, cols=('cherry', 'vanilla')):
    """flat lollipop swirl: two interleaved Archimedean spiral ribbons (true spiral bands), domed, with a rim band.
    Disc in the XZ plane centred at y 0. Face layer 'c' = band index."""
    bm = bmesh.new(); lay = bm.faces.layers.int.new('c')
    pitch = R / (turns + .5); steps = int(turns * 36) + 1
    def ht(r): return th * .5 * (1 - (r / R) ** 2) + th * .45
    def P3(r, a, sgn): return Vector((math.cos(a) * r, sgn * ht(r), math.sin(a) * r))
    for band in (0, 1):
        for sgn in (1, -1):
            prev = None
            for k in range(steps + 1):
                t = k / 36.0; a = t * math.tau
                r0 = min(R, max(0.0, (t + band * .5 - .5) * pitch)); r1 = min(R, max(0.0, (t + band * .5) * pitch))
                cur = (bm.verts.new(P3(r0, a, sgn)), bm.verts.new(P3(r1, a, sgn)))
                if prev and r1 > 1e-3 and r0 < R - 1e-3:
                    f = bm.faces.new((prev[0], prev[1], cur[1], cur[0]) if sgn > 0 else (prev[1], prev[0], cur[0], cur[1]))
                    f[lay] = band
                prev = cur
    rim = []
    na = 48
    for j in range(na):
        a = j * math.tau / na
        rim.append((bm.verts.new(P3(R, a, 1)), bm.verts.new(P3(R, a, -1))))
    for j in range(na):
        k = (j + 1) % na
        f = bm.faces.new((rim[j][0], rim[k][0], rim[k][1], rim[j][1])); f[lay] = 0
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-3)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); d = Vector((0, 1 if c.y >= 0 else -1, 0)) if abs(c.y) > th * .44 and (c.x * c.x + c.z * c.z) < (R * .98) ** 2 else Vector((c.x, 0, c.z))
        if f.normal.dot(d) < 0: f.normal_flip()
    return bm, lay

def quest_stand():
    """QUEST STAND: wafer-cookie kiosk under a cupcake-liner umbrella topped with a cherry; quest board beside it with
    a blank face; rolled-wafer scrolls in a basket. Front = -Z."""
    P = Prop('QuestStand')
    P.add(lathe(round_prof(7.0, .9, .35, y0=-.5), sides=30), S('vanilla', base=.72, up=.2), smooth=True)
    for k in range(6):                                                      # wafer counter: alternating layers
        P.add(at(box((6.6, .62, 3.4), .1), (-1.2, .55 + k * .62, -1.2)), S('ginger' if k % 2 == 0 else 'vanilla', base=.6 if k % 2 == 0 else .84, up=.1, jit=0))
    for i in range(6):                                                      # wafer grid on the front
        P.add(at(box((.12, 3.5, .1)), (-4.2 + i * 1.2, 2.3, -2.95)), S('ginger', base=.42, jit=0))
    P.add(at(box((7.4, .4, 4.0), .15), (-1.2, 4.4, -1.2)), S('berry', base=.6, jit=0))
    # umbrella: striped pole + liner canopy + piping + cherry
    bm = striped_tube([(-1.2, 4.5, .4), (-1.2, 12.0, .4)], .32, sides=10, stripes=2)
    P.add(bm, MS(bm.faces.layers.int['c'], ('lemon', 'vanilla'), base=.62), smooth=True)
    sides = 32
    can = lathe([(6.4, 10.4), (5.6, 11.1), (2.0, 13.0), (0, 13.2)], sides=sides, close_top=False, lay_fn=lambda i, a: (a // 2) % 2)
    for v in can.verts:                                                     # scalloped pleats
        a = math.atan2(v.co.z, v.co.x); r = math.hypot(v.co.x, v.co.z)
        if r > 5: k = 1 - .05 * (math.cos(a * 16) * .5 + .5); v.co.x *= k; v.co.z *= k
    bmesh.ops.translate(can, vec=Vector((-1.2, 0, .4)), verts=can.verts)
    P.add(can, MS(can.faces.layers.int['c'], ('lemon', 'vanilla'), grad=(10.4, 13.2, .5, .82)), smooth=True)
    can2 = lathe([(0, 13.05), (2.0, 12.85), (5.5, 11.0), (6.3, 10.35)], sides=sides, close_top=False)
    bmesh.ops.translate(can2, vec=Vector((-1.2, 0, .4)), verts=can2.verts)
    P.add(can2, S('lemon', base=.35, jit=0), smooth=True)
    P.add(at(torus(6.4, .32, n=40, sides=6), (-1.2, 10.4, .4)), S('vanilla', base=.86, jit=0), smooth=True)
    drip_ring(P, 6.4, 10.3, 'vanilla', 14, 4, .4, 1.1, .3)
    P.add(at(ball(.95, 2), (-1.2, 14.0, .4)), S('cherry', grad=(13, 15, .5, .85)), smooth=True)
    P.add(tube([Vector((-1.2, 14.8, .4)), Vector((-.8, 15.9, .6))], .1, sides=5), S('lime', base=.45, jit=0), smooth=True)
    # quest board beside: two pretzel posts, piped frame, blank face
    for sx in (-1, 1):
        P.add(at(cyl(.32, 8.2, sides=8), (5.6 + sx * 2.4, -.3, -.4)), S('ginger', base=.62, jit=0), smooth=True)
        P.add(at(ball(.5, 2), (5.6 + sx * 2.4, 8.0, -.4)), S('lime', base=.68, jit=0), smooth=True)
    P.add(at(box((5.6, 4.6, .5), .2), (5.6, 5.0, -.4)), S('choc', base=.45, jit=0))
    sign_plate(P, 'QuestStand', 5.6, 5.0, -.75, 4.4, 3.4)
    # basket of rolled-wafer scrolls
    P.add(at(lathe([(0, 0), (1.3, 0), (1.6, 1.4), (1.5, 1.5), (1.1, .25), (0, .25)], sides=16), (-5.4, 4.6, -1.6)), S('ginger', base=.5, jit=0), smooth=True)
    for k in range(4):
        a = k * 1.6
        P.add(at(cyl(.32, 2.2, sides=8), (-5.4 + math.cos(a) * .5, 4.8, -1.6 + math.sin(a) * .5), (math.cos(a) * 18, 0, math.sin(a) * 18)), S('vanilla', base=.82, jit=0), smooth=True)
    return P

def gumball_machine():
    """TELEPORT: giant gumball machine. Stepped glossy pedestal, cherry body with a gold coin plate and a big glowing
    chute door (walk in = teleport), sugar-glass globe full of gumballs, cherry lid with a knob. Front = -Z. ~32 tall."""
    P = Prop('GumballMachine')
    P.add(lathe(round_prof(11.5, 1.4, .5, y0=-.6), sides=40), S('vanilla', base=.72, up=.2), smooth=True)
    rng = random.Random(4)
    for k in range(16):                                                     # gumball ring round the base
        a = k * math.tau / 16
        if abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .5: continue
        P.add(at(ball(1.0, 2), (math.cos(a) * 10.6, 1.5, math.sin(a) * 10.6)), S(CANDY[k % 7], base=.62, up=.25, jit=0), smooth=True)
    body = lathe([(0, .8), (8.2, .8), (8.4, 1.6), (7.0, 2.4), (6.4, 11.0), (7.6, 12.2), (7.6, 13.4), (0, 13.4)], sides=32)
    door = G.arch_prism(3.2, 4.0, -10, -4, y0=1.6)
    P.add(G.bool_diff(body, door), S('cherry', grad=(.8, 13.4, .45, .8)), smooth=True)
    P.add(at(G.arch_frame(3.2, 4.0, .9, -7.4, -6.2), (0, 1.6, 0)), S('lemon', base=.65, up=.2))
    P.add(at(G.arch_tunnel(3.2, 4.0, -6.6, -3.0), (0, 1.6, 0)), S('choc', base=.15, jit=0))
    P.gadd(at(G.arch_cap(3.1, 4.0, -3.3), (0, 1.6, 0)), 'portal')
    P.add(at(box((3.6, 2.6, .8), .3), (0, 9.6, -6.7)), S('lemon', base=.6, up=.2))       # coin plate + slot + knob
    P.add(at(box((.35, 1.4, .3)), (0, 9.8, -7.15)), S('choc', base=.12, jit=0))
    P.add(at(cyl(1.3, .8, sides=16), (3.4, 8.0, -6.6), (90, 0, 0)), S('vanilla', base=.82, jit=0), smooth=True)
    P.add(at(box((.5, 2.2, .5), .15), (3.4, 8.0, -7.3)), S('vanilla', base=.82, jit=0))
    P.add(at(torus(7.65, .4, n=40, sides=6), (0, 12.8, 0)), S('lemon', base=.62, jit=0), smooth=True)
    # globe + gumballs
    R, cy = 9.6, 22.4
    P.add(at(lathe([(0, -R)] + [(math.cos(a) * R, math.sin(a) * R) for a in [-math.pi / 2 + k / 16 * math.pi for k in range(1, 16)]] + [(0, R)], sides=32), (0, cy, 0)),
          S('jelly', base=.7, up=0, jit=0), smooth=True)
    for k in range(52):
        while True:
            p = Vector((rng.uniform(-1, 1), rng.uniform(-1, .55), rng.uniform(-1, 1)))
            if p.length < .9: break
        r = 1.45
        P.add(at(ball(r, 2), Vector((p.x * (R - r - .3), cy + p.y * (R - r - .3), p.z * (R - r - .3)))), S(CANDY[k % 7], base=.62, up=.25, jit=0), smooth=True)
    P.add(at(torus(5.2, .55, n=32, sides=8), (0, cy - R + 1.5, 0)), S('lemon', base=.6, jit=0), smooth=True)
    P.add(lathe([(0, cy + R - 2.4), (5.6, cy + R - 2.4), (6.0, cy + R - 1.4), (5.0, cy + R + .2), (2.2, cy + R + 1.2), (0, cy + R + 1.4)], sides=28), S('cherry', grad=(cy + R - 2.4, cy + R + 1.4, .5, .85)), smooth=True)
    P.add(at(lathe(round_prof(1.1, 1.6, .5), sides=14), (0, cy + R + 1.2, 0)), S('lemon', base=.62, jit=0), smooth=True)
    P.add(at(ball(1.25, 2), (0, cy + R + 3.6, 0)), S('cherry', grad=(cy + R + 2.4, cy + R + 4.9, .55, .88)), smooth=True)
    sign_plate(P, 'GumballMachine', 0, 4.4, -11.2, 6.0, 1.6) if False else None
    # sign plate on two short posts in front (blank)
    for sx in (-1, 1):
        bm = striped_tube([(sx * 3.6, -.4, -12.6), (sx * 3.6, 4.4, -12.6)], .28, sides=10, stripes=2)
        P.add(bm, MS(bm.faces.layers.int['c'], ('cherry', 'vanilla'), base=.62), smooth=True)
    sign_plate(P, 'GumballMachine', 0, 3.4, -12.6, 6.4, 1.8)
    return P

# ================================================================== HERO: CANDY CASTLE
def waffle_shade(lay, a=.72, b=.42):
    u = PAL.u('ginger')
    return lambda f: [(u, clamp((a if f[lay] == 0 else b) + .12 * f.normal.y, .04, .96))] * len(f.loops)

def cone_tower(P, x, z, r, h, scoop, seed, wall_top):
    """ice-cream-cone tower: waffle shaft, icing collar, big scoop with drips, upturned waffle cone spire + cherry"""
    sh = waffle_lathe([(0, -.5), (r + .4, -.5), (r + .4, 1.2), (r, 2.0), (r, h), (r + .9, h + .6), (r + .9, h + 1.4), (0, h + 1.4)], sides=16)
    P.add(at(sh, (x, 0, z)), waffle_shade(sh.faces.layers.int['c']), smooth=False)
    for y in (wall_top + .4,):
        P.add(at(piping(ring_pts(r + .15, 0, 20), .38, beads=False, closed=True), (x, y, z)), S('vanilla', base=.86, jit=0), smooth=True)
    for k in range(4):                                                      # hard-candy windows (glow)
        a = k * math.tau / 4 + .4 + seed
        p = Vector((x + math.cos(a) * (r + .05), h * .72, z + math.sin(a) * (r + .05)))
        P.gadd(at(lathe(round_prof(.9, 2.6, .85, bot=True), sides=10), p, (90, -math.degrees(a) - 90, 0)) if False else
               at(at(box((1.6, 2.8, .4), .3), (0, 0, 0)), p, (0, -math.degrees(a) + 90, 0)), 'window')
        P.add(at(at(piping([(-1.0, -1.6, 0), (1.0, -1.6, 0), (1.0, 1.0, 0), (0, 1.9, 0), (-1.0, 1.0, 0)], .22, beads=False, closed=True), (0, 0, 0)), p, (0, -math.degrees(a) + 90, 0)),
              S('vanilla', base=.86, jit=0), smooth=True)
    sr = r * 1.38; sy = h + 1.2 + sr * .55
    P.add(at(soft(sr, seed, sub=3, amp=.1, sq=(1, .8, 1)), (x, sy, z)), S(scoop, grad=(sy - sr * .8, sy + sr * .8, .45, .9), up=.1), smooth=True)
    P.add(at(torus(sr * .98, sr * .2, n=28, sides=7), (x, sy - sr * .45, z)), S(scoop, base=.5, up=.15, jit=0), smooth=True)
    drip_ring(P, sr * .98, sy - sr * .5, scoop, 5, seed, 1.0, 2.6, .5, base=.55)
    # spire: upturned waffle cone + cherry
    ch = r * 2.4; cb = sy + sr * .55
    sp = waffle_lathe([(r * .85, cb - .4), (r * .9, cb), (.05, cb + ch), (0, cb + ch)], sides=16)
    P.add(at(sp, (x, 0, z)), waffle_shade(sp.faces.layers.int['c'], .74, .46), smooth=False)
    P.add(at(torus(r * .88, .32, n=20, sides=5), (x, cb + .1, z)), S('choc', base=.45, jit=0), smooth=True)
    P.add(at(ball(.85, 2), (x, cb + ch + .5, z)), S('cherry', grad=(cb + ch - .3, cb + ch + 1.4, .55, .88)), smooth=True)

def candy_castle():
    """HERO: gingerbread-and-frosting castle. Square curtain wall (gumdrop merlons, piped icing) with four
    ice-cream-cone corner towers, a gatehouse with a cut arch facing -Z, and a tall central keep crowned by a
    soft-serve swirl roof. ~76 wide, ~78 tall. Front = -Z (gate)."""
    P = Prop('CandyCastle'); HW, HD = 30.0, 26.0; WH = 16.0
    # curtain walls: gingerbread slabs with an icing coping, piped top line and gumdrop merlons
    def wall(x0, z0, x1, z1, gap=None):
        L = math.hypot(x1 - x0, z1 - z0); yaw = math.degrees(math.atan2(-(z1 - z0), x1 - x0))
        segs = [(-L / 2, L / 2)] if gap is None else [(-L / 2, -gap), (gap, L / 2)]
        for a, b in segs:
            mx, mz = (x0 + x1) / 2, (z0 + z1) / 2; c = (a + b) / 2; w = b - a
            P.add(at(at(box((w, WH + .5, 3.6), .25), (c, (WH - .5) / 2, 0)), (mx, 0, mz), (0, yaw, 0)), S('ginger', grad=(0, WH, .45, .68), up=.1))
            P.add(at(at(box((w + .6, .8, 4.4), .3), (c, WH + .2, 0)), (mx, 0, mz), (0, yaw, 0)), S('vanilla', base=.84, up=.1, jit=0))
            for sz in (-1, 1):
                P.add(at(at(piping([(a + .4, WH - .5, sz * 2.2), (b - .4, WH - .5, sz * 2.2)], .34, beads=False), (0, 0, 0)), (mx, 0, mz), (0, yaw, 0)), S('vanilla', base=.86, jit=0), smooth=True)
            n = max(1, int(w / 4.2))
            for k in range(n):
                xx = a + (k + .5) * w / n
                g = at(lathe([(0, 0), (1.15, 0), (1.1, .9), (.55, 1.8), (0, 1.95)], sides=7), (xx, WH + .6, 0))
                P.add(at(g, (mx, 0, mz), (0, yaw, 0)), sugar(CANDY[(k + int(abs(x0 + z0))) % 7], WH + .6, WH + 2.6, seed=k), smooth=True)
            for xx in [a + (k + .5) * w / 2 for k in range(2)]:            # icing drips down the outer face
                for sz in (-1,):
                    P.add(at(at(drip(random.Random(int(xx * 10)).uniform(1.2, 3.0), .5), (xx, WH - .6, sz * 2.0)), (mx, 0, mz), (0, yaw, 0)), S('vanilla', base=.86, jit=0), smooth=True)
    wall(-HW, -HD, HW, -HD, gap=8.0); wall(HW, -HD, HW, HD); wall(HW, HD, -HW, HD); wall(-HW, HD, -HW, -HD)
    # gatehouse: two half-towers and an arch across the gap, candy-cane portcullis bars
    for sx in (-1, 1):
        x = sx * 10.0
        P.add(at(lathe(round_prof(4.6, WH + 6, .6, y0=-.5), sides=20), (x, 0, -HD - .4)), S('ginger', grad=(0, WH + 6, .45, .7)), smooth=True)
        P.add(at(lathe([(0, 0), (5.3, 0), (5.3, 1.0), (5.0, 1.4), (0, 1.4)], sides=20), (x, WH + 5.4, -HD - .4)), S('vanilla', base=.84, jit=0), smooth=True)
        drip_ring(P, 5.25, WH + 5.6, 'vanilla', 8, int(x), .8, 2.4, .42)
        P.add(at(soft(3.6, 7 + sx, sub=3, amp=.08, sq=(1, .78, 1)), (x, WH + 8.6, -HD - .4)), S('pinkf', grad=(WH + 6, WH + 11.5, .45, .88)), smooth=True)
        P.add(at(ball(.8, 2), (x, WH + 11.6, -HD - .4)), S('cherry', base=.65, jit=0), smooth=True)
    arch = G.bool_diff(at(box((16.0, 8.0, 5.0), .3), (0, WH - 2.0, -HD - .4)), at(G.arch_prism(6.0, 6.0, -HD - 6, -HD + 6, y0=-1.0), (0, 0, 0)))
    P.add(arch, S('ginger', grad=(WH - 6, WH + 2, .5, .68)))
    P.add(at(G.arch_frame(6.0, 6.0, 1.0, -HD - 3.2, -HD - 2.2), (0, 0, 0)), S('vanilla', base=.85, jit=0))
    P.add(at(box((17.0, .9, 5.8), .3), (0, WH + 2.4, -HD - .4)), S('vanilla', base=.84, jit=0))
    P.add(at(cyl(2.2, .8, sides=20), (0, WH - .4, -HD - 3.3), (90, 0, 0)), S('cherry', base=.6, jit=0), smooth=True)   # crest candy (no text)
    P.add(at(torus(2.2, .35, n=20, sides=6), (0, WH - .4, -HD - 3.7)), S('lemon', base=.6, jit=0) if False else S('lemon', base=.6, jit=0), smooth=True) if False else None
    for k in range(5):                                                      # raised portcullis bars (candy canes) under the arch
        x = -4.0 + k * 2.0
        bm = striped_tube([(x, 9.6, -HD + 1.0), (x, 12.4, -HD + 1.0)], .3, sides=8, stripes=1)
        P.add(bm, MS(bm.faces.layers.int['c'], ('cherry', 'vanilla'), base=.62), smooth=True)
    # keep: hall block + tall round keep with soft-serve roof
    P.add(at(box((26, 18, 18), .5), (0, 9.0, 6.0)), S('ginger', grad=(0, 18, .45, .68)))
    P.add(at(box((27, 1.0, 19), .4), (0, 18.4, 6.0)), S('vanilla', base=.84, jit=0))
    for sx in (-1, 1):
        for k in range(3):
            P.gadd(at(box((2.0, 3.6, .3), .2), (sx * (4 + k * 3.6), 12.0, -3.05)), 'window')
            P.add(at(piping([(-1.3, -2.1, 0), (1.3, -2.1, 0), (1.3, 1.4, 0), (0, 2.6, 0), (-1.3, 1.4, 0)], .24, beads=False, closed=True), (sx * (4 + k * 3.6), 12.0, -3.2)),
                  S('vanilla', base=.86, jit=0), smooth=True)
    P.add(at(G.arch_cap(3.0, 4.0, -3.15), (0, 0, 0)), S('choc', base=.35, jit=0))
    P.add(at(G.arch_frame(3.0, 4.0, .7, -3.6, -2.9), (0, 0, 0)), S('vanilla', base=.85, jit=0))
    keep = waffle_lathe([(0, 17.0), (9.0, 17.0), (9.0, 46.0), (10.2, 46.8), (10.2, 48.2), (0, 48.2)], sides=20)
    P.add(at(keep, (0, 0, 8.0)), waffle_shade(keep.faces.layers.int['c'], .7, .46), smooth=False)
    P.add(at(torus(9.1, .45, n=32, sides=6), (0, 30.0, 8.0)), S('vanilla', base=.86, jit=0), smooth=True)
    for k in range(6):
        a = k * math.tau / 6 + math.pi / 6
        P.gadd(at(box((2.0, 4.0, .4), .3), (math.cos(a) * 9.05, 38.0, 8.0 + math.sin(a) * 9.05), (0, -math.degrees(a) + 90, 0)), 'window')
    P.add(at(lathe([(10.4, 0), (10.6, .9), (10.0, 1.6), (0, 1.6)], sides=28), (0, 47.6, 8.0)), S('vanilla', base=.85, jit=0), smooth=True)
    drip_ring(P, 10.4, 47.8, 'vanilla', 10, 21, 1.2, 3.6, .55)
    P.add(at(swirl(10.6, 14.0, turns=3.2, r0=3.4, r1=.8, n=52, sides=10), (0, 48.4, 8.0)), S('pinkf', grad=(48.5, 64, .45, .9), up=.12), smooth=True)
    P.add(at(ball(1.6, 3), (0, 66.4, 8.0)), S('cherry', grad=(65, 68, .5, .86)), smooth=True)
    P.add(tube([Vector((0, 67.8, 8.0)), Vector((.6, 69.6, 8.4)), Vector((1.8, 70.8, 8.9))], [.2, .17, .13], sides=5), S('lime', base=.45, jit=0), smooth=True)
    # corner cone towers
    for (sx, sz), scoop, seed in (((-1, -1), 'pinkf', 1), ((1, -1), 'frost', 2), ((1, 1), 'vanilla', 3), ((-1, 1), 'choc', 4)):
        cone_tower(P, sx * HW, sz * HD, 5.6, 26.0, scoop, seed, WH)
    return P

def drawbridge(L=18.0, w=12.0):
    """gingerbread plank drawbridge (lowered) along Z with licorice chains; origin = castle end (z 0), runs to +Z"""
    P = Prop('Drawbridge')
    for k in range(int(L / 1.5)):
        z = .75 + k * 1.5
        P.add(at(box((w, .7, 1.35), .18), (0, .05, z)), S('ginger', base=.6, up=.2, jit=.04, seed=k))
    for sx in (-1, 1):
        P.add(at(box((.8, .9, L), .2), (sx * (w / 2 - .2), .35, L / 2)), S('choc', base=.45, jit=0))
        x = sx * (w / 2 + 1.4)
        bm = striped_tube([(x, -1.0, -.6), (x, 11.5, -.6)], .8, sides=12, stripes=2, step=1.4)
        P.add(bm, MS(bm.faces.layers.int['c'], ('cherry', 'vanilla'), base=.62), smooth=True)
        P.add(at(lathe(round_prof(1.25, .8, .3), sides=14), (x, 11.4, -.6)), S('vanilla', base=.85, jit=0), smooth=True)
        P.add(at(ball(1.1, 2), (x, 13.1, -.6)), S('lemon', grad=(12, 14.3, .55, .88)), smooth=True)
        P.add(tube([Vector((sx * (w / 2 - .4), .9, L - 1.0)), Vector((sx * (w / 2 + .3), 5.0, L * .5)), Vector((x, 10.2, -.2))], .26, sides=6),
              S('choc', base=.3, jit=0), smooth=True)
    return P

# ================================================================== HERO: CHOCOLATE FALLS
def bell_r(y, R, Hh):
    """gumdrop bell radius at height y (0..Hh)"""
    t = clamp(y / Hh)
    return max(0.0, R * (1.04 - .1 * t - .62 * t ** 2.6))

def icing_cap(P, R, Hh, y0, seed, sides=32, wave=.06, n_drips=12, drip_r=.06, thick=1.035):
    """icing poured over a bell top: follows the bell surface, scalloped lower edge (waves) with drips at the lobes"""
    ys = [y0 + (Hh - y0) * t for t in (0, .2, .45, .7, .88)]
    cap = lathe([(bell_r(y, R, Hh) * thick, y) for y in ys] + [(R * .2 * thick, Hh * 1.005), (0, Hh * 1.02)], sides=sides, close_top=False)
    lob = 5 + seed % 3
    for v in cap.verts:
        if abs(v.co.y - y0) < 1e-3:
            a = math.atan2(v.co.z, v.co.x)
            v.co.y -= Hh * wave * (.5 + .5 * math.cos(a * lob + seed))
            r = bell_r(v.co.y, R, Hh) * thick; k = r / max(1e-6, math.hypot(v.co.x, v.co.z)); v.co.x *= k; v.co.z *= k
    P.add(cap, S('vanilla', grad=(y0 - Hh * wave, Hh, .76, .97)), smooth=True)
    rng = random.Random(seed)
    for k in range(lob):                                                    # drips hang from the lobe tips
        a = (k * math.tau - seed) / lob
        for da in (0, .12, -.12)[:1 + (k % 2)]:
            y = y0 - Hh * wave + .1; rr = bell_r(y, R, Hh) * thick
            P.add(at(drip(rng.uniform(1.0, 2.6) * Hh / 20, R * drip_r), (math.cos(a + da) * rr, y, math.sin(a + da) * rr)), S('vanilla', base=.9, jit=0), smooth=True)

def choco_falls(part='falls'):
    """HERO: Fudge Falls. A grape gumdrop mountain (sugar sparkle, icing cap + drips) with a chocolate spring pouring
    from a cave mouth halfway up, down a channel on its face and over a lip into a frothy pool at y 0. Lime, berry and
    lemon gumdrop shoulders frame it. Falls face -Z.
    Three props on one origin: part 'mountain' = ChocoMountain (bell, icing, cave, shoulders, crystals: the lip),
    'falls' = ChocoFalls (the cascade ribbon only), 'pool' = ChocoPool (the frothy pool slab, reaching down into the
    basin) so the export's falls check finds rock at the lip and other water at the foot"""
    R, Hh = 30.0, 60.0
    yc = 30.0; rc = bell_r(yc, R, Hh)
    path = []                                                               # cascade: hugs the bell from the cave lip down,
    for k in range(13):                                                     # then a free fall over a ledge
        y = yc - 2.6 - k * (yc - 2.6 - 9.0) / 12
        path.append(Vector((0, y, -bell_r(y, R, Hh) - .9)))
    lip = path[-1]
    for k in range(1, 6):
        t = k / 5; path.append(Vector((0, lip.y * (1 - t) + .2 * t, lip.z - 3.0 * math.sin(t * math.pi / 2) - 1.5 * t)))
    end = path[-1]
    if part == 'pool':
        P = Prop('ChocoPool'); rng = random.Random(8)
        P.add(at(lathe([(0, -3.9), (12, -3.9), (12, -.4), (12.5, .1), (12.2, .5), (0, .5)], sides=28), (0, 0, end.z + 2.0)), S('choc', base=.58, up=.1, jit=0), smooth=True)
        for k in range(10):                                                 # whipped-cream froth
            a = k * math.tau / 10; r = rng.uniform(1.8, 3.2)
            P.add(at(soft(r, 30 + k, sub=2, amp=.25, sq=(1, .65, 1)), (end.x + math.cos(a) * 6.0, .6, end.z + math.sin(a) * 3.6)), S('vanilla', grad=(-1, 3, .74, .96)), smooth=True)
        for k in range(3):
            P.add(at(torus(7.0 + k * 2.4, .45 - k * .08, n=28, sides=6), (end.x, .45, end.z)), S('choc', base=.74 - k * .06, jit=0), smooth=True)
        return P
    if part == 'falls':
        P = Prop('ChocoFalls')
        bm = bmesh.new(); lay = bm.faces.layers.int.new('c'); rows = []; NJ = 14
        for i, p in enumerate(path):
            w = 12.0 + i * .5 + 1.6 * math.sin(i * 1.3); hug = min(1.0, i / 3)    # top rows hug the rock (the lip)
            row = []
            for j in range(NJ + 1):
                q = -1 + 2 * j / NJ
                ripple = .45 * math.sin(q * 9 + i * .7)                         # rope-like flow ridges
                curl = (-(1 - q * q) * 2.0 - ripple * (1 - abs(q)) - (.8 if abs(q) > .93 else 0)) * hug
                row.append(bm.verts.new(p + Vector((q * w / 2 + .5 * math.sin(i * .9 + q * 3), 0, curl))))
            rows.append(row)
        for i in range(len(rows) - 1):
            for j in range(NJ):
                f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j])); f[lay] = j % 2
        bm.normal_update()
        for f in bm.faces:
            if f.normal.z > 0: f.normal_flip()
        u = PAL.u('choc')
        P.add(bm, lambda f: [(u, clamp(.46 + .26 * max(0.0, math.sin(l.vert.co.x * 1.4 + l.vert.co.y * .05)) ** 3 + .1 * (l.vert.co.y / 30), .04, .96)) for l in f.loops], smooth=True)
        return P
    P = Prop('ChocoMountain')
    ys = [-4, 0, 6, 14, 22, 30, 38, 45, 51, 55, 58]
    prof = [(0, -4)] + [(bell_r(y, R, Hh), y) for y in ys] + [(R * .2, 59.6), (0, 60)]
    m = lathe(prof, sides=32)
    for v in m.verts:
        d = Vector((v.co.x, 0, v.co.z))
        if d.length > .1:
            k = 1 + .05 * mn.noise(v.co * .08 + Vector((3, 0, 0))); v.co.x *= k; v.co.z *= k
    P.add(m, sugar('grape', -4, 60, .32, .84, .12, 1.0, 1), smooth=True)
    icing_cap(P, R, Hh, 44.0, 7, wave=.045, drip_r=.045)
    rng = random.Random(8)
    for k in range(10): rng.uniform(1.8, 3.2)                               # (the pool's froth draws: crystals stay put)
    # cave mouth at y 30 on the front (-Z)
    P.add(at(G.arch_frame(7.0, 3.0, 1.8, -rc - 2.6, -rc + 1.5), (0, yc - 3.0, 0)), S('vanilla', base=.84, up=.15))
    P.add(at(G.arch_cap(7.0, 3.0, -rc + .8), (0, yc - 3.0, 0)), S('choc', base=.08, jit=0))
    # gumdrop shoulders + sugar crystals
    for (x, z, r, h, col, sd) in ((-30, 8, 15, 30, 'lime', 2), (31, 10, 17, 34, 'berry', 3), (-14, 22, 13, 24, 'lemon', 4)):
        pr = [(0, -3)] + [(bell_r(y, r, h), y) for y in [-3, 0, h * .25, h * .5, h * .7, h * .85, h * .95]] + [(0, h)]
        P.add(at(lathe(pr, sides=22), (x, 0, z)), sugar(col, -3, h, .34, .86, .12, 1.0, sd), smooth=True)
    for k in range(12):
        a = rng.uniform(0, math.tau); y = rng.uniform(4, 34)
        if abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .45: continue
        rr = bell_r(y, R, Hh)
        P.add(at(spike(rng.uniform(1.0, 1.7), rng.uniform(3.5, 6), sides=6, shoulder=.7), (math.cos(a) * rr, y, math.sin(a) * rr), (math.sin(a) * 30, 0, -math.cos(a) * 30)),
              S('cloud', grad=(y, y + 6, .7, .98)))
    return P

# ================================================================== BRIDGES + ARCHES
def waffle_bridge(L=46.0, w=12.0, rise=3.2):
    """waffle-cone bridge along Z: an arched waffle deck between two giant waffle cones lying along the rails (tips
    north, open mouths south holding ice-cream scoops), wafer-roll posts. Deck ends at y 0.3 (z = +-L/2)."""
    P = Prop('WaffleBridge')
    def yd(z): return .3 + rise * (1 - (2 * z / L) ** 2)
    nx, nz = 12, 46
    bm = bmesh.new(); top = {}; bot = {}
    for i in range(nz + 1):
        z = -L / 2 + i * L / nz
        for j in range(nx + 1):
            x = -w / 2 + j * w / nx
            dim = (i % 2 == 1 and j % 2 == 1 and 0 < j < nx)
            top[i, j] = bm.verts.new((x, yd(z) - (.35 if dim else 0), z))
            bot[i, j] = bm.verts.new((x, yd(z) - 1.6, z))
    for i in range(nz):
        for j in range(nx):
            bm.faces.new((top[i, j], top[i, j + 1], top[i + 1, j + 1], top[i + 1, j]))
            bm.faces.new((bot[i, j + 1], bot[i, j], bot[i + 1, j], bot[i + 1, j + 1]))
        for j in (0, nx): bm.faces.new((top[i, j], top[i + 1, j], bot[i + 1, j], bot[i, j]))
    for i in (0, nz):
        for j in range(nx): bm.faces.new((top[i, j], top[i, j + 1], bot[i, j + 1], bot[i, j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    u = PAL.u('ginger')
    def wsh(f):
        out = []
        for l in f.loops:
            low = yd(l.vert.co.z) - 1.0 < l.vert.co.y < yd(l.vert.co.z) - .2
            out.append((u, .44 if low else (.74 if f.normal.y > .5 else .55)))
        return out
    P.add(bm, wsh)
    for sx in (-1, 1):
        for sz in (-1, 1):                                                  # cone mouth at the bridge end, tip toward mid-span
            Lc = L / 2 - 3.0
            cone = waffle_lathe([(0, 0), (.3, .3), (3.0, Lc - 1.0), (3.4, Lc - .5), (3.4, Lc), (0, Lc)], sides=14)
            cone = at(cone, (0, 0, 0), (90 if sz < 0 else -90, 0, 0))     # tip at origin, mouth toward the end
            bmesh.ops.translate(cone, vec=Vector((sx * (w / 2 + 2.2), 0, -sz * 1.5)), verts=cone.verts)
            for v in cone.verts: v.co.y += yd(v.co.z) + 2.6
            P.add(cone, waffle_shade(cone.faces.layers.int['c'], .74, .46), smooth=False)
            zc = sz * (L / 2 - 3.6)
            P.add(at(soft(3.6, 40 + sx + sz * 3, sub=3, amp=.1, sq=(1, .9, 1)), (sx * (w / 2 + 2.2), yd(zc) + 3.2, zc)),
                  S(['pinkf', 'frost', 'vanilla', 'lemon'][(sx + 1) + (sz + 1) // 2], grad=(yd(zc), yd(zc) + 6.5, .45, .9)), smooth=True)
            P.add(at(ball(.85, 2), (sx * (w / 2 + 2.2), yd(zc) + 6.6, zc)), S('cherry', base=.65, jit=0), smooth=True)
        for k in range(7):                                                  # wafer-roll posts under the cones
            z = -L / 2 + 4 + k * (L - 8) / 6
            P.add(at(cyl(.55, 2.4, sides=10), (sx * (w / 2 + 1.2), yd(z) - .4, z)), S('vanilla', base=.82, jit=0), smooth=True)
            P.add(at(torus(.58, .12, n=10, sides=4), (sx * (w / 2 + 1.2), yd(z) + .9, z)), S('ginger', base=.5, jit=0))
    for sz in (-1, 1):                                                      # piers into the river bed
        z = sz * L * .22
        P.add(at(lathe(round_prof(2.4, 9.0, .5, y0=-9.0), sides=16), (0, yd(z) - 1.2, z)), S('ginger', grad=(-8, 1, .4, .66)), smooth=True)
    return P

def biscuit_bridge(L=42.0, w=11.0, rise=2.6):
    """biscuit bridge along Z: shortbread rounds overlapping on an arched chocolate spine, sandwich-cookie piers,
    pretzel-stick rails between jam-cookie posts. Ends at y 0.3."""
    P = Prop('BiscuitBridge')
    def yd(z): return .3 + rise * (1 - (2 * z / L) ** 2)
    nz = 24
    pts = [Vector((0, yd(-L / 2 + i * L / nz) - .9, -L / 2 + i * L / nz)) for i in range(nz + 1)]
    sp = tube(pts, 1.0, sides=6, flat=(w / 2 - .4, .9))
    P.add(sp, S('choc', base=.42, up=.15, jit=0), smooth=True)
    def crimp(r, h, sides=14):
        prof = [(0, 0), (r, 0), (r, h), (0, h)]
        bm = lathe(prof, sides=sides)
        for v in bm.verts:
            a = math.atan2(v.co.z, v.co.x); rr = math.hypot(v.co.x, v.co.z)
            if rr > .1: k = 1 + .05 * math.cos(a * 10); v.co.x *= k; v.co.z *= k
        return bm
    rng = random.Random(3)
    for i in range(int(L / 3.2)):
        z = -L / 2 + 1.6 + i * 3.2
        for j, x in enumerate((-3.3, 0, 3.3)):
            zz = z + (1.6 if j == 1 else 0) * 0
            if abs(zz) > L / 2 - 1.4: continue
            P.add(at(crimp(2.15, .6), (x + rng.uniform(-.15, .15), yd(zz) - .3 + (j == 1) * .08, zz), (rng.uniform(-2, 2), rng.uniform(0, 30), rng.uniform(-2, 2))),
                  S('ginger', base=.68 + rng.uniform(-.05, .05), up=.2, jit=.02, seed=i * 3 + j), smooth=True)
    for sx in (-1, 1):
        posts = [-L / 2 + 1.5 + k * (L - 3) / 6 for k in range(7)]
        for z in posts:
            p = Vector((sx * (w / 2 - .3), yd(z), z))
            P.add(at(lathe(round_prof(.7, 3.6, .3), sides=12), p), S('ginger', base=.62, jit=0), smooth=True)
            P.add(at(crimp(1.1, .45), p + Vector((0, 3.5, 0))), S('ginger', base=.72, jit=0), smooth=True)
            P.add(at(lathe(round_prof(.55, .35, .15), sides=12), p + Vector((0, 3.9, 0))), S('cherry', base=.6, jit=0), smooth=True)
        for a, b in zip(posts, posts[1:]):
            for hgt in (1.4, 2.8):
                P.add(tube([Vector((sx * (w / 2 - .3), yd(a) + hgt, a)), Vector((sx * (w / 2 - .3), yd(b) + hgt, b))], .22, sides=6), S('ginger', base=.5, jit=0), smooth=True)
    for sz in (-1, 1):                                                      # sandwich-cookie piers
        z = sz * L * .2
        for k in range(5):
            P.add(at(lathe(round_prof(2.6, 1.1, .4, bot=True), sides=16), (0, yd(z) - 2.2 - k * 1.7, z)), S('choc' if k % 2 == 0 else 'vanilla', base=.5 if k % 2 == 0 else .85, up=.15, jit=0), smooth=True)
    return P

def donut_arch(seed=0, glaze='pinkf'):
    """giant glazed donut standing on edge over the path, half sunk; glaze cap with drips and sprinkles; frosting
    mounds at its feet. Path runs along Z through the hole (hole ~13 wide at the ground). Origin at ground."""
    P = Prop('DonutArch%d' % seed)
    R, r, cy = 18.0, 6.6, 10.0
    def torus_v(R, r, n, sides): return closed_torus(R, r, n, sides, plane='XY')
    d = torus_v(R, r, 40, 14)
    keep = [f for f in d.faces if f.calc_center_median().y > -cy - 2.5]
    bmesh.ops.delete(d, geom=[f for f in d.faces if f not in keep], context='FACES')
    P.add(at(d, (0, cy, 0)), S('ginger', grad=(-8, 30, .5, .72), up=.15), smooth=True)
    gl = torus_v(R + .05, r + .45, 40, 14)                                  # glaze: the top-and-front half of the ring
    kill = []
    for f in gl.faces:
        c = f.calc_center_median(); ang = math.atan2(c.y, c.x)
        if c.y < R * .22 + 2.6 * math.sin(ang * 9 + seed): kill.append(f)
    bmesh.ops.delete(gl, geom=kill, context='FACES')
    P.add(at(gl, (0, cy, 0)), S(glaze, grad=(cy, cy + R + r, .5, .9), up=.12), smooth=True)
    rng = random.Random(seed)
    for k in range(9):                                                      # glaze drips on both faces of the ring
        ang = rng.uniform(.25, math.pi - .25); side = rng.choice((-1, 1))
        p = Vector((math.cos(ang) * R, cy + math.sin(ang) * R * .6 + 1.5, side * (r + .25)))
        if p.y < cy + 2: continue
        P.add(at(drip(rng.uniform(1.4, 3.0), .6), p), S(glaze, base=.72, jit=0), smooth=True)
    pn = []
    for k in range(56):                                                     # sprinkles on the glaze
        ang = rng.uniform(.3, math.pi - .3); t = rng.uniform(-1.2, 1.2)
        c = Vector((math.cos(ang) * R, cy + math.sin(ang) * R, 0))
        n = (Vector((math.cos(ang) * math.cos(t), math.sin(ang) * math.cos(t), math.sin(t)))).normalized()
        pn.append((c + n * (r + .5), n))
    sprinkles_on(P, pn, seed, L=1.2, r=.18)
    for sx in (-1, 1):                                                      # frosting mounds hiding the sunk feet
        P.add(at(soft(7.0, seed + sx, sub=3, amp=.14, sq=(1.25, .5, 1.2)), (sx * R, .2, 0)), S('vanilla', grad=(-2, 3.5, .7, .95)), smooth=True)
    return P

# ================================================================== FOLIAGE + SCATTER
def candy_cane(seed=0, h=18.0):
    """candy-cane 'tree': helical-striped cane with a hook, planted in a sugar mound; slight lean"""
    rng = random.Random(seed); P = Prop('CandyCane%d' % seed)
    c2 = [('cherry', 'vanilla'), ('lime', 'vanilla'), ('berry', 'vanilla'), ('blue', 'vanilla')][seed % 4]
    hook_r = h * .14; lean = rng.uniform(-5, 5); r = h * .045
    pts = [Vector((0, -1.0, 0)), Vector((0, h * .5, 0)), Vector((0, h - hook_r, 0))]
    pts += [Vector((hook_r - math.cos(a) * hook_r, h - hook_r + math.sin(a) * hook_r, 0)) for a in [math.pi * k / 8 for k in range(1, 9)]]
    pts.append(pts[-1] + Vector((0, -h * .07, 0)))
    dense = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        k = max(1, int((b - a).length / (r * 1.4)))
        dense += [a.lerp(b, t / k) for t in range(1, k + 1)]
    bm = striped_tube(dense, r, sides=12, stripes=2, twist=1.0)
    bmesh.ops.rotate(bm, cent=Vector(), matrix=__import__('mathutils').Euler((math.radians(lean), math.radians(rng.uniform(0, 360)), 0), 'YXZ').to_matrix(), verts=bm.verts)
    P.add(bm, MS(bm.faces.layers.int['c'], c2, base=.62, up=.18), smooth=True)
    P.add(at(soft(r * 3.4, seed, sub=2, amp=.2, sq=(1, .45, 1)), (0, -.3, 0)), S('vanilla', grad=(-1, 1.2, .7, .95)), smooth=True)
    return P

def lollipop_tree(seed=0, h=13.0):
    """swirl lollipop on a bent stick, disc tilted to face the path (-Z), plus a smaller ball pop on a side stick"""
    rng = random.Random(seed); P = Prop('LollipopTree%d' % seed)
    cols = [('cherry', 'vanilla'), ('blue', 'lemon'), ('berry', 'lime'), ('grape', 'orange')][seed % 4]
    R = h * .3; top = Vector((rng.uniform(-.6, .6), h, rng.uniform(-.4, .4)))
    P.add(tube([Vector((0, -.6, 0)), Vector((0, h * .5, 0)), top - Vector((0, R * .6, 0))], [.42, .38, .34], sides=8), S('vanilla', grad=(0, h, .7, .9)), smooth=True)
    bm, lay = swirl_disc(R, seed, turns=2.6, th=1.0, cols=cols)
    P.add(at(bm, top, (88, rng.uniform(-20, 20), rng.uniform(-6, 6))), MS(lay, cols, base=.64, up=.08), smooth=True)
    # ball pop on a side stick
    a = rng.uniform(0, math.tau); bp = Vector((math.cos(a) * 3.0, h * .55, math.sin(a) * 3.0))
    P.add(tube([Vector((0, h * .25, 0)), Vector((math.cos(a) * 1.6, h * .42, math.sin(a) * 1.6)), bp], [.26, .24, .22], sides=6), S('vanilla', base=.82, jit=0), smooth=True)
    bb = ball(1.7, 3); lay2 = bb.faces.layers.int.new('c')
    for f in bb.faces:
        c = f.calc_center_median(); f[lay2] = int((math.atan2(c.z, c.x) + c.y * .9) / (math.pi / 3)) % 2
    P.add(at(bb, bp + Vector((0, 1.6, 0))), MS(lay2, (cols[0], 'vanilla'), base=.66, up=.15), smooth=True)
    P.add(at(soft(1.6, seed, sub=2, amp=.2, sq=(1, .4, 1)), (0, -.2, 0)), S('vanilla', grad=(-.8, .8, .7, .95)), smooth=True)
    return P

def cotton_candy_tree(seed=0, h=16.0):
    """cotton-candy tree: twisting pretzel trunk with 3 limbs, each holding a fluffy mass; masses pulled into one
    crown and bridged; smooth subdivided lumps, soft pastel gradient (dark inside/under, pale on top)"""
    rng = random.Random(seed); P = Prop('CottonCandyTree%d' % seed)
    col = ['cotton', 'cloud', 'cotton', 'blue'][seed % 4]
    trunk = [Vector((0, -1.2, 0)), Vector((rng.uniform(-.5, .5), h * .3, rng.uniform(-.5, .5))), Vector((rng.uniform(-1, 1), h * .55, rng.uniform(-1, 1)))]
    bm = striped_tube(trunk, h * .045, sides=10, stripes=2, twist=.6)
    P.add(bm, MS(bm.faces.layers.int['c'], ('berry', 'vanilla') if col != 'blue' else ('blue', 'vanilla'), base=.66, up=.12), smooth=True)
    tips = []
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(-.4, .4); d = rng.uniform(h * .16, h * .24)
        tip = trunk[-1] + Vector((math.cos(a) * d, h * rng.uniform(.14, .26), math.sin(a) * d))
        mid = trunk[-1].lerp(tip, .5) + Vector((0, .6, 0))
        P.add(tube([trunk[-1], mid, tip], [h * .03, h * .024, h * .018], sides=7), S('vanilla', base=.82, jit=0), smooth=True)
        tips.append(tip)
    cy = sum((t.y for t in tips)) / 3 + h * .06
    masses = []
    for t in tips:
        c = Vector((t.x * 1.05, lerp(t.y, cy, .5) + h * .05, t.z * 1.05)); masses.append((c, h * rng.uniform(.17, .22)))
    masses.append((Vector((trunk[-1].x, cy + h * .12, trunk[-1].z)), h * .23))
    for k, (c, r) in enumerate(masses):
        P.add(at(soft(r, seed * 11 + k, sub=3, amp=.1, freq=1.4), c), S(col, grad=(c.y - r, c.y + r, .38, .92), up=.12), smooth=True)
    for k in range(6):                                                      # small puffs on the crown surface: fluffy edge
        c, r = masses[rng.randrange(len(masses))]
        d = Vector((rng.uniform(-1, 1), rng.uniform(-.2, 1), rng.uniform(-1, 1))).normalized()
        P.add(at(soft(r * .42, seed * 31 + k, sub=2, amp=.12), c + d * r * .92), S(col, grad=(c.y - r, c.y + r * 1.4, .45, .95), up=.12), smooth=True)
    return P

def gumdrop_bush(seed=0):
    """3-5 sugar-coated gumdrops of different colours clustered on the ground (true gumdrop profile, sugar sparkle)"""
    rng = random.Random(seed); P = Prop('GumdropBush%d' % seed)
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(1.6, 2.6); r = rng.uniform(1.1, 1.7) * (1.25 if k == 0 else 1)
        col = CANDY[(seed * 3 + k) % 7]
        prof = [(0, -.3), (r, -.3), (r * 1.0, r * .12), (r * .9, r * .62), (r * .78, r * .98), (r * .58, r * 1.14), (r * .28, r * 1.21), (0, r * 1.22)]
        P.add(at(lathe(prof, sides=14), (math.cos(a) * d, 0, math.sin(a) * d)), sugar(col, -.3, r * 1.5, .42, .88, .2, .35, seed * 5 + k), smooth=True)
    return P

def gumdrop_mountain(seed=0, col='grape'):
    """frame mountain: a huge sugar-coated gumdrop bell with an icing cap that follows the surface and drips, sugar
    crystals on the flanks. Built 20 tall (scale when placing)."""
    rng = random.Random(seed); P = Prop('GumdropMountain%d' % seed)
    R, Hh = 14.0, 20.0
    ys = [-3, 0, 3, 6, 9, 12, 14.5, 16.5, 18, 19.2]
    m = lathe([(0, -3)] + [(bell_r(y, R, Hh), y) for y in ys] + [(R * .18, 19.8), (0, 20)], sides=26)
    for v in m.verts:
        if math.hypot(v.co.x, v.co.z) > .1:
            k = 1 + .05 * mn.noise(v.co * .12 + Vector((seed, 0, 0))); v.co.x *= k; v.co.z *= k
    P.add(m, sugar(col, -3, Hh, .32, .82, .14, .9, seed), smooth=True)
    icing_cap(P, R, Hh, Hh * .72, seed, sides=26, wave=.07)
    for k in range(7):
        a = rng.uniform(0, math.tau); y = rng.uniform(1, 9); rr = bell_r(y, R, Hh)
        P.add(at(spike(rng.uniform(.5, .9), rng.uniform(1.6, 2.8), sides=6, shoulder=.7), (math.cos(a) * rr, y, math.sin(a) * rr), (math.sin(a) * 35, 0, -math.cos(a) * 35)),
              S('cloud', grad=(y, y + 2.5, .7, .98)))
    return P

def jelly_bean(L, r, seed):
    """a bean: tube along a gentle arc with rounded ends"""
    pts = []; radii = []
    for k in range(9):
        t = -1 + k / 4
        pts.append(Vector((t * L / 2, 0, -.18 * L * (1 - t * t))))
        radii.append(r * math.sqrt(max(0.0, 1 - (abs(t) ** 4) * .9)) + .02)
    return tube(pts, radii, sides=9)

def jelly_beans(seed=0):
    """'rock' scatter: a heap of 6-9 glossy jelly beans, some speckled"""
    rng = random.Random(seed); P = Prop('JellyBeans%d' % seed)
    for k in range(rng.randint(5, 7)):
        L = rng.uniform(2.4, 3.6); r = L * .3
        x, z = rng.uniform(-2.2, 2.2), rng.uniform(-2.2, 2.2); y = r * .75 + (1.0 if k > 5 else 0)
        col = CANDY[(seed + k) % 7]
        sh = S(col, base=.6, up=.25, jit=0) if k % 3 else S(col, base=.6, up=.25, vn=(.35, k, .25), grad=(y - r, y + r, .45, .8))
        P.add(at(jelly_bean(L, r, k), (x, y, z), (rng.uniform(-15, 15), rng.uniform(0, 360), rng.uniform(-25, 25))), sh, smooth=True)
    return P

def candy_flower(seed=0):
    """patch of fondant flowers: lime stems, 6 soft petals, gum centres"""
    rng = random.Random(seed); P = Prop('CandyFlower%d' % seed)
    for k in range(rng.randint(3, 5)):
        x, z = rng.uniform(-1.8, 1.8), rng.uniform(-1.8, 1.8); h = rng.uniform(.9, 1.6)
        col = ['berry', 'lemon', 'blue', 'cherry', 'grape', 'orange'][(seed + k) % 6]
        top = Vector((x + rng.uniform(-.3, .3), h, z + rng.uniform(-.3, .3)))
        P.add(tube([Vector((x, -.3, z)), Vector((x, h * .5, z)), top], .12, sides=5), S('lime', base=.5, jit=0), smooth=True)
        tilt = rng.uniform(-25, 25)
        for p in range(6):
            a = p * math.tau / 6
            pet = ball(1.0, 1)
            bmesh.ops.scale(pet, vec=Vector((.78, .2, .42)), verts=pet.verts)
            bmesh.ops.rotate(pet, cent=Vector(), matrix=__import__('mathutils').Matrix.Rotation(math.radians(18), 3, 'Z'), verts=pet.verts)
            bmesh.ops.translate(pet, vec=Vector((.72, .12, 0)), verts=pet.verts)
            P.add(at(pet, top, (tilt, math.degrees(a), 0)), S(col, base=.66, up=.2, jit=0), smooth=True)
        lf = ball(1.0, 1); bmesh.ops.scale(lf, vec=Vector((.6, .1, .26)), verts=lf.verts); bmesh.ops.translate(lf, vec=Vector((.5, 0, 0)), verts=lf.verts)
        P.add(at(lf, Vector((x, h * .3, z)), (0, rng.uniform(0, 360), 25)), S('lime', base=.6, jit=0), smooth=True)
        P.add(at(ball(.34, 2), top + Vector((0, .16, 0))), S('lemon' if col != 'lemon' else 'cherry', base=.6, jit=0), smooth=True)
    return P

def candy_lamp():
    """path lamp: striped stick post, piped collar, glowing wrapped-candy lantern with twisted wrapper ends"""
    P = Prop('CandyLamp')
    P.add(at(lathe(round_prof(1.2, .8, .3, y0=-.4), sides=12), (0, 0, 0)), S('vanilla', base=.75, jit=0), smooth=True)
    bm = striped_tube([(0, 0, 0), (0, 10.2, 0)], .32, sides=8, stripes=2, step=2.0)
    P.add(bm, MS(bm.faces.layers.int['c'], ('grape', 'vanilla'), base=.62), smooth=True)
    P.add(at(torus(.6, .22, n=12, sides=5), (0, 10.0, 0)), S('lemon', base=.62, jit=0), smooth=True)
    P.add(tube([Vector((0, 10.2, 0)), Vector((0, 11.4, 0)), Vector((0, 11.4, -1.4))], .2, sides=6), S('vanilla', base=.8, jit=0), smooth=True)
    lan = ball(1.0, 3); bmesh.ops.scale(lan, vec=Vector((1.25, .95, .95)), verts=lan.verts)
    P.gadd(at(lan, (0, 9.9, -1.4)), 'lamp')
    for sx in (-1, 1):
        fan = lathe([(0, 0), (.25, .05), (.95, .95), (.7, 1.05), (0, .4)], sides=12)
        for v in fan.verts:
            a = math.atan2(v.co.z, v.co.x); k = 1 + .15 * math.cos(a * 6) * clamp(v.co.y); v.co.x *= k; v.co.z *= k
        P.add(at(fan, (sx * 1.1, 9.9, -1.4), (0, 0, -sx * 90)), S('lemon', base=.7, up=.1, jit=0), smooth=True)
    P.add(tube([Vector((0, 11.4, -1.4)), Vector((0, 10.9, -1.4))], .08, sides=4), S('vanilla', base=.8, jit=0))
    return P

def marshmallow(seed=0):
    """stepping-stone marshmallow: rounded cylinder, pink or white, slightly toasted top"""
    P = Prop('Marshmallow%d' % seed); col = ['pinkf', 'vanilla'][seed % 2]
    P.add(lathe(round_prof(3.4, 8.0, 1.0, y0=-6.8, bot=True), sides=18), S(col, grad=(-6.8, 1.2, .55, .9), up=.15), smooth=True)
    return P

def spawn_cookie():
    """spawn medallion: giant sugar cookie with a crimped rim, a piped icing star and sprinkles, flush to the floor"""
    P = Prop('SpawnCookie')
    bm = lathe(round_prof(8.0, .9, .35, y0=-.6), sides=36)
    for v in bm.verts:
        rr = math.hypot(v.co.x, v.co.z)
        if rr > 7: a = math.atan2(v.co.z, v.co.x); k = 1 + .025 * math.cos(a * 18); v.co.x *= k; v.co.z *= k
    P.add(bm, S('ginger', grad=(-.6, .3, .55, .75), up=.1), smooth=True)
    star = [(math.cos(a) * (5.0 if i % 2 == 0 else 2.2), math.sin(a) * (5.0 if i % 2 == 0 else 2.2)) for i, a in enumerate([k * math.tau / 10 - math.pi / 2 for k in range(10)])]
    P.add(ngon_prism(star, .25, .5, .12), S('pinkf', base=.75, up=.1, jit=0))
    P.add(piping([(x, .55, z) for x, z in star], .22, closed=True), S('vanilla', base=.88, jit=0), smooth=True)
    rng = random.Random(2); pn = []
    for k in range(40):
        a = rng.uniform(0, math.tau); d = rng.uniform(5.4, 7.4)
        pn.append((Vector((math.cos(a) * d, .3, math.sin(a) * d)), Vector((0, 1, 0))))
    sprinkles_on(P, pn, 1)
    return P

def giant_cone(seed=0):
    """story prop: a toppled giant ice-cream cone, scoop slumped on the ground and melting into a puddle"""
    rng = random.Random(seed); P = Prop('GiantCone%d' % seed)
    sc = ['pinkf', 'frost', 'vanilla', 'choc'][seed % 4]
    cone = waffle_lathe([(0, 0), (.3, .4), (3.4, 10.0), (3.8, 10.4), (3.8, 11.2), (0, 11.2)], sides=14)
    cone = at(cone, (0, 0, 0), (-90, 0, 0))                                # lying along -Z, tip at origin
    bmesh.ops.translate(cone, vec=Vector((0, 3.2, 6.0)), verts=cone.verts)
    for v in cone.verts: v.co.y -= (v.co.z - 6.0) * -.05
    P.add(cone, waffle_shade(cone.faces.layers.int['c'], .74, .46), smooth=False)
    P.add(at(soft(4.0, seed, sub=3, amp=.12, sq=(1, .75, 1)), (0, 3.0, -6.2)), S(sc, grad=(0, 7, .45, .9)), smooth=True)
    pud = lathe([(0, .12), (5.6, .12), (6.0, 0), (6.2, -.3)], sides=24, close_top=False)
    for v in pud.verts:
        a = math.atan2(v.co.z, v.co.x); k = 1 + .18 * math.sin(a * 5 + seed); v.co.x *= k; v.co.z *= k
    P.add(at(pud, (0, -.1, -7.6)), S(sc, base=.6, up=.1, jit=0), smooth=True)
    for k in range(5):
        a = rng.uniform(0, math.tau)
        P.add(at(drip(rng.uniform(.6, 1.6), .55), (math.cos(a) * 3.6, 4.6, -6.2 + math.sin(a) * 3.0)), S(sc, base=.7, jit=0), smooth=True)
    return P

def macaron_stack(seed=0):
    """3-4 big macarons stacked a little askew (crate-like set dressing near the stations)"""
    rng = random.Random(seed); P = Prop('MacaronStack%d' % seed); y = 0.0
    for k in range(rng.randint(3, 4)):
        col = ['pinkf', 'lime', 'lemon', 'grape', 'blue', 'orange'][(seed + k) % 6]
        off = Vector((rng.uniform(-.35, .35), y, rng.uniform(-.35, .35)))
        for yy in (0, 1.25):
            shell = [(0, 0), (1.45, 0), (1.75, .2), (1.8, .45), (1.5, .8), (.8, .98), (0, 1.02)] if yy else [(0, -.1), (.8, -.06), (1.5, .1), (1.8, .45), (1.75, .75), (1.45, .95), (0, .95)]
            P.add(at(lathe(shell, sides=18), off + Vector((0, yy, 0))), S(col, base=.62, up=.2, jit=0), smooth=True)
        bm = lathe([(0, .9), (1.6, .9), (1.6, 1.3), (0, 1.3)], sides=16)
        for v in bm.verts:
            rr = math.hypot(v.co.x, v.co.z)
            if rr > 1.4: a = math.atan2(v.co.z, v.co.x); k2 = 1 + .06 * math.cos(a * 12); v.co.x *= k2; v.co.z *= k2
        P.add(at(bm, off), S('vanilla', base=.86, jit=0), smooth=True)
        y += 2.25
    return P

# ================================================================== preview materials (mirror the Roblox material map)
# Roblox: hard candy + chocolate = Glass (opaque, glossy), jelly = Glass + Transparency (set in SETUP), gingerbread =
# Sand (crumb grain), frosting / icing / cotton candy / clouds = SmoothPlastic, the frosting ground = Snow (soft sugar).
KIND = {c: 'gloss' for c in CANDY}
KIND['choc'] = 'choc'
KIND.update({'jelly': 'jelly', 'ginger': 'cookie'})
ROBLOX_MAT = {'gloss': 'Glass', 'choc': 'Glass', 'jelly': 'Glass', 'cookie': 'Sand', 'frost': 'SmoothPlastic'}
def roblox_materials():
    """palette column -> Enum.Material name, for roblox_materials.write_map"""
    return {c: ROBLOX_MAT[KIND.get(c, 'frost')] for c in PAL.names}

_PM = {}
def _pmat(kind):
    if kind in _PM: return _PM[kind]
    import bpy
    base = G.materials()['pal']; m = base.copy(); m.name = 'Prev_' + kind
    b = m.node_tree.nodes['Principled BSDF']
    rough, spec, coat = {'gloss': (.16, .7, .7), 'choc': (.28, .35, .35), 'satin': (.42, .3, .05), 'jelly': (.05, .9, 1.0), 'cookie': (.82, .25, 0), 'frost': (.5, .35, .15)}[kind]
    b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
    try: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .06
    except Exception: pass
    if kind == 'jelly':
        b.inputs['Alpha'].default_value = .88
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
    _PM[kind] = m
    return m

def preview_mats(me):
    """assign each face of a palette mesh the preview material of its column's kind (glow meshes untouched)"""
    if not me.materials or not me.uv_layers.active or me.materials[0] is None or not me.materials[0].name.startswith(('Grove', 'Prev_')): return
    uv = me.uv_layers.active.data; slots = {}
    me.materials.clear()
    from pro_lib import NCOL
    for poly in me.polygons:
        col = PAL.names[min(NCOL - 1, int(uv[poly.loop_indices[0]].uv.x * NCOL))]
        k = KIND.get(col, 'frost')
        if me.name.startswith(('Path_', 'Sprinkles')) and k == 'gloss': k = 'satin'
        if me.name.startswith('River_'): k = 'satin'
        if k not in slots: me.materials.append(_pmat(k)); slots[k] = len(me.materials) - 1
        poly.material_index = slots[k]
