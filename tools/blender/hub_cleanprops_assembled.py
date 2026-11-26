# CLEAN POP PLAZA prop kit: the assembled overview picture. Loads the finished lobby models from
# art/hub_clean/*.blend and the prop kit from art/hub_clean_props/*.blend and lays them out as proposed:
# hall along the back edge behind the centrepiece, planters and lamps out to the back corners, lamps
# round the pads, benches + planter on one side, the leaderboard by the stage.
# Makes no models; writes art/previews/hub_cleanprops_assembled_beauty.png.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_assembled.py
#
# Scene axes (same as hub_clean_assembled.py): Blender +Y = towards the spawn (hub +Z), Blender X = -hub X;
# the centrepiece is at the origin (hub (0, 0, -45)), so hub (x, z) = scene (-x, z + 45).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_cleanprops_common as C  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

K, P = C.K, C.P
sc = K.reset()
STEP = 7.857
PLAZA_Y = 45.0
BASE = os.path.join(K.ROOT, "art", "hub_clean")


def load(blend, names, folder=BASE):
    with bpy.data.libraries.load(os.path.join(folder, blend)) as (src, dst):
        dst.objects = [n for n in names if n in src.objects]
    return {o.name.split(".")[0]: o for o in dst.objects}


def place(srcs, at, rot=0.0, mats=None):
    out = []
    for s in srcs:
        o = s.copy()
        if mats and s.name.split(".")[0] in mats:
            o.data = s.data.copy()
            K.set_mat(o, mats[s.name.split(".")[0]])
        o.location = at
        o.rotation_euler = (0, 0, rot)
        sc.collection.objects.link(o)
        out.append(o)
    return out


def tinted(ob, hexcol):
    return P.tinted_copy(ob.data.materials[0], hexcol)


# ------------------------------------------------------------------ the lobby so far
Ce = load("Hub_CleanCentre.blend", ["CleanCentre_Body", "CleanCentre_Core", "CleanCentre_Ring", "CleanCentre_Glass", "CleanCentre_Shine", "CleanCentre_Glow"])
place(Ce.values(), (0, 0, 0))
B = load("Hub_CleanBanner.blend", ["CleanBanner_Body", "CleanBanner_Trim", "CleanBanner_Bubbles", "CleanBanner_Glow"])
place(B.values(), (0, 10.6, 12.9))
Pd = load("Hub_CleanPad.blend", ["CleanPad_Body", "CleanPad_Tint", "CleanPad_Glow", "CleanPadSign_Body", "CleanPadSign_Tint"])
for i, (name, hx) in enumerate(K.PAD_COLOURS):
    x = -(-21 + 14 * i)
    m = tinted(Pd["CleanPad_Tint"], hx)
    g = P.flat_material("AGlow_" + name, K.PAD_GLOWS[name], 0.3, emit=4.0)
    place([Pd["CleanPad_Body"], Pd["CleanPad_Tint"], Pd["CleanPad_Glow"]], (x, 17, 0), 0, {"CleanPad_Tint": m, "CleanPad_Glow": g})
    place([Pd["CleanPadSign_Body"], Pd["CleanPadSign_Tint"]], (x, 17 - 5.9, 0), 0, {"CleanPadSign_Tint": m})
F = load("Hub_CleanFence.blend", ["CleanFence_Post", "CleanFence_PostGlow", "CleanFence_Rail", "CleanFence_Corner", "CleanFence_CornerGlow"])
for sx in (-1, 1):
    place([F["CleanFence_Corner"], F["CleanFence_CornerGlow"]], (sx * 55, PLAZA_Y - 55, 0))
    for k in range(-6, 7):
        place([F["CleanFence_Post"], F["CleanFence_PostGlow"]], (sx * 55, PLAZA_Y + k * STEP, 0))
    for k in range(-7, 7):
        place([F["CleanFence_Rail"]], (sx * 55, PLAZA_Y + (k + 0.5) * STEP, 0), math.pi / 2)
for k in range(-6, 7):            # back fence: only outside the hall
    if abs(k * STEP) > 32:
        place([F["CleanFence_Post"], F["CleanFence_PostGlow"]], (k * STEP, PLAZA_Y - 55, 0))
for k in range(-7, 7):
    if abs((k + 0.5) * STEP) > 34:
        place([F["CleanFence_Rail"]], ((k + 0.5) * STEP, PLAZA_Y - 55, 0))
Bo = load("Hub_CleanBooth.blend", ["CleanBooth_Body", "CleanBooth_Tint", "CleanBooth_Glow", "CleanBoothPad_Body", "CleanBoothPad_Glow"])
for i, (hz, (name, hx)) in enumerate(zip((-15, 4, 23), K.BOOTH_COLOURS)):
    y = hz + 45
    place([Bo["CleanBooth_Body"], Bo["CleanBooth_Tint"], Bo["CleanBooth_Glow"]], (-44, y, 0), -math.pi / 2,
          {"CleanBooth_Tint": tinted(Bo["CleanBooth_Tint"], hx)})
    place([Bo["CleanBoothPad_Body"], Bo["CleanBoothPad_Glow"]], (-44 + 9.75, y, 0))
T = load("Hub_CleanTree.blend", [f"CleanTree_{n}_{z}" for n in ("Ball", "Stack", "Cloud") for z in ("Tint", "Body", "Shine")])
TREES = [("Ball", -64, 4, 1.2, 1), ("Cloud", -66, 24, 1.0, 2), ("Stack", -63, 44, 1.1, 3), ("Stack", -44, -20, 1.3, 0),
         ("Cloud", 46, -20, 1.25, 1), ("Stack", 64, 8, 1.2, 0), ("Cloud", 66, 30, 1.0, 1), ("Ball", 65, 52, 1.1, 2)]
for n, x, y, s, ci in TREES:
    parts = [T[f"CleanTree_{n}_{z}"] for z in ("Tint", "Body", "Shine")]
    for o in place(parts, (x, y, -3), 0, {parts[0].name: tinted(parts[0], K.TREE_COLOURS[ci][1])}):
        o.scale = (s, s, s)
Bd = load("Hub_CleanBoard.blend", ["CleanBoard_Body", "CleanBoard_Glow"])
place(Bd.values(), (46, 25, 0), math.atan2(46, 20))
Gr = load("Hub_CleanGround.blend", ["CleanGround_Tile", "CleanGround_Kerb", "CleanGround_KerbBand", "CleanGround_KerbCorner", "CleanGround_KerbCornerBand"])
mB = P.flat_material("ATileB", "#E3E9F2", 0.3)
for i in range(8):
    for j in range(8):
        place([Gr["CleanGround_Tile"]], (-49 + 14 * i, PLAZA_Y - 49 + 14 * j, -0.2), 0, {"CleanGround_Tile": mB} if (i + j) % 2 else None)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, vec=(112, 112, 2.7), verts=bm.verts)
bmesh.ops.translate(bm, vec=(0, PLAZA_Y, -1.65), verts=bm.verts)
me = bpy.data.meshes.new("PreviewSlab")
bm.to_mesh(me)
bm.free()
slab = bpy.data.objects.new("PreviewSlab", me)
sc.collection.objects.link(slab)
me.materials.append(P.flat_material("PreviewSlab", K.PAL["white"], 0.4))

# ------------------------------------------------------------------ the prop kit
H = load("Hub_CleanHall.blend", ["CleanHall_Body", "CleanHall_Glow", "CleanHall_Shine"], C.OUT)
place(H.values(), (0, -7, 0))                                    # hub (0, 0, -52)
S = load("Hub_CleanProps.blend", ["CleanLamp_Body", "CleanLamp_Glow", "CleanBench_Body", "CleanBench_Tint",
                                  "CleanPlanter_Body", "CleanPlanter_Tint", "CleanPlanter_Shine"], C.OUT)
LAMP = [S["CleanLamp_Body"], S["CleanLamp_Glow"]]
BENCH = [S["CleanBench_Body"], S["CleanBench_Tint"]]
PLANT = [S["CleanPlanter_Body"], S["CleanPlanter_Tint"], S["CleanPlanter_Shine"]]
TC = dict(K.TREE_COLOURS)
for x, y in ((-30, 0), (33, 3), (-29, 36), (29, 36), (-49, -5), (49, -5), (-14, 66), (14, 66)):
    place(LAMP, (x, y, 0))
for x, y, rot, col in ((-38, -5, 0, "Mint"), (38, -5, 0, "Lilac"), (-44, -5, 0, "Peach"), (44, -5, 0, "Sky"),
                       (50, 56, math.pi / 2, "Mint"), (50, 78, math.pi / 2, "Peach")):
    place(PLANT, (x, y, 0), rot, {"CleanPlanter_Tint": tinted(S["CleanPlanter_Tint"], TC[col])})
for x, y, rot, col in ((50, 49, math.pi / 2, "Sky"), (50, 63, math.pi / 2, "Lilac"), (50, 71, math.pi / 2, "Sky")):
    place(BENCH, (x, y, 0), rot, {"CleanBench_Tint": tinted(S["CleanBench_Tint"], TC[col])})
if os.path.exists(os.path.join(C.OUT, "Hub_CleanLeaderboard.blend")):
    L = load("Hub_CleanLeaderboard.blend", ["CleanLeaderboard_Body", "CleanLeaderboard_Glow"], C.OUT)
    place(L.values(), (-38, 12, 0), math.atan2(-0.5, 1.0))       # hub (38, 0, -33), turned to the centre
bpy.context.view_layer.update()

fl = K.studio((0, 30, 0), 60)
fl.location.z = -3.0
fl.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.80, 0.62, 1)
fl.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
P.player_block((10, 30, 0))
P.shoot(os.path.join(C.PREV, "hub_cleanprops_assembled_beauty.png"), Vector((0, 22, 12)), Vector((0.42, 1.0, 0.36)), 150, 40)
P.shoot(os.path.join(C.PREV, "hub_cleanprops_assembled_player.png"), Vector((0, 0, 14)), Vector((0.12, 1.0, 0.1)), 92, 32, res=(1280, 720))
print("ASSEMBLED done")
