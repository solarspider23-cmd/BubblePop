# Yumori Springs - Studio setup

Files: `roblox/` (export of `onsen_map.blend` with `--materials --hero "^Pagoda(Base|Top)$" --soft
"(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant|cedar"`:
the two-part pagoda is the hero landmark, cedars are trees (foliage); paving = Limestone, ashlar / steps / lanterns =
Sandstone, rock = Rock, cedar = Wood / WoodPlanks, foliage = LeafyGrass, banks = Grass, water = Glass, roof glazes =
SmoothPlastic, bronze = Metal). Nothing is imported yet.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.YumoriSpringsKit` (studs, pivot at
   origin, one Model per file). If the importer drops the texture, upload `roblox/YumoriSprings_Palette.png` once and
   put its id in `M.PaletteTexture`.
2. ModuleScript `ServerStorage.YumoriSpringsSetup` = `roblox/YumoriSpringsSetup.lua`; run `roblox/YumoriSpringsKitPrep.lua`.
3. Import `roblox/AxisProbe.glb` once: the arrow must point along -Z, else `M.YAW_FIX = 180`.
4. Command bar:
```lua
local S = require(game.ServerStorage.YumoriSpringsSetup)
S.LightKeys.shoji = false                                -- paper windows glow, but only lanterns get PointLights
S.Build(game.ServerStorage.YumoriSpringsKit, workspace)
S.ApplyLook()
-- golden hour (values from the studied harbour place, warmer): low sun from the south-west, pink haze, violet shadows
local L = game.Lighting
L.Technology = Enum.Technology.Future; L.Brightness = 2.4
L.Ambient = Color3.fromRGB(86, 78, 112); L.OutdoorAmbient = Color3.fromRGB(150, 128, 160)
L.ColorShift_Top = Color3.fromRGB(255, 186, 128); L.ColorShift_Bottom = Color3.fromRGB(34, 38, 58)
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.24; atm.Haze = 1.1; atm.Glare = 0.3
atm.Color = Color3.fromRGB(226, 180, 166); atm.Decay = Color3.fromRGB(150, 120, 142)
for _, p in workspace:GetDescendants() do
    if p:IsA("MeshPart") and p.Name:match("^River_") then p.Transparency = 0.2; p.Reflectance = 0.05; p.CanCollide = false end
    if p:IsA("PointLight") then p.Range = 8; p.Brightness = 0.6; p.Shadows = false; p.Color = Color3.fromRGB(255, 176, 92) end
end
-- steam over the hot water: {x, y, z, radius, height} (from fx_points.json)
local STEAM = {
    {-30, 5.4, 24.5, 6, 9}, {30, 5.4, 24.5, 6, 9},          -- bath pools (under the teal pavilions)
    {-34, 2.2, 59.5, 3.6, 6}, {38, 2.2, 59.5, 3.2, 6},       -- rock pools on the islet
    {-15.7, 15.2, 2.6, 0.8, 3.2},                            -- noodle pot
}
for i, s in STEAM do
    local a = Instance.new("Part"); a.Name = "Steam" .. i; a.Anchored = true; a.CanCollide = false; a.CanQuery = false
    a.CanTouch = false; a.Transparency = 1; a.Size = Vector3.new(s[4] * 1.6, 0.2, s[4] * 1.2); a.Position = Vector3.new(s[1], s[2], s[3])
    local e = Instance.new("ParticleEmitter")
    e.Texture = "rbxasset://textures/particles/smoke_main.dds"
    e.Color = ColorSequence.new(Color3.fromRGB(255, 244, 238)); e.LightEmission = 0.15; e.LightInfluence = 0.8
    e.Transparency = NumberSequence.new({NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.75), NumberSequenceKeypoint.new(1, 1)})
    e.Size = NumberSequence.new({NumberSequenceKeypoint.new(0, s[4] * 0.35), NumberSequenceKeypoint.new(1, s[4] * 0.9)})
    e.Lifetime = NumberRange.new(2.5, 4); e.Speed = NumberRange.new(s[5] / 4, s[5] / 3); e.Rate = math.max(3, s[4] * 1.5)
    e.Rotation = NumberRange.new(0, 360); e.RotSpeed = NumberRange.new(-12, 12); e.SpreadAngle = Vector2.new(12, 12)
    e.EmissionDirection = Enum.NormalId.Top; e.Parent = a; a.Parent = workspace
end
local sp = Instance.new("SpawnLocation"); sp.Name = "IsletSpawn"; sp.Anchored = true; sp.Transparency = 1; sp.CanCollide = false
sp.Size = Vector3.new(8, 1, 6); sp.CFrame = CFrame.lookAt(Vector3.new(0, 2.1, 60), Vector3.new(0, 2.1, 0)); sp.Parent = workspace
```
Beauty camera (for a lobby / menu shot): `CFrame.lookAt(Vector3.new(0, 9, 160), Vector3.new(0, 24, -18))`,
`FieldOfView = 35` (vertical, same as the preview).

## Gameplay hooks (names in the placed map)
- Tiers: `Hardscape_T1` (Bath, y 4.5), `Hardscape_T2` (Market, y 11), `Hardscape_T3` (Upper, y 19); `Ground_Stage`
  = islet, banks, stream bed; `Cliff_Mountains` = walls (precise collision; add invisible walls at |x| > 66 and
  z < -52 if players must stay on the stage).
- Links: `FootBridge` (islet z 55 -> T1 z 35), `Stair65_8` (centre, T1 -> T2), `Stair80_6` x2 (x +-38, T2 -> T3).
- Pools: `HotPool1/2` (bath, water at y 5.1, sunken bench), `HotPool3/4` (islet), `KoiPond1` (market centre):
  good spots for sit / swim triggers. `NoodleStall` (x -17, z 3) has three stools.
- `PagodaBase` + `PagodaTop` share one origin (0, 19, -30); the top's lowest point is 14.75 above it by design (the
  validator warning is expected). The pagoda is solid: its doorway is a lit recess, not an interior.
- Collision: buildings, stairs, pools, bridge `precise`; lanterns, railings, stalls, crates `box`; trees / rocks
  `hull`; shrubs, ferns `none`.

Budget: 252 placements, 349k triangles in total (9 static chunks), largest props `PagodaBase` 12.5k / `PagodaTop`
12.3k (hero budget 30k), houses <= 11.6k (12k prop budget: coarser roof tiles, no back windows on the inns, plain
storey beams), `EXPORT_OK`, every placement check at 0 (clip, float, water, falls, collision). Railing bays carry
their left post only and every run closes with a `RailPost`, so bays never overlap; every auto-grounded prop is fitted
while placing (`fit` in onsen_map.py = the export's clip + float rules); the stream / front pool water is 4-stud cells
only where the ground dips under it, with far + side banks holding the front pool. Cut the back-slope cedars (group
`Nature`) first if phones struggle.
