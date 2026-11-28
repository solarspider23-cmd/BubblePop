# Frostpeak prop kit. Reuses the Whispering Grove kit (rocks, lanterns, fences, crates, barrels ...) with a winter
# palette: same ramp names, new colours ('grass' = snowfield, 'moss' = snow caps, 'leaf2' = ice), so every grove prop
# comes out snowy. New pieces: log cabin, snow pine, roll well, market stall, ice-fishing hut, Frost Spire.
import sys, os, math, random
SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SKILL, 'examples', 'whispering_grove'))
import forest_props as G
from forest_props import Prop, S, at, blob, box, cyl, spike, tube, hull, rock, rock_pts, ngon_prism, bool_diff, arch_frame, arch_tunnel, arch_prism, arch_cap
from pro_lib import Palette
from mathutils import Vector
import bmesh

G.PAL = Palette({
    'bark':   ('#3a2a20', '#5e4535', '#8a6a52'),
    'leaf':   ('#20503a', '#356e52', '#6aa088'),
    'leaf2':  ('#5aa6c8', '#9fd8ee', '#e6f8ff'),     # ice
    'pine':   ('#0f3a30', '#1f5e4a', '#4a8a72'),
    'grass':  ('#9fb4cc', '#d6e2f0', '#f6faff'),     # snowfield
    'moss':   ('#b8c8dc', '#e4eef8', '#ffffff'),     # snow caps
    'dirt':   ('#5e5048', '#8a7a6e', '#b4a698'),     # trodden snow / slush path
    'stone':  ('#4c5262', '#7c8496', '#b8c0d0'),
    'stonew': ('#5a5560', '#8e8894', '#c8c2cc'),
    'wood':   ('#5a3420', '#8e5a34', '#c8885a'),
    'wooddk': ('#2c1a12', '#4a2e20', '#74503a'),
    'red':    ('#6e1a1a', '#b83226', '#e8644a'),
    'cream':  ('#b8ad98', '#e6dcc6', '#fff8ea'),
    'gold':   ('#8a5a10', '#dca222', '#ffe680'),
    'cloth':  ('#6a1f30', '#a8334a', '#e06a7a'),     # stall awnings (berry red)
})
G.GLOW.update({'window': '#ffb24a', 'ice': '#5fe0ff', 'crystal': '#5fd4ff'})   # grove crystals turn to ice here
G.GLOW_E.update({'window': 3.0, 'ice': 1.2})

# ------------------------------------------------------------------ trees
def snow_pine(seed, h=30.0):
    """grove pine re-shaded: every up-facing tier face carries snow"""
    P = G.pine(seed, h); P.name = 'SnowPine%d' % seed
    # add snow caps: a thin flattened copy on each tier is overkill -> shade via a second pass on up faces
    rng = random.Random(seed)
    for i in range(5):
        y = h * (.22 + .145 * i); R = h * .3 * (1 - i * .17) * .78
        cap = hull(rock_pts((R, h * .05, R), n=18, seed=seed + i))
        P.add(at(cap, (0, y + h * .1, 0)), S('moss', base=.7, up=.2, jit=.04))
    return P

# ------------------------------------------------------------------ buildings
def cabin(seed=1, w=14.0, d=11.0, wall_h=7.2, door_w=3.4, door_h=6.0):
    """log cabin: stacked logs with crossed corners, the door gap is left IN the log courses (no pasted plate),
    windows likewise; plank gables, pitched roof with a snow blanket, icicles, stone chimney."""
    rng = random.Random(seed); P = Prop('Cabin%d' % seed)
    P.add(at(box((w + 1.6, 1.6, d + 1.6), .2), (0, .2, 0)), S('stone', base=.45, up=.2, jit=.06, seed=seed))    # footing (0.6 below)
    lr = .5; n = int(wall_h / (2 * lr * .92))
    win = [(-w / 2, 0, 2.2, 2.6, 4.2)]          # (side x, z centre, half width, sill y, top y) on the west wall
    for i in range(n):
        y = 1.0 + lr + i * 2 * lr * .92; odd = i % 2
        bark = S('bark' if odd else 'wood', base=.5, up=.15, jit=.05, seed=seed * 10 + i)
        for sz in (-1, 1):                       # front (+z) / back logs along x
            zc = sz * d / 2 + (0 if odd else 0)
            spans = [(-w / 2 - .9, w / 2 + .9)]
            if sz > 0 and y < 1.0 + door_h: spans = [(-w / 2 - .9, -door_w / 2), (door_w / 2, w / 2 + .9)]
            for x0, x1 in spans:
                P.add(tube([Vector((x0, y + (lr if odd else 0) * 0, zc)), Vector((x1, y, zc))], lr, sides=8), bark)
        for sx in (-1, 1):                       # side logs along z, offset half a log (interlock)
            yy = y + lr * .92
            spans = [(-d / 2 - .9, d / 2 + .9)]
            for wx, wz, hw_, s0, s1 in win:
                if sx * w / 2 == wx and s0 < yy < s1: spans = [(-d / 2 - .9, wz - hw_), (wz + hw_, d / 2 + .9)]
            if sx > 0 and 2.6 < yy < 4.2: spans = [(-d / 2 - .9, -2.2), (2.2, d / 2 + .9)]
            for z0, z1 in spans:
                P.add(tube([Vector((sx * w / 2, yy, z0)), Vector((sx * w / 2, yy, z1))], lr, sides=8),
                      S('wood' if odd else 'bark', base=.5, up=.15, jit=.05, seed=seed * 20 + i))
    top = 1.0 + n * 2 * lr * .92
    # window frames + warm panes set back inside the wall
    for sx in (-1, 1):
        x = sx * w / 2
        P.gadd(at(box((.2, 1.7, 4.0)), (x - sx * .25, 3.4, 0)), 'window')
        P.add(at(box((.5, .3, 4.8), .05), (x + sx * .3, 2.45, 0)), S('wooddk', base=.5))                 # sill
        P.add(at(blob(.7, seed + sx, n=12, sq=.4), (x + sx * .35, 2.7, 0)), S('moss', base=.8))           # snow on sill
        P.add(at(box((.35, 1.9, .3)), (x + sx * .1, 3.4, 0)), S('wooddk', base=.45))                       # mullion
        P.add(at(box((.35, .28, 4.0)), (x + sx * .1, 3.4, 0)), S('wooddk', base=.45))                      # transom
        for sz in (-1, 1):                                                   # open shutters, slightly angled
            sh = box((.22, 2.0, 1.9), .04)
            P.add(at(sh, (x + sx * .55, 3.4, sz * 3.25), (0, sz * sx * 18, 0)), S('red', base=.42, jit=.04, seed=sz + 5))
            for yy in (2.8, 4.0):
                P.add(at(box((.26, .14, 1.7)), (x + sx * .68, yy, sz * 3.25), (0, sz * sx * 18, 0)), S('red', base=.3))
    # door: planks recessed in the gap + frame boards + handle + lantern
    for k in range(5):                                                       # vertical planks
        pw = (door_w - .1) / 5
        P.add(at(box((pw - .06, door_h - .1, .35), .03), (-door_w / 2 + .05 + pw * (k + .5), 1.0 + (door_h - .1) / 2, d / 2 - .55)),
              S('wood', base=.42 + (k % 2) * .08, jit=.03, seed=30 + k))
    for y in (2.2, 1.0 + door_h - 1.4):                                      # iron hinge straps + bolts
        P.add(at(box((door_w * .7, .28, .12), .03), (-door_w * .12, y, d / 2 - .33)), S('stone', base=.22, jit=0))
        P.add(at(cyl(.2, .14, sides=6), (-door_w / 2 + .35, y, d / 2 - .3), (90, 0, 0)), S('stone', base=.3))
    P.add(at(box((.12, 1.0, .14), .03), (door_w / 2 - .55, 3.7, d / 2 - .3)), S('stone', base=.25))   # pull bar
    for x in (-door_w / 2 - .15, door_w / 2 + .15):
        P.add(at(box((.45, door_h + .4, .9), .05), (x, 1.0 + door_h / 2, d / 2)), S('wood', base=.62))
    P.add(at(box((door_w + 1.2, .5, .9), .05), (0, 1.0 + door_h + .25, d / 2)), S('wood', base=.62))
    P.add(at(blob(.2, 1, n=10), (door_w / 2 - .6, 3.6, d / 2 - .3)), S('gold', base=.7))
    P.add(at(box((door_w + 1.6, .5, 2.2), .08), (0, .95, d / 2 + 1.2)), S('stone', base=.5, up=.2))      # step
    # gables (plank triangles) + roof
    pitch = 34; rh = (w / 2 + .2) * math.tan(math.radians(pitch))
    for sz in (-1, 1):
        g = ngon_prism([(-w / 2 - .1, 0), (0, rh), (w / 2 + .1, 0)][::-1], -.25, .25)
        P.add(at(g, (0, top - .3, sz * d / 2), (-90, 0, 0)), S('wood', base=.6, jit=.06, seed=7))      # apex up
    over = 1.6; L = (w / 2 + over) / math.cos(math.radians(pitch))
    for sx in (-1, 1):
        cx = sx * (w / 2 + over) / 2; cy = top + rh - (w / 2 + over) / 2 * math.tan(math.radians(pitch)) + .2
        P.add(at(box((L, .5, d + 3.2), .08), (cx, cy, 0), (0, 0, -sx * pitch)), S('wooddk', base=.5, jit=.03))
        snow = box((L - .2, 1.1, d + 3.4), .4)
        P.add(at(snow, (cx - sx * math.sin(math.radians(pitch)) * -.75, cy + math.cos(math.radians(pitch)) * .75, 0), (0, 0, -sx * pitch)),
              S('moss', base=.72, up=.2, jit=.02))
        for k in range(9):                       # icicles along the eave
            z = -d / 2 - 1.2 + (d + 2.4) * k / 8
            ex = sx * (w / 2 + over - .3); ey = cy - (L / 2 - .3) * math.sin(math.radians(pitch)) - .1
            P.gadd(at(spike(.16, rng.uniform(.6, 1.6), sides=4, shoulder=.2), (ex, ey, z), (180, 0, 0)), 'ice')
    ridge_y = top + rh + .35
    P.add(tube([Vector((0, ridge_y, -d / 2 - 1.7)), Vector((0, ridge_y, d / 2 + 1.7))], .45, sides=6), S('wooddk', base=.5))   # ridge beam
    P.add(at(box((1.6, .9, d + 3.4), .35), (0, ridge_y + .45, 0)), S('moss', base=.8, up=.15))                                  # snow ridge cap
    cy0 = top - .5; cy1 = top + rh * .55 + 3.5                                                    # chimney from the wall top up through the roof
    k = 0; y = cy0
    while y < cy1 - .1:                                                      # stone courses, alternating shades
        hgt = min(.75, cy1 - y)
        P.add(at(box((2.2 + (k % 2) * .12, hgt - .05, 2.2 + ((k + 1) % 2) * .12), .08), (w * .28, y + hgt / 2, -d * .22)),
              S('stone', base=.44 + (k % 3) * .06, jit=.02, seed=40 + k)); y += hgt; k += 1
    # woodpile against the back wall: split log ends under a little lean-to
    wx0 = -w * .22
    for row in range(4):
        for c in range(6 - row):
            lx = wx0 - 2.2 + c * .78 + row * .39 + rng.uniform(-.05, .05)
            P.add(at(cyl(.36, 1.6, sides=7), (lx, 1.4 + row * .66, -d / 2 - 1.9), (90, 0, 0)), S('wood', base=.5 + rng.uniform(-.06, .06), jit=.02))
    P.add(at(box((5.6, .22, 2.4), .05), (wx0, 4.4, -d / 2 - 1.5), (-14, 0, 0)), S('wooddk', base=.5))
    P.add(at(box((5.4, .5, 2.4), .2), (wx0, 4.75, -d / 2 - 1.5), (-14, 0, 0)), S('moss', base=.8))
    for sx in (-1, 1):
        P.add(at(cyl(.16, 3.6, sides=5, y0=.8), (wx0 + sx * 2.6, 0, -d / 2 - 2.5)), S('wooddk', base=.45))
    P.add(at(box((2.7, .5, 2.7), .08), (w * .28, top + rh * .55 + 3.7, -d * .22)), S('stone', base=.6))
    P.add(at(blob(1.2, 5, n=12, sq=.45), (w * .28, top + rh * .55 + 4.1, -d * .22)), S('moss', base=.8))
    return P

def snowman(seed=1):
    rng = random.Random(seed); P = Prop('Snowman%d' % seed)
    for r, y in ((1.7, 1.3), (1.25, 3.6), (.9, 5.4)):
        P.add(at(blob(r, seed + int(y * 10), n=30, sq=.95), (0, y, 0)), S('moss', grad=(-r, r, .45, .92), up=.1, jit=.02))   # shaded so it reads on snow
    P.add(at(spike(.18, 1.1, sides=6, shoulder=.2), (0, 5.45, .82), (90, 0, 0)), S('gold', base=.42))              # carrot
    for sx in (-1, 1): P.add(at(blob(.13, 3 + sx, n=8, sq=1), (sx * .33, 5.75, .78)), S('wooddk', base=.1))
    for k in range(3): P.add(at(blob(.14, 9 + k, n=8, sq=1), (0, 3.2 + k * .5, 1.18 - k * .05)), S('wooddk', base=.1))
    circ = [Vector((math.cos(a * math.tau / 16) * .95, 0, math.sin(a * math.tau / 16) * .95)) for a in range(17)]
    P.add(at(tube(circ, .24, sides=5, cap0=False, cap1=False), (0, 4.75, 0)), S('cloth', base=.55))                 # scarf
    P.add(at(box((.42, 1.3, .14), .05), (.55, 4.2, .85), (8, 0, 10)), S('cloth', base=.5))
    P.add(cyl(.95, .14, sides=10, y0=6.05), S('wooddk', base=.3)); P.add(cyl(.62, 1.1, sides=10, y0=6.15), S('wooddk', base=.25))
    for sx in (-1, 1):
        P.add(tube([Vector((sx * 1.0, 3.8, 0)), Vector((sx * 2.0, 4.5, .2)), Vector((sx * 2.6, 5.1, .1))], [.09, .07, .04], sides=4), S('bark', base=.4))
    return P

def sled(seed=1):
    P = Prop('Sled%d' % seed)
    for sx in (-1, 1):
        run = [Vector((sx * .9, .25, -2.2)), Vector((sx * .9, .1, 1.4)), Vector((sx * .9, .45, 2.3)), Vector((sx * .9, 1.1, 2.4))]
        P.add(tube(run, .12, sides=5), S('red', base=.45))
        for z in (-1.4, .9): P.add(at(box((.14, .7, .14)), (sx * .9, .55, z)), S('wooddk', base=.4))
    for k in range(5): P.add(at(box((2.2, .14, .6), .04), (0, .95, -1.7 + k * .78)), S('wood', base=.6, jit=.04, seed=k))
    return P

def bench(seed=1):
    P = Prop('Bench%d' % seed)
    for k in range(3): P.add(at(box((4.6, .22, .42), .05), (0, 1.55, -.5 + k * .48)), S('wood', base=.55, jit=.04, seed=k))
    for k in range(2): P.add(at(box((4.6, .22, .36), .05), (0, 2.3 + k * .5, -.85), (-12, 0, 0)), S('wood', base=.58, jit=.04, seed=k + 3))
    for sx in (-1, 1):
        P.add(at(box((.3, 1.6, 1.4), .05), (sx * 1.9, .7, 0)), S('stone', base=.3))
        P.add(at(box((.26, 1.6, .26)), (sx * 1.9, 2.3, -.95), (-12, 0, 0)), S('stone', base=.3))
    P.add(at(box((4.4, .35, 1.3), .15), (0, 1.8, 0)), S('moss', base=.8))
    return P

def roll_well(seed=3):
    """village-square roll well: stone ring, timber A-frame + roof, rope + bucket, glowing ice core in the water"""
    P = Prop('RollWell'); rng = random.Random(seed)
    for k in range(14):                           # stone ring of chunky blocks
        a = k * math.tau / 14
        P.add(at(box((2.0, 2.4, 1.4), .18), (math.cos(a) * 3.6, 1.0, math.sin(a) * 3.6), (rng.uniform(-3, 3), -math.degrees(a) + 90, 0)),
              S('stone', base=.42 + rng.uniform(0, .14), up=.2, jit=.03, seed=k))
    P.add(cyl(4.5, .5, sides=14, y0=2.2, r2=4.4), S('stonew', base=.6, up=.2))
    P.add(at(blob(1.4, 8, n=14, sq=.4), (2.6, 2.8, 2.0)), S('moss', base=.85))
    P.gadd(cyl(3.0, .2, sides=14, y0=1.6), 'ice')
    P.gadd(at(hull([Vector(p).normalized() * 1.3 for p in [(1, 1, 1), (-1, 1, -1), (1, -1, -1), (-1, -1, 1), (0, 1.8, 0), (0, -1.8, 0)]]), (0, 3.8, 0), (0, 30, 0)), 'ice')
    for sx in (-1, 1):
        P.add(at(cyl(.32, 8.2, sides=6, y0=0), (sx * 4.2, 0, 0)), S('wood', grad=(0, 8, .35, .65)))
    P.add(tube([Vector((-4.6, 7.0, 0)), Vector((4.6, 7.0, 0))], .3, sides=8), S('wooddk', base=.5))
    P.add(cyl(.12, 2.2, sides=4, y0=4.8), S('cream', base=.5))                                              # rope
    P.add(tube([Vector((4.6, 7.0, 0)), Vector((5.3, 7.0, 0)), Vector((5.3, 6.0, 0)), Vector((5.9, 6.0, 0))], .13, sides=5), S('stone', base=.3))  # crank
    P.add(cyl(.55, .9, sides=8, y0=4.0, r2=.65), S('wood', base=.5))                                        # bucket
    for sx in (-1, 1):
        roof = box((6.6, .4, 7.4), .08)
        P.add(at(roof, (sx * 2.5, 9.1, 0), (0, 0, -sx * 32)), S('wooddk', base=.55))
        P.add(at(box((6.2, .8, 7.6), .3), (sx * 2.45, 9.65, 0), (0, 0, -sx * 32)), S('moss', base=.75))
    return P

def market_stall(seed=4, w=7.0, d=4.5):
    rng = random.Random(seed); P = Prop('Stall%d' % seed)
    P.add(at(box((w, 2.6, d), .1), (0, 1.3 - .3, 0)), S('wood', base=.55, jit=.05, seed=seed))             # counter
    P.add(at(box((w + .3, .3, d + .3), .06), (0, 2.45, 0)), S('wooddk', base=.55))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(at(cyl(.22, 6.4, sides=6, y0=-.3), (sx * (w / 2 - .2), 0, sz * (d / 2 - .2))), S('wooddk', grad=(0, 6, .35, .6)))
    for i in range(6):                            # striped awning: alternating cloth / cream slats
        z = -d / 2 - .6 + (d + 1.6) * (i + .5) / 6
        P.add(at(box((w + 1.0, .32, (d + 1.6) / 6 + .35)), (0, 6.3 - (z + d / 2) * .32, z), (18, 0, 0)),   # overlapping slats = one awning
              S('cloth' if i % 2 == 0 else 'cream', base=.6, jit=.02))
    P.add(at(box((w + .8, .7, d + 1.4), .3), (0, 6.95 - .25, -.4), (18, 0, 0)), S('moss', base=.78))             # snow on awning
    for k in range(9):                                                       # string of warm bulbs along the awning edge
        x = -w / 2 - .3 + (w + .6) * k / 8; sag = math.sin(math.pi * k / 8) * .35
        P.gadd(at(blob(.17, 50 + k, n=8, sq=1), (x, 5.0 - sag, d / 2 + .75)), 'window')
    for k in range(5):                            # goods: crates of glowing ice shards / jars
        x = -w / 2 + .9 + k * (w - 1.8) / 4
        P.add(at(box((1.0, .6, .9), .05), (x, 2.9, .4)), S('wood', base=.6, seed=k))
        P.gadd(at(spike(.25, rng.uniform(.6, 1.0), sides=5, shoulder=.6), (x, 3.2, .4)), 'ice')
    return P

def fishing_hut(seed=5, w=5.2, d=4.8, h=4.2):
    """ice-fishing shanty: board walls on skids, door + window, stovepipe, ridge-capped snowy roof,
    an ice hole with a rod stand and a bucket out front (all one prop so it stays together)"""
    rng = random.Random(seed); P = Prop('FishHut%d' % seed)
    for sx in (-1, 1):                                                      # skids
        P.add(tube([Vector((sx * (w / 2 - .5), .25, -d / 2 - .6)), Vector((sx * (w / 2 - .5), .25, d / 2 + .6))], .25, sides=6), S('wooddk', base=.45))
    n = 7
    for i in range(n):                                                      # horizontal boards, slight overlap
        y = .55 + (i + .5) * (h / n)
        for sz in (-1, 1):
            P.add(at(box((w, h / n + .06, .24), .03), (0, y, sz * d / 2)), S('red', base=.42 + (i % 2) * .06, jit=.02, seed=i))
        for sx in (-1, 1):
            P.add(at(box((.24, h / n + .06, d), .03), (sx * w / 2, y, 0)), S('red', base=.40 + (i % 2) * .06, jit=.02, seed=i + 9))
    for sx in (-1, 1):                                                      # corner trims
        for sz in (-1, 1):
            P.add(at(box((.36, h + .1, .36)), (sx * w / 2, .55 + h / 2, sz * d / 2)), S('cream', base=.75))
    tri_h = (w / 2) * math.tan(math.radians(32))
    for sz in (-1, 1):                                                      # gables
        g = ngon_prism([(-w / 2, 0), (0, tri_h), (w / 2, 0)][::-1], -.12, .12)
        P.add(at(g, (0, .55 + h - .05, sz * d / 2), (-90, 0, 0)), S('red', base=.48))
    P.add(at(box((1.4, 2.6, .2), .04), (0, 1.9, d / 2 + .1)), S('wooddk', base=.35))                       # door
    P.add(at(box((1.8, .25, .3)), (0, 3.3, d / 2 + .12)), S('cream', base=.75))
    P.add(at(blob(.12, 2, n=8), (.45, 1.9, d / 2 + .25)), S('gold', base=.7))
    P.gadd(at(box((.12, .9, 1.1)), (w / 2 + .08, 3.0, -.6)), 'window')                                      # side window
    for dz in (-.62, .62): P.add(at(box((.22, 1.2, .16)), (w / 2 + .14, 3.0, -.6 + dz)), S('cream', base=.75))
    for dy in (-.55, .55): P.add(at(box((.22, .16, 1.4)), (w / 2 + .14, 3.0 + dy, -.6)), S('cream', base=.75))
    over = .7; L = (w / 2 + over) / math.cos(math.radians(32)); top = .55 + h
    for sx in (-1, 1):
        cx = sx * (w / 2 + over) / 2; cy = top + tri_h - (w / 2 + over) / 2 * math.tan(math.radians(32)) + .15
        P.add(at(box((L, .3, d + 1.0), .05), (cx, cy, 0), (0, 0, -sx * 32)), S('wooddk', base=.5))
        P.add(at(box((L - .1, .55, d + 1.1), .22), (cx - sx * .2, cy + .4, 0), (0, 0, -sx * 32)), S('moss', base=.78))
    P.add(at(box((1.0, .55, d + 1.2), .22), (0, top + tri_h + .45, 0)), S('moss', base=.82))               # ridge cap
    P.add(cyl(.28, 3.2, sides=8, y0=top + tri_h * .4), S('stone', base=.3))                                 # stovepipe
    P.add(at(cyl(.42, .3, sides=8), (0, top + tri_h * .4 + 3.2, 0)), S('stone', base=.25))
    hx, hz = -1.4, d / 2 + 2.6                                                                              # ice hole out front
    P.add(at(cyl(.85, .12, sides=10), (hx, -.02, hz)), S('wooddk', base=.06, jit=0))
    for k in range(7):
        a = k * math.tau / 7
        P.add(at(blob(.32, k + seed, n=10, sq=.5), (hx + math.cos(a) * 1.05, .05, hz + math.sin(a) * 1.05)), S('moss', base=.85))
    P.add(tube([Vector((hx + 1.4, 0, hz - .5)), Vector((hx + 1.1, 1.1, hz - .2)), Vector((hx - .2, 2.2, hz + .3))], [.06, .05, .03], sides=4), S('wooddk', base=.4))   # rod
    P.add(at(cyl(.45, .8, sides=8, r2=.55), (hx + 2.4, 0, hz + .4)), S('stone', base=.42))                 # bucket
    return P

def frost_spire(seed=9):
    """hero: stone terrace + a 60-stud ice crystal spire with orbiting shards and a rune ring"""
    rng = random.Random(seed); P = Prop('FrostSpire')
    oct8 = lambda r: [(math.cos(a * math.tau / 8 + math.pi / 8) * r, math.sin(a * math.tau / 8 + math.pi / 8) * r) for a in range(8)][::-1]
    for i, (r, y0, y1) in enumerate(((16, -1.5, 1.5), (12.5, 1.5, 3.5), (9, 3.5, 5.2))):
        P.add(ngon_prism(oct8(r), y0, y1, .2), S('stone', base=.45 + i * .06, up=.25, jit=.04, seed=i))
        P.add(ngon_prism(oct8(r + .3), y1 - .2, y1 + .35, .1), S('moss', base=.8, up=.1))                  # snow lip
    for i in range(4):                            # front stair (+Z)
        P.add(at(box((7, 1.0, 2.2), .1), (0, -.5 + i * 1.3 + .5, 17.4 - i * 2.2)), S('stone', base=.5 + i * .03, jit=.03))
    P.gadd(at(spike(4.2, 46, sides=6, shoulder=.78), (0, 5.0, 0)), 'ice')
    for k in range(6):
        a = k * math.tau / 6; h = rng.uniform(14, 24)
        P.gadd(at(spike(rng.uniform(1.8, 2.6), h, sides=6, shoulder=.7), (math.cos(a) * 5.6, 4.6, math.sin(a) * 5.6),
                  (math.sin(a) * 24, 0, -math.cos(a) * 24)), 'ice')                      # splayed outward
    for k in range(5):
        a = k * math.tau / 5 + .3
        P.gadd(at(spike(.9, 3.4, sides=5, shoulder=.5), (math.cos(a) * 9.5, 26 + k * 3, math.sin(a) * 9.5), (30, k * 70, 20)), 'ice')
    circ = [Vector((math.cos(a * math.tau / 48) * 11, 0, math.sin(a * math.tau / 48) * 11)) for a in range(49)]
    P.gadd(at(tube(circ, .22, sides=5, cap0=False, cap1=False), (0, 30, 0), (78, 0, 0)), 'rune')
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        P.add(at(rock((1.4, 4.0, 1.0), seed=seed + k, n=20, flat=.95), (math.cos(a) * 13.5, 5.0 + 3.6, math.sin(a) * 13.5), (0, -math.degrees(a) + 90, 0)),
              S('stone', base=.45, top='moss', thr=.6, seed=k))
    return P
