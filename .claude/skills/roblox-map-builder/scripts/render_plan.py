# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Top-down plan render of a built map (for layout review and docs).
#   blender -b <map>.blend --python render_plan.py -- --center X Z --size S --out plan.png [--res 1600]
# X/Z/S in Roblox studs (X east, Z south). The image is north-up: image top = -Z (north), image right = +X (east).
# Pixel of a world point: px = (x - X) / S * res + res/2 ; py = (z - Z) / S * res + res/2  (annotate_plan.py uses this).
import bpy, sys, math
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
def arg(k, d=None, n=1):
    if k not in A: return d
    i = A.index(k); return A[i + 1] if n == 1 else A[i + 1:i + 1 + n]
cx, cz = map(float, arg('--center', ['0', '0'], 2)); S = float(arg('--size', '500')); out = arg('--out', 'plan.png')
res = int(arg('--res', '1600'))
sc = bpy.context.scene
for o in sc.objects:                                           # haze volume would wash the plan out
    if o.name.startswith('Haze'): o.hide_render = True
cam = bpy.data.objects.new('PlanCam', bpy.data.cameras.new('PlanCam')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = S; cam.data.clip_end = 5000
cam.location = (-cx, cz, 1500)                                  # Roblox (x, y, z) -> Blender (-x, z, y)
cam.rotation_euler = (0, 0, math.pi)                            # Blender looking down; rotate so +X Roblox is image right, -Z up
sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = res
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('PLAN_OK', out)
