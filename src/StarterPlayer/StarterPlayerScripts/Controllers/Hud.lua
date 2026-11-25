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

-- Coins (top left)
local coinsLabel = Instance.new("TextLabel")
coinsLabel.AnchorPoint = Vector2.new(0, 0)
coinsLabel.Position = UDim2.new(0, 24, 0, 46)
coinsLabel.Size = UDim2.fromOffset(280, 50)
coinsLabel.BackgroundTransparency = 1
coinsLabel.Font = Enum.Font.FredokaOne
coinsLabel.TextScaled = true
coinsLabel.TextXAlignment = Enum.TextXAlignment.Left
coinsLabel.TextColor3 = Color3.fromRGB(255, 215, 60)
coinsLabel.Text = "COINS: 0"
local coinsStroke = Instance.new("UIStroke")
coinsStroke.Thickness = 3
coinsStroke.Color = Color3.fromRGB(90, 50, 0)
coinsStroke.Parent = coinsLabel
local coinsScale = Instance.new("UIScale")
coinsScale.Parent = coinsLabel
coinsLabel.Parent = gui
task.spawn(function()
	local stats = player:WaitForChild("leaderstats")
	local coins = stats:WaitForChild("Coins") :: IntValue
	local last = coins.Value
	local function show()
		coinsLabel.Text = "COINS: " .. coins.Value
		local jump = coins.Value - last
		last = coins.Value
		coinsScale.Scale = jump >= 5 and 1.4 or 1.12
		TweenService:Create(coinsScale, TweenInfo.new(jump >= 5 and 0.3 or 0.12, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end
	coins.Changed:Connect(show)
	show()
end)

-- Bag (under the coins): how full it is, and what it's worth
local BagState = require(script.Parent.BagState)
local bagFrame = Instance.new("Frame")
bagFrame.Position = UDim2.new(0, 24, 0, 102)
bagFrame.Size = UDim2.fromOffset(300, 30)
bagFrame.BackgroundColor3 = Color3.fromRGB(20, 40, 110)
bagFrame.BackgroundTransparency = 0.25
local bc = Instance.new("UICorner")
bc.CornerRadius = UDim.new(0, 10)
bc.Parent = bagFrame
local bagStroke = Instance.new("UIStroke")
bagStroke.Thickness = 2.5
bagStroke.Color = Color3.fromRGB(255, 255, 255)
bagStroke.Parent = bagFrame
local bagFill = Instance.new("Frame")
bagFill.Size = UDim2.fromScale(0, 1)
bagFill.BackgroundColor3 = Color3.fromRGB(90, 220, 120)
local fc = Instance.new("UICorner")
fc.CornerRadius = UDim.new(0, 10)
fc.Parent = bagFill
bagFill.Parent = bagFrame
local bagText = Instance.new("TextLabel")
bagText.Size = UDim2.fromScale(1, 1)
bagText.BackgroundTransparency = 1
bagText.Font = Enum.Font.FredokaOne
bagText.TextScaled = true
bagText.TextColor3 = Color3.new(1, 1, 1)
bagText.ZIndex = 2
local btPad = Instance.new("UIPadding")
btPad.PaddingTop = UDim.new(0, 4)
btPad.PaddingBottom = UDim.new(0, 4)
btPad.Parent = bagText
local bts = Instance.new("UIStroke")
bts.Thickness = 2
bts.Color = Color3.fromRGB(20, 40, 110)
bts.Parent = bagText
bagText.Parent = bagFrame
local bagScale = Instance.new("UIScale")
bagScale.Parent = bagFrame
bagFrame.Parent = gui

-- "BAG FULL" message in the middle
local fullMsg = Instance.new("TextLabel")
fullMsg.AnchorPoint = Vector2.new(0.5, 0.5)
fullMsg.Position = UDim2.fromScale(0.5, 0.64)
fullMsg.Size = UDim2.fromOffset(620, 44)
fullMsg.BackgroundTransparency = 1
fullMsg.Font = Enum.Font.FredokaOne
fullMsg.TextScaled = true
fullMsg.TextColor3 = Color3.fromRGB(255, 80, 80)
fullMsg.Text = "BAG FULL! Sell your plastic at the recycler"
fullMsg.Visible = false
local fms = Instance.new("UIStroke")
fms.Thickness = 3
fms.Color = Color3.fromRGB(70, 0, 0)
fms.Parent = fullMsg
local fullScale = Instance.new("UIScale")
fullScale.Parent = fullMsg
fullMsg.Parent = gui

local function showBag()
	local n, cap = BagState.count(), BagState.capacity()
	local worth = player:GetAttribute("BagValue") or 0
	bagText.Text = ("BAG %d/%d scraps  •  %d coins"):format(n, cap, worth)
	local full = n >= cap
	TweenService:Create(bagFill, TweenInfo.new(0.1), { Size = UDim2.fromScale(math.clamp(n / cap, 0, 1), 1) }):Play()
	bagFill.BackgroundColor3 = full and Color3.fromRGB(255, 70, 70) or Color3.fromRGB(90, 220, 120)
	fullMsg.Visible = full
end
for _, a in { "BagCount", "BagValue", "BagCapacity" } do
	player:GetAttributeChangedSignal(a):Connect(showBag)
end
showBag()
-- local pops show at once (before the server confirms)
task.spawn(function()
	while true do
		task.wait(0.1)
		showBag()
	end
end)

-- Where scraps fly to (the middle of the bag bar, in screen pixels)
function Hud.bagScreenPoint(): Vector2
	-- the HUD ignores the top bar inset, so these are viewport pixels already
	local p, s = bagFrame.AbsolutePosition, bagFrame.AbsoluteSize
	return Vector2.new(p.X + s.X * 0.15, p.Y + s.Y / 2)
end

-- A scrap landed in the bag
function Hud.bagBump()
	bagScale.Scale = 1.06
	TweenService:Create(bagScale, TweenInfo.new(0.1), { Scale = 1 }):Play()
end

-- Tried to pop with a full bag: shake the warning
local lastNag = 0
function Hud.bagFull()
	local now = os.clock()
	if now - lastNag < 0.6 then
		return
	end
	lastNag = now
	fullScale.Scale = 1.25
	TweenService:Create(fullScale, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	bagScale.Scale = 1.15
	TweenService:Create(bagScale, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end

-- Sold at the recycler: big "+N coins" in the middle
local soldMsg = Instance.new("TextLabel")
soldMsg.AnchorPoint = Vector2.new(0.5, 0.5)
soldMsg.Position = UDim2.fromScale(0.5, 0.36)
soldMsg.Size = UDim2.fromOffset(520, 70)
soldMsg.BackgroundTransparency = 1
soldMsg.Font = Enum.Font.FredokaOne
soldMsg.TextScaled = true
soldMsg.TextColor3 = Color3.fromRGB(255, 215, 60)
soldMsg.TextTransparency = 1
local sms = Instance.new("UIStroke")
sms.Thickness = 4
sms.Color = Color3.fromRGB(90, 50, 0)
sms.Transparency = 1
sms.Parent = soldMsg
local soldScale = Instance.new("UIScale")
soldScale.Parent = soldMsg
soldMsg.Parent = gui
local soldId = 0
function Hud.sold(coins: number, n: number)
	soldId += 1
	local mine = soldId
	soldMsg.Text = ("SOLD %d scraps  +%d coins"):format(n, coins)
	soldMsg.TextTransparency = 0
	sms.Transparency = 0
	soldScale.Scale = 0.5
	TweenService:Create(soldScale, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	task.delay(1.6, function()
		if mine == soldId then
			TweenService:Create(soldMsg, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
			TweenService:Create(sms, TweenInfo.new(0.4), { Transparency = 1 }):Play()
		end
	end)
end

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
	or "Hold click to poke  •  L = switch look  •  1-9 = pop sound  •  K = squeeze sound"
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

-- Short message in the middle-top (test-room switches)
local toast = Instance.new("TextLabel")
toast.AnchorPoint = Vector2.new(0.5, 0)
toast.Position = UDim2.new(0.5, 0, 0, 104)
toast.Size = UDim2.fromOffset(420, 32)
toast.BackgroundTransparency = 1
toast.Font = Enum.Font.FredokaOne
toast.TextScaled = true
toast.TextColor3 = Color3.fromRGB(255, 235, 90)
toast.TextTransparency = 1
local ts = Instance.new("UIStroke")
ts.Thickness = 2
ts.Color = Color3.fromRGB(20, 40, 110)
ts.Transparency = 1
ts.Parent = toast
toast.Parent = gui
local toastId = 0
function Hud.toast(text: string)
	toastId += 1
	local mine = toastId
	toast.Text = text
	toast.TextTransparency = 0
	ts.Transparency = 0
	task.delay(2, function()
		if mine == toastId then
			TweenService:Create(toast, TweenInfo.new(0.4), { TextTransparency = 1 }):Play()
			TweenService:Create(ts, TweenInfo.new(0.4), { Transparency = 1 }):Play()
		end
	end)
end

return Hud
