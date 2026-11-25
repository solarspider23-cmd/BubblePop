-- Bubble variants: rare bubbles worth more coins. To add one, add an entry (rarest last).
--   chance: how often a bubble is this variant (1/50 = one in fifty), rolled again every time
--           a bubble grows back, so rare bubbles turn up in new spots
--   coins:  coins for popping it (normal bubbles give baseCoins)
--   look:   colour, see-through, shine; glow = ring behind it; sparkle = glitter; rainbow = cycles colours
return {
	baseCoins = 1,
	list = {
		{
			key = "Gold", chance = 1 / 200, coins = 5,
			color = { 255, 185, 25 }, transparency = 0.05, reflectance = 0.45,
			glow = { 255, 215, 80 }, sparkle = { 255, 240, 150 }, sparkleRate = 4,
		},
		{
			key = "Diamond", chance = 1 / 2000, coins = 25,
			color = { 170, 245, 255 }, transparency = 0.15, reflectance = 0.6,
			glow = { 120, 230, 255 }, sparkle = { 230, 255, 255 }, sparkleRate = 10,
		},
		{
			key = "Rainbow", chance = 1 / 20000, coins = 100,
			color = { 255, 90, 200 }, transparency = 0.05, reflectance = 0.4,
			glow = { 255, 255, 255 }, sparkle = { 255, 255, 255 }, sparkleRate = 16, rainbow = true,
		},
	},
}
