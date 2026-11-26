# Batch B combined preview: 4 pads in a row (with signs), the spawn pad, a fence corner with a 5-post run,
# kerb and corner, all on a patch of tiles. Run AFTER hub_plaza_pad/fence/ground/board.py (it appends
# their .blend files; it writes nothing but the preview).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_plaza_kit.py
#
# Output: art/previews/hub_plaza_kit.png (+ hub_plaza_kit_top.png)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as C  # noqa: E402
import bpy  # noqa: E402

sc = C.reset()
STEP = 110 / 14
src = {}
for blend, names in (("Hub_Pad.blend", ["Pad_Body", "Pad_Tint", "Pad_Glow", "PadSign_Body", "PadSign_Tint", "SpawnPad_Body"]),
                     ("Hub_Fence.blend", ["Fence_Post", "Fence_PostGlow", "Fence_Rail", "Fence_Corner"]),
                     ("Hub_Ground.blend", ["Ground_Tile", "Ground_Kerb", "Ground_KerbBand", "Ground_KerbCorner", "Ground_KerbCornerBand"]),
                     ("Hub_Board.blend", ["Board_Body"])):
    with bpy.data.libraries.load(os.path.join(C.OUT, blend), link=False) as (data_from, data_to):
        data_to.objects = [n for n in names if n in data_from.objects]
    for ob in data_to.objects:
        src[ob.name] = ob


def put(name, loc, rot=0.0, mat=None):
    s = src[name]
    ob = s.copy()
    if mat:
        ob.data = s.data.copy()
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    sc.collection.objects.link(ob)
    return ob


pink = C.flat_material("Tile_B", C.PAL["tilepink"], 0.3)
pad_mat = src["Pad_Tint"].data.materials[0]
# plaza patch: 5 x 3 tiles, x -35..35, y -28..14 (front +Y towards the camera); back-left corner at (-35, -28)
for i in range(5):
    for j in range(3):
        put("Ground_Tile", (-28 + 14 * i, -21 + 14 * j, -0.2), mat=None if (i + j) % 2 == 0 else pink)
for k in range(5):
    put("Ground_Kerb", (-28 + 14 * k, -28, -3), math.pi), put("Ground_KerbBand", (-28 + 14 * k, -28, -3), math.pi)
for k in range(3):
    put("Ground_Kerb", (-35, -21 + 14 * k, -3), math.pi / 2), put("Ground_KerbBand", (-35, -21 + 14 * k, -3), math.pi / 2)
put("Ground_KerbCorner", (-35, -28, -3), math.pi), put("Ground_KerbCornerBand", (-35, -28, -3), math.pi)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -7, -1.6))
slab = bpy.context.active_object
slab.scale = (70, 42, 2.8)
slab.data.materials.append(C.flat_material("Slab", C.PAL["cream"], 0.5))

# fence: corner 1 stud in from the edges, 5 posts along the back, 2 along the left side
fx, fy = -34, -27
put("Fence_Corner", (fx, fy, 0), math.pi)  # rail rings face +X and +Y here
for k in range(1, 6):
    put("Fence_Post", (fx + k * STEP, fy, 0)), put("Fence_PostGlow", (fx + k * STEP, fy, 0))
for k in range(5):
    put("Fence_Rail", (fx + (k + 0.5) * STEP, fy, 0))
for k in range(1, 3):
    put("Fence_Post", (fx, fy + k * STEP, 0), math.pi / 2), put("Fence_PostGlow", (fx, fy + k * STEP, 0), math.pi / 2)
for k in range(2):
    put("Fence_Rail", (fx, fy + (k + 0.5) * STEP, 0), math.pi / 2)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(fx, fy, 5.34), segments=32, ring_count=16)
bpy.ops.object.shade_smooth()
bpy.context.active_object.data.materials.append(C.flat_material("GumballStandIn", "#2878E6", 0.12))

# pads (front towards +Y) with signs behind, and the spawn pad
for i, (name, hx) in enumerate(C.PAD_COLOURS):
    x = -21 + 14 * i
    m = C.tinted_copy(pad_mat, hx, "Pad_" + name)
    put("Pad_Body", (x, -12, 0)), put("Pad_Tint", (x, -12, 0), mat=m)
    put("Pad_Glow", (x, -12, 0), mat=C.flat_material("Glow_" + name, C.PAD_GLOWS[name], 0.3, emit=4.0))
    put("PadSign_Body", (x, -17.9, 0)), put("PadSign_Tint", (x, -17.9, 0), mat=m)
put("SpawnPad_Body", (0, 6, 0))
put("Board_Body", (-27, 4, 0), math.radians(-60))
C.player_block((10, 3, 0))
for s in src.values():
    pass  # appended sources are not linked to the scene, so they don't render

C.studio((0, -7, 0), 30, floor_z=-3.0, floor_col=C.lin(C.PAL["grass"]))
C.shoot(os.path.join(C.PREV, "hub_plaza_kit.png"), (-3, -10, 1), (0.35, 1.0, 0.55), 75, 40)
C.shoot(os.path.join(C.PREV, "hub_plaza_kit_top.png"), (0, -7, 0), (0.0, 0.25, 1.0), 95, 40, res=(1280, 800))
print("KIT done")
