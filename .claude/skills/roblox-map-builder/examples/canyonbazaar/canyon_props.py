# Sunspire Canyon Bazaar prop kit (desert canyon oasis market at dusk).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: a caravan bazaar in a red-rock canyon: cream sandstone ashlar, terracotta pottery, dark palm timber, rope and
# wicker. Saturated colour ONLY on stretched shade cloths + goods (teal, saffron, plum), the turquoise oasis water and
# a few warm brass lanterns. No flags, banners or pennants: every cloth is stretched flat over a frame.
# Signature edge detail: a low sandstone parapet module with a cut arched niche holding a glowing brass lantern, repeated
# along the canyon foot and every ledge. Shared base: a two-course sandstone dais with a chamfered cap.
# Machinery (Prop, S, blob, materials, to_kit, arch_*, bool_diff) from the skill's grove module, helpers (T, bar, log,
# lathe, torus, sag, ashlar) from the medieval example; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, spike, tube, hull, rock_pts, nz, clamp

PAL = Palette({
    'sand':    ('#946a40', '#e6be86', '#fce4b8'),     # canyon floor sand
    'stone':   ('#7e5c40', '#dcbf96', '#fbedd0'),     # cream sandstone ashlar, paving, steps
    'cliff':   ('#3e120c', '#a4301c', '#e0603a'),     # red-orange cliff strata
    'cliff2':  ('#7a3a0e', '#e47a26', '#ffb468'),     # orange strata band / mesas
    'terra':   ('#5e2614', '#b85a32', '#ec9a68'),     # terracotta pots, tiles
    'wood':    ('#22140c', '#4f3020', '#87593b'),     # dark palm timber
    'rope':    ('#6a4a26', '#b48a54', '#e8c992'),     # rope, wicker, straw
    'teal':    ('#03505c', '#0eb4bc', '#7af6ee'),     # teal cloth (accent)
    'saffron': ('#8a4602', '#f6a812', '#ffe470'),     # saffron cloth / spice (accent)
    'plum':    ('#3c0848', '#a0249e', '#ea7ae6'),     # plum cloth / rugs (accent)
    'water':   ('#036a78', '#12ccd2', '#9cfff2'),     # turquoise oasis water
    'palm':    ('#28401a', '#5f8a2c', '#b6d46a'),     # palm fronds, agave
    'scrub':   ('#4a4a2c', '#8a8a56', '#c8c496'),     # dry olive scrub
    'brass':   ('#5a3608', '#c08a2a', '#ffd88a'),     # brass lanterns, fittings
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'lamp': '#ffa23c', 'fire': '#ff6a1e', 'temple': '#ffb43c', 'relic': '#c27cff'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 4.0, 'fire': 4.0, 'temple': 7.0, 'relic': 3.0})
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, log, lathe, torus, sag, h01 = B.T, B.bar, B.log, B.lathe, B.torus, B.sag, B.h01
ashlar, ash_sh = B.ashlar, B.ash_sh
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ shared pieces
def dais(P, w, d, h=1.0, seed=0, col='stone'):
    """SHARED BASE: two-course sandstone dais (ashlar faces) with a chamfered cap, sunk 0.5 below the origin"""
    for (L, z, yaw) in ((w, -d / 2, 0), (w, d / 2, 180), (d, w / 2, -90), (d, -w / 2, 90)):
        pos = (0, -.5, z) if yaw in (0, 180) else (z, -.5, 0)
        P.add(T(ashlar(L, h + .5 - .25, 2.2, .7, seed=seed + int(L), depth=.06, ins=.06), pos, yaw), ash_sh(col, base=.6, var=.06, grime=.1))
    P.add(T(box((w - .2, h + .5, d - .2)), (0, (h - .5) / 2, 0)), S(col, base=.5, jit=.01))
    P.add(T(box((w + .3, .3, d + .3), .12), (0, h - .1, 0)), S(col, base=.7, up=.12, jit=.02))

def cloth_sheet(P, x0, x1, z0, z1, y0, y1, col, stripes=0, col2=None, nx=6, nzz=4, drop=.35, hem=True):
    """a cloth stretched flat over a frame: corners at (x0|x1, z0|z1), height y0 at z0 -> y1 at z1, a soft sag in the
    middle, double-sided, rolled hem along the edges; stripes = alternate colour bands across x"""
    bm = bmesh.new(); V = {}
    def p(i, j):
        u, v = i / nx, j / nzz
        y = lerp(y0, y1, v) - drop * math.sin(u * math.pi) * math.sin(v * math.pi)
        return (lerp(x0, x1, u), y, lerp(z0, z1, v))
    for i in range(nx + 1):
        for j in range(nzz + 1): V[i, j] = bm.verts.new(p(i, j))
    for i in range(nx):
        for j in range(nzz):
            f = bm.faces.new((V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
            f.material_index = (i * stripes // nx) % 2 if stripes else 0
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.08)
    u1, u2 = PAL.u(col), PAL.u(col2 or col)
    rng = random.Random(int(abs(x0 * 7 + z0 * 3)))
    def sh(f):
        u = u2 if f.material_index else u1
        v = .52 + .16 * f.normal.y + rng.uniform(-.02, .02) if f.normal.y > -.5 else .32
        return [(u, clamp(v, .04, .96))] * len(f.loops)
    P.add(bm, sh)
    if hem:
        for (a, b) in (((0, 0), (nx, 0)), ((0, nzz), (nx, nzz)), ((0, 0), (0, nzz)), ((nx, 0), (nx, nzz))):
            n = max(a[0], b[0]) - min(a[0], b[0]) + max(a[1], b[1]) - min(a[1], b[1])
            pts = [Vector(p(lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n))) for k in range(n + 1)]
            P.add(tube(pts, .1, sides=5), S(col, base=.3, up=.1, jit=.01))

def brass_lantern(P, c, s=1.0, key='lamp', hang=True):
    """pierced brass lantern: domed cap with a finial + ring, six ribs round a glowing core, a drip base"""
    x, y, z = c; k = s
    P.add(T(lathe([(0, 0), (.38 * k, .05 * k), (.45 * k, .2 * k), (.3 * k, .32 * k)], n=8), (x, y, z)), S('brass', base=.45, up=.15, jit=.02))
    P.add(T(lathe([(.46 * k, 0), (.52 * k, .08 * k), (.3 * k, .45 * k), (.12 * k, .62 * k), (.05 * k, .8 * k), (0, .85 * k)], n=8), (x, y + 1.3 * k, z)), S('brass', base=.55, up=.15, jit=.02))
    for i in range(6):
        a = i * math.tau / 6
        pts = [Vector((x + math.cos(a) * r * k, y + yy * k, z + math.sin(a) * r * k)) for r, yy in ((.3, .3), (.5, .75), (.46, 1.32))]
        P.add(tube(pts, .045 * k, sides=4), S('brass', base=.5, up=.1, jit=.02))
    P.gadd(T(lathe([(.25 * k, 0), (.42 * k, .45 * k), (.38 * k, .95 * k), (0, 1.0 * k)], n=6), (x, y + .32 * k, z)), key)
    if hang:
        P.add(T(torus(.14 * k, .035 * k, 8, 4), (x, y + 2.25 * k, z), 0, 0, 90), S('brass', base=.5, jit=.02))

# ------------------------------------------------------------------ market
def pot(P, c, h=1.6, r=.6, seed=0, col='terra', band='teal', tilt=0.0, yaw=0.0, kind=0):
    """terracotta jar (amphora / squat jar / long-necked) with a painted band and a rim"""
    x, y, z = c
    if kind == 0: prof = [(0, 0), (r * .45, 0), (r * .9, h * .25), (r, h * .5), (r * .7, h * .78), (r * .32, h * .86), (r * .38, h), (r * .3, h), (0, h * .9)]
    elif kind == 1: prof = [(0, 0), (r * .7, 0), (r * 1.1, h * .35), (r * .95, h * .7), (r * .65, h * .85), (r * .72, h), (r * .6, h), (0, h * .85)]
    else: prof = [(0, 0), (r * .5, 0), (r, h * .3), (r * .55, h * .55), (r * .18, h * .7), (r * .2, h), (r * .28, h * 1.02), (0, h * .95)]
    rng = random.Random(seed)
    P.add(T(lathe(prof, n=10), (x, y, z), yaw, tilt), S(col, base=.52 + rng.uniform(-.06, .06), up=.12, jit=.02, seed=seed))
    yb = h * (.5 if kind != 2 else .3)
    rb = (r * (1.0 if kind == 0 else 1.05 if kind == 1 else 1.0)) * 1.01
    P.add(T(T(torus(rb, .06, 12, 3), (0, yb, 0)), (x, y, z), yaw, tilt), S(band, base=.5, jit=.02))

def goods_pots(P, x, y, z, seed):
    rng = random.Random(seed)
    for i in range(3):
        pot(P, (x + (i - 1) * .9, y, z + rng.uniform(-.15, .15)), rng.uniform(.8, 1.2), rng.uniform(.32, .42), seed + i,
            band=('teal', 'saffron', 'plum')[i % 3], kind=rng.randint(0, 2))

def fruit_pile(P, x, y, z, seed, col='saffron'):
    """wicker basket heaped with fruit"""
    P.add(T(lathe([(0, 0), (.55, 0), (.8, .45), (.85, .5), (0, .5)], n=10), (x, y, z)), S('rope', base=.5, up=.1, jit=.03))
    P.add(T(torus(.82, .07, 10, 3), (x, y + .48, z)), S('rope', base=.38, jit=.02))
    rng = random.Random(seed)
    for k in range(7):
        a = k * 2.4; r = .45 * math.sqrt((k + .5) / 7)
        P.add(T(blob(.24, seed * 13 + k, n=10, sq=.95), (x + math.cos(a) * r, y + .55 + (.18 if k < 2 else 0), z + math.sin(a) * r)), S(col, base=.55 + rng.uniform(-.08, .08), up=.2, jit=.04))

def stall(cloth='teal', seed=1, w=8.0, d=6.0, goods='pots'):
    """market stall: sandstone step, four palm-timber posts with braces, a striped shade cloth stretched flat over a
    beam frame (tied at the corners), a plank counter with a carved front and a draped rug, goods on top, shelf behind"""
    P = Prop('Stall_%s%d' % (cloth.capitalize(), seed)); rng = random.Random(seed)
    dais(P, w + 1.2, d + 1.0, .5, seed)
    hf, hb = 7.0, 7.8
    for sx in (-1, 1):
        for sz, h in ((-1, hf), (1, hb)):
            x, z = sx * w / 2, sz * d / 2
            P.add(T(box((.42, h, .42), .06), (x, .5 + h / 2, z)), S('wood', base=.42, up=.06, jit=.02))
            P.add(T(cyl(.38, .35, 8, .05), (x, .45, z)), S('stone', base=.5, up=.1, jit=.02))
            P.add(T(torus(.3, .07, 8, 3), (x, .5 + h - .6, z)), S('rope', base=.5, jit=.02))
        P.add(bar((sx * w / 2, .5 + hf - .1, -d / 2), (sx * w / 2, .5 + hb - .1, d / 2), .34, .34), S('wood', base=.38, jit=.01))
        P.add(bar((sx * w / 2, .5 + hf - 1.6, -d / 2), (sx * w / 2, .5 + hf - .2, -d / 2 + 1.4), .2, .2), S('wood', base=.36, jit=.01))
    for sz, h in ((-1, hf), (1, hb)):
        P.add(bar((-w / 2 - .3, .5 + h - .1, sz * d / 2), (w / 2 + .3, .5 + h - .1, sz * d / 2), .34, .34), S('wood', base=.4, jit=.01))
    alt = {'teal': 'stone', 'saffron': 'terra', 'plum': 'stone'}[cloth]
    cloth_sheet(P, -w / 2 - .4, w / 2 + .4, -d / 2 - .5, d / 2 + .3, .5 + hf + .18, .5 + hb + .18, cloth, stripes=6, col2=alt, nx=6, nzz=3, drop=.3)
    # counter
    cz = -d / 2 + 1.1
    P.add(T(box((w - 1.0, .22, 1.5), .06), (0, 3.1, cz)), S('wood', base=.55, up=.12, jit=.02))
    P.add(T(box((w - 1.2, 2.6, .25), .04), (0, 1.8, cz - .55)), S('wood', base=.36, jit=.01))
    for k in range(4):                                                          # carved front panels
        xx = -w / 2 + .6 + (w - 1.2) * (k + .5) / 4
        P.add(T(box(((w - 1.2) / 4 - .4, 1.8, .12), .04), (xx, 1.8, cz - .7)), S('wood', base=.5, up=.06, jit=.02))
    rug_c = 'plum' if cloth != 'plum' else 'saffron'
    rug = bmesh.new()                                                           # rug draped over the counter front
    rw = 2.6; pts = [(3.25, cz + .4), (3.32, cz - .2), (3.2, cz - .72), (2.0, cz - .86), (.9, cz - .8)]
    Vs = [[rug.verts.new((xx, yy, zz)) for (yy, zz) in pts] for xx in (-rw / 2 + 1.2, rw / 2 + 1.2)]
    for i in range(len(pts) - 1): rug.faces.new((Vs[0][i], Vs[0][i + 1], Vs[1][i + 1], Vs[1][i]))
    bmesh.ops.solidify(rug, geom=list(rug.faces), thickness=.07)
    P.add(rug, S(rug_c, base=.5, up=.1, jit=.03))
    for yy in (2.4, 1.6):
        P.add(T(box((rw + .02, .12, .1)), (1.2, yy, cz - .86 + (2.4 - yy) * .05)), S('saffron' if rug_c == 'plum' else 'teal', base=.55, jit=.01))
    # goods
    if goods == 'pots': goods_pots(P, -1.5, 3.2, cz, seed)
    elif goods == 'fruit': fruit_pile(P, -1.8, 3.2, cz, seed); fruit_pile(P, 0.2, 3.2, cz, seed + 1, 'terra')
    else:
        for i, c in enumerate(('saffron', 'terra', 'plum')):
            x = -2.4 + i * 1.3
            P.add(T(lathe([(0, 0), (.5, 0), (.55, .4), (.45, .48), (0, .5)], n=10), (x, 3.2, cz)), S('rope', base=.5, jit=.02))
            P.add(T(lathe([(.48, 0), (.3, .3), (0, .45)], n=10), (x, 3.65, cz)), S(c, base=.55, up=.15, jit=.02))
    # back shelf with jars
    P.add(T(box((w - 1.0, .2, 1.0), .05), (0, 3.6, d / 2 - .8)), S('wood', base=.5, up=.1, jit=.01))
    for sx in (-1, 1): P.add(bar((sx * (w / 2 - .7), 3.5, d / 2 - .4), (sx * (w / 2 - .7), 3.5, d / 2 - 1.2), .2, .3), S('wood', base=.35, jit=.01))
    for i in range(5):
        pot(P, (-w / 2 + 1.2 + i * (w - 2.4) / 4, 3.7, d / 2 - .8), .9, .3, seed * 5 + i, band=('teal', 'saffron', 'plum')[i % 3], kind=(i + seed) % 3)
    # sacks by the side
    for k, c in enumerate(('saffron', 'terra')):
        x = w / 2 - .4 + .2 * k; z = -d / 2 + 2.4 + k * 1.1
        P.add(T(lathe([(0, 0), (.5, 0), (.62, .4), (.55, .9), (.42, 1.05), (.5, 1.15), (0, 1.1)], n=9), (x, .5, z)), S('rope', base=.55, up=.08, jit=.03))
        P.add(T(lathe([(.42, 0), (.25, .2), (0, .3)], n=8), (x, 1.6, z)), S(c, base=.55, up=.15, jit=.02))
    return P

def shade_sail(span=16.0, depth=12.0, seed=1):
    """street shade: two pairs of tall palm-timber posts on stone footings either side of the street, a beam frame and
    three stretched cloth panels (teal / saffron / plum) laced to it, guy ropes to stakes. Street runs along Z."""
    P = Prop('ShadeSail%d' % seed); rng = random.Random(seed); h = 11.0
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * span / 2, sz * depth / 2
            P.add(T(cyl(.7, .9, 8, .1, y0=-.4), (x, 0, z)), S('stone', base=.55, up=.1, jit=.02))
            P.add(log((x, .4, z), (x, h + .4, z), .3, 7, .24), S('wood', base=.42, jit=.02))
            for yy in (h * .35, h - .6): P.add(T(torus(.3, .07, 8, 3), (x, yy, z)), S('rope', base=.5, jit=.02))
            P.add(T(lathe([(.32, 0), (.38, .15), (.22, .4), (.06, .7), (0, .75)], n=8), (x, h + .4, z)), S('brass', base=.55, up=.15, jit=.02))
            sx2 = x + sx * 3.2
            P.add(tube([Vector((x, h - .8, z)), Vector((sx2, 0, z + sz * .6))], .05, sides=4), S('rope', base=.5, jit=.02))
            P.add(T(box((.25, .9, .25), .04), (sx2, .2, z + sz * .6), 0, sx * 15), S('wood', base=.4, jit=.02))
        P.add(bar((sx * span / 2, h - .1, -depth / 2), (sx * span / 2, h - .1, depth / 2), .32, .32), S('wood', base=.38, jit=.01))
    for sz in (-1, 1):
        P.add(bar((-span / 2 - .3, h + .1, sz * depth / 2), (span / 2 + .3, h + .1, sz * depth / 2), .32, .32), S('wood', base=.4, jit=.01))
    cols = ['teal', 'saffron', 'plum']; rng.shuffle(cols)
    pw = span / 3
    for i, c in enumerate(cols):
        x0 = -span / 2 - .4 + i * pw; x1 = x0 + pw + .8; yo = .35 + i * .28
        cloth_sheet(P, x0, x1, -depth / 2 - .3, depth / 2 + .3, h + yo + .5, h + yo - .2, c, stripes=2 if i == 1 else 0, col2='stone', nx=3, nzz=4, drop=.35)
        for zz in (-depth / 2 - .3, depth / 2 + .3):                           # lacing ropes to the beams
            for xx in (x0 + .4, (x0 + x1) / 2, x1 - .4):
                yy = h + yo + (.5 if zz < 0 else -.2)
                P.add(tube([Vector((xx, yy, zz)), Vector((xx, h + .1, zz + (.3 if zz < 0 else -.3)))], .04, sides=4), S('rope', base=.45, jit=.02))
    return P

def pottery_cluster(seed=1):
    """story cluster: big jars, a toppled amphora, a stack of bowls, a crate"""
    P = Prop('Pots%d' % seed); rng = random.Random(seed)
    for i, (x, z, h, r, k) in enumerate(((-1.2, .3, 2.6, .85, 0), (.8, -.5, 1.9, .8, 1), (.2, 1.3, 1.4, .55, 2), (1.9, .9, 1.2, .5, 1))):
        pot(P, (x, -.1, z), h, r, seed * 9 + i, band=('teal', 'saffron', 'plum', 'teal')[i], kind=k, yaw=rng.uniform(0, 360))
    pot(P, (-.4, .55, -1.6), 2.0, .55, seed + 40, band='saffron', kind=0, tilt=90, yaw=60)
    for k in range(4):                                                          # stacked bowls
        P.add(T(lathe([(0, 0), (.3, 0), (.62 - k * .04, .32), (.56 - k * .04, .34), (0, .14)], n=10), (-2.3, -.1 + k * .2, -.9)), S('terra', base=.5 + k * .04, up=.1, jit=.02))
    crate(P, (2.2, -.1, -1.5), 1.4, 20, seed)
    return P

def crate(P, c, s=1.4, yaw=0.0, seed=0):
    x, y, z = c
    P.add(T(box((s, s, s), .05), (x, y + s / 2, z), yaw), S('rope', base=.42, jit=.02, seed=seed))
    for yy in (.12, s - .12):
        for sz in (-1, 1):
            P.add(T(T(box((s + .08, .18, .1)), (0, yy, sz * s / 2)), (x, y, z), yaw), S('wood', base=.4, jit=.01))
            P.add(T(T(box((.1, .18, s + .08)), (sz * s / 2, yy, 0)), (x, y, z), yaw), S('wood', base=.4, jit=.01))
    for sz in (-1, 1):
        P.add(T(T(box((s * 1.25, .16, .1)), (0, s / 2, sz * s / 2), 0, 0, 45 * sz), (x, y, z), yaw), S('wood', base=.38, jit=.01))

def spice_sacks(seed=1):
    """story cluster: five open spice sacks with rolled rims and heaped spice cones, a brass scale, a scoop"""
    P = Prop('Sacks%d' % seed); rng = random.Random(seed)
    cols = ['saffron', 'terra', 'plum', 'saffron', 'palm']
    for i in range(5):
        a = i * 1.35; r = 1.2 if i else 0
        x, z = math.cos(a) * r, math.sin(a) * r; h = rng.uniform(.9, 1.3)
        P.add(T(lathe([(0, 0), (.55, 0), (.68, h * .4), (.6, h * .85), (.72, h), (.78, h + .12), (.58, h + .15), (0, h)], n=10), (x, -.1, z)), S('rope', base=.55 + rng.uniform(-.06, .06), up=.08, jit=.03))
        P.add(T(lathe([(.6, 0), (.4, .18), (.15, .32), (0, .36)], n=10), (x, h - .05, z)), S(cols[i], base=.55, up=.15, jit=.03))
    P.add(T(lathe([(0, 0), (.25, 0), (.18, .8), (.08, 1.6), (0, 1.65)], n=8), (2.0, -.1, -.6)), S('brass', base=.45, up=.1, jit=.02))   # scale
    P.add(bar((1.2, 1.6, -.6), (2.8, 1.6, -.6), .1, .1), S('brass', base=.6, jit=.02))
    for sx in (-1, 1):
        P.add(T(lathe([(0, 0), (.4, .05), (.45, .15), (0, .12)], n=10), (2.0 + sx * .8, 1.0, -.6)), S('brass', base=.55, up=.1, jit=.02))
        P.add(tube([Vector((2.0 + sx * .8, 1.15, -.6)), Vector((2.0 + sx * .8, 1.6, -.6))], .02, sides=3), S('brass', base=.4, jit=.01))
    P.add(T(box((1.2, .12, 1.2), .03), (2.0, -.05, -.6)), S('wood', base=.45, jit=.01))
    return P

def rug_rack(seed=1):
    """story cluster: timber rack with three patterned rugs hung over the pole, two rolled rugs leaning on it"""
    P = Prop('RugRack%d' % seed); L = 6.0; h = 3.6
    for sx in (-1, 1):
        x = sx * L / 2
        P.add(bar((x, -.2, -.9), (x, h, 0), .25, .25), S('wood', base=.42, jit=.02))
        P.add(bar((x, -.2, .9), (x, h, 0), .25, .25), S('wood', base=.4, jit=.02))
    P.add(log((-L / 2 - .3, h + .05, 0), (L / 2 + .3, h + .05, 0), .14, 7), S('wood', base=.5, up=.1, jit=.02))
    cols = [('plum', 'saffron'), ('teal', 'stone'), ('terra', 'saffron')]
    for i, (c1, c2) in enumerate(cols):
        x0 = -L / 2 + .3 + i * (L - .6) / 3; x1 = x0 + (L - .6) / 3 - .15
        bm = bmesh.new(); prof = [(.4, 1.3), (-.05, 2.6), (-.18, h - .1), (0, h + .22), (.18, h - .1), (.05, 2.4), (-.3, .9)]
        Vv = [[bm.verts.new((xx, y, z)) for (z, y) in prof] for xx in (x0, (x0 + x1) / 2, x1)]
        for a in range(2):
            for j in range(len(prof) - 1):
                f = bm.faces.new((Vv[a][j], Vv[a + 1][j], Vv[a + 1][j + 1], Vv[a][j + 1])); f.material_index = (j + a) % 2
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.08)
        u1, u2 = PAL.u(c1), PAL.u(c2)
        P.add(bm, lambda f, u1=u1, u2=u2: [(u2 if f.material_index else u1, clamp(.5 + .12 * f.normal.y, .04, .96))] * len(f.loops))
        for zz, yy in ((.36, 1.4), (-.26, 1.0)):
            P.add(T(box((x1 - x0, .14, .06)), ((x0 + x1) / 2, yy + .6, zz)), S(c2, base=.6, jit=.01))
    for k, (c, x) in enumerate((('teal', -1.6), ('plum', 1.0))):                # rolled rugs leaning
        P.add(log((x, -.2, 1.9), (x + .3, 3.2, .6), .38, 8), S(c, base=.5, up=.1, jit=.02))
        P.add(T(torus(.39, .05, 8, 3), (x + .15, 1.5, 1.25), 0, 66), S('saffron', base=.55, jit=.02))
    return P

def parapet_niche(L=8.0, seed=1):
    """SIGNATURE: low sandstone wall module (ashlar both faces, chamfered coping, end pilasters) with a cut arched
    niche in the middle holding a glowing brass lantern. Front = -Z."""
    P = Prop('Parapet%d' % int(L)); H = 3.2; th = 1.4
    wall = box((L, H + .6, th)); B.T(wall, (0, (H - .6) / 2, 0))
    cut = G.arch_prism(.8, 1.4, -th / 2 - .2, th / 2 - .5, 0); B.T(cut, (0, .9, 0))
    wall = G.bool_diff(wall, cut)
    P.add(wall, S('stone', base=.55, up=.08, jit=.02, seed=seed))
    for zz, yaw in ((-th / 2 - .01, 0), (th / 2 + .01, 180)):                   # ashlar skins (front skips the niche)
        sk = (lambda x, y: abs(x) < 1.1 and y < 3.15) if yaw == 0 else None
        P.add(T(ashlar(L - 1.6, H - .05, 1.8, .8, seed=seed + yaw, skip=sk, depth=.05, ins=.06), (0, 0, zz), yaw), ash_sh('stone', base=.62, var=.06, grime=.1))
    P.add(T(box((L + .3, .35, th + .45), .12), (0, H + .1, 0)), S('stone', base=.72, up=.12, jit=.02))
    for sx in (-1, 1):
        P.add(T(box((.9, H + .8, th + .4), .08), (sx * (L / 2 - .45), (H + .8) / 2 - .5, 0)), S('stone', base=.5, up=.08, jit=.02))
        P.add(T(box((1.1, .3, th + .6), .1), (sx * (L / 2 - .45), H + .45, 0)), S('stone', base=.7, up=.12, jit=.02))
    fr = G.arch_frame(.8, 1.4, .18, -th / 2 - .12, -th / 2 + .02); B.T(fr, (0, .9, 0))       # niche frame (terra)
    P.add(fr, S('terra', base=.5, up=.1, jit=.02))
    P.add(T(box((1.9, .16, .5), .04), (0, .9, -th / 2 - .05)), S('stone', base=.7, up=.1, jit=.01))
    brass_lantern(P, (0, .98, -.2), .58, hang=False)
    return P

def lantern_post(seed=1, h=7.5):
    """street lantern: sandstone base, timber post with a scroll bracket arm, a hanging pierced brass lantern"""
    P = Prop('LanternPost%d' % seed)
    P.add(T(lathe([(1.0, -.5), (1.0, .4), (.8, .55), (.55, .7), (.5, 1.2), (.62, 1.35), (0, 1.35)], n=8), (0, 0, 0)), S('stone', base=.6, up=.1, jit=.02))
    P.add(T(box((.42, h - 1.2, .42), .08), (0, 1.3 + (h - 1.2) / 2, 0)), S('wood', base=.42, up=.06, jit=.02))
    P.add(T(lathe([(.36, 0), (.42, .15), (.2, .4), (.08, .6), (0, .65)], n=8), (0, h + .1, 0)), S('brass', base=.55, up=.15, jit=.02))
    arm = [Vector((0, h - .4, 0)), Vector((0, h - .1, -.8)), Vector((0, h - .3, -1.7)), Vector((0, h - .7, -2.0))]
    P.add(tube(arm, .1, sides=5), S('brass', base=.48, jit=.02))
    P.add(tube([Vector((0, h - 1.6, 0)), Vector((0, h - .6, -1.2)), Vector((0, h - .45, -1.6))], .07, sides=4), S('brass', base=.45, jit=.02))
    P.add(tube([Vector((0, h - .7, -2.0)), Vector((0, h - 1.4, -2.0))], .03, sides=3), S('brass', base=.4, jit=.02))
    brass_lantern(P, (0, h - 3.55, -2.0), .95)
    return P

# ------------------------------------------------------------------ oasis
def palm(seed=1, h=18.0):
    """date palm: curved ringed trunk, flared root boss, a crown of drooping pinnate fronds, hanging date clusters"""
    P = Prop('Palm%d' % seed); rng = random.Random(seed)
    lean = rng.uniform(-.25, .25); lz = rng.uniform(.05, .22)
    n = 12
    pts = [Vector((math.sin(lean + t * .3) * h * .14 * t * t, h * t, lz * h * t * t)) for t in [k / n for k in range(n + 1)]]
    pts[0].y = -1.2
    P.add(T(lathe([(1.4, -.8), (1.1, 0), (.75, .6), (.6, 1.2), (0, 1.2)], n=9), (0, 0, 0)), S('wood', base=.38, up=.1, jit=.03))
    rad = [.7 - .3 * (k / n) for k in range(n + 1)]
    P.add(tube(pts, rad, sides=8, rough=.06, seed=seed), S('wood', base=.46, up=.04, jit=.05))
    for k in range(1, n):                                                       # ring scars
        P.add(T(torus(rad[k] * 1.04, .09, 8, 3), tuple(pts[k])), S('rope', base=.32, jit=.03))
    top = pts[-1]
    P.add(T(blob(.9, seed, n=14, sq=1.1), tuple(top)), S('wood', base=.38, jit=.04))
    nf = 10
    for i in range(nf):
        a = i * math.tau / nf + rng.uniform(-.15, .15); up = rng.uniform(.15, .5) if i % 2 else rng.uniform(-.2, .15)
        L = rng.uniform(6.5, 8.0)
        d = Vector((math.cos(a), 0, math.sin(a)))
        rach = [top + d * (L * t) + Vector((0, (up * 4 - 6.5 * t * t) * t + .4, 0)) for t in [k / 6 for k in range(7)]]
        P.add(tube(rach, [.16, .14, .12, .1, .08, .06, .03], sides=4), S('palm', base=.35, jit=.02))
        side = Vector((-d.z, 0, d.x))
        bm = bmesh.new(); Lft = []; Rgt = []; Mid = []
        for k in range(1, 7):
            t = k / 6; c = rach[k]; w = 1.5 * math.sin(min(1, t * 1.3) * math.pi * .9) + .2
            droop = Vector((0, -.9 * w, 0))
            Mid.append(bm.verts.new(c + Vector((0, .1, 0))))
            Lft.append(bm.verts.new(c + side * w + droop + d * .5))
            Rgt.append(bm.verts.new(c - side * w + droop + d * .5))
        for k in range(len(Mid) - 1):
            bm.faces.new((Mid[k], Mid[k + 1], Lft[k + 1], Lft[k])); bm.faces.new((Mid[k + 1], Mid[k], Rgt[k], Rgt[k + 1]))
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.06)
        P.add(bm, S('palm', base=.48 + (i % 3) * .06, up=.22, jit=.05, seed=seed * 7 + i))
    for k in range(3):                                                          # date clusters
        a = k * 2.1 + rng.uniform(0, .5); c = top + Vector((math.cos(a) * .9, -1.3, math.sin(a) * .9))
        P.add(tube([top + Vector((math.cos(a) * .5, -.2, math.sin(a) * .5)), c], .07, sides=4), S('saffron', base=.4, jit=.02))
        P.add(T(blob(.55, seed * 3 + k, n=14, sq=1.4), tuple(c)), S('saffron' if k % 2 else 'terra', base=.48, up=.15, jit=.05))
    return P

def oasis_pool(rx=15.0, rz=10.0, seed=1):
    """oasis spring: an irregular pool, a ring of cut sandstone curb stones, a lower inner shelf, turquoise water, reed
    clumps and lotus pads, a carved spout basin feeding it"""
    P = Prop('OasisPool%d' % seed); rng = random.Random(seed); n = 30
    out = []
    for i in range(n):
        a = i * math.tau / n
        k = 1 + (nz(math.cos(a) * 3, seed, math.sin(a) * 3, 1.3, 2) - .5) * .3
        out.append((math.cos(a) * rx * k, math.sin(a) * rz * k))
    ins = [(x * .9, z * .9) for x, z in out]
    bm = bmesh.new()
    O0 = [bm.verts.new((x, -.6, z)) for x, z in out]; O1 = [bm.verts.new((x, .7, z)) for x, z in out]
    I1 = [bm.verts.new((x, .7, z)) for x, z in ins]; I0 = [bm.verts.new((x, -.3, z)) for x, z in ins]
    for i in range(n):
        j = (i + 1) % n
        for a, b in ((O0, O1), (O1, I1), (I1, I0)): bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, S('stone', base=.5, up=.12, jit=.04))
    for i in range(n):                                                          # cut curb stones
        x, z = (out[i][0] + ins[i][0]) / 2, (out[i][1] + ins[i][1]) / 2
        yaw = -math.degrees(math.atan2(z, x)) + 90
        P.add(T(box((math.tau * math.hypot(*out[i]) / n * .92, .35, 1.3), .12), (x, .82, z), yaw), S('stone', base=.64 + rng.uniform(-.06, .06), up=.12, jit=.02))
    wb = bmesh.new(); wv = [wb.verts.new((x * .99, .25, z * .99)) for x, z in ins]; wb.faces.new(wv)
    bmesh.ops.triangulate(wb, faces=list(wb.faces))
    P.add(wb, lambda f: [(PAL.u('water'), .55)] * len(f.loops))
    rb = bmesh.new(); rv = [rb.verts.new((x * .82, .3, z * .82)) for x, z in ins]; rb.faces.new(rv)     # deep centre (darker)
    bmesh.ops.triangulate(rb, faces=list(rb.faces))
    P.add(rb, lambda f: [(PAL.u('water'), .4)] * len(f.loops))
    for k in range(5):                                                          # lotus pads
        a = rng.uniform(0, math.tau); r = rng.uniform(.4, .75)
        x, z = math.cos(a) * rx * r, math.sin(a) * rz * r
        P.add(T(cyl(rng.uniform(.6, 1.0), .08, 9, 0, y0=.32), (x, 0, z)), S('palm', base=.55, up=.1, jit=.03))
        if k % 2 == 0: P.add(T(spike(.25, .5, 6, 0, .38), (x + .2, 0, z)), S('plum', base=.65, up=.1, jit=.03))
    for k in range(4):                                                          # reed clumps on the rim
        i = int(n * (.1 + k * .23)) % n; x, z = out[i]
        for j in range(6):
            a = j * 1.1; base = Vector((x * 1.04 + math.cos(a) * .4, .5, z * 1.04 + math.sin(a) * .4))
            P.add(tube([base, base + Vector((math.cos(a) * .5, 3.0 + j % 3 * .6, math.sin(a) * .5))], [.09, .02], sides=3), S('palm', base=.45 + j * .03, jit=.03))
    i = n // 4; sx, sz = out[i]                                                 # spout basin on the back rim (+Z)
    P.add(T(lathe([(1.3, -.4), (1.4, .3), (1.3, 1.6), (1.05, 1.7), (1.0, 1.2), (0, 1.2)], n=10), (sx * 1.08, .5, sz * 1.08)), S('stone', base=.56, up=.12, jit=.02))
    P.add(T(lathe([(.8, 0), (.7, .3), (.4, .5), (.45, 1.1), (.2, 1.3), (0, 1.35)], n=8), (sx * 1.08, 2.2, sz * 1.08)), S('terra', base=.5, up=.12, jit=.02))
    P.add(tube([Vector((sx * 1.04, 3.0, sz * 1.0)), Vector((sx * .97, 2.6, sz * .9)), Vector((sx * .93, .3, sz * .86))], [.12, .14, .2], sides=6), S('water', base=.8, up=.1, jit=0))
    return P

def hoodoo(seed=1, h=16.0):
    """sandstone hoodoo: a broad banded column (overlapping strata drums, alternating red / orange), a narrower neck
    under a darker, wider cap rock, talus at the foot"""
    P = Prop('Hoodoo%d' % seed); rng = random.Random(seed)
    y = -1.0; r = h * .26; k = 0
    while y < h * .7:
        hh = rng.uniform(h * .14, h * .2); rr = r * rng.uniform(.92, 1.06)
        P.add(T(hull(rock_pts((rr, hh * .7, rr * rng.uniform(.9, 1.1)), 22, seed * 11 + k, None)), (rng.uniform(-.2, .2), y + hh * .5, rng.uniform(-.2, .2))),
              S('cliff2' if k % 2 else 'cliff', base=.52 + rng.uniform(-.04, .04), up=.18, jit=.04, seed=seed + k))
        y += hh * .6; r *= .9; k += 1
    P.add(T(hull(rock_pts((r * .7, h * .07, r * .7), 14, seed + 50, None)), (0, y + h * .02, 0)), S('cliff', base=.34, jit=.04))
    P.add(T(hull(rock_pts((h * .2, h * .07, h * .17), 22, seed + 60, .3)), (rng.uniform(-.3, .3), y + h * .1, 0)), S('stone', base=.42, up=.2, jit=.05))
    for i in range(5):
        a = i * 1.3
        P.add(T(blob(rng.uniform(.7, 1.4), seed * 5 + i, n=12, sq=.6), (math.cos(a) * h * .24, .1, math.sin(a) * h * .24)), S('cliff2', base=.45, up=.2, jit=.04))
    return P

def boulder(seed=1, r=2.4):
    """layered sandstone boulder: a flat-bedded lower slab, a smaller upper stratum offset on it, a chip at the foot"""
    P = Prop('Boulder%d' % seed); rng = random.Random(seed)
    P.add(hull(rock_pts((r, r * .45, r * .85), 26, seed, .5)), S('cliff2', grad=(-r * .3, r * .5, .34, .7), up=.15, vn=(1.6, seed, .16)))
    P.add(T(hull(rock_pts((r * .7, r * .32, r * .6), 22, seed + 3, .6)), (r * .15, r * .5, -r * .1)), S('cliff', grad=(r * .3, r * .9, .4, .72), up=.15, vn=(1.6, seed, .14)))
    P.add(T(blob(r * .3, seed + 9, n=12, sq=.65), (r * .95, -.1, r * .35)), S('stone', base=.5, up=.2, jit=.04))
    return P

def scrub(seed=1, r=1.6):
    """dry desert shrub: low, dense: a dozen small olive-grey leaf puffs on a twiggy woody base, a few dead twigs"""
    P = Prop('Scrub%d' % seed); rng = random.Random(seed)
    for k in range(7):
        a = k * .9 + rng.uniform(0, .4); top = Vector((math.cos(a) * r * .55, r * rng.uniform(.25, .45), math.sin(a) * r * .55))
        P.add(tube([Vector((0, -.3, 0)), top], [.09, .04], sides=4), S('wood', base=.45, jit=.03))
    for k in range(12):
        a = k * 2.4; rr = r * .75 * math.sqrt((k + .5) / 12)
        P.add(T(blob(r * rng.uniform(.26, .36), seed * 7 + k, n=10, sq=.75), (math.cos(a) * rr, r * (.3 + .25 * (1 - rr / r)), math.sin(a) * rr)),
              S('scrub', base=.46 + rng.uniform(-.06, .08), up=.22, jit=.04, seed=k))
    return P

def agave(seed=1, r=1.6):
    """agave rosette: thick tapering leaves curving up and out, a dark leaf tip each, a flower stalk on one"""
    P = Prop('Agave%d' % seed); rng = random.Random(seed)
    for ring, (n, tilt, L) in enumerate(((7, 62, r * 1.4), (6, 40, r * 1.2), (4, 18, r))):
        for i in range(n):
            a = i * math.tau / n + ring * .4
            d = Vector((math.cos(a), 0, math.sin(a)))
            pts = [Vector((0, .1 + ring * .1, 0)) + d * (L * t * math.sin(math.radians(tilt))) + Vector((0, L * t * math.cos(math.radians(tilt)) + (t * t * .3 * L if ring == 2 else -t * t * .2 * L), 0)) for t in (0, .35, .7, 1.0)]
            P.add(tube(pts, [.42, .36, .2, .01], sides=4, flat=(2.0, .45)), S('palm', grad=(0, L, .32, .7), up=.1))
            P.add(T(spike(.06, .25, 3, 0), tuple(pts[-1])), S('wood', base=.3, jit=.01))
    if seed % 2:
        P.add(tube([Vector((0, .5, 0)), Vector((.3, r * 3, .2)), Vector((.5, r * 4.2, .3))], [.15, .1, .06], sides=5), S('scrub', base=.45, jit=.02))
        for k in range(4):
            P.add(T(blob(.35, seed + k, n=10, sq=.6), (.45 + (k - 1.5) * .25, r * 4.0 - k * .15, .3)), S('saffron', base=.6, up=.2, jit=.04))
    return P

def dry_grass(seed=1, n=9):
    P = Prop('DryGrass%d' % seed); rng = random.Random(seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); h = rng.uniform(.9, 1.7); lean = rng.uniform(.2, .6)
        b = Vector((math.cos(a) * .3, -.2, math.sin(a) * .3))
        P.add(tube([b, b + Vector((math.cos(a) * lean * .4, h * .6, math.sin(a) * lean * .4)), b + Vector((math.cos(a) * lean, h, math.sin(a) * lean))], [.07, .04, .005], sides=3),
              S('saffron' if k % 3 == 0 else 'scrub', base=.55, up=.1, jit=.05))
    return P

# ------------------------------------------------------------------ traversal
def carved_stair(rise=24.0, run=40.0, w=6.0, land=10.0, seed=1):
    """stair carved into the canyon wall: sandstone treads climbing toward -Z, a solid ashlar-faced support mass from
    the floor, an open-side parapet with chamfered coping following the slope, a mid landing, and a top landing that
    runs +X (land studs) into the cliff ledge. Origin = bottom centre of the flight."""
    P = Prop('CarvedStair%d_%d' % (int(rise), seed)); rng = random.Random(seed)
    n = int(rise / .8); dr, dz = rise / n, run / n
    for i in range(n):
        z0 = run / 2 - i * dz; yt = dr * (i + 1)
        P.add(T(box((w, .5, dz + .08), .05), (0, yt - .25, z0 - dz / 2)), S('stone', base=.6 + rng.uniform(-.05, .05), up=.14, jit=.01))
    P.add(hull([Vector((x, y, z)) for x in (-w / 2, w / 2) for (z, y) in ((run / 2, -.8), (run / 2, 0), (-run / 2, rise - .6), (-run / 2, -.8))]), S('stone', base=.4, jit=.01))
    P.add(T(box((w + land, .6, 8.0), .1), (land / 2, rise - .3, -run / 2 - 4)), S('stone', base=.62, up=.12, jit=.02))   # top landing
    P.add(T(box((w + land, rise, 8.0)), (land / 2, rise / 2 - .6, -run / 2 - 4)), S('stone', base=.42, jit=.01))
    P.add(T(ashlar(w + land, rise - .6, 2.6, 1.2, seed=seed + 5, depth=.07, ins=.08), (land / 2, -.6, -run / 2 - 8.01), 180), ash_sh('stone', base=.6, grime=.15))
    P.add(T(ashlar(8.0, rise - .6, 2.6, 1.2, seed=seed + 6, depth=.07, ins=.08), (-w / 2 - .01, -.6, -run / 2 - 4), -90), ash_sh('stone', base=.56, grime=.15))
    ang = math.degrees(math.atan2(rise, run)); Ls = math.hypot(rise, run)
    x = -w / 2 - .7                                                             # open-side face + parapet
    for k in range(n // 2):                                                     # stepped face blocks under the treads
        z0 = run / 2 - (2 * k + 1) * dz; yt = dr * (2 * k + 2)
        P.add(T(box((.25, yt + .5, 2 * dz - .1), .04), (-w / 2 - .12, (yt - .5) / 2 - .2, z0)), S('stone', base=.5 + (k % 3) * .04, up=.06, jit=.02))
    P.add(T(box((1.0, 1.6, Ls), .1), (-w / 2 + .5, rise / 2 + .7, 0), 0, ang), S('stone', base=.55, up=.08, jit=.02))
    P.add(T(box((1.4, .35, Ls + .3), .12), (-w / 2 + .5, rise / 2 + 1.6, 0), 0, ang), S('stone', base=.72, up=.12, jit=.02))
    for zz, yy in ((run / 2 - .5, .5), (-run / 2 - .5, rise)):                  # newels with lantern niches
        P.add(T(box((1.6, 3.2, 1.6), .1), (-w / 2 + .5, yy + 1.4, zz)), S('stone', base=.55, up=.1, jit=.02))
        P.add(T(box((2.0, .4, 2.0), .14), (-w / 2 + .5, yy + 3.1, zz)), S('stone', base=.72, up=.12, jit=.02))
        brass_lantern(P, (-w / 2 + .5, yy + 3.3, zz), .6, hang=False)
    P.add(T(box((1.0, 1.6, 8.0), .1), (-w / 2 + .5, rise + .5, -run / 2 - 4)), S('stone', base=.55, up=.08, jit=.02))
    P.add(T(box((w + land, 1.6, 1.0), .1), (land / 2, rise + .5, -run / 2 - 7.5)), S('stone', base=.55, up=.08, jit=.02))
    return P

def rope_bridge(L=64.0, w=5.0, drop=3.2):
    """rope bridge spanning along Z from z = -L/2 to +L/2 (deck y 0 at both ends, sagging to -drop): slatted planks on
    two rope stringers, sagging rope handrails with rope verticals, a pair of carved anchor posts + stone blocks at each end"""
    P = Prop('RopeBridge%d' % int(L)); rng = random.Random(3)
    def y(z): return -drop * math.cos(z / L * math.pi)
    n = int(L / 1.1)
    for i in range(n):
        z = -L / 2 + (i + .5) * L / n
        dy = (y(z + .3) - y(z - .3)) / .6
        P.add(T(box((w + rng.uniform(-.3, .2), .2, L / n * .78), .04), (rng.uniform(-.1, .1), y(z) - .1, z), rng.uniform(-3, 3), -math.degrees(math.atan(dy))),
              S('wood', base=.5 + rng.uniform(-.08, .08), up=.1, jit=.02))
    m = 24; zs = [-L / 2 + L * k / m for k in range(m + 1)]
    for sx in (-1, 1):
        P.add(tube([Vector((sx * (w / 2 - .3), y(z) - .32, z)) for z in zs], .12, sides=4), S('rope', base=.42, jit=.02))
        rail = [Vector((sx * (w / 2 + .1), y(z) * .65 + 3.4, z)) for z in zs]
        P.add(tube(rail, .13, sides=4), S('rope', base=.5, jit=.02))
        for k in range(1, m):
            P.add(tube([rail[k], Vector((sx * (w / 2 - .2), y(zs[k]) - .25, zs[k]))], .05, sides=3), S('rope', base=.45, jit=.02))
        for sz in (-1, 1):
            z = sz * (L / 2 + .6)
            P.add(T(box((.8, 5.2, .8), .1), (sx * (w / 2 + .3), 1.8, z)), S('wood', base=.42, up=.06, jit=.02))
            P.add(T(lathe([(.5, 0), (.6, .2), (.3, .55), (0, .8)], n=8), (sx * (w / 2 + .3), 4.4, z)), S('brass', base=.55, up=.15, jit=.02))
            for k in range(3): P.add(T(torus(.5, .08, 8, 3), (sx * (w / 2 + .3), 2.6 + k * .3, z)), S('rope', base=.5, jit=.02))
            P.add(T(box((1.6, 1.4, 1.6), .15), (sx * (w / 2 + .3), -.2, z + sz * 1.6)), S('stone', base=.55, up=.12, jit=.02))
            P.add(tube([Vector((sx * (w / 2 + .3), 3.2, z)), Vector((sx * (w / 2 + .3), .4, z + sz * 1.6))], .1, sides=4), S('rope', base=.45, jit=.02))
    return P

# ------------------------------------------------------------------ stations (blank sign boards for GUIs)
def sign_board(P, c, w=4.0, h=1.8, yaw=0.0, posts=True, col='teal'):
    """BLANK sign: carved timber frame with a cream face (SurfaceGui goes here) and a coloured top rail; no text"""
    x, y, z = c
    L = lambda bm: T(bm, (x, y, z), yaw)
    P.add(L(box((w, h, .18))), S('stone', base=.85, up=0, jit=0))
    for yy in (-h / 2 - .1, h / 2 + .1):
        P.add(L(T(box((w + .5, .28, .32), .05), (0, yy, 0))), S('wood', base=.45, up=.08, jit=.01))
    for xx in (-w / 2 - .12, w / 2 + .12):
        P.add(L(T(box((.28, h + .4, .32), .05), (xx, 0, 0))), S('wood', base=.42, up=.08, jit=.01))
    P.add(L(T(box((w * .7, .2, .36), .05), (0, h / 2 + .35, 0))), S(col, base=.55, up=.1, jit=.01))
    P.add(L(T(lathe([(.25, 0), (.3, .12), (.15, .3), (0, .45)], n=8), (0, h / 2 + .45, 0))), S('brass', base=.55, up=.12, jit=.02))
    if posts:
        for xx in (-w / 2 - .12, w / 2 + .12):
            P.add(L(T(box((.36, y + h / 2, .36), .05), (xx, -(y + h / 2) / 2 + h / 2, .1))), S('wood', base=.4, jit=.01))

def spawn_fountain():
    """spawn plaza fountain: octagonal sandstone basin with a teal-tiled band, a carved column with two bowls spilling
    into it, four lion-free spout lips, turquoise water"""
    P = Prop('SpawnFountain'); R = 7.0; rng = random.Random(4)
    oct_ = lambda r: [(math.cos(i * math.tau / 8 + math.pi / 8) * r, math.sin(i * math.tau / 8 + math.pi / 8) * r) for i in range(8)]
    bm = bmesh.new()
    O0 = [bm.verts.new((x, -.5, z)) for x, z in oct_(R)]; O1 = [bm.verts.new((x, 1.6, z)) for x, z in oct_(R)]
    I1 = [bm.verts.new((x, 1.6, z)) for x, z in oct_(R - 1.0)]; I0 = [bm.verts.new((x, .3, z)) for x, z in oct_(R - 1.0)]
    for i in range(8):
        j = (i + 1) % 8
        for a, b in ((O0, O1), (O1, I1), (I1, I0)): bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, S('stone', base=.55, up=.12, jit=.03))
    for i in range(8):                                                          # coping + teal tile panels per side
        a = i * math.tau / 8 + math.pi / 4 + math.pi / 8 - math.pi / 8
        cx, cz = math.cos(a) * (R - .5), math.sin(a) * (R - .5); yaw = -math.degrees(a) + 90
        sl = 2 * R * math.tan(math.pi / 8)
        P.add(T(box((sl * .98, .35, 1.5), .12), (cx, 1.75, cz), yaw), S('stone', base=.72, up=.12, jit=.02))
        cx2, cz2 = math.cos(a) * (R * math.cos(math.pi / 8) + .02), math.sin(a) * (R * math.cos(math.pi / 8) + .02)
        P.add(T(box((sl * .7, .9, .12), .03), (cx2, .75, cz2), yaw), S('teal', base=.55, up=.05, jit=.04))
        for k in (-1, 1):
            P.add(T(box((.16, .9, .14)), (cx2 + math.cos(a + math.pi / 2) * k * sl * .2, .75, cz2 + math.sin(a + math.pi / 2) * k * sl * .2), yaw), S('saffron', base=.6, jit=.01))
    wb = bmesh.new(); wb.faces.new([wb.verts.new((x, 1.2, z)) for x, z in oct_(R - 1.0)])
    bmesh.ops.triangulate(wb, faces=list(wb.faces)); P.add(wb, lambda f: [(PAL.u('water'), .58)] * len(f.loops))
    P.add(T(lathe([(1.6, 0), (1.5, .6), (.9, .9), (.7, 2.2), (.85, 2.4), (.6, 2.6), (.55, 4.2)], n=10), (0, 1.0, 0)), S('stone', base=.6, up=.1, jit=.02))
    for y0, r in ((4.9, 3.0), (7.8, 1.7)):                                     # two spill bowls
        P.add(T(lathe([(.4, -.6), (1.0, -.4), (r, 0), (r + .15, .25), (r - .1, .3), (0, .1)], n=12), (0, y0, 0)), S('stone', base=.62, up=.15, jit=.02))
        P.add(T(torus(r + .05, .1, 12, 3), (0, y0 + .2, 0)), S('teal', base=.5, jit=.02))
        P.add(T(cyl(r - .15, .05, 12, 0, y0=.24), (0, y0, 0)), S('water', base=.6, up=0, jit=0))
        P.add(T(torus(r + .45, .12, 16, 3), (0, 1.25 if y0 < 6 else y0 - 2.75, 0)), S('water', base=.92, up=.05, jit=0))
    P.add(T(lathe([(.55, 0), (.6, .3), (.35, .7), (.4, 1.1), (.15, 1.5), (0, 1.6)], n=8), (0, 8.1, 0)), S('brass', base=.55, up=.15, jit=.02))
    for i in range(4):                                                          # step blocks + planter at the diagonals
        a = i * math.tau / 4 + math.pi / 4
        P.add(T(box((3.0, .5, 1.6), .1), (math.cos(a) * (R + .9), -.1, math.sin(a) * (R + .9)), -math.degrees(a) + 90), S('stone', base=.6, up=.12, jit=.02))
    return P

def trader_pavilion():
    """SELL station: a wide trader pavilion on the shared dais: six posts, two stretched cloth layers (saffron over
    plum), a long counter with a brass balance scale, open treasure chests of coins, a blank sign board on the front"""
    P = Prop('TraderPavilion'); w, d = 14.0, 9.0
    dais(P, w + 2, d + 2, .8, 7)
    for sx in (-1, 0, 1):
        for sz in (-1, 1):
            x, z = sx * w / 2, sz * d / 2; h = 8.5 if sz < 0 else 9.5
            P.add(T(box((.5, h, .5), .07), (x, .8 + h / 2, z)), S('wood', base=.42, up=.06, jit=.02))
            P.add(T(lathe([(.45, 0), (.5, .2), (.32, .5), (.1, .8), (0, .85)], n=8), (x, .8 + h, z)), S('brass', base=.55, up=.15, jit=.02))
            P.add(T(torus(.36, .08, 8, 3), (x, .8 + h - .9, z)), S('rope', base=.5, jit=.02))
    for sz, h in ((-1, 8.5), (1, 9.5)):
        P.add(bar((-w / 2 - .3, .8 + h - .3, sz * d / 2), (w / 2 + .3, .8 + h - .3, sz * d / 2), .4, .4), S('wood', base=.4, jit=.01))
    for sx in (-1, 0, 1):
        P.add(bar((sx * w / 2, .8 + 8.2, -d / 2), (sx * w / 2, .8 + 9.2, d / 2), .36, .36), S('wood', base=.38, jit=.01))
    cloth_sheet(P, -w / 2 - .6, w / 2 + .6, -d / 2 - .8, d / 2 + .5, 9.55, 10.55, 'plum', stripes=8, col2='saffron', nx=8, nzz=4, drop=.4)
    cz = -d / 2 + 1.4
    P.add(T(box((w - 1.5, .3, 1.8), .07), (0, 3.3, cz)), S('wood', base=.55, up=.12, jit=.02))
    P.add(T(box((w - 1.8, 2.5, .3), .05), (0, 2.05, cz - .6)), S('wood', base=.36, jit=.01))
    for k in range(6):
        xx = -w / 2 + 1.0 + (w - 2.0) * (k + .5) / 6
        P.add(T(box(((w - 2.0) / 6 - .4, 1.7, .12), .04), (xx, 2.0, cz - .8)), S('terra', base=.5, up=.06, jit=.02))
    P.add(T(lathe([(.4, 0), (.3, .2), (.12, .4), (.1, 2.2), (0, 2.3)], n=8), (-2.0, 3.45, cz)), S('brass', base=.5, up=.12, jit=.02))   # balance scale
    P.add(bar((-3.6, 5.5, cz), (-.4, 5.5, cz), .12, .12), S('brass', base=.62, jit=.02))
    for sx in (-1, 1):
        x = -2.0 + sx * 1.5
        for k in range(3): P.add(tube([Vector((x, 5.5, cz)), Vector((x + math.cos(k * 2.1) * .5, 4.2, cz + math.sin(k * 2.1) * .5))], .02, sides=3), S('brass', base=.4, jit=.01))
        P.add(T(lathe([(0, 0), (.6, .06), (.65, .2), (0, .16)], n=10), (x, 4.1, cz)), S('brass', base=.55, up=.1, jit=.02))
    for k, x in enumerate((2.0, 4.4)):                                          # coin chests
        P.add(T(box((1.8, 1.0, 1.2), .08), (x, 3.95, cz)), S('wood', base=.45, up=.08, jit=.02))
        for xx in (-.6, .6): P.add(T(box((.15, 1.05, 1.25)), (x + xx, 3.95, cz)), S('brass', base=.55, jit=.02))
        P.add(T(box((1.7, .5, 1.1)), (x, 4.55, cz)), S('saffron', base=.62, up=.25, jit=.06))
        P.add(T(box((1.8, .15, 1.2), .05), (x, 5.0, cz + .75), 0, -70), S('wood', base=.5, up=.08, jit=.02))
    for i in range(4): pot(P, (-w / 2 + 1.4 + i * 1.0, .8, d / 2 - 1.0), 1.6, .5, 70 + i, band=('teal', 'saffron', 'plum', 'teal')[i], kind=i % 3)
    sign_board(P, (0, 7.1, -d / 2 - .1), 6.0, 1.8, 0, posts=False, col='saffron')
    return P

def forge_station():
    """UPGRADE station: a sandstone forge hearth with glowing coals, a hooded terracotta chimney, an anvil on a stump,
    a leather bellows, a tool rack with blades, a quench trough and a blank sign board on posts"""
    P = Prop('ForgeStation'); rng = random.Random(5)
    dais(P, 16, 11, .6, 11)
    hx, hz = -3.0, 2.0
    P.add(T(box((6.0, 3.0, 4.0), .15), (hx, .6 + 1.5, hz)), S('stone', base=.5, up=.08, jit=.02))
    P.add(T(ashlar(6.0, 2.9, 1.5, .75, seed=3, depth=.05, ins=.06), (hx, .6, hz - 2.01)), ash_sh('stone', base=.6, grime=.25))
    P.add(T(box((5.0, .3, 3.0)), (hx, 3.7, hz)), S('wood', base=.2, jit=.01))
    for k in range(9):
        P.gadd(T(blob(.45, 30 + k, n=10, sq=.6), (hx - 1.8 + (k % 3) * 1.8 + rng.uniform(-.3, .3), 3.9, hz - 1.0 + (k // 3) * 1.0)), 'fire')
    P.add(T(lathe([(3.0, 0), (2.9, .4), (1.6, 3.0), (1.1, 3.4), (1.1, 9.0), (1.4, 9.2), (1.4, 9.8), (0, 9.8)], n=8, a0=math.pi / 8), (hx, 6.0, hz + .6)), S('terra', base=.5, up=.1, jit=.03))
    for y in (6.1, 9.4, 14.8): P.add(T(torus(3.0 if y < 7 else 1.25, .12, 8, 3), (hx, y, hz + .6)), S('brass', base=.45, jit=.02))
    for sx in (-1, 1):
        P.add(T(box((.6, 3.0, .6), .06), (hx + sx * 2.7, 4.5, hz - 1.6)), S('wood', base=.4, jit=.02))
    P.add(T(box((6.4, 4.0, 1.0), .1), (hx, 3.6 + 2.0, hz + 2.4)), S('stone', base=.45, jit=.02))          # fire-back wall
    P.add(T(ashlar(6.4, 3.9, 1.4, .7, seed=8, depth=.05, ins=.06), (hx, 3.6, hz + 1.89), 180), ash_sh('stone', base=.5, grime=.35))
    for sx in (-1, 1):                                                          # cheek walls round the coal bed
        P.add(T(box((.6, 1.0, 3.6), .08), (hx + sx * 2.9, 4.1, hz + .2)), S('stone', base=.6, up=.1, jit=.02))
    ax, az = 3.0, -1.5                                                         # anvil on a stump
    P.add(T(lathe([(.9, -.3), (.85, 1.4), (.95, 1.5), (0, 1.5)], n=9), (ax, .6, az)), S('wood', base=.42, up=.1, jit=.03))
    anv = hull([Vector(p) for p in ((-1.2, 0, -.45), (1.2, 0, -.45), (-1.2, 0, .45), (1.2, 0, .45), (-.6, .7, -.3), (.6, .7, -.3), (-.6, .7, .3), (.6, .7, .3),
                                    (-1.4, 1.2, -.5), (1.0, 1.2, -.5), (-1.4, 1.2, .5), (1.0, 1.2, .5), (-1.5, .9, -.45), (2.3, 1.15, 0), (2.0, .95, 0))])
    P.add(T(anv, (ax - .4, 2.1, az)), S('wood', base=.2, up=.25, jit=.02))
    P.add(T(box((.25, .2, 2.4), .04), (ax + .9, 3.4, az + .3), 30), S('wood', base=.4, jit=.01))    # hammer
    P.add(T(box((.9, .55, .5), .06), (ax + .4, 3.4, az - .4), 30), S('wood', base=.2, up=.2, jit=.02))
    bx, bz = hx + 4.2, hz + 1.0                                                 # bellows
    bel = hull([Vector(p) for p in ((-.9, 0, -1.6), (.9, 0, -1.6), (-.3, 0, 1.2), (.3, 0, 1.2), (-.8, .9, -1.4), (.8, .9, -1.4), (-.2, .5, 1.1), (.2, .5, 1.1))])
    P.add(T(bel, (bx, 1.4, bz), -30), S('terra', base=.32, up=.15, jit=.02))
    P.add(T(box((.4, 1.0, .4)), (bx, .9, bz)), S('wood', base=.4, jit=.02))
    tx = 5.6                                                                     # tool rack with blades
    for sx in (-1, 1): P.add(T(box((.35, 4.2, .35), .05), (tx + sx * 1.6, .6 + 2.1, 3.0)), S('wood', base=.42, jit=.02))
    P.add(T(box((3.6, .3, .4), .05), (tx, 4.2, 3.0)), S('wood', base=.45, jit=.02))
    for k in range(4):
        x = tx - 1.2 + k * .8
        P.add(T(spike(.12, 2.4, 4, 0, .3), (x, .9, 2.85), 0, 0, 180), S('stone', base=.9, up=0, jit=.02))
        P.add(T(box((.6, .14, .2)), (x, 3.65, 2.85)), S('brass', base=.55, jit=.02))
        P.add(T(box((.16, .6, .16)), (x, 4.0, 2.85)), S('wood', base=.35, jit=.02))
    P.add(T(box((3.0, 1.2, 1.4), .1), (1.5, 1.2, 4.0)), S('wood', base=.4, up=.08, jit=.02))   # quench trough
    P.add(T(box((2.6, .1, 1.0)), (1.5, 1.75, 4.0)), S('water', base=.42, jit=0))
    sign_board(P, (-6.0, 4.4, -4.8), 3.6, 1.6, 0, posts=True, col='terra')
    return P

def quest_board():
    """QUEST station: a timber notice board under a small stretched teal cloth, three blank parchment panels, pinned
    rolled scrolls in a basket, a lantern and a bench"""
    P = Prop('QuestBoard'); w = 7.0
    dais(P, w + 3, 4.5, .4, 21)
    for sx in (-1, 1):
        P.add(T(box((.5, 8.0, .5), .07), (sx * w / 2, .4 + 4.0, 0)), S('wood', base=.42, up=.06, jit=.02))
        P.add(T(lathe([(.42, 0), (.48, .2), (.28, .5), (.08, .75), (0, .8)], n=8), (sx * w / 2, 8.4, 0)), S('brass', base=.55, up=.15, jit=.02))
        P.add(bar((sx * w / 2, 7.6, 0), (sx * w / 2, 6.6, -2.2), .25, .25), S('wood', base=.36, jit=.01))
    P.add(T(box((w + .6, 4.0, .4), .06), (0, 4.6, 0)), S('wood', base=.4, jit=.02))
    for k, x in enumerate((-2.2, 0, 2.2)):
        P.add(T(box((1.9, 2.6 - (k % 2) * .4, .1), .02), (x, 4.7 + (k % 2) * .2, -.25), 0, 0, (k - 1) * 3), S('stone', base=.88, up=0, jit=.01))
        P.add(T(lathe([(.12, 0), (.14, .06), (0, .12)], n=6), (x, 5.85 + (k % 2) * .2, -.32), 0, 90), S('plum', base=.5, jit=.01))
    P.add(bar((-w / 2 - .4, 7.6, 0), (w / 2 + .4, 7.6, 0), .3, .3), S('wood', base=.4, jit=.01))
    P.add(bar((-w / 2 - .4, 6.6, -2.2), (w / 2 + .4, 6.6, -2.2), .25, .25), S('wood', base=.4, jit=.01))
    cloth_sheet(P, -w / 2 - .6, w / 2 + .6, -2.6, .3, 6.85, 7.95, 'teal', stripes=4, col2='stone', nx=4, nzz=2, drop=.15)
    brass_lantern(P, (w / 2 - 1.0, 4.9, -2.2), .7)
    P.add(tube([Vector((w / 2 - 1.0, 6.55, -2.2)), Vector((w / 2 - 1.0, 6.48, -2.2))], .03, sides=3), S('rope', base=.4, jit=.01))
    P.add(tube([Vector((w / 2 - 1.0, 6.48, -2.2)), Vector((w / 2 - 1.0, 6.25, -2.2))], .03, sides=3), S('rope', base=.4, jit=.01))
    P.add(T(lathe([(0, 0), (.6, 0), (.75, .9), (.8, 1.0), (0, .9)], n=10), (-w / 2 - .2, .4, -1.2)), S('rope', base=.5, up=.1, jit=.03))
    for k in range(4):
        a = k * 1.6
        P.add(T(log((0, 0, 0), (0, 1.3, 0), .14, 6), (-w / 2 - .2 + math.cos(a) * .3, 1.0, -1.2 + math.sin(a) * .3), 0, 10 * math.cos(a), 10 * math.sin(a)), S('stone', base=.82, up=0, jit=.01))
    P.add(T(box((3.0, .3, 1.0), .08), (1.0, 1.4, -2.0)), S('wood', base=.5, up=.1, jit=.01))
    for sx in (-1, 1): P.add(T(box((.4, 1.1, .8), .05), (1.0 + sx * 1.1, .85, -2.0)), S('stone', base=.55, up=.1, jit=.02))
    sign_board(P, (0, 8.75, -.05), 3.4, 1.0, 0, posts=False, col='teal')
    return P

def relic_kiosk():
    """RELIC / PET station on the ledge: a small domed kiosk on four horseshoe arches (teal-tiled dome, brass finial),
    a pedestal inside with a floating glowing relic gem, two jars at the steps, blank sign board on a stand"""
    P = Prop('RelicKiosk'); s = 9.0; h = 6.5
    dais(P, s + 2, s + 2, .8, 31)
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(box((1.4, h, 1.4), .1), (sx * (s / 2 - .7), .8 + h / 2, sz * (s / 2 - .7))), S('stone', base=.56, up=.08, jit=.02))
            P.add(T(box((1.8, .4, 1.8), .12), (sx * (s / 2 - .7), .8 + h, sz * (s / 2 - .7))), S('stone', base=.7, up=.12, jit=.02))
    hw = s / 2 - 1.4
    for yaw in (0, 90, 180, 270):                                               # arched spandrel on each side
        fr = G.arch_frame(hw, h - hw - .6, .5, -.6, .6); B.T(fr, (0, .8, -s / 2 + .7))
        P.add(T(fr, (0, 0, 0), yaw), S('terra', base=.5, up=.1, jit=.02))
        wall = box((s, 1.6, 1.0)); B.T(wall, (0, .8 + h + .8, -s / 2 + .7)); B.T(wall, (0, 0, 0), yaw)
        P.add(wall, S('stone', base=.58, up=.08, jit=.02))
        P.add(T(T(box((s - 1.0, .3, .2)), (0, .8 + h + .7, -s / 2 + .15)), (0, 0, 0), yaw), S('teal', base=.55, jit=.02))
    P.add(T(box((s + .6, .45, s + .6), .15), (0, .8 + h + 1.75, 0)), S('stone', base=.72, up=.12, jit=.02))
    dome = [(s / 2 - .2, 0), (s / 2 - .1, .6)] + [(math.cos(a) * (s / 2 - .1), .6 + math.sin(a) * (s / 2 + .6)) for a in [k * math.pi / 2 / 7 for k in range(1, 8)]] + [(0, s / 2 + 1.3)]
    P.add(T(lathe(dome, n=16), (0, .8 + h + 1.95, 0)), S('teal', base=.5, up=.2, jit=.02))
    for k in range(16):                                                         # gilt ribs on the dome
        a = k * math.tau / 16
        pts = [Vector((math.cos(a) * r * 1.01, .8 + h + 1.95 + y, math.sin(a) * r * 1.01)) for r, y in dome[1:-1]]
        if k % 2 == 0: P.add(tube(pts, .07, sides=3), S('brass', base=.55, jit=.02))
    top = .8 + h + 1.95 + s / 2 + 1.3
    P.add(T(lathe([(.5, 0), (.6, .3), (.3, .7), (.45, 1.1), (.15, 1.6), (.2, 1.9), (0, 2.6)], n=8), (0, top - .2, 0)), S('brass', base=.6, up=.15, jit=.02))
    P.add(T(lathe([(1.4, 0), (1.3, .5), (.8, .7), (.7, 2.2), (1.1, 2.4), (1.1, 2.7), (0, 2.7)], n=8), (0, .8, 0)), S('stone', base=.62, up=.1, jit=.02))
    gem = bmesh.new(); gp = [Vector((0, -.9, 0)), Vector((0, .9, 0))] + [Vector((math.cos(a) * .6, 0, math.sin(a) * .6)) for a in [k * math.tau / 6 for k in range(6)]]
    P.gadd(T(hull(gp), (0, 5.0, 0)), 'relic')
    P.add(T(torus(1.0, .06, 14, 3), (0, 5.0, 0), 0, 70), S('brass', base=.6, jit=.02))
    for sx in (-1, 1): pot(P, (sx * 2.6, .8, -s / 2 - .4), 1.5, .5, 90 + sx, band='teal', kind=1)
    sign_board(P, (s / 2 + 1.8, 2.6, -s / 2 - .6), 3.4, 1.4, -20, posts=True, col='plum')
    return P

def brazier(seed=1):
    """temple brazier: fluted sandstone pedestal, a brass bowl on three claw legs, a heap of glowing coals + flames"""
    P = Prop('Brazier%d' % seed)
    P.add(T(lathe([(1.3, -.5), (1.3, .4), (1.0, .6), (.75, .9), (.7, 2.6), (.9, 2.8), (1.0, 3.1), (0, 3.1)], n=10), (0, 0, 0)), S('stone', base=.6, up=.1, jit=.02))
    P.add(T(lathe([(.3, 0), (.9, .2), (1.5, .8), (1.65, 1.0), (1.45, 1.05), (0, .5)], n=12), (0, 3.4, 0)), S('brass', base=.5, up=.15, jit=.02))
    for i in range(3):
        a = i * math.tau / 3
        P.add(tube([Vector((math.cos(a) * .6, 3.1, math.sin(a) * .6)), Vector((math.cos(a) * 1.0, 3.5, math.sin(a) * 1.0)), Vector((math.cos(a) * 1.25, 4.1, math.sin(a) * 1.25))], .1, sides=4), S('brass', base=.4, jit=.02))
    P.gadd(T(blob(1.1, seed, n=14, sq=.4), (0, 4.4, 0)), 'fire')
    for k in range(3):
        a = k * 2.1
        hh = 2.0 - k * .45; rr = .55 - k * .1
        P.gadd(T(lathe([(rr * .6, 0), (rr, hh * .2), (rr * .8, hh * .45), (rr * .35, hh * .75), (0, hh)], n=6), (math.cos(a) * .4, 4.3, math.sin(a) * .4), k * 40, 10 * math.cos(a), 10 * math.sin(a)), 'fire')
    return P

def market_gate():
    """horseshoe-arch gate over the street: ashlar piers with chamfered plinths, a pointed horseshoe arch with terra
    voussoir frame, a teal-tiled frieze band, crenellated stepped parapet, a hanging lantern in the opening.
    Opening 14 wide, 13 high; built across X, walk-through along Z."""
    P = Prop('MarketGate'); hw = 7.0; spring = 7.0; D = 4.0; W = 26.0; H = 20.0
    mass = box((W, H + .5, D)); B.T(mass, (0, (H - .5) / 2, 0))
    cut = G.arch_prism(hw, spring, -D / 2 - .5, D / 2 + .5, -1.0)
    for v in cut.verts:                                                         # pointed horseshoe: widen + peak the top
        if v.co.y > spring:
            t = (v.co.y - spring) / hw
            v.co.x *= 1.08 - .3 * t; v.co.y = spring + (v.co.y - spring) * 1.25
    mass = G.bool_diff(mass, cut)
    P.add(mass, S('stone', base=.55, up=.08, jit=.02))
    for zz, yaw in ((-D / 2 - .01, 0), (D / 2 + .01, 180)):
        P.add(T(ashlar(W, H - 1.0, 2.8, 1.2, seed=yaw + 3, skip=lambda x, y: abs(x) < hw * 1.12 and y < spring + hw * 1.3, depth=.07, ins=.08), (0, 0, zz), yaw), ash_sh('stone', base=.62, grime=.15))
        fr = G.arch_frame(hw, spring, 1.0, -.3, .3)
        for v in fr.verts:
            if v.co.y > spring:
                t = (v.co.y - spring) / (hw + 1.0)
                v.co.x *= 1.08 - .3 * min(1, (v.co.y - spring) / hw); v.co.y = spring + (v.co.y - spring) * 1.25
        P.add(T(fr, (0, 0, zz - (.3 if yaw == 0 else -.3)), yaw), S('terra', base=.5, up=.1, jit=.03))
        P.add(T(box((W + .4, 1.0, .5), .05), (0, H - 3.0, zz - (.25 if yaw == 0 else -.25))), S('teal', base=.5, up=.05, jit=.03))
        for k in range(12):
            P.add(T(box((.5, .5, .3)), (-W / 2 + 1.1 + k * (W - 2.2) / 11, H - 3.0, zz - (.55 if yaw == 0 else -.55)), 0, 0, 45), S('saffron', base=.6, jit=.01))
    for sx in (-1, 1):
        P.add(T(box((W / 2 - hw * 1.12 + .6, 1.6, D + 1.0), .15), (sx * (W / 2 - (W / 2 - hw * 1.12) / 2), .3, 0)), S('stone', base=.5, up=.1, jit=.02))
    P.add(T(box((W + .8, .6, D + .8), .2), (0, H, 0)), S('stone', base=.72, up=.12, jit=.02))
    for k in range(7):                                                          # stepped merlons
        x = -W / 2 + 1.5 + k * (W - 3) / 6
        for j, (ww, hh) in enumerate(((2.0, 1.0), (1.3, .9), (.6, .7))):
            P.add(T(box((ww, hh, D - .4), .08), (x, H + .3 + sum((1.0, .9, .7)[:j]) + hh / 2, 0)), S('stone', base=.6 + j * .04, up=.1, jit=.02))
    for sx in (-1, 1):                                                          # bracket lanterns on both faces of the jambs
        for sz in (-1, 1):
            x = sx * (hw * 1.12 + 2.2); z = sz * (D / 2 + .2)
            P.add(tube([Vector((x, 9.6, z)), Vector((x, 10.2, z + sz * 1.0)), Vector((x, 9.9, z + sz * 1.5))], .09, sides=4), S('brass', base=.45, jit=.02))
            brass_lantern(P, (x, 7.4, z + sz * 1.5), .85)
    return P

# ------------------------------------------------------------------ hero
def sun_temple():
    """HERO: Temple of the Setting Sun, a rock-cut facade standing in a rectangular niche
    cut into the end wall (front = -Z like every prop; the map turns it 180 and scales it 1.35). Two-storey Petra-style facade:
    a wide stepped podium, six fluted columns with lotus capitals, entablature with a terra frieze, a broken pediment
    framing a round tholos (columns, conical roof, sun urn), obelisk wings, a deep cut doorway with a glowing inner hall
    and a glowing sun disc above the door, tall rock mass behind."""
    P = Prop('SunTemple'); W = 56.0; D = 14.0
    # rock mass behind (the cliff the facade is carved from)
    # CARVED NICHE: the facade stands in a rectangular niche cut into the end wall. Cliff face plane z = -1, a
    # three-step chiselled surround stepping back toward the facade, and the cliff strata (red / orange / red / cream
    # cap, same bands as the canyon walls at the map's 1.35 scale) continuing beside and above the niche.
    rr = random.Random(77)
    OW = [36.0, 34.0, 32.0, 30.0]; OT = [72.0, 70.0, 68.0, 66.0]; XO, TOP = 54.0, 70.0
    def strata(y):
        return ('cliff', .34) if y < 17.8 else ('cliff2', .42) if y < 38.5 else ('cliff', .4) if y < 63.0 else ('stone', .5)
    y = -1.0
    while y < TOP - .1:
        hh = min(TOP - y, rr.uniform(7.0, 9.5)); ym = y + hh / 2; col, b = strata(ym)
        sh = S(col, base=b + rr.uniform(-.03, .03), up=.08, jit=.01)
        for sx in (-1, 1):                                                      # piers beside the niche
            P.add(T(box((XO - OW[0], hh - .06, 15.0), .05), (sx * (XO + OW[0]) / 2, ym, 6.5)), sh)
        if y + hh > OT[0]:                                                      # mass above the niche
            y0_ = max(y, OT[0]); P.add(T(box((2 * OW[0] + .2, y + hh - y0_ - .06, 15.0), .05), (0, (y0_ + y + hh) / 2, 6.5)), sh)
        y += hh
    for k in range(3):                                                          # stepped chiselled surround
        zf = -1.0 + 1.3 * (k + 1); d = 14.0 - 1.3 * (k + 1); zc = zf + d / 2
        o0, o1, t0, t1 = OW[k], OW[k + 1], OT[k], OT[k + 1]
        sh = S('stone', base=.56 - .05 * k, up=.1, jit=.01)
        for sx in (-1, 1):
            P.add(T(box((o0 - o1, t1 + 1.0, d), .1), (sx * (o0 + o1) / 2, (t1 - 1.0) / 2, zc)), sh)
        P.add(T(box((2 * o0, t0 - t1, d), .1), (0, (t0 + t1) / 2, zc)), sh)
    P.add(T(box((2 * XO + 2, 1.2, 16.0), .3), (0, TOP + .4, 6.5)), S('stone', base=.62, up=.12, jit=.02))   # cap course

    # podium: 4 steps
    for k in range(5):
        P.add(T(box((W + 10 - k * 2.4, 1.0, D + 14 - k * 2.6), .1), (0, k * 1.0, k * 1.3 + 2)), S('stone', base=.58 + (k % 2) * .05, up=.14, jit=.01))
    y0 = 4.5
    back = box((2 * 30.5, 67, 6)); B.T(back, (0, y0 + 32, 6))
    cut = G.arch_prism(4.5, 10.0, -1.0, 12.0, -2.0); B.T(cut, (0, y0, 0))
    back = G.bool_diff(back, cut)
    P.add(back, S('stone', base=.5, up=.06, jit=.02))
    P.add(T(ashlar(W - 2, 26, 3.4, 1.6, seed=5, skip=lambda x, y: abs(x) < 6.3 and y < 15.6, depth=.08, ins=.1), (0, y0, 2.99), 180), ash_sh('stone', base=.6, grime=.2))
    # doorway: tunnel + glowing hall + frame
    P.add(T(G.arch_tunnel(4.5, 10.0, 2.95, 9.0), (0, y0, 0)), S('stone', base=.28, jit=.02))
    P.gadd(T(G.arch_cap(4.5, 10.0, 0), (0, y0, 8.8)), 'temple')
    fr = G.arch_frame(4.5, 10.0, 1.2, -.6, .6); P.add(T(fr, (0, y0, 2.4), 0), S('terra', base=.5, up=.1, jit=.02))
    P.add(T(box((15.0, 1.2, 1.6), .12), (0, y0 + 16.6, 2.2)), S('stone', base=.68, up=.12, jit=.02))
    # sun disc above the door (glowing core + carved rays)
    P.gadd(T(cyl(2.6, .5, 16, 0), (0, y0 + 20.5, 2.1), 0, 90), 'temple')
    P.add(T(torus(2.95, .38, 16, 4), (0, y0 + 20.5, 2.5), 0, 90), S('brass', base=.55, up=.1, jit=.02))
    for k in range(12):
        a = k * math.tau / 12
        ray = spike(.38, 2.0, 4, 0, .3)
        B.T(ray, (0, 3.3, 0)); B.T(ray, (0, 0, 0), 0, 0, -math.degrees(a)); B.T(ray, (0, y0 + 20.5, 2.6))
        P.add(ray, S('brass', base=.5, up=.1, jit=.02))
    # lower order: 6 fluted columns
    def column(x, z, yb, h, r, fl=12):
        prof = [(r * 1.35, 0), (r * 1.35, .6), (r * 1.15, .9), (r * 1.05, 1.2), (r, 1.4), (r * .9, h - 2.2), (r * 1.25, h - 1.5), (r * 1.5, h - .8), (r * 1.35, h - .5), (r * 1.4, h - .5), (r * 1.4, h), (0, h)]
        bm = lathe(prof, n=fl * 2)
        for v in bm.verts:                                                      # flutes
            if 1.3 < v.co.y < h - 2.3:
                a = math.atan2(v.co.z, v.co.x); k = 1 - .07 * (round(a / (math.pi / fl)) % 2)
                v.co.x *= k; v.co.z *= k
        P.add(T(bm, (x, yb, z)), S('stone', base=.6, up=.08, jit=.02))
        P.add(T(box((r * 3.0, .6, r * 3.0), .1), (x, yb + h + .3, z)), S('stone', base=.7, up=.1, jit=.02))
    for x in (-21, -14, -7, 7, 14, 21): column(x, -1.0, y0, 24.0, 1.35)
    ent = y0 + 24.6
    P.add(T(box((W + 1, 2.0, 5.0), .15), (0, ent + 1.0, .5)), S('stone', base=.64, up=.1, jit=.02))
    P.add(T(box((W + .6, 2.4, 4.6), .1), (0, ent + 3.2, .7)), S('terra', base=.52, up=.06, jit=.02))
    for k in range(18):                                                        # frieze rosettes
        P.add(T(cyl(.6, .3, 8, .05), (-W / 2 + 2 + k * (W - 4) / 17, ent + 3.2, -1.65), 0, 90), S('saffron', base=.6, up=.1, jit=.02))
    P.add(T(box((W + 2.4, 1.2, 6.0), .2), (0, ent + 5.0, .4)), S('stone', base=.72, up=.12, jit=.02))
    # broken pediment wings + tholos
    y2 = ent + 5.6
    for sx in (-1, 1):
        x = sx * 18.0
        pw = hull([Vector(p) for p in ((x - sx * 10, y2, -2), (x + sx * 10, y2, -2), (x + sx * 10, y2 + 6, -2), (x - sx * 10, y2, 3), (x + sx * 10, y2, 3), (x + sx * 10, y2 + 6, 3))])
        P.add(pw, S('stone', base=.58, up=.1, jit=.02))
        P.add(bar((x - sx * 10.5, y2 + .2, -2.4), (x + sx * 10.5, y2 + 6.3, -2.4), .7, .7), S('stone', base=.72, up=.1, jit=.02))
        for xx in (x - sx * 6, x + sx * 6):                                    # upper half-columns
            column(xx, -1.0, y2, 16.0, 1.0, 10)
        P.add(T(box((5.6, 9.0, .5), .08), (x, y2 + 6.0, 2.75)), S('terra', base=.48, up=.05, jit=.02))   # false door
        P.add(T(box((4.4, 7.8, .5)), (x, y2 + 5.6, 2.95)), S('stone', base=.25, jit=.01))
        P.add(T(box((6.4, .7, 1.0), .1), (x, y2 + 10.8, 2.5)), S('stone', base=.7, up=.12, jit=.02))
        P.add(T(box((10, 1.4, 4.5), .12), (x, y2 + 16.7, .5)), S('stone', base=.68, up=.1, jit=.02))
        ob = spike(1.4, 9.0, 4, 0, 0, math.pi / 4, .85)                          # obelisk finials
        P.add(T(ob, (x, y2 + 17.4, .5)), S('stone', base=.62, up=.12, jit=.02))
        P.add(T(spike(.5, 1.2, 4, 0, 0, math.pi / 4, .4), (x, y2 + 17.4 + 9.0 - .4, .5)), S('brass', base=.6, up=.1, jit=.02))
    # tholos (centre): drum + 8 columns + cone roof + urn
    tc = (0, y2, 1.0)
    P.add(T(cyl(7.0, 1.2, 16, .15), tc), S('stone', base=.62, up=.12, jit=.02))
    P.add(T(cyl(4.6, 14.0, 16, 0, y0=1.2), tc), S('stone', base=.44, up=.04, jit=.02))
    P.gadd(T(cyl(1.6, 5.0, 10, 0, y0=2.4), (0, y2, -3.6)), 'temple')
    for k in range(8):
        a = math.pi + k * math.pi / 7
        column(math.cos(a) * 6.0, 1.0 + math.sin(a) * 6.0, y2 + 1.2, 13.0, .7, 8)
    P.add(T(cyl(7.2, 1.6, 16, .2), (0, y2 + 14.8, 1.0)), S('stone', base=.68, up=.1, jit=.02))
    P.add(T(lathe([(7.4, 0), (7.0, .6), (4.0, 3.0), (1.4, 5.2), (0, 5.6)], n=16), (0, y2 + 16.4, 1.0)), S('terra', base=.52, up=.15, jit=.02))
    P.add(T(lathe([(1.2, 0), (1.4, .8), (.6, 1.6), (1.0, 2.6), (.4, 3.4), (.2, 4.2), (0, 4.4)], n=10), (0, y2 + 21.7, 1.0)), S('brass', base=.6, up=.15, jit=.02))
    # carved lantern niches flanking the door
    for sx in (-1, 1):
        for x in (sx * 10.5, sx * 17.5):
            fr = G.arch_frame(1.2, 2.2, .35, -.3, .3); P.add(T(fr, (x, y0 + 4.0, 2.6)), S('terra', base=.48, jit=.02))
            P.add(T(box((2.4, 3.4, .3)), (x, y0 + 5.7, 2.95)), S('stone', base=.22, jit=.01))
            brass_lantern(P, (x, y0 + 4.0, 2.4), .8, hang=False)
    return P
