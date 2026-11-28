# Moon Sweepers prop kit. Roblox space (X east, Y up, Z south, 1 unit = 1 stud), origin = bottom centre, front = -Z.
# Theme: retro space programme (white panels, gold foil, orange safety chevrons, rivets, port windows, antennae).
# Signature edge detail: runway beacon posts (white post, steel collar, amber glow cap) on every lip and pad edge.
# Shared station base: hexagonal landing pad on four splayed lander legs with an orange chevron rim.
# Machinery (Prop, S, at, blob, materials, to_kit) from the skill's grove module; every PROP here is new.
import sys, os, math, random
SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(SK, 'examples', 'whispering_grove')); sys.path.insert(0, os.path.join(SK, 'scripts'))
import bmesh
from mathutils import Vector
import forest_props as G
from pro_lib import Palette, Sh, box, cyl, spike, tube, hull, rock_pts, nz, clamp

G.PAL = Palette({
    'regA':   ('#4d4943', '#9a958d', '#e2ddd3'),     # warm regolith (hub, dusty plains)
    'regB':   ('#2c2e33', '#686c74', '#b3b7bf'),     # cool lunar grey (crater field, risers)
    'mare':   ('#121317', '#2a2c32', '#5a5e68'),     # dark basalt (junkyard, dark side)
    'panel':  ('#8a94a6', '#dfe5ee', '#ffffff'),     # white tech panels
    'steel':  ('#262d3a', '#5a667c', '#aab8ce'),
    'foil':   ('#6e4204', '#dca226', '#fff2a6'),     # gold mylar blankets
    'orange': ('#9e3600', '#ff6a1a', '#ffb684'),     # safety orange
    'red':    ('#701020', '#d8283c', '#ff8a96'),
    'navy':   ('#0b1124', '#1c2a55', '#4d66aa'),     # solar cells, dark trims
    'ice':    ('#0f3756', '#3aa2d6', '#c6f3ff'),
    'frost':  ('#6f849f', '#cfdff0', '#ffffff'),
    'ocean':  ('#08245e', '#1d68c8', '#7cbcff'),     # Earth
    'land':   ('#294f1e', '#5f9638', '#cbd68e'),
    'rust':   ('#40200f', '#84461f', '#c98a52'),     # scorched / rusted junk
    'char':   ('#0a0a0c', '#26201e', '#4a3a30'),     # heat shield, burnt
})
G.MATS.clear()
ZONE = {1: '#ffd23a', 2: '#ff7a3a', 3: '#3ae0ff', 4: '#a57aff'}
G.GLOW.clear(); G.GLOW.update({'z%d' % k: v for k, v in ZONE.items()})
G.GLOW.update({'beacon': '#ffae2a', 'cyan': '#3fe6ff', 'sell': '#3dff8a', 'egg': '#ff4fd2', 'rebirth': '#9a4dff',
               'engine': '#ff7a22', 'ice': '#79f0ff', 'window': '#9fe2ff', 'meteor': '#ff5a1a', 'red': '#ff2a3a'})
G.GLOW_E.clear(); G.GLOW_E.update({'beacon': 2.6, 'cyan': 1.4, 'sell': 1.5, 'egg': 1.4, 'rebirth': 1.3, 'engine': 3.0,
                                   'ice': 1.2, 'window': 1.0, 'meteor': 2.6, 'red': 2.4})
for k in ZONE: G.GLOW_E['z%d' % k] = 1.8
Prop, S, at, blob = G.Prop, G.S, G.at, G.blob
PAL = G.PAL

# ------------------------------------------------------------------ helpers
def smooth(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

def lerp(a, b, t): return a + (b - a) * t

def lathe(profile, n=24, y_off=0.0, a0=0.0):
    """revolve [(r, y), ...] (bottom -> top) around Y; r == 0 collapses to a point"""
    bm = bmesh.new(); rings = []
    for r, y in profile:
        if r <= 1e-4: rings.append([bm.verts.new((0, y + y_off, 0))])
        else: rings.append([bm.verts.new((math.cos(a0 + a) * r, y + y_off, math.sin(a0 + a) * r)) for a in [i * math.tau / n for i in range(n)]])
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

def torus(R, r, n=24, sides=6, y=0.0, a0=0.0, a1=math.tau):
    full = abs(a1 - a0 - math.tau) < 1e-6
    pts = [Vector((math.cos(a) * R, y, math.sin(a) * R)) for a in [a0 + (a1 - a0) * i / n for i in range(n + 1)]]
    return tube(pts, r, sides=sides, cap0=not full, cap1=not full)

def beam(a, b, r=.35, sides=6):
    return tube([Vector(a), Vector(b)], r, sides=sides)

def egg(r, h, n=16):
    prof = [(0, 0)] + [(r * math.sin(t * math.pi) * (1 - .18 * t), h * (1 - math.cos(t * math.pi)) / 2) for t in [k / 10 for k in range(1, 10)]] + [(0, h)]
    return lathe(prof, n)

def dish(R, depth, n=20, t=.25):
    """parabolic dish opening up (+Y), thickness t"""
    prof = [(0, 0)] + [(R * k / 6, depth * (k / 6) ** 2) for k in range(1, 7)] + [(R + t, depth + t * .3)]
    prof += [(R * k / 6 * .97, depth * (k / 6) ** 2 + t) for k in range(6, 0, -1)] + [(0, t)]
    return lathe(prof, n)

class ShAng(Sh):
    """two-colour checker by face angle around Y (rocket roll pattern / foil wraps)"""
    def __init__(self, a, b, n, **k):
        super().__init__(PAL, a, **k); self.b = b; self.n = n
    def __call__(self, f):
        c = f.calc_center_median(); i = int((math.atan2(c.z, c.x) % math.tau) / math.tau * self.n)
        save = self.col
        if i % 2: self.col = self.b
        out = Sh.__call__(self, f); self.col = save
        return out

def rivets(P, cx, cy, cz, R, n, col='steel', s=.18, a0=0.0):
    for k in range(n):
        a = a0 + k * math.tau / n
        P.add(at(cyl(s, s * .8, sides=5), (cx + math.cos(a) * R, cy, cz + math.sin(a) * R)), S(col, base=.65, jit=0))

def port(P, pos, yaw, r=1.0, glow='window', frame='steel', pitch=0.0):
    """round port window: steel frame ring + rivets + glowing pane set back; faces -Z before yaw"""
    P.add(at(torus(r, r * .18, n=16, sides=5), pos, (90 + pitch, yaw, 0)), S(frame, base=.55, jit=0), smooth=True)
    P.gadd(at(cyl(r * .86, .08, sides=14), pos, (90 + pitch, yaw, 0)), glow)

def beacon_post(P, x, y, z, h=2.4, key='beacon', col='panel'):
    """signature: white octagonal post, steel collar, amber glow cap"""
    P.add(at(cyl(.62, .3, sides=8, bev=.08), (x, y - .4, z)), S('steel', base=.4, jit=0))
    P.add(at(cyl(.32, h, sides=8, bev=.06, y0=-.2), (x, y, z)), S(col, base=.62, up=.15, jit=.02))
    P.add(at(cyl(.42, .3, sides=8, bev=.06), (x, y + h - .45, z)), S('steel', base=.55, jit=0))
    P.gadd(at(lathe([(0, 0), (.36, .02), (.4, .3), (.26, .58), (0, .66)], n=8), (x, y + h - .18, z)), key)

# ------------------------------------------------------------------ signature edge: beacon rail
def beacon_rail(L=10.0, key='beacon'):
    """post at x=0 + a sagging cable to the next post (x = L, not included): chain these along every lip"""
    P = Prop('BeaconRail_%s' % key)
    beacon_post(P, 0, 0, 0, key=key)
    pts = [Vector(((L - .45) * t, 1.85 - math.sin(t * math.pi) * .35, 0)) for t in [k / 6 for k in range(7)]]   # ends at the next post's face
    P.add(tube(pts, .09, sides=5), S('steel', base=.35, jit=0))
    P.add(at(box((1.6, .25, 1.6), .08), (0, -.1, 0)), S('steel', base=.3, jit=0))
    return P

# ------------------------------------------------------------------ shared station base
def station_base(P, R=9.0, top=2.4):
    """hex landing pad on 4 splayed lander legs; chevron rim; corner beacons. Adds into P, deck top = y top"""
    P.add(at(cyl(R, .9, sides=6, bev=.25, rot0=math.pi / 6), (0, top - .9, 0)), S('panel', base=.55, up=.25, jit=.02))
    P.add(at(cyl(R + .5, .5, sides=6, bev=.15, rot0=math.pi / 6), (0, top - 1.35, 0)), S('steel', base=.35, jit=0))
    P.add(at(cyl(R * .62, .14, sides=6, rot0=math.pi / 6), (0, top - .02, 0)), S('steel', base=.62, jit=0))     # inner plate
    for k in range(6):                                                            # orange chevron rim on each edge
        a = math.pi / 6 + (k + .5) * math.tau / 6; ap = math.pi / 6 + k * math.tau / 6
        ex, ez = math.cos(a) * R * .93, math.sin(a) * R * .93
        yaw = -math.degrees(a) + 90
        for j in (-1, 0, 1):
            ox = math.cos(a + math.pi / 2) * j * 2.0; oz = math.sin(a + math.pi / 2) * j * 2.0
            for sg in (-1, 1):
                P.add(at(at(box((1.1, .12, .34), .04), (sg * .28, 0, 0), (0, sg * 45, 0)), (ex + ox, top + .02, ez + oz), (0, yaw, 0)),
                      S('orange', base=.62, jit=0))
        cx, cz = math.cos(ap) * (R - .9), math.sin(ap) * (R - .9)
        beacon_post(P, cx, top, cz, h=1.5)
    for k in range(4):                                                            # splayed legs + footpads
        a = math.pi / 4 + k * math.tau / 4
        top_p = Vector((math.cos(a) * R * .55, top - 1.3, math.sin(a) * R * .55))
        foot = Vector((math.cos(a) * (R + 1.6), .3, math.sin(a) * (R + 1.6)))
        P.add(tube([top_p, foot], .42, sides=8), S('steel', base=.5, jit=0), smooth=True)
        mid = top_p.lerp(foot, .55)
        P.add(tube([Vector((math.cos(a + .5) * R * .7, top - 1.3, math.sin(a + .5) * R * .7)), mid], .2, sides=6), S('foil', base=.6, jit=0))
        P.add(at(lathe([(0, -.4), (1.4, -.4), (1.5, 0), (1.1, .35), (.5, .45), (0, .45)], n=12), foot), S('panel', base=.5, jit=0), smooth=True)
        P.add(at(cyl(.55, .5, sides=8), foot + Vector((0, .35, 0))), S('steel', base=.4, jit=0))
    # foil skirt hanging under the deck (hides the hollow)
    P.add(at(cyl(R * .7, top - 1.3, sides=6, rot0=math.pi / 6, r2=R * .82), (0, 0, 0)), S('foil', base=.5, up=.1, jit=.18, seed=3))

# ------------------------------------------------------------------ hub stations
def dust_exchange():
    """SELL: a gold-foil intake hopper on the base, ribbed vacuum hose to a nozzle, glowing dust canisters + coin screen"""
    P = Prop('DustExchange'); station_base(P); T = 2.4
    hop = lathe([(1.6, 0), (1.9, 1.2), (6.2, 6.0), (6.6, 6.5), (6.6, 7.2), (6.0, 7.3), (5.7, 6.6), (2.2, 3.4), (0, 3.4)], n=20)
    P.add(at(hop, (0, T + 7.2, 1.0)), S('panel', base=.55, up=.25, jit=.02), smooth=True)
    P.add(at(torus(6.7, .35, n=24, sides=6), (0, T + 13.9, 1.0)), S('orange', base=.6, jit=0), smooth=True)
    P.add(at(torus(6.4, .25, n=24, sides=6), (0, T + 12.2, 1.0)), S('steel', base=.45, jit=0), smooth=True)
    P.gadd(at(lathe([(0, 0), (4.6, 0), (5.0, .3), (0, 1.4)], n=20), (0, T + 11.9, 1.0)), 'sell')   # glowing dust heap in the bowl
    P.add(at(cyl(1.7, 7.2, sides=12, bev=.1), (0, T, 1.0)), S('steel', base=.45, jit=0), smooth=True)  # neck
    for k in range(4):                                                            # struts
        a = math.pi / 4 + k * math.tau / 4
        P.add(beam((math.cos(a) * 5.0, T, 1.0 + math.sin(a) * 5.0), (math.cos(a) * 4.6, T + 9.6, 1.0 + math.sin(a) * 4.6), .3), S('steel', base=.5, jit=0))
        P.add(at(box((.9, .9, .9), .15), (math.cos(a) * 4.6, T + 9.6, 1.0 + math.sin(a) * 4.6)), S('orange', base=.55, jit=0))
    rivets(P, 0, T + 13.3, 1.0, 6.5, 16)
    # hose: from the hopper rim over the front to a nozzle head at the deck edge, ribbed with rings
    hp = [Vector(p) for p in ((-4.8, T + 12.4, -2.5), (-6.6, T + 12.0, -5.0), (-7.2, T + 8.0, -6.6), (-6.4, T + 3.6, -7.0), (-4.6, T + 1.6, -6.6))]
    sm = []
    for a, b in zip(hp, hp[1:]): sm += [a.lerp(b, t / 4) for t in range(4)]
    sm.append(hp[-1])
    P.add(tube(sm, .75, sides=10), S('steel', base=.35, jit=0), smooth=True)
    for i in range(1, len(sm) - 1, 2):
        d = (sm[i + 1] - sm[i - 1]).normalized()
        q = d.to_track_quat('Y', 'Z').to_euler()
        rb = torus(.85, .14, n=12, sides=4); bmesh.ops.rotate(rb, cent=Vector(), matrix=q.to_matrix(), verts=rb.verts)
        bmesh.ops.translate(rb, vec=sm[i], verts=rb.verts); P.add(rb, S('orange', base=.6, jit=0), smooth=True)
    P.add(at(lathe([(0, 0), (1.5, 0), (1.5, .4), (1.0, 1.6), (.85, 2.6), (0, 2.6)], n=14), (-4.6, T + 1.6, -6.6), (180, 0, 0)), S('panel', base=.6, jit=0), smooth=True)
    P.add(at(box((3.2, .6, 3.2), .15), (-4.6, T, -6.6)), S('steel', base=.35, jit=0))
    # canister rack (right side): 3 glass canisters with glowing dust
    P.add(at(box((7.6, .6, 2.6), .15), (4.2, T, -5.4)), S('steel', base=.4, jit=0))
    P.add(at(box((7.6, .5, 2.6), .15), (4.2, T + 5.6, -5.4)), S('steel', base=.4, jit=0))
    for j in range(3):
        x = 1.8 + j * 2.4
        P.add(at(cyl(1.0, .5, sides=12, bev=.1), (x, T + .6, -5.4)), S('panel', base=.6, jit=0), smooth=True)
        P.add(at(cyl(1.0, .5, sides=12, bev=.1), (x, T + 5.1, -5.4)), S('panel', base=.6, jit=0), smooth=True)
        P.gadd(at(cyl(.82, 1.8 + j * .9, sides=12), (x, T + 1.1, -5.4)), 'sell')
        P.add(at(cyl(.86, 4.0 - (1.8 + j * .9), sides=12), (x, T + 1.1 + 1.8 + j * .9, -5.4)), S('navy', base=.4, jit=0), smooth=True)
        for sx in (-1, 1): P.add(beam((x + sx * 1.05, T + 1.1, -6.3), (x + sx * 1.05, T + 5.1, -6.3), .1, 4), S('steel', base=.6, jit=0))
    # coin screen on a mast (left back): frame, glowing coin icon (disc + ring), antenna
    P.add(beam((-5.6, T, 4.6), (-5.6, T + 9.4, 4.6), .35), S('steel', base=.45, jit=0))
    P.add(at(box((5.2, 4.2, .7), .25), (-5.6, T + 9.4, 4.2), (0, 25, 0)), S('panel', base=.6, jit=.02))
    P.add(at(box((4.4, 3.4, .3), .1), (-5.6 + .15, T + 9.8, 3.8), (0, 25, 0)), S('navy', base=.3, jit=0))
    P.gadd(at(cyl(1.2, .12, sides=14), (-5.6 + .3, T + 9.8, 3.62), (90, 25, 0)), 'sell')
    P.add(at(torus(1.35, .14, n=14, sides=4), (-5.6 + .32, T + 9.8, 3.58), (90, 25, 0)), S('foil', base=.65, jit=0))
    return P

def vac_pack(P, x, y, z, yaw=0.0, col='orange'):
    """vacuum backpack: twin tanks, frame, dust window, hose loop + nozzle (hangs on a hook)"""
    for sx in (-1, 1):
        P.add(at(lathe([(0, 0), (.7, .1), (.8, .5), (.8, 3.0), (.6, 3.5), (0, 3.6)], n=12), (x + sx * .85, y, z), (0, yaw, 0)), S(col, base=.58, jit=0), smooth=True)
        P.add(at(torus(.82, .1, n=12, sides=4), (x + sx * .85, y + 1.2, z)), S('steel', base=.5, jit=0))
    P.gadd(at(box((.5, 1.6, .2)), (x, y + 1.6, z - .55)), 'cyan')
    P.add(at(box((2.6, .35, .5), .08), (x, y + 3.0, z + .3)), S('steel', base=.4, jit=0))
    P.add(at(box((2.6, .35, .5), .08), (x, y + .5, z + .3)), S('steel', base=.4, jit=0))
    hp = [Vector((x + 1.4, y + 2.6, z - .2)), Vector((x + 2.0, y + 1.2, z - .7)), Vector((x + 1.6, y - .6, z - .9)), Vector((x + .8, y - 1.4, z - 1.0))]
    P.add(tube(hp, .22, sides=6), S('steel', base=.3, jit=0), smooth=True)
    P.add(at(cyl(.32, 1.4, sides=8, r2=.5), (x + .8, y - 2.8, z - 1.0)), S('panel', base=.6, jit=0))

def gear_locker():
    """SHOP: curved white locker wall with 3 vacuum packs on hooks, central holo pedestal with a glowing vacuum gun"""
    P = Prop('GearLocker'); station_base(P); T = 2.4
    for k in range(7):                                                            # curved back wall (panels + ribs)
        a = math.radians(-135 + k * 15 + 7.5) + math.pi; x, z = math.cos(a) * 7.0, math.sin(a) * 7.0
        yaw = -math.degrees(a) - 90
        P.add(at(box((1.9, 10.0, .7), .18), (x, T, z), (0, yaw, 0)), S('panel', base=.56, up=.15, jit=.03, seed=k))
        P.add(at(box((1.85, 9.2, .3), .06), (x * .93, T + .2, z * .93), (0, yaw, 0)), S('navy', base=.3, up=.1, jit=.03, seed=k))
        P.gadd(at(box((.25, 6.0, .1)), (x * .905, T + 2.2, z * .905), (0, yaw, 0)), 'cyan')
    for k in range(8):
        a = math.radians(-135 + k * 15) + math.pi; x, z = math.cos(a) * 7.0, math.sin(a) * 7.0
        P.add(at(cyl(.32, 10.6, sides=8, bev=.08), (x, T, z)), S('steel', base=.45, jit=0))
    P.add(at(torus(7.0, .4, n=18, sides=6, y=T + 10.4, a0=math.radians(45), a1=math.radians(135)), (0, 0, 0)), S('orange', base=.6, jit=0), smooth=True)
    # canopy: angled roof panels with a light strip
    for k in range(6):
        a = math.radians(45 + k * 15 + 7.5); x, z = math.cos(a) * 5.4, math.sin(a) * 5.4
        P.add(at(box((2.0, .35, 5.0), .1), (x, T + 11.3, z), (14, -math.degrees(a) + 90, 0)), S('panel', base=.65, jit=.02))
    P.gadd(at(torus(4.0, .14, n=16, sides=4, y=T + 11.0, a0=math.radians(50), a1=math.radians(130)), (0, 0, 0)), 'cyan')
    for j, (a, col) in enumerate(((112, 'orange'), (90, 'red'), (68, 'foil'))):  # 3 packs on hooks
        r = math.radians(a); x, z = math.cos(r) * 6.0, math.sin(r) * 6.0
        P.add(at(box((.3, .3, 1.0)), (x, T + 7.0, z - .3)), S('steel', base=.5, jit=0))
        vac_pack(P, x, T + 2.8, z - .8, 0, col)
    # holo pedestal + gun hologram
    P.add(at(cyl(2.2, .6, sides=6, bev=.15), (0, T, -3.4)), S('steel', base=.4, jit=0))
    P.add(at(cyl(1.5, 3.2, sides=6, bev=.15, r2=1.2), (0, T + .6, -3.4)), S('panel', base=.6, jit=.02))
    P.gadd(at(torus(1.35, .12, n=14, sides=4), (0, T + 3.85, -3.4)), 'cyan')
    gy = T + 5.6
    P.gadd(at(cyl(.55, 3.6, sides=10), (0, gy, -1.6), (90, 0, 0)), 'cyan')       # barrel
    P.gadd(at(lathe([(0, 0), (.6, 0), (1.3, 1.4), (0, 1.4)], n=10), (0, gy, -5.3), (90, 0, 0)), 'cyan')   # nozzle bell
    P.gadd(at(cyl(1.0, 1.8, sides=10), (0, gy - .2, -1.0), (90, 0, 0)), 'cyan')   # dust chamber
    P.gadd(at(box((.5, 1.6, .7)), (0, gy - 1.4, -.6), (15, 0, 0)), 'cyan')        # grip
    return P

def reentry_pod():
    """REBIRTH: scorched capsule on its heat shield, port windows, RCS quads, glowing orbit ring on 3 arms"""
    P = Prop('ReentryPod'); station_base(P); T = 2.4
    P.add(at(lathe([(0, 0), (5.6, .2), (6.0, .9), (5.8, 1.5), (0, 1.6)], n=24), (0, T, 0)), S('char', base=.45, jit=.15, seed=2), smooth=True)
    P.add(at(lathe([(5.5, 0), (5.3, 1.0), (2.8, 8.4), (2.6, 9.0), (0, 9.1)], n=24), (0, T + 1.5, 0)),
          ShAng('panel', 'panel', 24, base=.55, up=.2, jit=.04), smooth=True)
    for y, r in ((T + 3.0, 5.0), (T + 6.2, 3.8)):
        P.add(at(torus(r, .2, n=24, sides=4, y=y), (0, 0, 0)), S('steel', base=.5, jit=0), smooth=True)
    P.add(at(cyl(2.3, 1.6, sides=16, bev=.2), (0, T + 10.4, 0)), S('foil', base=.6, jit=.12))
    P.add(at(cyl(1.6, .8, sides=16, bev=.15), (0, T + 12.0, 0)), S('steel', base=.45, jit=0))
    P.add(at(box((3.0, 3.6, .6), .25), (0, T + 3.0, -4.62), (-18, 0, 0)), S('steel', base=.4, jit=0))     # hatch frame
    P.add(at(box((2.4, 3.0, .4), .2), (0, T + 3.3, -4.85), (-18, 0, 0)), S('panel', base=.66, jit=0))
    P.add(at(box((1.6, .3, .3), .08), (0, T + 4.6, -4.75), (-18, 0, 0)), S('orange', base=.6, jit=0))
    for sx in (-1, 1): port(P, (sx * 2.85, T + 6.4, -2.85), sx * 45, .7, 'window', pitch=18)
    for k in range(4):                                                            # RCS quads
        a = math.pi / 4 + k * math.tau / 4; x, z = math.cos(a) * 3.55, math.sin(a) * 3.55
        P.add(at(box((1.0, 1.0, .6), .12), (x, T + 6.6, z), (0, -math.degrees(a) - 90, 0)), S('steel', base=.4, jit=0))
        for d in (-1, 1): P.add(at(cyl(.15, .5, sides=6, r2=.25), (x + math.cos(a) * .3, T + 7.0 + d * .55, z + math.sin(a) * .3), (0 if d > 0 else 180, 0, 0)), S('char', base=.5, jit=0))
    P.gadd(at(torus(9.4, .45, n=40, sides=6, y=T + 6.0), (0, 0, 0)), 'rebirth')          # orbit ring
    for k in range(3):
        a = math.pi / 2 + k * math.tau / 3; x, z = math.cos(a), math.sin(a)
        P.add(beam((x * 6.6, T, z * 6.6), (x * 9.4, T + 5.6, z * 9.4), .35), S('steel', base=.5, jit=0))
        P.add(at(box((1.4, 1.4, 1.4), .3), (x * 9.4, T + 5.3, z * 9.4)), S('panel', base=.6, jit=0))
        P.gadd(at(cyl(.5, .2, sides=8), (x * 9.4, T + 4.55, z * 9.4)), 'rebirth')
    return P

def egg_incubator():
    """PETS: console with a screen, 3 cryo cages (ring + ribs) holding alien eggs with glowing spots, coolant pipes"""
    P = Prop('EggIncubator'); station_base(P); T = 2.4
    P.add(at(cyl(2.0, 4.4, sides=6, bev=.25, r2=1.6), (0, T, 1.0)), S('panel', base=.55, jit=.02))
    P.add(at(box((3.2, 2.2, .5), .15), (0, T + 4.8, .1), (-25, 0, 0)), S('steel', base=.4, jit=0))
    P.gadd(at(box((2.6, 1.6, .1)), (0, T + 4.85, -.16), (-25, 0, 0)), 'egg')
    P.add(at(cyl(.9, .7, sides=6, bev=.1), (0, T + 4.4, 1.0)), S('steel', base=.4, jit=0))
    pals = [('egg', 'panel'), ('cyan', 'ice'), ('sell', 'land')]
    for j, a in enumerate((-150, -90, -30)):
        r = math.radians(a); x, z = math.cos(r) * 5.6, math.sin(r) * 5.6
        P.add(at(cyl(2.2, 1.0, sides=12, bev=.2), (x, T, z)), S('steel', base=.4, jit=0), smooth=True)
        P.add(at(cyl(1.9, .25, sides=12), (x, T + 1.0, z)), S('panel', base=.6, jit=0), smooth=True)
        P.add(at(torus(2.05, .2, n=16, sides=4, y=T + 1.15), (x, 0, z)), S('orange', base=.6, jit=0), smooth=True)
        g, ec = pals[j]
        P.add(at(egg(1.25, 3.6, n=14), (x, T + 1.2, z)), S(ec, base=.55, up=.25, jit=0), smooth=True)
        for k in range(5):
            u = k * 1.3 + j; h = 1.0 + (k * .53) % 2.4
            rr = 1.22 * math.sin(math.pi * h / 3.6) ** .7
            P.gadd(at(blob(.32, k + j * 7, n=10, sq=.5), (x + math.cos(u) * rr, T + 1.2 + h, z + math.sin(u) * rr)), g)
        for k in range(4):                                                        # cage ribs over the egg
            u = k * math.pi / 4
            pts = [Vector((x + math.cos(u) * 2.05 * math.cos(t), T + 1.2 + 4.6 * math.sin(t) ** .8, z + math.sin(u) * 2.05 * math.cos(t))) for t in [i / 8 * math.pi for i in range(9)]]
            P.add(tube(pts, .12, sides=4), S('steel', base=.55, jit=0))
        P.add(at(cyl(.6, .4, sides=8), (x, T + 5.75, z)), S('panel', base=.6, jit=0))
        P.gadd(at(cyl(.4, .15, sides=8), (x, T + 6.15, z)), g)
        P.add(tube([Vector((0, T + .5, .4)), Vector((x * .5, T + .5, z * .5 + .2)), Vector((x * .82, T + .5, z * .82))], .25, sides=6), S('foil', base=.6, jit=0), smooth=True)
    return P

# ------------------------------------------------------------------ hub landmark: lunar lander
def lunar_lander():
    """gold-foil descent stage on 4 legs with dish feet, faceted ascent cabin, triangular windows, dish antenna, RCS, ladder"""
    P = Prop('LunarLander'); y0 = 6.0
    P.add(at(cyl(5.2, 4.0, sides=8, bev=.3, rot0=math.pi / 8), (0, y0, 0)), S('foil', base=.55, up=.15, jit=.2, seed=4))
    for k in range(8):                                                            # crinkled foil pillows per face
        a = math.pi / 8 + (k + .5) * math.tau / 8
        P.add(at(blob(1.9, 30 + k, n=18, sq=1.0), (math.cos(a) * 4.7, y0 + 2.0, math.sin(a) * 4.7), (0, -math.degrees(a), 0), (.4, .9, 1.0)),
              S('foil', base=.62, jit=.2, seed=k), smooth=False)
    P.add(at(cyl(5.4, .4, sides=8, rot0=math.pi / 8), (0, y0 + 4.0, 0)), S('steel', base=.4, jit=0))
    P.add(at(cyl(5.4, .4, sides=8, rot0=math.pi / 8), (0, y0 - .2, 0)), S('steel', base=.35, jit=0))
    P.add(at(lathe([(1.2, 0), (2.6, -2.2), (2.5, -2.4), (1.0, -.2)], n=14), (0, y0, 0)), S('char', base=.4, jit=0), smooth=True)   # descent engine bell
    for k in range(4):
        a = math.pi / 4 + k * math.tau / 4; d = Vector((math.cos(a), 0, math.sin(a)))
        hip = d * 5.0 + Vector((0, y0 + 3.0, 0)); foot = d * 10.0 + Vector((0, .5, 0))
        P.add(tube([hip, foot], .42, sides=8), S('foil', base=.55, jit=.1), smooth=True)
        for sd in (-1, 1):
            side = Vector((-d.z, 0, d.x)) * sd
            P.add(tube([d * 4.6 + side * 3.0 + Vector((0, y0 + .2, 0)), hip.lerp(foot, .6)], .2, sides=6), S('steel', base=.5, jit=0))
        P.add(tube([d * 5.0 + Vector((0, y0 - .1, 0)), hip.lerp(foot, .6)], .2, sides=6), S('steel', base=.45, jit=0))
        P.add(at(lathe([(0, -.3), (1.7, -.3), (1.9, .1), (1.3, .5), (0, .55)], n=14), foot), S('foil', base=.6, jit=.08), smooth=True)
        P.add(beam(foot + Vector((0, .4, 0)), foot + Vector((0, -1.4, 0)) + d * .3, .08, 4), S('steel', base=.5, jit=0))   # contact probe
    # ladder on the front (-Z) leg + porch
    fl = Vector((math.cos(-math.pi * .5), 0, math.sin(-math.pi * .5)))
    P.add(at(box((3.2, .3, 2.4), .08), (0, y0 + 4.2, -5.6)), S('steel', base=.45, jit=0))
    for sx in (-1, 1): P.add(beam((sx * .8, y0 + 4.0, -6.6), (sx * .8, 1.2, -9.4), .12, 5), S('steel', base=.55, jit=0))
    for k in range(7):
        t = (k + .5) / 7; P.add(beam((-.8, y0 + 4.0 + (1.2 - y0 - 4.0) * t, -6.6 + (-2.8) * t), (.8, y0 + 4.0 + (1.2 - y0 - 4.0) * t, -6.6 + (-2.8) * t), .1, 4), S('steel', base=.6, jit=0))
    # ascent stage: faceted cabin
    yA = y0 + 4.4
    cab = [(-3.6, 0, -3.2), (3.6, 0, -3.2), (-3.6, 0, 3.4), (3.6, 0, 3.4), (-3.9, 2.6, -3.0), (3.9, 2.6, -3.0), (-4.2, 3.4, 1.8), (4.2, 3.4, 1.8),
           (-2.6, 5.4, -2.4), (2.6, 5.4, -2.4), (-3.2, 5.8, 2.6), (3.2, 5.8, 2.6), (-1.8, 2.0, -4.0), (1.8, 2.0, -4.0), (-1.4, 4.8, -3.4), (1.4, 4.8, -3.4)]
    P.add(at(hull([Vector(p) for p in cab]), (0, yA, 0)), S('panel', base=.5, up=.25, jit=.08, seed=7))
    P.add(at(box((3.2, 2.8, 2.4), .2), (4.6, yA + 1.0, 1.0)), S('foil', base=.55, jit=.15))      # side tank
    P.add(at(box((3.0, 2.6, 2.2), .2), (-4.4, yA + 1.4, .8)), S('steel', base=.4, jit=.05))
    for sx in (-1, 1):                                                            # triangular windows in frames
        tri = [Vector((sx * .5, 3.2, 0)), Vector((sx * 1.7, 3.2, 0)), Vector((sx * .6, 4.5, 0))]
        cen = sum(tri, Vector()) / 3
        big = [cen + (p - cen) * 1.35 for p in tri]
        P.add(at(hull([p + Vector((0, 0, z)) for p in big for z in (-.05, .6)]), (0, yA, -3.75)), S('steel', base=.3, jit=0))
        P.gadd(at(hull([p + Vector((0, 0, z)) for p in tri for z in (-.12, .2)]), (0, yA, -3.75)), 'window')
    P.add(at(box((1.8, 1.8, .4), .15), (0, yA + 1.2, -3.85)), S('steel', base=.45, jit=0))       # hatch
    P.add(at(cyl(1.4, 1.0, sides=12, bev=.15), (0, yA + 5.6, .4)), S('steel', base=.45, jit=0))  # docking port
    P.add(at(torus(1.45, .15, n=12, sides=4, y=yA + 6.6), (0, 0, .4)), S('orange', base=.6, jit=0))
    P.add(beam((-2.0, yA + 5.2, 2.0), (-3.4, yA + 8.6, 3.0), .14, 5), S('steel', base=.5, jit=0))   # dish antenna
    P.add(at(dish(1.8, .7, n=16), (-3.4, yA + 8.4, 3.0), (-35, 30, 0)), S('panel', base=.6, jit=0), smooth=True)
    P.add(beam((2.4, yA + 5.4, 1.6), (2.8, yA + 9.4, 1.8), .07, 4), S('steel', base=.6, jit=0))
    P.gadd(at(cyl(.2, .3, sides=6), (2.8, yA + 9.4, 1.8)), 'red')
    for k in range(4):                                                            # RCS quads on booms
        a = math.pi / 4 + k * math.tau / 4; d = Vector((math.cos(a) * 4.6, yA + 3.4, math.sin(a) * 4.0))
        P.add(beam(Vector((d.x * .7, d.y, d.z * .7)), d, .15, 5), S('steel', base=.45, jit=0))
        P.add(at(box((1.0, 1.0, 1.0), .2), d), S('panel', base=.6, jit=0))
        P.add(at(cyl(.14, .5, sides=6, r2=.26), d + Vector((0, .45, 0))), S('char', base=.5, jit=0))
        P.add(at(cyl(.14, .5, sides=6, r2=.26), d - Vector((0, .45, 0)), (180, 0, 0)), S('char', base=.5, jit=0))
    return P

# ------------------------------------------------------------------ hero: the moon rocket + launch tower
def moon_rocket():
    """three-stage rocket on a launch mount: roll-pattern checker, orange bands, foil interstage, 5 engine bells, fins,
    capsule + escape tower; ~92 tall"""
    P = Prop('MoonRocket'); B = 9.0                                               # B = base of the first stage
    P.add(at(cyl(14.0, 2.0, sides=8, bev=.4, rot0=math.pi / 8), (0, -1.0, 0)), S('steel', base=.35, jit=0))   # pad plinth
    P.add(at(cyl(12.0, .4, sides=8, rot0=math.pi / 8), (0, 1.0, 0)), S('panel', base=.5, jit=0))
    for k in range(8):                                                            # chevrons on the plinth top
        a = math.pi / 8 + (k + .5) * math.tau / 8
        for sg in (-1, 1):
            P.add(at(at(box((2.0, .15, .6), .05), (sg * .5, 0, 0), (0, sg * 45, 0)), (math.cos(a) * 10.5, 1.42, math.sin(a) * 10.5), (0, -math.degrees(a) + 90, 0)), S('orange', base=.62, jit=0))
        beacon_post(P, math.cos(a - math.tau / 16) * 13.2, 1.0, math.sin(a - math.tau / 16) * 13.2, h=1.6)
    P.add(at(cyl(8.0, 3.0, sides=16, bev=.3), (0, 1.4, 0)), S('steel', base=.45, jit=0))           # mount ring
    for k in range(4):                                                            # hold-down arms
        a = k * math.tau / 4 + math.pi / 4
        P.add(at(box((2.2, 4.2, 2.6), .3), (math.cos(a) * 7.6, 1.4, math.sin(a) * 7.6), (0, -math.degrees(a), 0)), S('orange', base=.55, jit=0))
    for k, (x, z) in enumerate(((0, 0), (3.0, 0), (-3.0, 0), (0, 3.0), (0, -3.0))):        # engine bells
        P.add(at(lathe([(2.0, 0), (1.9, .4), (1.2, 3.0), (.9, 4.4), (1.2, 4.8)], n=16), (x, B - 4.8, z)), S('char', base=.45, up=.1, jit=0), smooth=True)
        P.gadd(at(cyl(1.7, .15, sides=14), (x, B - 4.7, z)), 'engine')
    # first stage: roll-pattern checker band, orange belts, rivets
    P.add(at(lathe([(7.0, 0), (7.2, .6), (7.2, 12.0)], n=24), (0, B, 0)), S('panel', base=.56, up=.1, jit=.02), smooth=True)
    P.add(at(lathe([(7.2, 0), (7.2, 10.0)], n=24), (0, B + 12.0, 0)), ShAng('panel', 'navy', 8, base=.56, up=.1, jit=0), smooth=True)
    P.add(at(lathe([(7.2, 0), (7.2, 14.0), (6.4, 17.0)], n=24), (0, B + 22.0, 0)), S('panel', base=.58, up=.1, jit=.02), smooth=True)
    for y in (B + 2.5, B + 21.6, B + 34.0):
        P.add(at(torus(7.25, .55, n=24, sides=6, y=y), (0, 0, 0)), S('orange', base=.6, jit=0), smooth=True)
    rivets(P, 0, B + 11.8, 0, 7.3, 24)
    for k in range(4):                                                            # fins + fairings
        a = k * math.tau / 4
        d = Vector((math.cos(a), 0, math.sin(a))); s = Vector((-d.z, 0, d.x))
        pts = []
        for w in (-.45, .45):
            for p in ((6.8, -1.5), (12.0, -3.5), (12.0, 1.0), (6.8, 8.5)):
                pts.append(d * p[0] + Vector((0, B + p[1], 0)) + s * w)
        P.add(hull(pts), S('red', base=.55, up=.15, jit=0))
        P.add(at(lathe([(0, 0), (1.3, 1.4), (1.3, 6.0), (0, 8.4)], n=10), d * 7.6 + Vector((0, B - 2.4, 0))), S('panel', base=.6, jit=0), smooth=True)
    # interstage (foil), second stage, third stage, capsule, escape tower
    yI = B + 39.0
    P.add(at(cyl(6.6, 4.0, sides=24, r2=6.0), (0, yI, 0)), S('foil', base=.58, jit=.2, seed=9))
    P.add(at(lathe([(6.0, 0), (6.0, 15.0)], n=24), (0, yI + 4.0, 0)), S('panel', base=.58, up=.1, jit=.02), smooth=True)
    P.add(at(lathe([(6.05, 0), (6.05, 4.0)], n=24), (0, yI + 7.5, 0)), ShAng('panel', 'navy', 8, base=.56, jit=0), smooth=True)
    P.add(at(torus(6.08, .45, n=24, sides=6, y=yI + 18.6), (0, 0, 0)), S('orange', base=.6, jit=0), smooth=True)
    yC = yI + 19.0
    P.add(at(cyl(6.0, 3.0, sides=24, r2=4.6), (0, yC, 0)), S('foil', base=.55, jit=.18, seed=12))
    P.add(at(lathe([(4.6, 0), (4.6, 8.0)], n=24), (0, yC + 3.0, 0)), S('panel', base=.6, up=.1, jit=.02), smooth=True)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        P.add(at(box((1.0, 3.6, .6), .15), (math.cos(a) * 4.7, yC + 5.0, math.sin(a) * 4.7), (0, -math.degrees(a) - 90, 0)), S('steel', base=.4, jit=0))
    yK = yC + 11.0
    P.add(at(lathe([(4.7, 0), (4.4, .6), (1.6, 7.0), (1.2, 7.4), (0, 7.5)], n=24), (0, yK, 0)), S('panel', base=.6, up=.2, jit=.02), smooth=True)
    port(P, (0, yK + 3.0, -3.25), 0, .8, 'window', pitch=-23)
    for sx in (-1, 1): port(P, (sx * 2.25, yK + 3.0, -2.25), -sx * 45, .55, 'window', pitch=-23)
    for k in range(4):                                                            # escape tower lattice
        a = k * math.tau / 4 + math.pi / 4
        P.add(beam((math.cos(a) * 1.2, yK + 7.0, math.sin(a) * 1.2), (math.cos(a) * .5, yK + 13.0, math.sin(a) * .5), .16, 5), S('orange', base=.6, jit=0))
    for t in (.33, .66):
        P.add(at(torus(1.2 - .7 * t, .1, n=8, sides=4, y=yK + 7.0 + 6.0 * t), (0, 0, 0)), S('orange', base=.6, jit=0))
    P.add(at(lathe([(.7, 0), (.8, 2.4), (.3, 4.6), (0, 5.2)], n=10), (0, yK + 13.0, 0)), S('red', base=.6, jit=0), smooth=True)
    P.gadd(at(cyl(.3, .4, sides=8), (0, yK + 18.1, 0)), 'red')
    return P

def launch_tower(H=86.0):
    """umbilical tower beside the rocket (rocket axis at x = -14): 4-leg truss, X bracing, platforms with beacon tips,
    3 swing arms reaching to the rocket, crane hammerhead"""
    P = Prop('LaunchTower'); w = 3.4
    P.add(at(box((12.0, 1.4, 12.0), .3), (0, -.6, 0)), S('steel', base=.35, jit=0))
    C = [(-w, -w), (w, -w), (w, w), (-w, w)]
    for x, z in C:
        P.add(at(box((.8, H, .8), .12), (x, H / 2, z)), S('red', base=.5, up=.1, jit=0))
    lv = int(H / 8)
    for i in range(lv):
        y0, y1 = i * 8.0 + .6, (i + 1) * 8.0
        for j in range(4):
            (ax, az), (bx, bz) = C[j], C[(j + 1) % 4]
            P.add(beam((ax, y0, az), (bx, y1, bz), .2, 4), S('red', base=.45, jit=0))
            P.add(beam((ax, y1, az), (bx, y1, bz), .22, 4), S('red', base=.55, jit=0))
        if i % 2 == 1:
            P.add(at(box((2 * w + 3.0, .35, 2 * w + 3.0), .1), (0, y1, 0)), S('steel', base=.5, jit=0))
            for sx in (-1, 1):
                for sz in (-1, 1): P.gadd(at(cyl(.22, .3, sides=6), (sx * (w + 1.3), y1 + .35, sz * (w + 1.3))), 'beacon')
    for y, L in ((28.0, 10.0), (52.0, 11.0), (70.0, 11.5)):                       # swing arms toward -X
        P.add(at(box((L, 1.4, 2.6), .2), (-w - L / 2, y, 0)), S('panel', base=.55, jit=.02))
        for sz in (-1, 1): P.add(beam((-w, y + .7, sz * 1.3), (-w - L, y + 2.2, sz * 1.3), .1, 4), S('steel', base=.6, jit=0))
        P.add(beam((-w, y + 5.0, 0), (-w - L * .8, y + .7, 0), .18, 4), S('red', base=.5, jit=0))
        P.add(at(box((1.6, 2.4, 3.2), .25), (-w - L + .5, y - .5, 0)), S('orange', base=.55, jit=0))
    P.add(at(box(((2 * w + 2) * 1.0, 3.0, 2 * w + 2), .3), (0, H, 0)), S('panel', base=.5, jit=.02))   # hammerhead crane
    P.add(at(box((22.0, 1.4, 1.8), .2), (2.0, H + 3.0, 0)), S('red', base=.5, jit=0))
    P.add(beam((12.0, H + 3.0, 0), (12.0, H - 6.0, 0), .06, 4), S('steel', base=.4, jit=0))
    P.add(at(box((1.4, 1.0, 1.4), .2), (12.0, H - 7.0, 0)), S('orange', base=.55, jit=0))
    P.add(beam((0, H + 4.4, 0), (0, H + 11.0, 0), .2, 5), S('steel', base=.6, jit=0))
    P.gadd(at(lathe([(0, 0), (.5, .2), (.5, .8), (0, 1.0)], n=8), (0, H + 11.0, 0)), 'red')
    return P

# ------------------------------------------------------------------ zone gate (airlock arch), jump pad
def airlock_gate(zone=1, w=22.0, h=18.0):
    """priced zone gate at the head of each crater ramp: two hex pylons with chevron stripes, lintel with a round
    zone porthole, laser bars (thin) across the opening, chevron floor plate. Opening along X, walk through along Z."""
    P = Prop('Airlock_z%d' % zone); g = 'z%d' % zone
    for sx in (-1, 1):
        x = sx * (w / 2 + 2.4)
        P.add(at(cyl(3.6, 1.6, sides=6, bev=.3, rot0=math.pi / 6), (x, -.8, 0)), S('steel', base=.35, jit=0))
        P.add(at(cyl(2.4, h + 1.0, sides=6, bev=.3, r2=2.0, rot0=math.pi / 6), (x, .6, 0)), S('panel', base=.55, up=.2, jit=.03))
        for y in range(2, int(h) - 1, 3):                                         # chevron stripes on the inner face
            P.add(at(box((.2, 1.0, 1.9), .05), (x - sx * (2.06 - .02 * y), y + .5, 0), (0, 0, sx * 4)), S('orange' if (y // 3) % 2 else 'navy', base=.6, jit=0))
        P.gadd(at(box((.25, h - 3.0, .3)), (x - sx * 1.95, 1.0 + (h - 3.0) / 2, -1.25)), g)
        P.gadd(at(box((.25, h - 3.0, .3)), (x - sx * 1.95, 1.0 + (h - 3.0) / 2, 1.25)), g)
        P.add(at(cyl(2.6, .8, sides=6, bev=.2), (x, h + 1.6, 0)), S('steel', base=.45, jit=0))
        beacon_post(P, x, h + 2.4, 0, h=1.6, key=g)
    P.add(at(box((w + 9.6, 4.4, 4.4), .5), (0, h - .6, 0)), S('panel', base=.58, up=.2, jit=.02))
    P.add(at(box((w + 10.0, .6, 4.8), .2), (0, h - 1.0, 0)), S('steel', base=.4, jit=0))
    P.add(at(box((w + 10.0, .6, 4.8), .2), (0, h + 1.75, 0)), S('orange', base=.6, jit=0))
    for sz in (-1, 1):
        P.add(at(torus(1.75, .3, n=20, sides=6), (0, h - .6, sz * 2.3), (90, 0, 0)), S('steel', base=.45, jit=0), smooth=True)
        P.gadd(at(cyl(1.5, .2, sides=20), (0, h - .6, sz * 2.3 - .1), (90, 0, 0)), g)
    for y in (3.0, 7.0, 11.0):                                                    # laser bars (thin, not a wall)
        P.gadd(at(cyl(.12, w + .4, sides=6), (-(w + .4) / 2, y, 0), (0, 0, -90)), g)
    P.add(at(box((w + 2.0, .4, 9.0), .15), (0, -.1, 0)), S('steel', base=.4, jit=0))
    for k in range(-2, 3):
        for sg in (-1, 1):
            P.add(at(at(box((.5, .1, 2.6), .03), (sg * .7, 0, 0), (0, sg * 40, 0)), (k * 4.0, .14, 0), (0, 0, 0)), S('orange', base=.6, jit=0))
    return P

def jump_pad(key='cyan'):
    """low-gravity launcher: vented steel skirt, white deck, 3 glow rings + up-chevron glow plates"""
    P = Prop('JumpPad_%s' % key)
    P.add(at(cyl(5.0, 1.0, sides=12, bev=.25, r2=4.6), (0, -.4, 0)), S('steel', base=.4, jit=0))
    for k in range(12):
        a = (k + .5) * math.tau / 12
        P.add(at(box((1.0, .5, .2), .05), (math.cos(a) * 4.82, .1, math.sin(a) * 4.82), (0, -math.degrees(a) - 90, 0)), S('char', base=.4, jit=0))
    P.add(at(cyl(4.4, .4, sides=24, bev=.1), (0, .6, 0)), S('panel', base=.6, jit=0), smooth=True)
    for r in (1.2, 2.4, 3.6):
        P.gadd(at(torus(r, .14, n=24, sides=4, y=1.02), (0, 0, 0)), key)
    P.gadd(at(cyl(.7, .1, sides=12), (0, 1.0, 0)), key)
    return P

# ------------------------------------------------------------------ geology
def moon_rock(seed, r=3.0, col='regB', pit=True):
    """faceted boulder sunk into a regolith skirt, with a small chipped pit; 2 satellite pebbles"""
    P = Prop('MoonRock%d_%s' % (seed, col)); rng = random.Random(seed)
    P.add(at(rock((r, r * .72, r * .9), seed=seed, n=34), (0, r * .32, 0)), S(col, base=.42, up=.32, jit=.08, seed=seed))
    P.add(at(hull(rock_pts((r * 1.35, r * .22, r * 1.25), n=20, seed=seed + 5, flat=.0)), (0, 0, 0)), S('regA' if col != 'mare' else 'regB', base=.45, up=.25, jit=.05, seed=seed))
    for k in range(2):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(1.25, 1.6)
        P.add(at(rock((r * .25, r * .2, r * .22), seed=seed + 11 + k, n=14), (math.cos(a) * d, r * .05, math.sin(a) * d)), S(col, base=.45, up=.3, jit=.08))
    return P

def rock(r, seed, n=30):
    return hull(rock_pts(r, n=n, seed=seed, flat=.55))

def meteorite(seed=1, r=3.2):
    """split meteorite: two dark halves around a glowing molten core, in a raised impact ring with ejecta"""
    P = Prop('Meteorite%d' % seed); rng = random.Random(seed)
    for sx in (-1, 1):
        pts = [p for p in rock_pts((r, r * .85, r), n=40, seed=seed + (sx > 0) * 9, flat=.4) if p.x * sx > -.2]
        pts = [Vector((p.x if p.x * sx > 0 else sx * .25, p.y, p.z)) for p in pts]
        P.add(at(hull(pts), (sx * .7, r * .55, 0), (0, 0, sx * 8)), S('mare', base=.35, up=.3, jit=.12, seed=seed + sx))
    P.gadd(at(blob(r * .62, seed + 3, n=24, sq=.95), (0, r * .65, 0)), 'meteor')
    ring = [Vector((math.cos(a) * r * 2.4, 0, math.sin(a) * r * 2.4)) for a in [k * math.tau / 20 for k in range(21)]]
    P.add(tube(ring, r * .45, sides=6, cap0=False, cap1=False, rough=.25, seed=seed, flat=(1.0, .45)), S('regB', base=.5, up=.3, jit=.06))
    for k in range(5):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(2.8, 3.6)
        P.add(at(rock((r * .3, r * .2, r * .26), seed=seed + 20 + k, n=12), (math.cos(a) * d, 0, math.sin(a) * d)), S('rust' if k % 2 else 'mare', base=.4, up=.3, jit=.1))
    return P

def ice_crystal(seed=1, s=1.0):
    """ice cluster: 5-7 hex spikes leaning out from a frost-crusted rock, glowing cores in the tallest"""
    P = Prop('IceCrystal%d' % seed); rng = random.Random(seed)
    P.add(at(rock((3.2 * s, 1.6 * s, 3.0 * s), seed=seed, n=26), (0, .4 * s, 0)), S('mare', base=.35, up=.3, jit=.08, top='frost', thr=.55, topbase=.6))
    n = rng.randint(5, 7)
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-.3, .3); lean = rng.uniform(8, 28) if k else 4
        h = (rng.uniform(4.0, 7.0) if k else 10.0) * s; r = (rng.uniform(.6, 1.0) if k else 1.4) * s
        d = 0 if k == 0 else rng.uniform(.8, 1.6) * s
        rot = (lean * math.cos(a), 0, -lean * math.sin(a))
        P.add(at(spike(r, h, sides=6, shoulder=.74), (math.cos(a) * d, .2 * s, math.sin(a) * d), rot), S('ice', grad=(0, h, .3, .9), up=.1))
        if k < 2: P.gadd(at(spike(r * .45, h * .7, sides=6, shoulder=.7), (math.cos(a) * d, .6 * s, math.sin(a) * d), rot), 'ice')
    return P

# ------------------------------------------------------------------ junk + set dressing
def wheel(P, c, R=1.6, w=.8, axis='x'):
    rot = (0, 0, 90) if axis == 'x' else (90, 0, 0)
    P.add(at(torus(R, w * .45, n=16, sides=6), c, rot), S('steel', base=.35, jit=0), smooth=True)
    for k in range(6):
        a = k * math.tau / 6
        P.add(at(beam((0, 0, 0), (0, math.cos(a) * R * .9, math.sin(a) * R * .9), .08, 4), c), S('panel', base=.6, jit=0))
    P.add(at(cyl(.4, w, sides=8), (c[0] - w / 2, c[1], c[2]), (0, 0, -90)), S('foil', base=.6, jit=0))

def moon_rover():
    """abandoned lunar rover: tube chassis, 4 wire wheels with fenders, 2 seats, console, dish + camera mast"""
    P = Prop('MoonRover'); y = 1.9
    for sz in (-1, 1): P.add(beam((-1.8, y, sz * 4.2), (1.8, y, sz * 4.2), .18, 6), S('steel', base=.5, jit=0))
    for sx in (-1, 1): P.add(beam((sx * 1.8, y, -4.4), (sx * 1.8, y, 4.4), .2, 6), S('steel', base=.5, jit=0))
    P.add(at(box((3.8, .3, 8.0), .1), (0, y + .1, 0)), S('foil', base=.55, jit=.15))
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = (sx * 2.8, 1.6, sz * 3.2); wheel(P, c)
            P.add(at(torus(1.95, .12, n=10, sides=4, a0=math.radians(20), a1=math.radians(160)), (sx * 2.8, 1.6, sz * 3.2), (0, 0, 90)), S('panel', base=.6, jit=0))
            P.add(at(box((.9, .2, 3.6), .05), (sx * 2.8, 3.55, sz * 3.2)), S('orange', base=.55, jit=0))
    for sz in (.2, 2.2):                                                          # seats (frame + sling)
        P.add(at(box((2.8, .3, 1.6), .1), (0, y + .5, sz)), S('navy', base=.4, jit=0))
        P.add(at(box((2.8, 1.8, .3), .1), (0, y + .6, sz + .9), (-12, 0, 0)), S('navy', base=.45, jit=0))
    P.add(at(box((2.4, 1.6, .8), .15), (0, y + .4, -2.0), (-20, 0, 0)), S('panel', base=.55, jit=0))
    P.gadd(at(box((1.6, .5, .1)), (0, y + 1.2, -2.42), (-20, 0, 0)), 'cyan')
    P.add(beam((0, y + 1.2, -2.4), (0, y + 4.6, -3.0), .1, 5), S('steel', base=.55, jit=0))
    P.add(at(dish(1.6, .6, n=14), (0, y + 4.4, -3.0), (-50, 20, 0)), S('panel', base=.6, jit=0), smooth=True)
    P.add(beam((1.0, y + .6, -3.2), (1.0, y + 3.0, -3.6), .08, 4), S('steel', base=.55, jit=0))
    P.add(at(box((.8, .6, .9), .1), (1.0, y + 3.1, -3.6)), S('steel', base=.35, jit=0))
    P.add(at(box((3.0, 1.0, 1.2), .15), (0, y + .3, 3.8)), S('panel', base=.55, jit=.05))    # tool pallet
    return P

def satellite_wreck(seed=1):
    """crashed satellite half-buried: foil bus, one bent solar wing (cells + frame), tipped dish, snapped booms"""
    P = Prop('SatWreck%d' % seed); rng = random.Random(seed)
    P.add(at(box((5.0, 4.0, 5.0), .4), (0, .6, 0), (12, 20, 8)), S('foil', base=.55, jit=.2, seed=seed))
    P.add(at(box((5.3, .5, 5.3), .15), (0, 4.4, 0), (12, 20, 8)), S('steel', base=.4, jit=0))
    for j in range(3):                                                            # bent wing: 3 panels kinking down
        x = 4.0 + j * 4.2; ang = -6 - j * 14
        P.add(at(box((4.0, .3, 3.4), .08), (x, 3.0 - j * 1.2, .4), (0, 20, ang)), S('navy', base=.4, up=.25, jit=.06, seed=j))
        for sz in (-1, 1):
            P.add(at(at(box((4.1, .36, .25), .05), (0, 0, sz * 1.6)), (x, 3.0 - j * 1.2, .4), (0, 20, ang)), S('steel', base=.55, jit=0))
        P.add(at(at(box((.2, .38, 3.3), .05), (0, 0, 0)), (x, 3.0 - j * 1.2, .4), (0, 20, ang)), S('steel', base=.5, jit=0))
    P.add(at(dish(2.6, 1.0, n=18), (-3.0, 3.0, -2.6), (-70, 40, 20)), S('panel', base=.6, jit=0), smooth=True)
    P.add(beam((-1.0, 3.0, -1.0), (-6.0, 5.6, 3.0), .14, 5), S('steel', base=.5, jit=0))
    P.gadd(at(cyl(.25, .3, sides=6), (-6.0, 5.6, 3.0)), 'red')
    P.add(hull(rock_pts((8.0, 1.4, 7.0), n=24, seed=seed + 3, flat=0)), S('regB', base=.45, up=.3, jit=.06))   # dirt mound it ploughed
    return P

def fuel_tanks():
    """3 horizontal tanks on cradles (2 bottom, 1 on top), orange end caps, pipe manifold"""
    P = Prop('FuelTanks')
    for (x, y), col in zip(((-2.6, 2.6), (2.6, 2.6), (0, 7.0)), ('panel', 'panel', 'foil')):
        P.add(at(lathe([(0, -6.0), (1.6, -5.9), (2.4, -5.0), (2.5, -4.6), (2.5, 4.6), (2.4, 5.0), (1.6, 5.9), (0, 6.0)], n=16), (x, y, 0), (90, 0, 0)), S(col, base=.55, up=.2, jit=.02), smooth=True)
        for z in (-4.8, 4.8): P.add(at(torus(2.52, .3, n=16, sides=5), (x, y, z), (90, 0, 0)), S('orange', base=.6, jit=0), smooth=True)
    for z in (-3.0, 3.0):
        P.add(at(box((10.0, 1.6, 1.4), .2), (0, -.2, z)), S('steel', base=.4, jit=0))
        P.add(at(box((4.6, 1.2, 1.2), .2), (0, 4.5, z)), S('steel', base=.45, jit=0))
    P.add(tube([Vector((-2.6, 5.0, 5.6)), Vector((-2.6, 6.4, 6.4)), Vector((0, 7.0, 6.6)), Vector((2.6, 6.4, 6.4)), Vector((2.6, 5.0, 5.6))], .3, sides=6), S('steel', base=.5, jit=0), smooth=True)
    P.add(at(cyl(.6, .8, sides=8), (0, 7.0, 6.3), (90, 0, 0)), S('red', base=.55, jit=0))
    return P

def floodlight():
    """hub floodlight mast: tripod foot, tapered pole, ring catwalk, 4-lamp head, red top beacon"""
    P = Prop('FloodLight')
    for k in range(3):
        a = k * math.tau / 3
        P.add(beam((math.cos(a) * 3.0, .1, math.sin(a) * 3.0), (0, 5.0, 0), .3, 6), S('steel', base=.45, jit=0))
        P.add(at(cyl(.8, .4, sides=8), (math.cos(a) * 3.0, -.2, math.sin(a) * 3.0)), S('steel', base=.35, jit=0))
    P.add(at(cyl(.7, 20.0, sides=8, r2=.45, bev=.1), (0, 1.0, 0)), S('panel', base=.58, up=.1, jit=.02))
    for y in (6.0, 12.0): P.add(at(torus(.62, .15, n=10, sides=4, y=y), (0, 0, 0)), S('orange', base=.6, jit=0))
    P.add(at(cyl(2.2, .3, sides=12), (0, 17.8, 0)), S('steel', base=.45, jit=0))
    P.add(at(torus(2.2, .08, n=16, sides=4, y=18.8), (0, 0, 0)), S('steel', base=.6, jit=0))
    P.add(at(box((4.4, .6, .6), .1), (0, 21.0, 0)), S('steel', base=.4, jit=0))
    for sx in (-1.6, -.55, .55, 1.6):
        P.add(at(box((.95, 1.0, .9), .15), (sx, 21.6, -.2), (20, 0, 0)), S('panel', base=.6, jit=0))
        P.gadd(at(box((.7, .7, .1)), (sx, 21.95, -.68), (20, 0, 0)), 'window')
    P.gadd(at(lathe([(0, 0), (.3, .05), (.3, .4), (0, .55)], n=8), (0, 22.5, .3)), 'red')
    return P

def comms_dish():
    """hub antenna: big dish on a yoke, turret drum, foil base, feed horn on 3 struts"""
    P = Prop('CommsDish')
    P.add(at(cyl(4.0, 1.4, sides=8, bev=.3, rot0=math.pi / 8), (0, -.4, 0)), S('foil', base=.55, jit=.15))
    P.add(at(cyl(2.4, 4.2, sides=12, bev=.2, r2=2.0), (0, 1.0, 0)), S('panel', base=.55, jit=.02), smooth=True)
    P.add(at(torus(2.3, .2, n=16, sides=4, y=3.0), (0, 0, 0)), S('orange', base=.6, jit=0))
    for sx in (-1, 1): P.add(at(box((.6, 3.4, 1.4), .15), (sx * 2.0, 5.0, 0)), S('steel', base=.45, jit=0))
    P.add(at(cyl(.5, 4.4, sides=8), (-2.2, 7.4, 0), (0, 0, -90)), S('steel', base=.5, jit=0))
    P.add(at(dish(7.0, 2.8, n=24, t=.35), (0, 7.4, 0), (-55, 0, 0)), S('panel', base=.62, up=.15, jit=0), smooth=True)
    from mathutils import Matrix
    Rm = Matrix.Rotation(math.radians(-55), 3, 'X'); C0 = Vector((0, 7.4, 0))
    tip = C0 + Rm @ Vector((0, 6.0, 0)); d = Rm @ Vector((0, 1, 0))
    for k in range(3):
        a = k * math.tau / 3 + math.pi / 2
        rim = C0 + Rm @ Vector((math.cos(a) * 5.0, 2.8 * (5.0 / 7.0) ** 2 + .3, math.sin(a) * 5.0))
        P.add(beam(rim, tip, .1, 4), S('steel', base=.6, jit=0))
    P.add(at(cyl(.5, 1.2, sides=8), tip - d * .6), S('foil', base=.6, jit=0))
    P.gadd(at(cyl(.25, .3, sides=8), tip + d * .6), 'red')
    return P

def supply_crates(seed=1):
    """stack of 3 white supply crates with orange corner caps and foil straps + a cylindrical canister"""
    P = Prop('SupplyCrates%d' % seed); rng = random.Random(seed)
    spots = [((0, 0, 0), 0), ((3.3, 0, .4), 12), ((1.5, 2.6, .2), -8)]
    for k, ((x, y, z), yaw) in enumerate(spots):
        P.add(at(box((3.0, 2.6, 3.0), .25), (x, y, z), (0, yaw, 0)), S('panel', base=.55, up=.25, jit=.04, seed=k))
        P.add(at(box((3.1, .35, 3.1), .08), (x, y + 1.15, z), (0, yaw, 0)), S('orange', base=.6, jit=0))
        P.add(at(box((.5, 2.7, 3.1), .05), (x, y - .05, z), (0, yaw, 0)), S('foil', base=.6, jit=0))
    P.add(at(cyl(1.1, 3.2, sides=12, bev=.15), (-2.6, 0, 1.0)), S('steel', base=.5, jit=0), smooth=True)
    P.add(at(torus(1.12, .12, n=12, sides=4, y=2.2), (-2.6, 0, 1.0)), S('orange', base=.6, jit=0))
    return P

# ------------------------------------------------------------------ mess (cleanable)
def crater(seed=1, col='regB', vg=.62):
    """modelled impact crater for R = 1 (place with s = R): smooth 36-sided lathe, raised rim crest, bowl to a dark
    floor, skirt that feathers into the ground tone (vg); shade per vertex so tones blend, + a few ejecta rocks.
    Origin = bowl floor; the map carves a shallow flat dish (0.12 R) under it so the floor never floats."""
    P = Prop('Crater%d_%s' % (seed, col)); rng = random.Random(seed)
    prof = [(1.75, .02), (1.5, .11), (1.3, .2), (1.15, .27), (1.04, .31), (.96, .29), (.86, .21), (.72, .11),
            (.55, .05), (.32, .025), (0, .02)]
    bm = lathe(prof, n=36, a0=rng.uniform(0, 1))
    for v in bm.verts:                                                            # slightly irregular rim
        r = math.hypot(v.co.x, v.co.z)
        if r > .5:
            a = math.atan2(v.co.z, v.co.x); w = math.exp(-((r - 1.04) / .35) ** 2)
            v.co.y += w * .05 * (math.sin(3 * a + seed) + .6 * math.sin(5 * a + 2 * seed))
    u = PAL.u(col)
    def tone(f):                                                                  # ground tone; only a hint of rim / floor
        out = []
        for l in f.loops:
            r = math.hypot(l.vert.co.x, l.vert.co.z)
            v = vg - .03 * (1 - smooth(r / .9)) + .02 * math.exp(-((r - 1.04) / .2) ** 2)
            out.append((u, clamp(v, .04, .96)))
        return out
    P.add(bm, tone, smooth=True)
    for k in range(rng.randint(3, 5)):                                            # ejecta on the skirt
        a = rng.uniform(0, math.tau); d = rng.uniform(1.2, 1.6); rr = rng.uniform(.06, .11)
        P.add(at(rock((rr, rr * .7, rr * .85), seed=seed * 7 + k, n=12), (math.cos(a) * d, .14 - (d - 1.2) * .3, math.sin(a) * d)),
              S(col, base=vg - .03, up=.08, jit=.03, seed=seed + k))
    return P

def dust_patch(seed=1, r=6.0, col='regA'):
    """sweepable dust drift: low lumpy pancake, lighter than the ground, rippled rings + 3 pebbles"""
    P = Prop('DustPatch%d_%s' % (seed, col)); rng = random.Random(seed)
    n = 20; prof = []
    bm = bmesh.new(); rings = []
    for j, (t, h) in enumerate(((1.0, -.25), (.8, .18), (.55, .42), (.3, .58))):
        ring = []
        for k in range(n):
            a = k * math.tau / n
            rr = r * t * (1 + .22 * math.sin(3 * a + seed) + .12 * math.sin(7 * a + seed * 2.3))
            ring.append(bm.verts.new((math.cos(a) * rr, h + (nz(math.cos(a) * rr, 0, math.sin(a) * rr, 3, seed) - .5) * .25, math.sin(a) * rr)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        for k in range(n): bm.faces.new((A[k], A[(k + 1) % n], B[(k + 1) % n], B[k]))
    bm.faces.new(rings[-1]); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        if f.normal.y < 0: f.normal_flip()
    P.add(bm, S(col, base=.66, up=.2, jit=.06, seed=seed))
    for k in range(3):
        a = rng.uniform(0, math.tau); d = r * rng.uniform(.3, .7)
        P.add(at(rock((.5, .35, .45), seed=seed * 5 + k, n=10), (math.cos(a) * d, .35, math.sin(a) * d)), S('regB', base=.45, up=.3, jit=.1))
    return P

def dust_pile(seed=1, col='regA'):
    """sweepable heap: stacked mounds + a sparkle of dust-gem bits (glow)"""
    P = Prop('DustPile%d_%s' % (seed, col)); rng = random.Random(seed)
    for k in range(3):
        a = k * 2.1 + seed; d = 0 if k == 0 else 1.6
        P.add(at(hull(rock_pts((2.4 - k * .4, 1.4 - k * .25, 2.2 - k * .4), n=22, seed=seed + k, flat=.2)), (math.cos(a) * d, 0, math.sin(a) * d)), S(col, base=.6, up=.3, jit=.07, seed=k))
    for k in range(4):
        a = rng.uniform(0, math.tau)
        P.gadd(at(spike(.22, .7, sides=4, shoulder=.5), (math.cos(a) * 1.4, rng.uniform(.6, 1.2), math.sin(a) * 1.4), (rng.uniform(-30, 30), 0, rng.uniform(-30, 30))), 'cyan')
    return P

def junk_heap(seed=1):
    """space junk to haul: bent hull panel, snapped pipe, gear, bolts, broken box - built of small parts"""
    P = Prop('JunkHeap%d' % seed); rng = random.Random(seed)
    P.add(at(box((3.6, .25, 2.4), .08), (0, .5, 0), (0, rng.uniform(0, 90), 18)), S('panel', base=.5, up=.3, jit=.1, seed=seed))
    P.add(at(box((2.4, .25, 1.8), .08), (.8, .9, .6), (25, rng.uniform(0, 90), -30)), S('rust', base=.5, up=.3, jit=.1))
    P.add(tube([Vector((-1.8, .3, -1.0)), Vector((-.4, .5, -1.4)), Vector((1.2, 1.1, -1.6))], .32, sides=8), S('steel', base=.45, jit=0), smooth=True)
    g = cyl(1.0, .35, sides=12)                                                   # gear
    P.add(at(g, (-1.2, .4, .9), (70, 30, 0)), S('foil', base=.55, jit=0))
    for k in range(6):
        a = k * math.tau / 6
        P.add(at(box((.4, .35, .3)), (-1.2 + math.cos(a) * 1.05, .4 + math.sin(a) * 1.0 * .34, .9 + math.sin(a) * .94), (70, 30, 0)), S('foil', base=.5, jit=0))
    P.add(at(box((1.3, 1.1, 1.3), .15), (1.6, .2, -.2), (8, 40, 14)), S('orange', base=.5, jit=.05))
    for k in range(5):
        a = rng.uniform(0, math.tau); d = rng.uniform(1.6, 2.6)
        P.add(at(cyl(.18, .6, sides=6), (math.cos(a) * d, .1, math.sin(a) * d), (90, rng.uniform(0, 180), 0)), S('steel', base=.6, jit=0))
    P.add(hull(rock_pts((3.2, .4, 2.8), n=16, seed=seed + 7, flat=0)), S('regB', base=.5, up=.3, jit=.05))
    return P

def meteor_chunk(seed=1):
    """small glowing meteor fragment to collect: dark shell with molten seams, scorch disc"""
    P = Prop('MeteorChunk%d' % seed)
    P.add(at(rock((1.4, 1.1, 1.3), seed=seed, n=20), (0, .5, 0)), S('mare', base=.35, up=.35, jit=.12, seed=seed))
    P.gadd(at(blob(.75, seed + 4, n=14, sq=.9), (.45, .9, -.35)), 'meteor')
    P.gadd(at(blob(.55, seed + 6, n=12, sq=.9), (-.5, .6, .45)), 'meteor')
    P.add(at(cyl(2.6, .12, sides=12, r2=2.2), (0, 0, 0)), S('char', base=.35, jit=.08))
    return P

def ice_shards(seed=1):
    """collectable ice: 3 short glowing shards on a frost puddle"""
    P = Prop('IceShards%d' % seed); rng = random.Random(seed)
    P.add(at(cyl(2.2, .14, sides=10, r2=1.9), (0, 0, 0)), S('frost', base=.6, jit=.06))
    for k in range(3):
        a = k * 2.2 + seed; d = .7
        P.add(at(spike(.45, rng.uniform(1.6, 2.6), sides=6), (math.cos(a) * d, .1, math.sin(a) * d), (rng.uniform(-25, 25), 0, rng.uniform(-25, 25))), S('ice', grad=(0, 2.4, .35, .9)))
        P.gadd(at(spike(.2, 1.2, sides=6), (math.cos(a) * d, .2, math.sin(a) * d)), 'ice')
    return P

def earth():
    """Earth for the sky: faceted sphere, oceans / continents / cloud + polar caps by noise (faces), origin = centre"""
    P = Prop('Horizon_Earth')
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    def shade(f):
        c = f.calc_center_median()
        land = nz(c.x * 1.2, c.y * 1.2, c.z * 1.2, 1.0, 5)
        cloud = nz(c.x * 2.0, c.y * 4.0, c.z * 2.0, 1.0, 9)
        col, v = ('ocean', .5)
        if land > .56: col, v = ('land', .45 + (land - .56) * 2)
        if cloud > .66 or abs(c.y) > .88: col, v = ('frost', .75)
        u = PAL.u(col); return [(u, v)] * len(f.loops)
    P.add(bm, shade)
    return P
