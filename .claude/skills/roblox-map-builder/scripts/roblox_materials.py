# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Roblox materials per palette ramp: one module for the Blender preview and the export.
#   Map script:  import roblox_materials as RM
#                RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Cloud', 'Horizon'))   # after look()
#                RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides={'Cloud': 'SmoothPlastic'})
#   Export:      roblox_export.py -- --name X --materials        (reads material_map.json next to the .blend)
# Each solid mesh face points at one palette column, so the column decides the Roblox material; the exporter splits
# meshes per (material, colour) into MeshParts with Material + Color set by the setup module (no texture).
import json, os
import bpy

# default ramp-name -> Roblox material guesses (a build passes its own dict; names are Enum.Material names)
DEFAULT = {
    'grass': 'Grass', 'lawn': 'Grass', 'moss': 'Grass', 'leaf': 'LeafyGrass', 'leaf2': 'LeafyGrass', 'pine': 'LeafyGrass',
    'dirt': 'Ground', 'mud': 'Mud', 'sand': 'Sand', 'snow': 'Snow', 'ice': 'Ice', 'rock': 'Rock', 'stone': 'Slate',
    'cliff': 'Rock', 'basalt': 'Basalt', 'wood': 'WoodPlanks', 'wooddk': 'Wood', 'bark': 'Wood', 'gold': 'Foil',
    'metal': 'Metal', 'cloud': 'Marble', 'cream': 'SmoothPlastic', 'conc': 'Concrete', 'asph': 'Asphalt',
    'sea': 'SmoothPlastic', 'water': 'SmoothPlastic', 'brick': 'Brick', 'cloth': 'Fabric',
}

# preview look per Roblox material: (bump kind, scale, strength, roughness, metallic, specular)
LOOK = {
    'Grass':      ('noise', 2.2, .35, .95, 0, .15), 'LeafyGrass': ('noise', 1.4, .4, .9, 0, .15),
    'Ground':     ('noise', 5.0, .25, .95, 0, .1),  'Mud': ('noise', 3.0, .2, .6, 0, .3),
    'Sand':       ('noise', 14., .18, .95, 0, .1),  'Snow': ('noise', 2.5, .14, .75, 0, .2),
    'Ice':        ('noise', .6, .08, .12, 0, .7),   'Rock': ('voronoi', .32, .5, .9, 0, .15),
    'Slate':      ('voronoi', .65, .3, .85, 0, .2),  'Basalt': ('voronoi', .45, .4, .85, 0, .15),
    'WoodPlanks': ('wave', .35, .3, .8, 0, .15),    'Wood': ('wave', .9, .25, .8, 0, .15),
    'Foil':       ('noise', 3.0, .05, .22, .9, .5), 'Metal': ('noise', 6.0, .08, .4, .8, .4),
    'Marble':     ('noise', .8, .06, .35, 0, .45),  'SmoothPlastic': (None, 0, 0, .5, 0, .3),
    'Concrete':   ('noise', 8.0, .15, .9, 0, .15),  'Asphalt': ('noise', 16., .15, .9, 0, .1),
    'Brick':      ('voronoi', .8, .2, .9, 0, .1),   'Fabric': ('noise', 25., .1, .95, 0, .05),
}

def column_of(pal, u):
    from pro_lib import NCOL
    return pal.names[min(len(pal.names) - 1, int(u * NCOL))]

def _variant(base, name, look):
    kind, scale, strength, rough, metal, spec = look
    m = base.copy(); m.name = 'RBX_' + name; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if not kind: return m
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    if kind == 'noise':
        t = nt.nodes.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value = scale; t.inputs['Detail'].default_value = 4
        out = t.outputs['Fac']
    elif kind == 'voronoi':
        t = nt.nodes.new('ShaderNodeTexVoronoi'); t.feature = 'DISTANCE_TO_EDGE'; t.inputs['Scale'].default_value = scale
        out = t.outputs['Distance']
    else:                                                                  # wave: planks / grain along X
        t = nt.nodes.new('ShaderNodeTexWave'); t.inputs['Scale'].default_value = scale; t.inputs['Distortion'].default_value = 3
        t.bands_direction = 'X'; out = t.outputs['Fac']
    nt.links.new(geo.outputs['Position'], t.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = strength; bump.inputs['Distance'].default_value = .1
    nt.links.new(out, bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    # a little value variation from the same pattern so large surfaces are not one flat tone
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = .18
    nt.links.new(tex.outputs['Color'], mix.inputs['A']); nt.links.new(out, mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m

def mat_for(col, mapping): return mapping.get(col, DEFAULT.get(col, 'SmoothPlastic'))

def resolve(name, col, mapping, overrides):
    """material for palette ramp `col` on object/mesh `name`: per-prop overrides ({prefix: 'Mat'} = whole prop,
    {prefix: {ramp: 'Mat'}} = only those ramps) win over the build mapping"""
    for k, v in (overrides or {}).items():
        if name.startswith(k):
            if isinstance(v, str): return v
            if col in v: return v[col]
    return mat_for(col, mapping)

def preview(pal, pal_mat, mapping, skip=('Cloud', 'Horizon'), overrides=None):
    """give every palette mesh one Blender material slot per Roblox material (by palette column per face)"""
    cache = {}
    for me in bpy.data.meshes:
        if not me.materials or me.materials[0] != pal_mat or me.name.startswith(skip) or not me.uv_layers.active: continue
        uv = me.uv_layers.active.data; slots = {}
        me.materials.clear()
        for poly in me.polygons:
            rb = resolve(me.name, column_of(pal, uv[poly.loop_indices[0]].uv.x), mapping, overrides)
            if rb not in slots:
                if rb not in cache: cache[rb] = _variant(pal_mat, rb, LOOK.get(rb, LOOK['SmoothPlastic']))
                me.materials.append(cache[rb]); slots[rb] = len(me.materials) - 1
            poly.material_index = slots[rb]
    return cache

def write_map(pal, mapping, path, overrides=None):
    """material_map.json for the exporter: palette column index -> Roblox material, + per-prop-name overrides"""
    cols = {str(i): mat_for(n, mapping) for i, n in enumerate(pal.names)}
    json.dump({'columns': cols, 'names': list(pal.names), 'overrides': overrides or {}}, open(path, 'w'), indent=1)
