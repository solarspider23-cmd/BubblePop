# Batch A1 (docs/art_plan.md): the giant gumball machine, the lobby's landmark.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_machine_build_machine.py
#   (run hub_machine_build_gumball_lo.py first if you want the gumball pile in the previews)
#
# Outputs (art/hub_machine/)
#   Hub_Machine.fbx            Machine_Body, Machine_Knob (spins), Machine_Flap (swings),
#                              Machine_Glass (Roblox Glass), Machine_Shine (flat white highlight)
#   Hub_Machine_color.png / _normal.png / _roughness.png   one 1024 set shared by Body, Knob, Flap
#   Hub_Machine.blend, Hub_Machine.bounds.json (sizes, triangle counts, knob spin point, flap hinge)
# Previews (art/previews/): hub_machine_beauty / _flat / _thumb / _turn .png
#
# About 28 wide x 28 deep x 47 tall, standing on the origin, front on +Y. Toy-plastic gold (no metal,
# so no metalness map). All words stay in-game text; nothing is written on the model.

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_machine_common as C  # noqa: E402

TEX = 1024
GLOBE_C = Vector((0, 0, 29.0))   # globe centre
GLOBE_R = 14.0
KNOB_C = Vector((0, 9.0, 7.9))   # middle of the dial, on the coin plate's front face
FLAP_HINGE = Vector((0, 9.35, 4.55))
BODY, KNOB, FLAP = 0, 1, 2

scene = C.reset()
b = C.Build()


def toward_front(at):
    """Frame for a lathe whose axis points out of the front (+Y)."""
    m = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    return Matrix.Translation(Vector(at)) @ m


# ------------------------------------------------------------------ stage (pink, flat top to stand on)
b.use("pink", obj=BODY, w=0.42)
b.lathe(C.fillet([(13.4, 0.2), (13.4, 1.5), (8.4, 1.5)], 0.55, 3), segs=48)
b.use("cream", w=0.6)
b.lathe([(14.0, 0.0)] + C.arc(13.3, 0.0, 0.7, 12, 100, 4), segs=48)

# ------------------------------------------------------------------ body (red rounded square, tapering up)
YSQ = 0.95


def body_n(z):
    return 4.0 if z < 12.4 else max(3.0, 4.0 - (z - 12.4) / 1.3)


b.use("gold", w=0.9)
b.lathe(C.fillet([(9.3, 1.45), (10.0, 1.45), (10.0, 2.7), (9.0, 2.7)], 0.42, 2), segs=56,
        shape=C.squircle(lambda z: 4.0, YSQ))
b.use("red", w=1.0)
b.lathe([(8.8, 2.3), (9.15, 2.75), (9.2, 3.5), (9.05, 6.0), (8.82, 9.0), (8.62, 11.5), (8.58, 12.0),
         (8.34, 12.12), (8.34, 12.3), (8.55, 12.42),            # the moulded seam (a groove)
         (8.45, 12.9), (8.1, 13.4), (7.5, 13.65), (6.9, 13.7)],
        segs=56, shape=C.squircle(body_n, YSQ))

# ------------------------------------------------------------------ neck cup (red) and beaded collar (gold)
b.use("red", w=0.9)
b.lathe([(7.4, 13.3), (8.2, 13.3), (8.55, 13.4), (8.7, 13.7), (8.55, 14.0), (8.2, 14.15),  # clip-on lip
         (7.85, 14.4), (7.7, 15.0), (7.85, 15.8), (8.5, 16.8), (9.3, 17.5), (10.05, 18.0), (10.5, 18.25)], segs=48)
b.use("gold", w=1.0)
b.lathe([(10.3, 18.15), (10.85, 18.25), (11.05, 18.6), (11.05, 19.1), (10.85, 19.45), (10.4, 19.6), (10.2, 19.62)],
        segs=48, cap_end=True)   # the fan is the floor you see through the glass
BEADS = 30
for i in range(BEADS):
    a = 2 * math.pi * (i + 0.5) / BEADS
    rad, tan = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    fr = Matrix.Translation(rad * 10.95 + Vector((0, 0, 18.85))) @ Matrix(
        ((tan.x, 0, rad.x, 0), (tan.y, 0, rad.y, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    b.instance(1, i)
    b.lathe([(0.6, 0.0), (0.56, 0.24), (0.40, 0.47), (0.17, 0.59)], segs=6, frame=fr, cap_end=True)
b.instance(0, 0)

# ------------------------------------------------------------------ cap (gold lip, red dome, gold knob)
b.use("gold", w=0.9)
b.lathe([(4.4, 42.0), (5.15, 41.95), (5.45, 42.3), (5.3, 42.7), (4.9, 42.8)], segs=40, cap_start=True)
b.use("red", w=0.8)
b.lathe([(5.0, 42.7), (5.1, 43.4), (4.8, 44.0), (4.0, 44.45), (2.6, 44.7), (1.2, 44.78)], segs=40)
b.use("gold", w=0.9)
b.lathe([(1.7 * math.cos(math.radians(a)), 45.4 + 1.7 * math.sin(math.radians(a))) for a in range(-28, 85, 14)],
        segs=24, cap_end=True)

# ------------------------------------------------------------------ coin plate (cream) with gold dial and slot
b.use("cream", w=1.6)
b.rbox((6.0, 1.5, 5.8), (0, 8.25, 8.7), 0.45, 3)
b.use("gold")
b.lathe(C.fillet([(2.0, -0.1), (2.0, 0.32), (0.6, 0.32)], 0.2, 3), segs=28, frame=toward_front(KNOB_C))
b.rbox((2.6, 0.5, 1.0), (0, 9.03, 10.75), 0.22, 3)
b.use("navy")
b.rbox((1.7, 0.3, 0.42), (0, 9.17, 10.75), 0.05, 1)

# ------------------------------------------------------------------ chute (cream frame, dark mouth, tray)
b.use("cream", w=1.4)
outer, inner = C.arch(3.1, 1.4, 5.3, 1.5), C.arch(2.4, 2.05, 4.7, 1.0)


def ring(t, y):
    return [(ix + (ox - ix) * t, y, iz + (oz - iz) * t) for (ix, iz), (ox, oz) in zip(inner, outer)]


b.loft([ring(0, 8.8), ring(0, 9.55), ring(0.15, 9.75), ring(0.85, 9.75), ring(1, 9.55), ring(1, 8.3)])
b.use("navy")
back = b.loft([ring(0, 8.86), ring(0.001, 8.85)])
b.fan(back[1], (0, 8.85, 3.4), flip=True)
b.use("cream")
TS = 14


def tray(s, z):
    return [(3.0 * s * math.cos(math.pi * k / TS), 9.3 + 2.3 * s * math.sin(math.pi * k / TS), z) for k in range(TS + 1)]


tr = b.loft([tray(1.0, 1.4), tray(1.0, 2.05), tray(0.97, 2.22), tray(0.88, 2.22), tray(0.85, 2.08), tray(0.85, 1.95)])
b.fan(tr[-1], (0, 10.0, 1.95))

# ------------------------------------------------------------------ the turning knob (hero detail; separate, spins)
b.use("gold", obj=KNOB, w=2.3)
b.lathe(C.fillet([(0.95, 0.25), (0.95, 0.75), (0.4, 0.75)], 0.12, 2), segs=16, frame=toward_front(KNOB_C))
b.use("cream")
WN = 28


def wing(inset, y):
    """Butterfly outline (two fat lobes, narrow waist), shrunk by `inset`, at depth y."""
    pts = []
    for k in range(WN):
        t = -2 * math.pi * k / WN          # clockwise in (x, z) = counter-clockwise seen from the front
        rho = 0.6 + 1.2 * math.cos(t) ** 2 - inset
        pts.append((rho * math.cos(t), y, KNOB_C.z + rho * math.sin(t)))
    return pts


Y0, Y1 = KNOB_C.y + 0.62, KNOB_C.y + 1.45
wr = b.loft([wing(0.5, Y0), wing(0.2, Y0), wing(0.06, Y0 + 0.07), wing(0.0, Y0 + 0.22), wing(0.0, Y1 - 0.22),
             wing(0.06, Y1 - 0.07), wing(0.2, Y1), wing(0.5, Y1)])
b.fan(wr[-1], (0, Y1, KNOB_C.z), flip=True)
b.use("gold")
b.lathe([(0.62, 1.38), (0.6, 1.58), (0.42, 1.76), (0.16, 1.84)], segs=14, frame=toward_front(KNOB_C), cap_end=True)

# ------------------------------------------------------------------ chute flap (separate, swings on its top edge)
b.use("gold", obj=FLAP, w=1.4)
b.solid(C.arch(2.28, 2.5, 4.58, 0.9, 3), 9.15, 9.6, "xz", bevel=0.14)
b.rbox((2.0, 0.45, 0.45), (0, 9.72, 2.95), 0.14, 1)

objs = b.finalize({BODY: "Machine_Body", KNOB: "Machine_Knob", FLAP: "Machine_Flap"}, scene)
body, knob, flap = objs["Machine_Body"], objs["Machine_Knob"], objs["Machine_Flap"]
order = b.mats

# ------------------------------------------------------------------ glass globe and shine (no texture)
g = C.Build()
g.use("glass", obj=0)
a0 = math.degrees(math.asin((21.0 - GLOBE_C.z) / GLOBE_R))
a1 = math.degrees(math.asin((42.2 - GLOBE_C.z) / GLOBE_R))
GS = 12
g.lathe([(10.3, 19.55), (11.15, 19.62), (11.5, 19.95), (11.5, 20.35), (11.3, 20.7)] +      # thick rim
        [(GLOBE_R * math.cos(math.radians(a0 + (a1 - a0) * i / GS)),
          GLOBE_C.z + GLOBE_R * math.sin(math.radians(a0 + (a1 - a0) * i / GS))) for i in range(GS + 1)], segs=48)


def on_globe(az, el, r):
    az, el = math.radians(az), math.radians(el)
    return GLOBE_C + Vector((-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))) * r


def shine_patch(outline, center):
    def pts(scale, r):
        return [on_globe(center[0] + (u - center[0]) * scale, center[1] + (v - center[1]) * scale, r) for u, v in outline]
    rings = g.loft([pts(1.0, 13.9), pts(1.0, 14.2), pts(0.86, 14.28), pts(0.45, 14.3)])
    g.fan(rings[-1], on_globe(center[0], center[1], 14.3))


g.use("shine", obj=1)
tilt = math.radians(-18)
win = [(-27 + u * math.cos(tilt) - v * math.sin(tilt), 37 + u * math.sin(tilt) + v * math.cos(tilt))
       for u, v in C.rrect(13, 25, 5.5, 3)]
shine_patch(win, (-27, 37))
shine_patch(C.arc(-13.5, 17.5, 3.4, 0, 320, 8), (-13.5, 17.5))
gobjs = g.finalize({0: "Machine_Glass", 1: "Machine_Shine"}, scene, pack=False)
glass, shine = gobjs["Machine_Glass"], gobjs["Machine_Shine"]

# ------------------------------------------------------------------ bake the shared 1024 texture set
BAKE = {
    "red": dict(hexcol=C.HEX["red"], rough=0.18, grad=(2.0, 14.0, 0.10)),
    "cream": dict(hexcol=C.HEX["cream"], rough=0.28, grad=(0.0, 12.0, 0.05)),
    "pink": dict(hexcol=C.HEX["pink"], rough=0.50),
    "gold": dict(hexcol=C.HEX["gold"], rough=0.22),
    "navy": dict(hexcol=C.HEX["navy"], rough=0.60),
}
paths = C.bake_set(scene, [body, knob, flap], [C.bake_material(n, **BAKE[n]) for n in order], TEX, "Hub_Machine",
                   ao_strength=0.55, ao_tint=(0.80, 0.62, 0.72))
full = C.textured_material("Hub_Machine", paths)
flat = C.textured_material("Hub_Machine_Flat", paths, flat=True)
for ob in (body, knob, flap):
    C.single_material(ob, full)
C.single_material(glass, C.glass_material("Machine_Glass"))
C.single_material(shine, C.plain_material("Machine_Shine", "#FFFFFF", 0.3, emit=0.6))

# ------------------------------------------------------------------ report + files
model = [body, knob, flap, glass, shine]
tris = {o.name: C.tri_count(o) for o in model}
total = sum(tris.values())
lo = Vector([min((o.matrix_world @ v.co)[i] for o in model for v in o.data.vertices) for i in range(3)])
hi = Vector([max((o.matrix_world @ v.co)[i] for o in model for v in o.data.vertices) for i in range(3)])
print("TRIANGLES", tris, "total", total)
print("SIZE %.2f wide x %.2f deep x %.2f tall; lowest point %.3f" % (hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.z))
assert total <= 12000 and max(tris.values()) <= 10000, "over the triangle budget"
assert tris["Machine_Shine"] <= 200
for got, want in ((hi.x - lo.x, 28), (hi.y - lo.y, 28), (hi.z - lo.z, 47)):
    assert abs(got - want) / want <= 0.10, "size is more than 10%% off: %.2f vs %s" % (got, want)

C.export_fbx(model, os.path.join(C.OUT, "Hub_Machine.fbx"))
tex = {"textures": ["Hub_Machine_color.png", "Hub_Machine_normal.png", "Hub_Machine_roughness.png"]}
C.write_json(os.path.join(C.OUT, "Hub_Machine.bounds.json"), {
    "_about": "Gumball machine. Roblox axes: X right, Y up, Z = -Blender Y. The model stands on the origin "
              "(bottom centre of the stage) and its front (coin plate, chute) faces Roblox -Z.",
    "_size": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
    "_tris_total": total,
    "_globe": {"center": C.rbx(GLOBE_C), "radius": GLOBE_R,
               "note": "GumballPile_Globe.json positions are measured from this point"},
    "Machine_Body": dict(C.roblox_box(body), material="SmoothPlastic + SurfaceAppearance", color=[255, 255, 255], **tex),
    "Machine_Knob": dict(C.roblox_box(knob), material="SmoothPlastic + SurfaceAppearance", color=[255, 255, 255],
                         spin_point=C.rbx(KNOB_C), spin_axis=[0, 0, 1],
                         note="turn about spin_axis through spin_point", **tex),
    "Machine_Flap": dict(C.roblox_box(flap), material="SmoothPlastic + SurfaceAppearance", color=[255, 255, 255],
                         hinge=C.rbx(FLAP_HINGE), hinge_axis=[1, 0, 0],
                         note="swings outward (toward the front) about hinge_axis through hinge", **tex),
    "Machine_Glass": dict(C.roblox_box(glass), material="Glass", color=[235, 248, 255], transparency=0.6,
                          note="no texture, no shadow"),
    "Machine_Shine": dict(C.roblox_box(shine), material="SmoothPlastic (or Neon)", color=[255, 255, 255],
                          transparency=0.15, note="no texture, no shadow, no collision"),
})

# ------------------------------------------------------------------ previews
state = {"pile": []}
PJ = os.path.join(C.OUT, "GumballPile_Globe.json")
LB = os.path.join(C.OUT, "Hub_GumballLo.blend")
if os.path.exists(PJ) and os.path.exists(LB):
    with bpy.data.libraries.load(LB) as (src, dst):
        dst.meshes = [m for m in src.meshes if m in ("GumballLo", "GumballCore_Globe")]
    got = {m.name: m for m in dst.meshes}
    state["pile"] = C.add_pile(scene, PJ, got["GumballLo"], GLOBE_C, core_mesh=got.get("GumballCore_Globe"))
    state["lo"] = got["GumballLo"]


def set_flat(on):
    for ob in (body, knob, flap):
        ob.data.materials[0] = flat if on else full
    for o in state["pile"]:
        if o.name.startswith("PreviewGum"):
            m = o.data.materials[0]
            want = m.name.rstrip("F") + ("F" if on else "")
            if want not in bpy.data.materials:
                C.textured_material(want, C.gumball_paths(), flat=on, tint=C.GUMBALL_HEX[int(m.name.rstrip("F")[-1])])
            o.data.materials[0] = bpy.data.materials[want]


def extra(st):
    dbg = os.environ.get("HUB_DEBUG_DIR")
    if dbg:
        for o in state["pile"] + [glass]:
            o.hide_render = True
        C.backface_sheet(scene, st, [body, knob, flap, shine], lo, hi, os.path.join(dbg, "machine_backfaces.png"))
        glass.hide_render = False
        C.backface_sheet(scene, st, [glass], lo, hi, os.path.join(dbg, "machine_glass_backfaces.png"))
        for o in state["pile"]:
            o.hide_render = False
        # close-up of the hero detail
        C.frame(scene, st["cam"], (0.45, 0.85, 0.12), (-6, 7, 1.2), (6, 12, 13), 60, (1100, 960))
        C.render(scene, os.path.join(dbg, "machine_closeup.png"))


C.standard_previews(scene, "hub_machine", lo, hi, set_flat, view=(0.50, 0.82, 0.22), player=(-17.5, 9, 0),
                    extra=extra)
C.save_blend(os.path.join(C.OUT, "Hub_Machine.blend"), model)
print("MACHINE done")
