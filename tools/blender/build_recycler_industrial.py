# BubblePop "Recycler_Industrial": a chunky, toy-like industrial recycling
# machine (original design, in the spirit of a survival-game scrap recycler).
# Builds the model, bakes ONE toon-banded colour texture, exports a
# Roblox-ready FBX and renders previews. Re-runnable:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_recycler_industrial.py
#   (add "-- fast" for quick low-sample bakes/previews, "-- qa" for extra
#    side/top/back-left QA renders in art/previews/qa_recycler_*.png)
#
# Conventions (same as build_bubblewrap.py / StealAFish ckit.py):
#   * 1 unit = 1 stud, Blender +Z up. Origin = bottom centre of the footprint.
#   * FRONT of the machine (output slot, tray, gauges) faces Blender +Y, which
#     is the MeshPart's Front face (-Z, LookVector) in Roblox.
#   * FBX: meshes turned half round about Z for the export, axis_forward -Z,
#     axis_up Y, FBX_SCALE_ALL, triangulated, path_mode STRIP. Bounds json in
#     Roblox axes like the bubble wrap files.
#
# Outputs (art/recycler/):
#   Recycler_Industrial.fbx         parts Recycler_Industrial_Body + _Glow
#   Recycler_Industrial_Body.png    1024 baked toon colour texture (Body)
#   Recycler_Industrial.bounds.json per part size/center/tris
#   Recycler_Industrial.json        part list: texture or neon colour
#   recycler_industrial.blend       the built scene (for tweaks)
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(ROOT, "art", "recycler")
PREV = os.path.join(ROOT, "art", "previews")
os.makedirs(ART, exist_ok=True)
os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FAST = "fast" in ARGS
QA = "qa" in ARGS

NAME = "Recycler_Industrial"
BODY = NAME + "_Body"
GLOW = NAME + "_Glow"
TEX = 1024
GLOW_RGB = (255, 176, 32)     # warm amber Neon (beacon, status lamps, slot strip)

# palette (sRGB 0-255)
C = dict(
    green=(84, 190, 78), green_dk=(40, 132, 72), metal=(150, 160, 172), metal_dk=(72, 78, 90),
    hole=(30, 32, 38), yellow=(255, 204, 28), black=(38, 38, 44), white=(246, 244, 232),
    red=(232, 62, 50), rubber=(52, 56, 64),
)
LIGHT = Vector((-0.45, 0.62, 0.66)).normalized()   # baked toon key light: upper front-left


def lin1(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(c):
    return tuple(lin1(x) for x in c)


# ---------------------------------------------------------------- materials (bake shaders)
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    m.use_backface_culling = True
    return m, nt, nt.nodes.new, nt.links.new


def vmath(N, L, op, a, b=None, scale=None):
    n = N("ShaderNodeVectorMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (tuple, list)):
            n.inputs[i].default_value = v
        else:
            L(v, n.inputs[i])
    if scale is not None:
        n.inputs["Scale"].default_value = scale
    return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]


def ramp(N, L, src, stops):
    """Constant (toon) ramp: stops = [(pos, value), ...] first pos = 0."""
    r = N("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for e, (p, v) in zip(els, stops):
        e.position = p
        e.color = (v, v, v, 1)
    L(src, r.inputs["Fac"])
    return r.outputs["Color"]


def mathn(N, L, op, a, b=None, clamp=False):
    n = N("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L(v, n.inputs[i])
    return n.outputs[0]


BAKE_IMG = None
MATS = {}


def bake_mat(key, kind="plain", dent=False):
    """Emission shader that paints the final toon look for baking:
    base colour x banded key light x banded cavity (AO) + light edge highlight."""
    m, nt, N, L = node_mat("bake_" + key)
    out = N("ShaderNodeOutputMaterial")
    em = N("ShaderNodeEmission")
    geo = N("ShaderNodeNewGeometry")
    tc = N("ShaderNodeTexCoord")
    # base colour
    if kind == "hazard":
        pos = tc.outputs["Object"]
        s = vmath(N, L, "DOT_PRODUCT", pos, (1.0, 1.0, 1.0))
        f = mathn(N, L, "FRACT", mathn(N, L, "DIVIDE", s, 0.78))
        stripe = mathn(N, L, "GREATER_THAN", f, 0.5)            # 1 = black
        nz = mathn(N, L, "ABSOLUTE", vmath(N, L, "DOT_PRODUCT", geo.outputs["Normal"], (0, 0, 1)))
        top = mathn(N, L, "GREATER_THAN", nz, 0.6)              # flat tops: dark metal
        y, k, d = (Vector(lin(C["yellow"])), Vector(lin(C["black"])), Vector(lin(C["metal_dk"])))
        # base = y + (k-y)*stripe ; then base + (d-base)*top
        sc1 = N("ShaderNodeVectorMath"); sc1.operation = "SCALE"
        sc1.inputs[0].default_value = tuple(k - y); L(stripe, sc1.inputs["Scale"])
        b1 = vmath(N, L, "ADD", sc1.outputs["Vector"], tuple(y))
        diff = vmath(N, L, "SUBTRACT", tuple(d), b1)
        sc2 = N("ShaderNodeVectorMath"); sc2.operation = "SCALE"
        L(diff, sc2.inputs[0]); L(top, sc2.inputs["Scale"])
        base = vmath(N, L, "ADD", b1, sc2.outputs["Vector"])
    else:
        base_v = Vector(lin(C[key if kind == "plain" else kind]))
        base = vmath(N, L, "ADD", tuple(base_v), (0, 0, 0))
    # toon key light bands
    ndl = vmath(N, L, "DOT_PRODUCT", geo.outputs["Normal"], tuple(LIGHT))
    ndl01 = mathn(N, L, "ADD", mathn(N, L, "MULTIPLY", ndl, 0.5), 0.5)
    shade = ramp(N, L, ndl01, [(0.0, 0.66), (0.42, 0.82), (0.66, 1.0)])
    # cavity / contact lines from AO
    ao = N("ShaderNodeAmbientOcclusion")
    ao.samples = 8 if FAST else 24
    ao.inputs["Distance"].default_value = 0.16
    cav = ramp(N, L, ao.outputs["AO"], [(0.0, 0.42), (0.45, 0.72), (0.7, 1.0)])
    col = vmath(N, L, "MULTIPLY", base, shade)
    col = vmath(N, L, "MULTIPLY", col, cav)
    if dent:   # soft toon dents / wear patches on the painted metal
        nz = N("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.9
        nz.inputs["Detail"].default_value = 1.0
        L(tc.outputs["Object"], nz.inputs["Vector"])
        dm = ramp(N, L, nz.outputs["Fac"], [(0.0, 1.0), (0.63, 0.88), (0.70, 0.94)])
        col = vmath(N, L, "MULTIPLY", col, dm)
    # convex edge highlight (bevel normal differs from face normal)
    bev = N("ShaderNodeBevel")
    bev.samples = 4 if FAST else 8
    bev.inputs["Radius"].default_value = 0.03
    dn = vmath(N, L, "DOT_PRODUCT", bev.outputs["Normal"], geo.outputs["Normal"])
    edge = mathn(N, L, "LESS_THAN", dn, 0.975)
    edge = mathn(N, L, "MULTIPLY", edge, mathn(N, L, "GREATER_THAN", ao.outputs["AO"], 0.6))  # not in creases
    lighter = vmath(N, L, "ADD", vmath(N, L, "SCALE", col, scale=0.72), (0.12, 0.12, 0.12))
    lighter = vmath(N, L, "ADD", lighter, vmath(N, L, "SCALE", col, scale=0.55))
    dlt = vmath(N, L, "SUBTRACT", lighter, col)
    sc = N("ShaderNodeVectorMath"); sc.operation = "SCALE"
    L(dlt, sc.inputs[0]); L(edge, sc.inputs["Scale"])
    col = vmath(N, L, "ADD", col, sc.outputs["Vector"])
    L(col, em.inputs["Color"])
    L(em.outputs[0], out.inputs["Surface"])
    t = N("ShaderNodeTexImage")
    t.image = BAKE_IMG
    nt.nodes.active = t
    MATS[key] = m
    return m


def preview_mat(name, img=None, color=None, emit=0.0):
    m, nt, N, L = node_mat(name)
    out = N("ShaderNodeOutputMaterial")
    p = N("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.55
    p.inputs["Specular IOR Level"].default_value = 0.3
    if img is not None:
        t = N("ShaderNodeTexImage")
        t.image = img
        L(t.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = lin(color) + (1,)
    if emit:
        p.inputs["Emission Color"].default_value = lin(color) + (1,)
        p.inputs["Emission Strength"].default_value = emit
    L(p.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- geometry helpers
PARTS = []   # (object, is_glow)


def part(bm, mats, loc=(0, 0, 0), rot=(0, 0, 0), smooth=False, glow=False, name="p"):
    """mats: list of material keys; bm faces' material_index index into it."""
    mat = Euler(rot).to_matrix().to_4x4()
    mat.translation = Vector(loc)
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    for f in bm.faces:
        f.smooth = smooth
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for k in mats:
        me.materials.append(MATS[k] if not glow else MATS["glow"])
    PARTS.append((ob, glow))
    return ob


def box(sx, sy, sz, bevel=0.0, segs=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=segs, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def cyl(r, depth, n=12, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=n, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    return bm


def facing(bm, d, min_area=0.0):
    d = Vector(d)
    return [f for f in bm.faces if f.normal.dot(d) > 0.99 and f.calc_area() > min_area]


def recess(bm, face, thick, depth, mat_in, mat_wall=None):
    """Inset a face and push it in: walls + dark bottom (keeps normals out)."""
    r = bmesh.ops.inset_individual(bm, faces=[face], thickness=thick, depth=-depth, use_even_offset=True)
    face.material_index = mat_in
    if mat_wall is not None:
        for f in r["faces"]:
            f.material_index = mat_wall
    return face


def axis_rot(d):
    """Euler that turns +Z onto direction d."""
    return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler()


def rivet(pos, normal, r=0.07):
    bm = cyl(r, 0.07, n=6, r2=r * 0.6)
    bmesh.ops.translate(bm, vec=(0, 0, 0.02), verts=bm.verts)
    part(bm, ["metal"], loc=pos, rot=axis_rot(normal), name="rivet")


def rrect(cx, cy, w, h, r, z, n=3):
    """Rounded rectangle ring, CCW seen from above, 4*n verts."""
    pts = []
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        ox, oy = cx + sx * (w / 2 - r), cy + sy * (h / 2 - r)
        a0 = math.pi / 2 * k
        for i in range(n):
            a = a0 + (math.pi / 2) * (i / (n - 1))
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a), z))
    return pts


def band(bm, A, B, outward=True, mi=0):
    """Quads between ring A (lower / outer) and ring B; outward faces out of the CCW ring."""
    n = len(A)
    for i in range(n):
        j = (i + 1) % n
        q = [A[i], A[j], B[j], B[i]]
        f = bm.faces.new(q if outward else q[::-1])
        f.material_index = mi


# ---------------------------------------------------------------- the machine
BODY_W, BODY_D, BODY_CY = 3.9, 3.5, -0.25      # body x width, y depth, y centre
BASE_TOP = 0.52
BODY_TOP = 3.9
LID_TOP = 4.13
FRONT_Y = BODY_CY + BODY_D / 2                  # 1.5
BACK_Y = BODY_CY - BODY_D / 2                   # -2.0


def build():
    # --- base: dark foot + hazard-striped plinth
    part(box(4.2, 4.2, 0.12, 0.03), ["metal_dk"], loc=(0, 0, 0.06), name="foot")
    part(box(4.5, 4.5, 0.42, 0.07, 1), ["hazard"], loc=(0, 0, 0.31), name="plinth")

    # --- main green body with recessed panel seams on the four sides
    bm = box(BODY_W, BODY_D, BODY_TOP - BASE_TOP + 0.05, 0.16, 2)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        for f in facing(bm, d, 1.0):
            bmesh.ops.inset_individual(bm, faces=[f], thickness=0.16, depth=-0.035, use_even_offset=True)
    part(bm, ["green"], loc=(0, BODY_CY, (BODY_TOP + BASE_TOP - 0.05) / 2), name="body")
    # horizontal belly seam: a thin dark-green belt around the body
    part(box(BODY_W + 0.08, BODY_D + 0.08, 0.2, 0.05, 1), ["green_dk"], loc=(0, BODY_CY, 2.05), name="belt")

    # --- chunky corner guards with rivets
    gz0, gz1 = BASE_TOP - 0.02, BODY_TOP + 0.08
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * BODY_W / 2, BODY_CY + sy * BODY_D / 2
            part(box(0.44, 0.44, gz1 - gz0, 0.08, 1), ["green_dk"], loc=(x, y, (gz0 + gz1) / 2), name="guard")
            for z in (0.95, 1.6, 2.5, 3.25):
                rivet((x + sx * 0.22, y, z), (sx, 0, 0))
                rivet((x, y + sy * 0.22, z), (0, sy, 0))

    # --- lid (overhanging dark-green slab)
    part(box(4.25, 3.9, LID_TOP - BODY_TOP + 0.05, 0.1, 2), ["green_dk"], loc=(0, BODY_CY, (BODY_TOP - 0.05 + LID_TOP) / 2), name="lid")
    for x in (-1.9, -0.65, 0.65, 1.9):
        rivet((x, BODY_CY + 1.95, LID_TOP - 0.12), (0, 1, 0), r=0.06)

    # --- hopper: flared funnel leaning forward, hazard rim, dark inside
    hcx, hcy = -0.3, -0.25
    z0, z1, z2 = LID_TOP - 0.02, 5.2, 5.5
    zin = 4.4
    B = rrect(hcx, hcy, 2.5, 2.1, 0.3, z0)
    T = rrect(hcx, hcy + 0.3, 3.3, 2.9, 0.45, z1)
    T2 = rrect(hcx, hcy + 0.3, 3.48, 3.08, 0.52, z1)        # lip step out
    R1 = rrect(hcx, hcy + 0.3, 3.48, 3.08, 0.52, z2)
    R2 = rrect(hcx, hcy + 0.3, 3.02, 2.62, 0.36, z2)        # inner rim edge
    R3 = rrect(hcx, hcy + 0.3, 3.02, 2.62, 0.36, z1 - 0.05)
    IB = rrect(hcx, hcy + 0.05, 2.2, 1.8, 0.22, zin)
    bm = bmesh.new()
    rings = {k: [bm.verts.new(p) for p in v] for k, v in dict(B=B, T=T, T2=T2, R1=R1, R2=R2, R3=R3, IB=IB).items()}
    band(bm, rings["B"], rings["T"], True, 0)                # outer funnel wall (green)
    band(bm, rings["T"], rings["T2"], False, 2)              # underside of lip (faces down)
    band(bm, rings["T2"], rings["R1"], True, 1)              # hazard rim band
    band(bm, rings["R1"], rings["R2"], True, 2)              # rim top
    band(bm, rings["R3"], rings["R2"], False, 2)             # inner rim wall
    band(bm, rings["IB"], rings["R3"], False, 3)             # inner funnel wall (dark)
    f = bm.faces.new(rings["IB"])                            # floor
    f.material_index = 4
    part(bm, ["green", "hazard", "metal_dk", "rubber", "hole"], name="hopper")
    # dark-green reinforcing ridge around the funnel, with rivets
    def wall_ring(t, grow, z):
        return rrect(hcx, hcy + 0.3 * t, 2.5 + 0.8 * t + 2 * grow, 2.1 + 0.8 * t + 2 * grow, 0.3 + 0.15 * t + grow, z)
    zr0, zr1 = 4.55, 4.78
    t0, t1 = (zr0 - z0) / (z1 - z0), (zr1 - z0) / (z1 - z0)
    bm = bmesh.new()
    Wl = [bm.verts.new(p) for p in wall_ring(t0, -0.02, zr0)]
    Ol = [bm.verts.new(p) for p in wall_ring(t0, 0.09, zr0)]
    Oh = [bm.verts.new(p) for p in wall_ring(t1, 0.09, zr1)]
    Wh = [bm.verts.new(p) for p in wall_ring(t1, -0.02, zr1)]
    band(bm, Ol, Wl, False)
    band(bm, Ol, Oh, True)
    band(bm, Oh, Wh, True)
    part(bm, ["green_dk"], name="hopper_ridge")
    tm = (t0 + t1) / 2
    hw, hd = (2.5 + 0.8 * tm) / 2 + 0.09, (2.1 + 0.8 * tm) / 2 + 0.09
    for k in (-0.6, 0.0, 0.6):
        rivet((hcx + k * hw, hcy + 0.3 * tm + hd, (zr0 + zr1) / 2), (0, 1, 0), r=0.05)
        rivet((hcx + k * hw, hcy + 0.3 * tm - hd, (zr0 + zr1) / 2), (0, -1, 0), r=0.05)
        rivet((hcx + hw, hcy + 0.3 * tm + k * hd, (zr0 + zr1) / 2), (1, 0, 0), r=0.05)
        rivet((hcx - hw, hcy + 0.3 * tm + k * hd, (zr0 + zr1) / 2), (-1, 0, 0), r=0.05)
    # crusher rollers inside the hopper (chunky gear teeth)
    for oy in (-0.34, 0.34):
        bm = cyl(0.34, 1.85, n=12)
        for v in bm.verts:
            a = math.atan2(v.co.y, v.co.x)
            if round(a / (2 * math.pi / 12)) % 2:
                v.co.x *= 0.62
                v.co.y *= 0.62
        if oy < 0:   # offset the teeth so the two rollers interlock
            bmesh.ops.rotate(bm, verts=bm.verts, matrix=Matrix.Rotation(math.pi / 12, 3, "Z"))
        part(bm, ["metal"], loc=(hcx, hcy + 0.05 + oy, zin + 0.2), rot=(0, math.pi / 2, 0), name="roller")

    # --- exhaust pipe (back right) with cap and hollow top
    px, py = 1.62, -1.62
    part(cyl(0.2, 1.05, 10), ["metal"], loc=(px, py, LID_TOP + 0.48), smooth=True, name="pipe")
    part(cyl(0.25, 0.12, 10), ["metal_dk"], loc=(px, py, LID_TOP + 0.45), smooth=True, name="pipe_band")
    bm = cyl(0.27, 0.24, 10)
    top = facing(bm, (0, 0, 1))[0]
    recess(bm, top, 0.07, 0.2, 1, 1)
    part(bm, ["metal_dk", "hole"], loc=(px, py, LID_TOP + 1.05), name="pipe_cap")
    part(cyl(0.3, 0.1, 10), ["metal_dk"], loc=(px, py, LID_TOP + 0.05), name="pipe_foot")

    # --- beacon (front right of the lid): dark base, amber dome (Glow), cage bar
    bx, by = 1.68, 1.05
    part(cyl(0.36, 0.2, 12), ["metal_dk"], loc=(bx, by, LID_TOP + 0.08), name="beacon_base")
    part(cyl(0.29, 0.46, 12, r2=0.17), ["glow"], loc=(bx, by, LID_TOP + 0.4), smooth=True, glow=True, name="beacon")
    part(cyl(0.2, 0.08, 10), ["metal_dk"], loc=(bx, by, LID_TOP + 0.66), name="beacon_cap")
    for a in (0.0, math.pi / 2):
        part(box(0.62, 0.06, 0.06), ["metal_dk"], loc=(bx, by, LID_TOP + 0.42), rot=(0, 0, a), name="cage_ring")

    # --- front: output slot frame with dark recess, sloped tray, glow strip
    fy = FRONT_Y
    bm = box(2.7, 0.42, 0.95, 0.07, 1)
    recess(bm, facing(bm, (0, 1, 0), 0.5)[0], 0.16, 0.3, 1, 2)
    part(bm, ["metal", "hole", "metal_dk"], loc=(0, fy + 0.1, 1.42), name="slot")
    part(box(2.3, 0.08, 0.07), ["glow"], loc=(0, fy + 0.32, 1.97), glow=True, name="slot_light")
    part(box(2.6, 0.12, 0.08, 0.02), ["metal_dk"], loc=(0, fy + 0.3, 2.04), name="slot_light_hood")
    part(box(2.5, 0.8, 0.12, 0.03), ["metal"], loc=(0, fy + 0.55, 0.86), rot=(math.radians(-14), 0, 0), name="tray")
    for sx in (-1, 1):
        part(box(0.12, 0.8, 0.34, 0.03), ["yellow"], loc=(sx * 1.25, fy + 0.55, 0.92), rot=(math.radians(-14), 0, 0), name="tray_side")
    part(box(2.62, 0.12, 0.3, 0.04), ["hazard"], loc=(0, fy + 0.93, 0.72), name="tray_lip")

    # control panel: two gauges, red button, two status lamps (Glow)
    part(box(3.0, 0.14, 1.05, 0.05, 1), ["metal_dk"], loc=(0, fy + 0.05, 2.85), name="panel")
    for gx, ang in ((-0.95, 35), (-0.1, -50)):
        bm = cyl(0.36, 0.16, 16)
        f = facing(bm, (0, 0, 1))[0]
        recess(bm, f, 0.07, 0.04, 1, 0)
        part(bm, ["metal", "white"], loc=(gx, fy + 0.2, 2.85), rot=(-math.pi / 2, 0, 0), name="gauge")
        bm = box(0.05, 0.03, 0.26)
        bmesh.ops.translate(bm, vec=(0, 0, 0.1), verts=bm.verts)
        part(bm, ["red"], loc=(gx, fy + 0.27, 2.85), rot=(0, math.radians(ang), 0), name="needle")
        part(cyl(0.05, 0.05, 6), ["black"], loc=(gx, fy + 0.27, 2.85), rot=(-math.pi / 2, 0, 0), name="hub")
    part(cyl(0.2, 0.1, 12), ["metal_dk"], loc=(0.8, fy + 0.15, 2.7), rot=(-math.pi / 2, 0, 0), name="btn_ring")
    part(cyl(0.15, 0.14, 12, r2=0.12), ["red"], loc=(0.8, fy + 0.24, 2.7), rot=(-math.pi / 2, 0, 0), smooth=True, name="btn")
    for lx in (0.65, 1.0):
        part(cyl(0.13, 0.08, 10), ["black"], loc=(lx, fy + 0.15, 3.15), rot=(-math.pi / 2, 0, 0), name="lamp_ring")
        part(cyl(0.09, 0.1, 10, r2=0.06), ["glow"], loc=(lx, fy + 0.2, 3.15), rot=(-math.pi / 2, 0, 0), smooth=True, glow=True, name="lamp")
    for x in (-1.4, 1.4):
        for z in (2.42, 3.28):
            rivet((x, fy + 0.12, z), (0, 1, 0), r=0.055)

    # --- right side: big pull lever
    rx = BODY_W / 2
    part(box(0.24, 0.8, 0.8, 0.06, 1), ["metal_dk"], loc=(rx + 0.08, -0.4, 2.55), name="lever_box")
    bm = box(0.12, 0.12, 1.05, 0.02)
    bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
    part(bm, ["metal"], loc=(rx + 0.24, -0.4, 2.55), rot=(math.radians(-38), 0, 0), name="lever")
    tip = Vector((0, 0, 1.08))
    tip.rotate(Euler((math.radians(-38), 0, 0)))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.19)
    part(bm, ["red"], loc=Vector((rx + 0.24, -0.4, 2.55)) + tip, smooth=True, name="knob")
    part(cyl(0.13, 0.1, 8), ["black"], loc=(rx + 0.22, -0.4, 2.55), rot=(0, math.pi / 2, 0), name="pivot")

    # --- left side: louvred vent
    lx0 = -BODY_W / 2
    bm = box(0.36, 2.0, 1.2, 0.06, 1)
    recess(bm, facing(bm, (-1, 0, 0), 0.5)[0], 0.13, 0.22, 1, 2)
    part(bm, ["metal", "hole", "metal_dk"], loc=(lx0 - 0.05, -0.25, 2.85), name="vent")
    for z in (2.53, 2.75, 2.97, 3.19):
        part(box(0.05, 1.68, 0.13), ["metal"], loc=(lx0 - 0.12, -0.25, z), rot=(0, math.radians(-35), 0), name="slat")
    # left side small pipe loop
    part(cyl(0.11, 1.5, 8), ["yellow"], loc=(lx0 - 0.17, -0.25, 1.4), rot=(math.pi / 2, 0, 0), smooth=True, name="side_pipe")
    for yy in (-0.9, 0.4):
        part(box(0.2, 0.14, 0.3, 0.03), ["metal_dk"], loc=(lx0 - 0.08, yy, 1.4), name="pipe_clamp")

    # --- back: access hatch with rivets and handle
    bkz = 2.75
    part(box(2.1, 0.1, 1.5, 0.05, 1), ["green_dk"], loc=(0, BACK_Y - 0.04, bkz), name="hatch")
    for x in (-0.9, 0.9):
        for z in (bkz - 0.6, bkz + 0.6):
            rivet((x, BACK_Y - 0.09, z), (0, -1, 0), r=0.06)
    part(box(0.8, 0.1, 0.1, 0.03), ["metal_dk"], loc=(0, BACK_Y - 0.2, bkz), name="handle")
    for x in (-0.36, 0.36):
        part(box(0.1, 0.18, 0.1, 0.0), ["metal_dk"], loc=(x, BACK_Y - 0.13, bkz), name="handle_post")
    part(box(2.6, 0.12, 0.35, 0.04), ["hazard"], loc=(0, BACK_Y - 0.03, 1.15), name="back_stripe")


# ---------------------------------------------------------------- join / uv / bake
def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(me)
    bm.free()
    return ob


def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


def uv_unwrap(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def bake(ob, path):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 8 if FAST else 48
    sc.render.bake.margin = 8
    sc.render.bake.use_clear = True
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="EMIT")
    BAKE_IMG.filepath_raw = path
    BAKE_IMG.file_format = "PNG"
    BAKE_IMG.save()


# ---------------------------------------------------------------- export
def export(objs):
    half_turn = Matrix.Rotation(math.pi, 4, "Z")
    bounds = {}
    for ob in objs:
        xs = [v.co for v in ob.data.vertices]
        lo = Vector([min(c[i] for c in xs) for i in range(3)])
        hi = Vector([max(c[i] for c in xs) for i in range(3)])
        bounds[ob.name] = {
            "size": [round(hi.x - lo.x, 4), round(hi.z - lo.z, 4), round(hi.y - lo.y, 4)],
            "center": [round((hi.x + lo.x) / 2, 4), round((hi.z + lo.z) / 2, 4), round(-(hi.y + lo.y) / 2, 4)],
            "tris": tris(ob),
            "origin": "bottom centre of footprint",
        }
        ob.data.transform(half_turn)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(ART, NAME + ".fbx"), use_selection=True, object_types={"MESH"}, mesh_smooth_type="OFF",
        use_triangles=True, axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", path_mode="STRIP", colors_type="NONE",
    )
    for ob in objs:
        ob.data.transform(half_turn)
    with open(os.path.join(ART, NAME + ".bounds.json"), "w") as f:
        json.dump(bounds, f, indent=1)
    return bounds


# ---------------------------------------------------------------- previews
def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 16 if FAST else 64
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = lin((226, 236, 248)) + (1,)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.4
    sun.angle = math.radians(8)
    so = bpy.data.objects.new("Sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (-Vector((-0.5, 0.35, 0.8)).normalized()).to_track_quat("-Z", "Y").to_euler()
    # light ground to catch the shadow
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
    me = bpy.data.meshes.new("Ground")
    bm.to_mesh(me)
    g = bpy.data.objects.new("Ground", me)
    sc.collection.objects.link(g)
    me.materials.append(preview_mat("ground", color=(232, 236, 242)))
    return sc


def camera(name, loc, target, lens=45):
    cd = bpy.data.cameras.new(name)
    co = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = Vector(loc)
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    return co


def render(cam, path, res=(1200, 1200)):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 50 if FAST else 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


# ---------------------------------------------------------------- main
def main():
    global BAKE_IMG
    bpy.ops.wm.read_factory_settings(use_empty=True)
    BAKE_IMG = bpy.data.images.new(BODY, TEX, TEX, alpha=False)
    for k in ("green", "green_dk", "metal", "metal_dk", "hole", "yellow", "black", "white", "red", "rubber"):
        bake_mat(k, dent=k in ("green", "green_dk"))
    bake_mat("hazard", kind="hazard")
    MATS["glow"] = preview_mat("Neon", color=GLOW_RGB, emit=4.0)

    build()
    body = join([o for o, g in PARTS if not g], BODY)
    glow = join([o for o, g in PARTS if g], GLOW)
    for o in (body, glow):
        o.data.shade_flat() if hasattr(o.data, "shade_flat") else None
    uv_unwrap(body)
    tex_path = os.path.join(ART, BODY + ".png")
    bake(body, tex_path)

    # final materials: Body = baked texture only, Glow = plain neon colour
    body.data.materials.clear()
    body.data.materials.append(preview_mat("Recycler_Body", img=BAKE_IMG))
    for p in body.data.polygons:
        p.material_index = 0
    glow.data.materials.clear()
    glow.data.materials.append(MATS["glow"])
    for p in glow.data.polygons:
        p.material_index = 0

    bounds = export([body, glow])
    with open(os.path.join(ART, NAME + ".json"), "w") as f:
        json.dump({
            "model": NAME,
            "fbx": NAME + ".fbx",
            "front": "Blender +Y = MeshPart Front (-Z / LookVector) in Roblox: output slot, tray, gauges",
            "parts": [
                {"name": BODY, "texture": BODY + ".png", "material": "SmoothPlastic", "tris": bounds[BODY]["tris"]},
                {"name": GLOW, "neon": list(GLOW_RGB), "material": "Neon", "tris": bounds[GLOW]["tris"]},
            ],
            "total_tris": bounds[BODY]["tris"] + bounds[GLOW]["tris"],
        }, f, indent=1)
    print("TRIS", {k: v["tris"] for k, v in bounds.items()})

    setup_render()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ART, "recycler_industrial.blend"))
    tgt = (0, 0, 2.55)
    render(camera("CamFront", (7.6, 10.2, 5.8), tgt), os.path.join(PREV, "recycler_industrial_front.png"))
    render(camera("CamBack", (-7.6, -10.2, 5.8), tgt), os.path.join(PREV, "recycler_industrial_back.png"))
    if QA:
        render(camera("CamL", (-12.5, 2.0, 4.0), tgt), os.path.join(PREV, "qa_recycler_left.png"))
        render(camera("CamR", (12.5, -2.0, 4.0), tgt), os.path.join(PREV, "qa_recycler_right.png"))
        render(camera("CamTop", (0.5, 1.5, 14.0), (0, 0, 2.5)), os.path.join(PREV, "qa_recycler_top.png"))
        render(camera("CamLow", (3.0, 9.0, 1.2), (0, 0, 2.2)), os.path.join(PREV, "qa_recycler_low_front.png"))


main()
