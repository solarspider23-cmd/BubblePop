# BubblePop thumbnail 5 "Bubble Blaster" (first person, no text). Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_thumbnails_v4.py
#   (add "-- fast" for a quick low-sample test; env PCT=<percent> sets its size)
#
# First-person view: blocky Roblox-style arms (black sleeves, white hands) hold a big
# chunky toy "bubble blaster" rocket launcher (teal tube, orange rings, yellow bell,
# red grip) in the lower right. A fat cartoon rocket (yellow body, red tip, teal fins)
# flies along a puffy white smoke trail curving into a giant wall of glossy light-blue
# bubble wrap, where a huge colourful cartoon burst (white/yellow/cyan cloud ring,
# spikes, shockwave ring) blows a crater of popped bubbles and sprays bubbles,
# confetti-like plastic scraps, gold coins, rainbow bubbles and icy diamonds outward.
# Output: art/thumbnails/thumb_5_rpg.png (Cycles, light DOF, bloom).
# Shared helpers: build_thumbnails.py (T), _v2 (V), _v3 (W).
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

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
SP = 1.2
link = T.link
mat = V.mat

CAM = Vector((1.0, -19.5, 3.4))
WALL_TURN = math.radians(-18)      # the wall recedes toward the right of the frame
HIT = (-2.6, 7.4)                  # impact point on the wall (wall-local x, height)


def wall_matrix():
    return Matrix.Rotation(WALL_TURN, 4, "Z") @ Matrix.Rotation(math.radians(90), 4, "X")


def wall_point(u, v, out=0.0):
    """World point on the wall at local (u along, v up), `out` toward the viewer."""
    return wall_matrix() @ Vector((u, v, out))


def build_wall(M):
    dome = V.hi_dome()
    pop = T.popped_mesh()
    root = link(bpy.data.objects.new("Wall", None))
    root.matrix_world = wall_matrix()
    rnd = random.Random(4)
    hx, hz = HIT
    for i in range(-26, 22):
        for k in range(0, 20):
            x, z = i * SP, k * SP + 0.6
            d = math.hypot(x - hx, z - hz) + rnd.uniform(-0.5, 0.5)
            if d < 2.0:
                continue                      # blown clean away: bare film in the crater
            if d < 4.3:
                V.instance(f"WP{i}_{k}", pop, M["popped"], (x, z, 0), (0, 0, rnd.uniform(0, 6.3)), (1, 1, 1.4), root)
            else:
                s = (1 + rnd.uniform(-0.015, 0.015),) * 2 + (1 + rnd.uniform(-0.03, 0.03),)
                V.instance(f"W{i}_{k}", dome, M["bubble"], (x, z, 0), (0, 0, rnd.uniform(0, 6.3)), s, root)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
    f = T.mesh_obj("WallFilm", bm, M["film"], smooth=False)
    f.parent = root
    f.scale = (40, 20, 1)
    f.location = (-3, 12, -0.01)
    # floor of bubble wrap in front of the wall
    W.bubble_floor(M, (-24, 20), (-16, 4), gone_fn=lambda x, y: (wall_matrix().inverted() @ Vector((x, y, 0))).z < 0.7)


def build_launcher(M, rear, aim, up_hint, scale=0.34):
    """Toy bubble blaster. Local +Z = barrel toward the muzzle, local +Y = up."""
    z = (aim - rear).normalized()
    x = Vector(up_hint).cross(z).normalized()
    y = z.cross(x)
    root = link(bpy.data.objects.new("Launcher", None))
    root.matrix_world = Matrix.Translation(rear) @ Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Scale(scale, 4)
    L = V.lathe_obj
    L("Tube", [(0.0, 3.7), (0.5, 3.7), (0.5, 0.25), (0.42, 0.05), (0.0, 0.0)], M["teal"], 48, root)
    L("RearCap", [(0.0, 0.3), (0.6, 0.3), (0.66, 0.15), (0.6, -0.15), (0.35, -0.3), (0.0, -0.32)], M["orange"], 48, root)
    for zc in (1.45, 2.75):
        L("Ring", [(0.0, zc + 0.16), (0.58, zc + 0.16), (0.62, zc + 0.08), (0.62, zc - 0.08), (0.58, zc - 0.16), (0.0, zc - 0.16)],
          M["orange"], 48, root)
    L("Bell", [(0.0, 4.55), (0.92, 4.55), (0.98, 4.45), (0.8, 4.1), (0.56, 3.7), (0.45, 3.5), (0.0, 3.5)], M["yellow"], 48, root)
    L("BellIn", [(0.0, 4.56), (0.8, 4.56), (0.0, 4.2)], M["navy"], 48, root)
    # top sight + grips
    V.rbox("Sight", (0.36, 0.42, 1.2), (0.0, 0.68, 2.1), M["yellow"], 0.14, parent=root)
    s = V.lathe_obj("SightDot", [(0.0, 0.0), (0.12, 0.0), (0.0, -0.06)], M["red"], 24, root)
    s.location = (0, 0.82, 2.72)
    V.rbox("Grip", (0.4, 1.0, 0.5), (0.0, -0.85, 1.6), M["red"], 0.15, rot=(math.radians(-20), 0, 0), parent=root)
    V.rbox("Trigger", (0.12, 0.3, 0.12), (0.0, -0.55, 2.0), M["navy"], 0.04, parent=root)
    V.rbox("FrontGrip", (0.4, 0.8, 0.45), (0.0, -0.75, 2.9), M["orange"], 0.15, parent=root)
    # cute bubble studs on the side (the "bubble blaster")
    dome = V.hi_dome()
    for n, (a, zc, sc) in enumerate(((150, 0.75, 0.42), (170, 2.15, 0.36), (140, 3.25, 0.3), (200, 0.75, 0.3))):
        t = math.radians(a)
        o = V.instance(f"Stud{n}", dome, M["bubble"], (0.5 * math.cos(t), 0.5 * math.sin(t), zc),
                       (0, 0, 0), (sc,) * 3, root)
        o.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector((math.cos(t), math.sin(t), 0))).to_euler()
    bpy.context.view_layer.update()
    return root


def blocky_arm(M, name, hand_at, arm_dir, hand_size=0.62, arm_len=4.0, arm_w=0.7, turn=None):
    """Roblox arm: a white rounded-cube hand at hand_at, black sleeve running back along arm_dir."""
    d = Vector(arm_dir).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    if turn is not None:
        q = q @ Matrix.Rotation(turn, 3, "Z").to_quaternion()
    hand = V.rbox(name + "Hand", (hand_size, hand_size, hand_size * 1.05), (0, 0, 0), M["hand"], 0.16)
    hand.location = hand_at
    hand.rotation_euler = q.to_euler()
    sl = V.rbox(name + "Sleeve", (arm_w, arm_w, arm_len), (0, 0, 0), M["sleeve"], 0.08)
    sl.location = Vector(hand_at) + d * (hand_size * 0.5 + arm_len / 2 - 0.05)
    sl.rotation_euler = q.to_euler()
    return hand, sl


def rocket(M, at, direction):
    root = link(bpy.data.objects.new("Rocket", None))
    z = Vector(direction).normalized()
    x = Vector((0, 0, 1)).cross(z).normalized()
    y = z.cross(x)
    root.matrix_world = Matrix.Translation(at) @ Matrix((x, y, z)).transposed().to_4x4()
    L = V.lathe_obj
    L("RBody", [(0.0, 1.5), (0.45, 1.5), (0.5, 1.2), (0.5, 0.0), (0.42, -0.15), (0.0, -0.15)], M["yellow"], 48, root)
    L("RBand", [(0.0, 0.95), (0.53, 0.95), (0.53, 0.7), (0.0, 0.7)], M["orange"], 48, root)
    L("RTip", [(0.0, 2.35), (0.18, 2.28), (0.36, 2.05), (0.47, 1.75), (0.48, 1.5), (0.0, 1.5)], M["red"], 48, root)
    L("RNozzle", [(0.0, -0.1), (0.32, -0.1), (0.38, -0.4), (0.0, -0.4)], M["navy"], 32, root)
    for n in range(4):
        a = n * math.pi / 2 + math.pi / 4
        fin = V.rbox(f"Fin{n}", (0.09, 0.55, 0.75), (0, 0, 0), M["teal"], 0.04, parent=root)
        fin.location = (0.62 * math.cos(a), 0.62 * math.sin(a), 0.15)
        fin.rotation_euler = (0, 0, a + math.pi / 2)
    win = V.lathe_obj("RWindow", [(0.0, 0.05), (0.2, 0.0), (0.0, -0.02)], M["white"], 24, root)
    win.location = (0, -0.5, 1.15)
    win.rotation_euler = (math.radians(90), 0, 0)
    return root


def out_dir(p):
    return (wall_matrix().to_3x3() @ Vector((0, 0, 1))).normalized()


def bezier(a, c, b, t):
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b


def thumb_5():
    sc = T.reset()
    V.setup(sc)
    M = W.extra_mats(V.make_mats())
    M["teal"] = mat("Teal", (20, 200, 190), rough=0.2, coat=1.0)
    M["orange"] = mat("Orange", (255, 120, 20), rough=0.2, coat=1.0)
    M["red"] = mat("Red", (240, 40, 50), rough=0.2, coat=1.0)
    M["hand"] = mat("HandWhite", (245, 245, 248), rough=0.5)
    M["sleeve"] = mat("SleeveBlack", (28, 28, 34), rough=0.6)
    M["cloud"] = mat("Cloud", (235, 248, 255), rough=0.6, coat=0.3)
    M["flash"] = V.glow("Flash", (255, 240, 170), 2.5)
    M["cyanring"] = V.glow("CyanRing", (110, 230, 255), 3.0)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    hit = wall_point(*HIT)
    nrm = (wall_matrix().to_3x3() @ Vector((0, 0, 1))).normalized()     # wall faces the viewer
    tgt = hit + Vector((5.4, 0, -1.2))
    cam = T.camera(sc, CAM, tgt, lens=28, roll=0)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (hit - CAM).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "4.0"))
    bpy.context.view_layer.update()
    cw = cam.matrix_world.to_3x3()
    right, upv, fwd = cw.col[0], cw.col[1], -cw.col[2]
    build_wall(M)
    # launcher in the lower right, aimed at the hit point
    rear = CAM + right * 1.0 - upv * 0.42 + fwd * 1.6
    launcher = build_launcher(M, rear, hit + Vector((0, 0, 1.5)), upv)
    lw = launcher.matrix_world
    muzzle = lw @ Vector((0, 0, 4.6))
    # blocky arms: right hand on the pistol grip, left hand on the front grip
    blocky_arm(M, "R", lw @ Vector((0.0, -1.2, 1.5)), (right * 0.55 - upv * 0.7 - fwd * 0.45), hand_size=0.36, arm_len=2.5, arm_w=0.4)
    blocky_arm(M, "L", lw @ Vector((-0.1, -1.05, 2.9)), (-right * 0.45 - upv * 0.85 - fwd * 0.2), hand_size=0.36, arm_len=2.5, arm_w=0.4)
    # rocket mid-flight on a curving path + puffy smoke trail
    # the rocket is placed on screen (centre, a bit high) deep in the room, flying
    # sideways-and-in toward the blast so it reads in profile; the trail arcs back to the muzzle
    rp = cam.matrix_world @ T.screen(cam, float(os.environ.get("RU", "-0.05")), float(os.environ.get("RV", "0.12")),
                                     float(os.environ.get("RD", "15.5")))
    rdir = (hit + out_dir(hit) * 0.5 - rp).normalized()
    rocket(M, rp, rdir).scale = (1.8,) * 3
    tail = rp - rdir * 1.2
    ctrl = (muzzle + tail) / 2 + upv * 1.6 + right * 0.3
    smoke, ell, caps = W.metaball("Smoke", M["cloud"], res=0.05)
    rnd = random.Random(12)
    n = 54
    for k in range(n):
        t = 0.04 + 0.96 * k / (n - 1)
        p = bezier(muzzle, ctrl, tail, t) + Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), rnd.uniform(-0.08, 0.08)))
        r = 0.09 + 0.36 * (k / (n - 1)) ** 0.6 + rnd.uniform(-0.03, 0.03)
        ell(p, r)
    # the BIG burst at the wall
    out = nrm
    burst_c = hit + out * 1.0
    puff, pell, _ = W.metaball("BurstCloud", M["cloud"], res=0.06)
    for k in range(16):     # ring of fat cloud puffs round the crater
        a = 2 * math.pi * k / 16 + rnd.uniform(-0.08, 0.08)
        r = 3.4 + rnd.uniform(-0.3, 0.4)
        local = Vector((HIT[0] + r * math.cos(a), HIT[1] + r * math.sin(a), 0.9 + rnd.uniform(0, 0.9)))
        pell(wall_matrix() @ local, rnd.uniform(0.6, 0.9))
    V.spark_burst(M, hit + out * 3.0, cam, 5.2, strong=True, halo_k=2.0, core=0.0, ring=2.6, light=False)
    fl = bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=burst_c)
    f = bpy.context.active_object
    f.name = "Flash"
    f.scale = (1, 1, 1)
    f.data.materials.append(M["flash"])
    for r, k in ((5.6, 2.6), (6.6, 1.4)):
        ring = W.impact_ring(M, (0, 0, 0), r, k, "Shock")
        ring.data.materials[0] = M["cyanring"]
        ring.matrix_world = Matrix.Translation(hit + out * 0.4) @ (wall_matrix().to_3x3().to_4x4()) @ Matrix.Scale(1, 4)
    lt = bpy.data.lights.new("BlastLight", "POINT")
    lt.energy = 700
    lt.color = (1.0, 0.95, 0.8)
    lt.shadow_soft_size = 2.0
    link(bpy.data.objects.new("BlastLight", lt)).location = burst_c + out * 2.0
    # spray: bubbles, scraps, coins, rainbow + diamond bubbles flying out toward the viewer
    dome = V.hi_dome()
    ball = W.sphere_bubble_mesh()
    cm = T.coin_mesh()
    gm = W.gem_mesh()
    hu, hv, _ = T.project(sc, cam, hit)
    ru, rv, _ = T.project(sc, cam, rp)

    def clear_of_rocket(p, margin=0.1):
        pu, pv, _ = T.project(sc, cam, p)
        return math.hypot(pu - ru, (pv - rv) * 0.56) > margin
    tang_u = (wall_matrix().to_3x3() @ Vector((1, 0, 0)))
    tang_v = (wall_matrix().to_3x3() @ Vector((0, 1, 0)))
    for k in range(150):
        a = rnd.uniform(0, 2 * math.pi)
        spread = rnd.uniform(0.7, 2.2)
        d = (out + (tang_u * math.cos(a) + tang_v * math.sin(a)) * spread).normalized()
        dist = rnd.uniform(3.0, 8.0)
        p = hit + d * dist
        if (p - CAM).length < 5.0 or (p - rear).length < 3.5:
            continue
        pu, pv, _ = T.project(sc, cam, p)
        if (pu > hu + 0.13 and -0.25 < pv < 0.4) or not clear_of_rocket(p, 0.09):
            continue                              # keep the rocket's lane clear
        rot = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
        roll = rnd.random()
        if roll < 0.4:
            V.instance(f"FlyB{k}", dome, M["bubble"], p, rot, (rnd.uniform(0.7, 1.05),) * 3)
        elif roll < 0.55:
            V.instance(f"FlyS{k}", ball, M["bubble"], p, rot, (rnd.uniform(0.45, 0.8),) * 3)
        else:
            m = M["clearbit"] if rnd.random() < 0.25 else M["bits"][k % 6]
            V.instance(f"FlyX{k}", T.scrap_mesh(4000 + k % 50), m, p, rot, (rnd.uniform(0.22, 0.34),) * 3)
    # hero goodies in the spray (placed so they read)
    for k, (du, dv, do, s) in enumerate(((-4.6, 2.8, 4.5, 1.0), (3.8, 3.6, 5.5, 0.95), (-2.0, -3.6, 6.5, 1.1),
                                          (5.6, -1.2, 6.0, 1.0), (-6.4, -0.6, 5.0, 0.9), (1.4, 5.0, 4.0, 0.9))):
        if not clear_of_rocket(hit + tang_u * du + tang_v * dv + out * do):
            continue
        V.instance(f"Coin{k}", cm, M["coin"], hit + tang_u * du + tang_v * dv + out * do,
                   (rnd.uniform(0.3, 1.2), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6)), (s * 1.6,) * 3)
    for k, (du, dv, do) in enumerate(((-5.4, 4.2, 3.5), (5.2, 1.8, 6.5))):
        V.instance(f"Rainbow{k}", ball, M["rainbow"], hit + tang_u * du + tang_v * dv + out * do, (0.3, 0.2, 0.5), (1.2,) * 3)
    for k, (du, dv, do) in enumerate(((3.2, 5.6, 3.0), (-3.4, -2.2, 8.0))):
        V.instance(f"Gem{k}", gm, M["ice"], hit + tang_u * du + tang_v * dv + out * do,
                   (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 6)), (0.7,) * 3)
    for k, (du, dv, do, s) in enumerate(((-7.0, 3.5, 2.0, 0.6), (6.8, 4.5, 2.5, 0.5), (0.5, -5.2, 3.0, 0.45),
                                          (-1.2, 7.2, 2.0, 0.55))):
        V.twinkle(M, hit + tang_u * du + tang_v * dv + out * do, cam, s, f"Tw{k}")
    # light
    V.area("Key", tuple(CAM + Vector((-6, 2, 9))), tuple(hit), 2000, 10, (1.0, 0.95, 0.88))
    V.area("Fill", tuple(CAM + Vector((6, -2, 3))), tuple(hit), 1200, 8, (0.9, 0.95, 1.0))
    V.area("Hands", tuple(CAM + Vector((2, 1, 4))), tuple(rear), 300, 3, (1.0, 0.97, 0.92))
    T.compositor(sc, bloom=0.8, threshold=1.6, vignette=0.12)
    T.render(sc, os.path.join(T.OUT, "thumb_5_rpg" + ("_fast" if FAST else "") + ".png"))


if __name__ == "__main__":
    thumb_5()
