# blender -b --factory-startup --python town_map.py [-- norender] [-- name.png ...] -> Maple Junction (town_map.blend)
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: CITY GRID town centre.
#   Street grid: Main Boulevard (E-W, z 70, 56 wide, planted median) + North Street (z -96) + West / East Avenues
#   (x -84 / 84). Town Square (x -68..68, z -80..42) with the fountain, lawns, the job board and the spawn; the clock-tower
#   Town Hall faces the square from the north; Bank (west) and Car Dealer (east) face it across the avenues; a shop row
#   lines the boulevard's south side with a back alley (dumpsters, fire escapes) behind it; the boulevard ends east at
#   the Train Station, platform canopies + a parked commuter train behind it. Skyline towers frame every edge.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import town_kit as K
F = K.G
from pro_lib import clean, KM, r2b, clamp, lerp, MB
sys.path.insert(0, os.path.join(HERE, '..', 'oaktrees'))
import gen_trees as GT                                     # realistic alpha-card trees (Trunk / Branches / Leaves)
TTEX = {'oak': 'oak_t', 'birch': 'birch_t'}                # leaf atlases re-graded for the sunny street

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean(); F.MATS.clear()
SC = bpy.context.scene
KITC = bpy.data.collections.new('Kit'); SC.collection.children.link(KITC)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

# ------------------------------------------------------------------ layout constants
CURB = .6
X0, X1, Z0, Z1 = -280.0, 400.0, -268.0, 256.0                 # ground extent
STREETS_EW = {'North': (-96.0, 32.0), 'Blvd': (70.0, 56.0)}     # z centre, width (curb to curb)
STREETS_NS = {'West': (-84.0, 32.0), 'East': (84.0, 32.0)}      # x centre, width
BLVD_X1 = 236.0                                                  # boulevard ends at the station forecourt
ST_X = 300.0; ST_Z = 70.0                                        # station centre (faces west)
TRACK_X = (350.0, 364.0)
SIDEW = 12.0

def road_at(x, z):
    for nm, (c, w) in STREETS_EW.items():
        if abs(z - c) < w / 2 and x < (BLVD_X1 if nm == 'Blvd' else 276.0): return True
    for c, w in STREETS_NS.values():
        if abs(x - c) < w / 2: return True
    return False

def blocks():
    """block rectangles (x0, x1, z0, z1) at curb height = everything that is not road"""
    xs = [X0, -100.0, -68.0, 68.0, 100.0, X1]
    zs = [Z0, -112.0, -80.0, 42.0, 98.0, Z1]
    out = []
    for i in range(0, 5, 2):
        for j in range(0, 5, 2):
            x0, x1, z0, z1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            if x0 == 100.0 and j == 0: x1 = 276.0
            if x0 == 100.0 and j == 4: x1 = 276.0
            if x0 == 100.0 and j == 2: x1 = X1
            out.append((x0, x1, z0, z1))
    out.append((BLVD_X1, X1, 42.0, 98.0))                        # station forecourt (boulevard end)
    out.append((276.0, X1, Z0, -112.0)); out.append((276.0, X1, -80.0 + 0, 42.0)) if False else None
    out.append((276.0, X1, -112.0, -80.0)); out.append((276.0, X1, 98.0, Z1))
    out.append((276.0, X1, Z0, -112.0))
    return out

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; STATIC_TRIS = {}
def kit(key, fn):
    if key not in LIB:
        if isinstance(fn, str):                                          # realistic tree species from gen_trees
            objs, tr, _ = GT.make_tree(fn, KITC, prefix='Tree', tex=TTEX)
            LIB[key] = ({o.name: o.data for o in objs}, tr['total'], None)
            return LIB[key][0]
        P = fn(); me = F.to_kit(P, KITC); LIB[key] = (me, P.tris, P)
    return LIB[key][0]
def place(key, fn, x, z, yaw=0.0, y=CURB, s=1.0, group='Props'):
    meshes = kit(key, fn)
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    return LIB[key][2]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def rot(p, yaw):
    """local (x, y, z) of a prop turned by yaw -> world offset"""
    a = math.radians(yaw); x, y, z = p
    return (x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a))
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = len(me.polygons); return ob

ANCHORS = []
def anchor(name, kind, group, x, y, z, yaw=0.0, size=(4, 1, 4), **attrs):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group, 'pos': [round(x, 2), round(y, 2), round(z, 2)],
                    'yaw': round(yaw % 360, 1), 'size': list(size), 'attrs': attrs})
def anchor_local(name, kind, group, base, yaw, local, size, ayaw=None, **attrs):
    o = rot(local, yaw)
    anchor(name, kind, group, base[0] + o[0], base[1] + o[1], base[2] + o[2], yaw if ayaw is None else ayaw, size, **attrs)

# ------------------------------------------------------------------ ground: asphalt, blocks, curbs, markings
def U(col): return K.PAL.u(col)
def flat(col, v): u = U(col); return lambda f: [(u, v)] * len(f.loops)

def ground():
    mb = MB()
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(p) for p in ((X0 - 40, 0, Z0 - 40), (X0 - 40, 0, Z1 + 40), (X1 + 40, 0, Z1 + 40), (X1 + 40, 0, Z0 - 40))])
    f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    mb.add(bm, flat('asph', .62)); static('Ground_Asphalt', mb, 'Ground')
    mb = MB()
    for (x0, x1, z0, z1) in blocks():
        mb.add(K.slab(x0, x1, -.2, CURB, z0, z1, drop=('-y',)), lambda f: [(U('pave'), .7 if f.normal.y > .5 else .3)] * len(f.loops))
    static('Ground_Blocks', mb, 'Ground')

def zebra(mb, cx, cz, along, length, width=10.0, n=None):
    """crosswalk stripes across a road: stripes run along `along` ('x' = stripes parallel to x), centred, spanning length"""
    n = n or int(length / 3.2)
    for k in range(n):
        t = -length / 2 + (k + .5) * length / n
        if along == 'z': bm = K.slab(cx + t - .8, cx + t + .8, 0, .04, cz - width / 2, cz + width / 2, drop=("-y",))
        else: bm = K.slab(cx - width / 2, cx + width / 2, 0, .04, cz + t - .8, cz + t + .8, drop=("-y",))
        mb.add(bm, flat('white', .5))

def markings():
    mb = MB(); my = MB()
    INT_X = [c for c, w in STREETS_NS.values()]; INT_Z = [c for c, w in STREETS_EW.values()]
    # crosswalks round each intersection
    for (xc, xw) in STREETS_NS.values():
        for (zc, zw) in STREETS_EW.values():
            zebra(mb, xc, zc - zw / 2 - 6, 'z', xw - 2)                  # across the N-S street, north leg
            zebra(mb, xc, zc + zw / 2 + 6, 'z', xw - 2)
            zebra(mb, xc - xw / 2 - 6, zc, 'x', zw - 2)
            zebra(mb, xc + xw / 2 + 6, zc, 'x', zw - 2)
            for sz in (-1, 1): mb.add(K.slab(xc - xw / 2 + 1, xc + xw / 2 - 1, 0, .04, zc + sz * (zw / 2 + 12) - .6, zc + sz * (zw / 2 + 12) + .6, drop=("-y",)), flat('white', .5))
    zebra(mb, 0, 70, 'x', 54); zebra(mb, 0, -96, 'x', 30)                  # mid-block crossings square -> shops / hall
    # lane lines
    def gaps(v, ints, half):
        return any(abs(v - c) < half for c in ints)
    for nm, (zc, zw) in STREETS_EW.items():
        xend = BLVD_X1 if nm == 'Blvd' else 276.0
        x = X0
        while x < xend - 4:
            if not gaps(x + 3, INT_X, 30) and abs(x + 3) > 8:
                if nm == 'Blvd':
                    for off in (-17.5, 17.5): mb.add(K.slab(x, x + 6, 0, .04, zc + off - .3, zc + off + .3, drop=("-y",)), flat('white', .5))
                else:
                    for off in (-.45, .45): my.add(K.slab(x, x + 8, 0, .04, zc + off - .2, zc + off + .2, drop=("-y",)), flat('yellow', .62))
            x += 8 if nm != 'Blvd' else 12
    for nm, (xc, xw) in STREETS_NS.items():
        z = Z0
        while z < Z1:
            if not gaps(z + 4, INT_Z, 44):
                for off in (-.45, .45): my.add(K.slab(xc + off - .2, xc + off + .2, 0, .04, z, z + 8, drop=("-y",)), flat('yellow', .62))
            z += 8
    # car-dealer lot + station taxi rank parking bays
    for k in range(7):
        x = 172 + k * 9; mb.add(K.slab(x - .25, x + .25, CURB, CURB + .04, 4, 22, drop=("-y",)), flat('white', .5))
    static('Road_Markings', mb, 'Ground'); static('Road_Lines', my, 'Ground')

def median():
    """boulevard median: raised planted strip with cream curb, breaks at the avenues and the square crossing"""
    mb = MB(); zc = 70.0
    segs = [(-220.0, -112.0), (-56.0, -8.0), (8.0, 56.0), (112.0, BLVD_X1 - 10)]
    for a, b in segs:
        mb.add(K.slab(a, b, 0, .9, zc - 5, zc + 5, drop=('-y',)), lambda f: [(U('cream'), .55 if f.normal.y < .5 else .7)] * len(f.loops))
        mb.add(K.slab(a + .7, b - .7, .9, 1.05, zc - 4.3, zc + 4.3), flat('grass', .55))
        MEDIAN.append((a, b))
    static('Median_Blvd', mb, 'Ground')
MEDIAN = []

def square():
    """Town Square: plaza paving rings round the fountain, 4 raised lawns with stone edging, axial walk"""
    mb = MB(); FX, FZ = 0.0, -20.0
    for r0, r1, col, v in ((20, 23, 'cream', .82), (31, 32.5, 'cream', .8)):
        n = 32; bm = bmesh.new()
        A = [bm.verts.new((FX + math.cos(k * math.tau / n) * r0, CURB + .03, FZ + math.sin(k * math.tau / n) * r0)) for k in range(n)]
        Bq = [bm.verts.new((FX + math.cos(k * math.tau / n) * r1, CURB + .03, FZ + math.sin(k * math.tau / n) * r1)) for k in range(n)]
        for k in range(n):
            j = (k + 1) % n; f = bm.faces.new((A[k], A[j], Bq[j], Bq[k])); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        mb.add(bm, flat(col, v))
    for sx in (-1, 1):                                                             # axial walk strips (cream bands)
        mb.add(K.slab(sx * 7 - .5, sx * 7 + .5, CURB, CURB + .03, -68, -44), flat('cream', .8))
        mb.add(K.slab(sx * 7 - .5, sx * 7 + .5, CURB, CURB + .03, 4, 30), flat('cream', .8))
    for (x0, x1, z0, z1) in LAWNS:
        mb.add(K.slab(x0, x1, CURB, CURB + .9, z0, z1, drop=('-y',)), lambda f: [(U('cream'), .62 if f.normal.y < .5 else .78)] * len(f.loops))
        mb.add(K.slab(x0 + .8, x1 - .8, CURB + .9, CURB + 1.05, z0 + .8, z1 - .8), flat('grass', .58))
    static('Square_Plaza', mb, 'Ground')
LAWNS = [(-56, -26, -66, -42), (26, 56, -66, -42), (-56, -24, 2, 28), (24, 56, 2, 28)]

def railway():
    """rail corridor: two tracks along Z behind the station + buffers"""
    for k in range(-10, 10):                          # k = 10 (z 310) would hang past the ground edge
        z = ST_Z + k * 24
        for tx in TRACK_X: place('TrackSeg', K.track_seg, tx, z, 0, y=CURB - .2, group='Rail')

# ------------------------------------------------------------------ buildings
BSPEC = {   # key: kwargs for K.building (sides none by default: they stand in rows)
    'B_ShopRed':    dict(w=30, d=30, floors=3, mat='brick', accent='red', quoins='cream', flowers=1, roof=('ac', 'tank')),
    'B_ShopTeal':   dict(w=34, d=30, floors=3, mat='cream', accent='teal', win='archtop', ground='wide', crown='pediment', roof=('shed', 'ac'), seed=2),
    'B_ShopYellow': dict(w=26, d=28, floors=5, mat='slate', accent='yellow', win='square', balconies=True, roof=('tank', 'antenna'), seed=3),
    'B_SageShop':   dict(w=26, d=28, floors=3, mat='sage', accent='yellow', shutters='blue', flowers=1, roof=('ac',), seed=4, door_side=-1),
    'B_SageHouse':  dict(w=24, d=26, floors=2, mat='sage', ground='door', accent='blue', shutters='blue', roof=('antenna',), seed=5),
    'B_BrickTall':  dict(w=28, d=30, floors=6, mat='brick', accent='blue', win='tall', crown='gable', roof=('tank', 'ac'), seed=6, trim='cream'),
    'B_CreamOffice': dict(w=40, d=34, floors=7, mat='cream', accent='teal', win='band', wfrac=.78, whf=.5, ground='wide', roof=('shed', 'ac', 'antenna'), seed=7, awning=False),
    'B_BrickCorner': dict(w=34, d=30, floors=4, mat='brick', accent='teal', win='arch', crown='gable', roof=('sky', 'ac'), seed=8, quoins='cream'),
    'B_SlateApt':   dict(w=30, d=28, floors=4, mat='slate', ground='door', accent='red', balconies=True, roof=('tank',), seed=9),
    'B_Cafe':       dict(w=28, d=26, floors=2, mat='cream', accent='red', flowers=1, roof=('ac',), seed=10, shutters='teal'),
    'B_Boutique':   dict(w=30, d=30, floors=3, mat='sage', accent='blue', win='archtop', roof=('ac', 'antenna'), seed=11, quoins='cream'),
    'B_BrickSmall': dict(w=22, d=26, floors=2, mat='brick', accent='yellow', roof=('ac',), seed=12, flowers=1),
}
def bkit(key, back='none', sides='none', lite=False):
    kk = key + ('F' if back == 'fire' else '') + ('W' if back == 'windows' else '') + ('S' if sides != 'none' else '') + ('L' if lite else '')
    kw = dict(BSPEC[key]); kw['sides'] = sides; kw['back'] = back; kw['lite'] = lite
    return kk, (lambda kk=kk, kw=kw: K.building(kk, **kw))

def row(keys, start, direction, front, group, back='none', gap=0.0, limit=None, lite=False):
    """lay buildings side by side from `start` (a point on the frontage line = back edge of the sidewalk) along
    `direction` (unit x/z), fronts facing `front`; returns list of (key, centre, yaw, prop)"""
    out = []; s = 0.0; dx, dz = direction; fx, fz = front
    yaw = face(0, 0, fx, fz)
    for i, key in enumerate(keys):
        w, d = BSPEC[key]['w'], BSPEC[key]['d']
        if limit and s + w > limit: break
        sides = 'windows' if BSPEC[key]['floors'] >= 5 else 'none'
        kk, fn = bkit(key, back, sides, lite)
        cx = start[0] + dx * (s + w / 2) - fx * d / 2; cz = start[1] + dz * (s + w / 2) - fz * d / 2
        P = place(kk, fn, cx, cz, yaw, group=group)
        reserve(cx, cz, max(w, d) * .5)
        hx, hz = (w / 2, d / 2) if abs(fx) < .5 else (d / 2, w / 2)
        RECTS.append((kk, cx - hx, cx + hx, cz - hz, cz + hz))
        out.append((kk, (cx, cz), yaw, P))
        s += w + gap
    return out

RECTS = []
def check_rects():
    bad = []
    for i, a in enumerate(RECTS):
        for b in RECTS[i + 1:]:
            ox = min(a[2], b[2]) - max(a[1], b[1]); oz = min(a[4], b[4]) - max(a[3], b[3])
            if ox > .5 and oz > .5: bad.append('%s x %s (%.1f x %.1f)' % (a[0], b[0], ox, oz))
    print('RECT_OVERLAPS', len(bad), bad[:20])

def sign_anchor(name, rec, group, **attrs):
    kk, (cx, cz), yaw, P = rec
    if P.sign is None: return
    (sx, sy, sz), (sw, sh) = P.sign
    anchor_local(name, 'sign', group, (cx, CURB, cz), yaw, (sx, sy, sz - .05), (sw, sh, .2), **attrs)

def buildings():
    S = {}
    # NW block: along North Street (fronts face +Z at z -124), from the West Avenue corner westward
    r = row(['B_BrickCorner', 'B_ShopRed', 'B_SageHouse', 'B_BrickTall'], (-112, -124), (-1, 0), (0, 1), 'NW')
    S['nw'] = r
    r = row(['B_SlateApt', 'B_SageShop', 'B_BrickSmall'], (-112, -156), (0, -1), (1, 0), 'NW', lite=True)
    # NE block: along North Street eastward
    r = row(['B_ShopTeal', 'B_SageHouse', 'B_BrickTall', 'B_Cafe', 'B_ShopRed'], (112, -124), (1, 0), (0, 1), 'NE')
    r = row(['B_ShopYellow', 'B_BrickSmall', 'B_SlateApt'], (112, -156), (0, -1), (-1, 0), 'NE', lite=True)
    # West block: Bank faces the square (east) in the middle of the West Avenue frontage
    S['bankrow2'] = row(['B_SageHouse'], (-112, 30), (0, -1), (1, 0), 'West')
    r = row(['B_CreamOffice', 'B_BrickCorner', 'B_ShopYellow'], (-140, 30), (-1, 0), (0, 1), 'West')
    S['blvd_n_w'] = r
    r = row(['B_BrickTall', 'B_SlateApt'], (-170, -68), (-1, 0), (0, -1), 'West', lite=True)
    # East block: fronts on North Street + boulevard behind the car dealer
    r = row(['B_BrickSmall', 'B_SageShop', 'B_CreamOffice', 'B_Cafe'], (160, -68), (1, 0), (0, -1), 'East', lite=True)   # ends at x 276: clear of the station row
    # South centre block: the SHOP ROW facing the boulevard (back alley behind, fire escapes)
    S['shops'] = row(['B_ShopRed', 'B_Cafe', 'B_ShopTeal', 'B_SageShop'], (-56, 110), (1, 0), (0, -1), 'ShopRow', back='fire', gap=1.3)
    S['south'] = row(['B_SlateApt', 'B_BrickTall', 'B_SageHouse', 'B_BrickSmall', 'B_BrickCorner'][:4], (-56, 184), (1, 0), (0, 1), 'AlleyBack', back='fire', gap=1.0) if False else \
        row(['B_SlateApt', 'B_BrickTall', 'B_SageHouse', 'B_ShopYellow'], (56, 228), (-1, 0), (0, 1), 'AlleyBack', back='fire', gap=1.0, lite=True)
    # SW + SE blocks along the boulevard south side
    S['sw'] = row(['B_Boutique', 'B_BrickCorner', 'B_SageHouse', 'B_ShopRed', 'B_CreamOffice'], (-112, 110), (-1, 0), (0, -1), 'SW')
    r = row(['B_BrickTall', 'B_SageShop', 'B_SlateApt'], (-112, 142), (0, 1), (1, 0), 'SW', lite=True)
    S['se'] = row(['B_Cafe', 'B_BrickSmall', 'B_ShopYellow', 'B_ShopTeal'], (112, 110), (1, 0), (0, -1), 'SE')
    r = row(['B_SageHouse', 'B_BrickTall', 'B_SlateApt'], (112, 140), (0, 1), (-1, 0), 'SE', lite=True)
    return S

# ------------------------------------------------------------------ landmarks + stations
TH_Z = -162.0
def landmarks(S):
    P = place('TownHall', K.town_hall, 0, TH_Z, 180, group='Hero')
    place('ClockTower', K.clock_tower, 0, TH_Z - 6, 180, y=CURB + K.TH_H, group='Hero')
    reserve(0, TH_Z, 62)
    d = rot(P.door, 180); anchor('TownHallDoor', 'door', 'Landmarks', d[0], CURB + d[1], TH_Z + d[2], 0, (9, 15, 2))
    # bank (west side, faces the square)
    bx, bz = -112 - 32, -28.0; yaw = face(bx, bz, 0, bz)
    P = place('Bank', K.bank, bx, bz, yaw, group='Stations'); reserve(bx, bz, 30)
    d = rot(P.door, yaw); anchor('Bank', 'station', 'Stations', bx + d[0], CURB + 3, bz + d[2], yaw, (8, 6, 4), Station='Bank')
    anchor('Bank_Prompt', 'prompt', 'Stations', bx + rot((0, 0, -19 - 14), yaw)[0], CURB + 1.5, bz, yaw, (6, 6, 6), Station='Bank')
    # car dealer (east side, faces the square) + display lot to its south-east
    cx, cz = 112 + 24, -19.0; yaw = face(cx, cz, 0, cz)
    P = place('CarShowroom', K.car_showroom, cx, cz, yaw, group='Stations'); reserve(cx, cz, 32)
    tt = rot(P.turntable, yaw); place('Car_sedan_red', lambda: K.car('sedan', 'red'), cx + tt[0], cz + tt[2], 35, y=CURB + 1.3, group='Stations')
    place('Car_hatch_yellow', lambda: K.car('hatch', 'yellow'), cx + rot((14, 0, 6), yaw)[0], cz + rot((14, 0, 6), yaw)[2], yaw + 20, y=CURB + .64, group='Stations')
    anchor('CarDealer', 'station', 'Stations', cx + tt[0], CURB + 1.3, cz + tt[2], yaw, (14, 4, 14), Station='CarDealer')
    sg = rot(P.sign, yaw); anchor('CarDealer_Sign', 'sign', 'Signs', cx + sg[0], CURB + sg[1], cz + sg[2], yaw, (40, 4, .2), Station='CarDealer')
    for k, (key, col) in enumerate((('sedan', 'blue'), ('van', 'cream'), ('hatch', 'teal'), ('sedan', 'cream'), ('hatch', 'red'), ('sedan', 'teal'))):
        x = 176.5 + k * 9
        place('Car_%s_%s' % (key, col), (lambda key=key, col=col: K.car(key, col)), x, 13, 180, group='CarLot')
    for x in (168, 236): place('StreetLamp', K.street_lamp, x, 26, 0, group='CarLot')
    # job board in the square (west lawn edge, faces the axis)
    jx, jz = -20.0, 12.0; yaw = face(jx, jz, 0, 12)
    P = place('JobBoard', K.job_board, jx, jz, yaw, group='Stations'); reserve(jx, jz, 7)
    b = rot(P.board, yaw); anchor('JobBoard', 'station', 'Stations', jx + b[0], CURB + b[1], jz + b[2], yaw, (9, 6.6, .3), Station='JobBoard')
    # shops: the shop row's red shop = general store, the SW boutique
    for name, rec, st in (('Shop', S['shops'][0], 'Shop'), ('Cafe', S['shops'][1], 'Cafe'), ('Boutique', S['sw'][0], 'Boutique')):
        kk, (cx, cz), yaw, P = rec
        sign_anchor(name + '_Sign', rec, 'Signs', Station=st)
        door = rot((P.w / 2 - 1.6 - 2.3 - .5, CURB, -P.d / 2 - 1.0), yaw) if True else None
        anchor(name, 'station', 'Stations', cx + door[0], CURB + 3, cz + door[2], yaw, (6, 6, 4), Station=st)
    k = 0
    for grp in ('shops', 'sw', 'se', 'blvd_n_w'):
        for rec in S[grp]:
            k += 1; sign_anchor('ShopSign%02d' % k, rec, 'Signs')
    # train station (faces west down the boulevard), platform canopies, the train
    yaw = face(ST_X, ST_Z, 0, ST_Z)
    P = place('TrainStation', K.train_station, ST_X, ST_Z, yaw, group='Hero'); reserve(ST_X, ST_Z, 50)
    anchor('TrainStation_Sign', 'sign', 'Signs', ST_X - 18 - .75, CURB + 21.7, ST_Z, yaw, (20.8, 1.8, .2), Station='TrainStation')
    px = ST_X + 18 + 13
    for k in range(-4, 5):
        place('PlatformCanopy', K.platform_canopy, px, ST_Z + k * 24, 0, group='Rail')
    for k, kind in enumerate(('loco', 'carriage', 'carriage')):
        place('Train_%s' % kind, (lambda kind=kind: K.train_car(kind)), TRACK_X[0], ST_Z - 40 + k * 47.4, 0, y=CURB + 1.0, group='Rail')
    anchor('TrainStation', 'station', 'Stations', px, CURB + 2.2, ST_Z, face(px, ST_Z, TRACK_X[0], ST_Z), (16, 6, 10), Station='TrainStation')
    anchor('TrainTravel', 'travel', 'Stations', px + 8, CURB + 2.2, ST_Z - 4, face(px, ST_Z, TRACK_X[0], ST_Z), (6, 8, 30), Station='TrainStation')
    anchor('TrainDoor', 'traindoor', 'Stations', TRACK_X[0] - 5, CURB + 6, ST_Z - 40 + 47.4 * .28 - 47.4 * 0, 90, (1, 8, 5))
    # station forecourt: planters, benches, lamps, trees round the taxi rank
    for z in (36, 104):
        for x in (244, 262):
            place('Planter2', lambda: K.planter(2), x, z, 0, group='Station')
    for x in (242, 270):
        place('StreetLamp', K.street_lamp, x, 30, 0, group='Station'); place('StreetLamp', K.street_lamp, x, 110, 0, group='Station')
    for z in (20, 120):
        place('Bench', K.bench, 254, z, 0 if z < 70 else 180, group='Station')
    # filler: lite buildings north + south of the station along the rail corridor, facing the forecourt
    row(['B_BrickTall', 'B_SlateApt', 'B_ShopYellow', 'B_BrickSmall'], (276, 12), (0, -1), (-1, 0), 'Station', lite=True)
    row(['B_SageShop', 'B_BrickCorner', 'B_SlateApt', 'B_BrickSmall'], (276, 128), (0, 1), (-1, 0), 'Station', lite=True)
    # fountain + spawn
    place('Fountain', K.fountain, 0, -20, 0, group='Square'); reserve(0, -20, 20)

SKY_SPOTS = [(-240, -232), (-170, -240), (-96, -258), (96, -258), (170, -240), (240, -232), (320, -236),
             (-248, -40) if False else (-262, -96), (-262, 60), (-248, 170), (-240, 240), (-150, 250), (-96, 254), (0, 256), (96, 252), (160, 250), (240, 240), (320, 230),
             (310, -160), (395, -120), (400, -20), (400, 70), (400, 160)]
def skyline_ring():
    sk = [('SkyA', 40, 36, 14, 'cream', 'bands', 'step'), ('SkyB', 34, 34, 11, 'brick', 'bands', 'flat'),
          ('SkyC', 30, 30, 13, 'slate', 'bands', 'roof'), ('SkyD', 44, 30, 9, 'sage', 'bands', 'flat'),
          ('SkyE', 36, 36, 13, 'cream', 'bands', 'step')]
    spots = SKY_SPOTS
    _unused = [(-240, -232), (-170, -236), (-96, -246), (-40, -244), (40, -244), (96, -246), (170, -236), (240, -232), (320, -236),
             (-248, -150), (-248, -40), (-250, 60), (-248, 170), (-240, 236), (-150, 240), (-96, 244), (0, 246), (96, 244), (160, 236), (240, 236), (320, 230),
             (310, -160), (395, -120), (400, -20), (400, 70), (400, 160)]
    rng = random.Random(5)
    for i, (x, z) in enumerate(spots):
        nm, w, d, fl, mat, st, cr = sk[i % len(sk)]
        place(nm, (lambda a=(nm, w, d, fl, mat, st, cr): K.skyline(*a, seed=i)), x, z, rng.choice((0, 90, 180, 270)), group='Skyline')

# ------------------------------------------------------------------ street dressing
def sidewalk_lines():
    """polylines (x, z, along-dir, out-dir) on the sidewalks at 3.5 studs from the curb"""
    L = []
    for nm, (zc, w) in STREETS_EW.items():
        xe = BLVD_X1 if nm == 'Blvd' else 276.0
        for s in (-1, 1): L.append(('ew', zc + s * (w / 2 + 3.5), -218.0, xe - 4, s))
    for nm, (xc, w) in STREETS_NS.items():
        for s in (-1, 1): L.append(('ns', xc + s * (w / 2 + 3.5), -212.0, 200.0, s))
    return L

def near_intersection(x, z, m=10):
    for xc, xw in STREETS_NS.values():
        for zc, zw in STREETS_EW.values():
            if abs(x - xc) < xw / 2 + 12 + m and abs(z - zc) < zw / 2 + 12 + m: return True
    return False

def dressing(rng):
    lines = sidewalk_lines()
    for kind, c, a, b, s in lines:
        t = a; k = 0
        while t < b:
            x, z = (t, c) if kind == 'ew' else (c, t)
            if near_intersection(x, z, 2) or not free(x, z, 3): t += 6; continue
            if k % 3 == 0:
                lamp_yaw = face(x, z, x, z + s) if kind == 'ew' else face(x, z, x + s, z)
                place('StreetLamp', K.street_lamp, x, z, lamp_yaw + 90, group='Street'); reserve(x, z, 3)
            elif k % 3 == 1:
                q = k // 3
                if q % 2 == 0:                                           # realistic trees cost ~2-3k: every other slot
                    place('StreetGrate', K.street_grate, x, z, rng.uniform(0, 4) * 90, group='Street')
                    sp = 'StreetBirch' if q % 4 else 'StreetOak'
                    place('r' + sp, sp, x, z, rng.uniform(0, 360), s=rng.uniform(.82, .9) if sp == 'StreetOak' else rng.uniform(.95, 1.05), group='Street')   # crown clears the facades
                reserve(x, z, 6)
            # small furniture between: bench / bin / hydrant facing the street
            m = t + 15
            xm, zm = (m, c) if kind == 'ew' else (c, m)
            if m < b and not near_intersection(xm, zm, 2) and free(xm, zm, 4):
                to = (xm, zm + s * 5) if kind == 'ew' else (xm + s * 5, zm)
                yaw = face(xm, zm, *to) + 180
                r = rng.random()
                if r < .3: place('Bench', K.bench, xm, zm, yaw, group='Street'); reserve(xm, zm, 4)
                elif r < .5: place('Bin', K.litter_bin, xm, zm, 0, group='Street'); reserve(xm, zm, 2)
                elif r < .65: place('Hydrant', K.hydrant, xm, zm, rng.uniform(0, 360), group='Street'); reserve(xm, zm, 2)
                elif r < .8: place('Planter%d' % (k % 2 + 1), (lambda q=k % 2 + 1: K.planter(q)), xm, zm, 0, group='Street'); reserve(xm, zm, 4)
            t += 36; k += 1
    # boulevard median trees + lamps
    for a, b in MEDIAN:
        t = a + 10; k = 0
        while t < b - 6:
            if t > 130:                                                     # keep the station vista open: sparse lamps only
                if k % 3 == 0: place('StreetLamp', K.street_lamp, t, 70, 0, y=1.05, group='Median')
            elif k % 2: place('StreetLamp', K.street_lamp, t, 70, 0, y=1.05, group='Median')
            else: place('rStreetBirch', 'StreetBirch', t, 70, rng.uniform(0, 360), y=1.0, s=1.1, group='Median')
            t += 18; k += 1
    # traffic lights: 2 per intersection on opposite corners, arms over the E-W roads
    for xc, xw in STREETS_NS.values():
        for zc, zw in STREETS_EW.values():
            for sx, sz in ((1, -1), (-1, 1)):
                x = xc + sx * (xw / 2 + 2.5); z = zc + sz * (zw / 2 + 2.5)
                front = (-sz, 0)
                place('TrafficLight_%s' % ('red' if sx > 0 else 'green'), (lambda l=('red' if sx > 0 else 'green'): K.traffic_light(1, l)),
                      x, z, face(x, z, x + front[0], z), group='Signals')
                reserve(x, z, 3)

def square_dressing(rng):
    for (x0, x1, z0, z1) in LAWNS:
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        for k, (dx, dz) in enumerate(((-.25, -.2), (.25, .25))):
            x = cx + dx * (x1 - x0); z = cz + dz * (z1 - z0)
            if abs(x) < 34 and z > 0: continue
            if k == 0: place('rStreetOak', 'StreetOak', x, z, rng.uniform(0, 360), y=CURB + 1.0, s=1.3, group='Square')   # park: one big oak per lawn
        place('FlowerBed1', K.flower_bed, cx, (z0 if cz < -20 else z1) + (-2.6 if cz < -20 else 2.6), 0, group='Square')
    # ring of benches + lamps round the fountain plaza, planters on the axis
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8; r = 27.0
        x, z = math.cos(a) * r, -20 + math.sin(a) * r
        if k % 2 == 0: place('StreetLamp', K.street_lamp, x, z, 0, group='Square'); reserve(x, z, 2)
        else: place('Bench', K.bench, x, z, face(x, z, 0, -20) + 180, group='Square'); reserve(x, z, 3)
    for x in (-12, 12):
        for z in (-62, 24):
            place('Planter1', lambda: K.planter(1), x, z, 0, group='Square'); reserve(x, z, 4)
    for x in (-40, 40):
        place('Bin', K.litter_bin, x, -34, 0, group='Square')
    # town hall forecourt: planters + lamps flanking the steps
    for sx in (-1, 1):
        for z in (-121, -128.5):
            place('Planter2', lambda: K.planter(2), sx * 36, z, 0, group='Hero')
        place('StreetLamp', K.street_lamp, sx * 30, -120, 0, group='Hero')
        place('Hedge1', lambda: K.hedge(1, 12), sx * 60, -150, 90, group='Hero')

def alley(rng):
    """back alley z ~141..184 between the shop row and the south row: dumpsters, bags, pallets, pipes"""
    z0, z1 = 141.0, 197.0
    items = [('Dumpster_teal', lambda: K.dumpster(1, 'teal'), -44, z0 + 9, 0), ('TrashBags', K.trash_bags, -36, z0 + 7, 30),
             ('Pallets', K.pallets, -8, z0 + 8, 10), ('Dumpster_blue', lambda: K.dumpster(2, 'blue'), 14, z1 - 10, 180),
             ('TrashBags', K.trash_bags, 22, z1 - 8, 200), ('Dumpster_teal', lambda: K.dumpster(1, 'teal'), 40, z0 + 9, 0),
             ('Pallets', K.pallets, -30, z1 - 8, 160), ('Bin', K.litter_bin, 50, z1 - 6, 0)]
    for key, fn, x, z, yaw in items:
        place(key, fn, x, z, yaw, group='Alley'); reserve(x, z, 4)
    for x in (-50, -20, 26):
        place('WallPipes', K.wall_pipes, x, z0 + .2, 180, group='Alley')
    for x in (-36, 6, 46):
        place('StreetLamp', K.street_lamp, x, z1 - 2.5, 180, group='Alley')

def traffic(rng):
    """parked cars along curbs + a few cars in the lanes, the bus at its stop, taxis at the station"""
    cars = [('sedan', 'red'), ('hatch', 'teal'), ('sedan', 'blue'), ('van', 'cream'), ('hatch', 'yellow'), ('sedan', 'cream'), ('taxi', 'yellow')]
    def ck(i):
        k, c = cars[i % len(cars)]
        return ('Car_taxi', K.taxi) if k == 'taxi' else ('Car_%s_%s' % (k, c), (lambda k=k, c=c: K.car(k, c)))
    i = 0
    MOVING = ((-150, 70 - 14, -90, 0), (40, 70 + 14, 90, 2), (180, 70 - 14, -90, 4), (-84 + 7, -40, 0, 1), (84 - 7, 150, 180, 5), (-30, -96 - 7, -90, 6))
    def clear_of_moving(x, z): return all(abs(x - mx) > 16 or abs(z - mz) > 8 for mx, mz, _, _ in MOVING)
    for nm, (zc, w) in STREETS_EW.items():
        xe = BLVD_X1 - 10 if nm == 'Blvd' else 266.0
        for s in (-1, 1):
            z = zc + s * (w / 2 - 4); x = -210.0
            while x < xe:
                if not near_intersection(x, z, 8) and abs(x) > 14 and rng.random() < .22 and clear_of_moving(x, z) and not (nm == 'Blvd' and s > 0 and 120 < x < 170):
                    key, fn = ck(i); i += 1
                    place(key, fn, x, z, 90 if s < 0 else -90, y=0, group='Traffic')
                x += 18
    for nm, (xc, w) in STREETS_NS.items():
        for s in (-1, 1):
            x = xc + s * (w / 2 - 4); z = -205.0
            while z < 195:
                if not near_intersection(x, z, 8) and rng.random() < .24 and clear_of_moving(x, z):
                    key, fn = ck(i); i += 1
                    place(key, fn, x, z, 0 if s > 0 else 180, y=0, group='Traffic')
                z += 18
    # moving cars in lanes (static here; road path hooks drive the real ones)
    for (x, z, yaw, idx) in MOVING:
        key, fn = ck(idx); place(key, fn, x, z, yaw, y=0, group='Traffic')
    # the bus at its stop (boulevard south side, kerb lane, heading east -> front +X)
    place('CityBus', K.bus, 146, 70 + 28 - 6, -90, y=0, group='Traffic')
    place('BusStop', K.bus_stop, 146, 98 + 4.5, 180, group='Street'); reserve(146, 102, 8)
    anchor('BusStop', 'busstop', 'Stations', 146, CURB, 102, 180, (12, 8, 5))
    for k in range(3): place('Car_taxi', K.taxi, 250 + k * 0, 56 + k * 9, -90, y=CURB, group='Traffic')

# ------------------------------------------------------------------ road path points (car / NPC scripts)
def road_paths():
    step = 24.0
    def lane(name, pts, attrs):
        for k, (x, z) in enumerate(pts):
            anchor('%s_%02d' % (name, k + 1), 'roadpath', 'RoadPaths', x, .2, z, 0, (2, 2, 2), Path=name, Order=k + 1, **attrs)
    for nm, (zc, w) in STREETS_EW.items():
        xe = BLVD_X1 - 6 if nm == 'Blvd' else 270.0
        off = 14.0 if nm == 'Blvd' else 7.0
        xs = [X0 + 10 + step * k for k in range(int((xe - X0 - 10) / step) + 1)]
        lane(nm + '_East', [(x, zc + off) for x in xs], {'Dir': 'east', 'Speed': 30})
        lane(nm + '_West', [(x, zc - off) for x in reversed(xs)], {'Dir': 'west', 'Speed': 30})
    for nm, (xc, w) in STREETS_NS.items():
        zs = [Z0 + 10 + step * k for k in range(int((Z1 - Z0 - 20) / step) + 1)]
        lane(nm + '_South', [(xc - 7, z) for z in zs], {'Dir': 'south', 'Speed': 26})
        lane(nm + '_North', [(xc + 7, z) for z in reversed(zs)], {'Dir': 'north', 'Speed': 26})
    k = 0
    for nm1, (xc, xw) in STREETS_NS.items():
        for nm2, (zc, zw) in STREETS_EW.items():
            k += 1; anchor('Junction_%s_%s' % (nm1, nm2), 'roadnode', 'RoadPaths', xc, .2, zc, 0, (xw, 2, zw), Streets='%s,%s' % (nm1, nm2))
    loop = [(-62, -74), (62, -74), (62, 36), (-62, 36)]                                   # NPC sidewalk loop round the square
    pts = []
    for a, b in zip(loop, loop[1:] + loop[:1]):
        n = int(math.dist(a, b) / 16)
        pts += [(lerp(a[0], b[0], t / n), lerp(a[1], b[1], t / n)) for t in range(n)]
    for k, (x, z) in enumerate(pts):
        anchor('SquareWalk_%02d' % (k + 1), 'npcpath', 'NPCPaths', x, CURB + .2, z, 0, (2, 2, 2), Path='SquareWalk', Order=k + 1)

# ------------------------------------------------------------------ look: bright daytime
def look():
    w = bpy.data.worlds.new('Day'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.62, .82, 1.0, 1)
    cr.elements[1].position = .55; cr.elements[1].color = (.12, .4, .95, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .9
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .1; b.inputs['Roughness'].default_value = .92
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.6; sun.data.color = (1.0, .95, .86); sun.data.angle = math.radians(4)
    el = math.radians(48); az = math.radians(140)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    LOOK['sun'] = [round(math.cos(el) * math.sin(az), 3), round(math.sin(el), 3), round(-math.cos(el) * math.cos(az), 3)]
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = 1.2; fill.data.color = (.6, .78, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.4, .7, .5)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    SC.view_settings.exposure = 0.0
    try: SC.eevee.taa_render_samples = 48
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (2400, 2400, 600); hz.location = (0, 0, 290); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.remove(vt.nodes['Principled BSDF'])
    pv = vt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00012
    pv.inputs['Color'].default_value = (.75, .87, 1.0, 1)
    vt.links.new(pv.outputs[0], vt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False
LOOK = {}

def shot(name, loc, tgt, fov=50, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SPAWN = (0.0, CURB, 26.0)
SHOTS = {
    'map_beauty.png': ((-40, 10, 92), (25, 50, -165), 55),
    'map_overview.png': ((-330, 300, 330), (40, 0, -20), 42),
    'map_top.png': ((60, 900, 1), (60, 0, 0), 46),
    'map_spawn.png': ((0, 7.5, 34), (0, 55, -170), 60),
    'map_station.png': ((150, 11, 76), (300, 24, 70), 50),
    'map_alley.png': ((-60, 8, 158), (40, 12, 166), 58),
    'map_shops.png': ((-20, 8, 52), (10, 14, 130), 58),
    'map_bank.png': ((-60, 8, 0), (-144, 18, -19), 58),
    'map_dealer.png': ((60, 8, 6), (140, 10, -10), 58),
    'map_platform.png': ((330, 9, 150), (346, 8, 20), 55),
    'map_street.png': ((-196, 6.5, 46), (-120, 9, 36), 50),                 # street tree close-up (boulevard sidewalk)
}

def build():
    for loc, t, f in SHOTS.values():
        if loc[1] < 20: reserve(loc[0], loc[2], 3)
    reserve(SPAWN[0], SPAWN[2], 6); reserve(0, -96, 10); reserve(0, 70, 10)
    rng = random.Random(7)
    ground(); markings(); median(); square()
    S = buildings()
    for nm, cx, cz, hx, hz in (('Bank', -144, -28, 31, 23), ('CarShowroom', 136, -19, 24, 29), ('TownHall', 0, TH_Z, 54, 46), ('Station', ST_X, ST_Z, 26, 54)):
        RECTS.append((nm, cx - hx, cx + hx, cz - hz, cz + hz))
    for i, (x, z) in enumerate(SKY_SPOTS): RECTS.append(('Sky%d' % i, x - 22, x + 22, z - 22, z + 22))
    check_rects()
    landmarks(S); railway(); skyline_ring()
    square_dressing(rng); alley(rng); traffic(rng); dressing(rng); road_paths()
    anchor('SpawnLocation', 'spawn', 'Spawn', SPAWN[0], CURB + .5, SPAWN[2], 0, (12, 1, 12))

build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
STATS = {'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
         'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()},
         'kit_tris_x_count': dict(sorted(((k, v[1] * COUNT.get(k, 0)) for k, v in LIB.items()), key=lambda kv: -kv[1]))}
json.dump(STATS, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'look': LOOK}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'town_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATS['tris_total'], 'clipped', K.CP.STATS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
