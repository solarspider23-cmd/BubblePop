-- Every sound in the game. Ids from Roblox's own licensed library (creator "Roblox") or our
-- own sounds made by tools/make_sounds.py (synthesised from scratch, uploaded by the owner).
-- id 0 = use the built-in `file` stand-in.
--   volume, pitch: base values; pitchVar: random +- so repeats don't sound identical
--   gap: minimum seconds between two plays of the same sound
local Sounds = {
	pop = { id = 73858435411469, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.9, pitch = 1, pitchVar = 0.1 },
	stompPop = { id = 73858435411469, file = "rbxasset://sounds/volume_slider.ogg", volume = 0.6, pitch = 0.85, pitchVar = 0.15, gap = 0.05 },
	-- squeeze during the press. fit + length (seconds): stretched to end exactly at the pop.
	press = { id = 101809582107091, file = "", volume = 0.35, pitch = 1, pitchVar = 0.05, fit = true, length = 0.45 },
	rarePop = { id = 127645268874265, file = "", volume = 0.6, pitch = 1.1, pitchVar = 0.05 }, -- chime when you pop a rare bubble (Roblox CoinTransfer_01)
	sell = { id = 127645268874265, file = "", volume = 0.9, pitch = 0.9, pitchVar = 0 }, -- selling your bag at the recycler
	reveal = { id = 127645268874265, file = "", volume = 0.35, pitch = 1.6, pitchVar = 0.05, range = 30 }, -- a rare bubble lights up as you get close
	chestOpen = { id = 127645268874265, file = "", volume = 0.3, pitch = 1.3, pitchVar = 0.05 }, -- the hub's free gift chest opens as you walk up (same licensed chime)
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

-- Test-room squeeze picker: press K in game to step through these.
Sounds.squeezeOptions = {
	{ name = "Old creak", id = 101809582107091, fit = true, length = 0.45 },
	{ name = "Creak (new, 3 takes)", ids = { 94185270716416, 114510604286791, 108163865453732 }, fit = true, length = 0.42 },
	{ name = "Rubber squeak (ours)", ids = { 70521663961841, 121451753806522, 116362971844470 }, fit = true, length = 0.42 },
	{ name = "Plastic crinkle (ours)", ids = { 137414476354317, 122416838324018, 93352862992156 }, fit = true, length = 0.42 },
	{ name = "Crinkle + squeak (ours)", ids = { 135069387407627, 80768085619573, 89997755256426 }, fit = true, length = 0.42 },
	{ name = "Pro rubber squeaks", ids = { 9118742154, 9118741970, 9118742207 }, pitch = 1.2, volume = 0.3 },
	{ name = "Pro squeeze toy", ids = { 9125994570, 9125994543, 9125994785 }, pitch = 1.3, volume = 0.3 },
	{ name = "No squeeze sound", id = 0 },
}

return Sounds
