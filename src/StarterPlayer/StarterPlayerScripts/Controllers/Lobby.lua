-- Hub vs popping room on this client. In the hub: third person, no run HUD, a hint and (for the
-- player who stepped on a pad first) a panel to pick the room and press Start.
-- In a run (player attribute InRun): first person, run HUD and shop.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local HubConfig = require(ReplicatedStorage.Shared.Config.Hub)
local Hud = require(script.Parent.Hud)
local Shop = require(script.Parent.Shop)

local Lobby = {}

local player = Players.LocalPlayer
local DARK = Color3.fromRGB(20, 40, 110)

local function text(parent: Instance, t: string, size: UDim2, pos: UDim2, col: Color3?): TextLabel
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	l.TextScaled = true
	l.TextColor3 = col or Color3.new(1, 1, 1)
	l.Text = t
	l.Size = size
	l.Position = pos
	local st = Instance.new("UIStroke")
	st.Thickness = 3
	st.Color = DARK
	st.Parent = l
	l.Parent = parent
	return l
end

function Lobby.start(remotes: Folder)
	local StartPad = remotes:WaitForChild("StartPad") :: RemoteEvent

	local gui = Instance.new("ScreenGui")
	gui.Name = "HubGui"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.Parent = player:WaitForChild("PlayerGui")

	local hint = text(gui, "STEP ON A PAD TO PLAY!", UDim2.fromOffset(520, 40), UDim2.new(0.5, -260, 0, 50), Color3.fromRGB(255, 225, 80))

	-- pad owner panel: room picker + Start
	local panel = Instance.new("Frame")
	panel.AnchorPoint = Vector2.new(0.5, 1)
	panel.Position = UDim2.new(0.5, 0, 1, -30)
	panel.Size = UDim2.fromOffset(420, 150)
	panel.BackgroundColor3 = Color3.fromRGB(40, 90, 190)
	panel.Visible = false
	local pc = Instance.new("UICorner")
	pc.CornerRadius = UDim.new(0, 18)
	pc.Parent = panel
	local ps = Instance.new("UIStroke")
	ps.Thickness = 4
	ps.Color = DARK
	ps.Parent = panel
	panel.Parent = gui
	local title = text(panel, "YOUR PAD", UDim2.new(1, -24, 0, 32), UDim2.fromOffset(12, 10), Color3.fromRGB(255, 225, 80))
	local roomName = text(panel, "Room: " .. HubConfig.rooms[1].name, UDim2.new(1, -24, 0, 26), UDim2.fromOffset(12, 46))
	local startBtn = Instance.new("TextButton")
	startBtn.AnchorPoint = Vector2.new(0.5, 1)
	startBtn.Position = UDim2.new(0.5, 0, 1, -12)
	startBtn.Size = UDim2.fromOffset(240, 56)
	startBtn.BackgroundColor3 = Color3.fromRGB(60, 200, 90)
	startBtn.FontFace = Font.fromEnum(Enum.Font.LuckiestGuy)
	startBtn.TextScaled = true
	startBtn.TextColor3 = Color3.new(1, 1, 1)
	startBtn.Text = "START"
	local bc = Instance.new("UICorner")
	bc.CornerRadius = UDim.new(0, 14)
	bc.Parent = startBtn
	local bs = Instance.new("UIStroke")
	bs.Thickness = 3
	bs.Color = DARK
	bs.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	bs.Parent = startBtn
	local pad = Instance.new("UIPadding")
	pad.PaddingTop, pad.PaddingBottom = UDim.new(0, 8), UDim.new(0, 8)
	pad.Parent = startBtn
	startBtn.Parent = panel
	startBtn.MouseButton1Click:Connect(function()
		StartPad:FireServer()
	end)
	local _ = roomName

	local function padPart(i: number): BasePart?
		local hub = workspace:FindFirstChild("Hub")
		return hub and hub:FindFirstChild("Pad" .. i) :: BasePart?
	end

	local function refreshPanel()
		local i = player:GetAttribute("PadOwner")
		local part = i and padPart(i)
		panel.Visible = part ~= nil and player:GetAttribute("InRun") ~= true
		if part then
			title.Text = ("PAD %d  •  %d/%d  •  %ds"):format(i, part:GetAttribute("Members") or 1, HubConfig.maxPlayers, part:GetAttribute("Countdown") or 0)
		end
	end

	local function apply()
		local inRun = player:GetAttribute("InRun") == true
		if Hud.gui then
			Hud.gui.Enabled = inRun
		end
		if Shop.gui then
			Shop.gui.Enabled = inRun
		end
		hint.Visible = not inRun
		player.CameraMode = inRun and Enum.CameraMode.LockFirstPerson or Enum.CameraMode.Classic
		UserInputService.MouseIconEnabled = not inRun -- in a run the Hud draws a crosshair
		if not inRun then
			player.CameraMaxZoomDistance = 20
			player.CameraMinZoomDistance = 6 -- pull the camera out of first person in the hub
			task.delay(0.1, function()
				player.CameraMinZoomDistance = 0.5
			end)
		end
		refreshPanel()
	end
	player:GetAttributeChangedSignal("InRun"):Connect(apply)
	player:GetAttributeChangedSignal("PadOwner"):Connect(refreshPanel)
	task.spawn(function()
		while true do
			task.wait(0.25)
			refreshPanel()
		end
	end)
	apply()
end

return Lobby
