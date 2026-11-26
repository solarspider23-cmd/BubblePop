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
		{ model = 137095276416476, size = { 1.13, 0.07, 1.13 }, center = { 0.0, 0.035, -0.0 }, texture = { Blue = 135199124568848 } }, -- H (crumpled: owner likes it)
		{ model = 79384248715427, size = { 1.13, 0.218, 1.13 }, center = { 0.0, 0.109, -0.0 }, texture = { Blue = 108557943965039 } }, -- I
		{ model = 91291224227746, size = { 1.13, 0.15, 1.13 }, center = { 0.0, 0.075, -0.0 }, texture = { Blue = 136041281793338 } }, -- J
	},
	sheet = {
		model = 78176672889725,
		size = { 6.05, 0.059, 6.05 },
		center = { 0.025, 0.0295, -0.025 },
		topOffset = 0.04, -- the sheet's top (where bubbles sit) is this far above its origin
	},
	-- the lobby gumball (one near-white glossy ball, tinted per colour in game). Its textures are in
	-- art/GumballLook.rbxmx (a SurfaceAppearance: games can't set texture maps from scripts).
	gumball = {
		model = 119599622536830,
		size = { 0.9949, 0.9949, 0.9949 },
		maps = { color = 95711767485834, normal = 135854173628793, roughness = 119594612790878, metalness = 96962788681730 },
	},
	-- The candy lobby (art/hub_*; docs/art_review.md). Each entry is one uploaded Model asset; Main loads it
	-- into ReplicatedStorage.HubAssets/<entry>/<mesh>. meshes = the middle of each mesh measured from the
	-- model's origin (bottom centre of the footprint, front facing -Z), as Roblox imported it
	-- (art/hub_*/*.meshes.json). look = the SurfaceAppearance in art/<look>.rbxmx put on the textured meshes;
	-- meshes listed in flat get no look (glow, glass, shine and plain-colour pieces). model = 0: Hub uses
	-- its part-built pieces instead.
	hub = {
		Machine = {
			model = 100276863444750,
			look = "HubMachineLook",
			meshes = { Machine_Body = { 0, 23.545, 0 }, Machine_Flap = { 0, 3.54, -9.547 }, Machine_Glass = { 0, 30.875, 0 }, Machine_Knob = { 0, 7.9, -10.045 }, Machine_Shine = { 4.75, 36.086, -10.781 } },
			flat = { "Machine_Glass", "Machine_Shine" },
		},
		Banner = {
			model = 105870305541717,
			meshes = { Banner_Body = { 0, 4.6, -3.3 }, Banner_Bolts = { 0, 4.6, -4.3 }, Banner_Trim = { 0, 4.6, 0.825 } },
		},
		GumballLo = {
			model = 85044186253132,
			look = "GumballLook",
			meshes = { GumballCore_Globe = { 0.209, -4.263, -0.245 }, GumballCore_Jar = { -0.009, 1.749, -0.014 }, GumballLo = { 0, 0, 0 } },
			flat = { "GumballCore_Globe", "GumballCore_Jar" },
		},
		Pad = {
			model = 135391288871981,
			look = "HubPadLook",
			meshes = { Pad_Body = { 0, 0.3, 0 }, Pad_Glow = { 0, 0.335, 0 }, Pad_Tint = { 0, 0.325, 0 } },
			flat = { "Pad_Glow" },
		},
		PadSign = {
			model = 92044368166549,
			look = "HubPadLook",
			meshes = { PadSign_Body = { 0, 3.31, 0 }, PadSign_Tint = { 0, 5, 0 } },
		},
		SpawnPad = {
			model = 97415859542233,
			look = "HubPadLook",
			meshes = { SpawnPad_Body = { 0, 0.185, 0 } },
		},
		Fence = {
			model = 129055144509829,
			look = "HubFenceLook",
			meshes = { Fence_Corner = { 0, 2.25, 0 }, Fence_Post = { 0, 1.69, 0 }, Fence_PostGlow = { 0, 3.655, 0 }, Fence_Rail = { 0, 1.8, 0 } },
			flat = { "Fence_PostGlow" },
		},
		Board = {
			model = 95092420454361,
			look = "HubBoardLook",
			meshes = { Board_Body = { 0, 7.48, 0.245 } },
		},
		Ground = {
			model = 94561536984653,
			meshes = { Ground_Kerb = { 0, 1.925, -0.625 }, Ground_KerbBand = { 0, 0.5, -1.285 }, Ground_KerbCorner = { 0.625, 1.925, -0.625 }, Ground_KerbCornerBand = { 0.775, 0.5, -0.775 }, Ground_Tile = { 0, 0.1, 0 } },
		},
		Booth = {
			model = 138183472225784,
			look = "HubBoothLook",
			meshes = { Booth_Body = { 0, 5.5, 0 }, Booth_Tint = { 0, 5.731, 0 } },
		},
		BoothPad = {
			model = 108719534609631,
			meshes = { BoothPad_Body = { 0, 0.175, 0 }, BoothPad_Glow = { 0, 0.28, 0 } },
		},
		TopperBag = {
			model = 123738322552133,
			look = "HubBoothLook",
			meshes = { BoothTopper_Bag_Body = { 0, 1.537, -0.055 } },
		},
		TopperTicket = {
			model = 84486230080434,
			look = "HubBoothLook",
			meshes = { BoothTopper_Ticket_Body = { 0, 1.424, 0 } },
		},
		TopperCrystal = {
			model = 128124075571544,
			look = "HubBoothLook",
			meshes = { BoothTopper_Crystal_Body = { -0.047, 1.475, 0 } },
		},
		Chest = {
			model = 100925972838246,
			look = "HubChestLook",
			meshes = { Chest_Body = { 0, 1.75, -0.065 }, Chest_Glow = { 0, 0.04, 0 }, Chest_Lid = { 0, 4.67, -0.205 } },
			flat = { "Chest_Glow" },
		},
		Pit = {
			model = 89366551700928,
			look = "HubPitLook",
			meshes = { Pit_Body = { 0, 1.5, -0.782 } },
		},
		Jar = {
			model = 106034307238590,
			look = "HubJarLook",
			meshes = { Jar_Body = { 0, 6.305, 0 }, Jar_Glass = { 0, 6.825, 0 }, Jar_Shine = { -0.996, 6.5, -3.019 } },
			flat = { "Jar_Glass", "Jar_Shine" },
		},
		Island = {
			model = 120732527213759,
			look = "HubIslandLook",
			meshes = { Island_Rim = { 0, -8.665, 0 }, Island_Under = { 0, -31.5, 0 } },
		},
		Lollipop = {
			model = 123214833283791,
			look = "HubLollipopLook",
			meshes = { Lollipop_Ball_Body = { 0, 4.259, 0 }, Lollipop_Ball_Shine = { 0, 12.505, 0 }, Lollipop_Ball_Tint = { 0, 11.2, 0 }, Lollipop_Heart_Body = { 0, 3.925, 0 }, Lollipop_Heart_Shine = { 0, 12.93, 0 }, Lollipop_Heart_Tint = { 0, 10.601, 0 }, Lollipop_Swirl_Body = { 0, 4.225, 0 }, Lollipop_Swirl_Shine = { 0, 12.563, 0 }, Lollipop_Swirl_Tint = { 0, 11, 0 } },
			flat = { "Lollipop_Ball_Shine", "Lollipop_Heart_Shine", "Lollipop_Swirl_Shine" },
		},
		Dressing = {
			model = 130476156329433,
			look = "HubLollipopLook",
			meshes = { Dressing_Cupcake_Body = { 0, 2.875, 0 }, Dressing_Cupcake_Tint = { 0, 3.5, 0 }, Dressing_Gumdrop_Tint = { 0, 1.425, 0 }, Dressing_Sweet_Tint = { 0, 0.864, 0 } },
		},
	},
	-- CLEAN POP PLAZA (art/hub_clean; the "clean" theme in Config/Hub.lua). Same layout as hub; Main loads
	-- these only with the clean theme. Glow, glass, shine and plain-colour meshes are flat (no look).
	hubClean = {
		CleanCentre = {
			model = 124778207235213,
			look = "HubCleanCentreLook",
			meshes = { CleanCentre_Body = { 0, 11.44, 0 }, CleanCentre_Core = { 0.25, 31.3, -0.377 }, CleanCentre_Glass = { 0, 31.5, 0 }, CleanCentre_Glow = { 0, 11.475, 0 }, CleanCentre_Ring = { 0, 31.802, 0.428 }, CleanCentre_Shine = { -4.546, 37.552, -9.719 } },
			flat = { "CleanCentre_Glass", "CleanCentre_Glow", "CleanCentre_Shine" },
		},
		CleanBanner = {
			model = 91391836801130,
			meshes = { CleanBanner_Body = { 0, 4.6, -0.45 }, CleanBanner_Bubbles = { 0, 4.6, -1.075 }, CleanBanner_Glow = { 0, 4.6, -0.27 }, CleanBanner_Trim = { 0, 4.6, 2.815 } },
		},
		CleanPad = {
			model = 101691221986884,
			look = "HubCleanPadLook",
			meshes = { CleanPad_Body = { 0, 0.26, 0 }, CleanPad_Glow = { 0, 0.335, 0 }, CleanPad_Tint = { 0, 0.325, 0 } },
			flat = { "CleanPad_Glow" },
		},
		CleanPadSign = {
			model = 93859490575056,
			look = "HubCleanPadLook",
			meshes = { CleanPadSign_Body = { 0, 3.31, 0 }, CleanPadSign_Tint = { 0, 5, 0 } },
		},
		CleanSpawnPad = {
			model = 129742043957840,
			look = "HubCleanPadLook",
			meshes = { CleanSpawnPad_Body = { 0, 0.185, 0 } },
		},
		CleanFence = {
			model = 87577223014707,
			look = "HubCleanFenceLook",
			meshes = { CleanFence_Corner = { 0, 2.04, 0 }, CleanFence_CornerGlow = { 0, 4.855, 0 }, CleanFence_Post = { 0, 1.55, 0 }, CleanFence_PostGlow = { 0, 3.31, 0 }, CleanFence_Rail = { 0, 1.87, 0 } },
			flat = { "CleanFence_CornerGlow", "CleanFence_PostGlow" },
		},
		CleanBooth = {
			model = 72234480176616,
			look = "HubCleanBoothLook",
			meshes = { CleanBooth_Body = { 0, 5.13, -0.64 }, CleanBooth_Glow = { 0, 8.685, 0 }, CleanBooth_Tint = { 0, 4.63, -0.5 } },
			flat = { "CleanBooth_Glow" },
		},
		CleanBoothPad = {
			model = 107932624449180,
			look = "HubCleanBoothLook",
			meshes = { CleanBoothPad_Body = { 0, 0.175, 0 }, CleanBoothPad_Glow = { 0, 0.3, 0 } },
			flat = { "CleanBoothPad_Glow" },
		},
		CleanGift = {
			model = 101301662501219,
			look = "HubCleanGiftLook",
			meshes = { CleanGift_Body = { 0, 1.6, 0 }, CleanGift_Glow = { 0, 0.04, 0 }, CleanGift_Lid = { 0, 4.326, 0 } },
			flat = { "CleanGift_Glow" },
		},
		CleanIsland = {
			model = 71592646245579,
			look = "HubCleanIslandLook",
			meshes = { CleanIsland_Crystal = { 2.157, -42.959, 12.485 }, CleanIsland_Glow = { 0, -6.63, 0 }, CleanIsland_Rim = { 0, -5.85, 0 }, CleanIsland_Under = { -0.066, -35.25, -0.596 } },
			flat = { "CleanIsland_Glow" },
		},
		CleanTree = {
			model = 90648958603988,
			look = "HubCleanTreeLook",
			meshes = { CleanTree_Ball_Body = { 0, 3.9, 0 }, CleanTree_Ball_Shine = { -1.731, 13.308, -2.542 }, CleanTree_Ball_Tint = { 0, 11, 0 }, CleanTree_Cloud_Body = { 0, 4.05, 0 }, CleanTree_Cloud_Shine = { -1.432, 12.511, -2.105 }, CleanTree_Cloud_Tint = { -0.1, 11.15, 0 }, CleanTree_Stack_Body = { 0, 3.2, 0 }, CleanTree_Stack_Shine = { -1.475, 10.967, -2.167 }, CleanTree_Stack_Tint = { 0, 10.65, 0 } },
			flat = { "CleanTree_Ball_Shine", "CleanTree_Cloud_Shine", "CleanTree_Stack_Shine" },
		},
	},
	zone = "Blue", -- which texture set the test room uses
}
