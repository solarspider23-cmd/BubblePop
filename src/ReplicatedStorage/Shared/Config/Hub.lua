-- The lobby hub: where you spawn (third person). Classic studded Roblox bricks, no bubble wrap.
-- 4 pads: stand on one to make a group (up to maxPlayers); a countdown starts, the first player on
-- the pad can press Start; then the group goes into a fresh run in the popping room.
local function rgb(r, g, b)
	return { r, g, b }
end

return {
	origin = { 0, 0, 400 }, -- hub centre (far away from the popping room)
	size = 96, -- the studded baseplate is size x size studs
	spawn = { 0, 4, 30 }, -- from the origin: where players appear, facing the pads
	pads = {
		{ -30, -6 }, { -10, -6 }, { 10, -6 }, { 30, -6 }, -- x, z from the origin
	},
	padRadius = 5,
	maxPlayers = 4,
	countdown = 10, -- seconds before a pad starts on its own
	backToHubSeconds = 8, -- after the room is cleared
	rooms = { { name = "Starter Room" } }, -- what the pad owner can pick (more later)

	colors = {
		baseplate = rgb(163, 162, 165), -- classic Roblox grey
		border = rgb(13, 105, 172), -- bright blue bricks
		padBase = rgb(242, 243, 243),
		pad = { rgb(255, 89, 89), rgb(255, 176, 0), rgb(75, 151, 75), rgb(180, 128, 255) },
		booth = rgb(255, 255, 255),
		boothRoofShop = rgb(255, 176, 0),
		boothRoofPasses = rgb(196, 40, 28),
		sign = rgb(17, 17, 17),
	},
}
