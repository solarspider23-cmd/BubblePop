# Maple Junction - Studio setup

Files: `roblox/` = export of `town_map.blend`
(`roblox_export.py -- --name MapleJunction --hero "^(TownHall|TrainStation)$"`, no `--materials`).
76 kit props, 419 placements, 6 static chunks, **439,275 placed triangles** (budget 450k; report.md: Budget ok, EXPORT_OK,
placement checks all 0). Nothing is imported yet.

## Texture
Every solid MeshPart uses ONE painted atlas, `roblox/MapleJunction_Palette.png` (1024 px, 4 x 4 blocks made by
`city_paint.py`): brick, cream stucco (ashlar joints), sage clapboard, slate shingles, asphalt, sidewalk slabs are real 2D
tiles (dark band + light band, clipped at the tile period in the mesh so bricks keep their size); glass, metal, leaf,
grass, wood and the accent colours are painted ramps. The GLBs embed it; if the importer drops it, upload the PNG once and
set it on every non-glow MeshPart:
```lua
local S = require(game.ServerStorage.MapleJunctionSetup)
S.PaletteTexture = "rbxassetid://<the id Roblox gives you>"
for _, p in game.ServerStorage.MapleJunctionKit:GetDescendants() do
    if p:IsA("MeshPart") and not p.Name:find("_Glow_") then p.TextureID = S.PaletteTexture end
end
```
Glow keys (Neon): `lamp` (street lanterns, platform + passage lamps, + PointLight), `sigred` / `siggreen` (one lit lens per
traffic signal), `walk` (pedestrian signal, bus-shelter ad panel), `spray` (fountain jets + spill curtains).

## Realistic street trees (`Tree*` props: own textures, SurfaceAppearance)
The faceted street / median / park trees are replaced by realistic alpha-card trees from `examples/oaktrees/gen_trees.py`
(imported by `town_map.py`), 25 trees, ~49k tris: every tree is THREE MeshParts on one origin, placed with the same CFrame:
`Tree<Species>_Trunk` (bark), `Tree<Species>_Branches` (twig cards), `Tree<Species>_Leaves` (leaf cards).

| Species | Where | Tris (Trunk / Branches / Leaves) | Copies |
|---|---|---|---|
| `StreetOak` | half the sidewalk tree slots (in a `StreetGrate`, scale 0.82-0.9 so the crown clears facades) + one big oak per square lawn (scale 1.3) | 810 / 216 / 992 | 11 (7 street, 4 park) |
| `StreetBirch` | the other sidewalk tree slots (in a `StreetGrate`) + the boulevard median | 820 / 152 / 676 | 14 |

`StreetGrate` (260 tris, palette atlas like every other solid) is the old tree pit alone: stone kerb, iron grate, trunk
ring; the realistic trunk stands in its ring. Street slots: every other old slot keeps a tree (realistic trees cost
~1.6-2k each), lamps and furniture unchanged. Leaf atlases graded for the sunny street: `oak_t`, `birch_t`.

Each tree GLB in `roblox/kit/` embeds its own PNGs (also in `examples/oaktrees/roblox/textures/`): `*_Trunk` =
`<bark>_bark_color` + `_normal` (1024, tiling: UVs run past 0..1 on purpose), `*_Leaves` = `<leaf>_leaves_color` (1024
RGBA atlas, alpha cut-out) + normal, `*_Branches` = `<twig>_twigs_color` (512 RGBA) + normal. After import check each
`Tree*` MeshPart has a SurfaceAppearance (else upload the PNGs and make one), then set **AlphaMode** `*_Trunk` =
**Overlay**, `*_Branches` / `*_Leaves` = **Transparency**, and DoubleSided = true on the cards. `S.Build` tries these
with a pcall and never puts the palette TextureID on a part that has a SurfaceAppearance; by hand:
```lua
for _, p in workspace.MapleJunction:GetDescendants() do
    local sa = p:IsA("MeshPart") and p:FindFirstChildOfClass("SurfaceAppearance")
    if sa and p.Name:match("^Tree") then
        sa.AlphaMode = if p.Name:match("_Trunk$") then Enum.AlphaMode.Overlay else Enum.AlphaMode.Transparency
        if not p.Name:match("_Trunk$") then p.DoubleSided = true; p.CanCollide = false; p.CanQuery = false end
    end
end
```

## Import
1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.MapleJunctionKit` (studs, pivot at origin,
   anchored). Import `roblox/AxisProbe.glb` once: arrow along -Z, else `M.YAW_FIX = 180`.
2. ModuleScripts in ServerStorage: `MapleJunctionSetup` = `roblox/MapleJunctionSetup.lua`, `MapleJunctionHooks` =
   `roblox/MapleJunctionHooks.lua` (same as `Hooks.lua`). Run `roblox/MapleJunctionKitPrep.lua` once in the command bar.
3. Command bar:
```lua
local S = require(game.ServerStorage.MapleJunctionSetup)
S.Build(game.ServerStorage.MapleJunctionKit, workspace)
require(game.ServerStorage.MapleJunctionHooks).Build(workspace.MapleJunction)
```
Collision (report.md): buildings, landmarks, platform, fountain, ground = PreciseConvexDecomposition (awnings and fire
escapes must not block sidewalks / the alley); street furniture, cars, train, skyline = Box; tree trunks + grates Hull, tree cards none; markings,
flower beds, trash bags = none.

## Look: bright daytime town (paste after Build; replaces `S.ApplyLook()`)
```lua
local L = game:GetService("Lighting")
L.Technology = Enum.Technology.Future
L.ClockTime = 9.8                      -- sun ~48 deg, from the south-east (behind-left of the spawn view)
L.GeographicLatitude = 30
L.Brightness = 3.2
L.ExposureCompensation = 0.1
L.Ambient = Color3.fromRGB(120, 132, 150)
L.OutdoorAmbient = Color3.fromRGB(150, 170, 200)
L.ColorShift_Top = Color3.fromRGB(255, 244, 222)
L.ColorShift_Bottom = Color3.fromRGB(70, 88, 120)
L.EnvironmentDiffuseScale = 0.6
L.EnvironmentSpecularScale = 0.25
L.GlobalShadows = true
L.ShadowSoftness = 0.25
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.28; atm.Offset = 0.15; atm.Haze = 0.6; atm.Glare = 0.2
atm.Color = Color3.fromRGB(214, 232, 255); atm.Decay = Color3.fromRGB(150, 185, 235)
local cc = L:FindFirstChildOfClass("ColorCorrectionEffect") or Instance.new("ColorCorrectionEffect", L)
cc.Saturation = 0.12; cc.Contrast = 0.1; cc.Brightness = 0.02; cc.TintColor = Color3.fromRGB(255, 252, 246)
local bloom = L:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect", L)
bloom.Intensity = 0.25; bloom.Size = 18; bloom.Threshold = 1.2
```
Use a plain Roblox Sky (default clouds) - the skyline ring frames the edges; the asphalt plane ends 40 studs past the
blocks, which the towers hide from street level. Compare with `previews/map_spawn.png` / `map_beauty.png`.

## Gameplay hooks (Hooks.lua, 239 parts)
- `Spawn/SpawnLocation` (0, 1.1, 26) facing north.
- Stations (attr `Station`): `Shop`, `Cafe`, `Boutique` (shop doors), `Bank` (+ `Bank_Prompt` at the steps), `CarDealer`
  (turntable in the open display hall; 6 lot cars + 2 display cars are props), `JobBoard` (board face), `TrainStation`
  (platform) + `TrainTravel` (boarding box beside the train) + `TrainDoor`.
- 20 `sign` faces: every shopfront fascia on the square / boulevard, the dealer fascia, the station band. No text is
  modelled anywhere: labels are SurfaceGuis / BillboardGuis.
- Road paths: `North_East/West`, `Blvd_East/West`, `West_South/North`, `East_South/North` lane points every 24 studs
  (attrs Path, Order, Dir, Speed), 4 `roadnode` junction boxes, `SquareWalk` NPC sidewalk loop (26 points).
- Parked / lane cars, the bus and the train are static props: hide or replace them with scripted vehicles that follow
  the road paths.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: `--name MapleJunction --hero ^(TownHall|TrainStation)$` (unchanged). Placement fixes: east-block corner building is a Cafe (ends at x 276, clear of the station row), parked cars keep clear of the lane cars, road markings have no bottom face (no coplanar floor with the asphalt), track ends at z 286 (on the ground).
