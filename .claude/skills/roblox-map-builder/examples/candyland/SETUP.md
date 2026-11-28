# Sugarcrest Kingdom - Studio setup

`roblox/` contains the export of `candy_map.blend`. It was made with `--materials --hero "^(CandyCastle|ChocoMountain)$" --rock
"(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|mountain"` (gumdrop mountains are the map's rock frame: they overlap
each other and bed into the ground on purpose);
`material_map.json` holds the material per palette ramp:

| Roblox material | What uses it |
|---|---|
| Glass (opaque, glossy) | hard candy: cherry, berry, lime, lemon, grape, blue, orange; chocolate |
| Glass + Transparency | blue-raspberry jelly (moat, gumball globe, egg dome, candy jars) |
| Sand (crumb grain) | gingerbread, biscuits, waffle cones, donut dough, crumb banks |
| SmoothPlastic | frosting, icing, cotton candy, clouds, board tiles, gumdrops |
| Snow (soft sugar) | the mint frosting ground |

Nothing has been imported into Studio yet.

Budget (report.md): 259 placements, **440,172 placed triangles** (hard budget 450k), 52 kit props, 11 static chunks,
`EXPORT_OK`, every placement check at 0 (clip, float, water, falls, collision). Fudge Falls is three props on one origin:
`ChocoMountain` (the gumdrop mountain = the lip, hero, precise), `ChocoFalls` (the cascade ribbon, none) and `ChocoPool`
(the frothy pool slab at its foot, none). The moat's piped icing rims are their own static `IcingCaps_CastleRim` (not
water) on the flat lips. Every auto-grounded hard prop is fitted while placing (`fit` in candy_map.py = the export's
clip + float rules).

| Item | Triangles |
|---|---|
| CandyCastle (hero) | 20.2k, largest MeshPart 19.0k |
| ChocoMountain (hero) + ChocoFalls + ChocoPool | 3.1k + 0.5k + 2.0k |
| Each station | 6.8k to 11.5k |
| All static chunks together | 95k |

## Import
1. File > Import 3D:
   - Select every GLB in `roblox/kit/` and `roblox/static/`, plus `roblox/AxisProbe.glb`.
   - Settings: scale unit studs, pivot at scene origin, anchored.
   - Put the imported models in one Folder, `ServerStorage.SugarcrestKingdomKit`.
2. Set up the scripts:
   - ModuleScript `ServerStorage.SugarcrestKingdomSetup` = `roblox/SugarcrestKingdomSetup.lua`.
   - ModuleScript `ServerStorage.SugarcrestKingdomHooks` = `Hooks.lua`.
   - Run `roblox/SugarcrestKingdomKitPrep.lua` once in the command bar to set collision fidelity.
3. AxisProbe: its arrow must point along LookVector (-Z). If it points backwards, set `M.YAW_FIX = 180`.
4. Command bar:
```lua
local S = require(game.ServerStorage.SugarcrestKingdomSetup)
S.LightKeys.oven = true; S.LightKeys.portal = true; S.LightKeys.window = true   -- oven fire, gumball chute, castle windows
S.Build(game.ServerStorage.SugarcrestKingdomKit, workspace)
S.ApplyLook()                                                        -- picks ClockTime ~8.5 to match the Blender sun (38 deg, SE)
require(game.ServerStorage.SugarcrestKingdomHooks).Build(workspace.SugarcrestKingdom)
-- pastel late morning: warm cream key, lilac-blue shadows, thin pink haze, soft bloom
local L = game.Lighting
L.Technology = Enum.Technology.Future
L.Brightness = 3
L.Ambient = Color3.fromRGB(150, 140, 190); L.OutdoorAmbient = Color3.fromRGB(176, 170, 220)
L.ColorShift_Top = Color3.fromRGB(255, 236, 214); L.ColorShift_Bottom = Color3.fromRGB(120, 110, 170)
L.EnvironmentDiffuseScale = 0.6; L.EnvironmentSpecularScale = 1     -- Glass candy picks up the sky
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.3; atm.Offset = 0.1; atm.Haze = 1.2; atm.Glare = 0.2
atm.Color = Color3.fromRGB(255, 226, 240); atm.Decay = Color3.fromRGB(150, 160, 255)
local bloom = L:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect", L)
bloom.Intensity = 0.35; bloom.Size = 18; bloom.Threshold = 1.1
local cc = L:FindFirstChildOfClass("ColorCorrectionEffect") or Instance.new("ColorCorrectionEffect", L)
cc.Saturation = 0.18; cc.Contrast = 0.08; cc.TintColor = Color3.fromRGB(255, 248, 252)
-- jelly glass: the only parts with colour (84, 224, 252) on Glass are the moat, gumball globe, egg dome and jars
local JELLY = Color3.fromRGB(84, 224, 252)
for _, p in workspace.SugarcrestKingdom:GetDescendants() do
	if p:IsA("MeshPart") and p.Material == Enum.Material.Glass then
		local c = p.Color
		if math.abs(c.R - JELLY.R) + math.abs(c.G - JELLY.G) + math.abs(c.B - JELLY.B) < 0.05 then
			p.Transparency = p.Name:find("Moat") and 0.2 or 0.45
		end
	end
	if p:IsA("PointLight") then p.Range = 10; p.Brightness = 0.8; p.Shadows = false end
end
```
Sky: no modelled sky dome is exported. Use a plain `Sky` (or none) with the Atmosphere above. The cotton-candy cloud
ring (`Clouds_Horizon`) and the gumdrop mountain ring frame the map.

Compare a Studio screenshot from the spawn with `previews/map_spawn.png`. Tune the numbers above, not the build.

Beauty camera (menu shot): `CFrame.lookAt(Vector3.new(-150, 62, 214), Vector3.new(10, 6, -96))`, `FieldOfView = 38`.

## Collision
- **Precise:** the stations, bridges, donut arches, castle, Fudge Falls and drawbridge.
- **Box:** lamps, macarons and marshmallow stepping stones.
- **Hull:** canes, trees, gumdrops, jelly beans and mountains.
- **None:**
  - The board tiles, sprinkles, icing caps, flowers and clouds. The tiles and caps float 0.3-0.5 above the collidable
    ground, so you walk on the ground under them.
  - The river surface and the jelly moat surface. Players wade down to the beds at about y -6 (river) and y 0 (moat).
    For a "lava" rule, put a kill or slow volume on the River_Choc part.

## Gameplay hooks (`Hooks.lua`, generated from `anchors.json` by `hooks_lua.py`)
Hooks are invisible tagged Parts (`Sugarcrest_<kind>`) with attributes. Every station has a BLANK wafer sign face (a
cream plate in a piped frame). Put a SurfaceGui on the sign hook's Front face. No text is modelled.

| Hook | Kind | Position (x, y, z) | Yaw | What |
|---|---|---|---|---|
| Spawn | spawn | (0, 1.3, 142) | 0 (faces north) | spawn cookie; view = Royal Road through the donut arch to the castle |
| CupcakeFountain | station | (0, 3.6, 151) | 0 | spawn plaza fountain front |
| SweetShop (+ _Sign) | station / sign | (-98, 2.9, 175) | 0 | shop door + counter window |
| BakeryOven (+ _Sign) | station / sign | (98, 2.0, 175) | 0 | upgrade oven mouth |
| EggMachine (+ _Sign) | station / sign | (-162.5, 2.8, -130.8) | 241.6 | hatch dome; sign on the pedestal |
| QuestStand (+ _Sign) | station / sign | (-16.9, 6.1, -78.4) | 308.9 | wafer kiosk; 4.4 x 3.4 board = quest list |
| GumballMachine (+ _Sign) | station / sign | stop (176, 80) | faces the stop | teleport menu |
| GumballPortal | travel | glowing chute door | | walk-in teleport trigger |
| CastleGate | door | (0, 6, -150.5) | 180 | castle interior / boss / rebirth gate |
| StepStone1..5 | stepstone | across the river near (204, 3) | | marshmallow jump run (attr Order) |
| FallsSplash / FallsCave | vfx | Fudge Falls | | ParticleEmitter spots: chocolate splash + foam, spring glints |

Exact values are in `anchors.json` and `Hooks.lua`.

## Files
| File | What it is |
|---|---|
| `candy_props.py` | the kit: 30 prop functions |
| `candy_studio.py` | prop_studio wrapper with the candy preview materials. Close-ups: `./studio.sh "castle()"` writes to `studio/` |
| `candy_map.py` | the layout, H, trails, river, moat, icing caps, clouds, placement with the exporter's clip test, look, renders, `anchors.json`, `material_map.json` |
| `hooks_lua.py` | builds `Hooks.lua` from `anchors.json` |

Rebuild and export:
```bash
blender -b --factory-startup --python candy_map.py -- more
blender -b candy_map.blend --python <skill>/scripts/roblox_export.py -- --name SugarcrestKingdom --materials --hero "^(CandyCastle|ChocoMountain)$" --rock "(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|mountain"
py hooks_lua.py
```
