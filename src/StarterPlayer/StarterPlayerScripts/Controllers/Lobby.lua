-- Hub vs popping room on this client. In the hub: third person, no run HUD, a hint and (for the
-- player who stepped on a pad first) a panel to pick the room and press Start.
-- In a run (player attribute InRun): first person, run HUD and shop.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local HubConfig = require(ReplicatedStorage.Shared.Config.Hub)
local Hud = require(script.Parent.Hud)
local BubbleView = require(script.Parent.BubbleView)
local Shop = require(script.Parent.Shop)

local Lobby = {}

---------------------------------------------------------------- hub lighting (clean theme)
-- Lighting is global, so the hub's look is put on while not in a run and the room's taken back
-- for a run: the properties below are saved as they are now (the server's values), the hub's own
-- effects are only enabled in the hub, and BubbleView puts the room look's lighting back.
local Lighting = game:GetService("Lighting")
local HUB_LIT = HubConfig.theme == "clean" and HubConfig.lighting or nil
local PROPS = { "Brightness", "ClockTime", "GeographicLatitude", "Ambient", "OutdoorAmbient", "ColorShift_Top", "ExposureCompensation", "GlobalShadows", "ShadowSoftness", "EnvironmentDiffuseScale", "EnvironmentSpecularScale" }
local saved: { [string]: any } = {}
for _, k in PROPS do
	saved[k] = (Lighting :: any)[k]
end
local function rgb(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local hubBloom, hubCC, hubAtmo
if HUB_LIT then
	hubBloom = Instance.new("BloomEffect")
	hubBloom.Name = "HubBloom"
	hubBloom.Enabled = false
	hubBloom.Intensity = HUB_LIT.bloom.intensity
	hubBloom.Size = HUB_LIT.bloom.size
	hubBloom.Threshold = HUB_LIT.bloom.threshold
	hubBloom.Parent = Lighting
	hubCC = Instance.new("ColorCorrectionEffect")
	hubCC.Name = "HubColour"
	hubCC.Enabled = false
	hubCC.Saturation = HUB_LIT.colorCorrection.saturation
	hubCC.Contrast = HUB_LIT.colorCorrection.contrast
	hubCC.Brightness = HUB_LIT.colorCorrection.brightness
	hubCC.TintColor = rgb(HUB_LIT.colorCorrection.tint)
	hubCC.Parent = Lighting
	local a = HUB_LIT.atmosphere
	hubAtmo = Instance.new("Atmosphere") -- (no Enabled switch: parented to Lighting only in the hub)
	hubAtmo.Name = "HubAtmosphere"
	hubAtmo.Density = a.density
	hubAtmo.Offset = a.offset
	hubAtmo.Color = rgb(a.color)
	hubAtmo.Decay = rgb(a.decay)
	hubAtmo.Glare = a.glare
	hubAtmo.Haze = a.haze
end

local function hubLighting(on: boolean)
	if not HUB_LIT then
		return
	end
	local L = Lighting :: any
	if on then
		L.Brightness = HUB_LIT.brightness
		L.ClockTime = HUB_LIT.clockTime
		L.GeographicLatitude = HUB_LIT.latitude
		L.Ambient = rgb(HUB_LIT.ambient)
		L.OutdoorAmbient = rgb(HUB_LIT.outdoor)
		L.ColorShift_Top = rgb(HUB_LIT.colorShiftTop)
		L.ExposureCompensation = HUB_LIT.exposure
		L.GlobalShadows = true
		L.ShadowSoftness = HUB_LIT.shadowSoftness
		L.EnvironmentDiffuseScale = HUB_LIT.envDiffuse
		L.EnvironmentSpecularScale = HUB_LIT.envSpecular
		local roomBloom = Lighting:FindFirstChild("LookBloom") :: BloomEffect?
		if roomBloom then
			roomBloom.Enabled = false
		end
		hubAtmo.Parent = Lighting
	else
		for _, k in PROPS do
			L[k] = saved[k]
		end
		hubAtmo.Parent = nil
		BubbleView.applyLighting() -- the room look's brightness, time, ambient, bloom
	end
	hubBloom.Enabled = on
	hubCC.Enabled = on
end

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
		hubLighting(not inRun)
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
