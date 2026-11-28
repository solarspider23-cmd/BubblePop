# Puffpaw - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 83 | reuse: fewer unique meshes = less memory |
| Placed props | 568 (658 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 11 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 4 | sea / skirt planes |
| Total placed tris | 419,987 | hard budget 450,000 (--budget) |
| Largest prop | PetFountain (16108 tris) | <= 20000 per MeshPart |
| Footprint | x -280..528, z -573..347 | keep under 2,048 from origin for float precision comfort |
| Palette | Puffpaw_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Bench_pink | box | 700 |
| Bridge_1 | precise | 7608 |
| Bridge_2 | precise | 6416 |
| Bridge_3 | precise | 9528 |
| CandyCane1 | box | 556 |
| Chest_T2 | box | 198 |
| Chest_T3 | box | 234 |
| Cloud1 | none | 910 |
| Cloud2 | none | 1092 |
| Cloud3 | none | 728 |
| Cloud4 | none | 910 |
| CoinPile_L | hull | 280 |
| CoinPile_S | hull | 216 |
| CottonTree1 | hull | 1540 |
| CottonTree2 | hull | 1540 |
| CottonTree3 | hull | 1540 |
| CrystalClump_T2 | hull | 160 |
| CrystalClump_T3 | hull | 184 |
| CrystalSpire1 | precise | 292 |
| CrystalSpire2 | precise | 316 |
| CrystalSpire3 | precise | 268 |
| CrystalTree1sky | hull | 1266 |
| CrystalTree2pink | hull | 1266 |
| CrystalTree4sky | hull | 1266 |
| EggStand_basic | precise | 3122 |
| EggStand_candy | precise | 2318 |
| EggStand_crystal | precise | 2510 |
| EggStand_golden | precise | 3054 |
| EggStand_meadow | precise | 5366 |
| EggStand_spotted | precise | 3122 |
| Fence_candy | box | 280 |
| Fence_crystal | box | 280 |
| Fence_hub | box | 280 |
| Fence_meadow | box | 280 |
| FlowerPatch1 | none | 496 |
| FlowerPatch2 | none | 496 |
| FlowerPatch3 | none | 496 |
| FlowerPatch4 | none | 496 |
| FlowerPatch5 | none | 620 |
| GiftBox_lilac | box | 240 |
| GiftBox_pink | box | 240 |
| GiftBox_sky | box | 240 |
| GlowShroom1 | hull | 504 |
| GrassTuft1 | none | 192 |
| Gumdrops1 | hull | 512 |
| Gumdrops2 | hull | 384 |
| LampPost_hub | box | 592 |
| LeaderboardFrame | precise | 2360 |
| Lollipop1 | box | 1324 |
| Lollipop2 | box | 1324 |
| Lollipop3 | box | 1324 |
| Mushroom_orange2 | hull | 504 |
| Mushroom_red1 | hull | 504 |
| PetFountain | precise | 16108 |
| PetShop | precise | 6810 |
| PetStatue | precise | 6808 |
| PuffBush_leaf1 | none | 774 |
| PuffBush_leaf2 | none | 594 |
| PuffBush_leaf3 | none | 774 |
| PuffBush_mint5 | none | 774 |
| PuffBush_pink4 | none | 594 |
| PuffBush_pink6 | none | 594 |
| PuffBush_sky7 | none | 774 |
| PuffTree_green1 | hull | 1216 |
| PuffTree_green3 | hull | 1216 |
| PuffTree_green7 | hull | 1216 |
| PuffTree_pink5 | hull | 1216 |
| RainbowArch | precise | 8296 |
| SeaRock1 | hull | 456 |
| SeaRock2 | hull | 456 |
| SoftRock_stone1 | hull | 288 |
| SoftRock_stone2 | hull | 288 |
| SoftRock_stone3 | hull | 288 |
| SpawnPad | precise | 1888 |
| StarLamp1 | box | 316 |
| Stump1 | hull | 530 |
| TradeBooth_pink | precise | 1534 |
| TradeBooth_sky | precise | 1534 |
| TradePad | none | 1420 |
| UpgradeMachine | precise | 8512 |
| ZoneGate_candy | precise | 5704 |
| ZoneGate_crystal | precise | 5704 |
| ZoneGate_meadow | precise | 5704 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| PuffTree_green1 | 17 | 1216 | 20,672 | 5% |
| PetFountain | 1 | 16108 | 16,108 | 4% |
| CrystalTree2pink | 9 | 1266 | 11,394 | 3% |
| Fence_hub | 37 | 280 | 10,360 | 2% |
| Bridge_3 | 1 | 9528 | 9,528 | 2% |
| PuffBush_leaf1 | 12 | 774 | 9,288 | 2% |
| CottonTree3 | 6 | 1540 | 9,240 | 2% |
| Fence_meadow | 32 | 280 | 8,960 | 2% |
| Fence_crystal | 32 | 280 | 8,960 | 2% |
| FlowerPatch2 | 18 | 496 | 8,928 | 2% |
| UpgradeMachine | 1 | 8512 | 8,512 | 2% |
| RainbowArch | 1 | 8296 | 8,296 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (8)

- note Bridge_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bridge_3: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence_candy: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence_crystal: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence_hub: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence_meadow: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- PetStatue: lowest point y=15.08 above its origin (floats when placed)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `PuffpawKit`).
2. Insert `PuffpawSetup.lua` as ModuleScript ServerStorage.PuffpawSetup, run `PuffpawKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.PuffpawSetup).Build(game.ServerStorage.PuffpawKit, workspace)`, then `.ApplyLook()`.