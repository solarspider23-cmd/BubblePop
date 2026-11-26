# CLEAN POP PLAZA 3: fence kit. Clean white posts with a pastel band and a soft glow cap, two rails,
# a taller corner post with a glow orb. One 256 texture set (Hub_CleanFence_*).
# Fence line 55 from the plaza centre, posts every 7.857 (same as art/hub_plaza Hub_Fence).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_fence.py
#
# Outputs (art/hub_clean/): Hub_CleanFence.fbx with CleanFence_Post, CleanFence_PostGlow, CleanFence_Rail,
# CleanFence_Corner, CleanFence_CornerGlow (each stands on the origin; place them separately in game)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402

P = K.P
TEX = 256
STEP = 7.857
sc = K.reset()

Z = {
    "white": K.zone("f_white", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 1.6), 0.22, ao=0.25, ao_dist=0.5, grad=0.0),
    "band": K.zone("f_band", K.PAL["sky"], 0.16, ao=0.2, ao_dist=0.3, grad=0.0),
    "seat": K.zone("f_seat", K.PAL["grey"], 0.4, ao=0.4, ao_dist=0.4, grad=0.0),
    "rail": K.zone("f_rail", K.PAL["white"], 0.24, ao=0.0, grad=0.0),
    "rail2": K.zone("f_rail2", K.PAL["sky"], 0.2, ao=0.0, grad=0.0),
}
GLOW = P.flat_material("CleanFence_Glow", K.PAL["glow"], 0.3, emit=4.0)
mats = dict(Z, glow=GLOW)

post = P.MeshBuilder("CleanFence_Post")
c10 = lambda d: P.circle2d(d, 10)
post.lathe([(0.92, 0.0), (1.0, 0.18), (0.76, 0.46), (0.68, 0.62), (0.68, 2.1),
            (0.8, 2.16, "band"), (0.8, 2.54), (0.68, 2.6, "white"), (0.72, 2.76), (0.84, 2.9), (0.84, 3.02),
            (0.74, 3.1, "seat"), (0.5, 3.1)], c10, zone="white")
pglow = P.MeshBuilder("CleanFence_PostGlow")
pglow.lathe([(0.7, 3.08), (0.7, 3.2), (0.6, 3.38), (0.36, 3.5), (0.0, 3.54)], lambda d: P.circle2d(d, 8), zone="glow")

rail = P.MeshBuilder("CleanFence_Rail")
h = STEP / 2
rail.tube([(-h, 0, 2.38), (h, 0, 2.38)], 0.3, segs=8, zone="rail")
rail.tube([(-h, 0, 1.25), (h, 0, 1.25)], 0.22, segs=6, zone="rail2")

corner = P.MeshBuilder("CleanFence_Corner")
c12 = lambda d: P.circle2d(d, 12)
corner.lathe([(1.26, 0.0), (1.36, 0.18), (1.3, 0.4), (1.04, 0.62), (0.94, 0.85), (0.94, 2.75),
              (1.08, 2.82, "band"), (1.08, 3.3), (0.94, 3.37, "white"), (1.0, 3.6), (1.16, 3.82), (1.16, 3.98),
              (1.02, 4.08, "seat"), (0.6, 4.08)], c12, zone="white")
cglow = P.MeshBuilder("CleanFence_CornerGlow")
K.sphere(cglow, (0, 0, 4.82), 0.95, 12, 7, zone="glow", a0=22)

o_post, o_pglow, o_rail, o_corner, o_cglow = (post.build(mats), pglow.build(mats, weighted=False), rail.build(mats),
                                               corner.build(mats), cglow.build(mats, weighted=False))
textured = [o_post, o_rail, o_corner]
P.unwrap(textured, margin=0.03)
for o in (o_pglow, o_cglow):
    P.unwrap([o], margin=0.02)
o_rail.location = (0, 30, 0)
o_corner.location = (0, -30, 0)
fin, maps = P.bake_set("Hub_CleanFence", textured, TEX)
o_rail.location = o_corner.location = (0, 0, 0)

objs = [o_post, o_pglow, o_rail, o_corner, o_cglow]
print("[Hub_CleanFence] triangles")
P.report(objs, {"CleanFence_Post": 250, "CleanFence_PostGlow": 80, "CleanFence_Rail": 100, "CleanFence_Corner": 350, "CleanFence_CornerGlow": 200})
K.backface_report("CleanFence", [o_post, o_pglow, o_corner, o_cglow])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanFence.fbx"), objs)
tex = K.tex_names("Hub_CleanFence")
SA_ = "SmoothPlastic (SurfaceAppearance)"
P.write_bounds(os.path.join(K.OUT, "Hub_CleanFence.bounds.json"), {
    "CleanFence_Post": P.bounds_entry(o_post, textures=tex, material=SA_, note="white post, sky-blue band, grey seat for the glow cap"),
    "CleanFence_PostGlow": P.bounds_entry(o_pglow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False),
    "CleanFence_Rail": P.bounds_entry(o_rail, textures=tex, material=SA_, castShadow=False,
                                      note="one 7.857 segment along X: white top rail (height 2.38), thinner sky-blue lower rail (1.25); ends hide inside the posts"),
    "CleanFence_Corner": P.bounds_entry(o_corner, textures=tex, material=SA_, note="taller, fatter corner post"),
    "CleanFence_CornerGlow": P.bounds_entry(o_cglow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                            note="glow orb on the corner post (replaces the gumball the candy corner gets in game)"),
}, notes="CLEAN POP PLAZA fence. Replaces Rail x8, Post x60, PostLight x60 in buildPlaza(). Fence line 55 studs from the plaza "
         "centre. Per side: posts at u = k * 7.857 for k = -6..6 (13 CleanFence_Post + CleanFence_PostGlow), corners at "
         "k = +-7 (CleanFence_Corner + CleanFence_CornerGlow), 14 CleanFence_Rail segments centred at u = (k + 0.5) * 7.857, "
         "k = -7..6. All origins on the plaza floor (height 0).")
for o in (o_pglow, o_cglow):
    K.set_mat(o, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanFence.blend"), None)

# ------------------------------------------------------------------ previews: a corner with 3 posts each way
for o in objs:
    o.hide_render = True
run = K.copies([o_corner, o_cglow], (0, 0, 0))
import bpy  # noqa: E402
for k in range(1, 4):
    run += K.copies([o_post, o_pglow], (-k * STEP, 0, 0))
    run += K.copies([o_post, o_pglow], (0, k * STEP, 0))
for k in range(3):
    run += K.copies([o_rail], (-(k + 0.5) * STEP, 0, 0))
    r2 = K.copies([o_rail], (0, (k + 0.5) * STEP, 0))
    r2[0].rotation_euler = (0, 0, math.pi / 2)
    run += r2
bpy.context.view_layer.update()
K.studio((-8, 8, 1), 16)
P.standard_previews("hub_clean_fence", run, block_at=(-6, 5, 0), beauty_dir=(-0.35, 1.0, 0.45), lens=60)
# close-up of one post and the corner
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_fence_parts.png"), (-3.6, 0, 2.3), (-0.25, 1.0, 0.25), 17, 50, res=(1280, 720))
print("FENCE done")
