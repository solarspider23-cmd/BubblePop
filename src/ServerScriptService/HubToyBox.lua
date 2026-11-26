-- TOY BOX lobby (clean theme with Config/Hub.lua useModels = false; owner 2026-11-26): every piece is
-- plain Roblox parts (blocks, cylinders, balls, wedges), chunky, studded Plastic tops, in the Toy Box
-- colours from Config/Hub.lua `toybox` (sky / butter / coral, mint for plants, warm white trim).
-- Same layout and positions as the clean theme. Hub.lua passes its helpers in `h`.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HubConfig = require(ReplicatedStorage:WaitForChild("Shared").Config.Hub)

local ToyBox = {}

local T = HubConfig.toybox
local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local SKY, BUTTER, CORAL, MINT, TRIM = color(T.sky), color(T.butter), color(T.coral), color(T.mint), color(T.trim)
local INK = color(T.ink)
local PLASTIC = Enum.Material.Plastic
local CYL, BALL = Enum.PartType.Cylinder, Enum.PartType.Ball
local UP = CFrame.Angles(0, 0, math.pi / 2) -- cylinder standing up
local FACE_Z = CFrame.Angles(0, math.pi / 2, 0) -- cylinder as a disc facing +Z

function ToyBox.build(h)
	local at, part, folder = h.at, h.part, h.folder
	local S = HubConfig.size
	local half = S / 2

	-- a Plastic block; studs = studded top
	local function blk(name: string, size: Vector3, cf: any, col: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.mat = opts.mat or PLASTIC
		return part(name, size, cf, col, opts)
	end
	local function cyl(name: string, pos: Vector3, d: number, ht: number, col: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.shape = CYL
		return blk(name, Vector3.new(ht, d, d), CFrame.new(pos) * UP, col, opts)
	end
	local function ball(name: string, pos: Vector3, d: number, col: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.shape = BALL
		return blk(name, Vector3.new(d, d, d), pos, col, opts)
	end
	local function disc(name: string, cf: CFrame, d: number, th: number, col: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.shape = CYL
		return blk(name, Vector3.new(th, d, d), cf * FACE_Z, col, opts)
	end
	-- a wedge: high at its +Z side, sloping down to its -Z side
	local function wedge(name: string, size: Vector3, cf: CFrame, col: Color3): WedgePart
		local w = Instance.new("WedgePart")
		w.Name = name
		w.Anchored = true
		w.Size = size
		w.CFrame = cf
		w.Color = col
		w.Material = PLASTIC
		w.TopSurface = Enum.SurfaceType.Smooth
		w.BottomSurface = Enum.SurfaceType.Smooth
		w.Parent = folder
		return w
	end
	-- big bold text on a part's face
	local function write(p: BasePart, face: Enum.NormalId, text: string, col: Color3?, ppS: number?)
		return h.sign(p, face, text, col or TRIM, INK, ppS or 40)
	end

	------------------------------------------------------------ island, plaza, fence, spawn
	local isl = HubConfig.island
	cyl("Grass", at(0, -5.5, 0), isl.radius * 2, 5, MINT, { mat = Enum.Material.SmoothPlastic, gloss = 0 })
	cyl("IslandRim", at(0, -8.6, 0), isl.radius * 2 + 1.5, 1.4, TRIM, { shadow = false })
	for k, layer in { { 0.96, 7 }, { 0.82, 8 }, { 0.64, 8 }, { 0.44, 8 }, { 0.24, 7 } } do -- stepped warm stone
		local y = -9.3 - (k - 0.5) * 7.6
		cyl("IslandRock", at(0, y, 0), isl.radius * 2 * layer[1], layer[2], color(T.stone[k] or T.stone[#T.stone]), { shadow = false })
	end
	blk("Plaza", Vector3.new(S, 2.8, S), at(0, -1.6, 0), TRIM)
	blk("PlazaBand", Vector3.new(S + 0.8, 1, S + 0.8), at(0, -2.4, 0), SKY)
	blk("Floor", Vector3.new(S, 0.2, S), at(0, -0.1, 0), color(HubConfig.colors.floor), { studs = true, shadow = false })

	-- fence: chunky block posts with coloured caps, two rails; an invisible wall so nobody climbs out
	local edge = half - 1
	local caps = { CORAL, SKY, BUTTER }
	for _, side in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
		local alongX = side[2] ~= 0
		local step = edge / 7
		for k = -7, 7 do
			local u = k * step
			local x, z = alongX and u or side[1] * edge, alongX and side[2] * edge or u
			blk("FencePost", Vector3.new(1.4, 3.4, 1.4), at(x, 1.7, z), TRIM)
			blk("FenceCap", Vector3.new(1.9, 0.7, 1.9), at(x, 3.75, z), caps[(k + 8) % 3 + 1], { studs = true })
		end
		local rail = alongX and Vector3.new(S - 2, 0.6, 0.6) or Vector3.new(0.6, 0.6, S - 2)
		local rx, rz = alongX and 0 or side[1] * edge, alongX and side[2] * edge or 0
		blk("FenceRail", rail, at(rx, 2.7, rz), SKY)
		blk("FenceRail", rail, at(rx, 1.3, rz), SKY)
		local wall = alongX and Vector3.new(S - 2, 3.4, 0.8) or Vector3.new(0.8, 3.4, S - 2)
		h.blocker("FenceWall", wall, at(rx, 1.7, rz))
	end

	-- spawn pad: a chunky studded butter square on a trim base
	local sp = at(HubConfig.spawn[1], 0, HubConfig.spawn[3])
	blk("SpawnBase", Vector3.new(10, 0.4, 10), sp + Vector3.new(0, 0.2, 0), TRIM)
	blk("SpawnPad", Vector3.new(8.4, 0.6, 8.4), sp + Vector3.new(0, 0.3, 0), BUTTER, { studs = true })

	------------------------------------------------------------ centrepiece: stacked pedestal with a big bubble
	local C = T.centre
	local cz = C.z
	local y = 0
	for _, tier in C.tiers do
		cyl("CentreTier", at(0, y + tier[2] / 2, cz), tier[1], tier[2], color(tier[3]))
		y += tier[2]
	end
	local bubbleY = y + C.bubble / 2 - 1.2
	local bubble = ball("CentreBubble", at(0, bubbleY, cz), C.bubble, color(T.glass.colour), { transparency = T.glass.transparency, mat = Enum.Material.SmoothPlastic, gloss = 0.15, shadow = false })
	local rim = Instance.new("Highlight") -- a soft white edge so the bubble reads against the sky
	rim.FillTransparency = 1
	rim.OutlineColor = TRIM
	rim.OutlineTransparency = 0.3
	rim.DepthMode = Enum.HighlightDepthMode.Occluded
	rim.Parent = bubble
	ball("BubbleShine", at(-C.bubble * 0.2, bubbleY + C.bubble * 0.24, cz + C.bubble * 0.3), C.bubble * 0.16, TRIM, { solid = false, shadow = false })
	ball("BubbleShine2", at(-C.bubble * 0.31, bubbleY + C.bubble * 0.08, cz + C.bubble * 0.36), C.bubble * 0.07, TRIM, { solid = false, shadow = false })
	local stageTop = C.tiers[1][2]
	for _, s in C.small do -- a few chunky bubbles round the stage
		ball("StageBubble", at(s[1], stageTop + s[4] / 2 - 0.2, cz + s[3]), s[4], color(s[5]))
	end

	-- BUBBLE POP sign block on two posts in front of the centrepiece
	local L = T.logo
	for _, sx in { -1, 1 } do
		local px = sx * (L.w / 2 - 4)
		blk("LogoPost", Vector3.new(1.6, L.y - L.h / 2, 1.6), at(px, (L.y - L.h / 2) / 2, L.z - 0.4), color(L.posts))
	end
	blk("LogoFrame", Vector3.new(L.w + 1.4, L.h + 1.4, 1.2), at(0, L.y, L.z - 0.4), color(L.frame), { studs = true })
	local logo = blk("Logo", Vector3.new(L.w, L.h, 1.2), at(0, L.y, L.z), color(L.face))
	write(logo, Enum.NormalId.Back, "BUBBLE POP", TRIM, 11)
	for _, sx in { -1, 1 } do -- butter end bubbles
		ball("LogoBall", at(sx * (L.w / 2 + 0.9), L.y, L.z), 3.2, BUTTER)
	end

	------------------------------------------------------------ back building (frames the centrepiece)
	local B = T.back
	local g = -3 -- grass top
	local bz = B.z
	blk("BackWall", Vector3.new(B.wallW, B.wallH, 4), at(0, g + B.wallH / 2, bz), TRIM)
	blk("BackBand", Vector3.new(B.wallW + 0.4, 1.4, 4.4), at(0, g + B.wallH - 3, bz), CORAL)
	blk("BackCap", Vector3.new(B.wallW + 1.2, 1, 5), at(0, g + B.wallH + 0.5, bz), SKY, { studs = true })
	-- a big three-band arch (discs half hidden behind the wall) behind the bubble
	local arcY = g + B.wallH
	disc("BackArch", CFrame.new(at(0, arcY, bz - 2.2)), 38, 1, SKY)
	disc("BackArch", CFrame.new(at(0, arcY, bz - 1.6)), 31, 1, BUTTER)
	disc("BackArch", CFrame.new(at(0, arcY, bz - 1.0)), 24, 1, CORAL)
	disc("BackArch", CFrame.new(at(0, arcY, bz - 0.4)), 17, 1, TRIM)
	for _, wx in { -15, -8, 8, 15 } do -- round windows
		disc("BackWindow", CFrame.new(at(wx, g + 9, bz + 2)), 4, 0.4, SKY)
		disc("BackWindowRim", CFrame.new(at(wx, g + 9, bz + 1.95)), 4.8, 0.4, BUTTER)
	end
	for _, sx in { -1, 1 } do
		local tx = sx * B.towerX
		cyl("Tower", at(tx, g + B.towerH / 2, bz), B.towerD, B.towerH, SKY)
		cyl("TowerBand", at(tx, g + 2, bz), B.towerD + 0.8, 1.2, TRIM)
		cyl("TowerBand", at(tx, g + B.towerH - 2, bz), B.towerD + 0.8, 1.2, CORAL)
		cyl("TowerTop", at(tx, g + B.towerH + 0.4, bz), B.towerD + 1.2, 0.8, TRIM)
		ball("TowerDome", at(tx, g + B.towerH + 0.6, bz), B.towerD, BUTTER)
		ball("TowerBall", at(tx, g + B.towerH + B.towerD / 2 + 1.2, bz), 2.4, CORAL)
		disc("TowerWindow", CFrame.new(at(tx, g + B.towerH - 8, bz + B.towerD / 2 - 0.1)), 3.6, 0.6, TRIM)
		-- wing: a butter block with a coral gable roof
		local wx = sx * B.wingX
		blk("Wing", Vector3.new(B.wingW, B.wingH, 10), at(wx, g + B.wingH / 2, bz), BUTTER)
		blk("WingBase", Vector3.new(B.wingW + 0.6, 1.4, 10.6), at(wx, g + 0.7, bz), TRIM)
		blk("WingEave", Vector3.new(B.wingW + 1, 0.6, 11), at(wx, g + B.wingH + 0.3, bz), TRIM)
		wedge("WingRoof", Vector3.new(B.wingW + 1, 4, 5.5), CFrame.new(at(wx, g + B.wingH + 2.6, bz + 2.75)) * CFrame.Angles(0, math.pi, 0), CORAL)
		wedge("WingRoof", Vector3.new(B.wingW + 1, 4, 5.5), CFrame.new(at(wx, g + B.wingH + 2.6, bz - 2.75)), CORAL)
		blk("WingDoor", Vector3.new(4, 6, 0.4), at(wx, g + 3, bz + 5.1), SKY)
		ball("WingKnob", at(wx + 1.2, g + 3, bz + 5.4), 0.6, BUTTER, { solid = false })
	end

	------------------------------------------------------------ pads (Pad1-4 stay invisible standing parts)
	local w, d = HubConfig.padSize[1], HubConfig.padSize[2]
	for i, xz in HubConfig.pads do
		local x, z = xz[1], xz[2]
		local col = color(T.padColours[i] or T.padColours[1])
		blk("PadBase", Vector3.new(w + 2, 0.5, d + 2), at(x, 0.25, z), TRIM)
		blk("PadTop", Vector3.new(w, 0.7, d), at(x, 0.35, z), col, { studs = true })
		-- raised rim on the back and sides (the front stays open towards the spawn)
		blk("PadRim", Vector3.new(w + 2, 1.1, 1), at(x, 0.55, z - d / 2 - 0.5), col, { studs = true })
		for _, sx in { -1, 1 } do
			blk("PadRim", Vector3.new(1, 1.1, d + 1), at(x + sx * (w / 2 + 0.5), 0.55, z + 0.5 - 0.5), col, { studs = true })
		end
		local pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, 0.45, z), col, { transparency = 1, solid = false, shadow = false })
		-- block sign behind the pad: big "PAD n", the player count under it
		local sz = z - d / 2 - 2
		for _, sx in { -1, 1 } do
			blk("PadSignPost", Vector3.new(1, 5, 1), at(x + sx * 3.4, 2.5, sz), TRIM)
		end
		local board = blk("PadSign", Vector3.new(8.4, 3.6, 0.8), at(x, 5.6, sz), col)
		blk("PadSignCap", Vector3.new(9, 0.6, 1.2), at(x, 7.7, sz), TRIM, { studs = true })
		local t = write(board, Enum.NormalId.Back, ("PAD %d"):format(i), TRIM, 40)
		t.Size = UDim2.fromScale(0.96, 0.6)
		t.Position = UDim2.fromScale(0.02, 0)
		local cnt = t:Clone()
		cnt.Text = ("0/%d"):format(HubConfig.maxPlayers)
		cnt.Size = UDim2.fromScale(0.9, 0.36)
		cnt.Position = UDim2.fromScale(0.05, 0.6)
		cnt.Parent = t.Parent
		h.padText[i] = t
		h.padCount[i] = cnt
		pad:SetAttribute("Index", i)
		pad:SetAttribute("Members", 0)
		h.padParts[i] = pad
	end

	------------------------------------------------------------ booths: block stalls with striped wedge awnings
	for i, s in HubConfig.booths do
		local accent = color(T.boothColours[i] or T.boothColours[1])
		local pos = at(s[1], 0, s[2])
		local f = CFrame.lookAt(pos, pos - Vector3.xAxis) -- open side (local -Z) faces the middle
		local function piece(name, size, x, yy, zz, c, o)
			return blk(name, size, f * CFrame.new(x, yy, zz), c, o)
		end
		piece("BoothFloor", Vector3.new(12, 0.6, 10), 0, 0.3, 0, TRIM, { studs = true })
		piece("BoothBack", Vector3.new(12, 8.4, 1), 0, 4.8, 4.5, accent)
		for _, sx in { -1, 1 } do
			piece("BoothSide", Vector3.new(1, 8.4, 9), sx * 5.5, 4.8, 0, accent)
			piece("BoothPost", Vector3.new(1.4, 8.6, 1.4), sx * 5.6, 4.9, -4.4, TRIM)
		end
		piece("BoothCounter", Vector3.new(10, 3.4, 2), 0, 2.3, -3.6, accent)
		piece("BoothCounterTop", Vector3.new(11, 0.5, 2.6), 0, 4.25, -3.6, TRIM, { studs = true })
		piece("BoothRoof", Vector3.new(13, 1, 10.6), 0, 9.6, 0, TRIM, { studs = true })
		for k = 0, 4 do -- striped awning, sloping down to the front
			local c = k % 2 == 0 and accent or TRIM
			wedge("BoothAwning", Vector3.new(2.6, 1.8, 3), f * CFrame.new(-5.2 + k * 2.6, 8.4, -6.4), c)
		end
		-- shelf with a few chunky goods
		piece("BoothShelf", Vector3.new(9, 0.5, 1.4), 0, 6, 3.4, TRIM)
		for k, c in { CORAL, SKY, BUTTER } do
			ball("BoothGood", (f * CFrame.new(-3 + (k - 1) * 3, 7, 3.4)).Position, 1.6, c, { solid = false })
		end
		-- sign block on the roof
		local name = HubConfig.boothNames and HubConfig.boothNames[i] or "COMING SOON"
		local plate = piece("BoothSign", Vector3.new(10, 2.6, 0.8), 0, 11.5, -2, accent)
		piece("BoothSignCap", Vector3.new(10.6, 0.5, 1.2), 0, 13.05, -2, TRIM, { studs = true })
		write(plate, Enum.NormalId.Front, name, TRIM, 40)
		-- pad in front
		local po = f * CFrame.new(0, 0, -9.75)
		blk("BoothPadBase", Vector3.new(8, 0.3, 8), po * CFrame.new(0, 0.15, 0), TRIM)
		blk("BoothPad", Vector3.new(6.4, 0.45, 6.4), po * CFrame.new(0, 0.22, 0), accent, { studs = true })
	end

	------------------------------------------------------------ gift box: block, ribbon bands, bow
	do
		local pos = at(-24, 0, 40)
		local f = CFrame.lookAt(pos, at(-14, 0, 20))
		local function piece(name, size, x, yy, zz, c, o)
			return blk(name, size, f * CFrame.new(x, yy, zz), c, o)
		end
		piece("GiftBox", Vector3.new(5, 4, 5), 0, 2, 0, CORAL)
		piece("GiftLid", Vector3.new(5.6, 1.2, 5.6), 0, 4.6, 0, CORAL, { studs = true })
		piece("GiftRibbon", Vector3.new(1.1, 4.02, 5.04), 0, 2, 0, BUTTER)
		piece("GiftRibbon", Vector3.new(5.04, 4.02, 1.1), 0, 2, 0, BUTTER)
		piece("GiftRibbonLid", Vector3.new(1.1, 1.22, 5.64), 0, 4.6, 0, BUTTER)
		piece("GiftRibbonLid", Vector3.new(5.64, 1.22, 1.1), 0, 4.6, 0, BUTTER)
		for _, sx in { -1, 1 } do
			ball("GiftBow", (f * CFrame.new(sx * 1, 5.8, 0)).Position, 1.8, BUTTER)
		end
		local knot = ball("GiftKnot", (f * CFrame.new(0, 5.7, 0)).Position, 1.1, BUTTER)
		local light = Instance.new("PointLight")
		light.Color = color(T.lampLight)
		light.Range = 10
		light.Brightness = 1
		light.Parent = knot
		h.label(knot, "FREE GIFT!", 3.5, 9, 2.2, nil, "🎁", CORAL)
	end

	------------------------------------------------------------ how-to-play board
	do
		local o = CFrame.lookAt(at(-46, 0, -20), at(0, 0, 4))
		local function piece(name, size, x, yy, zz, c, op)
			return blk(name, size, o * CFrame.new(x, yy, zz), c, op)
		end
		for _, sx in { -1, 1 } do
			piece("BoardLeg", Vector3.new(1.2, 6, 1.2), sx * 5.6, 3, 0.4, TRIM)
		end
		piece("BoardFrame", Vector3.new(14, 10, 0.8), 0, 7, 0.4, SKY)
		local face = piece("Board", Vector3.new(12.8, 8.8, 0.3), 0, 6.8, -0.1, TRIM)
		piece("BoardCap", Vector3.new(14.6, 0.8, 1.4), 0, 12.4, 0.4, CORAL, { studs = true })
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 30
		gui.LightInfluence = 0
		local title = Instance.new("TextLabel")
		title.Size = UDim2.fromScale(0.9, 0.22)
		title.Position = UDim2.fromScale(0.05, 0.04)
		title.BackgroundTransparency = 1
		title.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
		title.TextScaled = true
		title.Text = "HOW TO PLAY"
		title.TextColor3 = CORAL
		title.Parent = gui
		local body = Instance.new("TextLabel")
		body.Size = UDim2.fromScale(0.86, 0.68)
		body.Position = UDim2.fromScale(0.07, 0.28)
		body.BackgroundTransparency = 1
		body.FontFace = Font.fromEnum(Enum.Font.FredokaOne)
		body.TextScaled = true
		body.TextXAlignment = Enum.TextXAlignment.Left
		body.TextYAlignment = Enum.TextYAlignment.Top
		body.TextColor3 = INK
		body.Text = "1. Stand on a pad with your friends\n2. Pop every bubble in the room\n3. Sell your scraps at the chute\n4. Upgrade and clear it FAST!"
		body.Parent = gui
		gui.Parent = face
	end

	------------------------------------------------------------ block fountain (the fountain spot)
	do
		local fp = at(-38, 0, 16)
		cyl("FountainBase", fp + Vector3.new(0, 0.6, 0), 21, 1.2, TRIM)
		cyl("FountainWall", fp + Vector3.new(0, 1.6, 0), 20, 1.4, SKY) -- sky rim round brim-full water
		cyl("Water", fp + Vector3.new(0, 2.15, 0), 18.4, 0.6, color(T.water), { transparency = 0.15, solid = false, mat = Enum.Material.SmoothPlastic, gloss = 0.2 })
		blk("FountainBlock", Vector3.new(4.4, 3, 4.4), fp + Vector3.new(0, 3.2, 0), BUTTER, { studs = true })
		blk("FountainBlock2", Vector3.new(3, 2.4, 3), fp + Vector3.new(0, 5.9, 0), CORAL, { studs = true })
		local top = ball("FountainBall", fp + Vector3.new(0, 8.6, 0), 3.4, SKY)
		local jet = Instance.new("ParticleEmitter") -- water spraying up and falling back
		jet.EmissionDirection = Enum.NormalId.Top
		jet.Rate = 40
		jet.Lifetime = NumberRange.new(1.1, 1.3)
		jet.Speed = NumberRange.new(11, 13)
		jet.SpreadAngle = Vector2.new(22, 22)
		jet.Acceleration = Vector3.new(0, -26, 0)
		jet.Size = NumberSequence.new(0.6, 0.3)
		jet.Transparency = NumberSequence.new(0.2, 0.6)
		jet.Color = ColorSequence.new(Color3.fromRGB(180, 220, 250))
		jet.Parent = top
	end

	------------------------------------------------------------ ball pit (the old display spot)
	do
		local bp = at(-26, 0, -6)
		local cols = { CORAL, SKY, BUTTER }
		for k, side in { { 0, 1 }, { 0, -1 }, { 1, 0 }, { -1, 0 } } do
			local alongX = side[2] ~= 0
			local size = alongX and Vector3.new(8, 2, 0.8) or Vector3.new(0.8, 2, 6.4)
			blk("PitWall", size, bp + Vector3.new(side[1] * 3.6, 1, side[2] * 3.6), cols[(k - 1) % 3 + 1], { studs = true })
		end
		blk("PitFloor", Vector3.new(6.4, 0.4, 6.4), bp + Vector3.new(0, 0.2, 0), TRIM)
		local rng = Random.new(4)
		for _ = 1, 34 do
			local p = bp + Vector3.new(rng:NextNumber(-2.5, 2.5), rng:NextNumber(0.9, 1.9), rng:NextNumber(-2.5, 2.5))
			ball("PitBall", p, 1.4, cols[rng:NextInteger(1, 3)], { solid = false, shadow = false })
		end
	end

	------------------------------------------------------------ leaderboard
	local lb = HubConfig.polish.leaderboard
	if lb then
		local pos = at(lb.x, 0, lb.z)
		local o = CFrame.lookAt(pos, at(0, 0, 0))
		local function piece(name, size, x, yy, zz, c, op)
			return blk(name, size, o * CFrame.new(x, yy, zz), c, op)
		end
		for _, sx in { -1, 1 } do
			piece("BoardLeg", Vector3.new(1.2, 3, 1.2), sx * 4.6, 1.5, 0.3, TRIM)
		end
		piece("BoardFrame", Vector3.new(12, 7.4, 0.8), 0, 6.5, 0.3, color(lb.frame))
		local face = piece("BoardFace", Vector3.new(10.8, 6.2, 0.3), 0, 6.3, -0.2, color(lb.face))
		local head = piece("BoardHead", Vector3.new(12.6, 1.8, 1.2), 0, 10.9, 0.3, CORAL, { studs = true })
		write(head, Enum.NormalId.Front, lb.title, TRIM, 40)
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 40
		gui.LightInfluence = 0
		local rowColors = { CORAL, SKY, color(T.trunk) }
		for i, row in lb.rows do
			local r = Instance.new("TextLabel")
			r.BackgroundTransparency = 1
			r.Position = UDim2.fromScale(0.06, 0.08 + (i - 1) * 0.28)
			r.Size = UDim2.fromScale(0.88, 0.26)
			r.Font = Enum.Font.FredokaOne
			r.TextScaled = true
			r.TextColor3 = rowColors[i] or INK
			r.Text = row
			r.Parent = gui
		end
		gui.Parent = face
	end
end

-- a simple tree: cylinder trunk and ball tops (mint)
function ToyBox.tree(h, base: Vector3, s: number, rng: Random)
	local leaf, leaf2 = color(T.mint), color(T.mintDark)
	local trunk = color(T.trunk)
	local o = { mat = PLASTIC }
	h.vcyl("Trunk", base + Vector3.new(0, 3.5 * s, 0), 1.8 * s, 7 * s, trunk, table.clone(o))
	local top = rng:NextInteger(1, 2) == 1 and leaf or leaf2
	h.ball("Leaves", base + Vector3.new(0, 9 * s, 0), 7.5 * s, top, table.clone(o))
	h.ball("Leaves", base + Vector3.new(0, 13 * s, 0), 5 * s, top, { mat = PLASTIC, solid = false })
end

return ToyBox
