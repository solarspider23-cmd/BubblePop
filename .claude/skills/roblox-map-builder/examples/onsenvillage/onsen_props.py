# Yumori Springs prop kit (mountain hot-spring village at golden hour).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: an old onsen town on terraces: cream plaster, sand ashlar, dark cedar timber, pale sage foliage. The ONLY
# saturated colours are 4 roof glazes (teal copper / indigo / plum / persimmon) + a maple red accent used sparingly.
# Signature edge detail: cedar railing bays with bronze onion caps (giboshi) on every post, along every terrace lip.
# Shared base: sand-ashlar plinth with a chamfered cap course (houses, pagoda, pools, stair cheeks).
# Machinery (Prop, S, blob, materials, to_kit) from the skill's grove module, helpers (T, bar, log, lathe, torus, ashlar)
# from the medieval example; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, spike, tube, hull, rock_pts, nz, clamp, ngon_prism

PAL = Palette({
    'cream':  ('#9c8a73', '#e9dcc3', '#fff8ea'),     # plaster (light end) + paving (mid)
    'stone':  ('#6e5d47', '#c9ad86', '#eedbbb'),     # sand ashlar, steps, lanterns
    'rock':   ('#4a4250', '#8d8090', '#c9bec6'),     # grey-violet mountain rock
    'wood':   ('#26150f', '#5a3526', '#8f5f43'),     # dark cedar timber
    'woodlt': ('#6b4a2c', '#b58a5a', '#e6c995'),     # honey wood: buckets, rope, straw, deck boards
    'leaf':   ('#5d7468', '#a7bfb3', '#dceae2'),     # pale sage foliage
    'pine':   ('#2e4237', '#5f7d67', '#a2bba2'),     # darker sage: pines, cedars
    'grass':  ('#4d6a3a', '#8fae6a', '#c9dca0'),     # banks, lawns, moss
    'water':  ('#2d6b73', '#6fb3b3', '#c4ece4'),     # milky hot-spring turquoise
    'roofA':  ('#23514c', '#4f9488', '#93d0c2'),     # teal copper glaze (pagoda + bath pavilions)
    'roofB':  ('#2c3466', '#626da7', '#a7b2e6'),     # indigo (upper inns)
    'roofC':  ('#3f2f5a', '#8a6bb4', '#c7b0e8'),     # plum (tall upper houses)
    'roofD':  ('#6e3014', '#d27b3f', '#f6b67c'),     # persimmon (market shops)
    'maple':  ('#6e1a0e', '#d24a2a', '#ff8e5a'),     # autumn maple accent (sparingly)
    'iron':   ('#1c1a1e', '#44404a', '#8a8590'),     # bronze-iron fittings
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'lamp': '#ffb35c', 'shoji': '#ffd9a6'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 2.8, 'shoji': 1.1})
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, log, lathe, torus, sag, h01 = B.T, B.bar, B.log, B.lathe, B.torus, B.sag, B.h01
ashlar, ash_sh = B.ashlar, B.ash_sh
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ roofs
def flared_roof(P, outer, inner, y0, y1, col, curl=1.0, thick=.45, tile=1.5, rings=6, conc=1.8, hips=True,
                soffit='wood', corr=.1, push=.05, hip_r=.24):
    """Asian glazed roof: a lofted surface from the eave polygon `outer` (corners [(x, z)], y0) to the inner polygon
    `inner` (same corner count, y1): concave rise, upturned corners, tile corrugation on top, wood soffit under,
    fascia band at the eave and a band at the top. hips = rounded hip ridges up every corner."""
    nC = len(outer)
    ns = []
    for i in range(nC):
        a, b = outer[i], outer[(i + 1) % nC]
        ns.append(max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / tile * 2) // 2 * 2))
    def pt(i, j, t, top):
        s = j / ns[i]
        a0 = (lerp(outer[i][0], inner[i][0], t), lerp(outer[i][1], inner[i][1], t))
        a1 = (lerp(outer[(i + 1) % nC][0], inner[(i + 1) % nC][0], t), lerp(outer[(i + 1) % nC][1], inner[(i + 1) % nC][1], t))
        x, z = lerp(a0[0], a1[0], s), lerp(a0[1], a1[1], s)
        c = (1 - 2 * min(s, 1 - s)) ** 4; w = (1 - t) ** 2.2
        k = 1 + push * c * w
        y = y0 + (y1 - y0) * t ** conc + curl * w * c
        if top: y += corr * (1 if j % 2 else -1) * (1 - t * .6) * (1 - c)
        else: y -= thick
        return (x * k, y, z * k)
    bm = bmesh.new(); TV = []; BV = []
    for k in range(rings + 1):
        t = k / rings
        TV.append([bm.verts.new(pt(i, j, t, True)) for i in range(nC) for j in range(ns[i])])
        BV.append([bm.verts.new(pt(i, j, t, False)) for i in range(nC) for j in range(ns[i])])
    M = len(TV[0])
    for k in range(rings):
        for m in range(M):
            n = (m + 1) % M
            f = bm.faces.new((TV[k][m], TV[k][n], TV[k + 1][n], TV[k + 1][m])); f.material_index = 0 if m % 2 else 3
            f = bm.faces.new((BV[k][n], BV[k][m], BV[k + 1][m], BV[k + 1][n])); f.material_index = 1
    for m in range(M):
        n = (m + 1) % M
        f = bm.faces.new((BV[0][m], BV[0][n], TV[0][n], TV[0][m])); f.material_index = 2
        f = bm.faces.new((TV[rings][m], TV[rings][n], BV[rings][n], BV[rings][m])); f.material_index = 2
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    rng = random.Random(len(outer) * 7 + int(y0 * 10))
    u, us = PAL.u(col), PAL.u(soffit)
    def sh(f):
        n = f.normal; mi = f.material_index
        if mi == 1: return [(us, clamp(.42 + rng.uniform(-.03, .03), .04, .96))] * len(f.loops)
        if mi == 2: return [(u, .26)] * len(f.loops)
        v = (.56 if mi == 0 else .45) + .14 * n.y + rng.uniform(-.02, .02)
        return [(u, clamp(v, .04, .96))] * len(f.loops)
    P.add(bm, sh)
    if hips:
        start = 0
        for i in range(nC):
            pts = [Vector(pt(i, 0, k / rings, True)) + Vector((0, .16, 0)) for k in range(rings + 1)]
            k_ = hip_r / .24
            pts = [p + Vector((0, (hip_r - .24) * .6, 0)) for p in pts]
            P.add(tube(pts, [hip_r * 1.2] + [hip_r] * rings, sides=5), S(col, base=.36, up=.1, jit=.02))
            tip = pts[0]; d = (pts[0] - pts[1]).normalized()                       # curled ridge-end tile
            P.add(T(lathe([(0, 0), (.42 * k_, .15 * k_), (.36 * k_, .45 * k_), (0, .55 * k_)], n=8), tuple(tip + d * .1 * k_)), S(col, base=.3, jit=.02))
            start += ns[i]

def hip_roof(P, hw, hd, y0, rise, col, oh=2.4, curl=1.0, ridge_frac=None, tile=.9, ridge=True):
    """rectangular hip roof over a hw x hd (half sizes) wall box: ridge along X, ridge beam + end ornaments"""
    rx = max(.6, hw - hd) if ridge_frac is None else hw * ridge_frac
    outer = [(-hw - oh, -hd - oh), (hw + oh, -hd - oh), (hw + oh, hd + oh), (-hw - oh, hd + oh)]
    inner = [(-rx, -.25), (rx, -.25), (rx, .25), (-rx, .25)]
    flared_roof(P, outer, inner, y0, y0 + rise, col, curl=curl, tile=tile)
    if ridge:
        top = y0 + rise
        P.add(T(box((2 * rx + 1.0, .7, .9), .12), (0, top + .2, 0)), S(col, base=.3, up=.1, jit=.02))
        P.add(T(box((2 * rx + .6, .3, .5), .08), (0, top + .65, 0)), S(col, base=.42, up=.1, jit=.02))
        for sx in (-1, 1):                                                      # ridge-end ornaments (onigawara)
            P.add(T(lathe([(0, 0), (.5, .1), (.62, .5), (.4, .95), (.12, 1.25), (0, 1.3)], n=8), (sx * (rx + .5), top + .1, 0), 0, 0, -sx * 18),
                  S(col, base=.33, up=.1, jit=.02))

def skirt_roof(P, hw, hd, y0, y1, col, oh=2.0, curl=.8, inset=.25, tile=1.5, rings=5):
    """pent roof around a storey (pagoda tiers, inn skirts): from the eave down to the wall line"""
    outer = [(-hw - oh, -hd - oh), (hw + oh, -hd - oh), (hw + oh, hd + oh), (-hw - oh, hd + oh)]
    inner = [(-hw + inset, -hd + inset), (hw - inset, -hd + inset), (hw - inset, hd - inset), (-hw + inset, hd - inset)]
    flared_roof(P, outer, inner, y0, y1, col, curl=curl, rings=rings, conc=1.5, tile=tile)

# ------------------------------------------------------------------ walls with real openings
def holed_wall(P, L, H, th, holes, pos, yaw, col='cream', base=.8, seed=0):
    """wall panel L long (x -L/2..L/2), H high, th thick, holes [(x0, x1, y0, y1)] cut as real gaps (cells around them)"""
    xs = sorted({-L / 2, L / 2} | {h[0] for h in holes} | {h[1] for h in holes})
    ys = sorted({0.0, H} | {h[2] for h in holes} | {h[3] for h in holes})
    rng = random.Random(seed)
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            xm, ym = (xa + xb) / 2, (ya + yb) / 2
            if any(h[0] < xm < h[1] and h[2] < ym < h[3] for h in holes): continue
            P.add(T(T(box((xb - xa, yb - ya, th)), (xm, ym, 0)), pos, yaw),
                  S(col, base=base + rng.uniform(-.015, .015), up=.06, jit=.01))

def window(P, x, y0, w, h, th, pos, yaw, bars=(3, 4)):
    """cut window: timber frame round the hole, sill, recessed shoji lattice with a warm paper glow behind it"""
    L = lambda bm: T(bm, pos, yaw)
    fr = S('wood', base=.42, up=.08, jit=.02)
    for xx in (x - w / 2 - .12, x + w / 2 + .12):
        P.add(L(T(box((.3, h + .5, th + .16)), (xx, y0 + h / 2, 0))), fr)
    P.add(L(T(box((w + .7, .3, th + .16)), (x, y0 + h + .12, 0))), fr)
    P.add(L(T(box((w + .9, .26, th + .42), .05), (x, y0 - .13, -.12))), S('wood', base=.5, up=.1, jit=.02))
    z = .05                                                                     # lattice sits in the wall middle
    nx, ny = bars
    for i in range(1, nx):
        P.add(L(T(box((.09, h, .1)), (x - w / 2 + w * i / nx, y0 + h / 2, z))), S('wood', base=.32, jit=.01))
    for j in range(1, ny):
        P.add(L(T(box((w, .09, .1)), (x, y0 + h * j / ny, z))), S('wood', base=.32, jit=.01))
    P.gadd(L(T(box((w, h, .06)), (x, y0 + h / 2, z + .12))), 'shoji')

def doorway(P, x, w, h, th, pos, yaw, open_frac=.5):
    """cut doorway: heavy posts + lintel, a sliding lattice door half open, warm lit interior paper behind"""
    L = lambda bm: T(bm, pos, yaw)
    fr = S('wood', base=.38, up=.08, jit=.02)
    for xx in (x - w / 2 - .18, x + w / 2 + .18):
        P.add(L(T(box((.42, h + .4, th + .3), .05), (xx, h / 2 + .2, 0))), fr)
    P.add(L(T(box((w + 1.1, .45, th + .3), .05), (x, h + .25, 0))), fr)
    P.add(L(T(box((w + .5, .16, th + .2)), (x, .08, 0))), S('stone', base=.5, up=.1, jit=.02))   # stone threshold
    dw = w * (1 - open_frac); dx = x - w / 2 + dw / 2
    P.add(L(T(box((dw, h, .14), .02), (dx, h / 2, .05))), S('woodlt', base=.4, up=.05, jit=.01))
    for j in range(1, 6):
        P.add(L(T(box((dw - .2, .07, .06)), (dx, h * .45 + (h * .5) * j / 6, -.04))), S('wood', base=.3, jit=.01))
    P.gadd(L(T(box((w, h, .06)), (x, h / 2, th / 2 + 1.6))), 'shoji')         # lit inner partition 1.6 deep
    P.add(L(T(box((w + .2, .1, 1.8)), (x, .05, th / 2 + .8))), S('woodlt', base=.5, up=.1, jit=.01))  # floor boards

def giboshi(P, pos, r=.32):
    """bronze onion cap (the signature post finial)"""
    k = r / .3
    P.add(T(lathe([(r * 1.05, 0), (r * .85, .16 * k), (r * 1.3, .36 * k), (r * 1.4, .52 * k), (r * 1.15, .7 * k),
                   (r * .55, .86 * k), (r * .22, .98 * k), (0, 1.2 * k)], n=8), pos),
          S('iron', base=.7, up=.15, jit=.02))
    P.add(T(torus(r * 1.08, .05 * k, 8, 3), (pos[0], pos[1] + .12 * k, pos[2])), S('iron', base=.5, jit=.01))

def balcony(P, x0, x1, z, y, depth=1.5, side=-1):
    """deck on brackets along a wall at z (side = -1 front), cedar rail with giboshi posts"""
    zc = z + side * depth / 2
    n = max(2, int((x1 - x0) / .7))
    for i in range(n):
        xx = lerp(x0, x1, (i + .5) / n)
        P.add(T(box(((x1 - x0) / n - .08, .2, depth)), (xx, y, zc)), S('woodlt', base=.42 + .04 * (i % 2), up=.08, jit=.01))
    P.add(T(box((x1 - x0 + .2, .35, .35)), (lerp(x0, x1, .5), y - .25, z + side * depth)), S('wood', base=.4, jit=.01))
    posts = max(2, int((x1 - x0) / 3.2) + 1)
    for i in range(posts):
        xx = lerp(x0 + .2, x1 - .2, i / (posts - 1)); zz = z + side * (depth - .2)
        P.add(T(box((.32, 2.2, .32), .04), (xx, y + 1.1, zz)), S('wood', base=.42, up=.08, jit=.01))
        giboshi(P, (xx, y + 2.2, zz), .22)
        P.add(bar((xx, y - .2, z), (xx, y - 1.6, z + side * .02), .25, .25), S('wood', base=.36, jit=.01))      # bracket post
        P.add(bar((xx, y - 1.4, z), (xx, y - .2, z + side * (depth - .2)), .22, .22), S('wood', base=.38, jit=.01))
    zz = z + side * (depth - .2)
    P.add(T(box((x1 - x0, .22, .28), .05), (lerp(x0, x1, .5), y + 1.85, zz)), S('wood', base=.46, up=.1, jit=.01))
    P.add(T(box((x1 - x0, .16, .2)), (lerp(x0, x1, .5), y + .7, zz)), S('wood', base=.4, jit=.01))
    nb = int((x1 - x0) / .55)
    for i in range(nb):
        xx = lerp(x0 + .3, x1 - .3, i / max(1, nb - 1))
        P.add(T(box((.1, 1.1, .1)), (xx, y + 1.25, zz)), S('wood', base=.36, jit=.01))

def plinth(P, w, d, h=1.0, out=.6, seed=0):
    """SHARED BASE: sand-ashlar plinth (block faces) with a chamfered cap course, sunk 0.5 below the origin"""
    for (L, z, yaw) in ((w + out * 2, -(d / 2 + out), 0), (w + out * 2, d / 2 + out, 180), (d + out * 2, w / 2 + out, -90), (d + out * 2, -(w / 2 + out), 90)):
        if yaw in (0, 180): pos = (0, -.5, z)
        else: pos = (z, -.5, 0)
        P.add(T(ashlar(L, h + .5 - .25, 1.8, .75, seed=seed + int(L), depth=.06, ins=.06), pos, yaw), ash_sh('stone', base=.6, var=.06, grime=.12))
    P.add(T(box((w + out * 2 - .2, h + .5, d + out * 2 - .2)), (0, (h - .5) / 2, 0)), S('stone', base=.5, jit=.01))
    P.add(T(box((w + out * 2 + .3, .32, d + out * 2 + .3), .12), (0, h - .1, 0)), S('stone', base=.68, up=.12, jit=.02))

def frame_storey(P, w, d, y, h, posts_x=(), posts_z=(), beam=True):
    """dark cedar framing: corner posts, extra posts, a head beam (nageshi) and sill all round"""
    fr = S('wood', base=.38, up=.08, jit=.02)
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(box((.62, h + .1, .62), .05), (sx * w / 2, y + h / 2, sz * d / 2)), fr)
    for xx in posts_x:
        for sz in (-1, 1): P.add(T(box((.45, h, .4), .04), (xx, y + h / 2, sz * (d / 2 + .05))), fr)
    for zz in posts_z:
        for sx in (-1, 1): P.add(T(box((.4, h, .45), .04), (sx * (w / 2 + .05), y + h / 2, zz)), fr)
    if beam:
        for yy, hh in ((y + h - .35, .5), (y + .18, .36)):
            P.add(T(box((w + .5, hh, .5)), (0, yy, -d / 2 - .02)), fr); P.add(T(box((w + .5, hh, .5)), (0, yy, d / 2 + .02)), fr)   # unbevelled: prop budget
            P.add(T(box((.5, hh, d + .5)), (-w / 2 - .02, yy, 0)), fr); P.add(T(box((.5, hh, d + .5)), (w / 2 + .02, yy, 0)), fr)

def storey_walls(P, w, d, y, h, front=('door',), win_w=2.4, seed=0, th=.5, sides=True, back=True):
    """four plaster walls of one storey with cut openings; returns the x positions of window centres on the front"""
    def opens(L, kinds):
        n = len(kinds); out = []
        for i, k in enumerate(kinds):
            x = -L / 2 + L * (i + .5) / n
            if k == 'door': out.append(('door', x, 3.2, 0.0, min(h - .9, 4.6)))
            elif k == 'win': out.append(('win', x, win_w, 1.5, min(h - 1.2, 3.8)))
        return out
    nside = max(1, int(d / 6))
    walls = [((0, y, -d / 2), 0, w, front), ((0, y, d / 2), 180, w, ('win',) * max(1, int(w / 5)) if back else ()),
             ((-w / 2, y, 0), 90, d, ('win',) * nside if sides else ()), ((w / 2, y, 0), -90, d, ('win',) * nside if sides else ())]
    for pos, yaw, L, kinds in walls:
        ops = opens(L - 1.2, kinds)
        holes = [(x - ww / 2, x + ww / 2, y0, y1) for k, x, ww, y0, y1 in ops]
        holed_wall(P, L - .2, h, th, holes, pos, yaw, seed=seed)
        for k, x, ww, y0, y1 in ops:
            if k == 'win': window(P, x, y0, ww, y1 - y0, th, pos, yaw)
            else: doorway(P, x, ww, y1, th, pos, yaw)
    frame_storey(P, w, d, y, h)

def paper_lantern(P, pos, r=.55, h=1.0, key='lamp'):
    """chouchin: glowing ribbed paper body with dark wood top + bottom rings and a hanging cord"""
    x, y, z = pos
    body = lathe([(r * .55, 0), (r * .9, h * .15), (r, h * .5), (r * .9, h * .85), (r * .55, h)], n=10)
    P.gadd(T(body, (x, y - h, z)), key)
    for k in range(1, 5):
        yy = y - h + h * k / 5; rr = r * (1.0 if 1 < k < 4 else .93)
        P.add(T(torus(rr + .02, .03, 8, 3), (x, yy, z)), S('wood', base=.35, jit=.01))
    for yy, rr in ((y, r * .6), (y - h, r * .6)):
        P.add(T(cyl(rr, .18, 10, .03, y0=-.09), (x, yy, z)), S('wood', base=.3, up=.1, jit=.01))
    P.add(T(cyl(.04, .6, 4, y0=0), (x, y + .05, z)), S('iron', base=.3, jit=.01))

# ------------------------------------------------------------------ buildings
def house(name='Inn', w=14.0, d=10.0, storeys=2, sh=6.5, roof='roofB', kind='inn', seed=0, rise=None, balc=True):
    """village house / inn: ashlar plinth, plaster storeys with cut windows + door, cedar framing, skirt roofs between
    storeys, a front balcony on the upper storey, hip roof with ridge ornaments, paper lanterns at the door"""
    P = Prop(name); pl = 1.0
    plinth(P, w, d, pl, seed=seed)
    y = pl
    for s in range(storeys):
        if s == 0 and kind == 'shop':
            shopfront(P, w, d, y, sh)
        else:
            nw = max(1, int(w / 4.6))
            if s == 0: front = tuple(['win'] * (nw // 2) + ['door'] + ['win'] * (nw - nw // 2))
            else: front = ('win',) * nw
            storey_walls(P, w, d, y, sh, front=front, seed=seed + s, back=kind != 'inn')   # inn backs face the tree line: plain
        if s < storeys - 1:
            skirt_roof(P, w / 2, d / 2, y + sh - 1.3, y + sh + .5, roof, oh=1.9, curl=.7, tile=2.8, rings=4)   # prop budget 12k
            if balc and s == storeys - 2:
                balcony(P, -w / 2 + .6, w / 2 - .6, -d / 2 - .1, y + sh + 1.1, depth=1.6)
        y += sh
    hip_roof(P, w / 2, d / 2, y - .1, rise if rise else d * .55, roof, oh=2.5, curl=1.1, tile=1.9)
    if kind != 'shop':
        for sx in (-1, 1): paper_lantern(P, (sx * 2.6, pl + 4.9, -d / 2 - .9), .45, .85)
        for sx in (-1, 1): P.add(bar((sx * 2.6, pl + 5.6, -d / 2 - .1), (sx * 2.6, pl + 5.6, -d / 2 - .95), .12, .12), S('wood', base=.35, jit=.01))
    return P

def shopfront(P, w, d, y, h):
    """open market front: back + side walls, a wide opening with a counter, shelves of goods, a slatted awning"""
    th = .5
    holed_wall(P, w - .2, h, th, [], (0, y, d / 2), 180)
    for sx in (-1, 1): holed_wall(P, d - .2, h, th, [(-1.4, 1.4, 1.5, 4.0)], (sx * w / 2, y, 0), -sx * 90)
    for sx in (-1, 1): window(P, 0, 1.5, 2.8, 2.5, th, (sx * w / 2, y, 0), -sx * 90)
    for sx in (-1, 1): holed_wall(P, 1.6, h, th, [], (sx * (w / 2 - .8), y, -d / 2), 0)
    P.add(T(box((w - 3.2, 1.2, th)), (0, y + h - .6, -d / 2)), S('cream', base=.78, up=.05, jit=.01))
    frame_storey(P, w, d, y, h, posts_x=(-w / 2 + 1.7, w / 2 - 1.7))
    P.add(T(box((w - .6, .25, d - .6)), (0, y + .12, 0)), S('woodlt', base=.45, up=.08, jit=.01))           # floor
    P.add(T(box((w - 4.0, 1.6, 1.2), .08), (0, y + .8, -d / 2 + 1.2)), S('wood', base=.45, up=.1, jit=.02))  # counter
    P.add(T(box((w - 3.6, .18, 1.5), .05), (0, y + 1.65, -d / 2 + 1.2)), S('woodlt', base=.55, up=.12, jit=.01))
    rng = random.Random(int(w * 10))
    for i in range(int((w - 5) / 1.3)):                                          # goods on the counter: jars, bundles
        x = -w / 2 + 2.8 + i * 1.3
        if i % 2: P.add(T(lathe([(.3, 0), (.42, .3), (.36, .7), (.18, .8), (.2, .95), (0, .95)], n=8), (x, y + 1.74, -d / 2 + 1.2)), S(rng.choice(('cream', 'stone', 'iron')), base=.6, up=.15, jit=.02))
        else: P.add(T(box((.8, .5, .6), .1), (x, y + 2.0, -d / 2 + 1.2), rng.uniform(-15, 15)), S('woodlt', base=.62, up=.1, jit=.02))
    for k, yy in enumerate((1.6, 3.0, 4.4)):                                   # back shelves with goods
        P.add(T(box((w - 2, .16, .9)), (0, y + yy, d / 2 - .9)), S('wood', base=.42, up=.1, jit=.01))
        for i in range(int((w - 3) / 1.4)):
            x = -w / 2 + 1.8 + i * 1.4
            P.add(T(lathe([(.25, 0), (.34, .25), (.3, .55), (.12, .65), (0, .66)], n=7), (x, y + yy + .08, d / 2 - .9)), S(rng.choice(('cream', 'stone', 'woodlt', 'iron')), base=.55 + rng.uniform(-.1, .1), up=.15, jit=.02))
    P.gadd(T(box((w - 1.6, h - 1.2, .06)), (0, y + h / 2 + .3, d / 2 - .35)), 'shoji')      # warm back wall
    ay = y + h - 1.8                                                             # slatted awning on brackets (under the skirt roof)
    for i in range(int((w - 1) / .55)):
        x = -w / 2 + .8 + i * .55
        P.add(bar((x, ay, -d / 2 - .1), (x, ay - 1.0, -d / 2 - 2.6), .5, .12), S('woodlt', base=.5 + (i % 2) * .05, up=.1, jit=.01))
    for sx in (-1, 0, 1):
        P.add(bar((sx * (w / 2 - .8), ay - 1.6, -d / 2), (sx * (w / 2 - .8), ay - .85, -d / 2 - 2.4), .25, .25), S('wood', base=.38, jit=.01))
    P.add(bar((-w / 2 + .3, ay - 1.05, -d / 2 - 2.5), (w / 2 - .3, ay - 1.05, -d / 2 - 2.5), .3, .3), S('wood', base=.4, jit=.01))
    for sx in (-1, 1): paper_lantern(P, (sx * (w / 2 - 2.2), ay - 1.25, -d / 2 - 2.0), .45, .8)

def pagoda(part='base'):
    """HERO: five-tier bathhouse pagoda. Stepped ashlar platform + veranda, five storeys (plaster, cedar posts, cut
    lattice windows on every face, door at the front), teal-copper skirt roofs with upturned corners, balcony rails on
    the upper tiers, final pyramid roof and a bronze spire of nine rings with a jewel"""
    P = Prop('Pagoda' + part.capitalize())
    if part == 'base': plinth(P, 18.0, 18.0, 1.0, out=.6, seed=3)
    if part == 'base': plinth(P, 15.0, 15.0, 2.2, out=.2, seed=9)                 # second stepped course
    for i in range(5 if part == 'base' else 0):                                                          # front steps up the platform
        P.add(T(box((6.0, .45, 1.0 - i * .1), .06), (0, .2 + i * .44, -10.2 + i * .55)), S('stone', base=.64 + (i % 2) * .04, up=.12, jit=.02))
    sizes = [12.0, 10.6, 9.2, 7.8, 6.4]; hs = [7.0, 5.6, 5.0, 4.6, 4.2]
    y = 2.2
    if part == 'base': P.add(T(box((14.2, .3, 14.2)), (0, y + .05, 0)), S('woodlt', base=.42, up=.1, jit=.01))      # veranda floor
    for sx in ((-1, 1) if part == 'base' else ()):
        for k in range(5):
            P.add(T(box((.35, 1.6, .35), .04), (sx * 6.9, y + .8, -6.9 + k * 3.45)), S('wood', base=.4, jit=.01))
            if not (sx < 0 and k == 2): P.add(T(box((.35, 1.6, .35), .04), (-6.9 + k * 3.45, y + .8, sx * 6.9)), S('wood', base=.4, jit=.01))
            if k in (0, 4): giboshi(P, (sx * 6.9, y + 1.6, -6.9 + k * 3.45), .24)
        P.add(T(box((.25, .22, 14.0)), (sx * 6.9, y + 1.35, 0)), S('wood', base=.46, up=.1, jit=.01))
        for x0, x1 in (((-7.0, -3.2), (3.2, 7.0)) if sx < 0 else ((-7.0, 7.0),)):
            P.add(T(box((x1 - x0, .22, .25)), ((x0 + x1) / 2, y + 1.35, sx * 6.9)), S('wood', base=.46, up=.1, jit=.01))
            P.add(T(box((x1 - x0, .16, .2)), ((x0 + x1) / 2, y + .55, sx * 6.9)), S('wood', base=.4, jit=.01))
    for i, (s, h) in enumerate(zip(sizes, hs)):
        hw = s / 2
        if (i < 2) != (part == 'base'): y += h; continue
        if i == 0: front = ('win', 'door', 'win')
        else: front = ('win',) * (2 if s > 8 else 1)
        storey_walls(P, s, s, y, h, front=front, win_w=2.0 if s > 8 else 1.8, seed=20 + i)
        top = y + h
        if i < 4:
            nxt = sizes[i + 1] / 2
            skirt_roof(P, hw, hw, top - 1.1, top + 1.35, 'roofA', oh=2.6 - i * .15, curl=1.3, inset=hw - nxt + .3)
            if i >= 1:                                                          # bracket clusters under each eave
                for sx in (-1, 1):
                    for sz in (-1, 1):
                        P.add(bar((sx * hw, top - .8, sz * hw), (sx * (hw + 1.4), top - .9, sz * (hw + 1.4)), .45, .45), S('wood', base=.35, jit=.01))
            if i >= 1:                                                          # balcony rail round the next tier
                rr = nxt + 1.0
                for sx in (-1, 1):
                    P.add(T(box((.18, .2, 2 * rr)), (sx * rr, top + 1.9, 0)), S('wood', base=.45, up=.1, jit=.01))
                    P.add(T(box((2 * rr, .2, .18)), (0, top + 1.9, sx * rr)), S('wood', base=.45, up=.1, jit=.01))
                    for k in range(4):
                        t = -rr + 2 * rr * k / 3
                        P.add(T(box((.2, 1.2, .2)), (sx * rr, top + 1.35, t)), S('wood', base=.38, jit=.01))
                        P.add(T(box((.2, 1.2, .2)), (t, top + 1.35, sx * rr)), S('wood', base=.38, jit=.01))
                P.add(T(box((2 * rr, .2, 2 * rr)), (0, top + .78, 0)), S('woodlt', base=.42, up=.1, jit=.01))
        y = top
    if part == 'base':
        for sx in (-1, 1): paper_lantern(P, (sx * 3.4, 2.2 + 6.3, -6.9), .55, 1.0)
        return P
    hw = sizes[-1] / 2
    flared_roof(P, [(-hw - 2.4, -hw - 2.4), (hw + 2.4, -hw - 2.4), (hw + 2.4, hw + 2.4), (-hw - 2.4, hw + 2.4)],
                [(-.45, -.45), (.45, -.45), (.45, .45), (-.45, .45)], y - 1.0, y + 4.2, 'roofA', curl=1.4)
    y += 4.2                                                                    # sorin spire
    P.add(T(lathe([(1.1, 0), (1.1, .5), (.8, .6), (.8, 1.0), (.5, 1.2), (.35, 1.5)], n=12), (0, y - .3, 0)), S('iron', base=.5, up=.15, jit=.02))
    P.add(T(cyl(.16, 8.0, 8, y0=0), (0, y + 1.0, 0)), S('iron', base=.45, up=.1, jit=.02))
    for k in range(9):
        P.add(T(torus(.62 - k * .03, .1, 14, 5), (0, y + 1.6 + k * .62, 0)), S('iron', base=.62, up=.15, jit=.02))
    P.add(T(lathe([(0, 0), (.45, .2), (.6, .6), (.4, 1.0), (.15, 1.3), (0, 1.6)], n=10), (0, y + 8.8, 0)), S('iron', base=.72, up=.15, jit=.02))
    return P

def bath_pavilion(w=16.0, d=12.0, h=6.6, roof='roofA'):
    """open bath shelter over a pool: round cedar columns on stone bases, tie beams, bracket arms, hip roof"""
    P = Prop('BathPavilion')
    xs = [-w / 2, 0.0, w / 2]
    for x in xs:
        for sz in (-1, 1):
            z = sz * d / 2
            P.add(T(lathe([(.75, -.4), (.75, .25), (.55, .45), (.5, .7), (0, .7)], n=8), (x, 0, z)), S('stone', base=.6, up=.15, jit=.02))
            P.add(T(cyl(.33, h, 10, y0=.6), (x, 0, z)), S('wood', base=.42, up=.05, jit=.01))
            P.add(bar((x, h - 1.4, z), (x + (.0 if x == 0 else -math.copysign(1.4, x)), h - .3, z), .3, .3), S('wood', base=.36, jit=.01))
    for sz in (-1, 1):
        P.add(T(box((w + .8, .55, .5), .05), (0, h + .1, sz * d / 2)), S('wood', base=.38, up=.08, jit=.01))
        P.add(T(box((w + .4, .3, .35), .04), (0, h - 1.3, sz * d / 2)), S('wood', base=.33, jit=.01))
    for x in xs:
        P.add(T(box((.5, .55, d + .8), .05), (x, h + .1, 0)), S('wood', base=.38, up=.08, jit=.01))
    for k in range(9):                                                          # exposed rafters under the roof
        x = -w / 2 + w * k / 8
        P.add(T(box((.22, .22, d + 1.0)), (x, h + .5, 0)), S('wood', base=.44, jit=.01))
    hip_roof(P, w / 2, d / 2, h + .4, 5.0, roof, oh=2.2, curl=1.2)
    for x in (-w / 2 + 2.5, w / 2 - 2.5): paper_lantern(P, (x, h - .2, -d / 2), .5, .9)
    return P

# ------------------------------------------------------------------ hot pools + water features
def pool_outline(rx, rz, seed, n=28):
    rng = random.Random(seed); out = []
    for i in range(n):
        a = i * math.tau / n
        k = 1 + (nz(math.cos(a) * 3, seed, math.sin(a) * 3, 1.3, 2) - .5) * .35
        out.append((math.cos(a) * rx * k, math.sin(a) * rz * k))
    return out

def hot_pool(rx=7.0, rz=5.0, seed=1, spout=True):
    """steaming rock pool: raised ashlar-and-boulder rim, cut-stone curb, milky water, sunken bench step, boulders
    round the edge, a bamboo spout pouring in from a stone basin"""
    P = Prop('HotPool%d' % seed); rng = random.Random(seed)
    out = pool_outline(rx, rz, seed)
    ins = [(x * .86, z * .86) for x, z in out]
    n = len(out)
    bm = bmesh.new()                                                            # curb ring (solid band, real thickness)
    O0 = [bm.verts.new((x, -.5, z)) for x, z in out]; O1 = [bm.verts.new((x, .95, z)) for x, z in out]
    I1 = [bm.verts.new((x, .95, z)) for x, z in ins]; I0 = [bm.verts.new((x, -.2, z)) for x, z in ins]
    for i in range(n):
        j = (i + 1) % n
        for a, b in ((O0, O1), (O1, I1), (I1, I0)): bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        c = f.calc_center_median(); f.material_index = int(h01(round(math.atan2(c.z, c.x), 1), 0, 0) * 3)
    u = PAL.u('stone')
    P.add(bm, lambda f: [(u, clamp(.52 + f.material_index * .05 + .12 * f.normal.y, .04, .96))] * len(f.loops))
    for i in range(n):                                                          # cut capstones on the curb
        x, z = (out[i][0] + ins[i][0]) / 2, (out[i][1] + ins[i][1]) / 2
        yaw = -math.degrees(math.atan2(z, x)) + 90
        P.add(T(box((math.tau * math.hypot(*out[i]) / n * .93, .3, (1 - .86) * math.hypot(out[i][0], out[i][1]) + .5), .1), (x, 1.05, z), yaw), S('stone', base=.66 + rng.uniform(-.05, .05), up=.12, jit=.02))
    wb = bmesh.new()                                                            # water surface
    wv = [wb.verts.new((x * .99, .62, z * .99)) for x, z in ins]; wb.faces.new(wv)
    bmesh.ops.triangulate(wb, faces=list(wb.faces))
    P.add(wb, lambda f: [(PAL.u('water'), .62)] * len(f.loops))
    P.add(T(box((rx * 1.1, .4, 1.2), .1), (0, .25, rz * .62)), S('stone', base=.42, up=.1, jit=.02))   # sunken bench
    for k in range(9):                                                          # boulders on the rim (back half)
        a = math.pi * (1.05 + .9 * k / 8) + rng.uniform(-.1, .1); i = int(a / math.tau * n) % n
        x, z = out[i]
        P.add(T(blob(rng.uniform(.6, 1.1), seed * 17 + k, n=16, sq=.7), (x * 1.02, .9, z * 1.02)), S('rock', base=.5, up=.2, jit=.05))
    if spout:                                                                   # bamboo spout (kakei) + stone basin
        bx, bz = out[n * 3 // 4][0] * 1.05, out[n * 3 // 4][1] * 1.05
        P.add(T(lathe([(1.1, -.3), (1.2, .2), (1.15, 1.3), (.95, 1.35), (.9, 1.0), (0, 1.0)], n=12), (bx, .9, bz)), S('stone', base=.55, up=.12, jit=.02))
        tip = Vector((bx * .78, 3.1, bz * .78)); root = Vector((bx * 1.12, 3.6, bz * 1.12))
        P.add(tube([root, tip], .2, sides=8), S('grass', base=.62, up=.1, jit=.02))
        for t in (.2, .7):
            c = root.lerp(tip, t)
            P.add(T(torus(.23, .06, 10, 4), tuple(c)), S('grass', base=.4, jit=.02))
            for s in (-1, 1):
                P.add(bar((c.x + s * .5, .6, c.z), (c.x, c.y - .1, c.z), .15, .15), S('woodlt', base=.42, jit=.02))
        P.add(tube([tip, tip + Vector((0, -.6, 0)) + (tip - root).normalized() * .3, Vector((tip.x * .96, .65, tip.z * .96))], [.09, .11, .16], sides=6), S('water', base=.8, up=.1, jit=0))
    return P

def koi_pond(seed=1, r=3.6):
    """small round stone pond: dressed rim, water, three koi, lily pads, a moss boulder"""
    P = Prop('KoiPond%d' % seed); rng = random.Random(seed)
    P.add(lathe([(r + .5, -.4), (r + .55, .35), (r + .35, .62), (r - .1, .62), (r - .25, .3), (r - .25, -.1), (0, -.1)], n=22), S('stone', base=.6, up=.15, jit=.02))
    for k in range(11):
        a = k * math.tau / 11
        P.add(T(box((1.9, .26, .9), .09), (math.cos(a) * (r + .15), .72, math.sin(a) * (r + .15)), -math.degrees(a) + 90), S('stone', base=.68 + rng.uniform(-.05, .05), up=.12, jit=.02))
    P.add(T(cyl(r - .3, .05, 22, y0=.32), (0, 0, 0)), S('water', base=.42, jit=0))
    for k, col in enumerate(('maple', 'cream', 'maple')):                       # koi: body, tail fins
        a = rng.uniform(0, math.tau); d = rng.uniform(.6, r * .6); x, z = math.cos(a) * d, math.sin(a) * d; yaw = rng.uniform(0, 360)
        fish = tube([Vector((-.55, 0, 0)), Vector((-.1, 0, 0)), Vector((.4, 0, 0))], [.05, .2, .1], sides=6, flat=(1, .6))
        P.add(T(fish, (x, .38, z), yaw), S(col, base=.6, up=.1, jit=.02))
        P.add(T(T(box((.36, .04, .32)), (.62, 0, 0), 0, 0, 0), (x, .38, z), yaw), S(col, base=.7, jit=.02))
    for k in range(4):
        a = rng.uniform(0, math.tau); d = rng.uniform(1, r * .8)
        P.add(T(cyl(rng.uniform(.4, .6), .06, 9, y0=.36), (math.cos(a) * d, 0, math.sin(a) * d)), S('grass', base=.55, up=.1, jit=.03))
    P.add(T(blob(1.0, seed + 3, n=16, sq=.75), (r * .45, .5, -r * .3)), S('rock', base=.5, up=.2, jit=.04, top='grass', thr=.55, topbase=.5))
    return P

# ------------------------------------------------------------------ edge modules (repeated along every terrace)
def rail_post(P, x):
    P.add(T(box((.7, .5, .7), .08), (x, 0, 0)), S('stone', base=.6, up=.12, jit=.02))
    P.add(T(box((.42, 2.9, .42), .05), (x, 1.45 - .2, 0)), S('wood', base=.4, up=.08, jit=.02))
    giboshi(P, (x, 2.75, 0), .27)

def railing_post():
    """the closing post at the end of a railing run (bays carry only their left post, so bays never overlap)"""
    P = Prop('RailPost'); rail_post(P, 0.0); return P

def railing(L=6.0, seed=1):
    """SIGNATURE: cedar railing bay with giboshi-capped posts, top + mid rails, slim balusters, stone post feet.
    One post at the left end (x = -L/2): bays laid end to end share posts; the run closes with railing_post()"""
    P = Prop('Railing%d' % int(L)); rng = random.Random(seed)
    rail_post(P, -L / 2)
    P.add(T(box((L - .44, .26, .34), .06), (0, 2.45, 0)), S('wood', base=.48, up=.12, jit=.02))
    P.add(T(box((L - .44, .2, .24), .04), (0, 1.0, 0)), S('wood', base=.42, up=.1, jit=.02))
    P.add(T(box((L - .44, .16, .2)), (0, .35, 0)), S('wood', base=.36, jit=.01))
    n = int((L - .8) / .5)
    for i in range(n):
        x = -L / 2 + .55 + (L - 1.1) * i / max(1, n - 1)
        P.add(T(box((.11, 2.05, .11)), (x, 1.37, 0)), S('wood', base=.38 + rng.uniform(-.02, .02), jit=.01))
    return P

def toro(seed=1, h=5.2):
    """stone lantern (kasuga-style): hex stepped base, bulged shaft, hex platform, firebox with cut openings and a
    glowing core, hex roof with upturned corners, jewel finial"""
    P = Prop('Toro%d' % seed); st = lambda b=.62: S('stone', base=b, up=.15, jit=.02)
    hexp = lambda r, y0, y1, bev=.06: cyl(r, y1 - y0, 6, bev, y0=y0)
    P.add(hexp(1.15, -.4, .25), st(.55)); P.add(hexp(.95, .25, .55), st(.6))
    P.add(lathe([(.42, .55), (.5, .75), (.38, 1.2), (.34, 2.1), (.42, 2.45), (.5, 2.6)], n=12), st(.64))
    for k in range(3): P.add(T(torus(.4, .05, 12, 4), (0, 1.3 + k * .3, 0)), st(.52))
    P.add(hexp(.95, 2.55, 2.85, .08), st(.6)); P.add(hexp(.75, 2.85, 2.95), st(.55))
    for k in range(6):                                                          # firebox: 6 posts + open frames
        a = k * math.tau / 6
        P.add(T(box((.2, 1.05, .2)), (math.cos(a) * .62, 3.48, math.sin(a) * .62), -math.degrees(a)), st(.6))
        am = a + math.pi / 6; cx, cz = math.cos(am) * .55, math.sin(am) * .55; yw = -math.degrees(am) + 90
        for yy in (3.03, 3.9): P.add(T(box((.6, .16, .12)), (cx, yy, cz), yw), st(.58))
        if k in (1, 4):
            P.add(T(box((.06, .75, .08)), (cx, 3.46, cz), yw), st(.5)); P.add(T(box((.55, .06, .08)), (cx, 3.46, cz), yw), st(.5))
    P.gadd(cyl(.4, .9, 6, y0=3.0), 'lamp')
    P.add(hexp(.72, 3.98, 4.08), st(.55))
    hexo = [(math.cos(k * math.tau / 6) * 1.35, math.sin(k * math.tau / 6) * 1.35) for k in range(6)]
    hexi = [(math.cos(k * math.tau / 6) * .18, math.sin(k * math.tau / 6) * .18) for k in range(6)]
    flared_roof(P, hexo, hexi, 4.1, 4.85, 'stone', curl=.35, thick=.22, tile=9, rings=4, conc=1.6, soffit='stone', corr=0, push=.08, hip_r=.08)
    P.add(T(lathe([(.25, 0), (.3, .12), (.22, .2), (.28, .45), (.12, .7), (0, .8)], n=10), (0, 4.8, 0)), st(.66))
    return P

def planter(L=4.0, seed=1):
    """stone trough planter (hollow, soil inside) with cloud-pruned sage shrubs and a few moss stones"""
    P = Prop('Planter%d' % seed); rng = random.Random(seed); d = 1.8; h = 1.2
    for x, z, sx, sz in ((0, -d / 2 + .15, L, .3), (0, d / 2 - .15, L, .3), (-L / 2 + .15, 0, .3, d), (L / 2 - .15, 0, .3, d)):
        P.add(T(box((sx, h + .4, sz), .06), (x, h / 2 - .2, z)), S('stone', base=.58, up=.12, jit=.02))
    for x in (-L / 2, L / 2):
        P.add(T(box((.5, .25, d + .3), .08), (x * .97, h + .05, 0)), S('stone', base=.68, up=.12, jit=.02))
    P.add(T(box((L + .25, .2, .45), .07), (0, h + .02, -d / 2 + .1)), S('stone', base=.7, up=.12, jit=.02))
    P.add(T(box((L - .5, .15, d - .5)), (0, h - .2, 0)), S('woodlt', base=.25, jit=.02))
    P.add(T(box((L + .2, .3, d + .2), .08), (0, .0, 0)), S('stone', base=.5, up=.1, jit=.02))         # foot band
    for sz in (-1, 1):                                                          # carved inset panel frames
        for x0, x1 in ((-L / 2 + .4, -.15), (.15, L / 2 - .4)):
            for (a, b, yy, hh) in ((x0, x1, .35, .1), (x0, x1, h - .35, .1)):
                P.add(T(box((b - a, hh, .1)), ((a + b) / 2, yy, sz * (d / 2 + .02))), S('stone', base=.68, up=.1, jit=.01))
            for xx in (x0, x1):
                P.add(T(box((.1, h - .7, .1)), (xx, h / 2, sz * (d / 2 + .02))), S('stone', base=.68, up=.1, jit=.01))
    n = max(2, int(L / 1.4))
    for k in range(n):
        x = -L / 2 + .8 + (L - 1.6) * k / max(1, n - 1)
        P.add(log((x, h - .2, 0), (x + rng.uniform(-.2, .2), h + .5, 0), .09, 5), S('wood', base=.4, jit=.02))
        for j in range(6):
            a = j * math.tau / 5 + rng.uniform(0, .6); d = 0 if j == 5 else rng.uniform(.3, .5)
            r = rng.uniform(.38, .5) * (1.15 if j == 5 else 1)
            c = (x + math.cos(a) * d, h + .45 + (j == 5) * .45 + rng.uniform(0, .15), math.sin(a) * d * .7)
            P.add(T(blob(r, seed * 9 + k * 7 + j, n=26, sq=.8), c), S('leaf', grad=(h, h + 1.4, .32, .82), up=.15, jit=.03))
    for k in range(4):                                                          # moss stones at the trough foot
        x = rng.uniform(-L / 2, L / 2)
        P.add(T(blob(.28, seed + k, n=12, sq=.7), (x, h - .1, rng.uniform(-.5, .5))), S('grass', base=.45, up=.2, jit=.03))
    return P

def stair_flight(rise=6.5, run=13.0, width=8.0, seed=1, cheek=True):
    """stone stair: bevelled sand treads with tone variation and a nosing shadow, ashlar cheek walls following the slope
    with chamfered capstones, newel blocks top + bottom. Built climbing toward -Z (front of the flight = +Z end)."""
    P = Prop('Stair%d_%d' % (int(rise * 10), int(width))); rng = random.Random(seed)
    n = max(2, round(rise / .5)); dr, dz = rise / n, run / n
    for i in range(n):
        z0 = run / 2 - i * dz
        P.add(T(box((width, dr * (i + 1) + .5, dz + .05), .05), (0, (dr * (i + 1) - .5) / 2, z0 - dz / 2)), S('stone', base=.6 + rng.uniform(-.05, .05), up=.14, jit=.01))
        P.add(T(box((width - .1, .12, .14)), (0, dr * (i + 1) - .04, z0 - .02)), S('stone', base=.72, jit=.01))
    if cheek:
        ang = math.degrees(math.atan2(rise, run)); Ls = math.hypot(rise, run)
        for sx in (-1, 1):
            x = sx * (width / 2 + .55)
            pts = [Vector((x + dx, y, z)) for dx in (-.55, .55) for (z, y) in ((run / 2, -.5), (run / 2, 1.2), (-run / 2, rise + 1.2), (-run / 2, -.5))]
            P.add(hull(pts), S('stone', base=.52, up=.05, jit=.01))
            for k in range(1, 5):                                               # mortar joints down the cheek
                z = run / 2 - run * k / 5; ytop = 1.2 + rise * k / 5
                P.add(T(box((1.16, ytop + .4, .08)), (x, (ytop - .5) / 2, z)), S('stone', base=.38, jit=.01))
            P.add(T(box((1.5, .38, Ls + .4), .12), (x, rise / 2 + 1.38, 0), 0, ang), S('stone', base=.7, up=.12, jit=.02))   # sloped coping
            for zz, yy in ((run / 2 - .5, .9), (-run / 2 + .5, rise + .9)):
                P.add(T(box((1.5, yy + 1.4 + .5, 1.5), .1), (x, (yy + 1.4 - .5) / 2, zz)), S('stone', base=.55, up=.1, jit=.02))
                P.add(T(box((1.8, .4, 1.8), .14), (x, yy + 1.4 + .2, zz)), S('stone', base=.7, up=.12, jit=.02))
    return P

def footbridge(L=20.0, y0=1.6, y1=4.5, arch=1.6, w=6.0):
    """arched cedar footbridge: plank deck on curved stringers, giboshi-capped rail posts, curved top rail, trestle
    legs in pairs with cross braces. Spans from z = +L/2 (y0) to z = -L/2 (y1); origin at mid-span water level."""
    P = Prop('FootBridge'); n = 22
    def yz(t): return lerp(y0, y1, t) + math.sin(t * math.pi) * arch, L / 2 - L * t
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n; (ya, za), (yb, zb) = yz(t0), yz(t1)
        a = math.degrees(math.atan2(yb - ya, za - zb))
        P.add(T(box((w, .3, (za - zb) * 1.0 - .06)), (0, (ya + yb) / 2 - .15, (za + zb) / 2), 0, a), S('woodlt', base=.42 + (i % 3) * .04, up=.12, jit=.01))
    for sx in (-1, 1):
        pts = [Vector((sx * (w / 2 - .2), yz(k / n)[0] - .55, yz(k / n)[1])) for k in range(n + 1)]
        P.add(tube(pts, .32, sides=6, flat=(1.3, 1)), S('wood', base=.38, jit=.01))
        rail = [Vector((sx * (w / 2 - .1), yz(k / n)[0] + 2.4, yz(k / n)[1])) for k in range(n + 1)]
        P.add(tube(rail, .17, sides=6), S('wood', base=.48, up=.1, jit=.01))
        mid = [p + Vector((0, -1.3, 0)) for p in rail]
        P.add(tube(mid, .1, sides=5), S('wood', base=.4, jit=.01))
        for k in range(0, n + 1, 3):
            y, z = yz(k / n)
            P.add(T(box((.36, 2.7, .36), .04), (sx * (w / 2 - .1), y + 1.05, z)), S('wood', base=.4, up=.08, jit=.01))
            giboshi(P, (sx * (w / 2 - .1), y + 2.55, z), .24)
    for t in (.3, .7):                                                          # trestle legs into the stream bed
        y, z = yz(t)
        for sx in (-1, 1):
            P.add(log((sx * (w / 2 - .5), -2.6, z), (sx * (w / 2 - .5), y - .4, z), .32, 8), S('wood', base=.34, jit=.02))
            P.add(T(cyl(.55, .5, 8, .05, y0=-.4), (sx * (w / 2 - .5), 0, z)), S('stone', base=.5, up=.1, jit=.02))
        P.add(bar((-(w / 2 - .5), y - .9, z), (w / 2 - .5, y - .9, z), .3, .3), S('wood', base=.36, jit=.01))
        P.add(bar((-(w / 2 - .5), -.2, z), (w / 2 - .5, y - 1.1, z), .2, .2), S('wood', base=.33, jit=.01))
    return P

# ------------------------------------------------------------------ story props (clusters of 2-4 at stairs + bridge)
def bucket(P, c, r=.55, h=.8, seed=0, tilt=0.0):
    x, y, z = c
    bm = lathe([(r * .85, 0), (r, h), (r * .9, h), (r * .76, .12), (0, .12)], n=12)
    P.add(T(bm, (x, y, z), 0, tilt), S('woodlt', base=.55, up=.1, jit=.02, seed=seed))
    for yy in (.2, h - .18):
        rr = lerp(r * .85, r, yy / h) + .03
        P.add(T(torus(rr, .045, 14, 4), (x, y + yy, z), 0, tilt), S('iron', base=.42, jit=.01))

def towel_rack(seed=1):
    """drying rack: two cedar uprights with feet, three poles, folded towels draped over (cream with indigo stripe),
    a pyramid of wooden buckets and a low stool beside it"""
    P = Prop('TowelRack%d' % seed); rng = random.Random(seed)
    for x in (-2.0, 2.0):
        P.add(T(box((.34, 3.6, .34), .04), (x, 1.6, 0)), S('wood', base=.42, up=.08, jit=.02))
        P.add(T(box((.4, .3, 1.6), .06), (x, .1, 0)), S('wood', base=.36, up=.08, jit=.02))
        giboshi(P, (x, 3.4, 0), .2)
    for yy in (1.6, 2.4, 3.15):
        P.add(log((-2.2, yy, 0), (2.2, yy, 0), .08, 6), S('woodlt', base=.55, jit=.01))
    for k, (x, yy) in enumerate(((-1.1, 3.15), (.6, 3.15), (-.3, 2.4), (1.2, 2.4), (-1.3, 1.6))):
        tw = .9 + rng.uniform(-.1, .1); dr = rng.uniform(.8, 1.2)
        for s in (-1, 1):                                                       # folded cloth hanging both sides
            pts = [Vector((x, yy + .06, s * .02)), Vector((x, yy - .3, s * .13)), Vector((x, yy - dr, s * .16))]
            P.add(T(box((tw, .05, .05)), (x, yy + .07, 0)), S('cream', base=.82, jit=.01))
            P.add(T(box((tw, dr, .06)), (x, yy - dr / 2, s * .12), 0, s * 4), S('cream', base=.8 + rng.uniform(-.04, .04), up=.05, jit=.01))
            P.add(T(box((tw + .01, .14, .07)), (x, yy - dr * .7, s * .12), 0, s * 4), S('roofB', base=.52, jit=.01))
    for (x, z, y) in ((2.9, -.4, 0), (3.9, -.4, 0), (3.4, .45, 0), (3.4, 0, .82)):
        bucket(P, (x, y, z), seed=int(x * 10))
    P.add(T(box((1.3, .16, .8), .05), (-3.1, .9, -.3)), S('woodlt', base=.5, up=.12, jit=.02))
    for sx in (-1, 1):
        P.add(T(box((.16, .9, .7), .03), (-3.1 + sx * .5, .45, -.3)), S('wood', base=.4, jit=.02))
    return P

def noodle_stall(seed=1):
    """yatai cart: two spoked wheels, cedar counter cabin with a plank top, small persimmon-tiled hip roof on four
    posts, a steaming iron pot, stacked bowls, condiment jars, a hanging paper lantern and three stools"""
    P = Prop('NoodleStall'); rng = random.Random(seed)
    w, d = 5.2, 2.6
    for sx in (-1, 1):                                                          # wheels
        P.add(T(torus(1.15, .13, 20, 5), (sx * (w / 2 + .3), 1.2, .3), 0, 0, 90), S('wood', base=.35, jit=.01))
        P.add(T(T(cyl(.25, .5, 8, y0=-.25), (0, 0, 0), 0, 0, 90), (sx * (w / 2 + .3), 1.2, .3)), S('iron', base=.4, jit=.01))
        for k in range(8):
            a = k * math.pi / 4
            P.add(bar((sx * (w / 2 + .3), 1.2, .3), (sx * (w / 2 + .3), 1.2 + math.sin(a) * 1.1, .3 + math.cos(a) * 1.1), .09, .09), S('wood', base=.4, jit=.01))
    P.add(T(box((w, 1.9, d), .08), (0, 2.0, .3)), S('wood', base=.42, up=.08, jit=.02))                     # cabin
    for i in range(7):
        P.add(T(box((.08, 1.7, .06)), (-w / 2 + .5 + i * (w - 1) / 6, 2.0, .3 - d / 2 - .04)), S('wood', base=.3, jit=.01))
    P.add(T(box((w + .6, .2, d + .9), .06), (0, 3.05, .1)), S('woodlt', base=.55, up=.12, jit=.01))      # counter top
    for x in (-w / 2 + .3, w / 2 - .3):
        for z in (.3 - d / 2 + .3, .3 + d / 2 - .3):
            P.add(T(box((.26, 3.6, .26), .03), (x, 4.95, z)), S('wood', base=.4, jit=.01))
    hip_roof(P, w / 2 - .1, d / 2, 6.7, 1.5, 'roofD', oh=.9, curl=.5, tile=.7)
    P.add(T(lathe([(.65, 0), (.75, .2), (.72, .85), (.6, .95), (0, .95)], n=12), (w / 2 - 1.1, 3.15, .4)), S('iron', base=.38, up=.12, jit=.02))
    P.add(T(lathe([(.3, 0), (.35, .1), (0, .12)], n=8), (w / 2 - 1.1, 4.1, .4)), S('woodlt', base=.5, jit=.01))
    for k in range(4):                                                          # stacked bowls
        P.add(T(lathe([(.18, 0), (.38, .25), (.34, .27), (.15, .05), (0, .05)], n=10), (-1.2, 3.15 + k * .2, .1)), S('cream', base=.82, up=.1, jit=.01))
    for k, col in enumerate(('roofB', 'cream', 'woodlt')):
        P.add(T(lathe([(.16, 0), (.2, .2), (.17, .45), (.08, .5), (.1, .6), (0, .6)], n=8), (-.2 + k * .4, 3.15, -.4)), S(col, base=.55, up=.12, jit=.02))
    for k in range(3): P.add(log((-2.3 + k * .12, 3.2, -.2), (-1.8 + k * .1, 3.25, .7), .04, 4), S('woodlt', base=.6, jit=.01))
    paper_lantern(P, (-w / 2 + .6, 6.4, -.8), .5, .9)
    for k in range(3):                                                          # stools
        x = -1.7 + k * 1.7; z = -1.9
        P.add(T(lathe([(.42, 0), (.46, .1), (.4, .15), (0, .15)], n=10), (x, 1.5, z)), S('woodlt', base=.55, up=.12, jit=.02))
        for a in range(3):
            aa = a * math.tau / 3 + k
            P.add(log((x + math.cos(aa) * .45, -.2, z + math.sin(aa) * .45), (x + math.cos(aa) * .25, 1.52, z + math.sin(aa) * .25), .06, 5), S('wood', base=.4, jit=.01))
    return P

def taru(P, c, r=.95, h=1.6, seed=0, yaw=0.0, lie=False):
    """sake cask: straw-wrapped body, rope bands, lid; lying casks rest on their side"""
    x, y, z = c
    def put(bm):
        if lie: T(bm, (0, -h / 2, 0), 0, 90)
        return T(bm, (x, y + (r if lie else 0), z), yaw)
    P.add(put(lathe([(r * .9, 0), (r, h * .25), (r * 1.02, h * .5), (r, h * .75), (r * .9, h), (r * .82, h), (0, h - .05)], n=14)), S('woodlt', base=.62, up=.1, jit=.02, seed=seed))
    for t in (.12, .5, .88):
        rr = r * (1.0 if t == .5 else .95) + .04
        P.add(put(T(torus(rr, .06, 16, 4), (0, h * t, 0))), S('wood', base=.38, jit=.01))
    P.add(put(cyl(r * .86, .08, 14, y0=h - .02)), S('wood', base=.48, up=.1, jit=.01))
    if not lie:
        P.add(T(T(box((.5, .8, .06)), (0, h * .5, -r - .03)), (x, y, z), yaw), S('cream', base=.85, jit=.01))   # blank paper label (no text)

def sake_barrels(seed=1):
    """cluster: cedar pallet, three standing casks, one on top, one lying in a chock, a wooden ladle bucket"""
    P = Prop('SakeBarrels%d' % seed); rng = random.Random(seed)
    for i in range(6):
        P.add(T(box((4.6, .22, .55), .03), (0, .15, -1.5 + i * .6)), S('woodlt', base=.42 + (i % 2) * .05, up=.1, jit=.01))
    for x in (-1.6, 1.6): P.add(T(box((.4, .35, 3.6)), (x, -.1, 0)), S('wood', base=.38, jit=.01))
    for (x, z) in ((-1.1, -.5), (1.1, -.5), (0, .95)): taru(P, (x, .26, z), seed=int(x * 10 + z))
    taru(P, (0, 1.86, -.1), r=.8, h=1.3, seed=7)
    taru(P, (3.6, 0, .4), r=.85, h=1.5, seed=9, yaw=20, lie=True)
    for s in (-1, 1): P.add(T(box((.5, .4, .3)), (3.6, .2, .4 + s * .9), 20), S('wood', base=.4, jit=.01))
    bucket(P, (-3.3, 0, .6), .55, .8, 3)
    P.add(log((-3.3, .6, .6), (-2.9, 2.0, .2), .05, 5), S('woodlt', base=.6, jit=.01))
    return P

def crates(seed=1):
    """stack: slatted cedar crates with corner battens, a rope-tied sack pile and a basket of root vegetables"""
    P = Prop('Crates%d' % seed); rng = random.Random(seed)
    def crate(c, s, yaw):
        x, y, z = c
        P.add(T(box((s, s, s), .05), (x, y + s / 2, z), yaw), S('woodlt', base=.42, up=.1, jit=.02))
        for k in range(4):
            yy = y + s * (k + .5) / 4
            for sz in (-1, 1):
                P.add(T(T(box((s + .06, s / 4 - .1, .08)), (0, 0, sz * s / 2)), (x, yy, z), yaw), S('woodlt', base=.55 + rng.uniform(-.04, .04), up=.08, jit=.01))
        for sx in (-1, 1):
            for sz in (-1, 1):
                P.add(T(T(box((.16, s + .04, .16)), (sx * s / 2, 0, sz * s / 2)), (x, y + s / 2, z), yaw), S('wood', base=.38, jit=.01))
    crate((-1.0, 0, 0), 1.9, 8); crate((1.1, 0, -.2), 1.7, -6); crate((-.8, 1.9, .1), 1.5, 22)
    for k in range(3):
        P.add(T(blob(.75, seed * 5 + k, n=14, sq=.7), (2.2 + k * .5, .5 + (k == 2) * .7, 1.3 - k * .4)), S('cream', base=.62, up=.12, jit=.03))
    P.add(T(lathe([(.7, 0), (.95, .8), (.88, .85), (.62, .1), (0, .1)], n=14), (-2.6, 0, 1.2)), S('woodlt', base=.5, up=.1, jit=.02))
    for k in range(6):
        a = k * math.tau / 6
        P.add(T(blob(.28, seed + k, n=10, sq=.9), (-2.6 + math.cos(a) * .45, .85, 1.2 + math.sin(a) * .45)), S('roofD' if k % 2 else 'grass', base=.5, up=.15, jit=.03))
    return P

def bench(seed=1, L=4.2):
    """thick cedar bench: two planks, cross battens, iron bolts, carved stone feet"""
    P = Prop('Bench%d' % seed)
    for z in (-.35, .35): P.add(T(box((L, .28, .62), .07), (0, 1.25, z)), S('woodlt', base=.5 + (z > 0) * .04, up=.12, jit=.02))
    for x in (-L / 2 + .6, L / 2 - .6):
        P.add(T(box((.4, .3, 1.5), .05), (x, 1.0, 0)), S('wood', base=.4, jit=.01))
        P.add(T(lathe([(.6, -.3), (.62, .1), (.48, .3), (.42, .9), (.55, 1.0), (0, 1.0)], n=6), (x, 0, 0)), S('stone', base=.6, up=.12, jit=.02))
        for z in (-.35, .35): P.add(T(cyl(.07, .05, 6, y0=1.39), (x, 0, z)), S('iron', base=.5, jit=.01))
    return P

def hand_cart(seed=1):
    """two-wheeled hand cart: plank bed with side boards, long handles, spoked wheels, carrying a cask and sacks"""
    P = Prop('HandCart%d' % seed)
    P.add(T(box((3.0, .25, 4.2), .05), (0, 1.6, 0)), S('woodlt', base=.48, up=.1, jit=.02))
    for sx in (-1, 1):
        P.add(T(box((.16, .7, 4.2), .04), (sx * 1.5, 2.05, 0)), S('woodlt', base=.42, jit=.02))
        P.add(log((sx * 1.1, 1.45, 2.0), (sx * .9, 1.0, 5.2), .1, 6), S('wood', base=.4, jit=.01))
        P.add(T(torus(1.2, .12, 20, 5), (sx * 1.8, 1.2, -.4), 0, 0, 90), S('wood', base=.35, jit=.01))
        for k in range(6):
            a = k * math.pi / 3
            P.add(bar((sx * 1.8, 1.2, -.4), (sx * 1.8, 1.2 + math.sin(a) * 1.15, -.4 + math.cos(a) * 1.15), .09, .09), S('wood', base=.4, jit=.01))
    P.add(log((-.9, 1.0, 5.2), (.9, 1.0, 5.2), .1, 6), S('wood', base=.45, jit=.01))
    P.add(log((-1.9, 1.2, -.4), (1.9, 1.2, -.4), .12, 6), S('iron', base=.4, jit=.01))
    P.add(T(box((.2, 1.4, .2)), (0, .7, 1.6)), S('wood', base=.38, jit=.01))
    taru(P, (-.4, 1.73, -1.0), r=.8, h=1.3, seed=4)
    for k in range(2): P.add(T(blob(.7, seed * 3 + k, n=14, sq=.65), (.6 - k * .9, 2.1, .9 + k * .6)), S('cream', base=.62, up=.12, jit=.03))
    return P

def paper_lantern_post(seed=1, h=5.2):
    """cedar lamp post with a crossarm and a hanging paper lantern, stone footing"""
    P = Prop('LanternPost%d' % seed)
    P.add(T(lathe([(.6, -.4), (.62, .2), (.45, .45), (0, .45)], n=8), (0, 0, 0)), S('stone', base=.58, up=.12, jit=.02))
    P.add(T(box((.36, h, .36), .04), (0, h / 2 + .3, 0)), S('wood', base=.4, up=.08, jit=.02))
    giboshi(P, (0, h + .3, 0), .24)
    P.add(bar((0, h - .3, 0), (0, h - .3, -1.5), .26, .2), S('wood', base=.45, jit=.01))
    P.add(bar((0, h - 1.3, 0), (0, h - .4, -1.0), .16, .16), S('wood', base=.38, jit=.01))
    paper_lantern(P, (0, h - .55, -1.3), .45, .85)
    return P

def torii(w=9.0, h=8.5):
    """shrine gate: two cedar columns on stone bases, double lintel (kasagi with upswept ends + nuki tie beam),
    a centre strut; no plaque (labels are GUIs)"""
    P = Prop('Torii')
    for sx in (-1, 1):
        x = sx * w / 2
        P.add(T(lathe([(.8, -.4), (.8, .4), (.6, .6), (0, .6)], n=10), (x, 0, 0)), S('stone', base=.58, up=.12, jit=.02))
        P.add(T(cyl(.38, h - .6, 10, r2=.32, y0=.5), (x, 0, 0)), S('wood', base=.38, up=.05, jit=.01))
    P.add(T(box((w + 1.6, .45, .5), .06), (0, h - 2.0, 0)), S('wood', base=.4, up=.08, jit=.01))
    pts = [Vector((x, h + .2 + (abs(x) / (w / 2 + 1.6)) ** 3 * .7, 0)) for x in [-(w / 2 + 2.0) + (w + 4.0) * k / 12 for k in range(13)]]
    P.add(tube(pts, .45, sides=4, flat=(1.0, .6), rot0=math.pi / 4), S('wood', base=.3, up=.1, jit=.01))
    P.add(tube([p + Vector((0, -.6, 0)) for p in pts[1:-1]], .32, sides=4, flat=(1.0, .7), rot0=math.pi / 4), S('wood', base=.42, jit=.01))
    P.add(T(box((.5, 1.4, .4), .04), (0, h - 1.1, 0)), S('wood', base=.36, jit=.01))
    return P

def stepping_stones(seed=1, n=6, L=10.0):
    P = Prop('SteppingStones%d' % seed); rng = random.Random(seed)
    for k in range(n):
        t = k / (n - 1); x = rng.uniform(-.6, .6); z = L / 2 - L * t
        P.add(T(blob(rng.uniform(.9, 1.2), seed * 11 + k, n=14, sq=.45), (x, .1, z)), S('stone', base=.55, up=.25, jit=.04))
    return P

# ------------------------------------------------------------------ nature
def jp_pine(seed=1, h=16.0):
    """Japanese black pine: thick leaning trunk with a kink, horizontal limbs ending in big flat layered needle clouds
    (pruned garden style), dark undersides, light tops"""
    P = Prop('JpPine%d' % seed); rng = random.Random(seed * 7)
    lean = rng.choice((-1, 1)) * rng.uniform(.6, 1.0)
    pts = [Vector((0, -1.0, 0)), Vector((lean * .6, h * .22, .3)), Vector((lean * 2.4, h * .45, -.4)), Vector((lean * 2.0, h * .7, .2)), Vector((lean * 1.0, h * .86, 0))]
    P.add(tube(pts, [h * .065, h * .05, h * .04, h * .028, h * .015], sides=9, rough=.08, seed=seed), S('wood', base=.36, up=.05, jit=.04))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(0, .5)
        P.add(log((math.cos(a) * h * .04, .8, math.sin(a) * h * .04), (math.cos(a) * h * .12, -.4, math.sin(a) * h * .12), h * .03, 5, h * .008), S('wood', base=.32, jit=.03))
    pads = []
    specs = [(.42, -2.6, .3), (.52, 2.4, .26), (.62, -.9, .24), (.7, 1.9, .2), (.78, -2.3, .17)]
    for k, (t, a, Lk) in enumerate(specs):
        i = min(3, int(t * 4)); base = pts[i].lerp(pts[i + 1], t * 4 - i)
        a += rng.uniform(-.3, .3); L = h * Lk
        end = base + Vector((math.cos(a) * L, h * .05, math.sin(a) * L))
        P.add(tube([base, base.lerp(end, .5) + Vector((0, h * .04, 0)), end], [h * .022, h * .015, h * .008], sides=6), S('wood', base=.34, jit=.03))
        pads.append((end, h * (.16 + Lk * .25)))
    pads.append((pts[-1] + Vector((0, h * .02, 0)), h * .15))
    for k, (c, r) in enumerate(pads):                                           # layered flat needle clouds
        sh = S('pine', grad=(c.y - r * .25, c.y + r * .35, .22, .78), up=.2, jit=.02, vn=(4, seed + k, .07))
        P.add(T(blob(r, seed * 31 + k * 5, n=34, sq=.32), tuple(c)), sh)
        for j in range(2):
            a = rng.uniform(0, math.tau); off = Vector((math.cos(a) * r * .35, r * (.16 + j * .1), math.sin(a) * r * .35))
            P.add(T(blob(r * (.62 - j * .15), seed * 31 + k * 5 + j + 1, n=26, sq=.38), tuple(c + off)), sh)
    return P

def cloud_tree(seed=1, h=13.0, col='leaf'):
    """broadleaf in the garden style: flared forked trunk, 5 boughs, a dense rounded crown of overlapping puffs packed
    on every bough end + a central dome (no floating puffs), dark beneath, sunlit on top"""
    P = Prop(('Maple%d' if col == 'maple' else 'CloudTree%d') % seed); rng = random.Random(seed * 13)
    fork = Vector((rng.uniform(-.4, .4), h * .32, rng.uniform(-.4, .4)))
    P.add(tube([Vector((0, -1.0, 0)), Vector((0, h * .16, 0)), fork], [h * .065, h * .05, h * .042], sides=9, rough=.05, seed=seed), S('wood', base=.36, up=.05, jit=.03))
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(0, .5)
        P.add(log((math.cos(a) * h * .03, .9, math.sin(a) * h * .03), (math.cos(a) * h * .1, -.3, math.sin(a) * h * .1), h * .03, 5, h * .007), S('wood', base=.33, jit=.03))
    ends = []
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.25, .25); L = h * rng.uniform(.22, .28); up = rng.uniform(.55, .8)
        e = fork + Vector((math.cos(a) * L, L * up, math.sin(a) * L))
        P.add(tube([fork, fork.lerp(e, .5) + Vector((0, h * .03, 0)), e], [h * .03, h * .02, h * .01], sides=6), S('wood', base=.35, jit=.03))
        ends.append(e)
    top = fork + Vector((0, h * .3, 0))
    P.add(tube([fork, top - Vector((0, h * .1, 0))], [h * .03, h * .012], sides=6), S('wood', base=.35, jit=.03))
    lo, hi = fork.y + h * .05, top.y + h * .2
    sh = lambda k: S(col, grad=(lo, hi, .2, .8), up=.16, jit=.02, vn=(5, seed + k, .07))
    P.add(T(blob(h * .21, seed * 41, n=44, sq=.7), tuple(top)), sh(0))                      # central dome
    for k, c in enumerate(ends):
        out = (c - fork); out.y = 0; out = out.normalized() if out.length else Vector((1, 0, 0))
        for j in range(3):
            r = h * rng.uniform(.13, .17) * (1 - j * .18)
            off = out * (j - 1) * r * .5 + Vector((rng.uniform(-.3, .3), j * r * .35, rng.uniform(-.3, .3)))
            P.add(T(blob(r, seed * 41 + k * 3 + j + 1, n=34, sq=.74), tuple(c + off)), sh(k))
    return P

def cedar(seed=1, h=26.0):
    """mountain cedar for the backdrop: straight trunk, stacked drooping sage skirts (narrow spire)"""
    P = Prop('Cedar%d' % seed); rng = random.Random(seed)
    P.add(tube([Vector((0, -1, 0)), Vector((0, h * .6, 0)), Vector((0, h * .97, 0))], [h * .03, h * .02, h * .004], sides=7), S('wood', base=.36, jit=.03))
    tiers = 6
    for i in range(tiers):
        t = i / (tiers - 1); y = h * (.22 + .7 * t); R = h * lerp(.22, .07, t); ht = h * .2 * lerp(1, .7, t)
        sk = B.bough_skirt(R, ht, h * .03, 7 if R > 3 else 6, rng); T(sk, (0, y, 0))
        P.add(sk, S('pine', grad=(y - 1, y + ht, .2 + t * .1, .62 + t * .08), up=.15, jit=.03, seed=seed + i))
    return P

def boulder(seed=1, r=3.0, moss=True):
    P = Prop('Boulder%d' % seed)
    P.add(T(blob(r, seed * 7, n=24, sq=.7), (0, r * .35, 0)), S('rock', base=.5, up=.22, jit=.05, top='grass' if moss else None, thr=.75, topbase=.45))
    P.add(T(blob(r * .45, seed * 7 + 1, n=14, sq=.7), (r * .8, r * .1, r * .3)), S('rock', base=.46, up=.22, jit=.05))
    return P

def crag(seed=1, h=26.0, r=7.0):
    """tall framing crag: 4-5 overlapping tapered rock columns of different heights (one mass, vertical facets),
    sage moss on the flat tops and ledges, fallen blocks at the foot"""
    P = Prop('Crag%d' % seed); rng = random.Random(seed)
    for k in range(5):
        hh = h * rng.uniform(.55, 1.0) * (1 - k * .08); rr = r * rng.uniform(.45, .65)
        a = k * math.tau / 5 + rng.uniform(0, .6); d = r * .35 * (k > 0)
        pts = [p for p in rock_pts((rr, hh * .5, rr * .8), n=30, seed=seed * 13 + k)]
        for p in pts:
            p.y = min(p.y, hh * (.3 + .1 * rng.random()))
            p.x *= lerp(1.0, .6, (p.y / (hh * .5) + 1) / 2); p.z *= lerp(1.0, .6, (p.y / (hh * .5) + 1) / 2)
        P.add(T(hull(pts), (math.cos(a) * d, hh * .5 - 2.0, math.sin(a) * d), rng.uniform(0, 360)),
              S('rock', base=.44 + rng.uniform(-.04, .06), up=.22, jit=.05, top='grass', thr=.78, topbase=.42))
    for k in range(3):
        a = rng.uniform(0, math.tau)
        P.add(T(blob(r * rng.uniform(.18, .28), seed * 5 + k, n=16, sq=.7), (math.cos(a) * r * .9, .3, math.sin(a) * r * .9)), S('rock', base=.48, up=.22, jit=.05))
    return P

def shrub(seed=1, r=1.6, col='leaf'):
    P = Prop('Shrub%d' % seed); rng = random.Random(seed)
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(0, .5); d = 0 if k == 0 else r * .55
        rr = r * rng.uniform(.55, .78)
        P.add(T(blob(rr, seed * 5 + k, n=28, sq=.74), (math.cos(a) * d, rr * .45, math.sin(a) * d)), S(col, grad=(0, r * 1.2, .3, .78), up=.18, jit=.03, seed=k))
    return P

def fern_tuft(seed=1):
    """low clump of sage fronds for wall feet and banks"""
    P = Prop('Tuft%d' % seed); rng = random.Random(seed)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-.2, .2); L = rng.uniform(.9, 1.5)
        pts = [Vector((0, 0, 0)), Vector((math.cos(a) * L * .5, L * .6, math.sin(a) * L * .5)), Vector((math.cos(a) * L, L * .35, math.sin(a) * L))]
        P.add(tube(pts, [.14, .1, .02], sides=3, flat=(2.2, .5)), S('grass', base=.5, up=.15, jit=.05))
    return P
