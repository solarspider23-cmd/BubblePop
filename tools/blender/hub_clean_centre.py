# CLEAN POP PLAZA 1a: the hero centrepiece. A giant glass bubble held in a sculpted white tulip
# pedestal on a round stage, small pastel bubbles floating inside it, one slim orbit ring.
# Replaces the gumball machine (same footprint: 28 across, about 44 tall).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_clean_centre.py
#
# Outputs (art/hub_clean/): Hub_CleanCentre.fbx with
#   CleanCentre_Body  (stage, pedestal, waist band, collar; fixed colours, 1024 texture set)
#   CleanCentre_Core  (the pastel bubbles inside the glass; fixed colours; may bob / turn in game)
#   CleanCentre_Ring  (orbit ring with 3 small bubbles; may spin in game)
#   CleanCentre_Glass (the giant bubble; Roblox Glass, no texture)
#   CleanCentre_Shine (white highlight on the bubble; flat white)
#   CleanCentre_Glow  (ring set in the stage + ring under the bubble; Neon)
#   Hub_CleanCentre_color/_normal/_roughness.png (1024), .blend, .bounds.json, previews hub_clean_centre_*.png

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
from mathutils import Vector  # noqa: E402

P = K.P
TEX = 1024
sc = K.reset()

BR, BZ = 12.5, 31.5            # bubble radius and centre height
RING_R, RING_TILT = 13.9, math.radians(16)


def zb(rho):
    """Height of the bubble's underside at radius rho."""
    return BZ - math.sqrt(BR * BR - rho * rho)


# ------------------------------------------------------------------ zone materials
Z = {
    "stage_top": K.zone("stage_top", K.PAL["white"], 0.42, ao=0.3, ao_dist=3.0, grad=0.0),
    "stage_side": K.zone("stage_side", K.vgrad(K.PAL["grey"], K.PAL["white"], 0.0, 1.3), 0.22, ao=0.2, ao_dist=1.5, grad=0.0),
    "stage_band": K.zone("stage_band", K.PAL["sky"], 0.18, ao=0.25, ao_dist=0.6, grad=0.0),
    "groove": K.zone("groove", K.PAL["grey"], 0.45, ao=0.45, ao_dist=0.8, grad=0.0),
    "ped": K.zone("ped", K.vgrad("#E3EBF8", K.PAL["white"], 2.0, 17.0), 0.2, ao=0.3, ao_dist=4.0, grad=0.0),
    "band": K.zone("band", K.vgrad(K.PAL["bluedeep"], K.PAL["blue"], 9.2, 11.0), 0.12, ao=0.2, ao_dist=1.0, grad=0.0),
    "collar": K.zone("collar", K.vgrad(K.PAL["sky"], "#D6ECFF", 19.0, 22.5), 0.2, ao=0.25, ao_dist=2.0, grad=0.0),
    "ring": K.zone("ring", K.PAL["white"], 0.3, ao=0.15, ao_dist=1.0, grad=0.0),
}
CORE = [  # offset from the bubble centre, radius, colour
    ((-2.5, 1.0, -3.5), 4.2, "blue"),
    ((4.2, -1.5, 1.0), 3.0, "mint"),
    ((-3.8, -2.0, 3.8), 2.4, "lilac"),
    ((1.5, 3.5, 5.5), 1.8, "peach"),
    ((5.0, 3.0, -4.5), 1.6, "sky"),
]
for nm in ("blue", "mint", "lilac", "peach", "sky", "white"):
    Z["b_" + nm] = K.zone("b_" + nm, K.PAL[nm], 0.12, ao=0.18, ao_dist=3.0, grad=0.0)

# ------------------------------------------------------------------ body
body = P.MeshBuilder("CleanCentre_Body")
SEG = 56
circ = lambda d: P.circle2d(d, SEG, turn=math.pi / SEG)
# stage: 28 across, 1.5 high, a pastel band let into the side, a glow groove near the edge
prof = K.arc_pts(13.7, 0.3, 0.3, -90, 0, 2)
prof += [(14.0, 0.5), (13.86, 0.58, "stage_band"), (13.86, 0.92), (14.0, 1.0, "stage_side")]
prof += [(q[0], q[1]) for q in K.arc_pts(13.6, 1.1, 0.4, 0, 90, 3)]
prof[-1] = (13.6, 1.5, "stage_top")
prof += [(12.75, 1.5), (12.62, 1.38, "groove"), (11.98, 1.38), (11.85, 1.5, "stage_top"), (10.0, 1.5)]
# a low plinth under the pedestal (a second soft step)
prof += [(q[0], q[1], "stage_side") for q in K.arc_pts(9.55, 1.75, 0.45, -20, 90, 3)]
prof += [(8.0, 2.2)]
body.lathe(prof, circ, zone="stage_side")

# pedestal: a tulip. Radius by height from a smooth curve, soft flutes fading in towards the cup.
KEY = [(2.2, 8.35), (2.9, 8.3), (3.8, 7.3), (5.5, 5.6), (7.8, 4.25), (10.2, 3.75), (12.8, 4.15),
       (15.4, 5.45), (18.0, 7.25), (19.6, 8.2), (20.6, 8.75)]


def catmull(pts, per=3):
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n - 1)]
        for s in range(per):
            t = s / per
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)))
    out.append(pts[-1])
    return out


PSEG, LOBES = 40, 8
curve = catmull(KEY, 3)


def sstep(x, a, b):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def flute(z):
    return 0.085 * sstep(z, 11.5, 16.5) * (1 - sstep(z, 18.6, 20.6))


def ped_ring(r, z, amp=0.0):
    pts = []
    for i in range(PSEG):
        a = 2 * math.pi * i / PSEG
        rr = r * (1 + amp * math.cos(LOBES * a))
        pts.append((rr * math.cos(a), rr * math.sin(a), z))
    return pts


rings = [ped_ring(r, z, flute(z)) for z, r in curve]
zones = ["ped"] * (len(rings) - 1)
# a glow groove under the rolled rim, the rim, then the pastel collar the bubble sits in and the dish under it
TOP = [(8.95, 21.0, "ped"), (8.78, 21.06, "groove"), (8.9, 21.54, "ped"), (9.1, 21.6, "ped"), (9.3, 22.0, "ped"),
       (9.32, 22.45, "ped"), (9.15, 22.78, "ped"), (8.9, 22.88, "collar"), (8.7, 22.8, "collar"),
       (8.5, zb(8.5) - 0.12, "collar"), (7.4, zb(7.4) - 0.3, "collar"), (6.0, zb(6.0) - 0.45, "collar"),
       (4.4, zb(4.4) - 0.6, "collar"), (2.6, zb(2.6) - 0.7, "collar")]
prev = "ped"
for r, z, zn in TOP:
    rings.append(ped_ring(r, z))
    zones.append(prev)
    prev = zn
K.loft(body, rings, zones=zones)
body.lathe([(2.6, zb(2.6) - 0.7), (0.0, zb(0) - 0.75)], lambda d: P.circle2d(d, PSEG), zone="collar")
# waist band: a glossy bubble-blue bracelet clipped round the narrowest point
body.lathe([(3.72, 9.25), (4.22, 9.35), (4.42, 9.75), (4.45, 10.2), (4.42, 10.65), (4.22, 11.05), (3.9, 11.15)],
           lambda d: P.circle2d(d, PSEG), zone="band")

# ------------------------------------------------------------------ bubbles inside the glass
core = P.MeshBuilder("CleanCentre_Core")
for off, r, nm in CORE:
    c = Vector((0, 0, BZ)) + Vector(off)
    K.sphere(core, c, r, 20 if r > 2.5 else 14, 10 if r > 2.5 else 8, zone="b_" + nm)

# ------------------------------------------------------------------ orbit ring (tilted, spins about its own axis)
ring = P.MeshBuilder("CleanCentre_Ring")
ru = Vector((math.cos(RING_TILT), 0, math.sin(RING_TILT)))
rv = Vector((0, 1, 0))
rfr = P.frame((0, 0, BZ), ru, rv)
K.torus(ring, None, RING_R, 0.7, 64, 8, zone="ring", fr=rfr, squash=0.85)
BEADS = [(25, 1.9, "sky"), (150, 1.45, "peach"), (265, 1.65, "mint")]
for ang, r, nm in BEADS:
    a = math.radians(ang)
    c = Vector((0, 0, BZ)) + ru * RING_R * math.cos(a) + rv * RING_R * math.sin(a)
    K.sphere(ring, c, r, 14, 8, zone="b_" + nm)

mats = dict(Z)
o_body, o_core, o_ring = body.build(mats), core.build(mats), ring.build(mats)
textured = [o_body, o_core, o_ring]
P.unwrap(textured, margin=0.004)
fin, maps = P.bake_set("Hub_CleanCentre", textured, TEX)

# ------------------------------------------------------------------ glass, shine, glow (no textures)
GLASS = K.glass_material("CleanGlass")
WHITE = P.flat_material("CleanShine", "#FFFFFF", 0.3, emit=1.2)
GLOW = P.flat_material("CleanGlow", K.PAL["glow"], 0.3, emit=5.0)
flat = {"glass": GLASS, "shine": WHITE, "glow": GLOW}

glass = P.MeshBuilder("CleanCentre_Glass")
K.sphere(glass, (0, 0, BZ), BR, 48, 22, zone="glass")
o_glass = glass.build(flat)


def patch(mb, az0, el0, outline, r, levels=(1.0, 0.62, 0.28), centre=(0.0, 0.0)):
    """A thin curved decal on the bubble: 2D outline (studs, in the tangent plane) wrapped on the sphere."""
    def pt(u, v):
        el = el0 + v / r
        az = az0 + u / (r * math.cos(el0))
        return Vector((r * math.cos(el) * math.sin(az), r * math.cos(el) * math.cos(az), BZ + r * math.sin(el)))
    rows = []
    for s in levels:
        rows.append([mb.bm.verts.new(pt(centre[0] + (u - centre[0]) * s, centre[1] + (v - centre[1]) * s)) for u, v in outline])
    n = len(outline)
    for a, b in zip(rows, rows[1:]):
        for j in range(n):
            k = (j + 1) % n
            mb.face((a[j], a[k], b[k], b[j]), "shine")
    cv = mb.bm.verts.new(pt(*centre))
    for j in range(n):
        mb.face((rows[-1][j], rows[-1][(j + 1) % n], cv), "shine")


def pill2d(length, width, tilt_deg, n=6):
    h = (length - width) / 2
    pts = [(width / 2 * math.cos(math.radians(a)), h + width / 2 * math.sin(math.radians(a))) for a in [180 * i / n for i in range(n + 1)]]
    pts += [(-x, -y) for x, y in pts]
    t = math.radians(tilt_deg)
    return [(x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)) for x, y in pts]


shine = P.MeshBuilder("CleanCentre_Shine")
SR = BR + 0.12
patch(shine, math.radians(-30), math.radians(36), pill2d(6.4, 2.3, -24), SR)
patch(shine, math.radians(-12), math.radians(15), pill2d(1.7, 1.7, 0, 5), SR)
o_shine = shine.build(flat, weighted=False)
# make sure the decal faces outwards
me = o_shine.data
if sum((p.normal.dot(p.center - Vector((0, 0, BZ))) for p in me.polygons)) < 0:
    me.flip_normals()

glow = P.MeshBuilder("CleanCentre_Glow")
gc = lambda d: P.circle2d(d, 48)
glow.lathe([(12.56, 1.45), (12.04, 1.45)], gc, zone="glow")
glow.lathe([(8.87, 21.1), (8.99, 21.5)], gc, zone="glow")
o_glow = glow.build(flat, weighted=False)
for o in (o_glass, o_shine, o_glow):
    P.unwrap([o], margin=0.02)

allobjs = [o_body, o_core, o_ring, o_glass, o_shine, o_glow]
print("[Hub_CleanCentre] triangles")
total = P.report(allobjs, {"CleanCentre_Body": 10000, "CleanCentre_Glow": 200})
print(f"  budget 8000-12000: {'OK' if total <= 12000 else 'OVER'}")
K.backface_report("CleanCentre", [o_body, o_core, o_ring, o_shine, o_glow])

# ------------------------------------------------------------------ export + bounds
P.export_fbx(os.path.join(K.OUT, "Hub_CleanCentre.fbx"), allobjs)
tex = K.tex_names("Hub_CleanCentre")
axis = [round(-math.sin(RING_TILT), 4), round(math.cos(RING_TILT), 4), 0.0]
P.write_bounds(os.path.join(K.OUT, "Hub_CleanCentre.bounds.json"), {
    "_size": [30.0, round(BZ + BR, 2), 29.8],
    "_tris_total": total,
    "CleanCentre_Body": P.bounds_entry(o_body, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                       note="stage (walkable flat top at 1.5), tulip pedestal, blue waist band, pastel collar"),
    "CleanCentre_Core": P.bounds_entry(o_core, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                       note="5 solid pastel bubbles inside the glass; optional slow bob / turn about the bubble centre",
                                       spin={"point": [0, BZ, 0], "axis": [0, 1, 0]}),
    "CleanCentre_Ring": P.bounds_entry(o_ring, textures=tex, tint=None, material="SmoothPlastic (SurfaceAppearance)",
                                       note="orbit ring with 3 small bubbles; optional slow spin about its own (tilted) axis",
                                       spin={"point": [0, BZ, 0], "axis": axis}),
    "CleanCentre_Glass": P.bounds_entry(o_glass, textures=None, material="Glass", color=[190, 228, 255], transparency=0.45,
                                        castShadow=False, note="the giant bubble: sphere radius 12.5, centre height 31.5"),
    "CleanCentre_Shine": P.bounds_entry(o_shine, textures=None, material="SmoothPlastic (or Neon)", color=[255, 255, 255],
                                        castShadow=False, note="thin one-sided white highlight on the bubble, front left"),
    "CleanCentre_Glow": P.bounds_entry(o_glow, textures=None, material="Neon", color=K.rgb255(K.PAL["glow"]), castShadow=False,
                                       note="ring in the stage groove + ring in the groove under the cup rim"),
}, notes="CLEAN POP PLAZA hero. Replaces everything in Hub.lua buildGumballMachine() except the logo (MachineStage .. GlobeKnob "
         "and the gumballs). Origin = centre of the stage on the plaza floor: hub (0, 0, -45), front (+Y here = Roblox -Z after "
         "the usual lookAt) facing the spawn. Stage 28 across x 1.5 high (keep an invisible cylinder for walking), pedestal up "
         "to 22.6, bubble 25 across centred at height 31.5 (top 44). The orbit ring with its bubbles is about 30 across.")

set_glow = [o_glow]
P.save_blend(os.path.join(K.OUT, "Hub_CleanCentre.blend"), None)

# ------------------------------------------------------------------ previews
K.studio((0, 0, 20), 26)
P.standard_previews("hub_clean_centre", allobjs, block_at=(17.5, 6, 0), beauty_dir=(0.5, 1.0, 0.42), lens=60)
# what a player sees walking up to it (eye height 5, from the spawn side)
if not K.FAST: P.shoot(os.path.join(K.PREV, "hub_clean_centre_eye.png"), (0, 0, 21), Vector((0.25, 1, 0)) + Vector((0, 0, -0.22)), 62, 32,
        res=(960, 960))
print("CENTRE done")
