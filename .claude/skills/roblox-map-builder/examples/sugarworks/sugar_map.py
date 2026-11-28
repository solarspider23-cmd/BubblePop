# blender -b --factory-startup --python sugar_map.py -> Sugarworks Tycoon (sugar_map.blend) + previews\
# Roblox space (X east, Y up, Z south, 1 unit = 1 stud). Archetype: tycoon plots (flat, 8 identical plots, one boulevard).
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import sugar_props as FP
F = FP.G
from pro_lib import (clean, KM, r2b, nz, clamp, smooth, grid, voronoi_cells, shrink, ccw, ngon_prism, MB, box, hull, rock_pts)

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

# ------------------------------------------------------------------ layout (all flat: tycoon plots must be equal)
X0, X1, Z0, Z1 = -150, 150, -312, 252          # plateau
ROAD_W = 32; SIDE = 7                           # road x +-16, sidewalk to +-23, lawn strip, plots from +-26
PLOT = 84; PX = 68
PLOT_Z = [-195, -100, -5, 90]
PLOTS = [(sx * PX, z) for z in PLOT_Z for sx in (-1, 1)]       # 8 plots, team index = list order
SPAWN = (0, 212); PLAZA_R = 36
EXCH = (0, -264); APRON_R = 46
ROAD_Z = (-220, 178)
SLAB_Y = 1.2                                    # plot tile top
def H(x, z): return 0.0

# ------------------------------------------------------------------ instancing
LIB = {}; COUNT = {}; TRIS = [0]; PTS = []
def kit(key, fn):
    if key not in LIB:
        P = fn(); LIB[key] = (F.to_kit(P, KIT), P.tris)
    return LIB[key][0]
def place(key, fn, x, z, yaw=0.0, s=1.0, y=0.0, group='Props'):
    meshes = kit(key, fn)
    R = Matrix.Rotation(math.radians(yaw), 3, 'Y')
    M = Matrix.Translation(r2b((x, y, z))) @ (KM @ R @ KM.inverted()).to_4x4() @ Matrix.Scale(s, 4)
    for me in meshes.values():
        ob = bpy.data.objects.new(me.name, me); ob.matrix_world = M; sub(group).objects.link(ob)
    COUNT[key] = COUNT.get(key, 0) + 1; TRIS[0] += LIB[key][1]
def face(x, z, tx, tz): return math.degrees(math.atan2(-(tx - x), -(tz - z)))
def local(px, pz, yaw, lx, lz):
    """plot-local (lx, lz) -> world; local -Z = the plot's road side"""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return px + lx * c + lz * s, pz - lx * s + lz * c
def free(x, z, r): return all((x - a) ** 2 + (z - b) ** 2 >= (r + c) ** 2 for a, b, c in PTS)
def on_hard(x, z, m=0.0):
    """road / sidewalks / plots / plaza / apron: no scatter there"""
    if abs(x) < 24 + m and ROAD_Z[0] - 30 < z < ROAD_Z[1] + 10: return True
    for px, pz in PLOTS:
        if abs(x - px) < PLOT / 2 + 2 + m and abs(z - pz) < PLOT / 2 + 2 + m: return True
    if math.hypot(x - SPAWN[0], z - SPAWN[1]) < PLAZA_R + 3 + m: return True
    if math.hypot(x - EXCH[0], z - EXCH[1]) < APRON_R + 2 + m: return True
    return not (X0 + 7 + m < x < X1 - 7 - m and Z0 + 7 + m < z < Z1 - 7 - m)

# ------------------------------------------------------------------ one plot (identical for all 8; only the team glow differs)
def plot(i, px, pz):
    yaw = face(px, pz, 0, pz)                      # road side faces the boulevard
    L = lambda lx, lz: local(px, pz, yaw, lx, lz)
    g = 'Plot%d' % (i + 1)
    place('plotbase', FP.plot_base, px, pz, yaw, group=g)
    place('gate%d' % i, lambda: FP.gate(i), *L(0, -42), yaw, y=.6, group=g)
    # fence: 7 x 12 along back + sides, front split around the gate (gate pillars end at |lx| 10.7)
    posts = set()
    for k in range(7):
        c = -36 + k * 12
        place('fence%d' % i, lambda: FP.fence(12, i), *L(c, 42), yaw, y=.6, group=g); posts |= {(c - 6, 42), (c + 6, 42)}
        for sx in (-1, 1): place('fence%d' % i, lambda: FP.fence(12, i), *L(sx * 42, c), yaw + 90, y=.6, group=g); posts |= {(sx * 42, c - 6), (sx * 42, c + 6)}
    for sx in (-1, 1):
        for c in (24, 36): place('fence%d' % i, lambda: FP.fence(12, i), *L(sx * c, -42), yaw, y=.6, group=g); posts |= {(sx * (c - 6), -42), (sx * (c + 6), -42)}
        place('fenceS%d' % i, lambda: FP.fence(8.1, i), *L(sx * 13.95, -42), yaw, y=.6, group=g); posts |= {(sx * 18.0, -42)}   # the gate pillar is its other post
    for lx, lz in sorted(posts): place('fencepost', FP.fence_post, *L(lx, lz), yaw, y=.6, group=g)   # one post per corner
    # starter line along local X at lz 4: dropper over the belt start -> 3 belts -> upgrader -> collector
    for c in (-16, -4, 8): place('conveyor', FP.conveyor, *L(c, 4), yaw, y=SLAB_Y, group=g)
    place('dropper', FP.dropper, *L(-16, 4), yaw, y=SLAB_Y, group=g)
    place('upgrader', FP.upgrader, *L(-2, 4), yaw, y=SLAB_Y, group=g)
    place('collector', FP.collector, *L(19.5, 4), yaw, y=SLAB_Y + .4, group=g)        # base plate on the slab, not in it
    place('cashpad', FP.cash_pad, *L(19.5, -14), yaw, y=SLAB_Y, group=g)
    for c in (-26, -14, -2): place('button', FP.buy_button, *L(c, -24), yaw, y=SLAB_Y, group=g)
    # empty slots for the next line + an upgrade building
    place('slot40', lambda: FP.slot_marker(40, 8), *L(-2, 22), yaw, y=SLAB_Y, group=g)
    place('slot12', lambda: FP.slot_marker(12, 12), *L(22, 22), yaw, y=SLAB_Y, group=g)
    place('slot20', lambda: FP.slot_marker(20, 14), *L(-24, 34), yaw, y=SLAB_Y, group=g)
    place('walk', lambda: FP.walkway(18), *L(0, -32), yaw, y=SLAB_Y, group=g)                 # gate -> buttons
    place('walkx', lambda: FP.walkway(30, 5), *L(-14, -18), yaw + 90, y=SLAB_Y, group=g)        # along the button row
    for lz in (-.6, 8.6): place('hazard', FP.hazard, *L(-4, lz), yaw, y=SLAB_Y, group=g)         # line safety stripes
    place('chute', FP.coin_chute, *L(19.5, 4), yaw, y=SLAB_Y, group=g)
    place('sacks', FP.candy_sacks, *L(32, 16), yaw + 8, y=SLAB_Y, group=g)
    for k, (lx, lz, a) in enumerate(((-31.5, -5, 10), (-35.5, -2, 35), (-31.5, 1, -15), (31, -30, 20))):   # >= 3.7 apart: crates never overlap
        place('crate%d' % (k % 3), lambda k=k: FP.candy_crate(k % 3), *L(lx, lz), yaw + a, y=SLAB_Y - .1, group=g)

# ------------------------------------------------------------------ ground: striped lawn, road, sidewalks, plaza, apron, cliffs, sea
def ground():
    bm = grid(X0, X1, Z0, Z1, (X1 - X0) // 4, (Z1 - Z0) // 4, H)
    uL = F.PAL.u('lawn')
    def shade(f):
        c = f.calc_center_median()
        stripe = (int((c.z - Z0) // 10) % 2) * .07                        # mowed stripes
        v = .5 + stripe + (nz(c.x, 0, c.z, 30, 3) - .5) * .12
        return [(uL, clamp(v, .1, .9))] * len(f.loops)
    mb = MB(); mb.add(bm, shade)
    road = MB(); rng = random.Random(3)
    z0, z1 = ROAD_Z
    road.add(F.at(box((ROAD_W, .4, z1 - z0), .05), (0, -.05, (z0 + z1) / 2)), F.S('asph', base=.45, up=.15, jit=0))
    for z in range(int(z0) + 6, int(z1) - 4, 12):                          # lane dashes
        road.add(F.at(box((.9, .1, 6), 0), (0, .2, z)), F.S('lemon', base=.62, jit=0))
    for sx in (-1, 1):
        road.add(F.at(box((1.0, .9, z1 - z0), .15), (sx * 16.5, .2, (z0 + z1) / 2)), F.S('pink', base=.6, up=.2, jit=0))
        for z in range(int(z0), int(z1), 6):                               # sidewalk tiles
            road.add(F.at(box((5.8, .6, 5.8), .12), (sx * 20, .1, z + 3)), F.S('conc', base=.58 + rng.uniform(-.06, .06), up=.2, jit=0))
    for (cx, cz), R, seed in ((SPAWN, PLAZA_R, 4), (EXCH, APRON_R, 6)):    # plaza + apron: candy-tile paving
        base = F.at(F.cyl(R + .6, .5, sides=40, y0=-.35), (cx, 0, cz)); road.add(base, F.S('choc', base=.55, up=.1, jit=0))
        for site, poly in voronoi_cells(cx - R, cx + R, cz - R, cz + R, 4.2, seed=seed):
            if max(math.hypot(x - cx, z - cz) for x, z in poly) > R: continue
            col = 'pink' if (site[0] - cx) ** 2 + (site[1] - cz) ** 2 < (R * .32) ** 2 else 'cream'
            road.add(ngon_prism(ccw(shrink(poly, .92)), -.3, .32 + rng.uniform(-.04, .04), .1),
                     F.S(col, base=.55 + rng.uniform(-.08, .08), up=.15, jit=0))
    # path from the plaza / apron to the road ends (fills the gaps between disc and road)
    for z0p, z1p in ((ROAD_Z[1] - 2, SPAWN[1] - PLAZA_R + 6), (EXCH[1] + APRON_R - 6, ROAD_Z[0] + 2)):
        road.add(F.at(box((ROAD_W, .4, abs(z1p - z0p)), .05), (0, -.05, (z0p + z1p) / 2)), F.S('asph', base=.45, up=.15, jit=0))
    # cliff skirt: faceted walls from the lawn edge to the sea, jittered so it reads as rock
    per = []
    for x in range(X0, X1, 8): per.append((x, Z0))
    for z in range(Z0, Z1, 8): per.append((X1, z))
    for x in range(X1, X0, -8): per.append((x, Z1))
    for z in range(Z1, Z0, -8): per.append((X0, z))
    rr = random.Random(9); n = len(per); rings = []
    cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
    for (x, z) in per:
        d = Vector((x - cx, 0, z - cz)).normalized()
        ring = []
        for y, out in ((0.05, 0), (-2.5, 1.2), (-14, 3.5 + rr.uniform(-1.5, 2)), (-26, 6 + rr.uniform(-2, 3)), (-40, 10 + rr.uniform(-2, 4))):
            ring.append(Vector((x + d.x * out, y + (rr.uniform(-1, 1) if y < -1 else 0), z + d.z * out)))
        rings.append(ring)
    cl = bmesh.new(); V = [[cl.verts.new(p) for p in r] for r in rings]
    for k in range(n):
        a, b = V[k], V[(k + 1) % n]
        for j in range(4): cl.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    bmesh.ops.recalc_face_normals(cl, faces=list(cl.faces))
    for f in cl.faces:
        if (f.calc_center_median() - Vector((cx, -10, cz))).dot(f.normal) < 0: f.normal_flip()
    mb.add(cl, F.S('cliff', grad=(-40, 0, .2, .72), up=.15, top='lawn', thr=.55, topbase=.42))
    sea = MB()
    sea.add(F.at(box((3600, .5, 3600)), (0, -32.5, 0)), F.S('sea', base=.42, up=0, jit=0))
    bed = MB(); bed.add(F.at(box((3700, .5, 3700)), (0, -38.0, 0)), F.S('cliff', base=.3, up=0, jit=0))   # sea bed 5.5 under the water
    for name, m in (('Ground', mb), ('Hardscape', road), ('Sea_Water', sea), ('Ocean_Floor', bed)):
        me = F.mesh_from(name, m, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new(name, me))

# ------------------------------------------------------------------ build
def build():
    rng = random.Random(11)
    for i, (px, pz) in enumerate(PLOTS): plot(i, px, pz)
    place('exchange', FP.exchange, *EXCH, face(*EXCH, *SPAWN), y=.3, group='Hero')
    for sx in (-1, 1):                                                       # giant lollipops flank the hall
        for (dx, dz, s, sd) in ((50, 22, 2.3, 3), (40, -14, 1.9, 1)):
            place('lolly%d' % sd, lambda sd=sd: FP.lollipop_tree(sd), sx * dx, EXCH[1] + dz, face(sx * dx, EXCH[1] + dz, 0, 0) + 90, s=s, group='Hero')
            PTS.append((sx * dx, EXCH[1] + dz, 8))
    place('spawn', FP.spawn_pad, *SPAWN, y=.3, group='Plaza')
    for k in range(8):                                                       # plaza ring: lollipops + benches facing the pad
        a = k * math.tau / 8 + math.tau / 16
        x, z = SPAWN[0] + math.cos(a) * (PLAZA_R - 4), SPAWN[1] + math.sin(a) * (PLAZA_R - 4)
        if z < SPAWN[1] - 20: continue                                       # keep the road mouth open
        if k % 2: place('bench', FP.choc_bench, x, z, face(x, z, *SPAWN), y=.3, group='Plaza')
        else: place('lolly%d' % (k % 4), lambda k=k: FP.lollipop_tree(k % 4), x, z, rng.uniform(0, 360), s=1.2, y=.3, group='Plaza')
        PTS.append((x, z, 4))
    for pz in PLOT_Z:                                                         # street lamps + benches along the sidewalks
        for dz in (-30, 30):
            for sx in (-1, 1): place('lamp', FP.candy_lamp, sx * 19.5, pz + dz, face(sx * 19.5, pz + dz, 0, pz + dz), y=.4, group='Street')
    for z in (-147.5, -52.5, 42.5, 137.5):
        for sx in (-1, 1):
            place('bench', FP.choc_bench, sx * 21.6, z, face(sx * 21.6, z, 0, z), y=.4, group='Street')
            place('bin', FP.wrapper_bin, sx * 21.4, z + 4.6, 0, y=.4, group='Street')
    for sx in (-1, 1):                                                        # chocolate fountains flank the Exchange apron
        place('fountain', FP.choc_fountain, sx * 30, EXCH[1] + 30, 0, y=.3, group='Hero'); PTS.append((sx * 30, EXCH[1] + 30, 8))
    # lawns: tree + bush rows in the gaps between plots, then the outer lawns
    for z in (-147.5, -52.5, 42.5):
        for sx in (-1, 1):
            for k, x in enumerate(range(34, 112, 15)):
                X = sx * x
                if k % 2 == 0: place('lolly%d' % (k % 4), lambda k=k: FP.lollipop_tree(k % 4), X, z, rng.uniform(0, 360), s=rng.uniform(.8, 1.0), group='Lawn')
                else: place('gum%d' % (k % 3), lambda k=k: FP.gumdrop_bush(k % 3), X, z, rng.uniform(0, 360), group='Lawn')
                PTS.append((X, z, 4))
    def scatter(n, key, fn, r, s_rng, pad=0.0):
        done = 0
        for _ in range(n * 60):
            if done >= n: break
            x, z = rng.uniform(X0, X1), rng.uniform(Z0, Z1)
            if on_hard(x, z, pad) or not free(x, z, r): continue
            PTS.append((x, z, r)); place(key, fn, x, z, rng.uniform(0, 360), s=rng.uniform(*s_rng), group='Lawn'); done += 1
    for sd in range(4): scatter(9, 'lolly%d' % sd, lambda sd=sd: FP.lollipop_tree(sd), 7, (.9, 1.35), 3)
    for sd in range(3): scatter(16, 'gum%d' % sd, lambda sd=sd: FP.gumdrop_bush(sd), 3.5, (.8, 1.3), 1)
    for sd in range(3): scatter(10, 'corn%d' % sd, lambda sd=sd: FP.candy_corn(sd), 2.5, (.9, 1.3), 1)
    for z in range(int(ROAD_Z[0]) + 10, int(ROAD_Z[1]), 9):                   # peppermint stepping discs on the lawn gaps
        if any(abs(z - pz) < 46 for pz in PLOT_Z): continue
        for sx in (-1, 1):
            for x in (31,):
                place('mint', FP.peppermint, sx * x, z + (x - 30) * .3, rng.uniform(0, 360), y=.05, group='Lawn'); PTS.append((sx * x, z, 2.4))
    for sd in range(3): scatter(4, 'crate%d' % sd, lambda sd=sd: FP.candy_crate(sd), 3, (1, 1), 2)
    for k in range(10):                                                       # sea stacks off the cliffs
        a = k * math.tau / 10 + rng.uniform(-.2, .2); d = rng.uniform(1.05, 1.2)
        x, z = math.cos(a) * 190 * d, (Z0 + Z1) / 2 + math.sin(a) * 330 * d
        place('stack%d' % (k % 3), lambda k=k: FP.rock_cliff(k % 3, r=rng.uniform(9, 14)), x, z, rng.uniform(0, 360), y=-34, group='Sea')

# ------------------------------------------------------------------ look: golden-hour sunset
def look():
    b = F.materials()['pal'].node_tree.nodes['Principled BSDF']             # matte candy: no blue sky sheen on pale floors
    b.inputs['Specular IOR Level'].default_value = .12; b.inputs['Roughness'].default_value = .95
    w = bpy.data.worlds.new('Sky'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.05; mr.inputs['From Max'].default_value = .55
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (1.0, .74, .45, 1); cr.elements[1].color = (.3, .26, .62, 1)
    e = cr.elements.new(.2); e.color = (1.0, .5, .62, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .55
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 5.2; sun.data.color = (1, .86, .7); sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(74), 0, math.radians(-72))              # low sun from the west: long shadows across the road
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (1800, 1800, 300); hz.location = (0, 0, 120); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); nt = vm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00014; pv.inputs['Color'].default_value = (1, .9, .86, 1)
    nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False

def horizon():
    mb = MB(); rng = random.Random(21)
    for k in range(9):                                                        # distant candy islands on the sea
        a = k * math.tau / 9 + rng.uniform(-.15, .15); d = rng.uniform(700, 1050); r = rng.uniform(60, 120)
        bm = hull(rock_pts((r, r * .35, r * .8), n=30, seed=k, flat=.0))
        mb.add(F.at(bm, (math.cos(a) * d, -26, math.sin(a) * d)), F.S('cliff', grad=(-30, 20, .3, .55), up=.1, top='lawn', thr=.5, topbase=.5, seed=k))
    for k in range(16):                                                       # cotton-candy clouds
        a = k * math.tau / 16 + rng.uniform(-.1, .1); d = rng.uniform(520, 900); y = rng.uniform(150, 280)
        cx, cz = math.cos(a) * d, math.sin(a) * d; col = ['pink', 'grape', 'cream'][k % 3]
        for j in range(rng.randint(4, 7)):
            r = rng.uniform(26, 48); off = Vector((rng.uniform(-60, 60), rng.uniform(-8, 14), rng.uniform(-30, 30)))
            mb.add(F.at(F.blob(r, k * 13 + j, n=26, sq=.62), (cx + off.x, y + off.y, cz + off.z)),
                   F.S(col, grad=(y - 30, y + 30, .62, .95), up=.1, jit=0))
    me = F.mesh_from('Horizon', mb, F.materials()['pal']); sub('Ground').objects.link(bpy.data.objects.new('Horizon', me))

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 5000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

build(); ground(); horizon()
bpy.context.view_layer.layer_collection.children['Kit'].exclude = True
look()
json.dump({'instances': COUNT, 'total_instances': sum(COUNT.values()), 'tris_placed': TRIS[0],
           'kit_tris': {k: v[1] for k, v in LIB.items()}}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'sugar_map.blend'))
if 'norender' not in ARGS:
    shot('map_spawn.png', (0, 9, 240), (0, 26, -264), 26)
    shot('map_overview.png', (250, 200, 290), (0, -10, -40), 30)
    px, pz = PLOTS[3]
    shot('map_plot.png', (24, 30, pz + 50), (px + 6, 2, pz), 30)
    shot('map_line.png', (px - 26, 10, pz - 12), (px + 2, 4, pz + 4), 30)
    shot('map_exchange.png', (12, 8, -200), (0, 30, -264), 30)
    shot('map_plaza.png', (44, 16, 262), (0, 3, 205), 30)
print('MAP_OK', sum(COUNT.values()), TRIS[0])
