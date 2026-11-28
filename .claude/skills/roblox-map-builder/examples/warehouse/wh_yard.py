# Northgate truck yard: box trailer, tractor unit, weld-mesh fence, yard light, bin, cones, chocks, dock stair.
# Imported at the end of wh_props. Yard props are built on y 0 = yard surface (the map places them at y -4).
from kitlib import *
from wh_props import pallet_load
from wh_veh import wheel
import math, random

def axle_set(s, z, x=3.1, r=1.6, w=1.7, hub='steel'):
    for sx in (-1, 1): truck_wheel(s, (sx * x, r, z), r, w, sx, dual=True)

def truck_wheel(s, c, r, w, side, dual=False):
    """truck wheel: deep-sidewall tyre with tread blocks, dished steel disc with 6 hand holes, raised hub, 10 wheel nuts,
    a hub cap; dual = twin tyres (one wider tyre with a groove) on the rear axles. Axle along x, outer face toward side."""
    hw = w / 2; n = 22
    p = [(r * .58, -hw), (r * .86, -hw), (r * .95, -hw * .86), (r, -hw * .6), (r, hw * .6), (r * .95, hw * .86), (r * .86, hw), (r * .58, hw)]
    t = lathe(p, n)
    for v in t.verts:                                                # tread blocks
        if abs(v.co.y) < hw * .65:
            a = math.atan2(v.co.z, v.co.x); k = 1 + .035 * (1 if int((a + math.pi) / math.tau * n * 2) % 2 else -1)
            v.co.x *= k; v.co.z *= k
    at(t, (0, 0, 0), (0, 0, 90)); at(t, c); s.add(t, S('rubber', base=.28, up=.15, jit=0), True)
    if dual: s.add(at(ring_tube(V(0, 0, 0), r * 1.0, .06, n, 4, 'X'), c), S('rubber', base=.08, up=0, jit=0), True)
    o = side * hw * .82                                              # disc face sits a little inside the tyre wall
    disc = lathe([(r * .6, o * 1.0), (r * .56, o * .9), (r * .42, o * .72), (r * .3, o * .78), (r * .22, o * 1.02), (r * .1, o * 1.08), (0, o * 1.08)], 18)
    at(disc, (0, 0, 0), (0, 0, 90)); at(disc, c); s.add(disc, S('steel', base=.66, up=.2, jit=0), True)
    for k in range(6):                                               # hand holes
        a = k * math.tau / 6 + .26
        h = cyl(r * .07, .04, 8, 0, y0=-.02); at(h, (0, 0, 0), (0, 0, 90))
        at(h, (c[0] + o * .77 + side * .01, c[1] + math.cos(a) * r * .36, c[2] + math.sin(a) * r * .36)); s.add(h, S('rubber', base=.05, up=0, jit=0))
    for k in range(10):                                              # wheel nuts on the raised hub
        a = k * math.tau / 10
        nut = cyl(.055, .12, 6); at(nut, (0, 0, 0), (0, 0, 90))
        at(nut, (c[0] + o * 1.02 + side * .03, c[1] + math.cos(a) * r * .17, c[2] + math.sin(a) * r * .17)); s.add(nut, S('steel', base=.8, up=.2, jit=0))
    cap = cyl(r * .09, .14, 10, 0); at(cap, (0, 0, 0), (0, 0, 90)); at(cap, (c[0] + o * 1.08 + side * .05, c[1], c[2])); s.add(cap, S('steel', base=.85, up=.2, jit=0))

def wheel_arch(P, c, R, w, col):
    """moulded wheel-arch liner over the top half of a tyre: a curved strip with a lip, attached under the cab"""
    bm = bmesh.new(); rows = []
    for i in range(13):
        a = math.radians(20 + i * 140 / 12)
        y, z = math.sin(a) * R, -math.cos(a) * R
        rows.append([bm.verts.new((c[0] + dx, c[1] + y, c[2] + z)) for dx in (-w / 2, w / 2)])
    for A, Bq in zip(rows, rows[1:]): bm.faces.new((A[0], A[1], Bq[1], Bq[0]))
    bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=.12)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    P.add(bm, S(col, base=.25, up=.2, jit=0), True)

def truck_mirrors(P, sx, hw, fz, col):
    """main + wide-angle mirrors: sculpted housings (body-colour backs, black rims) stacked on one vertical bar that is
    held off the A-pillar by an upper and a lower arm; glass faces rearward and toes in toward the driver"""
    x = sx * (hw + 1.0); zf = fz(10.5) + .35
    T(P, [V(x, 12.1, zf), V(x, 8.0, zf)], .07, 'rubber', 8, base=.25)            # mount bar
    for y in (11.7, 8.4):                                                          # arms back to the A-pillar
        T(P, [V(sx * (hw - .05), y + .1, fz(y) + .9), V(sx * (hw + .55), y + .05, fz(y) + .45), V(x, y, zf)], .07, 'rubber', 8, base=.25)
        P.add(at(rbox((.35, .45, .5), .12, 1), (sx * (hw + .02), y + .1, fz(y) + .9)), S('rubber', base=.22, up=.2, jit=0))
    for yc, h, wd in ((10.35, 2.3, .95), (8.75, .95, .85)):
        hs = rbox((wd, h, .5), .2, 2)
        for v in hs.verts:                                                          # rounded, slightly bulged back
            if v.co.z < 0: v.co.z -= .12 * (1 - (v.co.x / (wd / 2)) ** 2)
        at(hs, (0, 0, 0), (0, -sx * 12, 0)); at(hs, (x + sx * .05, yc, zf - .02)); P.add(hs, S(col, base=.5, up=.2, jit=0), True)
        rim = rbox((wd + .06, h + .06, .14), .08, 1); at(rim, (0, 0, 0), (0, -sx * 12, 0)); at(rim, (x + sx * .05, yc, zf + .24))
        P.add(rim, S('rubber', base=.2, up=.2, jit=0))
        gl = quad(wd - .16, h - .16, 'z', 0, 0, 0, flip=True); at(gl, (0, 0, 0), (0, -sx * 12, 0)); at(gl, (x + sx * .05, yc, zf + .32))
        P.add(gl, S('glass', base=.62, up=0, jit=0))


def box_trailer(doors='open', seed=0):
    """13.6 m box semi-trailer: aluminium-panel body with post ribs, rear doors (open = swung flat on the sides, cargo
    visible), chassis rails, crossmembers, tri-axle bogie, mudguards, side guards, landing legs + crank, rear bumper +
    lights, marker lights, kingpin plate. Rear (doors) toward -z, kingpin end +z. Floor 4.0 over the yard."""
    P = Prop('Trailer%s' % doors.capitalize()); L, W, y0, y1 = 43.0, 8.0, 4.0, 12.6; hl, hw = L / 2, W / 2; rng = random.Random(seed)
    body = box((W, y1 - y0, L), .05)
    if doors == 'open': bmesh.ops.delete(body, geom=[f for f in body.faces if f.calc_center_median().z < -hl + .1], context='FACES')
    at(body, (0, (y0 + y1) / 2, 0)); P.add(body, SF(lambda c, n: ('cladding', .82) if abs(n.y) < .5 else ('cladding', .7), up=.05))
    for k in range(22):                                                  # side posts
        z = -hl + 1 + k * (L - 2) / 21
        for sx in (-1, 1): P.add(quad(.22, y1 - y0 - .8, 'x', sx * (hw + .012), z, (y0 + y1) / 2, flip=sx < 0), S('cladding', base=.6, up=0, jit=0))
    for y in (y0 + .2, y1 - .2):
        for sx in (-1, 1): B(P, (.18, .45, L), (sx * (hw + .05), y, 0), 'steel', 0, base=.6)
    for sx in (-1, 1):                                                   # amber side marker lights
        for k in range(5): P.gadd(at(box((.06, .15, .3), 0), (sx * (hw + .16), y0 + .2, -hl + 4 + k * 9)), 'beacon')
    if doors == 'open':                                                  # interior: dark walls, floor, a few pallets inside
        P.add(quad(W - .4, L - .5, 'y', y0 + .15, 0, 0), S('pallet', base=.32, up=0, jit=0))
        inner = box((W - .3, y1 - y0 - .3, L - .4), 0); bmesh.ops.reverse_faces(inner, faces=list(inner.faces))
        inner.normal_update(); bmesh.ops.delete(inner, geom=[f for f in inner.faces if f.calc_center_median().z < -hl + .5 or f.normal.y > .5], context='FACES')
        at(inner, (0, (y0 + y1) / 2, 0)); P.add(inner, S('cladding', base=.42, up=.1, jit=0))
        for k in range(3):
            for sx in (-1, 1):
                if rng.random() < .8: pallet_load(rng.choice(['wrapped', 'cartons']), rng.randint(0, 99), True, 4.0).emit(P, (sx * 1.95, y0 + .15, hl - 3 - k * 4.0), [(0, 90, 0)])
        for sx in (-1, 1):                                               # doors swung back flat against the sides
            d = box((.2, y1 - y0 - .3, W / 2 - .1), 0); at(d, (sx * (hw + .35), (y0 + y1) / 2, -hl + W / 4 + .1)); P.add(d, S('cladding', base=.78, up=.1, jit=0))
            for k in range(2):
                T(P, [V(sx * (hw + .5), y0 + .4, -hl + .8 + k * 1.8), V(sx * (hw + .5), y1 - .4, -hl + .8 + k * 1.8)], .07, 'steel', 6, base=.6)
            P.add(at(box((.2, .5, .5), 0), (sx * (hw + .2), y1 - 1.5, -hl + .2)), S('steel', base=.4, up=.2, jit=0))
    else:
        P.add(quad(.05, y1 - y0 - .4, 'z', -hl - .03, 0, (y0 + y1) / 2), S('rubber', base=.1, up=0, jit=0))
        for x in (-2.8, -1.2, 1.2, 2.8): T(P, [V(x, y0 + .4, -hl - .12), V(x, y1 - .4, -hl - .12)], .07, 'steel', 6, base=.6)
    for sx in (-1, 1): B(P, (.4, y1 - y0, .5), (sx * (hw - .15), (y0 + y1) / 2, -hl - .05), 'steel', 0, base=.5)     # rear frame
    B(P, (W, .6, .5), (0, y1 - .25, -hl - .05), 'steel', 0, base=.5)
    B(P, (W, .5, .6), (0, y0 - .1, -hl), 'steel', 0, base=.45)
    # chassis + crossmembers + kingpin plate
    for sx in (-1, 1):
        r = ibeam(L - 1, 1.4, .5, .12, .14, 'z'); at(r, (sx * 1.6, y0 - .8, -hl + .5)); P.add(r, S('rubber', base=.3, up=.2, jit=0))
    for k in range(10): B(P, (W - .4, .4, .3), (0, y0 - .3, -hl + 2 + k * 4.2), 'rubber', 0, base=.3)
    B(P, (5.0, .2, 6.0), (0, y0 - .25, hl - 3.5), 'steel', 0, base=.4)
    P.add(at(cyl(.3, .6, 10, 0, y0=-.6), (0, y0 - .3, hl - 4.0)), S('steel', base=.5, up=.2, jit=0))
    # tri-axle bogie with mudguards
    s = Sub()
    for z in (-hl + 7, -hl + 10.5, -hl + 14): axle_set(s, z)
    s.emit(P)
    for z in (-hl + 7, -hl + 10.5, -hl + 14): T(P, [V(-3, 1.6, z), V(3, 1.6, z)], .2, 'rubber', 8, base=.3)
    for sx in (-1, 1):
        g = prism_x([(-hl + 5, 3.6), (-hl + 5, 3.9), (-hl + 16, 3.9), (-hl + 16, 3.6)], -.9, .9); at(g, (sx * 3.1, 0, 0)); P.add(g, S('rubber', base=.28, up=.2, jit=0))
        for z in (-hl + 5.2, -hl + 15.8): B(P, (1.7, 1.6, .08), (sx * 3.1, 2.8, z), 'rubber', 0, base=.2)
        for y in (1.6, 2.6): B(P, (.15, .35, 18), (sx * (hw - .25), y, -hl + 26), 'steel', 0, base=.55)   # side underrun guards
        for z in (-hl + 18, -hl + 26, -hl + 34): B(P, (.2, 2.4, .2), (sx * (hw - .35), 2.3, z), 'steel', 0, base=.45)
    # landing legs + crank + sand shoes
    for sx in (-1, 1):
        B(P, (.5, 3.6, .5), (sx * 2.6, 2.0, hl - 9), 'rubber', .03, base=.3)
        B(P, (.35, 1.0, .35), (sx * 2.6, .6, hl - 9), 'steel', .03, base=.5)
        P.add(drop_bottom(at(box((1.0, .2, 1.4), .04), (sx * 2.6, .1, hl - 9))), S('rubber', base=.25, up=.2, jit=0))
    T(P, [V(-2.6, 2.6, hl - 9), V(-4.2, 2.6, hl - 9), V(-4.2, 2.0, hl - 9)], .08, 'steel', 6, base=.55)
    T(P, [V(-2.6, 3.2, hl - 9), V(2.6, 3.2, hl - 9)], .1, 'steel', 6, base=.45)
    # rear bumper + light clusters + plate patch
    B(P, (W - 1.0, .45, .4), (0, 2.0, -hl + .4), 'steel', .04, base=.45)
    for sx in (-1, 1):
        B(P, (.4, 2.0, .3), (sx * 3.2, 3.0, -hl + .5), 'steel', 0, base=.45)
        B(P, (1.6, .6, .3), (sx * 2.6, 3.3, -hl + .1), 'rubber', .05, base=.25)
        glowbox(P, (.6, .4, .05), (sx * 2.2, 3.3, -hl - .06), 'stop')
        P.add(quad(.5, .4, 'z', -hl - .06, sx * 2.9, 3.3), S('beam', base=.6, up=0, jit=0))
    return P

def tractor_unit(col='green', seed=0):
    """cab-over tractor: high-roof raked cab with round front corners, wrap-round windscreen + side windows, doors, grille, bumper +
    headlights, mirrors, steps, chassis rails, fuel + AdBlue tanks, front + twin rear axles, fifth wheel, exhaust, mudflaps.
    Front = -z. Ground y 0."""
    P = Prop('Tractor%s' % col.capitalize()); hw = 3.9
    cz0, cz1, cy0, cyT = -9.4, -1.6, 3.4, 13.4                      # cab box (high-roof sleeper)
    RK, RC = .7, 1.0                                                # front rake at the roof, vertical corner radius
    def fz(y): return cz0 + (y - cy0) / (cyT - cy0) * RK
    def corner(x):
        e = abs(x) - (hw - RC)
        return 0.0 if e <= 0 else RC - math.sqrt(max(RC * RC - e * e, 0))
    def surf(x, y, off=0.0): return V(x, y, fz(y) + corner(x) - off)
    def panel(x0, x1, y0, y1, off, colr, v, nx=10, glow=None):
        """a decal skin that follows the cab front: raked face + wrapped round corners"""
        bm = bmesh.new(); rows = []
        for y in (y0, y1):
            rows.append([bm.verts.new(surf(x0 + (x1 - x0) * i / nx, y, off)) for i in range(nx + 1)])
        for i in range(nx): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
        bm.normal_update()
        for f in bm.faces:
            if f.normal.z > 0: f.normal_flip()
        if glow: P.gadd(bm, glow)
        else: P.add(bm, S(colr, base=v, up=.1, jit=0), True)
    # cab shell: box, raked front, big round front corners, rounded roof edges
    cab = box((2 * hw, cyT - cy0, cz1 - cz0), 0); at(cab, (0, (cy0 + cyT) / 2, (cz0 + cz1) / 2))
    G.bevel(cab, RC, 5, [e for e in cab.edges if all(abs(abs(v.co.x) - hw) < .01 and abs(v.co.z - cz0) < .01 for v in e.verts)])
    G.bevel(cab, .45, 3, [e for e in cab.edges if all(abs(v.co.y - cyT) < .01 for v in e.verts)])
    for v in cab.verts:
        if v.co.z < (cz0 + cz1) / 2: v.co.z += (v.co.y - cy0) / (cyT - cy0) * RK
    cab.normal_update(); bmesh.ops.delete(cab, geom=[f for f in cab.faces if f.normal.y < -.9], context='FACES')
    P.add(cab, S(col, base=.55, up=.2, jit=0), True)
    # windscreen: black bonded surround + big glass that wraps into the corners; sun visor; parked wipers
    panel(-hw + .25, hw - .25, 8.0, 12.25, .02, 'rubber', .14, 16)
    panel(-hw + .45, hw - .45, 8.22, 12.05, .04, 'glass', .2, 16)
    vis = box((2 * hw - .9, .35, .7), .06); at(vis, (0, 12.6, fz(12.6) - .25)); P.add(vis, S('rubber', base=.22, up=.2, jit=0))
    for x0 in (-2.6, .3): T(P, [surf(x0, 8.32, .08), surf(x0 + 2.2, 8.5, .08)], .05, 'rubber', 4, base=.15)
    for k in range(3): P.gadd(at(box((.3, .14, .1), 0), (-.8 + k * .8, cyT - .25, fz(cyT - .25) + .05)), 'beacon')   # roof marker lights
    # grille: dark mesh field, body-colour slats, a bright top trim; blank centre plate (no logo)
    panel(-2.75, 2.75, 4.75, 7.65, .02, 'rubber', .1, 8)
    for k in range(5):
        y = 5.05 + k * .58; b = box((5.4, .16, .14), .03); at(b, (0, y, fz(y) - .08)); P.add(b, S(col, base=.48, up=.25, jit=0))
    b = box((5.6, .12, .12), .03); at(b, (0, 7.72, fz(7.72) - .06)); P.add(b, S('steel', base=.82, up=.25, jit=0))
    b = box((1.1, .55, .12), .04); at(b, (0, 6.75, fz(6.75) - .12)); P.add(b, S('steel', base=.78, up=.25, jit=0))
    # headlight clusters wrapping the lower corners: housing, lens, LED daytime strip
    for sx in (-1, 1):
        a, c = (2.85, hw - .08) if sx > 0 else (-(hw - .08), -2.85)
        panel(a, c, 3.55, 5.05, .03, 'rubber', .2, 6)
        panel(a + .12 * sx if sx < 0 else a + .12, c - .12 if sx > 0 else c + .12, 3.7, 4.75, .06, 'glass', .6, 6)
        panel(a + .12 if sx > 0 else a + .12, c - .12 if sx > 0 else c - .12, 4.82, 4.94, .07, None, 0, 6, glow='lamp')
    # bumper: body-colour upper, dark spoiler with intake and fog lights; corner step pockets
    bp = rbox((2 * hw + .2, 1.1, 1.2), .3, 2); at(bp, (0, 3.0, cz0 + .2)); P.add(bp, S(col, base=.5, up=.2, jit=0))
    sp = rbox((2 * hw + .1, .75, 1.1), .2, 1); at(sp, (0, 2.1, cz0 + .3)); P.add(sp, S('rubber', base=.25, up=.2, jit=0))
    P.add(quad(3.6, .35, 'z', cz0 - .26, 0, 2.15), S('rubber', base=.06, up=0, jit=0))
    for sx in (-1, 1):
        f = cyl(.24, .1, 12, 0, y0=-.05); at(f, (0, 0, 0), (90, 0, 0)); at(f, (sx * 2.9, 2.15, cz0 - .27)); P.add(f, S('glass', base=.7, up=0, jit=0))
    # sides: big door window + quarter light, door shut lines, handle, steps, mirrors (glass faces rearward)
    for sx in (-1, 1):
        x = sx * (hw + .012)
        P.add(quad(3.4, 3.7, 'x', x, cz0 + 2.4, 10.1, flip=sx < 0), S('rubber', base=.14, up=0, jit=0))
        P.add(quad(3.1, 3.45, 'x', x + sx * .01, cz0 + 2.5, 10.1, flip=sx < 0), S('glass', base=.22, up=0, jit=0))
        P.add(quad(.08, 3.45, 'x', x + sx * .02, cz0 + 1.3, 10.1, flip=sx < 0), S('rubber', base=.12, up=0, jit=0))
        for zz in (cz0 + 4.3, cz0 + .75): P.add(quad(.06, 8.0, 'x', x, zz, 8.0, flip=sx < 0), S('rubber', base=.12, up=0, jit=0))
        P.add(quad(4.2, .06, 'x', x, cz0 + 2.5, 4.05, flip=sx < 0), S('rubber', base=.12, up=0, jit=0))
        B(P, (.2, .22, .9), (sx * (hw + .12), 7.6, cz0 + 3.7), 'rubber', .05, base=.3)
        for k in range(3): B(P, (.7, .14, 1.4), (sx * (hw - .15), .95 + k * .95, cz0 + 1.75), 'steel', .03, base=.6)
        truck_mirrors(P, sx, hw, fz, col)
    # chassis, tanks, axles, fifth wheel, exhaust, mudflaps
    for sx in (-1, 1):
        r = ibeam(17.5, 1.2, .45, .1, .12, 'z'); at(r, (sx * 1.6, 2.6, -9.0)); P.add(r, S('rubber', base=.3, up=.2, jit=0))
    tk = lathe([(1.0, -2.8), (1.05, -2.6), (1.05, 2.6), (1.0, 2.8), (0, 2.8)], 14); at(tk, (0, 0, 0), (90, 0, 0)); at(tk, (-2.9, 2.2, 1.0))
    P.add(tk, S('steel', base=.8, up=.3, jit=0), True)
    for z in (-1.6, 3.4): P.add(at(ring_tube(V(0, 0, 0), 1.08, .06, 14, 4, 'Z'), (-2.9, 2.2, z)), S('rubber', base=.25, up=.2, jit=0), True)
    B(P, (1.6, 1.6, 2.0), (2.9, 2.2, .4), 'rubber', .1, base=.3)
    s = Sub()
    for sx in (-1, 1): truck_wheel(s, (sx * 3.15, 1.65, -5.0), 1.65, 1.15, sx, dual=False)
    for z in (2.8, 6.4): axle_set(s, z, 3.1)
    s.emit(P)
    for sx in (-1, 1):
        wheel_arch(P, (sx * 3.15, 1.65, -5.0), 2.05, 1.5, 'rubber')
        g = prism_x([(1.0, 3.4), (1.0, 3.7), (8.2, 3.7), (8.2, 3.4)], -.95, .95); at(g, (sx * 3.1, 0, 0)); P.add(g, S('rubber', base=.28, up=.2, jit=0))
        B(P, (1.7, 1.8, .06), (sx * 3.1, 1.9, 8.2), 'rubber', 0, base=.22)
    fw = cyl(2.3, .45, 18, .05); at(fw, (0, 3.6, 4.6)); P.add(fw, S('rubber', base=.32, up=.25, jit=0), True)
    P.add(quad(1.0, 1.6, 'y', 4.06, 0, 5.6), S('rubber', base=.08, up=0, jit=0))
    P.add(at(cyl(.32, 8.5, 10), (2.9, 4.0, -1.2)), S('steel', base=.75, up=.3, jit=0), True)
    P.add(at(cyl(.38, 1.6, 10), (2.9, 9.0, -1.2)), S('steel', base=.6, up=.2, jit=0), True)
    B(P, (2.0, 1.2, .3), (0, 6.2, -1.45), 'rubber', .05, base=.25)                                     # cab back + air lines
    for k, c in enumerate(('red', 'yellow', 'plastic')):
        T(P, [V(-.6 + k * .5, 5.8, -1.25), V(-.6 + k * .5, 4.6, 1.2), V(-.6 + k * .5, 4.2, 2.6)], .07, c, 6, base=.5, cap=False)
    return P

def fence_panel(L=10.0, H=8.0):
    """3D weld-mesh fence panel between two posts: vertical wires, double horizontals, V-fold stiffening ribs"""
    P = Prop('FencePanel%d' % int(L))
    P.add(drop_bottom(at(box((.35, H + .6, .35), .02), (-L / 2, (H + .6) / 2, 0)), 0), S('green', base=.32, up=.2, jit=0))
    P.add(at(box((.45, .1, .45), 0), (-L / 2, H + .65, 0)), S('green', base=.3, up=.2, jit=0))
    P.add(drop_bottom(at(cyl(.5, .3, 8), (-L / 2, 0, 0)), 0), S('concrete', base=.45, up=.2, jit=0))
    n = int(L / .5)
    for k in range(1, n):
        x = -L / 2 + k * L / n
        w = box((.05, H - .4, .05), 0); bmesh.ops.delete(w, geom=[f for f in w.faces if abs(f.normal.y) > .9], context='FACES')
        at(w, (x, .3 + (H - .4) / 2, 0)); P.add(w, S('green', base=.35, up=.1, jit=0))
    for y in (.4, 2.4, 5.3, H - .1):
        for dz in (-.05, .05): P.add(at(box((L, .05, .05), 0), (0, y, dz)), S('green', base=.35, up=.1, jit=0))
    for y in (1.4, 3.9, 6.6):                                              # V folds
        for dz, dy in ((-.12, -.15), (-.12, .15)):
            P.add(at(box((L, .05, .05), 0), (0, y + dy, dz)), S('green', base=.35, up=.1, jit=0))
    return P

def yard_light(h=30.0):
    """galvanised tapered column on a bolted base, outreach arm, two LED floodlight heads"""
    P = Prop('YardLight')
    P.add(drop_bottom(at(lathe([(1.2, 0), (1.2, .8), (.9, 1.0), (0, 1.0)], 10), (0, 0, 0)), 0), S('concrete', base=.45, up=.2, jit=0))
    P.add(at(box((1.3, .12, 1.3), 0), (0, 1.06, 0)), S('steel', base=.5, up=.2, jit=0))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(at(cyl(.08, .3, 6), (sx * .5, 1.1, sz * .5)), S('steel', base=.6, up=.2, jit=0))
    P.add(lathe([(.42, 1.1), (.24, h), (0, h)], 12), S('steel', base=.58, up=.2, jit=0), True)
    T(P, [V(0, h - 1.0, 0), V(0, h - .2, -1.6), V(0, h - .2, -3.0)], .16, 'steel', 8, base=.55)
    for sx in (-1, 1):
        hd = rbox((1.8, .5, 1.3), .1, 1); at(hd, (0, 0, 0), (-20, 0, 0)); at(hd, (sx * 1.1, h - .55, -3.0)); P.add(hd, S('rubber', base=.3, up=.2, jit=0))
        for k in range(5): P.add(at(box((.06, .35, 1.1), 0), (sx * 1.1 - .7 + k * .35, h - .2, -3.0), (-20, 0, 0)), S('rubber', base=.35, up=.2, jit=0))
        g = box((1.6, .03, 1.1), 0); at(g, (0, 0, 0), (-20, 0, 0)); at(g, (sx * 1.1, h - .82, -3.1)); P.gadd(g, 'lamp')
    T(P, [V(-1.1, h - .2, -3.0), V(1.1, h - .2, -3.0)], .1, 'steel', 6, base=.55)
    return P

def yard_bin(col='green', seed=0):
    """1100 l steel trade-waste bin: tapered body, two lids, push handles, 4 castors"""
    P = Prop('YardBin%d' % seed); w, d = 5.2, 3.6
    body = hull([V(sx * w / 2 * k, y, z) for sx in (-1, 1) for (y, z, k) in ((1.0, -d / 2 + .5, .95), (1.0, d / 2 - .3, .95), (4.6, -d / 2, 1), (4.6, d / 2, 1))])
    P.add(body, S(col, base=.45, up=.25, jit=0))
    B(P, (w + .3, .3, d + .3), (0, 4.6, 0), col, .08, base=.5)
    for sx in (-1, 1):
        lid = box((w / 2 - .05, .15, d + .4), .05); at(lid, (sx * w / 4, 4.85, 0), (sx * -3 if seed else 0, 0, 0)); P.add(lid, S('rubber', base=.28, up=.25, jit=0))
        T(P, [V(sx * w / 2 * .9, 3.6, -d / 2 - .4), V(sx * w / 2 * .6, 3.6, -d / 2 - .4)], .1, 'steel', 6, base=.55)
        for sz in (-1, 1):
            P.add(at(cyl(.12, .5, 6), (sx * (w / 2 - .5), .6, sz * (d / 2 - .5))), S('steel', base=.5, up=.2, jit=0))
            c = cyl(.32, .25, 10, 0, y0=-.12); at(c, (0, 0, 0), (0, 0, 90)); at(c, (sx * (w / 2 - .5), .33, sz * (d / 2 - .5))); P.add(c, S('rubber', base=.3, up=.2, jit=0))
    for k in range(3): P.add(quad(w - .6, .08, 'z', -d / 2 + .3 - .01, 0, 1.8 + k * .9), S(col, base=.3, up=0, jit=0))
    return P

def traffic_cone(seed=0):
    P = Prop('Cone')
    P.add(drop_bottom(at(box((1.6, .15, 1.6), .1), (0, .075, 0)), 0), S('rubber', base=.25, up=.2, jit=0))
    P.add(lathe([(.62, .15), (.52, .6), (.12, 2.6), (0, 2.6)], 14), S('beam', base=.55, up=.25, jit=0), True)
    for y in (1.1, 1.75): P.add(lathe([(.62 - (y - .15) * .2 + .01, y), (.62 - (y + .3 - .15) * .2 + .01, y + .3)], 14), S('paper', base=.9, up=.2, jit=0), True)
    return P

def wheel_chock():
    P = Prop('WheelChock')
    P.add(prism_x([(-.7, 0), (.7, 0), (.7, .25), (-.5, 1.0), (-.7, 1.0)], -.5, .5), S('yellow', base=.55, up=.25, jit=0))
    T(P, [V(0, .6, .2), V(0, 1.4, .9)], .05, 'steel', 6, base=.6)
    return P

def dock_stair(h=4.0, w=5.0):
    """cast concrete stair from the yard up to the dock floor: steps with steel nosings, side upstands, galvanised rails.
    Origin = yard level at the bottom of the flight; rises toward -z (into the dock face)."""
    P = Prop('DockStair'); n = 6; r = h / n; t = 1.2
    for k in range(n):
        z0 = -k * t; y = (k + 1) * r
        st = box((w, y, t), 0); drop_bottom(at(st, (0, y / 2, z0 - t / 2)), 0); P.add(st, S('concrete', base=.55 - .02 * (k % 2), up=.2, jit=.02, seed=k))
        P.add(quad(w, .12, 'y', y + .003, 0, z0 - .08), S('steel', base=.55, up=0, jit=0))
    for sx in (-1, 1):
        P.add(at(prism_x([(.3, 0), (.3, .8), (-n * t, h + .8), (-n * t, 0)], -.3, .3), (sx * (w / 2 + .3), 0, 0)), S('concrete', base=.5, up=.2, jit=0))
        T(P, [V(sx * (w / 2 + .3), 4.2, .2), V(sx * (w / 2 + .3), h + 3.6, -n * t)], .1, 'steel', 6, base=.65)
        for k in (0, n):
            z = -k * t; T(P, [V(sx * (w / 2 + .3), .8 + k * r, z), V(sx * (w / 2 + .3), 3.6 + k * r + .6, z)], .1, 'steel', 6, base=.65)
    return P
