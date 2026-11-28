# WhisperingGrove - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 47 | reuse: fewer unique meshes = less memory |
| Placed props | 785 (814 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 12 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 439,233 | hard budget 450,000 (--budget) |
| Largest prop | ElderTree (4466 tris) | <= 20000 per MeshPart |
| Footprint | x -218..218, z -218..216 | keep under 2,048 from origin for float precision comfort |
| Palette | WhisperingGrove_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Barrel1 | box | 400 |
| Birch252 | hull | 566 |
| Birch252_v001 | hull | 566 |
| Bridge | precise | 1818 |
| Bush501 | none | 432 |
| Bush503 | none | 310 |
| Bush503_v001 | none | 310 |
| Campfire | box | 1216 |
| Crate1 | box | 164 |
| CrystalCluster | hull | 204 |
| ElderTree | precise | 4877 |
| Fence1 | box | 172 |
| Fern601 | none | 560 |
| Fern602 | none | 640 |
| Flowerscloth903 | none | 782 |
| Flowerscloth903_v001 | none | 782 |
| Flowerscream902 | none | 784 |
| GlowShroom400 | hull | 228 |
| GlowShroom401 | hull | 228 |
| LanternPost | box | 290 |
| Lily1201 | none | 248 |
| Lily1202 | none | 204 |
| Log301 | hull | 1304 |
| Log802 | hull | 1304 |
| Oak102 | hull | 952 |
| Oak102_v001 | hull | 952 |
| Oak102_v002 | hull | 952 |
| Oak104 | hull | 750 |
| Pine201 | hull | 244 |
| Pine202 | hull | 244 |
| Pine203 | hull | 244 |
| QuestBoard | box | 592 |
| Reeds1101 | none | 350 |
| RngAltar | precise | 3110 |
| Rock702 | hull | 46 |
| Rock703 | hull | 42 |
| Rock703_v001 | hull | 42 |
| Rock703_v002 | hull | 42 |
| Shroom410 | hull | 344 |
| Shroom411 | hull | 346 |
| Signpost | box | 68 |
| Steps1301 | hull | 196 |
| Stump801 | hull | 200 |
| Tent1 | precise | 135 |
| Tent2 | precise | 135 |
| Tuft1001 | none | 90 |
| Tuft1001_v001 | none | 90 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| Oak102 | 38 | 952 | 36,176 | 8% |
| Oak102_v001 | 37 | 952 | 35,224 | 8% |
| Oak104 | 35 | 750 | 26,250 | 6% |
| Oak102_v002 | 26 | 952 | 24,752 | 6% |
| Flowerscloth903 | 21 | 782 | 16,422 | 4% |
| Bush501 | 37 | 432 | 15,984 | 4% |
| Birch252_v001 | 24 | 566 | 13,584 | 3% |
| Birch252 | 23 | 566 | 13,018 | 3% |
| Fern601 | 23 | 560 | 12,880 | 3% |
| Pine202 | 52 | 244 | 12,688 | 3% |
| Pine201 | 49 | 244 | 11,956 | 3% |
| Flowerscream902 | 13 | 784 | 10,192 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (0)

- none

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `WhisperingGroveKit`).
2. Insert `WhisperingGroveSetup.lua` as ModuleScript ServerStorage.WhisperingGroveSetup, run `WhisperingGroveKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.WhisperingGroveSetup).Build(game.ServerStorage.WhisperingGroveKit, workspace)`, then `.ApplyLook()`.