# BubblePop "Crystals" icon: 10 design options for the owner to pick from.
# Background Blender only:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_crystal_options.py
#   (add "-- 3 7" after the script to rebuild only those numbers; the sheet is
#    always rebuilt from whatever PNGs are on disk)
#
# Same look as build_crystal_icon.py: Workbench FLAT shading, per-facet toon
# colours chosen here from each face normal vs a fixed light, inverted-hull
# navy outline (RGB 20,40,110), orthographic camera auto-fitted with padding,
# transparent film.
#
# Outputs: art/icons/crystal_options/Crystal_01.png .. Crystal_10.png (512x512)
#          art/previews/crystal_options_sheet.png (5x2 grid, numbered)
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
OUT = os.path.join(ROOT, "art", "icons", "crystal_options")
PREV = os.path.join(ROOT, "art", "previews")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = {int(a) for a in ARGS if a.isdigit()}
FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

NAVY = (20, 40, 110)
WHITE = (255, 255, 255)
CYAN_HI = (215, 252, 255)
CYAN = (110, 235, 255)

# palettes: hi, mid, low, deep (sides) + top_hi, top (lit cap facets)
PAL = {
    "magenta": dict(hi=(255, 125, 232), mid=(218, 40, 196), low=(146, 36, 214), deep=(84, 24, 160), top_hi=CYAN_HI, top=CYAN),
    "violet": dict(hi=(214, 140, 255), mid=(160, 70, 240), low=(112, 40, 200), deep=(70, 22, 150), top_hi=(250, 220, 255), top=(255, 140, 235)),
    "teal": dict(hi=(130, 255, 225), mid=(0, 205, 185), low=(0, 140, 165), deep=(12, 85, 135), top_hi=(235, 255, 250), top=(150, 255, 235)),
    "bluepurple": dict(hi=(160, 160, 255), mid=(105, 90, 245), low=(78, 52, 205), deep=(50, 30, 150), top_hi=CYAN_HI, top=CYAN),
    "pinkwhite": dict(hi=(255, 240, 252), mid=(255, 180, 232), low=(238, 115, 208), deep=(185, 60, 178), top_hi=WHITE, top=(220, 250, 255)),
    "stone": dict(hi=(175, 178, 210), mid=(128, 130, 172), low=(92, 92, 135), deep=(60, 60, 105), top_hi=(200, 205, 230), top=(175, 178, 210)),
    "halo": dict(hi=(255, 235, 250), mid=(255, 200, 245), low=(255, 200, 245), deep=(255, 200, 245), top_hi=WHITE, top=WHITE),
}

# ------------------------------------------------------------------ kit
STATE = {}


def reset(az_deg, el_deg):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rot = Matrix.Rotation(math.radians(az_deg), 3, 'Z') @ Matrix.Rotation(-math.radians(el_deg), 3, 'X')
    STATE["rot"] = rot
    STATE["fwd"] = rot @ Vector((0, 1, 0))
    STATE["right"] = rot @ Vector((1, 0, 0))
    STATE["up"] = rot @ Vector((0, 0, 1))
    # light from upper-left-front, turned with the camera azimuth
    STATE["light"] = (Matrix.Rotation(math.radians(az_deg), 3, 'Z') @ Vector((-0.85, -0.35, 0.60))).normalized()
    STATE["solids"] = []
    STATE["flats"] = []


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def band(n, pal, top):
    d = n.dot(STATE["light"])
    if top and d > 0.75:
        return pal["top_hi"]
    if top and d > 0.40:
        return pal["top"]
    if d > 0.60:
        return pal["hi"]
    if d > 0.15:
        return pal["mid"]
    if d > -0.35:
        return pal["low"]
    return pal["deep"]


def add_obj(name, bm, mat=Matrix()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = mat
    return ob


def paint(ob, fn):
    me = ob.data
    if "Col" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["Col"])
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = attr
    me.color_attributes.render_color_index = 0
    mw = ob.matrix_world
    zs = [(mw @ v.co).z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    rot = mw.to_3x3()
    for poly in me.polygons:
        n = (rot @ poly.normal).normalized()
        zc = ((mw @ poly.center).z - zmin) / max(1e-6, zmax - zmin)
        c = fn(poly, n, zc)
        for li in poly.loop_indices:
            attr.data[li].color_srgb = (c[0] / 255, c[1] / 255, c[2] / 255, 1.0)


def solid(name, bm, mat, pal, top="tri", grad=0.6, colour_fn=None):
    """A faceted solid, toon-painted. top: 'tri' = triangle faces are cap
    facets, 'up' = faces pointing up are cap facets, None = no cap colours."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = add_obj(name, bm, mat)
    p = PAL[pal]

    def fn(poly, n, z):
        if colour_fn:
            c = colour_fn(poly, n, z)
            if c:
                return c
        is_top = (top == "tri" and len(poly.vertices) == 3) or (top == "up" and n.z > 0.55)
        c = band(n, p, is_top)
        return lerp(c, p["deep"], max(0.0, 0.35 - z) * grad)
    paint(ob, fn)
    STATE["solids"].append(ob)
    return ob


def hull(src, thick):
    me = src.data.copy()
    ob = bpy.data.objects.new(src.name + "_Outline", me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = src.matrix_world.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    s = sum(src.matrix_world.to_scale()) / 3
    for v in bm.verts:
        n = v.normal
        cosang = min((f.normal.dot(n) for f in v.link_faces), default=1.0)
        v.co += n * (thick / s) / max(0.45, cosang)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    paint(ob, lambda p, n, z: NAVY)
    return ob


def flat_poly(name, pts2d, centre, depth, colour, outline=0.0, hollow_centre=False):
    """Flat shape in the camera plane (pts in screen units: right, up).
    depth: distance toward the camera (+) or away (-) from `centre`.
    outline > 0 also adds a navy copy grown by that much just behind."""
    def make(pts, d, col, nm):
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in pts]
        c = bm.verts.new((sum(p[0] for p in pts) / len(pts), 0, sum(p[2] for p in pts) / len(pts)))
        for i in range(len(vs)):
            bm.faces.new((c, vs[i], vs[(i + 1) % len(vs)]))
        m = Matrix.Translation(centre - STATE["fwd"] * d) @ STATE["rot"].to_4x4()
        ob = add_obj(nm, bm, m)
        paint(ob, lambda p, n, z: col)
        STATE["flats"].append(ob)
        return ob
    pts = [(x, 0.0, y) for x, y in pts2d]
    ob = make(pts, depth, colour, name)
    if outline > 0:
        grown = []
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[2] for p in pts) / len(pts)
        n = len(pts)
        for i, p in enumerate(pts):
            # push each point out along the average of its two edge normals
            a, b = pts[i - 1], pts[(i + 1) % n]
            e1 = Vector((p[0] - a[0], p[2] - a[2])).normalized()
            e2 = Vector((b[0] - p[0], b[2] - p[2])).normalized()
            n1 = Vector((e1.y, -e1.x))
            n2 = Vector((e2.y, -e2.x))
            nn = (n1 + n2)
            if nn.length < 1e-6:
                nn = n1
            nn.normalize()
            # make sure it points outward
            if nn.dot(Vector((p[0] - cx, p[2] - cy))) < 0:
                nn = -nn
            k = outline / max(0.35, nn.dot(n1))
            grown.append((p[0] + nn.x * k, 0.0, p[2] + nn.y * k))
        make(grown, depth - 0.01, NAVY, name + "_Outline")
    return ob


def star_pts(r_out, r_in, points=4, rot=0.0):
    out = []
    for i in range(points * 2):
        a = math.pi / 2 + rot + math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        out.append((math.cos(a) * r, math.sin(a) * r))
    return out


def circle_pts(r, n=40):
    return [(math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r) for i in range(n)]


def sparkle(name, sx, sy, size, thick, colour=WHITE):
    """sx, sy: screen position as fraction of the solid bounds (-1..1)."""
    STATE.setdefault("sparkles", []).append((name, sx, sy, size, colour))


# ------------------------------------------------------------- shapes
def crystal_bm(radius, height, shoulder, sides=6, taper=0.78, twist=0.0, point_bottom=0.0):
    bm = bmesh.new()
    base, sh = [], []
    for i in range(sides):
        a = twist + 2 * math.pi * i / sides
        base.append(bm.verts.new((math.cos(a) * radius * taper, math.sin(a) * radius * taper, 0.0)))
        sh.append(bm.verts.new((math.cos(a) * radius, math.sin(a) * radius, height * shoulder)))
    apex = bm.verts.new((0, 0, height))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((base[i], base[j], sh[j], sh[i]))
        bm.faces.new((sh[i], sh[j], apex))
    if point_bottom > 0:
        bot = bm.verts.new((0, 0, -point_bottom))
        for i in range(sides):
            bm.faces.new((base[(i + 1) % sides], base[i], bot))
    else:
        bm.faces.new(list(reversed(base)))
    return bm


def bipyramid_bm(sides, r, h_top, h_bot, twist=0.0, table=0.0, table_r=0.55, crown_z=None):
    """Classic gem: optional flat table, girdle ring, pointed pavilion."""
    bm = bmesh.new()
    ring = [bm.verts.new((math.cos(twist + 2 * math.pi * i / sides) * r,
                          math.sin(twist + 2 * math.pi * i / sides) * r, 0.0)) for i in range(sides)]
    bot = bm.verts.new((0, 0, -h_bot))
    for i in range(sides):
        bm.faces.new((ring[(i + 1) % sides], ring[i], bot))
    if table > 0:
        tb = [bm.verts.new((math.cos(twist + 2 * math.pi * (i + 0.5) / sides) * r * table_r,
                            math.sin(twist + 2 * math.pi * (i + 0.5) / sides) * r * table_r, h_top)) for i in range(sides)]
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((ring[i], ring[j], tb[i]))
            bm.faces.new((tb[i], ring[j], tb[j]))
        bm.faces.new(tb)
    else:
        top = bm.verts.new((0, 0, h_top))
        for i in range(sides):
            bm.faces.new((ring[i], ring[(i + 1) % sides], top))
    return bm


def brilliant_simple(r, table_r, crown_h, girdle_h, pav_h, n):
    """Round brilliant (chunky): 8-sided table, 16-point girdle, kite+star crown
    facets, pointed pavilion with 16 facets."""
    bm = bmesh.new()
    m = 2 * n
    t = [bm.verts.new((math.cos(2 * math.pi * i / n) * r * table_r,
                       math.sin(2 * math.pi * i / n) * r * table_r, crown_h)) for i in range(n)]
    gu = [bm.verts.new((math.cos(2 * math.pi * k / m) * r, math.sin(2 * math.pi * k / m) * r, girdle_h)) for k in range(m)]
    gl = [bm.verts.new((math.cos(2 * math.pi * k / m) * r, math.sin(2 * math.pi * k / m) * r, 0.0)) for k in range(m)]
    bot = bm.verts.new((0, 0, -pav_h))
    bm.faces.new(t)
    for i in range(n):
        j = (i + 1) % n
        a, b, c = gu[2 * i], gu[2 * i + 1], gu[(2 * i + 2) % m]
        bm.faces.new((t[i], a, b))       # upper girdle facet
        bm.faces.new((t[i], b, t[j]))    # star facet
        bm.faces.new((t[j], b, c))       # upper girdle facet
    for k in range(m):
        k2 = (k + 1) % m
        bm.faces.new((gl[k], gl[k2], gu[k2], gu[k]))
        bm.faces.new((gl[k2], gl[k], bot))
    return bm


def heart_bm(size=1.0, depth=0.45, n=28):
    pts = []
    for i in range(n):
        tt = 2 * math.pi * i / n
        x = 16 * math.sin(tt) ** 3
        y = 13 * math.cos(tt) - 5 * math.cos(2 * tt) - 2 * math.cos(3 * tt) - math.cos(4 * tt)
        pts.append((x / 16 * size, (y + 2) / 16 * size))
    bm = bmesh.new()
    outer = [bm.verts.new((x, 0.0, z)) for x, z in pts]
    cx, cz = 0.0, -0.05 * size
    inner = [bm.verts.new((cx + (x - cx) * 0.55, -depth * 0.75, cz + (z - cz) * 0.55)) for x, z in pts]
    back_inner = [bm.verts.new((cx + (x - cx) * 0.55, depth * 0.55, cz + (z - cz) * 0.55)) for x, z in pts]
    fc = bm.verts.new((cx, -depth, cz))
    bc = bm.verts.new((cx, depth * 0.7, cz))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
        bm.faces.new((inner[i], inner[j], fc))
        bm.faces.new((outer[j], outer[i], back_inner[i], back_inner[j]))
        bm.faces.new((back_inner[j], back_inner[i], bc))
    return bm


def orb_bm(r=1.0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)   # 80 facets
    return bm


def rock_bm(seed=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    rnd = random.Random(seed)
    for v in bm.verts:
        v.co *= 1.0 + rnd.uniform(-0.12, 0.12)
        v.co.z = max(v.co.z, -0.3)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.05)
    return bm


# ------------------------------------------------------------ designs
def T(x, y, z):
    return Matrix.Translation((x, y, z))


def R(deg, axis):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def d01():   # the approved 3-crystal cluster
    reset(-18, 24)
    solid("Main", crystal_bm(0.62, 2.55, 0.66, twist=math.radians(42)), T(0.05, 0, -1.25) @ R(5, 'Y'), "magenta")
    solid("Left", crystal_bm(0.40, 1.45, 0.62, twist=math.radians(25)), T(-0.62, -0.05, -1.30) @ R(-34, 'Y') @ R(4, 'X'), "magenta")
    solid("Right", crystal_bm(0.34, 1.10, 0.60, twist=math.radians(5)), T(0.62, -0.12, -1.32) @ R(38, 'Y') @ R(6, 'X'), "magenta")
    sparkle("S1", 0.78, 0.62, 0.24, 0)
    sparkle("S2", -0.80, 0.30, 0.13, 0)


def d02():   # round brilliant, seen from above-front
    reset(-10, 34)
    pal = PAL["bluepurple"]

    def facet(p, n, z):
        if n.z > 0.97:
            return CYAN_HI                      # table
        if n.z > 0.2:                           # crown: alternate bright / dark
            c = band(n, pal, False)
            return lerp(c, CYAN, 0.45) if p.index % 2 == 0 else c
        return None
    solid("Gem", brilliant_simple(1.0, 0.56, 0.42, 0.08, 0.95, 8), R(-6, 'Y'), "bluepurple", top=None,
          colour_fn=facet, grad=0.0)
    sparkle("S1", 0.80, 0.75, 0.30, 0)
    sparkle("S2", -0.85, -0.55, 0.14, 0)


def d03():   # tall single shard
    reset(-20, 18)
    bm = crystal_bm(0.66, 2.7, 0.70, sides=5, taper=0.88, twist=math.radians(20), point_bottom=0.6)
    solid("Shard", bm, R(-20, 'Y') @ R(8, 'X'), "violet")
    sparkle("S1", 0.85, 0.70, 0.30, 0)
    sparkle("S2", -0.90, -0.30, 0.15, 0)


def d04():   # faceted orb gem
    reset(-15, 18)
    pal = PAL["pinkwhite"]

    def facet(p, n, z):
        c = band(n, pal, False)
        # checker the facets so the cut reads: odd ones a step darker/pinker
        return lerp(c, (230, 60, 200), 0.22) if (p.index * 7) % 3 == 0 else c
    solid("Orb", orb_bm(1.0), R(-10, 'Z') @ R(-12, 'X'), "pinkwhite", top=None, grad=0.0,
          colour_fn=facet)
    sparkle("S1", 0.78, 0.78, 0.28, 0)
    sparkle("S2", -0.95, -0.55, 0.13, 0)


def d05():   # heart gem
    reset(-14, 10)
    solid("Heart", heart_bm(1.0, 0.42), R(-12, 'Z'), "magenta", top=None, grad=0.3)
    sparkle("S1", 0.85, 0.85, 0.26, 0)
    sparkle("S2", -0.95, -0.35, 0.13, 0)


def d06():   # crystals growing from a little rock
    reset(-18, 20)
    solid("Rock", rock_bm(), T(0, 0, -1.05) @ Matrix.Diagonal((1.3, 1.0, 0.8, 1.0)), "stone", top=None, grad=0.0)
    solid("Main", crystal_bm(0.5, 2.3, 0.68, twist=math.radians(42)), T(0.0, 0.05, -0.95) @ R(4, 'Y'), "violet")
    solid("Left", crystal_bm(0.36, 1.45, 0.62, twist=math.radians(20)), T(-0.6, -0.2, -0.95) @ R(-30, 'Y') @ R(8, 'X'), "violet")
    solid("Right", crystal_bm(0.32, 1.2, 0.6, twist=math.radians(10)), T(0.62, -0.25, -0.98) @ R(36, 'Y') @ R(10, 'X'), "violet")
    sparkle("S1", 0.80, 0.75, 0.24, 0)


def d07():   # classic diamond (rhombus) side view
    reset(-12, 22)
    solid("Diamond", bipyramid_bm(8, 1.25, 0.62, 1.3, twist=math.radians(22.5), table=1, table_r=0.6),
          Matrix(), "teal", top="up", grad=0.0)
    sparkle("S1", 0.85, 0.80, 0.28, 0)
    sparkle("S2", -0.90, -0.10, 0.14, 0)


def d08():   # hexagonal prism lying at an angle (double-terminated)
    reset(-10, 26)
    bm = crystal_bm(0.55, 2.4, 0.7, sides=6, taper=1.0, twist=math.radians(30), point_bottom=0.75)
    solid("Prism", bm, R(-22, 'Z') @ R(58, 'Y') @ T(0, 0, -0.8), "bluepurple")
    sparkle("S1", 0.30, 0.95, 0.24, 0)
    sparkle("S2", -0.30, -0.95, 0.14, 0)


def d09():   # fan of 5 small shards
    reset(-10, 16)
    angles = [-56, -28, 0, 28, 56]
    heights = [1.35, 1.8, 2.2, 1.8, 1.35]
    pals = ["violet", "magenta", "magenta", "magenta", "violet"]
    for i, (a, h, p) in enumerate(zip(angles, heights, pals)):
        y = -0.05 * abs(i - 2) - 0.1 * (i - 2 == 0)
        solid(f"Shard{i}", crystal_bm(0.26, h, 0.70, sides=6, twist=math.radians(15 + 10 * i)),
              T(0, -0.1 * (2 - abs(i - 2)), -1.0) @ R(a, 'Y'), p)
    sparkle("S1", 0.0, 1.0, 0.22, 0)


def d10():   # gem with a glowing core and halo burst behind it
    reset(-12, 14)
    solid("Gem", bipyramid_bm(6, 0.85, 1.25, 1.25, twist=math.radians(0)), Matrix(), "violet", top=None, grad=0.0)
    STATE["halo"] = True
    STATE["core"] = True


DESIGNS = [d01, d02, d03, d04, d05, d06, d07, d08, d09, d10]
INFO = {
    1: "3-crystal cluster (the first icon), magenta/violet with cyan tips",
    2: "round brilliant-cut gem seen from above, blue-purple with a bright table",
    3: "one tall pointed shard, violet with pink tip",
    4: "faceted round orb gem, pink-white",
    5: "heart-shaped faceted gem, magenta",
    6: "violet crystals growing out of a small grey-blue rock",
    7: "classic diamond (rhombus gem) side view, teal",
    8: "double-pointed hex crystal lying at an angle, blue-purple",
    9: "fan of 5 shards, magenta centre, violet ends",
    10: "violet gem with a white glowing core in front of a pink light burst",
}


# ------------------------------------------------------------ render
def screen_bounds(objs):
    r, u = STATE["right"], STATE["up"]
    xs, ys = [], []
    for ob in objs:
        mw = ob.matrix_world
        for v in ob.data.vertices:
            w = mw @ v.co
            xs.append(w.dot(r))
            ys.append(w.dot(u))
    return min(xs), max(xs), min(ys), max(ys)


def finish_and_render(path):
    solids = list(STATE["solids"])
    x0, x1, y0, y1 = screen_bounds(solids)
    ext = max(x1 - x0, y1 - y0)
    thick = 0.030 * ext
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r, u, f = STATE["right"], STATE["up"], STATE["fwd"]
    # world point in front of everything at screen (sx, sy)
    def at(sx, sy, toward=4.0):
        return r * sx + u * sy - f * toward

    hulls = [hull(o, thick) for o in solids]
    if STATE.get("halo"):
        hc = at(cx, cy, -3.0)
        flat_poly("Burst", star_pts(ext * 0.68, ext * 0.40, points=8, rot=math.pi / 8), hc, 0.0, (255, 170, 238), outline=thick)
        flat_poly("Glow", circle_pts(ext * 0.42, 36), hc, 0.05, (255, 222, 250))
    if STATE.get("core"):
        cc = at(cx - ext * 0.03, cy + ext * 0.02, 4.0)
        flat_poly("Core", star_pts(ext * 0.26, ext * 0.075, points=4), cc, 0.0, WHITE, outline=thick * 0.8)
        flat_poly("CoreDot", circle_pts(ext * 0.075, 16), cc, 0.02, (255, 240, 255))
    for (name, sx, sy, size, col) in STATE.get("sparkles", []):
        p = at(cx + sx * (x1 - x0) / 2 * 1.0, cy + sy * (y1 - y0) / 2 * 1.0, 6.0)
        s = size * ext / 2.4
        flat_poly(name, star_pts(s, s * 0.27), p, 0.0, col, outline=thick * 0.9)

    x0, x1, y0, y1 = screen_bounds(solids + hulls + STATE["flats"])
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = max(x1 - x0, y1 - y0) * 1.14
    cam_data.clip_end = 200
    cam = bpy.data.objects.new("Cam", cam_data)
    sc.collection.objects.link(cam)
    centre = r * ((x0 + x1) / 2) + u * ((y0 + y1) / 2) - f * 40
    cam.matrix_world = Matrix.Translation(centre) @ (STATE["rot"] @ Matrix.Rotation(math.radians(90), 3, 'X')).to_4x4()
    sc.camera = cam

    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'VERTEX'
    sh.show_backface_culling = True
    sh.show_object_outline = False
    sh.show_cavity = False
    sh.show_specular_highlight = False
    sc.display.render_aa = '32'
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_number(n, path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    cu = bpy.data.curves.new("Num", 'FONT')
    cu.body = str(n)
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(FONT)
    ob = bpy.data.objects.new("Num", cu)
    sc.collection.objects.link(ob)
    cd = bpy.data.cameras.new("Cam")
    cd.type = 'ORTHO'
    cd.ortho_scale = 2.4
    cam = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 5)
    sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'SINGLE'
    sh.single_color = (0.007, 0.021, 0.155)   # linear of NAVY
    sc.display.render_aa = '16'
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = 240
    sc.render.resolution_y = 120
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return np.flipud(px)   # top row first


def box_down(px, f):
    h, w, _ = px.shape
    pre = np.concatenate([px[..., :3] * px[..., 3:4], px[..., 3:4]], axis=2)
    s = pre.reshape(h // f, f, w // f, f, 4).mean(axis=(1, 3))
    a = s[..., 3:4]
    return np.concatenate([np.where(a > 1e-5, s[..., :3] / np.maximum(a, 1e-5), 0), a], axis=2)


def over(dst, src, x, y):
    h, w, _ = src.shape
    a = src[..., 3:4]
    dst[y:y + h, x:x + w, :3] = src[..., :3] * a + dst[y:y + h, x:x + w, :3] * (1 - a)


def contact_sheet():
    tile, label, gap = 256, 96, 24
    cols, rows = 5, 2
    W = cols * tile + (cols + 1) * gap
    H = rows * (tile + label) + (rows + 1) * gap
    sheet = np.zeros((H, W, 4), dtype=np.float32)
    sheet[..., :3] = np.array([120, 190, 240]) / 255
    sheet[..., 3] = 1
    tmp = os.path.join(OUT, "_num.png")
    for i in range(10):
        n = i + 1
        cx = gap + (i % cols) * (tile + gap)
        cy = gap + (i // cols) * (tile + label + gap)
        p = os.path.join(OUT, f"Crystal_{n:02d}.png")
        if os.path.exists(p):
            over(sheet, box_down(load_rgba(p), 2), cx, cy)
        render_number(n, tmp)
        num = load_rgba(tmp)
        over(sheet, num[12:108, :, :], cx + (tile - 240) // 2, cy + tile)
    os.remove(tmp)
    img = bpy.data.images.new("sheet", W, H, alpha=True)
    img.pixels = np.flipud(sheet).ravel().tolist()
    img.filepath_raw = os.path.join(PREV, "crystal_options_sheet.png")
    img.file_format = 'PNG'
    img.save()


for idx, fn in enumerate(DESIGNS, start=1):
    if ONLY and idx not in ONLY:
        continue
    STATE.clear()
    fn()
    finish_and_render(os.path.join(OUT, f"Crystal_{idx:02d}.png"))
contact_sheet()
print("CRYSTAL OPTIONS DONE")
