# CLEAN POP PLAZA 5a: the island rim and underside (replace the frosting rim and the chocolate).
# A smooth white bumper lip with a pastel band and a thin light line, and under it four soft tiers of
# white rock and pale stone narrowing to a rounded tip, with a few pastel crystals growing out of the
# ledges. Same size as art/hub_island: about 204 across at the rim, underside 198 wide hanging to -60.
# Blender height 0 = the grass surface. One 1024 texture set (Hub_CleanIsland_*).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_island.py
#
# Outputs (art/hub_clean/): Hub_CleanIsland.fbx with CleanIsland_Rim, CleanIsland_Under,
# CleanIsland_Crystal, CleanIsland_Glow

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

P = K.P
TEX = 1024
sc = K.reset()

TIERS = [  # outer radius, top, bottom, zone
    (97.0, -10.5, -27.0, "rockA"),
    (70.0, -24.0, -41.0, "rockB"),
    (44.0, -38.0, -52.0, "rockC"),
    (22.0, -49.0, -60.0, "rockD"),
]
Z = {
    "white": K.zone("i_white", K.vgrad(K.PAL["grey"], K.PAL["white"], -12.0, -2.0), 0.24, ao=0.3, ao_dist=6.0, grad=0.0),
    "band": K.zone("i_band", K.PAL["sky"], 0.18, ao=0.25, ao_dist=2.0, grad=0.0),
    "rockA": K.zone("i_rockA", K.vgrad("#DDE2EC", K.PAL["white"], -27.0, -14.0), 0.4, ao=0.4, ao_dist=14.0, grad=0.0),
    "rockB": K.zone("i_rockB", K.vgrad("#B9C3D8", "#D6DDEA", -41.0, -27.0), 0.5, ao=0.4, ao_dist=14.0, grad=0.0),
    "rockC": K.zone("i_rockC", K.vgrad("#E4DACB", K.PAL["cream"], -52.0, -40.0), 0.4, ao=0.4, ao_dist=12.0, grad=0.0),
    "rockD": K.zone("i_rockD", K.vgrad("#AEB9D0", "#CDD5E4", -60.0, -50.0), 0.5, ao=0.4, ao_dist=10.0, grad=0.0),
}
CRYSTAL = ["sky", "mint", "lilac", "peach"]
for nm in CRYSTAL:
    Z["c_" + nm] = K.zone("i_c_" + nm, K.PAL[nm], 0.1, ao=0.2, ao_dist=4.0, grad=0.0)
GLOW = P.flat_material("CleanIsland_Glow", K.PAL["glow"], 0.3, emit=5.0)
mats = dict(Z, glow=GLOW)

# ------------------------------------------------------------------ rim: white bumper lip rolling over the grass edge
rim = P.MeshBuilder("CleanIsland_Rim")
RSEG = 96
rc = lambda d: P.circle2d(d, RSEG)
rim.lathe([(97.2, 0.02), (98.2, 0.45), (100.0, 0.6), (101.6, 0.1), (102.3, -1.4), (102.4, -3.6), (102.25, -6.0),
           (101.85, -6.3), (101.85, -6.95), (101.85, -6.95, "band"), (101.8, -9.0), (102.1, -9.3, "white"), (101.8, -10.6),
           (100.3, -11.7), (97.5, -12.3), (94.0, -12.3)], rc, zone="white")
glow = P.MeshBuilder("CleanIsland_Glow")
glow.lathe([(101.98, -6.38), (101.98, -6.88)], rc, zone="glow")

# ------------------------------------------------------------------ underside: four soft tiers
USEG = 72
SHAPE = [(0.93, 0.0), (0.985, 0.08), (1.0, 0.25), (0.995, 0.5), (0.96, 0.75), (0.88, 0.92), (0.78, 1.0)]
TIP = [(0.95, 0.0), (1.0, 0.18), (0.98, 0.42), (0.87, 0.66), (0.66, 0.85), (0.36, 0.96)]


def lobed(r, z, phase, amp=0.032):
    pts = []
    for i in range(USEG):
        a = 2 * math.pi * i / USEG
        rr = r * (1 + amp * (0.6 * math.cos(3 * a + phase) + 0.4 * math.cos(5 * a + 2.3 * phase)))
        pts.append((rr * math.cos(a), rr * math.sin(a), z))
    return pts


under = P.MeshBuilder("CleanIsland_Under")
rings, zones = [], []
for ti, (R, zt, zb_, zn) in enumerate(TIERS):
    for f, t in (TIP if ti == len(TIERS) - 1 else SHAPE):
        rings.append(lobed(R * f, zt + (zb_ - zt) * t, 1.1 + ti * 1.7, 0.032 if ti else 0.02))
        zones.append(zn)
K.loft(under, rings, zones=zones[:-1])
last = [under.bm.verts.new(Vector(p)) for p in rings[-1]]
tip = under.bm.verts.new(Vector((0, 0, TIERS[-1][2])))
for j in range(USEG):
    under.face((last[j], last[(j + 1) % USEG], tip), TIERS[-1][3])

# ------------------------------------------------------------------ crystals growing out of the ledges
cry = P.MeshBuilder("CleanIsland_Crystal")


def crystal(base, axis, rho, length, zone):
    axis = Vector(axis).normalized()
    u = axis.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = Vector((1, 0, 0))
    u.normalize()
    v = axis.cross(u)
    cry.lathe([(rho * 0.7, 0.0), (rho, length * 0.55), (rho * 0.85, length * 0.72), (0.0, length)],
              lambda d: P.circle2d(d, 6), (Vector(base), u, v, axis), zone=zone, smooth=False)


CLUSTERS = [  # angle (deg), radius, height of the root, size
    (25, 82.0, -24.5, 1.0), (150, 83.0, -24.5, 0.85), (262, 82.0, -24.5, 1.1),
    (95, 58.0, -38.5, 0.9), (318, 58.0, -38.5, 1.0), (205, 36.0, -50.0, 0.8),
]
for ci, (ang, rad, z, s) in enumerate(CLUSTERS):
    a = math.radians(ang)
    out = Vector((math.cos(a), math.sin(a), 0))
    tan = Vector((-math.sin(a), math.cos(a), 0))
    root = out * rad + Vector((0, 0, z))
    zn = "c_" + CRYSTAL[ci % 4]
    zn2 = "c_" + CRYSTAL[(ci + 1) % 4]
    crystal(root, out * 0.45 - Vector((0, 0, 1)), 3.6 * s, 17.0 * s, zn)
    crystal(root + tan * 3.6 * s, out * 0.5 + tan * 0.4 - Vector((0, 0, 1)), 2.4 * s, 10.5 * s, zn2)
    crystal(root - tan * 3.3 * s + out * 1.2, out * 0.8 - tan * 0.45 - Vector((0, 0, 1)), 2.0 * s, 8.5 * s, zn)

o_rim, o_under, o_cry, o_glow = rim.build(mats), under.build(mats), cry.build(mats, weighted=False), glow.build(mats, weighted=False)
textured = [o_rim, o_under, o_cry]
P.unwrap(textured, margin=0.004)
P.unwrap([o_glow], margin=0.02)
fin, maps = P.bake_set("Hub_CleanIsland", textured, TEX)

objs = [o_rim, o_under, o_cry, o_glow]
print("[Hub_CleanIsland] triangles")
t = P.report(objs, {"CleanIsland_Glow": 200})
print(f"  budget 5000-8000: {'OK' if t <= 8000 else 'OVER'}")
P.export_fbx(os.path.join(K.OUT, "Hub_CleanIsland.fbx"), objs)
tex = K.tex_names("Hub_CleanIsland")
SA_ = "SmoothPlastic (SurfaceAppearance)"
P.write_bounds(os.path.join(K.OUT, "Hub_CleanIsland.bounds.json"), {
    "grassTopBlenderZ": 0.0, "grassTopHubY": -3.0, "_tris_total": t,
    "CleanIsland_Rim": P.bounds_entry(o_rim, textures=tex, material=SA_, note="white bumper lip rolling over the grass edge, sky-blue band"),
    "CleanIsland_Under": P.bounds_entry(o_under, textures=tex, material=SA_, note="four soft tiers of white rock and pale stone, rounded tip"),
    "CleanIsland_Crystal": P.bounds_entry(o_cry, textures=tex, material=SA_ + " (or Glass / Neon tint for sparkle)",
                                          note="6 clusters of pastel crystals growing out of the ledges; flat-shaded on purpose"),
    "CleanIsland_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                       note="thin light line round the whole rim"),
}, notes="CLEAN POP PLAZA island. Height 0 here = the grass surface = hub y -3: place each mesh at hub (center.x, center.y - 3, "
         "center.z). CleanIsland_Rim replaces the edge of Grass + Frosting; CleanIsland_Under replaces IslandRock x6. The flat "
         "Grass part (cylinder radius 99, top at y = -3) stays; the rim rolls over its edge.")
K.set_mat(o_glow, GLOW)
P.save_blend(os.path.join(K.OUT, "Hub_CleanIsland.blend"), None)

# ------------------------------------------------------------------ previews (with a stand-in lawn and plaza slab on top)
def slab(name, verts_fn, col, rough):
    bm = bmesh.new()
    verts_fn(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    me.materials.append(P.flat_material(name, col, rough))
    return ob


lawn = slab("PreviewLawn", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=98.5, radius2=98.5, depth=1.0,
                                                           matrix=__import__("mathutils").Matrix.Translation((0, 0, -0.5))), "#BFEBD0", 0.6)
plaza = slab("PreviewPlaza", lambda bm: (bmesh.ops.create_cube(bm, size=1.0), bmesh.ops.scale(bm, vec=(112, 112, 3), verts=bm.verts),
                                         bmesh.ops.translate(bm, vec=(0, 0, 1.5), verts=bm.verts)), K.PAL["white"], 0.4)
fl = K.studio((0, 0, -30), 110)
fl.location.z = -75
up = bpy.data.lights.new("UpFill", "AREA")       # stands in for the sky light that reaches the underside in game
up.shape = "DISK"
up.size = 260
up.energy = 1.6e5
upo = bpy.data.objects.new("UpFill", up)
upo.location = (40, 160, -70)
upo.rotation_euler = (Vector((0, 0, -25)) - Vector(upo.location)).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(upo)
show = objs + [lawn, plaza]
P.standard_previews("hub_clean_island", show, block_at=(0, 60, 3), beauty_dir=(0.45, 1.0, 0.16), lens=60, turn_elev=-0.05)
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_island_below.png"), (0, 0, -28), (0.5, 1.0, -0.42), 330, 50, res=(1280, 960))
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_island_closeup.png"), (70, 55, -18), (0.75, 1.0, -0.1), 80, 50, res=(1280, 960))
print("ISLAND done")
