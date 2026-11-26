# Batch A2 (docs/art_plan.md): the BUBBLE POP logo banner that hangs across the gumball machine.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_machine_build_banner.py
#
# Outputs (art/hub_machine/): Hub_Banner.fbx, Hub_Banner.blend, Hub_Banner.bounds.json
#   Banner_Body   red pill plaque with a puffy edge; its front is a FLAT face 44.5 x 7 (the words
#                 BUBBLE POP stay in-game text on the middle 37.5 x 7 of it)
#   Banner_Trim   white backing rim with a raised bead and a groove, plus the two chunky brackets
#   Banner_Bolts  the two big toy-gold dome bolts (their own mesh: a flat-colour part has one colour)
# Previews (art/previews/): hub_machine_banner_beauty / _flat / _thumb / _turn .png
#
# Flat colours, no textures. Built hanging at its place on the machine, then moved to stand on
# the origin; "mount_on_machine" in the bounds file says where its origin goes.

import math
import os
import sys

from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_machine_common as C  # noqa: E402

L, RAD = 37.5, 3.5            # straight part and end radius of the flat face (44.5 x 7 pill)
MOUNT = Vector((0, 12.5, 17.5))  # on the machine: back of the rim / centre height (Blender axes)
ARM_X, ARM_Z, ARM_BACK = 5.5, -0.9, -6.7   # brackets reach back into the machine's neck
BODY, TRIM, BOLTS = 0, 1, 2
N = 16                         # steps round each end

scene = C.reset()
b = C.Build()


def pill(d, y):
    r = RAD + d
    pts = [(L / 2 + r * math.cos(a), y, r * math.sin(a)) for a in (math.radians(-90 + 180 * i / N) for i in range(N + 1))]
    pts += [(-L / 2 + r * math.cos(a), y, r * math.sin(a)) for a in (math.radians(90 + 180 * i / N) for i in range(N + 1))]
    return pts


# red plaque: flat face, puffy rounded edge
b.use("red", obj=BODY)
rings = b.loft([pill(0.0, 2.0), pill(0.22, 1.95), pill(0.38, 1.8), pill(0.45, 1.55), pill(0.45, 0.72)])
b.fan(rings[0], (0, 2.0, 0), flip=True)

# white rim: groove next to the plaque, then a raised bead, flat back
b.use("white", obj=TRIM)
rings = b.loft([pill(0.42, 0.75), pill(0.62, 0.75), pill(0.68, 1.0), pill(0.89, 1.17),
                pill(1.1, 1.0), pill(1.1, 0.15), pill(0.95, 0.0)])
b.fan(rings[-1], (0, 0, 0))
# brackets: chunky arms with a flange where they join the rim
for sx in (-1, 1):
    b.rbox((1.9, abs(ARM_BACK) + 0.3, 1.8), (sx * ARM_X, (ARM_BACK + 0.3) / 2, ARM_Z), 0.45, 2)
    b.rbox((3.0, 0.7, 2.9), (sx * ARM_X, -0.3, ARM_Z), 0.3, 1)

# gold dome bolts at the two ends (outside the 37.5 x 7 text area)
b.use("gold", obj=BOLTS)
for sx in (-1, 1):
    fr = Matrix.Translation(Vector((sx * 20.3, 2.0, 0))) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    b.lathe([(1.45, -0.1), (1.45, 0.12), (1.3, 0.42), (0.95, 0.66), (0.4, 0.82)], segs=14, frame=fr, cap_end=True)

objs = b.finalize({BODY: "Banner_Body", TRIM: "Banner_Trim", BOLTS: "Banner_Bolts"}, scene, pack=False)
model = [objs["Banner_Body"], objs["Banner_Trim"], objs["Banner_Bolts"]]

# stand it on the origin (bottom centre of its footprint)
lo = Vector([min(v.co[i] for o in model for v in o.data.vertices) for i in range(3)])
hi = Vector([max(v.co[i] for o in model for v in o.data.vertices) for i in range(3)])
shift = Vector((0, -(lo.y + hi.y) / 2, -lo.z))
for o in model:
    o.data.transform(Matrix.Translation(shift))
mount = MOUNT - shift
lo, hi = lo + shift, hi + shift

COL = {"Banner_Body": C.HEX["red"], "Banner_Trim": C.HEX["cream"], "Banner_Bolts": C.HEX["gold"]}
ROUGH = {"Banner_Body": 0.2, "Banner_Trim": 0.3, "Banner_Bolts": 0.22}
full = {n: C.plain_material(n, COL[n], ROUGH[n]) for n in COL}
flat = {n: C.plain_material(n + "_Flat", COL[n], 0.55) for n in COL}
for o in model:
    C.single_material(o, full[o.name])

tris = {o.name: C.tri_count(o) for o in model}
total = sum(tris.values())
body_box = C.roblox_box(model[0])
print("TRIANGLES", tris, "total", total)
print("SIZE %.2f long x %.2f high x %.2f deep (with brackets); plaque %s" % (hi.x - lo.x, hi.z - lo.z, hi.y - lo.y, body_box["size"]))
assert total < 1500, "over the triangle budget"
assert abs((hi.x - lo.x) - 46) / 46 <= 0.10 and abs((hi.z - lo.z) - 8.5) / 8.5 <= 0.10

C.export_fbx(model, os.path.join(C.OUT, "Hub_Banner.fbx"))
face_c = Vector((0, 2.0, 0)) + shift
C.write_json(os.path.join(C.OUT, "Hub_Banner.bounds.json"), {
    "_about": "Logo banner. Roblox axes: X right, Y up, Z = -Blender Y. Stands on the origin; its front faces Roblox -Z. "
              "Flat colours, no textures.",
    "_size": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
    "_tris_total": total,
    "mount_on_machine": {"origin": C.rbx(mount),
                         "note": "put the banner's origin here, measured from the machine's origin, both facing the same way; "
                                 "the brackets then reach into the machine's neck"},
    "text_face": {"center": C.rbx(face_c), "size": [37.5, 7.0], "normal": [0, 0, -1],
                  "note": "flat front of Banner_Body; the whole flat area is a 44.5 x 7 pill"},
    "Banner_Body": dict(body_box, color=C.rgb255(COL["Banner_Body"]), material="SmoothPlastic"),
    "Banner_Trim": dict(C.roblox_box(model[1]), color=C.rgb255(COL["Banner_Trim"]), material="SmoothPlastic"),
    "Banner_Bolts": dict(C.roblox_box(model[2]), color=C.rgb255(COL["Banner_Bolts"]), material="SmoothPlastic"),
})


def set_flat(on):
    for o in model:
        o.data.materials[0] = (flat if on else full)[o.name]


C.standard_previews(scene, "hub_machine_banner", lo, hi, set_flat, view=(0.45, 0.80, 0.30), player=(-26, 3, 0))
C.save_blend(os.path.join(C.OUT, "Hub_Banner.blend"), model)
print("BANNER done")
