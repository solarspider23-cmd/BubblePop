# Shared helpers for the Batch D "Sky island" scripts (hub_island_*.py):
# mesh building with UVs, procedural bake to texture sets, studio previews,
# FBX export (house convention, same call as build_gumball.py) and bounds files.
#
# Not run on its own. Every hub_island_<asset>.py does:
#   import hub_island_common as C
#   C.reset(); b = C.Builder("Island_Rim") ... ; C.bake_set(...); C.export(...); C.previews(...)
#
# Axes: 1 Blender unit = 1 stud, Z up, front on +Y. Roblox X = Blender X, Roblox Y = Blender Z,
# Roblox Z = -Blender Y. Meshes are turned half round about Z for the FBX export (Roblox imports an
# FBX turned half round; same trick as kit.py / build_bubblewrap.py), then turned back.

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "art", "hub_island")
PREVIEWS = os.path.join(ROOT, "art", "previews")
TMP = os.path.join(OUT, "_tmp")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEWS, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

QUICK = os.environ.get("ISLAND_QUICK") == "1"

# palette (sRGB hex, from docs/art_plan.md)
PAL = {
    "red": "#E62D46", "cream": "#FFFCFA", "pink": "#FFB4D2", "tile": "#FFD6E6", "mint": "#6EDCBE",
    "lemon": "#FFC832", "gold": "#FFC83C", "grass": "#7DD75A", "choc": "#6E412D", "plum": "#283250",
    "glow": "#BE1E5A",
}
GUMBALLS = [("Red", "#E62D3C"), ("Blue", "#2878E6"), ("Amber", "#FFAF00"), ("Green", "#32AF46"),
            ("Pink", "#FF78BE"), ("Orange", "#FF8C28"), ("Purple", "#965AE6"), ("White", "#FFFFFF")]


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lin(h):
    """sRGB hex -> linear RGBA tuple."""
    c = [x / 255 for x in hex_rgb(h)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ------------------------------------------------------------------ mesh building
class Builder:
    """One output mesh. Faces carry a material index (a bake zone) and per-loop UVs."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = []

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def face(self, verts, uvs, mat, smooth=True):
        f = self.bm.faces.new(verts)
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        f.material_index = self.mi(mat)
        f.smooth = smooth
        return f

    def grid(self, rows, uvs, mat, closed=False, smooth=True):
        """rows: list of rows of Vector (row i+1 is 'below' row i, columns run so that
        the outside is on the right when walking down a column... i.e. the same order as
        lathe(): rows go down the profile, columns go counter-clockwise round +Z).
        A row of length 1 is a pole. uvs: same shape, (u, v) per point."""
        vrows = [[self.bm.verts.new(p) for p in row] for row in rows]
        for i in range(len(rows) - 1):
            a, b = vrows[i], vrows[i + 1]
            ua, ub = uvs[i], uvs[i + 1]
            n = max(len(a), len(b))
            cols = n if closed else n - 1
            for j in range(cols):
                j2 = (j + 1) % n
                if len(b) == 1:
                    self.face((a[j], b[0], a[j2]), (ua[j], ub[0], ua[j2]), mat, smooth)
                elif len(a) == 1:
                    self.face((a[0], b[j], b[j2]), (ua[0], ub[j], ub[j2]), mat, smooth)
                else:
                    self.face((a[j], b[j], b[j2], a[j2]), (ua[j], ub[j], ub[j2], ua[j2]), mat, smooth)
        return vrows

    def lathe(self, mat, profile, segs, rect, sectors=1, turn=0.0, smooth=True, vlen=None, squash=(1, 1), at=(0, 0, 0)):
        """Spin profile [(r, z), ...] (walk it top -> outside -> bottom so normals face out)
        round Z. UV: the circle is cut into `sectors` equal parts that all map onto rect
        (u0, v0, u1, v1) (a repeating texture), v follows the profile's length.
        vlen: profile length that maps to the full v range (default: its own length)."""
        u0, v0, u1, v1 = rect
        lengths = [0.0]
        for (ra, za), (rb, zb) in zip(profile, profile[1:]):
            lengths.append(lengths[-1] + math.hypot(rb - ra, zb - za))
        total = vlen or lengths[-1]
        sps = segs // sectors
        at = Vector(at)
        rings = []
        for r, z in profile:
            if r < 1e-6:
                rings.append([self.bm.verts.new(at + Vector((0, 0, z)))])
                continue
            ring = []
            for j in range(segs):
                a = turn + 2 * math.pi * j / segs
                ring.append(self.bm.verts.new(at + Vector((r * math.cos(a) * squash[0], r * math.sin(a) * squash[1], z))))
            rings.append(ring)
        for i in range(len(profile) - 1):
            A, B = rings[i], rings[i + 1]
            va = v1 - (v1 - v0) * lengths[i] / total
            vb = v1 - (v1 - v0) * lengths[i + 1] / total
            for j in range(segs):
                j2 = (j + 1) % segs
                loc = j % sps
                ua = u0 + (u1 - u0) * loc / sps
                ub = u0 + (u1 - u0) * (loc + 1) / sps
                if len(B) == 1:
                    self.face((A[j], B[0], A[j2]), ((ua, va), ((ua + ub) / 2, vb), (ub, va)), mat, smooth)
                elif len(A) == 1:
                    self.face((A[0], B[j], B[j2]), (((ua + ub) / 2, va), (ua, vb), (ub, vb)), mat, smooth)
                else:
                    self.face((A[j], B[j], B[j2], A[j2]), ((ua, va), (ua, vb), (ub, vb), (ub, va)), mat, smooth)
        for ring, r in ((rings[0], profile[0][0]), (rings[-1], profile[-1][0])):
            pass  # lathes here are open shells (ends are poles or tucked into other pieces)
        return rings

    def transform(self, matrix, verts=None):
        bmesh.ops.transform(self.bm, matrix=matrix, verts=verts if verts is not None else self.bm.verts)

    def to_object(self, scene=None):
        scene = scene or bpy.context.scene
        me = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        ob = bpy.data.objects.new(self.name, me)
        scene.collection.objects.link(ob)
        return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def smart_uv(ob, rect, angle=60.0, margin=0.02):
    """Smart-project a mesh's UVs and fit them into rect (u0, v0, u1, v1) of the atlas."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if not ob.data.uv_layers:
        ob.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    u0, v0, u1, v1 = rect
    for d in ob.data.uv_layers.active.data:
        d.uv = (u0 + d.uv[0] * (u1 - u0), v0 + d.uv[1] * (v1 - v0))


# ------------------------------------------------------------------ node helpers
class NT:
    """Small wrapper to write shader node graphs tersely."""

    def __init__(self, mat):
        mat.use_nodes = True
        self.mat = mat
        self.t = mat.node_tree
        self.n = self.t.nodes
        self.l = self.t.links

    def node(self, kind, **inputs):
        nd = self.n.new(kind)
        for k, v in inputs.items():
            self.set(nd.inputs[k], v)
        return nd

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.l.new(v, sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0, clamp=False):
        m = self.n.new("ShaderNodeMath")
        m.operation = op
        m.use_clamp = clamp
        self.set(m.inputs[0], a)
        self.set(m.inputs[1], b)
        return m.outputs[0]

    def mrange(self, x, a, b, c=0.0, d=1.0, smooth=False):
        m = self.n.new("ShaderNodeMapRange")
        m.clamp = True
        if smooth:
            m.interpolation_type = "SMOOTHSTEP"
        self.set(m.inputs["Value"], x)
        for k, v in zip(("From Min", "From Max", "To Min", "To Max"), (a, b, c, d)):
            m.inputs[k].default_value = v
        return m.outputs["Result"]

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n.new("ShaderNodeMix")
        m.data_type = "RGBA"
        m.blend_type = blend
        m.clamp_result = True
        self.set(m.inputs["Factor"], fac)
        self.set(m.inputs[6], a)
        self.set(m.inputs[7], b)
        return m.outputs[2]

    def vmath(self, op, a, b=(0, 0, 0)):
        m = self.n.new("ShaderNodeVectorMath")
        m.operation = op
        self.set(m.inputs[0], a)
        self.set(m.inputs[1], b)
        return m.outputs[0] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else m.outputs[1]

    def xyz(self, vec):
        s = self.n.new("ShaderNodeSeparateXYZ")
        self.set(s.inputs[0], vec)
        return s.outputs

    def combine(self, x, y, z):
        c = self.n.new("ShaderNodeCombineXYZ")
        self.set(c.inputs[0], x)
        self.set(c.inputs[1], y)
        self.set(c.inputs[2], z)
        return c.outputs[0]

    def noise(self, vec, scale, detail=1.0, rough=0.5, w=0.0, dims="4D"):
        nd = self.n.new("ShaderNodeTexNoise")
        nd.noise_dimensions = dims
        self.set(nd.inputs["Vector"], vec)
        if dims == "4D":
            self.set(nd.inputs["W"], w)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        return nd.outputs["Fac"]

    def voronoi(self, vec, scale, feature="F1", dims="3D", w=0.0, rand=1.0):
        nd = self.n.new("ShaderNodeTexVoronoi")
        nd.voronoi_dimensions = dims
        nd.feature = feature
        self.set(nd.inputs["Vector"], vec)
        if dims == "4D":
            self.set(nd.inputs["W"], w)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Randomness"].default_value = rand
        return nd

    def ao(self, dist, samples=16, only_local=False):
        nd = self.n.new("ShaderNodeAmbientOcclusion")
        nd.samples = samples
        nd.only_local = only_local
        nd.inputs["Distance"].default_value = dist
        return nd.outputs["AO"]

    def uv(self):
        return self.n.new("ShaderNodeTexCoord").outputs["UV"]

    def obj(self):
        return self.n.new("ShaderNodeTexCoord").outputs["Object"]

    def rgb(self, h):
        nd = self.n.new("ShaderNodeRGB")
        nd.outputs[0].default_value = lin(h) if isinstance(h, str) else h
        return nd.outputs[0]


# registry: material name -> dict(albedo=socket, rough=socket, normal=socket or None)
BAKE = {}


def bake_material(name, build):
    """build(nt) -> dict(albedo=colour socket, rough=float socket, height=float socket or None,
    bump=(strength, distance)). Makes a Principled material whose maps can be baked."""
    m = bpy.data.materials.new(name)
    nt = NT(m)
    nt.n.clear()
    out = build(nt)
    for key in ("albedo", "rough"):
        if not isinstance(out[key], bpy.types.NodeSocket):
            if key == "albedo":
                out[key] = nt.rgb(out[key])
            else:
                vn = nt.node("ShaderNodeValue")
                vn.outputs[0].default_value = out[key]
                out[key] = vn.outputs[0]
    bsdf = nt.node("ShaderNodeBsdfPrincipled")
    nt.set(bsdf.inputs["Base Color"], out["albedo"])
    nt.set(bsdf.inputs["Roughness"], out["rough"])
    if out.get("height") is not None:
        s, d = out.get("bump", (0.5, 0.05))
        bump = nt.node("ShaderNodeBump")
        bump.inputs["Strength"].default_value = s
        bump.inputs["Distance"].default_value = d
        nt.set(bump.inputs["Height"], out["height"])
        nt.set(bsdf.inputs["Normal"], bump.outputs["Normal"])
    o = nt.node("ShaderNodeOutputMaterial")
    nt.set(o.inputs["Surface"], bsdf.outputs["BSDF"])
    BAKE[name] = dict(nt=nt, albedo=out["albedo"], rough=out["rough"], bsdf=bsdf, out=o)
    return m


def setup_cycles(samples):
    """CPU only (owner's fanless Mac crashed with several GPU renders at once), <= 64 samples."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = min(samples, 64)
    sc.cycles.use_denoising = True


def bake_set(objects, prefix, size, clear=True, select=None, normal=True):
    """Bake colour, roughness and (tangent, OpenGL Y+) normal of every BAKE material used by
    `objects` into <prefix>_color/_roughness/_normal.png (size x size) in OUT. Objects keep
    their UVs; all must use the same atlas without overlaps (unless the values agree).
    select: the objects to bake (default all); the others still cast AO/shadow."""
    sc = bpy.context.scene
    setup_cycles(4 if QUICK else 24)
    sc.render.bake.margin = 6
    sc.render.bake.margin_type = "EXTEND"
    sc.render.bake.use_clear = clear
    targets = select or objects
    mats = []
    for ob in targets:
        for m in ob.data.materials:
            if m and m.name in BAKE and m not in mats:
                mats.append(m)
    paths = {}
    for kind, btype, cs in (("color", "EMIT", "sRGB"), ("roughness", "EMIT", "Non-Color"), ("normal", "NORMAL", "Non-Color")):
        if kind == "normal" and not normal:
            continue
        name = f"{prefix}_{kind}"
        path = os.path.join(OUT, name + ".png")
        if name in bpy.data.images:
            img = bpy.data.images[name]
        elif not clear and os.path.exists(path):
            img = bpy.data.images.load(path)
            img.name = name
        else:
            img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=(kind == "normal"))
            img.generated_color = (0.5, 0.5, 1.0, 1) if kind == "normal" else (0.5, 0.5, 0.5, 1)
        img.colorspace_settings.name = cs
        undo = []
        for m in mats:
            info = BAKE[m.name]
            nt = info["nt"]
            tex = nt.n.new("ShaderNodeTexImage")
            tex.image = img
            for nd in nt.n:
                nd.select = False
            tex.select = True
            nt.n.active = tex
            em = None
            if btype == "EMIT":
                em = nt.n.new("ShaderNodeEmission")
                src = info["albedo"] if kind == "color" else info["rough"]
                nt.l.new(src, em.inputs["Color"])
                nt.l.new(em.outputs["Emission"], info["out"].inputs["Surface"])
            undo.append((nt, tex, em, info))
        bpy.ops.object.select_all(action="DESELECT")
        for ob in targets:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = targets[0]
        kw = dict(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z") if btype == "NORMAL" else {}
        bpy.ops.object.bake(type=btype, **kw)
        for nt, tex, em, info in undo:
            nt.n.remove(tex)
            if em:
                nt.n.remove(em)
                nt.l.new(info["bsdf"].outputs["BSDF"], info["out"].inputs["Surface"])
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        paths[kind] = path
        print(f"[bake] {path}")
    return paths


def load_maps(prefix):
    maps = {}
    for k in ("color", "roughness", "normal"):
        p = os.path.join(OUT, f"{prefix}_{k}.png")
        name = f"{prefix}_{k}"
        if name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[name])
        im = bpy.data.images.load(p)
        im.name = name
        im.colorspace_settings.name = "sRGB" if k == "color" else "Non-Color"
        maps[k] = im
    return maps


def textured_material(name, maps, tint=None, flat=False):
    """What Roblox shows: SurfaceAppearance colour (x tint), roughness and normal maps.
    flat=True: colour map only (low phone graphics)."""
    m = bpy.data.materials.new(name)
    nt = NT(m)
    nt.n.clear()
    uvn = nt.node("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    tc = nt.node("ShaderNodeTexImage")
    tc.image = maps["color"]
    nt.set(tc.inputs["Vector"], uvn.outputs["UV"])
    bsdf = nt.node("ShaderNodeBsdfPrincipled")
    col = tc.outputs["Color"]
    if tint:
        col = nt.mix(1.0, col, lin(tint), "MULTIPLY")
    nt.set(bsdf.inputs["Base Color"], col)
    if flat:
        bsdf.inputs["Roughness"].default_value = 0.5
    else:
        tr = nt.node("ShaderNodeTexImage")
        tr.image = maps["roughness"]
        nt.set(tr.inputs["Vector"], uvn.outputs["UV"])
        nt.set(bsdf.inputs["Roughness"], tr.outputs["Color"])
        tn = nt.node("ShaderNodeTexImage")
        tn.image = maps["normal"]
        nt.set(tn.inputs["Vector"], uvn.outputs["UV"])
        nm = nt.node("ShaderNodeNormalMap")
        nt.set(nm.inputs["Color"], tn.outputs["Color"])
        nt.set(bsdf.inputs["Normal"], nm.outputs["Normal"])
    o = nt.node("ShaderNodeOutputMaterial")
    nt.set(o.inputs["Surface"], bsdf.outputs["BSDF"])
    return m


def flat_material(name, hexcol, rough=0.5, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    return m


def set_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0


# ------------------------------------------------------------------ export + bounds
def roblox_box(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)])
    hi = Vector([max(v[i] for v in vs) for i in range(3)])
    return {
        "size": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
        "center": [round((hi.x + lo.x) / 2, 3), round((hi.z + lo.z) / 2, 3), round(-(hi.y + lo.y) / 2, 3)],
    }


def export(objects, fbx_name):
    """FBX with the house settings (build_gumball.py), meshes half-turned for Roblox."""
    half = Matrix.Rotation(math.pi, 4, "Z")
    for o in objects:
        o.data.transform(half)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(OUT, fbx_name)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH"},
        mesh_smooth_type="OFF", use_triangles=True, axis_forward="-Z", axis_up="Y",
        apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    for o in objects:
        o.data.transform(half)
    print(f"[export] {path}")
    return path


def write_bounds(name, data):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print(f"[bounds] {path}")


def finalize_mesh(ob, weld=True, angle=None):
    """Triangulate-ready cleanup: weld, recalc nothing (orientation is built in), smooth,
    weighted normals off (Blender 4.1+ uses face-corner smooth by default)."""
    if weld:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.to_mesh(ob.data)
        bm.free()
    ob.data.update()


def report_tris(objects, label):
    total = 0
    for o in objects:
        t = tri_count(o)
        total += t
        print(f"[{label}] {o.name}: {t} tris")
    print(f"[{label}] TOTAL {total} tris")
    return total


# ------------------------------------------------------------------ previews
def look(cam, loc, target, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def studio(center, R, sky=False, floor_z=None, floor_col=(0.62, 0.6, 0.6, 1)):
    """Soft studio: pale neutral gradient world (or a sky), key/fill/rim/top area lights
    scaled to a model of radius R around center. Returns the camera."""
    sc = bpy.context.scene
    world = bpy.data.worlds.new("Studio")
    sc.world = world
    world.use_nodes = True
    wn, wl = world.node_tree.nodes, world.node_tree.links
    wn.clear()
    tc = wn.new("ShaderNodeTexCoord")
    sep = wn.new("ShaderNodeSeparateXYZ")
    wl.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = wn.new("ShaderNodeValToRGB")
    if sky:
        ramp.color_ramp.elements[0].position = 0.45
        ramp.color_ramp.elements[0].color = (0.55, 0.78, 0.95, 1)
        ramp.color_ramp.elements[1].position = 0.85
        ramp.color_ramp.elements[1].color = (0.13, 0.42, 0.85, 1)
    else:
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (0.32, 0.31, 0.33, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (0.80, 0.82, 0.88, 1)
    wl.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = wn.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0 if sky else 0.7
    wl.new(ramp.outputs["Color"], bg.inputs["Color"])
    # the camera sees a flat pale backdrop; reflections see the gradient
    lp = wn.new("ShaderNodeLightPath")
    flatbg = wn.new("ShaderNodeBackground")
    flatbg.inputs["Color"].default_value = (0.16, 0.45, 0.95, 1) if sky else (0.78, 0.78, 0.80, 1)
    flatbg.inputs["Strength"].default_value = 1.0
    mixs = wn.new("ShaderNodeMixShader")
    wl.new(lp.outputs["Is Camera Ray"], mixs.inputs[0])
    wl.new(bg.outputs[0], mixs.inputs[1])
    wl.new(flatbg.outputs[0], mixs.inputs[2])
    wo = wn.new("ShaderNodeOutputWorld")
    wl.new(mixs.outputs[0], wo.inputs["Surface"])

    center = Vector(center)

    def lamp(name, off, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy * R * R
        ld.color = color
        ld.shape = "DISK"
        ld.size = size * R
        lo = bpy.data.objects.new(name, ld)
        lo.location = center + Vector(off) * R
        lo.rotation_euler = (center - lo.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)

    lamp("Key", (-1.6, 2.0, 2.4), 150, 1.6, (1.0, 0.97, 0.93))
    lamp("Fill", (2.4, 1.4, 1.0), 45, 2.2, (0.92, 0.95, 1.0))
    lamp("Rim", (0.6, -2.4, 1.8), 80, 1.6)
    lamp("Top", (0, 0, 3.0), 30, 3.0)

    if floor_z is not None:
        me = bpy.data.meshes.new("Floor")
        fb = bmesh.new()
        bmesh.ops.create_grid(fb, x_segments=1, y_segments=1, size=R * 30)
        bmesh.ops.translate(fb, vec=Vector((center.x, center.y, floor_z - 0.002)), verts=fb.verts)
        fb.to_mesh(me)
        fb.free()
        fm = bpy.data.materials.new("FloorMat")
        fm.use_nodes = True
        fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = floor_col
        fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
        me.materials.append(fm)
        fo = bpy.data.objects.new("Floor", me)
        sc.collection.objects.link(fo)
        fo["preview_only"] = True

    cd = bpy.data.cameras.new("Cam")
    cd.clip_end = 20000
    cd.clip_start = 0.05
    cam = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
    return cam


def player_block(loc):
    """Grey 2 x 1 x 5 stud 'player' for scale (preview only)."""
    me = bpy.data.meshes.new("Player")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((2, 1, 5)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc) + Vector((0, 0, 2.5)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(flat_material("PlayerGrey", "#8C8C96", 0.6))
    ob = bpy.data.objects.new("Player", me)
    bpy.context.scene.collection.objects.link(ob)
    ob["preview_only"] = True
    return ob


def render(path, w, h, samples=None):
    sc = bpy.context.scene
    setup_cycles(samples or (16 if QUICK else 64))
    k = min(1.0, 1280 / w, 960 / h)  # owner's machine: never bigger than 1280 x 960
    sc.render.resolution_x, sc.render.resolution_y = int(w * k), int(h * k)
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[render] {path}")
    return path


def compose(paths, out, cols=2):
    """Tile same-size PNGs into one image (row-major, top-left first)."""
    ims = [bpy.data.images.load(p) for p in paths]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    arr = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = k // cols, k % cols
        arr[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = px
    outim = bpy.data.images.new("compose", cols * w, rows * h, alpha=False)
    outim.pixels = arr.ravel()
    outim.filepath_raw = out
    outim.file_format = "PNG"
    outim.save()
    for im in ims:
        bpy.data.images.remove(im)
    bpy.data.images.remove(outim)
    print(f"[compose] {out}")


def thumb(src, out, w=256, h=192):
    im = bpy.data.images.load(src)
    im.scale(w, h)
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    print(f"[thumb] {out}")
