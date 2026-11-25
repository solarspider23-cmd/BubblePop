-- Upgrades bought with coins in the shop. Each has levels; level 1 is what you start with.
-- To change prices or add a level, edit the lists (value and cost lists must be the same length).
--   values: what the upgrade gives at each level
--   costs:  coins to reach that level (level 1 is free: you start there)
return {
	order = { "bag", "popSpeed", "boots" },

	bag = {
		name = "Bigger Bag",
		describe = "Carry %d scraps",
		values = { 25, 40, 60, 90, 130, 180, 250, 350, 500, 750 },
		costs = { 0, 15, 40, 90, 180, 350, 650, 1200, 2200, 4000 },
	},
	popSpeed = {
		name = "Pop Speed",
		describe = "%.2fs per pop",
		values = { 0.56, 0.5, 0.45, 0.4, 0.35, 0.3, 0.26, 0.22 },
		costs = { 0, 30, 80, 180, 400, 800, 1500, 3000 },
	},
	boots = {
		-- 0 = walking doesn't pop. Otherwise the radius (studs) of floor wrap popped under you.
		name = "Spiky Boots",
		describe = "Pop radius %.1f",
		levelNames = { "No boots", "Spiky Boots", "Spikier Boots", "Mega Spikes" },
		values = { 0, 0.9, 1.3, 1.8 },
		costs = { 0, 150, 1000, 5000 },
	},
}
