# Shared setup for the CLEAN POP PLAZA prop kit (hub_cleanprops_*.py): same kit, palette, axes and
# export as hub_clean_common.py, but everything is written to art/hub_clean_props/.
# Not run by itself.
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/hub_cleanprops_<asset>.py

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hub_clean_common as K  # noqa: E402
import bpy  # noqa: E402

P = K.P
OUT = os.path.join(K.ROOT, "art", "hub_clean_props")
os.makedirs(OUT, exist_ok=True)
K.OUT = OUT
P.OUT = OUT
P.TMP = os.path.join(OUT, "_tmp")
PREV = K.PREV


def arch_ring(hw, hb, ht, n=8):
    """ring(d) for lathe(): an arched window outline (half width hw, bottom at -hb, the round top
    starts at ht), grown outwards by d. Ring plane = the frame's u, v."""
    def ring(d):
        r = hw + d
        pts = [(r, -hb - d)]
        pts += [(r * math.cos(math.pi * i / n), ht + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
        pts.append((-r, -hb - d))
        return pts
    return ring


def out_frame(origin, az):
    """Frame whose profile height runs outwards along azimuth az (radians from +Y towards +X); v = up."""
    return P.frame(origin, (-math.cos(az), math.sin(az), 0), (0, 0, 1))


def ngon(mb, ring_pts, fr, w, zone):
    o, U, V, W = fr
    mb.face([mb.bm.verts.new(o + U * x + V * y + W * w) for x, y in ring_pts], zone, smooth=False)


def window(body, glow, origin, az, hw, hb, ht, n=8, zone="frame", depth=0.42, fat=0.45):
    """Arched window: a fat white frame (body) round a flat glowing pane (glow)."""
    fr = out_frame(origin, az)
    ring = arch_ring(hw, hb, ht, n)
    body.lathe([(fat, -0.5), (fat, depth * 0.55), (fat * 0.7, depth), (fat * 0.2, depth), (0.02, depth * 0.45), (0.02, 0.0)],
               ring, fr, zone=zone)
    ngon(glow, ring(0.03), fr, depth * 0.3, "glow")


def emit_preview(ob, hexcol, strength=3.0, name=None):
    m = P.flat_material(name or ob.name + "_Prev", hexcol, 0.3, emit=strength)
    K.set_mat(ob, m)
    return m
