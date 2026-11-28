# Glowroot Caverns - Studio setup

Files: `roblox/` = export of `cave_map.blend` (`--name GlowrootCaverns --hero "^Glowroot$"`, soft regex extended with
`shroom|fung|spore`, rock regex extended with `stalac` (stalactites are rock, bedded in the ceiling by design),
**no `--materials`**: every solid MeshPart carries ONE painted 1024 atlas `GlowrootCaverns_Palette.png`
made by `cave_paint.py`), then `py post_export.py` (this map's collision rules + no auto PointLights) and `py hooks_lua.py`.
63 kit props, 422 placements, 10 static chunks, **428,282 placed triangles** (budget 450k; report.md: Budget ok, placement
checks all 0, 1 warning = 3 zero-area faces on LogSeat, harmless). Nothing is imported yet.

Placement-check pass: the two mine tracks are static (`Track_Rails1/2`, cut to length along their lines and draped on
the floor; the 8-stud kit segments overlapped at every leg); the lake water only covers floor (no edge over a hole by
the falls) and the floor keeps a lip 0.15 over the waterline 6-10 studs round the lake; the lake bed glow stones are
`BedGlow1` (a `Lake*` name made them water); the camp fire ring sits on the floor; a final pass in `cave_map.py`
(`validate`) runs the exporter's clip and float test on the dressing and drops the few pieces that would fail (geodes,
sprays, ore piles and carts carry anchors: the piece they clip into goes instead). Collision rules for this map are in
the exporter's COLLISION list too (`GlowVine*`, `CaveFalls`, `BedGlow*` none, `MineShop` precise).

## Build order
1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.GlowrootCavernsKit` (studs, pivot at
   scene origin, anchored, one Model per file) + `roblox/AxisProbe.glb` once (arrow along -Z, else `M.YAW_FIX = 180`).
2. ModuleScripts in ServerStorage: `GlowrootCavernsSetup` = `roblox/GlowrootCavernsSetup.lua`, `GlowrootCavernsHooks` =
   `roblox/GlowrootCavernsHooks.lua`. Run `roblox/GlowrootCavernsKitPrep.lua` once in the command bar.
3. If the importer drops the embedded texture: upload `GlowrootCaverns_Palette.png` once, set it as `TextureID` on every
   non-`_Glow_` MeshPart in the kit (never invent the id).
4. Command bar:
```lua
local S = require(game.ServerStorage.GlowrootCavernsSetup)
S.Build(game.ServerStorage.GlowrootCavernsKit, workspace)
require(game.ServerStorage.GlowrootCavernsHooks).Build(workspace.GlowrootCaverns)
```
Then paste the look below (do NOT also run `S.ApplyLook()`: the export guessed a daylight look).

## Palette
`previews/palette.png` (from `cave_palette.py` via `palette_sheet.py`): base ramps with a value structure (rock = teal-slate
shadow -> mauve -> warm lit face, sage moss, mid-tone floor), ONE dominant glow family (teal-cyan: lake, crystals, fungi,
vines, glow-worms), ONE warm accent (amber: Heart, lanterns, sunbeam), grotto accents (Forge fire, Camp firelight,
Elevator cool white, Brewery magenta = the only violet). Neon colours in `M.Glow` match it.

## Shell, collision, hanging props
- `Terrain_Walls_*` = cave walls + tunnel ceilings below y 30 (PreciseConvexDecomposition, normals face into the cave).
  `Horizon_Vault_*` = the vault above y 30 (no collision, out of reach). `Horizon_Crust_0` = coarse outer rock skin that
  closes the volume so the sun only enters through the shaft (no collision). `Ground_CaveFloor_0` = walkable floor
  (precise). If a Terrain_Walls chunk ever fills the tunnel with collision in Studio, set its `CollisionFidelity` to
  `PreciseConvexDecomposition` again via KitPrep, or add invisible box walls along the tunnel sides.
- The only opening to the sky is the slanted sun shaft over the lake (top at y ~170, lip ring `SkylightLip`).
- **Hanging on purpose (origin at the TOP):** `GlowVine1-3` (names contain "vine": the exporter's float test exempts them;
  they still pass the inside-rock test, hung 0.45 under the LOWEST ceiling point over their root knot),
  `Stalactite1-3`, `StalactiteCurtain1-2`, `CaveFalls` lip and the top of `Glowroot` are not foliage and are not checked.
  Every glowing fungus (`GlowShroom*`, `ShroomPatch*`) passes the inside + float test per MeshPart: each glow key has
  spore nodules at the foot (0.3 up, above the placement sink) so the glow parts are grounded too. `GlowWorms*` (vault
  specks) and `GlowPuddle*` (floor puddles, set Material Glass / Reflectance 0.3 for reflections) have no collision.
- Collision (set by `post_export.py`): precise = shell, floor, stations, MineFrame, Scaffold, bridges, SpawnDais,
  Glowroot; box = carts, lanterns, crates, barrels, buffers, quest board, campfire, seats; none = vines, dripstone,
  rails (`Track_*`), small fungi, crystal shards, bed glow, falls, lip; hull = rocks, stalagmites, geodes, sprays, ore, giant fungi.

## The look: dark cave, colour from glow, one warm sunbeam
```lua
local L = game.Lighting
L.Technology = Enum.Technology.Future           -- needed for the PointLights + sun shadows through the shaft
L.GlobalShadows = true; L.Brightness = 3.2; L.ExposureCompensation = 0.25
L.Ambient = Color3.fromRGB(16, 20, 34)           -- palette 'ambient' #101422 lifted: walls read, never crushed to black
L.OutdoorAmbient = Color3.fromRGB(10, 11, 18)
L.EnvironmentDiffuseScale = 0.15; L.EnvironmentSpecularScale = 0.3
L.ColorShift_Top = Color3.fromRGB(255, 214, 160); L.ColorShift_Bottom = Color3.fromRGB(20, 60, 70)
for _, c in L:GetChildren() do if c:IsA("PostEffect") or c:IsA("Atmosphere") or c:IsA("Sky") then c:Destroy() end end
-- aim the sun down the shaft: toward-sun direction (0.195, 0.927, 0.320) (elev 68 deg, from the south-east)
local want = Vector3.new(0.195, 0.927, 0.320).Unit; local best, bt, bl = -2, 12, 0
for lat = -60, 60, 1 do L.GeographicLatitude = lat
    for t = 6, 18, 0.05 do L.ClockTime = t; local d = L:GetSunDirection():Dot(want); if d > best then best, bt, bl = d, t, lat end end end
L.GeographicLatitude = bl; L.ClockTime = bt; print("sun match", best, bt, bl)   -- expect > 0.999

local atm = Instance.new("Atmosphere")            -- dusty cave haze (thin: tunnels must stay readable)
atm.Density = 0.36; atm.Offset = 0; atm.Haze = 1.8; atm.Glare = 0
atm.Color = Color3.fromRGB(118, 108, 94); atm.Decay = Color3.fromRGB(34, 40, 58); atm.Parent = L
local bloom = Instance.new("BloomEffect"); bloom.Intensity = 1.1; bloom.Size = 28; bloom.Threshold = 0.9; bloom.Parent = L
local rays = Instance.new("SunRaysEffect"); rays.Intensity = 0.12; rays.Spread = 0.6; rays.Parent = L   -- when you look up the shaft
local cc = Instance.new("ColorCorrectionEffect"); cc.Contrast = 0.12; cc.Saturation = 0.2; cc.TintColor = Color3.fromRGB(240, 236, 255); cc.Parent = L

local root = workspace.GlowrootCaverns
for _, p in root:GetDescendants() do
    if p:IsA("MeshPart") and p.Name:find("_Glow_") then p.CastShadow = false end
    if p:IsA("BasePart") and p.Name:find("^Lake_Water") then p.Material = Enum.Material.Glass; p.Transparency = 0.45; p.Color = Color3.fromRGB(20, 180, 190); p.Reflectance = 0.1 end
    if p:IsA("BasePart") and p.Name == "CaveFalls" then p.Transparency = 0.3 end
    if p:IsA("BasePart") and p.Name:find("^GlowPuddle%d$") then p.Material = Enum.Material.Glass; p.Reflectance = 0.3; p.Transparency = 0.2 end
    if p:IsA("BasePart") and p.Name == "CaveFalls_Glow_falls" then p.Transparency = 0.45 end
end
```
The lake bed under the see-through water carries Neon `BedGlow` stones + 4 underwater lights: the water glows from below.

## Sunbeam (hero light)
```lua
local H = workspace.GlowrootCaverns.Hooks.Hero
local a0 = Instance.new("Attachment", H.SunShaftTop); local a1 = Instance.new("Attachment", H.SunShaftBottom)
for _, spec in { {26, 36, 0.62}, {10, 16, 0.42} } do                       -- wide soft shaft + bright core
    local b = Instance.new("Beam"); b.Attachment0 = a0; b.Attachment1 = a1; b.Width0 = spec[1]; b.Width1 = spec[2]
    b.FaceCamera = true; b.LightEmission = 1; b.LightInfluence = 0; b.Segments = 1; b.Color = ColorSequence.new(Color3.fromRGB(255, 214, 150))
    b.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, spec[3]),
        NumberSequenceKeypoint.new(0.85, spec[3] + 0.12), NumberSequenceKeypoint.new(1, 1)}); b.Parent = H.SunShaftTop
end
local sp = Instance.new("SpotLight"); sp.Face = Enum.NormalId.Bottom; sp.Angle = 28; sp.Range = 60; sp.Brightness = 4
sp.Color = Color3.fromRGB(255, 214, 160); sp.Shadows = true
local holder = Instance.new("Part"); holder.Anchored = true; holder.CanCollide = false; holder.CanQuery = false; holder.Transparency = 1
holder.Size = Vector3.one; holder.CFrame = CFrame.lookAt(H.SunShaftBottom.Position + (H.SunShaftTop.Position - H.SunShaftBottom.Position).Unit * 55, H.SunShaftBottom.Position) * CFrame.Angles(math.rad(-90), 0, 0)
sp.Parent = holder; holder.Name = "SunSpot"; holder.Parent = H
```
The real sun also enters through the shaft (Future + GlobalShadows): the spot on the Glowroot heart is lit twice.

## Point lights (keep the count reasonable)
`GlowrootCavernsHooks` creates **30 PointLights** (Shadows off) from `anchors.json`, only where they carry the read:
the Glowroot heart (amber) + upper braid (soft teal), 3 underwater lake lights, the falls, the spawn ring, 7 big cyan /
amber / magenta geodes, 4 giant mushrooms (teal, magenta in the Brewery), ~6 path / cluster lanterns, the scaffold, and
one accent light per station (Shop lamp, Forge fire, Camp fire, Lift cool white + shaft glow, Brewery magenta). Every
other lantern, frame lamp and crystal is Neon only. No parts get automatic lights (`M.LightKeys = {}`).

## Particles (built-in textures, no ids invented)
```lua
local function emitter(name, cf, size, props, parent)
    local a = Instance.new("Part"); a.Name = name; a.Anchored = true; a.CanCollide = false; a.CanQuery = false; a.CanTouch = false
    a.Transparency = 1; a.Size = size; a.CFrame = cf; a.Parent = parent or workspace.GlowrootCaverns
    local e = Instance.new("ParticleEmitter"); for k, v in props do e[k] = v end; e.Parent = a; return e
end
local NS, NK, CS = NumberSequence.new, NumberSequenceKeypoint.new, ColorSequence.new
local H = workspace.GlowrootCaverns.Hooks.Hero
local top, bot = H.SunShaftTop.Position, H.SunShaftBottom.Position
emitter("BeamDust", CFrame.lookAt((top + bot) / 2, bot) * CFrame.Angles(math.rad(90), 0, 0), Vector3.new(18, (top - bot).Magnitude * 0.8, 18), {
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(255, 226, 170)), LightEmission = 0.7,
    LightInfluence = 0, Rate = 28, Lifetime = NumberRange.new(6, 10), Speed = NumberRange.new(0.1, 0.4), SpreadAngle = Vector2.new(180, 180),
    Size = NS({NK(0, 0), NK(0.2, 0.22), NK(0.8, 0.18), NK(1, 0)}), Transparency = NS(0.3), Acceleration = Vector3.new(0, -0.05, 0)})
emitter("Spores", CFrame.new(0, 22, -20), Vector3.new(200, 40, 170), {                   -- drifting bioluminescent spores
    Texture = "rbxasset://textures/particles/sparkles_main.dds", Color = CS(Color3.fromRGB(120, 255, 200), Color3.fromRGB(190, 255, 110)),
    LightEmission = 1, LightInfluence = 0, Rate = 35, Lifetime = NumberRange.new(8, 12), Speed = NumberRange.new(0.2, 0.8),
    SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.15, 0), Size = NS({NK(0, 0), NK(0.3, 0.16), NK(1, 0)})})
emitter("FallsMist", CFrame.new(H.Waterfall.Position), Vector3.new(14, 2, 8), {                 -- spray at the plunge
    Texture = "rbxasset://textures/particles/smoke_main.dds", Color = CS(Color3.fromRGB(200, 250, 255)), LightEmission = 0.3,
    Rate = 14, Lifetime = NumberRange.new(2, 3.5), Speed = NumberRange.new(2, 5), SpreadAngle = Vector2.new(60, 60),
    Size = NS({NK(0, 3), NK(1, 9)}), Transparency = NS({NK(0, 0.7), NK(1, 1)})}, H)
for _, m in workspace.GlowrootCaverns:GetDescendants() do                                  -- drips off the stalactite tips
    if m:IsA("MeshPart") and m.Name == "Stalactite1_Glow_cyan" and math.random() < 0.6 then
        local e = Instance.new("ParticleEmitter"); e.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        e.Color = CS(Color3.fromRGB(150, 240, 255)); e.LightEmission = 1; e.Rate = 0.35; e.Lifetime = NumberRange.new(1.4)
        e.Speed = NumberRange.new(0); e.Acceleration = Vector3.new(0, -70, 0); e.Size = NS(0.12); e.Parent = m
    end
end
```

## Gameplay hooks (see the header of GlowrootCavernsHooks.lua)
spawn (dais, faces north) | 5 stations with label + prompt (MineShop, CrystalForge, QuestCamp, DeepLift, BrewStation) |
mine-cart path points `Rail1_01..06` (depot -> Ore Exchange) and `Rail2_01..06` (branch -> Crystal Forge) + 4 cart spawns |
29 breakables (geodes, sprays, ore piles) with `Kind` amber/cyan/violet and `Tier` 1 (hall) .. 4 (lift grotto) |
`DeepDiveTrigger` (cage interior, attr `Destination`) | `ChasmKill`, `LiftShaftKill` | `SunShaftTop/Bottom` | Waterfall |
LakeWater | GlowrootHeart (secret) | ChasmBridge.

## Previews
`previews/map_beauty.png` (bloomed with `post.py`; raw = `map_beauty_raw.png`), `palette.png`, `before_after.png`, `stations.png`, `map_overview.png` (vault, crust,
hanging props and the sky lip hidden; walls cut at y 12 by a preview-only copy), district shots `map_spawn / falls /
shop / forge / camp / lift / brew / hall_e.png`, `map_stats.json`. Rebuild: `blender -b --factory-startup --python
cave_map.py [-- norender] [-- name.png ...]`; props QA: `./studio.sh qa/<dir> "geode('cyan',1)" ...`.
