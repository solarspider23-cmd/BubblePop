# Moon Sweepers - Studio setup

Files: `roblox/` (export of `moon_map.blend` with `--materials`: ground and rocks use Roblox Sand (dusty regolith), Slate (grey
shelves, crater walls), Basalt (dark mare) and Snow (frost); tech props SmoothPlastic / Metal). Nothing is imported yet.
The ground is roughed in the mesh itself: modelled crater props (smooth 36-sided bowls with lit rims and ejecta, group `Craters`) sitting in shallow ground dishes and jagged riser walls.

1. Import 3D: every GLB in `roblox/kit/` and `roblox/static/` into `ServerStorage.MoonSweepersKit` (studs, pivot at
   origin, one Model per file). Upload `roblox/MoonSweepers_Palette.png` once if the importer drops the texture and put
   its id in `M.PaletteTexture`.
2. Create ModuleScript `ServerStorage.MoonSweepersSetup` with `roblox/MoonSweepersSetup.lua`.
3. Command bar: run `roblox/MoonSweepersKitPrep.lua` (collision fidelity per prop).
4. Import `roblox/AxisProbe.glb` once: its arrow must point along -Z; if it points +Z set `M.YAW_FIX = 180`.
5. Command bar:
```lua
local S = require(game.ServerStorage.MoonSweepersSetup)
S.Build(game.ServerStorage.MoonSweepersKit, workspace)
S.ApplyLook()
-- moon extras: black starry sky, no haze, earthshine ambient, low gravity, spawn on the hub pad facing the crater
local L = game.Lighting
L.Ambient = Color3.fromRGB(40, 46, 64); L.OutdoorAmbient = Color3.fromRGB(96, 108, 140)
L.EnvironmentDiffuseScale = 0.3; L.EnvironmentSpecularScale = 0.2
local atm = L:FindFirstChildOfClass("Atmosphere"); if atm then atm.Density = 0; atm.Haze = 0; atm.Glare = 0 end
local sky = L:FindFirstChildOfClass("Sky") or Instance.new("Sky")
sky.StarCount = 3000; sky.CelestialBodiesShown = false   -- the Earth is a mesh (Horizon_Earth); sun disc stays via SunAngularSize
sky.Parent = L
workspace.Gravity = 70        -- low-gravity hop (default 196.2); tune with the jump pads
local sp = workspace:FindFirstChildOfClass("SpawnLocation") or Instance.new("SpawnLocation")
sp.Size = Vector3.new(8, 1, 8); sp.Transparency = 1; sp.CanCollide = false; sp.Anchored = true
sp.CFrame = CFrame.new(0, 9.5, -318) * CFrame.Angles(0, math.pi, 0)   -- hub pad, looking south (+Z) through Gate 1 at the rocket
sp.Parent = workspace
```
For the black space sky, upload a plain black (optionally starred) image of your own and set the six `Skybox*` faces
to it; the default Roblox skybox is a blue day sky. No asset ids are invented here.

## Gameplay hooks (names in the placed map)
- Stations: `DustExchange` (sell), `GearLocker` (shop), `ReentryPod` (rebirth), `EggIncubator` (pets) in group `Hub`.
- Zone gates: `Airlock_z1` (free, hub edge) .. `Airlock_z4`, group `Gates`; the glowing laser bars are the barrier parts.
  Return pads `JumpPad_z1..z4` on each lower shelf next to the ramp foot.
- Mess (collision none, ready for ProximityPrompts / touch collection): groups `Mess_Z1` (DustPatch, DustPile),
  `Mess_Z2` (MeteorChunk, DustPatch), `Mess_Z3` (JunkHeap), `Mess_Z4` (IceShards, JunkHeap).
- Zones by radius from (0, 0): Z1 205-251 (floor y -12), Z2 145-199 (-34), Z3 92-139 (-58), Z4 52-86 (-84).
- Add invisible walls on the shelf lips (radius 259.7, 206.7, 146.7, 93.7; gaps at the ramps) so players cannot
  drop past a locked airlock: the beacon rails mark the lips but are only 2.4 studs tall.

Budget: 660 placements, 409,522 triangles in total (450k hard budget); 33 static chunks (static <= 150k).

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: `--name MoonSweepers --materials --float-ok <default>|earth` (Horizon_Earth is a sky backdrop). Budget: ground polar grid 400 x coarser radial steps (static under 150k), beacon rails in 20-stud spans, hub rail 36 segments. Mess (dust / meteor chunks / junk) only on calm ground and sat on the highest mesh point under it; crater props never overlap; the spawn jump pad sits on the hub deck (top y 9.1).
