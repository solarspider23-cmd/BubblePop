# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Shared helpers for hand-modelled map art (headless Blender). Geometry is built in ROBLOX space
# (X east, Y up, Z south; 1 unit = 1 stud) with bmesh, then rotated into Blender space with the
# K matrix (Roblox (x,y,z) -> Blender (-x,z,y), a proper rotation), so an add-on upload lands
# every mesh predictably: part centre = mesh bbox centre, identity rotation.
#
# Colour: ONE palette texture per package (512x512, 16 vertical gradient strips dark->light). Every face loop gets a UV
# (u = its strip, v = its shade), so faces read as flat colours with soft gradients (no photo textures).
# Glow pieces (lava, fire, bluefire) are separate meshes; the setup module makes them Neon in their glow colour.
import bpy, bmesh, math, os, json, random
import numpy as np
from mathutils import Vector, Matrix, Euler, noise as mn

OUT = os.path.join(os.getcwd(), 'out')          # palette PNGs land next to the build
WORK = OUT
PREV = os.path.join(os.getcwd(), 'previews')
for _d in (OUT, WORK, PREV): os.makedirs(_d, exist_ok=True)

KM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
def r2b(p): return KM @ Vector(p)
def b2r(p): return KM.inverted() @ Vector(p)

def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, t): return a + (b - a) * t
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)

def nz(x, y, z, s=1.0, seed=0):
    """perlin in 0..1"""
    return mn.noise(Vector((x / s + seed * 17.13, y / s + seed * 3.7, z / s - seed * 9.1))) * .5 + .5

# ------------------------------------------------------------------ palette
NCOL, CW, IMG = 16, 32, 512
class Palette:
    def __init__(self, ramps):
        """ramps: {name: (dark, mid, light)} in column order (max 16). 'white' is always added for glow meshes."""
        self.names = ['white'] + [n for n in ramps if n != 'white']
        assert len(self.names) <= NCOL
        self.ramps = dict(ramps); self.ramps['white'] = ('#ffffff', '#ffffff', '#ffffff')
    def u(self, name): return (self.names.index(name) + .5) / NCOL
    def image(self, tag):
        px = np.zeros((IMG, IMG, 4), dtype=np.float32); px[..., 3] = 1
        v = np.linspace(0, 1, IMG)
        for i, n in enumerate(self.names):
            d, m, l = [np.array(hexrgb(c)) for c in self.ramps[n]]
            t = v[:, None]
            col = np.where(t < .5, d + (m - d) * (t / .5), m + (l - m) * ((t - .5) / .5))
            px[:, i * CW:(i + 1) * CW, :3] = col[:, None, :]
        img = bpy.data.images.new(tag + '_Pal', IMG, IMG, alpha=False)
        img.pixels.foreach_set(px.ravel())
        path = os.path.join(OUT, tag + '_Palette.png')
        img.filepath_raw = path; img.file_format = 'PNG'; img.save(); img.pack()
        return img
    def material(self, tag):
        img = self.image(tag)
        m = bpy.data.materials.new(tag + '_Mat'); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img; tex.interpolation = 'Linear'
        nt.links.new(tex.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = .85
        return m

# ------------------------------------------------------------------ shading rules (face -> per-loop (u, v))
class Sh:
    """shade spec: col = palette column; facet: v = base + up * n.y + jitter (one value per face = flat faceted look);
    grad: per-vertex v by height between y0..y1 (soft gradient); top: faces with n.y > thr use col_top"""
    def __init__(self, pal, col, base=.5, up=.25, jit=.1, grad=None, top=None, thr=.6, topbase=None, seed=0, vn=None):
        self.pal, self.col, self.base, self.up, self.jit = pal, col, base, up, jit
        self.grad, self.top, self.thr, self.topbase = grad, top, thr, topbase
        self.rng = random.Random(seed); self.vn = vn
    def __call__(self, f):
        n = f.normal
        col = self.col; base = self.base
        if self.top and n.y > self.thr:
            col = self.top; base = self.topbase if self.topbase is not None else base
        u = self.pal.u(col)
        if self.grad:
            y0, y1, a, b = self.grad
            out = []
            for l in f.loops:
                p = l.vert.co
                t = clamp((p.y - y0) / (y1 - y0))
                v = lerp(a, b, t) + self.up * n.y * .3
                if self.vn: v += (nz(p.x, p.y, p.z, self.vn[0], self.vn[1]) - .5) * self.vn[2]
                out.append((u, clamp(v, .04, .96)))
            return out
        v = base + self.up * n.y + (self.rng.random() - .5) * 2 * self.jit
        return [(u, clamp(v, .04, .96))] * len(f.loops)

# ------------------------------------------------------------------ mesh accumulator
class MB:
    def __init__(self):
        self.V = []; self.F = []; self.UV = []; self.SM = []
    def add(self, bm, shade, smooth=False):
        bm.normal_update()
        base = len(self.V)
        bm.verts.index_update()
        self.V.extend(tuple(v.co) for v in bm.verts)
        for f in bm.faces:
            self.F.append(tuple(base + v.index for v in f.verts))
            self.UV.append(shade(f))
            self.SM.append(smooth)
        bm.free()
    def merge(self, o):
        b = len(self.V); self.V += o.V; self.F += [tuple(i + b for i in f) for f in o.F]; self.UV += o.UV; self.SM += o.SM
    @property
    def tris(self): return sum(len(f) - 2 for f in self.F)

# ------------------------------------------------------------------ primitives (bmesh in Roblox space)
def xf(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=None, order='YXZ'):
    """rot = (pitch about X, yaw about Y, roll about Z) in degrees"""
    if scale is not None:
        bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    if any(rot):
        e = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), order)
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=e.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return bm

def bevel(bm, off, seg=1, edges=None):
    if off <= 0: return bm
    bmesh.ops.bevel(bm, geom=list(edges if edges is not None else bm.edges), offset=off, offset_type='OFFSET', segments=seg,
                    profile=.5, affect='EDGES', clamp_overlap=True)
    return bm

def box(size, bev=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    return bevel(bm, min(bev, min(size) * .45))

def hull(pts):
    bm = bmesh.new()
    for p in pts: bm.verts.new(p)
    r = bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
    kill = list({g for g in r['geom_interior'] + r['geom_unused'] if isinstance(g, bmesh.types.BMVert)})
    if kill: bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2), verts=list(bm.verts), edges=list(bm.edges))
    return bm

def rock_pts(r, n=26, seed=0, flat=None, squash=1.0):
    """points on a lumpy ellipsoid (radii r = (rx, ry, rz)); flat = cut the bottom at -ry * flat"""
    rng = random.Random(seed); pts = []
    for i in range(n):
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if .2 < v.length <= 1: break
        v.normalize(); k = rng.uniform(.82, 1.08)
        p = Vector((v.x * r[0] * k, v.y * r[1] * k, v.z * r[2] * k))
        if flat is not None: p.y = max(p.y, -r[1] * flat)
        pts.append(p)
    if flat is not None:
        for a in range(6):
            t = a / 6 * math.tau + rng.random() * .4
            pts.append(Vector((math.cos(t) * r[0] * .8, -r[1] * flat, math.sin(t) * r[2] * .8)))
    return pts

def rock(r, seed=0, n=26, flat=.55):
    return hull(rock_pts(r, n, seed, flat))

def ngon_prism(poly, y0, y1, bev=0.0):
    """poly = [(x, z), ...] counter-clockwise seen from above (+Y); extruded y0..y1, top edge chamfer"""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y1, z)) for x, z in poly]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, y0 - y1, 0)), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if bev > 0:
        top = [e for e in bm.edges if all(abs(v.co.y - y1) < 1e-4 for v in e.verts)]
        bevel(bm, bev, 1, top)
    return bm

def cyl(r, h, sides=6, bev=0.0, r2=None, y0=0.0, rot0=0.0):
    """vertical prism / frustum from y0 to y0 + h"""
    r2 = r if r2 is None else r2
    poly = [(math.cos(rot0 + a * math.tau / sides) * r, math.sin(rot0 + a * math.tau / sides) * r) for a in range(sides)]
    bm = ngon_prism(poly, y0, y0 + h, 0)
    if r2 != r:
        for v in bm.verts:
            if abs(v.co.y - (y0 + h)) < 1e-4: v.co.x *= r2 / r; v.co.z *= r2 / r
    if bev > 0:
        top = [e for e in bm.edges if all(abs(v.co.y - (y0 + h)) < 1e-4 for v in e.verts)]
        bevel(bm, bev, 1, top)
    return bm

def spike(r, h, sides=6, tip=.0, y0=0.0, rot0=0.0, shoulder=.72):
    """a crystal / spire: prism up to h * shoulder, then a pyramid tip"""
    bm = bmesh.new()
    ring = lambda rr, y: [bm.verts.new((math.cos(rot0 + a * math.tau / sides) * rr, y, math.sin(rot0 + a * math.tau / sides) * rr)) for a in range(sides)]
    b = ring(r, y0); m = ring(r * .86, y0 + h * shoulder)
    t = bm.verts.new((0, y0 + h, 0)) if tip <= 0 else None
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((b[i], b[j], m[j], m[i]))
        if t: bm.faces.new((m[i], m[j], t))
    if not t:
        tt = ring(tip, y0 + h); bm.faces.new(list(reversed(tt)) if False else tt)
        for i in range(sides):
            j = (i + 1) % sides; bm.faces.new((m[i], m[j], tt[j], tt[i]))
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def frames(pts):
    """parallel-transport frames along a polyline (Vectors)"""
    T = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        T.append((b - a).normalized())
    up = Vector((0, 1, 0)) if abs(T[0].y) < .9 else Vector((1, 0, 0))
    N = [T[0].cross(up).normalized()]
    for i in range(1, len(pts)):
        n = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(n.normalized() if n.length > 1e-6 else N[-1])
    B = [T[i].cross(N[i]) for i in range(len(pts))]
    return T, N, B

def tube(pts, radii, sides=6, cap0=True, cap1=True, rough=0.0, seed=0, flat=None, rot0=0.0):
    """swept polygon along pts; radii scalar or list; rough = random ring radius jitter; flat = (sx, sy) ellipse scale"""
    pts = [Vector(p) for p in pts]
    if not isinstance(radii, (list, tuple)): radii = [radii] * len(pts)
    T, N, B = frames(pts)
    rng = random.Random(seed)
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        r = radii[i]; ring = []
        for a in range(sides):
            ang = rot0 + a * math.tau / sides
            k = 1 + (rng.random() - .5) * 2 * rough
            sx, sy = flat if flat else (1, 1)
            ring.append(bm.verts.new(p + (N[i] * math.cos(ang) * sx + B[i] * math.sin(ang) * sy) * r * k))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for a in range(sides):
            b = (a + 1) % sides
            bm.faces.new((rings[i][a], rings[i][b], rings[i + 1][b], rings[i + 1][a]))
    if cap0 and radii[0] > 1e-4: bm.faces.new(list(reversed(rings[0])))
    if cap1 and radii[-1] > 1e-4: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def ribbon(pts, widths, y=None, lift=0.0):
    """a flat strip on the ground following pts (x, y, z); widths per point"""
    pts = [Vector(p) for p in pts]
    if not isinstance(widths, (list, tuple)): widths = [widths] * len(pts)
    bm = bmesh.new(); L = []; R = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        t = Vector((b.x - a.x, 0, b.z - a.z)).normalized()
        n = Vector((-t.z, 0, t.x))
        yy = (p.y if y is None else y) + lift
        L.append(bm.verts.new((p.x + n.x * widths[i] / 2, yy, p.z + n.z * widths[i] / 2)))
        R.append(bm.verts.new((p.x - n.x * widths[i] / 2, yy, p.z - n.z * widths[i] / 2)))
    for i in range(len(pts) - 1):
        f = bm.faces.new((L[i], R[i], R[i + 1], L[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    return bm

def grid(x0, x1, z0, z1, nx, nzz, hfun):
    """heightfield quad grid (Roblox space): y = hfun(x, z)"""
    bm = bmesh.new(); V = []
    for i in range(nx + 1):
        row = []
        x = x0 + (x1 - x0) * i / nx
        for j in range(nzz + 1):
            z = z0 + (z1 - z0) * j / nzz
            row.append(bm.verts.new((x, hfun(x, z), z)))
        V.append(row)
    for i in range(nx):
        for j in range(nzz):
            bm.faces.new((V[i][j], V[i][j + 1], V[i + 1][j + 1], V[i + 1][j]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    return bm

def strip_surface(xs, zf, zb, yf, yb=None):
    """a surface between a front curve z = zf(x) and a back curve zb(x) (quad strip over x samples), heights yf(x[, z])"""
    bm = bmesh.new(); A = []; Bv = []
    for x in xs:
        A.append(bm.verts.new((x, yf(x), zf(x))))
        Bv.append(bm.verts.new((x, (yb or yf)(x), zb(x))))
    for i in range(len(xs) - 1):
        bm.faces.new((A[i], A[i + 1], Bv[i + 1], Bv[i]))
    for f in bm.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    return bm

def voronoi_cells(x0, x1, z0, z1, cell, seed=0, jit=.42):
    """jittered-grid Voronoi cells clipped to the rectangle: list of (site, polygon[(x, z)])"""
    rng = random.Random(seed)
    nx = max(1, int((x1 - x0) / cell)); nzz = max(1, int((z1 - z0) / cell))
    S = {}
    for i in range(-1, nx + 1):
        for j in range(-1, nzz + 1):
            S[(i, j)] = (x0 + (i + .5 + rng.uniform(-jit, jit)) * cell, z0 + (j + .5 + rng.uniform(-jit, jit)) * cell)
    out = []
    for i in range(nx):
        for j in range(nzz):
            s = S[(i, j)]
            poly = [(s[0] - cell * 2, s[1] - cell * 2), (s[0] + cell * 2, s[1] - cell * 2), (s[0] + cell * 2, s[1] + cell * 2), (s[0] - cell * 2, s[1] + cell * 2)]
            for di in (-2, -1, 0, 1, 2):
                for dj in (-2, -1, 0, 1, 2):
                    if (di, dj) == (0, 0) or (i + di, j + dj) not in S: continue
                    o = S[(i + di, j + dj)]
                    poly = clip_half(poly, s, o)
                    if not poly: break
            poly = clip_rect(poly, x0, x1, z0, z1)
            if len(poly) >= 3: out.append((s, poly))
    return out

def clip_half(poly, s, o):
    """keep the side of the bisector of s-o closer to s"""
    mx, mz = (s[0] + o[0]) / 2, (s[1] + o[1]) / 2; nx, nzz = o[0] - s[0], o[1] - s[1]
    d = lambda p: (p[0] - mx) * nx + (p[1] - mz) * nzz
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = d(a), d(b)
        if da <= 0: out.append(a)
        if (da < 0) != (db < 0) and da != db:
            t = da / (da - db); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out

def clip_rect(poly, x0, x1, z0, z1):
    for s, o in (((x0 + 1, 0), (x0 - 1, 0)), ((x1 - 1, 0), (x1 + 1, 0)), ((0, z0 + 1), (0, z0 - 1)), ((0, z1 - 1), (0, z1 + 1))):
        # bisector trick: the half-plane through the edge
        if s[1] == 0 and o[1] == 0:
            e = (s[0] + o[0]) / 2; sgn = 1 if s[0] > o[0] else -1
            poly = clip_fn(poly, lambda p, e=e, sgn=sgn: (e - p[0]) * sgn)
        else:
            e = (s[1] + o[1]) / 2; sgn = 1 if s[1] > o[1] else -1
            poly = clip_fn(poly, lambda p, e=e, sgn=sgn: (e - p[1]) * sgn)
        if not poly: return []
    return poly

def clip_fn(poly, d):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        da, db = d(a), d(b)
        if da <= 0: out.append(a)
        if (da < 0) != (db < 0) and da != db:
            t = da / (da - db); out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out

def shrink(poly, k):
    cx = sum(p[0] for p in poly) / len(poly); cz = sum(p[1] for p in poly) / len(poly)
    return [(cx + (p[0] - cx) * k, cz + (p[1] - cz) * k) for p in poly]

def ccw(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return poly if a < 0 else list(reversed(poly))   # (x, z) with +Y up: CCW from above has negative signed area in x-z

# ------------------------------------------------------------------ output
class Out:
    """named groups -> uploaded meshes. solid groups use the palette; glow groups carry their Neon colour"""
    def __init__(self, pal, tag):
        self.pal, self.tag = pal, tag
        self.groups = {}; self.glow = {}
    def g(self, name, glow=None):
        if name not in self.groups:
            self.groups[name] = MB()
            if glow: self.glow[name] = hexrgb(glow)
        return self.groups[name]
    def add(self, name, bm, shade, smooth=False, glow=None):
        self.g(name, glow).add(bm, shade, smooth)
    def gadd(self, name, bm, glow):
        """a glow piece: uv on the white strip"""
        u = self.pal.u('white')
        self.g(name, glow).add(bm, lambda f: [(u, .5)] * len(f.loops))

    def build(self, coll, maxtris=16000, offset=(0, 0, 0)):
        mat = self.pal.material(self.tag)
        parts = []
        for name, mb in self.groups.items():
            if not mb.F: continue
            for k, piece in enumerate(split(mb, maxtris)):
                nm = name if k == 0 else '%s_%d' % (name, k)
                parts.append(make_obj(nm, piece, mat, coll, self.glow.get(name), offset))
        return parts, mat

def split(mb, maxtris):
    if mb.tris <= maxtris: return [mb]
    cents = [sum((Vector(mb.V[i]) for i in f), Vector()) / len(f) for f in mb.F]
    lo = Vector((min(c.x for c in cents), min(c.y for c in cents), min(c.z for c in cents)))
    hi = Vector((max(c.x for c in cents), max(c.y for c in cents), max(c.z for c in cents)))
    ax = max(range(3), key=lambda a: hi[a] - lo[a])
    order = sorted(range(len(mb.F)), key=lambda i: cents[i][ax])
    tri = [len(f) - 2 for f in mb.F]
    acc = 0; half = mb.tris / 2; cut = 0
    for n, i in enumerate(order):
        acc += tri[i]
        if acc >= half: cut = n + 1; break
    out = []
    for sel in (order[:cut], order[cut:]):
        m = MB(); remap = {}
        for i in sel:
            f = mb.F[i]
            nf = []
            for vi in f:
                if vi not in remap: remap[vi] = len(m.V); m.V.append(mb.V[vi])
                nf.append(remap[vi])
            m.F.append(tuple(nf)); m.UV.append(mb.UV[i]); m.SM.append(mb.SM[i])
        out += split(m, maxtris)
    return out

def make_obj(name, mb, mat, coll, glow, offset=(0, 0, 0)):
    """mesh in Blender space, origin = bbox centre; returns the part record (Roblox space centre / size)"""
    Vr = np.array(mb.V, dtype=np.float64)
    lo, hi = Vr.min(0), Vr.max(0); c = (lo + hi) / 2
    vb = [tuple(KM @ Vector(v - c)) for v in Vr]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vb, [], mb.F)
    uvl = me.uv_layers.new(name='UVMap')
    li = 0
    for fi, poly in enumerate(me.polygons):
        for k, l in enumerate(poly.loop_indices): uvl.data[l].uv = mb.UV[fi][k]
    me.polygons.foreach_set('use_smooth', mb.SM)
    me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free()
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = KM @ Vector(c + np.array(offset))
    coll.objects.link(ob)
    tris = len(me.polygons)
    return dict(name=name, c=[round(float(x), 3) for x in c], s=[round(float(x), 3) for x in (hi - lo)],
                glow=([round(x, 4) for x in glow] if glow else None), tris=tris)

def clean():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)
    for i in list(bpy.data.images): bpy.data.images.remove(i)

# ------------------------------------------------------------------ preview rendering (EEVEE; glow = emission)
def preview_setup(glowmap, sky=(0.09, 0.035, 0.04), sun_rot=(52, 0, 35), sun_col=(1.0, .78, .6), sun_e=3.2, glow_e=1.0):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    try: sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    except Exception: pass
    w = bpy.data.worlds.new('PrevWorld'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*sky, 1); bg.inputs[1].default_value = 1.6
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = sun_e; sun.data.color = sun_col; sun.data.angle = math.radians(3)
    sun.rotation_euler = Euler([math.radians(a) for a in sun_rot])
    try: sc.eevee.use_shadows = True
    except Exception: pass
    # glow meshes: an emission material (preview only, never uploaded)
    for ob in list(sc.objects):
        g = glowmap.get(ob.name)
        if ob.type == 'MESH' and g:
            m = bpy.data.materials.new('Glow_' + ob.name); m.use_nodes = True
            nt = m.node_tree; b = nt.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = (*g, 1)
            b.inputs['Emission Color'].default_value = (*g, 1); b.inputs['Emission Strength'].default_value = glow_e
            ob.data.materials.clear(); ob.data.materials.append(m)

def render(path, loc, tgt, lens=28, res=(1600, 900)):
    """loc / tgt in Roblox space"""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
    sc.camera = cam; cam.location = r2b(loc); cam.data.lens = lens; cam.data.clip_end = 6000; cam.data.clip_start = .5
    cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
