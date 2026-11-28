# Northgate Distribution - build, export and Studio setup

PHOTOREAL interior example: real-object kit (pallet racking, forklifts, dock doors, an overhead crane, trailers),
Roblox materials per palette ramp (`--materials`) and a Cycles pass that renders the same scene photoreal.

## Build
```bash
"${BLENDER:-blender}" -b --factory-startup --python wh_map.py -- [norender | more]   # wh_map.blend + previews/map_*.png
"${BLENDER:-blender}" -b wh_map.blend --python wh_real.py -- spawn aisle crane dock mezz yard truck   # previews/real_*.png
./studio.sh "forklift(1, 'wrapped')" "rack_bay(1)"                                          # close-up QA -> studio/
```
`wh_real.py` never saves: it turns the preview scene into a photoreal one at render time (smooth by angle, Bevel node
on every material, polished-concrete roughness noise, a real spot light under every high-bay, sun + Nishita sky through
the open docks and skylights, a volume-scatter dust box, DOF; OPTIX/CUDA if there is a GPU). Env knobs: `SAMPLES`,
`SPOT`, `SUN`, `SKY`, `HAZE=0`, `DENSITY`, `EXPOSURE`, `RX`/`RY`.

## Export
```bash
"${BLENDER:-blender}" -b wh_map.blend --python ../../scripts/roblox_export.py -- --name NorthgateWarehouse --materials \
  --hero '^(CraneTrolley|Mezzanine)$' \
  --float-ok '(?i)HighBay|Skylight|Truss|Runway|Crane|Container|Charger|FirePoint|DockDoor|PersonnelDoor'
```
Collision rules for this map's prop names live in `collision_rules.json` (read automatically next to the .blend).
`roblox_sample/` holds the report (EXPORT_OK, 379k tris, placement checks all 0), manifest, setup and KitPrep modules.

## Studio
Import `kit/` + `static/` + AxisProbe into `ServerStorage.NorthgateWarehouseKit`, run the KitPrep script, then
`require(game.ServerStorage.NorthgateWarehouseSetup).Build(kit, workspace)`. Suggested look (instead of `ApplyLook()`):
```lua
local L = game.Lighting
L.Technology = Enum.Technology.Future; L.ClockTime = 16.8; L.Brightness = 2.2
L.Ambient = Color3.fromRGB(70, 74, 82); L.OutdoorAmbient = Color3.fromRGB(120, 126, 136)
local a = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L); a.Density = 0.32; a.Haze = 1.4
a.Color = Color3.fromRGB(214, 206, 190); a.Decay = Color3.fromRGB(150, 140, 120)
```
Add a PointLight (Range 40, Brightness 1.5, warm white) to each `HighBay0` Neon part for the interior pools of light.
Spawn: `anchors.json` (-108, 0.5, 38) facing east down the cross aisle, the crane + container in view.

## Method notes
- Repeated props are the budget: one rack bay is ~3k tris (lite pallets, no bevels, single-sided decal quads for
  tape, labels, perforation slots); 55 bays = 160k of the 379k total. `tricount.py` prints tris per sub-assembly.
- `cull()` in `wh_map.py` drops faces nobody sees (bottoms on the floor, backs of wall props) but skips hanging
  props (`HANGING`): a lamp's glowing disc IS its bottom face.
- Cycles + the Bevel node draws seams along long thin n-gon fan triangles (truck cab): those meshes get bevel-free
  material copies in `wh_real.py`.
