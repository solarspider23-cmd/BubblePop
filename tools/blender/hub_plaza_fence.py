# Batch B3: candy-cane fence kit. One 256 texture set (Hub_Fence_*) shared by post, corner and rail.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_plaza_fence.py
#
# Outputs (art/hub_plaza/): Hub_Fence.fbx holding
#   Fence_Post      fat round candy-cane post, 1.6 across, 3.4 tall (spiral stripes in the texture)
#   Fence_PostGlow  gumdrop cap (Neon, flat colour)
#   Fence_Rail      one 7.857 segment: cream rail at 2.4, mint rail at 1.2 (ends hide inside the posts)
#   Fence_Corner    2.2 across, 4.5 tall, with a cup on top for the game's gumball
# Hub_Fence_color/_normal/_roughness.png (256), Hub_Fence.blend, Hub_Fence.bounds.json
# previews: art/previews/hub_plaza_fence_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as C  # noqa: E402
from mathutils import Vector  # noqa: E402

TEX = 256
STEP = 110 / 14          # 7.857: post spacing (15 posts per 110-stud side)
RAILS = (1.2, 2.4)
sc = C.reset()


def grommets(nb, axes):
    """Painted + embossed rings where the rails enter the post. axes: 'x' = rails on +X and -X (posts),
    '-x-y' = rails on -X and -Y only (corner)."""
    ring_all, hole_all = 0.0, 0.0
    sides = [("x", 0)] if axes == "x" else [("x", -1), ("y", -1)]
    for ax, sign in sides:
        side_coord = nb.x if ax == "x" else nb.y
        across = nb.y if ax == "x" else nb.x
        facing = nb.smooth(nb.ab(side_coord) if sign == 0 else nb.mul(side_coord, sign), 0.35, 0.6)
        for zr in RAILS:
            d = nb.length2(across, nb.sub(nb.z, zr))
            ring = nb.mul(nb.mul(nb.smooth(d, 0.27, 0.31), nb.smooth(d, 0.46, 0.41)), facing)
            hole = nb.mul(nb.smooth(d, 0.31, 0.26), facing)
            ring_all = ring if isinstance(ring_all, float) else nb.mx(ring_all, ring)
            hole_all = hole if isinstance(hole_all, float) else nb.mx(hole_all, hole)
    return ring_all, hole_all


def cane(radius, axes):
    def color(nb):
        s = nb.spiral(nb.x, nb.y, nb.z, radius, n=2, angle_deg=38, sharp=6.0)
        c = nb.mixc(C.lin(C.PAL["cream"]), C.lin(C.PAL["red"]), s)
        ring, hole = grommets(nb, axes)
        c = nb.mixc(c, C.lin(C.PAL["cream"]), ring)
        return nb.scalec(c, nb.sub(1.0, nb.mul(hole, 0.35)))

    def rough(nb):
        s = nb.spiral(nb.x, nb.y, nb.z, radius, n=2, angle_deg=38, sharp=6.0)
        return nb.lerp(0.26, 0.18, s)

    def height(nb):
        s = nb.spiral(nb.x, nb.y, nb.z, radius, n=2, angle_deg=38, sharp=3.0)
        ring, hole = grommets(nb, axes)
        return nb.add(nb.mul(s, 0.012), nb.mul(ring, 0.04))

    return color, rough, height


def rail_color(nb):
    return nb.mixc(C.lin(C.PAL["mint"]), C.lin(C.PAL["cream"]), nb.smooth(nb.z, 1.7, 1.9))


pc, pr, ph = cane(0.8, "x")
cc, cr, ch = cane(1.1, "-x-y")
Z = {
    "cane_post": C.zone_material("cane_post", pc, pr, ph, ao=0.2, ao_dist=0.5, grad=0.08, zr=(0, 3.4)),
    "cane_corner": C.zone_material("cane_corner", cc, cr, ch, ao=0.2, ao_dist=0.5, grad=0.08, zr=(0, 4.5)),
    "collar": C.zone_material("collar", C.PAL["cream"], 0.3, ao=0.25, ao_dist=0.4, grad=0.06, zr=(0, 4.5)),
    "cup": C.zone_material("cup", C.PAL["pink"], 0.35, ao=0.35, ao_dist=0.5, grad=0.0),
    "rail": C.zone_material("rail", rail_color, 0.3, ao=0.1, grad=0.0),
}
GLOW = C.flat_material("Fence_PostGlow", C.PAL["glow"], 0.3, emit=4.0)
mats = dict(Z, glow=GLOW)

ring12 = lambda d: C.circle2d(d, 12)
post = C.MeshBuilder("Fence_Post")
post.lathe([(1.0, 0.0, "collar"), (1.0, 0.16), (0.9, 0.33), (0.8, 0.40, "cane_post"), (0.8, 3.02, "collar"),
            (0.9, 3.10), (0.9, 3.27), (0.78, 3.38), (0.6, 3.36)], ring12)

glow = C.MeshBuilder("Fence_PostGlow")
glow.lathe([(0.64, 3.32), (0.64, 3.5), (0.57, 3.74), (0.38, 3.92), (0.0, 3.99)], lambda d: C.circle2d(d, 10), zone="glow")

corner = C.MeshBuilder("Fence_Corner")
corner.lathe([(1.38, 0.0, "collar"), (1.38, 0.2), (1.24, 0.42), (1.1, 0.5, "cane_corner"), (1.1, 3.95, "collar"),
              (1.22, 4.05), (1.22, 4.3), (1.06, 4.5), (0.86, 4.5, "cup"), (0.72, 4.36), (0.0, 4.28)],
             lambda d: C.circle2d(d, 16))

rail = C.MeshBuilder("Fence_Rail")
for z in RAILS:
    rail.tube([(-STEP / 2, 0, z), (STEP / 2, 0, z)], 0.28, segs=8, zone="rail")

o_post, o_glow, o_corner, o_rail = post.build(mats), glow.build(mats), corner.build(mats), rail.build(mats)
textured = [o_post, o_corner, o_rail]
C.unwrap(textured, margin=0.03)
C.unwrap([o_glow], margin=0.03)
o_corner.location = (6, 0, 0)
o_rail.location = (0, 8, 0)
fin, maps = C.bake_set("Hub_Fence", textured, TEX)
for o in (o_corner, o_rail):
    o.location = (0, 0, 0)

print("[Hub_Fence] triangles")
C.report([o_post, o_glow, o_rail, o_corner],
         {"Fence_Post": 250, "Fence_PostGlow": 80, "Fence_Rail": 100, "Fence_Corner": 350})

C.export_fbx(os.path.join(C.OUT, "Hub_Fence.fbx"), [o_post, o_glow, o_rail, o_corner])
tex = {"color": "Hub_Fence_color.png", "normal": "Hub_Fence_normal.png", "roughness": "Hub_Fence_roughness.png"}
C.write_bounds(os.path.join(C.OUT, "Hub_Fence.bounds.json"), {
    "Fence_Post": C.bounds_entry(o_post, textures=tex, material="SmoothPlastic (SurfaceAppearance)",
                                 note="turn so its X axis runs along the fence (rail grommets are on +-X)"),
    "Fence_PostGlow": C.bounds_entry(o_glow, textures=None, material="Neon", color=C.rgb255(C.PAL["glow"]),
                                     castShadow=False, note="same origin as Fence_Post"),
    "Fence_Rail": C.bounds_entry(o_rail, textures=tex, material="SmoothPlastic (SurfaceAppearance)",
                                 note="one segment, post centre to post centre (7.857); X along the fence"),
    "Fence_Corner": C.bounds_entry(o_corner, textures=tex, material="SmoothPlastic (SurfaceAppearance)",
                                   gumball={"diameter": 2.4, "center": [0, 5.34, 0]},
                                   note="rail rings on its -X and +Z sides (Roblox; Blender -X and -Y): turn it so those face along the two fence runs"),
}, notes="Replaces Rail x8, Post x60, PostLight x60 in buildPlaza(). Fence line 55 studs from the plaza centre "
         "(edge = half - 1). Per side: posts at u = k * 7.857 for k = -6..6 (13 Fence_Post + Fence_PostGlow), corners "
         "at k = +-7 (Fence_Corner + the game's gumball), 14 Fence_Rail segments centred at u = (k + 0.5) * 7.857, "
         "k = -7..6. All origins on the plaza floor (height 0).")
o_glow.data.materials.clear()
o_glow.data.materials.append(GLOW)
C.save_blend(os.path.join(C.OUT, "Hub_Fence.blend"), None)

# ------------------------------------------------------------------ previews: a fence corner with two runs
C.studio((0, 0, 2), 10)


def place(src, loc, rot=0.0):
    ob = src.copy()
    ob.location = loc
    ob.rotation_euler = (0, 0, rot)
    ob.hide_render = False
    sc.collection.objects.link(ob)
    return ob


ball = None
parts = []
# corner at the origin; a run of 3 posts along -X and 1 post along -Y (front of the fence faces +Y)
cx, cy = 0.0, 0.0
parts.append(place(o_corner, (cx, cy, 0)))
for k in range(1, 4):
    parts += [place(o_post, (cx - k * STEP, cy, 0)), place(o_glow, (cx - k * STEP, cy, 0))]
for k in range(0, 3):
    parts.append(place(o_rail, (cx - (k + 0.5) * STEP, cy, 0)))
parts += [place(o_post, (cx, cy - STEP, 0), math.pi / 2), place(o_glow, (cx, cy - STEP, 0), math.pi / 2)]
parts.append(place(o_rail, (cx, cy - 0.5 * STEP, 0), math.pi / 2))
# a stand-in gumball on the corner (the game adds the real one)
import bpy  # noqa: E402
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(cx, cy, 5.34), segments=32, ring_count=16)
ball = bpy.context.active_object
bpy.ops.object.shade_smooth()
ball.data.materials.append(C.flat_material("GumballStandIn", "#E62D3C", 0.12))
for o in (o_post, o_glow, o_corner, o_rail):
    o.hide_render = True
C.standard_previews("hub_plaza_fence", parts + [ball], block_at=(-12, 3.5, 0), beauty_dir=(0.55, 1.0, 0.42), aim_z=2.6)

# close-up of the three parts side by side
for o in parts + [ball]:
    o.hide_render = True
show = [place(o_post, (-3.2, 0, 0)), place(o_glow, (-3.2, 0, 0)), place(o_corner, (0.5, 0, 0)),
        place(o_rail, (6.5, 0, 0))]
lo, hi = C.world_bounds(show)
C.shoot(os.path.join(C.PREV, "hub_plaza_fence_parts.png"), (lo + hi) / 2, (0.25, 1.0, 0.3),
        C.fit_dist((hi - lo).length / 2, 50, margin=0.95), 50)
print("FENCE done")
