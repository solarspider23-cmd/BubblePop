-- Uploaded Blender models (tools/upload_model.py, tools/upload_textures.py).
-- model = Roblox Model asset id (the server loads it once); texture = image id per zone colour.
-- center = the mesh's middle measured from its origin (bottom centre of the footprint), from
-- art/bubblewrap/*.bounds.json. model = 0 means "not uploaded": the placeholder shapes are used.
return {
	enabled = true,
	intact = {
		model = 71922247748464,
		size = { 1.123, 0.48, 1.1238 },
		center = { -0.0022, 0.24, -0.0018 },
		texture = { Blue = 73220471840074 },
	},
	popped = {
		{ model = 116264308152944, size = { 1.119, 0.1128, 1.1259 }, center = { 0, 0.0564, 0 }, texture = { Blue = 78517176437500 } },
		{ model = 96857663396623, size = { 1.1053, 0.1098, 1.1299 }, center = { 0, 0.0549, 0 }, texture = { Blue = 113740392816629 } },
		{ model = 70369270734741, size = { 1.1041, 0.0922, 1.1299 }, center = { 0, 0.0461, 0 }, texture = { Blue = 130970752515282 } },
		{ model = 133920320540481, size = { 1.13, 0.2468, 1.13 }, center = { 0.0, 0.1234, -0.0 }, texture = { Blue = 138365642853579 } }, -- D
		{ model = 99501359932186, size = { 1.13, 0.1712, 1.13 }, center = { 0.0, 0.0856, -0.0 }, texture = { Blue = 97467581921901 } }, -- E
		{ model = 130968089036837, size = { 1.13, 0.1986, 1.13 }, center = { 0.0, 0.0993, -0.0 }, texture = { Blue = 85450337595573 } }, -- F
		{ model = 83008851952611, size = { 1.13, 0.112, 1.13 }, center = { 0.0, 0.056, -0.0 }, texture = { Blue = 72474087099384 } }, -- G
		-- H (crumpled, faceted) removed 2026-11-25: owner said some popped looks were bad
		{ model = 79384248715427, size = { 1.13, 0.218, 1.13 }, center = { 0.0, 0.109, -0.0 }, texture = { Blue = 108557943965039 } }, -- I
		{ model = 91291224227746, size = { 1.13, 0.15, 1.13 }, center = { 0.0, 0.075, -0.0 }, texture = { Blue = 136041281793338 } }, -- J
	},
	sheet = {
		model = 78176672889725,
		size = { 6.05, 0.059, 6.05 },
		center = { 0.025, 0.0295, -0.025 },
		topOffset = 0.04, -- the sheet's top (where bubbles sit) is this far above its origin
	},
	zone = "Blue", -- which texture set the test room uses
}
