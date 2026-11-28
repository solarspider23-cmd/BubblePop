# Eggstead - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 143 | reuse: fewer unique meshes = less memory |
| Placed props | 1158 (1292 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 5 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 396,553 | hard budget 450,000 (--budget) |
| Largest prop | EggHatchery (4978 tris) | <= 20000 per MeshPart |
| Footprint | x -540..539, z -618..620 | keep under 2,048 from origin for float precision comfort |
| Palette | Eggstead_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| BarnBackdrop | precise | 890 |
| Boulder1 | hull | 38 |
| Boulder2 | hull | 30 |
| Boulder3 | hull | 34 |
| Bush1 | none | 282 |
| Bush2 | none | 286 |
| Bush3 | none | 226 |
| Cloud1 | none | 152 |
| Cloud2 | none | 142 |
| Cloud3 | none | 144 |
| CollectPad_blue | none | 780 |
| CollectPad_orange | none | 780 |
| CollectPad_pink | none | 780 |
| CollectPad_purple | none | 780 |
| CollectPad_red | none | 780 |
| CollectPad_sky | none | 780 |
| CollectPad_teal | none | 780 |
| CollectPad_yellow | none | 780 |
| ConveyorCap | box | 126 |
| ConveyorSeg | box | 1096 |
| Coop_blue | precise | 3704 |
| Coop_orange | precise | 3704 |
| Coop_pink | precise | 3704 |
| Coop_purple | precise | 3704 |
| Coop_red | precise | 3704 |
| Coop_sky | precise | 3704 |
| Coop_teal | precise | 3704 |
| Coop_yellow | precise | 3704 |
| EggBridge | precise | 2504 |
| EggDrain | precise | 1714 |
| EggHatchery | precise | 5597 |
| EggLamp | box | 328 |
| EggShop | precise | 2570 |
| FeedTrough | box | 756 |
| Fence4e_blue | box | 128 |
| Fence4e_orange | box | 128 |
| Fence4e_pink | box | 128 |
| Fence4e_purple | box | 128 |
| Fence4e_red | box | 128 |
| Fence4e_sky | box | 128 |
| Fence4e_teal | box | 128 |
| Fence4e_yellow | box | 128 |
| Fence4s_blue | box | 40 |
| Fence4s_orange | box | 40 |
| Fence4s_pink | box | 40 |
| Fence4s_purple | box | 40 |
| Fence4s_red | box | 40 |
| Fence4s_sky | box | 40 |
| Fence4s_teal | box | 40 |
| Fence4s_yellow | box | 40 |
| Fence8_blue | box | 192 |
| Fence8_orange | box | 192 |
| Fence8_pink | box | 192 |
| Fence8_purple | box | 192 |
| Fence8_red | box | 192 |
| Fence8_sky | box | 192 |
| Fence8_teal | box | 192 |
| Fence8_yellow | box | 192 |
| Fence8c_blue | box | 104 |
| Fence8c_orange | box | 104 |
| Fence8c_pink | box | 104 |
| Fence8c_purple | box | 104 |
| Fence8c_red | box | 104 |
| Fence8c_sky | box | 104 |
| Fence8c_teal | box | 104 |
| Fence8c_yellow | box | 104 |
| FencePost_blue | box | 332 |
| FencePost_orange | box | 332 |
| FencePost_pink | box | 332 |
| FencePost_purple | box | 332 |
| FencePost_red | box | 332 |
| FencePost_sky | box | 332 |
| FencePost_teal | box | 332 |
| FencePost_yellow | box | 332 |
| FlowerPatch1 | none | 206 |
| FlowerPatch2 | none | 206 |
| FlowerPatch3 | none | 206 |
| FlowerTub2 | box | 438 |
| FlowerTub3 | box | 438 |
| FlowerTub4 | box | 438 |
| FlowerTub5 | box | 438 |
| FlowerTub6 | box | 438 |
| GateFrame_blue | precise | 1960 |
| GateFrame_orange | precise | 1960 |
| GateFrame_pink | precise | 1960 |
| GateFrame_purple | precise | 1960 |
| GateFrame_red | precise | 1960 |
| GateFrame_sky | precise | 1960 |
| GateFrame_teal | precise | 1960 |
| GateFrame_yellow | precise | 1960 |
| GateMat_blue | none | 140 |
| GateMat_orange | none | 140 |
| GateMat_pink | none | 140 |
| GateMat_purple | none | 140 |
| GateMat_red | none | 140 |
| GateMat_sky | none | 140 |
| GateMat_teal | none | 140 |
| GateMat_yellow | none | 140 |
| GiantEgg0 | box | 636 |
| GiantEgg1 | box | 636 |
| GiantEgg2 | box | 636 |
| GiantEgg3 | box | 636 |
| HayStack | box | 456 |
| LilyPads1 | none | 124 |
| LilyPads2 | none | 124 |
| NestPedestal_blue | box | 572 |
| NestPedestal_orange | box | 572 |
| NestPedestal_pink | box | 572 |
| NestPedestal_purple | box | 572 |
| NestPedestal_red | box | 572 |
| NestPedestal_sky | box | 572 |
| NestPedestal_teal | box | 572 |
| NestPedestal_yellow | box | 572 |
| NestStatue | box | 1020 |
| OwnerSign_blue | box | 648 |
| OwnerSign_orange | box | 648 |
| OwnerSign_pink | box | 648 |
| OwnerSign_purple | box | 648 |
| OwnerSign_red | box | 648 |
| OwnerSign_sky | box | 648 |
| OwnerSign_teal | box | 648 |
| OwnerSign_yellow | box | 648 |
| ParkBench | box | 396 |
| Pine1 | hull | 94 |
| Pine2 | hull | 94 |
| PlotYard_blue | box | 1468 |
| PlotYard_orange | box | 1468 |
| PlotYard_pink | box | 1468 |
| PlotYard_purple | box | 1468 |
| PlotYard_red | box | 1468 |
| PlotYard_sky | box | 1468 |
| PlotYard_teal | box | 1468 |
| PlotYard_yellow | box | 1468 |
| RanchFence | box | 194 |
| Reeds1 | none | 138 |
| Reeds2 | none | 138 |
| SellStand | precise | 2072 |
| SiloBackdrop | box | 340 |
| Tree1 | hull | 308 |
| Tree2 | hull | 324 |
| Tree3 | hull | 334 |
| UpgradeStand | precise | 1998 |
| Windmill | precise | 1558 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Tree2 | 90 | 324 | 29,160 | 7% |
| Tree1 | 76 | 308 | 23,408 | 6% |
| ConveyorSeg | 17 | 1096 | 18,632 | 5% |
| Pine1 | 163 | 94 | 15,322 | 4% |
| RanchFence | 72 | 194 | 13,968 | 4% |
| EggBridge | 3 | 2504 | 7,512 | 2% |
| Pine2 | 65 | 94 | 6,110 | 2% |
| FeedTrough | 8 | 756 | 6,048 | 2% |
| NestPedestal_red | 10 | 572 | 5,720 | 1% |
| NestPedestal_yellow | 10 | 572 | 5,720 | 1% |
| NestPedestal_sky | 10 | 572 | 5,720 | 1% |
| NestPedestal_purple | 10 | 572 | 5,720 | 1% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (18)

- note ConveyorSeg: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_blue: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_orange: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_pink: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_purple: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_red: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_sky: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_teal: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8_yellow: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_blue: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_orange: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_pink: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_purple: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_red: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_sky: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_teal: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Fence8c_yellow: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note RanchFence: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `EggsteadKit`).
2. Insert `EggsteadSetup.lua` as ModuleScript ServerStorage.EggsteadSetup, run `EggsteadKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.EggsteadSetup).Build(game.ServerStorage.EggsteadKit, workspace)`, then `.ApplyLook()`.