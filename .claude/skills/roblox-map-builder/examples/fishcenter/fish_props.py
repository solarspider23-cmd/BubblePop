# Tidehook Lagoon prop kit (tropical stilt fishing resort, bright morning).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: a fishing-sim hub on stilts: weathered silver-tan decks, dark teak posts, honey bamboo, golden layered thatch,
# coral stone, palm green. Saturated colour ONLY on 4 station accents: coral red, sun yellow, lagoon teal, lime.
# Signature edge detail: teak rail posts capped with teal glass fishing floats in a rope net + double rope swags.
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
from pro_lib import Palette, box, cyl, spike, tube, hull, rock_pts, nz, clamp, ngon_prism

PAL = Palette({
    'deck':   ('#5e574d', '#a59a88', '#e2d8c4'),     # weathered silver-tan planks, palm trunks
    'wood':   ('#24160f', '#57392a', '#8c6448'),     # dark teak: posts, pilings, frames
    'bamboo': ('#6b5424', '#b99a52', '#ecd79a'),     # honey bamboo, rope, woven mats
    'thatch': ('#6f4f22', '#c49a4e', '#f2d58f'),     # golden palm thatch
    'sand':   ('#a8946e', '#e9dcbb', '#fffaeb'),     # white coral sand
    'coral':  ('#8a7468', '#d6c2b4', '#f6ece4'),     # pale coral stone (plinths, reef rocks)
    'rock':   ('#22252b', '#4b4f57', '#8a8f98'),     # dark volcanic rock, eyes, shadows
    'palm':   ('#1f5a2e', '#4f9c3c', '#b4e070'),     # palm fronds, island grass
    'water':  ('#0e4f7a', '#2fb3c4', '#c9f6f2'),     # turquoise water (dark = deep sea, light = glass)
    'paint':  ('#9aa3ad', '#e8ecef', '#ffffff'),     # white paint (lighthouse, boats, notes, ice)
    'red':    ('#7a1d14', '#e2493a', '#ff9a80'),     # coral red accent
    'yellow': ('#8a5a06', '#f4b928', '#ffe78a'),     # sun yellow accent
    'teal':   ('#0d4f50', '#1fa39b', '#86eedd'),     # lagoon teal accent
    'lime':   ('#3b6a0e', '#8fcf2c', '#d8ff8a'),     # lime accent
    'metal':  ('#3a2e1c', '#a37a3a', '#f0cf86'),     # brass fittings
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'fire': '#ff7a1a', 'lamp': '#ffc35a', 'beacon': '#fff0b0'})
G.GLOW_E.clear(); G.GLOW_E.update({'fire': 3.2, 'lamp': 2.6, 'beacon': 4.0})
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, lathe, torus, sag, h01 = B.T, B.bar, B.lathe, B.torus, B.sag, B.h01
ashlar_ring, ash_sh = B.ashlar_ring, B.ash_sh
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
V3 = Vector

def ball(r, n=10, m=6):
    return lathe([(0, -r)] + [(r * math.sin(math.pi * k / m), -r * math.cos(math.pi * k / m)) for k in range(1, m)] + [(0, r)], n=n)

def ring_band(P, r, y, h, col, base=.5, n=16, out=.08):
    """raised binding / hoop round a vertical pole of radius r"""
    P.add(T(lathe([(r, 0), (r + out, h * .25), (r + out, h * .75), (r, h)], n=n), (0, y, 0)), S(col, base=base, up=.1, jit=.02))

def pole(P, a, b, r, col='bamboo', base=.55, nodes=2.2, sides=6):
    """bamboo pole a->b with raised nodes every `nodes` studs"""
    a, b = V3(a), V3(b); L = (b - a).length; pts = [a]; rad = [r]
    n = max(1, int(L / nodes))
    for k in range(1, n + 1):
        t = k / (n + 1) if n > 1 else .5
        t = k * L / (n + 1) / L
        for dt, rr in ((-.06, r), (0, r * 1.16), (.06, r)):
            pts.append(a.lerp(b, t + dt / L)); rad.append(rr)
    pts.append(b); rad.append(r * .97)
    P.add(tube(pts, rad, sides=sides), S(col, base=base, up=.12, jit=.03))

def rope(P, pts, r=.08, col='bamboo', base=.62):
    P.add(tube([V3(p) for p in pts], r, sides=4), S(col, base=base, up=.1, jit=.02))

def lash(P, c, r, col='bamboo'):
    """rope lashing: two thin hoops round a pole joint at c"""
    for dy in (-.12, .12):
        P.add(T(torus(r + .05, .06, 10, 4), (c[0], c[1] + dy, c[2])), S(col, base=.7, up=.1, jit=.02))

def loft(rings, closed=True):
    """quads between successive rings (lists of Vector, same count); closed = each ring is a loop"""
    bm = bmesh.new(); R = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(R[0])
    for A, Bq in zip(R, R[1:]):
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bm.verts.ensure_lookup_table()
    return bm

# ------------------------------------------------------------------ fish (market, aquarium, icons)
def fish(P, pos, yaw=0.0, L=2.0, col='yellow', pitch=0.0, roll=0.0, kind='round', fin=None, sides=6):
    """a stylised fish along local +X (nose at +X): elliptical body (laterally flat), forked tail, dorsal + pelvic
    fins, eyes. kind: 'round' (snapper), 'long' (tuna / marlin, add bill), 'flat' (angelfish: tall)"""
    fin = fin or col
    hk = {'round': .2, 'long': .14, 'flat': .34}[kind]
    xs = [.5, .44, .3, .1, -.12, -.3, -.4]
    rs = [.0, .45, .85, 1.0, .82, .42, .22]
    pts = [V3((x * L, 0, 0)) for x in xs]; rad = [max(.02, r * hk * L) for r in rs]
    parts = [(tube(pts, rad, sides=sides, flat=(.5, 1.0)), S(col, base=.5, up=.38, jit=.02))]
    tail = [(-.36, 0), (-.56, .26), (-.62, .22), (-.5, 0), (-.62, -.22), (-.56, -.26)]
    tb = ngon_prism([(x * L, y * L * (1.4 if kind == 'flat' else 1)) for x, y in tail], -.025 * L, .025 * L)
    parts.append((T(tb, (0, 0, 0), 0, -90), S(fin, base=.42, up=.1, jit=.02)))
    dh = {'round': .22, 'long': .14, 'flat': .5}[kind]
    dor = ngon_prism([(.18 * L, 0), (-.05 * L, dh * L), (-.24 * L, .02 * L)], -.02 * L, .02 * L)
    parts.append((T(dor, (0, hk * L * .78, 0), 0, -90), S(fin, base=.45, up=.1, jit=.02)))
    if kind == 'flat':
        ven = ngon_prism([(.14 * L, 0), (-.06 * L, -.42 * L), (-.2 * L, -.02 * L)], -.02 * L, .02 * L)
        parts.append((T(ven, (0, -hk * L * .7, 0), 0, -90), S(fin, base=.45, up=.1, jit=.02)))
    else:
        for s in (-1, 1):
            pf = ngon_prism([(0, 0), (-.16 * L, .02 * L), (-.1 * L, .1 * L)], -.012 * L, .012 * L)
            parts.append((T(pf, (.16 * L, -hk * L * .3, s * hk * L * .45), 25 * s, 0, -30), S(fin, base=.45, up=.1, jit=.02)))
    if kind == 'long':
        parts.append((T(spike(.035 * L, .3 * L, 5), (0, 0, 0), 0, 0, -90), S(col, base=.35, up=.1, jit=.02)))
        parts[-1] = (T(parts[-1][0], (.48 * L, 0, 0)), parts[-1][1])
    for s in (-1, 1):
        parts.append((T(ball(.055 * L, 6, 3), (.36 * L, hk * L * .25, s * hk * L * .36)), S('paint', base=.9, up=0, jit=0)))
        parts.append((T(ball(.032 * L, 4, 2), (.37 * L, hk * L * .26, s * hk * L * .41)), S('rock', base=.1, up=0, jit=0)))
    for bm, sh in parts:
        P.add(T(bm, pos, yaw, pitch, roll), sh)

# ------------------------------------------------------------------ thatch (layered, fringed)
def ring_rect(hw, hd, nx, nz_, bulge=0.0):
    """closed rectangle loop with nx points on the X sides and nz_ on the Z sides, sides bulge outward a little"""
    cs = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]; out = []
    for i in range(4):
        a, b = cs[i], cs[(i + 1) % 4]; n = nx if i % 2 == 0 else nz_
        dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz); nxv, nzv = dz / L, -dx / L
        for j in range(n):
            s = j / n; k = math.sin(math.pi * s) * bulge
            out.append((a[0] + dx * s + nxv * k, a[1] + dz * s + nzv * k))
    return out

def ring_circ(r, n, a0=0.0): return [(math.cos(a0 + i * math.tau / n) * r, math.sin(a0 + i * math.tau / n) * r) for i in range(n)]

def thatch_band(P, ringA, yA, ringB, yB, th=.45, fringe=.35, seed=0, col='thatch', base=.55):
    """one layer of thatch: outer surface from ringA (eave, fringed) up to ringB, a thickness `th` under it, closed rim"""
    rng = random.Random(seed); n = len(ringA)
    def inward(p, d):
        v = V3((p[0], 0, p[1])); L = v.length
        d = min(d, L * .6)
        return v * ((L - d) / L) if L > 1e-6 else v
    ob = []; ib = []
    for i, p in enumerate(ringA):
        dy = -fringe * (rng.uniform(.55, 1.0) if i % 2 else rng.uniform(0, .25))
        q = V3((p[0], yA + dy, p[1])); ob.append(q)
        w = inward(p, th * 1.2); ib.append(V3((w.x, yA + dy + th * .5, w.z)))
    ot = [V3((p[0], yB, p[1])) for p in ringB]
    it = []
    for p in ringB:
        w = inward(p, th * 1.2); it.append(V3((w.x, yB - th, w.z)))
    bm = loft([ob, ot, it, ib, ob])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    u = PAL.u(col); vrng = random.Random(seed * 7 + 1)
    colv = [base + vrng.uniform(-.07, .07) for _ in range(n)]
    def sh(f):
        c = f.calc_center_median(); a = math.atan2(c.z, c.x) % math.tau
        k = int(a / math.tau * n) % n
        v = colv[k] + .16 * f.normal.y
        if f.normal.y < -.2: v = base - .22
        return [(u, clamp(v, .04, .96))] * len(f.loops)
    P.add(bm, sh)

def thatch_hip(P, hw, hd, y0, rise, oh=2.2, layers=3, ridge=True, seed=0, col='thatch', bulge=.35, top_frac=None):
    """hip roof of `layers` overlapping fringed thatch bands; ridge bundle along X with bindings"""
    rx = max(.5, hw - hd) if top_frac is None else hw * top_frac
    hw0, hd0 = hw + oh, hd + oh
    nx = max(4, int(2 * hw0 / 1.0)); nz_ = max(4, int(2 * hd0 / 1.0))
    for k in range(layers):
        t0 = k / layers; t1 = min(1.0, (k + 1) / layers + .08)
        def R(t, extra=0.0):
            return ring_rect(lerp(hw0, rx + .4, t) + extra, lerp(hd0, .4, t) + extra, nx, nz_, bulge * (1 - t))
        yA = y0 + rise * t0 + (.25 if k else 0); yB = y0 + rise * (t1 ** .92)
        thatch_band(P, R(t0, .25 * (k > 0)), yA, R(t1), yB, fringe=.4 if k == 0 else .3, seed=seed * 5 + k, col=col,
                    base=.56 - k * .02)
    top = y0 + rise
    if ridge:
        pts = [V3((x, top + .1, 0)) for x in (-rx - 1.0, -rx, 0, rx, rx + 1.0)]
        P.add(tube(pts, [.35, .62, .66, .62, .35], sides=7), S(col, base=.48, up=.14, jit=.03))
        for k in range(-2, 3):
            x = k * (rx + .6) / 2.2
            P.add(T(torus(.66, .09, 10, 4), (x, top + .1, 0), 0, 0, 90), S('bamboo', base=.42, up=.1, jit=.02))
    return top

def thatch_cone(P, r, y0, rise, layers=4, seed=0, col='thatch', n=24):
    for k in range(layers):
        t0 = k / layers; t1 = min(1.0, (k + 1) / layers + .1)
        rA = lerp(r, .35, t0) + (.25 if k else 0); rB = lerp(r, .35, t1)
        thatch_band(P, ring_circ(rA, n), y0 + rise * t0 + (.2 if k else 0), ring_circ(max(rB, .3), n), y0 + rise * t1,
                    fringe=.4 if k == 0 else .3, seed=seed * 5 + k, col=col, base=.56 - k * .02)
    top = y0 + rise
    P.add(T(lathe([(.9, 0), (.7, .5), (.35, 1.4), (.55, 1.8), (0, 2.6)], n=10), (0, top - .6, 0)), S(col, base=.5, up=.15, jit=.03))
    P.add(T(torus(.75, .1, 10, 4), (0, top - .1, 0)), S('bamboo', base=.42, up=.1, jit=.02))
    return top + 1.8

# ------------------------------------------------------------------ walls, floors, awnings
def mat_cell(P, x0, x1, y0, y1, pos, yaw, th=.35, seed=0):
    """woven palm-mat infill between posts: strips 0.55 tall, alternating tone and depth (reads as weave)"""
    n = max(1, round((y1 - y0) / .55)); h = (y1 - y0) / n
    for i in range(n):
        d = .05 if i % 2 else -.05
        P.add(T(T(box((x1 - x0, h - .04, th)), ((x0 + x1) / 2, y0 + h * (i + .5), d)), pos, yaw),
              S('bamboo' if i % 2 else 'thatch', base=.6 if i % 2 else .5, up=.06, jit=.02, seed=seed + i))

def woven_wall(P, L, H, holes, pos, yaw, seed=0, th=.35):
    """wall panel L long, H high (local x -L/2..L/2), holes [(x0, x1, y0, y1)] left open; cells woven"""
    xs = sorted({-L / 2, L / 2} | {h[0] for h in holes} | {h[1] for h in holes})
    ys = sorted({0.0, H} | {h[2] for h in holes} | {h[3] for h in holes})
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            xm, ym = (xa + xb) / 2, (ya + yb) / 2
            if any(h[0] < xm < h[1] and h[2] < ym < h[3] for h in holes): continue
            mat_cell(P, xa, xb, ya, yb, pos, yaw, th, seed)
    for x0, x1, y0, y1 in holes:                               # bamboo frame round every opening
        segs = [((x0, y0, 0), (x0, y1, 0)), ((x1, y0, 0), (x1, y1, 0)), ((x0 - .2, y1, 0), (x1 + .2, y1, 0))]
        if y0 > .1: segs.append(((x0 - .2, y0, 0), (x1 + .2, y0, 0)))
        for a, b in segs:
            P.add(tube([local(a, pos, yaw), local(b, pos, yaw)], .16, sides=5), S('bamboo', base=.45, up=.1, jit=.02))

def local(p, pos, yaw):
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    return R @ V3(p) + V3(pos)

def plank_floor(P, w, d, y, th=.6, plank=1.1, col='deck', seed=0, along='x'):
    """deck platform: planks along `along` with gaps, a dark skirt beam round it"""
    rng = random.Random(seed)
    if along == 'x':
        n = max(1, int(d / plank)); pw = d / n
        for i in range(n):
            P.add(T(box((w, th * .5, pw - .1), .04), (0, y - th * .25, -d / 2 + pw * (i + .5))), S(col, base=.56 + rng.uniform(-.08, .06), up=.12, jit=.01))
    else:
        n = max(1, int(w / plank)); pw = w / n
        for i in range(n):
            P.add(T(box((pw - .1, th * .5, d), .04), (-w / 2 + pw * (i + .5), y - th * .25, 0)), S(col, base=.56 + rng.uniform(-.08, .06), up=.12, jit=.01))
    P.add(T(box((w - .2, th * .6, d - .2)), (0, y - th * .75, 0)), S('wood', base=.3, jit=.01))
    for sx in (-1, 1):
        P.add(T(box((.4, th, d + .4), .06), (sx * (w / 2 + .1), y - th * .55, 0)), S('wood', base=.42, up=.08, jit=.01))
    for sz in (-1, 1):
        P.add(T(box((w + .4, th, .4), .06), (0, y - th * .55, sz * (d / 2 + .1))), S('wood', base=.42, up=.08, jit=.01))

def awning(P, x0, x1, y, z, depth, drop, col, stripes=True, scallop=True):
    """striped canvas awning off a wall at z (front = -Z): slopes out `depth`, down `drop`, scalloped valance"""
    n = max(2, int((x1 - x0) / 1.1)); w = (x1 - x0) / n
    for i in range(n):
        c = col if (i % 2 == 0 or not stripes) else 'paint'
        xa = x0 + w * i
        q = [V3((xa, y, z)), V3((xa + w, y, z)), V3((xa + w, y - drop, z - depth)), V3((xa, y - drop, z - depth))]
        bm = loft([q, [p + V3((0, -.12, 0)) for p in q]], closed=True)
        bm.faces.new([bm.verts[k] for k in range(4)][::-1]); bm.faces.new([bm.verts[k] for k in range(4, 8)])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, S(c, base=.58, up=.15, jit=.02))
        if scallop:                                                         # valance: a hanging half-disc per stripe
            pts = [(0, 0)] + [(math.cos(math.pi + math.pi * k / 6) * w * .5, math.sin(math.pi + math.pi * k / 6) * w * .42) for k in range(7)]
            pts = [(xa + w / 2 + px, py) for px, py in pts[1:]]
            vb = ngon_prism([(px, py) for px, py in pts], -.04, .04)
            bm2 = T(vb, (0, 0, 0), 0, -90)
            P.add(T(bm2, (0, y - drop - .12, z - depth)), S(c, base=.5, up=.1, jit=.02))
    P.add(tube([V3((x0 - .1, y - drop - .1, z - depth)), V3((x1 + .1, y - drop - .1, z - depth))], .1, sides=5), S('wood', base=.4, jit=.01))

def sign_board(P, pos, yaw, w=6.0, h=1.6):
    """BLANK carved sign board for a GUI label (no text): teak frame, light plank face, rope hangers above"""
    L = lambda bm: T(bm, pos, yaw)
    P.add(L(box((w, h, .22), .05)), S('deck', base=.78, up=.05, jit=.0))
    for a, b in (((-w / 2, -h / 2), (w / 2, -h / 2)), ((-w / 2, h / 2), (w / 2, h / 2)), ((-w / 2, -h / 2), (-w / 2, h / 2)), ((w / 2, -h / 2), (w / 2, h / 2))):
        P.add(L(bar((a[0], a[1], -.08), (b[0], b[1], -.08), .22, .2, .04)), S('wood', base=.4, up=.08, jit=.01))
    for sx in (-1, 1):
        P.add(L(T(ball(.18, 8, 4), (sx * w / 2, h / 2, -.1))), S('metal', base=.6, up=.1, jit=.01))

# ------------------------------------------------------------------ edge modules (repeated on every deck lip)
def rail_post(seed=1):
    """teak rail post with the signature cap: a teal glass float in a rope net on a collar"""
    P = Prop('RailPost')
    _post(P, 0)
    return P

def _post(P, x, h=3.2):
    P.add(T(box((.5, h + .8, .5), .06), (x, (h - .8) / 2, 0)), S('wood', base=.42, up=.08, jit=.02))
    P.add(T(box((.66, .22, .66)), (x, h + .02, 0)), S('wood', base=.5, up=.12, jit=.01))
    P.add(T(ball(.36, 8, 4), (x, h + .45, 0)), S('teal', base=.6, up=.25, jit=.02))
    P.add(T(torus(.37, .045, 8, 3), (x, h + .45, 0), 0, 90), S('bamboo', base=.7, up=.1, jit=.01))
    for y in (3.0, 1.85):
        P.add(T(torus(.33, .08, 6, 3), (x, y, 0)), S('bamboo', base=.62, up=.1, jit=.01))

def rail_bay(L=6.0, buoy=False, seed=1, post=True):
    """SIGNATURE edge module: post at -L/2, two rope swags to +L/2 (next bay's post), striped float on some bays.
    post=False ('N' variant): swags only, where another run already put a post on that corner"""
    P = Prop('RailBay%s%s%s' % (('%.2f' % L).replace('.', 'p'), 'B' if buoy else '', '' if post else 'N'))
    x0, x1 = -L / 2, L / 2
    if post: _post(P, x0)
    for y, drop in ((3.0, .35), (1.85, .3)):
        P.add(tube([V3(p) for p in sag((x0 + .25, y, 0), (x1 - .25, y, 0), drop, 5)], .085, sides=3), S('bamboo', base=.62, up=.1, jit=.02))
    if buoy:
        c = V3((0, 3.0 - .35 - .9, 0))
        rope(P, [(0, 3.0 - .35, 0), tuple(c + V3((0, .45, 0)))], .04)
        body = lathe([(0, -.55), (.3, -.45), (.42, -.15), (.42, .2), (.3, .45), (0, .55)], n=10)
        P.add(T(body, tuple(c)), S('red', base=.55, up=.25, jit=.02))
        P.add(T(lathe([(.43, -.08), (.43, .1)], n=10), tuple(c)), S('paint', base=.85, up=.1, jit=.01))
    return P

def tiki_torch(seed=1, h=7.0, stilt=0.0):
    """bamboo torch: pole with nodes, lashings, woven cup, two-tongue flame. stilt > 0 (TikiTorchStilt): the pole runs
    that much further down, for torches standing in the water beside the boardwalk (planted in the seabed)"""
    P = Prop('TikiTorchStilt' if stilt else 'TikiTorch'); rng = random.Random(seed)
    pole(P, (0, -.8 - stilt, 0), (0, h - 1.0, 0), .2, 'bamboo', .5, nodes=3.0, sides=5)
    for y in (h - 2.2, h - 1.6): lash(P, (0, y, 0), .22)
    P.add(T(lathe([(.22, 0), (.42, .3), (.62, .8), (.66, 1.15), (.5, 1.15), (.44, .85)], n=8), (0, h - 1.4, 0)), S('thatch', base=.5, up=.12, jit=.03))
    for k in range(4):
        a = k * math.tau / 4 + .4
        P.add(bar((math.cos(a) * .3, h - 1.3, math.sin(a) * .3), (math.cos(a) * .64, h - .25, math.sin(a) * .64), .1, .08, .02), S('bamboo', base=.4, jit=.02))
    P.add(T(lathe([(.5, 0), (.5, .12)], n=12), (0, h - .3, 0)), S('rock', base=.25, jit=.01))
    for k, (s, rr) in enumerate(((1.0, .42), (.7, .3))):
        fl = spike(rr, 1.5 * s, 5, shoulder=.35)
        P.gadd(T(fl, (k * .12, h - .2, k * .08), rng.uniform(0, 60), 0, 6 - 12 * k), 'fire')
    return P

def lifebuoy_stand(seed=1):
    P = Prop('LifebuoyStand')
    P.add(T(box((.45, 5.2, .45), .07), (0, 1.8, 0)), S('wood', base=.42, up=.08, jit=.02))
    P.add(T(box((.9, .5, .9), .08), (0, -.2, 0)), S('wood', base=.35, up=.08, jit=.02))
    P.add(bar((0, 3.6, -.2), (0, 3.6, -.6), .14, .14, .03), S('metal', base=.5, jit=.01))
    for k in range(8):
        a0 = k * math.tau / 8; a1 = (k + 1) * math.tau / 8
        P.add(T(torus(1.05, .32, 6, 8, a0, a1), (0, 2.6, -.75), 0, 90), S('red' if k % 2 else 'paint', base=.55, up=.25, jit=.02))
    P.add(T(ball(.22, 8, 4), (0, 4.3, 0)), S('teal', base=.6, up=.2, jit=.02))
    return P

# ------------------------------------------------------------------ nature
def palm(seed=1, h=18.0, lean=4.0, nfr=11, nuts=True, name=None):
    """coconut palm: curved ringed trunk (silver-tan), flared foot, boot sheaths, coconuts, V-folded serrated fronds
    that arch and droop (both sides modelled)"""
    P = Prop(name or 'Palm%d' % seed); rng = random.Random(seed)
    a = rng.uniform(0, math.tau); d = V3((math.cos(a), 0, math.sin(a)))
    p0 = V3((0, -1.5, 0)); p1 = V3((0, h * .45, 0)) + d * lean * .15; p2 = V3((0, h, 0)) + d * lean
    C = lambda t: p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t
    n = int(h / 1.4); pts = []; rad = []; r0 = h * .04
    for i in range(n + 1):
        t = i / n
        for dt, k in ((0, 1.0), (.45 / n, .88)):
            if t + dt > 1: continue
            pts.append(C(t + dt)); rad.append(r0 * (1 + 1.1 * (1 - smooth(t / .12))) * lerp(1, .78, t) * k)
    ut = PAL.u('deck')
    P.add(tube(pts, rad, sides=6), lambda f: [(ut, clamp(.36 + .2 * (l.vert.co.y / h) + (.12 if (l.vert.co.y / 1.1) % 1 < .5 else 0) + .08 * f.normal.y, .04, .96)) for l in f.loops])
    top = C(1.0)
    P.add(T(blob(r0 * 1.6, seed * 3, n=18, sq=.9), tuple(top)), S('bamboo', base=.38, up=.15, jit=.04))
    for k in range(6):                                                         # leaf-boot sheaths round the crown
        b = k * math.tau / 6 + rng.uniform(0, .3)
        P.add(T(spike(r0 * .5, r0 * 2.6, 4, shoulder=.6), tuple(top - V3((0, r0 * .8, 0))), math.degrees(-b), 0, 125), S('deck', base=.38, jit=.04))
    if nuts:
        for k in range(4):
            b = k * math.tau / 4 + rng.uniform(0, .4)
            c = top + V3((math.cos(b) * r0 * 1.3, -r0 * 1.4 - rng.uniform(0, .3), math.sin(b) * r0 * 1.3))
            P.add(T(ball(r0 * .95, 8, 5), tuple(c)), S('bamboo', base=.3, up=.2, jit=.03))
    u = PAL.u('palm')
    for k in range(nfr):
        hi = k >= nfr * .6
        az = k * math.tau / (nfr * .6 if not hi else nfr * .4) + (.5 if hi else 0) + rng.uniform(-.2, .2)
        el = math.radians(rng.uniform(55, 70) if hi else rng.uniform(15, 45))
        Lf = h * (rng.uniform(.34, .42) if hi else rng.uniform(.5, .6)); droop = rng.uniform(.9, 1.3) if hi else rng.uniform(1.5, 2.1)
        dirh = V3((math.cos(az), 0, math.sin(az))); side = V3((-dirh.z, 0, dirh.x))
        N = 10; mid = []; L_ = []; R_ = []
        for i in range(N + 1):
            s = i / N
            p = top + dirh * (Lf * s * math.cos(el) * .95) + V3((0, Lf * (s * math.sin(el) - droop * .5 * s * s), 0))
            w = Lf * .2 * math.sin(math.pi * min(1, s * 1.06)) ** .6 * (1.0 if i % 2 == 0 else .6)
            mid.append(p); L_.append(p + side * w - V3((0, w * .5, 0))); R_.append(p - side * w - V3((0, w * .5, 0)))
        bm = bmesh.new()
        M = [bm.verts.new(p) for p in mid]; Lv = [bm.verts.new(p) for p in L_]; Rv = [bm.verts.new(p) for p in R_]
        dn = V3((0, -.05, 0))
        M2 = [bm.verts.new(p + dn) for p in mid]; L2 = [bm.verts.new(p + dn) for p in L_]; R2 = [bm.verts.new(p + dn) for p in R_]
        for i in range(N):
            bm.faces.new((M[i], M[i + 1], Lv[i + 1], Lv[i])); bm.faces.new((M[i], Rv[i], Rv[i + 1], M[i + 1]))
            bm.faces.new((M2[i], L2[i], L2[i + 1], M2[i + 1])); bm.faces.new((M2[i], M2[i + 1], R2[i + 1], R2[i]))
        bm.normal_update()
        topv = top.y
        def sh(f, s0=rng.uniform(-.05, .05)):
            out = []
            for l in f.loops:
                dd = (l.vert.co - top).length / Lf
                v = .36 + .32 * dd + .1 * f.normal.y + s0
                out.append((u, clamp(v, .04, .96)))
            return out
        P.add(bm, sh)
        P.add(tube(mid[:6], [r0 * .35, r0 * .25, r0 * .18, r0 * .12, r0 * .08, r0 * .05], sides=4), S('palm', base=.3, up=.1, jit=.02))
    return P

def palm_planter(seed=1):
    """woven round planter (bamboo hoops) with a young palm and fern tufts"""
    P = Prop('PalmPlanter%d' % seed)
    P.add(lathe([(1.7, -.4), (1.9, .2), (2.1, 1.6), (2.25, 1.85), (2.05, 1.9), (1.85, 1.75), (0, 1.75)], n=14), S('thatch', base=.48, up=.1, jit=.03))
    for y in (.35, 1.0, 1.6): P.add(T(torus(lerp(1.92, 2.18, y / 1.6), .1, 14, 4), (0, y, 0)), S('bamboo', base=.5, up=.1, jit=.02))
    P.add(T(lathe([(1.9, 0), (1.6, .2), (0, .3)], n=12), (0, 1.62, 0)), S('rock', base=.3, up=.1, jit=.03))
    sub = palm(seed + 40, 11.0, 1.6, 7, nuts=False)
    _merge_prop(P, sub, (0, 1.8, 0), .9)
    for k in range(3):
        a = k * math.tau / 3 + .4
        _fern(P, (math.cos(a) * 1.1, 1.85, math.sin(a) * 1.1), seed + k, .6)
    return P

def _merge_prop(P, sub, pos=(0, 0, 0), s=1.0, yaw=0.0):
    """copy a built Prop's geometry into P (moved/scaled), keeping its per-face UVs"""
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    def tr(mb, dst):
        base = len(dst.V)
        dst.V.extend(tuple(R @ (V3(v) * s) + V3(pos)) for v in mb.V)
        dst.F.extend(tuple(i + base for i in f) for f in mb.F); dst.UV.extend(mb.UV); dst.SM.extend(mb.SM)
    tr(sub.solid, P.solid)
    for k, mb in sub.glow.items(): tr(mb, P.glow.setdefault(k, G.MB()))

def _fern(P, c, seed, s=1.0):
    rng = random.Random(seed)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-.2, .2); L = rng.uniform(1.0, 1.5) * s
        pts = [V3(c), V3(c) + V3((math.cos(a) * L * .5, L * .65, math.sin(a) * L * .5)), V3(c) + V3((math.cos(a) * L, L * .3, math.sin(a) * L))]
        P.add(tube(pts, [.16 * s, .12 * s, .02], sides=3, flat=(2.4, .5)), S('palm', base=.45, up=.2, jit=.05))

def tropical_shrub(seed=1, r=2.2):
    """elephant-ear clump: paddle leaves on arching stems (both sides) + a few red hibiscus flowers"""
    P = Prop('Shrub%d' % seed); rng = random.Random(seed)
    u = PAL.u('palm')
    for k in range(12):
        a = k * math.tau / 12 * 2.3 + rng.uniform(-.25, .25); L = r * rng.uniform(.5, 1.0); up = rng.uniform(1.0, 1.7)
        base = V3((math.cos(a) * .2, -.2, math.sin(a) * .2)); tip = V3((math.cos(a) * L * .6, L * up, math.sin(a) * L * .6))
        P.add(tube([base, base.lerp(tip, .5) + V3((0, .3, 0)), tip], [.09, .07, .05], sides=4), S('palm', base=.35, jit=.03))
        d = V3((math.cos(a), rng.uniform(.5, 1.1), math.sin(a))).normalized(); sd = V3((-math.sin(a), 0, math.cos(a)))
        ll = r * rng.uniform(.75, 1.0); n = 4; bm = bmesh.new(); top = []; bot = []
        for i in range(n + 1):
            s = i / n; w = ll * .42 * math.sin(math.pi * s) ** .7
            p = tip + d * ll * s - V3((0, ll * .35 * s * s, 0))
            top.append((bm.verts.new(p + sd * w), bm.verts.new(p + V3((0, .06, 0))), bm.verts.new(p - sd * w)))
            bot.append((bm.verts.new(p + sd * w - V3((0, .05, 0))), bm.verts.new(p - V3((0, .0, 0))), bm.verts.new(p - sd * w - V3((0, .05, 0)))))
        for i in range(n):
            for j in range(2):
                bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]))
                bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]))
        bm.normal_update()
        P.add(bm, lambda f, s0=rng.uniform(-.06, .06): [(u, clamp(.42 + .25 * f.normal.y + s0, .04, .96))] * len(f.loops))
    for k in range(4):
        a = rng.uniform(0, math.tau); c = V3((math.cos(a) * r * .55, r * rng.uniform(.6, .9), math.sin(a) * r * .55))
        for j in range(5):
            b = j * math.tau / 5
            P.add(T(T(box((.55, .07, .3), .03), (.3, 0, 0), math.degrees(b), 0, 18), tuple(c)), S('red', base=.6, up=.2, jit=.03))
        P.add(T(ball(.12, 6, 4), tuple(c + V3((0, .1, 0)))), S('yellow', base=.7, jit=.02))
    return P

def grass_tuft(seed=1):
    """low tropical grass + fern tuft: arching blades in two greens round a small leafy core"""
    P = Prop('GrassTuft%d' % seed); rng = random.Random(seed)
    for k in range(9):
        a = k * math.tau / 9 + rng.uniform(-.2, .2); L = rng.uniform(1.0, 1.8)
        pts = [V3((0, -.2, 0)), V3((math.cos(a) * L * .4, L * .7, math.sin(a) * L * .4)), V3((math.cos(a) * L, L * .35, math.sin(a) * L))]
        P.add(tube(pts, [.13, .1, .02], sides=3, flat=(2.2, .45)), S('palm', base=.3 + .08 * (k % 2), up=.15, jit=.04))
    _fern(P, (0, .1, 0), seed + 5, .8)
    return P

def coral_branch(seed=1, col='red', s=1.0, depth=2):
    """staghorn coral: forking tapered branches with rounded tips on a stone foot"""
    P = Prop('CoralBranch%d%s' % (seed, col[0])); rng = random.Random(seed)
    P.name = 'CoralBranch%d%s%s' % (seed, col[0], '' if depth == 2 else 'd%d' % depth)
    P.add(T(blob(1.0 * s, seed, n=14, sq=.55), (0, 0, 0)), S('coral', base=.5, up=.2, jit=.04))
    def grow(p, d, L, r, depth):
        q = p + d * L
        P.add(tube([p, p.lerp(q, .5) + V3((0, L * .08, 0)), q], [r, r * .85, r * .7], sides=6), S(col, base=.52, up=.2, jit=.03))
        if depth == 0:
            P.add(T(ball(r * .8, 6, 4), tuple(q)), S(col, base=.75, up=.1, jit=.02)); return
        for k in range(2):
            a = rng.uniform(0, math.tau); nd = (d + V3((math.cos(a), .2, math.sin(a))) * .7).normalized()
            grow(q, nd, L * .72, r * .7, depth - 1)
    for k in range(4):
        a = k * math.tau / 4 + rng.uniform(0, .5)
        grow(V3((0, .3 * s, 0)), V3((math.cos(a) * .55, 1, math.sin(a) * .55)).normalized(), 1.6 * s, .26 * s, depth)
    return P

def brain_coral(seed=1, r=1.6, col='yellow'):
    """brain coral: squashed dome with wavy meander ridges following its surface"""
    P = Prop('BrainCoral%d' % seed)
    sq = .82
    prof = [(r * math.sin(math.pi / 2 * k / 6) * 1.0, r * sq * math.cos(math.pi / 2 * k / 6)) for k in range(6, -1, -1)]
    P.add(T(lathe([(r * .95, -.4)] + prof, n=12), (0, 0, 0)), S(col, base=.42, up=.25, jit=.03))
    for k, ph in enumerate((.4, .85, 1.3)):
        w = 6 + k
        pts = []
        for i in range(25):
            th = i * math.tau / 24; p2 = ph + .07 * math.sin(w * th + k)
            pts.append(V3((r * 1.01 * math.sin(p2) * math.cos(th), r * sq * 1.01 * math.cos(p2), r * 1.01 * math.sin(p2) * math.sin(th))))
        P.add(tube(pts, .09, sides=4, cap0=False, cap1=False), S(col, base=.66, up=.15, jit=.02))
    return P

def reef_rock(seed=1, r=2.6):
    """pale coral-stone rock: lumpy main mass, a second lump, barnacle bumps, dark wet foot"""
    P = Prop('ReefRock%d' % seed); rng = random.Random(seed)
    P.add(T(blob(r, seed * 7, n=40, sq=.62), (0, r * .25, 0)), S('coral', base=.5, up=.25, jit=.06, top='sand', thr=.8, topbase=.62))
    P.add(T(blob(r * .55, seed * 7 + 1, n=16, sq=.7), (r * .75, r * .05, r * .35)), S('coral', base=.48, up=.22, jit=.05))
    P.add(T(blob(r * 1.05, seed * 7 + 2, n=16, sq=.3), (0, -r * .1, 0)), S('rock', base=.35, up=.15, jit=.04))
    for k in range(7):
        a = rng.uniform(0, math.tau); y = rng.uniform(0, r * .5)
        P.add(T(lathe([(.28, 0), (.22, .18), (.1, .22), (0, .1)], n=6), (math.cos(a) * r * .86, y, math.sin(a) * r * .86)), S('paint', base=.6, up=.15, jit=.04))
    return P

def sea_stack(seed=1, h=34.0, r=8.0):
    """tall volcanic sea stack: stacked tilted rock columns, grass caps, a palm tuft on top"""
    P = Prop('SeaStack%d' % seed); rng = random.Random(seed)
    top0 = None
    for k in range(4):
        hh = h * (1.0 if k == 0 else rng.uniform(.5, .85)) * (1 - k * .1); rr = r * rng.uniform(.6, .85)
        if top0 is None: top0 = hh * .5 - 3.0 + hh * .32
        a = k * math.tau / 4 + rng.uniform(0, .5); dd = r * .38 * (k > 0)
        pts = rock_pts((rr, hh * .5, rr * .85), n=28, seed=seed * 13 + k)
        for p in pts:
            p.y = min(p.y, hh * (.32 + .1 * rng.random()))
            f = lerp(1.0, .55, (p.y / (hh * .5) + 1) / 2); p.x *= f; p.z *= f
        P.add(T(hull(pts), (math.cos(a) * dd, hh * .5 - 3.0, math.sin(a) * dd), rng.uniform(0, 360)),
              S('rock', base=.42, up=.25, jit=.05, top='palm', thr=.8, topbase=.42))
    for k in range(3):
        a = rng.uniform(0, math.tau)
        P.add(T(blob(r * .3, seed * 5 + k, n=14, sq=.6), (math.cos(a) * r * .9, -.5, math.sin(a) * r * .9)), S('coral', base=.5, up=.2, jit=.05))
    _merge_prop(P, palm(seed + 70, 12.0, 2.0, 7), (0, top0 - .8, 0))
    return P

def cloud(seed=1, w=80.0):
    """flat-bottomed cumulus for the horizon (SmoothPlastic white)"""
    P = Prop('Cloud%d' % seed); rng = random.Random(seed)
    for k in range(12):
        x = rng.uniform(-w * .4, w * .4); r = w * rng.uniform(.11, .2) * (1.3 - abs(x) / w)
        pts = rock_pts((r, r * .8, r * .85), n=44, seed=seed * 11 + k)
        for p in pts: p.y = max(p.y, -r * .15)
        P.add(T(hull(pts), (x, r * .15, rng.uniform(-w * .08, w * .08))), S('paint', grad=(0, w * .25, .62, .96), up=.1))
    return P

# ------------------------------------------------------------------ story props
def crate(P, c, s=2.0, yaw=0.0, fishin=False, seed=0):
    """slatted fish crate: corner posts, side slats with gaps, open top (fish on ice inside when fishin)"""
    L = lambda bm: T(bm, c, yaw)
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(L(T(box((.22, s * .7, .22), .03), (sx * (s / 2 - .11), s * .35, sz * (s * .4 - .11)))), S('wood', base=.4, up=.08, jit=.02))
    for j in range(3):
        y = s * (.12 + j * .22)
        for sz in (-1, 1):
            P.add(L(T(box((s, s * .16, .1)), (0, y, sz * s * .4))), S('deck', base=.62 + .04 * j, up=.08, jit=.02))
        for sx in (-1, 1):
            P.add(L(T(box((.1, s * .16, s * .8)), (sx * s / 2, y, 0))), S('deck', base=.58, up=.08, jit=.02))
    P.add(L(T(box((s - .2, .1, s * .8 - .2)), (0, .08, 0))), S('deck', base=.4, jit=.01))
    if fishin:
        P.add(L(T(box((s - .25, .25, s * .8 - .25)), (0, s * .55, 0))), S('paint', base=.82, up=.08, jit=.03))
        rng = random.Random(seed)
        for k in range(3):
            p = local((-s * .2 + k * s * .2, s * .72, rng.uniform(-.2, .2)), c, yaw)
            fish(P, p, yaw + 90 + rng.uniform(-15, 15), s * .45, rng.choice(('red', 'yellow', 'teal')), pitch=90)

def crate_stack(seed=1):
    P = Prop('Crates%d' % seed); rng = random.Random(seed)
    crate(P, (0, 0, 0), 2.2, rng.uniform(-8, 8), True, seed)
    crate(P, (2.5, 0, .3), 2.0, rng.uniform(-10, 10))
    crate(P, (1.2, 1.55, .1), 2.0, rng.uniform(15, 30), True, seed + 1)
    return P

def barrel(P, c, r=.9, h=1.8, col='wood', yaw=0.0, lie=False, lid=True, seed=0):
    prof = [(r * .86, 0), (r, h * .5), (r * .86, h)]
    bm = lathe([(r * .82, 0)] + [(lerp(r * .86, r, math.sin(math.pi * k / 6)), h * k / 6) for k in range(7)] + [(r * .82, h)], n=14)
    if lie: bm = T(bm, (0, -h / 2, 0)); bm = T(bm, (0, r, 0), 0, 90)
    P.add(T(bm, c, yaw), S(col, base=.5, up=.15, jit=.04, seed=seed))
    for y in (.15, .5, .85):
        hb = T(torus(lerp(r * .88, r, math.sin(math.pi * y)) + .03, .07, 14, 4), (0, h * y, 0))
        if lie: hb = T(T(hb, (0, -h / 2, 0)), (0, r, 0), 0, 90)
        P.add(T(hb, c, yaw), S('metal', base=.4, up=.1, jit=.02))

def barrels(seed=1):
    P = Prop('Barrels%d' % seed)
    barrel(P, (0, 0, 0), .9, 1.9, 'wood', seed=seed)
    barrel(P, (1.9, 0, .4), .8, 1.6, 'wood', 30, seed=seed + 1)
    barrel(P, (.8, 0, 1.9), .8, 1.6, 'wood', 80, lie=True, seed=seed + 2)
    rope(P, [(-.9, 1.9, -.2)] + [(math.cos(a) * .55, 1.95 + k * .01, math.sin(a) * .55) for k, a in enumerate([j * math.tau / 12 for j in range(13)])], .07)
    return P

def net_pile(seed=1):
    """heap of teal fishing net: lumpy mound with a rope mesh draped over its surface, cork floats on the rim, a
    glass float on top"""
    P = Prop('NetPile%d' % seed); rng = random.Random(seed)
    R, Hh = 2.0, 1.1
    def hgt(x, z):
        r = math.hypot(x / R, z / (R * .8))
        return Hh * max(0.0, 1 - r * r) ** .7 * (1 + .18 * math.sin(x * 2.1 + seed) * math.cos(z * 1.7)) if r < 1 else 0.0
    bm = bmesh.new(); n = 10; VV = {}
    for i in range(n + 1):
        for j in range(n + 1):
            x, z = lerp(-R, R, i / n), lerp(-R * .8, R * .8, j / n)
            VV[i, j] = bm.verts.new((x, hgt(x, z) - .05, z))
    for i in range(n):
        for j in range(n):
            if all(hgt(lerp(-R, R, a / n), lerp(-R * .8, R * .8, b / n)) <= 0 for a in (i, i + 1) for b in (j, j + 1)): continue
            bm.faces.new((VV[i, j], VV[i, j + 1], VV[i + 1, j + 1], VV[i + 1, j]))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    P.add(bm, S('teal', base=.3, up=.25, jit=.04))
    for k in range(9):                                                         # rope mesh following the surface
        for axis in (0, 1):
            t = lerp(-.85, .85, k / 8); pts = []
            for j in range(13):
                u = lerp(-1, 1, j / 12)
                x, z = (t * R, u * R * .8) if axis else (u * R, t * R * .8)
                y = hgt(x, z)
                if y > .02: pts.append(V3((x, y + .03, z)))
            if len(pts) > 2: P.add(tube(pts, .045, sides=3), S('teal', base=.72, up=.1, jit=.02))
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.2, .2)
        c = (math.cos(a) * R * .85, .15, math.sin(a) * R * .7)
        P.add(T(lathe([(.18, 0), (.3, .1), (.3, .32), (.18, .42)], n=8), c, 0, rng.uniform(60, 90)), S('yellow', base=.55, up=.2, jit=.03))
    P.add(T(ball(.45, 10, 6), (-.3, Hh + .3, .1)), S('teal', base=.62, up=.3, jit=.02))
    P.add(T(torus(.46, .05, 10, 4), (-.3, Hh + .3, .1), 0, 90), S('bamboo', base=.7, jit=.01))
    return P

def buoy_stack(seed=1):
    """trap floats and a coiled rope: stacked red/yellow/white buoys"""
    P = Prop('BuoyStack%d' % seed); rng = random.Random(seed)
    cols = ['red', 'yellow', 'paint', 'red', 'yellow']
    for k, (x, z, y, rot) in enumerate(((0, 0, 0, 0), (1.3, .2, 0, 30), (.6, -1.1, 0, 60), (.35, -.15, .62, 90), (-1.2, .9, 0, 20))):
        body = lathe([(0, 0), (.4, .08), (.55, .35), (.55, .7), (.4, .98), (0, 1.05)], n=10)
        P.add(T(body, (x, y + (.55 if rot == 90 else 0), z), rng.uniform(0, 90), rot if rot == 90 else 0), S(cols[k], base=.55, up=.25, jit=.03))
        if rot != 90: P.add(T(lathe([(.56, .45), (.56, .6)], n=10), (x, y, z)), S('paint' if cols[k] != 'paint' else 'red', base=.8, jit=.01))
    for k in range(4):
        P.add(T(torus(.75 - k * .06, .09, 14, 4), (-1.0, .1 + k * .17, -1.0)), S('bamboo', base=.62 - k * .03, up=.1, jit=.02))
    return P

def cooler(seed=1, col='teal'):
    """fish cooler: rounded box body, white lid with hinge + latch, side handles, a tail sticking out"""
    P = Prop('Cooler%d' % seed)
    P.add(T(box((2.6, 1.4, 1.5), .22), (0, .7, 0)), S(col, base=.55, up=.2, jit=.02))
    P.add(T(box((2.7, .35, 1.6), .15), (0, 1.55, 0)), S('paint', base=.82, up=.15, jit=.01))
    P.add(T(box((2.2, .12, 1.2), .05), (0, 1.75, 0)), S('paint', base=.9, up=.1, jit=.01))
    for sx in (-1, 1):
        P.add(bar((sx * 1.38, .95, -.4), (sx * 1.38, .95, .4), .14, .14, .03), S('paint', base=.6, jit=.01))
    P.add(T(box((.4, .3, .12), .03), (0, 1.35, -.8)), S('metal', base=.55, up=.1, jit=.01))
    P.add(T(box((.6, .16, .2)), (0, .1, 0)), S('rock', base=.3, jit=.01))
    fish(P, (.3, 1.95, .1), -20, 1.7, 'red', pitch=90)
    return P

def bench(seed=1, L=5.0):
    """driftwood bench: two slab seat planks on X-legs with a stretcher, pegs"""
    P = Prop('Bench%d' % seed); rng = random.Random(seed)
    for k, z in enumerate((-.38, .38)):
        P.add(T(box((L, .3, .7), .1), (0, 1.75, z), rng.uniform(-1, 1)), S('deck', base=.62 + .05 * k, up=.15, jit=.02))
    for sx in (-1, 1):
        x = sx * (L / 2 - .7)
        for sz in (-1, 1):
            P.add(bar((x, -.3, sz * .7), (x, 1.6, -sz * .55), .3, .3, .06), S('wood', base=.42, up=.08, jit=.02))
        P.add(T(ball(.12, 6, 4), (x, 1.92, 0)), S('metal', base=.5, jit=.01))
    P.add(bar((-L / 2 + .7, .8, 0), (L / 2 - .7, .8, 0), .22, .22, .05), S('wood', base=.38, jit=.02))
    return P

def rod(P, base, tip, reel=True, col='red'):
    """fishing rod: cork grip, rod blank, guides, reel, line"""
    base, tip = V3(base), V3(tip); d = (tip - base).normalized()
    P.add(tube([base, base + d * 1.1], [.11, .1], sides=6), S('thatch', base=.55, up=.1, jit=.02))
    P.add(tube([base + d * 1.1, tip], [.07, .025], sides=5), S(col, base=.5, up=.15, jit=.02))
    if reel:
        side = d.cross(V3((0, 1, 0))).normalized() if abs(d.y) < .95 else V3((1, 0, 0))
        c = base + d * .9 - d.cross(side).normalized() * .22
        P.add(T(lathe([(.22, -.12), (.24, -.06), (.24, .06), (.22, .12)], n=10), tuple(c), 0, 0, 0), S('metal', base=.55, up=.15, jit=.01))

def rod_rack(seed=1, n=6):
    """A-frame rod rack: bamboo frame, slotted top rail, rods leaning in slots, a bait jar at the foot"""
    P = Prop('RodRack%d' % seed); rng = random.Random(seed)
    L = n * .8 + 1.0
    for sx in (-1, 1):
        x = sx * L / 2
        pole(P, (x, -.4, .7), (x, 4.2, 0), .16, 'bamboo', .5, nodes=1.6)
        pole(P, (x, -.4, -.7), (x, 4.2, 0), .16, 'bamboo', .5, nodes=1.6)
        lash(P, (x, 4.0, 0), .2)
    pole(P, (-L / 2 - .2, 4.0, 0), (L / 2 + .2, 4.0, 0), .16, 'bamboo', .55, nodes=2.0)
    P.add(T(box((L, .25, .5), .05), (0, .9, .45)), S('wood', base=.42, up=.1, jit=.02))
    cols = ['red', 'yellow', 'teal', 'lime', 'paint', 'red', 'yellow']
    for k in range(n):
        x = -L / 2 + .9 + k * .8
        rod(P, (x, .6, .3), (x + rng.uniform(-.3, .3), 7.6 + rng.uniform(-.6, .4), -.35), True, cols[k % len(cols)])
    return P

def rod_holder(seed=1):
    """fishing-spot rod holder: teak post with a brass bracket of three tubes, rods bending out over the water with
    lines down, bait bucket + small tackle box"""
    P = Prop('RodHolder%d' % seed); rng = random.Random(seed)
    P.add(T(box((.5, 3.6, .5), .07), (0, 1.0, 0)), S('wood', base=.42, up=.08, jit=.02))
    P.add(T(box((1.8, .3, .6), .06), (0, 2.6, 0)), S('metal', base=.5, up=.1, jit=.01))
    for k, a in enumerate((-28, 0, 28)):
        r = math.radians(a); d = V3((math.sin(r), .9, -math.cos(r))).normalized()
        b = V3((math.sin(r) * .7, 2.7, 0))
        P.add(tube([b - d * .4, b + d * .5], .13, sides=6), S('metal', base=.55, up=.1, jit=.01))
        g = b - d * .9
        P.add(tube([g, g + d * 1.1], [.11, .1], sides=6), S('thatch', base=.55, up=.1, jit=.02))
        pts = [g + d * 1.1 + d * (5.6 * t) - V3((0, 1.6 * t * t, 0)) for t in (0, .35, .7, 1.0)]
        P.add(tube(pts, [.07, .055, .04, .025], sides=5), S(('red', 'yellow', 'teal')[k], base=.5, up=.15, jit=.02))
        P.add(T(lathe([(.22, -.12), (.24, -.06), (.24, .06), (.22, .12)], n=10), tuple(g + d * .9 - V3((0, .25, 0)))), S('metal', base=.55, up=.15, jit=.01))
        tip = pts[-1]; P.add(tube([tip, tip - V3((0, 3.2, 0))], .015, sides=3), S('paint', base=.9, jit=0))
    P.add(T(lathe([(.45, 0), (.55, .9), (.5, .92), (0, .92)], n=12), (1.0, 0, .5)), S('paint', base=.72, up=.1, jit=.02))
    P.add(T(lathe([(.5, 0), (0, .05)], n=12), (1.0, .8, .5)), S('rock', base=.3, jit=.02))
    P.add(T(torus(.5, .04, 12, 4, 0, math.pi), (1.0, .95, .5), 0, 90), S('metal', base=.45, jit=.01))
    P.add(T(box((1.3, .7, .8), .1), (-1.0, .35, .6)), S('red', base=.5, up=.2, jit=.02))
    P.add(T(box((1.35, .14, .85), .05), (-1.0, .72, .6)), S('red', base=.65, up=.2, jit=.02))
    P.add(T(box((.5, .12, .14), .03), (-1.0, .86, .6)), S('rock', base=.3, jit=.01))
    return P

def umbrella(seed=1):
    """palapa sun shade: teak pole on a stone foot, conical layered thatch, ring bindings"""
    P = Prop('Palapa%d' % seed)
    P.add(lathe([(1.1, -.3), (1.1, .3), (.7, .5), (0, .5)], n=12), S('coral', base=.55, up=.15, jit=.02))
    pole(P, (0, .3, 0), (0, 7.6, 0), .25, 'bamboo', .5, nodes=2.0)
    for k in range(6):
        a = k * math.tau / 6
        P.add(bar((0, 6.4, 0), (math.cos(a) * 3.6, 7.25, math.sin(a) * 3.6), .14, .12, .03), S('bamboo', base=.45, jit=.02))
    thatch_cone(P, 4.6, 6.9, 2.6, 2, seed, n=16)
    return P

def hammock_palms(seed=1):
    """two palms with a striped hammock slung between them on ropes (a resting story)"""
    P = Prop('HammockPalms%d' % seed)
    for x, sd in ((-5.2, seed * 2 + 80), (5.2, seed * 2 + 81)):
        _merge_prop(P, palm(sd, 15.0, .8, 10), (x, 0, 0))
    n = 10; rows = []
    for j, z in enumerate((-.85, 0, .85)):
        rows.append([V3((lerp(-3.6, 3.6, i / n), 4.3 - 1.9 * math.sin(math.pi * i / n) + abs(z) * .35 * math.sin(math.pi * i / n), z)) for i in range(n + 1)])
    for j in range(2):
        for i in range(n):
            q = [rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]]
            bm = loft([q, [p - V3((0, .1, 0)) for p in q]]); bm.faces.new(bm.verts[:4][::-1]); bm.faces.new(bm.verts[4:8])
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            P.add(bm, S(('red', 'paint', 'yellow', 'paint', 'teal')[i % 5], base=.6, up=.2, jit=.02))
    for sx in (-1, 1):
        x0 = sx * 3.6
        P.add(tube([V3((x0, 4.3, -.85)), V3((x0, 4.3, .85))], .1, sides=5), S('wood', base=.45, jit=.01))
        for z in (-.85, 0, .85): rope(P, [(sx * 5.0, 5.1, 0), (x0, 4.3, z)], .05)
        lash(P, (sx * 5.2, 5.1, 0), .55)
    return P

def drying_rack(seed=1):
    """fish drying rack: two bamboo A-frames, a top pole, lines of hanging fish"""
    P = Prop('DryRack%d' % seed); rng = random.Random(seed)
    for x in (-3, 3):
        pole(P, (x, -.4, .8), (x, 4.6, 0), .16, 'bamboo', .5)
        pole(P, (x, -.4, -.8), (x, 4.6, 0), .16, 'bamboo', .5)
        lash(P, (x, 4.4, 0), .2)
    pole(P, (-3.4, 4.4, 0), (3.4, 4.4, 0), .16, 'bamboo', .55)
    for k in range(7):
        x = -2.4 + k * .8
        rope(P, [(x, 4.3, 0), (x, 3.6, 0)], .03)
        fish(P, (x, 2.85, 0), 0, 1.3 + rng.uniform(-.2, .2), rng.choice(('red', 'yellow', 'deck', 'teal')), roll=-90)
    return P

def marker_buoy(seed=1, col='yellow'):
    """fishing-spot marker: floating striped buoy body, cage top with a small lamp, chain below (origin = waterline)"""
    P = Prop('MarkerBuoy%s' % col.capitalize())
    P.add(lathe([(0, -1.6), (.9, -1.2), (1.4, -.2), (1.45, .4), (1.2, .9), (.5, 1.2), (0, 1.25)], n=14), S(col, base=.55, up=.25, jit=.02))
    P.add(T(lathe([(1.46, -.05), (1.46, .35)], n=14), (0, 0, 0)), S('paint', base=.85, jit=.01))
    for k in range(4):
        a = k * math.tau / 4
        P.add(bar((math.cos(a) * .5, 1.1, math.sin(a) * .5), (math.cos(a) * .2, 3.0, math.sin(a) * .2), .12, .12, .03), S('rock', base=.35, jit=.01))
    P.add(T(torus(.35, .07, 10, 4), (0, 2.0, 0)), S('rock', base=.35, jit=.01))
    P.gadd(T(ball(.3, 8, 4), (0, 2.6, 0)), 'lamp')
    P.add(T(lathe([(.3, 0), (.32, .12), (0, .2)], n=8), (0, 3.0, 0)), S('rock', base=.3, jit=.01))
    P.add(T(torus(.95, .08, 14, 4), (0, -.9, 0)), S('rock', base=.3, jit=.01))
    return P

def bait_bucket(P, c, seed=0):
    """metal bait bucket with handle, worms (red tubes) and shrimp curls inside"""
    rng = random.Random(seed)
    P.add(T(lathe([(.6, 0), (.75, 1.1), (.7, 1.12), (.58, .15), (0, .15)], n=12), c), S('metal', base=.5, up=.15, jit=.02))
    P.add(T(torus(.76, .05, 12, 4), (c[0], c[1] + 1.1, c[2])), S('metal', base=.65, jit=.01))
    P.add(T(torus(.75, .04, 12, 4, 0, math.pi), (c[0], c[1] + 1.1, c[2]), 0, 90), S('metal', base=.45, jit=.01))
    P.add(T(lathe([(.68, 0), (0, .05)], n=12), (c[0], c[1] + .95, c[2])), S('rock', base=.3, jit=.02))
    for k in range(4):
        a = rng.uniform(0, math.tau)
        pts = [V3((c[0] + math.cos(a + j * .6) * .3, c[1] + 1.0 + .08 * math.sin(j * 2), c[2] + math.sin(a + j * .6) * .3)) for j in range(5)]
        P.add(tube(pts, .07, sides=4), S('red', base=.62, up=.1, jit=.03))

# ------------------------------------------------------------------ buildings / stations
def hut_body(P, w, d, H, front_holes, side_holes=(), back_holes=(), floor_h=.9, seed=0):
    """stilt-resort hut: plank floor platform + front steps, thick bamboo corner + mid posts, woven walls with cut
    openings, top beam all round. returns eave height"""
    plank_floor(P, w + 2.0, d + 2.0, floor_h, .7, col='deck', seed=seed)
    for k in range(2):                                                         # front steps down to the deck
        P.add(T(box((4.0, .3, .9), .05), (0, floor_h * (1 - (k + 1) / 3) - .1, -(d / 2 + 1.0) - .45 - k * .9)), S('deck', base=.6 - k * .05, up=.12, jit=.01))
        P.add(T(box((4.2, floor_h * (1 - (k + 1) / 3), .9)), (0, floor_h * (1 - (k + 1) / 3) / 2 - .2, -(d / 2 + 1.0) - .45 - k * .9)), S('wood', base=.35, jit=.01))
    y0 = floor_h
    for sx in (-1, 1):
        for sz in (-1, 1):
            pole(P, (sx * w / 2, y0 - .3, sz * d / 2), (sx * w / 2, y0 + H + .4, sz * d / 2), .42, 'bamboo', .48, nodes=2.0, sides=7)
    walls = [((0, y0, -d / 2), 0, w, front_holes), ((0, y0, d / 2), 180, w, back_holes),
             ((-w / 2, y0, 0), 90, d, side_holes), ((w / 2, y0, 0), -90, d, side_holes)]
    for pos, yaw, L, holes in walls:
        woven_wall(P, L - .8, H, holes, pos, yaw, seed)
    for (a, b) in (((-w / 2, -d / 2), (w / 2, -d / 2)), ((w / 2, -d / 2), (w / 2, d / 2)), ((w / 2, d / 2), (-w / 2, d / 2)), ((-w / 2, d / 2), (-w / 2, -d / 2))):
        P.add(tube([V3((a[0], y0 + H, a[1])), V3((b[0], y0 + H, b[1]))], .3, sides=6), S('bamboo', base=.42, up=.1, jit=.02))
        P.add(tube([V3((a[0], y0 + .25, a[1])), V3((b[0], y0 + .25, b[1]))], .22, sides=6), S('bamboo', base=.4, up=.1, jit=.02))
    for sx in (-1, 1):
        for sz in (-1, 1): lash(P, (sx * w / 2, y0 + H, sz * d / 2), .44)
    return y0 + H

def shutter(P, x0, x1, y1, pos, yaw, col):
    """propped top-hinged window shutter (woven), with a bamboo prop stick"""
    w = x1 - x0
    sh = T(box((w + .3, 2.4, .15), .04), ((x0 + x1) / 2, -1.2, 0))
    sh = T(sh, (0, 0, 0), 0, 55)
    P.add(T(T(sh, (0, y1 + .1, -.1)), pos, yaw), S(col, base=.55, up=.12, jit=.02))
    P.add(T(bar(((x0 + x1) / 2, y1 - 2.2, -.2), ((x0 + x1) / 2, y1 - .9, -1.75), .08, .08, .02), pos, yaw), S('bamboo', base=.5, jit=.01))

def hook_icon(P, c, s=1.0):
    """big brass fish hook (shape icon, no text): eye, shank, bend, point + barb"""
    pts = [V3((0, 3.2 * s, 0)), V3((0, 1.4 * s, 0))]
    for k in range(1, 9):
        a = math.pi + math.pi * k / 8
        pts.append(V3((math.cos(a) * .9 * s + .9 * s, 1.4 * s + math.sin(a) * 1.1 * s, 0)))
    pts.append(V3((1.8 * s, 2.2 * s, 0)))
    P.add(T(tube(pts, [.2 * s] * len(pts), sides=7), c), S('metal', base=.62, up=.25, jit=.02))
    P.add(T(spike(.24 * s, .7 * s, 5, shoulder=.4), (c[0] + 1.8 * s, c[1] + 2.15 * s, c[2])), S('metal', base=.7, up=.2, jit=.01))
    P.add(T(T(spike(.14 * s, .5 * s, 4, shoulder=.3), (0, 0, 0), 0, 0, 145), (c[0] + 1.75 * s, c[1] + 2.0 * s, c[2])), S('metal', base=.66, jit=.01))
    P.add(T(torus(.36 * s, .1 * s, 10, 5), (c[0], c[1] + 3.5 * s, c[2]), 0, 90, 0), S('metal', base=.6, up=.2, jit=.02))

def rod_shop():
    """ROD SHOP (coral red): bamboo hut, woven walls, hip thatch, red striped awning over the counter window, propped
    side shutters, blank sign board, rod rack + rod barrel at the front, brass hook icon on the ridge"""
    P = Prop('RodShop')
    w, d, H = 14.0, 10.0, 7.0
    fh = [(-5.0, 1.5, 2.6, 5.4), (3.2, 5.8, 0.0, 5.2)]                         # counter window, door
    sh = [(-1.4, 1.4, 2.6, 4.8)]
    eave = hut_body(P, w, d, H, fh, sh, [(-2.5, 2.5, 2.6, 4.8)], seed=11)
    y0 = .9
    P.add(T(box((7.2, .3, 1.3), .08), (-1.75, y0 + 2.45, -d / 2 - .55)), S('deck', base=.66, up=.12, jit=.01))      # counter shelf
    for x in (-4.8, 1.3): P.add(bar((x, y0 + .3, -d / 2 - .1), (x, y0 + 2.3, -d / 2 - 1.0), .2, .2, .04), S('wood', base=.4, jit=.01))
    for k in range(3): rod(P, (-5.0, y0 + 2.72 + k * .02, -d / 2 - .25 - k * .4), (1.2, y0 + 2.75, -d / 2 - .3 - k * .4), k == 1, ('red', 'yellow', 'teal')[k])
    for sx in (-1, 1): shutter(P, -1.4, 1.4, y0 + 4.8, (sx * w / 2, 0, 0), -90 * sx, 'red')
    awning(P, -5.6, 2.1, y0 + 6.0, -d / 2 - .2, 2.8, 1.3, 'red')
    for x in (-5.5, 2.0): pole(P, (x, y0 - .2, -d / 2 - 2.9), (x, y0 + 4.7, -d / 2 - 2.9), .17, 'bamboo', .5)
    top = thatch_hip(P, w / 2, d / 2, eave + .2, 6.2, 2.4, 3, seed=11)
    hook_icon(P, (-.9, top + .2, 0), 1.0)
    # rod barrel by the door
    barrel(P, (5.6, y0 - .05, -d / 2 - 1.6), .75, 1.5, 'wood', seed=4)
    for k in range(5):
        a = k * math.tau / 5
        rod(P, (5.6 + math.cos(a) * .3, y0 + .6, -d / 2 - 1.6 + math.sin(a) * .3), (5.6 + math.cos(a) * 1.4, y0 + 7.6, -d / 2 - 1.6 + math.sin(a) * 1.0), k % 2 == 0, ('red', 'yellow', 'teal', 'red', 'lime')[k])
    return P

def bait_shop():
    """BAIT SHOP (lime): round hut of upright bamboo staves, cone thatch (4 layers), curved counter opening with a lime
    awning, bait barrels + bucket, a giant lure icon hanging off the finial"""
    P = Prop('BaitShop')
    R, H, fh = 6.0, 6.2, .9
    P.add(lathe([(R + 1.6, -.6), (R + 1.6, fh - .3), (R + 1.4, fh), (0, fh)], n=24), S('deck', base=.56, up=.12, jit=.02))
    for k in range(24):                                                        # deck ring planks (radial seams)
        a = k * math.tau / 24
        P.add(bar((math.cos(a) * 1.0, fh + .01, math.sin(a) * 1.0), (math.cos(a) * (R + 1.5), fh + .01, math.sin(a) * (R + 1.5)), .06, .04, 0), S('wood', base=.3, jit=.0))
    for k in range(2):
        P.add(T(box((4.0, .3, .9), .05), (0, fh * (1 - (k + 1) / 3) - .1, -(R + 1.6) - .45 - k * .9)), S('deck', base=.6 - k * .05, up=.12, jit=.01))
    n = 64; front = math.radians(-90)
    counter = (math.radians(-90 - 38), math.radians(-90 + 20)); door = (math.radians(-90 + 33), math.radians(-90 + 55))
    def ang_in(a, rg):
        a = (a - rg[0]) % math.tau; return a <= (rg[1] - rg[0]) % math.tau
    for k in range(n):
        a = k * math.tau / n; x, z = math.cos(a) * R, math.sin(a) * R
        if ang_in(a, door): continue
        if ang_in(a, counter):
            pole(P, (x, fh - .1, z), (x, fh + 2.5, z), .22, 'bamboo', .5 + .06 * (k % 2), nodes=9, sides=5)
            pole(P, (x, fh + 5.2, z), (x, fh + H, z), .22, 'bamboo', .5 + .06 * (k % 2), nodes=9, sides=5)
        else:
            pole(P, (x, fh - .1, z), (x, fh + H, z), .22, 'bamboo', .48 + .07 * (k % 3), nodes=2.4, sides=5)
    for y in (fh + .4, fh + H - .2):
        P.add(T(torus(R + .2, .2, 32, 5), (0, y, 0)), S('bamboo', base=.4, up=.1, jit=.02))
    pts = [V3((math.cos(a) * (R + .55), fh + 2.6, math.sin(a) * (R + .55))) for a in [lerp(counter[0], counter[1], k / 8) for k in range(9)]]
    P.add(tube(pts, .3, sides=6, flat=(2.2, .5)), S('deck', base=.66, up=.15, jit=.01))
    for a in (counter[0] + .08, counter[1] - .08):
        P.add(tube([V3((math.cos(a) * R, fh + 2.5, math.sin(a) * R)), V3((math.cos(a) * R, fh + 5.2, math.sin(a) * R))], .26, sides=6), S('bamboo', base=.42, jit=.02))
    for a in (door[0] - .03, door[1] + .03):
        P.add(tube([V3((math.cos(a) * R, fh, math.sin(a) * R)), V3((math.cos(a) * R, fh + H, math.sin(a) * R))], .3, sides=6), S('bamboo', base=.42, jit=.02))
    # lime awning: a cone skirt sector over the counter
    m = 9; ring0 = []; ring1 = []
    for k in range(m + 1):
        a = lerp(counter[0] - .05, counter[1] + .05, k / m)
        ring0.append(V3((math.cos(a) * (R + .2), fh + 5.9, math.sin(a) * (R + .2)))); ring1.append(V3((math.cos(a) * (R + 3.0), fh + 4.6, math.sin(a) * (R + 3.0))))
    for k in range(m):
        q = [ring0[k], ring0[k + 1], ring1[k + 1], ring1[k]]
        bm = loft([q, [p - V3((0, .12, 0)) for p in q]]); bm.faces.new(bm.verts[:4][::-1]); bm.faces.new(bm.verts[4:8])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, S('lime' if k % 2 == 0 else 'paint', base=.58, up=.15, jit=.02))
        mid = (ring1[k] + ring1[k + 1]) / 2; tng = (ring1[k + 1] - ring1[k]); wv = tng.length
        hd = ngon_prism([(math.cos(math.pi + math.pi * j / 6) * wv * .5, -math.sin(math.pi + math.pi * j / 6) * wv * .4 * -1) for j in range(7)], -.04, .04)
        hd = T(T(hd, (0, 0, 0), 0, 90), (0, 0, 0), -math.degrees(math.atan2(tng.z, tng.x)))
        P.add(T(hd, tuple(mid - V3((0, .12, 0)))), S('lime' if k % 2 == 0 else 'paint', base=.5, up=.1, jit=.02))
    for a in (counter[0] - .02, counter[1] + .02):
        pole(P, (math.cos(a) * (R + 2.9), fh - .2, math.sin(a) * (R + 2.9)), (math.cos(a) * (R + 2.9), fh + 4.7, math.sin(a) * (R + 2.9)), .17, 'bamboo', .5)
    top = thatch_cone(P, R + 2.6, fh + H + .1, 7.0, 4, seed=21, n=24)
    # giant lure hanging off a bamboo arm from the finial
    pole(P, (0, top - 1.2, 0), (0, top + 1.6, 0), .16, 'bamboo', .5)
    P.add(bar((0, top + 1.4, 0), (0, top + 1.4, -3.0), .2, .2, .04), S('bamboo', base=.45, jit=.02))
    rope(P, [(0, top + 1.3, -2.8), (0, top + .3, -2.8)], .05)
    lc = V3((0, top - .6, -2.8))
    body = tube([lc + V3((0, .8, 0)), lc + V3((0, .3, 0)), lc + V3((0, -.4, 0)), lc + V3((0, -.9, 0))], [.18, .42, .45, .2], sides=8)
    P.add(body, S('lime', base=.55, up=.25, jit=.02))
    for y in (.4, 0, -.4): P.add(T(torus(.46, .06, 10, 4), tuple(lc + V3((0, y, 0)))), S('yellow', base=.65, jit=.01))
    P.add(T(T(ngon_prism([(-.5, 0), (.5, 0), (0, .55)], -.05, .05), (0, 0, 0), 0, -90), tuple(lc + V3((0, .85, -.0)))), S('paint', base=.75, jit=.01))
    for s in (-1, 1): P.add(T(ball(.12, 6, 4), tuple(lc + V3((s * .32, .45, -.2)))), S('rock', base=.15, jit=0))
    for y in (-.95,):
        for k in range(3):
            a = k * math.tau / 3
            P.add(tube([lc + V3((0, y, 0)), lc + V3((math.cos(a) * .35, y - .45, math.sin(a) * .35)), lc + V3((math.cos(a) * .3, y - .7, math.sin(a) * .3 - .1))], .05, sides=4), S('metal', base=.6, jit=.01))
    # bait goods outside the counter
    barrel(P, (-3.6, fh - .05, -R - 2.2), .8, 1.6, 'wood', seed=5)
    bait_bucket(P, (-2.0, fh - .05, -R - 2.6), 3)
    bait_bucket(P, (-4.8, fh - .05, -R - 1.2), 4)
    return P

def fish_market():
    """FISH MARKET / SELL (sun yellow): open pavilion on 8 teak posts with stone feet, wide hip thatch, long ice counter
    with fish laid out, hanging brass scale, yellow striped awning strip, crates + barrels behind, marlin on the ridge"""
    P = Prop('FishMarket'); rng = random.Random(31)
    w, d, H, fh = 22.0, 12.0, 7.4, .9
    plank_floor(P, w + 2, d + 2, fh, .7, seed=31)
    for k in range(2):
        P.add(T(box((w - 2, .3, .9), .05), (0, fh * (1 - (k + 1) / 3) - .1, -(d / 2 + 1.0) - .45 - k * .9)), S('deck', base=.6 - k * .05, up=.12, jit=.01))
    for sx in (-1.5, -.5, .5, 1.5):
        for sz in (-1, 1):
            x, z = sx * w / 3, sz * d / 2
            P.add(T(lathe([(.75, 0), (.75, .4), (.55, .6), (0, .6)], n=10), (x, fh, z)), S('coral', base=.6, up=.15, jit=.02))
            P.add(T(box((.62, H, .62), .08), (x, fh + .5 + H / 2, z)), S('wood', base=.42, up=.08, jit=.02))
            for s2 in (-1, 1):                                                   # knee braces
                P.add(bar((x, fh + H - 1.6, z), (x + s2 * 1.4, fh + H + .3, z), .25, .25, .04), S('wood', base=.38, jit=.02))
    for z in (-d / 2, d / 2):
        P.add(T(box((w + 1.2, .7, .7), .08), (0, fh + H + .65, z)), S('wood', base=.45, up=.1, jit=.02))
    for x in (-w / 2, -w / 6, w / 6, w / 2):
        P.add(T(box((.6, .6, d + 1.0), .08), (x, fh + H + .65, 0)), S('wood', base=.42, up=.1, jit=.02))
    # counter: plank front, teal kick, ice bed with fish
    cz = -d / 2 + 1.6; cw = w - 3
    for k in range(int(cw / .9)):
        x = -cw / 2 + .45 + k * .9
        P.add(T(box((.84, 2.6, .25)), (x, fh + 1.3, cz - .9)), S('deck', base=.55 + .06 * (k % 2), up=.08, jit=.01))
    P.add(T(box((cw + .4, .4, .4), .05), (0, fh + .2, cz - 1.0)), S('teal', base=.5, up=.1, jit=.01))
    P.add(T(box((cw, 2.6, 1.8)), (0, fh + 1.3, cz)), S('wood', base=.35, jit=.01))
    P.add(T(box((cw + .5, .3, 2.3), .08), (0, fh + 2.7, cz)), S('deck', base=.7, up=.12, jit=.01))
    P.add(T(box((cw - .6, .25, 1.6), .1), (0, fh + 2.95, cz)), S('paint', base=.82, up=.1, jit=.04))
    kinds = [('red', 'round'), ('yellow', 'long'), ('teal', 'round'), ('deck', 'long'), ('lime', 'flat'), ('red', 'round'), ('yellow', 'flat')]
    for k in range(8):
        c, kd = kinds[k % len(kinds)]
        fish(P, (-cw / 2 + 1.3 + k * (cw - 2.6) / 7, fh + 3.25, cz + rng.uniform(-.3, .3)), 90 + rng.uniform(-20, 20), rng.uniform(1.4, 2.0), c, pitch=90, kind=kd)
    # brass hanging scale
    sx_ = 5.0
    rope(P, [(sx_, fh + H + .3, cz - .4), (sx_, fh + 5.6, cz - .4)], .05)
    P.add(T(lathe([(0, 0), (.45, .1), (.5, .7), (.45, 1.2), (0, 1.3)], n=12), (sx_, fh + 4.3, cz - .4)), S('metal', base=.6, up=.2, jit=.02))
    P.add(T(lathe([(0, 0), (.4, .05), (.42, .1)], n=12), (sx_, fh + 4.25, cz - .4), 0, 0, 90), S('paint', base=.9, jit=0))
    for k in range(3):
        a = k * math.tau / 3
        rope(P, [(sx_, fh + 4.3, cz - .4), (sx_ + math.cos(a) * .9, fh + 3.4, cz - .4 + math.sin(a) * .9)], .03)
    P.add(T(lathe([(0, 0), (1.0, .05), (1.05, .3), (.95, .3), (.9, .12), (0, .12)], n=14), (sx_, fh + 3.25, cz - .4)), S('metal', base=.55, up=.2, jit=.02))
    fish(P, (sx_, fh + 3.45, cz - .4), 30, 1.7, 'red', pitch=90)
    # back: crates of fish + barrels + shelf
    crate(P, (-7.5, fh, d / 2 - 2.0), 2.2, 10, True, 2); crate(P, (-5.0, fh, d / 2 - 1.8), 2.0, -6)
    crate(P, (-6.3, fh + 1.55, d / 2 - 1.9), 2.0, 20)
    barrel(P, (7.5, fh, d / 2 - 2.0), .9, 1.9, 'wood', seed=8); barrel(P, (5.5, fh, d / 2 - 1.6), .8, 1.7, 'wood', 40, seed=9)
    awning(P, -w / 2 - .6, w / 2 + .6, fh + H + .5, -d / 2 - .3, 2.2, 1.0, 'yellow')
    top = thatch_hip(P, w / 2 + .2, d / 2 + .2, fh + H + 1.0, 6.6, 2.6, 3, seed=31)
    # marlin icon on the ridge
    P.add(T(box((.5, 2.6, .5), .06), (0, top + 1.0, 0)), S('wood', base=.4, jit=.02))
    fish(P, (0, top + 2.6, 0), 0, 5.0, 'teal', kind='long', fin='yellow', pitch=0, roll=0)
    return P

def thatch_gable(P, hw, hd, y0, rise, oh=2.0, layers=3, seed=0, col='thatch'):
    """steep A-frame thatch: ridge along Z, each side `layers` stepped slabs with a fringed lower edge, woven gable
    triangles front and back, ridge bundle with bindings, crossed bamboo horns at both gable tips"""
    rng = random.Random(seed)
    ang = math.atan2(rise, hw + oh); Ls = (hw + oh) / math.cos(ang); yr = y0 + rise; L = 2 * hd + 2 * oh
    for sx in (-1, 1):
        for j in range(layers):
            f = 1 - j * .3; ls = Ls * f
            bm = T(box((ls, .4, L - j * .3), .06), (sx * ls / 2, .22 * j, 0))
            P.add(T(bm, (0, yr, 0), 0, 0, -sx * math.degrees(ang)), S(col, base=.56 - j * .03, up=.15, jit=.03, seed=seed + j))
            n = int((L - j * .3) / .7)
            for k in range(n):                                                     # fringe tufts on the lower edge
                z = -(L - j * .3) / 2 + (k + .5) * (L - j * .3) / n
                tl = .5 + .4 * rng.random() if k % 2 else .3
                tb = T(box((tl, .14, .62)), (sx * (ls + tl / 2 - .2), .22 * j - .12, z))
                P.add(T(tb, (0, yr, 0), 0, 0, -sx * math.degrees(ang + .12)), S(col, base=.46, up=.1, jit=.03))
    for sz in (-1, 1):                                                         # woven gable triangles
        rows = 9
        for i in range(rows):
            y = y0 + rise * (i + .5) / rows * .92; w2 = (hw + .1) * (1 - (i + .5) / rows * .92)
            P.add(T(box((2 * w2, rise / rows * .92 - .04, .3)), (0, y, sz * hd)), S('bamboo' if i % 2 else 'thatch', base=.6 if i % 2 else .5, up=.05, jit=.02))
    P.add(tube([V3((0, yr + .25, -hd - oh - .4)), V3((0, yr + .25, hd + oh + .4))], .42, sides=7), S(col, base=.48, up=.15, jit=.03))
    for k in range(5):
        z = lerp(-hd - oh, hd + oh, k / 4)
        P.add(T(torus(.44, .08, 10, 4), (0, yr + .25, z), 0, 90), S('bamboo', base=.42, jit=.02))
    for sz in (-1, 1):
        for sx in (-1, 1):
            a = V3((-sx * .9, yr - .8, sz * (hd + oh - .3))); b = V3((sx * 1.6, yr + 2.4, sz * (hd + oh + .1)))
            P.add(tube([a, b], [.18, .12], sides=6), S('bamboo', base=.5, up=.1, jit=.02))
        lash(P, (0, yr + .35, sz * (hd + oh)), .2)
    return yr

def boat_house():
    """BOAT RENTAL (lagoon teal): bamboo hut with a two-tier hip roof, teal shutters + door, crossed oars and a lifebuoy
    on the front wall, rope coils, a blank sign board"""
    P = Prop('BoatHouse')
    w, d, H = 12.0, 9.0, 6.0
    fh = [(-1.4, 1.4, 0.0, 5.0), (-5.0, -2.6, 2.4, 4.6), (2.6, 5.0, 2.4, 4.6)]
    eave = hut_body(P, w, d, H, fh, [(-1.2, 1.2, 2.4, 4.6)], [(-1.2, 1.2, 2.4, 4.6)], seed=41)
    y0 = .9
    for x0, x1 in ((-5.0, -2.6), (2.6, 5.0)): shutter(P, x0, x1, y0 + 4.6, (0, 0, -d / 2), 0, 'teal')
    P.add(T(box((2.6, 4.9, .18), .04), (-.0, y0 + 2.5, -d / 2 + .9)), S('teal', base=.42, up=.05, jit=.01))      # door ajar inside
    for s in (-1, 1):                                                          # crossed oars over the door
        a = V3((s * -2.4, y0 + 6.4, -d / 2 - .35)); b = V3((s * 2.4, y0 + 9.4, -d / 2 - .35))
        P.add(tube([a, b], .1, sides=5), S('deck', base=.62, jit=.02))
        P.add(T(box((.9, 1.6, .14), .05), tuple(b + (b - a).normalized() * .6), 0, 0, math.degrees(math.atan2(b.y - a.y, b.x - a.x)) - 90), S('teal', base=.55, up=.1, jit=.02))
    for k in range(8):
        a0 = k * math.tau / 8
        P.add(T(torus(.95, .3, 6, 8, a0, a0 + math.tau / 8), (6.0, y0 + 3.0, -d / 2 - .75), 0, 90), S('red' if k % 2 else 'paint', base=.55, up=.25, jit=.02))
    for k in range(4):
        P.add(T(torus(.8 - k * .07, .1, 14, 4), (-4.6, y0 + .12 + k * .19, -d / 2 - .6)), S('bamboo', base=.6 - k * .03, up=.1, jit=.02))
    thatch_gable(P, w / 2, d / 2, eave + .1, 8.0, 2.0, 3, seed=41)
    return P

def quest_board():
    """QUEST BOARD: two bamboo posts with lashings, framed cork panel with blank pinned notes, little gable thatch roof,
    a hanging lantern, scroll crate at the foot (labels are GUIs, nothing written)"""
    P = Prop('QuestBoard'); rng = random.Random(51)
    W, Hb, yb = 7.0, 4.2, 2.0
    for sx in (-1, 1):
        pole(P, (sx * (W / 2 + .3), -.6, 0), (sx * (W / 2 + .3), yb + Hb + 1.6, 0), .3, 'bamboo', .48, nodes=2.0, sides=7)
        lash(P, (sx * (W / 2 + .3), yb + .2, 0), .32); lash(P, (sx * (W / 2 + .3), yb + Hb - .2, 0), .32)
        P.add(T(box((1.0, .4, 1.0), .08), (sx * (W / 2 + .3), -.15, 0)), S('coral', base=.55, up=.12, jit=.02))
    P.add(T(box((W, Hb, .3)), (0, yb + Hb / 2, 0)), S('thatch', base=.42, up=.02, jit=.02))
    for a, b in (((-W / 2, yb), (W / 2, yb)), ((-W / 2, yb + Hb), (W / 2, yb + Hb)), ((-W / 2, yb), (-W / 2, yb + Hb)), ((W / 2, yb), (W / 2, yb + Hb))):
        P.add(bar((a[0], a[1], -.12), (b[0], b[1], -.12), .3, .3, .05), S('wood', base=.42, up=.08, jit=.02))
    cols = ['paint', 'paint', 'yellow', 'paint', 'teal', 'paint', 'paint', 'red']
    k = 0
    for row in range(2):
        for col in range(4):
            x = -W / 2 + .95 + col * 1.7 + rng.uniform(-.15, .15); y = yb + 1.15 + row * 1.9 + rng.uniform(-.1, .1)
            P.add(T(box((1.25, 1.5, .06)), (x, y, -.18), 0, 0, rng.uniform(-7, 7)), S(cols[k % 8], base=.82 if cols[k % 8] == 'paint' else .68, up=.0, jit=.03))
            P.add(T(ball(.1, 6, 4), (x, y + .6, -.25)), S(('red', 'yellow', 'teal')[k % 3], base=.6, jit=.01))
            k += 1
    sign_board(P, (0, yb + Hb + .75, -.2), 0, 5.4, 1.1)
    # gable roof: two thatch slabs + ridge bundle
    yr = yb + Hb + 1.7
    for s in (-1, 1):
        bm = T(box((W + 2.6, .35, 2.4), .08), (0, 0, s * 1.05)); bm = T(bm, (0, yr + .6, 0), 0, s * 28)
        P.add(bm, S('thatch', base=.55, up=.15, jit=.03))
        for j in range(9):
            P.add(T(T(box((.9, .12, .6), .03), (-W / 2 - .9 + j * 1.0, -.2, s * 2.1)), (0, yr + .6, 0), 0, s * 28), S('thatch', base=.46, up=.1, jit=.03))
    P.add(tube([V3((-W / 2 - 1.4, yr + .9, 0)), V3((W / 2 + 1.4, yr + .9, 0))], .34, sides=6), S('thatch', base=.45, up=.12, jit=.02))
    # hanging lantern on the right post
    lx = W / 2 + .3 + .9
    P.add(bar((W / 2 + .3, yb + Hb + .9, 0), (lx, yb + Hb + .9, 0), .14, .14, .03), S('wood', base=.4, jit=.01))
    rope(P, [(lx, yb + Hb + .85, 0), (lx, yb + Hb + .2, 0)], .03)
    P.add(T(lathe([(.35, 0), (.45, .1), (.45, .9), (.3, 1.05), (.12, 1.2)], n=8), (lx, yb + Hb - 1.0, 0)), S('metal', base=.45, up=.1, jit=.02))
    P.gadd(T(lathe([(.3, 0), (.38, .4), (.3, .8)], n=8), (lx, yb + Hb - .9, 0)), 'lamp')
    # scroll crate
    crate(P, (-W / 2 + .3, 0, -1.6), 1.6, 12)
    for k in range(4):
        P.add(T(T(cyl(.16, 1.5, 8), (0, -.75, 0)), (-W / 2 + .1 + k * .25, 1.35, -1.6 + rng.uniform(-.2, .2)), rng.uniform(0, 40), 70, 0), S('paint', base=.8, up=.1, jit=.02))
    return P

def fish_index_wall():
    """AQUARIUM INDEX wall: plank backboard on teak posts, 3 x 4 oval plaques each with a mounted fish (different
    colours and shapes), blank brass name plates, small hip thatch roof (index entries are GUIs)"""
    P = Prop('FishIndexWall'); rng = random.Random(61)
    W, Hh, yb = 12.0, 7.0, .8
    for sx in (-1, 1):
        P.add(T(box((.7, Hh + 2.6, .7), .08), (sx * (W / 2 + .2), (Hh + 2.6) / 2 - .5, 0)), S('wood', base=.42, up=.08, jit=.02))
        P.add(T(lathe([(.8, 0), (.8, .3), (.55, .5), (0, .5)], n=10), (sx * (W / 2 + .2), -.2, 0)), S('coral', base=.6, up=.12, jit=.02))
    for k in range(int(W / .8)):
        P.add(T(box((.76, Hh, .3), .03), (-W / 2 + .4 + k * .8, yb + Hh / 2, 0)), S('deck', base=.5 + .06 * (k % 2), up=.05, jit=.02))
    for y in (yb, yb + Hh):
        P.add(T(box((W + .8, .4, .5), .06), (0, y, -.1)), S('wood', base=.45, up=.1, jit=.02))
    kinds = [('red', 'round'), ('yellow', 'long'), ('teal', 'flat'), ('lime', 'round'), ('deck', 'long'), ('red', 'flat'),
             ('yellow', 'round'), ('teal', 'long'), ('paint', 'round'), ('red', 'long'), ('lime', 'flat'), ('yellow', 'round')]
    i = 0
    for row in range(3):
        for col in range(4):
            x = -W / 2 + 1.6 + col * (W - 3.2) / 3; y = yb + 1.2 + row * 2.25
            pl = lathe([(0, 0), (1.15, .02), (1.2, .18), (1.05, .26), (0, .26)], n=14)
            P.add(T(T(pl, (0, 0, 0), 0, 90), (x, y, -.15), 0, 0, 0, s=(1.0, .72, 1.0)), S('wood', base=.55, up=.05, jit=.02))
            c, kd = kinds[i]
            fish(P, (x, y + .1, -.65), 0, 1.6 if kd != 'long' else 1.9, c, kind=kd)
            P.add(T(box((.9, .22, .08), .02), (x, y - .78, -.5)), S('metal', base=.66, up=.05, jit=.01))
            i += 1
    sign_board(P, (0, yb + Hh + .9, -.4), 0, 6.5, 1.3)
    thatch_hip(P, W / 2 + .4, .9, yb + Hh + 1.8, 2.4, 1.4, 1, seed=61)
    return P

def welcome_arch():
    """WELCOME ARCH on the spawn axis: two lashed triple-bamboo pillars on coral plinths, a curved driftwood lintel
    with a thatch ridge cap, hanging glass floats + a carved fish, torch cups on top of the pillars"""
    P = Prop('WelcomeArch'); rng = random.Random(71)
    hw, Hp = 7.5, 10.5
    for sx in (-1, 1):
        x = sx * hw
        P.add(T(lathe([(1.5, -.6), (1.5, .5), (1.2, .8), (1.2, 1.2), (.95, 1.4), (0, 1.4)], n=12), (x, 0, 0)), S('coral', base=.58, up=.12, jit=.02))
        for k in range(3):
            a = k * math.tau / 3 + .5
            pole(P, (x + math.cos(a) * .42, 1.0, math.sin(a) * .42), (x + math.cos(a) * .42, Hp, math.sin(a) * .42), .32, 'bamboo', .48 + .05 * k, nodes=2.2, sides=7)
        for y in (2.2, Hp - 2.6): P.add(T(torus(.82, .12, 12, 4), (x, y, 0)), S('bamboo', base=.7, up=.1, jit=.02))
        P.add(T(lathe([(.5, 0), (.8, .4), (.9, .9), (.7, .9), (.6, .5), (0, .5)], n=12), (x, Hp, 0)), S('thatch', base=.5, up=.12, jit=.03))
        P.gadd(T(spike(.5, 1.5, 6, shoulder=.35), (x, Hp + .55, 0), rng.uniform(0, 60)), 'fire')
    pts = [V3((-hw - 1.6, Hp - 1.9, 0)), V3((-hw * .5, Hp - .8, 0)), V3((0, Hp - .5, 0)), V3((hw * .5, Hp - .8, 0)), V3((hw + 1.6, Hp - 1.9, 0))]
    P.add(tube(pts, [.5, .62, .66, .62, .5], sides=8, rough=.06, seed=3), S('deck', base=.6, up=.15, jit=.02))
    P.add(tube([p + V3((0, .75, 0)) for p in pts[1:4]], [.42, .5, .42], sides=7), S('thatch', base=.5, up=.15, jit=.03))
    for sx in (-1, 1): lash(P, (sx * hw, Hp - 1.3, 0), .85)
    cols = ['teal', 'yellow', 'teal', 'red']
    for k, x in enumerate((-4.8, -2.6, 2.6, 4.8)):
        y = Hp - .7 - .35 * abs(x) / 4.8
        drop = 1.0 + .6 * (k % 2)
        rope(P, [(x, y, 0), (x, y - drop, 0)], .04)
        P.add(T(ball(.42, 10, 6), (x, y - drop - .4, 0)), S(cols[k], base=.6, up=.3, jit=.02))
        P.add(T(torus(.43, .045, 10, 4), (x, y - drop - .4, 0), 0, 90), S('bamboo', base=.7, jit=.01))
    rope(P, [(0, Hp - 1.0, 0), (0, Hp - 1.6, 0)], .05)
    fish(P, (0, Hp - 2.3, 0), 0, 3.2, 'yellow', kind='round', fin='red')
    return P

# ------------------------------------------------------------------ boats (origin = waterline centre, bow = -Z)
def boat_hull(L, W, D, top=1.4, sheer=.7, n=20, k=9, thick=.22):
    """hollow lofted boat hull: U sections closed by the sheer line (solid), sharp bow at -Z, transom at +Z, minus a
    smaller copy raised through the top (boolean) = a real open boat with wall + floor thickness"""
    def sec(s, inset=0.0, lift=0.0):
        hw = max(.03, W / 2 * math.sin(math.pi / 2 * min(1, s / .45)) ** .8 * (1 - .12 * s) - inset)
        d = D * (.5 + .5 * math.sin(math.pi * min(1, s / .9))) - inset
        yt = top + sheer * (1 - s) ** 2 + lift
        z = -L / 2 + L * s
        if lift > 0:
            return [V3((hw * u, -d + (yt + d) * abs(u) ** 2.4, z)) for u in [-1 + i / k for i in range(2 * k + 1)]]
        st = yt - .55                                                          # section rows sit ON the paint lines
        ys = [yt, st, lerp(0, st, .6), lerp(0, st, .25), 0.0, -d * .4, -d * .75, -d]
        us = [((y + d) / (yt + d)) ** (1 / 2.4) for y in ys]
        return [V3((-hw * u, y, z)) for u, y in zip(us, ys)] + [V3((hw * u, y, z)) for u, y in list(zip(us, ys))[-2::-1]]
    def solid(secs):
        bm = loft(secs); m = len(secs[0])
        bm.faces.new(bm.verts[:m][::-1]); bm.faces.new(bm.verts[-m:])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        return bm
    outer = solid([sec(.02 + .98 * i / n) for i in range(n + 1)])
    inner = solid([sec(lerp(.09, .97, i / n), thick, 3.0) for i in range(n + 1)])
    ytf = lambda z: top + sheer * (1 - (z + L / 2) / L) ** 2
    return G.bool_diff(outer, inner), sec, ytf

def paint_hull(col, stripe, bottom, ytf):
    """hull shading: bottom colour below the waterline, a stripe band under the sheer line (follows it), body between"""
    def sh(f):
        c = f.calc_center_median(); n = f.normal; top = ytf(c.z)
        if c.y < -.02: ramp, b = bottom, .45
        elif c.y > top - .56: ramp, b = stripe, .55
        else: ramp, b = col, .55
        if n.x * c.x < -.05 * abs(c.x) and abs(c.x) > .2 and n.y < .6: ramp, b = 'paint', .62        # inner walls
        if n.y > .6 and c.y < top - .3: ramp, b = 'deck', .55                 # inside floor boards
        return [(PAL.u(ramp), clamp(b + .2 * n.y + (h01(round(c.x, 1), 0, round(c.z, 1)) - .5) * .04, .04, .96))] * len(f.loops)
    return sh

def skiff(seed=1):
    """rowboat (white, teal stripe, red bottom): hollow hull, gunwale rail, 2 thwarts, oars shipped, bow line + cleat"""
    P = Prop('Skiff')
    L, W, D, top = 12.0, 4.4, 1.1, .9
    bm, sec, ytf = boat_hull(L, W, D, top, .8)
    P.add(bm, paint_hull('paint', 'teal', 'red', ytf))
    for side in (-1, 1):
        pts = [V3((p.x, p.y + .05, p.z)) for p in [sec(s)[0 if side < 0 else -1] for s in [lerp(.04, 1.0, i / 12) for i in range(13)]]]
        P.add(tube(pts, .14, sides=5), S('wood', base=.45, up=.15, jit=.02))
    for z in (-1.0, 2.2):
        s = (z + L / 2) / L; hw = sec(s)[0].x
        P.add(T(box((abs(hw) * 2 - .3, .2, .9), .04), (0, top - .1, z)), S('deck', base=.62, up=.12, jit=.01))
    for s_ in (-1, 1):
        P.add(tube([V3((s_ * .6, top + .2, -2.6)), V3((s_ * 1.0, top + .25, 3.4))], .08, sides=5), S('deck', base=.62, jit=.01))
        P.add(T(box((.5, .08, 1.6), .03), (s_ * 1.03, top + .25, 3.9)), S('teal', base=.55, jit=.01))
    rope(P, [(0, top + 1.3, -L / 2 + .3), (0, top + .8, -L / 2 - .6), (0, top + .3, -L / 2 - 1.4)], .06)
    return P

def motor_boat(seed=1):
    """small fishing boat (sun yellow, white stripe, teal bottom): hull, canvas sun roof on 4 posts, outboard motor,
    rod holders, cooler, net bin, bow cleat"""
    P = Prop('FishingBoat')
    L, W, D, top = 16.0, 6.0, 1.4, 1.1
    bm, sec, ytf = boat_hull(L, W, D, top, 1.0)
    P.add(bm, paint_hull('yellow', 'paint', 'teal', ytf))
    for side in (-1, 1):
        pts = [V3((p.x, p.y + .05, p.z)) for p in [sec(s)[0 if side < 0 else -1] for s in [lerp(.04, 1.0, i / 12) for i in range(13)]]]
        P.add(tube(pts, .16, sides=5), S('wood', base=.45, up=.15, jit=.02))
    P.add(T(box((4.6, .2, 7.0), .04), (0, top - .35, 2.0)), S('deck', base=.6, up=.1, jit=.01))
    for sx in (-1, 1):
        for z in (.2, 4.4):
            P.add(T(box((.22, 3.8, .22), .04), (sx * 1.9, top + 1.6, z)), S('paint', base=.75, up=.05, jit=.01))
    rb = T(box((4.8, .2, 5.4), .1), (0, top + 3.6, 2.3)); P.add(rb, S('teal', base=.55, up=.2, jit=.02))
    for k in range(5):
        P.add(T(box((4.9, .08, .5)), (0, top + 3.73, .1 + k * 1.1)), S('paint', base=.85, jit=.01))
    # outboard motor on the transom
    mz = L / 2 + .3
    P.add(T(box((1.0, 1.4, 1.2), .3), (0, top + .9, mz + .5)), S('paint', base=.75, up=.2, jit=.02))
    P.add(T(box((1.05, .3, 1.25), .12), (0, top + 1.6, mz + .5)), S('red', base=.55, up=.2, jit=.02))
    P.add(T(box((.35, 2.4, .5), .08), (0, top - .9, mz + .6)), S('rock', base=.35, up=.1, jit=.02))
    P.add(T(lathe([(.12, 0), (.5, .05), (.5, .12), (.12, .17)], n=8), (0, top - 1.9, mz + .95), 0, 90), S('metal', base=.5, jit=.01))
    P.add(bar((0, top + 1.1, mz), (0, top + 1.2, mz - 1.4), .12, .12, .03), S('rock', base=.3, jit=.01))
    for sx in (-1, 1):                                                         # rod holders on the stern quarters
        rod(P, (sx * 2.4, top + .1, 5.4), (sx * 4.2, top + 6.5, 8.6), True, 'red' if sx < 0 else 'yellow')
    barrel(P, (-1.2, top - .25, -.8), .6, 1.1, 'teal', seed=3)
    P.add(T(box((1.8, 1.0, 1.1), .15), (1.0, top + .25, -1.4)), S('paint', base=.75, up=.2, jit=.02))
    P.add(T(box((1.9, .2, 1.2), .08), (1.0, top + .8, -1.4)), S('teal', base=.5, up=.2, jit=.02))
    rope(P, [(0, top + 1.8, -L / 2 + .3), (0, top + 1.2, -L / 2 - .8), (0, top + .4, -L / 2 - 1.8)], .07)
    return P

# ------------------------------------------------------------------ the hero: lighthouse aquarium
DOME_R = 20.0; DOME_Y = 2.2; DOME_OPEN = 5.4
def aquarium_dome():
    """glass dome aquarium: coral-stone ashlar drum with a teal cap course, glass hemisphere (water-ramp light = Glass)
    with white ribs + brass rings, top collar for the lighthouse, arched entrance porch with a glass barrel vault,
    coral, sea grass and fish inside"""
    P = Prop('AquaDome'); rng = random.Random(81)
    R, y0 = DOME_R, DOME_Y
    P.add(ashlar_ring(R + 1.0, -.6, y0 - .35, 3.2, 1.0, seed=3, skip=lambda a, y: abs(((a - math.radians(270)) + math.pi) % math.tau - math.pi) < .2),
          ash_sh('coral', base=.62, var=.07, grime=.12))
    P.add(lathe([(R + .9, -.6), (R + .9, y0 - .35), (0, y0 - .35)], n=40), S('coral', base=.45, jit=.01))
    P.add(lathe([(R + 1.35, y0 - .45), (R + 1.4, y0 - .1), (R + .6, y0 + .15), (0, y0 + .15)], n=40), S('teal', base=.55, up=.2, jit=.01))
    P.add(lathe([(R - .2, y0 + .15), (R - .2, y0 + .25), (0, y0 + .25)], n=32), S('sand', base=.6, up=.1, jit=.03))
    N, M = 32, 8; ft = math.acos(DOME_OPEN / R)
    def vp(i, j, rr=R):
        th = i * math.tau / N; ph = ft * j / M
        return V3((rr * math.cos(ph) * math.cos(th), y0 + rr * math.sin(ph), rr * math.cos(ph) * math.sin(th)))
    door = lambda i: abs(((i + .5) * math.tau / N - math.radians(270) + math.pi) % math.tau - math.pi) < math.radians(12)
    gl = bmesh.new(); VV = {}
    def gv(i, j, rr):
        k = (i % N, j, rr)
        if k not in VV: VV[k] = gl.verts.new(vp(i % N, j, rr))
        return VV[k]
    for i in range(N):
        for j in range(M):
            if j < 2 and door(i): continue
            for rr, flip in ((R, False), (R - .08, True)):
                q = [gv(i, j, rr), gv(i + 1, j, rr), gv(i + 1, j + 1, rr), gv(i, j + 1, rr)]
                gl.faces.new(q[::-1] if flip else q)
    gl.normal_update()
    ug = PAL.u('water')
    P.add(gl, lambda f: [(ug, .84)] * len(f.loops))
    for i in range(0, N, 2):                                                   # meridian ribs
        if door(i) and door(i - 1): continue
        j0 = 2 if (door(i) or door(i - 1)) else 0
        pts = [vp(i, j, R + .12) for j in range(j0, M + 1)]
        P.add(tube(pts, .32, sides=5), S('paint', base=.8, up=.12, jit=.01))
    for j in (2, 4, 6):
        ph = ft * j / M; r = R * math.cos(ph) + .12
        if j == 2:
            a0 = math.radians(270 + 12); P.add(T(torus(r, .28, 40, 5, a0, a0 + math.tau - math.radians(24)), (0, y0 + R * math.sin(ph), 0)), S('metal', base=.6, up=.15, jit=.01))
        else:
            P.add(T(torus(r, .26, 40, 5), (0, y0 + R * math.sin(ph), 0)), S('metal', base=.6, up=.15, jit=.01))
    yt = y0 + R * math.sin(ft)
    P.add(T(lathe([(DOME_OPEN + .6, -.2), (DOME_OPEN + .5, .5), (DOME_OPEN - .4, 1.1), (DOME_OPEN - 1.0, 1.1), (DOME_OPEN - 1.0, -.1)], n=24), (0, yt, 0)), S('paint', base=.78, up=.15, jit=.01))
    P.add(T(torus(DOME_OPEN + .55, .22, 24, 5), (0, yt + .2, 0)), S('metal', base=.62, jit=.01))
    # entrance porch at -Z: portal frame + glass barrel vault 5 deep, floor slab
    zf = -R * math.cos(math.radians(12)) + .4; zo = zf - 5.0; hw, wall = 3.6, 2.4
    for sx in (-1, 1):
        for z in (zo, zf):
            P.add(T(box((.7, wall, .7), .08), (sx * hw, y0 + wall / 2, z)), S('paint', base=.78, up=.1, jit=.01))
    for z in (zo, zo + 2.5, zf):
        P.add(T(torus(hw, .3, 14, 5, 0, math.pi), (0, y0 + wall, z), 0, 90, 0), S('paint', base=.8, up=.12, jit=.01))
    prof = [(-hw, y0 + .3), (-hw, y0 + wall)] + [(-math.cos(math.pi * k / 10) * hw, y0 + wall + math.sin(math.pi * k / 10) * hw) for k in range(1, 10)] + [(hw, y0 + wall), (hw, y0 + .3)]
    vb = bmesh.new()
    for (xa, ya), (xb, yb) in zip(prof, prof[1:]):
        for sc_, flip in ((1.0, False), ((hw - .08) / hw, True)):
            ya_, yb_ = y0 + (ya - y0) * sc_, y0 + (yb - y0) * sc_
            q = [vb.verts.new(p) for p in ((xa * sc_, ya_, zo), (xb * sc_, yb_, zo), (xb * sc_, yb_, zf), (xa * sc_, ya_, zf))]
            vb.faces.new(q if flip else q[::-1])
    vb.normal_update()
    P.add(vb, lambda f: [(ug, .84)] * len(f.loops))
    P.add(T(box((2 * hw + 1.6, .5, zf - zo + 1.0), .1), (0, y0 - .05, (zf + zo) / 2)), S('coral', base=.66, up=.12, jit=.02))
    P.add(T(box((2 * hw + 2.6, 1.2, 2.0), .12), (0, y0 + wall + hw + .5, zo - .2)), S('teal', base=.55, up=.15, jit=.01))
    sign_board(P, (0, y0 + wall + hw + .5, zo - 1.3), 0, 6.0, 1.0)
    # inside: coral, sea grass, fish
    for k in range(9):
        a = k * math.tau / 9 + .3; d = rng.uniform(9, 16)
        if abs(((a - math.radians(270)) + math.pi) % math.tau - math.pi) < .5: continue
        c = (math.cos(a) * d, y0 + .2, math.sin(a) * d)
        if k % 3 == 0: _merge_prop(P, brain_coral(k, rng.uniform(1.4, 2.2), ('yellow', 'lime', 'red')[k % 3]), c)
        else: _merge_prop(P, coral_branch(k, ('red', 'teal', 'yellow', 'lime')[k % 4], rng.uniform(1.2, 1.7), 1), c, 1.0, rng.uniform(0, 360))
    for k in range(10):
        a = rng.uniform(0, math.tau); d = rng.uniform(7, 15); b = V3((math.cos(a) * d, y0 + .2, math.sin(a) * d))
        hh = rng.uniform(3, 7); pts = [b + V3((math.sin(j * 1.3 + k) * .4, hh * j / 5, math.cos(j * 1.1 + k) * .4)) for j in range(6)]
        P.add(tube(pts, [.22, .2, .17, .14, .1, .05], sides=4, flat=(2.0, .6)), S('palm', base=.45, up=.1, jit=.04))
    for k in range(13):
        a = rng.uniform(0, math.tau); d = rng.uniform(8, 15.5); y = y0 + rng.uniform(3, 13)
        rmax = math.sqrt(max(1, R * R - (y - y0) ** 2)) - 2.5
        d = min(d, rmax)
        c, kd = rng.choice((('red', 'round'), ('yellow', 'flat'), ('teal', 'round'), ('lime', 'flat'), ('yellow', 'long'), ('paint', 'round')))
        fish(P, (math.cos(a) * d, y, math.sin(a) * d), math.degrees(-a) + 90 + rng.uniform(-20, 20), rng.uniform(2.0, 3.4), c, kind=kd, sides=6)
    return P

def lighthouse():
    """the lighthouse rising out of the dome: coral plinth, tapered tower in red / white bands, small framed windows,
    corbelled gallery with railing, glass lantern room with mullions and the beacon, red cap + vent ball + finial"""
    P = Prop('Lighthouse')
    H = 50.0; r0, r1 = 4.8, 3.4
    rt = lambda y: lerp(r0, r1, y / H)
    P.add(lathe([(6.2, -.6), (6.2, 2.0), (5.6, 2.6), (5.3, 2.6), (5.3, 3.4), (0, 3.4)], n=20), S('coral', base=.6, up=.12, jit=.02))
    bands = [(3.2, 12.0, 'paint'), (12.0, 20.0, 'red'), (20.0, 28.0, 'paint'), (28.0, 36.0, 'red'), (36.0, 44.0, 'paint'), (44.0, H, 'red')]
    for y0, y1, c in bands:
        P.add(lathe([(rt(y0), y0), (rt(y1), y1)], n=20), S(c, base=.55, up=.1, jit=.01))
        P.add(T(lathe([(rt(y0) + .12, -.15), (rt(y0) + .12, .15)], n=20), (0, y0, 0)), S('paint' if c == 'red' else 'red', base=.4, jit=.01))
    for k, y in enumerate((16.0, 24.0, 32.0, 40.0)):                          # windows on a spiral (stair inside)
        a = math.radians(-90 + 70 * k); r = rt(y)
        c = V3((math.cos(a) * r, y, math.sin(a) * r)); yaw = -math.degrees(a) - 90
        P.add(T(box((1.5, 2.2, .5), .08), tuple(c), yaw), S('paint', base=.85, up=.1, jit=.01))
        P.add(T(box((1.0, 1.7, .3)), tuple(c + V3((math.cos(a) * .12, 0, math.sin(a) * .12))), yaw), S('rock', base=.18, jit=.01))
        P.add(T(box((1.8, .25, .7), .05), tuple(c - V3((0, 1.2, 0))), yaw), S('paint', base=.75, up=.1, jit=.01))
    # gallery
    P.add(T(lathe([(r1 - .1, 0), (r1 + .9, .6), (5.8, 1.0), (5.8, 1.5), (0, 1.5)], n=24), (0, H - .5, 0)), S('paint', base=.72, up=.15, jit=.01))
    for k in range(16):
        a = k * math.tau / 16
        P.add(bar((math.cos(a) * (r1 - .1), H - 2.4, math.sin(a) * (r1 - .1)), (math.cos(a) * 5.4, H + .55, math.sin(a) * 5.4), .3, .26, .04), S('paint', base=.6, jit=.01))
        P.add(T(box((.16, 2.4, .16), .02), (math.cos(a) * 5.5, H + 2.2, math.sin(a) * 5.5)), S('rock', base=.3, jit=.01))
    for y in (H + 2.2, H + 3.4):
        P.add(T(torus(5.5, .12 if y < H + 3 else .16, 32, 5), (0, y, 0)), S('rock', base=.32, up=.1, jit=.01))
    # lantern room
    yl = H + 1.0
    P.add(T(lathe([(3.3, 0), (3.3, 1.4), (3.0, 1.5), (0, 1.5)], n=16), (0, yl, 0)), S('red', base=.5, jit=.01))
    P.add(T(lathe([(2.9, 0), (2.9, 5.0), (0, 5.0)], n=16), (0, yl + 1.5, 0)), lambda f: [(PAL.u('water'), .84)] * len(f.loops))
    for k in range(8):
        a = k * math.tau / 8
        P.add(T(box((.25, 5.0, .25)), (math.cos(a) * 2.95, yl + 4.0, math.sin(a) * 2.95)), S('rock', base=.3, jit=.01))
    for y in (yl + 1.5, yl + 3.7, yl + 6.5):
        P.add(T(torus(3.0, .15, 16, 4), (0, y, 0)), S('rock', base=.3, jit=.01))
    P.gadd(T(lathe([(0, 0), (1.1, .4), (1.5, 1.4), (1.5, 2.4), (1.1, 3.2), (0, 3.6)], n=12), (0, yl + 2.2, 0)), 'beacon')
    P.add(T(lathe([(3.6, 0), (3.5, .4), (2.6, 1.6), (1.4, 2.6), (.5, 3.0), (0, 3.05)], n=16), (0, yl + 6.4, 0)), S('red', base=.55, up=.2, jit=.01))
    P.add(T(ball(.65, 10, 6), (0, yl + 9.9, 0)), S('rock', base=.3, up=.2, jit=.01))
    P.add(T(spike(.15, 2.6, 5, shoulder=.4), (0, yl + 10.4, 0)), S('metal', base=.6, jit=.01))
    return P
