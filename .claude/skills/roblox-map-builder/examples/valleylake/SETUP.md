# Mistvale Lake - Studio setup

Files: `roblox/` = export of `valley_map.blend` with `--hero "^(TreeOakHero_\w+|Waterfall)$" --cliff-buffer 8` and **no `--materials`**:
every solid MeshPart carries ONE shared hand-painted-look atlas, `roblox/MistvaleLake_Palette.png` (1024 px, 4 x 4
painted blocks made by `paint.py`: rock strokes + cracks + chips + light top-edge streaks, moss / grass dabs, leaf
shapes with lit rims for broadleaf / pine / blossom, timber grain, roof ribs, cobbles, sand, paper, water). UVs: block
= material, block row = the per-vertex shade (dark under, light top), block x = a planar projection of the surface, so
strokes follow the forms. Glow keys (Neon): `lamp` (lanterns, + PointLight), `shoji` (warm paper panels),
`falls` (waterfall streaks), `foam` (plunge-pool foam + spray). 76 kit props, 411 placements, 10 static chunks,
**419,132 placed triangles**, EXPORT_OK, every placement check at 0 (clip, float, water, falls, collision, 8-stud cliff buffer)
(budget 450k, report.md: Budget ok). Nothing is imported yet. The TREES are the exception to the one-atlas rule: they are
the realistic alpha-card trees (next section) and carry their own textures.

### Realistic trees (`Tree*` props: own textures, SurfaceAppearance)
Made by `examples/oaktrees/gen_trees.py` (imported by `valley_map.py`, species table `TREES` there): every tree is THREE
MeshParts on one origin (trunk base), placed with the same CFrame: `Tree<Species>_Trunk` (bark tubes),
`Tree<Species>_Branches` (crossed twig cards) and `Tree<Species>_Leaves` (leaf / needle cluster cards).

| Species | Where | Tris (Trunk / Branches / Leaves) | Copies |
|---|---|---|---|
| `OakHero` | the islet: big leaning gnarled oak, 8 surface roots, crown swung out over the lake (scale 1.2) | 7,502 / 1,376 / 7,000 | 1 |
| `OakA`, `OakB` | broad oaks framing the west beach and the east shore | 4,530 / 872 / 2,984 ; 3,958 / 704 / 1,880 | 1, 2 |
| `YoungTree` | saplings in the village and along the paths | 910 / 152 / 540 | 5 |
| `OakPink` | the flowering tree by the dock (the realistic oak, pink petal atlas) | 3,354 / 616 / 1,792 | 1 |
| `PineA`, `PineB` | tall / fuller firs near the camera | 1,914 / 120 / 5,500 ; 1,766 / 216 / 5,380 | 1, 1 |
| `PineC` | cheap background fir: back village, terrace, cliff shelves | 1,064 / 32 / 1,996 | 13 |

Each tree GLB in `roblox/kit/` embeds its own PNGs (colour + OpenGL normal map; the same files are in
`examples/oaktrees/roblox/textures/`): `*_Trunk` = `<bark>_bark_color` (1024, tiling, UVs run past 0..1 on purpose) +
`<bark>_bark_normal`; `*_Leaves` = `<leaf>_leaves_color` (1024 RGBA 4 x 4 cluster atlas, alpha cut-out) +
`<leaf>_leaves_normal`; `*_Branches` = `<twig>_twigs_color` (512 RGBA) + normal. Valley grades (`_v` files: brighter,
more saturated leaves so they sit in the cyan haze): `oak_v`, `young_v`, `fir_v` (blue-green needles), `blossom_v`.

Import (same Import 3D pass as the rest of `kit/`), then check every `Tree*` MeshPart:
1. A `SurfaceAppearance` child holding ColorMap + NormalMap. If the importer made only a `TextureID` (or dropped the
   PNG), upload the PNG from `examples/oaktrees/roblox/textures/` and build the SurfaceAppearance by hand
   (ColorMap = `*_color`, NormalMap = `*_normal`).
2. **AlphaMode**: `*_Trunk` = **Overlay**, `*_Branches` and `*_Leaves` = **Transparency** (the GLB marks the cards
   alpha BLEND, double-sided). `S.Build` sets these for you with a pcall, and so does the command bar snippet below, if
   the property can be written.
3. `*_Branches` / `*_Leaves`: DoubleSided = true (else the cards vanish from behind), CastShadow on; collision none
   (`M.Collision`: CanCollide / CanQuery off); `*_Trunk` collision hull.
4. Build never puts the palette `TextureID` on a part that has a SurfaceAppearance.
```lua
for _, p in workspace.MistvaleLake:GetDescendants() do
    local sa = p:IsA("MeshPart") and p:FindFirstChildOfClass("SurfaceAppearance")
    if sa and p.Name:match("^Tree") then
        sa.AlphaMode = if p.Name:match("_Trunk$") then Enum.AlphaMode.Overlay else Enum.AlphaMode.Transparency
        if not p.Name:match("_Trunk$") then p.DoubleSided = true; p.CanCollide = false; p.CanQuery = false end
    end
end
```

### How the painted texture loads
Each GLB embeds the same atlas. Studio's 3D importer turns it into the MeshPart's `TextureID` (one texture upload,
deduplicated by content). If the importer drops it or makes copies, upload `MistvaleLake_Palette.png` once (Asset
Manager / Creator Hub), then set it everywhere (phone-friendly: one 1024 texture for the whole map):
```lua
local S = require(game.ServerStorage.MistvaleLakeSetup)
S.PaletteTexture = "rbxassetid://<your uploaded atlas id>"     -- never invent this id: it is the one Roblox gives you
for _, p in game.ServerStorage.MistvaleLakeKit:GetDescendants() do
    if p:IsA("MeshPart") and not p.Name:find("_Glow_") then p.TextureID = S.PaletteTexture end
end
```
MeshPart `Color` is ignored while a `TextureID` is set, so the painted colours are exactly the preview's. Want a
material response too (grass sheen, wood bump)? Put a `SurfaceAppearance` with `ColorMap` = the atlas id on a part
instead of TextureID (same UVs); keep it to the few hero parts.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.MistvaleLakeKit` (studs, pivot at
   origin, anchored, one Model per file). Import `roblox/AxisProbe.glb` once: the arrow must point along -Z, else set
   `M.YAW_FIX = 180` in the setup module.
2. ModuleScripts in ServerStorage: `MistvaleLakeSetup` = `roblox/MistvaleLakeSetup.lua`, `MistvaleLakeHooks` =
   `roblox/MistvaleLakeHooks.lua`. Run `roblox/MistvaleLakeKitPrep.lua` once in the command bar.
3. Command bar (build, hooks, then the look below):
```lua
local S = require(game.ServerStorage.MistvaleLakeSetup)
S.Build(game.ServerStorage.MistvaleLakeKit, workspace)
require(game.ServerStorage.MistvaleLakeHooks).Build(workspace.MistvaleLake)
```

## The look: bright cyan daylight, strong blue haze, soft bloom (the acceptance criterion)
Paste after Build (do NOT also run `S.ApplyLook()`: these values replace it). Tuned against the Blender preview
(`previews/map_beauty.png`, whose Blender haze is now matched to these values: no heavy preview haze hiding geometry).
```lua
local L = game.Lighting
L.Technology = Enum.Technology.Future          -- ShadowMap on low-end if needed (lanterns lose their light only)
L.ClockTime = 14.5; L.GeographicLatitude = 30  -- sun high (~52 deg) from the south-west, behind-left of the beauty view
L.Brightness = 3.2; L.ExposureCompensation = 0.15
L.Ambient = Color3.fromRGB(96, 138, 190)       -- cool blue shadows, never grey
L.OutdoorAmbient = Color3.fromRGB(140, 192, 240)
L.ColorShift_Top = Color3.fromRGB(255, 248, 232); L.ColorShift_Bottom = Color3.fromRGB(60, 112, 175)
L.EnvironmentDiffuseScale = 1; L.EnvironmentSpecularScale = 0.7; L.GlobalShadows = true
for _, c in L:GetChildren() do if c:IsA("PostEffect") or c:IsA("Atmosphere") or c:IsA("Sky") then c:Destroy() end end

local atm = Instance.new("Atmosphere")          -- light cyan haze; tested in Studio: 0.6 washed the map solid blue, 0.3 read well
atm.Density = 0.28; atm.Offset = 0.1; atm.Haze = 1.2; atm.Glare = 0.2      -- keep Density <= ~0.32 on a map this size
atm.Color = Color3.fromRGB(150, 226, 255); atm.Decay = Color3.fromRGB(88, 168, 240); atm.Parent = L

local sky = Instance.new("Sky")                 -- default Roblox sky textures, deep blue zenith from the Atmosphere
sky.SunAngularSize = 14; sky.StarCount = 0; sky.CelestialBodiesShown = true; sky.Parent = L

local bloom = Instance.new("BloomEffect")       -- soft glow on water, foam, motes, sand highlights
bloom.Intensity = 0.6; bloom.Size = 28; bloom.Threshold = 0.9; bloom.Parent = L

local cc = Instance.new("ColorCorrectionEffect") -- the saturated painterly grade
cc.Brightness = 0.03; cc.Contrast = 0.12; cc.Saturation = 0.28; cc.TintColor = Color3.fromRGB(236, 248, 255); cc.Parent = L

local rays = Instance.new("SunRaysEffect"); rays.Intensity = 0.05; rays.Spread = 0.6; rays.Parent = L

-- water look (Lake_Water = lake at y 0, Stream_Water = stream ribbon 0.02-0.4, Pool_Water = plunge pool 0.4)
for _, p in workspace.MistvaleLake:GetDescendants() do
    if p:IsA("BasePart") and (p.Name:match("^Lake_Water") or p.Name:match("^Stream_Water") or p.Name:match("^Pool_Water")) then
        p.TextureID = ""; p.Material = Enum.Material.Glass; p.Color = Color3.fromRGB(22, 172, 238)   -- water: glass, not paint
        p.Transparency = 0.22; p.Reflectance = 0.18; p.CanCollide = false; p.CanQuery = true   -- casts hit it
    elseif p:IsA("MeshPart") and p.Name == "Waterfall" then
        p.Transparency = 0.12                                       -- painted sheet; the _Glow_falls streaks are Neon
    end
    if p:IsA("PointLight") then p.Range = 9; p.Brightness = 0.8; p.Shadows = false; p.Color = Color3.fromRGB(255, 196, 110) end
end
```
The lake bed under the water is the modelled `Ground_Valley` mesh (sand, darker in the deep middle), so Glass at 0.22
shows the shallows lighter near the beach, like the preview. For swimmable water use Terrain instead: fill the lake
footprint (`Terrain:FillBlock` / `FillCylinder` around (15, -3, 35), r ~64-98, top y 0) and set
`Terrain.WaterColor = (20, 178, 236)`, `WaterTransparency = 0.55`, `WaterReflectance = 0.7`, `WaterWaveSize = 0.06`,
`WaterWaveSpeed = 6`, then hide `Lake_Water` (keep the stream ribbon).

## Glowing motes + waterfall mist (ParticleEmitters, built-in textures)
```lua
local function emitter(name, cf, size, props)
    local a = Instance.new("Part"); a.Name = name; a.Anchored = true; a.CanCollide = false; a.CanQuery = false; a.CanTouch = false
    a.Transparency = 1; a.Size = size; a.CFrame = cf; a.Parent = workspace.MistvaleLake
    local e = Instance.new("ParticleEmitter"); for k, v in props do e[k] = v end; e.Parent = a; return e
end
local NS, N = NumberSequence.new, NumberSequenceKeypoint.new
emitter("Motes", CFrame.new(0, 24, -10), Vector3.new(280, 40, 300), {          -- soft floating light motes
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = ColorSequence.new(Color3.fromRGB(205, 250, 255)),
    LightEmission = 1, LightInfluence = 0, Rate = 28, Lifetime = NumberRange.new(7, 11), Speed = NumberRange.new(.3, 1.2),
    SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, .25, 0), Rotation = NumberRange.new(0, 360),
    Size = NS({N(0, 0), N(.25, .55), N(.75, .45), N(1, 0)}), Transparency = NS({N(0, 1), N(.3, .15), N(.7, .25), N(1, 1)}),
    Shape = Enum.ParticleEmitterShape.Box})
emitter("FallsMist", CFrame.new(48, 2, -186), Vector3.new(18, 1, 8), {          -- plunge-pool spray
    Texture = "rbxasset://textures/particles/smoke_main.dds", Color = ColorSequence.new(Color3.fromRGB(235, 252, 255)),
    LightEmission = .35, LightInfluence = .6, Rate = 14, Lifetime = NumberRange.new(2.5, 4), Speed = NumberRange.new(4, 7),
    SpreadAngle = Vector2.new(35, 35), Acceleration = Vector3.new(0, -1, 3), Rotation = NumberRange.new(0, 360),
    RotSpeed = NumberRange.new(-15, 15), Size = NS({N(0, 4), N(1, 13)}), Transparency = NS({N(0, 1), N(.2, .6), N(1, 1)})})
```
Preview stand-ins (Blender only, not exported): `PreviewWater` (vertex-coloured shallows + gentle ripple bump), 80
emissive motes (`anchors.json` -> `motes`), two soft mist volumes (a misty glare patch on the lake off the dock and the
plunge-pool spray), and `post.py` (soft bloom + vibrance = Roblox Bloom + ColorCorrection). Roblox: the `FallsMist`
emitter above, and for the lake glare a second copy of it at (-2, 1, 52), Size (40, 1, 28), Rate 5, Speed 0.3-0.8,
Transparency 0.85-1, LightEmission 0.6.

Beauty camera (menu / thumbnail): `CFrame.lookAt(Vector3.new(8, 68, 152), Vector3.new(36, 10, -90))`, FieldOfView 58.

## Gameplay hooks (`workspace.MistvaleLake.Hooks`, from `anchors.json`)
| Kind | Names | Where |
|---|---|---|
| spawn | `SpawnLocation` | west beach (-60, 1.3, 66), facing the dock |
| fishing | `DockSpot1-4` | dock end platform (3, LookVector out over the lake) + one on the walkway side |
| fishzone | `LakeZone1-4` | 30 x 30 boxes on the open lake |
| station | `FishShop`, `BaitStall`, `RodShop`, `Market`, `Inn` | the blank sign board of each market stall; the Inn sign stand by the big lakeside longhouse |
| waterfall | `Waterfall` | 20 x 4 x 10 box in the plunge pool at the foot of the falls (48, 2, -186) |

Flowing stream + falls: `S.AnimateWater` scrolls a streak Texture on `Stream_Water_*` (Top) and `Waterfall` (Front /
Back); upload a tiling streak texture, set `S.WaterTexture`, and run it from a LocalScript with a copy of the setup
module in ReplicatedStorage (references/roblox_pipeline.md, "Flowing water").

Station anchors sit flush on blank sign boards: add the BillboardGui / SurfaceGui labels in Studio (nothing is written
in the meshes). Collision: rocks / trees hull, houses / dock / walls / stair / stepping stones / `Cliff_Wall` precise, sign stands /
poles / lantern posts box, lantern ropes / lilies / reeds / flowers / tufts / bushes / water / falls none. The cliff
wall closes the map on every side: ONE static closed ring solid `Cliff_Wall` (4 chunks, ~37k tris): 2 tiers at the
front, 3 on the sides, up to 6 (~150 studs) at the back, each tier a row of fused rounded rock slabs with creased seams
that never line up between tiers, ledges narrow / wide, moss on the ledges and rounded lips, a buried foot with
`RockTalus` scree, big `*VLo` boulders bedded against the faces and along the top for a rocky skyline. The waterfall
sits in a cleft: its lip rocks bed into the cliff at y ~66, its foot in `Pool_Water`. The foot is fitted round the
village (`FOOT_NEED`: every reserved spot and path keeps 9 studs + the slab bulge), so no house, stall, path or trunk
is within 8 studs of the rock (export `--cliff-buffer 8`). Add invisible walls on the cliff foot if players must not
climb the tiers.

Budget: cliff wall ~37k (static) + talus / bedded / skyline boulders and shore rocks ~45k (no bare slope anywhere: the wall has rock tops and a lumpy skyline), houses ~95k (16 houses), realistic
trees ~106k for 25 trees (table above: hero 15.9k, full oaks / firs 6.5-8.4k, background fir 3.1k, sapling 1.6k),
bushes / reeds / undergrowth ~20k (undergrowth halved to pay for the trees), ground + beach + water + paths ~16k. The map
sits at 419k of 450k. Cut first: `NTH` (cliff samples round the ring), the bedded ledge boulders (`Cliffs` group),
`PineC` copies on the cliff shelves (`CliffTrees`), the `Grass` group.
