# Eggstead Isle prop kit ("Steal a ___" egg game: buy an egg off the lane, carry it home, others raid your plot).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: LOW POLY spring farm. Flat-shaded chunky shapes (6-10 sides), bevelled edges, bright clean colours.
# Neutral shared base: straw-cream yards, white-cream plaster, honey wood, warm stone. Eight plot accents (roof, trim,
# gate, nest rings, pad rim) carry the colour coding: red, orange, yellow, teal, sky, blue, purple, pink.
# Identity: the speckled Egg (lathe egg, wider below the middle) with a painted zigzag band; straw nests; egg finials
# on every post. No text, no letters, no flags or banners (labels are GUIs on anchors).
# Machinery (Prop, S, blob, materials, to_kit) from the grove example, transforms (T, bar, lathe, torus) from the
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
    'grass':  ('#3f8a3a', '#7cc455', '#c8ee88'),     # island lawn, hills
    'leaf':   ('#2b7a3e', '#58bd52', '#bdee78'),     # canopies, bushes, hedges
    'wood':   ('#6b4426', '#b57d4b', '#efc890'),     # honey wood: posts, rails, planks, trunks
    'cream':  ('#b89a62', '#efdcaa', '#fffaea'),     # straw yards, plaster walls, eggshell, nests
    'stone':  ('#7a6e60', '#c4b49a', '#f2e8d4'),     # warm stone: plinths, pavers, rocks
    'dark':   ('#1d222b', '#3b4352', '#737e90'),     # belt rubber, rollers, iron
    'water':  ('#1b6aa8', '#43ade2', '#b4eeff'),     # lake
    'red':    ('#a11e2a', '#ff4848', '#ffb4aa'),     # plot accents (also egg paint)
    'orange': ('#ae4c0c', '#ff922c', '#ffd49c'),
    'yellow': ('#ad8608', '#ffd23a', '#fff4a8'),
    'teal':   ('#077a5f', '#1ed6a2', '#aaffe2'),
    'sky':    ('#0f6ea8', '#3cc2ff', '#baedff'),
    'blue':   ('#1a2c9c', '#4565ff', '#b6c4ff'),
    'purple': ('#58209c', '#a35cff', '#ddc4ff'),
    'pink':   ('#a0206c', '#ff62c2', '#ffc4ea'),
})
ACC = ('red', 'orange', 'yellow', 'teal', 'sky', 'blue', 'purple', 'pink')
ACC_HEX = {'red': '#ff5050', 'orange': '#ff9a34', 'yellow': '#ffd84a', 'teal': '#2ce8b4', 'sky': '#4ccbff',
           'blue': '#5a78ff', 'purple': '#b072ff', 'pink': '#ff70cc'}
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
GLOWS = {'lamp': '#ffe6a0', 'heat': '#ffb35c', 'hatch': '#ffe36a', 'drain': '#8ae9ff', 'window': '#ffd98a'}
GLOWS.update({'g_' + a: h for a, h in ACC_HEX.items()})
G.GLOW.clear(); G.GLOW.update(GLOWS)
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 3.2, 'heat': 2.4, 'hatch': 3.4, 'drain': 2.4, 'window': 2.2})
for a in ACC: G.GLOW_E['g_' + a] = 2.6
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, lathe, torus = B.T, B.bar, B.lathe, B.torus
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
V3 = Vector
WARM = ('red', 'orange', 'yellow', 'pink')

# ------------------------------------------------------------------ generic helpers
def rbox(size, r=.2, seg=1):
    """bevelled box (low poly: 1 segment = a chamfer)"""
    bm = box(size); return bevel(bm, min(r, min(size) * .45), seg)

def upright(poly, d, pos, yaw=0.0, s=1.0):
    """2D poly [(x, up)] standing upright facing -Z, extruded d toward the front (-Z) from z = 0"""
    bm = ngon_prism([(x * s, z * s) for x, z in poly], 0, d)
    return T(T(bm, (0, 0, 0), 0, -90), pos, yaw)

def merge_prop(P, sub, pos=(0, 0, 0), s=1.0, yaw=0.0):
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    def tr(mb, dst):
        base = len(dst.V)
        dst.V.extend(tuple(R @ (V3(v) * s) + V3(pos)) for v in mb.V)
        dst.F.extend(tuple(i + base for i in f) for f in mb.F); dst.UV.extend(mb.UV); dst.SM.extend(mb.SM)
    tr(sub.solid, P.solid)
    for k, mb in sub.glow.items(): tr(mb, P.glow.setdefault(k, G.MB()))

def sh(col, base=.55, up=.2, jit=.02, seed=0): return S(col, base=base, up=up, jit=jit, seed=seed)

def egg_profile(R, H, m=7):
    """egg outline (r, y) bottom -> top: widest a little below the middle, narrower dome on top"""
    out = []
    for k in range(m + 1):
        a = math.pi * k / m; y = H * (1 - math.cos(a)) / 2
        r = R * math.sin(a) * (1.06 - .2 * (y / H))
        out.append((max(r, 0.0) if 0 < k < m else 0.0, y))
    return out

def egg_slice(R, H, t0, t1, m=7, grow=1.0):
    """a band of the egg between heights t0..t1 (fractions of H), radius x grow: painted bands sit proud by grow"""
    prof = egg_profile(R, H, 24)
    def r_at(t):
        y = t * H
        for (ra, ya), (rb, yb) in zip(prof, prof[1:]):
            if ya <= y <= yb: return lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6))
        return 0.0
    rows = [(r_at(lerp(t0, t1, i / 2)) * grow, lerp(t0, t1, i / 2) * H) for i in range(3)]
    return rows

def egg(P, c, R, H, shell='cream', band=None, band2=None, n=10, m=7, yaw=0.0, tilt=0.0, spots=None, seed=0, base=.72):
    """the identity Egg: faceted lathe egg; optional painted zigzag band (band colour) + thin rings (band2) + speckles"""
    def put(bm): return T(T(bm, (0, 0, 0), 0, tilt), c, yaw)
    P.add(put(lathe(egg_profile(R, H, m), n)), sh(shell, base, .22, .03, seed))
    if band:
        # zigzag band: a ring of n triangles alternating up / down, laid proud of the shell
        prof = egg_profile(R, H, 24)
        def r_at(y):
            for (ra, ya), (rb, yb) in zip(prof, prof[1:]):
                if ya <= y <= yb: return lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6))
            return 0.0
        bm = bmesh.new(); N = n * 2; y0, y1 = H * .4, H * .58; ring = []
        for i in range(N + 1):
            a = i * math.tau / N + math.pi / n * .5
            yu = y1 if i % 2 else y1 - (y1 - y0) * .55
            yd = y0 + (y1 - y0) * .55 if i % 2 else y0
            ring.append([bm.verts.new((math.cos(a) * r_at(yy) * 1.035, yy, math.sin(a) * r_at(yy) * 1.035)) for yy in (yd, yu)])
        for A, Bq in zip(ring, ring[1:]):
            bm.faces.new((A[0], Bq[0], Bq[1], A[1]))
        bm.normal_update()
        for f in bm.faces:
            cc = f.calc_center_median()
            if f.normal.dot(Vector((cc.x, 0, cc.z))) < 0: f.normal_flip()
        P.add(put(bm), sh(band, .6, .15, .02))
    if band2:
        for t in (.3, .68):
            y = H * t; prof = egg_profile(R, H, 24)
            rr = next(lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6)) for (ra, ya), (rb, yb) in zip(prof, prof[1:]) if ya <= y <= yb)
            P.add(put(T(torus(rr * 1.0, H * .028, n, 4), (0, y, 0))), sh(band2, .58, .1, .01))
    if spots:
        rng = random.Random(seed)
        for k in range(spots):
            t = rng.uniform(.12, .85); a = rng.uniform(0, math.tau); y = H * t
            prof = egg_profile(R, H, 24)
            rr = next(lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6)) for (ra, ya), (rb, yb) in zip(prof, prof[1:]) if ya <= y <= yb)
            d = V3((math.cos(a) * rr, y, math.sin(a) * rr)); nrm = V3((math.cos(a), .0, math.sin(a)))
            sp = cyl(R * rng.uniform(.07, .12), R * .05, 5, y0=-R * .02)
            M = nrm.to_track_quat('Y', 'Z').to_matrix()
            bmesh.ops.rotate(sp, cent=V3(), matrix=M, verts=sp.verts); bmesh.ops.translate(sp, vec=d, verts=sp.verts)
            P.add(put(sp), sh(band or 'wood', .45, .1, .03))

def straw_nest(P, c, R, h=1.0, n=10, col='wood', seed=0, wisps=8):
    """chunky low-poly nest: a fat torus rim with a dished floor, straw wisps poking out of the rim"""
    rng = random.Random(seed)
    P.add(T(lathe([(R * .55, 0), (R * .92, h * .2), (R, h * .62), (R * .9, h), (R * .7, h * .92), (R * .5, h * .55), (0, h * .45)], n), c),
          S(col, base=.6, up=.25, jit=.05, seed=seed))
    for k in range(wisps):
        a = k * math.tau / wisps + rng.uniform(-.2, .2)
        p0 = V3(c) + V3((math.cos(a) * R * .9, h * .78, math.sin(a) * R * .9))
        d = V3((math.cos(a + rng.choice((-1, 1)) * .9), rng.uniform(.1, .5), math.sin(a + rng.choice((-1, 1)) * .9)))
        P.add(tube([p0, p0 + d * R * .3], [R * .06, 0.0], sides=3), S('wood', base=.8 if k % 2 else .7, up=.1, jit=.03))

def egg_finial(P, c, s=1.0, acc='red', n=8):
    """post-top egg knob: accent collar + cream egg with an accent band"""
    P.add(T(lathe([(.42 * s, 0), (.5 * s, .12 * s), (.36 * s, .26 * s), (.2 * s, .3 * s)], n), c), sh(acc, .55))
    egg(P, (c[0], c[1] + .26 * s, c[2]), .34 * s, .9 * s, 'cream', None, acc, n=n, m=6)

def post(P, a, h, w=.7, col='wood', cap=None, base_col='stone'):
    """square post with a stone footing (extends below ground) and a chamfered top"""
    x, y, z = a
    P.add(T(rbox((w * 1.5, .9, w * 1.5), .12), (x, y + .2, z)), sh(base_col, .55))
    P.add(T(rbox((w, h, w), .1), (x, y + h / 2 - .1, z)), sh(col, .55, .15))
    if cap: P.add(T(rbox((w * 1.25, .3, w * 1.25), .08), (x, y + h - .05, z)), sh(cap, .6))

# ------------------------------------------------------------------ plot kit (one per accent colour)
def nest_pedestal(acc='red'):
    """incubator slot: octagon stone plinth with an accent ring + four gem studs, honey-wood stem with a collar, a straw
    nest on a cream dish, a warm glow ring under the nest lip (the egg sits here: EggSlot anchor)"""
    P = Prop('NestPedestal_%s' % acc)
    P.add(lathe([(1.9, -.4), (1.9, .35), (1.75, .5), (1.45, .55), (0, .55)], 8, math.pi / 8), sh('stone', .55, .2, .03))
    P.add(lathe([(1.93, .12), (1.97, .2), (1.97, .34), (1.93, .4), (1.6, .4), (1.6, .12)], 8, math.pi / 8), sh(acc, .55, .15))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        P.add(T(lathe([(0, -.12), (.14, 0), (0, .12)], 4), (math.cos(a) * 1.98, .27, math.sin(a) * 1.98), 0, 90), sh('cream', .9, .1, 0))
    P.add(lathe([(.62, .5), (.62, 1.0), (.5, 1.15), (.5, 2.2), (.62, 2.35), (.62, 2.6)], 6), sh('wood', .55, .15, .03))
    P.add(lathe([(.7, 1.3), (.78, 1.4), (.78, 1.6), (.7, 1.7), (0, 1.7)], 6), sh(acc, .5, .15))
    P.add(lathe([(.6, 2.55), (1.35, 2.75), (1.45, 2.95), (0, 2.95)], 8, math.pi / 8), sh('cream', .62, .2, .02))
    P.gadd(T(torus(1.3, .09, 12, 4), (0, 2.88, 0)), 'heat')
    straw_nest(P, (0, 2.85, 0), 1.35, .75, 9, seed=3, wisps=6)
    return P

def fence_run(acc='red', L=8.0, post=True, r0=.5, r1=None, tag=''):
    """picket fence segment along +X (0..L), front -Z: a slim honey post with an accent cap at x=0, two accent rails,
    cream pointed pickets with gaps (cheap: 29 of these per plot; corners + gate ends get FencePost_ with an egg knob).
    Rails run r0..r1 (default stop .5 short of the next post / FencePost, so no part sits inside another); post=False
    where a FencePost or a gate pillar already stands at x=0"""
    P = Prop('Fence%d%s_%s' % (int(L), tag, acc))
    r1 = L - .5 if r1 is None else r1
    if post:
        P.add(T(rbox((.7, 3.5, .7), .1), (0, 1.5, 0)), sh('wood', .55, .15))
        P.add(T(rbox((.95, .3, .95), .08), (0, 3.35, 0)), sh(acc, .6))
    for y in (1.0, 2.5):
        P.add(T(box((r1 - r0, .32, .26)), ((r0 + r1) / 2, y, .2)), sh(acc, .55, .2))
    a0, a1 = max(.8, r0 + .4), min(L - .4, r1 - .4)
    n = max(1, round(int(L / 1.6) * (a1 - a0) / (L - 1.2)))
    for i in range(n):
        x = a0 + (a1 - a0) * (i + .5) / n
        hh = 2.9 + (.18 if i % 2 else 0)
        poly = [(-.32, -.3), (.32, -.3), (.32, hh - .45), (0, hh), (-.32, hh - .45)]
        P.add(upright(poly, .16, (x, 0, .12)), sh('cream', .76, .15, .03, i))
    return P

def fence_post(acc='red'):
    """the closing post of a fence run"""
    P = Prop('FencePost_%s' % acc)
    post(P, (0, 0, 0), 3.6, .8, 'wood', acc)
    egg_finial(P, (0, 3.55, 0), .9, acc, 6)
    return P

def gate_frame(acc='red', W=16.0):
    """yard entrance (the laser / force-gate spot, opening W): two stone-footed pillars with accent shafts and inset
    cream panels, round emitter lamps facing the opening at three heights (glow in the accent), an arched honey-wood top
    beam with an accent keystone egg in a nest. Opening clear: x +-(W/2 - 1), y 0..9.5"""
    P = Prop('GateFrame_%s' % acc)
    hw = W / 2
    for sx in (-1, 1):
        x = sx * hw
        P.add(T(rbox((2.6, 1.4, 2.6), .25), (x, .3, 0)), sh('stone', .55, .2, .03))
        P.add(T(rbox((2.2, .4, 2.2), .1), (x, 1.15, 0)), sh(acc, .45))
        P.add(T(rbox((1.8, 8.6, 1.8), .22), (x, 5.6, 0)), sh(acc, .58, .18))
        for zz in (-.91, .91):
            P.add(T(rbox((1.0, 6.2, .1), .03), (x, 5.4, zz)), sh('cream', .82, .1, .01))
        P.add(T(rbox((2.3, .5, 2.3), .12), (x, 10.05, 0)), sh('wood', .5))
        for y in (2.5, 5.2, 7.9):                                                # emitter nodes toward the opening
            P.add(T(T(lathe([(.42, 0), (.48, .14), (.4, .3), (0, .3)], 8), (0, 0, 0), 0, 0, 90 * -sx), (x - sx * .88, y, 0)), sh('dark', .5, .1))
            P.gadd(T(T(lathe([(.28, 0), (.26, .14), (0, .2)], 8), (0, 0, 0), 0, 0, 90 * -sx), (x - sx * 1.17, y, 0)), 'g_' + acc)
        egg_finial(P, (x, 10.3, 0), 1.3, acc, 8)
    # arched top beam (honey wood) + accent trim under it
    n = 10; arc = []
    for i in range(n + 1):
        t = i / n; x = lerp(-hw, hw, t); y = 10.6 + math.sin(math.pi * t) * 2.2
        arc.append(V3((x, y, 0)))
    P.add(tube(arc, .62, sides=6, flat=(1.0, 1.25)), sh('wood', .55, .2))
    P.add(tube([p + V3((0, -.75, 0)) for p in arc[1:-1]], .22, sides=5), sh(acc, .55))
    straw_nest(P, (0, 12.55, 0), 1.25, .7, 8, seed=5, wisps=5)
    egg(P, (0, 12.9, 0), .8, 1.9, 'cream', acc, None, n=8, m=6, seed=2)
    return P

def owner_sign(acc='red'):
    """owner board: two honey posts, accent frame, BLANK cream face toward -Z (GUI), a little gable cap with an egg"""
    P = Prop('OwnerSign_%s' % acc)
    for sx in (-1, 1):
        post(P, (sx * 3.6, 0, 0), 8.6, .55, 'wood', None)
    P.add(T(rbox((8.0, 4.4, .5), .18), (0, 6.0, 0)), sh(acc, .55))
    P.add(T(rbox((7.0, 3.5, .2), .05), (0, 6.0, -.3)), sh('cream', .86, .05, .005))   # blank face (GUI here)
    P.add(T(rbox((6.6, 3.1, .2), .05), (0, 6.0, .3)), sh('cream', .74, .05, .005))
    roof = [(-4.6, 0), (4.6, 0), (0, 1.5)]
    P.add(upright(roof, 1.1, (0, 8.15, .55)), sh(acc, .48, .2))
    P.add(T(rbox((9.6, .3, 1.3), .08), (0, 8.2, 0)), sh('wood', .55))
    egg_finial(P, (0, 9.55, 0), .9, acc, 6)
    for sx in (-1, 1):                                                          # brackets
        P.add(bar((sx * 3.6, 3.4, -.1), (sx * 2.2, 3.85, -.1), .25, .25, .04), sh('wood', .45))
    return P

def collect_pad(acc='red'):
    """cash collect pad: octagon stone ring, accent rim with a glow ring, cream disc with a raised gold coin stack icon
    (three coins + a chevron of honey wood) - flat enough to walk over"""
    P = Prop('CollectPad_%s' % acc)
    P.add(lathe([(3.4, -.05), (3.4, .25), (3.15, .4), (0, .4)], 8, math.pi / 8), sh('stone', .55))   # sits ON the yard paving
    P.add(lathe([(3.05, .38), (3.05, .55), (2.6, .55), (2.6, .38)], 12), sh(acc, .55))
    P.gadd(T(torus(2.82, .1, 16, 4), (0, .58, 0)), 'g_' + acc)
    P.add(lathe([(2.5, .38), (2.5, .5), (0, .5)], 12), sh('cream', .82, .1, .01))
    for k, (dx, dz, n) in enumerate(((-.5, .2, 3), (.75, -.3, 2), (-.1, -.9, 1))):
        for j in range(n):
            P.add(T(lathe([(.62, 0), (.66, .06), (.66, .18), (.62, .24), (0, .24)], 10), (dx, .5 + j * .25, dz)), sh('yellow', .6 + .04 * j, .15))
    return P

def plot_slab(acc='red', W=56.0, D=64.0, aisle=10.0):
    """the yard: chamfered stone footing + accent kerb, straw-cream ground, a paved stone aisle from the gate (-Z) to the
    coop, square stone pads under the ten nests. Top y = .6"""
    P = Prop('PlotYard_%s' % acc)
    P.add(T(rbox((W + 1.2, .9, D + 1.2), .3), (0, -.2, 0)), sh('stone', .5, .2, .02))
    P.add(T(rbox((W + .6, .3, D + .6), .12), (0, .32, 0)), sh(acc, .5, .15))
    top = bmesh.new(); nxg, nzg = 7, 8; rng0 = random.Random(9)
    vv = {}
    for i in range(nxg + 1):
        for j in range(nzg + 1):
            vv[i, j] = top.verts.new((lerp(-W / 2 + .3, W / 2 - .3, i / nxg), .55, lerp(-D / 2 + .3, D / 2 - .3, j / nzg)))
    for i in range(nxg):
        for j in range(nzg):
            top.faces.new((vv[i, j], vv[i, j + 1], vv[i + 1, j + 1], vv[i + 1, j]))
    for f in top.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    P.add(top, S('cream', base=.36, up=.0, jit=.05, seed=7))
    P.add(T(box((W - .6, .3, D - .6)), (0, .39, 0)), S('cream', base=.3, up=.1, jit=.0))
    # aisle pavers (front gate -> coop door)
    ts = 2.4; nx = int(aisle / ts); nzz = int((D - 22) / ts)
    rng = random.Random(4)
    for i in range(nx):
        for j in range(nzz):
            x = -aisle / 2 + ts * (i + .5); z = -D / 2 + 1.0 + ts * (j + .5)
            P.add(T(box((ts - .25, .2, ts - .25)), (x, .58, z)), sh('stone', .68 + rng.uniform(-.06, .06), .1, .01))
    for x, z in NEST_SLOTS:
        P.add(T(rbox((5.2, .2, 5.2), .1), (x, .58, z)), sh('stone', .62, .1, .01))
    return P

NEST_SLOTS = [(-22, -15), (-13, -15), (13, -15), (22, -15), (-22, -4), (-13, -4), (13, -4), (22, -4), (-12, 8), (12, 8)]
PAD_POS = (0, 7.0)
COOP_Z = 22.0

def coop(acc='red'):
    """the nest-coop (the plot's base building): stone plinth, cream plaster walls with honey timber corner posts and a
    belt rail, an arched doorway CUT in the front (-Z) with a wood frame and a ramp, round window cut in the front gable
    (warm glow set back), accent gable roof with overhang, shingle courses, ridge beam + cap, a cupola with an egg
    finial; a lean-to nest-box rack on the +X side. Footprint ~22 x 14 (+5 rack)"""
    P = Prop('Coop_%s' % acc)
    W, D, Hw, th = 20.0, 14.0, 9.0, .8
    P.add(T(rbox((W + 1.6, 1.4, D + 1.6), .3), (0, .3, 0)), sh('stone', .55, .2, .03))
    y0 = 1.0
    # walls: front (with arched door cut), back, sides
    front = T(rbox((W, Hw, th), .1), (0, y0 + Hw / 2, -D / 2 + th / 2))
    door = G.arch_prism(3.4, 4.6, -1.5, 1.5, -1.0)
    door = T(door, (0, y0, -D / 2 + th / 2))
    front = G.bool_diff(front, door)
    P.add(front, sh('cream', .76, .12, .02))
    P.add(T(rbox((W, Hw, th), .1), (0, y0 + Hw / 2, D / 2 - th / 2)), sh('cream', .72, .12, .02))
    for sx in (-1, 1):
        sw = T(rbox((th, Hw, D - 2 * th + .02), .05), (sx * (W / 2 - th / 2), y0 + Hw / 2, 0))
        win = T(rbox((2.0, 2.6, 2.0), .02), (sx * (W / 2 - th / 2), y0 + 5.2, 0))
        P.add(G.bool_diff(sw, win), sh('cream', .74, .12, .02))
        P.add(T(rbox((th * .3, 2.6, 2.0), .02), (sx * (W / 2 - th * .9), y0 + 5.2, 0)), sh('dark', .3, .05, .0))
        P.gadd(T(box((.1, 2.4, 1.8)), (sx * (W / 2 - th * .95), y0 + 5.2, 0)), 'window')
        for dz in (-1.2, 1.2):                                                   # shutters
            P.add(T(rbox((.25, 2.9, 1.1), .06), (sx * (W / 2 + .12), y0 + 5.2, dz * 1.6)), sh(acc, .5, .15))
        P.add(T(rbox((.5, .3, 2.6), .06), (sx * (W / 2 + .1), y0 + 3.75, 0)), sh('wood', .5))
    P.add(T(rbox((W - 1.6, .2, D - 1.6), .02), (0, y0 + .1, 0)), sh('wood', .5, .1, .03))   # plank floor inside
    # door frame: arch of wood voussoirs + jambs, threshold ramp
    fr = G.arch_frame(3.4, 4.6, .55, -.35, .35)
    P.add(T(fr, (0, y0, -D / 2 + th / 2 - .12)), sh('wood', .58, .15))
    P.add(T(rbox((7.4, .35, 2.6), .1), (0, y0 - .25, -D / 2 - 1.0), 0, -8), sh('wood', .5, .2))
    # timber corner posts + belt rail + eave plate
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(rbox((1.0, Hw + .4, 1.0), .12), (sx * W / 2, y0 + Hw / 2, sz * D / 2)), sh('wood', .55, .15))
    for sz in (-1, 1):
        if sz > 0: P.add(T(rbox((W + .6, .45, .4), .08), (0, y0 + 2.6, D / 2 + .25)), sh('wood', .5))
        else:
            for sx in (-1, 1):
                P.add(T(rbox((W / 2 - 4.6, .45, .4), .08), (sx * (W / 4 + 2.15), y0 + 2.6, -D / 2 - .25)), sh('wood', .5))
        P.add(T(rbox((W + 1.0, .6, .6), .1), (0, y0 + Hw + .1, sz * (D / 2 + .1))), sh('wood', .45))
    for sx in (-1, 1):                                                          # door lanterns
        P.add(bar((sx * 4.9, y0 + 6.2, -D / 2 - .1), (sx * 4.9, y0 + 6.2, -D / 2 - 1.1), .2, .2, .03), sh('dark', .5))
        P.gadd(T(lathe(egg_profile(.38, 1.0, 5), 6), (sx * 4.9, y0 + 5.0, -D / 2 - 1.1)), 'lamp')
        P.add(T(lathe([(.42, 0), (.45, .12), (0, .14)], 6), (sx * 4.9, y0 + 6.0, -D / 2 - 1.1)), sh('dark', .45))
    for sx in (-1, 1):
        P.add(T(rbox((.4, .45, D + .6), .08), (sx * (W / 2 + .25), y0 + 2.6, 0)), sh('wood', .5))
    # gables (front with a round window cut, back plain); roof ridge runs along Z
    yg = y0 + Hw; rise = 6.6
    gpoly = [(-W / 2, 0), (W / 2, 0), (0, rise)]
    fg = upright(gpoly, th, (0, yg, -D / 2 + th))
    ow = T(T(cyl(1.5, 3.0, 10), (0, -1.5, 0)), (0, 0, 0), 0, 90)
    ow = T(ow, (0, yg + 2.4, -D / 2 + th / 2))
    P.add(G.bool_diff(fg, ow), sh('cream', .8, .12, .02))
    P.add(T(T(torus(1.55, .25, 10, 4), (0, 0, 0), 0, 90), (0, yg + 2.4, -D / 2 - .05)), sh('wood', .55))
    P.gadd(T(T(cyl(1.5, .1, 10), (0, 0, 0), 0, 90), (0, yg + 2.4, -D / 2 + th + .2)), 'window')
    P.add(upright(gpoly, th, (0, yg, D / 2)), sh('cream', .74, .12, .02))
    # roof: two slabs + 3 shingle courses each, ridge beam + cap, overhang 1.4
    ov = 1.6; Ls = math.hypot(W / 2, rise); Lr = Ls + ov; ang = math.degrees(math.atan2(rise, W / 2))
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for sx in (-1, 1):
        dirv = V3((sx * ca, -sa, 0)); nrm = V3((sx * sa, ca, 0)); ridge = V3((0, yg + rise, 0))
        c = ridge + dirv * (Lr / 2) + nrm * .42
        P.add(T(T(rbox((Lr, .7, D + 2 * ov), .2), (0, 0, 0), 0, 0, -sx * ang), tuple(c)), sh(acc, .58, .25, .02))
        for k in range(4):                                                       # shingle step courses
            d = Lr * (k + .6) / 4.4
            c = ridge + dirv * d + nrm * .85
            P.add(T(T(rbox((.5, .3, D + 2 * ov + .1), .1), (0, 0, 0), 0, 0, -sx * ang), tuple(c - nrm * .15)), sh(acc, .44, .15))
    P.add(T(rbox((.9, .9, D + 2 * ov + .3), .2), (0, yg + rise + .55, 0)), sh('wood', .5))
    P.add(T(rbox((1.6, .45, D + 2 * ov + .5), .15), (0, yg + rise + .95, 0)), sh(acc, .42))
    # cupola on the ridge
    cy0 = yg + rise + .7
    P.add(T(rbox((3.4, 2.8, 3.4), .2), (0, cy0 + 1.4, 0)), sh('cream', .82, .12))
    for sx in (-1, 1):
        P.add(T(rbox((.12, 1.6, 1.8), .02), (sx * 1.72, cy0 + 1.6, 0)), sh('dark', .3, .05))
    P.add(T(lathe([(2.8, 0), (2.8, .3), (0, 2.2)], 4, math.pi / 4), (0, cy0 + 2.8, 0)), sh(acc, .5, .25))
    egg_finial(P, (0, cy0 + 4.7, 0), 1.0, acc, 8)
    # nest-box rack (lean-to on +X): 3 boxes with straw, small accent roof
    rx = W / 2 + 2.6
    P.add(T(rbox((4.4, 3.6, D - 2.0), .2), (rx, 1.8, 0)), sh('wood', .5, .15))
    for k in range(3):
        z = (k - 1) * (D - 3.0) / 3
        P.add(T(rbox((.2, 2.3, 3.2), .03), (rx + 2.25, 2.4, z)), sh('dark', .25, .05))
        P.add(T(rbox((.3, .4, 3.6), .06), (rx + 2.35, 1.2, z)), sh('wood', .62))
        straw_nest(P, (rx + 2.0, 1.1, z), 1.1, .55, 7, seed=k + 11, wisps=3)
        egg(P, (rx + 2.0, 1.3, z), .45, 1.1, 'cream', None, None, n=6, m=5)
    P.add(T(T(rbox((5.8, .45, D - .6), .15), (0, 0, 0), 0, 0, -18), (rx + .3, 4.3, 0)), sh(acc, .5, .25))
    return P

def hay_bale(seed=0):
    """square hay bale: chamfered straw block, two twine bands, straw tufts on top"""
    P = Prop('HayBale%d' % seed); rng = random.Random(seed)
    P.add(T(rbox((3.6, 2.0, 2.2), .35), (0, .95, 0)), S('yellow', base=.74, up=.18, jit=.04, seed=seed))
    for x in (-.9, .9):
        P.add(T(rbox((.18, 2.08, 2.28), .04), (x, .95, 0)), sh('wood', .35, .1))
    for k in range(5):
        x, z = rng.uniform(-1.4, 1.4), rng.uniform(-.8, .8)
        P.add(tube([V3((x, 1.9, z)), V3((x + rng.uniform(-.4, .4), 2.35, z + rng.uniform(-.3, .3)))], [.09, 0.0], sides=3), sh('yellow', .82, .1))
    return P

def hay_stack():
    """three bales stacked (2 + 1), a pitchfork-free story pile"""
    P = Prop('HayStack')
    for i, (x, y, z, yaw) in enumerate(((-1.9, 0, 0, 0), (1.9, 0, .2, 6), (0, 1.95, .1, -8))):
        merge_prop(P, hay_bale(i + 1), (x, y, z), 1.0, yaw)
    return P

def feed_trough():
    """grain trough: honey plank trough on splayed legs, grain heap inside, small egg-crate beside it"""
    P = Prop('FeedTrough')
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(bar((sx * 2.6, -.3, sz * .9), (sx * 2.3, 1.6, sz * .55), .3, .3, .04), sh('wood', .45))
    P.add(T(rbox((6.2, .3, 1.8), .08), (0, 1.55, 0)), sh('wood', .52))
    for sz in (-1, 1):
        P.add(T(T(rbox((6.2, 1.2, .25), .06), (0, 0, 0), 0, -sz * 14), (0, 2.1, sz * .95)), sh('wood', .58))
    for sx in (-1, 1):
        P.add(T(rbox((.25, 1.2, 2.2), .06), (sx * 3.1, 2.1, 0)), sh('wood', .5))
    P.add(T(blob(1.0, 5, 18, .5), (0, 2.25, 0), s=(2.6, 1, .75)), S('yellow', base=.62, up=.2, jit=.05))
    # egg crate on the ground beside it
    P.add(T(rbox((2.2, .9, 1.6), .1), (4.6, .45, .4)), sh('wood', .6))
    for i in range(3):
        for j in range(2):
            egg(P, (3.9 + i * .7, .8, -.05 + j * .8), .28, .7, 'cream', None, None, n=6, m=5)
    return P

def flower_tub(seed=0, col='pink'):
    """half-barrel planter: honey staves with iron hoops, soil, low-poly tulips"""
    P = Prop('FlowerTub%d' % seed); rng = random.Random(seed)
    P.add(lathe([(1.0, -.3), (1.15, .6), (1.1, 1.2), (.95, 1.2), (.95, .9), (0, .9)], 8), sh('wood', .55, .2))
    for y in (.25, .95):
        P.add(T(torus(1.15 if y < .5 else 1.12, .07, 8, 3), (0, y, 0)), sh('dark', .45))
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.2, .2); r = rng.uniform(.2, .65)
        x, z = math.cos(a) * r, math.sin(a) * r; h = rng.uniform(.8, 1.4)
        P.add(tube([V3((x, .9, z)), V3((x, .9 + h, z))], .05, sides=3), sh('leaf', .45))
        P.add(T(lathe([(0, 0), (.22, .1), (.24, .35), (.12, .42), (0, .3)], 5, rng.uniform(0, 1)), (x, .9 + h - .05, z)), sh(col if k % 3 else 'yellow', .6, .15))
        P.add(T(T(lathe([(0, 0), (.14, .3), (0, .6)], 3), (0, 0, 0), 0, 0, 50), (x + .1, 1.0, z)), sh('leaf', .55))
    return P

# ------------------------------------------------------------------ lane kit
BELT_W, BELT_Y = 10.0, 1.7          # belt top height above the lane walkway (walkway y .25)
def conveyor_seg(L=16.0):
    """egg conveyor segment along -Z (z 0..-L): stone feet, honey side boards with an accent-free dark iron top rail,
    roller ends showing at the sides, dark rubber belt with raised cream chevron cleats pointing south (+Z, toward the
    drain), skirt of cream under the boards"""
    P = Prop('ConveyorSeg')
    hw = BELT_W / 2
    for sx in (-1, 1):
        x = sx * (hw + .55)
        P.add(T(rbox((1.1, 1.6, L), .15), (x, .55, -L / 2)), sh('wood', .52, .2))
        P.add(T(rbox((.5, .3, L), .08), (x + sx * .05, 1.45, -L / 2)), sh('dark', .55, .2))
        for k in range(4):                                                       # plank seams + roller hubs
            z = -L * (k + .5) / 4
            P.add(T(T(lathe([(.36, 0), (.36, .2), (.2, .3), (0, .3)], 8), (0, 0, 0), 0, 0, -90 * sx), (x + sx * .5, .85, z)), sh('dark', .6, .1))
        for z in (-1.0, -L + 1.0):
            P.add(T(rbox((1.6, 1.2, 1.6), .2), (x, .1, z)), sh('stone', .52))
    P.add(T(box((BELT_W, .3, L)), (0, BELT_Y - .15, -L / 2)), sh('dark', .45, .15, .01))
    P.add(T(box((BELT_W - .2, 1.1, L - .05)), (0, .8, -L / 2)), sh('dark', .25, .05, .0))
    # chevrons every 4 studs (two bars meeting, apex toward +Z)
    for k in range(int(L / 4)):
        z = -2.0 - k * 4.0
        for sx in (-1, 1):
            a = V3((sx * 3.2, BELT_Y + .02, z - 1.4)); b = V3((0, BELT_Y + .02, z + .6))
            P.add(bar(a, b, .55, .12, .03), sh('cream', .7, .1, .01))
    return P

def conveyor_end():
    """end cap block for the belt (roller drum + boards)"""
    P = Prop('ConveyorCap')
    P.add(T(T(lathe([(.95, 0), (.95, BELT_W + .2), (0, BELT_W + .2)], 10), (0, 0, 0), 0, 0, 90), (BELT_W / 2 + .1, 1.0, 0)), sh('dark', .5, .1))
    for sx in (-1, 1):
        P.add(T(rbox((1.1, 1.8, 2.0), .2), (sx * (BELT_W / 2 + .55), .6, 0)), sh('wood', .5))
    return P

def lane_lamp():
    """lane lamp: stone base, honey post with an iron arm, an egg-shaped glowing lantern in an iron cage, accent-free"""
    P = Prop('EggLamp')
    P.add(lathe([(1.0, -.4), (1.0, .4), (.75, .65), (.5, .7), (0, .7)], 6), sh('stone', .55))
    P.add(lathe([(.32, .6), (.28, 7.6), (.42, 7.8), (.42, 8.2), (0, 8.2)], 6), sh('wood', .55, .15))
    P.add(bar((0, 7.8, 0), (0, 8.4, -1.5), .22, .22, .04), sh('dark', .5))
    P.add(T(lathe([(.5, 0), (.6, .2), (.3, .35), (0, .35)], 6), (0, 8.05, -1.6)), sh('dark', .45))
    P.gadd(T(lathe(egg_profile(.55, 1.5, 6), 8), (0, 6.5, -1.6)), 'lamp')
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        P.add(tube([V3((math.cos(a) * .55, 6.45, -1.6 + math.sin(a) * .55)), V3((math.cos(a) * .62, 7.2, -1.6 + math.sin(a) * .62)),
                    V3((math.cos(a) * .2, 8.05, -1.6 + math.sin(a) * .2))], .06, sides=3), sh('dark', .5))
    P.add(T(lathe([(.6, 0), (.6, .15), (0, .15)], 6), (0, 6.35, -1.6)), sh('dark', .45))
    return P

def deco_egg(k=0):
    """giant painted egg (lane / plaza decor) on a straw nest on a stone plinth"""
    combos = (('cream', 'red', 'sky'), ('sky', 'yellow', 'cream'), ('pink', 'teal', 'cream'), ('yellow', 'purple', 'orange'),
              ('teal', 'orange', 'cream'), ('purple', 'yellow', 'pink'))
    sh_, band, b2 = combos[k % len(combos)]
    P = Prop('GiantEgg%d' % k)
    P.add(lathe([(3.0, -.4), (3.0, .6), (2.7, .9), (0, .9)], 8, math.pi / 8), sh('stone', .55, .2, .03))
    straw_nest(P, (0, .8, 0), 2.6, 1.5, 10, seed=k + 20, wisps=9)
    egg(P, (0, 1.4, 0), 2.1, 5.6, sh_, band, b2, n=10, m=8, tilt=6 * (1 if k % 2 else -1), spots=6, seed=k)
    return P

def foot_bridge(span=30.0, w=7.0):
    """humped plank footbridge over the belt (along X): stone abutments on the walkways, a plank deck on an arch of two
    honey stringers, posts with egg knobs, rope-free rails. Deck clears the belt by > 4 studs"""
    P = Prop('EggBridge')
    n = 12; rise = 6.2; hw = span / 2
    def yd(x): return .3 + rise * math.cos(min(1.0, abs(x) / hw) * math.pi / 2) ** .9
    for sx in (-1, 1):
        P.add(T(rbox((3.0, 1.6, w + 1.6), .3), (sx * (hw - .8), .3, 0)), sh('stone', .55, .2, .03))
    xs = [lerp(-hw, hw, i / n) for i in range(n + 1)]
    for sz in (-1, 1):
        P.add(tube([V3((x, yd(x) - .6, sz * (w / 2 - .2))) for x in xs], .38, sides=4, flat=(1.0, 1.6)), sh('wood', .45, .15))
    for a, b in zip(xs, xs[1:]):
        xm = (a + b) / 2; ang = math.degrees(math.atan2(yd(b) - yd(a), b - a))
        P.add(T(T(rbox((b - a - .15, .35, w), .08), (0, 0, 0), 0, 0, ang), (xm, (yd(a) + yd(b)) / 2, 0)), sh('wood', .62 + .05 * ((xs.index(a)) % 2), .2))
    for sz in (-1, 1):
        for i in range(0, n + 1, 2):
            x = xs[i]; y = yd(x)
            P.add(T(rbox((.45, 2.9, .45), .08), (x, y + 1.3, sz * (w / 2 + .1))), sh('wood', .55))
            P.add(T(lathe(egg_profile(.32, .75, 5), 6), (x, y + 2.75, sz * (w / 2 + .1))), sh('cream', .8, .15))
        P.add(tube([V3((x, yd(x) + 2.4, sz * (w / 2 + .1))) for x in xs], .17, sides=4), sh('wood', .5))
        P.add(tube([V3((x, yd(x) + 1.2, sz * (w / 2 + .1))) for x in xs], .12, sides=4), sh('wood', .45))
    return P

# ------------------------------------------------------------------ hero: the Great Egg Hatchery (belt head)
def hatchery():
    """the egg dispenser at the north head of the lane. Concept: a giant cracked egg that is also a machine. A tiered
    stone + honey-wood base, a huge straw nest, the egg (cream with a sky + yellow zigzag band) split along a jagged crack
    with the top shell lifted on two iron hinge arms; inside a glowing golden yolk core. At the front a riveted iron
    hatch tunnel (arched opening, glow inside) feeds the belt; two incubator tanks with glowing domes, copper-free iron
    pipes, a cog wheel on each side, egg-lamp crown on the lifted shell. Front = -Z... turned to face the lane (south)"""
    P = Prop('EggHatchery')
    # base tiers
    chan = lambda: T(box((14.2, 13.0, 16.0)), (0, 6.7, -26.0))
    P.add(G.bool_diff(lathe([(26, -1.0), (26, 1.4), (24.5, 2.0), (0, 2.0)], 12, math.pi / 12), chan()), sh('stone', .5, .2, .03))
    P.add(G.bool_diff(lathe([(24.6, 1.8), (24.6, 2.4), (22.0, 2.4), (22.0, 1.8)], 12, math.pi / 12), chan()), sh('yellow', .5))
    P.add(G.bool_diff(lathe([(21.0, 2.0), (21.0, 5.2), (19.5, 5.8), (0, 5.8)], 12, math.pi / 12), chan()), sh('wood', .5, .2, .03))
    for k in range(10):                                                         # egg lamps round the base rim
        a = (k + .5) * math.tau / 10
        if abs(math.cos(a)) < .42 and math.sin(a) < 0: continue                  # keep the hatch front clear
        x, z = math.cos(a) * 23.3, math.sin(a) * 23.3
        P.add(T(lathe([(.6, 0), (.45, .4), (.3, 3.2), (.55, 3.5), (0, 3.6)], 6), (x, 2.0, z)), sh('wood', .5))
        P.gadd(T(lathe(egg_profile(.6, 1.5, 5), 6), (x, 5.5, z)), 'lamp')
        P.add(T(lathe([(.65, 0), (.7, .2), (0, .3)], 6), (x, 6.95, z)), sh('dark', .45))
    for k in range(12):                                                         # plank seams on the wood drum
        a = k * math.tau / 12
        P.add(T(rbox((.4, 3.4, .5), .06), (math.cos(a) * 21.05, 3.6, math.sin(a) * 21.05), -math.degrees(a)), sh('wood', .35))
    straw_nest(P, (0, 5.5, 0), 17.0, 6.0, 14, seed=9, wisps=18)
    # the egg: lower shell (cut by a jagged crack line), lifted top shell
    R, H = 13.5, 34.0; y0 = 7.0; n = 14
    prof = egg_profile(R, H, 22)
    def r_at(y):
        for (ra, ya), (rb, yb) in zip(prof, prof[1:]):
            if ya <= y <= yb: return lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6))
        return 0.0
    yc = H * .56
    crack = [yc + (2.0 if i % 2 else -1.6) for i in range(n)]               # jagged crack height per column
    def shell(lower):
        bm = bmesh.new(); rows = []
        ys = [p[1] for p in prof]
        for i in range(n):
            a = i * math.tau / n; col = []
            yy = [y for y in ys if (y < crack[i] if lower else y > crack[i])]
            yy = ([] if lower else [crack[i]]) + yy + ([crack[i]] if lower else [])
            col = [(a, y) for y in yy]
            rows.append(col)
        # resample each column to the same count
        m = 10; cols = []
        for i in range(n):
            ys_i = [y for _, y in rows[i]]; lo, hi = (0.0, crack[i]) if lower else (crack[i], H)
            cols.append([lerp(lo, hi, j / m) for j in range(m + 1)])
        V = []
        for i in range(n):
            a = i * math.tau / n
            V.append([bm.verts.new((math.cos(a) * r_at(y), y, math.sin(a) * r_at(y))) for y in cols[i]])
        for i in range(n):
            j = (i + 1) % n
            for k in range(m):
                bm.faces.new((V[i][k], V[i][k + 1], V[j][k + 1], V[j][k]))
        # thickness rim at the crack
        inner = []
        k_rim = m if lower else 0
        for i in range(n):
            a = i * math.tau / n; y = cols[i][k_rim]; r = r_at(y) - 1.0
            inner.append(bm.verts.new((math.cos(a) * r, y, math.sin(a) * r)))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((V[i][k_rim], V[j][k_rim], inner[j], inner[i]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-3)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        return bm
    low = shell(True)
    P.add(T(low, (0, y0, 0)), sh('cream', .74, .22, .03))
    # inner dark of the lower shell + glowing yolk core
    P.add(T(lathe([(0, 0), (R * .7, 2), (R * .9, 8), (R * .93, yc - 2.5), (0, yc - 2.5)], 12), (0, y0 + .5, 0)), sh('cream', .4, .1, .02))
    P.gadd(T(lathe([(0, 0), (5.2, .8), (6.4, 3.0), (5.6, 5.8), (2.8, 7.2), (0, 7.5)], 10), (0, y0 + yc - 6.0, 0)), 'hatch')
    # painted zigzag band on the lower shell (sky) + yellow ring
    bm = bmesh.new(); N = n * 2; ya, yb = H * .3, H * .44; ring = []
    for i in range(N + 1):
        a = i * math.tau / N
        y1 = yb if i % 2 else ya + (yb - ya) * .45; y2 = ya + (yb - ya) * .55 if i % 2 else ya
        ring.append([bm.verts.new((math.cos(a) * r_at(y) * 1.02, y, math.sin(a) * r_at(y) * 1.02)) for y in (y2, y1)])
    for A, Bq in zip(ring, ring[1:]): bm.faces.new((A[0], Bq[0], Bq[1], A[1]))
    bm.normal_update()
    for f in bm.faces:
        cc = f.calc_center_median()
        if f.normal.dot(V3((cc.x, 0, cc.z))) < 0: f.normal_flip()
    P.add(T(bm, (0, y0, 0)), sh('sky', .6, .15))
    P.add(T(torus(r_at(H * .22) * 1.02, .45, n, 4), (0, y0 + H * .22, 0)), sh('yellow', .6))
    # lifted top shell: tilted back (+Z) on hinge arms
    top = shell(False)
    lift = 7.5; tilt = 24
    T(top, (0, -yc, 0)); T(top, (0, 0, 0), 0, tilt); T(top, (0, y0 + yc + lift, 3.5))
    P.add(top, sh('cream', .78, .22, .03))
    for sx in (-1, 1):                                                          # iron hinge arms (back) with knuckles
        a = V3((sx * 5.0, y0 + yc - 1.0, R * .82)); b = V3((sx * 4.4, y0 + yc + lift + 1.2, R * .8 + 2.0))
        P.add(tube([a, (a + b) / 2 + V3((0, 0, 2.2)), b], .7, sides=6), sh('dark', .5, .15))
        P.add(T(T(T(cyl(1.2, 1.8, 8), (0, -.9, 0)), (0, 0, 0), 0, 0, 90), a), sh('yellow', .5))
        P.add(T(T(T(cyl(1.0, 1.6, 8), (0, -.8, 0)), (0, 0, 0), 0, 0, 90), b), sh('yellow', .5))
    tp = Matrix.Rotation(math.radians(tilt), 3, 'X') @ V3((0, H - yc - .5, 0)) + V3((0, y0 + yc + lift, 3.5))
    egg_finial(P, tuple(tp), 2.6, 'yellow', 8)
    # front hatch tunnel: riveted iron arch over the belt exit (opening 12 wide, 9 high), glow set back inside
    zf = -23.0; ay = .25
    fr = G.arch_frame(7.0, 4.5, 1.6, -2.0, 2.0)
    P.add(T(fr, (0, ay, zf)), sh('dark', .5, .2))
    P.add(T(G.arch_frame(8.6, 4.5, .55, -2.2, 2.2), (0, ay, zf)), sh('yellow', .55))
    tun = G.arch_tunnel(7.0, 4.5, zf - 2.0, zf + 6.5)
    P.add(T(tun, (0, ay, 0)), sh('dark', .3, .05))
    P.gadd(T(G.arch_cap(6.95, 4.45, zf + 6.0), (0, ay, 0)), 'hatch')
    for k in range(9):                                                         # rivets on the arch face
        a = math.pi * k / 8; r = 7.8
        P.add(T(T(lathe([(.3, 0), (.25, .2), (0, .25)], 5), (0, 0, 0), 0, -90), (math.cos(a) * r, ay + 4.5 + math.sin(a) * r, zf - 2.05)), sh('stone', .8))
    # side incubator tanks with glowing domes + pipes + cog wheels
    for sx in (-1, 1):
        tx, tz = sx * 18.0, -10.0
        P.add(T(lathe([(3.4, 0), (3.4, .8), (3.0, 1.2), (3.0, 7.2), (3.4, 7.6), (3.4, 8.2), (0, 8.2)], 8, math.pi / 8), (tx, 5.8, tz)), sh('dark', .5, .15))
        for y in (8.2, 11.4):
            P.add(T(torus(3.05, .22, 8, 4), (tx, y, tz)), sh('yellow', .55))
        P.gadd(T(lathe([(2.6, 0), (2.5, 1.2), (1.6, 2.4), (0, 2.8)], 8, math.pi / 8), (tx, 14.0, tz)), 'heat')
        P.add(T(lathe([(.5, 0), (.4, .6), (0, .9)], 6), (tx, 16.8, tz)), sh('dark', .5))
        P.add(tube([V3((tx - sx * 2.6, 11.0, tz)), V3((sx * 11.0, 13.0, tz + 1.5)), V3((sx * 9.5, 15.0, -6.0))], .55, sides=6), sh('dark', .55, .15))
        # cog wheel on the side of the wood drum
        cx, cz = sx * 20.2, 6.0
        cog = lathe([(2.4, 0), (2.4, .7), (0, .7)], 16)
        for t in range(8):
            a = t * math.tau / 8
            tooth = T(rbox((.9, .7, .9), .08), (math.cos(a) * 2.7, .35, math.sin(a) * 2.7), -math.degrees(a))
            P.add(T(T(tooth, (0, 0, 0), 0, 0, 90 * sx), (cx, 7.8, cz)), sh('yellow', .5))
        P.add(T(T(cog, (0, 0, 0), 0, 0, 90 * sx), (cx, 7.8, cz)), sh('yellow', .55))
        P.add(T(T(lathe([(.8, 0), (.8, 1.2), (0, 1.2)], 8), (0, 0, 0), 0, 0, 90 * sx), (cx, 7.8, cz)), sh('dark', .5))
    return P

def egg_drain():
    """the drain at the south end: a low woven basket ring (honey staves + cream wicker bands) round a dark pit that the
    belt tips into, a faint cyan glow deep inside, on a stone plinth; two posts with egg lamps. Low (< 4 studs) so the
    spawn keeps its view up the lane to the hatchery"""
    P = Prop('EggDrain')
    P.add(T(rbox((16.0, 1.4, 12.0), .4), (0, .2, 0)), sh('stone', .52, .2, .03))
    P.add(G.bool_diff(lathe([(7.2, .6), (7.6, 2.2), (7.4, 3.2), (6.6, 3.2), (6.0, 1.2), (0, 1.2)], 14), T(cyl(6.2, 4.0, 14), (0, 1.25, 0))), sh('wood', .55, .2, .03))
    for k in range(14):
        a = k * math.tau / 14
        P.add(T(rbox((.35, 2.9, .5), .06), (math.cos(a) * 7.45, 1.85, math.sin(a) * 7.45), -math.degrees(a)), sh('wood', .38))
    for y, r in ((1.4, 7.45), (2.6, 7.55)):
        P.add(T(torus(r, .26, 14, 4), (0, y, 0)), sh('cream', .7, .15))
    P.add(T(lathe([(6.0, 0), (4.0, -2.0), (0, -2.2)], 14), (0, 1.25, 0)), sh('dark', .15, .02, 0))
    P.gadd(T(lathe([(2.6, 0), (0, 0)], 10), (0, -.85, 0)), 'drain')
    P.add(T(T(rbox((10.4, .35, 4.0), .1), (0, 0, 0), 0, 14), (0, 1.95, -6.4)), sh('dark', .5, .1))     # chute lip from the belt
    for sx in (-1, 1):
        post(P, (sx * 7.6, .5, -5.0), 7.0, .7, 'wood', 'sky')
        P.add(bar((sx * 7.6, 7.0, -5.0), (sx * 7.6, 7.4, -6.4), .2, .2, .03), sh('dark', .5))
        P.gadd(T(lathe(egg_profile(.5, 1.3, 5), 6), (sx * 7.6, 5.9, -6.4)), 'lamp')
        P.add(T(lathe([(.55, 0), (.6, .15), (0, .15)], 6), (sx * 7.6, 7.15, -6.4)), sh('dark', .45))
    return P

def gate_mat(acc='red'):
    """welcome path in the plot colour on the lane walkway in front of a gate: rounded accent slab with a cream egg inlay"""
    P = Prop('GateMat_%s' % acc)
    P.add(T(rbox((14.0, .8, 6.0), .15), (0, .05, 0)), sh(acc, .52, .1, .01))
    P.add(T(rbox((13.0, .1, 5.0), .04), (0, .47, 0)), sh(acc, .64, .1, .01))
    eggp = [(math.sin(a) * 1.0 * (1.06 - .2 * ((1 - math.cos(a)) / 2)), 1.4 * (1 - math.cos(a)) - 1.4) for a in [math.pi * k / 7 for k in range(8)]]
    poly = [(x, y) for x, y in eggp] + [(-x, y) for x, y in reversed(eggp[1:-1])]
    P.add(T(ngon_prism([(y, x) for x, y in poly], .45, .56), (0, 0, 0)), sh('cream', .85, .05, .0))
    return P

# ------------------------------------------------------------------ spawn + shops
def stall(name, roof_a, roof_b, W=12.0, D=7.0):
    """market stand shell: stone footing, honey counter with a cream top, 4 posts, a striped low-poly awning (alternating
    roof_a / roof_b panels, scalloped front edge), blank cream sign board on the ridge (GUI). Front = -Z"""
    P = Prop(name)
    P.add(T(rbox((W + 1.2, .8, D + 1.2), .25), (0, .1, 0)), sh('stone', .55, .2, .03))
    P.add(T(rbox((W, 3.0, 2.0), .2), (0, 2.0, -D / 2 + 1.0)), sh('wood', .55, .2))
    P.add(T(rbox((W + .4, .35, 2.5), .1), (0, 3.6, -D / 2 + 1.0)), sh('cream', .8, .1))
    for k in range(5):
        P.add(T(rbox(((W - 1) / 5 - .3, 2.2, .12), .05), (-W / 2 + .5 + (W - 1) / 5 * (k + .5), 2.0, -D / 2 - .02)), sh('wood', .4))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(rbox((.6, 7.6, .6), .1), (sx * (W / 2 - .3), 4.1, sz * (D / 2 - .3))), sh('wood', .5, .15))
    P.add(T(rbox((W - .6, 7.4, .4), .1), (0, 4.0, D / 2 - .3)), sh('cream', .74, .12))         # back wall
    # awning: 6 striped panels sloping down to the front, a scalloped valance (half-octagon tabs) under the front edge
    n = 6; pw = (W + 1.6) / n; ang = 16; tz = math.tan(math.radians(ang))
    for k in range(n):
        x = -(W + 1.6) / 2 + pw * (k + .5); col = roof_a if k % 2 == 0 else roof_b
        P.add(T(T(rbox((pw, .3, D + 2.0), .06), (0, 0, 0), 0, -ang), (x, 8.3, -.3)), sh(col, .6, .25))
        yf = 8.3 - tz * (D / 2 + 1.3)
        tab = [(-pw / 2, 0)] + [(math.cos(math.pi + math.pi * i / 4) * pw / 2, math.sin(math.pi + math.pi * i / 4) * pw * .38) for i in range(1, 4)] + [(pw / 2, 0)]
        P.add(upright(tab, .2, (x, yf, -D / 2 - 1.15)), sh(col, .52, .1))
    P.add(T(rbox((W + 2.0, .4, .5), .1), (0, 8.3 + tz * (D / 2 + .7) - .5, D / 2 + .7)), sh('wood', .45))
    P.add(T(rbox((W * .62, 2.6, .5), .2), (0, 10.7, D / 2 - .1)), sh('wood', .5))
    P.add(T(rbox((W * .62 - .8, 1.9, .2), .05), (0, 10.7, D / 2 - .45)), sh('cream', .86, .05, .005))   # blank sign (GUI)
    return P

def egg_shop():
    """Egg Shop stand (buy): yellow / cream awning, egg cartons and painted eggs on the counter, a crate pyramid of eggs
    beside it, a big egg on a nest on the roof"""
    P = stall('EggShop', 'yellow', 'cream')
    for k, (x, c) in enumerate(((-4.0, 'sky'), (-1.4, 'pink'), (1.4, 'teal'), (4.0, 'orange'))):
        P.add(T(rbox((2.2, .5, 1.4), .1), (x, 4.0, -2.5)), sh('cream', .6, .1))
        for j in range(2):
            egg(P, (x - .5 + j, 4.15, -2.5), .38, 1.0, c if j else 'cream', None, None, n=6, m=5)
    for i, (x, y, z) in enumerate(((7.6, .5, -1.0), (7.6, .5, 1.4), (7.6, 1.9, .2))):
        P.add(T(rbox((2.2, 1.4, 2.2), .15), (x, y + .7, z)), sh('wood', .58))
        for j in range(3):
            egg(P, (x - .6 + j * .6, y + 1.3, z), .3, .8, ('cream', 'yellow', 'sky')[(i + j) % 3], None, None, n=6, m=5)
    straw_nest(P, (0, 12.0, 3.3), 1.8, 1.0, 9, seed=31, wisps=5)
    egg(P, (0, 12.4, 3.3), 1.3, 3.2, 'cream', 'yellow', 'sky', n=8, m=7, seed=3)
    return P

def upgrade_stand():
    """Upgrades stand: teal / cream awning, a workbench counter with a vice-free incubator machine (glowing dome), a gear
    icon disc on the roof (shape, no text), tool rack with a hammer and a wrench on the back wall"""
    P = stall('UpgradeStand', 'teal', 'cream')
    P.add(T(rbox((3.4, 1.4, 1.8), .2), (-2.8, 4.5, -2.4)), sh('dark', .5))
    P.gadd(T(lathe([(1.3, 0), (1.2, .7), (.7, 1.3), (0, 1.5)], 8), (-2.8, 5.2, -2.4)), 'heat')
    egg(P, (-2.8, 5.3, -2.4), .5, 1.3, 'cream', 'teal', None, n=6, m=5)
    for x in (1.6, 3.4):
        P.add(T(T(lathe([(.25, 0), (.25, 1.6), (0, 1.6)], 6), (0, 0, 0), 0, 0, 90), (x + .8, 4.1, -2.6)), sh('wood', .55))
    P.add(T(rbox((1.4, .6, .7), .1), (2.6, 4.2, -2.6)), sh('dark', .55))
    # gear icon on the roof ridge
    gx, gy, gz = 0, 12.2, 3.0
    gear = lathe([(1.8, 0), (1.8, .5), (0, .5)], 12)
    P.add(T(T(T(gear, (0, -.25, 0)), (0, 0, 0), 0, -90), (gx, gy, gz)), sh('teal', .55))
    for t in range(8):
        a = t * math.tau / 8
        tooth = T(rbox((.8, .8, .5), .08), (math.cos(a) * 2.05, math.sin(a) * 2.05, 0), 0, 0, math.degrees(a))
        P.add(T(tooth, (gx, gy, gz)), sh('teal', .5))
    P.add(T(T(T(lathe([(.7, 0), (.7, .7), (0, .7)], 8), (0, -.35, 0)), (0, 0, 0), 0, -90), (gx, gy, gz - .1)), sh('cream', .85))
    P.add(T(rbox((.6, 2.6, .6), .1), (gx, 10.6, gz)), sh('wood', .5))
    # tools on the back wall
    P.add(T(rbox((6.0, .3, .3), .05), (0, 6.2, 2.9)), sh('wood', .45))
    P.add(bar((-1.5, 6.1, 2.75), (-1.5, 4.2, 2.75), .25, .25, .04), sh('wood', .6)); P.add(T(rbox((1.3, .6, .5), .1), (-1.5, 6.2, 2.7)), sh('dark', .6))
    P.add(bar((1.5, 6.1, 2.75), (1.5, 4.4, 2.75), .25, .2, .04), sh('dark', .7)); P.add(T(torus(.4, .12, 6, 3), (1.5, 6.2, 2.75)), sh('dark', .7))
    return P

def sell_stand():
    """Sell stand: orange / cream awning, a balance scale with egg on one pan and coins on the other, coin heaps and a
    tied sack, a coin disc icon on the roof"""
    P = stall('SellStand', 'orange', 'cream')
    sx0 = -2.0
    P.add(T(lathe([(.9, 0), (.9, .3), (.3, .5), (.25, 3.0), (0, 3.0)], 6), (sx0, 3.8, -2.4)), sh('dark', .55))
    P.add(bar((sx0 - 2.0, 6.7, -2.4), (sx0 + 2.0, 6.9, -2.4), .2, .2, .03), sh('yellow', .6))
    for dx, dy in ((-2.0, 4.6), (2.0, 4.8)):
        for k in (-1, 1):
            P.add(tube([V3((sx0 + dx, 6.75, -2.4)), V3((sx0 + dx + k * .55, dy + .2, -2.4))], .04, sides=3), sh('dark', .6))
        P.add(T(lathe([(.1, 0), (.75, .15), (.8, .3), (0, .3)], 8), (sx0 + dx, dy, -2.4)), sh('yellow', .6))
    egg(P, (sx0 - 2.0, 4.85, -2.4), .38, 1.0, 'cream', 'orange', None, n=6, m=5)
    for k in range(3):
        P.add(T(lathe([(.3, 0), (.3, .1), (0, .1)], 8), (sx0 + 2.0, 5.1 + k * .11, -2.4)), sh('yellow', .65))
    for x, z, n in ((2.5, -2.4, 4), (4.0, -2.1, 3)):
        for k in range(n):
            P.add(T(lathe([(.45, 0), (.45, .14), (0, .14)], 8), (x + (k % 2) * .1, 3.8 + k * .15, z)), sh('yellow', .6 + .04 * k))
    P.add(T(blob(1.0, 4, 18, .9), (7.4, 1.1, -1.0), s=(1.2, 1.3, 1.2)), sh('cream', .55, .2))
    P.add(tube([V3((7.4, 2.2, -1.0)), V3((7.4, 2.8, -1.0))], [.35, .5], sides=6), sh('cream', .6))
    P.add(T(torus(.36, .08, 6, 3), (7.4, 2.35, -1.0)), sh('wood', .4))
    for k in range(5):
        P.add(T(lathe([(.5, 0), (.5, .15), (0, .15)], 8), (6.6 + (k % 3) * .6, .4 + (k // 3) * .16, -3.0 + k * .2)), sh('yellow', .62))
    coin = lathe([(1.7, 0), (1.7, .45), (0, .45)], 12)
    P.add(T(T(T(coin, (0, -.22, 0)), (0, 0, 0), 0, -90), (0, 12.2, 3.0)), sh('yellow', .62))
    P.add(T(T(T(torus(1.35, .14, 12, 4), (0, 0, 0), 0, 90), (0, 0, 0)), (0, 12.2, 2.7)), sh('orange', .55))
    P.add(T(rbox((.6, 2.6, .6), .1), (0, 10.6, 3.0)), sh('wood', .5))
    return P

def nest_statue():
    """spawn centrepiece: round stone plinth with steps, a big straw nest holding three painted eggs (one standing tall)"""
    P = Prop('NestStatue')
    P.add(lathe([(6.5, -.4), (6.5, .5), (5.6, .5), (5.6, 1.1), (4.8, 1.1), (4.8, 2.6), (4.4, 3.0), (0, 3.0)], 10, math.pi / 10), sh('stone', .55, .2, .03))
    P.add(T(torus(4.85, .22, 10, 4), (0, 2.3, 0)), sh('yellow', .55))
    straw_nest(P, (0, 2.9, 0), 4.2, 2.0, 10, seed=41, wisps=10)
    egg(P, (0, 3.6, 0), 1.7, 4.6, 'cream', 'pink', 'yellow', n=10, m=8, spots=5, seed=1)
    egg(P, (-2.3, 3.8, 1.0), 1.1, 2.9, 'sky', 'yellow', None, n=8, m=6, tilt=-14, yaw=40)
    egg(P, (2.2, 3.8, .8), 1.1, 2.9, 'yellow', 'teal', None, n=8, m=6, tilt=16, yaw=-30)
    return P

def bench():
    P = Prop('ParkBench')
    for sx in (-1, 1):
        P.add(T(rbox((.6, 2.0, 2.0), .15), (sx * 2.6, .7, 0)), sh('stone', .55))
    for k in range(3):
        P.add(T(rbox((6.4, .3, .55), .08), (0, 1.75, -.7 + k * .65)), sh('wood', .6 + .03 * k))
    for k in range(2):
        P.add(T(T(rbox((6.4, .55, .25), .08), (0, 0, 0), 0, -12), (0, 2.6 + k * .7, 1.05)), sh('wood', .58))
    for sx in (-1, 1):
        P.add(bar((sx * 2.6, 1.6, .9), (sx * 2.6, 3.6, 1.25), .3, .3, .05), sh('wood', .5))
    return P

# ------------------------------------------------------------------ nature + backdrop
def tree(seed=1, h=14.0, col='leaf'):
    """low-poly round tree: tapered faceted trunk with a root flare, 3-4 faceted canopy blobs (dark under, light top)"""
    P = Prop('Tree%d' % seed); rng = random.Random(seed)
    P.add(tube([V3((0, -1.0, 0)), V3((0, h * .45, 0)), V3((rng.uniform(-.6, .6), h * .7, rng.uniform(-.6, .6)))], [h * .09, h * .07, h * .05], sides=6), sh('wood', .42, .15, .04))
    for k in range(4):
        a = k * math.pi / 2 + rng.uniform(0, .5)
        P.add(T(T(T(lathe([(h * .045, 0), (h * .02, h * .14), (0, h * .16)], 4), (0, 0, 0), 0, 0, 62), (0, 0, 0), math.degrees(a)), (0, -.2, 0)), sh('wood', .38))
    cs = [((0, h * .78, 0), h * .3)] + [((math.cos(a) * h * .18, h * (.62 + rng.uniform(-.05, .08)), math.sin(a) * h * .18), h * rng.uniform(.2, .25))
                                       for a in [rng.uniform(0, math.tau) + k * math.tau / 3 for k in range(3)]]
    G.leafy(P, cs, col, h * .45, h * 1.05, seed, sq=.82)
    return P

def pine(seed=1, h=18.0):
    """low-poly cone tree: three stacked faceted cones, a short trunk"""
    P = Prop('Pine%d' % seed); rng = random.Random(seed)
    P.add(tube([V3((0, -1.0, 0)), V3((0, h * .3, 0))], [h * .06, h * .045], sides=5), sh('wood', .4))
    for k in range(3):
        y = h * (.2 + .24 * k); r = h * (.3 - .07 * k); hh = h * (.42 - .05 * k)
        P.add(T(lathe([(r, 0), (r * .8, hh * .15), (0, hh)], 7, rng.uniform(0, 1)), (0, y, 0)),
              S('leaf', grad=(y, y + hh, .2 + .1 * k, .62 + .08 * k), up=.15, jit=.04, seed=seed + k))
    return P

def bush(seed=1, r=2.2, berry=None):
    P = Prop('Bush%d' % seed); rng = random.Random(seed)
    cs = [((0, r * .6, 0), r)] + [((math.cos(a) * r * .75, r * .45, math.sin(a) * r * .75), r * .7) for a in [k * math.tau / 3 + rng.uniform(0, .5) for k in range(3)]]
    G.leafy(P, cs, 'leaf', 0, r * 1.6, seed + 50, sq=.75)
    if berry:
        for k in range(6):
            a = rng.uniform(0, math.tau); y = rng.uniform(.5, .9) * r
            P.add(T(lathe([(0, -.25), (.25, 0), (0, .25)], 5), (math.cos(a) * r * 1.15, y, math.sin(a) * r * 1.15)), sh(berry, .6, .15))
    return P

def flower_patch(seed=1, cols=('pink', 'yellow')):
    """ground flowers: a tuft of leaves + 5-7 little 5-petal flowers (decor, no collision)"""
    P = Prop('FlowerPatch%d' % seed); rng = random.Random(seed)
    for k in range(7):
        a = rng.uniform(0, math.tau); r = rng.uniform(0, 1.6); x, z = math.cos(a) * r, math.sin(a) * r
        h = rng.uniform(.6, 1.1)
        P.add(tube([V3((x, -.1, z)), V3((x, h, z))], .05, sides=3), sh('leaf', .4))
        c = cols[k % len(cols)]
        P.add(T(lathe([(.0, -.05), (.35, .05), (.0, .12)], 5, rng.uniform(0, 1)), (x, h, z)), sh(c, .65, .15))
        P.add(T(lathe([(0, 0), (.1, .08), (0, .16)], 4), (x, h + .02, z)), sh('yellow' if c != 'yellow' else 'orange', .7))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(0, .5)
        P.add(T(T(lathe([(0, 0), (.22, .4), (0, 1.0)], 3), (0, 0, 0), 0, 0, 40), (0, -.1, 0), math.degrees(a)), sh('leaf', .5))
    return P

def boulder(seed=1, r=2.5):
    P = Prop('Boulder%d' % seed)
    P.add(G.rock((r, r * .62, r * .85), seed=seed, n=16, flat=.4), S('stone', base=.5, up=.25, jit=.06, seed=seed))
    return P

def ranch_fence(L=12.0):
    """island edge ranch fence: two round-topped honey posts, three split rails (cheap: seen from afar)"""
    P = Prop('RanchFence')
    P.add(T(rbox((.8, 4.6, .8), .15), (0, 1.6, 0)), sh('wood', .5, .15))
    P.add(T(lathe([(.45, 0), (.3, .3), (0, .4)], 5), (0, 3.9, 0)), sh('wood', .62))
    for y in (1.1, 2.2, 3.3):                                                   # rails stop short of the next post (no overlap)
        P.add(T(rbox((L - 1.3, .4, .3), .08), (L / 2, y, .3)), sh('wood', .58 + y * .02, .15))
    return P

def barn():
    """backdrop red barn (seen from across the lake): stone plinth, red board walls with cream X-braced doors and trim,
    gambrel roof in dark slate with cream eaves, hay loft opening, little cupola. ~16 x 22"""
    P = Prop('BarnBackdrop')
    W, D, Hw = 16.0, 22.0, 9.0
    P.add(T(rbox((W + 1, 1.4, D + 1), .3), (0, .2, 0)), sh('stone', .5))
    P.add(T(rbox((W, Hw, D), .2), (0, 1 + Hw / 2, 0)), sh('red', .55, .15, .02))
    # gambrel roof profile (lower steep + upper shallow) as an upright prism along Z
    prof = [(-W / 2 - .8, 0), (W / 2 + .8, 0), (W / 2 - 1.2, 4.6), (0, 7.2), (-W / 2 + 1.2, 4.6)]
    P.add(upright(prof, D + 1.6, (0, Hw + 1.0, D / 2 + .8)), sh('dark', .55, .25, .02))
    gab = [(-W / 2, 0), (W / 2, 0), (W / 2 - 1.8, 4.1), (0, 6.4), (-W / 2 + 1.8, 4.1)]
    for z in (-D / 2 - .05, D / 2 + .25):
        P.add(upright(gab, .3, (0, Hw + 1.0, z)), sh('red', .5, .1, .02))
    for sz in (-1, 1):
        zz = sz * (D / 2 + .1)
        P.add(T(rbox((7.0, 6.4, .3), .1), (0, 4.2, zz)), sh('cream', .82, .1))
        P.add(T(rbox((6.2, 5.6, .32), .05), (0, 4.2, zz)), sh('red', .45, .1))
        for a in (1, -1):
            P.add(bar((-3.0, 1.6, zz + sz * .2), (3.0, 6.8, zz + sz * .2) if a > 0 else (3.0, 1.6, zz + sz * .2), .35, .2, .03) if False else
                  bar((-2.9, 1.7 if a > 0 else 6.7, zz + sz * .22), (2.9, 6.7 if a > 0 else 1.7, zz + sz * .22), .4, .2, .03), sh('cream', .8))
        P.add(T(rbox((3.0, 2.4, .3), .1), (0, Hw + 3.2, zz)), sh('cream', .82))
        P.add(T(rbox((2.4, 1.8, .34), .05), (0, Hw + 3.2, zz)), sh('dark', .3))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(rbox((.7, Hw, .7), .1), (sx * W / 2, 1 + Hw / 2, sz * D / 2)), sh('cream', .82))
    P.add(T(rbox((2.4, 2.2, 2.4), .15), (0, Hw + 8.7, 0)), sh('red', .55))
    P.add(T(lathe([(2.1, 0), (0, 1.8)], 4, math.pi / 4), (0, Hw + 9.8, 0)), sh('dark', .5))
    return P

def silo():
    P = Prop('SiloBackdrop')
    P.add(lathe([(4.2, -.4), (4.2, .6), (3.8, .9), (3.8, 18.0), (4.0, 18.3), (3.0, 20.6), (1.0, 21.6), (0, 21.8)], 10), sh('cream', .72, .18, .02))
    for y in (4.0, 9.0, 14.0):
        P.add(T(torus(3.84, .18, 10, 3), (0, y, 0)), sh('dark', .5))
    P.add(T(lathe([(1.2, 0), (1.0, .6), (0, .9)], 6), (0, 21.6, 0)), sh('red', .55))
    return P

def windmill():
    """backdrop windmill: tapered octagonal tower (cream, honey trim), red cap, 4 lattice sails (frames, not cloth)"""
    P = Prop('Windmill')
    P.add(lathe([(5.0, -.4), (5.0, .8), (4.6, 1.0), (3.2, 16.0), (3.5, 16.4), (3.5, 17.0), (0, 17.0)], 8, math.pi / 8), sh('cream', .74, .2, .02))
    for y in (5.0, 11.0):
        r = lerp(4.6, 3.2, (y - 1) / 15)
        P.add(T(torus(r + .05, .2, 8, 3), (0, y, 0)), sh('wood', .5))
    P.add(T(rbox((2.4, 3.6, .3), .1), (0, 2.2, -4.55)), sh('wood', .45))
    P.add(T(lathe([(3.8, 0), (3.6, 1.2), (2.2, 3.6), (0, 4.4)], 8, math.pi / 8), (0, 16.8, 0)), sh('red', .55, .2))
    hub = V3((0, 18.6, -3.6))
    P.add(T(T(lathe([(.9, 0), (.9, 1.6), (.4, 2.0), (0, 2.0)], 8), (0, 0, 0), 0, -90), hub + V3((0, 0, 1.6))), sh('dark', .5))
    for k in range(4):
        a = k * math.pi / 2 + .35
        d = V3((math.cos(a), math.sin(a), 0)); nrm = V3((-math.sin(a), math.cos(a), 0))
        tip = hub + d * 13.0
        P.add(bar(hub, tip, .45, .45, .05), sh('wood', .5))
        for t in (.3, .5, .7, .9):
            p = hub + d * 13.0 * t
            P.add(bar(p, p + nrm * 2.6, .2, .2, .03), sh('wood', .55))
        P.add(bar(hub + d * 3.5 + nrm * 2.6, tip + nrm * 2.6, .2, .2, .03), sh('wood', .55))
        P.add(T(T(rbox((9.5, 2.3, .1), .02), (0, 0, 0), 0, 0, math.degrees(a)), hub + d * 8.3 + nrm * 1.3 + V3((0, 0, .15))), sh('cream', .8, .05))
    return P

def cloud(seed=1):
    P = Prop('Cloud%d' % seed); rng = random.Random(seed)
    for k in range(5):
        x = (k - 2) * 5.0 + rng.uniform(-1, 1); r = 5.5 - abs(k - 2) * 1.2
        P.add(T(blob(r, seed * 7 + k, 18, .7), (x, r * .4, rng.uniform(-1.5, 1.5))), S('cream', base=.9, up=.1, jit=.02))
    return P

def lily_pads(seed=1):
    P = Prop('LilyPads%d' % seed); rng = random.Random(seed)
    for k in range(4):
        a = rng.uniform(0, math.tau); r = rng.uniform(0, 3); x, z = math.cos(a) * r, math.sin(a) * r
        P.add(T(lathe([(1.0, 0), (1.0, .1), (0, .1)], 7, rng.uniform(0, 3)), (x, 0, z)), sh('leaf', .5))
        if k == 0: P.add(T(lathe([(0, 0), (.4, .2), (.3, .5), (0, .55)], 5), (x, .1, z)), sh('pink', .65))
    return P

def reeds(seed=1):
    P = Prop('Reeds%d' % seed); rng = random.Random(seed)
    for k in range(9):
        a = rng.uniform(0, math.tau); r = rng.uniform(0, 1.2); x, z = math.cos(a) * r, math.sin(a) * r; h = rng.uniform(2.5, 4.2)
        P.add(tube([V3((x, -.5, z)), V3((x + rng.uniform(-.4, .4), h, z + rng.uniform(-.4, .4)))], [.12, .02], sides=3), sh('leaf', .55))
        if k % 3 == 0: P.add(T(lathe([(.15, 0), (.18, .3), (.15, .8), (0, .9)], 4), (x, h * .7, z)), sh('wood', .35))
    return P
