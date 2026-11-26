# Shared helpers for the CLEAN POP PLAZA lobby theme (hub_clean_*.py).
# Not run by itself. Each hub_clean_<asset>.py does `import hub_clean_common as K` and uses
# K.P (the Batch B plaza helpers: MeshBuilder, zone materials, baking, export, previews) plus the
# extra shapes and the clean palette defined here.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_<asset>.py
#   CLEAN_QUICK=1 for fast low-sample test renders.
#
# Rules (docs/art_plan.md): 1 unit = 1 stud, Z up, model stands on the origin, front = +Y,
# kit.py-style half-turn export, CPU renders only, 64 samples at most, one Blender at a time.

import math
import os
import sys

if os.environ.get("CLEAN_QUICK") == "1":
    os.environ["PLAZA_QUICK"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_plaza_common as P  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = P.ROOT
OUT = os.path.join(ROOT, "art", "hub_clean")
PREV = os.path.join(ROOT, "art", "previews")
os.makedirs(OUT, exist_ok=True)
# point the shared helpers at this theme's folders
P.OUT = OUT
P.TMP = os.path.join(OUT, "_tmp")
QUICK = P.QUICK

# ------------------------------------------------------------------ Clean Pop Plaza palette (sRGB hex)
PAL = {
    "white": "#FAFBFD",   # soft white (main)
    "cream": "#FFF4E6",   # warm cream
    "grey": "#DCE2EC",    # light cool grey (never pure grey)
    "stone": "#E9E6E4",   # pale warm stone (island)
    "stone2": "#D5D8E2",  # deeper pale stone
    "blue": "#2E9BFF",    # HERO accent: bubble blue
    "bluedeep": "#1B6FD8",
    "sky": "#A8D8FF",
    "mint": "#A6EBD2",
    "lilac": "#CDBDF8",
    "peach": "#FFCDB0",
    "slate": "#4A5E8A",   # darkest allowed (windows, slots)
    "tint": "#F6F4F3",    # neutral for tint meshes
    "glow": "#1464C8",    # Neon: dark saturated bubble blue
}
# the 4 play pads (pastel, a touch stronger than the trim pastels so they read on a phone)
PAD_COLOURS = [("Sky", "#6FBFFF"), ("Mint", "#6FDDB6"), ("Lilac", "#B49CF5"), ("Peach", "#FFAA80")]
PAD_GLOWS = {"Sky": "#1464C8", "Mint": "#0F9670", "Lilac": "#6440D2", "Peach": "#D25A28"}
BOOTH_COLOURS = [("Sky", "#6FBFFF"), ("Mint", "#6FDDB6"), ("Lilac", "#B49CF5")]
TREE_COLOURS = [("Sky", "#8CCBFF"), ("Mint", "#8FE6C6"), ("Lilac", "#C3AEF7"), ("Peach", "#FFBE9C"), ("White", "#FAFBFD")]

lin = P.lin
rgb255 = P.rgb255


FAST = os.environ.get("CLEAN_FULL") != "1"   # default: beauty preview only (set CLEAN_FULL=1 for thumb, flat and turnaround too)


def reset():
    sc = P.reset()
    sc.render.threads_mode = "AUTO"
    if os.environ.get("CLEAN_CPU") == "1":
        sc.cycles.device = "CPU"
        return sc
    # GPU (Cycles Metal), as the lead asked once this was the only Blender helper; one Blender at a time
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        sc.cycles.device = "GPU"
    except Exception as e:  # noqa: BLE001
        print("GPU not available, using CPU:", e)
        sc.cycles.device = "CPU"
    return sc


def _fast_previews(prefix, objs, block_at, beauty_dir=(0.6, 1.0, 0.55), lens=50, turn_elev=0.28, aim_z=None):
    """Beauty shot only (the lead asked to skip thumbnails, colour-only and turnarounds for speed)."""
    block = P.player_block(block_at)
    lo, hi = P.world_bounds(objs + [block])
    c = (lo + hi) / 2
    if aim_z is not None:
        c.z = aim_z
    P.shoot(os.path.join(PREV, prefix + "_beauty.png"), c, beauty_dir, P.fit_dist((hi - lo).length / 2, lens, margin=1.02), lens)
    bpy.data.objects.remove(block)


_full_previews = P.standard_previews
if FAST:
    P.standard_previews = _fast_previews


# ------------------------------------------------------------------ extra shapes on a P.MeshBuilder
def arc_pts(cx, cy, r, a0, a1, n):
    """Points on an arc (degrees), n segments, in profile space (d, w)."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def pill_profile(d, w0, w1, bv, n=3, top=True, bottom=True):
    """Side profile of a rounded slab for lathe(): offset d, from w0 to w1, edges rounded by bv."""
    pts = []
    if bottom:
        pts += arc_pts(d - bv, w0 + bv, bv, -90, 0, n)
    else:
        pts.append((d, w0))
    if top:
        pts += arc_pts(d - bv, w1 - bv, bv, 0, 90, n)
    else:
        pts.append((d, w1))
    return pts


def sphere(mb, c, r, segs=24, rings=12, zone="body", sz=1.0, a0=0.0, a1=180.0, cap_first=False, cap_last=False):
    """UV sphere (or a band of one between polar angles a0..a1, measured from the bottom)."""
    prof = []
    for i in range(rings + 1):
        a = math.radians(a0 + (a1 - a0) * i / rings)
        d = r * math.sin(a)
        prof.append((0.0 if d < 1e-5 else d, -r * math.cos(a) * sz))
    mb.lathe(prof, lambda d: P.circle2d(d, segs), P.frame(c), zone=zone, cap_first=cap_first, cap_last=cap_last)


def torus(mb, c, R, r, segs=32, tsegs=8, zone="body", fr=None, squash=1.0, a_off=0.0):
    prof = [(R + r * math.cos(a_off + 2 * math.pi * i / tsegs), r * squash * math.sin(a_off + 2 * math.pi * i / tsegs))
            for i in range(tsegs + 1)]
    prof[-1] = prof[0]
    mb.lathe(prof, lambda d: P.circle2d(d, segs), fr or P.frame(c), zone=zone)


def loft(mb, rings, zone="body", zones=None, closed=True, cap_first=False, cap_last=False, smooth=True):
    """Skin a list of explicit rings (each a list of 3D points, same count)."""
    rows = [[mb.bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(rows[0])
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        z = zones[i] if zones else zone
        for j in range(n if closed else n - 1):
            k = (j + 1) % n
            mb.face((a[j], a[k], b[k], b[j]), z, smooth)
    if cap_first:
        mb.face(rows[0], zones[0] if zones else zone, smooth)
    if cap_last:
        mb.face(rows[-1], zones[-1] if zones else zone, smooth)
    return rows


def rbox(mb, half, c, R, bv, zone="body", k=4, n=3, fr=None):
    """Rounded box: half = (hx, hy, hz) outer half sizes, corner radius R (plan view), edge bevel bv.
    Stands with its centre at c (or in frame fr: ring plane = u,v ; height = w)."""
    hx, hy, hz = half
    a, b = hx - R, hy - R
    prof = pill_profile(R, -hz, hz, bv, n)
    mb.lathe(prof, lambda d: P.rrect2d(a, b, d, k), fr or P.frame(c), zone=zone, cap_first=True, cap_last=True)


def shine_patch(mb, centre, r, az0, el0, length, width, tilt_deg=-24, zone="shine", n=5):
    """The house 'shine': a thin one-sided white pill wrapped on a sphere (centre, radius r).
    az0 = angle from +Y towards +X, el0 = elevation (radians)."""
    h = (length - width) / 2
    pts = [(width / 2 * math.cos(math.pi * i / n), h + width / 2 * math.sin(math.pi * i / n)) for i in range(n + 1)]
    pts += [(-x, -y) for x, y in pts]
    t = math.radians(tilt_deg)
    outline = [(x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)) for x, y in pts]
    c = Vector(centre)

    def pt(u, v):
        el = el0 + v / r
        az = az0 + u / (r * math.cos(el0))
        return c + Vector((r * math.cos(el) * math.sin(az), r * math.cos(el) * math.cos(az), r * math.sin(el)))
    rows = [[mb.bm.verts.new(pt(u * s, v * s)) for u, v in outline] for s in (1.0, 0.5)]
    m = len(outline)
    for j in range(m):
        k = (j + 1) % m
        mb.face((rows[0][k], rows[0][j], rows[1][j], rows[1][k]), zone)
    cv = mb.bm.verts.new(pt(0, 0))
    for j in range(m):
        mb.face((rows[1][(j + 1) % m], rows[1][j], cv), zone)


def face_out(ob, centre):
    """Flip a one-sided decal mesh if it faces towards centre."""
    c = Vector(centre)
    if sum(p.normal.dot(p.center - c) for p in ob.data.polygons) < 0:
        ob.data.flip_normals()


# ------------------------------------------------------------------ colour helpers for zone materials
def vgrad(lo_hex, hi_hex, z0, z1, axis="z"):
    """Colour function: soft gradient from lo (at z0) to hi (at z1) along an object axis."""
    def fn(nb):
        t = nb.smooth(getattr(nb, axis), z0, z1)
        return nb.mixc(lin(lo_hex), lin(hi_hex), t)
    return fn


def zone(name, color, rough=0.25, height=None, **kw):
    kw.setdefault("ao", 0.2)
    kw.setdefault("grad", 0.04)
    return P.zone_material(name, color, rough, height, **kw)


def glass_material(name="GlassPreview", tint=(0.80, 0.92, 1.0), lo=0.06, hi=0.7):
    """Stand-in for Roblox Glass (about 0.5 transparency): see-through with a soft reflection."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    tr = nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = tuple(tint) + (1,)
    gl = nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.04
    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.25
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    links.new(lw.outputs["Facing"], mr.inputs["Value"])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mr.outputs["Result"], mix.inputs["Fac"])
    links.new(tr.outputs["BSDF"], mix.inputs[1])
    links.new(gl.outputs["BSDF"], mix.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def set_mat(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def studio(center, radius):
    """Soft showroom light on a calm mid blue-grey floor (white models need a darker backdrop)."""
    fl = P.studio(center, radius, floor_col=(0.36, 0.42, 0.52))
    fl.scale = (8, 8, 1)
    # the camera sees a flat backdrop colour close to the far floor (soft horizon); lighting keeps the studio sky
    nt = bpy.context.scene.world.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    sky = out.inputs[0].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeBackground")
    cam.inputs["Color"].default_value = (0.40, 0.47, 0.62, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(sky, mix.inputs[1])
    nt.links.new(cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    sc = bpy.context.scene
    sc.view_settings.view_transform = "Standard"     # true palette colours (AgX washes the pastels out)
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.55
    return fl


def backface_report(name, objs):
    lo, hi = P.world_bounds(objs)
    c = (lo + hi) / 2
    r = (hi - lo).length / 2
    bad, hits = P.count_backfaces_from(objs, P.ray_grid(c, r, n=16))
    print(f"[{name}] backface check: {bad} bad of {hits} ray hits {'OK' if bad == 0 else 'CHECK'}")
    return bad


def copies(objs, at, mats=None):
    """Linked-data copies of objs at a location (for preview line-ups); mats = {name: material}."""
    out = []
    for src in objs:
        ob = src.copy()
        ob.data = src.data.copy()
        if mats and src.name in mats:
            set_mat(ob, mats[src.name])
        ob.location = at
        ob.hide_render = False
        bpy.context.scene.collection.objects.link(ob)
        out.append(ob)
    return out


def tex_names(set_name):
    return {"color": f"{set_name}_color.png", "normal": f"{set_name}_normal.png", "roughness": f"{set_name}_roughness.png"}
