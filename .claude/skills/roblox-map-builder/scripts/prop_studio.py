# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Close-up QA renders: one prop per image, framed to fill it, 3/4 front + a back view, then a contact sheet.
#   blender -b --factory-startup --python prop_studio.py -- --module sky_props --out studio "trophy()" "egg_shrine()" ...
# Run from the build folder (the props module is imported from there). Each expression is evaluated on the module.
# Why: kit sheets shrink props to a few hundred pixels and let crude shapes pass. Judge every prop at this size.
import sys, os, math
A = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d=None):
    if k in A:
        i = A.index(k); v = A[i + 1]; del A[i:i + 2]; return v
    return d
MOD = arg('--module'); OUT = os.path.abspath(arg('--out', 'studio')); RES = int(arg('--res', '900'))
sys.path.insert(0, os.getcwd())
import bpy
from mathutils import Vector
FP = __import__(MOD); G = getattr(FP, 'G', None)
import blocks as BK
from pro_lib import clean, r2b
os.makedirs(OUT, exist_ok=True)

def setup():
    clean()
    if G: G.MATS.clear()
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    w = bpy.data.worlds.new('W'); sc.world = w; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.55, .7, .95, 1); bg.inputs[1].default_value = .75
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 4.2; sun.data.color = (1, .92, .8); sun.data.angle = math.radians(6)
    sun.rotation_euler = (math.radians(52), 0, math.radians(35))
    if G:
        b = G.materials()['pal'].node_tree.nodes['Principled BSDF']
        b.inputs['Specular IOR Level'].default_value = .15; b.inputs['Roughness'].default_value = .92
    sc.render.resolution_x = sc.render.resolution_y = RES
    return sc

shots = []
for expr in A:
    sc = setup()
    P = eval(expr, vars(FP))
    if hasattr(P, 'blocks'):                                                   # block (Part) props: studs + neon
        mats = {'pal': BK.stud_material(FP.PAL, 'Kit'), 'clear': BK.clear_material()}
        meshes = [o.data for o in BK.mesh_blocks(P.blocks, FP.PAL, P.name, sc.collection, mats)]
        tris = sum(len(m.polygons) for m in meshes)
    else:
        meshes = list(G.to_kit(P, sc.collection).values()); tris = P.tris
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for me in meshes:
        for v in me.vertices: lo = Vector(map(min, lo, v.co)); hi = Vector(map(max, hi, v.co))
    c = (lo + hi) / 2; size = (hi - lo).length
    gm = bpy.data.meshes.new('Floor'); s = size * 3
    gm.from_pydata([(-s, -s, lo.z), (s, -s, lo.z), (s, s, lo.z), (-s, s, lo.z)], [], [(0, 1, 2, 3)])
    fl = bpy.data.objects.new('Floor', gm); sc.collection.objects.link(fl)
    fm = bpy.data.materials.new('F'); fm.node_tree.nodes['Principled BSDF'].inputs[0].default_value = (.78, .82, .9, 1); gm.materials.append(fm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50; dist = size * 1.55
    name = P.name
    for tag, yaw in (('front', -32), ('back', 148)):
        a = math.radians(yaw)
        # prop front = Roblox -Z = Blender -Y: the front view sits on the -Y side
        cam.location = c + Vector((math.sin(a) * dist, -math.cos(a) * dist, size * .42))
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        path = os.path.join(OUT, '%s_%s.png' % (name, tag)); sc.render.filepath = path
        bpy.ops.render.render(write_still=True); shots.append((name, tag, path))
    print('STUDIO', name, tris, getattr(P, 'count', ''))

try:
    from PIL import Image, ImageDraw
    names = []
    for n, t, p in shots:
        if n not in names: names.append(n)
    cell = RES // 2; W = cell * 2; H = cell * len(names)
    sheet = Image.new('RGB', (W, H), (30, 30, 40)); d = ImageDraw.Draw(sheet)
    for r, n in enumerate(names):
        for k, t in enumerate(('front', 'back')):
            p = [s for s in shots if s[0] == n and s[1] == t][0][2]
            sheet.paste(Image.open(p).convert('RGB').resize((cell, cell)), (k * cell, r * cell))
        d.text((8, r * cell + 6), n, fill=(255, 255, 255))
    sheet.save(os.path.join(OUT, 'contact.png')); print('CONTACT', os.path.join(OUT, 'contact.png'))
except ImportError:
    pass
