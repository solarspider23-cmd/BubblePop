# MoonSweepers - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 77 | reuse: fewer unique meshes = less memory |
| Placed props | 660 (1107 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 33 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 409,522 | hard budget 450,000 (--budget) |
| Largest prop | DustExchange (6822 tris) | <= 20000 per MeshPart |
| Footprint | x -294..288, z -398..1680 | keep under 2,048 from origin for float precision comfort |
| Palette | MoonSweepers_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Airlock_z1 | precise | 2348 |
| Airlock_z2 | precise | 2348 |
| Airlock_z3 | precise | 2348 |
| Airlock_z4 | precise | 2348 |
| BeaconRail_beacon | box | 290 |
| BeaconRail_beacon_v001 | box | 290 |
| BeaconRail_beacon_v002 | box | 290 |
| BeaconRail_beacon_v003 | box | 290 |
| BeaconRail_beacon_v004 | box | 290 |
| BeaconRail_z1 | box | 290 |
| BeaconRail_z2 | box | 290 |
| BeaconRail_z3 | box | 290 |
| BeaconRail_z3_v001 | box | 290 |
| BeaconRail_z4 | box | 290 |
| BeaconRail_z4_v001 | box | 290 |
| CommsDish | hull | 1072 |
| Crater1_mare | box | 802 |
| Crater1_regA | box | 802 |
| Crater1_regB | box | 802 |
| Crater2_mare | box | 798 |
| Crater2_mare_v001 | box | 798 |
| Crater2_regA | box | 798 |
| Crater2_regB | box | 798 |
| Crater3_mare | box | 840 |
| Crater3_regA | box | 840 |
| Crater3_regB | box | 840 |
| DustExchange | precise | 7374 |
| DustPatch10_regB | none | 210 |
| DustPatch11_regB | none | 208 |
| DustPile0_regA | none | 174 |
| DustPile1_regA | none | 180 |
| DustPile2_regA | none | 170 |
| EggIncubator | hull | 6368 |
| FloodLight | hull | 820 |
| FuelTanks | box | 1796 |
| GearLocker | hull | 7132 |
| Horizon_Earth | none | 1280 |
| IceCrystal0 | hull | 220 |
| IceCrystal1 | hull | 200 |
| IceCrystal2 | hull | 194 |
| JumpPad_cyan | box | 1356 |
| JumpPad_z1 | box | 1356 |
| JumpPad_z2 | box | 1356 |
| JumpPad_z3 | box | 1356 |
| JumpPad_z4 | box | 1356 |
| JunkHeap0 | hull | 422 |
| JunkHeap1 | hull | 412 |
| JunkHeap2 | hull | 422 |
| LaunchTower | precise | 2364 |
| LunarLander | precise | 2548 |
| MeteorChunk0 | none | 124 |
| MeteorChunk1 | none | 122 |
| MeteorChunk2 | none | 124 |
| Meteorite7 | hull | 480 |
| MoonRock0_regA | hull | 146 |
| MoonRock1_regA | hull | 142 |
| MoonRock20_regB | hull | 140 |
| MoonRock21_regB | hull | 130 |
| MoonRock22_regB | hull | 130 |
| MoonRock2_regA | hull | 138 |
| MoonRock30_mare | hull | 136 |
| MoonRock31_mare | hull | 136 |
| MoonRock40_mare | hull | 136 |
| MoonRock41_mare | hull | 148 |
| MoonRock50_regB | hull | 134 |
| MoonRock51_regB | hull | 140 |
| MoonRock52_regB | hull | 138 |
| MoonRock60_regA | hull | 152 |
| MoonRock61_regA | hull | 134 |
| MoonRock62_regA | hull | 134 |
| MoonRock63_regA | hull | 150 |
| MoonRocket | hull | 7380 |
| MoonRover | hull | 2516 |
| ReentryPod | hull | 6006 |
| SupplyCrates1 | box | 560 |
| SupplyCrates2 | box | 560 |
| SupplyCrates3 | box | 560 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| BeaconRail_beacon_v003 | 88 | 290 | 25,520 | 6% |
| BeaconRail_beacon_v002 | 79 | 290 | 22,910 | 6% |
| FloodLight | 24 | 820 | 19,680 | 5% |
| BeaconRail_beacon_v004 | 44 | 290 | 12,760 | 3% |
| SupplyCrates1 | 17 | 560 | 9,520 | 2% |
| BeaconRail_beacon | 32 | 290 | 9,280 | 2% |
| Crater3_regB | 11 | 840 | 9,240 | 2% |
| Crater2_regA | 11 | 798 | 8,778 | 2% |
| MoonRocket | 1 | 7380 | 7,380 | 2% |
| DustExchange | 1 | 7374 | 7,374 | 2% |
| GearLocker | 1 | 7132 | 7,132 | 2% |
| Crater1_regA | 8 | 802 | 6,416 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (5)

- note BeaconRail_beacon: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note BeaconRail_beacon_v001: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note BeaconRail_beacon_v002: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note BeaconRail_beacon_v003: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note BeaconRail_beacon_v004: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `MoonSweepersKit`).
2. Insert `MoonSweepersSetup.lua` as ModuleScript ServerStorage.MoonSweepersSetup, run `MoonSweepersKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.MoonSweepersSetup).Build(game.ServerStorage.MoonSweepersKit, workspace)`, then `.ApplyLook()`.