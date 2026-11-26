# CLEAN POP PLAZA: the assembled overview picture. Loads the finished models from art/hub_clean/*.blend
# (run the other hub_clean_*.py scripts first) and lays them out as in Hub.lua: centrepiece + banner,
# the 4 pads with signs, a fence corner, a booth with its pad, bubble trees, the board, on the tiled plaza.
# Makes no models; writes art/previews/hub_clean_assembled_beauty.png (+ _flat, _thumb, _wide).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_assembled.py
#
# Scene axes: Blender +Y = towards the spawn (hub +Z), Blender X = -hub X; the centrepiece is at the origin
# (hub (0, 0, -45)), so the plaza centre is at (0, 45).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

P = K.P
sc = K.reset()
STEP = 7.857
PLAZA_Y = 45.0


def load(blend, names):
    path = os.path.join(K.OUT, blend)
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in names if n in src.objects]
    return {o.name.split(".")[0]: o for o in dst.objects}


def place(srcs, at, rot=0.0, mats=None):
    out = []
    for s in srcs:
        o = s.copy()
        if mats and s.name in mats:
            o.data = s.data.copy()
            K.set_mat(o, mats[s.name])
        o.location = at
        o.rotation_euler = (0, 0, rot)
        sc.collection.objects.link(o)
        out.append(o)
    return out


def tinted(ob, hexcol):
    return P.tinted_copy(ob.data.materials[0], hexcol)


shown = []
C = load("Hub_CleanCentre.blend", ["CleanCentre_Body", "CleanCentre_Core", "CleanCentre_Ring", "CleanCentre_Glass", "CleanCentre_Shine", "CleanCentre_Glow"])
shown += place(C.values(), (0, 0, 0))
B = load("Hub_CleanBanner.blend", ["CleanBanner_Body", "CleanBanner_Trim", "CleanBanner_Bubbles", "CleanBanner_Glow"])
shown += place(B.values(), (0, 10.6, 12.9))

Pd = load("Hub_CleanPad.blend", ["CleanPad_Body", "CleanPad_Tint", "CleanPad_Glow", "CleanPadSign_Body", "CleanPadSign_Tint", "CleanSpawnPad_Body"])
for i, (name, hx) in enumerate(K.PAD_COLOURS):
    x = -(-21 + 14 * i)
    m = tinted(Pd["CleanPad_Tint"], hx)
    g = P.flat_material("AGlow_" + name, K.PAD_GLOWS[name], 0.3, emit=4.0)
    shown += place([Pd["CleanPad_Body"], Pd["CleanPad_Tint"], Pd["CleanPad_Glow"]], (x, 17, 0), 0,
                   {"CleanPad_Tint": m, "CleanPad_Glow": g})
    shown += place([Pd["CleanPadSign_Body"], Pd["CleanPadSign_Tint"]], (x, 17 - 5.9, 0), 0, {"CleanPadSign_Tint": m})
shown += place([Pd["CleanSpawnPad_Body"]], (0, 79, 0))

F = load("Hub_CleanFence.blend", ["CleanFence_Post", "CleanFence_PostGlow", "CleanFence_Rail", "CleanFence_Corner", "CleanFence_CornerGlow"])
for sx in (-1, 1):            # both back corners, the back line and the two side lines
    shown += place([F["CleanFence_Corner"], F["CleanFence_CornerGlow"]], (sx * 55, PLAZA_Y - 55, 0))
    for k in range(-6, 7):
        shown += place([F["CleanFence_Post"], F["CleanFence_PostGlow"]], (sx * 55, PLAZA_Y + k * STEP, 0))
    for k in range(-7, 7):
        shown += place([F["CleanFence_Rail"]], (sx * 55, PLAZA_Y + (k + 0.5) * STEP, 0), math.pi / 2)
for k in range(-6, 7):
    shown += place([F["CleanFence_Post"], F["CleanFence_PostGlow"]], (k * STEP, PLAZA_Y - 55, 0))
for k in range(-7, 7):
    shown += place([F["CleanFence_Rail"]], ((k + 0.5) * STEP, PLAZA_Y - 55, 0))

Bo = load("Hub_CleanBooth.blend", ["CleanBooth_Body", "CleanBooth_Tint", "CleanBooth_Glow", "CleanBoothPad_Body", "CleanBoothPad_Glow"])
for i, (hz, (name, hx)) in enumerate(zip((-15, 4, 23), K.BOOTH_COLOURS)):
    y = hz + 45
    shown += place([Bo["CleanBooth_Body"], Bo["CleanBooth_Tint"], Bo["CleanBooth_Glow"]], (-44, y, 0), -math.pi / 2,
                   {"CleanBooth_Tint": tinted(Bo["CleanBooth_Tint"], hx)})
    shown += place([Bo["CleanBoothPad_Body"], Bo["CleanBoothPad_Glow"]], (-44 + 9.75, y, 0))

T = load("Hub_CleanTree.blend", [f"CleanTree_{n}_{z}" for n in ("Ball", "Stack", "Cloud") for z in ("Tint", "Body", "Shine")])
TREES = [("Ball", -64, 4, 1.2, 1), ("Cloud", -66, 24, 1.0, 2), ("Stack", -63, 44, 1.1, 3), ("Stack", -40, -17, 1.3, 0),
         ("Ball", -20, -19, 1.0, 2), ("Cloud", 22, -18, 1.25, 1), ("Ball", 45, -16, 1.1, 3), ("Stack", 64, 8, 1.2, 0), ("Cloud", 66, 30, 1.0, 1)]
for n, x, y, s, ci in TREES:
    parts = [T[f"CleanTree_{n}_{z}"] for z in ("Tint", "Body", "Shine")]
    new = place(parts, (x, y, -3), 0, {parts[0].name: tinted(parts[0], K.TREE_COLOURS[ci][1])})
    for o in new:
        o.scale = (s, s, s)
    shown += new

if os.path.exists(os.path.join(K.OUT, "Hub_CleanBoard.blend")):
    Bd = load("Hub_CleanBoard.blend", ["CleanBoard_Body", "CleanBoard_Glow"])
    shown += place(Bd.values(), (46, 25, 0), math.atan2(46, 20))
if os.path.exists(os.path.join(K.OUT, "Hub_CleanGift.blend")):
    G = load("Hub_CleanGift.blend", ["CleanGift_Body", "CleanGift_Lid", "CleanGift_Glow"])
    shown += place(G.values(), (24, 85, 0), math.radians(-150))

# the plaza: 8 x 8 tiles (two tints) on a white slab; the lawn is the studio floor
tiles = []
if os.path.exists(os.path.join(K.OUT, "Hub_CleanGround.blend")):
    Gr = load("Hub_CleanGround.blend", ["CleanGround_Tile", "CleanGround_Kerb", "CleanGround_KerbBand", "CleanGround_KerbCorner", "CleanGround_KerbCornerBand"])
    mB = P.flat_material("ATileB", "#E3E9F2", 0.3)
    for i in range(8):
        for j in range(8):
            tiles += place([Gr["CleanGround_Tile"]], (-49 + 14 * i, PLAZA_Y - 49 + 14 * j, -0.2), 0,
                           {"CleanGround_Tile": mB} if (i + j) % 2 else None)
    for i in range(8):
        u = -49 + 14 * i
        for (pos, rot) in (((u, PLAZA_Y + 56, -3), 0), ((u, PLAZA_Y - 56, -3), math.pi), ((56, PLAZA_Y + u, -3), -math.pi / 2),
                           ((-56, PLAZA_Y + u, -3), math.pi / 2)):
            tiles += place([Gr["CleanGround_Kerb"], Gr["CleanGround_KerbBand"]], pos, rot)
    for (pos, rot) in (((56, PLAZA_Y + 56, -3), 0), ((-56, PLAZA_Y + 56, -3), math.pi / 2), ((-56, PLAZA_Y - 56, -3), math.pi),
                       ((56, PLAZA_Y - 56, -3), -math.pi / 2)):
        tiles += place([Gr["CleanGround_KerbCorner"], Gr["CleanGround_KerbCornerBand"]], pos, rot)
import bmesh  # noqa: E402
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
bpy.context.view_layer.update()

fl = K.studio((0, 30, 0), 60)
fl.location.z = -3.0
fl.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.52, 0.80, 0.62, 1)   # soft mint lawn
fl.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
block = P.player_block((10, 30, 0))

target = Vector((-14, 12, 11))
view = Vector((0.62, 1.0, 0.45))
base = os.path.join(K.PREV, "hub_clean_assembled")
P.shoot(base + "_beauty.png", target, view, 124, 40)
if not K.FAST: P.shoot(base + "_thumb.png", target, view, 124, 40, res=(256, 192))
if not K.FAST: P.shoot(base + "_wide.png", (0, 38, 4), (0.25, 1.0, 0.5), 205, 40)
for o in shown:
    if o.data.materials and o.data.materials[0] and o.data.materials[0].use_nodes and "Tint" in o.data.materials[0].node_tree.nodes:
        o.data = o.data.copy()
        K.set_mat(o, P.flat_copy(o.data.materials[0]))
if not K.FAST: P.shoot(base + "_flat.png", target, view, 124, 40)
print("ASSEMBLED done")
