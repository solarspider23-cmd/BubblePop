# Northgate structure + doors + the hero crane. Imported at the end of wh_props.
# Building: hall x -120..120, z -80..80; walls 1 thick (inner faces x +-119.5, z +-79.5); eaves 36, ridge 40 at z 0.
from kitlib import *
import math, random

EAVE, RIDGE, CHORD = 36.0, 40.0, 32.0          # roof top chord at the walls / ridge, truss bottom chord
RUNWAY_Y = 22.0                                 # crane rail top

def steel_column(h=34.5, bracket=False, guard=True, sides=(-1, 1)):
    """H-section column: base plate + anchor bolts + grout pad, cap plate, optional crane runway bracket, yellow guard"""
    P = Prop('SteelColumn%s%s%s' % ('B' if bracket else '', 'G' if guard else '', '' if len(sides) == 2 else 'N'))
    c = ibeam(h, 1.4, 1.2, .14, .16, 'y'); at(c, (0, .3, 0)); P.add(c, S('steel', base=.48, up=.2, jit=0))
    P.add(drop_bottom(at(box((2.2, .2, 2.2), .02), (0, .1, 0))), S('concrete', base=.5, up=.25, jit=0))
    P.add(at(box((1.9, .1, 1.9), 0), (0, .25, 0)), S('steel', base=.4, up=.2, jit=0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(at(cyl(.07, .25, 6), (sx * .75, .3, sz * .75)), S('steel', base=.65, up=.2, jit=0))
            P.add(at(cyl(.11, .06, 6), (sx * .75, .3, sz * .75)), S('steel', base=.55, up=.2, jit=0))
    P.add(at(box((1.6, .14, 1.6), 0), (0, h + .37, 0)), S('steel', base=.45, up=.2, jit=0))
    if bracket:                                                      # corbel bracket under the runway (both sides, -z and +z)
        for sz in sides:
            br = prism_x([(sz * .7, RUNWAY_Y - 4.0), (sz * .7, RUNWAY_Y - 1.6), (sz * 2.0, RUNWAY_Y - 1.6), (sz * 2.0, RUNWAY_Y - 2.0)], -.08, .08)
            P.add(br, S('steel', base=.45, up=.2, jit=0))
            B(P, (1.0, .1, 1.4), (0, RUNWAY_Y - 1.55, sz * 1.35), 'steel', 0, base=.5)
    if guard:                                                        # two-piece wrap guard with black bands
        g = box((2.0, 1.5, 2.0), .14); drop_bottom(at(g, (0, .75, 0)), 0); P.add(g, S('yellow', base=.6, up=.25, jit=0))
        for k in range(2):
            y = .35 + k * .65
            for f in ('z', 'x'):
                for sg in (-1, 1):
                    q = quad(2.02, .22, f, sg * 1.01, 0, y, flip=sg > 0)
                    P.add(q, S('rubber', base=.18, up=0, jit=0))
    return P

def roof_truss(span=160.0):
    """pitched lattice truss across the hall (along z), square-hollow chords + webs; sits on the column caps (y CHORD..)"""
    P = Prop('RoofTruss'); hs = span / 2; n = 20
    def top(z): return EAVE - 1.9 + (RIDGE - EAVE) * (1 - abs(z) / hs)
    def bar(a, b, r, v=.45):
        a, b = V(*a), V(*b); d = b - a; L = d.length
        bm = box((r, r, L), 0); bm.normal_update()
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=rot, verts=bm.verts); at(bm, ((a + b) / 2).to_tuple()); P.add(bm, S('steel', base=v, up=.2, jit=0))
    zs = [-hs + 1 + k * (span - 2) / n for k in range(n + 1)]
    for a, b in zip(zs, zs[1:]):
        bar((0, top(a), a), (0, top(b), b), .7)
        bar((0, CHORD, a), (0, CHORD, b), .6)
    for k, z in enumerate(zs):
        bar((0, CHORD, z), (0, top(z), z), .35, .5)
        if k < n:
            z2 = zs[k + 1]
            if (k < n / 2) == (k % 2 == 0): bar((0, CHORD, z), (0, top(z2), z2), .3, .5)
            else: bar((0, top(z), z), (0, CHORD, z2), .3, .5)
    for z in (-hs + 1.0, hs - 1.0):                                    # end posts standing on the wall columns
        B(P, (.8, top(z) - CHORD + .65, .8), (0, (top(z) + CHORD - .3 + .35) / 2, z), 'steel', 0, base=.42)
    return P

def high_bay(seed=0, drop=3.0):
    """LED high-bay 'UFO' lamp on a pendant rod: finned heat sink, driver, diffuser glow; origin at the lamp bottom"""
    P = Prop('HighBay%d' % seed)
    fins = lathe([(1.25, .15), (1.3, .45), (1.05, .75), (.55, .95), (.5, 1.25), (0, 1.25)], 16)
    for v in fins.verts:
        if v.co.y > .3:
            a = math.atan2(v.co.z, v.co.x); k = 1 + .05 * (1 if int((a + math.pi) / math.tau * 16 + .5) % 2 else -1)
            v.co.x *= k; v.co.z *= k
    P.add(fins, S('rubber', base=.35, up=.3, jit=0), True)
    P.add(lathe([(1.32, 0), (1.32, .15), (0, .15)], 16), S('steel', base=.7, up=.2, jit=0), True)
    P.gadd(lathe([(1.18, -.02), (0, -.02)], 16), 'lamp')
    P.add(at(box((.7, .4, .5), .05), (0, 1.45, 0)), S('steel', base=.75, up=.2, jit=0))
    P.add(at(cyl(.06, drop, 6), (0, 1.65, 0)), S('steel', base=.6, up=.2, jit=0))
    return P

def dock_door(state='open', seed=0):
    """loading dock: insulated roller door (open / half / closed) in a 10 x 12 opening, guide rails, coil box + motor,
    leveler plate in the floor, yellow guard posts, dock light arm, signal lights + push-button box inside; shelter pads +
    rubber bumpers outside. Wall prop: inner face at z 0 (room toward -z), wall 1 thick (exterior face z +1), floor y 0, yard y -4."""
    P = Prop('DockDoor%s' % state.capitalize()); OW, OH = 10.0, 12.0
    yb = {'open': OH - .6, 'half': 5.5, 'closed': 0.0}[state]
    for sx in (-1, 1):                                                 # steel guide channels
        B(P, (.5, OH + 1.5, .5), (sx * (OW / 2 + .25), (OH + 1.5) / 2, -.25), 'steel', .03, base=.5)
    B(P, (OW + 1.6, 1.8, 1.6), (0, OH + 1.4, -.8), 'steel', .08, base=.55)       # coil housing
    B(P, (1.2, 1.2, 1.0), (OW / 2 + 1.3, OH + 1.4, -.6), 'plastic', .1, base=.4)  # motor
    P.add(at(cyl(.3, .4, 10), (OW / 2 + .5, OH + 1.4, -1.0), (90, 0, 0)), S('steel', base=.4, up=.2, jit=0))
    if yb < OH - .7:                                                   # curtain: insulated slats, ribs on both faces
        h = OH - yb
        B(P, (OW - .05, h, .25), (0, yb + h / 2, .5), 'cladding', 0, base=.62)
        k = 0; y = yb + .35
        while y < OH - .2:
            P.add(quad(OW - .1, .07, 'z', .37, 0, y), S('cladding', base=.35, up=0, jit=0))
            P.add(quad(OW - .1, .07, 'z', .63, 0, y, flip=True), S('cladding', base=.4, up=0, jit=0))
            y += .7; k += 1
        B(P, (OW - .05, .2, .35), (0, yb + .1, .5), 'rubber', 0, base=.25)
        if state == 'half':
            for x in (-OW / 4, OW / 4): P.add(quad(1.4, .5, 'z', .36, x, yb + 2.0), S('glass', base=.35, up=0, jit=0))
    else:
        B(P, (OW - .05, .4, .3), (0, OH - .25, .5), 'rubber', 0, base=.25)
    lv = box((OW - .6, .12, 6.0), 0); drop_bottom(at(lv, (0, .0, -3.0)), -.06); P.add(lv, S('steel', base=.42, up=.15, jit=0))   # leveler deck
    for z in [-.4 - k * .55 for k in range(10)]: P.add(quad(OW - .9, .05, 'y', .065, 0, z), S('steel', base=.62, up=0, jit=0))
    for sx in (-1, 1):
        P.add(quad(.25, 6.0, 'y', .066, sx * (OW / 2 - .5), -3.0), S('yellow', base=.55, up=0, jit=0))
        B(P, (.6, 4.2, .6), (sx * (OW / 2 + 1.3), 2.1, -1.0), 'yellow', .1, base=.6)                     # guard posts
        for k in range(3): P.add(quad(.62, .25, 'z', -1.31, sx * (OW / 2 + 1.3), .8 + k * 1.2), S('rubber', base=.2, up=0, jit=0))
        P.add(at(sphere(.32, 10, 5), (sx * (OW / 2 + 1.3), 4.2, -1.0)), S('yellow', base=.6, up=.25, jit=0))
    for x in (-OW / 2 + .3, OW / 2 - .3):                              # lip hinge edge
        pass
    B(P, (OW - .4, .4, .15), (0, -.25, .07), 'steel', 0, base=.45)        # lip folded down at the doorway
    # outside: shelter pads + bumpers + steel edge angle on the dock face
    for sx in (-1, 1):
        B(P, (1.4, OH + 1.5, 2.2), (sx * (OW / 2 + .8), (OH + 1.5) / 2 - .5, 2.1), 'rubber', .25, base=.22)
        for k in range(3): P.add(quad(.12, OH, 'x', sx * (OW / 2 + .1), 2.1, OH / 2 - .5, flip=sx > 0), S('yellow', base=.55, up=0, jit=0)) if k == 1 else None
        bm = box((1.0, 1.8, 1.0), .12); at(bm, (sx * 3.6, -2.3, 1.5)); P.add(bm, S('rubber', base=.22, up=.25, jit=.02))
        for y in (-3.0, -1.6): P.add(at(cyl(.08, .1, 6), (sx * 3.6, y, 2.0), (90, 0, 0)), S('steel', base=.6, up=.2, jit=0))
    B(P, (OW + 4.2, 1.4, 2.2), (0, OH + .7, 2.1), 'rubber', .25, base=.22)
    B(P, (OW + .4, .3, .3), (0, -.15, 1.15), 'steel', 0, base=.5)
    # dock light on a swivel arm + signal lights + push buttons
    x = OW / 2 + 2.6
    B(P, (.6, 1.0, .3), (x, 9.0, -.15), 'steel', .05, base=.5)
    T(P, [V(x, 9.0, -.3), V(x - .6, 9.1, -2.5), V(x - 2.2, 9.0, -3.6)], .09, 'steel', 6, base=.55)
    hd = lathe([(0, 0), (.55, 0), (.6, .2), (.35, .9), (0, .9)], 12); at(hd, (0, 0, 0), (-120, 0, 0)); at(hd, (x - 2.2, 9.0, -3.6)); P.add(hd, S('yellow', base=.55, up=.25, jit=0), True)
    for sx, z, face in ((-1, -.25, -1), (-1, 1.05, 1)):
        bx = -(OW / 2 + 2.4)
        B(P, (.9, 2.0, .4), (bx, 8.5 if face < 0 else 9.2, z + face * .2), 'rubber', .08, base=.25)
        for k, key in enumerate(('stop', 'go')):
            on = (key == 'go') == (state == 'open')
            c = lathe([(0, 0), (.32, 0), (.3, .12), (0, .14)], 10); at(c, (0, 0, 0), (90 * face, 0, 0)); at(c, (bx, (8.5 if face < 0 else 9.2) + .45 - k * .9, z + face * .4))
            if on: P.gadd(c, key)
            else: P.add(c, S('red' if key == 'stop' else 'green', base=.25, up=.1, jit=0))
    B(P, (.9, 1.3, .45), (x - 1.3, 5.0, -.25), 'paper', .06, base=.8)
    for k, col in enumerate(('green', 'red', 'rubber')): P.add(at(cyl(.12, .12, 8), (x - 1.3, 5.35 - k * .35, -.48), (-90, 0, 0)), S(col, base=.5, up=.2, jit=0))
    return P

def personnel_door():
    """single steel fire door with frame, vision panel, push bar, closer (wall prop, inner face z 0)"""
    P = Prop('PersonnelDoor')
    for sx in (-1, 1): B(P, (.35, 8.25, .5), (sx * 2.02, 4.125, -.1), 'steel', .04, base=.6)
    B(P, (4.35, .35, .5), (0, 8.1, -.1), 'steel', .04, base=.6)
    B(P, (3.7, 7.9, .25), (0, 3.95, .2), 'plastic', .03, base=.62)
    P.add(quad(.8, 2.2, 'z', .07, .9, 5.6), S('glass', base=.3, up=0, jit=0))
    B(P, (3.0, .25, .3), (0, 3.6, -.12), 'steel', .08, base=.7)
    for sx in (-1, 1): B(P, (.3, .5, .4), (sx * 1.4, 3.6, -.05), 'steel', .05, base=.55)
    B(P, (1.4, .35, .4), (-1.0, 7.6, -.2), 'steel', .05, base=.5)
    T(P, [V(-1.0, 7.45, -.3), V(.4, 7.5, -.5), V(1.3, 7.6, -.1)], .05, 'steel', 6, base=.6)
    P.add(quad(4.6, .3, 'y', .01, 0, -.5), S('rubber', base=.2, up=0, jit=0))
    return P

# ================================================================== hero: overhead bridge crane + container
def runway_beam(L=30.0):
    """crane runway girder segment along x: I-beam 1.4 deep + square rail on top (rail top = local y 0 = RUNWAY_Y)"""
    P = Prop('RunwayBeam%d' % int(L))
    b = ibeam(L - .02, 1.4, .8, .12, .14, 'x'); at(b, (-L / 2 + .01, -.9, 0)); P.add(b, S('yellow', base=.5, up=.2, jit=0))
    B(P, (L, .2, .25), (0, -.1, 0), 'steel', 0, base=.6)
    for x in (-L / 2 + 5, 0, L / 2 - 5):
        for sz in (-1, 1): P.add(quad(.1, 1.1, 'z', sz * .061, x, -.9, flip=sz > 0), S('yellow', base=.35, up=0, jit=0))
    return P

def crane_bridge(span=49.0):
    """double-girder overhead travelling crane: box girders along z, end trucks on the runway rails (x is travel),
    trolley + hoist drum + motors on top, walkway with handrail, festoon cable, pendant; hook block hangs to y_hook.
    Origin: midpoint between the runways at rail-top height RUNWAY_Y."""
    P = Prop('CraneBridge'); hs = span / 2; gx = 2.2; GH, GW = 3.0, 1.1
    for sx in (-1, 1):                                                   # box girders: webs, flanges, stiffener ribs
        B(P, (GW, GH, span - 2.0), (sx * gx, 1.9 + GH / 2, 0), 'yellow', .05, base=.58)
        B(P, (GW + .5, .14, span - 2.0), (sx * gx, 1.9 + GH + .07, 0), 'yellow', 0, base=.65)
        B(P, (GW + .5, .14, span - 2.0), (sx * gx, 1.83, 0), 'yellow', 0, base=.5)
        for k in range(1, 16):
            z = -hs + 1 + k * (span - 2) / 16
            for f in (-1, 1): P.add(quad(.12, GH - .1, 'x', sx * gx + f * (GW / 2 + .006), z, 1.9 + GH / 2, flip=f < 0), S('yellow', base=.4, up=0, jit=0))
        P.add(at(box((.12, .14, span - 2.4), 0), (sx * gx, 1.9 + GH + .2, 0)), S('steel', base=.6, up=.2, jit=0))   # trolley rail
    for sz in (-1, 1):                                                   # end trucks with wheels on the runway rails
        z = sz * (hs - .3)
        B(P, (8.0, 1.8, 1.6), (0, 1.0, z), 'yellow', .1, base=.52)
        for sx in (-1, 1):
            w = cyl(.75, .5, 14, 0, y0=-.25); at(w, (0, 0, 0), (0, 0, 90)); at(w, (sx * 3.0, .55, z)); P.add(w, S('steel', base=.4, up=.2, jit=0), True)
            B(P, (1.2, 1.4, 1.0), (sx * 3.0, 1.8, z + sz * .9), 'plastic', .1, base=.45)                  # travel drive motors
            P.add(at(box((.5, .7, .4), .06), (sx * 3.9, .9, z)), S('red', base=.5, up=.2, jit=0))         # buffers
        P.add(quad(7.6, .3, 'z', z - sz * .81, 0, 1.2, flip=sz > 0), S('rubber', base=.2, up=0, jit=0))
    # walkway with checker plate + handrail on the +x side
    B(P, (1.8, .12, span - 3), (gx + 1.7, 1.95, 0), 'steel', 0, base=.45)
    for z in [-hs + 2 + k * (span - 4) / 8 for k in range(9)]: T(P, [V(gx + 2.5, 2.0, z), V(gx + 2.5, 5.4, z)], .07, 'yellow', 6, base=.6)
    for y in (3.7, 5.4): T(P, [V(gx + 2.5, y, -hs + 2), V(gx + 2.5, y, hs - 2)], .07, 'yellow', 6, base=.6, cap=False)
    # festoon cable loops along the -x girder
    for k in range(5):
        z0 = -hs + 4 + k * 8.6
        T(P, [V(-gx - .9, 4.5, z0 + d) + V(0, -math.sin(d / 8.6 * math.pi) * 1.2, 0) for d in [i * 8.6 / 6 for i in range(7)]], .1, 'rubber', 6, base=.25, cap=False)
    return P

def crane_trolley(hook_drop=12.0):
    """crab: frame, rope drum, gearbox + motor, two rope falls down to the hook block, spreader beam with 4 chains.
    Origin: trolley-rail top centre; hook block at y -hook_drop."""
    P = Prop('CraneTrolley'); gx = 2.2
    B(P, (6.0, .7, 5.0), (0, .55, 0), 'yellow', .08, base=.55)
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(at(cyl(.45, .4, 12, 0, y0=-.2), (sx * gx, .35, sz * 1.8), (0, 0, 90)), S('steel', base=.4, up=.2, jit=0), True)
    drum = cyl(1.1, 3.6, 18, 0, y0=-1.8); at(drum, (0, 0, 0), (0, 0, 90)); at(drum, (0, 2.0, -.5)); P.add(drum, S('steel', base=.55, up=.25, jit=0), True)
    for x in (-1.8, 1.8):
        f = cyl(1.4, .25, 18, 0, y0=-.12); at(f, (0, 0, 0), (0, 0, 90)); at(f, (x, 2.0, -.5)); P.add(f, S('yellow', base=.45, up=.2, jit=0), True)
    for k in range(10): P.add(at(ring_tube(V(0, 0, 0), 1.13, .06, 16, 4, 'X'), (-1.5 + k * .33, 2.0, -.5)), S('steel', base=.75, up=.2, jit=0), True)
    B(P, (1.6, 1.6, 1.8), (2.8, 1.8, 1.4), 'plastic', .12, base=.42)
    m = cyl(.7, 2.0, 14, 0, y0=-1.0); at(m, (0, 0, 0), (0, 0, 90)); at(m, (1.0, 1.8, 1.6)); P.add(m, S('plastic', base=.45, up=.2, jit=0), True)
    for k in range(6): P.add(at(ring_tube(V(0, 0, 0), .72, .04, 14, 4, 'X'), (.3 + k * .3, 1.8, 1.6)), S('plastic', base=.3, up=.2, jit=0), True)
    B(P, (1.4, 1.2, 1.4), (-2.6, 1.6, 1.6), 'rubber', .08, base=.35)
    hy = -hook_drop
    for x in (-.7, .7):                                                   # rope falls (two parts each side)
        for dz in (-.25, .25): T(P, [V(x, 1.0, -.5 + dz), V(x * .8, hy + 1.6, dz * .6)], .06, 'steel', 5, base=.7, cap=False)
    blk = rbox((2.2, 2.0, 1.4), .25, 2); at(blk, (0, hy + 1.0, 0)); P.add(blk, S('yellow', base=.55, up=.25, jit=0), True)
    for x in (-.55, .55):
        sh = cyl(.75, .25, 16, 0, y0=-.12); at(sh, (0, 0, 0), (0, 0, 90)); at(sh, (x, hy + 1.45, 0)); P.add(sh, S('steel', base=.5, up=.2, jit=0), True)
    hk = [V(0, hy, 0), V(0, hy - .8, 0), V(.1, hy - 1.6, 0), V(.6, hy - 2.1, 0), V(.5, hy - 2.7, 0), V(-.1, hy - 2.85, 0), V(-.6, hy - 2.5, 0), V(-.65, hy - 2.0, 0)]
    P.add(tube(hk, [.3, .32, .3, .26, .24, .22, .18, .14], 10), S('steel', base=.45, up=.25, jit=0), True)
    P.add(at(cyl(.32, .4, 10), (0, hy - .2, 0)), S('steel', base=.4, up=.2, jit=0))
    # sling to a spreader beam, 4 chains down to the container's corner castings (container top at hy - 6.8)
    sy = hy - 4.6; ct = hy - 6.8
    for x in (-3.5, 3.5): T(P, [V(-.1, hy - 2.3, 0), V(x, sy + .5, 0)], .08, 'rubber', 6, base=.3, cap=False)
    B(P, (16.0, .9, .7), (0, sy, 0), 'yellow', .06, base=.55)
    for x in (-8.9, 8.9):
        for z in (-3.6, 3.6):
            pts = [V(x * .88, sy - .4, z * .1), V(x, ct + .1, z)]
            T(P, pts, .07, 'steel', 4, base=.7, cap=False)
            P.add(at(box((.3, .4, .3), .04), (x, ct + .25, z)), S('steel', base=.45, up=.2, jit=0))
    # pendant control box on a cable
    T(P, [V(2.6, .3, -1.6), V(2.6, hy + 5.5, -1.6)], .04, 'rubber', 4, base=.2, cap=False)
    B(P, (.5, 1.2, .4), (2.6, hy + 4.9, -1.6), 'yellow', .08, base=.55)
    for k in range(4): P.add(at(cyl(.08, .06, 8), (2.6, hy + 5.25 - k * .25, -1.81), (-90, 0, 0)), S('rubber', base=.25, up=.2, jit=0))
    return P

def shipping_container(col='red', seed=0):
    """20 ft ISO box: corrugated side + end walls (trapezoid profile), top/bottom rails, corner posts + castings,
    double doors at +x with 4 locking bars, cam keepers, handles. 19 x 8.1 x 7.7, long axis x, origin bottom centre."""
    P = Prop('Container%s' % col.capitalize()); L, H, W = 19.0, 8.1, 7.7; hl, hw = L / 2, W / 2
    sh = lambda v=.5: S(col, base=v, up=.22, jit=0)
    def corr(n, length, depth, axis):                                    # corrugated panel profile, outward toward +side
        pts = []; p = length / n
        for k in range(n):
            a = -length / 2 + k * p
            pts += [(a, 0), (a + p * .15, depth), (a + p * .5, depth), (a + p * .65, 0)]
        pts.append((length / 2, 0))
        return pts
    for sz in (-1, 1):                                                   # long side walls
        prof = corr(36, L - 1.0, .2, 'x')
        bm = bmesh.new(); vb = []
        for x, d in prof:
            vb.append((bm.verts.new((x, .45, sz * (hw - .25 + d))), bm.verts.new((x, H - .45, sz * (hw - .25 + d)))))
        for (a0, a1), (b0, b1) in zip(vb, vb[1:]): bm.faces.new((a0, b0, b1, a1) if sz > 0 else (a0, a1, b1, b0))
        bm.normal_update()
        for f in bm.faces:
            if f.normal.z * sz < 0: f.normal_flip()
        P.add(bm, SF(lambda c, n: (col, .5 if abs(n.x) < .3 else .36 + .1 * n.x), up=0))
    end = bmesh.new(); vb = []                                           # front end wall (-x)
    for z, d in corr(10, W - 1.0, .18, 'z'):
        vb.append((end.verts.new((-hl + .25 - d, .45, z)), end.verts.new((-hl + .25 - d, H - .45, z))))
    for (a0, a1), (b0, b1) in zip(vb, vb[1:]): end.faces.new((a0, a1, b1, b0))
    end.normal_update()
    for f in end.faces:
        if f.normal.x > 0: f.normal_flip()
    P.add(end, sh(.48))
    roof = box((L - .8, .12, W - .8), 0); at(roof, (0, H - .3, 0)); P.add(roof, sh(.55))
    for k in range(12): P.add(quad(.25, W - 1.0, 'y', H - .23, -hl + 1.2 + k * 1.5), sh(.62))
    for y in (.25, H - .2):                                              # top + bottom side rails, end rails
        for sz in (-1, 1): B(P, (L, .45 if y < 1 else .4, .4), (0, y, sz * (hw - .2)), col, 0, base=.42)
        for sx in (-1, 1): B(P, (.4, .45, W - .8), (sx * (hl - .2), y, 0), col, 0, base=.42)
    for sx in (-1, 1):                                                   # corner posts + castings with holes
        for sz in (-1, 1):
            B(P, (.5, H - .9, .5), (sx * (hl - .25), H / 2, sz * (hw - .25)), col, 0, base=.4)
            for y in (.3, H - .3):
                B(P, (.6, .6, .6), (sx * (hl - .3), y, sz * (hw - .3)), 'rubber', .03, base=.4)
                P.add(quad(.32, .2, 'x', sx * (hl + .005), sz * (hw - .3), y, flip=sx < 0), S('rubber', base=.05, up=0, jit=0))
    door = box((.2, H - .9, W - 1.0), 0); at(door, (hl - .15, H / 2, 0)); P.add(door, sh(.5))   # doors (+x)
    for k in range(7): P.add(quad(W - 1.1, .1, 'x', hl - .04, 0, 1.0 + k * 1.0), sh(.38))
    P.add(quad(.05, H - 1.0, 'x', hl - .039, 0, H / 2), S('rubber', base=.1, up=0, jit=0))
    for z in (-2.8, -1.0, 1.0, 2.8):                                     # locking bars + cam keepers + handles
        T(P, [V(hl + .12, .5, z), V(hl + .12, H - .5, z)], .07, 'steel', 6, base=.55)
        for y in (.6, H - .6): B(P, (.2, .3, .35), (hl + .1, y, z), 'steel', 0, base=.45)
        T(P, [V(hl + .15, 3.0, z), V(hl + .45, 3.0, z + .55)], .05, 'steel', 6, base=.55)
    P.add(quad(.9, .6, 'x', hl + .01, -1.9, 6.4), S('paper', base=.85, up=0, jit=0))          # blank data plate
    for k in range(2): P.add(quad(.18, .9, 'x', hl + .01, -3.0 + k * 6.0, 1.0), S('rubber', base=.3, up=0, jit=0))
    floor = box((L - .8, .1, W - .8), 0); at(floor, (0, .5, 0)); P.add(floor, S('pallet', base=.35, up=.1, jit=0))
    for k in range(12): P.add(quad(.3, W - .9, 'y', .05, -hl + 1.2 + k * 1.5, flip=True), S('rubber', base=.25, up=0, jit=0))   # cross members (under)
    return P

def skylight(w=10.0, d=10.0, slope=1):
    """roof-light: aluminium upstand frame + glazing bars round a translucent panel (glass on top, daylight glow under).
    Built on the roof deck underside plane; slope = +1 for the south roof (deck falls toward +z), -1 north."""
    P = Prop('Skylight%s' % ('S' if slope > 0 else 'N')); pitch = -slope * math.degrees(math.atan(4 / 80))
    s = Sub()
    for sx in (-1, 1):
        s.add(at(box((.4, .9, d + .4), 0), (sx * (w / 2 + .2), .15, 0)), S('steel', base=.62, up=.2, jit=0))
        s.add(at(box((w + .8, .9, .4), 0), (0, .15, sx * (d / 2 + .2))), S('steel', base=.62, up=.2, jit=0))
    for k in range(1, 4): s.add(at(box((.15, .2, d), 0), (-w / 2 + k * w / 4, .55, 0)), S('steel', base=.6, up=.2, jit=0))
    s.add(at(box((w, .08, d), 0), (0, .55, 0)), S('glass', base=.55, up=.2, jit=0))
    s.gadd(at(box((w - .1, .02, d - .1), 0), (0, .49, 0)), 'sky')
    s.emit(P, (0, 0, 0), [(pitch, 0, 0)])
    return P
