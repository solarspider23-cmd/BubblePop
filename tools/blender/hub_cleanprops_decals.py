# CLEAN POP PLAZA props 6: floor decal textures (512 PNG, white on transparent; colour them in game
# with Decal.Color3 / Texture.Color3). Drawn with maths (no downloads).
#   Decal_Ring.png  a soft double ring to lay round stations (booths, board, lamps)
#   Decal_Path.png  a path stripe with soft edges and a row of dots; tiles along its length (image up/down)
#   Decal_Star.png  a fat rounded star
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_decals.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art", "hub_clean_props")
N = 512
ys, xs = np.mgrid[0:N, 0:N]
u = (xs + 0.5) / N * 2 - 1      # -1..1
v = (ys + 0.5) / N * 2 - 1
PX = 2.0 / N


def cover(sd, soft=1.5):
    """Signed distance (negative inside) -> coverage, soft = edge width in pixels."""
    return np.clip(0.5 - sd / (soft * PX), 0, 1)


def band(x, c, half, soft=1.5):
    return cover(np.abs(x - c) - half, soft)


SHEET = []


def save(name, alpha):
    a = np.clip(alpha, 0, 1).astype(np.float32)
    SHEET.append(a)
    px = np.ones((N, N, 4), np.float32)
    px[..., 3] = a
    im = bpy.data.images.new(name, N, N, alpha=True)
    im.alpha_mode = "STRAIGHT"
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = os.path.join(OUT, name + ".png")
    im.file_format = "PNG"
    im.save()
    print("wrote", im.filepath_raw)


# ring: a fat main ring, a thin inner ring, a soft glow outside and a faint fill
r = np.sqrt(u * u + v * v)
ring = band(r, 0.80, 0.055)
ring = np.maximum(ring, 0.8 * band(r, 0.665, 0.014))
glow = 0.35 * np.exp(-((r - 0.80) / 0.09) ** 2)
fill = 0.10 * cover(r - 0.80)
save("Decal_Ring", np.maximum(np.maximum(ring, glow), fill))

# path: tiles up/down. Two edge lines, a faint body, and two round dots per tile down the middle
body = 0.16 * cover(np.abs(u) - 0.78)
lines = band(np.abs(u), 0.74, 0.045)
inner = 0.6 * band(np.abs(u), 0.60, 0.012)
vv = (v + 1) / 2                                   # 0..1 along the path
dy = (np.mod(vv * 2, 1.0) - 0.5) / 2 * 2           # two dots per tile, in the same units as u
dots = cover(np.sqrt(u * u + dy * dy) - 0.11)
dy2 = (np.mod(vv * 2 + 0.5, 1.0) - 0.5) / 2 * 2
small = 0.7 * cover(np.sqrt(u * u + dy2 * dy2) - 0.045)
save("Decal_Path", np.maximum.reduce([body, lines, inner, dots, small]))

# star: 5 fat points, rounded tips and valleys (distance to the star polygon, then round off)
R1, R2, RND = 0.60, 0.33, 0.14
ang = np.radians(90 + 36 * np.arange(10))
rad = np.where(np.arange(10) % 2 == 0, R1, R2)
vx, vy = rad * np.cos(ang), rad * np.sin(ang)
dmin = np.full((N, N), 1e9)
inside = np.zeros((N, N), bool)
for i in range(10):
    ax, ay, bx, by = vx[i], vy[i], vx[(i + 1) % 10], vy[(i + 1) % 10]
    ex, ey = bx - ax, by - ay
    t = np.clip(((u - ax) * ex + (v - ay) * ey) / (ex * ex + ey * ey), 0, 1)
    dmin = np.minimum(dmin, np.hypot(u - (ax + t * ex), v - (ay + t * ey)))
    cond = ((ay > v) != (by > v)) & (u < (bx - ax) * (v - ay) / (by - ay + 1e-12) + ax)
    inside ^= cond
sd = np.where(inside, -dmin, dmin) - RND
star = cover(sd)
halo = 0.30 * np.exp(-(np.maximum(sd, 0) / 0.06) ** 2)
shine = 0.0
save("Decal_Star", np.maximum(star, halo))
# check sheet: the three decals over the plaza blue (the path shown twice to prove it tiles)
cols = [SHEET[0], np.concatenate([SHEET[1][N // 2:], SHEET[1][:N // 2]]), SHEET[2]]
a = np.concatenate(cols, axis=1)
bg = np.array([0.10, 0.33, 0.80], np.float32)
px = np.ones((N, 3 * N, 4), np.float32)
px[..., :3] = bg + (1 - bg) * a[..., None]
im = bpy.data.images.new("sheet", 3 * N, N)
im.pixels.foreach_set(px.ravel())
im.filepath_raw = os.path.join(ROOT, "art", "previews", "hub_cleanprops_decals.png")
im.file_format = "PNG"
im.save()
print("DECALS done")
