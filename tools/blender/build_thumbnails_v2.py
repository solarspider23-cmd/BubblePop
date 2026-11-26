# BubblePop game thumbnails, v2 "glossy close-up" style (owner's style reference:
# art/references/thumb_style_ref.webp - used for style only). Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_thumbnails_v2.py
#   (add "-- 1" or "-- 2" for one thumbnail only, "-- fast" for a quick low-sample half-size test)
#
# 1  thumb_1_poke.png  an angled sheet of glossy light-blue bubble wrap in a chunky
#                      yellow frame, rows running diagonally; a cartoon hand holds a
#                      chunky yellow/black poker pressing into one bubble that bursts
#                      in a warm golden sparkle with plastic scraps flying; a few
#                      popped bubbles nearby; soft blurred colourful background
#                      (the Muncher recycler, bins of scraps, coin piles).
# 2  thumb_2_rare.png  same set-up, the poked bubble is a glowing RAINBOW bubble with
#                      an extra-strong sparkle and gold coins popping out.
#
# No text. Cycles (GPU if available), depth of field, compositor bloom.
# Reflections/lighting use Blender's bundled CC0 studio HDRI (Poly Haven, Greg
# Zaal; datafiles/studiolights/world). Helpers come from build_thumbnails.py.
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_thumbnails as T  # noqa: E402

ROOT = T.ROOT
OUT = T.OUT
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
ONLY = [a for a in ARGS if a in ("1", "2")] or ["1", "2"]
RES = (1920, 1080)
rgba = T.rgba
link = T.link

SPACING = 1.2
COLS = range(-9, 3)     # bubble columns (local X); the frame's right edge sits just past the focal bubble
ROWS = range(-7, 7)
FOCAL = (0, 0)
PANEL_TURN = math.radians(34)


# ---------------------------------------------------------------- materials
def mat(name, base, rough=0.3, metal=0.0, coat=0.0, transm=0.0, ior=1.45, emit=None, emit_k=0.0, sss=0.0,
        film=0.0):
    m, N, L = T.new_mat(name)
    p = N("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = rgba(base)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Coat Roughness"].default_value = 0.03
    p.inputs["Transmission Weight"].default_value = transm
    p.inputs["IOR"].default_value = ior
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.3)
        p.inputs["Subsurface Scale"].default_value = 0.08
    if film:
        p.inputs["Thin Film Thickness"].default_value = film
        p.inputs["Thin Film IOR"].default_value = 1.5
    if emit is not None:
        p.inputs["Emission Color"].default_value = rgba(emit)
        p.inputs["Emission Strength"].default_value = emit_k
    L(p.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def rainbow(name, k=2.2):
    """Glossy bubble with glowing rainbow bands (object-space, tilted)."""
    m, N, L = T.new_mat(name)
    tc = N("ShaderNodeTexCoord")
    dp = N("ShaderNodeVectorMath")
    dp.operation = "DOT_PRODUCT"
    dp.inputs[1].default_value = (0.8, 0.35, 0.9)
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.5
    mr.inputs["From Max"].default_value = 0.75
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    cols = [(255, 50, 90), (255, 140, 20), (255, 225, 30), (60, 220, 80), (30, 160, 255), (150, 80, 255)]
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, rgba(cols[0])
    els[1].position, els[1].color = 5.0 / 6, rgba(cols[5])
    for i in range(1, 5):
        e = els.new(i / 6.0)
        e.color = rgba(cols[i])
    p = N("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.08
    p.inputs["Coat Weight"].default_value = 1.0
    p.inputs["Coat Roughness"].default_value = 0.02
    p.inputs["Emission Strength"].default_value = k
    L(tc.outputs["Object"], dp.inputs[0])
    L(dp.outputs["Value"], mr.inputs["Value"])
    L(mr.outputs[0], cr.inputs[0])
    L(cr.outputs[0], p.inputs["Base Color"])
    L(cr.outputs[0], p.inputs["Emission Color"])
    L(p.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    return m


def glow(name, rgb, k):
    return T.flat_mat(name, rgb, k)


def make_mats():
    M = {}
    M["bubble"] = mat("Bubble", (140, 215, 255), rough=0.04, coat=1.0, transm=0.45, ior=1.35, film=380)
    M["popped"] = mat("Popped", (110, 190, 250), rough=0.2, coat=0.6, transm=0.5, film=300)
    M["film"] = mat("Film", (60, 160, 250), rough=0.25, coat=0.6)
    M["board"] = mat("Board", (245, 250, 255), rough=0.5)
    M["frame"] = mat("Frame", (255, 196, 20), rough=0.25, coat=0.8)
    M["corner"] = mat("Corner", (235, 40, 45), rough=0.25, coat=0.8)
    M["handle"] = mat("Handle", (255, 200, 15), rough=0.22, coat=1.0)
    M["grip"] = mat("Grip", (22, 22, 26), rough=0.45)
    M["steel"] = mat("Steel", (225, 230, 238), rough=0.12, metal=1.0)
    M["skin"] = mat("Skin", (250, 165, 110), rough=0.45, sss=0.1)
    M["sleeve"] = mat("Sleeve", (60, 120, 235), rough=0.6)
    M["coin"] = mat("Coin", (255, 186, 30), rough=0.18, metal=1.0)
    M["floor"] = mat("Floor", (250, 140, 190), rough=0.6)
    M["wall"] = mat("Wall", (120, 200, 255), rough=0.8)
    bits = [(255, 70, 160), (130, 225, 40), (255, 140, 20), (160, 95, 255), (40, 200, 255), (255, 215, 30)]
    M["bits"] = [mat(f"Bit{n}", c, rough=0.2, coat=1.0) for n, c in enumerate(bits)]
    M["clearbit"] = mat("ClearBit", (170, 225, 255), rough=0.1, coat=1.0, transm=0.5, film=380)
    M["rainbow"] = rainbow("Rainbow", 0.9)
    M["spark"] = glow("Spark", (255, 232, 160), 4.0)
    M["spark2"] = glow("Spark2", (255, 170, 40), 2.0)
    return M


# ---------------------------------------------------------------- meshes
def hi_dome():
    bm = T.lathe_bm(T.dome_profile(R=0.53, H=0.46, p=2.6, n=28, lip=0.585), 64)
    me = bpy.data.meshes.new("Dome")
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


def rbox(name, size, loc, m, bevel=0.08, rot=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=4, affect="EDGES", profile=0.5)
    o = T.mesh_obj(name, bm, m, smooth=True)
    o.location = loc
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    return o


def lathe_obj(name, prof, m, segs=48, parent=None):
    bm = T.lathe_bm(prof, segs)
    o = T.mesh_obj(name, bm, m, smooth=True)
    if parent:
        o.parent = parent
    return o


def instance(name, me, m, loc, rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    o = link(bpy.data.objects.new(name, me))
    if len(me.materials) == 0:
        me.materials.append(m)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = m
    o.location = loc
    o.rotation_euler = rot
    o.scale = scale
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- panel
def build_panel(M, focal_mat=None, popped=()):
    """Bubble wrap sheet in a chunky yellow frame. Local XY plane, focal bubble at the origin."""
    root = link(bpy.data.objects.new("Panel", None))
    root.rotation_euler = (0, 0, PANEL_TURN)
    dome = hi_dome()
    pop = T.popped_mesh()
    rnd = random.Random(9)
    for i in COLS:
        for j in ROWS:
            x, y = i * SPACING, j * SPACING
            if (i, j) in popped:
                instance(f"P{i}_{j}", pop, M["popped"], (x, y, 0), (0, 0, rnd.uniform(0, 6.3)), (1, 1, 1.4), root)
                continue
            m = M["bubble"]
            sc = (1 + rnd.uniform(-0.015, 0.015),) * 2 + (1 + rnd.uniform(-0.03, 0.03),)
            if (i, j) == FOCAL:
                m = focal_mat or m
                sc = (1.07, 1.07, 0.8) if focal_mat is None else (1.4, 1.4, 1.3)   # pressed / rare and big
            instance(f"B{i}_{j}", dome, m, (x, y, 0), (0, 0, rnd.uniform(0, 6.3)), sc, root)
    x0, x1 = COLS[0] * SPACING - 0.75, COLS[-1] * SPACING + 0.75
    y0, y1 = ROWS[0] * SPACING - 0.75, ROWS[-1] * SPACING + 0.75
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    film = rbox("Film", (w, h, 0.04), (cx, cy, -0.02), M["film"], 0.01, parent=root)
    rbox("Board", (w + 0.4, h + 0.4, 0.3), (cx, cy, -0.2), M["board"], 0.05, parent=root)
    F, FH = 0.62, 0.5    # chunky frame bar width / height
    rbox("FrameR", (F, h + 2 * F, FH), (x1 + F / 2, cy, FH / 2 - 0.25), M["frame"], 0.16, parent=root)
    rbox("FrameL", (F, h + 2 * F, FH), (x0 - F / 2, cy, FH / 2 - 0.25), M["frame"], 0.16, parent=root)
    rbox("FrameT", (w + 2 * F, F, FH), (cx, y1 + F / 2, FH / 2 - 0.25), M["frame"], 0.16, parent=root)
    rbox("FrameB", (w + 2 * F, F, FH), (cx, y0 - F / 2, FH / 2 - 0.25), M["frame"], 0.16, parent=root)
    for sx, sy in ((x1, y1), (x1, y0), (x0, y1), (x0, y0)):
        rbox("Corner", (0.95, 0.95, 0.62), (sx + (0.31 if sx == x1 else -0.31), sy + (0.31 if sy == y1 else -0.31), 0.06),
             M["corner"], 0.18, parent=root)
    return root


# ---------------------------------------------------------------- tool + hand
def build_tool(M, tip, axis, side):
    """Chunky poker: steel pin from the tip, yellow handle with black grips, held by a
    cartoon hand. Local +Z runs from the tip up the tool; local +X = `side`
    (where the back of the hand faces)."""
    z = Vector(axis).normalized()
    x = (Vector(side) - z * Vector(side).dot(z)).normalized()
    y = z.cross(x)
    root = link(bpy.data.objects.new("Tool", None))
    root.matrix_world = Matrix.Translation(Vector(tip)) @ Matrix((x, y, z)).transposed().to_4x4()
    # steel pin: needle point, shaft, collar
    lathe_obj("Pin", [(0.0, 0.0), (0.03, 0.06), (0.075, 0.35), (0.085, 1.55), (0.0, 1.55)][::-1], M["steel"], 32, root)
    lathe_obj("Ferrule", [(0.0, 1.95), (0.2, 1.95), (0.23, 1.85), (0.23, 1.6), (0.15, 1.5), (0.0, 1.5)], M["steel"], 48, root)
    hp = [(0.0, 5.15), (0.22, 5.12), (0.36, 4.98), (0.4, 4.7), (0.4, 2.2), (0.33, 1.98), (0.22, 1.9), (0.0, 1.9)]
    lathe_obj("Handle", hp, M["handle"], 48, root)
    for z0, z1 in ((2.3, 2.85), (3.1, 3.65)):
        lathe_obj("Grip", [(0.0, z1), (0.415, z1), (0.43, z1 - 0.06), (0.43, z0 + 0.06), (0.415, z0), (0.0, z0)],
                  M["grip"], 48, root)
    # hand (metaballs: one smooth blobby cartoon hand)
    mb = bpy.data.metaballs.new("Hand")
    mb.resolution = 0.06
    mb.render_resolution = 0.015
    mb.threshold = 0.6
    ho = link(bpy.data.objects.new("Hand", mb))
    ho.parent = root
    mb.materials.append(M["skin"])

    def ball(c, r):
        e = mb.elements.new()
        e.type = "BALL"
        e.co = c
        e.radius = r / 0.575
        return e

    def caps(a, b, r):
        a, b = Vector(a), Vector(b)
        e = mb.elements.new()
        e.type = "CAPSULE"
        e.co = (a + b) / 2
        e.radius = r / 0.575
        e.size_x = (b - a).length / 2
        e.rotation = Vector((1, 0, 0)).rotation_difference(b - a)
        return e

    RH, RF = 0.41, 0.225        # handle radius, finger radius
    # palm on the far side (-X) of the handle, fingers curl over the top and
    # round to the camera side (+X) so the knuckles and fingertips show
    e = ball((-0.62, 0.0, 4.4), 0.5)
    e.type = "ELLIPSOID"
    e.size_x, e.size_y, e.size_z = 0.75, 1.05, 1.35
    for n, zf in enumerate((3.95, 4.33, 4.71, 5.06)):
        rf = RF * (1.0 if n < 3 else 0.85)
        R = RH + rf * 0.8
        pts = [Vector((R * math.cos(math.radians(a)), R * math.sin(math.radians(a)), zf)) for a in (170, 125, 80, 35, -5, -40)]
        pts[0] = Vector((-0.75, 0.25, zf + 0.05))
        for a, b in zip(pts, pts[1:]):
            caps(a, b, rf)
        ball(pts[-1], rf * 1.03)
    # thumb lies along the handle toward the tip on the -Y side
    caps((-0.5, -0.45, 4.3), (-0.05, -0.5, 3.85), 0.2)
    caps((-0.05, -0.5, 3.85), (0.25, -0.38, 3.55), 0.18)
    # wrist + forearm leaving the frame, then a sleeve
    caps((-0.75, 0.0, 4.9), (-1.3, 0.0, 6.0), 0.45)
    caps((-1.3, 0.0, 6.0), (-1.9, 0.0, 7.4), 0.5)
    sl = lathe_obj("Sleeve", [(0.0, 1.6), (0.64, 1.6), (0.7, 1.5), (0.7, 0.1), (0.62, 0.0), (0.0, 0.0)], M["sleeve"], 40,
                   root)
    a0, a1 = Vector((-1.55, 0.0, 6.55)), Vector((-1.9, 0.0, 7.4))
    sl.matrix_basis = Matrix.Translation(a0) @ Vector((0, 0, 1)).rotation_difference(a1 - a0).to_matrix().to_4x4()
    return root


# ---------------------------------------------------------------- effects
def spark_burst(M, at, cam, size, rays=8, strong=False, halo_k=1.8, core=0.14, ring=0.0, light=True):
    """Warm golden sparkle: bright core, long thin rays facing the camera, a warm light."""
    root = link(bpy.data.objects.new("Burst", None))
    root.location = at
    q = cam.matrix_world.to_quaternion()
    root.rotation_euler = q.to_euler()
    if core > 0:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size * core, location=(0, 0, 0))
        c = bpy.context.active_object
        c.name = "BurstCore"
        c.data.materials.append(M["spark"])
        c.parent = root
        c.location = (0, 0, 0)
    if ring > 0:   # separate spikes radiating from a ring round the bubble (keeps it visible)
        rnd = random.Random(8)
        for k in range(18):
            a = 2 * math.pi * k / 18 + rnd.uniform(-0.06, 0.06)
            r1 = size * (1.0 if k % 2 == 0 else 0.62) * rnd.uniform(0.85, 1.1)
            w = 0.07 if k % 2 == 0 else 0.05
            pts = [(ring * math.cos(a - w), ring * math.sin(a - w)), (r1 * math.cos(a), r1 * math.sin(a)),
                   (ring * math.cos(a + w), ring * math.sin(a + w))]
            o = T.flat_poly(f"Spike{k}", pts, M["spark"] if k % 2 == 0 else M["spark2"])
            o.parent = root
    for n in range(2 if ring == 0 else 0):
        pts = T.star_outline(rays, size * (1.0 if n == 0 else 0.6), size * 0.045, rot=(0.2 if n == 0 else 0.2 + math.pi / rays))
        o = T.flat_poly(f"Rays{n}", pts, M["spark"] if n == 0 else M["spark2"], z=0.01 * n)
        o.parent = root
        o.scale = (1, 1, 1)
    if strong and ring == 0:
        pts = T.star_outline(16, size * 0.75, size * 0.1, jitter=0.25, seed=5)
        o = T.flat_poly("Rays2", pts, M["spark2"], z=-0.01)
        o.parent = root
    hm, N, L = T.new_mat("Halo")
    tc = N("ShaderNodeTexCoord")
    vl = N("ShaderNodeVectorMath")
    vl.operation = "LENGTH"
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 1.0
    mr.inputs["From Max"].default_value = 0.0
    pw = N("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    em = N("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba((255, 185, 50))
    em.inputs["Strength"].default_value = halo_k
    tr = N("ShaderNodeBsdfTransparent")
    mx = N("ShaderNodeMixShader")
    L(tc.outputs["Object"], vl.inputs[0])
    L(vl.outputs["Value"], mr.inputs["Value"])
    L(mr.outputs[0], pw.inputs[0])
    fac = pw.outputs[0]
    if ring > 0:
        rn = ring / (size * 1.5)
        m2 = N("ShaderNodeMapRange")
        m2.inputs["From Min"].default_value = rn * 0.8
        m2.inputs["From Max"].default_value = rn * 1.05
        L(vl.outputs["Value"], m2.inputs["Value"])
        mu = N("ShaderNodeMath")
        mu.operation = "MULTIPLY"
        L(fac, mu.inputs[0])
        L(m2.outputs[0], mu.inputs[1])
        fac = mu.outputs[0]
    L(fac, mx.inputs[0])
    L(tr.outputs[0], mx.inputs[1])
    L(em.outputs[0], mx.inputs[2])
    L(mx.outputs[0], N("ShaderNodeOutputMaterial").inputs[0])
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    half = max(abs(v.co.x) for v in bm.verts)
    for v in bm.verts:
        v.co /= half          # exactly -1..1, so the gradient reaches 0 at the edge
    halo = T.mesh_obj("Halo", bm, hm, smooth=False)
    halo.parent = root
    halo.location = (0, 0, -1.5 if ring > 0 else -0.05)   # rare: glow sits behind the bubble
    halo.scale = (size * 1.5,) * 3
    if not light:
        return root
    ld = bpy.data.lights.new("BurstLight", "POINT")
    ld.energy = 60 if strong else 200
    ld.color = (1.0, 0.8, 0.45)
    ld.shadow_soft_size = 0.3
    lo = link(bpy.data.objects.new("BurstLight", ld))
    lo.location = Vector(at) + Vector((0, 0, 0.4))
    return root


def twinkle(M, at, cam, size, name="Twinkle"):
    o = T.flat_poly(name, T.star_outline(4, size, size * 0.14), M["spark"])
    o.location = at
    o.rotation_euler = cam.matrix_world.to_quaternion().to_euler()
    return o


# ---------------------------------------------------------------- background
def append_muncher(at, turn):
    path = os.path.join(ROOT, "art", "recycler", "Recycler_Muncher.blend")
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in ("Body", "Glass", "Glow") if n in src.objects]
    root = link(bpy.data.objects.new("Muncher", None))
    root.location = at
    root.rotation_euler = (0, 0, turn)
    for o in dst.objects:
        link(o)
        o.parent = root
    return root


def bin_of_scraps(M, name, at, col, size=(2.6, 1.8, 1.3), seed=1, fill="bits"):
    rnd = random.Random(seed)
    root = link(bpy.data.objects.new(name, None))
    root.location = at
    root.rotation_euler = (0, 0, rnd.uniform(-0.3, 0.3))
    m = mat(name + "Mat", col, rough=0.3, coat=0.6)
    w, d, h = size
    t = 0.14
    rbox(name + "Floor", (w, d, t), (0, 0, t / 2), m, 0.05, parent=root)
    rbox(name + "F", (w, t, h), (0, -d / 2, h / 2), m, 0.06, parent=root)
    rbox(name + "B", (w, t, h), (0, d / 2, h / 2), m, 0.06, parent=root)
    rbox(name + "L", (t, d, h), (-w / 2, 0, h / 2), m, 0.06, parent=root)
    rbox(name + "R", (t, d, h), (w / 2, 0, h / 2), m, 0.06, parent=root)
    cm = T.coin_mesh()
    for n in range(60):
        p = (rnd.uniform(-w / 2 + 0.25, w / 2 - 0.25), rnd.uniform(-d / 2 + 0.25, d / 2 - 0.25), h - 0.1 + rnd.uniform(-0.1, 0.25))
        if fill == "coins":
            instance(f"{name}C{n}", cm, M["coin"], p, (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), 0), (1.3,) * 3, root)
        else:
            instance(f"{name}S{n}", T.scrap_mesh(1000 + seed * 100 + n), M["bits"][n % 6], p,
                     (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), (0.28,) * 3, root)
    return root


def floor_point(cam, u, v, z=-0.36, far=40.0):
    """World point on the floor seen at image coords u, v (0..1, v up)."""
    sc = bpy.context.scene
    fr = cam.data.view_frame(scene=sc)          # tr, br, bl, tl in camera space
    tr, br, bl, tl = fr
    p = bl + (br - bl) * u + (tl - bl) * v
    o = cam.matrix_world.translation
    d = (cam.matrix_world.to_3x3() @ p).normalized()
    if d.z < -1e-4:
        t = (z - o.z) / d.z
        if t < far:
            return o + d * t
    return o + d * far


def build_background(M, cam):
    # floor the panel lies on + a far wall; colourful props in the corner of the frame past the panel
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80)
    fl = T.mesh_obj("Floor", bm, M["floor"], smooth=False)
    fl.location.z = -0.36
    face = lambda p: math.atan2(cam.location.y - p.y, cam.location.x - p.x) - math.pi / 2  # +Y front toward camera
    p = floor_point(cam, 0.80, 0.80)
    append_muncher(p, face(p))
    for name, uv, col, kw in (("BinRed", (0.96, 0.52), (235, 45, 55), {}),
                              ("BinGreen", (0.66, 0.97), (60, 200, 90), {}),
                              ("BinBlue", (0.97, 0.83), (40, 110, 240), {}),
                              ("BinCoins", (0.86, 0.38), (255, 140, 20), {"size": (2.0, 1.6, 1.0), "fill": "coins"})):
        p = floor_point(cam, *uv)
        b = bin_of_scraps(M, name, p, col, seed=len(name), **kw)
        b.rotation_euler.z = face(p) + random.Random(len(name)).uniform(-0.3, 0.3)
        print("PROP", name, tuple(round(c, 1) for c in p))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80)
    wall = T.mesh_obj("Wall", bm, M["wall"], smooth=False)
    far = floor_point(cam, 0.85, 0.9)
    d = Vector((far.x - cam.location.x, far.y - cam.location.y, 0)).normalized()
    wall.location = cam.location + d * ((far - cam.location).length + 8)
    wall.location.z = 20
    wall.rotation_euler = (math.radians(90), 0, math.atan2(d.y, d.x) - math.pi / 2)


# ---------------------------------------------------------------- scene
def setup(sc):
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        cy.device = "GPU"
    except Exception as e:  # CPU fallback
        print("GPU setup failed:", e)
    cy.samples = 48 if FAST else 256
    cy.use_denoising = True
    cy.max_bounces = 8
    cy.transmission_bounces = 8
    cy.glossy_bounces = 6
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = float(os.environ.get("EXPO", "-0.1"))
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = int(os.environ.get("PCT", "50")) if FAST else 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    # world: bundled CC0 studio HDRI for lighting + reflections
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(os.path.dirname(bpy.app.binary_path), "..", "Resources",
                                                  f"{bpy.app.version[0]}.{bpy.app.version[1]}", "datafiles",
                                                  "studiolights", "world", "sunrise.exr"))
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(140))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Generated"], mp.inputs[0])
    nt.links.new(mp.outputs[0], env.inputs[0])
    nt.links.new(env.outputs[0], nt.nodes["Background"].inputs[0])
    nt.nodes["Background"].inputs["Strength"].default_value = 0.6


def area(name, loc, target, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    ld.color = color
    o = link(bpy.data.objects.new(name, ld))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def build(variant):
    sc = T.reset()
    setup(sc)
    M = make_mats()
    rare = variant == "2"
    popped = {(-1, 0), (0, -1), (-1, -1), (1, 1)} if not rare else {(-1, 0), (0, 1), (1, -1)}
    panel = build_panel(M, M["rainbow"] if rare else None, popped)
    # camera: looking down onto the panel from the lower left, focus on the poked bubble
    tgt = Vector((0.6, 0.6, 0.25))
    cam = T.camera(sc, tgt + Vector((-2.3, -6.4, 5.6)), tgt, lens=34, roll=float(os.environ.get("ROLL", "30")))
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (cam.location - Vector((0, 0, 0.35))).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "0.1"))
    # lights: warm key from the top right, cool rim from behind
    area("Key", (6, -4, 9), (0, 0, 0), 1300, 6, (1.0, 0.93, 0.82))
    area("Fill", (-8, -6, 5), (0, 0, 0), 500, 8, (0.85, 0.92, 1.0))
    area("Rim", (2, 10, 6), (0, 0, 0), 900, 6, (0.9, 0.95, 1.0))
    # the poker comes in from the top right, pressing the focal bubble
    fw = panel.matrix_world
    bpy.context.view_layer.update()
    tip = fw @ Vector((FOCAL[0] * SPACING, FOCAL[1] * SPACING, 0.37))
    axis = Vector((0.95, -0.25, 1.05))
    side = Vector((-0.28, -0.78, 0.68))   # local +X (fingertips) toward the camera
    tool = build_tool(M, tip, axis, side)
    tool.scale = (0.85, 0.85, 0.85)
    build_background(M, cam)
    # golden burst at the tip + flying scraps
    bpy.context.view_layer.update()
    if rare:
        # rays fan out from BEHIND the rainbow bubble so it stays fully visible
        # rainbow bands run diagonally across the screen, whatever the bubble's turn
        fb = bpy.data.objects[f"B{FOCAL[0]}_{FOCAL[1]}"]
        bpy.context.view_layer.update()
        cw = cam.matrix_world.to_3x3()
        diag = fb.matrix_world.to_3x3().inverted() @ (cw.col[0] * 0.7 + cw.col[1] * 0.7)
        nt = M["rainbow"].node_tree
        dot = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeVectorMath")
        dot.inputs[1].default_value = diag.normalized() * 0.8 + Vector((0, 0, 0))
        mrn = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMapRange")
        mrn.inputs["From Min"].default_value = -0.4
        mrn.inputs["From Max"].default_value = 0.4
        centre = tip - Vector((0, 0, 0.12))
        spark_burst(M, centre + (cam.location - centre).normalized() * 0.9, cam, 2.3, strong=True, halo_k=1.4, core=0.0,
                    ring=0.72)
    else:
        spark_burst(M, tip + Vector((0.0, -0.05, 0.12)), cam, 1.5)
    rnd = random.Random(31 if rare else 17)
    for n in range(7 if not rare else 4):
        a = math.radians(rnd.uniform(100, 330))
        r = rnd.uniform(1.0, 2.0)
        p = tip + Vector((r * math.cos(a), r * math.sin(a), rnd.uniform(0.6, 1.8)))
        m = M["clearbit"] if n % 2 == 0 else M["bits"][n % 6]
        instance(f"Fly{n}", T.scrap_mesh(500 + n), m, p, (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)),
                 (rnd.uniform(0.28, 0.38),) * 3)
    for n, (dx, dy, dz, s) in enumerate(((-0.9, -0.2, 0.9, 0.28), (0.35, -0.7, 1.4, 0.2), (-1.4, 0.6, 0.5, 0.17))):
        twinkle(M, tip + Vector((dx, dy, dz)), cam, s * (1.4 if rare else 1.0), f"Tw{n}")
    if rare:   # gold coins popping out of the rainbow bubble
        cm = T.coin_mesh()
        tu, tv, td = T.project(sc, cam, tip)
        # (screen offset u, v from the bubble, depth factor, size in px at 1920 wide)
        for n, (du, dv, df, px) in enumerate(((-0.13, 0.16, 0.9, 120), (0.02, 0.27, 0.92, 110), (-0.24, 0.03, 0.85, 130),
                                              (0.12, 0.33, 0.95, 95), (-0.2, 0.3, 0.9, 100), (-0.3, -0.17, 0.8, 115))):
            d = td * df
            k = T.screen_scale(cam, d) / 1920.0
            o = instance(f"Coin{n}", cm, M["coin"], T.screen(cam, tu + du, tv + dv, d),
                         (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6)), (1.3 * px * k / 0.68,) * 3)
            o.parent = cam
    T.compositor(sc, bloom=0.9 if rare else 0.7, threshold=1.6, vignette=0.15)
    name = "thumb_2_rare" if rare else "thumb_1_poke"
    T.render(sc, os.path.join(OUT, name + ("_fast" if FAST else "") + ".png"))


if __name__ == "__main__":   # build_thumbnails_v3.py imports the helpers
    for v in ONLY:
        build(v)
