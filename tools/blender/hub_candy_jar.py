# Batch C4: gumball jar - old sweet-shop jar: gold base, stepped white pedestal with a gold band,
# slightly bulging glass with a thick rim, chunky ridged red screw lid with a ball knob, white shine.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_candy_jar.py [-- fast]
#
# Outputs (art/hub_candy/): Hub_Jar.fbx (Jar_Body, Jar_Glass, Jar_Shine), Hub_Jar_color/normal/
# roughness.png (512), Hub_Jar.bounds.json, Hub_Jar.blend
# Previews: art/previews/hub_candy_jar_{beauty,turn,flat,thumb,eye}.png
# Inside floor of the jar = height 3.2, inside diameter 5.8 (Batch A's gumball pile is made for it).

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_candy_common as C  # noqa: E402

C.reset()

FLOOR_Z, IN_R = 3.2, 2.9
SEG = 28

ts = C.TexSet("Hub_Jar", 512, ao_dist=0.9)
ts.paint("gold", "gold", rough=0.2, ao=0.4, grad=0.03, zref=12.6)
ts.paint("white", "cream", rough=0.28, ao=0.45, grad=0.05, zref=4.0)
ts.paint("red", "red", rough=0.24, ao=0.45, grad=0.04, zref=12.6)

jar = C.Model("Hub_Jar", ts)
jar.zone("Jar_Body", "tex", note="gold base, white pedestal with gold band, red lid and knob")
jar.zone("Jar_Glass", "glass", color="#EBF8FF", transparency=0.7, note="Roblox Glass, see-through ~0.6, no shadow")
jar.zone("Jar_Shine", "shine", color="cream", transparency=0.25, note="flat white highlight, SmoothPlastic, no shadow")

# gold base (8 across, 1.2 high)
jar.add("Jar_Body", "gold", C.lathe([(3.92, 0.0), (4.0, 0.42), (3.86, 1.08), (3.45, 1.2)], segs=SEG, caps=(True, True)))
# stepped white pedestal (6.5 across, up to 3.2) with a raised collar holding the glass
jar.add("Jar_Body", "white", C.lathe([(3.22, 1.1), (3.22, 1.5), (2.95, 1.75), (2.95, 2.72), (3.25, 2.95), (3.22, 3.38), (2.98, 3.42), (2.8, 3.22), (0.0, 3.2)], segs=SEG, caps=(True, False)))
# gold band round the pedestal waist
jar.add("Jar_Body", "gold", C.lathe([(2.9, 1.92), (3.1, 2.02), (3.1, 2.42), (2.9, 2.52)], segs=SEG, caps=(False, False)), closed=False)

# glass: bulging shell with a thick rolled rim (outer surface up, over the rim, inner surface down)
glass = [(3.05, 3.15), (3.18, 4.3), (3.2, 7.4), (2.98, 9.9), (3.12, 10.15),
         (2.88, 10.5), (2.88, 9.9), (3.0, 7.4), (2.96, 4.3), (IN_R, FLOOR_Z)]
jar.add("Jar_Glass", None, C.lathe(glass, segs=28, caps=(False, False)), closed=False, occluder=False)

# chunky ridged screw lid (6.8 across) with a domed top and a ball knob; top of everything 12.6
NR = 10
ridge = lambda i: 1.0 if (i // 2) % 2 == 0 else 0.955  # noqa: E731
jar.add("Jar_Body", "red", C.lathe([(3.05, 10.38), (3.35, 10.45), (3.4, 10.65), (3.4, 11.12)], segs=NR * 4, ripple=ridge, caps=(True, False)), closed=False)
jar.add("Jar_Body", "red", C.lathe([(3.05, 10.86), (3.37, 11.06), (3.34, 11.26), (3.12, 11.43), (1.9, 11.66), (0.0, 11.75)], segs=SEG, caps=(False, False)), closed=False)
jar.add("Jar_Body", "red", C.ellipsoid((0, 0, 11.95 + 0.0), (0.8, 0.8, 0.66), u=10, v=6))

# shine: a tall rounded window highlight and a small dot on the front-left of the glass
def glass_r(z):
    pts = [(3.05, 3.15), (3.18, 4.3), (3.2, 7.4), (2.98, 9.9)]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 3.0


def shine_patch(a_mid, half_w, z0, z1, rows=10, p=4.0):
    bm = bmesh.new()
    prev = None
    for i in range(rows + 1):
        t = -1 + 2 * i / rows
        z = (z0 + z1) / 2 + t * (z1 - z0) / 2
        w = half_w * max(1 - abs(t) ** p, 0.0) ** (1 / p)
        r = glass_r(z) + 0.04
        row = []
        for s in (-1, 0, 1):
            a = a_mid + s * w / r
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        if prev:
            for k in range(2):
                f = bm.faces.new((prev[k], prev[k + 1], row[k + 1], row[k]))
                f.smooth = True
        prev = row
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # face outward
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    return bm


A = math.radians(108)  # front, a little to the left (front = +Y = 90 degrees)
jar.add("Jar_Shine", None, shine_patch(A, 0.32, 5.0, 9.1, rows=10), closed=False, occluder=False)
jar.add("Jar_Shine", None, shine_patch(A + 0.02, 0.28, 3.9, 4.55, rows=4, p=2.0), closed=False, occluder=False)

jar.extra = {
    "replaces": "Hub.lua buildCandyJar(): JarBase, JarPedestal, Jar, JarLid, JarLidKnob (the 40 JarGumballs become Batch A's pile)",
    "placement": "centre at hub (-26, 0, -6), as today; the shine sits on the front, slightly left (front = Roblox -Z)",
    "insideFloor": {"height": FLOOR_Z, "diameter": IN_R * 2, "note": "gumball pile positions are measured from (0, 3.2, 0)"},
}

C.build([jar])
if C.NOPREV:
    sys.exit(0)
C.studio()
C.standard_previews(jar, "hub_candy_jar", block_at=(-6.0, 1.5, 0))
C.save_blend("Hub_Jar", [jar])
