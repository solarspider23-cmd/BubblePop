# BubblePop game thumbnails (Roblox, 1920 x 1080). Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_thumbnails.py
#   (add "-- A" or "-- B" to render only one, "-- fast" for a quick half-size test)
#
# A  "Big POP"         huge close-up of glossy light-blue bubble wrap, the middle
#                      bubble bursting in a comic star, plastic bits + gold coins
#                      flying out, one glowing rainbow bubble, chunky "POP!".
# B  "Plastic Muncher" the recycler (art/recycler/Recycler_Muncher.blend, appended)
#                      chomping a stream of colourful scraps into its funnel, gold
#                      coins bursting from its chute, bubble-wrap floor, sunburst
#                      sky, chunky "POP & SELL!".
#
# Style: big shapes, few elements, bright toon colours (flat-banded "toon"
# materials made with Shader to RGB), yellow text with a thick navy
# (20, 40, 110) outline. Text and the comic burst are parented to the camera
# so they are laid out in screen space. Output: art/thumbnails/thumb_A_pop.png,
# art/thumbnails/thumb_B_muncher.png (Eevee, Standard view, compositor bloom).
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "art", "thumbnails")
os.makedirs(OUT, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
NAVY = (20, 40, 110)
RES = (1920, 1080)


# ---------------------------------------------------------------- colour + materials
def lin1(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(c):
    return tuple(lin1(x) for x in c)


def rgba(c):
    return lin(c) + (1.0,)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt.nodes.new, nt.links.new


def flat_mat(name, rgb, strength=1.0):
    """Unlit flat colour (text, comic shapes)."""
    m, N, L = new_mat(name)
    e = N("ShaderNodeEmission")
    e.inputs["Color"].default_value = rgba(rgb)
    e.inputs["Strength"].default_value = strength
    L(e.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def grad_mat(name, top, bottom, axis="Y", lo=0.0, hi=1.0):
    """Unlit vertical gradient in the object's own space (text fill)."""
    m, N, L = new_mat(name)
    tc = N("ShaderNodeTexCoord")
    sx = N("ShaderNodeSeparateXYZ")
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = lo
    mr.inputs["From Max"].default_value = hi
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = rgba(bottom)
    cr.color_ramp.elements[1].color = rgba(top)
    e = N("ShaderNodeEmission")
    L(tc.outputs["Object"], sx.inputs[0])
    L(sx.outputs[axis], mr.inputs["Value"])
    L(mr.outputs[0], cr.inputs[0])
    L(cr.outputs[0], e.inputs["Color"])
    L(e.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def toon_mat(name, light, mid, dark, spec=0.0, spec_rough=0.12, spec_cut=0.55, rim=None, emit=1.0, glow=0.0):
    """Cartoon banded shading: diffuse light -> 3 hard colour bands, optional
    hard-edged white gloss highlight and a facing-ratio rim colour."""
    m, N, L = new_mat(name)
    d = N("ShaderNodeBsdfDiffuse")
    s2r = N("ShaderNodeShaderToRGB")
    bw = N("ShaderNodeRGBToBW")
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, rgba(dark)
    els[1].position, els[1].color = 0.12, rgba(mid)
    e3 = els.new(0.45)
    e3.color = rgba(light)
    L(d.outputs[0], s2r.inputs[0])
    L(s2r.outputs["Color"], bw.inputs[0])
    L(bw.outputs[0], cr.inputs[0])
    col = cr.outputs["Color"]
    if rim is not None:
        lw = N("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.35
        st = N("ShaderNodeMath")
        st.operation = "GREATER_THAN"
        st.inputs[1].default_value = 0.62
        mx = N("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs["B"].default_value = rgba(rim)
        L(lw.outputs["Facing"], st.inputs[0])
        L(st.outputs[0], mx.inputs["Factor"])
        L(col, mx.inputs["A"])
        col = mx.outputs["Result"]
    if spec > 0:
        g = N("ShaderNodeBsdfGlossy")
        g.inputs["Roughness"].default_value = spec_rough
        s2 = N("ShaderNodeShaderToRGB")
        b2 = N("ShaderNodeRGBToBW")
        st2 = N("ShaderNodeMapRange")
        st2.inputs["From Min"].default_value = spec_cut
        st2.inputs["From Max"].default_value = spec_cut + 0.04
        mul = N("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = spec
        mx2 = N("ShaderNodeMix")
        mx2.data_type = "RGBA"
        mx2.inputs["B"].default_value = (1, 1, 1, 1)
        L(g.outputs[0], s2.inputs[0])
        L(s2.outputs["Color"], b2.inputs[0])
        L(b2.outputs[0], st2.inputs["Value"])
        L(st2.outputs[0], mul.inputs[0])
        L(mul.outputs[0], mx2.inputs["Factor"])
        L(col, mx2.inputs["A"])
        col = mx2.outputs["Result"]
    e = N("ShaderNodeEmission")
    e.inputs["Strength"].default_value = emit + glow
    L(col, e.inputs["Color"])
    L(e.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def rainbow_mat(name, glow=1.6):
    """Glowing rainbow bands around the bubble + white gloss (blooms in comp)."""
    m, N, L = new_mat(name)
    tc = N("ShaderNodeTexCoord")
    sx = N("ShaderNodeSeparateXYZ")
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.55
    mr.inputs["From Max"].default_value = 0.55
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    cols = [(255, 60, 90), (255, 150, 30), (255, 230, 40), (90, 225, 70), (40, 170, 255), (160, 90, 255)]
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, rgba(cols[0])
    els[1].position, els[1].color = 1.0 / 6 * 5, rgba(cols[5])
    for i in range(1, 5):
        el = els.new(i / 6.0)
        el.color = rgba(cols[i])
    # tilt the bands: use x*0.7 + y*0.3 + z*0.5
    vm = N("ShaderNodeVectorMath")
    vm.operation = "DOT_PRODUCT"
    vm.inputs[1].default_value = (0.75, 0.35, 0.55)
    L(tc.outputs["Object"], vm.inputs[0])
    L(vm.outputs["Value"], mr.inputs["Value"])
    L(mr.outputs[0], cr.inputs[0])
    # gloss
    g = N("ShaderNodeBsdfGlossy")
    g.inputs["Roughness"].default_value = 0.12
    s2 = N("ShaderNodeShaderToRGB")
    b2 = N("ShaderNodeRGBToBW")
    st2 = N("ShaderNodeMapRange")
    st2.inputs["From Min"].default_value = 0.5
    st2.inputs["From Max"].default_value = 0.54
    mx2 = N("ShaderNodeMix")
    mx2.data_type = "RGBA"
    mx2.inputs["B"].default_value = (1, 1, 1, 1)
    L(g.outputs[0], s2.inputs[0])
    L(s2.outputs["Color"], b2.inputs[0])
    L(b2.outputs[0], st2.inputs["Value"])
    L(st2.outputs[0], mx2.inputs["Factor"])
    L(cr.outputs["Color"], mx2.inputs["A"])
    e = N("ShaderNodeEmission")
    e.inputs["Strength"].default_value = glow
    L(mx2.outputs["Result"], e.inputs["Color"])
    L(e.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def sunburst_mat(name, c1, c2, centre_glow, rays=18):
    """Screen-filling sunburst for a backdrop plane (object space, centred at origin)."""
    m, N, L = new_mat(name)
    tc = N("ShaderNodeTexCoord")
    sx = N("ShaderNodeSeparateXYZ")
    at = N("ShaderNodeMath")
    at.operation = "ARCTAN2"
    mul = N("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = rays / (2 * math.pi)
    fr = N("ShaderNodeMath")
    fr.operation = "FRACT"
    gt = N("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    mx = N("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.inputs["A"].default_value = rgba(c1)
    mx.inputs["B"].default_value = rgba(c2)
    L(tc.outputs["Object"], sx.inputs[0])
    L(sx.outputs["Y"], at.inputs[0])
    L(sx.outputs["X"], at.inputs[1])
    L(at.outputs[0], mul.inputs[0])
    L(mul.outputs[0], fr.inputs[0])
    L(fr.outputs[0], gt.inputs[0])
    L(gt.outputs[0], mx.inputs["Factor"])
    # soft white glow in the middle
    vl = N("ShaderNodeVectorMath")
    vl.operation = "LENGTH"
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 30.0
    mx2 = N("ShaderNodeMix")
    mx2.data_type = "RGBA"
    mx2.inputs["A"].default_value = rgba(centre_glow)
    L(tc.outputs["Object"], vl.inputs[0])
    L(vl.outputs["Value"], mr.inputs["Value"])
    pw = N("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 0.45
    L(mr.outputs[0], pw.inputs[0])
    L(pw.outputs[0], mx2.inputs["Factor"])
    L(mx.outputs["Result"], mx2.inputs["B"])
    e = N("ShaderNodeEmission")
    L(mx2.outputs["Result"], e.inputs["Color"])
    L(e.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


# ---------------------------------------------------------------- meshes
def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def mesh_obj(name, bm, mat=None, smooth=True):
    for f in bm.faces:
        f.smooth = smooth
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    if mat:
        ob.data.materials.append(mat)
    return ob


def lathe_bm(profile, segs=48):
    """profile: list of (r, z) from the top (r=0) down. Closed top fan."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z))
                          for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[j], a[i], b[0]))
            else:
                bm.faces.new((a[i], b[i], b[j], a[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def dome_profile(R=0.54, H=0.43, p=3.0, n=22, lip=0.6):
    """Chunky superellipse dome (flat-ish top, steep sides) + a small flared lip."""
    pts = [(0.0, H)]
    for k in range(1, n + 1):
        t = (math.pi / 2) * k / n
        s, c = math.sin(t), math.cos(t)
        pts.append((R * s ** (2 / p), H * c ** (2 / p)))
    pts.append((lip, 0.0))
    return pts


def bubble_mesh(name="BubbleDome"):
    bm = lathe_bm(dome_profile())
    me = bpy.data.meshes.new(name)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


def popped_mesh(name="BubblePopped"):
    """Deflated, crinkled pancake with a dark 3-way tear (two materials: 0 film, 1 hole)."""
    rnd = random.Random(3)
    bm = bmesh.new()
    segs, rings = 36, 6
    vs = []
    for k in range(rings + 1):
        rr = 0.56 * k / rings
        row = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            z = 0.12 * (1 - (k / rings) ** 2) + (0.025 * math.sin(5 * a + k) if 0 < k < rings else 0)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), max(0.0, z) + rnd.uniform(-0.01, 0.01) * (k < rings))))
        vs.append(row)
    centre = bm.verts.new((0, 0, 0.12))
    for i in range(segs):
        bm.faces.new((centre, vs[1][i], vs[1][(i + 1) % segs]))
    for k in range(1, rings):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((vs[k][i], vs[k + 1][i], vs[k + 1][j], vs[k][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


def star_outline(n, r_out, r_in, jitter=0.0, seed=1, rot=0.0):
    rnd = random.Random(seed)
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        r *= 1 + rnd.uniform(-jitter, jitter)
        a = rot + math.pi * i / n + rnd.uniform(-jitter, jitter) * 0.3
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def flat_poly(name, pts, mat, z=0.0, depth=0.0):
    """A flat (or thin extruded) polygon in the local XY plane facing +Z."""
    bm = bmesh.new()
    top = [bm.verts.new((x, y, z)) for x, y in pts]
    f = bm.faces.new(top)
    if depth > 0:
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        for v in r["geom"]:
            if isinstance(v, bmesh.types.BMVert):
                v.co.z -= depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return mesh_obj(name, bm, mat, smooth=False)


def coin_mesh(name="Coin", r=0.34, t=0.09):
    """Chunky cartoon coin: rounded rim, slightly dished face (axis = local Z)."""
    prof = [(0.0, t * 0.35), (r * 0.72, t * 0.35), (r * 0.8, t * 0.55), (r * 0.95, t * 0.5), (r, 0.0),
            (r * 0.95, -t * 0.5), (r * 0.8, -t * 0.55), (r * 0.72, -t * 0.35), (0.0, -t * 0.35)]
    bm = lathe_bm(prof, 40)
    me = bpy.data.meshes.new(name)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


def scrap_mesh(seed, name="Scrap"):
    """Irregular chunky plastic shard (5-7 sided slab with bevel look)."""
    rnd = random.Random(seed)
    n = rnd.randint(5, 7)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.25, 0.25)
        r = rnd.uniform(0.6, 1.0)
        pts.append((r * math.cos(a), r * math.sin(a) * rnd.uniform(0.6, 0.9)))
    bm = bmesh.new()
    top = [bm.verts.new((x, y, 0.09)) for x, y in pts]
    f = bm.faces.new(top)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in r["geom"]:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z -= 0.18
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.05, segments=2, affect="EDGES")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def obj(name, me, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, parent=None):
    o = link(bpy.data.objects.new(name, me))
    if mat is not None:
        if len(o.data.materials) == 0:
            o.data.materials.append(mat)
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = mat
    o.location = loc
    o.rotation_euler = rot
    o.scale = (scale, scale, scale) if not isinstance(scale, tuple) else scale
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- text
def text_obj(name, body, size, mat, extrude=0.0, offset=0.0, bevel=0.0, parent=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.offset = offset
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.space_character = 0.92
    cu.resolution_u = 24
    o = link(bpy.data.objects.new(name, cu))
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def chunky_text(prefix, body, size, parent, at, tilt_deg, fill_top=(255, 244, 90), fill_bot=(255, 186, 10),
                outline=0.07, depth=0.22, shadow=(0.03, -0.05)):
    """Yellow fill + very thick navy outline + a navy 3D drop block, all in a
    camera-space empty at `at` (local XY = screen plane, +Z toward the camera)."""
    root = link(bpy.data.objects.new(prefix + "_Root", None))
    root.parent = parent
    root.location = at
    root.rotation_euler = (0, 0, math.radians(tilt_deg))
    fill = grad_mat(prefix + "_Fill", fill_top, fill_bot, "Y", -size * 0.42, size * 0.42)
    navy = flat_mat(prefix + "_Navy", NAVY)
    white = flat_mat(prefix + "_Shine", (255, 255, 255))
    f = text_obj(prefix + "_Text", body, size, fill, parent=root)
    f.location = (0, 0, 0.02)
    hi = text_obj(prefix + "_Shine", body, size, white, offset=-size * 0.035, parent=root)  # inner shine rim
    hi.location = (-size * 0.012, size * 0.016, 0.01)
    o = text_obj(prefix + "_Outline", body, size, navy, offset=size * outline, parent=root)
    o.location = (0, 0, -0.01)
    sh = text_obj(prefix + "_Shadow", body, size, navy, offset=size * outline, extrude=depth * 0.5, parent=root)
    sh.location = (shadow[0] * size, shadow[1] * size, -0.05 - depth)
    # put the fill on top of the shine: the shine text peeks out at the top-left edge only
    return root


# ---------------------------------------------------------------- scene setup
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16 if FAST else 64
    try:
        sc.eevee.use_raytracing = False
    except AttributeError:
        pass
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 50 if FAST else 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    return sc


def world(sc, rgb, strength=1.0):
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = rgba(rgb)
    bg.inputs["Strength"].default_value = strength


def sun(name, d, energy, angle=6.0):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = energy
    ld.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, ld))
    o.rotation_euler = (-Vector(d).normalized()).to_track_quat("-Z", "Y").to_euler()
    return o


def camera(sc, loc, target, lens=35, dof=None, roll=0.0):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_width = 36
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 500
    co = link(bpy.data.objects.new("Cam", cd))
    co.location = Vector(loc)
    q = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y")
    co.rotation_euler = (q @ Euler((0, 0, math.radians(roll))).to_quaternion()).to_euler()
    if dof:
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
        cd.dof.aperture_fstop = dof
    sc.camera = co
    return co


def screen(cam, u, v, d):
    """Camera-local point at depth d for screen coords u, v in [-0.5, 0.5] (v up)."""
    cd = cam.data
    w = d * cd.sensor_width / cd.lens
    h = w * RES[1] / RES[0]
    return Vector((u * w, v * h, -d))


def screen_scale(cam, d):
    """World units per full screen width at depth d."""
    return d * cam.data.sensor_width / cam.data.lens


def project(sc, cam, p):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    c = world_to_camera_view(sc, cam, Vector(p))
    return c.x - 0.5, c.y - 0.5, c.z


def compositor(sc, bloom=0.7, threshold=1.0, vignette=0.25):
    ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    sc.compositing_node_group = ng
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes.new, ng.links.new
    rl = N("CompositorNodeRLayers")
    gl = N("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Quality"].default_value = "High"
    gl.inputs["Threshold"].default_value = threshold
    gl.inputs["Strength"].default_value = bloom
    gl.inputs["Size"].default_value = 0.6
    L(rl.outputs["Image"], gl.inputs["Image"])
    img = gl.outputs["Image"]
    if vignette > 0:
        zero = N("ShaderNodeMath")
        zero.operation = "MULTIPLY"
        zero.inputs[1].default_value = 0.0
        L(rl.outputs["Image"], zero.inputs[0])
        em = N("CompositorNodeEllipseMask")
        em.inputs["Size"].default_value = (1.3, 1.45)
        L(zero.outputs[0], em.inputs["Mask"])
        bl = N("CompositorNodeBlur")
        bl.inputs["Size"].default_value = (int(RES[0] * 0.2), int(RES[0] * 0.2))
        L(em.outputs["Mask"], bl.inputs["Image"])
        mr = N("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 1.0 - vignette
        L(bl.outputs["Image"], mr.inputs["Value"])
        mx = N("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        L(img, mx.inputs["A"])
        L(mr.outputs["Result"], mx.inputs["B"])
        img = mx.outputs["Result"]
    out = N("NodeGroupOutput")
    L(img, out.inputs[0])
    return ng


def render(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


# ---------------------------------------------------------------- shared props
def make_mats():
    M = {}
    M["bubble"] = toon_mat("Bubble", (165, 228, 255), (85, 185, 250), (35, 125, 225), spec=1.0, spec_cut=0.5,
                           rim=(200, 240, 255))
    M["popped"] = toon_mat("Popped", (200, 236, 255), (140, 205, 250), (90, 165, 235), spec=0.0)
    M["hole"] = flat_mat("Hole", (30, 70, 150))
    M["sheet"] = toon_mat("Sheet", (60, 140, 230), (45, 115, 215), (30, 90, 195))
    M["coin"] = toon_mat("Coin", (255, 215, 30), (255, 165, 0), (205, 95, 0), spec=1.0, spec_rough=0.2,
                         spec_cut=0.55, rim=(170, 80, 0))
    bits = {"Pink": (255, 80, 170), "Lime": (140, 230, 50), "Orange": (255, 140, 30), "Purple": (165, 100, 255),
            "Cyan": (40, 210, 255), "Yellow": (255, 220, 40)}
    M["bits"] = []
    for k, c in bits.items():
        lt = tuple(min(255, int(x + (255 - x) * 0.45)) for x in c)
        dk = tuple(int(x * 0.72) for x in c)
        M["bits"].append(toon_mat("Bit" + k, lt, c, dk, spec=0.8, spec_cut=0.5))
    M["rainbow"] = rainbow_mat("Rainbow", glow=2.0)
    M["sparkle"] = flat_mat("Sparkle", (255, 255, 255), 2.5)
    return M


def bubble_field(M, nx, ny, skip=None, popped=(), spacing=1.2, sheet=True, rnd_seed=5):
    """A sheet of bubbles centred on the origin (z=0 film top)."""
    dome = bubble_mesh()
    pop = popped_mesh()
    pop.materials.append(M["popped"])
    rnd = random.Random(rnd_seed)
    objs = {}
    for i in range(-nx, nx + 1):
        for j in range(-ny, ny + 1):
            x, y = i * spacing, j * spacing
            if skip and skip(x, y):
                continue
            if (i, j) in popped:
                o = obj(f"P_{i}_{j}", pop, M["popped"], (x, y, 0), (0, 0, rnd.uniform(0, 6.28)))
            else:
                o = obj(f"B_{i}_{j}", dome, M["bubble"], (x, y, 0), (0, 0, rnd.uniform(0, 6.28)),
                        (1 + rnd.uniform(-0.02, 0.02),) * 2 + (1 + rnd.uniform(-0.04, 0.04),))
            objs[(i, j)] = o
    if sheet:
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=max(nx, ny) * spacing * 1.2)
        s = mesh_obj("Sheet", bm, M["sheet"], smooth=False)
        s.location.z = -0.005
    return objs


def sparkle(M, name, loc, size, parent=None, rot=0.0):
    """4-point cartoon sparkle (flat, faces local +Z)."""
    pts = star_outline(4, 1.0, 0.22, rot=rot + math.pi / 4 * 0)
    o = flat_poly(name, pts, M["sparkle"])
    o.location = loc
    o.scale = (size, size, size)
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- A: Big POP
def thumb_a():
    sc = reset()
    world(sc, (170, 215, 250), 0.35)
    M = make_mats()
    sun("Key", (-0.45, -0.55, 0.75), 3.2, angle=4)
    sun("Fill", (0.6, 0.3, 0.5), 0.6, angle=10)
    # bubble wrap: popped centre bubble at (0, 0)
    bubble_field(M, 11, 9, popped={(0, 0), (-1, 0)}, spacing=1.2)
    # glowing rainbow bubble replaces the one at (2, -1)
    rb = bpy.data.objects.get("B_2_-1")
    rb.material_slots[0].material = M["rainbow"]
    rb.scale = (1.08, 1.08, 1.15)
    cam = camera(sc, (1.2, -5.4, 5.4), (0.75, 0.05, 0.1), lens=30, dof=None, roll=0)
    # comic burst around the popped bubble (camera space, a little in front of it)
    bx, by, bd = project(sc, cam, (0.0, 0.0, 0.35))
    d = bd * 0.7
    root = link(bpy.data.objects.new("Burst", None))
    root.parent = cam
    root.location = screen(cam, bx, by, d)
    k = screen_scale(cam, d) / 1920.0   # world units per pixel at the burst depth
    navy = flat_mat("BurstNavy", NAVY)
    layers = [(NAVY, 330, 205, 0.0), ((255, 120, 20), 300, 182, 0.01), ((255, 220, 30), 245, 150, 0.02),
              ((255, 255, 235), 135, 88, 0.03)]
    for n, (c, ro, ri, z) in enumerate(layers):
        m = navy if c == NAVY else flat_mat(f"Burst{n}", c, 1.0 if n < 3 else 1.4)
        o = flat_poly(f"Burst_{n}", star_outline(12, ro * k, ri * k, jitter=0.12, seed=4, rot=0.2), m, z=z)
        o.parent = root
    # flying scraps + coins (world space, around the burst, toward the camera)
    rnd = random.Random(11)
    cmesh = coin_mesh()
    flyers = [  # (screen u, v, depth factor, kind, size px)
        (0.06, 0.31, 0.55, "coin", 140), (0.23, 0.17, 0.5, "coin", 160), (0.37, -0.02, 0.45, "coin", 150),
        (-0.2, -0.2, 0.5, "coin", 135), (0.13, 0.34, 0.62, "bit", 100), (-0.24, 0.0, 0.6, "bit", 95),
        (0.36, 0.3, 0.55, "bit", 100), (-0.08, -0.3, 0.55, "bit", 100), (0.12, -0.27, 0.5, "bit", 90),
    ]
    for n, (u, v, df, kind, px) in enumerate(flyers):
        dd = bd * df
        kk = screen_scale(cam, dd) / 1920.0
        p = screen(cam, bx + u, by + v, dd)
        if kind == "coin":
            o = obj(f"Coin_{n}", cmesh, M["coin"], p, (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 3)),
                    px * kk / 0.68)
        else:
            sm = scrap_mesh(n)
            o = obj(f"Bit_{n}", sm, M["bits"][n % len(M["bits"])], p,
                    (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6)), px * kk / 1.1)
        o.parent = cam
    # sparkles on the rainbow bubble
    rx, ry, rd = project(sc, cam, rb.location + Vector((0, 0, 0.3)))
    for n, (du, dv, s) in enumerate(((0.06, 0.09, 40), (-0.07, 0.07, 28), (0.075, -0.03, 22))):
        dd = rd * 0.8
        kk = screen_scale(cam, dd) / 1920.0
        sparkle(M, f"Spark_{n}", screen(cam, rx + du, ry + dv, dd), s * kk, parent=cam)
    # title
    td = 6.0
    chunky_text("Pop", "POP!", screen_scale(cam, td) * 0.235, cam, screen(cam, -0.255, 0.285, td), 9)
    compositor(sc, bloom=1.0, threshold=1.0, vignette=0.22)
    render(sc, os.path.join(OUT, "thumb_A_pop.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "thumb_A_pop.blend"))


if __name__ == "__main__":   # build_thumbnails_v2.py imports the helpers
    thumb_a()
