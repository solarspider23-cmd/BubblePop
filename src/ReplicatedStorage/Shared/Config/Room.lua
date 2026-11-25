-- The popping room: floor and walls covered in bubble wrap sheets, plain ceiling.
-- Everything is built from these numbers (server: walls, sheets; client: bubbles).
local function rgb(r, g, b)
	return { r, g, b }
end

return {
	floorY = 0, -- top of the floor slab
	floorSheets = 6, -- the floor is floorSheets x floorSheets sheets (6 x 6 = 36 x 36 studs)
	wallRows = 3, -- sheets stacked up each wall (3 x 6 = 18 studs tall); the ceiling sits on top
	sheetSize = 6, -- one sheet is 6 x 6 studs
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
		sheet = rgb(28, 88, 180),
		wall = rgb(20, 60, 130),
		floor = rgb(20, 60, 130),
		ceiling = rgb(245, 245, 250),
	},
}
