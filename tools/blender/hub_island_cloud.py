# Batch D3: cloud puffs (docs/art_plan.md, BATCH D). Three soft clumps in one FBX, flat white,
# no texture.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_island_cloud.py
#
# Cloud_A (wide five-puff heap), Cloud_B (tall round three-puff), Cloud_C (long low drifter):
# merged rounded blobs (metaballs) with a flatter bottom, about 20 wide, bottom centre on the
# origin, decimated to 150-300 triangles with smooth shading (no small bumps).
#
# Outputs (art/hub_island/): Hub_Cloud.fbx, Hub_Cloud.blend, Hub_Cloud.bounds.json
# Previews (art/previews/): hub_island_cloud_beauty/_turn/_flat/_thumb.png

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import hub_island_common as C  # noqa: E402

NAME = "Hub_Cloud"
TARGET = 296  # triangles per cloud

# (x, y, z, radius) puffs, z = height of the puff centre; built ~20 wide
CLOUDS = {
    "Cloud_A": [(-6.0, 0.2, 2.9, 4.0), (-0.8, -0.4, 4.8, 5.4), (5.0, 0.2, 3.4, 4.3), (0.6, 2.6, 2.6, 3.4)],
    "Cloud_B": [(-4.2, 0.0, 3.4, 4.4), (1.6, 0.2, 5.4, 5.9), (6.2, -0.3, 2.9, 3.6)],
    "Cloud_C": [(-6.8, 0.0, 2.3, 3.4), (-1.6, 0.3, 3.3, 4.6), (3.8, -0.2, 2.8, 3.8), (8.0, 0.1, 2.0, 2.7)],
}


def metaball_mesh(name, puffs, res):
    mb = bpy.data.metaballs.new(name + "_mb")
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = 0.6
    for x, y, z, r in puffs:
        el = mb.elements.new()
        el.co = (x, y, z)
        el.radius = r * 1.2
        el.stiffness = 2.6
    ob = bpy.data.objects.new(name + "_mbob", mb)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    return me


def blob_mesh(name, puffs):
    """Polygonise the metaballs coarsely (even triangles, lobes kept) at the finest
    resolution that stays within the budget."""
    res = 0.9
    while True:
        me = metaball_mesh(name, puffs, res)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
        n = len(bm.faces)
        if n <= TARGET:
            break
        bm.free()
        bpy.data.meshes.remove(me)
        res *= 1.04
    print(f"[{name}] metaball resolution {res:.2f}")
    # flatter bottom: squash everything below the base line up toward it
    zs = [v.co.z for v in bm.verts]
    base = min(zs) + (max(zs) - min(zs)) * 0.2
    for v in bm.verts:
        if v.co.z < base:
            v.co.z = base + (v.co.z - base) * 0.15
    lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
    hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
    bmesh.ops.translate(bm, vec=Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.name = name
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    C.reset()
    white = C.flat_material("CloudWhite", "#FFFFFF", 0.9)
    obs = []
    for name, puffs in CLOUDS.items():
        ob = blob_mesh(name, puffs)
        ob.data.materials.append(white)
        C.smart_uv(ob, (0, 0, 1, 1), angle=66, margin=0.02)
        obs.append(ob)
    total = C.report_tris(obs, NAME)
    C.export(obs, NAME + ".fbx")
    bounds = {
        "_notes": [
            "Three cloud models, each with its bottom centre on the origin, ~20 wide; scale 14 - 80 wide in game.",
            "Flat colour, no texture: SmoothPlastic, Color 255,255,255, CastShadow false, CanCollide false.",
            "Replaces the Cloud balls made by puff() in Hub.lua buildScenery (one model per puff cluster).",
        ],
        "totalTris": total,
    }
    for ob in obs:
        d = C.roblox_box(ob)
        d.update(tris=C.tri_count(ob), color=[255, 255, 255], material="SmoothPlastic (flat, no texture)", castShadow=False)
        bounds[ob.name] = d
    C.write_bounds(NAME + ".bounds.json", bounds)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(C.OUT, NAME + ".blend"))

    # previews on a sky backdrop
    for i, ob in enumerate(obs):
        ob.location = ((i - 1) * 24, 0, 0)
    C.player_block((37, 0, 0))
    cam = C.studio((0, 0, 5), 30, sky=True)
    beauty = os.path.join(C.PREVIEWS, "hub_island_cloud_beauty.png")
    C.look(cam, (30, 72, 22), (0, 0, 4.5), 38)
    C.render(beauty, 1280, 960)
    C.thumb(beauty, os.path.join(C.PREVIEWS, "hub_island_cloud_thumb.png"))
    # flat: these have no maps, so the colour-only view is the same model at matte grey-white
    C.render(os.path.join(C.PREVIEWS, "hub_island_cloud_flat.png"), 1280, 960, samples=32)
    views = []
    for k, (dx, dy) in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        for i, ob in enumerate(obs):
            ob.location = ((i - 1) * 24 * abs(dy), (i - 1) * 24 * -dx, 0)
        p = os.path.join(C.TMP, f"cloud_turn_{k}.png")
        C.look(cam, (dx * 120, dy * 120, 14), (0, 0, 4.5), 45)
        C.render(p, 640, 480, samples=32)
        views.append(p)
    C.compose(views, os.path.join(C.PREVIEWS, "hub_island_cloud_turn.png"))


main()
