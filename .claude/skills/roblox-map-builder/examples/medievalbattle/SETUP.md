# Riverfield Siege - Studio setup

Files: `roblox/` (export of `battle_map.blend` with `--materials`: grass = Grass, roads / banks = Ground, keeps + bridge =
Limestone, chapel / field stone = Slate, timber = WoodPlanks / Wood, iron = CorrodedMetal, canvas / paint = Fabric,
river = Glass). Nothing is imported yet. Ground, roads (`Path_Roads` ribbons) and hills have smooth normals.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.RiverfieldSiegeKit` (studs, pivot at
   origin, one Model per file). If the importer drops the texture, upload `roblox/RiverfieldSiege_Palette.png` once and
   put its id in `M.PaletteTexture`.
2. ModuleScript `ServerStorage.RiverfieldSiegeSetup` = `roblox/RiverfieldSiegeSetup.lua`; run `roblox/RiverfieldSiegeKitPrep.lua`.
3. Import `roblox/AxisProbe.glb` once: arrow must point along -Z, else `M.YAW_FIX = 180`.
4. Command bar:
```lua
local S = require(game.ServerStorage.RiverfieldSiegeSetup)
S.Build(game.ServerStorage.RiverfieldSiegeKit, workspace)
S.ApplyLook()
-- storm-break dusk: low amber sun from the south-west, slate sky, thin warm haze
local L = game.Lighting
L.ClockTime = 17.4; L.GeographicLatitude = 30
L.Ambient = Color3.fromRGB(70, 66, 74); L.OutdoorAmbient = Color3.fromRGB(128, 120, 118)
local atm = L:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere", L)
atm.Density = 0.32; atm.Haze = 1.6; atm.Color = Color3.fromRGB(214, 186, 160); atm.Decay = Color3.fromRGB(92, 104, 128)
for _, p in workspace:GetDescendants() do                 -- river: see-through, slightly reflective
    if p:IsA("MeshPart") and p.Name:match("^River_") then p.Transparency = 0.25; p.Reflectance = 0.08; p.CanCollide = false end
end
for side, x in { Crimson = -238, Azure = 238 } do         -- team spawns in the courtyards, facing the gate / bridge tower
    local sp = Instance.new("SpawnLocation"); sp.Name = side .. "Spawn"; sp.Anchored = true
    sp.Size = Vector3.new(8, 1, 8); sp.Transparency = 1; sp.CanCollide = false
    sp.CFrame = CFrame.lookAt(Vector3.new(x, 16.6, 0), Vector3.new(0, 16.6, 0)); sp.Parent = workspace
end
```
Set the two SpawnLocations' `TeamColor` to your teams (Crimson = west / red shields, Azure = east / blue shields).

## Gameplay hooks (names in the placed map)
- Keeps: groups `Keep_red` (x -255) / `Keep_blue` (x +255): `Gatehouse_*` (gate on the river side), `Donjon_*` +
  `DonjonTop_*` (crown, same origin, lowest point 32 up by design), `WallStair14` x2 to the wall-walk (y 30),
  `Hardscape_Court_*` courtyard at y 16.
- Lanes over the river (x 0): `SunderedBridge` + `BridgeTower` at z 0 (deck y 6.5; the two inner spans are crossed on
  timber patches, so the tower is the chokepoint); `FootBridge40` x2 to `RuinedChapel` on Chapel Isle (0, -142, top y 10);
  Southern Ford at z 100-160 (water 0.9 deep, gravel bed), trenches with `Wattle*` walls on both banks.
- Cover: `Mantlet_*`, `Cheval10`, `DryWall*`, `SiegeTower_*`, `BatteringRam`, `HayBales*`, `Palisade*` (signature,
  every trench lip and the ford banks), `Trebuchet_*` camps south of each keep.
- Collision: walkable statics and walls `precise`, cover `box`, decor (roads, debris, duckboards, graves) `none`.
- Add invisible walls on the valley rims (|x| > 320, |z| > 200) if players must stay in the arena.

Budget: 474 placements, 448,719 triangles in total (450k hard budget).
12 static chunks.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: `--name RiverfieldSiege --materials --hero ^(SunderedBridge|BridgeTower)$` (the bridge + its gate tower are the brief's hero). 450k budget: 4-stud ground grid, faces buried inside a prop's own solid parts are culled at kit build (never visible), fewer trees / mantlets / carts / chevals / drystone walls / bushes / tufts, wattle on every other trench segment. Props are grounded on the ground MESH (Hm), the river is a 4-stud water grid cut where it would be buried under the isle / far banks, the bed rises to a bank at the map ends. East keep uses a mirrored stair kit (`WallStair14M`; the rotated copy ran into the east walls). Gate / donjon braziers removed (they stood inside them).
