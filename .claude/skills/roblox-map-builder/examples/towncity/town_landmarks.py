# Maple Junction landmarks + stations: Town Hall body + Clock Tower (heroes), Train Station (hero), platform canopy,
# fountain, bank, car showroom, job board, bus stop, skyline frame towers. Origin bottom centre, front -Z.
import math, random
import bmesh
from mathutils import Vector
from town_props import *          # noqa: F401,F403
from town_props import window_unit, holed_front, ring_frame, front_quad, flower

def frustum(x0, x1, z0, z1, y0, y1, inset_x, inset_z):
    """box whose top is inset (mansard / hip roof / plinth taper)"""
    bm = bmesh.new()
    lo = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))]
    hi = [bm.verts.new(p) for p in ((x0 + inset_x, y1, z0 + inset_z), (x1 - inset_x, y1, z0 + inset_z), (x1 - inset_x, y1, z1 - inset_z), (x0 + inset_x, y1, z1 - inset_z))]
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    for k in range(4): j = (k + 1) % 4; bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def column(P, x, z, y0, h, r=1.1, col='cream', sides=12):
    """classical column: square plinth, torus base, fluted-look shaft (12 sides, slight taper), capital + abacus"""
    add(P, slab(x - r * 1.4, x + r * 1.4, y0, y0 + .8, z - r * 1.4, z + r * 1.4), col, .7)
    add(P, T(cyl(r * 1.25, .5, sides=sides, y0=y0 + .8), (x, 0, z)), col, .75, smooth=True)
    add(P, T(cyl(r, h - 2.8, sides=sides, y0=y0 + 1.3, r2=r * .88), (x, 0, z)), col, .8, smooth=True)
    add(P, T(cyl(r * .95, .6, sides=sides, y0=y0 + h - 1.5, r2=r * 1.25), (x, 0, z)), col, .78, smooth=True)
    add(P, slab(x - r * 1.45, x + r * 1.45, y0 + h - .9, y0 + h, z - r * 1.45, z + r * 1.45), col, .84)

def pediment(P, x0, x1, y, z, h, depth, col='cream', tymp='brick', emblem=True):
    """triangular pediment: raking cornices + tympanum + round emblem (no text)"""
    w = x1 - x0; cx = (x0 + x1) / 2
    bm = bmesh.new()
    Fv = [bm.verts.new(p) for p in ((x0 + 1, y, z + .4), (x1 - 1, y, z + .4), (cx, y + h - 1, z + .4))]
    Bv = [bm.verts.new(p) for p in ((x0 + 1, y, z + depth), (x1 - 1, y, z + depth), (cx, y + h - 1, z + depth))]
    bm.faces.new(Fv[::-1]); bm.faces.new(Bv)
    for k in range(3): j = (k + 1) % 3; bm.faces.new((Fv[k], Fv[j], Bv[j], Bv[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, tymp, .6, up=0)
    for sx in (-1, 1):                                                                      # raking cornices
        a = V3((cx + sx * (w / 2 + .6), y - .2, z - .2)); b = V3((cx, y + h + .2, z - .2))
        add(P, bar(a, b, depth + .8, 1.0, 0), col, .82)
    add(P, slab(x0 - .6, x1 + .6, y - 1.0, y, z - .6, z + depth), col, .8)
    if emblem:
        add(P, T(cyl(h * .28, .5, sides=16), (cx, y + h * .38, z + .1), 0, 90), 'yellow', .62, smooth=True)
        add(P, T(torus(h * .28, .2, n=16, sides=4), (cx, y + h * .38, z - .1), 0, 90), 'cream', .85)
        add(P, T(ngon_prism([(math.cos(k * math.tau / 10 + math.pi / 2) * (h * .18 if k % 2 == 0 else h * .08), math.sin(k * math.tau / 10 + math.pi / 2) * (h * .18 if k % 2 == 0 else h * .08)) for k in range(10)], 0, .3), (cx, y + h * .38, z - .45), 0, 90), 'cream', .9)

def clock_face(P, c, r, yaw=0.0):
    """clock: cream dial, gold bezel, 12 tick marks (no numerals), two hands, centre boss; faces -Z before yaw"""
    def L(bm): return T(bm, c, yaw)
    add(P, L(T(cyl(r * 1.08, .5, sides=24), (0, 0, 0), 0, 90)), 'yellow', .55, smooth=True)
    add(P, L(T(cyl(r, .3, sides=24), (0, 0, -.45), 0, 90)), 'cream', .92, smooth=True)
    add(P, L(T(torus(r * 1.04, .22, n=24, sides=4), (0, 0, -.55), 0, 90)), 'yellow', .7)
    for k in range(12):
        a = k * math.tau / 12; big = k % 3 == 0
        add(P, L(T(box((.35 if big else .2, r * (.2 if big else .12), .15)), (math.sin(a) * r * .82, math.cos(a) * r * .82, -.85), 0, 0, -math.degrees(a))), 'metal', .2)
    add(P, L(T(box((.3, r * .55, .12)), (0, 0, -.95), 0, 0, -50)), 'metal', .15)
    add(P, L(T(T(box((.22, r * .78, .12)), (0, r * .3, 0)), (0, 0, -1.05), 0, 0, 25)), 'metal', .15)
    add(P, L(T(cyl(.4, .3, sides=8), (0, 0, -1.2), 0, 90)), 'yellow', .7)

def arch_open(P, x, y0, w, h, zf, depth, col, frame='cream'):
    """an arched opening framed with voussoirs: the wall around it must be built by the caller with a rect hole;
    this adds the spandrel fills, the arch ring and the reveal"""
    rh = w / 2; ys = y0 + h - rh
    for side in (-1, 1):
        arc_q = [(x + side * math.cos(math.pi * k / 10) * rh, ys + math.sin(math.pi * k / 10) * rh) for k in range(0, 6)]
        poly = [(x + side * w / 2, y0 + h)] + list(reversed(arc_q))
        for zz, flip in ((zf, False), (zf + depth, True)):
            bm = bmesh.new(); f = bm.faces.new([bm.verts.new((px, py, zz)) for px, py in poly]); f.normal_update()
            if (f.normal.z > 0) != flip: f.normal_flip()
            add(P, bm, col, .64, up=0, jit=0)
    arc = [(x + math.cos(math.pi * k / 10) * rh, ys + math.sin(math.pi * k / 10) * rh) for k in range(11)]
    bm = bmesh.new()
    for (ax, ay), (bx_, by_) in zip(arc, arc[1:]):
        bm.faces.new([bm.verts.new(p) for p in ((ax, ay, zf), (ax, ay, zf + depth), (bx_, by_, zf + depth), (bx_, by_, zf))])
    bm.normal_update()
    for f in bm.faces:
        cc = f.calc_center_median()
        if f.normal.dot(V3((x, ys, cc.z)) - cc) < 0: f.normal_flip()
    add(P, bm, col, .5, up=0, jit=0)
    ring = [V3((x + math.cos(math.pi * k / 10) * (rh + .5), ys + math.sin(math.pi * k / 10) * (rh + .5), zf - .15)) for k in range(11)]
    add(P, tube(ring, .55, sides=4, rot0=math.pi / 4), frame, .8)
    add(P, T(box((1.4, 1.6, .9)), (x, ys + rh + .6, zf - .3)), frame, .86)
    for sx in (-1, 1): add(P, slab(x + sx * w / 2 - .5, x + sx * w / 2 + .5, ys - .5, ys + .2, zf - .4, zf + .2), frame, .8)

# ================================================================== TOWN HALL (hero) + CLOCK TOWER (hero)
TH_W, TH_D, TH_H = 104.0, 52.0, 34.0
def town_hall():
    """civic hall on a podium: brick wings with arched + tall windows, cream rusticated ground floor, projecting
    centre pavilion with a 6-column portico + pediment, grand stair, teal copper mansard roofs with dormers,
    balustrades, urns. The clock tower is a separate prop at (0, TH_H, 6)."""
    P = Prop('TownHall'); hw, hd = TH_W / 2, TH_D / 2; zf = -hd; G0 = 3.0
    add(P, slab(-hw - 2, hw + 2, -.6, G0, -hd - 2, hd + 2), 'cream', .55)                                # podium
    add(P, slab(-hw - 2.4, hw + 2.4, G0 - .5, G0, -hd - 2.4, hd + 2.4), 'cream', .82)
    for k in range(6):                                                                                   # grand stair
        y = k * .5; add(P, slab(-26, 26, -.6, y + .5, -hd - 2 - 14 + k * 2.3, -hd - 2), 'cream', .7 + .02 * (k % 2))
    for sx in (-1, 1):                                                                                   # stair cheeks + lamps
        add(P, slab(min(sx * 26, sx * 27.6), max(sx * 26, sx * 27.6), -.6, 4.4, -hd - 16, -hd - 2), 'cream', .6)
        add(P, T(cyl(.9, 1.2, sides=8, y0=4.4), (sx * 26.8, 0, -hd - 14)), 'cream', .8)
        add(P, T(ball(1.0, 10, 6), (sx * 26.8, 6.4, -hd - 14)), 'yellow', .6, smooth=True)
    # body: wings (x |20..52|) brick over a cream ground floor, 2 floors of windows
    F1, F2 = G0 + 13, G0 + 13 + 18
    for sx in (-1, 1):
        x0, x1 = (20, hw) if sx > 0 else (-hw, -20)
        nb = 4; bw = (x1 - x0) / nb; xs = [x0 + bw * (i + .5) for i in range(nb)]
        holes = [(x - 2.6, x + 2.6, G0 + 2.5, G0 + 10.5) for x in xs] + [(x - 2.8, x + 2.8, F1 + 3, F1 + 14) for x in xs]
        holed_front(P, x0, x1, G0, F1, [h for h in holes if h[2] < F1], zf, 'cream', .62)
        holed_front(P, x0, x1, F1, TH_H, [h for h in holes if h[2] >= F1], zf, 'brick', .66)
        for x in xs:
            window_unit(P, x, G0 + 2.5, 5.2, 8.0, zf, 'tall', col_frame='cream')
            window_unit(P, x, F1 + 3, 5.6, 11.0, zf, 'arch', col_frame='cream', wall_col='brick')
        for k in range(5):                                                                                # rustication grooves
            add(P, slab(x0, x1, G0 + 1.8 + k * 2.4, G0 + 2.0 + k * 2.4, zf - .15, zf), 'cream', .5, up=0)
        add(P, slab(x0 - .2, x1 + .2, F1 - .6, F1 + .5, zf - .6, zf + .2), 'cream', .82)                  # string course
        for x in (x0 + .9, x1 - .9): add(P, slab(x - 1.2, x + 1.2, F1, TH_H, zf - .5, zf + .2), 'cream', .78)   # pilasters
        # side + back walls (plain brick, decal windows)
        xo = hw if sx > 0 else -hw
        add(P, slab(xo - .6 if sx > 0 else xo, xo if sx > 0 else xo + .6, G0, TH_H, -hd, hd, drop=('-x',) if sx > 0 else ('+x',)), 'brick', .64, up=0)
        add(P, slab(x0, x1, G0, TH_H, hd - .6, hd, drop=('-z',)), 'brick', .62, up=0)
        for k in range(4):
            for yy in (G0 + 3, F1 + 4):
                from town_props import deco_window
                deco_window(P, '+x' if sx > 0 else '-x', -hd + TH_D * (k + .5) / 4, yy, 4.0, 8.5, hw + .02)
                deco_window(P, '+z', xs[k], yy, 4.6, 8.5, hd + .02)
        # mansard roof with dormers
        add(P, slab(x0 - .9, x1 + .9, TH_H, TH_H + 1.4, -hd - .9, hd + .9), 'cream', .82)
        add(P, frustum(x0, x1, -hd, hd, TH_H + 1.4, TH_H + 10, 3.5, 3.5), 'teal', .55, up=.3)
        add(P, slab(x0 + 3.2, x1 - 3.2, TH_H + 10, TH_H + 10.6, -hd + 3.2, hd - 3.2), 'cream', .8)
        for x in xs:
            dz = zf + 1.8
            add(P, slab(x - 2.4, x + 2.4, TH_H + 2, TH_H + 7.5, dz - .4, dz + 3), 'cream', .76)
            P.add(front_quad(x - 1.6, x + 1.6, TH_H + 2.6, TH_H + 6.6, dz - .45), S('glass', grad=(TH_H + 2, TH_H + 7, .45, .9), up=0, jit=0))
            bm = bmesh.new(); pts = [(x - 3, TH_H + 7.5), (x + 3, TH_H + 7.5), (x, TH_H + 9.6)]
            Fv = [bm.verts.new((px, py, dz - .7)) for px, py in pts]; Bv = [bm.verts.new((px, py, dz + 3)) for px, py in pts]
            bm.faces.new(Fv[::-1]); bm.faces.new(Bv)
            for k in range(3): j = (k + 1) % 3; bm.faces.new((Fv[k], Fv[j], Bv[j], Bv[k]))
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, 'teal', .45)
    # centre pavilion (x -20..20) projects 7 forward, portico of 6 columns, pediment
    zc = zf - 7
    add(P, slab(-20, 20, G0, TH_H + 4, zc + .6, hd, drop=('-y',)), 'metal', .25, up=0)
    holed_front(P, -20, 20, G0, TH_H + 4, [(-4.5, 4.5, G0, G0 + 15)] + [(x - 2.6, x + 2.6, G0 + 3, G0 + 12) for x in (-13, 13)] +
                [(x - 2.8, x + 2.8, F1 + 3, F1 + 14) for x in (-13, 0, 13)], zc, 'cream', .7)
    for x in (-13, 13): window_unit(P, x, G0 + 3, 5.2, 9.0, zc, 'tall')
    for x in (-13, 0, 13): window_unit(P, x, F1 + 3, 5.6, 11.0, zc, 'arch', wall_col='cream')
    for sx in (-1, 1):
        add(P, slab(sx * 20 - (.6 if sx > 0 else 0), sx * 20 + (0 if sx > 0 else .6), G0, TH_H + 4, zc, zf), 'cream', .64)
    # main door: big double door in a framed recess
    add(P, slab(-4.5, 4.5, G0, G0 + 15, zc + 1.6, zc + 1.9), 'wood', .4, up=0)
    for sx in (-1, 1):
        add(P, slab(sx * 2.25 - 1.9, sx * 2.25 + 1.9, G0 + 1, G0 + 12, zc + 1.4, zc + 1.6), 'wood', .55, up=0)
        add(P, T(ball(.35, 6, 4), (sx * .7, G0 + 6.5, zc + 1.2)), 'yellow', .8)
    add(P, slab(-4.5, -4.5 + .6, G0, G0 + 15, zc, zc + 1.6), 'cream', .55, up=0); add(P, slab(4.5 - .6, 4.5, G0, G0 + 15, zc, zc + 1.6), 'cream', .55, up=0)
    add(P, slab(-4.5, 4.5, G0 + 14.4, G0 + 15, zc, zc + 1.6), 'cream', .55, up=0)
    P.add(front_quad(-3.8, 3.8, G0 + 12.3, G0 + 14.3, zc + 1.55), S('glass', base=.6, up=0, jit=0))
    zp = zc - 9                                                                                           # portico
    add(P, slab(-22, 22, G0 - .1, G0 + .5, zp - 2, zc), 'cream', .76)
    for k in range(6):
        column(P, -17.5 + k * 7, zp, G0 + .5, 24, 1.3)
    add(P, slab(-21, 21, G0 + 24.5, G0 + 28, zp - 2, zc + .5), 'cream', .8)                              # entablature
    add(P, slab(-21.6, 21.6, G0 + 27.4, G0 + 28.4, zp - 2.6, zc + .5), 'cream', .88)
    add(P, slab(-21, 21, G0 + 25.3, G0 + 26.5, zp - 2.15, zp - 1.9), 'teal', .5, up=0)                    # frieze stripe
    pediment(P, -21.6, 21.6, G0 + 28.4, zp - 2.6, 11, 9, tymp='cream')
    add(P, frustum(-20, 20, zc + 9, hd, TH_H + 4, TH_H + 8, 2, 2), 'teal', .5, up=.3)
    # balustrade + urns on the cornice of the wings
    for sx in (-1, 1):
        x0, x1 = (20, hw) if sx > 0 else (-hw, -20)
        for k in range(3):
            x = x0 + (x1 - x0) * (k + .5) / 3
            add(P, T(lathe([(.9, 0), (.6, .6), (1.0, 1.4), (.4, 2.2), (.6, 2.6), (0, 2.9)], n=8), (x, TH_H + 1.4, zf - .2)), 'cream', .8, smooth=True)
    P.door = (0.0, G0, zc + 1.6)
    return P

def clock_tower():
    """tower standing on the town hall roof: brick shaft with cream quoins + bands, clock stage with 4 clock faces,
    open belfry (corner piers, arched openings, bell), octagonal drum, teal copper dome, lantern + gold finial"""
    P = Prop('ClockTower'); w = 22.0; hw = w / 2
    add(P, slab(-hw, hw, -1, 40, -hw, hw), 'brick', .64, up=0)                                         # shaft
    for k in range(9):
        y = k * 4.4
        for sx in (-1, 1):
            for sz in (-1, 1):
                a, b = (2.4, 1.2) if k % 2 == 0 else (1.2, 2.4)
                add(P, cslab(sx, sz, hw, a, b, y, y + 3.6), 'cream', .8, up=0)
    for y in (12, 26):
        add(P, slab(-hw - .4, hw + .4, y, y + .8, -hw - .4, hw + .4), 'cream', .8)
    for yaw in (0, 90, 180, 270):                                                                          # tall slit windows
        for k in (12.8, 26.8):
            bm = front_quad(-1.4, 1.4, k + 2, k + 10, -hw - .03); P.add(T(bm, (0, 0, 0), yaw), S('glass', grad=(k, k + 10, .45, .85), up=0, jit=0))
            add(P, T(T(ring_frame(2.6, 7.8, .5, .3, True), (0, k + 6, -hw - .12)), (0, 0, 0), yaw), 'cream', .82)
    add(P, slab(-hw - 1.2, hw + 1.2, 40, 42, -hw - 1.2, hw + 1.2), 'cream', .84)                          # clock stage
    add(P, slab(-hw - .4, hw + .4, 42, 58, -hw - .4, hw + .4), 'cream', .74, up=0)
    for sx in (-1, 1):
        for sz in (-1, 1): add(P, cslab(sx, sz, hw + .4, 2.2, 2.2, 42, 58, .5), 'cream', .86)
    for yaw in (0, 90, 180, 270):
        clock_face(P, tuple(T_point((0, 50, -hw - .45), yaw)), 6.8, yaw)
    add(P, slab(-hw - 1.6, hw + 1.6, 58, 59.6, -hw - 1.6, hw + 1.6), 'cream', .88)
    # belfry: 4 corner piers + arches + parapet, bell inside
    bw = hw - 1
    for sx in (-1, 1):
        for sz in (-1, 1): add(P, cslab(sx, sz, bw, 2.6, 2.6, 59.6, 73, 0), 'brick', .64, up=0)
    for yaw in (0, 90, 180, 270):
        tmp = Prop('tmp')
        for sx in (-1, 1): add(tmp, slab(sx * (bw - 2.6) - (.01 if sx > 0 else -.01), sx * (bw - 2.6), 59.6, 73, -bw, -bw + 1.4), 'brick', .64)
        add(tmp, slab(-bw + 2.6, bw - 2.6, 69.5, 73, -bw, -bw + 1.4), 'brick', .64, up=0)
        arch_open(tmp, 0, 59.6, 2 * (bw - 2.6), 9.9, -bw, 1.4, 'brick')
        add(tmp, slab(-bw + 2.6, bw - 2.6, 59.6, 62, -bw, -bw + 1.4), 'cream', .7)                        # sill wall
        _merge(P, tmp, yaw)
    add(P, slab(-bw + 1, bw - 1, 59.4, 59.8, -bw + 1, bw - 1), 'metal', .3)
    add(P, lathe([(0, 63), (2.6, 63.2), (2.9, 64), (2.2, 66.5), (1.4, 68.4), (.5, 69), (0, 69.2)], n=14), 'yellow', .55, smooth=True)
    add(P, slab(-hw - .8, hw + .8, 73, 74.6, -hw - .8, hw + .8), 'cream', .88)
    for sx in (-1, 1):
        for sz in (-1, 1):
            add(P, T(lathe([(1.1, 0), (.7, .7), (1.2, 1.6), (.5, 2.6), (.7, 3.0), (0, 3.4)], n=8), (sx * (hw - .4), 74.6, sz * (hw - .4))), 'cream', .82, smooth=True)
    # drum + dome + lantern + finial
    add(P, T(cyl(8.4, 5, sides=8, y0=74.6, rot0=math.pi / 8), (0, 0, 0)), 'cream', .76)
    for k in range(8):
        a = k * math.tau / 8
        add(P, T(box((1.2, 5, 1.2)), (math.cos(a) * 8.4, 77.1, math.sin(a) * 8.4)), 'cream', .88)
        P.add(T(T(front_quad(-1.6, 1.6, 75.6, 78.8, -7.95), (0, 0, 0), 90 - math.degrees(a + math.tau / 16)), (0, 0, 0)), S('glass', base=.55, up=0, jit=0))
    add(P, T(cyl(9.0, 1.0, sides=16, y0=79.6), (0, 0, 0)), 'cream', .86, smooth=True)
    prof = [(8.6, 80.6)] + [(8.6 * math.cos(math.pi / 2 * k / 7), 80.6 + 10.5 * math.sin(math.pi / 2 * k / 7)) for k in range(1, 8)]
    add(P, lathe(prof, n=16), 'teal', .5, smooth=True)
    for k in range(8):                                                                                      # dome ribs
        a = k * math.tau / 8
        rib = [V3((math.cos(a) * r * 1.01, y, math.sin(a) * r * 1.01)) for r, y in prof[:-1]]
        add(P, tube(rib, .22, sides=4), 'yellow', .62)
    add(P, T(cyl(2.2, 4.4, sides=8, y0=90.8), (0, 0, 0)), 'cream', .8)
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8
        add(P, T(box((.5, 4.4, .5)), (math.cos(a) * 2.25, 93, math.sin(a) * 2.25)), 'cream', .9)
    add(P, lathe([(2.8, 95.2), (2.4, 96.2), (.4, 99), (0, 99.4)], n=8), 'teal', .5, smooth=True)
    add(P, lathe([(0, 99.2), (.6, 99.6), (.7, 100.4), (.2, 101.2), (.25, 104.5), (0, 105)], n=8), 'yellow', .7, smooth=True)
    return P

def cslab(sx, sz, h, a, b, y0, y1, out=.2):
    """corner block at corner (sx, sz) of a square of half-size h: a x b deep into the corner, proud by `out`"""
    xr = (h - a, h + out) if sx > 0 else (-h - out, -h + a)
    zr = (h - b, h + out) if sz > 0 else (-h - out, -h + b)
    return slab(xr[0], xr[1], y0, y1, zr[0], zr[1])

def T_point(p, yaw):
    v = Matrix.Rotation(math.radians(yaw), 3, 'Y') @ V3(p); return v

def _merge(P, tmp, yaw=0.0, pos=(0, 0, 0)):
    """copy a temp Prop's solid mesh into P turned by yaw (keeps UVs)"""
    from pro_lib import MB
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    mb = tmp.solid; base = len(P.solid.V)
    P.solid.V += [tuple(R @ V3(v) + V3(pos)) for v in mb.V]
    P.solid.F += [tuple(i + base for i in f) for f in mb.F]
    P.solid.UV += mb.UV; P.solid.SM += mb.SM

# ================================================================== TRAIN STATION (hero) + platform
ST_W, ST_D = 84.0, 36.0
def train_station():
    """brick head house: central great arched window with fan glazing over a walk-through arched passage to the
    platform, flanking arched doors, side towers with slate pyramid roofs + clocks, cornice + parapet, teal roof"""
    P = Prop('TrainStation'); hw, hd = ST_W / 2, ST_D / 2; zf = -hd; H = 36.0
    add(P, slab(-hw - 1, hw + 1, -.6, 1.2, -hd - 3, hd + 1), 'cream', .6)
    for k in range(3): add(P, slab(-12, 12, -.6, .4 * (k + 1), -hd - 6 + k * 1.2, -hd - 3), 'cream', .7)
    # passage: floor + walls + barrel vault through the building (x -7..7, height 18)
    pw, ph = 14.0, 20.0; rr = pw / 2; ys = ph - rr
    add(P, slab(-pw / 2, pw / 2, .9, 1.2, -hd, hd), 'pave', .62, up=0)
    for sx in (-1, 1):
        add(P, slab(sx * pw / 2 - (0 if sx < 0 else .01), sx * pw / 2 + (.6 * sx), 1.2, ys, -hd, hd), 'cream', .6, up=0)
    arc = [(math.cos(math.pi * k / 10) * rr, ys + math.sin(math.pi * k / 10) * rr) for k in range(11)]
    bm = bmesh.new()
    for (ax, ay), (bx_, by_) in zip(arc, arc[1:]):
        bm.faces.new([bm.verts.new(p) for p in ((ax, ay, -hd), (bx_, by_, -hd), (bx_, by_, hd), (ax, ay, hd))])
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(V3((0, ys, c.z)) - c) < 0: f.normal_flip()
    add(P, bm, 'cream', .5, up=0)
    for k in range(4):                                                                       # hanging lamps in the passage
        z = -hd + ST_D * (k + .5) / 4
        add(P, tube([V3((0, ys + rr - .2, z)), V3((0, ys + rr - 4, z))], .06, sides=3), 'metal', .4)
        P.gadd(T(ball(.9, 8, 5), (0, ys + rr - 4.6, z)), 'lamp')
    # front wall with holes: passage arch, 2 side doors, ground windows, great window above
    gw = 30.0; gy0 = 22.0
    holes = [(-pw / 2, pw / 2, 1.2, ph), (-gw / 2, gw / 2, gy0, gy0 + gw / 2 + 4)]
    for sx in (-1, 1):
        holes += [(sx * 16 - 3, sx * 16 + 3, 1.2, 12.5), (sx * 28 - 2.6, sx * 28 + 2.6, 4, 13), (sx * 36.5 - 2.4, sx * 36.5 + 2.4, 4, 13)]
    holed_front(P, -hw, hw, 1.2, H, holes, zf, 'brick', .66)
    arch_open(P, 0, 1.2, pw, ph, zf, ST_D * 0 + .6, 'brick')
    for sx in (-1, 1):
        arch_open(P, sx * 16, 1.2, 6, 11.3, zf, .6, 'brick')
        add(P, slab(sx * 16 - 3, sx * 16 + 3, 1.2, 9.2, zf + 1.4, zf + 1.6), 'wood', .45, up=0)              # doors
        P.add(front_quad(sx * 16 - 2.4, sx * 16 + 2.4, 5, 9, zf + 1.35), S('glass', base=.55, up=0, jit=0))
        add(P, slab(sx * 16 - 3, sx * 16 + 3, 1.2, 12.5, zf + 1.6, zf + 1.8), 'metal', .25, up=0)
        for xx in (sx * 28, sx * 36.5): window_unit(P, xx, 4, 5.2 if abs(xx) < 30 else 4.8, 9, zf, 'archtop' if False else 'arch', wall_col='brick')
    # great window: glass + fan glazing bars + transom, keystone, deep frame
    gr = gw / 2; gys = gy0 + 4
    pts = [(-gr, gy0), (gr, gy0), (gr, gys)] + [(math.cos(math.pi * k / 16) * gr, gys + math.sin(math.pi * k / 16) * gr) for k in range(1, 16)] + [(-gr, gys)]
    P.add(quad([(px, py, zf + 1.0) for px, py in reversed(pts)]), S('glass', grad=(gy0, gys + gr, .5, .92), up=0, jit=0))
    for side in (-1, 1):
        arc_q = [(side * math.cos(math.pi * k / 16) * gr, gys + math.sin(math.pi * k / 16) * gr) for k in range(0, 9)]
        poly = [(side * gr, gy0 + gw / 2 + 4)] + list(reversed(arc_q))
        bm = bmesh.new(); f = bm.faces.new([bm.verts.new((px, py, zf)) for px, py in poly]); f.normal_update()
        if f.normal.z > 0: f.normal_flip()
        add(P, bm, 'brick', .66, up=0, jit=0)
    for k in range(1, 8):
        a = math.pi * k / 8
        add(P, bar((0, gys, zf + .8), (math.cos(a) * gr, gys + math.sin(a) * gr, zf + .8), .35, .35, 0), 'cream', .9)
    add(P, T(torus(gr * .35, .25, n=12, sides=4, a0=0, a1=math.pi), (0, gys, zf + .8), 0, 90), 'cream', .9)
    add(P, slab(-gr, gr, gys - .2, gys + .3, zf + .5, zf + 1.0), 'cream', .9)
    for k in range(1, 6): add(P, slab(-gr + gw * k / 6 - .17, -gr + gw * k / 6 + .17, gy0, gys, zf + .5, zf + 1.0), 'cream', .9)
    ring = [V3((math.cos(math.pi * k / 16) * (gr + .8), gys + math.sin(math.pi * k / 16) * (gr + .8), zf - .2)) for k in range(17)]
    add(P, tube(ring, .9, sides=4, rot0=math.pi / 4), 'cream', .82)
    add(P, slab(-gr - 1.4, gr + 1.4, gy0 - 1.2, gy0, zf - .8, zf + .4), 'cream', .84)
    # sign band (blank, GUI) over the passage arch
    add(P, slab(-11, 11, ph + .4, ph + 3.0, zf - .5, zf), 'teal', .4, up=0)
    add(P, slab(-10.4, 10.4, ph + .8, ph + 2.6, zf - .7, zf - .4), 'cream', .92, up=0)
    # string course, cornice, parapet
    add(P, slab(-hw - .3, hw + .3, 14.4, 15.2, zf - .5, hd + .3), 'cream', .82)
    add(P, slab(-hw - 1, hw + 1, H, H + 1.4, zf - 1.2, hd + 1), 'cream', .86)
    for x in range(-40, 41, 8):
        if abs(x) < 16: continue
        add(P, slab(x - .5, x + .5, H - 1.4, H, zf - 1.0, zf), 'cream', .82)
    add(P, slab(-hw, hw, H + 1.4, H + 4, zf, zf + .8), 'brick', .62, up=0)
    add(P, slab(-hw - .3, hw + .3, H + 4, H + 4.6, zf - .3, zf + 1.1), 'cream', .86)
    gpts = [(-18, 0), (18, 0), (0, 9)]                                                      # central gable over the window
    bm = bmesh.new(); Fv = [bm.verts.new((x, H + 4.6 + y, zf)) for x, y in gpts]; Bv = [bm.verts.new((x, H + 4.6 + y, zf + 1.2)) for x, y in gpts]
    bm.faces.new(Fv[::-1]); bm.faces.new(Bv)
    for k in range(3): j = (k + 1) % 3; bm.faces.new((Fv[k], Fv[j], Bv[j], Bv[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, 'brick', .6, up=0)
    for sx in (-1, 1): add(P, bar((sx * 19, H + 4.4, zf - .3), (0, H + 14, zf - .3), 1.8, .9, 0), 'cream', .86)
    clock_face(P, (0, H + 7.6, zf - .2), 3.4)
    # roof behind
    for xa, xb in ((-hw, -pw / 2 - .6), (pw / 2 + .6, hw)):                                # body either side of the passage
        add(P, slab(xa, xb, 1.2, H, -hd + .6, hd, drop=('-y', '-z')), 'brick', .6, up=0)
    add(P, slab(-pw / 2 - .6, pw / 2 + .6, ph + .2, H, -hd + .6, hd, drop=('-y', '-z')), 'brick', .6, up=0)
    arch_open(P, 0, 1.2, pw, ph, hd - .6, .6, 'brick')                                       # back portal onto the platform
    add(P, frustum(-hw + 1, hw - 1, zf + 2, hd, H + .5, H + 9, 0, 14), 'teal', .5, up=.3)
    # side towers
    for sx in (-1, 1):
        tx = sx * (hw + 6); tw = 12
        add(P, slab(tx - tw / 2, tx + tw / 2, -.6, H + 14, zf - 2, zf + 14), 'brick', .64, up=0)
        for k in range(10):
            y = 1 + k * 5
            for ex in (tx - tw / 2, tx + tw / 2 - 1.6):
                add(P, slab(ex - .1, ex + 1.7, y, y + 4, zf - 2.3, zf - 1.9 + (1.6 if k % 2 else .8)), 'cream', .82, up=0)
        for yy in (5, 20, 33):
            P.add(front_quad(tx - 1.6, tx + 1.6, yy, yy + 7, zf - 2.05), S('glass', grad=(yy, yy + 7, .45, .85), up=0, jit=0))
            add(P, T(ring_frame(3.2, 7, .5, .3, True), (tx, yy + 3.5, zf - 2.15)), 'cream', .84)
            add(P, slab(tx - 2.4, tx + 2.4, yy - .5, yy, zf - 2.8, zf - 1.9), 'cream', .8)
        add(P, slab(tx - tw / 2 - .8, tx + tw / 2 + .8, H + 14, H + 15.4, zf - 2.8, zf + 14.8), 'cream', .86)
        add(P, frustum(tx - tw / 2 - .4, tx + tw / 2 + .4, zf - 2.4, zf + 14.4, H + 15.4, H + 26, 5.6, 7.8), 'slate', .5, up=.3)
        add(P, T(lathe([(0, 0), (.5, .2), (.5, 2.4), (.2, 4.6), (0, 5)], n=6), (tx, H + 25.6, zf + 6)), 'yellow', .7)
    P.passage = (0.0, 1.2, 0.0)
    return P

def platform_canopy(L=24.0, W=22.0):
    """platform segment along Z (track side = +X): raised deck with stone edge + yellow safety line, two rows of
    steel columns with brackets, curved canopy roof (teal) with a glazed ridge strip, hanging lamps, a bench"""
    P = Prop('PlatformCanopy'); hw = W / 2; Y = 2.2
    add(P, slab(-hw, hw, -.6, Y, -L / 2, L / 2), 'pave', .62, up=0)
    add(P, slab(hw - 1.4, hw, Y - .2, Y + .05, -L / 2, L / 2), 'cream', .82)
    add(P, slab(hw - 2.6, hw - 1.8, Y, Y + .04, -L / 2, L / 2), 'yellow', .7, up=0)
    for z in (-L / 4, L / 4):
        for x in (-hw * .45, hw * .45):
            add(P, T(cyl(.45, 16, sides=8, y0=Y), (x, 0, z)), 'teal', .4)
            add(P, T(cyl(.7, .6, sides=8, y0=Y), (x, 0, z)), 'teal', .3)
            for dx in (-1, 1):
                add(P, bar((x, Y + 12, z), (x + dx * 3.6, Y + 15.4, z), .25, .25, 0), 'teal', .45)
        add(P, bar((-hw * .45, Y + 15.5, z), (hw * .45, Y + 15.5, z), .5, .4, 0), 'teal', .4)
    prof = [(-hw - 1, Y + 14.2), (-hw * .5, Y + 16.6), (0, Y + 17.4), (hw * .5, Y + 16.6), (hw + 1, Y + 14.2)]
    for (ax, ay), (bx_, by_) in zip(prof, prof[1:]):
        q = [V3((ax, ay, -L / 2)), V3((bx_, by_, -L / 2)), V3((bx_, by_, L / 2)), V3((ax, ay, L / 2))]
        bm = bmesh.new(); A = [bm.verts.new(p) for p in q]; Bq = [bm.verts.new(p + V3((0, -.3, 0))) for p in q]
        bm.faces.new(A); bm.faces.new(Bq[::-1])
        for k in range(4): j = (k + 1) % 4; bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        add(P, bm, 'teal' if abs(ax + bx_) > 1 else 'glass', .55, up=.2)
    for sx in (-1, 1): add(P, slab(sx * (hw + 1) - .3, sx * (hw + 1) + .3, Y + 13.4, Y + 14.4, -L / 2, L / 2), 'cream', .85)
    for z in (-L / 2 + 3, L / 2 - 3):
        add(P, tube([V3((0, Y + 16, z)), V3((0, Y + 12.4, z))], .05, sides=3), 'metal', .4)
        P.gadd(T(cyl(.6, .9, sides=8, y0=Y + 11.5, r2=.3), (0, 0, z)), 'lamp')
    add(P, T(box((5.5, .3, 1.6)), (-hw * .2, Y + 1.7, 0)), 'wood', .6)
    for sx in (-1, 1): add(P, T(box((.3, 1.7, 1.4)), (-hw * .2 + sx * 2.4, Y + .85, 0)), 'metal', .35)
    return P

# ================================================================== fountain, kiosks, stations
def fountain():
    """town square fountain: 8-sided basin (panelled cream wall, overhanging coping, inner wall), teal water,
    lathed centre column with two bowls and spill sheets, gold finial, 8 rim jets arcing in, 4 bollards"""
    P = Prop('Fountain'); R = 15.0; n = 8
    poly = [(math.cos(k * math.tau / n + math.pi / n) * R, math.sin(k * math.tau / n + math.pi / n) * R) for k in range(n)]
    for k in range(n):                                                                                     # basin wall segments
        a, b = poly[k], poly[(k + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        L = math.dist(a, b)
        add(P, T(box((L + .4, 3.0, 1.6)), (mid[0], .9, mid[1]), -ang), 'cream', .66)
        add(P, T(box((L + 1.4, .55, 2.6)), (mid[0], 2.6, mid[1]), -ang), 'cream', .86)
        nv = (mid[0] / R, mid[1] / R)
        add(P, T(box((L - 2.4, 1.6, .2)), (mid[0] * 1.03 + nv[0] * .4, 1.1, mid[1] * 1.03 + nv[1] * .4), -ang), 'cream', .55)
        if k % 2 == 0:
            jx, jz = mid[0] * .92, mid[1] * .92
            add(P, T(cyl(.45, .9, sides=8, y0=2.7), (jx, 0, jz)), 'yellow', .6)
            arcp = [V3((jx * (1 - t), 3.6 + math.sin(t * math.pi) * 6.0 - t * 2.5, jz * (1 - t))) for t in [i / 7 * .55 for i in range(8)]]
            P.gadd(tube(arcp, [.32, .3, .28, .26, .24, .22, .2, .18], sides=5), 'spray')
    P.add(T(ngon_prism([(x * .95, z * .95) for x, z in poly], -.4, 1.6), (0, 0, 0)), S('teal', base=.55, up=.25, jit=0))
    add(P, T(cyl(4.0, 1.6, sides=16, y0=.4), (0, 0, 0)), 'cream', .6)
    add(P, lathe([(3.0, 2.0), (2.6, 2.8), (1.6, 3.6), (1.4, 6.0), (2.0, 6.6), (7.2, 7.4), (7.5, 8.0), (6.8, 8.3), (1.4, 8.3), (0, 8.3)], n=16), 'cream', .74, smooth=True)
    add(P, lathe([(6.7, 8.3), (6.6, 8.35), (0, 8.35)], n=16), 'teal', .6)
    add(P, lathe([(1.2, 8.3), (1.0, 11.5), (1.4, 12.0), (3.8, 12.6), (4.0, 13.1), (3.4, 13.3), (0, 13.3)], n=12), 'cream', .78, smooth=True)
    add(P, lathe([(.9, 13.3), (.5, 15.0), (1.0, 15.6), (0, 17.6)], n=8), 'yellow', .65, smooth=True)
    for (r0, y0, r1, y1) in ((7.55, 7.9, 7.85, 5.6), (4.05, 12.9, 4.3, 10.9)):                              # short spill curtains
        bm = bmesh.new(); m = 16
        A = [bm.verts.new((math.cos(k * math.tau / m) * r0, y0, math.sin(k * math.tau / m) * r0)) for k in range(m)]
        Bq = [bm.verts.new((math.cos(k * math.tau / m) * r1, y1, math.sin(k * math.tau / m) * r1)) for k in range(m)]
        for k in range(m): j = (k + 1) % m; bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
        bm.normal_update()
        for f in bm.faces:
            c = f.calc_center_median()
            if f.normal.dot(V3((c.x, 0, c.z))) < 0: f.normal_flip()
        P.gadd(bm, 'spray')
    P.gadd(T(cyl(1.2, 1.2, sides=8, y0=17.0, r2=.2), (0, 0, 0)), 'spray')
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 8
        x, z = math.cos(a) * (R + 4), math.sin(a) * (R + 4)
        add(P, T(lathe([(.8, -.4), (.8, .3), (.6, .5), (.55, 2.6), (.75, 2.8), (.3, 3.4), (0, 3.5)], n=8), (x, 0, z)), 'metal', .4, smooth=True)
    return P

def job_board():
    """job board kiosk: timber frame on stone feet, shingled gable roof, a BLANK cork board both sides (GUI) with
    pinned notes in pastel colours (no writing), a lamp, and a small crate step"""
    P = Prop('JobBoard'); W = 10.0
    for sx in (-1, 1):
        add(P, slab(sx * W / 2 - .7, sx * W / 2 + .7, -.4, .8, -.7, .7), 'cream', .55)
        add(P, slab(sx * W / 2 - .4, sx * W / 2 + .4, .8, 10.4, -.4, .4), 'wood', .45)
        add(P, bar((sx * W / 2, 6.0, 0), (sx * (W / 2 - 1.6), 8.6, 0), .3, .3, 0), 'wood', .4)
    add(P, slab(-W / 2 + .4, W / 2 - .4, 2.6, 9.2, -.25, .25), 'wood', .7)                                    # cork board
    for zz in (-.3, .3):
        add(P, slab(-W / 2 + .4, W / 2 - .4, 2.4, 2.8, zz - .1, zz + .1), 'wood', .4)
        add(P, slab(-W / 2 + .4, W / 2 - .4, 9.0, 9.4, zz - .1, zz + .1), 'wood', .4)
    rng = random.Random(4)
    for zs in (-1, 1):
        for k in range(9):
            x = -3.2 + (k % 3) * 3.2 + rng.uniform(-.4, .4); y = 3.6 + (k // 3) * 1.9 + rng.uniform(-.2, .2)
            c = ('cream', 'yellow', 'teal', 'red', 'blue')[rng.randrange(5)]
            add(P, T(box((2.0, 1.5, .06)), (x, y, zs * .3), 0, 0, rng.uniform(-6, 6)), c, .82 if c == 'cream' else .7, up=0)
            add(P, T(ball(.12, 6, 3), (x, y + .5, zs * .36)), 'red', .6)
    for sx in (-1, 1):
        q = [V3((sx * .02, 12.4, -2.6)), V3((sx * (W / 2 + 1.4), 9.6, -2.6)), V3((sx * (W / 2 + 1.4), 9.6, 2.6)), V3((sx * .02, 12.4, 2.6))]
        bm = bmesh.new(); A = [bm.verts.new(p) for p in q]; Bq = [bm.verts.new(p + V3((0, .35, 0))) for p in q]
        bm.faces.new(A); bm.faces.new(Bq[::-1])
        for k in range(4): j = (k + 1) % 4; bm.faces.new((A[k], A[j], Bq[j], Bq[k]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); add(P, bm, 'red', .5, up=.2)
    add(P, slab(-.3, .3, 12.3, 12.9, -2.8, 2.8), 'wood', .5)
    add(P, slab(-W / 2 - .4, W / 2 + .4, 9.4, 10.4, -.4, .4), 'wood', .55)
    add(P, tube([V3((0, 10.4, -.4)), V3((0, 11.0, -1.6))], .08, sides=4), 'metal', .4)
    P.gadd(T(cyl(.45, .6, sides=6, y0=10.3, r2=.2), (0, 0, -1.6)), 'lamp')
    add(P, T(box((1.8, 1.4, 1.8)), (3.6, .3, -2.2), 15), 'wood', .6)
    P.board = (0.0, 5.9, -.32)
    return P

def bus_stop():
    """bus shelter: steel frame, glass back + end panels, curved roof, slatted bench, BLANK ad panel (GUI, lit),
    bus-stop pole with a blank round sign"""
    P = Prop('BusStop'); L, D, Hh = 12.0, 5.0, 8.4
    for x in (-L / 2, 0, L / 2):
        for z in (-D / 2 + .3, D / 2 - .3):
            add(P, slab(x - .2, x + .2, -.3, Hh, z - .2, z + .2), 'metal', .35)
    P.add(front_quad(-L / 2 + .2, L / 2 - .2, 1.0, Hh - .6, 0) if False else T(front_quad(-L / 2 + .2, L / 2 - .2, 1.0, Hh - .6, 0), (0, 0, D / 2 - .3)), S('glass', grad=(1, Hh, .7, .92), up=0, jit=0))
    for sx in (-1, 1):
        P.add(T(T(front_quad(-D / 2 + .5, D / 2 - .5, 1.0, Hh - .6, 0), (0, 0, 0), 90 * sx), (sx * L / 2, 0, 0)), S('glass', grad=(1, Hh, .7, .92), up=0, jit=0))
    for y in (1.0, Hh - .6): add(P, slab(-L / 2, L / 2, y - .15, y + .15, D / 2 - .45, D / 2 - .15), 'metal', .4)
    q = [(-D / 2 - 1.2, Hh + .2), (0, Hh + 1.0), (D / 2 + .2, Hh + .4)]
    for (az, ay), (bz, by) in zip(q, q[1:]):
        add(P, bar((-L / 2 - .5, (ay + by) / 2, (az + bz) / 2), (L / 2 + .5, (ay + by) / 2, (az + bz) / 2), math.hypot(bz - az, by - ay) + .1, .3, 0) if False else
            T(box((L + 1, .3, math.hypot(bz - az, by - ay) + .1)), (0, (ay + by) / 2, (az + bz) / 2), 0, -math.degrees(math.atan2(by - ay, bz - az))), 'teal', .5)
    add(P, slab(-L / 2 - .5, L / 2 + .5, Hh - .2, Hh + .3, -D / 2 - 1.3, -D / 2 - .9), 'yellow', .65)
    for k in range(3): add(P, slab(-L / 2 + 1.2, L / 2 - 3.4, 2.2, 2.4, -.4 + k * .6, -.1 + k * .6), 'wood', .6)
    for x in (-L / 2 + 1.6, L / 2 - 4): add(P, slab(x - .15, x + .15, -.3, 2.2, -.2, 1.2), 'metal', .4)
    add(P, slab(L / 2 - 2.8, L / 2 - .4, .6, 7.4, D / 2 - .45, D / 2 - .15), 'metal', .3)                     # ad panel
    P.gadd(T(front_quad(L / 2 - 2.6, L / 2 - .6, .9, 7.1, 0), (0, 0, D / 2 - .5)), 'walk')
    add(P, T(cyl(.18, 11, sides=8, y0=-.3), (-L / 2 - 2.5, 0, -D / 2)), 'metal', .45)
    add(P, T(cyl(1.4, .2, sides=16), (-L / 2 - 2.5, 10.2, -D / 2 - .1), 0, 90), 'red', .55)
    add(P, T(cyl(1.0, .3, sides=16), (-L / 2 - 2.5, 10.2, -D / 2 - .25), 0, 90), 'cream', .9)
    P.ad = (L / 2 - 1.6, 4.0, D / 2 - .5)
    return P

def bank():
    """bank: temple front on a stepped podium, 4 columns, pediment with a coin emblem, rusticated cream walls,
    bronze door, tall windows, attic band, small teal dome with lantern"""
    P = Prop('Bank'); W, D, H = 44.0, 38.0, 30.0; hw, hd = W / 2, D / 2; zf = -hd; G0 = 3.0
    add(P, slab(-hw - 1, hw + 1, -.6, G0, -hd - 1, hd + 1), 'cream', .55)
    for k in range(5): add(P, slab(-15, 15, -.6, .6 * (k + 1), -hd - 1 - 12 + k * 2.2, -hd - 1), 'cream', .68 + .03 * (k % 2))
    holes = [(-4, 4, G0, G0 + 14)] + [(sx * 13 - 2.6, sx * 13 + 2.6, G0 + 4, G0 + 18) for sx in (-1, 1)]
    holed_front(P, -hw, hw, G0, H, holes, zf, 'cream', .66)
    for k in range(7): add(P, slab(-hw, hw, G0 + 2 + k * 3.4, G0 + 2.25 + k * 3.4, zf - .15, zf), 'cream', .5, up=0)
    for sx in (-1, 1): window_unit(P, sx * 13, G0 + 4, 5.2, 14, zf, 'tall', wall_col='cream')
    add(P, slab(-4, 4, G0, G0 + 14, zf + 1.4, zf + 1.6), 'yellow', .45, up=0)
    for sx in (-1, 1):
        add(P, slab(sx * 2 - 1.7, sx * 2 + 1.7, G0 + .8, G0 + 12.6, zf + 1.25, zf + 1.4), 'yellow', .6, up=0)
        add(P, T(ball(.3, 6, 4), (sx * .6, G0 + 6.5, zf + 1.1)), 'yellow', .85)
    for sx in (-1, 1):
        add(P, slab(sx * 4 - (.6 if sx > 0 else 0), sx * 4 + (0 if sx > 0 else .6), G0, G0 + 14, zf, zf + 1.4), 'cream', .55, up=0)
    add(P, slab(-4, 4, G0 + 13.4, G0 + 14, zf, zf + 1.4), 'cream', .55, up=0)
    add(P, slab(-hw, hw, G0, H, -hd + .6, hd, drop=('-y',)), 'cream', .62, up=0)
    zp = zf - 8
    add(P, slab(-17, 17, G0 - .1, G0 + .4, zp - 2, zf), 'cream', .74)
    for k in range(4): column(P, -12 + k * 8, zp, G0 + .4, 22, 1.4)
    add(P, slab(-17, 17, G0 + 22.4, G0 + 26, zp - 2, zf + .5), 'cream', .8)
    add(P, slab(-17.6, 17.6, G0 + 25.6, G0 + 26.6, zp - 2.6, zf + .5), 'cream', .88)
    pediment(P, -17.6, 17.6, G0 + 26.6, zp - 2.6, 9, 9.6, tymp='cream')
    add(P, slab(-hw - .5, hw + .5, H, H + 1.4, -hd - .5, hd + .5), 'cream', .86)
    add(P, slab(-hw + 1, hw - 1, H + 1.4, H + 4, -hd + 1, hd - 1), 'cream', .7)
    add(P, T(cyl(7, 2.2, sides=16, y0=H + 4), (0, 0, 4)), 'cream', .8, smooth=True)
    add(P, lathe([(6.6, H + 6.2)] + [(6.6 * math.cos(math.pi / 2 * k / 6), H + 6.2 + 6 * math.sin(math.pi / 2 * k / 6)) for k in range(1, 7)], n=16) if False else
        T(lathe([(6.6, 0)] + [(6.6 * math.cos(math.pi / 2 * k / 6), 6 * math.sin(math.pi / 2 * k / 6)) for k in range(1, 7)], n=16), (0, H + 6.2, 4)), 'teal', .5, smooth=True)
    add(P, T(lathe([(1.2, 0), (1.2, 2), (.2, 3.6), (0, 4)], n=8), (0, H + 12, 4)), 'yellow', .7, smooth=True)
    from town_props import deco_window
    for k in range(3):
        a = -hd + D * (k + .5) / 3
        deco_window(P, '+x', a, G0 + 5, 4.4, 12, hw + .02); deco_window(P, '-x', a, G0 + 5, 4.4, 12, hw + .02)
    P.door = (0.0, G0, zf + 1.4)
    return P

def car_showroom():
    """car dealer: open-front display hall (no glass so the cars read), steel portal frame, chequered tile floor,
    accent-striped back wall, BLANK fascia sign band (GUI) on a deep canopy, service bay with a roll-up door,
    rooftop sign frame (blank), turntable podium"""
    P = Prop('CarShowroom'); W, D, H = 56.0, 36.0, 17.0; hw, hd = W / 2, D / 2; zf = -hd
    add(P, slab(-hw, hw, -.6, .6, -hd, hd), 'pave', .7)
    for i in range(int(W / 8)):
        for j in range(int(D / 8)):
            if (i + j) % 2: add(P, slab(-hw + i * 8, -hw + i * 8 + 8, .6, .64, -hd + j * 8, -hd + j * 8 + 8), 'slate', .62, up=0)
    add(P, slab(-hw, hw, .6, H, hd - .8, hd, drop=('-y',)), 'cream', .72, up=0)                              # back wall
    for k, c in enumerate(('red', 'yellow', 'red')): add(P, slab(-hw + .8, hw - .8, 3 + k * 1.4, 4 + k * 1.4, hd - 1.0, hd - .8), c, .6, up=0)
    for sx in (-1, 1):                                                                                      # side walls
        add(P, slab(sx * hw - (.8 if sx > 0 else 0), sx * hw + (0 if sx > 0 else .8), .6, H, -hd, hd), 'cream', .7, up=0)
    from town_props import deco_window
    for k in range(3): deco_window(P, '-x', -hd + D * (k + .5) / 3, 3, 6, 9, hw + .02)
    for x in (-hw + .7, -hw / 3, hw / 3, hw - 6.7):                                                           # portal frame
        add(P, slab(x - .7, x + .7, .6, H, zf - .2, zf + 1.2), 'metal', .4)
    add(P, slab(-hw - 2, hw + 2, H, H + 1.2, zf - 6, hd + .5), 'metal', .45)                                 # canopy roof
    add(P, slab(-hw - 2, hw + 2, H - 4.6, H + 1.2, zf - 6.6, zf - 6), 'red', .45, up=0)                       # fascia
    add(P, slab(-hw + 2, hw - 2, H - 4.0, H + .6, zf - 6.9, zf - 6.6), 'cream', .92, up=0)
    for x in (-hw + 1, hw - 1):
        add(P, bar((x, H - 4.6, zf - 6.2), (x, H - 10, zf), .4, .4, 0), 'metal', .4)
    # service bay on the right end with a roll-up door
    add(P, slab(hw - 6.0, hw - .8, .6, H, zf, zf + 1.0), 'cream', .7)
    add(P, slab(hw - 5.6, hw - 1.2, .6, 11, zf - .1, zf + .2), 'metal', .5)
    for k in range(10): add(P, slab(hw - 5.6, hw - 1.2, 1 + k * 1.0, 1.1 + k * 1.0, zf - .25, zf - .1), 'metal', .35, up=0)
    add(P, slab(hw - 6.0, hw - .8, 11, 12, zf - .5, zf + 1.0), 'red', .5)
    add(P, T(cyl(9, .7, sides=24, y0=.6), (-6, 0, 2)), 'cream', .88, smooth=True)                            # turntable
    add(P, T(torus(9, .3, n=24, sides=4), (-6, 1.3, 2)), 'yellow', .65)
    for x in (-18, 6):                                                                                       # rooftop sign frame (blank)
        add(P, slab(x - .3, x + .3, H + 1.2, H + 9, zf + 4, zf + 4.6), 'metal', .4)
    add(P, slab(-20, 8, H + 4, H + 9, zf + 3.8, zf + 4.2), 'red', .5, up=0)
    add(P, slab(-19.4, 7.4, H + 4.5, H + 8.5, zf + 3.6, zf + 3.8), 'cream', .92, up=0)
    P.sign = (0.0, H - 2.0, zf - 6.95); P.turntable = (-6.0, 1.3, 2.0)
    return P

def skyline(name, w, d, floors, mat='cream', style='bands', crown='flat', seed=1, fh=9.0):
    """cheap frame tower for the skyline ring: glass core + per-floor bands (or piers), setback crown, mast"""
    P = Prop(name); rng = random.Random(seed); hw, hd = w / 2, d / 2; H = floors * fh
    add(P, slab(-hw + .4, hw - .4, -.6, H, -hd + .4, hd - .4, drop=('-y',)), 'glass', .55, up=0)
    if style == 'bands':
        for f in range(0, floors + 1, 2):
            y = f * fh
            add(P, slab(-hw, hw, y - 1.6, y + 1.6, -hd, hd, drop=('-y', '+y')), mat, .62, up=0)
        add(P, slab(-hw, hw, -.6, 3, -hd, hd, drop=('-y', '+y')), mat, .5, up=0)
    else:
        n = max(2, int(w / 7))
        for sx, sz, L, along in ((0, -1, w, 'x'), (0, 1, w, 'x'), (-1, 0, d, 'z'), (1, 0, d, 'z')):
            m = max(2, int(L / 12))
            for k in range(m + 1):
                t = -L / 2 + L * k / m
                if along == 'x': add(P, slab(t - .9, t + .9, -.6, H, sz * hd - .5, sz * hd + .5), mat, .62, up=0)
                else: add(P, slab(sx * hw - .5, sx * hw + .5, -.6, H, t - .9, t + .9), mat, .62, up=0)
        for f in range(0, floors + 1, 2):
            add(P, slab(-hw - .2, hw + .2, f * fh - .4, f * fh + .6, -hd - .2, hd + .2, drop=('-y', '+y')), mat, .7, up=0)
    add(P, slab(-hw - .6, hw + .6, H, H + 1.6, -hd - .6, hd + .6), mat, .8)
    if crown == 'step':
        add(P, slab(-hw * .7, hw * .7, H + 1.6, H + 10, -hd * .7, hd * .7), mat, .66, up=0)
        add(P, slab(-hw * .4, hw * .4, H + 10, H + 16, -hd * .4, hd * .4), mat, .72, up=0)
        add(P, T(cyl(.4, 14, sides=6, y0=H + 16, r2=.15), (0, 0, 0)), 'metal', .5)
    elif crown == 'roof':
        add(P, frustum(-hw, hw, -hd, hd, H + 1.6, H + 9, hw * .6, hd * .6), 'teal', .5, up=.3)
    else:
        from town_props import water_tank
        water_tank(P, (rng.uniform(-hw * .4, hw * .4), H + 1.6, rng.uniform(-hd * .4, hd * .4)), 1.0)
    return P
