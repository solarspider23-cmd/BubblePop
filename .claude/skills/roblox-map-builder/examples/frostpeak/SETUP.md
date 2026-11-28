# Frostpeak - Studio setup

Files: `roblox/` = export of the map .blend (`roblox_export.py -- --name Frostpeak`). 24 kit props, 559 (625 MeshParts) placements, 11 static chunks, **335,832 placed triangles** (budget 450k). Import as for every map in this skill: GLBs in `roblox/kit/` + `roblox/static/` into `ServerStorage.FrostpeakKit`, `FrostpeakSetup.lua` as a ModuleScript, run `FrostpeakKitPrep.lua`, then `require(game.ServerStorage.FrostpeakSetup).Build(game.ServerStorage.FrostpeakKit, workspace)`.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: unchanged.
