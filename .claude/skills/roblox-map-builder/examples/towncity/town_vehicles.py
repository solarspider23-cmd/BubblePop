# Maple Junction vehicles: lofted car bodies (one section function per type), city bus, commuter train.
# Origin = ground centre, front = -Z (headlights at -Z). Wheels sit on y = 0.
import math, random
import bmesh
from mathutils import Vector
from town_props import *          # noqa: F401,F403
from town_props import PAL

def _smoothstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else (1.0 if x >= a else 0.0); return t * t * (3 - 2 * t)

def loft_closed(rings):
    bm = bmesh.new(); R = [[bm.verts.new(p) for p in ring] for ring in rings]; n = len(R[0])
    for A, Bq in zip(R, R[1:]):
        for i in range(n):
            j = (i + 1) % n; bm.faces.new((A[i], A[j], Bq[j], Bq[i]))
    bm.faces.new(R[0][::-1]); bm.faces.new(R[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def body_shell(L, W, floor, belt_f, roof_f, cab_f, width_f, n=16, glass_inset=.84):
    """lofted body: ring per section s (0 front .. 1 rear); belt_f(s) shoulder height, roof_f(s) roof height,
    cab_f(s) 0..1 cabin amount, width_f(s) width factor. Returns bm (closed)."""
    rings = []
    ss = [i / n for i in range(n + 1)]
    for s in ss:
        z = -L / 2 + L * s; w = W / 2 * width_f(s); b = belt_f(s); c = cab_f(s); r = lerp(b + .05, roof_f(s), c)
        xg, xr = lerp(.97, glass_inset, c), lerp(.9, .62, c)
        half = [(w * .9, floor), (w, floor + .6), (w, b), (w * xg, lerp(b + .03, r - .3, c)), (w * xr, r)]
        ring = [V3((x, y, z)) for x, y in half] + [V3((-x, y, z)) for x, y in reversed(half)]
        rings.append(ring)
    return loft_closed(rings)

def body_shader(col, belt_f, L, floor, glass_rule=None):
    """face colours: rocker + underside dark metal, glass above the belt (except near-flat roof faces), body below"""
    ub, ug, um = PAL.u(col), PAL.u('glass'), PAL.u('metal')
    def f(face):
        c = face.calc_center_median(); n = face.normal
        s = (c.z + L / 2) / L; b = belt_f(clamp(s))
        if c.y < floor + .45: return [(um, .25)] * len(face.loops)
        if c.y > b + .12 and abs(n.y) < .8 and (glass_rule is None or glass_rule(s, c, n)):
            return [(ug, clamp(.35 + .5 * clamp((c.y - b) / 2.5)))] * len(face.loops)
        return [(ub, clamp(.5 + .3 * n.y + .05 * n.x))] * len(face.loops)
    return f

def wheels(P, xs, zs, r=1.3, w=.9, hub='cream'):
    for x in xs:
        for z in zs:
            add(P, T(cyl(r, w, sides=10, y0=-w / 2), (x, r, z), 0, 0, 90), 'metal', .18, smooth=True)
            sgn = 1 if x > 0 else -1
            add(P, T(cyl(r * .55, .2, sides=8, y0=w / 2 - .05), (x, r, z), 0, 0, -90 * sgn), hub, .78)
            
def car(kind='sedan', col='red', seed=1):
    """stylised car: lofted body + greenhouse, wheels with hubs, grille, head/tail lights, bumpers, mirrors, door seams"""
    P = Prop('Car_%s_%s' % (kind, col))
    if kind == 'sedan':
        L, W, floor = 14.0, 6.4, .95
        belt = lambda s: lerp(2.55, 3.0, _smoothstep(0, .3, s)) - .35 * _smoothstep(.93, 1, s) + .12 * _smoothstep(.75, .9, s)
        cab = lambda s: _smoothstep(.3, .46, s) * (1 - _smoothstep(.68, .82, s))
        roof = lambda s: 5.0
    elif kind == 'hatch':
        L, W, floor = 12.0, 6.2, .95
        belt = lambda s: lerp(2.6, 3.1, _smoothstep(0, .28, s)) - .3 * _smoothstep(.95, 1, s)
        cab = lambda s: _smoothstep(.26, .44, s) * (1 - _smoothstep(.9, 1.0, s))
        roof = lambda s: 5.2 - .3 * _smoothstep(.7, 1, s)
    elif kind == 'van':
        L, W, floor = 15.5, 6.8, 1.0
        belt = lambda s: lerp(3.0, 3.4, _smoothstep(0, .18, s)) - .3 * _smoothstep(.96, 1, s)
        cab = lambda s: _smoothstep(.1, .24, s) * (1 - _smoothstep(.97, 1.0, s))
        roof = lambda s: 6.8
    else:                                                     # taxi = sedan shape
        return taxi(seed)
    wf = lambda s: .86 + .14 * _smoothstep(0, .1, s) - .06 * _smoothstep(.9, 1, s)
    glass_rule = None
    if kind == 'van': glass_rule = lambda s, c, n: s < .36 and n.z < .5
    bm = body_shell(L, W, floor, belt, roof, cab, wf, n=18)
    P.add(bm, body_shader(col, belt, L, floor, glass_rule))
    wheels(P, (-W / 2 * .86, W / 2 * .86), (-L * .32, L * .3), r=1.25 if kind != 'van' else 1.35)
    zf, zr = -L / 2, L / 2
    add(P, slab(-W * .36, W * .36, .8, 1.6, zf - .25, zf + .3), 'metal', .65)                       # bumpers
    add(P, slab(-W * .36, W * .36, .8, 1.6, zr - .3, zr + .25), 'metal', .65)
    add(P, slab(-W * .2, W * .2, 1.7, 2.3, zf - .08, zf + .3), 'metal', .2)                         # grille
    for sx in (-1, 1):
        add(P, slab(sx * W * .27 - .5, sx * W * .27 + .5, 1.9, 2.4, zf - .05, zf + .3), 'cream', .92)  # headlights
        add(P, slab(sx * W * .32 - .5, sx * W * .32 + .5, 2.0, 2.5, zr - .3, zr + .05), 'red', .55)    # tail lights
        zm = -L / 2 + L * (.3 if kind != 'van' else .14)
        add(P, T(box((.8, .5, .35)), (sx * (W / 2 + .1), belt(.3) + .2, zm)), col, .5)                 # mirrors
        add(P, slab(sx * W / 2 - .04, sx * W / 2 + .04, floor + .7, belt(.55) - .1, -L * .02, L * .02), 'metal', .25, up=0)  # door seam
    if kind == 'van':
        add(P, slab(-W * .4, W * .4, 6.8, 7.1, -L * .2, L * .4), 'metal', .4)                         # roof rack
        for k in range(4): add(P, slab(-W * .42, W * .42, 7.1, 7.3, -L * .15 + k * L * .17, -L * .15 + k * L * .17 + .25), 'metal', .45)
    return P

def taxi(seed=1):
    P = car('sedan', 'yellow', seed); P.name = 'Car_taxi'
    add(P, T(box((2.6, .9, 1.2), .15), (0, 5.4, .2)), 'cream', .85)
    add(P, slab(-1.2, 1.2, 5.05, 5.15, -.2, .6), 'metal', .3)
    for sx in (-1, 1): add(P, slab(sx * 3.2 - .03, sx * 3.2 + .03, 2.0, 2.6, -4, 4), 'metal', .2, up=0)       # side stripe
    return P

def bus(seed=1):
    """city bus: lofted box body, raked windscreen, window band with pillars, two doors on the kerb side (+X),
    destination band (blank, dark), roof AC pods, 6 wheels"""
    P = Prop('CityBus'); L, W, floor = 36.0, 8.2, 1.1
    belt = lambda s: lerp(3.2, 4.4, _smoothstep(0, .05, s))
    cab = lambda s: _smoothstep(0, .03, s)
    roof = lambda s: 10.4
    wf = lambda s: .95 + .05 * _smoothstep(0, .04, s)
    def glass_rule(s, c, n):
        if c.y > 9.0 and s > .05: return False                                             # roof band painted
        if abs(n.x) > .5:
            seg = (s * 9) % 1
            return seg > .26                                                                # window pillars
        return True
    P.add(body_shell(L, W, floor, belt, roof, cab, wf, n=36, glass_inset=.97), body_shader('blue', belt, L, floor, glass_rule))
    add(P, slab(-W / 2 - .05, W / 2 + .05, 3.8, 4.4, -L / 2 + 1, L / 2 - .5), 'yellow', .65, up=0)     # belt stripe
    add(P, slab(-W * .4, W * .4, 9.0, 9.9, -L / 2 - .02, -L / 2 + .5), 'metal', .15)                    # destination band
    for zc in (-L * .36, L * .05):                                                          # doors on the kerb side
        add(P, slab(W / 2 - .1, W / 2 + .08, floor + .3, 9.0, zc - 2.0, zc + 2.0), 'metal', .3, up=0)
        P.add(T(T(front_quad(-1.7, 1.7, floor + .9, 8.6, 0), (0, 0, 0), -90), (W / 2 + .1, 0, zc)), S('glass', base=.45, up=0, jit=0))
        add(P, slab(W / 2 + .08, W / 2 + .14, floor + .9, 8.6, zc - .08, zc + .08), 'metal', .3, up=0)
    for zc in (-L * .2, L * .25):
        add(P, T(box((5.0, 1.0, 7.0), .3), (0, 10.8, zc)), 'cream', .8)
    wheels(P, (-W / 2 * .88, W / 2 * .88), (-L * .33, L * .2, L * .34), r=1.6, w=1.1)
    add(P, slab(-W * .45, W * .45, .9, 1.9, -L / 2 - .3, -L / 2 + .3), 'metal', .6)
    add(P, slab(-W * .45, W * .45, .9, 1.9, L / 2 - .3, L / 2 + .3), 'metal', .6)
    for sx in (-1, 1):
        add(P, slab(sx * W * .33 - .6, sx * W * .33 + .6, 2.0, 2.7, -L / 2 - .08, -L / 2 + .2), 'cream', .92)
        add(P, slab(sx * W * .36 - .5, sx * W * .36 + .5, 2.2, 3.4, L / 2 - .2, L / 2 + .08), 'red', .55)
        add(P, T(box((.3, 1.4, .3)), (sx * (W / 2 + .5), 7.5, -L / 2 + .6)), 'metal', .3)
    return P

# ------------------------------------------------------------------ train
TRACK_GAUGE = 7.0
def _car_shell(L, W, nose, floor=2.4, belt=5.4, roof=12.6):
    """carriage / cab section loft: rounded roof shoulders, raked nose at the front when nose=True"""
    rings = []; n = 20
    for i in range(n + 1):
        s = i / n; z = -L / 2 + L * s
        k = _smoothstep(0, .16, s) if nose else 1.0
        r = lerp(belt + 2.6, roof, k) if nose else roof
        w = W / 2 * (lerp(.82, 1.0, _smoothstep(0, .08, s)) if nose else 1.0)
        zz = z + (1 - k) * 0                                                     # nose rake via ring height only
        half = [(w * .92, floor), (w, floor + .8), (w, belt), (w, 6.2), (w, 6.8), (w, 9.8), (w * .98, r - 1.4), (w * .8, r - .25), (w * .45, r)]
        rings.append([V3((x, y, zz)) for x, y in half] + [V3((-x, y, zz)) for x, y in reversed(half)])
    return loft_closed(rings)

def _train_shader(L, nose, doors):
    ut, uc, uy, ug, um = PAL.u('teal'), PAL.u('cream'), PAL.u('yellow'), PAL.u('glass'), PAL.u('metal')
    def f(face):
        c = face.calc_center_median(); n = face.normal; s = (c.z + L / 2) / L
        if c.y < 3.0: return [(um, .25)] * len(face.loops)
        if nose and s < .12 and c.y > 6.6 and n.z < -.15: return [(ug, .55)] * len(face.loops)        # windscreen
        if 6.8 < c.y < 9.6 and abs(n.x) > .6:
            if any(abs(c.z - dz) < 2.4 for dz in doors): return [(um, .35)] * len(face.loops)
            if not (nose and s < .14) and int(s * 20 + .5) % 3: return [(ug, .5 + .3 * (c.y - 6.8) / 2.8)] * len(face.loops)
        if c.y < 5.4: return [(ut, .5 + .2 * n.y)] * len(face.loops)
        if c.y < 6.2: return [(uy, .62)] * len(face.loops)
        if c.y > 11.6: return [(uc, .55 + .2 * n.y)] * len(face.loops)
        return [(uc, .78 + .1 * n.y)] * len(face.loops)
    return f

def train_car(kind='loco'):
    """commuter train car: lofted shell (teal skirt, yellow belt stripe, cream upper, glazed window band, raked
    windscreen on the cab), plug doors, two bogies with wheelsets + side frames, couplers, roof AC pods, pantograph"""
    P = Prop('Train_%s' % kind); L, W = 46.0, 9.6; nose = kind == 'loco'
    doors = (-L * .28, L * .28) if not nose else (-L * .05, L * .3)
    P.add(_car_shell(L, W, nose), _train_shader(L, nose, doors))
    for dz in doors:
        for sx in (-1, 1):
            add(P, slab(sx * W / 2 - .06, sx * W / 2 + .06, 3.0, 10.4, dz - 2.4, dz + 2.4), 'metal', .32, up=0)
            P.add(T(T(front_quad(-.9, .9, 6.6, 9.8, 0), (0, 0, 0), -90 * sx), (sx * (W / 2 + .08), 0, dz - 1.15)), S('glass', base=.5, up=0, jit=0))
            P.add(T(T(front_quad(-.9, .9, 6.6, 9.8, 0), (0, 0, 0), -90 * sx), (sx * (W / 2 + .08), 0, dz + 1.15)), S('glass', base=.5, up=0, jit=0))
    for bz in (-L * .33, L * .33):                                                        # bogies
        add(P, slab(-W * .38, W * .38, 1.2, 2.4, bz - 4.0, bz + 4.0), 'metal', .2)
        for sx in (-1, 1):
            add(P, slab(sx * TRACK_GAUGE / 2 - .25 - sx * 1.0, sx * TRACK_GAUGE / 2 + .25 - sx * 1.0, .9, 2.2, bz - 4.4, bz + 4.4), 'metal', .35)
            for wz in (bz - 2.6, bz + 2.6):
                add(P, T(cyl(1.1, .5, sides=12, y0=-.25), (sx * (TRACK_GAUGE / 2 - .5), 1.1, wz), 0, 0, 90), 'metal', .4)
    for z in (-L / 2 - .6, L / 2 + .6):
        add(P, slab(-.6, .6, 2.6, 3.6, z - .6, z + .6), 'metal', .3)
    for zc in ((-L * .1, L * .2) if nose else (-L * .25, 0, L * .25)):
        add(P, T(box((5.2, 1.0, 7.0), .35), (0, 12.8, zc)), 'cream', .62)
    if nose:
        add(P, T(box((2.6, .6, 2.4), .1), (0, 12.9, -L * .3)), 'metal', .35)                  # pantograph
        add(P, bar((-1, 13.2, -L * .3), (0, 16.0, -L * .3 + 1.4), .16, .16, 0), 'metal', .45)
        add(P, bar((0, 16.0, -L * .3 + 1.4), (1, 17.6, -L * .3), .16, .16, 0), 'metal', .45)
        add(P, slab(-2.4, 2.4, 17.5, 17.8, -L * .3 - .2, -L * .3 + .2), 'metal', .5)
        for sx in (-1, 1):
            add(P, slab(sx * 2.6 - .7, sx * 2.6 + .7, 4.0, 4.8, -L / 2 - .1, -L / 2 + .3), 'cream', .95)   # headlights
        add(P, slab(-W * .3, W * .3, 2.4, 3.4, -L / 2 - .4, -L / 2 + .4), 'yellow', .55)               # nose skirt
    return P

def track_seg(L=24.0):
    """one track segment along Z: ballast bed, 12 sleepers, two rails with chairs"""
    P = Prop('TrackSeg')
    bm = bmesh.new()
    pts = [(-6.5, -.3), (-5.0, .8), (5.0, .8), (6.5, -.3)]
    Fv = [bm.verts.new((x, y, -L / 2)) for x, y in pts]; Bv = [bm.verts.new((x, y, L / 2)) for x, y in pts]
    for i in range(3): bm.faces.new((Fv[i], Fv[i + 1], Bv[i + 1], Bv[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    add(P, bm, 'pave', .3, up=0)
    for k in range(12):
        z = -L / 2 + (k + .5) * L / 12
        add(P, slab(-5.2, 5.2, .7, 1.2, z - .7, z + .7), 'wood', .4)
    for sx in (-1, 1):
        x = sx * TRACK_GAUGE / 2
        add(P, slab(x - .35, x + .35, 1.2, 1.5, -L / 2, L / 2), 'metal', .35)
        add(P, slab(x - .18, x + .18, 1.5, 2.1, -L / 2, L / 2), 'metal', .7, up=.2)
    return P
