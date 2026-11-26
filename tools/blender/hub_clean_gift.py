# CLEAN POP PLAZA 4b: the gift box (replaces the free-gift chest). A soft cream present with a
# bubble-blue satin ribbon and a fat bow (hero detail); the lid is a separate mesh so it can open.
# 6.0 x 4.4 footprint, 5.75 tall (the chest was 6 x 4 x 5.8). One 512 texture set.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_gift.py
#
# Outputs (art/hub_clean/): Hub_CleanGift.fbx (CleanGift_Body, CleanGift_Lid, CleanGift_Glow), Hub_CleanGift_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

P = K.P
TEX = 512
sc = K.reset()
RW = 0.55   # half width of the ribbon


def ribbon(nb, soft=0.03):
    return nb.mx(nb.smooth(nb.ab(nb.x), RW + soft, RW - soft), nb.smooth(nb.ab(nb.y), RW + soft, RW - soft))


def paper_color(lo, hi, z0, z1):
    def fn(nb):
        paper = nb.mixc(K.lin(lo), K.lin(hi), nb.smooth(nb.z, z0, z1))
        satin = nb.mixc(K.lin(K.PAL["bluedeep"]), K.lin(K.PAL["blue"]), nb.smooth(nb.z, 0.0, 4.0))
        return nb.mixc(paper, satin, ribbon(nb))
    return fn


paper_rough = lambda nb: nb.lerp(0.5, 0.24, ribbon(nb))
paper_height = lambda nb: nb.mul(ribbon(nb, 0.07), 0.05)
Z = {
    "box": K.zone("g_box", paper_color("#F1E6D6", K.PAL["cream"], 0.0, 2.6), paper_rough, paper_height, ao=0.3, ao_dist=0.8, grad=0.0),
    "lid": K.zone("g_lid", paper_color(K.PAL["cream"], K.PAL["white"], 2.9, 4.0), paper_rough, paper_height, ao=0.3, ao_dist=0.8, grad=0.0),
    "inside": K.zone("g_inside", K.PAL["sky"], 0.45, ao=0.4, ao_dist=1.5, grad=0.0),
    "under": K.zone("g_under", K.PAL["cream"], 0.5, ao=0.3, ao_dist=1.0, grad=0.0),
    "bow": K.zone("g_bow", K.vgrad(K.PAL["bluedeep"], K.PAL["blue"], 3.9, 5.3), 0.24, ao=0.35, ao_dist=0.8, grad=0.0),
}
GLOW = P.flat_material("CleanGift_Glow", K.PAL["glow"], 0.3, emit=3.0)
mats = dict(Z, glow=GLOW)

# ------------------------------------------------------------------ box (5.6 x 4.0, 3.2 high, open top with an inside)
BR_ = 0.6
bring = lambda d: P.rrect2d(2.8 - BR_, 2.0 - BR_, d, 4)
body = P.MeshBuilder("CleanGift_Body")
prof = K.arc_pts(BR_ - 0.22, 0.22, 0.22, -90, 0, 3) + [(BR_, 3.05), (BR_ - 0.08, 3.2), (BR_ - 0.3, 3.2, "inside"),
                                                        (BR_ - 0.36, 3.1), (BR_ - 0.36, 1.4), (BR_ - 0.36, 1.4)]
body.lathe(prof, bring, zone="box", cap_last=True)

# ------------------------------------------------------------------ lid (6.0 x 4.4, 2.85 .. 4.0) with the bow
LR = 0.8
lring = lambda d: P.rrect2d(3.0 - LR, 2.2 - LR, d, 4)
lid = P.MeshBuilder("CleanGift_Lid")
lprof = [(LR - 0.32, 3.3, "under"), (LR - 0.32, 2.85), (LR - 0.08, 2.85, "lid"), (LR, 2.95)]
lprof += K.arc_pts(LR - 0.28, 3.72, 0.28, 0, 90, 3)
lid.lathe(lprof, lring, zone="under", cap_first=True, cap_last=True)


def loop(mb, side):
    """One bow loop: a fat flattened ring standing on the lid, leaning outwards."""
    mk = mb.mark()
    K.torus(mb, None, 0.66, 0.33, 18, 8, zone="bow", fr=P.frame((0, 0, 0), (1, 0, 0), (0, 0, 1)), squash=1.5)
    m = (Matrix.Translation((side * 0.2, 0, 4.42)) @ Matrix.Rotation(side * math.radians(-58), 4, "Y")
         @ Matrix.Translation((0, 0, 0.78)) @ Matrix.Diagonal((0.85, 1.0, 1.25, 1.0)))
    mb.transform(m, mk)


for s in (1, -1):
    loop(lid, s)
# knot
mk = lid.mark()
K.sphere(lid, (0, 0, 0), 0.52, 12, 8, zone="bow")
lid.transform(Matrix.Translation((0, 0, 4.5)) @ Matrix.Diagonal((0.95, 1.15, 0.9, 1.0)), mk)
# two ribbon tails lying on the lid, towards the front corners
for s in (1, -1):
    mkt = lid.mark()
    lid.tube([(s * 0.25, 0.25, 4.25), (s * 0.9, 0.95, 4.13), (s * 1.55, 1.55, 4.1), (s * 2.0, 1.95, 4.08)],
             [0.3, 0.4, 0.42, 0.3], segs=8, zone="bow", caps=True)
    # the tails are flat ribbons: squash the tube onto the lid top
    lid.transform(Matrix.Translation((0, 0, 4.0)) @ Matrix.Diagonal((1, 1, 0.42, 1)) @ Matrix.Translation((0, 0, -4.0 + 0.12)), mkt)

glow = P.MeshBuilder("CleanGift_Glow")
glow.lathe([(5.0, 0.0), (4.9, 0.08), (4.3, 0.08), (4.2, 0.0)], lambda d: P.circle2d(d, 32), zone="glow")

o_body, o_lid, o_glow = body.build(mats), lid.build(mats), glow.build(mats, weighted=False)
textured = [o_body, o_lid]
P.unwrap(textured, margin=0.012)
P.unwrap([o_glow], margin=0.02)
o_glow.hide_render = True
fin, maps = P.bake_set("Hub_CleanGift", textured, TEX)
o_glow.hide_render = False

print("[Hub_CleanGift] triangles")
t = P.report([o_body, o_lid, o_glow], {"CleanGift_Glow": 200})
print(f"  budget 2500: {'OK' if t < 2500 else 'OVER'}")
K.backface_report("CleanGift", [o_body, o_lid])
P.export_fbx(os.path.join(K.OUT, "Hub_CleanGift.fbx"), [o_body, o_lid, o_glow])
tex = K.tex_names("Hub_CleanGift")
SA_ = "SmoothPlastic (SurfaceAppearance)"
P.write_bounds(os.path.join(K.OUT, "Hub_CleanGift.bounds.json"), {
    "_tris_total": t,
    "lidHinge": {"point": [0, 3.2, 2.0], "axis": [1, 0, 0],
                 "note": "Roblox axes: back top edge of the box. Turn CleanGift_Lid about this line by up to about 100 degrees "
                         "(top swinging backwards, towards Roblox +Z) to open; or simply lift the lid straight up 2 studs"},
    "CleanGift_Body": P.bounds_entry(o_body, textures=tex, tint=None, material=SA_, note="cream box, blue ribbon, sky-blue inside (floor at 1.4)"),
    "CleanGift_Lid": P.bounds_entry(o_lid, textures=tex, tint=None, material=SA_, note="lid with the ribbon cross and the bow; separate so it can open"),
    "CleanGift_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                     note="Neon floor ring 10 across round the box, no shadow"),
}, notes="CLEAN POP PLAZA gift box. Replaces ChestBody, ChestLid, ChestBand x2, ChestBandLid x2, ChestLock, ChestGlow in "
         "buildChest(). Origin on the plaza floor at hub (-24, 0, 40), front (+Y here = Roblox -Z) facing (-14, 0, 20) as today. "
         "Box 5.6 x 4.0 x 3.2, lid 6.0 x 4.4, 5.75 tall with the bow.")
K.set_mat(o_glow, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanGift.blend"), None)

# ------------------------------------------------------------------ previews
K.studio((0, 0, 2.5), 6)
show = [o_body, o_lid, o_glow]
P.standard_previews("hub_clean_gift", show, block_at=(-5.6, 0.5, 0), beauty_dir=(0.5, 1.0, 0.45), lens=60)
# open: lid swung back about the hinge
hinge = Vector((0, -2.0, 3.2))
o_lid.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-95), 4, "X") @ Matrix.Translation(-hinge)
import bpy  # noqa: E402
bpy.context.view_layer.update()
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_gift_open.png"), (0, -1.2, 3.2), (0.45, 1.0, 0.7), 26, 60, res=(960, 720))
print("GIFT done")
