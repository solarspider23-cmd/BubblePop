# SunspireBazaar - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 38 | reuse: fewer unique meshes = less memory |
| Placed props | 251 (348 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 12 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 290,669 | hard budget 450,000 (--budget) |
| Largest prop | SunTemple (15122 tris) | <= 20000 per MeshPart |
| Footprint | x -107..105, z -279..291 | keep under 2,048 from origin for float precision comfort |
| Palette | SunspireBazaar_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Agave1 | none | 736 |
| Agave2 | none | 646 |
| Boulder1 | hull | 106 |
| Boulder2 | hull | 94 |
| Brazier1 | box | 478 |
| CarvedStair24_1 | precise | 3390 |
| CarvedStair24_2 | precise | 3392 |
| DryGrass1 | none | 126 |
| DryGrass2 | none | 126 |
| ForgeStation | precise | 1768 |
| Hoodoo1 | hull | 438 |
| Hoodoo2 | hull | 444 |
| Hoodoo3 | hull | 420 |
| Hoodoo4 | hull | 452 |
| LanternPost1 | box | 606 |
| MarketGate | precise | 3766 |
| OasisPool1 | precise | 2182 |
| Palm1 | hull | 1828 |
| Palm2 | hull | 1832 |
| Palm3 | hull | 1828 |
| Parapet7 | box | 878 |
| Parapet8 | box | 886 |
| Pots1 | box | 1404 |
| Pots2 | box | 1404 |
| QuestBoard | box | 1826 |
| RelicKiosk | precise | 3332 |
| RopeBridge60 | precise | 4688 |
| RugRack1 | box | 562 |
| Sacks2 | box | 1122 |
| Scrub1 | none | 272 |
| Scrub2 | none | 272 |
| ShadeSail1 | box | 2240 |
| SpawnFountain | precise | 2000 |
| Stall_Plum3 | box | 3174 |
| Stall_Saffron2 | box | 3472 |
| Stall_Teal1 | box | 3318 |
| SunTemple | precise | 15369 |
| TraderPavilion | precise | 3676 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Parapet8 | 66 | 886 | 58,476 | 20% |
| SunTemple | 1 | 15369 | 15,369 | 5% |
| Stall_Teal1 | 4 | 3318 | 13,272 | 5% |
| Palm1 | 7 | 1828 | 12,796 | 4% |
| Stall_Saffron2 | 3 | 3472 | 10,416 | 4% |
| Palm3 | 5 | 1828 | 9,140 | 3% |
| Parapet7 | 8 | 878 | 7,024 | 2% |
| ShadeSail1 | 3 | 2240 | 6,720 | 2% |
| LanternPost1 | 11 | 606 | 6,666 | 2% |
| Stall_Plum3 | 2 | 3174 | 6,348 | 2% |
| Agave1 | 8 | 736 | 5,888 | 2% |
| Palm2 | 3 | 1832 | 5,496 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (2)

- note CarvedStair24_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note CarvedStair24_2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `SunspireBazaarKit`).
2. Insert `SunspireBazaarSetup.lua` as ModuleScript ServerStorage.SunspireBazaarSetup, run `SunspireBazaarKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.SunspireBazaarSetup).Build(game.ServerStorage.SunspireBazaarKit, workspace)`, then `.ApplyLook()`.