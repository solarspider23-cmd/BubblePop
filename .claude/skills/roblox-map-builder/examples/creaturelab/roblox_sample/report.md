# Bloomcrest - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 84 | reuse: fewer unique meshes = less memory |
| Placed props | 239 (321 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 8 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 445,998 | hard budget 450,000 (--budget) |
| Largest prop | Rotunda (16690 tris) | <= 20000 per MeshPart |
| Footprint | x -537..601, z -564..640 | keep under 2,048 from origin for float precision comfort |
| Palette | Bloomcrest_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| BerryBaskets | box | 3194 |
| Bollard | box | 154 |
| CapsuleFountain | precise | 4488 |
| CapsuleShelf1 | box | 9134 |
| Cloud1 | none | 448 |
| Cloud2 | none | 444 |
| Cloud3 | none | 422 |
| DisplayRack | box | 8572 |
| DockCables | none | 910 |
| DrinkCooler | box | 512 |
| EntranceCanopy | precise | 2176 |
| EntryMat | none | 532 |
| EvoChamber | precise | 9142 |
| FiddleFig1 | hull | 4396 |
| FiddleFig2 | hull | 5064 |
| FlowerBed1 | none | 1212 |
| FlowerBed2 | none | 1212 |
| FlowerBed3 | none | 1212 |
| GardenWall14 | box | 222 |
| HallCeiling | none | 3712 |
| HallTrim | none | 4712 |
| HangingArt1 | none | 216 |
| HangingArt2 | none | 216 |
| HangingArt3 | none | 216 |
| HangingClock | none | 432 |
| HangingPotC | none | 1534 |
| HealCorner | none | 2054 |
| HealCounter | precise | 2900 |
| HealMachine | box | 7490 |
| LabArchway | precise | 1848 |
| LabShelf | box | 3654 |
| LabWing | precise | 3880 |
| LampPost | box | 804 |
| LilyPads1 | none | 504 |
| LilyPads2 | none | 504 |
| LongPlanter12 | box | 1220 |
| MedShelf1 | box | 4516 |
| MicroscopeBench | box | 1102 |
| Monstera1 | box | 1732 |
| Monstera2 | box | 1732 |
| OliveTree2 | hull | 4660 |
| PCTerminal | box | 2034 |
| ParkBench | box | 1052 |
| ParkTree1 | hull | 3668 |
| ParkTree2 | hull | 3104 |
| ParkTree3 | hull | 3768 |
| PendantLampM | none | 380 |
| PendantLampT | none | 380 |
| PinkParkTree4 | hull | 3206 |
| PlushCoral | none | 592 |
| PlushMint | none | 592 |
| PotionShelf2 | box | 5464 |
| Reeds1 | none | 144 |
| RestNook | precise | 1758 |
| RopeLine4 | box | 782 |
| Rotunda | precise | 16762 |
| RoundBush1b | none | 1004 |
| RoundBush2g | none | 1004 |
| RoundPlanter2 | box | 2288 |
| RoundRugM | none | 778 |
| RoundRugT | none | 778 |
| SaleStand | box | 2020 |
| ShopCounter | box | 4428 |
| SlidingDoors | none | 1232 |
| SnakePlant1 | box | 736 |
| SnakePlant2 | box | 736 |
| SnakePlant3 | box | 736 |
| SpecimenTankA | box | 2572 |
| SpecimenTankB | box | 2572 |
| StarterTable | precise | 6436 |
| SteppingStone | precise | 70 |
| SupplyBoxes1 | box | 2968 |
| Topiary8 | box | 584 |
| TradeDesk | precise | 4758 |
| TrophyShelf | box | 2808 |
| VendingMachineC | box | 2364 |
| VendingMachineS | box | 2364 |
| WaitBenchT | box | 816 |
| WallCapsules | none | 3826 |
| WelcomeSign | box | 3246 |
| Whiteboard | box | 1652 |
| WingRoof | none | 4636 |
| WingTrim | none | 1104 |
| Workbench1 | box | 2052 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| ParkTree3 | 6 | 3768 | 22,608 | 5% |
| ParkTree1 | 5 | 3668 | 18,340 | 4% |
| CapsuleShelf1 | 2 | 9134 | 18,268 | 4% |
| Rotunda | 1 | 16762 | 16,762 | 4% |
| FlowerBed1 | 9 | 1212 | 10,908 | 2% |
| FiddleFig2 | 2 | 5064 | 10,128 | 2% |
| GardenWall14 | 45 | 222 | 9,990 | 2% |
| OliveTree2 | 2 | 4660 | 9,320 | 2% |
| EvoChamber | 1 | 9142 | 9,142 | 2% |
| MedShelf1 | 2 | 4516 | 9,032 | 2% |
| CapsuleFountain | 2 | 4488 | 8,976 | 2% |
| DisplayRack | 1 | 8572 | 8,572 | 2% |

## Over-detailed for their size (> 600 tris per stud; players do not see that detail)

- CapsuleShelf1: 9134 tris for 12.0 studs
- DisplayRack: 8572 tris for 8.5 studs
- WallCapsules: 3826 tris for 6.3 studs

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (9)

- note EntranceCanopy: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- HallCeiling: lowest point y=21.73 above its origin (floats when placed)
- HallTrim: lowest point y=0.95 above its origin (floats when placed)
- note LabWing: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- TrophyShelf: lowest point y=3.00 above its origin (floats when placed)
- WingRoof: lowest point y=19.70 above its origin (floats when placed)
- note WingRoof: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- WingTrim: lowest point y=4.03 above its origin (floats when placed)
- note WingTrim: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `BloomcrestKit`).
2. Insert `BloomcrestSetup.lua` as ModuleScript ServerStorage.BloomcrestSetup, run `BloomcrestKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.BloomcrestSetup).Build(game.ServerStorage.BloomcrestKit, workspace)`, then `.ApplyLook()`.