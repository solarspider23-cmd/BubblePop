# blender -b wh_map.blend --python wh_real.py -- [shot ...] -> previews/real_<shot>.png : photoreal Cycles pass of Northgate
# (render only, never saved): smooth by angle, bevelled edges, physical sky + low sun through the open docks and the
# skylights, a real downlight under every high-bay, polished-concrete reflections, dust haze (world volume), DOF.
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(bpy.data.filepath); PREV = os.path.join(HERE, 'previews')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SC = bpy.context.scene
def r2b(p): return Vector((-p[0], p[2], p[1]))

SC.render.engine = 'CYCLES'; cy = SC.cycles
cy.samples = int(os.environ.get('SAMPLES', 192)); cy.use_denoising = True; cy.max_bounces = 6; cy.volume_bounces = 0
try:
    pr = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            pr.compute_device_type = t; pr.get_devices()
            if any(d.type == t for d in pr.devices):
                for d in pr.devices: d.use = d.type == t
                cy.device = 'GPU'; print('DEVICE', t); break
        except Exception: pass
except Exception: pass
SC.view_settings.view_transform = 'AgX'
try: SC.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
SC.view_settings.exposure = float(os.environ.get('EXPOSURE', 0.0))

for me in bpy.data.meshes:                                       # smooth by angle: boxes stay crisp, round parts go smooth
    if me.name.startswith('Tractor'): continue                   # long raked cab faces band when smoothed: keep the authored shading
    try: me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(35))
    except Exception: pass

# ---- materials
PBR = {   # Roblox material -> (roughness, metallic, coat, bump scale, bump strength)
    'Concrete': (.42, 0, 0, 18., .12), 'Asphalt': (.85, 0, 0, 60., .25), 'Metal': (.42, .3, .1, 0, 0), 'DiamondPlate': (.4, .9, 0, 0, 0),
    'Cardboard': (.92, 0, 0, 40., .06), 'WoodPlanks': (.8, 0, 0, 0, 0), 'Wood': (.75, 0, 0, 0, 0), 'Plastic': (.32, 0, .3, 0, 0),
    'SmoothPlastic': (.28, 0, .25, 0, 0), 'Rubber': (.75, 0, 0, 0, 0), 'Glass': (.05, 0, 0, 0, 0)}
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    if b is None: continue
    if m.name.startswith('Glow_'):
        k = m.name[5:]
        for n in list(nt.nodes):
            if n.type in ('MAP_RANGE', 'LAYER_WEIGHT'): nt.nodes.remove(n)
        b.inputs['Emission Strength'].default_value = {'lamp': 30, 'sky': 1.2, 'beacon': 12, 'stop': 10, 'go': 10}.get(k, 10)
        if k == 'sky':                                           # skylight: let the real sun + sky through, faint milky glow
            out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mix = nt.nodes.new('ShaderNodeMixShader')
            mix.inputs[0].default_value = .85; nt.links.new(b.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], out.inputs['Surface'])
        continue
    kind = m.name[4:] if m.name.startswith('RBX_') else ''
    r, met, coat, bs, bstr = PBR.get(kind, (.6, 0, 0, 0, 0))
    b.inputs['Roughness'].default_value = r; b.inputs['Metallic'].default_value = met
    try: b.inputs['Coat Weight'].default_value = coat
    except Exception: pass
    bev = nt.nodes.new('ShaderNodeBevel'); bev.inputs['Radius'].default_value = .05; bev.samples = 6
    bump = next((n for n in nt.nodes if n.type == 'BUMP'), None)
    nt.links.new(bev.outputs['Normal'], bump.inputs['Normal'] if bump else b.inputs['Normal'])
    if kind in ('Metal', 'Plastic', 'SmoothPlastic', 'Rubber') and bump is not None: bump.inputs['Strength'].default_value = 0
    if kind in ('Metal', 'Plastic', 'SmoothPlastic', 'Rubber'):
        for n in nt.nodes:
            if n.type == 'MIX' and n.blend_type == 'MULTIPLY': n.inputs['Factor'].default_value = .03
    if kind == 'Concrete':                                       # polished slab: roughness varies (scuffs, tyre tracks)
        geo = nt.nodes.new('ShaderNodeNewGeometry'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = .08; nz.inputs['Detail'].default_value = 6
        nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = .22; mr.inputs['To Max'].default_value = .6
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    if kind == 'Glass':
        b.inputs['Transmission Weight'].default_value = .9; b.inputs['IOR'].default_value = 1.1

for me in bpy.data.meshes:                                       # truck cab: big n-gon faces fan into thin triangles; the bevel
    if not me.name.startswith('Tractor'): continue              # node draws seams along them, so these get bevel-free copies
    for i, m in enumerate(me.materials):
        if m is None or m.name.startswith('Glow_'): continue
        c = bpy.data.materials.get(m.name + '_NoBev')
        if c is None:
            c = m.copy(); c.name = m.name + '_NoBev'
            for n in list(c.node_tree.nodes):
                if n.type == 'BEVEL': c.node_tree.nodes.remove(n)
            bb = c.node_tree.nodes.get('Principled BSDF')
            if bb and m.name == 'RBX_SmoothPlastic':                  # satin truck paint: no mirror-sharp stripes
                bb.inputs['Roughness'].default_value = .5; bb.inputs['Coat Weight'].default_value = .15; bb.inputs['Coat Roughness'].default_value = .3
        me.materials[i] = c
# ---- lights: drop the preview lights; a real downlight under every high-bay; sun + physical sky; haze
for ob in list(SC.objects):
    if ob.type == 'LIGHT': bpy.data.objects.remove(ob)
def light(kind, loc, energy, col, size=1.0, aim=None, spot=None):
    L = bpy.data.lights.new('L', kind); L.energy = energy; L.color = col; L.shadow_soft_size = size
    if spot: L.spot_size = math.radians(spot); L.spot_blend = .8
    ob = bpy.data.objects.new('L', L); SC.collection.objects.link(ob); ob.location = r2b(loc)
    if aim is not None: ob.rotation_euler = (r2b(aim) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob
lamps = [ob for ob in SC.objects if ob.type == 'MESH' and ob.data.name == 'HighBay0' and 'Kit' not in [c.name for c in ob.users_collection]]
for ob in lamps:
    p = ob.matrix_world.translation; rp = (-p.x, p.z, p.y)
    light('SPOT', (rp[0], rp[1] - .15, rp[2]), float(os.environ.get('SPOT', 26000)), (1, .95, .88), 1.2, (rp[0], 0, rp[2]), 120)
print('DOWNLIGHTS', len(lamps))
for ob in SC.objects:                                            # LED panels under the mezzanine
    if ob.type == 'MESH' and ob.data.name == 'Mezzanine':
        o = ob.matrix_world.translation; ox, oz = -o.x, o.y
        for x in (-21, -1, 19):
            for z in (-11, 11): light('AREA', (ox + x, 12.1, oz + z), 900, (1, .97, .92), 3.0, (ox + x, 0, oz + z))
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
sun.data.energy = float(os.environ.get('SUN', 5.5)); sun.data.color = (1, .78, .55); sun.data.angle = math.radians(.8)
SD = Vector((-.6, .34, .72)).normalized()                         # Roblox direction TO the sun: low, south-west
sun.rotation_euler = (-r2b(SD)).to_track_quat('-Z', 'Y').to_euler()
w = SC.world; nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky'); bgn = nt.nodes.new('ShaderNodeBackground'); out = nt.nodes.new('ShaderNodeOutputWorld')
try:
    sky.sky_type = 'NISHITA'; sky.sun_elevation = math.asin(SD.y); sky.sun_rotation = math.atan2(-SD.x, SD.z) + math.pi; sky.sun_disc = False
except Exception: pass
bgn.inputs['Strength'].default_value = float(os.environ.get('SKY', .35))
nt.links.new(sky.outputs[0], bgn.inputs[0]); nt.links.new(bgn.outputs[0], out.inputs['Surface'])
if os.environ.get('HAZE', '1') != '0':                           # dust in the hall: a volume box (sun shafts through doors / skylights)
    bpy.ops.mesh.primitive_cube_add(size=1); hz = bpy.context.active_object; hz.name = 'Haze'
    hz.scale = (240, 160, 40); hz.location = r2b((0, 18, 0))
    hm = bpy.data.materials.new('Haze'); hm.use_nodes = True; hn = hm.node_tree; hn.nodes.clear()
    vs = hn.nodes.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = float(os.environ.get('DENSITY', .0022)); vs.inputs['Anisotropy'].default_value = .55
    vo = hn.nodes.new('ShaderNodeOutputMaterial'); hn.links.new(vs.outputs[0], vo.inputs['Volume']); hz.data.materials.append(hm)
    hz.visible_shadow = False

SHOTS = {
    'spawn':  ((-110, 6.5, 38), (0, 10, 40), 24),
    'aisle':  ((-92, 6, 28), (-92, 9, -40), 24),
    'crane':  ((-44, 5.5, 50), (-12, 14, 37), 22),
    'dock':   ((-28, 6.5, 44), (5, 5, 76), 22),
    'mezz':   ((40, 8, -2), (90, 12, -55), 22),
    'yard':   ((40, 10, 142), (-20, 2, 84), 24),
    'forklift': ((-52, 5, 28), (-44, 4, 36), 30),
    'office': ((60, 19.5, -44), (98, 18, -66), 24),
    'truck':  ((-13, 2.0, 143.5), (0, 2.5, 130), 26),
}
cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
SC.camera = cam; cam.data.clip_start = .1; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6
SC.render.resolution_x, SC.render.resolution_y = int(os.environ.get('RX', 1600)), int(os.environ.get('RY', 900))
for name in (ARGS or ['spawn', 'aisle', 'crane', 'dock', 'mezz', 'yard']):
    loc, tgt, lens = SHOTS[name]
    cam.data.lens = lens; cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.focus_distance = (Vector(tgt) - Vector(loc)).length * .9
    SC.render.filepath = os.path.join(PREV, 'real_' + name + '.png'); bpy.ops.render.render(write_still=True); print('RENDERED', name)
