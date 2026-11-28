# RiverfieldSiege - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 90 | reuse: fewer unique meshes = less memory |
| Placed props | 474 (491 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 12 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 448,719 | hard budget 450,000 (--budget) |
| Largest prop | SunderedBridge (13575 tris) | <= 20000 per MeshPart |
| Footprint | x -322..322, z -212..209 | keep under 2,048 from origin for float precision comfort |
| Palette | RiverfieldSiege_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| AmmoPile2 | box | 1370 |
| BatteringRam | hull | 3783 |
| Boulder1 | hull | 125 |
| Boulder2 | hull | 118 |
| Boulder3 | hull | 130 |
| Brazier1 | box | 800 |
| BridgeTower | precise | 10774 |
| BrokenCart1 | hull | 1922 |
| BrokenCart2 | hull | 1924 |
| Bush1 | none | 131 |
| Bush2 | none | 132 |
| Bush3 | none | 128 |
| Campfire1 | hull | 1057 |
| Cheval10 | box | 1163 |
| CurtainWall26_blue | precise | 1470 |
| CurtainWall26_red | precise | 1470 |
| CurtainWall27_blue | precise | 1672 |
| CurtainWall27_red | precise | 1674 |
| DeadTree1 | hull | 371 |
| DeadTree2 | hull | 373 |
| DeadTree3 | hull | 371 |
| Debris_blue1 | none | 759 |
| Debris_blue2 | none | 760 |
| Debris_blue3 | none | 755 |
| Debris_red1 | none | 759 |
| Debris_red2 | none | 760 |
| Debris_red3 | none | 755 |
| DonjonTop_blue | precise | 5444 |
| DonjonTop_red | precise | 5443 |
| Donjon_blue | precise | 9710 |
| Donjon_red | precise | 9710 |
| DryWall12_2 | box | 933 |
| DryWall12_4 | box | 930 |
| DryWall14_1 | box | 1072 |
| DryWall14_3 | box | 1066 |
| Duckboard6 | none | 120 |
| Dummy_blue1 | box | 470 |
| Dummy_red1 | box | 470 |
| FootBridge40 | precise | 4647 |
| Gatehouse_blue | precise | 9100 |
| Gatehouse_red | precise | 9098 |
| Graves1 | none | 625 |
| Graves2 | none | 621 |
| HayBales1 | box | 384 |
| HayBales2 | box | 385 |
| Ladder17_24 | hull | 1098 |
| Mantlet_blue1 | box | 1778 |
| Mantlet_blue2 | box | 1776 |
| Mantlet_red1 | box | 1778 |
| Mantlet_red2 | box | 1776 |
| Oak1 | hull | 696 |
| Oak2 | hull | 685 |
| Oak3 | hull | 830 |
| Palisade10_2 | box | 912 |
| Palisade12_1 | box | 1088 |
| Palisade14_1 | box | 1311 |
| Palisade15_1 | box | 1399 |
| Pine_full4 | hull | 506 |
| Pine_squat5 | hull | 361 |
| Pine_squat6 | hull | 365 |
| Pine_tall1 | hull | 589 |
| Pine_tall2 | hull | 580 |
| Pine_young7 | hull | 307 |
| Pine_young8 | hull | 288 |
| Rubble1 | hull | 244 |
| Rubble2 | hull | 232 |
| Rubble3 | hull | 246 |
| RuinedChapel | precise | 10947 |
| SiegeTower_blue | precise | 6807 |
| SiegeTower_red | precise | 6807 |
| SunderedBridge | precise | 13575 |
| Supplies1 | box | 1717 |
| Supplies2 | box | 1711 |
| Tent_blue | precise | 815 |
| Tent_red | precise | 815 |
| Tower_blue | precise | 3845 |
| Tower_red | precise | 3848 |
| Trebuchet_blue | hull | 4243 |
| Trebuchet_red | hull | 4243 |
| Tuft1 | none | 56 |
| Tuft2 | none | 56 |
| Tuft3 | none | 60 |
| WallStair14 | precise | 2703 |
| WallStair14M | precise | 2703 |
| Wattle12 | box | 700 |
| Wattle14 | box | 779 |
| Wattle15 | box | 860 |
| WeaponRack_blue | box | 1061 |
| WeaponRack_red | box | 1062 |
| Well | box | 1695 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Tower_red | 4 | 3848 | 15,392 | 3% |
| Tower_blue | 4 | 3845 | 15,380 | 3% |
| CurtainWall27_red | 9 | 1674 | 15,066 | 3% |
| CurtainWall27_blue | 9 | 1672 | 15,048 | 3% |
| SunderedBridge | 1 | 13575 | 13,575 | 3% |
| Palisade15_1 | 8 | 1399 | 11,192 | 2% |
| RuinedChapel | 1 | 10947 | 10,947 | 2% |
| BridgeTower | 1 | 10774 | 10,774 | 2% |
| Donjon_red | 1 | 9710 | 9,710 | 2% |
| Donjon_blue | 1 | 9710 | 9,710 | 2% |
| Pine_tall1 | 16 | 589 | 9,424 | 2% |
| FootBridge40 | 2 | 4647 | 9,294 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (5)

- DonjonTop_blue: lowest point y=32.00 above its origin (floats when placed)
- DonjonTop_red: lowest point y=32.00 above its origin (floats when placed)
- note Ladder17_24: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note WallStair14: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note WallStair14M: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `RiverfieldSiegeKit`).
2. Insert `RiverfieldSiegeSetup.lua` as ModuleScript ServerStorage.RiverfieldSiegeSetup, run `RiverfieldSiegeKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.RiverfieldSiegeSetup).Build(game.ServerStorage.RiverfieldSiegeKit, workspace)`, then `.ApplyLook()`.