# The Shattered Void - prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre,
# front = -Z. Theme: shards of a broken world orbiting a singularity: glassy black-violet obsidian, ancient lilac
# void-stone ruins with pale trim and abstract rune inlays (circles, diamonds, chevrons: never letters), violet and
# cyan crystal growths, magenta void flora. Glow (Neon) carries the drama; every solid wears the painted atlas.
# Machinery (Prop, materials, to_kit) from the skill's grove module, T / lathe / torus from the medieval example.
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix, noise as MN
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, hull, rock_pts, nz, clamp, ngon_prism, bevel, spike

PAL = Palette({
    'obsid':   ('#05040c', '#1c1636', '#5a4a96'),     # glassy island rock
    'crust':   ('#0f0b22', '#2a2250', '#6a58a8'),     # island ground
    'turf':    ('#06222e', '#12586a', '#46c0cc'),     # void moss patches
    'pave':    ('#26233e', '#58547e', '#a8a4d0'),     # rune paving / bridge decks
    'stone':   ('#2c2946', '#67628e', '#bdb8e0'),     # ancient lilac void-stone
    'trim':    ('#5c5a80', '#aeacd2', '#f4f2ff'),     # pale silver-bone trim
    'crystal': ('#1e0844', '#6a26c4', '#e2b6ff'),     # violet crystal bodies
    'cyanc':   ('#022838', '#0c86aa', '#a0f6ff'),     # cyan crystal bodies
    'flora':   ('#2a0632', '#8e1f86', '#ff92dc'),     # magenta void flora
    'stem':    ('#0a1228', '#22386a', '#6a90d0'),     # tendril stems
    'metal':   ('#08070f', '#24213c', '#625c8e'),     # dark iron
    'far':     ('#05040c', '#120e26', '#2e2752'),     # distant silhouettes
    'dark':    ('#000000', '#030208', '#0e0a1c'),     # the singularity
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
import void_paint
void_paint.install(G, PAL)
GLOW = {'void': '#ff2fd2', 'violet': '#9b4dff', 'cyan': '#2ff2ff', 'core': '#f4e8ff', 'lamp': '#86f6ff', 'rift': '#c33cff',
        'flame': '#ff4fe6'}
G.GLOW.clear(); G.GLOW.update(GLOW)
G.GLOW_E.clear(); G.GLOW_E.update({'void': 2.4, 'violet': 2.6, 'cyan': 2.6, 'core': 2.6, 'lamp': 3.4, 'rift': 2.6, 'flame': 3.4})
Prop, S = G.Prop, G.S
T, lathe, torus = B.T, B.lathe, B.torus
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

def V(col, y0, y1, a, b, nk=.12, ns=None, seed=0, amp=.08):
    """per-vertex height gradient (dark low -> light high) + normal lift + noise"""
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

# ------------------------------------------------------------------ primitives
def annulus(r0, r1, y0, y1, n=32, a0=0.0, a1=math.tau):
    """flat ring sector (r0..r1) from y0 to y1"""
    full = abs(a1 - a0 - math.tau) < 1e-6; m = n if full else n + 1
    bm = bmesh.new(); I0, I1, O0, O1 = [], [], [], []
    for i in range(m):
        a = a0 + (a1 - a0) * i / n; c, s = math.cos(a), math.sin(a)
        I0.append(bm.verts.new((c * r0, y0, s * r0))); I1.append(bm.verts.new((c * r0, y1, s * r0)))
        O0.append(bm.verts.new((c * r1, y0, s * r1))); O1.append(bm.verts.new((c * r1, y1, s * r1)))
    rng = range(n) if full else range(n)
    for i in rng:
        j = (i + 1) % m
        bm.faces.new((I1[i], O1[i], O1[j], I1[j])); bm.faces.new((I0[j], O0[j], O0[i], I0[i]))
        bm.faces.new((O0[i], O0[j], O1[j], O1[i])); bm.faces.new((I0[j], I0[i], I1[i], I1[j]))
    if not full:
        bm.faces.new((I0[0], I1[0], O1[0], O0[0])); bm.faces.new((O0[-1], O1[-1], I1[-1], I0[-1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def disc(r, y0, y1, n=24):
    poly = [(math.cos(a * math.tau / n) * r, math.sin(a * math.tau / n) * r) for a in range(n)]
    return ngon_prism(poly, y0, y1)

def shaft(r, h, seed, sides=6, shoulder=.74, tipoff=.18, base=-.8):
    """a crystal: irregular hex prism from `base` to h*shoulder, then an off-centre facetted point"""
    rng = random.Random(seed); bm = bmesh.new()
    R = [r * rng.uniform(.8, 1.15) for _ in range(sides)]; a0 = rng.uniform(0, 1)
    def ring(k, y):
        return [bm.verts.new((math.cos(a0 + i * math.tau / sides) * R[i] * k, y, math.sin(a0 + i * math.tau / sides) * R[i] * k)) for i in range(sides)]
    b = ring(1.0, base); m = ring(.92, h * shoulder)
    tip = bm.verts.new((rng.uniform(-1, 1) * r * tipoff, h, rng.uniform(-1, 1) * r * tipoff))
    for i in range(sides):
        j = (i + 1) % sides; bm.faces.new((b[i], b[j], m[j], m[i])); bm.faces.new((m[i], m[j], tip))
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def shard_rock(r, seed, n=22, flat=None, elong=(1, 1, 1)):
    """angular obsidian chunk: hull of few points = big glassy facets"""
    return hull(rock_pts((r * elong[0], r * elong[1], r * elong[2]), n=n, seed=seed, flat=flat))

def chamfer_box(size, bev=.25): return box(size, bev)

def flame(base, h, r, a, seed):
    return G.flame_tongue(Vector(base), h, r, a, seed)

# ------------------------------------------------------------------ crystals
def crystal_cluster(seed=1, s=1.0, kind='violet', name=None, big=4, glow=5, hang=False):
    """obsidian seat + big painted crystals leaning out + small painted + neon crystals + glow chips.
    hang=True: grows downward (origin at top)"""
    rng = random.Random(seed); P = Prop(name or 'Crystal%s%d' % (kind.capitalize(), seed))
    body = 'crystal' if kind == 'violet' else 'cyanc'; gk = 'violet' if kind == 'violet' else 'cyan'
    seat = shard_rock(3.6 * s, seed, 22, flat=.3, elong=(1.2, .6, 1.1))
    T(seat, (0, .5 * s, 0)); P.add(seat, FS('obsid', .34, .3, .06, seed))
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(0, 1); d = 3.0 * s
        c = shard_rock(rng.uniform(1.2, 1.8) * s, seed * 3 + k, 14, flat=.35); T(c, (math.cos(a) * d, .3 * s, math.sin(a) * d)); P.add(c, FS('obsid', .38, .3, .08, k))
    for k in range(rng.randint(4, 6)):                                    # rubble chips round the seat
        a = rng.uniform(0, math.tau); d = rng.uniform(3.8, 5.0) * s
        c = shard_rock(rng.uniform(.4, .8) * s, seed * 7 + k, 10, flat=.4); T(c, (math.cos(a) * d, .1, math.sin(a) * d))
        P.add(c, FS('obsid', .4, .3, .08, k))
    for k in range(big):
        a = k * math.tau / big + rng.uniform(-.4, .4); d = (0 if k == 0 else rng.uniform(1.2, 2.0)) * s
        h = (rng.uniform(11, 14) if k == 0 else rng.uniform(6.5, 9.5)) * s; r = (1.8 if k == 0 else rng.uniform(1.0, 1.35)) * s
        c = shaft(r, h, seed * 13 + k)
        T(c, (math.cos(a) * d, .7 * s, math.sin(a) * d), roll=rng.uniform(-6, 6), pitch=rng.uniform(4, 9) if k == 0 else rng.uniform(16, 30), yaw=90 - math.degrees(a))
        P.add(c, V(body, 0, h, .22, .88, nk=.08))
    for k in range(3):
        a = rng.uniform(0, math.tau); d = rng.uniform(2.4, 3.2) * s
        c = shaft(rng.uniform(.5, .7) * s, rng.uniform(2.4, 3.6) * s, seed * 17 + k)
        T(c, (math.cos(a) * d, .4 * s, math.sin(a) * d), pitch=rng.uniform(30, 50), yaw=90 - math.degrees(a)); P.add(c, V(body, 0, 3 * s, .3, .9))
    for k in range(glow):
        a = rng.uniform(0, math.tau); d = rng.uniform(1.6, 3.0) * s
        h = rng.uniform(2.6, 5.2) * s; r = rng.uniform(.38, .62) * s
        c = shaft(r, h, seed * 29 + k, sides=5)
        T(c, (math.cos(a) * d, .5 * s, math.sin(a) * d), roll=rng.uniform(-10, 10), pitch=rng.uniform(18, 42), yaw=90 - math.degrees(a))
        P.gadd(c, 'void' if (kind == 'violet' and k % 2) else gk)
    for k in range(6):                                                    # glow chips in the seat cracks
        a = rng.uniform(0, math.tau); d = rng.uniform(1.0, 2.8) * s
        c = shaft(.2 * s, rng.uniform(.7, 1.3) * s, seed * 41 + k, sides=4)
        T(c, (math.cos(a) * d, 1.0 * s, math.sin(a) * d), pitch=rng.uniform(30, 55), yaw=90 - math.degrees(a)); P.gadd(c, gk)
    if hang:
        flip = Matrix.Rotation(math.pi, 4, 'X')
        for mb in [P.solid] + list(P.glow.values()):
            mb.V = [tuple(flip @ Vector(v)) for v in mb.V]
            mb.V = [(x, y + .6 * s, z) for x, y, z in mb.V]
            mb.F = [tuple(reversed(f)) for f in mb.F]; mb.UV = [list(reversed(u)) for u in mb.UV]
    return P

def heart_crystal(seed=5):
    """the big crystal on the Starwatch shard: one huge cyan/violet column cluster on a stone collar"""
    P = crystal_cluster(seed, 2.1, 'cyan', 'HeartCrystal', big=4, glow=6)
    col = annulus(5.2, 7.4, -.4, .9, 24); P.add(col, FS('stone', .5, .3, .05))
    P.add(annulus(6.8, 7.7, .9, 1.3, 24), FS('trim', .6, .3, .04))
    for k in range(8):
        a = k * math.tau / 8
        P.gadd(T(box((.7, .12, .7)), (math.cos(a) * 6.3, .95, math.sin(a) * 6.3), yaw=-math.degrees(a) + 45), 'cyan')
    return P

# ------------------------------------------------------------------ floating debris (intentionally floating)
def float_shard(seed=1, s=1.0):
    """broken-off island chip: a crust slab with a chipped lip, a two-tier faceted obsidian keel ending in two
    stalactites, crystal sprouts and a glow seam. Origin = top centre (hangs in the void on purpose)."""
    rng = random.Random(seed); P = Prop('DebrisShard%d' % seed)   # 'debris': floats on purpose
    n = 10; pts = []
    for i in range(n):
        a = i * math.tau / n + rng.uniform(-.2, .2); r = rng.uniform(2.8, 4.2) * s * (1.25 if i in (2, 3) else 1)
        pts.append(Vector((math.cos(a) * r, rng.uniform(-.25, .1) * s, math.sin(a) * r * .85)))
    P.add(hull([p + Vector((0, .55 * s, 0)) for p in pts] + [p * .98 for p in pts]), FS('crust', .48, .25, .08, seed))
    P.add(hull([p * 1.02 + Vector((0, -.1, 0)) for p in pts] + [p * .82 + Vector((0, -rng.uniform(1.6, 2.4) * s, 0)) for p in pts]), V('obsid', -3 * s, 0, .2, .6, nk=.12))
    mid = [p * .6 + Vector((rng.uniform(-.4, .4), -2.2 * s, rng.uniform(-.4, .4))) for p in pts[::2]]
    low = [p * .3 + Vector((0, -4.6 * s, 0)) for p in pts[1::3]]
    P.add(hull(mid + low), V('obsid', -5 * s, -2 * s, .1, .45))
    for k, (o, L) in enumerate(((Vector((.8, 0, .4)), 4.2), (Vector((-1.2, 0, -.6)), 2.8))):
        st = shaft(.9 * s * (1 - k * .3), L * s, seed * 3 + k, sides=5, base=0); T(st, o * s + Vector((0, -4.0 * s, 0)), pitch=180 + rng.uniform(-10, 10))
        P.add(st, V('obsid', -9 * s, -4 * s, .1, .45))
    for k in range(3):
        p = pts[(k * 3 + 1) % n] * .5
        P.add(T(shard_rock(rng.uniform(.4, .7) * s, seed * 11 + k, 9, flat=.4), p + Vector((0, .5 * s, 0))), FS('obsid', .4, .3, .08, k))
    k = shaft(.5 * s, 2.8 * s, seed * 5, sides=5); T(k, pts[1] * .4 + Vector((0, .4 * s, 0)), pitch=18, yaw=rng.uniform(0, 360)); P.gadd(k, 'violet')
    k = shaft(.32 * s, 1.7 * s, seed * 9, sides=4); T(k, pts[6] * .45 + Vector((0, .4 * s, 0)), pitch=-24, yaw=rng.uniform(0, 360)); P.gadd(k, 'cyan')
    a = pts[0]
    P.gadd(tube([a * 1.03 + Vector((0, -.3, 0)), a * .93 + Vector((0, -1.2 * s, 0)), a * .8 + Vector((0, -2.0 * s, 0))], .14 * s, sides=4), 'void')
    return P

def far_rock(seed=1):
    """distant silhouette: a broken island chunk (wide flat top, keel tapering to one or two points), faint glints"""
    rng = random.Random(seed); P = Prop('FarDebris%d' % seed)    # far drifting debris (unreachable), floats on purpose
    n = 8; pts = [Vector((math.cos(a) * rng.uniform(8, 12), rng.uniform(-.5, .5), math.sin(a) * rng.uniform(7, 11))) for a in [i * math.tau / n + rng.uniform(-.2, .2) for i in range(n)]]
    tips = [Vector((rng.uniform(-3, 3), -rng.uniform(14, 20), rng.uniform(-3, 3)))]
    if seed % 2: tips.append(Vector((rng.uniform(3, 6), -rng.uniform(8, 11), rng.uniform(-2, 2))))
    P.add(hull(pts + [p * .7 + Vector((0, -4, 0)) for p in pts[::2]] + tips), FS('far', .4, .35, .12, seed))
    for k in range(3):
        a = rng.uniform(0, math.tau); P.gadd(T(shaft(.9, rng.uniform(3, 5), seed + k, sides=4), (math.cos(a) * 5, .3, math.sin(a) * 5), pitch=20, yaw=rng.uniform(0, 360)), 'violet' if k else 'cyan')
    return P

# ------------------------------------------------------------------ ruins
def rune_glyph(kind, w):
    """abstract rune inlay (never a letter): diamond / chevron / ring-dot, flat in XY facing -Z (thickness .12)"""
    out = []
    if kind == 0:
        out.append(T(box((w * .7, w * .7, .12)), (0, 0, 0), roll=45))
    elif kind == 1:
        out.append(T(box((w * .9, w * .18, .12)), (-w * .22, 0, 0), roll=40)); out.append(T(box((w * .9, w * .18, .12)), (w * .22, 0, 0), roll=-40))
    else:
        r = T(annulus(w * .3, w * .45, -.06, .06, 12), pitch=90); out.append(r); out.append(T(box((w * .2, w * .2, .12)), roll=45))
    return out

def pillar(seed=1, h=16.0, broken=True, name=None):
    """fluted void-stone column: stepped plinth, entasis shaft with 12 flutes, rune band, capital; broken = jagged top +
    fallen drum + rubble at the foot"""
    rng = random.Random(seed); P = Prop(name or ('PillarBroken%d' % seed if broken else 'Pillar%d' % seed))
    P.add(T(chamfer_box((6.4, 1.2, 6.4), .25), (0, -.4, 0)), FS('stone', .42, .3, .05, seed))
    P.add(T(chamfer_box((5.4, .9, 5.4), .22), (0, .65, 0)), FS('trim', .5, .3, .04))
    top = h * (rng.uniform(.55, .78) if broken else 1.0)
    n = 24; bm = bmesh.new(); rings = []
    ys = [1.1 + (top - 1.1) * i / 8 for i in range(9)]
    for yi, y in enumerate(ys):
        t = (y - 1.1) / max(1, h - 1.1); rr = 1.95 * (1 - .12 * t)
        ring = []
        for i in range(n):
            a = i * math.tau / n; fl = .86 if i % 2 else 1.0
            yy = y
            if broken and yi == len(ys) - 1: yy = y + (math.sin(i * .9 + seed) * .6 + rng.uniform(-.35, .25))
            ring.append(bm.verts.new((math.cos(a) * rr * fl, yy, math.sin(a) * rr * fl)))
        rings.append(ring)
    for A, Bq in zip(rings, rings[1:]):
        for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], Bq[(i + 1) % n], Bq[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); P.add(bm, V('stone', 0, h, .3, .68, nk=.1, ns=3, seed=seed))
    by = min(top - 1.0, h * .34)
    P.add(T(annulus(1.6, 2.15, by - .45, by + .45, 24), (0, 0, 0)), FS('trim', .55, .3, .04))
    P.gadd(annulus(2.1, 2.22, by - .16, by + .16, 24), 'violet')
    if not broken:
        P.add(T(chamfer_box((5.0, .8, 5.0), .2), (0, h + .4, 0)), FS('trim', .6, .3, .04))
        P.add(T(chamfer_box((4.2, .9, 4.2), .2), (0, h - .45, 0)), FS('stone', .55, .3, .04))
    else:
        d = cyl(1.75, 2.4, 24); T(d, (0, 1.75, 0), roll=90); T(d, (rng.choice((-1, 1)) * 4.6, -.3, rng.uniform(-2.5, 2.5)), yaw=rng.uniform(0, 180))
        P.add(d, FS('stone', .48, .25, .06, seed))
        for k in range(5):
            a = rng.uniform(0, math.tau); dd = rng.uniform(3.4, 5.0)
            P.add(T(chamfer_box((rng.uniform(.7, 1.4),) * 3, .2), (math.cos(a) * dd, .1, math.sin(a) * dd), yaw=rng.uniform(0, 90), pitch=rng.uniform(-20, 20)), FS('stone', .45, .3, .08, k))
    return P

def void_arch(seed=3, hw=7.0, h=13.0):
    """ruined gateway arch: two square piers with trim bands + rune inlays, a voussoir arch whose right shoulder broke
    away: three of its stones float above the gap (void magic), with glow undersides"""
    rng = random.Random(seed); P = Prop('VoidArch')
    for sx in (-1, 1):
        x = sx * (hw + 1.6)
        P.add(T(chamfer_box((4.4, 1.4, 4.4), .25), (x, 0, 0)), FS('stone', .4, .3, .05))
        P.add(T(chamfer_box((3.4, h, 3.4), .2), (x, .7 + h / 2, 0)), V('stone', 0, h, .3, .66, nk=.08, ns=3, seed=seed + sx))
        for y in (h * .38, h + .4):
            P.add(T(chamfer_box((3.9, .7, 3.9), .18), (x, y + .7, 0)), FS('trim', .58, .3, .04))
        for z in (-1.75, 1.75):
            for g in rune_glyph(rng.randint(0, 2), 1.2):
                P.gadd(T(g, (x, h * .62, z * (1 if z > 0 else 1))), 'cyan')
    R0, R1 = hw, hw + 3.2; yc = h + .7 + 1.2; n = 11
    for i in range(n):
        a0 = math.pi * i / n; a1 = math.pi * (i + 1) / n
        broken = i in (1, 2, 3)
        pts = []
        for a in (a0 + .015, a1 - .015):
            for r in (R0, R1):
                for z in (-1.5, 1.5): pts.append(Vector((math.cos(a) * r, yc + math.sin(a) * r, z)))
        st = hull(pts)
        if broken:
            c = sum(pts, Vector()) / len(pts); lift = Vector((rng.uniform(-.8, .8), 3.5 + i * 1.3, rng.uniform(-1, 1)))
            bmesh.ops.translate(st, vec=-c, verts=st.verts); T(st, c + lift, yaw=rng.uniform(-14, 14), roll=rng.uniform(-25, 25), pitch=rng.uniform(-10, 10))
            P.add(st, FS('stone', .55, .3, .06, i))
            P.gadd(T(disc(1.0, -.06, .06, 8), c + lift - Vector((0, 1.9, 0)), pitch=rng.uniform(-8, 8)), 'violet')
        else:
            P.add(st, FS('stone', .58 if i != 5 else .64, .25, .05, i))
            if i == 5:
                for g in rune_glyph(0, 1.3): P.gadd(T(g, (0, yc + R0 + 1.6, -1.56)), 'void')
    for k in range(4):                                                        # rubble of the fallen shoulder
        a = rng.uniform(-.6, .6); P.add(T(chamfer_box((rng.uniform(.8, 1.6),) * 3, .2), (hw * .6 + rng.uniform(-1, 3), .2, rng.uniform(-3, 3)), yaw=rng.uniform(0, 90), pitch=rng.uniform(-25, 25)), FS('stone', .46, .3, .08, k))
    return P

def rubble(seed=1):
    rng = random.Random(seed); P = Prop('Rubble%d' % seed)
    for k in range(rng.randint(5, 8)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 3.0); s = rng.uniform(.8, 1.8)
        P.add(T(chamfer_box((s * 1.3, s * .8, s), .22), (math.cos(a) * d, s * .3 - .2, math.sin(a) * d), yaw=rng.uniform(0, 90), pitch=rng.uniform(-18, 18), roll=rng.uniform(-18, 18)), FS('stone', .45, .3, .1, k))
    P.add(T(shard_rock(1.4, seed, 12, flat=.4), (rng.uniform(-1, 1), .2, rng.uniform(-1, 1))), FS('obsid', .35, .3, .08))
    P.gadd(T(shaft(.3, 1.6, seed, 5), (1.2, 0, -.8), pitch=24), 'violet')
    return P

# ------------------------------------------------------------------ floor runes, lamps, rails
def rune_circle(r=8.0, name='RuneCircle', seed=1):
    """flat ceremonial circle: pale trim ring set into dark stone, two broken glow rings, 8 glyph diamonds, centre sigil"""
    rng = random.Random(seed); P = Prop(name)
    P.add(annulus(r * .94, r, -.3, .12, 48), FS('trim', .55, .25, .03))
    P.add(annulus(r * .12, r * .94, -.3, .06, 48), FS('stone', .28, .25, .04))
    P.add(disc(r * .13, -.3, .1, 16), FS('trim', .6, .25, .03))
    for rr, w, gaps, key in ((.82, .035, 6, 'violet'), (.58, .03, 4, 'cyan'), (.32, .04, 3, 'void')):
        seg = math.tau / gaps
        for g in range(gaps):
            P.gadd(annulus(r * (rr - w), r * (rr + w), .06, .13, 10, g * seg + .08, (g + 1) * seg - .08), key)
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8; d = r * .7
        P.gadd(T(box((r * .07, .07, r * .07)), (math.cos(a) * d, .1, math.sin(a) * d), yaw=-math.degrees(a) + 45), 'violet')
        P.add(T(box((r * .22, .1, r * .03)), (math.cos(a) * r * .45, .07, math.sin(a) * r * .45), yaw=-math.degrees(a)), FS('trim', .5, .2, .03))
    return P

def crystal_lantern(seed=1, h=7.5):
    """stone lamp post: plinth, octagonal post with a trim collar, iron crown cage holding a cyan crystal (lamp glow)"""
    P = Prop('CrystalLantern')
    P.add(T(chamfer_box((1.8, .9, 1.8), .18), (0, -.3, 0)), FS('stone', .42, .3, .05))
    P.add(cyl(.5, h - 1.6, 8, .08, r2=.42, y0=.6), V('stone', 0, h, .32, .66))
    P.add(T(annulus(.44, .72, h * .45 - .2, h * .45 + .2, 8)), FS('trim', .55, .3, .04))
    P.add(T(chamfer_box((1.4, .35, 1.4), .1), (0, h - 1.2, 0)), FS('trim', .6, .3, .04))
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        P.add(tube([Vector((math.cos(a) * .55, h - 1.0, math.sin(a) * .55)), Vector((math.cos(a) * .75, h + .1, math.sin(a) * .75)), Vector((math.cos(a) * .35, h + 1.3, math.sin(a) * .35))], .09, sides=4), FS('metal', .5, .3))
    P.add(T(cyl(.5, .3, 8, r2=.2), (0, h + 1.25, 0)), FS('metal', .5, .3))
    P.gadd(T(shaft(.42, 1.9, seed, 6, base=0), (0, h - 1.0, 0)), 'lamp')
    return P

def rail_segment(L=8.0):
    """low balustrade: two square posts with diamond caps, a trim rail and a glow rune line under it"""
    P = Prop('VoidRail')
    for x in (-L / 2, L / 2):
        P.add(T(chamfer_box((1.0, 3.2, 1.0), .14), (x, 1.2, 0)), V('stone', 0, 3, .32, .62))
        P.add(T(box((.7, .7, .7), .1), (x, 3.0, 0), roll=45, yaw=45), FS('trim', .6, .3))
    P.add(T(chamfer_box((L, .4, .7), .12), (0, 2.6, 0)), FS('trim', .58, .3, .03))
    P.add(T(chamfer_box((L, .35, .5), .1), (0, .25, 0)), FS('stone', .42, .3, .03))
    P.gadd(T(box((L - 1.2, .1, .1)), (0, 1.6, -.2)), 'cyan')
    for k in range(3):
        x = -L / 2 + L * (k + 1) / 4
        P.add(T(chamfer_box((.35, 2.0, .35), .08), (x, 1.4, 0)), FS('stone', .5, .3))
    return P

def brazier(seed=1):
    """void brazier: three iron legs on a stone foot, a bevelled stone bowl, magenta void fire with a white core"""
    rng = random.Random(seed); P = Prop('VoidBrazier')
    P.add(T(chamfer_box((2.4, .6, 2.4), .15), (0, -.2, 0)), FS('stone', .42, .3))
    for k in range(3):
        a = k * math.tau / 3
        P.add(tube([Vector((math.cos(a) * 1.0, .3, math.sin(a) * 1.0)), Vector((math.cos(a) * .55, 2.0, math.sin(a) * .55)), Vector((math.cos(a) * .95, 3.3, math.sin(a) * .95))], .14, sides=5), FS('metal', .5, .3))
    bowl = lathe([(0, 3.1), (.7, 3.15), (1.35, 3.5), (1.6, 4.25), (1.45, 4.35), (.0, 3.9)], n=10)
    P.add(bowl, V('stone', 3, 4.4, .35, .7)); P.add(T(annulus(1.45, 1.7, 4.15, 4.45, 10)), FS('trim', .6, .3))
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = .45 if k else 0
        P.gadd(flame((math.cos(a) * d, 4.0, math.sin(a) * d), rng.uniform(1.6, 2.8) * (1.3 if not k else 1), .5, a, seed + k), 'flame')
    P.gadd(flame((0, 4.0, 0), 1.3, .3, 0, seed + 9), 'core')
    return P

# ------------------------------------------------------------------ void flora
def tendril(seed=1, s=1.0):
    """root bulb + 5 curling tendrils (tapering tubes) with glowing bud tips and pods along the stems"""
    rng = random.Random(seed); P = Prop('VoidTendril%d' % seed)
    P.add(T(lathe([(0, -.6), (1.3 * s, -.4), (1.6 * s, .5 * s), (1.0 * s, 1.3 * s), (.4 * s, 1.6 * s), (0, 1.7 * s)], 10)), V('stem', -.5, 1.7 * s, .2, .55))
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); L = rng.uniform(5, 9) * s; curl = rng.uniform(.8, 1.5)
        pts = []
        for i in range(9):
            t = i / 8; ang = a + curl * t * t * 2.2
            rad = (.4 + 2.0 * math.sin(t * 2.2)) * s
            pts.append(Vector((math.cos(ang) * rad, 1.2 * s + L * (t - .25 * t * t * t), math.sin(ang) * rad)))
        rr = [(.42 * (1 - t) + .06) * s for t in [i / 8 for i in range(9)]]
        P.add(tube(pts, rr, sides=6), V('stem', 0, L, .22, .62, nk=.06))
        tip = pts[-1]
        P.gadd(T(lathe([(0, -.35 * s), (.42 * s, 0), (.3 * s, .45 * s), (0, .75 * s)], 8), tip), 'void')
        for j in (3, 5):
            p = pts[j]; d = Vector((math.cos(a + 1.6), 0, math.sin(a + 1.6))) * .35 * s
            P.add(T(lathe([(0, -.2), (.3 * s, 0), (.22 * s, .3 * s), (0, .45 * s)], 6), p + d), FS('flora', .6, .3))
    for k in range(6):                                                    # small moss fronds hiding the bulb rim
        a = k * math.tau / 6 + rng.uniform(0, .5)
        b = Vector((math.cos(a) * 1.2 * s, .1, math.sin(a) * 1.2 * s)); e = Vector((math.cos(a) * 2.6 * s, .6 * s, math.sin(a) * 2.6 * s))
        P.add(tube([b, (b + e) / 2 + Vector((0, .5 * s, 0)), e], [.35 * s, .25 * s, .05], sides=4, flat=(1, .35)), FS('turf', .55, .3, .08, k))
    return P

def spore_pods(seed=1, s=1.0):
    """3-5 bulbous magenta pods on short stems, each split by glowing slits, fronds at the base"""
    rng = random.Random(seed); P = Prop('SporePods%d' % seed)
    n = rng.randint(3, 5)
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-.4, .4); d = (0 if k == 0 else rng.uniform(1.4, 2.4)) * s
        hh = (rng.uniform(3, 4.2) if k == 0 else rng.uniform(1.6, 2.8)) * s; r = (1.3 if k == 0 else rng.uniform(.7, 1.0)) * s
        base = Vector((math.cos(a) * d, 0, math.sin(a) * d))
        P.add(tube([base + Vector((0, -.4, 0)), base + Vector((0, hh * .4, 0)), base + Vector((0, hh * .55, 0))], [.32 * r, .25 * r, .3 * r], sides=6), V('stem', 0, hh, .2, .5))
        top = base + Vector((0, hh * .5, 0))
        pod = lathe([(0, 0), (r * .7, r * .25), (r, r * .9), (r * .85, r * 1.6), (r * .4, r * 2.1), (0, r * 2.25)], 12)
        P.add(T(pod, top), V('flora', top.y, top.y + 2.3 * r, .25, .8, nk=.1))
        for j in range(4):
            aa = j * math.tau / 4 + a
            P.gadd(T(box((.12 * r, 1.3 * r, .12 * r)), top + Vector((math.cos(aa) * r * .93, r * 1.15, math.sin(aa) * r * .93)), yaw=-math.degrees(aa)), 'void')
        P.gadd(T(lathe([(0, 0), (r * .25, .1), (0, .35 * r)], 6), top + Vector((0, 2.2 * r, 0))), 'core')
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(0, .4)
        b = Vector((math.cos(a) * .6 * s, .05, math.sin(a) * .6 * s)); e = Vector((math.cos(a) * 3.0 * s, .4 * s, math.sin(a) * 3.0 * s))
        P.add(tube([b, (b + e) / 2 + Vector((0, .7 * s, 0)), e], [.45 * s, .32 * s, .05], sides=4, flat=(1, .3)), FS('turf', .52, .3, .08, k))
    return P

def crystal_chips(seed=1):
    """ground cover: a low obsidian chip with 3-5 small crystals (painted + neon) poking out"""
    rng = random.Random(seed); P = Prop('CrystalChips%d' % seed)
    P.add(T(shard_rock(1.3, 400 + seed, 12, flat=.3, elong=(1.3, .5, 1.0)), (0, .1, 0)), FS('obsid', .36, .35, .08, seed))
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.0)
        c = shaft(rng.uniform(.18, .32), rng.uniform(.9, 2.0), seed * 7 + k, 5)
        T(c, (math.cos(a) * d, .2, math.sin(a) * d), pitch=rng.uniform(10, 40), yaw=90 - math.degrees(a))
        if k % 2: P.gadd(c, ('violet', 'cyan', 'void')[seed % 3])
        else: P.add(c, V('crystal' if seed % 2 else 'cyanc', 0, 2, .35, .9))
    return P

def void_grass(seed=1):
    """tuft of curling void-moss blades (teal) with glowing magenta tips"""
    rng = random.Random(seed); P = Prop('VoidGrass%d' % seed)
    for k in range(9):
        a = k * math.tau / 9 + rng.uniform(-.3, .3); L = rng.uniform(1.2, 2.4); c = rng.uniform(.4, .9)
        pts = [Vector((math.cos(a) * (.15 + c * t * t), L * t - .25, math.sin(a) * (.15 + c * t * t))) for t in (0, .35, .7, 1)]
        P.add(tube(pts, [.14, .11, .07, .02], sides=4, flat=(1, .45), rot0=a), V('turf', 0, 2.4, .3, .85))
        if k % 3 == 0: P.gadd(T(G.blob(.12, k, 8, 1.0), pts[-1]), 'void')
    return P

# ------------------------------------------------------------------ stations
def station_dais(P, r=9.0, steps=2, col='stone'):
    """shared station base: stepped octagonal void-stone dais with a pale trim lip and glow joint"""
    for i in range(steps):
        rr = r - i * 1.6
        P.add(T(ngon_prism([(math.cos(a * math.tau / 8 + math.pi / 8) * rr, math.sin(a * math.tau / 8 + math.pi / 8) * rr) for a in range(8)], -.6 if i == 0 else 0, .8 * (i + 1), .15)), FS(col, .44 + i * .05, .3, .04, i))
        P.add(annulus(rr - .2, rr + .08, .8 * (i + 1) - .1, .8 * (i + 1) + .06, 8, math.pi / 8, math.pi / 8 + math.tau), FS('trim', .6, .3, .03))
    P.gadd(annulus(r - 1.7, r - 1.55, .81, .86, 8, math.pi / 8, math.pi / 8 + math.tau), 'violet')
    return .8 * steps

def sign_plate(P, pos, w=8.0, h=2.2, yaw=0.0):
    """blank sign board for a GUI label (no text in the mesh): trim frame + dark face + glow corner gems"""
    P.add(T(chamfer_box((w, h, .4), .1), pos, yaw=yaw), FS('stone', .24, .1, .02))
    P.add(T(chamfer_box((w + .6, .35, .55), .1), Vector(pos) + Vector((0, h / 2 + .1, 0)), yaw=yaw), FS('trim', .6, .3))
    P.add(T(chamfer_box((w + .6, .35, .55), .1), Vector(pos) - Vector((0, h / 2 + .1, 0)), yaw=yaw), FS('trim', .55, .3))
    for sx in (-1, 1):
        P.gadd(T(box((.5, .5, .5)), Vector(pos) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Vector((sx * (w / 2 + .1), 0, -.2)), roll=45, yaw=yaw), 'cyan')

def shop_kiosk():
    """Void Merchant: dais, stone counter with trim, back shelf wall of wares, four crystal ribs curving over to a
    faceted crystal canopy, hanging crystal lanterns, crates + a floating orb, blank sign board on the canopy front"""
    P = Prop('VoidMerchant'); rng = random.Random(4)
    y0 = station_dais(P, 10.0, 2)
    P.add(T(chamfer_box((12, 3.0, 2.6), .25), (0, y0 + 1.5, -2.5)), V('stone', y0, y0 + 3, .3, .6))
    P.add(T(chamfer_box((12.8, .45, 3.2), .15), (0, y0 + 3.2, -2.5)), FS('trim', .62, .3))
    for x in (-4, 0, 4):
        for g in rune_glyph(x // 4 + 1, 1.0): P.gadd(T(g, (x, y0 + 1.6, -3.86)), 'cyan')
    P.add(T(chamfer_box((13, 8.5, 1.4), .25), (0, y0 + 4.25, 4.2)), V('stone', y0, y0 + 8.5, .28, .55))
    for y in (y0 + 3.2, y0 + 5.6):
        P.add(T(chamfer_box((11.5, .3, 1.6), .08), (0, y, 3.2)), FS('trim', .55, .3))
        for k in range(5):
            x = -4.6 + k * 2.3
            if k % 2: P.gadd(T(shaft(.32, 1.4, k + int(y), 5, base=0), (x, y + .15, 3.2)), 'violet' if y < y0 + 4 else 'cyan')
            else: P.gadd(T(lathe([(0, 0), (.5, .3), (.45, .8), (0, 1.0)], 8), (x, y + .15, 3.2)), 'void')
    for i, x in enumerate((-6.2, 6.2)):
        for z in (4.6, -4.0):
            pts = [Vector((x, y0 if z > 0 else y0 + 3.4, z)), Vector((x * 1.02, y0 + 9.5, z * .9)), Vector((x * .85, y0 + 12.0, z * .2 - .8))]
            P.add(tube(pts, [.5, .4, .3], sides=6), V('cyanc', y0, y0 + 12, .3, .8))
    can = hull([Vector((math.cos(a) * 8.0, y0 + 11.6 + (.6 if k % 2 else 0), math.sin(a) * 6.4 - .4)) for k, a in enumerate([i * math.tau / 10 for i in range(10)])] + [Vector((0, y0 + 14.2, -.4))] +
               [Vector((math.cos(a) * 7.4, y0 + 11.1, math.sin(a) * 5.8 - .4)) for a in [i * math.tau / 10 for i in range(10)]])
    P.add(can, V('crystal', y0 + 11, y0 + 14.2, .35, .85))
    for k in range(6):
        a = k * math.tau / 6 + .3; p = Vector((math.cos(a) * 5.4, y0 + 13.0, math.sin(a) * 4.2 - .4))
        P.gadd(T(shaft(.5, 2.4, k, 5), p, pitch=rng.uniform(-15, 15), roll=rng.uniform(-15, 15)), 'violet')
    for x in (-4.2, 0, 4.2):
        top = Vector((x, y0 + 11.0, -3.8))
        P.add(tube([top, top - Vector((0, 1.6, 0))], .06, sides=4), FS('metal', .5))
        P.add(T(cyl(.45, .25, 6, r2=.2), top - Vector((0, 1.7, 0))), FS('metal', .5))
        P.gadd(T(shaft(.32, 1.2, int(x) + 9, 6, base=0), top - Vector((0, 1.65, 0)), pitch=180), 'lamp')
    sign_plate(P, (0, y0 + 10.0, -5.6), 7.0, 1.8)
    P.add(T(chamfer_box((2.0, 2.0, 2.0), .2), (7.6, y0 + 1.0, -1.0), yaw=12), FS('stone', .45, .3))
    P.add(T(chamfer_box((1.6, 1.6, 1.6), .18), (7.4, y0 + 2.8, -1.0), yaw=-18), FS('stone', .5, .3))
    P.gadd(T(lathe([(0, 0), (.7, .35), (.6, 1.0), (0, 1.3)], 10), (-6.0, y0 + 4.4, -2.4)), 'cyan')
    P.add(T(chamfer_box((1.2, .9, 1.2), .12), (-6.0, y0 + 3.4, -2.4)), FS('trim', .55))
    return P

def upgrade_altar():
    """Ascension Altar: round 3-step dais, faceted obelisk with a glowing rune channel, two floating rings (one iron,
    one glow) tilted round it, four void braziers on the corners (as small bowls on posts), crystal shards at the foot"""
    P = Prop('AscensionAltar'); rng = random.Random(6)
    y0 = 0
    for i, (r, h) in enumerate(((9.5, .9), (8.0, .9), (6.4, .9))):
        P.add(T(cyl(r, h, 16, .2, y0=y0 - (.6 if i == 0 else 0))), FS('stone', .42 + i * .06, .3, .04, i))
        P.add(annulus(r - .15, r + .08, y0 + h - .08, y0 + h + .06, 16), FS('trim', .6))
        y0 += h
    P.gadd(annulus(5.0, 5.2, y0 + .01, y0 + .06, 32), 'violet')
    ob = bmesh.new(); rings = []
    for y, r in ((y0, 2.6), (y0 + 1.5, 2.2), (y0 + 13, 1.5), (y0 + 15.5, 0)):
        if r == 0: rings.append([ob.verts.new((0, y, 0))]); continue
        rings.append([ob.verts.new((math.cos(a * math.tau / 4 + math.pi / 4) * r, y, math.sin(a * math.tau / 4 + math.pi / 4) * r)) for a in range(4)])
    for A, Bq in zip(rings, rings[1:]):
        for i in range(4):
            if len(Bq) == 1: ob.faces.new((A[i], A[(i + 1) % 4], Bq[0]))
            else: ob.faces.new((A[i], A[(i + 1) % 4], Bq[(i + 1) % 4], Bq[i]))
    ob.faces.new(list(reversed(rings[0]))); bmesh.ops.recalc_face_normals(ob, faces=list(ob.faces))
    P.add(ob, V('stone', y0, y0 + 15, .3, .72, nk=.05))
    P.add(T(chamfer_box((3.4, 1.0, 3.4), .2), (0, y0 + 1.2, 0), yaw=45), FS('trim', .6))
    for a in range(4):
        ang = a * math.tau / 4 + math.pi / 4; nrm = Vector((math.cos(ang + math.pi / 4), 0, math.sin(ang + math.pi / 4)))
        for k in range(5):
            y = y0 + 3.0 + k * 2.0; r = lerp(2.2, 1.55, (y - y0 - 1.5) / 11.5) * .72
            P.gadd(T(box((.55, 1.2, .14)), nrm * (r + .02) + Vector((0, y, 0)), yaw=-math.degrees(ang + math.pi / 4) + 90), 'cyan')
    for k, (R, tilt, key) in enumerate(((5.0, 14, None), (4.0, -22, 'void'))):
        ring = torus(R, .35 if key is None else .22, n=32, sides=6)
        T(ring, (0, y0 + 9 + k * 2.2, 0), pitch=tilt, roll=tilt * .6)
        if key: P.gadd(ring, key)
        else:
            P.add(ring, FS('metal', .55, .3))
            for j in range(6):
                a = j * math.tau / 6; p = Vector((math.cos(a) * R, 0, math.sin(a) * R))
                g = T(shaft(.3, .9, j, 4, base=-.45), p); T(g, (0, y0 + 9, 0), pitch=tilt, roll=tilt * .6); P.gadd(g, 'violet')
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4; p = Vector((math.cos(a) * 7.6, 0, math.sin(a) * 7.6))
        P.add(T(cyl(.55, 3.0, 8, .06, y0=.9), p), V('stone', 0, 4, .32, .62))
        P.add(T(lathe([(0, 3.8), (.6, 3.85), (1.0, 4.3), (.85, 4.45), (0, 4.2)], 8), p), V('stone', 3.8, 4.5, .4, .7))
        P.gadd(flame(p + Vector((0, 4.2, 0)), 1.6, .4, a, k), 'flame')
    for k in range(5):
        a = rng.uniform(0, math.tau)
        P.gadd(T(shaft(.3, rng.uniform(1, 2), k + 50, 5, base=-.3), (math.cos(a) * 3.4, y0, math.sin(a) * 3.4), pitch=rng.uniform(15, 35), yaw=rng.uniform(0, 360)), 'violet')
    return P

def quest_stand():
    """Seer's Lectern: dais, curved stone screen with a blank board between two crystal-capped posts, a lectern
    pedestal with an open stone codex (blank pages), a floating cyan orb, scroll pedestals"""
    P = Prop('SeersLectern')
    y0 = station_dais(P, 8.5, 2)
    for k in range(9):                                                        # curved screen behind (backs onto +Z)
        a0 = math.radians(200 + k * 15.5); a1 = a0 + math.radians(15.5)
        pts = []
        for a in (a0 + .01, a1 - .01):
            for r in (6.0, 7.2):
                for y in (y0, y0 + 6.5 + 1.2 * math.cos((k - 4) / 4 * 1.2)): pts.append(Vector((math.cos(a) * r, y, -math.sin(a) * r)))
        P.add(hull(pts), V('stone', y0, y0 + 8, .3, .6, ns=4, seed=k))
    P.add(annulus(6.0, 7.5, y0 + 7.6, y0 + 8.1, 18, math.radians(20), math.radians(160)), FS('trim', .6))
    sign_plate(P, (0, y0 + 4.6, 5.5), 6.4, 3.4, 0)
    for sx in (-1, 1):
        x = sx * 5.2
        P.add(T(chamfer_box((1.6, 7.6, 1.6), .2), (x, y0 + 3.8, 3.2)), V('stone', y0, y0 + 8, .3, .62))
        P.add(T(chamfer_box((2.1, .5, 2.1), .12), (x, y0 + 7.8, 3.2)), FS('trim', .6))
        P.gadd(T(shaft(.6, 2.6, sx + 3, 6, base=0), (x, y0 + 8.0, 3.2)), 'cyan')
    ped = lathe([(1.3, y0), (1.1, y0 + .5), (.55, y0 + .9), (.5, y0 + 3.4), (.9, y0 + 3.8), (1.4, y0 + 4.0), (0, y0 + 4.0)], 10)
    P.add(ped, V('stone', y0, y0 + 4, .32, .66))
    book = T(chamfer_box((3.0, .4, 2.2), .1), (0, y0 + 4.4, 0), pitch=-16); P.add(book, FS('stone', .4))
    for sx in (-1, 1):
        P.add(T(chamfer_box((1.35, .14, 1.9), .04), (sx * .72, y0 + 4.68, -.05), pitch=-16, roll=sx * -6), FS('trim', .78, .1, .02))
    orb = G.blob(.9, 7, n=30, sq=1.0); T(orb, (0, y0 + 6.6, -.4)); P.gadd(orb, 'cyan')
    P.gadd(T(torus(1.5, .08, 24, 4), (0, y0 + 6.6, -.4), pitch=70), 'violet')
    for k, x in enumerate((-3.4, 3.4)):
        P.add(T(cyl(.6, 2.2, 8, .08, y0=y0), (x, 0, -1.5)), V('stone', y0, y0 + 2.2, .32, .6))
        for j in range(2):
            P.add(T(cyl(.24, 1.6, 8), (x - .8 + j * 1.6, y0 + 2.45, -1.5), roll=90, yaw=20 * (j - .5)), FS('trim', .7, .2))
    return P

def spawn_dais():
    """spawn platform: big round stepped dais, rune circle inlay, four obelisk markers with crystal heads"""
    P = Prop('SpawnDais')
    for i, (r, h) in enumerate(((12.5, .9), (10.8, .6))):
        P.add(T(cyl(r, h, 24, .15, y0=-.6 if i == 0 else .3)), FS('pave', .45 + i * .05, .3, .04, i))
        P.add(annulus(r - .2, r + .1, (.3 if i == 0 else .9) - .08, (.3 if i == 0 else .9) + .06, 24), FS('trim', .6))
    rc = rune_circle(9.6, 'tmp', 2)
    for mb, key in [(rc.solid, None)] + [(m, k) for k, m in rc.glow.items()]:
        sh = [(x, y + .9, z) for x, y, z in mb.V]; mb.V = sh
        if key is None: P.solid.merge(mb)
        else: P.glow.setdefault(key, type(mb)()).merge(mb)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4; p = Vector((math.cos(a) * 11.4, .3, math.sin(a) * 11.4))
        P.add(T(chamfer_box((1.6, .6, 1.6), .12), p + Vector((0, .3, 0))), FS('trim', .55))
        ob = hull([p + Vector((sx * .6, 0, sz * .6)) for sx in (-1, 1) for sz in (-1, 1)] + [p + Vector((sx * .4, 5.0, sz * .4)) for sx in (-1, 1) for sz in (-1, 1)] + [p + Vector((0, 6.0, 0))])
        P.add(ob, V('stone', 0, 6, .3, .7))
        P.gadd(T(shaft(.4, 1.4, k, 4, base=-.2), p + Vector((0, 6.3, 0))), 'cyan')
        P.gadd(T(box((.12, 2.6, .12)), p + Vector((0, 3.0, 0)) + Vector((-math.cos(a), 0, -math.sin(a))) * .52, yaw=-math.degrees(a)), 'violet')
    return P

def arena_rim(R=40.0, gaps=(0, 90, 180, 270)):
    """arena edge: a ring of low stone wall segments with trim caps and glow rune strips, a crystal post either side of
    each entrance gap (gaps = angles in degrees, 0 = +X east, 90 = +Z south)"""
    P = Prop('ArenaRim'); n = 48; gw = math.radians(9)
    def in_gap(a): return any(abs((a - math.radians(g) + math.pi) % math.tau - math.pi) < gw for g in gaps)
    for i in range(n):
        a0 = i * math.tau / n; a1 = a0 + math.tau / n; am = (a0 + a1) / 2
        if in_gap(am): continue
        P.add(annulus(R - 1.0, R + 1.0, -.6, 2.4, 2, a0 + .01, a1 - .01), V('stone', 0, 2.4, .3, .58, ns=4, seed=i))
        P.add(annulus(R - 1.25, R + 1.25, 2.4, 2.9, 2, a0 + .01, a1 - .01), FS('trim', .6, .3, .03, i))
        P.gadd(annulus(R - 1.06, R - .98, .8, 1.4, 2, a0 + .03, a1 - .03), 'violet')
    for g in gaps:
        for s in (-1, 1):
            a = math.radians(g) + s * (gw + .02); p = Vector((math.cos(a) * R, 0, math.sin(a) * R))
            P.add(T(chamfer_box((2.6, 7.0, 2.6), .2), p + Vector((0, 3.0, 0)), yaw=-math.degrees(a)), V('stone', 0, 7, .3, .65))
            P.add(T(chamfer_box((3.2, .6, 3.2), .15), p + Vector((0, 6.6, 0)), yaw=-math.degrees(a)), FS('trim', .6))
            P.gadd(T(shaft(.7, 2.8, g + s, 5, base=-.2), p + Vector((0, 6.9, 0))), 'void')
    return P

def rift_gate():
    """HERO 2 - the Rift Gate: octagonal stepped dais, a full ring of 18 void-stone voussoirs (r 13) with trim bands,
    two of them drifted out of the ring, crystal spikes bursting outward, a swirling violet rift membrane with glow
    rings and spiral arms, two guardian obelisks. Front (walk-in side) = -Z."""
    P = Prop('RiftGate'); rng = random.Random(9)
    y0 = station_dais(P, 15.0, 3)
    R0, R1, D = 12.0, 15.2, 2.6; yc = y0 + R1 + .2; n = 18
    for i in range(n):
        a0 = i * math.tau / n + .012; a1 = (i + 1) * math.tau / n - .012
        pts = []
        for a in (a0, a1):
            for r in (R0, R1):
                for z in (-D, D): pts.append(Vector((math.cos(a) * r, yc + math.sin(a) * r, z)))
        st = hull(pts); am = (a0 + a1) / 2
        if i in (2, 3):                                                       # drifted stones (float out, glow beneath)
            c = sum(pts, Vector()) / len(pts); out = Vector((math.cos(am), math.sin(am), 0)) * (3.5 + (i - 2) * 1.8)
            bmesh.ops.translate(st, vec=-c, verts=st.verts); T(st, c + out, roll=math.degrees(am) * .1 + rng.uniform(-18, 18), yaw=rng.uniform(-10, 10))
            P.add(st, FS('stone', .58, .3, .05, i)); P.gadd(T(G.blob(.5, i, 16, 1.0), c + out * .55), 'rift')
            continue
        if am > math.pi and am < math.tau and abs(math.cos(am)) < .25: pass
        P.add(st, V('stone', yc - R1, yc + R1, .3, .7, ns=5, seed=i))
        if i % 3 == 0:
            p = Vector((math.cos(am) * (R1 + .1), yc + math.sin(am) * (R1 + .1), 0))
            P.add(T(chamfer_box((1.4, 1.4, D * 2 + .5), .15), p, roll=math.degrees(am)), FS('trim', .62))
        for z in (-D - .05,):
            for g in rune_glyph(i % 3, 1.0):
                bmesh.ops.rotate(g, cent=Vector(), matrix=Matrix.Rotation(am - math.pi / 2, 3, 'Z'), verts=g.verts)
                P.gadd(T(g, (math.cos(am) * (R0 + R1) / 2, yc + math.sin(am) * (R0 + R1) / 2, z)), 'cyan')
    for k in range(7):                                                        # crystal spikes bursting from the ring
        am = rng.uniform(.2, math.pi - .2) if k < 5 else rng.uniform(math.pi + .5, math.tau - .5)
        p = Vector((math.cos(am) * R1, yc + math.sin(am) * R1, rng.uniform(-1.5, 1.5)))
        c = shaft(rng.uniform(.8, 1.4), rng.uniform(4, 8), k + 70)
        rot = Matrix.Rotation(am - math.pi / 2 + rng.uniform(-.4, .4), 3, 'Z') @ Matrix.Rotation(rng.uniform(-.3, .3), 3, 'X')
        bmesh.ops.rotate(c, cent=Vector(), matrix=rot, verts=c.verts); T(c, p)
        if k % 2: P.gadd(c, 'violet')
        else: P.add(c, V('crystal', yc - 20, yc + 20, .4, .85))
    mem = disc(R0 + .3, -.08, .08, 36); T(mem, (0, yc, 0), pitch=90); P.gadd(mem, 'rift')
    for k, (r, w, key) in enumerate(((10.6, .25, 'void'), (8.0, .22, 'cyan'), (5.2, .3, 'core'), (2.4, .4, 'void'))):
        ring = annulus(r - w, r + w, -.25 - k * .08, -.15 - k * .08, 36); T(ring, (0, yc, 0), pitch=90); P.gadd(ring, key)
    for arm in range(5):                                                      # spiral arms on the membrane front
        pts = []
        for i in range(14):
            t = i / 13; a = arm * math.tau / 5 + t * 3.4; r = 1.6 + t * 9.2
            pts.append(Vector((math.cos(a) * r, yc + math.sin(a) * r, -.5 - .25 * (1 - t))))
        P.gadd(tube(pts, [.18 + .2 * math.sin(t * math.pi) for t in [i / 13 for i in range(14)]], sides=4), 'core' if arm % 2 else 'violet')
    for sx in (-1, 1):                                                        # guardian obelisks
        x = sx * 19.5
        P.add(T(chamfer_box((3.2, 1.2, 3.2), .2), (x, y0 - .2, -3)), FS('trim', .55))
        ob = hull([Vector((x + a * 1.3, y0 + .3, -3 + b * 1.3)) for a in (-1, 1) for b in (-1, 1)] + [Vector((x + a * .8, y0 + 13, -3 + b * .8)) for a in (-1, 1) for b in (-1, 1)] + [Vector((x, y0 + 15.5, -3))])
        P.add(ob, V('stone', y0, y0 + 15, .3, .7))
        P.gadd(T(box((.2, 8, .2)), (x, y0 + 6.5, -4.36)), 'violet')
        P.gadd(T(shaft(.7, 2.4, sx + 90, 5, base=0), (x, y0 + 15.8, -3)), 'void')
    return P

def singularity():
    """HERO 1 - the Singularity: a black core (r 22) wrapped by a thin white photon ring, a tilted accretion disc of
    banded glow annuli (white-hot inside -> magenta -> violet -> cyan), the lensed far side of the disc arching over and
    under the core, orbiting rock debris and bending light streaks. Origin = core centre (it hangs in the void)."""
    P = Prop('OrbitSingularity'); rng = random.Random(13)   # hangs in the void with its orbiting disc + debris
    Rc = 22.0
    core = bmesh.new(); bmesh.ops.create_uvsphere(core, u_segments=40, v_segments=24, radius=Rc)
    P.add(core, FS('dark', .1, .05, .0), smooth=True)
    TILT = math.radians(-24)
    Mt = Matrix.Rotation(TILT, 3, 'X')                                       # near (south, +Z) edge tilts UP: opens to viewers below
    def disc_ring(r0, r1, key, gaps=0, seg=64, dy=0.0, gapw=.0):
        n = gaps or 1; sp = math.tau / n
        for g in range(n):
            a0, a1 = (g * sp + gapw, (g + 1) * sp - gapw) if gaps else (0, math.tau)
            bm = annulus(r0, r1, -.6 + dy, .6 + dy, seg // n if gaps else seg, a0, a1)
            bmesh.ops.rotate(bm, cent=Vector(), matrix=Mt, verts=bm.verts); P.gadd(bm, key)
    disc_ring(Rc + 2.0, Rc + 5.5, 'core')
    disc_ring(Rc + 6.5, Rc + 13.0, 'void', gaps=5, gapw=.05)
    disc_ring(Rc + 14.0, Rc + 21.0, 'violet', gaps=7, gapw=.06, dy=.2)
    disc_ring(Rc + 22.5, Rc + 25.0, 'cyan', gaps=9, gapw=.12, dy=-.2)
    disc_ring(Rc + 27.0, Rc + 28.0, 'violet', gaps=12, gapw=.18)
    # photon ring + lensed far disc arcs: rings standing in the XY plane (seen face-on from the south / spawn)
    pr = annulus(Rc + .4, Rc + 1.4, -.2, .2, 64); T(pr, pitch=90); P.gadd(pr, 'core')
    for (r0, r1, key) in ((Rc + 2.2, Rc + 4.8, 'core'), (Rc + 5.6, Rc + 9.5, 'void'), (Rc + 10.5, Rc + 13.0, 'violet')):
        for a0, a1 in ((math.radians(18), math.radians(162)), (math.radians(198), math.radians(342))):
            arc = annulus(r0, r1, -1.6, -1.2, 30, a0, a1)                          # behind the core (+y here = -Z after pitch)
            T(arc, pitch=90); P.gadd(arc, key)
    # orbiting debris (rock chunks with crystal sprouts) in the disc plane and a second inclined orbit
    for k in range(30):
        a = k * math.tau / 26 + rng.uniform(-.1, .1); r = rng.uniform(Rc + 30, Rc + 46)
        incl = Matrix.Rotation(TILT, 3, 'X') if k % 3 else Matrix.Rotation(math.radians(-38), 3, 'Z') @ Matrix.Rotation(math.radians(60), 3, 'X')
        p = incl @ Vector((math.cos(a) * r, rng.uniform(-3, 3), math.sin(a) * r))
        s = rng.uniform(2.4, 5.5)
        rk = shard_rock(s, 200 + k, 12, elong=(1.3, .8, 1.0)); T(rk, p, yaw=rng.uniform(0, 360), pitch=rng.uniform(0, 90))
        P.add(rk, FS('obsid', .35, .35, .1, k))
        if k % 3 == 0:
            P.gadd(T(shaft(s * .25, s * 1.1, k, 4, base=0), p + Vector((0, s * .6, 0)), pitch=rng.uniform(-30, 30)), 'violet' if k % 2 else 'cyan')
    # light streaks bending round the core: thin glow arcs on inclined circles
    for k in range(9):
        r = rng.uniform(Rc + 8, Rc + 40); a0 = rng.uniform(0, math.tau); L = rng.uniform(.5, 1.2)
        incl = Matrix.Rotation(rng.uniform(-.5, .5), 3, 'Z') @ Matrix.Rotation(TILT + rng.uniform(-.25, .25), 3, 'X')
        pts = [incl @ Vector((math.cos(a0 + L * t) * r, 0, math.sin(a0 + L * t) * r)) for t in [i / 10 for i in range(11)]]
        P.gadd(tube(pts, [.05 + .35 * math.sin(t * math.pi) for t in [i / 10 for i in range(11)]], sides=4, cap0=False, cap1=False), 'core' if k % 3 == 0 else ('cyan' if k % 3 == 1 else 'void'))
    return P

# ------------------------------------------------------------------ traversal
def rune_bridge(L=60.0, dy=0.0, w=9.0, seed=1, name=None, part='prop'):
    """rune bridge built along -Z from z=+L/2 (y -dy/2) to z=-L/2 (y +dy/2): bevelled paving slabs on an obsidian keel,
    trim curbs with a cyan rune strip, posts with crystal lamps every ~12 studs, a glow rune ring hanging under each
    keel block. Origin = span centre at deck level.
    part='deck' returns only the walkable deck (slabs + curbs: a static walkway joining the shards, the map script
    makes it ground); part='prop' returns the rest (keels, rings, posts, rune strips), which hangs from / stands on it"""
    rng = random.Random(seed); P = Prop(name or 'RuneBridge%d' % seed); DK = Prop((name or 'RuneBridge%d' % seed) + 'Deck')
    ns = max(4, int(L / 4.0)); sl = L / ns
    def at(t): return Vector((0, -dy / 2 + dy * t, L / 2 - L * t))
    pitch = math.degrees(math.atan2(dy, L))
    for i in range(ns):
        c = at((i + .5) / ns)
        DK.add(T(chamfer_box((w, .9, sl - .08), .14), c - Vector((0, .45, 0)), pitch=pitch), FS('pave', .5 + rng.uniform(-.06, .06), .3, .03, i))
    DK.add(T(chamfer_box((w - .3, .3, L - .2), .05), at(.5) - Vector((0, .7, 0)), pitch=pitch), FS('pave', .42, .3, .02))   # continuous bed under the slab seams
    for sx in (-1, 1):
        for i in range(ns):
            c = at((i + .5) / ns) + Vector((sx * (w / 2 + .5), 0, 0))
            DK.add(T(chamfer_box((1.0, 1.4, sl - .05), .15), c + Vector((0, .1, 0)), pitch=pitch), FS('trim', .56, .3, .03, i))
        a, b = at(0.01) + Vector((sx * (w / 2 + .5), .93, 0)), at(.99) + Vector((sx * (w / 2 + .5), .93, 0))   # rune strip ON the curb top
        P.gadd(tube([a, b], .12, sides=4), 'cyan')
    nk = max(2, int(L / 14))
    for k in range(nk):
        t = (k + .5) / nk; c = at(t)
        keel = hull([c + Vector((sx * w * .45, -1.0, sz * L / nk * .42)) for sx in (-1, 1) for sz in (-1, 1)] + [c + Vector((rng.uniform(-1, 1), -rng.uniform(5, 8), rng.uniform(-1, 1)))] +
                    [c + Vector((sx * w * .2, -3.2, sz * L / nk * .3)) for sx in (-1, 1) for sz in (-1, 1)])
        P.add(keel, V('obsid', c.y - 8, c.y, .12, .5))
        ring = torus(2.6, .14, 20, 4); T(ring, c + Vector((0, -4.0, 0))); P.gadd(ring, 'violet')
    npst = max(2, int(L / 12) + 1)
    for k in range(npst):
        t = k / (npst - 1) * .96 + .02
        for sx in (-1, 1):
            if (k + (sx > 0)) % 2: continue
            c = at(t) + Vector((sx * (w / 2 + .5), .8, 0))
            P.add(T(chamfer_box((1.2, 3.6, 1.2), .15), c + Vector((0, 1.83, 0))), V('stone', c.y, c.y + 3.6, .32, .64))
            P.add(T(chamfer_box((1.6, .4, 1.6), .1), c + Vector((0, 3.78, 0))), FS('trim', .6))
            P.gadd(T(shaft(.38, 1.5, k * 2 + sx, 5, base=0), c + Vector((0, 3.98, 0))), 'lamp')
    return DK if part == 'deck' else P

def step_stone(seed=1, r=3.4, part='prop'):
    """floating stepping stone: flat paved top (walkable), faceted obsidian keel with a stalactite, a glow rune ring
    under the lip. Origin = top centre."""
    rng = random.Random(seed); P = Prop('StepStone%d' % seed); TP = Prop('StepStoneTop%d' % seed)
    n = 9; top = [Vector((math.cos(a) * r * rng.uniform(.9, 1.06), 0, math.sin(a) * r * rng.uniform(.9, 1.06))) for a in [i * math.tau / n for i in range(n)]]
    TP.add(hull([p + Vector((0, .0, 0)) for p in top] + [p * .97 + Vector((0, -.7, 0)) for p in top]), FS('pave', .52, .3, .04, seed))   # walkable top: static (part='top')
    keel = [p * .8 + Vector((0, -1.0, 0)) for p in top] + [p * .4 + Vector((0, -2.6, 0)) for p in top[::2]] + [Vector((rng.uniform(-.5, .5), -5.2, rng.uniform(-.5, .5)))]
    P.add(hull(keel), V('obsid', -5, 0, .1, .5))
    TP.add(annulus(r * .5, r * .64, -.05, .06, 12), FS('trim', .6, .2))
    P.gadd(annulus(r * .82, r * .9, -1.4, -1.25, 16), 'cyan')
    P.gadd(T(shaft(.25, 1.0, seed, 4), (top[2].x * .7, -1.0, top[2].z * .7), pitch=160), 'violet')
    return TP if part == 'top' else P

def lift_pad(name='LiftPad'):
    """gravity lift pad: round 2-tier dais with 8 crystal teeth, a glowing cyan core disc and rune ring"""
    P = Prop(name)
    P.add(T(cyl(6.2, 1.0, 16, .15, y0=-.7)), FS('stone', .44, .3)); P.add(annulus(6.0, 6.3, .2, .36, 16), FS('trim', .6))
    P.add(T(cyl(4.8, .5, 16, .1, y0=.3)), FS('pave', .5, .3)); P.add(annulus(4.6, 4.9, .7, .82, 16), FS('trim', .6))
    P.gadd(disc(3.2, .78, .86, 24), 'cyan'); P.add(annulus(3.2, 3.6, .7, .86, 24), FS('metal', .5))
    P.gadd(annulus(4.0, 4.2, .81, .86, 24), 'violet')
    for k in range(8):
        a = k * math.tau / 8; p = Vector((math.cos(a) * 5.5, .3, math.sin(a) * 5.5))
        c = shaft(.45, 1.8 if k % 2 else 2.6, k, 5, base=-.3)
        rot = Matrix.Rotation(-a, 3, 'Y') @ Matrix.Rotation(math.radians(-14), 3, 'Z')
        bmesh.ops.rotate(c, cent=Vector(), matrix=Matrix.Rotation(math.radians(14), 3, 'X'), verts=c.verts)
        T(c, p, yaw=-math.degrees(a) - 90)
        if k % 2: P.gadd(c, 'violet')
        else: P.add(c, V('cyanc', 0, 3, .4, .85))
    return P

def lift_beam(h=58.0):
    """gravity lift column (glow only, walk-through): 6 thin streak bars on r 3 + rings every 6 studs, fading thinner up"""
    P = Prop('LiftBeam')
    for k in range(6):
        a = k * math.tau / 6
        P.gadd(T(box((.18, h, .18)), (math.cos(a) * 3.0, h / 2, math.sin(a) * 3.0)), 'cyan')
    for i in range(int(h / 6)):
        y = 3 + i * 6; w = .22 * (1 - .5 * i / (h / 6))
        P.gadd(annulus(2.2, 2.2 + w * 2, y - w, y + w, 24), 'cyan' if i % 2 else 'core')
    return P
