# v3: detailed Part builds replacing the too-plain v1 models (lamps, shop, hatchery, rebirth, wins pad, treadmill).
# Rule: no bare cubes. Every model gets plinth + trims, chamfers (wedges), round parts (cylinders / balls), framed
# panels, real display items and light fittings.
import math, random
from blocks import BlockProp
import plus_props as K

# ------------------------------------------------------------------ detail helpers
def chamfer_block(P, size, pos, col, v, bev=1.0, top=True):
    """block whose top edges are chamfered with 4 wedges (reads bevelled, not a raw cube)"""
    sx, sy, sz = size; x, y, z = pos
    P.b((sx - 2 * bev, sy, sz - 2 * bev), (x, y, z), col, v)
    P.b((sx, sy - bev, sz), (x, y - bev / 2, z), col, v - .03)
    if top:
        yt = y + sy / 2 - bev / 2
        for yaw, ox, oz, L in ((0, 0, -(sz / 2 - bev / 2), sx - 2 * bev), (180, 0, sz / 2 - bev / 2, sx - 2 * bev),
                               (90, -(sx / 2 - bev / 2), 0, sz - 2 * bev), (-90, sx / 2 - bev / 2, 0, sz - 2 * bev)):
            P.b((L, bev, bev), (x + ox, yt, z + oz), col, v + .04, rot=(0, yaw, 0), shape='wedge')

def octo(P, w, h, pos, col, v):
    """8-sided column from two overlapping blocks"""
    x, y, z = pos
    P.b((w, h, w * .42), (x, y, z), col, v); P.b((w * .42, h, w), (x, y, z), col, v)
    P.b((w * .78, h, w * .78), (x, y, z), col, v - .02, rot=(0, 45, 0))

def cyl_v(P, d, h, pos, col, v, mat='stud', tr=0.0):
    P.b((h, d, d), pos, col, v, rot=(0, 0, 90), shape='cyl', mat=mat, tr=tr)

def ring(P, centre, radius, n, part, col, v, plane='xy', mat='stud'):
    """n blocks laid tangent around a circle (plane 'xy' = vertical ring facing Z, 'xz' = flat ring)"""
    cx, cy, cz = centre
    for k in range(n):
        a = k * 2 * math.pi / n
        if plane == 'xy': P.b(part, (cx + math.cos(a) * radius, cy + math.sin(a) * radius, cz), col, v, rot=(0, 0, math.degrees(a) + 90), mat=mat)
        else: P.b(part, (cx + math.cos(a) * radius, cy, cz + math.sin(a) * radius), col, v, rot=(0, -math.degrees(a) + 90, 0), mat=mat)

def gable(P, w, d, h, pos, col, v, trim=None):
    """gable roof along X: two wedges back to back + ridge trim"""
    x, y, z = pos
    P.b((w, h, d / 2), (x, y + h / 2, z - d / 4), col, v, shape='wedge')
    P.b((w, h, d / 2), (x, y + h / 2, z + d / 4), col, v - .04, rot=(0, 180, 0), shape='wedge')
    if trim: P.b((w + .4, .6, .9), (x, y + h + .1, z), trim, .62)

def bulbs_frame(P, w, h, pos, col='gold', n_w=8, n_h=4):
    """marquee light bulbs around a sign"""
    x, y, z = pos
    for i in range(n_w + 1):
        for sy in (-1, 1): P.b((.7, .7, .7), (x - w / 2 + w * i / n_w, y + sy * h / 2, z), col, .85, shape='ball', mat='neon')
    for j in range(1, n_h):
        for sx in (-1, 1): P.b((.7, .7, .7), (x + sx * w / 2, y - h / 2 + h * j / n_h, z), col, .85, shape='ball', mat='neon')

def framed_panel(P, w, h, pos, face='navy', frame='gold', fv=.6, depth=.6, rot=(0, 0, 0)):
    x, y, z = pos
    P.b((w, h, depth), (x, y, z), face, .3, rot=rot)
    for (sw, sh, ox, oy) in ((w + .8, .6, 0, h / 2), (w + .8, .6, 0, -h / 2), (.6, h + .8, w / 2, 0), (.6, h + .8, -w / 2, 0)):
        P.b((sw, sh, depth + .4), (x + ox, y + oy, z), frame, fv, rot=rot)

# ------------------------------------------------------------------ display items (no plain cubes on shelves)
def speed_shoe(P, pos, col, yaw=0):
    x, y, z = pos
    S = BlockProp('Shoe')
    S.b((1.4, .35, 3.2), (0, .18, 0), 'snow', .92)                              # sole
    S.b((1.3, .9, 2.2), (0, .8, .4), col, .6)                                   # upper
    S.b((1.3, .8, 1.3), (0, .7, -.9), col, .62, shape='ball')                   # toe
    S.b((1.32, .3, 1.5), (0, 1.35, .5), 'snow', .9)                             # collar
    for k in range(3): S.b((1.36, .14, .22), (0, 1.05, -.4 + k * .45), 'snow', .95)   # laces
    S.b((.2, .6, 1.4), (.72, .8, .5), 'gold', .7, mat='neon')                   # speed stripe
    P.put(S, pos, yaw)

def potion(P, pos, col):
    x, y, z = pos
    cyl_v(P, 1.4, 1.6, (x, y + .8, z), 'snow', .9, mat='smooth', tr=.4)
    cyl_v(P, 1.15, 1.1, (x, y + .62, z), col, .65, mat='neon')
    cyl_v(P, .7, .6, (x, y + 1.9, z), 'snow', .9, mat='smooth', tr=.4)
    cyl_v(P, .55, .5, (x, y + 2.35, z), 'wood', .5)

def gift(P, pos, col, s=1.6):
    x, y, z = pos
    P.b((s, s, s), (x, y + s / 2, z), col, .6)
    P.b((s + .1, s + .1, .3), (x, y + s / 2, z), 'gold', .7); P.b((.3, s + .1, s + .1), (x, y + s / 2, z), 'gold', .7)
    for sx in (-1, 1): P.b((.7, .5, .5), (x + sx * .35, y + s + .2, z), 'gold', .75, shape='ball')

def barrel(P, pos, h=3.2, col='wood'):
    x, y, z = pos
    cyl_v(P, 2.4, h, (x, y + h / 2, z), col, .5)
    for yy in (.35, h / 2, h - .35): cyl_v(P, 2.6, .3, (x, y + yy, z), 'basalt', .35)
    cyl_v(P, 2.0, .2, (x, y + h + .02, z), col, .62)

# ------------------------------------------------------------------ lamps
def lamp_pillar(base_col='rock', pillar_col='fire', lantern='gold'):
    """street lantern pillar: chamfered stepped plinth, 8-sided banded column, capital, caged lantern with a glowing
    core, wedge roof and a ball finial"""
    P = BlockProp('LampPillar')
    chamfer_block(P, (11, 2.2, 11), (0, .9, 0), base_col, .4, bev=.9)
    chamfer_block(P, (8.6, 2.0, 8.6), (0, 3.0, 0), base_col, .48, bev=.7)
    octo(P, 5.6, 16, (0, 12, 0), pillar_col, .52)
    for y in (6.0, 12.0, 18.0): cyl_v(P, 6.6, .9, (0, y, 0), lantern, .6)
    cyl_v(P, 7.8, 1.2, (0, 20.6, 0), base_col, .5); chamfer_block(P, (8.4, 1.4, 8.4), (0, 21.8, 0), base_col, .55, bev=.6)
    for sx in (-1, 1):                                                          # lantern cage
        for sz in (-1, 1): P.b((.7, 5.2, .7), (sx * 2.6, 25.2, sz * 2.6), 'basalt', .25)
    for y in (22.8, 27.6):
        for yaw in (0, 90):
            for s in (-1, 1): P.b((5.9, .5, .5), (0, y, s * 2.6) if yaw == 0 else (s * 2.6, y, 0), 'basalt', .28, rot=(0, yaw, 0))
    P.b((4.0, 4.4, 4.0), (0, 25.2, 0), lantern, .78, mat='neon')
    P.b((5.0, 4.6, 5.0), (0, 25.2, 0), 'snow', .9, mat='smooth', tr=.6)
    for yaw in (0, 90, 180, 270): P.b((6.6, 1.6, 3.3), (-math.sin(math.radians(yaw)) * 1.65, 28.7, -math.cos(math.radians(yaw)) * 1.65), 'basalt', .3, rot=(0, yaw, 0), shape='wedge')
    P.b((1.4, 1.4, 1.4), (0, 30.0, 0), lantern, .7, shape='ball')
    return P

# ------------------------------------------------------------------ shop
def shop_stall():
    """SPEED SHOP: platform with a ramp, panelled counter, back wall with shelves of speed shoes / potions / gifts,
    gable roof + striped scalloped awning, marquee sign with bulbs, lanterns, barrels"""
    P = BlockProp('Shop'); w, d = 20, 12
    chamfer_block(P, (w + 4, 1.4, d + 4), (0, .2, 0), 'stone', .55, bev=.6)
    P.b((8, 1.2, 3), (0, .3, -(d / 2 + 3.2)), 'stone', .62, rot=(0, 180, 0), shape='wedge')           # ramp up to the counter
    # counter: panelled front, overhanging top with trim
    P.b((w - 2, 4.2, 3), (0, 3.0, -d / 2 + 2), 'wood', .5)
    for k in range(4): framed_panel(P, 3.4, 2.4, (-6.75 + k * 4.5, 3.0, -d / 2 + .4), 'wood', 'wood', .62, depth=.3)
    P.b((w - .6, .7, 3.8), (0, 5.4, -d / 2 + 2), 'gold', .6); P.b((w - 1, .4, 3.4), (0, 5.95, -d / 2 + 2), 'wood', .66)
    speed_shoe(P, (-6, 6.2, -d / 2 + 2), 'red', 20); speed_shoe(P, (-2.5, 6.2, -d / 2 + 2), 'mint', -15)
    potion(P, (2, 6.2, -d / 2 + 2), 'pink'); potion(P, (4, 6.2, -d / 2 + 2), 'mint'); gift(P, (7, 6.2, -d / 2 + 2), 'red')
    # back wall + shelves
    P.b((w - 1, 13, 1), (0, 7, d / 2 - .5), 'wood', .45)
    for k in range(5): P.b((.5, 13, .4), (-w / 2 + 2 + k * (w - 4) / 4, 7, d / 2 - 1.1), 'wood', .38)
    for y in (4.6, 8.4):
        P.b((w - 3, .5, 2.2), (0, y, d / 2 - 2), 'wood', .6)
        for k in range(5):
            x = -7 + k * 3.5
            if (k + int(y)) % 3 == 0: speed_shoe(P, (x, y + .25, d / 2 - 2), ['pink', 'gold', 'navy', 'red', 'mint'][k], 90)
            elif (k + int(y)) % 3 == 1: potion(P, (x, y + .25, d / 2 - 2), ['fire', 'mint', 'pink', 'gold', 'navy'][k])
            else: gift(P, (x, y + .25, d / 2 - 2), ['mint', 'pink', 'gold', 'red', 'navy'][k], 1.4)
    # posts + roof + awning
    for sx in (-1, 1):
        for sz in (-1, 1):
            octo(P, 1.4, 14, (sx * (w / 2 - .6), 7.4, sz * (d / 2 - .6)), 'wood', .42)
            cyl_v(P, 1.9, .5, (sx * (w / 2 - .6), 14.2, sz * (d / 2 - .6)), 'gold', .6)
    P.b((w + 1, .8, d + 1), (0, 14.6, 0), 'wood', .4)
    gable(P, w + 2, d + 2, 4.5, (0, 15.0, 0), 'red', .5, trim='gold')
    nst = 10
    for k in range(nst):                                                       # striped awning + scallops
        x = -(w + 2) / 2 + (w + 2) * (k + .5) / nst; col = 'red' if k % 2 else 'snow'
        P.b(((w + 2) / nst, .4, 5), (x, 13.2, -d / 2 - 2.2), col, .6 if k % 2 else .92, rot=(-20, 0, 0))
        P.b((.4, (w + 2) / nst, (w + 2) / nst), (x, 12.1, -d / 2 - 4.5), col, .6 if k % 2 else .92, rot=(0, 90, 0), shape='cyl')
    # marquee sign
    P.b((16, 5.4, 1.2), (0, 22.6, 0), 'navy', .3)
    framed_panel(P, 15, 4.4, (0, 22.6, -.4), 'navy', 'gold', .62, depth=.4)
    P.b((12, 1.6, .3), (0, 23.2, -.8), 'snow', .95, mat='neon'); P.b((8, 1.0, .3), (0, 21.4, -.8), 'gold', .75, mat='neon')
    bulbs_frame(P, 16.4, 6.0, (0, 22.6, -.9), 'gold', 10, 3)
    for sx in (-1, 1): P.b((.8, 4, .8), (sx * 5, 19.4, 0), 'wood', .4)
    for sx in (-1, 1):                                                          # hanging lanterns
        x = sx * (w / 2 + .2)
        P.b((.2, 1.6, .2), (x, 12.2, -d / 2 - .6), 'basalt', .3)
        cyl_v(P, 1.4, 1.8, (x, 10.6, -d / 2 - .6), 'gold', .78, mat='neon'); cyl_v(P, 1.8, .4, (x, 11.7, -d / 2 - .6), 'basalt', .3)
    barrel(P, (w / 2 + 3, .2, -2)); barrel(P, (w / 2 + 3.2, .2, 1.4)); gift(P, (w / 2 + 3, 3.6, -.3), 'pink', 1.8)
    return P

# ------------------------------------------------------------------ hatchery
def hatchery():
    """EGG HATCHERY: tiered round base with rims, glass dome over a big spotted egg on a glowing cradle, ring frame,
    4 ornate pillars with gem capitals, stepped round roof with a finial, 3 display eggs on pedestals, marquee sign"""
    P = BlockProp('Hatchery')
    for k, (d_, h, col, v) in enumerate(((34, 1.4, 'stone', .52), (30, 1.4, 'stone', .62), (24, 1.2, 'gold', .6))):
        cyl_v(P, d_, h, (0, .2 + k * 1.3, 0), col, v)
    for k in range(3): P.b((9 - k * 1.5, 1.2, 2.4), (0, .2 + k * 1.1, -17.6 + k * 1.6), 'stone', .62 + k * .03)
    cyl_v(P, 12, 1.6, (0, 4.4, 0), 'navy', .45); cyl_v(P, 10.6, .5, (0, 5.4, 0), 'pink', .75, mat='neon')
    P.b((9, 11.5, 9), (0, 11.0, 0), 'snow', .94, shape='ball'); P.b((7.6, 5.2, 7.6), (0, 16.0, 0), 'snow', .94, shape='ball')
    rng = random.Random(4)
    for k in range(12):                                                         # egg spots (balls, not cubes)
        a = k * math.pi * 2 / 12; y = (9.5, 12.5, 15.0)[k % 3]; r = {9.5: 4.3, 12.5: 4.2, 15.0: 3.4}[y]
        P.b((1.6, 1.6, 1.0), (math.cos(a) * r, y, math.sin(a) * r), ['pink', 'mint', 'gold'][k % 3], .62, shape='ball', rot=(0, -math.degrees(a) + 90, 0))
    P.b((15, 17, 15), (0, 12.2, 0), 'snow', .95, shape='ball', mat='smooth', tr=.7)   # glass dome
    ring(P, (0, 12.2, 0), 8.0, 20, (2.6, 1.0, 1.0), 'gold', .62, plane='xy')
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 12, sz * 12
            chamfer_block(P, (4, 1.6, 4), (x, 4.6, z), 'stone', .6, bev=.5)
            octo(P, 2.6, 18, (x, 14.4, z), 'snow', .82)
            for y in (8, 14, 20): cyl_v(P, 3.2, .7, (x, y, z), 'pink', .6)
            chamfer_block(P, (4.4, 1.6, 4.4), (x, 24.2, z), 'gold', .6, bev=.5)
            P.b((1.8, 1.8, 1.8), (x, 26.0, z), 'mint', .7, mat='neon', rot=(45, 45, 0))
    for k, (d_, h, col, v) in enumerate(((32, 1.4, 'pink', .5), (28, 1.6, 'snow', .92), (22, 1.8, 'pink', .55), (15, 2.0, 'snow', .92), (8, 2.2, 'pink', .6))):
        cyl_v(P, d_, h, (0, 25.6 + k * 1.7, 0), col, v)
    P.b((2.4, 2.4, 2.4), (0, 35.4, 0), 'gold', .75, shape='ball'); P.b((.6, 3, .6), (0, 37.6, 0), 'gold', .6)
    for k, (x, col) in enumerate(((-9, 'mint'), (0, 'gold'), (9, 'red'))):   # display eggs in front
        z = -20.5
        cyl_v(P, 4.2, 1.2, (x, .4, z), 'stone', .62); cyl_v(P, 3.6, .3, (x, 1.1, z), col, .75, mat='neon')
        P.b((2.6, 3.4, 2.6), (x, 2.9, z), col, .62, shape='ball'); P.b((2.1, 1.5, 2.1), (x, 4.5, z), col, .7, shape='ball')
    P.b((18, 5, 1.2), (0, 31, -16.5), 'navy', .3); framed_panel(P, 17, 4.2, (0, 31, -16.9), 'navy', 'pink', .6, depth=.4)
    P.b((13, 1.6, .3), (0, 31.5, -17.3), 'snow', .95, mat='neon'); P.b((8, 1, .3), (0, 29.8, -17.3), 'pink', .75, mat='neon')
    bulbs_frame(P, 18.4, 5.6, (0, 31, -17.4), 'pink', 10, 3)
    for sx in (-1, 1): P.b((.8, 4, .8), (sx * 6, 27.6, -16.5), 'gold', .55)
    return P

# ------------------------------------------------------------------ rebirth
def rebirth_altar():
    """REBIRTH portal: 8-sided stepped dais with rune ring, a standing ring portal (tangent blocks) with a glowing
    swirl disc, 4 obelisks with gem caps, stair, floating crystal"""
    P = BlockProp('Rebirth')
    for k, (w, h) in enumerate(((28, 1.4), (23, 1.4), (18, 1.4))):              # round stepped dais with gold rims
        cyl_v(P, w, h, (0, .4 + k * 1.4, 0), 'stone', .5 + k * .07); cyl_v(P, w + .5, .35, (0, 1.0 + k * 1.4, 0), 'gold', .6)
    ring(P, (0, 4.0, 0), 7.2, 16, (1.4, .2, .5), 'mint', .75, plane='xz', mat='neon')
    for k in range(3): P.b((8 - k * 1.4, 1.3, 2.4), (0, .3 + k * 1.3, -14 + k * 1.6), 'stone', .62 + k * .03)
    ring(P, (0, 14.0, 0), 9.0, 24, (2.8, 1.8, 2.2), 'navy', .5, plane='xy')     # portal ring
    ring(P, (0, 14.0, 0), 9.0, 12, (.9, .9, 2.6), 'gold', .62, plane='xy')
    P.b((.6, 15.6, 15.6), (0, 14.0, 0), 'pink', .7, shape='cyl', rot=(0, 90, 0), mat='neon', tr=.35)
    P.b((.8, 8, 8), (0, 14.0, 0), 'snow', .9, shape='cyl', rot=(0, 90, 0), mat='neon', tr=.3)
    for sx in (-1, 1): chamfer_block(P, (4, 3, 4), (sx * 9, 4.2 + 1.5, 0), 'navy', .45, bev=.6)
    for a in range(45, 360, 90):                                                # obelisks
        x, z = math.sin(math.radians(a)) * 12.5, math.cos(math.radians(a)) * 12.5
        chamfer_block(P, (3.4, 1.4, 3.4), (x, 4.4, z), 'stone', .6, bev=.4)
        P.b((2.2, 11, 2.2), (x, 10.5, z), 'navy', .42); P.b((2.6, .6, 2.6), (x, 8, z), 'gold', .6); P.b((2.6, .6, 2.6), (x, 13, z), 'gold', .6)
        P.b((2.2, 2.2, 2.2), (x, 17.0, z), 'navy', .5, rot=(0, 45, 0), shape='wedge')
        P.b((1.6, 1.6, 1.6), (x, 18.6, z), 'mint', .75, mat='neon', rot=(45, 45, 0))
    P.b((3, 3, 3), (0, 27.0, 0), 'pink', .8, mat='neon', rot=(45, 45, 0))
    return P

# ------------------------------------------------------------------ wins pad
def wins_pad(col='gold', r=12.0):
    """wins pad: stepped round base with a gold rim, glowing ring and centre emblem, a translucent light column and a
    floating cylinder trophy with block handles"""
    P = BlockProp('WinsPad')
    cyl_v(P, r + 3, 1.0, (0, .1, 0), 'basalt', .3); cyl_v(P, r + 2.2, .5, (0, .75, 0), 'gold', .6)
    cyl_v(P, r + 1, .4, (0, 1.0, 0), col, .75, mat='neon'); cyl_v(P, r - 1.2, .5, (0, 1.1, 0), 'stone', .65)
    cyl_v(P, r * .45, .3, (0, 1.4, 0), col, .7, mat='neon')
    ring(P, (0, 1.4, 0), (r - 1.2) * .5 * .78, 12, (1.0, .2, .35), col, .75, plane='xz', mat='neon')
    cyl_v(P, r * .7, 14, (0, 8, 0), col, .7, mat='neon', tr=.82)
    T = BlockProp('Cup'); y = 0
    cyl_v(T, 3.6, .8, (0, .4, 0), 'gold', .55); cyl_v(T, 1.0, 2.0, (0, 1.8, 0), 'gold', .62); cyl_v(T, 2.2, .5, (0, 3.0, 0), 'gold', .7)
    for k, d_ in enumerate((2.6, 3.6, 4.2, 4.4)): cyl_v(T, d_, .9, (0, 3.6 + k * .9, 0), 'gold', .62 + k * .05)
    for sx in (-1, 1):
        for k in range(4):
            a = math.radians(90 - k * 60); T.b((.7, .7, .7), (sx * (2.2 + math.cos(a) * 1.1), 5.0 + math.sin(a) * 1.2, 0), 'gold', .7)
    T.b((1.0, 1.0, 1.0), (0, 7.5, 0), 'gold', .85, mat='neon', rot=(45, 45, 0))
    P.put(T, (0, 9, 0))
    return P

# ------------------------------------------------------------------ treadmill
def treadmill(tier=0):
    cols = ['grass', 'stone', 'mint', 'gold', 'pink', 'fire']; c = cols[tier % len(cols)]
    P = BlockProp('Treadmill')
    chamfer_block(P, (11, 1.6, 24), (0, .6, 0), 'stone', .4, bev=.5)
    for sz in (-1, 1): P.b((9, 1.4, 1.4), (0, 1.8, sz * 10.4), 'basalt', .3, shape='cyl')            # end rollers
    P.b((7.6, .4, 20.4), (0, 1.9, 0), 'basalt', .18)
    for k in range(10): P.b((7.4, .12, .5), (0, 2.12, -9 + k * 2), 'basalt', .35)
    for k in range(4): P.b((3.2, .16, 1.0), (0, 2.2, -6 + k * 4), c, .75, mat='neon', rot=(0, 0, 0))
    for sx in (-1, 1):
        P.b((1.2, 1.6, 22), (sx * 4.6, 2.1, 0), c, .55)
        P.b((.6, 7, .6), (sx * 4.6, 5.2, -10.2), 'stone', .55); P.b((.6, 4.5, .6), (sx * 4.6, 4.4, -2), 'stone', .55)
        P.b((.5, .5, 9), (sx * 4.6, 6.6, -6.2), 'stone', .65, rot=(-10, 0, 0))                     # handrail
    P.b((10.2, .8, 1.4), (0, 8.6, -10.2), 'stone', .6)
    P.b((7, 4.2, 1.0), (0, 10.4, -10.6), 'basalt', .25, rot=(-15, 0, 0))
    P.b((6, 3.2, .3), (0, 10.4, -11.15), c, .72, mat='neon', rot=(-15, 0, 0))
    for k in range(3): P.b((.8, .8, .4), (-2 + k * 2, 8.2, -11.0), ['red', 'gold', 'mint'][k], .75, mat='neon', shape='ball')
    return P
