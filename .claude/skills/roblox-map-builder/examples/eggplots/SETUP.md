# Eggstead Isle - Studio setup

Files: `roblox/` = export of `egg_map.blend` with `--materials --hero "^EggHatchery$"`. Ground = Grass, lane +
plaza pavers = Concrete, wood = WoodPlanks, trunks = Wood, boulders / shore = Slate, everything else SmoothPlastic
(the low-poly flat look). 143 kit props, 1,158 placements, 5 static chunks, **396,553 placed triangles** (budget 450k;
report.md: Budget ok, placement checks clip 0 / float 0 / water 0 / collision 0). One plot = 23.1k placed triangles.
Nothing is imported yet.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.EggsteadKit` (studs, pivot at
   origin, anchored, one Model per file). Import `roblox/AxisProbe.glb` once: its arrow must point along -Z, else set
   `M.YAW_FIX = 180` in the setup module.
2. ModuleScripts in ServerStorage: `EggsteadSetup` = `roblox/EggsteadSetup.lua`, `EggsteadHooks` =
   `roblox/EggsteadHooks.lua`. Run `roblox/EggsteadKitPrep.lua` once in the command bar.
3. Command bar:
```lua
local S = require(game.ServerStorage.EggsteadSetup)
S.Build(game.ServerStorage.EggsteadKit, workspace)
S.ApplyLook()
require(game.ServerStorage.EggsteadHooks).Build(workspace.Eggstead)
local L = game.Lighting
L.Technology = Enum.Technology.Future; L.Brightness = 3; L.ClockTime = 8.3
L.OutdoorAmbient = Color3.fromRGB(170, 195, 215); L.ColorShift_Top = Color3.fromRGB(255, 240, 215)
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = .22; atm.Haze = .4; atm.Glare = .15; atm.Color = Color3.fromRGB(215, 235, 250); atm.Decay = Color3.fromRGB(200, 230, 225)
for _, p in workspace.Eggstead:GetDescendants() do
    if p:IsA("BasePart") and p.Name:match("^Sea_Lake") then p.Transparency = .15; p.Reflectance = .05 end
end
```
Beauty camera: `CFrame.lookAt(Vector3.new(150, 95, 215), Vector3.new(0, 6, -20))`, FieldOfView 40.

## Layout (Roblox space, lane centre x = 0, island floor y = 0)
- Lane: paving x +-26 (top y 0.25), z -146..146. Belt 10 wide, top y 1.95, runs from z -151 (inside the hatch
  tunnel, north) to z 129 (south) into the drain at (0, 139.5). The chevrons point south, the direction of travel.
- Hatchery (hero): centre (0, -175.5), scale 1.35, front faces south; tunnel mouth at z ~ -141.
- Footbridges over the belt at z -64, 0, 64 (deck 6.5 high in the middle, 7 wide), in the gaps between plots.
- Plots: centres x +-62, z -96, -32, 32, 96. Plot-local frame: front (-Z) = lane side; yard 56 along the lane x 64 deep.
  West plots 1-4 (north -> south): red, yellow, sky, purple. East plots 5-8: orange, teal, blue, pink. Each plot has:
  a 16-wide gate opening on the lane side, the owner board right of the gate, 10 nests (4 + 4 + 2) either side of
  the paved aisle, the collect pad on the aisle in front of the coop door, and the coop at the back.
- Spawn plaza (0, 176) r 27; spawn (0, 178) facing north. Egg Shop (-40, 174) faces east, Sell (40, 174) faces west,
  Upgrades (0, 212) faces north (all at scale 1.3).

## Gameplay hooks (`workspace.Eggstead.Hooks`, invisible anchored Parts, CollectionService tag `Eggstead_<kind>`)
| Folder | Parts | Use |
|---|---|---|
| Spawn | `SpawnLocation` | real SpawnLocation (Neutral), faces north up the lane |
| Plot1..Plot8 | `Plot<N>` (attrs PlotId, Accent) | yard bounds box (56 x 16 x 64): claim / ownership / steal zone |
| | `Gate` | laser / force-gate span in the entrance (14 x 9.6 x 1). Both pillars carry glowing emitter lamps (`GateFrame_<acc>_Glow_g_<acc>`) |
| | `OwnerSign` | blank face of the owner board; put a SurfaceGui (Face Front) here |
| | `CollectPad` | cash pad trigger |
| | `EggSlot1..10` (attrs PlotId, SlotIndex) | egg pivot on each nest pedestal (top of the straw nest) |
| | `CoopDoor` | coop doorway |
| Conveyor | `ConveyorStart`, `ConveyorEnd`, `HatchMouth`, `Path01..Path15` (attr Order), `DrainTrigger` | spawn eggs at Start, move them along the path north -> south, delete them in the drain |
| Shops | `EggShop`, `Upgrades`, `Sell` (+ `<name>Sign` roof sign faces), `Hatchery` | ProximityPrompts / labels (GUIs only) |

No text is modelled anywhere: owner names, prices and shop names are GUIs on these anchors.

## Collision and performance
- Precise: coops, gate frames, hatchery, bridges, drain, stalls, barns, windmills. Box: yards, fences, nests, signs,
  conveyor, hay, trough, lamps, giant eggs, ranch fence. Hull: trees, bushes, boulders. None: flower patches, reeds,
  lilies, collect pads, gate mats, water (the pads are walk-over triggers).
- The conveyor is static geometry. Move eggs by script along the Path points, or put an anchored invisible Part over
  the belt with `AssemblyLinearVelocity = (0, 0, 16)`.
- Placement checks (all 0, export flags unchanged): fence runs stop 0.5 short of the next post and the run that starts
  at a corner FencePost or a gate pillar has no post of its own (`Fence8c_` / `Fence4s_` / `Fence4e_` variants); the
  ranch fence rails stop short of the next post; coops and collect pads stand ON the yard paving; the drain plinth sits
  clear of the belt end cap; hill trees are grounded on the BUILT ground mesh (`Hg`, a ray down: the coarse hill grid
  departs from `H` by several studs); the lake is a convex outline at island distance 1.5 (its edge runs under the
  bank) over a hidden flat floor `Ground_SeaFloor` 6 under the water (every water point has a bed within 8).
- If phones struggle, cut in this order: hill trees (58k), island trees (28k), flower patches (11k), lake dressing (10.5k).
