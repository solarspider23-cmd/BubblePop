# CLEAN POP PLAZA 5b: bubble trees (replace the lollipop trees). Pastel bubbles on a white stem with
# a round planter foot. Three shapes, each about 15 tall with an 8-wide head; heads are tinted in game.
# One 512 texture set (Hub_CleanTree_*).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_tree.py
#
# Outputs (art/hub_clean/): Hub_CleanTree.fbx with CleanTree_Ball_*, CleanTree_Stack_*, CleanTree_Cloud_*
# (each: _Tint head, _Body stem, _Shine highlight); every model stands on the origin.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
import bpy  # noqa: E402

P = K.P
TEX = 512
sc = K.reset()

Z = {
    "tint": K.zone("t_tint", K.PAL["tint"], 0.16, ao=0.3, ao_dist=3.0, grad=0.07, zr=(6.0, 15.0)),
    "stem": K.zone("t_stem", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 5.0), 0.24, ao=0.3, ao_dist=1.5, grad=0.0),
    "band": K.zone("t_band", K.PAL["sky"], 0.18, ao=0.2, ao_dist=0.5, grad=0.0),
}
SHINE = P.flat_material("CleanTree_Shine", "#FFFFFF", 0.3, emit=1.0)
mats = dict(Z, shine=SHINE)
SHAPES = {   # head bubbles: (centre, radius, segs, rings); the first is the one the stem holds
    "Ball": [((0, 0, 11.0), 4.0, 18, 11)],
    "Stack": [((0, 0, 9.0), 3.4, 16, 9), ((0, 0, 12.25), 2.4, 12, 7), ((0, 0, 14.25), 1.45, 10, 6)],
    "Cloud": [((0, 0, 10.6), 3.3, 14, 8), ((-2.7, 0.3, 9.3), 2.3, 10, 6), ((2.8, -0.2, 9.6), 2.0, 10, 6), ((0.7, 0.2, 13.4), 1.9, 10, 5)],
}
STEM_TOP = {"Ball": 7.6, "Stack": 6.2, "Cloud": 7.9}

models, textured, order = {}, [], []
for name, balls in SHAPES.items():
    head = P.MeshBuilder(f"CleanTree_{name}_Tint")
    for c, r, sg, rg in balls:
        K.sphere(head, c, r, sg, rg, zone="tint")
    stem = P.MeshBuilder(f"CleanTree_{name}_Body")
    top = STEM_TOP[name]
    stem.lathe([(1.9, 0.0), (2.05, 0.3), (1.9, 0.68), (1.25, 0.95), (0.9, 1.6), (0.72, top - 0.8),
                (1.1, top - 0.65, "band"), (1.15, top - 0.3), (1.0, top + 0.2)], lambda d: P.circle2d(d, 10), zone="stem")
    shine = P.MeshBuilder(f"CleanTree_{name}_Shine")
    c, r = balls[0][0], balls[0][1]
    K.shine_patch(shine, c, r + 0.06, math.radians(-32), math.radians(38), r * 0.85, r * 0.3)
    o_h, o_s, o_sh = head.build(mats), stem.build(mats), shine.build(mats, weighted=False)
    K.face_out(o_sh, c)
    models[name] = [o_h, o_s, o_sh]
    textured += [o_h, o_s]
    order += [o_h, o_s, o_sh]

P.unwrap(textured, margin=0.012)
for n in models:
    P.unwrap([models[n][2]], margin=0.05)
for i, n in enumerate(models):          # apart for the bake so each model only shades itself
    for o in models[n]:
        o.location = (i * 40, 0, 0)
fin, maps = P.bake_set("Hub_CleanTree", textured, TEX)
for o in order:
    o.location = (0, 0, 0)

print("[Hub_CleanTree] triangles")
entries = {}
tex = K.tex_names("Hub_CleanTree")
variants = {n: K.rgb255(h) for n, h in K.TREE_COLOURS}
for n, (o_h, o_s, o_sh) in models.items():
    t = P.report([o_h, o_s, o_sh])
    print(f"  {n} budget 700: {'OK' if t < 700 else 'OVER'}")
    entries[o_h.name] = P.bounds_entry(o_h, textures=tex, tint="tree colour (SurfaceAppearance.Color)", variants=variants,
                                       material="SmoothPlastic (SurfaceAppearance)")
    entries[o_s.name] = P.bounds_entry(o_s, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                       note="white stem, round planter foot, sky-blue collar")
    entries[o_sh.name] = P.bounds_entry(o_sh, textures=None, material="SmoothPlastic (flat white)", color=[255, 255, 255], castShadow=False)
    K.backface_report("CleanTree_" + n, [o_h, o_s, o_sh])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanTree.fbx"), order)
P.write_bounds(os.path.join(K.OUT, "Hub_CleanTree.bounds.json"), entries,
               notes="CLEAN POP PLAZA bubble trees. Replace LollyStick, Lolly, LollySwirl, LollyMiddle in Hub.lua lollipop() "
                     "(26 copies). Three models (Ball, Stack, Cloud); each = its _Tint, _Body and _Shine MeshParts, standing on the "
                     "origin (base = the grass point), about 15 tall, head 8 wide (Cloud 10). Scale all three parts together "
                     "(0.8 - 1.4) as today. The shine faces front-left (+Y here).")
P.save_blend(os.path.join(K.OUT, "Hub_CleanTree.blend"), None)

# ------------------------------------------------------------------ previews
cols = [K.TREE_COLOURS[0][1], K.TREE_COLOURS[1][1], K.TREE_COLOURS[2][1]]
for i, n in enumerate(models):
    o_h, o_s, o_sh = models[n]
    K.set_mat(o_h, P.tinted_copy(fin, cols[i], "CleanTree_" + n))
    for o in models[n]:
        o.location = ((i - 1) * 12, 0, 0)
bpy.context.view_layer.update()
K.studio((0, 0, 7), 16)
P.standard_previews("hub_clean_tree", order, block_at=(-19.5, 2, 0), beauty_dir=(0.4, 1.0, 0.3), lens=60)
for o in order:
    o.hide_render = True
objs = []
for j, (cn, hx) in enumerate(K.TREE_COLOURS):
    m = P.tinted_copy(fin, hx, "CleanTreeC_" + cn)
    n = list(models)[j % 3]
    src = models[n]
    for o in src:
        o.location = (0, 0, 0)
    objs += K.copies(src, ((j - 2) * 11, 0, 0), {src[0].name: m})
lo, hi = P.world_bounds(objs)
P.shoot(os.path.join(K.PREV, "hub_clean_tree_colours.png"), (lo + hi) / 2, (0.15, 1.0, 0.25), 82, 50, res=(1280, 720))
print("TREE done")
