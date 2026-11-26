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

	-- Which look the hub uses: "gumball" (giant gumball machine, candy colours) or "aero" (glossy bubble HQ).
	theme = "gumball",
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
}
Hub.colors = Hub.themes[Hub.theme] or Hub.themes.aero

return Hub
