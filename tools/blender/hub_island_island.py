# Batch D1: the sky island as "a slice of cake in the sky" (docs/art_plan.md, BATCH D).
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_island_island.py
#   (ISLAND_QUICK=1 for fast low-sample renders while iterating)
#
# Builds, from an empty scene:
#   Island_Rim   soft rounded grass lip + a fat pink frosting band with drips of different
#                lengths running down the chocolate (the hero detail)
#   Island_Under smooth milk chocolate underside: 4 soft rounded tiers like an upside-down
#                cake, ending in a rounded tip 58 studs below the grass
# Both share one 1024 texture set (colour / roughness / OpenGL normal), baked from procedural
# materials. The flat grass disc players walk on stays a Roblox part (radius 99, top at hub
# y = -3); these meshes wrap around its edge and hang under it.
#
# Blender height 0 = the grass surface (hub y = -3). Front = +Y (the model is round anyway).
#
# Outputs (art/hub_island/): Hub_Island.fbx, Hub_Island_color/_normal/_roughness.png,
#   Hub_Island.blend, Hub_Island.bounds.json
# Previews (art/previews/): hub_island_island_beauty/_turn/_flat/_thumb.png

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import hub_island_common as C  # noqa: E402

NAME = "Hub_Island"
TEX = 1024
RIM_SEGS, RIM_SECTORS = 72, 8          # around; the texture repeats once per sector (45 degrees)
CHOC_SEGS, CHOC_SECTORS = 48, 8
GRASS_R = 99.0                          # the Roblox grass disc (radius 99, 5 thick)

# ------------------------------------------------------------------ profiles (r, z)
# walk each one top -> outside -> bottom so the faces point out
LIP = [  # grass lip: starts under the grass disc, rolls over its edge, tucks under
    (94.0, -0.35), (96.0, 0.22), (98.4, 0.52), (100.3, 0.24),
    (101.15, -0.45), (101.4, -1.25), (101.05, -1.95), (100.35, -2.3),
]
FROST = [  # pillowy frosting band, starts tucked under the lip, ends tucked into the chocolate
    (100.1, -1.95), (101.0, -2.45), (101.85, -3.3), (102.15, -4.7),
    (101.85, -6.2), (101.05, -7.2), (100.15, -7.55), (98.9, -7.45),
]
TIERS = [  # (radius, top z, bottom z): an upside-down tiered cake, each tier a puffy rounded ring
    (99.6, -4.0, -19.6), (86.5, -20.2, -32.0), (70.0, -32.6, -42.2), (51.0, -42.8, -50.2), (30.0, -50.8, None),
]
TIP_Z = -59.0


def round_poly(ctrl):
    """ctrl [(r, z, corner_radius, steps)] -> smooth profile: each corner replaced by a
    quadratic curve (steps + 1 points); radius 0 keeps the point as it is."""
    out = []
    pts = [Vector((c[0], c[1])) for c in ctrl]
    for i, c in enumerate(ctrl):
        P = pts[i]
        if i in (0, len(ctrl) - 1) or c[2] <= 0:
            out.append((P.x, P.y))
            continue
        A, B = pts[i - 1], pts[i + 1]
        rad = min(c[2], (A - P).length * 0.49, (B - P).length * 0.49)
        p0, p1 = P + (A - P).normalized() * rad, P + (B - P).normalized() * rad
        n = c[3]
        for k in range(n + 1):
            t = k / n
            q = (1 - t) ** 2 * p0 + 2 * t * (1 - t) * P + t * t * p1
            out.append((q.x, q.y))
    return out


def choc_profile():
    ctrl = [(98.7, -4.0, 0, 0)]
    for k, (R, zt, zb) in enumerate(TIERS):
        if k == 0:
            ctrl.append((R, -9.0, 8.0, 2))                 # gentle barrel under the drips
        else:
            ctrl.append((R - 2.6, zt, 1.1, 1))             # groove where two tiers meet
            ctrl.append((R, zt - 2.4, 2.2, 2))             # puffy shoulder
        if zb is not None:
            ctrl.append((R - 0.7, zb, min(4.2, (zb - zt) / -2.6), 2))  # rounded bottom edge
    R = TIERS[-1][0]
    ctrl.append((R * 0.55, TIP_Z + 0.9, 6.0, 2))
    ctrl.append((0.0, TIP_Z, 0, 0))
    return round_poly(ctrl)


CHOC = choc_profile()

# ------------------------------------------------------------------ atlas (u0, v0, u1, v1)
UV_LIP = (0.004, 0.878, 0.996, 0.996)
UV_FROST = (0.004, 0.752, 0.996, 0.868)
UV_CHOC = (0.004, 0.004, 0.494, 0.736)
UV_DRIPS = (0.512, 0.006, 0.994, 0.736)


def plen(profile):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(profile, profile[1:]))


def wall_r(z):
    """Radius of the chocolate wall at height z (first tier only), as the lathe draws it
    between ring points (the polygon's flat sides are a hair inside: cos(pi/segs))."""
    for (ra, za), (rb, zb) in zip(CHOC, CHOC[1:]):
        if zb <= z <= za:
            t = (za - z) / (za - zb) if za != zb else 0.0
            return (ra + (rb - ra) * t) * math.cos(math.pi / CHOC_SEGS)
    return CHOC[-1][0] * math.cos(math.pi / CHOC_SEGS)


# ------------------------------------------------------------------ drips
def make_drips(rng, count=44):
    drips = []
    # lengths cycle long / short / medium with jitter so neighbours always differ
    pattern = [0.95, 0.3, 0.7, 0.12, 0.85, 0.45, 1.0, 0.25, 0.6, 0.38]
    for i in range(count):
        ang = 2 * math.pi * (i + rng.uniform(-0.2, 0.2)) / count
        f = pattern[i % len(pattern)] * rng.uniform(0.88, 1.08)
        L = 1.8 + 8.6 * min(f, 1.0)              # 1.8 .. 10.4 below the band
        a0 = rng.uniform(2.0, 2.6) + 0.45 * f    # half width
        b0 = rng.uniform(1.25, 1.45)             # thickness off the wall
        drips.append((ang, L, a0, b0))
    return drips


def drip_rows(L, a0, b0):
    """Rows (z, half width, thickness) down one drip, last row is the tip. The top flares
    out where it leaves the frosting band, like a real drip of icing."""
    z_top, z_e = -6.0, -7.45
    z_tip = z_e - L
    rv = min(a0 * 1.0, L * 0.6)
    zc = z_tip + rv
    rows = [(z_top, a0 * 1.6, b0 * 0.75), (z_e, a0 * 1.45, b0 * 0.85)]
    if zc < z_e - 2.2:
        rows.append((z_e - 1.0, a0 * 1.0, b0 * 0.95))
        rows.append(((z_e - 1.0 + zc) / 2, a0 * 0.9, b0 * 0.95))
    elif zc < z_e - 0.6:
        rows.append(((z_e + zc) / 2, a0 * 0.98, b0 * 0.95))
    rows.append((zc, a0 * 1.04, b0 * 1.05))
    ab, bb = rows[-1][1], rows[-1][2]
    for psi in (40, 70):
        p = math.radians(psi)
        rows.append((zc - rv * math.sin(p), ab * math.cos(p), bb * math.cos(p) ** 0.55))
    rows.append((z_tip, 0.0, 0.0))
    return rows


def build_drips(b, drips):
    K = 4
    islands = []
    for ang, L, a0, b0 in drips:
        rows = drip_rows(L, a0, b0)
        width = math.pi / 2 * (max(r[1] for r in rows) + max(r[2] for r in rows)) * 1.0
        height = rows[0][0] - rows[-1][0]
        islands.append((width, height))
    # shelf-pack the islands into UV_DRIPS at a fixed texel density
    u0, v0, u1, v1 = UV_DRIPS
    gap = 7 / TEX
    dens = 9.6 / TEX                         # UV per stud
    while True:
        places, x, y, shelf_h, ok = [], u0, v0, 0.0, True
        order = sorted(range(len(islands)), key=lambda k: -islands[k][1])
        pos = {}
        for k in order:
            w, h = islands[k][0] * dens, islands[k][1] * dens
            if x + w > u1:
                x, y, shelf_h = u0, y + shelf_h + gap, 0.0
            if y + h > v1:
                ok = False
                break
            pos[k] = (x, y, w, h)
            x += w + gap
            shelf_h = max(shelf_h, h)
        if ok:
            break
        dens *= 0.95
    print(f"[drips] texel density {dens * TEX:.1f} px/stud")

    for k, (ang, L, a0, b0) in enumerate(drips):
        rows = drip_rows(L, a0, b0)
        px, py, pw, ph = pos[k]
        z_top, z_tip = rows[0][0], rows[-1][0]
        prow, puv = [], []
        for z, a, th in rows:
            rw = wall_r(z)
            if a == 0.0:
                p = Vector((math.cos(ang) * (rw - 0.4), math.sin(ang) * (rw - 0.4), z))
                prow.append([p])
                puv.append([(px + pw / 2, py + ph * (z - z_tip) / (z_top - z_tip))])
                continue
            row, uvr = [], []
            for c in range(K + 1):
                phi = -math.pi / 2 + math.pi * c / K
                t = a * math.sin(phi)
                rad = rw - 0.4 + (th + 0.4) * math.cos(phi)
                th_ang = ang + t / rw
                row.append(Vector((math.cos(th_ang) * rad, math.sin(th_ang) * rad, z)))
                uvr.append((px + pw * c / K, py + ph * (z - z_tip) / (z_top - z_tip)))
            prow.append(row)
            puv.append(uvr)
        b.grid(prow, puv, "Drip")


# ------------------------------------------------------------------ bake materials
def periodic(nt, rect, sector_len, plength):
    """Noise coordinates in studs that wrap seamlessly at the sector edges:
    (Rc cos a, Rc sin a, s) with a = 2 pi * (u within the sector)."""
    u0, v0, u1, v1 = rect
    uvx = nt.xyz(nt.uv())
    fu = nt.math("DIVIDE", nt.math("SUBTRACT", uvx[0], u0), u1 - u0)
    s = nt.math("MULTIPLY", nt.math("DIVIDE", nt.math("SUBTRACT", v1, uvx[1]), v1 - v0), plength)
    a = nt.math("MULTIPLY", fu, 2 * math.pi)
    rc = sector_len / (2 * math.pi)
    return nt.combine(nt.math("MULTIPLY", nt.math("COSINE", a), rc), nt.math("MULTIPLY", nt.math("SINE", a), rc), s), s


def shade_mix(nt, base_hex, light, shadow_tint):
    """base colour x light (0..1.1), with the dark side leaning toward shadow_tint (rgb mult)."""
    base = nt.rgb(base_hex)
    dark = nt.mix(1.0, base, shadow_tint + (1,), "MULTIPLY")
    t = nt.mrange(light, 0.45, 1.0, 0.0, 1.0)
    col = nt.mix(t, dark, base)
    over = nt.mrange(light, 1.0, 1.15, 0.0, 1.0)
    return nt.mix(nt.math("MULTIPLY", over, 0.6), col, (1, 1, 1, 1), "SCREEN")


def mat_grass():
    sector = 2 * math.pi * 100.0 / RIM_SECTORS

    def build(nt):
        p, s = periodic(nt, UV_LIP, sector, plen(LIP))
        z = nt.xyz(nt.obj())[2]
        vor = nt.voronoi(p, 0.42, "SMOOTH_F1")
        vor.inputs["Smoothness"].default_value = 0.8
        tuft = nt.mrange(vor.outputs["Distance"], 0.0, 0.75, 1.0, 0.0)
        top = nt.mrange(z, -2.0, 0.45, 0.62, 1.04, smooth=True)
        ao = nt.mrange(nt.ao(3.0, 16), 0.3, 1.0, 0.55, 1.0)
        light = nt.math("MULTIPLY", nt.math("MULTIPLY", top, ao), nt.math("ADD", 0.975, nt.math("MULTIPLY", tuft, 0.04)))
        col = shade_mix(nt, C.PAL["grass"], light, (0.62, 0.78, 0.95))
        rough = nt.math("ADD", 0.68, nt.math("MULTIPLY", tuft, -0.08))
        return dict(albedo=col, rough=rough, height=tuft, bump=(0.35, 0.25))
    return C.bake_material("Grass", build)


def mat_frosting():
    sector = 2 * math.pi * 101.5 / RIM_SECTORS

    def build(nt):
        p, s = periodic(nt, UV_FROST, sector, plen(FROST))
        z = nt.xyz(nt.obj())[2]
        # soft piped ripples
        rip = nt.noise(p, 0.16, 1.0, 0.4, 1.7)
        # sprinkle dots (nonpareils): sparse round dots, 4 candy colours + white
        vor = nt.voronoi(p, 0.36, "F1")
        dot = nt.mrange(vor.outputs["Distance"], 0.30, 0.38, 1.0, 0.0)
        sep = nt.n.new("ShaderNodeSeparateColor")
        nt.set(sep.inputs[0], vor.outputs["Color"])
        keep = nt.mrange(sep.outputs["Red"], 0.52, 0.54, 0.0, 1.0)
        dot = nt.math("MULTIPLY", dot, keep)
        ramp = nt.n.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        el = ramp.color_ramp.elements
        el[0].position, el[0].color = 0.0, C.lin(C.PAL["cream"])
        el[1].position, el[1].color = 0.3, C.lin(C.PAL["lemon"])
        for pos, key in ((0.5, "mint"), (0.7, "red"), (0.85, "cream")):
            e = el.new(pos)
            e.color = C.lin(C.PAL[key])
        nt.set(ramp.inputs["Fac"], sep.outputs["Green"])
        top = nt.mrange(z, -7.5, -2.6, 0.62, 1.06, smooth=True)
        ao = nt.mrange(nt.ao(3.0, 16), 0.3, 1.0, 0.6, 1.0)
        light = nt.math("MULTIPLY", nt.math("MULTIPLY", top, ao), nt.math("ADD", 0.97, nt.math("MULTIPLY", rip, 0.06)))
        cake = shade_mix(nt, C.PAL["pink"], light, (0.78, 0.62, 0.86))
        spr = nt.mix(1.0, ramp.outputs["Color"], nt.math("ADD", 0.35, nt.math("MULTIPLY", light, 0.62)), "MULTIPLY")
        col = nt.mix(dot, cake, spr)
        rough = nt.math("ADD", 0.48, nt.math("MULTIPLY", dot, -0.2))
        height = nt.math("ADD", nt.math("MULTIPLY", rip, 0.6), nt.math("MULTIPLY", dot, 0.5))
        return dict(albedo=col, rough=rough, height=height, bump=(0.45, 0.2))
    return C.bake_material("Frosting", build)


def mat_drip():
    def build(nt):
        z = nt.xyz(nt.obj())[2]
        geo = nt.n.new("ShaderNodeNewGeometry")
        nz = nt.xyz(geo.outputs["Normal"])[2]
        ao = nt.mrange(nt.ao(2.0, 16), 0.3, 1.0, 0.55, 1.0)
        top = nt.mrange(z, -18.0, -7.5, 0.9, 1.0)
        face = nt.mrange(nz, -0.9, 0.4, 0.82, 1.04)
        light = nt.math("MULTIPLY", nt.math("MULTIPLY", top, ao), face)
        col = shade_mix(nt, C.PAL["pink"], light, (0.78, 0.62, 0.86))
        return dict(albedo=col, rough=0.4, height=None)
    return C.bake_material("Drip", build)


def mat_choc():
    sector = 2 * math.pi * 99.0 / CHOC_SECTORS

    def build(nt):
        p, s = periodic(nt, UV_CHOC, sector, plen(CHOC))
        z = nt.xyz(nt.obj())[2]
        geo = nt.n.new("ShaderNodeNewGeometry")
        nz = nt.xyz(geo.outputs["Normal"])[2]
        swirl = nt.noise(p, 0.05, 1.0, 0.4, 4.2)
        ao = nt.mrange(nt.ao(6.0, 24), 0.25, 1.0, 0.5, 1.0)
        face = nt.mrange(nz, -1.0, 0.5, 0.74, 1.08, smooth=True)
        depth = nt.mrange(z, -58.0, -6.0, 0.86, 1.0)
        light = nt.math("MULTIPLY", nt.math("MULTIPLY", ao, face), depth)
        light = nt.math("MULTIPLY", light, nt.math("ADD", 0.96, nt.math("MULTIPLY", swirl, 0.07)))
        col = shade_mix(nt, C.PAL["choc"], light, (0.72, 0.6, 0.86))
        rough = nt.math("ADD", 0.33, nt.math("MULTIPLY", swirl, 0.08))
        return dict(albedo=col, rough=rough, height=swirl, bump=(0.2, 0.6))
    return C.bake_material("Choc", build)


# ------------------------------------------------------------------ build
def build():
    C.reset()
    rng = random.Random(20261125)
    rim = C.Builder("Island_Rim")
    rim.lathe("Grass", LIP, RIM_SEGS, UV_LIP, RIM_SECTORS)
    rim.lathe("Frosting", FROST, RIM_SEGS, UV_FROST, RIM_SECTORS)
    drips = C.Builder("Island_Drips")
    build_drips(drips, make_drips(rng))
    choc = C.Builder("Island_Under")
    choc.lathe("Choc", CHOC, CHOC_SEGS, UV_CHOC, CHOC_SECTORS, turn=math.pi / CHOC_SEGS)

    mats = {"Grass": mat_grass(), "Frosting": mat_frosting(), "Drip": mat_drip(), "Choc": mat_choc()}
    obs = {}
    for b in (rim, drips, choc):
        ob = b.to_object()
        for m in b.mats:
            ob.data.materials.append(mats[m])
        obs[b.name] = ob
    return obs


def check_normals(ob):
    """Count faces whose normal points toward the island's axis (should be none on these
    shells, except underside faces which point down)."""
    bad = 0
    for p in ob.data.polygons:
        c = p.center
        radial = Vector((c.x, c.y, 0)).normalized()
        n = p.normal
        if n.dot(radial) < -0.2 and n.z > -0.5:
            bad += 1
    return bad


def main():
    obs = build()
    rim, drips, under = obs["Island_Rim"], obs["Island_Drips"], obs["Island_Under"]
    for ob in (rim, drips, under):
        print(f"[check] {ob.name}: {check_normals(ob)} inward-facing faces")

    # bake: rim + chocolate first with the drips hidden (repeating sectors must agree),
    # then the drips (unique UVs) with everything visible for contact shading
    drips.hide_render = True
    C.bake_set([rim, under], NAME, TEX, clear=True)
    drips.hide_render = False
    C.bake_set([rim, under, drips], NAME, TEX, clear=False, select=[drips])

    # join the drips into the rim (one mesh: grass lip + frosting + drips)
    bpy.ops.object.select_all(action="DESELECT")
    drips.select_set(True)
    rim.select_set(True)
    bpy.context.view_layer.objects.active = rim
    bpy.ops.object.join()

    maps = C.load_maps(NAME)
    final = C.textured_material("Island", maps)
    flat = C.textured_material("IslandFlat", maps, flat=True)
    for ob in (rim, under):
        C.set_material(ob, final)

    meshes = [rim, under]
    total = C.report_tris(meshes, NAME)
    C.export(meshes, NAME + ".fbx")
    bounds = {
        "_notes": [
            "Blender height 0 = the grass surface. In the hub, grass top is at hub y = -3, so place each mesh",
            "at hub (center.x, center.y - 3, center.z) (Roblox puts a MeshPart's origin at its box centre).",
            "Both meshes share one SurfaceAppearance: Hub_Island_color/_normal/_roughness.png (1024).",
            "The flat Grass part (cylinder radius 99, 5 thick, top at y = -3) stays; the rim rolls over its edge.",
            "Island_Rim replaces the edge of Grass + Frosting; Island_Under replaces IslandRock x6.",
        ],
        "grassTopBlenderZ": 0.0,
        "grassTopHubY": -3.0,
        "totalTris": total,
        "texture": {"color": NAME + "_color.png", "normal": NAME + "_normal.png",
                    "roughness": NAME + "_roughness.png", "size": TEX},
    }
    for ob, col, mat in ((rim, C.PAL["pink"], "SmoothPlastic + SurfaceAppearance"),
                         (under, C.PAL["choc"], "SmoothPlastic + SurfaceAppearance")):
        d = C.roblox_box(ob)
        d.update(tris=C.tri_count(ob), color=C.hex_rgb(col), material=mat, castShadow=ob is rim)
        bounds[ob.name] = d
    C.write_bounds(NAME + ".bounds.json", bounds)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))

    previews(rim, under, final, flat)


def previews(rim, under, final, flat):
    # stand-in for the Roblox grass disc (preview only)
    me = bpy.data.meshes.new("GrassDisc")
    b = C.Builder("GrassDisc")
    b.lathe("g", [(0.0, 0.0), (GRASS_R, 0.0), (GRASS_R, -5.0)], 96, (0, 0, 1, 1))
    disc = b.to_object()
    disc.data.materials.append(C.flat_material("GrassPart", C.PAL["grass"], 0.8))
    disc["preview_only"] = True
    C.player_block((0, 70, 0))

    cam = C.studio((0, 0, -22), 110)
    beauty = os.path.join(C.PREVIEWS, "hub_island_island_beauty.png")
    C.look(cam, (190, 250, 70), (0, 0, -24), 42)
    C.render(beauty, 1280, 960)
    C.thumb(beauty, os.path.join(C.PREVIEWS, "hub_island_island_thumb.png"))

    for ob in (rim, under):
        C.set_material(ob, flat)
    C.render(os.path.join(C.PREVIEWS, "hub_island_island_flat.png"), 1280, 960)
    for ob in (rim, under):
        C.set_material(ob, final)

    views = []
    for k, (dx, dy) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        p = os.path.join(C.TMP, f"island_turn_{k}.png")
        C.look(cam, (dx * 330, dy * 330, 45), (0, 0, -24), 50)
        C.render(p, 640, 480, samples=48)
        views.append(p)
    C.compose(views, os.path.join(C.PREVIEWS, "hub_island_island_turn.png"))

    # close-up of the drips at a player's eye level just outside the edge
    C.look(cam, (40, 150, 2), (20, 100, -9), 30)
    C.render(os.path.join(C.PREVIEWS, "hub_island_island_closeup.png"), 1280, 800)
    # from below
    C.look(cam, (120, 170, -95), (0, 0, -30), 38)
    C.render(os.path.join(C.PREVIEWS, "hub_island_island_below.png"), 1200, 900, samples=48)


main()
