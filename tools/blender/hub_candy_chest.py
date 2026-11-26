# Batch C2: free-gift chest (red toy chest with toy-gold bands, corner caps, star lock and a bow).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_candy_chest.py [-- fast]
#
# Outputs (art/hub_candy/): Hub_Chest.fbx (Chest_Body, Chest_Lid, Chest_Glow), Hub_Chest_color/normal/
# roughness.png (512), Hub_Chest.bounds.json (with the lid hinge), Hub_Chest.blend
# Previews: art/previews/hub_candy_chest_{beauty,turn,flat,thumb,eye,open}.png

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_candy_common as C  # noqa: E402

C.reset()

W, D, BODY_H = 6.0, 4.0, 3.5
LID_RY, LID_RZ = 2.05, 1.75
BAND_X = 1.9

ts = C.TexSet("Hub_Chest", 512, ao_dist=1.0)


def coins(P, N):
    """A heap of gold coins: little round discs with a rim (normal map) and a slight colour spread."""
    x, y = P[:, 0], P[:, 1]
    best = np.full(len(P), 9.0)
    tone = np.zeros(len(P))
    cell = 0.62
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            ix = np.floor(x / cell) + ox
            iy = np.floor(y / cell) + oy
            hsh = np.mod(np.sin(ix * 127.1 + iy * 311.7) * 43758.5453, 1.0)
            hs2 = np.mod(np.sin(ix * 269.5 + iy * 183.3) * 43758.5453, 1.0)
            cx = (ix + 0.2 + 0.6 * hsh) * cell
            cy = (iy + 0.2 + 0.6 * hs2) * cell
            d = np.hypot(x - cx, y - cy)
            closer = d < best
            best = np.where(closer, d, best)
            tone = np.where(closer, hsh, tone)
    r = 0.27
    disc = np.clip((r - best) / 0.035, 0, 1)
    rim = np.clip(1 - np.abs(best - (r - 0.06)) / 0.03, 0, 1)
    h = 0.04 * disc + 0.012 * rim
    gold = np.array(C.lin("gold"))
    deep = np.array(C.lin("#F0A828"))
    k = (0.35 + 0.65 * tone)[:, None] * disc[:, None]
    col = deep[None, :] * (1 - k) + gold[None, :] * k
    return {"col": col, "h": h, "rough": 0.18 + 0.12 * (1 - disc)}


ts.paint("red", "red", rough=0.24, ao=0.45, grad=0.07, zref=5.5)
ts.paint("gold", "gold", rough=0.2, ao=0.4, grad=0.03, zref=5.5)
ts.paint("coins", "gold", rough=0.2, ao=0.55, grad=0.0, fn=coins)
ts.paint("dark", "navy", rough=0.5, ao=0.2, grad=0.0)

chest = C.Model("Hub_Chest", ts)
chest.zone("Chest_Body", "tex", note="body, corner caps, bands, star lock, gold-coin interior")
chest.zone("Chest_Lid", "tex", bake_offset=(0, 0, 8), note="opens: hinge line along X at the back top edge of the body")
chest.zone("Chest_Glow", "glow", color="#C89614", emit=2.5, note="Neon floor disc, transparency ~0.35, no shadow")

# body: open box with a rounded rim and an inner wall down to the coin heap
chest.add("Chest_Body", "red", C.rlathe(W, D, 0.5, [(0.35, 0.0), (0.08, 0.1), (0.0, 0.4), (0.0, 3.2), (0.05, 3.42), (0.18, 3.5), (0.34, 3.5), (0.42, 3.4), (0.42, 3.0)], steps=4))
chest.add("Chest_Body", "coins", C.rlathe(W - 0.84, D - 0.84, 0.1, [(0.0, 3.02), (0.0, 3.12), (0.5, 3.3), (1.1, 3.42)], steps=3, caps=(False, True)), closed=False)
# gold corner caps and straps
for sx in (-1, 1):
    for sy in (-1, 1):
        chest.add("Chest_Body", "gold", C.rbox((1.0, 1.0, 1.15), (sx * 2.72, sy * 1.72, 0.575), r=0.33, segs=2))
    for sy in (-1, 1):
        chest.add("Chest_Body", "gold", C.rbox((0.66, 0.62, 3.3), (sx * BAND_X, sy * (D / 2 - 0.19), 1.75), r=0.2, segs=2))
# star lock (hero detail) with a keyhole
STAR_C = Vector((0, D / 2 + 0.12, 2.02))
chest.add("Chest_Body", "gold", C.slab(C.star_outline(1.12, 0.5, round_tips=0.1), 0.36, bevel=0.1, bsegs=2,
                                       matrix=C.frame_matrix(STAR_C, (1, 0, 0), (0, 0, 1))))
key = [(0.2 * math.cos(a), 0.12 + 0.2 * math.sin(a)) for a in np.radians(np.arange(-60, 241, 30))] + [(-0.12, -0.34), (0.12, -0.34)]
chest.add("Chest_Body", "dark", C.slab(key, 0.12, bevel=0.0, matrix=C.frame_matrix(STAR_C + Vector((0, 0.17, -0.1)), (1, 0, 0), (0, 0, 1))))

# lid: a barrel top, gold bands over it, a hasp down onto the lock, and a bow on top
arc = [(LID_RY * math.cos(a), BODY_H + LID_RZ * math.sin(a)) for a in np.radians(np.arange(0, 181, 15))]
xz = C.frame_matrix((0, 0, 0), (0, 1, 0), (0, 0, 1))  # outline (y, z), thickness along X
chest.add("Chest_Lid", "red", C.slab(arc, W + 0.1, bevel=0.4, bsegs=3, matrix=xz))
band = [((LID_RY + 0.1) * math.cos(a), BODY_H + (LID_RZ + 0.1) * math.sin(a)) for a in np.radians(np.arange(0, 181, 15))]
for sx in (-1, 1):
    chest.add("Chest_Lid", "gold", C.slab(band, 0.66, bevel=0.14, bsegs=2,
                                          matrix=Matrix.Translation((sx * BAND_X, 0, 0)) @ xz))
chest.add("Chest_Lid", "gold", C.rbox((0.8, 0.4, 0.78), (0, D / 2 + 0.36, 3.6), r=0.16, segs=2))
top = BODY_H + LID_RZ
chest.add("Chest_Lid", "gold", C.ellipsoid((0, 0, top + 0.06), (0.42, 0.38, 0.32), u=10, v=6))
for s in (-1, 1):
    loop = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        loop.append((s * (0.78 + 0.55 * math.cos(a)), -0.05 * math.sin(a), top + 0.32 + 0.34 * math.sin(a) + 0.12 * math.cos(a)))
    chest.add("Chest_Lid", "gold", C.tube(loop, 0.2, segs=6, caps=None, closed=True, up=(0, 1, 0)), closed=False)
    tail = [(s * 0.22, 0.25, top + 0.0), (s * 0.48, 0.95, top - 0.25), (s * 0.66, 1.38, top - 0.62)]
    chest.add("Chest_Lid", "gold", C.tube(tail, [0.2, 0.2, 0.18], segs=6, caps="round", cap_rings=1))

chest.add("Chest_Glow", None, C.lathe([(5.0, 0.0), (4.85, 0.08), (0.0, 0.08)], segs=32, caps=(False, False)), closed=False)

chest.extra = {
    "replaces": "Hub.lua buildChest(): ChestBody, ChestLid, ChestBand x2, ChestBandLid x2, ChestLock, ChestGlow",
    "placement": "front left of the plaza at hub (-24, 0, 40), front (+Y here = Roblox -Z) faces (-14, 0, 20) as today",
    "lidHinge": {"point": [0, BODY_H, D / 2], "axis": [1, 0, 0],
                 "note": "Roblox axes: back top edge of the body. Rotate Chest_Lid about this line by up to about 105 degrees, top swinging backwards (towards Roblox +Z), to open"},
    "lockLight": {"position": [0, 2.02, -(D / 2 + 0.3)], "note": "good spot for the PointLight / Sparkles that sit on ChestLock today"},
}

C.build([chest])
if C.NOPREV:
    sys.exit(0)
C.studio()
C.standard_previews(chest, "hub_candy_chest", block_at=(-4.8, 1.0, 0))
# open-lid check
sc = bpy.context.scene
lid = chest.zones["Chest_Lid"]["obj"]
lid.rotation_mode = "XYZ"
pivot = Vector((0, -D / 2, BODY_H))
lid.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(105), 4, "X") @ Matrix.Translation(-pivot)
for o in sc.objects:
    if o.type == "MESH" and o.name != "studio_floor":
        o.hide_render = o not in chest.objects
lo, hi = C.model_bounds(chest.objects)
ls = C.lights(5)
cam = C.camera()
pos, mid = C.frame_shot(lo, hi, (0.5, 1.0, 0.9), 50, pad=1.0)
C.shoot(os.path.join(C.PREV, "hub_candy_chest_open.png"), pos, mid, 50, (1280, 960))
lid.matrix_world = Matrix.Identity(4)
for o in ls + [cam]:
    bpy.data.objects.remove(o)
C.save_blend("Hub_Chest", [chest])
