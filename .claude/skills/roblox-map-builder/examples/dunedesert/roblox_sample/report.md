# GildedDunes - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 60 | reuse: fewer unique meshes = less memory |
| Placed props | 474 (485 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 9 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 304,805 | hard budget 450,000 (--budget) |
| Largest prop | StepPyramid (17770 tris) | <= 20000 per MeshPart |
| Footprint | x -365..365, z -369..364 | keep under 2,048 from origin for float precision comfort |
| Palette | GildedDunes_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| CamelKneel1 | hull | 2618 |
| CamelKneel2 | hull | 2618 |
| CamelStand1 | hull | 2674 |
| CamelStand2 | hull | 2674 |
| Campfire | box | 418 |
| CargoPile1 | box | 1446 |
| ColossusHead | precise | 14526 |
| ColumnBroken2 | box | 430 |
| ColumnFallen3 | box | 578 |
| ColumnTall1 | box | 802 |
| DryShrub1 | none | 342 |
| DryShrub2 | none | 338 |
| DuneGrass1 | none | 39 |
| DuneGrass2 | none | 45 |
| OasisBasin | precise | 1328 |
| OasisWater | none | 32 |
| Obelisk1 | box | 3672 |
| ObeliskFallenMid2 | hull | 1098 |
| ObeliskFallenTop1 | hull | 1536 |
| ObeliskStump1 | precise | 546 |
| Outcrop1 | hull | 98 |
| Outcrop2 | hull | 94 |
| PylonGate | precise | 2752 |
| QuestStele | box | 1084 |
| RockStack1 | hull | 120 |
| RockStack2 | hull | 122 |
| RugSpread1 | none | 836 |
| RuinArch1 | precise | 1000 |
| RuinArch2 | precise | 1000 |
| RuinHouse1 | precise | 1824 |
| RuinHouse2 | precise | 2088 |
| RuinWall1 | precise | 1344 |
| RuinWall2 | precise | 1232 |
| RuinWall3 | precise | 880 |
| SandDrift1 | none | 224 |
| SleepTent1 | precise | 984 |
| SleepTent2 | precise | 984 |
| SpawnDais | precise | 1698 |
| StepPyramid | precise | 17910 |
| SunAstrolabe | box | 2154 |
| SunkenTemple | precise | 18240 |
| TraderTent | precise | 4446 |
| TreasureMound1 | precise | 484 |
| TreasureMound2 | precise | 700 |
| TreasureMound3 | precise | 1368 |
| TreePalmA_Branches | none | 52 |
| TreePalmA_Leaves | none | 1020 |
| TreePalmA_Trunk | hull | 1980 |
| TreePalmB_Branches | none | 40 |
| TreePalmB_Leaves | none | 924 |
| TreePalmB_Trunk | hull | 1420 |
| TreePalmC_Branches | none | 28 |
| TreePalmC_Leaves | none | 828 |
| TreePalmC_Trunk | hull | 750 |
| Waystone1 | box | 358 |
| Waystone2 | box | 362 |
| WyrmRib1 | precise | 772 |
| WyrmRib2 | precise | 772 |
| WyrmRib3 | precise | 676 |
| WyrmSkull | hull | 2012 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| DryShrub1 | 86 | 342 | 29,412 | 10% |
| SunkenTemple | 1 | 18240 | 18,240 | 6% |
| StepPyramid | 1 | 17910 | 17,910 | 6% |
| DryShrub2 | 43 | 338 | 14,534 | 5% |
| ColossusHead | 1 | 14526 | 14,526 | 5% |
| Obelisk1 | 3 | 3672 | 11,016 | 4% |
| TreePalmA_Trunk | 5 | 1980 | 9,900 | 3% |
| ColumnTall1 | 10 | 802 | 8,020 | 3% |
| TreasureMound3 | 5 | 1368 | 6,840 | 2% |
| TreePalmA_Leaves | 5 | 1020 | 5,100 | 2% |
| Waystone1 | 14 | 358 | 5,012 | 2% |
| ObeliskStump1 | 9 | 546 | 4,914 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (3)

- note TreePalmA_Branches: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note TreePalmB_Branches: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note TreePalmB_Leaves: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `GildedDunesKit`).
2. Insert `GildedDunesSetup.lua` as ModuleScript ServerStorage.GildedDunesSetup, run `GildedDunesKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.GildedDunesSetup).Build(game.ServerStorage.GildedDunesKit, workspace)`, then `.ApplyLook()`.