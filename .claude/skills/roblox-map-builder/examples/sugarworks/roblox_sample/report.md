# Sugarworks - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 63 | reuse: fewer unique meshes = less memory |
| Placed props | 856 (1163 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 5 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 8 | sea / skirt planes |
| Total placed tris | 329,060 | hard budget 450,000 (--budget) |
| Largest prop | Exchange (12267 tris) | <= 20000 per MeshPart |
| Footprint | x -215..217, z -396..327 | keep under 2,048 from origin for float precision comfort |
| Palette | Sugarworks_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| BuyButton | box | 704 |
| CandyCorn0 | hull | 240 |
| CandyCorn1 | hull | 180 |
| CandyCorn2 | hull | 180 |
| CandyCrate0 | box | 144 |
| CandyCrate1 | box | 144 |
| CandyCrate2 | box | 144 |
| CandyLamp | box | 522 |
| CashPad | box | 900 |
| ChocBench | box | 464 |
| ChocFountain | precise | 2164 |
| Cliff0 | precise | 38 |
| Cliff1 | precise | 46 |
| Cliff2 | precise | 38 |
| CoinChute | hull | 396 |
| Collector1 | hull | 1092 |
| Conveyor | hull | 1256 |
| Dropper1 | hull | 760 |
| Exchange | precise | 13158 |
| Fence12_t0 | box | 112 |
| Fence12_t1 | box | 112 |
| Fence12_t2 | box | 112 |
| Fence12_t3 | box | 112 |
| Fence12_t4 | box | 112 |
| Fence12_t5 | box | 112 |
| Fence12_t6 | box | 112 |
| Fence12_t7 | box | 112 |
| Fence8_t0 | box | 112 |
| Fence8_t1 | box | 112 |
| Fence8_t2 | box | 112 |
| Fence8_t3 | box | 112 |
| Fence8_t4 | box | 112 |
| Fence8_t5 | box | 112 |
| Fence8_t6 | box | 112 |
| Fence8_t7 | box | 112 |
| FencePost | box | 66 |
| Gate_t0 | precise | 1204 |
| Gate_t1 | precise | 1204 |
| Gate_t2 | precise | 1204 |
| Gate_t3 | precise | 1204 |
| Gate_t4 | precise | 1204 |
| Gate_t5 | precise | 1204 |
| Gate_t6 | precise | 1204 |
| Gate_t7 | precise | 1204 |
| Gumdrop0 | hull | 552 |
| Gumdrop1 | hull | 414 |
| Gumdrop2 | hull | 414 |
| Hazard36 | none | 360 |
| Lolly0 | hull | 652 |
| Lolly1 | hull | 652 |
| Lolly2 | hull | 652 |
| Lolly3 | hull | 650 |
| Peppermint | none | 160 |
| PlotBase | box | 2200 |
| Sacks1 | box | 448 |
| Slot12x12 | none | 168 |
| Slot20x14 | none | 216 |
| Slot40x8 | none | 384 |
| SpawnPad | precise | 612 |
| Upgrader1 | hull | 554 |
| Walk18x6 | none | 156 |
| Walk30x5 | none | 252 |
| WrapperBin | box | 146 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Conveyor | 24 | 1256 | 30,144 | 9% |
| PlotBase | 8 | 2200 | 17,600 | 5% |
| BuyButton | 24 | 704 | 16,896 | 5% |
| Lolly0 | 23 | 652 | 14,996 | 5% |
| FencePost | 208 | 66 | 13,728 | 4% |
| Exchange | 1 | 13158 | 13,158 | 4% |
| Gumdrop0 | 22 | 552 | 12,144 | 4% |
| Lolly2 | 16 | 652 | 10,432 | 3% |
| Gumdrop1 | 22 | 414 | 9,108 | 3% |
| Gumdrop2 | 22 | 414 | 9,108 | 3% |
| Collector1 | 8 | 1092 | 8,736 | 3% |
| CandyLamp | 16 | 522 | 8,352 | 3% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (10)

- note CoinChute: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- FencePost: lowest point y=0.60 above its origin (floats when placed)
- note Gate_t0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t3: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t4: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t5: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t6: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Gate_t7: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `SugarworksKit`).
2. Insert `SugarworksSetup.lua` as ModuleScript ServerStorage.SugarworksSetup, run `SugarworksKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.SugarworksSetup).Build(game.ServerStorage.SugarworksKit, workspace)`, then `.ApplyLook()`.