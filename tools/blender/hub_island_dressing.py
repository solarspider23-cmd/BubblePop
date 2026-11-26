# Batch D4 (stretch goal): grass dressing for the empty green ring (docs/art_plan.md, BATCH D).
# Shares the lollipop texture set: bakes into the bottom quarter (v < 0.25) of
# Hub_Lollipop_color/_normal/_roughness.png, which hub_island_lollipop.py leaves alone.
# Run hub_island_lollipop.py first.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_island_dressing.py
#
# Models (each stands on the origin, front +Y):
#   Dressing_Gumdrop  sugar-coated gumdrop bush, ~4 across, 3 tall          (_Tint)
#   Dressing_Sweet    wrapped sweet lying on the grass, ~5 long, striped     (_Tint)
#   Dressing_Cupcake  cupcake ~5 tall: tinted frosting swirl (_Tint), pleated pink-and-cream cup
#                     and a red cherry (_Body)
#
# Outputs (art/hub_island/): Hub_Dressing.fbx, Hub_Dressing.blend, Hub_Dressing.bounds.json
#   (+ the shared Hub_Lollipop_*.png updated in its bottom quarter)
# Previews (art/previews/): hub_island_dressing_beauty/_turn/_flat/_thumb/_colours.png

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(__file__))
import hub_island_common as C  # noqa: E402

NAME = "Hub_Dressing"
ATLAS = "Hub_Lollipop"
TEX = 512
RECTS = {
    "Dressing_Gumdrop_Tint": (0.0, 0.0, 0.25, 0.245),
    "Dressing_Sweet_Tint": (0.25, 0.0, 0.5, 0.245),
    "Dressing_Cupcake_Tint": (0.5, 0.0, 0.75, 0.245),
    "Dressing_Cupcake_Body": (0.75, 0.0, 1.0, 0.245),
}
SPHERE5 = [(0.0, 1.0), (0.707, 0.707), (1.0, 0.0), (0.707, -0.707), (0.0, -1.0)]


def placed(b, fn, matrix):
    before = set(b.bm.verts)
    fn()
    new = [v for v in b.bm.verts if v not in before]
    bmesh.ops.transform(b.bm, matrix=matrix, verts=new)
    return new


def build_gumdrop():
    t = C.Builder("Dressing_Gumdrop_Tint")
    prof = [(0.0, 3.0), (1.05, 2.93), (1.65, 2.55), (1.98, 1.65), (2.1, 0.6), (2.02, 0.1), (1.8, -0.15)]
    t.lathe("Sugar", prof, 24, (0, 0, 1, 1))
    return [t]


def build_sweet():
    t = C.Builder("Dressing_Sweet_Tint")
    # profile along the sweet's length (built round Z, then laid along X)
    prof = [(0.0, 2.6), (0.95, 2.55), (1.05, 2.3), (0.45, 1.75), (0.38, 1.55), (0.8, 1.28), (1.05, 0.7),
            (1.1, 0.0), (1.05, -0.7), (0.8, -1.28), (0.38, -1.55), (0.45, -1.75), (1.05, -2.3), (0.95, -2.55), (0.0, -2.6)]
    new = placed(t, lambda: t.lathe("Sweet", prof, 14, (0, 0, 1, 1)), Matrix.Identity(4))
    for v in new:  # pleated, frilly wrapper ends
        if abs(v.co.z) > 1.9:
            a = math.atan2(v.co.y, v.co.x)
            k = 1 + 0.17 * math.cos(7 * a)
            v.co.x *= k
            v.co.y *= k
    lay = Matrix.Translation((0, 0, 0.92)) @ Matrix.Rotation(math.radians(90), 4, "Y") @ Matrix.Diagonal(Vector((0.92, 1.0, 1.0, 1)))
    bmesh.ops.transform(t.bm, matrix=lay, verts=new)
    return [t]


def build_cupcake():
    t, b = C.Builder("Dressing_Cupcake_Tint"), C.Builder("Dressing_Cupcake_Body")
    # pleated cup (12 pleats), slightly flared, open top hidden under the frosting
    cup = [(1.5, 2.25), (1.62, 2.2), (1.45, 0.25), (1.38, -0.05)]  # bottom sits on the grass (no hidden base)
    new = placed(b, lambda: b.lathe("Cup", cup, 20, (0, 0, 1, 1)), Matrix.Identity(4))
    for v in new:
        r = math.hypot(v.co.x, v.co.y)
        if r > 0.5:
            a = math.atan2(v.co.y, v.co.x)
            k = 1 + 0.05 * math.cos(10 * a)
            v.co.x *= k
            v.co.y *= k
    # frosting swirl: three soft piped tiers ending in a peak
    fr = [(0.0, 5.05), (0.75, 4.55), (0.62, 4.3), (1.25, 3.95), (1.05, 3.6), (1.8, 3.15),
          (1.95, 2.6), (1.75, 2.1), (1.35, 1.95)]
    t.lathe("Frosting", fr, 14, (0, 0, 1, 1))
    # cherry on top, nestled into the peak
    cm = Matrix.Translation((0.15, 0.1, 5.25)) @ Matrix.Diagonal(Vector((0.6, 0.6, 0.55, 1)))
    placed(b, lambda: b.lathe("Cherry", SPHERE5, 8, (0, 0, 1, 1)), cm)
    return [t, b]


# ------------------------------------------------------------------ bake materials
def neutral(nt, v):
    return nt.combine(v, v, v)


def mat_sugar():
    def build(nt):
        vor = nt.voronoi(nt.obj(), 2.6, "F1")
        grain = nt.mrange(vor.outputs["Distance"], 0.0, 0.5, 1.0, 0.0)
        ao = nt.mrange(nt.ao(1.0, 16), 0.3, 1.0, 0.85, 1.0)
        z = nt.xyz(nt.obj())[2]
        v = nt.math("MULTIPLY", nt.math("MULTIPLY", ao, nt.mrange(z, 0.0, 2.8, 0.86, 0.97)), nt.math("ADD", 0.97, nt.math("MULTIPLY", grain, 0.04)))
        return dict(albedo=neutral(nt, v), rough=nt.math("ADD", 0.5, nt.math("MULTIPLY", grain, -0.12)), height=grain, bump=(0.3, 0.06))
    return C.bake_material("Sugar", build)


def mat_sweet():
    def build(nt):
        p = nt.xyz(nt.obj())
        ang = nt.math("ARCTAN2", nt.math("SUBTRACT", p[2], 0.92), p[1])
        band = nt.mrange(nt.math("SINE", nt.math("ADD", nt.math("MULTIPLY", ang, 3.0), nt.math("MULTIPLY", p[0], 2.2))), -0.2, 0.25, 0.0, 1.0, smooth=True)
        ao = nt.mrange(nt.ao(0.8, 16), 0.3, 1.0, 0.8, 1.0)
        v = nt.math("MULTIPLY", nt.math("ADD", 0.6, nt.math("MULTIPLY", band, 0.38)), ao)
        return dict(albedo=neutral(nt, v), rough=0.16, height=band, bump=(0.3, 0.08))
    return C.bake_material("Sweet", build)


def mat_frosting():
    def build(nt):
        ao = nt.mrange(nt.ao(0.9, 16), 0.3, 1.0, 0.78, 1.0)
        z = nt.xyz(nt.obj())[2]
        v = nt.math("MULTIPLY", ao, nt.mrange(z, 2.0, 5.0, 0.9, 0.97))
        return dict(albedo=neutral(nt, v), rough=0.42, height=None)
    return C.bake_material("Frosting", build)


def mat_cup():
    def build(nt):
        p = nt.xyz(nt.obj())
        ang = nt.math("ARCTAN2", p[1], p[0])
        stripe = nt.mrange(nt.math("SINE", nt.math("MULTIPLY", ang, 5.0)), -0.15, 0.15, 0.0, 1.0)
        col = nt.mix(stripe, nt.rgb(C.PAL["cream"]), nt.rgb(C.PAL["pink"]))
        ao = nt.mrange(nt.ao(1.0, 16), 0.3, 1.0, 0.7, 1.0)
        col = nt.mix(1.0, col, ao, "MULTIPLY")
        return dict(albedo=col, rough=0.35, height=None)
    return C.bake_material("Cup", build)


def mat_cherry():
    def build(nt):
        ao = nt.mrange(nt.ao(0.6, 16), 0.3, 1.0, 0.75, 1.0)
        return dict(albedo=nt.mix(1.0, nt.rgb(C.PAL["red"]), ao, "MULTIPLY"), rough=0.15, height=None)
    return C.bake_material("Cherry", build)


def main():
    C.reset()
    mats = {"Sugar": mat_sugar(), "Sweet": mat_sweet(), "Frosting": mat_frosting(), "Cup": mat_cup(), "Cherry": mat_cherry()}
    models = {}
    for key, fn in (("Gumdrop", build_gumdrop), ("Sweet", build_sweet), ("Cupcake", build_cupcake)):
        parts = []
        for b in fn():
            ob = b.to_object()
            for m in b.mats:
                ob.data.materials.append(mats[m])
            C.smart_uv(ob, RECTS[ob.name], angle=55, margin=0.03)
            parts.append(ob)
        models[key] = parts
    for k, parts in enumerate(models.values()):
        for ob in parts:
            ob.location.x = (k - 1) * 20
    allobs = [ob for parts in models.values() for ob in parts]
    if not os.path.exists(os.path.join(C.OUT, ATLAS + "_color.png")):
        raise SystemExit("run hub_island_lollipop.py first (the dressing shares its texture set)")
    C.bake_set(allobs, ATLAS, TEX, clear=False)
    for ob in allobs:
        ob.location.x = 0

    maps = C.load_maps(ATLAS)
    final = C.textured_material("Dress", maps)
    flat = C.textured_material("DressFlat", maps, flat=True)
    for ob in allobs:
        C.set_material(ob, final)
    total = C.report_tris(allobs, NAME)
    for key, parts in models.items():
        print(f"[{NAME}] Dressing_{key}: {sum(C.tri_count(o) for o in parts)} tris")
    C.export(allobs, NAME + ".fbx")
    bounds = {
        "_notes": [
            "Grass dressing (new, replaces nothing): scatter on the grass ring between the fence and the glass.",
            "Each model stands on the origin, front +Y. Shares the lollipop SurfaceAppearance (Hub_Lollipop_*.png).",
            "_Tint pieces: SurfaceAppearance Color = a gumball colour (also MeshPart.Color). _Body: no tint.",
        ],
        "texture": {"color": ATLAS + "_color.png", "normal": ATLAS + "_normal.png", "roughness": ATLAS + "_roughness.png", "size": TEX},
        "totalTris": total,
    }
    for ob in allobs:
        d = C.roblox_box(ob)
        tinted = ob.name.endswith("_Tint")
        d.update(tris=C.tri_count(ob), color="tint (gumball colours)" if tinted else C.hex_rgb(C.PAL["pink"]),
                 material="SmoothPlastic + SurfaceAppearance" + (" (tinted)" if tinted else ""), castShadow=True)
        bounds[ob.name] = d
    C.write_bounds(NAME + ".bounds.json", bounds)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))

    # ---------------------------------------------------------------- previews
    tints = {h: C.textured_material("D_" + n, maps, tint=h) for n, h in C.GUMBALLS}
    flats = {h: C.textured_material("DF_" + n, maps, tint=h, flat=True) for n, h in C.GUMBALLS}
    pick = {"Gumdrop": C.GUMBALLS[0][1], "Sweet": C.GUMBALLS[6][1], "Cupcake": C.GUMBALLS[4][1]}

    def show(matset, bodymat):
        for key, parts in models.items():
            for ob in parts:
                C.set_material(ob, matset[pick[key]] if ob.name.endswith("_Tint") else bodymat)

    for i, parts in enumerate(models.values()):
        for ob in parts:
            ob.location = ((i - 1) * 7.0, 0, 0)
    show(tints, final)
    C.player_block((11, 0, 0))
    cam = C.studio((0, 0, 2.5), 8, floor_z=0.0, floor_col=C.lin(C.PAL["grass"]))
    beauty = os.path.join(C.PREVIEWS, "hub_island_dressing_beauty.png")
    C.look(cam, (14, 26, 10), (1.0, 0, 2.2), 45)
    C.render(beauty, 1280, 960)
    C.thumb(beauty, os.path.join(C.PREVIEWS, "hub_island_dressing_thumb.png"))
    show(flats, flat)
    C.render(os.path.join(C.PREVIEWS, "hub_island_dressing_flat.png"), 1280, 960)
    show(tints, final)
    views = []
    for k, (dx, dy) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        for i, parts in enumerate(models.values()):
            for ob in parts:
                ob.location = ((i - 1) * 7.0 * abs(dy), (i - 1) * 7.0 * -dx, 0)
        p = os.path.join(C.TMP, f"dress_turn_{k}.png")
        C.look(cam, (dx * 34, dy * 34, 7), (0, 0, 2.2), 50)
        C.render(p, 640, 480, samples=40)
        views.append(p)
    C.compose(views, os.path.join(C.PREVIEWS, "hub_island_dressing_turn.png"))
    # colours: every model in all 8 gumball colours
    for ob in allobs:
        ob.hide_render = True
    for row, (key, parts) in enumerate(models.items()):
        for n, (cname, hexc) in enumerate(C.GUMBALLS):
            for ob in parts:
                c = ob.copy()
                c.data = ob.data.copy()
                bpy.context.scene.collection.objects.link(c)
                c.hide_render = False
                C.set_material(c, tints[hexc] if ob.name.endswith("_Tint") else final)
                c.location = ((n - 3.5) * 5.6, -row * 7.5, 0)
    bpy.data.objects["Player"].hide_render = True
    C.look(cam, (0, 40, 30), (0, -7.5, 1.5), 40)
    C.render(os.path.join(C.PREVIEWS, "hub_island_dressing_colours.png"), 1280, 960)


main()
