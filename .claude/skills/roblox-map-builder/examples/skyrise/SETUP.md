# Skyrise - Studio setup

Files: `roblox/` = export of the map .blend (`roblox_export.py -- --name Skyrise --soft <default>|puffy|charred --float-ok <default>|skyrock|bridge`). 116 kit props, 907 (1163 MeshParts) placements, 11 static chunks, **448,550 placed triangles** (budget 450k). Import as for every map in this skill: GLBs in `roblox/kit/` + `roblox/static/` into `ServerStorage.SkyriseKit`, `SkyriseSetup.lua` as a ModuleScript, run `SkyriseKitPrep.lua`, then `require(game.ServerStorage.SkyriseSetup).Build(game.ServerStorage.SkyriseKit, workspace)`.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: puffy / charred trees are trees (--soft); floating sky rocks and island-to-island bridge spans are meant to hang (--float-ok).
