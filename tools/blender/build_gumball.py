# Gumball: one smooth, glossy, candy-coated sphere for the lobby (machine globe,
# jar, kickable balls). Neutral near-white maps so Roblox can tint it any colour.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_gumball.py
#
# Outputs
#   art/gumball/Gumball.fbx                 1 stud diameter, centred, triangulated
#   art/gumball/Gumball_color.png           1024, neutral near-white, faint mottling + specks
#   art/gumball/Gumball_roughness.png       1024, glossy (~0.1-0.2) with slight variation
#   art/gumball/Gumball_normal.png          1024, OpenGL (Y+) tangent normal, tiny dimples
#   art/gumball/Gumball_metalness.png       1024, black
#   art/gumball/Gumball.blend
#   art/previews/gumball_single.png, art/previews/gumball_colours.png
#
# Mesh: a "cube sphere" (a cube with every face split into N x N, pushed out to a
# sphere with equal-angle spacing), so there are no pinched poles. UVs: each cube
# face gets its own tile in a 3 x 2 layout. All detail comes from 3D noise baked
# in object space, so the texture lines up across the tile edges (no visible seams).
# Axes/export match build_bubblewrap.py (1 Blender unit = 1 stud).

import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "art", "gumball")
PREVIEWS = os.path.join(ROOT, "art", "previews")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREVIEWS, exist_ok=True)

N = 11          # quads per cube-face edge -> 6*N*N*2 = 1452 triangles
RADIUS = 0.5    # 1 stud diameter
TEX = 1024
QUICK = os.environ.get("GUMBALL_QUICK") == "1"

# ------------------------------------------------------------------ reset
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


# ------------------------------------------------------------------ mesh
def build_mesh():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    # cube faces: (normal axis, sign, u axis, v axis), tile (col,row) in a 3x2 atlas
    faces = [
        ((0, 1), (1, 1), (2, 1), (0, 0)),    # +X: u=+Y, v=+Z
        ((0, -1), (1, -1), (2, 1), (1, 0)),  # -X: u=-Y
        ((1, 1), (0, -1), (2, 1), (2, 0)),   # +Y: u=-X
        ((1, -1), (0, 1), (2, 1), (0, 1)),   # -Y: u=+X
        ((2, 1), (0, 1), (1, 1), (1, 1)),    # +Z: u=+X, v=+Y
        ((2, -1), (0, 1), (1, -1), (2, 1)),  # -Z: u=+X, v=-Y
    ]
    pad = 8.0 / TEX            # gap around each tile (texels -> UV)
    tw, th = 1.0 / 3.0, 1.0 / 2.0
    for (na, ns), (ua, us), (va, vs), (col, row) in faces:
        grid = {}
        for i in range(N + 1):
            for j in range(N + 1):
                a = -1 + 2 * i / N
                b = -1 + 2 * j / N
                # equal-angle spacing so quads are near-even on the sphere
                pa = math.tan(a * math.pi / 4)
                pb = math.tan(b * math.pi / 4)
                p = [0.0, 0.0, 0.0]
                p[na] = ns
                p[ua] = us * pa
                p[va] = vs * pb
                v = Vector(p).normalized() * RADIUS
                grid[i, j] = (v, (i / N, j / N))
        verts = {}
        for k, (co, _) in grid.items():
            verts[k] = bm.verts.new(co)
        for i in range(N):
            for j in range(N):
                ks = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                f = bm.faces.new([verts[k] for k in ks])
                for loop, k in zip(f.loops, ks):
                    s, t = grid[k][1]
                    loop[uv].uv = (col * tw + pad + s * (tw - 2 * pad),
                                   row * th + pad + t * (th - 2 * pad))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    # outward normals
    for f in bm.faces:
        if f.normal.dot(f.calc_center_median()) < 0:
            f.normal_flip()
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY")
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("Gumball")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("Gumball", me)
    sc.collection.objects.link(ob)
    return ob


ball = build_mesh()


# ------------------------------------------------------------------ bake material
def nodes_for(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return nt, nt.nodes, nt.links


def noise(nodes, links, vec, scale, detail=2.0, rough=0.5, w=0.0):
    n = nodes.new("ShaderNodeTexNoise")
    n.noise_dimensions = "4D"
    n.inputs["W"].default_value = w
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    links.new(vec, n.inputs["Vector"])
    return n.outputs["Fac"]


def maprange(nodes, links, x, a, b, c, d):
    m = nodes.new("ShaderNodeMapRange")
    m.clamp = True
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    m.inputs["To Min"].default_value = c
    m.inputs["To Max"].default_value = d
    links.new(x, m.inputs["Value"])
    return m.outputs["Result"]


def math_op(nodes, links, op, a, b):
    m = nodes.new("ShaderNodeMath")
    m.operation = op
    if isinstance(a, float):
        m.inputs[0].default_value = a
    else:
        links.new(a, m.inputs[0])
    if isinstance(b, float):
        m.inputs[1].default_value = b
    else:
        links.new(b, m.inputs[1])
    return m.outputs[0]


src = bpy.data.materials.new("GumballBake")
nt, nodes, links = nodes_for(src)
tc = nodes.new("ShaderNodeTexCoord")
co = tc.outputs["Object"]

# colour: near-white base, soft mottling, a faint uneven-coating band, tiny specks
mottle = maprange(nodes, links, noise(nodes, links, co, 5.0, 4.0, 0.55), 0.3, 0.7, -1.0, 1.0)
coat = maprange(nodes, links, noise(nodes, links, co, 1.4, 1.0, 0.5, 3.1), 0.35, 0.65, -1.0, 1.0)
vor = nodes.new("ShaderNodeTexVoronoi")
vor.voronoi_dimensions = "3D"
vor.inputs["Scale"].default_value = 55.0
vor.inputs["Randomness"].default_value = 1.0
links.new(co, vor.inputs["Vector"])
# speck mask: only cells whose random colour is high get a small dot in the middle
dot = maprange(nodes, links, vor.outputs["Distance"], 0.06, 0.14, 1.0, 0.0)
sep = nodes.new("ShaderNodeSeparateColor")
links.new(vor.outputs["Color"], sep.inputs["Color"])
pick = maprange(nodes, links, sep.outputs["Red"], 0.80, 0.82, 0.0, 1.0)
speck = math_op(nodes, links, "MULTIPLY", dot, pick)
v = math_op(nodes, links, "MULTIPLY", mottle, 0.022)
v = math_op(nodes, links, "ADD", v, math_op(nodes, links, "MULTIPLY", coat, 0.018))
v = math_op(nodes, links, "ADD", v, math_op(nodes, links, "MULTIPLY", speck, -0.07))
albedo = math_op(nodes, links, "ADD", v, 0.90)   # linear ~0.90 -> sRGB ~0.95

# roughness: glossy shell, slightly duller patches and specks
rnoise = maprange(nodes, links, noise(nodes, links, co, 3.0, 3.0, 0.6, 7.7), 0.3, 0.7, 0.0, 1.0)
rough = math_op(nodes, links, "ADD", math_op(nodes, links, "MULTIPLY", rnoise, 0.10), 0.10)
rough = math_op(nodes, links, "ADD", rough, math_op(nodes, links, "MULTIPLY", speck, 0.12))

# bump: tiny shallow dimples + a whisper of large-scale unevenness
dvor = nodes.new("ShaderNodeTexVoronoi")
dvor.voronoi_dimensions = "3D"
dvor.feature = "SMOOTH_F1"
dvor.inputs["Scale"].default_value = 30.0
dvor.inputs["Smoothness"].default_value = 0.6
links.new(co, dvor.inputs["Vector"])
dimple = maprange(nodes, links, dvor.outputs["Distance"], 0.0, 0.6, 0.0, 1.0)
fine = noise(nodes, links, co, 60.0, 2.0, 0.5, 1.3)
height = math_op(nodes, links, "ADD", dimple,
                 math_op(nodes, links, "MULTIPLY", fine, 0.35))
height = math_op(nodes, links, "ADD", height,
                 math_op(nodes, links, "MULTIPLY", coat, 0.15))
bump = nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.08
bump.inputs["Distance"].default_value = 0.004
links.new(height, bump.inputs["Height"])

bsdf = nodes.new("ShaderNodeBsdfPrincipled")
links.new(albedo, bsdf.inputs["Base Color"])
links.new(rough, bsdf.inputs["Roughness"])
links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
outn = nodes.new("ShaderNodeOutputMaterial")
links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
ball.data.materials.append(src)

# ------------------------------------------------------------------ bake
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 4 if QUICK else 16
sc.render.bake.margin = 16
sc.render.bake.margin_type = "EXTEND"
bpy.context.view_layer.objects.active = ball
ball.select_set(True)


def bake_to(name, btype, colorspace, setup=None, **kw):
    img = bpy.data.images.new(name, TEX, TEX, alpha=False, float_buffer=(btype == "NORMAL"))
    img.colorspace_settings.name = colorspace
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    for n in nodes:
        n.select = False
    tex.select = True
    nodes.active = tex
    restore = setup() if setup else None
    bpy.ops.object.bake(type=btype, **kw)
    if restore:
        restore()
    nodes.remove(tex)
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    return img


# colour and roughness are baked as EMIT (exact values, no lighting)
def via_emit(sock):
    def setup():
        em = nodes.new("ShaderNodeEmission")
        links.new(sock, em.inputs["Color"])
        links.new(em.outputs["Emission"], outn.inputs["Surface"])

        def restore():
            links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
            nodes.remove(em)
        return restore
    return setup


bake_to("Gumball_color", "EMIT", "sRGB", via_emit(albedo))
bake_to("Gumball_roughness", "EMIT", "Non-Color", via_emit(rough))
bake_to("Gumball_normal", "NORMAL", "Non-Color", normal_space="TANGENT",
        normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")   # OpenGL (Y+)
met = bpy.data.images.new("Gumball_metalness", TEX, TEX, alpha=False)
met.generated_color = (0, 0, 0, 1)
met.colorspace_settings.name = "Non-Color"
met.filepath_raw = os.path.join(OUT, "Gumball_metalness.png")
met.file_format = "PNG"
met.save()

# reload the saved PNGs (8-bit, as Roblox will see them)
maps = {}
for k in ("color", "roughness", "normal"):
    bpy.data.images.remove(bpy.data.images["Gumball_" + k])
    im = bpy.data.images.load(os.path.join(OUT, "Gumball_%s.png" % k))
    im.colorspace_settings.name = "sRGB" if k == "color" else "Non-Color"
    maps[k] = im

# ------------------------------------------------------------------ final material
fin = bpy.data.materials.new("Gumball")
nt2, n2, l2 = nodes_for(fin)
uvn = n2.new("ShaderNodeUVMap")
uvn.uv_map = "UVMap"
tcol = n2.new("ShaderNodeTexImage"); tcol.image = maps["color"]
trgh = n2.new("ShaderNodeTexImage"); trgh.image = maps["roughness"]
tnrm = n2.new("ShaderNodeTexImage"); tnrm.image = maps["normal"]
for t in (tcol, trgh, tnrm):
    l2.new(uvn.outputs["UV"], t.inputs["Vector"])
# tint = colour map x tint colour (what SurfaceAppearance.Color does in Roblox)
tint = n2.new("ShaderNodeMix")
tint.data_type = "RGBA"
tint.blend_type = "MULTIPLY"
tint.inputs["Factor"].default_value = 1.0
tint.inputs[7].default_value = (1, 1, 1, 1)
tint.name = "Tint"
l2.new(tcol.outputs["Color"], tint.inputs[6])
nm = n2.new("ShaderNodeNormalMap")
l2.new(tnrm.outputs["Color"], nm.inputs["Color"])
b2 = n2.new("ShaderNodeBsdfPrincipled")
l2.new(tint.outputs[2], b2.inputs["Base Color"])
l2.new(trgh.outputs["Color"], b2.inputs["Roughness"])
l2.new(nm.outputs["Normal"], b2.inputs["Normal"])
b2.inputs["Metallic"].default_value = 0.0
o2 = n2.new("ShaderNodeOutputMaterial")
l2.new(b2.outputs["BSDF"], o2.inputs["Surface"])
ball.data.materials.clear()
ball.data.materials.append(fin)
bpy.data.materials.remove(src)

# ------------------------------------------------------------------ export FBX
tris = len(ball.data.polygons)
for o in sc.objects:
    o.select_set(o is ball)
bpy.context.view_layer.objects.active = ball
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "Gumball.fbx"), use_selection=True, object_types={"MESH"},
    mesh_smooth_type="OFF", use_triangles=True, axis_forward="-Z", axis_up="Y",
    apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
)
print("GUMBALL triangles:", tris)

# ------------------------------------------------------------------ preview scene
def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


def tinted(name, hexcol):
    m = fin.copy()
    m.name = "Gumball_" + name
    m.node_tree.nodes["Tint"].inputs[7].default_value = srgb(hexcol)
    return m


def add_light(name, kind, loc, energy, size, color=(1, 1, 1), target=(0, 0, 0)):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    d = Vector(target) - Vector(loc)
    lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(lo)
    return lo


# world: soft studio gradient so the shell has something to reflect
world = bpy.data.worlds.new("Studio")
sc.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
wtc = wn.new("ShaderNodeTexCoord")
wsep = wn.new("ShaderNodeSeparateXYZ")
wl.new(wtc.outputs["Generated"], wsep.inputs["Vector"])
ramp = wn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.06, 1)
ramp.color_ramp.elements[1].position = 0.75
ramp.color_ramp.elements[1].color = (0.75, 0.78, 0.85, 1)
wl.new(wsep.outputs["Z"], ramp.inputs["Fac"])
bg = wn.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.6
wl.new(ramp.outputs["Color"], bg.inputs["Color"])
wo = wn.new("ShaderNodeOutputWorld")
wl.new(bg.outputs["Background"], wo.inputs["Surface"])

# floor: soft warm-grey sweep with a little sheen
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -RADIUS))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.55, 0.53, 0.52, 1)
fb.inputs["Roughness"].default_value = 0.35
floor.data.materials.append(fm)

add_light("Key", "AREA", (-1.6, -1.8, 2.2), 140, (0.8, 0.6))
add_light("Fill", "AREA", (2.4, -1.2, 0.9), 35, (2.0, 2.0), (0.92, 0.96, 1.0))
add_light("Rim", "AREA", (0.6, 2.4, 1.6), 90, (2.0, 0.6))
add_light("Top", "AREA", (0, 0, 3.0), 25, (3.0, 3.0))

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam

sc.cycles.samples = 48 if QUICK else 256
sc.cycles.use_denoising = True
sc.render.resolution_x = 1200
sc.render.resolution_y = 900
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"


def aim(loc, target, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# single red gumball
ball.data.materials.clear()
ball.data.materials.append(tinted("Red", "#e0161b"))
aim((0.0, -4.2, 1.1), (0, 0, -0.05), 85)
render(os.path.join(PREVIEWS, "gumball_single.png"))

# colour cluster: 8 gumballs sharing the one mesh
colours = [("Red", "#e0161b"), ("Blue", "#1a5fe0"), ("Yellow", "#ffdc1a"),
           ("Green", "#2fbf3a"), ("Pink", "#ff6fb5"), ("Orange", "#ff7a12"),
           ("Purple", "#8a3ad6"), ("White", "#f4f1ea")]
spots = [(-1.65, 0.0), (-0.55, 0.05), (0.55, -0.02), (1.65, 0.04),
         (-1.1, 1.0), (0.0, 1.02), (1.1, 0.98), (-2.2, 1.05)]
balls = []
for (nm_, hx), (x, y) in zip(colours, spots):
    o = bpy.data.objects.new("Gumball_" + nm_, ball.data.copy())
    o.data.materials.clear()
    o.data.materials.append(tinted(nm_ + "2", hx))
    o.location = (x, y, 0)
    o.rotation_euler = (x * 1.7, y * 2.3, x + y)
    sc.collection.objects.link(o)
    balls.append(o)
ball.hide_render = True
aim((0.0, -8.0, 3.2), (0.0, 0.5, -0.05), 55)
sc.render.resolution_x = 1600
render(os.path.join(PREVIEWS, "gumball_colours.png"))

# keep only the gumball in the saved .blend (preview copies removed)
for o in balls:
    bpy.data.objects.remove(o)
ball.hide_render = False
ball.data.materials.clear()
ball.data.materials.append(fin)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Gumball.blend"))
print("GUMBALL done")
