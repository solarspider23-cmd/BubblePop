# Riverfield Siege prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: a war a season old: pale limestone ashlar with mortar joints, dark oak with iron straps, rope, straw, scorch.
# Team colour (crimson 'red' / azure 'blue') only on painted shields, shutters, tent canvas and wood stripes. No flags.
# Signature edge detail: the sharpened-stake palisade (cut points, rope lashing band, iron cramps) on every trench lip.
# Shared base: battered ashlar plinth with a chamfered top course (walls, towers, keep, piers, well).
# Machinery (Prop, S, blob, materials, to_kit, bool_diff, arch_*) from the skill's grove module; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
from pro_lib import Palette, Sh, box, cyl, spike, tube, hull, rock_pts, rock, nz, clamp, ngon_prism

G.PAL = Palette({
    'grass':  ('#2c421a', '#587f30', '#a3c06a'),
    'dirt':   ('#33241a', '#6a4c36', '#a8876a'),
    'stone':  ('#5e5546', '#ada187', '#ebe1c8'),     # pale limestone ashlar (keeps, bridge)
    'stoneg': ('#36383e', '#73767d', '#b6b8bd'),     # old grey stone (chapel, field walls, rocks)
    'slate':  ('#1f2530', '#465268', '#8593ab'),     # roof slates
    'wood':   ('#46301f', '#7d5535', '#bd8c5c'),
    'wooddk': ('#17110c', '#3a2a1d', '#6a4c35'),     # old / charred oak
    'straw':  ('#6e521c', '#c29c46', '#f0da8e'),     # straw, rope, wicker
    'canvas': ('#6f6450', '#c9bc9c', '#f4ecd8'),
    'iron':   ('#121418', '#383c44', '#7b818c'),
    'red':    ('#4a0b10', '#a31e28', '#e65e68'),
    'blue':   ('#0b1d46', '#2350a4', '#6c97e6'),
    'brass':  ('#5e3f0e', '#b98428', '#f0cd78'),
    'water':  ('#0d262e', '#285a68', '#7aaeb9'),
    'pine':   ('#122a1b', '#264f31', '#5a8a5c'),
})
G.MATS.clear()
G.GLOW.clear(); G.GLOW.update({'fire': '#ff7a1e', 'ember': '#ff3e12', 'candle': '#ffc65a'})
G.GLOW_E.clear(); G.GLOW_E.update({'fire': 3.0, 'ember': 2.4, 'candle': 2.2})
Prop, S, blob, bool_diff = G.Prop, G.S, G.blob, G.bool_diff
PAL = G.PAL
TEAM = {'red': 'red', 'blue': 'blue'}

# ------------------------------------------------------------------ transforms + basic helpers
def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

def T(bm, pos=(0, 0, 0), yaw=0.0, pitch=0.0, roll=0.0, s=None):
    """roll (Z) first, then pitch (X), then yaw (Y, +yaw turns the -Z front toward -X), then move"""
    if s is not None: bmesh.ops.scale(bm, vec=Vector(s if isinstance(s, (tuple, list)) else (s, s, s)), verts=bm.verts)
    M = (Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Matrix.Rotation(math.radians(pitch), 3, 'X') @
         Matrix.Rotation(math.radians(roll), 3, 'Z'))
    bmesh.ops.rotate(bm, cent=Vector(), matrix=M, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(pos), verts=bm.verts)
    return bm

def frame_to(bm, a, b):
    """bm built along +X from 0..L (Y up): rotate X onto b - a (Y stays as up as possible), move to a"""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    up0 = Vector((0, 1, 0)) if abs(d.y) < .95 else Vector((1, 0, 0))
    z = d.cross(up0).normalized(); y = z.cross(d)
    M = Matrix((d, y, z)).transposed()
    bmesh.ops.rotate(bm, cent=Vector(), matrix=M, verts=bm.verts)
    bmesh.ops.translate(bm, vec=a, verts=bm.verts)
    return bm

def bar(a, b, w=.4, t=.4, bev=.05):
    """square timber from a to b (w across, t thick)"""
    L = (Vector(b) - Vector(a)).length
    bm = box((L, t, w), bev); bmesh.ops.translate(bm, vec=Vector((L / 2, 0, 0)), verts=bm.verts)
    return frame_to(bm, a, b)

def log(a, b, r=.4, sides=7, r2=None):
    return tube([Vector(a), Vector(b)], [r, r if r2 is None else r2], sides=sides)

def lathe(profile, n=24, a0=0.0):
    """revolve [(r, y), ...] (bottom -> top) around Y; r == 0 collapses to a point"""
    bm = bmesh.new(); rings = []
    for r, y in profile:
        if r <= 1e-4: rings.append([bm.verts.new((0, y, 0))])
        else: rings.append([bm.verts.new((math.cos(a0 + i * math.tau / n) * r, y, math.sin(a0 + i * math.tau / n) * r)) for i in range(n)])
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1: continue
        if len(A) == 1:
            for i in range(n): bm.faces.new((A[0], B[(i + 1) % n], B[i]))
        elif len(B) == 1:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[0]))
        else:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    if len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def torus(R, r, n=24, sides=6, a0=0.0, a1=math.tau):
    full = abs(a1 - a0 - math.tau) < 1e-6
    pts = [Vector((math.cos(a) * R, 0, math.sin(a) * R)) for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]
    return tube(pts, r, sides=sides, cap0=not full, cap1=not full)

def sag(a, b, drop, n=6):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, math.sin(i / n * math.pi) * drop, 0)) for i in range(n + 1)]

def h01(x, y, z):
    return (math.sin(x * 12.9898 + y * 78.233 + z * 37.719) * 43758.5453) % 1.0

# ------------------------------------------------------------------ masonry
def ashlar(w, h, bw=4.0, bh=1.9, seed=0, skip=None, depth=.12, ins=.09):
    """running-bond ashlar panel in the XY plane facing +Z: x -w/2..w/2, y 0..h. Each block is a quad inset into a
    raised face with mortar bevels (block faces get material_index 1 for ash_sh). skip(x, y) drops a block."""
    bm = bmesh.new(); rng = random.Random(seed)
    rows = max(1, round(h / bh)); bh2 = h / rows
    for i in range(rows):
        y0, y1 = i * bh2, (i + 1) * bh2
        x = -w / 2 - (bw * .5 if i % 2 else 0) - rng.uniform(0, bw * .3)
        while x < w / 2 - 1e-3:
            ww = bw * rng.uniform(.7, 1.3); xa, xb = max(x, -w / 2), min(x + ww, w / 2); x += ww
            if xb - xa < .25 or (skip and any(skip(xx, yy) for xx in (xa + .15, (xa + xb) / 2, xb - .15) for yy in (y0 + .15, (y0 + y1) / 2, y1 - .15))): continue
            f = bm.faces.new([bm.verts.new(p) for p in ((xa, y0, 0), (xb, y0, 0), (xb, y1, 0), (xa, y1, 0))])
    fs = list(bm.faces)
    bmesh.ops.inset_individual(bm, faces=fs, thickness=ins, depth=depth, use_even_offset=True)
    bm.normal_update()
    for f in bm.faces: f.material_index = 1 if f.normal.z > .999 else 0
    return bm

def ashlar_ring(R, y0, y1, bw=2.8, bh=1.5, seed=0, skip=None, depth=.1, ins=.08):
    """ashlar on a cylinder of radius R (flat chord blocks, random lengths per course); skip(angle, y)"""
    bm = bmesh.new(); rng = random.Random(seed)
    rows = max(1, round((y1 - y0) / bh)); bh2 = (y1 - y0) / rows; C = math.tau * R
    p = lambda a, y: (math.cos(a) * R, y, math.sin(a) * R)
    for i in range(rows):
        ya, yb = y0 + i * bh2, y0 + (i + 1) * bh2
        cuts = [0.0]
        while cuts[-1] < C - bw * .6: cuts.append(cuts[-1] + bw * rng.uniform(.65, 1.35))
        cuts[-1] = C; off = rng.uniform(0, math.tau)
        for s0, s1 in zip(cuts, cuts[1:]):
            n = max(1, int((s1 - s0) / (R * .7)) + 1)
            a0, a1 = off + s0 / R, off + s1 / R
            if skip and any(skip(aa % math.tau, (ya + yb) / 2) for aa in (a0 + .1 / R, (a0 + a1) / 2, a1 - .1 / R)): continue
            angs = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
            bot = [bm.verts.new(p(a, ya)) for a in angs]; top = [bm.verts.new(p(a, yb)) for a in angs]
            bm.faces.new([bot[k] for k in range(n, -1, -1)] + [top[k] for k in range(n + 1)])
    fs = list(bm.faces)
    bmesh.ops.inset_individual(bm, faces=fs, thickness=ins, depth=depth, use_even_offset=True)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median(); rad = Vector((c.x, 0, c.z)).normalized()
        f.material_index = 1 if f.normal.dot(rad) > .99 else 0
    return bm

def ash_sh(col='stone', base=.62, var=.07, up=.08, grime=.08):
    """per-block tone from the block centre hash, mortar darker, a little grime low down"""
    u = PAL.u(col)
    def f_(f):
        c = f.calc_center_median()
        if f.material_index == 1: v = base + (h01(c.x, c.y, c.z) - .5) * 2 * var + up * f.normal.y
        else: v = base - .3
        v -= grime * (1 - smooth((c.y + 1) / 7))
        return [(u, clamp(v, .04, .96))] * len(f.loops)
    return f_

def stone(P, c, size, yaw=0.0, col='stoneg', base=.55, bev=0.0, seed=0, pitch=0.0, roll=0.0):
    """one real block (ruins, rubble, steps, quoins)"""
    rng = random.Random(seed)
    P.add(T(box(size, bev), c, yaw, pitch, roll), S(col, base=base + rng.uniform(-.06, .06), up=.12, jit=.02, seed=seed))

def course_wall(P, a, b, y0, top, thick, bl=2.4, bh=1.2, col='stoneg', base=.56, seed=0, holes=(), bev_top=.12, jitter=.06, bottom=None):
    """a wall of real stone blocks from (x, z) a to b: top(t) = top height at distance t along the wall,
    holes = [(t0, t1, ylo, yhi(t))] openings. Blocks are clipped to holes; the top row is bevelled."""
    rng = random.Random(seed); ax, az = a; bx, bz = b
    L = math.hypot(bx - ax, bz - az); dx, dz = (bx - ax) / L, (bz - az) / L
    yaw = math.degrees(math.atan2(-dz, dx))
    i = 0; y = y0
    while True:
        yc = y + bh / 2; t = -(bl * .5 if i % 2 else 0) - rng.uniform(0, .5)
        any_row = False
        while t < L - 1e-3:
            ln = bl * rng.uniform(.7, 1.25); ta, tb = max(t, 0.0), min(t + ln, L); t += ln
            segs = [(ta, tb)]
            for h0, h1, ylo, yhi in holes:
                nxt = []
                for sa, sb in segs:
                    tm = (max(sa, h0) + min(sb, h1)) / 2
                    tc = min(max(tm, h0), h1); yl = ylo(tc) if callable(ylo) else ylo
                    if sb <= h0 or sa >= h1 or not (yl <= yc <= yhi(tc)): nxt.append((sa, sb)); continue
                    if sa < h0: nxt.append((sa, h0))
                    if sb > h1: nxt.append((h1, sb))
                segs = nxt
            for sa, sb in segs:
                tm = (sa + sb) / 2
                if sb - sa < .35 or yc > top(tm) or (bottom and yc < bottom(tm)): continue
                any_row = True
                last = yc + bh > top(tm)
                gap = .07
                cx, cz = ax + dx * tm, az + dz * tm
                off = rng.uniform(-jitter, jitter)
                P.add(T(box((sb - sa - gap, bh - gap, thick + rng.uniform(-.1, .1)), bev_top if last else 0.0),
                        (cx - dz * off, yc, cz + dx * off), yaw + rng.uniform(-1.5, 1.5)),
                      S(col, base=base + rng.uniform(-.07, .07) - .1 * (1 - smooth(yc / 5)), up=.12, jit=.02, seed=seed + i))
        if not any_row and y > max(top(L * k / 8) for k in range(9)): break
        y += bh; i += 1
        if y > 60: break

def merlon_row(P, L, y, z, depth, mw=2.2, gap=1.4, mh=2.0, col='stone', slit=True, seed=0):
    """crenellation along X centred at x = 0, merlons with cut arrow slits (every other one)"""
    n = max(1, int((L + gap) / (mw + gap))); span = n * mw + (n - 1) * gap; x0 = -span / 2 + mw / 2
    for k in range(n):
        x = x0 + k * (mw + gap)
        m = box((mw, mh, depth)); T(m, (x, y + mh / 2, z))
        if slit and k % 2 == 1:
            m = bool_diff(m, T(box((.26, 1.1, depth + 1)), (x, y + mh * .5, z)))
        P.add(m, S(col, base=.64 + random.Random(seed + k).uniform(-.05, .05), up=.12, jit=.03))
        P.add(T(box((mw + .2, .22, depth + .2), .08), (x, y + mh + .11, z)), S(col, base=.72, up=.1, jit=.02))

def corbels(P, L, y, z0, out, pitch=2.4, col='stone'):
    """stepped corbel blocks along X under a projecting parapet, projecting from z0 by out (sign = direction)"""
    n = int(L / pitch); s = 1 if out > 0 else -1
    for k in range(n):
        x = -L / 2 + (k + .5) * L / n
        P.add(T(box((.9, .6, abs(out))), (x, y - .3, z0 + out / 2)), S(col, base=.6, up=.1, jit=.03))
        P.add(T(box((.9, .55, abs(out) * .55)), (x, y - .85, z0 + out * .275)), S(col, base=.56, up=.1, jit=.03))

def slit_frame(P, pos, yaw, h=2.4, col='stone'):
    """dressed frame round a CUT arrow slit (front = -Z before yaw): jambs, lintel, sill proud; the cut is lined
    dark from 0.3 behind the face so the slit reads as a deep black slot"""
    for sx in (-1, 1): P.add(T(T(box((.7, h + .3, .5), .06), (sx * .8, h / 2, -.1)), pos, yaw), S(col, base=.7, up=.1, jit=.02))
    P.add(T(T(box((2.3, .5, .55), .06), (0, h + .3, -.12)), pos, yaw), S(col, base=.72, up=.1, jit=0))
    P.add(T(T(box((2.3, .35, .65), .06), (0, -.12, -.15)), pos, yaw), S(col, base=.66, up=.1, jit=0))
    P.add(T(T(box((.92, h + .02, 1.0)), (0, h / 2, .85)), pos, yaw), S('iron', base=.05, up=0, jit=0))

def slit_cutter(cut, pos, yaw, h=2.4, depth=1.6):
    """add an arrow-slit cutter box (front = -Z before yaw, from 0.3 out to depth in) into bmesh cut"""
    add_into(cut, T(T(box((.9, h, depth + .3)), (0, h / 2, depth / 2 - .15)), pos, yaw))

def add_into(dst, bm):
    import bpy
    me = bpy.data.meshes.new('_tmp'); bm.to_mesh(me); bm.free(); dst.from_mesh(me); bpy.data.meshes.remove(me)
    return dst

def merge(P, tmp, yaw=0.0, pos=(0, 0, 0)):
    """move a temp Prop built in canonical orientation (front face at -Z) into P, turned by yaw"""
    M = Matrix.Rotation(math.radians(yaw), 3, 'Y'); o = Vector(pos)
    for src, dst in [(tmp.solid, P.solid)] + [(mb, P.glow.setdefault(k, G.MB())) for k, mb in tmp.glow.items()]:
        src.V = [tuple(M @ Vector(v) + o) for v in src.V]; dst.merge(src)

def heater_shield(P, pos, yaw, team, s=1.0, tilt=0.0, stripe='brass'):
    """painted heater shield facing -Z before yaw: oak backing rim, painted field, chevron, brass boss"""
    out = [(-.62, 1.3), (.62, 1.3)]
    for k in range(1, 8):
        t = k / 8; out.append((.62 * math.cos(t * math.pi / 2) ** .8, 1.3 - t * 1.3 * .55 - t * t * .7))
    out.append((0, 0))
    for k in range(7, 0, -1):
        t = k / 8; out.append((-.62 * math.cos(t * math.pi / 2) ** .8, 1.3 - t * 1.3 * .55 - t * t * .7))
    poly = [(x * s, y * s) for x, y in out]
    def plate(pp, z0, z1):
        bm = ngon_prism(pp, z0, z1); return T(bm, (0, 0, 0), 0, -90)   # prism (x, z) -> vertical, extrusion -> -Z
    rim = plate([(x * 1.08, y * 1.04 - .03 * s) for x, y in poly], 0, .12 * s)
    face = plate([(x * .94, y * .96 + .03 * s) for x, y in poly], .12 * s, .2 * s)
    for bm, sh in ((rim, S('wooddk', base=.45, up=.1, jit=0)), (face, S(team, base=.55, up=.1, jit=.02))):
        P.add(T(bm, pos, yaw, tilt), sh)
    for sg in (-1, 1):                                                         # chevron
        P.add(T(T(box((.95 * s, .16 * s, .06 * s)), (sg * .3 * s, .62 * s, -.23 * s), 0, 0, sg * 38), pos, yaw, tilt), S(stripe, base=.62, jit=0))
    P.add(T(T(lathe([(0, 0), (.2 * s, 0), (.18 * s, .08 * s), (.08 * s, .15 * s), (0, .16 * s)], n=8), (0, .78 * s, -.2 * s), 0, -90), pos, yaw, tilt), S('brass', base=.6, jit=0))

def plinth_band(P, L, z, y=2.2, out=.35, col='stone'):
    P.add(T(box((L, .55, abs(out) * 2), .16), (0, y + .27, z)), S(col, base=.66, up=.15, jit=.02))

# ------------------------------------------------------------------ keep: curtain wall, towers, gatehouse, donjon, stair
WALL_H, WALL_T = 14.0, 6.0

def curtain_wall(L=30.0, team='red', H=WALL_H, Tk=WALL_T):
    """wall segment along X (outside = -Z): battered plinth, ashlar both faces, corbelled parapet with cut merlons,
    flagstone wall-walk, inner kerb, team shields on the parapet. Ends are open (towers cover them)."""
    P = Prop('CurtainWall%d_%s' % (L, team)); sd = int(L * 7)
    P.add(T(box((L, H + 2, Tk - .4)), (0, H / 2 - 1, 0)), S('stone', base=.45, jit=0))
    for sg in (-1, 1):                                                          # battered plinth (shared base)
        pts = [Vector((x, y, sg * zz)) for x in (-L / 2, L / 2) for y, zz in ((-2.0, Tk / 2 + 1.5), (2.2, Tk / 2 + .06), (2.2, Tk / 2 - .5), (-2.0, Tk / 2 - .5))]
        P.add(hull(pts), S('stone', base=.5, up=.18, jit=.02))
        plinth_band(P, L, sg * (Tk / 2), out=.35)
    P.add(T(ashlar(L, H - 2.8, seed=sd), (0, 2.8, -Tk / 2), 180), ash_sh())
    P.add(T(ashlar(L, H - 2.8, seed=sd + 1), (0, 2.8, Tk / 2)), ash_sh())
    zf = -Tk / 2 - .6                                                           # parapet on corbels
    corbels(P, L, H - 1.0, -Tk / 2, -.6)
    P.add(T(box((L, 2.8, 1.6)), (0, H + .4, zf + .8)), S('stone', base=.5, jit=0))
    P.add(T(ashlar(L, 2.8, bw=3.4, bh=1.4, seed=sd + 2), (0, H - 1.0, zf - .02), 180), ash_sh(base=.64))
    P.add(T(ashlar(L, 1.9, bw=2.6, bh=.95, seed=sd + 4, depth=.06), (0, H, zf + 1.6)), ash_sh(base=.58, grime=0))
    P.add(T(box((L, .24, 1.9), .08), (0, H + 1.92, zf + .8)), S('stone', base=.72, up=.1, jit=.02))
    merlon_row(P, L - 1.4, H + 2.04, zf + .8, 1.5, seed=sd)
    P.add(T(ashlar(L, Tk - 1.0, bw=4.0, bh=2.6, seed=sd + 3, depth=.05), (0, H + .01, Tk / 2), 0, -90), ash_sh(base=.58, up=0))
    P.add(T(box((L, .7, .8), .12), (0, H + .35, Tk / 2 - .4)), S('stone', base=.66, up=.15, jit=.02))
    n = int(L / 9)
    for k in range(n):                                                          # shields between merlons, outside
        x = -L / 2 + (k + .5) * L / n
        heater_shield(P, (x, H - .4, zf - .1), 0, team, s=1.25)
    return P

def tower_body(P, cx, cz, R, H, team, seed=0, roof=True, slits=4, slit_a0=0.0):
    """round tower: battered base, ashlar drum with CUT arrow slits, corbel ring, crenellated parapet with cut
    merlon slits, conical slate roof (stepped courses) + iron finial and brass ball"""
    sl = [(slit_a0 + k * math.tau / slits, H * .5) for k in range(slits)]
    core = T(cyl(R - .12, H + 2, sides=24, y0=-2), (cx, 0, cz)); cut = bmesh.new()
    for a, y in sl:
        yaw = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        slit_cutter(cut, (cx + math.cos(a) * (R - .12), y, cz + math.sin(a) * (R - .12)), yaw, h=2.6)
    if slits: core = bool_diff(core, cut)
    else: cut.free()
    P.add(core, S('stone', base=.42, jit=0))
    P.add(T(lathe([(R + 1.7, -2.2), (R + 1.7, -.4), (R + .06, 3.0), (0, 3.0)], n=24), (cx, 0, cz)), S('stone', base=.5, up=.18, jit=.02))
    P.add(T(lathe([(R + .4, 3.0), (R + .4, 3.5), (R + .1, 3.7), (0, 3.7)], n=24), (cx, 0, cz)), S('stone', base=.66, up=.1, jit=.02), smooth=True)
    def skip(ang, y):
        return any(abs((ang - a + math.pi) % math.tau - math.pi) * R < 1.2 and y0 - .6 < y < y0 + 3.2 for a, y0 in sl)
    P.add(T(ashlar_ring(R, 3.7, H - 1.4, bw=4.2, bh=2.0, seed=seed, skip=skip), (cx, 0, cz)), ash_sh())
    for a, y in sl:
        yaw = math.degrees(math.atan2(-math.cos(a), -math.sin(a)))
        slit_frame(P, (cx + math.cos(a) * (R + .1), y, cz + math.sin(a) * (R + .1)), yaw, h=2.6)
    nc = max(10, int(math.tau * R / 2.4))
    for k in range(nc):                                                         # corbel ring
        a = k * math.tau / nc
        for j, (o, hh, y) in enumerate(((.8, .7, H - 1.75),)):
            P.add(T(box((.8, hh, o)), (cx + math.cos(a) * (R + o / 2), y, cz + math.sin(a) * (R + o / 2)), -math.degrees(a) + 90), S('stone', base=.6 - j * .04, up=.1, jit=.03))
    P.add(T(lathe([(R + .8, H - 1.4), (R + .8, H + 1.3), (R - .7, H + 1.3), (R - .7, H - .3), (0, H - .3)], n=28), (cx, 0, cz)), S('stone', base=.6, up=.1, jit=.02))
    P.add(T(ashlar_ring(R + .82, H - 1.4, H + 1.3, bw=2.4, bh=1.35, seed=seed + 3), (cx, 0, cz)), ash_sh(base=.64))
    nm = max(6, int(math.tau * (R + .05) / 3.6))
    for k in range(nm):
        a = (k + .25) * math.tau / nm; yaw = -math.degrees(a) + 90
        m = box((2.0, 1.9, 1.5))
        if k % 2: m = bool_diff(m, box((.26, 1.0, 2.5)))
        P.add(T(T(m, (0, .95, 0)), (cx + math.cos(a) * (R + .05), H + 1.3, cz + math.sin(a) * (R + .05)), yaw), S('stone', base=.64, up=.12, jit=.03))
        P.add(T(box((2.2, .22, 1.7), .08), (cx + math.cos(a) * (R + .05), H + 3.31, cz + math.sin(a) * (R + .05)), yaw), S('stone', base=.72, up=.1, jit=0))
    if roof:
        Rb, yb, hr, N = R - .5, H + 1.0, R * 1.75, 9
        prof = [(0, yb - .2), (Rb + .5, yb - .2)]
        for k in range(N):
            t0, t1 = k / N, (k + 1) / N
            r0, r1 = Rb * (1 - t0) ** 1.1 + .5 * (1 - t0), Rb * (1 - t1) ** 1.1 + .5 * (1 - t1)
            prof += [(r0 + .22, yb + t0 * hr), (r1 + .02, yb + t1 * hr - .05)]
        prof += [(.25, yb + hr), (0, yb + hr + .1)]
        P.add(T(lathe(prof, n=16), (cx, 0, cz)), S('slate', base=.5, up=.25, jit=.06, seed=seed))
        P.add(T(lathe([(0, 0), (.3, 0), (.32, .5), (.12, .7), (.12, 2.4), (0, 3.6)], n=8), (cx, yb + hr - .1, cz)), S('iron', base=.45, jit=0))
        P.add(T(lathe([(0, 0), (.35, .1), (.45, .45), (.3, .8), (0, .9)], n=10), (cx, yb + hr + 1.0, cz)), S('brass', base=.6, jit=0), smooth=True)
    if team:
        for k in range(2):
            a = slit_a0 + math.pi / slits + k * math.pi
            heater_shield(P, (cx + math.cos(a) * (R + .95), H - .8, cz + math.sin(a) * (R + .95)), math.degrees(math.atan2(-math.cos(a), -math.sin(a))), team, s=1.3)

def round_tower(team='red', H=26.0, R=8.5):
    P = Prop('Tower_%s' % team)
    tower_body(P, 0, 0, R, H, team, seed=5, slits=4, slit_a0=math.pi * .25)
    return P

def ell_outline(hw, spring, rise, n=16):
    """elliptical / segmental arch outline in XY, open at the bottom (feet at y = 0)"""
    pts = [(-hw, 0.0), (-hw, spring)]
    pts += [(-math.cos(math.pi * i / n) * hw, spring + math.sin(math.pi * i / n) * rise) for i in range(1, n)]
    return pts + [(hw, spring), (hw, 0.0)]

def outline_prism(L, z0, z1, y0=None):
    """closed solid of an outline (XY) from z0 to z1; y0 extends the feet down"""
    bm = bmesh.new(); L = [(x, y if (y > 0 or y0 is None) else y0) for x, y in L]
    F = [bm.verts.new((x, y, z1)) for x, y in L]; B = [bm.verts.new((x, y, z0)) for x, y in L]
    bm.faces.new(F); bm.faces.new(list(reversed(B)))
    for i in range(len(L)): j = (i + 1) % len(L); bm.faces.new((F[j], F[i], B[i], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def in_arch(x, y, hw, spring, rise, m=0.0):
    if abs(x) > hw + m or y < -1: return False
    if y <= spring: return True
    return (x / (hw + m)) ** 2 + ((y - spring) / (rise + m)) ** 2 <= 1.0

def voussoirs(P, cx, y0, z, hw, spring, rise, depth=.6, band=1.3, n=13, col='stone', base=.7, quoins=True, keep=None):
    """wedge stones round an arch (face plane at z, half proud), bigger keystone, jamb quoins down the sides"""
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        kb = band * (1.35 if k == n // 2 else 1.0); pts = []
        for a in (a0 + .015, a1 - .015):
            for b_ in (0, kb):
                x = cx - math.cos(a) * (hw + b_); y = y0 + spring + math.sin(a) * (rise + b_)
                for zz in (z - depth / 2, z + depth / 2): pts.append(Vector((x, y, zz)))
        if keep and not keep(sum(p.x for p in pts) / len(pts)): continue
        P.add(hull(pts), S(col, base=base + (h01(k, a0, z) - .5) * .1, up=.12, jit=.02))
    if quoins:
        rows = max(1, int(spring / 1.3))
        for sg in (-1, 1):
            for i in range(rows):
                w = band * (1.0 if i % 2 else .65); hh = spring / rows
                P.add(T(box((w, hh - .08, depth)), (cx + sg * (hw + w / 2), y0 + i * hh + hh / 2, z)),
                      S(col, base=base - .03 + (h01(i, sg, z) - .5) * .08, up=.12, jit=.02))

def parapet_front(P, L, y, d, seed, team=None, shields=0, mw=2.2, gap=1.4, mtrim=6.0, ps=1.5):
    """corbelled crenellated parapet on a front face at z = -d (canonical), wall-walk at height y"""
    corbels(P, L, y - 1.0, -d, -.6)
    zf = -d - .6
    P.add(T(box((L, 2.8, 1.6)), (0, y + .4, zf + .8)), S('stone', base=.5, jit=0))
    P.add(T(ashlar(L, 2.8, bw=2.6, bh=1.4, seed=seed), (0, y - 1.0, zf - .02), 180), ash_sh(base=.64))
    P.add(T(ashlar(L, 1.9, bw=2.6, bh=.95, seed=seed + 4, depth=.06), (0, y, zf + 1.6)), ash_sh(base=.58, grime=0))
    P.add(T(box((L + .1, .24, 1.9), .08), (0, y + 1.92, zf + .8)), S('stone', base=.72, up=.1, jit=.02))
    merlon_row(P, L - mtrim, y + 2.04, zf + .8, 1.5, mw=mw, gap=gap, seed=seed)
    for k in range(shields):
        x = -L / 2 + (k + .5) * L / shields
        heater_shield(P, (x, y - .4, zf - .1), 0, team, s=ps)

def gatehouse(team='red', W=30.0, D=16.0, H=18.0, gw=10.0, spring=8.0, rise=5.0):
    """the keep gate (outside = -Z): ashlar block with a CUT arched passage, voussoirs, raised portcullis, open oak
    doors, corbelled crenellated top, two D-towers flanking the arch, team shields"""
    P = Prop('Gatehouse_%s' % team); hw = gw / 2
    core = T(box((W - .4, H + 2, D - .4)), (0, H / 2 - 1, 0))
    core = bool_diff(core, outline_prism(ell_outline(hw, spring, rise), -D / 2 - 1, D / 2 + 1, y0=-3))
    P.add(core, S('stone', base=.5, jit=.02))
    for sg in (-1, 1):
        for sx in (-1, 1):
            pts = [Vector((sx * x, y, sg * zz)) for x in (W / 2, hw + .1) for y, zz in ((-2.0, D / 2 + 1.5), (2.2, D / 2 + .06), (2.2, D / 2 - .5), (-2.0, D / 2 - .5))]
            P.add(hull(pts), S('stone', base=.5, up=.18, jit=.02))
    sk = lambda x, y: in_arch(x, y + 2.2, hw, spring, rise, 1.2)
    P.add(T(ashlar(W, H - 2.2, seed=31, skip=sk), (0, 2.2, -D / 2), 180), ash_sh())
    P.add(T(ashlar(W, H - 2.2, seed=32, skip=sk), (0, 2.2, D / 2)), ash_sh())
    for sg in (-1, 1):
        P.add(T(ashlar(D - .6, spring - .2, bw=2.6, seed=33 + sg, depth=.06), (sg * (hw - .02), 0, 0), -90 * sg), ash_sh(base=.56))
        voussoirs(P, 0, 0, sg * (D / 2 + .1), hw, spring, rise)
    P.add(T(box((gw + .2, .3, D + .4)), (0, -.15, 0)), S('stoneg', base=.5, jit=.05))
    for k in range(int(D / 2)):
        P.add(T(box((gw - .3, .12, 1.8), .04), (0, .02, -D / 2 + 1 + k * 2)), S('stoneg', base=.56 + (k % 2) * .06, jit=.02))
    zp = -D / 2 + 2.2                                                          # portcullis, raised into its slot
    for k in range(7):
        x = -hw + .8 + k * (gw - 1.6) / 6
        P.add(T(box((.32, 5.0, .32)), (x, spring + 1.4, zp)), S('iron', base=.42, jit=0))
        P.add(T(spike(.2, .9, sides=4, rot0=math.pi / 4), (x, spring - 1.1, zp), 0, 180), S('iron', base=.5, jit=0))
    for j in range(3): P.add(T(box((gw - .6, .3, .34)), (0, spring - .6 + j * 1.4, zp)), S('iron', base=.38, jit=0))
    for sg in (-1, 1):                                                          # open oak doors against the passage walls
        hx = sg * (hw - .35); z0 = D / 2 - 1.0
        for i in range(6):
            u = (i + .5) / 6 * hw; xo = sg * (hw - u)
            top = spring + rise * math.sqrt(max(0, 1 - (xo / hw) ** 2)) - .3
            P.add(T(box((.4, top, hw / 6 - .05), .04), (hx, top / 2, z0 - u)), S('wood', base=.5 + (i % 2) * .06, up=.1, jit=.02))
        for y in (1.6, spring * .55, spring - .4):
            P.add(T(box((.16, .4, hw * .92), .04), (hx - sg * .28, y, z0 - hw * .47)), S('iron', base=.4, jit=0))
            for k in range(4): P.add(T(cyl(.11, .14, sides=5), (hx - sg * .3, y, z0 - .4 - k * hw * .28), 0, 0, 90), S('iron', base=.6, jit=0))
    parapet_front(P, W, H, D / 2, 34, mtrim=14)
    P.add(T(box((W, 1.4, 1.0), .1), (0, H + .7, D / 2 - .5)), S('stone', base=.62, up=.1, jit=.02))
    P.add(T(ashlar(W, D - 1.6, bw=2.6, bh=2.0, seed=36, depth=.05), (0, H + .01, D / 2 - 1.0), 0, -90), ash_sh(base=.58, up=0))
    for sg in (-1, 1):
        tower_body(P, sg * 12.6, -D / 2 + .5, 5.4, H + 4.5, None, seed=37 + sg, slits=2, slit_a0=math.radians(215 if sg < 0 else -35))
        heater_shield(P, (sg * 7.4, spring + rise + 2.6, -D / 2 - .45), 0, team, s=1.6)
    return P

def donjon_face(P, W, H, hw, opens, team, seed, door=None, top=False):
    """one face of the donjon in canonical orientation (face plane z = -hw): ashlar with openings, voussoirs,
    sills, dark panes + open team shutters, the oak door, corbelled parapet + shields"""
    if top:
        parapet_front(P, W + 1.2, H, hw, seed + 9, team, shields=2, mtrim=6.0); return
    def sk(x, y):
        yy = y + 2.9
        return any(in_arch(x - ox, yy - oy, a, b, c, .6) for ox, oy, a, b, c in opens + ([door] if door else []))
    P.add(T(ashlar(W, H - 4.3, bw=4.0, bh=1.9, seed=seed, skip=lambda x, y: sk(-x, y)), (0, 2.9, -hw), 180), ash_sh())
    for ox, oy, a, b, c in opens:
        voussoirs(P, ox, oy, -hw, a, b, c, depth=.5, band=.8, n=9)
        P.add(T(box((a * 2 + .7, .35, .9), .06), (ox, oy - .1, -hw - .25)), S('stone', base=.72, up=.1, jit=0))
        P.add(T(box((a * 2 + .2, b + c, .12)), (ox, oy + (b + c) / 2, -hw + 1.1)), S('iron', base=.08, up=0, jit=0))
        P.add(T(box((.16, b + c * .8, .1)), (ox, oy + (b + c * .8) / 2, -hw + 1.0)), S('iron', base=.35, jit=0))
        for sg in (-1, 1):                                                      # shutters folded open on the wall
            sx = ox + sg * (a + .95 + a * .5)
            P.add(T(box((a * 1.0, b + .3, .16), .04), (sx, oy + (b + .3) / 2, -hw - .42)), S(team, base=.5, up=.1, jit=.02))
            for yy in (.5, b - .2):
                P.add(T(box((a * 1.1, .14, .12)), (sx, oy + yy, -hw - .55)), S('iron', base=.4, jit=0))
    if door:
        ox, oy, a, b, c = door
        voussoirs(P, ox, oy, -hw, a, b, c, depth=.5, band=.9, n=11)
        for i in range(5):
            P.add(T(box((a * 2 / 5 - .05, b + c * .8, .3), .03), (ox - a + (i + .5) * a * 2 / 5, oy + (b + c * .8) / 2, -hw + 1.0)), S('wood', base=.44 + (i % 2) * .05, up=.05, jit=.02))
        for yy in (.6, 1.7, 2.8):
            P.add(T(box((a * 1.9, .18, .1)), (ox, oy + yy, -hw + .8)), S('iron', base=.42, jit=0))
        P.add(T(torus(.3, .06, n=10, sides=4), (ox + a * .5, oy + 1.6, -hw + .7), 0, 90), S('iron', base=.5, jit=0))

def donjon(team='red', W=24.0, H=36.0):
    """the great keep tower (front = -Z faces the courtyard): battered plinth, ashlar, CUT arched windows with team
    shutters, cut door at the top of a forestair, corner pilasters, bartizans, hipped slate roof, chimney"""
    P = Prop('Donjon_%s' % team); hw = W / 2
    win = lambda yset: [(x, y, 1.2, 2.6, 1.2) for x in (-5.5, 5.5) for y in yset]
    faces = {0: [(5.5, 16.0, 1.2, 2.6, 1.2)] + win((26.0,)), 90: win((16.0, 26.0)), 180: win((16.0, 26.0)), -90: win((16.0, 26.0))}
    door = (-4.0, 6.0, 1.6, 2.6, 1.6)
    core = T(box((W - .4, H + 2, W - .4)), (0, H / 2 - 1, 0)); cut = bmesh.new()
    for yaw, opens in faces.items():
        for ox, oy, a, b, c in opens + ([door] if yaw == 0 else []):
            pr = outline_prism([(px + ox, py + oy) for px, py in ell_outline(a, b, c, 10)], -hw - 1.0, -hw + 1.3)
            add_into(cut, T(pr, (0, 0, 0), yaw))
    core = bool_diff(core, cut)
    P.add(core, S('stone', base=.5, jit=.02))
    pl = [Vector((sx * (hw + 1.6), -2.0, sz * (hw + 1.6))) for sx in (-1, 1) for sz in (-1, 1)]
    pl += [Vector((sx * (hw + .06), 2.4, sz * (hw + .06))) for sx in (-1, 1) for sz in (-1, 1)]
    P.add(hull(pl), S('stone', base=.5, up=.18, jit=.02))
    P.add(T(box((W + .7, .55, W + .7), .16), (0, 2.65, 0)), S('stone', base=.66, up=.15, jit=.02))
    for yaw, opens in faces.items():
        tmp = Prop('_f'); donjon_face(tmp, W, H, hw, opens, team, 50 + yaw, door if yaw == 0 else None); merge(P, tmp, yaw)
    for sx in (-1, 1):                                                          # corner pilasters with sloped caps
        for sz in (-1, 1):
            for ax in (0, 1):
                px = sx * (hw - .9) if ax else sx * (hw + .45); pz = sz * (hw + .45) if ax else sz * (hw - .9)
                wx, wz = (1.8, .9) if ax else (.9, 1.8)
                P.add(T(box((wx, H - 7.0, wz), .1), (px, 2.9 + (H - 7) / 2, pz)), S('stone', base=.6, up=.12, jit=.03))
                ox, oz = (0, sz) if ax else (sx, 0)
                pts = [Vector((px + dx * wx / 2, H - 4.1 + (1.0 if (dx * ox + dz * oz) <= 0 else 0), pz + dz * wz / 2)) for dx in (-1, 1) for dz in (-1, 1)]
                pts += [Vector((px + dx * wx / 2, H - 4.15, pz + dz * wz / 2)) for dx in (-1, 1) for dz in (-1, 1)]
                P.add(hull(pts), S('stone', base=.66, up=.2, jit=.02))
    for i in range(12):                                                         # forestair out toward the courtyard
        y = 6.0 - i * .5; z = -hw - 3.4 - i * 1.0 - .5
        P.add(T(box((3.4, y, 1.05), .05), (-4.0, y / 2, z)), S('stone', base=.58 + (i % 2) * .05, up=.15, jit=.02))
    P.add(T(box((5.0, 6.0, 3.4), .08), (-4.0, 3.0, -hw - 1.7)), S('stone', base=.6, up=.15, jit=.02))
    for sx in (-1, 1):
        course_wall(P, (-4.0 + sx * 2.15, -hw - 15.4), (-4.0 + sx * 2.15, -hw - .1), 0.0,
                    lambda t: (6.0 - (12 - (t - 3.4)) * .5 if t > 3.4 else .5) + 1.0, .5, bl=1.6, bh=.8, col='stone', base=.62, seed=58 + sx)
    return P

def donjon_top(team='red', W=24.0, H=36.0):
    """the donjon's crown (separate kit piece, same origin): corbelled parapets with shields, bartizans, roof, chimney"""
    P = Prop('DonjonTop_%s' % team); hw = W / 2
    for yaw in (0, 90, 180, -90):
        tmp = Prop('_t'); donjon_face(tmp, W, H, hw, [], team, 50 + yaw, top=True); merge(P, tmp, yaw)
    P.add(T(box((W - .6, .3, W - .6)), (0, H - .15, 0)), S('stone', base=.55, jit=.02))
    for sx in (-1, 1):                                                          # bartizans
        for sz in (-1, 1):
            px, pz = sx * (hw + .4), sz * (hw + .4); r = 2.0
            P.add(T(lathe([(0, H - 4.0), (.6, H - 4.0), (1.3, H - 2.8), (r, H - 1.4), (r, H + 3.6), (0, H + 3.6)], n=12), (px, 0, pz)), S('stone', base=.6, up=.15, jit=.03))
            P.add(T(ashlar_ring(r + .01, H - 1.2, H + 3.4, bw=1.6, bh=1.1, seed=70 + sx + 3 * sz), (px, 0, pz)), ash_sh(base=.62))
            P.add(T(lathe([(0, H + 3.5), (r + .35, H + 3.5), (r * .7, H + 5.6), (r * .35, H + 7.2), (.1, H + 8.4), (0, H + 8.6)], n=12), (px, 0, pz)), S('slate', base=.5, up=.25, jit=.05))
            P.add(T(lathe([(0, 0), (.12, 0), (.12, 1.2), (0, 1.8)], n=6), (px, H + 8.5, pz)), S('iron', base=.45, jit=0))
    Rr = hw - 1.0; yb = H + .9; N = 8; hr = 11.0                                # hipped slate roof
    prof = [(0, yb - .2), ((Rr + .5) * 1.414, yb - .2)]
    for k in range(N):
        t0, t1 = k / N, (k + 1) / N
        prof += [(Rr * 1.414 * (1 - t0) + .3, yb + t0 * hr), (Rr * 1.414 * (1 - t1) + .05, yb + t1 * hr - .05)]
    prof += [(.2, yb + hr), (0, yb + hr + .1)]
    P.add(lathe(prof, n=4, a0=math.pi / 4), S('slate', base=.5, up=.25, jit=.06, seed=3))
    P.add(T(lathe([(0, 0), (.3, 0), (.3, 2.5), (0, 3.6)], n=6), (0, yb + hr - .2, 0)), S('iron', base=.45, jit=0))
    P.add(T(box((2.0, 7.0, 1.6), .1), (5.0, yb + 3.5, 3.0)), S('stone', base=.6, up=.12, jit=.03))
    P.add(T(box((2.4, .4, 2.0), .08), (5.0, yb + 7.2, 3.0)), S('stone', base=.7, up=.1, jit=0))
    return P

def wall_stair(H=WALL_H, w=5.0):
    """stone stair climbing along +X from the courtyard to the wall-walk (the wall is at +Z), block side wall"""
    P = Prop('WallStair%d' % int(H)); n = int(math.ceil(H / .7)); rise = H / n; run = 1.15
    for i in range(n):
        y = (i + 1) * rise; x = i * run + run / 2
        P.add(T(box((run + .05, .32, w + .2), .08), (x, y - .16, 0)), S('stone', base=.66 + (i % 3) * .03, up=.15, jit=.02))
        P.add(T(box((run, y + .2, w)), (x, (y - .8) / 2, 0)), S('stone', base=.5, jit=.02))
    L = n * run
    course_wall(P, (0, -w / 2 - .45), (L + 2.8, -w / 2 - .45), -.5, lambda t: min(H + .9, (t / run) * rise + .9), .9, bl=2.2, bh=1.1, col='stone', base=.6, seed=91)
    P.add(T(box((3.0, H + .5, w)), (L + 1.5, (H - .5) / 2, 0)), S('stone', base=.5, jit=.02))
    P.add(T(box((3.2, .32, w + .2), .08), (L + 1.5, H - .16, 0)), S('stone', base=.66, up=.15, jit=.02))
    return P

# ------------------------------------------------------------------ the Sundered Bridge (hero) + bridge tower
BR_DECK = 6.5

def sundered_bridge():
    """4-span stone bridge along X (abutments at +-40, ramps to +-54) over a river bed at y -6.5. The two inner
    spans are broken: arch stubs with curved undersides, jagged break, rubble in the river, a timber patch walkway
    to the central pier (the bridge tower stands there). Origin y = 0 = valley reference."""
    P = Prop('SunderedBridge'); D = BR_DECK; zb = 5.0; sp = -1.6; rs = 5.0
    def pier(cx, hwid, hz):
        P.add(T(box((hwid * 2, D + 9, hz * 2)), (cx, (D - 9) / 2, 0)), S('stone', base=.5, jit=.02))
        for sg in (-1, 1):
            pts = [Vector((cx + x, y, sg * zz)) for y in (-9.0, .8) for x, zz in ((-hwid, hz - .2), (hwid, hz - .2), (0, hz + 3.2))]
            pts += [Vector((cx + x, 2.6, sg * zz)) for x, zz in ((-hwid * .7, hz - .2), (hwid * .7, hz - .2), (0, hz + 1.0))]
            P.add(hull(pts), S('stone', base=.56, up=.2, jit=.04, seed=int(cx)))
        for zs in (-1, 1):
            pan = ashlar(hwid * 2, 9.8, seed=int(cx) + 7 * zs); T(pan, (cx, -9, zs * hz), 0 if zs > 0 else 180); P.add(pan, ash_sh(base=.58))
    for sg in (-1, 1):                                                          # outer spans (intact)
        a, b = sg * 40.0, sg * 22.5; cx = (a + b) / 2; hw = abs(a - b) / 2
        core = T(box((hw * 2, D + 9, zb * 2)), (cx, (D - 9) / 2, 0))
        cp = outline_prism(ell_outline(hw, sp + 9, rs), -zb - 1, zb + 1, y0=-1); bmesh.ops.translate(cp, vec=Vector((cx, -9, 0)), verts=cp.verts)
        P.add(bool_diff(core, cp), S('stone', base=.48, jit=.02))
        for zs in (-1, 1):
            pan = ashlar(hw * 2, D + 9 - .3, seed=100 + sg * 3 + zs, skip=lambda x, y, hw=hw: in_arch(x, y, hw, sp + 9, rs, 1.1))
            T(pan, (cx, -9, zs * zb), 0 if zs > 0 else 180); P.add(pan, ash_sh(base=.6))
            voussoirs(P, cx, -9, zs * (zb + .1), hw, sp + 9, rs, band=1.2, n=15, quoins=False)
        pier(sg * 20.0, 2.5, zb)
        for i in range(14):                                                     # approach ramp down to y 3
            x = sg * (40.5 + i); y = lerp(D, 3.0, (i + .5) / 14)
            P.add(T(box((1.02, y + 3, zb * 2)), (x, (y - 3) / 2, 0)), S('stone', base=.5, jit=.02))
            P.add(T(box((1.06, .16, zb * 2 - 1.9), .03), (x, y + .04, 0), 0, 0, -sg * math.degrees(math.atan((D - 3) / 14))), S('stoneg', base=.6 + (i % 2) * .05, jit=.02))
        for zs in (-1, 1):                                                      # flared wing walls
            course_wall(P, (sg * 40, zs * (zb + .1)), (sg * 55, zs * (zb + 3.6)), -3.0,
                        lambda t: lerp(D + 1.0, 3.2, clamp(t / 15.5)), 1.0, bl=2.6, bh=1.2, col='stone', base=.62, seed=110 + sg + zs)
    pier(0.0, 7.0, 8.0)
    for sg in (-1, 1):                                                          # broken inner spans: stubs with arch undersides
        icx = sg * 12.25; ihw = 5.25; irs = 4.0
        for xa, xb in ((sg * 14.0, sg * 17.5), (sg * 7.0, sg * 9.2)):
            lo, hi = min(xa, xb), max(xa, xb)
            stub = T(box((hi - lo, D + 9, zb * 2)), ((lo + hi) / 2, (D - 9) / 2, 0))
            cp = outline_prism(ell_outline(ihw, sp + 9, irs), -zb - 1, zb + 1, y0=-1); bmesh.ops.translate(cp, vec=Vector((icx, -9, 0)), verts=cp.verts)
            P.add(bool_diff(stub, cp), S('stone', base=.48, jit=.02))
            for zs in (-1, 1):
                pan = ashlar(hi - lo, D + 9 - .3, seed=140 + int(lo) + zs, skip=lambda x, y, c=(lo + hi) / 2, f=zs: in_arch(x * f + c - icx, y, ihw, sp + 9, irs, .9))
                T(pan, ((lo + hi) / 2, -9, zs * zb), 0 if zs > 0 else 180); P.add(pan, ash_sh(base=.6))
                voussoirs(P, icx, -9, zs * (zb + .1), ihw, sp + 9, irs, band=1.0, n=13, quoins=False, keep=lambda x, lo=lo, hi=hi: lo - .3 < x < hi + .3)
        rng = random.Random(9 + sg)
        for i in range(18):                                                     # jagged break edges
            x = sg * rng.uniform(13.4, 14.6) if i < 11 else sg * rng.uniform(9.0, 9.8)
            stone(P, (x, D - rng.uniform(.3, 3.6), rng.uniform(-4.3, 4.3)), (rng.uniform(1.0, 1.8), rng.uniform(.7, 1.1), rng.uniform(1.2, 2.2)),
                  rng.uniform(0, 90), col='stone', base=.62, seed=200 + i, roll=rng.uniform(-20, 20))
        for i in range(12):                                                     # rubble in the river
            x = sg * rng.uniform(9.6, 14.2)
            P.add(T(rock((rng.uniform(.9, 1.8), rng.uniform(.6, 1.2), rng.uniform(.9, 1.6)), seed=300 + i + sg * 50, n=12), (x, -6.4 + rng.uniform(0, 2.6), rng.uniform(-6, 6))), S('stone', base=.5, up=.25, jit=.06))
        for i in range(9):
            stone(P, (sg * rng.uniform(9.6, 14.2), -5.2 + rng.uniform(0, 3.2), rng.uniform(-5, 5)), (1.6, .9, 1.2), rng.uniform(0, 180), col='stone', base=.56, seed=400 + i, roll=rng.uniform(-35, 35), pitch=rng.uniform(-25, 25))
        xa, xb = sg * 15.4, sg * 7.6                                            # timber patch walkway
        for zz in (-2.2, 2.2):
            P.add(bar((xa, D - .55, zz), (xb, D - .55, zz), .7, .7, .06), S('wooddk', base=.45, up=.1, jit=.03))
            P.add(bar((sg * 12.0, D - .9, zz), (sg * 10.6, -1.9, zz * 1.25), .5, .5, .05), S('wooddk', base=.38, up=.1, jit=.03))
            P.add(T(box((.9, .7, .9), .05), (sg * 10.6, -2.0, zz * 1.25)), S('stone', base=.55, jit=.03))
        for i in range(11):
            x = lerp(xa, xb, (i + .5) / 11)
            P.add(T(box((.62, .22, 5.8), .04), (x, D - .09, 0), rng.uniform(-3, 3), 0, rng.uniform(-1, 1)), S('wood', base=.5 + rng.uniform(-.06, .06), up=.12, jit=.02))
        for zz in (-2.9, 2.9):
            for x in (xa, (xa + xb) / 2, xb):
                P.add(log((x, D - .3, zz), (x, D + 3.2, zz), .2), S('wooddk', base=.45, jit=.03))
            P.add(tube(sag((xa, D + 2.9, zz), ((xa + xb) / 2, D + 2.9, zz), .35) + sag(((xa + xb) / 2, D + 2.9, zz), (xb, D + 2.9, zz), .35)[1:], .08, sides=5), S('straw', base=.45, jit=0))
        pv = ashlar(25.0, zb * 2 - 1.9, bw=2.2, bh=1.6, seed=120 + sg, depth=.05)  # deck paving 15 .. 40
        T(pv, (sg * 27.5, D + .01, zb - .95), 0, -90); P.add(pv, ash_sh(col='stoneg', base=.62, up=0, grime=0))
        for zs in (-1, 1):                                                      # parapets (broken near the gap)
            z = zs * (zb - .5)
            def top(t):
                if t < 2.5: return D + .3 + t * .5
                if t < 25: return D + 1.7
                return lerp(D + 1.7, 3.0 + 1.7, clamp((t - 25) / 14))
            course_wall(P, (sg * 14.6, z), (sg * 54.0, z), 2.0, top, 1.0, bl=2.6, bh=1.0, col='stone', base=.64, seed=130 + sg * 2 + zs,
                        bottom=lambda t: (D if t < 25.4 else lerp(D, 3.0, clamp((t - 25.4) / 14))) - .9)
    return P

def tower_face(P, w, d, kind, y1, seed, sp, rs, phw, slits=((-3.0, 12.0), (3.0, 12.0), (-3.0, 20.0), (3.0, 20.0))):
    """one face of the bridge tower in canonical orientation (face plane z = -d)"""
    Hb = 30.0
    if kind == 'slit': sk = lambda x, y: any(abs(x - sx) < 1.0 and sy - 1.6 < y < sy + 1.8 for sx, sy in slits)
    else: sk = lambda x, y: in_arch(x, y, phw, sp, rs, 1.2)
    P.add(T(ashlar(w - .3, Hb - .8, seed=seed, skip=sk), (0, 0, -d), 180), ash_sh(base=.62))
    if kind == 'slit':
        for sx, sy in slits: slit_frame(P, (sx, sy - 1.4, -d - .02), 0, h=2.8)
    else: voussoirs(P, 0, 0, -d, phw, sp, rs, band=1.1, n=11)
    y0 = Hb + .7                                                                 # belfry face
    P.add(T(ashlar(w - .3, y1 - y0, bw=2.4, bh=1.3, seed=seed + 5, skip=lambda x, y: in_arch(x, y - .3, 3.0, 4.8, 2.6, .9)), (0, y0, -d), 180), ash_sh(base=.64))
    voussoirs(P, 0, y0 + .3, -d, 3.0, 4.8, 2.6, band=.9, n=11, quoins=False)
    P.add(T(box((7.4, .4, 1.2), .08), (0, y0 + .2, -d - .2)), S('stone', base=.68, up=.12, jit=.02))
    corbels(P, w + 1.0, y1 + .2, -d, -.5)
    P.add(T(box((w + 1.0, 2.4, 1.2)), (0, y1 + 1.4, -d + .1)), S('stone', base=.5, jit=0))
    P.add(T(ashlar(w + 1.0, 2.4, bw=2.4, bh=1.2, seed=seed + 9), (0, y1 + .2, -d - .52), 180), ash_sh(base=.64))
    P.add(T(box((w + 1.2, .24, 1.5), .08), (0, y1 + 2.72, -d + .1)), S('stone', base=.72, up=.1, jit=.02))
    merlon_row(P, w - 2, y1 + 2.84, -d + .1, 1.2, mw=1.8, gap=1.2, mh=1.8, seed=seed)

def bridge_tower():
    """square gate tower on the central pier (14 x 16, origin = deck level): CUT arched passage along X, quoins,
    CUT slits, string course, open belfry with a bronze bell on an oak headstock, corbelled parapet, broken spire"""
    P = Prop('BridgeTower'); W, D, Hb = 14.0, 16.0, 30.0; hx, hz = W / 2, D / 2
    sp, rs, phw = 5.4, 3.4, 3.4
    core = T(box((W - .4, Hb + 1, D - .4)), (0, Hb / 2 - .5, 0))
    core = bool_diff(core, T(outline_prism(ell_outline(phw, sp, rs), -hx - 1, hx + 1, y0=-2), (0, 0, 0), 90))
    cut = bmesh.new()
    for yaw in (0, 180):
        for sx, sy in ((-3.0, 12.0), (3.0, 12.0), (-3.0, 20.0), (3.0, 20.0)):
            tmpc = bmesh.new(); slit_cutter(tmpc, (sx, sy - 1.4, -hz), 0, h=2.8); add_into(cut, T(tmpc, (0, 0, 0), yaw))
    core = bool_diff(core, cut)
    P.add(core, S('stone', base=.5, jit=.02))
    y0, y1 = Hb + .7, Hb + 11.0
    for yaw, w, d, kind in ((0, W, hz, 'slit'), (180, W, hz, 'slit'), (90, D, hx, 'pass'), (-90, D, hx, 'pass')):
        tmp = Prop('_f'); tower_face(tmp, w, d, kind, y1, 150 + yaw, sp, rs, phw); merge(P, tmp, yaw)
    for sx in (-1, 1):                                                          # corner quoins
        for sz in (-1, 1):
            for i in range(int(Hb / 1.5)):
                lg = i % 2 == 0; y = i * 1.5 + .75
                P.add(T(box((1.8 if lg else 1.0, 1.42, 1.0 if lg else 1.8), .06), (sx * (hx - (.9 if lg else .5) + .3), y, sz * (hz - (.5 if lg else .9) + .3))),
                      S('stone', base=.7 + (h01(i, sx, sz) - .5) * .08, up=.12, jit=.02))
    P.add(T(box((W + 1.0, .7, D + 1.0), .2), (0, Hb + .35, 0)), S('stone', base=.68, up=.15, jit=.02))
    bel = T(box((W, y1 - y0, D)), (0, (y0 + y1) / 2, 0))
    bel = bool_diff(bel, T(box((W - 3.0, y1 - y0, D - 3.0)), (0, (y0 + y1) / 2 + 1.2, 0)))
    bel = bool_diff(bel, outline_prism([(x, y + y0 + .3) for x, y in ell_outline(3.0, 4.8, 2.6, 12)], -hz - 1, hz + 1))
    bel = bool_diff(bel, T(outline_prism([(x, y + y0 + .3) for x, y in ell_outline(3.0, 4.8, 2.6, 12)], -hx - 1, hx + 1), (0, 0, 0), 90))
    P.add(bel, S('stone', base=.56, jit=.02))
    P.add(bar((-5.6, y1 - 2.4, 0), (5.6, y1 - 2.4, 0), 1.0, 1.0, .08), S('wood', base=.42, up=.1, jit=.03))
    for sx in (-1, 1): P.add(T(box((.6, 1.3, 1.4), .06), (sx * 1.6, y1 - 2.4, 0)), S('iron', base=.4, jit=0))
    bell = lathe([(0, 0), (2.4, 0), (2.5, .25), (2.15, .7), (1.75, 1.4), (1.55, 2.4), (1.5, 3.2), (1.25, 3.7), (.7, 3.95), (0, 4.0)], n=20)
    P.add(T(bell, (0, y1 - 6.9, 0)), S('brass', grad=(y1 - 6.9, y1 - 2.9, .38, .74), up=.15), smooth=True)
    P.add(T(torus(2.35, .14, n=20, sides=5), (0, y1 - 6.65, 0)), S('brass', base=.7, jit=0), smooth=True)
    P.add(log((0, y1 - 3.0, 0), (.3, y1 - 6.2, 0), .16), S('iron', base=.4, jit=0))
    P.add(T(lathe([(0, 0), (.45, .1), (.5, .5), (0, .8)], n=8), (.3, y1 - 6.9, 0)), S('iron', base=.45, jit=0), smooth=True)
    P.add(T(box((W - 3.0, .4, D - 3.0)), (0, y0 + 1.0, 0)), S('wooddk', base=.4, jit=.04))
    P.add(T(box((W + .4, .4, D + .4)), (0, y1 + .2, 0)), S('stone', base=.55, jit=.02))
    yb, hr, Rr = y1 + .6, 22.0, 6.2                                             # broken spire
    prof = [(0, yb - .2), (Rr * 1.414 + .4, yb - .2)]
    N = 12
    for k in range(N):
        t0, t1 = k / N, (k + 1) / N
        prof += [(Rr * 1.414 * (1 - t0) ** 1.15 + .35, yb + t0 * hr), (Rr * 1.414 * (1 - t1) ** 1.15 + .08, yb + t1 * hr - .06)]
    prof += [(.15, yb + hr), (0, yb + hr + .1)]
    spire = lathe(prof, n=4, a0=math.pi / 4)
    nc = Vector((.42, 1.0, -.3)).normalized(); p0 = Vector((0, yb + 8.5, 0))
    yp = lambda x, z: p0.y - (nc.x * x + nc.z * z) / nc.y
    spire = bool_diff(spire, hull([Vector((x, yp(x, z) + o, z)) for x in (-14, 14) for z in (-14, 14) for o in (0, 40)]))
    us, ud = PAL.u('slate'), PAL.u('wooddk')
    def sh_sp(f):
        if f.normal.dot(nc) > .97: return [(ud, .16 + (h01(*f.calc_center_median()) - .5) * .08)] * len(f.loops)
        return S('slate', base=.5, up=.25, jit=.06, seed=4)(f)
    P.add(spire, sh_sp)
    rng = random.Random(4); apex = Vector((0, yb + hr, 0))
    ch = lambda: S('wooddk', base=.22 + rng.uniform(0, .08), up=.1, jit=.02)
    P.add(bar((0, yb + 2, 0), (0, yb + hr - .6, 0), .5, .5, .05), ch())        # king post up to the old apex
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, -1), (-1, 1))):       # hip rafters (two snapped short)
        foot = Vector((sx * Rr * .98, yb + .2, sz * Rr * .98)); end = foot.lerp(apex, .74 if k in (1, 2) else 1.0)
        P.add(bar(foot, end, .42, .42, .04), ch())
    for t, gone in ((.5, (1,)), (.72, (0, 1))):                                # purlin rings with missing members
        c = [Vector((sx * Rr * .98, yb + .2, sz * Rr * .98)).lerp(apex, t) for sx, sz in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        for k in range(4):
            if k in gone: continue
            P.add(bar(c[k], c[(k + 1) % 4], .3, .3, .03), ch())
    for k in range(8):                                                          # common rafters poking past the break
        t = (k + .5) / 8; side = k % 4; sx, sz = ((1, 0), (0, -1), (-1, 0), (0, 1))[side]
        f0 = Vector((sx * Rr * .98 + (t - .5) * 6 * abs(sz), yb + .2, sz * Rr * .98 + (t - .5) * 6 * abs(sx)))
        P.add(bar(f0, f0.lerp(apex, rng.uniform(.5, .66)), .26, .26, .03), ch())
    for k in range(7):
        P.add(T(box((1.3, .14, .9), .03), (rng.uniform(-5, 5), y1 + 2.95, rng.uniform(-6.5, 6.5)), rng.uniform(0, 90), rng.uniform(-8, 8)), S('slate', base=.5, jit=.05))
    return P

# ------------------------------------------------------------------ Chapel Isle
def buttress(P, pos, yaw, h=7.5, seed=0, col='stoneg'):
    """stepped buttress in canonical orientation (wall face at z = 0, buttress out to -Z), merged with yaw"""
    tmp = Prop('_b'); rng = random.Random(seed); y = -.6
    for i, (w, d, hh) in enumerate(((1.9, 1.9, h * .55), (1.5, 1.1, h * .45))):
        nb = max(1, int(hh / 1.25))
        for k in range(nb):
            stone(tmp, (0, y + (k + .5) * hh / nb, -d / 2), (w - .06 * (k % 2), hh / nb - .07, d), col=col, base=.56 + rng.uniform(-.05, .05), seed=seed + i * 9 + k)
        y += hh
        tmp.add(hull([Vector((sx * w / 2, y + (0 if zz < -d + .01 else .9), zz)) for sx in (-1, 1) for zz in (-d - .15, 0.0)] +
                     [Vector((sx * w / 2, y - .05, zz)) for sx in (-1, 1) for zz in (-d - .15, 0.0)]), S(col, base=.66, up=.2, jit=.02))
    merge(P, tmp, yaw, pos)

def pew(P, pos, yaw, tipped=False, seed=0):
    tmp = Prop('_p'); rng = random.Random(seed)
    tmp.add(T(box((4.6, .22, 1.1), .04), (0, 1.5, 0)), S('wood', base=.42 + rng.uniform(-.04, .04), up=.12, jit=.02))
    tmp.add(T(box((4.6, 1.2, .18), .04), (0, 2.5, .62), 8), S('wood', base=.4, up=.1, jit=.02))
    for x in (-2.2, 0.0, 2.2):
        tmp.add(hull([Vector((x + dx, y, z)) for dx in (-.1, .1) for y, z in ((0, -.5), (0, .55), (1.45, -.5), (3.1, .7), (3.2, .5), (1.6, .55))]), S('wooddk', base=.5, up=.1, jit=.02))
    if tipped: rot_mb(tmp.solid, 0, 80, .25)
    merge(P, tmp, yaw, pos)

def truss(P, z, x0, x1, y, apex, broken=False, seed=0):
    """charred roof truss across the nave: tie beam, principal rafters, king post, struts (or a snapped one)"""
    ch = lambda: S('wooddk', base=.24 + random.Random(seed).uniform(0, .08), up=.1, jit=.03)
    if not broken:
        P.add(bar((x0, y, z), (x1, y, z), .6, .6, .05), ch())
        for xa in (x0, x1): P.add(bar((xa, y + .2, z), (0, apex, z), .5, .5, .05), ch())
        P.add(bar((0, y, z), (0, apex, z), .45, .45, .04), ch())
        for sg in (-1, 1): P.add(bar((0, y + .8, z), (sg * 3.2, y + (apex - y) * .58, z), .3, .3, .03), ch())
    else:
        P.add(bar((x0, y, z), (x0 * .1, y - .4, z), .6, .6, .05), ch())
        P.add(bar((x0 * .1, y - .4, z), (x1 * .7, .4, z + 1.5), .6, .6, .05), ch())
        P.add(bar((x0, y + .2, z), (x0 * .45, y + (apex - y) * .6, z), .5, .5, .05), ch())

def ruined_chapel():
    """roofless gothic chapel (door at -Z): real block walls with cut lancets, a gable with a pointed door and an
    oculus, a broken apse, stepped buttresses, flagstones with gaps, altar with candles, pews, charred trusses, ivy"""
    P = Prop('RuinedChapel'); rng = random.Random(21)
    X, Z0, Z1, th = 8.2, -15.2, 12.0, 1.6
    def lancet(tc, hw=1.2, sill=3.6, spring=7.0, apex=8.8):
        return (tc - hw, tc + hw, sill, lambda t, tc=tc: spring + (apex - spring) * max(0, 1 - abs(t - tc) / hw) ** .55)
    wins = [5.0, 13.6, 22.2]
    topE = lambda t: 11.0 - 6.8 * math.exp(-((t - 15) / 5.0) ** 2) + (nz(t, 0, 1, 2.2, 3) - .5) * 2.6
    topW = lambda t: 10.6 - 3.0 * smooth((t - 20) / 6) + (nz(t, 0, 2, 2.0, 5) - .5) * 1.8
    course_wall(P, (X, Z0), (X, Z1), -.6, topE, th, holes=[lancet(t) for t in wins], seed=21)
    course_wall(P, (-X, Z0), (-X, Z1), -.6, topW, th, holes=[lancet(t) for t in wins], seed=22)
    gx = X + .8; L = 2 * gx
    gable = lambda t: min(11 + 6.5 * (1 - abs(t - gx) / gx), 99 if t < gx + 1 else 15.2 - (t - gx) * .9) + (nz(t, 0, 3, 1.6, 7) - .5) * 1.2
    door = (gx - 2.2, gx + 2.2, -1, lambda t: 5.6 + 2.8 * max(0, 1 - abs(t - gx) / 2.2) ** .55)
    ocul = (gx - 1.5, gx + 1.5, lambda t: 12.4 - math.sqrt(max(0, 2.25 - (t - gx) ** 2)), lambda t: 12.4 + math.sqrt(max(0, 2.25 - (t - gx) ** 2)))
    course_wall(P, (-gx, Z0), (gx, Z0), -.6, gable, th + .2, holes=[door, ocul], seed=23)
    n = 6                                                                       # apse
    for k in range(n):
        a0, a1 = k * math.pi / n, (k + 1) * math.pi / n
        p0 = (X * math.cos(a0), Z1 + X * math.sin(a0)); p1 = (X * math.cos(a1), Z1 + X * math.sin(a1))
        tp = lambda t, k=k: 9.0 - 3.5 * math.sin(k / (n - 1) * math.pi) ** 2 + (nz(t, k, 4, 1.8, 9) - .5) * 1.6
        holes = [lancet(2.15, hw=.9, sill=3.4, spring=5.8, apex=7.0)] if k in (2, 3) else []
        course_wall(P, p0, p1, -.6, tp, th, holes=holes, seed=30 + k)
    for sg in (-1, 1):                                                          # window frames: jambs, pointed voussoirs, mullion
        for tc in wins:
            tmp = Prop('_w')
            voussoirs(tmp, 0, 3.6, -.85, 1.2, 3.4, 1.8, depth=.4, band=.55, n=7, col='stoneg', base=.66)
            tmp.add(T(box((.3, 4.6, .5)), (0, 5.9, -.6)), S('stoneg', base=.66, up=.1, jit=0))
            tmp.add(T(box((3.2, .3, 1.0), .06), (0, 3.45, -.6)), S('stoneg', base=.7, up=.1, jit=0))
            if not (sg > 0 and abs(tc - 15) < 3): merge(P, tmp, -90 * sg, (sg * X, 0, Z0 + tc))
        for t in (.4, 9.3, 17.9, 26.8):
            hh = topE(t) if sg > 0 else topW(t)
            buttress(P, (sg * (X + .8), 0, Z0 + t), -90 * sg, h=max(4.0, min(8.5, hh - 1.0)), seed=40 + int(t) + sg)
    tmp = Prop('_d')                                                             # door + oculus frames on the gable
    voussoirs(tmp, 0, 0, -.85, 2.2, 5.6, 2.8, depth=.5, band=.8, n=11, col='stoneg', base=.68)
    tmp.add(T(torus(1.75, .32, n=16, sides=5), (0, 12.4, -.9), 0, 90), S('stoneg', base=.7, up=.1, jit=0), smooth=True)
    for k in range(4):
        a = k * math.pi / 4
        tmp.add(T(box((3.1, .2, .25)), (0, 12.4, -.8), 0, 0, math.degrees(a)), S('stoneg', base=.66, jit=0))
    tmp.add(T(cyl(.45, .3, sides=8), (0, 12.4, -.95), 0, 90), S('stoneg', base=.7, jit=0))
    merge(P, tmp, 0, (0, 0, Z0))
    for sx in (-1, 1): buttress(P, (sx * (gx - .9), 0, Z0 - .9), 0, h=9.0, seed=50 + sx)
    for i in range(-3, 3):                                                      # flagstone floor with gaps
        for j in range(11):
            x = (i + .5) * 2.4; z = Z0 + 1.6 + j * 2.4 + (1.2 if i % 2 else 0)
            if z > Z1 + 2 or rng.random() < .22: continue
            P.add(T(box((2.3, .25, 2.3)), (x, .05, z), rng.uniform(-3, 3), rng.uniform(-2, 2), rng.uniform(-2, 2)), S('stoneg', base=.5 + rng.uniform(-.06, .06), up=.1, jit=.02))
    az = Z1 + 3.0                                                               # altar
    P.add(T(box((4.4, 2.4, 2.0), .08), (0, 1.2, az)), S('stone', base=.6, up=.12, jit=.02))
    for x in (-1.4, 0, 1.4): P.add(T(box((.9, 1.6, .2), .04), (x, 1.3, az - 1.05)), S('stone', base=.52, jit=0))
    P.add(T(box((5.0, .35, 2.6), .1), (0, 2.58, az)), S('stone', base=.72, up=.12, jit=.02))
    for k, x in enumerate((-1.8, -.9, .8, 1.7)):
        hh = (.9, .6, 1.1, .7)[k]
        P.add(T(cyl(.16, hh, sides=6), (x, 2.75, az - .4 + (k % 2) * .5)), S('canvas', base=.75, up=.1, jit=0))
        P.gadd(T(spike(.1, .35, sides=4), (x, 2.75 + hh, az - .4 + (k % 2) * .5)), 'candle')
    for sx in (-1, 1):                                                          # iron candle stands
        P.add(T(lathe([(.6, 0), (.5, .15), (.12, .4), (.1, 3.2), (.5, 3.3), (.5, 3.45), (0, 3.45)], n=8), (sx * 3.4, 0, az - .6)), S('iron', base=.4, jit=0))
        for dx in (-.3, 0, .3):
            P.add(T(cyl(.12, .5, sides=6), (sx * 3.4 + dx, 3.45, az - .6)), S('canvas', base=.75, jit=0))
            P.gadd(T(spike(.08, .28, sides=4), (sx * 3.4 + dx, 3.95, az - .6)), 'candle')
    pew(P, (-3.0, 0, -6.0), 0, seed=1); pew(P, (3.2, 0, -2.0), 6, seed=2); pew(P, (-2.8, 0, 2.5), -8, tipped=True, seed=3); pew(P, (3.4, 0, 5.8), 0, seed=4)
    truss(P, -8.0, -X, X, 10.0, 15.6, seed=5)
    truss(P, -1.0, -X, X, 9.8, 15.4, broken=True, seed=6)
    P.add(bar((-6.0, .4, 7.0), (2.0, 2.6, 9.4), .6, .6, .05), S('wooddk', base=.25, up=.1, jit=.03))
    P.add(bar((4.5, .3, -10.0), (6.6, 3.4, -4.0), .55, .55, .05), S('wooddk', base=.22, up=.1, jit=.03))
    for i in range(26):                                                         # rubble along the broken east wall + inside
        x = X + rng.uniform(-2.8, 2.6); z = Z0 + rng.uniform(9, 21)
        stone(P, (x, rng.uniform(.2, .9), z), (rng.uniform(1.4, 2.4), rng.uniform(.8, 1.2), rng.uniform(1.2, 1.7)), rng.uniform(0, 180), col='stoneg', base=.55, seed=60 + i, roll=rng.uniform(-30, 30), pitch=rng.uniform(-20, 20))
    for i in range(10):
        P.add(T(rock((rng.uniform(.5, 1.0), rng.uniform(.3, .6), rng.uniform(.5, .9)), seed=80 + i, n=10), (X + rng.uniform(-3, 3), .1, Z0 + rng.uniform(8, 22))), S('stoneg', base=.5, up=.25, jit=.06))
    for k in range(9):                                                          # ivy on the west wall
        z = Z0 + 3 + k * 2.6; y = rng.uniform(4.5, 9.0)
        P.add(T(blob(rng.uniform(.9, 1.5), 90 + k, n=16, sq=.7), (-X - 1.0, y, z), 0, 0, 0, (.55, 1.2, 1.0)), S('pine', base=.45, up=.3, jit=.1, seed=k))
        P.add(T(blob(.8, 120 + k, n=12, sq=.7), (-X - .95, y - 2.0, z + .6), 0, 0, 0, (.5, 1.3, .8)), S('grass', base=.42, up=.3, jit=.1, seed=k))
    return P

def footbridge(L=40.0):
    """timber trestle footbridge along X, deck 1.2 above its ends' ground, bents into the river bed, rope rails"""
    P = Prop('FootBridge%d' % int(L)); rng = random.Random(int(L)); D = 1.2; hw = L / 2
    nb = max(2, int(L / 8)); xs = [-hw + 3 + i * (L - 6) / (nb - 1) for i in range(nb)]
    for x in xs:                                                                # trestle bents
        for zz in (-2.4, 2.4): P.add(log((x, -9.0, zz), (x, D - .3, zz), .34, sides=7), S('wooddk', base=.45, up=.1, jit=.04))
        P.add(bar((x, D - .55, -2.9), (x, D - .55, 2.9), .55, .55, .05), S('wood', base=.38, up=.1, jit=.03))
        P.add(bar((x, -5.0, -2.4), (x, D - .9, 2.4), .3, .26, .03), S('wood', base=.36, jit=.03))
        P.add(bar((x, -5.0, 2.4), (x, D - .9, -2.4), .3, .26, .03), S('wood', base=.36, jit=.03))
        for zz in (-2.4, 2.4): P.add(T(torus(.4, .07, n=8, sides=4), (x, D - 1.4, zz)), S('straw', base=.45, jit=0))
    for zz in (-1.8, 0.0, 1.8): P.add(bar((-hw, D - .2, zz), (hw, D - .2, zz), .45, .4, .04), S('wooddk', base=.4, up=.1, jit=.03))
    n = int(L / .78)
    for i in range(n):
        x = -hw + (i + .5) * L / n
        if i in (int(n * .62),): continue                                      # one missing plank
        P.add(T(box((.66, .2, 5.4 + rng.uniform(-.3, .3)), .04), (x, D + .1, rng.uniform(-.1, .1)), rng.uniform(-2.5, 2.5), 0, rng.uniform(-1, 1)), S('wood', base=.5 + rng.uniform(-.07, .07), up=.12, jit=.02))
    for zz in (-2.6, 2.6):                                                      # posts + top rail + rope
        for x in xs + [-hw + .4, hw - .4]:
            P.add(log((x, D, zz), (x, D + 3.4, zz), .17, sides=6), S('wooddk', base=.45, jit=.03))
        P.add(bar((-hw + .4, D + 3.3, zz), (hw - .4, D + 3.3, zz), .22, .22, .03), S('wood', base=.42, up=.1, jit=.02))
        pts = []
        for a, b in zip(sorted(xs + [-hw + .4, hw - .4]), sorted(xs + [-hw + .4, hw - .4])[1:]):
            pts += sag((a, D + 2.0, zz), (b, D + 2.0, zz), .35, 4)[:-1]
        pts.append(Vector((hw - .4, D + 2.0, zz)))
        P.add(tube(pts, .07, sides=4), S('straw', base=.45, jit=0))
    for sg in (-1, 1):                                                          # end steps
        for k, y in enumerate((D - .5, D - 1.1)):
            P.add(T(box((.9, .22, 5.0), .04), (sg * (hw + .5 + k * .9), y, 0)), S('wood', base=.45, up=.1, jit=.02))
            P.add(T(box((.3, .7, 4.6)), (sg * (hw + .5 + k * .9), y - .45, 0)), S('wooddk', base=.4, jit=.02))
    return P

def gravestones(seed=1):
    """3 tilted headstones on mounds, a makeshift oak cross with a dented helm, a sword driven into the turf"""
    P = Prop('Graves%d' % seed); rng = random.Random(seed)
    for k in range(3):
        x = (k - 1) * 3.2 + rng.uniform(-.4, .4); z = rng.uniform(-.6, .6)
        pts = [Vector((sx * .9, y, sz * .22)) for sx in (-1, 1) for sz in (-1, 1) for y in (-.6, 1.9)]
        pts += [Vector((math.cos(a) * .9, 1.9 + math.sin(a) * .7, sz * .22)) for a in [i * math.pi / 8 for i in range(9)] for sz in (-1, 1)]
        P.add(T(hull(pts), (x, 0, z - 1.0), rng.uniform(-8, 8), rng.uniform(-10, 6), rng.uniform(-8, 8)), S('stoneg', base=.56, up=.15, jit=.04, seed=k))
        P.add(T(hull(rock_pts((1.1, .45, 1.9), n=16, seed=seed + k, flat=.0)), (x, -.15, z + 1.2)), S('dirt', base=.42, up=.3, jit=.06, seed=k))
        P.add(T(blob(.4, seed * 3 + k, n=10, sq=.6), (x + .6, .1, z - 1.3)), S('grass', base=.45, up=.3, jit=.1))
    x = 5.6
    P.add(bar((x, -.6, 0), (x, 3.2, 0), .32, .26, .03), S('wood', base=.42, jit=.03))
    P.add(bar((x - 1.0, 2.2, 0), (x + 1.0, 2.25, 0), .28, .24, .03), S('wood', base=.42, jit=.03))
    P.add(T(torus(.3, .07, n=8, sides=4), (x, 2.22, 0), 0, 0, 90), S('straw', base=.45, jit=0))
    helm = lathe([(.62, 0), (.64, .3), (.6, .7), (.45, 1.05), (.2, 1.22), (0, 1.25)], n=12)
    P.add(T(helm, (x, 3.05, 0), 0, 12, 0), S('iron', base=.45, up=.2, jit=0), smooth=True)
    P.add(T(box((1.0, .14, .1)), (x, 3.45, -.55), 0, 12), S('iron', base=.2, jit=0))
    P.add(T(box((.3, 3.4, .1)), (-5.4, 1.1, .4), 0, 0, 6), S('iron', base=.6, up=.1, jit=0))
    P.add(T(box((1.4, .22, .25), .04), (-5.2, 2.9, .4), 0, 0, 6), S('iron', base=.42, jit=0))
    P.add(T(cyl(.12, .9, sides=6), (-5.13, 3.0, .4), 0, 0, 6), S('wooddk', base=.4, jit=0))
    P.add(T(lathe([(0, 0), (.22, .05), (.22, .25), (0, .3)], n=8), (-5.06, 3.9, .4), 0, 0, 6), S('brass', base=.6, jit=0))
    return P

# ------------------------------------------------------------------ signature edge + field fortifications
def palisade(L=12.0, seed=1):
    """SIGNATURE: sharpened log stakes (bark body, fresh-cut tips), leaning out to -Z, two rope lashing bands, a
    back rail with iron cramps and raking braces behind"""
    P = Prop('Palisade%d_%d' % (int(L), seed)); rng = random.Random(seed)
    n = max(3, int(L / 1.02)); xs = [-L / 2 + (i + .5) * L / n for i in range(n)]
    for i, x in enumerate(xs):
        h = rng.uniform(6.0, 7.2) - (.5 if i % 3 == 1 else 0); r = rng.uniform(.42, .52)
        st = cyl(r, h + .9, sides=6, y0=-.9, rot0=rng.uniform(0, 1))
        P.add(T(st, (x, 0, 0), rng.uniform(-6, 6), -6, rng.uniform(-2, 2)), S('wooddk', base=.5, up=.1, jit=.05, seed=i))
        tip = spike(r, 1.5, sides=6, rot0=rng.uniform(0, 1), shoulder=.02)
        P.add(T(T(tip, (0, h, 0)), (x, 0, 0), 0, -6, 0), S('wood', base=.72, up=.15, jit=.05, seed=i))
    for y, d in ((4.6, .12), (1.9, .1)):                                       # rope lashing bands
        z = -math.tan(math.radians(6)) * y - .52
        pts = []
        for a, b in zip(xs, xs[1:]): pts += sag((a, y, z), (b, y, z), d, 3)[:-1]
        pts.append(Vector((xs[-1], y, z)))
        P.add(tube(pts, .09, sides=4), S('straw', base=.5, jit=0))
    zr = .9
    P.add(log((-L / 2, 3.3, zr), (L / 2, 3.3, zr), .3, sides=6), S('wood', base=.42, up=.1, jit=.03))
    for k in range(0, n, 4):                                                    # braces + cramps
        x = xs[k]
        P.add(log((x, 3.3, zr), (x, -.3, 3.4), .26, sides=6), S('wood', base=.4, up=.1, jit=.03))
        P.add(T(box((.5, .7, .3)), (x, 3.3, zr - .25)), S('iron', base=.38, jit=0))
        for dx in (-.15, .15): P.add(T(cyl(.07, .1, sides=4), (x + dx, 3.3, zr - .42), 0, 90), S('iron', base=.6, jit=0))
    return P

def cheval(L=10.0, seed=1):
    """cheval de frise: a squared log run through with crossed stakes sharpened both ends, rope at each cross"""
    P = Prop('Cheval%d' % int(L)); rng = random.Random(seed); y = 1.7
    P.add(T(box((L, .8, .8), .1), (0, y, 0)), S('wood', base=.42, up=.1, jit=.03))
    for sg in (-1, 1): P.add(T(box((.25, 1.0, 1.0), .05), (sg * L / 2, y, 0)), S('iron', base=.4, jit=0))
    n = int(L / 1.6)
    for i in range(n):
        x = -L / 2 + (i + .5) * L / n
        for k, a in enumerate((45, -45)):
            a2 = math.radians(a + rng.uniform(-6, 6)); d = Vector((0, math.cos(a2), math.sin(a2)))
            c = Vector((x + (k - .5) * .3, y, 0)); a_ = c - d * 2.4; b_ = c + d * 2.4
            P.add(log(a_, b_, .17, sides=5), S('wooddk', base=.5, up=.1, jit=.04))
            for e, dd in ((a_, -d), (b_, d)):
                sp_ = spike(.17, .7, sides=6, shoulder=.02); frame_to(T(sp_, (0, 0, 0), 0, 0, -90), e, e + dd)
                P.add(sp_, S('wood', base=.72, up=.1, jit=.03))
        P.add(T(torus(.55, .08, n=8, sides=4), (x, y, 0), 0, 0, 90), S('straw', base=.45, jit=0))
    return P

def wattle(L=12.0, H=5.0, seed=1):
    """trench revetment: stakes with woven withies (in-and-out wicker), a capping log; faces -Z"""
    P = Prop('Wattle%d' % int(L)); rng = random.Random(seed)
    ns = max(2, int(L / 1.5)) + 1; xs = [-L / 2 + i * L / (ns - 1) for i in range(ns)]
    for x in xs: P.add(log((x, -.8, 0), (x, H + .4, 0), .17, sides=6), S('wooddk', base=.45, jit=.04))
    rows = int(H / .46)
    for r in range(rows):
        y = .1 + r * H / rows; pts = []
        for i, x in enumerate(xs):
            for t in (0.0,):
                xx = x + t * (xs[1] - xs[0]); zz = (.16 if (i + r) % 2 else -.16) if t == 0 else 0
                pts.append(Vector((xx, y + rng.uniform(-.03, .03), zz)))
        P.add(tube(pts, .12, sides=3), S('straw', base=.36 + (r % 3) * .04, up=.1, jit=.02))
    P.add(log((-L / 2 - .2, H + .2, 0), (L / 2 + .2, H + .2, 0), .22, sides=6), S('wood', base=.4, jit=.03))
    return P

def duckboard(L=6.0, seed=1):
    P = Prop('Duckboard%d' % int(L)); rng = random.Random(seed)
    for zz in (-.6, .6): P.add(T(box((L, .22, .3)), (0, .11, zz)), S('wooddk', base=.4, jit=.03))
    for i in range(int(L / .7)):
        P.add(T(box((.42, .1, 1.7)), (-L / 2 + .35 + i * .7, .27, 0), rng.uniform(-3, 3)), S('wood', base=.46 + rng.uniform(-.06, .06), up=.1, jit=.02))
    return P

# ------------------------------------------------------------------ siege engines
def wheel(P, c, R=1.6, w=.6, axis='x', spokes=8, col='wood'):
    """spoked wheel: hub with iron cap, spokes, felloe ring, iron tyre; axis 'x', 'z' or 'y' (lying flat)"""
    pitch, roll = {'x': (0, 90), 'z': (90, 0), 'y': (0, 0)}[axis]
    pl = lambda bm: T(bm, c, 0, pitch, roll)
    P.add(pl(T(torus(R - .2, .22, n=16, sides=6), (0, 0, 0), 0, 0, 0, (1, w / .44, 1))), S(col, base=.45, up=.1, jit=.02), smooth=True)
    P.add(pl(T(torus(R, .1, n=16, sides=4), (0, 0, 0), 0, 0, 0, (1, w / .2, 1))), S('iron', base=.42, jit=0), smooth=True)
    P.add(pl(cyl(.35, w + .4, sides=8, y0=-(w + .4) / 2)), S('wooddk', base=.45, jit=0))
    P.add(pl(cyl(.42, .14, sides=8, y0=w / 2 + .1)), S('iron', base=.45, jit=0))
    for k in range(spokes):
        a = k * math.tau / spokes
        d = {'x': Vector((0, math.cos(a), math.sin(a))), 'z': Vector((math.cos(a), math.sin(a), 0)), 'y': Vector((math.cos(a), 0, math.sin(a)))}[axis]
        P.add(log(Vector(c) + d * .3, Vector(c) + d * (R - .3), .1, sides=4), S(col, base=.42, jit=.02))

def rot_mb(mb, pitch=0.0, roll=0.0, lift=0.0):
    M = Matrix.Rotation(math.radians(pitch), 3, 'X') @ Matrix.Rotation(math.radians(roll), 3, 'Z')
    mb.V = [tuple(M @ Vector(v) + Vector((0, lift, 0))) for v in mb.V]

def trebuchet(team='red'):
    """counterweight trebuchet, cocked (throws toward -Z): skid frame on wheels, braced A-frames, iron-capped axle,
    tapered arm, hinged iron-banded counterweight box heaped with stones, sling + stone in the trough, windlass"""
    P = Prop('Trebuchet_%s' % team); rng = random.Random(7)
    for sx in (-1, 1): P.add(bar((sx * 4.5, 1.0, -11), (sx * 4.5, 1.0, 11), .9, .9, .08), S('wood', base=.42, up=.1, jit=.03))
    for z in (-10.2, -4.0, 4.0, 10.2): P.add(bar((-5.0, 1.55, z), (5.0, 1.55, z), .7, .5, .06), S('wood', base=.4, up=.1, jit=.03))
    for sx in (-1, 1):
        for sz in (-1, 1): wheel(P, (sx * 5.5, 1.6, sz * 8.6), R=1.6, w=.5)
    A = Vector((0, 13.0, 0))
    for sx in (-1, 1):
        x = sx * 4.5
        for sz in (-1, 1): P.add(bar((x, 1.4, sz * 7.0), (x, 13.0, sz * .4), .75, .75, .06), S('wood', base=.44, up=.1, jit=.03))
        P.add(bar((x, 1.4, 0), (x, 13.6, 0), .7, .7, .06), S('wood', base=.46, up=.1, jit=.03))
        for sz in (-1, 1): P.add(bar((x, 1.4, sz * 3.6), (x, 6.8, sz * .3), .45, .45, .04), S('wood', base=.4, jit=.03))
        P.add(bar((x, 6.4, -3.6), (x, 6.4, 3.6), .45, .45, .04), S('wood', base=.4, jit=.03))
        P.add(T(box((1.0, 1.0, 1.2), .08), (x, 13.0, 0)), S('iron', base=.42, jit=0))
    P.add(bar((-4.5, 12.1, 0), (4.5, 12.1, 0), .5, .5, .04), S('wood', base=.38, jit=.03))
    P.add(log((-5.4, 13.0, 0), (5.4, 13.0, 0), .45, sides=8), S('iron', base=.4, jit=0))
    E = Vector((0, 1.7, 15.5)); u = (E - A).normalized(); Cw = A - u * 5.0
    P.add(tube([Cw - u * .4, A, E], [.65, .6, .32], sides=8), S('wood', base=.46, up=.1, jit=.03))
    for t in (-.35, .08, .3, .55, .8):
        c = A.lerp(E, t) if t >= 0 else A + (A - Cw) * t * 2.6 / 5
        r_ = .66 if t <= .1 else lerp(.6, .34, t)
        b = torus(r_ + .04, .07, n=10, sides=4); frame_to(T(b, (0, 0, 0), 0, 0, 90), c, c + u); P.add(b, S('iron', base=.42, jit=0))
    cy = Cw.y - 4.4
    for sx in (-1, 1): P.add(bar((sx * 1.4, Cw.y, Cw.z), (sx * 1.6, cy + 4.0, Cw.z), .25, .25, .03), S('iron', base=.42, jit=0))
    P.add(T(box((4.2, 4.0, 4.0), .1), (0, cy + 2.0, Cw.z)), S('wood', base=.38, up=.1, jit=.03))
    for sz in (-1, 1):
        for i in range(5):
            P.add(T(box((4.3, .72, .14), .03), (0, cy + .4 + i * .8, Cw.z + sz * 2.02)), S(team if i == 2 else 'wood', base=.48 + rng.uniform(-.05, .05), up=.1, jit=.02))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(T(box((.22, 4.2, .22)), (sx * 2.1, cy + 2.0, Cw.z + sz * 2.05)), S('iron', base=.4, jit=0))
        P.add(T(box((.16, .3, 4.2)), (sx * 2.12, cy + 3.6, Cw.z)), S('iron', base=.4, jit=0))
    for k in range(9):
        P.add(T(blob(rng.uniform(.55, .9), 30 + k, n=12, sq=.85), (rng.uniform(-1.4, 1.4), cy + 4.0 + rng.uniform(.1, .5), Cw.z + rng.uniform(-1.4, 1.4))), S('stoneg', base=.5, up=.25, jit=.06))
    P.add(T(box((1.6, .3, 13.0)), (0, .55, 3.4)), S('wood', base=.38, jit=.03))      # trough
    for sx in (-1, 1): P.add(T(box((.2, .6, 13.0)), (sx * .9, .8, 3.4)), S('wood', base=.42, jit=.03))
    pouch = Vector((0, 1.15, 9.0))
    for sx in (-1, 1): P.add(tube(sag(E + Vector((sx * .2, 0, 0)), pouch + Vector((sx * .5, .2, 0)), .3, 6), .07, sides=4), S('straw', base=.42, jit=0))
    P.add(T(lathe([(0, 0), (.8, .05), (1.0, .35), (.9, .55), (0, .5)], n=10), pouch - Vector((0, .35, 0))), S('dirt', base=.42, up=.1, jit=.03))
    P.add(T(blob(.75, 77, n=14, sq=.95), pouch + Vector((0, .35, 0))), S('stoneg', base=.55, up=.25, jit=.04))
    P.add(log((-3.6, 2.4, 10.4), (3.6, 2.4, 10.4), .55, sides=8), S('wood', base=.4, jit=.03))   # windlass
    for sx in (-1, 1):
        P.add(T(box((.5, 1.6, .9), .05), (sx * 3.9, 1.6, 10.4)), S('wood', base=.38, jit=.03))
        for k in range(6):
            a = k * math.pi / 3
            P.add(log((sx * 4.3, 2.4, 10.4), (sx * 4.3, 2.4 + math.cos(a) * 1.8, 10.4 + math.sin(a) * 1.8), .12, sides=5), S('wood', base=.45, jit=.02))
    P.add(tube([Vector((0, 2.95, 10.4)), Vector((0, 2.6, 13.0)), E + Vector((0, .3, -.3))], .08, sides=4), S('straw', base=.42, jit=0))
    return P

def shot_stone(r, seed):
    """dressed round trebuchet shot: smooth lathe sphere, slightly irregular"""
    rng = random.Random(seed)
    bm = lathe([(0, -r)] + [(r * math.sin(k * math.pi / 6) * rng.uniform(.95, 1.04), -r * math.cos(k * math.pi / 6)) for k in range(1, 6)] + [(0, r)], n=10)
    return bm

def ammo_pile(seed=1):
    """trebuchet shot: round stones stacked on a plank pallet"""
    P = Prop('AmmoPile%d' % seed); rng = random.Random(seed)
    for zz in (-1.2, 1.2): P.add(T(box((4.6, .35, .5)), (0, .18, zz)), S('wooddk', base=.42, jit=.03))
    for i in range(8): P.add(T(box((.5, .14, 3.2), .02), (-2.1 + i * .6, .42, 0), rng.uniform(-3, 3)), S('wood', base=.46 + rng.uniform(-.05, .05), jit=.02))
    k = 0
    for lvl, (nx, nz_) in enumerate(((3, 2), (2, 1), (1, 1))):
        for i in range(nx):
            for j in range(nz_):
                x = (i - (nx - 1) / 2) * 1.4; z = (j - (nz_ - 1) / 2) * 1.4 + (0 if lvl == 0 else .0)
                P.add(T(shot_stone(.72, seed * 11 + k), (x, 1.2 + lvl * 1.0, z)), S('stoneg', base=.56, up=.25, jit=.03, seed=k), smooth=True); k += 1
    P.add(T(shot_stone(.7, seed * 3), (2.9, .62, .8)), S('stoneg', base=.52, up=.25, jit=.03), smooth=True)
    return P

def siege_tower(team='red'):
    """tapered timber assault tower on six solid wheels: cladding planks under nailed hides, raised drawbridge with
    chains, plank crenels on top, open back with ladders, team shields"""
    P = Prop('SiegeTower_%s' % team); rng = random.Random(11); Hh = 26.0; b0, b1 = 5.0, 4.0
    hwf = lambda y: lerp(b0, b1, y / Hh)
    for sx in (-1, 1):
        for zz in (-3.6, 0.0, 3.6):
            c = Vector((sx * 5.7, 1.5, zz))
            P.add(T(cyl(1.5, .7, sides=12, y0=-.35), c, 0, 0, 90), S('wood', base=.44, up=.05, jit=.03), smooth=True)
            P.add(T(T(torus(1.5, .12, n=12, sides=4), (0, 0, 0), 0, 0, 0, (1, 3, 1)), c, 0, 0, 90), S('iron', base=.42, jit=0))
            P.add(T(cyl(.38, 1.1, sides=8, y0=-.55), c, 0, 0, 90), S('iron', base=.45, jit=0))
    for zz in (-3.6, 0.0, 3.6): P.add(bar((-6.3, 1.5, zz), (6.3, 1.5, zz), .5, .5, .04), S('wooddk', base=.4, jit=.03))
    for sx in (-1, 1): P.add(bar((sx * b0, 2.4, -5.6), (sx * b0, 2.4, 5.6), .8, .8, .06), S('wood', base=.4, up=.1, jit=.03))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(bar((sx * b0, 2.0, sz * b0), (sx * b1, Hh, sz * b1), .7, .7, .06), S('wood', base=.42, up=.1, jit=.03))
    for fy in (2.8, 9.0, 15.2, 21.4):                                           # floors
        h_ = hwf(fy)
        for sz in (-1, 1): P.add(bar((-h_, fy, sz * h_), (h_, fy, sz * h_), .45, .45, .04), S('wood', base=.38, jit=.03))
        for sx in (-1, 1): P.add(bar((sx * h_, fy, -h_), (sx * h_, fy, h_), .45, .45, .04), S('wood', base=.38, jit=.03))
        P.add(T(box((h_ * 2 - .4, .25, h_ * 2 - .4)), (0, fy + .3, 0)), S('wooddk', base=.4, jit=.04))
    for yaw in (0, 90, -90):                                                    # cladding planks + hides (front, sides)
        tmp = Prop('_c'); n = 11
        for i in range(n):
            t = (i + .5) / n * 2 - 1
            a = (t * b0, 2.4, -b0 - .1); b = (t * b1 * .98, Hh - .4, -b1 - .1)
            tmp.add(bar(a, b, .86, .28, .03), S('wood', base=.44 + rng.uniform(-.06, .06), up=.08, jit=.02))
        for k in range(6):
            y0 = 4.0 + (k // 2) * 6.6; x0 = -2.4 + (k % 2) * 3.5; hh = 5.6; ww = 3.0 + rng.uniform(-.3, .3)
            hw_ = lambda y: hwf(y) / b0
            pts = []
            for yy, xx in ((y0, x0), (y0, x0 + ww), (y0 + hh, x0 + ww * .95), (y0 + hh + .4, x0 + .1)):
                z = -lerp(b0, b1, yy / Hh) - .3
                for dz in (0, .12): pts.append(Vector((xx * lerp(1, b1 / b0, yy / Hh), yy + rng.uniform(-.2, .2), z - dz)))
            tmp.add(hull(pts), S('canvas', base=.38 + rng.uniform(-.05, .05), up=.05, jit=.04, seed=k))
            for j in range(4):
                yy = y0 + .3 + j * hh / 3.4; z = -lerp(b0, b1, yy / Hh) - .45
                tmp.add(T(cyl(.09, .1, sides=4), ((x0 + .3) * lerp(1, b1 / b0, yy / Hh), yy, z), 0, 90), S('iron', base=.6, jit=0))
        if yaw != 0:
            heater_shield(tmp, (0, 17.0, -lerp(b0, b1, 17 / Hh) - .5), 0, team, s=1.8, tilt=-2)
        merge(P, tmp, yaw)
    for i in range(7):                                                          # drawbridge (raised) + chains
        x = -3.0 + i * 1.0
        P.add(T(box((.92, 6.0, .3), .03), (x, 21.6 + 3.0, -b1 - .7)), S('wood', base=.44 + rng.uniform(-.05, .05), jit=.02))
    for y in (22.6, 26.4): P.add(T(box((6.8, .35, .2)), (0, y, -b1 - .9)), S('iron', base=.4, jit=0))
    for sx in (-1, 1): P.add(tube(sag((sx * 2.8, 27.4, -b1 - .9), (sx * 3.6, Hh + 1.2, -b1 + .2), .3, 4), .1, sides=4), S('iron', base=.45, jit=0))
    for k in range(6):                                                          # plank crenels on top
        for yaw in (0, 90, 180, -90):
            if yaw == 0: continue
            tmp = Prop('_m'); x = -b1 + .7 + k * (b1 * 2 - 1.4) / 5
            tmp.add(T(box((.9, 2.0 if k % 2 == 0 else 1.0, .25), .03), (x, Hh + (1.0 if k % 2 == 0 else .5), -b1)), S('wood', base=.46, jit=.02))
            merge(P, tmp, yaw)
    P.add(T(box((b1 * 2, .3, b1 * 2)), (0, Hh + .1, 0)), S('wooddk', base=.42, jit=.04))
    for fy, fy2 in ((2.8, 9.0), (9.0, 15.2), (15.2, 21.4), (21.4, 26.0)):         # ladders at the open back
        x = 1.6 if fy % 2 else -1.6
        for dx in (-.6, .6): P.add(bar((x + dx, fy + .3, hwf(fy) - .8), (x + dx, fy2 + .3, hwf(fy2) - 2.2), .2, .2, .02), S('wood', base=.48, jit=.02))
        for r in range(int((fy2 - fy) / .9)):
            t = (r + .5) / int((fy2 - fy) / .9); y = lerp(fy + .3, fy2 + .3, t); z = lerp(hwf(fy) - .8, hwf(fy2) - 2.2, t)
            P.add(bar((x - .6, y, z), (x + .6, y, z), .14, .14, .01), S('wood', base=.5, jit=.02))
    return P

def battering_ram():
    """wheeled ram shed: post frame, gable roof of planks under overlapping hides, iron-capped log on ropes"""
    P = Prop('BatteringRam'); rng = random.Random(5); Lz, Wx, Hr = 12.0, 5.6, 5.8
    for sx in (-1, 1):
        for sz in (-1, 1): wheel(P, (sx * 3.4, 1.3, sz * 4.0), R=1.3, w=.45)
        P.add(bar((sx * 2.8, 1.5, -Lz / 2), (sx * 2.8, 1.5, Lz / 2), .6, .6, .05), S('wood', base=.4, jit=.03))
        for z in (-Lz / 2 + .3, 0.0, Lz / 2 - .3): P.add(bar((sx * 2.8, 1.5, z), (sx * 2.8, 4.2, z), .5, .5, .04), S('wood', base=.44, jit=.03))
        P.add(bar((sx * 2.8, 4.2, -Lz / 2), (sx * 2.8, 4.2, Lz / 2), .5, .5, .04), S('wood', base=.42, jit=.03))
    for z in (-Lz / 2 + .3, Lz / 2 - .3): P.add(bar((-2.8, 1.5, z), (2.8, 1.5, z), .45, .45, .04), S('wood', base=.38, jit=.03))
    P.add(bar((0, Hr, -Lz / 2 - .4), (0, Hr, Lz / 2 + .4), .55, .55, .05), S('wood', base=.42, jit=.03))
    for sx in (-1, 1):
        n = 12
        for i in range(n):
            z = -Lz / 2 + (i + .5) * Lz / n
            P.add(bar((sx * 3.5, 3.8, z), (0, Hr + .3, z), Lz / n - .06, .2, .02), S('wood', base=.42 + rng.uniform(-.05, .05), jit=.02))
        for k in range(4):
            z0 = -Lz / 2 + k * Lz / 4 - .2; z1 = z0 + Lz / 4 + .5
            pts = []
            for zz in (z0, z1):
                for t, dy in ((0.0, .0), (1.0, .0)):
                    p = Vector((sx * 3.5, 3.8, zz)).lerp(Vector((0, Hr + .3, zz)), t * .96)
                    pts += [p + Vector((0, .25, 0)), p + Vector((0, .4, 0))]
            P.add(hull([p + Vector((sx * rng.uniform(-.1, .3), rng.uniform(-.1, .1), 0)) for p in pts]), S('canvas', base=.36 + rng.uniform(-.05, .05), up=.1, jit=.04, seed=k))
    ram = tube([Vector((0, 2.6, Lz / 2 + 1.0)), Vector((0, 2.6, -Lz / 2 - 2.6))], [.7, .75], sides=9)
    P.add(ram, S('wooddk', base=.5, up=.1, jit=.03))
    P.add(T(lathe([(0, 0), (.95, 0), (.95, 1.4), (.6, 2.2), (0, 2.6)], n=9), (0, 2.6, -Lz / 2 - 2.6), 90), S('iron', base=.45, up=.1, jit=0))
    for z in (-Lz / 2 - 1.6, -Lz / 2 - .6, 2.0, Lz / 2):
        P.add(T(torus(.78, .1, n=10, sides=4), (0, 2.6, z), 0, 90), S('iron', base=.42, jit=0))
    for z in (-3.0, 3.0):
        for sx in (-1, 1): P.add(tube([Vector((sx * .3, Hr - .2, z)), Vector((sx * .5, 3.2, z + .4))], .08, sides=4), S('straw', base=.42, jit=0))
    return P

def mantlet(team='red', seed=1):
    """wheeled oak pavise: planks with a cut sight slit, iron bands, painted team chevron, rear prop, arrows stuck"""
    P = Prop('Mantlet_%s%d' % (team, seed)); rng = random.Random(seed); W, Hm = 5.4, 5.6; lean = 12
    n = 7
    for i in range(n):
        x = -W / 2 + (i + .5) * W / n
        for y0, y1 in ((.3, 3.75), (4.2, Hm + rng.uniform(-.2, .25))):
            P.add(T(T(box((W / n - .06, y1 - y0, .3), .03), (x, (y0 + y1) / 2, 0)), (0, 0, 0), 0, lean), S('wood', base=.46 + rng.uniform(-.05, .05), up=.05, jit=.02))
    for y in (1.2, 3.3, 5.0): P.add(T(T(box((W + .2, .32, .12)), (0, y, -.2)), (0, 0, 0), 0, lean), S('iron', base=.42, jit=0))
    for sg in (-1, 1):
        P.add(T(T(box((2.9, .55, .06)), (sg * .9, 2.2, -.2), 0, 0, sg * -32), (0, 0, 0), 0, lean), S(team, base=.56, up=.05, jit=0))
    P.add(log((-W / 2 - .4, .7, .3), (W / 2 + .4, .7, .3), .16, sides=6), S('iron', base=.4, jit=0))
    for sg in (-1, 1): wheel(P, (sg * (W / 2 + .4), .7, .3), R=.75, w=.25, spokes=6)
    P.add(bar((0, 4.6, 1.0), (0, -.3, 3.6), .32, .32, .03), S('wood', base=.4, jit=.03))
    for k in range(4):
        x = rng.uniform(-2, 2); y = rng.uniform(1.6, 5.0); z = -.25 - math.tan(math.radians(lean)) * y
        d = Vector((rng.uniform(-.2, .2), rng.uniform(.1, .35), -1)).normalized(); a = Vector((x, y, z)); b = a + d * 2.6
        P.add(log(a, b, .05, sides=4), S('wood', base=.6, jit=0))
        for j in range(3):
            P.add(T(box((.02, .2, .45)), b - d * .25, j * 120, 0, 0), S('canvas', base=.8, jit=0))
    return P

# ------------------------------------------------------------------ camp + clutter
def tent(team='red', seed=1):
    """ridge tent (door at -Z): sagging canvas with a team hem band, closed back, front flaps tied open, poles,
    guy ropes + pegs, bedroll and chest inside"""
    P = Prop('Tent_%s' % team); rng = random.Random(seed); hw, hl, ht = 3.2, 4.2, 5.0
    def slope(sg):
        bm = bmesh.new(); NU, NV = 8, 4; V = []
        for i in range(NU + 1):
            z = -hl + 2 * hl * i / NU; row = []
            for j in range(NV + 1):
                t = j / NV; x = sg * hw * t; y = lerp(ht, .35, t) - .35 * math.sin(math.pi * t) * (1 - abs(z) / hl * .3)
                y -= .22 * math.sin(math.pi * i / NU * 2) ** 2 * math.sin(math.pi * t)
                row.append(bm.verts.new((x * (1 + .05 * t), y, z)))
            V.append(row)
        for i in range(NU):
            for j in range(NV): bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        for f in bm.faces:
            f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.12)
        return bm
    uc, ut = PAL.u('canvas'), PAL.u(team)
    def tsh(f):
        c = f.calc_center_median(); hem = c.y < 1.35
        v = (.52 if hem else .68) + f.normal.y * .12 + (h01(c.x, c.y, c.z) - .5) * .05
        return [(ut if hem else uc, clamp(v, .04, .96))] * len(f.loops)
    for sg in (-1, 1): P.add(slope(sg), tsh)
    back = bmesh.new(); vs = [back.verts.new(p) for p in ((-hw, .35, hl), (hw, .35, hl), (0, ht, hl))]
    back.faces.new(vs); bmesh.ops.solidify(back, geom=list(back.faces), thickness=.12); P.add(back, tsh)
    for sg in (-1, 1):                                                          # front flaps tied back
        fl = bmesh.new(); vs = [fl.verts.new(p) for p in ((0, ht - .2, -hl), (sg * hw * .95, .4, -hl), (sg * hw * .55, .5, -hl - 1.4))]
        fl.faces.new(vs); bmesh.ops.solidify(fl, geom=list(fl.faces), thickness=.1); P.add(fl, S('canvas', base=.6, up=.1, jit=.02))
        P.add(T(torus(.3, .07, n=8, sides=4), (sg * hw * .62, 1.6, -hl - .7)), S('straw', base=.42, jit=0))
    for z in (-hl - .1, hl + .1): P.add(log((0, -.4, z), (0, ht + .7, z), .14, sides=6), S('wood', base=.45, jit=.02))
    P.add(log((0, ht + .05, -hl - .3), (0, ht + .05, hl + .3), .12, sides=6), S('wood', base=.45, jit=.02))
    for sz in (-1, 1):
        peg = Vector((0, 0, sz * (hl + 3.6)))
        P.add(tube([Vector((0, ht + .5, sz * (hl + .1))), peg + Vector((0, .3, 0))], .05, sides=4), S('straw', base=.48, jit=0))
        P.add(T(box((.2, .9, .2)), peg + Vector((0, .1, 0)), 0, sz * 18), S('wood', base=.5, jit=0))
    for sx in (-1, 1):
        for z in (-2.4, 0.0, 2.4):
            peg = Vector((sx * (hw + 2.2), 0, z))
            P.add(tube([Vector((sx * hw * .98, .7, z)), peg + Vector((0, .3, 0))], .05, sides=4), S('straw', base=.48, jit=0))
            P.add(T(box((.2, .9, .2)), peg + Vector((0, .1, 0)), 0, 0, -sx * 18), S('wood', base=.5, jit=0))
    P.add(T(blob(.9, 3, n=12, sq=.5), (-1.2, .35, 1.6), 0, 0, 0, (1.0, 1.0, 2.0)), S('canvas', base=.45, up=.2, jit=.05))
    P.add(T(box((1.6, 1.0, 1.0), .08), (1.4, .5, 2.6)), S('wooddk', base=.5, up=.1, jit=.03))
    for dx in (-.5, .5): P.add(T(box((.12, 1.04, 1.04)), (1.4 + dx, .5, 2.6)), S('iron', base=.42, jit=0))
    P.add(T(box((hw * 2, .1, hl * 2)), (0, .05, 0)), S('dirt', base=.3, jit=.02))
    return P

def flame(P, c, h=2.2, r=.6, seed=0, key='fire'):
    rng = random.Random(seed)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); d = r * rng.uniform(.2, .55)
        P.gadd(T(spike(r * rng.uniform(.35, .5), h * rng.uniform(.55, 1.0), sides=5, shoulder=.35), (c[0] + math.cos(a) * d, c[1], c[2] + math.sin(a) * d), rng.uniform(0, 60), rng.uniform(-14, 14), rng.uniform(-14, 14)), key)
    P.gadd(T(spike(r * .5, h * .45, sides=5, shoulder=.4), c), 'ember')

def campfire(seed=1):
    """stone ring, crossed charred logs, flames, tripod with an iron pot on a chain, log seats"""
    P = Prop('Campfire%d' % seed); rng = random.Random(seed)
    for k in range(10):
        a = k * math.tau / 10
        P.add(T(rock((.55, .4, .45), seed=seed * 9 + k, n=10), (math.cos(a) * 1.9, .1, math.sin(a) * 1.9)), S('stoneg', base=.48, up=.25, jit=.06))
    for k in range(4):
        a = k * math.pi / 4 + .3
        d = Vector((math.cos(a), .32, math.sin(a))); P.add(log(Vector((0, .2, 0)) - d * 1.6, Vector((0, .35, 0)) + d * 1.6, .22, sides=6), S('wooddk', base=.3, up=.1, jit=.05))
    P.add(T(cyl(1.4, .12, sides=10), (0, 0, 0)), S('wooddk', base=.12, jit=.03))
    flame(P, (0, .3, 0), h=2.4, r=.7, seed=seed)
    top = Vector((0, 6.0, 0))
    for k in range(3):
        a = k * math.tau / 3 + .5
        P.add(log(Vector((math.cos(a) * 3.0, -.2, math.sin(a) * 3.0)), top + Vector((math.cos(a) * .2, .3, math.sin(a) * .2)), .1, sides=5), S('wood', base=.42, jit=.03))
    P.add(T(torus(.25, .07, n=8, sides=4), top), S('straw', base=.45, jit=0))
    for k in range(4): P.add(T(torus(.12, .04, n=6, sides=3), top - Vector((0, .3 + k * .24, 0)), k * 90, 90, 0), S('iron', base=.42, jit=0))
    P.add(T(lathe([(0, 0), (.5, .05), (.75, .4), (.78, .9), (.68, 1.0), (.62, .95), (0, .95)], n=12), top - Vector((0, 2.75, 0))), S('iron', base=.3, up=.15, jit=0), smooth=True)
    P.add(T(torus(.7, .04, n=12, sides=3), top - Vector((0, 1.82, 0)), 0, 0, 0, (1, 1, 1)), S('iron', base=.4, jit=0))
    for sx in (-1, 1): P.add(log(top - Vector((0, 1.3, 0)), top - Vector((sx * .72, 1.82, 0)), .03, sides=3), S('iron', base=.4, jit=0))
    for k, (x, z, yaw) in enumerate(((-3.6, -1.0, 20), (3.4, 1.6, -15))):
        P.add(T(log((-1.5, .5, 0), (1.5, .5, 0), .5, sides=8), (x, 0, z), yaw), S('wood', base=.42, up=.1, jit=.03))
        for sg in (-1, 1): P.add(T(cyl(.5, .05, sides=8, y0=-.025), (x + sg * 1.5 * math.cos(math.radians(yaw)), .5, z - sg * 1.5 * math.sin(math.radians(yaw))), yaw, 0, 90), S('wood', base=.7, jit=.02))
    return P

def brazier(seed=1):
    """iron brazier: three curled legs, riveted bowl, glowing coals and flames"""
    P = Prop('Brazier%d' % seed)
    for k in range(3):
        a = k * math.tau / 3
        pts = [Vector((math.cos(a) * r, y, math.sin(a) * r)) for r, y in ((1.3, 0), (1.1, .4), (.7, 1.6), (.9, 2.6), (1.0, 3.0))]
        P.add(tube(pts, .12, sides=5), S('iron', base=.4, jit=0))
        P.add(T(torus(.2, .07, n=8, sides=3), (math.cos(a) * 1.35, .2, math.sin(a) * 1.35), -math.degrees(a), 0, 90), S('iron', base=.42, jit=0))
    P.add(T(torus(.75, .08, n=12, sides=4), (0, 1.6, 0)), S('iron', base=.4, jit=0))
    P.add(T(lathe([(0, 0), (.5, 0), (1.0, .25), (1.45, .8), (1.5, 1.05), (1.35, 1.0), (0, .7)], n=14), (0, 2.6, 0)), S('iron', base=.35, up=.15, jit=0), smooth=True)
    for k in range(10): P.add(T(cyl(.07, .08, sides=4), (math.cos(k * .628) * 1.48, 3.5, math.sin(k * .628) * 1.48), -math.degrees(k * .628) + 90, 90), S('iron', base=.6, jit=0))
    for k in range(7):
        a = k * .9; P.gadd(T(blob(.35, 40 + k, n=8, sq=.6), (math.cos(a) * .6, 3.45, math.sin(a) * .6)), 'ember')
    flame(P, (0, 3.4, 0), h=2.0, r=.75, seed=seed + 3)
    return P

def crate(P, c, s=2.2, yaw=0.0, seed=0):
    """plank crate: core + slat boards + iron corner brackets"""
    rng = random.Random(seed); tmp = Prop('_k')
    tmp.add(T(box((s - .1, s - .1, s - .1)), (0, s / 2, 0)), S('wood', base=.36, jit=.03))
    for sg in (-1, 1):
        for axis in range(2):
            for k in range(3):
                o = (k - 1) * s / 3
                if axis == 0: tmp.add(T(box((s, s / 3 - .08, .12)), (0, s / 2 + o, sg * s / 2)), S('wood', base=.5 + rng.uniform(-.06, .06), up=.08, jit=.02))
                else: tmp.add(T(box((.12, s / 3 - .08, s)), (sg * s / 2, s / 2 + o, 0)), S('wood', base=.48 + rng.uniform(-.06, .06), up=.08, jit=.02))
        for sz in (-1, 1):
            tmp.add(T(box((.5, .3, .5)), (sg * (s / 2 - .15), s - .15, sz * (s / 2 - .15))), S('iron', base=.42, jit=0))
    tmp.add(T(box((s + .02, .14, s + .02), .02), (0, s - .05, 0)), S('wood', base=.55, up=.1, jit=.02))
    merge(P, tmp, yaw, c)

def barrel(P, c, h=2.6, r=1.0, seed=0, tilt=0.0):
    rng = random.Random(seed)
    prof = [(0, 0)] + [(r * (1 + .14 * math.sin(math.pi * k / 6)), h * k / 6) for k in range(7)] + [(0, h)]
    bm = lathe(prof, n=12)
    P.add(T(bm, c, rng.uniform(0, 30), tilt), lambda f: [(PAL.u('wood'), clamp(.42 + .1 * (int((math.atan2(f.calc_center_median().z - c[2], f.calc_center_median().x - c[0]) % math.tau) / math.tau * 12) % 2) + f.normal.y * .15, .04, .96))] * len(f.loops))
    for t in (.12, .38, .62, .88):
        rr = r * (1 + .14 * math.sin(math.pi * t)) + .04
        P.add(T(T(torus(rr, .07, n=12, sides=3), (0, h * t, 0)), c, 0, tilt), S('iron', base=.4, jit=0))

def supply_pile(seed=1):
    """two crates, a barrel pair, tied sacks"""
    P = Prop('Supplies%d' % seed); rng = random.Random(seed)
    crate(P, (0, 0, 0), 2.3, rng.uniform(-10, 10), seed); crate(P, (.3, 2.3, .1), 1.8, rng.uniform(10, 30), seed + 1)
    crate(P, (2.6, 0, -.8), 2.0, rng.uniform(-30, -10), seed + 2)
    barrel(P, (-2.4, 0, .4), seed=seed); barrel(P, (-2.2, 0, 2.6), h=2.4, seed=seed + 1)
    for k in range(3):
        x, z = 1.6 + k * .9, 1.8 + (k % 2) * .6
        P.add(T(blob(.75, seed * 5 + k, n=14, sq=.8), (x, .7, z), 0, 0, 0, (1, 1.15, 1)), S('canvas', base=.55, up=.2, jit=.05))
        P.add(T(cyl(.25, .3, sides=6), (x, 1.5, z)), S('canvas', base=.5, jit=0))
        P.add(T(torus(.27, .05, n=6, sides=3), (x, 1.5, z)), S('straw', base=.4, jit=0))
    return P

def hay_bales(seed=1):
    """stacked straw bales with twine bands and loose straw"""
    P = Prop('HayBales%d' % seed); rng = random.Random(seed)
    spots = [(-1.5, 0, 0, 5), (1.4, 0, .3, -8), (0, 0, 1.8, 90), (0, 1.35, .3, 4)]
    for k, (x, y, z, yaw) in enumerate(spots):
        b = box((2.8, 1.3, 1.5), .22); T(b, (x, y + .65, z), yaw + rng.uniform(-4, 4))
        P.add(b, S('straw', base=.6, up=.15, jit=.06, seed=k))
        for o in (-.7, .7):
            ox, oz = o * math.cos(math.radians(yaw)), -o * math.sin(math.radians(yaw))
            P.add(T(box((.1, 1.36, 1.56)), (x + ox, y + .65, z + oz), yaw), S('straw', base=.3, jit=0))
    for k in range(10):
        a = rng.uniform(0, math.tau); d = rng.uniform(1.8, 3.4)
        P.add(T(box((.9, .05, .12)), (math.cos(a) * d, .03, math.sin(a) * d), rng.uniform(0, 180)), S('straw', base=.7, jit=.05))
    return P

def broken_cart(seed=1):
    """two-wheeled cart slumped on a snapped wheel: plank bed, side stakes, shafts down, the lost wheel and spill"""
    P = Prop('BrokenCart%d' % seed); rng = random.Random(seed); roll = 13
    tmp = Prop('_c')
    tmp.add(T(box((3.6, .3, 6.0), .04), (0, 2.0, 0)), S('wood', base=.44, up=.1, jit=.03))
    for i in range(7): tmp.add(T(box((3.7, .08, .8), .02), (0, 2.18, -2.6 + i * .86)), S('wood', base=.5 + rng.uniform(-.05, .05), up=.1, jit=.02))
    for sx in (-1, 1):
        tmp.add(bar((sx * 1.9, 2.0, -3.0), (sx * 1.9, 2.0, 3.0), .3, .3, .03), S('wooddk', base=.4, jit=.03))
        for k in range(5):
            z = -2.6 + k * 1.3; tmp.add(log((sx * 1.85, 2.0, z), (sx * 1.85, 3.6, z), .1, sides=5), S('wooddk', base=.42, jit=.03))
        tmp.add(bar((sx * 1.85, 3.5, -2.9), (sx * 1.85, 3.5, 2.9), .2, .2, .02), S('wood', base=.42, jit=.02))
        tmp.add(bar((sx * .9, 2.0, -3.0), (sx * .7, .1, -7.0), .26, .26, .03), S('wood', base=.42, jit=.03))
    tmp.add(log((-2.3, 1.4, .4), (2.3, 1.4, .4), .16, sides=6), S('iron', base=.4, jit=0))
    wheel(tmp, (2.25, 1.4, .4), R=1.5, w=.35)
    rot_mb(tmp.solid, 0, roll, -.3)
    merge(P, tmp)
    lw = Prop('_w'); wheel(lw, (0, .35, 0), R=1.5, w=.35, axis='y'); rot_mb(lw.solid, 6, 0); merge(P, lw, 25, (-4.2, 0, 2.4))
    for k in range(3):
        P.add(T(blob(.7, seed * 7 + k, n=12, sq=.7), (-2.6 + k * .8, .45, -1.5 - k * .5), 0, 0, 0, (1, 1, 1.3)), S('canvas', base=.55, up=.2, jit=.05))
    crate(P, (-2.8, 0, 1.0), 1.6, 33, seed)
    return P

def weapon_rack(team='red'):
    """A-frame rack: five spears, three swords, two team shields leaning at its foot"""
    P = Prop('WeaponRack_%s' % team); rng = random.Random(3)
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(bar((sx * 2.6, -.3, sz * 1.2), (sx * 2.6, 3.6, 0), .3, .3, .03), S('wood', base=.42, jit=.03))
    P.add(bar((-2.9, 3.4, 0), (2.9, 3.4, 0), .32, .32, .03), S('wood', base=.46, jit=.03))
    P.add(bar((-2.7, 1.0, -.75), (2.7, 1.0, -.75), .26, .26, .03), S('wood', base=.42, jit=.03))
    for k in range(5):
        x = -2.0 + k * 1.0; base = Vector((x, .2, -1.1)); top = Vector((x + rng.uniform(-.1, .1), 6.2, .5))
        P.add(log(base, top, .07, sides=5), S('wood', base=.55, jit=.02))
        d = (top - base).normalized(); h_ = spike(.18, 1.0, sides=4, shoulder=.3); T(h_, (0, 0, 0), 0, 0, 0, (1, 1, .35)); frame_to(T(h_, (0, 0, 0), 0, 0, -90), top, top + d)
        P.add(h_, S('iron', base=.62, up=.1, jit=0))
    for k in range(3):
        x = -1.5 + k * 1.5
        P.add(T(box((.32, 2.7, .06)), (x, 1.75, .9)), S('iron', base=.7, up=.1, jit=0))
        P.add(T(box((1.2, .18, .22), .03), (x, 3.18, .9)), S('iron', base=.4, jit=0))
        P.add(T(cyl(.1, .8, sides=6), (x, 3.27, .9)), S('wooddk', base=.42, jit=0))
        P.add(T(lathe([(0, 0), (.18, .05), (.18, .2), (0, .25)], n=6), (x, 4.05, .9)), S('brass', base=.6, jit=0))
    for k, x in enumerate((-1.3, 1.4)):
        heater_shield(P, (x, -.05, -1.9 - k * .3), rng.uniform(-10, 10), team, s=1.35, tilt=-14)
    return P

def training_dummy(team='red', seed=1):
    """straw dummy on a post and crossbar, twine bands, sack head, a team shield on its arm"""
    P = Prop('Dummy_%s%d' % (team, seed))
    P.add(log((0, -.6, 0), (0, 4.4, 0), .2, sides=6), S('wooddk', base=.45, jit=.03))
    P.add(bar((-1.8, 3.3, 0), (1.8, 3.3, 0), .22, .22, .03), S('wood', base=.45, jit=.03))
    P.add(T(blob(1.0, seed + 3, n=16, sq=.9), (0, 2.6, 0), 0, 0, 0, (1, 1.4, .8)), S('straw', base=.6, up=.15, jit=.06))
    for y in (2.0, 3.0): P.add(T(torus(.92, .06, n=10, sides=3), (0, y, 0), 0, 0, 0, (1, 1, .8)), S('straw', base=.3, jit=0))
    for sx in (-1, 1): P.add(T(blob(.4, seed + sx, n=10, sq=.9), (sx * 1.7, 3.3, 0), 0, 0, 0, (1.4, 1, 1)), S('straw', base=.58, jit=.05))
    P.add(T(blob(.6, seed + 9, n=12, sq=.9), (0, 4.5, 0)), S('canvas', base=.55, up=.15, jit=.05))
    P.add(T(torus(.3, .06, n=8, sides=3), (0, 4.0, 0)), S('straw', base=.4, jit=0))
    heater_shield(P, (1.75, 2.1, -.45), 8, team, s=1.0)
    return P

def ladder(L=16.0, seed=1, lean=0.0):
    """siege ladder leaning back by lean degrees (top toward +Z): two rails, lashed rungs"""
    P = Prop('Ladder%d_%d' % (int(L), int(lean)))
    for sx in (-1, 1): P.add(bar((sx * .9, 0, 0), (sx * .8, L, 0), .26, .26, .03), S('wood', base=.46, jit=.03))
    for k in range(int(L / 1.1)):
        y = .6 + k * 1.1; w = lerp(.9, .8, y / L)
        P.add(log((-w, y, 0), (w, y, 0), .09, sides=5), S('wood', base=.5, jit=.02))
        for sx in (-1, 1): P.add(T(torus(.18, .04, n=6, sides=3), (sx * w, y, 0), 0, 0, 90), S('straw', base=.4, jit=0))
    if lean: rot_mb(P.solid, lean)
    return P

def battle_debris(team='red', seed=1):
    """small battlefield litter: a dropped team shield, a dented helm, a snapped spear, arrows stuck in the turf"""
    P = Prop('Debris_%s%d' % (team, seed)); rng = random.Random(seed)
    heater_shield(P, (0, .15, 0), rng.uniform(0, 360), team, s=1.2, tilt=-82)
    helm = lathe([(.66, -.05), (.68, .05), (.64, .3), (.6, .7), (.45, 1.05), (.2, 1.22), (0, 1.25)], n=14)
    P.add(T(helm, (2.2, .55, 1.2), rng.uniform(0, 360), 0, 75), S('iron', base=.62, up=.25, jit=0), smooth=True)
    P.add(T(torus(.67, .06, n=14, sides=4), (2.2, .55, 1.2), 0, 0, 75), S('brass', base=.55, jit=0))
    P.add(log((-2.6, .15, 1.5), (.4, .3, 2.6), .07, sides=5), S('wood', base=.55, jit=.02))
    P.add(log((-3.1, .12, .4), (-2.5, .14, 1.4), .07, sides=5), S('wood', base=.5, jit=.02))
    for k in range(6):
        a = Vector((rng.uniform(-2, 3), -.3, rng.uniform(-2.4, -.8))); d = Vector((rng.uniform(-.4, .4), 1, rng.uniform(-.3, .5))).normalized(); b = a + d * 2.4
        P.add(log(a, b, .05, sides=4), S('wood', base=.6, jit=0))
        for j in range(3):
            a3 = math.radians(j * 120); P.add(T(box((.03, .5, .2)), b - d * .35 + Vector((math.cos(a3) * .08, 0, math.sin(a3) * .08)), -j * 120), S('red' if k % 2 else 'canvas', base=.65, jit=0))
    return P

def rough_stone(w, h, d, seed):
    """a field stone: a box with jittered corners and a few extra points, hulled (tight packing, irregular faces)"""
    rng = random.Random(seed); pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1): pts.append(Vector((sx * w / 2 * rng.uniform(.82, 1.0), sy * h / 2 * rng.uniform(.8, 1.0), sz * d / 2 * rng.uniform(.82, 1.0))))
    for k in range(5):
        pts.append(Vector((rng.uniform(-w, w) * .4, h / 2 * rng.choice((-1, 1)) * rng.uniform(.9, 1.1), rng.uniform(-d, d) * .4)))
    return hull(pts)

def drystone_wall(L=12.0, seed=1):
    """low field wall of tightly stacked rough stones (3 courses, battered), upright coping stones, moss; one slumped
    gap with the fallen stones at its foot"""
    P = Prop('DryWall%d_%d' % (int(L), seed)); rng = random.Random(seed); gap = L * .22
    for c in range(3):
        y = c * .95; x = -L / 2 - rng.uniform(0, .6); dep = 1.7 - c * .2
        while x < L / 2:
            w = rng.uniform(1.0, 1.7); xc = min(x + w / 2, L / 2 - w / 4)
            if not (c >= 1 and abs(xc - gap) < 1.3 + (c - 1) * .5):
                P.add(T(rough_stone(w, .98, dep, seed * 97 + c * 31 + int((x + 50) * 7)), (xc, y + .45, rng.uniform(-.08, .08)), rng.uniform(-4, 4), 0, rng.uniform(-4, 4)),
                      S('stoneg', base=.5 + rng.uniform(-.07, .07), up=.2, jit=.04))
            x += w * .97
    x = -L / 2 + .25
    while x < L / 2 - .2:
        if abs(x - gap) > 1.9:
            P.add(T(rough_stone(.36, 1.0, 1.25, seed * 13 + int(x * 11)), (x, 3.2, 0), 0, 0, rng.uniform(-12, 12)), S('stoneg', base=.56, up=.15, jit=.04))
        x += .4
    for k in range(5):
        x = rng.uniform(-L / 2 + 1, L / 2 - 1)
        if abs(x - gap) < 2: continue
        P.add(T(blob(.55, seed + k, n=10, sq=.45), (x, 2.75, rng.uniform(-.6, .6)), 0, 0, 0, (1.5, .5, 1)), S('grass', base=.42, up=.3, jit=.08))
    for k in range(5):
        P.add(T(rough_stone(rng.uniform(.9, 1.4), .8, 1.1, seed * 5 + k), (gap + rng.uniform(-1.6, 1.6), .3, rng.choice((-1, 1)) * rng.uniform(1.2, 2.0)), rng.uniform(0, 90), rng.uniform(-15, 15), rng.uniform(-15, 15)), S('stoneg', base=.48, up=.25, jit=.05))
    return P

def rubble(seed=1, s=1.0):
    """a heap of fallen ashlar blocks and broken stone"""
    P = Prop('Rubble%d' % seed); rng = random.Random(seed)
    for i in range(9):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.4) * s
        stone(P, (math.cos(a) * d, rng.uniform(.3, 1.2) * s * (1 - d / 3.5), math.sin(a) * d), (rng.uniform(1.6, 2.6) * s, rng.uniform(.9, 1.3) * s, rng.uniform(1.2, 1.7) * s),
              rng.uniform(0, 180), col='stone', base=.6, seed=seed * 3 + i, roll=rng.uniform(-30, 30), pitch=rng.uniform(-25, 25))
    for i in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(1.0, 3.2) * s
        P.add(T(rock((.6 * s, .4 * s, .5 * s), seed=seed * 7 + i, n=10), (math.cos(a) * d, .1, math.sin(a) * d)), S('stoneg', base=.5, up=.25, jit=.06))
    return P

# ------------------------------------------------------------------ nature + ground detail
def boulder(seed=1, r=3.0):
    P = Prop('Boulder%d' % seed); rng = random.Random(seed)
    P.add(T(rock((r, r * .62, r * .85), seed=seed, n=26), (0, r * .32, 0)), S('stoneg', base=.5, up=.3, jit=.07, seed=seed))
    P.add(T(rock((r * .45, r * .32, r * .4), seed=seed + 5, n=14), (r * .9, r * .12, r * .4)), S('stoneg', base=.48, up=.3, jit=.07))
    for k in range(3):
        a = rng.uniform(0, math.tau)
        P.add(T(blob(r * .3, seed + k, n=12, sq=.4), (math.cos(a) * r * .3, r * .58, math.sin(a) * r * .25), 0, 0, 0, (1.4, .45, 1.1)), S('grass', base=.42, up=.3, jit=.08))
    return P

PINE_FORMS = {   # tiers, base radius (x h), top radius, skirt height, first skirt (x h), droop
    'tall':  (8, .2, .05, .19, .14, .5),
    'full':  (7, .28, .06, .21, .16, .6),
    'squat': (5, .36, .09, .27, .1, .7),
    'young': (4, .3, .08, .3, .12, .5),
}

def bough_skirt(R, ht, droop, n, rng):
    """one fir whorl: a star skirt (2n rim points: drooping bough tips + raised notches), a tip on top, an underside
    ring so the skirt has thickness and a dark belly; built at y = 0 (rim level)"""
    bm = bmesh.new(); rim = []
    a0 = rng.uniform(0, math.tau)
    for k in range(2 * n):
        a = a0 + k * math.pi / n; tip = k % 2 == 0
        rr = R * (rng.uniform(.95, 1.08) if tip else rng.uniform(.62, .7))
        yy = (-droop * rng.uniform(.8, 1.2)) if tip else ht * .12
        rim.append(bm.verts.new((math.cos(a) * rr, yy, math.sin(a) * rr)))
    top = bm.verts.new((rng.uniform(-.15, .15), ht, rng.uniform(-.15, .15)))
    under = [bm.verts.new((math.cos(a0 + k * math.tau / n) * R * .32, ht * .18, math.sin(a0 + k * math.tau / n) * R * .32)) for k in range(n)]
    m = 2 * n
    for k in range(m): bm.faces.new((rim[k], rim[(k + 1) % m], top))
    for k in range(n):
        u0, u1 = under[k], under[(k + 1) % n]
        bm.faces.new((rim[2 * k + 1], rim[2 * k], u0)); bm.faces.new((rim[(2 * k + 2) % m], rim[2 * k + 1], u1)); bm.faces.new((rim[2 * k + 1], u0, u1))
    bm.faces.new(list(reversed(under)))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def pine(seed=1, h=26.0, form='full'):
    """fir in four forms (tall spire / full / squat broad / young): tapering trunk with root flare and branch
    stubs, whorls of drooping star-shaped bough skirts (tips hang, notches rise), dark bellies, light tops;
    each seed a slightly different green"""
    P = Prop('Pine_%s%d' % (form, seed)); rng = random.Random(seed * 7 + len(form))
    tiers, R0, R1, th, y0, droop = PINE_FORMS[form]
    tone = rng.uniform(-.05, .05)
    bark = S('wood', base=.36, up=.05, jit=.04)
    P.add(tube([Vector((0, -1.0, 0)), Vector((0, h * .5, 0)), Vector((0, h * .95, 0))], [h * .034, h * .022, h * .006], sides=8), bark)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(0, .5)
        P.add(log((math.cos(a) * h * .02, .9, math.sin(a) * h * .02), (math.cos(a) * h * .075, -.3, math.sin(a) * h * .075), h * .017, sides=5, r2=h * .005), bark)
    for i in range(tiers):
        t = i / (tiers - 1)
        y = h * (y0 + (.9 - y0) * t ** .92); R = h * lerp(R0, R1, t ** .85); ht = h * th * lerp(1.0, .8, t)
        n = 6 if R > 3.5 else 5
        sk = bough_skirt(R, ht, h * .03 * droop * lerp(1.2, .5, t), n, rng)
        T(sk, (0, y, 0))
        P.add(sk, S('pine', grad=(y - h * .03, y + ht, .16 + t * .1 + tone, .56 + t * .1 + tone), up=.16, jit=.04, seed=seed + i))
        if i < tiers - 2:                                                       # bare branch stubs under the skirt
            for k in range(3):
                a = rng.uniform(0, math.tau)
                P.add(log((0, y + ht * .1, 0), (math.cos(a) * R * .55, y - h * .01, math.sin(a) * R * .55), h * .007, sides=4, r2=h * .003), S('wooddk', base=.4, jit=.03))
    return P

def broadleaf(seed=1, h=20.0):
    """field oak: flared, slightly twisted trunk forking into 4-5 boughs (each with a side branch); every leaf mass
    sits on a bough end or between two of them, overlapping into one rounded crown, dark beneath, sunlit on top"""
    P = Prop('Oak%d' % seed); rng = random.Random(seed * 13)
    bark = lambda: S('wood', base=.33 + rng.uniform(-.03, .03), up=.06, jit=.04)
    fork = Vector((rng.uniform(-.5, .5), h * .4, rng.uniform(-.5, .5)))
    P.add(tube([Vector((0, -1.2, 0)), Vector((rng.uniform(-.4, .4), h * .2, rng.uniform(-.4, .4))), fork], [h * .065, h * .05, h * .042], sides=9, rough=.05, seed=seed), bark())
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(0, .5)
        P.add(log((math.cos(a) * h * .035, 1.2, math.sin(a) * h * .035), (math.cos(a) * h * .11, -.4, math.sin(a) * h * .11), h * .03, sides=5, r2=h * .008), bark())
    nb = rng.randint(4, 5); ends = []
    for k in range(nb):
        a = k * math.tau / nb + rng.uniform(-.25, .25); L = h * rng.uniform(.3, .38); up = rng.uniform(.5, .75)
        mid = fork + Vector((math.cos(a) * L * .45, L * up * .55, math.sin(a) * L * .45))
        end = fork + Vector((math.cos(a) * L, L * up, math.sin(a) * L))
        P.add(tube([fork, mid, end], [h * .032, h * .02, h * .01], sides=6), bark())
        side = mid + Vector((math.cos(a + 1.2) * L * .35, L * .3, math.sin(a + 1.2) * L * .35))
        P.add(tube([mid, side], [h * .012, h * .005], sides=5), bark())
        ends += [end, side]
    crown_c = fork + Vector((0, h * .3, 0))
    P.add(tube([fork, crown_c], [h * .03, h * .012], sides=6), bark())
    pts = ends + [crown_c, crown_c + Vector((0, h * .12, 0))]
    pts += [(ends[2 * k] + ends[2 * ((k + 1) % nb)]) / 2 + Vector((0, h * .06, 0)) for k in range(nb)]
    lo, hi = min(p.y for p in pts) - h * .2, max(p.y for p in pts) + h * .22
    for k, c in enumerate(pts):
        r = h * rng.uniform(.17, .22) * (1.15 if c.y > crown_c.y else 1.0)
        col = 'grass' if (k + seed) % 3 else 'pine'
        P.add(T(blob(r, seed * 31 + k, n=16, sq=.8), c),
              S(col, grad=(lo, hi, .14, .7), up=.18, jit=.03, vn=(5, seed + k, .08)))
    return P

def dead_tree(seed=1, h=16.0):
    """charred, leafless tree: forked trunk, snapped top, crooked branches and twigs"""
    P = Prop('DeadTree%d' % seed); rng = random.Random(seed)
    sh = lambda: S('wooddk', base=.32 + rng.uniform(-.04, .04), up=.08, jit=.04)
    top = Vector((rng.uniform(-.6, .6), h * .7, rng.uniform(-.6, .6)))
    P.add(tube([Vector((0, -1.2, 0)), Vector((.2, h * .3, -.1)), top], [h * .05, h * .036, h * .022], sides=8, rough=.08, seed=seed), sh())
    for k in range(3):
        a = k * math.tau / 3 + rng.uniform(0, .6)
        P.add(log((math.cos(a) * .3, .6, math.sin(a) * .3), (math.cos(a) * h * .09, -.4, math.sin(a) * h * .09), h * .03, sides=6, r2=h * .01), sh())
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(-.3, .3); y0 = h * rng.uniform(.38, .66)
        base = Vector((math.cos(a) * .3, y0, math.sin(a) * .3)); L = h * rng.uniform(.22, .36)
        mid = base + Vector((math.cos(a) * L * .55, L * .45, math.sin(a) * L * .55)); end = mid + Vector((math.cos(a + .4) * L * .45, L * .35, math.sin(a + .4) * L * .45))
        P.add(tube([base, mid, end], [h * .016, h * .01, h * .004], sides=5), sh())
        for j in range(2):
            b2 = mid.lerp(end, .3 + j * .4); e2 = b2 + Vector((rng.uniform(-1.5, 1.5), rng.uniform(.6, 1.6), rng.uniform(-1.5, 1.5)))
            P.add(tube([b2, e2], [h * .006, h * .002], sides=4), sh())
    P.add(T(spike(h * .022, h * .06, sides=6, shoulder=.1), top - Vector((0, .2, 0)), 0, 8, 0), S('wood', base=.55, jit=.04))
    return P

def bush(seed=1, r=2.0):
    P = Prop('Bush%d' % seed); rng = random.Random(seed)
    for k in range(5):
        a = k * math.tau / 5 + rng.uniform(0, .5); d = 0 if k == 0 else r * .6
        P.add(T(blob(r * rng.uniform(.55, .8), seed * 5 + k, n=16, sq=.75), (math.cos(a) * d, r * .45, math.sin(a) * d)), S('grass' if k % 2 else 'pine', grad=(0, r * 1.3, .3, .7), up=.2, jit=.06, seed=k))
    return P

def grass_tuft(seed=1):
    P = Prop('Tuft%d' % seed); rng = random.Random(seed)
    for k in range(6):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, .6)
        P.add(T(spike(.12, rng.uniform(.9, 1.7), sides=3, shoulder=.2), (math.cos(a) * d, -.1, math.sin(a) * d), rng.uniform(0, 120), rng.uniform(-22, 22), rng.uniform(-22, 22)), S('grass', base=.55, up=.1, jit=.08, seed=k))
    return P

def scorch(seed=1):
    """shallow scorched impact scar (modelled, smooth 32-sided), char centre, scattered stones + a splintered stake.
    Origin = centre; map carves no dish, the rim feathers into the grass tone"""
    P = Prop('Scorch%d' % seed); rng = random.Random(seed)
    prof = [(1.0, .02), (.9, .05), (.76, .07), (.6, .05), (.4, .03), (.2, .02), (0, .02)]
    bm = lathe(prof, n=32, a0=rng.uniform(0, 1))
    for v in bm.verts:
        r = math.hypot(v.co.x, v.co.z)
        if r > .3: a = math.atan2(v.co.z, v.co.x); v.co.y += .02 * math.sin(3 * a + seed) * r
    ud, ug = PAL.u('wooddk'), PAL.u('dirt')
    def tone(f):
        out = []
        for l in f.loops:
            r = math.hypot(l.vert.co.x, l.vert.co.z)
            out.append((ud, clamp(.14 + .2 * smooth((r - .35) / .55), .04, .96)) if r < .78 else (ug, .36))
        return out
    P.add(bm, tone, smooth=True)
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(.6, .95)
        P.add(T(rock((.07, .05, .06), seed=seed * 7 + k, n=8), (math.cos(a) * d, .1, math.sin(a) * d)), S('stoneg', base=.4, up=.2, jit=.05))
    return P

def well(seed=1):
    """courtyard well: ring of ashlar blocks with a coping ring, oak posts, a little slate roof, windlass + bucket"""
    P = Prop('Well'); rng = random.Random(seed); R = 2.6
    for c in range(3):
        n = 10
        for k in range(n):
            a = (k + .5 * (c % 2)) * math.tau / n
            stone(P, (math.cos(a) * R, .45 + c * .9, math.sin(a) * R), (1.55, .84, .8), -math.degrees(a) + 90, col='stone', base=.6, seed=seed * 9 + c * 10 + k)
    P.add(lathe([(R + .55, 2.6), (R + .6, 2.95), (R - .55, 2.95), (R - .6, 2.6)], n=20), S('stone', base=.7, up=.12, jit=.02))
    P.add(cyl(R - .5, .2, sides=16, y0=-.2), S('water', base=.25, jit=0))
    for sx in (-1, 1):
        P.add(bar((sx * (R + .2), -.4, 0), (sx * (R + .2), 6.2, 0), .42, .42, .04), S('wood', base=.42, jit=.03))
        P.add(bar((sx * (R + .2), 4.4, 0), (sx * R * .45, 5.9, 0), .25, .25, .03), S('wood', base=.4, jit=.03))
    for sz in (-1, 1):
        P.add(bar((-R - .9, 6.0, sz * .2), (R + .9, 6.0, sz * .2), .2, .2, .02), S('wood', base=.45, jit=.02))
        P.add(T(box((R * 2 + 2.2, .2, 2.0), .04), (0, 6.65, sz * 1.0), 0, sz * -30), S('slate', base=.5, up=.2, jit=.04))
    P.add(bar((-R - 1.1, 7.25, 0), (R + 1.1, 7.25, 0), .28, .28, .03), S('wood', base=.42, jit=.02))
    P.add(log((-R - .4, 4.2, 0), (R + .4, 4.2, 0), .35, sides=8), S('wood', base=.46, jit=.02))
    P.add(bar((R + .5, 4.2, 0), (R + .5, 3.2, -.2), .14, .14, .02), S('iron', base=.42, jit=0))
    P.add(bar((R + .5, 3.2, -.2), (R + 1.2, 3.2, -.2), .14, .14, .02), S('wood', base=.5, jit=0))
    for k in range(4): P.add(T(torus(.37, .05, n=10, sides=3), (-1.0 + k * .5, 4.2, 0), 0, 0, 90), S('straw', base=.45, jit=0))
    P.add(log((.2, 3.9, 0), (.2, 2.4, 0), .05, sides=4), S('straw', base=.45, jit=0))
    barrel(P, (.2, 1.6, 0), h=.85, r=.42, seed=seed)
    return P
