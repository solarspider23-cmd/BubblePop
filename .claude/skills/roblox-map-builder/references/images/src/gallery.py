# Renders the before/after pairs for references/bug_gallery.md (each scene holds BAD on the left, GOOD on the right).
#   blender -b --factory-startup --python gallery.py
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(SK, 'examples', 'sugarworks'))
os.chdir(HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import sugar_props as FP
G = FP.G
from pro_lib import clean, KM, r2b, cyl, box, MB

OUT = os.path.join(HERE, 'gallery'); os.makedirs(OUT, exist_ok=True)

def scene_reset():
    clean()
    sc = bpy.context.scene; G.MATS.clear()
    w = bpy.data.worlds.new('Sky'); sc.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    bg.inputs[0].default_value = (.42, .58, .95, 1); bg.inputs[1].default_value = .9      # clear blue sky
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 4.5; sun.data.color = (1, .88, .74); sun.rotation_euler = (math.radians(55), 0, math.radians(25))
    sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 1600, 800
    return sc

def put(P, loc, yaw=0.0, s=1.0):
    coll = bpy.context.scene.collection
    for me in G.to_kit(P, coll).values():
        ob = bpy.data.objects[me.name]
        R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
        ob.matrix_world = Matrix.Translation(r2b(loc)) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
        ob.name = ob.name + '_%d' % int(loc[0])

def flat(name, bm, rgb, spec=.5, rough=.6):
    me = bpy.data.meshes.new(name); bm.transform(KM.to_4x4()); bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new(name); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Specular IOR Level'].default_value = spec; b.inputs['Roughness'].default_value = rough
    me.materials.append(m); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob

def ground(rgb=(.36, .72, .3), size=400):
    flat('Ground', G.at(box((size, 1, size)), (0, -.5, 0)), rgb, .2, .9)

def shot(name, loc, tgt, lens=40):
    sc = bpy.context.scene
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = r2b(loc); cam.data.lens = lens
    cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)

# ---- A. doorway: boolean on a solid drum (flat wall in the hole) vs hollow shell (real opening)
def drum(hollow):
    P = FP.Prop('Drum%d' % hollow); R = 12.0; hw, spring = 3.5, 6.0
    wall = cyl(R, 13.0, sides=28, y0=0)
    if hollow: wall = G.bool_diff(wall, cyl(R - 1.2, 15, sides=28, y0=-1))
    P.add(G.bool_diff(wall, G.arch_prism(hw, spring, -R - 3, -R + 3, y0=-2)), FP.S('cream', grad=(0, 13, .5, .72)), smooth=True)
    P.add(G.arch_frame(hw, spring, 1.0, -R - .8, -R + .6), FP.S('pink', base=.6))
    P.add(FP.at(FP.dome(R + .4, 8, n=28, rings=5), (0, 13, 0)), FP.S('mint', grad=(13, 21, .45, .8)), smooth=True)
    if hollow:
        P.add(G.arch_tunnel(hw, spring, -R + .5, -R + 4), FP.S('choc', base=.12, jit=0))
        P.gadd(G.arch_cap(hw - .3, spring, -R + 3.8), 'lamp')
    return P
scene_reset(); ground()
put(drum(False), (-18, 0, 0), 180); put(drum(True), (18, 0, 0), 180)
shot('door.png', (0, 12, 62), (0, 7, 0), 38)

# ---- B. grounding on a slope: centre height (front corners float) vs lowest footprint point minus sink
scene_reset()
slope = 22.0
g = box((140, 1, 80)); G.at(g, (0, -.5, 0), (0, 0, slope)); flat('Slope', g, (.36, .72, .3), .2, .9)
H = lambda x: math.tan(math.radians(slope)) * x
for x, good in ((-12, False), (12, True)):
    P = FP.candy_crate(1, s=5.0)
    if good:
        y = min(H(x - 2.5), H(x + 2.5)) - .25                  # lowest point of the 6-stud footprint, sunk .25
    else:
        y = H(x)                                           # centre height
    put(P, (x, y, 0), 0)
shot('grounding.png', (0, 3.5, 34), (0, 1.5, 0), 34)

# ---- C. big pale floors: glossy pink tiles turn lilac under a blue sky; warm matte tiles stay warm
scene_reset()
for x0, cols, spec, rough in ((-24, ((1, .82, .9), (1, .93, .96)), .5, .5), (24, ((1, .86, .58), (1, .95, .84)), .12, .95)):
    for i in range(4):
        for j in range(4):
            t = box((9.7, .6, 9.7)); G.at(t, (x0 - 15 + i * 10, 0, -15 + j * 10))
            flat('T%d_%d_%d' % (x0, i, j), t, cols[(i + j) % 2], spec, rough)
put(FP.candy_crate(2, s=3), (-24, .3, 0), 20); put(FP.candy_crate(2, s=3), (24, .3, 0), 20)
shot('floor.png', (0, 30, 52), (0, 0, -2), 34)

# ---- D. ring vs pillars: ring radius = pillar offset hides the ring inside the pillars
def ring_gate(bad):
    P = FP.Prop('RingGate%d' % bad); off = 3.6 if bad else 4.2; R = 3.6 if bad else 3.0
    for sz in (-1, 1): P.add(FP.at(box((1.8, 9.0, 1.8), .2), (0, 4.8, sz * off)), FP.S('grape', base=.5, up=.25))
    P.add(FP.at(box((3.2, 2.0, off * 2 + 2.4), .4), (0, 10.0, 0)), FP.S('grape', base=.6, up=.2))
    P.gadd(FP.at(FP.torus(R, .35, n=28, sides=5), (0, 6.2, 0), (0, 0, 90)), 'ring')
    if bad: P.gadd(FP.at(box((.15, 5.4, 3.2)), (0, 5.4, 0)), 'beam')
    else:
        for y in (3.7, 4.5): P.gadd(FP.at(box((.12, .12, 3.6)), (0, y, 0)), 'beam')
    return P
scene_reset(); ground()
put(ring_gate(True), (-9, 0, 0), 70); put(ring_gate(False), (9, 0, 0), 70)
shot('ring.png', (0, 9, 28), (0, 5, 0), 36)
print('GALLERY_OK')
