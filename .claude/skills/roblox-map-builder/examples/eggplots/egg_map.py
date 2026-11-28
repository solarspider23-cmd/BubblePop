# blender -b --factory-startup --python egg_map.py [-- norender] [-- name.png ...] -> Eggstead Isle (egg_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). "Steal a ___" egg map: an island arena in a lake. A central lane
# runs north -> south: the Great Egg Hatchery (hero) spits eggs onto a conveyor that rides past 8 identical plots (two
# rows of 4 facing each other across the lane) to a basket drain; the spawn plaza with three shop stands sits at the
# south end. Three humped footbridges cross the belt in the gaps between plots. Ranch fence round the island, lake,
# rolling hills with trees, a barn, silo and windmill as the backdrop.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import egg_props as EP
F = EP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box, cyl, ngon_prism

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]
U = lambda col: EP.PAL.u(col)
def sh_val(col, v): return lambda f: [(U(col), clamp(v + .1 * f.normal.y, .04, .96))] * len(f.loops)

# ------------------------------------------------------------------ layout numbers
LANE_HW = 26.0                       # paved lane x +-26 (belt in the middle, walkways either side)
WALK_Y = .25                         # lane paving top
LANE_Z = (-146.0, 146.0)
PLOT_CX = 62.0; PLOT_Z = (-96.0, -32.0, 32.0, 96.0)
PLOT_W, PLOT_D = 56.0, 64.0          # along the lane (world z) x deep (world x)
YARD_Y = .55; PAVE_Y = .68
# plot ids: 1-4 west (north -> south), 5-8 east; accents alternate warm / cool across and along the lane
PLOTS = [(i + 1, -PLOT_CX, z, -90.0, a) for i, (z, a) in enumerate(zip(PLOT_Z, ('red', 'yellow', 'sky', 'purple')))] + \
        [(i + 5, PLOT_CX, z, 90.0, a) for i, (z, a) in enumerate(zip(PLOT_Z, ('orange', 'teal', 'blue', 'pink')))]
HATCH_Z = -175.5; HATCH_S = 1.35                     # hero centre (front faces south down the lane)
BELT_N, BELT_S = -151.0, 129.0       # belt runs from the hatch tunnel (north) to the drain (south)
SEG = 16.0
BRIDGES = (-64.0, 0.0, 64.0)
DRAIN_Z = 139.5                      # plinth clears the belt end cap (cap at BELT_S + .9)
PLAZA = (0.0, 176.0); PLAZA_R = 27.0
SPAWN = (0.0, WALK_Y, 178.0)
ISLE = (132.0, 236.0, 4.0)           # superellipse half sizes x, z + exponent
WATER_Y = -1.6

def isle_d(x, z):
    ax, az, p = ISLE
    return (abs(x / ax) ** p + abs(z / az) ** p) ** (1 / p)

def H(x, z):
    d = isle_d(x, z)
    if d <= 1.0: return 0.0
    bank = -5.0 * smooth((d - 1.0) / .07)
    hill = 34.0 * smooth((d - 1.32) / .5) + 30.0 * smooth((d - 1.9) / .7)
    bump = (nz(x, 0, z, 60, 3) - .5) * 14.0 * smooth((d - 1.35) / .3)
    return bank + hill + bump

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []; GROUP_TRIS = {}
def kit(key, fn):
    if key not in LIB:
        P = fn(); LIB[key] = (F.to_kit(P, KIT), P.tris)
    return LIB[key][0]
FOOT = {}
def foot(key):
    if key not in FOOT:
        r = 0.0
        for me in LIB[key][0].values():
            for v in me.vertices:
                if v.co.z < .8: r = max(r, math.hypot(v.co.x, v.co.y))
        FOOT[key] = min(r, 9.0)
    return FOOT[key]
def place(key, fn, x, z, yaw=0.0, s=1.0, y=None, sink=.25, group='Props'):
    meshes = kit(key, fn)
    if y is None:
        fr = foot(key) * s
        hs = [Hg(x, z)] + [Hg(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]; GROUP_TRIS[group] = GROUP_TRIS.get(group, 0) + LIB[key][1]
GROUND_BVH = [None]
def Hg(x, z):
    """height of the BUILT ground mesh (the coarse hill grid departs from H by several studs): ray down"""
    if GROUND_BVH[0] is None: return H(x, z)
    hit = GROUND_BVH[0].ray_cast(r2b((x, 2000.0, z)), Vector((0, 0, -1)), 4000.0)
    return hit[0].z if hit[0] is not None else H(x, z)
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
STATIC_TRIS = {}
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris
def to_world(local, pos, yaw):
    return Vector(pos) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Vector(local)

ANCHORS = []
def anchor(name, kind, p, yaw=0.0, size=(4, 1, 4), group=None, attrs=None):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group or kind, 'pos': [round(p[0], 2), round(p[1], 2), round(p[2], 2)],
                    'yaw': round(yaw % 360, 1), 'size': [round(v, 2) for v in size], 'attrs': attrs or {}})

# ------------------------------------------------------------------ hardscape: lane paving + spawn plaza
def inset_top(bm, th=.08, depth=-.05):
    fs = list(bm.faces)
    for f in fs:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.inset_individual(bm, faces=fs, thickness=th, depth=depth, use_even_offset=True)
    bm.normal_update()

def hardscape():
    """lane: a stone slab (kerbed, chamfer into the lawn) carrying 4-stud pavers in a running bond, a cream band along
    the belt bed; spawn plaza: polar pavers round a yellow-rimmed centre disc; a short paved neck lane -> plaza"""
    mb = MB(); z0, z1 = LANE_Z
    mb.add(T(box((LANE_HW * 2 + 2.0, 1.4, z1 - z0 + 2.0)), (0, WALK_Y - .72, (z0 + z1) / 2)), sh_val('stone', .45))
    bm = bmesh.new(); ts = 4.0; rng = random.Random(2)
    for j in range(int((z1 - z0) / ts)):
        za, zb = z0 + j * ts, z0 + (j + 1) * ts; off = (ts / 2) if j % 2 else 0
        xs = [-LANE_HW] + [x for x in [-LANE_HW + off + k * ts for k in range(1, 15)] if -LANE_HW < x < LANE_HW] + [LANE_HW]
        for xa, xb in zip(xs, xs[1:]):
            if xb - xa < .5: continue
            bm.faces.new([bm.verts.new((x, WALK_Y, z)) for x, z in ((xa, za), (xb, za), (xb, zb), (xa, zb))])
    inset_top(bm, .1, -.06)
    def shp(f):
        c = f.calc_center_median(); h = EP.B.h01(round(c.x, 1), 0, round(c.z, 1))
        v = .66 + (h - .5) * .14 - (.2 if f.normal.y < .9 else 0)
        return [(U('stone'), clamp(v, .04, .96))] * len(f.loops)
    mb.add(bm, shp)
    for sx in (-1, 1):                                                         # kerb strips (cream) along the lane edges
        mb.add(T(EP.rbox((1.2, .5, z1 - z0), .15), (sx * (LANE_HW + .3), WALK_Y + .05, (z0 + z1) / 2)), sh_val('cream', .72))
    # neck + plaza
    cx, cz = PLAZA
    mb.add(T(EP.lathe([(PLAZA_R + 1.0, -1.2), (PLAZA_R + 1.0, WALK_Y - .02), (0, WALK_Y - .02)], 40), (cx, 0, cz)), sh_val('stone', .45))
    bm = bmesh.new(); r = 5.0; ring = 0
    while r < PLAZA_R - .1:
        rb = min(r + 3.0, PLAZA_R); n = max(8, round(math.tau * (r + rb) / 2 / 3.4))
        for k in range(n):
            a0 = (k + .5 * (ring % 2)) * math.tau / n; a1 = a0 + math.tau / n
            pts = [(math.cos(a) * rr, math.sin(a) * rr) for rr, a in ((r, a0), (r, (a0 + a1) / 2), (r, a1), (rb, a1), (rb, (a0 + a1) / 2), (rb, a0))]
            bm.faces.new([bm.verts.new((cx + x, WALK_Y, cz + z)) for x, z in pts])
        r = rb; ring += 1
    inset_top(bm, .1, -.06)
    def shq(f):
        c = f.calc_center_median(); rr = math.hypot(c.x - cx, c.z - cz); ring = int((rr - 5) / 3)
        h = EP.B.h01(round(c.x, 1), 0, round(c.z, 1))
        v = (.74 if ring % 2 else .64) + (h - .5) * .08 - (.2 if f.normal.y < .9 else 0)
        return [(U('stone'), clamp(v, .04, .96))] * len(f.loops)
    mb.add(bm, shq)
    mb.add(T(EP.lathe([(5.0, WALK_Y - .1), (5.0, WALK_Y + .05), (0, WALK_Y + .05)], 20), (cx, 0, cz)), sh_val('cream', .8))
    mb.add(T(EP.torus(5.0, .35, 20, 4), (cx, WALK_Y + .05, cz)), sh_val('yellow', .6))
    mb.add(T(EP.torus(PLAZA_R + .5, .45, 40, 4), (cx, WALK_Y + .02, cz)), sh_val('cream', .75))
    static('Hardscape_Lane', mb, 'Hardscape')

def T(bm, pos=(0, 0, 0), yaw=0.0, pitch=0.0, roll=0.0, s=None): return EP.T(bm, pos, yaw, pitch, roll, s)

def ground():
    """island lawn + lake bank + hills: fine grid near the island, coarse on the hills; faces wholly under the lane slab
    are skipped. Colour: lawn by noise, stone shore below the waterline"""
    def axis(lo, hi, fine_lo, fine_hi, f, c):
        out = list(range(lo, fine_lo, c)) + [x for x in range(fine_lo, fine_hi, f)] + list(range(fine_hi, hi + 1, c))
        return sorted(set(out))
    xs = axis(-560, 560, -200, 200, 6, 40); zs = axis(-640, 640, -320, 320, 6, 40)
    bm = bmesh.new(); VV = {}
    def v(i, j):
        if (i, j) not in VV: VV[i, j] = bm.verts.new((xs[i], H(xs[i], zs[j]), zs[j]))
        return VV[i, j]
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if abs(xs[i]) < LANE_HW - 1 and abs(xs[i + 1]) < LANE_HW - 1 and LANE_Z[0] + 1 < zs[j] and zs[j + 1] < LANE_Z[1] - 1: continue
            f = bm.faces.new((v(i, j), v(i, j + 1), v(i + 1, j + 1), v(i + 1, j))); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    def shg(f):
        out = []
        for l in f.loops:
            p = l.vert.co
            if p.y < WATER_Y + .3: out.append((U('stone'), clamp(.48 + p.y * .02, .2, .7)))
            else:
                vv = .52 + (nz(p.x, 0, p.z, 22, 5) - .5) * .24 + .05 * smooth(p.y / 40)
                out.append((U('grass'), clamp(vv, .04, .96)))
        return out
    mb = MB(); mb.add(bm, shg, smooth=False); static('Ground_Island', mb, 'Ground')
    from mathutils.bvhtree import BVHTree
    gm = bpy.data.objects['Ground_Island'].data; GROUND_BVH[0] = BVHTree.FromPolygons([v.co.copy() for v in gm.vertices], [p.vertices[:] for p in gm.polygons])
    # lake: a convex outline at island distance 1.5, where the bank is 3-10 studs above the water, so every edge runs
    # under the bank and the hills bed it (a rectangle to the map edge sat 60 under the hills: edges failed the bank check)
    w = MB(); wb = bmesh.new()
    wb.faces.new([wb.verts.new((x, WATER_Y, z)) for x, z in [isle_point(t * math.tau / 96, 1.5) for t in range(96)]])
    for f in wb.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    w.add(wb, lambda f: [(U('water'), .55)] * len(f.loops)); static('Sea_Lake', w, 'Water')
    # hidden lake floor 6 under the water (below every bit of ground): water under the island / props has a bed within 8
    sb = MB(); bb = bmesh.new()
    bb.faces.new([bb.verts.new((x, WATER_Y - 6.0, z)) for x, z in ((-202, -358), (202, -358), (202, 358), (-202, 358))])
    for f in bb.faces:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    sb.add(bb, lambda f: [(U('stone'), .3)] * len(f.loops)); static('Ground_SeaFloor', sb, 'Water')

# ------------------------------------------------------------------ one plot (plot-local: front -Z faces the lane)
NEST_Y = PAVE_Y
FRONT_RUNS = [((-28.0, -32.0), (1, 0), (8, 8, 4)), ((8.0, -32.0), (1, 0), (4, 8, 8)),
              ((28.0, -32.0), (0, 1), (8,) * 8), ((28.0, 32.0), (-1, 0), (8,) * 7), ((-28.0, 32.0), (0, -1), (8,) * 8)]
def plot(pid, cx, cz, yaw, acc):
    g = 'Plot%d' % pid
    W = lambda lx, lz, ly=0.0: to_world((lx, ly, lz), (cx, 0, cz), yaw)
    def put(key, fn, lx, lz, lyaw=0.0, y=YARD_Y, s=1.0):
        p = W(lx, lz); place(key, fn, p.x, p.z, yaw + lyaw, s=s, y=y, group=g)
    put('yard_' + acc, lambda: EP.plot_slab(acc), 0, 0, y=0.0)
    put('coop_' + acc, lambda: EP.coop(acc), 0, EP.COOP_Z, y=YARD_Y + .02)        # stands ON the yard (was sunk .3 into it)
    for k, (lx, lz) in enumerate(EP.NEST_SLOTS):
        put('nest_' + acc, lambda: EP.nest_pedestal(acc), lx, lz, y=NEST_Y)
        p = W(lx, lz, NEST_Y + 3.35)
        anchor('EggSlot%d' % (k + 1), 'eggslot', p, yaw, (2.6, 3.6, 2.6), g, {'PlotId': pid, 'SlotIndex': k + 1})
    put('pad_' + acc, lambda: EP.collect_pad(acc), EP.PAD_POS[0], EP.PAD_POS[1], y=PAVE_Y + .07)    # on the aisle paving, not sunk through the yard
    anchor('CollectPad', 'collectpad', W(EP.PAD_POS[0], EP.PAD_POS[1], PAVE_Y + .6), yaw, (5.6, 1.2, 5.6), g, {'PlotId': pid})
    put('gate_' + acc, lambda: EP.gate_frame(acc), 0, -32.0, y=0.0)
    put('mat_' + acc, lambda: EP.gate_mat(acc), 0, -36.4, y=WALK_Y)
    anchor('Gate', 'gate', W(0, -32.0, 5.2), yaw, (14.0, 9.6, 1.0), g, {'PlotId': pid})
    sp = (18.5, -34.6)
    put('sign_' + acc, lambda: EP.owner_sign(acc), sp[0], sp[1], y=0.0)
    anchor('OwnerSign', 'ownersign', W(sp[0], sp[1] - .45, 6.0), yaw, (7.0, 3.5, .2), g, {'PlotId': pid})
    anchor('CoopDoor', 'coopdoor', W(0, EP.COOP_Z - 8.0, 4.0), yaw, (6.8, 7.6, 2.0), g, {'PlotId': pid})
    anchor('Plot%d' % pid, 'plot', W(0, 0, 8.0), yaw, (PLOT_W, 16.0, PLOT_D), g, {'PlotId': pid, 'Accent': acc})
    # fence: runs of 8 / 4 with a post at each segment start; corner + run-end posts carry the egg knob
    for ri, ((sx_, sz_), (dx, dz), lens) in enumerate(FRONT_RUNS):
        x, z = sx_, sz_; ly = math.degrees(math.atan2(-dz, dx))
        for li, L in enumerate(lens):
            kw = {}
            if ri == 0 and li == len(lens) - 1: kw = dict(r1=float(L) - 1.4, tag='e')      # ends at the gate pillar (foot x +-6.7..9.3)
            elif ri == 1 and li == 0: kw = dict(post=False, r0=1.4, tag='s')                # starts at the other gate pillar
            elif li == 0: kw = dict(post=False, tag='c')                                     # starts at a corner FencePost
            put('fence%d%s_%s' % (L, kw.get('tag', ''), acc), (lambda L=L, kw=kw: EP.fence_run(acc, float(L), **kw)), x, z, ly, y=0.0)
            x += dx * L; z += dz * L
    for lx, lz in ((-28, -32), (28, -32), (28, 32), (-28, 32)):
        put('fpost_' + acc, lambda: EP.fence_post(acc), lx, lz, y=0.0)
    put('haystack', EP.hay_stack, -20.5, 26.5, 90)
    put('trough', EP.feed_trough, 22.5, 12.5, -90)
    for sx in (-1, 1):
        put('tub%d' % (2 if sx < 0 else 3), (lambda sd=(2 if sx < 0 else 3): EP.flower_tub(sd, ('pink', 'sky')[sd % 2])), sx * 11.5, -29.0)

# ------------------------------------------------------------------ lane, belt, hero, drain
def lane():
    place('hatchery', EP.hatchery, 0, HATCH_Z, 180, s=HATCH_S, y=0.0, group='Hero')
    anchor('Hatchery', 'station', (0, 66.0, HATCH_Z), 180, (6, 2, 6), 'Shops')
    anchor('HatchMouth', 'conveyor', (0, 6.0, HATCH_Z + 25.5 * HATCH_S), 180, (12, 10, 2), 'Conveyor')
    z = BELT_N + SEG
    k = 0
    while z <= BELT_S + .1:
        place('belt', EP.conveyor_seg, 0, z, 0, y=WALK_Y, group='Conveyor'); z += SEG; k += 1
    place('beltcap', EP.conveyor_end, 0, BELT_S + .9, 0, y=WALK_Y, group='Conveyor')
    anchor('ConveyorStart', 'conveyor', (0, WALK_Y + EP.BELT_Y + .5, BELT_N + 4.0), 180, (EP.BELT_W, 1, 2), 'Conveyor')
    anchor('ConveyorEnd', 'conveyor', (0, WALK_Y + EP.BELT_Y + .5, BELT_S - 1.0), 180, (EP.BELT_W, 1, 2), 'Conveyor')
    n = 14
    for i in range(n + 1):
        zz = lerp(BELT_N + 4.0, BELT_S - 1.0, i / n)
        anchor('Path%02d' % (i + 1), 'conveyorpath', (0, WALK_Y + EP.BELT_Y + .5, zz), 180, (1, 1, 1), 'Conveyor', {'Order': i + 1})
    anchor('DrainTrigger', 'drain', (0, WALK_Y + 2.5, BELT_S + 3.5), 180, (EP.BELT_W + 2, 5, 4), 'Conveyor')
    place('drain', EP.egg_drain, 0, DRAIN_Z, 0, y=WALK_Y - .2, group='Conveyor')
    for z in BRIDGES:
        place('bridge', EP.foot_bridge, 0, z, 0, y=WALK_Y, group='Lane')
    for z in (-128.0, -64.0, 0.0, 64.0, 128.0):
        for sx in (-1, 1):
            place('lamp', EP.lane_lamp, sx * 23.5, z + 6.0, 90 * sx, y=WALK_Y, group='Lane')
    # giant painted eggs flanking the hatchery + the plaza neck
    for k, (x, z, yw) in enumerate(((-40, -148, 20), (40, -148, -20), (-40, 150, 160), (40, 150, -160))):
        place('gegg%d' % k, (lambda k=k: EP.deco_egg(k)), x, z, yw, group='Lane'); reserve(x, z, 5)
    reserve(0, HATCH_Z, 38)

def spawn_area():
    cx, cz = PLAZA
    anchor('SpawnLocation', 'spawn', (SPAWN[0], WALK_Y + .5, SPAWN[2]), 180, (10, 1, 10), 'Spawn')
    for key, fn, x, z, yw, nm in (('eggshop', EP.egg_shop, -40.0, cz - 2, -90, 'EggShop'), ('sellstand', EP.sell_stand, 40.0, cz - 2, 90, 'Sell'),
                                  ('upgrade', EP.upgrade_stand, 0, cz + PLAZA_R + 9.0, 0, 'Upgrades')):
        place(key, fn, x, z, yw, s=1.3, y=0.0, group='Shops'); reserve(x, z, 12)
        anchor(nm, 'shop', tuple(to_world((0, 3.2, -6.0), (x, 0, z), yw)), yw, (14, 6, 4), 'Shops')
        anchor(nm + 'Sign', 'shopsign', tuple(to_world((0, 13.9, 3.9), (x, 0, z), yw)), yw, (6.5, 2.4, .3), 'Shops')
    place('statue', EP.nest_statue, -22.0, cz + 18.0, 30, y=0.0, group='Spawn'); reserve(-22, cz + 18, 7)
    for sx in (-1, 1):
        place('bench', EP.bench, sx * 20.0, cz - 18.5, 180 + sx * 45, y=WALK_Y, group='Spawn')
    place('tubA', lambda: EP.flower_tub(4, 'yellow'), 22.0, cz + 18.0, 0, y=WALK_Y, group='Spawn')
    place('tubB', lambda: EP.flower_tub(5, 'red'), 26.0, cz + 15.0, 0, y=WALK_Y, group='Spawn')
    for k in range(8):                                                         # plaza rim: tubs + lamps, gaps toward lane / shops
        a = math.radians(22.5 + k * 45); x, z = cx + math.cos(a) * (PLAZA_R - 2.5), cz + math.sin(a) * (PLAZA_R - 2.5)
        if k % 2: place('tubC', lambda: EP.flower_tub(6, 'orange'), x, z, k * 30, y=WALK_Y, group='Spawn')
        else: place('lamp', EP.lane_lamp, x, z, -math.degrees(a) - 90, y=WALK_Y, group='Spawn')
    for x, z in ((-12, 145), (12, 145)):
        place('lamp', EP.lane_lamp, x, z, 0, y=WALK_Y, group='Spawn')

# ------------------------------------------------------------------ dressing + backdrop
def isle_point(t, k=.965):
    """point on the island superellipse at parameter angle t, scaled by k"""
    ax, az, p = ISLE; c, s = math.cos(t), math.sin(t)
    return (k * ax * math.copysign(abs(c) ** (2 / p), c), k * az * math.copysign(abs(s) ** (2 / p), s))

def dressing(rng):
    # ranch fence round the island (a gap of 0 - the fence is the arena edge)
    pts = [isle_point(i * math.tau / 720) for i in range(720)]
    acc_len = 0.0; last = pts[0]; segs = []
    for p in pts[1:] + pts[:1]:
        d = math.hypot(p[0] - last[0], p[1] - last[1])
        if d >= 16.0: segs.append((last, p)); last = p
    for a, b in segs:
        yw = math.degrees(math.atan2(-(b[1] - a[1]), b[0] - a[0]))
        place('ranch', lambda: EP.ranch_fence(16.0), a[0], a[1], yw, s=1.0, group='Edge')
    # trees + bushes on the island margins (behind the plots, round the hatchery, round the plaza)
    TREES = {'t1': lambda: EP.tree(1, 15.0), 't2': lambda: EP.tree(2, 18.0), 't3': lambda: EP.tree(3, 13.0), 'p1': lambda: EP.pine(1, 20.0), 'p2': lambda: EP.pine(2, 16.0)}
    for k in range(900):
        x, z = rng.uniform(-128, 128), rng.uniform(-232, 232)
        if isle_d(x, z) > .93: continue
        if abs(x) < 100 and -132 < z < 132: continue                              # plots + lane
        if abs(x) < 34 and z > -150: continue                                     # lane + plaza axis
        if math.hypot(x - PLAZA[0], z - PLAZA[1]) < PLAZA_R + 16: continue
        if not free(x, z, 7): continue
        key = rng.choice(list(TREES)); place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(.85, 1.15), group='Trees'); reserve(x, z, 7)
    for k in range(260):
        x, z = rng.uniform(-128, 128), rng.uniform(-232, 232)
        if isle_d(x, z) > .94 or (abs(x) < 96 and -128 < z < 128) or (abs(x) < 30 and z > -150): continue
        if math.hypot(x - PLAZA[0], z - PLAZA[1]) < PLAZA_R + 4 or not free(x, z, 3): continue
        if rng.random() < .5: place('bush%d' % (k % 3), (lambda s=k % 3: EP.bush(s + 1, 2.0, ('red', 'pink', None)[s])), x, z, rng.uniform(0, 360), group='Trees')
        else: place('fp%d' % (k % 3), (lambda s=k % 3: EP.flower_patch(s + 1, (('pink', 'yellow'), ('sky', 'cream'), ('red', 'orange'))[s])), x, z, rng.uniform(0, 360), group='Flowers')
        reserve(x, z, 3)
    # gaps between plots + the strip between the lane kerb and the plot fronts: flower patches + bushes (no blocking)
    for sx in (-1, 1):
        for gz in (-128.0, -64.0, 0.0, 64.0, 128.0):
            for k, lx in enumerate((40.0, 58.0, 76.0, 90.0)):
                place('fp%d' % (k % 3), (lambda s=k % 3: EP.flower_patch(s + 1, (('pink', 'yellow'), ('sky', 'cream'), ('red', 'orange'))[s])), sx * lx, gz + (1.5 if k % 2 else -1.5), k * 40, group='Flowers')
            place('bush%d' % 0, lambda: EP.bush(1, 2.0, 'red'), sx * 100.0, gz, 0, group='Trees')
    # lake: reeds + lily pads near the shore, boulders on the bank
    for k in range(70):
        t = rng.uniform(0, math.tau); x, z = isle_point(t, rng.uniform(1.04, 1.12))
        if rng.random() < .5: place('reeds%d' % (k % 2), (lambda s=k % 2: EP.reeds(s + 1)), x, z, rng.uniform(0, 360), y=WATER_Y - .3, group='Lake')
        else: place('lily%d' % (k % 2), (lambda s=k % 2: EP.lily_pads(s + 1)), x, z, rng.uniform(0, 360), y=WATER_Y + .05, group='Lake')
    for k in range(40):
        t = rng.uniform(0, math.tau); x, z = isle_point(t, rng.uniform(1.0, 1.03))
        place('boulder%d' % (k % 3), (lambda s=k % 3: EP.boulder(s + 1, 2.2 + s)), x, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.4), group='Lake')
    # hills: farm backdrop + forests
    for key, fn, x, z, yw in (('barn', EP.barn, -230, -150, 70), ('silo', EP.silo, -232, -124, 0), ('windmill', EP.windmill, 235, -60, -100),
                              ('barn', EP.barn, 210, 250, -150), ('silo', EP.silo, 232, 242, 0), ('windmill', EP.windmill, -210, 260, 140)):
        place(key, fn, x, z, yw, group='Backdrop'); reserve(x, z, 22)
    for k in range(700):
        x, z = rng.uniform(-540, 540), rng.uniform(-620, 620)
        d = isle_d(x, z)
        if d < 1.36 or not free(x, z, 9): continue
        if rng.random() > .65: continue
        key = rng.choice(('p1', 'p2', 't1', 't2', 'p1'))
        place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(1.0, 1.5), group='Hills'); reserve(x, z, 9)
    for k, (x, z, y, s) in enumerate(((-300, -400, 150, 3.0), (260, -380, 170, 2.6), (420, 80, 160, 2.8), (-420, 120, 175, 3.2),
                                      (-200, 420, 150, 2.6), (230, 450, 165, 3.0), (0, -520, 180, 3.4))):
        place('cloud%d' % (k % 3), (lambda k=k: EP.cloud(k % 3 + 1)), x, z, rng.uniform(0, 360), y=y, s=s, group='Sky')

def build():
    hardscape(); ground()
    for p in PLOTS: plot(*p)
    for pid, cx, cz, yw, acc in PLOTS: reserve(cx, cz, 40)
    lane(); spawn_area()
    for loc, tgt, fov in SHOTS.values(): reserve(loc[0], loc[2], 6)
    dressing(random.Random(11))

# ------------------------------------------------------------------ look: crisp spring morning
def look():
    w = bpy.data.worlds.new('Spring'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.3; mr.inputs['From Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.85, .93, .9, 1)
    cr.elements[1].position = .7; cr.elements[1].color = (.16, .48, .95, 1)
    e = cr.elements.new(.3); e.color = (.55, .8, 1.0, 1)
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .9
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .15; b.inputs['Roughness'].default_value = .9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.6; sun.data.color = (1.0, .93, .82); sun.data.angle = math.radians(2.5)
    el = math.radians(34); az = math.radians(115)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = .9; fill.data.color = (.72, .86, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.5, .7, .4)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    # thin haze volume
    hz = bpy.data.meshes.new('Haze'); hb = bmesh.new(); bmesh.ops.create_cube(hb, size=1.0); hb.to_mesh(hz); hb.free()
    ho = bpy.data.objects.new('HazeVolume', hz); SC.collection.objects.link(ho); ho.scale = (1500, 1500, 400); ho.location = (0, 0, 150)
    hm = bpy.data.materials.new('HazeMat'); hm.use_nodes = True; hn = hm.node_tree
    for n in list(hn.nodes):
        if n.type != 'OUTPUT_MATERIAL': hn.nodes.remove(n)
    vol = hn.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = .00012
    vol.inputs['Color'].default_value = (.8, .9, 1.0, 1)
    hn.links.new(vol.outputs[0], hn.nodes['Material Output'].inputs['Volume']); hz.materials.append(hm)
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    for k, v in (('taa_render_samples', 32), ('shadow_pool_size', '1024'), ('use_raytracing', False), ('volumetric_end', 1500.0)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)

MATERIALS = {'grass': 'Grass', 'leaf': 'SmoothPlastic', 'wood': 'WoodPlanks', 'cream': 'SmoothPlastic', 'stone': 'SmoothPlastic',
             'dark': 'SmoothPlastic', 'water': 'SmoothPlastic'}
for a in EP.ACC: MATERIALS[a] = 'SmoothPlastic'
MAT_OVERRIDES = {'Hardscape_': {'stone': 'Concrete'}, 'Tree': {'wood': 'Wood'}, 'Pine': {'wood': 'Wood'}, 'Boulder': {'stone': 'Slate'},
                 'Ground_': {'stone': 'Slate'}, 'Cloud': 'SmoothPlastic', 'Sea_': 'SmoothPlastic', 'HayStack': {'yellow': 'Fabric'}}
def material_skin():
    import roblox_materials as RM
    RM.preview(EP.PAL, F.materials()['pal'], MATERIALS, skip=('Cloud', 'Sea_'), overrides=MAT_OVERRIDES)
    RM.write_map(EP.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)

def shot(name, loc, tgt, fov=35, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

SHOTS = {   # vertical FOV
    'map_beauty.png': ((150, 95, 215), (0, 6, -20), 40),
    'map_overview.png': ((0, 520, 40), (0, 0, -8), 52),
    'map_spawn.png': ((SPAWN[0], 8.0, SPAWN[2] + 6), (0, 10, 40), 60),
    'map_plot.png': ((-10, 30, -12), (-60, 2, -36), 50),
    'map_hero.png': ((22, 22, -108), (0, 18, -168), 50),
    'map_lane.png': ((14, 14, 40), (-4, 4, -40), 55),
    'map_shops.png': ((0, 20, 140), (0, 4, 192), 55),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
plot_tris = GROUP_TRIS.get('Plot1', 0)
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
           'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'tris_by_group': GROUP_TRIS, 'tris_one_plot': plot_tris,
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'plots': [{'id': p[0], 'centre': [p[1], p[2]], 'yaw': p[3], 'accent': p[4]} for p in PLOTS]},
          open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'egg_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), 'plot', plot_tris, STATIC_TRIS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
