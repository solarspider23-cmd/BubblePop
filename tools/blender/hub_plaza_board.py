# Batch B4: how-to-play board. One 512 texture set (Hub_Board_*).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_plaza_board.py
#
# Board_Body (one mesh, fixed colours): puffy red frame (14.8 x 10.8, top edge 11.9) around a flat cream
# text face (13 x 9, centre 6.5 up), pale pink back, two fat candy-cane posts with round feet and gold
# clips, a red "!" badge with a white rim on the top-left corner, and a mint swirl lollipop tucked behind
# the top-right corner (the hero detail).
# Outputs (art/hub_plaza/): Hub_Board.fbx, Hub_Board_color/_normal/_roughness.png (512), Hub_Board.blend,
# Hub_Board.bounds.json; previews art/previews/hub_plaza_board_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as C  # noqa: E402

TEX = 512
FZ = 6.5                      # face centre height
CA, CB = 6.0, 4.0             # frame core rectangle
POST_X, POST_R = 8.0, 0.6
# seen from the front, +X is the viewer's LEFT: badge top-left, lollipop top-right
LOLLY = (-6.9, -0.1, 13.4)
BADGE = (6.6, 0.5, 12.1)
sc = C.reset()


def frame_height(nb):
    # a soft moulded seam line around the outside middle of the frame
    return nb.mul(nb.smooth(nb.ab(nb.y), 0.09, 0.03), -0.035)


def leg_color(nb):
    lx = nb.sub(nb.ab(nb.x), POST_X)
    s = nb.spiral(lx, nb.y, nb.z, POST_R, n=2, angle_deg=38, sharp=6.0)
    return nb.mixc(C.lin(C.PAL["cream"]), C.lin(C.PAL["red"]), s)


def leg_height(nb):
    lx = nb.sub(nb.ab(nb.x), POST_X)
    return nb.mul(nb.spiral(lx, nb.y, nb.z, POST_R, n=2, angle_deg=38, sharp=3.0), 0.015)


def swirl(nb, sharp=5.0):
    lx, lz = nb.sub(nb.x, LOLLY[0]), nb.sub(nb.z, LOLLY[2])
    a = nb.atan2(lz, lx)
    r = nb.length2(lx, lz)
    t = nb.add(nb.mul(a, 2 / (2 * math.pi)), nb.div(r, 0.55))
    return nb.clamp01(nb.add(nb.mul(nb.sin(nb.mul(t, 2 * math.pi)), sharp), 0.5))


def badge_in(nb):
    """1 on the red face of the badge, 0 on its white rim (painted by radius: a clean edge)."""
    r = nb.length2(nb.sub(nb.x, BADGE[0]), nb.sub(nb.z, BADGE[2]))
    return nb.smooth(r, 1.14, 1.08)


Z = {
    "face": C.zone_material("face", C.PAL["cream"], 0.5, ao=0.3, ao_dist=0.6, grad=0.04, zr=(2, 11)),
    "back": C.zone_material("back", C.PAL["pink"], 0.38, ao=0.25, ao_dist=0.6, grad=0.06, zr=(1, 12)),
    "frame": C.zone_material("frame", C.PAL["red"], 0.2, frame_height, ao=0.22, ao_dist=0.6, grad=0.1, zr=(1, 12)),
    "leg": C.zone_material("leg", leg_color, 0.22, leg_height, ao=0.22, ao_dist=0.5, grad=0.1, zr=(0, 11)),
    "collar": C.zone_material("collar", C.PAL["cream"], 0.3, ao=0.25, ao_dist=0.4, grad=0.06, zr=(0, 11)),
    "gold": C.zone_material("gold", C.PAL["gold"], 0.2, ao=0.2, ao_dist=0.4, grad=0.0),
    "badge": C.zone_material("badge", lambda nb: nb.mixc(C.lin(C.PAL["cream"]), C.lin(C.PAL["red"]), badge_in(nb)),
                             lambda nb: nb.lerp(0.25, 0.3, badge_in(nb)), ao=0.2, ao_dist=0.4, grad=0.0),
    "lolly": C.zone_material("lolly", lambda nb: nb.mixc(C.lin(C.PAL["mint"]), C.lin(C.PAL["cream"]), swirl(nb)),
                             lambda nb: nb.lerp(0.2, 0.14, swirl(nb)),
                             lambda nb: nb.mul(swirl(nb, 2.5), 0.03), ao=0.12, ao_dist=0.5, grad=0.0),
    "stick": C.zone_material("stick", C.PAL["cream"], 0.35, ao=0.2, ao_dist=0.4, grad=0.0),
}

b = C.MeshBuilder("Board_Body")
ring = lambda d: C.rrect2d(CA, CB, d, 4)
fr = C.frame((0, 0, FZ), (-1, 0, 0), (0, 0, 1))   # ring in X-Z, depth along +Y
b.lathe([(0.55, 0.15), (0.66, 0.55), (0.9, 0.75), (1.2, 0.62), (1.4, 0.25), (1.4, -0.25), (1.2, -0.62),
         (0.9, -0.75), (0.66, -0.55), (0.55, -0.15)], ring, fr, zone="frame")
b.lathe([(0.62, 0.25), (0.62, 0.25)], ring, fr, zone="face", cap_first=True)
b.lathe([(0.62, -0.25), (0.62, -0.25)], ring, fr, zone="back", cap_first=True)

c12 = lambda d: C.circle2d(d, 12)
c10 = lambda d: C.circle2d(d, 10)
for sx in (1, -1):
    pf = C.frame((sx * POST_X, 0, 0))
    b.lathe([(0.95, 0.0, "collar"), (0.95, 0.18), (0.78, 0.42), (0.6, 0.5, "leg"), (0.6, 10.0, "collar"),
             (0.72, 10.12), (0.72, 10.42), (0.5, 10.7), (0.0, 10.82)], c12, pf)
    for zc in (3.6, 9.2):  # gold clips holding the frame
        b.lathe([(0.6, zc - 0.25), (0.76, zc - 0.15), (0.76, zc + 0.15), (0.6, zc + 0.25)], c10, pf, zone="gold")

# "!" badge: white rim, flat red face (2 across) for the in-game "!"
bf = C.frame(BADGE, (-1, 0, 0), (0, 0, 1))
b.lathe([(1.5, 0.0, "badge"), (1.5, 0.22), (1.36, 0.42), (1.18, 0.44), (1.08, 0.36),
         (1.02, 0.34)], lambda d: C.circle2d(d, 16), bf, cap_first=True, cap_last=True)

# lollipop behind the top-right corner: puffy swirl disc, stick going back and down, a gold clip
lf = C.frame(LOLLY, (-1, 0, 0), (0, 0, 1))
b.lathe([(1.2, -0.42), (1.5, -0.25), (1.56, 0.0), (1.5, 0.25), (1.2, 0.42)], lambda d: C.circle2d(d, 16), lf,
        zone="lolly", cap_first=True, cap_last=True)
b.tube([(LOLLY[0], LOLLY[1], LOLLY[2]), (-6.7, -1.1, 12.1), (-6.6, -1.1, 11.2), (-6.6, -1.1, 9.0)], 0.21, segs=6,
       zone="stick", caps=True)
b.lathe([(0.21, 9.8), (0.34, 9.88), (0.34, 10.12), (0.21, 10.2)], lambda d: C.circle2d(d, 8),
        C.frame((-6.6, -1.1, 0)), zone="gold")

mats = dict(Z)
ob = b.build(mats)
C.unwrap([ob], margin=0.02)
fin, maps = C.bake_set("Hub_Board", [ob], TEX)
print("[Hub_Board] triangles")
C.report([ob], {"Board_Body": 1500})

C.export_fbx(os.path.join(C.OUT, "Hub_Board.fbx"), [ob])
tex = {"color": "Hub_Board_color.png", "normal": "Hub_Board_normal.png", "roughness": "Hub_Board_roughness.png"}
C.write_bounds(os.path.join(C.OUT, "Hub_Board.bounds.json"), {
    "Board_Body": C.bounds_entry(ob, textures=tex, material="SmoothPlastic (SurfaceAppearance)",
                                 textFace={"size": [13.0, 9.0], "center": [0, FZ, -0.25],
                                           "note": "flat cream face; corners rounded 0.6 (text stays inset)"},
                                 badgeFace={"diameter": 2.0, "center": [BADGE[0], BADGE[2], -(BADGE[1] + 0.34)],
                                            "note": "flat red disc for the '!' text"}),
}, notes="Replaces BoardFrame, Board, BoardLeg x2 and Alert in buildLeft(). Origin on the floor under the middle "
         "of the board; same spot and facing as today: bpos = (-46, 0, -20) with the front turned to (0, _, 4). "
         "Put the existing SurfaceGui on an invisible 13 x 9 x 0.1 part at textFace.center, and the '!' label on a "
         "2 x 2 part at badgeFace.center.")
C.save_blend(os.path.join(C.OUT, "Hub_Board.blend"), None)

C.studio((0, 0, 6), 9)
C.standard_previews("hub_plaza_board", [ob], block_at=(-11.5, 2.0, 0), beauty_dir=(0.5, 1.0, 0.3))
print("BOARD done")
