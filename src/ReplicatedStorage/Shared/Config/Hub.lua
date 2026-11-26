-- The lobby hub: where you spawn (third person). A raised tiled plaza (studded tiles, no bubble wrap):
-- Bubble HQ with the floating logo at the back, the 4 play pads in front of it, how-to-play board,
-- bubble fountain and a bubble display on the left, 3 booths on the right, a free gift chest front left.
-- 4 pads: stand on one to make a group (up to maxPlayers); a countdown starts, the first player on
-- the pad can press Start; then the group goes into a fresh run in the popping room.
local function rgb(r, g, b)
	return { r, g, b }
end

local Hub = {
	origin = { 0, 300, 1500 }, -- hub centre: a floating island high in the sky, far from the popping room (hidden under the clouds)
	size = 112, -- the plaza is size x size studs (8 x 8 tiles)
	spawn = { 0, 4, 34 }, -- from the origin: where players appear, facing the pads
	pads = {
		{ -21, -23 }, { -7, -23 }, { 7, -23 }, { 21, -23 }, -- x, z from the origin (z -23 keeps the signs clear of the machine's stage)
	},
	padSize = { 12, 9 }, -- each play pad is a rectangle, x by z studs
	booths = { { 44, -15 }, { 44, 4 }, { 44, 23 } }, -- right side, evenly spaced, facing the middle
	boothScale = 1.3,
	floatingBubbles = { count = 40, minSize = 1.5, maxSize = 6, riseSpeed = { 1.5, 4 }, topY = 75, radius = 85 },
	dome = { radius = 100, centreY = -20 }, -- the glass bubble the whole hub sits in
	island = { radius = 99 }, -- the hub is a floating island in the sky; the bubble's lower glass is solid
	maxPlayers = 4,
	countdown = 10, -- seconds before a pad starts on its own
	backToHubSeconds = 8, -- after the room is cleared
	rooms = { { name = "Starter Room" } }, -- what the pad owner can pick (more later)

	-- Which look the hub uses: "clean" (Clean Pop Plaza: bubble centrepiece, soft pastels), "gumball"
	-- (giant gumball machine, candy colours) or "aero" (glossy bubble HQ).
	theme = "clean",
	themes = {
		aero = {
			-- Frutiger Aero: glossy white, aqua, sky blue and lime green, glass and bubbles
			tileA = rgb(252, 253, 255), -- checkerboard floor
			tileB = rgb(220, 243, 252),
			white = rgb(250, 251, 253),
			blue = rgb(20, 130, 235), -- glossy sky blue: the main accent
			lightBlue = rgb(110, 215, 245), -- aqua
			pink = rgb(120, 205, 45), -- (lime green; was pink before the aero look)
			lavender = rgb(160, 232, 248), -- (pale aqua stage)
			chrome = rgb(215, 225, 235),
			dome = rgb(170, 230, 255), -- the big glass bubble over the hub
			gold = rgb(255, 200, 60),
			glow = rgb(30, 110, 210), -- neon bits use dark colours (bright ones blow out to white)
			grass = rgb(115, 210, 70),
			padBase = rgb(248, 248, 250),
			pad = { rgb(230, 70, 90), rgb(230, 150, 20), rgb(40, 170, 90), rgb(130, 90, 230) },
			booths = { rgb(0, 185, 220), rgb(105, 195, 40), rgb(50, 130, 250) }, -- aqua, lime, sky blue
		},
		gumball = {
			-- Gumball Park: candy pink/white floor, a giant gumball machine, candy-cane fence, lollipop trees
			tileA = rgb(255, 248, 252),
			tileB = rgb(255, 214, 230),
			white = rgb(255, 252, 250),
			blue = rgb(230, 45, 70), -- (main accent: gumball-machine red)
			lightBlue = rgb(110, 220, 190), -- (mint)
			pink = rgb(255, 200, 50), -- (lemon yellow)
			lavender = rgb(255, 180, 210), -- (pink stage)
			chrome = rgb(255, 255, 255),
			dome = rgb(255, 205, 230), -- pink-tinted bubble
			gold = rgb(255, 200, 60),
			glow = rgb(190, 30, 90),
			grass = rgb(125, 215, 90),
			padBase = rgb(255, 252, 250),
			pad = { rgb(225, 45, 60), rgb(40, 120, 230), rgb(240, 185, 20), rgb(50, 175, 70) }, -- gumball colours
			booths = { rgb(255, 105, 170), rgb(70, 205, 165), rgb(245, 185, 40) }, -- pink, mint, lemon
			padGlow = { rgb(180, 20, 45), rgb(20, 90, 190), rgb(190, 125, 0), rgb(25, 140, 45) }, -- neon rings on the pad models
			boothGlow = { rgb(190, 30, 90), rgb(30, 156, 120), rgb(200, 140, 10) },
			gumballs = { rgb(230, 45, 60), rgb(40, 120, 230), rgb(255, 175, 0), rgb(50, 175, 70), rgb(255, 120, 190), rgb(255, 140, 40), rgb(150, 90, 230), rgb(255, 255, 255) },
		},
		clean = {
			-- Clean Pop Plaza: soft white, cream and light grey; pastel sky, mint, lilac and peach; bubble blue.
			-- Tints from art/hub_clean/*.bounds.json.
			floor = rgb(232, 228, 220), -- one studded floor, warm off-white (owner: classic Roblox studs; a bit darker than 245,243,238 under the sun)
			tileA = rgb(250, 251, 253), -- soft white
			tileB = rgb(232, 238, 246), -- light grey-blue
			white = rgb(250, 251, 253),
			cream = rgb(255, 246, 232),
			grey = rgb(225, 230, 238),
			blue = rgb(46, 155, 255), -- bubble blue: the main accent
			lightBlue = rgb(111, 191, 255), -- pastel sky
			pink = rgb(180, 156, 245), -- (lilac)
			lavender = rgb(255, 246, 232), -- (cream stage, part fallback)
			chrome = rgb(225, 230, 238),
			dome = rgb(190, 228, 255),
			gold = rgb(255, 170, 128), -- (peach)
			glow = rgb(20, 100, 200),
			grass = rgb(160, 225, 175), -- pastel mint grass
			padBase = rgb(250, 251, 253),
			pad = { rgb(111, 191, 255), rgb(111, 221, 182), rgb(180, 156, 245), rgb(255, 170, 128) }, -- sky, mint, lilac, peach
			padGlow = { rgb(20, 100, 200), rgb(15, 150, 112), rgb(100, 64, 210), rgb(210, 90, 40) },
			booths = { rgb(111, 191, 255), rgb(111, 221, 182), rgb(180, 156, 245) }, -- sky, mint, lilac
			boothGlow = { rgb(20, 100, 200), rgb(15, 150, 112), rgb(100, 64, 210) },
			-- tree tints: sky, mint, lilac, pale sky (the bounds' peach and white tints came out brown and grey in game)
			gumballs = { rgb(140, 203, 255), rgb(143, 230, 198), rgb(195, 174, 247), rgb(190, 228, 255) },
			grassSmooth = true, -- smooth pastel grass instead of the Grass material
		},
	},

	-- How the uploaded candy models are placed (Config/Models.hub; only used with the gumball theme;
	-- anything that didn't load falls back to the part-built pieces). Numbers from docs/art_review.md.
	models = {
		glass = rgb(235, 248, 255), glassTransparency = 0.6, -- globe and jar glass
		shine = rgb(255, 255, 255), shineTransparency = 0.15, -- the white highlight pieces (not Neon: it blows out)
		gumCore = rgb(143, 43, 88), -- the dark filler inside the globe and jar piles
		bannerRed = rgb(230, 45, 70), bannerTrim = rgb(255, 252, 250), bannerBolts = rgb(255, 200, 60),
		kerb = rgb(255, 252, 250), kerbBand = rgb(230, 45, 70),
		boothPad = rgb(255, 252, 250),
		chestGlow = rgb(200, 150, 20), chestGlowTransparency = 0.35,
		toppers = { "TopperBag", "TopperTicket", "TopperCrystal" }, -- booth 1 shop, 2 passes, 3 crystals
		topperScale = 1.5,
		cornerGumballs = { 1, 2, 3, 4 }, -- gumball colour per fence corner (red, blue, amber, green)
		lollipops = { "Swirl", "Ball", "Heart" },
		dressing = { count = 24, kinds = { "Gumdrop", "Sweet", "Cupcake" }, maxRadius = 92, minEdge = 61, size = { 0.8, 1.3 } },
	},

	-- Booth names (1 shop, 2 passes, 3 crystals) and their sign icons
	boothNames = { "SHOP", "PASSES", "CRYSTALS" },
	boothIcons = { "🛒", "🎟️", "💎" },

	-- CLEAN THEME POLISH (ServerScriptService/HubPolish.lua): ground paths and rings, props, a back
	-- colonnade, floating islands and a rainbow. Positions are x, z from the hub origin (floor top = 0);
	-- turn = degrees about the up axis. Each prop type is built by one function, so a modelled prop
	-- (hall facade, lamp, bench, planter) can replace the part-built one later.
	polish = {
		path = rgb(214, 234, 255), -- pale sky walkway
		pathTrim = rgb(111, 191, 255), -- sky kerb line along every path
		-- rectangles { x1, z1, x2, z2 }: from the spawn to the pads, across to the booths and the left stations
		paths = {
			{ -4, -17, 4, 29 }, -- spawn -> pads
			{ -29, -17, 29, -12 }, -- along the front of the pads
			{ -20, 1, 30, 7 }, -- the cross walk (left stations <-> booths)
			{ 26, -17, 30, 27 }, -- along the booth pads
			{ -20, -14, -16, 33 }, -- along the left stations, down to the gift
		},
		-- rings round stations { x, z, inner radius, outer radius }
		rings = {
			{ -38, 16, 11.2, 13 }, -- fountain
			{ -26, -6, 4.6, 6.2 }, -- rainbow bubble display
			{ -24, 40, 5, 6.6 }, -- gift
			{ 0, 34, 6.2, 7.8 }, -- spawn
			{ 34.25, -15, 5, 6.2 }, { 34.25, 4, 5, 6.2 }, { 34.25, 23, 5, 6.2 }, -- booth pads
		},
		ringColors = { rgb(150, 205, 255), rgb(200, 185, 250), rgb(255, 200, 170), rgb(150, 205, 255), rgb(150, 205, 255), rgb(150, 228, 200), rgb(200, 185, 250) },
		-- the round rug round the centrepiece stage (only the part in front of the back fence)
		rug = { centre = { 0, -45 }, bands = { { 14, 15.6, rgb(150, 205, 255) }, { 15.6, 16.4, rgb(250, 251, 253) }, { 16.4, 19.2, rgb(200, 185, 250) }, { 19.2, 20, rgb(250, 251, 253) } } },
		planters = { -- { x, z, turn }
			{ -14, 51, 0 }, { 14, 51, 0 }, { -38, 51, 0 }, { 38, 51, 0 },
			{ -26, -51, 0 }, { 26, -51, 0 }, { -42, -51, 0 }, { 42, -51, 0 },
			{ -51, -38, 90 }, { -51, 0, 90 }, { -51, 36, 90 },
			{ 51, -36, 90 }, { 51, -5.5, 90 }, { 51, 13.5, 90 }, { 51, 40, 90 },
			{ 9, 16, 90 }, { -9, 16, 90 }, -- beside the spawn walk
			{ 14, -8, 0 }, { -14, -8, 0 }, -- between the walks in front of the pads
		},
		bushColors = { rgb(140, 203, 255), rgb(143, 230, 198), rgb(195, 174, 247), rgb(255, 190, 210), rgb(255, 225, 150) },
		lamps = { -- { x, z }
			{ -6.5, 26 }, { 6.5, 26 }, { -31, -14.5 }, { 31, -14.5 },
			{ 33, -5.5 }, { 33, 13.5 }, { -14, -4 }, { -14, 20 }, { 40, 34 }, { -40, -32 }, { 24, -38 },
		},
		lampGlow = rgb(25, 85, 185), -- neon globe (dark-ish: bright neon blows out to white)
		lampGlass = rgb(200, 230, 255),
		gardens = { -- round flower beds { x, z, radius } in the empty corners
			{ 40, 42, 6 }, { -44, 43, 5 }, { -34, -41, 6 }, { 36, -41, 6 },
		},
		gardenTop = rgb(170, 230, 190),
		benches = { -- { x, z, turn } (turn 0 = seat faces +z)
			{ -12, 26, 90 }, { 12, 26, -90 }, { -30, 30, 45 }, { 20, 38, 180 },
		},
		-- the modelled back hall (Hub_CleanHall) replaces the colonnade when it loads; the back fence is left out where it stands
		hall = { x = 0, z = -52, scale = 1.25, glow = rgb(20, 100, 200) },
		-- the modelled leaderboard stand, turned to face the hub centre
		leaderboard = { x = 38, z = -33, title = "FASTEST CLEARS", rows = { "1.  ---   --:--", "2.  ---   --:--", "3.  ---   --:--" } },
		benchColors = { rgb(140, 203, 255), rgb(143, 230, 198), rgb(195, 174, 247), rgb(255, 190, 156) }, -- cushion tints
		colonnade = { z = -63, x1 = -48, x2 = 48, bays = 8, height = 24, column = rgb(250, 251, 253), arch = rgb(200, 185, 250), beam = rgb(255, 246, 232), band = rgb(111, 191, 255), crest = rgb(150, 205, 255) },
		islands = { -- { x, y, z, radius } from the hub origin, outside the glass
			{ -190, 25, -150, 22 }, { 210, 55, -120, 18 }, { -260, -15, 90, 26 }, { 240, 5, 170, 20 }, { 40, 70, -300, 24 }, { -120, 80, 280, 16 },
		},
		islandGrass = rgb(160, 225, 175),
		islandRock = rgb(215, 205, 235),
		rainbow = { centre = { 0, -125, -440 }, radius = 210, width = 9, transparency = 0.2, colors = { rgb(255, 150, 160), rgb(255, 200, 140), rgb(255, 240, 150), rgb(160, 230, 170), rgb(150, 200, 255), rgb(195, 170, 250) } },
	},

	-- Hub lighting (clean theme; this client only, while not in a run: Controllers/Lobby.lua).
	-- The popping room keeps its own lighting.
	lighting = {
		brightness = 1.8,
		clockTime = 14.2,
		latitude = 35,
		ambient = rgb(150, 160, 185),
		outdoor = rgb(165, 175, 200),
		colorShiftTop = rgb(255, 238, 215), -- slightly warm sun
		exposure = -0.1,
		shadowSoftness = 0.35,
		envDiffuse = 0.5,
		envSpecular = 0.5,
		bloom = { intensity = 0.15, size = 24, threshold = 1.2 }, -- (soft: the white floor blows out easily)
		colorCorrection = { saturation = 0.12, contrast = 0.04, brightness = 0, tint = rgb(255, 252, 246) },
		atmosphere = { density = 0.2, offset = 0.12, color = rgb(205, 230, 255), decay = rgb(150, 195, 240), glare = 0, haze = 0.4 },
	},

	-- How the Clean Pop Plaza models are placed (Config/Models.hubClean; only with the clean theme).
	-- reuse = candy sets (Config/Models.hub) the clean theme also uses, recoloured here.
	modelsClean = {
		reuse = { "Board", "Ground" },
		glass = rgb(190, 228, 255), glassTransparency = 0.5, -- the centrepiece's giant bubble (lower looks darker and turns the peach bubble tan)
		glassRim = rgb(255, 255, 255), glassRimTransparency = 0.35, -- a soft white Highlight outline round it
		coreTint = rgb(255, 235, 255), -- (multiplies the bubbles inside: a touch of pink takes the tan out of the peach one)
		shine = rgb(255, 255, 255), shineTransparency = 0.15,
		glow = rgb(20, 100, 200), -- neon rings and lines
		bannerBlue = rgb(46, 155, 255), bannerTrim = rgb(250, 251, 253), bannerBubbles = rgb(168, 216, 255), bannerBubblesGloss = 0.3,
		kerb = rgb(250, 251, 253), kerbBand = rgb(111, 191, 255), -- candy kerb, recoloured
		board = rgb(111, 191, 255), boardFace = rgb(250, 251, 253), -- candy board as plain sky blue with a white face
		trees = { "Ball", "Stack", "Cloud" },
		giftGlowTransparency = 0.35,
	},
}
Hub.colors = Hub.themes[Hub.theme] or Hub.themes.aero

return Hub
