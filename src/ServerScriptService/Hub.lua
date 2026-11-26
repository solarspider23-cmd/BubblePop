-- The lobby hub: builds the studded brick plaza with 4 pads, and runs the pads.
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

local folder = Instance.new("Folder")
folder.Name = "Hub"

-- a classic Roblox brick: studs on top
local function brick(name: string, size: Vector3, pos: Vector3, col: Color3, studs: boolean?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.Position = pos
	p.Color = col
	p.Material = Enum.Material.Plastic
	p.TopSurface = studs == false and Enum.SurfaceType.Smooth or Enum.SurfaceType.Studs
	p.BottomSurface = Enum.SurfaceType.Inlet
	p.Parent = folder
	return p
end

local function sign(parent: BasePart, face: Enum.NormalId, text: string, col: Color3?, stroke: Color3?)
	local gui = Instance.new("SurfaceGui")
	gui.Face = face
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 30
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(0.92, 0.8)
	t.Position = UDim2.fromScale(0.04, 0.1)
	t.BackgroundTransparency = 1
	t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	t.TextScaled = true
	t.Text = text
	t.TextColor3 = col or Color3.new(1, 1, 1)
	local st = Instance.new("UIStroke")
	st.Thickness = 4
	st.Color = stroke or Color3.fromRGB(20, 40, 110)
	st.Parent = t
	t.Parent = gui
	gui.Parent = parent
end

Hub.spawnCFrame = CFrame.lookAt(O + Vector3.new(HubConfig.spawn[1], HubConfig.spawn[2], HubConfig.spawn[3]), O + Vector3.new(0, HubConfig.spawn[2], -10))

local padParts: { BasePart } = {}

function Hub.build()
	local c = HubConfig.colors
	local S = HubConfig.size
	brick("Baseplate", Vector3.new(S, 2, S), O + Vector3.new(0, -1, 0), color(c.baseplate))
	-- low brick border, in rows of bright colours
	local wallCols = { Color3.fromRGB(13, 105, 172), Color3.fromRGB(196, 40, 28), Color3.fromRGB(245, 205, 48), Color3.fromRGB(75, 151, 75) }
	for i, side in { { 0, -S / 2, S, 2 }, { 0, S / 2, S, 2 }, { -S / 2, 0, 2, S }, { S / 2, 0, 2, S } } do
		for row = 0, 2 do
			brick("Wall", Vector3.new(side[3], 1.2, side[4]), O + Vector3.new(side[1], 0.6 + row * 1.2, side[2]), wallCols[(i + row) % #wallCols + 1])
		end
	end
	-- spawn brick
	local sp = brick("SpawnBrick", Vector3.new(8, 1, 8), Hub.spawnCFrame.Position - Vector3.new(0, HubConfig.spawn[2] - 0.5, 0), Color3.fromRGB(99, 95, 98))
	sign(sp, Enum.NormalId.Top, "SPAWN", Color3.new(1, 1, 1))

	-- the pads, with a big "PICK A PAD!" sign behind them
	local back = brick("PadSign", Vector3.new(76, 10, 1), O + Vector3.new(0, 7, -18), Color3.fromRGB(13, 105, 172))
	sign(back, Enum.NormalId.Back, "STEP ON A PAD TO PLAY!", Color3.fromRGB(255, 225, 80))
	for _, leg in { -36, 36 } do
		brick("SignLeg", Vector3.new(2, 12, 2), O + Vector3.new(leg, 6, -18), Color3.fromRGB(99, 95, 98))
	end
	for i, xz in HubConfig.pads do
		local pos = O + Vector3.new(xz[1], 0, xz[2])
		brick("PadBase", Vector3.new(HubConfig.padRadius * 2 + 2, 0.6, HubConfig.padRadius * 2 + 2), pos + Vector3.new(0, 0.3, 0), color(c.padBase))
		local pad = Instance.new("Part")
		pad.Name = "Pad" .. i
		pad.Anchored = true
		pad.CanCollide = false
		pad.Shape = Enum.PartType.Cylinder
		pad.Size = Vector3.new(0.3, HubConfig.padRadius * 2, HubConfig.padRadius * 2)
		pad.CFrame = CFrame.new(pos + Vector3.new(0, 0.7, 0)) * CFrame.Angles(0, 0, math.pi / 2)
		pad.Color = color(c.pad[i] or c.pad[1])
		pad.Material = Enum.Material.Neon
		pad.Transparency = 0.25
		pad:SetAttribute("Index", i)
		pad:SetAttribute("Members", 0)
		pad.Parent = folder
		local bb = Instance.new("BillboardGui")
		bb.Name = "Info"
		bb.Size = UDim2.fromScale(8, 3)
		bb.StudsOffsetWorldSpace = Vector3.new(0, 5, 0)
		bb.LightInfluence = 0
		local t = Instance.new("TextLabel")
		t.Name = "Text"
		t.Size = UDim2.fromScale(1, 1)
		t.BackgroundTransparency = 1
		t.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
		t.TextScaled = true
		t.TextColor3 = Color3.new(1, 1, 1)
		t.Text = ("PAD %d\n0/%d"):format(i, HubConfig.maxPlayers)
		local st = Instance.new("UIStroke")
		st.Thickness = 3
		st.Color = Color3.fromRGB(20, 40, 110)
		st.Parent = t
		t.Parent = bb
		bb.Parent = pad
		padParts[i] = pad
	end

	-- two booths (placeholders): game passes and the crystal shop
	for _, b in { { -30, 26, "PASSES", c.boothRoofPasses }, { 30, 26, "SHOP", c.boothRoofShop } } do
		local base = O + Vector3.new(b[1], 0, b[2])
		brick("Counter", Vector3.new(10, 3, 3), base + Vector3.new(0, 1.5, 0), color(c.booth))
		for _, dx in { -4.5, 4.5 } do
			brick("Post", Vector3.new(1, 8, 1), base + Vector3.new(dx, 4, -2), color(c.booth))
		end
		local roof = brick("Roof", Vector3.new(12, 1, 6), base + Vector3.new(0, 8.5, -1), color(b[4]))
		local board = brick("Board", Vector3.new(10, 2.5, 0.6), base + Vector3.new(0, 10.3, 1.2), color(b[4]), false)
		sign(board, Enum.NormalId.Back, b[3], Color3.new(1, 1, 1))
		local _ = roof
	end

	-- leaderboard wall (placeholder)
	local lb = brick("Leaderboard", Vector3.new(20, 12, 1), O + Vector3.new(0, 6, S / 2 - 4), Color3.fromRGB(17, 17, 17))
	sign(lb, Enum.NormalId.Front, "FASTEST CLEARS\n(coming soon)", Color3.fromRGB(255, 225, 80))

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
					local d = Vector3.new(r.Position.X - centre.X, 0, r.Position.Z - centre.Z).Magnitude
					if d <= HubConfig.padRadius and math.abs(r.Position.Y - centre.Y) < 6 then
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
