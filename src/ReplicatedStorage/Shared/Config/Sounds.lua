-- Every sound in the game. Ids only from Roblox's own licensed libraries
-- (creator "Roblox" or "APMOfficial"). id 0 = use the built-in `file` stand-in.
--   volume, pitch: base values; pitchVar: random +- so repeats don't sound identical
--   gap: minimum seconds between two plays of the same sound
-- Candidates found 2026-11-24 (all creator Roblox; not auditioned yet):
--   15675055424 Roblox_UI_Cute_Pop, 17208204604 Roblox GUI - Bubble,
--   16480574637 Pinball_Bumper_Full_01, 16480568148 Pinball_Bumper_Soft_Click_05,
--   16480556621 Pinball_Large_Plastic_Button_Press_01, 16480550203 Pinball_Tiny_Button_Press_03,
--   16480576087 Pinball_Ball_Plastic_Slide_04 (press), 127645268874265 CoinTransfer_01 (coins),
--   17208353912 Roblox GUI - Negative (bag full)
return {
	pop = { id = 15675055424, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.9, pitch = 1, pitchVar = 0.1 },
	stompPop = { id = 15675055424, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.6, pitch = 0.85, pitchVar = 0.15, gap = 0.05 },
	press = { id = 16480576087, file = "", volume = 0.25, pitch = 1.2, pitchVar = 0.05 }, -- squeeze during the press
	regrow = { id = 0, file = "", volume = 0.2, pitch = 1.6, pitchVar = 0.1 },
	otherPop = { id = 15675055424, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.35, pitch = 1, pitchVar = 0.15, range = 60, gap = 0.03 },
}
