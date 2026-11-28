# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# blender -b --factory-startup --python frost_kit_sheet.py  -> prop QA sheet for the Frostpeak kit
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import frost_props as FP   # <- your build's props module
G = FP.G
from pro_lib import clean, r2b

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
clean()
coll = bpy.data.collections.new('Kit'); bpy.context.scene.collection.children.link(coll)
ROWS = [
    [FP.cabin(1), FP.cabin(2, w=11, d=9, wall_h=6.4), FP.roll_well(), FP.market_stall()],
    [FP.snow_pine(3), FP.snow_pine(4, h=24), G.mossy_rock(9), G.lantern_post(), G.fence(), G.crate(), G.barrel(), FP.fishing_hut()],
    [FP.frost_spire()],
]
stats = {}; z = 0; ROWINFO = []
for row in ROWS:
    x = 0; depth = 0; rowh = 0
    for P in row:
        out = G.to_kit(P, coll)
        lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
        for me in out.values():
            for v in me.vertices: lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
        w = hi.x - lo.x
        for me in out.values(): bpy.data.objects[me.name].location = r2b((x + w / 2, 0, z))
        stats[P.name] = P.tris; x += w + 7; depth = max(depth, hi.y - lo.y); rowh = max(rowh, hi.z - lo.z)
    ROWINFO.append((x - 7, z, max(depth, 1), max(rowh, 1))); z -= depth + 30   # later rows go BEHIND, so front cameras see each row clear
sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
w = bpy.data.worlds.new('W'); sc.world = w
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.6, .72, .9, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.4; sun.data.color = (1, .9, .78); sun.rotation_euler = (math.radians(55), 0, math.radians(30))
gm_ = bpy.data.meshes.new('G'); gm_.from_pydata([(-600, -600, -.05), (600, -600, -.05), (600, 600, -.05), (-600, 600, -.05)], [], [(0, 1, 2, 3)])
g = bpy.data.objects.new('G', gm_); sc.collection.objects.link(g)
gmat = bpy.data.materials.new('Gm'); gmat.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (.72, .8, .9, 1); gm_.materials.append(gmat)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1800, 1100
def shot(name, loc, tgt, lens=35):
    cam.location = r2b(loc); cam.data.lens = lens; cam.data.clip_end = 3000
    cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)
# auto-framed front (+Z) three-quarter view of every row: fits the row width at 35 mm
for i, (rw, rz, rd, rh) in enumerate(ROWINFO):
    dist = max(rw * .95, rh * 1.6) + rd
    shot('kit_row%d.png' % i, (rw * .62, rh * .55 + dist * .18, rz + dist), (rw / 2, rh * .32, rz), 35)
print('KIT_OK', json.dumps(stats))
