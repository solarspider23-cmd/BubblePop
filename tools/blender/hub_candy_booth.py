# Batch C1: candy booth (tinted) + three roof toppers (Bag / Ticket / Crystal) + booth pad.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_candy_booth.py [-- fast]
#
# Outputs (art/hub_candy/):
#   Hub_Booth.fbx                 Booth_Body (white base, gold band, window, sill, white awning stripes, ridge, mount)
#                                 Booth_Tint (walls + coloured awning stripes; neutral, tinted per booth)
#   Hub_BoothTopper_Bag.fbx       Shop booth topper      (BoothTopper_Bag_Body)
#   Hub_BoothTopper_Ticket.fbx    Passes booth topper    (BoothTopper_Ticket_Body)
#   Hub_BoothTopper_Crystal.fbx   Crystals booth topper  (BoothTopper_Crystal_Body)
#   Hub_BoothPad.fbx              BoothPad_Body (white, flat colour) + BoothPad_Glow (Neon, recoloured)
#   Hub_Booth_color/normal/roughness.png   one 512 set shared by the booth and the toppers
#   *.bounds.json, Hub_Booth.blend
# Previews (art/previews/): hub_candy_booth_{beauty,turn,flat,thumb,eye,colours}.png,
#   hub_candy_toppers.png, hub_candy_boothpad_beauty.png

import math
import os
import sys

import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_candy_common as C  # noqa: E402

C.reset()

W, D, H = 11.7, 9.1, 7.8          # body
ROOF_W, EAVE_Y = 13.0, 5.5        # awning 13 wide, eaves at +-5.5 (11 deep)
NSTRIPE = 7
SW = ROOF_W / NSTRIPE
WIN_W, WIN_H, SILL_Z = 7.8, 3.4, 3.0
FRONT = D / 2


def zc(y):
    """Centre line of the awning (a soft barrel arch, ridge along X)."""
    t = max(-1.0, min(1.0, y / EAVE_Y))
    return 8.95 + 1.3 * (1 - t * t)


MOUNT_TOP = 11.0

# ------------------------------------------------------------------ paints
ts = C.TexSet("Hub_Booth", 512, ao_dist=1.3)


def stitches(P, N):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    s = (x + ROOF_W / 2) / SW
    f = s - np.floor(s)
    dist = np.minimum(f, 1 - f) * SW
    L = np.abs(y) + np.clip(8.95 - z, 0, None) * 1.2
    groove = np.clip(1 - np.abs(dist - 0.3) / 0.07, 0, 1)
    dash = (np.mod(L, 0.62) < 0.38).astype(float)
    h = -0.03 * groove * dash
    return {"h": h}


ts.paint("wall", "tintwhite", rough=0.26, tint=True, ao=0.32, grad=0.05, zref=8)
ts.paint("awn_c", "tintwhite", rough=0.55, tint=True, ao=0.3, grad=0.0, fn=stitches)
ts.paint("awn_w", "cream", rough=0.55, ao=0.35, grad=0.0, fn=stitches)
ts.paint("white", "cream", rough=0.3, ao=0.45, grad=0.05, zref=8)
ts.paint("gold", "gold", rough=0.22, ao=0.4, grad=0.0)


def window_dark(P, N):
    # navy-plum inside, a touch lighter at the top so it reads as a deep opening
    zt = np.clip((P[:, 2] - SILL_Z) / WIN_H, 0, 1)
    base = np.array(C.lin("navy"))
    top = np.array(C.lin("#3A4670"))
    col = base[None, :] * (1 - zt[:, None] * 0.6) + top[None, :] * (zt[:, None] * 0.6)
    return {"col": col}


ts.paint("dark", "navy", rough=0.45, ao=0.3, grad=0.0, fn=window_dark)

# topper paints (zref 3: they are about 3 studs tall)
ts.paint("t_red", "red", rough=0.24, ao=0.4, grad=0.06, zref=3)
ts.paint("t_white", "cream", rough=0.3, ao=0.4, grad=0.04, zref=3)
ts.paint("t_gold", "gold", rough=0.2, ao=0.4, grad=0.04, zref=3)
COIN_C = Vector((0, 0.0, 1.05))


def coin_star(P, N):
    # an embossed star on the bag's gold coin (normal map only)
    u = P[:, 0] - COIN_C.x
    v = P[:, 2] - COIN_C.z
    r = np.hypot(u, v)
    a = np.arctan2(v, u) - math.pi / 2
    k = np.cos(5 * a)
    star_r = 0.24 + 0.1 * (k + 1) / 2 * 1.0
    front = (N[:, 1] > 0.5).astype(float)
    inside = np.clip((star_r - r) / 0.04, 0, 1)
    return {"h": 0.035 * inside * front}


ts.paint("t_coin", "gold", rough=0.18, ao=0.35, grad=0.0, fn=coin_star)
ts.paint("t_ticket", "lemon", rough=0.25, ao=0.4, grad=0.05, zref=3)
TICKET_TILT = math.radians(9)
TICKET_C = Vector((0, 0, 1.62))


def ticket_perf(P, N):
    # a dotted "tear here" line near the right end of the ticket (normal map)
    d = Vector((math.cos(TICKET_TILT), 0, math.sin(TICKET_TILT)))
    e = Vector((-math.sin(TICKET_TILT), 0, math.cos(TICKET_TILT)))
    q = P - np.array(TICKET_C)
    u = q @ np.array(d)
    v = q @ np.array(e)
    face = (np.abs(N[:, 1]) > 0.6).astype(float)
    line = np.clip(1 - np.abs(u - 0.98) / 0.07, 0, 1)
    dots = np.clip(1 - np.abs(np.mod(v + 0.12, 0.3) - 0.15) / 0.09, 0, 1)
    return {"h": -0.03 * line * dots * face}


ts.paint("t_ticket_face", "lemon", rough=0.25, ao=0.4, grad=0.05, zref=3, fn=ticket_perf)
ts.paint("t_star", "red", rough=0.22, ao=0.35, grad=0.0)
LIGHT = np.array([-0.45, 0.65, 0.6]) / np.linalg.norm([-0.45, 0.65, 0.6])


def facets(colors):
    cols = [np.array(C.lin(c)) for c in colors]

    def fn(P, N):
        d = N @ LIGHT
        out = np.where(d[:, None] > 0.45, cols[0], np.where(d[:, None] > -0.05, cols[1], cols[2]))
        return {"col": out}
    return fn


ts.paint("t_crys", "#E650BE", rough=0.12, ao=0.25, grad=0.0, fn=facets(["#FF8CDC", "#DC3CBE", "#9446D8"]))
ts.paint("t_tip", "#6EE6F5", rough=0.12, ao=0.2, grad=0.0, fn=facets(["#DCFAFF", "#78E6F8", "#46AAE6"]))

# ------------------------------------------------------------------ booth
booth = C.Model("Hub_Booth", ts)
booth.zone("Booth_Body", "tex", note="white base, gold band, window, sill, white awning stripes, ridge, topper mount")
booth.zone("Booth_Tint", "tex", note="walls + coloured awning stripes: neutral, set SurfaceAppearance.Color to the booth accent")

# white base band (plinth)
booth.add("Booth_Body", "white", C.rlathe(12.3, 9.7, 1.6, [(0.3, 0.0), (0.06, 0.12), (0.0, 0.4), (0.0, 0.72), (0.08, 0.98), (0.3, 1.08), (0.65, 1.1)], steps=4))
# walls
booth.add("Booth_Tint", "wall", C.rlathe(W, D, 1.3, [(0.0, 0.85), (0.0, 7.3), (0.1, 7.6), (0.35, 7.8), (0.8, 7.85)], steps=4))
# gold trim band under the roof
booth.add("Booth_Body", "gold", C.rlathe(12.2, 9.6, 1.55, [(0.42, 7.5), (0.1, 7.58), (0.0, 7.8), (0.0, 8.32), (0.1, 8.52), (0.35, 8.6), (1.0, 8.62)], steps=4))

# roof core: fills the gable under the arch (white), its ends are the side gables
core = [(-4.75, 8.35), (4.75, 8.35)]
for i in range(9):
    y = 4.75 - 9.5 * i / 8
    core.append((y, zc(y) - 0.12))
booth.add("Booth_Body", "white", C.slab(core, 12.0, bevel=0.25, bsegs=2,
                                        matrix=C.frame_matrix((0, 0, 0), (0, 1, 0), (0, 0, 1))))

# awning: 7 puffy pillow stripes over the arch, each ending in a rounded scallop tab front and back
def pillow_section(a, top, bot, n=8, p=3.0):
    pts = []
    for i in range(n):
        ang = 2 * math.pi * (i + 0.5) / n
        c, s = math.cos(ang), math.sin(ang)
        u = a * math.copysign(abs(c) ** (2 / p), c)
        v = (top if s > 0 else bot) * math.copysign(abs(s) ** (2 / p), s)
        pts.append((u, v))
    return pts


def stripe_frames(x):
    """Points along one stripe: front tab tip -> arch -> back tab tip, with section scales."""
    ye, ze = EAVE_Y, zc(EAVE_Y)
    tab = [((x, ye + 0.36, ze - 0.78), (0.42, 0.6)), ((x, ye + 0.3, ze - 0.5), (0.8, 0.85)), ((x, ye + 0.18, ze - 0.2), (0.96, 0.95))]
    arch = []
    n = 11
    for i in range(n):
        y = EAVE_Y - 2 * EAVE_Y * i / (n - 1)
        puff = 1.0 + 0.12 * math.sin(math.pi * i / (n - 1))  # a little fatter in the middle
        arch.append(((x, y, zc(y)), (1.0, puff)))
    back = [((x, -p[1], p[2]), s) for (p, s) in reversed(tab)]
    seq = tab + arch + back
    pts = [Vector(p) for p, _ in seq]
    U = Vector((1, 0, 0))
    frames = []
    for i, (p, (su, sv)) in enumerate(seq):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        V = t.cross(U).normalized()
        frames.append((pts[i], U * su, V * sv))
    return frames


sec = pillow_section(SW / 2 * 1.05, 0.34, 0.2, n=8, p=3.0)
for k in range(NSTRIPE):
    x = -ROOF_W / 2 + (k + 0.5) * SW
    coloured = k % 2 == 0
    booth.add("Booth_Tint" if coloured else "Booth_Body", "awn_c" if coloured else "awn_w", C.sweep(sec, stripe_frames(x)))

# ridge roll and the topper mount
ridge_z = zc(0) + 0.22
booth.add("Booth_Body", "white", C.tube([(-6.15, 0, ridge_z), (0, 0, ridge_z), (6.15, 0, ridge_z)], 0.44, segs=10, cap_rings=2))
booth.add("Booth_Body", "gold", C.lathe([(0.8, ridge_z), (0.98, 10.6), (1.0, 10.78), (0.88, 10.96), (0.6, MOUNT_TOP), (0.0, MOUNT_TOP)], segs=16, caps=(True, False)))

# serving window: navy-plum inside, thick rounded white frame, chunky counter sill
WIN_CZ = SILL_Z + WIN_H / 2
booth.add("Booth_Body", "dark", C.slab(C.rrect_pts(WIN_W + 0.3, WIN_H + 0.3, 0.6, 3), 0.2, bevel=0.0,
                                       matrix=C.frame_matrix((0, FRONT - 0.03, WIN_CZ), (1, 0, 0), (0, 0, 1))))
path = [Vector((x, FRONT, z + WIN_CZ)) for x, z in C.rrect_pts(WIN_W + 0.75, WIN_H + 0.75, 0.75, 3)]
fsec = pillow_section(0.4, 0.5, 0.3, n=8, p=3.2)
frames = []
for i, p in enumerate(path):
    t = (path[(i + 1) % len(path)] - path[i - 1]).normalized()
    V = Vector((0, 1, 0))
    U = t.cross(V).normalized()
    frames.append((p + Vector((0, 0.05, 0)), U, V))
booth.add("Booth_Body", "white", C.sweep(fsec, frames, closed_path=True))
booth.add("Booth_Body", "white", C.rbox((WIN_W + 1.6, 1.7, 0.6), (0, FRONT + 0.55, SILL_Z - 0.22), r=0.24, segs=2))

booth.extra = {
    "replaces": "Hub.lua buildBooths(): BoothBody, BoothTrim, BoothWindow, BoothSill, Awning x5, RoofTop (and RoofBall -> topper)",
    "placement": "one per HubConfig.booths entry (right side, x=44, z=-15/4/23), front (+Y here) faces the plaza middle; built at final size (boothScale 1.3 already included)",
    "tints": {"pink": "#FF69AA", "mint": "#46CDA5", "lemon": "#F5B928"},
    "topperMount": {"position": [0, MOUNT_TOP, 0], "note": "put the topper model's origin (bottom centre) here"},
    "window": {"opening": [WIN_W, WIN_H], "sillHeight": SILL_Z, "frontFaceZ": -FRONT},
    "boothPad": {"position": [0, 0, -(FRONT + 5.2)], "note": "Hub_BoothPad centre, in front of the window"},
}

# ------------------------------------------------------------------ toppers (origin = bottom centre, sits on the mount)
def puck(m, zone, paint, r, h, segs=16):
    m.add(zone, paint, C.lathe([(r * 0.94, 0.0), (r, h * 0.35), (r * 0.92, h * 0.85), (r * 0.7, h), (0.0, h)], segs=segs, caps=(True, False)))


bag = C.Model("Hub_BoothTopper_Bag", ts)
bag.zone("BoothTopper_Bag_Body", "tex")
Z = "BoothTopper_Bag_Body"
bag.add(Z, "t_red", C.rlathe(2.3, 1.35, 0.36, [(0.16, 0.0), (0.05, 0.08), (0.03, 0.3), (0.0, 1.95), (0.3, 1.97)], steps=2))
bag.add(Z, "t_white", C.rlathe(2.46, 1.5, 0.42, [(0.1, 1.62), (0.0, 1.72), (0.0, 2.02), (0.08, 2.14), (0.25, 2.17), (0.45, 2.17)], steps=2))
for sy in (-0.42, 0.42):
    pts = []
    for i in range(7):
        a = math.pi * i / 6
        pts.append((-0.55 * math.cos(a), sy, 2.05 + 0.85 * math.sin(a)))
    bag.add(Z, "t_gold", C.tube(pts, 0.2, segs=6, caps="flat"))
coin = C.lathe([(0.66, 0.0), (0.7, 0.07), (0.64, 0.17), (0.5, 0.2), (0.0, 0.2)], segs=16, caps=(False, False))
import bmesh  # noqa: E402
bmesh.ops.rotate(coin, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"), verts=coin.verts)
bmesh.ops.translate(coin, vec=Vector((0, 0.66, COIN_C.z)), verts=coin.verts)
COIN_C.y = 0.66
bag.add(Z, "t_coin", coin, closed=False)
bag.extra = {"replaces": "RoofBall on the Shop booth", "mountOn": "Hub_Booth topperMount"}

ticket = C.Model("Hub_BoothTopper_Ticket", ts)
ticket.zone("BoothTopper_Ticket_Body", "tex")
Z = "BoothTopper_Ticket_Body"
puck(ticket, Z, "t_gold", 0.85, 0.32, segs=12)
ticket.add(Z, "t_gold", C.lathe([(0.3, 0.2), (0.3, 0.8), (0.22, 0.9), (0.0, 0.9)], segs=10, caps=(False, False)))
# outline: rounded ticket with round notches in the two short sides
TW, TH, TR, NR = 3.2, 2.1, 0.38, 0.36
o = []
base = C.rrect_pts(TW, TH, TR, 2)
per = len(base) // 4
corners = [base[i * per:(i + 1) * per] for i in range(4)]  # TR, TL, BL, BR (counter-clockwise)
o += corners[0] + corners[1]
o += [(-TW / 2 + NR * math.cos(a), NR * math.sin(a)) for a in np.radians([90, 45, 0, -45, -90])]
o += corners[2] + corners[3]
o += [(TW / 2 + NR * math.cos(a), NR * math.sin(a)) for a in np.radians([270, 225, 180, 135, 90])]
tx = Vector((math.cos(TICKET_TILT), 0, math.sin(TICKET_TILT)))
tz = Vector((-math.sin(TICKET_TILT), 0, math.cos(TICKET_TILT)))
ticket.add(Z, "t_ticket_face", C.slab(o, 0.5, bevel=0.1, bsegs=2, matrix=C.frame_matrix(TICKET_C, tx, tz)))
ticket.add(Z, "t_star", C.slab(C.star_outline(0.8, 0.42, round_tips=0.13), 0.3, bevel=0.07, bsegs=2,
                               matrix=C.frame_matrix(TICKET_C + Vector((0, 0.3, 0)) - tx * 0.25, tx, tz)))
ticket.extra = {"replaces": "RoofBall on the Passes booth", "mountOn": "Hub_Booth topperMount"}

crys = C.Model("Hub_BoothTopper_Crystal", ts)
crys.zone("BoothTopper_Crystal_Body", "tex")
Z = "BoothTopper_Crystal_Body"
puck(crys, Z, "t_gold", 0.95, 0.38)


def crystal(m, r, h, tip, rot_y, rot_z, at):
    body = C.lathe([(r * 0.82, 0.0), (r, h)], segs=6, caps=(True, False), smooth=False)
    point = C.lathe([(r, h), (0.0, h + tip)], segs=6, caps=(False, False), smooth=False)
    mat = Matrix.Translation(Vector(at)) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Rotation(rot_y, 4, "Y")
    for b in (body, point):
        bmesh.ops.transform(b, matrix=mat, verts=b.verts)
    m.add(Z, "t_crys", body)
    m.add(Z, "t_tip", point, closed=False)


crystal(crys, 0.62, 1.85, 0.95, 0.0, math.radians(30), (0, 0, 0.15))
crystal(crys, 0.42, 1.0, 0.62, math.radians(-32), math.radians(10), (-0.42, 0.05, 0.2))
crystal(crys, 0.4, 0.85, 0.58, math.radians(30), math.radians(-14), (0.45, 0.12, 0.2))
crys.extra = {"replaces": "RoofBall on the Crystals booth", "mountOn": "Hub_Booth topperMount"}

# ------------------------------------------------------------------ booth pad (flat colours)
pad = C.Model("Hub_BoothPad")
pad.zone("BoothPad_Body", "flat", color="cream", rough=0.3)
pad.zone("BoothPad_Glow", "glow", color="glowpink", emit=3.0,
         note="Neon; recolour per booth: pink #BE1E5A, mint #1E9C78, lemon #C88C0A")
pad.zones["BoothPad_Glow"]["tint_glow"] = True
SEG = 26
pad.add("BoothPad_Body", None, C.lathe([(4.55, 0.0), (4.42, 0.24), (4.18, 0.35), (3.95, 0.25)], segs=SEG, caps=(False, False)), closed=False)
pad.add("BoothPad_Body", None, C.lathe([(3.32, 0.24), (3.22, 0.35), (3.22, 0.35), (0.0, 0.35)], segs=SEG, caps=(False, False)), closed=False)
pad.add("BoothPad_Glow", None, C.lathe([(4.02, 0.28), (3.28, 0.28)], segs=SEG, caps=(False, False)), closed=False)
pad.extra = {"replaces": "Hub.lua buildBooths(): BoothPadRing, BoothPad", "placement": "in front of each booth, centre 5.2 studs in front of the booth front (Hub_Booth boothPad)"}

models = [booth, bag, ticket, crys, pad]
totals = C.build(models)

# ------------------------------------------------------------------ previews
import bpy  # noqa: E402
if C.NOPREV:
    sys.exit(0)
C.studio()
for o in pad.objects:
    o.location = (0, FRONT + 5.2, 0)
for o in bag.objects:
    o.location = (0, 0, MOUNT_TOP)
C.standard_previews(booth, "hub_candy_booth", extra_objs=[z["obj"] for z in pad.zones.values()] + [z["obj"] for z in bag.zones.values()],
                    block_at=(-8.0, 6.5, 0), tint="#FF69AA")
for o in pad.objects + bag.objects:
    o.location = (0, 0, 0)

# colour variants: the three booths in a row with their toppers and pads
row = []
specs = [("lemon", "#F5B928", "#C88C0A", crys), ("mint", "#46CDA5", "#1E9C78", ticket), ("pink", "#FF69AA", "#BE1E5A", bag)]
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "MESH" and o.name != "studio_floor":
        o.hide_render = True
for k, (nm, accent, glow, top) in enumerate(specs):
    dx = (k - 1) * 16.0
    for src in booth.objects + pad.objects + top.objects:
        cp = src.copy()
        cp.data = src.data.copy()
        sc.collection.objects.link(cp)
        cp.hide_render = False
        cp.location = (dx, 0, 0)
        if src in pad.objects:
            cp.location = (dx, FRONT + 5.2, 0)
        if src in top.objects:
            cp.location = (dx, 0, MOUNT_TOP)
        cp.data.materials.clear()
        if src.name == "Booth_Tint":
            cp.data.materials.append(C.tex_material(ts, "tint_" + nm, C.lin(accent)))
        elif src.name == "BoothPad_Glow":
            cp.data.materials.append(C.flat_material("glow_" + nm, glow, "glow", emit=3.0))
        elif src.name == "BoothPad_Body":
            cp.data.materials.append(C.flat_material("padw_" + nm, "cream", "flat"))
        else:
            cp.data.materials.append(C.tex_material(ts, "body_" + nm + src.name))
        row.append(cp)
blk = C.player_block((27.5, 8, 0))
lo, hi = C.model_bounds(row + [blk])
ls = C.lights((hi - lo).length / 2)
cam = C.camera()
pos, mid = C.frame_shot(lo, hi, (0.0, 1.0, 0.38), 50, pad=1.0)
C.shoot(os.path.join(C.PREV, "hub_candy_booth_colours.png"), pos, mid, 50, (1280, 960))
for o in row + ls + [cam, blk]:
    bpy.data.objects.remove(o)

# toppers close-up (all three side by side) and the booth pad
for o in sc.objects:
    if o.type == "MESH" and o.name != "studio_floor":
        o.hide_render = True
show = []
for k, m in enumerate((bag, ticket, crys)):
    for o in m.objects:
        o.location = ((k - 1) * 4.2, 0, 0)
        o.hide_render = False
        show.append(o)
lo, hi = C.model_bounds(show)
ls = C.lights(4)
cam = C.camera()
pos, mid = C.frame_shot(lo, hi, (0.3, 1.0, 0.3), 60, pad=1.15)
C.shoot(os.path.join(C.PREV, "hub_candy_toppers.png"), pos, mid, 60, (1280, 800))
for o in show:
    o.location = (0, 0, 0)
    o.hide_render = True
for o in ls + [cam]:
    bpy.data.objects.remove(o)
for o in pad.objects:
    o.hide_render = False
lo, hi = C.model_bounds(pad.objects)
ls = C.lights(5)
cam = C.camera()
pos, mid = C.frame_shot(lo, hi, (0.4, 1.0, 0.7), 50, pad=1.0)
C.shoot(os.path.join(C.PREV, "hub_candy_boothpad_beauty.png"), pos, mid, 50, (1200, 900))
for o in ls + [cam]:
    bpy.data.objects.remove(o)
for o in sc.objects:
    if o.type == "MESH":
        o.hide_render = False

C.save_blend("Hub_Booth", models)
print("BOOTH TOTALS", totals)
