# CLEAN POP PLAZA 1b: the logo banner. A soft white pill with a bubble-blue plaque (flat, text-free
# face for the in-game BUBBLE POP text), a thin glow line in the groove, two pastel bubble studs and
# two arms that plug into the centrepiece's cup. Flat colours, no texture. About 46.4 x 9.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_banner.py
#
# Outputs (art/hub_clean/): Hub_CleanBanner.fbx with CleanBanner_Body (blue plaque), CleanBanner_Trim
# (white rim + arms), CleanBanner_Bubbles (pastel studs), CleanBanner_Glow (Neon line); .blend, .bounds.json

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402

P = K.P
sc = K.reset()
CZ = 4.6            # height of the plaque centre above the model origin
A = 18.7            # half length of the straight part
M = {
    "blue": P.flat_material("CleanBanner_Blue", K.PAL["blue"], 0.22),
    "white": P.flat_material("CleanBanner_White", K.PAL["white"], 0.25),
    "sky": P.flat_material("CleanBanner_Sky", K.PAL["sky"], 0.15),
    "glow": P.flat_material("CleanBanner_Glow", K.PAL["glow"], 0.3, emit=5.0),
}
fr = P.frame((0, 0, CZ), (-1, 0, 0), (0, 0, 1))      # ring in the X-Z plane, depth (w) along +Y
pill = lambda d: P.rrect2d(A, 0.01, d, 7)

trim = P.MeshBuilder("CleanBanner_Trim")
trim.lathe([(4.1, -0.6), (4.4, -0.42), (4.5, -0.1), (4.46, 0.25), (4.28, 0.47), (4.08, 0.45), (3.98, 0.22), (3.76, 0.22)],
           pill, fr, zone="white", cap_first=True)
# two fat arms reaching back into the centrepiece's cup, each with a soft collar on the banner
for sx in (1, -1):
    afr = P.frame((sx * 4.2, -0.5, CZ), (1, 0, 0), (0, 0, -1))   # w = +Y ... built towards -Y below
    trim.lathe([(1.25, 0.0), (1.2, -0.3), (0.95, -0.55), (0.75, -0.8), (0.72, -5.6), (0.0, -5.6)], lambda d: P.circle2d(d, 12), afr, zone="white")

body = P.MeshBuilder("CleanBanner_Body")
body.lathe([(3.74, 0.2), (3.7, 0.5), (3.62, 0.64), (3.5, 0.7), (3.5, 0.7)], pill, fr, zone="blue", cap_last=True)

glow = P.MeshBuilder("CleanBanner_Glow")
glow.lathe([(3.96, 0.27), (3.78, 0.27)], pill, fr, zone="glow")

bub = P.MeshBuilder("CleanBanner_Bubbles")
for sx in (1, -1):
    bfr = P.frame((sx * 20.4, 0.7, CZ), (-1, 0, 0), (0, 0, 1))
    prof = [(1.3 * math.cos(math.radians(a)), 0.75 * math.sin(math.radians(a))) for a in (0, 22, 45, 68)] + [(0.0, 0.75)]
    bub.lathe(prof, lambda d: P.circle2d(d, 16), bfr, zone="sky")

objs = [body.build(M), trim.build(M), bub.build(M), glow.build(M, weighted=False)]
o_body, o_trim, o_bub, o_glow = objs
for o in objs:
    P.unwrap([o], margin=0.02)
print("[Hub_CleanBanner] triangles")
total = P.report(objs, {"CleanBanner_Glow": 200})
print(f"  budget 1500: {'OK' if total < 1500 else 'OVER'}")
K.backface_report("CleanBanner", objs)

P.export_fbx(os.path.join(K.OUT, "Hub_CleanBanner.fbx"), objs)
P.write_bounds(os.path.join(K.OUT, "Hub_CleanBanner.bounds.json"), {
    "_tris_total": total,
    "mount_on_centre": {"origin": [0.0, 12.9, -10.6],
                        "note": "put the banner's origin here, measured from the centrepiece origin, both facing the same way "
                                "(plaque centre ends up 17.5 above the floor); the two arms then reach into the pedestal's cup"},
    "text_face": {"center": [0.0, CZ, -0.7], "size": [37.5, 7.0], "normal": [0, 0, -1],
                  "note": "flat front of CleanBanner_Body; the whole flat area is a 44.4 x 7 pill"},
    "CleanBanner_Body": P.bounds_entry(o_body, material="SmoothPlastic", color=K.rgb255(K.PAL["blue"]), note="bubble-blue plaque, flat text-free face"),
    "CleanBanner_Trim": P.bounds_entry(o_trim, material="SmoothPlastic", color=K.rgb255(K.PAL["white"]), note="white rim and the two mounting arms"),
    "CleanBanner_Bubbles": P.bounds_entry(o_bub, material="SmoothPlastic", color=K.rgb255(K.PAL["sky"]), reflectance=0.3, note="two pastel bubble studs at the ends"),
    "CleanBanner_Glow": P.bounds_entry(o_glow, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False, note="thin light line in the groove round the plaque"),
}, notes="CLEAN POP PLAZA logo banner. Replaces LogoRim, LogoRimEnd x2, LogoEnd x2, Logo, LogoShine in buildGumballMachine(). "
         "46.4 long x 9 high; plaque 44.8 x 7.4 with a flat 44.4 x 7 face. Put the BUBBLE POP SurfaceGui on an invisible "
         "37.5 x 7 part at text_face.center. Flat colours, no textures.")
P.save_blend(os.path.join(K.OUT, "Hub_CleanBanner.blend"), None)

K.studio((0, 0, 4), 22)
P.standard_previews("hub_clean_banner", objs, block_at=(-26, 0.5, 0), beauty_dir=(0.45, 1.0, 0.35), lens=60)
print("BANNER done")
