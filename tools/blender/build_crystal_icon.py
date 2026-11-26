# BubblePop "Crystals" premium currency icon. Re-runnable, background only:
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_crystal_icon.py
#
# A cluster of chunky faceted crystals (one tall main crystal, two small ones at
# its base) in magenta -> violet with cyan highlight facets, a white sparkle and
# a thick dark-navy outline (RGB 20,40,110, the HUD stroke colour).
#
# How it is drawn: Workbench, FLAT lighting, colour = per-corner colour
# attribute. Each facet's colour is picked in this script from its normal vs a
# fixed light (3 toon bands + rim), so the look is exact and repeatable. The
# outline is an inverted hull (copy pushed out along normals, flipped, navy,
# backface culling on). Orthographic camera, transparent film.
#
# Outputs (art/icons/): Crystal_512.png, Crystal_128.png (4x box downscale of a
# 512 render), Crystal_512_outline-free.png; copy at art/previews/crystal_icon.png
import math
import os
import shutil

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ICONS = os.path.join(ROOT, "art", "icons")
PREV = os.path.join(ROOT, "art", "previews")
os.makedirs(ICONS, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

NAVY = (20, 40, 110)
OUTLINE = 0.085          # outline thickness (world units; frame is ~3 units tall)
LIGHT = Vector((-0.85, -0.35, 0.60)).normalized()   # from upper-left-front (camera at -Y)

# toon palette (sRGB 0-255)
HI = (255, 125, 232)     # lit pink-magenta
MID = (218, 40, 196)     # magenta
LOW = (146, 36, 214)     # violet
DEEP = (84, 24, 160)     # deep violet (shadow side)
CYAN = (110, 235, 255)   # cyan highlight facets
CYAN_HI = (215, 252, 255)
WHITE = (255, 255, 255)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def crystal_bm(radius, height, shoulder, sides=6, taper=0.78, twist=0.0, tip_off=(0.0, 0.0)):
    """Hexagonal crystal: base ring, shoulder ring, pointed apex. Origin at base."""
    bm = bmesh.new()
    base, sh = [], []
    for i in range(sides):
        a = twist + 2 * math.pi * i / sides
        base.append(bm.verts.new((math.cos(a) * radius * taper, math.sin(a) * radius * taper, 0.0)))
        sh.append(bm.verts.new((math.cos(a) * radius, math.sin(a) * radius, height * shoulder)))
    apex = bm.verts.new((tip_off[0], tip_off[1], height))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((base[i], base[j], sh[j], sh[i]))
        bm.faces.new((sh[i], sh[j], apex))
    bm.faces.new(list(reversed(base)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def add_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = mat
    return ob


def face_colour(n_world, z_rel, is_top):
    """Toon band colour for one facet."""
    d = n_world.dot(LIGHT)
    if d > 0.72:
        c = CYAN_HI if is_top else CYAN
    elif d > 0.40:
        c = HI if is_top else lerp(HI, MID, 0.35)
    elif d > 0.0:
        c = MID
    elif d > -0.45:
        c = LOW
    else:
        c = DEEP
    # gentle top->bottom gradient: lower parts lean violet
    return lerp(c, DEEP, max(0.0, 0.35 - z_rel) * 0.6)


def paint(ob, fn):
    me = ob.data
    attr = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = attr
    me.color_attributes.render_color_index = 0
    mw = ob.matrix_world
    zs = [(mw @ v.co).z for v in me.vertices]
    zmin, zmax = min(zs), max(zs)
    rot = mw.to_3x3()
    for poly in me.polygons:
        n = (rot @ poly.normal).normalized()
        zc = ((mw @ poly.center).z - zmin) / max(1e-6, zmax - zmin)
        c = fn(poly, n, zc)
        for li in poly.loop_indices:
            attr.data[li].color_srgb = (c[0] / 255, c[1] / 255, c[2] / 255, 1.0)


def crystal(name, radius, height, shoulder, mat, twist, tip_off=(0, 0)):
    ob = add_obj(name, crystal_bm(radius, height, shoulder, twist=twist, tip_off=tip_off), mat)
    paint(ob, lambda p, n, z: face_colour(n, z, len(p.vertices) == 3))
    return ob


def hull(src, thick):
    """Inverted-hull outline: push verts out along normals, flip, paint navy."""
    me = src.data.copy()
    ob = bpy.data.objects.new(src.name + "_Outline", me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = src.matrix_world.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    # scale-aware push: divide by object scale so thickness is in world units
    s = sum(src.matrix_world.to_scale()) / 3
    for v in bm.verts:
        n = v.normal
        # sharper corners need a longer push to keep the rim even
        cosang = min((f.normal.dot(n) for f in v.link_faces), default=1.0)
        v.co += n * (thick / s) / max(0.45, cosang)
    for f in bm.faces:
        f.normal_flip()
    bm.to_mesh(me)
    bm.free()
    me.color_attributes.remove(me.color_attributes["Col"])
    paint(ob, lambda p, n, z: NAVY)
    return ob


def star_bm(r_out, r_in, points=4, depth=0.0):
    bm = bmesh.new()
    vs = []
    for i in range(points * 2):
        a = math.pi / 2 + math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        vs.append(bm.verts.new((math.cos(a) * r, 0.0, math.sin(a) * r)))
    c = bm.verts.new((0, depth, 0))
    for i in range(len(vs)):
        bm.faces.new((c, vs[i], vs[(i + 1) % len(vs)]))   # faces -Y (camera)
    return bm


def sparkle(name, loc, size, colour=WHITE):
    """Flat 4-point star facing the camera, with its own navy outline star."""
    rot = CAM_ROT
    m = Matrix.Translation(loc) @ rot.to_4x4()
    s = add_obj(name, star_bm(size, size * 0.26), m)
    paint(s, lambda p, n, z: colour)
    back = m @ Matrix.Translation((0, 0.02, 0))
    o = add_obj(name + "_Outline", star_bm(size + OUTLINE * 1.6, size * 0.26 + OUTLINE * 1.1), back)
    paint(o, lambda p, n, z: NAVY)
    return s, o


# ---------------------------------------------------------------- scene
reset()
sc = bpy.context.scene

CAM_EL = math.radians(24)     # look slightly down
CAM_AZ = math.radians(-18)    # slight 3/4 turn
CAM_ROT = (Matrix.Rotation(CAM_AZ, 3, 'Z') @ Matrix.Rotation(-CAM_EL, 3, 'X'))

parts = []
# main crystal: tall, slightly leaning right
parts.append(crystal("Main", 0.62, 2.55, 0.66,
                     Matrix.Translation((0.05, 0, -1.25)) @ Matrix.Rotation(math.radians(-6), 4, 'Y'),
                     twist=math.radians(10)))
# left small crystal leaning out
parts.append(crystal("Left", 0.40, 1.45, 0.62,
                     Matrix.Translation((-0.55, -0.20, -1.25)) @ Matrix.Rotation(math.radians(38), 4, 'Y')
                     @ Matrix.Rotation(math.radians(14), 4, 'X'),
                     twist=math.radians(25)))
# right small crystal leaning out, in front
parts.append(crystal("Right", 0.34, 1.10, 0.60,
                     Matrix.Translation((0.55, -0.35, -1.28)) @ Matrix.Rotation(math.radians(-42), 4, 'Y')
                     @ Matrix.Rotation(math.radians(16), 4, 'X'),
                     twist=math.radians(5)))
outlines = [hull(p, OUTLINE) for p in parts]

# sparkles (placed on the camera-facing side of the main crystal)
cam_fwd = CAM_ROT @ Vector((0, 1, 0))
sp1 = sparkle("Sparkle", Vector((0.62, 0, 0.62)) - cam_fwd * 2.0, 0.34)
sp2 = sparkle("SparkleSmall", Vector((-0.58, 0, 0.95)) - cam_fwd * 2.0, 0.17)

# camera
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 3.55
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
cam.matrix_world = Matrix.Translation(Vector((0, 0, -0.02)) - cam_fwd * 10) @ (CAM_ROT @ Matrix.Rotation(math.radians(90), 3, 'X')).to_4x4()
sc.camera = cam

# render settings
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'VERTEX'
sc.display.shading.show_backface_culling = True
sc.display.shading.show_object_outline = False
sc.display.shading.show_cavity = False
sc.display.shading.show_specular_highlight = False
sc.display.render_aa = '32'
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def downscale(src, dst, factor=4):
    """Box downscale with premultiplied alpha (exact for 512 -> 128)."""
    img = bpy.data.images.load(src)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb, a = px[..., :3], px[..., 3:4]
    pre = np.concatenate([rgb * a, a], axis=2)
    small = pre.reshape(h // factor, factor, w // factor, factor, 4).mean(axis=(1, 3))
    a2 = small[..., 3:4]
    rgb2 = np.where(a2 > 1e-5, small[..., :3] / np.maximum(a2, 1e-5), 0)
    out = np.concatenate([rgb2, a2], axis=2)
    nimg = bpy.data.images.new("small", w // factor, h // factor, alpha=True)
    nimg.pixels = out.ravel().tolist()
    nimg.filepath_raw = dst
    nimg.file_format = 'PNG'
    nimg.save()


p512 = os.path.join(ICONS, "Crystal_512.png")
render(p512)
downscale(p512, os.path.join(ICONS, "Crystal_128.png"))
shutil.copyfile(p512, os.path.join(PREV, "crystal_icon.png"))

# outline-free variant
for o in outlines + [sp1[1], sp2[1]]:
    o.hide_render = True
render(os.path.join(ICONS, "Crystal_512_outline-free.png"))
print("CRYSTAL ICON DONE")
