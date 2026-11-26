# Shared helpers for Batch A "The Machine" (docs/art_plan.md): the lobby's giant gumball
# machine, its logo banner and the low-detail gumball pile. Used by
#   hub_machine_build_gumball_lo.py, hub_machine_build_machine.py,
#   hub_machine_build_banner.py, hub_machine_build_assembled.py
# Background Blender only. 1 Blender unit = 1 stud, Z up, front of every model on +Y,
# models stand on the origin. Roblox axes in the json files: X right, Y up, Z = -Blender Y.

import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "art", "hub_machine")
PREVIEWS = os.path.join(ROOT, "art", "previews")
GUMBALL = os.path.join(ROOT, "art", "gumball")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEWS, exist_ok=True)
QUICK = os.environ.get("HUB_QUICK") == "1"

# palette (docs/art_plan.md section 1)
HEX = {
    "red": "#E62D46", "cream": "#FFFCFA", "pink": "#FFB4D2", "gold": "#FFC83C",
    "navy": "#283250", "mint": "#6EDCBE", "glow": "#BE1E5A",
}
GUMBALL_HEX = ["#E62D3C", "#2878E6", "#FFAF00", "#32AF46", "#FF78BE", "#FF8C28", "#965AE6", "#FFFFFF"]


def rgb255(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lin(h):
    """sRGB hex -> linear rgba for shader nodes."""
    c = [x / 255 for x in rgb255(h)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


# ---------------------------------------------------------------- 2D helpers
def fillet(pts, r, steps=3):
    """Round the inside corners of a 2D polyline. r = one radius or one per inside point."""
    out = [tuple(pts[0])]
    for k in range(1, len(pts) - 1):
        a, b, c = Vector(pts[k - 1]), Vector(pts[k]), Vector(pts[k + 1])
        rr = r[k - 1] if isinstance(r, (list, tuple)) else r
        d1, d2 = a - b, c - b
        if rr <= 0 or d1.length < 1e-6 or d2.length < 1e-6:
            out.append(tuple(b))
            continue
        ang = d1.angle(d2)
        if ang > math.pi - 1e-3:
            out.append(tuple(b))
            continue
        t = min(rr / math.tan(ang / 2), d1.length * 0.49, d2.length * 0.49)
        p0, p1 = b + d1.normalized() * t, b + d2.normalized() * t
        for i in range(steps + 1):
            s = i / steps
            out.append(tuple((1 - s) ** 2 * p0 + 2 * s * (1 - s) * b + s * s * p1))
    out.append(tuple(pts[-1]))
    return out


def arc(cx, cy, r, a0, a1, steps):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def rrect(w, h, r, steps=4, center=(0, 0)):
    """Rounded rectangle outline, counter-clockwise."""
    hw, hh = w / 2 - r, h / 2 - r
    out = []
    for k, (cx, cy) in enumerate(((hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh))):
        for i in range(steps + 1):
            a = math.pi / 2 * (k + i / steps)
            out.append((center[0] + cx + r * math.cos(a), center[1] + cy + r * math.sin(a)))
    return out


def arch(hw, z0, z1, r, steps=5):
    """Door shape: flat bottom, rounded top corners. Counter-clockwise from bottom right."""
    out = [(hw, z0)]
    out += arc(hw - r, z1 - r, r, 0, 90, steps)
    out += arc(-hw + r, z1 - r, r, 90, 180, steps)
    out.append((-hw, z0))
    return out


def squircle(n_of_z, ysq=1.0):
    """Lathe cross-section: a rounded square (superellipse) whose exponent can change with height."""
    def shape(theta, a, z):
        n = n_of_z(z)
        c, s = math.cos(theta), math.sin(theta)
        r = a / (abs(c) ** n + abs(s) ** n) ** (1.0 / n)
        return Vector((r * c, r * s * ysq, z))
    return shape


# ---------------------------------------------------------------- mesh builder
class Build:
    """Collects every piece of one model in a single bmesh, with UVs in studs. finalize() packs the
    UVs into one atlas and splits the result into the named objects."""

    def __init__(self):
        self.bm = bmesh.new()
        bm = self.bm
        self.uv = bm.loops.layers.uv.new("UVMap")
        self.L_obj = bm.faces.layers.int.new("obj")
        self.L_done = bm.faces.layers.int.new("done")
        self.L_grp = bm.faces.layers.int.new("grp")    # instance group (0 = none)
        self.L_inst = bm.faces.layers.int.new("inst")  # copy number inside the group (0 = master)
        self.L_key = bm.faces.layers.int.new("key")    # face order inside one copy
        self.mats = []
        self.mat = 0
        self.obj = 0
        self.w = 1.0
        self.grp = 0
        self.inst = 0
        self.key = 0

    def use(self, mat=None, obj=None, w=None):
        if mat is not None:
            if mat not in self.mats:
                self.mats.append(mat)
            self.mat = self.mats.index(mat)
        if obj is not None:
            self.obj = obj
        if w is not None:
            self.w = w

    def instance(self, grp, inst):
        """Faces made from now on belong to copy `inst` of group `grp`; every copy must be built
        the same way. All copies share the master's UVs (saves texture space). grp 0 = off."""
        self.grp, self.inst, self.key = grp, inst, 0

    def _tag(self, f):
        f.smooth = True
        f.material_index = self.mat
        f[self.L_obj] = self.obj
        f[self.L_done] = 1
        f[self.L_grp] = self.grp
        f[self.L_inst] = self.inst
        f[self.L_key] = self.key
        self.key += 1

    def _face(self, verts, uvs=None):
        f = self.bm.faces.new(verts)
        self._tag(f)
        if uvs:
            for loop, uv in zip(f.loops, uvs):
                loop[self.uv].uv = uv
        return f

    def _box_uv(self, faces):
        for f in faces:
            f.normal_update()
            n = f.normal
            ax = max(range(3), key=lambda i: abs(n[i]))
            for loop in f.loops:
                co = loop.vert.co
                uv = (co.y, co.z) if ax == 0 else ((co.x, co.z) if ax == 1 else (co.x, co.y))
                loop[self.uv].uv = (uv[0] * self.w, uv[1] * self.w)

    def _finish_new(self, matrix=None):
        """Tag, orient and box-map the faces made by bmesh operators since the last call."""
        bm = self.bm
        new = [f for f in bm.faces if f[self.L_done] == 0]
        big = [f for f in new if len(f.verts) > 4]
        if big:
            bmesh.ops.triangulate(bm, faces=big)
            new = [f for f in bm.faces if f[self.L_done] == 0]
        bmesh.ops.recalc_face_normals(bm, faces=new)
        if matrix is not None:
            bmesh.ops.transform(bm, matrix=matrix, verts=list({v for f in new for v in f.verts}))
        new.sort(key=lambda f: f.index)
        for f in new:
            self._tag(f)
        self._box_uv(new)
        return new

    # --- shapes
    def lathe(self, profile, segs=48, frame=None, shape=None, seam=math.pi, cap_end=False, cap_start=False):
        """Spin a profile [(r, z)] round Z (or the Z of `frame`). List the profile counter-clockwise
        round the solid (up the outside, then inward over the top) so faces point outward. A point
        given twice makes a hard edge. cap_end / cap_start close the hole with a fan."""
        bm, w = self.bm, self.w

        def P(theta, r, z):
            v = shape(theta, r, z) if shape else Vector((r * math.cos(theta), r * math.sin(theta), z))
            return frame @ v if frame else v

        runs = [[profile[0]]]
        for p, q in zip(profile, profile[1:]):
            if abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6:
                runs.append([q])
            else:
                runs[-1].append(q)
        first = last = None
        for run in runs:
            if len(run) < 2:
                continue
            rings = [[bm.verts.new(P(seam + 2 * math.pi * i / segs, r, z)) for i in range(segs)] for r, z in run]
            vs = [0.0]
            for p, q in zip(run, run[1:]):
                vs.append(vs[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
            # u follows the real distance round the fattest ring (so squircles do not stretch)
            ref = rings[max(range(len(run)), key=lambda k: run[k][0])]
            us = [0.0]
            for i in range(segs):
                us.append(us[-1] + (ref[(i + 1) % segs].co - ref[i].co).length)
            # big rings are unrolled as two half strips (front and back) so they pack tighter
            half = segs // 2 if segs >= 40 else segs
            shift = [0.0 if i < half else us[-1] + 1.0 for i in range(segs)]
            for k in range(len(run) - 1):
                a, b = rings[k], rings[k + 1]
                for i in range(segs):
                    j = (i + 1) % segs
                    self._face((a[i], a[j], b[j], b[i]),
                               [((us[i] + shift[i]) * w, vs[k] * w), ((us[i + 1] + shift[i]) * w, vs[k] * w),
                                ((us[i + 1] + shift[i]) * w, vs[k + 1] * w), ((us[i] + shift[i]) * w, vs[k + 1] * w)])
            if first is None:
                first = (rings[0], run[0])
            last = (rings[-1], run[-1])

        def flat(theta, r, z):
            v = shape(theta, r, z) if shape else Vector((r * math.cos(theta), r * math.sin(theta), z))
            return (v.x * w, v.y * w)

        for want, (ring, (r, z)), flip in ((cap_end, last, False), (cap_start, first, True)):
            if not want:
                continue
            c = bm.verts.new(P(0.0, 0.0, z))
            for i in range(segs):
                j = (i + 1) % segs
                ti, tj = seam + 2 * math.pi * i / segs, seam + 2 * math.pi * j / segs
                if flip:
                    self._face((ring[j], ring[i], c), [flat(tj, r, z), flat(ti, r, z), (0.0, 0.0)])
                else:
                    self._face((ring[i], ring[j], c), [flat(ti, r, z), flat(tj, r, z), (0.0, 0.0)])

    def rbox(self, size, center, bevel, segs=3, rot=None):
        bm = self.bm
        made = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector(size), verts=made["verts"])
        edges = list({e for v in made["verts"] for e in v.link_edges})
        if bevel > 0:
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=segs, profile=0.5, affect="EDGES")
        m = Matrix.Translation(Vector(center))
        if rot:
            m = m @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
        return self._finish_new(m)

    def solid(self, outline, lo, hi, plane="xz", bevel=0.0, segs=2, matrix=None):
        """A flat outline pushed into a solid with rounded edges. plane "xz": outline is (x, z)
        seen from the front, running from y = lo to y = hi. plane "xy": (x, y), from z = lo to hi."""
        bm = self.bm

        def pt(u, v, t):
            return Vector((u, t, v)) if plane == "xz" else Vector((u, v, t))

        a = [bm.verts.new(pt(u, v, lo)) for u, v in outline]
        b = [bm.verts.new(pt(u, v, hi)) for u, v in outline]
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(a[::-1])
        bm.faces.new(b)
        if bevel > 0:
            edges = list({e for v in a + b for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=segs, profile=0.5, affect="EDGES")
        return self._finish_new(matrix)

    def loft(self, rings, flip=False, closed=True):
        """Quads between consecutive rings of points (each ring the same length)."""
        bm = self.bm
        vr = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
        faces = []
        n = len(vr[0])
        for a, b in zip(vr, vr[1:]):
            for i in range(n if closed else n - 1):
                j = (i + 1) % n
                vs = (a[i], a[j], b[j], b[i])
                faces.append(self._face(vs[::-1] if flip else vs))
        self._box_uv(faces)
        return vr

    def fan(self, ring_verts, center, flip=False):
        bm = self.bm
        c = bm.verts.new(Vector(center))
        n = len(ring_verts)
        faces = []
        for i in range(n):
            j = (i + 1) % n
            vs = (ring_verts[i], ring_verts[j], c)
            faces.append(self._face(vs[::-1] if flip else vs))
        self._box_uv(faces)

    # --- output
    def finalize(self, names, scene, pack=True, margin=0.006):
        """names = {obj id: object name}. Returns {name: object}."""
        bm = self.bm
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big:
            bmesh.ops.triangulate(bm, faces=big)
        me = bpy.data.meshes.new("build_tmp")
        slots = [bpy.data.materials.new("slot_" + n) for n in self.mats]  # keeps the face -> material numbers
        for sl in slots:
            me.materials.append(sl)
        bm.to_mesh(me)
        bm.free()
        tmp = bpy.data.objects.new("build_tmp", me)
        scene.collection.objects.link(tmp)
        if pack:
            bpy.context.view_layer.objects.active = tmp
            tmp.select_set(True)
            scene.tool_settings.use_uv_select_sync = True
            bpy.ops.object.mode_set(mode="EDIT")
            eb = bmesh.from_edit_mesh(me)
            grp, inst, key = eb.faces.layers.int["grp"], eb.faces.layers.int["inst"], eb.faces.layers.int["key"]
            uv = eb.loops.layers.uv["UVMap"]
            for f in eb.faces:
                copy = f[grp] > 0 and f[inst] > 0
                f.hide_set(copy)
                f.select_set(not copy)
            bmesh.update_edit_mesh(me)
            bpy.ops.uv.select_all(action="SELECT")
            bpy.ops.uv.pack_islands(rotate=True, rotate_method="CARDINAL", scale=True, margin_method="FRACTION", margin=margin,
                                    shape_method="CONCAVE")
            eb = bmesh.from_edit_mesh(me)
            grp, inst, key = eb.faces.layers.int["grp"], eb.faces.layers.int["inst"], eb.faces.layers.int["key"]
            uv = eb.loops.layers.uv["UVMap"]
            master = {(f[grp], f[key]): [l[uv].uv.copy() for l in f.loops]
                      for f in eb.faces if f[grp] > 0 and f[inst] == 0}
            for f in eb.faces:
                f.hide_set(False)
                if f[grp] > 0 and f[inst] > 0:
                    for l, u in zip(f.loops, master[(f[grp], f[key])]):
                        l[uv].uv = u
            bmesh.update_edit_mesh(me)
            bpy.ops.object.mode_set(mode="OBJECT")
        out = {}
        for oid, name in names.items():
            b2 = bmesh.new()
            b2.from_mesh(me)
            lay = b2.faces.layers.int["obj"]
            bmesh.ops.delete(b2, geom=[f for f in b2.faces if f[lay] != oid], context="FACES")
            for lname in ("obj", "done", "grp", "inst", "key"):
                b2.faces.layers.int.remove(b2.faces.layers.int[lname])
            m2 = bpy.data.meshes.new(name)
            for sl in slots:
                m2.materials.append(sl)
            b2.to_mesh(m2)
            b2.free()
            ob = bpy.data.objects.new(name, m2)
            scene.collection.objects.link(ob)
            out[name] = ob
        bpy.data.objects.remove(tmp)
        bpy.data.meshes.remove(me)
        for ob in out.values():
            weighted_normals(ob)
        return out


def weighted_normals(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    mod = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
    mod.keep_sharp = True
    mod.weight = 60
    bpy.ops.object.modifier_apply(modifier=mod.name)


def single_material(ob, mat):
    """One material for the whole object (after the bake everything shares one texture set)."""
    ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.data.update()


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ---------------------------------------------------------------- bake
def bake_material(name, hexcol, rough, grad=None, bump=None):
    """Procedural source material for the bake. grad = (z0, z1, amount): darker toward z0.
    bump = "bubbles": soft embossed bubbles (normal map only)."""
    m = bpy.data.materials.new("bake_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    geo = nodes.new("ShaderNodeNewGeometry")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geo.outputs["Position"], sep.inputs["Vector"])

    def mrange(x, a, b, c, d):
        n = nodes.new("ShaderNodeMapRange")
        n.clamp = True
        for k, v in zip(("From Min", "From Max", "To Min", "To Max"), (a, b, c, d)):
            n.inputs[k].default_value = v
        links.new(x, n.inputs["Value"])
        return n.outputs["Result"]

    base = nodes.new("ShaderNodeRGB")
    base.outputs[0].default_value = lin(hexcol)
    albedo = base.outputs[0]
    if grad:
        z0, z1, amt = grad
        fac = mrange(sep.outputs["Z"], z0, z1, 1.0 - amt, 1.0)
        mul = nodes.new("ShaderNodeVectorMath")
        mul.operation = "SCALE"
        links.new(albedo, mul.inputs[0])
        links.new(fac, mul.inputs["Scale"])
        albedo = mul.outputs["Vector"]
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 2.0
    links.new(geo.outputs["Position"], noise.inputs["Vector"])
    rsock = mrange(noise.outputs["Fac"], 0.3, 0.7, rough - 0.03, rough + 0.03)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(albedo, bsdf.inputs["Base Color"])
    links.new(rsock, bsdf.inputs["Roughness"])
    if bump == "bubbles":
        vor = nodes.new("ShaderNodeTexVoronoi")
        vor.voronoi_dimensions = "3D"
        vor.feature = "F1"
        vor.inputs["Scale"].default_value = 0.42
        vor.inputs["Randomness"].default_value = 0.75
        links.new(geo.outputs["Position"], vor.inputs["Vector"])
        # a soft dome in the middle of each cell (cells are ~2.4 studs, domes ~1.3 across)
        h = mrange(vor.outputs["Distance"], 0.10, 0.34, 1.0, 0.0)
        sm = nodes.new("ShaderNodeMath")
        sm.operation = "POWER"
        sm.inputs[1].default_value = 1.6
        links.new(h, sm.inputs[0])
        bn = nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = 0.32
        bn.inputs["Distance"].default_value = 0.22
        links.new(sm.outputs[0], bn.inputs["Height"])
        links.new(bn.outputs["Normal"], bsdf.inputs["Normal"])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    m["_h"] = 1
    return {"mat": m, "albedo": albedo, "rough": rsock, "bsdf": bsdf, "out": out}


def _pixels(img):
    arr = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(img.size[1], img.size[0], 4)


def _save(arr, path, colorspace):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = colorspace
    full = np.ones((h, w, 4), dtype=np.float32)
    full[..., :arr.shape[2]] = np.clip(arr[..., :3], 0, 1)
    img.pixels.foreach_set(full.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def dilate(arr, mask, iters=24):
    """Spread baked texels into the empty space round the islands (so mip-maps do not bleed)."""
    arr, mask = arr.copy(), mask.copy()
    for _ in range(iters):
        if mask.all():
            break
        acc = np.zeros_like(arr)
        cnt = np.zeros(mask.shape, dtype=np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ms = np.roll(np.roll(mask, dy, 0), dx, 1)
                acc += np.roll(np.roll(arr, dy, 0), dx, 1) * ms[..., None]
                cnt += ms
        new = (~mask) & (cnt > 0)
        arr[new] = acc[new] / cnt[new][:, None]
        mask |= new
    if not mask.all():
        arr[~mask] = arr[mask].mean(axis=0)
    return arr


def bake_set(scene, objs, mats, size, prefix, ao_groups=None, ao_distance=5.0, ao_strength=0.8,
             ao_tint=(0.66, 0.50, 0.66)):
    """Bake colour (+ soft painted-in shading), roughness and normal maps for objects that share
    one atlas. mats = [bake_material(...)] in slot order. ao_groups = lists of objects that
    shade each other (default: each object alone, so moving pieces leave no shadow behind)."""
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.bake.margin = 0
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BakeWorld")
    scene.world.light_settings.distance = ao_distance
    for ob in objs:
        assert len(ob.data.materials) == len(mats)
        for i, h in enumerate(mats):
            ob.data.materials[i] = h["mat"]   # (clear() would reset every face to slot 0)
    ao_groups = ao_groups or [[o] for o in objs]

    def run(kind):
        img = bpy.data.images.new("bake_" + kind, size, size, alpha=False, float_buffer=True)
        img.colorspace_settings.name = "Non-Color"
        added = []
        for h in mats:
            nt = h["mat"].node_tree
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            for n in nt.nodes:
                n.select = False
            tex.select = True
            nt.nodes.active = tex
            em = None
            if kind in ("color", "rough", "mask"):
                em = nt.nodes.new("ShaderNodeEmission")
                if kind == "mask":
                    em.inputs["Color"].default_value = (1, 1, 1, 1)
                else:
                    nt.links.new(h["albedo"] if kind == "color" else h["rough"], em.inputs["Color"])
                nt.links.new(em.outputs["Emission"], h["out"].inputs["Surface"])
            added.append((h, tex, em))
        scene.cycles.samples = {"ao": 24 if QUICK else 96, "normal": 4}.get(kind, 1)
        first = True
        for grp in ao_groups:
            for o in objs:
                o.hide_render = o not in grp
            for ob in grp:
                bpy.ops.object.select_all(action="DESELECT")
                ob.select_set(True)
                bpy.context.view_layer.objects.active = ob
                if kind == "ao":
                    bpy.ops.object.bake(type="AO", margin=0, use_clear=first)
                elif kind == "normal":
                    bpy.ops.object.bake(type="NORMAL", margin=0, use_clear=first, normal_space="TANGENT",
                                        normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
                else:
                    bpy.ops.object.bake(type="EMIT", margin=0, use_clear=first)
                first = False
        for o in objs:
            o.hide_render = False
        for h, tex, em in added:
            nt = h["mat"].node_tree
            if em:
                nt.links.new(h["bsdf"].outputs["BSDF"], h["out"].inputs["Surface"])
                nt.nodes.remove(em)
            nt.nodes.remove(tex)
        arr = _pixels(img).copy()
        bpy.data.images.remove(img)
        return arr

    mask = run("mask")[..., 0] > 0.5
    color = run("color")[..., :3]          # linear
    rough = run("rough")[..., :3]
    normal = run("normal")[..., :3]
    ao = run("ao")[..., 0]
    # soft shading painted into the colour map: grooves and overhangs lean pink/purple
    occ = np.clip((1.0 - ao) * 1.25, 0, 1) ** 1.2 * ao_strength
    tint = np.array(ao_tint, dtype=np.float32)
    color = color * (1.0 - occ[..., None] * (1.0 - tint))
    srgb = np.where(color <= 0.0031308, color * 12.92, 1.055 * np.clip(color, 0, None) ** (1 / 2.4) - 0.055)
    normal[~mask] = (0.5, 0.5, 1.0)
    paths = {}
    for kind, arr, cs in (("color", srgb, "sRGB"), ("roughness", rough, "Non-Color"), ("normal", normal, "Non-Color")):
        paths[kind] = os.path.join(OUT, "%s_%s.png" % (prefix, kind))
        _save(dilate(arr, mask), paths[kind], cs)
    fill = float(mask.mean())
    print("[bake] %s: %d px maps, %.0f%% of the atlas used" % (prefix, size, fill * 100))
    for h in mats:
        bpy.data.materials.remove(h["mat"])
    return paths


def textured_material(name, paths, flat=False, tint=None):
    """What Roblox will show: the three PNGs (flat = colour map only, for the low-graphics check)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    uvn = nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    def tex(path, cs):
        t = nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = cs
        links.new(uvn.outputs["UV"], t.inputs["Vector"])
        return t

    col = tex(paths["color"], "sRGB").outputs["Color"]
    if tint:
        mx = nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        mx.inputs[7].default_value = lin(tint)
        links.new(col, mx.inputs[6])
        col = mx.outputs[2]
    links.new(col, bsdf.inputs["Base Color"])
    if flat:
        bsdf.inputs["Roughness"].default_value = 0.55
    else:
        links.new(tex(paths["roughness"], "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
        nm = nodes.new("ShaderNodeNormalMap")
        links.new(tex(paths["normal"], "Non-Color").outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def plain_material(name, hexcol, rough=0.3, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    return m


def glass_material(name="GlassPreview"):
    """Stand-in for Roblox Glass at ~0.6 transparency: see-through with a soft reflection."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    tr = nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.97, 1.0, 1)
    gl = nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.04
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.22
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.05
    mr.inputs["To Max"].default_value = 0.65
    links.new(lw.outputs["Facing"], mr.inputs["Value"])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mr.outputs["Result"], mix.inputs["Fac"])
    links.new(tr.outputs["BSDF"], mix.inputs[1])
    links.new(gl.outputs["BSDF"], mix.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- export
def roblox_box(ob):
    """Bounding box in Roblox axes (X right, Y up, Z = -Blender Y)."""
    cos = [ob.matrix_world @ v.co for v in ob.data.vertices]
    lo = Vector([min(c[i] for c in cos) for i in range(3)])
    hi = Vector([max(c[i] for c in cos) for i in range(3)])
    return {
        "size": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
        "center": [round((hi.x + lo.x) / 2, 3), round((hi.z + lo.z) / 2, 3), round(-(hi.y + lo.y) / 2, 3)],
        "tris": tri_count(ob),
    }


def rbx(p):
    """Blender point -> Roblox axes."""
    return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)]


def export_fbx(objs, path, half_turn=True):
    """Same call as build_gumball.py. Like kit.py, the meshes are turned half round for the
    export, which undoes the half turn Roblox gives an imported FBX: in game X = Blender X and
    Z = -Blender Y, as the bounds files say."""
    turn = Matrix.Rotation(math.pi, 4, "Z")
    if half_turn:
        for o in objs:
            o.data.transform(turn)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH"},
        mesh_smooth_type="OFF", use_triangles=True, axis_forward="-Z", axis_up="Y",
        apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    if half_turn:
        for o in objs:
            o.data.transform(turn)


def save_blend(path, keep):
    """Save only the model objects (previews are rebuilt by the script)."""
    for o in list(bpy.data.objects):
        if o not in keep:
            bpy.data.objects.remove(o)
    bpy.ops.wm.save_as_mainfile(filepath=path)


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


# ---------------------------------------------------------------- preview renders
def setup_cycles(scene, samples=64):
    """Preview renders: Cycles on the GPU (Metal) when it is there, else the CPU; at most 128
    samples with the denoiser. HUB_CPU=1 forces the CPU. One Blender at a time (fanless Mac)."""
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 6
    if os.environ.get("HUB_CPU") != "1":
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == "METAL"
            if any(d.use for d in prefs.devices):
                scene.cycles.device = "GPU"
        except Exception as e:
            print("[render] CPU (%s)" % e)
    print("[render] device", scene.cycles.device)
    scene.cycles.samples = min(128, max(12, samples // 4) if QUICK else samples)
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 12
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.film_transparent = False


def studio(scene, lo, hi):
    """Bright soft studio light on a pale neutral sweep; returns the preview-only objects."""
    lo, hi = Vector(lo), Vector(hi)
    R = (hi - lo).length / 2
    made = []
    world = bpy.data.worlds.new("Studio")
    scene.world = world
    world.use_nodes = True
    wn, wl = world.node_tree.nodes, world.node_tree.links
    wn.clear()
    tc = wn.new("ShaderNodeTexCoord")
    sep = wn.new("ShaderNodeSeparateXYZ")
    wl.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = wn.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.72, 0.72, 0.75, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (0.80, 0.84, 0.92, 1)
    wl.new(sep.outputs["Z"], ramp.inputs["Fac"])
    bg = wn.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.6
    wl.new(ramp.outputs["Color"], bg.inputs["Color"])
    wo = wn.new("ShaderNodeOutputWorld")
    wl.new(bg.outputs["Background"], wo.inputs["Surface"])

    fm = bpy.data.meshes.new("PreviewFloor")
    fb = bmesh.new()
    bmesh.ops.create_grid(fb, x_segments=1, y_segments=1, size=max(R * 40, 60))
    bmesh.ops.translate(fb, vec=Vector((0, 0, min(lo.z, 0.0) - 0.002)), verts=fb.verts)
    fb.to_mesh(fm)
    fb.free()
    fmat = bpy.data.materials.new("PreviewFloor")
    fmat.use_nodes = True
    fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.60, 0.60, 0.63, 1)
    fmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    fm.materials.append(fmat)
    floor = bpy.data.objects.new("PreviewFloor", fm)
    floor.is_shadow_catcher = True
    scene.collection.objects.link(floor)
    made.append(floor)

    def sun(name, direction, strength, angle, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "SUN")
        d.energy = strength
        d.angle = math.radians(angle)
        d.color = color
        o = bpy.data.objects.new(name, d)
        o.rotation_euler = (-Vector(direction)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(o)
        made.append(o)
        return o

    # direction = from the model toward the light
    made_suns = [sun("Key", (-0.45, 0.6, 0.85), 1.9, 25, (1.0, 0.98, 0.95)),
                 sun("Fill", (0.8, 0.5, 0.35), 0.45, 60, (0.92, 0.95, 1.0)),
                 sun("Rim", (0.3, -0.8, 0.6), 0.6, 40)]
    cd = bpy.data.cameras.new("PreviewCam")
    cam = bpy.data.objects.new("PreviewCam", cd)
    cd.clip_end = 5000
    scene.collection.objects.link(cam)
    scene.camera = cam
    made.append(cam)
    return {"objects": made, "cam": cam, "suns": made_suns, "floor": floor}


def aim_suns(st, yaw):
    """Turn the lights with the camera (for the four-view sheet)."""
    base = [(-0.45, 0.6, 0.85), (0.8, 0.5, 0.35), (0.3, -0.8, 0.6)]
    rot = Matrix.Rotation(yaw, 3, "Z")
    for o, d in zip(st["suns"], base):
        o.rotation_euler = (-(rot @ Vector(d))).to_track_quat("-Z", "Y").to_euler()


def frame(scene, cam, direction, lo, hi, lens=60, res=(1280, 960), fill=1.0, look=None):
    """Put the camera along `direction` (from the model) so the box lo..hi fills the picture."""
    lo, hi = Vector(lo), Vector(hi)
    mid = Vector(look) if look else (lo + hi) / 2
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    cam.data.lens = lens
    d = Vector(direction).normalized()
    # fit the 8 corners
    fwd = -d
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd)
    aspect = res[0] / res[1]
    tan_h = 18.0 / lens if aspect >= 1 else 18.0 / lens * aspect
    tan_v = tan_h / aspect
    need = 0.0
    for cx in (lo.x, hi.x):
        for cy in (lo.y, hi.y):
            for cz in (lo.z, hi.z):
                p = Vector((cx, cy, cz)) - mid
                depth = p.dot(d)  # toward the camera
                need = max(need, abs(p.dot(right)) / tan_h + depth, abs(p.dot(up)) / tan_v + depth)
    cam.location = mid + d * need / fill * 1.06
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, path):
    scene.render.filepath = path
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as e:
        if scene.cycles.device != "GPU":
            raise
        print("[render] GPU failed (%s); back to the CPU" % str(e)[:80])
        scene.cycles.device = "CPU"
        bpy.ops.render.render(write_still=True)
    print("[render]", path)


def player_block(scene, at):
    """The grey 5-stud-tall, 2-stud-wide 'player' for scale."""
    me = bpy.data.meshes.new("PreviewPlayer")
    b = bmesh.new()
    made = bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=Vector((2, 1, 5)), verts=made["verts"])
    bmesh.ops.translate(b, vec=Vector((at[0], at[1], at[2] + 2.5)), verts=made["verts"])
    b.to_mesh(me)
    b.free()
    me.materials.append(plain_material("PreviewPlayer", "#8C8C96", 0.6))
    ob = bpy.data.objects.new("PreviewPlayer", me)
    scene.collection.objects.link(ob)
    return ob


def sheet(paths, out, cols=None):
    """Stick pictures of the same size side by side (the four-view turn sheet)."""
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        imgs.append(_pixels(im).copy())
        bpy.data.images.remove(im)
    cols = cols or len(imgs)
    rows = [np.concatenate(imgs[i:i + cols], axis=1) for i in range(0, len(imgs), cols)]
    arr = np.concatenate(rows[::-1], axis=0)
    h, w = arr.shape[:2]
    img = bpy.data.images.new("sheet", w, h, alpha=False)
    img.pixels.foreach_set(arr.ravel())
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    for p in paths:
        os.remove(p)
    print("[sheet]", out)


def thumb(src, out, size=(256, 192)):
    im = bpy.data.images.load(src)
    im.scale(*size)
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    print("[thumb]", out)


def standard_previews(scene, prefix, lo, hi, set_flat, view=(0.52, 0.80, 0.26), player=None,
                      samples=64, lens=60, extra=None):
    """beauty (1280 x 960: capped by the lead for the fanless Mac), flat (colour maps only), thumb (256 x 192), turn (4 views).
    set_flat(True/False) switches the model between its full and colour-only materials."""
    setup_cycles(scene, samples)
    st = studio(scene, lo, hi)
    cam = st["cam"]
    pl = player_block(scene, player) if player else None
    blo, bhi = Vector(lo), Vector(hi)
    if pl:
        for i in range(3):
            blo[i] = min(blo[i], player[i] - (1, 0.5, 0)[i])
            bhi[i] = max(bhi[i], player[i] + (1, 0.5, 5)[i])
    frame(scene, cam, view, blo, bhi, lens)
    beauty = os.path.join(PREVIEWS, prefix + "_beauty.png")
    render(scene, beauty)
    thumb(beauty, os.path.join(PREVIEWS, prefix + "_thumb.png"))
    set_flat(True)
    render(scene, os.path.join(PREVIEWS, prefix + "_flat.png"))
    set_flat(False)
    if extra:
        extra(st)
    tmp = []
    for k, (label, yaw) in enumerate((("front", 0), ("right", 90), ("back", 180), ("left", 270))):
        a = math.radians(yaw)
        # yaw 0 = camera in front (+Y); 90 = on the model's right as seen from the front (+X)
        d = Vector((math.sin(a), math.cos(a), 0.16))
        aim_suns(st, -a)
        frame(scene, cam, d, blo, bhi, 70, (640, 720))
        p = os.path.join(PREVIEWS, "%s_turn_%d.png" % (prefix, k))
        render(scene, p)
        tmp.append(p)
    sheet(tmp, os.path.join(PREVIEWS, prefix + "_turn.png"))
    aim_suns(st, 0.0)
    return st


# ---------------------------------------------------------------- gumball pile (previews)
def gumball_paths():
    return {k: os.path.join(GUMBALL, "Gumball_%s.png" % k) for k in ("color", "roughness", "normal")}


def add_pile(scene, pile_json, lo_mesh, origin, flat=False, core_mesh=None):
    """Preview only: put the low-detail gumball at every position of a pile json (Roblox axes),
    tinted with the 8 gumball colours, plus the core."""
    with open(pile_json) as f:
        data = json.load(f)
    mats = [textured_material("PileGum%d%s" % (i, "F" if flat else ""), gumball_paths(), flat=flat, tint=h)
            for i, h in enumerate(GUMBALL_HEX)]
    made = []
    d = data["diameter"]
    for (x, y, z), ci in zip(data["positions"], data["colors"]):
        me = lo_mesh.copy()
        me.materials.clear()
        me.materials.append(mats[ci])
        ob = bpy.data.objects.new("PreviewGum", me)
        ob.scale = (d, d, d)
        ob.location = Vector(origin) + Vector((x, -z, y))
        ob.rotation_euler = (x * 1.3, y * 2.1, z * 0.7)
        scene.collection.objects.link(ob)
        made.append(ob)
    if core_mesh is not None:
        me = core_mesh.copy()
        me.materials.clear()
        me.materials.append(plain_material("PileCore", data["core"]["color_hex"], 0.8))
        ob = bpy.data.objects.new("PreviewCore", me)
        ob.location = Vector(origin)
        scene.collection.objects.link(ob)
        made.append(ob)
    return made


def backface_sheet(scene, st, objs, lo, hi, out):
    """Debug picture: outward faces blue, faces that point the wrong way red (Roblox would not
    draw those). Four views in one image."""
    m = bpy.data.materials.new("BackfaceCheck")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.1, 0.3, 0.9, 1)
    mix.inputs[7].default_value = (1.0, 0.0, 0.0, 1)
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Factor"])
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.5
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(mix.outputs[2], dif.inputs["Color"])
    nt.links.new(mix.outputs[2], em.inputs["Color"])
    nt.links.new(dif.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(add.outputs["Shader"], o.inputs["Surface"])
    old = {ob: list(ob.data.materials) for ob in objs}
    for ob in objs:
        ob.data.materials.clear()
        ob.data.materials.append(m)
    samples = scene.cycles.samples
    scene.cycles.samples = 8
    tmp = []
    for k, (dx, dy, dz) in enumerate(((0.5, 0.8, 0.3), (0.8, -0.5, 0.3), (-0.5, -0.8, 0.5), (-0.6, 0.6, -0.12))):
        frame(scene, st["cam"], (dx, dy, dz), lo, hi, 70, (560, 600))
        p = out.replace(".png", "_%d.png" % k)
        render(scene, p)
        tmp.append(p)
    sheet(tmp, out)
    scene.cycles.samples = samples
    for ob, mats in old.items():
        ob.data.materials.clear()
        for x in mats:
            ob.data.materials.append(x)
    bpy.data.materials.remove(m)
