# TidehookLagoon - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 70 | reuse: fewer unique meshes = less memory |
| Placed props | 567 (603 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 19 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 4 | sea / skirt planes |
| Total placed tris | 423,096 | hard budget 450,000 (--budget) |
| Largest prop | AquaDome (13536 tris) | <= 20000 per MeshPart |
| Footprint | x -693..714, z -771..846 | keep under 2,048 from origin for float precision comfort |
| Palette | TidehookLagoon_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| AquaDome | precise | 13536 |
| BaitShop | precise | 9544 |
| Barrels1 | box | 1860 |
| Bench1 | box | 380 |
| BoatHouse | precise | 8500 |
| BrainCoral1 | none | 742 |
| BrainCoral2 | none | 742 |
| BuoyStack1 | box | 992 |
| Cloud1 | none | 604 |
| Cloud2 | none | 610 |
| Cloud3 | none | 592 |
| Cooler1 | box | 464 |
| Cooler2 | box | 464 |
| CoralBranch1rd1 | none | 696 |
| CoralBranch2yd1 | none | 696 |
| CoralBranch3td1 | none | 694 |
| Crates1 | box | 2148 |
| DryRack1 | box | 2216 |
| FishIndexWall | box | 5878 |
| FishMarket | precise | 11314 |
| FishingBoat | precise | 3064 |
| GrassTuft1 | none | 224 |
| GrassTuft2 | none | 224 |
| HammockPalms1 | hull | 4222 |
| LifebuoyStand | box | 1044 |
| Lighthouse | precise | 4756 |
| MarkerBuoyRed | none | 638 |
| MarkerBuoyYellow | none | 638 |
| NetPile1 | none | 1690 |
| Palapa1 | hull | 876 |
| Palm1 | hull | 1940 |
| Palm2 | hull | 2014 |
| Palm3 | hull | 1894 |
| Palm4 | hull | 1992 |
| PalmPlanter1 | box | 1944 |
| PalmPlanter2 | box | 1944 |
| QuestBoard | box | 3520 |
| RailBay3p00 | box | 288 |
| RailBay3p50 | box | 288 |
| RailBay3p75 | box | 288 |
| RailBay4p25 | box | 288 |
| RailBay4p75 | box | 288 |
| RailBay4p75B | box | 416 |
| RailBay5p00 | box | 288 |
| RailBay5p00B | box | 416 |
| RailBay5p25 | box | 288 |
| RailBay5p25B | box | 416 |
| RailBay5p50 | box | 288 |
| RailBay5p50B | box | 416 |
| RailBay5p75 | box | 288 |
| RailBay5p75B | box | 416 |
| RailBay6p00 | box | 288 |
| RailBay6p00B | box | 416 |
| RailBay6p25 | box | 288 |
| RailBay6p25B | box | 416 |
| RailPost | box | 224 |
| ReefRock1 | hull | 350 |
| ReefRock2 | hull | 340 |
| RodHolder1 | box | 892 |
| RodRack1 | box | 1532 |
| RodShop | precise | 8536 |
| SeaStack1 | none | 1614 |
| SeaStack2 | none | 1630 |
| SeaStack3 | none | 1610 |
| SeaStack4 | none | 1626 |
| Shrub1 | none | 1648 |
| Shrub2 | none | 1648 |
| Skiff | precise | 1796 |
| TikiTorchStilt | box | 834 |
| WelcomeArch | precise | 3454 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| RailBay6p00 | 84 | 288 | 24,192 | 6% |
| TikiTorchStilt | 24 | 834 | 20,016 | 5% |
| Palm3 | 9 | 1894 | 17,046 | 4% |
| RailBay6p25 | 55 | 288 | 15,840 | 4% |
| AquaDome | 1 | 13536 | 13,536 | 3% |
| RailBay6p00B | 29 | 416 | 12,064 | 3% |
| Palm4 | 6 | 1992 | 11,952 | 3% |
| Palm1 | 6 | 1940 | 11,640 | 3% |
| RailBay5p75 | 40 | 288 | 11,520 | 3% |
| FishMarket | 1 | 11314 | 11,314 | 3% |
| BaitShop | 1 | 9544 | 9,544 | 2% |
| RailBay5p50 | 32 | 288 | 9,216 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (3)

- note Palm1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Palm2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Palm4: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `TidehookLagoonKit`).
2. Insert `TidehookLagoonSetup.lua` as ModuleScript ServerStorage.TidehookLagoonSetup, run `TidehookLagoonKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.TidehookLagoonSetup).Build(game.ServerStorage.TidehookLagoonKit, workspace)`, then `.ApplyLook()`.