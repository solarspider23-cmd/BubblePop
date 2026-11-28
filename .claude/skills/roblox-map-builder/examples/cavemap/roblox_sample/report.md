# GlowrootCaverns - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 63 | reuse: fewer unique meshes = less memory |
| Placed props | 421 (717 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 10 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 434,678 | hard budget 450,000 (--budget) |
| Largest prop | Glowroot (5955 tris) | <= 20000 per MeshPart |
| Footprint | x -212..220, z -230..134 | keep under 2,048 from origin for float precision comfort |
| Palette | GlowrootCaverns_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Barrels2 | box | 1650 |
| BedGlow1 | none | 756 |
| BrewStation | hull | 3284 |
| CampTent | precise | 777 |
| Campfire | box | 1198 |
| CaveFalls | none | 6932 |
| CaveRockA | hull | 968 |
| CaveRockB | hull | 898 |
| CaveRockBLo | hull | 364 |
| CaveRockC | hull | 552 |
| CaveRockCLo | hull | 410 |
| CaveRockD | hull | 396 |
| CaveRockE | hull | 192 |
| CaveRockF | hull | 1478 |
| CaveRockFLo | hull | 380 |
| Crates1 | box | 584 |
| CrystalForge | hull | 3518 |
| CrystalShardsCyan | hull | 462 |
| CrystalSprayCyan | hull | 972 |
| CrystalSprayViolet | hull | 972 |
| DeepLift | hull | 3166 |
| GeodeAmber | hull | 2234 |
| GeodeCyan | hull | 2234 |
| GeodeViolet | hull | 2234 |
| GlowPuddle1 | hull | 204 |
| GlowPuddle2 | hull | 204 |
| GlowShroomCluster2 | hull | 1756 |
| GlowShroomCluster3 | hull | 1690 |
| GlowShroomGiant1 | hull | 2832 |
| GlowShroomGiant1M | hull | 2832 |
| GlowShroomGiant2 | hull | 2832 |
| GlowShroomGiant2M | hull | 2832 |
| GlowVine1 | none | 1058 |
| GlowVine2 | none | 688 |
| GlowVine3 | none | 656 |
| GlowWorms1 | hull | 506 |
| GlowWorms2 | hull | 506 |
| Glowroot | hull | 8861 |
| LogSeat | none | 128 |
| MineCartAmber | hull | 1906 |
| MineCartCyan | hull | 1916 |
| MineFrame | hull | 1070 |
| MineLantern | hull | 622 |
| MineShop | precise | 6310 |
| OrePileCyan | hull | 2262 |
| PlankBridge | precise | 2108 |
| QuestBoard | box | 1204 |
| RailBuffer | hull | 358 |
| RopeBridge | precise | 3448 |
| Scaffold | hull | 4482 |
| ShroomPatch3 | hull | 390 |
| ShroomPatch4 | hull | 390 |
| SkylightLip | hull | 5164 |
| SpawnDais | precise | 2202 |
| Stalactite1 | hull | 532 |
| Stalactite2 | hull | 422 |
| Stalactite3 | hull | 312 |
| StalactiteCurtain1 | hull | 798 |
| StalactiteCurtain2 | hull | 798 |
| Stalagmite1 | hull | 492 |
| Stalagmite2 | hull | 492 |
| Stalagmite3 | hull | 492 |
| ToolRack | hull | 824 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| GeodeCyan | 15 | 2234 | 33,510 | 8% |
| CaveRockD | 56 | 396 | 22,176 | 5% |
| MineFrame | 17 | 1070 | 18,190 | 4% |
| CrystalShardsCyan | 26 | 462 | 12,012 | 3% |
| CrystalSprayCyan | 11 | 972 | 10,692 | 2% |
| GlowShroomCluster2 | 6 | 1756 | 10,536 | 2% |
| GlowShroomCluster3 | 6 | 1690 | 10,140 | 2% |
| MineCartCyan | 5 | 1916 | 9,580 | 2% |
| GlowVine1 | 9 | 1058 | 9,522 | 2% |
| MineLantern | 15 | 622 | 9,330 | 2% |
| OrePileCyan | 4 | 2262 | 9,048 | 2% |
| Stalactite1 | 17 | 532 | 9,044 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (1)

- LogSeat: 3 zero-area faces

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `GlowrootCavernsKit`).
2. Insert `GlowrootCavernsSetup.lua` as ModuleScript ServerStorage.GlowrootCavernsSetup, run `GlowrootCavernsKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.GlowrootCavernsSetup).Build(game.ServerStorage.GlowrootCavernsKit, workspace)`, then `.ApplyLook()`.