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

-- Ceiling lights: a grid of glowing panels with lights under them
local lightStep = 12
for x = -half + lightStep / 2, half - lightStep / 2, lightStep do
	for z = -half + lightStep / 2, half - lightStep / 2, lightStep do
		local panel = block("Light", Vector3.new(4, 0.2, 4), CFrame.new(x, y0 + height - 0.1, z), Color3.fromRGB(255, 250, 235), Enum.Material.Neon)
		panel.CanCollide = false
		local l = Instance.new("PointLight")
		l.Range = 22
		l.Brightness = 0.9
		l.Shadows = false
		l.Parent = panel
	end
end

-- Bubble wrap sheets (the bubbles themselves are drawn by each client)
local sheetFolder = Instance.new("Folder")
sheetFolder.Name = "Sheets"
sheetFolder.Parent = world
for _, s in layout.sheets do
	local p = Instance.new("Part")
	p.Name = "Sheet"
	p.Anchored = true
	p.CanCollide = s.surface ~= "floor" -- the floor slab already holds players up
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = color(Room.colors.sheet)
	p.Size = Vector3.new(s.size - 0.02, s.thickness, s.size - 0.02) -- tiny gap: no flicker at seams
	local n = Vector3.new(s.nx, s.ny, s.nz)
	local r = Vector3.new(s.rx, s.ry, s.rz)
	p.CFrame = CFrame.fromMatrix(Vector3.new(s.x, s.y, s.z), r, n)
	p.Parent = sheetFolder
end

world.Parent = workspace

Lighting.Ambient = Color3.fromRGB(120, 130, 150)
Lighting.OutdoorAmbient = Color3.fromRGB(140, 150, 170)
Lighting.Brightness = 1
Lighting.ClockTime = 14

---------------------------------------------------------------- remotes
local remotes = Instance.new("Folder")
remotes.Name = "Remotes"
local PopRequest = Instance.new("RemoteEvent")
PopRequest.Name = "PopRequest" -- client -> server: (bubbleId) after a full press
PopRequest.Parent = remotes
local StompRequest = Instance.new("RemoteEvent")
StompRequest.Name = "StompRequest" -- client -> server: ({bubbleId, ...}) floor bubbles walked over
StompRequest.Parent = remotes
local BubbleChanged = Instance.new("RemoteEvent")
BubbleChanged.Name = "BubbleChanged" -- server -> clients: {id (popped) or -id (grew back)}, poppedBy userId per entry
BubbleChanged.Parent = remotes
local GetPopped = Instance.new("RemoteFunction")
GetPopped.Name = "GetPopped" -- client -> server: list of popped ids right now
GetPopped.Parent = remotes
remotes.Parent = ReplicatedStorage

---------------------------------------------------------------- state
local poppedAt: { [number]: number } = {} -- id -> os.clock() when popped
local pending: { number } = {} -- changes to send
local pendingBy: { number } = {}

local function queue(change, userId)
	table.insert(pending, change)
	table.insert(pendingBy, userId)
end

local lastClick: { [Player]: number } = {}
local stompLimit: { [Player]: (number) -> boolean } = {}
local clickLimit: { [Player]: (number) -> boolean } = {}

local function addPop(player: Player)
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
		BubbleChanged:FireClient(player, { -id }, { 0 })
	end
end

PopRequest.OnServerEvent:Connect(function(player, id)
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
	local r = root(player)
	if not r then
		return refuse(player, id)
	end
	local b = bubbles[id]
	local distance = (r.Position - Vector3.new(b.x, b.y, b.z)).Magnitude
	local ok = PopRules.clickOk(distance, now - (lastClick[player] or -math.huge), Pop)
	if not ok then
		return refuse(player, id)
	end
	lastClick[player] = now
	poppedAt[id] = now
	queue(id, player.UserId)
	addPop(player)
end)

StompRequest.OnServerEvent:Connect(function(player, ids)
	if type(ids) ~= "table" or #ids > 30 then
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
			local b = bubbles[id]
			if b.surface == "floor" then
				local dx, dz = r.Position.X - b.x, r.Position.Z - b.z
				if PopRules.stompOk(math.sqrt(dx * dx + dz * dz), r.Position.Y - y0, Pop) then
					poppedAt[id] = now
					queue(id, player.UserId)
					addPop(player)
				else
					refuse(player, id)
				end
			end
		end
	end
end)

GetPopped.OnServerInvoke = function()
	local list = {}
	for id in poppedAt do
		table.insert(list, id)
	end
	return list
end

-- Send changes in small batches; grow bubbles back
local sinceFlush, sinceRegrow = 0, 0
RunService.Heartbeat:Connect(function(dt)
	sinceFlush += dt
	sinceRegrow += dt
	if sinceRegrow >= 0.5 then
		sinceRegrow = 0
		local now = os.clock()
		for id, t in poppedAt do
			if now - t >= Pop.regrowSeconds then
				poppedAt[id] = nil
				queue(-id, 0)
			end
		end
	end
	if sinceFlush >= 0.05 and #pending > 0 then
		sinceFlush = 0
		BubbleChanged:FireAllClients(pending, pendingBy)
		pending, pendingBy = {}, {}
	end
end)

---------------------------------------------------------------- players
local function onPlayer(player: Player)
	local stats = Instance.new("Folder")
	stats.Name = "leaderstats"
	local pops = Instance.new("IntValue")
	pops.Name = "Pops"
	pops.Parent = stats
	stats.Parent = player
	clickLimit[player] = PopRules.rateLimiter(10)
	stompLimit[player] = PopRules.rateLimiter(Pop.stompMaxPerSecond)
	player.CameraMode = Enum.CameraMode.LockFirstPerson
	player.CharacterAdded:Connect(function(char)
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
end)
