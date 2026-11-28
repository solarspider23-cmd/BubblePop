# Northgate Distribution prop kit: a real-looking distribution warehouse. Roblox space (X east, Y up, Z south, 1 unit = 1 stud),
# origin = bottom centre, front = -Z. 1 m ~ 3.14 studs. WALL props are built with their back on z = 0, face toward -z.
# Lean rules: faces that sit on the floor or against a neighbour are not built; small parts 6-8 sides; detail as
# single-sided decal quads (tape, labels, seams, perforation slots) instead of geometry.
from kitlib import *
import math, random

# ================================================================== pallets + loads
PW, PD, PH = 3.8, 3.1, .45          # pallet: width (x), depth (z), height

def pallet_sub(lite=False, tone=0):
    """EUR-style pallet: top deck boards, 3 block rows, stringers, bottom boards. lite = deck slab + 3 block rows (rack copies)"""
    s = Sub(); sh = lambda v: S('pallet', base=v + tone * .05, up=.2, jit=.03, seed=tone)
    if lite:
        b = box((PW, .16, PD), 0); at(b, (0, PH - .08, 0)); s.add(b, sh(.58))
        for x in (-PW / 2 + .3, 0, PW / 2 - .3):
            b = drop_bottom(at(box((.55, PH - .16, PD - .02), 0), (x, (PH - .16) / 2, 0)), 0); s.add(b, sh(.42))
        return s
    for k in range(5):                                            # top deck boards with gaps
        x = -PW / 2 + .36 + k * (PW - .72) / 4
        s.add(at(box((.68, .1, PD), 0), (x, PH - .05, 0)), sh(.6 + .06 * ((k * 3) % 2)))
    for z in (-PD / 2 + .25, 0, PD / 2 - .25):                    # stringer boards under the deck
        s.add(at(box((PW, .1, .5), 0), (0, PH - .15, z)), sh(.5))
    for x in (-PW / 2 + .3, 0, PW / 2 - .3):                      # 9 blocks
        for z in (-PD / 2 + .25, 0, PD / 2 - .25):
            s.add(drop_bottom(at(box((.55, .25, .5), 0), (x, .175, z))), sh(.4))
    for x in (-PW / 2 + .3, 0, PW / 2 - .3):                      # bottom runners
        s.add(drop_bottom(at(box((.62, .07, PD), 0), (x, .035, 0))), sh(.46))
    return s

def carton(s, size, loc, rot=0.0, tone=.55, label=True, back=True, seed=0, bev=.02):
    """one cardboard carton: box with a tape strip over the top and a blank paper label on the front"""
    w, h, d = size; b = box(size, bev)
    if not back:
        b.normal_update(); bmesh.ops.delete(b, geom=[f for f in b.faces if f.normal.z > .98], context='FACES')
    drop_bottom(at(b, (0, h / 2, 0)), 0)
    sub = Sub(); sub.add(b, S('cardboard', base=tone, up=.18, jit=.04, seed=seed))
    sub.add(quad(w + .02, .32, 'y', h + .012), S('cardboard', base=tone - .14, up=0, jit=0))         # tape
    sub.add(quad(.34, .32, 'z', -d / 2 - .012, 0, h - .16), S('cardboard', base=tone - .14, up=0, jit=0))
    if label: sub.add(quad(.6, .42, 'z', -d / 2 - .014, w * .18, h * .5), S('paper', base=.82, up=0, jit=0))
    sub.emit(s, loc, [(0, rot, 0)])

def load_cartons(s, rng, h_max=4.2, back=True, cols=2, rows=2, lite=False):
    if lite: rows = 1
    """carton stack on a pallet deck (y = PH)"""
    cw, cd = PW / cols, PD / rows; lay = rng.randint(2, 3) if h_max > 3 else 2; ch = min(1.5, (h_max - .1) / lay)
    tone = rng.uniform(.48, .62)
    for L in range(lay):
        for i in range(cols):
            for j in range(rows):
                if L == lay - 1 and rng.random() < .12: continue
                x = -PW / 2 + cw * (i + .5) + rng.uniform(-.04, .04); z = -PD / 2 + cd * (j + .5) + rng.uniform(-.04, .04)
                carton(s, (cw - .05, ch - .02, cd - .05), (x, PH + L * ch, z), rng.uniform(-1.2, 1.2), tone + rng.uniform(-.04, .04),
                       label=(j == 0), back=back or j < rows - 1, seed=rng.randint(0, 99), bev=0 if lite else .02)

def load_wrapped(s, rng, h_max=4.2, back=True):
    """stretch-wrapped carton block: brown cartons seen through a milky film; banding straps, top sheet, label"""
    h = rng.uniform(3.0, h_max); w, d = PW - .1, PD - .1
    b = rbox((w, h, d), .14, 1); drop_bottom(at(b, (0, PH + h / 2, 0)), PH)
    if not back:
        b.normal_update(); bmesh.ops.delete(b, geom=[f for f in b.faces if f.normal.z > .98], context='FACES')
    s.add(b, SF(lambda c, n: ('cardboard', .5) if n.y < .5 else ('cardboard', .62), up=.1))
    for y in [PH + h * t for t in (.33, .66)]:                       # carton seams through the film
        s.add(quad(w - .2, .06, 'z', -d / 2 - .012, 0, y), S('cardboard', base=.3, up=0, jit=0))
    for x in (-w / 4, w / 4): s.add(quad(.06, h - .3, 'z', -d / 2 - .012, x, PH + h / 2), S('cardboard', base=.3, up=0, jit=0))
    for k in range(3):                                               # film bands round all four sides (milky, low contrast)
        y = PH + h * (.18 + .3 * k); bh = h * rng.uniform(.16, .22)
        s.add(quad(w + .02, bh, 'z', -d / 2 - .02, 0, y), S('cardboard', base=.74, up=0, jit=0))
        s.add(quad(d + .02, bh, 'x', -w / 2 - .02, 0, y, flip=True), S('cardboard', base=.7, up=0, jit=0))
        s.add(quad(d + .02, bh, 'x', w / 2 + .02, 0, y), S('cardboard', base=.7, up=0, jit=0))
        if back: s.add(quad(w + .02, bh, 'z', d / 2 + .02, 0, y, flip=True), S('cardboard', base=.7, up=0, jit=0))
    s.add(quad(w * .9, d * .9, 'y', PH + h + .015), S('paper', base=.78, up=0, jit=0))            # top sheet
    for x in (-w / 3, w / 3):                                          # banding straps over the top + front
        s.add(quad(.12, d + .04, 'y', PH + h + .03, x), S('rubber', base=.25, up=0, jit=0))
        s.add(quad(.12, h, 'z', -d / 2 - .03, x, PH + h / 2), S('rubber', base=.25, up=0, jit=0))
    s.add(quad(.8, .6, 'z', -d / 2 - .035, -w * .1, PH + h * .55), S('paper', base=.9, up=0, jit=0))

def drum_bm(h=2.9, r=.95, sides=12, lite=False):
    """steel 200 l drum: rolled rims + two rolling hoops"""
    if lite: return lathe([(r - .05, 0), (r, .1), (r, h * .33), (r + .04, h * .33 + .05), (r, h * .33 + .1), (r, h * .66), (r + .04, h * .66 + .05), (r, h * .66 + .1), (r, h - .1), (r - .1, h), (0, h - .04)], 8)
    p = [(0, .02), (r - .06, .02), (r, .08), (r, .2), (r - .03, .25), (r - .03, h * .33 - .1), (r + .04, h * .33), (r - .03, h * .33 + .1),
         (r - .03, h * .66 - .1), (r + .04, h * .66), (r - .03, h * .66 + .1), (r - .03, h - .25), (r, h - .2), (r, h - .06), (r - .08, h), (r - .14, h - .06), (0, h - .06)]
    return lathe(p, sides)

def load_drums(s, rng, col='plastic', lite=False):
    for x in (-PW / 4 + .02, PW / 4 - .02):
        for z in (-PD / 4, PD / 4):
            c = rng.choice([col, col, 'steel'])
            d = drum_bm(lite=lite); at(d, (x, PH, z), (0, rng.uniform(0, 90), 0)); s.add(d, S(c, base=.5 if c != 'steel' else .55, up=.3, jit=0), True)
            s.add(at(cyl(.12, .06, 6), (x + .45, PH + 2.84, z)), S('steel', base=.5, up=.2, jit=0))
    s.add(quad(.12, PD + .1, 'y', PH + 2.95, 0), S('rubber', base=.25, up=0, jit=0))

def load_sacks(s, rng, lite=False):
    """pillowy bags in brick bond, 4 layers"""
    for L in range(4):
        for k in range(3):
            if L % 2 == 0: size = (PW - .2, .55, PD / 3 - .06); loc = (0, PH + .3 + L * .55, -PD / 3 + k * PD / 3)
            else: size = (PW / 3 - .06, .55, PD - .2); loc = (-PW / 3 + k * PW / 3, PH + .3 + L * .55, 0)
            b = rbox(size, .24, 1 if lite else 2)
            if lite: drop_bottom(b, -size[1] / 2)
            for v in b.verts: v.co.y *= 1 - .25 * (abs(v.co.x) / (size[0] / 2)) ** 2 * (abs(v.co.z) / (size[2] / 2)) ** 2
            s.add(at(b, loc), S('paper', base=.62 + rng.uniform(-.04, .04), up=.25, jit=.02), True)

def load_crates(s, rng, lite=False):
    """blue plastic stacking crates with hand-hole recesses"""
    for L in range(4):
        for i in (-1, 1):
            x = i * PW / 4; y = PH + L * .95
            s.add(at(box((PW / 2 - .1, .9, PD - .1), 0 if lite else .06), (x, y + .45, 0)), S('plastic', base=.48, up=.25, jit=.02))
            s.add(quad(.8, .22, 'z', -PD / 2 + .04, x, y + .66), S('rubber', base=.15, up=0, jit=0))
            s.add(quad(PW / 2 - .3, .06, 'z', -PD / 2 + .04, x, y + .3), S('plastic', base=.3, up=0, jit=0))

def pallet_load(kind, seed=0, lite=False, h_max=4.2, back=True):
    rng = random.Random(seed); s = Sub()
    pallet_sub(lite, seed % 3).emit(s)
    if kind == 'cartons': load_cartons(s, rng, h_max, back, lite=lite)
    elif kind == 'wrapped': load_wrapped(s, rng, h_max, back)
    elif kind == 'drums': load_drums(s, rng, lite=lite)
    elif kind == 'sacks': load_sacks(s, rng, lite)
    elif kind == 'crates': load_crates(s, rng, lite)
    return s

def floor_pallet(kind='wrapped', seed=0):
    P = Prop('Pallet%s%d' % (kind.capitalize(), seed)); pallet_load(kind, seed, False, 5.0).emit(P); return P

def pallet_stack(n=8, seed=0):
    """a stack of empty pallets, slightly misaligned"""
    P = Prop('PalletStack%d' % seed); rng = random.Random(seed)
    for k in range(n): pallet_sub(False, k % 3).emit(P, (rng.uniform(-.12, .12), k * PH, rng.uniform(-.12, .12)), [(0, rng.uniform(-2.5, 2.5), 0)])
    return P

# ================================================================== pallet racking
BAY = 9.0; FD = 3.4; FLUE = .6; LEVELS = (5.0, 10.0, 15.0); UH = 21.0     # bay length, frame depth, flue, beam levels, upright height

def upright_frame(s, x, z0, z1, h=UH):
    """one rack frame: two perforated posts (z0 aisle side, z1 flue side), base plates, zig-zag bracing"""
    out = -1 if z0 < z1 else 1                                       # aisle direction
    for z in (z0, z1):
        p = box((.32, h, .3), .02); drop_bottom(at(p, (x, h / 2, z)), 0); s.add(p, S('rack', base=.5, up=.2, jit=0))
        if z == z0:                                                   # perforation slot line down the aisle face
            s.add(quad(.07, h - 1.0, 'z', z + out * .152, x, h / 2, flip=out > 0), S('rack', base=.12, up=0, jit=0))
        s.add(drop_bottom(at(box((.6, .08, .55), 0), (x, .04, z))), S('steel', base=.5, up=.2, jit=0))
        for dx in (-.2, .2): s.add(at(cyl(.05, .1, 6), (x + dx, .08, z)), S('steel', base=.7, up=.2, jit=0))
    n = 8; zs = (z0 + .1 * (1 if z1 > z0 else -1), z1 - .1 * (1 if z1 > z0 else -1))
    for k in range(n):
        y0 = .9 + k * (h - 1.8) / n; y1 = y0 + (h - 1.8) / n
        a, b = (zs[0], zs[1]) if k % 2 == 0 else (zs[1], zs[0])
        s.add(tube([V(x, y0, a), V(x, y1, b)], .07, 4, False, False), S('rack', base=.45, up=.2, jit=0))
    for y in (.9, h - .9): s.add(tube([V(x, y, zs[0]), V(x, y, zs[1])], .07, 4, False, False), S('rack', base=.45, up=.2, jit=0))

def beam_pair(s, x0, x1, y, zf, zb, conn=True):
    """two step beams at level y between uprights x0..x1: front (zf, aisle side) + back (zb); connector plates; pallet supports"""
    L = x1 - x0 - .32
    for z, front in ((zf, True), (zb, False)):
        b = box((L, .5, .18), .02); at(b, ((x0 + x1) / 2, y - .25, z)); s.add(b, S('beam', base=.55, up=.25, jit=0))
        if front and conn:
            for x in (x0 + .32, x1 - .32): s.add(at(box((.26, .8, .22), 0), (x, y - .3, z)), S('beam', base=.4, up=.2, jit=0))
            s.add(quad(L - .8, .03, 'z', z - .095 if zf < zb else z + .095, (x0 + x1) / 2, y - .05, flip=zf > zb), S('beam', base=.85, up=0, jit=0))
    for k in range(2):                                                # pallet support bars across the beams
        x = x0 + 2.2 + k * (L - 4.1)
        s.add(at(box((.12, .08, abs(zb - zf) + .1), 0), (x, y + .04, (zf + zb) / 2)), S('steel', base=.5, up=.2, jit=0))

LOAD_MIX = ['cartons', 'cartons', 'wrapped', 'wrapped', 'wrapped', 'crates', 'cartons', None]

def rack_bay(seed=0, double=True, fill=.8):
    """one 9-stud bay of selective pallet racking, local front (aisle) = -z. double = back-to-back with a second aisle at +z.
    Uprights at the bay's -x end only: rows add RackEnd at the far end. 4 storage levels (floor + 3 beams), 2 pallets each."""
    P = Prop('RackBay%s%d' % ('D' if double else 'S', seed)); rng = random.Random(seed * 31 + 7); s = Sub()
    sides = [(-FLUE / 2 - FD, -FLUE / 2)] + ([(FLUE / 2 + FD, FLUE / 2)] if double else [])
    for zf, zb in sides: upright_frame(s, -BAY / 2, zf, zb)
    if double:
        for y in (6.5, 14.0): s.add(at(box((.14, .14, FLUE + .1), 0), (-BAY / 2, y, 0)), S('steel', base=.55, up=.2, jit=0))
    for zf, zb in sides:
        sgn = -1 if zf < 0 else 1
        for y in LEVELS: beam_pair(s, -BAY / 2, BAY / 2, y, zf + sgn * .09 * -1, zb - sgn * .09 * -1)
        for li, y in enumerate((0.0,) + LEVELS):
            hmax = 4.2 if li < 3 else 4.6
            for px in (-BAY / 4, BAY / 4):
                if rng.random() > fill: continue
                kind = rng.choice(LOAD_MIX) or 'cartons'
                if li == 0 and kind in ('sacks', 'crates'): kind = 'wrapped'
                ld = pallet_load(kind, rng.randint(0, 999), lite=True, h_max=hmax, back=False)
                zc = (zf + zb) / 2; yy = y + (.0 if li == 0 else .08)
                ld.emit(s, (px + rng.uniform(-.1, .1), yy, zc + sgn * .1 * 0), [(0, 0 if sgn < 0 else 180, 0)])
                if li > 0: s.add(quad(.9, .32, 'z', zf + sgn * .012, px, y - .25, flip=sgn > 0), S('paper', base=.9, up=0, jit=0))
    s.emit(P)
    return P

def rack_end(double=True, frame=True):
    """the last upright frames of a row + yellow end-of-aisle frame protectors (frame=False: guard only, RackGuard)"""
    P = Prop(('RackEnd%s' if frame else 'RackGuard%s') % ('D' if double else 'S')); s = Sub()
    sides = [(-FLUE / 2 - FD, -FLUE / 2)] + ([(FLUE / 2 + FD, FLUE / 2)] if double else [])
    for zf, zb in (sides if frame else []): upright_frame(s, 0, zf, zb)
    if double and frame:
        for y in (6.5, 14.0): s.add(at(box((.14, .14, FLUE + .1), 0), (0, y, 0)), S('steel', base=.55, up=.2, jit=0))
    s.emit(P)
    z0 = -FLUE / 2 - FD - .5; z1 = (FLUE / 2 + FD + .5) if double else -FLUE / 2 + .5
    poly = [(.25, 0), (.25, 1.6), (0, 1.9), (-.25, 1.6), (-.25, 0)]
    for z in (z0, z1):                                               # bent-plate post guards
        g = box((.9, 1.3, .9), .12); drop_bottom(at(g, (.5, .65, z)), 0); P.add(g, S('yellow', base=.6, up=.25, jit=0))
        for k in range(2): P.add(quad(.92, .22, 'z', z - .452, .5, .35 + k * .5), S('rubber', base=.2, up=0, jit=0))
    rail = box((.5, .55, abs(z1 - z0) - 1.1), .08); at(rail, (.75, .62, (z0 + z1) / 2)); P.add(rail, S('yellow', base=.62, up=.25, jit=0))
    for z in (z0 + 1.2, z1 - 1.2, (z0 + z1) / 2):
        P.add(drop_bottom(at(box((.5, .35, .5), .05), (.75, .17, z))), S('yellow', base=.45, up=.2, jit=0))
    return P

# vehicles + structure + equipment live in their own modules
from wh_veh import *
from wh_struct import *
from wh_equip import *
from wh_yard import *
