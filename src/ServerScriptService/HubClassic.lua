-- CLASSIC lobby (Config/Hub.lua theme = "classic"; owner 2026-11-27): a clean, classic simulator hub.
-- A floating sky island built from plain Plastic parts with studded tops, in ONE simple colour scheme
-- (Config/Hub.lua classic.palette: base / main / accent ramps; the underside a stepped stone that fits).
-- Stations share the palette and are told apart by their signs and icons. Two layouts (classic.layout):
-- "full" (stations round a plaza, trees / bushes / rocks / flowers fill the gaps) and "minimal" (compact:
-- spawn, pads, shops, gift chest, leaderboards, landmark, paths; no nature).
-- Hub.lua passes its helpers in `h` (part, at, folder, blocker, sign, padParts, padText, padCount).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HubConfig = require(ReplicatedStorage:WaitForChild("Shared").Config.Hub)

local Classic = {}

local K = HubConfig.classic
local P, LAY = K.P, K.L
local function rgb(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
-- a palette colour by name ("main", "mainLight", "baseDark", "accent", "stone2", "top" ...) or an rgb table
local function col(c: any): Color3
	if type(c) == "table" then
		return rgb(c)
	end
	if c == "top" then
		return rgb(P.base.mid)
	end
	local stone = c:match("^stone(%d)$")
	if stone then
		return rgb(P.stone[tonumber(stone)] or P.stone[#P.stone])
	end
	for _, name in { "base", "main", "accent" } do
		if c == name then
			return rgb(P[name].mid)
		elseif c == name .. "Light" then
			return rgb(P[name].light)
		elseif c == name .. "Dark" then
			return rgb(P[name].dark)
		end
	end
	error("HubClassic: unknown palette colour " .. tostring(c))
end
local PLASTIC = Enum.Material.Plastic
local CYL, BALL = Enum.PartType.Cylinder, Enum.PartType.Ball
local UP = CFrame.Angles(0, 0, math.pi / 2) -- cylinder standing up

function Classic.build(h)
	local at, part, folder = h.at, h.part, h.folder
	local BASE_L, BASE_M, BASE_D = col("baseLight"), col("base"), col("baseDark")
	local MAIN_L, MAIN_M, MAIN_D = col("mainLight"), col("main"), col("mainDark")
	local ACC_L, ACC_M = col("accentLight"), col("accent")
	local INK = rgb(P.ink)
	local SIGN_BOARD, SIGN_TEXT, SIGN_LINE = col(P.signBoard), col(P.signText), col(P.signOutline)

	-- a Plastic block with a studded top (studs = false for a smooth one)
	local function blk(name: string, size: Vector3, cf: any, c: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.mat = opts.mat or PLASTIC
		if opts.studs == nil then
			opts.studs = true
		end
		return part(name, size, cf, c, opts)
	end
	local function cyl(name: string, pos: Vector3, d: number, ht: number, c: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.shape = CYL
		opts.studs = false
		return blk(name, Vector3.new(ht, d, d), CFrame.new(pos) * UP, c, opts)
	end
	local function ball(name: string, pos: Vector3, d: number, c: Color3, o: { [string]: any }?): Part
		local opts = table.clone(o or {})
		opts.shape = BALL
		opts.studs = false
		return blk(name, Vector3.new(d, d, d), pos, c, opts)
	end
	-- a flat plate on the island from x1, z1 to x2, z2, top at `top`
	local function plate(name: string, r: { number }, top: number, c: Color3, grow: number?)
		local g = grow or 0
		local x1, z1, x2, z2 = r[1] - g, r[2] - g, r[3] + g, r[4] + g
		return blk(name, Vector3.new(x2 - x1, top, z2 - z1), at((x1 + x2) / 2, top / 2, (z1 + z2) / 2), c)
	end
	local function write(p: BasePart, face: Enum.NormalId, text: string, c: Color3, outline: Color3, ppS: number)
		return h.sign(p, face, text, c, outline, ppS)
	end
	local function faceMiddle(x: number, z: number): CFrame -- front (-Z) turned towards the spawn axis
		local pos = at(x, 0, z)
		return CFrame.lookAt(pos, at(0, 0, z))
	end
	local function named(st): string
		return st.icon and (st.icon .. " " .. st.name) or st.name
	end

	------------------------------------------------------------ island: stepped rows, top > base dark > stone
	local function island(cx: number, cy: number, cz: number, scale: number, name: string): number
		local I = LAY.island
		local y = 0
		local rw = I.row * math.max(0.5, scale)
		for li, layer in I.layers do
			local r, th = layer[1] * scale, layer[2] * math.max(0.6, scale)
			local key = layer[3]
			local c = type(key) == "number" and col("stone" .. key) or col(key)
			local n = math.max(1, math.ceil(2 * r / rw))
			local z0 = -n * rw / 2
			for k = 0, n - 1 do
				local zc = z0 + (k + 0.5) * rw
				local half = math.sqrt(math.max(0, r * r - zc * zc))
				if half > 1 then
					blk(name, Vector3.new(half * 2, th, rw), at(cx, cy + y - th / 2, cz + zc), c, { shadow = li <= 2 })
				end
			end
			y -= th
		end
		return y
	end
	local IC = LAY.island.centre or { 0, 0 } -- the island's middle (a layout can move it to fit its pieces)
	local bottom = island(IC[1], 0, IC[2], 1, "Island")
	for _, hr in LAY.island.hanging do -- a few rocks hanging under the steps
		blk("HangingRock", Vector3.new(hr[3] * 2, hr[3] * 3, hr[3] * 2), at(IC[1] + hr[1], bottom * 0.55 - hr[3], IC[2] + hr[2]), col("stone5"), { studs = false, shadow = false })
	end
	do -- invisible wall round the walkable top
		local W = LAY.island
		local segs = 40
		for k = 0, segs - 1 do
			local a = (k + 0.5) / segs * math.pi * 2
			local len = 2 * W.wallRadius * math.tan(math.pi / segs) + 0.5
			local pos = at(IC[1] + math.cos(a) * W.wallRadius, W.wallHeight / 2, IC[2] + math.sin(a) * W.wallRadius)
			h.blocker("EdgeWall", Vector3.new(len, W.wallHeight, 1), CFrame.lookAt(pos, at(IC[1], W.wallHeight / 2, IC[2])))
		end
	end
	for _, s in LAY.islets do -- small floating islands far out
		island(s[1], s[2], s[3], s[4] / LAY.island.radius, "Islet")
	end

	------------------------------------------------------------ ground plates (plaza, paths, spawn)
	local PLAZA_TOP, PATH_TOP = 0.3, 0.2
	for _, r in LAY.plates do
		plate("PlazaKerb", r, PLAZA_TOP - 0.05, MAIN_M, K.kerbWidth)
		plate("Plaza", r, PLAZA_TOP, BASE_L)
	end
	for _, r in LAY.paths do
		plate("Path", r, PATH_TOP, MAIN_L)
	end
	local sp = HubConfig.spawn
	do
		local s = K.spawnPad.size
		blk("SpawnPad", Vector3.new(s + 1.2, 0.3, s + 1.2), at(sp[1], PLAZA_TOP + 0.15, sp[3]), MAIN_D)
		blk("SpawnPadTop", Vector3.new(s, 0.4, s), at(sp[1], PLAZA_TOP + 0.2, sp[3]), MAIN_L)
	end

	------------------------------------------------------------ play pads (Pad1-4 stay the invisible standing parts)
	local w, d = HubConfig.padSize[1], HubConfig.padSize[2]
	for i, xz in HubConfig.pads do
		local x, z = xz[1], xz[2]
		blk("PadRim", Vector3.new(w + 2, 0.6, d + 2), at(x, PLAZA_TOP + 0.3, z), MAIN_D)
		blk("PadLine", Vector3.new(w + 0.8, 0.7, d + 0.8), at(x, PLAZA_TOP + 0.35, z), col(P.padLine or "baseLight"))
		blk("PadTop", Vector3.new(w, 0.8, d), at(x, PLAZA_TOP + 0.4, z), MAIN_M)
		local pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, PLAZA_TOP + 0.95, z), MAIN_M, { transparency = 1, solid = false, shadow = false })
		-- sign behind the pad: big "PAD n", the player count under it
		local S = K.pad.sign
		local sz = z - d / 2 - 2
		for _, sx in { -1, 1 } do
			blk("PadSignPost", Vector3.new(0.9, S.y, 0.9), at(x + sx * (S.w / 2 - 1.2), PLAZA_TOP + S.y / 2, sz - 0.4), MAIN_D)
		end
		blk("PadSignFrame", Vector3.new(S.w + 0.6, S.h + 0.6, 0.5), at(x, S.y, sz - 0.4), MAIN_D, { studs = false })
		local board = blk("PadSign", Vector3.new(S.w, S.h, 0.4), at(x, S.y, sz), SIGN_BOARD, { studs = false })
		blk("PadSignCap", Vector3.new(S.w + 1, 0.5, 1.2), at(x, S.y + S.h / 2 + 0.55, sz - 0.3), MAIN_D)
		local t = write(board, Enum.NormalId.Back, ("PAD %d"):format(i), SIGN_TEXT, SIGN_LINE, 20)
		t.Size = UDim2.fromScale(0.92, 0.58)
		t.Position = UDim2.fromScale(0.04, 0.05)
		local cnt = t:Clone()
		cnt.Text = ("0/%d"):format(HubConfig.maxPlayers)
		cnt.Size = UDim2.fromScale(0.8, 0.34)
		cnt.Position = UDim2.fromScale(0.1, 0.62)
		cnt.Parent = t.Parent
		h.padText[i] = t
		h.padCount[i] = cnt
		pad:SetAttribute("Index", i)
		pad:SetAttribute("Members", 0)
		h.padParts[i] = pad
	end

	------------------------------------------------------------ landmark: stepped base, giant bubble, BUBBLE POP sign
	do
		local L, pos = K.landmark, LAY.landmark
		local y = PLAZA_TOP
		local shades = { BASE_D, BASE_M, BASE_L }
		for k, tier in L.tiers do
			blk("LandmarkBase", Vector3.new(tier[1], tier[2], tier[1]), at(0, y + tier[2] / 2, pos.z), shades[k] or BASE_L)
			y += tier[2]
		end
		local B = L.bubble
		local by = y + B / 2 - 1.5
		local bubble = ball("GiantBubble", at(0, by, pos.z), B, rgb(P.bubble), { transparency = L.bubbleTransparency, mat = Enum.Material.SmoothPlastic, gloss = 0.1, shadow = false })
		local rim = Instance.new("Highlight") -- a soft edge so the bubble reads against the sky
		rim.FillTransparency = 1
		rim.OutlineColor = rgb(P.bubbleRim)
		rim.OutlineTransparency = 0.25
		rim.DepthMode = Enum.HighlightDepthMode.Occluded
		rim.Parent = bubble
		local shine = Color3.new(1, 1, 1)
		ball("BubbleShine", at(-B * 0.2, by + B * 0.22, pos.z + B * 0.3), B * 0.15, shine, { mat = Enum.Material.SmoothPlastic, gloss = 0, solid = false, shadow = false })
		ball("BubbleShine2", at(-B * 0.3, by + B * 0.06, pos.z + B * 0.36), B * 0.065, shine, { mat = Enum.Material.SmoothPlastic, gloss = 0, solid = false, shadow = false })
		local S = L.sign
		local postH = S.y - S.h / 2 + 0.5
		for _, sx in { -1, 1 } do
			blk("LandmarkPost", Vector3.new(2, postH, 2), at(sx * (S.w / 2 - 5), postH / 2 + PLAZA_TOP, pos.signZ - 0.8), MAIN_D)
		end
		blk("LandmarkSignFrame", Vector3.new(S.w + 1.2, S.h + 1.2, 1), at(0, S.y, pos.signZ - 0.6), MAIN_D, { studs = false })
		local face = blk("LandmarkSign", Vector3.new(S.w, S.h, 0.6), at(0, S.y, pos.signZ), col(P.logoFace), { studs = false })
		blk("LandmarkSignCap", Vector3.new(S.w + 2, 0.8, 1.8), at(0, S.y + S.h / 2 + 1, pos.signZ - 0.5), MAIN_D)
		write(face, Enum.NormalId.Back, "BUBBLE POP", col(P.logoText), rgb(P.logoOutline), 12)
	end

	------------------------------------------------------------ stations (all in the palette; signs and icons tell them apart)
	local stationSpots: { { number } } = {}
	local function booth(st)
		local f = faceMiddle(st.x, st.z)
		local function piece(name, size, x, yy, zz, c, o)
			return blk(name, size, f * CFrame.new(x, PLAZA_TOP + yy, zz), c, o)
		end
		piece("BoothFloor", Vector3.new(13, 0.4, 11), 0, 0.2, 0, BASE_M)
		piece("BoothBack", Vector3.new(11, 8.6, 0.8), 0, 4.7, 4.6, MAIN_M, { studs = false })
		for _, sx in { -1, 1 } do
			piece("BoothSide", Vector3.new(0.8, 8.6, 9), sx * 5.6, 4.7, 0.5, MAIN_M, { studs = false })
			piece("BoothPost", Vector3.new(1.2, 9, 1.2), sx * 5.6, 4.9, -4.4, BASE_L)
		end
		piece("BoothCounter", Vector3.new(10.4, 3.4, 1.8), 0, 2.1, -3.6, MAIN_M, { studs = false })
		piece("BoothCounterTop", Vector3.new(11.2, 0.5, 2.4), 0, 4.05, -3.6, BASE_L)
		piece("BoothRoofTrim", Vector3.new(13.4, 0.6, 11.4), 0, 9.7, 0, BASE_L, { studs = false })
		piece("BoothRoof", Vector3.new(13, 1, 11), 0, 10.5, 0, MAIN_D)
		local plate = piece("BoothSign", Vector3.new(11, 3, 0.8), 0, 13, -3.5, SIGN_BOARD, { studs = false })
		piece("BoothSignCap", Vector3.new(11.6, 0.5, 1.2), 0, 14.75, -3.5, MAIN_D)
		write(plate, Enum.NormalId.Front, named(st), SIGN_TEXT, SIGN_LINE, 40)
		-- key-button pad in front (the station's prompt spot later)
		local po = f * CFrame.new(0, PLAZA_TOP, -K.booth.padDistance)
		blk("BoothPadRim", Vector3.new(7.4, 0.3, 7.4), po * CFrame.new(0, 0.15, 0), BASE_L)
		blk("BoothPad", Vector3.new(6.2, 0.4, 6.2), po * CFrame.new(0, 0.2, 0), ACC_M)
	end
	local function textBoard(f: CFrame, title: string, rows: { string }?, body: string?)
		local function piece(name, size, x, yy, zz, c, o)
			return blk(name, size, f * CFrame.new(x, PLAZA_TOP + yy, zz), c, o)
		end
		for _, sx in { -1, 1 } do
			piece("BoardLeg", Vector3.new(1.2, 4, 1.2), sx * 5.4, 2, 0.4, MAIN_D)
		end
		piece("BoardFrame", Vector3.new(13.4, 9.4, 0.8), 0, 8.5, 0.4, MAIN_D, { studs = false })
		local face = piece("Board", Vector3.new(12.2, 8.2, 0.3), 0, 8.3, -0.1, BASE_L, { studs = false })
		local head = piece("BoardHead", Vector3.new(14, 2, 1.4), 0, 14, 0.3, SIGN_BOARD)
		write(head, Enum.NormalId.Front, title, SIGN_TEXT, SIGN_LINE, 40)
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 30
		gui.LightInfluence = 0
		if body then
			local t = Instance.new("TextLabel")
			t.Size = UDim2.fromScale(0.88, 0.86)
			t.Position = UDim2.fromScale(0.06, 0.07)
			t.BackgroundTransparency = 1
			t.FontFace = Font.fromEnum(Enum.Font.FredokaOne)
			t.TextScaled = true
			t.TextXAlignment = Enum.TextXAlignment.Left
			t.TextColor3 = INK
			t.Text = body
			t.Parent = gui
		end
		for i, row in rows or {} do -- placeholder rows (filled in later by the server)
			local r = Instance.new("TextLabel")
			r.Name = "Row" .. i
			r.BackgroundTransparency = 1
			r.Position = UDim2.fromScale(0.08, 0.07 + (i - 1) * 0.3)
			r.Size = UDim2.fromScale(0.84, 0.26)
			r.FontFace = Font.fromEnum(Enum.Font.FredokaOne)
			r.TextScaled = true
			r.TextXAlignment = Enum.TextXAlignment.Left
			r.TextColor3 = i == 1 and MAIN_D or INK
			r.Text = row
			r.Parent = gui
		end
		gui.Parent = face
	end
	-- the free gift chest: body + a separate lid on a back hinge (Controllers/HubChest opens it on this client)
	local function gift(st)
		local C = K.chest
		local cw, ch, cd, lh = C.size[1], C.size[2], C.size[3], C.lid
		local f = faceMiddle(st.x, st.z)
		local model = Instance.new("Model")
		model.Name = "GiftChest"
		local function piece(name, size, x, yy, zz, c, o, parent)
			local op = table.clone(o or {})
			op.parent = parent or model
			return blk(name, size, f * CFrame.new(x, PLAZA_TOP + yy, zz), c, op)
		end
		piece("ChestPlinth", Vector3.new(cw + 2, 0.6, cd + 2), 0, 0.3, 0, MAIN_D)
		piece("ChestBody", Vector3.new(cw, ch, cd), 0, 0.6 + ch / 2, 0, ACC_M, { studs = false })
		piece("ChestBand", Vector3.new(1, ch + 0.04, cd + 0.04), 0, 0.6 + ch / 2, 0, MAIN_L, { studs = false })
		piece("ChestBand", Vector3.new(cw + 0.04, 0.6, cd + 0.04), 0, 0.6 + ch - 0.6, 0, MAIN_L, { studs = false })
		piece("ChestInside", Vector3.new(cw - 0.8, 0.2, cd - 0.8), 0, 0.6 + ch - 0.05, 0, ACC_L, { studs = false, mat = Enum.Material.SmoothPlastic, shadow = false })
		-- the lid: its own model, turned by the client about the hinge (the body's back top edge)
		local lid = Instance.new("Model")
		lid.Name = "Lid"
		lid.Parent = model
		local top = 0.6 + ch
		piece("LidTop", Vector3.new(cw + 0.2, lh, cd + 0.2), 0, top + lh / 2, 0, ACC_M, { solid = false }, lid)
		piece("LidBand", Vector3.new(1, lh + 0.04, cd + 0.24), 0, top + lh / 2, 0, MAIN_L, { solid = false }, lid)
		piece("LidLatch", Vector3.new(1.2, 1.2, 0.4), 0, top - 0.1, -cd / 2 - 0.25, MAIN_L, { solid = false, studs = false }, lid)
		local hinge = piece("Hinge", Vector3.new(cw, 0.2, 0.2), 0, top, cd / 2 + 0.1, MAIN_L, { solid = false, transparency = 1, shadow = false })
		hinge.CanQuery = false
		-- the glow, the confetti and a blocker (lid parts don't collide)
		local glowPart = piece("ChestGlow", Vector3.new(1, 1, 1), 0, top + 0.6, 0, ACC_L, { solid = false, transparency = 1, shadow = false })
		local light = Instance.new("PointLight")
		light.Name = "Glow"
		light.Color = ACC_L
		light.Brightness = 0
		light.Range = C.glowRange
		light.Enabled = false
		light.Parent = glowPart
		local confetti = Instance.new("ParticleEmitter")
		confetti.Name = "Confetti"
		confetti.Rate = 0
		confetti.EmissionDirection = Enum.NormalId.Top
		confetti.Lifetime = NumberRange.new(0.8, 1.4)
		confetti.Speed = NumberRange.new(10, 16)
		confetti.SpreadAngle = Vector2.new(35, 35)
		confetti.Acceleration = Vector3.new(0, -28, 0)
		confetti.Drag = 1.5
		confetti.Size = NumberSequence.new(0.35, 0.25)
		confetti.Rotation = NumberRange.new(0, 360)
		confetti.RotSpeed = NumberRange.new(-300, 300)
		confetti.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.8, 0), NumberSequenceKeypoint.new(1, 1) })
		confetti.LightInfluence = 0.4
		confetti.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, ACC_M), ColorSequenceKeypoint.new(0.5, MAIN_M), ColorSequenceKeypoint.new(1, BASE_L) })
		confetti.Parent = glowPart
		h.blocker("ChestLidBlock", Vector3.new(cw, lh, cd), f * CFrame.new(0, PLAZA_TOP + top + lh / 2, 0)).Parent = model
		model.PrimaryPart = hinge
		model.Parent = folder
		-- sign behind the chest (high enough to show over the open lid)
		for _, sx in { -1, 1 } do
			blk("GiftSignPost", Vector3.new(0.9, 9, 0.9), f * CFrame.new(sx * 4, PLAZA_TOP + 4.5, cd / 2 + 2.6), MAIN_D)
		end
		local plate = blk("GiftSign", Vector3.new(10, 2.8, 0.6), f * CFrame.new(0, PLAZA_TOP + 10, cd / 2 + 2.6), SIGN_BOARD, { studs = false })
		blk("GiftSignCap", Vector3.new(10.6, 0.5, 1), f * CFrame.new(0, PLAZA_TOP + 11.65, cd / 2 + 2.6), MAIN_D)
		write(plate, Enum.NormalId.Front, named(st), SIGN_TEXT, SIGN_LINE, 40)
	end
	for _, st in LAY.stations do
		if st.kind == "booth" then
			booth(st)
		elseif st.kind == "board" then
			textBoard(faceMiddle(st.x, st.z), st.name, nil, K.howTo)
		elseif st.kind == "gift" then
			gift(st)
		end
		table.insert(stationSpots, { st.x, st.z })
	end
	for _, lb in LAY.leaderboards or {} do
		textBoard(faceMiddle(lb.x, lb.z), lb.title, lb.rows)
		table.insert(stationSpots, { lb.x, lb.z })
	end

	------------------------------------------------------------ nature (full layout): trees, bushes, rocks, flowers
	local N = LAY.nature
	if not N then
		return
	end
	local rng = Random.new(N.seed)
	local taken: { { number } } = {} -- { x, z, radius } of everything placed
	local function inRect(x: number, z: number, rect: { number }, m: number): boolean
		return x > rect[1] - m and x < rect[3] + m and z > rect[2] - m and z < rect[4] + m
	end
	local function blocked(x: number, z: number, r: number): boolean
		if Vector2.new(x - IC[1], z - IC[2]).Magnitude > LAY.island.wallRadius - 2 - r then
			return true
		end
		local m = r + 1.5
		for _, rect in LAY.plates do
			if inRect(x, z, rect, m) then
				return true
			end
		end
		for _, rect in LAY.paths do
			if inRect(x, z, rect, m) then
				return true
			end
		end
		for _, s in stationSpots do
			if (Vector2.new(x, z) - Vector2.new(s[1], s[2])).Magnitude < 9 + r then
				return true
			end
		end
		for _, t in taken do
			if (Vector2.new(x, z) - Vector2.new(t[1], t[2])).Magnitude < t[3] + r then
				return true
			end
		end
		return false
	end
	local function spot(cx: number, cz: number, spread: number, r: number): (number?, number?)
		for _ = 1, 14 do
			local a, dd = rng:NextNumber(0, math.pi * 2), rng:NextNumber(0, spread)
			local x, z = cx + math.cos(a) * dd, cz + math.sin(a) * dd
			if not blocked(x, z, r) then
				table.insert(taken, { x, z, r })
				return x, z
			end
		end
		return nil, nil
	end
	local function list(keys: { any }): { Color3 }
		local out = {}
		for _, k in keys do
			table.insert(out, col(k))
		end
		return out
	end
	local leaves, bushC, rockC, flowerC = list(P.leaves), list(P.bushes), list(P.rocks), list(P.flowers)
	local trunkC = col(P.trunk)
	local function tree(base: Vector3, s: number, kind: number)
		local leaf = leaves[rng:NextInteger(1, #leaves)]
		local turn = CFrame.Angles(0, rng:NextNumber(0, math.pi / 2), 0)
		if kind == 1 then -- round: cylinder trunk, a big ball and two smaller ones
			cyl("Trunk", base + Vector3.new(0, 3.6 * s, 0), 1.6 * s, 7.6 * s, trunkC)
			ball("Leaves", base + Vector3.new(0, 9 * s, 0), 8 * s, leaf, { solid = false })
			ball("Leaves", base + (turn * Vector3.new(2.6 * s, 7.4 * s, 0.8 * s)), 5 * s, leaf, { solid = false })
			ball("Leaves", base + (turn * Vector3.new(-2.2 * s, 7.8 * s, -1.4 * s)), 5.4 * s, leaf, { solid = false })
		else -- blocky: square trunk, two studded leaf blocks
			blk("Trunk", Vector3.new(1.6 * s, 7 * s, 1.6 * s), CFrame.new(base + Vector3.new(0, 3.3 * s, 0)) * turn, trunkC, { studs = false })
			blk("Leaves", Vector3.new(7.5 * s, 4.4 * s, 7.5 * s), CFrame.new(base + Vector3.new(0, 8 * s, 0)) * turn, leaf, { solid = false })
			blk("Leaves", Vector3.new(4.8 * s, 3 * s, 4.8 * s), CFrame.new(base + Vector3.new(0, 11.4 * s, 0)) * turn * CFrame.Angles(0, math.pi / 4, 0), leaf, { solid = false })
		end
	end
	local smin, smax = N.treeSize[1], N.treeSize[2]
	for _, c in N.trees do
		for _ = 1, c[3] do
			local s = rng:NextNumber(smin, smax)
			local x, z = spot(c[1], c[2], c[4], 4.2 * s)
			if x then
				tree(at(x, 0, z), s, rng:NextInteger(1, 2))
			end
		end
	end
	for _, s in LAY.islets do -- a tree or two on each far islet
		for k = 1, 2 do
			tree(at(s[1] + (k - 1.5) * s[4] * 0.6, s[2], s[3] + (k - 1.5) * s[4] * 0.3), s[4] / 14, k)
		end
	end
	for _, c in N.bushes do
		for _ = 1, c[3] do
			local s = rng:NextNumber(0.8, 1.3)
			local x, z = spot(c[1], c[2], 3.5, 1.8 * s)
			if x then
				local bc = bushC[rng:NextInteger(1, #bushC)]
				local turn = CFrame.Angles(0, rng:NextNumber(0, math.pi / 2), 0)
				blk("Bush", Vector3.new(3.4 * s, 2.2 * s, 3.4 * s), CFrame.new(at(x, 1.05 * s, z)) * turn, bc)
				blk("Bush", Vector3.new(2.2 * s, 1.2 * s, 2.2 * s), CFrame.new(at(x, 2.6 * s, z)) * turn * CFrame.Angles(0, math.pi / 4, 0), bc, { solid = false })
			end
		end
	end
	for _, c in N.rocks do
		for k = 1, c[3] do
			local s = k == 1 and rng:NextNumber(2.6, 3.6) or rng:NextNumber(1.4, 2.4)
			local x, z = spot(c[1], c[2], 4, s * 0.7)
			if x then
				local cf = CFrame.new(at(x, s * 0.35, z)) * CFrame.Angles(rng:NextNumber(-0.12, 0.12), rng:NextNumber(0, math.pi), rng:NextNumber(-0.12, 0.12))
				blk("Rock", Vector3.new(s * 1.2, s, s), cf, rockC[rng:NextInteger(1, #rockC)])
			end
		end
	end
	local stem = bushC[1]
	for _, c in N.flowers do
		local fc = flowerC[rng:NextInteger(1, #flowerC)]
		for _ = 1, c[3] do
			local x, z = spot(c[1], c[2], 3.2, 0.5)
			if x then
				blk("FlowerStem", Vector3.new(0.2, 0.8, 0.2), at(x, 0.4, z), stem, { solid = false, studs = false, shadow = false })
				blk("Flower", Vector3.new(0.7, 0.5, 0.7), CFrame.new(at(x, 0.95, z)) * CFrame.Angles(0, rng:NextNumber(0, 1.5), 0), fc, { solid = false, shadow = false })
			end
		end
	end
end

return Classic
