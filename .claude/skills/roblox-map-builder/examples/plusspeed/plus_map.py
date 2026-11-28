# blender -b --factory-startup --python plus_map.py [-- norender] -> +1 Speed Run (plus_map.blend), previews\, roblox\PlusSpeed.rbxmx
# Everything is Blocks (Parts). Roblox space: X east, Y up, Z south; the track runs toward -Z.
import sys, os, math, random, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector, Matrix
import plus_props as FP
import plus_props_v4 as V4
from blocks import Block, BlockProp, transformed, mesh_blocks, stud_material, clear_material, write_rbxmx, rotm
from pro_lib import clean, r2b

PREV = os.path.join(HERE, 'previews'); os.makedirs(PREV, exist_ok=True)
OUT = os.path.join(HERE, 'roblox'); os.makedirs(OUT, exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
clean(); SC = bpy.context.scene
PAL = FP.PAL
GROUPS = {}
def grp(name): return GROUPS.setdefault(name, [])
def blk(group, size, pos, col, v, mat='stud', rot=(0, 0, 0), shape='block', name='Block', tr=0.0):
    grp(group).append(Block(tuple(size), Matrix.Translation(Vector(pos)) @ rotm(rot), col, v, mat, shape, name, tr))
def place(prop, pos, yaw=0.0, s=1.0, group='Props'):
    grp(group).extend(transformed(prop, pos, yaw, s))

# ------------------------------------------------------------------ layout
TRACK_W = 144; TILE_W, TILE_L = 48, 50; ZONE_L = 250; NZ = 8
HUB_Z = (100, -100); TRACK_Z0 = -100
FIN_Z0 = TRACK_Z0 - NZ * ZONE_L; FIN_Z1 = FIN_Z0 - 170
ZONES = [
    dict(name='Meadow',  floor=('grass', .5, .62), wall=('dirt', .5), cap=('grass', .55), lamp=('dirt', 'fire', 'gold'), pad='gold'),
    dict(name='Desert',  floor=('sand', .48, .6), wall=('rock', .5), cap=('sand', .62), lamp=('rock', 'fire', 'gold'), pad='fire'),
    dict(name='Beach',   floor=('sand', .76, .88), wall=('sand', .55), cap=('grass', .6), lamp=('wood', 'mint', 'mint'), pad='mint'),
    dict(name='Candy',   floor=('pink', .66, .82), wall=('pink', .45), cap=('snow', .94), lamp=('pink', 'snow', 'pink'), pad='pink'),
    dict(name='Snow',    floor=('snow', .74, .88), wall=('snow', .48), cap=('snow', .96), lamp=('stone', 'snow', 'mint'), pad='mint'),
    dict(name='Volcano', floor=('basalt', .4, .5), wall=('basalt', .3), cap=('basalt', .46), lamp=('basalt', 'fire', 'fire'), pad='fire'),
    dict(name='NeonCity', floor=('navy', .38, .48), wall=('navy', .22), cap=('navy', .42), lamp=('navy', 'stone', 'pink'), pad='pink'),
    dict(name='Space',   floor=('navy', .14, .24), wall=('basalt', .2), cap=('navy', .3), lamp=('basalt', 'navy', 'mint'), pad='mint'),
]

def walls(group, z0, z1, wall, cap, rng, inner=TRACK_W / 2, sides=(-1, 1), tiers=3, kerb='red'):
    """stepped canyon: tier n is a row of 24-wide blocks with a 2-stud cap, each tier taller and further out.
    Returns cap tops [(side, tier, x, y, z)] for dressing."""
    tops = []
    n = int(round((z0 - z1) / TILE_L))
    for sx in sides:
        base_h = 0
        for t in range(tiers):
            x = sx * (inner + 12 + t * 24)
            for i in range(n):
                z = z0 - TILE_L * (i + .5)
                h = (30 + t * 16) + rng.uniform(-3, 4) + (6 if t == 2 and i % 3 == 1 else 0)
                blk(group, (24, h, TILE_L), (x, h / 2 - 1, z), wall[0], wall[1] - t * .04 + rng.uniform(-.03, .03), name='Rock')
                blk(group, (25, 2, TILE_L), (x, h, z), cap[0], cap[1] - t * .03 + rng.uniform(-.02, .02), name='Cap')
                kerb_z(group, x - sx * 11.3, h + 1, z + TILE_L / 2, z - TILE_L / 2, kerb)
                tops.append((sx, t, x, h + 1, z))
    return tops

def kerb_z(group, x, y, za, zb, col, step=6.25):
    """race kerb along Z: alternating colour/white blocks proud of the cap edge, wedge bevel toward the track"""
    n = max(1, int(round(abs(za - zb) / step))); st = (za - zb) / n
    for i in range(n):
        c, v = (col, .55) if i % 2 == 0 else ('snow', .97)
        blk(group, (2.4, 1.0, abs(st)), (x, y + .5, za - st * (i + .5)), c, v, name='Kerb')

def kerb_x(group, xa, xb, y, z, col, step=6.0):
    n = max(1, int(round(abs(xb - xa) / step))); st = (xb - xa) / n
    for i in range(n):
        c, v = (col, .55) if i % 2 == 0 else ('snow', .97)
        blk(group, (abs(st), 1.0, 2.4), (xa + st * (i + .5), y + .5, z), c, v, name='Kerb')

def oval_track(group, ax, az, w=12.0, n=72):
    """running-track oval: red lane band, white inner/outer lines and 2 lane lines"""
    pts = [(math.cos(k * math.tau / n) * ax, math.sin(k * math.tau / n) * az) for k in range(n)]
    for k in range(n):
        (x0, z0), (x1, z1) = pts[k], pts[(k + 1) % n]
        mx, mz = (x0 + x1) / 2, (z0 + z1) / 2; L = math.hypot(x1 - x0, z1 - z0) + .6
        yaw = math.degrees(math.atan2(x1 - x0, z1 - z0))
        nx, nz = mx / ax ** 2, mz / az ** 2; nl = math.hypot(nx, nz); nx, nz = nx / nl, nz / nl
        blk(group, (w, .3, L), (mx, .15, mz), 'red', .42, rot=(0, yaw, 0), name='Track')
        for off, wd, v in ((-w / 2, .9, .97), (w / 2, .9, .97), (-w / 6, .5, .9), (w / 6, .5, .9)):
            blk(group, (wd, .35, L), (mx + nx * off, .2, mz + nz * off), 'snow', v, rot=(0, yaw, 0), name='Lane')

def floor(group, x0, x1, z0, z1, col, v1, v2, name='Tile'):
    nx = int(round((x1 - x0) / TILE_W)); nz = int(round((z0 - z1) / TILE_L))
    for i in range(nx):
        for j in range(nz):
            blk(group, (TILE_W, 2, TILE_L), (x0 + TILE_W * (i + .5), -1, z0 - TILE_L * (j + .5)), col, v1 if (i + j) % 2 else v2, name=name)

def dress_caps(tops, items, rng, every=1, group='Dressing', tiers=(0, 1, 2)):
    """put theme props on cap tops (centre of the 24-wide cap), skipping some for rhythm"""
    k = 0
    for sx, t, x, y, z in tops:
        if t not in tiers: continue
        k += 1
        if k % every: continue
        fn, s = rng.choice(items)
        place(fn(rng.randint(0, 99)), (x + rng.uniform(-3, 3), y, z + rng.uniform(-10, 10)), rng.uniform(0, 360), s, group)

# ------------------------------------------------------------------ hub
def hub(rng):
    """v4 stadium hub: striped infield inside an oval running track, stations face in from the outer band"""
    g = 'Hub'
    for i in range(int((HUB_Z[0] - HUB_Z[1]) / 10)):                             # mowing stripes across the whole floor
        blk(g, (240, 2, 10), (0, -1, HUB_Z[0] - 5 - i * 10), 'grass', .5 if i % 2 else .62, name='Lawn')
    oval_track(g, 74, 60)
    blk(g, (26, .3, 46), (0, .16, -77), 'red', .42, name='Runway')              # straight from the oval to START
    for x in (-13, 13): blk(g, (.9, .36, 46), (x, .2, -77), 'snow', .97, name='Lane')
    tops = walls(g, HUB_Z[0], HUB_Z[1], ('rock', .55), ('grass', .55), rng, inner=120)
    for t in range(3):                                                         # back wall behind spawn
        y_h = 30 + t * 16
        for i in range(int((240 + t * 48 + 48) / 24)):
            x = -120 - t * 24 - 24 + 12 + i * 24
            h = y_h + rng.uniform(-3, 4)
            blk(g, (24, h, 24), (x, h / 2 - 1, HUB_Z[0] + 12 + t * 24), 'rock', .55 - t * .04, name='Rock')
            blk(g, (24, 2, 25), (x, h, HUB_Z[0] + 12 + t * 24), 'grass', .55, name='Cap')
            kerb_x(g, x - 12, x + 12, h + 1, HUB_Z[0] + 1.2 + t * 24, 'red')
            tops.append((0, t, x, h + 1, HUB_Z[0] + 12 + t * 24))
    for t in range(3):                                                         # hub front corners up to the track walls
        for sx in (-1, 1):
            x0 = TRACK_W / 2 + 12 + t * 24; x1 = 120 + 12 + t * 24
            n = int((x1 - x0) / 24) + 1
            for i in range(n):
                x = sx * (x0 + i * 24); h = 30 + t * 16 + rng.uniform(-3, 4)
                if abs(x) >= 120 + t * 24 + 12: continue
                blk(g, (24, h, 24), (x, h / 2 - 1, HUB_Z[1] - 12 - t * 24), 'rock', .55 - t * .04, name='Rock')
                blk(g, (24, 2, 25), (x, h, HUB_Z[1] - 12 - t * 24), 'grass', .55, name='Cap')
                kerb_x(g, x - 12, x + 12, h + 1, HUB_Z[1] - 1.2 - t * 24, 'red')
    dress_caps(tops, [(lambda s: FP.voxel_tree(s, 14), 1.0), (lambda s: FP.voxel_tree(s, 18), 1.0), (lambda s: FP.bush(s), 1.2)], rng, 1, 'HubDressing')
    place(FP.spawn_pad(), (0, 0, 30), 0, 1, 'Spawn')                            # infield, facing START
    place(V4.egg_hatchery(), (98, 0, 40), 90, 1, 'Stations')                   # east band, facing the infield
    place(V4.sneaker_shop(), (98, 0, -38), 90, 1, 'Stations')
    place(V4.rebirth_portal(), (-98, 0, -38), -90, 1, 'Stations')              # west band
    for k in range(5): place(FP.treadmill(k), (-100, 0, 14 + k * 12), 90, 1, 'Treadmills')
    place(V4.podium_board(), (0, 0, 86), 180, 1, 'Stations')                  # behind spawn, facing the hub
    for x, z in ((-50, 0), (50, 0)):                                           # infield medals = the goal, shown at spawn
        place(V4.medal_pad('gold', 8), (x, 0, z), 180, 1, 'HubDressing')
    for x, z in ((-28, -66), (28, -66), (-28, 66), (28, 66)):
        place(FP.lamp_pillar('stone', 'red', 'gold'), (x * 2.9, 0, z * 1.25), 0, .55, 'HubDressing')
    for x, z, s in ((-106, 84, 1), (106, 84, 1), (-108, -86, 1), (108, -86, 1)):
        place(FP.voxel_tree(int(abs(x + z)), 16), (x, 0, z), rng.uniform(0, 360), s, 'HubDressing')
    for x, z in ((-30, 40), (30, 40), (-30, -30), (30, -30)):
        place(FP.flowers(int(abs(x * z)) % 50), (x, 0, z), 0, 1.2, 'HubDressing')
    place(V4.start_gate(), (0, 0, TRACK_Z0), 180, 1, 'StartArch')              # face the hub
    for k in range(6):                                                         # stadium hoardings along both walls (icons only)
        for sx in (-1, 1):
            z = 70 - k * 28
            place(V4.hoarding(('bolt', 'shoe', 'medal')[k % 3], ('red', 'mint', 'gold')[k % 3]), (sx * 118.5, 1.5, z), 90 * sx, 1, 'Hoardings')

# ------------------------------------------------------------------ zones
DRESS = {
    'Meadow':   [(lambda s: FP.voxel_tree(s, 15), 1.0), (lambda s: FP.voxel_tree(s, 19, 'leaf'), 1.0), (lambda s: FP.bush(s), 1.2), (lambda s: FP.flowers(s), 1.3)],
    'Desert':   [(lambda s: FP.cactus(s, 10), 1.0), (lambda s: FP.cactus(s, 13), 1.0), (lambda s: FP.mesa(s, .9), 1.0)],
    'Beach':    [(lambda s: FP.palm(s, 18), 1.0), (lambda s: FP.palm(s, 22), 1.0), (lambda s: FP.bush(s, 'leaf', .8), 1.0)],
    'Candy':    [(lambda s: FP.lollipop(s, 12), 1.0), (lambda s: FP.candy_cane(s, 12), 1.0), (lambda s: FP.gumdrop(s, ['pink', 'mint', 'gold'][s % 3]), 1.2)],
    'Snow':     [(lambda s: FP.pine(s, 18, True), 1.0), (lambda s: FP.pine(s, 22, True), 1.0), (lambda s: FP.snowman(s), 1.0), (lambda s: FP.ice_crystal(s), 1.0)],
    'Volcano':  [(lambda s: FP.lava_rock(s), 1.0), (lambda s: FP.mini_volcano(s), .7), (lambda s: FP.lava_rock(s, 1.4), 1.0)],
    'NeonCity': [(lambda s: FP.city_tower(s, 40), 1.0), (lambda s: FP.city_tower(s, 56), 1.0), (lambda s: FP.neon_sign(s), 1.0)],
    'Space':    [(lambda s: FP.asteroid(s, 1.2), 1.0), (lambda s: FP.ice_crystal(s, 1.2), 1.0)],
}

def zone(k, Zd, rng):
    zs = TRACK_Z0 - k * ZONE_L; ze = zs - ZONE_L; g = 'Zone%d_%s' % (k + 1, Zd['name'])
    col, v1, v2 = Zd['floor']; floor(g, -TRACK_W / 2, TRACK_W / 2, zs, ze, col, v1 - .05, v2 + .05)
    for x in (-TRACK_W / 6, TRACK_W / 6):                                      # lane lines
        for i in range(int(ZONE_L / 10)): blk(g, (.8, .3, 6), (x, .15, zs - 5 - i * 10), 'snow', .95, name='LaneLine')
    blk(g, (TRACK_W, .3, 2.4), (0, .15, zs - 1.2), Zd['pad'], .7, mat='neon', name='ZoneLine')
    for x in (-TRACK_W / 2 + .6, TRACK_W / 2 - .6): blk(g, (1.2, .5, ZONE_L), (x, .25, (zs + ze) / 2), 'snow', .95, name='Edge')
    tops = walls(g, zs, ze, Zd['wall'], Zd['cap'], rng, kerb=Zd['pad'])
    dress_caps(tops, DRESS[Zd['name']], rng, 1, g + '_Dressing')
    if Zd['name'] == 'NeonCity':                                               # neon window strips on the inner walls
        for sx, t, x, y, z in tops:
            if t == 0:
                for yy in range(6, int(y) - 4, 8): blk(g, (.4, 1.2, 30), (sx * (TRACK_W / 2 + .2), yy, z), ['pink', 'mint', 'gold'][int(z) % 3], .7, mat='neon', name='Window')
    if Zd['name'] == 'Volcano':                                                # lava seams in the walls
        for sx, t, x, y, z in tops[::2]:
            if t == 0: blk(g, (.4, y - 6, 1.6), (sx * (TRACK_W / 2 + .2), (y - 6) / 2, z + 7), 'fire', .62, mat='neon', name='Seam')
    if Zd['name'] == 'Space':
        for i in range(10):                                                    # planets + stars above the canyon
            sx = rng.choice((-1, 1))
            place(FP.planet(rng.randint(0, 9), rng.uniform(14, 30)), (sx * rng.uniform(120, 220), rng.uniform(70, 150), rng.uniform(ze, zs)), rng.uniform(0, 360), 1, g + '_Sky')
        for i in range(60):
            place(FP.star(i, rng.uniform(1.2, 2.6)), (rng.uniform(-260, 260), rng.uniform(60, 190), rng.uniform(ze, zs)), rng.uniform(0, 90), 1, g + '_Sky')
    if k > 0: place(FP.zone_gate(*Zd['lamp'], w=150), (0, 0, zs), 0, 1, g + '_Gate')
    for sx, t, x, y, z in tops:
        if t == 0 and int((zs - z) // 50) in (0, 2, 4):                         # distance boards on the first ledge, facing the track
            place(FP.dist_board(Zd['lamp'][0]), (sx * (TRACK_W / 2 + 4), y, z), -90 * sx, 1, g + '_Boards')
    for sx, t, x, y, z in tops:
        if t == 0 and int((zs - z) // 50) in (1, 3):                           # lamp pillars along the first ledge
            place(FP.lamp_pillar(*Zd['lamp']), (sx * (TRACK_W / 2 + 6), y, z), 0, .5, g + '_Lamps')
    for i, x in enumerate((-48, 0, 48)):                                       # wins pads near the zone end
        place(V4.medal_pad(Zd['pad'], 12 if i != 1 else 15), (x, 0, ze + 30), 180, 1, g + '_Wins')

def finish(rng):
    g = 'Finish'
    floor(g, -TRACK_W / 2, TRACK_W / 2, FIN_Z0, FIN_Z1, 'gold', .55, .8, 'Tile')
    tops = walls(g, FIN_Z0, FIN_Z1, ('snow', .62), ('gold', .6), rng)
    for t in range(3):                                                         # end wall
        for i in range(int((TRACK_W + 48 * (t + 1) + 48) / 24) + 1):
            x = -(TRACK_W / 2 + 24 + t * 24) + 12 + i * 24
            h = 40 + t * 16 + rng.uniform(-2, 3)
            blk(g, (24, h, 24), (x, h / 2 - 1, FIN_Z1 - 12 - t * 24), 'snow', .62 - t * .05, name='Rock')
            blk(g, (24, 2, 25), (x, h, FIN_Z1 - 12 - t * 24), 'gold', .6, name='Cap')
    dress_caps(tops, [(lambda s: FP.lamp_pillar('stone', 'gold', 'gold'), .6)], rng, 2, 'FinishDressing', tiers=(0,))
    place(FP.big_arch('gold'), (0, 0, FIN_Z0), 0, 1, 'FinishArch')
    place(FP.trophy(), (0, 0, FIN_Z0 - 120), 180, 1.6, 'Finish')
    place(FP.wins_pad('gold', 24), (0, 0, FIN_Z0 - 60), 0, 1, 'Finish')
    for sx in (-1, 1):
        for dz in (30, 90): place(FP.lamp_pillar('stone', 'gold', 'gold'), (sx * 56, 0, FIN_Z0 - dz), 0, .7, 'Finish')

def sky(rng):
    for i in range(46):
        place(FP.cloud(i, rng.uniform(1.4, 2.6)), (rng.choice((-1, 1)) * rng.uniform(150, 600), rng.uniform(150, 260), rng.uniform(FIN_Z1 - 200, 300)),
              rng.uniform(0, 360), 1, 'Clouds')
    for z0 in (300, -700, -1700):                                             # outer ground plates beyond the walls
        for sx in (-1, 1): blk('Outer', (1000, 40, 1000), (sx * (144 + 500), 18, z0 - 500), 'grass', .45, name='Ground')
    for i in range(140):                                                      # outer woods / hills on the plates
        sx = rng.choice((-1, 1)); x = sx * rng.uniform(160, 640); z = rng.uniform(FIN_Z1 - 150, 280)
        if rng.random() < .25:
            w = rng.uniform(30, 70); h = rng.uniform(10, 30)
            blk('Outer', (w, h, w * rng.uniform(.7, 1.2)), (x, 38 + h / 2, z), 'grass', rng.uniform(.4, .55), rot=(0, rng.uniform(0, 90), 0), name='Hill')
        else: place(FP.voxel_tree(i, rng.uniform(14, 22)), (x, 38, z), rng.uniform(0, 360), 1, 'Outer')

# ------------------------------------------------------------------ look
def look():
    w = bpy.data.worlds.new('Sky'); SC.world = w
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -.3; mr.inputs['From Max'].default_value = .55
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].color = (.7, .86, 1.0, 1); cr.elements[1].color = (.12, .42, .96, 1)
    e = cr.elements.new(.45); e.color = (.8, .92, 1.0, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = .8
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); SC.collection.objects.link(sun)
    sun.data.energy = 4.4; sun.data.color = (1, .96, .9); sun.data.angle = math.radians(4)
    el = math.radians(52); to_sun = r2b((math.cos(el) * .55, math.sin(el), math.cos(el) * .83)) - r2b((0, 0, 0))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()
    SC.render.engine = 'BLENDER_EEVEE'; SC.view_settings.view_transform = 'AgX'
    try: SC.view_settings.look = 'AgX - Punchy'
    except Exception: pass
    me = bpy.data.meshes.new('Haze'); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
    hz = bpy.data.objects.new('Haze', me); hz.scale = (3000, 6000, 600); hz.location = r2b((0, 100, -1000)); SC.collection.objects.link(hz)
    vm = bpy.data.materials.new('HazeMat'); nt = vm.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    pv = nt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = .00012; pv.inputs['Color'].default_value = (.85, .93, 1, 1)
    nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume']); me.materials.append(vm); hz.visible_shadow = False

def shot(name, loc, tgt, lens=30, res=(1920, 1080)):
    cam = bpy.data.objects.get('Cam') or bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    if cam.name not in SC.collection.objects: SC.collection.objects.link(cam)
    SC.camera = cam; cam.data.lens = lens; cam.data.clip_end = 8000; cam.data.clip_start = .3
    cam.location = r2b(loc); cam.rotation_euler = (r2b(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    SC.render.resolution_x, SC.render.resolution_y = res
    SC.render.filepath = os.path.join(PREV, name); bpy.ops.render.render(write_still=True)

rng = random.Random(5)
hub(rng)
for k, Zd in enumerate(ZONES): zone(k, Zd, rng)
finish(rng); sky(rng)
MAP = bpy.data.collections.new('Map'); SC.collection.children.link(MAP)
mats = {'pal': stud_material(PAL, 'PlusSpeed'), 'clear': clear_material()}
nparts = 0
for gname, blocks in GROUPS.items():
    c = bpy.data.collections.new(gname); MAP.children.link(c)
    mesh_blocks(blocks, PAL, gname, c, mats); nparts += len(blocks)
look()
n = write_rbxmx(os.path.join(OUT, 'PlusSpeed.rbxmx'), 'PlusSpeedMap', GROUPS, PAL, variant='Studs')
tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Haze')
json.dump({'parts': nparts, 'groups': {k: len(v) for k, v in GROUPS.items()}, 'tris': tris}, open(os.path.join(PREV, 'map_stats.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'plus_map.blend'))
if 'norender' not in ARGS:
    shot('map_spawn.png', (0, 11, 44), (0, 30, -300), 26)
    shot('map_hub_east.png', (-30, 30, 0), (98, 14, 0), 30)
    shot('map_hub_west.png', (30, 30, 0), (-98, 14, 0), 30)
    shot('map_hub_top.png', (0, 260, 20), (0, 0, -10), 30)
    shot('map_hub.png', (150, 110, 190), (0, 0, -10), 30)
    shot('map_track.png', (0, 12, -112), (0, 14, -600), 26)
    for k in (1, 3, 5, 6, 7):
        zs = TRACK_Z0 - k * ZONE_L
        shot('map_zone%d.png' % (k + 1), (40, 16, zs - 24), (-20, 16, zs - 230), 28)
    shot('map_finish.png', (0, 26, FIN_Z0 + 60), (0, 30, FIN_Z0 - 150), 28)
    shot('map_overview.png', (520, 520, -60), (0, 0, -1150), 30)
print('MAP_OK parts=%d tris=%d rbxmx=%d' % (nparts, tris, n))
