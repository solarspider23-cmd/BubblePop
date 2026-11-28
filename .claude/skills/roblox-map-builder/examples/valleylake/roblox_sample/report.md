# MistvaleLake - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 76 | reuse: fewer unique meshes = less memory |
| Placed props | 411 (454 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 10 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 419,132 | hard budget 450,000 (--budget) |
| Largest prop | TreeOakHero_Trunk (7502 tris) | <= 20000 per MeshPart |
| Footprint | x -381..412, z -374..306 | keep under 2,048 from origin for float precision comfort |
| Palette | MistvaleLake_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Bush1 | none | 494 |
| Bush3 | none | 484 |
| Bush4 | none | 340 |
| Crates1 | box | 1448 |
| Crates2 | box | 1448 |
| Crates3 | box | 1448 |
| FishingDock | precise | 4272 |
| Flowers1 | none | 340 |
| Flowers2 | none | 340 |
| FootBridge | precise | 1696 |
| LanternPost1 | box | 312 |
| LanternRope_28_0p1 | none | 616 |
| LanternRope_29_0p1 | none | 616 |
| LanternRope_34_0p2 | none | 616 |
| LanternRope_35_0p2 | none | 616 |
| LanternRope_36_0p1 | none | 616 |
| LanternRope_37_0p2 | none | 616 |
| LanternRope_38_0p2 | none | 616 |
| LanternRope_41_0p5 | none | 616 |
| LanternRope_42_m0p7 | none | 616 |
| LanternRope_43_m0p7 | none | 616 |
| LanternRope_49_m0p0 | none | 788 |
| LanternRope_54_m0p1 | none | 788 |
| LilyPads1 | none | 556 |
| LilyPads2 | none | 556 |
| LongHouse1 | precise | 6232 |
| LongHouse3 | precise | 6232 |
| MarketStall1 | precise | 3996 |
| MarketStall2 | precise | 3996 |
| MarketStall3 | precise | 3996 |
| Reeds1 | none | 280 |
| Reeds2 | none | 280 |
| RockBare1 | hull | 432 |
| RockKnob1 | hull | 700 |
| RockKnob2 | hull | 780 |
| RockMassiveVLo | hull | 372 |
| RockPillow1VLo | hull | 242 |
| RockPillow2 | hull | 700 |
| RockPillow2VLo | hull | 234 |
| RockTalus | hull | 260 |
| RockTower1VLo | hull | 202 |
| RopePole1 | box | 396 |
| SignStand1 | box | 324 |
| SteppingStones1 | precise | 960 |
| StoneStair | precise | 1520 |
| StoneWall1 | precise | 1040 |
| Storehouse3 | precise | 2128 |
| TownHouse2 | precise | 5440 |
| TownHouse4 | precise | 5440 |
| TreeOakA_Branches | none | 872 |
| TreeOakA_Leaves | none | 2984 |
| TreeOakA_Trunk | hull | 4530 |
| TreeOakB_Branches | none | 704 |
| TreeOakB_Leaves | none | 1880 |
| TreeOakB_Trunk | hull | 3958 |
| TreeOakHero_Branches | none | 1376 |
| TreeOakHero_Leaves | none | 7000 |
| TreeOakHero_Trunk | hull | 7502 |
| TreeOakPink_Branches | none | 616 |
| TreeOakPink_Leaves | none | 1792 |
| TreeOakPink_Trunk | hull | 3354 |
| TreePineA_Branches | none | 120 |
| TreePineA_Leaves | none | 5500 |
| TreePineA_Trunk | hull | 1914 |
| TreePineB_Branches | none | 216 |
| TreePineB_Leaves | none | 5380 |
| TreePineB_Trunk | hull | 1766 |
| TreePineC_Branches | none | 32 |
| TreePineC_Leaves | none | 1996 |
| TreePineC_Trunk | hull | 1064 |
| TreeYoungTree_Branches | none | 152 |
| TreeYoungTree_Leaves | none | 540 |
| TreeYoungTree_Trunk | hull | 910 |
| Tuft1 | none | 45 |
| Tuft2 | none | 45 |
| Waterfall | none | 4442 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| TreePineC_Leaves | 17 | 1996 | 33,932 | 8% |
| StoneWall1 | 28 | 1040 | 29,120 | 7% |
| TownHouse2 | 4 | 5440 | 21,760 | 5% |
| TownHouse4 | 4 | 5440 | 21,760 | 5% |
| LongHouse1 | 3 | 6232 | 18,696 | 4% |
| LongHouse3 | 3 | 6232 | 18,696 | 4% |
| TreePineC_Trunk | 17 | 1064 | 18,088 | 4% |
| RockTalus | 67 | 260 | 17,420 | 4% |
| Storehouse3 | 5 | 2128 | 10,640 | 3% |
| RockMassiveVLo | 23 | 372 | 8,556 | 2% |
| MarketStall1 | 2 | 3996 | 7,992 | 2% |
| TreeOakB_Trunk | 2 | 3958 | 7,916 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (14)

- note FishingDock: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_28_0p1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_29_0p1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_34_0p2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_35_0p2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_36_0p1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_37_0p2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_38_0p2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_41_0p5: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_42_m0p7: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_43_m0p7: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_49_m0p0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note LanternRope_54_m0p1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note TreeOakHero_Branches: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `MistvaleLakeKit`).
2. Insert `MistvaleLakeSetup.lua` as ModuleScript ServerStorage.MistvaleLakeSetup, run `MistvaleLakeKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.MistvaleLakeSetup).Build(game.ServerStorage.MistvaleLakeKit, workspace)`, then `.ApplyLook()`.