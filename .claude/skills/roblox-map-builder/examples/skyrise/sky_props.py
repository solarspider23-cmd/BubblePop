# Skyrise Simulator prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Machinery (Prop, S, blob, at, materials, to_kit, bool_diff) from the skill's grove module; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector
import forest_props as G
from pro_lib import Palette, box, cyl, spike, tube, hull, ngon_prism, rock_pts, nz

G.PAL = Palette({
    'grass':  ('#2f8f3a', '#5fd04a', '#c4f77a'),
    'dirt':   ('#6a3f24', '#a8703f', '#e3ad74'),
    'rock':   ('#4a4258', '#8c80a0', '#d2c8e0'),     # island undersides: dusty lavender stone strata
    'stone':  ('#6f7590', '#b9bfd6', '#f2f4fb'),     # paving, pedestals
    'sand':   ('#c07a2c', '#f2bf62', '#ffeab0'),
    'snow':   ('#8fa8cc', '#e2eeff', '#ffffff'),
    'ice':    ('#1f6fa8', '#4fc6ee', '#c4f6ff'),
    'basalt': ('#2a2534', '#4c4560', '#8e84a6'),
    'wood':   ('#4f2c14', '#93582c', '#d6995c'),
    'leaf':   ('#17703f', '#38bd5c', '#a6f27a'),
    'gold':   ('#9a5600', '#ffbd1a', '#fff29a'),
    'red':    ('#9e1c38', '#ff475c', '#ffa2ad'),
    'cloud':  ('#a6b6e0', '#eef3ff', '#ffffff'),
    'violet': ('#45259a', '#8a5aff', '#d8c8ff'),
    'pink':   ('#b02a6e', '#ff6aae', '#ffc2de'),
})
G.MATS.clear()
ZONE = {1: '#7dff6a', 2: '#ffcc33', 3: '#5fdcff', 4: '#ff6a2a', 5: '#ffe14a'}
G.GLOW.clear(); G.GLOW.update({'z%d' % k: v for k, v in ZONE.items()})
G.GLOW.update({'lamp': '#ffd27a', 'crystal': '#5fe8ff', 'gem': '#c46aff', 'lava': '#ff6a1a', 'sell': '#3dff8a',
               'pad': '#6ff0ff', 'egg': '#ff9ae0', 'shine': '#fff1a8', 'ice': '#9fefff'})
G.GLOW_E.clear(); G.GLOW_E.update({'lamp': 3.5, 'lava': 3.4, 'crystal': 1.6, 'gem': 1.6, 'sell': 2.2, 'pad': 2.2, 'egg': 1.4,
                                   'shine': 2.6, 'ice': 1.4})
for k in ZONE: G.GLOW_E['z%d' % k] = 2.2
Prop, S, at, blob = G.Prop, G.S, G.at, G.blob

# ------------------------------------------------------------------ helpers
def lathe(profile, n=24, y_off=0.0):
    """revolve [(r, y), ...] (bottom -> top) around Y; caps where r == 0 collapse to a point"""
    bm = bmesh.new(); rings = []
    for r, y in profile:
        if r <= 1e-4: rings.append([bm.verts.new((0, y + y_off, 0))])
        else: rings.append([bm.verts.new((math.cos(a) * r, y + y_off, math.sin(a) * r)) for a in [i * math.tau / n for i in range(n)]])
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1: continue
        if len(A) == 1:
            for i in range(n): bm.faces.new((A[0], B[(i + 1) % n], B[i]))
        elif len(B) == 1:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[0]))
        else:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    if len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return bm

def sphere(r, seg=16, rings=10):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r); return bm

def torus(R, r, n=24, sides=6):
    pts = [Vector((math.cos(a) * R, 0, math.sin(a) * R)) for a in [i * math.tau / n for i in range(n + 1)]]
    return tube(pts, r, sides=sides, cap0=False, cap1=False)

def gem(r, h):
    """faceted octahedron-ish gem standing on its tip"""
    return lathe([(0, 0), (r, h * .55), (r * .62, h), (0, h * 1.02)], n=6)

# ------------------------------------------------------------------ islands (built per island by the map; these are the pieces)
def island_under(seed, R, depth, rim_fn, top_y=0.0, n=40, bands=6):
    """underside of a floating island: rings from the rim inward/down to a tip, strata colour bands, hanging rocks.
    rim_fn(angle) -> rim radius. Origin = island centre at the top surface height."""
    rng = random.Random(seed); P = Prop('IslandUnder%d' % seed)
    bm = bmesh.new(); rings = []
    K = 9
    for k in range(K + 1):
        t = k / K; y = top_y - .6 - depth * t ** 1.15
        rs = (1 - t ** 1.6) * (1 + (.06 if 0 < k < K else 0) * math.sin(seed + k * 1.7))
        if k == K: rings.append([bm.verts.new((rng.uniform(-2, 2), y, rng.uniform(-2, 2)))]); continue
        ring = []
        for i in range(n):
            a = i * math.tau / n; r = rim_fn(a) * rs * (1 + (rng.uniform(-.05, .05) if k else 0))
            ring.append(bm.verts.new((math.cos(a) * r, y + (rng.uniform(-.8, .8) if k else 0), math.sin(a) * r)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(B) == 1:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[0]))
        else:
            for i in range(n): bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:                                                        # outward = away from the axis / down
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, -1.0, c.z))) < 0: f.normal_flip()
    def strata(f):
        c = f.calc_center_median(); band = int((top_y - c.y) / (depth / bands))
        if c.y > top_y - 2.4: col, v = 'dirt', .55
        else: col, v = 'rock', [.38, .55, .46, .62, .42, .5][band % 6]
        u = G.PAL.u(col); vv = max(.05, min(.95, v + f.normal.y * .1 + (rng.random() - .5) * .05))
        return [(u, vv)] * len(f.loops)
    P.solid.add(bm, strata)
    for k in range(int(R * .35)):                                              # hanging rocks under the rim
        a = rng.uniform(0, math.tau); t = rng.uniform(.15, .55)
        r = rim_fn(a) * (1 - t ** 1.6) * .96; y = top_y - .6 - depth * t ** 1.15
        h = rng.uniform(3, 9) * (1.4 - t)
        sp = spike(rng.uniform(1.2, 2.6), h, sides=5, shoulder=.25)
        P.add(at(sp, (math.cos(a) * r, y + .5, math.sin(a) * r), (180 + rng.uniform(-12, 12), rng.uniform(0, 360), 0)),
              S('rock', base=rng.uniform(.35, .55), jit=.04))
    for k in range(4 + int(R * .03)):                                          # glow crystals growing out of the strata
        a = rng.uniform(0, math.tau); t = rng.uniform(.2, .55)
        r = rim_fn(a) * (1 - t ** 1.6) * .97; y = top_y - .6 - depth * t ** 1.15
        out = Vector((math.cos(a), -.35, math.sin(a))).normalized()
        for j in range(3):
            h = rng.uniform(6, 12); tilt = Vector((rng.uniform(-.3, .3), rng.uniform(-.3, .3), rng.uniform(-.3, .3)))
            g = lathe([(0, 0), (1.7, .3 * h), (1.7, .8 * h), (0, h)], n=6)
            dirv = (out + tilt).normalized(); q = Vector((0, 1, 0)).rotation_difference(dirv)
            bmesh.ops.rotate(g, cent=Vector(), matrix=q.to_matrix(), verts=g.verts)
            P.gadd(at(g, (math.cos(a) * r, y, math.sin(a) * r)), 'crystal')
    for k in range(int(R * .2)):                                               # vines over the rim
        a = rng.uniform(0, math.tau); r = rim_fn(a) * 1.0
        p0 = Vector((math.cos(a) * r, top_y - .2, math.sin(a) * r)); out = Vector((math.cos(a), 0, math.sin(a)))
        L = rng.uniform(4, 10); pts = [p0, p0 + out * .7 + Vector((0, -L * .5, 0)), p0 + out * .4 + Vector((0, -L, 0))]
        P.add(tube(pts, [.28, .22, .14], sides=5), S('leaf', base=.45))
        for j in range(3): P.add(at(sphere(.55, 8, 6), pts[0].lerp(pts[2], (j + 1) / 3.6) + out * .5), S('leaf', base=.55), smooth=True)
    for k in range(int(R * .12)):                                              # roots hanging over the edge
        a = rng.uniform(0, math.tau); r = rim_fn(a) * .99
        p0 = Vector((math.cos(a) * r, top_y - 1.0, math.sin(a) * r)); out = Vector((math.cos(a), 0, math.sin(a)))
        L = rng.uniform(5, 11)
        P.add(tube([p0, p0 + out * .8 + Vector((0, -L * .4, 0)), p0 + out * .5 + Vector((0, -L, 0))], [.45, .3, .12], sides=5),
              S('wood', base=.35))
    return P

def floating_rock(seed, r=6.0):
    """small decorative sky rock: grass cap, rock cone, maybe a tiny tree"""
    rng = random.Random(seed); P = Prop('SkyRock%d' % seed)
    P.add(at(hull(rock_pts((r, r * .35, r * .85), n=20, seed=seed, flat=.0)), (0, .2, 0)), S('grass', base=.62, up=.25, jit=.04))
    P.add(at(spike(r * .95, r * 1.9, sides=7, shoulder=.35), (0, 0, 0), (180, rng.uniform(0, 60), 0)),
          S('rock', grad=(-r * 1.9, 0, .32, .62), jit=.04))
    if seed % 2 == 0:
        P.add(cyl(.35, r * .5, sides=6, y0=.2), S('wood', base=.5))
        P.add(at(sphere(r * .32, 12, 8), (0, r * .5 + r * .25, 0)), S('leaf', grad=(r * .4, r * 1.0, .45, .85)), smooth=True)
    return P

def cloud(seed, s=1.0):
    rng = random.Random(seed); P = Prop('Cloud%d' % seed)
    for k in range(rng.randint(5, 8)):
        r = rng.uniform(9, 17) * s
        P.add(at(sphere(r, 10, 6), (rng.uniform(-26, 26) * s, rng.uniform(-2, 5) * s, rng.uniform(-12, 12) * s), s=(1, .5, 1)),
              S('cloud', grad=(-6 * s, 10 * s, .55, .95), up=.1, jit=0), smooth=True)
    return P

# ------------------------------------------------------------------ paths / bridges / gates
def path_stone(seed, r=1.6):
    rng = random.Random(seed); P = Prop('PathStone%d' % seed)
    pts = [(math.cos(a) * r * rng.uniform(.8, 1.1), math.sin(a) * r * rng.uniform(.8, 1.1)) for a in [i * math.tau / 7 for i in range(7)]]
    P.add(ngon_prism(pts, -.3, .22, .12), S('stone', base=.55, up=.2, jit=.05, seed=seed))
    return P

def bridge(L, rise=0.0, w=9.0, kind='wood', seed=1):
    """bridge from z=0 to z=-L, rising by `rise`: planks (wood) or slabs (stone) with posts, rails and rope/arches.
    Origin = start of the deck centre line."""
    rng = random.Random(seed); P = Prop('Bridge_%s_%d_%d' % (kind, round(L), round(rise)))
    n = max(4, int(L / (1.6 if kind == 'wood' else 4.0)))
    pitch = math.degrees(math.atan2(rise, L))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n; z = -L * (t0 + t1) / 2; y = rise * (t0 + t1) / 2
        seg = L / n
        if kind == 'wood':
            P.add(at(box((w + rng.uniform(-.3, .3), .5, seg * .86), .06), (rng.uniform(-.15, .15), y - .25, z), (pitch, rng.uniform(-1.5, 1.5), 0)),
                  S('wood', base=.5 + rng.uniform(-.08, .08), up=.25, jit=0))
        else:
            P.add(at(box((w, .9, seg * .96), .15), (0, y - .45, z), (pitch, 0, 0)), S('stone', base=.55 + (k % 2) * .06, up=.25, jit=0))
    for sx in (-1, 1):                                                          # stringers under the deck
        P.add(tube([Vector((sx * (w / 2 - .6), -.9, 1)), Vector((sx * (w / 2 - .6), rise - .9, -L - 1))], .45, sides=6),
              S('wood' if kind == 'wood' else 'stone', base=.35))
    nposts = max(2, int(L / 10)) + 1
    tops = {-1: [], 1: []}
    for k in range(nposts):
        t = k / (nposts - 1); z = -L * t; y = rise * t
        for sx in (-1, 1):
            x = sx * (w / 2 + .1)
            if kind == 'wood':
                P.add(at(box((.7, 4.4, .7), .1), (x, y + 1.4, z)), S('wood', base=.45))
                P.add(at(spike(.55, .6, sides=4, rot0=45, shoulder=.0), (x, y + 3.6, z)), S('wood', base=.6))
            else:
                P.add(at(box((1.2, 3.6, 1.2), .2), (x, y + 1.3, z)), S('stone', base=.6))
                P.add(at(sphere(.75, 10, 6), (x, y + 3.6, z)), S('gold', base=.6), smooth=True)
            tops[sx].append(Vector((x, y + 3.0, z)))
    for sx in (-1, 1):                                                          # rails: sagging rope (wood) / straight bar (stone)
        T = tops[sx]
        for a, b in zip(T, T[1:]):
            if kind == 'wood':
                mid = a.lerp(b, .5) + Vector((0, -.8, 0))
                P.add(tube([a, mid, b], .18, sides=5), S('dirt', base=.65))
            else:
                P.add(tube([a + Vector((0, .3, 0)), b + Vector((0, .3, 0))], .3, sides=6), S('gold', base=.55))
    return P

def zone_gate(z, w=16.0):
    """zone gate: two banded stone pillars, arched crest with the zone gem, glowing barrier, lock plate + price plate.
    Front (-Z) faces the player arriving from the lower island."""
    P = Prop('ZoneGate%d' % z); hw = w / 2
    for sx in (-1, 1):
        x = sx * (hw + 1.6)
        P.add(at(box((4.2, 1.2, 4.2), .3), (x, .3, 0)), S('stone', base=.5))
        for k in range(5):
            P.add(at(box((3.2 - (k % 2) * .25, 3.0, 3.2 - (k % 2) * .25), .25), (x, 2.4 + k * 3.0, 0)), S('stone', base=.55 + (k % 2) * .08))
        P.add(at(box((4.0, .8, 4.0), .25), (x, 17.4, 0)), S('gold', base=.6))
        P.add(at(gem(1.2, 2.6), (x, 17.8, 0)), S('stone', base=.7))
        P.gadd(at(gem(.9, 2.0), (x, 18.2, 0)), 'z%d' % z)
    arc = [Vector((math.cos(a) * (hw + 1.6), 17.5 + math.sin(a) * 6.5, 0)) for a in [math.pi * i / 12 for i in range(13)]]
    P.add(tube(arc, 1.1, sides=8), S('stone', base=.62), smooth=True)
    P.add(at(cyl(3.0, 1.0, sides=6), (0, 23.6, -.2), (90, 0, 0)), S('gold', base=.6))                 # crest medallion
    P.gadd(at(gem(1.4, 2.8), (0, 22.2, -.9), (90, 0, 0)), 'z%d' % z)
    for k in range(9):                                                                                  # barrier: glowing bars you can see through
        P.gadd(at(box((.32, 15.6, .32)), (-hw + w * (k + .5) / 9, 8.4, .2)), 'z%d' % z)
    for y in (1.0, 15.8): P.gadd(at(box((w + .3, .4, .4)), (0, y, .2)), 'z%d' % z)
    P.add(at(box((7.0, 3.6, .5), .2), (0, 10.5, -.6)), S('basalt', base=.55))                           # price plate
    P.add(at(cyl(1.2, .3, sides=14), (-2.2, 10.5, -.95), (90, 0, 0)), S('gold', base=.7, jit=0))
    for k, wl in enumerate((3.0, 2.0)): P.add(at(box((wl, .45, .2)), (-.6 + wl / 2, 11.0 - k * .9, -.95)), S('gold', base=.75, jit=0))
    P.add(at(box((2.6, 2.2, .5), .25), (0, 5.4, -.6)), S('gold', base=.6))                              # padlock
    P.add(at(torus(.9, .28, n=14, sides=5), (0, 6.6, -.6), (90, 0, 0)), S('gold', base=.45))
    P.add(at(cyl(.3, .4, sides=8), (0, 5.4, -.95), (90, 0, 0)), S('basalt', base=.3, jit=0))
    return P

# ------------------------------------------------------------------ spawn island stations
def egg_shrine():
    """egg hatch station: tiered round podium, giant spotted egg on a cushion, four crystal posts, front steps (-Z)"""
    P = Prop('EggShrine')
    P.add(lathe([(10.5, -.6), (10.5, .6), (9.4, .9), (9.4, 1.8), (7.6, 2.1), (7.6, 3.0), (0, 3.0)], n=32), S('stone', base=.6, up=.2), smooth=False)
    P.add(at(torus(9.5, .35, n=40, sides=5), (0, 1.85, 0)), S('gold', base=.55))
    for k in range(3): P.add(at(box((7 - k, .9, 2.2), .1), (0, .1 + k * .9, -10.2 + k * 1.1)), S('stone', base=.66 + k * .03))
    P.add(lathe([(4.2, 3.0), (4.6, 3.6), (3.8, 4.6), (0, 4.8)], n=24), S('red', base=.55, up=.2), smooth=True)   # cushion
    P.add(lathe([(0, 4.4), (3.2, 5.6), (4.6, 8.0), (4.7, 10.0), (4.2, 12.6), (3.0, 14.8), (1.4, 16.2), (0, 16.6)], n=28),
          S('cloud', grad=(4, 16.6, .62, .95), up=.1), smooth=True)
    rng = random.Random(3)
    for k in range(9):                                                                                  # egg spots
        a = rng.uniform(0, math.tau); y = rng.uniform(6.5, 13.5)
        prof_r = {6.5: 4.5, 8: 4.6, 10: 4.7, 12.6: 4.2, 14: 3.5}
        rr = min(prof_r.items(), key=lambda kv: abs(kv[0] - y))[1]
        P.add(at(cyl(rng.uniform(.8, 1.3), .5, sides=10), (math.cos(a) * (rr - .1), y, math.sin(a) * (rr - .1)), (90, -math.degrees(a) - 90, 0)),
              S(['pink', 'violet', 'gold'][k % 3], base=.6, jit=0), smooth=True)
    for k in range(4):                                                                                  # crystal posts
        a = math.tau * k / 4 + math.pi / 4; x, z = math.cos(a) * 8.4, math.sin(a) * 8.4
        P.add(at(cyl(.8, 4.5, sides=6, y0=0), (x, 1.8, z)), S('stone', base=.55))
        P.gadd(at(gem(.9, 3.0), (x, 6.3, z)), 'egg')
    P.gadd(at(torus(5.6, .25, n=36, sides=5), (0, 9.5, 0), (14, 0, 6)), 'shine')
    return P

def sell_pad():
    """sell station: glowing pad with a giant coin on a stand behind it (front -Z)"""
    P = Prop('SellPad')
    P.add(cyl(6.0, .8, sides=28, y0=-.5), S('stone', base=.65), smooth=True)
    P.gadd(at(cyl(4.8, .25, sides=28, y0=.3), (0, 0, 0)), 'sell')
    P.add(at(torus(5.4, .3, n=36, sides=5), (0, .4, 0)), S('gold', base=.55))
    P.add(at(box((1.2, 9, 1.2), .2), (0, 4.4, 6.6)), S('wood', base=.45))
    P.add(at(cyl(4.2, 1.0, sides=28), (0, 11.5, 6.6), (90, 0, 0)), S('gold', base=.6, up=.2), smooth=True)
    P.add(at(torus(3.4, .35, n=28, sides=5), (0, 11.5, 6.0), (90, 0, 0)), S('gold', base=.38))
    P.add(at(box((.8, 4.0, .4)), (0, 11.5, 6.0)), S('gold', base=.38))
    for k in range(6):                                                                                  # coin stacks
        a = k * math.tau / 6; x, z = math.cos(a) * 3.0, math.sin(a) * 3.0
        for j in range(2 + k % 3):
            P.add(at(cyl(.8, .3, sides=12), (x, .45 + j * .32, z)), S('gold', base=.55 + (j % 2) * .12, jit=0), smooth=True)
    return P

def upgrade_stand():
    """upgrade booth: counter, striped awning, posts, big glowing up-arrow sign (front -Z)"""
    P = Prop('UpgradeStand'); w, d = 12.0, 6.0
    P.add(at(box((w, 1.0, d + 2), .2), (0, -.1, 0)), S('stone', base=.6))
    P.add(at(box((w - 1, 3.4, 2.2), .2), (0, 2.1, -d / 2 + 1.2)), S('wood', base=.55, up=.2))
    P.add(at(box((w - .6, .5, 2.8), .15), (0, 4.0, -d / 2 + 1.2)), S('gold', base=.6))
    for sx in (-1, 1):
        for sz in (-1, 1): P.add(at(box((.7, 8.6, .7), .1), (sx * (w / 2 - .5), 4.3, sz * (d / 2 - .3))), S('wood', base=.45))
    for k in range(8):
        P.add(at(box(((w + 1) / 8, .35, d + 2.2), .05), (-(w + 1) / 2 + (w + 1) / 16 * (2 * k + 1), 9.0, -.4), (-10, 0, 0)),
              S('violet' if k % 2 else 'cloud', base=.6, jit=0))
    P.add(at(box((w - 1, 4.0, .4), .2), (0, 6.6, d / 2 - .3)), S('basalt', base=.55))
    arrow = [(-1.2, -1.6), (1.2, -1.6), (1.2, .2), (2.4, .2), (0, 2.4), (-2.4, .2), (-1.2, .2)]
    P.gadd(at(ngon_prism(arrow, -.2, .2), (0, 6.6, d / 2 - .55), (-90, 0, 0)), 'z5')
    for k in range(3): P.add(at(gem(.6, 1.4), (-3 + k * 3, 4.25, -d / 2 + 1.2)), S('violet', base=.6), smooth=False)
    return P

def teleport_pad(key='pad'):
    P = Prop('Teleport_%s' % key)
    P.add(cyl(5.2, 1.0, sides=6, y0=-.6), S('stone', base=.6))
    P.add(cyl(4.4, .25, sides=6, y0=.4), S('basalt', base=.5, jit=0))
    P.gadd(at(torus(3.3, .22, n=6, sides=4), (0, .7, 0)), key)
    P.gadd(at(cyl(1.6, .15, sides=6, y0=.6), (0, 0, 0)), key)
    for k in range(3):
        a = k * math.tau / 3 + math.pi / 6; x, z = math.cos(a) * 4.4, math.sin(a) * 4.4
        P.add(at(cyl(.55, 3.4, sides=6, y0=.4), (x, 0, z)), S('stone', base=.55))
        P.gadd(at(gem(.6, 1.6), (x, 4.2, z)), key)
    return P

def leaderboard():
    P = Prop('Leaderboard')
    for sx in (-1, 1): P.add(at(box((1.4, 18, 1.4), .2), (sx * 7.4, 8.6, 0)), S('stone', base=.55))
    P.add(at(box((14.4, 11, 1.0), .3), (0, 11.5, 0)), S('basalt', base=.5))
    P.add(at(box((15.6, 1.0, 1.6), .2), (0, 17.4, 0)), S('gold', base=.6))
    P.add(at(box((15.6, .8, 1.6), .2), (0, 5.8, 0)), S('gold', base=.55))
    for k in range(5): P.add(at(box((11 - k * 1.2, .9, .2)), (-.4 - k * .6 + (11 - k * 1.2) / 2 - 5.5, 15.2 - k * 1.8, -.55)),
                             S(['gold', 'stone', 'dirt', 'violet', 'violet'][k], base=.7, jit=0))
    crown = [(-2.4, 0), (2.4, 0), (2.4, 1.2), (1.6, 2.6), (.8, 1.4), (0, 2.9), (-.8, 1.4), (-1.6, 2.6), (-2.4, 1.2)]
    P.add(at(ngon_prism(crown, -.4, .4), (0, 18.0, 0), (90, 0, 0)), S('gold', base=.65))
    return P

def lamp_post(seed=1):
    P = Prop('SkyLamp')
    P.add(cyl(.9, .8, sides=8, y0=-.4), S('stone', base=.5))
    P.add(cyl(.35, 9.0, sides=8, y0=.3), S('wood', base=.45))
    P.add(tube([Vector((0, 9.0, 0)), Vector((0, 10.0, -.6)), Vector((0, 9.8, -2.0))], .25, sides=6), S('wood', base=.45))
    P.add(at(cyl(.75, .4, sides=8), (0, 9.2, -2.0)), S('gold', base=.55))
    P.gadd(at(sphere(.9, 10, 7), (0, 8.4, -2.0)), 'lamp')
    return P

def puffy_tree(seed, h=13.0, col='leaf'):
    """simulator puffy tree: curved trunk + 3-6 smooth round canopy balls"""
    rng = random.Random(seed); P = Prop('Puffy%d_%s' % (seed, col))
    bend = Vector((rng.uniform(-1, 1), 0, rng.uniform(-1, 1))) * h * .08
    pts = [Vector((0, -.5, 0)) + bend * t * t + Vector((0, h * .62 * t, 0)) for t in [i / 4 for i in range(5)]]
    P.add(tube(pts, [h * .07, h * .06, h * .05, h * .042, h * .035], sides=8), S('wood', grad=(0, h * .6, .3, .6)), smooth=True)
    top = pts[-1]; R = h * .3
    balls = [(top + Vector((0, R * .55, 0)), R)]
    for k in range(rng.randint(3, 5)):
        a = k * math.tau / 4 + rng.uniform(-.4, .4)
        balls.append((top + Vector((math.cos(a) * R * .7, rng.uniform(-.1, .35) * R, math.sin(a) * R * .7)), R * rng.uniform(.6, .78)))
    for c, r in balls: P.add(at(sphere(r, 16, 10), c), S(col, grad=(top.y - R * .6, top.y + R * 1.5, .3, .9), up=.1), smooth=True)
    return P

def flower_bed(seed, r=3.0):
    rng = random.Random(seed); P = Prop('FlowerBed%d' % seed)
    P.add(at(torus(r, .45, n=18, sides=6), (0, .3, 0)), S('stone', base=.6))
    P.add(cyl(r - .2, .5, sides=18, y0=-.3), S('dirt', base=.45, jit=0))
    for k in range(int(r * 5)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, r - .8); x, z = math.cos(a) * d, math.sin(a) * d; h = rng.uniform(.8, 1.5)
        P.add(at(cyl(.08, h, sides=4), (x, .2, z)), S('leaf', base=.5))
        P.add(at(sphere(.38, 8, 6), (x, .2 + h, z)), S(['pink', 'gold', 'violet', 'red', 'cloud'][k % 5], base=.62, jit=0), smooth=True)
    return P

# ------------------------------------------------------------------ resource nodes (the things players break)
def coin_pile(seed, s=1.0):
    rng = random.Random(seed); P = Prop('CoinPile%d' % seed)
    P.add(at(sphere(2.6 * s, 14, 8), (0, -.4, 0), s=(1, .55, 1)), S('gold', grad=(-.4, 1.2 * s, .6, .92)), smooth=True)
    for k in range(5):
        a = k * math.tau / 5 + .3; d = rng.uniform(.6, 1.6) * s
        P.add(at(cyl(.7 * s, .22 * s, sides=14), (math.cos(a) * d, .9 * s, math.sin(a) * d), (78, math.degrees(a), 0)),
              S('gold', base=.78, jit=0), smooth=True)
    for k in range(18):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.6) * s
        y = max(0, (1 - (d / (2.6 * s)) ** 2) * 1.1 * s) - .1
        P.add(at(cyl(.62 * s, .2 * s, sides=12), (math.cos(a) * d, y, math.sin(a) * d), (rng.uniform(-35, 35), 0, rng.uniform(-35, 35))),
              S('gold', base=.72 + rng.uniform(-.08, .1), jit=0), smooth=True)
    P.gadd(at(gem(.35 * s, .9 * s), (rng.uniform(-.6, .6), 1.0 * s, rng.uniform(-.6, .6))), 'shine')
    return P

def chest(seed=1, s=1.0):
    """treasure chest, lid open (back +Z hinge), coins + a gem inside"""
    P = Prop('Chest%d' % seed); w, d, h = 4.6 * s, 3.0 * s, 2.4 * s
    P.add(at(box((w, h, d), .12 * s), (0, h / 2 - .1, 0)), S('wood', base=.5, up=.2))
    for x in (-w / 2 + .5 * s, w / 2 - .5 * s): P.add(at(box((.45 * s, h + .1, d + .1)), (x, h / 2 - .1, 0)), S('gold', base=.55))
    P.add(at(box((w + .1, .35 * s, d + .1)), (0, h - .25 * s, 0)), S('gold', base=.6))
    lid = box((w, .8 * s, d), .15 * s); P.add(at(lid, (0, h + d / 2 * .64, d / 2 + .2 * s), (-62, 0, 0)), S('wood', base=.6))
    P.add(at(sphere(1.4 * s, 12, 7), (0, h - .2 * s, 0), s=(1.4, .45, .9)), S('gold', base=.65), smooth=True)
    P.gadd(at(gem(.5 * s, 1.2 * s), (.6 * s, h + .1, -.2 * s)), 'gem')
    P.add(at(box((.9 * s, 1.0 * s, .25 * s)), (0, h * .62, -d / 2 - .1)), S('gold', base=.45))
    return P

def crystal_node(seed, key='crystal', col='ice', s=1.0):
    rng = random.Random(seed); P = Prop('Crystal%d_%s' % (seed, key))
    P.add(at(hull(rock_pts((2.6 * s, 1.1 * s, 2.2 * s), n=16, seed=seed)), (0, .2, 0)), S('rock', base=.45, up=.2))
    for k in range(rng.randint(4, 6)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 1.4) * s; h = rng.uniform(2.4, 5.2) * s * (1.3 if k == 0 else 1)
        rot = (rng.uniform(-24, 24), rng.uniform(0, 60), rng.uniform(-24, 24)) if k else (0, 0, 0)
        g = lathe([(0, 0), (.62 * s, .3 * h), (.62 * s, .8 * h), (0, h)], n=6)
        if k % 2: P.add(at(g, (math.cos(a) * d, .6, math.sin(a) * d), rot), S(col, grad=(0, h, .45, .9)))
        else: P.gadd(at(g, (math.cos(a) * d, .6, math.sin(a) * d), rot), key)
    return P

# ------------------------------------------------------------------ biome dressing
def cactus(seed, h=7.0):
    rng = random.Random(seed); P = Prop('Cactus%d' % seed)
    sh = S('leaf', grad=(0, h, .35, .7), up=.15)
    P.add(lathe([(.9, -.4), (1.0, h * .9), (.6, h), (0, h + .25)], n=10), sh, smooth=True)
    for sx in (-1, 1):
        if rng.random() < .8:
            y0 = h * rng.uniform(.35, .55); L = rng.uniform(1.6, 2.4); up = rng.uniform(1.6, 3.0)
            pts = [Vector((0, y0, 0)), Vector((sx * L, y0 + .2, 0)), Vector((sx * L, y0 + up, 0))]
            P.add(tube(pts, .62, sides=8), sh, smooth=True)
            P.add(at(sphere(.62, 8, 6), pts[-1]), sh, smooth=True)
    P.add(at(sphere(.45, 8, 6), (0, h + .25, 0)), S('pink', base=.6), smooth=True)
    return P

def mesa_rock(seed, r=7.0):
    rng = random.Random(seed); P = Prop('Mesa%d' % seed); y = -.6
    for k in range(rng.randint(3, 4)):
        rr = r * (1 - k * .18); hh = rng.uniform(1.6, 2.6)
        pts = [(math.cos(a) * rr * rng.uniform(.85, 1.05), math.sin(a) * rr * rng.uniform(.85, 1.05)) for a in [i * math.tau / 9 for i in range(9)]]
        P.add(ngon_prism(pts, y, y + hh, .3), S('sand' if k % 2 == 0 else 'dirt', base=.5 + k * .05, up=.25, jit=.03)); y += hh
    return P

def ice_spike(seed, s=1.0):
    rng = random.Random(seed); P = Prop('IceSpike%d' % seed)
    for k in range(rng.randint(3, 5)):
        h = rng.uniform(5, 11) * s * (1.25 if k == 0 else 1); a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(1, 2.2) * s
        rot = (rng.uniform(-18, 18), 0, rng.uniform(-18, 18)) if k else (0, 0, 0)
        g = lathe([(0, -.5), (1.2 * s, .2 * h), (.9 * s, .7 * h), (0, h)], n=5)
        if k == 1: P.gadd(at(g, (math.cos(a) * d, 0, math.sin(a) * d), rot), 'ice')
        else: P.add(at(g, (math.cos(a) * d, 0, math.sin(a) * d), rot), S('ice', grad=(0, h, .35, .9)))
    return P

def snow_tree(seed, h=14.0):
    rng = random.Random(seed); P = Prop('SnowTree%d' % seed)
    P.add(cyl(h * .05, h * .3, sides=7, y0=-.4), S('wood', base=.4))
    for i in range(3):
        y = h * (.22 + .22 * i); R = h * .34 * (1 - i * .24)
        P.add(lathe([(R, y), (R * .55, y + h * .2), (0, y + h * .3)], n=12), S('leaf', base=.35 + i * .06, up=.1), smooth=True)
        P.add(lathe([(R * .72, y + h * .1), (R * .4, y + h * .22), (0, y + h * .31)], n=12), S('snow', grad=(y, y + h * .3, .6, .95)), smooth=True)
    return P

def basalt_rocks(seed, s=1.0):
    rng = random.Random(seed); P = Prop('Basalt%d' % seed)
    for k in range(rng.randint(4, 7)):
        a = rng.uniform(0, math.tau); d = rng.uniform(0, 2.4) * s; h = rng.uniform(2, 6.5) * s
        P.add(at(cyl(rng.uniform(.8, 1.3) * s, h, sides=6, y0=-.4), (math.cos(a) * d, 0, math.sin(a) * d), (0, rng.uniform(0, 60), 0)),
              S('basalt', grad=(0, h, .3, .62)))
        if k % 3 == 0: P.gadd(at(cyl(.25 * s, h * .7, sides=4, y0=0), (math.cos(a) * d + .9 * s, 0, math.sin(a) * d)), 'lava')
    return P

def lava_pool(seed, r=6.0):
    rng = random.Random(seed); P = Prop('LavaPool%d' % seed)
    pts = [(math.cos(a) * r * rng.uniform(.85, 1.1), math.sin(a) * r * rng.uniform(.85, 1.1)) for a in [i * math.tau / 12 for i in range(12)]]
    P.add(ngon_prism(pts, -.5, .5, .3), S('basalt', base=.42, up=.2))
    inner = [(x * .78, z * .78) for x, z in pts]
    P.gadd(ngon_prism(inner, .35, .62), 'lava')
    for k in range(5):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(.9, 1.2)
        P.add(at(hull(rock_pts((1.2, .9, 1.0), n=12, seed=seed * 9 + k)), (math.cos(a) * d, .3, math.sin(a) * d)), S('basalt', base=.5))
    return P

def charred_tree(seed, h=10.0):
    rng = random.Random(seed); P = Prop('Charred%d' % seed)
    pts = [Vector((0, -.4, 0)), Vector((rng.uniform(-.6, .6), h * .5, 0)), Vector((rng.uniform(-1, 1), h, rng.uniform(-1, 1)))]
    P.add(tube(pts, [h * .07, h * .05, h * .02], sides=6), S('basalt', base=.45))
    for k in range(3):
        a = rng.uniform(0, math.tau); y = h * rng.uniform(.45, .8); L = h * rng.uniform(.25, .4)
        P.add(tube([Vector((0, y, 0)), Vector((math.cos(a) * L, y + L * .6, math.sin(a) * L))], [h * .03, h * .012], sides=5), S('basalt', base=.45))
    P.gadd(at(cyl(.2, h * .5, sides=4, y0=h * .1), (h * .06, 0, 0)), 'lava')
    return P

def bush(seed, col='leaf', r=2.2):
    rng = random.Random(seed); P = Prop('Bush%d_%s' % (seed, col))
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(.8, 1.6)
        rr = r * rng.uniform(.65, 1.0)
        P.add(at(sphere(rr, 12, 8), (math.cos(a) * d, rr * .6, math.sin(a) * d)), S(col, grad=(0, r * 1.6, .35, .85)), smooth=True)
    return P

def signpost(z):
    P = Prop('Sign%d' % z)
    P.add(cyl(.4, 6, sides=8, y0=-.4), S('wood', base=.45))
    P.add(at(box((6.0, 2.4, .5), .15), (0, 4.6, -.1)), S('wood', base=.6, up=.2))
    P.gadd(at(box((5.0, 1.4, .1)), (0, 4.6, -.4)), 'z%d' % z)
    P.add(at(ngon_prism([(-1.2, -.8), (1.2, -.8), (2.0, 0), (1.2, .8), (-1.2, .8)], -.25, .25), (0, 6.6, -.1), (90, 0, 0)), S('gold', base=.6))
    return P

# ------------------------------------------------------------------ hero
def trophy():
    """HERO: giant golden trophy on a tiered marble pedestal; cup with handles, crown + star, two tilted glow rings.
    ~60 tall."""
    P = Prop('Trophy')
    P.add(lathe([(17, -1.0), (17, 1.0), (15.5, 1.4), (15.5, 3.2), (13, 3.6), (13, 5.6), (10.5, 6.0), (10.5, 8.2), (0, 8.2)], n=40),
          S('cloud', base=.5, up=.22))
    for y, r in ((1.0, 17.1), (3.2, 15.6), (5.6, 13.1), (8.2, 10.6)): P.add(at(torus(r, .35, n=48, sides=5), (0, y, 0)), S('gold', base=.55))
    for k in range(4): P.add(at(box((12 - k * 1.5, 1.2, 3.0), .15), (0, -.2 + k * 2.1, -17.5 + k * 2.1)), S('cloud', base=.55 + k * .02))
    cup = [(6.0, 8.2), (6.4, 9.2), (3.6, 10.2), (2.0, 12.0), (1.6, 15.5), (2.4, 18.0), (5.0, 19.6), (8.6, 22.0),
           (10.6, 26.0), (11.4, 31.0), (11.8, 34.0), (12.6, 35.2), (11.2, 35.4), (10.2, 33.0), (0, 30.0)]
    P.add(lathe(cup, n=40), S('gold', grad=(8, 36, .42, .9), up=.15), smooth=True)
    for y in (19.6, 34.0): P.add(at(torus(5.2 if y < 20 else 12.0, .5, n=40, sides=6), (0, y, 0)), S('gold', base=.75))
    for sx in (-1, 1):                                                                                  # handles: smooth C-curves
        c = Vector((sx * 11.0, 26.6, 0))
        h = [c + Vector((sx * math.cos(math.radians(a)) * 5.2, math.sin(math.radians(a)) * 5.6, 0)) for a in range(78, -79, -12)]
        P.add(tube(h, 1.05, sides=10), S('gold', base=.65), smooth=True)
        for e in (h[0], h[-1]): P.add(at(sphere(1.35, 10, 7), e), S('gold', base=.72), smooth=True)
    P.add(at(cyl(5.6, .8, sides=28), (0, 26.5, -11.2), (90, 0, 0)), S('gold', base=.8), smooth=True)     # medallion on the cup
    star = [(math.cos(a) * (3.6 if i % 2 == 0 else 1.6), math.sin(a) * (3.6 if i % 2 == 0 else 1.6))
            for i, a in enumerate([k * math.tau / 10 - math.pi / 2 for k in range(10)])]
    P.add(at(ngon_prism(star, -.5, .5), (0, 26.5, -11.7), (90, 0, 0)), S('red', base=.6))
    P.add(lathe([(11.8, 35.0), (11.0, 36.6), (8.2, 38.4), (4.4, 39.4), (1.6, 39.8), (1.2, 41.6), (0, 41.8)], n=40),
          S('gold', grad=(35, 42, .55, .9)), smooth=True)                                           # lid
    for k in range(8):                                                                              # gems round the lid
        a = k * math.tau / 8
        P.gadd(at(gem(.9, 1.8), (math.cos(a) * 9.6, 36.9, math.sin(a) * 9.6), (90, -math.degrees(a) - 90, 0)), 'gem' if k % 2 else 'z5')
    P.add(at(sphere(1.6, 14, 9), (0, 42.6, 0)), S('gold', base=.75), smooth=True)
    P.add(at(ngon_prism(star, -.7, .7), (0, 47.4, 0), (90, 0, 0), s=(1.4, 1, 1.4)), S('gold', base=.85))
    P.gadd(at(torus(22, .6, n=56, sides=6), (0, 28, 0), (18, 0, 8)), 'shine')
    P.gadd(at(torus(25, .45, n=60, sides=6), (0, 24, 0), (-12, 40, -10)), 'z5')
    return P

def spawn_pad():
    P = Prop('SpawnPad')
    P.add(lathe([(7.0, -.5), (7.0, .3), (6.2, .5), (0, .5)], n=32), S('stone', base=.7))
    star = [(math.cos(a) * (4.4 if i % 2 == 0 else 2.0), math.sin(a) * (4.4 if i % 2 == 0 else 2.0))
            for i, a in enumerate([k * math.tau / 10 - math.pi / 2 for k in range(10)])]
    P.add(ngon_prism(star, .45, .62), S('gold', base=.65, jit=0))
    P.gadd(at(torus(6.6, .22, n=36, sides=5), (0, .45, 0)), 'pad')
    return P


def lava_crack(seed, L=16.0):
    """glowing zig-zag crack in the ground (flat, walk-over)"""
    rng = random.Random(seed); P = Prop('LavaCrack%d' % seed)
    pts = [Vector((0, .06, 0))]
    for k in range(6): pts.append(pts[-1] + Vector((rng.uniform(-1.6, 1.6), 0, -L / 6)))
    for a, b in zip(pts, pts[1:]):
        d = b - a; c = (a + b) / 2; ang = math.degrees(math.atan2(-d.x, -d.z))
        P.add(at(box((1.5, .12, d.length + .4)), c, (0, ang, 0)), S('basalt', base=.18, jit=0))
        P.gadd(at(box((.55, .16, d.length + .2)), c + Vector((0, .02, 0)), (0, ang, 0)), 'lava')
    return P


# v2 models override the first pass
from sky_models import *  # noqa
from sky_models2 import *  # noqa
from sky_models3 import *  # noqa
from sky_models4 import *  # noqa
