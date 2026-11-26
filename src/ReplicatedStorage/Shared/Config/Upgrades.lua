-- Upgrades bought with coins in the shop. Each has levels; level 1 is what you start with.
-- To change prices or add a level, edit the lists (value and cost lists must be the same length).
--   values: what the upgrade gives at each level
--   costs:  money to reach that level, in CENTS (1500 = $15.00; level 1 is free: you start there)
-- Balance (2026-11-25): runs start fresh and the starter room is worth about $33 when cleared,
-- so one starter run buys roughly bag Lv5, Pop Speed Lv4, Tool Lv4 and Spiky Boots; the top
-- levels need the bigger rooms (or Robux skips).
return {
	order = { "bag", "popSpeed", "tool", "boots" },

	bag = {
		name = "Bigger Bag",
		describe = "Carry %d scraps",
		values = { 25, 40, 60, 90, 130, 180, 250, 350, 500, 750 },
		costs = { 0, 25, 60, 120, 220, 400, 700, 1200, 2000, 3500 }, -- $0.25 (one full bag) .. $35
	},
	popSpeed = {
		name = "Pop Speed",
		describe = "%.2fs per pop",
		values = { 0.56, 0.5, 0.45, 0.4, 0.35, 0.3, 0.26, 0.22 },
		costs = { 0, 50, 120, 250, 450, 800, 1400, 2500 }, -- $0.50 .. $25
	},
	tool = {
		-- bubbles one press pops: the one you aim at plus its nearest neighbours on the same wall/floor
		name = "Better Tool",
		describe = "%d bubbles per press",
		levelNames = { "Stick", "Fork", "Trident", "Rake", "Big Rake", "Roller", "Mega Roller" },
		values = { 1, 2, 3, 5, 7, 9, 13 },
		costs = { 0, 100, 300, 700, 1500, 3000, 6000 }, -- $1 .. $60
		spread = 2.6, -- extra bubbles must be within this many bubble-spacings of the aimed one
	},
	boots = {
		-- 0 = walking doesn't pop. Otherwise the radius (studs) of floor wrap popped under you.
		name = "Spiky Boots",
		describe = "Pop radius %.1f",
		levelNames = { "No boots", "Spiky Boots", "Spikier Boots", "Mega Spikes" },
		values = { 0, 0.9, 1.3, 1.8 },
		costs = { 0, 300, 1500, 5000 }, -- $3 .. $50
	},
}
