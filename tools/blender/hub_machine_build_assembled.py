# Batch A check picture: the machine, the banner and the gumball pile put together as in the game.
# Preview only (nothing is exported). Run the three build scripts first.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_machine_build_assembled.py
#
# Outputs (art/previews/): hub_machine_assembled_beauty / _flat / _thumb / _turn / _player .png
# The words on the banner are a stand-in for the in-game text (they are not part of any model).

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_machine_common as C  # noqa: E402

scene = C.reset()


def bring(blend):
    with bpy.data.libraries.load(os.path.join(C.OUT, blend)) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        scene.collection.objects.link(o)
    return {o.name: o for o in dst.objects}


machine = bring("Hub_Machine.blend")
banner = bring("Hub_Banner.blend")
with bpy.data.libraries.load(os.path.join(C.OUT, "Hub_GumballLo.blend")) as (src, dst):
    dst.meshes = [m for m in src.meshes if m in ("GumballLo", "GumballCore_Globe")]
lo_mesh = {m.name: m for m in dst.meshes}

mb = json.load(open(os.path.join(C.OUT, "Hub_Machine.bounds.json")))
bb = json.load(open(os.path.join(C.OUT, "Hub_Banner.bounds.json")))
ox, oy, oz = bb["mount_on_machine"]["origin"]
for o in banner.values():
    o.location = (ox, -oz, oy)
gx, gy, gz = mb["_globe"]["center"]
pile = C.add_pile(scene, os.path.join(C.OUT, "GumballPile_Globe.json"), lo_mesh["GumballLo"], (gx, -gz, gy),
                  core_mesh=lo_mesh["GumballCore_Globe"])

# stand-in for the in-game text
tx, ty, tz = bb["text_face"]["center"]
cu = bpy.data.curves.new("PreviewText", "FONT")
cu.body = "BUBBLE POP"
cu.align_x, cu.align_y = "CENTER", "CENTER"
cu.size = 5.6
cu.extrude = 0.02
text = bpy.data.objects.new("PreviewText", cu)
text.location = (ox + tx, -oz - tz + 0.06, oy + ty)
text.rotation_euler = (1.5708, 0, 3.14159)
scene.collection.objects.link(text)
cu.materials.append(C.plain_material("PreviewText", "#FFFFFF", 0.4))

body_mats = {}
full = machine["Machine_Body"].data.materials[0]
paths = {k: os.path.join(C.OUT, "Hub_Machine_%s.png" % k) for k in ("color", "roughness", "normal")}
flat = C.textured_material("Hub_Machine_Flat", paths, flat=True)


def set_flat(on):
    for n in ("Machine_Body", "Machine_Knob", "Machine_Flap"):
        machine[n].data.materials[0] = flat if on else full
    for o in list(banner.values()):
        o.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55 if on else 0.25
    for o in pile:
        if o.name.startswith("PreviewGum"):
            m = o.data.materials[0]
            want = m.name.rstrip("F") + ("F" if on else "")
            if want not in bpy.data.materials:
                C.textured_material(want, C.gumball_paths(), flat=on, tint=C.GUMBALL_HEX[int(m.name.rstrip("F")[-1])])
            o.data.materials[0] = bpy.data.materials[want]


bpy.context.view_layer.update()
allobj = list(machine.values()) + list(banner.values())
lo = Vector([min((o.matrix_world @ v.co)[i] for o in allobj for v in o.data.vertices) for i in range(3)])
hi = Vector([max((o.matrix_world @ v.co)[i] for o in allobj for v in o.data.vertices) for i in range(3)])


def extra(st):
    # what a player sees walking up to it (eye 5 studs up, 34 studs in front)
    cam = st["cam"]
    scene.render.resolution_x, scene.render.resolution_y = 1280, 960
    cam.data.lens = 22
    cam.location = (9, 40, 5.5)
    cam.rotation_euler = (Vector((0, 0, 21)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    C.render(scene, os.path.join(C.PREVIEWS, "hub_machine_assembled_player.png"))
    cam.data.lens = 35
    cam.location = (7, 23, 6.5)
    cam.rotation_euler = (Vector((0, 8, 7.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    C.render(scene, os.path.join(C.PREVIEWS, "hub_machine_assembled_closeup.png"))


C.standard_previews(scene, "hub_machine_assembled", lo, hi, set_flat, view=(0.42, 0.86, 0.2), player=(-19, 12, 0),
                    extra=extra)
print("ASSEMBLED done")
