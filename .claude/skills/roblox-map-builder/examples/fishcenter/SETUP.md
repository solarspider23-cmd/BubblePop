# Tidehook Lagoon - Studio setup

Files: `roblox/` = export of `fish_map.blend` with `--materials --hero "^(AquaDome|Lighthouse)$" --soft
"(?i)tree|pine|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant(?!er)"`
(the default foliage list, except that a palm PLANTER is a tub, not foliage) (deck = WoodPlanks,
teak / bamboo = Wood, thatch = Fabric, sand = Sand, coral stone = Limestone, volcanic rock = Basalt, palms = LeafyGrass,
water + dome glass = Glass, paint / accents = SmoothPlastic, brass = Metal). 70 kit props, 567 placements,
19 static chunks; 423k placed triangles (budget 450k), `EXPORT_OK`, every placement check at 0 (clip, float, water,
falls, collision). Rails: runs are collected and laid by `rails_flush` so each corner has ONE post (a run whose start is
taken is laid backwards, a taken end post is skipped). Torches standing just off the deck edge are `TikiTorchStilt`
(pole down into the seabed). The seabed never drops below y -7.5 (a bed within 8 under the whole sea; its colour still
follows the old depth profile) and rises to +1 at the world edge so the sea plane's border meets a bank. Auto-grounded
props are fitted while placing (`fit` in fish_map.py = the export's clip + float rules). Nothing is imported yet.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.TidehookLagoonKit` (studs, pivot at
   origin, anchored, one Model per file). Import `roblox/AxisProbe.glb` once: the arrow must point along -Z, else set
   `M.YAW_FIX = 180` in the setup module.
2. ModuleScripts in ServerStorage: `TidehookLagoonSetup` = `roblox/TidehookLagoonSetup.lua`,
   `TidehookLagoonHooks` = `roblox/TidehookLagoonHooks.lua`. Run `roblox/TidehookLagoonKitPrep.lua` once in the command bar.
3. Command bar:
```lua
local S = require(game.ServerStorage.TidehookLagoonSetup)
S.Build(game.ServerStorage.TidehookLagoonKit, workspace)
S.ApplyLook()
require(game.ServerStorage.TidehookLagoonHooks).Build(workspace.TidehookLagoon)
-- bright tropical late morning: sun from the east-south-east ~40 deg, cyan horizon, thin aqua air
local L = game.Lighting
L.Technology = Enum.Technology.Future; L.Brightness = 3; L.ClockTime = 8.7
L.Ambient = Color3.fromRGB(110, 140, 170); L.OutdoorAmbient = Color3.fromRGB(150, 185, 210)
L.ColorShift_Top = Color3.fromRGB(255, 240, 215); L.ColorShift_Bottom = Color3.fromRGB(40, 70, 90)
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.22; atm.Haze = 0.6; atm.Glare = 0.2; atm.Color = Color3.fromRGB(190, 230, 255); atm.Decay = Color3.fromRGB(120, 175, 220)
for _, p in workspace.TidehookLagoon:GetDescendants() do
    if p:IsA("BasePart") and p.Material == Enum.Material.Glass then
        if p.Name:match("^Sea_Water") then p.Transparency = 0.35; p.CanCollide = false; p.CanQuery = false
        else p.Transparency = 0.55 end                                  -- aquarium dome + lantern room glass
        p.Reflectance = 0.08
    end
    if p:IsA("PointLight") then p.Range = 9; p.Brightness = 0.7; p.Shadows = false end
end
```
Beauty camera (menu / thumbnail): `CFrame.lookAt(Vector3.new(-46, 24, 205), Vector3.new(0, 16, 0))`, FieldOfView 38.

## Water and FX hints
- The sea is 4 flat Glass Parts (`Sea_Water_*`, y = 0) over a modelled seabed (`Ground_Seabed_*`: white sand under
  the stations, turquoise shoals at the reef, deep blue beyond). Keep the Parts if the game only casts into water (cheap,
  matches the previews). For swimming / boats with real buoyancy, fill Roblox Terrain water instead: `Terrain:FillBlock`
  y -40..0 over x/z -700..700, then delete the Sea_Water parts; set `Terrain.WaterColor` (40, 180, 200),
  WaterTransparency 0.6, WaterWaveSize 0.15, WaterReflectance 0.3. Pilings and the seabed already reach below y 0.
- Lighthouse beacon: the `Lighthouse_Glow_beacon` part is Neon; add a rotating SpotLight (Range 60, Angle 25,
  Brightness 4, warm white) on a part at (0, 60, 0) turned by a server script for the sweep, plus a PointLight
  (Range 20). `beacon` is not in `M.LightKeys`, so it gets no automatic PointLight.
- Torches (`TikiTorch_Glow_fire`) and lamps get small PointLights from `Build()`. Add a fire ParticleEmitter
  (rbxasset://textures/particles/fire_main.dds, Size 0.6-0.2, Lifetime 0.4-0.7, Rate 12, orange -> red) at each torch
  top (torch pivot + 7 studs) if the budget allows; skip on phones.
- Splash / bubble FX at the fishing spots: a ParticleEmitter on each `Hooks.fishzone` part (tiny white rings rising,
  Rate 2) reads as "fish here".

## Gameplay hooks (`workspace.TidehookLagoon.Hooks`, invisible anchored Parts, attribute `HookKind`)
| Folder | Parts | Use |
|---|---|---|
| spawn | `SpawnLocation` (0, 5, 87.5), faces the dome | real SpawnLocation (Neutral) on the spawn plaza compass rose |
| station | `RodShop`, `BaitShop`, `FishMarket`, `BoatDock`, `QuestBoard`, `Aquarium`, `FishIndex` | spots for name BillboardGuis (a default label is made; restyle it); place ProximityPrompts on the station props |
| sell | `SellCounter` (19 x 4 x 3) | along the market's ice counter: sell trigger |
| fishing | `PierNE_Spot1..3`, `PierN_Spot1..4`, `PierNW_Spot1..3` | stand spots at the railing gaps on the pier ends; LookVector = cast direction (out to sea) |
| fishzone | `PierNE_Deep1/2`, `PierN_Deep1/2`, `PierNW_Deep1/2`, `Lagoon_0/90/180` | 24 x 24 deep-water zones by the marker buoys (higher tier fish), 14 x 14 lagoon beginner zones |
| boat | `BoatSpawn1/2` | boat spawns at the dock slips (waterline, bow = LookVector); the placed `Skiff` / `FishingBoat` show where |

Station props (placed Models inside `workspace.TidehookLagoon.<Group>`): `RodShop` (SW, rod racks beside it),
`BaitShop` (SE), `FishMarket` (E, open counter), `BoatHouse` + `Skiff` + `FishingBoat` (W), `QuestBoard` (spawn plaza,
west side), `AquaDome` + `Lighthouse` + `FishIndexWall` (centre; the dome door faces the spawn). Walkable statics:
`Hardscape_Ring` (ring boardwalk, deck y 4.5), `Hardscape_Centre` (stone platform + 4 spokes), `Hardscape_<Pad>` and
`Hardscape_Pier*` (precise collision).

## Collision and performance
- Buildings, boats, arch, dome: precise. Rails, torches, boards, benches, crates: box. Palms, rocks, sea stacks: hull.
  Corals, shrubs, nets, buoys, clouds, water: none. `Ground_Seabed` is precise; set CanCollide false on it if players
  never reach the seabed (saves physics).
- Rails are box collision, so they work as invisible walls along every deck edge; the railing gaps on the pier ends
  are open on purpose (cast spots). Add an invisible wall or a water kill/swim zone if falling in should be handled.
- Budget: 437k placed triangles, AquaDome 13.5k (hero), largest non-hero prop FishMarket 11.3k. Cut first if phones
  struggle: group `Coral` (underwater corals), clouds (use a Roblox Sky), torch count, islet palms.
