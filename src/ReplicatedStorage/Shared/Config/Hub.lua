-- The lobby hub: where you spawn (third person). A raised tiled plaza (studded tiles, no bubble wrap):
-- Bubble HQ with the floating logo at the back, the 4 play pads in front of it, how-to-play board,
-- bubble fountain and a bubble display on the left, 3 booths on the right, a free gift chest front left.
-- 4 pads: stand on one to make a group (up to maxPlayers); a countdown starts, the first player on
-- the pad can press Start; then the group goes into a fresh run in the popping room.
local function rgb(r, g, b)
	return { r, g, b }
end

return {
	origin = { 0, 0, 400 }, -- hub centre (far away from the popping room)
	size = 112, -- the plaza is size x size studs (8 x 8 tiles)
	spawn = { 0, 4, 34 }, -- from the origin: where players appear, facing the pads
	pads = {
		{ -21, -28 }, { -7, -28 }, { 7, -28 }, { 21, -28 }, -- x, z from the origin
	},
	padSize = { 12, 9 }, -- each play pad is a rectangle, x by z studs
	booths = { { 45, -14 }, { 45, 4 }, { 45, 22 } }, -- right side, evenly spaced, facing the middle
	dome = { radius = 100, centreY = -20 }, -- the glass bubble the whole hub sits in
	maxPlayers = 4,
	countdown = 10, -- seconds before a pad starts on its own
	backToHubSeconds = 8, -- after the room is cleared
	rooms = { { name = "Starter Room" } }, -- what the pad owner can pick (more later)

	colors = {
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
}
