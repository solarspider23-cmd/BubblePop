# CLEAN POP PLAZA props 1: the back hall. A facade that fills the back edge of the plaza behind the
# centrepiece: two round towers with glossy sky-blue bubble domes and soft glowing arched windows, a
# colonnade with glowing niches between them, and a big empty round medallion up top. No text.
# About 60 wide x 10 deep x 24 tall, front = +Y. One 1024 texture set (Hub_CleanHall_*).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_hall.py
#
# Outputs (art/hub_clean_props/): Hub_CleanHall.fbx (CleanHall_Body, CleanHall_Glow, CleanHall_Shine),
# textures, .blend, .bounds.json

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_cleanprops_common as C  # noqa: E402
import bpy  # noqa: E402

K, P = C.K, C.P
TEX = 1024
sc = K.reset()
PAL = K.PAL
Z = {
    "wall": K.zone("h_wall", K.vgrad(PAL["grey"], PAL["white"], 0.0, 9.0), 0.26, ao=0.35, ao_dist=2.5, grad=0.0),
    "base": K.zone("h_base", PAL["grey"], 0.3, ao=0.3, ao_dist=1.5, grad=0.0),
    "cream": K.zone("h_cream", K.vgrad(PAL["cream"], PAL["white"], 11.0, 20.0), 0.3, ao=0.35, ao_dist=2.5, grad=0.0),
    "frame": K.zone("h_frame", PAL["white"], 0.2, ao=0.3, ao_dist=0.8, grad=0.0),
    "sky": K.zone("h_sky", PAL["sky"], 0.18, ao=0.25, ao_dist=1.0, grad=0.0),
    "dome": K.zone("h_dome", K.vgrad(PAL["blue"], "#6FBFFF", 16.0, 21.5), 0.12, ao=0.25, ao_dist=2.0, grad=0.0),
    "mint": K.zone("h_mint", PAL["mint"], 0.18, ao=0.25, ao_dist=1.0, grad=0.0),
    "lilac": K.zone("h_lilac", PAL["lilac"], 0.18, ao=0.25, ao_dist=1.0, grad=0.0),
    "peach": K.zone("h_peach", PAL["peach"], 0.18, ao=0.25, ao_dist=1.0, grad=0.0),
    "med": K.zone("h_med", K.vgrad("#8CCBFF", "#D4ECFF", 9.5, 22.5), 0.4, ao=0.3, ao_dist=2.0, grad=0.0),
}
GLOW = P.flat_material("CleanHall_Glow", "#7CC4FF", 0.3, emit=2.2)
SHINE = P.flat_material("CleanHall_Shine", "#FFFFFF", 0.3, emit=1.0)
mats = dict(Z, glow=GLOW, shine=SHINE)

body = P.MeshBuilder("CleanHall_Body")
glow = P.MeshBuilder("CleanHall_Glow")
shine = P.MeshBuilder("CleanHall_Shine")

TX, TR = 25.0, 4.5          # tower centre and radius
DOME_Z, DOME_R = 16.6, 4.7
shine_centres = []
for sx in (1, -1):
    c = (sx * TX, 0, 0)
    body.lathe([(5.0, 0.0, "base"), (5.0, 0.0), (5.05, 0.5), (4.9, 1.0), (4.62, 1.3), (4.5, 1.6, "wall"), (TR, 13.6, "sky"),
                (4.95, 13.9), (5.1, 14.4), (4.95, 14.9), (4.45, 15.15, "frame"), (4.3, 15.4), (4.3, 16.1), (4.75, 16.35),
                (4.85, 16.6), (4.85, 16.6)],
               lambda d: P.circle2d(d, 20), P.frame(c), cap_first=True)
    # bubble dome (a touch more than a half ball) and its finial
    K.sphere(body, (sx * TX, 0, DOME_Z), DOME_R, 20, 7, zone="dome", a0=82, a1=180)
    body.lathe([(0.9, 20.9, "frame"), (1.0, 21.2), (0.75, 21.5), (0.5, 21.6)], lambda d: P.circle2d(d, 10), P.frame(c))
    K.sphere(body, (sx * TX, 0, 22.25), 0.85, 10, 6, zone=("mint" if sx > 0 else "peach"))
    K.shine_patch(shine, (sx * TX, 0, DOME_Z), DOME_R + 0.07, math.radians(-30), math.radians(40), 3.4, 1.1)
    # windows: 3 round the front on two floors
    for az in (-42, 0, 42):
        a = math.radians(az)
        for z0, hb, ht in ((4.2, 1.5, 0.9), (9.9, 1.3, 0.7)):
            o = (sx * TX + (TR - 0.12) * math.sin(a), (TR - 0.12) * math.cos(a), z0)
            C.window(body, glow, o, a, 1.05, hb, ht, n=6)

# main wall between the towers, with a base lip
body.lathe([(0.3, 0.0, "base"), (0.3, 0.0), (0.4, 0.5), (0.32, 1.0), (0.1, 1.25, "wall"), (0.05, 1.5), (0.05, 13.0), (0.05, 13.0)],
           lambda d: P.rrect2d(21.5, 2.1, d, 2), P.frame((0, -1.2, 0)), cap_last=True)
# niches: glowing arches in the wall between the columns
for x in (-13, -6.5, 0, 6.5, 13):
    C.window(body, glow, (x, 0.9, 4.6), 0.0, 1.6, 2.6, 1.6, n=8, fat=0.5, depth=0.5)
# colonnade: six fat columns carrying a rounded beam
for x in (-16.25, -9.75, -3.25, 3.25, 9.75, 16.25):
    body.lathe([(1.3, 0.0, "base"), (1.3, 0.0), (1.38, 0.35), (1.25, 0.72), (0.98, 0.95, "frame"), (0.9, 1.3), (0.84, 8.9, "sky"),
                (1.12, 9.1), (1.22, 9.45), (1.12, 9.8), (0.9, 9.95, "frame"), (1.3, 10.3), (1.3, 10.8)],
               lambda d: P.circle2d(d, 10), P.frame((x, 3.3, 0)), cap_first=True)
K.rbox(body, (21.6, 1.75, 1.25), (0, 2.85, 11.9), 0.9, 0.5, zone="frame", k=3, n=3)
K.rbox(body, (21.3, 1.95, 0.32), (0, 2.85, 13.2), 0.9, 0.3, zone="sky", k=3, n=2)
# cream tablet behind the medallion (stepped skyline) with two small shoulders
K.rbox(body, (14.0, 4.2, 1.9), None, 3.6, 0.5, zone="cream", k=5, n=3, fr=P.frame((0, -1.1, 15.6), (-1, 0, 0), (0, 0, 1)))
for sx in (1, -1):
    K.sphere(body, (sx * 17.3, -0.6, 14.9), 1.9, 12, 7, zone=("lilac" if sx > 0 else "sky"), a0=60, a1=180)
    K.sphere(body, (sx * 12.2, 0.9, 19.3), 1.15, 10, 6, zone=("peach" if sx > 0 else "mint"))
# the medallion: fat white ring round an empty soft-blue face
MZ, MR = 15.9, 8.0
mfr = P.frame((0, 0.6, MZ), (-1, 0, 0), (0, 0, 1))
body.lathe([(7.2, -2.2, "frame"), (7.7, -2.0), (MR, -1.5), (MR, 1.0), (7.8, 1.6), (7.3, 1.95), (6.8, 1.95), (6.45, 1.7),
            (6.3, 1.3), (6.3, 1.05, "med"), (6.3, 1.05), (3.2, 1.05), (0.0, 1.05)],
           lambda d: P.circle2d(d, 32), mfr, cap_first=True)
glow.lathe([(6.28, 1.12), (5.95, 1.12)], lambda d: P.circle2d(d, 32), mfr, zone="glow")
# three little bubbles riding the ring
for ang, r, zn in ((38, 1.15, "mint"), (150, 0.9, "peach"), (205, 0.7, "lilac")):
    a = math.radians(ang)
    K.sphere(body, (math.cos(a) * 7.6, 2.3, MZ + math.sin(a) * 7.6), r, 10, 6, zone=zn)

o_body = body.build(mats)
o_glow = glow.build(mats, weighted=False)
o_shine = shine.build(mats, weighted=False)
# glow panes and shines are one-sided: make them face out (+Y side of the building / away from dome centres)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
for ob, ref in ((o_glow, None), (o_shine, None)):
    me = ob.data
    for p in me.polygons:
        if ob is o_glow:
            cx = TX if p.center.x > 20.6 else (-TX if p.center.x < -20.6 else p.center.x)
            outward = Vector((p.center.x - cx, p.center.y - (0 if abs(cx) == TX else -5), 0))
        else:
            cx = TX if p.center.x > 0 else -TX
            outward = p.center - Vector((cx, 0, DOME_Z))
        if p.normal.dot(outward) < 0:
            p.flip()
    me.update()

P.unwrap([o_body], margin=0.006)
P.unwrap([o_glow], margin=0.02)
P.unwrap([o_shine], margin=0.05)
o_glow.hide_render = True
o_shine.hide_render = True
fin, maps = P.bake_set("Hub_CleanHall", [o_body], TEX)
o_glow.hide_render = False
o_shine.hide_render = False
print("[Hub_CleanHall] triangles")
t = P.report([o_body, o_glow, o_shine])
print(f"  budget 8000: {'OK' if t < 8000 else 'OVER'}")
K.backface_report("CleanHall", [o_body, o_glow, o_shine])
P.export_fbx(os.path.join(C.OUT, "Hub_CleanHall.fbx"), [o_body, o_glow, o_shine])
tex = K.tex_names("Hub_CleanHall")
P.write_bounds(os.path.join(C.OUT, "Hub_CleanHall.bounds.json"), {
    "CleanHall_Body": P.bounds_entry(o_body, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                     medallionFace={"diameter": 12.6, "center": [0, MZ, -1.65],
                                                    "note": "flat empty soft-blue disc (for a logo image later, or leave empty)"}),
    "CleanHall_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=[124, 196, 255], castShadow=False,
                                     note="12 tower windows, 5 wall niches and the thin ring inside the medallion. Soft sky glow; "
                                          "if it blows out to white in game use the darker house glow [20, 100, 200]."),
    "CleanHall_Shine": P.bounds_entry(o_shine, textures=None, material="SmoothPlastic (flat white)", color=[255, 255, 255],
                                      castShadow=False, note="white highlight on each dome"),
}, notes="CLEAN POP PLAZA back hall (facade only, no inside). Origin on the floor under the middle. Place at hub (0, 0, -52), front "
         "(+Y here = Roblox -Z after the usual lookAt) facing the spawn: its front-most point is 5.1 in front of the origin "
         "(hub z -46.9), so it stays behind z -46. The centrepiece stage (radius 14 at z -45, 1.5 high) overlaps the middle "
         "columns at floor level; that is intended (the columns rise out of the stage). 60 wide, 10 deep, towers 23 tall, "
         "medallion top 23.9. Collision: one invisible box 60 x 14 x 9 is enough.")
K.set_mat(o_glow, GLOW)
K.set_mat(o_shine, SHINE)
P.save_blend(os.path.join(C.OUT, "Hub_CleanHall.blend"), None)
K.studio((0, 0, 10), 36)
P.standard_previews("hub_cleanprops_hall", [o_body, o_glow, o_shine], block_at=(0, 9.0, 0), beauty_dir=(0.35, 1.0, 0.28), lens=50)
print("HALL done")
