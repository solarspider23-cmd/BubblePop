# Northgate Distribution warehouse kit helpers (palette + primitives). Roblox space (X east, Y up, Z south, 1 unit = 1 stud),
# origin = bottom centre, front = -Z. Scale: 1 m ~ 3.14 studs (avatar 5.5 studs).
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
from pro_lib import Palette, box, cyl, tube, hull, ngon_prism, rock, clamp, lerp, nz

G.PAL = Palette({
    'concrete': ('#4e4c47', '#8a877f', '#c2beb4'),   # floor slab, dock walls
    'asphalt':  ('#1b1c1f', '#323438', '#5a5c61'),   # yard
    'steel':    ('#3c424a', '#7c858f', '#c4ccd4'),   # galvanised steel, structure
    'rack':     ('#0c2450', '#1c4a96', '#5a86d8'),   # pallet-rack uprights (blue paint)
    'beam':     ('#6a2808', '#d0581a', '#ff9a5a'),   # rack beams, crane girder (safety orange)
    'cardboard':('#5e4222', '#a67a48', '#d4ac78'),   # boxes
    'pallet':   ('#4e402c', '#8f7a58', '#c8b48c'),   # pallet timber
    'yellow':   ('#6a4e00', '#dcae08', '#ffe46a'),   # forklift paint, barriers, floor lines
    'rubber':   ('#0f0f11', '#222226', '#45454a'),   # tyres, black parts
    'cladding': ('#4a5058', '#9aa2aa', '#d8dde2'),   # wall sandwich panels, roof deck
    'red':      ('#4a0c0e', '#a81c20', '#ec5a58'),   # fire kit, container, lights
    'plastic':  ('#0c2a46', '#2468a6', '#86bce8'),   # drums, IBC frames, crates
    'paper':    ('#8e8e8a', '#d8d8d2', '#fafaf6'),   # labels, IBC tank, wrap
    'glass':    ('#1a2a3a', '#6a8aa8', '#c8dcef'),   # office glazing, skylights
    'green':    ('#14301e', '#2a6a40', '#6aae7a'),   # first-aid box, container option, trailer
})
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'lamp': '#fff3dc', 'sky': '#e4eeff', 'beacon': '#ff8a1a', 'stop': '#ff2a2a', 'go': '#3aff6a'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 4.0, 'sky': 2.0, 'beacon': 3.0, 'stop': 3.0, 'go': 3.0})
Prop, S, at = G.Prop, G.S, G.at
PAL = G.PAL

# ------------------------------------------------------------------ helpers
def V(*a): return Vector(a)
def B(P, size, loc, col, bev=.06, rot=(0, 0, 0), base=.55, up=.25, jit=.03, seed=0):
    P.add(at(box(size, bev), loc, rot), S(col, base=base, up=up, jit=jit, seed=seed))
def CY(P, r, h, loc, col, sides=8, bev=0.0, rot=(0, 0, 0), r2=None, base=.55, up=.25):
    P.add(at(cyl(r, h, sides, bev, r2), loc, rot), S(col, base=base, up=up, jit=0), sides > 7)
def T(P, pts, r, col, sides=6, base=.55, up=.2, cap=True):
    P.add(tube(pts, r, sides, cap, cap), S(col, base=base, up=up, jit=0), smooth=True)
def glowbox(P, size, loc, key, rot=(0, 0, 0)):
    b = box(size, 0); at(b, loc, rot); P.gadd(b, key)

class Sub:
    """a reusable sub-assembly emitted into props with a chain of rotations then a translation"""
    def __init__(self): self.items = []
    def add(self, bm, sh, smooth=False): self.items.append((bm, sh, smooth))
    def gadd(self, bm, key): self.items.append((bm, key, 'glow'))
    def emit(self, P, loc=(0, 0, 0), rots=()):
        for bm, sh, sm in self.items:
            b2 = bm.copy()
            for r in rots: at(b2, (0, 0, 0), r)
            at(b2, loc)
            if sm == 'glow': P.gadd(b2, sh)
            else: P.add(b2, sh, sm)

def lathe(prof, sides=12, closed=False, rot0=0.0):
    """revolve [(r, y)] round Y"""
    bm = bmesh.new(); rings = []
    for r, y in prof:
        if r < 1e-4: rings.append([bm.verts.new((0, y, 0))])
        else: rings.append([bm.verts.new((math.cos(rot0 + a * math.tau / sides) * r, y, math.sin(rot0 + a * math.tau / sides) * r)) for a in range(sides)])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for A, Bb in pairs:
        for a in range(sides):
            b = (a + 1) % sides
            if len(A) == 1 and len(Bb) == 1: break
            try:
                if len(A) == 1: bm.faces.new((A[0], Bb[a], Bb[b]))
                elif len(Bb) == 1: bm.faces.new((A[a], A[b], Bb[0]))
                else: bm.faces.new((A[a], A[b], Bb[b], Bb[a]))
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def prism_x(poly_zy, x0, x1):
    """profile in the Z-Y plane [(z, y)], extruded along X"""
    bm = ngon_prism([(z, y) for z, y in poly_zy], x0, x1)
    for v in bm.verts: v.co = Vector((v.co.y, v.co.z, v.co.x))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def prism_z(poly_xy, z0, z1):
    """profile in the X-Y plane [(x, y)], extruded along Z"""
    bm = ngon_prism([(x, y) for x, y in poly_xy], z0, z1)
    for v in bm.verts: v.co = Vector((v.co.x, v.co.z, v.co.y))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def ring_tube(c, R, r, n=16, sides=6, axis='Y'):
    pts = []
    for k in range(n + 1):
        a = k * math.tau / n
        if axis == 'Y': pts.append(c + V(math.cos(a) * R, 0, math.sin(a) * R))
        elif axis == 'X': pts.append(c + V(0, math.cos(a) * R, math.sin(a) * R))
        else: pts.append(c + V(math.cos(a) * R, math.sin(a) * R, 0))
    return tube(pts, r, sides, False, False)

def pol(r, phi, y=0.0): a = math.radians(phi); return V(math.cos(a) * r, y, math.sin(a) * r)
def sphere(r, n=10, rings=7, y=0.0):
    prof = [(math.sin(math.pi * i / rings) * r, y - math.cos(math.pi * i / rings) * r) for i in range(rings + 1)]
    prof[0] = (0, prof[0][1]); prof[-1] = (0, prof[-1][1])
    return lathe(prof, n)
def rbox(size, r, seg=2):
    b = box(size, 0); G.bevel(b, min(r, min(size) * .45), seg); return b

def quad(w, h, axis='y', off=0.0, a=0.0, b=0.0, flip=False):
    """one single-sided quad: axis 'y' = facing +y at height off (w along x, h along z); 'z' = facing -z at z off (w x, h y);
    'x' = facing +x at x off (w along z, h along y). flip reverses it. Decals / lines on a surface: 2 tris, no hidden sides."""
    bm = bmesh.new()
    if axis == 'y': pts = [(a - w / 2, off, b - h / 2), (a - w / 2, off, b + h / 2), (a + w / 2, off, b + h / 2), (a + w / 2, off, b - h / 2)]; n = V(0, 1, 0)
    elif axis == 'z': pts = [(a - w / 2, b - h / 2, off), (a + w / 2, b - h / 2, off), (a + w / 2, b + h / 2, off), (a - w / 2, b + h / 2, off)]; n = V(0, 0, -1)
    else: pts = [(off, b - h / 2, a - w / 2), (off, b - h / 2, a + w / 2), (off, b + h / 2, a + w / 2), (off, b + h / 2, a - w / 2)]; n = V(1, 0, 0)
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.normal_update()
    if (f.normal.dot(n) < 0) != flip: f.normal_flip()
    return bm
def quad_top(w, d, y, z=0.0, x=0.0): return quad(w, d, 'y', y, x, z)

def ibeam(L, h, w, tw, tf, axis='y'):
    """I / H section of length L along axis ('y' column, 'x' or 'z' beam), centred on the axis, starting at 0"""
    poly = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, -h / 2 + tf), (tw / 2, -h / 2 + tf), (tw / 2, h / 2 - tf), (w / 2, h / 2 - tf),
            (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, h / 2 - tf), (-tw / 2, h / 2 - tf), (-tw / 2, -h / 2 + tf), (-w / 2, -h / 2 + tf)]
    if axis == 'y':          # column: web along x, flanges face +-z
        bm = ngon_prism([(x, y) for x, y in poly], 0, L)
        return bm
    if axis == 'x':          # beam along x: profile in z-y
        return prism_x([(x, y) for x, y in poly], 0, L)
    return prism_z([(x, y) for x, y in poly], 0, L)

def SF(fn, up=.22):
    """per-face colour from fn(centre, normal) -> (ramp, value)"""
    def f(face):
        c = face.calc_center_median(); col, v = fn(c, face.normal)
        return [(PAL.u(col), clamp(v + up * face.normal.y, .04, .96))] * len(face.loops)
    return f

def drop_bottom(bm, y=0.02):
    """delete downward faces lying on y (sits on the floor / another surface)"""
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y < -.98 and max(v.co.y for v in f.verts) < y + .01], context='FACES')
    return bm
