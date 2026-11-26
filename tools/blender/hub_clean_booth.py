# CLEAN POP PLAZA 4a: the booth (one model, tinted in game) and its round pad. One 512 texture set.
# A modern kiosk pod: white rounded body, big dark window with a thick soft frame, pastel plinth,
# sill and a fat pillow canopy (hero detail) with a light bar under it and a text-free sign plate.
# Size like Hub.lua's booth at boothScale 1.3: body 11.3 x 8.7, canopy 12.3 x 9.9, 10.4 tall.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_booth.py
#
# Outputs (art/hub_clean/): Hub_CleanBooth.fbx (CleanBooth_Body, CleanBooth_Tint, CleanBooth_Glow),
# Hub_CleanBoothPad.fbx (CleanBoothPad_Body, CleanBoothPad_Glow), Hub_CleanBooth_*.png (512)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
from mathutils import Vector  # noqa: E402

P = K.P
TEX = 512
sc = K.reset()

WY, WZ = 4.35, 4.75          # window: front wall plane, centre height (sill at 3.05)


def window_color(nb):
    # dark slate glass, lighter towards the bottom, with one soft diagonal shine band
    base = nb.mixc(K.lin("#5C74A8"), K.lin(K.PAL["slate"]), nb.smooth(nb.z, 3.0, 6.4))
    band = nb.smooth(nb.ab(nb.sub(nb.add(nb.x, nb.mul(nb.z, 0.9)), 2.6)), 0.75, 0.55)
    return nb.mixc(base, K.lin("#8FA6D6"), nb.mul(band, 0.55))


Z = {
    "white": K.zone("b_white", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.8, 4.5), 0.22, ao=0.3, ao_dist=1.6, grad=0.0),
    "seam": K.zone("b_seam", K.PAL["grey"], 0.45, ao=0.45, ao_dist=0.6, grad=0.0),
    "frame": K.zone("b_frame", K.PAL["white"], 0.18, ao=0.25, ao_dist=0.6, grad=0.0),
    "window": K.zone("b_window", window_color, 0.1, ao=0.35, ao_dist=0.7, grad=0.0),
    "plate": K.zone("b_plate", K.PAL["white"], 0.5, ao=0.15, ao_dist=0.4, grad=0.0),
    "tint": K.zone("b_tint", K.PAL["tint"], 0.2, ao=0.22, ao_dist=1.6, grad=0.05, zr=(0, 9.5)),
    "pad": K.zone("b_pad", K.PAL["white"], 0.4, ao=0.2, ao_dist=0.5, grad=0.0),
    "pad_rim": K.zone("b_pad_rim", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 0.3), 0.22, ao=0.2, ao_dist=0.5, grad=0.0),
}
GLOW = P.flat_material("CleanBooth_Glow", K.PAL["glow"], 0.3, emit=4.0)
mats = dict(Z, glow=GLOW)

# ------------------------------------------------------------------ body (white)
HX, HY, R = 5.65, 4.35, 1.3
bring = lambda d: P.rrect2d(HX - R, HY - R, d, 5)
body = P.MeshBuilder("CleanBooth_Body")
prof = [(R, 0.7), (R, 1.6), (R - 0.1, 1.67, "seam"), (R - 0.1, 1.83), (R, 1.9, "white"), (R, 7.5)]
body.lathe(prof, bring, zone="white")
# window: thick soft frame + dark glass, sitting proud of the front wall
wfr = P.frame((0, WY, WZ), (-1, 0, 0), (0, 0, 1))
wring = lambda d: P.rrect2d(2.8, 0.8, d, 5)
body.lathe([(0.9, 0.07), (0.9, 0.07, "frame"), (0.93, 0.3), (1.08, 0.4), (1.3, 0.36), (1.46, 0.2), (1.52, -0.05)],
           wring, wfr, zone="window", cap_first=True)
# text-free sign plate on the front of the canopy (7.2 x 1.2)
CY, CZ = 0.4, 8.2            # canopy centre (shifted forward), mid height of its edge
pfr = P.frame((0, CY + 4.95, CZ), (-1, 0, 0), (0, 0, 1))
body.lathe([(0.6, -0.3), (0.6, 0.2), (0.52, 0.28), (0.52, 0.28)], lambda d: P.rrect2d(3.0, 0.01, d, 5), pfr,
           zone="plate", cap_last=True)
# little collar on the roof for the glow finial
body.lathe([(1.15, 9.2), (1.05, 9.45), (0.8, 9.56), (0.5, 9.5)], lambda d: P.circle2d(d, 12), P.frame((0, CY, 0)), zone="white")

# ------------------------------------------------------------------ tint: plinth, sill, canopy
tint = P.MeshBuilder("CleanBooth_Tint")
PR = 1.6
tint.lathe(K.pill_profile(PR, 0.0, 0.95, 0.3, 3) + [(R - 0.05, 0.95)], lambda d: P.rrect2d(5.95 - PR, 4.65 - PR, d, 5), zone="tint")
K.rbox(tint, (4.3, 0.8, 0.25), (0, WY + 0.5, 2.9), 0.55, 0.2, zone="tint", k=3, n=2)
CR = 2.6
cring = lambda d: P.rrect2d(6.15 - CR, 4.95 - CR, d, 6)
cprof = [(R - 0.1, 7.4), (CR - 1.0, 7.4)] + K.arc_pts(CR - 0.8, 8.2, 0.8, -80, 80, 6)
cprof += [(CR - 1.5, 9.1), (CR - 2.3, 9.2), (0.2, 9.26)]
tint.lathe(cprof, cring, P.frame((0, CY, 0)), zone="tint", cap_last=True)

# ------------------------------------------------------------------ glow: light bar under the canopy + finial orb
glow = P.MeshBuilder("CleanBooth_Glow")
glow.lathe([(R + 0.04, 6.95), (R + 0.12, 7.15), (R + 0.04, 7.35)], bring, zone="glow")
K.sphere(glow, (0, CY, 9.9), 0.52, 8, 5, zone="glow", a0=25)

# ------------------------------------------------------------------ booth pad (9.1 across, 0.35 high)
pad = P.MeshBuilder("CleanBoothPad_Body")
pad.lathe([(4.55, 0.0), (4.4, 0.26), (4.15, 0.35), (3.9, 0.24, "pad"), (3.42, 0.24), (3.3, 0.33)],
          lambda d: P.circle2d(d, 22), zone="pad_rim", cap_last=True)
pglow = P.MeshBuilder("CleanBoothPad_Glow")
pglow.lathe([(3.84, 0.3), (3.48, 0.3)], lambda d: P.circle2d(d, 24), zone="glow")

o_body, o_tint, o_glow = body.build(mats), tint.build(mats), glow.build(mats, weighted=False)
o_pad, o_pglow = pad.build(mats), pglow.build(mats, weighted=False)
textured = [o_body, o_tint, o_pad]
P.unwrap(textured, margin=0.012)
for o in (o_glow, o_pglow):
    P.unwrap([o], margin=0.02)
o_pad.location = (40, 0, 0)
fin, maps = P.bake_set("Hub_CleanBooth", textured, TEX)
o_pad.location = (0, 0, 0)

print("[Hub_CleanBooth] triangles")
t = P.report([o_body, o_tint, o_glow], {"CleanBooth_Glow": 200})
print(f"  booth budget 4000: {'OK' if t < 4000 else 'OVER'}")
t2 = P.report([o_pad, o_pglow], {"CleanBoothPad_Glow": 200})
print(f"  booth pad budget 300: {'OK' if t2 < 300 else 'OVER'}")
K.backface_report("CleanBooth", [o_body, o_tint, o_glow])

P.export_fbx(os.path.join(K.OUT, "Hub_CleanBooth.fbx"), [o_body, o_tint, o_glow])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanBoothPad.fbx"), [o_pad, o_pglow])
tex = K.tex_names("Hub_CleanBooth")
SA_ = "SmoothPlastic (SurfaceAppearance)"
variants = {n: K.rgb255(h) for n, h in K.BOOTH_COLOURS}
P.write_bounds(os.path.join(K.OUT, "Hub_CleanBooth.bounds.json"), {
    "_tris_total": t,
    "window": {"opening": [7.4, 3.4], "sillHeight": 3.05, "frontFaceZ": -(WY + 0.07)},
    "signFace": {"size": [6.6, 1.0], "center": [0, CZ, -(CY + 4.95 + 0.28)], "normal": [0, 0, -1],
                 "note": "flat white plate on the canopy front for in-game text (SHOP, PASSES ...)"},
    "boothPad": {"position": [0, 0, -9.75], "note": "Hub_CleanBoothPad centre, in front of the window (same as the candy booth)"},
    "CleanBooth_Body": P.bounds_entry(o_body, textures=tex, tint=None, material=SA_, note="white body, window frame, dark window, sign plate"),
    "CleanBooth_Tint": P.bounds_entry(o_tint, textures=tex, tint="booth colour (SurfaceAppearance.Color)", material=SA_,
                                      variants=variants, note="plinth, counter sill, pillow canopy"),
    "CleanBooth_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                      note="light bar under the canopy and the small orb on the roof"),
}, notes="CLEAN POP PLAZA booth. Replaces BoothBody, BoothTrim, BoothWindow, BoothSill, Awning x5, RoofTop, RoofBall in "
         "buildBooths(). One per HubConfig.booths entry (x = 44, z = -15 / 4 / 23), origin on the plaza floor, front (+Y here) "
         "facing the plaza middle. Built at final size (boothScale 1.3 included): plinth 11.9 x 9.3, body 11.3 x 8.7, canopy "
         "12.3 x 9.9 (0.4 further forward), 10.4 tall.")
P.write_bounds(os.path.join(K.OUT, "Hub_CleanBoothPad.bounds.json"), {
    "CleanBoothPad_Body": P.bounds_entry(o_pad, textures=tex, tint=None, material=SA_, note="white disc, flat walkable top at 0.33"),
    "CleanBoothPad_Glow": P.bounds_entry(o_pglow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False),
}, notes="Replaces BoothPadRing and BoothPad. 9.1 across, 0.35 high; centre 9.75 in front of the booth origin.")
for o in (o_glow, o_pglow):
    K.set_mat(o, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanBooth.blend"), None)

# ------------------------------------------------------------------ previews
m0 = P.tinted_copy(fin, K.BOOTH_COLOURS[0][1], "CleanBooth_Sky")
K.set_mat(o_tint, m0)
o_pad.location = o_pglow.location = (0, 9.75, 0)
K.studio((0, 3, 4), 13)
show = [o_body, o_tint, o_glow, o_pad, o_pglow]
P.standard_previews("hub_clean_booth", show, block_at=(-8.5, 6.5, 0), beauty_dir=(0.55, 1.0, 0.36), lens=60)
# a player's view: eye height 5, 15 studs from the window
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_booth_eye.png"), (0, 4, 5.2), (0.35, 1.0, 0.02), 19, 28, res=(1280, 960))
for o in show:
    o.hide_render = True
objs = []
for i, (name, hx) in enumerate(K.BOOTH_COLOURS):
    m = P.tinted_copy(fin, hx, "CleanBooth_" + name)
    objs += K.copies([o_body, o_tint, o_glow], ((1 - i) * 15, 0, 0), {"CleanBooth_Tint": m})
    objs += K.copies([o_pad, o_pglow], ((1 - i) * 15, 9.75, 0))
lo, hi = P.world_bounds(objs)
P.shoot(os.path.join(K.PREV, "hub_clean_booth_colours.png"), (lo + hi) / 2, (0.25, 1.0, 0.4), 78, 50, res=(1280, 720))
print("BOOTH done")
