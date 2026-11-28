-- The hub's free gift chest opens when you walk up to it (this player only; cosmetic, no reward yet:
-- the reward comes later and will be decided on the server). The lid turns about its back hinge with a
-- little bounce, confetti bursts out, a soft glow comes from inside and a light chime plays. It closes
-- again when you walk away, and stays shut while you're in a run. Numbers: Config/Hub.lua classic.chest (colours come from the palette, set by HubClassic).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local HubConfig = require(ReplicatedStorage.Shared.Config.Hub)
local Sfx = require(script.Parent.Sfx)

local HubChest = {}

function HubChest.start()
	local C = HubConfig.classic and HubConfig.classic.chest
	if not (HubConfig.classicOn and C) then
		return
	end
	task.spawn(function()
		local hub = workspace:WaitForChild("Hub", 30)
		local chest = hub and hub:WaitForChild("GiftChest", 30)
		if not chest then
			return
		end
		local hinge = chest:WaitForChild("Hinge") :: BasePart
		local lid = chest:WaitForChild("Lid") :: Model
		local glowPart = chest:WaitForChild("ChestGlow") :: BasePart
		local light = glowPart:WaitForChild("Glow") :: PointLight
		local confetti = glowPart:WaitForChild("Confetti") :: ParticleEmitter
		local base = hinge.CFrame
		local parts: { BasePart } = {}
		local offsets: { CFrame } = {}
		for _, p in lid:GetDescendants() do
			if p:IsA("BasePart") then
				table.insert(parts, p)
				table.insert(offsets, base:ToObjectSpace(p.CFrame))
			end
		end

		local angle = Instance.new("NumberValue") -- degrees the lid is open
		local cframes: { CFrame } = table.create(#parts)
		angle.Changed:Connect(function(a)
			local turn = base * CFrame.Angles(math.rad(a), 0, 0)
			for i, off in offsets do
				cframes[i] = turn * off
			end
			workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
		end)

		local player = Players.LocalPlayer
		local open = false
		local tween: Tween? = nil
		local function set(want: boolean)
			if want == open then
				return
			end
			open = want
			if tween then
				tween:Cancel()
			end
			if want then
				tween = TweenService:Create(angle, TweenInfo.new(C.openTime, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Value = C.openAngle })
				light.Enabled = true
				TweenService:Create(light, TweenInfo.new(C.openTime), { Brightness = C.glowBrightness }):Play()
				confetti:Emit(C.confettiCount)
				Sfx.play(C.sound, glowPart.Position)
			else
				tween = TweenService:Create(angle, TweenInfo.new(C.closeTime, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Value = 0 })
				TweenService:Create(light, TweenInfo.new(C.closeTime), { Brightness = 0 }):Play()
			end
			(tween :: Tween):Play()
		end

		local acc = 0
		RunService.Heartbeat:Connect(function(dt)
			acc += dt
			if acc < 0.1 then
				return
			end
			acc = 0
			local char = player.Character
			local root = char and char:FindFirstChild("HumanoidRootPart") :: BasePart?
			local near = false
			if root and player:GetAttribute("InRun") ~= true then
				local d = root.Position - glowPart.Position -- (from the middle of the chest)
				near = Vector2.new(d.X, d.Z).Magnitude <= C.radius and math.abs(d.Y) < 10
			end
			set(near)
		end)
	end)
end

return HubChest
