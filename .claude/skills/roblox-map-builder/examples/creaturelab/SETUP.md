# Bloomcrest Care Centre - Studio setup

Files: `roblox/` = export of `lab_map.blend` with `--materials --hero "^(Rotunda|EvoChamber)$"` (walls / counters /
plastic = SmoothPlastic, hall + wing floor tiles = Marble, steel = Metal, birch = WoodPlanks, trunks = Wood, foliage =
LeafyGrass, lawn = Grass, paving = Concrete, glass = Glass). 84 kit props, 239 placements, 8 static
chunks; 445,998 placed triangles (budget 450k, report.md: Budget ok, placement checks all 0). Nothing is imported yet.

Placement-check pass (export flags unchanged): the forecourt now has its floor (the polar tiles ran r 45.6 -> 34 and
made nothing; a sky-coloured hole sat under the fountains, lamps and vending machines); the rotunda roof is part of the
`Rotunda` prop (a roof rests on its walls; as its own prop it could only "float") and its ceiling skin faces down into
the hall (it faced up: invisible from inside in Roblox); ceiling ring tubes and pendant lamps hang just under the roof
skin; the arch opening fits the `LabArchway` pilasters; forecourt hedges 14 deg apart on the paving band; a hidden pond
bed under the dish. Renamed for the right classification: `WallClock` -> `HangingClock`, `ArtFrame*` -> `HangingArt*`
(wall-hung), `WaterCooler` -> `DrinkCooler` (not water), `BlossomPark4` -> `PinkParkTree4` (a tree, trunk hull).

Polish pass (2026-11-18): interior trim (`HallTrim` / `WingTrim`: pilasters every 18 deg, wainscot panels, teal chair
rail, light-cove glow ring), a coffered `HallCeiling` (16 ribs, ring beams, mint coffers) under the dome with the pendant
lamps hanging from its middle ring beam, wall decor (blank-face clocks, abstract art frames, wall capsule cases), smooth
plant language (fig trees, monstera, snake plants, hanging planters, rounded park + blossom trees, topiary hedges,
round bushes), station story clusters (heal corner with blanket bed + plush, supply cartons + sale stand, dock pylons +
server cabinet, rope line + trophy shelf), entry mat, rugs, water cooler, plush toys, and a designed garden (curving
loop path + pond link + spawn link, pond with stones / lilies / reeds, tree groups, flower beds, low boundary wall,
distant hills). Fixed: the rotunda roof lathes had closed end caps that sealed the dome and oculus with flat discs.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.BloomcrestKit` (studs, pivot at
   origin, anchored, one Model per file). Import `roblox/AxisProbe.glb` once: the arrow must point along -Z, else set
   `M.YAW_FIX = 180` in the setup module.
2. ModuleScripts in ServerStorage: `BloomcrestSetup` = `roblox/BloomcrestSetup.lua`, `BloomcrestHooks` =
   `roblox/BloomcrestHooks.lua`. Run `roblox/BloomcrestKitPrep.lua` once in the command bar.
3. Command bar:
```lua
local S = require(game.ServerStorage.BloomcrestSetup)
S.Build(game.ServerStorage.BloomcrestKit, workspace)
S.ApplyLook()
require(game.ServerStorage.BloomcrestHooks).Build(workspace.Bloomcrest)
-- bright clean late morning outside, evenly lit inside
local L = game.Lighting
L.Technology = Enum.Technology.Future; L.Brightness = 3; L.ClockTime = 9.2
L.Ambient = Color3.fromRGB(150, 160, 170); L.OutdoorAmbient = Color3.fromRGB(170, 190, 210)
L.EnvironmentDiffuseScale = .6; L.EnvironmentSpecularScale = .3
L.ColorShift_Top = Color3.fromRGB(255, 245, 229)
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = .2; atm.Haze = .3; atm.Glare = .1; atm.Color = Color3.fromRGB(220, 243, 255); atm.Decay = Color3.fromRGB(150, 190, 230)
for _, p in workspace.Bloomcrest:GetDescendants() do
    if p:IsA("BasePart") then
        if p.Material == Enum.Material.Glass then p.Transparency = .6; p.Reflectance = .05 end
        if p.Name:match("_Glow_liquid") then p.Transparency = .4 end          -- see the eggs inside the specimen tanks
        if p.Name:match("_Glow_evo") or p.Name:match("_Glow_heal") then        -- soft light on the hero machines
            if not p:FindFirstChildOfClass("PointLight") then
                local l = Instance.new("PointLight", p); l.Range = 12; l.Brightness = .8; l.Shadows = false; l.Color = p.Color
            end
        end
    end
    if p:IsA("PointLight") and p.Parent.Name:match("PendantLamp") then p.Range = 18; p.Brightness = 1.2 end
end
```
Beauty camera (menu / thumbnail, inside): `CFrame.lookAt(Vector3.new(9, 12, 34), Vector3.new(-2, 7, -50))`, FieldOfView 50.
Exterior: `CFrame.lookAt(Vector3.new(40, 26, 150), Vector3.new(0, 12, 40))`, FieldOfView 42.

## Layout (Roblox space, hall centre = origin, floor y = 1)
- Hall (rotunda): inner r 44, walls 22, dome ceiling to ~31 with a glass oculus. Entrance S (doors 14 x 13 at z 44.8),
  arch N (18 wide) into the lab wing (x +-24, z -36 .. -116, half-round end, ceiling 20, two skylights + a glass dome).
- Spawn plaza (0, 0.35, 118) faces -Z: path > forecourt (y 1, level with the hall floor) > doors > arch > Bloom Chamber.
- Stations: Heal W (machine x -40, counter x -27), Shop E (counter x 27, shelves on the wall), Storage NE (3 PCs on the
  wall at 294-318 deg), Trade NW (desk at 228 deg), Starter table (0, -60), Bloom Chamber (0, -93).

## Roofs and the camera
The rotunda roof is part of the `Rotunda` prop (precise collision, it rests on the walls). `HallCeiling` and `WingRoof`
(folder `Roof`) are separate props with no collision, so the interior reads from a third-person camera (ceiling 22-31
over a 92 wide hall; walls stay at 22). For a top-down or cutaway camera over the wing, hide them locally:
`for _, p in workspace.Bloomcrest.Roof:GetDescendants() do if p:IsA("BasePart") then p.LocalTransparencyModifier = 1 end end`
(the rotunda roof stays: hide the `Rotunda` MeshParts whose position is above y 23 if a full cutaway is needed).

## Gameplay hooks (`workspace.Bloomcrest.Hooks`, invisible anchored Parts, attribute `HookKind`)
| Folder | Parts | Use |
|---|---|---|
| spawn | `SpawnLocation` (0, 0.85, 118) | real SpawnLocation (Neutral), faces the entrance |
| station | `Heal`, `Shop`, `Storage`, `Trade`, `Lab`, `Starter` | name BillboardGui spots (a default label is made; restyle it) |
| counter | `HealCounter`, `ShopCounter`, `TradeDesk` | trigger boxes along the counters (ProximityPrompt) |
| healslot | `HealSlot1..6` | the six glowing cradles on the Restoration Bay: show the party's capsules here while healing |
| pc | `PC1..3` | storage terminals; the screens are blank glow parts (`PCTerminal_Glow_screen`) for a SurfaceGui |
| starter | `Starter_Mint`, `Starter_Coral`, `Starter_Sky` | the three starter Gem Pods under glass on the lab table |
| chamber | `ChamberPad` | Bloom Chamber pad (evolution / scan cutscene spot) |
| door | `DoorLeafL`, `DoorLeafR` | closed positions of the sliding leaves; the modelled leaves stand open (tween them) |
| sign | `WelcomeSign` | blank panel on the welcome monolith for the centre's name |

No text is modelled anywhere: every name, price and screen is a GUI on these anchors or on the glow / blank parts.

## Collision and performance
- Rotunda, LabWing, LabArchway, EntranceCanopy, EvoChamber, TradeDesk, HealCounter, StarterTable, RestNook, fountains:
  precise. Shelves, counters, machines, tanks, benches, terminals, lamps, planters: box. Trees: hull. Roofs, pendant
  lamps, sliding doors, flower beds, bushes, clouds: none. Floors / lawn / plaza: precise statics.
- The sliding doors have no collision (the doorway is always passable); script them if they should close.
- Trims, ceiling, hanging planters, rugs, mat, wall decor, plush, pond water, lily pads, reeds: none. Topiary,
  garden wall, indoor plants, supply cartons, sale stand, rope line, trophy shelf, water cooler: box.
- Budget: 435k placed triangles (15k headroom). Cut first if phones struggle: outdoor trees (43, ~75k), round bushes /
  flower beds, the 62 garden-wall segments (14k), capsule shelves (8k each), Horizon_Hills (11k; a Roblox Sky works).

## Catch balls and trees (2026-11-18)
- The capture ball is the original **catch ball** (`catch_ball` in lab_props.py), replacing the Gem Pod everywhere
  (`capsule()` now draws it): two thick shells on a seam tilted 20 deg, silver seam core, a raised pill latch with a
  glowing gem + light ring at the front, hinge knuckles at the back. Tiers: Basic mint over white (plain), Great sky
  with two stripes, Ultra coral over charcoal with a chevron, Master plum over gold with a star; a small raised Bloom
  Paw on each. LOD by size: hero ~1.6-2k tris (starter table, fountains), standard ~1k, shelf ~250-370. The middle
  starter ball is half-open (upper shell 70 deg up, glow inside). Glow key `gem` = the latch gems and the open-ball glow.
- Trees follow the skill's stylised_trees.md method: Skin-modifier skeleton trunks with branches, crowns of many
  separate leaves. Indoors: fiddle-leaf figs (curved two-sided leaves with a crease on petioles), braided olive trees
  (three twisting strands, dense small-leaf crown), monstera, snake plants; outdoors: rounded park trees and pink
  blossom trees in groups. 15 outdoor trees (~3.1-4k tris each).
- `HangingPot` (hanging planters) is named so the exporter's floating-foliage check does not treat it as ground
  foliage: it hangs from the coffered ceiling on purpose.
