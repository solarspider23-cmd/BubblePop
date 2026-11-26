# BubblePop recycler: "Recycler_Muncher" (nickname Chompy), the machine in the
# middle of the hub where players sell their plastic scraps.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_recycler_muncher.py
#   (add "-- fast" for quick low-sample previews, "-- qa" for extra side/top/back check renders
#    in the scratch folder given by env RECYCLER_QA, default art/previews/qa)
#
# Look: a round, pot-bellied mint machine with a big yellow funnel "mouth" on
# top (scraps go in there), two round gauge eyes, pink cheeks, a big round
# porthole belly with a white frame, little white teeth along its top and a
# pile of colourful shredded plastic inside, a coin chute on the front-right
# that spits gold coins onto a tray, a pull lever on the left, a vent on the
# back and a little glowing antenna. Toy-like, chunky, readable.
#
# Conventions (same as build_bubblewrap.py / StealAFish kit):
#   * 1 unit = 1 stud, Blender +Z up, origin = bottom centre of the footprint.
#   * Front (the face) looks along Blender +Y = Roblox -Z.
#   * FBX: meshes turned half round about Z for the export, axis_forward -Z,
#     axis_up Y, FBX_SCALE_ALL, triangulated, path_mode STRIP.
#
# Output (art/recycler/):
#   Recycler_Muncher.fbx          3 meshes: Body (textured), Glass, Glow
#   Recycler_Muncher_Body.png     1024 baked toon colour texture for Body
#   Recycler_Muncher.bounds.json  per part size/center in Roblox axes + tris
#   Recycler_Muncher.json         parts list (texture / colour, glass / neon)
#   Recycler_Muncher.blend        the built scene, for later tweaks
# Previews: art/previews/recycler_muncher_front.png, _back.png
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(ROOT, "art", "recycler")
PREV = os.path.join(ROOT, "art", "previews")
QA_DIR = os.environ.get("RECYCLER_QA") or os.path.join(PREV, "qa")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
QA = "qa" in ARGS
os.makedirs(ART, exist_ok=True)
os.makedirs(PREV, exist_ok=True)
sys.path.insert(0, HERE)
import kit  # noqa: E402

NAME = "Recycler_Muncher"
TEX = 1024

# ---------------------------------------------------------------- colours (0-255)
COL = {
    "Mint": (70, 214, 182),       # the body
    "MintDeep": (28, 160, 150),   # trims on the body
    "Yellow": (255, 206, 40),     # funnel, base, bezels, chute
    "White": (250, 250, 246),     # frame, rim, collar, teeth
    "Dark": (38, 46, 78),         # pupils, slot, throat, vent slats
    "Cavity": (40, 74, 138),      # inside the belly window
    "Pink": (255, 118, 172),      # cheeks, lever knob, bits
    "Gold": (255, 186, 20),       # coins
    "Silver": (205, 215, 230),    # bolts
    "BitBlue": (80, 185, 255),
    "BitLime": (140, 230, 60),
    "BitOrange": (255, 140, 40),
    "BitPurple": (170, 110, 250),
    "Bubble": (165, 222, 255),    # decorative bubbles on the sides and back
}
GLASS_RGB = (190, 235, 255)
GLOW_RGB = (255, 196, 30)   # suggested Neon colour (warm yellow); tone down in Studio if it blows out

PAL = {k: (v, 0.0, 0.4, 0) for k, v in COL.items()}
PAL["Glass"] = (GLASS_RGB, 0.0, 0.05, 0, 0.3)
PAL["Glow"] = (GLOW_RGB, 0.0, 0.3, 3.0)

p = kit.Piece(NAME, palette=PAL)
SEG = 24

# ---------------------------------------------------------------- body profile
# a smooth pot-belly: many thin rings so the baked toon bands follow round curves
BODY = [(1.72 + 0.28 * math.sin(math.pi * 0.5 * min(1.0, (z - 0.55) / 0.5)) - 0.06 * ((z - 1.8) / 1.65) ** 4 * ((z > 1.8) * 1.0)
         - 0.21 * max(0.0, (z - 2.45) / 1.0) ** 2, z)
        for z in (0.55, 0.64, 0.75, 0.9, 1.1, 1.4, 1.8, 2.2, 2.5, 2.8, 3.05, 3.25, 3.45)]


def body_r(z):
    for (r0, z0), (r1, z1) in zip(BODY, BODY[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return BODY[-1][0]


def on_body(phi_deg, z, out=0.0):
    """Matrix putting local +Z on the outward normal of the body at angle phi
    (0 = front +Y, positive toward +X), height z. Local X runs along the
    surface to the right, local -Y is world up."""
    phi = math.radians(phi_deg)
    r = body_r(z) + out
    return kit.place((r * math.sin(phi), r * math.cos(phi), z), rx=-math.pi / 2, rz=-phi)


def up(u, v):  # local offset with v = world up (see on_body)
    return (u, -v)


# ---------------------------------------------------------------- base
p.lathe("Yellow", kit.can(2.2, 0.0, 0.55, 0.12, bottom=True), SEG)
p.lathe("Glow", [(2.215, 0.2), (2.215, 0.32)], SEG, caps=False, smooth=True)
p.lathe("MintDeep", kit.can(1.95, 0.5, 0.68, 0.06), SEG)
for i in range(8):
    a = 2 * math.pi * (i + 0.5) / 8
    p.lathe("Silver", kit.can(0.1, 0.55, 0.64, 0.03), 6, at=(2.08 * math.cos(a), 2.08 * math.sin(a), 0))

# ---------------------------------------------------------------- body + collar
p.lathe("Mint", BODY, SEG)
p.lathe("MintDeep", kit.can(1.82, 3.3, 3.45, 0.04), SEG)
p.lathe("White", kit.can(1.78, 3.42, 3.78, 0.1), SEG)

# ---------------------------------------------------------------- funnel (hopper) on top
funnel = [(1.32, 3.72), (1.5, 4.1), (1.8, 4.5), (2.02, 4.85), (2.08, 4.95),
          (1.9, 4.96), (1.62, 4.55), (1.3, 4.25), (1.02, 4.08), (0.0, 4.08)]
p.lathe("Yellow", funnel, SEG, caps=True)
p.lathe("Dark", [(1.04, 4.1), (0.0, 4.1)], SEG, caps=False, smooth=False)
# rolled white rim (a torus)
rim = [(2.0 + 0.14 * math.cos(math.radians(a)), 4.98 + 0.14 * math.sin(math.radians(a))) for a in range(-90, 271, 60)]
p.lathe("White", rim, SEG, caps=False)
# yellow stripes down the outside of the funnel (mint) for a toy look
for i in range(6):
    a = 2 * math.pi * i / 6 + math.pi / 6
    d = Vector((math.cos(a), math.sin(a), 0))
    pts = [d * 1.37 + Vector((0, 0, 3.85)), d * 1.62 + Vector((0, 0, 4.28)), d * 1.93 + Vector((0, 0, 4.72))]
    p.limb("MintDeep", [tuple(q) for q in pts], [0.07, 0.07, 0.07], segs=5, smooth=True)

# antenna at the back of the rim with a glowing ball
p.limb("Dark", [(0, -1.96, 5.0), (0, -1.98, 5.2), (0, -1.95, 5.25)], [0.055, 0.055, 0.055], segs=6)
p.ball("Glow", (0, -1.95, 5.34), 0.15, 8, 5)
# white teeth round the throat: it chomps whatever you throw in
for i in range(10):
    a = 2 * math.pi * (i + 0.5) / 10
    d = Vector((math.cos(a), math.sin(a), 0))
    p.stud("White", tuple(d * 1.0 + Vector((0, 0, 4.1))), 0.1, out=tuple(Vector((0, 0, 1)) - d * 0.35), length=0.17)

# ---------------------------------------------------------------- belly window (front)
WZ = 1.8      # window centre height
WY = 1.62     # frame back plane (buried in the body)
with p.group(kit.place((0, WY, WZ), rx=-math.pi / 2)):
    frame = [(0.95, 0.0), (0.97, 0.3), (0.93, 0.42), (0.86, 0.47), (0.79, 0.44), (0.76, 0.36),
             (0.76, 0.2), (0.6, 0.2), (0.6, 0.0), (0.95, 0.0)]
    p.lathe("White", frame, SEG, caps=False)
    p.lathe("Cavity", [(0.77, 0.23), (0.0, 0.23)], SEG, caps=False, smooth=False)
    p.lathe("Glass", [(0.78, 0.4), (0.7, 0.55), (0.48, 0.68), (0.0, 0.73)], SEG, caps=False)
    for i in range(8):   # yellow bolts on the frame
        a = 2 * math.pi * (i + 0.5) / 8
        p.stud("Yellow", (0.875 * math.cos(a), 0.875 * math.sin(a), 0.46), 0.06, out=(0, 0, 1), length=0.05)
# teeth hanging from the top of the window (it munches!)
for x in (-0.39, -0.13, 0.13, 0.39):
    top = WZ + math.sqrt(0.76 ** 2 - x * x) + 0.04
    p.box("White", (0.22, 0.12, 0.3), (x, WY + 0.33, top - 0.15), 0.05)
# shredded plastic bits piled inside
rng = random.Random(7)
BITS = ["Pink", "Yellow", "BitBlue", "BitLime", "BitOrange", "BitPurple", "White"]
placed = 0
while placed < 30:
    u, v = rng.uniform(-0.68, 0.68), rng.uniform(-0.7, 0.35)
    d = math.hypot(u, v)
    if d > 0.66 or (v > -0.15 and rng.random() < 0.55):
        continue
    ymax = WY + 0.4 + 0.25 * max(0.0, 1 - (d / 0.78) ** 2)
    y = rng.uniform(WY + 0.27, ymax - 0.08)
    s = rng.uniform(0.09, 0.16)
    p.box(BITS[placed % len(BITS)], (s * 1.6, s * 0.5, s), (u, y, WZ + v), 0.0,
          rot=(rng.uniform(0, 6.3), rng.uniform(0, 6.3), rng.uniform(0, 6.3)))
    placed += 1

# ---------------------------------------------------------------- face: gauge eyes + cheeks
for side in (-1, 1):
    with p.group(on_body(side * 18, 3.08, -0.12) @ kit.place(rx=math.radians(-12))):
        p.lathe("Yellow", kit.can(0.44, 0.0, 0.3, 0.07), 20)
        p.lathe("White", [(0.355, 0.3), (0.34, 0.35), (0.23, 0.4), (0.0, 0.42)], 20, caps=False)
        pu, pv = up(-side * 0.05, -0.04)   # pupils look a little down and in, at the player
        p.lathe("Dark", [(0.17, 0.0), (0.14, 0.04), (0.0, 0.06)], 12, at=(pu, pv, 0.375), caps=False)
        hu, hv = up(-side * 0.05 + 0.06, 0.03)
        p.ball("White", (hu, hv, 0.44), 0.045, 6, 4)
    with p.group(on_body(side * 33, 2.62, -0.005)):
        p.lathe("Pink", [(0.17, 0.0), (0.13, 0.025), (0.0, 0.035)], 12, caps=False)

# ---------------------------------------------------------------- coin chute (front right)
CHUTE = 55   # degrees from the front toward +X
with p.group(kit.place((0, 0, 0), rz=-math.radians(CHUTE) + math.pi / 2)):
    # local +X points out of the body here
    p.box("Yellow", (0.5, 0.86, 0.6), (1.9, 0, 1.38), 0.12, segs=2)        # hood
    p.box("Dark", (0.08, 0.6, 0.24), (2.13, 0, 1.3), 0.03)                  # coin slot
    p.ball("Glow", (1.98, -0.22, 1.69), 0.08, 8, 4)                         # two lamps on the hood
    p.ball("Glow", (1.98, 0.22, 1.69), 0.08, 8, 4)
    tilt = math.radians(14)
    with p.group(kit.place((2.0, 0, 1.12), ry=tilt)):
        p.box("White", (0.75, 0.7, 0.07), (0.33, 0, 0), 0.02)              # tray
        for s in (-1, 1):
            p.box("Yellow", (0.75, 0.07, 0.16), (0.33, s * 0.36, 0.05), 0.02)  # tray rails
        p.box("Yellow", (0.07, 0.7, 0.14), (0.7, 0, 0.05), 0.02)           # tray lip
        p.lathe("Gold", kit.can(0.16, 0.035, 0.09, 0.02), 10, at=(0.36, 0.13, 0))
        p.lathe("Gold", kit.can(0.16, 0.035, 0.09, 0.02), 10, at=(0.56, -0.12, 0))
    # a coin popping out of the slot
    with p.group(kit.place((2.14, 0.05, 1.33), ry=math.radians(70))):
        p.lathe("Gold", kit.can(0.15, -0.03, 0.03, 0.02), 10)
# a little coin pile on the base ledge, front left
for k, (a, h) in enumerate(((-48, 0.0), (-48, 0.06), (-56, 0.0), (-42, 0.0))):
    r = 2.0 if k != 2 else 2.02
    ang = math.radians(90 - a)
    p.lathe("Gold", kit.can(0.15, 0.55 + h, 0.61 + h, 0.02), 10,
            at=(r * math.cos(ang) * 1.0, r * math.sin(ang), 0))

# ---------------------------------------------------------------- lever (left side)
with p.group(on_body(-90, 2.1, -0.05)):
    p.lathe("Yellow", kit.can(0.24, 0.0, 0.16, 0.05), 12)
    p.lathe("Dark", kit.can(0.12, 0.16, 0.22, 0.03), 8)
p.limb("Silver", [(-2.08, 0, 2.1), (-2.1, 0.08, 2.5), (-2.1, 0.12, 2.82)], [0.06, 0.06, 0.06], segs=6, smooth=True)
p.ball("Pink", (-2.1, 0.12, 2.92), 0.17, 10, 6)

# ---------------------------------------------------------------- bubbles (the game's motif) on the sides/back
for phi, z, r in ((-128, 2.75, 0.3), (-142, 2.2, 0.2), (-118, 1.85, 0.16), (125, 2.6, 0.26), (140, 1.95, 0.18), (112, 1.45, 0.2)):
    with p.group(on_body(phi, z, -0.03)):
        p.lathe("Bubble", [(r, 0.0), (r * 0.8, r * 0.5), (0.0, r * 0.72)], 10, caps=False)
        p.ball("White", up(-r * 0.3, r * 0.3) + (r * 0.62,), r * 0.2, 6, 4)

# ---------------------------------------------------------------- back: vent panel + pipe
with p.group(on_body(180, 2.0, -0.02)):
    p.box("White", (1.25, 1.05, 0.32), (0, 0, 0), 0.1)
    for k in range(4):
        p.box("Dark", (0.95, 0.09, 0.1), (0, -0.33 + k * 0.22, 0.17), 0.03)
    for su in (-1, 1):
        for sv in (-1, 1):
            p.stud("Silver", (su * 0.52, sv * 0.42, 0.16), 0.045, out=(0, 0, 1), length=0.04)
# a bent pipe from the vent down into the base
pipe = kit.bend([(0.85, -1.9, 1.5), (0.85, -2.08, 1.5), (0.85, -2.08, 0.62)], 0.18, 3)
p.limb("Yellow", pipe, [0.11] * len(pipe), segs=8, smooth=True)
p.lathe("MintDeep", kit.can(0.16, 0.55, 0.68, 0.03), 10, at=(0.85, -2.08, 0))


# ================================================================= build objects
def toon_mat(name, rgb):
    """Bake material: base colour x toon light bands x banded contact shadow."""
    m = bpy.data.materials.new("bake_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    em = N("ShaderNodeEmission")
    geo = N("ShaderNodeNewGeometry")
    dot = N("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = Vector((0.28, 0.42, 1.0)).normalized()
    ramp = N("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    # positions are on N.L mapped from [-1, 1] to [0, 1]
    bands = [(0.0, (0.76, 0.74, 0.86)), (0.42, (0.89, 0.89, 0.95)), (0.64, (1.0, 1.0, 1.0)), (0.93, (1.08, 1.08, 1.06))]
    cr.elements[0].position, cr.elements[0].color = bands[0][0], bands[0][1] + (1,)
    cr.elements[1].position, cr.elements[1].color = bands[1][0], bands[1][1] + (1,)
    for pos, c in bands[2:]:
        e = cr.elements.new(pos)
        e.color = c + (1,)
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    ao = N("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.3
    ao.samples = 16
    aor = N("ShaderNodeValToRGB")
    aor.color_ramp.interpolation = "CONSTANT"
    aor.color_ramp.elements[0].position = 0.0
    aor.color_ramp.elements[0].color = (0.8, 0.8, 0.9, 1)
    aor.color_ramp.elements[1].position = 0.62
    aor.color_ramp.elements[1].color = (1, 1, 1, 1)
    m1 = N("ShaderNodeMix")
    m1.data_type = "RGBA"
    m1.blend_type = "MULTIPLY"
    m1.inputs[0].default_value = 1.0
    m1.inputs[6].default_value = kit_lin(rgb) + (1,)
    m2 = N("ShaderNodeMix")
    m2.data_type = "RGBA"
    m2.blend_type = "MULTIPLY"
    m2.inputs[0].default_value = 1.0
    L(geo.outputs["Normal"], dot.inputs[0])
    L(dot.outputs["Value"], mr.inputs["Value"])
    L(mr.outputs[0], ramp.inputs[0])
    L(ramp.outputs[0], m1.inputs[7])
    L(m1.outputs[2], m2.inputs[6])
    L(ao.outputs["AO"], aor.inputs[0])
    L(aor.outputs[0], m2.inputs[7])
    L(m2.outputs[2], em.inputs[0])
    L(em.outputs[0], out.inputs["Surface"])
    return m


def kit_lin(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(f(c) for c in rgb)


def make_obj(name, bm):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tris(ob):
    return len(ob.data.polygons)


kit.reset()
sc = bpy.context.scene
builders, p.builders = p.builders, {}
body_parts, glass, glow = [], None, None
for mat, bm in builders.items():
    ob = make_obj(mat, bm)
    if mat == "Glass":
        ob.name = ob.data.name = "Glass"
        glass = ob
    elif mat == "Glow":
        ob.name = ob.data.name = "Glow"
        glow = ob
    else:
        ob.data.materials.append(toon_mat(mat, COL[mat]))
        body_parts.append(ob)

# join body parts into one mesh
bpy.ops.object.select_all(action="DESELECT")
for o in body_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = body_parts[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = "Body"

# remove faces nobody can see: buried inside another part, or facing the floor
from mathutils.bvhtree import BVHTree  # noqa: E402
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm)


def buried(pt, n):
    loc, hn, idx, dist = tree.ray_cast(pt + n * 2e-4, n, 4.0)
    return loc is not None and hn.dot(n) > 0.05


dead = []
for fc in bm.faces:
    c = fc.calc_center_median()
    n = fc.normal
    if n.z < -0.98 and c.z < 0.01:
        dead.append(fc)
        continue
    pts = [c] + [c + (v.co - c) * 0.9 for v in fc.verts]
    if all(buried(q, n) for q in pts):
        dead.append(fc)
print("CULLED", len(dead), "hidden faces of", len(bm.faces))
bmesh.ops.delete(bm, geom=dead, context="FACES")
bm.to_mesh(body.data)
bm.free()

# UVs: smart project, packed
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.006, rotate=True)
bpy.ops.object.mode_set(mode="OBJECT")

# bake the toon colour into one texture
img = bpy.data.images.new(NAME + "_Body", TEX, TEX, alpha=False)
img.colorspace_settings.name = "sRGB"
for m in body.data.materials:
    n = m.node_tree.nodes.new("ShaderNodeTexImage")
    n.image = img
    m.node_tree.nodes.active = n
glass.hide_render = True
glow.hide_render = True
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 16 if FAST else 64
sc.render.bake.margin = 6
sc.render.bake.use_clear = True
bpy.ops.object.bake(type="EMIT")
img.filepath_raw = os.path.join(ART, NAME + "_Body.png")
img.file_format = "PNG"
img.save()
glass.hide_render = False
glow.hide_render = False
print("BAKED", img.filepath_raw)


# ---------------------------------------------------------------- final (Roblox-like) materials
def plain_mat(name, rgb=None, image=None, alpha=1.0, emit=0.0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True   # Roblox culls back faces too
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Specular IOR Level"].default_value = 0.35
    if image is not None:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = image
        m.node_tree.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    else:
        bs.inputs["Base Color"].default_value = kit_lin(rgb) + (1,)
    if emit:
        bs.inputs["Emission Color"].default_value = kit_lin(rgb) + (1,)
        bs.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        bs.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


body.data.materials.clear()
body.data.materials.append(plain_mat("Recycler_Body", image=img))
for poly in body.data.polygons:
    poly.material_index = 0
glass.data.materials.append(plain_mat("Recycler_Glass", GLASS_RGB, alpha=0.35, rough=0.05))
glow.data.materials.append(plain_mat("Recycler_Glow", GLOW_RGB, emit=2.0))
# smooth/flat shading as authored stays on the polygons; no UVs needed on Glass/Glow
parts = [body, glass, glow]

# ---------------------------------------------------------------- checks + bounds + export
problems = []
for o in parts:
    for poly in o.data.polygons:
        if poly.area < 1e-7:
            problems.append(f"{o.name}: tiny face {poly.index}")
bounds = {}
lo_all, hi_all = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for o in parts:
    xs = [v.co for v in o.data.vertices]
    lo = Vector([min(c[i] for c in xs) for i in range(3)])
    hi = Vector([max(c[i] for c in xs) for i in range(3)])
    for i in range(3):
        lo_all[i], hi_all[i] = min(lo_all[i], lo[i]), max(hi_all[i], hi[i])
    bounds[o.name] = {
        "size": [round(hi.x - lo.x, 4), round(hi.z - lo.z, 4), round(hi.y - lo.y, 4)],
        "center": [round((hi.x + lo.x) / 2, 4), round((hi.z + lo.z) / 2, 4), round(-(hi.y + lo.y) / 2, 4)],
        "tris": tris(o),
        "origin": "bottom centre of footprint (model origin)",
    }
total = sum(tris(o) for o in parts)
bounds["_model"] = {
    "size": [round(hi_all.x - lo_all.x, 4), round(hi_all.z - lo_all.z, 4), round(hi_all.y - lo_all.y, 4)],
    "center": [round((hi_all.x + lo_all.x) / 2, 4), round((hi_all.z + lo_all.z) / 2, 4), round(-(hi_all.y + lo_all.y) / 2, 4)],
    "tris": total,
    "front": "Roblox -Z (Blender +Y)",
}
half_turn = Matrix.Rotation(math.pi, 4, "Z")
for o in parts:
    o.data.transform(half_turn)
bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.fbx(
    filepath=os.path.join(ART, NAME + ".fbx"), use_selection=True, object_types={"MESH"}, mesh_smooth_type="OFF",
    use_triangles=True, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
)
for o in parts:
    o.data.transform(half_turn)
with open(os.path.join(ART, NAME + ".bounds.json"), "w") as f:
    json.dump(bounds, f, indent=1)
manifest = {
    "model": NAME,
    "fbx": NAME + ".fbx",
    "front": "Roblox -Z (Blender +Y); origin at the bottom centre of the footprint",
    "parts": [
        {"name": "Body", "texture": NAME + "_Body.png", "material": "SmoothPlastic", "glass": False, "neon": False},
        {"name": "Glass", "color": list(GLASS_RGB), "material": "Glass", "transparency": 0.6, "glass": True, "neon": False},
        {"name": "Glow", "color": list(GLOW_RGB), "material": "Neon", "glass": False, "neon": True},
    ],
    "tris": {o.name: tris(o) for o in parts} | {"total": total},
}
with open(os.path.join(ART, NAME + ".json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("EXPORTED", total, "tris", {o.name: tris(o) for o in parts}, "size", bounds["_model"]["size"])
for pr in problems[:20]:
    print("PROBLEM", pr)

# ---------------------------------------------------------------- previews
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 16 if FAST else 64
sc.view_settings.view_transform = "Standard"
sc.render.film_transparent = False
w = bpy.data.worlds.new("Sky")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = kit_lin((205, 230, 252)) + (1,)
bg.inputs["Strength"].default_value = 1.0


def sun(name, d, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = energy
    ld.angle = math.radians(8)
    ld.color = color
    lo_ = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(lo_)
    lo_.rotation_euler = (-Vector(d).normalized()).to_track_quat("-Z", "Y").to_euler()


sun("Key", (0.5, 0.7, 0.9), 2.4, (1.0, 0.97, 0.92))
sun("Fill", (-0.6, -0.5, 0.5), 0.8, (0.85, 0.92, 1.0))
floor_me = bpy.data.meshes.new("Floor")
floor_me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("Floor", floor_me)
sc.collection.objects.link(floor)
floor.data.materials.append(plain_mat("FloorMat", (175, 215, 245), rough=0.7))


def shot(path, loc, target=(0, 0, 2.55), lens=50, res=(1100, 1100)):
    cd = bpy.data.cameras.new("Cam")
    co = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    sc.camera = co
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if FAST else 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


D = 15.5
shot(os.path.join(PREV, "recycler_muncher_front.png"), (D * 0.42, D * 0.87, 6.4))
shot(os.path.join(PREV, "recycler_muncher_back.png"), (-D * 0.5, -D * 0.84, 6.4))
if QA:
    os.makedirs(QA_DIR, exist_ok=True)
    shot(os.path.join(QA_DIR, "rm_front.png"), (0, D, 2.8), res=(800, 800))
    shot(os.path.join(QA_DIR, "rm_side_r.png"), (D, 0, 2.8), res=(800, 800))
    shot(os.path.join(QA_DIR, "rm_side_l.png"), (-D, 0, 2.8), res=(800, 800))
    shot(os.path.join(QA_DIR, "rm_top.png"), (0.01, 2.5, D + 2), target=(0, 0, 2.5), res=(800, 800))
    shot(os.path.join(QA_DIR, "rm_close.png"), (2.2, 6.5, 3.0), target=(0, 1.5, 2.3), res=(900, 900))
    shot(os.path.join(QA_DIR, "rm_close_left.png"), (-6.5, 2.0, 3.2), target=(0, 0, 2.4), res=(900, 900))
    shot(os.path.join(QA_DIR, "rm_close_back.png"), (1.5, -7.0, 3.6), target=(0, 0, 2.6), res=(900, 900))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, NAME + ".blend"))
if os.path.exists(os.path.join(ART, NAME + ".blend1")):
    os.remove(os.path.join(ART, NAME + ".blend1"))
