# Batch D2: lollipop trees (docs/art_plan.md, BATCH D). Three shapes in one FBX, one shared
# 512 texture set, tinted heads.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_island_lollipop.py
#
# Models (each stands on the origin, front on +Y, about 15 tall, head 8 across):
#   Lollipop_Swirl  thick puffy disc with a raised two-arm swirl (normal map + brighter line)
#   Lollipop_Ball   round ball lollipop with a toy-gold bow tied at the neck
#   Lollipop_Heart  puffy heart-shaped lollipop
# Each model = <Name>_Tint (neutral head, recoloured in game), <Name>_Body (cream stick, pink
# frosting dollop at the foot, gold bow; fixed colours) and <Name>_Shine (flat white highlight).
#
# Texture atlas Hub_Lollipop_* (512): heads in the top half, bodies in [0.5..1] x [0.25..0.5];
# the bottom quarter (v < 0.25) is kept free for the grass dressing (hub_island_dressing.py).
#
# Outputs (art/hub_island/): Hub_Lollipop.fbx, Hub_Lollipop_color/_normal/_roughness.png,
#   Hub_Lollipop.blend, Hub_Lollipop.bounds.json
# Previews (art/previews/): hub_island_lollipop_beauty/_turn/_flat/_thumb/_colours.png

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import hub_island_common as C  # noqa: E402

NAME = "Hub_Lollipop"
TEX = 512
HEAD_Z = 11.0
STICK_R = 0.6

RECTS = {
    "Lollipop_Swirl_Tint": (0.0, 0.5, 0.5, 1.0),
    "Lollipop_Ball_Tint": (0.5, 0.5, 1.0, 1.0),
    "Lollipop_Heart_Tint": (0.0, 0.25, 0.5, 0.5),
    "Lollipop_Swirl_Body": (0.5, 0.25, 0.667, 0.5),
    "Lollipop_Heart_Body": (0.667, 0.25, 0.833, 0.5),
    "Lollipop_Ball_Body": (0.833, 0.25, 1.0, 0.5),
}

UPRIGHT = Matrix.Rotation(math.radians(90), 4, "X")  # local +Z (face) -> Blender -Y, local +Y -> +Z


def placed(b, fn, matrix):
    before = set(b.bm.verts)
    fn()
    new = [v for v in b.bm.verts if v not in before]
    bmesh.ops.transform(b.bm, matrix=matrix, verts=new)


# pillow profile (scale toward the middle, height): poles front and back, puffy rounded edge
PILLOW = [(0.0, 1.0), (0.6, 0.97), (0.88, 0.74), (1.0, 0.0), (0.88, -0.74), (0.6, -0.97), (0.0, -1.0)]
SPHERE5 = [(0.0, 1.0), (0.707, 0.707), (1.0, 0.0), (0.707, -0.707), (0.0, -1.0)]


def sphere_profile(n):
    return [(math.sin(math.pi * i / (n - 1)), math.cos(math.pi * i / (n - 1))) for i in range(n)]


def stick_and_dollop(b, top):
    b.lathe("Stick", [(STICK_R, top), (STICK_R, 1.0)], 10, (0, 0, 1, 1))
    # piped frosting dollop (two soft tiers), bottom just under the ground, top tucked into the stick
    dollop = [(0.0, 2.02), (0.5, 2.0), (1.0, 1.62), (1.45, 1.36), (1.75, 0.98), (1.98, 0.76), (2.35, 0.35), (2.25, -0.15)]
    b.lathe("Dollop", dollop[1:], 10, (0, 0, 1, 1))


def pillow(b, mat, outline, thick, segs_note=None):
    """Puffy flat shape from a closed outline [(x, y)] (counter-clockwise, star-shaped about
    (0, 0)), built in the local XY plane with thickness along local Z."""
    rows, uvs = [], []
    for s, h in PILLOW:
        if s == 0.0:
            rows.append([Vector((0, 0, h * thick))])
            uvs.append([(0.5, 0.5)])
            continue
        rows.append([Vector((x * s, y * s, h * thick)) for x, y in outline])
        uvs.append([(0.5, 0.5)] * len(outline))
    b.grid(rows, uvs, mat, closed=True)


def pillow_z(s_frac):
    """Height (fraction of the thickness) of the PILLOW surface at scale fraction s."""
    pts = PILLOW[:4]
    for (s0, h0), (s1, h1) in zip(pts, pts[1:]):
        if s0 <= s_frac <= s1:
            return h0 + (h1 - h0) * (s_frac - s0) / (s1 - s0)
    return 0.0


def shine_arc(b, center, r0, r1, a0, a1, zfn, steps=4):
    """Crescent highlight in the local XY plane, lying 0.05 above the surface z = zfn(x, y)
    and facing +Z."""
    rows = []
    for r in (r0, r1):  # inner -> outer with columns counter-clockwise: faces point +Z
        row = []
        for i in range(steps + 1):
            t = i / steps
            a = math.radians(a0 + (a1 - a0) * t)
            taper = math.sin(math.pi * t) ** 0.5  # pointed ends
            rr = (r0 + r1) / 2 + (r - (r0 + r1) / 2) * max(taper, 0.15)
            x, y = center[0] + rr * math.cos(a), center[1] + rr * math.sin(a)
            row.append(Vector((x, y, zfn(x, y) + 0.05)))
        rows.append(row)
    b.grid(rows, [[(0, 0)] * (steps + 1)] * 2, "Shine")


def outline_radius(outline, ang):
    """Distance from (0, 0) to a star-shaped outline in direction ang."""
    best = None
    n = len(outline)
    d = Vector((math.cos(ang), math.sin(ang)))
    for i in range(n):
        p, q = Vector(outline[i]), Vector(outline[(i + 1) % n])
        e = q - p
        den = d.x * e.y - d.y * e.x
        if abs(den) < 1e-9:
            continue
        t = (p.x * e.y - p.y * e.x) / den
        u = (p.x * d.y - p.y * d.x) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = t if best is None else min(best, t)
    return best


def mirrored(b, fn):
    """Build fn() in local space twice: front (+Z) and back (mirrored to -Z)."""
    fn()
    before = set(b.bm.verts)
    fn()
    new = [v for v in b.bm.verts if v not in before]
    bmesh.ops.transform(b.bm, matrix=Matrix.Rotation(math.pi, 4, "Y"), verts=new)


def heart_outline(n=32, scale=0.25):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = -16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * scale, (y + 2.5) * scale))
    # make it counter-clockwise about +Z
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    return pts if area > 0 else pts[::-1]


# ------------------------------------------------------------------ models
def build_swirl():
    tint, body, shine = C.Builder("Lollipop_Swirl_Tint"), C.Builder("Lollipop_Swirl_Body"), C.Builder("Lollipop_Swirl_Shine")
    head = Matrix.Translation((0, 0, HEAD_Z)) @ UPRIGHT
    disc = [(r * 4.0, z * 1.0) for r, z in PILLOW]
    placed(tint, lambda: tint.lathe("SwirlHead", disc, 32, (0, 0, 1, 1)), head)
    stick_and_dollop(body, 8.6)
    placed(shine, lambda: mirrored(shine, lambda: shine_arc(shine, (0, 0), 2.2, 2.85, 105, 165,
        lambda x, y: pillow_z(math.hypot(x, y) / 4.0) * 1.0)), head)
    return tint, body, shine


def cube_sphere(b, mat, center, R, N=5):
    """Sphere from a cube with each face split N x N (no pinched poles): rounder than a
    UV sphere for the same triangles (the gumball's method)."""
    c = Vector(center)
    axes = [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]
    grid = {}
    for na, ua, va in axes[::2] + [(0, 1, 2)][:0]:
        pass
    faces = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
    for na, ua, va in faces:
        for sgn in (1, -1):
            pts = {}
            for i in range(N + 1):
                for j in range(N + 1):
                    p = [0.0, 0.0, 0.0]
                    p[na] = sgn
                    p[ua] = math.tan((-1 + 2 * i / N) * math.pi / 4)
                    p[va] = math.tan((-1 + 2 * j / N) * math.pi / 4)
                    key = tuple(round(x * 1e5) for x in Vector(p).normalized())
                    if key not in grid:
                        grid[key] = b.bm.verts.new(c + Vector(p).normalized() * R)
                    pts[i, j] = grid[key]
            for i in range(N):
                for j in range(N):
                    vs = [pts[i, j], pts[i + 1, j], pts[i + 1, j + 1], pts[i, j + 1]]
                    f = b.face(vs, [(0, 0)] * 4, mat)
                    f.normal_update()
                    if f.normal.dot(f.calc_center_median() - c) < 0:
                        f.normal_flip()


def build_ball():
    tint, body, shine = C.Builder("Lollipop_Ball_Tint"), C.Builder("Lollipop_Ball_Body"), C.Builder("Lollipop_Ball_Shine")
    R, cz = 3.85, HEAD_Z + 0.2
    cube_sphere(tint, "BallHead", (0, 0, cz), R, 5)
    stick_and_dollop(body, cz - R + 1.2)
    # toy-gold bow just under the ball: knot, two fat loops, two tails
    ell = [(r, z) for r, z in SPHERE5]

    def blob(size, at, rx=0.0, ry=0.0, rz=0.0, segs=8):
        m = Matrix.Translation(at) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X") \
            @ Matrix.Diagonal(Vector((size[0], size[1], size[2], 1)))
        placed(body, lambda: body.lathe("Bow", ell, segs, (0, 0, 1, 1)), m)

    kz = cz - R + 0.2
    blob((0.95, 0.95, 0.7), (0, 0.15, kz))
    for s in (-1, 1):
        blob((1.45, 0.75, 0.62), (s * 1.75, 0.35, kz + 0.3), ry=s * math.radians(-24))
        blob((0.42, 0.3, 1.15), (s * 0.95, 0.45, kz - 1.35), ry=s * math.radians(22), segs=6)
    # crescent shine, upper left, on the front and the back of the ball
    frame = Matrix.Translation((0, 0, cz)) @ Matrix.Rotation(math.radians(-90), 4, "X") @ Matrix.Rotation(math.pi, 4, "Z")
    on_ball = lambda x, y: math.sqrt(max(R * R - x * x - y * y, 0.0))  # noqa: E731
    placed(shine, lambda: shine_arc(shine, (0, 0), 1.75, 2.45, 105, 165, on_ball), frame)
    placed(shine, lambda: shine_arc(shine, (0, 0), 1.75, 2.45, 105, 165, on_ball),
           Matrix.Translation((0, 0, cz)) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation((0, 0, -cz)) @ frame)
    return tint, body, shine


def build_heart():
    tint, body, shine = C.Builder("Lollipop_Heart_Tint"), C.Builder("Lollipop_Heart_Body"), C.Builder("Lollipop_Heart_Shine")
    outline = heart_outline()
    low = min(y for _, y in outline)
    head = Matrix.Translation((0, 0, 7.0 - low)) @ UPRIGHT  # heart tip at height 7
    th = 0.95
    placed(tint, lambda: pillow(tint, "HeartHead", outline, th), head)
    stick_and_dollop(body, 8.0)
    zf = lambda x, y: pillow_z(math.hypot(x, y) / outline_radius(outline, math.atan2(y, x))) * th  # noqa: E731
    placed(shine, lambda: mirrored(shine, lambda: shine_arc(shine, (-1.9, 1.85), 0.55, 1.0, 100, 175, zf)), head)
    return tint, body, shine


# ------------------------------------------------------------------ bake materials
def neutral(nt, v):
    return nt.combine(v, v, v)


def mat_swirl():
    def build(nt):
        p = nt.xyz(nt.obj())
        x, zz = p[0], nt.math("SUBTRACT", p[2], HEAD_Z)
        theta = nt.math("ARCTAN2", zz, x)
        rho = nt.math("SQRT", nt.math("ADD", nt.math("MULTIPLY", x, x), nt.math("MULTIPLY", zz, zz)))
        phase = nt.math("ADD", nt.math("MULTIPLY", theta, 2.0), nt.math("MULTIPLY", rho, 2 * math.pi / 2.3))
        w = nt.math("ADD", 0.5, nt.math("MULTIPLY", nt.math("SINE", phase), 0.5))
        band = nt.mrange(w, 0.42, 0.62, 0.0, 1.0, smooth=True)
        edge = nt.mrange(rho, 2.8, 4.0, 1.0, 0.9)
        v = nt.math("MULTIPLY", nt.math("ADD", 0.66, nt.math("MULTIPLY", band, 0.31)), edge)  # ~214 / 252 (sRGB)
        return dict(albedo=neutral(nt, v), rough=nt.math("ADD", 0.16, nt.math("MULTIPLY", band, 0.06)),
                    height=band, bump=(0.55, 0.12))
    return C.bake_material("SwirlHead", build)


def mat_ball():
    def build(nt):
        p = nt.xyz(nt.obj())
        z = p[2]
        ang = nt.math("ARCTAN2", p[1], p[0])
        phase = nt.math("ADD", nt.math("MULTIPLY", ang, 3.0), nt.math("MULTIPLY", z, 1.25))
        band = nt.mrange(nt.math("SINE", phase), -0.15, 0.25, 0.0, 1.0, smooth=True)
        shade = nt.mrange(z, HEAD_Z - 3.8, HEAD_Z + 3.8, 0.9, 1.0)
        v = nt.math("MULTIPLY", nt.math("ADD", 0.74, nt.math("MULTIPLY", band, 0.23)), shade)
        return dict(albedo=neutral(nt, v), rough=0.17, height=band, bump=(0.35, 0.1))
    return C.bake_material("BallHead", build)


def mat_heart():
    def build(nt):
        p = nt.xyz(nt.obj())
        geo = nt.n.new("ShaderNodeNewGeometry")
        ny = nt.math("ABSOLUTE", nt.xyz(geo.outputs["Normal"])[1])
        v = nt.mrange(ny, 0.0, 1.0, 0.86, 0.96)  # faces bright, rolled edge a touch darker
        return dict(albedo=neutral(nt, v), rough=0.17, height=None)
    return C.bake_material("HeartHead", build)


def mat_flat(name, hexcol, rough, ao_dist=1.2, dark=(0.78, 0.66, 0.86)):
    def build(nt):
        ao = nt.mrange(nt.ao(ao_dist, 16), 0.3, 1.0, 0.0, 1.0)
        z = nt.xyz(nt.obj())[2]
        base = nt.rgb(hexcol)
        shadow = nt.mix(1.0, base, dark + (1,), "MULTIPLY")
        col = nt.mix(nt.math("MULTIPLY", ao, nt.mrange(z, -0.2, 1.2, 0.75, 1.0)), shadow, base)
        return dict(albedo=col, rough=rough, height=None)
    return C.bake_material(name, build)


# ------------------------------------------------------------------ main
def main():
    C.reset()
    mats = {
        "SwirlHead": mat_swirl(), "BallHead": mat_ball(), "HeartHead": mat_heart(),
        "Stick": mat_flat("Stick", C.PAL["cream"], 0.25), "Dollop": mat_flat("Dollop", C.PAL["pink"], 0.45),
        "Bow": mat_flat("Bow", C.PAL["gold"], 0.25, 0.8),
    }
    shine_mat = C.flat_material("ShineWhite", C.PAL["cream"], 0.3, emit=0.6)
    models = {}
    for key, fn in (("Swirl", build_swirl), ("Ball", build_ball), ("Heart", build_heart)):
        parts = []
        for b in fn():
            ob = b.to_object()
            if b.name.endswith("_Shine"):
                ob.data.materials.append(shine_mat)
            else:
                for m in b.mats:
                    ob.data.materials.append(mats[m])
            parts.append(ob)
        models[key] = parts

    # UVs: each textured mesh gets its own rectangle of the atlas
    for parts in models.values():
        for ob in parts:
            if ob.name in RECTS:
                C.smart_uv(ob, RECTS[ob.name], angle=55, margin=0.03)

    # bake with the three models apart (object coordinates don't move, AO stays separate)
    for k, parts in enumerate(models.values()):
        for ob in parts:
            ob.location.x = (k - 1) * 40
    baked = [ob for parts in models.values() for ob in parts if ob.name in RECTS]
    shines = [ob for parts in models.values() for ob in parts if ob.name.endswith("_Shine")]
    for ob in shines:
        ob.hide_render = True
    # keep the dressing's quarter of an existing atlas (if the dressing was baked already)
    keep = os.path.exists(os.path.join(C.OUT, NAME + "_color.png"))
    C.bake_set(baked, NAME, TEX, clear=not keep)
    for ob in shines:
        ob.hide_render = False
    for parts in models.values():
        for ob in parts:
            ob.location.x = 0

    maps = C.load_maps(NAME)
    final = C.textured_material("Lolly", maps)
    flat = C.textured_material("LollyFlat", maps, flat=True)
    tinted = {}
    for ob in baked:
        C.set_material(ob, final)

    allobs = [ob for parts in models.values() for ob in parts]
    total = C.report_tris(allobs, NAME)
    for key, parts in models.items():
        print(f"[{NAME}] Lollipop_{key}: {sum(C.tri_count(o) for o in parts)} tris")
    C.export(allobs, NAME + ".fbx")
    bounds = {
        "_notes": [
            "Three lollipop models; each stands on the origin (bottom centre at 0,0,0), front +Y, ~15 tall.",
            "In game, each model = its _Tint, _Body and _Shine MeshParts; scale all three together (0.8 - 1.4).",
            "_Tint: SurfaceAppearance Hub_Lollipop_* with Color = a gumball colour (also MeshPart.Color).",
            "_Body: same SurfaceAppearance, no tint (cream stick, pink frosting dollop, gold bow).",
            "_Shine: flat white SmoothPlastic (no texture), no shadow; optional Transparency 0.15.",
            "Replaces LollyStick, Lolly, LollySwirl, LollyMiddle in Hub.lua lollipop(); base = the grass point.",
        ],
        "texture": {"color": NAME + "_color.png", "normal": NAME + "_normal.png", "roughness": NAME + "_roughness.png", "size": TEX},
        "totalTris": total,
    }
    for ob in allobs:
        d = C.roblox_box(ob)
        if ob.name.endswith("_Tint"):
            d.update(color="tint (gumball colours)", material="SmoothPlastic + SurfaceAppearance (tinted)", castShadow=True)
        elif ob.name.endswith("_Body"):
            d.update(color=C.hex_rgb(C.PAL["cream"]), material="SmoothPlastic + SurfaceAppearance", castShadow=True)
        else:
            d.update(color=C.hex_rgb(C.PAL["cream"]), material="SmoothPlastic (flat, no texture)", castShadow=False)
        d["tris"] = C.tri_count(ob)
        bounds[ob.name] = d
    C.write_bounds(NAME + ".bounds.json", bounds)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))

    previews(models, maps, final, flat)


def tint_set(parts, mat):
    for ob in parts:
        if ob.name.endswith("_Tint"):
            C.set_material(ob, mat)


def place(parts, x, y=0.0, rz=0.0, s=1.0):
    for ob in parts:
        ob.location = (x, y, 0)
        ob.rotation_euler = (0, 0, rz)
        ob.scale = (s, s, s)


def previews(models, maps, final, flat):
    tints = {h: C.textured_material("Lolly_" + n, maps, tint=h) for n, h in C.GUMBALLS}
    flats = {h: C.textured_material("LollyF_" + n, maps, tint=h, flat=True) for n, h in C.GUMBALLS}
    pick = {"Swirl": C.GUMBALLS[0][1], "Ball": C.GUMBALLS[1][1], "Heart": C.GUMBALLS[4][1]}
    for i, (key, parts) in enumerate(models.items()):
        place(parts, (i - 1) * 10.5)
        tint_set(parts, tints[pick[key]])
    C.player_block((16.5, 0, 0))
    cam = C.studio((0, 0, 7.5), 14, floor_z=0.0)
    beauty = os.path.join(C.PREVIEWS, "hub_island_lollipop_beauty.png")
    C.look(cam, (24, 44, 15), (1.5, 0, 7.2), 45)
    C.render(beauty, 1280, 960)
    C.thumb(beauty, os.path.join(C.PREVIEWS, "hub_island_lollipop_thumb.png"))
    for key, parts in models.items():
        tint_set(parts, flats[pick[key]])
        for ob in parts:
            if ob.name.endswith("_Body"):
                C.set_material(ob, flat)
    C.render(os.path.join(C.PREVIEWS, "hub_island_lollipop_flat.png"), 1280, 960)
    for key, parts in models.items():
        tint_set(parts, tints[pick[key]])
        for ob in parts:
            if ob.name.endswith("_Body"):
                C.set_material(ob, final)

    views = []
    for k, (dx, dy) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        p = os.path.join(C.TMP, f"lolly_turn_{k}.png")
        for i, parts in enumerate(models.values()):
            for ob in parts:
                ob.location = ((i - 1) * 10.5 * abs(dy) , (i - 1) * 10.5 * -dx, 0)
        C.look(cam, (dx * 58, dy * 58, 10), (0, 0, 7.5), 50)
        C.render(p, 640, 480, samples=40)
        views.append(p)
    C.compose(views, os.path.join(C.PREVIEWS, "hub_island_lollipop_turn.png"))

    # colours: 8 gumball colours, shapes mixed, on a grass-green floor
    keys = list(models.keys())
    copies = []
    for n, (cname, hexc) in enumerate(C.GUMBALLS):
        key = keys[n % 3]
        for ob in models[key]:
            c = ob.copy()
            c.data = ob.data.copy()
            bpy.context.scene.collection.objects.link(c)
            if ob.name.endswith("_Tint"):
                C.set_material(c, tints[hexc])
            c.location = ((n % 4 - 1.5) * 10.5, (n // 4) * -11.0, 0)
            c.rotation_euler = (0, 0, 0)
            copies.append(c)
    for parts in models.values():
        for ob in parts:
            ob.hide_render = True
    C.look(cam, (0, 52, 24), (0, -5.5, 6.5), 42)
    C.render(os.path.join(C.PREVIEWS, "hub_island_lollipop_colours.png"), 1280, 960)


main()
