# Frostpeak - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 24 | reuse: fewer unique meshes = less memory |
| Placed props | 559 (625 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 11 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 335,832 | hard budget 450,000 (--budget) |
| Largest prop | Cabin3 (3562 tris) | <= 20000 per MeshPart |
| Footprint | x -218..215, z -218..218 | keep under 2,048 from origin for float precision comfort |
| Palette | Frostpeak_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Barrel1 | box | 400 |
| Bench1 | box | 376 |
| Cabin1 | precise | 3682 |
| Cabin2 | precise | 3568 |
| Cabin3 | precise | 3838 |
| Crate1 | box | 164 |
| CrystalCluster | hull | 202 |
| Drift1 | none | 34 |
| Drift2 | none | 34 |
| Fence1 | box | 172 |
| FishHut5 | precise | 1934 |
| FrostSpire | precise | 1314 |
| LanternPost | box | 290 |
| Rock700 | hull | 54 |
| Rock701 | hull | 112 |
| Rock702 | hull | 46 |
| RollWell | box | 1072 |
| Sled1 | hull | 340 |
| SnowPine31 | hull | 386 |
| SnowPine31_v001 | hull | 386 |
| SnowPine32 | hull | 380 |
| Snowman1 | hull | 532 |
| Stall4 | precise | 702 |
| Stall5 | precise | 702 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| SnowPine31 | 144 | 386 | 55,584 | 17% |
| SnowPine31_v001 | 123 | 386 | 47,478 | 14% |
| SnowPine32 | 121 | 380 | 45,980 | 14% |
| Cabin3 | 4 | 3838 | 15,352 | 5% |
| Cabin1 | 4 | 3682 | 14,728 | 4% |
| Cabin2 | 4 | 3568 | 14,272 | 4% |
| LanternPost | 21 | 290 | 6,090 | 2% |
| FishHut5 | 3 | 1934 | 5,802 | 2% |
| Barrel1 | 12 | 400 | 4,800 | 1% |
| Rock701 | 24 | 112 | 2,688 | 1% |
| Fence1 | 13 | 172 | 2,236 | 1% |
| Crate1 | 12 | 164 | 1,968 | 1% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (0)

- none

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `FrostpeakKit`).
2. Insert `FrostpeakSetup.lua` as ModuleScript ServerStorage.FrostpeakSetup, run `FrostpeakKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.FrostpeakSetup).Build(game.ServerStorage.FrostpeakKit, workspace)`, then `.ApplyLook()`.