# BubblePop: popped bubble variants D..J (more variety on a popped wall).
# Imported by build_bubblewrap.py (it calls bind(globals()) first so this file
# can use its helpers: make_mesh, Canvas, mixc, R_SKIRT ...). Not run alone.
#
# Each variant is a height field over the same 1.13-stud footprint (outer ring
# at R_SKIRT, z = 0, origin bottom centre), meshed with a constrained Delaunay
# triangulation so tear outlines and creases are real edges. Tears keep a
# "floor" just above the film (painted dark), like A..C. The toon texture is
# painted from the mesh itself (its normals rasterised into the 1.2 x 1.2
# planar UV), then each variant adds its own base colours, creases and tears.
#
#   D  half-deflated: a dome that kept air on one side, sagging dimple + short slit
#   E  5-petal star burst, petal tips curled up, big dark star
#   F  long jagged rip right across, one side lifted as a flap
#   G  pin-prick: shallow cup, tiny hole, radial wrinkles (the light one)
#   H  crumpled flat, zigzag creases, sideways tear near the edge (faceted)
#   I  caved-in cup: dark dent, bright rim ridge, crescent split
#   J  shredded: two holes + a ragged tear, a lifted tatter (the dark one)
import math
import random

import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

G = {}
Z_FLOOR = 0.012
MAX_TRIS = 120
KEYS = "DEFGHIJ"


def bind(g):
    G.update(g)


# ---------------------------------------------------------------- small maths
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def sstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0))
    return t * t * (3 - 2 * t)


def bump(d, R):
    return math.cos(0.5 * math.pi * d / R) ** 2 if d < R else 0.0


def skirt(x, y):
    """1 inside, falling to 0 at the footprint edge (pancake slope to the film)."""
    return sstep(G["R_SKIRT"], 0.43, math.hypot(x, y))


def rot2(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def seg_d(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    t = clamp(((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / (vx * vx + vy * vy + 1e-12))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def in_poly(p, poly):
    x, y = p
    inside = False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0:
            inside = not inside
    return inside


def poly_d(p, poly):
    return min(seg_d(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def noise2(x, y, seed):
    r = random.Random(seed)
    acc = 0.0
    for _ in range(3):
        fx, fy, ph = r.uniform(5, 11), r.uniform(5, 11), r.uniform(0, 6.3)
        acc += math.sin(fx * x + ph) * math.sin(fy * y + 1.7 * ph)
    return acc / 3


# ---------------------------------------------------------------- tear shapes
def slit(spine, widths, rnd, zup, zlo, jag=0.25, rim=0.02, smooth=1, floor_every=1, **kw):
    """A slit/rip along a spine: upper side (left of travel) and lower side,
    zig-zag jagged. zup/zlo: lip height per spine index (callables)."""
    n = len(spine)
    up, lo, zu, zl = [], [], [], []
    for k in range(1, n - 1):
        (ax, ay), (bx, by) = spine[k - 1], spine[k + 1]
        tx, ty = bx - ax, by - ay
        ll = math.hypot(tx, ty)
        nx, ny = -ty / ll, tx / ll
        w = widths[k]
        j1 = 1 + (jag if k % 2 else -jag) + rnd.uniform(-0.1, 0.1)
        j2 = 1 + (-jag if k % 2 else jag) + rnd.uniform(-0.1, 0.1)
        x, y = spine[k]
        up.append((x + nx * w * j1, y + ny * w * j1))
        lo.append((x - nx * w * j2, y - ny * w * j2))
        zu.append(zup(k))
        zl.append(zlo(k))
    poly = [spine[0]] + lo + [spine[-1]] + up[::-1]          # counter-clockwise when travelling +x
    lipz = [zlo(0)] + zl + [zlo(n - 1)] + zu[::-1]
    floor = [spine[k] for k in range(1, n - 1, floor_every)]
    d = dict(poly=poly, lipz=lipz, floor=floor, rim=rim, smooth=smooth)
    d.update(kw)
    return d


def blob(c, r, n, rnd, z, jag=0.25, rim=0.02, smooth=2, a0=0.0, **kw):
    poly, lipz = [], []
    for i in range(n):
        a = a0 + 2 * math.pi * i / n + rnd.uniform(-0.15, 0.15)
        rr = r * (1 + (jag if i % 2 else -jag * 0.6) + rnd.uniform(-0.08, 0.08))
        poly.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
        lipz.append(z(i) if callable(z) else z)
    d = dict(poly=poly, lipz=lipz, floor=[c], rim=rim, smooth=smooth)
    d.update(kw)
    return d


def arc_pts(c, r, a0, a1, n):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * t / (n - 1))),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * t / (n - 1)))) for t in range(n)]


def taper(n, w, p=0.7):
    return [w * math.sin(math.pi * k / (n - 1)) ** p for k in range(n)]


# ---------------------------------------------------------------- the variants
def spec_D():
    """Half-deflated: one side kept its air (a saggy dome), the other side
    flopped flat with a wrinkled dimple and a short slit."""
    rnd = random.Random(101)
    dome, dim = (-0.10, 0.10), (0.19, -0.17)

    def hf(x, y):
        d = math.hypot(x - dome[0], y - dome[1])
        h = 0.045 + 0.20 * (1 - (d / 0.42) ** 2) ** 0.8 if d < 0.42 else 0.045   # round-topped saggy dome
        h -= 0.03 * bump(math.hypot(x - dim[0], y - dim[1]), 0.17)
        return skirt(x, y) * max(h, 0.02) + 0.003 * noise2(x, y, 5)

    sp = [(dim[0] - 0.15, dim[1] - 0.05), (dim[0] - 0.07, dim[1] - 0.025), (dim[0], dim[1] + 0.01), (dim[0] + 0.07, dim[1] + 0.05), (dim[0] + 0.13, dim[1] + 0.10)]
    tears = [slit(sp, taper(5, 0.04, 0.5), rnd, lambda k: 0.035, lambda k: 0.03, jag=0.2, rim=0.024, smooth=2, halo=0.05)]
    creases = [  # wrinkles around the dimple, where the dome sags into it
        (arc_pts(dim, 0.15, 95, 160, 4), "v", 0.016),
        (arc_pts(dim, 0.14, 200, 250, 3), "v", 0.012),
        (arc_pts(dim, 0.12, 20, 70, 3), "r", 0.012),
    ]
    fill = [(0.47, 12, 0.1), (0.33, 8, 0.3)]
    extra = [dome] + arc_pts(dome, 0.14, 15, 315, 6) + arc_pts(dome, 0.28, 40, 340, 7)
    return dict(hf=hf, tears=tears, creases=creases, fill=fill, extra=extra, smooth=True, paint=paint_D, dome=dome)


def spec_E():
    """Star burst: five petals of film split from the centre, tips curled up."""
    rnd = random.Random(202)
    a0 = 90 + 8
    arms = [a0 + 72 * k + rnd.uniform(-6, 6) for k in range(5)]
    poly, lipz, floor, petals = [], [], [(0.0, 0.0)], []
    for k, a in enumerate(arms):
        rt = 0.40 * rnd.uniform(0.92, 1.04)
        for (r, da, z) in ((0.19, -14, 0.065), (rt, 0, 0.042), (0.19, 14, 0.065)):
            poly.append((r * math.cos(math.radians(a + da)), r * math.sin(math.radians(a + da))))
            lipz.append(z)
        pa = a + 36 + rnd.uniform(-5, 5)
        pr = 0.115 * rnd.uniform(0.9, 1.1)
        poly.append((pr * math.cos(math.radians(pa)), pr * math.sin(math.radians(pa))))
        lipz.append(0.165 + rnd.uniform(-0.015, 0.015))           # petal tip curls up
        petals.append(pa)
        floor.append((0.27 * math.cos(math.radians(a)), 0.27 * math.sin(math.radians(a))))

    def hf(x, y):
        r = math.hypot(x, y)
        return skirt(x, y) * (0.045 + 0.06 * sstep(0.40, 0.14, r))

    creases = [([(0.16 * math.cos(math.radians(pa)), 0.16 * math.sin(math.radians(pa))),
                 (0.30 * math.cos(math.radians(pa)), 0.30 * math.sin(math.radians(pa)))], "r", 0.025) for pa in petals]
    tears = [dict(poly=poly, lipz=lipz, floor=floor, rim=0.016, smooth=1, halo=0.05)]
    fill = [(0.47, 10, 0.05)]
    return dict(hf=hf, tears=tears, creases=creases, fill=fill, extra=[], smooth=True, paint=paint_E, petals=petals)


def spec_F():
    """A long jagged rip right across; the film above it peeled up as a flap."""
    rnd = random.Random(303)
    n = 10
    sp = []
    for k in range(n):
        t = k / (n - 1)
        x = -0.44 + 0.88 * t
        sp.append((x, 0.08 * x + 0.05 * math.sin(math.pi * t * 1.3) - 0.02 + (rnd.uniform(-0.012, 0.012) if 0 < k < n - 1 else 0)))
    w = taper(n, 0.055, 0.5)

    def along(k):
        return math.sin(math.pi * k / (n - 1)) ** 0.6

    tear = slit(sp, w, rnd, lambda k: 0.05 + 0.15 * along(k), lambda k: 0.03 + 0.012 * along(k),
                jag=0.45, rim=0.014, smooth=0, floor_every=1, flap=True)

    def side(x, y):  # >0 above the rip (flap side)
        return y - (0.08 * x - 0.02 + 0.05 * math.sin(math.pi * (x + 0.44) / 0.88 * 1.3))

    def hf(x, y):
        d = side(x, y)
        t = clamp((x + 0.44) / 0.88)
        lift = math.sin(math.pi * t) ** 0.6
        h = 0.045 + 0.004 * noise2(x, y, 9)
        if d > 0:
            h += 0.15 * lift * sstep(0.34, 0.03, d)
        return skirt(x, y) * h

    creases = [([(-0.10, 0.13), (0.0, 0.22), (0.08, 0.34)], "v", 0.03)]   # fold where the flap bends up
    fill = [(0.47, 12, 0.0), (0.30, 8, 0.2)]
    return dict(hf=hf, tears=[tear], creases=creases, fill=fill, extra=[(0.18, 0.20), (-0.25, 0.18)], smooth=True,
                paint=paint_F, side=side)


def spec_G():
    """Pin-prick pop: the dome sank into a shallow cup round a tiny hole with
    wrinkles running out from it like spokes."""
    rnd = random.Random(404)
    c = (0.03, 0.02)
    nh = 7
    hole = blob(c, 0.062, nh, rnd, 0.034, jag=0.3, rim=0.024, smooth=2, halo=0.07)

    def hf(x, y):
        r = math.hypot(x - c[0], y - c[1])
        return skirt(x, y) * (0.03 + 0.09 * sstep(0.06, 0.40, r))

    creases = []
    for i in range(nh):
        a = 2 * math.pi * i / nh + 0.3 + rnd.uniform(-0.12, 0.12)
        L = rnd.uniform(0.34, 0.42)
        pts = [(c[0] + r * math.cos(a + 0.12 * r), c[1] + r * math.sin(a + 0.12 * r)) for r in (0.09, 0.09 + (L - 0.09) / 2, L)]
        creases.append((pts, "v", 0.02))
    fill = [(0.47, 14, 0.0), (0.27, 7, 0.75)]
    return dict(hf=hf, tears=[hole], creases=creases, fill=fill, extra=[], smooth=True, paint=paint_G, centre=c)


def spec_H():
    """Squashed totally flat and crumpled; a sideways tear near the edge."""
    rnd = random.Random(505)

    def hf(x, y):
        return skirt(x, y) * (0.045 + 0.012 * noise2(x, y, 21))

    sp = arc_pts((0.0, 0.0), 0.32, 200, 290, 6)
    tear = slit(sp[::-1], taper(6, 0.04, 0.6), rnd, lambda k: 0.035, lambda k: 0.07, jag=0.35, rim=0.02, smooth=1)
    creases = []
    lines = [((-0.40, 0.18), (0.30, 0.36)), ((-0.30, -0.02), (0.42, 0.10)), ((0.05, 0.42), (0.20, -0.28)), ((-0.42, 0.34), (-0.10, -0.08))]
    for n, (a, b) in enumerate(lines):
        pts = []
        m = 4
        for k in range(m):
            t = k / (m - 1)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            off = (0.035 if k % 2 else -0.035) * (0 < k < m - 1)
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            ll = math.hypot(nx, ny)
            pts.append((x + nx / ll * off, y + ny / ll * off))
        creases.append((pts, "r" if n % 2 else "v", 0.02))
    fill = [(0.47, 12, 0.0), (0.22, 5, 0.4)]
    return dict(hf=hf, tears=[tear], creases=creases, fill=fill, extra=[], smooth=False, paint=paint_H)


def spec_I():
    """Caved in: the dome pushed inside out into a dent, a thick rim ridge
    round it and a crescent split along one side."""
    rnd = random.Random(606)
    RR = 0.41

    def hf(x, y):
        r = math.hypot(x, y)
        if r < RR:
            h = 0.028 + 0.19 * (r / RR) ** 1.8
        else:
            h = 0.218 * sstep(G["R_SKIRT"], RR, r)
        return h

    sp = arc_pts((0.0, 0.0), 0.29, 25, 145, 7)
    tear = slit(sp[::-1], taper(7, 0.045, 0.6), rnd,
                lambda k: hf(0.33, 0) + 0.02, lambda k: hf(0.25, 0) - 0.01, jag=0.3, rim=0.02, smooth=1, floor_every=2)
    fill = [(RR, 14, 0.0), (0.19, 7, 0.4), (0.0, 1, 0.0)]
    return dict(hf=hf, tears=[tear], creases=[], fill=fill, extra=[], smooth=True, paint=paint_I, rr=RR, ring_keep=True)


def spec_J():
    """Shredded: two small holes and a ragged tear, with a lifted tatter."""
    rnd = random.Random(707)

    def hf(x, y):
        return skirt(x, y) * (0.07 + 0.018 * noise2(x, y, 33))

    h1 = blob((-0.24, 0.10), 0.10, 7, rnd, lambda i: 0.15 if i == 2 else 0.07, jag=0.35, rim=0.012, smooth=1, tatter=2)
    h2 = blob((0.27, -0.17), 0.065, 6, rnd, 0.06, jag=0.3, rim=0.012, smooth=1)
    sp = [(-0.10, -0.36), (-0.04, -0.22), (-0.06, -0.08), (0.03, 0.06), (0.02, 0.20), (0.11, 0.34)]   # ragged tear running between the holes
    t3 = slit(sp, taper(6, 0.05, 0.5), rnd, lambda k: 0.08, lambda k: 0.06 + (0.05 if k == 3 else 0), jag=0.45, rim=0.012, smooth=0)
    fill = [(0.47, 11, 0.0)]
    extra = [(0.22, 0.12), (-0.25, -0.18), (0.25, 0.32), (0.38, 0.05), (-0.36, 0.30), (-0.22, 0.38)]
    return dict(hf=hf, tears=[h1, h2, t3], creases=[([(0.14, -0.02), (0.22, 0.06), (0.33, 0.10)], "v", 0.02)], fill=fill,
                extra=extra, smooth=True, paint=paint_J)


SPECS = dict(D=spec_D, E=spec_E, F=spec_F, G=spec_G, H=spec_H, I=spec_I, J=spec_J)


# ---------------------------------------------------------------- meshing
def build(name, spec):
    R = G["R_SKIRT"]
    hf = spec["hf"]
    pts, zs, edges = [], [], []

    def add(p, z):
        pts.append(tuple(p))
        zs.append(z)
        return len(pts) - 1

    for i in range(16):
        a = 2 * math.pi * i / 16
        add((R * math.cos(a), R * math.sin(a)), 0.0)
    polys = [t["poly"] for t in spec["tears"]]
    for t in spec["tears"]:
        ids = [add(p, z) for p, z in zip(t["poly"], t["lipz"])]
        edges += [(ids[i], ids[(i + 1) % len(ids)]) for i in range(len(ids))]
        for f in t["floor"]:
            add(f, Z_FLOOR)

    def near_tear(p, m):
        return any(in_poly(p, pl) or poly_d(p, pl) < m for pl in polys)

    def crowded(p, m):
        return any(math.hypot(p[0] - q[0], p[1] - q[1]) < m for q in pts)

    for cpts, kind, depth in spec["creases"]:
        ids = []
        for n, p in enumerate(cpts):
            t = n / max(1, len(cpts) - 1)
            bend = math.sin(math.pi * t) if len(cpts) > 2 else 0.6
            off = depth * (0.4 + 0.6 * bend) * (1 if kind == "r" else -1)
            if near_tear(p, 0.02) or crowded(p, 0.03):
                ids.append(None)
                continue
            ids.append(add(p, max(Z_FLOOR + 0.01, hf(*p) + off)))
        edges += [(a, b) for a, b in zip(ids, ids[1:]) if a is not None and b is not None]
    for p in spec["extra"]:
        if not near_tear(p, 0.05) and not crowded(p, 0.07):
            add(p, hf(*p))
    for r, n, ph in spec["fill"]:
        for i in range(n):
            a = 2 * math.pi * (i + ph) / n
            p = (r * math.cos(a), r * math.sin(a))
            margin = 0.035 if spec.get("ring_keep") else 0.05
            if near_tear(p, margin) or crowded(p, 0.07 if r < 0.45 else 0.05):
                continue
            add(p, hf(*p))

    vo, eo, fo, ov, oe, of = delaunay_2d_cdt([Vector(p) for p in pts], edges, [], 0, 1e-6)
    verts = []
    for i, v in enumerate(vo):
        src = ov[i]
        z = zs[src[0]] if src else hf(v.x, v.y)
        verts.append((v.x, v.y, z))
    faces = []
    for f in fo:
        a, b, c = (verts[i] for i in f)
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        faces.append(tuple(f) if area > 0 else tuple(reversed(f)))
    ob = G["make_mesh"](name, verts, faces, spec["smooth"])
    nt = G["tris"](ob)
    assert nt <= MAX_TRIS, f"{name}: {nt} tris > {MAX_TRIS}"
    return ob


# ---------------------------------------------------------------- painting
LIGHT = np.array([-0.35, 0.45, 0.82]) / np.linalg.norm([-0.35, 0.45, 0.82])


def raster(cv, ob, flat):
    """Height + normal of the mesh at every texel (planar top-down UV)."""
    me = ob.data
    me.calc_loop_triangles()
    V = np.array([v.co[:] for v in me.vertices])
    VN = np.array([v.normal[:] for v in me.vertices])
    res = cv.res
    H = np.zeros((res, res))
    N = np.zeros((res, res, 3))
    N[..., 2] = 1
    span = cv.X[0, -1] - cv.X[0, 0]
    x0 = cv.X[0, 0]
    for lt in me.loop_triangles:
        ia, ib, ic = lt.vertices
        a, b, c = V[ia], V[ib], V[ic]
        lo = np.minimum(np.minimum(a, b), c)
        hi = np.maximum(np.maximum(a, b), c)
        i0 = max(0, int((lo[0] - x0) / span * (res - 1)) - 1)
        i1 = min(res, int((hi[0] - x0) / span * (res - 1)) + 3)
        j0 = max(0, int((lo[1] - x0) / span * (res - 1)) - 1)
        j1 = min(res, int((hi[1] - x0) / span * (res - 1)) + 3)
        sx, sy = cv.X[j0:j1, i0:i1], cv.Y[j0:j1, i0:i1]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (sx - c[0]) + (c[0] - b[0]) * (sy - c[1])) / den
        l2 = ((c[1] - a[1]) * (sx - c[0]) + (a[0] - c[0]) * (sy - c[1])) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        H[j0:j1, i0:i1][m] = (l1 * a[2] + l2 * b[2] + l3 * c[2])[m]
        if flat:
            fn = np.array(lt.normal[:])
            N[j0:j1, i0:i1][m] = fn
        else:
            n = l1[..., None] * VN[ia] + l2[..., None] * VN[ib] + l3[..., None] * VN[ic]
            N[j0:j1, i0:i1][m] = n[m]
    N /= np.linalg.norm(N, axis=2, keepdims=True) + 1e-9
    return H, N


def soft(cv, x):
    """Anti-aliased 0..1 toon switch for a value that crosses 0."""
    return np.clip(x / (1.5 * cv.px) + 0.5, 0, 1)


def toon(cv, N, base, z, lo=0.84, hi=0.955, k_shade=0.55, k_hi=0.5, band=0.012):
    lit = 0.55 * N[..., 2] + 0.45 * (N @ LIGHT)
    shade = G["mixc"](base, z["dark"], k_shade)
    light = G["mixc"](base, (255, 255, 255), k_hi)
    cv.put(shade, np.clip((lo - lit) / band + 0.5, 0, 1))
    cv.put(light, np.clip((lit - hi) / band + 0.5, 0, 1))
    return lit


def chaikin(poly, n):
    for _ in range(n):
        nb = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            nb += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        poly = nb
    return poly


def sdist(cv, poly):
    X, Y = cv.X, cv.Y
    inside = np.zeros_like(X, dtype=bool)
    dmin = np.full_like(X, 9.0)
    for i in range(len(poly)):
        p0, p1 = poly[i], poly[(i + 1) % len(poly)]
        cond = (p0[1] > Y) != (p1[1] > Y)
        xint = (p1[0] - p0[0]) * (Y - p0[1]) / ((p1[1] - p0[1]) + 1e-12) + p0[0]
        inside ^= cond & (X < xint)
        d, _ = cv.segdist(p0, p1)
        dmin = np.minimum(dmin, d)
    return np.where(inside, -dmin, dmin)


def paint_tear(cv, t, z, rim_col=(255, 255, 255), halo_col=None):
    poly = chaikin(list(t["poly"]), t.get("smooth", 1))
    sd = sdist(cv, poly)
    if t.get("halo") and halo_col is not None:
        cv.put(halo_col, cv.step(sd, t["halo"]) * 0.7)
    if t["rim"] > 0:
        cv.put(rim_col, cv.step(sd, t["rim"]))
    cv.put(z["gap"], cv.step(sd, -0.006))
    cv.put(G["mixc"](z["gap"], z["pop"], 0.22), cv.step(sd, -0.006) * (1 - cv.step(-sd, 0.022)) * 0.6)
    return sd


def paint_creases(cv, spec, z, base, wv=0.013, wr=0.011, kv=0.75, kr=0.8):
    dark = G["mixc"](base, z["dark"], 0.75)
    light = G["mixc"](base, (255, 255, 255), 0.7)
    for cpts, kind, _ in spec["creases"]:
        for a, b in zip(cpts, cpts[1:]):
            d, _ = cv.segdist(a, b)
            if kind == "v":
                cv.put(dark, kv * cv.step(d, wv))
            else:
                cv.put(light, kr * cv.step(d, wr))


def base_canvas(z, base):
    cv = G["Canvas"]()
    cv.fill(base)
    return cv


def paint_D(cv, spec, z, H, N):
    """Saturated body colour where it still holds air, pale where it sagged."""
    X, Y = cv.X, cv.Y
    pop, body = z["pop"], z["body"]
    cv.fill(pop)
    cv.put(G["mixc"](pop, body, 0.5), soft(cv, H - 0.085))
    cv.put(body, soft(cv, H - 0.13))
    lit = 0.55 * N[..., 2] + 0.45 * (N @ LIGHT)
    air = soft(cv, H - 0.11)
    cv.put(z["dark"], np.clip((0.80 - lit) / 0.012 + 0.5, 0, 1) * air * 0.85)              # dome's shadow side
    cv.put(G["mixc"](pop, z["dark"], 0.5), np.clip((0.83 - lit) / 0.012 + 0.5, 0, 1) * (1 - air) * 0.8)
    dx, dy = spec["dome"]
    cv.put(z["light"], cv.step(np.hypot(X - dx + 0.03, Y - dy - 0.03), 0.09))                # light cap
    r = np.hypot(X - dx, Y - dy)
    ang = np.degrees(np.arctan2(Y - dy, X - dx))
    t = np.clip((ang - 100) / 70, 0, 1)
    band = (ang > 100) & (ang < 170)
    cv.put((255, 255, 255), cv.step(np.abs(r - 0.17), 0.026 * np.sin(np.pi * t) ** 0.6) * band)  # gloss streak
    paint_creases(cv, spec, z, pop, wv=0.012)
    for t_ in spec["tears"]:
        paint_tear(cv, t_, z, halo_col=G["mixc"](pop, (255, 255, 255), 0.5))


def paint_E(cv, spec, z, H, N):
    pop = z["pop"]
    cv.fill(pop)
    toon(cv, N, pop, z, lo=0.86, k_shade=0.5)
    paint_creases(cv, spec, z, pop, wr=0.02, kr=0.85)
    # petal tips: bright where the film curls up towards you
    cv.put(G["mixc"](pop, (255, 255, 255), 0.75), soft(cv, H - 0.125))
    t = spec["tears"][0]
    paint_tear(cv, t, z, halo_col=G["mixc"](pop, z["dark"], 0.45))


def paint_F(cv, spec, z, H, N):
    pop = z["pop"]
    X, Y = cv.X, cv.Y
    side = Y - (0.08 * X - 0.02 + 0.05 * np.sin(np.pi * (X + 0.44) / 0.88 * 1.3))   # same line as spec_F's side()
    flap = G["mixc"](pop, (255, 255, 255), 0.35)
    cv.fill(G["mixc"](pop, z["dark"], 0.12))
    cv.put(flap, soft(cv, side))
    toon(cv, N, pop, z, lo=0.80, k_shade=0.45, hi=0.97)
    cv.put((255, 255, 255), soft(cv, H - 0.12) * soft(cv, side))                      # lifted edge catches the light
    t = spec["tears"][0]
    # shadow the lifted flap throws on the low side
    sh = (side < 0) & (side > -0.09) & (np.abs(X) < 0.40)
    cv.put(G["mixc"](pop, z["dark"], 0.7), sh * np.clip((0.09 + side) / 0.02, 0, 1) * 0.9)
    paint_creases(cv, spec, z, flap, wv=0.016)
    paint_tear(cv, t, z, rim_col=(255, 255, 255))


def paint_G(cv, spec, z, H, N):
    pop = z["pop"]
    pale = G["mixc"](pop, (255, 255, 255), 0.4)
    cv.fill(pale)
    toon(cv, N, pale, z, lo=0.80, k_shade=0.35, k_hi=0.6)
    paint_creases(cv, spec, z, pale, wv=0.011, kv=0.7)
    X, Y = cv.X, cv.Y
    c = spec["centre"]
    r = np.hypot(X - c[0], Y - c[1])
    cv.put(G["mixc"](pale, z["dark"], 0.3), cv.step(np.abs(r - 0.39), 0.012) * 0.6)    # soft cup-edge ring
    paint_tear(cv, spec["tears"][0], z, halo_col=G["mixc"](pale, z["dark"], 0.35))


def paint_H(cv, spec, z, H, N):
    pop, body = z["pop"], z["body"]
    mid = G["mixc"](pop, body, 0.35)
    cv.fill(mid)
    toon(cv, N, mid, z, lo=0.925, hi=0.94, k_shade=0.45, k_hi=0.55, band=0.006)   # faceted crumple: many small bands
    paint_creases(cv, spec, z, mid, wv=0.01, wr=0.009)
    paint_tear(cv, spec["tears"][0], z)


def paint_I(cv, spec, z, H, N):
    pop = z["pop"]
    X, Y = cv.X, cv.Y
    r = np.hypot(X, Y)
    RR = spec["rr"]
    cv.fill(pop)
    inside = cv.step(r, RR - 0.01)
    cv.put(G["mixc"](pop, z["dark"], 0.35), inside * soft(cv, 0.15 - H))
    cv.put(G["mixc"](pop, z["dark"], 0.62), inside * soft(cv, 0.085 - H))
    # inner wall facing away from the light is darker (dent reads as a hollow)
    lit = 0.55 * N[..., 2] + 0.45 * (N @ LIGHT)
    cv.put(G["mixc"](pop, z["dark"], 0.8), inside * np.clip((0.84 - lit) / 0.012 + 0.5, 0, 1) * 0.6)
    cv.put(G["mixc"](pop, (255, 255, 255), 0.75), cv.step(np.abs(r - RR), 0.03))     # bright rim ridge
    outside = 1 - cv.step(r, RR + 0.03)
    cv.put(G["mixc"](pop, z["dark"], 0.4), outside * np.clip((0.84 - lit) / 0.012 + 0.5, 0, 1))
    paint_tear(cv, spec["tears"][0], z)


def paint_J(cv, spec, z, H, N):
    pop = z["pop"]
    base = G["mixc"](pop, z["dark"], 0.18)
    cv.fill(base)
    toon(cv, N, base, z, lo=0.86, k_shade=0.5)
    paint_creases(cv, spec, z, base)
    for t in spec["tears"]:
        paint_tear(cv, t, z, rim_col=G["mixc"](pop, (255, 255, 255), 0.7))
    # the lifted tatter on hole 1: a bright ragged tongue
    t = spec["tears"][0]
    tp = t["poly"][t["tatter"]]
    cx, cy = t["floor"][0]
    d, s = cv.segdist((cx + (tp[0] - cx) * 0.35, cy + (tp[1] - cy) * 0.35), (tp[0] + (tp[0] - cx) * 0.25, tp[1] + (tp[1] - cy) * 0.25))
    cv.put(G["mixc"](pop, (255, 255, 255), 0.6), cv.step(d, 0.03 * (1 - 0.6 * s)))


def paint(path, ob, spec, z):
    cv = G["Canvas"]()
    H, N = raster(cv, ob, not spec["smooth"])
    spec["paint"](cv, spec, z, H, N)
    return cv.save(path)


def build_all():
    out = {}
    for k in KEYS:
        spec = SPECS[k]()
        out[k] = (build("Bubble_Popped_" + k, spec), spec)
    return out
