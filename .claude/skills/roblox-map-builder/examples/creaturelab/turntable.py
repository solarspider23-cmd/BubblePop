# 4-angle turntable close-up of one prop in a sky-lit studio with the map's look (Standard view, cyan sky):
#   blender -b --factory-startup --python turntable.py -- "expr" outdir [ground_y]
import sys, os, math
A = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.getcwd())
import bpy
from mathutils import Vector
import lab_props as FP
from pro_lib import clean
clean(); FP.G.MATS.clear()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('W'); sc.world = w; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.6, .75, .95, 1); bg.inputs[1].default_value = .8
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 5.0; sun.data.color = (1, .97, .9); sun.data.angle = math.radians(6); sun.rotation_euler = (math.radians(45), 0, math.radians(30))
P = eval(A[0], vars(FP)); meshes = list(FP.G.to_kit(P, sc.collection).values())
lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
for me in meshes:
    for v in me.vertices: lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
c = (lo + hi) / 2; size = (hi - lo).length
gm = bpy.data.meshes.new('Floor'); s = size * 3
gm.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
fl = bpy.data.objects.new('Floor', gm); sc.collection.objects.link(fl)
fm = bpy.data.materials.new('F'); fm.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (.8, .83, .88, 1); gm.materials.append(fm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
sc.render.resolution_x = sc.render.resolution_y = 700
out = os.path.abspath(A[1]); os.makedirs(out, exist_ok=True)
for k, yaw in enumerate((-30, 60, 150, 240)):  # turntable
    a = math.radians(yaw); d = size * 1.25
    cam.location = c + Vector((math.sin(a) * d, -math.cos(a) * d, size * .25))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, '%s_%d.png' % (P.name, k)); bpy.ops.render.render(write_still=True)
print('TURN', P.name, P.tris)
