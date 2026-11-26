# Batch C3: gumball pit - one fat inflatable ring (two stacked tubes, like a paddling pool) with
# red/cream candy stripes, an entrance gap with a little ramp, and a quilted mint floor.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_candy_pit.py [-- fast]
#
# Outputs (art/hub_candy/): Hub_Pit.fbx (Pit_Body), Hub_Pit_color/normal/roughness.png (512),
# Hub_Pit.bounds.json, Hub_Pit.blend
# Previews: art/previews/hub_candy_pit_{beauty,turn,flat,thumb,eye,top}.png

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_candy_common as C  # noqa: E402

C.reset()

RC = 10.6            # ring centre line radius
LOBE_R, C1, C2 = 0.8, 0.8, 2.2   # two stacked tubes (centres at height 0.8 and 2.2) -> 3 high, 1.6 thick
MID = 1.5
GAP = 5.0            # clear entrance width
DELTA = math.asin((GAP / 2 + LOBE_R) / RC)   # half-angle of the opening at the ring's station ends
T0 = math.pi / 2 + DELTA
SPAN = 2 * math.pi - 2 * DELTA
NSTRIPE = 27
FLOOR_Z = 0.3


def section(n=18, k=0.25):
    """Outline of two merged circles (smooth union), sampled round (0, MID); bottom flattened."""
    def f(u, v):
        a = math.hypot(u, v - C1) - LOBE_R
        b = math.hypot(u, v - C2) - LOBE_R
        return -k * math.log(math.exp(-a / k) + math.exp(-b / k))
    pts = []
    for i in range(n):
        th = -math.pi / 2 + 2 * math.pi * i / n
        du, dv = math.cos(th), math.sin(th)
        lo, hi = 0.0, 3.0
        for _ in range(40):
            m = (lo + hi) / 2
            if f(du * m, MID + dv * m) < 0:
                lo = m
            else:
                hi = m
        u, v = du * lo, MID + dv * lo
        pts.append((u, max(v, 0.0)))
    return pts


SEC = section()

ts = C.TexSet("Hub_Pit", 512, ao_dist=1.2, ss=4)
STRIPE_ANG = SPAN / NSTRIPE


def stripes(P, N):
    th = np.arctan2(P[:, 1], P[:, 0])
    s = np.mod(th - T0, 2 * math.pi) / STRIPE_ANG + P[:, 2] * 0.17
    red = (np.mod(np.floor(s), 2) == 0)[:, None]
    col = np.where(red, np.array(C.lin("red")), np.array(C.lin("cream")))
    rough = np.where(red[:, 0], 0.2, 0.24)
    return {"col": col, "rough": rough}


def quilt(P, N):
    c = 1.7
    a = (P[:, 0] + P[:, 1]) / math.sqrt(2) / c
    b = (P[:, 0] - P[:, 1]) / math.sqrt(2) / c
    fa, fb = a - np.floor(a), b - np.floor(b)
    pillow = np.power(np.sin(math.pi * fa), 0.5) * np.power(np.sin(math.pi * fb), 0.5)
    up = np.clip(N[:, 2], 0, 1)
    h = 0.11 * pillow * up
    base = np.array(C.lin("mint"))
    col = base[None, :] * (0.84 + 0.16 * pillow)[:, None]
    return {"col": col, "h": h}


ts.paint("ring", "red", rough=0.2, ao=0.45, grad=0.08, zref=3.0, fn=stripes)
ts.paint("floor", "mint", rough=0.45, ao=0.5, grad=0.0, fn=quilt)

pit = C.Model("Hub_Pit", ts)
pit.zone("Pit_Body", "tex", note="ring + floor + ramp, one textured mesh")

# the ring: sweep the section round the arc, with rounded (inflated) ends at the gap
frames = []
nst = NSTRIPE * 2
for i in range(nst + 1):
    th = T0 + SPAN * i / nst
    U = Vector((math.cos(th), math.sin(th), 0))
    frames.append((Vector((RC * U.x, RC * U.y, MID)), U, Vector((0, 0, 1))))


def cap(th, sign):
    U = Vector((math.cos(th), math.sin(th), 0))
    T = Vector((-math.sin(th), math.cos(th), 0)) * sign
    o = Vector((RC * U.x, RC * U.y, MID))
    out = []
    for k in (1, 2, 3):
        a = math.pi / 2 * k / 3.6
        out.append((o + T * LOBE_R * 1.05 * math.sin(a), U * math.cos(a), Vector((0, 0, 1)) * math.cos(a)))
    return out


frames = list(reversed(cap(T0, -1))) + frames + cap(T0 + SPAN, 1)
sec_c = [(u, v - MID) for u, v in SEC]
pit.add("Pit_Body", "ring", C.sweep(sec_c, frames))

# padded floor (sits under the ring) and the entrance ramp
pit.add("Pit_Body", "floor", C.lathe([(RC - 0.2, 0.0), (RC - 0.2, FLOOR_Z), (RC - 0.2, FLOOR_Z), (0.0, FLOOR_Z)], segs=48, caps=(False, False)), closed=False)
ramp = [(RC - 1.4, 0.0), (RC + 2.35, 0.0), (RC + 2.2, 0.07), (RC + 1.85, 0.12), (RC + 0.1, FLOOR_Z), (RC - 1.4, FLOOR_Z)]
pit.add("Pit_Body", "floor", C.slab(ramp, GAP - 0.4, bevel=0.1, bsegs=2,
                                    matrix=C.frame_matrix((0, 0, 0), (0, 1, 0), (0, 0, 1))))

pit.extra = {
    "replaces": "Hub.lua buildGumballPit(): PitFloor, PitWall x16 (the 7 BouncyGumballs and the sign stay)",
    "placement": "centre at hub (-38, 0, 16); the entrance (Blender +Y = Roblox -Z) should face the plaza middle, i.e. turn it so the gap points to +X",
    "insideFloorHeight": FLOOR_Z,
    "ring": {"outerDiameter": round(2 * (RC + LOBE_R), 2), "innerDiameter": round(2 * (RC - LOBE_R), 2), "height": 3.0,
             "entranceWidth": GAP, "entranceDirection": [0, 0, -1]},
    "collision": "keep simple invisible parts: a ring of wall blocks (skip the 5-stud gap) and a floor slab 0.3 high",
}

C.build([pit])
if C.NOPREV:
    sys.exit(0)
C.studio()
C.standard_previews(pit, "hub_candy_pit", block_at=(-3.0, 14.0, 0))
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "MESH" and o.name != "studio_floor":
        o.hide_render = o not in pit.objects
ls = C.lights(12)
cam = C.camera()
C.shoot(os.path.join(C.PREV, "hub_candy_pit_top.png"), (0.01, 5, 46), (0, 0.5, 0), 50, (1280, 960))
for o in ls + [cam]:
    bpy.data.objects.remove(o)
C.save_blend("Hub_Pit", [pit])
