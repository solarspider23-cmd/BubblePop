-- Every sound in the game. Ids from Roblox's own licensed library (creator "Roblox") or our
-- own sounds made by tools/make_sounds.py (synthesised from scratch, uploaded by the owner).
-- id 0 = use the built-in `file` stand-in.
--   volume, pitch: base values; pitchVar: random +- so repeats don't sound identical
--   gap: minimum seconds between two plays of the same sound
local Sounds = {
	pop = { id = 73858435411469, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.9, pitch = 1, pitchVar = 0.1 },
	stompPop = { id = 73858435411469, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.6, pitch = 0.85, pitchVar = 0.15, gap = 0.05 },
	press = { id = 101809582107091, file = "", volume = 0.35, pitch = 1, pitchVar = 0.05 }, -- squeeze during the press
	regrow = { id = 0, file = "", volume = 0.2, pitch = 1.6, pitchVar = 0.1 },
	otherPop = { id = 73858435411469, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.35, pitch = 1, pitchVar = 0.15, range = 60, gap = 0.03 },
}

-- Test-room sound picker: press 1-9 in game to swap the pop sound and hear the difference.
-- ids = several takes of the same pop; a random one plays each time (never the same twice in a row).
-- "Pro" sounds are from Pro Sound Effects, Roblox's licensed sound library (free to use in Roblox games),
-- pitched up so a balloon pop sounds like a small bubble.
Sounds.popOptions = {
	{ name = "Tiny (ours, your pick)", id = 73858435411469, pitch = 1 },
	{ name = "Tiny+ (ours, 4 takes)", ids = { 117117622350047, 114787371042780, 139992956267612, 88845581321578 }, pitch = 1 },
	{ name = "Snap (ours, 4 takes)", ids = { 131306854348834, 131356068771467, 104585229360428, 112355204599573 }, pitch = 1 },
	{ name = "Pock (ours, 4 takes)", ids = { 89865884276766, 133833172142947, 75384767854831, 108560738872232 }, pitch = 1 },
	{ name = "Pro balloon, small", ids = { 9113263454, 9113263444, 9113263649 }, pitch = 2.4 },
	{ name = "Pro balloon, tiny", ids = { 9113263454, 9113263444, 9113263649 }, pitch = 3.2 },
	{ name = "Pro balloon, medium", ids = { 9113263454, 9113263444, 9113263649 }, pitch = 1.7 },
	{ name = "Roblox Cute Pop", id = 15675055424, pitch = 1 },
	{ name = "Tiny+ and Snap mixed", ids = { 117117622350047, 114787371042780, 131306854348834, 131356068771467, 139992956267612, 104585229360428 }, pitch = 1 },
}

return Sounds
