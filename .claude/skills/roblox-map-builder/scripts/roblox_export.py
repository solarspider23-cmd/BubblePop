# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Roblox export for a map built with this skill.
#   blender -b <map>.blend --python roblox_export.py -- --name Sugarworks [--out roblox] [--fmt glb|fbx]
# Reads the saved map (.blend with collections Kit + Map), writes <out>/:
#   kit/<Prop>.glb          one file per kit prop (solid MeshPart + one Neon MeshPart per glow key), origin = prop pivot
#   static/<Chunk>.glb      ground / hardscape / horizon split under the MeshPart limits, origin = chunk centre
#   AxisProbe.glb           orientation test piece (arrow points along the prop front, -Z; red cube on +X)
#   <Name>Setup.lua         ModuleScript: placement rows + Build() + ApplyLook() + collision rules (idempotent)
#   <Name>KitPrep.lua       command-bar script: collision fidelity per prop (CreateMeshPartAsync), RenderFidelity
#   manifest.json           per prop: parts, tris, size, collision, glow colours; static chunks; big parts
#   report.md               validator: Roblox limits, origins, UVs, budgets, placement checks
# Space: the skill's scripts work in Roblox space; Blender holds it as (-x, z, y) (pro_lib.KM). Placements here are
# converted back to Roblox CFrames exactly. GLB export uses Y-up; the Studio importer's facing is checked with AxisProbe
# (see references/roblox_pipeline.md, "Orientation check") and corrected by M.YAW_FIX in the setup module.
import bpy, bmesh, sys, os, json, math, re, shutil
from mathutils import Matrix, Vector

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(k, d=None):
    return ARGV[ARGV.index(k) + 1] if k in ARGV else d
NAME = arg('--name', os.path.splitext(os.path.basename(bpy.data.filepath))[0])
OUT = os.path.abspath(arg('--out', os.path.join(os.path.dirname(bpy.data.filepath), 'roblox')))
FMT = arg('--fmt', 'glb')
MATS = '--materials' in ARGV                 # Roblox materials: per (material, colour) MeshParts, Material + Color, no texture
MAT_TILE = float(arg('--mat-tile', '8'))     # box UVs: 1 UV unit = this many studs (material texture scale on meshes)
PARTCOL = {}; PARTMAT = {}                    # materials mode: MeshPart name -> colour / Enum.Material name
MATMAP = {'columns': {}, 'overrides': {}}
if MATS:
    _mp = arg('--matmap', os.path.join(os.path.dirname(bpy.data.filepath), 'material_map.json'))
    MATMAP = json.load(open(_mp))                 # written by the map script: scripts/roblox_materials.write_map
# optional per-map Studio look (references/roblox_pipeline.md 11b): SurfaceMaterial, TextureTint, Glow, GlowTransparency, Haze
_lk = arg('--look', os.path.join(os.path.dirname(bpy.data.filepath), 'roblox_look.json'))
SLOOK = json.load(open(_lk)) if os.path.exists(_lk) else {}

# ---------------- Roblox limits (references/roblox_pipeline.md)
MAX_TRIS = 20000            # triangles per MeshPart
SPLIT_TRIS = 18000          # leave headroom
MAX_EXTENT = 2048           # studs per MeshPart axis
SPLIT_EXTENT = 2000
MAX_TEX = 1024              # texture px
# performance budgets (phone-first). Over budget = export FAILS (exit 1) unless --allow-over.
BUDGET_TOTAL = int(arg('--budget', '450000'))       # placed triangles for the whole map (incl. static chunks)
BUDGET_PROP = int(arg('--prop-budget', '12000'))    # one kit prop, all its parts together
BUDGET_HERO = int(arg('--hero-budget', '30000'))    # props matching --hero (regex): the 1-3 landmarks
HERO_RE = arg('--hero', r'^$')
BUDGET_STATIC = int(arg('--static-budget', '150000'))  # all static chunks (ground, hardscape, horizon) together
ALLOW_OVER = '--allow-over' in ARGV
TINY = 2.0                  # parts smaller than this (max axis) do not cast shadows

# collision rule per prop name (regex, first match wins): none | box | hull | precise
#   none    = decor you walk through or over: flat decals, grass, flowers, glow, sky
#   box     = boxy props (crates, benches, buttons, fences): cheapest, use for anything roughly a box
#   hull    = convex-ish props (rocks, bushes, trees' trunks matter less than not snagging)
#   precise = buildings with doorways / arches players walk through (PreciseConvexDecomposition)
COLLISION = [
    (r'^(DryShrub|DuneGrass|SandDrift|RugSpread|OasisWater)\d*$', 'none'),                                    # The Gilded Dunes
    (r'^(StepPyramid|PylonGate|SunkenTemple|SpawnDais|OasisBasin|TraderTent|SleepTent\d|RuinWall\d|RuinHouse\d|RuinArch\d|ColossusHead|WyrmRib\d|ObeliskStump\d|TreasureMound\d)$', 'precise'),
    (r'^(ColumnTall\d|ColumnBroken\d|ColumnFallen\d|Obelisk\d|Waystone\d|QuestStele|SunAstrolabe|CargoPile\d|Campfire)$', 'box'),
    (r'^(Camel\w+|WyrmSkull|RockStack\d|Outcrop\d|ObeliskFallen\w+)$', 'hull'),
    (r'^(CupcakeFountain|SweetShop|BakeryOven|EggMachine|GumballMachine|QuestStand|CandyCastle|ChocoMountain|WaffleBridge|BiscuitBridge|DonutArch\d|Drawbridge)$', 'precise'),   # Sugarcrest Kingdom
    (r'^(Path_Tiles|Sprinkles|IcingCaps|River_Choc|ChocoFalls|ChocoPool|Banks_Crumb|Moat_Jelly|Clouds_Horizon|SpawnCookie|CandyFlower\d)', 'none'),
    (r'^(CandyLamp|MacaronStack\d|Marshmallow\d)$', 'box'),
    (r'^(TradePad|FlowerPatch\d|GrassTuft\d|Cloud\d)$|^Path_|^Sea_|^PuffBush_', 'none'),                               # Puffpaw Isles
    (r'^(PetFountain|PetStatue|PetShop|UpgradeMachine|RainbowArch|SpawnPad|LeaderboardFrame|TradeBooth_\w+)$|^EggStand_|^ZoneGate_|^Bridge_\d|^Ground_|^Paving_', 'precise'),
    (r'^(Fence_\w+|LampPost_\w+|Bench_\w+|StarLamp\d|CandyCane\d|Lollipop\d|PicnicSet|Chest_T\d|GiftBox_\w+)$', 'box'),
    (r'^SeaRock\d$', 'hull'),                                                                  # Puffpaw lagoon rocks (before the generic 'Sea' none)
    (r'^Tree\w+_(Leaves|Branches)$', 'none'),                                                   # realistic alpha-card trees: cards never collide (trunk = hull)
    (r'^Road_|TrashBags|FlowerBed\d', 'none'),                                                   # Maple Junction
    (r'^(TownHall|ClockTower|TrainStation|PlatformCanopy|CarShowroom|Bank|Fountain|BusStop|B_[A-Za-z]+)$|^Median_|^Square_', 'precise'),
    (r'^(StreetLamp|TrafficLight_\w+|Bench|Bin|Hydrant|Dumpster_\w+|Pallets|JobBoard|CityBus|WallPipes|TrackSeg|Sky[A-E])$|^Car_|^Train_|^Planter\d|^Hedge\d', 'box'),
    (r'Paving_Paths|VoidGrass\d|CrystalChips\d|RuneCircle|OverlookCircle|ArenaCircle|LiftBeam|DebrisShard\d|FarDebris\d|Singularity|CrystalHang\d|VoidTendril\d', 'none'),   # Shattered Void
    (r'Ground_Shard|RuneBridge|StepStone\d|LiftPad|SpawnDais|RiftGate|ArenaRim|VoidMerchant|AscensionAltar|SeersLectern|VoidArch', 'precise'),
    (r'CrystalLantern|VoidRail|VoidBrazier', 'box'),
    (r'FlowerPatch\d|LilyPads\d|Reeds\d|GateMat_|CollectPad_|Sea_Lake', 'none'),                      # Eggstead Isle
    (r'Coop_|GateFrame_|EggHatchery|EggBridge|EggDrain|EggShop|UpgradeStand|SellStand|BarnBackdrop|Windmill', 'precise'),
    (r'PlotYard_|Fence\d+_|FencePost_|NestPedestal_|OwnerSign_|HayStack|FeedTrough|FlowerTub|EggLamp|GiantEgg|NestStatue|RanchFence|ConveyorSeg|ConveyorCap|SiloBackdrop', 'box'),
    (r'RotundaRoof|WingRoof|PendantLamp|SlidingDoors|GemPod|FlowerBed|Bush\d', 'none'),        # Bloomcrest Care Centre
    (r'HallTrim|WingTrim|HallCeiling|HangingPot|Pond_Water|LilyPads|Reeds\d|EntryMat|RoundRug|HangingClock|HangingArt|WallCapsules|Plush|RoundBush|HealCorner|DockCables', 'none'),
    (r'Topiary|GardenWall|FigTree|Monstera|SnakePlant|SupplyBoxes|SaleStand|RopeLine|TrophyShelf|DrinkCooler', 'box'),
    (r'Rotunda|LabWing|EvoChamber|TradeDesk|EntranceCanopy|LabArchway|CapsuleFountain|RestNook|HealCounter|StarterTable', 'precise'),
    (r'HealMachine|ShopCounter|CapsuleShelf|PotionShelf|MedShelf|LabShelf|BerryBaskets|DisplayRack|PCTerminal|WaitBench|ParkBench|Workbench|MicroscopeBench|Whiteboard|SpecimenTank|VendingMachine|WelcomeSign|LongPlanter|RoundPlanter|LampPost|Bollard|PottedTree|PottedFern|Hedge\d', 'box'),
    (r'Palm\d|Hoodoo|Boulder', 'hull'), (r'Scrub|Agave|DryGrass', 'none'),                      # Sunspire Canyon Bazaar
    (r'SunTemple|MarketGate|CarvedStair|RopeBridge|TraderPavilion|RelicKiosk|ForgeStation|OasisPool', 'precise'),
    (r'Stall_|ShadeSail|Parapet\d|LanternPost|Brazier|QuestBoard|Pots\d|Sacks\d|RugRack', 'box'),
    (r'Shrub\d|CoralBranch|BrainCoral|NetPile|MarkerBuoy|Sea_Water', 'none'),                   # Tidehook Lagoon
    (r'AquaDome|Lighthouse|RodShop|BaitShop|FishMarket|BoatHouse|WelcomeArch|Skiff|FishingBoat', 'precise'),
    (r'RailBay|RailPost|TikiTorch|LifebuoyStand|QuestBoard|FishIndexWall|RodRack|RodHolder|Cooler|DryRack|BuoyStack', 'box'),
    (r'LanternRope|Waterfall|Lake_Water|Stream_Water|Pool_Water|Path_Dirt|Ground_Beach|Lilies|Reeds|Flowers|GnarledCanopy', 'none'),  # Mistvale Lake
    (r'LongHouse|TownHouse|Storehouse|FishingDock|StoneStair|StoneWall|SteppingStone|Cliff_Wall', 'precise'),
    (r'SignStand|RopePole|LanternPost', 'box'),
    (r'CloudTree', 'hull'), (r'Shrub|Tuft|Steam', 'none'),                                     # Yumori Springs
    (r'Pagoda|InnB|TallC|ShopD|BathPavilion|Stair\d|HotPool|KoiPond|Torii|SteppingStones', 'precise'),
    (r'Railing|Toro|Planter|TowelRack|NoodleStall|SakeBarrels|HandCart|LanternPost', 'box'),
    (r'^(GlowVine\d|CaveFalls|BedGlow\d)$', 'none'), (r'^MineShop$', 'precise'),             # Glowroot Caverns
    (r'Path_|River_|Scorch|Debris_|Duckboard|Graves', 'none'),                                  # Riverfield Siege
    (r'CurtainWall|WallStair|Donjon|SunderedBridge|BridgeTower|RuinedChapel|FootBridge|Tower_', 'precise'),
    (r'Palisade|Cheval|Wattle|Mantlet|HayBales|Supplies|WeaponRack|DryWall|AmmoPile|Dummy_|Well', 'box'),
    (r'^Fern\d+(_v\d+)?$', 'none'),                                                                       # Whispering Grove: ferns are foliage
    (r'^LavaPool\d+(_v\d+)?$', 'none'),                                                        # Skyrise: lava pools are flat glow decals (no lid)
    (r'DustPatch|DustPile|MeteorChunk|IceShards|Hazard|Walk|Slot|Peppermint|PathStone|LavaCrack|Track_|Tuft|Pebbles|Mushrooms|SnowMound|IceShards|AshPile|EmberRocks|DryShrub|Grass|Flower|Lily|Reeds|Pebble|Litter|Drift|Cloud|Horizon|Sea', 'none'),
    (r'Airlock|LaunchTower|LunarLander|Ground|Hardscape|Terrain|Floor|Top_|Paving|Bridge|Fountain|Cliff|Exchange|Gate|Elder|Altar|Cabin|Hut|Spire|Bridge|Stall|Well|Tent', 'precise'),
    (r'BeaconRail|JumpPad|SupplyCrates|FuelTanks|PlotBase|Slab|Crate|Bench|Button|Fence|Bin|Sacks|Pad|Sign|Board|Lamp|Post|Barrel', 'box'),
    (r'.*', 'hull'),
]
# per-map rules first: collision_rules.json next to the .blend (or --collision <file>), {"rules": [[regex, kind], ...]}
_cr = arg('--collision', os.path.join(os.path.dirname(bpy.data.filepath), 'collision_rules.json'))
if os.path.exists(_cr):
    COLLISION[:0] = [tuple(r) for r in json.load(open(_cr))['rules']]
def collision_of(name):
    for rx, kind in COLLISION:
        if re.search(rx, name): return kind     # case-sensitive: 'Hut' must not match 'Chute'
    return 'hull'

KM = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))        # Roblox -> Blender (same as pro_lib.KM)
KMi = KM.inverted()
def r_pos(vb): return KMi @ Vector(vb)

def clean_name(n): return re.sub(r'[^A-Za-z0-9_]', '_', n.replace('.', '_v'))
def base_of(meshname): return clean_name(re.sub(r'_Glow_[^.]+', '', meshname))
def glow_of(meshname):
    m = re.search(r'_Glow_([^.]+)', meshname); return m.group(1) if m else None

sc = bpy.context.scene
for d in ('kit', 'static'): os.makedirs(os.path.join(OUT, d), exist_ok=True)

# ---------------- 1. kit props: group kit objects by prop
kit_coll = bpy.data.collections.get('Kit'); map_coll = bpy.data.collections.get('Map')
assert kit_coll and map_coll, 'expected collections Kit and Map (build the map with the skill first)'
KIT = {}                                                # prop -> [mesh]
for ob in kit_coll.all_objects:
    if ob.type == 'MESH': KIT.setdefault(base_of(ob.data.name), []).append(ob.data)
KIT_MESHES = {me.name for ms in KIT.values() for me in ms}

def mat_color(mat):
    """glow colour (sRGB 0-255) from an emission material"""
    try:
        c = mat.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value
        return [round(min(1, max(0, c[i])) ** (1 / 2.2) * 255) for i in range(3)]
    except Exception: return [255, 255, 255]

def tris_of(me): return sum(len(p.vertices) - 2 for p in me.polygons)
def bbox(me, M=None):
    vs = [(M @ v.co) if M else v.co for v in me.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi

TMP = bpy.data.collections.new('_export'); sc.collection.children.link(TMP)

def newobj(name, me):
    """object with exactly `name` (the MeshPart name in Roblox): move any existing holder of the name out of the way,
    or Blender appends .001 and the setup module's name lookups (glow keys, colours) break"""
    other = bpy.data.objects.get(name)
    if other is not None: other.name = name + '__src'
    o = bpy.data.objects.new(name, me); TMP.objects.link(o)
    assert o.name == name, (o.name, name)
    return o

def _face_rgb(me, poly, img):
    w, h = img.size; uv = me.uv_layers.active.data[poly.loop_indices[0]].uv; px = img.pixels
    i = (int(min(.999, max(0, uv.y)) * (h - 1)) * w + int(min(.999, max(0, uv.x)) * (w - 1))) * 4
    return tuple(round(px[i + k] * 255) for k in range(3))

def material_split(objs, max_parts=8):
    """materials mode: split every palette (solid) object into one object per (Roblox material, colour) - material from
    the face's palette column (material_map.json), colour quantised - with box-projected UVs (1 UV = MAT_TILE studs).
    The setup module sets Material + Color per part from M.PartMaterial / M.PartColor."""
    NCOL = 16                                                           # palette columns (pro_lib.NCOL)
    out = []
    for o in objs:
        me = o.data
        img = None
        try: img = me.materials[0].node_tree.nodes['Image Texture'].image
        except Exception: pass
        if '_Glow_' in o.name or img is None or not me.uv_layers.active:
            out.append(o); continue
        over = next((m for k, m in MATMAP['overrides'].items() if o.name.startswith(k)), None)
        names = MATMAP.get('names', [])
        groups = {}
        for poly in me.polygons:
            uvx = me.uv_layers.active.data[poly.loop_indices[0]].uv.x; ci = min(NCOL - 1, int(uvx * NCOL))
            mat = MATMAP['columns'].get(str(ci), 'SmoothPlastic')
            if isinstance(over, str): mat = over                            # whole-prop override
            elif isinstance(over, dict) and ci < len(names) and names[ci] in over: mat = over[names[ci]]   # per-ramp override
            c = _face_rgb(me, poly, img); key = (mat, tuple(min(255, round(x / 28) * 28) for x in c))
            groups.setdefault(key, []).append(poly.index)
        keys = sorted(groups, key=lambda k: -len(groups[k]))
        while len(keys) > max_parts:                                        # merge the smallest group into the nearest colour
            small = keys.pop()                                              # of the same material (else any material)
            same = [k for k in keys if k[0] == small[0]] or keys
            near = min(same, key=lambda k: sum((x - y) ** 2 for x, y in zip(k[1], small[1])))
            groups[near] += groups.pop(small)
        for ci, key in enumerate(keys):
            bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); keep = set(groups[key])
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
            uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
            for f in bm.faces:
                n = f.normal; ax = max(range(3), key=lambda a: abs(n[a])); a2, b2 = [i for i in range(3) if i != ax]
                for l in f.loops: l[uv].uv = (l.vert.co[a2] / MAT_TILE, l.vert.co[b2] / MAT_TILE)
            nm = '%s_C%d' % (o.name, ci); nme = bpy.data.meshes.new(nm); bm.to_mesh(nme); bm.free()
            mname = 'M_%s_%02x%02x%02x' % ((key[0],) + key[1])
            mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
            mat.diffuse_color = (*[x / 255 for x in key[1]], 1); nme.materials.append(mat)
            no = newobj(nm, nme); no.matrix_world = o.matrix_world; out.append(no)
            PARTCOL[nm] = list(key[1]); PARTMAT[nm] = key[0]
        bpy.data.objects.remove(o)
    return out

def export(objs, path):
    if MATS: objs = material_split(objs)
    for o in sc.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if FMT == 'fbx':
        bpy.ops.export_scene.fbx(filepath=path + '.fbx', use_selection=True, apply_scale_options='FBX_SCALE_NONE',
                                 axis_forward='-Z', axis_up='Y', object_types={'MESH'}, path_mode='COPY', embed_textures=True)
    else:
        bpy.ops.export_scene.gltf(filepath=path + '.glb', export_format='GLB', use_selection=True, export_yup=True,
                                  export_apply=True, export_texcoords=True, export_normals=True, export_materials='EXPORT')
    for o in objs: bpy.data.objects.remove(o)

REPORT = []; WARN = []
manifest = {'name': NAME, 'format': FMT, 'props': {}, 'static': [], 'bigparts': []}
for prop, meshes in sorted(KIT.items()):
    objs = []; parts = []
    lo_all = Vector((1e9,) * 3); hi_all = Vector((-1e9,) * 3)
    for me in meshes:
        g = glow_of(me.name)
        pn = prop if not g else '%s_Glow_%s' % (prop, g)
        me = me.copy()                                                    # export copy: drop degenerate faces (booleans)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges); bm.to_mesh(me); bm.free()
        o = newobj(pn, me); objs.append(o)
        lo, hi = bbox(me); lo_all = Vector(map(min, lo_all, lo)); hi_all = Vector(map(max, hi_all, hi))
        t = tris_of(me); size = [round(x, 2) for x in r_pos(hi - lo)]; size = [abs(x) for x in size]
        parts.append({'name': pn, 'tris': t, 'size': size, 'glow': g, 'color': mat_color(me.materials[0]) if g else None})
        if t > MAX_TRIS: WARN.append('%s: %d tris > %d (split the prop or decimate)' % (pn, t, MAX_TRIS))
        if max(size) > MAX_EXTENT: WARN.append('%s: %.0f studs > %d' % (pn, max(size), MAX_EXTENT))
        uvs = me.uv_layers.active
        if uvs and not re.search(r'^Tree\w+_Trunk$', pn) and any(not (-.001 <= l.uv.x <= 1.001 and -.001 <= l.uv.y <= 1.001) for l in uvs.data):
            WARN.append('%s: UVs outside 0..1 (palette strip expects 0..1)' % pn)
        zero = sum(1 for p in me.polygons if p.area < 1e-7)
        if zero: WARN.append('%s: %d zero-area faces' % (pn, zero))
    rlo, rhi = r_pos(lo_all), r_pos(hi_all)
    ymin = min(rlo.y, rhi.y); xs = sorted((rlo.x, rhi.x)); zs = sorted((rlo.z, rhi.z))
    if ymin > .5 and not re.search(r'_(Leaves|Branches)$', prop): WARN.append('%s: lowest point y=%.2f above its origin (floats when placed)' % (prop, ymin))
    if abs((xs[0] + xs[1]) / 2) > max(3.0, (xs[1] - xs[0]) * .25) or abs((zs[0] + zs[1]) / 2) > max(3.0, (zs[1] - zs[0]) * .25):
        WARN.append('note %s: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)' % prop)
    manifest['props'][prop] = {'parts': parts, 'tris': sum(p['tris'] for p in parts), 'collision': collision_of(prop),
                               'size': [round(xs[1] - xs[0], 2), round(max(rlo.y, rhi.y) - ymin, 2), round(zs[1] - zs[0], 2)]}
    export(objs, os.path.join(OUT, 'kit', prop))

# ---------------- 2. placements (instances in Map) + static meshes
ROWS = {}; STATIC = []; PLACED = []; _PL = {}
for ob in map_coll.all_objects:
    if ob.type != 'MESH': continue
    grp = clean_name(ob.users_collection[0].name)
    if ob.data.name in KIT_MESHES:
        prop = base_of(ob.data.name)
        M = ob.matrix_world
        key = (prop, tuple(round(v, 3) for row in M for v in row))
        _PL.setdefault(key, (prop, []))[1].append(ob)                 # every mesh of one placed prop, tested together
        if key in ROWS: continue
        R = (KMi @ M.to_3x3() @ KM); s = R.col[0].length; R = R * (1.0 / s)
        p = r_pos(M.translation)
        ROWS[key] = [prop, grp, round(p.x, 3), round(p.y, 3), round(p.z, 3)] + [round(R[i][j], 4) for i in range(3) for j in range(3)] + [round(s, 4)]
    else:
        STATIC.append((ob, grp))

def split_faces(me, M):
    """faces -> chunks under SPLIT_TRIS / SPLIT_EXTENT (median cut on the longest axis of face centres)"""
    cents = [M @ p.center for p in me.polygons]; tri = [len(p.vertices) - 2 for p in me.polygons]
    vw = [M @ v.co for v in me.vertices]
    def ext(ids):
        pts = [vw[i] for f in ids for i in me.polygons[f].vertices]
        lo = Vector((min(v.x for v in pts), min(v.y for v in pts), min(v.z for v in pts)))
        hi = Vector((max(v.x for v in pts), max(v.y for v in pts), max(v.z for v in pts)))
        return lo, hi
    out = []
    def rec(ids):
        lo, hi = ext(ids); e = hi - lo
        if (sum(tri[i] for i in ids) <= SPLIT_TRIS and max(e) <= SPLIT_EXTENT) or len(ids) == 1:
            out.append((ids, lo, hi)); return
        cl = [cents[i] for i in ids]
        clo = Vector((min(c.x for c in cl), min(c.y for c in cl), min(c.z for c in cl)))
        chi = Vector((max(c.x for c in cl), max(c.y for c in cl), max(c.z for c in cl)))
        ax = max(range(3), key=lambda a: chi[a] - clo[a])
        ids = sorted(ids, key=lambda i: cents[i][ax]); h = len(ids) // 2
        rec(ids[:h]); rec(ids[h:])
    rec(list(range(len(me.polygons))))
    return out

def palette_rgb(me, poly):
    """average palette colour under a face (for oversize faces turned into Parts)"""
    try:
        img = me.materials[0].node_tree.nodes['Image Texture'].image; w, h = img.size
        uv = me.uv_layers.active.data[poly.loop_indices[0]].uv
        px = img.pixels; i = (int(uv.y * (h - 1)) * w + int(uv.x * (w - 1))) * 4
        return [round(px[i + k] * 255) for k in range(3)]
    except Exception: return [128, 128, 128]

SROWS = []; BIG = []
def big_part(ob, grp, lo, hi):
    """low-poly oversize mesh (sea plane, skirt slab) -> Parts tiled under the 2048-stud Part limit"""
    rlo, rhi = r_pos(lo), r_pos(hi)
    a = Vector(map(min, rlo, rhi)); b = Vector(map(max, rlo, rhi)); e = b - a
    n = [max(1, math.ceil(e[i] / SPLIT_EXTENT)) for i in range(3)]
    col = palette_rgb(ob.data, max(ob.data.polygons, key=lambda p: p.area))
    for i in range(n[0]):
        for k in range(n[2]):
            sz = Vector((e.x / n[0], max(e.y, .2), e.z / n[2]))
            c = Vector((a.x + sz.x * (i + .5), (a.y + b.y) / 2, a.z + sz.z * (k + .5)))
            BIG.append({'name': '%s_%d_%d' % (clean_name(ob.name), i, k), 'group': grp,
                        'pos': [round(x, 3) for x in c], 'size': [round(x, 3) for x in sz], 'color': col})
for ob, grp in STATIC:
    me = ob.data; M = ob.matrix_world
    lo, hi = bbox(me, M)
    if tris_of(me) < 64 and max(hi - lo) > MAX_EXTENT:
        big_part(ob, grp, lo, hi); continue
    for k, (ids, lo, hi) in enumerate(split_faces(me, M)):
        e = hi - lo
        if max(e) > MAX_EXTENT:                                    # a single huge face (sea plane / skirt slab) -> Parts
            poly = me.polygons[ids[0]]; c = (lo + hi) / 2; rc = r_pos(c); re_ = r_pos(e)
            size = [max(abs(re_.x), .2), max(abs(re_.y), .2), max(abs(re_.z), .2)]
            BIG.append({'name': '%s_%d' % (clean_name(ob.name), k), 'group': grp, 'pos': [round(x, 3) for x in rc],
                        'size': [round(x, 3) for x in size], 'color': palette_rgb(me, poly)})
            continue
        bm = bmesh.new(); bm.from_mesh(me); bm.transform(M)
        keep = set(ids); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
        c = (lo + hi) / 2
        bmesh.ops.translate(bm, vec=-c, verts=bm.verts)
        nm = '%s_%d' % (clean_name(ob.name), k)
        nme = bpy.data.meshes.new(nm); bm.to_mesh(nme); bm.free()
        for m_ in me.materials: nme.materials.append(m_)
        o = newobj(nm, nme)
        t = tris_of(nme)
        manifest['static'].append({'name': nm, 'group': grp, 'tris': t, 'size': [round(abs(x), 2) for x in r_pos(e)]})
        rc = r_pos(c)
        SROWS.append([nm, grp, round(rc.x, 3), round(rc.y, 3), round(rc.z, 3), 1, 0, 0, 0, 1, 0, 0, 0, 1, 1])
        if t > MAX_TRIS: WARN.append('static %s: %d tris' % (nm, t))
        export([o], os.path.join(OUT, 'static', nm))
manifest['bigparts'] = BIG

# ---------------- 3. axis probe: arrow along -Z (prop front), red cube on +X, green on +Y
bm = bmesh.new()
for loc, size in (((0, 0, -4), (1, 1, 8)), ((0, 0, -9), (3, 1, 2))):        # shaft + head, front = -Z (Roblox)
    b = bmesh.new(); bmesh.ops.create_cube(b, size=1); bmesh.ops.scale(b, vec=Vector(size), verts=b.verts)
    bmesh.ops.translate(b, vec=Vector(loc), verts=b.verts)
    me_ = bpy.data.meshes.new('t'); b.to_mesh(me_); b.free(); bm.from_mesh(me_); bpy.data.meshes.remove(me_)
bm.transform(KM.to_4x4()); pm = bpy.data.meshes.new('AxisProbe'); bm.to_mesh(pm); bm.free()
objs = [bpy.data.objects.new('AxisProbe', pm)]
for nm, loc in (('AxisProbe_PlusX', (4, 0, 0)), ('AxisProbe_PlusY', (0, 4, 0))):
    b = bmesh.new(); bmesh.ops.create_cube(b, size=1.5); bmesh.ops.translate(b, vec=KM @ Vector(loc), verts=b.verts)
    m_ = bpy.data.meshes.new(nm); b.to_mesh(m_); b.free(); objs.append(bpy.data.objects.new(nm, m_))
for o in objs: TMP.objects.link(o)
export(objs, os.path.join(OUT, 'AxisProbe'))

# ---------------- 4. palette texture next to the kit (upload once, shared by every solid MeshPart)
pal = None
for img in bpy.data.images:
    if img.name.endswith('_Pal'):
        pal = os.path.join(OUT, NAME + '_Palette.png'); img.filepath_raw = pal; img.file_format = 'PNG'; img.save()
        if max(img.size) > MAX_TEX: WARN.append('palette %dpx > %d' % (max(img.size), MAX_TEX))
        break

# ---------------- 5. look -> Roblox Lighting (approximate; verify in Studio, see roblox_pipeline.md "Lighting")
def look():
    L = {}
    sun = next((o for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SUN'), None)
    if sun:
        d = sun.matrix_world.to_3x3() @ Vector((0, 0, -1))               # light travel direction (Blender)
        to_sun = r_pos(-d).normalized()                                   # Roblox space, pointing at the sun
        elev = math.degrees(math.asin(max(-1, min(1, to_sun.y))))
        L['SunDir'] = [round(x, 3) for x in to_sun]; L['SunElevation'] = round(elev, 1)
        # Roblox: the sun rises in the east (+X at latitude 0) and sets in the west; noon = 12
        L['ClockTime'] = round(6 + elev / 15 if to_sun.x >= 0 else 18 - elev / 15, 2)
        c = sun.data.color; L['SunColor'] = [round(c[i] * 255) for i in range(3)]
        L['Brightness'] = round(min(5, sun.data.energy / 1.4), 2)
    hz = bpy.data.materials.get('HazeMat')
    if hz:
        n = next((n for n in hz.node_tree.nodes if n.type == 'PRINCIPLED_VOLUME'), None)
        if n:
            dens = n.inputs['Density'].default_value; col = n.inputs['Color'].default_value
            L['AtmosphereDensity'] = round(min(.32, .2 + dens * 60), 3)   # Roblox Density > ~0.35 washes big maps out
            L['AtmosphereColor'] = [round(col[i] ** (1 / 2.2) * 255) for i in range(3)]
    w = sc.world
    try:
        ramp = next(n for n in w.node_tree.nodes if n.type == 'VALTORGB').color_ramp.elements
        hor, zen = ramp[0].color, ramp[-1].color
        L['Horizon'] = [round(min(1, hor[i]) ** (1 / 2.2) * 255) for i in range(3)]
        L['Zenith'] = [round(min(1, zen[i]) ** (1 / 2.2) * 255) for i in range(3)]
    except Exception: pass
    return L
LOOK = look(); manifest['look'] = LOOK

# ---------------- 6. Luau: setup module + kit prep
def lua_rgb(c): return 'Color3.fromRGB(%d, %d, %d)' % tuple(c)
rows = sorted(ROWS.values(), key=lambda r: (r[1], r[0])) + SROWS
glow = {}
for p in manifest['props'].values():
    for part in p['parts']:
        if part['glow']: glow[part['glow']] = part['color']
for k, v in SLOOK.get('Glow', {}).items(): glow[k] = list(v)
def lrgb(v): return 'Color3.fromRGB(%d, %d, %d)' % tuple(v)
groups = sorted({r[1] for r in rows} | {b['group'] for b in BIG})
G = {g: i + 1 for i, g in enumerate(groups)}
props = sorted({r[0] for r in rows}); P = {p: i + 1 for i, p in enumerate(props)}
def num(x): s = ('%.3f' % x).rstrip('0').rstrip('.'); return '0' if s in ('-0', '') else s
row_lines = ',\n'.join('\t{%d,%d,%s}' % (P[r[0]], G[r[1]], ','.join(num(v) for v in r[2:])) for r in rows)
coll = {p: (manifest['props'][p]['collision'] if p in manifest['props'] else collision_of(p)) for p in props}
L = LOOK
lua = '''-- %(name)sSetup: generated by roblox-map-builder/scripts/roblox_export.py. Do not hand-edit the rows; re-export.
-- Usage (Studio command bar, Edit mode):
--   require(game.ServerStorage.%(name)sSetup).Build(game.ServerStorage.%(name)sKit, workspace)
--   require(game.ServerStorage.%(name)sSetup).ApplyLook()      -- optional, sets Lighting / Atmosphere / Sky colours
-- Kit folder: every GLB from kit/ and static/ imported as a Model named after its file (pivot = file origin).
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")

local M = {}
M.Name = "%(name)s"
M.Tag = "MapBuilder_%(name)s"
M.YAW_FIX = 0          -- degrees; set after the AxisProbe check (0 or 180)
M.PaletteTexture = ""  -- optional rbxassetid:// of %(name)s_Palette.png if the importer dropped the texture
M.Groups = {%(groups)s}
M.Props = {%(props)s}
M.Collision = {%(coll)s}  -- none | box | hull | precise (fidelity is applied by %(name)sKitPrep)
M.Glow = {%(glow)s}
M.Materials = %(mats)s   -- true: every solid part gets Material + Color below (no texture); false: palette texture
M.PartMaterial = {%(partmat)s}
M.PartColor = {%(partcol)s}
-- SurfaceMaterial: static part name -> {Roblox material, Color}. Large ground meshes look like flat paint with the palette
-- texture up close; listing them here swaps in Roblox's tiling Grass / Sand / Ground / Rock material instead.
M.SurfaceMaterial = {%(surfmat)s}
-- TextureTint: {Lua pattern on the part name, Color}. A MeshPart ignores Color while it has a TextureID, so the tint goes
-- through a SurfaceAppearance (ColorMap = the palette, Color = tint): cools / warms a palette swatch without re-exporting.
-- SurfaceAppearance maps can only be set from Studio (command bar / plugin), so run Build in Edit mode.
M.TextureTint = {%(tint)s}
M.GlowTransparency = {%(glowt)s}
M.Haze = %(haze)s
M.LightKeys = {lamp = true, furnace = true, window = true, fire = true}   -- glow keys that also get a small PointLight
M.Light = {Range = 8, Brightness = 0.6}
M.BigParts = {%(big)s}
-- rows: {prop index, group index, x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22, scale}
M.Rows = {
%(rows)s
}

local function styleParts(model: Instance, prop: string)
	local kind = M.Collision[prop] or "hull"
	local all = model:GetDescendants(); table.insert(all, model)        -- a kit file imported as a single MeshPart too
	for _, p in all do
		if p:IsA("BasePart") then
			p.Anchored = true
			p.CanTouch = false
			local glowKey = string.match(p.Name, "_Glow_(.+)$")
			if glowKey then
				p.Material = Enum.Material.Neon
				p.Color = M.Glow[glowKey] or p.Color
				p.Transparency = M.GlowTransparency[glowKey] or p.Transparency
				p.CanCollide = false
				p.CanQuery = false
				p.CastShadow = false
				if M.LightKeys[glowKey] and not p:FindFirstChildOfClass("PointLight") then
					local l = Instance.new("PointLight")
					l.Color = p.Color; l.Range = M.Light.Range; l.Brightness = M.Light.Brightness; l.Shadows = false
					l.Parent = p
				end
			else
				p.CanCollide = kind ~= "none"
				p.CanQuery = kind ~= "none"
				if M.Materials then
					if p:IsA("MeshPart") then p.TextureID = "" end
					p.Material = Enum.Material[M.PartMaterial[p.Name] or "SmoothPlastic"]
					p.Color = M.PartColor[p.Name] or p.Color
				elseif p:IsA("MeshPart") and M.PaletteTexture ~= "" and p.TextureID == "" and not p:FindFirstChildOfClass("SurfaceAppearance") then p.TextureID = M.PaletteTexture end
				if p:IsA("MeshPart") and p.TextureID ~= "" and not p:FindFirstChildOfClass("SurfaceAppearance") then
					for _, t in M.TextureTint do
						if string.match(p.Name, t[1]) then
							local sa = Instance.new("SurfaceAppearance"); sa.Name = "Tint"
							if pcall(function() sa.ColorMap = p.TextureID; sa.Color = t[2] end) then sa.Parent = p else sa:Destroy(); warn("[" .. M.Name .. "] TextureTint needs Edit mode") end
							break
						end
					end
				end
				local sm = M.SurfaceMaterial[p.Name]                               -- big ground: a real tiling Roblox material, not one flat palette swatch
				if sm and p:IsA("MeshPart") then p.TextureID = ""; p.Material = Enum.Material[sm[1]]; p.Color = sm[2] end
				local sa = p:FindFirstChildOfClass("SurfaceAppearance")          -- realistic trees: cards cut out, bark overlay
				if sa then pcall(function() sa.AlphaMode = if string.match(p.Name, "_Trunk$") then Enum.AlphaMode.Overlay else Enum.AlphaMode.Transparency end) end
				if p:IsA("MeshPart") and (string.match(p.Name, "_Leaves$") or string.match(p.Name, "_Branches$")) then pcall(function() p.DoubleSided = true end); p.CastShadow = true end
				if math.max(p.Size.X, p.Size.Y, p.Size.Z) < %(tiny)s then p.CastShadow = false end
			end
		end
	end
end

function M.Build(kit: Instance, parent: Instance?): Model
	parent = parent or workspace
	local old = (parent :: Instance):FindFirstChild(M.Name)
	if old and CollectionService:HasTag(old, M.Tag) then old:Destroy() end      -- idempotent: only our own root
	local root = Instance.new("Model")
	root.Name = M.Name
	CollectionService:AddTag(root, M.Tag)
	local folders = {}
	for i, g in M.Groups do
		local f = Instance.new("Folder"); f.Name = g; f.Parent = root; folders[i] = f
	end
	local fix = CFrame.Angles(0, math.rad(M.YAW_FIX), 0)
	local missing = {}
	for _, r in M.Rows do
		local prop = M.Props[r[1]]
		local tpl = kit:FindFirstChild(prop)
		if not tpl then missing[prop] = true; continue end
		local cf = CFrame.new(r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14]) * fix
		local c = tpl:Clone()
		if c:IsA("Model") then
			if r[15] ~= 1 then c:ScaleTo(c:GetScale() * r[15]) end
			c:PivotTo(cf)
		elseif c:IsA("BasePart") then
			c.Size *= r[15]; c.CFrame = cf
		end
		styleParts(c, prop)
		c.Parent = folders[r[2]]
	end
	for _, b in M.BigParts do
		local p = Instance.new("Part")
		p.Name = b[1]; p.Anchored = true; p.CanTouch = false; p.Material = Enum.Material.SmoothPlastic
		p.Size = Vector3.new(b[6], b[7], b[8]); p.Position = Vector3.new(b[3], b[4], b[5]); p.Color = b[9]
		p.Parent = folders[b[2]]
	end
	local loose = 0                                                           -- every BasePart anchored, always
	for _, p in root:GetDescendants() do
		if p:IsA("BasePart") and not p.Anchored then p.Anchored = true; loose += 1 end
	end
	if loose > 0 then warn("[" .. M.Name .. "] " .. loose .. " parts were not anchored (fixed)") end
	root.Parent = parent
	for prop in missing do warn("[" .. M.Name .. "] kit is missing " .. prop) end
	return root
end

-- flowing water (optional, client): scrolls a Texture on parts whose name has river / stream / falls.
-- Call from a LocalScript with this module in ReplicatedStorage (see roblox_pipeline.md "Flowing water"):
--   require(game.ReplicatedStorage:WaitForChild("%(name)sSetup")).AnimateWater(workspace:WaitForChild("%(name)s"))
M.WaterTexture = ""     -- rbxassetid:// of a tiling streak texture you uploaded; "" = only scroll Textures already on the parts
M.WaterFlow = {river = 6, stream = 6, falls = 14}   -- studs per second along the texture V axis
function M.AnimateWater(root: Instance): RBXScriptConnection?
	local list = {}
	for _, p in root:GetDescendants() do
		if not p:IsA("BasePart") then continue end
		local n = string.lower(p.Name)
		local speed
		for key, s in M.WaterFlow do if string.find(n, key, 1, true) then speed = s end end
		if not speed then continue end
		local texs = {}
		for _, t in p:GetChildren() do if t:IsA("Texture") then table.insert(texs, t) end end
		if #texs == 0 and M.WaterTexture ~= "" then
			for _, face in (if string.find(n, "falls", 1, true) then { Enum.NormalId.Front, Enum.NormalId.Back } else { Enum.NormalId.Top }) do
				local t = Instance.new("Texture")
				t.Texture = M.WaterTexture; t.Face = face; t.StudsPerTileU = 8; t.StudsPerTileV = 8; t.Transparency = 0.45
				t.Parent = p; table.insert(texs, t)
			end
		end
		for _, t in texs do table.insert(list, {t, speed}) end
	end
	if #list == 0 then warn("[" .. M.Name .. "] AnimateWater: no river / stream / falls Textures (set M.WaterTexture)"); return nil end
	local clock = 0
	return game:GetService("RunService").RenderStepped:Connect(function(dt)
		clock += dt
		for _, e in list do e[1].OffsetStudsV = (clock * e[2]) %% e[1].StudsPerTileV end
	end)
end

M.Look = {%(look)s}
function M.ApplyLook()
	local L = M.Look
	if L.ClockTime then
		-- morning and evening give the same sun height on opposite sides: keep the one that matches the Blender sun
		local best, bestDot = L.ClockTime, -2
		for _, t in { L.ClockTime, 24 - L.ClockTime } do
			Lighting.ClockTime = t
			local d = Lighting:GetSunDirection():Dot(L.SunDir.Unit)
			if d > bestDot then best, bestDot = t, d end
		end
		Lighting.ClockTime = best
		if bestDot < 0.8 then warn("[" .. M.Name .. "] sun direction differs from the preview (dot " .. string.format("%%.2f", bestDot) .. "): adjust Lighting.GeographicLatitude") end
	end
	if L.Brightness then Lighting.Brightness = L.Brightness end
	if L.SunColor then Lighting.ColorShift_Top = L.SunColor end
	if L.Zenith then Lighting.Ambient = L.Zenith:Lerp(Color3.new(0, 0, 0), 0.6); Lighting.OutdoorAmbient = L.Zenith:Lerp(Color3.fromRGB(140, 140, 140), 0.8) end   -- mostly neutral: a sky-blue ambient turns pale rock to ice
	local atm = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
	if L.AtmosphereDensity then atm.Density = L.AtmosphereDensity end
	if L.AtmosphereColor then atm.Color = L.AtmosphereColor end
	if L.Horizon then atm.Decay = L.Horizon end
	atm.Haze = M.Haze; atm.Glare = 0.3
	atm.Parent = Lighting
	local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
	bloom.Intensity = 0.35; bloom.Size = 16; bloom.Threshold = 1.05            -- Neon glows without blowing out
	bloom.Parent = Lighting
	local cc = Lighting:FindFirstChild("MapBuilderGrade") or Instance.new("ColorCorrectionEffect")
	cc.Name = "MapBuilderGrade"; cc.Contrast = 0.12; cc.Saturation = 0.12
	if L.SunColor then cc.TintColor = Color3.new(1, 1, 1):Lerp(L.SunColor, 0.12) end
	cc.Parent = Lighting
end

return M
''' % {
    'name': NAME, 'tiny': num(TINY),
    'groups': ', '.join('"%s"' % g for g in groups), 'props': ', '.join('"%s"' % p for p in props),
    'coll': ', '.join('%s = "%s"' % (p, coll[p]) for p in props),
    'glow': ', '.join('%s = %s' % (k, lua_rgb(v)) for k, v in sorted(glow.items())),
    'mats': 'true' if MATS else 'false',
    'surfmat': ', '.join('["%s"] = {"%s", %s}' % (k, v[0], lrgb(v[1])) for k, v in sorted(SLOOK.get('SurfaceMaterial', {}).items())),
    'tint': ', '.join('{"%s", %s}' % (p, lrgb(c)) for p, c in SLOOK.get('TextureTint', [])),
    'glowt': ', '.join('%s = %s' % (k, num(v)) for k, v in sorted(SLOOK.get('GlowTransparency', {}).items())),
    'haze': num(SLOOK.get('Haze', 0.5)),
    'partmat': ', '.join('["%s"] = "%s"' % (k, v) for k, v in sorted(PARTMAT.items())),
    'partcol': ', '.join('["%s"] = %s' % (k, lua_rgb(v)) for k, v in sorted(PARTCOL.items())),
    'big': ', '.join('{"%s", %d, %s, %s, %s}' % (b['name'], G[b['group']], ','.join(num(x) for x in b['pos']),
                                                 ','.join(num(x) for x in b['size']), lua_rgb(b['color'])) for b in BIG),
    'rows': row_lines,
    'look': ', '.join(('%s = %s' % (k, lua_rgb(v)) if k in ('SunColor', 'AtmosphereColor', 'Horizon', 'Zenith') else
                       '%s = %s' % (k, num(v)) if isinstance(v, (int, float)) else '%s = Vector3.new(%s)' % (k, ','.join(num(x) for x in v)))
                      for k, v in L.items()),
}
open(os.path.join(OUT, NAME + 'Setup.lua'), 'w', encoding='utf8').write(lua)

prep = '''-- %(name)sKitPrep: run ONCE in the Studio command bar (Edit mode) after importing the kit into ServerStorage.%(name)sKit.
-- CollisionFidelity cannot be changed on an existing MeshPart, so each solid part is re-created with
-- AssetService:CreateMeshPartAsync using the fidelity its prop needs; glow parts get Box + no collision.
local AssetService = game:GetService("AssetService")
local kit = game.ServerStorage:WaitForChild("%(name)sKit")
local Setup = require(game.ServerStorage:WaitForChild("%(name)sSetup"):Clone())  -- a clone, so an edited Setup is never read from the require cache
local FID = { none = Enum.CollisionFidelity.Box, box = Enum.CollisionFidelity.Box, hull = Enum.CollisionFidelity.Hull,
	precise = Enum.CollisionFidelity.PreciseConvexDecomposition }
local done = 0
for _, model in kit:GetChildren() do
	local kind = Setup.Collision[model.Name] or "hull"
	for _, p in model:GetDescendants() do
		if p:IsA("MeshPart") then
			local want = string.find(p.Name, "_Glow_") and Enum.CollisionFidelity.Box or FID[kind]
			if p.CollisionFidelity ~= want and not pcall(function() p.CollisionFidelity = want end) then
				local ok, fresh = pcall(AssetService.CreateMeshPartAsync, AssetService, p.MeshId,
					{ CollisionFidelity = want, RenderFidelity = Enum.RenderFidelity.Automatic })
				if ok then
					p:ApplyMesh(fresh)
					done += 1
				else
					warn(model.Name, p.Name, fresh)
				end
			end
		end
	end
end
print("[%(name)sKitPrep] re-meshed", done, "parts")
''' % {'name': NAME}
open(os.path.join(OUT, NAME + 'KitPrep.lua'), 'w', encoding='utf8').write(prep)

# ---------------- 6b. performance budgets (hard)
OVER = []
for pn_, v_ in manifest['props'].items():
    lim = BUDGET_HERO if re.search(HERO_RE, pn_) else BUDGET_PROP
    if v_['tris'] > lim: OVER.append('prop %s: %d tris > %d (decimate, drop hidden faces, fewer bevel segments)' % (pn_, v_['tris'], lim))
_st = sum(x['tris'] for x in manifest['static'])
if _st > BUDGET_STATIC: OVER.append('static chunks: %d tris > %d (simplify ground / horizon, use Sky + Atmosphere)' % (_st, BUDGET_STATIC))
_placed = {}
for r_ in ROWS.values():
    if r_[0] in manifest['props']: _placed[r_[0]] = _placed.get(r_[0], 0) + manifest['props'][r_[0]]['tris']
_tot = sum(_placed.values()) + _st
if _tot > BUDGET_TOTAL:
    top = sorted(_placed.items(), key=lambda kv: -kv[1])[:6]
    OVER.append('map total: %d tris > %d. Biggest placed costs: %s' % (_tot, BUDGET_TOTAL, ', '.join('%s %dk' % (k, v // 1000) for k, v in top)))

PLACED = list(_PL.values())                           # [(prop, [objects])]
# ---------------- 6c. placement check (hard): see references/roblox_pipeline.md "Placement checks"
#   clip   every non-rock prop: > 5% of its body inside a rock / static chunk / another prop (foliage: > 8%)
#   float  every prop: lowest point > 0.5 above the surface under its footprint (foliage: > 1.0 under its origin)
#   water  flat water needs a bed <= 8 below every point and its edges under / against the bank; falls touch a lip + pool
#   collide foliage none, rocks solid, walkable statics solid (or solid just under), walk-through props not hull,
#          paths not blocked by colliding props; optional --cliff-buffer: studs kept clear round rock / cliff feet
SOFT_RE = re.compile(arg('--soft', r'(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant'))
ROCK_RE = re.compile(arg('--rock', r'(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag'))
FLOAT_OK_RE = re.compile(arg('--float-ok', r'(?i)hang|vine|ivy|lamp-rope|rope|cloud|bird|lily|canopy|_leaves|_branches|glow|beam|debris|orbit'))
WATER_RE = re.compile(arg('--water', r'(?i)water|lake|river|stream|pond|pool|falls|moat'))
FALLS_RE = re.compile(r'(?i)falls|waterfall|cascade')
FOLIAGE_RE = re.compile(r'(?i)_leaves|_branches|leaf|tuft|grass|flower|petal|blossom|fern|reed|lily|lilies|vine|ivy|moss|bush|shrub|gnarledcanopy')
NOT_FOLIAGE_RE = re.compile(r'(?i)pot|planter|tub|bed|trunk|stump|stall|stand|shop')
WALK_RE = re.compile(arg('--walk', r'(?i)bridge|stair|dock|pier|arch|gate|door|tunnel|portal|torii|ramp|house|hall|shop|stall|pavilion|temple|inn'))
PATH_RE = re.compile(arg('--path', r'(?i)path|trail(?!er)'))   # not 'Trailer'
NO_WALK_RE = re.compile(arg('--no-walk', r'(?i)horizon|sky|backdrop|far|distant|cloud|skirt|backwall|mountain'))
BUFFER = float(arg('--cliff-buffer', '0'))
CLIFF_RE = re.compile(arg('--cliff', r'(?i)rock|cliff|boulder|crag|mesa|butte'))   # buffer: rocks >= 10 tall
CLIP = []; COUNTS = {k: 0 for k in ('clip', 'float', 'water', 'falls', 'collision', 'buffer')}
if '--no-clip-check' not in ARGV:
    from mathutils.bvhtree import BVHTree
    _bm = bmesh.new(); OWN = []; OWNERS = []          # BVH face index -> owner; owner = {name, kind, coll, obs}
    def _owner(name, obs, static=False):
        if WATER_RE.search(name): kind = 'water'
        elif static: kind = 'static'
        elif ROCK_RE.search(name): kind = 'rock'
        else: kind = 'prop'
        coll = collision_of(name) if static or name not in manifest['props'] else manifest['props'][name]['collision']
        OWNERS.append({'name': name, 'kind': kind, 'coll': coll, 'obs': obs, 'static': static}); return len(OWNERS) - 1
    def _add(ob, w):
        m = ob.data.copy(); m.transform(ob.matrix_world); _bm.from_mesh(m); OWN.extend([w] * len(m.polygons)); bpy.data.meshes.remove(m)
    for ob, grp in STATIC:
        w = _owner(ob.name, [ob], True); _add(ob, w)
    PW = []                                                       # owner per placed prop (None = soft: never an obstacle)
    for prop, obs in PLACED:
        if SOFT_RE.search(prop): PW.append(None); continue
        w = _owner(prop, obs)
        for ob in obs: _add(ob, w)
        PW.append(w)
    BVH = BVHTree.FromBMesh(_bm); _bm.free()
    SOLID = BVH
    def cast(o, d, dist, ok):
        """first hit along d whose owner passes ok(owner index); other owners' faces are stepped through"""
        o = Vector(o); left = dist
        for _ in range(32):
            hit, nrm, i, dd = BVH.ray_cast(o, d, left)
            if hit is None: return None
            if ok(OWN[i]): return hit, nrm, OWN[i], dist - left + dd
            step = dd + 1e-3; o = hit + d * 1e-3; left -= step
            if left <= 0: return None
        return None
    def near(p, r, ok):
        return [h for h in BVH.find_nearest_range(p, r) if ok(OWN[h[2]])]
    DIRS = [Vector(d) for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))]
    UP = Vector((0, 0, 1)); DOWN = Vector((0, 0, -1))
    def inside(p, ok=lambda w: OWNERS[w]['kind'] != 'water'):
        """inside ONE solid: >= 5 of 6 axis rays first hit a back face of the same owner (open sheets stacked from
        several owners - paving over ground over a wall - do not add up to a fake volume)"""
        back = {}
        for d in DIRS:
            h = cast(p, d, 400, ok)
            if h is not None and h[1].dot(d) > 0: back[h[2]] = back.get(h[2], 0) + 1
        w = max(back, key=back.get, default=None)
        return w if w is not None and back[w] >= 5 else None
    def solid_ok(me):
        return lambda w: w != me and OWNERS[w]['kind'] != 'water'
    def any_ok(me):
        return lambda w: w != me
    def pts_of(obs, cap=160):
        nv = sum(len(ob.data.vertices) for ob in obs); step = max(1, nv // cap); pts = []
        for ob in obs:
            vs = ob.data.vertices; pts += [ob.matrix_world @ vs[i].co for i in range(0, len(vs), step)]
        return pts
    def bounds(obs):
        cs = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
        lo = Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
        hi = Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
        return lo, hi
    _seen = {}
    def fail(key, check, msg):
        _seen.setdefault(key, []).append(msg); COUNTS[check] += 1
    def at(obs): return '(%.0f, %.0f, %.0f)' % tuple(r_pos(obs[0].matrix_world.translation))
    for (prop, obs), me in zip(PLACED, PW):
        soft = me is None
        pts = pts_of(obs)
        lo_z = min((q.z for q in pts), default=0); hi_z = max((q.z for q in pts), default=0)
        body = [q for q in pts if q.z > lo_z + max(.6, .15 * (hi_z - lo_z))]   # the base is sunk / bedded on purpose
        isrock = bool(ROCK_RE.search(prop)); iswater = bool(WATER_RE.search(prop))
        if body and not isrock and not iswater:
            ins = [w for w in (inside(q, solid_ok(me)) for q in body) if w is not None]
            if len(ins) / len(body) > (.08 if soft else .05):
                w = max(set(ins), key=ins.count)
                fail(prop, 'clip', '%s at %s: %d%% inside %s' % (prop, at(obs), 100 * len(ins) // len(body), OWNERS[w]['name']))
        if soft:                                                              # foliage: origin ray, 1.0 tolerance
            o = obs[0].matrix_world.translation; lowest = lo_z
            hit = cast(Vector((o.x, o.y, lowest + 3)), DOWN, 80, lambda w: True)
            if hit is not None and lowest - hit[0].z > 1.0 and not FLOAT_OK_RE.search(prop):
                fail(prop + '#f', 'float', '%s at %s: floats %.1f studs above the ground' % (prop, at(obs), lowest - hit[0].z))
        elif not FLOAT_OK_RE.search(prop) and not FALLS_RE.search(prop):
            lo, hi = bounds(obs); c = (lo + hi) / 2; sx, sy = (hi.x - lo.x) * .35, (hi.y - lo.y) * .35
            surf = []
            for dx, dy in ((0, 0), (-1, -1), (1, -1), (1, 1), (-1, 1)):
                h = cast(Vector((c.x + dx * sx, c.y + dy * sy, hi.z + .5)), DOWN, hi.z - lo.z + 200, any_ok(me))
                if h is not None: surf.append(h[0].z)
            gap = lo.z - max(surf) if surf else 1e9
            if gap > .5:
                fail(prop + '#f', 'float', '%s at %s: lowest point %s above the surface under it' % (prop, at(obs), ('%.1f studs' % gap) if surf else 'with nothing'))
    # ---- water
    WATERS = [(w, o) for w, o in enumerate(OWNERS) if o['kind'] == 'water']
    for w, o in WATERS:
        name = o['name']; obs = o['obs']
        if FALLS_RE.search(name):                                             # waterfall: lip at the top, pool at the foot
            pts = [ob.matrix_world @ v.co for ob in obs for v in ob.data.vertices]
            zl = min(p.z for p in pts); zh = max(p.z for p in pts); band = max(1.5, .04 * (zh - zl))
            top = [p for p in pts if p.z > zh - band][::max(1, len([p for p in pts if p.z > zh - band]) // 60)]
            bot = [p for p in pts if p.z < zl + band][::max(1, len([p for p in pts if p.z < zl + band]) // 60)]
            lip = sum(1 for p in top if near(p, 2.5, lambda v, w=w: v != w and OWNERS[v]['kind'] != 'water'))
            pool = sum(1 for p in bot if near(p, 3.0, lambda v, w=w: v != w and OWNERS[v]['kind'] == 'water'))
            if lip < .5 * len(top): fail(name + '#lip', 'falls', '%s at %s: top does not meet a rock / ground lip (%d of %d top points within 2.5)' % (name, at(obs), lip, len(top)))
            if pool < .5 * len(bot): fail(name + '#pool', 'falls', '%s at %s: foot does not meet a pool (%d of %d foot points within 3 of water)' % (name, at(obs), pool, len(bot)))
            continue
        nobed = []; spill = []; tot = 0; edges = 0
        for ob in obs:
            Mw = ob.matrix_world; me_ = ob.data; N3 = Mw.to_3x3().inverted().transposed()
            ups = [f for f in me_.polygons if (N3 @ f.normal).normalized().z > .9]
            if not ups: continue
            cand = [Mw @ f.center for f in ups] + [Mw @ me_.vertices[i].co for f in ups for i in f.vertices]
            cand = cand[::max(1, len(cand) // 400)]
            for p in cand:
                tot += 1; q = p + UP * .02
                h = cast(q, UP, 6, lambda v: OWNERS[v]['kind'] != 'water')
                if h is not None and h[1].z > .3: continue                    # under the bank / beach: hidden
                h = cast(q, DOWN, 8, lambda v: OWNERS[v]['kind'] != 'water')
                if h is None: nobed.append(p)
            upv = {i for f in ups for i in f.vertices}; cnt = {}
            for f in me_.polygons:                                        # the water's own open edge (a closed pool
                for ek in f.edge_keys: cnt[ek] = cnt.get(ek, 0) + 1         # prop with a rim has none to test)
            bverts = sorted({i for ek, k in cnt.items() if k == 1 and ek[0] in upv and ek[1] in upv for i in ek})
            for i in bverts[::max(1, len(bverts) // 200)]:
                p = Mw @ me_.vertices[i].co; edges += 1
                if near(p, .6, lambda v, w=w: v != w and OWNERS[v]['kind'] == 'water'): continue   # runs into other water
                h = cast(p + UP * 30, DOWN, 60, lambda v: OWNERS[v]['kind'] != 'water')
                if h is not None and h[0].z >= p.z - .05: continue            # bank at / above the water edge
                if near(p, .6, lambda v: OWNERS[v]['kind'] != 'water'): continue   # meets a wall / rim
                spill.append(p)
        if tot and len(nobed) > .02 * tot:
            fail(name + '#bed', 'water', '%s: %d of %d surface points have no bed within 8 studs (floats); first at (%.0f, %.0f, %.0f)' % (name, len(nobed), tot, *r_pos(nobed[0])))
        if edges and len(spill) > .02 * edges:
            fail(name + '#bank', 'water', '%s: %d of %d edge points stand above the bank (spills over); first at (%.0f, %.0f, %.0f)' % (name, len(spill), edges, *r_pos(spill[0])))
    # ---- collision sanity
    COLLIDES = lambda v: OWNERS[v]['coll'] != 'none' and OWNERS[v]['kind'] != 'water'
    for pn_, v_ in sorted(manifest['props'].items()):
        c_ = v_['collision']
        if FOLIAGE_RE.search(pn_) and not NOT_FOLIAGE_RE.search(pn_) and not ROCK_RE.search(pn_) and c_ != 'none':
            fail(pn_ + '#c', 'collision', '%s: foliage with collision %s (players snag on leaves): make it none' % (pn_, c_))
        if ROCK_RE.search(pn_) and c_ == 'none' and max(v_['size']) > 4 and pn_ in {p for p, _ in PLACED}:
            fail(pn_ + '#c', 'collision', '%s: %.0f-stud rock with collision none (players walk into it): hull' % (pn_, max(v_['size'])))
        if WALK_RE.search(pn_) and c_ == 'hull':
            fail(pn_ + '#c', 'collision', '%s: walk-through prop (door / bridge / stair) with hull collision fills its openings: precise or box' % pn_)
    for w, o in enumerate(OWNERS):
        if o['kind'] == 'water' and (o['coll'] in ('hull', 'box') or (o['static'] and o['coll'] == 'precise')):
            fail(o['name'] + '#c', 'collision', '%s: water with %s collision (a solid lid players walk on): none' % (o['name'], o['coll'])); continue
        if not o['static'] or o['kind'] == 'water' or NO_WALK_RE.search(o['name']) or FLOAT_OK_RE.search(o['name']): continue
        if o['coll'] == 'hull':
            fail(o['name'] + '#c', 'collision', '%s: walkable static with hull collision (a blob over the floor): precise' % o['name']); continue
        if o['coll'] != 'none': continue
        ob = o['obs'][0]; Mw = ob.matrix_world
        ups = [Mw @ f.center for f in ob.data.polygons if (Mw.to_3x3() @ f.normal).normalized().z > .7]
        ups = ups[::max(1, len(ups) // 200)]
        bad = [p for p in ups if cast(p + UP * .05, DOWN, 1.5, lambda v, w=w: v != w and COLLIDES(v)) is None]
        if ups and len(bad) > .05 * len(ups):
            fail(o['name'] + '#c', 'collision', '%s: walkable surface with collision none and no solid floor within 1.5 below (%d of %d points): players fall through' % (o['name'], len(bad), len(ups)))
    for w, o in enumerate(OWNERS):                                    # paths blocked by colliding props
        if not PATH_RE.search(o['name']) or o['kind'] == 'water': continue
        blk = {}
        for ob in o['obs']:
            Mw = ob.matrix_world
            ups = [Mw @ f.center for f in ob.data.polygons if (Mw.to_3x3() @ f.normal).normalized().z > .7]
            for p in ups[::max(1, len(ups) // 400)]:
                h = cast(p + UP * .3, UP, 5, lambda v, w=w: v != w and COLLIDES(v) and not OWNERS[v]['static'] and not WALK_RE.search(OWNERS[v]['name']))
                if h is not None: blk.setdefault(h[2], []).append(p)
        for v, ps in blk.items():
            if len(ps) >= 2:
                fail(o['name'] + '#p%d' % v, 'collision', '%s: path blocked by %s (%s collision) at (%.0f, %.0f, %.0f)' % (o['name'], OWNERS[v]['name'], OWNERS[v]['coll'], *r_pos(ps[0])))
    if BUFFER > 0:                                                    # clear ground round rock / cliff feet
        for o in OWNERS:
            if (o['kind'] == 'rock' or o['static']) and CLIFF_RE.search(o['name']):
                lo_, hi_ = bounds(o['obs']); o['cliff'] = hi_.z - lo_.z >= 10
        ROCKY = lambda v: OWNERS[v].get('cliff', False)
        for (prop, obs), me in zip(PLACED, PW):
            if ROCK_RE.search(prop) or FLOAT_OK_RE.search(prop) or WATER_RE.search(prop): continue
            if me is None and not prop.endswith('_Trunk'): continue
            lo, hi = bounds(obs)
            if me is not None and max(hi.x - lo.x, hi.y - lo.y) < 6: continue    # small decor may sit by rocks
            c = (lo + hi) / 2; z = lo.z + 1.5
            if me is None:                                            # tree: the trunk base, not the branch spread
                o_ = obs[0].matrix_world.translation
                ring = [Vector((o_.x + math.cos(a) * 1.5, o_.y + math.sin(a) * 1.5, z)) for a in [k * math.tau / 8 for k in range(8)]]
            else:
                ring = [Vector((c.x + dx * (hi.x - lo.x) / 2, c.y + dy * (hi.y - lo.y) / 2, z)) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            hits = [h for p in ring for h in near(p, BUFFER, ROCKY) if h[0].z > lo.z + 2]   # rock rising beside, not the ledge under it
            if hits:
                d = min(h[3] for h in hits)
                fail(prop + '#b', 'buffer', '%s at %s: %.1f studs from %s (buffer %.0f)' % (prop, at(obs), d, OWNERS[OWN[min(hits, key=lambda h: h[3])[2]]]['name'], BUFFER))
        for w, o in enumerate(OWNERS):
            if not PATH_RE.search(o['name']) or not o['static']: continue
            ob = o['obs'][0]; Mw = ob.matrix_world; vs = ob.data.vertices
            bad = [Mw @ vs[i].co for i in range(0, len(vs), max(1, len(vs) // 400)) if any(h[0].z > (Mw @ vs[i].co).z + 2 for h in near(Mw @ vs[i].co + UP * 1.5, BUFFER, ROCKY))]
            if bad: fail(o['name'] + '#b', 'buffer', '%s: %d path points within %.0f studs of a rock foot, first at (%.0f, %.0f, %.0f)' % (o['name'], len(bad), BUFFER, *r_pos(bad[0])))
    for k, v in _seen.items(): CLIP += v[:3] + (['... and %d more %s' % (len(v) - 3, k.split('#')[0])] if len(v) > 3 else [])
    if CLIP: OVER += ['placement: ' + c for c in CLIP]
print('CHECK_COUNTS ' + json.dumps(COUNTS))

# ---------------- 7. validator report
total_tris = sum(manifest['props'][r[0]]['tris'] for r in ROWS.values() if r[0] in manifest['props']) + sum(s['tris'] for s in manifest['static'])
inst = len(ROWS); parts = sum(len(manifest['props'][r[0]]['parts']) for r in ROWS.values() if r[0] in manifest['props'])
xs = [r[2] for r in ROWS.values()]; zs = [r[4] for r in ROWS.values()]
lines = ['# %s - Roblox export report' % NAME, '',
         '| Check | Value | Limit / target |', '|---|---|---|',
         '| Kit props | %d | reuse: fewer unique meshes = less memory |' % len(manifest['props']),
         '| Placed props | %d (%d MeshParts) | under ~5k parts per area for phones |' % (inst, parts),
         '| Static chunks | %d | each <= %d tris, <= %d studs |' % (len(manifest['static']), MAX_TRIS, MAX_EXTENT),
         '| Oversize faces -> Parts | %d | sea / skirt planes |' % len(BIG),
         '| Total placed tris | %s | hard budget %s (--budget) |' % (format(total_tris, ','), format(BUDGET_TOTAL, ',')),
         '| Largest prop | %s (%d tris) | <= %d per MeshPart |' % (max(manifest['props'].items(), key=lambda kv: max(p['tris'] for p in kv[1]['parts']))[0],
                                                       max(p['tris'] for v in manifest['props'].values() for p in v['parts']), MAX_TRIS),
         '| Footprint | x %.0f..%.0f, z %.0f..%.0f | keep under 2,048 from origin for float precision comfort |' % (min(xs), max(xs), min(zs), max(zs)),
         '| Palette | %s | <= %d px |' % (os.path.basename(pal) if pal else 'none', MAX_TEX),
         '| Placement checks | %s | all 0 (clip, float, water, falls, collision, buffer) |' % ', '.join('%s %d' % kv for kv in COUNTS.items()),
         '', '## Collision per prop', '', '| Prop | Collision | Tris |', '|---|---|---|']
lines += ['| %s | %s | %d |' % (p, v['collision'], v['tris']) for p, v in sorted(manifest['props'].items())]
_rank = sorted(_placed.items(), key=lambda kv: -kv[1])[:12]
lines += ['', '## Where the triangles go (cut here first)', '', '| Prop | Copies | Tris each | Placed tris | Share |', '|---|---|---|---|---|']
lines += ['| %s | %d | %d | %s | %.0f%% |' % (k, v // max(1, manifest['props'][k]['tris']), manifest['props'][k]['tris'], format(v, ','), 100 * v / max(1, _tot)) for k, v in _rank]
_dense = []
for pn_, v_ in manifest['props'].items():
    sz_ = max(max(p['size']) for p in v_['parts']) or 1
    if v_['tris'] / sz_ > 600 and v_['tris'] > 1500: _dense.append('%s: %d tris for %.1f studs' % (pn_, v_['tris'], sz_))
if _dense: lines += ['', '## Over-detailed for their size (> 600 tris per stud; players do not see that detail)', ''] + ['- ' + d for d in _dense]
lines += ['', '## Budget (%s)' % ('OVER' if OVER else 'ok'), ''] + (['- ' + w for w in OVER] if OVER else ['- within budget: total <= %d, prop <= %d (hero <= %d), static <= %d' % (BUDGET_TOTAL, BUDGET_PROP, BUDGET_HERO, BUDGET_STATIC)])
lines += ['', '## Warnings (%d)' % len(WARN), ''] + (['- ' + w for w in WARN] if WARN else ['- none'])
lines += ['', '## Next steps', '', '1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; '
          'set pivot to scene origin; anchored; insert into ServerStorage, folder `%sKit`).' % NAME,
          '2. Insert `%sSetup.lua` as ModuleScript ServerStorage.%sSetup, run `%sKitPrep.lua` once in the command bar.' % (NAME, NAME, NAME),
          '3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.',
          '4. Command bar: `require(game.ServerStorage.%sSetup).Build(game.ServerStorage.%sKit, workspace)`, then `.ApplyLook()`.' % (NAME, NAME)]
open(os.path.join(OUT, 'report.md'), 'w', encoding='utf8').write('\n'.join(lines))
json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
bpy.data.collections.remove(TMP)
if not OVER or ALLOW_OVER: print('EXPORT_OK props=%d rows=%d static=%d big=%d warn=%d tris=%d -> %s' % (len(manifest['props']), inst, len(manifest['static']), len(BIG), len(WARN), total_tris, OUT))
if OVER:
    for w_ in OVER: print('OVER_BUDGET ' + w_)
    if not ALLOW_OVER:
        print('EXPORT_FAILED: fix every OVER_BUDGET line (cut triangles; move/regrounded clipping or floating props) and re-export')
        sys.stdout.flush(); os._exit(1)
