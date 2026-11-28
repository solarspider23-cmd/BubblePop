# blender -b --factory-startup --python wh_map.py [-- norender | more] -> Northgate Distribution (wh_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: ONE HALL + AISLE GRID + DOCK APRON.
# Hall x -120..120, z -80..80 (walls 1 thick, centred on the lines), floor y 0, eaves 36, ridge 40 at z 0.
# Truck yard south of the dock wall, z 80..146, surface y -4.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import wh_props as FP
F = FP.G
from pro_lib import clean, KM, r2b, nz, clamp, lerp, MB
from fitlib import add_owner

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean(); F.MATS.clear()
SC = bpy.context.scene
KIT = bpy.data.collections.new('Kit'); SC.collection.children.link(KIT)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
SUB = {}
def sub(name):
    if name not in SUB:
        c = bpy.data.collections.new(name); MAP.children.link(c); SUB[name] = c
    return SUB[name]

X0, X1, Z0, Z1 = -120.0, 120.0, -80.0, 80.0; WT = 1.0; EAVE, RIDGE = 36.0, 40.0; YARD_Y, YARD_Z = -4.0, 146.0
DOORS = [(-90, 'closed'), (-60, 'open'), (-30, 'half'), (0, 'open'), (30, 'closed'), (60, 'open'), (90, 'closed')]
TRUSS_X = [-105 + 30 * k for k in range(8)]
OPEN = [('z', Z1, x, 10.0, 0, 12.0) for x, _ in DOORS] + [('x', X0, 38.0, 4.4, 0, 8.3), ('z', Z1, -110.0, 4.4, 0, 8.3)]
def deck_y(z): return EAVE - .55 + (RIDGE - EAVE) * (1 - abs(z) / 80.0)     # roof deck underside (on the truss top chords)

LIB = {}; COUNT = {}; TRIS = [0]; ANCHORS = []; CULLED = [0]
WALL_PROPS = ('FirePoint', 'Charger', 'PersonnelDoor')
HANGING = ('HighBay', 'Container', 'Crane', 'Skylight', 'Runway', 'RoofTruss', 'SiteOffice')
def cull(meshes, name):
    """delete faces nobody sees: flat bottoms on the floor (y ~ 0 facing down), backs of wall props against the wall.
    Blender space here: x = -X, y = Z, z = Y."""
    tris = 0
    for me in meshes.values():
        bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); kill = []
        for f in bm.faces:
            zs = [v.co.z for v in f.verts]; ys = [v.co.y for v in f.verts]
            if f.normal.z < -.98 and max(zs) < .06 and min(zs) > -.06 and not name.startswith(HANGING): kill.append(f)
            elif name.startswith(WALL_PROPS) and f.normal.y > .98 and min(ys) > -.06: kill.append(f)
        tris += sum(len(f.verts) - 2 for f in kill)
        bmesh.ops.delete(bm, geom=kill, context='FACES'); bm.to_mesh(me); bm.free()
    return tris
def kit(key, fn):
    if key not in LIB:
        P = eval('FP.' + fn) if isinstance(fn, str) else fn()
        meshes = F.to_kit(P, KIT); cut = cull(meshes, P.name)
        LIB[key] = (meshes, P.tris - cut, P.name); CULLED[0] += cut
    return LIB[key][0]
def place(key, fn, x, z, yaw=0.0, y=0.0, group='Props'):
    meshes = kit(key, fn)
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y'); Mr = (KM @ R @ KM.inverted()).to_4x4()
    obs = []
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = Matrix.Translation(r2b((x, y, z))) @ Mr; sub(group).objects.link(ob); obs.append(ob)
        if '_Glow_' in me.name: ob.visible_shadow = False
    add_owner(obs)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
    return obs
def anchor(name, kind, group, x, y, z, yaw, size, **attrs):
    ANCHORS.append({'name': name, 'kind': kind, 'group': group, 'pos': [round(x, 2), round(y, 2), round(z, 2)],
                    'yaw': round(yaw % 360, 1), 'size': list(size), 'attrs': attrs})
def yaw_of(dx, dz): return math.degrees(math.atan2(-dx, -dz))      # local front (-z) along (dx, dz)

# ================================================================== statics
U_ = FP.PAL.u
def shade(col, v, up=.05, n=None):
    return lambda f: [(U_(col), clamp(v + up * f.normal.y + (0 if n is None else (nz(l.vert.co.x, l.vert.co.y, l.vert.co.z, n[0], n[1]) - .5) * n[2]), .04, .96)) for l in f.loops]
def mesh_obj(name, mb, group='Building'):
    me = F.mesh_from(name, mb, F.materials()['pal']); ob = bpy.data.objects.new(name, me); sub(group).objects.link(ob)
    add_owner([ob]); return ob
def bx(mb, size, c, col, v, up=.05, n=None, kill_down=False):
    g = FP.box(size, 0); FP.at(g, c)
    if kill_down: g.normal_update(); bmesh.ops.delete(g, geom=[f for f in g.faces if f.normal.y < -.9], context='FACES')
    mb.add(g, shade(col, v, up, n))

def walls():
    mb = MB(); seams = MB()
    runs = [('z', Z0, X0, X1, 0.0), ('z', Z1, X0, X1, YARD_Y), ('x', X0, Z0, Z1, 0.0), ('x', X1, Z0, Z1, 0.0)]
    def blk(ax, at_, a, b, y0, y1):
        if b - a < .05 or y1 - y0 < .05: return
        for ya, yb_, col, v in ((y0, min(3.0, y1), 'concrete', .55), (max(3.0, y0), y1, 'cladding', .66)):
            if yb_ - ya < .05: continue
            size = (b - a, yb_ - ya, WT) if ax == 'z' else (WT, yb_ - ya, b - a)
            c = ((a + b) / 2, (ya + yb_) / 2, at_) if ax == 'z' else (at_, (ya + yb_) / 2, (a + b) / 2)
            bx(mb, size, c, col, v, .03, (30, 3, .08))
    for ax, at_, a, b, ybot in runs:
        ops = sorted([(c - w / 2, c + w / 2, y0, y1) for ax2, at2, c, w, y0, y1 in OPEN if ax2 == ax and at2 == at_])
        cur = a - WT / 2; end = b + WT / 2
        for o0, o1, y0, y1 in ops:
            blk(ax, at_, cur, o0, ybot, EAVE); blk(ax, at_, o0, o1, ybot, y0); blk(ax, at_, o0, o1, y1, EAVE); cur = o1
        blk(ax, at_, cur, end, ybot, EAVE)
        # panel joints on both faces (vertical seams every 3.6 from the plinth to the eave), plinth top flashing
        n = int((b - a) / 3.6)
        for k in range(1, n):
            t = a + k * (b - a) / n
            if any(o0 - .3 < t < o1 + .3 for o0, o1, y0, y1 in ops): ys = [(y1, EAVE) for o0, o1, y0, y1 in ops if o0 - .3 < t < o1 + .3]
            else: ys = [(3.2, EAVE)]
            for ya, yb_ in ys:
                for s in (-1, 1):
                    q = FP.quad(.08, yb_ - ya, 'z' if ax == 'z' else 'x', 0, t, (ya + yb_) / 2, flip=(s > 0) if ax == 'z' else (s < 0))
                    FP.at(q, (0, 0, at_ + s * (WT / 2 + .01)) if ax == 'z' else (at_ + s * (WT / 2 + .01), 0, 0))
                    seams.add(q, shade('cladding', .45, 0))
        for s in (-1, 1):
            size = (b - a + WT, .25, .25) if ax == 'z' else (.25, .25, b - a + WT)
            c = ((a + b) / 2, 3.1, at_ + s * (WT / 2 + .1)) if ax == 'z' else (at_ + s * (WT / 2 + .1), 3.1, (a + b) / 2)
            bx(mb, size, c, 'steel', .55, .1)
    for xw in (X0, X1):                                                  # gables up to the ridge
        g = FP.prism_x([(Z0 - .5, EAVE), (0, RIDGE + .3), (Z1 + .5, EAVE)], xw - WT / 2, xw + WT / 2); mb.add(g, shade('cladding', .66, .03))
    mesh_obj('Building_Walls', mb); mesh_obj('Building_Seams', seams)

SKY_X = [-90 + 30 * k for k in range(7)]; SKY_Z = [(-62, -52), (-32, -22), (22, 32), (52, 62)]
def roof():
    """deck slabs on the truss top chords with skylight holes, liner rib lines underneath, purlins, ridge cap, eaves gutters"""
    mb = MB(); lines = MB(); T = .3
    xb = sorted({X0 - 1.0, X1 + 1.0} | {c + d for c in SKY_X for d in (-5, 5)})
    zb = sorted({Z0 - 1.5, Z1 + 1.5, 0.0} | {e for a, b in SKY_Z for e in (a, b)})
    def cell(xa, xb_, za, zb_):
        bm = bmesh.new()
        vs = {}
        for i, x in enumerate((xa, xb_)):
            for j, z in enumerate((za, zb_)):
                for k, yo in enumerate((0, T)): vs[i, j, k] = bm.verts.new((x, deck_y(z) + yo, z))
        for q in (((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)), ((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)),
                  ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0))):
            bm.faces.new([vs[k] for k in q])
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        mb.add(bm, lambda f: [(U_('cladding'), .5 if f.normal.y < 0 else .62)] * len(f.loops))
    for xa, xb_ in zip(xb, xb[1:]):
        for za, zb_ in zip(zb, zb[1:]):
            hole = any(abs((xa + xb_) / 2 - c) < 5 for c in SKY_X) and any(a <= (za + zb_) / 2 <= b for a, b in SKY_Z)
            if not hole: cell(xa, xb_, za, zb_)
    for k in range(int((X1 - X0) / 2.5)):                                 # liner ribs (dark lines on the underside)
        x = X0 + 1.25 + k * 2.5
        for za, zb_ in ((Z0, 0.0), (0.0, Z1)):
            segs = [(za, zb_)]
            if any(abs(x - c) < 5.2 for c in SKY_X):
                cuts = [(a - .5, b + .5) for a, b in SKY_Z if za <= a <= zb_]; segs = []; cur = za
                for a, b in cuts: segs.append((cur, a)); cur = b
                segs.append((cur, zb_))
            for a, b in segs:
                bm = bmesh.new(); p = [bm.verts.new((x + dx, deck_y(z) - .02, z)) for dx, z in ((-.12, a), (.12, a), (.12, b), (-.12, b))]
                f = bm.faces.new(p); f.normal_update()
                if f.normal.y > 0: f.normal_flip()
                lines.add(bm, lambda f: [(U_('cladding'), .3)] * len(f.loops))
    for z in [Z0 + 4 + k * 8 for k in range(20)]:                         # purlins (Z sections) along x
        if abs(z) < 1: continue
        bx(mb, (X1 - X0, .9, .3), (0, deck_y(z) - .45, z), 'steel', .5, .15)
        bx(mb, (X1 - X0, .12, .7), (0, deck_y(z) - .86, z + .2), 'steel', .52, .15)
    bx(mb, (X1 - X0 + 2, .5, 2.4), (0, RIDGE - .3 + .25 + .1, 0), 'cladding', .7, .1)
    for s in (-1, 1): bx(mb, (X1 - X0 + 2, .9, 1.0), (0, EAVE - .1, s * (80.0 + 1.5)), 'steel', .6, .1)
    mesh_obj('Building_Roof', mb, 'Roof'); mesh_obj('Building_RoofLines', lines, 'Roof')

def floors():
    """concrete slab (mottled grid), saw-cut joints, lane + bay markings; yard asphalt + concrete apron with lines"""
    mb = MB(); n = 10.0
    for i in range(int((X1 - X0) / n)):
        for j in range(int((Z1 - Z0) / n)):
            x0, z0 = X0 + i * n, Z0 + j * n
            bm = FP.quad(n, n, 'y', 0, x0 + n / 2, z0 + n / 2)
            mb.add(bm, lambda f: [(U_('concrete'), clamp(.56 + (nz(l.vert.co.x, 0, l.vert.co.z, 26, 1) - .5) * .22 + (nz(l.vert.co.x, 0, l.vert.co.z, 7, 4) - .5) * .06, .05, .95)) for l in f.loops])
    for x0, x1, z0, z1 in ((X0 - .5, X1 + .5, Z1 - .5, Z1 + .5),):     # dock-face lip (the slab drops to the yard)
        g = FP.box((x1 - x0, 4.0, z1 - z0), 0); FP.at(g, ((x0 + x1) / 2, -2.0, (z0 + z1) / 2)); mb.add(g, shade('concrete', .5, .05, (8, 2, .1)))
    mesh_obj('Building_Floor', mb)
    ln = MB()
    def line(x0, z0, x1, z1, w, col='yellow', v=.62):
        d = Vector((x1 - x0, 0, z1 - z0)); L = d.length; d.normalize(); nrm = Vector((-d.z, 0, d.x)) * (w / 2)
        bm = bmesh.new(); p = [bm.verts.new(v_) for v_ in (Vector((x0, .02, z0)) - nrm, Vector((x0, .02, z0)) + nrm, Vector((x1, .02, z1)) + nrm, Vector((x1, .02, z1)) - nrm)]
        f = bm.faces.new(p); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
        ln.add(bm, lambda f: [(U_(col), v)] * len(f.loops))
    for k in range(1, int((X1 - X0) / 20)):                            # saw-cut joints
        line(X0 + k * 20, Z0 + .6, X0 + k * 20, Z1 - .6, .08, 'concrete', .3)
    for k in range(1, int((Z1 - Z0) / 20)): line(X0 + .6, Z0 + k * 20, X1 - .6, Z0 + k * 20, .08, 'concrete', .3)
    for z in (27.6, 46.4): line(X0 + 1, z, X1 - 1, z, .45)                # cross-aisle lane edges
    for k in range(int((X1 - X0 - 10) / 8)):                              # dashed centre line
        x = X0 + 6 + k * 8; line(x, 37.0, x + 4.5, 37.0, .3, 'paper', .85)
    line(X0 + 1, 77.0, X1 - 1, 77.0, .3, 'green', .55)
    for x, _ in DOORS:                                                    # staging bays in front of each dock door
        for a, b, c, d in ((x - 6, 50, x + 6, 50), (x - 6, 72, x - 6, 50), (x + 6, 72, x + 6, 50)): line(a, b, c, d, .3)
        for k in range(5): line(x - 6 + k * 3, 72.4, x - 4 + k * 3, 74.6, .35, 'yellow', .6)
    for z in range(-46, 24, 7): line(9.0, z, 41.0, z, .2, 'paper', .8)
    mesh_obj('Floor_Lines', ln)
    # yard
    ym = MB(); g = 10.0
    for i in range(int((X1 - X0 + 40) / g)):
        for j in range(int((YARD_Z + 30 - Z1) / g) + 1):
            x0 = X0 - 20 + i * g; z0 = Z1 + .5 + j * g; z1 = min(z0 + g, YARD_Z + 30)
            if z1 - z0 < .1: continue
            col = 'asphalt' if z0 < YARD_Z else 'concrete'
            bm = FP.quad(g, z1 - z0, 'y', YARD_Y, x0 + g / 2, (z0 + z1) / 2)
            ym.add(bm, lambda f, col=col: [(U_(col), clamp((.45 if col == 'asphalt' else .5) + (nz(l.vert.co.x, 0, l.vert.co.z, 30, 2) - .5) * .25, .05, .95)) for l in f.loops])
    mesh_obj('Yard_Ground', ym, 'Yard')
    yl = MB(); ln = yl
    def yline(x0, z0, x1, z1, w, col='paper', v=.82):
        d = Vector((x1 - x0, 0, z1 - z0)); d.normalize(); nrm = Vector((-d.z, 0, d.x)) * (w / 2)
        bm = bmesh.new(); p = [bm.verts.new(v_) for v_ in (Vector((x0, YARD_Y + .02, z0)) - nrm, Vector((x0, YARD_Y + .02, z0)) + nrm, Vector((x1, YARD_Y + .02, z1)) + nrm, Vector((x1, YARD_Y + .02, z1)) - nrm)]
        f = bm.faces.new(p); f.normal_update()
        if f.normal.y < 0: f.normal_flip()
        yl.add(bm, lambda f: [(U_(col), v)] * len(f.loops))
    for x, _ in DOORS:                                                    # trailer bay guide lines
        for s in (-1, 1): yline(x + s * 7.5, 84, x + s * 7.5, 130, .35)
    for x0 in (-117, 105):                                                # hatched no-park zones
        for k in range(6): yline(x0 + k * 2.2, 84, x0 + k * 2.2 + 3, 90, .35, 'yellow', .6)
    mesh_obj('Yard_Lines', yl, 'Yard')

# ================================================================== layout
RACK_ROWS = [-101.0 + k * 18.4 for k in range(6)]                       # double rows (centres); wall row on the west wall
RACK_S, NBAY = 24.0, 8                                                   # south end of every row, bays per row
def rack_row(xc, double=True, seed=0):
    """bays running north from z RACK_S (yaw 90: local front -> -x / west, local +x -> north); guard at both ends"""
    yaw = 90 if double else -90
    for k in range(NBAY):
        zc = RACK_S - FP.BAY / 2 - k * FP.BAY
        key = 'bay%s%d' % ('D' if double else 'S', (seed + k * 3) % 5)
        if double: place(key, 'rack_bay(%d, True)' % ((seed + k * 3) % 5), xc, zc, yaw, 0, 'Racks')
        else: place(key, 'rack_bay(%d, False)' % (10 + (seed + k) % 3), xc, zc, yaw, 0, 'Racks')
    zn = RACK_S - NBAY * FP.BAY
    if double:
        place('endD', 'rack_end(True)', xc, zn, 90, 0, 'Racks')             # north end: frames + guard (guard on local +x = north)
        place('guardD', 'rack_end(True, False)', xc, RACK_S, -90, 0, 'Racks')   # south end: guard only (local +x -> south)
    else:
        place('endS', 'rack_end(False)', xc, RACK_S, -90, 0, 'Racks')        # wall row: its bays' uprights sit at their north ends

def build():
    rng = random.Random(7)
    # ---- structure: columns, trusses, runway, crane, lamps, skylights
    for x in TRUSS_X:
        place('truss', 'roof_truss()', x, 0, 0, 0, 'Structure')
        place('colN', 'steel_column(31.25, False, False)', x, Z0 + 1.3, 0, 0, 'Structure')
        place('colS', 'steel_column(31.25, True, True, (-1,))', x, Z1 - 1.3, 0, 0, 'Structure')
        place('colC', 'steel_column(31.25, True, True)', x, 27.0, 0, 0, 'Structure')
    for z in (-48, -16, 16, 48):
        for x in (X0 + 1.3, X1 - 1.3):
            if x < 0 and z < 30: continue                                 # the wall rack row runs there
            place('colN', 'steel_column(31.25, False, False)', x, z, 90, 0, 'Structure')
    for zr in (27.0 + 1.35, Z1 - 1.3 - 1.35):
        for k in range(8): place('runway', 'runway_beam(30)', X0 + 15 + k * 30, zr, 0, FP.RUNWAY_Y, 'Structure')
    zc = ((27.0 + 1.35) + (Z1 - 1.3 - 1.35)) / 2; span = (Z1 - 1.3 - 1.35) - (27.0 + 1.35)
    CX = -12.0
    place('crane', 'crane_bridge(%.2f)' % span, CX, zc, 0, FP.RUNWAY_Y, 'Crane')
    ty = FP.RUNWAY_Y + 1.9 + 3.0 + .27; drop = 3.3
    place('trolley', 'crane_trolley(%.1f)' % drop, CX, 37.0, 0, ty, 'Crane')
    place('container', "shipping_container('red')", CX, 37.0, 0, ty - drop - 6.8 - 8.1, 'Crane')
    for x in [-110, -92, -73, -55, -37, -18, 0, 20, 40, 60, 80, 100]:
        for z in [-66, -46, -26, -6, 14, 37, 62]:
            place('lamp', 'high_bay(0, 2.0)', x, z, 0, 32.0 - 1.65 - 2.0, 'Lights')
    for c in SKY_X:
        for a, b in SKY_Z:
            zm = (a + b) / 2; place('sky%s' % ('S' if zm > 0 else 'N'), 'skylight(10, 10, %d)' % (1 if zm > 0 else -1), c, zm, 0, deck_y(zm) - .3, 'Roof')
    # ---- racking
    rack_row(X0 + WT / 2 + .05, False, 1)
    for i, xc in enumerate(RACK_ROWS): rack_row(xc, True, i * 2)
    # ---- dock wall: doors, staging, fire points
    for x, st in DOORS:
        place('dock_' + st, "dock_door('%s')" % st, x, Z1 - WT / 2, 0, 0, 'Dock')
        anchor('Dock%d' % (DOORS.index((x, st)) + 1), 'station', 'Docks', x, 1, 70, 0, (10, 12, 8), State=st)
    place('pdoorS', 'personnel_door()', -110, Z1 - WT / 2, 0, 0, 'Dock')
    place('pdoorW', 'personnel_door()', X0 + WT / 2, 38.0, yaw_of(1, 0), 0, 'Dock')
    for x, st in DOORS:
        if st == 'open' or st == 'half':
            for k in range(rng.randint(3, 5)):
                i, j = k % 2, k // 2
                kind = rng.choice(['wrapped', 'wrapped', 'cartons', 'drums'])
                place('fp_%s%d' % (kind, k % 3), "floor_pallet('%s', %d)" % (kind, k % 3), x - 2.9 + i * 5.8, 66 - j * 6.0, rng.choice((0, 0, 180)) + rng.uniform(-3, 3), 0, 'Staging')
    place('fpw', "floor_pallet('wrapped', 2)", 30 - 2.9, 66, 0, 0, 'Staging')
    place('jack0', 'pallet_jack(0)', 2.5, 56, 160, 0, 'Staging'); place('jack0', 'pallet_jack(0)', -57, 57, 200, 0, 'Staging')
    place('stackE', 'pallet_stack(8, 1)', 102, 72, 10, 0, 'Staging'); place('stackE2', 'pallet_stack(6, 2)', 107, 72, -6, 0, 'Staging')
    for x in (-50, 10):
        place('fire', 'fire_point()', x, Z0 + WT / 2, 180, 0, 'Dock')
    place('fire', 'fire_point()', X1 - WT / 2, 32.0, yaw_of(-1, 0), 0, 'Dock')
    place('barrier', 'safety_barrier(10)', -112.5, 33.0, 0, 0, 'Spawn'); place('barrier', 'safety_barrier(10)', -112.5, 43.0, 0, 0, 'Spawn')
    for z in (31.0, 45.0): place('bollard', 'bollard()', -106.0, z, 0, 0, 'Spawn')
    anchor('Spawn', 'spawn', 'Spawn', -108, .5, 38, yaw_of(1, 0), (6, 1, 6))
    # ---- forklifts on the move + parked
    place('fl_load', "forklift(1, 'wrapped')", -44, 36.0, yaw_of(1, 0), 0, 'Vehicles')
    place('fl_empty', 'forklift(0)', 22, 62, yaw_of(-.3, 1), 0, 'Vehicles')
    for k, z in enumerate((-6.0, 2.0, 10.0)):                             # charging bay on the east wall
        place('charger', 'charger_unit(0)', X1 - WT / 2, z, yaw_of(-1, 0), 0, 'Bulk')
        if k < 2: place('fl_park', 'forklift(0)', X1 - 11.5, z, yaw_of(-1, 0) + 180, 0, 'Vehicles')
        anchor('Charger%d' % (k + 1), 'station', 'Stations', X1 - 6, 1, z, 90, (4, 6, 4), Kind='charge')
    # ---- bulk floor: block stack lanes, IBCs, drums, stillages
    for zi, z in enumerate(range(-43, 21, 7)):
        for xi in range(5):
            if rng.random() < .82:
                kind = rng.choice(['wrapped', 'wrapped', 'cartons', 'sacks', 'crates'])
                place('bk_%s%d' % (kind, xi % 3), "floor_pallet('%s', %d)" % (kind, 10 + xi % 3), 12.5 + xi * 6.6, z + 3.5, rng.choice((0, 180)) + rng.uniform(-2, 2), 0, 'Bulk')
    for i in range(3):
        for j in range(2): place('ibc%d' % ((i + j) % 2), 'ibc_tote(%d)' % ((i + j) % 2), 62 + i * 4.3, 6 + j * 3.6, 0, 0, 'Bulk')
    for i in range(3): place('fp_drums%d' % (i % 2), "floor_pallet('drums', %d)" % (20 + i % 2), 82 + i * 4.4, 9, 0, 0, 'Bulk')
    for i in range(3): place('still%d' % (i % 2), 'mesh_stillage(%d)' % (i % 2), 62 + i * 4.4, -14, 0, 0, 'Bulk')
    place('wrapper', 'stretch_wrapper(0)', 96, -20, 90, 0, 'Bulk')
    anchor('Wrapper', 'station', 'Stations', 92, 1, -20, 90, (8, 8, 8), Kind='wrap')
    # ---- mezzanine + office + packing under it
    MX, MZ = 85.0, -57.0
    place('mezz', 'mezzanine()', MX, MZ, 0, 0, 'Mezzanine')
    place('office', 'site_office()', 98.0, -68.0, 0, 14.0, 'Mezzanine')
    anchor('Office', 'station', 'Stations', 80, 15, -68, 90, (6, 8, 6), Kind='orders')
    for k in range(3): place('bench%d' % (k % 2), 'packing_bench(%d)' % (k % 2), 66 + k * 12, -44, 180, 0, 'Packing')
    place('conv', 'conveyor(24)', 104, -50, 0, 0, 'Packing')
    for k in range(3): anchor('PackBench%d' % (k + 1), 'station', 'Stations', 66 + k * 12, 1, -40, 0, (8, 6, 4), Kind='pack')
    for k in range(4):
        place('fp_cartons%d' % k, "floor_pallet('cartons', %d)" % (30 + k), 62 + k * 5.0, -70, rng.uniform(-3, 3), 0, 'Packing')
    # ---- yard (y -4): trailers, tractors, fence, lights, bins, stair, cones
    for x, st in DOORS:
        if x in (-60, 0): place('trl_open', "box_trailer('open', %d)" % (abs(x) // 30), x, Z1 + .5 + 1.8 + 21.5, 0, YARD_Y, 'Yard')
        if x == 90: place('trl_closed', "box_trailer('closed')", x, Z1 + .5 + 1.8 + 21.5, 0, YARD_Y, 'Yard')
    place('tractor', "tractor_unit('green')", 0, Z1 + .5 + 1.8 + 21.5 + 17.5 + 4.6, 180, YARD_Y, 'Yard')
    place('tractor', "tractor_unit('green')", -95, 128, yaw_of(1, 0), YARD_Y, 'Yard')
    for x, st in DOORS:
        if x in (-60, 0, 90):
            for s in (-1, 1): place('chock', 'wheel_chock()', x + s * 3.1, Z1 + .5 + 1.8 + 7 - 1.6 - .75, 180, YARD_Y, 'Yard')
    place('dstair', 'dock_stair()', -110, Z1 + .5 + 7.2 + .25, 0, YARD_Y, 'Yard')
    for k in range(int((X1 - X0) / 10)): place('fence', 'fence_panel()', X0 + 5 + k * 10, YARD_Z, 0, YARD_Y, 'Yard')
    for s in (-1, 1):
        for k in range(int((YARD_Z - Z1 - 1) / 10) + 1):
            place('fence', 'fence_panel()', s * X1, Z1 + 1.0 + 5 + k * 10.0 - (0 if Z1 + 1 + 5 + k * 10 + 5 <= YARD_Z else 0), yaw_of(s, 0), YARD_Y, 'Yard')
    for x in (-80, 0, 80): place('ylight', 'yard_light()', x, YARD_Z - 4, 0, YARD_Y, 'Yard')
    for x in (-112, -105): place('bin%d' % (x % 2), "yard_bin('green', %d)" % (abs(x) % 2), x, 136, 0, YARD_Y, 'Yard')
    for k, (x, z) in enumerate(((42, 100), (45, 106), (48, 112), (-30, 118), (-26, 124))): place('cone', 'traffic_cone()', x, z, rng.uniform(0, 90), YARD_Y, 'Yard')
    place('ystack', 'pallet_stack(10, 3)', 110, 120, 15, YARD_Y, 'Yard'); place('ystack2', 'pallet_stack(7, 4)', 111, 126, -8, YARD_Y, 'Yard')
    anchor('YardBounds', 'border', 'Border', 0, 0, (Z1 + YARD_Z) / 2, 0, (X1 - X0, 20, YARD_Z - Z1), Note='weld-mesh fence = border')
    anchor('HallBounds', 'border', 'Border', 0, EAVE / 2, 0, 0, (X1 - X0, EAVE, Z1 - Z0), Note='clad walls = border')

# ================================================================== look: late-afternoon, hazy
def look():
    w = bpy.data.worlds.new('Day'); SC.world = w; bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (.55, .68, .9, 1); bg.inputs[1].default_value = .9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.0; sun.data.color = (1, .82, .62); sun.data.angle = math.radians(1.5)
    d = Vector((-.55, -.32, .78)).normalized()                       # Roblox-space direction TO the sun: low, from the south-west
    sun.rotation_euler = (-r2b(d)).to_track_quat('-Z', 'Y').to_euler()
    for name, (x0, x1, z0, z1) in {'hall': (X0, X1, Z0, Z1)}.items():
        L = bpy.data.lights.new('Fill', 'AREA'); L.shape = 'RECTANGLE'; L.size = (x1 - x0) * .9; L.size_y = (z1 - z0) * .9
        L.energy = 2.2 * (x1 - x0) * (z1 - z0); L.color = (.92, .95, 1.0)
        ob = bpy.data.objects.new('Fill', L); SC.collection.objects.link(ob); ob.location = r2b(((x0 + x1) / 2, 31.0, (z0 + z1) / 2))
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 3000; cam.data.clip_start = .2
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

walls(); roof(); floors(); build()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
static_tris = sum(len(ob.data.polygons) for c in SUB.values() for ob in c.objects if ob.data.name.startswith(('Building_', 'Floor_', 'Yard_')))
look()
import roblox_materials as RM
RM.LOOK.update({'Cardboard': ('noise', 30., .08, .9, 0, .1), 'Rubber': (None, 0, 0, .8, 0, .2), 'Plastic': (None, 0, 0, .35, 0, .5),
                'Glass': (None, 0, 0, .04, 0, .5), 'DiamondPlate': ('voronoi', 4.0, .2, .45, .8, .5)})
MATERIALS = {'concrete': 'Concrete', 'asphalt': 'Asphalt', 'steel': 'Metal', 'rack': 'Metal', 'beam': 'Metal', 'cardboard': 'Cardboard',
             'pallet': 'WoodPlanks', 'yellow': 'Plastic', 'rubber': 'Rubber', 'cladding': 'Metal', 'red': 'Plastic', 'plastic': 'Plastic',
             'paper': 'SmoothPlastic', 'glass': 'Glass', 'green': 'Plastic'}
OVERRIDES = {'Floor_Lines': 'SmoothPlastic', 'Yard_Lines': 'SmoothPlastic', 'Mezzanine': {'pallet': 'Wood'}, 'SiteOffice': {'cladding': 'SmoothPlastic'},
             'Trailer': {'cladding': 'SmoothPlastic'}, 'DockDoor': {'steel': 'DiamondPlate'}, 'Forklift': {'yellow': 'SmoothPlastic'}, 'Tractor': {'green': 'SmoothPlastic'}}
RM.preview(FP.PAL, F.materials()['pal'], MATERIALS, skip=('Sky',), overrides=OVERRIDES)
RM.write_map(FP.PAL, MATERIALS, os.path.join(HERE, 'material_map.json'), overrides=OVERRIDES)
json.dump({'anchors': ANCHORS, 'spawn': [-108, .5, 38]}, open(os.path.join(HERE, 'anchors.json'), 'w'), indent=1)
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed_props': TRIS[0], 'tris_static': static_tris,
           'tris_total': TRIS[0] + static_tris, 'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'wh_map.blend'))
print('STATS props', TRIS[0], 'static', static_tris, 'total', TRIS[0] + static_tris, 'culled', CULLED[0])
if 'norender' not in ARGS:
    shot('map_spawn.png', (-110, 6.5, 38), (0, 9, 40), 24)
    shot('map_aisle.png', (-90.0, 6, 30), (-92, 8, -40), 22)
    shot('map_dock.png', (-24, 7, 22), (20, 4, 75), 22)
    shot('map_yard.png', (40, 12, 145), (-20, 2, 82), 24)
    shot('map_mezz.png', (40, 8, -2), (90, 12, -55), 22)
    for ob in SUB['Roof'].objects: ob.hide_render = True
    for ob in SUB['Structure'].objects:
        if ob.name.startswith('RoofTruss'): ob.hide_render = True
    shot('map_overview.png', (-170, 210, 260), (0, 0, 10), 30)
    if 'more' in ARGS: shot('map_top.png', (0, 420, 33), (0, 0, 32), 30)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
