# WhisperingGrove - Studio setup

Files: `roblox/` = export of the map .blend (`roblox_export.py -- --name WhisperingGrove --soft (?i)tree|pine|oak|birch|bush|broadleaf|canopy|fern|flower|grass|shrub|leaf|tuft|reed|vine|ivy|moss|lily|petal|blossom|hedge|plant`). 47 kit props, 785 (814 MeshParts) placements, 12 static chunks, **439,233 placed triangles** (budget 450k). Import as for every map in this skill: GLBs in `roblox/kit/` + `roblox/static/` into `ServerStorage.WhisperingGroveKit`, `WhisperingGroveSetup.lua` as a ModuleScript, run `WhisperingGroveKitPrep.lua`, then `require(game.ServerStorage.WhisperingGroveSetup).Build(game.ServerStorage.WhisperingGroveKit, workspace)`.

## Export checks
Placement checks (roblox_export.py 6c): clip 0, float 0, water 0, falls 0, collision 0, buffer 0; EXPORT_OK.
Flags: oak + birch added to --soft (tree species).
