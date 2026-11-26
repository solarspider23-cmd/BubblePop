# CLEAN POP PLAZA props 2-4: lamp post, park bench and planter. They share ONE 512 texture set
# (Hub_CleanProps_*); each is its own FBX and stands on the origin, front = +Y.
#   Hub_CleanLamp    (CleanLamp_Body, CleanLamp_Glow)                 about 9.2 tall, glowing bubble globe
#   Hub_CleanBench   (CleanBench_Body, CleanBench_Tint)               about 5.2 long, pastel cushions (tint)
#   Hub_CleanPlanter (CleanPlanter_Body, CleanPlanter_Tint, CleanPlanter_Shine)  about 6 wide, bubble bushes (tint)
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_small.py

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_cleanprops_common as C  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

K, P = C.K, C.P
TEX = 512
sc = K.reset()
PAL = K.PAL
Z = {
    "white": K.zone("p_white", K.vgrad(PAL["grey"], PAL["white"], 0.0, 2.5), 0.22, ao=0.3, ao_dist=1.0, grad=0.0),
    "grey": K.zone("p_grey", PAL["grey"], 0.3, ao=0.3, ao_dist=0.8, grad=0.0),
    "sky": K.zone("p_sky", PAL["sky"], 0.18, ao=0.25, ao_dist=0.6, grad=0.0),
    "blue": K.zone("p_blue", PAL["blue"], 0.16, ao=0.25, ao_dist=0.6, grad=0.0),
    "soil": K.zone("p_soil", PAL["stone2"], 0.6, ao=0.5, ao_dist=1.5, grad=0.0),
    "tint": K.zone("p_tint", PAL["tint"], 0.2, ao=0.35, ao_dist=1.6, grad=0.0),
}
GLOW = P.flat_material("CleanLamp_Glow", "#7CC4FF", 0.3, emit=3.0)
SHINE = P.flat_material("CleanPlanter_Shine", "#FFFFFF", 0.3, emit=1.0)
mats = dict(Z, glow=GLOW, shine=SHINE)

# ------------------------------------------------------------------ lamp
GZ, GR = 7.75, 1.2
lamp = P.MeshBuilder("CleanLamp_Body")
lamp.lathe([(1.25, 0.0, "white"), (1.25, 0.0), (1.33, 0.3), (1.2, 0.62), (0.85, 0.85), (0.55, 1.15), (0.38, 1.7), (0.33, 3.0, "sky"),
            (0.55, 3.1), (0.62, 3.35), (0.55, 3.6), (0.32, 3.7, "white"), (0.3, 6.1), (0.5, 6.35), (0.95, 6.6, "sky"), (1.12, 6.85),
            (1.12, 7.0), (0.95, 7.12, "white"), (0.6, 7.05)], lambda d: P.circle2d(d, 12), cap_first=True)
lamp.lathe([(0.62, 8.72, "sky"), (0.62, 8.9), (0.45, 9.05, "white"), (0.3, 9.1), (0.28, 9.3), (0.0, 9.4)], lambda d: P.circle2d(d, 12))
lglow = P.MeshBuilder("CleanLamp_Glow")
K.sphere(lglow, (0, 0, GZ), GR, 18, 10, zone="glow")

# ------------------------------------------------------------------ bench
bench = P.MeshBuilder("CleanBench_Body")
btint = P.MeshBuilder("CleanBench_Tint")
for sx in (1, -1):
    K.rbox(bench, (1.05, 1.2, 0.3), None, 0.6, 0.22, zone="white", k=4, n=3, fr=P.frame((sx * 2.3, 0, 1.2), (0, 1, 0), (0, 0, 1)))
    K.sphere(bench, (sx * 2.3, 0.55, 2.35), 0.42, 8, 5, zone="sky")
bench.tube([(-2.2, 0.35, 0.75), (2.2, 0.35, 0.75)], 0.2, 8, zone="grey")
bench.tube([(-2.2, -0.45, 1.25), (2.2, -0.45, 1.25)], 0.2, 8, zone="grey")
K.rbox(btint, (2.08, 0.95, 0.3), (0, 0.12, 1.6), 0.32, 0.26, zone="tint", k=3, n=3)
m0 = btint.mark()
K.rbox(btint, (2.08, 0.78, 0.26), None, 0.6, 0.22, zone="tint", k=4, n=3, fr=P.frame((0, -0.82, 2.85), (-1, 0, 0), (0, 0, 1)))
piv = Vector((0, -0.82, 2.1))
btint.transform(Matrix.Translation(piv) @ Matrix.Rotation(math.radians(10), 4, "X") @ Matrix.Translation(-piv), m0)

# ------------------------------------------------------------------ planter
plant = P.MeshBuilder("CleanPlanter_Body")
ptint = P.MeshBuilder("CleanPlanter_Tint")
pshine = P.MeshBuilder("CleanPlanter_Shine")
plant.lathe([(1.25, 0.0, "grey"), (1.25, 0.0), (1.32, 0.25), (1.25, 0.5), (1.15, 0.6, "white"), (1.25, 0.8), (1.62, 1.75, "sky"),
             (1.78, 1.85), (1.86, 2.1), (1.78, 2.35), (1.6, 2.45, "white"), (1.4, 2.4), (1.32, 2.2, "soil"), (1.32, 2.2), (0.6, 2.25),
             (0.0, 2.25)], lambda d: P.rrect2d(1.15, 0.12, d, 5), cap_first=True)
BUSH = [((0.25, 0.1, 3.75), 1.75, 14, 8), ((-1.45, -0.05, 3.2), 1.35, 12, 7), ((1.75, 0.0, 3.1), 1.25, 12, 7),
        ((1.0, 0.85, 2.85), 0.9, 8, 5), ((-0.55, 0.9, 2.8), 0.85, 8, 5), ((-0.9, -0.2, 4.75), 0.8, 8, 5)]
for c, r, sg, rg in BUSH:
    K.sphere(ptint, c, r, sg, rg, zone="tint")
K.shine_patch(pshine, BUSH[0][0], BUSH[0][1] + 0.05, math.radians(-30), math.radians(36), 1.4, 0.48)

o_lamp, o_lglow = lamp.build(mats), lglow.build(mats, weighted=False)
o_bench, o_btint = bench.build(mats), btint.build(mats)
o_plant, o_ptint, o_pshine = plant.build(mats), ptint.build(mats), pshine.build(mats, weighted=False)
K.face_out(o_pshine, BUSH[0][0])
MODELS = {
    "Hub_CleanLamp": [o_lamp, o_lglow],
    "Hub_CleanBench": [o_bench, o_btint],
    "Hub_CleanPlanter": [o_plant, o_ptint, o_pshine],
}
textured = [o_lamp, o_bench, o_btint, o_plant, o_ptint]
P.unwrap(textured, margin=0.01)
P.unwrap([o_lglow], margin=0.02)
P.unwrap([o_pshine], margin=0.05)
for i, objs in enumerate(MODELS.values()):      # apart for the bake so each model only shades itself
    for o in objs:
        o.location = (i * 40, 0, 0)
o_lglow.hide_render = o_pshine.hide_render = True
fin, maps = P.bake_set("Hub_CleanProps", textured, TEX)
o_lglow.hide_render = o_pshine.hide_render = False
for objs in MODELS.values():
    for o in objs:
        o.location = (0, 0, 0)
bpy.context.view_layer.update()

tex = K.tex_names("Hub_CleanProps")
tints = {n: K.rgb255(h) for n, h in K.TREE_COLOURS}
SA = "SmoothPlastic (SurfaceAppearance)"
ENT = {
    "CleanLamp_Body": dict(textures=tex, tint=None, material=SA),
    "CleanLamp_Glow": dict(textures=None, material="Neon", color=[124, 196, 255], castShadow=False,
                           globe={"center": [0, GZ, 0], "radius": GR},
                           note="the bubble globe; put a PointLight here (range ~18, soft sky blue). If Neon blows out to white use [20, 100, 200]."),
    "CleanBench_Body": dict(textures=tex, tint=None, material=SA, note="white arm panels with sky knobs, two grey rails"),
    "CleanBench_Tint": dict(textures=tex, tint="cushion colour (SurfaceAppearance.Color)", variants=tints, material=SA,
                            seatTop={"height": 1.9, "note": "top of the seat cushion, for a Seat part 4 x 0.4 x 1.8"}),
    "CleanPlanter_Body": dict(textures=tex, tint=None, material=SA, note="pill-shaped white tub, sky lip, grey foot"),
    "CleanPlanter_Tint": dict(textures=tex, tint="bush colour (SurfaceAppearance.Color)", variants=tints, material=SA),
    "CleanPlanter_Shine": dict(textures=None, material="SmoothPlastic (flat white)", color=[255, 255, 255], castShadow=False),
}
NOTES = {
    "Hub_CleanLamp": "CLEAN POP PLAZA lamp post, 9.4 tall, base 2.7 across. Origin on the floor under the post. Suggested: 8 lamps, "
                     "one each side of every path / at plaza corners, e.g. hub (+-20, 0, -30), (+-44, 0, -44), (+-44, 0, 0), (+-20, 0, 40).",
    "Hub_CleanBench": "CLEAN POP PLAZA bench, 5.2 long x 2.1 deep x 3.6 tall, seat top 1.9. Origin on the floor under the middle; you sit "
                      "facing +Y here (Roblox -Z after the usual lookAt). Suggested: pairs facing the centre along the left and right "
                      "edges, e.g. hub (+-50, 0, 10) and (+-50, 0, 30), with a planter between each pair.",
    "Hub_CleanPlanter": "CLEAN POP PLAZA planter, 6.0 wide x 4.0 deep, bushes up to 5.6. Origin on the floor under the middle; long side "
                        "along X. Tint the bushes per planter (sky / mint / lilac / peach). Suggested: between benches, either side of "
                        "the hall steps, and at the booth row ends.",
}
for name, objs in MODELS.items():
    print(f"[{name}] triangles")
    t = P.report(objs)
    print(f"  budget 1500: {'OK' if t < 1500 else 'OVER'}")
    K.backface_report(name, objs)
    P.export_fbx(os.path.join(C.OUT, name + ".fbx"), objs)
    P.write_bounds(os.path.join(C.OUT, name + ".bounds.json"), {o.name: P.bounds_entry(o, **ENT[o.name]) for o in objs},
                   notes=NOTES[name] + " Textures: the shared Hub_CleanProps_* 512 set (lamp, bench and planter use the same three maps).")
K.set_mat(o_lglow, GLOW)
K.set_mat(o_pshine, SHINE)
P.save_blend(os.path.join(C.OUT, "Hub_CleanProps.blend"), None)

# ------------------------------------------------------------------ previews (one beauty per model, tinted)
K.set_mat(o_btint, P.tinted_copy(fin, K.TREE_COLOURS[0][1], "BenchSky"))
K.set_mat(o_ptint, P.tinted_copy(fin, K.TREE_COLOURS[1][1], "PlanterMint"))
K.studio((0, 0, 3), 9)
everything = [o for objs in MODELS.values() for o in objs]
SHOTS = {"Hub_CleanLamp": ("lamp", (-3.2, 0.5, 0), (0.5, 1.0, 0.22), 70), "Hub_CleanBench": ("bench", (-4.6, 0.5, 0), (0.55, 1.0, 0.4), 60),
         "Hub_CleanPlanter": ("planter", (-5.2, 0.5, 0), (0.5, 1.0, 0.42), 60)}
for name, objs in MODELS.items():
    for o in everything:
        o.hide_render = o not in objs
    tag, block_at, d, lens = SHOTS[name]
    block = P.player_block(block_at)
    lo, hi = P.world_bounds(objs + [block])
    P.shoot(os.path.join(C.PREV, f"hub_cleanprops_{tag}_beauty.png"), (lo + hi) / 2, d, P.fit_dist((hi - lo).length / 2, lens, margin=1.05),
            lens, res=(960, 720))
    bpy.data.objects.remove(block)
print("SMALL done")
