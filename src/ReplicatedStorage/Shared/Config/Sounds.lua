-- Every sound in the game. Ids only from Roblox's own licensed libraries
-- (creator "Roblox" or "APMOfficial"). id 0 = use the built-in `file` stand-in.
--   volume, pitch: base values; pitchVar: random +- so repeats don't sound identical
--   gap: minimum seconds between two plays of the same sound
return {
	pop = { id = 0, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.8, pitch = 1.5, pitchVar = 0.12 },
	stompPop = { id = 0, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.6, pitch = 1.25, pitchVar = 0.15, gap = 0.05 },
	press = { id = 0, file = "", volume = 0.3, pitch = 1, pitchVar = 0.05 }, -- squeeze creak during the press
	regrow = { id = 0, file = "", volume = 0.2, pitch = 1.6, pitchVar = 0.1 },
	otherPop = { id = 0, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.35, pitch = 1.4, pitchVar = 0.15, range = 60, gap = 0.03 },
}
