-- Crosshair, pop counter, hint text and the phone POP button.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Hud = {}

local player = Players.LocalPlayer
local gui = Instance.new("ScreenGui")
gui.Name = "Hud"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = player:WaitForChild("PlayerGui")

-- Crosshair: a small plus with a dark outline
local cross = Instance.new("Frame")
cross.Name = "Crosshair"
cross.AnchorPoint = Vector2.new(0.5, 0.5)
cross.Position = UDim2.fromScale(0.5, 0.5)
cross.Size = UDim2.fromOffset(22, 22)
cross.BackgroundTransparency = 1
cross.Parent = gui
local bars = {}
for _, size in { UDim2.new(1, 0, 0, 4), UDim2.new(0, 4, 1, 0) } do
	local bar = Instance.new("Frame")
	bar.AnchorPoint = Vector2.new(0.5, 0.5)
	bar.Position = UDim2.fromScale(0.5, 0.5)
	bar.Size = size
	bar.BackgroundColor3 = Color3.new(1, 1, 1)
	bar.BorderSizePixel = 0
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 1.5
	stroke.Color = Color3.fromRGB(20, 25, 40)
	stroke.Parent = bar
	bar.Parent = cross
	table.insert(bars, bar)
end
local crossScale = Instance.new("UIScale")
crossScale.Parent = cross

local aiming = false
function Hud.setAim(on: boolean)
	if on == aiming then
		return
	end
	aiming = on
	for _, bar in bars do
		bar.BackgroundColor3 = on and Color3.fromRGB(255, 225, 60) or Color3.new(1, 1, 1)
	end
	TweenService:Create(crossScale, TweenInfo.new(0.08), { Scale = on and 1.3 or 1 }):Play()
end

function Hud.kick()
	crossScale.Scale = 1.7
	TweenService:Create(crossScale, TweenInfo.new(0.15, Enum.EasingStyle.Quad), { Scale = aiming and 1.3 or 1 }):Play()
end

-- Pop counter
local counter = Instance.new("TextLabel")
counter.AnchorPoint = Vector2.new(0.5, 0)
counter.Position = UDim2.new(0.5, 0, 0, 46)
counter.Size = UDim2.fromOffset(260, 50)
counter.BackgroundTransparency = 1
counter.Font = Enum.Font.FredokaOne
counter.TextScaled = true
counter.TextColor3 = Color3.new(1, 1, 1)
counter.Text = "POPS: 0"
local cs = Instance.new("UIStroke")
cs.Thickness = 3
cs.Color = Color3.fromRGB(20, 40, 110)
cs.Parent = counter
local counterScale = Instance.new("UIScale")
counterScale.Parent = counter
counter.Parent = gui

local function watchPops()
	local stats = player:WaitForChild("leaderstats")
	local pops = stats:WaitForChild("Pops") :: IntValue
	local function show()
		counter.Text = "POPS: " .. pops.Value
		counterScale.Scale = 1.15
		TweenService:Create(counterScale, TweenInfo.new(0.12), { Scale = 1 }):Play()
	end
	pops.Changed:Connect(show)
	show()
end
task.spawn(watchPops)

-- Hint
local hint = Instance.new("TextLabel")
hint.AnchorPoint = Vector2.new(0.5, 1)
hint.Position = UDim2.new(0.5, 0, 1, -20)
hint.Size = UDim2.fromOffset(520, 28)
hint.BackgroundTransparency = 1
hint.Font = Enum.Font.FredokaOne
hint.TextScaled = true
hint.TextColor3 = Color3.new(1, 1, 1)
hint.TextTransparency = 0.15
hint.Text = UserInputService.TouchEnabled and "Hold POP to poke  •  walk on the floor wrap"
	or "Hold click to poke  •  walk on the floor wrap"
local hs = Instance.new("UIStroke")
hs.Thickness = 2
hs.Color = Color3.fromRGB(20, 40, 110)
hs.Parent = hint
hint.Parent = gui

-- Phone: a big POP button (hold to keep popping)
Hud.popButton = nil :: TextButton?
if UserInputService.TouchEnabled then
	local b = Instance.new("TextButton")
	b.AnchorPoint = Vector2.new(1, 1)
	b.Position = UDim2.new(1, -30, 1, -110)
	b.Size = UDim2.fromOffset(110, 110)
	b.BackgroundColor3 = Color3.fromRGB(255, 70, 175)
	b.Font = Enum.Font.FredokaOne
	b.Text = "POP"
	b.TextScaled = true
	b.TextColor3 = Color3.new(1, 1, 1)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = b
	local st = Instance.new("UIStroke")
	st.Thickness = 4
	st.Color = Color3.fromRGB(110, 10, 70)
	st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	st.Parent = b
	b.Parent = gui
	Hud.popButton = b
end

return Hud
