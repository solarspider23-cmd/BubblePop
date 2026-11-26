# Batch A3 (docs/art_plan.md): the low-detail gumball and the two neat gumball piles.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_machine_build_gumball_lo.py
#
# Outputs (art/hub_machine/)
#   Hub_GumballLo.fbx          GumballLo (300 triangles, 1 stud across, centred, SAME UV layout as
#                              art/gumball/Gumball.fbx so it reuses the Gumball_* maps),
#                              GumballCore_Globe, GumballCore_Jar (dull dark-pink fillers)
#   Hub_GumballLo.blend, Hub_GumballLo.bounds.json
#   GumballPile_Globe.json     ball centres that do not overlap, measured from the globe's centre
#   GumballPile_Jar.json       the same for the jar, measured from the centre of the jar's floor
# Previews (art/previews/): hub_machine_gumballlo_beauty / _flat / _thumb / _turn / _colours .png
#
# The piles are settled with a small physics loop (balls dropped in, pushed apart until none
# overlap), then only the balls you can see from outside are kept; the core hides the gaps.

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_machine_common as C  # noqa: E402

N = 5            # quads per cube-face edge -> 6*N*N*2 = 300 triangles
TEX = 1024       # the existing gumball maps (for the tile padding)
CORE_HEX = "#8F2B58"

scene = C.reset()


# ------------------------------------------------------------------ low-detail gumball
def build_ball():
    """Same cube-sphere and 3 x 2 UV tiles as build_gumball.py, with fewer divisions."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    faces = [
        ((0, 1), (1, 1), (2, 1), (0, 0)), ((0, -1), (1, -1), (2, 1), (1, 0)),
        ((1, 1), (0, -1), (2, 1), (2, 0)), ((1, -1), (0, 1), (2, 1), (0, 1)),
        ((2, 1), (0, 1), (1, 1), (1, 1)), ((2, -1), (0, 1), (1, -1), (2, 1)),
    ]
    pad = 8.0 / TEX
    tw, th = 1.0 / 3.0, 1.0 / 2.0
    for (na, ns), (ua, us), (va, vs), (col, row) in faces:
        verts, st = {}, {}
        for i in range(N + 1):
            for j in range(N + 1):
                p = [0.0, 0.0, 0.0]
                p[na] = ns
                p[ua] = us * math.tan((-1 + 2 * i / N) * math.pi / 4)
                p[va] = vs * math.tan((-1 + 2 * j / N) * math.pi / 4)
                verts[i, j] = bm.verts.new(Vector(p).normalized() * 0.5)
                st[i, j] = (i / N, j / N)
        for i in range(N):
            for j in range(N):
                ks = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                f = bm.faces.new([verts[k] for k in ks])
                for loop, k in zip(f.loops, ks):
                    s, t = st[k]
                    loop[uv].uv = (col * tw + pad + s * (tw - 2 * pad), row * th + pad + t * (th - 2 * pad))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.dot(f.calc_center_median()) < 0:
            f.normal_flip()
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY")
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("GumballLo")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("GumballLo", me)
    scene.collection.objects.link(ob)
    return ob


ball = build_ball()


# ------------------------------------------------------------------ pile physics
def push_apart(pos, d):
    diff = pos[:, None, :] - pos[None, :, :]
    dist = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dist, 1e9)
    ov = d - dist
    hit = ov > 0
    if not hit.any():
        return pos, 0.0
    corr = (np.where(hit, ov * 0.5, 0.0) / np.maximum(dist, 1e-6))[..., None] * diff
    cnt = np.maximum(hit.sum(axis=1), 1)[:, None]
    return pos + corr.sum(axis=1) / cnt * 1.2, float(ov.max())


def settle(n, d, clamp, drop, seed):
    """Drop n balls of diameter d a few at a time; returns centres (Blender axes, Z up)."""
    rng = np.random.default_rng(seed)
    pos = np.zeros((0, 3))
    vel = np.zeros((0, 3))
    dt, g = 1 / 60, -90.0
    step = 0
    while True:
        if len(pos) < n and step % 12 == 0:
            k = min(3, n - len(pos))
            pos = np.vstack([pos, drop(rng, k)])
            vel = np.vstack([vel, np.zeros((k, 3))])
        elif len(pos) >= n:
            step_left = locals().get("step_left", 900) - 1
            if step_left <= 0:
                break
        prev = pos.copy()
        vel[:, 2] += g * dt
        pos = pos + vel * dt
        for _ in range(6):
            pos, _ov = push_apart(pos, d * 1.004)
            pos = clamp(pos)
        vel = (pos - prev) / dt * 0.90
        step += 1
    # last pass with no gravity: make sure nothing overlaps at all
    for it in range(60000):
        pos, ov = push_apart(pos, d * 1.003)
        pos = clamp(pos)
        if ov <= d * 0.0025:
            break
        if it % 50 == 49:  # a ring of balls jammed flat against the wall: nudge them so one pops up
            pos = clamp(pos + rng.normal(0, d * 0.004, pos.shape))
    return pos


def min_gap(pos):
    diff = pos[:, None, :] - pos[None, :, :]
    dist = np.linalg.norm(diff, axis=2)
    np.fill_diagonal(dist, 1e9)
    return float(dist.min())


def pick_colours(pos, d, seed):
    rng = np.random.default_rng(seed)
    cols = [-1] * len(pos)
    for i in np.argsort(pos[:, 2]):
        near = {cols[j] for j in range(len(pos)) if cols[j] >= 0 and np.linalg.norm(pos[i] - pos[j]) < d * 1.2}
        free = [c for c in range(8) if c not in near] or list(range(8))
        cols[i] = int(rng.choice(free))
    return cols


def covered(pos, d, i):
    """True if another ball sits on top of ball i (so it cannot be seen from above)."""
    dz = pos[:, 2] - pos[i, 2]
    dh = np.linalg.norm(pos[:, :2] - pos[i, :2], axis=1)
    return bool(((dz > 0.35 * d) & (dh < 0.62 * d)).any())


# --- globe: balls 3.8 across in a sphere of radius 14, two thirds full
D, R = 3.8, 14.0
RC = R - D / 2 - 0.08          # how far a centre can be from the middle
LEVEL = -R + 2 * R * 2 / 3     # top of the pile, measured from the globe's centre
CUP = -9.4                     # the machine's collar hides everything below this height


def globe_clamp(p):
    r = np.linalg.norm(p, axis=1)
    k = np.where(r > RC, RC / np.maximum(r, 1e-9), 1.0)
    return p * k[:, None]


def globe_drop(rng, k):
    a = rng.uniform(0, 2 * math.pi, k)
    rr = rng.uniform(0, 7.5, k)
    return np.stack([rr * np.cos(a), rr * np.sin(a), rng.uniform(7.0, 9.0, k)], axis=1)


def top_of(pos, d):
    tops = np.sort(pos[:, 2])[-max(3, len(pos) // 12):]
    return float(tops.mean() + d / 2)


n = 150
best = None
for _ in range(8):
    pos = settle(n, D, globe_clamp, globe_drop, seed=5)
    lvl = top_of(pos, D)
    print("[globe] %d balls -> pile top %.2f (want %.2f)" % (n, lvl, LEVEL))
    if best is None or abs(lvl - LEVEL) < abs(best[1] - LEVEL):
        best = (pos, lvl, n)
    if abs(lvl - LEVEL) < 0.7:
        break
    n += int(round((LEVEL - lvl) * 9))
pos, lvl, n = best
assert min_gap(pos) >= D - 1e-3, min_gap(pos)
assert np.linalg.norm(pos, axis=1).max() <= R - D / 2 + 1e-6
rad = np.linalg.norm(pos, axis=1)
keep = [i for i in range(len(pos))
        if pos[i, 2] + D / 2 > CUP + 0.1 and (rad[i] > RC - 0.5 * D or not covered(pos, D, i))]
globe = pos[keep]
globe_all = len(pos)
print("[globe] settled %d, kept %d you can see; smallest gap between centres %.3f (balls are %.1f)"
      % (globe_all, len(globe), min_gap(globe), D))

# --- jar: balls 1.6 across in a cylinder 5.8 across and 7 high, three quarters full
JD, JR, JH = 1.6, 2.9, 7.0
JRC = JR - JD / 2 - 0.04
JLEVEL = JH * 0.75


def jar_clamp(p):
    r = np.linalg.norm(p[:, :2], axis=1)
    k = np.where(r > JRC, JRC / np.maximum(r, 1e-9), 1.0)
    q = p.copy()
    q[:, :2] *= k[:, None]
    q[:, 2] = np.maximum(q[:, 2], JD / 2 + 0.02)
    return q


def jar_drop(rng, k):
    a = rng.uniform(0, 2 * math.pi, k)
    rr = rng.uniform(0, 1.6, k)
    return np.stack([rr * np.cos(a), rr * np.sin(a), rng.uniform(8.0, 9.0, k)], axis=1)


jn = 40
jbest = None
for _ in range(8):
    jpos = settle(jn, JD, jar_clamp, jar_drop, seed=11)
    jl = top_of(jpos, JD)
    print("[jar] %d balls -> pile top %.2f (want %.2f)" % (jn, jl, JLEVEL))
    if jbest is None or abs(jl - JLEVEL) < abs(jbest[1] - JLEVEL):
        jbest = (jpos, jl, jn)
    if abs(jl - JLEVEL) < 0.3:
        break
    jn += int(round((JLEVEL - jl) * 8))
jpos, jl, jn = jbest
assert min_gap(jpos) >= JD - 1e-3, min_gap(jpos)
jrad = np.linalg.norm(jpos[:, :2], axis=1)
jkeep = [i for i in range(len(jpos)) if jrad[i] > JRC - 0.5 * JD or not covered(jpos, JD, i)]
jar = jpos[jkeep]
print("[jar] settled %d, kept %d; smallest gap %.3f (balls are %.1f)" % (len(jpos), len(jar), min_gap(jar), JD))


# ------------------------------------------------------------------ cores
def lumpy(seed, amount):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 6)

    def shape(theta, r, z):
        k = 1 + amount * (math.sin(3 * theta + ph[0] + z * 0.9) * 0.5 + math.sin(5 * theta + ph[1] - z * 1.7) * 0.5)
        return Vector((r * k * math.cos(theta), r * k * math.sin(theta), z))
    return shape


b = C.Build()
b.use("core", obj=0)
# globe core: a ball that stays under the outer layer, flat-topped under the top layer
core_r = RC - 0.80 * D
core_top = float(np.sort(globe[:, 2])[-max(3, len(globe) // 6):].mean()) - 0.62 * D
prof = []
z0 = max(-core_r * 0.98, CUP - 1.0)
for i in range(5):
    z = z0 + (core_top - 1.2 - z0) * i / 4
    prof.append((math.sqrt(max(core_r ** 2 - z ** 2, 0.3)), z))
rt = math.sqrt(max(core_r ** 2 - core_top ** 2, 1.0))
prof += [(rt - 0.5, core_top), (0.6, core_top + 0.25)]
b.lathe(prof, segs=13, shape=lumpy(3, 0.035), cap_end=True, cap_start=True)
b.use("core", obj=1)
jcore_r = JRC - 0.80 * JD
jcore_top = float(np.sort(jar[:, 2])[-max(3, len(jar) // 6):].mean()) - 0.62 * JD
b.lathe([(jcore_r, 0.05), (jcore_r, jcore_top * 0.5), (jcore_r, jcore_top - 0.3), (jcore_r - 0.3, jcore_top), (0.2, jcore_top + 0.1)],
        segs=12, shape=lumpy(4, 0.05), cap_end=True, cap_start=True)
cores = b.finalize({0: "GumballCore_Globe", 1: "GumballCore_Jar"}, scene, pack=False)
core_mat = C.plain_material("GumballCore", CORE_HEX, 0.85)
for ob in cores.values():
    C.single_material(ob, core_mat)
core_globe, core_jar = cores["GumballCore_Globe"], cores["GumballCore_Jar"]

# ------------------------------------------------------------------ files
fin = C.textured_material("Gumball", C.gumball_paths())
fin_flat = C.textured_material("GumballFlat", C.gumball_paths(), flat=True)
ball.data.materials.append(fin)

tris = {o.name: C.tri_count(o) for o in (ball, core_globe, core_jar)}
print("TRIANGLES", tris)
assert 280 <= tris["GumballLo"] <= 320 and tris["GumballCore_Globe"] < 200 and tris["GumballCore_Jar"] < 200

# exported exactly like art/gumball/Gumball.fbx (no half turn: it is a ball, and the cores are round)
C.export_fbx([ball, core_globe, core_jar], os.path.join(C.OUT, "Hub_GumballLo.fbx"), half_turn=False)


def pile_json(path, pts, d, cols, note, core_ob, extra):
    C.write_json(path, dict({
        "note": note,
        "axes": "Roblox: X right, Y up, Z = -Blender Y",
        "diameter": d,
        "count": len(pts),
        "min_centre_distance": round(min_gap(pts), 4),
        "positions": [C.rbx(p) for p in pts],
        "colors": cols,
        "color_note": "index 0-7 into the 8 gumball colours (red, blue, amber, green, pink, orange, purple, white); touching balls never share one",
        "core": dict(C.roblox_box(core_ob), mesh=core_ob.name, color_hex=CORE_HEX, color=C.rgb255(CORE_HEX),
                     material="SmoothPlastic", note="place at the same origin as the positions"),
    }, **extra))


pile_json(os.path.join(C.OUT, "GumballPile_Globe.json"), globe, D, pick_colours(globe, D, 1),
          "Gumball centres inside the machine's globe, measured from the globe's centre (hub height 29). "
          "Only the balls you can see from outside; GumballCore_Globe fills the middle.",
          core_globe, {"container": "sphere radius 14", "settled": globe_all,
                       "pile_top": round(lvl, 2), "hidden_below": CUP})
pile_json(os.path.join(C.OUT, "GumballPile_Jar.json"), jar, JD, pick_colours(jar, JD, 2),
          "Gumball centres inside the jar, measured from the centre of the jar's floor. GumballCore_Jar fills the middle.",
          core_jar, {"container": "cylinder 5.8 across, 7 high", "settled": len(jpos), "pile_top": round(jl, 2)})

C.write_json(os.path.join(C.OUT, "Hub_GumballLo.bounds.json"), {
    "GumballLo": dict(C.roblox_box(ball), material="SmoothPlastic + the existing Gumball SurfaceAppearance (tinted)",
                      note="1 stud across, centred; same UV layout as art/gumball/Gumball.fbx; scale to 3.8 (globe) or 1.6 (jar)"),
    "GumballCore_Globe": dict(C.roblox_box(core_globe), color=C.rgb255(CORE_HEX), material="SmoothPlastic",
                              note="origin = globe centre; no texture; no shadow"),
    "GumballCore_Jar": dict(C.roblox_box(core_jar), color=C.rgb255(CORE_HEX), material="SmoothPlastic",
                            note="origin = centre of the jar's floor; no texture; no shadow"),
})

# ------------------------------------------------------------------ previews
# the pile inside a glass ball, with the 8 colours
ball.hide_render = True
core_globe.hide_render = True
core_jar.hide_render = True
gb = bmesh.new()
bmesh.ops.create_uvsphere(gb, u_segments=64, v_segments=32, radius=R)
for f in gb.faces:
    f.smooth = True
gm = bpy.data.meshes.new("PreviewGlass")
gb.to_mesh(gm)
gb.free()
gm.materials.append(C.glass_material())
glass = bpy.data.objects.new("PreviewGlass", gm)
glass.location = (0, 0, R)
scene.collection.objects.link(glass)

GJ = os.path.join(C.OUT, "GumballPile_Globe.json")
JJ = os.path.join(C.OUT, "GumballPile_Jar.json")
state = {"pile": C.add_pile(scene, GJ, ball.data, (0, 0, R), core_mesh=core_globe.data)}
JAR_AT = (22, 4, 0)
state["jar"] = C.add_pile(scene, JJ, ball.data, JAR_AT, core_mesh=core_jar.data)
jb = bmesh.new()
bmesh.ops.create_cone(jb, cap_ends=True, segments=40, radius1=JR, radius2=JR, depth=JH)
bmesh.ops.translate(jb, vec=(0, 0, JH / 2), verts=jb.verts)
jm = bpy.data.meshes.new("PreviewJar")
jb.to_mesh(jm)
jb.free()
for p in jm.polygons:
    p.use_smooth = len(p.vertices) == 4
jm.materials.append(C.glass_material("JarGlass"))
jglass = bpy.data.objects.new("PreviewJar", jm)
jglass.location = JAR_AT
scene.collection.objects.link(jglass)


def set_flat(on):
    for o in state["pile"] + state["jar"]:
        if o.name.startswith("PreviewGum"):
            m = o.data.materials[0]
            want = m.name.rstrip("F") + ("F" if on else "")
            if want not in bpy.data.materials:
                C.textured_material(want, C.gumball_paths(), flat=on, tint=C.GUMBALL_HEX[int(m.name.rstrip("F")[-1])])
            o.data.materials[0] = bpy.data.materials[want]


st = C.standard_previews(scene, "hub_machine_gumballlo", (-R, -R, 0), (JAR_AT[0] + JR, R, 2 * R), set_flat,
                         view=(0.35, 0.86, 0.3), player=(-18, 6, 0), samples=64)

# colour row: the 8 tints on the low-detail ball, with the full-detail gumball behind for comparison
for o in state["pile"] + state["jar"] + [glass, jglass]:
    o.hide_render = True
for o in scene.objects:
    if o.name == "PreviewPlayer":
        o.hide_render = True
row = []
hi_path = os.path.join(C.GUMBALL, "Gumball.blend")
hi_mesh = None
if os.path.exists(hi_path):
    with bpy.data.libraries.load(hi_path) as (src, dst):
        dst.meshes = [m for m in src.meshes if m == "Gumball"]
    hi_mesh = dst.meshes[0] if dst.meshes else None
for i, h in enumerate(C.GUMBALL_HEX):
    for k, mesh in enumerate((ball.data, hi_mesh)):
        if mesh is None:
            continue
        me = mesh.copy()
        me.materials.clear()
        me.materials.append(C.textured_material("Row%d_%d" % (i, k), C.gumball_paths(), tint=h))
        ob = bpy.data.objects.new("PreviewRow", me)
        ob.location = ((i - 3.5) * 1.25, -k * 1.5, 0.5)
        scene.collection.objects.link(ob)
        row.append(ob)
C.frame(scene, st["cam"], (0.0, 0.8, 0.5), (-5, -2, 0), (5, 0.5, 1), 60, (1280, 560))
C.render(scene, os.path.join(C.PREVIEWS, "hub_machine_gumballlo_colours.png"))

ball.hide_render = core_globe.hide_render = core_jar.hide_render = False
C.save_blend(os.path.join(C.OUT, "Hub_GumballLo.blend"), [ball, core_globe, core_jar])
print("GUMBALL LO done")
