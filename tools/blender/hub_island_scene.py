# Batch D: whole-island preview, from about the same angle as art/previews/hub_sky_island.jpg.
# Loads the finished Hub_Island / Hub_Lollipop / Hub_Cloud .blend files (run their scripts
# first), adds the Roblox grass disc and a plain 112 x 112 white slab for the plaza, places 26
# lollipops the way Hub.lua does and a cloud floor below. Preview only: nothing is exported.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_island_scene.py
#
# Output: art/previews/hub_island_scene.png (and hub_island_scene_far.png)

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import hub_island_common as C  # noqa: E402


def load(blend):
    with bpy.data.libraries.load(os.path.join(C.OUT, blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    out = {}
    for ob in dst.objects:
        if ob is not None and ob.type == "MESH":
            out[ob.name] = ob
    return out


def box(name, size, center, hexcol, rough=0.4):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(C.flat_material(name + "Mat", hexcol, rough))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def place_copy(src, loc, rz=0.0, s=1.0, mat=None):
    c = src.copy()
    if mat:
        c.data = src.data.copy()
        C.set_material(c, mat)
    bpy.context.scene.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (0, 0, rz)
    c.scale = (s, s, s)
    return c


def main():
    C.reset()
    island = load("Hub_Island.blend")
    lolly = load("Hub_Lollipop.blend")
    cloud = load("Hub_Cloud.blend")
    for ob in island.values():
        bpy.context.scene.collection.objects.link(ob)

    # Roblox parts that stay: grass disc (radius 99, top at 0), and the plaza slab (3 above grass)
    b = C.Builder("GrassDisc")
    b.lathe("g", [(0.0, 0.0), (99.0, 0.0), (99.0, -5.0)], 96, (0, 0, 1, 1))
    disc = b.to_object()
    disc.data.materials.append(C.flat_material("GrassPart", C.PAL["grass"], 0.8))
    box("Plaza", (112, 112, 3), (0, 0, 1.5), C.PAL["cream"], 0.35)

    # 26 lollipops on the grass ring, like Hub.lua buildScenery (between the plaza and the edge)
    maps = C.load_maps("Hub_Lollipop")
    tints = [C.textured_material("L_" + n, maps, tint=h) for n, h in C.GUMBALLS]
    body = C.textured_material("L_Body", maps)  # (reloading the maps orphaned the file's own material)
    shapes = ["Swirl", "Ball", "Heart"]
    rng = random.Random(7)
    placed, maxR = 0, 99 - 12
    while placed < 26:
        x, y = rng.uniform(-maxR, maxR), rng.uniform(-maxR, maxR)
        if max(abs(x), abs(y)) > 64 and math.hypot(x, y) < maxR:
            placed += 1
            s = rng.uniform(0.8, 1.4)
            shape = shapes[placed % 3]
            rz = rng.uniform(0, math.pi)
            t = tints[rng.randrange(len(tints))]
            for part in ("Tint", "Body", "Shine"):
                src = lolly[f"Lollipop_{shape}_{part}"]
                place_copy(src, (x, y, 0), rz, s, {"Tint": t, "Body": body}.get(part))

    # cloud floor far below and a few puffs around
    names = list(cloud.keys())
    for k in range(70):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(60, 650)
        size = rng.uniform(40, 80) / 20
        place_copy(cloud[names[k % 3]], (math.cos(a) * r, math.sin(a) * r, rng.uniform(-125, -110)), rng.uniform(0, 6.3), size)
    for k in range(12):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(170, 400)
        size = rng.uniform(14, 28) / 20
        place_copy(cloud[names[k % 3]], (math.cos(a) * r, math.sin(a) * r, rng.uniform(-45, 40)), rng.uniform(0, 6.3), size)

    cam = C.studio((0, 0, -20), 140, sky=True)
    # same feel as hub_sky_island.jpg: from outside the bubble, a little above the grass
    C.look(cam, (0, 330, 70), (0, 0, -12), 35)
    C.render(os.path.join(C.PREVIEWS, "hub_island_scene.png"), 1280, 800, samples=48)
    C.look(cam, (260, 330, -30), (0, 0, -22), 32)
    C.render(os.path.join(C.PREVIEWS, "hub_island_scene_low.png"), 1280, 800, samples=48)


main()
