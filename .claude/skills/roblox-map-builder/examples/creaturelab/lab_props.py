# Bloomcrest Care Centre prop kit (creature-collecting game: care centre + mart + storage + research lab).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: a bright, clean, friendly care centre. Bases: clean white walls, soft cream counters + floor tiles, brushed
# steel, light birch. Accents: mint/teal (care), coral (mart), sky blue (storage / trade), gold (premium tier).
# Own identity: the "Bloom Paw" emblem (a rounded paw pad with three leaf-shaped toes, a shape, never letters) and the
# Gem Pod capture capsule (faceted 8-sided pod: white lower shell, tier-coloured upper shell, steel ring latch with a
# glowing gem stud on the front and a hinge block at the back). Tiers: mint, sky, coral, gold.
# Machinery (Prop, S, blob, materials, to_kit) from the grove module, transforms (T, bar, lathe, torus, sag) from the
# medieval example; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, spike, tube, hull, rock_pts, nz, clamp, ngon_prism, bevel

PAL = Palette({
    'wall':   ('#a9b3ba', '#e8eef0', '#ffffff'),     # clean white walls, paint, plastic shells
    'cream':  ('#b09d80', '#efe5d0', '#fffaf0'),     # soft cream counters, floor tiles, roof underside
    'mint':   ('#2f8f78', '#7fdcbf', '#d6fff2'),     # care accent (heal), capsule tier 1
    'teal':   ('#0f5a61', '#1f9fa3', '#8ae6df'),     # deep teal trim, cushions, roof
    'coral':  ('#9c3c34', '#ff7d68', '#ffc8b8'),     # mart accent, capsule tier 3
    'gold':   ('#8a6a12', '#f2c23c', '#fff0a6'),     # premium accent, capsule tier 4
    'sky':    ('#2a4f9c', '#5fa3ff', '#c4e2ff'),     # storage / trade accent, capsule tier 2
    'steel':  ('#3c4652', '#8e99a5', '#e2e8ee'),     # brushed steel machines, frames, legs
    'dark':   ('#14181e', '#2b323b', '#59626d'),     # rubber, screen bezels, keys
    'wood':   ('#5e3f28', '#c69a6a', '#f2d6ae'),     # light birch furniture, baskets, trunks
    'leaf':   ('#1d6b3c', '#4cb85c', '#b6ee7c'),     # foliage
    'grass':  ('#3e8c3c', '#70c658', '#bdee8c'),     # lawns
    'paving': ('#8e8a84', '#dcd5c8', '#f7f3ea'),     # exterior paving
    'glass':  ('#2a7a88', '#a4e8f0', '#eafdff'),     # glass (Glass material in Roblox)
    'berry':  ('#6a1f4c', '#dc4a80', '#ffa6c8'),     # berries, pink potions, flowers
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
GLOWS = {'heal': '#54ffc6', 'screen': '#86d6ff', 'liquid': '#52ffa8', 'liquid2': '#ff9ab8', 'lamp': '#fff1cc',
         'gem': '#c8fff4', 'evo': '#8ef4ff'}
G.GLOW.clear(); G.GLOW.update(GLOWS)
G.GLOW_E.clear(); G.GLOW_E.update({'heal': 2.6, 'screen': 1.6, 'liquid': 2.2, 'liquid2': 2.2, 'lamp': 3.0, 'gem': 2.4, 'evo': 3.2})
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, lathe, torus, sag = B.T, B.bar, B.lathe, B.torus, B.sag
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
V3 = Vector
TIERS = ('mint', 'sky', 'coral', 'gold')
FL = 1.0                     # interior floor top (building floor slab), exterior ground y = 0

# ------------------------------------------------------------------ generic helpers
def ball(r, n=10, m=6):
    return lathe([(0, -r)] + [(r * math.sin(math.pi * k / m), -r * math.cos(math.pi * k / m)) for k in range(1, m)] + [(0, r)], n=n)

def rbox(size, r=.2, seg=2):
    """rounded box (bevel with `seg` segments); r clamped to the smallest half size"""
    bm = box(size); return bevel(bm, min(r, min(size) * .45), seg)

def loft(rings, closed=True):
    bm = bmesh.new(); R = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(R[0])
    for A, Bq in zip(R, R[1:]):
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    return bm

def ring_seg(r0, r1, y0, y1, a0, a1, n=12):
    """solid annular sector: radii r0..r1, heights y0..y1, angles a0..a1 (deg; x = cos, z = sin: 90 = +Z south)"""
    bm = bmesh.new(); rows = []
    for i in range(n + 1):
        a = math.radians(lerp(a0, a1, i / n)); c, s = math.cos(a), math.sin(a)
        rows.append([bm.verts.new((c * r, y, s * r)) for r, y in ((r0, y0), (r1, y0), (r1, y1), (r0, y1))])
    for A, Bq in zip(rows, rows[1:]):
        for k in range(4):
            j = (k + 1) % 4; bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
    full = abs(a1 - a0) >= 359.99
    if not full:
        bm.faces.new(rows[0]); bm.faces.new(rows[-1][::-1])
    else:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def merge_prop(P, sub, pos=(0, 0, 0), s=1.0, yaw=0.0):
    """copy a built Prop's geometry into P (moved / scaled / turned), keeping UVs + glow keys"""
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    def tr(mb, dst):
        base = len(dst.V)
        dst.V.extend(tuple(R @ (V3(v) * s) + V3(pos)) for v in mb.V)
        dst.F.extend(tuple(i + base for i in f) for f in mb.F); dst.UV.extend(mb.UV); dst.SM.extend(mb.SM)
    tr(sub.solid, P.solid)
    for k, mb in sub.glow.items(): tr(mb, P.glow.setdefault(k, G.MB()))

def upright(poly, d, pos, yaw=0.0, s=1.0):
    """2D poly [(x, up)] standing upright facing -Z, extruded d toward the front (-Z) from z = 0"""
    bm = ngon_prism([(x * s, z * s) for x, z in poly], 0, d)
    return T(T(bm, (0, 0, 0), 0, -90), pos, yaw)

def leaf_poly(L, w, n=7, a=0.0, c=(0, 0)):
    """lens-shaped leaf: length L along direction a (deg from +up, clockwise = +x), half width w"""
    pts = []
    for k in range(n + 1):
        t = k / n; pts.append((w * math.sin(math.pi * t) ** .8, L * t))
    for k in range(n - 1, 0, -1):
        t = k / n; pts.append((-w * math.sin(math.pi * t) ** .8, L * t))
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [(c[0] + x * ca + y * sa, c[1] - x * sa + y * ca) for x, y in pts]

def emblem(P, pos, yaw=0.0, s=1.0, d=.2, pad='coral', toe='mint', base=.62):
    """the Bloom Paw: rounded paw pad (soft heart-ish blob) + three leaf toes fanned above it. Fits ~2.2 x 2.2 at s=1,
    centred on pos, facing -Z (extruded d toward -Z)"""
    pp = []
    for k in range(20):
        t = k * math.tau / 20
        x = math.cos(t) * .62; y = math.sin(t) * .46
        if y < 0: x *= 1 - .18 * (-y / .46)                    # narrower at the bottom
        y += .12 * math.cos(t * 2) * (y > 0)                     # two soft lobes on top
        pp.append((x, y - .38))
    P.add(upright(pp, d, pos, yaw, s), S(pad, base=base, up=.1, jit=.01))
    for a, L, cx, cy in ((-38, .78, -.5, .22), (0, .9, 0, .38), (38, .78, .5, .22)):
        P.add(upright(leaf_poly(L, .2, 6, a, (cx, cy)), d * .9, pos, yaw, s), S(toe, base=base, up=.1, jit=.01))

def emblem_badge(P, pos, yaw=0.0, r=1.4, ring='teal', face='wall'):
    """round badge facing -Z: white disc (back face at pos), coloured rim ring, the Bloom Paw raised on its face"""
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y'); at = lambda o: tuple(V3(pos) + R @ V3(o))
    P.add(T(T(lathe([(r * 1.08, 0), (r * 1.08, .2), (r * .98, .28), (0, .28)], 24), (0, 0, 0), 0, -90), pos, yaw), S(face, base=.84, up=.05, jit=.0))
    P.add(T(T(torus(r * 1.06, r * .09, 24, 6), (0, 0, 0), 0, 90), at((0, 0, -.2)), yaw), S(ring, base=.55, up=.1, jit=.01))
    emblem(P, at((0, 0, -.27)), yaw, r * .62, .14)
    P.add(T(T(cyl(r * 1.07, .12, 24), (0, 0, 0), 0, -90), at((0, 0, .1)), yaw), S(face, base=.8, jit=0))

# ------------------------------------------------------------------ the Gem Pod capsule
def capsule(P, c, tier='mint', s=1.0, yaw=0.0, pitch=0.0, n=8, gem=True, open_deg=0.0):
    """the capture ball wherever the kit places one (was the Gem Pod): LOD by size / caller detail (n <= 6 = shelf)"""
    lod = 0 if s >= 1.5 else (2 if (n <= 6 or s < .75) else 1)
    catch_ball(P, c, tier, s, yaw, pitch, lod, open_deg)

def capsule_prop(tier='mint'):
    P = Prop('GemPod_%s' % tier)
    P.add(lathe([(.62, 0), (.62, .12), (.5, .2), (0, .2)], 16), S('steel', base=.5, up=.1, jit=.01))
    capsule(P, (0, .2, 0), tier, 1.6)
    return P

def cradle(P, c, tier, tilt=0.0, yaw=0.0):
    """capsule cradle slot: steel cup, glowing ring, capsule seated (used in the heal machine)"""
    R = lambda bm: T(T(bm, (0, 0, 0), 0, tilt), c, yaw)
    P.add(R(lathe([(.62, -.25), (.66, 0), (.6, .12), (.48, .1), (.4, -.05), (0, -.05)], 12)), S('steel', base=.55, up=.15, jit=.01))
    P.gadd(R(T(torus(.56, .07, 12, 4), (0, .1, 0))), 'heal')
    capsule(P, tuple(V3(c) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ (Matrix.Rotation(math.radians(tilt), 3, 'X') @ V3((0, -.02, 0)))), tier, .85, yaw, tilt, 6)

# ------------------------------------------------------------------ care station
def heal_machine():
    """the Restoration Bay: plinth, white console with a tilted cradle deck of 6 capsule slots (glowing rings), a mint
    arch frame with a glowing inner ring over it, the Bloom Paw badge at the crown, two glass liquid columns with steel
    caps + bubbles, pipes, a side screen"""
    P = Prop('HealMachine')
    W = 13.0
    P.add(T(rbox((W + 1.2, 1.0, 5.0), .3), (0, .3, .2)), S('cream', base=.62, up=.15, jit=.01))
    P.add(T(rbox((W + 1.25, .3, 5.05), .1), (0, .1, .2)), S('mint', base=.45, up=.1, jit=.01))
    P.add(T(rbox((W, 3.2, 3.6), .45, 2), (0, 2.4, .5)), S('wall', base=.8, up=.12, jit=.01))
    P.add(T(rbox((W + .1, .35, 3.7), .12), (0, 1.2, .5)), S('mint', base=.55, up=.1, jit=.01))
    for k in range(6):                                                        # vent slots on the front lower panel
        x = -4.5 + k * 1.8
        P.add(T(rbox((1.1, .16, .1), .04, 1), (x, 1.75, -1.33)), S('steel', base=.35, jit=.01))
    # tilted cradle deck
    tilt = -24.0
    deck = T(rbox((W - .6, .5, 2.6), .2, 2), (0, 0, 0), 0, tilt)
    P.add(T(deck, (0, 4.1, -.3)), S('cream', base=.7, up=.12, jit=.01))
    tiers = ('mint', 'coral', 'sky', 'gold', 'mint', 'sky')
    for k in range(6):
        x = -5.0 + k * 2.0
        cradle(P, (x, 4.38, -.42), tiers[k], tilt)
    P.add(T(T(rbox((W - .2, .25, .4), .08), (0, 0, 0), 0, tilt), (0, 4.0, -1.55)), S('mint', base=.55, up=.1, jit=.01))
    # back wall of the machine + arch frame
    P.add(T(rbox((W, 3.0, 1.2), .3, 2), (0, 5.2, 1.7)), S('wall', base=.78, up=.12, jit=.01))
    archR = 5.6; ay = 5.6
    prof = [(math.cos(math.pi * k / 16) * archR, math.sin(math.pi * k / 16) * archR) for k in range(17)]
    inner = [(x * .82, y * .82) for x, y in prof]
    ring = []
    for (xa, ya), (xb, yb) in zip(prof, prof[1:]):
        pass
    outer_poly = prof + inner[::-1]
    P.add(upright(outer_poly, 1.0, (0, ay, 2.1)), S('mint', base=.55, up=.12, jit=.01))
    P.add(upright([(x * 1.04, y * 1.04) for x, y in prof] + [(x * .995, y * .995) for x, y in prof[::-1]], 1.15, (0, ay, 2.15)), S('teal', base=.5, up=.1, jit=.01))
    for sx in (-1, 1):                                                        # arch feet
        P.add(T(rbox((1.6, 1.2, 1.5), .25), (sx * archR * .91, ay - .2, 1.6)), S('wall', base=.85, up=.1, jit=.01))
    gl = tube([V3((math.cos(math.pi * k / 20) * archR * .78, ay + math.sin(math.pi * k / 20) * archR * .78, 1.45)) for k in range(21)], .16, sides=6)
    P.gadd(gl, 'heal')
    emblem_badge(P, (0, ay + archR + .7, 1.2), 0, 1.2)
    # soft light panel inside the arch (screen behind the deck)
    P.gadd(T(rbox((7.0, 2.6, .12), .1), (0, ay + 1.6, 1.62)), 'heal')
    P.add(T(rbox((7.6, 3.2, .3), .25), (0, ay + 1.6, 1.78)), S('teal', base=.42, jit=.01))
    # liquid columns
    for sx in (-1, 1):
        x = sx * (W / 2 + .5)
        P.add(T(lathe([(.9, 0), (.95, .5), (.8, .7), (0, .7)], 16), (x, .8, .3)), S('steel', base=.5, up=.15, jit=.01))
        P.gadd(T(cyl(.55, 5.4, 12, 0, .55, 1.5), (x, 0, .3)), 'liquid')
        P.add(T(lathe([(.72, 0), (.72, 5.6), (0, 5.6)], 14), (x, 1.4, .3)), S('glass', base=.8, jit=0))
        P.add(T(lathe([(.95, 0), (.95, .45), (.7, .75), (.35, .9), (0, .92)], 16), (x, 7.0, .3)), S('steel', base=.55, up=.15, jit=.01))
        for y in (2.3, 4.1, 5.9):
            P.add(T(torus(.75, .07, 14, 4), (x, y, .3)), S('steel', base=.62, jit=.01))
        rng = random.Random(3 + sx)
        for k in range(5):
            P.add(T(ball(.12, 6, 3), (x + rng.uniform(-.25, .25), rng.uniform(1.8, 6.5), .3 - .5)), S('wall', base=.95, jit=0))
        P.add(tube([V3((x, 7.6, .3)), V3((x, 8.4, .3)), V3((x * .86, 8.6, 1.2)), V3((x * .78, 7.6, 1.6))], .2, sides=6), S('steel', base=.48, jit=.01))
    # side screen on an arm (right)
    P.add(tube([V3((W / 2 - .6, 5.6, 1.4)), V3((W / 2 + .2, 6.8, .6))], .15, sides=6), S('steel', base=.5, jit=.01))
    sc = T(rbox((1.9, 1.3, .22), .12), (0, 0, 0), 0, 0)
    P.add(T(sc, (W / 2 + .3, 7.1, .5), -20), S('dark', base=.4, jit=.01))
    P.gadd(T(T(rbox((1.6, 1.0, .1), .05, 1), (0, 0, -.1)), (W / 2 + .3, 7.1, .5), -20), 'screen')
    return P

def heal_counter():
    """curved nurse desk (convex to the front): cream top with a rounded nose, mint front panels between white fins,
    Bloom Paw on the front, inner work shelf with monitor + keyboard, call bell, clipboard tray, little plant"""
    P = Prop('HealCounter')
    R = 15.0; a0, a1 = 270 - 26, 270 + 26
    C = V3((0, 0, R - 1.5))
    def rs(r0, r1, y0, y1, aa=a0, bb=a1, n=20):
        return T(ring_seg(r0, r1, y0, y1, aa, bb, n), tuple(C))
    P.add(rs(R - 3.0, R - .2, -.2, .25), S('mint', base=.4, jit=.01))                    # kick plinth
    P.add(rs(R - 2.8, R, .25, 3.5), S('wall', base=.82, up=.1, jit=.01))
    for k in range(9):                                                                   # mint panels + fins
        aa = lerp(a0 + 1.2, a1 - 1.2, k / 9); bb = lerp(a0 + 1.2, a1 - 1.2, (k + 1) / 9)
        P.add(rs(R - .05, R + .12, .7, 3.05, aa + .45, bb - .45, 3), S('mint', base=.58, up=.1, jit=.015))
    P.add(rs(R - 3.1, R + .45, 3.5, 3.8), S('cream', base=.72, up=.1, jit=.01))           # top
    P.add(rs(R + .25, R + .55, 3.42, 3.72), S('teal', base=.55, up=.1, jit=.01))           # nose band
    P.add(rs(R - 3.5, R - 2.8, 2.3, 2.55, a0 + 2, a1 - 2), S('cream', base=.6, jit=.01))   # inner work shelf
    emblem(P, (0, 2.0, -1.68), 0, .9, .14)
    for sx in (-1, 1):                                                                   # end caps
        a = math.radians(a0 if sx < 0 else a1)
        e = C + V3((math.cos(a) * (R - 1.4), 0, math.sin(a) * (R - 1.4)))
        P.add(T(cyl(1.55, 3.6, 16, .1), (e.x, 0, e.z)), S('wall', base=.86, up=.1, jit=.01))
        P.add(T(lathe([(1.7, 0), (1.7, .3), (0, .3)], 16), (e.x, 3.6, e.z)), S('cream', base=.74, jit=.01))
        P.add(T(torus(1.6, .1, 16, 4), (e.x, 2.6, e.z)), S('mint', base=.5, jit=.01))
    # monitor + keyboard on the inner side (customer sees the back)
    for sx in (-1, 1):
        mx = sx * 3.4; mz = .9
        P.add(T(lathe([(.45, 0), (.45, .08), (.12, .12), (0, .12)], 10), (mx, 3.8, mz)), S('steel', base=.5, jit=.01))
        P.add(T(cyl(.09, .9, 6), (mx, 3.8, mz)), S('steel', base=.45, jit=.01))
        P.add(T(rbox((2.1, 1.4, .18), .1), (mx, 5.2, mz), sx * 12), S('wall', base=.85, jit=.01))
        P.gadd(T(T(rbox((1.8, 1.1, .06), .04, 1), (0, 0, .1)), (mx, 5.2, mz), sx * 12), 'screen')
        P.add(T(rbox((1.6, .1, .55), .04, 1), (mx, 3.85, mz + .8), sx * 12), S('dark', base=.45, jit=.01))
    P.add(T(lathe([(.38, 0), (.38, .08), (.32, .3), (.12, .42), (0, .44)], 12), (1.6, 3.8, -.9)), S('gold', base=.58, up=.2, jit=.01))  # call bell
    P.add(T(ball(.07, 6, 3), (1.6, 4.28, -.9)), S('gold', base=.75, jit=.01))
    P.add(T(rbox((1.1, .08, 1.4), .04, 1), (-1.6, 3.84, -.6), 14), S('wood', base=.6, jit=.01))  # clipboard
    P.add(T(rbox((.9, .02, 1.1), .02, 1), (-1.6, 3.9, -.6), 14), S('wall', base=.95, jit=0))
    P.add(T(rbox((.5, .1, .14), .03, 1), (-1.6, 3.92, -1.2), 14), S('steel', base=.6, jit=.01))
    # little plant pot at the right end
    pot_plant(P, (5.3, 3.8, 1.0), .55)
    return P

def pot_plant(P, c, s=1.0, col='mint', seed=1):
    """small round pot + leafy sprouts (used on counters, desks)"""
    P.add(T(lathe([(.35, 0), (.45, .55), (.52, .62), (.48, .68), (0, .66)], 10), c, 0, 0, 0, s), S('wall', base=.85, up=.1, jit=.01))
    P.add(T(T(torus(.5, .05, 10, 3), (0, .6, 0)), c, 0, 0, 0, s), S(col, base=.5, jit=.01))
    rng = random.Random(seed)
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.3, .3); L = rng.uniform(.6, .95)
        b = V3((0, .62, 0)); t = V3((math.cos(a) * L * .55, .62 + L, math.sin(a) * L * .55))
        pts = [b, b.lerp(t, .5) + V3((0, .1, 0)), t]
        P.add(T(tube(pts, [.05, .2, .02], sides=4, flat=(2.6, .4)), c, 0, 0, 0, s), S('leaf', base=.45 + .08 * (k % 2), up=.15, jit=.03))

def bottle(P, c, col, kind=0, s=1.0):
    """kind 0 round flask (cork), 1 spray bottle (trigger head), 2 tall vial, 3 jar with lid"""
    L = lambda bm: T(bm, c, 0, 0, 0, s)
    if kind == 0:
        P.add(L(lathe([(.0, 0), (.32, .02), (.4, .25), (.36, .5), (.14, .62), (.14, .8), (0, .8)], 8)), S(col, base=.58, up=.2, jit=.02))
        P.add(L(T(cyl(.12, .16, 6), (0, .8, 0))), S('wood', base=.55, jit=.01))
    elif kind == 1:
        P.add(L(lathe([(0, 0), (.3, .02), (.32, .6), (.22, .75), (.14, .8), (0, .8)], 8)), S(col, base=.58, up=.2, jit=.02))
        P.add(L(T(rbox((.24, .24, .44), .06, 1), (0, .92, -.1))), S('wall', base=.85, jit=.01))
        P.add(L(T(rbox((.1, .26, .1), .03, 1), (0, .74, -.22))), S('wall', base=.8, jit=.01))
        P.add(L(T(cyl(.05, .06, 5), (0, .92, -.32), 0, 90)), S('dark', base=.4, jit=.01))
    elif kind == 2:
        P.add(L(lathe([(0, 0), (.16, .02), (.17, .9), (.12, 1.0), (0, 1.0)], 6)), S(col, base=.6, up=.2, jit=.02))
        P.add(L(T(cyl(.13, .14, 6), (0, 1.0, 0))), S('steel', base=.6, jit=.01))
    else:
        P.add(L(lathe([(0, 0), (.36, .02), (.38, .5), (.33, .56), (0, .56)], 8)), S('glass', base=.75, jit=.01))
        P.add(L(T(ball(.12, 6, 3), (-.1, .25, 0))), S(col, base=.6, jit=.02))
        P.add(L(T(ball(.12, 6, 3), (.12, .22, .08))), S(col, base=.66, jit=.02))
        P.add(L(lathe([(.38, .55), (.4, .7), (0, .72)], 8)), S(col, base=.5, up=.15, jit=.01))

def shelf_frame(P, W, H, D, rows, col='wall', trim='mint', top=True, back=True):
    """open shelving: side panels, back panel, kick base, `rows` shelf heights; crown cap. Front = -Z"""
    for sx in (-1, 1):
        P.add(T(rbox((.4, H, D), .12), (sx * (W / 2 - .2), H / 2, 0)), S(col, base=.84, up=.1, jit=.01))
    if back: P.add(T(rbox((W - .4, H - .3, .2), .05), (0, H / 2, D / 2 - .1)), S(trim, base=.72, up=.05, jit=.01))
    P.add(T(rbox((W - .3, .6, D - .2), .1), (0, .3, -.05)), S(trim, base=.45, up=.1, jit=.01))
    for y in rows:
        P.add(T(rbox((W - .5, .2, D - .25), .06), (0, y, -.05)), S(col, base=.8, up=.12, jit=.01))
        P.add(T(rbox((W - .6, .3, .08), .04, 1), (0, y - .02, -D / 2 + .08)), S(trim, base=.55, jit=.01))   # blank price strip
    if top:
        P.add(T(rbox((W + .3, .45, D + .3), .18), (0, H + .1, 0)), S(col, base=.88, up=.12, jit=.01))
        P.add(T(rbox((W + .35, .14, D + .35), .06), (0, H - .05, 0)), S(trim, base=.55, jit=.01))

def med_shelf(seed=1):
    """medical wall cabinet: open upper shelves with flasks, spray bottles, vials, jars and cream boxes; closed lower
    cabinet with handles; mint trim and a leaf on the crown"""
    P = Prop('MedShelf%d' % seed); rng = random.Random(seed)
    W, H, D = 8.0, 9.0, 1.8
    shelf_frame(P, W, H, D, (3.0, 5.0, 7.0))
    for sx in (-1, 1):                                                           # lower cabinet doors
        P.add(T(rbox((W / 2 - .45, 2.15, .18), .1), (sx * (W / 4 - .05), 1.75, -D / 2 + .02)), S('cream', base=.76, up=.08, jit=.01))
        P.add(T(rbox((.12, .9, .16), .05, 1), (sx * .45, 1.9, -D / 2 - .12)), S('steel', base=.6, jit=.01))
    cols = ('mint', 'coral', 'sky', 'berry', 'gold')
    for y in (3.1, 5.1, 7.1):
        x = -W / 2 + .8
        while x < W / 2 - .7:
            k = rng.random()
            if k < .22:
                P.add(T(rbox((1.1, .8, 1.0), .08), (x + .3, y + .5, 0)), S('cream', base=.85, up=.1, jit=.02))
                P.add(T(rbox((1.12, .18, 1.02), .04, 1), (x + .3, y + .55, 0)), S(rng.choice(cols), base=.58, jit=.01))
                x += 1.4
            else:
                bottle(P, (x, y + .1, rng.uniform(-.3, .1)), rng.choice(cols), rng.choice((0, 1, 2, 3)), rng.uniform(.9, 1.15)); x += .78
    P.add(upright(leaf_poly(.9, .3, 6, 0, (0, 0)), .12, (0, H + .3, -D / 2 - .06)), S('mint', base=.55, jit=.01))
    return P

def wait_bench(seed=1, L=8.0, col='teal'):
    """waiting bench: steel loop legs, cushioned seat + back in teal, white arm rests with rounded caps"""
    P = Prop('WaitBench%s' % col[0].upper())
    for sx in (-1, 1):
        x = sx * (L / 2 - .5)
        pts = [V3((x, -.3, -.8)), V3((x, 1.7, -.8)), V3((x, 1.8, .9)), V3((x, 3.9, 1.2))]
        P.add(tube([V3((x, -.3, -.8)), V3((x, 1.75, -.8))], .14, sides=6), S('steel', base=.55, jit=.01))
        P.add(tube([V3((x, -.3, .8)), V3((x, 1.75, .8)), V3((x, 3.6, 1.1))], .14, sides=6), S('steel', base=.55, jit=.01))
        P.add(T(rbox((.6, .35, 2.4), .15), (x + sx * .25, 2.75, -.05)), S('wall', base=.86, up=.1, jit=.01))       # arm rest
        P.add(tube([V3((x + sx * .25, 1.75, -.8)), V3((x + sx * .25, 2.6, -.8))], .1, sides=6), S('steel', base=.6, jit=.01))
    P.add(T(rbox((L - .4, .3, 1.8), .1), (0, 1.6, 0)), S('steel', base=.5, jit=.01))
    P.add(T(rbox((L - 1.4, .55, 1.9), .25, 2), (0, 2.0, -.05)), S(col, base=.55, up=.15, jit=.01))
    P.add(T(T(rbox((L - 1.4, 1.6, .5), .22, 2), (0, 0, 0), 0, 12), (0, 3.15, .95)), S(col, base=.52, up=.12, jit=.01))
    for k in range(3):                                                          # tufted seams on the back
        x = -(L - 2.4) / 2 + k * (L - 2.4) / 2
        P.add(T(T(rbox((.08, 1.2, .1), .03, 1), (0, 0, 0), 0, 12), (x, 3.15, .68)), S(col, base=.35, jit=.01))
    return P

# ------------------------------------------------------------------ mart
def shop_counter():
    """mart counter: white body, coral front panels, glass display case on the customer side holding a capsule tray,
    register with a blank glowing screen, card reader, paper-bag stand, a coral awning lip"""
    P = Prop('ShopCounter')
    W, H, D = 12.0, 3.6, 3.2
    P.add(T(rbox((W + .2, .35, D + .2), .1), (0, .05, 0)), S('coral', base=.38, jit=.01))
    P.add(T(rbox((W, H - .3, D), .3, 2), (0, H / 2 + .05, 0)), S('wall', base=.82, up=.1, jit=.01))
    for k in range(4):
        x = -W / 2 + 1.5 + k * 3.0
        P.add(T(rbox((2.6, 2.4, .14), .12), (x, 1.8, -D / 2 - .03)), S('coral', base=.58, up=.1, jit=.015))
    emblem(P, (-W / 2 + 4.5, 1.8, -D / 2 - .1), 0, .55, .1, pad='wall', toe='wall', base=.9)
    P.add(T(rbox((W + .4, .3, D + .4), .12), (0, H, 0)), S('cream', base=.74, up=.1, jit=.01))
    # glass display case on the left half
    cx = -2.6
    P.add(T(rbox((6.0, .2, 2.2), .05), (cx, H + .2, -.3)), S('steel', base=.55, jit=.01))
    for k in range(6):
        capsule(P, (cx - 2.4 + k * .95, H + .32, -.35), TIERS[k % 4], .7, 0, 0, 8, True)
    P.add(T(rbox((6.0, 1.3, 2.2), .08), (cx, H + .95, -.3)), S('glass', base=.86, jit=0))
    P.add(T(rbox((6.1, .1, 2.3), .03, 1), (cx, H + 1.62, -.3)), S('steel', base=.62, jit=.01))
    # register
    rx = 3.2
    P.add(T(rbox((2.4, .6, 1.8), .15), (rx, H + .45, .3)), S('wall', base=.86, jit=.01))
    P.add(T(rbox((2.2, .1, .9), .04, 1), (rx, H + .78, -.1)), S('dark', base=.4, jit=.01))
    for i in range(3):
        for j in range(4):
            P.add(T(rbox((.32, .1, .2), .03, 1), (rx - .55 + j * .37, H + .86, -.38 + i * .28)), S('cream', base=.85, jit=.01))
    P.add(T(cyl(.12, .9, 6), (rx, H + .7, .7)), S('steel', base=.5, jit=.01))
    P.add(T(T(rbox((1.9, 1.3, .18), .1), (0, 0, 0), 0, -15), (rx, H + 1.95, .75), 180), S('wall', base=.86, jit=.01))
    P.gadd(T(T(rbox((1.6, 1.0, .06), .04, 1), (0, 0, -.1), 0, 15), (rx, H + 1.95, .75)), 'screen')
    P.add(T(T(rbox((.6, .25, .9), .08), (0, 0, 0), 0, 20), (rx + 2.0, H + .3, -.6)), S('dark', base=.45, jit=.01))  # card reader
    # bag stand at the right end
    for k in range(4):
        P.add(T(T(rbox((1.0, 1.3, .35), .08), (0, 0, 0), 0, 0, -6 + k * 4), (W / 2 - .9, H + .8, .3 + k * .1)), S('cream' if k % 2 else 'wood', base=.7, jit=.02))
    P.add(T(rbox((W + .6, .25, .6), .1), (0, H - .1, -D / 2 - .35)), S('coral', base=.5, up=.1, jit=.01))
    return P

def capsule_shelf(seed=1):
    """capsule gondola: four shelves of stepped display risers, one tier per shelf (mint, sky, coral, gold) bottom to
    top, coral trim, a big hero capsule on a crown plinth"""
    P = Prop('CapsuleShelf%d' % seed)
    W, H, D = 10.0, 9.0, 2.4
    shelf_frame(P, W, H, D, (1.4, 3.5, 5.6, 7.7), trim='coral')
    for r, (y, tier) in enumerate(zip((1.5, 3.6, 5.7, 7.8), TIERS)):
        P.add(T(rbox((W - .8, .3, .7), .08), (0, y + .15, .25)), S('cream', base=.82, jit=.01))      # riser step
        for k in range(5):
            x = -W / 2 + 1.4 + k * 1.8
            back = k % 2 == 1
            capsule(P, (x, y + (.3 if back else 0) + .1, .25 if back else -.45), tier, 1.05, 0, 0, 6, False)
    P.add(T(lathe([(.9, 0), (.9, .3), (.6, .5), (0, .5)], 12), (0, H + .3, 0)), S('coral', base=.55, jit=.01))
    capsule(P, (0, H + .8, 0), 'coral', 1.8, 0, 0, 8, True)
    return P

def potion_shelf(seed=2):
    """potion shelf: flasks, spray tonics, vials and berry jars in four colour runs, cream boxes at the ends"""
    P = Prop('PotionShelf%d' % seed); rng = random.Random(seed)
    W, H, D = 10.0, 9.0, 2.0
    shelf_frame(P, W, H, D, (1.4, 3.5, 5.6, 7.7), trim='coral')
    runs = (('mint', 1), ('berry', 0), ('sky', 2), ('gold', 3))
    for (y, (col, kind)) in zip((1.5, 3.6, 5.7, 7.8), runs):
        P.add(T(rbox((1.3, 1.0, 1.1), .1), (-W / 2 + 1.2, y + .6, 0)), S('cream', base=.85, up=.1, jit=.02))
        P.add(T(rbox((1.32, .2, 1.12), .04, 1), (-W / 2 + 1.2, y + .75, 0)), S(col, base=.55, jit=.01))
        for k in range(8):
            x = -W / 2 + 2.4 + k * .86
            bottle(P, (x, y + .1, -.3 if k % 2 else .2), col, kind, 1.15 if kind != 2 else 1.0)
    return P

def berry_baskets(seed=1):
    """tiered birch crate stand with three woven baskets heaped with berries (pink, gold, blue) and a leaf sprig"""
    P = Prop('BerryBaskets'); rng = random.Random(seed)
    for k, (w, h, z) in enumerate(((5.6, 2.6, .9), (5.6, 1.3, -.7))):
        P.add(T(rbox((w, h, 1.6), .1), (0, h / 2, z)), S('wood', base=.6, up=.12, jit=.02))
        for j in range(int(h / .45)):
            P.add(T(rbox((w + .05, .14, 1.62), .04, 1), (0, .2 + j * .45, z)), S('wood', base=.38, jit=.01))
    for k, (x, y, z, col) in enumerate(((-1.8, 2.6, .9, 'berry'), (0, 2.6, .9, 'gold'), (1.8, 2.6, .9, 'sky'), (-1.0, 1.3, -.7, 'berry'), (1.1, 1.3, -.7, 'mint'))):
        P.add(T(lathe([(.5, 0), (.75, .55), (.8, .62), (.72, .62), (0, .5)], 10), (x, y, z)), S('wood', base=.56, up=.1, jit=.02))
        for yy in (.18, .38):
            P.add(T(torus(.6 + yy * .3, .05, 10, 3), (x, y + yy, z)), S('wood', base=.38, jit=.01))
        for j in range(9):
            a = rng.uniform(0, math.tau); d = rng.uniform(0, .5)
            P.add(T(ball(.2, 6, 4), (x + math.cos(a) * d, y + .62 + (.5 - d) * .4, z + math.sin(a) * d)), S(col if col != 'mint' else 'leaf', base=rng.uniform(.5, .7), up=.2, jit=.02))
        P.add(T(tube([V3((x, y + .9, z)), V3((x + .3, y + 1.3, z - .1))], [.05, .02], sides=4, flat=(3, .5)), (0, 0, 0)), S('leaf', base=.5, jit=.02))
    return P

def display_rack():
    """round three-tier display rack: steel pole, coral discs, boxed capsules on each tier, capsule finial"""
    P = Prop('DisplayRack'); rng = random.Random(5)
    P.add(lathe([(1.8, 0), (1.8, .3), (1.4, .5), (0, .5)], 20), S('steel', base=.5, up=.15, jit=.01))
    P.add(T(cyl(.18, 6.8, 8), (0, .5, 0)), S('steel', base=.6, jit=.01))
    for k, (y, r) in enumerate(((1.6, 2.6), (3.6, 2.1), (5.6, 1.6))):
        P.add(T(lathe([(r, 0), (r + .1, .1), (r, .25), (0, .25)], 20), (0, y, 0)), S('coral', base=.58, up=.15, jit=.01))
        P.add(T(torus(r + .02, .08, 20, 4), (0, y + .25, 0)), S('wall', base=.9, jit=.01))
        n = int(r * 2.6)
        for j in range(n):
            a = j * math.tau / n + k * .3; tier = TIERS[(j + k) % 4]
            x, z = math.cos(a) * (r - .55), math.sin(a) * (r - .55)
            P.add(T(rbox((.8, 1.0, .5), .08), (x, y + .75, z), -math.degrees(a) + 90), S('wall', base=.86, jit=.02))
            P.add(T(rbox((.82, .3, .52), .05, 1), (x, y + .95, z), -math.degrees(a) + 90), S(tier, base=.58, jit=.01))
            R = Matrix.Rotation(math.radians(-math.degrees(a) + 90), 3, 'Y')
            capsule(P, tuple(V3((x, y + .3, z)) + R @ V3((0, 0, -.27))), tier, .4, -math.degrees(a) + 90, 0, 6, False)
    capsule(P, (0, 7.3, 0), 'gold', 1.0, 0, 0, 8, True)
    return P

# ------------------------------------------------------------------ storage + trade
def pc_terminal(seed=1, col='sky'):
    """storage terminal: rounded pedestal, angled neck, big framed screen (blank glow), keyboard deck with keys,
    capsule dock port with a glowing ring on the right, cable conduit"""
    P = Prop('PCTerminal')
    P.add(T(rbox((3.4, .6, 2.6), .25, 2), (0, .2, 0)), S('wall', base=.84, up=.12, jit=.01))
    P.add(T(rbox((3.45, .2, 2.65), .08), (0, .05, 0)), S(col, base=.45, jit=.01))
    P.add(T(T(rbox((1.6, 3.6, 1.2), .35, 2), (0, 0, 0), 0, 10), (0, 2.2, .35)), S('wall', base=.82, up=.1, jit=.01))
    P.add(T(T(rbox((1.65, .3, 1.25), .1), (0, 0, 0), 0, 10), (0, 1.3, .2)), S(col, base=.55, jit=.01))
    # keyboard deck
    kb = T(rbox((3.0, .35, 1.4), .15), (0, 0, 0), 0, -18)
    P.add(T(kb, (0, 3.75, -.75)), S('wall', base=.86, up=.1, jit=.01))
    for i in range(3):
        for j in range(7):
            k = T(T(rbox((.32, .14, .3), .04, 1), (-1.1 + j * .37, .2, -.35 + i * .36), 0, 0), (0, 0, 0), 0, -18)
            P.add(T(k, (0, 3.75, -.75)), S('dark' if (i + j) % 5 else col, base=.42, jit=.02))
    # screen
    scr = (0, 5.9, .55)
    P.add(T(T(rbox((3.6, 2.6, .35), .25, 2), (0, 0, 0), 0, -8), scr), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(T(rbox((3.7, .3, .4), .1), (0, -1.3, 0), 0, -8), scr), S(col, base=.55, jit=.01))
    P.add(T(T(rbox((3.15, 2.15, .1), .1, 1), (0, .05, -.2), 0, -8), scr), S('dark', base=.3, jit=.01))
    P.gadd(T(T(rbox((2.9, 1.9, .06), .08, 1), (0, .05, -.27), 0, -8), scr), 'screen')
    # capsule dock port
    P.add(T(T(cyl(.55, .7, 12, .08), (0, 0, 0), 0, 0, -90), (1.25, 3.55, -.7)), S('steel', base=.55, jit=.01))
    P.add(T(T(lathe([(.62, 0), (.62, .12), (.45, .2), (0, .16)], 12), (0, 0, 0), 0, 0, -90), (1.92, 3.55, -.7)), S('sky', base=.55, jit=.01))
    P.gadd(T(T(torus(.42, .06, 12, 4), (0, 0, 0), 0, 0, 90), (2.1, 3.55, -.7)), 'gem')
    P.add(tube([V3((0, .4, 1.1)), V3((0, .3, 1.6)), V3((0, -.3, 1.7))], .2, sides=6), S('dark', base=.4, jit=.01))
    return P

def swap_icon(P, pos, yaw=0.0, s=1.0, d=.18, ca='sky', cb='coral'):
    """two curved arrows chasing each other in a circle (trade icon, a shape)"""
    for k, col in ((0, ca), (1, cb)):
        a0 = k * math.pi + .25; a1 = a0 + math.pi - .7
        outer = [(math.cos(lerp(a0, a1, t / 8)) * 1.0, math.sin(lerp(a0, a1, t / 8)) * 1.0) for t in range(9)]
        inner = [(math.cos(lerp(a0, a1, t / 8)) * .62, math.sin(lerp(a0, a1, t / 8)) * .62) for t in range(9)]
        ah = a1; tip = (math.cos(ah + .38) * .81, math.sin(ah + .38) * .81)
        head = [(math.cos(ah) * 1.22, math.sin(ah) * 1.22), tip, (math.cos(ah) * .4, math.sin(ah) * .4)]
        P.add(upright(outer + inner[::-1], d, pos, yaw, s), S(col, base=.58, up=.1, jit=.01))
        P.add(upright(head, d, pos, yaw, s), S(col, base=.58, up=.1, jit=.01))

def trade_desk():
    """trade / battle registration desk: white desk with sky panels, a raised arch with the swap icon, two monitors,
    two capsule pedestals facing each other on the top, a ticket stand, and a queue of three stanchions with ropes"""
    P = Prop('TradeDesk')
    W, H, D = 11.0, 3.6, 3.0
    P.add(T(rbox((W + .2, .3, D + .2), .1), (0, .05, 0)), S('sky', base=.38, jit=.01))
    P.add(T(rbox((W, H - .25, D), .3, 2), (0, H / 2, 0)), S('wall', base=.82, up=.1, jit=.01))
    for k in range(3):
        P.add(T(rbox((3.0, 2.3, .14), .12), (-3.4 + k * 3.4, 1.8, -D / 2 - .03)), S('sky', base=.58, up=.1, jit=.015))
    P.add(T(rbox((W + .4, .3, D + .4), .12), (0, H, 0)), S('cream', base=.74, up=.1, jit=.01))
    # back arch with the swap icon
    prof = [(math.cos(math.pi * k / 12) * 3.2, math.sin(math.pi * k / 12) * 2.4) for k in range(13)]
    P.add(upright(prof + [(x * .8, y * .75) for x, y in prof[::-1]], .6, (0, H + .2, 1.6)), S('sky', base=.5, up=.1, jit=.01))
    P.add(upright([(x * .8, y * .75) for x, y in prof], .3, (0, H + .2, 1.75)), S('wall', base=.9, jit=0))
    swap_icon(P, (0, H + 1.8, 1.44), 0, 1.0, .14)
    for sx in (-1, 1):                                                          # monitors + capsule pedestals
        mx = sx * 4.3
        P.add(T(cyl(.1, .8, 6), (mx, H + .15, .7)), S('steel', base=.45, jit=.01))
        P.add(T(rbox((2.0, 1.3, .16), .1), (mx, H + 1.4, .7), 180), S('wall', base=.86, jit=.01))
        P.gadd(T(rbox((1.7, 1.0, .06), .04, 1), (mx, H + 1.4, .6)), 'screen')
        px = sx * 2.7
        P.add(T(lathe([(.55, 0), (.55, .2), (.35, .35), (.3, .75), (.45, .85), (0, .85)], 12), (px, H + .15, -.6)), S('steel', base=.55, up=.15, jit=.01))
        capsule(P, (px, H + 1.0, -.6), 'sky' if sx < 0 else 'coral', .9, -sx * 50)
    P.add(T(T(rbox((1.0, 1.4, .1), .05), (0, 0, 0), 0, -20), (W / 2 - 1.0, H + .8, -.6)), S('wall', base=.92, jit=0))   # ticket stand
    P.add(T(rbox((.9, .15, .5), .05), (W / 2 - 1.0, H + .2, -.5)), S('sky', base=.5, jit=.01))
    # queue stanchions in front
    posts = [(-3.0, -6.0), (0, -7.0), (3.0, -6.0)]
    for x, z in posts:
        P.add(T(lathe([(.55, 0), (.55, .15), (.15, .25), (0, .25)], 12), (x, 0, z)), S('steel', base=.5, jit=.01))
        P.add(T(cyl(.12, 2.6, 8), (x, .2, z)), S('steel', base=.62, jit=.01))
        P.add(T(ball(.2, 8, 4), (x, 2.85, z)), S('sky', base=.55, up=.2, jit=.01))
    for (xa, za), (xb, zb) in zip(posts, posts[1:]):
        P.add(tube(sag((xa, 2.55, za), (xb, 2.55, zb), .5, 6), .09, sides=5), S('sky', base=.45, jit=.01))
    return P

# ------------------------------------------------------------------ research lab
def egg(P, c, s=1.0, col='mint', spot='wall'):
    prof = [(0, 0)] + [(math.sin(math.pi * k / 8) * (.62 if k < 5 else .62 - (k - 4) * .05), (1 - math.cos(math.pi * k / 8)) * .78) for k in range(1, 8)] + [(0, 1.56)]
    P.add(T(lathe(prof, 10), c, 0, 0, 0, s), S(col, base=.6, up=.2, jit=.02))
    for a, y in ((.4, .5), (2.4, .8), (4.2, .45), (5.5, 1.05)):
        P.add(T(T(lathe([(.16, 0), (.12, .06), (0, .07)], 6), (0, 0, 0), 0, 0, -90), (c[0] + math.cos(a) * .6 * s, c[1] + y * s, c[2] + math.sin(a) * .6 * s), -math.degrees(a)), S(spot, base=.85, jit=.01))

def specimen_tank(col='liquid', seed=1):
    """specimen tank: steel base drum with a teal band + front control panel, glass cylinder of glowing liquid with a
    spotted creature egg inside and rising bubbles, domed steel cap with hoses curling back into the wall"""
    P = Prop('SpecimenTank%s' % ('A' if col == 'liquid' else 'B')); rng = random.Random(seed)
    R, H = 2.0, 7.5
    P.add(lathe([(2.7, -.2), (2.7, .4), (2.55, .6), (2.55, 1.5), (2.75, 1.7), (2.75, 2.1), (2.4, 2.3), (0, 2.3)], 20), S('steel', base=.55, up=.15, jit=.01))
    P.add(T(torus(2.62, .14, 20, 5), (0, 1.0, 0)), S('teal', base=.55, jit=.01))
    for k in range(4):                                                          # feet
        a = k * math.tau / 4 + math.pi / 4
        P.add(T(rbox((.9, .5, .9), .15), (math.cos(a) * 2.3, -.05, math.sin(a) * 2.3), -math.degrees(a)), S('dark', base=.4, jit=.01))
    P.add(T(rbox((2.2, 1.4, .5), .15), (0, 1.25, -2.65)), S('wall', base=.86, jit=.01))      # control panel
    P.add(T(rbox((1.9, 1.1, .1), .06, 1), (0, 1.3, -2.92)), S('dark', base=.35, jit=.01))
    for k, c2 in enumerate(('mint', 'gold', 'coral')):
        P.add(T(T(cyl(.14, .14, 8), (0, 0, 0), 0, -90), (-.55 + k * .55, 1.05, -2.98)), S(c2, base=.6, jit=.01))
    P.gadd(T(rbox((1.6, .35, .06), .04, 1), (0, 1.55, -2.99)), 'screen')
    P.gadd(T(cyl(R - .2, H - .4, 16, 0, R - .2, 2.4), (0, 0, 0)), col)
    P.add(T(lathe([(R, 0), (R, H), (0, H)], 18), (0, 2.3, 0)), S('glass', base=.8, jit=0))
    egg(P, (0, 4.2, 0), 1.3, 'mint' if col == 'liquid' else 'sky', 'wall')
    for k in range(8):
        P.add(T(ball(rng.uniform(.08, .16), 6, 3), (rng.uniform(-1.3, 1.3), rng.uniform(3, 9.2), rng.uniform(-1.4, -1.0))), S('wall', base=.95, jit=0))
    for y in (2.3 + H * .33, 2.3 + H * .66):
        P.add(T(torus(R + .08, .1, 18, 4), (0, y, 0)), S('steel', base=.62, jit=.01))
    yt = 2.3 + H
    P.add(T(lathe([(2.6, 0), (2.6, .5), (2.2, 1.0), (1.2, 1.5), (.5, 1.65), (0, 1.66)], 20), (0, yt, 0)), S('steel', base=.55, up=.15, jit=.01))
    P.add(T(torus(2.5, .14, 20, 5), (0, yt + .3, 0)), S('teal', base=.55, jit=.01))
    P.add(T(lathe([(.5, 0), (.5, .5), (.3, .7), (0, .7)], 10), (0, yt + 1.6, 0)), S('dark', base=.45, jit=.01))
    for sx in (-1, 1):
        P.add(tube([V3((sx * .9, yt + 1.4, .4)), V3((sx * 1.1, yt + 2.6, 1.2)), V3((sx * 1.2, yt + 2.4, 2.6)), V3((sx * 1.2, yt + 1.2, 3.1))], .2, sides=6), S('dark', base=.4, jit=.01))
    return P

def evo_chamber():
    """HERO: the Bloom Chamber (evolution / scan chamber). Two-step round dais with teal riser and glow rim, a pad with
    the Bloom Paw and a glowing ring, three floating scan rings held by a C-shaped gantry rising from behind, an emitter
    crown with a light lens on top, cable runs to a curved control console at the front right, four corner light posts"""
    P = Prop('EvoChamber')
    R = 8.5
    P.add(lathe([(R + 2.4, -.3), (R + 2.4, .45), (R + 2.2, .6), (0, .6)], 40), S('wall', base=.84, up=.12, jit=.01))
    P.add(T(lathe([(R + 2.45, 0), (R + 2.45, .2), (0, .2)], 40), (0, -.1, 0)), S('teal', base=.45, jit=.01))
    P.add(T(lathe([(R, 0), (R, .9), (R - .3, 1.1), (0, 1.1)], 40), (0, .5, 0)), S('cream', base=.74, up=.12, jit=.01))
    P.gadd(T(torus(R + .05, .14, 40, 5), (0, 1.25, 0)), 'evo')
    P.add(T(lathe([(R - 2.0, 0), (R - 2.0, .2), (0, .2)], 36), (0, 1.6, 0)), S('teal', base=.5, jit=.01))
    P.gadd(T(torus(R - 2.2, .18, 36, 5), (0, 1.82, 0)), 'evo')
    for k in range(12):                                                        # floor rays on the pad
        a = k * math.tau / 12
        P.add(T(T(rbox((2.2, .1, .5), .04, 1), (R - 4.6, 0, 0)), (0, 1.84, 0), -math.degrees(a)), S('sky' if k % 2 else 'mint', base=.6, jit=.01))
    pad = [(math.cos(t) * .62, math.sin(t) * .46) for t in [k * math.tau / 20 for k in range(20)]]
    pad = [(x * (1 - .18 * max(0, -y) / .46), y + .12 * math.cos(2 * math.atan2(y, x)) * (y > 0) - .38) for x, y in pad]
    P.add(T(ngon_prism([(x * 2.0, -y * 2.0) for x, y in pad], 0, .14), (0, 1.8, 0)), S('coral', base=.6, jit=.01))
    for a, L, cx, cy in ((-38, .78, -.5, .22), (0, .9, 0, .38), (38, .78, .5, .22)):
        lp = [(x * 2.0, -y * 2.0) for x, y in leaf_poly(L, .2, 6, a, (cx, cy))]
        P.add(T(ngon_prism(lp, 0, .14), (0, 1.8, 0)), S('mint', base=.6, jit=.01))
    # C gantry from the back (+Z): base block, curved spine, top arm
    gz = R + .4
    P.add(T(rbox((5.0, 2.4, 3.2), .5, 2), (0, 1.2, gz + .6)), S('wall', base=.8, up=.1, jit=.01))
    spine = [V3((0, 2.0, gz + .6)), V3((0, 8.0, gz + 1.2)), V3((0, 13.0, gz)), V3((0, 16.6, gz - 3.0)), V3((0, 17.4, gz - 6.8)), V3((0, 17.2, 0))]
    P.add(tube(spine, [1.25, 1.15, 1.1, 1.0, .95, .9], sides=8, flat=(1.0, 1.6)), S('wall', base=.84, up=.12, jit=.01))
    P.add(tube(spine, [1.3, 1.2, 1.15, 1.05, 1.0, .95], sides=8, flat=(1.02, .45)), S('teal', base=.5, jit=.01))
    for k, (y, r) in enumerate(((5.0, 6.2), (9.0, 5.6), (13.0, 5.0))):          # scan rings + their arms to the spine
        P.add(T(torus(r, .42, 40, 7), (0, y, 0)), S('wall', base=.86, up=.15, jit=.01))
        P.gadd(T(torus(r - .45, .14, 40, 5), (0, y, 0)), 'evo')
        P.add(T(torus(r + .38, .1, 40, 4), (0, y, 0)), S('teal', base=.55, jit=.01))
        sz = gz + (.9 if k == 0 else 1.0 if k == 1 else .4)
        P.add(T(rbox((1.2, 1.0, sz - r + .2), .25), (0, y, (r + sz) / 2)), S('steel', base=.55, jit=.01))
        for sx in (-1, 1):
            P.add(T(ball(.35, 8, 4), (sx * r, y, 0)), S('gold', base=.6, up=.2, jit=.01))
    # emitter crown above the rings
    yc = 16.0
    P.add(T(lathe([(.4, 0), (2.8, .3), (3.0, .9), (2.4, 1.3), (1.0, 1.5), (0, 1.5)], 24), (0, yc, 0)), S('wall', base=.84, up=.15, jit=.01))
    P.add(T(torus(2.9, .16, 24, 5), (0, yc + .65, 0)), S('teal', base=.55, jit=.01))
    P.gadd(T(lathe([(0, 0), (1.6, .2), (1.9, .5), (0, .55)], 20), (0, yc - .45, 0)), 'evo')
    for k in range(6):
        a = k * math.tau / 6
        P.add(T(spike(.25, 1.2, 5, shoulder=.5), (math.cos(a) * 2.4, yc + 1.2, math.sin(a) * 2.4)), S('gold', base=.6, jit=.01))
    for k in range(6):                                                          # faint light column (thin glow bars)
        a = k * math.tau / 6 + .25
        P.gadd(T(cyl(.07, 12.5, 4), (math.cos(a) * 1.4, 2.0, math.sin(a) * 1.4)), 'evo')
    # control console (front right), cables to the dais
    con = Prop('_c')
    con.add(T(rbox((5.0, 3.2, 2.0), .4, 2), (0, 1.6, 0)), S('wall', base=.84, up=.1, jit=.01))
    con.add(T(T(rbox((5.2, .4, 2.6), .2, 2), (0, 0, 0), 0, -20), (0, 3.5, -.5)), S('cream', base=.72, up=.1, jit=.01))
    for i in range(2):
        for j in range(6):
            con.add(T(T(cyl(.16, .2, 8), (-1.8 + j * .72, .25, -.5 + i * .7), 0, -20), (0, 3.5, -.4)), S(('mint', 'sky', 'coral', 'gold')[(i + j) % 4], base=.6, jit=.01))
    con.add(T(rbox((5.0, 2.4, .3), .2), (0, 5.2, 1.0)), S('wall', base=.86, jit=.01))
    con.gadd(T(rbox((4.4, 1.9, .08), .1, 1), (0, 5.2, .8)), 'screen')
    con.add(T(rbox((5.1, .3, 2.1), .1), (0, .1, 0)), S('teal', base=.45, jit=.01))
    merge_prop(P, con, (R + 3.8, 0, -R + 1.0), 1.0, 40)
    for a, b in (((R + 2.0, -R + 3.2), (R - .5, -2.0)), ((R + 4.4, -R + 2.4), (R + 1.0, 2.0))):
        pts = [V3((a[0], .15, a[1])), V3(((a[0] + b[0]) / 2 + .8, .2, (a[1] + b[1]) / 2)), V3((b[0], .25, b[1]))]
        P.add(tube(pts, .22, sides=6), S('dark', base=.35, jit=.01))
    for k in range(4):                                                         # corner light posts
        a = k * math.tau / 4 + math.pi / 4
        x, z = math.cos(a) * (R + 1.6), math.sin(a) * (R + 1.6)
        P.add(T(lathe([(.45, 0), (.45, .3), (.25, .45), (.25, 2.4), (.4, 2.6), (0, 2.65)], 10), (x, .5, z)), S('wall', base=.86, jit=.01))
        P.gadd(T(lathe([(.3, 0), (.34, .4), (0, .5)], 8), (x, 3.1, z)), 'evo')
    return P

def lab_table(P, W, D, H=3.6, col='wall'):
    """lab table: white top with a teal edge, steel legs with feet, a stretcher, cream drawer block with handles"""
    P.add(T(rbox((W, .3, D), .1), (0, H, 0)), S(col, base=.86, up=.12, jit=.01))
    P.add(T(rbox((W + .1, .16, D + .1), .05, 1), (0, H - .18, 0)), S('teal', base=.5, jit=.01))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(cyl(.14, H - .3, 6), (sx * (W / 2 - .4), 0, sz * (D / 2 - .4))), S('steel', base=.55, jit=.01))
            P.add(T(lathe([(.3, 0), (.3, .12), (0, .12)], 8), (sx * (W / 2 - .4), -.05, sz * (D / 2 - .4))), S('dark', base=.4, jit=.01))
    P.add(T(rbox((W - .8, .14, .2), .04, 1), (0, .9, D / 2 - .4)), S('steel', base=.55, jit=.01))
    if W > 5:
        dx = W / 2 - 2.0
        P.add(T(rbox((2.6, 2.4, D - .6), .15), (dx, H - 1.4, 0)), S('cream', base=.78, up=.1, jit=.01))
        for j in range(3):
            P.add(T(rbox((2.3, .66, .1), .06, 1), (dx, H - .6 - j * .78, -D / 2 + .25)), S('cream', base=.86, jit=.01))
            P.add(T(rbox((.7, .1, .14), .04, 1), (dx, H - .5 - j * .78, -D / 2 + .16)), S('steel', base=.62, jit=.01))

def workbench(seed=1):
    """lab workbench: table + test-tube rack with coloured tubes, conical + round flasks, a mini centrifuge with a domed
    lid, an open notebook, an angle lamp with a glowing shade"""
    P = Prop('Workbench%d' % seed); rng = random.Random(seed)
    W, D, H = 8.0, 3.4, 3.6
    lab_table(P, W, D, H)
    y = H + .15
    P.add(T(rbox((2.2, .2, .9), .05), (-2.4, y + .1, -.5)), S('steel', base=.55, jit=.01))         # tube rack
    P.add(T(rbox((2.2, .14, .9), .04, 1), (-2.4, y + .9, -.5)), S('steel', base=.6, jit=.01))
    for sx in (-1, 1):
        P.add(T(rbox((.12, 1.0, .9), .03, 1), (-2.4 + sx * 1.05, y + .55, -.5)), S('steel', base=.5, jit=.01))
    for k in range(6):
        c = ('mint', 'berry', 'sky', 'gold', 'coral', 'mint')[k]; f = rng.uniform(.5, .9)
        P.add(T(lathe([(0, 0), (.12, .05), (.12, 1.3), (0, 1.3)], 6), (-3.25 + k * .34, y + .2, -.5)), S('glass', base=.8, jit=0))
        P.add(T(lathe([(0, 0), (.1, .05), (.1, f), (0, f)], 6), (-3.25 + k * .34, y + .22, -.5)), S(c, base=.62, jit=.01))
    P.add(T(lathe([(.7, 0), (.7, .1), (.25, 1.0), (.2, 1.4), (.26, 1.5), (0, 1.5)], 10), (-.4, y, -.6)), S('glass', base=.82, jit=0))     # conical flask
    P.add(T(lathe([(.62, 0), (.62, .08), (.3, .55), (0, .6)], 10), (-.4, y + .02, -.6)), S('mint', base=.62, jit=.01))
    P.add(T(lathe([(0, 0), (.45, .05), (.55, .4), (.45, .75), (.16, .9), (.16, 1.4), (0, 1.4)], 10), (.6, y, .4)), S('berry', base=.6, up=.2, jit=.01))
    P.add(T(lathe([(.9, 0), (.95, .7), (.85, .8), (0, .8)], 14), (2.4, y, .4)), S('wall', base=.86, jit=.01))   # centrifuge
    P.add(T(lathe([(.88, 0), (.7, .35), (.3, .5), (0, .52)], 14), (2.4, y + .8, .4)), S('glass', base=.75, jit=0))
    P.add(T(rbox((.6, .14, .4), .04, 1), (2.4, y + .5, -.45)), S('dark', base=.4, jit=.01))
    P.add(T(rbox((1.6, .1, 1.2), .03, 1), (1.6, y + .05, -.9), 12), S('wall', base=.94, jit=0))                     # notebook
    P.add(T(rbox((.04, .12, 1.2), .02, 1), (1.6, y + .1, -.9), 12), S('teal', base=.5, jit=.01))
    lb = V3((-3.4, y, .9))                                                                                    # angle lamp
    P.add(T(lathe([(.5, 0), (.5, .15), (0, .2)], 10), tuple(lb)), S('teal', base=.5, jit=.01))
    P.add(tube([lb + V3((0, .2, 0)), lb + V3((.4, 2.2, .2)), lb + V3((1.6, 2.8, -.2))], .09, sides=5), S('steel', base=.55, jit=.01))
    P.add(T(ball(.18, 6, 3), tuple(lb + V3((.4, 2.2, .2)))), S('teal', base=.5, jit=.01))
    sh = lb + V3((1.7, 2.6, -.3))
    P.add(T(lathe([(.12, .5), (.55, .02), (.6, -.08), (.62, -.08), (.16, .55)], 10), tuple(sh)), S('teal', base=.58, jit=.01))
    P.gadd(T(lathe([(0, 0), (.45, .02), (0, .1)], 10), tuple(sh + V3((0, -.06, 0)))), 'lamp')
    return P

def microscope_bench():
    """small lab table with a modelled microscope (base, curved arm, stage with clips, turret + 3 objectives, angled
    eyepiece tube, focus knobs) and a slide box"""
    P = Prop('MicroscopeBench')
    lab_table(P, 4.6, 3.0, 3.6)
    y = 3.75; c = V3((-.3, y, 0))
    P.add(T(rbox((1.4, .3, 1.8), .14, 2), tuple(c + V3((0, .15, .1)))), S('wall', base=.86, jit=.01))
    arm = [c + V3((0, .3, .7)), c + V3((0, 1.2, .8)), c + V3((0, 2.2, .55)), c + V3((0, 2.7, .1))]
    P.add(tube(arm, [.32, .3, .28, .26], sides=8, flat=(.7, 1.0)), S('wall', base=.84, jit=.01))
    P.add(T(rbox((1.3, .14, 1.1), .04, 1), tuple(c + V3((0, 1.15, -.1)))), S('dark', base=.35, jit=.01))
    for sx in (-1, 1):
        P.add(T(rbox((.1, .06, .5), .02, 1), tuple(c + V3((sx * .35, 1.25, -.2)))), S('steel', base=.6, jit=.01))
        P.add(T(T(cyl(.24, .14, 10), (0, -.07, 0), 0, 0, 90), tuple(c + V3((sx * .3, 1.0, .7)))), S('steel', base=.5, jit=.01))
    P.add(T(lathe([(.38, 0), (.4, .15), (.2, .3), (0, .3)], 10), tuple(c + V3((0, 2.3, -.25)))), S('steel', base=.55, jit=.01))
    for k in range(3):
        a = k * math.tau / 3
        P.add(T(lathe([(.08, 0), (.1, .45), (0, .45)], 6), tuple(c + V3((math.cos(a) * .2, 1.85, -.25 + math.sin(a) * .2)))), S('steel', base=.62, jit=.01))
    P.add(tube([c + V3((0, 2.55, -.15)), c + V3((0, 3.25, .45))], [.18, .14], sides=8), S('wall', base=.82, jit=.01))
    P.add(T(lathe([(.16, 0), (.18, .25), (0, .25)], 8), tuple(c + V3((0, 3.2, .42)))), S('dark', base=.35, jit=.01))
    P.add(T(rbox((1.2, .4, .8), .08), (1.4, y + .2, .3), -10), S('sky', base=.55, jit=.01))
    P.add(T(rbox((1.0, .06, .6), .02, 1), (1.4, y + .43, .3), -10), S('wall', base=.9, jit=0))
    return P

def whiteboard():
    """rolling whiteboard: two T legs on casters, aluminium frame, blank board, marker tray with markers + eraser,
    two magnets holding a blank note"""
    P = Prop('Whiteboard')
    W, H = 10.0, 5.6; y0 = 2.6
    for sx in (-1, 1):
        x = sx * (W / 2 + .2)
        P.add(T(rbox((.4, y0 + H + .4, .4), .1), (x, (y0 + H + .4) / 2 + .4, 0)), S('steel', base=.6, jit=.01))
        P.add(T(rbox((.5, .4, 3.2), .15), (x, .7, 0)), S('steel', base=.5, jit=.01))
        for sz in (-1, 1):
            P.add(T(T(cyl(.3, .25, 8), (0, -.12, 0), 0, 0, 90), (x, .3, sz * 1.4)), S('dark', base=.35, jit=.01))
            P.add(T(rbox((.2, .3, .3), .05), (x, .65, sz * 1.4)), S('steel', base=.45, jit=.01))
    P.add(T(rbox((W, H, .2), .05), (0, y0 + H / 2, 0)), S('wall', base=.95, jit=0))
    for (a, b) in (((-W / 2, y0), (W / 2, y0)), ((-W / 2, y0 + H), (W / 2, y0 + H)), ((-W / 2, y0), (-W / 2, y0 + H)), ((W / 2, y0), (W / 2, y0 + H))):
        P.add(bar((a[0], a[1], 0), (b[0], b[1], 0), .4, .34, .08), S('steel', base=.68, jit=.01))
    P.add(T(rbox((W - 1.0, .16, .6), .05), (0, y0 - .05, -.35)), S('steel', base=.6, jit=.01))
    for k, c in enumerate(('teal', 'coral', 'sky')):
        P.add(T(T(cyl(.08, .6, 6), (0, -.3, 0), 0, 0, 90), (-1.7 + k * .4, y0 + .14, -.4)), S(c, base=.55, jit=.01))
    P.add(T(rbox((.8, .3, .35), .06), (2.0, y0 + .22, -.4)), S('dark', base=.45, jit=.01))
    P.add(T(rbox((1.6, 1.6, .04), .02, 1), (3.0, y0 + 3.6, -.13), 0, 0, 4), S('gold', base=.78, jit=0))
    for x, c in ((2.4, 'coral'), (3.6, 'mint')):
        P.add(T(T(cyl(.16, .12, 10), (0, 0, 0), 0, -90), (x, y0 + 4.3, -.15)), S(c, base=.6, jit=.01))
    return P

def starter_table():
    """starter-capsule table: round white pedestal table with a teal apron, three cushion pedestals under glass domes,
    each holding a Gem Pod (mint, coral, sky), small blank placard stands in front, a gold trim ring"""
    P = Prop('StarterTable')
    P.add(lathe([(2.6, 0), (2.6, .3), (1.4, .6), (1.0, 1.0), (1.0, 3.0), (1.6, 3.3), (0, 3.3)], 24), S('wall', base=.84, up=.12, jit=.01))
    P.add(T(torus(1.05, .12, 20, 4), (0, 2.0, 0)), S('teal', base=.5, jit=.01))
    P.add(T(lathe([(5.2, 0), (5.3, .2), (5.2, .5), (0, .5)], 40), (0, 3.3, 0)), S('cream', base=.76, up=.12, jit=.01))
    P.add(T(lathe([(5.32, 0), (5.32, .55), (5.0, .55), (5.0, 0)], 40), (0, 2.85, 0)), S('teal', base=.55, jit=.01))
    P.add(T(torus(5.3, .07, 40, 4), (0, 3.82, 0)), S('gold', base=.6, jit=.01))
    for k, tier in enumerate(('mint', 'coral', 'sky')):
        a = math.radians(-90 + (k - 1) * 50); r = 2.9
        x, z = math.cos(a) * r, math.sin(a) * r
        P.add(T(lathe([(1.0, 0), (1.0, .3), (.8, .5), (.8, .7), (0, .7)], 16), (x, 3.8, z)), S('steel', base=.55, up=.12, jit=.01))
        P.add(T(lathe([(.75, 0), (.8, .15), (.6, .35), (0, .4)], 12), (x, 4.45, z)), S(tier, base=.5, up=.15, jit=.01))
        capsule(P, (x, 4.75, z), tier, 1.25, -math.degrees(a) - 90, 0, 8, True, 70.0 if k == 1 else 0.0)
        P.add(T(lathe([(.95, 0)] + [(math.cos(math.pi / 2 * j / 6) * 1.05, math.sin(math.pi / 2 * j / 6) * 2.3 + .3) for j in range(1, 7)], 16), (x, 4.45, z)), S('glass', base=.84, jit=0))
        px, pz = math.cos(a) * 4.6, math.sin(a) * 4.6
        P.add(T(T(rbox((1.0, .6, .08), .03, 1), (0, 0, 0), 0, -25), (px, 4.15, pz), -math.degrees(a) - 90), S('wall', base=.94, jit=0))
        P.add(T(T(rbox((1.06, .1, .12), .03, 1), (0, -.3, 0), 0, -25), (px, 4.15, pz), -math.degrees(a) - 90), S(tier, base=.55, jit=.01))
    return P

def lab_archway():
    """the portal between the hall and the lab wing (fits an 18 wide x 17 tall opening): two teal pilasters with white
    caps, a white elliptical arch with a teal soffit band, the Bloom Paw badge at the crown, glow strip under the arch"""
    P = Prop('LabArchway')
    hw = 9.0; spring = 11.5; rise = 5.0; D = 2.6
    for sx in (-1, 1):
        P.add(T(rbox((1.6, spring, D), .3, 2), (sx * (hw + .3), spring / 2, 0)), S('teal', base=.5, up=.1, jit=.01))
        P.add(T(rbox((2.2, .8, D + .4), .2, 2), (sx * (hw + .3), spring + .2, 0)), S('wall', base=.88, jit=.01))
        P.add(T(rbox((2.2, .8, D + .4), .2, 2), (sx * (hw + .3), .3, 0)), S('wall', base=.84, jit=.01))
    prof = [(math.cos(math.pi * k / 16) * (hw + 1.1), math.sin(math.pi * k / 16) * (rise + 1.1)) for k in range(17)]
    inner = [(math.cos(math.pi * k / 16) * (hw - .3), math.sin(math.pi * k / 16) * (rise - .3)) for k in range(17)]
    P.add(upright(prof + inner[::-1], D, (0, spring + .6, D / 2)), S('wall', base=.86, up=.1, jit=.01))
    P.add(upright(inner + [(x * .97, y * .94) for x, y in inner[::-1]], D + .2, (0, spring + .6, D / 2 + .1)), S('teal', base=.55, jit=.01))
    P.gadd(tube([V3((math.cos(math.pi * k / 20) * (hw - .5), spring + .6 + math.sin(math.pi * k / 20) * (rise - .6), -D / 2 - .05)) for k in range(21)], .12, sides=5), 'heal')
    emblem_badge(P, (0, spring + .6 + rise + 1.3, -D / 2 - .05), 0, 1.7)
    return P

def pendant_lamp(drop=6.0, col='mint'):
    """pendant lamp hung from the ceiling (origin = the ceiling point, hangs DOWN to -drop): canopy, cord, bell shade
    with a white inner rim and a glowing bulb disc"""
    P = Prop('PendantLamp%s' % col[0].upper())
    P.add(lathe([(.5, -.35), (.5, -.15), (.15, 0), (0, 0)], 10), S('wall', base=.86, jit=.01))
    P.add(T(cyl(.05, drop - 1.4, 4), (0, -drop + 1.2, 0)), S('dark', base=.35, jit=.01))
    y = -drop
    P.add(T(lathe([(1.5, 0), (1.45, .25), (.9, .9), (.35, 1.4), (.2, 1.55), (0, 1.55)], 16), (0, y, 0)), S(col, base=.6, up=.15, jit=.01))
    P.add(T(torus(1.45, .08, 16, 4), (0, y + .05, 0)), S('wall', base=.92, jit=0))
    P.gadd(T(lathe([(0, 0), (1.2, .05), (0, .5)], 12), (0, y + .05, 0)), 'lamp')
    return P

def rest_nook():
    """little rest area for recovering creatures: oval rug, two round cushion beds (teal + coral) with pillows, a low
    round side table with a water bowl, a treat jar and a tiny plant"""
    P = Prop('RestNook')
    rug = [(math.cos(t) * 7.0, math.sin(t) * 4.6) for t in [k * math.tau / 28 for k in range(28)]]
    P.add(T(ngon_prism(rug, 0, .12), (0, .02, 0)), S('cream', base=.62, up=.05, jit=.01))
    P.add(T(T(torus(5.9, .1, 28, 3), (0, 0, 0), s=(1, 1, .72)), (0, .14, 0)), S('mint', base=.55, jit=.01))
    for sx, col in ((-1, 'teal'), (1, 'coral')):
        c = (sx * 3.6, .12, -.3)
        P.add(T(lathe([(1.9, 0), (2.1, .3), (2.15, .7), (1.95, .95), (1.55, .9), (1.4, .55), (0, .45)], 18), c), S(col, base=.55, up=.15, jit=.01))
        P.add(T(lathe([(1.4, 0), (1.35, .2), (0, .25)], 16), (c[0], .55, c[2])), S('cream', base=.82, jit=.01))
        P.add(T(rbox((1.1, .45, .7), .22, 2), (c[0] - sx * .4, .95, c[2] + .7), sx * 20), S('wall', base=.9, jit=.01))
    P.add(lathe([(1.0, 0), (1.0, .1), (.25, .2), (.25, 1.6), (1.2, 1.7), (1.2, 1.9), (0, 1.9)], 16), S('wall', base=.86, jit=.01))
    P.add(T(lathe([(.45, 0), (.55, .25), (.42, .25), (0, .12)], 12), (-.35, 1.9, .1)), S('sky', base=.55, jit=.01))
    P.add(T(lathe([(.42, .2), (0, .22)], 12), (-.35, 1.9, .1)), S('glass', base=.86, jit=0))
    P.add(T(lathe([(0, 0), (.3, .02), (.32, .55), (.25, .62), (0, .62)], 8), (.45, 1.9, -.2)), S('glass', base=.8, jit=0))
    P.add(T(lathe([(.3, 0), (.34, .12), (0, .14)], 8), (.45, 2.52, -.2)), S('gold', base=.6, jit=.01))
    for k in range(4):
        P.add(T(ball(.09, 6, 3), (.45 + (k % 2) * .12 - .06, 2.0 + k * .1, -.2)), S('berry', base=.6, jit=.01))
    pot_plant(P, (.3, 1.9, .6), .45)
    return P

# ------------------------------------------------------------------ architecture (Roblox space, map-centred)
ROT_R = 44.0; ROT_T = 1.6; WALL_H = 22.0          # rotunda: inner wall radius, thickness, wall height above FL
DOOR_W, DOOR_H = 14.0, 13.0                         # south entrance
ARCH_W, ARCH_H = 18.0, 17.5                         # north opening to the lab wing
WING_HW, WING_T, WING_H = 24.0, 1.4, 20.0           # lab wing: inner half width, wall thickness, wall height
WING_Z0, WING_ZC = -36.0, -92.0                     # wing side walls from z0 to zc, then a half-round end (radius WING_HW)
GLAZE = 32.0                                        # glass facade = +-GLAZE deg round south
def adeg(x, r): return math.degrees(math.asin(x / r))

def arc_wall(P, r0, r1, a0, a1, y0, y1, holes, step=5.0, col='wall', base=.84, band=None):
    """curved wall from angle a0..a1 split into cells; holes = [(ha0, ha1, hy0, hy1)] skipped"""
    As = sorted({a0, a1} | {h[0] for h in holes if a0 < h[0] < a1} | {h[1] for h in holes if a0 < h[1] < a1})
    Ys = sorted({y0, y1} | {h[2] for h in holes if y0 < h[2] < y1} | {h[3] for h in holes if y0 < h[3] < y1})
    for aa, ab in zip(As, As[1:]):
        for ya, yb in zip(Ys, Ys[1:]):
            am, ym = (aa + ab) / 2, (ya + yb) / 2
            if any(h[0] < am < h[1] and h[2] < ym < h[3] for h in holes): continue
            n = max(1, int(math.ceil((ab - aa) / step)))
            P.add(ring_seg(r0, r1, ya, yb, aa, ab, n), S(col, base=base, up=.08, jit=.008))

def rotunda():
    """HERO shell: the care hall. Ring wall (inner r 44) with a curved glass facade round the south entrance (steel
    mullions, transom, cream base course), the door gap, the 18 wide opening north to the lab, tall slot windows round the
    sides with glass + sills, teal plinth + white pilasters + mint cornice outside, mint dado + cream rail inside"""
    P = Prop('Rotunda')
    r0, r1 = ROT_R, ROT_R + ROT_T; y0, y1 = FL - 1.4, FL + WALL_H
    da = adeg(DOOR_W / 2, r0); na = adeg(ARCH_W / 2 + 1.15, r0)               # opening fits the LabArchway pilasters
    slots = list(WINDOWS)
    holes = [(90 - GLAZE, 90 + GLAZE, FL + 1.2, FL + 16.0), (90 - da, 90 + da, y0, FL + DOOR_H), (270 - na, 270 + na, y0, FL + ARCH_H)]
    holes += [(a - 2.2, a + 2.2, FL + 6.0, FL + 16.5) for a in slots]
    arc_wall(P, r0, r1, 0, 360, y0, y1, holes, 4.0)
    # glass facade: panes in the south opening (not in the door gap), mullions, transom over the door
    for a0_, a1_ in ((90 - GLAZE, 90 - da), (90 + da, 90 + GLAZE)):
        n = max(1, round((a1_ - a0_) / 5.0))
        for k in range(n + 1):
            a = lerp(a0_, a1_, k / n)
            P.add(ring_seg(r0 + .2, r1 - .2, FL + 1.2, FL + 16.0, a - .45, a + .45, 1), S('steel', base=.6, up=.1, jit=.01))
        P.add(ring_seg(r0 + .65, r0 + .85, FL + 1.2, FL + 16.0, a0_, a1_, n * 2), S('glass', base=.8, jit=0))
        P.add(ring_seg(r0 - .1, r1 + .1, FL + 8.4, FL + 8.9, a0_, a1_, n * 2), S('steel', base=.62, jit=.01))
    P.add(ring_seg(r0 + .65, r0 + .85, FL + DOOR_H + .6, FL + 16.0, 90 - da, 90 + da, 4), S('glass', base=.8, jit=0))
    P.add(ring_seg(r0 - .2, r1 + .2, FL + DOOR_H, FL + DOOR_H + .6, 90 - da - .5, 90 + da + .5, 4), S('steel', base=.55, jit=.01))
    P.add(ring_seg(r0 - .25, r1 + .25, FL + 15.8, FL + 16.4, 90 - GLAZE, 90 + GLAZE, 16), S('steel', base=.58, jit=.01))
    for a in (90 - da, 90 + da):
        P.add(ring_seg(r0 - .3, r1 + .3, FL - .2, FL + DOOR_H + .6, a - .9, a + .9, 1), S('steel', base=.5, up=.1, jit=.01))
    # slot windows: glass set back + sill + steel frame
    for a in slots:
        P.add(ring_seg(r0 + .6, r0 + .8, FL + 6.0, FL + 16.5, a - 2.2, a + 2.2, 2), S('glass', base=.8, jit=0))
        P.add(ring_seg(r0 - .35, r1 + .35, FL + 5.7, FL + 6.0, a - 2.6, a + 2.6, 2), S('cream', base=.78, up=.1, jit=.01))
        P.add(ring_seg(r0 - .1, r1 + .1, FL + 16.5, FL + 16.8, a - 2.4, a + 2.4, 2), S('mint', base=.55, jit=.01))
        P.add(ring_seg(r0 + .2, r1 - .2, FL + 6.0, FL + 16.5, a - .15, a + .15, 1), S('steel', base=.6, jit=.01))
    # outside: teal plinth, pilasters, mint cornice; inside: mint dado + cream rail (skipping openings)
    def ring_skip(rr0, rr1, ya, yb, col, base, gaps, step=4.0):
        As = [0.0]
        segs = []
        cur = 0.0
        for g0, g1 in sorted(gaps):
            segs.append((cur, g0)); cur = g1
        segs.append((cur, 360.0))
        for s0, s1 in segs:
            if s1 - s0 > .5: P.add(ring_seg(rr0, rr1, ya, yb, s0, s1, max(1, int((s1 - s0) / step))), S(col, base=base, up=.1, jit=.01))
    door_gap = [(90 - da - .9, 90 + da + .9), (270 - na, 270 + na)]
    ring_skip(r1, r1 + .5, -.4, FL + 1.4, 'teal', .45, door_gap)
    ring_skip(r1 - .1, r1 + .9, FL + WALL_H - 2.0, FL + WALL_H - .6, 'mint', .55, [(270 - na, 270 + na)] if False else [])
    ring_skip(r1 - .1, r1 + .6, FL + WALL_H - .6, FL + WALL_H, 'wall', .9, [])
    ring_skip(r0 - .35, r0, FL - .1, FL + 3.0, 'mint', .52, door_gap + [(90 - GLAZE, 90 + GLAZE)])
    ring_skip(r0 - .55, r0, FL + 3.0, FL + 3.4, 'cream', .78, door_gap + [(90 - GLAZE, 90 + GLAZE)])
    ring_skip(r0 - .5, r0, FL + WALL_H - 1.6, FL + WALL_H, 'cream', .72, [])
    for a in range(9, 360, 18):
        if 90 - GLAZE - 2 < a < 90 + GLAZE + 2 or 270 - na - 3 < a < 270 + na + 3 or 247 < a < 293: continue
        P.add(ring_seg(r1, r1 + .7, FL + 1.4, FL + WALL_H - 2.0, a - 1.3, a + 1.3, 1), S('wall', base=.92, up=.1, jit=.01))
    merge_prop(P, rotunda_roof())                                              # the roof rests on these walls: one prop
    return P

def lathe_open(profile, n=24):
    """lathe without the flat end caps (rings stay open: roofs, eaves, collars over openings)"""
    bm = lathe(profile, n)
    caps = [f for f in bm.faces if len(f.verts) > 4]
    bmesh.ops.delete(bm, geom=caps, context='FACES_ONLY')
    return bm

def rotunda_roof():
    """rotunda roof (no collision, hide it for cutaways): mint shallow dome with white ribs, eave lip, cream ceiling
    underneath with a teal coffer ring, glass oculus dome with steel ribs, a crown ring with the Bloom Paw finial"""
    P = Prop('RotundaRoof')
    yb = FL + WALL_H; ro = ROT_R + ROT_T + 2.0; rk = 13.0; yk = yb + 9.0
    prof = [(ro, yb - .4), (ro + .1, yb + .3)] + [(lerp(ro, rk, t), yb + .3 + (yk - yb - .3) * math.sin(t * math.pi / 2) ** 1.4) for t in [k / 10 for k in range(1, 11)]]
    outer = lathe_open([(rk, yk)] + prof[::-1], 48)
    P.add(outer, S('mint', base=.5, up=.18, jit=.012))
    inner = lathe_open([(rk - .2, yk - 1.2)] + [(r - .1, y - 1.4) for r, y in prof[::-1][:-2]] + [(ROT_R - .3, yb - .2)], 48)
    for f in inner.faces:                                                       # ceiling skin faces DOWN into the hall
        f.normal_update()
        if f.normal.y > 0: f.normal_flip()
    P.add(inner, S('cream', base=.74, up=-.1, jit=.01))
    P.add(lathe_open([(ro + .3, yb - .6), (ro + .4, yb + .1), (ro - .2, yb + .2), (ROT_R - .2, yb - .1), (ROT_R - .2, yb - .6)], 48), S('wall', base=.9, jit=.01))
    for k in range(16):                                                        # ribs
        a = k * math.tau / 16
        pts = [V3((math.cos(a) * r, y + .15, math.sin(a) * r)) for r, y in prof[1:]]
        P.add(tube(pts, .38, sides=5, flat=(1.0, .6)), S('wall', base=.9, up=.1, jit=.01))
    P.add(T(lathe_open([(rk + 1.0, 0), (rk + 1.0, 1.0), (rk - .2, 1.2), (rk - .2, -1.2), (rk + .8, -1.4)], 40), (0, yk, 0)), S('wall', base=.9, up=.1, jit=.01))
    P.add(T(torus(rk + 1.05, .3, 40, 6), (0, yk + .5, 0)), S('teal', base=.5, jit=.01))
    P.add(T(lathe_open([(rk + 2.6, 0), (rk + 2.6, .6), (rk - .3, .6), (rk - .3, 0)], 40), (0, yk - 2.4, 0)), S('teal', base=.5, jit=.01))   # coffer ring under
    gd = lathe_open([(rk - .1, 0)] + [(math.cos(math.pi / 2 * j / 8) * (rk - .1), math.sin(math.pi / 2 * j / 8) * 6.5) for j in range(1, 8)] + [(0, 6.5)], 32)
    P.add(T(gd, (0, yk + 1.0, 0)), S('glass', base=.82, jit=0))
    for k in range(8):
        a = k * math.tau / 8
        pts = [V3((math.cos(a) * math.cos(math.pi / 2 * j / 8) * rk, yk + 1.05 + math.sin(math.pi / 2 * j / 8) * 6.6, math.sin(a) * math.cos(math.pi / 2 * j / 8) * rk)) for j in range(9)]
        P.add(tube(pts, .22, sides=5), S('steel', base=.62, jit=.01))
    P.add(T(torus(rk * .72, .18, 24, 5), (0, yk + 5.6, 0)), S('steel', base=.6, jit=.01))
    P.add(T(lathe([(1.4, 0), (1.4, .5), (.9, .9), (0, .9)], 16), (0, yk + 7.4, 0)), S('wall', base=.9, jit=.01))
    P.gadd(T(lathe([(0, 0), (.8, .3), (.9, .9), (.5, 1.5), (0, 1.7)], 12), (0, yk + 8.2, 0)), 'heal')
    return P

def wing_outline(n_end=16):
    """plan polygon (x, z) of the lab wing interior: from (-hw, z0) to (-hw, zc), half round to (hw, zc), back to z0"""
    hw = WING_HW
    pts = [(-hw, WING_Z0), (-hw, WING_ZC)]
    for k in range(1, n_end):
        a = math.pi - math.pi * k / n_end
        pts.append((math.cos(a) * hw, WING_ZC - math.sin(a) * hw))
    pts += [(hw, WING_ZC), (hw, WING_Z0)]
    return pts

def lab_wing():
    """HERO shell: research wing walls: straight sides + half-round north end, tall windows with glass + sills, teal
    plinth, white pilasters, mint cornice outside; mint dado inside. Joins the rotunda at its north side"""
    P = Prop('LabWing')
    hw, t = WING_HW, WING_T; y0, y1 = FL - 1.4, FL + WING_H
    L = WING_Z0 - WING_ZC                                                        # side wall length
    win = [(z, z + 5.0) for z in (-46.0, -58.0, -70.0, -82.0)]
    for sx in (-1, 1):
        x = sx * (hw + t / 2)
        zs = sorted({WING_Z0, WING_ZC} | {w[0] for w in win} | {w[1] for w in win})
        for za, zb in zip(zs, zs[1:]):
            zm = (za + zb) / 2; isw = any(w[0] < zm < w[1] for w in win)
            for ya, yb in ([(y0, FL + 5.0), (FL + 16.0, y1)] if isw else [(y0, y1)]):
                P.add(T(box((t, yb - ya, abs(zb - za))), (x, (ya + yb) / 2, zm)), S('wall', base=.84, up=.08, jit=.008))
            if isw:
                P.add(T(box((.2, 11.0, abs(zb - za))), (x + sx * .1, FL + 10.5, zm)), S('glass', base=.8, jit=0))
                P.add(T(rbox((t + .7, .3, abs(zb - za) + .6), .08), (x, FL + 4.85, zm)), S('cream', base=.78, up=.1, jit=.01))
                P.add(T(box((t + .2, .3, abs(zb - za) + .4)), (x, FL + 16.15, zm)), S('mint', base=.55, jit=.01))
                P.add(T(box((.3, 11.0, .3)), (x, FL + 10.5, zm)), S('steel', base=.6, jit=.01))
        P.add(T(box((.5, FL + 1.8, L)), (x + sx * (t / 2 + .25), (FL + 1.8) / 2 - .4, (WING_Z0 + WING_ZC) / 2)), S('teal', base=.45, jit=.01))
        P.add(T(box((1.0, 1.4, L)), (x + sx * (t / 2), FL + WING_H - 1.3, (WING_Z0 + WING_ZC) / 2)), S('mint', base=.55, jit=.01))
        P.add(T(box((.35, 3.0, L)), (x - sx * (t / 2 + .17), FL + 1.5, (WING_Z0 + WING_ZC) / 2)), S('mint', base=.52, jit=.01))
        for z in (-40.0, -52.0, -64.0, -76.0, -88.0):
            P.add(T(rbox((.7, WING_H - 3.4, 2.4), .15), (x + sx * (t / 2 + .3), FL + (WING_H - 3.4) / 2 + .6, z + 1.5 if z < -40 else z)), S('wall', base=.92, up=.1, jit=.01))
    # half-round end: centre (0, zc), angles 180..360 (north)
    c = (0, 0, WING_ZC)
    holes = [(225 - 4, 225 + 4, FL + 5.0, FL + 16.0), (315 - 4, 315 + 4, FL + 5.0, FL + 16.0)]
    end = Prop('_e')
    arc_wall(end, hw, hw + t, 180, 360, y0, y1, holes, 6.0)
    for a in (225, 315):
        end.add(ring_seg(hw + .5, hw + .7, FL + 5.0, FL + 16.0, a - 4, a + 4, 2), S('glass', base=.8, jit=0))
        end.add(ring_seg(hw - .35, hw + t + .35, FL + 4.7, FL + 5.0, a - 4.5, a + 4.5, 2), S('cream', base=.78, up=.1, jit=.01))
    end.add(ring_seg(hw + t, hw + t + .5, -.4, FL + 1.4, 180, 360, 16), S('teal', base=.45, jit=.01))
    end.add(ring_seg(hw + t - .1, hw + t + .9, FL + WING_H - 2.0, FL + WING_H - .6, 180, 360, 16), S('mint', base=.55, jit=.01))
    end.add(ring_seg(hw - .35, hw, FL - .1, FL + 3.0, 180, 360, 16), S('mint', base=.52, jit=.01))
    merge_prop(P, end, c)
    return P

def wing_roof():
    """lab wing roof (no collision; hide it for cutaways): flat white slab built in 1-stud rows round its openings (two
    raised glass skylight lanterns on the axis, a glass dome over the round end) with a cream underside, mint parapets"""
    P = Prop('WingRoof')
    yb = FL + WING_H; hw = WING_HW + WING_T + .6; zt = WING_Z0 + 2.0; zc = WING_ZC; DR = 12.0
    sky = [(-58.0, -46.0), (-74.0, -62.0)]; sw = 6.0
    z = zt
    while z > zc - hw + .01:
        za, zb = z, max(z - 1.0, zc - hw); zm = (za + zb) / 2
        lim = hw if zm > zc else math.sqrt(max(0.0, hw * hw - (zm - zc) ** 2))
        cut = 0.0
        if any(a < zm < b for a, b in sky): cut = sw
        dz = abs(zm - zc)
        if dz < DR: cut = max(cut, math.sqrt(DR * DR - dz * dz))
        for x0, x1 in ((-lim, -cut), (cut, lim)) if cut > 0 else ((-lim, lim),):
            if x1 - x0 > .05:
                P.add(T(box((x1 - x0, 1.0, za - zb)), ((x0 + x1) / 2, yb - .5, zm)), lambda f: [(PAL.u('wall' if f.normal.y > -.5 else 'cream'), .86 if f.normal.y > -.5 else .74)] * len(f.loops))
        z = zb
    for za, zb in sky:                                                         # skylight lanterns
        zm = (za + zb) / 2; L = zb - za
        for sx in (-1, 1):
            P.add(T(T(box((.2, 4.2, L)), (0, 0, 0), 0, 0, sx * 35), (sx * 2.0, yb + 1.4, zm)), S('glass', base=.8, jit=0))
            P.add(T(rbox((.6, 1.0, L + .6), .1), (sx * sw, yb + .4, zm)), S('steel', base=.55, jit=.01))
        P.add(T(rbox((.5, .5, L + .4), .1), (0, yb + 3.2, zm)), S('steel', base=.6, jit=.01))
        for k in range(5):
            zz = za + L * k / 4
            for sx in (-1, 1):
                P.add(bar((sx * sw, yb + .8, zz), (0, yb + 3.2, zz), .25, .25, .04), S('steel', base=.58, jit=.01))
        for zz in (za, zb):
            P.add(upright([(-sw, 0), (sw, 0), (0, 2.9)], .2, (0, yb + .4, zz + .1)), S('glass', base=.8, jit=0))
    P.add(T(ring_seg(DR - .4, DR + 1.2, -1.3, .5, 0, 360, 32), (0, yb, zc)), S('teal', base=.5, jit=.01))
    hd = lathe([(DR, 0)] + [(math.cos(math.pi / 2 * j / 6) * DR, math.sin(math.pi / 2 * j / 6) * 6.5) for j in range(1, 6)] + [(0, 6.5)], 24)
    P.add(T(hd, (0, yb + .5, zc)), S('glass', base=.82, jit=0))
    for k in range(6):
        a = k * math.tau / 6
        pts = [V3((math.cos(a) * math.cos(math.pi / 2 * j / 6) * (DR + .05), yb + .5 + math.sin(math.pi / 2 * j / 6) * 6.55, zc + math.sin(a) * math.cos(math.pi / 2 * j / 6) * (DR + .05))) for j in range(7)]
        P.add(tube(pts, .2, sides=5), S('steel', base=.62, jit=.01))
    P.add(T(lathe([(.9, 0), (.9, .4), (0, .9)], 10), (0, yb + 7.0, zc)), S('steel', base=.6, jit=.01))
    P.add(T(lathe([(hw, -.4), (hw + .1, .9), (hw - .8, .9), (hw - .8, 0)], 32), (0, yb, zc)), S('mint', base=.5, jit=.01))
    for sx in (-1, 1):                                                         # parapets along the sides
        P.add(T(rbox((.8, 1.3, zt - zc), .12), (sx * (hw - .4), yb + .25, (zt + zc) / 2)), S('mint', base=.5, jit=.01))
    return P

def sliding_doors(open_frac=.6):
    """automatic sliding doors for the south entrance (14 wide x 13): steel header with a sensor + blue status glow,
    two glass leaves with steel stiles and push bars, slid open into the side panes, floor guide rails"""
    P = Prop('SlidingDoors')
    W, H = DOOR_W, DOOR_H; lw = W / 2
    P.add(T(rbox((W + 1.0, 1.4, 1.4), .2), (0, H + .3, 0)), S('steel', base=.55, up=.1, jit=.01))
    P.add(T(rbox((1.4, .5, .6), .15), (0, H - .6, -.6)), S('wall', base=.86, jit=.01))
    P.gadd(T(rbox((.8, .14, .1), .04, 1), (0, H - .62, -.92)), 'screen')
    off = lw * open_frac
    for sx in (-1, 1):
        cx = sx * (lw / 2 + off); z = sx * .15
        P.add(T(box((lw - .6, H - .7, .15)), (cx, H / 2, z)), S('glass', base=.82, jit=0))
        for ex in (-1, 1):
            P.add(T(rbox((.4, H - .4, .32), .08), (cx + ex * (lw / 2 - .2), H / 2, z)), S('steel', base=.6, jit=.01))
        for ey in (.35, H - .5):
            P.add(T(rbox((lw, .4, .32), .08), (cx, ey, z)), S('steel', base=.6, jit=.01))
        P.add(T(T(cyl(.12, 4.0, 6), (0, -2.0, 0)), (cx - sx * (lw / 2 - .9), H * .45, z - .4)), S('teal', base=.55, jit=.01))
    P.add(T(rbox((W, .1, .7), .03, 1), (0, .05, 0)), S('dark', base=.4, jit=.01))
    return P

def entrance_canopy():
    """curved canopy over the entrance (front = -Z = outward when placed facing south): white slab with a teal fascia,
    soffit glow strip, two slim columns, and the big Bloom Paw badge standing on top facing out"""
    P = Prop('EntranceCanopy')
    R0, R1 = 2.0, 11.0; a0, a1 = 270 - 70, 270 + 70; y = DOOR_H + 2.4
    P.add(ring_seg(R0, R1, y, y + 1.0, a0, a1, 24), S('wall', base=.88, up=.12, jit=.01))
    P.add(ring_seg(R1 - .2, R1 + .3, y - .3, y + 1.3, a0, a1, 24), S('teal', base=.5, jit=.01))
    P.add(ring_seg(R1 - .9, R1 - .6, y - .14, y, a0 + 2, a1 - 2, 24), S('wall', base=.95, jit=0))
    pts = [V3((math.cos(math.radians(a)) * (R1 - 1.4), y - .12, math.sin(math.radians(a)) * (R1 - 1.4))) for a in range(int(a0) + 4, int(a1) - 3, 8)]
    P.gadd(tube(pts, .12, sides=5), 'lamp')
    for sx in (-1, 1):
        a = math.radians(270 + sx * 40); x, z = math.cos(a) * (R1 - 1.8), math.sin(a) * (R1 - 1.8)
        P.add(T(lathe([(.9, 0), (.9, .5), (.5, .8), (.45, y - .6), (.7, y - .3), (.7, y), (0, y)], 12), (x, 0, z)), S('wall', base=.88, jit=.01))
        P.add(T(torus(.52, .1, 12, 4), (x, 3.0, z)), S('mint', base=.55, jit=.01))
    P.add(T(rbox((7.0, 1.0, 1.6), .3), (0, y + 1.4, -7.0)), S('wall', base=.88, jit=.01))
    emblem_badge(P, (0, y + 5.0, -7.0), 0, 3.4, ring='teal')
    P.add(T(rbox((3.0, 1.8, .9), .2), (0, y + 1.8, -6.9)), S('teal', base=.5, jit=.01))
    return P

# ------------------------------------------------------------------ exterior + decor
def leaf_ball(P, c, r, seed, col='leaf', n=30, sq=.85, base=.5):
    """chunky stylised leaf mass: a blob + a few smaller blobs around (canopy, bush)"""
    rng = random.Random(seed)
    P.add(T(blob(r, seed, n=n, sq=sq), c), S(col, base=base, up=.22, jit=.05))
    for k in range(4):
        a = rng.uniform(0, math.tau); d = r * .7
        P.add(T(blob(r * rng.uniform(.5, .65), seed * 7 + k, n=20, sq=sq), (c[0] + math.cos(a) * d, c[1] + rng.uniform(-.2, .35) * r, c[2] + math.sin(a) * d)), S(col, base=base + .04, up=.22, jit=.05))

def tree(seed=1, h=16.0):
    """rounded park tree: flared birch trunk splitting into two boughs, three-lobed chunky canopy, root flare"""
    P = Prop('Tree%d' % seed); rng = random.Random(seed)
    trunk = [V3((0, -1.2, 0)), V3((0, h * .25, 0)), V3((.3, h * .45, .2))]
    P.add(tube(trunk, [1.1, .75, .6], sides=8), S('wood', base=.42, up=.1, jit=.03))
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(0, .5)
        P.add(tube([V3((0, .6, 0)), V3((math.cos(a) * 1.5, -.1, math.sin(a) * 1.5)), V3((math.cos(a) * 2.1, -.6, math.sin(a) * 2.1))], [.45, .3, .1], sides=5), S('wood', base=.38, jit=.03))
    tops = []
    for k in range(2):
        a = rng.uniform(0, math.tau) + k * math.pi
        e = V3((.3 + math.cos(a) * h * .14, h * .66, .2 + math.sin(a) * h * .14))
        P.add(tube([V3((.3, h * .42, .2)), e], [.5, .32], sides=6), S('wood', base=.44, jit=.03)); tops.append(e)
    for k, e in enumerate(tops + [V3((0, h * .82, 0))]):
        leaf_ball(P, (e.x, e.y + 1.0, e.z), h * (.24 if k < 2 else .27), seed * 5 + k)
    return P

def bush(seed=1, r=2.0, flowers='berry'):
    """rounded bush with a few flower clusters (5-petal stars) on its top"""
    P = Prop('Bush%d%s' % (seed, flowers[0])); rng = random.Random(seed)
    leaf_ball(P, (0, r * .65, 0), r, seed, base=.48)
    for k in range(6):
        a = rng.uniform(0, math.tau); el = rng.uniform(.4, 1.1)
        c = V3((math.cos(a) * math.cos(el) * r * .82, r * .65 + math.sin(el) * r * .72, math.sin(a) * math.cos(el) * r * .82))
        for j in range(5):
            b = j * math.tau / 5
            P.add(T(T(rbox((.42, .07, .24), .03, 1), (.22, 0, 0), math.degrees(b)), tuple(c)), S(flowers, base=.62, up=.15, jit=.03))
        P.add(T(ball(.1, 6, 3), tuple(c + V3((0, .06, 0)))), S('gold', base=.7, jit=.01))
    return P

def round_planter(seed=1, r=3.2, flowers='berry'):
    """round white planter with a mint band + a raised cream lip, soil, a bush in the middle and flower rings"""
    P = Prop('RoundPlanter%d' % seed); rng = random.Random(seed)
    P.add(lathe([(r - .3, -.4), (r, .2), (r, 1.6), (r + .3, 1.8), (r + .3, 2.1), (r - .4, 2.1), (r - .4, 1.8), (0, 1.8)], 24), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(torus(r + .02, .14, 24, 4), (0, .9, 0)), S('mint', base=.55, jit=.01))
    P.add(T(lathe([(r - .4, 0), (r - .6, .2), (0, .3)], 20), (0, 1.8, 0)), S('wood', base=.3, jit=.02))
    sub = round_bush(seed, r * .55, flowers); merge_prop(P, sub, (0, 1.9, 0))
    for k in range(10):
        a = k * math.tau / 10 + rng.uniform(-.1, .1); d = r - .9
        c = V3((math.cos(a) * d, 2.2, math.sin(a) * d))
        P.add(tube([c - V3((0, .3, 0)), c + V3((0, .4, 0))], .05, sides=3), S('leaf', base=.4, jit=.02))
        for j in range(5):
            b = j * math.tau / 5
            P.add(T(T(box((.4, .07, .22)), (.2, 0, 0), math.degrees(b)), tuple(c + V3((0, .45, 0)))), S(('berry', 'gold', 'wall')[k % 3], base=.62, up=.15, jit=.03))
    return P

def long_planter(L=12.0, seed=1):
    """long planter box (white with a teal kick + cream coping) with a row of clipped round shrubs and flowers"""
    P = Prop('LongPlanter%d' % int(L)); rng = random.Random(seed)
    P.add(T(rbox((L, 2.2, 2.6), .25, 2), (0, .7, 0)), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(rbox((L + .1, .5, 2.7), .1), (0, -.1, 0)), S('teal', base=.45, jit=.01))
    P.add(T(rbox((L + .3, .3, 2.9), .12), (0, 1.85, 0)), S('cream', base=.78, up=.1, jit=.01))
    P.add(T(box((L - .6, .2, 2.0)), (0, 1.85, 0)), S('wood', base=.3, jit=.02))
    n = int(L / 2.6)
    for k in range(n):
        x = -L / 2 + 1.3 + k * (L - 2.6) / max(1, n - 1)
        leaf_ball(P, (x, 3.0, 0), 1.15, seed * 9 + k, n=14, base=.46 + .05 * (k % 2))
        for j in range(3):
            a = rng.uniform(0, math.tau); c = (x + math.cos(a) * .9, 3.3 + rng.uniform(0, .6), math.sin(a) * .9)
            P.add(T(ball(.2, 6, 3), c), S(('berry', 'gold', 'coral')[(k + j) % 3], base=.62, jit=.03))
    return P

def lamp_post(seed=1):
    """plaza lamp: round foot, slim white post with a mint collar, curved arm, glass lantern with a glowing core and a
    small teal cap with a capsule-shaped finial"""
    P = Prop('LampPost')
    P.add(lathe([(.8, -.3), (.8, .3), (.55, .6), (.3, 1.0), (0, 1.0)], 12), S('teal', base=.45, up=.1, jit=.01))
    P.add(T(cyl(.22, 9.0, 10), (0, .9, 0)), S('wall', base=.88, jit=.01))
    for y in (2.4, 8.8):
        P.add(T(torus(.3, .1, 10, 4), (0, y, 0)), S('mint', base=.55, jit=.01))
    P.add(T(lathe([(.9, 0), (.95, .3), (.3, .6), (0, .65)], 12), (0, 9.9, 0)), S('wall', base=.9, jit=.01))
    P.add(T(lathe([(.65, 0), (.7, 1.6), (.55, 1.7), (0, 1.7)], 10), (0, 10.4, 0)), S('glass', base=.82, jit=0))
    P.gadd(T(lathe([(0, 0), (.38, .3), (.4, 1.0), (0, 1.3)], 8), (0, 10.6, 0)), 'lamp')
    P.add(T(lathe([(.95, 0), (.95, .25), (.4, .8), (0, .85)], 12), (0, 12.1, 0)), S('teal', base=.5, up=.15, jit=.01))
    capsule(P, (0, 12.9, 0), 'mint', .6)
    return P

def ext_bench(seed=1):
    """park bench: white cast ends with round feet, birch slats (seat + back), mint arm caps"""
    P = Prop('ParkBench')
    L = 7.0
    for sx in (-1, 1):
        x = sx * (L / 2 - .4)
        P.add(upright([(-1.1, 0), (1.1, 0), (1.0, 1.9), (1.3, 2.0), (1.3, 2.3), (.9, 2.4), (.9, 4.4), (.6, 4.6), (.4, 2.4), (-.9, 2.3), (-1.1, 2.0)], .35, (x + .17, 0, 0), 90), S('wall', base=.86, up=.1, jit=.01))
        P.add(T(rbox((.6, .3, 1.6), .12), (x, 2.45, -.5)), S('mint', base=.55, jit=.01))
    for k in range(4):
        P.add(T(rbox((L, .22, .55), .08), (0, 2.05, -.95 + k * .62)), S('wood', base=.6, up=.12, jit=.03))
    for k in range(3):
        P.add(T(T(rbox((L, .5, .2), .08), (0, 0, 0), 0, 8), (0, 2.8 + k * .62, 1.05 + k * .08)), S('wood', base=.58, up=.1, jit=.03))
    return P

def potted_tree(seed=1, col='mint'):
    """indoor potted tree: tall white pot with a coloured band and foot, slim trunk, two-lobe leafy crown"""
    P = Prop('PottedTree%d' % seed)
    P.add(lathe([(1.2, 0), (1.5, .3), (1.8, 2.6), (2.0, 2.8), (1.8, 2.9), (0, 2.75)], 16), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(torus(1.72, .14, 16, 4), (0, 2.0, 0)), S(col, base=.55, jit=.01))
    P.add(T(lathe([(1.7, 0), (1.5, .15), (0, .25)], 14), (0, 2.7, 0)), S('wood', base=.3, jit=.02))
    P.add(tube([V3((0, 2.7, 0)), V3((.2, 5.5, .1)), V3((-.1, 7.5, 0))], [.32, .24, .18], sides=6), S('wood', base=.45, jit=.03))
    leaf_ball(P, (0, 8.6, 0), 2.3, seed * 3, n=16, base=.5)
    leaf_ball(P, (.9, 6.8, .4), 1.3, seed * 3 + 1, n=12, base=.46)
    return P

def potted_fern(seed=1, col='coral'):
    """low wide pot with arching fern fronds (both sides modelled)"""
    P = Prop('PottedFern%d' % seed); rng = random.Random(seed)
    P.add(lathe([(1.0, 0), (1.3, .2), (1.4, 1.5), (1.55, 1.65), (0, 1.55)], 14), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(torus(1.42, .12, 14, 4), (0, 1.1, 0)), S(col, base=.55, jit=.01))
    for k in range(11):
        a = k * math.tau / 11 + rng.uniform(-.2, .2); L = rng.uniform(1.8, 2.6)
        pts = [V3((0, 1.5, 0)), V3((math.cos(a) * L * .45, 1.5 + L * .75, math.sin(a) * L * .45)), V3((math.cos(a) * L, 1.5 + L * .45, math.sin(a) * L)), V3((math.cos(a) * L * 1.15, 1.5 + L * .05, math.sin(a) * L * 1.15))]
        P.add(tube(pts, [.1, .32, .22, .02], sides=3, flat=(2.6, .35)), S('leaf', base=.42 + .06 * (k % 2), up=.18, jit=.04))
    return P

def welcome_sign():
    """entry monolith on the path: rounded white slab on a teal plinth, the Bloom Paw badge on top, a BLANK inset panel
    for the name GUI (no text), small planters at its feet"""
    P = Prop('WelcomeSign')
    P.add(T(rbox((10.0, 1.0, 3.0), .3), (0, .3, 0)), S('teal', base=.45, up=.1, jit=.01))
    P.add(T(rbox((9.0, 5.6, 1.6), .6, 2), (0, 3.6, 0)), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(rbox((7.4, 3.0, .2), .2, 1), (0, 3.6, -.82)), S('cream', base=.84, jit=.01))
    P.add(T(rbox((7.6, .25, .3), .08), (0, 1.95, -.82)), S('mint', base=.55, jit=.01))
    emblem_badge(P, (0, 7.6, -.2), 0, 1.9)
    for sx in (-1, 1):
        P.add(T(lathe([(1.0, 0), (1.2, 1.0), (1.3, 1.1), (0, 1.0)], 12), (sx * 5.6, 0, -.6)), S('wall', base=.86, jit=.01))
        merge_prop(P, round_bush(sx + 5, .9, 'gold' if sx > 0 else 'berry'), (sx * 5.6, 1.0, -.6))
    return P

def vending_machine(col='coral'):
    """berry-juice vending machine: rounded white cabinet, coloured side panels, glass front with 3 shelves of
    bottles, a glowing blank button panel, coin slot + pick-up flap, a little awning on top"""
    P = Prop('VendingMachine%s' % col[0].upper())
    W, H, D = 4.2, 7.6, 2.8
    P.add(T(rbox((W, H, D), .4, 2), (0, H / 2 + .2, 0)), S('wall', base=.86, up=.1, jit=.01))
    for sx in (-1, 1):
        P.add(T(rbox((.2, H - 1.0, D - .6), .08), (sx * (W / 2 + .02), H / 2 + .2, 0)), S(col, base=.58, jit=.01))
    P.add(T(rbox((W + .2, .5, D + .2), .15), (0, .15, 0)), S('dark', base=.4, jit=.01))
    P.add(T(rbox((2.7, 5.2, .1), .1, 1), (-.45, 4.6, -D / 2 - .02)), S('dark', base=.3, jit=.01))
    for j in range(3):
        y = 2.4 + j * 1.7
        P.add(T(rbox((2.5, .12, .9), .03, 1), (-.45, y, -D / 2 + .5)), S('steel', base=.6, jit=.01))
        for k in range(4):
            bottle(P, (-1.35 + k * .6, y + .07, -D / 2 + .5), ('berry', 'gold', 'sky', 'mint')[(k + j) % 4], 0, .9)
    P.add(T(rbox((2.7, 5.2, .1), .05, 1), (-.45, 4.6, -D / 2 - .1)), S('glass', base=.84, jit=0))
    P.gadd(T(rbox((.8, 2.2, .1), .06, 1), (1.4, 5.0, -D / 2 - .05)), 'screen')
    P.add(T(rbox((.5, .3, .12), .05, 1), (1.4, 3.4, -D / 2 - .05)), S('steel', base=.62, jit=.01))
    P.add(T(rbox((2.7, .8, .14), .1), (-.45, 1.3, -D / 2 - .05)), S('dark', base=.4, jit=.01))
    P.add(T(T(rbox((W + .6, .2, 1.4), .08), (0, 0, 0), 0, 18), (0, H + .2, -D / 2 - .1)), S(col, base=.55, jit=.01))
    emblem(P, (1.4, 6.8, -D / 2 - .06), 0, .4, .08, pad=col, toe='mint')
    return P

def capsule_statue():
    """plaza fountain: round two-step basin (white with a teal coping + mint water), a fluted pedestal, a giant coral
    Gem Pod tilted open-ready on a steel cradle, four small jets of water (glow) arcing in"""
    P = Prop('CapsuleFountain')
    R = 7.5
    P.add(lathe([(R + .6, -.4), (R + .6, .5), (R, 1.6), (R + .4, 1.8), (R + .4, 2.1), (R - .6, 2.1), (R - .6, .8), (0, .8)], 40), S('wall', base=.86, up=.1, jit=.01))
    P.add(T(torus(R + .1, .22, 40, 5), (0, 2.1, 0)), S('teal', base=.5, jit=.01))
    P.add(T(lathe([(R - .6, 0), (R - .65, .05), (0, .08)], 36), (0, 1.6, 0)), S('glass', base=.6, jit=0))
    P.add(lathe([(2.6, .8), (2.6, 1.4), (2.0, 1.8), (1.6, 2.0), (1.4, 5.0), (2.0, 5.4), (2.2, 5.8), (0, 5.8)], 16), S('wall', base=.88, up=.12, jit=.01))
    for k in range(8):
        a = k * math.tau / 8
        P.add(T(rbox((.3, 2.8, .3), .1), (math.cos(a) * 1.55, 3.5, math.sin(a) * 1.55)), S('mint', base=.55, jit=.01))
    P.add(T(lathe([(2.4, 0), (2.5, .3), (1.8, .6), (0, .6)], 20), (0, 5.8, 0)), S('steel', base=.55, up=.12, jit=.01))
    capsule(P, (0, 5.95, 0), 'coral', 5.2, 0, -8, 8, True)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        s = V3((math.cos(a) * (R - .2), 2.2, math.sin(a) * (R - .2)))
        P.add(T(lathe([(.4, 0), (.4, .4), (.2, .7), (0, .7)], 8), tuple(s)), S('steel', base=.6, jit=.01))
        pts = [V3((math.cos(a) * (2.0 + 3.6 * t), 5.4 + 2.6 * math.sin(math.pi * t) - 3.6 * t, math.sin(a) * (2.0 + 3.6 * t))) for t in [q / 7 for q in range(8)]]
        P.gadd(tube(pts, [.2 - .015 * q for q in range(8)], sides=5), 'heal')
    return P

def bollard_light():
    """low path bollard: rounded white post, glowing ring band, teal cap"""
    P = Prop('Bollard')
    P.add(lathe([(.55, -.3), (.55, 2.0), (.5, 2.1), (0, 2.1)], 10), S('wall', base=.88, jit=.01))
    P.gadd(T(lathe([(.57, 0), (.57, .4), (0, .4)], 10), (0, 1.5, 0)), 'lamp')
    P.add(T(lathe([(.65, 0), (.6, .25), (.3, .45), (0, .5)], 10), (0, 2.1, 0)), S('teal', base=.5, jit=.01))
    return P

def hedge(L=8.0, seed=1):
    """clipped hedge segment: rounded box mass with lumps, on a dark soil strip"""
    P = Prop('Hedge%d' % int(L)); rng = random.Random(seed)
    P.add(T(rbox((L, 3.0, 2.4), .9, 2), (0, 1.3, 0)), S('leaf', base=.44, up=.2, jit=.03))
    for k in range(int(L / 1.6)):
        x = -L / 2 + .9 + k * 1.6
        P.add(T(blob(.9, seed * 11 + k, n=10, sq=.6), (x, 2.7, rng.uniform(-.4, .4))), S('leaf', base=.5, up=.2, jit=.04))
    return P

def flower_bed(seed=1, w=6.0, d=3.0):
    """low flower clumps in a soft oval: rounded leafy mounds with 5-petal flowers on short stems in two colours"""
    P = Prop('FlowerBed%d' % seed); rng = random.Random(seed)
    cols = (('berry', 'gold'), ('coral', 'wall'), ('sky', 'gold'))[seed % 3]
    for k in range(6):
        x = rng.uniform(-w / 2, w / 2); z = rng.uniform(-d / 2, d / 2) * math.sqrt(max(0, 1 - (2 * x / w) ** 2))
        r = rng.uniform(.7, .95)
        P.add(T(ball(r, 10, 6), (x, -.05, z), 0, 0, 0, (1, .55, 1)), S('leaf', base=.45, up=.25, jit=.02), smooth=True)
        for j in range(1 + k % 2):
            a = rng.uniform(0, math.tau); dd = rng.uniform(0, r * .55)
            c = V3((x + math.cos(a) * dd, r * .5 + .12, z + math.sin(a) * dd))
            P.add(tube([c - V3((0, .35, 0)), c], .04, sides=3), S('leaf', base=.35, jit=.02))
            for p in range(5):
                b = p * math.tau / 5
                P.add(T(T(box((.34, .06, .2)), (.17, 0, 0), math.degrees(b)), tuple(c)), S(cols[j % 2], base=.62, up=.15, jit=.03))
    return P

def cloud(seed=1, w=90.0):
    """flat-bottomed cumulus for the sky (SmoothPlastic white)"""
    P = Prop('Cloud%d' % seed); rng = random.Random(seed)
    for k in range(10):
        x = rng.uniform(-w * .4, w * .4); r = w * rng.uniform(.11, .19) * (1.3 - abs(x) / w)
        pts = rock_pts((r, r * .8, r * .85), n=36, seed=seed * 11 + k)
        for p in pts: p.y = max(p.y, -r * .15)
        P.add(T(hull(pts), (x, r * .15, rng.uniform(-w * .08, w * .08))), S('wall', grad=(0, w * .25, .7, .98), up=.1))
    return P

def wall_shelf_lab(seed=3):
    """lab wall shelving: steel frame, binders in rows (coloured spines, no text), sample jars, a plant, a lower drawer
    unit"""
    P = Prop('LabShelf'); rng = random.Random(seed)
    W, H, D = 9.0, 8.5, 1.8
    shelf_frame(P, W, H, D, (2.8, 4.8, 6.8), col='wall', trim='teal')
    for y in (2.9, 4.9):
        x = -W / 2 + .7
        while x < W / 2 - 1.6:
            w = rng.uniform(.35, .55); h = rng.uniform(1.3, 1.7)
            P.add(T(rbox((w, h, 1.2), .05, 1), (x, y + h / 2 + .1, 0), 0, 0, rng.uniform(-4, 4)), S(rng.choice(('teal', 'coral', 'sky', 'gold', 'mint')), base=.55, jit=.03))
            x += w + .05
        bottle(P, (W / 2 - 1.0, y + .1, 0), rng.choice(('mint', 'berry')), 3, 1.2)
    for k in range(4):
        bottle(P, (-W / 2 + 1.2 + k * 1.2, 6.9, -.1), ('mint', 'sky', 'berry', 'gold')[k], 3, 1.1)
    pot_plant(P, (W / 2 - 1.2, 6.9, 0), .9, 'teal', 3)
    for sx in (-1, 1):
        P.add(T(rbox((W / 2 - .45, 2.0, .16), .1), (sx * (W / 4 - .05), 1.6, -D / 2 + .02)), S('cream', base=.76, jit=.01))
        P.add(T(rbox((.8, .12, .14), .04, 1), (sx * (W / 4 - .05), 2.2, -D / 2 - .1)), S('steel', base=.62, jit=.01))
    return P

# ================================================================== POLISH PASS: trim, ceiling, plants, story props, garden
WINDOWS = (0, 36, 144, 216, 324)                       # hall slot windows (others became wall decor spots)
def roof_in_y(r):
    """underside of the rotunda roof at radius r (same profile as rotunda_roof's inner lathe)"""
    yb = FL + WALL_H; ro = ROT_R + ROT_T + 2.0; rk = 13.0; yk = yb + 9.0
    t = max(0.0, min(1.0, (ro - (r + .1)) / (ro - rk)))
    return max(yb - .2, yb + .3 + (yk - yb - .3) * math.sin(t * math.pi / 2) ** 1.4 - 1.4)

def _gap(a, gaps):
    return any(abs(((a - g0 + 180) % 360) - 180) < w for g0, w in gaps)

def hall_trim():
    """interior architecture of the hall (no collision, the walls behind collide): pilasters every 18 deg with capitals
    and bases, cream wainscot panels between them, a teal chair rail, mint skirting, and a light cove ring under the
    ceiling (cream ledge + warm glow strip on top)"""
    P = Prop('HallTrim')
    r = ROT_R; da = adeg(DOOR_W / 2, r) + 3; na = adeg(ARCH_W / 2, r) + 3
    gaps = [(90, GLAZE + 2), (270, na)]
    for a in range(9, 360, 18):                                                # pilasters
        if _gap(a, gaps): continue
        P.add(ring_seg(r - .55, r, FL + 3.4, FL + 19.0, a - 1.1, a + 1.1, 1), S('wall', base=.93, up=.1, jit=.005))
        P.add(ring_seg(r - .8, r, FL + 18.4, FL + 19.2, a - 1.5, a + 1.5, 1), S('cream', base=.8, up=.1, jit=.005))
        P.add(ring_seg(r - .75, r, FL + 3.0, FL + 3.8, a - 1.4, a + 1.4, 1), S('teal', base=.5, jit=.005))
    for k in range(20):                                                        # wainscot panels between pilasters
        a0 = k * 18 + 9; a1 = a0 + 18
        for s0, s1 in ((a0 + 1.6, a0 + 8.4), (a0 + 9.6, a1 - 1.6)):
            m = (s0 + s1) / 2
            if _gap(m, [(90, GLAZE + 6), (270, na + 3)]): continue
            P.add(ring_seg(r - .45, r - .3, FL + .7, FL + 2.5, s0, s1, 2), S('cream', base=.84, up=.1, jit=.005))
            P.add(ring_seg(r - .5, r - .42, FL + .55, FL + 2.65, s0 - .25, s1 + .25, 2), S('mint', base=.62, jit=.005))
    for s0, s1 in ((90 + GLAZE + 1, 270 - na), (270 + na, 360 + 90 - GLAZE - 1)):  # chair rail + skirting
        n = int((s1 - s0) / 4)
        P.add(ring_seg(r - .75, r - .3, FL + 3.0, FL + 3.55, s0, s1, n), S('teal', base=.52, up=.1, jit=.005))
        P.add(ring_seg(r - .62, r - .3, FL - .05, FL + .55, s0, s1, n), S('mint', base=.42, jit=.005))
    for s0, s1 in ((0, 270 - na + 1), (270 + na - 1, 360)):                    # light cove ring
        n = int((s1 - s0) / 4)
        P.add(ring_seg(r - 1.4, r - .3, FL + 19.0, FL + 19.5, s0, s1, n), S('cream', base=.82, up=.1, jit=.005))
        P.add(ring_seg(r - 1.45, r - 1.2, FL + 19.5, FL + 20.1, s0, s1, n), S('cream', base=.88, jit=.005))
        P.gadd(ring_seg(r - 1.15, r - .55, FL + 19.5, FL + 19.62, s0, s1, n), 'lamp')
    return P

def hall_ceiling():
    """coffered ceiling hung under the dome (no collision): 16 radial ribs from the oculus ring to the cove, three ring
    beams (teal), mint coffer panels in a checker between them, a white trim ring round the skylight"""
    P = Prop('HallCeiling')
    rings = (14.2, 21.0, 28.0, 35.0, 42.6)
    def pt(a, r, dy=0.0): return V3((math.cos(math.radians(a)) * r, roof_in_y(r) + dy, math.sin(math.radians(a)) * r))
    for k in range(16):
        a = k * 22.5
        pts = [pt(a, r, -.35) for r in [lerp(14.0, 42.8, q / 10) for q in range(11)]]
        P.add(tube(pts, .42, sides=4, flat=(.9, .7)), S('wall', base=.92, up=-.05, jit=.005))
    for r in rings[1:-1]:
        pts = [pt(q * 360 / 48, r, -.5) for q in range(48)]
        pts.append(pts[0])
        P.add(tube(pts, .45, sides=4, flat=(.8, .8), cap0=False, cap1=False), S('teal', base=.5, up=-.05, jit=.005))
    for r, dy in ((13.6, -.7), (42.6, -.7)):                                  # tubes stay under the roof skin
        pts = [pt(q * 360 / 48, r, dy) for q in range(48)]; pts.append(pts[0])
        P.add(tube(pts, .55, sides=5, cap0=False, cap1=False), S('wall', base=.9, jit=.005))
    for i, (ra, rb) in enumerate(zip(rings, rings[1:])):                       # coffer panels (checker)
        for k in range(16):
            if (i + k) % 2: continue
            a0, a1 = k * 22.5 + 1.6, (k + 1) * 22.5 - 1.6
            ring = []
            for q in range(5):
                ring.append(pt(lerp(a0, a1, q / 4), ra + .7, -.12))
            for q in range(4, -1, -1):
                ring.append(pt(lerp(a0, a1, q / 4), rb - .7, -.12))
            bm = bmesh.new(); vs = [bm.verts.new(p) for p in ring]; f = bm.faces.new(vs); f.normal_update()
            if f.normal.y > 0: f.normal_flip()
            P.add(bm, S('mint', base=.72, up=0, jit=.005))
    return P

def wing_trim():
    """lab wing interior trim + ceiling beams (no collision): pilasters between the windows, teal chair rail, cove ledge
    with a glow strip, cross beams under the flat ceiling (skipping the dome opening)"""
    P = Prop('WingTrim')
    hw = WING_HW; zt = WING_Z0 - 2.0
    for sx in (-1, 1):
        x = sx * (hw - .28)
        for z in (-39.0, -51.5, -63.5, -75.5, -87.5):
            P.add(T(box((.55, 15.6, 2.0)), (x, FL + 11.2, z)), S('wall', base=.93, up=.1, jit=.005))
            P.add(T(box((.8, .8, 2.6)), (x - sx * .1, FL + 18.9, z)), S('cream', base=.8, jit=.005))
        L = zt - WING_ZC
        P.add(T(box((.45, .55, L)), (sx * (hw - .5), FL + 3.3, (zt + WING_ZC) / 2)), S('teal', base=.52, jit=.005))
        P.add(T(box((1.1, .5, L)), (sx * (hw - .85), FL + 17.0, (zt + WING_ZC) / 2)), S('cream', base=.82, jit=.005))
        P.gadd(T(box((.6, .1, L)), (sx * (hw - .7), FL + 17.3, (zt + WING_ZC) / 2)), 'lamp')
    P.add(T(ring_seg(hw - .75, hw - .3, FL + 3.05, FL + 3.6, 180, 360, 16), (0, 0, WING_ZC)), S('teal', base=.52, jit=.005))
    P.add(T(ring_seg(hw - 1.4, hw - .3, FL + 16.75, FL + 17.25, 180, 360, 16), (0, 0, WING_ZC)), S('cream', base=.82, jit=.005))
    P.gadd(T(ring_seg(hw - 1.15, hw - .55, FL + 17.25, FL + 17.35, 180, 360, 16), (0, 0, WING_ZC)), 'lamp')
    for z in range(-40, int(WING_ZC) - 8, -6):                                 # cross beams
        if abs(z - WING_ZC) < 13.5: continue
        w = hw if z > WING_ZC else math.sqrt(max(0, hw * hw - (z - WING_ZC) ** 2))
        P.add(T(rbox((2 * w - .6, .7, .7), .15, 1), (0, FL + WING_H - 1.35, z)), S('wall', base=.9, up=-.05, jit=.005))
    for sx in (-1, 1):
        P.add(T(rbox((.8, .7, zt - WING_ZC + 4), .15, 1), (sx * 6.6, FL + WING_H - 1.35, (zt + WING_ZC) / 2 + 2)), S('teal', base=.5, jit=.005))
    return P

# ------------------------------------------------------------------ smooth plant language (indoor + outdoor)
def leaf_cluster(P, c, r, n, seed, cols=('leaf',), base=.5, sq=.75):
    """clustered round leaves: n small smooth ellipsoids scattered on a shell of radius r round c (reads as a soft,
    rounded leaf mass with real leaf bumps)"""
    rng = random.Random(seed)
    P.add(T(ball(r * .82, 10, 6), c, 0, 0, 0, (1, sq, 1)), S(cols[0], base=base - .08, up=.25, jit=.02), smooth=True)
    for k in range(n):
        u = rng.uniform(-.35, 1); a = rng.uniform(0, math.tau); rr = math.sqrt(1 - u * u)
        d = V3((math.cos(a) * rr, u * sq, math.sin(a) * rr)) * r * .9
        s = r * rng.uniform(.28, .4)
        P.add(T(ball(s, 9, 5), (c[0] + d.x, c[1] + d.y, c[2] + d.z), math.degrees(a), 0, 0, (1, .62, 1)),
              S(rng.choice(cols), base=base + rng.uniform(-.06, .1), up=.25, jit=.02), smooth=True)

def pot(P, c=(0, 0, 0), r=1.4, h=2.4, col='mint', style=0):
    """round planter pot: style 0 = tapered white with a colour band, 1 = cylinder with a rim + feet"""
    if style == 0:
        P.add(T(lathe([(r * .75, 0), (r * .85, .1), (r, h * .9), (r * 1.08, h), (r * .98, h * 1.04), (0, h * .96)], 18), c), S('wall', base=.86, up=.1, jit=.005), smooth=True)
        P.add(T(torus(r * .95, .1, 18, 4), (c[0], c[1] + h * .7, c[2])), S(col, base=.55, jit=.005))
    else:
        P.add(T(lathe([(r, .25), (r, h), (r * 1.08, h + .05), (r * 1.08, h + .25), (r * .9, h + .25), (0, h + .1)], 18), c), S(col, base=.55, up=.1, jit=.005), smooth=True)
        for k in range(3):
            a = k * math.tau / 3
            P.add(T(rbox((.35, .3, .35), .1), (c[0] + math.cos(a) * r * .75, c[1] + .12, c[2] + math.sin(a) * r * .75)), S('wood', base=.4, jit=.005))
    P.add(T(lathe([(r * .92, 0), (r * .5, .08), (0, .1)], 14), (c[0], c[1] + h * .92, c[2])), S('wood', base=.28, jit=.01))

def fig_tree(seed=1, col='mint', h=8.5):
    """indoor fiddle-leaf / round-leaf fig: tapered pot, slim trunk splitting in two, three clustered round-leaf crowns"""
    P = Prop('FigTree%d' % seed); rng = random.Random(seed)
    pot(P, (0, 0, 0), 1.5, 2.6, col, 0)
    t0 = V3((0, 2.4, 0)); tm = V3((.15, h * .55, .1))
    P.add(tube([t0, t0.lerp(tm, .5) + V3((.1, 0, 0)), tm], [.24, .2, .17], sides=7), S('wood', base=.45, jit=.01), smooth=True)
    tops = [V3((0, h, 0))]
    for k in range(2):
        a = rng.uniform(0, math.tau) + k * math.pi; e = V3((math.cos(a) * 1.4, h * .78, math.sin(a) * 1.4))
        P.add(tube([tm, tm.lerp(e, .5) + V3((0, .3, 0)), e], [.15, .12, .1], sides=6), S('wood', base=.45, jit=.01), smooth=True)
        tops.append(e)
    P.add(tube([tm, tops[0]], [.15, .12], sides=6), S('wood', base=.45, jit=.01), smooth=True)
    for k, e in enumerate(tops):
        leaf_cluster(P, tuple(e + V3((0, .5, 0))), 1.7 if k == 0 else 1.35, 11 if k == 0 else 8, seed * 5 + k, ('leaf', 'grass'))
    return P

def monstera(seed=1, col='coral'):
    """monstera in a footed pot: 7 big split leaves (heart shape with side slits) on arching stems, two-sided"""
    P = Prop('Monstera%d' % seed); rng = random.Random(seed)
    pot(P, (0, 0, 0), 1.3, 1.6, col, 1)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-.2, .2); L = rng.uniform(2.2, 3.2); el = rng.uniform(.6, 1.1)
        d = V3((math.cos(a), 0, math.sin(a)))
        base = V3((0, 1.7, 0)); tip = base + d * L * math.cos(el) + V3((0, L * math.sin(el), 0))
        P.add(tube([base, base.lerp(tip, .5) + V3((0, .4, 0)), tip], [.08, .07, .06], sides=4), S('leaf', base=.4, jit=.01))
        ls = rng.uniform(1.3, 1.8); W = ls * .42
        wf = lambda t: W * math.sin(math.pi * min(1, t * 1.05)) ** .7
        lobes = [[(0, 0)] + [(wf(t) * .32, -t * ls) for t in (.15, .5, .85)] + [(0, -ls)] + [(-wf(t) * .32, -t * ls) for t in (.85, .5, .15)]]
        for sd in (-1, 1):                                                  # side lobes with slits between them
            for jj in range(5):
                ta, tb = jj / 5 + .03, (jj + 1) / 5 - .03
                lobes.append([(0, -ta * ls), (sd * wf(ta + .05), -(ta + .08) * ls), (sd * wf(tb + .05), -(tb + .08) * ls), (0, -tb * ls)])
        lobes = [[(x, -z) for x, z in poly] for poly in lobes]
        yaw = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        for poly in lobes:
            bm = ngon_prism([(x, -z) for x, z in poly], -.03, .03)
            P.add(T(T(bm, (0, 0, 0), 0, -35), tuple(tip), yaw), S('leaf', base=rng.uniform(.42, .58), up=.25, jit=.02))
    return P

def snake_plant(seed=1, col='teal'):
    """tall snake plant: square pot, 11 upright sword leaves (flattened tapered blades, light edges)"""
    P = Prop('SnakePlant%d' % seed); rng = random.Random(seed)
    P.add(T(rbox((2.2, 2.0, 2.2), .35, 2), (0, 1.0, 0)), S(col, base=.55, up=.1, jit=.005))
    P.add(T(rbox((2.35, .3, 2.35), .12, 1), (0, 2.0, 0)), S('wall', base=.9, jit=.005))
    P.add(T(box((1.9, .1, 1.9)), (0, 2.05, 0)), S('wood', base=.28, jit=.01))
    for k in range(11):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .6); L = rng.uniform(3.2, 5.4)
        b = V3((math.cos(a) * d, 2.0, math.sin(a) * d)); lean = V3((math.cos(a) * .5, 0, math.sin(a) * .5))
        pts = [b, b + V3((0, L * .5, 0)) + lean * .4, b + V3((0, L, 0)) + lean]
        P.add(tube(pts, [.28, .3, .02], sides=5, flat=(1.0, .25), rot0=rng.uniform(0, 3)), S('leaf', base=rng.uniform(.3, .45), up=.2, jit=.02), smooth=True)
        P.add(tube([p + V3((0, -.05, 0)) for p in pts], [.31, .32, .02], sides=5, flat=(1.0, .12), rot0=0), S('gold', base=.55, jit=.01))
    return P

def hanging_planter(drop=5.0, col='coral', seed=1):
    """hanging planter (origin = ceiling point, hangs DOWN): three cords, a round bowl, a leaf mound and trailing vines"""
    P = Prop('HangingPot%s' % col[0].upper()); rng = random.Random(seed)
    yb = -drop
    P.add(lathe([(.4, -.3), (.4, -.1), (.15, 0), (0, 0)], 8), S('wall', base=.86, jit=.005))
    for k in range(3):
        a = k * math.tau / 3
        P.add(tube([V3((0, -.2, 0)), V3((math.cos(a) * 1.0, yb + 1.0, math.sin(a) * 1.0))], .04, sides=3), S('wood', base=.6, jit=.01))
    P.add(T(lathe([(0, 0), (.6, .05), (1.05, .6), (1.15, 1.05), (1.0, 1.1), (0, 1.0)], 16), (0, yb, 0)), S(col, base=.58, up=.1, jit=.005), smooth=True)
    leaf_cluster(P, (0, yb + 1.3, 0), .9, 7, seed, ('leaf', 'grass'), sq=.5)
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.2, .2); L = rng.uniform(1.6, 3.0)
        p0 = V3((math.cos(a) * 1.0, yb + 1.0, math.sin(a) * 1.0))
        pts = [p0 + V3((math.cos(a) * .3 * q / 4, -L * q / 4, math.sin(a) * .3 * q / 4)) for q in range(5)]
        P.add(tube(pts, .05, sides=3), S('leaf', base=.35, jit=.01))
        for q in range(1, 5):
            P.add(T(ball(.2, 6, 3), tuple(pts[q] + V3((.12 * (q % 2 * 2 - 1), 0, 0))), 0, 0, 0, (1, .5, 1)), S('leaf', base=.5, up=.2, jit=.02), smooth=True)
    return P

def round_tree(seed=1, h=17.0):
    """outdoor rounded park tree in the same language: smooth tapered trunk with two boughs, a soft canopy of big
    rounded leaf masses + clustered round leaves, root flare"""
    P = Prop('RoundTree%d' % seed); rng = random.Random(seed)
    P.add(tube([V3((0, -1.2, 0)), V3((0, h * .3, 0)), V3((.2, h * .5, .1))], [1.0, .7, .55], sides=9), S('wood', base=.45, up=.1, jit=.01), smooth=True)
    for k in range(4):
        a = k * math.tau / 4 + .4
        P.add(tube([V3((0, .4, 0)), V3((math.cos(a) * 1.3, -.2, math.sin(a) * 1.3)), V3((math.cos(a) * 1.9, -.7, math.sin(a) * 1.9))], [.42, .25, .08], sides=5), S('wood', base=.4, jit=.01), smooth=True)
    centres = [V3((0, h * .78, 0))]
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(0, .6); centres.append(V3((math.cos(a) * h * .2, h * .66 + rng.uniform(-.5, 1.0), math.sin(a) * h * .2)))
    for k, c in enumerate(centres[1:]):
        P.add(tube([V3((.2, h * .48, .1)), c], [.4, .22], sides=6), S('wood', base=.42, jit=.01), smooth=True)
    for k, c in enumerate(centres):
        r = h * (.27 if k == 0 else .21)
        P.add(T(ball(r, 12, 7), tuple(c), 0, 0, 0, (1, .82, 1)), S('leaf', base=.5 + .04 * (k % 2), up=.3, jit=.02), smooth=True)
        for j in range(3):
            a = rng.uniform(0, math.tau); u = rng.uniform(-.1, .8); rr = math.sqrt(1 - u * u)
            p = c + V3((math.cos(a) * rr, u * .82, math.sin(a) * rr)) * r * .92
            P.add(T(ball(r * .34, 8, 5), tuple(p), 0, 0, 0, (1, .7, 1)), S('grass', base=.55, up=.3, jit=.02), smooth=True)
    return P

def blossom_tree(seed=1, h=13.0):
    """small ornamental tree: smooth trunk, round canopy in soft pink (berry ramp light end) with leaf flecks"""
    P = Prop('BlossomTree%d' % seed); rng = random.Random(seed)
    P.add(tube([V3((0, -1.0, 0)), V3((0, h * .35, 0)), V3((.3, h * .55, 0))], [.7, .5, .4], sides=8), S('wood', base=.42, jit=.01), smooth=True)
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(0, .5); c = (math.cos(a) * h * .16, h * .7 + rng.uniform(0, .8), math.sin(a) * h * .16)
        P.add(T(ball(h * .2, 12, 7), c, 0, 0, 0, (1, .8, 1)), S('berry', base=.82, up=.15, jit=.02), smooth=True)
    P.add(T(ball(h * .24, 14, 8), (0, h * .86, 0), 0, 0, 0, (1, .8, 1)), S('berry', base=.86, up=.12, jit=.02), smooth=True)
    return P

def topiary_hedge(L=8.0, seed=1):
    """clipped hedge with a smooth rounded profile on a low white kerb, plus two topiary balls on top"""
    P = Prop('Topiary%d' % int(L))
    P.add(T(rbox((L + .4, .7, 2.9), .2, 2), (0, .1, 0)), S('wall', base=.86, jit=.005))
    P.add(T(rbox((L, 2.8, 2.4), 1.0, 3), (0, 1.8, 0)), S('leaf', base=.5, up=.25, jit=.01), smooth=True)
    for sx in (-1, 1):
        P.add(T(ball(.9, 12, 7), (sx * L * .3, 3.6, 0)), S('leaf', base=.56, up=.25, jit=.01), smooth=True)
    return P

def round_bush(seed=1, r=1.8, flowers='berry'):
    """smooth round shrub: soft leaf mound with clustered leaves and small 5-petal flowers sitting on its surface"""
    P = Prop('RoundBush%d%s' % (seed, flowers[0])); rng = random.Random(seed)
    leaf_cluster(P, (0, r * .6, 0), r, 7, seed, ('leaf', 'grass'), sq=.72)
    for k in range(5):
        a = rng.uniform(0, math.tau); u = rng.uniform(.2, .8); rr = math.sqrt(1 - u * u)
        c = V3((math.cos(a) * rr * r * .95, r * .6 + u * r * .72, math.sin(a) * rr * r * .95))
        for j in range(5):
            P.add(T(T(box((.36, .06, .2)), (.18, 0, 0), j * 72), tuple(c)), S(flowers, base=.65, up=.15, jit=.02))
        P.add(T(ball(.08, 5, 3), tuple(c + V3((0, .05, 0)))), S('gold', base=.75, jit=.01))
    return P

def garden_wall(L=14.0):
    """low garden boundary wall: white rendered wall with a teal coping and a mint plinth, a post at each end"""
    P = Prop('GardenWall%d' % int(L))
    P.add(T(rbox((L, 2.2, 1.0), .12, 1), (0, .6, 0)), S('wall', base=.85, up=.1, jit=.005))
    P.add(T(rbox((L + .3, .35, 1.4), .1, 1), (0, 1.85, 0)), S('teal', base=.5, up=.1, jit=.005))
    P.add(T(rbox((L + .1, .5, 1.2), .08, 1), (0, -.1, 0)), S('mint', base=.45, jit=.005))
    P.add(T(rbox((1.5, 3.0, 1.6), .2, 1), (L / 2, 1.0, 0)), S('wall', base=.9, jit=.005))
    P.add(T(lathe([(.7, 0), (.75, .2), (.4, .5), (0, .55)], 8), (L / 2, 2.5, 0)), S('teal', base=.55, jit=.005))
    return P

def lily_pads(seed=1):
    """floating lily pads (notched discs) with two pink flowers"""
    P = Prop('LilyPads%d' % seed); rng = random.Random(seed)
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 3.0); r = rng.uniform(.6, 1.0)
        poly = [(math.cos(t) * r, math.sin(t) * r) for t in [.35 + q * (math.tau - .7) / 12 for q in range(13)]] + [(0, 0)]
        P.add(T(ngon_prism(poly, 0, .08), (math.cos(a) * d, 0, math.sin(a) * d), rng.uniform(0, 360)), S('leaf', base=.5, up=.15, jit=.02))
        if k < 2:
            c = (math.cos(a) * d, .1, math.sin(a) * d)
            for j in range(6):
                P.add(T(T(box((.5, .08, .22)), (.22, 0, 0), j * 60, 0, -25), c), S('berry', base=.78, jit=.02))
            P.add(T(ball(.12, 6, 3), (c[0], .3, c[2])), S('gold', base=.75, jit=.01))
    return P

def reeds(seed=1):
    P = Prop('Reeds%d' % seed); rng = random.Random(seed)
    for k in range(10):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .9); L = rng.uniform(2.5, 4.2)
        b = V3((math.cos(a) * d, -.3, math.sin(a) * d))
        P.add(tube([b, b + V3((math.cos(a) * .3, L, math.sin(a) * .3))], [.1, .02], sides=3, flat=(2, .5)), S('leaf', base=.4, jit=.02))
        if k % 3 == 0:
            P.add(T(cyl(.12, .7, 5), tuple(b + V3((math.cos(a) * .25, L * .75, math.sin(a) * .25)))), S('wood', base=.3, jit=.01))
    return P

def stepping_stone(seed=1):
    P = Prop('SteppingStone')
    P.add(T(lathe([(1.2, -.4), (1.3, .2), (1.15, .35), (0, .4)], 12), (0, 0, 0), 0, 0, 0, (1, 1, .8)), S('paving', base=.7, up=.15, jit=.02), smooth=True)
    return P

# ------------------------------------------------------------------ story props + decor
def plush(col='mint', ear='leaf', seed=1):
    """creature plush toy (an original critter): round body, two leaf ears, stubby paws, dot eyes + blush, curled tail"""
    P = Prop('Plush%s' % col.capitalize())
    P.add(T(ball(1.0, 12, 7), (0, 1.0, 0), 0, 0, 0, (1, .9, .95)), S(col, base=.62, up=.2, jit=.01), smooth=True)
    P.add(T(ball(.62, 10, 6), (0, .85, -.6), 0, 0, 0, (1, .85, .6)), S('wall', base=.92, jit=.005), smooth=True)
    for sx in (-1, 1):
        P.add(upright(leaf_poly(1.0, .32, 6, sx * 25, (0, 0)), .12, (sx * .45, 1.6, .1), 0), S(ear, base=.55, up=.1, jit=.01))
        P.add(T(ball(.12, 6, 4), (sx * .32, 1.25, -.92)), S('dark', base=.15, jit=0))
        P.add(T(ball(.12, 6, 3), (sx * .55, 1.05, -.85), 0, 0, 0, (1, .5, .4)), S('coral', base=.75, jit=0))
        P.add(T(ball(.28, 8, 4), (sx * .55, .2, -.55), 0, 0, 0, (1, .7, 1.2)), S(col, base=.55, jit=.01), smooth=True)
    P.add(tube([V3((0, .5, .9)), V3((0, .8, 1.5)), V3((0, 1.4, 1.5)), V3((0, 1.4, 1.1))], [.22, .2, .15, .08], sides=6), S(col, base=.5, jit=.01), smooth=True)
    return P

def heal_corner():
    """Heal story cluster: a big creature bed with a folded + a draped blanket, a plush curled in it, food + water bowls,
    a towel stand with rolled towels, a small first-aid cart with a capsule tray"""
    P = Prop('HealCorner'); rng = random.Random(4)
    P.add(lathe([(2.6, 0), (2.8, .4), (2.85, 1.0), (2.6, 1.3), (2.1, 1.2), (1.95, .7), (0, .6)], 20), S('teal', base=.55, up=.12, jit=.005), smooth=True)
    P.add(T(lathe([(1.95, 0), (1.9, .25), (0, .32)], 18), (0, .6, 0)), S('cream', base=.84, jit=.005), smooth=True)
    bl = []
    for i in range(7):                                                         # draped blanket: a wavy sheet over the rim
        row = []
        for j in range(7):
            x = -1.6 + j * .55; z = -.6 + i * .5
            row.append(V3((x, .95 + .14 * math.sin(j * 1.3 + i) + .45 * smooth((z - 1.0) / 1.3), z)))
        bl.append(row)
    bm = bmesh.new(); vv = [[bm.verts.new(p) for p in row] for row in bl]
    for i in range(6):
        for j in range(6): bm.faces.new((vv[i][j], vv[i][j + 1], vv[i + 1][j + 1], vv[i + 1][j]))
    bm2 = bm.copy(); bmesh.ops.reverse_faces(bm2, faces=list(bm2.faces)); bmesh.ops.translate(bm2, vec=V3((0, -.06, 0)), verts=bm2.verts)
    P.add(bm, S('coral', base=.62, up=.15, jit=.01), smooth=True); P.add(bm2, S('coral', base=.5, jit=.01), smooth=True)
    merge_prop(P, plush('sky', 'leaf'), (.6, .55, -.3), .55, 200)
    for k in range(3):                                                         # folded blankets stack
        P.add(T(rbox((1.8, .35, 1.3), .15, 2), (3.9, .2 + k * .38, -.8), 8 * k), S(('mint', 'cream', 'coral')[k], base=.62, jit=.01))
    for x, c in ((-3.4, 'mint'), (-2.4, 'sky')):
        P.add(T(lathe([(.55, 0), (.65, .35), (.55, .38), (.42, .2), (0, .15)], 14), (x, 0, -1.6)), S(c, base=.55, jit=.005), smooth=True)
    for k in range(4):
        P.add(T(ball(.12, 6, 3), (-3.4 + rng.uniform(-.25, .25), .3, -1.6 + rng.uniform(-.25, .25))), S('wood', base=.45, jit=.01))
    P.add(T(lathe([(.4, .2), (0, .22)], 12), (-2.4, 0, -1.6)), S('glass', base=.85, jit=0))
    # towel stand
    P.add(T(rbox((1.6, .2, 1.0), .06), (-3.8, 1.9, 1.2)), S('wood', base=.6, jit=.01))
    P.add(T(rbox((1.6, .2, 1.0), .06), (-3.8, .7, 1.2)), S('wood', base=.6, jit=.01))
    for sx in (-1, 1):
        P.add(T(box((.12, 2.1, .12)), (-3.8 + sx * .72, 1.0, 1.2)), S('wood', base=.45, jit=.01))
    for k in range(3):
        P.add(T(T(cyl(.25, .9, 10), (0, -.45, 0), 0, 0, 90), (-4.2 + k * .42, 2.25, 1.2)), S(('wall', 'mint', 'wall')[k], base=.86, jit=.005), smooth=True)
    return P

def supply_boxes(seed=1):
    """Shop story: stacked supply cartons (cream with coral tape and a paw stamp), an open capsule carton showing pods,
    a hand trolley leaning on the stack"""
    P = Prop('SupplyBoxes%d' % seed); rng = random.Random(seed)
    spots = [(0, 0, 0, 2.4), (2.5, 0, .2, 2.0), (.3, 2.4, .1, 2.0), (-2.3, 0, -.3, 1.8), (1.4, 2.0, .3, 1.6)]
    for k, (x, y, z, s) in enumerate(spots):
        yaw = rng.uniform(-12, 12)
        P.add(T(rbox((s, s * .85, s * .9), .08, 1), (x, y + s * .425, z), yaw), S('cream', base=.72 + rng.uniform(-.04, .04), up=.1, jit=.01))
        P.add(T(rbox((s * .25, s * .86, s * .91), .03, 1), (x, y + s * .425, z), yaw), S('coral', base=.55, jit=.005))
        emblem(P, tuple(to_v(x, y + s * .5, z) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ V3((s * .3, 0, -s * .455))), yaw, s * .18, .03, pad='coral', toe='coral')
    cx, cz = 3.6, -2.2                                                          # open carton with pods
    P.add(T(rbox((2.0, 1.0, 1.4), .06, 1), (cx, .5, cz), 15), S('cream', base=.7, jit=.01))
    for sx in (-1, 1):
        P.add(T(T(box((2.0, .05, .7)), (0, 0, sx * .35), 0, sx * 50), (cx, 1.0, cz + sx * .7), 15), S('cream', base=.78, jit=.01))
    for k in range(5):
        capsule(P, (cx - .7 + k * .35, .8, cz + rng.uniform(-.3, .3)), TIERS[k % 4], .45, rng.uniform(0, 360), 0, 6, False)
    return P

def to_v(x, y, z): return V3((x, y, z))

def sale_stand():
    """Shop story: A-frame sidewalk stand with a blank coral board (GUI spot) and a wire bin of boxed capsules"""
    P = Prop('SaleStand')
    for sz in (-1, 1):
        P.add(T(T(rbox((2.6, 3.6, .14), .08, 1), (0, 1.8, 0), 0, sz * 12), (0, 0, sz * .2)), S('wall', base=.88, jit=.005))
        P.add(T(T(rbox((2.2, 2.5, .05), .04, 1), (0, 2.0, -sz * .08), 0, sz * 12), (0, 0, sz * .2)), S('coral', base=.6, jit=.005))
    P.add(T(lathe([(.25, 0), (.25, .2), (0, .2)], 8), (0, 3.6, 0)), S('teal', base=.5, jit=.005))
    bx, bz = 2.6, -.4
    P.add(T(lathe([(1.0, 0), (1.05, 1.6), (.95, 1.6), (.9, .1), (0, .1)], 14), (bx, 0, bz)), S('steel', base=.62, jit=.005))
    for k in range(5):
        a = k * math.tau / 5
        capsule(P, (bx + math.cos(a) * .45, 1.25 + (k % 2) * .15, bz + math.sin(a) * .45), TIERS[k % 4], .6, math.degrees(a), 0, 6)
    capsule(P, (bx, 1.55, bz), 'gold', .65, 30, 0, 6)
    return P

def dock_cables():
    """Storage story: cable runs across the floor under rubber cable covers to three glowing dock pylons + a server
    cabinet with blinking lights"""
    P = Prop('DockCables')
    for k, x in enumerate((-6.0, 0.0, 6.0)):
        P.add(T(lathe([(.6, 0), (.6, .3), (.4, .4), (.35, 2.2), (.5, 2.4), (0, 2.45)], 12), (x, 0, 0)), S('wall', base=.86, jit=.005), smooth=True)
        P.gadd(T(lathe([(.38, 0), (.38, .5), (0, .5)], 12), (x, 1.5, 0)), 'screen')
        P.add(tube([V3((x, .08, .4)), V3((x * .6, .08, 2.5)), V3((x * .2, .08, 4.0))], .14, sides=5, flat=(1.4, .5)), S('dark', base=.35, jit=.005))
    P.add(T(rbox((1.6, .14, 4.0), .05, 1), (0, .07, 4.2)), S('dark', base=.45, jit=.005))
    P.add(T(rbox((2.4, 5.2, 1.6), .2, 2), (9.5, 2.6, 1.0)), S('wall', base=.86, jit=.005))
    P.add(T(rbox((2.0, 4.4, .1), .1, 1), (9.5, 2.7, .17)), S('dark', base=.3, jit=.005))
    for j in range(6):
        P.gadd(T(box((1.4, .1, .06)), (9.5, .9 + j * .7, .12)), 'screen')
        P.gadd(T(box((.14, .14, .06)), (10.25, .9 + j * .7, .12)), 'heal')
    return P

def rope_line(n=4, L=4.0, col='sky'):
    """queue rope line: n steel stanchions with weighted bases, sagging coloured ropes"""
    P = Prop('RopeLine%d' % n)
    xs = [-(n - 1) * L / 2 + i * L for i in range(n)]
    for x in xs:
        P.add(T(lathe([(.6, 0), (.6, .15), (.2, .3), (0, .3)], 12), (x, 0, 0)), S('steel', base=.5, jit=.005), smooth=True)
        P.add(T(cyl(.12, 2.6, 8), (x, .2, 0)), S('steel', base=.65, jit=.005))
        P.add(T(ball(.22, 8, 4), (x, 2.9, 0)), S(col, base=.55, up=.2, jit=.005), smooth=True)
    for xa, xb in zip(xs, xs[1:]):
        P.add(tube(sag((xa, 2.55, 0), (xb, 2.55, 0), .55, 6), .1, sides=5), S(col, base=.45, jit=.005), smooth=True)
    return P

def trophy_shelf():
    """Trade story: wall trophy shelf (two birch boards on teal brackets) with gold cups, a star plaque on a stand,
    capsule-topped trophies and a ribbon medal hanging from the board"""
    P = Prop('TrophyShelf')
    for y in (4.0, 6.6):
        P.add(T(rbox((7.0, .25, 1.4), .08, 1), (0, y, 0)), S('wood', base=.62, up=.1, jit=.01))
        for sx in (-1, 1):
            P.add(T(rbox((.25, .9, 1.2), .06, 1), (sx * 2.8, y - .55, .05)), S('teal', base=.5, jit=.005))
    P.add(T(rbox((7.4, 4.4, .2), .1, 1), (0, 5.2, .7)), S('mint', base=.7, jit=.005))
    for k, x in enumerate((-2.6, -.9, .9, 2.6)):
        h = (1.4, 1.9, 1.6, 1.2)[k]
        P.add(T(lathe([(.4, 0), (.4, .2), (.15, .3), (.12, h * .45), (.55, h * .6), (.6, h * .95), (.5, h), (0, h * .7)], 12), (x, 4.12, -.1)), S('gold', base=.62, up=.25, jit=.01), smooth=True)
        for sx in (-1, 1):
            P.add(T(torus(.22, .05, 8, 4, 0, math.pi), (x + sx * .6, 4.12 + h * .78, -.1), 0, 0, 90 * sx), S('gold', base=.55, jit=.01))
    P.add(T(lathe([(.5, 0), (.5, .3), (0, .3)], 12), (-1.8, 6.72, -.1)), S('wall', base=.86, jit=.005))
    capsule(P, (-1.8, 7.0, -.1), 'gold', .9)
    P.add(T(lathe([(.5, 0), (.5, .3), (0, .3)], 12), (1.8, 6.72, -.1)), S('wall', base=.86, jit=.005))
    star = [(math.cos(math.pi / 2 + q * math.pi / 5) * (.8 if q % 2 == 0 else .35), math.sin(math.pi / 2 + q * math.pi / 5) * (.8 if q % 2 == 0 else .35)) for q in range(10)]
    P.add(upright(star, .15, (1.8, 7.9, -.05)), S('gold', base=.65, up=.1, jit=.005))
    P.add(T(rbox((.12, .9, .12), .04, 1), (1.8, 7.3, 0)), S('steel', base=.55, jit=.005))
    for sx in (-1, 1):
        P.add(T(T(box((.25, .9, .04)), (0, -.45, 0), 0, 0, sx * 18), (.1 * sx, 6.45, -.72)), S('sky' if sx < 0 else 'coral', base=.6, jit=.005))
    P.add(T(T(cyl(.32, .08, 12), (0, 0, 0), 0, -90), (0, 5.4, -.76)), S('gold', base=.7, jit=.005))
    return P

def floor_mat(w=14.0, d=6.0, col='teal'):
    """reception mat: rounded rectangle with a mint border and the Bloom Paw woven in"""
    P = Prop('EntryMat')
    P.add(T(rbox((w, .12, d), .5, 2), (0, .06, 0)), S(col, base=.5, up=.05, jit=.005))
    P.add(T(rbox((w - 1.0, .14, d - 1.0), .4, 2), (0, .07, 0)), S('mint', base=.6, jit=.005))
    P.add(T(rbox((w - 1.6, .16, d - 1.6), .35, 2), (0, .08, 0)), S(col, base=.48, jit=.005))
    pad = Prop('_m'); emblem(pad, (0, 0, 0), 0, 1.6, .05, pad='cream', toe='cream', base=.85)
    for i, v in enumerate(pad.solid.V): pad.solid.V[i] = (-v[0], .17 - v[2], -v[1])
    P.solid.merge(pad.solid)
    return P

def round_rug(r=6.0, col='coral', col2='cream'):
    """round rug: three concentric bands, a scalloped edge"""
    P = Prop('RoundRug%s' % col[0].upper())
    P.add(lathe([(r, 0), (r, .1), (0, .1)], 32), S(col, base=.58, jit=.005))
    P.add(T(lathe([(r * .78, 0), (r * .78, .12), (0, .12)], 28), (0, 0, 0)), S(col2, base=.82, jit=.005))
    P.add(T(lathe([(r * .55, 0), (r * .55, .14), (0, .14)], 24), (0, 0, 0)), S(col, base=.66, jit=.005))
    for k in range(16):
        a = k * math.tau / 16
        P.add(T(cyl(.5, .1, 8), (math.cos(a) * r, 0, math.sin(a) * r)), S(col, base=.5, jit=.005))
    return P

def wall_clock(col='teal'):
    """wall clock with a BLANK face (no numerals): rim ring, 12 tick dots, two hands, centre cap (faces -Z)"""
    P = Prop('HangingClock')               # wall-hung (float-ok 'hang')
    P.add(T(lathe([(1.4, 0), (1.45, .2), (1.3, .35), (0, .3)], 24), (0, 0, 0), 0, -90), S(col, base=.55, up=.1, jit=.005), smooth=True)
    P.add(T(lathe([(1.15, 0), (1.15, .32), (0, .32)], 24), (0, 0, 0), 0, -90), S('wall', base=.95, jit=0))
    for k in range(12):
        a = k * math.tau / 12
        P.add(T(box((.12, .12, .06)), (math.cos(a) * .95, math.sin(a) * .95, -.34)), S('dark', base=.3, jit=0))
    P.add(T(T(box((.1, .6, .05)), (0, .3, 0), 0, 0, -40), (0, 0, -.36)), S('dark', base=.2, jit=0))
    P.add(T(T(box((.08, .85, .05)), (0, .42, 0), 0, 0, 70), (0, 0, -.38)), S('dark', base=.25, jit=0))
    P.add(T(T(cyl(.1, .1, 8), (0, 0, 0), 0, -90), (0, 0, -.38)), S('coral', base=.6, jit=0))
    return P

def art_frame(seed=1, w=5.0, h=6.5):
    """framed poster with an abstract landscape (no text): hills, a sun disc, a little capsule; birch frame + mat"""
    P = Prop('HangingArt%d' % seed); rng = random.Random(seed)
    pal = (('sky', 'mint', 'teal', 'gold'), ('coral', 'gold', 'berry', 'wall'), ('mint', 'sky', 'teal', 'coral'))[seed % 3]
    P.add(T(rbox((w + .8, h + .8, .3), .1, 1), (0, 0, 0)), S('wood', base=.6, up=.1, jit=.005))
    P.add(T(box((w, h, .1)), (0, 0, -.18)), S('cream', base=.9, jit=0))
    P.add(T(box((w - .8, h - .8, .06)), (0, 0, -.24)), S(pal[0], base=.78, jit=0))
    for k in range(3):
        cx = -1.5 + k * 1.6; rr = 1.6 + k * .3
        hill = [(cx + math.cos(t) * rr, -(h - .8) / 2 + math.sin(t) * rr * .7) for t in [math.pi * q / 8 for q in range(9)]]
        hill = [(max(-(w - .8) / 2, min((w - .8) / 2, x)), y) for x, y in hill]
        P.add(upright(hill, .04, (0, 0, -.28)), S(pal[1 + k % 2], base=.55 + .08 * k, jit=0))
    sun = [(1.0 + math.cos(t) * .7, 1.6 + math.sin(t) * .7) for t in [q * math.tau / 14 for q in range(14)]]
    P.add(upright(sun, .05, (0, 0, -.3)), S(pal[3], base=.7, jit=0))
    return P

def wall_capsules(tier_a='mint', tier_b='coral'):
    """wall-mounted capsule display: rounded white case with a glass front, three capsules on lit pedestals, a teal
    header with the Bloom Paw"""
    P = Prop('WallCapsules')
    P.add(T(rbox((6.0, 3.6, 1.2), .3, 2), (0, 0, 0)), S('wall', base=.88, up=.1, jit=.005))
    P.add(T(box((5.4, 3.0, .1)), (0, 0, -.5)), S('cream', base=.7, jit=0))
    for k, t in enumerate((tier_a, 'gold', tier_b)):
        x = -1.8 + k * 1.8
        P.add(T(lathe([(.45, 0), (.45, .25), (0, .25)], 12), (x, -1.4, -.25)), S('steel', base=.6, jit=.005))
        P.gadd(T(torus(.45, .05, 12, 3), (x, -1.13, -.25)), 'gem')
        capsule(P, (x, -1.15, -.25), t, 1.2)
    P.add(T(box((5.6, 3.2, .06)), (0, 0, -.62)), S('glass', base=.85, jit=0))
    P.add(T(rbox((6.3, .7, 1.4), .2, 1), (0, 2.0, 0)), S('teal', base=.5, jit=.005))
    emblem(P, (0, 2.0, -.72), 0, .35, .05, pad='wall', toe='wall', base=.92)
    return P

def water_cooler():
    """water cooler: white cabinet with a sky front, upturned blue water bottle (glass), two taps, cup dispenser"""
    P = Prop('DrinkCooler')                 # not 'Water*': the checks would treat it as water
    P.add(T(rbox((1.8, 3.4, 1.6), .25, 2), (0, 1.7, 0)), S('wall', base=.88, up=.1, jit=.005))
    P.add(T(rbox((1.5, 1.6, .08), .1, 1), (0, 1.2, -.8)), S('sky', base=.6, jit=.005))
    P.add(T(rbox((1.2, .2, .7), .06, 1), (0, 2.1, -.95)), S('steel', base=.6, jit=.005))
    for sx, c in ((-1, 'sky'), (1, 'coral')):
        P.add(T(rbox((.25, .35, .3), .06, 1), (sx * .35, 2.65, -.88)), S(c, base=.6, jit=.005))
    P.add(T(lathe([(.2, 0), (.2, .3), (.75, .6), (.8, 2.2), (.6, 2.4), (0, 2.45)], 14), (0, 3.4, 0)), S('glass', base=.7, jit=0), smooth=True)
    P.add(T(lathe([(.72, 0), (.74, 1.5), (0, 1.5)], 14), (0, 4.0, 0)), S('sky', base=.62, jit=.005), smooth=True)
    P.add(T(cyl(.25, 1.6, 10), (1.05, 1.6, .2)), S('wall', base=.8, jit=.005))
    return P

# ================================================================== CATCH BALL (original design, replaces the Gem Pod)
# Smooth sphere of two thick shells meeting at a seam TILTED 20 deg (high at the back hinge, low at the front latch);
# the upper shell carries the tier colour + a trim pattern + a small raised Bloom Paw; a raised pill latch with a
# glowing gem and light ring straddles the seam at the front; three hinge knuckles at the back. Painted shading per
# vertex: light top, darker underside, a soft spec spot toward the key light. LODs: 0 hero (~2k), 1 standard (~900),
# 2 shelf (~300). open_deg > 0 swings the upper shell up about the hinge and lights a soft glow inside.
from mathutils import noise as MN
BALL_TILT = 20.0
BALL_STYLE = {   # tier key (old Gem Pod tiers) -> upper, upper value, lower, lower value, rim, trim kind, trim colour
    'mint':  ('mint', .52, 'wall', .82, 'wall', None, None),            # Basic: mint over white, plain
    'sky':   ('sky', .5, 'wall', .82, 'wall', 'stripes', 'wall'),       # Great: sky blue, two stripe bands
    'coral': ('coral', .5, 'dark', .34, 'wall', 'chevron', 'dark'),     # Ultra: coral over charcoal, chevron
    'gold':  ('berry', .2, 'gold', .55, 'gold', 'star', 'gold'),        # Master: plum over gold, star inlay
}
SPEC = Vector((-.45, .78, -.43)).normalized()

def _dense(poly, step=.1):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for k in range(n): out.append((lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
    return out

def sphere_decal(poly, d, t1, R, h=.05, step=.1):
    """a raised inlay that hugs a sphere of radius R (centre origin): poly in tangent-plane units round direction d
    (u along t1, v along t1 x d), gnomonic-projected onto the sphere, thickness h * R"""
    d = Vector(d).normalized(); t1 = (Vector(t1) - d * Vector(t1).dot(d)).normalized(); t2 = t1.cross(d)
    bm = ngon_prism(_dense(poly, step), 0, 1)
    for v in bm.verts:
        x, y, z = v.co
        v.co = (d + t1 * x + t2 * z).normalized() * R * (.995 + y * h)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); return bm

def _shell(R, g, th, upper, n, rings, inner):
    """one thick shell -> (outer, inner): outer cap lat 90 -> g with a bevelled rolled rim and a hidden plug; inner =
    the open inside surface (only for an open ball / hero), shaded separately"""
    s = 1 if upper else -1; Ri = R - th; gr = math.radians(g); out = [(0, s * R)]
    for k in range(1, rings + 1):
        lat = math.radians(lerp(90, g + 2.5, k / rings)); out.append((R * math.cos(lat), s * R * math.sin(lat)))
    out += [(R * .99 * math.cos(gr), s * R * math.sin(gr)), ((R - th * .55) * math.cos(gr), s * (R * math.sin(gr) - th * .12))]
    if not inner: out.append((0, s * (R * math.sin(gr) - th * .12)))           # hidden plug (closed ball)
    ob = lathe(out, n); ib = None
    if inner:
        caps = [f for f in ob.faces if len(f.verts) > 4]; bmesh.ops.delete(ob, geom=caps, context='FACES_ONLY')
    if inner:
        pr = [(Ri * math.cos(math.radians(lerp(g + 1, 90, k / rings))), s * Ri * math.sin(math.radians(lerp(g + 1, 90, k / rings)))) for k in range(rings)] + [(0, s * Ri)]
        ib = lathe([(Ri * .99, s * (R * math.sin(gr) - th * .1))] + pr, n)
        caps = [f for f in ib.faces if len(f.verts) > 4]; bmesh.ops.delete(ib, geom=caps, context='FACES_ONLY')
        bmesh.ops.reverse_faces(ib, faces=list(ib.faces))
    return ob, ib

def _ball_sh(col, base, Cw, R, kind='outer', spec=True):
    u = PAL.u(col)
    def sh(f):
        cen = f.calc_center_median(); dist = (cen - Cw).length
        if kind == 'shell' and dist < R * .955:                                  # inside of an open shell
            return [(PAL.u('cream'), clamp(.8 + .05 * l.vert.normal.y, .04, .96)) for l in f.loops]
        out = []
        for l in f.loops:
            nrm = l.vert.normal
            v = base + .2 * nrm.y + (.38 * max(0, nrm.dot(SPEC)) ** 14 if spec else 0)

            out.append((u, clamp(v, .04, .96)))
        return out
    return sh

def catch_ball(P, c, tier='mint', s=1.0, yaw=0.0, pitch=0.0, lod=1, open_deg=0.0):
    """the catch ball, resting on c (bottom), diameter 1.2 * s"""
    up, upv, lo, lov, rimc, trim, trimc = BALL_STYLE.get(tier, BALL_STYLE['mint'])
    R = .6; th = .07; g = 3.0
    n, rings = ((24, 7) if lod == 0 else (14, 4) if lod == 1 else (8, 2))
    opened = open_deg > 0
    hinge = V3((0, 0, R * .98))
    def M_part(bm, upper):
        if upper and opened:
            bmesh.ops.rotate(bm, cent=hinge, matrix=Matrix.Rotation(math.radians(open_deg), 3, 'X'), verts=bm.verts)
        bmesh.ops.rotate(bm, cent=V3(), matrix=Matrix.Rotation(math.radians(-BALL_TILT), 3, 'X'), verts=bm.verts)
        return T(T(bm, (0, R, 0)), (0, 0, 0), 0, pitch, 0, s)
    def place(bm, upper):
        return T(M_part(bm, upper), c, yaw)
    Cw = V3(c) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ (Matrix.Rotation(math.radians(pitch), 3, 'X') @ V3((0, R * s, 0)))
    Rs = R * s
    for upper, col, v in ((True, up, upv), (False, lo, lov)):
        ob, ib = _shell(R, g, th, upper, n, rings, opened)
        P.add(place(ob, upper), _ball_sh(col, v, Cw, Rs, 'outer'), smooth=True)
        if ib: P.add(place(ib, upper), S('cream', base=.84, up=.05, jit=0), smooth=True)
    P.add(place(ring_seg(R - th * .9, R - th * .2, -R * .07, R * .07, 0, 360, n), False), S('steel', base=.72, up=0, jit=0))   # silver seam core
    if opened:                                                                     # soft glow inside the lower shell
        P.gadd(place(lathe([(R * .8, 0), (R * .55, .04), (0, .05)], max(8, n // 2)), False), 'gem')
        P.gadd(place(T(ball(R * .22, 8, 4), (0, R * .28, 0)), False), 'gem')
    # front latch: raised pill straddling the seam + gem + light ring
    lt = rbox((R * .36, R * .62, R * .2), R * .1, 2 if lod < 2 else 1)
    P.add(place(T(lt, (0, 0, -R * .96)), False), _ball_sh(rimc if tier == 'gold' else 'wall', .78, Cw, Rs, 'flat'), smooth=True)
    gem = T(lathe([(0, -R * .13), (R * .1, 0), (0, R * .13)], 4 if lod == 2 else 6), (0, 0, -R * 1.08), 0, 90)
    P.gadd(place(gem, False), 'gem')
    if lod < 2:
        P.gadd(place(T(torus(R * .16, R * .022, 12, 3), (0, 0, -R * 1.07), 0, 90), False), 'gem')
    # back hinge: two knuckles on the lower shell, one on the upper, a pin
    for x, upper in ((-R * .16, False), (0.0, True), (R * .16, False)):
        if lod == 2 and upper: continue
        k = T(cyl(R * .075, R * .14, 6 if lod == 2 else 8), (0, -R * .07, 0), 0, 0, 90)
        P.add(place(T(k, (x, 0, R * .99)), upper), S('steel', base=.6, up=.1, jit=0), smooth=True)
    if lod < 2:                                                                     # hinge leaves on both shells
        for upper, y in ((False, -R * .12), (True, R * .12)):
            P.add(place(T(rbox((R * .44, R * .2, R * .06), R * .025, 1), (0, y, R * .975)), upper), S('steel', base=.55, up=.1, jit=0))
    if lod == 2: return
    # trim pattern on the upper shell (seam-local frame, before the tilt)
    decals = []
    if trim == 'stripes':
        for sx in (-1, 1):
            decals.append(sphere_decal([(sx * .14, -1.25), (sx * .3, -1.25), (sx * .3, 1.25), (sx * .14, 1.25)][::sx], (0, 1, 0), (1, 0, 0), R, .045))
    elif trim == 'chevron':
        decals.append(sphere_decal([(-.62, -.34), (0, .2), (.62, -.34), (.62, -.1), (0, .44), (-.62, -.1)][::-1], (0, .8, -.6), (1, 0, 0), R, .05))
    elif trim == 'star':
        st = [(math.cos(math.pi / 2 + q * math.pi / 5) * (.4 if q % 2 == 0 else .17), math.sin(math.pi / 2 + q * math.pi / 5) * (.4 if q % 2 == 0 else .17)) for q in range(10)]
        decals.append(sphere_decal(st, (0, .95, -.3), (1, 0, 0), R, .06))
        decals.append(sphere_decal([(math.cos(t) * .07, math.sin(t) * .07) for t in [q * math.tau / 8 for q in range(8)]], (0, .95, -.3), (1, 0, 0), R, .08))
    for bm in decals:
        P.add(place(bm, True), S(trimc, base=.88 if trimc == 'wall' else .3 if trimc == 'dark' else .66, up=.15, jit=0))
    # small raised Bloom Paw on the upper shell's right side (faces out, upright)
    d = V3((.8, .45, -.4)).normalized(); t1 = V3((0, 1, 0)).cross(d).normalized()
    pad = [(math.cos(t) * .62, math.sin(t) * .46) for t in [q * math.tau / 14 for q in range(14)]]
    pad = [(x * (1 - .18 * max(0, -y) / .46) * .28, -(y - .38) * .28) for x, y in pad]
    pcol = 'gold' if tier == 'gold' else 'wall'
    P.add(place(sphere_decal(pad[::-1], d, t1, R, .05, .08), True), S(pcol, base=.9 if pcol == 'wall' else .65, up=.1, jit=0))
    for a, L, cx, cy in ((-38, .78, -.5, .22), (0, .9, 0, .38), (38, .78, .5, .22)):
        lp = [(x * .28, -y * .28) for x, y in leaf_poly(L, .2, 4, a, (cx, cy))]
        P.add(place(sphere_decal(lp[::-1], d, t1, R, .05, .08), True), S(pcol, base=.9 if pcol == 'wall' else .65, up=.1, jit=0))

def catch_ball_prop(tier='mint', lod=0, open_deg=0.0, s=1.6):
    P = Prop('CatchBall_%s_l%d%s' % (tier, lod, '_open' if open_deg else ''))
    catch_ball(P, (0, 0, 0), tier, s, 0, 0, lod, open_deg)
    return P

def ball_lineup(lod=0):
    """QA sheet prop: the four tiers in a row + an open one"""
    P = Prop('BallLineup%d' % lod)
    for k, t in enumerate(TIERS):
        catch_ball(P, (-3.9 + k * 2.6, 0, 0), t, 1.6, 0, 0, lod)
    catch_ball(P, (6.5, 0, 0), 'coral', 1.6, 0, 0, lod, 70)
    return P

# ================================================================== TREES v2 (references/stylised_trees.md method)
# Skeleton + Skin-modifier trunks (smooth welded junctions), crowns of many distinct leaves (no faceted lumps).
def skin_mesh(nodes, edges, sub=1):
    """branching skeleton -> one smooth trunk mesh via Blender's Skin + Subdivision modifiers (Roblox space)"""
    import bpy
    me = bpy.data.meshes.new('_skin'); me.from_pydata([n[0] for n in nodes], edges, []); me.update()
    ob = bpy.data.objects.new('_skin', me); bpy.context.scene.collection.objects.link(ob)
    sk = ob.modifiers.new('skin', 'SKIN'); sk.use_smooth_shade = True; sk.branch_smoothing = .6
    sv = me.skin_vertices[0].data
    kids = {b for a, b in edges}
    for i, n in enumerate(nodes):
        sv[i].radius = (n[1], n[1]); sv[i].use_root = (i not in kids)          # one root per strand
    sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = sub; sd.render_levels = sub
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(res)
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(me); bpy.data.meshes.remove(res)
    bm.normal_update(); return bm

class Skel:
    def __init__(self): self.N = []; self.E = []
    def add(self, p, r, parent=None):
        self.N.append((tuple(p), r)); i = len(self.N) - 1
        if parent is not None: self.E.append((parent, i))
        return i
    def grow(self, parent, d, L, r0, r1, n, rng, bend=(0, .08, 0), wob=.12):
        i = parent; p = V3(self.N[parent][0]); d = V3(d).normalized()
        for k in range(1, n + 1):
            d = (d + V3(bend) + V3((rng.uniform(-wob, wob), rng.uniform(-wob, wob) * .5, rng.uniform(-wob, wob)))).normalized()
            p = p + d * (L / n); i = self.add(p, lerp(r0, r1, k / n), i)
        return i

def wood_sh(y0, y1, a=.3, b=.62):
    u = PAL.u('wood')
    return lambda f: [(u, clamp(lerp(a, b, clamp((l.vert.co.y - y0) / max(1e-3, y1 - y0))) + .1 * l.vert.normal.y
                              + (nz(l.vert.co.x * 2, l.vert.co.y * .4, l.vert.co.z * 2, 1, 3) - .5) * .12, .04, .96)) for l in f.loops]

def clump(c, r, seed, sub=2, sq=.82, lump=.16):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    off = V3((seed * 3.1, seed * 1.7, -seed * 2.3))
    for v in bm.verts:
        d = v.co.normalized(); k = 1 + lump * MN.noise(d * 1.8 + off) + lump * .5 * MN.noise(d * 4.0 - off)
        v.co = V3((d.x * r * k, d.y * r * sq * k, d.z * r * k)) + V3(c)
    bm.normal_update(); return bm

def leaf_card(bm, base, dirv, nrm, L, W, crease=.12, two=True):
    """one leaf: rounded card (base, two shoulders, rounded tip) with a raised centre crease; two-sided"""
    side = nrm.cross(dirv).normalized()
    prof = [(0, 0), (.22, .34), (.5, .46), (.78, .44), (.94, .28), (1, 0)]
    curl = lambda t, w: nrm * (L * .1 * math.sin(math.pi * t) - L * .06 * abs(w))      # leaf arches + edges curl down
    pts = [base + dirv * L * t + side * W * w + curl(t, w) for t, w in prof] + [base + dirv * L * t - side * W * w + curl(t, -w) for t, w in prof[-2:0:-1]]
    mid = base + dirv * L * .52 + nrm * L * crease
    nv = len(pts)
    for two_ in ((False, True) if two else (False,)):
        off = -nrm * .02 if two_ else V3()
        vs = [bm.verts.new(p + off) for p in pts]; m = bm.verts.new(mid + off)
        for i in range(nv):
            f = bm.faces.new((vs[i], vs[(i + 1) % nv], m)); f.normal_update()
            if (f.normal.dot(nrm) < 0) != two_: f.normal_flip()

def leaf_sh(col, y0, y1, a=.3, b=.72, seed=0):
    u = PAL.u(col); rr = random.Random(seed)
    def sh(f):
        j = rr.uniform(-.05, .05); out = []
        for l in f.loops:
            t = clamp((l.vert.co.y - y0) / max(1e-3, y1 - y0))
            out.append((u, clamp(lerp(a, b, t) + .14 * max(0, l.vert.normal.y) + j, .04, .96)))
        return out
    return sh

def fiddle_fig(seed=1, h=9.0, col='mint'):
    """fiddle-leaf fig: tapered pot, slender Skin trunk with 3-4 branches, ~55 large glossy rounded leaves on short
    petioles (curved two-sided cards with a centre crease), shaded dark at the stem to light at the tip"""
    P = Prop('FiddleFig%d' % seed); rng = random.Random(seed)
    pot(P, (0, 0, 0), 1.5, 2.5, col, 0)
    sk = Skel(); r0 = sk.add((0, 2.2, 0), .26)
    top = sk.grow(r0, (0, 1, 0), h * .55, .24, .13, 4, rng, bend=(0, .02, 0), wob=.06)
    tips = [top]
    nb = 3 if seed % 2 else 4
    trunk_nodes = list(range(1, len(sk.N)))
    for k in range(nb):
        a = k * math.tau / nb + rng.uniform(-.3, .3); bi = trunk_nodes[1 + k % (len(trunk_nodes) - 1)]
        tips.append(sk.grow(bi, (math.cos(a), .9, math.sin(a)), h * rng.uniform(.25, .34), .12, .06, 3, rng, bend=(0, .1, 0)))
    tips[0] = sk.grow(top, (0, 1, 0), h * .18, .12, .06, 2, rng)
    P.add(skin_mesh(sk.N, sk.E, 1), wood_sh(2.0, h), smooth=True)
    bm = bmesh.new(); y0 = h * .4; y1 = h + 1.5
    for ti in tips:
        node_chain = [ti]
        e = {b: a for a, b in sk.E}
        while len(node_chain) < 4 and node_chain[-1] in e: node_chain.append(e[node_chain[-1]])
        for ni in node_chain[:3]:
            p = V3(sk.N[ni][0])
            for k in range(6 if ni == ti else 5):
                a = rng.uniform(0, math.tau); out = V3((math.cos(a), rng.uniform(.1, .9), math.sin(a))).normalized()
                pet = p + out * .35
                P.add(tube([p, pet], [.04, .03], sides=3), S('leaf', base=.35, jit=0))
                dirv = (out + V3((0, -.25, 0))).normalized(); nrm = (V3((0, 1, 0)) - dirv * dirv.y).normalized()
                tw = rng.uniform(-.5, .5); nrm = (nrm + dirv.cross(nrm) * tw).normalized()
                leaf_card(bm, pet, dirv, nrm, rng.uniform(1.4, 1.9), rng.uniform(.8, 1.0), .08)
    bm.normal_update(); P.add(bm, leaf_sh('leaf', y0, y1, .32, .74, seed), smooth=True)
    return P

def olive_tree(seed=2, h=8.0, col='teal'):
    """olive / ficus: footed pot, three thin stems braided round each other (twisting Skin trunk), a dense soft crown of
    many small leaves over a dark core (two masses), smooth shading"""
    P = Prop('OliveTree%d' % seed); rng = random.Random(seed)
    pot(P, (0, 0, 0), 1.35, 1.8, col, 1)
    sk = Skel(); hub = None
    for k in range(3):
        prev = sk.add((math.cos(k * math.tau / 3) * .12, 1.9, math.sin(k * math.tau / 3) * .12), .11)
        for j in range(1, 9):
            t = j / 8; a = k * math.tau / 3 + t * math.tau * 1.25
            r = .42 * (1 - t * .55)
            prev = sk.add((math.cos(a) * r, 1.9 + t * h * .5, math.sin(a) * r), .1 - t * .03, prev)
        if hub is None: hub = prev
    P.add(skin_mesh(sk.N, sk.E, 1), wood_sh(1.9, h * .6, .28, .55), smooth=True)
    yt = 1.9 + h * .5
    for c, r in (((0, yt + 1.7, 0), 1.9), ((.9, yt + .9, .5), 1.35), ((-.8, yt + 1.0, -.4), 1.3)):
        leaf_mass(P, c, r, 'leaf', seed * 7 + int(r * 10), density=7.0, leaf=.55, two=True, core=0)
    return P

def leaf_mass(P, c, r, col, seed, density=1.0, sq=.8, leaf=1.2, two=False, core=.86):
    """canopy mass: dark displaced core + many leaf cards at random spots (gaussian directions, random roll + size),
    pointing out and drooping; shaded dark interior -> light tips, lit top, darker underside"""
    rng = random.Random(seed); c = V3(c)
    if core > 0: P.add(clump(c, r * core, seed, sub=2 if r < 2.5 else 1, sq=sq, lump=.12), leaf_sh(col, c.y - r, c.y + r, *((.45, .7) if col == 'berry' else (.1, .4)), seed), smooth=True)
    n = int(density * 4.6 * r * r) + 14
    bm = bmesh.new(); off = V3((seed * 1.7, seed * .3, -seed * 2.1))
    for k in range(n):
        while True:
            d = V3((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
            if d.y > -.35 or rng.random() < .25: break
        lump = 1 + .18 * MN.noise(d * 1.8 + off)
        base = c + V3((d.x, d.y * sq, d.z)) * r * .9 * lump * rng.uniform(.9, 1.02)
        nrm = V3((d.x, d.y / max(sq, .3), d.z)).normalized()
        dn = V3((0, -1, 0)) - nrm * (-nrm.y); dn = dn.normalized() if dn.length > 1e-3 else V3((1, 0, 0))
        side0 = nrm.cross(dn).normalized(); a = rng.uniform(-.9, .9)
        dirv = (nrm * rng.uniform(.35, .6) + dn * math.cos(a) * .8 + side0 * math.sin(a) * .8).normalized()
        L = leaf * rng.uniform(.75, 1.25); W = L * rng.uniform(.5, .62)
        side = nrm.cross(dirv).normalized() * W / 2; mid = base + dirv * L * .45 + nrm * L * .1; tip = base + dirv * L
        f = bm.faces.new([bm.verts.new(p) for p in (base, mid - side, tip, mid + side)]); f.normal_update()
        if f.normal.dot(nrm) < 0: f.normal_flip()
        if two:
            g = bm.faces.new([bm.verts.new(p - nrm * .01) for p in (base, mid + side, tip, mid - side)]); g.normal_update()
            if g.normal.dot(nrm) > 0: g.normal_flip()
    lo_, hi_ = (.62, .94) if col == 'berry' else (.3, .8)
    bm.normal_update(); P.add(bm, leaf_sh(col, c.y - r * sq, c.y + r * sq, lo_, hi_, seed + 1))

def park_tree(seed=1, h=18.0, col='leaf', name=None):
    """rounded park tree: Skin trunk (flared base, 4 roots dipping into the lawn, 3-4 limbs that fork) and a crown of
    overlapping leaf masses pulled to one canopy layer and bridged into one silhouette"""
    P = Prop(name or 'ParkTree%d' % seed); rng = random.Random(seed)
    sk = Skel(); b = sk.add((0, -.8, 0), h * .085)
    t = sk.grow(b, (rng.uniform(-.1, .1), 1, rng.uniform(-.1, .1)), h * .42, h * .07, h * .045, 4, rng, bend=(0, .02, 0), wob=.07)
    trunk = list(range(1, len(sk.N)))
    for k in range(4):                                                         # roots from the first trunk node, dipping
        a = k * math.tau / 4 + rng.uniform(-.3, .3)
        sk.grow(trunk[0], (math.cos(a), -.35, math.sin(a)), h * .14, h * .045, h * .012, 2, rng, bend=(0, -.25, 0), wob=.05)
    tips = []; nl = 3 + seed % 2
    for k in range(nl):
        a = k * math.tau / nl + rng.uniform(-.35, .35)
        m = sk.grow(t, (math.cos(a), .8, math.sin(a)), h * .22, h * .04, h * .026, 3, rng, bend=(0, .05, 0))
        for q in (-1, 1):
            tips.append(sk.grow(m, (math.cos(a + q * .5), .9, math.sin(a + q * .5)), h * .13, h * .022, h * .012, 2, rng))
    tips.append(sk.grow(t, (0, 1, 0), h * .2, h * .03, h * .015, 2, rng))
    P.add(skin_mesh(sk.N, sk.E, 1), wood_sh(-.8, h * .7, .25, .58), smooth=True)
    ch = sum(sk.N[i][0][1] for i in tips) / len(tips) + h * .06
    cs = []
    for i in tips:
        p = V3(sk.N[i][0]); r = h * rng.uniform(.13, .19)
        hx, hz = V3(sk.N[t][0]).x, V3(sk.N[t][0]).z
        p = V3((lerp(p.x, hx, .3), lerp(p.y, ch, .6) + h * .03, lerp(p.z, hz, .3))); cs.append((p, r))
    hub = V3((V3(sk.N[t][0]).x, ch + h * .12, V3(sk.N[t][0]).z)); cs.append((hub, h * .26))
    for i, (cc, r) in enumerate(cs):
        leaf_mass(P, cc, r, col, seed * 31 + i, density=.8, leaf=h * .095, core=.64)
    return P

def blossom_park(seed=2, h=14.0):
    return park_tree(seed, h, 'berry', 'PinkParkTree%d' % seed)   # a tree (trunk hull), not a blossom decal
