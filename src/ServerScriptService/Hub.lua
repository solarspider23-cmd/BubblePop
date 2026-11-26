-- The lobby hub: builds the plaza (HQ + logo, 4 play pads, fountain, booths, gift chest, scenery)
-- and runs the pads.
-- Main calls Hub.start({ canStart = fn() -> boolean, startRun = fn(players, roomIndex), inRun = fn(player) -> boolean }).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local HubConfig = require(Shared.Config.Hub)
local LobbyRules = require(Shared.Rules.Lobby)

local Hub = {}

local O = Vector3.new(HubConfig.origin[1], HubConfig.origin[2], HubConfig.origin[3])
local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local C = {}
for k, v in HubConfig.colors do
	if type(v[1]) == "number" then
		C[k] = color(v)
	end
end

local folder = Instance.new("Folder")
folder.Name = "Hub"

local function at(x: number, y: number, z: number): Vector3
	return O + Vector3.new(x, y, z)
end

-- One anchored part. cf may be a Vector3 (position) or a CFrame.
local function part(name: string, size: Vector3, cf: any, col: Color3, opts: { [string]: any }?): Part
	local o = opts or {}
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = typeof(cf) == "Vector3" and CFrame.new(cf) or cf
	p.Color = col
	p.Material = o.mat or Enum.Material.SmoothPlastic
	p.TopSurface = o.studs and Enum.SurfaceType.Studs or Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if o.shape then
		p.Shape = o.shape
	end
	p.Transparency = o.transparency or 0
	if p.Material == Enum.Material.SmoothPlastic then
		p.Reflectance = o.gloss or 0.06 -- a little shine everywhere (aero look)
	end
	p.CanCollide = o.solid ~= false
	p.CastShadow = o.shadow ~= false
	p.Parent = o.parent or folder
	return p
end
local BALL, CYL = Enum.PartType.Ball, Enum.PartType.Cylinder
local NEON, GLASS = Enum.Material.Neon, Enum.Material.Glass
local UP = CFrame.Angles(0, 0, math.pi / 2) -- cylinder standing up
local FACE_Z = CFrame.Angles(0, math.pi / 2, 0) -- cylinder facing +Z (a disc on a wall)

local function vcyl(name: string, pos: Vector3, d: number, h: number, col: Color3, opts: { [string]: any }?): Part
	local o = opts or {}
	o.shape = CYL
	return part(name, Vector3.new(h, d, d), CFrame.new(pos) * UP, col, o)
end
local function ball(name: string, pos: Vector3, d: number, col: Color3, opts: { [string]: any }?): Part
	local o = opts or {}
	o.shape = BALL
	return part(name, Vector3.new(d, d, d), pos, col, o)
end

local function stroke(t: TextLabel, thick: number, col: Color3)
	local st = Instance.new("UIStroke")
	st.Thickness = thick
	st.Color = col
	st.Parent = t
end

-- Text on a part's face
-- (text can't be bigger than 100 px, so big signs use fewer pixels per stud)
local function sign(parent: BasePart, face: Enum.NormalId, text: string, col: Color3?, strokeCol: Color3?, pixelsPerStud: number?)
	local gui = Instance.new("SurfaceGui")
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = pixelsPerStud or 30
	gui.LightInfluence = 0
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(0.92, 0.8)
	t.Position = UDim2.fromScale(0.04, 0.1)
	t.BackgroundTransparency = 1
	t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	t.TextScaled = true
	t.Text = text
	t.TextColor3 = col or Color3.new(1, 1, 1)
	stroke(t, math.max(2, (pixelsPerStud or 30) / 7), strokeCol or Color3.fromRGB(20, 40, 110))
	t.Parent = gui
	gui.Parent = parent
end

-- Floating text above a part
local function label(parent: BasePart, text: string, height: number, w: number, h: number, col: Color3?): TextLabel
	local bb = Instance.new("BillboardGui")
	bb.Name = "Info"
	bb.Size = UDim2.fromScale(w, h)
	bb.StudsOffsetWorldSpace = Vector3.new(0, height, 0)
	bb.LightInfluence = 0
	bb.MaxDistance = 140
	local t = Instance.new("TextLabel")
	t.Name = "Text"
	t.Size = UDim2.fromScale(1, 1)
	t.BackgroundTransparency = 1
	t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	t.TextScaled = true
	t.TextColor3 = col or Color3.new(1, 1, 1)
	t.Text = text
	stroke(t, 3, Color3.fromRGB(20, 40, 110))
	t.Parent = bb
	bb.Parent = parent
	return t
end

Hub.spawnCFrame = CFrame.lookAt(at(HubConfig.spawn[1], HubConfig.spawn[2], HubConfig.spawn[3]), at(0, HubConfig.spawn[2], -10))

local padParts: { BasePart } = {}

---------------------------------------------------------------- pieces

local function buildPlaza()
	local S = HubConfig.size
	local half = S / 2
	-- a floating island in the sky: grassy top, a frosting drip, then a chocolate underside that
	-- narrows to a point (candy theme), with clouds below. The plaza sits 3 studs above the grass.
	local isl = HubConfig.island
	part("Grass", Vector3.new(5, isl.radius * 2, isl.radius * 2), CFrame.new(at(0, -5.5, 0)) * UP, C.grass, { mat = Enum.Material.Grass, shape = CYL })
	local under = HubConfig.theme == "gumball" and Color3.fromRGB(110, 65, 45) or Color3.fromRGB(150, 110, 80)
	vcyl("Frosting", at(0, -8.5, 0), isl.radius * 2 + 1, 1.6, C.lavender)
	for k, layer in { { 0.97, 8 }, { 0.86, 9 }, { 0.7, 9 }, { 0.5, 9 }, { 0.3, 8 }, { 0.14, 7 } } do
		local y = -9.3 - (k - 0.5) * 8.6
		vcyl("IslandRock", at(0, y, 0), isl.radius * 2 * layer[1], layer[2], under, { mat = Enum.Material.Slate, shadow = false })
	end
	part("Plaza", Vector3.new(S, 2.8, S), at(0, -1.6, 0), C.white)
	part("PlazaTrim", Vector3.new(S + 1, 0.8, S + 1), at(0, -2.6, 0), C.blue)
	-- checkerboard of studded tiles
	local n = 8
	local t = S / n
	for i = 0, n - 1 do
		for j = 0, n - 1 do
			local x, z = -half + t * (i + 0.5), -half + t * (j + 0.5)
			part("Tile", Vector3.new(t, 0.2, t), at(x, -0.1, z), (i + j) % 2 == 0 and C.tileA or C.tileB, { shadow = false, gloss = 0.1 })
		end
	end
	-- low fence: posts with little glowing caps, one blue rail
	local edge = half - 1
	for _, side in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
		local alongX = side[2] ~= 0
		local rail = alongX and Vector3.new(S - 2, 0.6, 0.6) or Vector3.new(0.6, 0.6, S - 2)
		part("Rail", rail, at(side[1] * edge, 2.4, side[2] * edge), C.chrome, { mat = Enum.Material.Metal })
		part("Rail", rail, at(side[1] * edge, 1.2, side[2] * edge), C.lightBlue)
		for k = -7, 7 do
			local u = k * (edge / 7)
			local x, z = alongX and u or side[1] * edge, alongX and side[2] * edge or u
			if HubConfig.theme == "gumball" then -- candy-cane stripes
				for seg = 0, 3 do
					part("Post", Vector3.new(1.2, 0.8, 1.2), at(x, 0.4 + seg * 0.8, z), seg % 2 == 0 and C.white or C.blue)
				end
			else
				part("Post", Vector3.new(1.2, 3.2, 1.2), at(x, 1.6, z), C.white)
			end
			part("PostLight", Vector3.new(0.8, 0.8, 0.8), at(x, 3.6, z), C.glow, { mat = NEON, shadow = false })
		end
	end
	-- spawn spot
	vcyl("SpawnRing", at(HubConfig.spawn[1], 0.15, HubConfig.spawn[3]), 11, 0.3, C.blue)
	vcyl("SpawnDisc", at(HubConfig.spawn[1], 0.2, HubConfig.spawn[3]), 9.5, 0.3, C.white)
end

-- a little blocky person (decoration)
local function npc(feet: Vector3, shirt: Color3, pants: Color3)
	local base = CFrame.lookAt(feet, feet + Vector3.zAxis)
	local skin = Color3.fromRGB(255, 205, 150)
	local function bit(name, size, x, y, col)
		part(name, size, base * CFrame.new(x, y, 0), col)
	end
	bit("Leg", Vector3.new(1, 2, 1), -0.5, 1, pants)
	bit("Leg", Vector3.new(1, 2, 1), 0.5, 1, pants)
	bit("Torso", Vector3.new(2, 2, 1), 0, 3, shirt)
	bit("Arm", Vector3.new(1, 2, 1), -1.5, 3, skin)
	bit("Arm", Vector3.new(1, 2, 1), 1.5, 3, skin)
	local head = part("Head", Vector3.new(2, 1, 1), base * CFrame.new(0, 4.5, 0), skin)
	local mesh = Instance.new("SpecialMesh")
	mesh.MeshType = Enum.MeshType.Head
	mesh.Scale = Vector3.new(1.25, 1.25, 1.25)
	mesh.Parent = head
	local face = Instance.new("Decal")
	face.Texture = "rbxasset://textures/face.png"
	face.Face = Enum.NormalId.Front
	face.Parent = head
end

local function buildHQ()
	local z = -47
	-- stage and back wall
	part("Stage", Vector3.new(30, 1.5, 14), at(0, 0.75, -42), C.lavender)
	part("StageEdge", Vector3.new(30.4, 0.4, 0.4), at(0, 1.3, -34.9), C.gold)
	part("BackWall", Vector3.new(30, 16, 2), at(0, 8, -50), C.white)
	for _, x in { -10, 0, 10 } do
		part("WallStripe", Vector3.new(1.5, 16, 0.4), at(x, 8, -48.8), C.lightBlue)
	end
	-- two towers with glowing windows, domed roofs and flags
	for _, sx in { -1, 1 } do
		local x = sx * 19.5
		part("Tower", Vector3.new(9, 22, 9), at(x, 11, z), C.white)
		for _, dx in { -4.6, 4.6 } do
			part("TowerStripe", Vector3.new(0.6, 22, 0.6), at(x + dx, 11, z + 4.6), C.blue)
		end
		for row = 0, 2 do
			for _, dx in { -2, 2 } do
				part("Window", Vector3.new(2, 3, 0.3), at(x + dx, 6 + row * 5, z + 4.55), Color3.fromRGB(210, 150, 40), { mat = NEON, shadow = false })
			end
		end
		vcyl("TowerCap", at(x, 22.5, z), 11, 1, C.pink)
		ball("TowerDome", at(x, 23, z), 8, C.lightBlue)
		vcyl("FlagPole", at(x, 29, z), 0.4, 8, C.white)
		part("Flag", Vector3.new(4, 2.5, 0.2), at(x + sx * 2.2, 31.5, z), sx < 0 and C.pink or C.blue, { shadow = false })
	end
	-- pipes joining the towers
	for _, y in { 15, 18.5 } do
		part("Pipe", Vector3.new(30, 1.6, 1.6), at(0, y, -47), Color3.fromRGB(200, 205, 215), { shape = CYL, mat = Enum.Material.Metal })
		for _, x in { -9, 0, 9 } do
			part("PipeRing", Vector3.new(0.8, 2.1, 2.1), at(x, y, -47), C.gold, { shape = CYL })
		end
	end
	-- counter with two helpers behind it
	local counter = part("Counter", Vector3.new(16, 3.5, 3), CFrame.lookAt(at(0, 3.25, -38), at(0, 3.25, 0)), C.blue)
	part("CounterTop", Vector3.new(16.6, 0.5, 3.6), at(0, 5.25, -38), C.pink)
	local _ = counter
	local hqSign = part("HQSign", Vector3.new(14, 3, 0.4), CFrame.lookAt(at(0, 11.5, -48.6), at(0, 11.5, 0)), C.pink)
	sign(hqSign, Enum.NormalId.Front, "BUBBLE HQ", Color3.new(1, 1, 1), nil, 18)
	npc(at(-4, 1.5, -41.5), C.pink, Color3.fromRGB(60, 70, 110))
	npc(at(4, 1.5, -41.5), C.blue, Color3.fromRGB(60, 70, 110))

	-- the floating logo, a bubble-wrap emblem behind it and two crossed pop sticks
	local ey, ez = 39, -46
	for _, sgn in { -1, 1 } do
		local cf = CFrame.new(at(0, ey, ez - 1.5)) * CFrame.Angles(0, 0, sgn * math.rad(42))
		part("PopStick", Vector3.new(50, 2, 2), cf, Color3.fromRGB(255, 160, 50), { shape = CYL })
		local tip = (cf * CFrame.new(sgn * 25, 0, 0)).Position
		ball("StickTip", tip, 5, C.pink)
		part("StickBand", Vector3.new(1, 2.7, 2.7), cf * CFrame.new(sgn * 21.5, 0, 0), C.white, { shape = CYL })
	end
	part("EmblemRim", Vector3.new(1, 24.5, 24.5), CFrame.new(at(0, ey, ez - 0.6)) * FACE_Z, C.white, { shape = CYL })
	part("Emblem", Vector3.new(1, 22, 22), CFrame.new(at(0, ey, ez)) * FACE_Z, C.lightBlue, { shape = CYL })
	local bubbles = { { 0, 0, 7 } }
	for k = 0, 5 do
		local a = math.rad(k * 60)
		table.insert(bubbles, { math.cos(a) * 6.6, math.sin(a) * 6.6, 5.4 })
	end
	for _, b in bubbles do
		local pos = at(b[1], ey + b[2], ez + 0.5)
		ball("EmblemBubble", pos, b[3], Color3.fromRGB(215, 245, 255), { mat = GLASS, transparency = 0.15 })
		ball("EmblemShine", pos + Vector3.new(-b[3] * 0.18, b[3] * 0.18, b[3] * 0.4), b[3] * 0.22, Color3.new(1, 1, 1))
	end
	local lz = -43
	part("LogoRim", Vector3.new(47.5, 10.5, 1), at(0, 29, lz - 0.6), C.white)
	for _, sx in { -1, 1 } do
		part("LogoRimEnd", Vector3.new(1, 10.5, 10.5), CFrame.new(at(sx * 23.75, 29, lz - 0.6)) * FACE_Z, C.white, { shape = CYL })
		part("LogoEnd", Vector3.new(1.4, 9, 9), CFrame.new(at(sx * 23.75, 29, lz)) * FACE_Z, C.blue, { shape = CYL })
	end
	local plaque = part("Logo", Vector3.new(47.5, 9, 1.4), CFrame.lookAt(at(0, 29, lz), at(0, 29, 100)), C.blue)
	sign(plaque, Enum.NormalId.Front, "BUBBLE POP", Color3.new(1, 1, 1), Color3.fromRGB(15, 50, 140), 11)
	-- glossy shine across the top half of the logo
	part("LogoShine", Vector3.new(44, 3, 0.2), at(0, 31.6, lz + 0.8), Color3.new(1, 1, 1), { transparency = 0.65, solid = false, shadow = false })
end

local function buildPads()
	local w, d = HubConfig.padSize[1], HubConfig.padSize[2]
	for i, xz in HubConfig.pads do
		local x, z = xz[1], xz[2]
		local col = color(HubConfig.colors.pad[i] or HubConfig.colors.pad[1])
		part("PadBase", Vector3.new(w + 0.8, 0.4, d + 0.8), at(x, 0.2, z), C.padBase)
		part("PadEdge", Vector3.new(w + 0.8, 0.5, 0.4), at(x, 0.25, z - d / 2 - 0.6), col)
		local pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, 0.45, z), col, { mat = NEON, transparency = 0.3, solid = false, shadow = false })
		pad:SetAttribute("Index", i)
		pad:SetAttribute("Members", 0)
		label(pad, ("PAD %d\n0/%d"):format(i, HubConfig.maxPlayers), 5, 9, 3.4)
		padParts[i] = pad
	end
end

local function buildLeft()
	-- how-to-play board, turned towards the middle
	local bpos = at(-46, 6.5, -20)
	local face = CFrame.lookAt(bpos, at(0, 6.5, 4))
	part("BoardFrame", Vector3.new(14, 10, 0.6), face * CFrame.new(0, 0, 0.35), C.blue)
	local board = part("Board", Vector3.new(13, 9, 0.6), face, C.white)
	for _, dx in { -6, 6 } do
		part("BoardLeg", Vector3.new(1, 6.5, 1), face * CFrame.new(dx, -5.5, 0.3), C.white)
	end
	local alert = part("Alert", Vector3.new(0.6, 3, 3), face * CFrame.new(-6.5, 5.5, 0) * FACE_Z, Color3.fromRGB(230, 50, 60), { shape = CYL })
	label(alert, "!", 0, 2, 2)
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
	title.TextColor3 = C.blue
	title.Parent = gui
	local body = Instance.new("TextLabel")
	body.Size = UDim2.fromScale(0.86, 0.68)
	body.Position = UDim2.fromScale(0.07, 0.28)
	body.BackgroundTransparency = 1
	body.FontFace = Font.fromEnum(Enum.Font.FredokaOne)
	body.TextScaled = true
	body.TextXAlignment = Enum.TextXAlignment.Left
	body.TextYAlignment = Enum.TextYAlignment.Top
	body.TextColor3 = Color3.fromRGB(40, 50, 80)
	body.Text = "1. Stand on a pad with your friends\n2. Pop every bubble in the room\n3. Sell your scraps at the chute\n4. Upgrade and clear it FAST!"
	body.Parent = gui
	gui.Parent = board

end

local function buildFountain()
	-- bubble fountain: round basin, water, a giant bubble floating in the middle, water jets
	local f = at(-38, 0, 16)
	vcyl("FountainRim", f + Vector3.new(0, 1.1, 0), 21, 2.2, C.lightBlue)
	vcyl("FountainWall", f + Vector3.new(0, 1.2, 0), 20, 2.4, C.white)
	vcyl("Water", f + Vector3.new(0, 2.0, 0), 18, 0.6, Color3.fromRGB(70, 180, 255), { transparency = 0.15, solid = false })
	vcyl("FountainColumn", f + Vector3.new(0, 3.5, 0), 3, 4, C.white)
	vcyl("FountainCup", f + Vector3.new(0, 5.6, 0), 6, 0.6, C.lightBlue)
	local bubble = ball("FountainBubble", f + Vector3.new(0, 10, 0), 8, Color3.fromRGB(190, 235, 255), { mat = GLASS, transparency = 0.25, solid = false })
	ball("FountainShine", f + Vector3.new(-1.6, 11.6, 3), 1.6, Color3.new(1, 1, 1), { solid = false })
	local rise = Instance.new("ParticleEmitter") -- little bubbles drifting up
	rise.Rate = 3
	rise.Lifetime = NumberRange.new(2, 3)
	rise.Speed = NumberRange.new(2, 3)
	rise.SpreadAngle = Vector2.new(40, 40)
	rise.Size = NumberSequence.new(0.6, 0.2)
	rise.Transparency = NumberSequence.new(0.3, 1)
	rise.Color = ColorSequence.new(Color3.fromRGB(200, 240, 255))
	rise.Parent = bubble
	for k = 0, 5 do
		local a = math.rad(k * 60)
		local npos = f + Vector3.new(math.cos(a) * 8.5, 2.6, math.sin(a) * 8.5)
		local dir = (f + Vector3.new(0, 9, 0) - npos).Unit
		local nozzle = part("Nozzle", Vector3.new(0.6, 0.6, 0.6), CFrame.lookAt(npos, npos + dir) * CFrame.Angles(-math.pi / 2, 0, 0), C.gold, { solid = false })
		local jet = Instance.new("ParticleEmitter")
		jet.EmissionDirection = Enum.NormalId.Top
		jet.Rate = 30
		jet.Lifetime = NumberRange.new(0.9, 1)
		jet.Speed = NumberRange.new(13, 14)
		jet.SpreadAngle = Vector2.new(3, 3)
		jet.Acceleration = Vector3.new(0, -32, 0)
		jet.Size = NumberSequence.new(0.5, 0.25)
		jet.Transparency = NumberSequence.new(0.2, 0.6)
		jet.Color = ColorSequence.new(Color3.fromRGB(170, 225, 255))
		jet.Parent = nozzle
	end

end

local function buildDisplay()
	-- bubble display: a rare rainbow bubble in a glass case
	local dpos = at(-26, 0, -6)
	vcyl("DisplayBase", dpos + Vector3.new(0, 0.6, 0), 8, 1.2, C.gold)
	vcyl("DisplayPedestal", dpos + Vector3.new(0, 2.2, 0), 6.5, 2, C.white)
	part("DisplayCase", Vector3.new(6, 7, 6), dpos + Vector3.new(0, 6.7, 0), Color3.fromRGB(220, 240, 255), { mat = GLASS, transparency = 0.7 })
	part("DisplayLid", Vector3.new(6.6, 0.6, 6.6), dpos + Vector3.new(0, 10.5, 0), C.gold)
	for _, c in { { -1, -1 }, { -1, 1 }, { 1, -1 }, { 1, 1 } } do
		part("DisplayPost", Vector3.new(0.5, 7, 0.5), dpos + Vector3.new(c[1] * 2.9, 6.7, c[2] * 2.9), C.gold)
	end
	local rb = ball("RainbowBubble", dpos + Vector3.new(0, 6.5, 0), 4.2, Color3.fromRGB(255, 130, 220), { solid = false })
	rb.Reflectance = 0.15
	ball("RainbowShine", dpos + Vector3.new(-0.8, 7.4, 1.4), 1, Color3.new(1, 1, 1), { solid = false })
	local hl = Instance.new("Highlight") -- rainbow-ish rim so it pops out of the case
	hl.FillTransparency = 1
	hl.OutlineColor = Color3.fromRGB(255, 220, 80)
	hl.DepthMode = Enum.HighlightDepthMode.Occluded
	hl.Parent = rb
	local sparkle = Instance.new("ParticleEmitter")
	sparkle.Rate = 8
	sparkle.Lifetime = NumberRange.new(0.8, 1.4)
	sparkle.Speed = NumberRange.new(1, 2)
	sparkle.SpreadAngle = Vector2.new(180, 180)
	sparkle.Size = NumberSequence.new(0.5, 0)
	sparkle.LightEmission = 0.6
	sparkle.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 90)),
		ColorSequenceKeypoint.new(0.25, Color3.fromRGB(255, 220, 60)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(80, 220, 120)),
		ColorSequenceKeypoint.new(0.75, Color3.fromRGB(80, 160, 255)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 100, 255)),
	})
	sparkle.Parent = rb
	label(rb, "RAINBOW BUBBLE", 6, 10, 2, Color3.fromRGB(255, 225, 80))
end

local function buildBooths()
	for i, s in HubConfig.booths do
		local accent = color(HubConfig.colors.booths[i])
		local pos = at(s[1], 0, s[2])
		local face = CFrame.lookAt(pos, pos - Vector3.xAxis) -- open side faces the middle
		local k = HubConfig.boothScale or 1 -- everything in the booth is built at this size
		local function piece(name, size, x, y, zz, col, opts)
			return part(name, size * k, face * CFrame.new(x * k, y * k, zz * k), col, opts)
		end
		piece("BoothBody", Vector3.new(9, 6, 7), 0, 3, 0, accent)
		piece("BoothTrim", Vector3.new(9.4, 0.5, 7.4), 0, 6.25, 0, C.gold)
		piece("BoothWindow", Vector3.new(6, 2.6, 0.3), 0, 3.8, -3.55, Color3.fromRGB(40, 50, 80))
		piece("BoothSill", Vector3.new(7, 0.5, 1.2), 0, 2.3, -3.9, C.white)
		-- striped awning roof
		for k = 0, 4 do
			piece("Awning", Vector3.new(2, 0.6, 8.4), -4 + k * 2, 7, -0.5, k % 2 == 0 and C.white or accent)
		end
		piece("RoofTop", Vector3.new(7, 1.6, 5), 0, 8.1, 0, C.white)
		local roofBall = part("RoofBall", Vector3.new(2, 2, 2) * k, (face * CFrame.new(0, 9.6 * k, 0)).Position, C.gold, { shape = BALL })
		label(roofBall, "COMING SOON", 3, 10, 2.2, Color3.new(1, 1, 1))
		-- round pad in front
		local padPos = (face * CFrame.new(0, 0, -7.5 * k)).Position
		vcyl("BoothPadRing", padPos + Vector3.new(0, 0.15, 0), 7 * k, 0.3, accent, { mat = NEON, transparency = 0.2, shadow = false })
		vcyl("BoothPad", padPos + Vector3.new(0, 0.2, 0), 5.6 * k, 0.3, C.white, { shadow = false })
	end
end

local function buildChest()
	local pos = at(-24, 0, 40)
	local face = CFrame.lookAt(pos, at(-14, 0, 20))
	local red, gold = Color3.fromRGB(230, 60, 90), C.gold
	vcyl("ChestGlow", pos + Vector3.new(0, 0.15, 0), 10, 0.3, Color3.fromRGB(200, 150, 20), { mat = NEON, transparency = 0.35, shadow = false })
	part("ChestBody", Vector3.new(6, 3.5, 4), face * CFrame.new(0, 2.05, 0), red)
	part("ChestLid", Vector3.new(6, 4, 4), face * CFrame.new(0, 3.8, 0), red, { shape = CYL })
	for _, dx in { -2, 2 } do
		part("ChestBand", Vector3.new(0.6, 3.6, 4.1), face * CFrame.new(dx, 2.05, 0), gold)
		part("ChestBandLid", Vector3.new(0.6, 4.1, 4.1), face * CFrame.new(dx, 3.8, 0), gold, { shape = CYL })
	end
	local lock = part("ChestLock", Vector3.new(1.2, 1.4, 0.4), face * CFrame.new(0, 3.6, -2.1), gold)
	local light = Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 210, 90)
	light.Range = 12
	light.Brightness = 1.5
	light.Parent = lock
	local sp = Instance.new("Sparkles")
	sp.SparkleColor = Color3.fromRGB(255, 220, 80)
	sp.Parent = lock
	local t = label(lock, "FREE GIFT!", 4.5, 9, 2.2, Color3.new(1, 1, 1))
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 120, 120)),
		ColorSequenceKeypoint.new(0.35, Color3.fromRGB(255, 230, 90)),
		ColorSequenceKeypoint.new(0.7, Color3.fromRGB(120, 230, 140)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(120, 190, 255)),
	})
	g.Parent = t
end


---------------------------------------------------------------- gumball theme pieces
local GUM = (HubConfig.colors.gumballs or {}) :: { any }
local function gumColor(rng: Random): Color3
	return color(GUM[rng:NextInteger(1, #GUM)])
end

-- one gumball: the uploaded glossy mesh (tinted), or a plain ball if it didn't load
local function gumball(name: string, pos: Vector3, d: number, col: Color3, solid: boolean?): BasePart
	local assets = ReplicatedStorage:FindFirstChild("BubbleAssets")
	local template = assets and assets:FindFirstChild("Gumball") :: MeshPart?
	if not template then
		return ball(name, pos, d, col, { solid = solid == true, shadow = false, gloss = 0.15 })
	end
	local g = template:Clone()
	g.Name = name
	g.Size = Vector3.new(d, d, d)
	g.CFrame = CFrame.new(pos) * CFrame.Angles(math.random() * 6.3, math.random() * 6.3, 0)
	g.Color = col
	g.CanCollide = solid == true
	g.CanQuery = solid == true
	g.CastShadow = solid == true
	local look = g:FindFirstChildOfClass("SurfaceAppearance")
	if look then
		look.Color = col
	end
	g.Parent = folder
	return g
end

-- a giant gumball machine where the HQ stands: red base, coin slot and knob, a glass globe full of gumballs
local function buildGumballMachine()
	local z = -45
	local red = C.blue
	vcyl("MachineStage", at(0, 0.75, z), 28, 1.5, C.lavender)
	part("MachineStageEdge", Vector3.new(28.6, 0.4, 0.4), at(0, 1.3, z + 14.1), C.gold)
	part("MachineBase", Vector3.new(18, 12, 16), at(0, 7.5, z), red)
	part("MachineBaseTrim", Vector3.new(18.6, 0.8, 16.6), at(0, 1.9, z), C.gold)
	vcyl("MachineNeck", at(0, 14.5, z), 20, 2, red)
	vcyl("MachineCollar", at(0, 15.8, z), 22, 0.8, C.gold)
	-- coin slot plate, turning knob and the chute where gumballs come out
	local front = z + 8.05
	part("CoinPlate", Vector3.new(6, 6, 0.4), at(0, 8.5, front), Color3.fromRGB(215, 220, 230), { mat = Enum.Material.Metal })
	part("CoinSlot", Vector3.new(0.5, 2, 0.2), at(0, 10, front + 0.25), Color3.fromRGB(40, 40, 50))
	part("Knob", Vector3.new(1, 3.6, 3.6), CFrame.new(at(0, 7.6, front + 0.6)) * FACE_Z, C.white, { shape = CYL })
	part("KnobBar", Vector3.new(3.2, 0.7, 0.6), at(0, 7.6, front + 1.2), Color3.fromRGB(215, 220, 230), { mat = Enum.Material.Metal })
	part("Chute", Vector3.new(5, 3, 0.3), at(0, 3.6, front), Color3.fromRGB(50, 40, 60))
	part("ChuteFlap", Vector3.new(5.4, 0.5, 1.6), at(0, 2.3, front + 0.7), Color3.fromRGB(215, 220, 230), { mat = Enum.Material.Metal })
	-- the glass globe, two thirds full of gumballs
	local gc = at(0, 29, z)
	local R = 14
	local rng = Random.new(5)
	local n = 0
	while n < 110 do
		local v = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(-1, 1), rng:NextNumber(-1, 1))
		if v.Magnitude <= 1 and v.Y < 0.25 then
			n += 1
			gumball("Gumball", gc + v * (R - 2.2), 3.8, gumColor(rng))
		end
	end
	ball("Globe", gc, R * 2, Color3.fromRGB(235, 248, 255), { mat = GLASS, transparency = 0.6, shadow = false })
	ball("GlobeShine", gc + Vector3.new(-5, 6, 10.5), 3, Color3.new(1, 1, 1), { solid = false, shadow = false })
	vcyl("GlobeCap", at(0, 43, z), 10, 2.4, red)
	ball("GlobeKnob", at(0, 45, z), 3.6, red)
	-- the logo as a banner across the machine's neck
	local lz = z + 11
	part("LogoRim", Vector3.new(37.5, 8.5, 1), at(0, 17.5, lz - 0.6), C.white)
	for _, sx in { -1, 1 } do
		part("LogoRimEnd", Vector3.new(1, 8.5, 8.5), CFrame.new(at(sx * 18.75, 17.5, lz - 0.6)) * FACE_Z, C.white, { shape = CYL })
		part("LogoEnd", Vector3.new(1.4, 7, 7), CFrame.new(at(sx * 18.75, 17.5, lz)) * FACE_Z, red, { shape = CYL })
	end
	local plaque = part("Logo", Vector3.new(37.5, 7, 1.4), CFrame.lookAt(at(0, 17.5, lz), at(0, 17.5, 100)), red)
	sign(plaque, Enum.NormalId.Front, "BUBBLE POP", Color3.new(1, 1, 1), Color3.fromRGB(120, 10, 30), 11)
	part("LogoShine", Vector3.new(34, 2.2, 0.2), at(0, 19.4, lz + 0.8), Color3.new(1, 1, 1), { transparency = 0.65, solid = false, shadow = false })
end

-- a gumball pit where the fountain was: big bouncy gumballs to kick around while you wait
local function buildGumballPit()
	local c = at(-38, 0, 16)
	local rng = Random.new(3)
	vcyl("PitFloor", c + Vector3.new(0, 0.15, 0), 20, 0.3, C.lightBlue, { shadow = false })
	for k = 0, 15 do
		local a = k / 16 * math.pi * 2
		local pos = c + Vector3.new(math.cos(a) * 10.5, 1.5, math.sin(a) * 10.5)
		part("PitWall", Vector3.new(4.4, 3, 1), CFrame.lookAt(pos, c + Vector3.new(0, 1.5, 0)), k % 2 == 0 and C.white or C.blue)
	end
	for k = 1, 7 do
		local a = k / 7 * math.pi * 2
		local g = gumball("BouncyGumball", c + Vector3.new(math.cos(a) * 5, 3, math.sin(a) * 5), 4, gumColor(rng), true)
		g.Anchored = false
		g.CustomPhysicalProperties = PhysicalProperties.new(0.3, 0.3, 0.8, 1, 1) -- light and bouncy
	end
	local sign0 = part("PitSign", Vector3.new(1, 1, 1), c + Vector3.new(0, 1, -10.5), C.white, { transparency = 1, solid = false })
	label(sign0, "GUMBALL PIT", 6, 10, 2.2, color(HubConfig.colors.pink))
end

-- a big gumball jar where the rainbow bubble display was
local function buildCandyJar()
	local d = at(-26, 0, -6)
	local rng = Random.new(9)
	vcyl("JarBase", d + Vector3.new(0, 0.6, 0), 8, 1.2, C.gold)
	vcyl("JarPedestal", d + Vector3.new(0, 2.2, 0), 6.5, 2, C.white)
	for _ = 1, 40 do
		local a, r = rng:NextNumber(0, math.pi * 2), rng:NextNumber(0, 2)
		gumball("JarGumball", d + Vector3.new(math.cos(a) * r, rng:NextNumber(4, 8.5), math.sin(a) * r), 1.6, gumColor(rng))
	end
	local jar = vcyl("Jar", d + Vector3.new(0, 7, 0), 6.2, 7.6, Color3.fromRGB(235, 248, 255), { mat = GLASS, transparency = 0.65 })
	vcyl("JarLid", d + Vector3.new(0, 11.1, 0), 6.8, 0.8, C.blue)
	ball("JarLidKnob", d + Vector3.new(0, 11.8, 0), 1.6, C.blue)
	label(jar, "GUMBALL JAR", 7, 10, 2, color(HubConfig.colors.pink))
end

-- a lollipop tree: a white stick with a round candy (and a swirl) on top
local function lollipop(base: Vector3, s: number, rng: Random)
	vcyl("LollyStick", base + Vector3.new(0, 4.5 * s, 0), 0.9 * s, 9 * s, C.white)
	local cf = CFrame.new(base + Vector3.new(0, 11 * s, 0)) * CFrame.Angles(0, rng:NextNumber(0, math.pi), 0) * FACE_Z
	part("Lolly", Vector3.new(1.4 * s, 8 * s, 8 * s), cf, gumColor(rng), { shape = CYL })
	part("LollySwirl", Vector3.new(1.6 * s, 4.5 * s, 4.5 * s), cf, C.white, { shape = CYL })
	part("LollyMiddle", Vector3.new(1.8 * s, 2 * s, 2 * s), cf, gumColor(rng), { shape = CYL })
end

local function buildScenery()
	local rng = Random.new(7)
	local greens = { Color3.fromRGB(80, 180, 80), Color3.fromRGB(100, 195, 85), Color3.fromRGB(65, 160, 75) }
	-- puffy clouds: a thick cloud floor far below (hides the popping room), and a few puffs around
	local cloud = Color3.fromRGB(255, 255, 255)
	local function puff(c: Vector3, size: number)
		for _ = 1, rng:NextInteger(3, 5) do
			local off = Vector3.new(rng:NextNumber(-0.6, 0.6) * size, rng:NextNumber(-0.15, 0.2) * size, rng:NextNumber(-0.6, 0.6) * size)
			ball("Cloud", c + off, size * rng:NextNumber(0.6, 1), cloud, { solid = false, shadow = false, gloss = 0 })
		end
	end
	for _ = 1, 110 do
		local a, r = rng:NextNumber(0, math.pi * 2), rng:NextNumber(40, 700)
		puff(at(math.cos(a) * r, rng:NextNumber(-130, -110), math.sin(a) * r), rng:NextNumber(40, 80))
	end
	for _ = 1, 14 do
		local a, r = rng:NextNumber(0, math.pi * 2), rng:NextNumber(170, 400)
		puff(at(math.cos(a) * r, rng:NextNumber(-50, 40), math.sin(a) * r), rng:NextNumber(14, 28))
	end
	-- round cartoon trees on the island, between the plaza and the glass
	local placed = 0
	local maxR = HubConfig.island.radius - 12
	while placed < 26 do
		local x, z = rng:NextNumber(-maxR, maxR), rng:NextNumber(-maxR, maxR)
		if math.max(math.abs(x), math.abs(z)) > 64 and math.sqrt(x * x + z * z) < maxR then
			placed += 1
			local s = rng:NextNumber(0.8, 1.4)
			local base = at(x, -3, z)
			if HubConfig.theme == "gumball" then
				lollipop(base, s, rng)
				continue
			end
			vcyl("Trunk", base + Vector3.new(0, 4 * s, 0), 1.8 * s, 8 * s, Color3.fromRGB(140, 95, 60))
			local g = greens[rng:NextInteger(1, #greens)]
			ball("Leaves", base + Vector3.new(0, 10 * s, 0), 9 * s, g)
			ball("Leaves", base + Vector3.new(2 * s, 8 * s, 1 * s), 6 * s, g)
			ball("Leaves", base + Vector3.new(-2 * s, 8.5 * s, -1 * s), 6.5 * s, g)
		end
	end
end

-- The giant glass bubble over the hub. One big ball is invisible from inside (back faces aren't
-- drawn), so it's built from thin curved-glass panels: rings of panels from the ground to the top.
local function buildDome()
	local R, cy = HubConfig.dome.radius, HubConfig.dome.centreY
	local centre = at(0, cy, 0)
	local e0 = math.asin(math.clamp((-3 - cy) / R, -1, 1)) -- where the bubble meets the grass
	local bands = 10
	local de = (math.pi / 2 - e0) / bands
	local sheen = { -- a soft rainbow sheen from bottom to top, like a soap bubble
		C.dome, Color3.fromRGB(190, 240, 255), Color3.fromRGB(200, 255, 235), Color3.fromRGB(230, 220, 255), C.dome,
	}
	for b = 0, bands - 1 do
		local ea, eb = e0 + b * de, e0 + (b + 1) * de
		local em = (ea + eb) / 2
		local ring = R * math.cos(ea) -- widest edge of this band
		local n = math.max(6, math.floor(2 * math.pi * ring / 14 + 0.5))
		local w = 2 * ring * math.sin(math.pi / n) + 0.3
		local h = 2 * R * math.sin(de / 2) + 0.3
		local d = R * math.cos(de / 2)
		local col = sheen[math.floor(b / bands * (#sheen - 1) + 0.5) + 1]
		for k = 0, n - 1 do
			local phi = (k + (b % 2) * 0.5) / n * math.pi * 2
			local dir = Vector3.new(math.cos(em) * math.cos(phi), math.sin(em), math.cos(em) * math.sin(phi))
			local pos = centre + dir * d
			-- a bright window-like reflection on one side of the bubble
			local shine = em > 0.55 and em < 1.05 and phi > 3.6 and phi < 4.3
			part("Dome", Vector3.new(w, h, 0.3), CFrame.lookAt(pos, centre, Vector3.yAxis), shine and Color3.new(1, 1, 1) or col, {
				mat = Enum.Material.Glass,
				transparency = shine and 0.45 or 0.72,
				solid = b < 2, -- the low glass is a wall: nowhere to go but the island
				shadow = false,
			})
		end
	end
	-- (the floating bubbles are drawn and moved by each player: Controllers/HubBubbles)
end

function Hub.build()
	local gumball = HubConfig.theme == "gumball"
	buildPlaza()
	if gumball then
		buildGumballMachine()
		buildGumballPit()
		buildCandyJar()
	else
		buildHQ()
		buildFountain()
		buildDisplay()
	end
	buildPads()
	buildLeft()
	buildBooths()
	buildChest()
	buildScenery()
	buildDome()
	folder.Parent = workspace
end

-- Pads: who's standing on them, countdowns, start
function Hub.start(hooks)
	local StartPad = Instance.new("RemoteEvent")
	StartPad.Name = "StartPad" -- client -> server: the pad owner presses Start
	StartPad.Parent = ReplicatedStorage:WaitForChild("Remotes")

	local pads = {}
	for i = 1, #HubConfig.pads do
		pads[i] = LobbyRules.newPad()
	end
	local startNow: { [number]: boolean } = {}

	StartPad.OnServerEvent:Connect(function(player)
		for i, pad in pads do
			if LobbyRules.owner(pad) == player.UserId then
				startNow[i] = true
			end
		end
	end)

	local function show(i: number)
		local pad, part = pads[i], padParts[i]
		local text = part:FindFirstChild("Info") and part.Info:FindFirstChild("Text") :: TextLabel?
		part:SetAttribute("Members", #pad.members)
		part:SetAttribute("Owner", LobbyRules.owner(pad) or 0)
		part:SetAttribute("Countdown", pad.countdown and math.ceil(pad.countdown) or 0)
		if text then
			local line2 = ("%d/%d"):format(#pad.members, HubConfig.maxPlayers)
			if #pad.members > 0 then
				line2 ..= hooks.canStart() and ("  •  " .. math.max(0, math.ceil(pad.countdown or 0))) or "  •  room busy"
			end
			text.Text = ("PAD %d\n%s"):format(i, line2)
		end
	end

	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.2 then
			return
		end
		local step = acc
		acc = 0
		for i, pad in pads do
			local centre = padParts[i].Position
			local standing = {}
			for _, p in Players:GetPlayers() do
				local char = p.Character
				local r = char and char:FindFirstChild("HumanoidRootPart") :: BasePart?
				if r and not hooks.inRun(p) then
					local dx, dz = math.abs(r.Position.X - centre.X), math.abs(r.Position.Z - centre.Z)
					if dx <= HubConfig.padSize[1] / 2 + 0.5 and dz <= HubConfig.padSize[2] / 2 + 0.5 and math.abs(r.Position.Y - centre.Y) < 6 then
						table.insert(standing, p.UserId)
					end
				end
			end
			LobbyRules.update(pad, standing, HubConfig.maxPlayers)
			-- the owner sees the Start panel
			for _, p in Players:GetPlayers() do
				if p:GetAttribute("PadOwner") == i and LobbyRules.owner(pad) ~= p.UserId then
					p:SetAttribute("PadOwner", nil)
				end
			end
			local owner = LobbyRules.owner(pad)
			local ownerPlayer = owner and Players:GetPlayerByUserId(owner)
			if ownerPlayer then
				ownerPlayer:SetAttribute("PadOwner", i)
			end
			local ready = hooks.canStart()
			local fire = ready and LobbyRules.tick(pad, step, HubConfig.countdown)
			if not ready and #pad.members > 0 then
				pad.countdown = HubConfig.countdown -- wait for the room
			end
			if ready and startNow[i] and #pad.members > 0 then
				fire = true
			end
			startNow[i] = nil
			if fire then
				local group = {}
				for _, id in pad.members do
					local p = Players:GetPlayerByUserId(id)
					if p then
						table.insert(group, p)
						p:SetAttribute("PadOwner", nil)
					end
				end
				pads[i] = LobbyRules.newPad()
				hooks.startRun(group, 1)
			end
			show(i)
		end
	end)
end

return Hub
