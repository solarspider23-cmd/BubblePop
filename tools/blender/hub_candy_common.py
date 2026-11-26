# Shared helpers for Batch C "Candy corner" (booth, chest, pit, jar).
# Used by tools/blender/hub_candy_*.py. Background Blender only:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_candy_booth.py [-- fast]
#
# House rules (docs/art_plan.md sections 1-2, same axes/export as kit.py and the recycler):
#   * 1 Blender unit = 1 stud, Z up, model stands on the origin (bottom centre), front faces +Y.
#   * FBX: meshes turned half round about Z for export (Roblox imports FBX turned half round),
#     axis_forward -Z, axis_up Y, FBX_SCALE_ALL, triangulated, path_mode STRIP, no colours.
#   * bounds.json in Roblox axes: X = Blender X, Y = Blender Z, Z = -Blender Y.
#
# How a model is made:
#   m = Model("Hub_Jar", texset)          # texset = TexSet(...) shared by models baked together
#   m.zone("Jar_Body", "tex")              # tex / glass / glow / shine / flat
#   m.add("Jar_Body", "gold", lathe(...))  # a piece = a bmesh, painted with one paint
#   build([m, ...]) -> objects, UVs, culls hidden faces, bakes the texture set, exports, previews
#
# Textures are computed in numpy from baked object-space position / normal / paint-id maps plus a
# Cycles AO bake, so every paint is a small Python function (stripes, quilting, coins...).
# Baked at 2x and averaged down for clean edges. Normal maps are OpenGL (Y+).

import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "art", "hub_candy")
PREV = os.path.join(ROOT, "art", "previews")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
NOPREV = "noprev" in ARGS
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

# ------------------------------------------------------------------ palette (docs/art_plan.md)
HEX = {
    "red": "#E62D46", "cream": "#FFFCFA", "pink": "#FFB4D2", "palepink": "#FFD6E6",
    "mint": "#6EDCBE", "lemon": "#FFC832", "gold": "#FFC83C", "grass": "#7DD75A",
    "choc": "#6E412D", "navy": "#283250", "glowpink": "#BE1E5A",
    "booth_pink": "#FF69AA", "booth_mint": "#46CDA5", "booth_lemon": "#F5B928",
    "gum_pink": "#FF78BE", "gum_purple": "#965AE6", "gum_blue": "#2878E6",
    "tintwhite": "#F7F6F5",  # neutral near-white for tinted pieces (brightness ~246)
}


def srgb_to_lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def hexrgb(h):
    h = HEX.get(h, h).lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lin(h):
    return tuple(float(x) for x in srgb_to_lin(np.array(hexrgb(h)) / 255.0))


# ------------------------------------------------------------------ shape builders (return bmesh)
def _new():
    return bmesh.new()


def _face(bm, verts, smooth=True):
    f = bm.faces.new(verts)
    f.smooth = smooth
    return f


def _fan(bm, ring, center, flip, smooth=False):
    c = bm.verts.new(center)
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        _face(bm, (c, b, a) if flip else (c, a, b), smooth)


def _rings_to_faces(bm, rings, profile, smooth=True, closed_around=True):
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        pa, pb = profile[k], profile[k + 1]
        if abs(pa[0] - pb[0]) < 1e-7 and abs(pa[1] - pb[1]) < 1e-7:
            continue  # doubled point: hard edge
        if len(a) == 1 or len(b) == 1:  # pole
            ring, pole, up = (b, a[0], True) if len(a) == 1 else (a, b[0], False)
            n = len(ring)
            for i in range(n):
                j = (i + 1) % n
                _face(bm, (pole, ring[j], ring[i]) if up else (ring[i], ring[j], pole), smooth)
            continue
        n = len(a)
        last = n if closed_around else n - 1
        for i in range(last):
            j = (i + 1) % n
            _face(bm, (a[i], a[j], b[j], b[i]), smooth)


def lathe(profile, segs=32, at=(0, 0, 0), squash=(1, 1), turn=0.0, ripple=None, caps=(True, True), smooth=True):
    """Spin [(r, z), ...] (bottom to top, outside surface first) round Z. A point given twice
    makes a hard edge. r == 0 at an end makes a pole. ripple(i) -> radius factor per spoke."""
    bm = _new()
    at = Vector(at)
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new(at + Vector((0, 0, z)))])
            continue
        ring = []
        for i in range(segs):
            a = turn + 2 * math.pi * i / segs
            k = ripple(i) if ripple else 1.0
            ring.append(bm.verts.new(at + Vector((r * k * math.cos(a) * squash[0], r * k * math.sin(a) * squash[1], z))))
        rings.append(ring)
    _rings_to_faces(bm, rings, profile, smooth)
    if caps[0] and len(rings[0]) > 1:
        _fan(bm, rings[0], at + Vector((0, 0, profile[0][1])), flip=True)
    if caps[1] and len(rings[-1]) > 1:
        _fan(bm, rings[-1], at + Vector((0, 0, profile[-1][1])), flip=False)
    return bm


def rrect_pts(w, d, r, steps=4):
    r = max(min(r, w / 2 - 1e-4, d / 2 - 1e-4), 0.005)
    hw, hd = w / 2 - r, d / 2 - r
    out = []
    for k, (cx, cy) in enumerate(((hw, hd), (-hw, hd), (-hw, -hd), (hw, -hd))):
        for i in range(steps + 1):
            a = math.pi / 2 * (k + i / steps)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def rlathe(w, d, rc, profile, steps=4, at=(0, 0, 0), caps=(True, True), smooth=True):
    """Rounded-rectangle 'lathe': profile [(inset, z), ...]; each ring is a w x d rounded
    rectangle (corner radius rc) shrunk by `inset`. Doubled point = hard edge."""
    bm = _new()
    at = Vector(at)
    rings = []
    for inset, z in profile:
        pts = rrect_pts(w - 2 * inset, d - 2 * inset, rc - inset, steps)
        rings.append([bm.verts.new(at + Vector((x, y, z))) for x, y in pts])
    _rings_to_faces(bm, rings, profile, smooth)
    if caps[0]:
        _fan(bm, rings[0], at + Vector((0, 0, profile[0][1])), flip=True)
    if caps[1]:
        _fan(bm, rings[-1], at + Vector((0, 0, profile[-1][1])), flip=False)
    return bm


def rbox(size, center=(0, 0, 0), r=0.2, segs=2, rot=None):
    bm = _new()
    made = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=made["verts"])
    if r > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=segs, profile=0.5, affect="EDGES", clamp_overlap=True)
    for f in bm.faces:
        f.smooth = True
    if rot:
        m = Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X")
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=m, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def ellipsoid(center, radii, u=12, v=8, rot=None):
    bm = _new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(radii), verts=bm.verts)
    for f in bm.faces:
        f.smooth = True
    if rot:
        m = Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X")
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=m, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return bm


def slab(outline, thick, bevel=0.1, bsegs=2, matrix=None, smooth_sides=True):
    """Flat outline [(u, v), ...] (counter-clockwise) extruded along local Z from -t/2 to +t/2,
    all edges bevelled, then moved by `matrix` (4x4)."""
    bm = _new()
    a = [bm.verts.new((u, v, -thick / 2)) for u, v in outline]
    b = [bm.verts.new((u, v, thick / 2)) for u, v in outline]
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        _face(bm, (a[i], a[j], b[j], b[i]), smooth_sides)
    _face(bm, a[::-1], False)
    _face(bm, b, False)
    if bevel > 0:
        cap_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6]
        res = bmesh.ops.bevel(bm, geom=cap_edges, offset=bevel, segments=bsegs, profile=0.5, affect="EDGES", clamp_overlap=True)
        for f in res["faces"]:
            f.smooth = True
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return bm


def sweep(section, frames, caps=(True, True), closed_path=False, smooth=True):
    """Closed section [(u, v), ...] (counter-clockwise when U is right and V is up) swept
    through frames [(origin, U, V), ...] (U and V may be scaled). Caps are fans."""
    bm = _new()
    rings = []
    for o, U, V in frames:
        o, U, V = Vector(o), Vector(U), Vector(V)
        rings.append([bm.verts.new(o + U * u + V * v) for u, v in section])
    n = len(section)
    last = len(rings) if closed_path else len(rings) - 1
    for k in range(last):
        a, b = rings[k], rings[(k + 1) % len(rings)]
        for i in range(n):
            j = (i + 1) % n
            _face(bm, (a[i], a[j], b[j], b[i]), smooth)
    if not closed_path:
        for idx, flip in ((0, False), (-1, True)):
            if caps[0 if idx == 0 else 1]:
                o = Vector(frames[idx][0])
                _fan(bm, rings[idx], o, flip, smooth=False)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def path_frames(points, up=(0, 0, 1), scales=None, closed=False):
    """Frames along a path: U = side (perpendicular to tangent and `up`), V = up-ish."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    out = []
    for i in range(n):
        if closed:
            t = pts[(i + 1) % n] - pts[(i - 1) % n]
        else:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        t.normalize()
        U = t.cross(Vector(up))
        if U.length < 1e-6:
            U = Vector((1, 0, 0))
        U.normalize()
        V = U.cross(t).normalized()
        su, sv = scales[i] if scales else (1, 1)
        out.append((pts[i], U * su, V * sv))
    return out


def tube(points, radius, segs=8, caps="round", closed=False, up=(0, 0, 1), cap_rings=2):
    """Smooth round tube along a path. caps: 'round', 'flat' or None."""
    sec = [(math.cos(2 * math.pi * i / segs), math.sin(2 * math.pi * i / segs)) for i in range(segs)]
    radii = radius if isinstance(radius, (list, tuple)) else [radius] * len(points)
    pts = [Vector(p) for p in points]
    frames = path_frames(pts, up, closed=closed)
    frames = [(o, U * r, V * r) for (o, U, V), r in zip(frames, radii)]
    if caps == "round" and not closed:
        start, end = [], []
        for k in range(cap_rings, 0, -1):
            a = math.pi / 2 * k / (cap_rings + 0.6)
            s = math.cos(a)
            t0 = (pts[0] - pts[1]).normalized()
            o, U, V = frames[0]
            start.append((pts[0] + t0 * radii[0] * math.sin(a), U * s, V * s))
            t1 = (pts[-1] - pts[-2]).normalized()
            o, U, V = frames[-1]
            end.insert(0, (pts[-1] + t1 * radii[-1] * math.sin(a), U * s, V * s))
        frames = start + frames + end
    return sweep(sec, frames, caps=(caps is not None, caps is not None), closed_path=closed)


def star_outline(r_out, r_in, points=5, round_tips=0.0):
    """Star outline; round_tips > 0 blunts each outer tip (two points instead of one)."""
    raw = []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        raw.append(Vector((r * math.cos(a), r * math.sin(a))))
    if round_tips <= 0:
        return [tuple(p) for p in raw]
    out = []
    n = len(raw)
    for i, p in enumerate(raw):
        if i % 2 == 0:
            prev, nxt = raw[i - 1], raw[(i + 1) % n]
            out.append(tuple(p + (prev - p).normalized() * round_tips))
            out.append(tuple(p + (nxt - p).normalized() * round_tips))
        else:
            out.append(tuple(p))
    return out


def frame_matrix(origin, x_axis, y_axis):
    """4x4 matrix whose local X/Y map to the given axes (Z = X cross Y)."""
    X, Y = Vector(x_axis).normalized(), Vector(y_axis).normalized()
    Z = X.cross(Y).normalized()
    m = Matrix((X, Y, Z)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


# ------------------------------------------------------------------ paints
class Paint:
    def __init__(self, name, color, rough=0.3, tint=False, fn=None, ao=0.5, grad=0.06, zref=10.0):
        self.name, self.color, self.rough, self.tint = name, color, rough, tint
        self.fn, self.ao, self.grad, self.zref = fn, ao, grad, zref


class TexSet:
    def __init__(self, name, size=512, ao_dist=1.4, ss=2):
        self.name, self.size, self.ao_dist, self.ss = name, size, ao_dist, ss
        self.paints, self.pidx = [], {}
        self.images = {}

    def paint(self, name, color, **kw):
        self.pidx[name] = len(self.paints)
        self.paints.append(Paint(name, color, **kw))


ZONE_DEFAULTS = {
    "tex": "SmoothPlastic (SurfaceAppearance)",
    "glass": "Glass",
    "glow": "Neon",
    "shine": "SmoothPlastic",
    "flat": "SmoothPlastic",
}


class Model:
    def __init__(self, name, texset=None, ground=True):
        self.name, self.texset, self.ground = name, texset, ground
        self.zones = {}
        self.extra = {}
        self.objects = []

    def zone(self, name, kind, color=None, transparency=0.0, rough=0.3, emit=2.5, note="", bake_offset=(0, 0, 0)):
        self.zones[name] = dict(kind=kind, color=color, transparency=transparency, rough=rough, emit=emit,
                                pieces=[], note=note, bake_offset=Vector(bake_offset))

    def add(self, zone, paint, bm, closed=True, occluder=True):
        """paint: a texset paint name for tex zones (None keeps per-face indices already set)."""
        if self.zones[zone]["kind"] == "tex":
            lay = bm.faces.layers.int.get("paint") or bm.faces.layers.int.new("paint")
            if paint is not None:
                idx = self.texset.pidx[paint]
                for f in bm.faces:
                    f[lay] = idx
        self.zones[zone]["pieces"].append(dict(bm=bm, closed=closed, occluder=occluder and closed))


# ------------------------------------------------------------------ assembly
def _inside(bvh, p, eps=0.004):
    hit = bvh.find_nearest(p)
    if hit[0] is None:
        return False
    loc, nrm, _, dist = hit
    return dist > eps and (Vector(p) - loc).dot(nrm) < 0


def _bbox(bm):
    xs = [v.co for v in bm.verts]
    lo = Vector([min(c[i] for c in xs) for i in range(3)])
    hi = Vector([max(c[i] for c in xs) for i in range(3)])
    return lo, hi


def cull_hidden(model):
    """Delete faces that sit entirely inside another closed piece of the same model, and
    downward faces lying on the ground (z ~ 0) for floor-standing models."""
    pieces = [p for z in model.zones.values() for p in z["pieces"]]
    occ = []
    for p in pieces:
        if p["occluder"]:
            bmesh.ops.recalc_face_normals(p["bm"], faces=p["bm"].faces)
            lo, hi = _bbox(p["bm"])
            occ.append((p, BVHTree.FromBMesh(p["bm"]), lo, hi))
    removed = 0
    for p in pieces:
        bm = p["bm"]
        bm.normal_update()
        dead = []
        for f in bm.faces:
            pts = [v.co.copy() for v in f.verts] + [f.calc_center_median()]
            if model.ground and all(q.z < 0.02 for q in pts) and f.normal.z < -0.9:
                dead.append(f)
                continue
            for q, bvh, lo, hi in occ:
                if q is p:
                    continue
                if any(not (lo.x - 0.01 <= c.x <= hi.x + 0.01 and lo.y - 0.01 <= c.y <= hi.y + 0.01 and lo.z - 0.01 <= c.z <= hi.z + 0.01) for c in pts):
                    continue
                if all(_inside(bvh, c) for c in pts):
                    dead.append(f)
                    break
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            removed += len(dead)
    bmesh.ops  # noqa
    return removed


def make_objects(model, offset=Vector((0, 0, 0))):
    scene = bpy.context.scene
    removed = cull_hidden(model)
    print(f"[{model.name}] culled {removed} hidden faces")
    for zname, z in model.zones.items():
        mesh = bpy.data.meshes.new(zname)
        tmp = bmesh.new()
        for p in z["pieces"]:
            me = bpy.data.meshes.new("tmp")
            p["bm"].to_mesh(me)
            tmp.from_mesh(me)
            bpy.data.meshes.remove(me)
            p["bm"].free()
        bmesh.ops.remove_doubles(tmp, verts=tmp.verts, dist=1e-6)
        loose = [v for v in tmp.verts if not v.link_faces]
        if loose:
            bmesh.ops.delete(tmp, geom=loose, context="VERTS")
        bmesh.ops.triangulate(tmp, faces=tmp.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        tmp.to_mesh(mesh)
        tmp.free()
        obj = bpy.data.objects.new(zname, mesh)
        scene.collection.objects.link(obj)
        obj.location = offset + z["bake_offset"]
        # weighted normals: big flat faces stay flat, bevels stay round
        mod = obj.modifiers.new("WN", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
        mod.weight = 50
        mod.mode = "FACE_AREA"
        bpy.context.view_layer.objects.active = obj
        for o in scene.objects:
            o.select_set(o is obj)
        bpy.ops.object.modifier_apply(modifier="WN")
        obj["zone_kind"] = z["kind"]
        obj["model"] = model.name
        model.objects.append(obj)
        z["obj"] = obj
    return model.objects


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ------------------------------------------------------------------ baking
def setup_cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:  # noqa
        print("GPU not available, CPU", e)
        sc.cycles.device = "CPU"
    sc.cycles.samples = samples


def _float_img(name, R):
    img = bpy.data.images.new(name, R, R, alpha=True, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    return img


def _read(img, R):
    a = np.empty(R * R * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(R, R, 4)


def _save_png(name, arr, colorspace):
    """arr: (H, W, 3 or 4) values 0..1 already encoded (sRGB for colour)."""
    H, W = arr.shape[:2]
    img = bpy.data.images.new(name, W, H, alpha=False)
    img.colorspace_settings.name = colorspace
    rgba = np.ones((H, W, 4), np.float32)
    rgba[..., :3] = arr[..., :3]
    img.pixels.foreach_set(rgba.ravel())
    path = os.path.join(OUT, name + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    im = bpy.data.images.load(path)
    im.colorspace_settings.name = colorspace
    return im


def bake_texset(ts, objs, ss=2):
    sc = bpy.context.scene
    R = ts.size * ss
    # bake materials, one per paint, emission switched per pass
    mats = []
    for i, p in enumerate(ts.paints):
        m = bpy.data.materials.new("bake_" + p.name)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        tc = nt.nodes.new("ShaderNodeTexCoord")
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        em = nt.nodes.new("ShaderNodeEmission")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        # position encoded (P + 64) / 128
        mp = nt.nodes.new("ShaderNodeVectorMath")
        mp.operation = "MULTIPLY_ADD"
        nt.links.new(tc.outputs["Object"], mp.inputs[0])
        mp.inputs[1].default_value = (1 / 128,) * 3
        mp.inputs[2].default_value = (0.5,) * 3
        mn = nt.nodes.new("ShaderNodeVectorMath")
        mn.operation = "MULTIPLY_ADD"
        nt.links.new(geo.outputs["Normal"], mn.inputs[0])
        mn.inputs[1].default_value = (0.5,) * 3
        mn.inputs[2].default_value = (0.5,) * 3
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = ((i + 1) / 64.0, 0, 0, 1)
        tex = nt.nodes.new("ShaderNodeTexImage")
        nt.nodes.active = tex
        mats.append(dict(mat=m, em=em, pos=mp, nrm=mn, rgb=rgb, tex=tex))
    for o in objs:
        o.data.materials.clear()
        for d in mats:
            o.data.materials.append(d["mat"])
        att = o.data.attributes.get("paint")
        vals = np.zeros(len(o.data.polygons), np.int32)
        att.data.foreach_get("value", vals)
        o.data.polygons.foreach_set("material_index", vals)

    # UVs: all objects of the set unwrapped and packed together
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(78), island_margin=0.0, area_weight=0.0, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(margin=6.0 / R, rotate=True, shape_method="CONCAVE")
    except TypeError:
        bpy.ops.uv.pack_islands(margin=6.0 / R, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    # texel density (px per stud) for the height -> normal conversion
    a3, auv = 0.0, 0.0
    for o in objs:
        me = o.data
        uvl = me.uv_layers.active.data
        for poly in me.polygons:
            a3 += poly.area
            pts = [uvl[li].uv for li in poly.loop_indices]
            s = 0.0
            for k in range(len(pts)):
                x1, y1 = pts[k]
                x2, y2 = pts[(k + 1) % len(pts)]
                s += x1 * y2 - x2 * y1
            auv += abs(s) / 2
    density = math.sqrt(auv * R * R / max(a3, 1e-9))
    print(f"[{ts.name}] texel density {density / ss:.1f} px/stud at {ts.size}")

    hide = [o for o in sc.objects if o not in objs and o.type == "MESH"]
    for o in hide:
        o.hide_render = True
    # a ground plane under everything for contact shading in the AO pass
    gme = bpy.data.meshes.new("bake_ground")
    gbm = bmesh.new()
    bmesh.ops.create_grid(gbm, x_segments=1, y_segments=1, size=2000)
    gbm.to_mesh(gme)
    gbm.free()
    ground = bpy.data.objects.new("bake_ground", gme)
    sc.collection.objects.link(ground)
    ground.hide_render = True

    imgs = {}

    def run(kind, btype, samples):
        img = _float_img("bake_" + kind, R)
        for d in mats:
            d["tex"].image = img
            d["mat"].node_tree.nodes.active = d["tex"]
        setup_cycles(samples)
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.bake(type=btype, margin=10, margin_type="EXTEND", use_clear=True, target="IMAGE_TEXTURES")
        imgs[kind] = _read(img, R)
        bpy.data.images.remove(img)

    for kind, sock in (("pos", "pos"), ("nrm", "nrm"), ("id", "rgb")):
        for d in mats:
            d["mat"].node_tree.links.new(d[sock].outputs[0], d["em"].inputs["Color"])
        run(kind, "EMIT", 1)
    ground.hide_render = False
    sc.world = sc.world or bpy.data.worlds.new("bakeworld")
    sc.world.light_settings.distance = ts.ao_dist
    # AO bake per object position: objects offset in make_objects keep models apart
    run("ao", "AO", 8 if FAST else 48)
    ground.hide_render = True
    bpy.data.objects.remove(ground)
    for o in hide:
        o.hide_render = False

    P = imgs["pos"][..., :3] * 128.0 - 64.0
    N = imgs["nrm"][..., :3] * 2.0 - 1.0
    pid = np.floor(imgs["id"][..., 0] * 64.0 + 0.5).astype(int) - 1
    AO = np.clip(imgs["ao"][..., 0], 0, 1)
    u, c = np.unique(pid, return_counts=True)
    print(f"[{ts.name}] paint ids", dict(zip(u.tolist(), c.tolist())), "id raw sample", imgs["id"][R // 2, R // 2])

    col = np.zeros((R, R, 3))
    col[:] = srgb_to_lin(np.array(hexrgb("cream")) / 255.0)
    rough = np.full((R, R), 0.35)
    height = np.zeros((R, R))
    for i, p in enumerate(ts.paints):
        m = pid == i
        if not m.any():
            continue
        Pm, Nm = P[m], N[m]
        base = np.tile(np.array(lin(p.color)), (len(Pm), 1))
        r = np.full(len(Pm), p.rough)
        h = np.zeros(len(Pm))
        if p.fn:
            res = p.fn(Pm, Nm)
            base = res.get("col", base)
            r = res.get("rough", r)
            h = res.get("h", h)
        # soft painted shading: top-to-bottom gradient and AO in the grooves
        zn = np.clip(Pm[:, 2] / p.zref, 0, 1)
        shade = (1 - p.grad * (1 - zn)) * (1 - p.ao * (1 - AO[m]))
        col[m] = base * shade[:, None]
        rough[m] = r
        height[m] = h

    # height (studs) -> tangent-space normal, only between texels of the same surface
    def grad(axis):
        hp, hm = np.roll(height, -1, axis), np.roll(height, 1, axis)
        Pp, Pm_ = np.roll(P, -1, axis), np.roll(P, 1, axis)
        ok_p = np.linalg.norm(Pp - P, axis=-1) < 3.0 / density
        ok_m = np.linalg.norm(Pm_ - P, axis=-1) < 3.0 / density
        g = np.zeros_like(height)
        both = ok_p & ok_m
        g[both] = (hp - hm)[both] / 2
        g[ok_p & ~ok_m] = (hp - height)[ok_p & ~ok_m]
        g[ok_m & ~ok_p] = (height - hm)[ok_m & ~ok_p]
        return g * density

    gu = grad(1)  # along image x = U
    gv = grad(0)  # along image rows = V (Blender rows go bottom-up)
    nrm = np.stack([-gu, -gv, np.ones_like(height)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)

    def down(a):
        s = ts.size
        if a.ndim == 2:
            return a.reshape(s, ss, s, ss).mean((1, 3))
        return a.reshape(s, ss, s, ss, a.shape[-1]).mean((1, 3))

    col_s = lin_to_srgb(down(col))
    rough_s = down(rough)
    nrm_s = down(nrm)
    nrm_s /= np.linalg.norm(nrm_s, axis=-1, keepdims=True)
    ts.images["color"] = _save_png(ts.name + "_color", col_s, "sRGB")
    ts.images["roughness"] = _save_png(ts.name + "_roughness", np.repeat(rough_s[..., None], 3, -1), "Non-Color")
    ts.images["normal"] = _save_png(ts.name + "_normal", nrm_s * 0.5 + 0.5, "Non-Color")
    ts.density = density / ss
    for o in objs:
        o.data.materials.clear()
    for d in mats:
        bpy.data.materials.remove(d["mat"])


# ------------------------------------------------------------------ preview (Roblox-like) materials
def tex_material(ts, name, tint=(1, 1, 1), flat=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    uv = nt.nodes.new("ShaderNodeUVMap")
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = ts.images["color"]
    nt.links.new(uv.outputs[0], tc.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.name = "Tint"
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[7].default_value = tuple(tint) + (1,)
    nt.links.new(tc.outputs["Color"], mix.inputs[6])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Specular IOR Level"].default_value = 0.5
    if flat:
        bs.inputs["Roughness"].default_value = 0.45
    else:
        tr = nt.nodes.new("ShaderNodeTexImage")
        tr.image = ts.images["roughness"]
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = ts.images["normal"]
        nt.links.new(uv.outputs[0], tr.inputs[0])
        nt.links.new(uv.outputs[0], tn.inputs[0])
        nt.links.new(tr.outputs["Color"], bs.inputs["Roughness"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    return m


def flat_material(name, color, kind, transparency=0.0, rough=0.3, emit=2.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    c = lin(color) + (1,)
    bs.inputs["Base Color"].default_value = c
    bs.inputs["Roughness"].default_value = rough
    if kind == "glow":
        bs.inputs["Emission Color"].default_value = c
        bs.inputs["Emission Strength"].default_value = emit
    if kind == "glass":
        bs.inputs["Roughness"].default_value = 0.04
        bs.inputs["Specular IOR Level"].default_value = 1.0
        bs.inputs["Coat Weight"].default_value = 0.6
    if transparency > 0:
        bs.inputs["Alpha"].default_value = 1 - transparency
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            pass
    return m


def assign_preview_materials(model, flat=False, tint=None):
    for zname, z in model.zones.items():
        o = z["obj"]
        o.data.materials.clear()
        if z["kind"] == "tex":
            p = model.texset.paints
            is_tint = zname.endswith("_Tint")
            t = (1, 1, 1)
            if is_tint and tint:
                t = lin(tint)
            o.data.materials.append(tex_material(model.texset, zname + ("_flat" if flat else "") + "_mat", t, flat))
        else:
            col = z["color"]
            if z["kind"] == "glow" and tint and z.get("tint_glow"):
                col = tint
            o.data.materials.append(flat_material(zname + "_mat", col, z["kind"], z["transparency"], z["rough"], z["emit"]))
        for poly in o.data.polygons:
            poly.material_index = 0


# ------------------------------------------------------------------ export + bounds
def roblox_box(lo, hi):
    return ([round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
            [round((hi.x + lo.x) / 2, 3), round((hi.z + lo.z) / 2, 3), round(-(hi.y + lo.y) / 2, 3)])


def obj_box(o):
    vs = [v.co for v in o.data.vertices]
    lo = Vector([min(c[i] for c in vs) for i in range(3)])
    hi = Vector([max(c[i] for c in vs) for i in range(3)])
    return lo, hi


def export_model(model):
    objs = model.objects
    for o in objs:
        o.location = (0, 0, 0)
    half = Matrix.Rotation(math.pi, 4, "Z")
    for o in objs:
        o.data.transform(half)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, model.name + ".fbx"), use_selection=True, object_types={"MESH"},
        mesh_smooth_type="OFF", use_triangles=True, axis_forward="-Z", axis_up="Y",
        apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    for o in objs:
        o.data.transform(half)

    meshes = {}
    lo_all, hi_all = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    total = 0
    for zname, z in model.zones.items():
        o = z["obj"]
        lo, hi = obj_box(o)
        for i in range(3):
            lo_all[i], hi_all[i] = min(lo_all[i], lo[i]), max(hi_all[i], hi[i])
        size, center = roblox_box(lo, hi)
        t = tris(o)
        total += t
        e = {"size": size, "center": center, "tris": t, "material": ZONE_DEFAULTS[z["kind"]]}
        if z["kind"] == "tex":
            e["textures"] = {k: model.texset.name + "_" + k + ".png" for k in ("color", "normal", "roughness")}
            e["tinted"] = zname.endswith("_Tint")
            e["color"] = "#FFFFFF (texture carries the colours)" if not e["tinted"] else "tint per variant (SurfaceAppearance.Color)"
        else:
            e["color"] = "#" + "".join(f"{c:02X}" for c in hexrgb(z["color"]))
            if z["transparency"]:
                e["transparency"] = z["transparency"]
            e["castShadow"] = False
        if z["note"]:
            e["note"] = z["note"]
        meshes[zname] = e
    size, center = roblox_box(lo_all, hi_all)
    data = {"model": model.name, "fbx": model.name + ".fbx", "units": "1 unit = 1 stud",
            "axes": "Roblox: X right, Y up, Z = -Blender Y; front faces Roblox -Z",
            "origin": "bottom centre of the footprint at (0,0,0)",
            "size": size, "center": center, "tris": total, "meshes": meshes}
    data.update(model.extra)
    with open(os.path.join(OUT, model.name + ".bounds.json"), "w") as f:
        json.dump(data, f, indent=1)
    print(f"[{model.name}] TOTAL {total} tris, size (Roblox X,Y,Z) {size}")
    for zname in model.zones:
        print(f"    {zname}: {meshes[zname]['tris']} tris, size {meshes[zname]['size']}")
    return total


# ------------------------------------------------------------------ previews
def studio(R=10.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("studio")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.55, 0.53, 0.55, 1)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.80, 0.86, 0.95, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.9
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    o = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], o.inputs[0])
    # floor
    me = bpy.data.meshes.new("studio_floor")
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=400)
    bm.to_mesh(me)
    bm.free()
    fl = bpy.data.objects.new("studio_floor", me)
    sc.collection.objects.link(fl)
    fm = bpy.data.materials.new("studio_floor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0.62, 0.6, 0.6, 1)
    fb.inputs["Roughness"].default_value = 0.5
    me.materials.append(fm)
    fl.location.z = -0.002
    return fl


def lights(R, side=(0.6, 0.8)):
    sc = bpy.context.scene
    made = []
    sx, sy = side

    def lamp(pos, watts, size, color=(1, 1, 1)):
        d = bpy.data.lights.new("L", "AREA")
        d.energy = watts * R * R
        d.size = size * R
        d.color = color
        o = bpy.data.objects.new("L", d)
        o.location = Vector(pos) * R
        o.rotation_euler = (Vector((0, 0, R * 0.3)) - o.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(o)
        made.append(o)

    lamp((-1.4, 2.2, 2.6), 95, 2.2, (1.0, 0.97, 0.93))   # key, front-left above
    lamp((2.6, 1.0, 1.2), 30, 2.5, (0.9, 0.94, 1.0))     # fill, right
    lamp((0.4, -2.6, 2.2), 55, 2.0, (1.0, 0.95, 0.92))   # rim, behind
    lamp((0, 0, 3.5), 25, 3.0)                           # top
    return made


def player_block(pos):
    bm = rbox((2, 1, 5), (pos[0], pos[1], 2.5), r=0.08, segs=1)
    me = bpy.data.meshes.new("player")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("player_block", me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new("player")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.32, 0.33, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    me.materials.append(m)
    return o


def camera():
    sc = bpy.context.scene
    d = bpy.data.cameras.new("cam")
    c = bpy.data.objects.new("cam", d)
    sc.collection.objects.link(c)
    sc.camera = c
    d.clip_end = 3000
    d.sensor_width = 36
    return c


def shoot(path, pos, target, lens, res, samples=None):
    sc = bpy.context.scene
    c = sc.camera
    c.location = Vector(pos)
    c.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = lens
    setup_cycles(samples or (24 if FAST else 96))
    sc.cycles.use_denoising = True
    sc.cycles.use_adaptive_sampling = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)
    return path


def frame_shot(lo, hi, direction, lens, aspect=4 / 3, pad=1.08):
    mid = (Vector(lo) + Vector(hi)) / 2
    rad = (Vector(hi) - Vector(lo)).length / 2
    d = Vector(direction).normalized()
    fov_h = 2 * math.atan(18 / lens)
    fov_v = 2 * math.atan(math.tan(fov_h / 2) / aspect)
    dist = rad / math.sin(min(fov_h, fov_v) / 2) * pad * 0.9
    return mid + d * dist, mid


def compose(paths, out, cols, cell):
    """Tile rendered PNGs into one image (rows top to bottom)."""
    w, h = cell
    rows = math.ceil(len(paths) / cols)
    canvas = np.ones((rows * h, cols * w, 4), np.float32)
    for k, p in enumerate(paths):
        im = bpy.data.images.load(p)
        a = np.empty(w * h * 4, np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)
        r, c = k // cols, k % cols
        y0 = (rows - 1 - r) * h
        canvas[y0:y0 + h, c * w:(c + 1) * w] = a
        bpy.data.images.remove(im)
    img = bpy.data.images.new("compose", cols * w, rows * h, alpha=False)
    img.pixels.foreach_set(canvas.ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print("composed", out)


def downscale(src, out, size):
    im = bpy.data.images.load(src)
    im.scale(size[0], size[1])
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def model_bounds(objs):
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                lo[i], hi[i] = min(lo[i], w[i]), max(hi[i], w[i])
    return lo, hi


def standard_previews(model, prefix, extra_objs=(), eye=True, block_at=None, tint=None):
    """beauty, flat, thumb, turn (+eye) previews for one model at the origin."""
    sc = bpy.context.scene
    objs = list(model.objects) + list(extra_objs)
    for o in sc.objects:
        if o.type == "MESH" and o.name not in ("studio_floor",):
            o.hide_render = o not in objs
    lo, hi = model_bounds(objs)
    w = hi.x - lo.x
    blk = player_block(block_at or (lo.x - 1.8, hi.y * 0.3, 0))
    lo2, hi2 = model_bounds(objs + [blk])
    R = max((hi2 - lo2).length / 2, 3)
    ls = lights(R)
    cam = camera()
    out = {}
    pos, mid = frame_shot(lo2, hi2, (0.55, 1.0, 0.42), 50)
    mid.z = (lo2.z + hi2.z) * 0.45
    assign_preview_materials(model, tint=tint)
    out["beauty"] = shoot(os.path.join(PREV, prefix + "_beauty.png"), pos, mid, 50, (1280, 960))
    downscale(out["beauty"], os.path.join(PREV, prefix + "_thumb.png"), (256, 192))
    if eye:
        tz = (lo.z + hi.z) * 0.45
        e = Vector((3.5, hi.y + 15, 5))
        shoot(os.path.join(PREV, prefix + "_eye.png"), e, Vector((0, 0, tz)), 24, (1280, 960))
    blk.hide_render = True
    lo, hi = model_bounds(model.objects)
    cells = []
    for k, (nm, d) in enumerate((("front", (0, 1, 0.28)), ("right", (1, 0, 0.28)), ("back", (0, -1, 0.28)), ("left", (-1, 0, 0.28)))):
        p, m_ = frame_shot(lo, hi, d, 50)
        cells.append(shoot(os.path.join(PREV, f"_tmp_{prefix}_{nm}.png"), p, m_, 50, (640, 480), 32 if not FAST else 12))
    compose(cells, os.path.join(PREV, prefix + "_turn.png"), 2, (640, 480))
    for c in cells:
        os.remove(c)
    blk.hide_render = False
    assign_preview_materials(model, flat=True, tint=tint)
    shoot(os.path.join(PREV, prefix + "_flat.png"), pos, mid, 50, (1280, 960))
    assign_preview_materials(model)
    for o in ls + [cam, blk]:
        bpy.data.objects.remove(o)
    return out


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build(models, bake=True):
    """Make objects for all models (spaced apart for the AO bake), bake the shared texture
    set, export every model, save one .blend. Returns per-model triangle totals."""
    texsets = []
    for k, m in enumerate(models):
        make_objects(m, Vector((k * 120.0, 0, 0)))
        if m.texset and m.texset not in texsets:
            texsets.append(m.texset)
    for ts in texsets:
        objs = [z["obj"] for m in models if m.texset is ts for z in m.zones.values() if z["kind"] == "tex"]
        bake_texset(ts, objs, ss=ts.ss)
    totals = {}
    for m in models:
        totals[m.name] = export_model(m)
    for m in models:
        for o in m.objects:
            o.location = (0, 0, 0)
        assign_preview_materials(m)
    return totals


def save_blend(name, models):
    # spread the models out so the .blend is easy to look at
    for k, m in enumerate(models):
        for o in m.objects:
            o.location = (k * 25.0, 0, 0)
            o.hide_render = False
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))
    for m in models:
        for o in m.objects:
            o.location = (0, 0, 0)
