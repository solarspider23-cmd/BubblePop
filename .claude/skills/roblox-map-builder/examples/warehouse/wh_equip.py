# Northgate mezzanine, site office and floor equipment. Imported at the end of wh_props.
from kitlib import *
from wh_props import pallet_load, pallet_sub, PW, PD, PH
import math, random

def rail_run(P, a, b, h=3.6, step=3.4, col='yellow', kick=True):
    """handrail along a straight line a->b on a deck: posts, top rail, knee rail, kick plate"""
    a, b = V(*a), V(*b); d = b - a; L = d.length; n = max(1, int(L / step))
    for k in range(n + 1):
        p = a + d * (k / n); T(P, [p, p + V(0, h, 0)], .09, col, 6, base=.6)
    for y in (h, h / 2): T(P, [a + V(0, y, 0), b + V(0, y, 0)], .09, col, 6, base=.62, cap=False)
    if kick:
        ex = d.normalized(); nrm = V(-ex.z, 0, ex.x) * .03
        c = (a + b) / 2 + V(0, .25, 0); bm = box((L, .5, .06) if abs(ex.x) > .5 else (.06, .5, L), 0); at(bm, c.to_tuple()); P.add(bm, S(col, base=.5, up=.2, jit=0))

def mezzanine(W=62.0, D=42.0, H=14.0):
    """steel mezzanine: SHS columns, main beams + C joists, chipboard deck, fascia, handrails + kick plates on the open
    south / west edges, an up-and-over pallet gate, a straight stair up the west side to a landing, LED panels under.
    Origin = floor centre of the deck footprint; front (-z) = north wall side; the open edges face +z (south) and -x (west)."""
    P = Prop('Mezzanine'); hw, hd = W / 2, D / 2; xs = [-hw + .6 + k * (W - 1.2) / 4 for k in range(5)]; zs = [-hd + .6 + k * (D - 1.2) / 3 for k in range(4)]
    for x in xs:
        for z in zs:
            c = box((.8, H - 1.6, .8), 0); drop_bottom(at(c, (x, (H - 1.6) / 2, z)), 0); P.add(c, S('steel', base=.45, up=.2, jit=0))
            P.add(drop_bottom(at(box((1.4, .1, 1.4), 0), (x, .05, z))), S('steel', base=.4, up=.2, jit=0))
            for sx in (-1, 1): P.add(at(cyl(.07, .15, 6), (x + sx * .5, .1, z + sx * .5)), S('steel', base=.6, up=.2, jit=0))
    for z in zs:                                                          # main beams (along x) on the column lines
        bm = ibeam(W, 1.2, .7, .12, .14, 'x'); at(bm, (-hw, H - 1.0, z)); P.add(bm, S('steel', base=.42, up=.2, jit=0))
    for k in range(int(W / 2.6) + 1):                                     # C joists along z
        x = -hw + .3 + k * (W - .6) / int(W / 2.6)
        P.add(at(box((.18, .7, D - .2), 0), (x, H - .05 - .35 - .3, 0)), S('steel', base=.5, up=.2, jit=0))
    deck = box((W, .3, D), 0); at(deck, (0, H - .15, 0)); P.add(deck, SF(lambda c, n: ('pallet', .56) if n.y > .5 else ('steel', .4), up=.05))
    for k in range(1, int(W / 8)):                                        # chipboard sheet joints
        P.add(quad(.04, D - .2, 'y', H + .005, -hw + k * 8.0), S('pallet', base=.38, up=0, jit=0))
    for k in range(1, int(D / 4)): P.add(quad(W - .2, .04, 'y', H + .005, 0, -hd + k * 4.0), S('pallet', base=.38, up=0, jit=0))
    for z, x0, x1 in ((hd, -hw, hw),):                                    # fascia channels on the open edges
        B(P, (x1 - x0, .9, .14), ((x0 + x1) / 2, H - .45, z + .07), 'steel', 0, base=.5)
    B(P, (.14, .9, D), (-hw - .07, H - .45, 0), 'steel', 0, base=.5)
    for x in (-hw + 10, -hw + 30, -hw + 50):                              # LED panels under the deck
        for z in (-hd + 10, hd - 10):
            P.add(at(box((3.6, .1, 1.8), 0), (x, H - 1.75, z)), S('steel', base=.75, up=.2, jit=0))
            P.gadd(at(box((3.3, .02, 1.5), 0), (x, H - 1.81, z)), 'lamp')
    # stair (outside the -x edge): x -hw-5.2..-hw-.2, from z hd+24 (floor) up to z hd (landing at deck height), landing z hd..hd-6
    sx0, sx1 = -hw - 5.4, -hw - .2; n = 20; run = 24.0; rise = H / n; tz = run / n
    for k in range(n):                                                    # checker-plate treads with nosings
        z = hd + run - (k + .5) * tz; y = (k + 1) * rise
        P.add(at(box((sx1 - sx0 - .5, .12, tz + .1), 0), ((sx0 + sx1) / 2, y - .06, z)), S('steel', base=.48, up=.2, jit=0))
        P.add(quad(sx1 - sx0 - .5, .08, 'y', y + .002, (sx0 + sx1) / 2, z + tz / 2 - .1), S('yellow', base=.6, up=0, jit=0))
    for x in (sx0 + .15, sx1 - .15):                                      # stringers
        P.add(prism_x([(hd + run + .4, 0), (hd + run - .4, 0), (hd - .2, H - .9), (hd - .2, H + .1), (hd + .8, H + .1)], x - .14, x + .14), S('steel', base=.42, up=.2, jit=0))
    land = box((sx1 - sx0, .3, 6.2), 0); at(land, ((sx0 + sx1) / 2, H - .15, hd - 3.1)); P.add(land, S('steel', base=.46, up=.2, jit=0))
    for x in (sx0 + .3, sx1 - .3):
        for z in (hd - 5.9, hd - .3):
            c = box((.6, H - .3, .6), 0); drop_bottom(at(c, (x, (H - .3) / 2, z)), 0); P.add(c, S('steel', base=.45, up=.2, jit=0))
    for x in (sx0 + .1, sx1 - .1):                                        # stair handrails (raked)
        for y in (3.4, 1.7):
            T(P, [V(x, y + rise, hd + run - .3), V(x, H + y, hd + .2)], .08, 'yellow', 6, base=.6, cap=True)
        for k in range(0, n + 1, 5):
            z = hd + run - k * tz; y = k * rise
            T(P, [V(x, y, z), V(x, y + 3.4, z)], .08, 'yellow', 6, base=.6)
    rail_run(P, (sx0 + .1, H, hd - 6.1), (sx0 + .1, H, hd - .2))
    rail_run(P, (sx0 + .1, H, hd - 6.1), (sx1, H, hd - 6.1))
    # deck handrails: south edge (with a pallet-gate gap) + west edge (gap at the landing)
    gx0, gx1 = 8.0, 15.0
    rail_run(P, (-hw + .1, H, hd - .1), (gx0, H, hd - .1)); rail_run(P, (gx1, H, hd - .1), (hw - .5, H, hd - .1))
    rail_run(P, (-hw + .1, H, -hd + 1.5), (-hw + .1, H, hd - 6.3))
    # up-and-over pallet gate: two hinged rail frames (one down at the edge, one up behind)
    for z, up in ((hd - .1, False), (hd - 4.0, True)):
        y0 = H
        for x in (gx0, gx1): T(P, [V(x, y0, z), V(x, y0 + 3.8, z)], .1, 'yellow', 6, base=.6)
        T(P, [V(gx0, y0 + 3.8, z), V(gx1, y0 + 3.8, z)], .1, 'yellow', 6, base=.6)
        T(P, [V(gx0, y0 + 1.9, z), V(gx1, y0 + 1.9, z)], .08, 'yellow', 6, base=.6)
    for x in (gx0, gx1): T(P, [V(x, H + 3.8, hd - .1), V(x, H + 4.6, hd - 2.0), V(x, H + 3.8, hd - 4.0)], .08, 'yellow', 6, base=.55)
    B(P, (gx1 - gx0 + 1, .6, 3.6), ((gx0 + gx1) / 2, H + .3, hd - 2.0), 'steel', 0, base=.36)       # gate floor plate
    return P

def site_office(W=30.0, D=16.0, H=9.0):
    """modular mezzanine office: framed white panels, a ribbon of glazing with half-drawn blinds, door, roof + AC unit.
    Front (-z) faces the hall; built on the deck (y 0 = deck top)."""
    P = Prop('SiteOffice'); hw, hd = W / 2, D / 2
    gy0, gy1 = 3.2, 7.4
    def wall(L, axis, off, door=None):
        """wall panel with a glazing ribbon; axis 'z' = along x at z off, 'x' = along z at x off"""
        segs = [(-L / 2, L / 2)]
        for a, b, y0, y1, col, v in ((-L / 2, L / 2, 0, gy0, 'cladding', .76), (-L / 2, L / 2, gy1, H, 'cladding', .78)):
            sz = (b - a, y1 - y0, .3) if axis == 'z' else (.3, y1 - y0, b - a)
            c = ((a + b) / 2, (y0 + y1) / 2, off) if axis == 'z' else (off, (y0 + y1) / 2, (a + b) / 2)
            P.add(drop_bottom(at(box(sz, 0), c), 0) if y0 == 0 else at(box(sz, 0), c), S(col, base=v, up=.15, jit=0))
        n = max(2, int(L / 5))
        for k in range(n + 1):                                            # mullions
            t = -L / 2 + k * L / n
            c = (t, (gy0 + gy1) / 2, off) if axis == 'z' else (off, (gy0 + gy1) / 2, t)
            P.add(at(box((.25, gy1 - gy0, .4) if axis == 'z' else (.4, gy1 - gy0, .25), 0), c), S('rubber', base=.3, up=.2, jit=0))
        g = box((L, gy1 - gy0, .08) if axis == 'z' else (.08, gy1 - gy0, L), 0); at(g, (0, (gy0 + gy1) / 2, off) if axis == 'z' else (off, (gy0 + gy1) / 2, 0)); P.add(g, S('glass', base=.35, up=.1, jit=0))
        for k in range(n):                                                # blinds: pale slat bands, part drawn
            t = -L / 2 + (k + .5) * L / n; drop = (1.0 + 2.2 * ((k * 7) % 3) / 2)
            for j in range(int(drop / .22)):
                y = gy1 - .15 - j * .22
                bl = box((L / n - .3, .1, .05) if axis == 'z' else (.05, .1, L / n - .3), 0); at(bl, (t, y, off + .1) if axis == 'z' else (off + .1, y, t))
                P.add(bl, S('paper', base=.78, up=.1, jit=0))
        for y in (gy0, gy1):                                              # transom + sill caps
            P.add(at(box((L, .2, .5) if axis == 'z' else (.5, .2, L), 0), (0, y, off) if axis == 'z' else (off, y, 0)), S('cladding', base=.55, up=.2, jit=0))
    wall(W, 'z', -hd); wall(W, 'z', hd); wall(D, 'x', -hw); wall(D, 'x', hw)
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(drop_bottom(at(box((.6, H, .6), 0), (sx * hw, H / 2, sz * hd)), 0), S('cladding', base=.6, up=.2, jit=0))
    B(P, (W + 1.2, .6, D + 1.2), (0, H + .3, 0), 'cladding', .06, base=.62)
    B(P, (5.0, 2.0, 3.0), (hw - 6, H + 1.6, 2), 'cladding', .12, base=.7)        # AC condenser
    P.add(at(ring_tube(V(0, 0, 0), 1.0, .08, 16, 4, 'Y'), (hw - 6, H + 2.62, 2)), S('rubber', base=.25, up=.2, jit=0), True)
    P.add(quad(1.8, 1.8, 'y', H + 2.61, hw - 6, 2), S('rubber', base=.12, up=0, jit=0))
    # door in the west wall (toward the stair landing)
    B(P, (.4, 7.2, 3.6), (-hw - .2, 3.6, -hd + 3.5), 'plastic', .03, base=.55)
    T(P, [V(-hw - .5, 3.4, -hd + 2.2), V(-hw - .5, 3.4, -hd + 2.9)], .07, 'steel', 6, base=.7)
    return P

def ibc_tote(seed=0):
    """1000 l IBC: steel pallet base, white HDPE tank, galvanised tube cage, filler cap, bottom valve"""
    P = Prop('IBC%d' % seed); rng = random.Random(seed); w, d, h = 3.75, 3.15, 3.6
    B(P, (w, .5, d), (0, .25, 0), 'steel', .03, base=.42)
    for x in (-w / 2 + .3, 0, w / 2 - .3): P.add(quad(.9, .32, 'z', -d / 2 - .01, x * .6, .2), S('rubber', base=.15, up=0, jit=0))
    tank = rbox((w - .3, h - .9, d - .3), .45, 2); at(tank, (0, .5 + (h - .9) / 2, 0)); P.add(tank, S('paper', base=.7 - rng.random() * .1, up=.25, jit=0), True)
    fill = .3 + rng.random() * .5                                          # liquid level line through the tank
    P.add(quad(w - .5, .05, 'z', -d / 2 + .13, 0, .6 + (h - 1.0) * fill), S('plastic', base=.5, up=0, jit=0))
    for x in [-w / 2 + .12 + k * (w - .24) / 5 for k in range(6)]:
        for z in (-d / 2 + .1, d / 2 - .1): T(P, [V(x, .5, z), V(x, h, z)], .05, 'steel', 4, base=.7, cap=False)
    for z in [-d / 2 + .12 + k * (d - .24) / 4 for k in range(5)]:
        for x in (-w / 2 + .1, w / 2 - .1): T(P, [V(x, .5, z), V(x, h, z)], .05, 'steel', 4, base=.7, cap=False)
    for y in (.55, 1.6, 2.6, h):
        for z in (-d / 2 + .1, d / 2 - .1): T(P, [V(-w / 2 + .1, y, z), V(w / 2 - .1, y, z)], .06, 'steel', 4, base=.72, cap=False)
        for x in (-w / 2 + .1, w / 2 - .1): T(P, [V(x, y, -d / 2 + .1), V(x, y, d / 2 - .1)], .06, 'steel', 4, base=.72, cap=False)
    P.add(at(cyl(.5, .3, 12), (0, h - .3, 0)), S('plastic', base=.45, up=.2, jit=0), True)
    v = cyl(.28, .5, 10); at(v, (0, 0, 0), (90, 0, 0)); at(v, (0, .95, -d / 2 + .1)); P.add(v, S('rubber', base=.3, up=.2, jit=0))
    P.add(at(box((.6, .2, .2), .04), (0, 1.0, -d / 2 - .25)), S('red', base=.5, up=.2, jit=0))
    P.add(quad(1.0, .7, 'z', -d / 2 + .05, -.9, 2.3), S('paper', base=.95, up=0, jit=0))
    return P

def mesh_stillage(seed=0, full=True):
    """steel weld-mesh stillage cage with corner posts / feet; optionally full of cartons"""
    P = Prop('Stillage%d' % seed); rng = random.Random(seed); w, d, h = 3.8, 3.2, 3.6
    for sx in (-1, 1):
        for sz in (-1, 1):
            B(P, (.25, h + .5, .25), (sx * w / 2, (h + .5) / 2, sz * d / 2), 'steel', .02, base=.42)
            P.add(at(cyl(.2, .3, 6), (sx * w / 2, h + .5, sz * d / 2)), S('steel', base=.5, up=.2, jit=0))
    B(P, (w, .2, d), (0, .6, 0), 'steel', 0, base=.45)
    for y in (.6, h + .4):
        for sz in (-1, 1): B(P, (w, .14, .1), (0, y, sz * d / 2), 'steel', 0, base=.5)
        for sx in (-1, 1): B(P, (.1, .14, d), (sx * w / 2, y, 0), 'steel', 0, base=.5)
    for k in range(1, 12):                                                # mesh: vertical wires all round, a few horizontals
        x = -w / 2 + k * w / 12
        for sz in (-1, 1): P.add(at(box((.04, h - .2, .04), 0), (x, .6 + (h - .2) / 2, sz * d / 2)), S('steel', base=.62, up=.2, jit=0))
    for k in range(1, 10):
        z = -d / 2 + k * d / 10
        for sx in (-1, 1): P.add(at(box((.04, h - .2, .04), 0), (sx * w / 2, .6 + (h - .2) / 2, z)), S('steel', base=.62, up=.2, jit=0))
    for y in (1.5, 2.5, 3.4):
        for sz in (-1, 1): P.add(at(box((w, .04, .04), 0), (0, y, sz * d / 2)), S('steel', base=.62, up=.2, jit=0))
        for sx in (-1, 1): P.add(at(box((.04, .04, d), 0), (sx * w / 2, y, 0)), S('steel', base=.62, up=.2, jit=0))
    if full:
        for k in range(rng.randint(5, 8)):
            cw, ch, cd = rng.uniform(1.0, 1.7), rng.uniform(.8, 1.3), rng.uniform(1.0, 1.4)
            x = rng.uniform(-w / 2 + cw / 2 + .2, w / 2 - cw / 2 - .2); z = rng.uniform(-d / 2 + cd / 2 + .2, d / 2 - cd / 2 - .2)
            y = .7 + (k // 3) * 1.25
            if y + ch > h: continue
            b = box((cw, ch, cd), .02); at(b, (x, y + ch / 2, z), (0, rng.uniform(-8, 8), 0)); P.add(b, S('cardboard', base=rng.uniform(.45, .6), up=.18, jit=.03))
    return P

def conveyor(L=24.0, seed=0):
    """gravity roller conveyor: side channels, rollers, legs with cross braces + feet, end stop, two cartons riding it"""
    P = Prop('Conveyor%d' % int(L)); w, y = 3.4, 3.0; rng = random.Random(seed)
    for sx in (-1, 1): B(P, (.15, .6, L), (sx * w / 2, y - .1, 0), 'steel', .02, base=.55)
    n = int(L / .55)
    for k in range(n):
        r = cyl(.17, w - .2, 8, 0, y0=-(w - .2) / 2); at(r, (0, 0, 0), (0, 0, 90)); at(r, (0, y, -L / 2 + .3 + k * (L - .6) / (n - 1))); P.add(r, S('steel', base=.72, up=.25, jit=0), True)
    for k in range(int(L / 6) + 1):
        z = -L / 2 + .3 + k * (L - .6) / int(L / 6)
        for sx in (-1, 1):
            B(P, (.18, y - .4, .18), (sx * (w / 2 - .05), (y - .4) / 2, z), 'steel', 0, base=.45)
            P.add(drop_bottom(at(box((.45, .08, .45), 0), (sx * (w / 2 - .05), .04, z))), S('rubber', base=.3, up=.2, jit=0))
        T(P, [V(-w / 2, 1.0, z), V(w / 2, 1.0, z)], .07, 'steel', 4, base=.5)
    B(P, (w, .8, .15), (0, y + .2, L / 2), 'yellow', .03, base=.6)
    for k in range(2):
        cw = rng.uniform(1.6, 2.2); ch = rng.uniform(1.0, 1.5); z = -L / 4 + k * L / 2.5
        b = box((cw, ch, cw * .8), .02); at(b, (rng.uniform(-.2, .2), y + .17 + ch / 2, z)); P.add(b, S('cardboard', base=.55, up=.18, jit=.03))
        P.add(quad(cw + .02, .3, 'y', y + .17 + ch + .01, 0, z), S('cardboard', base=.4, up=0, jit=0))
    return P

def packing_bench(seed=0):
    """steel packing bench: worktop, undershelf with cartons, upright frame with a light bar, film roll + tape gun, monitor"""
    P = Prop('PackBench%d' % seed); w, d, h = 9.0, 3.6, 3.0
    for sx in (-1, 1):
        for sz in (-1, 1): B(P, (.2, h, .2), (sx * (w / 2 - .2), h / 2, sz * (d / 2 - .2)), 'steel', 0, base=.5)
        B(P, (.2, 4.2, .2), (sx * (w / 2 - .2), h + 2.1, d / 2 - .2), 'steel', 0, base=.5)
    top = box((w, .2, d), .03); at(top, (0, h + .1, 0)); P.add(top, SF(lambda c, n: ('pallet', .62) if n.y > .5 else ('steel', .5), up=.05))
    B(P, (w - .4, .1, d - .4), (0, .8, 0), 'steel', 0, base=.45)
    B(P, (w - .2, .3, .5), (0, h + 4.2, d / 2 - .2), 'steel', .03, base=.55)
    P.gadd(at(box((w - .8, .02, .3), 0), (0, h + 4.04, d / 2 - .2)), 'lamp')
    B(P, (w - .4, .1, .8), (0, h + 2.3, d / 2 - .5), 'steel', 0, base=.5)                 # upper shelf
    for k in range(3): B(P, (1.3, .9, .7), (-3 + k * 1.5, h + 2.8, d / 2 - .55), 'cardboard', .02, base=.5 + .04 * k)
    for k in range(3): B(P, (1.8, 1.1, 1.6), (-2.8 + k * 2.4, 1.4, 0), 'cardboard', .02, base=.48 + .05 * k)
    roll = cyl(.35, 1.6, 12, 0, y0=-.8); at(roll, (0, 0, 0), (0, 0, 90)); at(roll, (2.5, h + .55, -.6)); P.add(roll, S('paper', base=.82, up=.2, jit=0), True)
    tg = rbox((.35, .9, .7), .1, 1); at(tg, (.6, h + .55, .2), (0, 30, 0)); P.add(tg, S('red', base=.5, up=.2, jit=0), True)
    P.add(at(ring_tube(V(0, 0, 0), .3, .1, 12, 6, 'X'), (.6, h + .75, .2)), S('cardboard', base=.4, up=.2, jit=0), True)
    B(P, (2.6, .2, 1.6), (-2.5, h + .3, -.5), 'cardboard', .02, base=.55)                  # flat carton on the top
    T(P, [V(-3.3, h + .2, .9), V(-3.3, h + 1.2, .9)], .08, 'rubber', 6, base=.3)            # monitor + stand
    B(P, (2.0, 1.3, .15), (-3.3, h + 1.8, .85), 'rubber', .04, base=.25, rot=(8, 0, 0))
    P.add(quad(1.8, 1.1, 'z', .76, -3.3, h + 1.8), S('plastic', base=.25, up=0, jit=0))
    B(P, (1.4, .1, .5), (-3.3, h + .25, .1), 'rubber', .02, base=.3)
    B(P, (1.6, .25, 1.6), (3.4, h + .32, .4), 'steel', .05, base=.6)                        # scale
    return P

def stretch_wrapper(seed=0):
    """turntable pallet wrapper: low base + rotating disc, mast with film carriage, control panel; a pallet half-wrapped"""
    P = Prop('StretchWrapper'); r = 3.2
    base = cyl(r + .4, .35, 28, .05); drop_bottom(base, 0); P.add(base, S('steel', base=.45, up=.2, jit=0), True)
    P.add(at(cyl(r, .12, 28), (0, .35, 0)), S('rubber', base=.3, up=.25, jit=0), True)
    B(P, (2.4, .4, 3.0), (r + 1.4, .2, 0), 'steel', .05, base=.45)
    B(P, (1.0, 11.0, 1.0), (r + 1.4, 5.5, .8), 'yellow', .06, base=.58)
    B(P, (1.4, 1.6, 1.8), (r + .9, 4.5, .8), 'steel', .1, base=.55)
    roll = cyl(.42, 1.8, 14, 0, y0=-.9); at(roll, (r + .4, 4.5, .1)); P.add(roll, S('paper', base=.85, up=.2, jit=0), True)
    for z in (-.6, .2): T(P, [V(r + .6, 3.9, z), V(r + .6, 5.1, z)], .1, 'rubber', 8, base=.4)
    B(P, (1.6, 2.6, .9), (r + 1.4, 3.0, -1.3), 'yellow', .08, base=.55)
    P.add(quad(1.2, 1.6, 'z', -1.76, r + 1.4, 3.2), S('rubber', base=.15, up=0, jit=0))
    for k, col in enumerate(('green', 'red')): P.add(at(cyl(.15, .1, 8), (r + 1.1 + k * .6, 2.0, -1.76), (-90, 0, 0)), S(col, base=.5, up=.2, jit=0))
    pallet_load('cartons', seed + 3, False, 4.0).emit(P, (0, .47, 0), [(0, 20, 0)])
    return P

def charger_unit(seed=0):
    """wall-mounted forklift battery charger with a cable + plug hanging on a hook (wall prop)"""
    P = Prop('Charger%d' % seed)
    B(P, (2.6, 3.6, 1.4), (0, 6.0, -.7), 'cladding', .1, base=.72)
    for k in range(6): P.add(quad(1.6, .08, 'z', -1.41, 0, 6.8 - k * .25), S('rubber', base=.25, up=0, jit=0))
    P.gadd(at(box((.25, .25, .04), 0), (-.8, 7.4, -1.42)), 'go')
    P.add(quad(.9, .6, 'z', -1.41, .5, 5.0), S('rubber', base=.15, up=0, jit=0))
    T(P, [V(.6, 4.2, -.8), V(.8, 2.6, -1.4), V(-.2, 1.4, -1.6), V(-.8, 2.6, -1.0), V(-.9, 3.8, -.4)], .14, 'rubber', 8, base=.25, cap=False)
    B(P, (.6, .8, .45), (-.9, 4.0, -.4), 'red', .08, base=.45)
    return P

def fire_point():
    """fire point (wall prop): hose-reel cabinet, two extinguishers on brackets, a blank red sign board"""
    P = Prop('FirePoint')
    B(P, (3.4, 3.4, 1.4), (0, 6.2, -.7), 'red', .08, base=.5)
    P.add(quad(2.9, 2.9, 'z', -1.41, 0, 6.2), S('red', base=.38, up=0, jit=0))
    P.add(at(ring_tube(V(0, 0, 0), 1.05, .18, 20, 6, 'Z'), (0, 6.2, -1.45)), S('red', base=.6, up=.2, jit=0), True)
    for x in (-2.6, 2.6):
        e = lathe([(0, 0), (.42, 0), (.45, .1), (.45, 2.0), (.36, 2.3), (.15, 2.45), (0, 2.45)], 14); at(e, (x, .9, -.55)); P.add(e, S('red', base=.55, up=.3, jit=0), True)
        P.add(at(box((.3, .3, .4), .04), (x, 3.45, -.55)), S('rubber', base=.3, up=.2, jit=0))
        T(P, [V(x + .1, 3.4, -.55), V(x + .5, 2.6, -.95), V(x + .45, 1.7, -.98)], .06, 'rubber', 6, base=.25)
        P.add(quad(.75, .7, 'z', -.99, x, 1.9), S('paper', base=.92, up=0, jit=0))
        B(P, (.6, .2, .5), (x, .9, -.4), 'steel', .03, base=.6)
    B(P, (2.4, 1.5, .1), (0, 9.2, -.05), 'red', .03, base=.55)
    return P

def safety_barrier(L=10.0, ped=True):
    """yellow polymer-style traffic barrier: posts with black-band caps, two rails (ped: a lower kick rail too)"""
    P = Prop('Barrier%d' % int(L)); n = max(1, int(L / 5))
    for k in range(n + 1):
        x = -L / 2 + k * L / n
        P.add(drop_bottom(at(cyl(.32, 3.6, 12), (x, 0, 0)), 0), S('yellow', base=.6, up=.25, jit=0), True)
        P.add(at(lathe([(.34, 3.6), (.34, 3.75), (.2, 3.85), (0, 3.85)], 12), (x, 0, 0)), S('rubber', base=.25, up=.25, jit=0), True)
        P.add(at(lathe([(.42, 0), (.42, .12), (.3, .18), (0, .18)], 12), (x, 0, 0)), S('rubber', base=.3, up=.2, jit=0), True)
        for k2 in range(4): P.add(at(cyl(.07, .1, 6), (x + .3 * math.cos(k2 * 1.57), .15, .3 * math.sin(k2 * 1.57))), S('steel', base=.6, up=.2, jit=0))
    for y in ((1.9, 3.0) + ((.6,) if ped else ())):
        T(P, [V(-L / 2, y, 0), V(L / 2, y, 0)], .26, 'yellow', 10, base=.62, cap=False)
    for k in range(n):
        x = -L / 2 + (k + .5) * L / n
        for y in (1.9, 3.0): P.add(at(ring_tube(V(0, 0, 0), .27, .03, 10, 4, 'X'), (x, y, 0)), S('rubber', base=.2, up=.2, jit=0), True)
    return P

def bollard():
    P = Prop('Bollard')
    P.add(drop_bottom(at(lathe([(.45, 0), (.45, 3.6), (.36, 3.95), (0, 4.05)], 14), (0, 0, 0)), 0), S('yellow', base=.62, up=.3, jit=0), True)
    for y in (2.6, 3.1): P.add(at(lathe([(.46, y), (.46, y + .25)], 14), (0, 0, 0)), S('rubber', base=.2, up=.2, jit=0), True)
    P.add(at(lathe([(0, .02), (.75, .02), (.75, .08), (0, .08)], 14), (0, 0, 0)), S('concrete', base=.4, up=.2, jit=0))
    return P
