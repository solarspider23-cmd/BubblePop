# Sugarworks - Studio setup

Files: `roblox/` = export of the map .blend (`roblox_export.py -- --name Sugarworks --hero ^Exchange$`). 63 kit props, 856 (1163 MeshParts) placements, 5 static chunks, **329,060 placed triangles** (budget 450k). Import as for every map in this skill: GLBs in `roblox/kit/` + `roblox/static/` into `ServerStorage.SugarworksKit`, `SugarworksSetup.lua` as a ModuleScript, run `SugarworksKitPrep.lua`, then `require(game.ServerStorage.SugarworksSetup).Build(game.ServerStorage.SugarworksKit, workspace)`.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: the Candy Exchange is the brief's hero landmark (13.2k tris, hero budget 30k).
