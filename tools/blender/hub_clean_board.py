# CLEAN POP PLAZA 6a: the how-to-play board. A fat soft white frame round a flat cream text face
# (13 x 9, text-free), a thin light line inside the frame, a round bubble-blue badge for the "!"
# and two round feet. One 512 texture set (Hub_CleanBoard_*).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_board.py
#
# Outputs (art/hub_clean/): Hub_CleanBoard.fbx (CleanBoard_Body, CleanBoard_Glow), textures, .blend, .bounds.json

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402

P = K.P
TEX = 512
sc = K.reset()
FZ = 6.5
Z = {
    "frame": K.zone("bd_frame", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.5, 7.0), 0.2, ao=0.3, ao_dist=1.0, grad=0.0),
    "face": K.zone("bd_face", K.PAL["cream"], 0.55, ao=0.25, ao_dist=0.8, grad=0.0),
    "badge": K.zone("bd_badge", K.vgrad(K.PAL["bluedeep"], K.PAL["blue"], 10.0, 12.6), 0.16, ao=0.2, ao_dist=0.6, grad=0.0),
    "badge_face": K.zone("bd_badge_face", K.PAL["blue"], 0.4, ao=0.1, ao_dist=0.4, grad=0.0),
}
GLOW = P.flat_material("CleanBoard_Glow", K.PAL["glow"], 0.3, emit=4.0)
mats = dict(Z, glow=GLOW)
fr = P.frame((0, 0, FZ), (-1, 0, 0), (0, 0, 1))
ring = lambda d: P.rrect2d(6.5 - 0.6, 4.5 - 0.6, d, 5)

body = P.MeshBuilder("CleanBoard_Body")
body.lathe([(0.62, 0.12), (0.62, 0.12, "frame"), (0.68, 0.5), (0.88, 0.64), (1.2, 0.56), (1.4, 0.26), (1.43, -0.05),
            (1.38, -0.42), (1.18, -0.7), (0.9, -0.76), (0.9, -0.76)], ring, fr, zone="face", cap_first=True, cap_last=True)
for sx in (1, -1):
    body.lathe([(1.2, 0.0), (1.28, 0.25), (1.1, 0.6), (0.7, 0.85), (0.55, 1.1), (0.55, 1.7)], lambda d: P.circle2d(d, 10),
               P.frame((sx * 4.8, -0.05, 0)), zone="frame")
BX, BZ_ = 6.9, 11.2
bfr = P.frame((BX, 0.45, BZ_), (-1, 0, 0), (0, 0, 1))
body.lathe([(1.45, -0.35), (1.62, -0.1), (1.6, 0.25), (1.46, 0.45, "badge_face"), (1.3, 0.5), (1.3, 0.5)],
           lambda d: P.circle2d(d, 16), bfr, zone="badge", cap_last=True)
glow = P.MeshBuilder("CleanBoard_Glow")
glow.lathe([(0.63, 0.18), (0.675, 0.46)], ring, fr, zone="glow")

o_body, o_glow = body.build(mats), glow.build(mats, weighted=False)
P.unwrap([o_body], margin=0.012)
P.unwrap([o_glow], margin=0.02)
o_glow.hide_render = True
fin, maps = P.bake_set("Hub_CleanBoard", [o_body], TEX)
o_glow.hide_render = False
print("[Hub_CleanBoard] triangles")
t = P.report([o_body, o_glow], {"CleanBoard_Glow": 200})
print(f"  budget 1500: {'OK' if t < 1500 else 'OVER'}")
K.backface_report("CleanBoard", [o_body, o_glow])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanBoard.fbx"), [o_body, o_glow])
tex = K.tex_names("Hub_CleanBoard")
P.write_bounds(os.path.join(K.OUT, "Hub_CleanBoard.bounds.json"), {
    "CleanBoard_Body": P.bounds_entry(o_body, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                      textFace={"size": [13.0, 9.0], "center": [0, FZ, -0.12], "note": "flat cream face; corners rounded 0.6"},
                                      badgeFace={"size": [2.4, 2.4], "center": [BX, BZ_, -0.95], "note": "flat blue disc for the '!' label"}),
    "CleanBoard_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                      note="thin light line just inside the frame"),
}, notes="CLEAN POP PLAZA how-to-play board. Replaces BoardFrame, Board, BoardLeg x2 and Alert in buildLeft(). Origin on the floor "
         "under the middle of the board; same spot and facing as today: (-46, 0, -20) with the front turned to (0, _, 4). Frame "
         "14.7 x 10.7, top edge 11.8 above the floor (badge top 12.8). Put the SurfaceGui on an invisible 13 x 9 part at "
         "textFace.center and the '!' on a 2.4 x 2.4 part at badgeFace.center.")
K.set_mat(o_glow, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanBoard.blend"), None)
K.studio((0, 0, 6), 12)
P.standard_previews("hub_clean_board", [o_body, o_glow], block_at=(-10.5, 1.0, 0), beauty_dir=(0.45, 1.0, 0.3), lens=60)
print("BOARD done")
