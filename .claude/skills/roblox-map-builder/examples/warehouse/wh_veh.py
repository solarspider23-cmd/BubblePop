# Northgate vehicles: forklift, pallet jack, box trailer, tractor unit (front = -z). Imported at the end of wh_props.
from kitlib import *
from wh_props import pallet_load
import math, random

def wheel(s, c, r, w, sides=16, hub_col='steel', tread=True, side=1):
    """tyre + rim + hub nuts, axle along x, centre c, outer face toward side (+1 = +x)"""
    hw = w / 2
    p = [(r * .62, -hw), (r * .9, -hw), (r * .98, -hw * .8), (r, -hw * .45), (r, hw * .45), (r * .98, hw * .8), (r * .9, hw), (r * .62, hw)]
    t = lathe(p, sides)
    if tread:
        for v in t.verts:
            if abs(v.co.y) < hw * .5:
                a = math.atan2(v.co.z, v.co.x); k = 1 + .025 * (1 if int((a + math.pi) / math.tau * sides * 2) % 2 else -1)
                v.co.x *= k; v.co.z *= k
    at(t, (0, 0, 0), (0, 0, 90)); at(t, c); s.add(t, S('rubber', base=.3, up=.2, jit=0), True)
    rim = lathe([(r * .62, side * hw * .9), (r * .55, side * hw * .5), (r * .3, side * hw * .35), (r * .3, side * hw * .5), (0, side * hw * .5)], 12)
    at(rim, (0, 0, 0), (0, 0, 90)); at(rim, c); s.add(rim, S(hub_col, base=.6, up=.25, jit=0), True)
    for k in range(5):
        a = k * math.tau / 5
        n = cyl(.06, .08, 6); at(n, (0, 0, 0), (0, 0, 90)); at(n, (c[0] + side * hw * .55, c[1] + math.cos(a) * r * .18, c[2] + math.sin(a) * r * .18))
        s.add(n, S('steel', base=.7, up=.2, jit=0))

def forklift(seed=0, load=None):
    """electric counterbalance forklift: yellow body, rounded counterweight, overhead guard, mast, forks (front = -z)"""
    P = Prop('Forklift%d' % seed); W2 = 1.65
    prof = [(-2.0, .55), (-2.0, 1.9), (-1.2, 2.25), (.9, 2.4), (1.5, 3.6), (2.55, 3.65), (3.05, 3.2), (3.2, 2.2), (3.05, .9), (2.6, .55)]
    body = prism_x(prof, -W2, W2)
    G.bevel(body, .12, 2, [e for e in body.edges if abs(abs(e.verts[0].co.x) - W2) < .01 and abs(abs(e.verts[1].co.x) - W2) < .01])
    P.add(body, SF(lambda c, n: ('yellow', .55) if c.y > 1.2 else ('rubber', .3), up=.2))
    for sx in (-1, 1):                                               # dark wheel wells
        P.add(quad(1.9, 1.3, 'x', sx * (W2 + .01), -1.55, 1.05, flip=sx < 0), S('rubber', base=.12, up=0, jit=0))
        P.add(quad(1.4, 1.0, 'x', sx * (W2 + .01), 2.2, .95, flip=sx < 0), S('rubber', base=.12, up=0, jit=0))
    s = Sub()
    for sx in (-1, 1):
        wheel(s, (sx * (W2 - .05), .78, -1.55), .78, .85, 18, 'yellow', side=sx)
        wheel(s, (sx * (W2 - .25), .56, 2.2), .56, .6, 14, 'steel', side=sx)
    s.emit(P)
    B(P, (3.0, .25, 2.4), (0, 2.42, -.4), 'rubber', .05, base=.3)    # ribbed floor plate
    for k in range(5): P.add(quad(2.6, .06, 'y', 2.56, 0, -1.4 + k * .45), S('rubber', base=.5, up=0, jit=0))
    P.add(quad(.9, .5, 'z', -2.01, 0, 1.4), S('paper', base=.85, up=0, jit=0))   # blank capacity plate
    B(P, (.3, .12, .9), (-(W2 + .1), 1.25, -.4), 'steel', .03, base=.5)       # step
    B(P, (2.6, .9, 1.7), (0, 2.85, 1.0), 'yellow', .2, base=.5)               # seat box / battery hood
    seat = rbox((1.7, .45, 1.6), .2, 2); at(seat, (0, 3.5, .95)); P.add(seat, S('rubber', base=.32, up=.25, jit=0), True)
    back = rbox((1.7, 1.6, .4), .18, 2); at(back, (0, 0, 0), (12, 0, 0)); at(back, (0, 4.4, 1.75)); P.add(back, S('rubber', base=.32, up=.25, jit=0), True)
    for sx in (-1, 1): B(P, (.25, .35, 1.0), (sx * .95, 3.95, 1.0), 'rubber', .1, base=.3)
    dash = prism_x([(-2.0, 1.9), (-2.0, 3.1), (-1.6, 3.4), (-1.1, 3.4), (-1.1, 2.3)], -1.3, 1.3); P.add(dash, S('yellow', base=.5, up=.25, jit=0))
    B(P, (1.2, .5, .1), (0, 3.25, -1.65), 'rubber', .05, base=.25, rot=(-35, 0, 0))
    glowbox(P, (.6, .25, .04), (0, 3.3, -1.71), 'go', (-35, 0, 0))
    T(P, [V(0, 3.4, -1.3), V(0, 4.3, -.75)], .09, 'rubber', 8, base=.3)
    sw = ring_tube(V(0, 0, 0), .55, .07, 20, 6, 'Y'); at(sw, (0, 0, 0), (-55, 0, 0)); at(sw, (0, 4.35, -.72)); P.add(sw, S('rubber', base=.25, up=.25, jit=0), True)
    for k in range(3):
        sp = tube([V(0, 0, 0), pol(.5, k * 120)], .04, 4); at(sp, (0, 0, 0), (-55, 0, 0)); at(sp, (0, 4.35, -.72)); P.add(sp, S('rubber', base=.25, up=.2, jit=0))
    P.add(at(sphere(.09, 8, 4), (.45, 4.55, -.55)), S('red', base=.5, up=.2, jit=0))
    for k in range(3):                                                # hydraulic levers
        x = .7 + k * .22; T(P, [V(x, 3.3, -1.45), V(x + .05, 4.05, -1.25)], .035, 'steel', 6, base=.6)
        P.add(at(sphere(.09, 8, 4), (x + .05, 4.1, -1.24)), S('rubber', base=.25, up=.25, jit=0))
    gy = 7.3                                                          # overhead guard
    for sx in (-1, 1):
        T(P, [V(sx * 1.45, 2.3, -1.85), V(sx * 1.45, gy, -1.55)], .12, 'rubber', 8, base=.3)
        T(P, [V(sx * 1.45, 3.6, 2.4), V(sx * 1.45, gy, 1.9)], .12, 'rubber', 8, base=.3)
        B(P, (.22, .22, 3.8), (sx * 1.45, gy, .2), 'rubber', .04, base=.3)
    for z in (-1.6, 2.0): B(P, (3.1, .22, .22), (0, gy, z), 'rubber', .04, base=.3)
    for k in range(6): B(P, (2.8, .08, .18), (0, gy + .02, -1.15 + k * .6), 'rubber', 0, base=.35)
    P.add(at(cyl(.22, .12, 10), (.9, gy + .1, 1.9)), S('rubber', base=.3, up=.2, jit=0))
    bc = lathe([(.18, 0), (.18, .3), (.12, .42), (0, .45)], 10); at(bc, (.9, gy + .22, 1.9)); P.gadd(bc, 'beacon')
    for sx in (-1, 1):
        B(P, (.5, .4, .3), (sx * 1.3, gy - .3, -1.85), 'rubber', .06, base=.3)
        glowbox(P, (.38, .26, .04), (sx * 1.3, gy - .3, -2.02), 'lamp')
        glowbox(P, (.25, .15, .04), (sx * 1.0, 3.0, 3.21), 'stop')
    B(P, (.6, .3, .1), (0, 3.2, 3.22), 'rubber', .03, base=.3)
    P.add(at(cyl(.12, .5, 8), (0, 1.0, 3.25)), S('steel', base=.6, up=.2, jit=0))
    mz = -2.45; MH = 7.6; fy = .25 if load is None else 1.6           # mast
    for sx in (-1, 1):
        o = ibeam(MH, .5, .32, .1, .08, 'y'); at(o, (sx * 1.2, .35, mz)); P.add(o, S('rubber', base=.35, up=.2, jit=0))
        i = ibeam(MH - .4, .4, .26, .08, .07, 'y'); at(i, (sx * .9, .45 + fy * .3, mz - .2)); P.add(i, S('steel', base=.35, up=.2, jit=0))
        T(P, [V(sx * .55, fy + .8, mz - .25), V(sx * .55, MH - .2, mz - .25), V(sx * .55, MH - .2, mz - .1)], .05, 'steel', 4, base=.25)
        P.add(at(cyl(.24, .3, 10), (sx * .55, MH - .35, mz - .2)), S('steel', base=.45, up=.2, jit=0))
    for y in (.6, 4.0, MH + .2): B(P, (2.7, .3, .4), (0, y, mz), 'rubber', .04, base=.33)
    P.add(at(cyl(.2, MH - 1.0, 10), (0, .6, mz + .15)), S('steel', base=.75, up=.25, jit=0), True)
    P.add(at(cyl(.28, .7, 10), (0, .5, mz + .15)), S('rubber', base=.35, up=.2, jit=0), True)
    B(P, (3.0, 1.1, .2), (0, fy + .7, mz - .45), 'rubber', .05, base=.3)       # carriage + load backrest
    for k in range(6): B(P, (.12, 2.8, .1), (-1.25 + k * .5, fy + 2.4, mz - .45), 'rubber', 0, base=.3)
    B(P, (3.0, .14, .14), (0, fy + 3.8, mz - .45), 'rubber', .02, base=.3)
    for sx in (-1, 1):
        f = prism_x([(0, 0), (0, 1.3), (.16, 1.3), (.16, .14), (3.9, .1), (4.0, .02), (4.0, 0)], -.22, .22)
        at(f, (0, 0, 0), (0, 180, 0)); at(f, (sx * .8, fy, mz - .55)); P.add(f, S('steel', base=.32, up=.25, jit=0))
    if load: pallet_load(load, seed, False, 3.6).emit(P, (0, fy + .12, mz - 2.6))
    return P

def pallet_jack(seed=0):
    """hand pallet truck: twin forks, pump body, tiller handle (forks toward -z)"""
    P = Prop('PalletJack%d' % seed)
    for sx in (-1, 1):
        f = prism_x([(-3.6, 0.0), (-3.6, .1), (-3.4, .26), (0, .26), (0, 0.0)], -.28, .28); at(f, (sx * .85, .08, 0)); P.add(f, S('yellow', base=.5, up=.25, jit=0))
        w = cyl(.13, .32, 10, 0, y0=-.16); at(w, (0, 0, 0), (0, 0, 90)); at(w, (sx * .85, .14, -3.3)); P.add(w, S('rubber', base=.4, up=.2, jit=0))
    B(P, (2.3, .55, .7), (0, .45, .35), 'yellow', .1, base=.5)
    P.add(at(cyl(.28, 1.0, 12), (0, .7, .45)), S('rubber', base=.3, up=.2, jit=0), True)
    s = Sub(); wheel(s, (-.22, .3, .55), .3, .3, 14, 'steel', side=-1); wheel(s, (.22, .3, .55), .3, .3, 14, 'steel', side=1); s.emit(P)
    T(P, [V(0, 1.6, .5), V(0, 4.0, 1.3)], .07, 'rubber', 8, base=.3)
    for sx in (-1, 1): T(P, [V(0, 4.0, 1.3), V(sx * .55, 4.1, 1.35), V(sx * .6, 4.6, 1.55)], .07, 'rubber', 8, base=.3)
    T(P, [V(-.6, 4.6, 1.55), V(.6, 4.6, 1.55)], .1, 'rubber', 8, base=.35)
    T(P, [V(.2, 4.3, 1.4), V(.1, 4.45, 1.32)], .04, 'red', 6, base=.5)
    return P
