# The Gilded Dunes prop kit (open dune sea, high midday sun). Roblox space (X east, Y up, Z south, 1 unit = 1 stud),
# origin = bottom centre, front = -Z. Theme: a gilded sun-kingdom buried by the desert: pale-gold sandstone ashlar with
# carved SHAPE reliefs (sun discs, chevrons, rosettes; never glyphs), gold caps and inlays, a nomad caravan camped among
# the ruins (indigo / madder / saffron cloth stretched over poles, rugs, camels), one palm oasis (palms = realistic
# alpha-card species from examples/oaktrees/gen_trees.py, placed by the map).
# Signature detail: a raised sun disc relief (disc + ray wedges) on every built piece. Shared base: a stepped sandstone
# plinth with a gold trim line. Machinery (Prop, S, blob, materials, to_kit) from the skill's grove module, helpers
# (T, bar, lathe, torus, ashlar) from the medieval example; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, hull, nz, clamp, bevel, spike

PAL = Palette({
    'sand':    ('#a8743a', '#e8b86a', '#fff0c0'),     # pale gold dune sand
    'stone':   ('#8c6238', '#dcb276', '#fbe8bf'),     # gilded sandstone ashlar
    'stone2':  ('#6a3e26', '#b97c52', '#ecbf92'),     # weathered rose sandstone (ruin walls, contrast)
    'gold':    ('#6e3e06', '#d89a1c', '#fff0a0'),     # gold caps, inlays, brass
    'wood':    ('#3a2416', '#76502f', '#b88a5a'),     # poles, crates, well frame
    'cloth':   ('#8c7a5c', '#e2d3b2', '#fffaec'),     # cream canvas
    'indigo':  ('#0e1748', '#26399a', '#7a92ea'),     # nomad indigo cloth (accent)
    'red':     ('#551010', '#b4302a', '#f27a58'),     # madder red cloth / rugs (accent)
    'saffron': ('#8a4806', '#f0a01c', '#ffe27a'),     # saffron cloth / goods (accent)
    'water':   ('#05566e', '#14b4c4', '#aaf8ff'),     # oasis water (turquoise accent)
    'palm':    ('#264412', '#5c9a26', '#c4e470'),     # reeds, green scrub
    'bone':    ('#8a7a60', '#e0d4b8', '#fffaf0'),     # bleached bone
    'camel':   ('#6a4222', '#b8824a', '#eec48c'),     # camel hide
    'rock':    ('#5a2e1a', '#a85a34', '#e8a070'),     # distant mesas, outcrops
    'scrub':   ('#4e4e26', '#8e8a48', '#d2cc8a'),     # dry desert scrub
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
import dune_paint as PAINT
PAINT.install(G, PAL)
G.GLOW.clear(); G.GLOW.update({'gold': '#ffcf4a', 'portal': '#38f0ff', 'fire': '#ff7a1e', 'lamp': '#ffb347', 'gem': '#ff4fd8'})
G.GLOW_E.clear(); G.GLOW_E.update({'gold': 2.2, 'portal': 4.0, 'fire': 4.0, 'lamp': 3.0, 'gem': 3.0})
Prop, S, blob = G.Prop, G.S, G.blob
T, bar, lathe, torus, sag = B.T, B.bar, B.lathe, B.torus, B.sag
ash_sh, h01 = B.ash_sh, B.h01
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

def V(col, y0, y1, a, b, nk=.12, ns=None, seed=0, amp=.1):
    """soft per-loop shade: height ramp + vertex-normal lift + low-frequency noise"""
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

def merge_into(P, tmp, fn=None):
    """merge a temporary Prop's solid (+ glow) into P, optionally mapping every vertex (Vector -> Vector)"""
    for mb in [tmp.solid] + list(tmp.glow.values()):
        if fn: mb.V = [tuple(fn(Vector(v))) for v in mb.V]
    P.solid.merge(tmp.solid)
    for k, mb in tmp.glow.items(): P.glow.setdefault(k, G.MB()).merge(mb)

def grid_quad(x0, x1, z0, z1, y, cell=8.0):
    """flat top split into ~cell faces (the atlas squeezes a face that spans more than one texture period)"""
    nx = max(1, round((x1 - x0) / cell)); nzz = max(1, round((z1 - z0) / cell))
    bm = bmesh.new(); Vv = {}
    for i in range(nx + 1):
        for j in range(nzz + 1): Vv[i, j] = bm.verts.new((lerp(x0, x1, i / nx), y, lerp(z0, z1, j / nzz)))
    for i in range(nx):
        for j in range(nzz):
            f = bm.faces.new((Vv[i, j], Vv[i, j + 1], Vv[i + 1, j + 1], Vv[i + 1, j])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    return bm

def frustum(w0, d0, w1, d1, y0, y1):
    """battered block: base w0 x d0 at y0 -> top w1 x d1 at y1 (x / z full sizes)"""
    pts = [Vector((sx * w / 2, y, sz * d / 2)) for (w, d, y) in ((w0, d0, y0), (w1, d1, y1)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return hull(pts)

def disc(r, d, n=12, bev=.05):
    """a disc on the plane facing -Z (thickness d toward -Z)"""
    return T(cyl(r, d, n, bev=bev), (0, 0, 0), 0, -90)

# ------------------------------------------------------------------ carved shape reliefs (shapes only, never glyphs)
def sun_relief(P, c, r, yaw=0.0, col='stone', depth=.35, rays=12, gold=False, pitch=0.0):
    """SIGNATURE: raised sun disc + ray wedges on a plane facing -Z, turned by yaw and moved to c"""
    put = lambda bm: T(bm, c, yaw, pitch)
    P.add(put(disc(r * .42, depth, 12, min(.08, depth * .3))), S('gold' if gold else col, base=.64, up=.1, jit=.02))
    P.add(put(T(torus(r * .55, depth * .2, 14, 4), (0, 0, -depth * .2), 0, 90)), S(col, base=.55, jit=.02))
    for k in range(rays):
        a = k * math.tau / rays; L = r * (1.0 if k % 2 == 0 else .8)
        ca, sa = math.cos(a), math.sin(a); px, py = -sa, ca; w = r * .1
        pts = [Vector((ca * r * .63 + px * w, sa * r * .63 + py * w, 0)), Vector((ca * r * .63 - px * w, sa * r * .63 - py * w, 0)),
               Vector((ca * L, sa * L, 0)), Vector((ca * r * .63 + px * w * .6, sa * r * .63 + py * w * .6, -depth * .7)),
               Vector((ca * r * .63 - px * w * .6, sa * r * .63 - py * w * .6, -depth * .7)), Vector((ca * L * .96, sa * L * .96, -depth * .2))]
        P.add(put(hull(pts)), S('gold' if gold else col, base=.58, up=.1, jit=.03))

def zig_band(P, L, c, yaw=0.0, h=1.0, col='stone', depth=.25):
    """raised zigzag band between two rails (centre c, length L along local x, facing -Z)"""
    n = max(2, int(L / (h * 1.1)))
    pts = [Vector((-L / 2 + L * i / (2 * n), (h * .32 if i % 2 else -h * .32), -depth * .4)) for i in range(2 * n + 1)]
    P.add(T(tube(pts, depth * .45, sides=4, rot0=math.pi / 4), c, yaw), S(col, base=.62, up=.1, jit=.02))
    for sy in (-1, 1):
        P.add(T(T(box((L, .16, depth * .7)), (0, sy * h * .62, -depth * .35)), c, yaw), S(col, base=.66, jit=.01))

# ------------------------------------------------------------------ masonry
def block_wall(P, L, H, th, prof=None, bw=2.6, bh=1.5, col='stone2', seed=0, gap=None, z=0.0, base=.56, bev=.14):
    """wall of REAL bevelled blocks through the wall, running bond, broken top prof(x); gap = (xa, xb, top)"""
    rng = random.Random(seed); rows = max(1, round(H / bh)); bh2 = H / rows
    x0 = -L / 2
    for i in range(rows):
        y0 = i * bh2; x = x0 - (bw * .5 if i % 2 else 0)
        while x < x0 + L - 1e-3:
            ww = bw * rng.uniform(.75, 1.25); xa, xb = max(x, x0), min(x + ww, x0 + L); x += ww
            if xb - xa < .5: continue
            xm = (xa + xb) / 2
            if prof and y0 + bh2 * .5 > prof(xm): continue
            if gap and gap[0] < xm < gap[1] and y0 < gap[2]: continue
            P.add(T(box((xb - xa - .06, bh2 - .05, th + rng.uniform(-.1, .1)), bev), (xm, y0 + bh2 / 2 + rng.uniform(-.04, .04), z + rng.uniform(-.08, .08)), rng.uniform(-1.5, 1.5)),
                  S(col, base=base + rng.uniform(-.07, .07), up=.12, jit=.02, seed=seed + i))

def plinth(P, w, d, h=1.2, steps=2, col='stone', gold=True):
    """SHARED BASE: stepped sandstone plinth, a chamfered course per step, gold trim line on the top step"""
    for k in range(steps):
        ww, dd = w + (steps - 1 - k) * 1.6, d + (steps - 1 - k) * 1.6
        y1 = h * (k + 1) / steps
        P.add(T(box((ww, y1 + .6, dd), .12), (0, (y1 - .6) / 2, 0)), S(col, base=.56 - k * .02, up=.12, jit=.015, seed=k))
    if gold: P.add(T(box((w + .08, .14, d + .08)), (0, h - .25, 0)), S('gold', base=.62, jit=.01))

def column(P, c, h=14.0, r=1.3, col='stone', broken=None, seed=0):
    """square base + torus, drummed 10-sided shaft with entasis, flared bell capital + gold ring + abacus;
    broken = height of a jagged break instead of the capital"""
    x, y, z = c; rng = random.Random(seed)
    P.add(T(box((r * 3.0, 1.0, r * 3.0), .1), (x, y - .1, z)), S(col, base=.5, up=.12, jit=.02))
    P.add(T(torus(r * 1.12, .28, 12, 5), (x, y + .62, z)), S(col, base=.56, jit=.02))
    top = (h - 2.2) if broken is None else broken
    ndr = max(1, int(top / 2.4)); yy = y + .5
    for k in range(ndr):
        hh = (top - .5) / ndr; ra = r * (1 - .1 * k / ndr); rb = r * (1 - .1 * (k + 1) / ndr)
        P.add(T(lathe([(ra * .96, 0), (ra, .1), (rb, hh - .1), (rb * .96, hh)], n=10, a0=rng.uniform(0, 1)), (x, yy, z)),
              S(col, base=.55 + rng.uniform(-.05, .05), up=.1, jit=.03, seed=seed + k))
        yy += hh
    if broken is None:
        rt = r * .9
        P.add(T(lathe([(rt, 0), (rt * 1.05, .3), (rt * 1.5, 1.2), (rt * 1.65, 1.55), (rt * 1.5, 1.7), (0, 1.7)], n=12), (x, yy, z)), S(col, base=.6, up=.1, jit=.02))
        P.add(T(torus(rt * 1.04, .14, 12, 4), (x, yy + .25, z)), S('gold', base=.6, jit=.01))
        P.add(T(box((r * 3.4, .55, r * 3.4), .08), (x, yy + 1.95, z)), S(col, base=.62, up=.12, jit=.02))
    else:
        rr = r * .9; sl = rng.uniform(.25, .45); a0 = rng.uniform(0, math.tau)
        def brk_y(px, pz): return sl * (px * math.cos(a0) + pz * math.sin(a0)) + rng.uniform(-.12, .12)
        pts = [Vector((math.cos(a) * rr, -.3, math.sin(a) * rr)) for a in [k * math.tau / 10 for k in range(10)]]
        for k in range(10):
            a = k * math.tau / 10; px, pz = math.cos(a) * rr, math.sin(a) * rr
            pts.append(Vector((px, .35 + brk_y(px, pz) + (rr * sl if k % 3 == 0 else 0) * .0, pz)))
        for k in range(4):
            a = rng.uniform(0, math.tau); px, pz = math.cos(a) * rr * .5, math.sin(a) * rr * .5
            pts.append(Vector((px, .45 + brk_y(px, pz), pz)))
        P.add(T(hull(pts), (x, yy, z)), S(col, base=.66, up=.15, jit=.05))


# ------------------------------------------------------------------ HERO: the step pyramid
def step_pyramid():
    """HERO: six-tier gilded step pyramid (ashlar faces, cornice lips, sun + chevron reliefs on the sides), central stair
    with solid balustrades on the FRONT (-Z), open sun shrine on the summit (glowing gold sun disc). 100 x 100, ~74 tall."""
    P = Prop('StepPyramid'); rng = random.Random(3)
    S0 = 50.0; TH = 8.4; NT = 6; DS = 6.6
    halves = [S0 - k * DS for k in range(NT)]
    sw = 7.5
    for k, s in enumerate(halves):
        y0 = k * TH
        P.add(T(box((2 * s - .6, TH - .05, 2 * s - .6)), (0, y0 + TH / 2 - .02, 0)), S('stone', base=.45, jit=.01))
        P.add(grid_quad(-s, s, -s, s, y0 + TH, 10.0), S('stone', base=.62, up=.08, jit=.03, seed=k))
        for face in range(4):
            skip = (lambda x, y: abs(x) < sw + 1.0) if face == 0 else None
            pan = B.ashlar(2 * s, TH - .7, 6.0, (TH - .7) / 3.0, seed=k * 7 + face, skip=skip, depth=.14, ins=.1)
            T(pan, (0, y0, 0), 180); T(pan, (0, 0, -s + .02)); T(pan, (0, 0, 0), face * 90.0)
            P.add(pan, ash_sh('stone', base=.6, var=.07, grime=.0))
            P.add(T(T(box((2 * s + 1.4, .7, 1.0), .18), (0, y0 + TH - .3, -s - .2)), (0, 0, 0), face * 90.0), S('stone', base=.68, up=.1, jit=.02))
        for face in (1, 2, 3):
            a = math.radians(face * 90)
            at = lambda lx, y: (math.sin(a) * (-s - .1) + math.cos(a) * lx, y, math.cos(a) * (-s - .1) - math.sin(a) * lx)
            if k in (0, 2):
                n = 3 if k == 0 else 2
                for i in range(n):
                    sun_relief(P, at((i - (n - 1) / 2) * (2 * s / n), y0 + TH * .45), 2.2, face * 90.0, gold=(k == 0 and i == 1))
            if k in (1, 3):
                zig_band(P, 2 * s - 6, at(0, y0 + TH * .5), face * 90.0, h=1.6)
    ytop = NT * TH; zfront = -S0 - 12.0; zback = -halves[-1] + 1
    nst = int(ytop / .95); rise = ytop / nst; run = (zback - zfront) / nst
    for i in range(nst):
        y1 = (i + 1) * rise; za = zfront + i * run
        P.add(T(box((2 * sw, rise, run + 1.2), .06), (0, y1 - rise / 2, za + (run + 1.2) / 2 - .05)), S('stone', base=.58 + (i % 2) * .04, up=.14, jit=.02, seed=i))
    for sx in (-1, 1):
        x = sx * (sw + 1.3)
        pts = [Vector((x + d, y, zz)) for d in (-1.3, 1.3) for (y, zz) in ((-.3, zfront - 1.2), (2.4, zfront - 1.2), (ytop + 2.4, zback), (-.3, zback))]
        P.add(hull(pts), S('stone', base=.6, up=.12, jit=.02))
        cap = [Vector((x + d, y, zz)) for d in (-1.55, 1.55) for (y, zz) in ((2.4, zfront - 1.4), (3.0, zfront - 1.4), (ytop + 3.0, zback + .2), (ytop + 2.4, zback + .2))]
        P.add(hull(cap), S('stone', base=.72, up=.1, jit=.02))
        P.add(T(box((3.4, 1.2, 3.4), .15), (x, 3.6, zfront - 1.0)), S('stone', base=.66, up=.1, jit=.02))
        P.add(T(lathe([(1.2, 0), (1.25, .2), (.6, 1.0), (.25, 1.6), (0, 1.75)], n=8), (x, 4.2, zfront - 1.0)), S('gold', base=.6, up=.15, jit=.02))
        sun_relief(P, (x, 1.3, zfront - 1.32), 1.0, 0.0, gold=True)
    P.add(T(box((2 * S0 + 5, 1.6, 2 * S0 + 5), .2), (0, -.1, 0)), S('stone', base=.5, up=.12, jit=.01))
    P.add(grid_quad(-S0 - 2.5, S0 + 2.5, -S0 - 2.5, S0 + 2.5, .72, 10.0), S('stone', base=.55, up=.1, jit=.03, seed=99))
    # summit shrine
    yt = ytop; s = halves[-1] - 3.0
    for (w, d), (px, pz) in (((2 * s, 1.6), (0, s - .8)), ((1.6, 2 * s - 3), (-s + .8, .9)), ((1.6, 2 * s - 3), (s - .8, .9))):
        P.add(T(box((w, 9.0, d), .1), (px, yt + 4.5, pz)), S('stone', base=.56, up=.1, jit=.02))
    for i in range(4):
        column(P, (-s + 1.2 + i * (2 * s - 2.4) / 3, yt, -s + 1.4), h=9.0, r=.75, seed=40 + i)
    P.add(T(box((2 * s + 2.4, 1.3, 2 * s + 2.4), .2), (0, yt + 9.65, 0)), S('stone', base=.64, up=.1, jit=.02))
    P.add(T(box((2 * s + 1.0, 1.0, 2 * s + 1.0), .2), (0, yt + 10.8, 0)), S('stone', base=.6, up=.1, jit=.02))
    P.add(T(box((2 * s + 2.6, .2, 2 * s + 2.6)), (0, yt + 10.25, 0)), S('gold', base=.62, jit=.01))
    P.add(T(lathe([(2.4, 0), (2.4, .5), (1.6, 1.2), (.4, 3.4), (0, 3.6)], n=8), (0, yt + 11.3, 0)), S('gold', base=.58, up=.15, jit=.02))
    P.add(T(box((5.0, 2.4, 3.0), .2), (0, yt + 1.2, s - 3.2)), S('stone', base=.6, up=.1, jit=.02))
    P.gadd(T(disc(2.5, .5, 16, .1), (0, yt + 5.6, s - 1.8)), 'gold')
    for k in range(12):
        a = k * math.tau / 12; ca, sa = math.cos(a), math.sin(a)
        P.gadd(T(hull([Vector((ca * 2.7 - sa * .35, sa * 2.7 + ca * .35, 0)), Vector((ca * 2.7 + sa * .35, sa * 2.7 - ca * .35, 0)),
                       Vector((ca * 4.4, sa * 4.4, 0)), Vector((ca * 2.7, sa * 2.7, -.35))]), (0, yt + 5.6, s - 1.85)), 'gold')
    for k in range(12):
        a = rng.uniform(0, math.tau)
        x, z = math.cos(a) * (S0 + rng.uniform(2, 6)), math.sin(a) * (S0 + rng.uniform(2, 6))
        if z < -S0 + 2 and abs(x) < sw + 5: continue
        P.add(T(box((rng.uniform(1.6, 3.0), rng.uniform(1.0, 1.6), rng.uniform(1.4, 2.4)), .15), (x, .5, z), rng.uniform(0, 90), rng.uniform(-8, 8), rng.uniform(-8, 8)),
              S('stone', base=.55, up=.12, jit=.03))
    return P

# ------------------------------------------------------------------ city ruins
def pylon_gate():
    """processional pylon gateway: two battered towers built in courses (each course a frustum = visible joints),
    corner rolls + cornice, sun reliefs and chevron bands on the fronts, lintel with a winged gold sun disc; the east
    tower's top is broken away (fallen blocks at its foot). Opening 12 wide x 17 high. Front = -Z."""
    P = Prop('PylonGate'); rng = random.Random(5)
    gw = 6.0; Hh = 24.0; W0, D0, W1, D1 = 15.0, 9.0, 11.0, 6.6
    for sx in (-1, 1):
        cxx = sx * (gw + W0 / 2)
        top = Hh if sx < 0 else Hh - 5.5
        nc = 9; ch = top / nc
        for k in range(nc):
            t0, t1 = k * ch / Hh, (k + 1) * ch / Hh
            P.add(T(frustum(lerp(W0, W1, t0), lerp(D0, D1, t0), lerp(W0, W1, t1) + .02, lerp(D0, D1, t1) + .02, k * ch, (k + 1) * ch - .06), (cxx, 0, 0)),
                  S('stone', base=.56 + rng.uniform(-.05, .05), up=.1, jit=.02, seed=k + sx))
        if sx < 0:
            P.add(T(frustum(W1 + 1.0, D1 + 1.0, W1 + 2.6, D1 + 2.6, Hh, Hh + 1.6), (cxx, 0, 0)), S('stone', base=.66, up=.1, jit=.02))
            P.add(T(box((W1 + 2.8, .6, D1 + 2.8), .12), (cxx, Hh + 1.9, 0)), S('stone', base=.7, up=.1, jit=.02))
            P.add(T(box((W1 + 1.1, .16, D1 + 1.1)), (cxx, Hh - .1, 0)), S('gold', base=.6, jit=.01))
        else:
            for k in range(6):
                bx = cxx + rng.uniform(-W1 / 2 + 1.5, W1 / 2 - 1.5); bz = rng.uniform(-D1 / 2 + 1, D1 / 2 - 1)
                P.add(T(box((rng.uniform(1.8, 3.2), rng.uniform(.9, 1.5), rng.uniform(1.6, 2.6)), .15), (bx, top + .4, bz), rng.uniform(-20, 20), rng.uniform(-6, 6)),
                      S('stone', base=.55, up=.12, jit=.03))
            for k in range(5):
                P.add(T(box((rng.uniform(1.6, 2.8), rng.uniform(1.1, 1.8), rng.uniform(1.4, 2.4)), .18),
                        (cxx + rng.uniform(-6, 7), .4, rng.uniform(-D0 / 2 - 5, -D0 / 2 - 1.5)), rng.uniform(0, 90), rng.uniform(-12, 12), rng.uniform(-12, 12)),
                      S('stone', base=.52, up=.12, jit=.03))
        for cz in (-1, 1):
            for cx2 in (-1, 1):
                pts = [Vector((cxx + cx2 * lerp(W0, W1, t) / 2, t * Hh, cz * lerp(D0, D1, t) / 2)) for t in (0, top / Hh)]
                P.add(tube(pts, .45, sides=6), S('stone', base=.62, jit=.02))
        tilt = math.degrees(math.atan((D0 - D1) / 2 / Hh))
        for i, yy in enumerate((7.5, 15.0) if sx < 0 else (7.5, 13.5)):
            sun_relief(P, (cxx, yy, -lerp(D0, D1, yy / Hh) / 2 - .05), 2.6 if i == 0 else 2.0, 0.0, gold=(i == 0), pitch=-tilt)
        yb = 3.2
        zig_band(P, lerp(W0, W1, yb / Hh) - 3.0, (cxx, yb, -lerp(D0, D1, yb / Hh) / 2 - .05), 0.0, h=1.4)
    P.add(T(box((2 * gw + 3.0, 3.2, 5.2), .2), (0, 18.6, 0)), S('stone', base=.6, up=.12, jit=.02))
    P.add(T(box((2 * gw + 3.8, .9, 5.8), .15), (0, 20.6, 0)), S('stone', base=.68, up=.1, jit=.02))
    sun_relief(P, (0, 18.6, -2.65), 1.25, 0.0, gold=True)
    for sx in (-1, 1):
        for k in range(4):
            L = 4.6 - k * .75; y = 19.3 - k * .55
            pts = [Vector((sx * 1.4, y + .25, -2.62)), Vector((sx * 1.4, y - .25, -2.62)), Vector((sx * (1.4 + L), y + .05 - k * .15, -2.62)),
                   Vector((sx * 1.4, y + .2, -2.95)), Vector((sx * 1.4, y - .2, -2.95)), Vector((sx * (1.3 + L), y - k * .15, -2.75))]
            P.add(hull(pts), S('gold' if k == 0 else 'stone', base=.62 - k * .02, up=.1, jit=.02))
    P.add(T(box((2 * gw, .5, D0 + 1.0)), (0, .05, 0)), S('stone', base=.52, up=.1, jit=.02))
    return P

def ruin_wall(seed=1, L=16.0, H=7.0, door=False):
    """broken wall of real bevelled blocks with a ragged top; optional doorway with a lintel + small sun relief"""
    P = Prop('RuinWall%d' % seed); rng = random.Random(seed)
    ph = [rng.uniform(0, 6) for _ in range(2)]
    def prof(x):
        t = (x + L / 2) / L
        return H * (.35 + .65 * (.5 + .5 * math.sin(t * 3.1 + ph[0]))) * (.85 + .15 * math.sin(t * 9 + ph[1]))
    block_wall(P, L, H, 2.0, prof=(lambda x: max(prof(x), 6.0) if door and abs(x) < 3.2 else prof(x)), gap=(-1.8, 1.8, 5.0) if door else None, seed=seed)
    if door:
        P.add(T(box((5.4, .9, 2.3), .14), (0, 5.4, 0)), S('stone2', base=.62, up=.12, jit=.02))
        sun_relief(P, (0, 5.4, -1.2), .55, 0.0, col='stone2', depth=.2, rays=8)
    for k in range(int(L / 4)):
        P.add(T(box((rng.uniform(.8, 1.8), rng.uniform(.6, 1.1), rng.uniform(.8, 1.6)), .12), (rng.uniform(-L / 2, L / 2), .2, rng.choice((-1, 1)) * rng.uniform(1.8, 3.2)),
                rng.uniform(0, 90), rng.uniform(-15, 15), rng.uniform(-15, 15)), S('stone2', base=.55, up=.12, jit=.03))
    P.add(T(box((L + .4, .9, 2.6), .12), (0, -.1, 0)), S('stone2', base=.48, up=.1, jit=.02))
    return P

def ruin_house(seed=1):
    """corner of a roofless house: two block walls meeting at a pier, a doorway, a window, a fallen beam, a jar.
    14 x 11, front = -Z (door side)"""
    P = Prop('RuinHouse%d' % seed)
    pf = lambda L, H, k: (lambda x: H * (.55 + .45 * (.5 + .5 * math.sin((x + L / 2) / L * 2.6 + k))))
    tmp = Prop('t'); block_wall(tmp, 14.0, 8.0, 1.8, prof=lambda x: max(pf(14, 8, 1.3 + seed)(x), 6.4 if -4.8 < x < -.6 else 0), gap=(-4.2, -1.2, 5.0), seed=seed, z=-5.5)
    merge_into(P, tmp)
    tmp = Prop('t'); block_wall(tmp, 11.0, 8.0, 1.8, prof=lambda x: max(pf(11, 8, 2.5 + seed)(x), 7.0 if abs(x) < 1.8 else 0), gap=(-1.0, 1.0, 5.6), seed=seed + 5)
    tmp.add(T(box((3.8, .6, 2.2), .12), (0, 6.0, 0)), S('stone2', base=.62, up=.12, jit=.02))
    for f in range(len(tmp.solid.V)): pass
    merge_into(P, tmp, lambda v: Vector((7.0 - v.z, v.y, v.x)))
    for k in range(6):
        P.add(T(box((2.7 if k % 2 else 2.4, 1.42, 2.4 if k % 2 else 2.7), .16), (7.0, .71 + k * 1.44, -5.5), (k * 7) % 5 - 2), S('stone', base=.6 + (k % 2) * .05, up=.12, jit=.02))
    P.add(T(box((3.0, .5, 3.0), .12), (7.0, 8.9, -5.5)), S('stone', base=.68, up=.12, jit=.02))
    P.add(T(box((5.6, .8, 2.3), .12), (-2.7, 5.4, -5.5)), S('stone2', base=.62, up=.12, jit=.02))
    P.add(bar((-4.5, .2, 1.0), (5.0, 5.0, -4.2), .5, .5), S('wood', base=.38, jit=.02))
    P.add(T(lathe([(0, 0), (.5, 0), (.9, .6), (.8, 1.3), (.35, 1.6), (.42, 1.9), (0, 1.8)], n=10), (2.0, 0, -2.0)), S('red', base=.42, up=.12, jit=.02))
    P.add(grid_quad(-6.0, 6.4, -4.6, 5.0, .06, 6.0), S('stone2', base=.45, up=.05, jit=.04))
    return P

def ruin_arch(seed=1):
    """free-standing broken arch: block piers, round arch of voussoirs with a gold keystone, the right shoulder broken
    off (fallen voussoirs at the foot). Opening 8 wide. Front = -Z."""
    P = Prop('RuinArch%d' % seed); rng = random.Random(seed)
    hw, spring = 4.0, 8.0
    for sx in (-1, 1):
        x = sx * (hw + 1.5)
        for k in range(5):
            P.add(T(box((3.0 + rng.uniform(-.1, .1), 1.6, 3.0 + rng.uniform(-.1, .1)), .14), (x, k * 1.6 + .8, 0), rng.uniform(-2, 2)), S('stone', base=.56 + rng.uniform(-.06, .06), up=.12, jit=.02))
        P.add(T(box((3.6, .7, 3.6), .12), (x, spring + .35, 0)), S('stone', base=.66, up=.1, jit=.02))
    n = 11; R0, R1 = hw + .0, hw + 2.2
    for i in range(n):
        if i >= 8: continue
        a0, a1 = math.pi - i * math.pi / n, math.pi - (i + 1) * math.pi / n
        pts = [Vector((math.cos(a) * R, spring + .7 + math.sin(a) * R, zz)) for a in (a0 - .01, a1 + .01) for R in (R0, R1 + (.6 if i == n // 2 else 0)) for zz in (-1.4, 1.4)]
        P.add(hull(pts), S('gold' if i == n // 2 else 'stone', base=.58 + rng.uniform(-.05, .05), up=.12, jit=.02))
    for k in range(3):
        P.add(T(box((2.2, 1.4, 2.6), .15), (hw + 1.5 + rng.uniform(2.0, 4.5), .5, rng.uniform(-3, 3)), rng.uniform(0, 90), rng.uniform(-20, 20), rng.uniform(-20, 20)), S('stone', base=.55, up=.12, jit=.03))
    sun_relief(P, (-(hw + 1.5), 5.2, -1.55), .9, 0.0, rays=8)
    return P

def column_set(kind=0, seed=1):
    """kind 0 standing column, 1 broken column (jagged top), 2 broken stub + fallen drums + capital in the sand"""
    P = Prop('%s%d' % (('ColumnTall', 'ColumnBroken', 'ColumnFallen')[kind], seed)); rng = random.Random(seed)
    if kind == 0: column(P, (0, 0, 0), 15.0, 1.3, seed=seed)
    elif kind == 1: column(P, (0, 0, 0), 15.0, 1.3, broken=rng.uniform(4.5, 8.0), seed=seed)
    else:
        column(P, (0, 0, 0), 15.0, 1.3, broken=2.2, seed=seed)
        for k in range(3):
            d = T(lathe([(1.25, 0), (1.3, .1), (1.2, 2.3), (1.15, 2.4)], n=10), (0, 0, 0), 0, 0, 90)
            P.add(T(d, (3.4 + k * 2.6, 1.0, rng.uniform(-.6, .6) + k * .5), rng.uniform(-12, 12)), S('stone', base=.56, up=.12, jit=.03))
        P.add(T(lathe([(1.2, 0), (1.9, 1.1), (1.9, 1.5), (0, 1.5)], n=12), (-3.2, .6, 2.6), 30, 70, 0), S('stone', base=.6, up=.12, jit=.02))
    return P

# ------------------------------------------------------------------ obelisks
def _shaft(P, w0, w1, y0, y1, H, reliefs=True, col='stone', seed=0):
    """square tapered shaft (w0 at 0 .. w1 at H) cut at y0..y1, in drums, relief columns on all faces"""
    nsg = max(1, int((y1 - y0) / 4.5))
    for k in range(nsg):
        ya = lerp(y0, y1, k / nsg); yb = lerp(y0, y1, (k + 1) / nsg)
        wa, wb = lerp(w0, w1, ya / H), lerp(w0, w1, yb / H)
        P.add(frustum(wa, wa, wb, wb, ya, yb - .04), S(col, base=.58 + (k % 2) * .03, up=.1, jit=.02, seed=seed + k))
    if not reliefs: return
    for face in range(4):
        yy = y0 + 2.4; a = math.radians(face * 90)
        while yy < y1 - 1.5:
            w = lerp(w0, w1, yy / H); lz = -w / 2 - .02
            c = (math.sin(a) * lz, yy, math.cos(a) * lz); yawf = face * 90.0
            kind = int(round(yy / 3.1)) % 3
            if kind == 0: sun_relief(P, c, w * .3, yawf, depth=.15, rays=8)
            elif kind == 1:
                P.add(T(disc(w * .14, .14, 8, .03), c, yawf), S('gold', base=.6, jit=.02))
                for dx in (-1, 1):
                    P.add(T(T(disc(w * .08, .12, 6, .02), (dx * w * .28, 0, 0)), c, yawf), S(col, base=.62, jit=.02))
            else:
                pts = [Vector((-w * .3, -.3, -.1)), Vector((0, .3, -.1)), Vector((w * .3, -.3, -.1))]
                P.add(T(tube(pts, .12, sides=4), c, yawf), S(col, base=.64, jit=.02))
            yy += 3.1

def obelisk(seed=1, H=26.0):
    """standing obelisk on the stepped plinth: drummed tapered shaft, relief columns on four faces, gold pyramidion"""
    P = Prop('Obelisk%d' % seed); plinth(P, 7.0, 7.0, 1.6, 2)
    tmp = Prop('t'); _shaft(tmp, 3.6, 2.4, 0, H, H, seed=seed)
    merge_into(P, tmp, lambda v: v + Vector((0, 1.6, 0)))
    P.add(T(frustum(2.5, 2.5, .05, .05, 0, 2.8), (0, H + 1.6, 0)), S('gold', base=.62, up=.15, jit=.02))
    P.add(T(box((2.7, .25, 2.7)), (0, H + 1.55, 0)), S('gold', base=.55, jit=.01))
    return P

def obelisk_fallen(seed=1, part='top', H=26.0):
    """toppled obelisk piece lying on its side along x: 'top' (with pyramidion) or 'mid', jagged break ends"""
    P = Prop('ObeliskFallen%s%d' % (part.capitalize(), seed)); rng = random.Random(seed)
    w0, w1 = 3.6, 2.4
    y0, y1 = (14.0, H) if part == 'top' else (5.0, 13.5)
    tmp = Prop('t'); _shaft(tmp, w0, w1, y0, y1, H, seed=seed)
    def brk(y, w, sgn):
        pts = [Vector((sx * w / 2, y + rng.uniform(-.1, .1), sz * w / 2)) for sx in (-1, 1) for sz in (-1, 1)]
        pts += [Vector((rng.uniform(-.4, .4) * w, y + sgn * rng.uniform(.3, 1.1), rng.uniform(-.4, .4) * w)) for _ in range(6)]
        return hull(pts)
    tmp.add(brk(y0, lerp(w0, w1, y0 / H), -1), S('stone', base=.72, up=.1, jit=.05))
    if part == 'top': tmp.add(T(frustum(w1 + .1, w1 + .1, .05, .05, 0, 2.8), (0, H, 0)), S('gold', base=.6, up=.15, jit=.02))
    else: tmp.add(brk(y1, lerp(w0, w1, y1 / H), 1), S('stone', base=.72, up=.1, jit=.05))
    L0 = (y0 + y1) / 2; R = Matrix.Rotation(math.radians(rng.uniform(-10, 10)), 3, 'X') @ Matrix.Rotation(math.radians(-88), 3, 'Z')
    merge_into(P, tmp, lambda v: R @ (v - Vector((0, L0, 0))) + Vector((0, w0 * .22, 0)))
    return P

def obelisk_stump(seed=1):
    P = Prop('ObeliskStump%d' % seed); rng = random.Random(seed); plinth(P, 7.0, 7.0, 1.6, 2)
    tmp = Prop('t'); _shaft(tmp, 3.6, 2.4, 0, 4.0, 26.0, reliefs=False, seed=seed)
    merge_into(P, tmp, lambda v: v + Vector((0, 1.6, 0)))
    pts = [Vector((sx * 1.7, 5.4, sz * 1.7)) for sx in (-1, 1) for sz in (-1, 1)]
    pts += [Vector((sx * 1.7, 5.6 + .45 * (sx + sz) + rng.uniform(-.15, .15), sz * 1.7)) for sx in (-1, 1) for sz in (-1, 1)]
    pts += [Vector((rng.uniform(-1.2, 1.2), 0, rng.uniform(-1.2, 1.2))) for _ in range(5)]
    pts = pts[:8] + [Vector((p.x, 5.6 + .45 * (p.x + p.z) / 1.7 + rng.uniform(-.1, .3), p.z)) for p in pts[8:]]
    P.add(hull(pts), S('stone', base=.72, up=.1, jit=.05))
    sun_relief(P, (0, 3.6, -1.72), .9, 0.0, depth=.15, rays=8)
    for k in range(4):
        P.add(T(box((rng.uniform(.8, 1.5), rng.uniform(.6, 1.0), rng.uniform(.8, 1.4)), .1), (rng.uniform(-6, 6), .2, rng.uniform(4.6, 6.5) * rng.choice((-1, 1))), rng.uniform(0, 90), rng.uniform(-15, 15)),
              S('stone', base=.55, up=.12, jit=.03))
    return P

# ------------------------------------------------------------------ path markers + stations
def waystone(seed=1):
    """path marker: weathered standing stone with a carved sun disc on its front, a gold cap, and a small cairn"""
    P = Prop('Waystone%d' % seed); rng = random.Random(seed)
    pts = [Vector((sx * w * rng.uniform(.9, 1.05), y + rng.uniform(-.08, .08), sz * d * rng.uniform(.9, 1.05)))
           for y, w, d in ((-.6, 1.25, .8), (1.0, 1.2, .75), (2.6, 1.0, .65), (3.6, .8, .5), (4.1, .38, .3)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    P.add(hull(pts), S('stone', base=.56, up=.14, jit=.04, seed=seed))
    sun_relief(P, (0, 2.5, -.74), .58, 0.0, depth=.16, rays=8, gold=(seed % 2 == 0), pitch=-4)
    P.add(T(frustum(.72, .58, .1, .1, 0, .7), (0, 4.0, 0)), S('gold', base=.6, up=.15, jit=.02))
    for k in range(3):
        P.add(T(blob(.55 - k * .1, seed * 5 + k, n=12, sq=.45), (1.55, .05 + k * .32, .4)), S('stone2', base=.55, up=.15, jit=.04))
    P.add(T(blob(.45, seed + 9, n=10, sq=.5), (-1.25, .0, .6)), S('stone2', base=.5, up=.15, jit=.04))
    return P

def spawn_dais():
    """spawn: round three-step sandstone dais (r 13.4) with a gold sun mosaic (disc, 16 rays, indigo ring inlay) and four
    gold-capped short obelisk posts on the diagonals"""
    P = Prop('SpawnDais')
    for k, (r, y1) in enumerate(((13.4, .5), (12.4, 1.0), (11.4, 1.5))):
        P.add(lathe([(r, -.6), (r, y1 - .12), (r - .12, y1), (0, y1)], n=40), S('stone', base=.55 + k * .03, up=.12, jit=.01))
    y = 1.5
    P.add(lathe([(10.4, y), (10.4, y + .06), (9.6, y + .06), (9.6, y)], n=40), S('indigo', base=.55, jit=.01))
    P.add(cyl(3.0, .1, 24, y0=y), S('gold', base=.62, jit=.01))
    for k in range(16):
        a = k * math.tau / 16; L = 9.0 if k % 2 == 0 else 7.0; ca, sa = math.cos(a), math.sin(a); w = .55
        bm = bmesh.new(); vs = [bm.verts.new((px, y + .02, pz)) for px, pz in ((ca * 3.2 - sa * w, sa * 3.2 + ca * w), (ca * L, sa * L), (ca * 3.2 + sa * w, sa * 3.2 - ca * w))]
        f = bm.faces.new(vs); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=-.08)
        P.add(bm, S('gold', base=.6 + (k % 2) * .05, jit=.01))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2; x, z = math.cos(a) * 10.4, math.sin(a) * 10.4
        P.add(T(box((1.6, .5, 1.6), .1), (x, y + .25, z)), S('stone', base=.6, up=.1, jit=.02))
        P.add(T(frustum(1.15, 1.15, .75, .75, 0, 4.2), (x, y + .5, z)), S('stone', base=.6, up=.1, jit=.02))
        P.add(T(frustum(.8, .8, .05, .05, 0, .9), (x, y + 4.7, z)), S('gold', base=.62, up=.15, jit=.02))
        P.add(T(disc(.3, .1, 8, .02), (x - math.cos(a) * .5, y + 2.6, z - math.sin(a) * .5), math.degrees(math.atan2(math.cos(a), math.sin(a)))), S('gold', base=.6, jit=.02))
    return P

def quest_stele():
    """QUEST stand: tall carved tablet on the plinth with three BLANK recessed panels (quest GUIs), sun crest, brass oil
    lamps on posts, an offering table with scroll baskets"""
    P = Prop('QuestStele'); rng = random.Random(1)
    plinth(P, 9.0, 4.0, 1.2, 2)
    y = 1.2
    P.add(T(frustum(7.4, 1.8, 6.6, 1.4, 0, 8.0), (0, y, 0)), S('stone', base=.58, up=.1, jit=.02))
    P.add(T(box((7.6, .7, 2.0), .12), (0, y + 8.3, 0)), S('stone', base=.66, up=.1, jit=.02))
    pts = [Vector((x, y + 8.6, z)) for x in (-3.4, 3.4) for z in (-.8, .8)] + [Vector((0, y + 10.6, z)) for z in (-.7, .7)]
    P.add(hull(pts), S('stone', base=.62, up=.1, jit=.02))
    sun_relief(P, (0, y + 9.3, -.86), .9, 0.0, gold=True, rays=12, pitch=-20)
    for py, ph in ((y + 6.0, 2.0), (y + 3.6, 1.8), (y + 1.4, 1.6)):
        P.add(T(box((5.6, ph, .2)), (0, py, -.82)), S('stone', base=.74, jit=.01))
        for sy in (-1, 1): P.add(T(box((5.9, .16, .3)), (0, py + sy * ph / 2, -.88)), S('gold', base=.58, jit=.01))
    for sx in (-1, 1):
        x = sx * 5.6
        P.add(T(cyl(.16, 5.4, 6), (x, -.3, -1.6)), S('wood', base=.4, jit=.02))
        P.add(T(lathe([(.1, 0), (.55, .25), (.5, .5), (.2, .6), (0, .6)], n=8), (x, 5.1, -1.6)), S('gold', base=.55, up=.15, jit=.02))
        P.gadd(T(lathe([(.2, 0), (.15, .5), (0, .75)], n=6), (x, 5.65, -1.6)), 'fire')
    P.add(T(box((4.0, .35, 1.6), .08), (0, 1.8, -3.2)), S('wood', base=.45, up=.1, jit=.02))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(T(box((.25, 1.8, .25)), (sx * 1.7, .7, -3.2 + sz * .6)), S('wood', base=.38, jit=.02))
    for k in range(2):
        x = -1.0 + k * 2.0
        P.add(T(lathe([(.3, 0), (.6, .1), (.65, .6), (0, .6)], n=10), (x, 1.98, -3.2)), S('saffron', base=.5, up=.1, jit=.02))
        for j in range(3):
            P.add(T(T(cyl(.12, .9, 6), (0, 0, 0), 0, 0, 90), (x + rng.uniform(-.2, .2), 2.5 + j * .1, -3.2 + rng.uniform(-.2, .2)), rng.uniform(0, 180)), S('cloth', base=.6, jit=.02))
    return P

def sun_astrolabe():
    """UPGRADE station: octagonal stepped plinth, carved pedestal with gold claws holding a brass armillary of three
    tilted gold rings round a glowing sun orb, two stone work tables with ingots and a rod"""
    P = Prop('SunAstrolabe'); rng = random.Random(4)
    for k, (r, y1) in enumerate(((8.0, .6), (7.0, 1.2))):
        P.add(cyl(r, y1 + .6, 8, .12, y0=-.6, rot0=math.pi / 8), S('stone', base=.55 + k * .03, up=.12, jit=.01))
    P.add(T(torus(6.55, .1, 8, 4), (0, 1.2, 0)), S('gold', base=.6, jit=.01))
    y = 1.2
    P.add(T(lathe([(1.8, 0), (1.8, .5), (1.3, .7), (1.0, 1.0), (.9, 4.2), (1.3, 4.6), (1.6, 5.2), (0, 5.2)], n=12), (0, y, 0)), S('stone', base=.6, up=.12, jit=.02))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        pts = [Vector((math.cos(a) * r, y + yy, math.sin(a) * r)) for r, yy in ((1.4, 5.0), (2.2, 6.2), (2.0, 7.4), (1.5, 8.0))]
        P.add(tube(pts, [.24, .2, .14, .08], sides=6), S('gold', base=.55, jit=.02))
    c = (0, y + 9.4, 0)
    for i, (rx, ry, R) in enumerate(((0, 0, 3.4), (65, 20, 3.0), (-50, 70, 2.6))):
        P.add(T(T(torus(R, .18, 28, 5), (0, 0, 0), ry, rx), c), S('gold', base=.6 + i * .04, up=.1, jit=.02))
    for k in range(12):
        a = k * math.tau / 12
        P.add(T(box((.14, .5, .14)), (math.cos(a) * 3.4, c[1], math.sin(a) * 3.4)), S('gold', base=.5, jit=.02))
    P.add(T(tube([Vector((0, -3.7, 0)), Vector((0, 3.7, 0))], .1, sides=6), c, 0, 23), S('gold', base=.55, jit=.02))
    P.gadd(T(blob(1.1, 3, n=26, sq=1.0), c), 'gold')
    for sx in (-1, 1):
        x = sx * 4.6
        P.add(T(box((1.0, 1.5, 3.4), .12), (x, y + .75, 1.6)), S('stone2', base=.55, up=.12, jit=.02))
        P.add(T(box((1.8, .4, 4.2), .1), (x, y + 1.7, 1.6)), S('stone', base=.64, up=.12, jit=.02))
        for j in range(3):
            P.add(T(frustum(.7, .35, .55, .25, 0, .25), (x + rng.uniform(-.3, .3), y + 1.9 + j * .25, 1.6 + rng.uniform(-.3, .3)), rng.uniform(0, 40)), S('gold', base=.62, up=.15, jit=.02))
        P.add(bar((x - .4, y + 2.0, .2), (x + .3, y + 2.1, 2.8), .12, .12), S('wood', base=.4, jit=.02))
    sun_relief(P, (0, y + 2.3, -1.12), .75, 0.0, gold=True, rays=12, pitch=-6)
    return P

# ================================================================== batch 3: caravan camp, oasis, treasure, nature,
# the sand-wyrm skeleton, the colossus head and the sunken temple (appended to dune_props.py)

def uvsphere(r, seg=16, rings=10, c=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(r), verts=bm.verts); bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bm

def sheet(P, fn, nx, nzz, col, col2=None, stripes=0, th=.1, base=.55):
    """a cloth sheet over a parametric surface fn(u, v) -> Vector (u, v in 0..1), solidified, optional stripe bands
    across u (col / col2 alternating)"""
    bm = bmesh.new(); Vv = {}
    for i in range(nx + 1):
        for j in range(nzz + 1): Vv[i, j] = bm.verts.new(fn(i / nx, j / nzz))
    for i in range(nx):
        for j in range(nzz):
            f = bm.faces.new((Vv[i, j], Vv[i + 1, j], Vv[i + 1, j + 1], Vv[i, j + 1]))
            f.material_index = ((i * stripes) // nx) % 2 if stripes else 0
    bm.normal_update()
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=th)
    u1, u2 = PAL.u(col), PAL.u(col2 or col)
    def sh(f):
        c = f.calc_center_median()
        v = base + .18 * abs(f.normal.y) + (nz(c.x, c.y, c.z, 3, 7) - .5) * .08
        return [(u2 if f.material_index else u1, clamp(v, .04, .96))] * len(f.loops)
    P.add(bm, sh)

def peg_rope(P, a, b):
    P.add(tube(sag(a, b, .25, 5), .05, sides=3), S('cloth', base=.4, jit=.01))
    P.add(T(cyl(.09, .9, 4), (b[0], b[1] - .6, b[2])), S('wood', base=.35, jit=.01))

def crate(P, c, s=1.4, yaw=0.0, seed=0):
    """plank crate: bevelled body with plank grooves (thin proud boards), corner straps, gold-studded"""
    x, y, z = c; rng = random.Random(seed)
    P.add(T(box((s, s * .8, s), .06), (x, y + s * .4, z), yaw), S('wood', base=.5 + rng.uniform(-.06, .06), up=.12, jit=.03))
    for k in (-1, 1):
        P.add(T(T(box((s + .06, .12, s + .06)), (0, s * .4 + k * s * .26, 0)), (x, y, z), yaw), S('wood', base=.32, jit=.02))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(T(box((.1, s * .82, .1)), (sx * s / 2, s * .4, sz * s / 2)), (x, y, z), yaw), S('gold', base=.42, jit=.02))

def sack(P, c, r=.7, col='cloth', seed=0, yaw=0.0):
    x, y, z = c
    P.add(T(uvsphere((r, r * 1.05, r * .9), 10, 7, (0, r * .95, 0)), (x, y, z), yaw), V(col, y, y + 2 * r, .38, .7, ns=1.0, seed=seed, amp=.06), smooth=True)
    P.add(T(lathe([(r * .25, 0), (r * .18, r * .25), (r * .32, r * .5), (0, r * .52)], n=6), (x, y + r * 1.85, z)), S(col, base=.5, jit=.02))
    P.add(T(torus(r * .2, .05, 6, 3), (x, y + r * 1.95, z)), S('rope' if False else 'wood', base=.45, jit=.01))

def rolled_rug(P, a, b, r=.35, col='red', col2='indigo'):
    a, b = Vector(a), Vector(b)
    P.add(tube([a, b], r, sides=8), S(col, base=.5, up=.15, jit=.02))
    for t in (.2, .8): P.add(tube([a.lerp(b, t - .04), a.lerp(b, t + .04)], r * 1.04, sides=8), S(col2, base=.5, jit=.02))

def jar(P, c, h=1.5, r=.55, col='stone2', band='indigo', seed=0):
    x, y, z = c
    P.add(T(lathe([(0, 0), (r * .5, 0), (r, h * .35), (r * .9, h * .7), (r * .35, h * .85), (r * .42, h), (r * .3, h), (0, h * .9)], n=10), (x, y, z)), S(col, base=.52, up=.12, jit=.02, seed=seed))
    P.add(T(torus(r * .98, .05, 10, 3), (x, y + h * .5, z)), S(band, base=.5, jit=.01))

def trader_tent():
    """SHOP: caravan trader's tent: 6 poles, a long low roof of indigo + cream bands stretched between pole peaks with
    sags, a back wall and side curtains, an awning on two raking poles in front, guy ropes to pegs, a plank counter
    with goods (jars, cloth bolts, crates, coins, a brass scale), rugs inside and two hanging lamps. 14 x 10, front -Z"""
    P = Prop('TraderTent'); rng = random.Random(11)
    W, D = 14.0, 10.0; poles = [(-6.6, -5.0, 8.4), (0, -5.0, 9.6), (6.6, -5.0, 8.4), (-6.6, 5.0, 6.6), (0, 5.0, 7.8), (6.6, 5.0, 6.6)]
    for x, z, h in poles:
        P.add(T(cyl(.2, h + .6, 6, .04), (x, -.6, z)), S('wood', base=.42, jit=.02))
        P.add(T(lathe([(.25, 0), (.2, .25), (.05, .35), (0, .35)], n=6), (x, h, z)), S('gold', base=.6, jit=.02))
    def roof(u, v):
        x = lerp(-W / 2 - .4, W / 2 + .4, u); z = lerp(-D / 2 - .3, D / 2 + .3, v)
        yf = 8.4 + 1.2 * math.exp(-(x / 2.6) ** 2); yb = 6.6 + 1.2 * math.exp(-(x / 2.6) ** 2)
        y = lerp(yf, yb, v) - .55 * math.sin(v * math.pi) - .35 * abs(math.sin(x / 6.6 * math.pi)) * 1.0
        return Vector((x, y + .05, z))
    sheet(P, roof, 16, 8, 'indigo', 'cloth', stripes=8)
    sheet(P, lambda u, v: Vector((lerp(-W / 2, W / 2, u), lerp(.4, roof(u, 1).y - .1, v) - .25 * math.sin(u * math.pi * 4) * (1 - v), D / 2 + .25 + .2 * math.sin(u * 20))), 12, 3, 'cloth', 'red', stripes=6)
    for sx in (-1, 1):
        sheet(P, lambda u, v, sx=sx: Vector((sx * (W / 2 + .2), lerp(.4, lerp(8.2, 6.4, u) - .3, v), lerp(D / 2, -D / 2 + 3.2, u * (1 - .35 * v)))), 6, 3, 'indigo', 'cloth', stripes=3)
    def awn(u, v):
        x = lerp(-5.0, 5.0, u); z = lerp(-5.2, -8.4, v)
        return Vector((x, lerp(8.6 + .9 * math.exp(-(x / 2.4) ** 2), 6.8, v) - .3 * math.sin(u * math.pi) * math.sin(v * math.pi), z))
    sheet(P, awn, 8, 3, 'saffron', 'cloth', stripes=6)
    for sx in (-1, 1):
        P.add(tube([Vector((sx * 5.0, -.4, -9.4)), Vector((sx * 5.0, 6.9, -8.4))], .16, sides=6), S('wood', base=.42, jit=.02))
        peg_rope(P, (sx * 5.0, 6.8, -8.4), (sx * 6.2, .3, -11.6))
    for x, z, h in poles:
        if z > 0: peg_rope(P, (x, h - .4, z), (x * 1.15, .3, z + 3.2))
        elif abs(x) > 1: peg_rope(P, (x, h - .4, z), (x + math.copysign(3.0, x), .3, z - 1.5))
    # counter + goods
    P.add(T(box((10.0, .3, 1.6), .06), (0, 2.6, -3.6)), S('wood', base=.55, up=.12, jit=.02))
    P.add(T(box((10.0, 2.4, .2), .04), (0, 1.25, -4.25)), S('wood', base=.42, jit=.02))
    for k in range(6): P.add(T(box((.16, 2.4, .26)), (-4.8 + k * 1.92, 1.25, -4.4)), S('wood', base=.3, jit=.01))
    sun_relief(P, (0, 1.3, -4.5), .7, 0.0, col='gold', depth=.12, rays=8, gold=True)
    for k, x in enumerate((-4.0, -3.0, -2.2)): jar(P, (x, 2.75, -3.6), 1.1 + .2 * k, .38, ('stone2', 'stone', 'gold')[k], ('indigo', 'red', 'saffron')[k], k)
    for k in range(3):
        rolled_rug(P, (-.8 + k * .3, 2.95 + k * .02 + (.4 if k == 1 else 0), -4.1), (-.8 + k * .3 + .1, 2.95 + (.4 if k == 1 else 0), -3.1), .22, ('red', 'saffron', 'indigo')[k], 'cloth')
    P.add(T(lathe([(.5, 0), (.6, .15), (0, .15)], n=10), (2.0, 2.75, -3.6)), S('gold', base=.6, jit=.02))
    for k in range(6): P.add(T(cyl(.16, .05, 8), (2.0 + rng.uniform(-.25, .25), 2.92 + k * .05, -3.6 + rng.uniform(-.25, .25))), S('gold', base=.7, jit=.02))
    P.add(T(cyl(.06, 1.3, 4), (3.6, 2.75, -3.5)), S('gold', base=.5, jit=.01))
    P.add(bar((2.7, 4.0, -3.5), (4.5, 4.0, -3.5), .08, .08), S('gold', base=.55, jit=.01))
    for sx in (-1, 1):
        P.add(tube(sag((3.6 + sx * .9, 4.0, -3.5), (3.6 + sx * .9, 3.4, -3.5), 0, 2), .02, sides=3), S('gold', base=.4, jit=.01))
        P.add(T(lathe([(.35, 0), (.4, .08), (0, .1)], n=8), (3.6 + sx * .9, 3.3, -3.5)), S('gold', base=.6, jit=.02))
    crate(P, (5.6, 0, -2.8), 1.5, 15, 1); crate(P, (5.4, 1.2, -2.9), 1.0, -10, 2)
    sack(P, (-5.6, 0, -2.6), .65, 'saffron', 1); sack(P, (-5.2, 0, -1.4), .55, 'cloth', 2)
    # rugs on the floor inside
    for (x, z, w, d, c1, c2) in ((-2.5, 1.0, 6.0, 4.0, 'red', 'saffron'), (3.0, 1.6, 5.0, 3.6, 'indigo', 'cloth')):
        P.add(T(box((w, .08, d)), (x, .05, z)), S(c1, base=.5, jit=.01))
        P.add(T(box((w - .8, .1, d - .8)), (x, .07, z)), S(c2, base=.55, jit=.01))
        P.add(T(box((w - 1.6, .12, d - 1.6)), (x, .08, z)), S(c1, base=.45, jit=.01))
    for x in (-3.5, 3.5):
        P.add(tube([Vector((x, 8.3, -1.0)), Vector((x, 6.6, -1.0))], .03, sides=3), S('gold', base=.4, jit=.01))
        P.add(T(lathe([(0, 0), (.35, .2), (.45, .55), (.3, .85), (.05, 1.0), (0, 1.0)], n=8), (x, 5.6, -1.0)), S('gold', base=.55, up=.12, jit=.02))
        P.gadd(T(uvsphere((.28, .32, .28), 8, 6), (x, 6.05, -1.0)), 'lamp')
    return P

def sleep_tent(seed=1, col='red', col2='cloth'):
    """A-frame nomad tent: ridge pole on two forked posts, two cloth slopes with sag + stripes, a closed back gable,
    the front flaps tied back, guy ropes to pegs, a bedroll and a saddle bag inside. 6 x 8, front -Z"""
    P = Prop('SleepTent%d' % seed); rng = random.Random(seed)
    Hh, Wd, L = 4.6, 3.3, 8.0
    for z in (-L / 2, L / 2):
        P.add(T(cyl(.14, Hh + .5, 6), (0, -.5, z)), S('wood', base=.42, jit=.02))
        for sx in (-1, 1): P.add(tube([Vector((0, Hh - .2, z)), Vector((sx * .5, Hh + .5, z))], .07, sides=4), S('wood', base=.4, jit=.02))
    P.add(tube([Vector((0, Hh + .05, -L / 2 - .5)), Vector((0, Hh + .05, L / 2 + .5))], .12, sides=6), S('wood', base=.45, jit=.02))
    for sx in (-1, 1):
        sheet(P, lambda u, v, sx=sx: Vector((sx * lerp(.05, Wd + .2, v), lerp(Hh + .12, .05, v) - .25 * math.sin(v * math.pi) * math.sin(u * math.pi), lerp(-L / 2 - .2, L / 2 + .2, u))),
              6, 3, col, col2, stripes=5)
    sheet(P, lambda u, v: Vector((lerp(-Wd, Wd, u) * (1 - v), lerp(.05, Hh, v), L / 2 + .15)), 4, 2, col2)
    for sx in (-1, 1):                                                   # front flaps tied back
        sheet(P, lambda u, v, sx=sx: Vector((sx * lerp(Wd * .55 * (1 - v) + .2, Wd * (1 - v) + .4, u), lerp(.1, Hh - .1, v), -L / 2 - .1 - .4 * u * (1 - v))), 2, 3, col2, th=.08)
        P.add(T(torus(.35, .07, 8, 3), (sx * (Wd * .6), 1.8, -L / 2 - .3), 0, 90), S('wood', base=.5, jit=.01))
        peg_rope(P, (0, Hh, sx * (L / 2 + .3)), (0, .3, sx * (L / 2 + 3.0)))
        for z in (-2.5, 2.5): peg_rope(P, (sx * (Wd + .1), .4, z), (sx * (Wd + 1.4), .25, z))
    P.add(T(box((1.4, .3, 3.6), .12), (-1.1, .15, .5)), S('saffron', base=.5, up=.1, jit=.02))
    rolled_rug(P, (-1.7, .5, -1.3), (-.5, .5, -1.3), .3, 'indigo', 'cloth')
    P.add(T(box((1.0, .8, .6), .2), (1.5, .4, 1.8), 20), S('red', base=.45, up=.12, jit=.02))
    return P

def camel(pose='stand', seed=1, saddle='red'):
    """stylised camel (smooth hide): ellipsoid body + single hump, S-curved neck, long head with a soft muzzle, ears,
    jointed legs (knees, wide foot pads) or legs folded under ('kneel'), tasselled saddle blanket + two saddle bags"""
    P = Prop('Camel%s%d' % (pose.capitalize(), seed)); rng = random.Random(seed)
    kneel = pose == 'kneel'
    by = 2.4 if kneel else 6.2
    hide = V('camel', by - 2, by + 3.5, .38, .72, nk=.18, ns=2.0, seed=seed, amp=.05)
    P.add(uvsphere((1.55, 1.45, 3.1), 18, 12, (0, by, .1)), hide, smooth=True)
    P.add(uvsphere((1.15, 1.25, 1.6), 14, 9, (0, by + 1.15, .45)), hide, smooth=True)
    P.add(uvsphere((1.25, 1.2, 1.4), 12, 8, (0, by - .1, 1.9)), hide, smooth=True)
    neck = [Vector(p) for p in ((0, by + .3, -2.5), (0, by - .1, -3.7), (0, by + .9, -4.7), (0, by + 2.5, -5.1), (0, by + 3.1, -5.2))]
    P.add(tube(neck, [.85, .7, .55, .48, .45], sides=10), hide, smooth=True)
    hy = by + 3.3
    P.add(uvsphere((.52, .55, .95), 12, 8, (0, hy, -5.75)), hide, smooth=True)
    P.add(uvsphere((.44, .42, .62), 10, 7, (0, hy - .3, -6.55)), V('camel', hy - .8, hy, .3, .55, nk=.15), smooth=True)
    for sx in (-1, 1):
        P.add(T(uvsphere((.12, .25, .1), 6, 5), (sx * .38, hy + .5, -5.4), 0, 0, sx * -25), hide, smooth=True)
        P.add(uvsphere((.09, .07, .09), 6, 4, (sx * .36, hy + .12, -5.95)), S('wood', base=.15, jit=.01), smooth=True)
    P.add(tube([Vector((0, by + .3, 3.1)), Vector((0, by - .6, 3.5)), Vector((0, by - 1.4, 3.55))], [.16, .12, .08], sides=5), hide)
    P.add(T(uvsphere((.18, .3, .18), 6, 5), (0, by - 1.6, 3.55)), S('wood', base=.3, jit=.02), smooth=True)
    leg = V('camel', 0, by, .32, .6, nk=.12)
    for sx in (-1, 1):
        for sz, kz in ((-1, -2.0), (1, 2.2)):
            if kneel:
                if sz < 0: pts = [Vector((sx * 1.0, by - .6, -2.0)), Vector((sx * 1.05, .5, -2.9)), Vector((sx * .7, .38, -1.4))]
                else: pts = [Vector((sx * 1.2, by - .3, 2.0)), Vector((sx * 1.65, .55, .5)), Vector((sx * 1.45, .38, 2.7))]
                P.add(tube(pts, [.62, .36, .28], sides=8), leg, smooth=True)
                P.add(uvsphere((.38, .34, .4), 8, 5, tuple(pts[1])), S('camel', base=.32, jit=.02), smooth=True)
                P.add(uvsphere((.4, .22, .5), 8, 5, tuple(pts[2])), S('camel', base=.28, jit=.02), smooth=True)
            else:
                knee = Vector((sx * .85, 2.9 + (.2 if sz > 0 else 0), kz + (.15 if sz < 0 else -.35)))
                pts = [Vector((sx * .9, by - .6, kz)), Vector((sx * .88, 4.2, kz + (0 if sz < 0 else -.15))), knee, Vector((sx * .85, .55, kz)), Vector((sx * .85, .2, kz - .05))]
                P.add(tube(pts, [.72, .48, .3, .24, .27], sides=8), leg, smooth=True)
                P.add(uvsphere((.31, .3, .31), 8, 5, tuple(knee)), S('camel', base=.35, jit=.02), smooth=True)
                P.add(T(lathe([(.42, 0), (.45, .12), (.3, .3), (0, .3)], n=8), (sx * .85, -.05, kz - .1)), S('camel', base=.28, jit=.02))
    # saddle blanket (draped over the hump) + bags + rope girth
    def blanket(u, v):
        a = lerp(-1.25, 1.25, u); z = lerp(-1.3, 2.2, v)
        r = 1.62
        return Vector((math.sin(a) * r * 1.02, by + .15 + math.cos(a) * r * .95 + .95 * math.exp(-((z - .45) / 1.2) ** 2) * math.cos(a) ** 2, z))
    sheet(P, blanket, 8, 5, saddle, 'saffron', stripes=4, th=.08)
    for sx in (-1, 1):
        P.add(T(box((.6, 1.1, 1.3), .22), (sx * 1.85, by - .6, .2), 0, 0, sx * 8), S('indigo' if saddle == 'red' else 'red', base=.48, up=.12, jit=.02))
        for k in range(3):
            P.add(tube([Vector((sx * 1.5, by - 1.1, -1.0 + k * 1.4)), Vector((sx * 1.5, by - 1.6, -1.0 + k * 1.4))], .06, sides=4), S('saffron', base=.6, jit=.02))
    P.add(T(torus(1.62, .09, 18, 4, ), (0, by - .1, -.8), 0, 90), S('wood', base=.45, jit=.01))
    return P

def rug_spread(seed=1):
    """rest corner: a big patterned rug (border, field, medallion), three cushions, a brass tray with a teapot and cups"""
    P = Prop('RugSpread%d' % seed)
    for (w, d, c, y) in ((6.0, 4.4, 'red', .03), (5.2, 3.6, 'saffron', .05), (4.6, 3.0, 'red', .07), (2.0, 1.4, 'indigo', .09)):
        P.add(T(box((w, .06, d)), (0, y, 0)), S(c, base=.5, jit=.01))
    for k in range(10):
        for sz in (-1, 1): P.add(T(box((.06, .04, .3)), (-2.7 + k * .6, .03, sz * 2.35)), S('cloth', base=.7, jit=.01))
    for k, (x, z, c) in enumerate(((-2.0, 1.4, 'indigo'), (0, 1.7, 'saffron'), (2.0, 1.4, 'indigo'))):
        P.add(uvsphere((.85, .38, .55), 10, 6, (x, .38, z)), V(c, 0, .8, .35, .7, nk=.2), smooth=True)
    P.add(T(lathe([(0, 0), (.9, 0), (1.0, .08), (0, .08)], n=14), (0, .1, -.3)), S('gold', base=.62, jit=.01))
    P.add(T(lathe([(0, 0), (.3, 0), (.38, .3), (.25, .5), (.1, .55), (.12, .7), (0, .72)], n=10), (0, .18, -.3)), S('gold', base=.55, up=.15, jit=.02))
    P.add(tube([Vector((.35, .4, -.3)), Vector((.6, .55, -.3)), Vector((.72, .62, -.3))], .04, sides=4), S('gold', base=.5, jit=.01))
    for k in range(3):
        a = k * 2.1 + .5
        P.add(T(lathe([(0, 0), (.1, 0), (.13, .16), (0, .16)], n=6), (math.cos(a) * .6, .18, -.3 + math.sin(a) * .6)), S('gold', base=.6, jit=.02))
    return P

def campfire():
    """stone ring, crossed logs, flame glow, a three-legged tripod with a hanging pot, a log bench"""
    P = Prop('Campfire'); rng = random.Random(4)
    for k in range(9):
        a = k * math.tau / 9
        P.add(T(blob(.42, k, n=12, sq=.6), (math.cos(a) * 1.2, .05, math.sin(a) * 1.2)), S('stone2', base=.45, up=.2, jit=.04))
    for k in range(3):
        a = k * math.pi / 3
        P.add(tube([Vector((math.cos(a) * -.9, .15, math.sin(a) * -.9)), Vector((math.cos(a) * .9, .35, math.sin(a) * .9))], .14, sides=6), S('wood', base=.25, jit=.03))
    for k in range(4):
        a = k * math.tau / 4 + .3
        P.gadd(T(spike_flame(.35, 1.1 + .3 * (k % 2)), (math.cos(a) * .2, .2, math.sin(a) * .2)), 'fire')
    for k in range(3):
        a = k * math.tau / 3
        P.add(tube([Vector((math.cos(a) * 1.5, -.2, math.sin(a) * 1.5)), Vector((0, 3.0, 0))], .07, sides=4), S('wood', base=.4, jit=.02))
    P.add(tube([Vector((0, 3.0, 0)), Vector((0, 1.95, 0))], .025, sides=3), S('gold', base=.3, jit=.01))
    P.add(T(lathe([(0, 0), (.4, 0), (.5, .3), (.45, .55), (.5, .6), (0, .6)], n=10), (0, 1.35, 0)), S('wood', base=.15, up=.1, jit=.02))
    P.add(tube([Vector((-1.3, .4, 2.6)), Vector((1.3, .45, 2.8))], .4, sides=8), S('wood', base=.42, up=.1, jit=.03))
    return P

def spike_flame(r, h):
    pts = [Vector((math.cos(a) * r, 0, math.sin(a) * r)) for a in [k * math.tau / 5 for k in range(5)]] + [Vector((0, h, 0)), Vector((.1, h * .5, .05))]
    return hull(pts)

def cargo_pile(seed=1):
    """caravan cargo: crates stacked, sacks, rolled rugs, two water jars and a saddle bag"""
    P = Prop('CargoPile%d' % seed); rng = random.Random(seed)
    crate(P, (0, 0, 0), 1.6, 10, seed); crate(P, (1.8, 0, .3), 1.4, -15, seed + 1); crate(P, (.6, 1.3, .1), 1.2, 30, seed + 2)
    sack(P, (-1.6, 0, .4), .7, 'saffron', seed); sack(P, (-1.5, 0, -1.0), .6, 'cloth', seed + 3); sack(P, (2.8, 0, -1.1), .55, 'red', seed + 4)
    rolled_rug(P, (-.8, .35, -1.8), (1.6, .35, -1.6), .35, 'red', 'saffron')
    rolled_rug(P, (-.4, 1.0, -1.7), (1.3, 1.0, -1.65), .3, 'indigo', 'cloth')
    jar(P, (3.2, 0, .8), 1.5, .5, 'stone2', 'indigo', 1); jar(P, (3.6, 0, -.1), 1.2, .42, 'stone', 'red', 2)
    return P

def oasis_pool(part='basin'):
    """oasis: a round pool (r 10) with a turquoise water disc set below a rim of cut sandstone blocks, a stone well head
    with a timber A-frame windlass, rope and bucket on the rim, stepping slab down to the water, lily pads.
    Two props on one origin: 'basin' = OasisBasin (bed, rim, well; precise) and 'water' = OasisWater (the disc, no
    collision) so the export's water check sees the bed under it and the rim round its edge"""
    rng = random.Random(6)
    R = 10.0; n = 30
    if part == 'water':
        P = Prop('OasisWater'); P.add(grid_disc(R + .2, -.45, 4.0), S('water', base=.55, up=.0, jit=.03)); return P
    P = Prop('OasisBasin')
    P.add(cyl(R + .3, .8, 40, y0=-1.6), S('stone2', base=.35, jit=.01))
    for k in range(n):
        a0, a1 = k * math.tau / n, (k + 1) * math.tau / n - .015
        pts = [Vector((math.cos(a) * r, y, math.sin(a) * r)) for a in (a0, a1) for r in (R + .2, R + 2.0) for y in (-.6, .55 + rng.uniform(-.06, .06))]
        P.add(hull(pts), S('stone', base=.58 + rng.uniform(-.06, .06), up=.14, jit=.02, seed=k))
    for k in range(6):
        a = rng.uniform(0, math.tau); r = rng.uniform(2, R - 2)
        P.add(T(cyl(rng.uniform(.4, .7), .04, 8), (math.cos(a) * r, -.42, math.sin(a) * r)), S('palm', base=.5, jit=.03))
    # stepping slab down to the water at the front (-Z)
    for k in range(2): P.add(T(box((3.0, .3, 1.2), .08), (0, .2 - k * .45, -R + .4 + k * 1.1)), S('stone', base=.62, up=.12, jit=.02))
    # well head on the rim (east)
    wx = R + 4.0
    P.add(T(B.ashlar_ring(1.8, 0, 1.6, 1.4, .8, seed=3), (wx, 0, 0)), ash_sh('stone', base=.6, var=.06, grime=0))
    P.add(cyl(1.8, 1.6, 14, y0=-.3), S('stone', base=.45, jit=.01)) if False else None
    P.add(T(cyl(1.75, 1.55, 14), (wx, 0, 0)), S('stone', base=.5, jit=.01))
    P.add(T(torus(1.85, .2, 16, 5), (wx, 1.65, 0)), S('stone', base=.68, jit=.02))
    P.add(T(cyl(1.5, .05, 14), (wx, 1.0, 0)), S('water', base=.25, jit=.01))
    for sz in (-1, 1):
        P.add(tube([Vector((wx - .9, -.2, sz * 1.9)), Vector((wx, 4.6, sz * 1.3))], .13, sides=6), S('wood', base=.42, jit=.02))
        P.add(tube([Vector((wx + .9, -.2, sz * 1.9)), Vector((wx, 4.6, sz * 1.3))], .13, sides=6), S('wood', base=.42, jit=.02))
    P.add(tube([Vector((wx, 4.4, -1.6)), Vector((wx, 4.4, 1.6))], .18, sides=8), S('wood', base=.5, jit=.02))
    P.add(T(cyl(.32, .6, 8), (wx, 4.4, -1.9), 0, 90), S('wood', base=.4, jit=.02))
    P.add(tube([Vector((wx, 4.25, .2)), Vector((wx, 2.6, .2))], .03, sides=3), S('cloth', base=.45, jit=.01))
    P.add(T(lathe([(.3, 0), (.38, .55), (.36, .6), (0, .05)], n=8), (wx, 2.0, .2)), S('wood', base=.45, up=.12, jit=.02))
    P.add(T(torus(.38, .03, 8, 3), (wx, 2.4, .2)), S('gold', base=.45, jit=.01))
    return P

def grid_disc(R, y, cell):
    """flat disc split into rings / sectors of ~cell (atlas-friendly)"""
    bm = bmesh.new(); nr = max(1, int(R / cell)); c = bm.verts.new((0, y, 0)); prev = [c]
    for i in range(1, nr + 1):
        r = R * i / nr; m = max(8, int(math.tau * r / cell))
        ring = [bm.verts.new((math.cos(k * math.tau / m) * r, y, math.sin(k * math.tau / m) * r)) for k in range(m)]
        if len(prev) == 1:
            for k in range(m): bm.faces.new((c, ring[(k + 1) % m], ring[k]))
        else:
            bmesh.ops.bridge_loops if False else None
            pm = len(prev)
            for k in range(m):
                a = ring[k]; b = ring[(k + 1) % m]
                pa = prev[int(k * pm / m) % pm]; pb = prev[int((k + 1) * pm / m) % pm]
                if pa is pb: bm.faces.new((pa, b, a))
                else: bm.faces.new((pa, pb, b, a))
        prev = ring
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    return bm

def treasure_mound(tier=1):
    """DIG SPOT anchors: tier 1 a low sand mound with a cracked jar and a marker stick, tier 2 a bigger mound with a
    half-buried iron-banded chest (lid ajar, coins) and a shovel stuck in the sand, tier 3 a big mound with an ornate gold
    chest, a glowing gem, spilled coins, a skull and a waystone-style marker"""
    P = Prop('TreasureMound%d' % tier); rng = random.Random(tier * 7)
    R = (2.6, 3.4, 4.4)[tier - 1]; Hm = (.9, 1.3, 1.7)[tier - 1]
    mound = uvsphere((R, Hm * 2, R * .85), 20, 10, (0, -Hm * .95, 0))
    for v in mound.verts:
        v.co.y += .15 * math.sin(v.co.x * 2.1 + v.co.z) * max(0, v.co.y)
        if v.co.y < -.2: v.co.y = -.2 - (v.co.y + .2) * .05
    P.add(mound, V('sand', 0, Hm, .5, .66, nk=.1, ns=1.5, seed=tier, amp=.04), smooth=True)
    if tier == 1:
        P.add(T(lathe([(0, 0), (.5, 0), (.75, .5), (.6, 1.0), (.3, 1.2), (.35, 1.4), (0, 1.3)], n=10), (.4, Hm * .4, -.2), 30, 35), S('stone2', base=.5, up=.12, jit=.02))
        P.add(tube([Vector((-1.3, 0, .6)), Vector((-1.45, 2.6, .7))], .07, sides=4), S('wood', base=.45, jit=.02))
        P.add(T(box((.5, .4, .04)), (-1.45, 2.4, .66), 0, 0, 8), S('red', base=.5, jit=.02))
        return P
    gold = tier == 3
    cw, ch, cd = (2.2, 1.2, 1.5) if tier == 2 else (2.8, 1.5, 1.9)
    cy = Hm * .55
    P.add(T(box((cw, ch, cd), .1), (0, cy, 0), 12, 8), S('gold' if gold else 'wood', base=.48, up=.12, jit=.02))
    for dx in (-.32, .32):
        P.add(T(T(box((.18, ch + .06, cd + .06)), (dx * cw, 0, 0)), (0, cy, 0), 12, 8), S('wood' if gold else 'gold', base=.4, jit=.02))
    lid = T(lathe([(0, 0), (cd / 2, 0), (cd / 2, .1), (cd * .35, cd * .4), (0, cd * .5)], n=8), (0, 0, 0), 0, 0, 90)
    bmesh.ops.scale(lid, vec=Vector((cw / .1 / 4.0 if False else 1, 1, 1)), verts=lid.verts)
    lid = T(T(box((cw, .3, cd), .12), (0, .15, 0)), (0, 0, 0), 0, -35)
    P.add(T(T(lid, (0, ch / 2, cd / 2)), (0, cy, 0), 12, 8), S('gold' if gold else 'wood', base=.55, up=.12, jit=.02))
    for k in range(10 if gold else 6):
        P.add(T(cyl(.16, .05, 8), (rng.uniform(-cw * .35, cw * .35), cy + ch / 2 + .05 + rng.uniform(0, .2), rng.uniform(-cd * .3, cd * .3))), S('gold', base=.72, jit=.03))
    if tier == 2:
        P.add(tube([Vector((2.0, -.3, .8)), Vector((1.6, 2.6, 1.3))], .07, sides=5), S('wood', base=.5, jit=.02))
        P.add(T(box((.7, .9, .08), .04), (2.05, -.1, .75), 0, 10, -6), S('gold', base=.35, jit=.02))
    else:
        P.gadd(T(hull([Vector((0, .9, 0)), Vector((0, -.6, 0))] + [Vector((math.cos(a) * .55, .1, math.sin(a) * .55)) for a in [k * math.tau / 6 for k in range(6)]]), (0, cy + ch / 2 + 1.1, 0)), 'gem')
        for k in range(14):
            a = rng.uniform(0, math.tau); r = rng.uniform(1.6, 3.4)
            P.add(T(cyl(.18, .05, 8), (math.cos(a) * r, Hm * (1 - (r / R) ** 2) * .9 + .02, math.sin(a) * r), 0, rng.uniform(-20, 20)), S('gold', base=.72, jit=.03))
        P.add(uvsphere((.55, .5, .65), 10, 7, (-2.4, Hm * .3, 1.2)), V('bone', 0, 1, .45, .75), smooth=True)
        for sx in (-1, 1): P.add(uvsphere((.13, .13, .05), 6, 4, (-2.4 + sx * .22, Hm * .35, .6)), S('wood', base=.1, jit=.01), smooth=True)
        P.add(T(waystone_body(5), (3.9, -.2, -2.6), -20, 0, 0, .8), S('stone', base=.56, up=.14, jit=.04))
    return P

def waystone_body(seed):
    rng = random.Random(seed)
    return hull([Vector((sx * w * rng.uniform(.9, 1.05), y, sz * d)) for y, w, d in ((-.6, .9, .6), (1.5, .8, .5), (2.8, .3, .25)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])

def outcrop(seed=1, r=4.0):
    """sandstone outcrop: two or three wind-cut rock masses, layered (darker bands low, pale wind-scoured tops)"""
    P = Prop('Outcrop%d' % seed); rng = random.Random(seed)
    for k in range(rng.randint(2, 3)):
        rr = r * (1.0 if k == 0 else rng.uniform(.45, .7))
        ox = 0 if k == 0 else rng.uniform(-r, r) * .9; oz = 0 if k == 0 else rng.uniform(-r, r) * .7
        bm = G.rock((rr, rr * rng.uniform(.6, .95), rr * .8), seed=seed * 11 + k, n=30, flat=.4)
        for v in bm.verts:                                                  # terrace the sides: wind-cut ledges
            q = round(v.co.y / (rr * .3)) * rr * .3
            v.co.y = lerp(v.co.y, q, .55)
        P.add(T(bm, (ox, rr * .25, oz), rng.uniform(0, 360)), V('rock', -rr * .3, rr * 1.0, .32, .74, nk=.22, ns=2.5, seed=seed + k, amp=.06))
    return P

def dry_shrub(seed=1, r=1.4):
    """desert scrub: a woody tangle of forking twigs from one root crown with small dusty leaf tufts"""
    P = Prop('DryShrub%d' % seed); rng = random.Random(seed)
    for k in range(9):
        a = rng.uniform(0, math.tau); up = rng.uniform(.5, 1.2)
        tip = Vector((math.cos(a) * r, r * up, math.sin(a) * r))
        mid = tip * .5 + Vector((rng.uniform(-.3, .3), .2, rng.uniform(-.3, .3)))
        P.add(tube([Vector((0, -.2, 0)), mid, tip], [.07, .045, .02], sides=3), S('wood', base=.5, jit=.03))
        for j in range(2):
            P.add(T(blob(rng.uniform(.25, .4), seed * 9 + k * 3 + j, n=8, sq=.7), tuple(tip.lerp(mid, j * .6))), S('scrub', base=.5 + rng.uniform(-.1, .1), up=.2, jit=.05))
    return P

def dune_grass(seed=1, n=11, h=1.6):
    """tuft of tall pale dune grass: tapered folded blades arching out of a tight crown"""
    P = Prop('DuneGrass%d' % seed); rng = random.Random(seed)
    for k in range(n):
        a = rng.uniform(0, math.tau); lean = rng.uniform(.25, .7); L = h * rng.uniform(.7, 1.15)
        d = Vector((math.cos(a), 0, math.sin(a)))
        pts = [Vector((0, -.1, 0)) + d * .1, d * L * lean * .35 + Vector((0, L * .55, 0)), d * L * lean + Vector((0, L * .85, 0))]
        side = Vector((-d.z, 0, d.x)) * .07
        bm = bmesh.new(); vs = [bm.verts.new(pts[0] - side), bm.verts.new(pts[0] + side), bm.verts.new(pts[1] + side * .6), bm.verts.new(pts[1] - side * .6), bm.verts.new(pts[2])]
        bm.faces.new((vs[0], vs[1], vs[2], vs[3])); bm.faces.new((vs[3], vs[2], vs[4]))
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.03)
        P.add(bm, V('scrub', 0, h, .45, .8, nk=0))
    return P

def sand_drift(seed=1, L=10.0, W=4.0, Hh=1.6):
    """smooth sand drift banked against ruins (no collision): a long soft lump, steep lee face, sunk below the origin"""
    P = Prop('SandDrift%d' % seed)
    bm = uvsphere((L / 2, Hh * 2, W / 2), 16, 8, (0, -Hh, 0))
    for v in bm.verts:
        if v.co.z > 0: v.co.y = -Hh + (v.co.y + Hh) * (1 - .35 * v.co.z / (W / 2))
        if v.co.y < -.3: v.co.y = -.3
    P.add(bm, V('sand', 0, Hh, .52, .64, nk=.08, ns=2.0, seed=seed, amp=.03), smooth=True)
    return P

# ------------------------------------------------------------------ the sand-wyrm skeleton
def wyrm_skull():
    """giant sand-wyrm skull lying jaw-open in the sand: long ridged cranium with deep eye sockets, two swept-back horns,
    a long tapered snout with rows of conical teeth, the lower jaw dropped beside it. ~22 long, front -Z"""
    P = Prop('WyrmSkull'); rng = random.Random(9)
    bone = V('bone', -1, 7, .42, .78, nk=.2, ns=3.0, seed=2, amp=.06)
    cran = uvsphere((4.2, 3.4, 5.6), 24, 14, (0, 3.2, 2.0))
    for v in cran.verts:
        z = v.co.z
        if z < 2.0:
            t = clamp((2.0 - z) / 5.6)
            v.co.x *= 1 - .45 * t; v.co.y = 3.2 + (v.co.y - 3.2) * (1 - .4 * t)
        if v.co.y > 5.6: v.co.y += .6 * math.exp(-(v.co.x / .8) ** 2)                  # sagittal crest
    P.add(cran, bone, smooth=True)
    snout = tube([Vector((0, 2.8, -2.0)), Vector((0, 2.5, -6.0)), Vector((0, 2.1, -10.0)), Vector((0, 1.8, -12.6))], [2.4, 1.9, 1.4, .8], sides=12, flat=(1.15, .8))
    P.add(snout, bone, smooth=True)
    for sx in (-1, 1):
        P.add(uvsphere((1.3, 1.1, 1.4), 12, 8, (sx * 2.6, 4.2, .2)), S('wood', base=.08, jit=.01), smooth=True)             # socket void
        P.add(T(torus(1.45, .35, 16, 6), (sx * 2.75, 4.2, .2), 90 * sx, 0, 90), bone, smooth=True)                         # socket rim
        horn = [Vector((sx * 2.8, 5.2, 4.0)), Vector((sx * 3.8, 6.4, 7.0)), Vector((sx * 4.4, 6.6, 10.2)), Vector((sx * 4.2, 5.8, 12.6))]
        P.add(tube(horn, [1.0, .75, .45, .1], sides=8), V('bone', 4, 7, .5, .7, nk=.2), smooth=True)
        for k in range(9):
            z = -2.6 - k * 1.15
            w = lerp(1.9, .9, k / 8) * 1.08
            P.add(T(spike(.24, .9 - k * .04, sides=5), (sx * w, 1.6 - k * .08, z), 0, 180), S('bone', base=.72, up=.1, jit=.03))
        P.add(uvsphere((.35, .25, .35), 6, 4, (sx * .55, 2.6, -12.4)), S('wood', base=.1, jit=.01), smooth=True)          # nostril
    jaw = tube([Vector((0, .5, 1.5)), Vector((0, .4, -3.5)), Vector((0, .3, -8.0)), Vector((0, .35, -11.2))], [1.0, .8, .6, .4], sides=8, flat=(2.2, .6))
    for v in jaw.verts:
        if v.co.y > .5: v.co.y = .5 + (v.co.y - .5) * .4
    P.add(T(jaw, (3.6, -.2, -.8), -18, 0, 10), bone, smooth=True)
    return P

def wyrm_rib(seed=1, s=1.0):
    """one segment of the wyrm's spine lying belly-down: the vertebra (with a spinous process) high on top and a pair of
    thick ribs curving out and down to the sand on both sides = a bone arch players walk under (origin = ground centre)"""
    P = Prop('WyrmRib%d' % seed); rng = random.Random(seed)
    bone = V('bone', -1, 11 * s, .45, .82, nk=.2, ns=2.0, seed=seed, amp=.05)
    top = 9.6 * s
    P.add(uvsphere((1.4 * s, 1.2 * s, 1.3 * s), 14, 9, (0, top, 0)), bone, smooth=True)
    for sx in (-1, 1): P.add(uvsphere((.8 * s, .55 * s, .65 * s), 8, 6, (sx * 1.25 * s, top - .2 * s, 0)), bone, smooth=True)
    P.add(tube([Vector((0, top + .8 * s, 0)), Vector((0, top + 2.4 * s, .6 * s)), Vector((0, top + 3.4 * s, 1.3 * s))], [.65 * s, .35 * s, .1 * s], sides=8), bone, smooth=True)
    for sx in (-1, 1):
        n = 10; pts = []; sp = rng.uniform(.95, 1.06)
        for k in range(n + 1):
            a = k / n * 1.9
            x = 1.1 + 8.2 * sp * math.sin(min(a, math.pi / 2)) - 1.2 * max(0.0, a - math.pi / 2)
            pts.append(Vector((sx * x * s, (top - .3 * s) * math.cos(a) * (1 if a < math.pi / 2 else 1.6), .35 * k / n * s)))
        r = [lerp(.8, .42, k / n) * s for k in range(n + 1)]
        if seed % 3 == 0 and sx > 0: pts, r = pts[:5], r[:5]                    # one snapped rib
        P.add(tube(pts, r, sides=8), bone, smooth=True)
    return P

def rock_stack(seed=1, r=4.0):
    """wind-cut sandstone stack: 3-5 rounded slabs piled and offset (each narrower), dark rust bands low, pale tops"""
    P = Prop('RockStack%d' % seed); rng = random.Random(seed); y = -.6; ox = oz = 0.0
    for k in range(rng.randint(3, 5)):
        rr = r * (1 - .14 * k) * rng.uniform(.9, 1.05); h = rr * rng.uniform(.38, .5)
        bm = G.rock((rr, h, rr * rng.uniform(.7, .9)), seed=seed * 11 + k, n=24, flat=.7)
        lo = min(v.co.y for v in bm.verts); hi = max(v.co.y for v in bm.verts) - lo
        P.add(T(bm, (ox, y - lo, oz), rng.uniform(0, 360)), V('rock' if k % 2 == 0 else 'stone2', y, y + h * 1.8, .3, .66, nk=.25, ns=2.5, seed=seed + k, amp=.06))
        y += hi * .82; ox += rng.uniform(-.2, .2) * rr; oz += rng.uniform(-.2, .2) * rr
    return P

# ------------------------------------------------------------------ HERO: colossus head
def colossus_head():
    """HERO: giant half-buried stone head of a sun-king (face sculpted by displacement fields: brow, closed eyes in deep
    sockets, nose, cheekbones, full lips, chin; ears; a crown band with a ring of sun rays, two snapped), with a broken
    off crown piece. Head ~18 tall above its base, front -Z; the map tilts it and sinks it to the chin."""
    P = Prop('ColossusHead'); rng = random.Random(21)
    C = Vector((0, 9.0, 0)); RX, RY, RZ = 6.4, 8.6, 7.0
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=68, radius=1.0)
    def g(x, y, cx, cy, sx, sy): return math.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))
    for v in bm.verts:
        d = v.co.copy(); x, y, z = d.x * RX, d.y * RY, d.z * RZ
        # jaw narrower, cranium wider at the temples, flat back, flatter sides
        k = 1.0 - .22 * smooth((-y - 1.0) / 6.5); x *= k
        if z > 0: z *= .9
        p = Vector((x, y, z))
        if z < 0:
            fx, fy = x, y
            front = smooth(-z / 3.0)
            dz = 0.0
            dz += .9 * g(fx, fy, 0, 2.6, 4.0, .8)                            # brow ridge
            for sx in (-1, 1):
                dz -= 2.0 * g(fx, fy, sx * 2.25, 1.0, 1.35, .95)            # eye socket
                dz += 1.05 * g(fx, fy, sx * 2.25, .8, 1.05, .45)            # closed eyelid bulge
                dz += .55 * g(fx, fy, sx * 3.4, -1.4, 1.4, 1.2)             # cheekbone
                dz += .3 * g(fx, fy, sx * 1.05, -3.6, .45, .38)             # nostril wing
                dz -= .25 * g(fx, fy, sx * 2.1, -4.6, .5, .6)               # mouth corner
            nose = g(fx, 0, 0, 0, .85, 1) * smooth((1.6 - fy) / 1.2) * smooth((fy + 3.8) / .6)
            dz += nose * (1.0 + 1.6 * smooth((1.2 - fy) / 4.6))                # nose ridge growing to the tip
            dz -= .5 * g(fx, fy, 0, -3.95, .6, .2)                           # under the nose
            dz += 1.0 * g(fx, fy, 0, -4.45, 1.9, .38)                        # upper lip
            dz -= .7 * g(fx, fy, 0, -4.9, 1.9, .14)                         # lip line
            dz += .95 * g(fx, fy, 0, -5.35, 1.6, .42)                        # lower lip
            dz -= .3 * g(fx, fy, 0, -6.0, 1.4, .3)                           # chin fold
            dz += .7 * g(fx, fy, 0, -6.9, 1.9, .9)                           # chin
            p.z -= dz * front
        p.z += .12 * (nz(p.x, p.y, p.z, 2.0, 5) - .5)
        v.co = p + C
    P.add(bm, V('stone', 0, 18, .4, .72, nk=.16, ns=4.0, seed=3, amp=.06), smooth=True)
    for sx in (-1, 1):                                                       # ears
        e = uvsphere((.6, 1.9, 1.1), 10, 8, (sx * 6.05, 8.6, 1.1))
        P.add(e, V('stone', 6, 11, .42, .66, nk=.15), smooth=True)
        P.add(T(torus(1.0, .25, 12, 5), (sx * 6.25, 8.7, 1.1), 0, 0, 90), V('stone', 6, 11, .45, .7), smooth=True)
    # crown band + sun rays (two snapped off)
    P.add(T(lathe([(5.9, 0), (6.15, .3), (6.15, 1.6), (5.9, 1.9), (0, 1.9)], n=40), (0, 13.4, 0)), S('gold', base=.55, up=.12, jit=.02))
    for k in range(13):
        a = math.pi * .5 + (k - 6) * math.radians(17)
        if k in (2, 9): Ln = 1.3
        else: Ln = 6.0 if k % 2 == 0 else 4.4
        d = Vector((math.cos(a), 0, -math.sin(a)))
        base_c = Vector((0, 15.2, 0)) + d * 5.0
        tip = base_c + d * Ln * .35 + Vector((0, Ln, 0))
        side = Vector((-d.z, 0, d.x)) * 1.15
        pts = [base_c - side, base_c + side, base_c - side + d * .7, base_c + side + d * .7, tip, tip + d * .35]
        P.add(hull(pts), S('gold', base=.6, up=.1, jit=.03))
    sun_relief(P, (0, 14.35, -6.1), 1.05, 0.0, gold=True, depth=.4)
    for k in range(10):
        a = math.pi * .5 + (k - 4.5) * math.radians(20)
        if abs(k - 4.5) < 1: continue
        P.add(T(disc(.38, .25, 8, .05), (math.cos(a) * 6.12, 14.35, -math.sin(a) * 6.12), math.degrees(math.atan2(math.cos(a), -math.sin(a))) + 180), S('red', base=.5, jit=.02))
    P.add(cyl(4.6, 3.0, 20, y0=-1.0), V('stone', -1, 2, .35, .5))          # neck stub into the sand
    # snapped crown piece lying in the sand beside the head
    for k in range(2):
        a = rng.uniform(-.4, .4)
        pts = [Vector((-.8, 0, 0)), Vector((.8, 0, 0)), Vector((-.8, .5, .7)), Vector((.8, .5, .7)), Vector((0, 5.0, .2)), Vector((0, 5.0, .55))]
        P.add(T(hull(pts), (9.0 + k * 2.2, .9, -4.0 + k * 1.5), rng.uniform(0, 90), 82, 0), S('gold', base=.55, up=.12, jit=.03))
    R = Matrix.Rotation(math.radians(-9), 3, 'X') @ Matrix.Rotation(math.radians(11), 3, 'Z')     # tilted back + to the side
    P.solid.V = [tuple(R @ Vector(v)) for v in P.solid.V]
    return P

# ------------------------------------------------------------------ HERO: sunken temple (dungeon portal)
def sunken_temple():
    """HERO / DUNGEON PORTAL: a columned temple front sunk 12 studs into the dunes, reached by a 16-step stair down a
    walled trench. Local y 0 = trench floor (the map places it 12 below the surface), facade plane at z 0, body behind
    (+Z, buried under a sand mound), stair rising toward -Z to ground level (y 12) at z -38. Glowing portal in the door."""
    P = Prop('SunkenTemple'); rng = random.Random(13)
    FW, FH = 26.0, 21.0
    # body (mostly buried) + facade ashlar
    P.add(T(box((FW, FH, 20.0), .2), (0, FH / 2, 10.2)), S('stone', base=.5, jit=.01))
    pan = B.ashlar(FW, FH - 3.0, 4.0, 1.6, seed=4, skip=lambda x, y: abs(x) < 4.4 and y < 12.2, depth=.14, ins=.1)
    T(pan, (0, 0, 0), 180); T(pan, (0, 0, .18)); P.add(pan, ash_sh('stone', base=.6, var=.08, grime=.0))
    # cornice + sun disc frieze
    P.add(T(box((FW + 2.4, 1.2, 3.0), .2), (0, FH - 2.4, -.6)), S('stone', base=.68, up=.1, jit=.02))
    pts = [Vector((x, FH - 1.8, z)) for x in (-FW / 2 - 1.6, FW / 2 + 1.6) for z in (-2.6, 2.0)] + [Vector((x, FH + .6, z)) for x in (-FW / 2 - 2.2, FW / 2 + 2.2) for z in (-3.2, 2.0)]
    P.add(hull(pts), S('stone', base=.64, up=.1, jit=.02))
    P.add(T(box((FW + 4.6, .7, 5.6), .15), (0, FH + .95, -.6)), S('stone', base=.7, up=.1, jit=.02))
    for i, x in enumerate((-9.0, -4.5, 0.0, 4.5, 9.0)):
        sun_relief(P, (x, FH - 4.6, -.05), 1.5 if i == 2 else 1.0, 0.0, gold=(i == 2), depth=.3)
    zig_band(P, FW - 3.0, (0, FH - 6.6, -.05), 0.0, h=1.2)
    # doorway: stepped gold frame, dark recess, portal glow
    P.add(T(box((8.8, 12.6, .9), .1), (0, 6.3, -.3)), S('gold', base=.45, jit=.02))
    P.add(T(box((7.6, 11.8, 1.0), .05), (0, 5.9, -.35)), S('stone', base=.3, jit=.01))
    P.add(T(box((10.6, 1.6, 1.6), .15), (0, 13.2, -.6)), S('stone', base=.68, up=.1, jit=.02))
    sun_relief(P, (0, 13.2, -1.42), .7, 0.0, gold=True, depth=.25, rays=12)
    P.gadd(T(box((6.6, 11.0, .2)), (0, 5.5, -.9)), 'portal')
    for k in range(3): P.gadd(T(torus(1.4 + k * .9, .07, 24, 4), (0, 5.8, -1.1 - k * .02), 0, 90), 'portal')
    # portico columns
    for i, x in enumerate((-10.5, -6.0, 6.0, 10.5)):
        column(P, (x, 0, -3.4), FH - 3.3, 1.15, seed=60 + i)
    P.add(T(box((FW + .6, 1.4, 3.2), .15), (0, FH - 3.3 + .7, -3.4)), S('stone', base=.62, up=.1, jit=.02))
    # floor landing + stair + trench walls
    P.add(T(box((15.0, 1.0, 6.0), .1), (0, -.5, -3.0)), S('stone', base=.55, up=.12, jit=.02))
    nst = 16; rise = 12.0 / nst; run = 32.0 / nst
    for i in range(nst):
        y1 = (i + 1) * rise; z0 = -6.0 - i * run
        P.add(T(box((14.2, 2.4, run + .25), .06), (0, y1 - 1.2, z0 - run / 2)), S('stone', base=.56 + (i % 2) * .04, up=.14, jit=.02, seed=i))
    for sx in (-1, 1):
        tmp = Prop('t')
        block_wall(tmp, 42.5, 13.2, 2.0, bw=3.2, bh=1.65, col='stone', seed=20 + sx, base=.56)
        tmp.add(T(box((42.9, .7, 2.8), .15), (0, 13.45, 0)), S('stone', base=.7, up=.12, jit=.02))
        merge_into(P, tmp, lambda v, sx=sx: Vector((sx * 8.2 + v.z, v.y, -20.75 - v.x)))
        # sun pillar at the stair head
        P.add(T(box((2.6, 1.0, 2.6), .12), (sx * 9.6, 13.4, -40.0)), S('stone', base=.6, up=.1, jit=.02))
        P.add(T(frustum(1.9, 1.9, 1.2, 1.2, 0, 5.5), (sx * 9.6, 13.9, -40.0)), S('stone', base=.6, up=.1, jit=.02))
        P.add(T(frustum(1.3, 1.3, .05, .05, 0, 1.2), (sx * 9.6, 19.4, -40.0)), S('gold', base=.62, up=.15, jit=.02))
        sun_relief(P, (sx * 9.6, 16.8, -40.0 - .87), .55, 0.0, gold=True, depth=.15, rays=8, pitch=-7)
    # sand spilling down the stair
    for k in range(4):
        z = -12.0 - k * 7.0; y = 12.0 * (-z - 6.0) / 32.0
        d = uvsphere((rng.uniform(2.0, 3.4), 1.2, rng.uniform(1.6, 2.4)), 12, 6, (rng.choice((-1, 1)) * rng.uniform(3.5, 5.0), y - .4, z))
        for v in d.verts: v.co.y = max(v.co.y, y - .9)
        P.add(d, V('sand', y - 1, y + 1, .52, .64, nk=.08), smooth=True)
    return P
