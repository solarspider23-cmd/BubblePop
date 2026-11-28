# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Block-built (Part) maps: low-poly stud style for Roblox. Props are lists of Blocks (Block / Wedge / Cylinder / Ball)
# in ROBLOX space (X east, Y up, Z south, 1 unit = 1 stud, front = -Z). The same data is
#   1) meshed into Blender for preview (palette colours + procedural studs), and
#   2) written as an .rbxmx of real Parts (Glacier + a stud MaterialVariant, Neon for glow) - no meshes, no uploads.
# Roblox shape facts used here: Part.Shape Cylinder runs along the part's X axis; a WedgePart's tall end is at +Z
# (back) and its slope faces -Z (front) and up.
import math, os
import bpy, bmesh
from mathutils import Matrix, Vector, Euler
from pro_lib import hexrgb, KM, MB, clamp

MAT_TOKEN = {'stud': 1552, 'smooth': 272, 'neon': 288, 'plastic': 256, 'glass': 1568}   # Glacier (1552, checked in Studio) / SmoothPlastic / Neon

class Block:
    __slots__ = ('size', 'M', 'col', 'v', 'mat', 'shape', 'name', 'tr')
    def __init__(self, size, M, col, v, mat, shape, name, tr):
        self.size, self.M, self.col, self.v, self.mat, self.shape, self.name, self.tr = size, M, col, v, mat, shape, name, tr

def rotm(rot):
    """(pitch about X, yaw about Y, roll about Z) degrees, same order as pro_lib.xf"""
    return Euler([math.radians(a) for a in rot], 'YXZ').to_matrix().to_4x4()

class BlockProp:
    def __init__(self, name): self.name = name; self.blocks = []
    def b(self, size, pos=(0, 0, 0), col='stone', v=.55, rot=(0, 0, 0), mat='stud', shape='block', name=None, tr=0.0):
        M = Matrix.Translation(Vector(pos)) @ rotm(rot)
        self.blocks.append(Block(tuple(size), M, col, v, mat, shape, name or self.name, tr)); return self
    def put(self, other, pos=(0, 0, 0), yaw=0.0):
        """nest another BlockProp (e.g. a lamp on a gate)"""
        T = Matrix.Translation(Vector(pos)) @ rotm((0, yaw, 0))
        for k in other.blocks: self.blocks.append(Block(k.size, T @ k.M, k.col, k.v, k.mat, k.shape, k.name, k.tr))
        return self
    @property
    def count(self): return len(self.blocks)

def transformed(prop, pos, yaw=0.0, s=1.0):
    """world-space copies of a prop's blocks (uniform scale s scales sizes and offsets)"""
    T = Matrix.Translation(Vector(pos)) @ rotm((0, yaw, 0))
    out = []
    for k in prop.blocks:
        M = k.M.copy(); M.translation = M.translation * s
        out.append(Block(tuple(x * s for x in k.size), T @ M, k.col, k.v, k.mat, k.shape, k.name, k.tr))
    return out

# ------------------------------------------------------------------ colours
def rgb_of(pal, col, v):
    d, m, l = [Vector(hexrgb(c)) for c in pal.ramps[col]]
    c = d.lerp(m, v / .5) if v < .5 else m.lerp(l, (v - .5) / .5)
    return tuple(clamp(x) for x in c)

# ------------------------------------------------------------------ meshing (preview)
def shape_bm(shape, size):
    sx, sy, sz = size; bm = bmesh.new()
    if shape == 'wedge':
        v = [bm.verts.new(p) for p in ((-sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, -sz / 2), (sx / 2, -sy / 2, sz / 2), (-sx / 2, -sy / 2, sz / 2),
                                         (-sx / 2, sy / 2, sz / 2), (sx / 2, sy / 2, sz / 2))]
        for f in ((0, 3, 2, 1), (3, 4, 5, 2), (0, 1, 5, 4), (0, 4, 3), (1, 2, 5)): bm.faces.new([v[i] for i in f])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    elif shape == 'cyl':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=.5, radius2=.5, depth=1.0)   # axis Z in bmesh
        bmesh.ops.rotate(bm, cent=Vector(), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)   # -> axis X
        bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    elif shape == 'ball':
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=.5)
        bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    else:
        bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    return bm

def mesh_blocks(blocks, pal, name, coll, mats):
    """one solid mesh (palette + studs) + one mesh per neon colour + one for transparent blocks"""
    solid = MB(); neon = {}; clear = MB()
    for k in blocks:
        bm = shape_bm(k.shape, k.size); bm.transform(k.M)
        if k.mat == 'neon' and k.tr <= .05:
            key = k.col + '%.2f' % k.v
            rgb = rgb_of(pal, k.col, k.v); u = pal.u('white')
            neon.setdefault(key, (rgb, MB()))[1].add(bm, lambda f: [(u, .5)] * len(f.loops))
        elif k.tr > .05:
            u = pal.u(k.col); clear.add(bm, lambda f, u=u, v=k.v: [(u, v)] * len(f.loops))
        else:
            u = pal.u(k.col); v0 = k.v
            def sh(f, u=u, v0=v0):
                v = clamp(v0 + f.normal.y * .07 - (.06 if f.normal.y < -.5 else 0), .04, .96)
                return [(u, v)] * len(f.loops)
            solid.add(bm, sh)
    objs = []
    def emit(nm, mb, mat):
        if not mb.F: return
        vb = [tuple(KM @ Vector(v)) for v in mb.V]
        me = bpy.data.meshes.new(nm); me.from_pydata(vb, [], mb.F)
        uvl = me.uv_layers.new(name='UVMap')
        for fi, poly in enumerate(me.polygons):
            for j, l in enumerate(poly.loop_indices): uvl.data[l].uv = mb.UV[fi][j]
        me.materials.append(mat); ob = bpy.data.objects.new(nm, me); coll.objects.link(ob); objs.append(ob)
    emit(name, solid, mats['pal'])
    for key, (rgb, mb) in neon.items(): emit('%s_Neon_%s' % (name, key), mb, neon_mat(rgb, mats))
    emit(name + '_Clear', clear, mats['clear'])
    return objs

def neon_mat(rgb, mats):
    key = 'neon_%.2f_%.2f_%.2f' % rgb
    if key not in mats:
        m = bpy.data.materials.new(key); b = m.node_tree.nodes['Principled BSDF']
        lin = [x ** 2.2 for x in rgb]
        b.inputs['Base Color'].default_value = (*lin, 1); b.inputs['Emission Color'].default_value = (*lin, 1)
        b.inputs['Emission Strength'].default_value = 2.2; mats[key] = m
    return mats[key]

def stud_material(pal, tag, studs=1.0, strength=.35):
    """palette material + procedural studs (one round stud per `studs` studs, on every face) via a bump node,
    so previews read like Roblox stud surfaces; matte like Glacier"""
    m = pal.material(tag); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = .8; b.inputs['Specular IOR Level'].default_value = .2
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Position'], sep.inputs[0])
    sepn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sepn.inputs[0])
    def stud(a_out, b_out):
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        for i, o in enumerate((a_out, b_out)):
            mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'DIVIDE'; mul.inputs[1].default_value = studs
            nt.links.new(o, mul.inputs[0])
            fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; nt.links.new(mul.outputs[0], fr.inputs[0])
            sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = .5
            nt.links.new(fr.outputs[0], sub.inputs[0]); nt.links.new(sub.outputs[0], comb.inputs[i])
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(comb.outputs[0], ln.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .24; mr.inputs['From Max'].default_value = .32
        mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        nt.links.new(ln.outputs['Value'], mr.inputs['Value']); return mr.outputs['Result']
    X, Y, Z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
    parts = [(stud(X, Y), sepn.outputs['Z']), (stud(X, Z), sepn.outputs['Y']), (stud(Y, Z), sepn.outputs['X'])]
    acc = None
    for s_out, n_out in parts:
        ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; nt.links.new(n_out, ab.inputs[0])
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 4; nt.links.new(ab.outputs[0], pw.inputs[0])
        mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(s_out, mu.inputs[0]); nt.links.new(pw.outputs[0], mu.inputs[1])
        if acc is None: acc = mu.outputs[0]
        else:
            ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(acc, ad.inputs[0]); nt.links.new(mu.outputs[0], ad.inputs[1]); acc = ad.outputs[0]
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = strength; bump.inputs['Distance'].default_value = .06
    nt.links.new(acc, bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m

def clear_material():
    m = bpy.data.materials.new('Clear'); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Alpha'].default_value = .12
    b.inputs['Emission Color'].default_value = (1, 1, 1, 1); b.inputs['Emission Strength'].default_value = .3
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m

# ------------------------------------------------------------------ Roblox export (.rbxmx of Parts)
def _f(x): return ('%.4f' % x).rstrip('0').rstrip('.') if abs(x) > 1e-6 else '0'

def write_rbxmx(path, root_name, groups, pal, variant='Studs', min_shadow=1.5):
    """groups: {folder name: [Block, ...]} in world space. Writes a Model with one Folder per group. Glacier +
    MaterialVariant `variant` for stud parts, Neon for glow, SmoothPlastic + Transparency for clear parts.
    Parts are Anchored, CanTouch off; tiny / neon / clear parts cast no shadow."""
    ref = [0]
    def nref(): ref[0] += 1; return 'RBX%d' % ref[0]
    L = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4">',
         '<Item class="Model" referent="%s"><Properties><string name="Name">%s</string></Properties>' % (nref(), root_name)]
    n = 0
    for gname, blocks in groups.items():
        L.append('<Item class="Folder" referent="%s"><Properties><string name="Name">%s</string></Properties>' % (nref(), gname))
        for k in blocks:
            p = k.M.translation; R = k.M.to_3x3()
            r, g, b = [int(round(c * 255)) for c in rgb_of(pal, k.col, k.v)]
            cls = 'WedgePart' if k.shape == 'wedge' else 'Part'
            mat = 'smooth' if (k.tr > .05 and k.mat != 'neon') else k.mat
            props = ['<string name="Name">%s</string>' % k.name,
                     '<bool name="Anchored">true</bool><bool name="CanTouch">false</bool>',
                     '<CoordinateFrame name="CFrame"><X>%s</X><Y>%s</Y><Z>%s</Z>%s</CoordinateFrame>' % (
                         _f(p.x), _f(p.y), _f(p.z), ''.join('<R%d%d>%s</R%d%d>' % (i, j, _f(R[i][j]), i, j) for i in range(3) for j in range(3))),
                     '<Vector3 name="size"><X>%s</X><Y>%s</Y><Z>%s</Z></Vector3>' % tuple(_f(x) for x in k.size),
                     '<Color3uint8 name="Color3uint8">%d</Color3uint8>' % (0xFF000000 | (r << 16) | (g << 8) | b),
                     '<token name="Material">%d</token>' % MAT_TOKEN[mat],
                     '<token name="TopSurface">0</token><token name="BottomSurface">0</token>']
            if mat == 'stud': props.append('<string name="MaterialVariantSerialized">%s</string>' % variant)
            if k.tr > .05: props.append('<float name="Transparency">%s</float>' % _f(k.tr))
            if mat == 'neon' or k.tr > .05 or max(k.size) < min_shadow: props.append('<bool name="CastShadow">false</bool>')
            if k.tr > .05: props.append('<bool name="CanCollide">false</bool>')
            if cls == 'Part' and k.shape in ('cyl', 'ball'): props.append('<token name="shape">%d</token>' % (2 if k.shape == 'cyl' else 0))
            L.append('<Item class="%s" referent="%s"><Properties>%s</Properties></Item>' % (cls, nref(), ''.join(props)))
            n += 1
        L.append('</Item>')
    L.append('</Item></roblox>')
    open(path, 'w', encoding='utf8').write('\n'.join(L))
    return n
