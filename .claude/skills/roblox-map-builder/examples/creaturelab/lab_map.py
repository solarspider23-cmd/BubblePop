# blender -b --factory-startup --python lab_map.py [-- norender] [-- name.png ...] -> Bloomcrest Care Centre (lab_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: interior-first hub (a walkable building interior with
# a small exterior entry plaza). A round care hall (rotunda, inner r 44) with a glass south facade; stations round its
# wall (Heal W, Mart E, Storage NE, Trade NW); an 18 wide arch north into the research wing (specimen tanks, benches,
# starter table, the Bloom Chamber hero at the far end on the axis). Outside: raised forecourt with a capsule fountain,
# a short path south to the spawn plaza, lawns, hedges, trees, gentle hills.
# Bearings in the hall: angle a (deg) -> (cos a, sin a) * r: 0 = east, 90 = south (entrance), 180 = west, 270 = north.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import lab_props as LP
F = LP.G
from pro_lib import clean, KM, r2b, nz, clamp, smooth, lerp, MB, box, cyl, hull, rock_pts, ngon_prism

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

FL = LP.FL; RR = LP.ROT_R
FORE_Y = FL                      # forecourt terrace top (same as the hall floor: level entry)
SPAWN_Y = .35
SPAWN = (0.0, SPAWN_Y, 118.0)
D2R = math.radians
def pol(a, r): return (math.cos(D2R(a)) * r, math.sin(D2R(a)) * r)
def face_in(a): return 90.0 - a                     # yaw that turns a prop's -Z front toward the hall centre
U = lambda col: LP.PAL.u(col)
def sh_val(col, v): return lambda f: [(U(col), clamp(v + .1 * f.normal.y, .04, .96))] * len(f.loops)

# ------------------------------------------------------------------ ground (lawn + soft hills)
def H(x, z):
    d = math.hypot(x, (z + 20) * .85)
    rise = 30 * smooth((d - 150) / 200) + 25 * smooth((d - 330) / 200)
    bump = (nz(x, 0, z, 40, 3) - .5) * 3.0 * smooth((d - 95) / 60)
    dp = math.hypot(x - POND_C[0], z - POND_C[1])
    dish = 2.6 * (1 - smooth((dp - (POND_R - 4.0)) / 4.5))
    return -.05 + rise + bump - dish

# ------------------------------------------------------------------ instancing (same scheme as the examples)
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []
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
        hs = [H(x, z)] + [H(x + math.cos(a) * fr, z + math.sin(a) * fr) for a in [k * math.tau / 8 for k in range(8)]]
        y = min(hs) - sink * s
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def reserve(x, z, r): PTS.append((x, z, r))
STATIC_TRIS = {}
def static(name, mb, group):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    STATIC_TRIS[name] = mb.tris
def to_world(local, pos, yaw):
    return Vector(pos) + Matrix.Rotation(math.radians(yaw), 3, 'Y') @ Vector(local)

ANCHORS = []
def anchor(name, kind, p, yaw=0.0, size=(4, 1, 4)):
    ANCHORS.append({'name': name, 'kind': kind, 'pos': [round(p[0], 2), round(p[1], 2), round(p[2], 2)], 'yaw': round(yaw % 360, 1), 'size': list(size)})

# ------------------------------------------------------------------ floors (static, walkable)
def inset_top(bm, th=.08, depth=-.05):
    fs = [f for f in bm.faces]
    for f in fs:
        f.normal_update()
        if f.normal.y < 0: f.normal_flip()
    bmesh.ops.inset_individual(bm, faces=fs, thickness=th, depth=depth, use_even_offset=True)
    bm.normal_update()

def polar_tiles(mb, r0, r1, y, dr, dl, colfn, seed=0, a0=0.0, a1=360.0):
    """flat tiles in rings r0..r1 (ring width dr, tile length ~dl along the ring), each inset; colfn(ring, k, f) -> (col, v)"""
    rng = random.Random(seed); bm = bmesh.new(); meta = []
    r = r0; ring = 0
    while r < r1 - .05:
        rb = min(r + dr, r1); C = D2R(a1 - a0) * (r + rb) / 2; n = max(3, round(C / dl))
        off = rng.uniform(0, 1) * (a1 - a0) / n if a1 - a0 >= 359.9 else 0
        for k in range(n):
            aa = a0 + off + (a1 - a0) * k / n; ab = a0 + off + (a1 - a0) * (k + 1) / n
            m = max(1, int((ab - aa) / 4) + 1); angs = [lerp(aa, ab, q / m) for q in range(m + 1)]
            pts = [pol(t, r) for t in angs] + [pol(t, rb) for t in reversed(angs)]
            f = bm.faces.new([bm.verts.new((x, y, z)) for x, z in pts]); meta.append((f, ring, k))
        r = rb; ring += 1
    keep = {f: (rg, k) for f, rg, k in meta}
    inset_top(bm)
    def sh(f):
        c = f.calc_center_median()
        rr = math.hypot(c.x, c.z); rg = int((rr - r0) / dr); k = int((math.degrees(math.atan2(c.z, c.x)) % 360) / 6)
        col, v = colfn(rg, k, f)
        if f.normal.y < .9: v -= .18
        return [(U(col), clamp(v, .04, .96))] * len(f.loops)
    mb.add(bm, sh)

def hall_floor():
    """hall floor: slab, cream polar tiles, a teal ring band at r 30, a mint band round the centre inlay (r 14): a white
    disc with the Bloom Paw in coral + mint and an 8-ray star (sky / gold) round it"""
    mb = MB()
    mb.add(LP.lathe([(RR + .2, -1.6), (RR + .2, FL - .02), (0, FL - .02)], 72), sh_val('cream', .5))
    rng = random.Random(3)
    def cfn(rg, k, f):
        h = LP.B.h01(*[round(c, 1) for c in f.calc_center_median()])
        return ('cream', .66 + (h - .5) * .12 + (.08 if (rg + k) % 2 else 0))
    polar_tiles(mb, 15.2, 29.6, FL, 2.4, 3.2, cfn, 1)
    polar_tiles(mb, 31.0, RR + .1, FL, 2.6, 3.4, cfn, 2)
    for r0, r1, col, v in ((29.6, 31.0, 'teal', .5), (14.0, 15.2, 'mint', .55)):
        mb.add(LP.lathe([(r1, FL - .05), (r1, FL + .02), (r0, FL + .02), (r0, FL - .05)], 72), sh_val(col, v))
    mb.add(LP.lathe([(14.0, FL - .05), (14.0, FL), (0, FL)], 64), sh_val('wall', .86))
    y = FL + .03
    for k in range(8):                                                         # star rays
        a = k * 45 + 22.5
        tip = pol(a, 13.4); l = pol(a + 6, 9.6); r = pol(a - 6, 9.6); bc = pol(a, 9.0)
        bm = ngon_prism([bc, r, tip, l][::-1], FL, y); mb.add(bm, sh_val('sky' if k % 2 else 'gold', .6))
    pad = [(math.cos(t) * .62, math.sin(t) * .46) for t in [q * math.tau / 24 for q in range(24)]]
    pad = [(x * (1 - .18 * max(0, -y) / .46), y + .12 * math.cos(2 * math.atan2(y, x)) * (y > 0) - .38) for x, y in pad]
    s = 8.0
    mb.add(ngon_prism([(x * s, -y * s) for x, y in pad], FL, y + .02), sh_val('coral', .6))
    for a, L, cx, cy in ((-38, .78, -.5, .22), (0, .9, 0, .38), (38, .78, .5, .22)):
        mb.add(ngon_prism([(x * s, -y * s) for x, y in LP.leaf_poly(L, .2, 7, a, (cx, cy))], FL, y + .02), sh_val('mint', .6))
    static('Floor_Hall', mb, 'Floors')

def in_wing(x, z):
    if abs(x) > LP.WING_HW: return False
    if z > LP.WING_Z0 + 2: return False
    if z < LP.WING_ZC: return math.hypot(x, z - LP.WING_ZC) < LP.WING_HW
    return True

def wing_floor():
    """lab wing floor: slab, 3-stud square tiles (white / cream checker), a mint border along the walls, a teal runway
    stripe down the axis to the chamber; tiles inside the hall circle are skipped (no overlap)"""
    mb = MB(); ts = 3.0
    poly = LP.wing_outline(20)
    poly2 = [(x * (LP.WING_HW + .3) / LP.WING_HW, z) for x, z in poly]
    poly2 = [(x, z + 3.0 if z == LP.WING_Z0 else z) for x, z in poly2]
    mb.add(ngon_prism(poly2, -1.6, FL - .03), sh_val('cream', .5))
    bm = bmesh.new()
    for i in range(-8, 8):
        for j in range(0, 28):
            x0, x1 = i * ts, (i + 1) * ts; z0 = -33.0 - j * ts; z1 = z0 - ts
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            if math.hypot(cx, cz) < RR + 1.0 or not in_wing(cx, cz): continue
            corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
            if not all(in_wing(x, z) or math.hypot(x, z) < RR + 1.4 for x, z in corners): continue
            bm.faces.new([bm.verts.new((x, FL, z)) for x, z in corners])
    inset_top(bm, .07, -.04)
    def sh(f):
        c = f.calc_center_median(); i = math.floor(c.x / ts); j = math.floor(c.z / ts)
        if abs(c.x) < 3.0: col, v = 'teal', .55
        elif abs(c.x) > LP.WING_HW - 3.0 or (c.z < LP.WING_ZC and math.hypot(c.x, c.z - LP.WING_ZC) > LP.WING_HW - 3.0): col, v = 'mint', .58
        else: col, v = ('wall' if (i + j) % 2 else 'cream'), (.86 if (i + j) % 2 else .7)
        if f.normal.y < .9: v -= .2
        return [(U(col), clamp(v, .04, .96))] * len(f.loops)
    mb.add(bm, sh)
    static('Floor_Wing', mb, 'Floors')

# ------------------------------------------------------------------ exterior hardscape
FORE_C, FORE_R = (0.0, 44.0), 34.0
def path_z_y(z):                                                              # path height: forecourt -> spawn plaza
    return lerp(FORE_Y, SPAWN_Y, smooth((z - (FORE_C[1] + FORE_R - 2)) / 28))

def hardscape():
    """forecourt terrace (half disc in front of the facade, radial pavers, white kerb + teal edge), the path south with
    mint edge strips, the round spawn plaza with a compass-free ring inlay (paw at its centre)"""
    mb = MB(); cx, cz = FORE_C
    # forecourt: radial pavers on a raised slab, angles 0..180 (south half)
    def cfn(rg, k, f):
        h = LP.B.h01(*[round(c, 1) for c in f.calc_center_median()])
        return ('paving', .72 + (h - .5) * .1 + (.06 if (rg + k) % 2 else 0))
    bm0 = MB()
    polar_tiles(bm0, .4, FORE_R, FORE_Y, 2.6, 3.2, cfn, 5, 0, 180)               # the whole half disc (was r0 > r1: no tiles)
    keep = [i for i, f in enumerate(bm0.F) if any(math.hypot(bm0.V[j][0] + cx, bm0.V[j][2] + cz) > RR + LP.ROT_T for j in f)]
    bm0.F = [bm0.F[i] for i in keep]; bm0.UV = [bm0.UV[i] for i in keep]; bm0.SM = [bm0.SM[i] for i in keep]   # not under the hall wall
    for i, v in enumerate(bm0.V): bm0.V[i] = (v[0] + cx, v[1], v[2] + cz)
    mb.merge(bm0)
    mb.add(LP.T(LP.ring_seg(.4, RR + 1.2, -1.0, FORE_Y - .02, 0, 180, 48), (cx, 0, cz)), sh_val('paving', .5))   # slab: no hole under the forecourt
    mb.add(LP.T(LP.ring_seg(FORE_R - .05, FORE_R + .9, -.6, FORE_Y + .3, 0, 180, 48), (cx, 0, cz)), sh_val('wall', .84))
    mb.add(LP.T(LP.ring_seg(FORE_R + .9, FORE_R + 1.3, -.4, FORE_Y - .2, 0, 180, 48), (cx, 0, cz)), sh_val('teal', .45))
    for sx in (-1, 1):                                                        # side walls of the terrace (flat ends)
        mb.add(LP.T(LP.rbox((FORE_R - RR + .5, FORE_Y + .9, 1.0), .2), (sx * (RR + FORE_R) / 2 + sx * .2, (FORE_Y - .4) / 2, cz - .4)), sh_val('wall', .82))
    # path: from the forecourt edge (z ~ 78) to the spawn plaza (z ~ 106), pavers 2.4 long, 11 wide, mint edges
    z0, z1, hw = cz + FORE_R - 1.0, SPAWN[2] - 11.0, 5.5
    bm = bmesh.new(); n = int((z1 - z0) / 2.4)
    for i in range(n):
        za, zb = z0 + i * (z1 - z0) / n, z0 + (i + 1) * (z1 - z0) / n
        for xa, xb in ((-hw, -hw / 3), (-hw / 3, hw / 3), (hw / 3, hw)):
            bm.faces.new([bm.verts.new((x, path_z_y(z) + .02, z)) for x, z in ((xa, za), (xb, za), (xb, zb), (xa, zb))])
    inset_top(bm, .07, -.05)
    mb.add(bm, lambda f: [(U('paving'), clamp(.74 + (LP.B.h01(*[round(c, 1) for c in f.calc_center_median()]) - .5) * .1 - (.18 if f.normal.y < .9 else 0), .04, .96))] * len(f.loops))
    for sx in (-1, 1):
        pts = [(sx * (hw + .5), path_z_y(z) - .1, z) for z in [lerp(z0 - 1, z1 + 1, t / 12) for t in range(13)]]
        mb.add(LP.tube([Vector(p) for p in pts], .55, sides=4, flat=(1.0, .5)), sh_val('mint', .55))
    ys = [path_z_y(z) for z in [lerp(z0, z1, t / 12) for t in range(13)]]
    sl = bmesh.new()                                                          # path bed (sides down into the lawn)
    for t in range(12):
        za, zb = lerp(z0, z1, t / 12), lerp(z0, z1, (t + 1) / 12)
        for x in (-hw - .2, hw + .2):
            sl.faces.new([sl.verts.new(p) for p in ((x, ys[t], za), (x, ys[t + 1], zb), (x, -1.0, zb), (x, -1.0, za))])
    mb.add(sl, sh_val('paving', .45))
    # spawn plaza
    sx_, sy_, sz_ = SPAWN
    bm0 = MB()
    def cfn2(rg, k, f): return ('paving', .7 + (.08 if (rg + k) % 2 else 0) + (LP.B.h01(*[round(c, 1) for c in f.calc_center_median()]) - .5) * .08)
    polar_tiles(bm0, 4.0, 13.0, sy_ + .02, 3.0, 3.0, cfn2, 7)
    for i, v in enumerate(bm0.V): bm0.V[i] = (v[0] + sx_, v[1], v[2] + sz_)
    mb.merge(bm0)
    mb.add(LP.T(LP.lathe([(4.0, -.05), (4.0, .05), (0, .05)], 24), (sx_, sy_, sz_)), sh_val('mint', .58))
    mb.add(LP.T(LP.lathe([(13.0, -1.0), (13.0, .0), (0, .0)], 40), (sx_, sy_, sz_)), sh_val('paving', .5))
    mb.add(LP.T(LP.torus(13.2, .35, 40, 5), (sx_, sy_ + .05, sz_)), sh_val('wall', .85))
    pad = LP.Prop('_pad'); LP.emblem(pad, (0, 0, 0), 0, 2.4, .1)
    for i, v in enumerate(pad.solid.V):                                       # lay the paw flat in the plaza centre
        pad.solid.V[i] = (sx_ - v[0], sy_ + .02 - v[2], sz_ - v[1])            # upright -> flat (a rotation: top points north)
    mb.merge(pad.solid)
    static('Hardscape_Plaza', mb, 'Outside')

def ground():
    """lawn grid: 3-stud cells near the building, coarse to the hills; holes under the building, forecourt and plaza;
    colour by height + noise, darker under the wall foot"""
    fine = [x * 3.0 for x in range(-50, 51)]
    xs = [x for x in range(-700, -150, 50)] + fine + [x for x in range(200, 701, 50)]
    zs = [z for z in range(-700, -180, 50)] + [z * 3.0 for z in range(-58, 51)] + [z for z in range(200, 701, 50)]
    bm = bmesh.new(); VV = {}
    def v(i, j):
        if (i, j) not in VV: VV[i, j] = bm.verts.new((xs[i], H(xs[i], zs[j]), zs[j]))
        return VV[i, j]
    def hidden(cx, cz):
        if math.hypot(cx, cz) < RR + 1.0: return True
        if in_wing(cx, cz) or (abs(cx) < LP.WING_HW + .8 and LP.WING_ZC < cz < -30): return True
        if cz > FORE_C[1] - 1 and math.hypot(cx - FORE_C[0], cz - FORE_C[1]) < FORE_R + .5: return True
        if math.hypot(cx - SPAWN[0], cz - SPAWN[2]) < 12.5: return True
        if abs(cx) < 5.5 and FORE_C[1] + FORE_R - 2 < cz < SPAWN[2] - 10: return True
        return False
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if hidden(cx, cz): continue
            f = bm.faces.new((v(i, j), v(i, j + 1), v(i + 1, j + 1), v(i + 1, j))); f.normal_update()
            if f.normal.y < 0: f.normal_flip()
    def sh(f):
        out = []; c = f.calc_center_median(); bed = math.hypot(c.x - POND_C[0], c.z - POND_C[1]) < POND_R - .5
        for l in f.loops:
            p = l.vert.co
            if bed:                                                            # pond bed (whole face, no mixed columns)
                out.append((U('teal'), clamp(.42 + p.y * .05, .04, .96))); continue
            d = math.hypot(p.x, (p.z + 20) * .85)
            stripe = (.035 if int((p.x + 1000) / 9) % 2 else -.035) * (1 - smooth((d - 120) / 40))
            vv = .5 + (nz(p.x, 0, p.z, 18, 5) - .5) * .18 + .04 * smooth(p.y / 20) + stripe
            out.append((U('grass'), clamp(vv, .04, .96)))
        return out
    mb = MB(); mb.add(bm, sh, smooth=True); static('Ground_Lawn', mb, 'Ground')

# ------------------------------------------------------------------ interior stations
CEIL = FL + LP.WALL_H
def ceil_y(r):
    """underside of the rotunda roof at radius r (matches rotunda_roof's inner profile, approx)"""
    yb = FL + LP.WALL_H; ro = RR + LP.ROT_T + 2.0; rk = 13.0; yk = yb + 9.0
    t = clamp((ro - r) / (ro - rk))
    return yb + .3 + (yk - yb - .3) * math.sin(t * math.pi / 2) ** 1.4 - 1.4

def stations():
    T = FL
    # ---- Heal (west): machine against the wall, curved nurse counter, med shelves, benches, rest nook
    mp = (-40.2, T, 0.0); place('healmachine', LP.heal_machine, mp[0], mp[2], -90, y=T, group='Heal')
    for k in range(6):
        p = to_world((-5.0 + k * 2.0, 4.6, -.42), mp, -90); anchor('HealSlot%d' % (k + 1), 'healslot', p, -90, (1.4, 1.6, 1.4))
    place('healcounter', LP.heal_counter, -27.0, 0.0, -90, y=T, group='Heal')
    anchor('Heal', 'station', (-27.0, T + 9.0, 0.0), -90)
    anchor('HealCounter', 'counter', (-26.2, T + 2.0, 0.0), -90, (3, 4, 12))
    for a in (163.0, 197.0):
        x, z = pol(a, 42.0); place('medshelf1', lambda: LP.med_shelf(1), x, z, face_in(a), y=T, group='Heal')
    for a in (148.0,):
        x, z = pol(a, 41.0); place('monstera_m', lambda: LP.monstera(1, 'mint'), x, z, 30, y=T, group='Heal')
    for z in (-7.5, 7.5):
        place('benchT', lambda: LP.wait_bench(1, 8.0, 'teal'), -15.0, z, 90, y=T, group='Heal')
    x, z = pol(152.0, 32.0); place('restnook', LP.rest_nook, x, z, face_in(152.0), y=T, group='Heal')
    x, z = pol(127.0, 36.5); place('healcorner', LP.heal_corner, x, z, face_in(127.0), y=T, group='Heal')
    place('rug_m', lambda: LP.round_rug(7.5, 'mint', 'cream'), -15.0, 0.0, 0, y=T + .01, group='Heal')
    place('plush_m', LP.plush, -15.1, 9.5, 70, s=.75, y=T + 2.27, group='Heal')
    x, z = pol(205.0, 41.6); place('cooler', LP.water_cooler, x, z, face_in(205.0), y=T, group='Heal')
    x, z = pol(214.0, 41.6); place('snake_t', lambda: LP.snake_plant(1, 'teal'), x, z, 0, y=T, group='Heal')
    # ---- Mart (east): counter, capsule shelves + potion shelf on the wall, display rack, berry baskets
    place('shopcounter', LP.shop_counter, 27.0, 0.0, 90, y=T, group='Shop')
    anchor('Shop', 'station', (27.0, T + 9.0, 0.0), 90)
    anchor('ShopCounter', 'counter', (25.6, T + 2.0, 0.0), 90, (3, 4, 12))
    for a, key, fn in ((-15.0, 'capshelf', lambda: LP.capsule_shelf(1)), (0.0, 'potshelf', lambda: LP.potion_shelf(2)), (15.0, 'capshelf', lambda: LP.capsule_shelf(1))):
        x, z = pol(a, 41.6); place(key, fn, x, z, face_in(a), y=T, group='Shop')
    place('rack', LP.display_rack, 15.5, 12.5, 30, y=T, group='Shop')
    place('berries', LP.berry_baskets, 17.0, -12.5, 120, y=T, group='Shop')
    x, z = pol(28.5, 41.2); place('snake_c', lambda: LP.snake_plant(2, 'coral'), x, z, 0, y=T, group='Shop')
    x, z = pol(36.0, 36.5); place('supply', LP.supply_boxes, x, z, face_in(36.0) + 180, y=T, group='Shop')
    x, z = pol(331.0, 40.0); place('supply', LP.supply_boxes, x, z, face_in(331.0) + 180, y=T, group='Shop')
    place('salestand', LP.sale_stand, 9.0, 23.0, 200, y=T, group='Shop')
    place('plush_c', lambda: LP.plush('coral', 'mint'), 12.5, 25.5, 160, s=.8, y=T, group='Shop')
    # ---- Storage (north-east): three terminals against the wall
    for i, a in enumerate((294.0, 306.0, 318.0)):
        x, z = pol(a, 40.6); place('pc', LP.pc_terminal, x, z, face_in(a), y=T, group='Storage')
        anchor('PC%d' % (i + 1), 'pc', (x, T + 2.5, z), face_in(a), (3.4, 5, 3.4))
    anchor('Storage', 'station', (*pol(306.0, 38.0)[:1], T + 12.0, pol(306.0, 38.0)[1]), face_in(306.0))
    x, z = pol(286.0, 39.6); place('ffig_m', lambda: LP.fiddle_fig(1, 9.0, 'mint'), x, z, 40, y=T, group='Storage')
    x, z = pol(306.0, 33.8); place('dock', LP.dock_cables, x, z, face_in(306.0), y=T, group='Storage')
    # ---- Trade (north-west)
    a = 228.0; x, z = pol(a, 35.5); place('trade', LP.trade_desk, x, z, face_in(a), y=T, group='Trade')
    anchor('Trade', 'station', (x, T + 11.0, z), face_in(a))
    anchor('TradeDesk', 'counter', tuple(to_world((0, 2.0, -2.0), (x, T, z), face_in(a))), face_in(a), (11, 4, 3))
    x, z = pol(252.0, 41.6); place('vend_s', lambda: LP.vending_machine('sky'), x, z, face_in(252.0), y=T, group='Trade')
    x, z = pol(228.0, 43.2); place('trophy', LP.trophy_shelf, x, z, face_in(228.0), y=T, group='Trade')
    x, z = pol(238.0, 25.5); place('ropeline', LP.rope_line, x, z, face_in(238.0) + 90, y=T, group='Trade')
    x, z = pol(243.0, 39.5); place('monstera_c', lambda: LP.monstera(2, 'coral'), x, z, 0, y=T, group='Trade')
    # ---- centre + entry + lab portal
    for a in (45, 135, 225, 315):
        x, z = pol(a, 18.5)
        if a in (45, 225): place('ffig_t', lambda: LP.fiddle_fig(2, 8.0, 'teal'), x, z, a * 2, y=T, group='Centre')
        else: place('olive_t', lambda: LP.olive_tree(2, 8.0, 'teal'), x, z, a, y=T, group='Centre')
    for a in (45, 135, 225, 315):
        x, z = pol(a, 36.0); place('hang_c', lambda: LP.hanging_planter(5.5, 'coral', 2), x, z, a, y=LP.roof_in_y(36.0) - .3, group='Lamps')
    place('mat', LP.floor_mat, 0.0, 38.0, 0, y=T + .01, group='Centre')
    place('clock', LP.wall_clock, *pol(180.0, 43.4), face_in(180.0), y=T + 16.5, group='Decor')
    for a, sd in ((162.0, 1), (198.0, 2), (288.0, 3), (306.0, 1)):
        x, z = pol(a, 43.75); place('art%d' % sd, (lambda sd=sd: LP.art_frame(sd)), x, z, face_in(a), y=T + (14.0 if a in (162.0, 198.0) else 12.5), group='Decor')
    for a in (18.0, 342.0):
        x, z = pol(a, 43.3); place('wallcaps', LP.wall_capsules, x, z, face_in(a), y=T + 14.5, group='Decor')
    place('halltrim', LP.hall_trim, 0, 0, 0, y=0, group='Interior')
    place('wingtrim', LP.wing_trim, 0, 0, 0, y=0, group='Interior')
    place('ceiling', LP.hall_ceiling, 0, 0, 0, y=0, group='Roof')
    place('doors', LP.sliding_doors, 0.0, RR + LP.ROT_T / 2, 180, y=T, group='Entrance')
    for sx in (-1, 1):
        anchor('DoorLeaf%s' % ('L' if sx < 0 else 'R'), 'door', (sx * 3.5, T + 6.5, RR + LP.ROT_T / 2), 0, (7, 13, .4))
    place('canopy', LP.entrance_canopy, 0.0, RR + LP.ROT_T + .2, 180, y=T, group='Entrance')
    place('archway', LP.lab_archway, 0.0, -(RR + LP.ROT_T / 2), 180, y=T, group='Lab')
    for k in range(8):                                                         # pendant lamps on a ring
        a = k * 45 + 22.5; r = 28.0; x, z = pol(a, r)
        place('lamp_h', lambda: LP.pendant_lamp(7.0, 'mint'), x, z, 0, y=LP.roof_in_y(r) - .9, group='Lamps')   # hangs just under the ring beam
    # ---- Lab wing
    ez = LP.WING_ZC - 1.0
    place('evo', LP.evo_chamber, 0.0, ez, 180, y=T, group='Lab')
    anchor('Lab', 'station', (0.0, T + 21.0, ez), 180)
    anchor('ChamberPad', 'chamber', (0.0, T + 2.0, ez), 180, (12, 4, 12))
    for sx in (-1, 1):
        for i, z in enumerate((-50.0, -62.0, -74.0)):
            key = 'tankA' if (i + (sx > 0)) % 2 == 0 else 'tankB'
            place(key, (lambda: LP.specimen_tank('liquid', 1)) if key == 'tankA' else (lambda: LP.specimen_tank('liquid2', 2)),
                  sx * 20.6, z, 90 if sx > 0 else -90, y=T, group='Lab')
    st = (0.0, -60.0); place('starter', LP.starter_table, st[0], st[1], 180, y=T, group='Lab')
    anchor('Starter', 'station', (st[0], T + 10.0, st[1]), 180)
    for k, tier in enumerate(('mint', 'coral', 'sky')):
        a = math.radians(-90 + (k - 1) * 50); lx, lz = math.cos(a) * 2.9, math.sin(a) * 2.9
        p = to_world((lx, 5.4, lz), (st[0], T, st[1]), 180); anchor('Starter_%s' % tier.capitalize(), 'starter', p, 0, (2, 2.6, 2))
    place('bench1', lambda: LP.workbench(1), -11.0, -47.0, 180, y=T, group='Lab')
    place('bench1', lambda: LP.workbench(1), 11.0, -47.0, 180, y=T, group='Lab')
    place('micro', LP.microscope_bench, -16.5, -84.0, -90, y=T, group='Lab')
    place('board', LP.whiteboard, 17.0, -84.0, 90, y=T, group='Lab')
    for sx in (-1, 1):
        x = sx * 16.0; z = -math.sqrt((RR + LP.ROT_T) ** 2 - x * x) - 1.6
        place('labshelf', LP.wall_shelf_lab, x, z, 0, y=T, group='Lab')
    for x, z in ((-20.5, -88.0), (20.5, -88.0), (-6.5, -39.5), (6.5, -39.5)):
        place('snake_m', lambda: LP.snake_plant(3, 'mint'), x, z, 0, y=T, group='Lab')
    place('rug_t', lambda: LP.round_rug(7.5, 'teal', 'cream'), 0.0, -60.0, 0, y=T + .01, group='Lab')
    place('clock', LP.wall_clock, -(LP.WING_HW - .2), -45.0, -90, y=T + 13.0, group='Decor')
    place('art2', lambda: LP.art_frame(2), LP.WING_HW - .2, -45.0, 90, y=T + 9.0, group='Decor')
    place('plush_m', LP.plush, 12.5, -47.9, 150, s=.6, y=T + 3.75, group='Lab')
    for z in (-52.0, -68.0):
        for sx in (-1, 1):
            place('lamp_w', lambda: LP.pendant_lamp(5.0, 'teal'), sx * 10.0, z, 0, y=FL + LP.WING_H - 1.0, group='Lamps')
    place('wingroof', LP.wing_roof, 0, 0, 0, y=0, group='Roof')
    # the rotunda roof is part of the Rotunda prop (LP.rotunda merges it): a roof rests on its walls
    place('rotunda', LP.rotunda, 0, 0, 0, y=0, group='Building')
    place('labwing', LP.lab_wing, 0, 0, 0, y=0, group='Building')

# ------------------------------------------------------------------ designed garden (exterior)
POND_C, POND_R = (-92.0, 18.0), 15.0
LOOP = [(-35.5, 47), (-50, 33), (-60, 8), (-61, -25), (-55, -62), (-42, -102), (-22, -128), (0, -136), (22, -128), (42, -102),
        (55, -62), (61, -25), (60, 8), (50, 33), (35.5, 47)]
POND_LINK = [(-60.5, 2), (-69, 6), (-76, 12)]
SPAWN_LINK = [(-12.5, 116), (-30, 108), (-46, 90), (-55, 62), (-56, 40)]          # spawn plaza -> west loop (curving)
WALL_RX, WALL_RZ, WALL_CZ = 128.0, 168.0, -20.0

def catmull(pts, n=6, closed=False):
    P = [Vector((x, 0, z)) for x, z in pts]; out = []
    for i in range(len(P) - 1):
        p0 = P[max(i - 1, 0)]; p1, p2 = P[i], P[i + 1]; p3 = P[min(i + 2, len(P) - 1)]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1]); return out

def near_poly(x, z, pts, w):
    for a, b in zip(pts, pts[1:]):
        ax, az = a.x, a.z; bx, bz = b.x, b.z; dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz or 1e-6
        t = clamp(((x - ax) * dx + (z - az) * dz) / L2); px, pz = ax + dx * t, az + dz * t
        if (x - px) ** 2 + (z - pz) ** 2 < w * w: return True
    return False

GARDEN_PATHS = []
def garden_paths(mb):
    """curving garden paths (ribbon pavers with mint edging) round the building, to the pond and from the spawn"""
    for pts, w in ((LOOP, 6.0), (POND_LINK, 5.0), (SPAWN_LINK, 5.0)):
        c = catmull(pts, 8); GARDEN_PATHS.append((c, w))
        L = [0.0]
        for a, b in zip(c, c[1:]): L.append(L[-1] + (b - a).length)
        bm = bmesh.new(); prev = None
        for i, p in enumerate(c):
            a = c[max(i - 1, 0)]; b = c[min(i + 1, len(c) - 1)]; t = (b - a).normalized(); n = Vector((-t.z, 0, t.x)) * w / 2
            y = H(p.x, p.z) + .12
            row = [bm.verts.new((p.x + n.x, y, p.z + n.z)), bm.verts.new((p.x - n.x, y, p.z - n.z))]
            if prev: bm.faces.new((prev[0], prev[1], row[1], row[0]))
            prev = row
        mb.add(bm, lambda f: [(U('paving'), clamp(.72 + (.06 if int(f.calc_center_median().x * .5 + f.calc_center_median().z * .5) % 2 else 0) + (.1 if f.normal.y < 0 else 0), .04, .96))] * len(f.loops))
        for sd in (-1, 1):
            e = []
            for i, p in enumerate(c):
                a = c[max(i - 1, 0)]; b = c[min(i + 1, len(c) - 1)]; t = (b - a).normalized(); n = Vector((-t.z, 0, t.x)) * (w / 2 + .25) * sd
                e.append(Vector((p.x + n.x, H(p.x + n.x, p.z + n.z) + .05, p.z + n.z)))
            mb.add(LP.tube(e, .32, sides=4, flat=(1.0, .6)), sh_val('mint', .55))

def pond(mb):
    """pond: water disc (Glass) over the carved dish, a ring of smooth rim stones half sunk in the lawn"""
    rng = random.Random(14); cx, cz = POND_C
    bm = bmesh.new(); ring = [bm.verts.new((cx + math.cos(t) * (POND_R + .6), -.55, cz + math.sin(t) * (POND_R + .6))) for t in [k * math.tau / 40 for k in range(40)]]
    f = bm.faces.new(ring); f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    w = MB(); w.add(bm, lambda f: [(U('glass'), .55)] * len(f.loops)); static('Pond_Water', w, 'Garden')
    bed = bmesh.new(); f = bed.faces.new([bed.verts.new((cx + math.cos(t) * (POND_R + 1.5), -2.8, cz + math.sin(t) * (POND_R + 1.5))) for t in [k * math.tau / 24 for k in range(24)]])
    f.normal_update()
    if f.normal.y < 0: f.normal_flip()
    mb.add(bed, sh_val('teal', .4))                                           # pond bed under the dish: every water point has a floor within 8
    for k in range(30):
        a = k * math.tau / 30 + rng.uniform(-.05, .05); r = rng.uniform(1.0, 1.7)
        x, z = cx + math.cos(a) * (POND_R + .8), cz + math.sin(a) * (POND_R + .8)
        b = LP.T(LP.ball(r, 9, 5), (x, H(x, z) - .2, z), rng.uniform(0, 360), 0, 0, (1.3, .5, 1.0))
        mb.add(b, lambda f, v=rng.uniform(.6, .78): [(U('paving'), clamp(v + .1 * f.normal.y, .04, .96))] * len(f.loops), smooth=True)

def horizon():
    """distant scenery: soft rounded hills in two layers beyond the lawn (cooler + lighter with distance), dotted with
    round tree balls, a far blue ridge"""
    mb = MB(); rng = random.Random(31)
    for layer, (d0, d1, n, hr, col, v) in enumerate(((560, 640, 16, (40, 80), 'grass', .5), (700, 780, 14, (70, 140), 'leaf', .62))):
        for k in range(n):
            a = k * math.tau / n + rng.uniform(-.1, .1); d = rng.uniform(d0, d1); R = rng.uniform(120, 190); h = rng.uniform(*hr)
            cx, cz = math.cos(a) * d, math.sin(a) * d - 20
            prof = [(R, -10)] + [(R * math.cos(math.pi / 2 * j / 6), h * math.sin(math.pi / 2 * j / 6)) for j in range(1, 6)] + [(0, h)]
            bm = LP.T(LP.lathe(prof, 16), (cx, H(cx, cz) - 6, cz))
            mb.add(bm, lambda f, v=v: [(U(col), clamp(v + .12 * f.normal.y, .04, .96))] * len(f.loops), smooth=True)
            if layer == 0:
                for j in range(3):
                    b = rng.uniform(0, math.tau); rr = rng.uniform(.2, .7) * R
                    y = h * math.sqrt(max(0, 1 - (rr / R) ** 2)) + H(cx, cz) - 6
                    mb.add(LP.T(LP.ball(rng.uniform(9, 14), 8, 5), (cx + math.cos(b) * rr, y + 4, cz + math.sin(b) * rr)), lambda f: [(U('leaf'), clamp(.4 + .15 * f.normal.y, .04, .96))] * len(f.loops), smooth=True)
    static('Horizon_Hills', mb, 'Horizon')

def path_free(x, z, w):
    if any(near_poly(x, z, c, ww / 2 + w) for c, ww in GARDEN_PATHS): return False
    if math.hypot(x - POND_C[0], z - POND_C[1]) < POND_R + 2 + w: return False
    return True

def exterior(rng):
    cz = FORE_C[1]
    for sx in (-1, 1):
        place('fountain', LP.capsule_statue, sx * 14.5, cz + 19.0, 0, s=.72, y=FORE_Y - .05, group='Plaza'); reserve(sx * 14.5, cz + 19, 7)
        a = 90 + sx * 47; x, z = pol(a, FORE_R - 3.2)
        place('pbench', LP.ext_bench, x, z + cz, face_in(a), y=FORE_Y, group='Plaza')
        place('lamp', LP.lamp_post, sx * 9.5, cz + FORE_R - 3.5, 0, y=FORE_Y, group='Plaza')
        place('vend_c', lambda: LP.vending_machine('coral'), sx * 15.5, cz + 6.5, 180, y=FORE_Y, group='Plaza')
        place('lplanter', lambda: LP.long_planter(12.0, 1), sx * 26.0, cz + 4.5, 180 + sx * 30, y=FORE_Y, group='Plaza')
        for z in (88.0, 98.0, 106.0):                                          # bollards along the path
            place('bollard', LP.bollard_light, sx * 7.4, z, 0, y=path_z_y(z) - .1, group='Path')
        place('lamp', LP.lamp_post, sx * 9.0, 94.0, 0, group='Path')
        for z in (85.0, 100.5):                                                 # trimmed hedges lining the entry path
            place('topi8', lambda: LP.topiary_hedge(8.0, 1), sx * 11.5, z, 90, group='Path'); reserve(sx * 11.5, z, 4)
        for k in range(3):                                                      # hedges framing the forecourt arc (14 deg = 9.3 studs apart: no overlap)
            a = 90 + sx * (56 + k * 14.0); x, z = pol(a, FORE_R + 4.0)
            place('topi8', lambda: LP.topiary_hedge(8.0, 1), x, z + cz, face_in(a), y=FORE_Y, group='Garden'); reserve(x, z + cz, 4)   # on the paving band
    place('sign', LP.welcome_sign, -19.0, 109.0, -123, group='Spawn'); reserve(-19, 109, 6)
    anchor('SpawnLocation', 'spawn', (SPAWN[0], SPAWN_Y + .5, SPAWN[2]), 0, (10, 1, 10))
    anchor('WelcomeSign', 'sign', tuple(to_world((0, 3.6, -1.0), (-19.0, SPAWN_Y, 109.0), -123)), -123, (7.4, 3, .4))
    for sx in (-1, 1):
        place('rplanter2', lambda: LP.round_planter(2, 2.6, 'gold'), sx * 15.0, SPAWN[2] + 7.0, 0, group='Spawn'); reserve(sx * 15, SPAWN[2] + 7, 4)
        place('pbench', LP.ext_bench, sx * 12.0, SPAWN[2] - 2.5, sx * 90 + 0, y=SPAWN_Y, group='Spawn')
        place('topi8', lambda: LP.topiary_hedge(8.0, 1), sx * 18.5, SPAWN[2] + 1.0, 90, group='Spawn'); reserve(sx * 18.5, SPAWN[2] + 1, 4)
    for loc, _t, _f, _r in SHOTS.values(): reserve(loc[0], loc[2], 4)
    # building foot: soft bushes + flower beds round the hall and wing
    for a in range(146, 400, 16):
        aa = a % 360
        if 246 < aa < 294: continue
        x, z = pol(aa, RR + LP.ROT_T + 3.4)
        if not free(x, z, 2.0): continue
        if (a // 16) % 2: place('rbush_b', lambda: LP.round_bush(1, 1.8, 'berry'), x, z, rng.uniform(0, 360), group='Garden')
        else: place('fbed%d' % ((a // 16) % 3 + 1), (lambda sd=(a // 16) % 3 + 1: LP.flower_bed(sd, 6.0, 2.6)), x, z, face_in(aa), group='Garden')
        reserve(x, z, 2.2)
    for sx in (-1, 1):
        for z in (-48.0, -64.0, -80.0, -96.0):
            x = sx * (LP.WING_HW + LP.WING_T + 3.2)
            if (int(-z) // 16) % 2: place('rbush_g', lambda: LP.round_bush(2, 1.8, 'gold'), x, z, rng.uniform(0, 360), group='Garden')
            else: place('fbed3', lambda: LP.flower_bed(3, 6.0, 2.6), x, z, 90, group='Garden')
            reserve(x, z, 2.5)
    # flower beds along the loop path (outer side, palette colours in turn) + bushes on the inner side
    c, w = GARDEN_PATHS[0]
    for i in range(6, len(c) - 6, 15):
        p = c[i]; t = (c[i + 1] - c[i - 1]).normalized(); n = Vector((-t.z, 0, t.x))
        out = n if (p + n).length > p.length else -n
        q = p + out * (w / 2 + 3.4)
        if free(q.x, q.z, 3) and path_free(q.x, q.z, 1.5):
            place('fbed%d' % (i % 3 + 1), (lambda sd=i % 3 + 1: LP.flower_bed(sd, 8.0, 3.2)), q.x, q.z, math.degrees(math.atan2(-t.z, t.x)) + 90, group='Garden'); reserve(q.x, q.z, 3.5)
        q = p - out * (w / 2 + 2.6)
        if i % 24 == 6 and free(q.x, q.z, 2.5) and path_free(q.x, q.z, 1.2):
            place('rbush_b', lambda: LP.round_bush(1, 1.8, 'berry'), q.x, q.z, rng.uniform(0, 360), group='Garden'); reserve(q.x, q.z, 2.5)
    # pond: lily pads, reeds, stepping stones on the lawn side, a bench looking over it
    px, pz = POND_C
    for k, (a, d) in enumerate(((.3, 6.0), (2.2, 8.0), (4.1, 5.0))):
        place('lily%d' % (k % 2 + 1), (lambda k=k: LP.lily_pads(k % 2 + 1)), px + math.cos(a) * d, pz + math.sin(a) * d, rng.uniform(0, 360), y=-.5, group='Pond')
    for a in (1.2, 1.6, 3.4, 3.9, 5.2):
        place('reeds1', lambda: LP.reeds(1), px + math.cos(a) * (POND_R - .6), pz + math.sin(a) * (POND_R - .6), rng.uniform(0, 360), y=-1.0, group='Pond')
    for k in range(4):
        x, z = px + 17.5 + k * 2.6, pz - 9.0 - k * 1.2
        place('stone', LP.stepping_stone, x, z, rng.uniform(0, 360), group='Pond'); reserve(x, z, 1.5)
    place('pbench', LP.ext_bench, px + 4.0, pz - 19.5, 160, group='Pond'); reserve(px + 4, pz - 19.5, 4)
    # rounded trees in designed groups (odd counts), blossom accents, low bushes at their feet
    GROUPS = [(-82, -38, 3), (-80, -95, 1), (-36, -160, 1), (40, -158, 1), (84, -88, 3), (-112, 34, 2), (92, 52, 1), (-62, 92, 1)]
    TREES = {'rt1': lambda: LP.park_tree(1, 17.0), 'rt2': lambda: LP.park_tree(2, 20.0), 'rt3': lambda: LP.park_tree(3, 15.0), 'bl1': lambda: LP.blossom_park(4, 14.0)}
    for gi, (gx, gz, n) in enumerate(GROUPS):
        for k in range(n):
            for _ in range(20):
                a = rng.uniform(0, math.tau); d = 0 if k == 0 else rng.uniform(7, 11)
                x, z = gx + math.cos(a) * d, gz + math.sin(a) * d
                if free(x, z, 3.6) and path_free(x, z, 4): break
            else: continue
            key = 'bl1' if (k == n - 1 and n >= 3 and gi % 2 == 0) else rng.choice(('rt1', 'rt2', 'rt3'))
            place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(.9, 1.15), group='Trees'); reserve(x, z, 3.6)
        for k in range(1 if n >= 3 else 0):
            a = rng.uniform(0, math.tau); x, z = gx + math.cos(a) * 12, gz + math.sin(a) * 12
            if free(x, z, 2.5) and path_free(x, z, 1.5): place('rbush_g', lambda: LP.round_bush(2, 1.8, 'gold'), x, z, rng.uniform(0, 360), group='Trees'); reserve(x, z, 2.5)
    # boundary: low garden wall on an ellipse, a gate gap on the south axis
    C = WALL_RX * WALL_RZ; n = 46
    for k in range(n):
        t0, t1 = k * math.tau / n, (k + 1) * math.tau / n
        a = Vector((math.cos(t0) * WALL_RX, 0, WALL_CZ + math.sin(t0) * WALL_RZ)); b = Vector((math.cos(t1) * WALL_RX, 0, WALL_CZ + math.sin(t1) * WALL_RZ))
        m = (a + b) / 2
        if abs(m.x) < 10 and m.z > 0: continue
        d = b - a; L = d.length
        place('gwall', lambda: LP.garden_wall(14.0), m.x, m.z, math.degrees(math.atan2(-d.z, d.x)), s=L / 15.4, group='Boundary')
    # outside the wall: a few far groups on the slopes so the edge is not a hard line
    for k in range(2):
        a = k * math.tau / 2 + .3 + rng.uniform(-.1, .1); d = rng.uniform(1.12, 1.35)
        x, z = math.cos(a) * WALL_RX * d, WALL_CZ + math.sin(a) * WALL_RZ * d
        key = rng.choice(('rt1', 'rt2')); place(key, TREES[key], x, z, rng.uniform(0, 360), s=rng.uniform(1.1, 1.4), group='Trees')
    for k, (a, d, y, s) in enumerate(((200, 520, 140, 2.0), (250, 600, 170, 2.6), (300, 560, 150, 2.2), (340, 640, 175, 2.4), (150, 620, 160, 2.3), (40, 600, 150, 2.0), (100, 650, 180, 2.5))):
        x, z = pol(a, d); place('cloud%d' % (k % 3 + 1), (lambda k=k: LP.cloud(k % 3 + 1)), x, z, rng.uniform(0, 360), y=y, s=s, group='Sky')

def build():
    hall_floor(); wing_floor(); hardscape()
    mb = MB(); garden_paths(mb); pond(mb); static('Hardscape_Garden', mb, 'Garden')
    ground(); horizon()
    stations(); exterior(random.Random(9))

# ------------------------------------------------------------------ look: bright clean late morning
def look():
    w = bpy.data.worlds.new('Clear'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = .0; cr.elements[0].color = (.72, .9, 1.0, 1)
    cr.elements[1].position = .55; cr.elements[1].color = (.12, .42, .92, 1)
    e = cr.elements.new(.12); e.color = (.45, .74, 1.0, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .2; b.inputs['Roughness'].default_value = .7
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.4; sun.data.color = (1.0, .96, .9); sun.data.angle = math.radians(2.0)
    el = math.radians(48); az = math.radians(140)
    to_sun = r2b((math.cos(el) * math.sin(az), math.sin(el), -math.cos(el) * math.cos(az))) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.objects.new('SkyFill', bpy.data.lights.new('SkyFill', 'SUN')); SC.collection.objects.link(fill)
    fill.data.energy = 1.0; fill.data.color = (.7, .85, 1.0); fill.data.use_shadow = False
    to_f = r2b((-.4, .8, .3)) - r2b((0, 0, 0)); fill.rotation_euler = (-to_f).to_track_quat('-Z', 'Y').to_euler()
    # interior preview light (Roblox: Ambient + PointLights from the lamps; these only stand in for the bounce)
    for name, p, size, en in (('HallFill', (0, FL + 20, 0), 60, 26000), ('WingFill', (0, FL + 17, -76), 40, 12000)):
        L = bpy.data.lights.new(name, 'AREA'); L.shape = 'DISK'; L.size = size; L.energy = en; L.color = (1.0, .97, .92)
        o = bpy.data.objects.new(name, L); SC.collection.objects.link(o); o.location = r2b(p)
        o.rotation_euler = (0, 0, 0)
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    for k, v in (('taa_render_samples', 48), ('shadow_pool_size', '1024'), ('use_raytracing', True)):
        try: setattr(SC.eevee, k, v)
        except Exception as ex: print('EEVEE', k, ex)

MATERIALS = {'wall': 'SmoothPlastic', 'cream': 'SmoothPlastic', 'mint': 'SmoothPlastic', 'teal': 'SmoothPlastic',
             'coral': 'SmoothPlastic', 'gold': 'SmoothPlastic', 'sky': 'SmoothPlastic', 'steel': 'Metal', 'dark': 'SmoothPlastic',
             'wood': 'WoodPlanks', 'leaf': 'LeafyGrass', 'grass': 'Grass', 'paving': 'Concrete', 'glass': 'Glass', 'berry': 'SmoothPlastic'}
MAT_OVERRIDES = {'Floor_': {'cream': 'Marble', 'wall': 'Marble'}, 'Tree': {'wood': 'Wood'}, 'Cloud': 'SmoothPlastic',
                 'PottedTree': {'wood': 'Wood'}}
def material_skin():
    import roblox_materials as RM
    RM.LOOK['Glass'] = (None, 0, 0, .1, 0, .5)
    RM.preview(F.PAL, F.materials()['pal'], MATERIALS, skip=('Horizon',), overrides=MAT_OVERRIDES)
    RM.write_map(F.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=MAT_OVERRIDES)
    m = bpy.data.materials.get('RBX_Glass')
    if m:
        bsdf = m.node_tree.nodes['Principled BSDF']; bsdf.inputs['Alpha'].default_value = .22
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
        try: m.use_backface_culling = False
        except Exception: pass
    for k in ('liquid', 'liquid2'):                                            # liquid glow: see-through (Roblox: Transparency .4)
        m = F.materials().get(k)
        if m:
            m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = .55
            try: m.surface_render_method = 'BLENDED'
            except Exception: m.blend_method = 'BLEND'

def set_roof(visible):
    for o in sub('Roof').objects: o.hide_render = not visible

def shot(name, loc, tgt, fov=35, res=(1920, 1080), roof=True):
    set_roof(roof)
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(fov)
    cam.data.clip_end = 6000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)
    set_roof(True)

SHOTS = {   # vertical FOV (Roblox-style); roof False = cutaway
    'map_beauty.png': ((9, FL + 11, 34), (-2, FL + 6, -50), 50, True),
    'map_overview.png': ((95, 125, 140), (0, 0, -30), 40, False),
    'map_top.png': ((0, 420, -17.99), (0, 0, -18), 44, False),
    'map_exterior.png': ((40, 26, 150), (0, 12, 40), 42, True),
    'map_spawn.png': ((SPAWN[0], SPAWN_Y + 5.5, SPAWN[2] + 6), (0, 10, 40), 60, True),
    'map_heal.png': ((-6, FL + 8, 10), (-36, FL + 5, 0), 55, True),
    'map_shop.png': ((6, FL + 8, -8), (36, FL + 5, 2), 55, True),
    'map_storage.png': ((-2, FL + 8, 6), (22, FL + 4, -32), 55, True),
    'map_ceiling.png': ((0, FL + 5, 24), (0, FL + 26, -8), 70, True),
    'map_lab.png': ((0, FL + 9, -40), (0, FL + 7, -95), 55, True),
}
build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
if 'nomaterials' not in ARGS: material_skin()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': STATIC_TRIS,
           'tris_total': TRIS[0] + sum(STATIC_TRIS.values()), 'kit_tris': {k: v[1] for k, v in LIB.items()}},
          open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
json.dump({'anchors': ANCHORS, 'spawn': SPAWN, 'floor_y': FL}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'lab_map.blend'))
print('MAP_TRIS', TRIS[0], sum(STATIC_TRIS.values()), STATIC_TRIS)
if 'norender' not in ARGS:
    only = [a for a in ARGS if a.endswith('.png')]
    for n, (l, t, fov, roof) in SHOTS.items():
        if only and n not in only: continue
        shot(n, l, t, fov, roof=roof)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
