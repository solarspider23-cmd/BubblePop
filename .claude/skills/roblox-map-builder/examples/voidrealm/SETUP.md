# The Shattered Void - Studio setup

Files: `roblox/` = export of `void_map.blend` with `--hero "^(OrbitSingularity|RiftGate)$"` and **no `--materials`**: every
solid MeshPart carries ONE shared painted 1024 atlas, `roblox/ShatteredVoid_Palette.png` (4 x 4 blocks made by
`void_paint.py`: glassy obsidian with violet sheen strokes + cracks + glints, grainy dusk crust, teal moss dabs, slab
paving, lilac stone, bone trim, faceted violet / cyan crystal, magenta flora, tendril grain, dark iron, distant
silhouette, black singularity). Glow keys (Neon): `void` magenta, `violet`, `cyan`, `core` white-violet, `lamp`
cyan lantern crystals, `rift` portal membrane, `flame` void fire. 54 kit props, 320 placements (851 MeshParts),
14 static chunks (7 shards + paving + 5 bridge decks + the stepping-stone tops), **174,654 placed triangles** (budget
450k; report.md: Budget ok, 0 warnings, placement checks all 0).

Placement-check pass: the walkable bridge decks (slabs + curbs, `RuneBridgeDeck*`) and stepping-stone tops
(`Ground_ShardSteps`) are static ground like the shards they join; the `RuneBridge*` / `StepStone*` props keep the keels,
rune rings, posts and lamps that hang from / stand on them. Things that float on purpose carry names that say so:
`OrbitSingularity` (hero, was `Singularity`: hero flag changed to match), `DebrisShard*` (was `FloatShard*`), `FarDebris*`
(was `FarRock*`: far silhouettes, not reachable rocks). Hanging crystals are tilted onto the keel facet with their seat
flush; low ground cover sits with only its base in the ground; the lift pad moved to (-12, 112) off the Spawn -> Shop
bridge walkway; debris keeps off the bridge lines; a final pass in `void_map.py` (`validate`) runs the exporter's clip
and float test on all dressing and drops the few pieces that would fail.
`M.LightKeys` in the setup module is already edited to `{lamp = true, flame = true}` (lanterns + braziers get a
small PointLight; re-apply after a re-export). Nothing is imported yet.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.ShatteredVoidKit` (studs, pivot at
   origin, anchored, one Model per file). Import `roblox/AxisProbe.glb` once: the arrow must point along -Z, else set
   `M.YAW_FIX = 180`.
2. ModuleScripts in ServerStorage: `ShatteredVoidSetup` = `roblox/ShatteredVoidSetup.lua`, `ShatteredVoidHooks` =
   `roblox/ShatteredVoidHooks.lua`. Run `roblox/ShatteredVoidKitPrep.lua` once in the command bar.
3. If the importer drops the embedded texture: upload `ShatteredVoid_Palette.png` once and set it as `TextureID` on
   every non-`_Glow_` MeshPart in the kit (same snippet as `examples/valleylake/SETUP.md`; never invent the id).
4. Command bar:
```lua
local S = require(game.ServerStorage.ShatteredVoidSetup)
S.Build(game.ServerStorage.ShatteredVoidKit, workspace)
require(game.ServerStorage.ShatteredVoidHooks).Build(workspace.ShatteredVoid)
```
Workspace: `FallenPartsDestroyHeight = -400` (the VoidKill hook at y -160 should catch players first; scripts own it).

## The look: endless night void, glow carries it (paste after Build; do NOT also run `S.ApplyLook()`)
Tuned against `previews/map_beauty.png` / `map_spawn.png`: near-black indigo sky, readable lilac-violet shard tops
under a cool lavender key, a cyan rim from the north-east, every Neon piece blooming.
```lua
local L = game.Lighting
L.Technology = Enum.Technology.Future            -- lantern / brazier PointLights; ShadowMap on low-end is fine
L.ClockTime = 20.6; L.GeographicLatitude = 25    -- low sun just under the horizon -> moon-blue key, dark sky
L.Brightness = 1.6; L.ExposureCompensation = 0.25
L.Ambient = Color3.fromRGB(46, 34, 86)            -- violet shadows, never black: shard tops stay readable
L.OutdoorAmbient = Color3.fromRGB(92, 78, 160)
L.ColorShift_Top = Color3.fromRGB(196, 180, 255); L.ColorShift_Bottom = Color3.fromRGB(40, 150, 190)   -- cyan bounce from below
L.EnvironmentDiffuseScale = 0.6; L.EnvironmentSpecularScale = 0.8; L.GlobalShadows = true
for _, c in L:GetChildren() do if c:IsA("PostEffect") or c:IsA("Atmosphere") or c:IsA("Sky") then c:Destroy() end end

local sky = Instance.new("Sky")                   -- default textures, dense stars, no sun / moon discs
sky.StarCount = 5000; sky.CelestialBodiesShown = false; sky.SunAngularSize = 0; sky.MoonAngularSize = 0; sky.Parent = L

local atm = Instance.new("Atmosphere")            -- thin violet depth haze: far shards + under-tier fade to indigo
atm.Density = 0.3; atm.Offset = 0.05; atm.Haze = 0.6; atm.Glare = 0
atm.Color = Color3.fromRGB(60, 36, 130); atm.Decay = Color3.fromRGB(18, 10, 48); atm.Parent = L

local bloom = Instance.new("BloomEffect")         -- the Neon accretion disc, crystals, runes, membrane glow
bloom.Intensity = 0.9; bloom.Size = 30; bloom.Threshold = 0.82; bloom.Parent = L

local cc = Instance.new("ColorCorrectionEffect")  -- cool, saturated grade
cc.Brightness = 0.0; cc.Contrast = 0.16; cc.Saturation = 0.25; cc.TintColor = Color3.fromRGB(236, 228, 255); cc.Parent = L

for _, p in workspace.ShatteredVoid:GetDescendants() do
    if p:IsA("PointLight") then p.Range = 12; p.Brightness = 0.9; p.Shadows = false
        p.Color = p.Parent.Name:find("_Glow_flame") and Color3.fromRGB(255, 90, 230) or Color3.fromRGB(130, 240, 255) end
    if p:IsA("MeshPart") and p.Name:find("_Glow_") then p.CastShadow = false end
end
-- the singularity's light on the islands (no shadows, cheap): one big magenta light in the core
local core = Instance.new("Part"); core.Name = "SingularityLight"; core.Anchored = true; core.CanCollide = false
core.CanQuery = false; core.CanTouch = false; core.Transparency = 1; core.Size = Vector3.one; core.Position = Vector3.new(0, 50, -5)
local pl = Instance.new("PointLight"); pl.Range = 60; pl.Brightness = 2; pl.Color = Color3.fromRGB(255, 80, 220); pl.Shadows = false
pl.Parent = core; core.Parent = workspace.ShatteredVoid
```
Membrane: `RiftGate_Glow_rift` reads best a little see-through: `Transparency = 0.25`. The black core is a palette
MeshPart (`OrbitSingularity`); keep it opaque so the disc reads in front of it.

## Particles (built-in textures, no ids invented)
```lua
local function emitter(name, cf, size, props, parent)
    local a = Instance.new("Part"); a.Name = name; a.Anchored = true; a.CanCollide = false; a.CanQuery = false; a.CanTouch = false
    a.Transparency = 1; a.Size = size; a.CFrame = cf; a.Parent = parent or workspace.ShatteredVoid
    local e = Instance.new("ParticleEmitter"); for k, v in props do e[k] = v end; e.Parent = a; return e
end
local NS, N, CS = NumberSequence.new, NumberSequenceKeypoint.new, ColorSequence.new
emitter("SporeMotes", CFrame.new(0, 30, -10), Vector3.new(330, 60, 340), {      -- drifting magenta / cyan spores
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(255, 120, 240), Color3.fromRGB(120, 240, 255)),
    LightEmission = 1, LightInfluence = 0, Rate = 40, Lifetime = NumberRange.new(8, 12), Speed = NumberRange.new(.3, 1),
    SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, .3, 0), Rotation = NumberRange.new(0, 360),
    Size = NS({N(0, 0), N(.3, .5), N(.8, .4), N(1, 0)}), Transparency = NS({N(0, 1), N(.3, .1), N(.7, .3), N(1, 1)}),
    Shape = Enum.ParticleEmitterShape.Box})
emitter("AccretionDust", CFrame.new(0, 50, -5) * CFrame.Angles(math.rad(-24), 0, 0), Vector3.new(1, 1, 1), {   -- infall
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(255, 200, 255)),
    LightEmission = 1, LightInfluence = 0, Rate = 60, Lifetime = NumberRange.new(2.5, 4), Speed = NumberRange.new(-26, -18),
    Shape = Enum.ParticleEmitterShape.Disc, ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
    Size = NS({N(0, .4), N(1, 1.2)}), Transparency = NS({N(0, 1), N(.2, .2), N(1, 1)})})   -- scale the Part to Vector3.new(130, 1, 130)
emitter("RiftSwirl", CFrame.new(135, 29.7, -48), Vector3.new(20, 20, 1), {     -- portal sparks (rotate with the gate's CFrame)
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(210, 90, 255)),
    LightEmission = 1, Rate = 30, Lifetime = NumberRange.new(1, 1.8), Speed = NumberRange.new(1, 3), RotSpeed = NumberRange.new(-90, 90),
    SpreadAngle = Vector2.new(20, 20), Size = NS({N(0, .6), N(1, 0)}), Transparency = NS({N(0, .2), N(1, 1)}), Shape = Enum.ParticleEmitterShape.Box})
emitter("LiftStream", CFrame.new(-19, 2, 126), Vector3.new(5, 1, 5), {           -- gravity lift up-stream
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(120, 245, 255)),
    LightEmission = 1, Rate = 25, Lifetime = NumberRange.new(2.5, 3), Speed = NumberRange.new(20, 24), SpreadAngle = Vector2.new(4, 4),
    Size = NS({N(0, .5), N(1, .2)}), Transparency = NS({N(0, .2), N(1, 1)}), Shape = Enum.ParticleEmitterShape.Box})
```
For each `VoidBrazier` add a small `fire.dds` emitter (Color magenta 255,80,230, LightEmission 1, Rate 12) if the Neon
flame alone feels static. Optional script motion (cheap, client side): spin `OrbitSingularity_Glow_*` disc parts about the
disc normal (~6 deg/s) and the Altar's floating rings; bob the drifted RiftGate stones.

Preview stand-ins (Blender only, not exported): world shader stars + nebula, 120 emissive spore motes, a thin violet
volume haze, a magenta point light in the core, `post.py` bloom. Beauty camera: `CFrame.lookAt(Vector3.new(46, 34,
214), Vector3.new(0, 34, -30))`, FieldOfView 56. Spawn view: from (0, 8.5, 152) toward (0, 36, -10).

## Gameplay hooks (`workspace.ShatteredVoid.Hooks`, tags `ShatteredVoid_<kind>`)
| Kind | Names | Where |
|---|---|---|
| spawn | `SpawnLocation` | spawn dais (0, 1.2, 140), facing north at the singularity |
| station | `ShopSign`, `QuestsSign` (blank boards in the props), `UpgradesSign`, `RiftGateSign`, `ArenaSign` (billboards) | each station |
| prompt | `ShopPrompt`, `UpgradesPrompt`, `QuestsPrompt` (attr Station) | in front of each station |
| portal | `PortalTrigger` (attr Destination) | inside the Rift Gate membrane (135, 29.7, -48) |
| lift | `LiftBottom` (TargetY 62, Speed 60), `LiftTop` (Exit) | spawn shard (-19, 126) -> Starwatch shard |
| secret | `HeartCrystal` | Starwatch shard |
| arena / arenaspawn | `ArenaBounds`, `ArenaSpawn1-4` | arena shard (0, 20, -142) |
| bridge / stepstone | `Bridge_<A>_<B>` x5, `Step01-08` (attr Order) | ring road |
| viewpoint / hazard / killzone | `Overlook`, `SingularityCore`, `VoidKill` | promontory tip / core / y -160 |

Lift note: the beam top (y ~59) stands 3-4 studs off the Starwatch edge; give the lift script a small push toward
`LiftTop` at TargetY (or a short jump).

## Collision
Shards (`Ground_Shard*`), bridges, stepping stones, lift pads, stations, the arena rim and the Rift Gate are Precise;
lanterns / rails / braziers Box; crystals, pillars, rubble, rim chunks Hull; everything decorative or out of reach
(singularity, floating debris, far rocks, hanging crystals, rune circles, tendrils, grass, chips, lift beam) none.
