# NorthgateWarehouse - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 82 | reuse: fewer unique meshes = less memory |
| Placed props | 404 (559 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 8 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 379,090 | hard budget 450,000 (--budget) |
| Largest prop | TractorGreen (9214 tris) | <= 20000 per MeshPart |
| Footprint | x -120..120, z -80..146 | keep under 2,048 from origin for float precision comfort |
| Palette | NorthgateWarehouse_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Barrier10 | box | 1082 |
| Bollard | box | 168 |
| Charger0 | box | 176 |
| Cone | box | 168 |
| ContainerRed | box | 1530 |
| Conveyor24 | box | 1688 |
| CraneBridge | none | 1508 |
| CraneTrolley | none | 3416 |
| DockDoorClosed | precise | 1438 |
| DockDoorHalf | precise | 1414 |
| DockDoorOpen | precise | 1362 |
| DockStair | precise | 212 |
| FencePanel10 | box | 396 |
| FirePoint | box | 850 |
| Forklift0 | hull | 4338 |
| Forklift0_v001 | hull | 4338 |
| Forklift1 | hull | 4658 |
| HighBay0 | none | 272 |
| IBC0 | box | 588 |
| IBC1 | box | 588 |
| Mezzanine | precise | 3562 |
| PackBench0 | box | 882 |
| PackBench1 | box | 882 |
| PalletCartons10 | box | 592 |
| PalletCartons11 | box | 686 |
| PalletCartons12 | box | 780 |
| PalletCartons30 | box | 732 |
| PalletCartons31 | box | 592 |
| PalletCartons32 | box | 452 |
| PalletCartons33 | box | 498 |
| PalletCrates11 | box | 600 |
| PalletCrates12 | box | 600 |
| PalletDrums1 | box | 1738 |
| PalletDrums20 | box | 1738 |
| PalletJack0 | box | 1112 |
| PalletSacks10 | box | 1512 |
| PalletSacks11 | box | 1512 |
| PalletSacks12 | box | 1512 |
| PalletStack1 | box | 1854 |
| PalletStack2 | box | 1386 |
| PalletStack3 | box | 2322 |
| PalletStack4 | box | 1620 |
| PalletWrapped0 | box | 302 |
| PalletWrapped1 | box | 302 |
| PalletWrapped10 | box | 302 |
| PalletWrapped11 | box | 302 |
| PalletWrapped12 | box | 302 |
| PalletWrapped2 | box | 302 |
| PalletWrapped2_v001 | box | 302 |
| PersonnelDoor | box | 366 |
| PersonnelDoor_v001 | box | 366 |
| RackBayD0 | box | 3092 |
| RackBayD1 | box | 3030 |
| RackBayD2 | box | 3180 |
| RackBayD3 | box | 2760 |
| RackBayD4 | box | 2864 |
| RackBayS10 | box | 1434 |
| RackBayS11 | box | 1158 |
| RackBayS11_v001 | box | 1158 |
| RackBayS12 | box | 1272 |
| RackBayS12_v001 | box | 1272 |
| RackEndD | box | 818 |
| RackEndS | box | 528 |
| RackGuardD | box | 262 |
| RoofTruss | none | 996 |
| RunwayBeam30 | none | 68 |
| SiteOffice | precise | 2762 |
| SkylightN | none | 108 |
| SkylightS | none | 108 |
| SteelColumn | box | 270 |
| SteelColumnBG | box | 376 |
| SteelColumnBGN | box | 352 |
| Stillage0 | box | 1244 |
| Stillage1 | box | 1244 |
| StretchWrapper | box | 1148 |
| TractorGreen | hull | 9274 |
| TrailerClosed | precise | 7962 |
| TrailerOpen | precise | 8366 |
| WheelChock | none | 34 |
| YardBin0 | box | 414 |
| YardBin1 | box | 414 |
| YardLight | box | 474 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| RackBayD0 | 10 | 3092 | 30,920 | 8% |
| RackBayD1 | 10 | 3030 | 30,300 | 8% |
| RackBayD2 | 9 | 3180 | 28,620 | 8% |
| RackBayD3 | 10 | 2760 | 27,600 | 7% |
| RackBayD4 | 9 | 2864 | 25,776 | 7% |
| HighBay0 | 84 | 272 | 22,848 | 6% |
| TractorGreen | 2 | 9274 | 18,548 | 5% |
| TrailerOpen | 2 | 8366 | 16,732 | 4% |
| FencePanel10 | 38 | 396 | 15,048 | 4% |
| Forklift0_v001 | 2 | 4338 | 8,676 | 2% |
| RoofTruss | 8 | 996 | 7,968 | 2% |
| TrailerClosed | 1 | 7962 | 7,962 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (4)

- Charger0: lowest point y=1.27 above its origin (floats when placed)
- note DockStair: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- FirePoint: lowest point y=0.80 above its origin (floats when placed)
- RoofTruss: lowest point y=31.70 above its origin (floats when placed)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `NorthgateWarehouseKit`).
2. Insert `NorthgateWarehouseSetup.lua` as ModuleScript ServerStorage.NorthgateWarehouseSetup, run `NorthgateWarehouseKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.NorthgateWarehouseSetup).Build(game.ServerStorage.NorthgateWarehouseKit, workspace)`, then `.ApplyLook()`.