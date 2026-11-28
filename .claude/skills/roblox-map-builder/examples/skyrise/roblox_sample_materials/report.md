# Skyrise - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 118 | reuse: fewer unique meshes = less memory |
| Placed props | 1366 (1729 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 11 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 612,974 | phone view budget ~300-600k visible |
| Largest prop | Bridge_wood_116_21 (11488 tris) | <= 20000 per MeshPart |
| Footprint | x -1170..1194, z -1402..560 | keep under 2,048 from origin for float precision comfort |
| Palette | Skyrise_Palette.png | <= 1024 px |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| AshPile0 | none | 40 |
| AshPile1 | none | 40 |
| AshPile2 | none | 40 |
| Basalt0 | hull | 612 |
| Basalt1 | hull | 500 |
| Basalt2 | hull | 444 |
| Bridge_stone_102_27 | precise | 8668 |
| Bridge_stone_118_24 | precise | 10140 |
| Bridge_stone_95_44 | precise | 9092 |
| Bridge_wood_116_21 | precise | 11752 |
| Bridge_wood_74_14 | precise | 7804 |
| Bush0_leaf | hull | 880 |
| Bush1_pink | hull | 800 |
| Cactus0 | hull | 1228 |
| Cactus1 | hull | 1228 |
| Cactus2 | hull | 1228 |
| Charred0 | hull | 356 |
| Charred1 | hull | 356 |
| Chest1 | hull | 1574 |
| Chest2 | hull | 1574 |
| Chest3 | hull | 1574 |
| Chest4 | hull | 1574 |
| Cloud0 | none | 800 |
| Cloud1 | none | 600 |
| Cloud2 | none | 500 |
| Cloud3 | none | 600 |
| CoinPile0 | hull | 1496 |
| CoinPile1 | hull | 1496 |
| CoinPile2 | hull | 1496 |
| Crystal0_crystal | hull | 460 |
| Crystal1_crystal | hull | 386 |
| Crystal20_crystal | hull | 352 |
| Crystal21_gem | hull | 458 |
| Crystal2_crystal | hull | 460 |
| Crystal5_gem | hull | 458 |
| Crystal6_gem | hull | 354 |
| Crystal7_gem | hull | 392 |
| DryShrub0 | none | 216 |
| DryShrub1 | none | 216 |
| EggShrine | hull | 5788 |
| EmberRocks0 | none | 48 |
| EmberRocks1 | none | 48 |
| EmberRocks2 | none | 48 |
| FlowerBed0 | none | 1664 |
| FlowerBed1 | none | 1664 |
| Flowers0 | none | 196 |
| Flowers1 | none | 196 |
| Flowers2 | none | 196 |
| IceShards0 | none | 60 |
| IceShards1 | none | 60 |
| IceShards2 | none | 60 |
| IceSpike0 | hull | 80 |
| IceSpike1 | hull | 60 |
| IslandUnder1 | hull | 6370 |
| IslandUnder2 | hull | 7042 |
| IslandUnder3 | hull | 7010 |
| IslandUnder4 | hull | 6926 |
| IslandUnder5 | hull | 6996 |
| IslandUnder6 | hull | 5614 |
| LavaCrack0 | none | 144 |
| LavaCrack1 | none | 144 |
| LavaCrack2 | none | 144 |
| LavaPool0 | hull | 450 |
| LavaPool1 | hull | 450 |
| Leaderboard | hull | 1684 |
| Mesa0 | hull | 338 |
| Mesa1 | hull | 326 |
| Mushrooms0 | none | 312 |
| Mushrooms1 | none | 208 |
| PathStone0 | none | 38 |
| PathStone1 | none | 38 |
| PathStone2 | none | 38 |
| Pebbles0_stone | none | 40 |
| Pebbles10_sand | none | 40 |
| Pebbles11_sand | none | 40 |
| Pebbles1_stone | none | 40 |
| PlazaFountain | precise | 2076 |
| Puffy0_leaf | hull | 1784 |
| Puffy1_pink | hull | 1606 |
| Puffy20_leaf_b | hull | 4160 |
| Puffy21_leaf_b | hull | 3718 |
| Puffy2_leaf | hull | 1784 |
| Puffy3_pink | hull | 1784 |
| SellPad | box | 3714 |
| Sign1 | box | 418 |
| Sign2 | box | 418 |
| Sign3 | box | 418 |
| Sign4 | box | 418 |
| SkyLamp | box | 416 |
| SkyRock0 | hull | 248 |
| SkyRock1 | hull | 62 |
| SkyRock2 | hull | 244 |
| SkyRock3 | hull | 56 |
| SnowMound0 | none | 60 |
| SnowMound1 | none | 40 |
| SnowMound2 | none | 40 |
| SnowTree0 | hull | 332 |
| SnowTree1 | hull | 332 |
| SnowTree2 | hull | 332 |
| SpawnPad | box | 586 |
| Teleport_z1 | hull | 1838 |
| Teleport_z2 | hull | 1838 |
| Teleport_z3 | hull | 1838 |
| Teleport_z4 | hull | 1838 |
| Teleport_z5 | hull | 1838 |
| Trophy | hull | 8310 |
| Tuft0_grass | none | 36 |
| Tuft1_grass | none | 36 |
| Tuft2_grass | none | 36 |
| Tuft50_sand | none | 32 |
| Tuft51_sand | none | 32 |
| Tuft52_sand | none | 32 |
| UpgradeStand | hull | 4282 |
| ZoneGate1 | precise | 2528 |
| ZoneGate2 | precise | 2528 |
| ZoneGate3 | precise | 2528 |
| ZoneGate4 | precise | 2528 |
| ZoneGate5 | precise | 2528 |

## Warnings (8)

- note Bridge_stone_102_27: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_stone_118_24: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_stone_95_44: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_wood_116_21: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_wood_74_14: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LavaCrack0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LavaCrack1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LavaCrack2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `SkyriseKit`).
2. Insert `SkyriseSetup.lua` as ModuleScript ServerStorage.SkyriseSetup, run `SkyriseKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.SkyriseSetup).Build(game.ServerStorage.SkyriseKit, workspace)`, then `.ApplyLook()`.