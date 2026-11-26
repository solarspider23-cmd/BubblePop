-- BubblePop test room (prototype): builds the room, keeps track of which bubbles are popped,
-- and checks every pop a client asks for. Clients draw the bubbles and play the animations.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Room = require(Shared.Config.Room)
local Pop = require(Shared.Config.Pop)
local RoomLayout = require(Shared.Rules.RoomLayout)
local PopRules = require(Shared.Rules.PopRules)
local Variants = require(Shared.Config.Variants)
local VariantRules = require(Shared.Rules.Variants)
local BagConfig = require(Shared.Config.Bag)
local BagRules = require(Shared.Rules.Bag)
local Upgrades = require(Shared.Config.Upgrades)
local UpgradeRules = require(Shared.Rules.Upgrades)
local HubConfig = require(Shared.Config.Hub)
local Hub = require(script.Parent:WaitForChild("Hub"))

Players.CharacterAutoLoads = false -- spawn players only after the room exists

local layout = RoomLayout.new(Room)
local bubbles = layout.bubbles
local COUNT = #bubbles

local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end

---------------------------------------------------------------- world
local world = Instance.new("Folder")
world.Name = "Room"

local function block(name, size, cf, col, material)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cf
	p.Color = col
	p.Material = material or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = world
	return p
end

local half, height, y0 = layout.half, layout.height, layout.floorY
local wallT = 2
block("Floor", Vector3.new(half * 2 + wallT * 2, 2, half * 2 + wallT * 2), CFrame.new(0, y0 - 1, 0), color(Room.colors.floor))
block("Ceiling", Vector3.new(half * 2 + wallT * 2, 1, half * 2 + wallT * 2), CFrame.new(0, y0 + height + 0.5, 0), color(Room.colors.ceiling))
block("WallN", Vector3.new(half * 2 + wallT * 2, height, wallT), CFrame.new(0, y0 + height / 2, -half - wallT / 2), color(Room.colors.wall))
block("WallS", Vector3.new(half * 2 + wallT * 2, height, wallT), CFrame.new(0, y0 + height / 2, half + wallT / 2), color(Room.colors.wall))
block("WallW", Vector3.new(wallT, height, half * 2), CFrame.new(-half - wallT / 2, y0 + height / 2, 0), color(Room.colors.wall))
block("WallE", Vector3.new(wallT, height, half * 2), CFrame.new(half + wallT / 2, y0 + height / 2, 0), color(Room.colors.wall))
-- coloured strip along the bottom of each wall (below the wall wrap); its colour comes from the look
do
	local t, h = 0.03, Room.wallLift - 0.05
	local trimColor = color(Room.colors.trim or Room.colors.wall)
	local ty = y0 + h / 2
	block("TrimN", Vector3.new(half * 2, h, t), CFrame.new(0, ty, -half + t / 2), trimColor).CanCollide = false
	block("TrimS", Vector3.new(half * 2, h, t), CFrame.new(0, ty, half - t / 2), trimColor).CanCollide = false
	block("TrimW", Vector3.new(t, h, half * 2), CFrame.new(-half + t / 2, ty, 0), trimColor).CanCollide = false
	block("TrimE", Vector3.new(t, h, half * 2), CFrame.new(half - t / 2, ty, 0), trimColor).CanCollide = false
end

-- Recycler: a sell pad in the middle of the room (stand on it to sell) with the machine on it.
-- "Recycler" is the machine's box: solid, and where sold scraps fly to. A real model
-- (Config/Models.recycler) replaces the look when it's uploaded; the box then goes invisible.
do
	local rc = Room.recycler
	local size = Vector3.new(rc.size[1], rc.size[2], rc.size[3])
	local padSize = rc.pad or (rc.size[1] + 4)
	local pad = block("SellPad", Vector3.new(padSize, 0.2, padSize), CFrame.new(0, y0 + 0.1, 0), Color3.fromRGB(70, 78, 92), Enum.Material.DiamondPlate)
	pad.CanCollide = true
	-- hazard-yellow border so the pad reads as "stand here"
	local t, h = 0.45, 0.24
	for _, e in {
		{ Vector3.new(padSize, h, t), Vector3.new(0, 0, padSize / 2 - t / 2) },
		{ Vector3.new(padSize, h, t), Vector3.new(0, 0, -padSize / 2 + t / 2) },
		{ Vector3.new(t, h, padSize - 2 * t), Vector3.new(padSize / 2 - t / 2, 0, 0) },
		{ Vector3.new(t, h, padSize - 2 * t), Vector3.new(-padSize / 2 + t / 2, 0, 0) },
	} do
		local edge = block("SellPadEdge", e[1], CFrame.new(e[2] + Vector3.new(0, y0 + h / 2, 0)), Color3.fromRGB(255, 200, 40))
		edge.CanCollide = false
	end
	if rc.style == "chute" then
		-- a round glowing drain in the pad: scraps get sucked down into it
		local top = y0 + 0.2
		local function disc(name: string, d: number, h: number, y: number, col: Color3, mat: Enum.Material?): BasePart
			local part = block(name, Vector3.new(h, d, d), CFrame.new(0, y, 0) * CFrame.Angles(0, 0, math.pi / 2), col, mat)
			part.Shape = Enum.PartType.Cylinder
			part.CanCollide = false
			return part
		end
		disc("ChuteRing", 7.2, 0.3, top + 0.05, Color3.fromRGB(255, 200, 40))
		disc("ChuteHole", 6.2, 0.3, top + 0.02, Color3.fromRGB(15, 20, 30))
		local glow = disc("ChuteGlow", 5.4, 0.06, top + 0.2, Color3.fromRGB(40, 170, 90), Enum.Material.Neon)
		glow.Transparency = 0.25
		local light = Instance.new("PointLight")
		light.Color = Color3.fromRGB(90, 255, 140)
		light.Range = 10
		light.Brightness = 1.5
		light.Parent = glow
		-- grate bars across the hole
		for i = -2, 2 do
			local len = math.sqrt(math.max(0, 3.1 ^ 2 - (i * 1.1) ^ 2)) * 2
			local bar = block("ChuteBar", Vector3.new(len, 0.12, 0.22), CFrame.new(0, top + 0.3, i * 1.1), Color3.fromRGB(60, 66, 78), Enum.Material.Metal)
			bar.CanCollide = false
		end
		-- green sparkles drifting up out of the drain
		local at = Instance.new("Attachment")
		at.Parent = glow
		local fx = Instance.new("ParticleEmitter")
		fx.Texture = "rbxasset://textures/particles/sparkles_main.dds"
		fx.Rate = 8
		fx.Lifetime = NumberRange.new(0.8, 1.4)
		fx.Speed = NumberRange.new(1.5, 3)
		fx.SpreadAngle = Vector2.new(25, 25)
		fx.EmissionDirection = Enum.NormalId.Right -- the cylinder's axis points up
		fx.LightEmission = 1
		fx.Color = ColorSequence.new(Color3.fromRGB(150, 255, 180))
		fx.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 0) })
		fx.Parent = at
		-- "SELL" floating over it
		local sign = Instance.new("BillboardGui")
		sign.Size = UDim2.fromScale(5, 1.6)
		sign.StudsOffsetWorldSpace = Vector3.new(0, 3.5, 0)
		sign.AlwaysOnTop = true
		sign.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
		t.TextScaled = true
		t.Text = "SELL"
		t.TextColor3 = Color3.fromRGB(140, 255, 170)
		local st = Instance.new("UIStroke")
		st.Thickness = 3
		st.Color = Color3.fromRGB(10, 60, 30)
		st.Parent = t
		t.Parent = sign
		sign.Parent = glow
		-- invisible target the sold scraps fly into (just under the grate)
		local target = block("Recycler", Vector3.new(3, 0.4, 3), CFrame.new(0, top - 0.1, 0), Color3.new(0, 0, 0))
		target.Transparency = 1
		target.CanCollide = false
		target.CanQuery = false
	else
	local r = block("Recycler", size, CFrame.new(0, y0 + 0.2 + size.Y / 2, 0), color(rc.color))
	for _, face in { Enum.NormalId.Front, Enum.NormalId.Back, Enum.NormalId.Left, Enum.NormalId.Right } do
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Label"
		gui.Face = face
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 40
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(0.9, 0.3)
		label.Position = UDim2.fromScale(0.05, 0.35)
		label.BackgroundTransparency = 1
		label.Font = Enum.Font.FredokaOne
		label.TextScaled = true
		label.TextColor3 = Color3.new(1, 1, 1)
		label.Text = "RECYCLER"
		local stroke = Instance.new("UIStroke")
		stroke.Thickness = 4
		stroke.Color = Color3.fromRGB(20, 80, 35)
		stroke.Parent = label
		label.Parent = gui
		gui.Parent = r
	end
	end
end

-- One ceiling light in the middle of the room
do
	local lit = Room.lighting
	local panel = block("Light", Vector3.new(lit.lampSize, 0.2, lit.lampSize), CFrame.new(0, y0 + height - 0.1, 0), Color3.fromRGB(255, 250, 235), Enum.Material.Neon)
	panel.CanCollide = false
	local l = Instance.new("PointLight")
	l.Range = lit.lampRange
	l.Brightness = lit.lampBrightness
	l.Shadows = false
	l.Parent = panel
end

---------------------------------------------------------------- uploaded models
-- Load each Blender model once and keep its MeshPart in ReplicatedStorage.BubbleAssets for
-- clients to copy. Anything that fails to load is simply missing: placeholders are used instead.
local InsertService = game:GetService("InsertService")
local Models = require(Shared.Config.Models)

local assets = Instance.new("Folder")
assets.Name = "BubbleAssets"

local function loadMesh(name: string, def, textureId: number?): MeshPart?
	if not Models.enabled or not def or (def.model or 0) == 0 then
		return nil
	end
	local ok, model = pcall(function()
		return InsertService:LoadAsset(def.model)
	end)
	if not ok or not model then
		warn("BubblePop: model " .. name .. " didn't load: " .. tostring(model))
		return nil
	end
	local mesh = model:FindFirstChildWhichIsA("MeshPart", true)
	if not mesh then
		model:Destroy()
		return nil
	end
	mesh = mesh:Clone()
	model:Destroy()
	mesh.Name = name
	mesh.Anchored = true
	mesh.CanCollide = false
	mesh.CanTouch = false
	mesh.CastShadow = false
	mesh.Material = Enum.Material.SmoothPlastic
	if textureId and textureId ~= 0 then
		mesh.TextureID = "rbxassetid://" .. textureId
	end
	mesh.Parent = assets
	return mesh
end

local zone = Models.zone
loadMesh("Intact", Models.intact, Models.intact and Models.intact.texture[zone])
for i, def in Models.popped or {} do
	loadMesh("Popped" .. i, def, def.texture[zone])
end
local sheetMesh = loadMesh("Sheet", Models.sheet, nil)
do -- the lobby gumball: mesh + its glossy candy look (SurfaceAppearance saved in art/GumballLook.rbxmx)
	local gum = loadMesh("Gumball", Models.gumball, nil)
	local look = game:GetService("ServerStorage"):FindFirstChild("GumballLook")
	if gum and look then
		look:Clone().Parent = gum
	end
end
assets.Parent = ReplicatedStorage

-- Bubble wrap sheets (the bubbles themselves are drawn by each client)
local sheetFolder = Instance.new("Folder")
sheetFolder.Name = "Sheets"
sheetFolder.Parent = world
for _, s in layout.sheets do
	local n = Vector3.new(s.nx, s.ny, s.nz)
	local r = Vector3.new(s.rx, s.ry, s.rz)
	local p: BasePart
	if sheetMesh then
		-- the mesh's origin sits under the bubble plane by its top offset
		local k = Room.bubbleScale or 1
		local base = Vector3.new(s.x, s.y, s.z) + n * (s.thickness / 2 - Models.sheet.topOffset * k)
		local c = Models.sheet.center
		p = sheetMesh:Clone()
		p.Size = sheetMesh.Size * k
		p.CFrame = CFrame.fromMatrix(base, r, n) * CFrame.new(c[1] * k, c[2] * k, c[3] * k)
	else
		p = Instance.new("Part")
		p.Size = Vector3.new(s.size - 0.02, s.thickness, s.size - 0.02) -- tiny gap: no flicker at seams
		p.CFrame = CFrame.fromMatrix(Vector3.new(s.x, s.y, s.z), r, n)
		p.Material = Enum.Material.SmoothPlastic
	end
	p.Name = "Sheet"
	p.Anchored = true
	p.CanCollide = false -- the floor slab and walls behind already hold players in
	p.CastShadow = false
	p.Color = color(Room.colors.sheet)
	p.Parent = sheetFolder
end

world.Parent = workspace
Hub.build()

local lit = Room.lighting
Lighting.Ambient = color(lit.ambient)
Lighting.OutdoorAmbient = color(lit.ambient)
Lighting.Brightness = lit.brightness
Lighting.ExposureCompensation = lit.exposure
Lighting.ClockTime = 14
local cc = Instance.new("ColorCorrectionEffect")
cc.Contrast = lit.contrast
cc.Saturation = lit.saturation
cc.Parent = Lighting

---------------------------------------------------------------- remotes
local remotes = Instance.new("Folder")
remotes.Name = "Remotes"
local PopRequest = Instance.new("RemoteEvent")
PopRequest.Name = "PopRequest" -- client -> server: (bubbleId, {extra ids from a bigger tool}) after a full press
PopRequest.Parent = remotes
local StompRequest = Instance.new("RemoteEvent")
StompRequest.Name = "StompRequest" -- client -> server: ({bubbleId, ...}) floor bubbles walked over
StompRequest.Parent = remotes
local BubbleChanged = Instance.new("RemoteEvent")
BubbleChanged.Name = "BubbleChanged" -- server -> clients: {id (popped) or -id (grew back)}, poppedBy userId, variant per entry
BubbleChanged.Parent = remotes
local Sold = Instance.new("RemoteEvent")
Sold.Name = "Sold" -- server -> client: (coins, scraps) you just sold at the recycler
Sold.Parent = remotes
local BuyUpgrade = Instance.new("RemoteFunction")
BuyUpgrade.Name = "BuyUpgrade" -- client -> server: (kind) -> ok, message
BuyUpgrade.Parent = remotes
local TestCoins = Instance.new("RemoteEvent")
TestCoins.Name = "TestCoins" -- client -> server: give me coins (only works in Studio, for testing)
TestCoins.Parent = remotes
local TestClear = Instance.new("RemoteEvent")
TestClear.Name = "TestClear" -- client -> server: pop all but 10 bubbles (only works in Studio, for testing)
TestClear.Parent = remotes
local GetPopped = Instance.new("RemoteFunction")
GetPopped.Name = "GetPopped" -- client -> server: { popped = {ids}, variantIds = {ids}, variantKinds = {variant} }
GetPopped.Parent = remotes
remotes.Parent = ReplicatedStorage

---------------------------------------------------------------- state
local poppedAt: { [number]: number } = {} -- id -> os.clock() when popped
local pending: { number } = {} -- changes to send
local pendingBy: { number } = {}
local pendingKind: { number } = {}

-- Which bubbles are rare (Config/Variants). Missing = normal. Rolled at start and every regrow.
local variantOf: { [number]: number } = {}
local rng = Random.new()
local function rollVariant(id: number)
	local k = VariantRules.roll(Variants, rng:NextNumber())
	variantOf[id] = if k > 0 then k else nil
end
-- roll every bubble's variant for a new run; some variants have a cap per room
local function rollRoom()
	for id = 1, COUNT do
		rollVariant(id)
	end
	local seen: { [number]: number } = {}
	for id = 1, COUNT do
		local k = variantOf[id]
		local cap = k and Variants.list[k].maxPerRoom
		if cap then
			seen[k] = (seen[k] or 0) + 1
			if seen[k] > cap then
				variantOf[id] = nil
			end
		end
	end
end
rollRoom()

-- who is in the popping room right now (player attribute InRun); everyone else is in the hub
local function inRun(player: Player): boolean
	return player:GetAttribute("InRun") == true
end

local function queue(change, userId)
	table.insert(pending, change)
	table.insert(pendingBy, userId)
	table.insert(pendingKind, variantOf[math.abs(change)] or 0)
end

local lastClick: { [Player]: number } = {}
local stompLimit: { [Player]: (number) -> boolean } = {}
local clickLimit: { [Player]: (number) -> boolean } = {}

-- Bags: popped bubbles go in here; they turn into coins when sold at the recycler.
-- The client sees its bag through player attributes BagCount / BagValue / BagCapacity.
local bags: { [Player]: BagRules.Bag } = {}

local function showBag(player: Player)
	local bag = bags[player]
	if bag then
		player:SetAttribute("BagCount", bag.count)
		player:SetAttribute("BagValue", bag.value)
	end
end

-- Upgrades: levels per player (player attributes Upg_<kind>), applied as per-player settings
local popSettings: { [Player]: any } = {}

local function level(player: Player, kind: string): number
	return player:GetAttribute("Upg_" .. kind) or 1
end

local function applyUpgrades(player: Player)
	local pt = UpgradeRules.value(Upgrades, "popSpeed", level(player, "popSpeed"))
	local boots = UpgradeRules.value(Upgrades, "boots", level(player, "boots"))
	local tool = UpgradeRules.value(Upgrades, "tool", level(player, "tool"))
	popSettings[player] = setmetatable({ popTime = pt, stompRadius = boots, tool = tool }, { __index = Pop })
	player:SetAttribute("ToolPops", tool) -- bubbles per press
	player:SetAttribute("BagCapacity", UpgradeRules.value(Upgrades, "bag", level(player, "bag")))
	player:SetAttribute("PopTime", pt) -- the client presses this long
	player:SetAttribute("StompRadius", boots) -- 0 = walking doesn't pop
end

local function coinsValue(player: Player): IntValue?
	local stats = player:FindFirstChild("leaderstats")
	return stats and stats:FindFirstChild("Coins") :: IntValue?
end

BuyUpgrade.OnServerInvoke = function(player, kind)
	if not UpgradeRules.valid(Upgrades, kind) then
		return false, "unknown upgrade"
	end
	local c = coinsValue(player)
	if not c then
		return false, "not ready"
	end
	local ok, newLevel, left = UpgradeRules.buy(Upgrades, kind, level(player, kind), c.Value)
	if not ok then
		return false, UpgradeRules.maxed(Upgrades, kind, level(player, kind)) and "maxed" or "not enough coins"
	end
	c.Value = left
	player:SetAttribute("Upg_" .. kind, newLevel)
	applyUpgrades(player)
	return true, "bought"
end

TestCoins.OnServerEvent:Connect(function(player)
	if not RunService:IsStudio() then
		return -- testing only
	end
	local c = coinsValue(player)
	if c then
		c.Value += 1000
	end
end)

local function capacity(player: Player): number
	return player:GetAttribute("BagCapacity") or BagConfig.startCapacity
end

local function bagFull(player: Player): boolean
	local bag = bags[player]
	return not bag or BagRules.full(bag, capacity(player))
end

-- Put the popped bubble in the bag (rare bubbles are worth more) and count the pop
local function addPop(player: Player, id: number)
	local bag = bags[player]
	if not bag or not BagRules.add(bag, VariantRules.coins(Variants, variantOf[id]), capacity(player)) then
		return
	end
	showBag(player)
	local stats = player:FindFirstChild("leaderstats")
	local v = stats and stats:FindFirstChild("Pops")
	if v then
		v.Value += 1
	end
end

local function root(player: Player): BasePart?
	local c = player.Character
	local r = c and c:FindFirstChild("HumanoidRootPart")
	return r and r:IsA("BasePart") and r or nil
end

-- A refused pop the client already showed: tell just that client to put it back
local function refuse(player: Player, id: number)
	if not poppedAt[id] then
		BubbleChanged:FireClient(player, { -id }, { 0 }, { variantOf[id] or 0 })
	end
end

PopRequest.OnServerEvent:Connect(function(player, id, extras)
	if not inRun(player) then
		return
	end
	local now = os.clock()
	local allow = clickLimit[player]
	if not allow or not allow(now) then
		return
	end
	if not PopRules.validId(id, COUNT) then
		return
	end
	if poppedAt[id] then
		return -- someone already popped it; their change is on its way
	end
	if bagFull(player) then
		return refuse(player, id) -- full bag: sell first
	end
	local r = root(player)
	if not r then
		return refuse(player, id)
	end
	local b = bubbles[id]
	local distance = (r.Position - Vector3.new(b.x, b.y, b.z)).Magnitude
	local ok = PopRules.clickOk(distance, now - (lastClick[player] or -math.huge), popSettings[player] or Pop)
	if not ok then
		return refuse(player, id)
	end
	lastClick[player] = now
	poppedAt[id] = now
	queue(id, player.UserId)
	addPop(player, id)

	-- a bigger tool pops neighbours too (checked: count, same surface, close, still there, bag room)
	if type(extras) ~= "table" then
		return
	end
	local maxExtra = ((popSettings[player] or Pop).tool or 1) - 1
	local spread = Upgrades.tool.spread
	for i = 1, math.min(#extras, maxExtra) do
		local eid = extras[i]
		if PopRules.validId(eid, COUNT) and not poppedAt[eid] then
			if bagFull(player) or not PopRules.extraOk(b, bubbles[eid], Room.spacing, spread) then
				refuse(player, eid)
			else
				poppedAt[eid] = now
				queue(eid, player.UserId)
				addPop(player, eid)
			end
		end
	end
	for i = maxExtra + 1, math.min(#extras, 30) do
		local eid = extras[i]
		if PopRules.validId(eid, COUNT) then
			refuse(player, eid) -- more than the tool allows
		end
	end
end)

StompRequest.OnServerEvent:Connect(function(player, ids)
	if type(ids) ~= "table" or #ids > 30 or not inRun(player) then
		return
	end
	local r = root(player)
	if not r then
		return
	end
	local allow = stompLimit[player]
	local now = os.clock()
	for i = 1, #ids do
		local id = ids[i]
		if not allow or not allow(now) then
			return
		end
		if PopRules.validId(id, COUNT) and not poppedAt[id] then
			if bagFull(player) then
				refuse(player, id)
				continue
			end
			local b = bubbles[id]
			if b.surface == "floor" then
				local dx, dz = r.Position.X - b.x, r.Position.Z - b.z
				local ps = popSettings[player] or Pop
				if ps.stompRadius > 0 and PopRules.stompOk(math.sqrt(dx * dx + dz * dz), r.Position.Y - y0, ps) then
					poppedAt[id] = now
					queue(id, player.UserId)
					addPop(player, id)
				else
					refuse(player, id)
				end
			end
		end
	end
end)

GetPopped.OnServerInvoke = function()
	local list, vIds, vKinds = {}, {}, {}
	for id in poppedAt do
		table.insert(list, id)
	end
	for id, k in variantOf do
		table.insert(vIds, id)
		table.insert(vKinds, k)
	end
	return { popped = list, variantIds = vIds, variantKinds = vKinds }
end

-- Send changes in small batches; grow bubbles back
local sinceFlush, sinceRegrow, sinceSell = 0, 0, 0
local updateRun: (number) -> ()
local rc = Room.recycler
local function sellNearby()
	for player, bag in bags do
		local r = root(player)
		if bag.count > 0 and r and inRun(player)
			and BagRules.nearRecycler(r.Position.X, r.Position.Z, 0, 0, rc.pad or rc.size[1], rc.pad or rc.size[3], BagConfig.sellReach) then
			local n = bag.count
			local coins = BagRules.sell(bag)
			local stats = player:FindFirstChild("leaderstats")
			local c = stats and stats:FindFirstChild("Coins")
			if c then
				c.Value += coins
			end
			showBag(player)
			Sold:FireClient(player, coins, n)
		end
	end
end
-- The run: a timer from when the first player arrives until every bubble is popped.
-- Clients read ReplicatedStorage attributes RunStart (server time), BubblesLeft and
-- RunClearTime (seconds it took; set once the room is cleared).
ReplicatedStorage:SetAttribute("BubblesLeft", COUNT)
ReplicatedStorage:SetAttribute("RoomTotal", COUNT)
local runId = 0

-- Back to the hub (third person)
local function sendToHub(player: Player)
	player:SetAttribute("InRun", nil)
	player.CameraMode = Enum.CameraMode.Classic
	local char = player.Character
	if char then
		char:PivotTo(Hub.spawnCFrame)
	end
end

local function endRun()
	for _, p in Players:GetPlayers() do
		if inRun(p) then
			sendToHub(p)
		end
	end
end

updateRun = function(left: number)
	if ReplicatedStorage:GetAttribute("BubblesLeft") ~= left then
		ReplicatedStorage:SetAttribute("BubblesLeft", left)
	end
	local start = ReplicatedStorage:GetAttribute("RunStart")
	if left == 0 and start and not ReplicatedStorage:GetAttribute("RunClearTime") then
		ReplicatedStorage:SetAttribute("RunClearTime", workspace:GetServerTimeNow() - start)
		local mine = runId
		task.delay(HubConfig.backToHubSeconds, function()
			if runId == mine then
				endRun()
			end
		end)
	end
end

-- Every run starts fresh: coins, pops, bag and upgrades back to the start
local function resetRunState(player: Player)
	local stats = player:FindFirstChild("leaderstats")
	for _, n in { "Coins", "Pops" } do
		local v = stats and stats:FindFirstChild(n)
		if v then
			(v :: IntValue).Value = 0
		end
	end
	for _, kind in Upgrades.order do
		player:SetAttribute("Upg_" .. kind, nil)
	end
	bags[player] = BagRules.new()
	lastClick[player] = nil
	applyUpgrades(player)
	showBag(player)
end

-- A group from a hub pad goes into a fresh room
local function startRun(group: { Player }, _roomIndex: number)
	runId += 1
	-- reset the room: every bubble back, rare ones rolled again
	table.clear(poppedAt)
	rollRoom()
	for id = 1, COUNT do
		queue(-id, 0)
	end
	ReplicatedStorage:SetAttribute("RunClearTime", nil)
	ReplicatedStorage:SetAttribute("BubblesLeft", COUNT)
	ReplicatedStorage:SetAttribute("RunStart", workspace:GetServerTimeNow())
	local s = Room.spawn
	for i, p in group do
		resetRunState(p)
		p:SetAttribute("InRun", true)
		p.CameraMode = Enum.CameraMode.LockFirstPerson
		local char = p.Character
		if char then
			char:PivotTo(CFrame.new(s[1] + (i - 2.5) * 2, s[2], s[3]))
		end
	end
end

Hub.start({
	canStart = function()
		for _, p in Players:GetPlayers() do
			if inRun(p) then
				return false -- one room for now: wait until it's free
			end
		end
		return true
	end,
	startRun = startRun,
	inRun = inRun,
})

TestClear.OnServerEvent:Connect(function()
	if not RunService:IsStudio() then
		return -- testing only
	end
	local keep = 10
	local now = os.clock()
	for id = 1, COUNT do
		if not poppedAt[id] then
			if keep > 0 then
				keep -= 1
			else
				poppedAt[id] = now
				queue(id, 0)
			end
		end
	end
end)

RunService.Heartbeat:Connect(function(dt)
	sinceFlush += dt
	sinceRegrow += dt
	sinceSell += dt
	if sinceSell >= 0.2 then
		sinceSell = 0
		sellNearby()
	end
	if sinceRegrow >= 0.5 then
		sinceRegrow = 0
		local now = os.clock()
		local popped = 0
		for id, t in poppedAt do
			if Pop.regrow and now - t >= Pop.regrowSeconds then
				poppedAt[id] = nil
				rollVariant(id) -- it may grow back as a different (rare) bubble
				queue(-id, 0)
			else
				popped += 1
			end
		end
		updateRun(COUNT - popped)
	end
	if sinceFlush >= 0.05 and #pending > 0 then
		sinceFlush = 0
		BubbleChanged:FireAllClients(pending, pendingBy, pendingKind)
		pending, pendingBy, pendingKind = {}, {}, {}
	end
end)

---------------------------------------------------------------- players
local function onPlayer(player: Player)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"
	local pops = Instance.new("IntValue")
	pops.Name = "Pops"
	pops.Parent = stats
	local coins = Instance.new("IntValue")
	coins.Name = "Coins"
	coins.Parent = stats
	stats.Parent = player
	bags[player] = BagRules.new()
	applyUpgrades(player)
	showBag(player)
	clickLimit[player] = PopRules.rateLimiter(10)
	stompLimit[player] = PopRules.rateLimiter(Pop.stompMaxPerSecond)
	player.CameraMode = Enum.CameraMode.Classic -- the hub is third person
	player.CharacterAdded:Connect(function(char)
		local s = Room.spawn
		task.defer(function()
			if inRun(player) then
				char:PivotTo(CFrame.new(s[1], s[2], s[3]))
			else
				char:PivotTo(Hub.spawnCFrame)
			end
		end)
		local hum = char:WaitForChild("Humanoid") :: Humanoid
		hum.Died:Connect(function()
			task.wait(2)
			if player.Parent then
				player:LoadCharacter()
			end
		end)
	end)
	player:LoadCharacter()
end

Players.PlayerAdded:Connect(onPlayer)
for _, p in Players:GetPlayers() do
	task.spawn(onPlayer, p)
end
Players.PlayerRemoving:Connect(function(p)
	lastClick[p] = nil
	stompLimit[p] = nil
	clickLimit[p] = nil
	bags[p] = nil
	popSettings[p] = nil
end)
