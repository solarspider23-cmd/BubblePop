# ShatteredVoid - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 54 | reuse: fewer unique meshes = less memory |
| Placed props | 320 (851 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 14 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 174,654 | hard budget 450,000 (--budget) |
| Largest prop | OrbitSingularity (2400 tris) | <= 20000 per MeshPart |
| Footprint | x -753..692, z -774..766 | keep under 2,048 from origin for float precision comfort |
| Palette | ShatteredVoid_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| ArenaCircle | none | 2112 |
| ArenaRim | precise | 3156 |
| AscensionAltar | precise | 2852 |
| CrystalChips1 | none | 84 |
| CrystalChips2 | none | 82 |
| CrystalChips3 | none | 84 |
| CrystalCyan2 | hull | 594 |
| CrystalCyan4 | hull | 578 |
| CrystalHang0 | none | 526 |
| CrystalHang1 | none | 574 |
| CrystalViolet1 | hull | 600 |
| CrystalViolet3 | hull | 554 |
| DebrisShard1 | none | 232 |
| DebrisShard2 | none | 232 |
| DebrisShard3 | none | 220 |
| DebrisShard4 | none | 228 |
| FarDebris1 | none | 58 |
| FarDebris2 | none | 54 |
| FarDebris3 | none | 58 |
| HeartCrystal | hull | 1032 |
| LiftBeam | none | 1800 |
| LiftPad | precise | 1060 |
| LiftPadTop | precise | 1060 |
| OrbitSingularity | none | 7848 |
| OverlookCircle | none | 2112 |
| Pillar1 | hull | 988 |
| PillarBroken1 | hull | 1212 |
| PillarBroken2 | hull | 1212 |
| PillarBroken3 | hull | 1212 |
| RiftGate | precise | 3778 |
| RimChunk0 | hull | 76 |
| Rubble1 | hull | 314 |
| Rubble2 | hull | 262 |
| RuneBridgeRiftArena | precise | 1916 |
| RuneBridgeSeerArena | precise | 1912 |
| RuneBridgeShopSeer | precise | 1628 |
| RuneBridgeSpawnAltar | precise | 1636 |
| RuneBridgeSpawnShop | precise | 1636 |
| SeersLectern | precise | 1596 |
| SpawnDais | precise | 3112 |
| SporePods1 | hull | 704 |
| SporePods2 | hull | 704 |
| StepStone1 | precise | 158 |
| StepStone2 | precise | 158 |
| StepStone3 | precise | 158 |
| VoidArch | precise | 996 |
| VoidBrazier | box | 762 |
| VoidGrass1 | none | 288 |
| VoidGrass2 | none | 288 |
| VoidGrass3 | none | 288 |
| VoidMerchant | precise | 1672 |
| VoidRail | box | 408 |
| VoidTendril1 | none | 1120 |
| VoidTendril2 | none | 1120 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| VoidTendril1 | 12 | 1120 | 13,440 | 8% |
| VoidGrass1 | 30 | 288 | 8,640 | 5% |
| OrbitSingularity | 1 | 7848 | 7,848 | 4% |
| VoidTendril2 | 7 | 1120 | 7,840 | 4% |
| VoidGrass3 | 27 | 288 | 7,776 | 4% |
| VoidGrass2 | 23 | 288 | 6,624 | 4% |
| SporePods2 | 8 | 704 | 5,632 | 3% |
| SporePods1 | 7 | 704 | 4,928 | 3% |
| CrystalHang0 | 8 | 526 | 4,208 | 2% |
| CrystalHang1 | 7 | 574 | 4,018 | 2% |
| RiftGate | 1 | 3778 | 3,778 | 2% |
| CrystalViolet3 | 6 | 554 | 3,324 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (0)

- none

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `ShatteredVoidKit`).
2. Insert `ShatteredVoidSetup.lua` as ModuleScript ServerStorage.ShatteredVoidSetup, run `ShatteredVoidKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.ShatteredVoidSetup).Build(game.ServerStorage.ShatteredVoidKit, workspace)`, then `.ApplyLook()`.