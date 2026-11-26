# CLEAN POP PLAZA 2: play pad, pad sign and spawn pad. One 512 texture set (Hub_CleanPad_*).
# Same sizes and positions as art/hub_plaza Hub_Pad / Hub_PadSign / Hub_SpawnPad.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_pad.py
#
# Outputs (art/hub_clean/):
#   Hub_CleanPad.fbx       CleanPad_Body (white rim; fixed), CleanPad_Tint (soft top; tinted), CleanPad_Glow (Neon ring)
#   Hub_CleanPadSign.fbx   CleanPadSign_Body (white text face + mast), CleanPadSign_Tint (soft frame)
#   Hub_CleanSpawnPad.fbx  CleanSpawnPad_Body (white disc, blue rim, bubble emblem), CleanSpawnPad_Glow (Neon ring)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
from mathutils import Vector  # noqa: E402

P = K.P
TEX = 512
sc = K.reset()

BASE = "#EDEBEA"   # tint top: a touch under white so the printed bubble mark can be lighter


def bubble_mark(nb, R=2.3, wid=0.34, soft=0.05):
    """A bubble icon: a ring plus a short highlight arc inside it (top left). 0..1 mask in the x-y plane."""
    r = nb.length2(nb.x, nb.y)
    ring = nb.smooth(nb.ab(nb.sub(r, R)), wid / 2 + soft, wid / 2 - soft)
    a = nb.atan2(nb.mul(nb.y, -1.0), nb.x)                     # 0 = towards +X, grows towards -Y (top left seen from the front)
    arc_r = nb.smooth(nb.ab(nb.sub(r, R * 0.62)), wid * 0.42 + soft, wid * 0.42 - soft)
    arc_a = nb.smooth(nb.ab(nb.sub(a, math.radians(48))), math.radians(30), math.radians(24))
    return nb.mx(ring, nb.mul(arc_r, arc_a))


def top_mask(nb):
    return nb.smooth(nb.z, 0.40, 0.448)


Z = {
    "pad_tint": K.zone("pad_tint", lambda nb: nb.mixc(K.lin(BASE), K.lin("#FFFFFF"), nb.mul(bubble_mark(nb), top_mask(nb))),
                       lambda nb: nb.sub(0.3, nb.mul(nb.mul(bubble_mark(nb), top_mask(nb)), 0.14)),
                       lambda nb: nb.mul(nb.mul(bubble_mark(nb, soft=0.1), top_mask(nb)), 0.05),
                       ao=0.12, ao_dist=0.5, grad=0.0),
    "pad_white": K.zone("pad_white", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 0.5), 0.24, ao=0.25, ao_dist=0.5, grad=0.0),
    "pad_groove": K.zone("pad_groove", K.PAL["grey"], 0.4, ao=0.35, ao_dist=0.5, grad=0.0),
    "sign_tint": K.zone("sign_tint", K.PAL["tint"], 0.2, ao=0.12, ao_dist=0.6, grad=0.05, zr=(2.9, 7.1)),
    "sign_face": K.zone("sign_face", K.PAL["white"], 0.5, ao=0.25, ao_dist=0.4, grad=0.0),
    "sign_mast": K.zone("sign_mast", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 2.5), 0.24, ao=0.2, grad=0.0),
}
RIM_R = 4.72


def spawn_color(nb):
    return nb.mixc(K.lin(K.PAL["white"]), K.lin(K.PAL["blue"]), bubble_mark(nb, R=2.6, wid=0.6))


Z["spawn"] = K.zone("spawn", spawn_color,
                    lambda nb: nb.sub(0.34, nb.mul(bubble_mark(nb, R=2.6, wid=0.6), 0.18)),
                    lambda nb: nb.mul(bubble_mark(nb, R=2.6, wid=0.6, soft=0.12), 0.05), ao=0.25, ao_dist=0.5, grad=0.0)
Z["spawn_rim"] = K.zone("spawn_rim", K.vgrad(K.PAL["bluedeep"], K.PAL["blue"], 0.0, 0.3), 0.18, ao=0.15, ao_dist=0.4, grad=0.0)
GLOW = P.flat_material("CleanPad_Glow", K.PAD_GLOWS["Sky"], 0.3, emit=4.0)

# ------------------------------------------------------------------ play pad (13.5 x 10.5 at the floor, 0.6 high)
PA, PB, KC = 4.5, 3.0, 4
ring = lambda d: P.rrect2d(PA, PB, d, KC)
tint = P.MeshBuilder("CleanPad_Tint")
tint.lathe([(1.22, 0.20), (1.20, 0.36), (1.10, 0.43), (0.98, 0.45)], ring, zone="pad_tint", cap_last=True)
body = P.MeshBuilder("CleanPad_Body")
body.lathe([(2.25, 0.0), (2.14, 0.28), (1.97, 0.47), (1.82, 0.52), (1.69, 0.46), (1.64, 0.24),
            (1.18, 0.24, "pad_groove")], ring, zone="pad_white")
glow = P.MeshBuilder("CleanPad_Glow")
glow.lathe([(1.63, 0.26), (1.55, 0.41), (1.31, 0.41), (1.23, 0.26)], ring, zone="glow")

# ------------------------------------------------------------------ pad sign (face 8 x 3, centre 5 up, one mast)
SA, SB, SZ = 3.5, 1.0, 5.0
sring = lambda d: P.rrect2d(SA, SB, d, 4)
sfr = P.frame((0, 0, SZ), (-1, 0, 0), (0, 0, 1))
sign_tint = P.MeshBuilder("CleanPadSign_Tint")
sign_tint.lathe([(0.5, 0.10), (0.62, 0.42), (0.92, 0.4), (1.07, 0.0), (0.92, -0.4), (0.62, -0.42), (0.5, -0.10)], sring, sfr, zone="sign_tint")
sign_body = P.MeshBuilder("CleanPadSign_Body")
for w in (0.16, -0.16):
    sign_body.lathe([(0.62, w), (0.62, w)], sring, sfr, zone="sign_face", cap_first=True)
sign_body.lathe([(1.5, 0.0), (1.46, 0.14), (1.2, 0.3), (0.75, 0.42), (0.5, 0.7), (0.42, 1.3), (0.42, 3.1)],
                lambda d: P.circle2d(d, 10), zone="sign_mast")

# ------------------------------------------------------------------ spawn pad (11 across, 0.37 high)
spawn = P.MeshBuilder("CleanSpawnPad_Body")
spawn.lathe([(5.5, 0.0), (5.3, 0.3), (4.97, 0.37), (4.72, 0.25, "spawn"), (4.56, 0.30)],
            lambda d: P.circle2d(d, 32, turn=math.pi / 2), zone="spawn_rim", cap_last=True)

mats = dict(Z, glow=GLOW)
o_tint, o_body, o_glow = tint.build(mats), body.build(mats), glow.build(mats)
o_stint, o_sbody = sign_tint.build(mats), sign_body.build(mats)
o_spawn = spawn.build(mats)
textured = [o_body, o_tint, o_sbody, o_stint, o_spawn]
P.unwrap(textured, margin=0.02)
P.unwrap([o_glow], margin=0.02)
for o in (o_stint, o_sbody):
    o.location = (40, 0, 0)
o_spawn.location = (-40, 0, 0)
fin, maps = P.bake_set("Hub_CleanPad", textured, TEX)
for o in (o_stint, o_sbody, o_spawn):
    o.location = (0, 0, 0)

print("[Hub_CleanPad] triangles")
t1 = P.report([o_body, o_tint, o_glow], {"CleanPad_Glow": 200})
print(f"  pad total {t1} (budget 600) {'OK' if t1 < 600 else 'OVER'}")
t2 = P.report([o_sbody, o_stint])
print(f"  sign total {t2} (budget 400) {'OK' if t2 < 400 else 'OVER'}")
P.report([o_spawn], {"CleanSpawnPad_Body": 300})
K.backface_report("CleanPad", [o_body, o_tint, o_glow])
K.backface_report("CleanPadSign", [o_sbody, o_stint])

P.export_fbx(os.path.join(K.OUT, "Hub_CleanPad.fbx"), [o_body, o_tint, o_glow])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanPadSign.fbx"), [o_sbody, o_stint])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanSpawnPad.fbx"), [o_spawn])
tex = K.tex_names("Hub_CleanPad")
SA_ = "SmoothPlastic (SurfaceAppearance)"
variants = {n: K.rgb255(h) for n, h in K.PAD_COLOURS}
P.write_bounds(os.path.join(K.OUT, "Hub_CleanPad.bounds.json"), {
    "CleanPad_Body": P.bounds_entry(o_body, textures=tex, tint=None, material=SA_, note="white rim and groove floor; fixed colours"),
    "CleanPad_Tint": P.bounds_entry(o_tint, textures=tex, tint="pad colour (SurfaceAppearance.Color)", material=SA_,
                                    variants=variants, note="walkable top is flat at height 0.45; a lighter bubble mark is printed in the middle"),
    "CleanPad_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", castShadow=False,
                                    variants={n: K.rgb255(K.PAD_GLOWS[n]) for n, _ in K.PAD_COLOURS},
                                    note="flat colour, recoloured per pad (dark saturated version of the pad colour)"),
}, notes="CLEAN POP PLAZA play pad. Replaces PadBase, PadEdge and Pad1..Pad4 in Hub.lua buildPads(). Footprint 13.5 x 10.5 at the "
         "floor, 0.52 high, standing area (tinted top) 11.4 x 8.4 flat at 0.45. Origin at the pad centre on the plaza floor "
         "(pads at x = -21, -7, 7, 21, z = -28), front (+Y) towards the spawn. The invisible 12 x 9 standing part stays.")
P.write_bounds(os.path.join(K.OUT, "Hub_CleanPadSign.bounds.json"), {
    "CleanPadSign_Body": P.bounds_entry(o_sbody, textures=tex, tint=None, material=SA_,
                                        textFace={"size": [8.0, 3.0], "center": [0, 5.0, -0.16], "back": [0, 5.0, 0.16]},
                                        note="white text face front and back, one white mast on a round foot"),
    "CleanPadSign_Tint": P.bounds_entry(o_stint, textures=tex, tint="pad colour", material=SA_, variants=variants),
}, notes="Replaces the floating 'PAD n  0/4' label. Stands on the floor behind the pad: origin at pad centre + (0, 0, +5.9) in "
         "Roblox, facing the spawn like the pad. Put the SurfaceGui on an invisible 8 x 3 part at textFace.center.")
P.write_bounds(os.path.join(K.OUT, "Hub_CleanSpawnPad.bounds.json"), {
    "CleanSpawnPad_Body": P.bounds_entry(o_spawn, textures=tex, tint=None, material=SA_,
                                         note="white disc, bubble-blue rim, blue bubble mark (its highlight is on the front left)"),
}, notes="Replaces SpawnRing and SpawnDisc. 11 across, 0.37 high. Origin on the plaza floor at the spawn point (0, 0, 34).")
K.set_mat(o_glow, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanPad.blend"), None)

# ------------------------------------------------------------------ previews
sky = K.PAD_COLOURS[0][1]
m_sky = P.tinted_copy(fin, sky, "CleanPad_Sky")
for o in (o_tint, o_stint):
    K.set_mat(o, m_sky)
K.studio((0, 0, 1), 8)
o_sbody.location = o_stint.location = (0, -5.9, 0)
o_spawn.hide_render = True
P.standard_previews("hub_clean_pad", [o_body, o_tint, o_glow, o_sbody, o_stint], block_at=(-8.6, 1.5, 0), beauty_dir=(0.55, 1.0, 0.62))
for o in (o_body, o_tint, o_glow, o_sbody, o_stint):
    o.hide_render = True
o_spawn.hide_render = False
P.standard_previews("hub_clean_spawnpad", [o_spawn], block_at=(-7.0, 0.5, 0), beauty_dir=(0.45, 1.0, 0.75))
o_spawn.hide_render = True
objs = []
for i, (name, hx) in enumerate(K.PAD_COLOURS):
    m = P.tinted_copy(fin, hx, "CleanPad_" + name)
    g = P.flat_material("CleanGlow_" + name, K.PAD_GLOWS[name], 0.3, emit=4.0)
    objs += K.copies([o_body, o_tint, o_glow], ((i - 1.5) * 14, 0, 0), {"CleanPad_Tint": m, "CleanPad_Glow": g})
    objs += K.copies([o_sbody, o_stint], ((i - 1.5) * 14, -5.9, 0), {"CleanPadSign_Tint": m})
lo, hi = P.world_bounds(objs)
P.shoot(os.path.join(K.PREV, "hub_clean_pad_colours.png"), (lo + hi) / 2, (0.0, 1.0, 0.6), 92, 50, res=(1280, 720))
print("PAD done")
