# MapleJunction - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 76 | reuse: fewer unique meshes = less memory |
| Placed props | 419 (496 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 6 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 439,275 | hard budget 450,000 (--budget) |
| Largest prop | TownHall (11031 tris) | <= 20000 per MeshPart |
| Footprint | x -262..400, z -258..286 | keep under 2,048 from origin for float precision comfort |
| Palette | MapleJunction_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| B_Boutique | precise | 4419 |
| B_BrickCorner | precise | 5447 |
| B_BrickCornerL | precise | 4195 |
| B_BrickSmall | precise | 2595 |
| B_BrickSmallL | precise | 2136 |
| B_BrickTallFSL | precise | 6656 |
| B_BrickTallS | precise | 4940 |
| B_BrickTallSL | precise | 4432 |
| B_Cafe | precise | 3448 |
| B_CafeF | precise | 4184 |
| B_CafeL | precise | 2068 |
| B_CreamOfficeS | precise | 5928 |
| B_CreamOfficeSL | precise | 5164 |
| B_SageHouse | precise | 2816 |
| B_SageHouseFL | precise | 2408 |
| B_SageHouseL | precise | 1696 |
| B_SageShopF | precise | 5078 |
| B_SageShopL | precise | 2302 |
| B_ShopRed | precise | 4088 |
| B_ShopRedF | precise | 5250 |
| B_ShopTeal | precise | 4489 |
| B_ShopTealF | precise | 5687 |
| B_ShopYellowFSL | precise | 5918 |
| B_ShopYellowS | precise | 5110 |
| B_ShopYellowSL | precise | 4114 |
| B_SlateAptFL | precise | 4560 |
| B_SlateAptL | precise | 3004 |
| Bank | precise | 3612 |
| Bench | box | 228 |
| Bin | box | 382 |
| BusStop | precise | 360 |
| CarShowroom | precise | 1542 |
| Car_hatch_red | box | 764 |
| Car_hatch_teal | box | 764 |
| Car_hatch_yellow | box | 764 |
| Car_sedan_blue | box | 764 |
| Car_sedan_cream | box | 798 |
| Car_sedan_red | box | 764 |
| Car_sedan_teal | box | 764 |
| Car_taxi | box | 880 |
| Car_van_cream | box | 860 |
| CityBus | box | 1430 |
| ClockTower | precise | 6612 |
| Dumpster_blue | box | 348 |
| Dumpster_teal | box | 348 |
| FlowerBed1 | none | 464 |
| Fountain | precise | 2028 |
| Hedge1 | box | 128 |
| Hydrant | box | 394 |
| JobBoard | box | 912 |
| Pallets | box | 300 |
| Planter1 | box | 412 |
| Planter2 | box | 414 |
| PlatformCanopy | precise | 684 |
| SkyA | box | 638 |
| SkyB | box | 862 |
| SkyC | box | 246 |
| SkyD | box | 722 |
| SkyE | box | 622 |
| StreetGrate | hull | 260 |
| StreetLamp | box | 385 |
| TownHall | precise | 11031 |
| TrackSeg | box | 224 |
| TrafficLight_green | box | 784 |
| TrafficLight_red | box | 784 |
| TrainStation | precise | 6873 |
| Train_carriage | box | 1592 |
| Train_loco | box | 1656 |
| TrashBags | none | 132 |
| TreeStreetBirch_Branches | none | 152 |
| TreeStreetBirch_Leaves | none | 676 |
| TreeStreetBirch_Trunk | hull | 820 |
| TreeStreetOak_Branches | none | 216 |
| TreeStreetOak_Leaves | none | 992 |
| TreeStreetOak_Trunk | hull | 810 |
| WallPipes | box | 404 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| B_SlateAptL | 7 | 3004 | 21,028 | 5% |
| StreetLamp | 48 | 385 | 18,480 | 4% |
| B_BrickTallSL | 4 | 4432 | 17,728 | 4% |
| B_BrickCorner | 3 | 5447 | 16,341 | 4% |
| B_ShopRed | 3 | 4088 | 12,264 | 3% |
| B_CreamOfficeS | 2 | 5928 | 11,856 | 3% |
| TreeStreetBirch_Trunk | 14 | 820 | 11,480 | 3% |
| B_SageHouse | 4 | 2816 | 11,264 | 3% |
| TownHall | 1 | 11031 | 11,031 | 3% |
| TreeStreetOak_Leaves | 11 | 992 | 10,912 | 2% |
| B_BrickSmallL | 5 | 2136 | 10,680 | 2% |
| B_ShopYellowS | 2 | 5110 | 10,220 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (3)

- note TrafficLight_green: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note TrafficLight_red: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- Train_loco: 4 zero-area faces

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `MapleJunctionKit`).
2. Insert `MapleJunctionSetup.lua` as ModuleScript ServerStorage.MapleJunctionSetup, run `MapleJunctionKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.MapleJunctionSetup).Build(game.ServerStorage.MapleJunctionKit, workspace)`, then `.ApplyLook()`.