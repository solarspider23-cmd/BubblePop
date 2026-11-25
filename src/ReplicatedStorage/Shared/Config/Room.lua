-- The popping room: floor and walls covered in bubble wrap sheets, plain ceiling.
-- Everything is built from these numbers (server: walls, sheets; client: bubbles).
local function rgb(r, g, b)
	return { r, g, b }
end

return {
	floorY = 0, -- top of the floor slab
	floorSheets = 10, -- the floor is floorSheets x floorSheets sheets (10 x 10 = 60 x 60 studs)
	wallRows = 2, -- sheets stacked up each wall (2 x 6 = 12 studs tall); the ceiling sits on top
	wallLift = 0.7, -- wall wrap starts this high, so the bottom row clears the floor bubbles (plain strip below)
	sheetSize = 6, -- one sheet is 6 x 6 studs

	-- Recycler placeholder block in the middle of the room. Floor sheets under `clear` are left out.
	recycler = { size = { 10, 7, 10 }, clear = 12, color = { 60, 200, 90 } },
	spawn = { 0, 3, 18 }, -- where players appear (clear of the recycler)
	perSheet = 5, -- 5 x 5 bubbles per sheet
	spacing = 1.2, -- distance between bubble centres (perSheet * spacing must equal sheetSize)
	sheetThickness = 0.04,

	-- Placeholder bubble shapes (used until the Blender meshes are uploaded)
	bubbleWidth = 1.12,
	bubbleHeight = 0.48,
	poppedHeight = 0.11,

	-- Colours as {r, g, b} 0-255 (the "Blue" zone from tools/blender/build_bubblewrap.py)
	colors = {
		bubble = rgb(80, 190, 255),
		bubbleTransparency = 0.1,
		popped = rgb(140, 205, 250),
		tear = rgb(14, 36, 96),
		sheet = rgb(214, 220, 230), -- light grey film so the blue bubbles stand out
		wall = rgb(150, 156, 168),
		floor = rgb(130, 136, 148),
		ceiling = rgb(245, 245, 250),
	},

	-- Room lighting (bright and clear, so every bubble reads)
	lighting = {
		brightness = 1,
		ambient = rgb(135, 140, 155),
		exposure = 0,
		contrast = 0.1,
		saturation = 0.1,
		lampRange = 18,
		lampBrightness = 0.5,
	},

	-- Looks to compare in the test room (press L in game). "Cartoon" = the colours above with
	-- the painted textures; "Clear" = plain see-through plastic like real bubble wrap.
	-- A look may set sheet / wall / floor colours; anything it leaves out uses `colors`.
	looks = {
		{ name = "Cartoon" },
		{ name = "Cartoon (all blue)", sheet = rgb(28, 88, 180), wall = rgb(20, 60, 130), floor = rgb(20, 60, 130) },
		{
			name = "Clear",
			plain = true,
			bubble = rgb(235, 245, 252),
			bubbleTransparency = 0.45,
			bubbleMaterial = "Glass",
			bubbleReflectance = 0.15,
			popped = rgb(240, 244, 248),
			poppedTransparency = 0.2,
			tear = rgb(120, 135, 150),
			sheet = rgb(228, 236, 242),
			sheetTransparency = 0.35,
			wall = rgb(185, 192, 202),
			floor = rgb(165, 172, 182),
		},
	},
}
