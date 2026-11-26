# Batch B1 + B2: play pad, pad sign and spawn pad. One 512 texture set (Hub_Pad_*) shared by all three.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_plaza_pad.py
#   (PLAZA_QUICK=1 for fast low-sample test renders)
#
# Outputs (art/hub_plaza/):
#   Hub_Pad.fbx       Pad_Body (white rim, gold studs; fixed), Pad_Tint (cushion top; tinted),
#                     Pad_Glow (ring in the groove; Neon, recoloured)
#   Hub_PadSign.fbx   PadSign_Body (cream text face, legs, gold collars), PadSign_Tint (puffy frame)
#   Hub_SpawnPad.fbx  SpawnPad_Body (red rim, white disc, embossed gold star)
#   Hub_Pad_color.png / _normal.png / _roughness.png (512), Hub_Pad.blend, *.bounds.json
#   previews: art/previews/hub_plaza_pad_*.png, hub_plaza_padsign_*.png, hub_plaza_spawnpad_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

TEX = 512
sc = C.reset()

# ------------------------------------------------------------------ zone materials
def tint_top_height(nb):
    # bubble-wrap domes embossed on the walkable top only
    top = nb.smooth(nb.z, 0.40, 0.448)
    d = nb.hexdomes(nb.x, nb.y, 1.1, 0.42)
    return nb.mul(nb.mul(d, top), 0.035)


def tint_top_color(nb):
    top = nb.smooth(nb.z, 0.40, 0.448)
    d = nb.hexdomes(nb.x, nb.y, 1.1, 0.42)
    lift = nb.add(1.0, nb.mul(nb.mul(d, top), 0.035))
    return nb.scalec(C.lin(C.PAL["tint"]), lift)


def tint_top_rough(nb):
    top = nb.smooth(nb.z, 0.40, 0.448)
    d = nb.hexdomes(nb.x, nb.y, 1.1, 0.42)
    return nb.sub(0.26, nb.mul(nb.mul(d, top), 0.10))


STAR_R, STAR_RI = 2.9, 1.3


def star_mask(nb, soft=0.10):
    """Straight-edged five-point star (one point towards +Y), soft edge."""
    r = nb.length2(nb.x, nb.y)
    a = nb.atan2(nb.x, nb.y)  # angle from +Y
    u = nb.sub(nb.fract(nb.add(nb.div(a, 2 * math.pi / 5), 0.5)), 0.5)
    phi = nb.mul(nb.ab(u), 2 * math.pi / 5)  # 0 at a tip .. 36 deg at an inner corner
    ex = STAR_RI * math.cos(math.pi / 5) - STAR_R
    ey = STAR_RI * math.sin(math.pi / 5)
    den = nb.sub(nb.mul(nb.cos(phi), ey), nb.mul(nb.sin(phi), ex))
    rs = nb.div(STAR_R * ey, den)
    return nb.smooth(nb.sub(rs, r), -soft, soft)


RIM_R = 4.76  # red rim outside this radius, white disc inside (painted by radius: a clean edge)


def spawn_color(nb):
    r = nb.length2(nb.x, nb.y)
    s = star_mask(nb, 0.06)
    disc = nb.mixc(C.lin(C.PAL["cream"]), C.lin(C.PAL["gold"]), s)
    return nb.mixc(C.lin(C.PAL["red"]), disc, nb.smooth(r, RIM_R + 0.04, RIM_R - 0.04))


def spawn_height(nb):
    return nb.mul(star_mask(nb, 0.16), 0.06)


def spawn_rough(nb):
    r = nb.length2(nb.x, nb.y)
    inner = nb.lerp(0.32, 0.2, star_mask(nb, 0.06))
    return nb.lerp(0.22, inner, nb.smooth(r, RIM_R + 0.04, RIM_R - 0.04))


Z = {
    "pad_tint": C.zone_material("pad_tint", tint_top_color, tint_top_rough, tint_top_height, ao=0.12, ao_dist=0.5, grad=0.04, zr=(0, 0.5)),
    "pad_white": C.zone_material("pad_white", C.PAL["cream"], 0.28, ao=0.25, ao_dist=0.5, grad=0.08, zr=(0, 0.55)),
    "pad_groove": C.zone_material("pad_groove", C.PAL["cream"], 0.4, ao=0.35, ao_dist=0.5, grad=0.0),
    "pad_gold": C.zone_material("pad_gold", C.PAL["gold"], 0.2, ao=0.15, grad=0.0),
    "sign_tint": C.zone_material("sign_tint", C.PAL["tint"], 0.22, ao=0.12, ao_dist=0.6, grad=0.05, zr=(2.9, 7.1)),
    "sign_face": C.zone_material("sign_face", C.PAL["cream"], 0.5, ao=0.25, ao_dist=0.4, grad=0.03, zr=(3.5, 6.5)),
    "sign_leg": C.zone_material("sign_leg", C.PAL["cream"], 0.28, ao=0.2, grad=0.08, zr=(0, 3)),
    "spawn": C.zone_material("spawn", spawn_color, spawn_rough, spawn_height, ao=0.25, ao_dist=0.5, grad=0.05, zr=(0, 0.4)),
}
GLOW = C.flat_material("Pad_Glow", C.PAD_GLOWS["Red"], 0.3, emit=4.0)

# ------------------------------------------------------------------ play pad (13.4 x 10.4, 0.6 high)
PA, PB, K = 4.5, 3.0, 4          # core rectangle; outer offset 2.25 -> 13.5 x 10.5 at the floor
ring = lambda d: C.rrect2d(PA, PB, d, K)

tint = C.MeshBuilder("Pad_Tint")
tint.lathe([(1.22, 0.20), (1.20, 0.36), (1.10, 0.43), (0.98, 0.45)], ring, zone="pad_tint", cap_last=True)

body = C.MeshBuilder("Pad_Body")
body.lathe([(2.25, 0.0), (2.12, 0.30), (1.97, 0.47), (1.82, 0.52), (1.69, 0.46), (1.64, 0.24),
            (1.18, 0.24, "pad_groove")], ring, zone="pad_white")
# four gold corner studs on the rim (rivets pressed into the moulding)
for sx in (1, -1):
    for sy in (1, -1):
        c = Vector((sx * (PA + 1.84 * math.cos(math.pi / 4)), sy * (PB + 1.84 * math.sin(math.pi / 4)), 0))
        body.lathe([(0.3, 0.40), (0.28, 0.52), (0.0, 0.6)], lambda d: C.circle2d(d, 6),
                   C.frame(c), zone="pad_gold", cap_first=True)

glow = C.MeshBuilder("Pad_Glow")
glow.lathe([(1.63, 0.26), (1.55, 0.41), (1.31, 0.41), (1.23, 0.26)], ring, zone="glow")

# ------------------------------------------------------------------ pad sign (face 8 x 3, centre 5 up)
SA, SB, SZ = 3.5, 1.0, 5.0
sring = lambda d: C.rrect2d(SA, SB, d, 4)
sfr = C.frame((0, 0, SZ), (-1, 0, 0), (0, 0, 1))   # ring in the X-Z plane, depth along +Y
sign_tint = C.MeshBuilder("PadSign_Tint")
sign_tint.lathe([(0.5, 0.08), (0.64, 0.40), (0.94, 0.36), (1.07, 0.0), (0.94, -0.36),
                 (0.64, -0.40), (0.5, -0.08)], sring, sfr, zone="sign_tint")
sign_body = C.MeshBuilder("PadSign_Body")
for w in (0.16, -0.16):  # the flat text faces, front and back (edges tucked inside the frame)
    sign_body.lathe([(0.62, w), (0.62, w)], sring, sfr, zone="sign_face", cap_first=True)
for sx in (1, -1):
    f = C.frame((sx * 2.9, 0, 0))
    sign_body.lathe([(0.48, 0.0), (0.42, 0.22), (0.3, 0.3), (0.3, 3.2)], lambda d: C.circle2d(d, 6), f, zone="sign_leg")
    sign_body.lathe([(0.3, 2.55), (0.43, 2.68), (0.36, 2.98)], lambda d: C.circle2d(d, 6), f, zone="pad_gold")

# ------------------------------------------------------------------ spawn pad (11 across, 0.38 high)
spawn = C.MeshBuilder("SpawnPad_Body")
spawn.lathe([(5.5, 0.0), (5.27, 0.33), (4.97, 0.37), (4.72, 0.25), (4.56, 0.30)],
            lambda d: C.circle2d(d, 32, turn=math.pi / 2), zone="spawn", cap_last=True)

# ------------------------------------------------------------------ objects, UVs, bake
mats = dict(Z, glow=GLOW)
o_tint, o_body, o_glow = tint.build(mats), body.build(mats), glow.build(mats)
o_stint, o_sbody = sign_tint.build(mats), sign_body.build(mats)
o_spawn = spawn.build(mats)
textured = [o_body, o_tint, o_sbody, o_stint, o_spawn]
budget = {"Pad_Body": 600, "Pad_Tint": 600, "Pad_Glow": 200, "PadSign_Body": 400, "PadSign_Tint": 400, "SpawnPad_Body": 300}

C.unwrap(textured, margin=0.02)
C.unwrap([o_glow], margin=0.02)
# the glow is flat Neon; its UVs are unused. Move pieces apart so AO only sees its own model.
for o in (o_stint, o_sbody):
    o.location = (40, 0, 0)
o_spawn.location = (-40, 0, 0)
fin, maps = C.bake_set("Hub_Pad", textured, TEX)
for o in (o_stint, o_sbody, o_spawn):
    o.location = (0, 0, 0)

print("[Hub_Pad] triangles")
C.report([o_body, o_tint, o_glow], budget)
pad_total = C.tris(o_body) + C.tris(o_tint) + C.tris(o_glow)
print(f"  pad total {pad_total} (budget 600) {'OK' if pad_total < 600 else 'OVER'}")
C.report([o_sbody, o_stint], budget)
sign_total = C.tris(o_sbody) + C.tris(o_stint)
print(f"  sign total {sign_total} (budget 400) {'OK' if sign_total < 400 else 'OVER'}")
C.report([o_spawn], budget)

# ------------------------------------------------------------------ export
C.export_fbx(os.path.join(C.OUT, "Hub_Pad.fbx"), [o_body, o_tint, o_glow])
C.export_fbx(os.path.join(C.OUT, "Hub_PadSign.fbx"), [o_sbody, o_stint])
C.export_fbx(os.path.join(C.OUT, "Hub_SpawnPad.fbx"), [o_spawn])
tex = {"color": "Hub_Pad_color.png", "normal": "Hub_Pad_normal.png", "roughness": "Hub_Pad_roughness.png"}
C.write_bounds(os.path.join(C.OUT, "Hub_Pad.bounds.json"), {
    "Pad_Body": C.bounds_entry(o_body, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                               color=C.rgb255(C.PAL["cream"]), note="white rim, groove floor, gold studs; fixed colours"),
    "Pad_Tint": C.bounds_entry(o_tint, textures=tex, tint="pad colour (SurfaceAppearance.Color)",
                               material="SmoothPlastic (SurfaceAppearance)",
                               variants={n: C.rgb255(h) for n, h in C.PAD_COLOURS}, note="walkable top is flat at height 0.45"),
    "Pad_Glow": C.bounds_entry(o_glow, textures=None, material="Neon", castShadow=False,
                               variants={n: C.rgb255(C.PAD_GLOWS[n]) for n, _ in C.PAD_COLOURS},
                               note="flat colour, recoloured per pad (dark saturated version of the pad colour)"),
}, notes="Replaces PadBase, PadEdge and Pad1..Pad4 in Hub.lua buildPads(). Footprint 13.5 x 10.5 at the floor, "
         "0.6 high (studs), standing area (tinted top) 11.4 x 8.4 flat at 0.45. Place the origin at the pad centre "
         "on the plaza floor (pads at x = -21, -7, 7, 21, z = -28), front (+Y) towards the spawn. "
         "The invisible 12 x 9 standing part in code stays as it is.")
C.write_bounds(os.path.join(C.OUT, "Hub_PadSign.bounds.json"), {
    "PadSign_Body": C.bounds_entry(o_sbody, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                   textFace={"size": [8.0, 3.0], "center": [0, 5.0, -0.16], "back": [0, 5.0, 0.16]},
                                   note="cream text face front and back, white legs, gold collars"),
    "PadSign_Tint": C.bounds_entry(o_sbody if False else o_stint, textures=tex, tint="pad colour",
                                   material="SmoothPlastic (SurfaceAppearance)",
                                   variants={n: C.rgb255(h) for n, h in C.PAD_COLOURS}),
}, notes="Replaces the floating 'PAD n  0/4' label. Stands on the floor just behind the pad: origin at pad centre + "
         "(0, 0, +5.9) in Roblox (5.9 studs behind the pad centre, away from the spawn), facing the spawn like the pad. "
         "Put the SurfaceGui on an invisible 8 x 3 part at textFace.center (front face 0.16 in front of the sign's middle).")
C.write_bounds(os.path.join(C.OUT, "Hub_SpawnPad.bounds.json"), {
    "SpawnPad_Body": C.bounds_entry(o_spawn, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                    note="red rim, white disc, embossed gold star (one point towards +Y = front)"),
}, notes="Replaces SpawnRing and SpawnDisc. 11 across, 0.38 high. Origin on the plaza floor at the spawn point (0, 0, 34); "
         "turn it so the star points at the pads (front = -Z after lookAt towards the pads).")

o_glow.data.materials.clear()
o_glow.data.materials.append(GLOW)
C.save_blend(os.path.join(C.OUT, "Hub_Pad.blend"), None)

# ------------------------------------------------------------------ previews
red = C.PAD_COLOURS[0][1]
tint_red = C.tinted_copy(fin, red, "Pad_Red")
for o in (o_tint, o_stint):
    o.data.materials.clear()
    o.data.materials.append(tint_red)
C.studio((0, 0, 1), 8)

# pad with its sign behind it (as in game)
o_sbody.location = o_stint.location = (0, -5.9, 0)
o_spawn.hide_render = True
C.standard_previews("hub_plaza_pad", [o_body, o_tint, o_glow, o_sbody, o_stint], block_at=(-8.6, 1.5, 0),
                    beauty_dir=(0.55, 1.0, 0.62))

# sign alone
for o in (o_body, o_tint, o_glow):
    o.hide_render = True
o_sbody.location = o_stint.location = (0, 0, 0)
C.standard_previews("hub_plaza_padsign", [o_sbody, o_stint], block_at=(-6.2, 0.8, 0), beauty_dir=(0.5, 1.0, 0.3))
for o in (o_sbody, o_stint):
    o.hide_render = True

# spawn pad
o_spawn.hide_render = False
C.standard_previews("hub_plaza_spawnpad", [o_spawn], block_at=(-7.0, 0.5, 0), beauty_dir=(0.45, 1.0, 0.75))

# colour variants: the four pads in a row with their signs
o_spawn.hide_render = True
objs = []
for i, (name, hx) in enumerate(C.PAD_COLOURS):
    x = (i - 1.5) * 14
    m = C.tinted_copy(fin, hx, "Pad_" + name)
    g = C.flat_material("Glow_" + name, C.PAD_GLOWS[name], 0.3, emit=4.0)
    for src, mat, dy in ((o_body, None, 0), (o_tint, m, 0), (o_glow, g, 0), (o_sbody, None, -5.9), (o_stint, m, -5.9)):
        ob = src.copy()
        ob.data = src.data.copy()
        if mat:
            ob.data.materials.clear()
            ob.data.materials.append(mat)
        ob.location = (x, dy, 0)
        ob.hide_render = False
        sc.collection.objects.link(ob)
        objs.append(ob)
lo, hi = C.world_bounds(objs)
cen = (lo + hi) / 2
C.shoot(os.path.join(C.PREV, "hub_plaza_pad_colours.png"), cen, (0.0, 1.0, 0.6), 72, 50, res=(1280, 720))
print("PAD done")
