# CLEAN POP PLAZA props 5: the leaderboard stand. A fat white frame round a big flat cream text face
# (10 x 5, text-free), a bubble-blue header plate (flat, for the title text), a little peach crown on
# top and two round feet. About 12 wide x 10 tall. One 512 texture set (Hub_CleanLeaderboard_*).
# Named "Leaderboard" (not Hub_CleanBoard) because art/hub_clean/Hub_CleanBoard is the how-to-play board.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_board.py
#
# Outputs (art/hub_clean_props/): Hub_CleanLeaderboard.fbx (CleanLeaderboard_Body, CleanLeaderboard_Glow)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_cleanprops_common as C  # noqa: E402

K, P = C.K, C.P
TEX = 512
sc = K.reset()
PAL = K.PAL
FZ = 4.6          # middle of the text face
HZ = 8.25         # middle of the header plate
Z = {
    "frame": K.zone("lb_frame", K.vgrad(PAL["grey"], PAL["white"], 0.5, 6.0), 0.2, ao=0.3, ao_dist=1.0, grad=0.0),
    "face": K.zone("lb_face", PAL["cream"], 0.55, ao=0.25, ao_dist=0.8, grad=0.0),
    "head": K.zone("lb_head", K.vgrad(PAL["bluedeep"], PAL["blue"], 7.4, 9.0), 0.18, ao=0.2, ao_dist=0.6, grad=0.0),
    "head_face": K.zone("lb_head_face", PAL["blue"], 0.4, ao=0.1, ao_dist=0.4, grad=0.0),
    "crown": K.zone("lb_crown", "#FFB590", 0.16, ao=0.25, ao_dist=0.5, grad=0.0),
    "pearl": K.zone("lb_pearl", PAL["white"], 0.14, ao=0.15, ao_dist=0.3, grad=0.0),
    "sky": K.zone("lb_sky", PAL["sky"], 0.18, ao=0.2, ao_dist=0.5, grad=0.0),
}
GLOW = P.flat_material("CleanLeaderboard_Glow", K.PAL["glow"], 0.3, emit=4.0)
mats = dict(Z, glow=GLOW)
fr = P.frame((0, 0, FZ), (-1, 0, 0), (0, 0, 1))
ring = lambda d: P.rrect2d(4.4, 1.9, d, 5)

body = P.MeshBuilder("CleanLeaderboard_Body")
body.lathe([(0.62, 0.12), (0.62, 0.12, "frame"), (0.68, 0.5), (0.9, 0.66), (1.3, 0.58), (1.56, 0.26), (1.6, -0.05),
            (1.54, -0.42), (1.3, -0.7), (0.9, -0.76), (0.9, -0.76)], ring, fr, zone="face", cap_first=True, cap_last=True)
for sx in (1, -1):      # legs with round feet and a sky collar
    body.lathe([(1.25, 0.0), (1.33, 0.25), (1.15, 0.6), (0.72, 0.85), (0.55, 1.05, "sky"), (0.72, 1.12), (0.72, 1.4), (0.55, 1.47, "frame"),
                (0.5, 2.0)], lambda d: P.circle2d(d, 10), P.frame((sx * 3.7, -0.05, 0)), zone="frame", cap_first=True)
# header plate: a fat blue pill, proud of the frame, with a flat front
hfr = P.frame((0, 0.35, HZ), (-1, 0, 0), (0, 0, 1))
body.lathe([(0.78, -0.6, "head"), (0.9, -0.45), (0.9, 0.5), (0.78, 0.72), (0.6, 0.8, "head_face"), (0.6, 0.8)],
           lambda d: P.rrect2d(2.6, 0.02, d, 6), hfr, cap_first=True, cap_last=True)
# crown: a solid peach band with five points and white pearls
CZ = 9.0
body.lathe([(1.25, CZ - 0.1), (1.32, CZ + 0.15), (1.4, CZ + 0.45), (1.6, CZ + 0.95), (1.42, CZ + 1.0), (0.0, CZ + 0.9)],
           lambda d: P.circle2d(d, 12), P.frame((0, 0.2, 0)), zone="crown")
for i in range(5):
    a = math.radians(90 + 72 * i)
    px, py = 1.18 * math.cos(a), 0.2 + 1.18 * math.sin(a)
    body.lathe([(0.42, CZ + 0.85), (0.34, CZ + 1.3), (0.0, CZ + 1.75)], lambda d: P.circle2d(d, 6), P.frame((px, py, 0)), zone="crown")
    K.sphere(body, (px, py, CZ + 1.85), 0.32, 6, 4, zone="pearl")
glow = P.MeshBuilder("CleanLeaderboard_Glow")
glow.lathe([(0.63, 0.18), (0.675, 0.46)], ring, fr, zone="glow")

o_body, o_glow = body.build(mats), glow.build(mats, weighted=False)
P.unwrap([o_body], margin=0.012)
P.unwrap([o_glow], margin=0.02)
o_glow.hide_render = True
fin, maps = P.bake_set("Hub_CleanLeaderboard", [o_body], TEX)
o_glow.hide_render = False
print("[Hub_CleanLeaderboard] triangles")
t = P.report([o_body, o_glow])
print(f"  budget 1500: {'OK' if t < 1500 else 'OVER'}")
K.backface_report("CleanLeaderboard", [o_body, o_glow])
P.export_fbx(os.path.join(C.OUT, "Hub_CleanLeaderboard.fbx"), [o_body, o_glow])
tex = K.tex_names("Hub_CleanLeaderboard")
P.write_bounds(os.path.join(C.OUT, "Hub_CleanLeaderboard.bounds.json"), {
    "CleanLeaderboard_Body": P.bounds_entry(
        o_body, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
        textFace={"size": [10.0, 5.0], "center": [0, FZ, -0.12], "note": "flat cream face for the list; corners rounded 0.6"},
        headerFace={"size": [6.0, 1.1], "center": [0, HZ, -1.16], "note": "flat blue front of the header plate, for the title (white text)"}),
    "CleanLeaderboard_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                            note="thin light line just inside the frame"),
}, notes="CLEAN POP PLAZA leaderboard stand. Origin on the floor under the middle; front = +Y here (Roblox -Z after the usual lookAt). "
         "Frame 12 wide x 7 tall (1.1 to 8.1 above the floor), header plate 7 x 1.8 on the top edge, crown top about 11.1. "
         "Put the list SurfaceGui on an invisible 10 x 5 part at textFace.center and the title on a 6 x 1.1 part at headerFace.center. "
         "Suggested spot: hub (-40, 0, -43) turned to face the spawn, or wherever the leaderboard wall placeholder is.")
K.set_mat(o_glow, GLOW)
P.save_blend(os.path.join(C.OUT, "Hub_CleanLeaderboard.blend"), None)
K.studio((0, 0, 5), 11)
P.standard_previews("hub_cleanprops_board", [o_body, o_glow], block_at=(-8.5, 1.0, 0), beauty_dir=(0.4, 1.0, 0.25), lens=60)
print("BOARD done")
