-- Crosshair, pop counter, hint text and the phone POP button.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Hud = {}

local DARK_BLUE = Color3.fromRGB(20, 40, 110)

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

-- Bottom left: coins and bag in rounded "pills" with icons (Luckiest Guy, owner's pick)
local PILL_FONT = Font.fromEnum(Enum.Font.LuckiestGuy)

local function withCommas(n: number): string
	local s = tostring(math.floor(n))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end

local function pill(y: number, edge: Color3): Frame
	local f = Instance.new("Frame")
	f.AnchorPoint = Vector2.new(0, 1)
	f.Position = UDim2.new(0, 18, 1, y)
	f.Size = UDim2.fromOffset(190, 44)
	f.BackgroundColor3 = Color3.fromRGB(20, 35, 90)
	f.BackgroundTransparency = 0.2
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = f
	local st = Instance.new("UIStroke")
	st.Thickness = 2.5
	st.Color = edge
	st.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	st.Parent = f
	f.Parent = gui
	return f
end

local function pillText(parent: Frame, strokeCol: Color3): TextLabel
	local t = Instance.new("TextLabel")
	t.Position = UDim2.fromOffset(48, 5)
	t.Size = UDim2.new(1, -60, 1, -8)
	t.BackgroundTransparency = 1
	t.FontFace = PILL_FONT
	t.TextScaled = true
	t.TextXAlignment = Enum.TextXAlignment.Left
	t.TextColor3 = Color3.new(1, 1, 1)
	local st = Instance.new("UIStroke")
	st.Thickness = 2.5
	st.Color = strokeCol
	st.Parent = t
	t.Parent = parent
	return t
end

-- a drawn coin: gold disc with a lighter middle
local function coinIcon(parent: Instance, size: number)
	local c = Instance.new("Frame")
	c.Position = UDim2.fromOffset(5, 5)
	c.Size = UDim2.fromOffset(size, size)
	c.BackgroundColor3 = Color3.new(1, 1, 1)
	local k = Instance.new("UICorner")
	k.CornerRadius = UDim.new(1, 0)
	k.Parent = c
	local st = Instance.new("UIStroke")
	st.Thickness = 2.5
	st.Color = Color3.fromRGB(150, 90, 0)
	st.Parent = c
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new(Color3.fromRGB(255, 240, 150), Color3.fromRGB(255, 170, 20))
	g.Rotation = 90
	g.Parent = c
	local inner = Instance.new("Frame")
	inner.AnchorPoint = Vector2.new(0.5, 0.5)
	inner.Position = UDim2.fromScale(0.5, 0.5)
	inner.Size = UDim2.fromScale(0.55, 0.55)
	inner.BackgroundColor3 = Color3.fromRGB(255, 225, 110)
	local k2 = Instance.new("UICorner")
	k2.CornerRadius = UDim.new(1, 0)
	k2.Parent = inner
	inner.Parent = c
	c.Parent = parent
end

local coinsPill = pill(-110, Color3.fromRGB(255, 215, 80))
coinIcon(coinsPill, 34)
local coinsLabel = pillText(coinsPill, Color3.fromRGB(90, 45, 0))
local coinGrad = Instance.new("UIGradient")
coinGrad.Color = ColorSequence.new(Color3.fromRGB(255, 245, 170), Color3.fromRGB(255, 185, 30))
coinGrad.Rotation = 90
coinGrad.Parent = coinsLabel
coinsLabel.Text = "0"
local coinsScale = Instance.new("UIScale")
coinsScale.Parent = coinsPill
task.spawn(function()
	local stats = player:WaitForChild("leaderstats")
	local coins = stats:WaitForChild("Coins") :: IntValue
	local last = coins.Value
	local function show()
		coinsLabel.Text = withCommas(coins.Value)
		local jump = coins.Value - last
		last = coins.Value
		coinsScale.Scale = jump >= 5 and 1.2 or 1.08
		TweenService:Create(coinsScale, TweenInfo.new(jump >= 5 and 0.3 or 0.12, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	end
	coins.Changed:Connect(show)
	show()
end)

local BagState = require(script.Parent.BagState)
local bagFrame = pill(-58, Color3.fromRGB(150, 210, 255))
local bagIcon = Instance.new("TextLabel")
bagIcon.BackgroundTransparency = 1
bagIcon.Text = "🎒"
bagIcon.TextScaled = true
bagIcon.Position = UDim2.fromOffset(6, 5)
bagIcon.Size = UDim2.fromOffset(34, 34)
bagIcon.Parent = bagFrame
local bagText = pillText(bagFrame, DARK_BLUE)
local bagScale = Instance.new("UIScale")
bagScale.Parent = bagFrame

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
	local full = n >= cap
	bagText.Text = withCommas(n) .. "/" .. withCommas(cap)
	bagText.TextColor3 = full and Color3.fromRGB(255, 80, 80) or Color3.new(1, 1, 1)
	fullMsg.Visible = full
	local _ = worth
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

-- Run timer (top left): how long this run has lasted, and bubbles left
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local timerLabel = Instance.new("TextLabel")
timerLabel.Position = UDim2.fromOffset(20, 50)
timerLabel.Size = UDim2.fromOffset(200, 40)
timerLabel.BackgroundTransparency = 1
timerLabel.Font = Enum.Font.FredokaOne
timerLabel.TextScaled = true
timerLabel.TextXAlignment = Enum.TextXAlignment.Left
timerLabel.TextColor3 = Color3.new(1, 1, 1)
timerLabel.Text = "00:00"
local tls = Instance.new("UIStroke")
tls.Thickness = 3
tls.Color = DARK_BLUE
tls.Parent = timerLabel
timerLabel.Parent = gui
local leftLabel = Instance.new("TextLabel")
leftLabel.Position = UDim2.fromOffset(20, 90)
leftLabel.Size = UDim2.fromOffset(240, 24)
leftLabel.BackgroundTransparency = 1
leftLabel.Font = Enum.Font.FredokaOne
leftLabel.TextScaled = true
leftLabel.TextXAlignment = Enum.TextXAlignment.Left
leftLabel.TextColor3 = Color3.fromRGB(200, 225, 255)
local lls = Instance.new("UIStroke")
lls.Thickness = 2
lls.Color = DARK_BLUE
lls.Parent = leftLabel
leftLabel.Parent = gui

local function clock(seconds: number): string
	seconds = math.max(0, math.floor(seconds))
	local h, m, sec = seconds // 3600, (seconds // 60) % 60, seconds % 60
	if h > 0 then
		return ("%d:%02d:%02d"):format(h, m, sec)
	end
	return ("%02d:%02d"):format(m, sec)
end

-- Room cleared: a big message with the time it took
local clearedMsg = Instance.new("TextLabel")
clearedMsg.AnchorPoint = Vector2.new(0.5, 0.5)
clearedMsg.Position = UDim2.fromScale(0.5, 0.32)
clearedMsg.Size = UDim2.fromOffset(640, 120)
clearedMsg.BackgroundTransparency = 1
clearedMsg.Font = Enum.Font.FredokaOne
clearedMsg.TextScaled = true
clearedMsg.TextColor3 = Color3.fromRGB(255, 225, 70)
clearedMsg.Visible = false
local cms = Instance.new("UIStroke")
cms.Thickness = 5
cms.Color = Color3.fromRGB(90, 50, 0)
cms.Parent = clearedMsg
local clearedScale = Instance.new("UIScale")
clearedScale.Parent = clearedMsg
clearedMsg.Parent = gui

local function showLeft()
	local left = ReplicatedStorage:GetAttribute("BubblesLeft")
	leftLabel.Text = left and (left .. " bubbles left") or ""
end
ReplicatedStorage:GetAttributeChangedSignal("BubblesLeft"):Connect(showLeft)
showLeft()

local function showCleared()
	local t = ReplicatedStorage:GetAttribute("RunClearTime")
	if not t or clearedMsg.Visible then
		return
	end
	timerLabel.Text = clock(t)
	timerLabel.TextColor3 = Color3.fromRGB(255, 225, 70)
	clearedMsg.Text = "ROOM CLEARED!\n" .. clock(t)
	clearedMsg.Visible = true
	clearedScale.Scale = 0.3
	TweenService:Create(clearedScale, TweenInfo.new(0.5, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end
ReplicatedStorage:GetAttributeChangedSignal("RunClearTime"):Connect(showCleared)
showCleared()

task.spawn(function()
	while true do
		task.wait(0.25)
		local start = ReplicatedStorage:GetAttribute("RunStart")
		if start and not ReplicatedStorage:GetAttribute("RunClearTime") then
			timerLabel.Text = clock(workspace:GetServerTimeNow() - start)
		end
	end
end)

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
hint.Text = UserInputService.TouchEnabled and "Hold POP to poke  •  SHOP for upgrades"
	or "Hold click to poke  •  B = shop  •  L = look  •  1-9 = pop sound  •  K = squeeze sound"
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
