# CLEAN POP PLAZA 6b: ground pieces in the clean style, flat colours, no texture (same sizes and
# placement as art/hub_plaza Hub_Ground).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_ground.py
#
# Hub_CleanGround.fbx holds separate models: CleanGround_Tile (14 x 14 x 0.2, tinted),
# CleanGround_Kerb + CleanGround_KerbBand (straight, 14 long), CleanGround_KerbCorner + CleanGround_KerbCornerBand.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
import bpy  # noqa: E402

P = K.P
sc = K.reset()
TILE_A, TILE_B = K.PAL["white"], "#E3E9F2"
M = {
    "tile": P.flat_material("CleanGround_Tile", TILE_A, 0.3),
    "kerb": P.flat_material("CleanGround_Kerb", K.PAL["white"], 0.28),
    "band": P.flat_material("CleanGround_KerbBand", K.PAL["sky"], 0.2),
}
# (y outward, z) sections; y = 0 is the plaza slab edge (the kerb's hidden back), z = 0 the grass
WALL = [(1.1, 0.85), (1.2, 1.1), (1.25, 2.2), (1.2, 2.62), (1.0, 2.9), (0.7, 3.0), (0.0, 3.0)]
BAND = [(1.4, 0.0), (1.55, 0.18), (1.55, 0.74), (1.42, 0.95), (1.2, 1.0), (1.0, 1.0)]
HALF = 7.0


def straight(mb, section, zone):
    rows = [[mb.bm.verts.new((x, y, z)) for (y, z) in section] for x in (-HALF, HALF)]
    for i in range(len(section) - 1):
        mb.face((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]), zone)


tile = P.MeshBuilder("CleanGround_Tile")
tile.lathe([(7.0, 0.0), (7.0, 0.1), (6.95, 0.17), (6.86, 0.2)], P.square2d, zone="tile", cap_last=True)
kerb = P.MeshBuilder("CleanGround_Kerb")
straight(kerb, WALL, "kerb")
band = P.MeshBuilder("CleanGround_KerbBand")
straight(band, BAND, "band")
quarter = lambda d: P.circle2d(d, 6, arc=(0, math.pi / 2))
ckerb = P.MeshBuilder("CleanGround_KerbCorner")
ckerb.lathe(WALL, quarter, zone="kerb", closed=False)
cband = P.MeshBuilder("CleanGround_KerbCornerBand")
cband.lathe(BAND, quarter, zone="band", closed=False)

objs = [tile.build(M), kerb.build(M), band.build(M), ckerb.build(M), cband.build(M)]
o_tile, o_kerb, o_band, o_ck, o_cb = objs
for o in objs:
    P.unwrap([o], margin=0.02)
print("[Hub_CleanGround] triangles")
P.report(objs, {"CleanGround_Tile": 60})
print(f"  kerb {P.tris(o_kerb) + P.tris(o_band)} (budget 150), corner {P.tris(o_ck) + P.tris(o_cb)} (budget 150)")
P.export_fbx(os.path.join(K.OUT, "Hub_CleanGround.fbx"), objs)
P.write_bounds(os.path.join(K.OUT, "Hub_CleanGround.bounds.json"), {
    "CleanGround_Tile": P.bounds_entry(o_tile, material="SmoothPlastic", castShadow=False,
                                       variants={"A": K.rgb255(TILE_A), "B": K.rgb255(TILE_B), "optional warm": K.rgb255(K.PAL["cream"])},
                                       note="replaces each Tile part 1:1 (same 14 x 14 x 0.2 box, top at plaza height 0)"),
    "CleanGround_Kerb": P.bounds_entry(o_kerb, material="SmoothPlastic", color=K.rgb255(K.PAL["white"])),
    "CleanGround_KerbBand": P.bounds_entry(o_band, material="SmoothPlastic", color=K.rgb255(K.PAL["sky"])),
    "CleanGround_KerbCorner": P.bounds_entry(o_ck, material="SmoothPlastic", color=K.rgb255(K.PAL["white"])),
    "CleanGround_KerbCornerBand": P.bounds_entry(o_cb, material="SmoothPlastic", color=K.rgb255(K.PAL["sky"])),
}, notes="CLEAN POP PLAZA ground. Kerb replaces the Plaza slab's side faces and PlazaTrim (keep the slab as the walkable part). "
         "Kerb origin = on the slab edge line at grass height (plaza floor - 3), front (+Y) facing out of the plaza; it sits "
         "outside the 112 slab (1.55 out), top lip flush with the plaza floor. 8 segments per side, centres at u = -49, -35, "
         "..., 49. KerbCorner origin = the slab corner; unturned it fills the quadrant +X/+Y (Blender) = +X/-Z (Roblox).")
P.save_blend(os.path.join(K.OUT, "Hub_CleanGround.blend"), None)

# ------------------------------------------------------------------ previews: a plaza corner (3 x 3 tiles, kerb on two sides)
mB = P.flat_material("CleanGround_TileB", TILE_B, 0.3)
for o in objs:
    o.hide_render = True
show = []
for i in range(3):
    for j in range(3):
        show += K.copies([o_tile], (-7 - 14 * i, -7 - 14 * j, 3.0 - 0.2), {"CleanGround_Tile": mB} if (i + j) % 2 else None)
for i in range(3):
    show += K.copies([o_kerb, o_band], (-7 - 14 * i, 0, 0))
    r = K.copies([o_kerb, o_band], (0, -7 - 14 * i, 0))
    for o in r:
        o.rotation_euler = (0, 0, -math.pi / 2)
    show += r
show += K.copies([o_ck, o_cb], (0, 0, 0))
bpy.context.view_layer.update()
K.studio((-14, -14, 1), 26)
P.standard_previews("hub_clean_ground", show, block_at=(-10, -10, 3), beauty_dir=(0.55, 1.0, 0.5), lens=60)
print("GROUND done")
