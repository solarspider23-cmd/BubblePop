# detail close-up of one prop: blender -b --factory-startup --python closeup.py -- "expr" out.png camx camy camz tx ty tz [lens]
import sys, os, math
A = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.getcwd())
import bpy
import canyon_props as FP
from pro_lib import clean, r2b
clean(); FP.G.MATS.clear()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('W'); sc.world = w; w.node_tree.nodes['Background'].inputs[0].default_value = (.55, .7, .95, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = .75
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 4.2; sun.data.color = (1, .92, .8); sun.rotation_euler = (math.radians(52), 0, math.radians(35))
P = eval(A[0], vars(FP)); FP.G.to_kit(P, sc.collection)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = float(A[8]) if len(A) > 8 else 35
cam.location = r2b(tuple(map(float, A[2:5]))); cam.rotation_euler = (r2b(tuple(map(float, A[5:8]))) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = 900, 700
sc.render.filepath = os.path.abspath(A[1]); bpy.ops.render.render(write_still=True)
