-- Every sound in the game. Ids from Roblox's own licensed library (creator "Roblox") or our
-- own sounds made by tools/make_sounds.py (synthesised from scratch, uploaded by the owner).
-- id 0 = use the built-in `file` stand-in.
--   volume, pitch: base values; pitchVar: random +- so repeats don't sound identical
--   gap: minimum seconds between two plays of the same sound
local Sounds = {
	pop = { id = 82196317050694, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.9, pitch = 1, pitchVar = 0.1 },
	stompPop = { id = 76082160863455, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.6, pitch = 1, pitchVar = 0.15, gap = 0.05 },
	press = { id = 101809582107091, file = "", volume = 0.35, pitch = 1, pitchVar = 0.05 }, -- squeeze during the press
	regrow = { id = 0, file = "", volume = 0.2, pitch = 1.6, pitchVar = 0.1 },
	otherPop = { id = 82196317050694, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.35, pitch = 1, pitchVar = 0.15, range = 60, gap = 0.03 },
}

-- Test-room sound picker: press 1-6 in game to swap the pop sound and hear the difference.
Sounds.popOptions = {
	{ name = "Crisp (ours)", id = 82196317050694, pitch = 1 },
	{ name = "Juicy (ours)", id = 131774954529004, pitch = 1 },
	{ name = "Tiny (ours)", id = 73858435411469, pitch = 1 },
	{ name = "Big (ours)", id = 76082160863455, pitch = 1 },
	{ name = "Roblox Cute Pop", id = 15675055424, pitch = 1 },
	{ name = "Roblox Pinball Button", id = 16480556621, pitch = 1.1 },
}

return Sounds
