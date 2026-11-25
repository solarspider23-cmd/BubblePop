# BubblePop bubble wrap (v2, cartoon): builds every bubble wrap model, paints
# the toon textures, exports Roblox-ready FBX files, saves the .blend and
# renders the previews. Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_bubblewrap.py
#   (add "-- fast" after the script for quick low-sample previews,
#    "-- noprev" to only build + export)
#
# Conventions copied from ~/Documents/StealAFish/tools/blender (ckit.py):
#   * 1 unit = 1 stud. Blender +Z is up (Roblox +Y).
#   * FBX export: meshes turned half round about Z for the export (Roblox
#     imports an FBX turned half round), axis_forward -Z, axis_up Y,
#     FBX_SCALE_ALL, triangulated, path_mode STRIP. A <Name>.bounds.json beside
#     each file uses the same format as StealAFish.
#   * Origins sit at the BOTTOM CENTRE of each footprint.
#
# What it makes (art/bubblewrap/):
#   Bubble_Intact     chunky soft dome with a flared lip, 14 sides, 98 tris.
#                     Toon texture per zone: Bubble_Intact_<Zone>.png (light top,
#                     body, darker rim band, bounce light, painted gloss streak).
#   Bubble_Outline    optional inverted-hull outline for the intact bubble
#                     (normals point inward; dark colour), 98 tris.
#   Bubble_Popped_A/B/C  deflated squishy pancake with a rounded tear (slit,
#                     3-way burst, crooked slit). Smooth shading. Toon texture
#                     per zone: Bubble_Popped_<X>_<Zone>.png.
#   Sheet_Base        6 x 6 stud film tile for a 5 x 5 grid (1.2 stud spacing),
#                     0.04 thick, perforated overlap flap on +X / +Y. Tiles
#                     every 6 studs on floors and walls. Untextured (use Color).
# All bubble textures use the same planar UV (top-down, 1.2 x 1.2 studs).
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(ROOT, "art", "bubblewrap")
PREV = os.path.join(ROOT, "art", "previews")
os.makedirs(ART, exist_ok=True)
os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
NOPREV = "noprev" in ARGS

# ---------------------------------------------------------------- dimensions
R_SKIRT = 0.565      # outer edge of a bubble's footprint (1.13 studs across)
H_DOME = 0.48        # intact bubble height (chunkier than v1's 0.45)
SPACING = 1.2        # bubble grid spacing on a sheet
GRID = 5
TILE = SPACING * GRID  # 6.0 studs: sheets tile every 6 studs
SHEET_T = 0.04       # film thickness; bubbles sit on top of the sheet (z = SHEET_T)
FLAP = 0.05          # overlap flap width on +X / +Y
UV_SPAN = 1.2        # bubbles: planar UV over a 1.2 x 1.2 square
OUTLINE_W = 0.03     # inverted hull thickness
TEX = 512

# Zone palettes (Roblox Color3 0-255). body/light/dark paint the intact bubble,
# pop/gap the popped one, sheet is the sheet's Color.
ZONES = {
    "Blue": dict(body=(80, 190, 255), light=(200, 240, 255), dark=(30, 115, 225), bounce=(150, 225, 255),
                 pop=(140, 205, 250), gap=(14, 36, 96), sheet=(28, 88, 180), outline=(12, 30, 80)),
    "Pink": dict(body=(255, 70, 175), light=(255, 185, 228), dark=(200, 20, 125), bounce=(255, 140, 205),
                 pop=(255, 140, 200), gap=(80, 8, 48), sheet=(130, 20, 95), outline=(70, 5, 45)),
    "Gold": dict(body=(255, 212, 10), light=(255, 248, 160), dark=(235, 155, 0), bounce=(255, 235, 110),
                 pop=(255, 226, 100), gap=(90, 52, 0), sheet=(165, 105, 0), outline=(90, 50, 0)),
    "Neon": dict(body=(60, 235, 40), light=(195, 255, 150), dark=(15, 160, 25), bounce=(140, 255, 110),
                 pop=(145, 230, 120), gap=(8, 50, 12), sheet=(12, 80, 30), outline=(5, 45, 10)),
}
INTACT_T = 0.10      # Roblox Transparency (SmoothPlastic)
POPPED_T = 0.0
SHEET_TR = 0.0


def lin1(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(c):
    return tuple(lin1(x) for x in c)


# ---------------------------------------------------------------- mesh helpers
def make_mesh(name, verts, faces, smooth, vnormals=None, uv_span=UV_SPAN, uvs=None):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bm.verts.index_update()
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        f.smooth = smooth
        for lp in f.loops:
            co = lp.vert.co if uvs is None else uvs[lp.vert.index]
            lp[uvl].uv = (co[0] / uv_span + 0.5, co[1] / uv_span + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if vnormals is not None:
        me.normals_split_custom_set_from_vertices([Vector(n).normalized() for n in vnormals])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def check_mesh(ob, up_only=True):
    me = ob.data
    bad = []
    for p in me.polygons:
        if p.area < 1e-6:
            bad.append(f"{ob.name}: tiny face {p.index}")
        if up_only and p.normal.z <= 0.02:
            bad.append(f"{ob.name}: face {p.index} not facing up (n.z={p.normal.z:.2f})")
    return bad


def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


# ---------------------------------------------------------------- Bubble_Intact
INTACT_RINGS = [  # (radius, height, normal angle from vertical)
    (0.335, 0.456, 0.36),   # flattened top
    (0.478, 0.348, 0.95),   # round shoulder
    (0.522, 0.176, 1.42),   # near-vertical wall
    (R_SKIRT, 0.0, 0.62),   # flared lip: normals tip back up = soft fillet into the film
]


def intact_points():
    rnd = random.Random(7)
    S = 14
    verts = [(0, 0, H_DOME)]
    normals = [(0, 0, 1)]
    for k, (r, z, a) in enumerate(INTACT_RINGS):
        last = k == len(INTACT_RINGS) - 1
        for i in range(S):
            th = 2 * math.pi * i / S + (0.5 * math.pi / S if k % 2 else 0)
            dr = rnd.uniform(-0.003, 0.003) if last else rnd.uniform(-0.007, 0.007)
            dz = 0.0 if last else rnd.uniform(-0.005, 0.005)
            rr = r + dr
            verts.append((rr * math.cos(th), rr * math.sin(th), z + dz))
            normals.append((math.sin(a) * math.cos(th), math.sin(a) * math.sin(th), math.cos(a)))
    faces = [(0, 1 + i, 1 + (i + 1) % S) for i in range(S)]
    for k in range(len(INTACT_RINGS) - 1):
        a0, b0 = 1 + k * S, 1 + (k + 1) * S
        for i in range(S):
            j = (i + 1) % S
            if k % 2 == 0:
                faces.append((a0 + i, b0 + i, a0 + j))
                faces.append((a0 + j, b0 + i, b0 + j))
            else:
                faces.append((a0 + i, b0 + i, b0 + j))
                faces.append((a0 + i, b0 + j, a0 + j))
    return S, verts, normals, faces


# UV radius of each ring = distance along the dome surface from the top,
# scaled to fit the 0.565 footprint, so the wall gets real texture space and
# the toon bands land on clean rings (planar UV squashed the wall).
def _uv_radii():
    pts = [(0.0, H_DOME)] + [(r, z) for r, z, _ in INTACT_RINGS]
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return [R_SKIRT * x / acc[-1] for x in acc]


UV_R = _uv_radii()


def intact_uvs(S, verts):
    uvs = []
    for n, v in enumerate(verts):
        k = 0 if n == 0 else 1 + (n - 1) // S
        a = math.atan2(v[1], v[0])
        uvs.append((UV_R[k] * math.cos(a), UV_R[k] * math.sin(a)))
    return uvs


def build_intact():
    S, verts, normals, faces = intact_points()
    return make_mesh("Bubble_Intact", verts, faces, True, normals, uvs=intact_uvs(S, verts))


def build_outline():
    """Inverted hull: the dome pushed out along its normals, faces reversed so
    only its far side renders (Roblox culls back faces) = a dark rim."""
    S, verts, normals, faces = intact_points()
    out, nrm = [], []
    for n, (v, nv) in enumerate(zip(verts, normals)):
        v, nv = Vector(v), Vector(nv).normalized()
        if n >= 1 + 3 * S:      # lip ring: push straight out, stay on the film
            d = Vector((v.x, v.y, 0)).normalized()
            out.append(tuple(v + d * OUTLINE_W))
        else:
            out.append(tuple(v + nv * OUTLINE_W))
        nrm.append(tuple(-nv))
    faces = [tuple(reversed(f)) for f in faces]
    return make_mesh("Bubble_Outline", out, faces, True, nrm, uvs=intact_uvs(S, verts))


# ---------------------------------------------------------------- Bubble_Popped
POPPED = {
    "A": dict(kind="slit", seed=11, rot=8, off=(0.0, 0.0), a=0.36, b=0.12, bend=0.0, h=1.0),
    "B": dict(kind="star", seed=23, rot=-12, off=(0.01, -0.01), tips=(0, 5, 9), rt=0.36, rv=0.12, h=0.95),
    "C": dict(kind="slit", seed=37, rot=-38, off=(0.04, -0.03), a=0.33, b=0.11, bend=0.5, h=0.85),
}


def popped_layout(p):
    """Lip ring B (tear edge), mid ring M (folds), outer ring C (footprint),
    heights and ridge/valley flags, all in local xy."""
    rnd = random.Random(p["seed"])
    S = 14
    rot = math.radians(p["rot"])
    ox, oy = p["off"]
    th = [2 * math.pi * i / S for i in range(S)]

    def place(x, y):
        return (x * math.cos(rot) - y * math.sin(rot) + ox, x * math.sin(rot) + y * math.cos(rot) + oy)

    B = []
    for i, t in enumerate(th):
        jag = (0.12 if i % 2 else -0.08) + rnd.uniform(-0.05, 0.05)   # gentle: a rounder, cartoon tear
        if p["kind"] == "slit":
            x = p["a"] * math.cos(t)
            y = p["b"] * math.sin(t) * (1 + jag) * (0.55 + 0.45 * abs(math.sin(t)) ** 0.5)
            y += p["bend"] * (x * x - p["a"] ** 2 * 0.4)
        else:
            if i in p["tips"]:
                r = p["rt"] * rnd.uniform(0.94, 1.03)
            else:
                nearest = min(min(abs(i - k), S - abs(i - k)) for k in p["tips"])
                r = p["rv"] * (1.55 if nearest == 1 else 1.0) * (1 + 0.5 * jag)
            x, y = r * math.cos(t), r * math.sin(t)
        B.append(place(x, y))
    C = [(R_SKIRT * math.cos(t + rot), R_SKIRT * math.sin(t + rot)) for t in th]
    ridge = [i % 2 == 0 for i in range(S)]
    for _ in range(2):
        k = rnd.randrange(S)
        ridge[k] = not ridge[k]
    M = []
    for i in range(S):
        f = 0.5 + rnd.uniform(-0.06, 0.06)
        mx = B[i][0] + (C[i][0] - B[i][0]) * f
        my = B[i][1] + (C[i][1] - B[i][1]) * f
        a = rnd.uniform(-0.07, 0.07)
        M.append((mx * math.cos(a) - my * math.sin(a), mx * math.sin(a) + my * math.cos(a)))
    h = p["h"]
    zB = [h * (0.085 + (0.010 if i % 2 else -0.008) + rnd.uniform(-0.006, 0.006)) for i in range(S)]
    if p["kind"] == "star":
        for k in p["tips"]:
            zB[k] = h * 0.055
    zM = [h * ((0.108 if ridge[i] else 0.052) + rnd.uniform(-0.008, 0.008)) for i in range(S)]
    return dict(S=S, B=B, M=M, C=C, zB=zB, zM=zM, ridge=ridge, kind=p["kind"], off=place(0, 0), h=h)


def build_popped(name, p):
    L = popped_layout(p)
    S, B, M, C = L["S"], L["B"], L["M"], L["C"]
    verts = [(x, y, z) for (x, y), z in zip(B, L["zB"])]
    verts += [(x, y, z) for (x, y), z in zip(M, L["zM"])]
    verts += [(x, y, 0.0) for (x, y) in C]
    iB, iM, iC = 0, S, 2 * S
    faces = []
    for a0, b0 in ((iB, iM), (iM, iC)):
        for i in range(S):
            j = (i + 1) % S
            faces.append((a0 + i, b0 + i, b0 + j, a0 + j))
    zf = 0.014
    if L["kind"] == "slit":
        half = S // 2
        fidx = {0: iB + 0, half: iB + half}
        for i in range(1, half):
            x = (B[i][0] + B[S - i][0]) / 2
            y = (B[i][1] + B[S - i][1]) / 2
            fidx[i] = len(verts)
            verts.append((x, y, zf))
        for i in range(half):
            faces.append(tuple(dict.fromkeys([iB + i, iB + i + 1, fidx[i + 1], fidx[i]])))
        for jj in range(half, S):
            faces.append(tuple(dict.fromkeys([iB + jj, iB + (jj + 1) % S, fidx[S - (jj + 1)], fidx[S - jj]])))
    else:
        ci = len(verts)
        verts.append((L["off"][0], L["off"][1], zf))
        for i in range(S):
            faces.append((ci, iB + i, iB + (i + 1) % S))
    ob = make_mesh(name, verts, faces, True)   # smooth: soft squishy folds
    return ob, L


# ---------------------------------------------------------------- toon painting
class Canvas:
    def __init__(self, res=TEX):
        xs = (np.arange(res) + 0.5) / res * UV_SPAN - UV_SPAN / 2
        self.X, self.Y = np.meshgrid(xs, xs)
        self.res = res
        self.rgb = np.zeros((res, res, 3))
        self.px = UV_SPAN / res

    def fill(self, col):
        self.rgb[:] = np.array(col) / 255.0

    def put(self, col, a):
        a = np.clip(a, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - a) + (np.array(col) / 255.0) * a

    def step(self, d, edge):
        """Anti-aliased hard toon edge: 1 where d < edge."""
        return np.clip((edge - d) / (1.5 * self.px) + 0.5, 0, 1)

    def segdist(self, p0, p1):
        X, Y = self.X, self.Y
        vx, vy = p1[0] - p0[0], p1[1] - p0[1]
        ll = vx * vx + vy * vy + 1e-12
        t = np.clip(((X - p0[0]) * vx + (Y - p0[1]) * vy) / ll, 0, 1)
        return np.hypot(X - (p0[0] + t * vx), Y - (p0[1] + t * vy)), t

    def save(self, path):
        res = self.res
        img = bpy.data.images.new(os.path.basename(path)[:-4], res, res, alpha=True)
        px = np.concatenate([self.rgb, np.ones((res, res, 1))], axis=2).astype(np.float32)
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        return img


def mixc(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def paint_intact(path, z):
    """Toon bands seen from above / head-on: light cap, body, darker rim band,
    bounce light low-right, and a white curved gloss streak + dot upper-left
    (upper-left both head-on on a wall and from a camera on -Y over a floor)."""
    cv = Canvas()
    X, Y = cv.X, cv.Y
    r = np.hypot(X, Y)
    ang = np.degrees(np.arctan2(Y, X))
    cv.fill(z["body"])
    cv.put(z["light"], cv.step(np.hypot(X + 0.045, Y - 0.045), 0.16))        # light cap, offset to the light
    rim = 1 - cv.step(r, 0.385)
    cv.put(z["dark"], rim)                                                 # darker rim band
    cv.put(mixc(z["dark"], (0, 0, 0), 0.18), 1 - cv.step(r, 0.50))         # base of the lip, darkest
    # bounce light: thin crescent low-right inside the rim
    t = np.clip((ang + 80) / 70, 0, 1)
    inband = (ang > -80) & (ang < -10)
    w = 0.018 * np.sin(np.pi * t) ** 0.7
    cv.put(z["bounce"], cv.step(np.abs(r - 0.345), w) * inband)
    # gloss streak: curved, tapered, pure white
    t = np.clip((ang - 98) / 74, 0, 1)
    inband = (ang > 98) & (ang < 172)
    w = 0.036 * np.sin(np.pi * t) ** 0.6
    cv.put((255, 255, 255), cv.step(np.abs(r - 0.262), w) * inband)
    dx, dy = 0.262 * math.cos(math.radians(190)), 0.262 * math.sin(math.radians(190))
    cv.put((255, 255, 255), cv.step(np.hypot(X - dx, Y - dy), 0.024))
    return cv.save(path)


def paint_popped(path, L, z):
    """Squishy crumpled pancake: pale zone colour, soft rounded fold shading,
    a light halo and a fat white rim around a rounded dark tear."""
    cv = Canvas()
    X, Y = cv.X, cv.Y
    r = np.hypot(X, Y)
    B, M, C, S = L["B"], L["M"], L["C"], L["S"]
    # paint the tear from a rounded (Chaikin-smoothed) copy of the lip ring
    Bs = list(B)
    for _ in range(3):
        nb = []
        for i in range(len(Bs)):
            a, b = Bs[i], Bs[(i + 1) % len(Bs)]
            nb += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        Bs = nb
    base = z["pop"]
    shade = mixc(z["pop"], z["dark"], 0.55)
    hi = mixc(z["pop"], (255, 255, 255), 0.55)
    cv.fill(base)
    fade = np.clip((R_SKIRT - 0.02 - r) / 0.10, 0, 1)
    for i in range(S):
        for (p0, p1, w0, w1) in ((B[i], M[i], 1.0, 0.9), (M[i], C[i], 0.9, 0.2)):
            d, t = cv.segdist(p0, p1)
            w = (w0 + (w1 - w0) * t) * fade
            if L["ridge"][i]:
                cv.put(hi, 0.85 * w * np.exp(-(d / 0.028) ** 2))
            else:
                cv.put(shade, 0.80 * w * np.exp(-(d / 0.034) ** 2))
    # pancake edge: a soft darker band where it slopes down to the film
    cv.put(shade, 0.55 * np.clip((r - 0.45) / 0.06, 0, 1))
    # tear
    inside = np.zeros_like(X, dtype=bool)
    drim = np.full_like(X, 9.0)
    for i in range(len(Bs)):
        p0, p1 = Bs[i], Bs[(i + 1) % len(Bs)]
        cond = ((p0[1] > Y) != (p1[1] > Y))
        xint = (p1[0] - p0[0]) * (Y - p0[1]) / ((p1[1] - p0[1]) + 1e-12) + p0[0]
        inside ^= cond & (X < xint)
        d, _ = cv.segdist(p0, p1)
        drim = np.minimum(drim, d)
    sd = np.where(inside, -drim, drim)       # signed distance to the tear edge
    cv.put(hi, cv.step(sd, 0.085) * 0.75)                         # light halo
    cv.put((255, 255, 255), cv.step(sd, 0.030))                   # fat white rim
    cv.put(z["gap"], cv.step(sd, -0.008))                         # dark gap
    cv.put(mixc(z["gap"], z["pop"], 0.25), cv.step(sd, -0.008) * (1 - cv.step(-sd, 0.03)) * 0.6)  # soft inner lip
    return cv.save(path)


# ---------------------------------------------------------------- Sheet_Base
def build_sheet():
    rnd = random.Random(5)
    N = 10                       # top grid cells per side (0.6 studs each)
    h = TILE / 2
    top = SHEET_T

    def wrinkle(x, y):
        # frequencies are whole waves per 6-stud tile, so neighbouring tiles match at the seams
        f2, f3 = 2 * math.pi * 2 / TILE, 2 * math.pi * 3 / TILE
        w = 0.004 * math.sin(f2 * x + f3 * y + 0.4) + 0.003 * math.sin(-f3 * x + f2 * y + 2.0)
        edge = max(abs(x), abs(y))
        if edge > h - 0.45:      # a touch of edge waviness, zero AT the edge so tiles meet
            k = (edge - (h - 0.45)) / 0.45
            w += 0.010 * math.sin(math.pi * k) * math.sin(3.1 * (x + y) + 0.7)
        return w

    verts, idx = [], {}
    for i in range(N + 1):
        for j in range(N + 1):
            x = -h + TILE * i / N
            y = -h + TILE * j / N
            if 0 < i < N and 0 < j < N:
                x += rnd.uniform(-0.04, 0.04)
                y += rnd.uniform(-0.04, 0.04)
            idx[i, j] = len(verts)
            verts.append((x, y, top + wrinkle(x, y)))
    faces = []
    for i in range(N):
        for j in range(N):
            faces.append((idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]))
    loop = [idx[i, 0] for i in range(N)] + [idx[N, j] for j in range(N)] + \
           [idx[i, N] for i in range(N, 0, -1)] + [idx[0, j] for j in range(N, 0, -1)]
    bot = {}
    for v in loop:
        x, y, _ = verts[v]
        bot[v] = len(verts)
        verts.append((x, y, 0.0))
    for k in range(len(loop)):
        a, b = loop[k], loop[(k + 1) % len(loop)]
        faces.append((a, bot[a], bot[b], b))

    def flap(points, outward):
        n = len(points)
        ox, oy = outward
        inner, outer = [], []
        for (x, y, z) in points:
            inner.append(len(verts))
            verts.append((x, y, z + 0.012))
        for s, (x, y, z) in enumerate(points):
            tooth = FLAP if s % 2 == 0 else FLAP * 0.45
            if s in (0, n - 1):
                tooth = FLAP * 0.45
            outer.append(len(verts))
            verts.append((x + ox * tooth, y + oy * tooth, top + 0.010))
        for s in range(n - 1):
            a, b, c, d = inner[s], outer[s], outer[s + 1], inner[s + 1]
            faces.append((a, b, c, d) if (ox, oy) == (1, 0) else (a, d, c, b))
        return outer

    M2 = 2 * N  # flap points every 0.3 studs (perforation teeth)
    px = [(h, -h + TILE * s / M2, top + wrinkle(h, -h + TILE * s / M2)) for s in range(M2 + 1)]
    py = [(-h + TILE * s / M2, h, top + wrinkle(-h + TILE * s / M2, h)) for s in range(M2 + 1)]
    for outs, d in ((flap(px, (1, 0)), (1, 0)), (flap(py, (0, 1)), (0, 1))):
        lowv = []
        for v in outs:
            x, y, z = verts[v]
            lowv.append(len(verts))
            verts.append((x, y, SHEET_T - 0.002))
        for s in range(len(outs) - 1):
            a, b = outs[s], outs[s + 1]
            faces.append((a, lowv[s], lowv[s + 1], b) if d == (1, 0) else (b, lowv[s + 1], lowv[s], a))
    return make_mesh("Sheet_Base", verts, faces, True, uv_span=TILE + 2 * FLAP)


# ---------------------------------------------------------------- export
def export(ob, extra=None):
    half_turn = Matrix.Rotation(math.pi, 4, "Z")
    me = ob.data
    xs = [v.co for v in me.vertices]
    lo = Vector([min(c[i] for c in xs) for i in range(3)])
    hi = Vector([max(c[i] for c in xs) for i in range(3)])
    bounds = {ob.name: {
        "size": [round(hi.x - lo.x, 4), round(hi.z - lo.z, 4), round(hi.y - lo.y, 4)],
        "center": [round((hi.x + lo.x) / 2, 4), round((hi.z + lo.z) / 2, 4), round(-(hi.y + lo.y) / 2, 4)],
        "tris": tris(ob),
        "origin": "bottom centre of footprint",
    }}
    if extra:
        bounds[ob.name].update(extra)
    me.transform(half_turn)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(ART, ob.name + ".fbx"), use_selection=True, object_types={"MESH"}, mesh_smooth_type="OFF",
        use_triangles=True, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    me.transform(half_turn)
    with open(os.path.join(ART, ob.name + ".bounds.json"), "w") as f:
        json.dump(bounds, f, indent=1)


# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    m.use_backface_culling = True          # Roblox culls back faces too
    return m, nt, nt.nodes.new, nt.links.new


def roblox_mat(name, color=None, img=None, transp=0.0, rough=0.35, emit=0.0):
    """Roblox SmoothPlastic approximation: texture (or Color), mild specular,
    uniform Transparency, nothing Roblox can't show."""
    m, nt, N, L = node_mat(name)
    out = N("ShaderNodeOutputMaterial")
    p = N("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = 0.4
    if img is not None:
        tex = N("ShaderNodeTexImage")
        tex.image = img
        src = tex.outputs["Color"]
        L(src, p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = lin(color) + (1,)
        src = None
    if emit:
        p.inputs["Emission Strength"].default_value = emit
        if src is not None:
            L(src, p.inputs["Emission Color"])
        else:
            p.inputs["Emission Color"].default_value = lin(color) + (1,)
    shader = p.outputs[0]
    if transp > 0:
        tr = N("ShaderNodeBsdfTransparent")
        ms = N("ShaderNodeMixShader")
        ms.inputs[0].default_value = 1 - transp
        L(tr.outputs[0], ms.inputs[1])
        L(shader, ms.inputs[2])
        shader = ms.outputs[0]
        m.surface_render_method = "DITHERED"
    L(shader, out.inputs["Surface"])
    return m


def checker_mat(name, c1, c2, square=4.0):
    m, nt, N, L = node_mat(name)
    out = N("ShaderNodeOutputMaterial")
    p = N("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.6
    tc = N("ShaderNodeTexCoord")
    ck = N("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 1.0 / square
    ck.inputs["Color1"].default_value = lin(c1) + (1,)
    ck.inputs["Color2"].default_value = lin(c2) + (1,)
    L(tc.outputs["Object"], ck.inputs["Vector"])
    L(ck.outputs["Color"], p.inputs["Base Color"])
    L(p.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- scene
def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16 if FAST else 96
    try:
        sc.eevee.use_raytracing = True
    except AttributeError:
        pass
    sc.view_settings.view_transform = "Standard"   # keeps toon colours true (no filmic desaturation)
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    tc = N("ShaderNodeTexCoord")
    sx = N("ShaderNodeSeparateXYZ")
    mp = N("ShaderNodeMapRange")
    mp.inputs["From Min"].default_value = -0.2
    mp.inputs["From Max"].default_value = 1.0
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = lin((200, 222, 245)) + (1,)
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = lin((95, 160, 235)) + (1,)
    bg = N("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.8
    out = N("ShaderNodeOutputWorld")
    L(tc.outputs["Generated"], sx.inputs[0])
    L(sx.outputs["Z"], mp.inputs["Value"])
    L(mp.outputs[0], cr.inputs[0])
    L(cr.outputs[0], bg.inputs[0])
    L(bg.outputs[0], out.inputs["Surface"])
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.6
    sun.angle = math.radians(6)
    sun.color = (1.0, 0.97, 0.92)
    so = bpy.data.objects.new("Sun", sun)
    sc.collection.objects.link(so)
    sun_dir = Vector((-0.55, -0.35, 0.76)).normalized()
    so.rotation_euler = (-sun_dir).to_track_quat("-Z", "Y").to_euler()
    return sc


def camera(name, loc, target, lens=None, vfov=None, ortho=None, dof=None):
    cd = bpy.data.cameras.new(name)
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.clip_start = 0.05
    cd.clip_end = 1000
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
        cd.clip_end = 40
    elif vfov:
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(vfov)
    else:
        cd.lens = lens or 50
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
        cd.dof.aperture_fstop = dof
    return co


def render(cam, path, res):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if FAST else 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


def inst(src, mat, parent=None, loc=(0, 0, 0), rz=0.0, name=None):
    o = bpy.data.objects.new(name or (src.name + "_i"), src.data)
    bpy.context.scene.collection.objects.link(o)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    o.location = loc
    o.rotation_euler = (0, 0, rz)
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    return e


def set_visible(objs, on):
    for o in objs:
        o.hide_render = not on


# ---------------------------------------------------------------- main
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render()
    problems = []

    # stale v1 outputs this script no longer makes
    for f in ("Bubble_Shine.fbx", "Bubble_Shine.bounds.json", "Bubble_Popped_A.png", "Bubble_Popped_B.png", "Bubble_Popped_C.png"):
        if os.path.exists(os.path.join(ART, f)):
            os.remove(os.path.join(ART, f))
    if os.path.exists(os.path.join(PREV, "qa_Bubble_Shine.png")):
        os.remove(os.path.join(PREV, "qa_Bubble_Shine.png"))

    intact = build_intact()
    outline = build_outline()
    popped, layouts = {}, {}
    for k, p in POPPED.items():
        popped[k], layouts[k] = build_popped("Bubble_Popped_" + k, p)
    sheet = build_sheet()
    sources = [intact, outline] + list(popped.values()) + [sheet]
    for o in [intact] + list(popped.values()):
        problems += check_mesh(o)

    # textures per zone
    tex = {z: {"intact": paint_intact(os.path.join(ART, f"Bubble_Intact_{z}.png"), d),
               "popped": {k: paint_popped(os.path.join(ART, f"Bubble_Popped_{k}_{z}.png"), layouts[k], d) for k in POPPED}}
           for z, d in ZONES.items()}

    # preview / export materials per zone
    mats = {}
    for z, d in ZONES.items():
        neon = z == "Neon"
        mats[z] = dict(
            intact=roblox_mat(f"{z}_Intact", img=tex[z]["intact"], transp=INTACT_T, rough=0.3),
            popped={k: roblox_mat(f"{z}_Popped_{k}", img=tex[z]["popped"][k], transp=POPPED_T, rough=0.45) for k in POPPED},
            sheet=roblox_mat(f"{z}_Sheet", color=d["sheet"], transp=SHEET_TR, rough=0.4),
            outline=roblox_mat(f"{z}_Outline", color=d["outline"], rough=0.8) if not neon else
            roblox_mat(f"{z}_Outline", color=(20, 150, 30), rough=0.8, emit=2.5),   # Neon material outline
        )
    intact.data.materials.append(mats["Blue"]["intact"])
    outline.data.materials.append(mats["Blue"]["outline"])
    for k, o in popped.items():
        o.data.materials.append(mats["Blue"]["popped"][k])
    sheet.data.materials.append(mats["Blue"]["sheet"])

    report = {}
    for o in sources:
        extra = {}
        if o is intact:
            extra["textures"] = [f"Bubble_Intact_{z}.png" for z in ZONES]
        if o.name.startswith("Bubble_Popped"):
            extra["textures"] = [f"{o.name}_{z}.png" for z in ZONES]
        if o is outline:
            extra["note"] = "optional inverted hull for Bubble_Intact, same origin; dark SmoothPlastic or Neon, no texture"
        if o is sheet:
            extra["note"] = "tiles every 6 studs; top surface (where bubbles sit) is 0.04 above the origin; +X/+Y flap overlaps the neighbour"
        export(o, extra)
        report[o.name] = tris(o)
    set_visible(sources, False)
    print("TRIS", json.dumps(report))
    print("PROBLEMS", problems)
    if NOPREV:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, "bubblewrap.blend"))
        return

    outlines = []

    def wrap_sheet(parent, zone, pattern, seed=0):
        mz = mats[zone]
        inst(sheet, mz["sheet"], parent)
        rnd = random.Random(seed)
        for i in range(GRID):
            for j in range(GRID):
                x, y = (i - 2) * SPACING, (j - 2) * SPACING
                k = pattern(i, j)
                if k is None:
                    inst(intact, mz["intact"], parent, (x, y, SHEET_T))
                    outlines.append(inst(outline, mz["outline"], parent, (x, y, SHEET_T)))
                else:
                    inst(popped[k], mz["popped"][k], parent, (x, y, SHEET_T), rz=rnd.choice((0, 1, 2, 3)) * math.pi / 2)

    def rnd_pattern(seed, frac):
        r = random.Random(seed)
        cache = {}

        def f(i, j):
            if (i, j) not in cache:
                cache[i, j] = r.choice("ABC") if r.random() < frac else None
            return cache[i, j]
        return f

    floor_mat = checker_mat("P_Floor", (250, 250, 255), (225, 230, 245))

    def ground(loc, size, mat=floor_mat):
        bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
        g = bpy.context.active_object
        g.data.materials.append(mat)
        return g

    # 1. hero close-up
    H = Vector((0, 0, 0))
    ground(H + Vector((0, 0, -0.001)), 40)
    hp = empty("Hero", H)
    hero_pat = {(0, 0): "A", (1, 1): "B", (2, 0): "C", (3, 1): "A", (1, 2): "C", (4, 0): "B"}
    wrap_sheet(hp, "Blue", lambda i, j: hero_pat.get((i, j)), seed=3)
    tgt = H + Vector((-1.2, -1.9, 0.18))
    cam_hero = camera("CamHero", tgt + Vector((0.9, -3.0, 2.3)), tgt, lens=45, dof=6.0)

    # 2. full 5x5 sheet
    S2 = Vector((40, 0, 0))
    ground(S2 + Vector((0, 0, -0.001)), 40)
    wrap_sheet(empty("Sheet5x5", S2), "Blue", rnd_pattern(9, 0.35), seed=4)
    cam_sheet = camera("CamSheet", S2 + Vector((3.2, -7.4, 7.6)), S2 + Vector((0, 0, 0.1)), lens=50)

    # 3a. first person: wall covered in wrap, ~4 studs away
    W = Vector((0, 80, 0))
    ground(W + Vector((0, -10, -0.001)), 60)
    for a in range(-2, 3):
        for b in range(0, 3):
            e = empty(f"Wall_{a}_{b}", W + Vector((a * TILE, 0, b * TILE + TILE / 2)), (math.radians(90), 0, 0))
            cx, cz = a * TILE, b * TILE + TILE / 2

            def pat(i, j, cx=cx, cz=cz, r=random.Random(a * 7 + b)):
                x = cx + (i - 2) * SPACING
                z = cz + (j - 2) * SPACING
                d = math.hypot(x - 1.4, z - 5.6)
                p = 0.75 if d < 1.9 else (0.25 if d < 3.2 else 0.06)
                return r.choice("ABC") if r.random() < p else None
            wrap_sheet(e, "Blue", pat, seed=a * 13 + b)
    cam_wall = camera("CamWall", W + Vector((0.3, -4.0, 5.0)), W + Vector((0.3, 0, 4.9)), vfov=70)

    # 3b. first person: looking down at the floor wrap
    F = Vector((80, 80, 0))
    ground(F + Vector((0, 0, -0.001)), 80)
    for a in range(-2, 3):
        for b in range(-1, 4):
            e = empty(f"Floor_{a}_{b}", F + Vector((a * TILE, b * TILE, 0)))
            cx, cy = a * TILE, b * TILE

            def patf(i, j, cx=cx, cy=cy, r=random.Random(a * 5 + b * 3 + 1)):
                x = cx + (i - 2) * SPACING
                y = cy + (j - 2) * SPACING
                on_path = abs(x - 0.25 * y - 0.6) < 1.0 and y < 2.0
                return r.choice("ABC") if (on_path and r.random() < 0.9) or r.random() < 0.05 else None
            wrap_sheet(e, "Blue", patf, seed=a * 3 + b)
    cam_floor = camera("CamFloor", F + Vector((0, -2.6, 4.6 + SHEET_T)), F + Vector((0.4, 1.3, 0)), vfov=70)

    # 4. colour variants: each zone = 2 intact + 1 popped + 1 intact on a pad of its sheet colour
    V = Vector((0, -120, 0))
    ground(V + Vector((0, 0, -0.001)), 60, roblox_mat("P_Neutral", color=(235, 238, 245), rough=0.7))
    for n, z in enumerate(ZONES):
        mz = mats[z]
        base = V + Vector(((n - 1.5) * 3.1, 0, SHEET_T))
        for (dx, dy, k) in ((-0.6, 0.6, None), (0.6, 0.6, None), (-0.6, -0.6, "A"), (0.6, -0.6, None)):
            if k is None:
                inst(intact, mz["intact"], None, base + Vector((dx, dy, 0)))
            else:
                inst(popped[k], mz["popped"][k], None, base + Vector((dx, dy, 0)))
        bpy.ops.mesh.primitive_cube_add(size=1, location=base + Vector((0, 0, -SHEET_T / 2)))
        pad = bpy.context.active_object
        pad.scale = (2.6, 2.6, SHEET_T)
        pad.data.materials.append(mz["sheet"])
    cam_var = camera("CamVariants", V + Vector((0, -10.5, 6.4)), V + Vector((0, 0, 0.1)), lens=30)

    # QA turnarounds (clay + wire)
    clay = roblox_mat("QA_Clay", color=(190, 196, 210), rough=0.45)
    wire = roblox_mat("QA_Wire", color=(25, 30, 60), rough=0.9)
    wire.use_backface_culling = False
    qa = []
    for n, src in enumerate(sources):
        base = Vector((200 + n * 30, -300 - n * 30, 0))
        inst(src, clay, None, base, name="QA_" + src.name)
        w = inst(src, wire, None, base, name="QAW_" + src.name)
        mod = w.modifiers.new("Wire", "WIREFRAME")
        mod.thickness = 0.004 if src is not sheet else 0.012
        qa.append((src, base))
    clay.use_backface_culling = False

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, "bubblewrap.blend"))

    set_visible(outlines, False)
    render(cam_hero, os.path.join(PREV, "bubblewrap_hero.png"), (1600, 1000))
    render(cam_sheet, os.path.join(PREV, "bubblewrap_sheet_5x5.png"), (1400, 1200))
    render(cam_wall, os.path.join(PREV, "bubblewrap_fp_wall.png"), (1600, 900))
    crosshair(os.path.join(PREV, "bubblewrap_fp_wall.png"))
    render(cam_floor, os.path.join(PREV, "bubblewrap_fp_floor.png"), (1600, 900))
    crosshair(os.path.join(PREV, "bubblewrap_fp_floor.png"))
    render(cam_var, os.path.join(PREV, "bubblewrap_colour_variants.png"), (2000, 760))
    set_visible(outlines, True)
    render(cam_wall, os.path.join(PREV, "bubblewrap_fp_wall_outline.png"), (1600, 900))
    crosshair(os.path.join(PREV, "bubblewrap_fp_wall_outline.png"))
    render(cam_hero, os.path.join(PREV, "bubblewrap_hero_outline.png"), (1600, 1000))
    set_visible(outlines, False)
    side_by_side([os.path.join(PREV, n) for n in ("bubblewrap_fp_wall_v1.png", "bubblewrap_fp_wall.png", "bubblewrap_fp_wall_outline.png")],
                 os.path.join(PREV, "bubblewrap_wall_v1_vs_v2.png"))

    for src, base in qa:
        lo = Vector([min(v.co[i] for v in src.data.vertices) for i in range(3)])
        hi = Vector([max(v.co[i] for v in src.data.vertices) for i in range(3)])
        mid = base + (lo + hi) / 2
        ext = max(hi.x - lo.x, hi.y - lo.y) * 1.25
        views = [("front", Vector((0, -10, 0))), ("side", Vector((10, 0, 0))), ("back", Vector((0, 10, 0))),
                 ("top", Vector((0, -0.001, 10))), ("34", Vector((5, -7, 5)))]
        paths = []
        for vn, off in views:
            c = camera(f"QA_{src.name}_{vn}", mid + off, mid, ortho=ext)
            pth = os.path.join(PREV, f"_qa_{src.name}_{vn}.png")
            render(c, pth, (600, 450))
            paths.append(pth)
        stitch(paths, os.path.join(PREV, f"qa_{src.name}.png"))


def load_px(p):
    im = bpy.data.images.load(p)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    bpy.data.images.remove(im)
    return a


def save_px(a, out):
    img = bpy.data.images.new("px", a.shape[1], a.shape[0], alpha=True)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print("RENDER", out)


def stitch(paths, out):
    ims = [load_px(p) for p in paths]
    for p in paths:
        os.remove(p)
    h, w = ims[0].shape[:2]
    cols = 3
    rows = (len(ims) + cols - 1) // cols
    canvas = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for n, a in enumerate(ims):
        r, c = divmod(n, cols)
        r = rows - 1 - r
        canvas[r * h:(r + 1) * h, c * w:(c + 1) * w] = a
    save_px(canvas, out)


def side_by_side(paths, out):
    ims = [load_px(p) for p in paths if os.path.exists(p)]
    h = min(a.shape[0] for a in ims)
    ims = [a[::2, ::2] if a.shape[0] > h else a for a in ims]   # the fast v1 file may be half size
    ims = [a[:h // 2 * 2:2, ::2] if a.shape[0] == h and h > 600 else a for a in ims]
    h = min(a.shape[0] for a in ims)
    gap = np.ones((h, 12, 4), dtype=np.float32)
    row = []
    for a in ims:
        row += [a[:h], gap]
    save_px(np.concatenate(row[:-1], axis=1), out)


def crosshair(path):
    a = load_px(path)
    h, w = a.shape[:2]
    cx, cy = w // 2, h // 2
    s = max(1, w // 800)
    L, T = 12 * s, 2 * s
    for col, pad in (((0.05, 0.05, 0.1), 2 * s), ((1, 1, 1), 0)):
        a[cy - T - pad:cy + T + pad, cx - L - pad:cx + L + pad, :3] = col
        a[cy - L - pad:cy + L + pad, cx - T - pad:cx + T + pad, :3] = col
    save_px(a, path)


main()
