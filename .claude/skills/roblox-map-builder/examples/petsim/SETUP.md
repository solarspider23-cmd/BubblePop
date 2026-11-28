# Puffpaw Isles - Studio setup

Files: `roblox/` = export of `pet_map.blend` (palette texture, no `--materials`: the soft painted gradients ride on the
shared 512 px palette, so every surface stays SmoothPlastic-clean and toy-like). 83 kit props, 568 placements
(658 MeshParts), 11 static chunks + 4 sea tiles, **419,987 placed triangles** (budget 450k; report.md: Budget ok,
placement checks all 0). Nothing is imported yet.

Placement-check pass (export flags unchanged): fence posts a full segment apart and rails that stop short of the next
post; fence gaps at every bridge head (not at the gate 16 studs inland); bridges stand on two pairs of piers in the
lagoon; the sea is named as water (`Sea_LagoonWater`, `Sea_ShallowsWater`) over a lagoon floor `Ground_SeaBed` 6 under
it whose outer ring rises to the waterline at the sea's edge; trees in the `leaf` colour are `PuffTree_green*` (a tree,
trunk hull); `PuffBush_*` have no collision (foliage); `SeaRock*` are hull.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.PuffpawKit` (studs, pivot at origin,
   anchored, one Model per file). Import `roblox/AxisProbe.glb` once: its arrow must point along -Z, else set
   `M.YAW_FIX = 180` in the setup module.
2. ModuleScripts in ServerStorage: `PuffpawSetup` = `roblox/PuffpawSetup.lua`, `PuffpawHooks` = `roblox/PuffpawHooks.lua`
   (same as `Hooks.lua`). Run `roblox/PuffpawKitPrep.lua` once in the command bar.
3. Command bar:
```lua
local S = require(game.ServerStorage.PuffpawSetup)
S.Build(game.ServerStorage.PuffpawKit, workspace)
S.ApplyLook()
require(game.ServerStorage.PuffpawHooks).Build(workspace.Puffpaw)
local L = game.Lighting
L.Technology = Enum.Technology.Future
L.ClockTime = 13.2; L.GeographicLatitude = 30          -- high bright sun from the south-south-east
L.Brightness = 3; L.ExposureCompensation = 0.1
L.Ambient = Color3.fromRGB(120, 130, 160); L.OutdoorAmbient = Color3.fromRGB(175, 195, 230)
L.ColorShift_Top = Color3.fromRGB(255, 245, 230); L.ColorShift_Bottom = Color3.fromRGB(150, 170, 220)
L.EnvironmentDiffuseScale = 0.6; L.EnvironmentSpecularScale = 0.4
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.18; atm.Offset = 0.1; atm.Haze = 0.3; atm.Glare = 0.1
atm.Color = Color3.fromRGB(215, 235, 255); atm.Decay = Color3.fromRGB(150, 205, 255)
local bloom = L:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect", L)
bloom.Intensity = 0.35; bloom.Size = 18; bloom.Threshold = 1.05
local cc = L:FindFirstChildOfClass("ColorCorrectionEffect") or Instance.new("ColorCorrectionEffect", L)
cc.Saturation = 0.18; cc.Contrast = 0.08; cc.TintColor = Color3.fromRGB(255, 252, 246)
for _, p in workspace.Puffpaw:GetDescendants() do
	if p:IsA("BasePart") and p.Name:match("^Sea_") then p.Transparency = 0.12; p.Reflectance = 0.05 end
end
```
Use a bright default Sky (or a plain blue skybox); the clouds on the lagoon are meshes (`Cloud1..4`, no collision).
Beauty camera: `CFrame.lookAt(Vector3.new(34, 17, 78), Vector3.new(-12, 15, -6))`, FieldOfView 50.
Overview: `CFrame.lookAt(Vector3.new(-230, 360, 290), Vector3.new(110, 0, -70))`, FieldOfView 40.

## Layout (Roblox space, sea surface y -6)
| Island | Centre | Radius | Top y | Contents |
|---|---|---|---|---|
| Hub (Zone 0) | (0, 0) | ~92 | 5 (dome +0.6) | fountain + statue, plaza r 32, spawn (0, 70), hatchery W, shop E, upgrade NE, trading SW, leaderboard SE |
| Meadow (Zone 1) | (8, -238) | ~86 | 7 | puff trees, daisies, mushrooms, picnic, 42 breakables, Meadow egg |
| Candy (Zone 2) | (210, -172) | ~82 | 12 | cotton-candy trees, lollipops, canes, gumdrops, donut, 42 breakables, Candy egg |
| Crystal (Zone 3) | (222, 72) | ~82 | 18 | crystal trees, crystal spires, star lamps, glow shrooms, 42 breakables, Crystal egg |

- Bridges: hub N edge -> Meadow (Bridge_1), Meadow NE -> Candy (Bridge_2), Candy S -> Crystal (Bridge_3); 13 wide,
  humped, rising to the next island. A toll arch (`ZoneGate_meadow / candy / crystal`) stands 19 studs inside the near
  island's rim at every bridge head, front facing back into that island; the toll podium is on the left of the opening.
- Hub and Crystal are close (~54 studs of water) but NOT connected: Crystal is only reached through Candy.
- Rims: chunky fences all round (gaps only at bridge heads) = the fall guard. Add an invisible kill/return plane at
  y -12 if you want players who jump the fence sent back.
- The fountain hero is two MeshParts at one origin: `PetFountain` (basins, veils) + `PetStatue` (cushion + mascot; the
  report's "lowest point above its origin" note on PetStatue is intended - it sits on the fountain).

## Gameplay hooks (`workspace.Puffpaw.Hooks`, invisible anchored Parts, CollectionService tag `Puffpaw_<kind>`)
| Folder | Parts | Use |
|---|---|---|
| Spawn | `SpawnLocation` | real SpawnLocation (Neutral) on the spawn pad, faces north to the fountain |
| Stations | `Fountain`, `Hatchery`, `PetShop`, `UpgradeMachine`, `TradePad`, `TradeBooth1/2` (attr Station), `LeaderboardFace` | ProximityPrompts / billboards; LeaderboardFace = blank board face for a SurfaceGui (18 x 11) |
| EggStands | `EggStand1..6` (attrs Zone 0-3, Egg, Index) + `EggStand<N>_Prompt` | egg pivot on top of each pedestal; 1-3 hub (basic, spotted, golden), 4 meadow, 5 candy, 6 crystal |
| Gates | `Gate1..3` (attrs ZoneIndex, Bridge), `Gate<N>_Toll` | barrier span inside each arch (18 x 13 x 2; +Z side leads to the bridge), toll podium prompt |
| Breakables_Z1..3 | `Breakable_Z<z>_<nn>` (attrs Zone, Tier 1-3, Kind) | 42 per zone, 126 total; tier rises with distance from the zone entry |
| Zones | `Zone0..3` (attrs Zone, Name) | island bounds boxes (zone membership, music, pet roam area) |

No text is modelled anywhere: shop names, prices, gate costs and leaderboard rows are GUIs on these anchors.

## Collision and performance
- Precise: islands (`Ground_*`), plaza paving, bridges, gates, fountain + statue, shop, upgrade machine, rainbow arch,
  egg stands, spawn pad, leaderboard, trade booths. Box: fences, lamps, benches, chests, gifts, lollipops, canes,
  picnic set. Hull: trees, bushes, rocks, mushrooms, crystals, coin piles. None: paths, sea, clouds, flowers, tufts,
  trade pad (walk-over).
- Triangles by group: zones ~48-58k each + ~9-10k breakables each, fences 38k, hub dressing 32k, hero 23k (+ statue in
  the same group), hatchery 18k, stations 18k, bridges 22k, gates 17k, frame clouds 18k, static ground 33k.
- Breakables are 192-280 tris each; every kit mesh is shared, so the 126 breakables cost the memory of 7 meshes.
- Heaviest single meshes: PetFountain 16.1k + PetStatue 6.8k (heroes), Bridge_3 9.1k, UpgradeMachine 8.5k, RainbowArch 8.3k.
