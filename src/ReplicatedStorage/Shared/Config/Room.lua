-- The popping room: floor and walls covered in bubble wrap sheets, plain ceiling.
-- Everything is built from these numbers (server: walls, sheets; client: bubbles).
local function rgb(r, g, b)
	return { r, g, b }
end

-- Which room size to build: "wide" or "small" (see `sizes` at the bottom).
local SIZE = "starter"

local room = {
	floorY = 0, -- top of the floor slab
	wallLift = 0.7, -- wall wrap starts this high, so the bottom row clears the floor bubbles (plain strip below)
	perSheet = 5, -- 5 x 5 bubbles per sheet (the sheet model is made for 5 x 5)
	sheetThickness = 0.04,

	-- Placeholder bubble shapes (used until the Blender meshes are uploaded)
	bubbleWidth = 1.12, -- at bubbleScale 1
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

	-- The glow on the bubble under your crosshair (every look)
	aim = { fill = rgb(255, 255, 255), fillTransparency = 0.7, outline = rgb(255, 255, 255), outlineTransparency = 0.2 },

	-- Room lighting (bright and clear, so every bubble reads)
	lighting = {
		brightness = 1,
		ambient = rgb(135, 140, 155),
		exposure = 0,
		contrast = 0.1,
		saturation = 0.1,
		lampSize = 6, -- the one ceiling light (studs across)
		lampRange = 60, -- the most Roblox allows
		lampBrightness = 0.8,
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
		{
			-- Clear bubbles on a coloured sheet, with a shine spot, sunlight and shadows
			name = "Clear+",
			plain = true,
			bubble = rgb(240, 250, 255),
			bubbleTransparency = 0.3,
			bubbleMaterial = "Glass",
			bubbleReflectance = 0.25,
			shine = true, -- white shine spot on every unpopped bubble
			shadows = true, -- bubbles cast little shadows
			popped = rgb(150, 170, 190), -- popped plastic: flatter, darker, cloudier
			poppedTransparency = 0.25,
			tear = rgb(55, 75, 100),
			sheet = rgb(120, 190, 240),
			sheetTransparency = 0,
			wall = rgb(70, 95, 135),
			floor = rgb(60, 80, 115),
			trim = rgb(255, 200, 60), -- strip along the bottom of the walls
			lighting = { brightness = 2.2, clockTime = 10.5, ambient = rgb(120, 130, 150), bloom = 0.35, sunIn = true },
		},
	},
}

-- Room sizes to compare. bubbleScale shrinks the bubbles AND the sheets (1 = the original size).
-- sheetSize = 6 x bubbleScale, spacing = 1.2 x bubbleScale.
-- wallBubbleRows (optional) = bubbles up each wall; the top sheet row tucks into the ceiling.
room.sizes = {
	-- 40 x 40 room, small bubbles: each wall 40 across x 11 up = 440 (first room: not intimidating)
	starter = { bubbleScale = 5 / 6, floorSheets = 8, wallRows = 3, wallBubbleRows = 11, spawn = { 0, 3, 12 },
		recycler = { size = { 10, 7, 10 }, clear = 12, color = { 60, 200, 90 } } },
	-- 78 x 78 room, normal bubbles: each wall 65 across x 10 up = 650
	wide = { bubbleScale = 1, floorSheets = 13, wallRows = 2, spawn = { 0, 3, 18 },
		recycler = { size = { 10, 7, 10 }, clear = 18, color = { 60, 200, 90 } } },
	-- 60 x 60 room (as before), bubbles 5/6 the size: each wall 60 across x 11 up = 660
	small = { bubbleScale = 5 / 6, floorSheets = 12, wallRows = 3, wallBubbleRows = 11, spawn = { 0, 3, 18 },
		recycler = { size = { 10, 7, 10 }, clear = 12, color = { 60, 200, 90 } } },
}
for k, v in room.sizes[SIZE] do
	room[k] = v
end
room.size = SIZE
room.sheetSize = 6 * room.bubbleScale
room.spacing = 1.2 * room.bubbleScale
room.bubbleWidth *= room.bubbleScale
room.bubbleHeight *= room.bubbleScale
room.poppedHeight *= room.bubbleScale

return room
