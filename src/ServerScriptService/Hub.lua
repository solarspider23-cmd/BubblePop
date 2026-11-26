-- The lobby hub: builds the plaza (HQ + logo, 4 play pads, fountain, booths, gift chest, scenery)
-- and runs the pads.
-- Main calls Hub.start({ canStart = fn() -> boolean, startRun = fn(players, roomIndex), inRun = fn(player) -> boolean }).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local HubConfig = require(Shared.Config.Hub)
local LobbyRules = require(Shared.Rules.Lobby)
local Models = require(Shared.Config.Models)
local Piles = require(Shared.Config.GumballPiles)
local HubPolish = require(script.Parent.HubPolish)

local Hub = {}

local O = Vector3.new(HubConfig.origin[1], HubConfig.origin[2], HubConfig.origin[3])
local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local C = {}
for k, v in HubConfig.colors do
	if type(v) == "table" and type(v[1]) == "number" then
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
local function sign(parent: BasePart, face: Enum.NormalId, text: string, col: Color3?, strokeCol: Color3?, pixelsPerStud: number?): TextLabel
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
	return t
end

-- Floating text above a part. Clean theme: a rounded pastel panel with a white edge, bold white
-- text and an optional icon (fill = panel colour).
local function label(parent: BasePart, text: string, height: number, w: number, h: number, col: Color3?, icon: string?, fill: Color3?): TextLabel
	if HubConfig.theme == "clean" then
		local bb = Instance.new("BillboardGui")
		bb.Name = "Info"
		bb.Size = UDim2.fromScale(w, h)
		bb.StudsOffsetWorldSpace = Vector3.new(0, height, 0)
		bb.LightInfluence = 0
		bb.MaxDistance = 160
		local panel = Instance.new("Frame")
		panel.Size = UDim2.fromScale(1, 1)
		panel.BackgroundColor3 = fill or Color3.fromRGB(46, 155, 255)
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.45, 0)
		corner.Parent = panel
		local edge = Instance.new("UIStroke")
		edge.Thickness = 3
		edge.Color = Color3.new(1, 1, 1)
		edge.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		edge.Parent = panel
		local grad = Instance.new("UIGradient") -- a little lighter at the top: glossy
		grad.Rotation = 90
		grad.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(215, 215, 225))
		grad.Parent = panel
		local t = Instance.new("TextLabel")
		t.Name = "Text"
		t.Size = UDim2.fromScale(0.86, 0.72)
		t.Position = UDim2.fromScale(0.07, 0.14)
		t.BackgroundTransparency = 1
		t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
		t.TextScaled = true
		t.TextColor3 = Color3.new(1, 1, 1)
		t.Text = icon and (icon .. " " .. text) or text
		stroke(t, 2, Color3.fromRGB(20, 50, 120))
		t.Parent = panel
		panel.Parent = bb
		bb.Parent = parent
		return t
	end
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

---------------------------------------------------------------- uploaded lobby models
-- Main loads the theme's sets (Config/Models.hub: candy, gumball theme; Models.hubClean: Clean Pop
-- Plaza, clean theme, plus the candy sets in HubConfig.modelsClean.reuse) into
-- ReplicatedStorage.HubAssets/<set>/<mesh>. Each build function uses a set when it's there and its
-- part-built pieces when it isn't.
local THEME = HubConfig.theme
local CLEAN = THEME == "clean"
local MD = (CLEAN and HubConfig.modelsClean or HubConfig.models) or {}
local REUSE: { [string]: boolean } = {}
for _, k in (CLEAN and MD.reuse) or {} do
	REUSE[k] = true
end
local function setDef(set: string): any
	return (Models.hubClean and Models.hubClean[set]) or (Models.hub and Models.hub[set])
end
local function has(set: string): boolean
	local ok
	if THEME == "gumball" then
		ok = Models.hub ~= nil and Models.hub[set] ~= nil
	elseif CLEAN then
		ok = (Models.hubClean ~= nil and Models.hubClean[set] ~= nil) or (REUSE[set] == true and Models.hub ~= nil and Models.hub[set] ~= nil)
	else
		ok = false
	end
	if not ok then
		return false
	end
	local a = ReplicatedStorage:FindFirstChild("HubAssets")
	return a ~= nil and a:FindFirstChild(set) ~= nil
end

-- One mesh of a set, placed by its model's origin (origin = where the model's bottom centre
-- stands, its front facing the CFrame's look direction).
-- opts: scale, tint (texture colour), color (plain colour), mat, transparency, shadow, name, pivot (model-space point)
local function mesh(set: string, name: string, origin: CFrame, opts: { [string]: any }?): MeshPart
	local o = opts or {}
	local s = o.scale or 1
	local a = ReplicatedStorage:FindFirstChild("HubAssets") :: Folder
	local template = (a:FindFirstChild(set) :: Folder):FindFirstChild(name) :: MeshPart
	local c = setDef(set).meshes[name]
	local m = template:Clone()
	m.Name = o.name or name
	m.Size = template.Size * s
	m.CFrame = origin * CFrame.new(c[1] * s, c[2] * s, c[3] * s)
	if o.tint then
		m.Color = o.tint
		local look = m:FindFirstChildOfClass("SurfaceAppearance")
		if look then
			look.Color = o.tint
		end
	end
	if o.color then -- a plain-colour piece: no texture
		m.Color = o.color
		local look = m:FindFirstChildOfClass("SurfaceAppearance")
		if look then
			look:Destroy()
		end
	end
	if o.mat then
		m.Material = o.mat
	end
	if o.gloss then
		m.Reflectance = o.gloss
	end
	m.Transparency = o.transparency or 0
	m.CastShadow = o.shadow ~= false
	if o.pivot then -- a hinge or spin point, so the piece can be turned about it later
		local p = o.pivot
		m.PivotOffset = m.CFrame:ToObjectSpace(origin * CFrame.new(p[1] * s, p[2] * s, p[3] * s))
	end
	m.Parent = o.parent or folder
	return m
end

-- an invisible solid block for walking on and bumping into (meshes don't collide)
local function blocker(name: string, size: Vector3, cf: any, shape: Enum.PartType?): Part
	return part(name, size, cf, Color3.new(1, 1, 1), { transparency = 1, shadow = false, shape = shape })
end

local function glassOpts(): { [string]: any }
	return { mat = Enum.Material.Glass, color = color(MD.glass), transparency = MD.glassTransparency, shadow = false }
end
local function shineOpts(): { [string]: any }
	return { color = color(MD.shine), transparency = MD.shineTransparency, shadow = false }
end

Hub.spawnCFrame =CFrame.lookAt(at(HubConfig.spawn[1], HubConfig.spawn[2], HubConfig.spawn[3]), at(0, HubConfig.spawn[2], -10))

local padParts: { BasePart } = {}

---------------------------------------------------------------- pieces

-- quarter turns for a corner piece whose unturned shape fills the +X / -Z quadrant
local function cornerTurn(sx: number, sz: number): CFrame
	local q = (sx > 0 and sz < 0) and 0 or (sx < 0 and sz < 0) and 1 or (sx < 0 and sz > 0) and 2 or 3
	return CFrame.Angles(0, q * math.pi / 2, 0)
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

-- a low-detail gumball (globe, jar, fence corners): the 300-triangle mesh, or the full one if it's missing
local function lowGumball(name: string, pos: Vector3, d: number, col: Color3): BasePart
	if not has("GumballLo") then
		return gumball(name, pos, d, col)
	end
	local g = mesh("GumballLo", "GumballLo", CFrame.new(pos) * CFrame.Angles(math.random() * 6.3, math.random() * 6.3, 0), { name = name, scale = d, tint = col, shadow = false })
	return g
end

local function buildPlaza()
	local S = HubConfig.size
	local half = S / 2
	-- a floating island in the sky: grassy top, a frosting drip, then a chocolate underside that
	-- narrows to a point (candy theme), with clouds below. The plaza sits 3 studs above the grass.
	local isl = HubConfig.island
	part("Grass", Vector3.new(5, isl.radius * 2, isl.radius * 2), CFrame.new(at(0, -5.5, 0)) * UP, C.grass, { mat = HubConfig.colors.grassSmooth and Enum.Material.SmoothPlastic or Enum.Material.Grass, shape = CYL })
	if has("CleanIsland") then -- white bumper rim with a sky-blue band, soft white rock tiers, pastel crystals
		local io = CFrame.new(at(0, -3, 0))
		mesh("CleanIsland", "CleanIsland_Rim", io)
		mesh("CleanIsland", "CleanIsland_Under", io, { shadow = false })
		mesh("CleanIsland", "CleanIsland_Crystal", io, { shadow = false })
		mesh("CleanIsland", "CleanIsland_Glow", io, { mat = NEON, color = color(MD.glow), shadow = false })
	elseif has("Island") then -- cake slice: frosting rim with drips, chocolate tiers underneath
		mesh("Island", "Island_Rim", CFrame.new(at(0, -3, 0)))
		mesh("Island", "Island_Under", CFrame.new(at(0, -3, 0)), { shadow = false })
	else
		local under = HubConfig.theme == "gumball" and Color3.fromRGB(110, 65, 45) or Color3.fromRGB(150, 110, 80)
		vcyl("Frosting", at(0, -8.5, 0), isl.radius * 2 + 1, 1.6, C.lavender)
		for k, layer in { { 0.97, 8 }, { 0.86, 9 }, { 0.7, 9 }, { 0.5, 9 }, { 0.3, 8 }, { 0.14, 7 } } do
			local y = -9.3 - (k - 0.5) * 8.6
			vcyl("IslandRock", at(0, y, 0), isl.radius * 2 * layer[1], layer[2], under, { mat = Enum.Material.Slate, shadow = false })
		end
	end
	part("Plaza", Vector3.new(S, 2.8, S), at(0, -1.6, 0), C.white)
	local ground = has("Ground")
	if ground then -- rounded kerb round the slab, like a cake board: 8 pieces a side + 4 corners
		for _, side in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
			local out = Vector3.new(side[1], 0, side[2])
			for k = 0, 7 do
				local u = -49 + k * 14
				local pos = at(side[1] * half, -3, side[2] * half) + (side[1] == 0 and Vector3.new(u, 0, 0) or Vector3.new(0, 0, u))
				local cf = CFrame.lookAt(pos, pos + out)
				mesh("Ground", "Ground_Kerb", cf, { color = color(MD.kerb) })
				mesh("Ground", "Ground_KerbBand", cf, { color = color(MD.kerbBand) })
			end
		end
		for _, c in { { 1, 1 }, { 1, -1 }, { -1, 1 }, { -1, -1 } } do
			local cf = CFrame.new(at(c[1] * half, -3, c[2] * half)) * cornerTurn(c[1], c[2])
			mesh("Ground", "Ground_KerbCorner", cf, { color = color(MD.kerb) })
			mesh("Ground", "Ground_KerbCornerBand", cf, { color = color(MD.kerbBand) })
		end
	else
		part("PlazaTrim", Vector3.new(S + 1, 0.8, S + 1), at(0, -2.6, 0), C.blue)
	end
	-- clean theme: one classic studded floor in a soft warm off-white (no checkerboard)
	local n = 8
	if CLEAN and HubConfig.colors.floor then
		part("Floor", Vector3.new(S, 0.2, S), at(0, -0.1, 0), color(HubConfig.colors.floor), { mat = Enum.Material.Plastic, studs = true, shadow = false })
		n = 0
	end
	-- checkerboard of tiles
	local t = S / n
	for i = 0, n - 1 do
		for j = 0, n - 1 do
			local x, z = -half + t * (i + 0.5), -half + t * (j + 0.5)
			local col = (i + j) % 2 == 0 and C.tileA or C.tileB
			if ground then
				mesh("Ground", "Ground_Tile", CFrame.new(at(x, -0.2, z)), { name = "Tile", color = col, shadow = false })
			else
				part("Tile", Vector3.new(t, 0.2, t), at(x, -0.1, z), col, { shadow = false, gloss = 0.1 })
			end
		end
	end
	-- low fence: posts with little glowing caps and rails
	local edge = half - 1
	if has("CleanFence") then
		-- white posts with sky-blue bands and glowing caps, rails between, taller corner posts with a glow orb
		local step = edge / 7
		-- the modelled back hall stands across the back fence: leave the fence out there (the invisible wall stays)
		local hall = HubConfig.polish and HubConfig.polish.hall
		local hallHalf = (hall and has("CleanHall")) and 30 * (hall.scale or 1) or 0
		for _, side in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
			local alongX = side[2] ~= 0
			local turn = alongX and CFrame.identity or CFrame.Angles(0, math.pi / 2, 0) -- own X along the fence
			local function spot(u: number): CFrame
				local x, z = alongX and u or side[1] * edge, alongX and side[2] * edge or u
				return CFrame.new(at(x, 0, z)) * turn
			end
			local function hidden(u: number): boolean
				return side[2] == -1 and math.abs(u - (hall and hall.x or 0)) < hallHalf
			end
			for k = -6, 6 do
				if not hidden(k * step) then
					mesh("CleanFence", "CleanFence_Post", spot(k * step), { shadow = false })
					mesh("CleanFence", "CleanFence_PostGlow", spot(k * step), { mat = NEON, color = color(MD.glow), shadow = false })
				end
			end
			for k = -7, 6 do
				if not hidden((k + 0.5) * step) then
					mesh("CleanFence", "CleanFence_Rail", spot((k + 0.5) * step), { shadow = false })
				end
			end
			local wall = alongX and Vector3.new(S - 2, 3.4, 0.8) or Vector3.new(0.8, 3.4, S - 2)
			blocker("FenceWall", wall, at(alongX and 0 or side[1] * edge, 1.7, alongX and side[2] * edge or 0))
		end
		for _, c in { { 1, -1 }, { -1, -1 }, { -1, 1 }, { 1, 1 } } do
			local cf = CFrame.new(at(c[1] * edge, 0, c[2] * edge))
			mesh("CleanFence", "CleanFence_Corner", cf, { shadow = false })
			mesh("CleanFence", "CleanFence_CornerGlow", cf, { mat = NEON, color = color(MD.glow), shadow = false })
		end
	elseif has("Fence") and has("GumballLo") then
		-- candy-cane posts, glowing gumdrop caps, rails between, a gumball in each corner cup
		local step = edge / 7
		for _, side in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
			local alongX = side[2] ~= 0
			local turn = alongX and CFrame.identity or CFrame.Angles(0, math.pi / 2, 0) -- own X along the fence
			local function spot(u: number): CFrame
				local x, z = alongX and u or side[1] * edge, alongX and side[2] * edge or u
				return CFrame.new(at(x, 0, z)) * turn
			end
			for k = -6, 6 do
				mesh("Fence", "Fence_Post", spot(k * step), { shadow = false })
				mesh("Fence", "Fence_PostGlow", spot(k * step), { mat = NEON, color = C.glow, shadow = false })
			end
			for k = -7, 6 do
				mesh("Fence", "Fence_Rail", spot((k + 0.5) * step), { shadow = false })
			end
			-- invisible wall where the rails are (meshes don't collide)
			local wall = alongX and Vector3.new(S - 2, 3.4, 0.8) or Vector3.new(0.8, 3.4, S - 2)
			blocker("FenceWall", wall, at(alongX and 0 or side[1] * edge, 1.7, alongX and side[2] * edge or 0))
		end
		for k, c in { { 1, -1 }, { -1, -1 }, { -1, 1 }, { 1, 1 } } do
			local cf = CFrame.new(at(c[1] * edge, 0, c[2] * edge)) * cornerTurn(c[1], c[2])
			mesh("Fence", "Fence_Corner", cf, { shadow = false })
			local gi = MD.cornerGumballs[k] or 1
			lowGumball("CornerGumball", cf.Position + Vector3.new(0, 5.34, 0), 2.4, color(HubConfig.colors.gumballs[gi]))
		end
	else
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
	end
	-- spawn spot
	local sp = at(HubConfig.spawn[1], 0, HubConfig.spawn[3])
	if has("CleanSpawnPad") then -- white disc, bubble mark pointing at the pads
		mesh("CleanSpawnPad", "CleanSpawnPad_Body", CFrame.lookAt(sp, at(HubConfig.spawn[1], 0, HubConfig.pads[1][2])), { shadow = false })
	elseif has("SpawnPad") then -- star points at the pads
		mesh("SpawnPad", "SpawnPad_Body", CFrame.lookAt(sp, at(HubConfig.spawn[1], 0, HubConfig.pads[1][2])), { shadow = false })
	else
		vcyl("SpawnRing", sp + Vector3.new(0, 0.15, 0), 11, 0.3, C.blue)
		vcyl("SpawnDisc", sp + Vector3.new(0, 0.2, 0), 9.5, 0.3, C.white)
	end
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

local padText: { TextLabel } = {}
local padCount: { TextLabel } = {} -- (clean pad signs: the count on its own line)

local function buildPads()
	local w, d = HubConfig.padSize[1], HubConfig.padSize[2]
	local models = has("Pad") and has("PadSign")
	for i, xz in HubConfig.pads do
		local x, z = xz[1], xz[2]
		local col = color(HubConfig.colors.pad[i] or HubConfig.colors.pad[1])
		local pad: Part
		if has("CleanPad") and has("CleanPadSign") then
			-- pastel pad with a white rim and a glow line, and a sign standing just behind it, both facing the spawn
			local glow = HubConfig.colors.padGlow and HubConfig.colors.padGlow[i]
			local o = CFrame.lookAt(at(x, 0, z), at(x, 0, HubConfig.spawn[3]))
			mesh("CleanPad", "CleanPad_Body", o)
			mesh("CleanPad", "CleanPad_Tint", o, { tint = col })
			mesh("CleanPad", "CleanPad_Glow", o, { mat = NEON, color = glow and color(glow) or col, shadow = false })
			blocker("PadFloor", Vector3.new(13.5, 0.45, 10.5), at(x, 0.225, z)) -- walkable top at 0.45
			pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, 0.45, z), col, { transparency = 1, solid = false, shadow = false })
			local so = CFrame.lookAt(at(x, 0, z - 5.9), at(x, 0, HubConfig.spawn[3]))
			mesh("CleanPadSign", "CleanPadSign_Body", so)
			mesh("CleanPadSign", "CleanPadSign_Tint", so, { tint = col })
			blocker("PadSignPost", Vector3.new(8.2, 6.6, 0.8), so * CFrame.new(0, 3.3, 0))
			local face = part("PadSignFace", Vector3.new(8, 3, 0.05), so * CFrame.new(0, 5, -0.2), C.white, { transparency = 1, solid = false, shadow = false })
			-- big "PAD n" on top, the player count under it (readable from the spawn)
			local t = sign(face, Enum.NormalId.Front, ("PAD %d"):format(i), Color3.new(1, 1, 1), Color3.fromRGB(15, 60, 150), 40)
			t.Size = UDim2.fromScale(0.96, 0.62)
			t.Position = UDim2.fromScale(0.02, -0.02)
			local cnt = t:Clone()
			cnt.Text = ("0/%d"):format(HubConfig.maxPlayers)
			cnt.TextColor3 = color(HubConfig.colors.blue)
			local cs = cnt:FindFirstChildOfClass("UIStroke")
			if cs then
				cs.Color = Color3.new(1, 1, 1)
				cs.Thickness = 4
			end
			cnt.Size = UDim2.fromScale(0.9, 0.36)
			cnt.Position = UDim2.fromScale(0.05, 0.62)
			cnt.Parent = t.Parent
			padText[i] = t
			padCount[i] = cnt
			local glowC = HubConfig.colors.padGlow and HubConfig.colors.padGlow[i]
			local big = label(face, ("PAD %d"):format(i), 4.6, 4, 1.4, nil, "▶", glowC and color(glowC) or col)
			local bb = (big.Parent :: Instance).Parent :: BillboardGui
			bb.Size = UDim2.new(4, 26, 1.4, 9) -- (a little extra so it stays readable from the spawn)
			bb.MaxDistance = 90
		elseif models then
			-- jelly pad with a glow ring, and a sign standing just behind it, both facing the spawn
			local glow = HubConfig.colors.padGlow and HubConfig.colors.padGlow[i]
			local o = CFrame.lookAt(at(x, 0, z), at(x, 0, HubConfig.spawn[3]))
			mesh("Pad", "Pad_Body", o)
			mesh("Pad", "Pad_Tint", o, { tint = col })
			mesh("Pad", "Pad_Glow", o, { mat = NEON, color = glow and color(glow) or col, shadow = false })
			blocker("PadFloor", Vector3.new(13.5, 0.45, 10.5), at(x, 0.225, z)) -- walkable top at 0.45
			pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, 0.45, z), col, { transparency = 1, solid = false, shadow = false })
			local so = CFrame.lookAt(at(x, 0, z - 5.9), at(x, 0, HubConfig.spawn[3]))
			mesh("PadSign", "PadSign_Body", so)
			mesh("PadSign", "PadSign_Tint", so, { tint = col })
			blocker("PadSignPost", Vector3.new(8.2, 6.6, 0.8), so * CFrame.new(0, 3.3, 0))
			local face = part("PadSignFace", Vector3.new(8, 3, 0.05), so * CFrame.new(0, 5, -0.2), C.white, { transparency = 1, solid = false, shadow = false })
			padText[i] = sign(face, Enum.NormalId.Front, ("PAD %d\n0/%d"):format(i, HubConfig.maxPlayers), Color3.new(1, 1, 1), Color3.fromRGB(20, 40, 110), 40)
		else
			part("PadBase", Vector3.new(w + 0.8, 0.4, d + 0.8), at(x, 0.2, z), C.padBase)
			part("PadEdge", Vector3.new(w + 0.8, 0.5, 0.4), at(x, 0.25, z - d / 2 - 0.6), col)
			pad = part("Pad" .. i, Vector3.new(w, 0.3, d), at(x, 0.45, z), col, { mat = NEON, transparency = 0.3, solid = false, shadow = false })
			padText[i] = label(pad, ("PAD %d\n0/%d"):format(i, HubConfig.maxPlayers), 5, 9, 3.4)
		end
		pad:SetAttribute("Index", i)
		pad:SetAttribute("Members", 0)
		padParts[i] = pad
	end
end

local function buildLeft()
	-- how-to-play board, turned towards the middle
	local bpos = at(-46, 6.5, -20)
	local face = CFrame.lookAt(bpos, at(0, 6.5, 4))
	local board: BasePart
	if has("Board") then -- puffy red frame on candy-cane legs, the text on an invisible part on its cream face
		local o = CFrame.lookAt(at(-46, 0, -20), at(0, 0, 4))
		mesh("Board", "Board_Body", o, MD.board and { color = color(MD.board) } or nil)
		blocker("BoardBox", Vector3.new(14, 10, 1.6), o * CFrame.new(0, 6.5, 0.4))
		blocker("BoardLeg", Vector3.new(1, 5, 1), o * CFrame.new(-6, 2.5, 0.3))
		blocker("BoardLeg", Vector3.new(1, 5, 1), o * CFrame.new(6, 2.5, 0.3))
		-- (a plain-colour board gets a visible face so the text sits on white)
		local faceCol = MD.boardFace and color(MD.boardFace) or C.white
		board = part("Board", Vector3.new(13, 9, 0.05), o * CFrame.new(0, 6.5, -0.28), faceCol, { transparency = MD.boardFace and 0 or 1, solid = false, shadow = false })
		local badge = part("Alert", Vector3.new(2, 2, 0.05), o * CFrame.new(6.6, 12.1, -0.87), C.white, { transparency = 1, solid = false, shadow = false })
		sign(badge, Enum.NormalId.Front, "!", Color3.new(1, 1, 1), CLEAN and Color3.fromRGB(20, 70, 150) or Color3.fromRGB(120, 10, 30), 40)
	else
		part("BoardFrame", Vector3.new(14, 10, 0.6), face * CFrame.new(0, 0, 0.35), C.blue)
		board = part("Board", Vector3.new(13, 9, 0.6), face, C.white)
		for _, dx in { -6, 6 } do
			part("BoardLeg", Vector3.new(1, 6.5, 1), face * CFrame.new(dx, -5.5, 0.3), C.white)
		end
		local alert = part("Alert", Vector3.new(0.6, 3, 3), face * CFrame.new(-6.5, 5.5, 0) * FACE_Z, Color3.fromRGB(230, 50, 60), { shape = CYL })
		label(alert, "!", 0, 2, 2)
	end
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
	label(rb, "RAINBOW BUBBLE", 6, 10, 2, Color3.fromRGB(255, 225, 80), "🌈", Color3.fromRGB(190, 140, 245))
end

local function buildBooths()
	for i, s in HubConfig.booths do
		local accent = color(HubConfig.colors.booths[i])
		local pos = at(s[1], 0, s[2])
		local face = CFrame.lookAt(pos, pos - Vector3.xAxis) -- open side faces the middle
		local glowCol = HubConfig.colors.boothGlow and HubConfig.colors.boothGlow[i]
		if has("CleanBooth") and has("CleanBoothPad") then
			-- white booth with a pastel plinth, sill and pillow canopy, a sign plate on the canopy, a pad in front
			mesh("CleanBooth", "CleanBooth_Body", face)
			mesh("CleanBooth", "CleanBooth_Tint", face, { tint = accent })
			mesh("CleanBooth", "CleanBooth_Glow", face, { mat = NEON, color = glowCol and color(glowCol) or accent, shadow = false })
			blocker("BoothBox", Vector3.new(12, 9.2, 10), face * CFrame.new(0, 4.6, -0.5))
			local plate = part("BoothSign", Vector3.new(6.6, 1, 0.05), face * CFrame.new(0, 8.2, -5.66), C.white, { transparency = 1, solid = false, shadow = false })
			local name = HubConfig.boothNames and HubConfig.boothNames[i] or "COMING SOON"
			sign(plate, Enum.NormalId.Front, name, color(HubConfig.colors.blue), Color3.new(1, 1, 1), 40)
			local icon = HubConfig.boothIcons and HubConfig.boothIcons[i]
			local anchor = part("BoothLabel", Vector3.new(0.2, 0.2, 0.2), face * CFrame.new(0, 12.5, 0), C.white, { transparency = 1, solid = false, shadow = false })
			label(anchor, name, 0, 9, 2.6, nil, icon, glowCol and color(glowCol) or accent)
			local po = face * CFrame.new(0, 0, -9.75)
			mesh("CleanBoothPad", "CleanBoothPad_Body", po, { shadow = false })
			mesh("CleanBoothPad", "CleanBoothPad_Glow", po, { mat = NEON, color = glowCol and color(glowCol) or accent, shadow = false })
			blocker("BoothPadFloor", Vector3.new(0.35, 9, 9), CFrame.new(po.Position + Vector3.new(0, 0.175, 0)) * UP, CYL)
			continue
		end
		if has("Booth") and has("BoothPad") then
			-- candy booth (tinted walls and awning) with its topper on the roof and a glowing pad in front
			mesh("Booth", "Booth_Body", face)
			mesh("Booth", "Booth_Tint", face, { tint = accent })
			blocker("BoothBox", Vector3.new(12.4, 8, 11.4), face * CFrame.new(0, 4, 0.3))
			local topper = MD.toppers and MD.toppers[i]
			local top: BasePart
			if topper and has(topper) then
				local set = Models.hub[topper]
				local meshName = next(set.meshes) :: string
				top = mesh(topper, meshName, face * CFrame.new(0, 11, 0), { scale = MD.topperScale or 1 })
			else
				top = part("RoofBall", Vector3.new(2.6, 2.6, 2.6), (face * CFrame.new(0, 12.3, 0)).Position, C.gold, { shape = BALL })
			end
			label(top, HubConfig.boothNames and HubConfig.boothNames[i] or "COMING SOON", 4, 10, 2.2, Color3.new(1, 1, 1))
			local po = face * CFrame.new(0, 0, -9.75)
			mesh("BoothPad", "BoothPad_Body", po, { color = color(MD.boothPad), shadow = false })
			mesh("BoothPad", "BoothPad_Glow", po, { mat = NEON, color = glowCol and color(glowCol) or accent, shadow = false })
			blocker("BoothPadFloor", Vector3.new(0.35, 9, 9), CFrame.new(po.Position + Vector3.new(0, 0.175, 0)) * UP, CYL)
			continue
		end
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
		label(roofBall, HubConfig.boothNames and HubConfig.boothNames[i] or "COMING SOON", 3, 10, 2.2, Color3.new(1, 1, 1))
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
	local lock: BasePart
	if has("CleanGift") then -- cream gift box with a blue ribbon; the lid turns about the back top edge (pivot) to open later
		mesh("CleanGift", "CleanGift_Body", face)
		mesh("CleanGift", "CleanGift_Lid", face, { pivot = { 0, 3.2, 2.0 } })
		mesh("CleanGift", "CleanGift_Glow", face, { mat = NEON, color = color(MD.glow), transparency = MD.giftGlowTransparency, shadow = false })
		blocker("ChestBox", Vector3.new(6, 5.75, 4.4), face * CFrame.new(0, 2.875, 0))
		lock = part("ChestLock", Vector3.new(0.2, 0.2, 0.2), face * CFrame.new(0, 2.0, -2.1), gold, { transparency = 1, solid = false, shadow = false })
	elseif has("Chest") then -- fat red chest; the lid turns about its back top edge (pivot) to open later
		mesh("Chest", "Chest_Body", face)
		mesh("Chest", "Chest_Lid", face, { pivot = { 0, 3.5, 2.0 } })
		mesh("Chest", "Chest_Glow", face, { mat = NEON, color = color(MD.chestGlow), transparency = MD.chestGlowTransparency, shadow = false })
		blocker("ChestBox", Vector3.new(6.4, 6, 4.6), face * CFrame.new(0, 3, 0))
		lock = part("ChestLock", Vector3.new(0.2, 0.2, 0.2), face * CFrame.new(0, 2.02, -2.3), gold, { transparency = 1, solid = false, shadow = false })
	else
		vcyl("ChestGlow", pos + Vector3.new(0, 0.15, 0), 10, 0.3, Color3.fromRGB(200, 150, 20), { mat = NEON, transparency = 0.35, shadow = false })
		part("ChestBody", Vector3.new(6, 3.5, 4), face * CFrame.new(0, 2.05, 0), red)
		part("ChestLid", Vector3.new(6, 4, 4), face * CFrame.new(0, 3.8, 0), red, { shape = CYL })
		for _, dx in { -2, 2 } do
			part("ChestBand", Vector3.new(0.6, 3.6, 4.1), face * CFrame.new(dx, 2.05, 0), gold)
			part("ChestBandLid", Vector3.new(0.6, 4.1, 4.1), face * CFrame.new(dx, 3.8, 0), gold, { shape = CYL })
		end
		lock = part("ChestLock", Vector3.new(1.2, 1.4, 0.4), face * CFrame.new(0, 3.6, -2.1), gold)
	end
	local light = Instance.new("PointLight")
	light.Color = Color3.fromRGB(255, 210, 90)
	light.Range = 12
	light.Brightness = 1.5
	light.Parent = lock
	local sp = Instance.new("Sparkles")
	sp.SparkleColor = Color3.fromRGB(255, 220, 80)
	sp.Parent = lock
	local t = label(lock, "FREE GIFT!", 4.5, 9, 2.2, Color3.new(1, 1, 1), "🎁", Color3.fromRGB(255, 150, 120))
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 120, 120)),
		ColorSequenceKeypoint.new(0.35, Color3.fromRGB(255, 230, 90)),
		ColorSequenceKeypoint.new(0.7, Color3.fromRGB(120, 230, 140)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(120, 190, 255)),
	})
	g.Parent = t
end


-- a giant gumball machine where the HQ stands: red base, coin slot and knob, a glass globe full of gumballs
-- the BUBBLE POP banner across the machine's neck: the model, or the part-built one
local function buildBanner(machine: CFrame)
	if has("Banner") then
		local bo = machine * CFrame.new(0, 12.9, -10.56)
		mesh("Banner", "Banner_Body", bo, { color = color(MD.bannerRed) })
		mesh("Banner", "Banner_Trim", bo, { color = color(MD.bannerTrim) })
		mesh("Banner", "Banner_Bolts", bo, { color = color(MD.bannerBolts) })
		local face = part("Logo", Vector3.new(37.5, 7, 0.1), bo * CFrame.new(0, 4.6, -3.99), C.white, { transparency = 1, solid = false, shadow = false })
		sign(face, Enum.NormalId.Front, "BUBBLE POP", Color3.new(1, 1, 1), Color3.fromRGB(120, 10, 30), 11)
		return
	end
	local red = C.blue
	local z = machine.Position.Z - O.Z
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

-- the gumball model: body, knob and flap (with their pivots), glass globe, shine, a neat pile of
-- low-detail gumballs round a dark core. Invisible stage, base and globe for walking and bumping.
local function buildMachineModel(z: number)
	local o = CFrame.lookAt(at(0, 0, z), at(0, 0, HubConfig.spawn[3])) -- front towards the spawn
	mesh("Machine", "Machine_Body", o)
	mesh("Machine", "Machine_Knob", o, { pivot = { 0, 7.9, -9.0 } })
	mesh("Machine", "Machine_Flap", o, { pivot = { 0, 4.55, -9.35 } })
	mesh("Machine", "Machine_Glass", o, glassOpts())
	mesh("Machine", "Machine_Shine", o, shineOpts())
	blocker("MachineStage", Vector3.new(1.5, 28, 28), CFrame.new(at(0, 0.75, z)) * UP, CYL)
	blocker("MachineBase", Vector3.new(18, 14, 16), at(0, 8, z))
	blocker("Globe", Vector3.new(28, 28, 28), at(0, 29, z), BALL)
	local gc = o * CFrame.new(0, 29, 0)
	for _, b in Piles.globe.balls do
		lowGumball("Gumball", (gc * CFrame.new(b[1], b[2], b[3])).Position, Piles.globe.diameter, color(GUM[b[4]] or GUM[1]))
	end
	if has("GumballLo") then
		mesh("GumballLo", "GumballCore_Globe", gc, { color = color(MD.gumCore), shadow = false })
	end
	buildBanner(o)
end

local function buildGumballMachine()
	local z = -45
	if has("Machine") then
		buildMachineModel(z)
		return
	end
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
	buildBanner(CFrame.lookAt(at(0, 0, z), at(0, 0, HubConfig.spawn[3])))
end

-- Clean Pop Plaza centrepiece where the gumball machine stands: a stage and tulip pedestal holding a
-- giant glass bubble with pastel bubbles and an orbit ring inside (core and ring have pivots at the
-- bubble centre so the client can spin them later), and the BUBBLE POP banner across the cup.
-- Part fallback: the aero HQ.
local function buildCleanCentre()
	if not has("CleanCentre") then
		buildHQ()
		return
	end
	local z = -45
	local o = CFrame.lookAt(at(0, 0, z), at(0, 0, HubConfig.spawn[3])) -- front towards the spawn
	mesh("CleanCentre", "CleanCentre_Body", o)
	local coreTint = MD.coreTint and color(MD.coreTint) or nil
	mesh("CleanCentre", "CleanCentre_Core", o, { pivot = { 0, 31.5, 0 }, tint = coreTint })
	mesh("CleanCentre", "CleanCentre_Ring", o, { pivot = { 0, 31.5, 0 }, tint = coreTint })
	local glass = mesh("CleanCentre", "CleanCentre_Glass", o, { mat = GLASS, color = color(MD.glass), transparency = MD.glassTransparency, shadow = false })
	if MD.glassRim then -- a soft white outline so the big bubble reads against the sky
		local rim = Instance.new("Highlight")
		rim.FillTransparency = 1
		rim.OutlineColor = color(MD.glassRim)
		rim.OutlineTransparency = MD.glassRimTransparency or 0.4
		rim.DepthMode = Enum.HighlightDepthMode.Occluded
		rim.Parent = glass
	end
	mesh("CleanCentre", "CleanCentre_Shine", o, { color = color(MD.shine), transparency = MD.shineTransparency, shadow = false })
	mesh("CleanCentre", "CleanCentre_Glow", o, { mat = NEON, color = color(MD.glow), shadow = false })
	blocker("CentreStage", Vector3.new(1.5, 28, 28), CFrame.new(at(0, 0.75, z)) * UP, CYL)
	blocker("CentrePedestal", Vector3.new(21, 12, 12), CFrame.new(at(0, 11.5, z)) * UP, CYL)
	blocker("CentreBubble", Vector3.new(25, 25, 25), at(0, 31.5, z), BALL)
	if not has("CleanBanner") then
		buildBanner(o) -- the part-built banner
		return
	end
	-- the banner: its origin 12.9 up and 10.6 in front of the centrepiece's, flat colours
	local bo = o * CFrame.new(0, 12.9, -10.6)
	mesh("CleanBanner", "CleanBanner_Body", bo, { color = color(MD.bannerBlue) })
	mesh("CleanBanner", "CleanBanner_Trim", bo, { color = color(MD.bannerTrim) })
	mesh("CleanBanner", "CleanBanner_Bubbles", bo, { color = color(MD.bannerBubbles), gloss = MD.bannerBubblesGloss })
	mesh("CleanBanner", "CleanBanner_Glow", bo, { mat = NEON, color = color(MD.glow), shadow = false })
	local face = part("Logo", Vector3.new(37.5, 7, 0.1), bo * CFrame.new(0, 4.6, -0.76), C.white, { transparency = 1, solid = false, shadow = false })
	sign(face, Enum.NormalId.Front, "BUBBLE POP", Color3.new(1, 1, 1), Color3.fromRGB(15, 60, 150), 11)
end

-- a gumball pit where the fountain was: big bouncy gumballs to kick around while you wait
local function buildGumballPit()
	local c = at(-38, 0, 16)
	local rng = Random.new(3)
	if has("Pit") then
		-- inflatable candy-striped ring; its entrance (the model's front) points at the plaza middle (+X).
		-- Invisible walls round the ring with a 5-stud gap at the entrance, and a 0.3 floor slab.
		mesh("Pit", "Pit_Body", CFrame.lookAt(c, c + Vector3.xAxis))
		blocker("PitFloor", Vector3.new(0.3, 19.6, 19.6), CFrame.new(c + Vector3.new(0, 0.15, 0)) * UP, CYL)
		local r, w = 10.6, 4
		local a0 = math.asin((2.5 + w / 2) / r) -- first wall clears half the gap
		local n = 14
		for k = 0, n - 1 do
			local a = a0 + k / (n - 1) * (math.pi * 2 - 2 * a0)
			local pos = c + Vector3.new(math.cos(a) * r, 1.5, math.sin(a) * r)
			blocker("PitWall", Vector3.new(w, 3, 1.6), CFrame.lookAt(pos, c + Vector3.new(0, 1.5, 0)))
		end
	else
		vcyl("PitFloor", c + Vector3.new(0, 0.15, 0), 20, 0.3, C.lightBlue, { shadow = false })
		for k = 0, 15 do
			local a = k / 16 * math.pi * 2
			local pos = c + Vector3.new(math.cos(a) * 10.5, 1.5, math.sin(a) * 10.5)
			part("PitWall", Vector3.new(4.4, 3, 1), CFrame.lookAt(pos, c + Vector3.new(0, 1.5, 0)), k % 2 == 0 and C.white or C.blue)
		end
	end
	for k = 1, 7 do
		local a = k / 7 * math.pi * 2
		local g = gumball("BouncyGumball", c + Vector3.new(math.cos(a) * 5, 3, math.sin(a) * 5), 4, gumColor(rng), true)
		g.Anchored = false
		g.CustomPhysicalProperties = PhysicalProperties.new(0.3, 0.3, 0.8, 1, 1) -- light and bouncy
	end
	local sign0 = part("PitSign", Vector3.new(1, 1, 1), c + Vector3.new(0, 1, -10.5), C.white, { transparency = 1, solid = false })
	label(sign0, "GUMBALL PIT", 6, 10, 2.2, color(HubConfig.colors.pink), "🍬")
end

-- a big gumball jar where the rainbow bubble display was
local function buildCandyJar()
	local d = at(-26, 0, -6)
	local rng = Random.new(9)
	if has("Jar") then
		-- bulging glass jar on a gold and white base; the shine faces the plaza; a neat pile inside
		local o = CFrame.lookAt(d, at(0, 0, 0))
		mesh("Jar", "Jar_Body", o)
		local glass = mesh("Jar", "Jar_Glass", o, glassOpts())
		mesh("Jar", "Jar_Shine", o, shineOpts())
		blocker("JarBox", Vector3.new(12.6, 8, 8), CFrame.new(d + Vector3.new(0, 6.3, 0)) * UP, CYL)
		local floor = o * CFrame.new(0, 3.2, 0)
		for _, b in Piles.jar.balls do
			lowGumball("JarGumball", (floor * CFrame.new(b[1], b[2], b[3])).Position, Piles.jar.diameter, color(GUM[b[4]] or GUM[1]))
		end
		if has("GumballLo") then
			mesh("GumballLo", "GumballCore_Jar", floor, { color = color(MD.gumCore), shadow = false })
		end
		label(glass, "GUMBALL JAR", 7, 10, 2, color(HubConfig.colors.pink))
		return
	end
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
	local trees: { Vector2 } = {}
	while placed < 26 do
		local x, z = rng:NextNumber(-maxR, maxR), rng:NextNumber(-maxR, maxR)
		if math.max(math.abs(x), math.abs(z)) > 64 and math.sqrt(x * x + z * z) < maxR and not HubPolish.blocksTree(x, z) then
			placed += 1
			local s = rng:NextNumber(0.8, 1.4)
			local base = at(x, -3, z)
			if has("CleanTree") then -- ball, stack and cloud bubble trees in turn, pastel tints, each turned at random
				local shape = MD.trees[placed % #MD.trees + 1]
				local o = CFrame.new(base) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
				mesh("CleanTree", "CleanTree_" .. shape .. "_Tint", o, { scale = s, tint = gumColor(rng) })
				mesh("CleanTree", "CleanTree_" .. shape .. "_Body", o, { scale = s })
				mesh("CleanTree", "CleanTree_" .. shape .. "_Shine", o, { scale = s, color = color(MD.shine), transparency = MD.shineTransparency, shadow = false })
				blocker("TreeStem", Vector3.new(7 * s, 1.6 * s, 1.6 * s), CFrame.new(base + Vector3.new(0, 3.5 * s, 0)) * UP, CYL)
				table.insert(trees, Vector2.new(x, z))
				continue
			end
			if has("Lollipop") then -- swirl, ball and heart lollipops in turn, tinted, each turned at random
				local shape = MD.lollipops[placed % #MD.lollipops + 1]
				local o = CFrame.new(base) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
				mesh("Lollipop", "Lollipop_" .. shape .. "_Tint", o, { scale = s, tint = gumColor(rng) })
				mesh("Lollipop", "Lollipop_" .. shape .. "_Body", o, { scale = s })
				mesh("Lollipop", "Lollipop_" .. shape .. "_Shine", o, { scale = s, color = color(MD.shine), transparency = MD.shineTransparency, shadow = false })
				blocker("LollyStick", Vector3.new(9 * s, 1 * s, 1 * s), CFrame.new(base + Vector3.new(0, 4.5 * s, 0)) * UP, CYL)
				table.insert(trees, Vector2.new(x, z))
				continue
			end
			if HubConfig.theme ~= "aero" then -- (clean fallback: pastel lollipops)
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
	-- grass dressing: gumdrops, wrapped sweets and cupcakes on the grass ring outside the fence
	local dr = MD.dressing
	if dr and has("Dressing") then
		local drng = Random.new(11)
		local made, tries = 0, 0
		while made < dr.count and tries < 2000 do
			tries += 1
			local x, z = drng:NextNumber(-dr.maxRadius, dr.maxRadius), drng:NextNumber(-dr.maxRadius, dr.maxRadius)
			local clear = math.max(math.abs(x), math.abs(z)) > dr.minEdge and math.sqrt(x * x + z * z) < dr.maxRadius
			for _, t in trees do
				if clear and (t - Vector2.new(x, z)).Magnitude < 7 then
					clear = false
				end
			end
			if clear then
				local kind = dr.kinds[made % #dr.kinds + 1]
				local sc = drng:NextNumber(dr.size[1], dr.size[2])
				local o = CFrame.new(at(x, -3, z)) * CFrame.Angles(0, drng:NextNumber(0, math.pi * 2), 0)
				mesh("Dressing", "Dressing_" .. kind .. "_Tint", o, { scale = sc, tint = gumColor(drng) })
				if kind == "Cupcake" then
					mesh("Dressing", "Dressing_Cupcake_Body", o, { scale = sc })
				end
				table.insert(trees, Vector2.new(x, z))
				made += 1
			end
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
	elseif CLEAN then
		buildCleanCentre()
		buildFountain()
		buildDisplay()
	else
		buildHQ()
		buildFountain()
		buildDisplay()
	end
	buildPads()
	buildLeft()
	buildBooths()
	buildChest()
	if CLEAN then -- paths, rings, rug, planters, lamps, benches, back colonnade, islands, rainbow
		HubPolish.build({ part = part, ball = ball, vcyl = vcyl, at = at, has = has, mesh = mesh, folder = folder, blocker = blocker })
	end
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
		local text = padText[i]
		part:SetAttribute("Members", #pad.members)
		part:SetAttribute("Owner", LobbyRules.owner(pad) or 0)
		part:SetAttribute("Countdown", pad.countdown and math.ceil(pad.countdown) or 0)
		if text then
			local line2 = ("%d/%d"):format(#pad.members, HubConfig.maxPlayers)
			if #pad.members > 0 then
				line2 ..= hooks.canStart() and ("  •  " .. math.max(0, math.ceil(pad.countdown or 0))) or "  •  room busy"
			end
			if padCount[i] then
				padCount[i].Text = line2
			else
				text.Text = ("PAD %d\n%s"):format(i, line2)
			end
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
