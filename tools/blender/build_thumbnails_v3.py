# BubblePop game thumbnails, v3: original compositions with the polished glossy
# look (glossy 3D, shallow depth of field, warm bright light, saturated colours,
# one clear focal point, no text). Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_thumbnails_v3.py
#   (add "-- 3" or "-- 4" for one only, "-- fast" for a quick low-sample test;
#    env PCT=<percent> sets the fast test size)
#
# 3  thumb_3_stomp.png  low floor-level camera: a chunky red cartoon sneaker with big
#                       chrome spikes on the sole ("Spiky Boots") stomping onto glossy
#                       bubble wrap; a ring of bubbles bursting round the sole with
#                       sparkles, an impact ring and flying plastic scraps; a trail of
#                       popped bubbles leading back into the blurred distance.
# 4  thumb_4_haul.png   a big purple sack bursting at the seams, overflowing with
#                       colourful plastic scraps, a glowing rainbow bubble on top, icy
#                       diamond scraps and gold coins spilling onto bubble wrap, in
#                       front of a blurred wall of glossy bubble wrap.
#
# Shared helpers/materials: build_thumbnails.py (T) and build_thumbnails_v2.py (V).
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

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
ONLY = [a for a in ARGS if a in ("3", "4")] or ["3", "4"]
OUT = T.OUT
SP = 1.2
rgba = T.rgba
link = T.link
mat = V.mat


# ---------------------------------------------------------------- shared bits
def metaball(name, m, res=0.02):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.08
    mb.render_resolution = res
    mb.threshold = 0.6
    o = link(bpy.data.objects.new(name, mb))
    mb.materials.append(m)

    def ell(c, r, sx=1, sy=1, sz=1):
        e = mb.elements.new()
        e.type = "ELLIPSOID"
        e.co = c
        e.radius = r / 0.575
        e.size_x, e.size_y, e.size_z = sx, sy, sz
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
    return o, ell, caps


def bubble_floor(M, xr, yr, popped_fn=None, gone_fn=None, seed=3):
    """Floor sheet of glossy bubbles (z = 0 film top)."""
    dome = V.hi_dome()
    pop = T.popped_mesh()
    rnd = random.Random(seed)
    for i in range(int(xr[0] / SP), int(xr[1] / SP) + 1):
        for j in range(int(yr[0] / SP), int(yr[1] / SP) + 1):
            x, y = i * SP + (0.0 if j % 2 == 0 else 0.0), j * SP
            if gone_fn and gone_fn(x, y):
                continue
            if popped_fn and popped_fn(x, y):
                V.instance(f"FP{i}_{j}", pop, M["popped"], (x, y, 0), (0, 0, rnd.uniform(0, 6.3)), (1, 1, 1.4))
            else:
                s = (1 + rnd.uniform(-0.015, 0.015),) * 2 + (1 + rnd.uniform(-0.03, 0.03),)
                V.instance(f"FB{i}_{j}", dome, M["bubble"], (x, y, 0), (0, 0, rnd.uniform(0, 6.3)), s)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200)
    f = T.mesh_obj("FloorFilm", bm, M["film"], smooth=False)
    f.location.z = -0.01


def bubble_wall(M, y, xr, zr, seed=4):
    """Vertical wall of bubbles facing -Y at depth y."""
    dome = V.hi_dome()
    rnd = random.Random(seed)
    root = link(bpy.data.objects.new("Wall", None))
    root.location = (0, y, 0)
    root.rotation_euler = (math.radians(90), 0, 0)   # local +Z -> world -Y
    for i in range(int(xr[0] / SP), int(xr[1] / SP) + 1):
        for k in range(int(zr[0] / SP), int(zr[1] / SP) + 1):
            V.instance(f"W{i}_{k}", dome, M["bubble"], (i * SP, k * SP, 0), (0, 0, rnd.uniform(0, 6.3)), (1, 1, 1), root)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
    w = T.mesh_obj("WallFilm", bm, M["film"], smooth=False)
    w.parent = root
    w.scale = ((xr[1] - xr[0]) / 2 + 2, (zr[1] - zr[0]) / 2 + 2, 1)
    w.location = ((xr[0] + xr[1]) / 2, (zr[0] + zr[1]) / 2, -0.01)
    return root


def gem_mesh(name="Gem"):
    """Chunky brilliant-cut diamond: flat table, crown, pointed pavilion (8 sides)."""
    bm = bmesh.new()
    n = 8
    table = [bm.verts.new((0.5 * math.cos(2 * math.pi * i / n), 0.5 * math.sin(2 * math.pi * i / n), 0.45)) for i in range(n)]
    girdle = [bm.verts.new((math.cos(2 * math.pi * (i + 0.5) / n), math.sin(2 * math.pi * (i + 0.5) / n), 0.15)) for i in range(n)]
    tip = bm.verts.new((0, 0, -0.75))
    bm.faces.new(table)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((table[i], girdle[i], table[j]))
        bm.faces.new((girdle[i], girdle[j], table[j]))
        bm.faces.new((girdle[i], tip, girdle[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def sphere_bubble_mesh(name="BallBubble"):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.5)
    me = bpy.data.meshes.new(name)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    return me


def impact_ring(M, at, r, k=3.0, name="Ring"):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.05, major_segments=96, minor_segments=8,
                                     location=at)
    o = bpy.context.active_object
    o.name = name
    o.scale.z = 0.5
    o.data.materials.append(V.glow(name + "Mat", (255, 236, 170), k))
    return o


def extra_mats(M):
    M["ice"] = mat("Ice", (150, 225, 255), rough=0.02, transm=0.85, ior=1.6, coat=1.0,
                   emit=(120, 215, 255), emit_k=0.9, film=420)
    M["chrome"] = mat("Chrome", (235, 238, 245), rough=0.08, metal=1.0)
    M["red"] = mat("ShoeRed", (235, 35, 45), rough=0.25, coat=1.0)
    M["white"] = mat("ShoeWhite", (248, 248, 250), rough=0.3, coat=0.5)
    M["yellow"] = mat("ShoeYellow", (255, 200, 20), rough=0.25, coat=1.0)
    M["navy"] = mat("ShoeNavy", (30, 40, 90), rough=0.5)
    M["jeans"] = mat("Jeans", (50, 95, 200), rough=0.7)
    M["sack"] = mat("Sack", (140, 70, 235), rough=0.55, coat=0.2)
    M["sack2"] = mat("SackPatch", (255, 120, 190), rough=0.55)
    M["rope"] = mat("Rope", (255, 200, 60), rough=0.6)
    M["hole"] = mat("Hole", (40, 18, 70), rough=0.9)
    return M


# ---------------------------------------------------------------- 3: Spiky Boots stomp
def build_boot(M):
    """Chunky cartoon high-top sneaker. Local +X = toe, Z up, sole bottom at z = 0."""
    root = link(bpy.data.objects.new("Boot", None))
    # sole + yellow midsole stripe + toe bumper
    V.rbox("Sole", (3.2, 1.5, 0.42), (0.05, 0, 0.21), M["white"], 0.16, parent=root)
    V.rbox("Midsole", (3.26, 1.56, 0.12), (0.05, 0, 0.36), M["yellow"], 0.05, parent=root)
    # upper (one smooth blob)
    up, ell, caps = metaball("Upper", M["red"])
    up.parent = root
    ell((0.75, 0, 0.72), 0.62, 1.55, 1.12, 0.78)    # toe box
    ell((-0.35, 0, 0.95), 0.7, 1.35, 1.0, 1.0)      # heel/body
    caps((-0.6, 0, 1.0), (-0.55, 0, 2.15), 0.66)    # high-top shaft
    # white toe cap
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(1.05, 0, 0.55))
    tc = bpy.context.active_object
    tc.name = "ToeCap"
    tc.scale = (0.62, 0.7, 0.36)
    tc.data.materials.append(M["white"])
    tc.parent = root
    for f in tc.data.polygons:
        f.use_smooth = True
    # padded collar
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.16, major_segments=48, minor_segments=16,
                                     location=(-0.55, 0, 2.25))
    co = bpy.context.active_object
    co.name = "Collar"
    co.data.materials.append(M["white"])
    co.parent = root
    # laces across the tongue
    for n in range(4):
        x = 0.62 - n * 0.3
        z = 1.25 + n * 0.3
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.09, depth=0.9, location=(x, 0, z),
                                            rotation=(math.radians(90), 0, 0))
        la = bpy.context.active_object
        la.name = f"Lace{n}"
        la.data.materials.append(M["white"])
        la.parent = root
    # yellow star badge on both sides
    for side in (-1, 1):
        st = T.flat_poly(f"Star{side}", T.star_outline(5, 0.36, 0.16, rot=math.pi / 2), M["yellow"], depth=0.05)
        st.parent = root
        st.location = (-0.35, side * 0.8, 1.1)
        st.rotation_euler = (side * -math.pi / 2, 0, 0)
    # leg (jeans) going up out of frame
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.62, depth=6.0, location=(-0.55, 0, 5.2))
    lg = bpy.context.active_object
    lg.name = "Leg"
    lg.data.materials.append(M["jeans"])
    lg.parent = root
    # big chrome spikes under the sole
    for i, x in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        for y in ((-0.42, 0.42) if i % 2 == 0 else (-0.55, 0.0, 0.55)):
            sp = V.lathe_obj("Spike", [(0.0, 0.03), (0.18, 0.03), (0.16, -0.05), (0.0, -0.55)], M["chrome"], 24, root)
            sp.location = (x, y, 0.0)
    return root


def thumb_3():
    sc = T.reset()
    V.setup(sc)
    M = extra_mats(V.make_mats())
    M["popped"] = mat("PoppedDark", (60, 140, 235), rough=0.2, coat=0.8, transm=0.2, film=300)
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    boot_at = Vector((0.0, 0.0, 0.75))
    # camera at floor level
    tgt = Vector((-1.0, 0.9, 0.9))
    cam = T.camera(sc, (5.0, -7.6, 2.6), tgt, lens=34, roll=0)
    bpy.context.view_layer.update()
    # trail: a gently curving path of popped bubbles running back from the heel
    # laid out on screen: from the stomp up and to the left, back into the distance
    path = [Vector((0, 0))] + [V.floor_point(cam, u, v, z=0.0).to_2d() for u, v in
                               ((0.33, 0.5), (0.22, 0.58), (0.12, 0.63), (0.02, 0.66), (-0.1, 0.69))]

    def trail_d(x, y):
        q = Vector((x, y))
        best = 99
        for a, b in zip(path, path[1:]):
            ab = b - a
            t = max(0.0, min(1.0, (q - a).dot(ab) / ab.length_squared))
            best = min(best, (q - (a + ab * t)).length)
        return best

    def popped(x, y):
        r = math.hypot(x - boot_at.x, y - boot_at.y)
        if r < 2.25:
            return True                      # the bubbles under / round the stomp
        return trail_d(x, y) < 1.3 + 0.03 * math.hypot(x, y)
    bubble_floor(M, (-30, 14), (-8, 30), popped_fn=popped)
    wall = bubble_wall(M, 0, (-30, 30), (0, 22))
    look = Vector((-0.4 - 5.0, 0.6 + 7.6, 0)).normalized()     # camera's view direction on the floor
    wall.location = Vector((5.0, -7.6, 0)) + look * 40
    wall.rotation_euler = (math.radians(90), 0, math.atan2(look.y, look.x) - math.pi / 2)
    V.area("WallLight", tuple(Vector((5.0, -7.6, 8)) + look * 28), tuple(wall.location + Vector((0, 0, 6))), 6000, 20,
           (1.0, 0.97, 0.92))
    boot = build_boot(M)
    boot.location = boot_at
    boot.rotation_euler = (math.radians(-4), math.radians(8), math.radians(-118))   # toe toward the camera's left
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (cam.location - Vector((0.3, -0.5, 0.6))).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "0.3"))
    # light: warm key from front left, cool rim from behind, warm fill
    V.area("Key", (-3, -7, 7), (0, 0, 1), 1000, 6, (1.0, 0.92, 0.8))
    V.area("Rim", (2, 9, 5), (0, 0, 1), 1500, 6, (0.85, 0.92, 1.0))
    V.area("Fill", (8, -2, 3), (0, 0, 1), 400, 5, (1.0, 0.95, 0.9))
    # impact: rings, sparkle bursts round the sole, flying scraps + bits of film
    impact_ring(M, (0, 0, 0.3), 2.3, 1.6, "Ring1")
    impact_ring(M, (0, 0, 0.22), 3.0, 0.9, "Ring2")
    rnd = random.Random(7)
    for n in range(5):
        a = math.radians(-150 + n * 45 + rnd.uniform(-10, 10))
        p = Vector((2.1 * math.cos(a), 2.1 * math.sin(a), 0.45))
        V.spark_burst(M, p, cam, 0.8 + rnd.uniform(-0.1, 0.2), rays=6, halo_k=0.5, core=0.07, light=False)
    for n in range(16):
        a = math.radians(rnd.uniform(-200, 30))
        r = rnd.uniform(2.0, 3.6)
        p = Vector((r * math.cos(a), r * math.sin(a), rnd.uniform(0.5, 2.3)))
        m = M["clearbit"] if n % 3 == 0 else M["bits"][n % 6]
        V.instance(f"Fly{n}", T.scrap_mesh(300 + n), m, p, (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)),
                   (rnd.uniform(0.2, 0.3),) * 3)
    for n, (x, y, z, s) in enumerate(((2.6, -1.4, 1.7, 0.3), (-2.2, -1.9, 1.3, 0.25), (1.1, -2.7, 2.4, 0.22))):
        V.twinkle(M, Vector((x, y, z)), cam, s, f"Tw{n}")
    T.compositor(sc, bloom=0.8, threshold=1.6, vignette=0.15)
    T.render(sc, os.path.join(OUT, "thumb_3_stomp" + ("_fast" if FAST else "") + ".png"))


# ---------------------------------------------------------------- 4: the big haul
def build_sack(M):
    root = link(bpy.data.objects.new("Sack", None))
    prof = [(0.0, 3.05), (1.62, 3.05), (1.78, 3.2), (1.9, 3.12), (1.72, 2.95), (1.42, 2.75), (1.48, 2.55), (1.85, 2.2),
            (2.15, 1.7), (2.22, 1.2), (2.12, 0.65), (1.85, 0.25), (1.4, 0.04), (0.0, 0.0)]
    s = V.lathe_obj("SackBody", prof, M["sack"], 72, root)
    bm = bmesh.new()
    bm.from_mesh(s.data)
    rnd = random.Random(2)
    for v in bm.verts:   # lumpy, stuffed-full fabric
        a = math.atan2(v.co.y, v.co.x)
        bump = 0.07 * math.sin(5 * a + 1.3 * v.co.z) + 0.05 * math.sin(9 * a - 2.1 * v.co.z)
        k = max(0.0, min(1.0, v.co.z / 0.5)) * max(0.0, min(1.0, (2.9 - v.co.z) / 0.4))
        r = math.hypot(v.co.x, v.co.y)
        if r > 1e-4:
            v.co.x += v.co.x / r * bump * k
            v.co.y += v.co.y / r * bump * k
    bm.to_mesh(s.data)
    bm.free()
    # rope tie round the neck
    bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.12, major_segments=64, minor_segments=12,
                                     location=(0, 0, 2.68))
    rp = bpy.context.active_object
    rp.name = "Rope"
    rp.data.materials.append(M["rope"])
    rp.parent = root
    # pink patch with a ripped seam bursting open on the front (-Y)
    pa = V.rbox("Patch", (0.9, 0.12, 0.75), (-0.95, -1.98, 1.65), M["sack2"], 0.05, parent=root)
    pa.rotation_euler = (math.radians(-6), 0, math.radians(-25))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0.75, -2.08, 1.05))
    h = bpy.context.active_object
    h.name = "Rip"
    h.scale = (0.42, 0.12, 0.26)
    h.rotation_euler = (0, math.radians(-25), math.radians(20))
    h.data.materials.append(M["hole"])
    h.parent = root
    return root


def thumb_4():
    sc = T.reset()
    V.setup(sc)
    M = extra_mats(V.make_mats())
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    sack_r = 2.3
    bubble_floor(M, (-16, 16), (-10, 9), popped_fn=lambda x, y: random.Random(int(x * 7 + y * 13)).random() < 0.08,
                 gone_fn=lambda x, y: math.hypot(x, y) < sack_r)
    bubble_wall(M, 9.5, (-30, 30), (0, 18))
    build_sack(M)
    rnd = random.Random(5)
    # mound of scraps on top of the sack + some poking out of the rip
    for n in range(230):
        a = rnd.uniform(0, 2 * math.pi)
        r = 1.8 * math.sqrt(rnd.random())
        z = 3.0 + 1.5 * (1 - (r / 1.85) ** 2) * rnd.uniform(0.6, 1.0)
        V.instance(f"Pile{n}", T.scrap_mesh(2000 + n % 40), M["bits"][n % 6], (r * math.cos(a), r * math.sin(a), z),
                   (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), (rnd.uniform(0.3, 0.42),) * 3)
    for n in range(40):   # scraps tumbling over the rim and down the front
        a = math.radians(rnd.uniform(-150, -30))
        z = rnd.uniform(2.2, 3.2)
        r = 2.05 if z < 2.6 else 1.95
        V.instance(f"Drape{n}", T.scrap_mesh(2050 + n), M["bits"][(n + 3) % 6], (r * math.cos(a), r * math.sin(a), z),
                   (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), (rnd.uniform(0.28, 0.36),) * 3)
    for n in range(8):
        p = Vector((0.75, -2.15, 1.05)) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.25, 0.05), rnd.uniform(-0.2, 0.2)))
        V.instance(f"Rip{n}", T.scrap_mesh(2100 + n), M["bits"][(n + 2) % 6], p,
                   (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), (0.27,) * 3)
    # the glowing rainbow bubble on top of the heap
    rb = V.instance("RainbowBubble", sphere_bubble_mesh(), M["rainbow"], (0.1, -0.45, 4.85), (0, 0, 0), (1.35, 1.35, 1.25))
    # icy diamond scraps
    gm = gem_mesh()
    for n, (p, s, rot) in enumerate((((-1.15, -1.0, 4.15), 0.6, (0.4, 0.2, 0.3)), ((1.25, -1.2, 3.9), 0.52, (-0.5, 0.3, 1.0)),
                                     ((-2.2, -3.0, 0.55), 0.55, (0.9, 0.0, 0.2)), ((2.7, -2.6, 0.5), 0.5, (1.2, 0.3, 2.0)))):
        V.instance(f"Gem{n}", gm, M["ice"], p, rot, (s,) * 3)
    # gold coins: a spill on the floor in front + a few tumbling down the side
    cm = T.coin_mesh()
    for n in range(26):
        a = math.radians(rnd.uniform(-160, -20))
        r = rnd.uniform(2.3, 4.2)
        p = (r * math.cos(a), r * math.sin(a), 0.42 + rnd.uniform(0, 0.12))
        V.instance(f"Coin{n}", cm, M["coin"], p, (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), 0), (1.25,) * 3)
    for n, (p, rot) in enumerate((((-1.95, -1.4, 2.4), (1.1, 0.3, 0.5)), ((2.15, -1.2, 1.9), (0.6, -0.8, 1.0)),
                                  ((-0.6, -2.4, 3.1), (1.4, 0.1, 0.2)), ((1.35, -2.05, 3.4), (0.3, 1.0, 0.4)))):
        V.instance(f"FallCoin{n}", cm, M["coin"], p, rot, (1.3,) * 3)
    for n in range(10):   # a few scraps spilt on the floor too
        a = math.radians(rnd.uniform(-170, -10))
        r = rnd.uniform(2.4, 4.5)
        V.instance(f"Spill{n}", T.scrap_mesh(2200 + n), M["bits"][n % 6], (r * math.cos(a), r * math.sin(a), 0.5),
                   (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), rnd.uniform(0, 6)), (0.26,) * 3)
    # glow round the rainbow bubble + twinkles
    tgt = Vector((0.0, 0.0, 3.0))
    cam = T.camera(sc, (3.6, -12.6, 2.6), tgt, lens=37, roll=0)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = (cam.location - Vector((0, -1.8, 2.2))).length
    cam.data.dof.aperture_fstop = float(os.environ.get("FSTOP", "0.12"))
    bpy.context.view_layer.update()
    V.spark_burst(M, rb.location + (cam.location - rb.location).normalized() * 0.8, cam, 1.7, strong=True, halo_k=1.4,
                  core=0.0, ring=0.78)
    for n, (x, y, z, s) in enumerate(((-2.4, -1.2, 4.6, 0.3), (2.5, -1.0, 4.1, 0.26), (-1.2, -2.6, 0.9, 0.22),
                                      (1.9, -3.2, 0.8, 0.2), (-0.9, -0.6, 3.95, 0.18))):
        V.twinkle(M, Vector((x, y, z)), cam, s, f"Tw{n}")
    V.area("Key", (-5, -8, 9), (0, 0, 2), 1800, 7, (1.0, 0.92, 0.8))
    V.area("Rim", (4, 6, 7), (0, 0, 2), 1500, 6, (0.85, 0.92, 1.0))
    V.area("Fill", (8, -6, 3), (0, 0, 2), 500, 6, (1.0, 0.95, 0.9))
    T.compositor(sc, bloom=0.8, threshold=1.6, vignette=0.15)
    T.render(sc, os.path.join(OUT, "thumb_4_haul" + ("_fast" if FAST else "") + ".png"))


if __name__ == "__main__":
    if "3" in ONLY:
        thumb_3()
    if "4" in ONLY:
        thumb_4()
