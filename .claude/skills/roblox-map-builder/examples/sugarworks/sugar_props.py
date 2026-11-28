# Sugarworks Tycoon prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Machinery (Prop, S, blob, at, materials, to_kit) comes from the skill's grove module; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector
import forest_props as G
from pro_lib import Palette, box, cyl, spike, tube, hull, ngon_prism, rock_pts

G.PAL = Palette({
    'cream':   ('#d9b48f', '#fff1dc', '#ffffff'),
    'conc':    ('#e8b86a', '#ffe0a3', '#fff6dc'),     # butter floor tile (checker partner of cream)
    'asph':    ('#1f1a33', '#352c52', '#5a4f80'),
    'metal':   ('#3d4f7a', '#7f95c8', '#d4e0ff'),
    'pink':    ('#c2185b', '#ff4f9a', '#ffb3d6'),
    'mint':    ('#00897b', '#1fd6b4', '#a6ffe9'),
    'lemon':   ('#e08a00', '#ffc928', '#fff3a3'),
    'grape':   ('#4b1fa8', '#8a52ff', '#d0b8ff'),
    'choc':    ('#3a1d10', '#6e3a1f', '#a8653b'),
    'red':     ('#b0122f', '#ff3b50', '#ff9aa5'),
    'lawn':    ('#2f9a3a', '#62d14a', '#c6f57a'),
    'cliff':   ('#8a4a1e', '#d47f3a', '#ffc27a'),     # caramel / biscuit cliffs
    'sea':     ('#063a6b', '#1576b8', '#6fd3ff'),
    'sky':     ('#3a2a8e', '#ff7aa8', '#ffd7a0'),
    'orange':  ('#c44a00', '#ff8a1f', '#ffc27a'),
})
G.MATS.clear()
TEAM = ['#ff4fa3', '#33e0b0', '#ffd43a', '#9a6bff', '#ff7a3a', '#3ab6ff', '#ff4a5a', '#8cff5a']
G.GLOW.clear(); G.GLOW.update({'t%d' % i: c for i, c in enumerate(TEAM)})
G.GLOW.update({'lamp': '#ffcf7a', 'cash': '#3dff8a', 'button': '#3dff8a', 'ring': '#ff7ad9', 'furnace': '#ff8a2a', 'beam': '#7ae8ff'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 3.5, 'furnace': 3.2, 'cash': 2.2, 'button': 2.0, 'ring': 2.4, 'beam': 2.0})
for i in range(8): G.GLOW_E['t%d' % i] = 2.2
Prop, S, at, blob = G.Prop, G.S, G.at, G.blob

def dome(r, h, n=18, rings=6):
    pts = [Vector((math.cos(a) * r * math.cos(b), h * math.sin(b), math.sin(a) * r * math.cos(b)))
           for j in range(rings + 1) for b in [j / rings * math.pi / 2] for a in [i * math.tau / n for i in range(n)]]
    return hull(pts)

def sphere(r, seg=16, rings=10):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r); return bm

def torus(R, r, n=24, sides=6, y=0.0):
    pts = [Vector((math.cos(a) * R, y, math.sin(a) * R)) for a in [i * math.tau / n for i in range(n + 1)]]
    return tube(pts, r, sides=sides, cap0=False, cap1=False)

def stripes(P, pts, r, cols, seg=2, sides=8):
    """candy-cane tube: alternating colour segments along a polyline"""
    for i in range(len(pts) - 1):
        P.add(tube([pts[i], pts[i + 1]], r, sides=sides), S(cols[i % len(cols)], base=.6, up=.2, jit=.02), smooth=True)

def subdiv_line(pts, step):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        out += [a.lerp(b, k / n) for k in range(1, n + 1)]
    return out

# ------------------------------------------------------------------ plot pieces
def plot_base(size=84.0, tile=12.0):
    """the plot slab: tiled concrete, pink border, chamfered edge; top at y 1.2"""
    P = Prop('PlotBase'); n = int(size / tile)
    P.add(at(box((size + 2, 1.6, size + 2), .3), (0, -.2, 0)), S('pink', base=.55, up=.25, jit=0))
    for i in range(n):
        for j in range(n):
            x = -size / 2 + tile * (i + .5); z = -size / 2 + tile * (j + .5)
            P.add(at(box((tile - .3, .4, tile - .3), .08), (x, 1.0, z)), S('cream' if (i + j) % 2 else 'conc', base=.4 if (i + j) % 2 else .46, up=.2, jit=.02, seed=i * 9 + j))
    return P

def fence(L=12.0, team=0):
    """low cream wall + pink cap + team-colour glow strip between two posts (posts = fence_post, placed once per
    corner so neighbouring segments never stack two posts in one spot); along X, centred"""
    P = Prop('Fence%d_t%d' % (round(L), team)); W = L - 1.7       # ends just short of the posts
    P.add(at(box((W, 3.0, 1.0), .1), (0, 1.1, 0)), S('cream', base=.55, up=.2, jit=.03))
    P.add(at(box((W, .5, 1.4), .15), (0, 2.85, 0)), S('pink', base=.6))
    P.gadd(at(box((W - .2, .25, .3)), (0, 2.2, -.6)), 't%d' % team)
    P.gadd(at(box((W - .2, .25, .3)), (0, 2.2, .6)), 't%d' % team)
    return P

def fence_post():
    """one fence post: cream pillar + pink gumdrop cap"""
    P = Prop('FencePost')
    P.add(at(box((1.6, 3.2, 1.6), .2), (0, 2.2, 0)), S('cream', base=.7))          # stands on the plot slab (y .6 = slab top)
    P.add(at(blob(.95, 3, n=14, sq=.7), (0, 4.05, 0)), S('pink', base=.55))
    return P

def gate(team=0, w=16.0):
    """owner gate: two striped pillars with gumdrop tops, sign board, glowing claim pad; road side = -Z"""
    P = Prop('Gate_t%d' % team)
    for sx in (-1, 1):
        x = sx * (w / 2 + 1.3)
        P.add(at(box((2.8, 1.0, 2.8), .2), (x, .3, 0)), S('cream', base=.6))
        stripes(P, subdiv_line([Vector((x, .8, 0)), Vector((x, 12.5, 0))], 1.5), 1.05, ['pink', 'cream'])
        P.add(at(box((2.8, .8, 2.8), .2), (x, 12.6, 0)), S('cream', base=.7))
        P.add(at(spike(1.6, 2.6, sides=10, shoulder=.45), (x, 13.0, 0)), S('mint', grad=(13, 15.6, .45, .85)), smooth=True)
    P.add(at(box((w + 2.4, 4.4, .8), .2), (0, 10.4, -.2)), S('choc', base=.45))                     # sign board
    P.add(at(box((w + 3.2, .7, 1.2), .2), (0, 12.8, -.2)), S('lemon', base=.6))
    P.add(at(box((w + 3.2, .7, 1.2), .2), (0, 8.0, -.2)), S('lemon', base=.55))
    P.gadd(at(box((w - 2, 2.6, .2)), (0, 10.4, -.7)), 't%d' % team)                                    # name panel
    P.add(at(cyl(4.4, .3, sides=20, y0=-.1), (0, 0, -6.5)), S('cream', base=.75))                        # claim pad
    P.gadd(at(torus(3.6, .28, n=28, sides=5, y=.3), (0, 0, -6.5)), 't%d' % team)
    P.gadd(at(cyl(2.4, .12, sides=16, y0=.22), (0, 0, -6.5)), 't%d' % team)
    return P

def dropper(seed=1):
    """starter dropper: steel legs, lemon hopper with a funnel, candy jar on top, warning light"""
    P = Prop('Dropper%d' % seed)
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(at(box((.7, 9.2, .7), .1), (sx * 2.6, -.4 + 4.6, sz * 2.6)), S('metal', base=.45))
            P.add(at(box((1.6, .5, 1.6), .1), (sx * 2.6, -.05, sz * 2.6)), S('metal', base=.3))
    for y in (2.4, 6.0):
        for r in (0, 90):
            P.add(at(box((5.6, .35, .35)), (0, y, 0), (0, r, 0)), S('metal', base=.4))
    P.add(at(spike(3.4, 2.6, sides=4, tip=.9, rot0=45, shoulder=0), (0, 8.6, 0), (180, 0, 0)), S("lemon", base=.5))     # funnel
    P.add(at(box((7.0, 4.0, 7.0), .3), (0, 10.6, 0)), S('lemon', base=.55, up=.2))
    for sx in (-1, 1): P.add(at(box((7.2, .6, .5)), (0, 9.2 + (sx + 1) * 1.6, -3.55)), S('choc', base=.4))
    P.add(at(cyl(2.4, 4.2, sides=12, y0=12.6), (0, 0, 0)), S('mint', base=.55, up=.2), smooth=True)                   # jar
    P.add(at(cyl(2.7, .6, sides=12, y0=16.8), (0, 0, 0)), S('pink', base=.6), smooth=True)
    rng = random.Random(seed)
    for k in range(7):                                                       # candies in the jar mouth
        a = k * math.tau / 7
        P.add(at(blob(.75, k + seed, n=10, sq=.8), (math.cos(a) * 1.1, 17.6 + rng.uniform(0, .5), math.sin(a) * 1.1)),
              S(['pink', 'grape', 'lemon', 'red'][k % 4], base=.6), smooth=True)
    P.add(at(cyl(.5, 1.1, sides=8, y0=12.6), (3.0, 0, -3.0)), S('metal', base=.3))
    P.gadd(at(blob(.6, 9, n=10, sq=1), (3.0, 14.2, -3.0)), 'furnace')
    P.add(at(cyl(.9, 1.6, sides=8, y0=4.6), (0, 0, 0)), S("metal", base=.35))                                         # nozzle
    return P

def conveyor(L=12.0):
    """belt segment along X: legs, dark belt with ribs, steel side rails, lemon chevrons"""
    P = Prop('Conveyor')
    P.add(at(box((L, .5, 3.6), .05), (0, 2.6, 0)), S('asph', base=.4, jit=0))
    for k in range(int(L / 1.5)):
        P.add(at(box((.25, .12, 3.4)), (-L / 2 + .75 + k * 1.5, 2.9, 0)), S('asph', base=.62, jit=0))
    for sz in (-1, 1):
        P.add(at(box((L, .9, .45), .1), (0, 3.1, sz * 2.0)), S('metal', base=.55, up=.3))
        for x in (-L / 2 + 1, L / 2 - 1):
            P.add(at(box((.6, 2.8, .6), .1), (x, .9, sz * 1.6)), S('metal', base=.35))
        for k in range(int(L / 2)):
            P.add(at(cyl(.32, .35, sides=8), (-L / 2 + 1 + k * 2, 2.6, sz * 2.25), (90, 0, 0)), S('metal', base=.25))
    for k, x in enumerate((-L * .36, 0.0, L * .3)):                        # wrapped candies on the belt
        col = ['pink', 'mint', 'grape'][k]
        P.add(at(sphere(.62, 10, 7), (x, 3.55, 0), s=(1.2, .9, .9)), S(col, base=.62, up=.25, jit=0), smooth=True)
        for sx in (-1, 1): P.add(at(spike(.5, .6, sides=6, shoulder=0), (x + sx * .7, 3.55, 0), (0, 0, -sx * 90)), S(col, base=.75, jit=0))
    for x in (-L / 4, L / 4):
        P.add(at(ngon_prism([(-.5, -1.1), (.6, 0), (-.5, 1.1), (-.1, 0)], 2.88, 2.98), (x, 0, 0)), S('lemon', base=.7, jit=0))
    return P

def upgrader(seed=1):
    """scanner arch over the belt: two steel pillars, grape crown, glowing ring + scan beam"""
    P = Prop('Upgrader%d' % seed)
    for sz in (-1, 1):
        P.add(at(box((2.6, .8, 2.6), .2), (0, .2, sz * 4.2)), S('metal', base=.35))
        P.add(at(box((1.8, 9.0, 1.8), .2), (0, 4.8, sz * 4.2)), S('grape', base=.5, up=.25))
    P.add(at(box((3.2, 2.0, 10.8), .4), (0, 10.0, 0)), S('grape', base=.6, up=.2))
    P.add(at(spike(1.2, 2.0, sides=8, shoulder=.4), (0, 11.0, 0)), S('lemon', base=.6), smooth=True)
    P.gadd(at(torus(3.0, .35, n=28, sides=5), (0, 6.4, 0), (0, 0, 90)), 'ring')                  # ring around the belt
    for y in (3.7, 4.5): P.gadd(at(box((.12, .12, 3.6)), (0, y, 0)), 'beam')                         # scan lasers over the belt
    return P

def collector(seed=1):
    """chocolate melting vat: drum with cream drip rim, glowing mouth facing -X, lollipop chimney"""
    P = Prop('Collector%d' % seed)
    P.add(at(cyl(5.4, 1.0, sides=16, y0=-.4), (0, 0, 0)), S('metal', base=.3))
    P.add(cyl(5.0, 8.0, sides=16, y0=.6), S('choc', grad=(0, 8.6, .35, .65)), smooth=True)
    for k in range(5): P.add(cyl(5.15, .45, sides=16, y0=1.6 + k * 1.6), S('choc', base=.25, jit=0), smooth=True)
    P.add(cyl(5.4, .9, sides=16, y0=8.4), S('cream', base=.7), smooth=True)
    rng = random.Random(seed)
    for k in range(10):                                                      # drips
        a = k * math.tau / 10 + rng.uniform(-.1, .1); l = rng.uniform(1.0, 2.4)
        P.add(at(tube([Vector((0, 0, 0)), Vector((0, -l, 0))], [.55, .3], sides=6), (math.cos(a) * 5.3, 8.7, math.sin(a) * 5.3)),
              S('cream', base=.7), smooth=True)
    P.add(at(box((2.0, 3.6, 4.6), .3), (-4.7, 3.6, 0)), S('metal', base=.35))                                         # mouth frame
    P.gadd(at(box((.3, 2.6, 3.6)), (-5.75, 3.6, 0)), 'furnace')
    P.add(cyl(1.0, 5.0, sides=10, y0=9.2), S('metal', base=.45))                                                      # chimney
    stripes(P, subdiv_line([Vector((0, 14.0, 0)), Vector((0, 18.0, 0))], 1.0), .5, ['pink', 'cream'], sides=6)
    P.add(at(cyl(2.6, .9, sides=16), (0, 20.2, 0), (90, 0, 0)), S('pink', base=.6), smooth=True)
    P.add(at(torus(1.6, .35, n=18, sides=5), (0, 20.2, 0), (90, 0, 0)), S('cream', base=.8))
    return P

def cash_pad(seed=1):
    P = Prop('CashPad')
    P.add(cyl(4.2, .5, sides=20, y0=-.2), S('cream', base=.7), smooth=True)
    P.add(cyl(3.4, .25, sides=20, y0=.3), S('mint', base=.45), smooth=True)
    P.gadd(at(torus(3.8, .22, n=28, sides=5, y=.45), (0, 0, 0)), 'cash')
    for k, (x, z, n) in enumerate(((-.9, -.5, 4), (.8, .3, 6), (0, 1.1, 3))):
        for j in range(n): P.add(cyl(.7, .2, sides=10, y0=.55 + j * .22), S('lemon', base=.55 + (j % 2) * .12, jit=0), smooth=True)
    return P

def buy_button(seed=1):
    """button on a squat base with a price board on a post behind it (board faces -Z)"""
    P = Prop('BuyButton')
    P.add(cyl(2.6, 1.2, sides=16, y0=-.3), S('metal', base=.45), smooth=True)
    P.add(cyl(2.9, .4, sides=16, y0=.8), S('cream', base=.75), smooth=True)
    P.gadd(at(cyl(2.0, .55, sides=16, y0=1.1), (0, 0, 0)), 'button')
    for sx in (-1, 1): P.add(at(box((.35, 6.0, .35)), (sx * 2.4, 2.7, 3.2)), S('metal', base=.4))
    P.add(at(box((6.0, 3.0, .45), .15), (0, 5.2, 3.2)), S('choc', base=.4))
    P.add(at(box((6.4, .45, .6), .1), (0, 6.75, 3.2)), S('lemon', base=.6))
    P.add(at(cyl(.85, .15, sides=14), (-1.6, 5.2, 2.92), (90, 0, 0)), S('lemon', base=.7, jit=0))      # coin icon
    P.add(at(cyl(.5, .2, sides=10), (-1.6, 5.2, 2.85), (90, 0, 0)), S('lemon', base=.45, jit=0))
    for k, w in enumerate((2.4, 1.6)): P.add(at(box((w, .38, .1)), (-.35 + w / 2, 5.55 - k * .7, 2.92)), S('mint', base=.75, jit=0))
    P.add(at(torus(2.95, .2, n=24, sides=5, y=1.2), (0, 0, 0)), S('pink', base=.6))
    for k in range(3):                                                       # floor chevrons pointing at the button
        P.add(at(ngon_prism([(-1.0, -.9), (0, .3), (1.0, -.9), (1.0, -.3), (0, .9), (-1.0, -.3)], -.02, .06), (0, 0, -4.4 - k * 1.7), (0, 180, 0)),
              S('lemon', base=.62, jit=0))
    return P

def slot_marker(w=12.0, d=8.0):
    """empty build slot: four lemon corner brackets + a dashed outline, flush on the slab"""
    P = Prop('Slot%dx%d' % (w, d)); t, h = .7, .12
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.add(at(box((2.6, h, t)), (sx * (w / 2 - 1.3), .06, sz * d / 2)), S('lemon', base=.62, jit=0))
            P.add(at(box((t, h, 2.6)), (sx * w / 2, .06, sz * (d / 2 - 1.3))), S('lemon', base=.62, jit=0))
    for k in range(int(w / 3) - 1):
        x = -w / 2 + 3 * (k + 1)
        if abs(abs(x) - w / 2) > 2.2:
            for sz in (-1, 1): P.add(at(box((1.4, h, .4)), (x, .06, sz * d / 2)), S('cream', base=.7, jit=0))
    return P

# ------------------------------------------------------------------ town dressing
def lollipop_tree(seed=1, h=14.0):
    rng = random.Random(seed); P = Prop('Lolly%d' % seed)
    c1, c2 = [('pink', 'cream'), ('mint', 'cream'), ('grape', 'lemon'), ('red', 'cream')][seed % 4]
    P.add(cyl(.45, h, sides=8, y0=-.4), S('cream', base=.75), smooth=True)
    R = h * .32; cy = h + R * .55; th = 1.6; yaw = rng.uniform(0, 360)
    for k in range(12):                                                      # swirl disc = wedges, each one colour
        a0, a1 = k * math.tau / 12, (k + 1) * math.tau / 12
        poly = [(0, 0)] + [(math.cos(a0 + (a1 - a0) * t / 3) * R, math.sin(a0 + (a1 - a0) * t / 3) * R) for t in range(4)]
        P.add(at(ngon_prism(poly, -th / 2, th / 2), (0, cy, 0), (90, yaw, 0)), S(c1 if k % 2 else c2, base=.6, up=.15, jit=.02))
    P.add(at(torus(R, .35, n=24, sides=5), (0, cy, 0), (90, yaw, 0)), S(c1, base=.45))
    P.add(at(blob(.9, seed, n=12, sq=.8), (0, cy - R - .2, 0)), S('cream', base=.7))              # stick socket
    P.add(at(dome(2.2, .9, n=14, rings=3), (0, -.3, 0)), S('cream', grad=(-.3, .6, .6, .9)), smooth=True)   # sugar mound
    for k in range(3):
        a = yaw * .02 + k * math.tau / 3
        P.add(at(dome(.55, .6, n=8, rings=2), (math.cos(a) * 1.9, -.1, math.sin(a) * 1.9)), S([c1, 'lemon', 'mint'][k], base=.62), smooth=True)
    return P

def gumdrop_bush(seed=1):
    rng = random.Random(seed); P = Prop('Gumdrop%d' % seed)
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(1.6, 2.6); r = rng.uniform(1.2, 1.9) * (1.2 if k == 0 else 1)
        col = ['mint', 'grape', 'pink', 'lemon'][(seed + k) % 4]
        x, z = math.cos(a) * d, math.sin(a) * d
        P.add(at(cyl(r, r * .7, sides=12, r2=r * .82, y0=-.3), (x, 0, z)), S(col, base=.5, up=.25), smooth=True)
        P.add(at(dome(r * .82, r * .9, n=12, rings=4), (x, r * .7 - .3, z)), S(col, grad=(r * .4, r * 1.6, .55, .9)), smooth=True)
    return P

def candy_lamp(seed=1, h=13.0):
    """candy-cane street lamp: striped post, hook over -Z, hanging lantern"""
    P = Prop('CandyLamp')
    P.add(at(cyl(1.0, .8, sides=8, y0=-.3), (0, 0, 0)), S('metal', base=.35))
    hook = [Vector((0, .5, 0)), Vector((0, h, 0))] + [Vector((0, h + math.sin(a) * 1.8, -1.8 + math.cos(a) * 1.8))
                                                       for a in [math.pi * k / 6 for k in range(1, 7)]]
    stripes(P, subdiv_line(hook[:2], 1.3) + hook[2:], .42, ['red', 'cream'])
    lz = -3.6
    P.add(at(box((.12, 1.2, .12)), (0, h - .8, lz)), S('metal', base=.3))
    P.add(at(spike(1.0, .7, sides=6, shoulder=.2), (0, h - 1.6, lz)), S('choc', base=.35))
    P.gadd(at(cyl(.7, 1.4, sides=6, y0=h - 3.0), (0, 0, lz)), 'lamp')
    P.add(at(cyl(.85, .3, sides=6, y0=h - 3.2), (0, 0, lz)), S('choc', base=.35))
    return P

def choc_bench(seed=1):
    """chocolate-bar bench: segmented seat + back, steel legs; sit side = -Z"""
    P = Prop('ChocBench')
    for k in range(4):
        P.add(at(box((1.45, .55, 2.0), .18), (-2.25 + k * 1.5, 1.85, 0)), S('choc', base=.5, up=.3, jit=.02))
        P.add(at(box((1.45, 1.6, .5), .18), (-2.25 + k * 1.5, 3.2, .95), (-10, 0, 0)), S('choc', base=.5, up=.3, jit=.02))
    for sx in (-1, 1):
        P.add(at(box((.35, 1.9, 1.9), .05), (sx * 2.6, .7, 0)), S('metal', base=.4))
        P.add(at(box((.3, 2.6, .3)), (sx * 2.6, 2.6, 1.1), (-10, 0, 0)), S('metal', base=.4))
    return P

def candy_crate(seed=1, s=2.6):
    P = Prop('CandyCrate%d' % seed); col = ['pink', 'mint', 'grape'][seed % 3]
    P.add(at(box((s, s, s), .12), (0, s / 2 - .1, 0)), S('cream', base=.6, up=.2))
    for y in (.35, s - .55): P.add(at(box((s + .1, .35, s + .1), .06), (0, y, 0)), S(col, base=.55))
    P.add(at(box((s * .3, s + .05, s + .1)), (0, s / 2 - .1, 0)), S(col, base=.5))
    return P

def spawn_pad():
    P = Prop('SpawnPad')
    P.add(cyl(9.0, .8, sides=28, y0=-.6), S('cream', base=.75), smooth=True)
    P.add(cyl(7.6, .3, sides=28, y0=.15), S('pink', base=.5), smooth=True)
    star = [(math.cos(a) * (5.4 if i % 2 == 0 else 2.4), math.sin(a) * (5.4 if i % 2 == 0 else 2.4))
            for i, a in enumerate([k * math.tau / 10 - math.pi / 2 for k in range(10)])]
    P.add(ngon_prism(star, .4, .55), S('lemon', base=.7, jit=0))
    P.gadd(at(torus(8.3, .3, n=36, sides=5, y=.25), (0, 0, 0)), 'ring')
    return P

def exchange():
    """HERO: the Candy Exchange - drum hall with pilasters and an arched entrance (-Z), mint dome with lemon ribs,
    gumball crown, glowing halo ring, four lollipop finials. ~56 across, ~70 tall"""
    P = Prop('Exchange'); R = 24.0
    P.add(cyl(R + 5, 1.6, sides=32, y0=-1.0), S('conc', base=.55), smooth=True)                # plinth + steps at the door
    for k in range(3): P.add(at(box((22 - k * 2, .9, 3.0), .1), (0, -.4 + k * .8, -(R + 5.5) + k * 1.4)), S('conc', base=.6 + k * .04))
    door_hw, spring = 6.0, 10.0
    wall = G.bool_diff(cyl(R, 22.0, sides=32, y0=.6), cyl(R - 1.4, 24.0, sides=32, y0=-.5))   # hollow drum: a door cut shows the tunnel
    cut = G.arch_prism(door_hw, spring, -R - 4, -R + 4, y0=-2)
    P.add(G.bool_diff(wall, cut), S('cream', grad=(0, 22, .5, .72)), smooth=True)
    P.add(at(G.arch_frame(door_hw, spring, 1.4, -R - 1.2, -R + 1.0), (0, .6, 0)), S('pink', base=.6))
    P.add(at(G.arch_tunnel(door_hw, spring, -R + .9, -R + 6), (0, .6, 0)), S('choc', base=.12, jit=0))
    P.add(at(G.arch_cap(door_hw, spring, -R + 6), (0, .6, 0)), S('choc', base=.1, jit=0))
    P.gadd(at(G.arch_cap(door_hw - .6, spring, -R + 5.8), (0, .6, 0)), 'lamp')
    for k in range(9):                                                       # scalloped striped awning over the door
        x = -7.2 + k * 1.8
        P.add(at(box((1.8, .3, 4.2), .05), (x, 18.2, -R - 1.6), (-24, 0, 0)), S('pink' if k % 2 else 'cream', base=.62, jit=0))
        P.add(at(cyl(.9, .3, sides=10), (x, 16.95, -R - 3.45), (90, 0, 0)), S('pink' if k % 2 else 'cream', base=.6, jit=0), smooth=True)
    P.add(at(cyl(2.1, .6, sides=24), (0, 20.4, -R - .9), (90, 0, 0)), S('lemon', base=.62), smooth=True)      # coin emblem
    P.add(at(torus(1.6, .25, n=22, sides=5), (0, 20.4, -R - 1.3), (90, 0, 0)), S('lemon', base=.35))
    P.add(at(box((.5, 1.7, .3)), (0, 20.4, -R - 1.35)), S('lemon', base=.35))
    for k in range(16):                                                      # pilasters (skip the door)
        a = k * math.tau / 16
        if abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .45: continue
        P.add(at(box((2.4, 22, 1.6), .2), (math.cos(a) * (R + .4), 11.6, math.sin(a) * (R + .4)), (0, -math.degrees(a) + 90, 0)), S('pink', base=.55, up=.2))
    for y in (8.5, 22.4):                                                    # trim bands, cut where they cross the door
        band = G.bool_diff(cyl(R + 1.4, 1.2 if y > 20 else .7, sides=32, y0=y), cyl(R - .2, 3, sides=32, y0=y - 1))
        if y < spring + door_hw + 1: band = G.bool_diff(band, G.arch_prism(door_hw + 1.4, spring, -R - 4, -R + 4, y0=-2))
        P.add(band, S('lemon', base=.6), smooth=True)
    for k in range(10):                                                      # round windows up high
        a = k * math.tau / 10 + .31
        if abs(math.atan2(math.sin(a), math.cos(a)) + math.pi / 2) < .4: continue
        P.gadd(at(cyl(1.6, .4, sides=12), (math.cos(a) * (R + .15), 16, math.sin(a) * (R + .15)), (90, -math.degrees(a) - 90, 0)), 'lamp')
        P.add(at(torus(1.75, .35, n=14, sides=5), (math.cos(a) * (R + .4), 16, math.sin(a) * (R + .4)), (90, -math.degrees(a) - 90, 0)), S('cream', base=.75))
    P.add(at(dome(R + .5, 19, n=32, rings=8), (0, 23.4, 0)), S('mint', grad=(23, 42, .45, .82)), smooth=True)
    for k in range(12):                                                      # ribs
        a = k * math.tau / 12
        rib = [Vector((math.cos(a) * (R + .9) * math.cos(b), 23.4 + 19.4 * math.sin(b), math.sin(a) * (R + .9) * math.cos(b)))
               for b in [j / 8 * math.pi / 2 * .93 for j in range(9)]]
        P.add(tube(rib, .55, sides=5), S('lemon', base=.6))
    P.add(cyl(5.0, 3.0, sides=16, y0=41.0), S('pink', base=.55), smooth=True)                  # gumball crown
    P.add(at(sphere(8.0, 28, 16), (0, 51.5, 0)), S('cream', grad=(44, 59, .55, .9), up=.1), smooth=True)
    rng = random.Random(4)
    for k in range(34):                                                      # gumballs half-sunk in the crown
        u, v = rng.uniform(0, math.tau), rng.uniform(-.25, 1.1)
        p = Vector((math.cos(u) * math.cos(v) * 7.6, 51.5 + math.sin(v) * 7.6, math.sin(u) * math.cos(v) * 7.6))
        P.add(at(sphere(1.35, 10, 7), p), S(['pink', 'mint', 'lemon', 'grape', 'red'][k % 5], base=.62, up=.2, jit=0), smooth=True)
    P.add(cyl(2.4, 2.2, sides=12, y0=59.0), S('pink', base=.55), smooth=True)
    P.gadd(at(torus(13.5, .6, n=40, sides=6), (0, 47, 0), (0, 0, 10)), 'ring')
    for k in range(4):                                                       # lollipop finials on the drum
        a = k * math.tau / 4 + math.tau / 8; x, z = math.cos(a) * (R - 1), math.sin(a) * (R - 1)
        stripes(P, subdiv_line([Vector((x, 23, z)), Vector((x, 33, z))], 1.4), .5, ['pink', 'cream'], sides=6)
        P.add(at(cyl(3.0, 1.0, sides=16), (x, 35.5, z), (90, -math.degrees(a), 0)), S(['grape', 'lemon', 'pink', 'mint'][k], base=.6), smooth=True)
        P.add(at(torus(1.8, .35, n=16, sides=5), (x, 35.5, z), (90, -math.degrees(a), 0)), S('cream', base=.8))
    return P

def rock_cliff(seed, r=14.0):
    P = Prop('Cliff%d' % seed)
    P.add(hull(rock_pts((r, r * 2.2, r * .9), n=26, seed=seed, flat=.0)), S('cliff', grad=(-r * 2.2, r * 1.6, .25, .7), up=.12, top='lawn', thr=.6, topbase=.6, seed=seed))
    return P


def coin_chute():
    """pipe from the collector's side (origin) down to the cash pad 18 studs along -Z, on two posts"""
    P = Prop('CoinChute')
    pts = [Vector((0, 6.0, -5.6)), Vector((0, 7.2, -8.5)), Vector((0, 6.2, -13.0)), Vector((0, 4.4, -16.6)), Vector((0, 3.2, -17.6))]   # starts at the vat rim, mouth clears the coins
    P.add(tube(pts, .75, sides=10), S('metal', base=.6, up=.2), smooth=True)
    for t in (pts[0], pts[2]): P.add(at(torus(.95, .22, n=12, sides=5), t, (90, 0, 0)), S('lemon', base=.6))
    for z in (-8.5, -13.0): P.add(at(box((.45, 6.0, .45)), (0, 2.8, z)), S('metal', base=.35))
    P.add(at(cyl(1.0, .6, sides=10, y0=2.5), (0, 0, -17.8)), S('metal', base=.4))
    return P

def hazard(L=36.0):
    """flat lemon/choc hazard stripe band along X, flush on the slab"""
    P = Prop('Hazard%d' % L); n = int(L / 1.2)
    for k in range(n):
        P.add(at(box((1.2, .08, 1.0)), (-L / 2 + .6 + k * 1.2, .04, 0)), S('lemon' if k % 2 else 'choc', base=.62 if k % 2 else .5, jit=0))
    return P

def walkway(L=18.0, w=6.0):
    """painted mint walkway along Z, cream edge dashes (lifted .02 off the slab: no coplanar bottom)"""
    P = Prop('Walk%dx%d' % (L, w))
    P.add(at(box((w, .08, L)), (0, .06, 0)), S('mint', base=.7, up=0, jit=0))
    for k in range(int(L / 3)):
        for sx in (-1, 1): P.add(at(box((.4, .1, 1.6)), (sx * (w / 2 + .5), .07, -L / 2 + 1.5 + k * 3)), S('cream', base=.85, jit=0))
    return P

def candy_sacks(seed=1):
    """pallet with tied sugar sacks"""
    P = Prop('Sacks%d' % seed)
    for k in range(3): P.add(at(box((5.0, .35, 1.2), .05), (0, .3, -1.6 + k * 1.6)), S('choc', base=.6, jit=.03, seed=k))
    for sx in (-1, 1): P.add(at(box((.4, .5, 4.4)), (sx * 2.0, .0, 0)), S('choc', base=.45))
    for k, (x, z, y) in enumerate(((-1.2, -.9, .5), (1.2, -.8, .5), (-1.1, 1.0, .5), (1.2, 1.0, .5), (0, 0, 2.1))):
        P.add(at(blob(1.25, seed * 7 + k, n=18, sq=.85), (x, y + 1.1, z), s=(1, 1.1, 1)), S('cream', base=.68, up=.2, jit=.03), smooth=True)
        P.add(at(cyl(.38, .5, sides=8, y0=y + 2.2), (x, 0, z)), S('pink', base=.55))
    return P

def choc_fountain():
    """three-tier chocolate fountain: pink bowls, chocolate pouring between them, pool"""
    P = Prop('ChocFountain')
    P.add(cyl(7.0, 1.4, sides=24, y0=-.4), S('cream', base=.72), smooth=True)
    P.add(cyl(6.2, .3, sides=24, y0=.8), S('choc', base=.55, up=.25, jit=0), smooth=True)
    P.add(cyl(1.0, 9.0, sides=10, y0=.8), S('cream', base=.62), smooth=True)
    for y, r in ((4.4, 4.2), (7.4, 2.8), (9.6, 1.6)):
        P.add(at(cyl(r, .7, sides=20, r2=r * .7), (0, y, 0), (180, 0, 0)), S('pink', base=.58), smooth=True)
        P.add(cyl(r * .92, .25, sides=20, y0=y - .2), S('choc', base=.55, up=.25, jit=0), smooth=True)
        P.add(at(torus(r, .22, n=20, sides=5, y=y), (0, 0, 0)), S('cream', base=.85))
        for k in range(8):                                                   # chocolate curtain
            a = k * math.tau / 8 + y
            P.add(tube([Vector((math.cos(a) * r, y, math.sin(a) * r)), Vector((math.cos(a) * (r + .35), y - 1.2, math.sin(a) * (r + .35))),
                        Vector((math.cos(a) * (r + .45), max(.9, y - 3.0), math.sin(a) * (r + .45)))], [.35, .3, .26], sides=6),
                  S('choc', base=.55, up=.2, jit=0), smooth=True)
    P.add(at(sphere(.9, 10, 7), (0, 10.6, 0)), S('red', base=.6), smooth=True)
    return P

def candy_corn(seed=1):
    rng = random.Random(seed); P = Prop('CandyCorn%d' % seed)
    for k in range(rng.randint(3, 5)):
        x, z = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6); h = rng.uniform(1.6, 2.6); r = h * .42; tilt = rng.uniform(-14, 14)
        yaw = rng.uniform(0, 60)
        for col, b, f0, f1 in (('lemon', .6, 0, .4), ('orange', .62, .4, .78), ('cream', .85, .78, 1)):
            P.add(at(cyl(r * (1 - f0), h * (f1 - f0), sides=6, r2=r * (1 - f1) + .02, y0=h * f0 - .2), (x, 0, z), (tilt, yaw, 0)),
                  S(col, base=b, jit=0))
    return P

def peppermint(seed=1, r=2.2):
    """flat peppermint swirl stepping disc"""
    P = Prop('Peppermint')
    for k in range(10):
        a0, a1 = k * math.tau / 10, (k + 1) * math.tau / 10
        poly = [(0, 0)] + [(math.cos(a0 + (a1 - a0) * t / 3) * r, math.sin(a0 + (a1 - a0) * t / 3) * r) for t in range(4)]
        P.add(ngon_prism(poly, -.2, .3), S('red' if k % 2 else 'cream', base=.62 if k % 2 else .85, up=.1, jit=0))
    return P

def wrapper_bin():
    P = Prop('WrapperBin')
    P.add(cyl(1.0, 2.6, sides=10, y0=-.2), S('mint', base=.55, up=.2), smooth=True)
    for y in (.6, 1.9): P.add(cyl(1.08, .25, sides=10, y0=y), S('cream', base=.8, jit=0), smooth=True)
    P.add(at(dome(1.1, .7, n=10, rings=2), (0, 2.4, 0)), S('pink', base=.6), smooth=True)
    return P
