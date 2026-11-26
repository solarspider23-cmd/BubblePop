-- TEMPORARY shop panel for testing upgrades (the owner is picking a real UI template).
-- B or the SHOP button opens it. Buying asks the server; the server decides.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Upgrades = require(ReplicatedStorage.Shared.Config.Upgrades)
local UpgradeRules = require(ReplicatedStorage.Shared.Rules.Upgrades)
local Format = require(ReplicatedStorage.Shared.Format)
local Hud = require(script.Parent.Hud)
local Sfx = require(script.Parent.Sfx)

local Shop = {}

local player = Players.LocalPlayer
local DARK = Color3.fromRGB(20, 40, 110)

local function label(parent: Instance, text: string, size: UDim2, pos: UDim2, col: Color3?, align: Enum.TextXAlignment?): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.FredokaOne
	t.TextScaled = true
	t.TextColor3 = col or Color3.new(1, 1, 1)
	t.TextXAlignment = align or Enum.TextXAlignment.Left
	t.Text = text
	t.Size = size
	t.Position = pos
	local st = Instance.new("UIStroke")
	st.Thickness = 2
	st.Color = DARK
	st.Parent = t
	t.Parent = parent
	return t
end

local function round(o: GuiObject, r: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r)
	c.Parent = o
end

local function describe(kind: string, lvl: number): string
	local u = Upgrades[kind]
	local v = UpgradeRules.value(Upgrades, kind, lvl)
	if u.levelNames then
		local name = u.levelNames[lvl] or ("Level " .. lvl)
		if kind == "boots" and v == 0 then
			return name .. ": walking doesn't pop"
		end
		return name .. ": " .. u.describe:format(v)
	end
	return u.describe:format(v)
end

function Shop.start(remotes: Folder)
	local BuyUpgrade = remotes:WaitForChild("BuyUpgrade") :: RemoteFunction
	local TestCoins = remotes:WaitForChild("TestCoins") :: RemoteEvent

	local gui = Instance.new("ScreenGui")
	gui.Name = "Shop"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.DisplayOrder = 5
	gui.Parent = player:WaitForChild("PlayerGui")

	-- open button (right side)
	local open = Instance.new("TextButton")
	open.AnchorPoint = Vector2.new(1, 0.5)
	open.Position = UDim2.new(1, -24, 0.5, 0)
	open.Size = UDim2.fromOffset(130, 56)
	open.BackgroundColor3 = Color3.fromRGB(255, 190, 40)
	open.Font = Enum.Font.FredokaOne
	open.TextScaled = true
	open.TextColor3 = Color3.new(1, 1, 1)
	open.Text = UserInputService.TouchEnabled and "SHOP" or "SHOP (B)"
	round(open, 14)
	local os_ = Instance.new("UIStroke")
	os_.Thickness = 3
	os_.Color = Color3.fromRGB(120, 70, 0)
	os_.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	os_.Parent = open
	local op = Instance.new("UIPadding")
	op.PaddingTop, op.PaddingBottom = UDim.new(0, 8), UDim.new(0, 8)
	op.Parent = open
	open.Parent = gui

	-- panel
	local panel = Instance.new("Frame")
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.Position = UDim2.fromScale(0.5, 0.5)
	panel.Size = UDim2.fromOffset(560, 84 + #Upgrades.order * 96 + (RunService:IsStudio() and 66 or 0))
	panel.BackgroundColor3 = Color3.fromRGB(40, 90, 190)
	panel.Active = true
	panel.Visible = false
	round(panel, 18)
	local ps = Instance.new("UIStroke")
	ps.Thickness = 4
	ps.Color = DARK
	ps.Parent = panel
	panel.Parent = gui
	label(panel, "SHOP  (test version)", UDim2.new(1, -120, 0, 44), UDim2.fromOffset(24, 16), Color3.fromRGB(255, 225, 90))

	-- close button. Modal = frees the mouse from first person while the shop is open.
	local close = Instance.new("TextButton")
	close.AnchorPoint = Vector2.new(1, 0)
	close.Position = UDim2.new(1, -14, 0, 14)
	close.Size = UDim2.fromOffset(48, 48)
	close.BackgroundColor3 = Color3.fromRGB(230, 60, 70)
	close.Font = Enum.Font.FredokaOne
	close.TextScaled = true
	close.TextColor3 = Color3.new(1, 1, 1)
	close.Text = "X"
	close.Modal = true
	round(close, 12)
	close.Parent = panel

	local rows: { [string]: { lvl: TextLabel, desc: TextLabel, buy: TextButton } } = {}
	for i, kind in Upgrades.order do
		local u = Upgrades[kind]
		local row = Instance.new("Frame")
		row.Position = UDim2.fromOffset(18, 74 + (i - 1) * 96)
		row.Size = UDim2.new(1, -36, 0, 84)
		row.BackgroundColor3 = Color3.fromRGB(25, 60, 140)
		round(row, 14)
		row.Parent = panel
		label(row, u.name, UDim2.new(0.6, 0, 0, 34), UDim2.fromOffset(16, 8))
		local lvl = label(row, "", UDim2.new(0.25, 0, 0, 24), UDim2.new(0.38, 0, 0, 13), Color3.fromRGB(170, 210, 255))
		local desc = label(row, "", UDim2.new(0.62, 0, 0, 26), UDim2.fromOffset(16, 48), Color3.fromRGB(220, 235, 255))
		local buy = Instance.new("TextButton")
		buy.AnchorPoint = Vector2.new(1, 0.5)
		buy.Position = UDim2.new(1, -12, 0.5, 0)
		buy.Size = UDim2.fromOffset(150, 58)
		buy.Font = Enum.Font.FredokaOne
		buy.TextScaled = true
		buy.TextColor3 = Color3.new(1, 1, 1)
		round(buy, 12)
		local bp = Instance.new("UIPadding")
		bp.PaddingTop, bp.PaddingBottom = UDim.new(0, 8), UDim.new(0, 8)
		bp.Parent = buy
		buy.Parent = row
		rows[kind] = { lvl = lvl, desc = desc, buy = buy }
		buy.MouseButton1Click:Connect(function()
			local ok, msg = BuyUpgrade:InvokeServer(kind)
			if ok then
				Sfx.play("sell")
				Hud.toast(u.name .. "!  " .. describe(kind, player:GetAttribute("Upg_" .. kind) or 1))
			else
				Hud.toast(msg == "maxed" and "Already maxed" or "Not enough money")
			end
		end)
	end

	if RunService:IsStudio() then
		local test = Instance.new("TextButton")
		test.Position = UDim2.new(0, 18, 1, -62)
		test.Size = UDim2.new(0.5, -24, 0, 46)
		test.BackgroundColor3 = Color3.fromRGB(120, 60, 200)
		test.Font = Enum.Font.FredokaOne
		test.TextScaled = true
		test.TextColor3 = Color3.new(1, 1, 1)
		test.Text = "+$10 (test)"
		round(test, 12)
		local tp = Instance.new("UIPadding")
		tp.PaddingTop, tp.PaddingBottom = UDim.new(0, 8), UDim.new(0, 8)
		tp.Parent = test
		test.Parent = panel
		test.MouseButton1Click:Connect(function()
			TestCoins:FireServer()
		end)
		local clear = test:Clone()
		clear.Position = UDim2.new(0.5, 6, 1, -62)
		clear.Text = "Pop all but 10 (test)"
		clear.Parent = panel
		clear.MouseButton1Click:Connect(function()
			(remotes:WaitForChild("TestClear") :: RemoteEvent):FireServer()
		end)
	end

	local function coins(): number
		local stats = player:FindFirstChild("leaderstats")
		local c = stats and stats:FindFirstChild("Coins") :: IntValue?
		return c and c.Value or 0
	end

	local function refresh()
		for kind, r in rows do
			local lvl = player:GetAttribute("Upg_" .. kind) or 1
			local max = #Upgrades[kind].values
			r.lvl.Text = ("Lv %d/%d"):format(lvl, max)
			local cost = UpgradeRules.nextCost(Upgrades, kind, lvl)
			if cost then
				r.desc.Text = describe(kind, lvl) .. "  →  " .. describe(kind, lvl + 1):gsub("^.-: ", "")
				r.buy.Text = Format.money(cost) -- prices are in cents
				r.buy.BackgroundColor3 = coins() >= cost and Color3.fromRGB(60, 200, 90) or Color3.fromRGB(110, 120, 140)
			else
				r.desc.Text = describe(kind, lvl)
				r.buy.Text = "MAX"
				r.buy.BackgroundColor3 = Color3.fromRGB(255, 190, 40)
			end
		end
	end

	local function setOpen(on: boolean)
		panel.Visible = on
		UserInputService.MouseIconEnabled = on
		if on then
			refresh()
		end
	end
	open.MouseButton1Click:Connect(function()
		setOpen(not panel.Visible)
	end)
	close.MouseButton1Click:Connect(function()
		setOpen(false)
	end)
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and input.KeyCode == Enum.KeyCode.B then
			setOpen(not panel.Visible)
		end
	end)

	player.AttributeChanged:Connect(function(a)
		if a:sub(1, 4) == "Upg_" and panel.Visible then
			refresh()
		end
	end)
	task.spawn(function()
		local stats = player:WaitForChild("leaderstats")
		local c = stats:WaitForChild("Coins") :: IntValue
		c.Changed:Connect(function()
			if panel.Visible then
				refresh()
			end
		end)
	end)
end

return Shop
