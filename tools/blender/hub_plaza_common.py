# Shared helpers for the Batch B "Plaza kit" scripts (hub_plaza_*.py): shape builders,
# zone materials, texture baking, Roblox FBX export, bounds files and preview renders.
# Not run by itself. Each hub_plaza_<asset>.py does `import hub_plaza_common as C`.
#
# House rules (docs/art_plan.md sections 1-2):
#   * 1 Blender unit = 1 stud, Z up, model stands on the origin, front faces +Y.
#   * Export like kit.py: meshes turned half round about Z for the export, so in Roblox
#     X = Blender X, Y = Blender Z, Z = -Blender Y (this is what bounds.json uses).
#   * Textured meshes: one atlas per texture set (colour + normal (OpenGL) + roughness),
#     baked from object-space procedural zone materials, soft AO painted into the colour.
#   * Tint meshes are neutral near-white; Glow meshes are flat Neon, no texture.

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "art", "hub_plaza")
PREV = os.path.join(ROOT, "art", "previews")
TMP = os.path.join(OUT, "_tmp")
QUICK = os.environ.get("PLAZA_QUICK") == "1"
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

# palette (docs/art_plan.md), sRGB hex
PAL = {
    "red": "#E62D46", "cream": "#FFFCFA", "pink": "#FFB4D2", "tilepink": "#FFD6E6",
    "mint": "#6EDCBE", "lemon": "#FFC832", "gold": "#FFC83C", "grass": "#7DD75A",
    "choc": "#6E412D", "navy": "#283250", "glow": "#BE1E5A", "tint": "#F6F4F3",
}
PAD_COLOURS = [("Red", "#E12D3C"), ("Blue", "#2878E6"), ("Yellow", "#F0B914"), ("Green", "#32AF46")]
# Neon suggestions for the pad glow ring: dark, saturated versions (bright Neon blows out)
PAD_GLOWS = {"Red": "#B4142D", "Blue": "#145ABE", "Yellow": "#BE7D00", "Green": "#198C2D"}


def rgb255(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lin(h):
    """sRGB hex -> linear (r, g, b)."""
    out = []
    for c in rgb255(h):
        x = c / 255
        out.append(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92)
    return tuple(out)


# ------------------------------------------------------------------ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    # CPU only (owner's fanless Mac crashed with GPU renders); one Blender process at a time
    sc.cycles.device = "CPU"
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 6
    return sc


# ------------------------------------------------------------------ shapes
def circle2d(r, segs, arc=None, turn=0.0):
    if arc:
        a0, a1 = arc
        return [(r * math.cos(a0 + (a1 - a0) * i / segs), r * math.sin(a0 + (a1 - a0) * i / segs)) for i in range(segs + 1)]
    return [(r * math.cos(turn + 2 * math.pi * i / segs), r * math.sin(turn + 2 * math.pi * i / segs)) for i in range(segs)]


def rrect2d(a, b, d, k):
    """Ring around a core rectangle (half sizes a, b) at offset d: a rounded rectangle whose
    corner radius is d. k = segments per corner (k + 1 points per corner)."""
    pts = []
    for (cx, cy), a0 in (((a, b), 0), ((-a, b), 90), ((-a, -b), 180), ((a, -b), 270)):
        for i in range(k + 1):
            t = math.radians(a0 + 90 * i / k)
            pts.append((cx + d * math.cos(t), cy + d * math.sin(t)))
    return pts


def square2d(h):
    """Square ring with mitred corners (half size h): 4 points."""
    return [(h, h), (-h, h), (-h, -h), (h, -h)]


def frame(origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0)):
    """A local frame: ring points (p, q) map to origin + u*p + v*q, the profile height w runs
    along w = u x v."""
    u, v = Vector(u).normalized(), Vector(v).normalized()
    return (Vector(origin), u, v, u.cross(v))


class MeshBuilder:
    """One output mesh made of several zones (each zone becomes a bake material)."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.zones = []

    def zi(self, zone):
        if zone not in self.zones:
            self.zones.append(zone)
        return self.zones.index(zone)

    def face(self, verts, zone, smooth=True):
        f = self.bm.faces.new(verts)
        f.material_index = self.zi(zone)
        f.smooth = smooth
        return f

    def lathe(self, profile, ring, fr=None, zone="body", closed=True, cap_first=False, cap_last=False, smooth=True):
        """profile = [(d, w) or (d, w, zone), ...]; ring(d) -> 2D points around the axis.
        d <= 1e-6 makes a single apex point. Two identical consecutive points = hard edge.
        A zone given on a point applies to the band starting there (and later ones)."""
        o, U, V, W = fr or frame()
        rows, zones = [], []
        z = zone
        for p in profile:
            d, w = p[0], p[1]
            if len(p) > 2:
                z = p[2]
            zones.append(z)
            if d <= 1e-6:
                rows.append([self.bm.verts.new(o + W * w)])
            else:
                rows.append([self.bm.verts.new(o + U * x + V * y + W * w) for x, y in ring(d)])
        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]
            pa, pb = profile[i], profile[i + 1]
            if abs(pa[0] - pb[0]) < 1e-7 and abs(pa[1] - pb[1]) < 1e-7:
                continue
            n = max(len(a), len(b))
            last = n if closed else n - 1
            for j in range(last):
                k = (j + 1) % n
                if len(a) == 1:
                    vs = (a[0], b[j], b[k])
                elif len(b) == 1:
                    vs = (a[j], a[k], b[0])
                else:
                    vs = (a[j], a[k], b[k], b[j])
                self.face(vs, zones[i], smooth)
        if cap_first and len(rows[0]) > 2:
            self.face(rows[0], zones[0], smooth)
        if cap_last and len(rows[-1]) > 2:
            self.face(rows[-1], zones[-2] if len(zones) > 1 else zone, smooth)

    def tube(self, points, radius, segs=8, zone="body", caps=False, smooth=True):
        """A round tube along a path [(x, y, z), ...]."""
        pts = [Vector(q) for q in points]
        n = len(pts)
        normal, rows = None, []
        rads = radius if isinstance(radius, (list, tuple)) else [radius] * n
        for i, q in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            if normal is None:
                normal = t.cross(Vector((0, 0, 1)))
                if normal.length < 1e-4:
                    normal = Vector((1, 0, 0))
            normal = (normal - t * normal.dot(t)).normalized()
            side = t.cross(normal)
            rows.append([self.bm.verts.new(q + (normal * math.cos(2 * math.pi * k / segs) + side * math.sin(2 * math.pi * k / segs)) * rads[i]) for k in range(segs)])
        for a, b in zip(rows, rows[1:]):
            for k in range(segs):
                j = (k + 1) % segs
                self.face((a[k], a[j], b[j], b[k]), zone, smooth)
        if caps:
            self.face(rows[0][::-1], zone, smooth)
            self.face(rows[-1], zone, smooth)

    def transform(self, matrix, since):
        """Move the verts made after `since` (a len(bm.verts) mark)."""
        self.bm.verts.ensure_lookup_table()
        vs = [self.bm.verts[i] for i in range(since, len(self.bm.verts))]
        bmesh.ops.transform(self.bm, matrix=matrix, verts=vs)

    def mark(self):
        return len(self.bm.verts)

    def build(self, mats, sharp_angle=50, weighted=True):
        """Make the object: recalc normals, triangulate, zone materials, weighted normals."""
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        loose = [v for v in bm.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(bm, geom=loose, context="VERTS")
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        for z in self.zones:
            me.materials.append(mats[z])
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.set_sharp_from_angle(angle=math.radians(sharp_angle))
        if weighted:
            mod = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
            mod.mode = "FACE_AREA"
            mod.weight = 50
            mod.keep_sharp = True
            apply_mods(ob)
        return ob


def apply_mods(ob):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ------------------------------------------------------------------ node helper
class NB:
    """Tiny node-graph builder for zone materials."""

    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.n = self.nt.nodes
        self.l = self.nt.links
        self.n.clear()
        tc = self.n.new("ShaderNodeTexCoord")
        self.obj = tc.outputs["Object"]
        sep = self.n.new("ShaderNodeSeparateXYZ")
        self.l.new(self.obj, sep.inputs[0])
        self.x, self.y, self.z = sep.outputs[0], sep.outputs[1], sep.outputs[2]

    def _in(self, sock, val):
        if isinstance(val, (int, float)):
            sock.default_value = val
        else:
            self.l.new(val, sock)

    def m(self, op, a, b=0.0, c=None, clamp=False):
        node = self.n.new("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        self._in(node.inputs[0], a)
        self._in(node.inputs[1], b)
        if c is not None:
            self._in(node.inputs[2], c)
        return node.outputs[0]

    def add(self, a, b): return self.m("ADD", a, b)
    def sub(self, a, b): return self.m("SUBTRACT", a, b)
    def mul(self, a, b): return self.m("MULTIPLY", a, b)
    def div(self, a, b): return self.m("DIVIDE", a, b)
    def mn(self, a, b): return self.m("MINIMUM", a, b)
    def mx(self, a, b): return self.m("MAXIMUM", a, b)
    def ab(self, a): return self.m("ABSOLUTE", a)
    def sqrt(self, a): return self.m("SQRT", self.mx(a, 0.0))
    def sin(self, a): return self.m("SINE", a)
    def cos(self, a): return self.m("COSINE", a)
    def atan2(self, y, x): return self.m("ARCTAN2", y, x)
    def fract(self, a): return self.m("FRACT", a)
    def floor(self, a): return self.m("FLOOR", a)
    def clamp01(self, a): return self.m("ADD", a, 0.0, clamp=True)
    def pw(self, a, b): return self.m("POWER", self.mx(a, 0.0), b)

    def smooth(self, x, e0, e1):
        """smoothstep from e0 to e1 (e0 > e1 allowed: falls)."""
        node = self.n.new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP"
        node.clamp = True
        self._in(node.inputs["Value"], x)
        node.inputs["From Min"].default_value = e0
        node.inputs["From Max"].default_value = e1
        node.inputs["To Min"].default_value = 0.0
        node.inputs["To Max"].default_value = 1.0
        return node.outputs["Result"]

    def length2(self, x, y):
        return self.sqrt(self.add(self.mul(x, x), self.mul(y, y)))

    def lerp(self, a, b, t):
        """float lerp."""
        return self.add(a, self.mul(self.sub(b, a), t))

    def rgb(self, c):
        node = self.n.new("ShaderNodeRGB")
        node.outputs[0].default_value = tuple(c) + (1.0,)
        return node.outputs[0]

    def mixc(self, a, b, t):
        """colour lerp; a, b are sockets or linear tuples."""
        node = self.n.new("ShaderNodeMix")
        node.data_type = "RGBA"
        node.blend_type = "MIX"
        self._in(node.inputs["Factor"], t)
        for idx, val in ((6, a), (7, b)):
            if isinstance(val, tuple):
                node.inputs[idx].default_value = tuple(val) + (1.0,)
            else:
                self.l.new(val, node.inputs[idx])
        return node.outputs[2]

    def scalec(self, c, s):
        node = self.n.new("ShaderNodeMix")
        node.data_type = "RGBA"
        node.blend_type = "MULTIPLY"
        node.inputs["Factor"].default_value = 1.0
        if isinstance(c, tuple):
            node.inputs[6].default_value = tuple(c) + (1.0,)
        else:
            self.l.new(c, node.inputs[6])
        comb = self.n.new("ShaderNodeCombineXYZ")
        for i in range(3):
            self._in(comb.inputs[i], s)
        self.l.new(comb.outputs[0], node.inputs[7])
        return node.outputs[2]

    def ao(self, distance):
        node = self.n.new("ShaderNodeAmbientOcclusion")
        node.samples = 16 if QUICK else 32
        node.inputs["Distance"].default_value = distance
        return node.outputs["AO"]

    def hexdomes(self, x, y, spacing, radius):
        """Height 0..1 of round domes on a hex grid in the x-y plane."""
        best = None
        sy = spacing * math.sqrt(3)
        for ox, oy in ((0.0, 0.0), (spacing / 2, sy / 2)):
            lx = self.div(self.sub(x, ox), spacing)
            ly = self.div(self.sub(y, oy), sy)
            fx = self.mul(self.sub(lx, self.floor(self.add(lx, 0.5))), spacing)
            fy = self.mul(self.sub(ly, self.floor(self.add(ly, 0.5))), sy)
            d = self.length2(fx, fy)
            best = d if best is None else self.mn(best, d)
        t = self.clamp01(self.sub(1.0, self.pw(self.div(best, radius), 2.0)))
        return self.sqrt(t)

    def spiral(self, x, y, z, radius, n=2, angle_deg=38, phase=0.0, sharp=7.0):
        """Candy-cane stripe mask (0 = white, 1 = red) around the z axis: n red stripes,
        leaning at angle_deg from horizontal (the same angle at any post radius)."""
        ang = self.atan2(y, x)
        pitch = 2 * math.pi * radius * math.tan(math.radians(angle_deg))  # rise per turn
        t = self.add(self.mul(ang, n / (2 * math.pi)), self.mul(z, -n / pitch))
        s = self.sin(self.mul(self.add(t, phase), 2 * math.pi))
        return self.clamp01(self.add(self.mul(s, sharp), 0.5))


# ------------------------------------------------------------------ zone materials
def zone_material(name, color, rough, height=None, ao=0.22, ao_dist=0.6, grad=0.05, zr=(0.0, 1.0), bump=1.0):
    """A bake material. color: hex / linear tuple / fn(nb) -> colour socket.
    rough: float or fn(nb) -> float socket. height: fn(nb) -> float socket (studs).
    The baked colour = colour x soft AO x a gentle top-to-bottom gradient."""
    mat = bpy.data.materials.new(name)
    nb = NB(mat)
    if callable(color):
        base = color(nb)
    else:
        base = nb.rgb(lin(color) if isinstance(color, str) else color)
    shade = nb.sub(1.0, nb.mul(nb.sub(1.0, nb.ao(ao_dist)), ao)) if ao > 0 else 1.0
    if grad > 0:
        zn = nb.clamp01(nb.div(nb.sub(nb.z, zr[0]), max(zr[1] - zr[0], 1e-3)))
        g = nb.sub(1.0, nb.mul(nb.sub(1.0, zn), grad))
        shade = g if shade == 1.0 else nb.mul(shade, g)
    albedo = nb.scalec(base, shade) if shade != 1.0 else base
    r = rough(nb) if callable(rough) else rough
    bsdf = nb.n.new("ShaderNodeBsdfPrincipled")
    nb.l.new(albedo, bsdf.inputs["Base Color"])
    nb._in(bsdf.inputs["Roughness"], r)
    if height is not None:
        b = nb.n.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        b.inputs["Distance"].default_value = 1.0
        nb.l.new(height(nb), b.inputs["Height"])
        nb.l.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    out = nb.n.new("ShaderNodeOutputMaterial")
    nb.l.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat["albedo"] = albedo.node.name
    mat["albedo_out"] = albedo.identifier if hasattr(albedo, "identifier") else ""
    # keep handles for the bake passes
    mat["_bsdf"] = bsdf.name
    mat["_out"] = out.name
    BAKE_SOCKETS[mat.name] = (albedo, r)
    return mat


BAKE_SOCKETS = {}


def flat_material(name, hexcol, rough=0.35, emit=0.0, alpha=1.0):
    """Preview material for flat-colour / Neon / Glass meshes."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    c = lin(hexcol) + (1.0,)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = emit
    return mat


# ------------------------------------------------------------------ UV + bake
def unwrap(objs, margin=0.02, angle=55):
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, margin_method="FRACTION", margin=margin,
                                shape_method="CONCAVE")
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake_set(set_name, objs, size, samples=None, margin_px=None):
    """Bake colour, roughness and normal maps for objs (sharing one atlas), save
    <set_name>_color/_roughness/_normal.png in OUT, and give every object one final material."""
    sc = bpy.context.scene
    sc.cycles.samples = min(samples or (16 if QUICK else 48), 64)
    sc.render.bake.margin = margin_px or max(3, size // 128)
    sc.render.bake.margin_type = "EXTEND"
    mats = []
    for o in objs:
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
    for o in sc.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

    def run(kind, btype, colorspace, sock_index=None):
        img = bpy.data.images.new(f"{set_name}_{kind}", size, size, alpha=False, float_buffer=(btype == "NORMAL"))
        img.colorspace_settings.name = colorspace
        temp = []
        for m in mats:
            nt = m.node_tree
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            for n in nt.nodes:
                n.select = False
            tex.select = True
            nt.nodes.active = tex
            out = nt.nodes[m["_out"]]
            em = None
            if sock_index is not None:
                em = nt.nodes.new("ShaderNodeEmission")
                src = BAKE_SOCKETS[m.name][sock_index]
                if isinstance(src, (int, float)):
                    em.inputs["Color"].default_value = (src, src, src, 1)
                else:
                    nt.links.new(src, em.inputs["Color"])
                nt.links.new(em.outputs[0], out.inputs["Surface"])
            temp.append((m, tex, em))
        if btype == "NORMAL":
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        else:
            bpy.ops.object.bake(type=btype)
        for m, tex, em in temp:
            nt = m.node_tree
            if em:
                nt.nodes.remove(em)
                nt.links.new(nt.nodes[m["_bsdf"]].outputs[0], nt.nodes[m["_out"]].inputs["Surface"])
            nt.nodes.remove(tex)
        path = os.path.join(OUT, f"{set_name}_{kind}.png")
        if img.is_float:  # save the normal map as an 8-bit PNG (Roblox / plan rule)
            byte = bpy.data.images.new(img.name + "_8", size, size, alpha=False)
            byte.colorspace_settings.name = "Non-Color"
            px = np.empty(size * size * 4, dtype=np.float32)
            img.pixels.foreach_get(px)
            byte.pixels.foreach_set(px)
            bpy.data.images.remove(img)
            img = byte
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        return path

    run("color", "EMIT", "sRGB", 0)
    run("roughness", "EMIT", "Non-Color", 1)
    run("normal", "NORMAL", "Non-Color")
    maps = {}
    for k in ("color", "roughness", "normal"):
        im = bpy.data.images.load(os.path.join(OUT, f"{set_name}_{k}.png"))
        im.colorspace_settings.name = "sRGB" if k == "color" else "Non-Color"
        maps[k] = im
    fin = final_material(set_name, maps)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(fin)
    return fin, maps


def final_material(name, maps, tint=(1, 1, 1), flat=False):
    """What Roblox's SurfaceAppearance does: colour map x tint colour, roughness, normal."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    n, l = nt.nodes, nt.links
    n.clear()
    uv = n.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    tcol = n.new("ShaderNodeTexImage")
    tcol.image = maps["color"]
    l.new(uv.outputs[0], tcol.inputs[0])
    mix = n.new("ShaderNodeMix")
    mix.name = "Tint"
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[7].default_value = tuple(tint) + (1,)
    l.new(tcol.outputs["Color"], mix.inputs[6])
    b = n.new("ShaderNodeBsdfPrincipled")
    l.new(mix.outputs[2], b.inputs["Base Color"])
    if flat:
        b.inputs["Roughness"].default_value = 0.45
    else:
        tr = n.new("ShaderNodeTexImage")
        tr.image = maps["roughness"]
        l.new(uv.outputs[0], tr.inputs[0])
        l.new(tr.outputs["Color"], b.inputs["Roughness"])
        tn = n.new("ShaderNodeTexImage")
        tn.image = maps["normal"]
        l.new(uv.outputs[0], tn.inputs[0])
        nm = n.new("ShaderNodeNormalMap")
        l.new(tn.outputs["Color"], nm.inputs["Color"])
        l.new(nm.outputs[0], b.inputs["Normal"])
    o = n.new("ShaderNodeOutputMaterial")
    l.new(b.outputs[0], o.inputs["Surface"])
    return mat


def tinted_copy(mat, hexcol, name=None):
    m = mat.copy()
    m.name = name or (mat.name + "_" + hexcol)
    m.node_tree.nodes["Tint"].inputs[7].default_value = lin(hexcol) + (1,)
    return m


# ------------------------------------------------------------------ export
HALF = Matrix.Rotation(math.pi, 4, "Z")


def export_fbx(path, objs):
    """kit.py-style export: meshes turned half round for the export (Roblox imports an FBX
    turned half round), so in game X = Blender X and Z = -Blender Y."""
    for o in objs:
        o.location = (0, 0, 0)
    # check that custom normals turn with the mesh
    probe = objs[0].data
    before = [Vector(n.vector) for n in probe.corner_normals[:50]]
    for o in objs:
        o.data.transform(HALF)
    after = [Vector(n.vector) for n in probe.corner_normals[:50]]
    for a, b in zip(before, after):
        exp = HALF.to_3x3() @ a
        assert (exp - b).length < 1e-3, "custom normals did not turn with the mesh"
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH"},
        mesh_smooth_type="OFF", use_triangles=True, axis_forward="-Z", axis_up="Y",
        apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    for o in objs:
        o.data.transform(HALF)
    print("exported", path)


def bounds_entry(ob, **extra):
    vs = [v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)])
    hi = Vector([max(v[i] for v in vs) for i in range(3)])
    e = {
        "size": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
        "center": [round((hi.x + lo.x) / 2, 3), round((hi.z + lo.z) / 2, 3), round(-(hi.y + lo.y) / 2, 3)],
        "tris": tris(ob),
    }
    e.update(extra)
    return e


def write_bounds(path, entries, notes=None):
    data = {"_axes": "Roblox studs: X = Blender X, Y = up (Blender Z), Z = -Blender Y. 'center' is the middle "
                     "of each mesh's box, measured from the model origin (bottom centre of the footprint, on the floor).",
            "_front": "Front faces Roblox -Z (Blender +Y): CFrame.lookAt(pos, pos + faceDirection) points it.",
            }
    if notes:
        data["_notes"] = notes
    data.update(entries)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print("wrote", path)


def report(objs, budget=None):
    total = 0
    for o in objs:
        t = tris(o)
        total += t
        lim = (budget or {}).get(o.name)
        flag = "" if lim is None else ("  OK (< %d)" % lim if t < lim else "  OVER BUDGET (%d)" % lim)
        d = o.dimensions
        print(f"  {o.name:24s} {t:5d} tris   {d.x:.2f} x {d.y:.2f} x {d.z:.2f}{flag}")
    print(f"  total {total} tris")
    return total


# ------------------------------------------------------------------ preview studio
def studio(center, radius, floor_z=0.0, floor_col=(0.62, 0.6, 0.6)):
    sc = bpy.context.scene
    world = bpy.data.worlds.new("Studio")
    sc.world = world
    world.use_nodes = True
    wn, wl = world.node_tree.nodes, world.node_tree.links
    wn.clear()
    tc = wn.new("ShaderNodeTexCoord")
    sep = wn.new("ShaderNodeSeparateXYZ")
    wl.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = wn.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (0.30, 0.30, 0.33, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.85, 0.88, 0.95, 1)
    wl.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = wn.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.9
    wl.new(ramp.outputs[0], bg.inputs[0])
    wo = wn.new("ShaderNodeOutputWorld")
    wl.new(bg.outputs[0], wo.inputs[0])

    c = Vector(center)
    R = max(radius, 2.0)
    bpy.ops.mesh.primitive_plane_add(size=R * 40, location=(c.x, c.y, floor_z - 0.002))
    fl = bpy.context.active_object
    fl.name = "StudioFloor"
    fm = bpy.data.materials.new("StudioFloor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = floor_col + (1,)
    fb.inputs["Roughness"].default_value = 0.4
    fl.data.materials.append(fm)

    def light(name, off, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.shape = "DISK"
        ld.size = size * R
        ld.energy = energy * R * R
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = c + Vector(off) * R
        lo.rotation_euler = (c - lo.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)

    light("Key", (-1.4, 1.9, 2.2), 55, 1.4, (1.0, 0.97, 0.93))
    light("Fill", (2.4, 1.2, 0.9), 16, 2.2, (0.92, 0.95, 1.0))
    light("Rim", (0.6, -2.4, 1.6), 30, 2.0)
    light("Top", (0, 0, 3.0), 12, 3.0)
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.cycles.use_denoising = True
    return fl


def player_block(at):
    """The grey 2 x 1 x 5 'player' for scale."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(2, 1, 5), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(at) + Vector((0, 0, 2.5)), verts=bm.verts)
    me = bpy.data.meshes.new("PlayerBlock")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("PlayerBlock", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("PlayerGrey")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.32, 0.32, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    me.materials.append(m)
    return ob


def camera():
    sc = bpy.context.scene
    if sc.camera:
        return sc.camera
    cd = bpy.data.cameras.new("Cam")
    cd.clip_end = 10000
    cam = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def shoot(path, target, direction, dist, lens=50, res=(1280, 960), samples=None):
    sc = bpy.context.scene
    cam = camera()
    cam.data.lens = lens
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = min(samples or (16 if QUICK else 64), 64)
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)
    return path


def fit_dist(radius, lens, aspect=4 / 3, margin=1.15):
    fov = 2 * math.atan(18 / lens) if aspect >= 1 else 2 * math.atan(18 / lens)
    fov_v = 2 * math.atan(math.tan(fov / 2) / aspect) if aspect >= 1 else fov
    return radius * margin / math.sin(min(fov, fov_v) / 2)


def stitch(paths, cols, out):
    """Put same-size PNGs into one grid image (row-major, top row first)."""
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size
    rows = math.ceil(len(imgs) / cols)
    canvas = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, im in enumerate(imgs):
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h  # blender pixel rows start at the bottom
        canvas[y0:y0 + h, c * w:(c + 1) * w] = px
    res = bpy.data.images.new(os.path.basename(out), cols * w, rows * h, alpha=False)
    res.pixels.foreach_set(canvas.ravel())
    res.filepath_raw = out
    res.file_format = "PNG"
    res.save()
    for im in imgs:
        bpy.data.images.remove(im)
    bpy.data.images.remove(res)
    print("stitched", out)


def backface_check(objs):
    """Debug material: front faces white, back faces red. Returns the old materials."""
    m = bpy.data.materials.new("BackfaceCheck")
    m.use_nodes = True
    nt = m.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.9, 0.9, 0.9, 1)
    mix.inputs[7].default_value = (1, 0, 0, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], nt.nodes["Principled BSDF"].inputs["Base Color"])
    old = {}
    for o in objs:
        old[o.name] = list(o.data.materials)
        o.data.materials.clear()
        o.data.materials.append(m)
    return old


def restore_mats(objs, old):
    for o in objs:
        o.data.materials.clear()
        for m in old[o.name]:
            o.data.materials.append(m)


def count_backfaces_from(objs, origin_dirs, dist=200):
    """Rough numeric check: cast rays from points around the model; count hits on faces whose
    normal points away from the ray (we see their back). 0 means no flipped faces seen."""
    deps = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    bad = 0
    hits = 0
    names = {o.name for o in objs}
    for (o, d) in origin_dirs:
        ok, loc, nrm, idx, ob, _ = sc.ray_cast(deps, Vector(o), Vector(d).normalized(), distance=dist)
        if ok and ob.name in names:
            hits += 1
            if nrm.dot(Vector(d)) > 0:
                bad += 1
    return bad, hits


def ray_grid(center, radius, n=24):
    """Rays aimed at the model from a sphere of viewpoints (upper half + sides)."""
    rays = []
    c = Vector(center)
    for i in range(n):
        for j in range(1, 7):
            th = 2 * math.pi * i / n
            el = math.radians(-10 + j * 14)
            dirv = Vector((math.cos(th) * math.cos(el), math.sin(th) * math.cos(el), math.sin(el)))
            start = c + dirv * radius * 3
            for du in (-0.6, -0.3, 0, 0.3, 0.6):
                for dv in (-0.6, -0.3, 0, 0.3, 0.6):
                    side = dirv.cross(Vector((0, 0, 1))).normalized()
                    up = side.cross(dirv).normalized()
                    tgt = c + side * du * radius + up * dv * radius
                    rays.append((start, tgt - start))
    return rays


def save_blend(path, keep):
    """Save a .blend holding only the given objects (preview stuff is added afterwards)."""
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    print("saved", path)


# ------------------------------------------------------------------ standard previews
def flat_copy(mat):
    """Colour-only version of a material (normal and roughness maps off), as on low phone graphics."""
    m = mat.copy()
    m.name = mat.name + "_flat"
    if not m.use_nodes:
        return m
    nt = m.node_tree
    for b in [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]:
        for key in ("Roughness", "Normal"):
            for lk in list(b.inputs[key].links):
                nt.links.remove(lk)
        if b.inputs["Emission Strength"].default_value == 0:
            b.inputs["Roughness"].default_value = 0.45
    return m


def world_bounds(objs):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i])
                hi[i] = max(hi[i], w[i])
    return lo, hi


def standard_previews(prefix, objs, block_at, beauty_dir=(0.6, 1.0, 0.55), lens=50, turn_elev=0.28, aim_z=None):
    """<prefix>_beauty (1280x960, with the player block), _thumb (256x192), _flat (colour only),
    _turn (front, right, back, left in one 2 x 2 image)."""
    os.makedirs(TMP, exist_ok=True)
    block = player_block(block_at)
    lo, hi = world_bounds(objs + [block])
    c = (lo + hi) / 2
    if aim_z is not None:
        c.z = aim_z
    r = (hi - lo).length / 2
    dist = fit_dist(r, lens, margin=1.02)
    base = os.path.join(PREV, prefix)
    shoot(base + "_beauty.png", c, beauty_dir, dist, lens)
    shoot(base + "_thumb.png", c, beauty_dir, dist, lens, res=(256, 192))
    swaps = {}
    for o in objs:
        swaps[o.name] = list(o.data.materials)
        flats = [flat_copy(m) for m in o.data.materials]
        o.data.materials.clear()
        for m in flats:
            o.data.materials.append(m)
    shoot(base + "_flat.png", c, beauty_dir, dist, lens)
    restore_mats(objs, swaps)
    block.hide_render = True
    lo, hi = world_bounds(objs)
    c = (lo + hi) / 2
    r = (hi - lo).length / 2
    dist = fit_dist(r, lens, margin=1.0)
    views = []
    for name, d in (("front", (0, 1, turn_elev)), ("right", (1, 0, turn_elev)), ("back", (0, -1, turn_elev)), ("left", (-1, 0, turn_elev))):
        views.append(shoot(os.path.join(TMP, f"{prefix}_{name}.png"), c, d, dist, lens, res=(640, 480)))
    stitch(views, 2, base + "_turn.png")
    bpy.data.objects.remove(block)
