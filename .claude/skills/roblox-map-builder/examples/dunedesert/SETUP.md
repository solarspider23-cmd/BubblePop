# The Gilded Dunes - Studio setup

Export: `roblox/` = `dune_map.blend` exported with `--name GildedDunes --hero "^(StepPyramid|ColossusHead|SunkenTemple)$"
--rock "(?i)rock|cliff|boulder|stone|crag|mesa|butte|stalag|outcrop"` (60 kit props, 474 placements, 9 static chunks,
304,805 placed triangles, `EXPORT_OK`, every placement check at 0: clip, float, water, falls, collision; report.md).
Flags: the three landmarks (pyramid, colossus head, sunken temple) are the heroes (30k each); outcrops are rocks (bedded
into the dunes on purpose). Every auto-grounded prop is fitted while placing (`fit` in dune_map.py = the export's clip +
float rules: raised in 0.25 steps or nudged; a prop that fits nowhere is dropped), the skull rests on a level patch,
and the oasis is two props on one origin: `OasisBasin` (bed, rim, well; precise) + `OasisWater` (the disc; none).

## 1. Import
1. File > Import 3D: every file in `roblox/kit/` and `roblox/static/` + `AxisProbe.glb`. Scale unit **studs**, pivot =
   scene origin, anchored, keep materials. Put them in `ServerStorage.GildedDunesKit`.
2. `GildedDunesSetup.lua` -> ModuleScript `ServerStorage.GildedDunesSetup`; run `GildedDunesKitPrep.lua` once.
3. AxisProbe check, set `M.YAW_FIX` (references/roblox_pipeline.md section 5).
4. `require(game.ServerStorage.GildedDunesSetup).Build(game.ServerStorage.GildedDunesKit, workspace)` then `.ApplyLook()`.
5. `Hooks.lua` (= `roblox/GildedDunesHooks.lua`) -> ModuleScript, then `require(...).Build()`.

Texture: every solid mesh shares ONE painted 1024 atlas (`GildedDunes_Palette.png`, sand ripples, sandstone grain,
woven cloth, bone, hide). It is embedded in the GLBs; if the importer drops it, upload the PNG and set it as the
TextureID of the palette MeshParts. Do NOT export with `--materials`: the ripples live in the atlas.

Palms (`TreePalmA/B/C_Trunk / _Branches / _Leaves`) are the realistic alpha-card species from
`examples/oaktrees/gen_trees.py` (graded `palm_d`). On their SurfaceAppearance: Trunk AlphaMode Overlay, Branches +
Leaves AlphaMode Transparency, DoubleSided on, no collision (the setup module does this by name).

## 2. Lighting (Properties; `ApplyLook()` sets most of it)
| Object | Property | Value |
|---|---|---|
| Lighting | Technology | Future |
| | ClockTime | 13.7 (ApplyLook picks 13.7 or 10.3 to match the sun from the SSW) |
| | GeographicLatitude | 23 (sun high: short shadows) |
| | Brightness | 3.7 |
| | Ambient | 120, 110, 95 |
| | OutdoorAmbient | 150, 145, 135 |
| | ColorShift_Top | 255, 242, 219 |
| | ColorShift_Bottom | 60, 80, 120 (cool sky in the shadows) |
| | EnvironmentDiffuseScale / SpecularScale | 0.6 / 0.3 |
| | ShadowSoftness | 0.15 (crisp noon shadows) |
| Atmosphere | Density | 0.30 |
| | Offset | 0.05 |
| | Color | 255, 243, 222 (warm heat haze) |
| | Decay | 233, 236, 233 (bleached horizon) |
| | Glare / Haze | 0.4 / 1.4 |
| Sky | (default or a plain gradient sky) | CelestialBodiesShown on, SunAngularSize 14 |
| BloomEffect | Intensity / Size / Threshold | 0.3 / 18 / 1.1 |
| ColorCorrectionEffect | Brightness / Contrast / Saturation / TintColor | 0.02 / 0.12 / 0.12 / 255, 248, 236 |
| SunRaysEffect | Intensity / Spread | 0.05 / 0.3 |

Heat shimmer (optional): a few big, slow ParticleEmitters with a faint refraction-like texture are not available in
Roblox; fake it with Atmosphere Glare + Haze above and keep the far mesas soft.

## 3. Gameplay anchors (Hooks)
Spawn (sun dais), stations QuestStele / Upgrades / CaravanTrader (BillboardGui + ProximityPrompt), DungeonPortal,
18 DigSpots (attribute Tier 1-3), POI zone boxes (attribute Poi), PyramidSummit and OasisWell points. Names and labels
are GUIs only; nothing is written in the meshes.
