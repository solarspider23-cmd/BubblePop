-- Clean theme polish for the lobby hub: ground detail (paths with kerb lines, rings round the
-- stations, a round rug round the centrepiece), props (planters with bushes, lamp posts, benches),
-- a colonnade along the back, floating islands and a soft rainbow.
-- Everything is placed from Config/Hub.lua `polish`. One function per prop type (planter, lamp,
-- bench, colonnade, island). The modelled planter, lamp, bench, hall (instead of the colonnade) and
-- leaderboard (art/hub_clean_props) are used when they loaded; the part versions otherwise.
-- Ground layers: floor top = 0; each layer sits at least 0.02 above the one below (no z-fighting).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HubConfig = require(ReplicatedStorage:WaitForChild("Shared").Config.Hub)

local Polish = {}

local P = HubConfig.polish
local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end

-- h = helpers from Hub.lua: part, ball, vcyl, at, has, mesh, folder, shine
function Polish.build(h)
	if not P then
		return
	end
	local part, ball, vcyl, at = h.part, h.ball, h.vcyl, h.at
	local CYL = Enum.PartType.Cylinder
	local UP = CFrame.Angles(0, 0, math.pi / 2)
	local NEON, GLASS = Enum.Material.Neon, Enum.Material.Glass
	local WHITE = Color3.fromRGB(250, 251, 253)
	local flat = { shadow = false, solid = false, gloss = 0.02 }
	local function opts(extra)
		local o = table.clone(flat)
		for k, v in extra or {} do
			o[k] = v
		end
		return o
	end
	local ground = Instance.new("Folder")
	ground.Name = "Ground"
	ground.Parent = h.folder
	local props = Instance.new("Folder")
	props.Name = "Props"
	props.Parent = h.folder

	------------------------------------------------------------ ground
	-- a flat slab whose top is at height `top`
	local function slab(name, x1, z1, x2, z2, top, col)
		local th = 0.1
		return part(name, Vector3.new(x2 - x1, th, z2 - z1), at((x1 + x2) / 2, top - th / 2, (z1 + z2) / 2), col, opts({ parent = ground, mat = Enum.Material.Plastic, studs = true }))
	end
	-- studded pastel inlays a little above the studded floor. Paths: all kerb lines first (0.08), then all path tops (0.13). Overlapping pieces of one layer
	-- share colour and height, so the joins are seamless.
	local trimW = 0.6
	for _, r in P.paths do
		slab("PathTrim", r[1] - trimW, r[2] - trimW, r[3] + trimW, r[4] + trimW, 0.08, color(P.pathTrim))
	end
	for _, r in P.paths do
		slab("Path", r[1], r[2], r[3], r[4], 0.13, color(P.path))
	end
	-- an annulus of thin straight segments (cylinders can't have holes); `keep(pos)` filters segments
	local function ring(name, cx, cz, r1, r2, top, col, keep)
		local rm = (r1 + r2) / 2
		local n = math.max(16, math.floor(2 * math.pi * rm / 1.6))
		local len = 2 * r2 * math.sin(math.pi / n) + 0.05
		for k = 0, n - 1 do
			local a = k / n * math.pi * 2
			local pos = at(cx + math.cos(a) * rm, top - 0.05, cz + math.sin(a) * rm)
			if not keep or keep(pos) then
				local cf = CFrame.new(pos) * CFrame.Angles(0, -a, 0)
				part(name, Vector3.new(r2 - r1, 0.1, len), cf, col, opts({ parent = ground, mat = Enum.Material.Plastic, studs = true }))
			end
		end
	end
	for i, r in P.rings do
		ring("StationRing", r[1], r[2], r[3], r[4], 0.18, color(P.ringColors[i] or P.pathTrim))
	end
	-- the rug round the stage: bands outward, only in front of the back fence (the slab ends at z -56)
	local rug = P.rug
	local edge = h.at(0, 0, -HubConfig.size / 2 + 1.5).Z
	for k, b in rug.bands do
		ring("Rug", rug.centre[1], rug.centre[2], b[1], b[2], 0.2 + (k % 2) * 0.03, color(b[3]), function(pos)
			return pos.Z > edge
		end)
	end

	------------------------------------------------------------ props
	local function turnAt(x, z, deg, y)
		return CFrame.new(at(x, y or 0, z)) * CFrame.Angles(0, math.rad(deg or 0), 0)
	end
	local bushRng = Random.new(21)
	local function bushColor()
		return color(P.bushColors[bushRng:NextInteger(1, #P.bushColors)])
	end

	-- planter: white box with a sky rim, soil, three round pastel bushes (6 x 2.4 footprint)
	local function planter(cf: CFrame)
		local m = Instance.new("Model")
		m.Name = "Planter"
		m.Parent = props
		if h.has("CleanPlanter") then -- the modelled planter (6 x 4, bushes up to 5.6), one solid box
			h.mesh("CleanPlanter", "CleanPlanter_Body", cf, { parent = m })
			h.mesh("CleanPlanter", "CleanPlanter_Tint", cf, { tint = bushColor(), parent = m })
			h.mesh("CleanPlanter", "CleanPlanter_Shine", cf, { color = Color3.new(1, 1, 1), transparency = 0.15, shadow = false, parent = m })
			part("PlanterBox", Vector3.new(6, 2.45, 3.9), cf * CFrame.new(0, 1.225, 0), WHITE, { parent = m, transparency = 1, shadow = false })
			return
		end
		part("PlanterBox", Vector3.new(6, 2, 2.4), cf * CFrame.new(0, 1, 0), WHITE, { parent = m })
		part("PlanterRim", Vector3.new(6.4, 0.35, 2.8), cf * CFrame.new(0, 2.15, 0), color(P.pathTrim), { parent = m })
		part("PlanterSoil", Vector3.new(5.6, 0.2, 2), cf * CFrame.new(0, 2.3, 0), Color3.fromRGB(150, 120, 110), { parent = m, solid = false, shadow = false })
		for k, dx in { -1.9, 0, 1.9 } do
			local d = k == 2 and 2.9 or 2.4
			ball("Bush", (cf * CFrame.new(dx, 2.3 + d * 0.38, 0)).Position, d, bushColor(), { parent = m, solid = false, gloss = 0.08 })
		end
	end
	-- lamp post: white base and pole, a dark-ish neon globe inside a glass bubble, soft light
	local function lamp(cf: CFrame)
		local m = Instance.new("Model")
		m.Name = "Lamp"
		m.Parent = props
		local p = cf.Position
		if h.has("CleanLamp") then -- the modelled lamp post (9.4 tall) with a neon bubble globe and a soft light
			h.mesh("CleanLamp", "CleanLamp_Body", cf, { parent = m })
			local globe = h.mesh("CleanLamp", "CleanLamp_Glow", cf, { mat = NEON, color = color(P.lampGlow), shadow = false, parent = m })
			local light = Instance.new("PointLight")
			light.Color = Color3.fromRGB(170, 215, 255)
			light.Range = 16
			light.Brightness = 0.8
			light.Shadows = false
			light.Parent = globe
			vcyl("LampPost", p + Vector3.new(0, 3.5, 0), 1.2, 7, WHITE, { parent = m, transparency = 1, shadow = false })
			return
		end
		vcyl("LampBase", p + Vector3.new(0, 0.35, 0), 1.8, 0.7, WHITE, { parent = m })
		vcyl("LampBand", p + Vector3.new(0, 0.8, 0), 1.2, 0.3, color(P.pathTrim), { parent = m, shadow = false })
		vcyl("LampPole", p + Vector3.new(0, 4.6, 0), 0.55, 8, WHITE, { parent = m })
		vcyl("LampCup", p + Vector3.new(0, 8.7, 0), 1.4, 0.4, color(P.pathTrim), { parent = m })
		local glow = ball("LampGlow", p + Vector3.new(0, 10.1, 0), 1.6, color(P.lampGlow), { parent = m, mat = NEON, solid = false, shadow = false })
		ball("LampGlass", p + Vector3.new(0, 10.1, 0), 2.6, color(P.lampGlass), { parent = m, mat = GLASS, transparency = 0.55, solid = false, shadow = false })
		ball("LampShine", p + Vector3.new(-0.5, 10.7, 0.55), 0.6, Color3.new(1, 1, 1), { parent = m, solid = false, shadow = false, transparency = 0.2 })
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(170, 215, 255)
		light.Range = 14
		light.Brightness = 0.8
		light.Shadows = false
		light.Parent = glow
	end
	-- bench: rounded-ish white seat and back on two sky legs (6 wide); seat faces the cf's -z
	local benchRng = Random.new(8)
	local function bench(cf: CFrame)
		local m = Instance.new("Model")
		m.Name = "Bench"
		m.Parent = props
		if h.has("CleanBench") then -- the modelled bench (5.2 x 2.1, seat top 1.9), pastel cushion
			local cols = P.benchColors or P.bushColors
			h.mesh("CleanBench", "CleanBench_Body", cf, { parent = m })
			h.mesh("CleanBench", "CleanBench_Tint", cf, { tint = color(cols[benchRng:NextInteger(1, #cols)]), parent = m })
			part("BenchSeat", Vector3.new(5.2, 1.9, 2), cf * CFrame.new(0, 0.95, 0), WHITE, { parent = m, transparency = 1, shadow = false })
			return
		end
		for _, dx in { -2.3, 2.3 } do
			part("BenchLeg", Vector3.new(0.6, 1.5, 1.8), cf * CFrame.new(dx, 0.75, 0), color(P.pathTrim), { parent = m })
		end
		part("BenchSeat", Vector3.new(6, 0.45, 2.1), cf * CFrame.new(0, 1.72, 0), WHITE, { parent = m })
		part("BenchBack", Vector3.new(6, 1.5, 0.4), cf * CFrame.new(0, 2.9, 0.95) * CFrame.Angles(math.rad(-10), 0, 0), WHITE, { parent = m })
		part("BenchBackBand", Vector3.new(6.05, 0.3, 0.42), cf * CFrame.new(0, 3.3, 1.02) * CFrame.Angles(math.rad(-10), 0, 0), color(P.pathTrim), { parent = m, shadow = false })
	end
	for _, s in P.planters do
		planter(turnAt(s[1], s[2], s[3]))
	end
	for _, s in P.lamps do
		lamp(turnAt(s[1], s[2], 0))
	end
	-- garden: a round raised flower bed (white rim, mint top) with bushes and a small bubble tree
	local function garden(x: number, z: number, r: number)
		local m = Instance.new("Model")
		m.Name = "Garden"
		m.Parent = props
		local c = at(x, 0, z)
		vcyl("GardenRim", c + Vector3.new(0, 0.6, 0), r * 2 + 1, 1.2, WHITE, { parent = m })
		vcyl("GardenBand", c + Vector3.new(0, 0.9, 0), r * 2 + 1.1, 0.3, color(P.pathTrim), { parent = m, shadow = false })
		vcyl("GardenTop", c + Vector3.new(0, 1.25, 0), r * 2, 0.1, color(P.gardenTop or P.islandGrass), { parent = m, solid = false, shadow = false, gloss = 0 })
		for k = 0, 5 do
			local a = k / 6 * math.pi * 2 + 0.4
			local d = 1.6 + bushRng:NextNumber(0, 0.8)
			ball("Bush", c + Vector3.new(math.cos(a) * (r - 1.4), 1.2 + d * 0.35, math.sin(a) * (r - 1.4)), d, bushColor(), { parent = m, solid = false, gloss = 0.08 })
		end
		if h.has("CleanTree") then
			local shape = ({ "Ball", "Stack", "Cloud" })[bushRng:NextInteger(1, 3)]
			local o = CFrame.new(c + Vector3.new(0, 1.2, 0)) * CFrame.Angles(0, bushRng:NextNumber(0, 6.28), 0)
			local s = r / 8
			h.mesh("CleanTree", "CleanTree_" .. shape .. "_Tint", o, { scale = s, tint = bushColor(), parent = m })
			h.mesh("CleanTree", "CleanTree_" .. shape .. "_Body", o, { scale = s, parent = m })
			h.mesh("CleanTree", "CleanTree_" .. shape .. "_Shine", o, { scale = s, color = Color3.new(1, 1, 1), transparency = 0.15, shadow = false, parent = m })
		else
			ball("GardenBush", c + Vector3.new(0, 3, 0), r * 0.7, bushColor(), { parent = m, solid = false })
		end
	end
	for _, g in P.gardens or {} do
		garden(g[1], g[2], g[3])
	end
	for _, s in P.benches do
		bench(turnAt(s[1], s[2], s[3]))
	end

	------------------------------------------------------------ colonnade along the back (on the grass, y -3)
	local function colonnade(c)
		local m = Instance.new("Model")
		m.Name = "Colonnade"
		m.Parent = props
		local g = -3 -- grass top
		local bayW = (c.x2 - c.x1) / c.bays
		local H = c.height
		local col, arch, beam, band = color(c.column), color(c.arch), color(c.beam), color(c.band)
		for k = 0, c.bays do
			local x = c.x1 + k * bayW
			local base = at(x, g, c.z)
			part("ColumnBase", Vector3.new(4, 1.6, 4), base + Vector3.new(0, 0.8, 0), col, { parent = m })
			vcyl("ColumnRing", base + Vector3.new(0, 1.9, 0), 3.6, 0.6, band, { parent = m })
			vcyl("Column", base + Vector3.new(0, 1.6 + (H - 3.2) / 2, 0), 3, H - 3.2, col, { parent = m })
			part("ColumnCap", Vector3.new(4.2, 1.2, 4.2), base + Vector3.new(0, H - 1, 0), col, { parent = m })
			ball("ColumnBubble", base + Vector3.new(0, H + 5.2, 0), 3.2, color(c.crest), { parent = m, solid = false, gloss = 0.2 })
		end
		-- arches: a semicircle of blocks in each bay, springing from the columns
		local r = bayW / 2 - 1.5
		local spring = H - 0.4 - r - 0.6
		for k = 0, c.bays - 1 do
			local cx = c.x1 + (k + 0.5) * bayW
			local n = 9
			for j = 0, n - 1 do
				local a = (j + 0.5) / n * math.pi
				local pos = at(cx + math.cos(a) * (r + 0.6), g + spring + math.sin(a) * (r + 0.6), c.z)
				local seg = 2 * (r + 1.2) * math.sin(math.pi / (2 * n)) + 0.2
				part("Arch", Vector3.new(seg, 1.2, 2.4), CFrame.new(pos) * CFrame.Angles(0, 0, a - math.pi / 2), arch, { parent = m })
			end
		end
		-- beam with a sky band and a scalloped bubble crest
		local w = c.x2 - c.x1 + 4.4
		local mid = (c.x1 + c.x2) / 2
		part("Beam", Vector3.new(w, 2.4, 4), at(mid, g + H + 1.2, c.z), color(c.beam), { parent = m })
		part("BeamBand", Vector3.new(w + 0.1, 0.6, 4.1), at(mid, g + H + 1.2, c.z), band, { parent = m, shadow = false })
		for k = 0, c.bays - 1 do
			local cx = c.x1 + (k + 0.5) * bayW
			part("Crest", Vector3.new(1, 5, 5), CFrame.new(at(cx, g + H + 2.4, c.z)) * CFrame.Angles(0, math.pi / 2, 0), beam, { parent = m, shape = CYL })
		end
		-- the middle bay behind the centrepiece gets a taller arch top
		part("CrestTop", Vector3.new(1.2, 10, 10), CFrame.new(at(mid, g + H + 5, c.z)) * CFrame.Angles(0, math.pi / 2, 0), band, { parent = m, shape = CYL })
		part("CrestTopIn", Vector3.new(1.4, 7.4, 7.4), CFrame.new(at(mid, g + H + 5, c.z)) * CFrame.Angles(0, math.pi / 2, 0), beam, { parent = m, shape = CYL })
	end
	-- the modelled back hall (domed towers, arches, medallion) replaces the colonnade when it loads
	local function hall(c)
		local m = Instance.new("Model")
		m.Name = "Hall"
		m.Parent = props
		local s = c.scale or 1
		local pos = at(c.x, 0, c.z)
		local cf = CFrame.lookAt(pos, pos + Vector3.new(0, 0, 1)) -- front faces the spawn
		h.mesh("CleanHall", "CleanHall_Body", cf, { scale = s, parent = m })
		h.mesh("CleanHall", "CleanHall_Glow", cf, { scale = s, mat = NEON, color = color(c.glow), shadow = false, parent = m })
		h.mesh("CleanHall", "CleanHall_Shine", cf, { scale = s, color = Color3.new(1, 1, 1), transparency = 0.2, shadow = false, parent = m })
		part("HallWall", Vector3.new(60 * s, 14 * s, 9 * s), cf * CFrame.new(0, 7 * s, 0), WHITE, { parent = m, transparency = 1, shadow = false })
	end
	if P.hall and h.has("CleanHall") then
		hall(P.hall)
	elseif P.colonnade then
		colonnade(P.colonnade)
	end

	-- the modelled leaderboard stand: "FASTEST CLEARS" header and a placeholder top 3 (SurfaceGui on thin invisible parts)
	local lb = P.leaderboard
	if lb and h.has("CleanLeaderboard") then
		local m = Instance.new("Model")
		m.Name = "Leaderboard"
		m.Parent = props
		local pos = at(lb.x, 0, lb.z)
		local centre = at(0, 0, 0)
		local cf = CFrame.lookAt(pos, Vector3.new(centre.X, pos.Y, centre.Z))
		h.mesh("CleanLeaderboard", "CleanLeaderboard_Body", cf, { parent = m })
		h.mesh("CleanLeaderboard", "CleanLeaderboard_Glow", cf, { mat = NEON, color = Color3.fromRGB(20, 100, 200), shadow = false, parent = m })
		part("BoardStand", Vector3.new(12, 8, 3), cf * CFrame.new(0, 4, -0.2), WHITE, { parent = m, transparency = 1, shadow = false })
		local function face(name, size, z, y)
			local p = part(name, Vector3.new(size.X, size.Y, 0.05), cf * CFrame.new(0, y, z), WHITE, { parent = m, transparency = 1, shadow = false, solid = false })
			local g = Instance.new("SurfaceGui")
			g.Face = Enum.NormalId.Front
			g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			g.PixelsPerStud = 50
			g.LightInfluence = 0
			g.Parent = p
			return g
		end
		local head = face("BoardTitle", Vector2.new(6, 1.1), -1.16 - 0.04, 8.25)
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Size = UDim2.fromScale(1, 1)
		t.Font = Enum.Font.FredokaOne
		t.TextScaled = true
		t.TextColor3 = Color3.new(1, 1, 1)
		t.Text = lb.title
		t.Parent = head
		local list = face("BoardList", Vector2.new(10, 5), -0.12 - 0.04, 4.6)
		local pad = Instance.new("UIPadding")
		pad.PaddingTop = UDim.new(0.08, 0)
		pad.PaddingBottom = UDim.new(0.08, 0)
		pad.PaddingLeft = UDim.new(0.08, 0)
		pad.PaddingRight = UDim.new(0.08, 0)
		pad.Parent = list
		local rowColors = { Color3.fromRGB(230, 170, 30), Color3.fromRGB(140, 150, 170), Color3.fromRGB(200, 120, 70) }
		for i, row in lb.rows do
			local r = Instance.new("TextLabel")
			r.BackgroundTransparency = 1
			r.Position = UDim2.fromScale(0, (i - 1) / #lb.rows)
			r.Size = UDim2.fromScale(1, 1 / #lb.rows)
			r.Font = Enum.Font.FredokaOne
			r.TextScaled = true
			r.TextXAlignment = Enum.TextXAlignment.Center
			r.TextColor3 = rowColors[i] or Color3.fromRGB(60, 80, 120)
			r.Text = row
			r.Parent = list
		end
	end

	------------------------------------------------------------ surroundings
	-- a small floating island: pastel grass top, soft stone underneath narrowing down, a bubble tree or two
	local isRng = Random.new(5)
	local function island(x, y, z, r)
		local m = Instance.new("Model")
		m.Name = "FloatIsland"
		m.Parent = props
		local top = at(x, y, z)
		vcyl("IslandGrass", top - Vector3.new(0, 1, 0), r * 2, 2, color(P.islandGrass), { parent = m, solid = false, gloss = 0 })
		vcyl("IslandRim", top - Vector3.new(0, 2.3, 0), r * 2 + 0.8, 0.8, WHITE, { parent = m, solid = false, shadow = false })
		for k, layer in { { 0.95, 0.35 }, { 0.75, 0.35 }, { 0.5, 0.35 }, { 0.25, 0.3 } } do
			local hgt = r * layer[2]
			local yy = -2.7 - (k - 1) * r * 0.32 - hgt / 2
			vcyl("IslandRock", top + Vector3.new(0, yy, 0), r * 2 * layer[1], hgt, color(P.islandRock), { parent = m, solid = false, shadow = false, gloss = 0 })
		end
		local trees = r > 20 and 2 or 1
		for t = 1, trees do
			local a = isRng:NextNumber(0, math.pi * 2)
			local d = (trees == 1) and 0 or r * 0.4
			local base = top + Vector3.new(math.cos(a) * d, 0, math.sin(a) * d)
			local s = r / 14
			local tint = color(P.bushColors[isRng:NextInteger(1, #P.bushColors)])
			if h.has("CleanTree") then
				local shape = ({ "Ball", "Stack", "Cloud" })[isRng:NextInteger(1, 3)]
				local o = CFrame.new(base) * CFrame.Angles(0, isRng:NextNumber(0, 6.28), 0)
				h.mesh("CleanTree", "CleanTree_" .. shape .. "_Tint", o, { scale = s, tint = tint, parent = m })
				h.mesh("CleanTree", "CleanTree_" .. shape .. "_Body", o, { scale = s, parent = m })
				h.mesh("CleanTree", "CleanTree_" .. shape .. "_Shine", o, { scale = s, color = Color3.new(1, 1, 1), transparency = 0.15, shadow = false, parent = m })
			else
				vcyl("Stem", base + Vector3.new(0, 4 * s, 0), 1.2 * s, 8 * s, WHITE, { parent = m, solid = false })
				ball("Crown", base + Vector3.new(0, 10 * s, 0), 8 * s, tint, { parent = m, solid = false })
			end
		end
		for _, a in { 0.7, 2.6, 4.4 } do -- a few bushes round the edge
			local d = r * 0.75
			ball("IslandBush", top + Vector3.new(math.cos(a) * d, 0.6, math.sin(a) * d), r * 0.18, color(P.bushColors[isRng:NextInteger(1, #P.bushColors)]), { parent = m, solid = false, shadow = false })
		end
	end
	for _, s in P.islands or {} do
		island(s[1], s[2], s[3], s[4])
	end
	-- a soft rainbow arch far behind the centrepiece: bands of thin segments
	local rb = P.rainbow
	if rb then
		local m = Instance.new("Model")
		m.Name = "Rainbow"
		m.Parent = props
		local c = at(rb.centre[1], rb.centre[2], rb.centre[3])
		local n = 48
		for b, rgbc in rb.colors do
			local r = rb.radius - (b - 1) * rb.width
			local seg = 2 * r * math.sin(math.pi / (2 * n)) + 1
			for j = 0, n - 1 do
				local a = (j + 0.5) / n * math.pi
				local pos = c + Vector3.new(math.cos(a) * r, math.sin(a) * r, 0)
				part("RainbowBand", Vector3.new(seg, rb.width, 1), CFrame.new(pos) * CFrame.Angles(0, 0, a - math.pi / 2), color(rgbc), {
					parent = m, solid = false, shadow = false, transparency = rb.transparency, gloss = 0,
				})
			end
		end
	end
end

-- is (x, z) (from the hub origin) where the colonnade stands? (Hub.lua keeps trees out of it)
function Polish.blocksTree(x: number, z: number): boolean
	local c = P and P.colonnade
	if not c or HubConfig.theme ~= "clean" then
		return false
	end
	return z < c.z + 8 and z > c.z - 10 and x > c.x1 - 10 and x < c.x2 + 10
end

return Polish
