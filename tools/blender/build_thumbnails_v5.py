# BubblePop thumbnails 6 + 7 (no text). Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_thumbnails_v5.py
#   (add "-- 6" or "-- 7" for one only, "-- fast" for a quick test; env PCT=<percent>)
#
# 6  thumb_6_half.png     "Half and half": a big wall of glossy light-blue bubble wrap seen
#                         at an angle; left half shiny untouched, right half fully popped,
#                         a crisp dividing line; a first-person blocky Roblox hand (white
#                         hand, black sleeve) pokes the line with a chunky yellow/black
#                         poker, sparkle burst + flying scraps.
# 7  thumb_7_tsunami.png  "Bubble tsunami": a giant curling wave made of bubble wrap,
#                         popping and spraying bubbles off its crest like foam, towering
#                         over an excited blocky Roblox-style avatar on a bubble wrap
#                         floor; sunny, warm, fun.
# Shared helpers: build_thumbnails.py (T), _v2 (V), _v3 (W), _v4 (R).
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_thumbnails as T  # noqa: E402
import build_thumbnails_v2 as V  # noqa: E402
import build_thumbnails_v3 as W  # noqa: E402
import build_thumbnails_v4 as R  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
ONLY = [a for a in ARGS if a in ("6", "7")] or ["6", "7"]
SP = 1.2
link = T.link
mat = V.mat


def base_mats():
    M = W.extra_mats(V.make_mats())
    M["hand"] = mat("HandWhite", (245, 245, 248), rough=0.5)
    M["sleeve"] = mat("SleeveBlack", (28, 28, 34), rough=0.6)
    M["teal"] = mat("Teal", (20, 200, 190), rough=0.2, coat=1.0)
    M["orange"] = mat("Orange", (255, 120, 20), rough=0.2, coat=1.0)
    return M


def poker(M, tip, axis, up_hint, scale=1.0):
    """Chunky poker: steel needle + ferrule + yellow handle with black grips. Local +Z up the tool."""
    z = Vector(axis).normalized()
    x = Vector(up_hint).cross(z).normalized()
    y = z.cross(x)
    root = link(bpy.data.objects.new("Poker", None))
    root.matrix_world = Matrix.Translation(tip) @ Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Scale(scale, 4)
    L = V.lathe_obj
    L("Pin", [(0.0, 1.55), (0.085, 1.55), (0.075, 0.35), (0.03, 0.06), (0.0, 0.0)], M["steel"], 32, root)
    L("Ferrule", [(0.0, 1.95), (0.2, 1.95), (0.23, 1.85), (0.23, 1.6), (0.15, 1.5), (0.0, 1.5)], M["steel"], 48, root)
    L("Handle", [(0.0, 5.15), (0.22, 5.12), (0.36, 4.98), (0.4, 4.7), (0.4, 2.2), (0.33, 1.98), (0.22, 1.9), (0.0, 1.9)],
      M["handle"], 48, root)
    for z0, z1 in ((2.3, 2.85), (3.1, 3.65)):
        L("Grip", [(0.0, z1), (0.415, z1), (0.43, z1 - 0.06), (0.43, z0 + 0.06), (0.415, z0), (0.0, z0)], M["grip"], 48, root)
    bpy.context.view_layer.update()
    return root


# ---------------------------------------------------------------- 6: half and half
def thumb_6():
    sc = T.reset()
    V.setup(sc)
    M = base_mats()
    M["popped"] = mat("PoppedFlat", (120, 195, 250), rough=0.3, coat=0.6, transm=0.25, film=300)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    turn = math.radians(-32)
    wm = Matrix.Rotation(turn, 4, "Z") @ Matrix.Rotation(math.radians(90), 4, "X")
    root = link(bpy.data.objects.new("Wall", None))
    root.matrix_world = wm
    dome = V.hi_dome()
    pop = T.popped_mesh()
    rnd = random.Random(6)
    LINE = 0       # column index of the dividing line: columns < LINE intact, >= LINE popped
    FOC = (LINE, 6)   # the bubble being poked (on the line)
    for i in range(-22, 26):
        for k in range(0, 18):
            x, zz = i * SP, k * SP + 0.6
            if (i, k) == FOC:
                V.instance("Focal", dome, M["bubble"], (x, zz, 0), (0, 0, 0), (1.06, 1.06, 0.78), root)
            elif i < LINE:
                s = (1 + rnd.uniform(-0.015, 0.015),) * 2 + (1 + rnd.uniform(-0.03, 0.03),)
                V.instance(f"B{i}_{k}", dome, M["bubble"], (x, zz, 0), (0, 0, rnd.uniform(0, 6.3)), s, root)
            else:
                V.instance(f"P{i}_{k}", pop, M["popped"], (x, zz, 0), (0, 0, rnd.uniform(0, 6.3)), (1, 1, 1.2), root)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
    f = T.mesh_obj("WallFilm", bm, M["film"], smooth=False)
    f.parent = root
    f.scale = (40, 16, 1)
    f.location = (0, 10, -0.01)
    W.bubble_floor(M, (-30, 30), (-20, 6), gone_fn=lambda x, y: (wm.inverted() @ Vector((x, y, 0))).z < 0.7)
    focal = wm @ Vector((FOC[0] * SP, FOC[1] * SP + 0.6, 0.0))
    out = (wm.to_3x3() @ Vector((0, 0, 1))).normalized()
    along = (wm.to_3x3() @ Vector((1, 0, 0))).normalized()
    cam_pos = focal + out * 7.2 - along * 1.6 + Vector((0, 0, 0.4))
    cam = T.camera(sc, cam_pos, focal + along * 1.2 - Vector((0, 0, 0.3)), lens=30, roll=0)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (focal - cam_pos).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "3.0"))
    bpy.context.view_layer.update()
    cw = cam.matrix_world.to_3x3()
    right, upv, fwd = cw.col[0], cw.col[1], -cw.col[2]
    tip = focal + out * 0.33
    # the poker comes from the lower right of the screen (the player's right hand)
    hand_at = cam_pos + fwd * 3.2 + right * 1.25 - upv * 0.95
    axis = (hand_at - tip).normalized()
    PS = 0.85
    pk = poker(M, tip, axis, upv, scale=PS)
    hand_c = pk.matrix_world @ Vector((0, 0, 4.25))
    R.blocky_arm(M, "R", hand_c, (right * 0.5 - upv * 0.75 - fwd * 0.5), hand_size=0.8, arm_len=3.5, arm_w=0.72)
    V.spark_burst(M, tip + out * 0.15, cam, 1.3, core=0.12, halo_k=1.6)
    for n in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        p = tip + out * rnd.uniform(0.6, 2.0) + (along * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * rnd.uniform(0.7, 1.6)
        m = M["clearbit"] if n % 2 == 0 else M["bits"][n % 6]
        V.instance(f"Fly{n}", T.scrap_mesh(700 + n), m, p, (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)),
                   (rnd.uniform(0.17, 0.24),) * 3)
    for n, (da, dz, do, s) in enumerate(((-1.2, 1.0, 0.8, 0.22), (1.0, 1.3, 0.6, 0.18), (0.6, -0.9, 0.9, 0.16))):
        V.twinkle(M, tip + along * da + Vector((0, 0, dz)) + out * do, cam, s, f"Tw{n}")
    V.area("Key", tuple(cam_pos + Vector((-4, 0, 6))), tuple(focal), 1400, 6, (1.0, 0.93, 0.82))
    V.area("Fill", tuple(cam_pos + Vector((4, -2, 2))), tuple(focal), 400, 6, (0.9, 0.95, 1.0))
    T.compositor(sc, bloom=0.7, threshold=1.6, vignette=0.12)
    T.render(sc, os.path.join(T.OUT, "thumb_6_half" + ("_fast" if FAST else "") + ".png"))


# ---------------------------------------------------------------- 7: bubble tsunami
def wave_profile():
    """Cross-section of the curling wave in (x, z): flat base far behind (+x), a concave
    face rising toward the viewer, a crest and a lip curling over toward -x."""
    pts = [Vector(p) for p in ((22, 0), (12, 0), (7.5, 1.0), (4.5, 4.5), (3.6, 9.0), (4.2, 13.0), (2.5, 16.2),
                               (-1.0, 17.0), (-4.0, 15.6), (-5.6, 13.0), (-5.6, 10.4), (-4.6, 8.6))]
    # Catmull-Rom resample
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for k in range(12):
            t = k / 12
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return [Vector((p.x * 1.25, p.y * 1.3)) for p in out]


def avatar(M, at, face_dir):
    """Generic blocky avatar, 5 studs tall, arms up, big smile."""
    root = link(bpy.data.objects.new("Avatar", None))
    root.location = at
    root.rotation_euler = (0, 0, math.atan2(face_dir.x, -face_dir.y))   # local -Y (the face) toward face_dir
    skin = mat("AvSkin", (255, 205, 60), rough=0.4, coat=0.3)
    shirt = mat("AvShirt", (240, 60, 70), rough=0.5)
    pants = mat("AvPants", (40, 90, 220), rough=0.6)
    black = mat("AvFace", (20, 20, 28), rough=0.4)
    tongue = mat("AvTongue", (255, 110, 130), rough=0.4)
    B = V.rbox
    for s in (-1, 1):
        B("Leg", (0.95, 0.95, 2.0), (s * 0.5, 0, 1.0), pants, 0.08, parent=root)
    B("Torso", (2.0, 1.0, 2.0), (0, 0, 3.0), shirt, 0.1, parent=root)
    for s in (-1, 1):   # arms thrown up in excitement
        arm = B("Arm", (0.95, 0.95, 2.0), (0, 0, 0), skin, 0.1, parent=root)
        arm.location = (s * 1.45, 0, 4.75)
        arm.rotation_euler = (0, math.radians(s * 20), 0)
    B("Head", (1.25, 1.2, 1.2), (0, 0, 4.65), skin, 0.28, parent=root)
    # face on local -Y (toward the camera after the turn)
    for s in (-1, 1):
        e = B("Eye", (0.14, 0.06, 0.3), (s * 0.24, -0.6, 4.78), black, 0.05, parent=root)
    mo = T.flat_poly("Mouth", [(0.36 * math.cos(a), -0.32 * abs(math.sin(a)) * 1.0) for a in
                               [math.pi * k / 16 for k in range(17)]], black, depth=0.03)
    mo.parent = root
    mo.location = (0, -0.61, 4.52)
    mo.rotation_euler = (math.radians(90), 0, 0)
    tg = T.flat_poly("Tongue", [(0.18 * math.cos(a), -0.32 + 0.12 * math.sin(a)) for a in
                                [math.pi * k / 12 for k in range(13)]], tongue, depth=0.02)
    tg.parent = root
    tg.location = (0, -0.625, 4.52)
    tg.rotation_euler = (math.radians(90), 0, 0)
    return root


def sky_world(sc, top, horizon):
    """HDRI for light/reflections, a clean blue gradient sky for what the camera sees."""
    w = sc.world
    nt = w.node_tree
    N, L = nt.nodes.new, nt.links.new
    bg = nt.nodes["Background"]
    out = nt.nodes["World Output"]
    lp = N("ShaderNodeLightPath")
    tc = N("ShaderNodeTexCoord")
    sx = N("ShaderNodeSeparateXYZ")
    cr = N("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = T.rgba(horizon)
    cr.color_ramp.elements[1].position = 0.45
    cr.color_ramp.elements[1].color = T.rgba(top)
    sky = N("ShaderNodeBackground")
    sky.inputs["Strength"].default_value = 1.0
    mx = N("ShaderNodeMixShader")
    L(tc.outputs["Generated"], sx.inputs[0])
    L(sx.outputs["Z"], cr.inputs[0])
    L(cr.outputs[0], sky.inputs[0])
    L(lp.outputs["Is Camera Ray"], mx.inputs[0])
    L(bg.outputs[0], mx.inputs[1])
    L(sky.outputs[0], mx.inputs[2])
    L(mx.outputs[0], out.inputs["Surface"])


def thumb_7():
    sc = T.reset()
    V.setup(sc)
    M = base_mats()
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    sky_world(sc, (70, 150, 255), (200, 235, 255))
    rnd = random.Random(7)
    prof = wave_profile()
    # arc-length stations along the profile
    acc = [0.0]
    for a, b in zip(prof, prof[1:]):
        acc.append(acc[-1] + (b - a).length)
    total = acc[-1]

    def at_s(s):
        for i in range(len(acc) - 1):
            if acc[i + 1] >= s:
                t = (s - acc[i]) / max(1e-6, acc[i + 1] - acc[i])
                p = prof[i].lerp(prof[i + 1], t)
                d = (prof[i + 1] - prof[i]).normalized()
                return p, d
        return prof[-1], (prof[-1] - prof[-2]).normalized()

    WY = (-26, 26)
    # the film: a thick sheet following the profile, with the curl tightening a bit in the middle
    def bend(y):
        return 1.0 + 0.12 * math.cos(y / 26 * math.pi)       # 0.88 .. 1.12: crest leans further in the middle

    def warp(p2, y):
        k = bend(y)
        h = 0.45 + 0.55 * min(1.0, max(0.0, (WY[1] - y) / (WY[1] - WY[0]))) ** 0.8   # tallest at the near (-y) end
        return Vector((p2.x * (1.0 if p2.y < 6 else k) * (0.6 + 0.4 * h) - 1.5 * math.sin(y / 9.0) * (p2.y / 17), y,
                       p2.y * (0.92 + 0.08 * k) * h))

    bm = bmesh.new()
    nprof = len(prof)
    ys = [WY[0] + (WY[1] - WY[0]) * j / 60 for j in range(61)]
    grid = [[bm.verts.new(warp(prof[i], y)) for i in range(nprof)] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(nprof - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    film = T.mesh_obj("WaveFilm", bm, M["film"], smooth=True)
    sol = film.modifiers.new("Thick", "SOLIDIFY")
    sol.thickness = 0.12
    # bubbles on the face/inside of the curl (the side toward the viewer, normal = left of the direction)
    dome = V.hi_dome()
    pop = T.popped_mesh()
    s = 0.6
    while s < total - 0.4:
        p2, d2 = at_s(s)
        n2 = Vector((-d2.y, d2.x))      # profile runs +x -> -x, so this points toward -x / inside the curl
        if n2.x > 0:
            n2 = -n2
        y = WY[0] + 0.6
        while y < WY[1]:
            p = warp(p2, y)
            pn = warp(p2 + n2 * 0.05, y)
            nrm = (pn - p).normalized()
            q = Vector((0, 0, 1)).rotation_difference(nrm)
            rotm = q.to_euler()
            near_lip = s > total - 6.5
            if near_lip and rnd.random() < 0.55:
                o = V.instance("WP", pop, M["popped"], p, rotm, (1, 1, 1.3))
            elif not (near_lip and rnd.random() < 0.35):
                o = V.instance("WB", dome, M["bubble"], p, rotm, (1, 1, 1))
            y += SP
        s += SP
    # floor in front of the wave
    W.bubble_floor(M, (-50, 4), (-40, 40), gone_fn=lambda x, y: x > 3.0)
    # foam spray off the crest and lip
    ball = W.sphere_bubble_mesh()
    cm = T.coin_mesh()
    for k in range(420):
        y = rnd.uniform(-26, 10)
        s0 = rnd.uniform(total - 9, total)
        p2, d2 = at_s(s0)
        base = warp(p2, y)
        p = base + Vector((rnd.uniform(-4.5, 0.5), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.5, 3.0)))
        rot = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
        rr = rnd.random()
        if rr < 0.45:
            V.instance("FoamB", dome, M["bubble"], p, rot, (rnd.uniform(0.6, 1.0),) * 3)
        elif rr < 0.7:
            V.instance("FoamS", ball, M["bubble"], p, rot, (rnd.uniform(0.45, 0.9),) * 3)
        elif rr < 0.97:
            m = M["clearbit"] if rnd.random() < 0.5 else M["bits"][k % 6]
            V.instance("FoamX", T.scrap_mesh(5000 + k % 60), m, p, rot, (rnd.uniform(0.25, 0.38),) * 3)
        else:
            V.instance("FoamC", cm, M["coin"], p, rot, (1.4,) * 3)
    # camera low in front, looking up at the wave over the avatar
    cam_pos = Vector((float(os.environ.get("CX", "-13")), float(os.environ.get("CY", "-38")), 1.2))
    tgt = Vector((1.5, -15.5, 11.0))
    cam = T.camera(sc, cam_pos, tgt, lens=17, roll=0)
    cam.data.dof.use_dof = True
    av_at = Vector((-6.0, -32.5, 0.3))
    cam.data.dof.focus_distance = (av_at + Vector((0, 0, 3)) - cam_pos).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "1.6"))
    face = (cam_pos - av_at)
    face.z = 0
    av = avatar(M, av_at, face.normalized())
    bpy.context.view_layer.update()
    for n, (x, y, z, sz) in enumerate(((-6, -8, 14, 0.8), (-3, 6, 16, 0.6), (-8, 2, 9, 0.5), (-12, -6, 7, 0.4))):
        V.twinkle(M, Vector((x, y, z)), cam, sz, f"Tw{n}")
    sun = T.sun("Sun", (-0.6, -0.3, 0.75), 3.0, angle=3)
    sun.data.color = (1.0, 0.93, 0.82)
    V.area("Fill", tuple(cam_pos + Vector((2, -4, 6))), tuple(av_at), 800, 8, (0.95, 0.97, 1.0))
    T.compositor(sc, bloom=0.6, threshold=1.6, vignette=0.1)
    T.render(sc, os.path.join(T.OUT, "thumb_7_tsunami" + ("_fast" if FAST else "") + ".png"))


if __name__ == "__main__":
    if "6" in ONLY:
        thumb_6()
    if "7" in ONLY:
        thumb_7()
