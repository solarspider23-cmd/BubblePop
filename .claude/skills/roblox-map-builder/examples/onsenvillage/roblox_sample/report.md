# YumoriSprings - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 54 | reuse: fewer unique meshes = less memory |
| Placed props | 252 (286 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 9 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 348,824 | hard budget 450,000 (--budget) |
| Largest prop | PagodaTop (12140 tris) | <= 20000 per MeshPart |
| Footprint | x -144..117, z -139..134 | keep under 2,048 from origin for float precision comfort |
| Palette | YumoriSprings_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| BathPavilion | precise | 7740 |
| Bench1 | box | 372 |
| Boulder1 | hull | 62 |
| Boulder2 | hull | 64 |
| Cedar1 | hull | 266 |
| Cedar2 | hull | 272 |
| Cedar3 | hull | 260 |
| CloudTree1 | hull | 1126 |
| CloudTree3 | hull | 1112 |
| Crag1 | hull | 292 |
| Crag2 | hull | 316 |
| Crag3 | hull | 300 |
| Crag4 | hull | 312 |
| Crag5 | hull | 310 |
| Crag6 | hull | 318 |
| Crag7 | hull | 294 |
| Crag8 | hull | 314 |
| Crates1 | box | 836 |
| Crates2 | box | 840 |
| FootBridge | precise | 5500 |
| HandCart1 | box | 1812 |
| HotPool1 | precise | 2214 |
| HotPool2 | precise | 2210 |
| HotPool3 | precise | 1708 |
| HotPool4 | precise | 1700 |
| InnB | precise | 10046 |
| JpPine1 | hull | 1102 |
| JpPine2 | hull | 1106 |
| JpPine3 | hull | 1094 |
| KoiPond1 | precise | 1116 |
| LanternPost1 | box | 748 |
| LanternPost2 | box | 748 |
| Maple2 | hull | 1124 |
| Maple4 | hull | 1094 |
| NoodleStall | box | 5232 |
| PagodaBase | precise | 12488 |
| PagodaTop | precise | 12296 |
| Planter1 | box | 1170 |
| Planter2 | box | 1178 |
| RailPost | box | 246 |
| Railing6 | box | 466 |
| SakeBarrels1 | box | 3704 |
| ShopD | precise | 11612 |
| Shrub1 | none | 168 |
| Stair65_8 | precise | 1288 |
| Stair80_6 | precise | 1456 |
| SteppingStones1 | precise | 158 |
| SteppingStones2 | precise | 136 |
| TallC | precise | 11184 |
| Torii | precise | 460 |
| Toro1 | box | 1678 |
| TowelRack1 | box | 2316 |
| TowelRack2 | box | 2316 |
| Tuft1 | none | 98 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Railing6 | 52 | 466 | 24,232 | 7% |
| ShopD | 2 | 11612 | 23,224 | 7% |
| TallC | 2 | 11184 | 22,368 | 6% |
| Toro1 | 12 | 1678 | 20,136 | 6% |
| InnB | 2 | 10046 | 20,092 | 6% |
| BathPavilion | 2 | 7740 | 15,480 | 4% |
| PagodaBase | 1 | 12488 | 12,488 | 4% |
| PagodaTop | 1 | 12296 | 12,296 | 4% |
| JpPine3 | 11 | 1094 | 12,034 | 3% |
| Cedar1 | 30 | 266 | 7,980 | 2% |
| Planter1 | 6 | 1170 | 7,020 | 2% |
| CloudTree3 | 5 | 1112 | 5,560 | 2% |

## Over-detailed for their size (> 600 tris per stud; players do not see that detail)

- PagodaBase: 12488 tris for 20.4 studs

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (1)

- PagodaTop: lowest point y=14.75 above its origin (floats when placed)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `YumoriSpringsKit`).
2. Insert `YumoriSpringsSetup.lua` as ModuleScript ServerStorage.YumoriSpringsSetup, run `YumoriSpringsKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.YumoriSpringsSetup).Build(game.ServerStorage.YumoriSpringsKit, workspace)`, then `.ApplyLook()`.