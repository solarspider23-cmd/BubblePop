# Puffpaw Isles prop kit (pet-collecting simulator, HAPPY CHIBI style).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Style: squashy rounded chunky shapes, smooth shading, soft gradients (dark under, bright on top + a lit side), pastel
# but saturated candy colours. Everything soft and toy-like. No text, no letters, no flags or banners.
# Machinery (Prop, S, materials, to_kit) from the grove example, transforms (T, lathe, torus) from the medieval example;
# every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, nz, clamp, ngon_prism, bevel, lerp, smooth

PAL = Palette({
    'grass':  ('#3f9e45', '#7fd65e', '#d6ffa6'),
    'leaf':   ('#2f9a54', '#66d26e', '#d0ffb4'),
    'mint':   ('#25a68e', '#62e2c2', '#d4fff2'),
    'pink':   ('#d64888', '#ff8cc2', '#ffe4f2'),
    'cream':  ('#cf9f74', '#ffe4c2', '#fffcf4'),
    'sky':    ('#3384d6', '#78c4ff', '#e0f4ff'),
    'lilac':  ('#7c52d0', '#b494ff', '#f0e6ff'),
    'yellow': ('#d99a14', '#ffd247', '#fff7c8'),
    'orange': ('#e46e2a', '#ffa456', '#ffe6c8'),
    'red':    ('#cc3346', '#ff6a78', '#ffd6da'),
    'wood':   ('#8e5430', '#cf8d56', '#ffd8a6'),
    'water':  ('#1f9ad6', '#4fd2ff', '#dcfbff'),
    'stone':  ('#8a86a6', '#c8c4dc', '#f8f6ff'),
    'dark':   ('#231d36', '#3e355a', '#8a80aa'),
    'cloud':  ('#a9bde6', '#e8f1ff', '#ffffff'),
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
GLOWS = {'gem': '#ff9be0', 'lamp': '#fff0b0', 'ring_mint': '#6dffd8', 'ring_sky': '#7fd4ff', 'ring_gold': '#ffd84a',
         'ring_pink': '#ff8fd0', 'ring_lilac': '#c4a2ff', 'ring_green': '#9cff7a', 'star': '#fff3a0', 'crystal': '#c8a4ff',
         'shroom': '#7ff6ff', 'arrow': '#9cff7a', 'trade': '#ffd84a'}
G.GLOW.clear(); G.GLOW.update(GLOWS)
G.GLOW_E.clear(); G.GLOW_E.update({k: 2.4 for k in GLOWS}); G.GLOW_E.update({'lamp': 3.0, 'star': 3.0, 'gem': 2.0})
Prop = G.Prop
T, lathe, torus, frame_to = B.T, B.lathe, B.torus, B.frame_to
V3 = Vector
SUN = Vector((.45, .8, -.4)).normalized()          # shading key direction (upper left-front)

# ------------------------------------------------------------------ shading
def vsh(col, fn):
    u = PAL.u(col)
    return lambda f: [(u, clamp(fn(l.vert.co, f.normal), .05, .95)) for l in f.loops]

def soft(col, y0, y1, a=.34, b=.8, c=None, k=.12):
    """height gradient a->b between y0..y1 plus a lit side toward SUN (needs the shape centre c for a smooth normal)"""
    def fn(p, n):
        t = clamp((p.y - y0) / max(y1 - y0, 1e-4)); d = n
        if c is not None:
            d = (p - V3(c)); d = (d.normalized() + n).normalized() if d.length > 1e-6 else n
        return lerp(a, b, smooth(t)) + k * d.dot(SUN)
    return vsh(col, fn)

def flat(col, v=.62, up=.16):
    return vsh(col, lambda p, n: v + up * n.y)

# ------------------------------------------------------------------ primitives
def ell(rx, ry, rz, nu=16, nv=10):
    prof = [(math.sin(math.pi * k / nv), -math.cos(math.pi * k / nv)) for k in range(nv + 1)]
    prof[0] = (0, -1); prof[-1] = (0, 1)
    bm = lathe(prof, nu); bmesh.ops.scale(bm, vec=V3((rx, ry, rz)), verts=bm.verts)
    return bm

def puff(r, seed, lobes=7, amp=.2, nu=22, nv=14, sq=.9, flatb=.5, k=4.5, even=False):
    """soft cloud / crown: a sphere pushed out by smooth lobes, flattened underneath (smooth shading).
    even = lobes on a fibonacci spiral over the upper 85% (bubbly, evenly spaced bumps: puffball crowns)"""
    rng = random.Random(seed); L = []
    for i in range(lobes):
        if even:
            y = 1 - 1.7 * (i + .5) / lobes; rr = math.sqrt(max(0, 1 - y * y)); a = i * 2.39996 + seed
            L.append((V3((math.cos(a) * rr, y, math.sin(a) * rr)), rng.uniform(.8, 1.0)))
            continue
        d = V3((rng.gauss(0, 1), abs(rng.gauss(0, 1)) * .8 + .1, rng.gauss(0, 1))).normalized()
        L.append((d, rng.uniform(.6, 1.0)))
    bm = ell(1, 1, 1, nu, nv)
    for v in bm.verts:
        d = v.co.normalized() if v.co.length > 1e-6 else V3((0, 1, 0))
        kk = 1 + sum(w * amp * math.exp((d.dot(ld) - 1) * k) for ld, w in L) - amp * .25
        p = d * kk * r; p.y *= sq
        if p.y < -r * flatb: p.y = -r * flatb + (p.y + r * flatb) * .25
        v.co = p
    return bm

def rbox(size, r=.3, seg=2):
    return bevel(box(size), min(r, min(size) * .45), seg)

def rcyl(r, h, sides=16, bev=.3, seg=2, y0=0.0, r2=None):
    bm = cyl(r, h, sides, 0, r2, y0)
    if bev > 0:
        rims = [e for e in bm.edges if all(abs(v.co.y - y0) < 1e-4 for v in e.verts) or all(abs(v.co.y - (y0 + h)) < 1e-4 for v in e.verts)]
        bevel(bm, min(bev, h * .45), seg, rims)
    return bm

def pill(a, b, r, sides=8, rings=3):
    """capsule from a to b (rounded ends)"""
    a, b = V3(a), V3(b); L = (b - a).length
    prof = [(r * math.sin(math.pi / 2 * k / rings), -r * math.cos(math.pi / 2 * k / rings)) for k in range(rings + 1)]
    prof += [(r * math.cos(math.pi / 2 * k / rings), L + r * math.sin(math.pi / 2 * k / rings)) for k in range(rings + 1)]
    prof[0] = (0, -r); prof[-1] = (0, L + r)
    bm = lathe(prof, sides)
    # lathe is along +Y; turn so +Y points a -> b
    d = (b - a).normalized(); q = V3((0, 1, 0)).rotation_difference(d)
    bmesh.ops.rotate(bm, cent=V3(), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=a, verts=bm.verts)
    return bm

def arc_pts(R, a0, a1, n, y=0.0, cx=0.0, cz=0.0):
    return [V3((cx + math.cos(lerp(a0, a1, i / n)) * R, y, cz + math.sin(lerp(a0, a1, i / n)) * R)) for i in range(n + 1)]

def star_poly(ro, ri, n=5, a0=math.pi / 2):
    return [(math.cos(a0 + i * math.pi / n) * (ro if i % 2 == 0 else ri), math.sin(a0 + i * math.pi / n) * (ro if i % 2 == 0 else ri)) for i in range(2 * n)]

def star(ro, th, n=5, ri=None):
    """a chunky star standing upright facing -Z, centred at the origin, rounded front edge"""
    bm = ngon_prism(list(reversed(star_poly(ro, ri or ro * .5, n))), -th / 2, th / 2, th * .3)
    return T(bm, (0, 0, 0), 0, -90)         # prism axis Y -> Z, star point up

def disc_up(r, th, sides=12, y=0.0, bev=None):
    return rcyl(r, th, sides, th * .45 if bev is None else bev, 1, y)

def paw(P, c, s, col='pink', yaw=0.0, pitch=90.0, th=.25, sides=10):
    """paw-print icon: palm pad + 4 toe beans, built flat then stood up facing -Z (pitch 90) at c"""
    parts = [((0, 0, .25), (1.0, .82)), ((-.82, 0, -.58), (.36, .42)), ((-.3, 0, -1.0), (.36, .44)),
             ((.3, 0, -1.0), (.36, .44)), ((.82, 0, -.58), (.36, .42))]
    for (x, y, z), (rx, rz) in parts:
        bm = ell(rx * s, th, rz * s, sides, 4)
        T(bm, (x * s, 0, z * s)); T(bm, (0, 0, 0), 0, -pitch); T(bm, c, yaw)
        P.add(bm, soft(col, -s, s, .55, .8), True)

def lift(bm, dy):
    bmesh.ops.translate(bm, vec=V3((0, dy, 0)), verts=bm.verts); return bm

def egg_prof(R, H, m=10):
    out = []
    for k in range(m + 1):
        a = math.pi * k / m; y = H * (1 - math.cos(a)) / 2
        r = R * math.sin(a) * (1.06 - .22 * (y / H))
        out.append((r if 0 < k < m else 0.0, y))
    return out

def egg_r(R, H, y):
    prof = egg_prof(R, H, 40)
    for (ra, ya), (rb, yb) in zip(prof, prof[1:]):
        if ya <= y <= yb: return lerp(ra, rb, (y - ya) / max(yb - ya, 1e-6))
    return 0.0

# ------------------------------------------------------------------ egg (identity piece of the hatchery)
def egg(P, c, R, H, shell, deco, deco2='cream', n=18, m=12, seed=0):
    """smooth lathe egg + decoration: 'spots', 'stars', 'zig', 'swirl', 'gems', 'flowers'"""
    x0, y0, z0 = c
    P.add(T(lathe(egg_prof(R, H, m), n), c), soft(shell, y0, y0 + H, .42, .9, (x0, y0 + H * .45, z0), .1), True)
    rng = random.Random(seed)
    def onshell(y, a, out=1.0):
        r = egg_r(R, H, y) * out
        return V3((x0 + math.cos(a) * r, y0 + y, z0 + math.sin(a) * r))
    def stick(bm, y, a, s):
        """small decal piece built facing +Y, laid on the shell (tangent) at height y, angle a"""
        p = onshell(y, a, .97)
        nrm = (p - V3((x0, y0 + y - (H * .12 if y < H * .5 else -H * .08), z0))).normalized()
        q = V3((0, 1, 0)).rotation_difference(nrm)
        bmesh.ops.rotate(bm, cent=V3(), matrix=q.to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=p, verts=bm.verts); return bm
    if deco in ('spots', 'gems', 'stars', 'flowers'):
        rows = ((.3, 7), (.55, 6), (.78, 4))
        for i, (t, k) in enumerate(rows):
            for j in range(k):
                a = j * math.tau / k + i * .5
                s = R * (.32 if t < .7 else .24)
                if deco == 'spots': P.add(stick(ell(s, s * .22, s, 10, 4), t * H, a, s), soft(deco2, y0, y0 + H, .5, .85), True)
                elif deco == 'gems': P.gadd(stick(B.lathe([(0, -.1), (s * .7, 0), (s * .45, s * .5), (0, s * .62)], 6), t * H, a, s), 'gem')
                elif deco == 'stars':
                    bm = ngon_prism(list(reversed(star_poly(s, s * .45))), 0, s * .25, s * .08)
                    P.add(stick(bm, t * H, a, s), soft(deco2, y0, y0 + H, .55, .9), True)
                else:
                    for q in range(5):
                        aa = q * math.tau / 5
                        P.add(stick(T(ell(s * .38, s * .14, s * .3, 8, 3), (math.cos(aa) * s * .4, 0, math.sin(aa) * s * .4)), t * H, a, s), soft(deco2, y0, y0 + H, .55, .85), True)
                    P.add(stick(lift(ell(s * .22, s * .18, s * .22, 8, 3), s * .05), t * H, a, s), soft('yellow', y0, y0 + H, .55, .85), True)
    if deco in ('zig', 'swirl'):
        # proud band(s) round the egg: zig = zigzag ring, swirl = 3 tilted stripes
        bands = [(.42, .0)] if deco == 'zig' else [(.3, .35), (.52, .35), (.74, .35)]
        for yt, tilt in bands:
            bm = bmesh.new(); N = 36; ring = []
            for i in range(N + 1):
                a = i * math.tau / N
                yy = yt * H + (math.sin(a * 2) * tilt * R * .5 if deco == 'swirl' else (H * .045 if i % 2 else -H * .045))
                w = H * (.05 if deco == 'zig' else .045)
                ring.append([bm.verts.new(onshell(yy + d, a, 1.025)) for d in (-w, w)])
            for A, Bq in zip(ring, ring[1:]): bm.faces.new((A[0], Bq[0], Bq[1], A[1]))
            bm.normal_update()
            for f in bm.faces:
                cc = f.calc_center_median()
                if f.normal.dot(cc - V3((x0, cc.y, z0))) < 0: f.normal_flip()
            P.add(bm, soft(deco2, y0, y0 + H, .5, .85), True)

# ------------------------------------------------------------------ HERO: Puffpaw Fountain
def puffpaw(P, c, s=1.0, body='cream', inner='pink', collar='sky'):
    """the mascot: chubby sitting creature, huge head, tall round ears, big eyes with highlights, blush, w-mouth,
    raised waving paw, curled puff tail, collar with a bell. Built facing -Z at c (seat point), scale s."""
    cx, cy, cz = c
    def at(bm, p): return T(bm, (cx + p[0] * s, cy + p[1] * s, cz + p[2] * s))
    def sc(bm): bmesh.ops.scale(bm, vec=V3((s, s, s)), verts=bm.verts); return bm
    top = cy + 15 * s
    # body: pear-shaped sitting body
    bb = ell(4.15, 3.7, 3.9, 26, 16)
    for v in bb.verts:
        if v.co.y < -2.9: v.co.y = -2.9 + (v.co.y + 2.9) * .3
        v.co.x *= 1 - .1 * clamp(v.co.y / 3.7); v.co.z *= 1 - .1 * clamp(v.co.y / 3.7)
    P.add(at(sc(T(bb, (0, 3.2, 0))), (0, 0, 0)), soft(body, cy, top, .45, .9, (cx, cy + 3.2 * s, cz)), True)
    # belly patch
    P.add(at(sc(T(ell(2.5, 2.4, 1.0, 16, 8), (0, 2.6, -3.55))), (0, 0, 0)), soft('cloud', cy, top, .65, .95), True)
    # feet (front, toes forward) + toe beans
    for sx in (-1, 1):
        P.add(at(sc(ell(1.5, 1.0, 2.0, 14, 8)), (sx * 2.1, .7, -3.0)), soft(body, cy, top, .45, .85, (cx + sx * 2.1 * s, cy + .7 * s, cz - 3 * s)), True)
        for k in (-1, 0, 1):
            P.add(at(sc(ell(.32, .22, .32, 8, 4)), (sx * 2.1 + k * .55, .55, -4.85)), soft(inner, cy, top, .6, .8), True)
    # arms: left resting on belly, right raised waving
    P.add(at(sc(pill((0, 0, 0), (.9, -1.6, -1.1), .95, 12, 3)), (-3.4, 4.6, -.8)), soft(body, cy, top, .45, .88), True)
    P.add(at(sc(pill((0, 0, 0), (1.3, 2.6, -.9), .95, 12, 3)), (3.3, 4.6, -.6)), soft(body, cy, top, .45, .9), True)
    P.add(at(sc(ell(1.15, 1.2, 1.0, 12, 8)), (4.65, 7.35, -1.55)), soft(body, cy, top, .5, .92), True)
    P.add(at(sc(T(ell(.62, .5, .2, 10, 4), (0, 0, 0), 0, 0)), (4.7, 7.25, -2.5)), soft(inner, cy, top, .6, .85), True)
    # tail: curled puff behind
    P.add(at(sc(puff(1.9, 4, 7, .2, 16, 10, .95, .6, 6, True)), (0, 1.9, 3.9)), soft('cloud', cy, top, .6, .95), True)
    # collar + bell
    P.add(at(sc(torus(2.75, .42, 24, 8)), (0, 6.2, -.1)), soft(collar, cy, top, .45, .8), True)
    P.add(at(sc(ell(.75, .75, .75, 12, 8)), (0, 5.45, -2.75)), soft('yellow', cy, top, .5, .95, (cx, cy + 5.45 * s, cz - 2.75 * s)), True)
    P.add(at(sc(torus(.75, .12, 12, 5)), (0, 5.45, -2.75)), soft('yellow', cy, top, .4, .6), True)
    # head: big squashed sphere
    hc = V3((0, 10.2, -.4)); HR = (4.6, 4.0, 4.1)
    P.add(at(sc(ell(*HR, 28, 18)), hc), soft(body, cy, top, .45, .92, (cx, cy + 10.2 * s, cz - .4 * s)), True)
    # cheek fluff
    for sx in (-1, 1):
        P.add(at(sc(puff(1.3, 7 + sx, 5, .15, 12, 8, .8)), (sx * 4.0, 8.8, -1.0)), soft(body, cy, top, .55, .9), True)
    # ears: tall rounded cones tilted out, pink inner
    for sx in (-1, 1):
        ear = lathe([(0, 0), (1.55, .3), (1.6, 1.8), (1.25, 3.4), (.7, 4.5), (0, 5.0)], 16)
        bmesh.ops.scale(ear, vec=V3((1, 1, .6)), verts=ear.verts)
        inn = lathe([(0, 0), (1.0, .4), (1.0, 1.8), (.75, 3.2), (0, 4.1)], 12)
        bmesh.ops.scale(inn, vec=V3((1, 1, .35)), verts=inn.verts); T(inn, (0, .2, -.75))
        for bm, col, a, b in ((ear, body, .5, .9), (inn, inner, .55, .85)):
            T(bm, (0, 0, 0), 0, 0, -sx * 24); T(bm, (sx * 2.5, 13.0, -.3))
            P.add(at(sc(bm), (0, 0, 0)), soft(col, cy, top, a, b), True)
    # face (front = -Z): every piece is laid on the head surface along its normal
    def surf(x, y):
        t = 1 - ((x - hc.x) / HR[0]) ** 2 - ((y - hc.y) / HR[1]) ** 2
        p = V3((x, y, hc.z - HR[2] * math.sqrt(max(t, 0))))
        n = V3(((p.x - hc.x) / HR[0] ** 2, (p.y - hc.y) / HR[1] ** 2, (p.z - hc.z) / HR[2] ** 2)).normalized()
        return p, n
    def stick(bm, x, y, push):
        p, n = surf(x, y); q = V3((0, 0, -1)).rotation_difference(n)
        bmesh.ops.rotate(bm, cent=V3(), matrix=q.to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=p + n * push, verts=bm.verts)
        return at(sc(bm), (0, 0, 0))
    for sx in (-1, 1):
        ex, ey = sx * 1.75, 10.5
        P.add(stick(ell(.95, 1.3, .5, 16, 10), ex, ey, -.12), soft('dark', cy + 9, cy + 12, .1, .32), True)
        P.add(stick(T(ell(.36, .44, .18, 10, 6), (-.3, .45, -.42)), ex, ey, -.12), flat('cloud', .94, 0), True)
        P.add(stick(T(ell(.17, .19, .12, 8, 4), (.36, -.5, -.4)), ex, ey, -.12), flat('cloud', .9, 0), True)
        P.add(stick(ell(.85, .45, .2, 12, 4), sx * 2.85, 8.85, -.04), soft(inner, cy, top, .55, .72), True)
    P.add(stick(ell(.42, .3, .3, 10, 6), 0, 9.4, -.05), soft(inner, cy, top, .35, .55), True)
    for sx in (-1, 1):
        mp = [V3((sx * k * .55, -math.sin(k * math.pi) * .35, 0)) for k in (0, .25, .5, .75, 1.0)]
        P.add(stick(tube(mp, .12, sides=5), 0, 8.7, .02), flat('dark', .25, 0), True)

def pet_fountain():
    """hub hero: 3-tier pastel fountain (scalloped basin, water, mid bowl with a pale water veil and foam ring, top bowl
    with a short veil) and the giant Puffpaw statue sitting on a quilted cushion at the top, waving at the plaza.
    Front -Z; the map turns it to face spawn."""
    P = Prop('PetFountain')
    R0 = 19.0
    P.add(lathe([(R0 - 3.2, -1.0), (R0 + .4, -1.0), (R0 + 1.2, .6), (R0 + 1.3, 2.4), (R0 + .9, 3.4), (R0 - .2, 3.7),
                 (R0 - 1.2, 3.3), (R0 - 1.5, 1.8), (R0 - 1.6, .9), (R0 - 3.2, .9)], 64), soft('pink', -1, 4, .4, .82), True)
    for i in range(32):
        a = i * math.tau / 32
        P.add(T(ell(1.4, .9, 1.0, 10, 6), (math.cos(a) * (R0 - .1), 3.75, math.sin(a) * (R0 - .1)), -math.degrees(a)),
              soft('cream', 2.8, 4.6, .55, .95), True)
    P.add(lathe([(R0 - 1.4, 2.0), (0, 2.0)], 48), vsh('water', lambda p, n: .58 + .1 * math.sin(math.hypot(p.x, p.z) * .8)), True)
    rng = random.Random(3)
    for i in range(14):
        a = rng.uniform(0, math.tau); r = rng.uniform(4, 9)
        P.add(T(rcyl(.55, .14, 8, .05, 1), (math.cos(a) * r, 2.0, math.sin(a) * r), 0, rng.uniform(-8, 8), rng.uniform(-8, 8)), soft('yellow', 1.9, 2.3, .6, .9), True)
    def veil(rt, yt, rb, yb, n=48):
        """pale water sheet (both faces) falling from (rt, yt) to (rb, yb), vertical streaks, foam puffs at the foot"""
        o = lathe([(rt, yt), (lerp(rt, rb, .45), lerp(yt, yb, .3)), (lerp(rt, rb, .85), lerp(yt, yb, .75)), (rb, yb)], n)
        i_ = lathe([(rb - .35, yb), (lerp(rt, rb, .85) - .35, lerp(yt, yb, .75)), (lerp(rt, rb, .45) - .35, lerp(yt, yb, .3)), (rt - .3, yt)], n)
        for bm in (o, i_):
            for f in list(bm.faces):
                if len(f.verts) > 4: bm.faces.remove(f)
            P.add(bm, vsh('water', lambda p, nn: .72 + .16 * clamp((p.y - yb) / max(yt - yb, 1)) + .07 * math.sin(math.atan2(p.z, p.x) * 22)), True)
        m = max(10, int(rb * 1.6))
        for k in range(m):
            a = k * math.tau / m
            P.add(T(puff(1.1, 50 + k, 4, .2, 10, 6, .55, .4), (math.cos(a) * rb, yb + .2, math.sin(a) * rb)), soft('cloud', yb, yb + 1.5, .65, .95), True)
    # stem with candy rings
    P.add(lathe([(6.2, .8), (6.0, 2.3), (4.4, 2.9), (3.4, 3.6), (3.2, 5.0), (4.0, 5.6)], 32), soft('cream', .8, 6, .45, .85), True)
    P.add(T(torus(3.3, .45, 32, 8), (0, 4.2, 0)), soft('mint', 3.7, 4.7, .45, .8), True)
    # mid bowl + veil into the basin
    R1 = 10.5
    P.add(lathe([(3.8, 5.4), (7.0, 6.0), (R1, 7.4), (R1 + .7, 8.3), (R1 + .3, 9.0), (R1 - .6, 8.9), (R1 - .9, 8.4), (0, 8.4)], 48),
          soft('sky', 5.4, 9.1, .4, .85), True)
    for i in range(24):
        a = i * math.tau / 24
        P.add(T(ell(1.0, .7, .8, 10, 6), (math.cos(a) * (R1 + .3), 9.0, math.sin(a) * (R1 + .3)), -math.degrees(a)), soft('cream', 8.4, 9.8, .55, .95), True)
    P.add(lathe([(R1 - .8, 8.55), (0, 8.55)], 40), flat('water', .66, 0), True)
    veil(R1 + 1.05, 8.4, R1 + 2.6, 2.0)
    # upper stem + top bowl + short veil into the mid bowl
    P.add(lathe([(2.6, 8.4), (2.2, 10.0), (2.3, 12.6), (3.4, 13.4)], 24), soft('cream', 8, 13.5, .45, .85), True)
    P.add(T(torus(2.3, .35, 24, 8), (0, 11.0, 0)), soft('pink', 10.4, 11.6, .45, .8), True)
    R2 = 7.4
    P.add(lathe([(2.4, 13.2), (5.0, 13.8), (R2, 15.0), (R2 + .5, 15.8), (R2 + .1, 16.4), (R2 - .6, 16.2), (0, 16.2)], 40), soft('pink', 13, 16.6, .42, .85), True)
    for i in range(18):
        a = i * math.tau / 18
        P.add(T(ell(.8, .55, .65, 8, 5), (math.cos(a) * (R2 + .1), 16.35, math.sin(a) * (R2 + .1)), -math.degrees(a)), soft('cream', 15.8, 17.1, .55, .95), True)
    veil(R2 + .75, 16.0, R2 + 1.9, 8.55, 40)
    return P

def pet_statue():
    """the Puffpaw statue + its quilted cushion: a separate MeshPart sharing the fountain's origin (the hero is split
    under the 20k-triangle MeshPart cap). Place at the same CFrame as PetFountain."""
    P = Prop('PetStatue')
    P.add(T(puff(6.3, 11, 8, .08, 24, 10, .36, .6), (0, 17.3, 0)), soft('lilac', 16, 20, .45, .85), True)
    for i in range(4):
        a = i * math.tau / 4 + math.pi / 4
        P.add(T(ell(.7, .7, .7, 8, 6), (math.cos(a) * 5.9, 16.6, math.sin(a) * 5.9)), soft('yellow', 16, 18, .5, .9), True)
    puffpaw(P, (0, 18.7, .3), 1.45)
    return P

# ------------------------------------------------------------------ HERO 2: rainbow arch over the hatchery
def rainbow_arch(R=26.0):
    """6 chunky pastel bands on a half circle, standing on two big cloud feet, sparkle stars on the crown. Front -Z,
    the arch spans X (-R..R)."""
    P = Prop('RainbowArch')
    cols = ('red', 'orange', 'yellow', 'leaf', 'sky', 'lilac')
    w = 1.45
    for i, col in enumerate(cols):
        r = R - i * w
        pts = [V3((math.cos(a) * r, 2.5 + math.sin(a) * r, 0)) for a in [math.pi * k / 30 for k in range(31)]]
        P.add(tube(pts, w * .62, sides=10, flat=(1.3, 1.12)), soft(col, 0, R + 3, .5, .88), True)
    for sx in (-1, 1):
        x = sx * (R - 3.6)
        for k, (dx, dy, dz, r) in enumerate(((0, 2.8, 0, 6.0), (sx * 4.2, 1.8, -2.6, 4.2), (-sx * 3.6, 1.6, 2.8, 4.0),
                                            (sx * 1.2, 5.8, 1.2, 4.0), (-sx * 2.4, 4.2, -3.2, 3.4), (sx * 4.4, 1.4, 2.6, 3.2))):
            P.add(T(puff(r, 20 + k + sx, 6, .16, 18, 11, .82), (x + dx, dy, dz)), soft('cloud', 0, 9, .55, .95), True)
    for k in range(5):
        a = math.pi * (.2 + .15 * k)
        r = R + 2.0 + (1.2 if k % 2 else 0)
        P.gadd(T(star(1.3 if k == 2 else .9, .6), (math.cos(a) * r, 2.5 + math.sin(a) * r, 0), 0, 0, k * 11), 'star')
    return P

# ------------------------------------------------------------------ stations
def pet_shop():
    """open-front kiosk: round dais, curved back wall with toy shelves, 4 chubby pillars, curved counter in front, a
    candy-striped scalloped dome awning and a giant pet-food bowl + bone icon on top. Front -Z (counter side)."""
    P = Prop('PetShop')
    R = 9.0
    P.add(rcyl(R + 1.2, 1.2, 32, .4, 2, -.6), soft('cream', -.6, .6, .45, .8), True)
    P.add(T(torus(R + 1.2, .3, 48, 6), (0, .55, 0)), soft('pink', 0, 1, .5, .8), True)
    # back wall: half ring (angles 0..pi on the +Z side), rounded top
    bm = bmesh.new(); N = 20; rows = []
    for i in range(N + 1):
        a = math.pi * i / N
        rows.append([bm.verts.new((math.cos(a) * rr, y, math.sin(a) * rr)) for rr, y in ((R - .2, .6), (R - .2, 9.2), (R - .7, 9.7), (R - 1.2, 9.2), (R - 1.2, .6))])
    for A, Bq in zip(rows, rows[1:]):
        for k in range(4): bm.faces.new((A[k], Bq[k], Bq[k + 1], A[k + 1]))
    bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, soft('cream', 0, 10, .5, .88), True)
    # shelves with toy balls on the inner wall
    for y in (3.2, 5.8):
        bm = bmesh.new(); rows = []
        for i in range(N + 1):
            a = math.pi * (.08 + .84 * i / N)
            rows.append([bm.verts.new((math.cos(a) * rr, yy, math.sin(a) * rr)) for rr, yy in ((R - 1.2, y), (R - 2.6, y), (R - 2.6, y + .35), (R - 1.2, y + .35))])
        for A, Bq in zip(rows, rows[1:]):
            for k in range(3): bm.faces.new((A[k], Bq[k], Bq[k + 1], A[k + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        P.add(bm, soft('wood', y, y + .4, .55, .8), True)
        for k in range(7):
            a = math.pi * (.15 + .7 * k / 6); col = ('red', 'sky', 'yellow', 'mint', 'lilac', 'orange', 'pink')[(k + int(y)) % 7]
            r = .55 if k % 2 else .7
            P.add(T(ell(r, r, r, 10, 6), (math.cos(a) * (R - 1.9), y + .35 + r, math.sin(a) * (R - 1.9))), soft(col, y, y + 2, .45, .9), True)
    # pillars at the open front corners + mid
    for a in (math.radians(-10), math.radians(190), math.radians(-60), math.radians(240)):
        x, z = math.cos(a) * (R - .4), math.sin(a) * (R - .4)
        P.add(T(rcyl(.85, 9.4, 12, .3, 1), (x, .5, z)), soft('pink', 0, 10, .45, .85), True)
        for y in (2.6, 6.8):
            P.add(T(torus(.9, .22, 12, 5), (x, y, z)), soft('cream', y - .3, y + .3, .55, .9), True)
    # curved counter (front arc), top board + front kick
    bm = bmesh.new(); rows = []
    for i in range(N + 1):
        a = math.pi + math.radians(30) + math.radians(120) * i / N
        rows.append([bm.verts.new((math.cos(a) * rr, y, math.sin(a) * rr)) for rr, y in ((R - 2.0, .6), (R - 2.0, 3.6), (R - 3.4, 3.6), (R - 3.4, .6))])
    for A, Bq in zip(rows, rows[1:]):
        for k in range(3): bm.faces.new((A[k], Bq[k], Bq[k + 1], A[k + 1]))
    bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bevel(bm, .2, 1), soft('sky', .6, 3.8, .45, .85), True)
    bm = bmesh.new(); rows = []
    for i in range(N + 1):
        a = math.pi + math.radians(28) + math.radians(124) * i / N
        rows.append([bm.verts.new((math.cos(a) * rr, y, math.sin(a) * rr)) for rr, y in ((R - 1.6, 3.6), (R - 1.6, 4.1), (R - 3.8, 4.1), (R - 3.8, 3.6))])
    for A, Bq in zip(rows, rows[1:]):
        for k in range(3): bm.faces.new((A[k], Bq[k], Bq[k + 1], A[k + 1]))
    bm.faces.new(rows[0]); bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, soft('cream', 3.5, 4.2, .6, .9), True)
    # counter goodies: treat jar + bowl
    P.add(T(lathe([(0, 0), (.9, .05), (1.0, 1.2), (.7, 1.6), (.75, 1.9), (0, 1.95)], 12), (-2.4, 4.1, -5.8)), soft('sky', 4, 6, .55, .9), True)
    P.add(T(ell(.8, .5, .8, 12, 6), (-2.4, 6.1, -5.8)), soft('red', 5.6, 6.6, .5, .9), True)
    P.add(T(lathe([(0, 0), (1.2, 0), (1.4, .7), (1.1, .7), (0, .3)], 14), (2.6, 4.1, -5.6)), soft('pink', 4, 5, .5, .85), True)
    # dome awning: stripes alternate pink / cream by angle, scalloped skirt
    NS = 48; rows = []; bm = bmesh.new()
    prof = [(R + 2.0, 9.4), (R + 1.7, 10.6), (R + .4, 12.4), (R - 2.6, 14.2), (R - 5.5, 15.2), (0, 15.6)]
    for r0, y in prof:
        if r0 <= 0: rows.append([bm.verts.new((0, y, 0))]); continue
        ring = []
        for i in range(NS):
            a = i * math.tau / NS
            sc_ = 1.0
            if y < 9.5: sc_ = 1 - .06 * (1 - abs(math.cos(a * NS / 4)))
            ring.append(bm.verts.new((math.cos(a) * r0 * sc_, y - (0.6 * abs(math.sin(a * NS / 4)) if y < 9.5 else 0), math.sin(a) * r0 * sc_)))
        rows.append(ring)
    for A, Bq in zip(rows, rows[1:]):
        for i in range(NS):
            j = (i + 1) % NS
            if len(Bq) == 1: bm.faces.new((A[i], A[j], Bq[0]))
            else: bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bm.faces.new(list(reversed(rows[0])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    upk, uck = PAL.u('pink'), PAL.u('cream')
    def awn(f):
        c = f.calc_center_median(); a = math.atan2(c.z, c.x) % math.tau
        u = upk if int(a / (math.tau / 12)) % 2 == 0 else uck
        return [(u, clamp(.45 + .45 * clamp((l.vert.co.y - 9) / 7) + .1 * f.normal.dot(SUN), .05, .95)) for l in f.loops]
    P.add(bm, awn, True)
    P.add(T(torus(R + 1.95, .45, 48, 8), (0, 9.6, 0)), soft('yellow', 9, 10.2, .5, .85), True)
    # roof icon: pet bowl + bone
    P.add(T(lathe([(0, 0), (2.4, 0), (3.0, 1.6), (2.7, 1.8), (2.2, .6), (0, .5)], 20), (0, 15.3, 0)), soft('red', 15, 17.2, .45, .85), True)
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(T(ell(.85, .85, .85, 10, 6), (sx * 2.3, 0, sz * .7)), (0, 17.2, 0), 25, 0, 14), soft('cream', 16, 19.2, .55, .95), True)
    P.add(T(pill((-2.0, 0, 0), (2.0, 0, 0), .55, 10, 2), (0, 17.2, 0), 25, 0, 14), soft('cream', 16, 19, .55, .95), True)
    return P

def upgrade_machine():
    """giant gumball machine: rounded red drum base (coin plate, glowing up-chevron, chute + cup, crank), a big
    pale globe studded with gumballs, red cap + a star finial. Front -Z."""
    P = Prop('UpgradeMachine')
    P.add(lathe([(0, -.4), (5.6, -.4), (6.0, .4), (5.8, 1.2), (4.6, 1.6), (4.4, 6.6), (5.4, 7.4), (5.5, 8.2), (4.6, 8.6), (0, 8.6)], 32),
          soft('red', -.4, 8.6, .4, .85, (0, 4, 0)), True)
    for y in (2.2, 5.6):
        P.add(T(torus(4.5, .28, 32, 6), (0, y, 0)), soft('yellow', y - .3, y + .3, .5, .85), True)
    # coin plate + slot + chute + cup (front)
    P.add(T(rbox((2.6, 2.0, .6), .25, 2), (0, 4.2, -4.4)), soft('yellow', 3, 5.2, .5, .9), True)
    P.add(T(rbox((1.3, .25, .3), .1, 1), (0, 4.4, -4.75)), flat('dark', .3), True)
    chev = ngon_prism([(-1.2, -.4), (0, .8), (1.2, -.4), (1.2, -1.1), (0, .1), (-1.2, -1.1)], -.15, .15, 0)
    P.gadd(T(chev, (0, 6.6, -4.62), 0, -90), 'arrow')
    P.add(T(rbox((2.4, 1.6, 1.4), .45, 2), (0, 1.9, -5.0)), soft('cream', 1, 2.8, .5, .9), True)
    P.add(T(rbox((1.6, .9, .8), .3, 1), (0, 2.1, -5.55)), flat('dark', .35), True)
    # crank on the right side
    crank = rcyl(1.1, .6, 14, .2, 1); T(crank, (0, 0, 0), 0, 0, -90); T(crank, (4.6, 4.2, 0))
    P.add(crank, soft('yellow', 3, 5.4, .5, .9), True)
    P.add(pill((5.4, 4.2, 0), (5.4, 4.2, -1.8), .28, 8, 2), soft('cream', 3, 5.4, .5, .85), True)
    P.add(T(ell(.55, .55, .55, 10, 6), (5.4, 4.2, -2.2)), soft('red', 3.5, 5, .5, .9), True)
    # globe + gumballs
    GC = V3((0, 14.4, 0)); GR = 6.4
    P.add(T(ell(GR, GR, GR, 32, 20), GC), soft('cloud', GC.y - GR, GC.y + GR, .55, .95, GC, .1), True)
    rng = random.Random(5); cols = ('red', 'yellow', 'sky', 'mint', 'pink', 'orange', 'lilac')
    for i in range(46):
        y = rng.uniform(-.75, .55); a = rng.uniform(0, math.tau); rr = math.sqrt(1 - y * y)
        d = V3((math.cos(a) * rr, y, math.sin(a) * rr)); r = rng.uniform(.95, 1.25)
        P.add(T(ell(r, r, r, 10, 6), GC + d * (GR - r * .45)), soft(cols[i % 7], GC.y - GR, GC.y + GR, .5, .9, GC + d * (GR - r * .45)), True)
    P.add(T(torus(GR * .78, .45, 32, 8), GC + V3((0, -GR * .63, 0))), soft('red', 8, 11, .45, .8), True)
    # cap + star
    P.add(lathe([(0, 19.6), (3.6, 19.6), (4.2, 20.4), (3.6, 21.6), (1.2, 22.4), (0, 22.5)], 24), soft('red', 19.5, 22.6, .45, .85), True)
    P.add(T(rcyl(.45, 1.2, 8, .1, 1), (0, 22.2, 0)), soft('yellow', 22, 23.5, .5, .8), True)
    P.add(T(star(1.6, .9), (0, 24.6, 0)), soft('yellow', 23, 26.2, .55, .95), True)
    return P

def trade_booth(col='sky'):
    """round trade table with a big scalloped two-tone umbrella and two chubby stools. Front -Z."""
    P = Prop('TradeBooth_' + col)
    P.add(lathe([(0, -.3), (1.6, -.3), (1.7, .3), (.6, .8), (.5, 3.0), (3.3, 3.1), (3.5, 3.6), (3.3, 3.9), (0, 3.9)], 20), soft('cream', -.3, 4, .45, .85), True)
    P.add(T(torus(3.4, .22, 24, 5), (0, 3.5, 0)), soft(col, 3, 4, .5, .85), True)
    for sx in (-1, 1):
        P.add(T(lathe([(0, -.3), (1.1, -.3), (1.2, .2), (.7, .5), (.6, 1.8), (1.25, 2.0), (1.3, 2.6), (1.0, 2.9), (0, 3.0)], 14), (sx * 5.0, 0, 0)), soft(col, -.3, 3, .45, .85), True)
    # pole + umbrella
    P.add(T(rcyl(.3, 7.6, 8, .1, 1), (0, 3.9, 0)), soft('wood', 3, 12, .5, .8), True)
    NS = 32; bm = bmesh.new(); rows = []
    for r0, y in ((6.6, 10.4), (6.2, 10.9), (4.4, 12.0), (2.2, 12.8), (0, 13.1)):
        if r0 <= 0: rows.append([bm.verts.new((0, y, 0))]); continue
        rows.append([bm.verts.new((math.cos(i * math.tau / NS) * r0, y - (.5 * abs(math.sin(i * math.tau / NS * 4)) if y < 10.5 else 0),
                                   math.sin(i * math.tau / NS) * r0)) for i in range(NS)])
    for A, Bq in zip(rows, rows[1:]):
        for i in range(NS):
            j = (i + 1) % NS
            if len(Bq) == 1: bm.faces.new((A[i], A[j], Bq[0]))
            else: bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bm.faces.new(list(reversed(rows[0])))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    ua, ub = PAL.u(col), PAL.u('cream')
    def umb(f):
        c = f.calc_center_median(); a = math.atan2(c.z, c.x) % math.tau
        u = ua if int(a / (math.tau / 8)) % 2 == 0 else ub
        return [(u, clamp(.45 + .4 * clamp((l.vert.co.y - 10) / 3) + .12 * f.normal.dot(SUN), .05, .95)) for l in f.loops]
    P.add(bm, umb, True)
    P.add(T(ell(.6, .6, .6, 10, 6), (0, 13.4, 0)), soft('yellow', 13, 14, .5, .9), True)
    # trade goods on the table: two pet treat boxes
    P.add(T(rbox((1.4, 1.0, 1.0), .3, 2), (-1.2, 3.9, -.4)), soft('pink', 3.9, 5, .5, .9), True)
    P.add(T(ell(.65, .65, .65, 10, 6), (1.2, 4.55, .2)), soft('yellow', 3.9, 5.2, .5, .9), True)
    return P

def trade_pad():
    """flat trade circle: cream disc with a pastel rim and two glowing curved swap arrows (walk over, no collision)"""
    P = Prop('TradePad')
    P.add(rcyl(7.0, .5, 40, .2, 2, -.3), soft('cream', -.3, .2, .55, .85), True)
    P.add(T(torus(7.0, .35, 48, 6), (0, .2, 0)), soft('mint', 0, .5, .5, .85), True)
    for k in range(2):
        a0 = k * math.pi + .35; a1 = a0 + math.pi - .9
        pts = arc_pts(4.2, a0, a1, 14, .3)
        P.gadd(tube(pts, .55, sides=6, flat=(1, .35)), 'trade')
        tip = pts[-1]; d = (pts[-1] - pts[-2]).normalized(); nrm = V3((-d.z, 0, d.x))
        tri = [tip + d * 1.8, tip + nrm * 1.4, tip - nrm * 1.4]
        bm = ngon_prism([(p.x, p.z) for p in tri], .2, .5, 0)
        P.gadd(bm, 'trade')
    return P

def leaderboard():
    """blank board in a chunky rounded frame on two candy posts, a crown icon on top. Face -Z (blank cream panel)."""
    P = Prop('LeaderboardFrame')
    W, Hh, y0 = 18.0, 11.0, 4.0
    for sx in (-1, 1):
        P.add(T(rcyl(.9, y0 + Hh + .6, 12, .3, 1), (sx * (W / 2 + .4), -.4, .4)), soft('lilac', 0, 16, .45, .85), True)
        P.add(T(ell(1.3, 1.3, 1.3, 12, 8), (sx * (W / 2 + .4), y0 + Hh + 1.5, .4)), soft('yellow', 14, 18, .5, .95), True)
        P.add(T(lathe([(0, -.4), (1.8, -.4), (1.9, .3), (1.2, .7), (0, .8)], 14), (sx * (W / 2 + .4), 0, .4)), soft('lilac', -.4, 1, .45, .8), True)
    P.add(T(rbox((W, Hh, .5), .2, 1), (0, y0 + Hh / 2, .55)), flat('cream', .9, .02), True)
    frame = [((0, y0 + Hh + .45), (W + 1.4, 1.2)), ((0, y0 - .45), (W + 1.4, 1.2)), ((-W / 2 - .2, y0 + Hh / 2), (1.2, Hh + 1.6)), ((W / 2 + .2, y0 + Hh / 2), (1.2, Hh + 1.6))]
    for (x, y), (w, h) in frame:
        P.add(T(rbox((w, h, 1.3), .5, 2), (x, y, .4)), soft('sky', y0 - 1, y0 + Hh + 1, .45, .85), True)
    for sx in (-1, 1):
        for y in (y0 - .45, y0 + Hh + .45):
            P.add(T(ell(.65, .65, .65, 10, 6), (sx * (W / 2 + .2), y, -.3)), soft('pink', y - 1, y + 1, .5, .9), True)
    # crown
    cy = y0 + Hh + 1.1
    P.add(T(rcyl(3.2, 1.2, 20, .35, 2), (0, cy, .4)), soft('yellow', cy, cy + 4, .45, .85), True)
    for k in range(5):
        x = -2.6 + k * 1.3; h = 2.4 if k % 2 == 0 else 1.6
        P.add(T(lathe([(0, 0), (.75, .1), (.45, h * .8), (0, h)], 8), (x, cy + 1.0, .4)), soft('yellow', cy, cy + 4, .5, .9), True)
        P.add(T(ell(.4, .4, .4, 8, 6), (x, cy + 1.1 + h, .4)), soft('pink' if k % 2 else 'sky', cy, cy + 4, .55, .95), True)
    return P

EGG_KINDS = {   # kind: (shell, deco, deco colour, ring glow, pedestal accent)
    'basic':   ('cream', 'spots', 'leaf', 'ring_green', 'leaf'),
    'spotted': ('sky', 'spots', 'cloud', 'ring_sky', 'sky'),
    'golden':  ('yellow', 'stars', 'cloud', 'ring_gold', 'yellow'),
    'meadow':  ('leaf', 'flowers', 'cloud', 'ring_green', 'grass'),
    'candy':   ('pink', 'swirl', 'cloud', 'ring_pink', 'pink'),
    'crystal': ('lilac', 'gems', 'cloud', 'ring_lilac', 'lilac'),
}
def egg_stand(kind='basic'):
    """fluted cake pedestal with a glowing ring under a giant decorated egg; 3 little step pads in front. Front -Z."""
    shell, deco, dcol, ring, acc = EGG_KINDS[kind]
    P = Prop('EggStand_' + kind)
    P.add(rcyl(4.6, 1.0, 24, .4, 2, -.4), soft('cream', -.4, .6, .45, .8), True)
    prof = [(3.8, .6), (3.6, 1.2)]
    bm = lathe(prof + [(3.0, 1.5), (2.4, 2.0), (2.2, 3.6), (2.8, 4.0), (3.6, 4.3), (3.7, 4.9), (3.2, 5.2), (0, 5.2)], 24)
    for v in bm.verts:
        if 1.9 < v.co.y < 3.7:
            a = math.atan2(v.co.z, v.co.x); k = 1 + .08 * math.cos(a * 8)
            v.co.x *= k; v.co.z *= k
    P.add(bm, soft(acc, .6, 5.2, .45, .85, (0, 3, 0)), True)
    P.gadd(T(torus(3.75, .28, 32, 6), (0, 4.6, 0)), ring)
    P.gadd(T(torus(4.75, .2, 32, 6), (0, .55, 0)), ring)
    P.add(T(puff(2.2, 9, 6, .1, 16, 8, .45, .5), (0, 5.4, 0)), soft('cream', 5, 6.5, .55, .9), True)
    egg(P, (0, 5.6, 0), 2.8, 7.4, shell, deco, dcol, seed=3)
    return P

def zone_gate(acc='leaf', lock=True, name=None):
    """toll arch: two chubby stacked pillars with paw-ball finials, a rounded arch beam with bead ornaments, a padlock
    icon hanging in the middle (the scripted barrier fills the 16 x 13 opening), a coin toll podium on the left.
    Built facing -Z: walk through along Z."""
    P = Prop('ZoneGate_' + (name or acc))
    hw = 9.0
    for sx in (-1, 1):
        x = sx * (hw + 1.8)
        P.add(T(rcyl(2.9, 1.4, 20, .45, 2, -.6), (x, 0, 0)), soft('cream', -.6, 1, .45, .8), True)
        P.add(T(lathe([(2.3, .7), (2.0, 2.0), (1.9, 10.5), (2.4, 11.4), (2.5, 12.6), (2.0, 13.2), (0, 13.3)], 20), (x, 0, 0)), soft(acc, .7, 13.3, .42, .85), True)
        for y in (3.2, 6.6, 10.0):
            P.add(T(torus(2.0, .38, 20, 6), (x, y, 0)), soft('cream', y - .5, y + .5, .55, .9), True)
        P.add(T(ell(2.3, 2.3, 2.3, 18, 12), (x, 15.1, 0)), soft('cream', 13, 17.5, .5, .95, (x, 15.1, 0)), True)
        paw(P, (x, 15.2, -2.15), .62, 'pink' if acc != 'pink' else 'lilac', 0, 90, .22, 8)
    # arch beam: a fat curved tube between the pillar tops
    pts = [V3((math.cos(a) * (hw + 1.8), 12.2 + math.sin(a) * 4.0, 0)) for a in [math.pi * k / 18 for k in range(19)]]
    P.add(tube(pts, .95, sides=10, flat=(1.0, 1.25)), soft(acc, 11, 17, .45, .88), True)
    for k in range(1, 18, 2):
        p = pts[k] + V3((0, 0, -1.05))
        P.add(T(ell(.42, .42, .42, 8, 6), p), soft(('yellow', 'pink', 'sky')[k // 2 % 3], 11, 17, .55, .95), True)
    if lock:
        lc = V3((0, 13.0, -.4))
        P.add(T(torus(.95, .3, 14, 6), lc + V3((0, 1.2, 0)), 0, 90), soft('stone', 12, 15, .5, .85), True)
        P.add(T(rbox((2.6, 2.2, 1.0), .45, 2), lc), soft('yellow', 11.8, 14.2, .5, .95), True)
        P.add(T(ell(.3, .45, .15, 8, 4), lc + V3((0, .05, -.5))), flat('dark', .3), True)
        P.add(pill(lc + V3((0, 2.1, 0)), lc + V3((0, 16.2 - 13.0 - .2, 0)), .14, 5, 1), soft('stone', 13, 16, .5, .8), True)
    # toll podium (left of the opening, outside face)
    tx, tz = -(hw + 1.8) - .3, -4.6
    P.add(T(lathe([(0, -.4), (1.9, -.4), (2.0, .3), (1.3, .7), (1.1, 3.0), (1.7, 3.4), (1.6, 3.9), (0, 3.9)], 16), (tx, 0, tz)), soft('cream', -.4, 4, .45, .85), True)
    P.add(T(rcyl(1.2, .35, 14, .12, 1), (tx, 3.9, tz)), soft('yellow', 3.8, 4.4, .5, .9), True)
    for i, (dx, dz, dy) in enumerate(((0, 0, 0), (.5, .2, .3), (-.3, .4, .6), (.1, -.3, .9))):
        P.add(T(rcyl(.6, .25, 10, .08, 1), (tx + dx, 4.25 + dy, tz + dz), 0, i * 9, i * 7), soft('yellow', 4, 5.5, .6, .95), True)
    return P

def spawn_pad():
    """round spawn dais: two soft tiers, mint rim, a big paw-print inlay. Walkable (precise)."""
    P = Prop('SpawnPad')
    P.add(rcyl(8.0, .9, 40, .35, 2, -.5), soft('cream', -.5, .4, .45, .78), True)
    P.add(rcyl(6.2, .6, 40, .25, 2, .35), soft('sky', .3, 1.0, .5, .85), True)
    P.add(T(torus(6.25, .28, 48, 6), (0, .7, 0)), soft('cloud', .4, 1, .6, .95), True)
    paw(P, (0, .95, 0), 1.9, 'cloud', 0, 0, .14, 12)
    return P

def bridge(n=1, L=70.0, rise=2.0, theme='meadow', drop=0.0):
    """humped chunky bridge along -Z (start z = 0 .. end z = -L), deck rises by `rise`; rounded planks across, posts
    with ball caps every 7 studs, fat rope-like rails. Theme sets the colours. drop > 0: two pairs of round piers stand
    in the lagoon under the span (down to `drop` below the deck start), so the bridge rests on something"""
    rail, plank, ball = {'meadow': ('leaf', 'wood', 'yellow'), 'candy': ('pink', 'cream', 'mint'), 'crystal': ('lilac', 'cream', 'sky')}[theme]
    P = Prop('Bridge_%d' % n)
    W = 13.0
    def yat(t): return rise * t + 3.2 * math.sin(math.pi * t)
    nP = int(L / 1.7)
    for i in range(nP):
        t = (i + .5) / nP; z = -L * t; y = yat(t)
        y2 = yat(min(1, t + .01)); slope = math.degrees(math.atan2(y2 - y, L * .01))
        bm = rbox((W, .55, 1.45), .2, 1); T(bm, (0, 0, 0), 0, slope); T(bm, (0, y - .1, z))
        h = B.h01(i, 1, 2)
        P.add(bm, vsh(plank, lambda p, nn, h=h: .5 + .15 * h + .2 * nn.y), True)
    # under-beams (2 stringers) so the deck reads thick from the side
    for sx in (-1, 1):
        pts = [V3((sx * (W / 2 - 1.2), yat(t) - .9, -L * t)) for t in [k / 16 for k in range(17)]]
        P.add(tube(pts, .55, sides=6, flat=(1, 1.4)), soft('wood', -2, 8, .35, .6), True)
    if drop > 0:
        for t in (.3, .7):
            yb = yat(t) - 1.4
            for sx in (-1, 1):
                P.add(T(rcyl(1.1, yb + drop, 10, .3, 1), (sx * (W / 2 - 1.2), -drop, -L * t)), soft(rail, -drop, yb, .38, .7), True)
            P.add(T(rbox((W - 1.0, .7, 1.6), .25, 1), (0, yb - .2, -L * t)), soft('wood', yb - 1, yb, .4, .6), True)   # cap beam
    nposts = max(3, int(L / 7) + 1)
    for sx in (-1, 1):
        tops = []
        for k in range(nposts):
            t = k / (nposts - 1); z = -L * t; y = yat(t); x = sx * (W / 2 + .2)
            P.add(T(rcyl(.55, 3.4, 10, .2, 1), (x, y - .7, z)), soft(rail, y - 1, y + 3, .45, .85), True)
            P.add(T(ell(.75, .75, .75, 10, 6), (x, y + 3.0, z)), soft(ball, y + 2, y + 4, .55, .95), True)
            tops.append(V3((x, y + 2.3, z)))
        pts = []
        for a, b2 in zip(tops, tops[1:]):
            for k in range(4): pts.append(a.lerp(b2, k / 4) - V3((0, math.sin(math.pi * k / 4) * .35, 0)))
        pts.append(tops[-1])
        P.add(tube(pts, .32, sides=7), soft(rail, -2, 12, .5, .85), True)
    return P

# ------------------------------------------------------------------ breakables (cheap: < 300 tris)
def coin_pile(big=False):
    """low gold mound with a short coin stack and loose coins leaning on it"""
    P = Prop('CoinPile_' + ('L' if big else 'S'))
    s = 1.45 if big else 1.0
    P.add(lathe([(0, -.3), (2.5 * s, -.3), (2.3 * s, .4 * s), (1.4 * s, .95 * s), (0, 1.15 * s)], 10),
          vsh('yellow', lambda p, n: .62 + .28 * n.y), True)
    for i in range(3 if big else 2):                                  # stack
        P.add(T(cyl(.75 * s, .22 * s, 10, 0, None, 0), (.2 * s, 1.0 * s + i * .23 * s, 0), i * 13), flat('yellow', .82, .1), True)
    rng = random.Random(11 if big else 7)
    for i in range(4 if big else 3):                                  # leaning coins
        a = i * math.tau / (4 if big else 3) + .4; r = 1.75 * s
        P.add(T(T(cyl(.7 * s, .18 * s, 8, 0, None, 0), (0, 0, 0), 0, 0, 72), (math.cos(a) * r, .75 * s, math.sin(a) * r), -math.degrees(a)), flat('yellow', .84, .1), True)
    return P

def chest(gold=False):
    """rounded treasure chest: plank body, domed lid, metal bands + lock (gold = tier 3: gold bands + gem)"""
    P = Prop('Chest_' + ('T3' if gold else 'T2'))
    body, band = ('pink', 'yellow') if gold else ('wood', 'yellow')
    P.add(T(rbox((4.2, 2.4, 2.8), .35, 1), (0, .95, 0)), soft(body, -.2, 2.2, .45, .8), True)
    bm = bmesh.new(); rows = []
    for k in range(7):
        a = math.pi * k / 6
        rows.append([bm.verts.new((x, 2.1 + math.sin(a) * 1.25, -math.cos(a) * 1.4)) for x in (-2.1, 2.1)])
    for A, Bq in zip(rows, rows[1:]): bm.faces.new((A[0], A[1], Bq[1], Bq[0]))
    for sx, idx in ((-1, 0), (1, 1)):
        bm.faces.new([r[idx] for r in rows])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, soft(body, 2, 3.4, .55, .88), True)
    for x in (-1.3, 1.3):
        P.add(T(rbox((.45, 2.55, 2.95), .12, 1), (x, .95, 0)), soft(band, -.2, 2.4, .5, .85), True)
    P.add(T(rbox((1.0, 1.1, .45), .2, 1), (0, 1.9, -1.55)), soft(band, 1, 2.6, .55, .9), True)
    if gold: P.gadd(T(ell(.3, .3, .2, 6, 4), (0, 1.95, -1.82)), 'gem')
    return P

def gift_box(col='pink', rib='yellow'):
    """chubby present: soft box, crossing ribbon bands, a two-loop bow"""
    P = Prop('GiftBox_' + col)
    P.add(T(rbox((3.0, 2.6, 3.0), .4, 1), (0, 1.1, 0)), soft(col, -.2, 2.4, .45, .85), True)
    P.add(T(rbox((3.08, 2.68, .6), .15, 1), (0, 1.1, 0)), soft(rib, -.2, 2.4, .5, .9), True)
    P.add(T(rbox((.6, 2.68, 3.08), .15, 1), (0, 1.1, 0)), soft(rib, -.2, 2.4, .5, .9), True)
    for sx in (-1, 1):
        P.add(T(ell(.75, .5, .4, 6, 4), (sx * .65, 2.75, 0), 0, 0, sx * 25), soft(rib, 2.2, 3.4, .55, .9), True)
    P.add(T(ell(.35, .32, .35, 6, 4), (0, 2.6, 0)), soft(rib, 2.2, 3.2, .5, .8), True)
    return P

def crystal_clump(big=False):
    """lilac rock base with 4-5 glowing hex crystals (tier 2 / tier 3)"""
    P = Prop('CrystalClump_' + ('T3' if big else 'T2'))
    s = 1.5 if big else 1.0
    P.add(T(puff(1.8 * s, 3, 5, .15, 8, 5, .55, .4), (0, .35 * s, 0)), soft('stone', -.5, 1.5 * s, .4, .75), True)
    rng = random.Random(4 if big else 2)
    for k in range(5 if big else 4):
        a = k * math.tau / (5 if big else 4) + rng.uniform(-.3, .3); d = .3 if k == 0 else 1.0 * s
        h = (3.4 if k == 0 else rng.uniform(1.6, 2.4)) * s
        bm = B.lathe([(0, -.2), (.55 * s, 0), (.5 * s, h * .72), (0, h)], 6)
        T(bm, (0, 0, 0), 0, 0 if k == 0 else rng.uniform(15, 30)); T(bm, (0, 0, 0), math.degrees(-a) + 90)
        T(bm, (math.cos(a) * d * (.0 if k == 0 else 1), .3 * s, math.sin(a) * d * (0 if k == 0 else 1)))
        P.gadd(bm, 'crystal')
    return P


def bubble_crown(P, c, r, seed, col, n=6, a=.28, b=.88, nu=12, nv=7, core=(14, 8)):
    """chibi puffball crown: a core ball + n round bubbles on a fibonacci spiral over its upper part, all overlapping,
    shaded from the crown centre (dark underside, bright lit top) so it reads as ONE soft scalloped crown"""
    c = V3(c); rng = random.Random(seed)
    sh = soft(col, c.y - r * .8, c.y + r * .95, a, b, c, .16)
    P.add(T(ell(r * .78, r * .72, r * .78, core[0], core[1]), c), sh, True)
    for i in range(n):
        y = .95 - 1.25 * (i + .5) / n; rr = math.sqrt(max(0, 1 - y * y)); ang = i * 2.39996 + seed
        d = V3((math.cos(ang) * rr, y, math.sin(ang) * rr))
        br = r * rng.uniform(.42, .52)
        P.add(T(ell(br, br * .94, br, nu, nv), c + V3((d.x * r * .6, d.y * r * .55, d.z * r * .6))), sh, True)

# ------------------------------------------------------------------ foliage (soft regex names: Tree / Bush / Flower / Grass)
def puff_tree(seed=1, col='leaf', h=16.0, trunk='wood', tag=''):
    """lollipop / puffball tree: curved tapered trunk with a root flare, one big smooth lobed crown"""
    rng = random.Random(seed)
    P = Prop('PuffTree_%s%d%s' % ({'leaf': 'green'}.get(col, col), seed, tag))   # a tree, not a 'leaf' decal
    r = h * .36; cy = h - r * .82
    lean = V3((rng.uniform(-.06, .06), 0, rng.uniform(-.06, .06)))
    pts = [V3((0, -.8, 0))] + [V3((math.sin(t * 2.4 + seed) * h * .025, cy * t, 0)) + lean * cy * t for t in (.2, .45, .7, .95)]
    P.add(tube(pts, [h * .085, h * .066, h * .056, h * .05, h * .048], sides=9), soft(trunk, 0, cy, .4, .7), True)
    P.add(lathe([(h * .14, -.6), (h * .12, .1), (h * .085, .9), (h * .07, 1.8), (0, 2.0)], 9), soft(trunk, -1, 2, .32, .5), True)
    top = pts[-1]
    bubble_crown(P, (top.x, cy, top.z), r, seed, col)
    return P

def cotton_tree(seed=1, h=17.0):
    """candy tree: candy-striped trunk (stripe faces alternate), two-tone cotton-candy puff crown"""
    rng = random.Random(seed)
    P = Prop('CottonTree%d' % seed)
    r = h * .34; cy = h - r * .8
    pts = [V3((0, -.8, 0))] + [V3((math.sin(t * 2.0 + seed) * h * .03, cy * t, 0)) for t in (.25, .5, .75, 1.0)]
    rad = [h * .07, h * .06, h * .052, h * .048, h * .045]
    fine = []; frad = []
    for i in range(len(pts) - 1):
        for k in range(4): fine.append(pts[i].lerp(pts[i + 1], k / 4)); frad.append(lerp(rad[i], rad[i + 1], k / 4))
    fine.append(pts[-1]); frad.append(rad[-1])
    bm = tube(fine, frad, sides=10)
    up, uc = PAL.u('pink'), PAL.u('cream')
    def stripes(f):
        c = f.calc_center_median(); a = math.atan2(c.z, c.x)
        u = up if int((c.y * 1.1 + a / math.tau * 2) % 2) == 0 else uc
        return [(u, clamp(.5 + .2 * f.normal.dot(SUN), .05, .95))] * len(f.loops)
    P.add(bm, stripes, True)
    c1 = ('pink', 'sky', 'mint')[seed % 3]
    bubble_crown(P, (pts[-1].x, cy, 0), r, seed, c1, 7, .36, .92)
    return P

def crystal_tree(seed=1, h=15.0, col='lilac'):
    """dream tree: pale twisty trunk, lilac puff crown with glowing crystal points poking out"""
    rng = random.Random(seed)
    P = Prop('CrystalTree%d%s' % (seed, col))
    r = h * .34; cy = h - r * .8
    pts = [V3((0, -.8, 0))] + [V3((math.sin(t * 3 + seed) * h * .04, cy * t, math.cos(t * 3 + seed) * h * .03)) for t in (.25, .5, .75, 1.0)]
    P.add(tube(pts, [h * .07, h * .058, h * .05, h * .045, h * .042], sides=9), soft('cream', 0, cy, .45, .75), True)
    c = V3((pts[-1].x, cy, pts[-1].z))
    bubble_crown(P, c, r, seed + 3, col, 6, .3, .9)
    for k in range(5):
        d = V3((rng.gauss(0, 1), abs(rng.gauss(0, 1)) + .3, rng.gauss(0, 1))).normalized()
        bm = B.lathe([(0, 0), (.8, .3), (.65, 2.2), (0, 3.2)], 6)
        q = V3((0, 1, 0)).rotation_difference(d); bmesh.ops.rotate(bm, cent=V3(), matrix=q.to_matrix(), verts=bm.verts)
        T(bm, c + d * r * .7); P.add(bm, soft('cloud', c.y - r, c.y + r * 1.6, .55, .95), True)
    return P

def puff_bush(seed=1, col='leaf', r=2.6):
    P = Prop('PuffBush_%s%d' % (col, seed))
    sh = soft(col, -.4, r * 1.3, .3, .86, (0, r * .45, 0), .15)
    P.add(T(ell(r * .8, r * .62, r * .8, 12, 7), (0, r * .42, 0)), sh, True)
    for k in range(4):
        a = k * math.tau / 4 + seed
        P.add(T(ell(r * .48, r * .46, r * .48, 9, 6), (math.cos(a) * r * .55, r * (.55 if k % 2 else .35), math.sin(a) * r * .55)), sh, True)
    P.add(T(ell(r * .5, r * .48, r * .5, 9, 6), (0, r * .9, 0)), sh, True)
    if seed % 2:
        rng = random.Random(seed)
        for k in range(5):
            a = rng.uniform(0, math.tau); y = rng.uniform(.4, .9)
            p = V3((math.cos(a) * r * .8 * math.sqrt(1 - y * y) * 1.15, r * .4 + y * r * .7, math.sin(a) * r * .8 * math.sqrt(1 - y * y) * 1.15))
            P.add(T(ell(.3, .3, .3, 6, 4), p), soft(('red', 'pink', 'yellow')[seed % 3], 0, 4, .55, .9), True)
    return P

def flower_patch(seed=1, cols=('pink', 'yellow', 'cloud')):
    """5-7 chibi daisies: thin stem, leaf, scalloped petal disc, round centre"""
    rng = random.Random(seed)
    P = Prop('FlowerPatch%d' % seed)
    n = rng.randint(4, 5)
    for i in range(n):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.8) if i else 0; x, z = math.cos(a) * d, math.sin(a) * d
        h = rng.uniform(1.0, 1.9)
        P.add(tube([V3((x, -.3, z)), V3((x + .08, h * .5, z)), V3((x, h, z))], .07, sides=4), flat('leaf', .5), True)
        P.add(T(ell(.35, .06, .18, 6, 2), (x + .25, h * .35, z), rng.uniform(0, 360), 0, 20), flat('leaf', .62), True)
        col = cols[i % len(cols)]
        poly = [(math.cos(k * math.tau / 12) * (.66 if k % 2 == 0 else .4), math.sin(k * math.tau / 12) * (.66 if k % 2 == 0 else .4)) for k in range(12)]
        bm = ngon_prism(poly, -.05, .07, 0)
        T(bm, (0, 0, 0), 0, rng.uniform(-30, -10)); T(bm, (x, h, z), rng.uniform(0, 360))
        P.add(bm, flat(col, .78, .12), True)
        P.add(T(ell(.22, .14, .22, 8, 4), (x, h + .1, z)), flat('yellow' if col != 'yellow' else 'orange', .7, .15), True)
    return P

def grass_tuft(seed=1):
    """chunky clover tuft: 3 rounded leaf blobs (cheap)"""
    rng = random.Random(seed)
    P = Prop('GrassTuft%d' % seed)
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(-.3, .3)
        P.add(T(ell(.55, .42, .55, 8, 5), (math.cos(a) * .55, .15, math.sin(a) * .55)), soft('grass', -.2, .8, .35, .75), True)
    return P

# ------------------------------------------------------------------ meadow dressing
def mushroom(seed=1, cap='red', h=4.0):
    """chubby toadstool: bulgy stem, domed cap with white spots, ring skirt"""
    P = Prop('Mushroom_%s%d' % (cap, seed))
    P.add(lathe([(0, -.3), (1.1, -.3), (1.25, .5), (1.0, 1.4), (.85, h * .65), (0, h * .7)], 14), soft('cream', -.3, h, .5, .85), True)
    R = h * .55
    P.add(lathe([(0, h * .55), (R * .8, h * .55), (R, h * .62), (R * .95, h * .8), (R * .7, h * .98), (R * .3, h * 1.08), (0, h * 1.1)], 20), soft(cap, h * .55, h * 1.1, .45, .9), True)
    rng = random.Random(seed)
    for k in range(6):
        a = k * math.tau / 6 + rng.uniform(-.3, .3)
        rr, y = ((R * .9, h * .84), (R * .56, h * 1.02))[k % 2]
        nrm = V3((math.cos(a) * (.8 if k % 2 == 0 else .5), .5 if k % 2 == 0 else .9, math.sin(a) * (.8 if k % 2 == 0 else .5))).normalized()
        rr += .05; y += .05
        bm = ell(.38, .1, .38, 8, 3); q = V3((0, 1, 0)).rotation_difference(nrm)
        bmesh.ops.rotate(bm, cent=V3(), matrix=q.to_matrix(), verts=bm.verts); T(bm, (math.cos(a) * rr, y, math.sin(a) * rr))
        P.add(bm, flat('cloud', .9, .05), True)
    return P

def picnic_set():
    """checkered blanket (cells alternate red / cream), a wicker basket with a handle, a cupcake and two cups. Front -Z."""
    P = Prop('PicnicSet')
    bm = bmesh.new(); n = 6; s = 1.5
    for i in range(n):
        for j in range(n):
            x0, z0 = (i - n / 2) * s, (j - n / 2) * s
            bm.faces.new([bm.verts.new((x, .12 + .03 * math.sin(x * .7 + z * .5), z)) for x, z in ((x0, z0), (x0, z0 + s), (x0 + s, z0 + s), (x0 + s, z0))])
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    ur, uc = PAL.u('red'), PAL.u('cream')
    P.add(bm, lambda f: [((ur if (int((f.calc_center_median().x + 9) / s) + int((f.calc_center_median().z + 9) / s)) % 2 else uc), .72)] * len(f.loops))
    P.add(T(lathe([(0, 0), (1.3, 0), (1.5, 1.4), (1.35, 1.5), (0, 1.5)], 14), (2.2, .1, 1.6)), soft('wood', 0, 1.6, .45, .8), True)
    P.add(T(torus(1.2, .14, 14, 5, 0, math.pi), (2.2, 1.55, 1.6), 0, 90), soft('wood', 1, 3, .5, .8), True)
    P.add(T(ell(1.05, .4, 1.05, 12, 5), (2.2, 1.55, 1.6)), soft('red', 1.4, 2, .5, .8), True)
    P.add(T(lathe([(0, 0), (.6, 0), (.75, .6), (0, .6)], 12), (-1.6, .12, -1.4)), soft('pink', 0, 1, .5, .8), True)
    P.add(T(puff(.62, 3, 4, .15, 12, 8, .9, .3), (-1.6, .9, -1.4)), soft('cloud', .6, 1.5, .6, .95), True)
    P.add(T(ell(.2, .2, .2, 6, 4), (-1.6, 1.5, -1.4)), soft('red', 1.3, 1.7, .6, .9), True)
    for dx in (-.2, .9):
        P.add(T(lathe([(0, 0), (.35, 0), (.42, .7), (.36, .7), (0, .2)], 10), (dx, .12, 2.6)), soft('sky', 0, .9, .5, .9), True)
    return P

def stump(seed=1):
    P = Prop('Stump%d' % seed)
    P.add(lathe([(1.9, -.5), (1.7, .2), (1.35, .6), (1.3, 1.9), (1.2, 2.0), (0, 2.0)], 14), soft('wood', -.5, 2, .35, .65), True)
    for k in range(3):
        P.add(T(torus(.35 + k * .35, .07, 14, 4), (0, 2.0, 0)), flat('cream', .6 - k * .05), True)
    P.add(T(lathe([(0, 1.95), (1.25, 1.95), (1.15, 2.05), (0, 2.05)], 14), (0, 0, 0)), flat('cream', .78), True)
    return P

def soft_rock(seed=1, r=3.0, col='stone'):
    """smooth pebble boulder (squashed soft lump)"""
    P = Prop('SoftRock_%s%d' % (col, seed))
    P.add(T(puff(r, seed + 40, 4, .14, 16, 10, .66, .45), (0, r * .32, 0)), soft(col, -.3, r, .3, .78, (0, r * .3, 0), .12), True)
    return P

# ------------------------------------------------------------------ candy dressing
def lollipop(seed=1, h=11.0, cols=('pink', 'cloud')):
    """giant swirl lollipop: two interleaved coiled candy ropes (pink + cream) form the disc, striped stick, mint bow"""
    P = Prop('Lollipop%d' % seed)
    P.add(T(rcyl(.38, h - 3.5, 10, .1, 1, -.6), (0, 0, 0)), flat('cloud', .82, .05), True)
    R = 3.4; c = V3((0, h - 3.0, 0)); turns = 3.0
    for k, col in enumerate(cols):
        pts = []; rads = []
        N = 44
        for i in range(N + 1):
            t = i / N; a = t * turns * math.tau + k * math.pi
            r = .3 + (R - .45) * t
            pts.append(c + V3((math.cos(a) * r, math.sin(a) * r, 0))); rads.append(.32 + .26 * min(1, t * 4))
        P.add(tube(pts, rads, sides=6, flat=(1.0, 1.25)), soft(col, c.y - R, c.y + R, .55, .9), True)
    P.add(T(ell(.55, .55, .55, 8, 6), c), soft(cols[0], c.y - 1, c.y + 1, .55, .9), True)
    for sx in (-1, 1):
        P.add(T(ell(.7, .38, .3, 8, 4), (sx * .65, h - 6.9, 0), 0, 0, sx * 30), soft('mint', h - 8, h - 6, .5, .85), True)
    return P

def candy_cane(seed=1, h=9.0):
    """hooked cane, red / cream diagonal stripes (fine rings so the stripes read)"""
    P = Prop('CandyCane%d' % seed)
    key = [V3((0, -.6, 0)), V3((0, h * .78, 0))] + [V3((-1.4 + math.cos(a) * 1.4, h * .78 + math.sin(a) * 1.4, 0)) for a in [math.pi * k / 8 for k in range(1, 9)]] + [V3((-2.8, h * .6, 0))]
    pts = []
    for a, b in zip(key, key[1:]):
        n = max(1, int((b - a).length / .45))
        for i in range(n): pts.append(a.lerp(b, i / n))
    pts.append(key[-1])
    bm = tube(pts, .55, sides=10)
    ur, uc = PAL.u('red'), PAL.u('cloud')
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    vid = {}
    for i, p in enumerate(pts): vid[i] = L[i]
    def st(f):
        p = f.calc_center_median()
        i = min(range(len(pts)), key=lambda j: (pts[j] - p).length)
        u = ur if int((L[i] * .62 + p.z * .75 + 10) % 2) == 0 else uc
        return [(u, clamp(.62 + .25 * f.normal.dot(SUN), .05, .95))] * len(f.loops)
    P.add(bm, st, True)
    return P

def gumdrops(seed=1):
    """3-4 sugar-dusted gumdrops in candy colours"""
    rng = random.Random(seed)
    P = Prop('Gumdrops%d' % seed)
    for k, col in enumerate(('red', 'mint', 'yellow', 'lilac')[:3 + seed % 2]):
        a = k * 2.1 + seed; d = 0 if k == 0 else 2.4; s = 1.0 if k == 0 else rng.uniform(.6, .8)
        P.add(T(lathe([(0, -.2), (1.6 * s, -.2), (1.7 * s, .5 * s), (1.3 * s, 1.6 * s), (.6 * s, 2.2 * s), (0, 2.3 * s)], 16), (math.cos(a) * d, 0, math.sin(a) * d)),
              soft(col, -.2, 2.3 * s, .45, .9, (math.cos(a) * d, s, math.sin(a) * d)), True)
    return P

def giant_donut():
    """pink-frosted donut lying tilted on the grass with sprinkles"""
    P = Prop('GiantDonut')
    bm = torus(3.4, 1.9, 32, 14); T(bm, (0, 0, 0), 0, 8); T(bm, (0, 1.6, 0))
    P.add(bm, soft('orange', -.5, 4, .4, .8), True)
    bm = bmesh.new(); NA, NB = 32, 8; rows = []
    for i in range(NA + 1):
        a = i * math.tau / NA; w = .12 * math.sin(a * 5)
        rows.append([bm.verts.new(V3((math.cos(a) * (3.4 + math.cos(b) * 2.0), math.sin(b) * 2.0 + .02, math.sin(a) * (3.4 + math.cos(b) * 2.0)))) for b in [lerp(-.25 + w, math.pi + .25 - w, k / NB) for k in range(NB + 1)]])
    for A, Bq in zip(rows, rows[1:]):
        for k in range(NB): bm.faces.new((A[k], A[k + 1], Bq[k + 1], Bq[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        cc = f.calc_center_median(); ring = V3((cc.x, 0, cc.z)).normalized() * 3.4
        if f.normal.dot(cc - ring) < 0: f.normal_flip()
    T(bm, (0, 0, 0), 0, 8); T(bm, (0, 1.6, 0))
    P.add(bm, soft('pink', 0, 4, .55, .92), True)
    rng = random.Random(2)
    for k in range(18):
        a = rng.uniform(0, math.tau); b = rng.uniform(.4, 2.6)
        p = V3((math.cos(a) * (3.4 + math.cos(b) * 2.05), math.sin(b) * 2.05, math.sin(a) * (3.4 + math.cos(b) * 2.05)))
        bm = pill((0, 0, 0), (.45, 0, 0), .12, 5, 1); T(bm, (0, 0, 0), rng.uniform(0, 360)); T(bm, p); T(bm, (0, 0, 0), 0, 8); T(bm, (0, 1.6, 0))
        P.add(bm, flat(('yellow', 'sky', 'mint', 'cloud', 'lilac')[k % 5], .75), True)
    return P

# ------------------------------------------------------------------ crystal dressing
def crystal_spire(seed=1, s=1.0):
    """big crystal cluster: soft rock base, 3-5 tall glowing points"""
    rng = random.Random(seed)
    P = Prop('CrystalSpire%d' % seed)
    P.add(T(puff(3.2 * s, seed + 9, 5, .15, 14, 8, .5, .4), (0, .5 * s, 0)), soft('stone', -.5, 2.5 * s, .35, .75), True)
    for k in range(3 + seed % 3):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(1.2, 2.2) * s
        h = (9.0 if k == 0 else rng.uniform(4, 6.5)) * s
        bm = B.lathe([(0, -.4), (1.2 * s, 0), (1.05 * s, h * .75), (0, h)], 6)
        T(bm, (0, 0, 0), rng.uniform(0, 60), 0 if k == 0 else rng.uniform(-28, 28), 0 if k == 0 else rng.uniform(-20, 20))
        T(bm, (math.cos(a) * d, .6 * s, math.sin(a) * d)); P.gadd(bm, 'crystal')
    return P

def star_lamp(seed=1):
    """lilac curled post (a hook at the top) holding a glowing star lantern"""
    P = Prop('StarLamp%d' % seed)
    P.add(T(lathe([(0, -.4), (1.3, -.4), (1.4, .3), (.7, .7), (0, .8)], 12), (0, 0, 0)), soft('lilac', -.4, 1, .45, .8), True)
    pts = [V3((0, .5, 0)), V3((0, 6, 0)), V3((0, 8.2, 0)), V3((.6, 9.4, 0)), V3((1.8, 9.6, 0)), V3((2.6, 8.9, 0))]
    P.add(tube(pts, .32, sides=8), soft('lilac', 0, 10, .45, .85), True)
    P.add(T(ell(.5, .5, .5, 8, 6), (0, 8.2, 0)), soft('cream', 7, 9, .55, .9), True)
    P.add(pill((2.6, 8.9, 0), (2.6, 8.0, 0), .08, 4, 1), flat('stone', .6), True)
    P.gadd(T(star(1.1, .7), (2.6, 7.0, 0)), 'star')
    return P

def glow_shroom(seed=1):
    """trio of round-capped glow mushrooms (cyan caps glow)"""
    rng = random.Random(seed)
    P = Prop('GlowShroom%d' % seed)
    for k in range(3):
        a = k * 2.2 + seed; d = 0 if k == 0 else 1.3; h = (2.6 if k == 0 else rng.uniform(1.4, 2.0))
        x, z = math.cos(a) * d, math.sin(a) * d
        P.add(T(lathe([(0, -.3), (.55, -.3), (.45, h * .5), (.35, h), (0, h)], 8), (x, 0, z)), soft('cream', 0, h, .5, .85), True)
        P.gadd(T(ell(h * .45, h * .28, h * .45, 12, 6), (x, h, z)), 'shroom')
    return P

# ------------------------------------------------------------------ shared street dressing
def fence(theme='meadow', L=14.0):
    """chunky rail fence segment from x = 0 to x = L: one fat post with a ball cap at x = 0, two rounded rails,
    3 rounded pickets. Theme sets colours."""
    post, rail, cap = {'meadow': ('cream', 'wood', 'red'), 'hub': ('cream', 'sky', 'pink'), 'candy': ('pink', 'cream', 'mint'),
                       'crystal': ('lilac', 'cream', 'sky')}[theme]
    P = Prop('Fence_%s' % theme)
    P.add(rcyl(.6, 3.6, 8, .2, 1, -.6), soft(post, -.6, 3.2, .45, .85), True)
    P.add(T(ell(.85, .85, .85, 8, 5), (0, 3.6, 0)), soft(cap, 2.8, 4.4, .55, .95), True)
    for y in (1.1, 2.4):                                                        # rails stop short of the next segment's post
        P.add(T(rbox((L - 1.7, .8, .65), .3, 1), (L / 2 - .1, y, 0)), soft(rail, y - .3, y + .3, .55, .8), True)
    for k in range(2):
        x = L * (k + 1) / 3
        bm = lathe([(.55, -.4), (.55, 2.6), (.4, 3.0), (0, 3.15)], 6); bmesh.ops.scale(bm, vec=V3((1, 1, .55)), verts=bm.verts)
        P.add(T(bm, (x, 0, 0)), soft(post, -.4, 3, .5, .85), True)
    return P

def lamp_post(theme='hub'):
    """chibi lamp: bulgy base, slim post with a candy ring, round glowing lantern under a little cap"""
    post, ring = {'hub': ('sky', 'pink'), 'meadow': ('wood', 'leaf'), 'candy': ('pink', 'mint')}[theme]
    P = Prop('LampPost_%s' % theme)
    P.add(lathe([(0, -.4), (1.2, -.4), (1.3, .3), (.8, .8), (.4, 1.4), (.32, 8.4), (.6, 8.7), (0, 8.8)], 12), soft(post, -.4, 9, .45, .85), True)
    P.add(T(torus(.42, .18, 12, 5), (0, 4.0, 0)), soft(ring, 3.7, 4.3, .55, .9), True)
    P.gadd(T(ell(1.2, 1.2, 1.2, 14, 8), (0, 9.9, 0)), 'lamp')
    P.add(T(lathe([(0, 0), (1.25, 0), (1.0, .5), (.3, .9), (0, 1.0)], 14), (0, 10.8, 0)), soft(ring, 10.8, 12, .5, .9), True)
    P.add(T(ell(.3, .3, .3, 8, 4), (0, 12.0, 0)), soft('yellow', 11.6, 12.4, .6, .9), True)
    return P

def bench(col='pink'):
    """chubby rounded bench: two soft seat slats + back slat on stubby round legs. Front -Z."""
    P = Prop('Bench_' + col)
    for z in (-.55, .55):
        P.add(T(rbox((6.0, .5, 1.0), .22, 2), (0, 1.7, z)), soft('wood', 1.4, 2, .55, .8), True)
    P.add(T(rbox((6.0, 1.2, .5), .22, 2), (0, 3.1, 1.25), 0, -12), soft('wood', 2.5, 3.8, .55, .85), True)
    for sx in (-1, 1):
        P.add(T(rbox((.6, 3.2, 3.0), .25, 2), (sx * 2.6, 1.1, .3)), soft(col, -.3, 3, .45, .85), True)
        P.add(T(ell(.45, .45, .45, 8, 6), (sx * 2.6, 2.9, 1.6)), soft('yellow', 2.5, 3.4, .55, .9), True)
    return P

def cloud(seed=1, s=1.0):
    """frame cloud floating on the lagoon: 4-6 overlapping puffs merged, flat bottom"""
    rng = random.Random(seed)
    P = Prop('Cloud%d' % seed)
    n = 4 + seed % 3
    for k in range(n):
        x = (k - (n - 1) / 2) * 5.0 * s + rng.uniform(-1, 1); z = rng.uniform(-2.5, 2.5) * s
        r = (6.5 if abs(k - (n - 1) / 2) < 1 else rng.uniform(3.8, 5.0)) * s
        P.add(T(puff(r, seed * 7 + k, 5, .14, 13, 8, .78, .35), (x, r * .3, z)), soft('cloud', -1, 7 * s, .45, .95, (x, 0, z), .12), True)
    return P

def sea_rock(seed=1, r=4.0):
    """rounded lagoon rock with a little grass cap (sits in the water as frame)"""
    P = Prop('SeaRock%d' % seed)
    P.add(T(puff(r, seed + 70, 5, .15, 16, 10, .8, .5), (0, r * .1, 0)), soft('stone', -r * .5, r, .3, .78, (0, 0, 0), .12), True)
    P.add(T(puff(r * .55, seed + 71, 4, .12, 12, 8, .45, .5), (r * .1, r * .78, 0)), soft('grass', r * .5, r * 1.1, .5, .85), True)
    return P

def mascot_test():
    P = Prop('MascotTest'); puffpaw(P, (0, 0, 0), 1.0); return P
