# Copied from ~/Documents/StealAFish/tools/blender/kit.py (2026-11-25) for its shape
# helpers (Piece.lathe/box/ball/limb/stud...). BubblePop scripts use only the shapes;
# they do their own materials, texture bake and export.
# Shared kit for Steal a Fish's Blender-made models (treadmill, tank frame,
# stalls, Fuse Machine). Copied from the owner's AnimeTD project (same export
# path, proven in Studio) with this game's palette and a few more shapes.
# Each build_*.py script makes one or more pieces with it:
#
#   import kit
#   p = kit.Piece("Treadmill")
#   p.box("Body", (2, 2, 10), (0, 0, 5), chamfer=0.2)
#   p.lathe("Metal", [(3, 0), (3, 1), (3, 1), (2, 1)], segs=8, smooth=False)
#   p.finish()
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_<name>.py
#
# Rules every piece follows:
#   * 1 Blender unit = 1 stud, Z is up, the piece stands on the origin.
#   * One object per material, named after it (see PALETTE). Each becomes one
#     MeshPart in Roblox; its colour and material are set in Lua (the palette
#     colours here are the suggested ones). No textures.
#   * finish() writes art/<Name>.fbx, art/<Name>.bounds.json (where each
#     object's box sits, in Roblox axes: X right, Y up, Z = -Blender Y, plus
#     its triangle count and suggested colour) and art/previews/<Name>.png.
#   * Roblox X = Blender X, Roblox Y = Blender Z, Roblox Z = -Blender Y.
#     A piece that Lua aims with CFrame.lookAt has its front on Roblox -Z,
#     so build its front facing Blender +Y.

from contextlib import contextmanager
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ART = os.path.join(ROOT, "art")
PREVIEWS = os.path.join(ART, "previews")

OCT = math.radians(22.5)  # turn for an eight-sided lathe with flat sides facing the axes
QUAD = math.radians(45)  # the same for a four-sided one

# name: (rgb 0-255, metallic, roughness, glow[, alpha]). The suggested Roblox
# colour of each mesh; previews use them too. Glowing things are dark
# (bright Neon blows out to white in the game).
PALETTE = {
    "Body": ((52, 58, 78), 0.0, 0.5, 0),  # dark blue-grey casing
    "BodyLight": ((225, 230, 240), 0.0, 0.4, 0),  # white casing
    "Dark": ((26, 28, 36), 0.0, 0.7, 0),  # rubber, belts, vents
    "Metal": ((176, 186, 200), 1.0, 0.35, 0),  # steel
    "Accent": ((255, 140, 30), 0.0, 0.4, 0),  # the bright colour (recoloured per use)
    "Accent2": ((40, 200, 230), 0.0, 0.4, 0),  # second bright colour
    "Red": ((230, 60, 60), 0.0, 0.4, 0),
    "Mark": ((235, 238, 245), 0.0, 0.5, 0),  # painted marks, dial faces
    "Screen": ((16, 70, 100), 0.0, 0.3, 1.2),  # Neon, dark
    "Glow": ((40, 190, 150), 0.0, 0.3, 2.5),  # Neon
    "Core": ((110, 50, 200), 0.0, 0.3, 3.0),  # Neon
    "Glass": ((175, 220, 245), 0.0, 0.05, 0, 0.3),  # Glass / see-through
    "Liquid": ((40, 150, 220), 0.0, 0.1, 0.4, 0.75),
    "Wood": ((172, 120, 72), 0.0, 0.7, 0),
    "WoodDark": ((104, 68, 44), 0.0, 0.7, 0),
    "Stone": ((120, 124, 134), 0.0, 0.9, 0),
    "Awning": ((70, 150, 230), 0.0, 0.8, 0),  # the coloured stripes (recoloured per stand)
    "AwningWhite": ((245, 242, 232), 0.0, 0.8, 0),
    "Sign": ((250, 244, 226), 0.0, 0.6, 0),
    "Rope": ((214, 190, 140), 0.0, 0.9, 0),
    # candy colours (owner, 2026-11-19: bright, playful, flashy, for ages 8-14)
    "Pink": ((255, 70, 170), 0.0, 0.35, 0),
    "Cyan": ((30, 200, 255), 0.0, 0.35, 0),
    "Lime": ((150, 235, 50), 0.0, 0.35, 0),
    "Yellow": ((255, 215, 40), 0.0, 0.35, 0),
    "Purple": ((150, 80, 245), 0.0, 0.35, 0),
    "Orange": ((255, 140, 30), 0.0, 0.35, 0),
    "White": ((250, 250, 255), 0.0, 0.35, 0),
    "GlowCyan": ((0, 120, 170), 0.0, 0.3, 3.0),  # Neon: dark but saturated
    "GlowPink": ((190, 30, 120), 0.0, 0.3, 3.0),
    "GlowLime": ((70, 150, 20), 0.0, 0.3, 3.0),
    "GlowYellow": ((180, 125, 0), 0.0, 0.3, 3.0),
    "Sand": ((180, 158, 108), 0.0, 0.9, 0),  # only in assembled previews
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, palette=None):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    rgb, metallic, rough, glow, *rest = (palette or PALETTE)[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    color = tuple((c / 255) ** 2.2 for c in rgb) + (1,)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if glow:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = glow
    if rest and rest[0] < 1:
        bsdf.inputs["Alpha"].default_value = rest[0]
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
    return m


def place(at=(0, 0, 0), rx=0.0, ry=0.0, rz=0.0, scale=None):
    """Matrix for Piece.group(): scale, then turn round X, Y, Z (radians),
    then move to `at`. scale = (-1, 1, 1) mirrors left to right."""
    m = Matrix.Translation(Vector(at)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
    if scale:
        m = m @ Matrix.Diagonal(Vector((scale[0], scale[1], scale[2], 1)))
    return m


def rrect(width, height, radius, steps=3, center=(0, 0)):
    """Outline [(u, v), ...] of a rectangle with rounded corners."""
    w, h = width / 2 - radius, height / 2 - radius
    out = []
    for k, (cx, cy) in enumerate(((w, h), (-w, h), (-w, -h), (w, -h))):
        for i in range(steps + 1):
            a = math.pi / 2 * (k + i / steps)
            out.append((center[0] + cx + radius * math.cos(a), center[1] + cy + radius * math.sin(a)))
    return out


def arc(center, radius, a0, a1, steps):
    """Points [(u, v), ...] on a circle from angle a0 to a1 (degrees)."""
    return [
        (center[0] + radius * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
         center[1] + radius * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
        for i in range(steps + 1)
    ]


BOLT = [(0.1, 1.0), (-0.45, 0.05), (-0.05, 0.05), (-0.25, -1.0), (0.5, 0.2), (0.08, 0.2), (0.4, 1.0)]  # lightning bolt, 2 tall
STAR = [(math.sin(math.pi * i / 5) * (1.0 if i % 2 == 0 else 0.45), math.cos(math.pi * i / 5) * (1.0 if i % 2 == 0 else 0.45)) for i in range(10)]


def scaled(outline, k, flip=False):
    return [((-u if flip else u) * k, v * k) for u, v in outline]


def can(r, z0, z1, c=0.08, top=True, bottom=False):
    """Lathe profile of a cylinder from z0 to z1 with its rims chamfered."""
    out = []
    out += [(r - c, z0), (r, z0 + c), (r, z0 + c)] if bottom else [(r, z0)]
    out += [(r, z1 - c), (r, z1 - c), (r - c, z1)] if top else [(r, z1)]
    return out


def bend(points, radius, steps=4):
    """Round the corners of a path [(x, y, z), ...]: each inside point is
    replaced by a small arc. For pipes and handrails made with limb()."""
    pts = [Vector(q) for q in points]
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        r = min(radius, (b - a).length * 0.49, (c - b).length * 0.49)
        p0, p1 = b + (a - b).normalized() * r, b + (c - b).normalized() * r
        for i in range(steps + 1):
            t = i / steps
            out.append((1 - t) ** 2 * p0 + 2 * t * (1 - t) * b + t * t * p1)
    out.append(pts[-1])
    return [tuple(q) for q in out]


def rounded(points, steps=6, bulge=0.32):
    """Profile helper: a quarter-round bulge between two (r, z) points."""
    (r0, z0), (r1, z1) = points
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append((r0 + (r1 - r0) * t + math.sin(math.pi * t) * bulge, z0 + (z1 - z0) * t))
    return out


def chamfered(width, height, c, top_extra=0.0):
    """Section [(y, z)] for sweep(): a rectangle standing on z = 0 with its
    four corners cut. top_extra makes the top wider than the bottom."""
    w, t = width / 2, width / 2 + top_extra
    return [
        (-w + c, 0), (w - c, 0), (w, c), (t, height - c),
        (t - c, height), (-t + c, height), (-t, height - c), (-w, c),
    ]


class Piece:
    def __init__(self, name, scale=1.0, palette=None):
        self.name = name
        self.scale = scale
        self.palette = palette or PALETTE
        self.builders = {}

    def bm(self, mat):
        if mat not in self.palette:
            raise KeyError("unknown material " + mat)
        if mat not in self.builders:
            self.builders[mat] = bmesh.new()
        return self.builders[mat]

    @contextmanager
    def group(self, matrix):
        """Everything made inside `with p.group(kit.place(...)):` is moved by
        the matrix afterwards (tilted consoles, mirrored halves, pieces put
        together for an assembled preview). Groups can be nested."""
        before = {m: set(bm.verts) for m, bm in self.builders.items()}
        yield
        for m, bm in self.builders.items():
            old = before.get(m, ())
            verts = [v for v in bm.verts if v not in old]
            if verts:
                bmesh.ops.transform(bm, matrix=matrix, verts=verts)

    # --- shapes -------------------------------------------------------------
    def lathe(self, mat, profile, segs=32, smooth=True, turn=0.0, at=(0, 0, 0), squash=(1, 1), caps=True):
        """Spin a profile [(radius, z), ...] round the Z axis. A point given
        twice in a row makes a hard edge there (the two rings stay separate).
        squash = (x, y) stretches the round shape into an oval. caps = False
        leaves both ends open (for ends hidden inside something else)."""
        bm = self.bm(mat)
        at = Vector(at)
        rings = []
        for r, z in profile:
            ring = []
            for i in range(segs):
                a = turn + 2 * math.pi * i / segs
                ring.append(bm.verts.new(at + Vector((r * math.cos(a) * squash[0], r * math.sin(a) * squash[1], z))))
            rings.append(ring)
        for (pa, a), (pb, b) in zip(zip(profile, rings), zip(profile[1:], rings[1:])):
            if abs(pa[0] - pb[0]) < 1e-6 and abs(pa[1] - pb[1]) < 1e-6:
                continue  # doubled point: hard edge, no faces between
            for i in range(segs):
                j = (i + 1) % segs
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                f.smooth = smooth
        for (r, _), ring, flip in ((profile[0], rings[0], True), (profile[-1], rings[-1], False)):
            if caps and r > 1e-6:
                f = bm.faces.new(ring[::-1] if flip else ring)
                f.smooth = False

    def box(self, mat, size, center, chamfer=0.0, turn=0.0, rot=None, segs=1):
        """Box with chamfered edges. turn = spin round Z about the ORIGIN
        before moving to center (as the pillar does); rot = (x, y, z) angles
        that tilt the box about its own middle. segs > 1 rounds the edges
        instead (smooth-shaded): the chunky toy look."""
        bm = self.bm(mat)
        made = bmesh.ops.create_cube(bm, size=1.0)
        verts = made["verts"]
        bmesh.ops.scale(bm, vec=Vector(size), verts=verts)
        if chamfer > 0:
            edges = list({e for v in verts for e in v.link_edges})
            result = bmesh.ops.bevel(bm, geom=edges, offset=chamfer, segments=segs, profile=0.5, affect="EDGES")
            if segs > 1:
                for f in result["faces"]:
                    f.smooth = True
            verts = list({v for f in result["faces"] for v in f.verts} | {v for v in verts if v.is_valid})
        if turn:
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(turn, 3, "Z"), verts=verts)
        if rot:
            m = Matrix.Rotation(rot[2], 3, "Z") @ Matrix.Rotation(rot[1], 3, "Y") @ Matrix.Rotation(rot[0], 3, "X")
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=m, verts=verts)
        bmesh.ops.translate(bm, vec=Vector(center), verts=verts)

    def sweep(self, mat, section, stations, at=(0, 0, 0), slant=0.0, turn=0.0, smooth=True):
        """Push a section [(y, z), ...] (counter-clockwise seen from +X)
        along X through stations [(x, lift), ...]: a beam, curved if the
        lifts differ. Each side of the section is smooth along the beam and
        hard against its neighbours. slant leans the two end faces outward
        toward the top (studs of X per stud of Z). turn spins it round Z."""
        bm = self.bm(mat)
        at = Vector(at)
        spin = Matrix.Rotation(turn, 3, "Z")
        z0 = min(z for _, z in section)
        last = len(stations) - 1

        def point(i, y, z):
            x, lift = stations[i][0], stations[i][1]
            if slant and i in (0, last):
                x += (-1 if i == 0 else 1) * slant * (z - z0)
            return at + spin @ Vector((x, y, z + lift))

        n = len(section)
        for k in range(n):
            (ya, za), (yb, zb) = section[k], section[(k + 1) % n]
            a = [bm.verts.new(point(i, ya, za)) for i in range(len(stations))]
            b = [bm.verts.new(point(i, yb, zb)) for i in range(len(stations))]
            for i in range(last):
                f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
                f.smooth = smooth
        for i, flip in ((0, False), (last, True)):
            ring = [bm.verts.new(point(i, y, z)) for y, z in section]
            bm.faces.new(ring[::-1] if flip else ring).smooth = False

    def sleeves(self, mat, section, stations, slant=0.0, length=0.9, grow=0.12, at=(0, 0, 0), turn=0.0):
        """Caps (gold, usually) over the two ends of a sweep() beam made
        with the same section, stations and slant."""
        cy = sum(y for y, _ in section) / len(section)
        cz = sum(z for _, z in section) / len(section)
        z0 = min(z for _, z in section)
        fat = [(y + math.copysign(grow, y - cy), z + math.copysign(grow, z - cz)) for y, z in section]
        for a, b, sign in ((stations[0], stations[1], -1), (stations[-1], stations[-2], 1)):
            run = abs(a[0] - b[0])
            t = min(length / run, 1.0)
            inner = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            outer = (a[0] + sign * grow, a[1] + (a[1] - b[1]) / run * grow)
            pair = [inner, outer] if sign > 0 else [outer, inner]
            # only the outer end leans; the inner end is cut square
            bm, o, spin = self.bm(mat), Vector(at), Matrix.Rotation(turn, 3, "Z")

            def point(st, y, z, lean):
                return o + spin @ Vector((st[0] + (sign * slant * (z - z0) if lean else 0.0), y, z + st[1]))

            n = len(fat)
            ends = [(st, st is outer) for st in pair]
            for k in range(n):
                (ya, za), (yb, zb) = fat[k], fat[(k + 1) % n]
                va = [bm.verts.new(point(st, ya, za, lean)) for st, lean in ends]
                vb = [bm.verts.new(point(st, yb, zb, lean)) for st, lean in ends]
                bm.faces.new((va[0], va[1], vb[1], vb[0]))
            for (st, lean), flip in zip(ends, (False, True)):
                ring = [bm.verts.new(point(st, y, z, lean)) for y, z in fat]
                bm.faces.new(ring[::-1] if flip else ring)

    def prism(self, mat, outline, lo, hi, at=(0, 0, 0), axis="z"):
        """Straight-sided solid from a flat outline. axis "z": outline is
        [(x, y), ...] and it runs from height lo to hi. axis "y": outline is
        [(x, z), ...] (a shape seen from the front) and it runs from y = lo
        to y = hi. axis "x": outline is [(y, z), ...] (seen from the side)
        and it runs from x = lo to x = hi."""
        bm = self.bm(mat)
        at = Vector(at)

        def point(u, v, w):
            if axis == "x":
                return at + Vector((w, u, v))
            return at + (Vector((u, v, w)) if axis == "z" else Vector((u, w, v)))

        a = [bm.verts.new(point(u, v, lo)) for u, v in outline]
        b = [bm.verts.new(point(u, v, hi)) for u, v in outline]
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(a[::-1])
        bm.faces.new(b)

    def stud(self, mat, center, radius=0.3, out=(0, -1, 0), length=None):
        """A small four-sided boss (a cut-off pyramid) standing out of a
        surface along `out`. Cheap: 10 triangles."""
        bm = self.bm(mat)
        out = Vector(out).normalized()
        length = length or radius * 0.7
        side = out.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(out)
        c = Vector(center)
        base = [bm.verts.new(c + (side * sx + up * sy) * radius) for sx, sy in ((0, -1), (1, 0), (0, 1), (-1, 0))]
        tip = [bm.verts.new(c + out * length + (side * sx + up * sy) * radius * 0.45) for sx, sy in ((0, -1), (1, 0), (0, 1), (-1, 0))]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((base[i], base[j], tip[j], tip[i]))
        bm.faces.new(tip)

    def ball(self, mat, center, radius, u=8, v=5, smooth=True):
        bm = self.bm(mat)
        made = bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=radius)
        for f in {f for vert in made["verts"] for f in vert.link_faces}:
            f.smooth = smooth
        bmesh.ops.translate(bm, vec=Vector(center), verts=made["verts"])

    def limb(self, mat, points, radii, segs=7, smooth=False, caps=True):
        """A tube that follows a path [(x, y, z), ...] and is radii[i] thick
        at each point: tree trunks, branches, roots. Flat-shaded by default,
        so it reads as carved wood."""
        bm = self.bm(mat)
        pts = [Vector(q) for q in points]
        n = len(pts)
        normal = None
        rings = []
        for i, q in enumerate(pts):
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            if normal is None:
                normal = t.cross(Vector((0, 0, 1)))
                if normal.length < 1e-4:
                    normal = Vector((1, 0, 0))
            normal = (normal - t * normal.dot(t)).normalized()
            side = t.cross(normal)
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                ring.append(bm.verts.new(q + (normal * math.cos(a) + side * math.sin(a)) * radii[i]))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for k in range(segs):
                j = (k + 1) % segs
                bm.faces.new((a[k], a[j], b[j], b[k])).smooth = smooth
        if caps:
            bm.faces.new(rings[0][::-1]).smooth = False
            bm.faces.new(rings[-1]).smooth = False

    # --- output ---------------------------------------------------------------
    def finish(self, view=(0.62, -0.78, 0.32), shots=None, weld=(), export=True, lens=50, res=(1100, 1100)):
        """Make the objects, export the FBX and the bounds file, render the
        preview. view = direction from the piece to the camera. shots =
        {suffix: (camera position, look-at, lens, width, height)} for extra
        or hand-placed renders (given instead of the automatic one)."""
        reset()
        scene = bpy.context.scene
        objects, bounds, tris = [], {}, 0
        lo_all, hi_all = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for name, bm in self.builders.items():
            if name in weld:
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            if self.scale != 1.0:
                bmesh.ops.scale(bm, vec=Vector((self.scale,) * 3), verts=bm.verts)
            lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
            hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
            for i in range(3):
                lo_all[i], hi_all[i] = min(lo_all[i], lo[i]), max(hi_all[i], hi[i])
            # Roblox puts each mesh's origin at the middle of its box; Y is up
            bounds[name] = {
                "size": [round(hi.x - lo.x, 4), round(hi.z - lo.z, 4), round(hi.y - lo.y, 4)],
                "center": [round((hi.x + lo.x) / 2, 4), round((hi.z + lo.z) / 2, 4), round(-(hi.y + lo.y) / 2, 4)],
            }
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
            mesh = bpy.data.meshes.new(name)
            bm.to_mesh(mesh)
            bm.free()
            mesh.materials.append(material(name, self.palette))
            obj = bpy.data.objects.new(name, mesh)
            scene.collection.objects.link(obj)
            objects.append(obj)
            count = sum(len(p.vertices) - 2 for p in mesh.polygons)
            bounds[name]["tris"] = count
            entry = self.palette[name]
            bounds[name]["color"] = list(entry[0])
            if entry[3]:
                bounds[name]["neon"] = True
            if len(entry) > 4:
                bounds[name]["transparency"] = round(1 - entry[4], 2)
            tris += count
        self.builders = {}
        size = hi_all - lo_all
        print(f"[{self.name}] {len(objects)} objects ({', '.join(o.name for o in objects)}), {tris} tris, "
              f"{size.x:.2f} wide x {size.z:.2f} tall x {size.y:.2f} deep")

        if export:
            os.makedirs(ART, exist_ok=True)
            # Roblox imports an FBX turned half round (checked in Studio with
            # the stall: its X = -Blender X and its Z = +Blender Y). Turning
            # the meshes half round for the export undoes that, so in the
            # game X = Blender X and Z = -Blender Y, as the bounds file says.
            half_turn = Matrix.Rotation(math.pi, 4, "Z")
            for o in objects:
                o.data.transform(half_turn)
            bpy.ops.object.select_all(action="DESELECT")
            for o in objects:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objects[0]
            bpy.ops.export_scene.fbx(
                filepath=os.path.join(ART, self.name + ".fbx"),
                use_selection=True,
                object_types={"MESH"},
                mesh_smooth_type="OFF",
                use_triangles=True,
                axis_forward="-Z",
                axis_up="Y",
                apply_scale_options="FBX_SCALE_ALL",
                path_mode="STRIP",
            )
            with open(os.path.join(ART, self.name + ".bounds.json"), "w") as f:
                json.dump(bounds, f, indent=1)
            for o in objects:
                o.data.transform(half_turn)  # back again for the preview

        if shots is None:
            mid = (lo_all + hi_all) / 2
            radius = size.length / 2
            d = Vector(view).normalized()
            fov = 2 * math.atan(18 / lens)  # 36 mm sensor
            pos = mid + d * (radius / math.sin(fov / 2) * 1.02)
            shots = {"": (pos, mid, lens, res[0], res[1])}
        render(self.name, shots, lo_all, hi_all)
        return tris


def render(name, shots, lo, hi):
    """Preview renders: bright studio lighting on a sandy floor."""
    scene = bpy.context.scene
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            pass
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.66, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scene.world = world

    mid = (Vector(lo) + Vector(hi)) / 2
    R = (Vector(hi) - Vector(lo)).length / 2  # everything below scales with the piece

    floor = bpy.data.meshes.new("Floor")
    fb = bmesh.new()
    bmesh.ops.create_grid(fb, x_segments=1, y_segments=1, size=max(R * 12, 20))
    bmesh.ops.translate(fb, vec=Vector((mid.x, mid.y, min(lo[2], 0.0) - 0.001)), verts=fb.verts)
    fb.to_mesh(floor)
    fb.free()
    floor_mat = bpy.data.materials.new("Floor")
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.47, 0.32, 1)
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    floor.materials.append(floor_mat)
    scene.collection.objects.link(bpy.data.objects.new("Floor", floor))

    first = next(iter(shots.values()))
    side = Vector(first[0]) - mid
    side.z = 0
    side = side.normalized() if side.length > 1e-6 else Vector((0, -1, 0))
    right = Vector((-side.y, side.x, 0))

    def lamp(offset, watts, color, size):
        data = bpy.data.lights.new("AREA", "AREA")
        data.energy = watts * R * R
        data.color = color
        data.size = size * R
        obj = bpy.data.objects.new("Lamp", data)
        obj.location = mid + side * offset[0] * R + right * offset[1] * R + Vector((0, 0, offset[2] * R))
        obj.rotation_euler = (mid - obj.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)

    lamp((1.6, 1.5, 1.8), 70, (1.0, 0.96, 0.9), 1.5)  # warm key
    lamp((1.4, -2.0, 0.6), 22, (0.62, 0.72, 1.0), 2.0)  # cool fill
    lamp((-1.8, -0.6, 1.6), 30, (1.0, 0.9, 0.8), 1.2)  # rim

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.clip_end = 5000
    os.makedirs(PREVIEWS, exist_ok=True)
    for suffix, (pos, target, lens, w, h) in shots.items():
        cam.location = pos
        cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        cam_data.lens = lens
        scene.render.resolution_x, scene.render.resolution_y = w, h
        scene.render.filepath = os.path.join(PREVIEWS, name + (("_" + suffix) if suffix else "") + ".png")
        bpy.ops.render.render(write_still=True)
        print(f"[{name}] rendered {scene.render.filepath}")
