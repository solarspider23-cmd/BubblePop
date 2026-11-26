# Batch B5: ground pieces, flat colours, no texture.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_plaza_ground.py
#
# Hub_Ground.fbx holds separate models:
#   Ground_Tile            14 x 14 x 0.2, flat top, small rounded edge -> a thin groove between tiles (tinted)
#   Ground_Kerb            straight 14-long kerb, 3 high, ~1.55 deep: cream wall with a rounded top lip
#   Ground_KerbBand        its red "cake board" band along the bottom (separate mesh: flat colours)
#   Ground_KerbCorner      quarter-round outside corner, same profile
#   Ground_KerbCornerBand  its red band
# Outputs (art/hub_plaza/): Hub_Ground.fbx, Hub_Ground.blend, Hub_Ground.bounds.json
# previews art/previews/hub_plaza_ground_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as C  # noqa: E402
import bpy  # noqa: E402

sc = C.reset()
M = {
    "tile": C.flat_material("Ground_Tile", C.PAL["cream"], 0.3),
    "kerb": C.flat_material("Ground_Kerb", C.PAL["cream"], 0.3),
    "band": C.flat_material("Ground_KerbBand", C.PAL["red"], 0.25),
}

# (y outward, z) sections; y = 0 is the plaza slab edge (the kerb's hidden back), z = 0 the grass
WALL = [(1.12, 0.85), (1.22, 1.15), (1.25, 2.3), (1.2, 2.68), (1.02, 2.92), (0.75, 3.0), (0.0, 3.0)]
BAND = [(1.42, 0.0), (1.55, 0.14), (1.55, 0.78), (1.44, 0.96), (1.2, 1.0), (1.02, 1.0)]
HALF = 7.0


def straight(mb, section, zone):
    rows = [[mb.bm.verts.new((x, y, z)) for (y, z) in section] for x in (-HALF, HALF)]
    for i in range(len(section) - 1):
        mb.face((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]), zone)


tile = C.MeshBuilder("Ground_Tile")
tile.lathe([(7.0, 0.0), (7.0, 0.1), (6.95, 0.17), (6.86, 0.2)], C.square2d, zone="tile", cap_last=True)

kerb = C.MeshBuilder("Ground_Kerb")
straight(kerb, WALL, "kerb")
band = C.MeshBuilder("Ground_KerbBand")
straight(band, BAND, "band")

quarter = lambda d: C.circle2d(d, 6, arc=(0, math.pi / 2))
ckerb = C.MeshBuilder("Ground_KerbCorner")
ckerb.lathe(WALL, quarter, zone="kerb", closed=False)
cband = C.MeshBuilder("Ground_KerbCornerBand")
cband.lathe(BAND, quarter, zone="band", closed=False)

objs = [tile.build(M), kerb.build(M), band.build(M), ckerb.build(M), cband.build(M)]
o_tile, o_kerb, o_band, o_ck, o_cb = objs
C.unwrap([o_tile], margin=0.02)
C.unwrap([o_kerb, o_band, o_ck, o_cb], margin=0.02)
print("[Hub_Ground] triangles")
C.report(objs, {"Ground_Tile": 60})
print(f"  kerb {C.tris(o_kerb) + C.tris(o_band)} (budget 150), corner {C.tris(o_ck) + C.tris(o_cb)} (budget 150)")

C.export_fbx(os.path.join(C.OUT, "Hub_Ground.fbx"), objs)
C.write_bounds(os.path.join(C.OUT, "Hub_Ground.bounds.json"), {
    "Ground_Tile": C.bounds_entry(o_tile, material="SmoothPlastic", castShadow=False,
                                  variants={"A": [255, 248, 252], "B": C.rgb255(C.PAL["tilepink"])},
                                  note="replaces each Tile part 1:1 (same 14 x 14 x 0.2 box, top at plaza height 0)"),
    "Ground_Kerb": C.bounds_entry(o_kerb, material="SmoothPlastic", color=C.rgb255(C.PAL["cream"])),
    "Ground_KerbBand": C.bounds_entry(o_band, material="SmoothPlastic", color=C.rgb255(C.PAL["red"])),
    "Ground_KerbCorner": C.bounds_entry(o_ck, material="SmoothPlastic", color=C.rgb255(C.PAL["cream"])),
    "Ground_KerbCornerBand": C.bounds_entry(o_cb, material="SmoothPlastic", color=C.rgb255(C.PAL["red"])),
}, notes="Kerb replaces the Plaza slab's side faces and PlazaTrim (keep the Plaza slab itself as the walkable/"
         "collision part). Kerb origin = on the slab edge line at grass height (plaza floor - 3), front (+Y) facing "
         "out of the plaza; the kerb sits OUTSIDE the 112 slab (back face on the slab edge, 1.55 out), its top lip "
         "flush with the plaza floor. 8 segments per side, centres at u = -49, -35, ..., 49 along the edge. "
         "KerbCorner origin = the slab corner itself (its lathe axis); unturned it fills the quadrant +X/+Y "
         "(Blender) = +X/-Z (Roblox); turn it in 90-degree steps for the other corners.")
C.save_blend(os.path.join(C.OUT, "Hub_Ground.blend"), None)

# ------------------------------------------------------------------ previews: a plaza corner
C.studio((0, 0, -1), 12, floor_z=-3.0, floor_col=C.lin(C.PAL["grass"]))
pink = C.flat_material("Tile_B", C.PAL["tilepink"], 0.3)
parts = []


def put(src, loc, rot=0.0, mat=None):
    ob = src.copy()
    if mat:
        ob.data = src.data.copy()
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    sc.collection.objects.link(ob)
    parts.append(ob)
    return ob


# 2 x 2 tiles; the plaza corner at (14, 14); kerbs on the +X and +Y edges
for i in range(2):
    for j in range(2):
        put(o_tile, (-7 + 14 * i, -7 + 14 * j, -0.2), mat=None if (i + j) % 2 == 0 else pink)
for k in range(2):
    put(o_kerb, (-7 + 14 * k, 14, -3)), put(o_band, (-7 + 14 * k, 14, -3))
    put(o_kerb, (14, -7 + 14 * k, -3), -math.pi / 2), put(o_band, (14, -7 + 14 * k, -3), -math.pi / 2)
put(o_ck, (14, 14, -3)), put(o_cb, (14, 14, -3))
# the plaza slab under the tiles (a plain part in game)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -1.6))
slab = bpy.context.active_object
slab.scale = (28, 28, 2.8)
slab.data.materials.append(C.flat_material("Slab", C.PAL["cream"], 0.5))
for o in objs:
    o.hide_render = True
C.standard_previews("hub_plaza_ground", parts, block_at=(9, 3, 0), beauty_dir=(1.0, 0.85, 0.5))

# colour variants: the two tile colours
for o in parts + [slab]:
    o.hide_render = True
show = [put(o_tile, (-7.5, 0, 0)), put(o_tile, (7.5, 0, 0), mat=pink)]
lo, hi = C.world_bounds(show)
C.shoot(os.path.join(C.PREV, "hub_plaza_ground_colours.png"), (lo + hi) / 2, (0.0, 1.0, 0.8),
        C.fit_dist((hi - lo).length / 2, 50, margin=0.95), 50, res=(1280, 720))
print("GROUND done")
