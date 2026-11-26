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
	maxPlayers = 4,
	countdown = 10, -- seconds before a pad starts on its own
	backToHubSeconds = 8, -- after the room is cleared
	rooms = { { name = "Starter Room" } }, -- what the pad owner can pick (more later)

	colors = {
		tileA = rgb(250, 250, 252), -- checkerboard floor
		tileB = rgb(222, 228, 238),
		white = rgb(248, 248, 250),
		blue = rgb(30, 140, 255), -- bubble blue: the main accent
		lightBlue = rgb(140, 215, 255),
		pink = rgb(255, 105, 180),
		lavender = rgb(185, 160, 255),
		gold = rgb(255, 200, 60),
		glow = rgb(30, 110, 210), -- neon bits use dark colours (bright ones blow out to white)
		grass = rgb(110, 200, 90),
		padBase = rgb(248, 248, 250),
		pad = { rgb(230, 70, 90), rgb(230, 150, 20), rgb(40, 170, 90), rgb(130, 90, 230) },
		booths = { rgb(60, 200, 140), rgb(160, 110, 255), rgb(255, 100, 170) }, -- mint, lavender, pink
	},
}
