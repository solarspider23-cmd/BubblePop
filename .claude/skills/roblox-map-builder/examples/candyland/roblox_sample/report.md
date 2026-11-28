# SugarcrestKingdom - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 52 | reuse: fewer unique meshes = less memory |
| Placed props | 259 (281 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 11 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 440,172 | hard budget 450,000 (--budget) |
| Largest prop | CandyCastle (19021 tris) | <= 20000 per MeshPart |
| Footprint | x -335..335, z -340..330 | keep under 2,048 from origin for float precision comfort |
| Palette | SugarcrestKingdom_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| BakeryOven | precise | 8192 |
| BiscuitBridge | precise | 10168 |
| CandyCane0 | box | 628 |
| CandyCane1 | box | 628 |
| CandyCane2 | box | 628 |
| CandyCane3 | box | 628 |
| CandyCastle | precise | 20253 |
| CandyFlower0 | none | 984 |
| CandyFlower1 | none | 738 |
| CandyFlower2 | none | 738 |
| CandyLamp | box | 1000 |
| ChocoFalls | none | 476 |
| ChocoMountain | precise | 3101 |
| ChocoPool | none | 2032 |
| CottonCandyTree0 | hull | 2190 |
| CottonCandyTree1 | hull | 2190 |
| CottonCandyTree2 | hull | 2190 |
| CottonCandyTree3 | hull | 2190 |
| CupcakeFountain | precise | 11242 |
| DonutArch0 | precise | 3068 |
| DonutArch1 | precise | 3076 |
| DonutArch2 | precise | 3108 |
| Drawbridge | precise | 1688 |
| EggMachine | precise | 6846 |
| GiantCone0 | hull | 852 |
| GiantCone1 | hull | 852 |
| GiantCone2 | hull | 852 |
| GiantCone3 | hull | 852 |
| GumballMachine | precise | 10199 |
| GumdropBush0 | none | 672 |
| GumdropBush1 | none | 504 |
| GumdropBush2 | none | 504 |
| GumdropBush3 | none | 504 |
| GumdropMountain0 | hull | 1432 |
| GumdropMountain1 | hull | 1552 |
| GumdropMountain2 | hull | 1612 |
| GumdropMountain3 | hull | 1432 |
| GumdropMountain4 | hull | 1552 |
| GumdropMountain5 | hull | 1612 |
| JellyBeans0 | hull | 948 |
| JellyBeans1 | hull | 790 |
| JellyBeans2 | hull | 790 |
| LollipopTree0 | hull | 1286 |
| LollipopTree1 | hull | 1286 |
| LollipopTree2 | hull | 1286 |
| LollipopTree3 | hull | 1286 |
| Marshmallow0 | box | 288 |
| Marshmallow1 | box | 288 |
| QuestStand | precise | 3916 |
| SpawnCookie | none | 2116 |
| SweetShop | precise | 11457 |
| WaffleBridge | precise | 6432 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| CandyCastle | 1 | 20253 | 20,253 | 5% |
| CandyLamp | 17 | 1000 | 17,000 | 4% |
| JellyBeans0 | 15 | 948 | 14,220 | 3% |
| CottonCandyTree0 | 6 | 2190 | 13,140 | 3% |
| CottonCandyTree1 | 6 | 2190 | 13,140 | 3% |
| CottonCandyTree2 | 6 | 2190 | 13,140 | 3% |
| CottonCandyTree3 | 6 | 2190 | 13,140 | 3% |
| SweetShop | 1 | 11457 | 11,457 | 3% |
| CupcakeFountain | 1 | 11242 | 11,242 | 3% |
| GumballMachine | 1 | 10199 | 10,199 | 2% |
| BiscuitBridge | 1 | 10168 | 10,168 | 2% |
| CandyFlower0 | 10 | 984 | 9,840 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (3)

- note ChocoFalls: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note ChocoPool: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Drawbridge: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `SugarcrestKingdomKit`).
2. Insert `SugarcrestKingdomSetup.lua` as ModuleScript ServerStorage.SugarcrestKingdomSetup, run `SugarcrestKingdomKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.SugarcrestKingdomSetup).Build(game.ServerStorage.SugarcrestKingdomKit, workspace)`, then `.ApplyLook()`.