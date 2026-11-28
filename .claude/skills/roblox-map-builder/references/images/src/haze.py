# haze too thick vs right, on the Sugarworks spawn view (run on sugar_map.blend)
import bpy, os, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'gallery')
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 960, 540
KM = lambda p: Vector((-p[0], p[2], p[1]))
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.lens = 26; cam.data.clip_end = 5000
cam.location = KM((0, 9, 240)); cam.rotation_euler = (KM((0, 26, -264)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
pv = next(n for n in bpy.data.materials['HazeMat'].node_tree.nodes if n.type == 'PRINCIPLED_VOLUME')
for tag, d in (('haze_bad', .0022), ('haze_good', .00014)):
    pv.inputs['Density'].default_value = d; sc.render.filepath = os.path.join(OUT, tag + '.png'); bpy.ops.render.render(write_still=True)
print('HAZE_OK')
