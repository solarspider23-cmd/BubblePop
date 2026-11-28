# blender -b --python kit_sheet.py  -> renders every prop in a row (prop QA sheet)
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import forest_props as F
from pro_lib import clean, KM, r2b

HERE = os.path.dirname(os.path.abspath(__file__)); PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
clean()
coll = bpy.data.collections.new('Kit'); bpy.context.scene.collection.children.link(coll)

ROWS = [
    [F.oak(1), F.oak(2, h=20, col='leaf2'), F.pine(3), F.bush(4), F.bush(5, col='leaf2'), F.fern(6)],
    [F.mushroom(7, 1.4), F.mushroom(8, 1.6, glow=True), F.mossy_rock(9), F.log(10), F.stump(11), F.flower_patch(12, 'red'),
     F.flower_patch(13, 'cream'), F.grass_tuft(14)],
    [F.lantern_post(), F.fence(), F.crate(), F.barrel(), F.tent(), F.campfire(), F.signpost(), F.crystal_cluster()],
    [F.quest_board(), F.bridge(), F.altar()],
]
stats = {}
z = 0
for row in ROWS:
    x = 0; depth = 0
    for P in row:
        out = F.to_kit(P, coll)
        lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
        for me in out.values():
            for v in me.vertices: lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
        w = hi.x - lo.x
        for me in out.values():
            ob = bpy.data.objects[me.name]; ob.location = r2b((x + w / 2, 0, z))
        stats[P.name] = P.tris
        x += w + 6; depth = max(depth, hi.y - lo.y)
    z += depth + 10
json.dump(stats, open(os.path.join(PREV, 'kit_tris.json'), 'w'), indent=1)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.62, .78, .95, 1); bg.inputs[1].default_value = 1.1
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.color = (1, .93, .82); sun.rotation_euler = (math.radians(50), 0, math.radians(30))
ground = bpy.data.meshes.new('G'); ground.from_pydata([(-500, -500, -.05), (500, -500, -.05), (500, 500, -.05), (-500, 500, -.05)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new('G', ground); sc.collection.objects.link(g)
gm = bpy.data.materials.new('Gm'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (.32, .5, .26, 1); ground.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1800, 1100
def shot(name, loc, tgt, lens=35):
    cam.location = r2b(loc); cam.data.lens = lens; cam.data.clip_end = 3000
    cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)
shot('kit_row0.png', (45, 22, -48), (45, 10, 0), 40)
shot('kit_row1.png', (40, 10, -12), (40, 1.5, 32), 40)
shot('kit_row2.png', (55, 14, 14), (55, 2, 52), 38)
shot('kit_row3.png', (40, 26, 18), (40, 4, 70), 38)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'grove_kit.blend'))
print('KIT_OK', json.dumps(stats))
