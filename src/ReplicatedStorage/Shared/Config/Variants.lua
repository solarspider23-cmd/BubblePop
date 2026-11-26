-- Bubble variants: rare bubbles worth more coins. To add one, add an entry (rarest last).
--   chance: how often a bubble is this variant (1/50 = one in fifty), rolled again every time
--           a bubble grows back, so rare bubbles turn up in new spots
--   coins:  money for popping it, in CENTS (normal bubbles give baseCoins = 1 cent)
--   maxPerRoom: (optional) never more than this many in one room
--   look:   colour, see-through, shine; glow = ring behind it; sparkle = glitter; rainbow = cycles colours
return {
	baseCoins = 1,
	-- Rare bubbles look normal until you get this close (studs), then they light up,
	-- so players can't spot them all from across the room and rush the good ones.
	revealDistance = 9,
	list = {
		-- Gold (1/300, 5 coins) removed 2026-11-25 by the owner; add it back here if wanted.
		{
			key = "Diamond", chance = 1 / 800, coins = 10, maxPerRoom = 10, -- about 4 per starter room, never more than 10
			color = { 170, 245, 255 }, transparency = 0.15, reflectance = 0.6,
			glow = { 120, 230, 255 }, sparkle = { 230, 255, 255 }, sparkleRate = 10,
		},
		{
			key = "Rainbow", chance = 1 / 10000, coins = 150, -- about 1 every other room
			color = { 255, 90, 200 }, transparency = 0.05, reflectance = 0.4,
			glow = { 255, 255, 255 }, sparkle = { 255, 255, 255 }, sparkleRate = 16, rainbow = true,
		},
	},
}
