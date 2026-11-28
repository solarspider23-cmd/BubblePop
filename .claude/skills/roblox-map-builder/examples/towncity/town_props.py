# Maple Junction prop kit: a cheerful stylised modern town centre (street grid, square, clock-tower town hall, station).
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Machinery (Prop, S, materials, to_kit) from the grove module; helpers T, bar, lathe, torus, sag from the medieval
# example; colour = city_paint atlas (true 2D brick / stucco / siding / slate / asphalt / paving tiles). Every prop is new.
# Buildings are ONE parametric facade generator (building()): piers + spandrels around real window openings, recessed
# glass, frames, sills, lintels, string courses, cornice brackets, parapet + rooftop kit; shopfronts with blank sign
# fascias (GUI faces), striped awnings, display windows and recessed doors. Variants come from parameters + seeds.
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
for p in (os.path.join(SK, 'examples', 'whispering_grove'), os.path.join(SK, 'examples', 'medievalbattle'), os.path.join(SK, 'scripts')):
    sys.path.insert(0, p)
os.makedirs(os.path.join(HERE, 'previews'), exist_ok=True)
import bmesh
from mathutils import Vector, Matrix
import forest_props as G
import battle_props as B
from pro_lib import Palette, box, cyl, tube, hull, nz, clamp, ngon_prism, bevel, rock_pts, spike

PAL = Palette({
    'brick':  ('#6e2f22', '#b4583c', '#ec946c'),     # warm red brick
    'cream':  ('#a8916c', '#eadbbd', '#fffaf0'),     # cream stucco / stone trim
    'sage':   ('#4f6b52', '#8eae86', '#d6eacb'),     # sage clapboard
    'slate':  ('#2f3a4c', '#5e7088', '#a9b9cf'),     # slate blue panels / roofs
    'asph':   ('#26282e', '#40444d', '#6c717c'),     # asphalt
    'pave':   ('#8a857b', '#c8c1b2', '#f2ede2'),     # sidewalk slabs / plaza
    'glass':  ('#2c5c92', '#68a6dd', '#d8f3ff'),     # window glass
    'metal':  ('#1c2026', '#4a515e', '#a8b1bf'),     # iron, steel, dark trim
    'grass':  ('#2f6e25', '#5fae3e', '#b6e278'),
    'leaf':   ('#215e28', '#4ea43e', '#b8e66e'),
    'wood':   ('#45291a', '#85573a', '#cc9e6e'),
    'red':    ('#86141c', '#e3363c', '#ff9c8e'),     # accents: awnings, cars, hydrants
    'yellow': ('#b07400', '#f7c22a', '#fff3a8'),
    'teal':   ('#0a5f63', '#1fb0aa', '#a8f2e6'),     # also copper patina + fountain water
    'blue':   ('#163884', '#3b72d6', '#b0ccff'),
})
G.PAL = PAL; B.PAL = PAL
G.MATS.clear()
import city_paint as CP
CP.install(G, PAL)
G.GLOW.clear(); G.GLOW.update({'lamp': '#ffd88a', 'sigred': '#ff3b30', 'siggreen': '#3dff7a', 'sigamber': '#ffb21f',
                               'spray': '#d6fbff', 'walk': '#f2f6ff', 'clock': '#fff1c2'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 2.4, 'sigred': 2.2, 'siggreen': 2.2, 'sigamber': 2.0, 'spray': 1.2, 'walk': 1.4, 'clock': .9})
Prop, S = G.Prop, G.S
T, bar, lathe, torus, sag = B.T, B.bar, B.lathe, B.torus, B.sag
def lerp(a, b, t): return a + (b - a) * t
def V3(p): return Vector(p)

def fl(col, v=.62):
    u = PAL.u(col); return lambda f: [(u, clamp(v, .04, .96))] * len(f.loops)
def sh(col, v=.6, up=.12, jit=.03, seed=0): return S(col, base=v, up=up, jit=jit, seed=seed)

def slab(x0, x1, y0, y1, z0, z1, drop=()):
    """axis box between the given bounds; drop = faces to delete ('+x', '-x', '+y', '-y', '+z', '-z')"""
    bm = box((x1 - x0, y1 - y0, z1 - z0)); bmesh.ops.translate(bm, vec=Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), verts=bm.verts)
    if drop:
        kill = []
        bm.normal_update()
        for f in bm.faces:
            n = f.normal
            for d in drop:
                ax = 'xyz'.index(d[1]); s = 1 if d[0] == '+' else -1
                if n[ax] * s > .9: kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
    return bm

def add(P, bm, col, v=.6, up=.1, jit=.02, smooth=False, seed=0):
    P.add(bm, S(col, base=v, up=up, jit=jit, seed=seed), smooth=smooth)

def ball(r, u=10, v=6):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r); return bm

def blob(r, seed, n=30, sq=.8): return hull(rock_pts((r, r * sq, r), n=n, seed=seed))

def ring_frame(w, h, t, d, front_only=False):
    """flat rectangular frame ring in the XY plane, centred, inner w x h, bar width t, depth d (z -d/2..d/2), no back"""
    bm = bmesh.new()
    def rect(hw, hh, z): return [bm.verts.new(p) for p in ((-hw, -hh, z), (hw, -hh, z), (hw, hh, z), (-hw, hh, z))]
    zf, zb = -d / 2, d / 2
    I0, O0, I1, O1 = rect(w / 2, h / 2, zf), rect(w / 2 + t, h / 2 + t, zf), rect(w / 2, h / 2, zb), rect(w / 2 + t, h / 2 + t, zb)
    want = []
    for i in range(4):
        j = (i + 1) % 4
        want.append((bm.faces.new((I0[i], O0[i], O0[j], I0[j])), 'front'))
        if front_only: continue
        want.append((bm.faces.new((O0[i], O1[i], O1[j], O0[j])), 'out'))
        want.append((bm.faces.new((I1[i], I0[i], I0[j], I1[j])), 'in'))
    bm.normal_update()
    for f, k in want:
        c = f.calc_center_median(); n = f.normal
        if k == 'front': bad = n.z > 0
        elif k == 'out': bad = n.dot(V3((c.x, c.y, 0))) < 0
        else: bad = n.dot(V3((c.x, c.y, 0))) > 0
        if bad: f.normal_flip()
    return bm

def quad(pts):
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in pts]); return bm

def front_quad(x0, x1, y0, y1, z):
    """a single quad facing -Z at depth z"""
    return quad([(x0, y0, z), (x0, y1, z), (x1, y1, z), (x1, y0, z)])

def holed_front(P, x0, x1, y0, y1, holes, zf, mat, v=.66):
    """front wall layer (outer face at zf, WALL_T thick, back face dropped) with rectangular openings [(xa, xb, ya, yb)]"""
    xs = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    ys = sorted({y0, y1} | {h[2] for h in holes} | {h[3] for h in holes})
    for xa, xb in zip(xs, xs[1:]):
        ya0 = None
        for ya, yb in zip(ys, ys[1:]):
            xm, ym = (xa + xb) / 2, (ya + yb) / 2
            hole = any(h[0] < xm < h[1] and h[2] < ym < h[3] for h in holes)
            if not hole and ya0 is None: ya0 = ya
            if hole and ya0 is not None:
                add(P, slab(xa, xb, ya0, ya, zf, zf + WALL_T, drop=('+z',)), mat, v, up=0); ya0 = None
        if ya0 is not None: add(P, slab(xa, xb, ya0, ys[-1], zf, zf + WALL_T, drop=('+z',)), mat, v, up=0)

# ------------------------------------------------------------------ small parts reused inside props
def ac_unit(P, pos, yaw=0.0, s=1.0):
    """rooftop / wall AC: cream casing on feet, fan grille ring + hub on top, side louvres"""
    L = lambda bm: T(bm, pos, yaw)
    add(P, L(T(box((4 * s, 2.4 * s, 3 * s), .15 * s), (0, 1.5 * s, 0))), 'cream', .72)
    for sx in (-1, 1): add(P, L(T(box((.4 * s, .4 * s, 3.2 * s)), (sx * 1.6 * s, .2 * s, 0))), 'metal', .35)
    add(P, L(T(torus(1.0 * s, .12 * s, n=8, sides=3), (-.6 * s, 2.72 * s, 0))), 'metal', .4)
    add(P, L(T(cyl(.92 * s, .06 * s, sides=12, y0=2.66 * s), (-.6 * s, 0, 0))), 'metal', .2)
    add(P, L(T(cyl(.3 * s, .14 * s, sides=8, y0=2.68 * s), (-.6 * s, 0, 0))), 'metal', .6)
    for k in range(4): add(P, L(T(box((.12 * s, 1.4 * s, .08 * s)), (1.1 * s + k * .28 * s, 1.5 * s, -1.53 * s))), 'metal', .45)

def water_tank(P, pos, s=1.0):
    """classic timber rooftop water tank on a steel stand: staves, iron hoops, conical cap, ladder"""
    x, y, z = pos
    for a in range(4):
        ang = a * math.tau / 4 + math.pi / 4
        px, pz = math.cos(ang) * 2.6 * s, math.sin(ang) * 2.6 * s
        add(P, T(box((.5 * s, 5 * s, .5 * s)), (x + px, y + 2.5 * s, z + pz)), 'metal', .35)
    add(P, T(box((6.4 * s, .5 * s, 6.4 * s)), (x, y + 5.1 * s, z)), 'metal', .4)
    P.add(T(cyl(3.2 * s, 6.5 * s, sides=10, y0=5.3 * s), (x, y, z)), S('wood', grad=(y + 5.3 * s, y + 11.8 * s, .38, .68), up=.0), smooth=True)
    for hy in (6.8, 10.2):
        add(P, T(torus(3.25 * s, .1 * s, n=10, sides=3), (x, y + hy * s, z)), 'metal', .3)
    add(P, T(cyl(3.5 * s, 2.6 * s, sides=10, r2=.25 * s, y0=11.8 * s), (x, y, z)), 'slate', .55, smooth=True)
    add(P, T(ball(.4 * s, 8, 4), (x, y + 14.5 * s, z)), 'metal', .5)
    for k in range(6):
        add(P, T(box((1.2 * s, .14 * s, .14 * s)), (x, y + (5.8 + k * 1.0) * s, z - 3.35 * s)), 'metal', .5)
    for sx in (-1, 1): add(P, T(box((.14 * s, 6.4 * s, .14 * s)), (x + sx * .6 * s, y + 8.4 * s, z - 3.35 * s)), 'metal', .5)

def antenna(P, pos, h=9.0):
    x, y, z = pos
    add(P, T(cyl(.6, .5, sides=8, y0=0), (x, y, z)), 'metal', .35)
    add(P, T(cyl(.14, h, sides=6, y0=.5, r2=.08), (x, y, z)), 'metal', .55)
    for k, L in enumerate((3.2, 2.4, 1.6)):
        add(P, T(box((L, .1, .1)), (x, y + h * (.45 + k * .17), z)), 'metal', .55)
    add(P, T(box((.1, .1, 2.0)), (x, y + h * .62, z)), 'metal', .5)
    add(P, T(ball(.22, 6, 4), (x, y + h + .5, z)), 'red', .6)

def roof_shed(P, pos, w=8.0, d=6.0, h=6.0, col='cream'):
    """stair bulkhead: small box room with a door, coping, vent pipe"""
    x, y, z = pos
    add(P, T(box((w, h, d), .1), (x, y + h / 2, z)), col, .62)
    add(P, T(box((w + .6, .5, d + .6), .1), (x, y + h + .2, z)), 'cream', .78)
    add(P, T(box((2.6, 4.4, .2)), (x - w * .2, y + 2.2, z - d / 2 - .05)), 'slate', .38)
    add(P, T(box((.3, .3, .3)), (x - w * .2 + .9, y + 2.2, z - d / 2 - .2)), 'metal', .7)
    add(P, T(cyl(.35, 2.6, sides=8, y0=h), (x + w * .3, y, z + d * .2)), 'metal', .45)
    add(P, T(cyl(.55, .4, sides=8, y0=h + 2.6), (x + w * .3, y, z + d * .2)), 'metal', .35)

def skylight(P, pos, w=5.0, d=4.0):
    x, y, z = pos
    add(P, T(box((w + .6, .8, d + .6), .1), (x, y + .4, z)), 'metal', .4)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-w / 2, .8, -d / 2), (w / 2, .8, -d / 2), (w / 2, .8, d / 2), (-w / 2, .8, d / 2), (0, 2.0, -d / 2), (0, 2.0, d / 2))]
    for f in ((vs[0], vs[4], vs[5], vs[3]), (vs[1], vs[2], vs[5], vs[4]), (vs[0], vs[1], vs[4]), (vs[3], vs[5], vs[2])):
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(T(bm, (x, y, z)), S('glass', base=.62, up=.25, jit=.0))
    add(P, T(box((.2, .2, d + .2)), (x, y + 2.0, z)), 'metal', .5)

def flower(P, pos, col, r=.42, tilt=0.0, n=None):
    """a flower head: one 5-petal star face + a centre face, facing n (default: up, tipped `tilt` toward -Z),
    lifted .08 off whatever it sits on (2 faces, ~11 tris)"""
    n = V3(n if n is not None else (0, 1, -tilt)).normalized()
    R = V3((0, 1, 0)).rotation_difference(n).to_matrix()
    pts = [(math.cos(k * math.tau / 10) * (r if k % 2 == 0 else r * .45), math.sin(k * math.tau / 10) * (r if k % 2 == 0 else r * .45)) for k in range(10)]
    o = V3(pos) + n * .08
    bm = bmesh.new(); bm.faces.new([bm.verts.new(o + R @ V3((x, 0, z))) for x, z in reversed(pts)])
    add(P, bm, col, .72, up=0, jit=0)
    bm = bmesh.new(); bm.faces.new([bm.verts.new(o + R @ V3((math.cos(k * math.tau / 5) * r * .3, .05, math.sin(k * math.tau / 5) * r * .3))) for k in range(4, -1, -1)])
    add(P, bm, 'yellow' if col != 'yellow' else 'cream', .85, up=0, jit=0)

def flower_box(P, pos, w, yaw=0.0, cols=('red', 'yellow')):
    L = lambda bm: T(bm, pos, yaw)
    add(P, L(T(box((w, .9, 1.1), .08), (0, .45, -.55))), 'wood', .45)
    rng = random.Random(int(w * 10 + pos[1]))
    n = max(2, int(w / 1.1))
    for k in range(n):
        add(P, L(T(blob(.5, k + 3, n=8, sq=.8), (-w / 2 + .55 + k * (w - 1.1) / max(1, n - 1), 1.05, -.55))), 'leaf', .55)
        flower(P, tuple(V3(pos) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ V3((-w / 2 + .55 + k * (w - 1.1) / max(1, n - 1) + .2, 1.45, -.85))), cols[k % 2], .36, .4)

# ------------------------------------------------------------------ windows
def window_unit(P, x, y0, ww, wh, zf, kind, col_frame='cream', sill_col='cream', shutters=None, flowers=False, wall_col='brick'):
    """dressing for ONE opening in a front wall whose outer face is at z = zf (front = -Z), opening x-ww/2..x+ww/2,
    y0..y0+wh. The wall pieces around the hole are made by the caller. Glass is recessed 0.55."""
    zg = zf + .55
    if kind == 'arch':
        rh = ww / 2; ys = y0 + wh - rh
        pts = [(x - ww / 2, y0), (x + ww / 2, y0), (x + ww / 2, ys)] + [(x + math.cos(math.pi * k / 8) * rh, ys + math.sin(math.pi * k / 8) * rh) for k in range(1, 8)] + [(x - ww / 2, ys)]
        P.add(quad([(px, py, zg) for px, py in reversed(pts)]), S('glass', grad=(y0, y0 + wh, .45, .88), up=0, jit=0))
        for side in (-1, 1):                                  # fill the hole corners above the arch with wall
            arc_q = [(x + side * math.cos(math.pi * k / 8) * rh, ys + math.sin(math.pi * k / 8) * rh) for k in range(0, 5)]
            poly = [(x + side * ww / 2, y0 + wh)] + list(reversed(arc_q))
            bm = bmesh.new()
            Fv = [bm.verts.new((px, py, zf)) for px, py in poly]
            f = bm.faces.new(Fv); f.normal_update()
            if f.normal.z > 0: f.normal_flip()
            add(P, bm, wall_col, .66, up=0, jit=0)
            bm = bmesh.new()                                   # arch reveal (wall thickness along the arc)
            for (ax, ay), (bx_, by_) in zip(arc_q, arc_q[1:]):
                bm.faces.new([bm.verts.new(p) for p in ((ax, ay, zf), (bx_, by_, zf), (bx_, by_, zg), (ax, ay, zg))])
            bm.normal_update()
            for f in bm.faces:
                c = f.calc_center_median()
                if f.normal.dot(V3((x, ys, c.z)) - c) < 0: f.normal_flip()
            add(P, bm, wall_col, .5, up=0, jit=0)
        arcp = [V3((x + math.cos(math.pi * k / 8) * (rh + .3), ys + math.sin(math.pi * k / 8) * (rh + .3), zf - .12)) for k in range(9)]
        add(P, tube(arcp, .32, sides=4, rot0=math.pi / 4), col_frame, .74)
        add(P, T(box((.9, .9, .5), .06), (x, ys + rh + .45, zf - .2)), col_frame, .82)            # keystone
        add(P, T(box((.16, wh - rh, .16)), (x, y0 + (wh - rh) / 2, zg - .1)), 'cream', .85)        # mullion
        add(P, T(box((ww, .16, .16)), (x, ys, zg - .1)), 'cream', .85)
    else:
        P.add(front_quad(x - ww / 2, x + ww / 2, y0, y0 + wh, zg), S('glass', grad=(y0, y0 + wh, .45, .9), up=0, jit=0))
        add(P, T(ring_frame(ww - .3, wh - .3, .3, .16, True), (x, y0 + wh / 2, zg - .1)), col_frame, .82)
        if kind == 'tall':
            add(P, T(box((ww - .3, .2, .2)), (x, y0 + wh * .55, zg - .12)), col_frame, .84)
            add(P, T(box((ww + .9, .55, .6)), (x, y0 + wh + .28, zf - .18)), 'cream', .8)    # lintel
        elif kind == 'square':
            for k in (1, 2):
                add(P, T(box((.2, wh - .3, .2)), (x - ww / 2 + ww * k / 3, y0 + wh / 2, zg - .12)), col_frame, .84)
        elif kind == 'band':
            add(P, T(box((.22, wh - .3, .2)), (x, y0 + wh / 2, zg - .12)), col_frame, .5)
    if kind != 'band':
        add(P, T(box((ww + .8, .38, .9)), (x, y0 - .19, zf - .3)), sill_col, .78)              # sill
    if shutters:
        for sx in (-1, 1):
            sx0 = x + sx * (ww / 2 + .75)
            add(P, T(box((1.3, wh, .22)), (sx0, y0 + wh / 2, zf - .14)), shutters, .5)
            for k in range(1, 4): add(P, T(box((1.1, .1, .1)), (sx0, y0 + wh * k / 4, zf - .28)), shutters, .36)
    if flowers: flower_box(P, (x, y0 - .4, zf - .3), ww + .4)

def deco_window(P, face, a, y0, ww, wh, out, col_frame='cream'):
    """flat 'decal' window on a plain side / back wall: glass quad + frame ring set 0.08 proud; face = '+x' | '-x' | '+z'"""
    bm_g = front_quad(-ww / 2, ww / 2, 0, wh, -.02)
    fr = T(ring_frame(ww - .1, wh - .1, .28, .14, True), (0, wh / 2, -.08))
    sl = slab(-ww / 2 - .3, ww / 2 + .3, -.3, 0, -.45, .05, drop=('+z', '-y'))
    yaw = {'+x': -90, '-x': 90, '+z': 180, '-z': 0}[face]
    for bm, col, v in ((bm_g, 'glass', None), (fr, col_frame, .8), (sl, 'cream', .75)):
        bm = T(bm, (0, 0, 0), yaw)
        if face == '+x': pos = (out, y0, a)
        elif face == '-x': pos = (-out, y0, a)
        elif face == '+z': pos = (a, y0, out)
        else: pos = (a, y0, -out)
        bm = T(bm, pos)
        if v is None: P.add(bm, S('glass', grad=(y0, y0 + wh, .3, .7), up=0, jit=0))
        else: add(P, bm, col, v, up=.05, jit=0)

# ------------------------------------------------------------------ shopfront
def shopfront(P, w, zf, gf, accent, kind='shop', door_side=1, awning=True, wall='brick', seed=0):
    """ground floor front: pilasters, bulkhead panels, display windows with mullions, recessed glass door, BLANK
    sign fascia (GUI face) and a striped awning. Returns the sign centre (x, y, z) and size."""
    rng = random.Random(seed)
    hw = w / 2; pil = 1.6; sign_y0, sign_y1 = gf - 3.4, gf - .6
    add(P, slab(-hw, hw, gf - .6, gf, zf - .6, zf + .6), 'cream', .8, up=.05)                      # cornice over shop
    add(P, slab(-hw - .2, hw + .2, gf - .2, gf + .4, zf - .9, zf + .3), 'cream', .86, up=.05)
    for x in (-hw + pil / 2, hw - pil / 2):                                                           # end pilasters
        add(P, slab(x - pil / 2, x + pil / 2, -.6, gf - .6, zf - .35, zf + .6), wall, .66, up=0)
        add(P, slab(x - pil / 2 - .15, x + pil / 2 + .15, -.6, 1.4, zf - .5, zf + .6), 'cream', .7)
        add(P, slab(x - pil / 2 - .15, x + pil / 2 + .15, sign_y0 - .6, sign_y0, zf - .5, zf + .6), 'cream', .82)
    # fascia: blank sign panel framed in the accent colour (GUI goes on the panel)
    add(P, slab(-hw + pil, hw - pil, sign_y0, sign_y1, zf - .1, zf + .6), accent, .32, up=0)
    add(P, slab(-hw + pil + .5, hw - pil - .5, sign_y0 + .45, sign_y1 - .45, zf - .3, zf - .05), 'cream', .9, up=0)
    sign = ((0.0, (sign_y0 + sign_y1) / 2, zf - .32), (w - 2 * pil - 1, sign_y1 - sign_y0 - .9))
    # glazing zone below the sign: bulkheads, display glass, door
    gx0, gx1 = -hw + pil, hw - pil
    dw = 4.6; dx = (gx1 - dw / 2 - .5) if door_side > 0 else (gx0 + dw / 2 + .5)
    if kind == 'wide': dx = 0.0
    yb = 2.6; yt = sign_y0 - .4
    add(P, slab(gx0, gx1, yt, sign_y0, zf + .1, zf + .6), 'metal', .28, up=0)                           # transom bar
    # display windows (left and right of the door)
    segs = [(gx0, dx - dw / 2), (dx + dw / 2, gx1)]
    for a, b in segs:
        if b - a < 1.0: continue
        add(P, slab(a, b, -.6, yb, zf + .1, zf + .6), accent, .52, up=0)                               # bulkhead
        add(P, slab(a + .4, b - .4, .4, yb - .5, zf, zf + .12), accent, .7, up=0)                       # raised panel
        add(P, slab(a, b, yb, yb + .4, zf - .1, zf + .6), 'cream', .84)                                   # display sill
        P.add(front_quad(a, b, yb + .4, yt, zf + .9), S('glass', grad=(yb, yt, .34, .78), up=0, jit=0))
        n = max(1, int((b - a) / 5.5))
        for k in range(n + 1):
            x = a + (b - a) * k / n
            add(P, slab(x - .2, x + .2, yb + .4, yt, zf + .3, zf + .8), 'metal', .32, up=0)
        add(P, slab(a, b, yt - .25, yt, zf + .3, zf + .8), 'metal', .32, up=0)
    # door: recessed 1.6, glass door with kick plate + push bar, side reveals
    zd = zf + 1.6
    for sx in (-1, 1):
        add(P, slab(dx + sx * dw / 2 - (.3 if sx > 0 else 0), dx + sx * dw / 2 + (0 if sx > 0 else .3), -.6, yt, zf + .1, zd), 'cream', .7, up=0)
    add(P, slab(dx - dw / 2, dx + dw / 2, yt - .5, yt, zf + .1, zd), 'cream', .74, up=0)
    add(P, slab(dx - dw / 2 + .1, dx + dw / 2 - .1, -.05, .1, zf + .1, zd), 'pave', .3, up=0)            # step
    add(P, slab(dx - dw / 2 + .3, dx + dw / 2 - .3, .1, yt - .5, zd, zd + .3), 'metal', .3, up=0)        # door frame
    P.add(front_quad(dx - dw / 2 + .7, dx + dw / 2 - .7, 1.4, yt - .9, zd - .02), S('glass', grad=(1, yt, .3, .7), up=0, jit=0))
    add(P, slab(dx - dw / 2 + .7, dx + dw / 2 - .7, .3, 1.4, zd - .12, zd), accent, .55, up=0)
    add(P, slab(dx - dw / 2 + 1.0, dx + dw / 2 - 1.0, 3.6, 3.9, zd - .35, zd - .1), 'yellow', .75, up=0)
    if awning:
        awning_band(P, -hw + pil + .3, hw - pil - .3, sign_y0 - .1, zf, 4.2, 1.6, accent)
    return sign

def awning_band(P, x0, x1, y, zf, depth, drop, col):
    """sloped striped awning (accent / cream stripes), side cheeks, scalloped valance, iron brackets"""
    n = max(3, int((x1 - x0) / 1.9)); n += n % 2 == 0; w = (x1 - x0) / n
    for i in range(n):
        c = col if i % 2 == 0 else 'cream'; xa = x0 + w * i
        q = [V3((xa, y, zf)), V3((xa + w, y, zf)), V3((xa + w, y - drop, zf - depth)), V3((xa, y - drop, zf - depth))]
        bm = bmesh.new(); A = [bm.verts.new(p) for p in q]; Bq = [bm.verts.new(p + V3((0, -.14, 0))) for p in q]
        bm.faces.new(A[::-1]); bm.faces.new(Bq); bm.faces.new((A[2], A[3], Bq[3], Bq[2]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        add(P, bm, c, .62 if c == col else .86, up=.15, jit=0)
        pts = [(xa + w / 2 + math.cos(math.pi + math.pi * k / 4) * w * .5, -math.sin(math.pi + math.pi * k / 4) * w * .36) for k in range(5)]
        bm2 = bmesh.new()
        Fv = [bm2.verts.new((px, y - drop - .1 - py, zf - depth - .03)) for px, py in pts]
        Bv = [bm2.verts.new((px, y - drop - .1 - py, zf - depth + .09)) for px, py in pts]
        bm2.faces.new(Fv); bm2.faces.new(Bv[::-1])
        for k in range(len(pts)):
            j = (k + 1) % len(pts); bm2.faces.new((Fv[k], Fv[j], Bv[j], Bv[k]))
        bmesh.ops.recalc_face_normals(bm2, faces=list(bm2.faces))
        add(P, bm2, c, .55 if c == col else .8, up=0, jit=0)
    add(P, tube([V3((x0, y - drop - .1, zf - depth)), V3((x1, y - drop - .1, zf - depth))], .1, sides=5), 'metal', .35)
    for xx in (x0 + .2, x1 - .2):
        add(P, bar((xx, y - drop - .1, zf - depth + .1), (xx, y - 1.9, zf), .16, .16, 0), 'metal', .35)

# ------------------------------------------------------------------ the building generator
WALL_T = .6
def building(name, w=30.0, d=28.0, floors=3, mat='brick', gf=13.0, fh=10.0, ground='shop', accent='red', win='tall',
             bay=6.0, wfrac=.48, whf=.56, seed=1, roof=('ac', 'tank'), sides='windows', back='windows', quoins=None,
             shutters=None, flowers=0, cornice=True, parapet=2.6, crown=None, door_side=1, awning=True, balconies=False,
             trim='cream', fire=False, lite=False):
    """front facade at z = -d/2. Returns Prop with .sign (centre, size) for the blank fascia and .roof_y."""
    rng = random.Random(seed); P = Prop(name)
    if lite:                                                   # cheaper back-row variant: same massing, less trim
        flowers = 0; quoins = None; shutters = None; balconies = False; roof = roof[:1]; cornice = 'plain'
    hw, hd = w / 2, d / 2; zf = -hd
    H = gf + floors * fh
    # core volume (hidden behind the walls; dark interior seen through glass edges)
    add(P, slab(-hw + .5, hw - .5, -.6, H, -hd + 4.0, hd - .5, drop=('-y',)), 'metal', .25, up=0)
    # plinth / sidewalls / back wall as plain slabs (tile-clipped brick / siding)
    add(P, slab(-hw, -hw + WALL_T, -.6, H, -hd, hd, drop=('+x',)), mat, .66, up=0)
    add(P, slab(hw - WALL_T, hw, -.6, H, -hd, hd, drop=('-x',)), mat, .66, up=0)
    add(P, slab(-hw, hw, -.6, H, hd - WALL_T, hd, drop=('-z',)), mat, .62, up=0)
    # ground floor
    sign = None
    if ground in ('shop', 'wide'):
        sign = shopfront(P, w, zf, gf, accent, kind=ground, door_side=door_side, awning=awning, wall=mat, seed=seed)
    elif ground == 'door':                                                      # residential: stoop, door, two windows
        holes = [(-2.2, 2.2, 1.1, 8.6)] + [(sx * hw * .55 - 2.1, sx * hw * .55 + 2.1, 3.0, 9.0) for sx in (-1, 1)]
        holed_front(P, -hw, hw, -.6, gf, holes, zf, mat)
        add(P, slab(-hw, hw, -.6, 1.6, zf - .3, zf + .2), 'cream', .55)
        add(P, slab(-3, 3, -.6, .5, zf - 3.4, zf), 'cream', .7)                                         # stoop
        add(P, slab(-3, 3, .5, 1.1, zf - 2.2, zf), 'cream', .76)
        add(P, slab(-2.2, 2.2, 1.1, 8.6, zf + .4, zf + .6), accent, .45, up=0)                           # door leaf
        add(P, slab(-1.6, 1.6, 2.0, 7.8, zf + .25, zf + .4), accent, .62, up=0)
        P.add(front_quad(-1.0, 1.0, 5.6, 7.4, zf + .22), S('glass', grad=(5.6, 7.4, .3, .7), up=0, jit=0))
        add(P, T(ball(.22, 6, 4), (1.4, 4.6, zf + .1)), 'yellow', .8)
        add(P, T(ring_frame(4.4, 7.5, .35, .3), (0, 1.1 + 7.5 / 2, zf - .1)), 'cream', .82)
        add(P, slab(-3.2, 3.2, 8.9, 9.5, zf - 2.6, zf + .1), 'cream', .82)                              # door canopy
        for sx in (-1, 1):
            add(P, bar((sx * 2.9, 8.9, zf - 2.4), (sx * 2.9, 6.4, zf), .2, .2, 0), 'metal', .35)
            window_unit(P, sx * hw * .55, 3.0, 4.2, 6.0, zf, 'tall', wall_col=mat, shutters=shutters)
    elif ground == 'garage':
        add(P, slab(-hw, hw, gf - 1.5, gf, zf, zf + WALL_T, drop=('+z',)), mat, .6, up=0)
    # ---- upper floors: piers (full height) + spandrels around each window column
    nb = max(1, int(w / bay)); bw = w / nb
    wx = [-hw + bw * (i + .5) for i in range(nb)]; ww = bw * wfrac; wh = fh * whf
    y_s = gf; y_e = H
    edges = [-hw] + [e for x in wx for e in (x - ww / 2, x + ww / 2)] + [hw]
    for i in range(0, len(edges), 2):                                                  # piers between window columns
        a, b = edges[i], edges[i + 1]
        if b - a > .01: add(P, slab(a, b, y_s, y_e, zf, zf + WALL_T, drop=('+z', '-y', '+y') + (('-x',) if a <= -hw + .01 else ()) + (('+x',) if b >= hw - .01 else ())), mat, .66, up=0)
    sill = fh * .22
    for x in wx:
        ys = [y_s] + [v for f in range(floors) for v in (gf + f * fh + sill, gf + f * fh + sill + wh)] + [y_e]
        for k in range(0, len(ys), 2):
            if ys[k + 1] - ys[k] > .01:
                add(P, slab(x - ww / 2, x + ww / 2, ys[k], ys[k + 1], zf, zf + WALL_T, drop=('+z', '-x', '+x') + (('+y',) if k == len(ys) - 2 else ()) + (('-y',) if k == 0 else ())), mat, .66, up=0)
        for f in range(floors):
            kind = win if not (win == 'arch' and f < floors - 1 and floors > 2) else 'tall'
            if win == 'archtop': kind = 'arch' if f == floors - 1 else 'tall'
            window_unit(P, x, gf + f * fh + sill, ww, wh, zf, kind, col_frame=trim if mat != 'cream' else 'cream',
                        shutters=shutters, flowers=(flowers and f == 0 and kind != 'band'), wall_col=mat)
            if balconies and f % 2 == 0 and abs(x) < hw - bw:
                by = gf + f * fh + sill - .2
                add(P, slab(x - ww / 2 - 1.2, x + ww / 2 + 1.2, by - .5, by, zf - 3.0, zf), 'cream', .7)
                for k in range(6):
                    xx = x - ww / 2 - 1.0 + k * (ww + 2.0) / 5
                    add(P, slab(xx - .1, xx + .1, by, by + 3.0, zf - 2.9, zf - 2.7), 'metal', .35, up=0)
                add(P, slab(x - ww / 2 - 1.2, x + ww / 2 + 1.2, by + 3.0, by + 3.3, zf - 3.0, zf - 2.6), 'metal', .4, up=0)
                for sx in (-1, 1): add(P, slab(x + sx * (ww / 2 + 1.1) - .1, x + sx * (ww / 2 + 1.1) + .1, by, by + 3.0, zf - 2.9, zf), 'metal', .35, up=0)
    # string courses at each floor line
    for f in range(1, floors):
        add(P, slab(-hw - .15, hw + .15, gf + f * fh - .3, gf + f * fh + .2, zf - .35, zf + .2), trim, .78, up=.05)
    if quoins:
        for sx in (-1, 1):
            for k in range(int((H - gf) / 2.2)):
                yy = gf + .2 + k * 2.2; wq = 2.2 if k % 2 == 0 else 1.4
                x0 = sx * hw - (wq if sx > 0 else 0); x1 = x0 + wq
                add(P, slab(x0, x1, yy, yy + 1.8, zf - .25, zf + .2), quoins, .8, up=0)
    # cornice: frieze band, brackets per bay, overhanging cap
    top = H
    if cornice:
        add(P, slab(-hw - .2, hw + .2, top - 1.6, top - .4, zf - .3, zf + .3), trim, .7, up=0)
        for i in range(nb + 1 if cornice is True else 0):
            x = -hw + bw * i
            for xx in ((x + .9,) if i == 0 else (x - .9,) if i == nb else (x - .9, x + .9)):
                add(P, T(box((.7, 1.4, 1.2)), (xx, top - .5, zf - .6)), trim, .82)
        add(P, slab(-hw - .9, hw + .9, top + .2, top + .9, zf - 1.5, zf + .3), trim, .86, up=.05)
        add(P, slab(-hw - .5, hw + .5, top - .4, top + .2, zf - 1.1, zf + .3), trim, .76, up=.05)
    # parapet + coping on all four sides, roof deck
    if parapet > 0:
        for (x0, x1, z0, z1) in ((-hw, hw, -hd, -hd + .8), (-hw, hw, hd - .8, hd), (-hw, -hw + .8, -hd, hd), (hw - .8, hw, -hd, hd)):
            add(P, slab(x0, x1, top, top + parapet, z0, z1, drop=('-y', '+y')), mat, .6, up=0)
            add(P, slab(x0 - .25, x1 + .25, top + parapet, top + parapet + .45, z0 - .25, z1 + .25), trim, .82, up=.05)
    add(P, slab(-hw + .8, hw - .8, top - .2, top + .3, -hd + .8, hd - .8, drop=('-y',)), 'slate', .3, up=0)
    if crown == 'pediment':                                                       # stepped front parapet with a disc
        add(P, slab(-w * .18, w * .18, top + parapet, top + parapet + 2.6, zf, zf + .8), mat, .6, up=0)
        add(P, slab(-w * .18 - .3, w * .18 + .3, top + parapet + 2.6, top + parapet + 3.1, zf - .3, zf + 1.1), trim, .82)
        add(P, T(cyl(1.2, .4, sides=14), (0, top + parapet + 1.3, zf - .2), 0, 90), trim, .78, smooth=True)
    elif crown == 'gable':
        gpts = [(-w * .22, 0), (w * .22, 0), (0, 4.2)]
        bm = bmesh.new(); Fv = [bm.verts.new((x, top + parapet + y, zf)) for x, y in gpts]; Bv = [bm.verts.new((x, top + parapet + y, zf + .8)) for x, y in gpts]
        bm.faces.new(Fv[::-1]); bm.faces.new(Bv)
        for k in range(3): j = (k + 1) % 3; bm.faces.new((Fv[k], Fv[j], Bv[j], Bv[k]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, mat, .6, up=0)
        add(P, T(box((1.4, 1.4, .6), .1), (0, top + parapet + 1.6, zf - .1), 0, 0, 45), trim, .82)
    # sides + back: decal windows per floor
    nside = max(1, int(d / 9))
    for f in range(floors):
        y0 = gf + f * fh + sill
        for k in range(nside):
            a = -hd + d * (k + .5) / nside
            if sides in ('windows', 'left'): deco_window(P, '-x', a, y0, 3.6, wh, hw + .02)
            if sides in ('windows', 'right'): deco_window(P, '+x', a, y0, 3.6, wh, hw + .02)
        if back == 'windows' or back == 'fire':
            for k in range(nb):
                deco_window(P, '+z', wx[k], y0, ww * .9, wh, hd + .02)
    if back == 'fire' or fire:
        fire_escape(P, wx, gf, fh, floors, hd + .02, ww)
    # rooftop kit
    ry = top + .3
    for item in roof:
        if item == 'ac':
            for k in range(rng.randint(1, 2)):
                ac_unit(P, (rng.uniform(-hw + 4, hw - 6), ry, rng.uniform(-hd + 4, hd - 6)), rng.choice((0, 90)), 1.0)
        elif item == 'tank': water_tank(P, (hw * .45, ry, hd * .35), .9)
        elif item == 'antenna': antenna(P, (-hw * .5, ry, hd * .4), rng.uniform(8, 12))
        elif item == 'shed': roof_shed(P, (-hw * .35, ry, hd * .25), 8, 6, 6, 'cream' if mat != 'cream' else 'sage')
        elif item == 'sky': skylight(P, (hw * .2, ry, -hd * .15))
    P.sign = sign; P.roof_y = top; P.H = H; P.w = w; P.d = d
    return P

def fire_escape(P, wx, gf, fh, floors, zb, ww):
    """iron fire escape on the back wall (+Z): landing per floor at each window pair, railings, zig-zag stairs, drop ladder"""
    x0 = min(wx) - ww / 2 - 1; x1 = (sorted(wx)[1] if len(wx) > 1 else wx[0]) + ww / 2 + 1
    for f in range(floors):
        y = gf + f * fh + 1.6
        add(P, slab(x0, x1, y - .3, y, zb, zb + 3.6), 'metal', .35, up=.2)
        add(P, slab(x0, x1, y + 3.2, y + 3.45, zb + 3.4, zb + 3.6), 'metal', .45, up=0)
        n = int((x1 - x0) / 1.2)
        for k in range(n + 1):
            xx = x0 + (x1 - x0) * k / n
            add(P, slab(xx - .07, xx + .07, y, y + 3.2, zb + 3.45, zb + 3.55), 'metal', .4, up=0)
        for xx in (x0, x1): add(P, slab(xx - .1, xx + .1, y, y + 3.4, zb, zb + 3.6), 'metal', .4, up=0)
        if f > 0:                                                               # stair from the landing below
            ya = y - fh; a = V3((x1 - 1.2, ya, zb + 2.6)); b = V3((x0 + 1.2, y, zb + 2.6))
            add(P, bar(a, b, 1.6, .25, 0), 'metal', .32)
            steps = 7
            for k in range(1, steps):
                p = a.lerp(b, k / steps)
                add(P, T(box((.25, .12, 1.7)), (p.x, p.y + .1, p.z)), 'metal', .5)
            for dz in (-.85, .85):
                add(P, tube([a + V3((0, 3, dz)), b + V3((0, 3, dz))], .07, sides=4), 'metal', .45)
    yl = gf + 1.6
    for sx in (-.5, .5): add(P, slab(x1 - 1.6 + sx - .07, x1 - 1.6 + sx + .07, yl - 7, yl, zb + 3.0, zb + 3.15), 'metal', .4, up=0)
    for k in range(7): add(P, slab(x1 - 2.2, x1 - 1.0, yl - 6.5 + k, yl - 6.4 + k, zb + 3.0, zb + 3.15), 'metal', .45, up=0)
