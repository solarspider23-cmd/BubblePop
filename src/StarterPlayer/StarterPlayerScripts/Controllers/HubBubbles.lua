-- Glassy bubbles drifting up around the lobby island (this player only; cosmetic).
-- Each bubble rises with a gentle wobble, then pops at the top and starts again near the ground.
-- Hidden while you're in a run.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local HubConfig = require(ReplicatedStorage.Shared.Config.Hub)

local HubBubbles = {}

function HubBubbles.start()
	local cfg = HubConfig.floatingBubbles
	if not cfg then
		return
	end
	local player = Players.LocalPlayer
	local O = Vector3.new(HubConfig.origin[1], HubConfig.origin[2], HubConfig.origin[3])
	local rng = Random.new()
	local folder = Instance.new("Folder")
	folder.Name = "HubBubbles"

	type Bubble = { body: BasePart, shine: BasePart, x: number, z: number, y: number, size: number, speed: number, phase: number, drift: number }
	local bubbles: { Bubble } = {}

	local function newBall(size: number, col: Color3, mat: Enum.Material, transparency: number): Part
		local p = Instance.new("Part")
		p.Shape = Enum.PartType.Ball
		p.Size = Vector3.new(size, size, size)
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		p.Material = mat
		p.Color = col
		p.Transparency = transparency
		p.Parent = folder
		return p
	end

	local function place(b: Bubble, fromGround: boolean)
		local a, r = rng:NextNumber(0, math.pi * 2), math.sqrt(rng:NextNumber()) * cfg.radius
		b.x, b.z = math.cos(a) * r, math.sin(a) * r
		b.y = fromGround and rng:NextNumber(1, 6) or rng:NextNumber(2, cfg.topY)
		b.size = rng:NextNumber(cfg.minSize, cfg.maxSize)
		b.speed = rng:NextNumber(cfg.riseSpeed[1], cfg.riseSpeed[2])
		b.phase = rng:NextNumber(0, math.pi * 2)
		b.drift = rng:NextNumber(0.5, 1.5)
		b.body.Size = Vector3.new(b.size, b.size, b.size)
		b.shine.Size = Vector3.one * b.size * 0.25
	end

	for _ = 1, cfg.count do
		local b = {
			body = newBall(1, Color3.fromRGB(200, 240, 255), Enum.Material.Glass, 0.45),
			shine = newBall(1, Color3.new(1, 1, 1), Enum.Material.SmoothPlastic, 0.1),
			x = 0, z = 0, y = 0, size = 1, speed = 1, phase = 0, drift = 1,
		}
		place(b, false)
		table.insert(bubbles, b)
	end

	-- a little pop at the top: the bubble swells and fades, then starts again at the bottom
	local function popAt(pos: Vector3, size: number)
		local p = newBall(size, Color3.fromRGB(220, 245, 255), Enum.Material.Glass, 0.45)
		p.Position = pos
		local tw = TweenService:Create(p, TweenInfo.new(0.25), { Size = Vector3.one * size * 1.6, Transparency = 1 })
		tw.Completed:Connect(function()
			p:Destroy()
		end)
		tw:Play()
	end

	local parts: { BasePart } = {}
	local cframes: { CFrame } = {}
	local t = 0
	RunService.Heartbeat:Connect(function(dt)
		local show = player:GetAttribute("InRun") ~= true
		folder.Parent = show and workspace or nil
		if not show then
			return
		end
		t += dt
		table.clear(parts)
		table.clear(cframes)
		for _, b in bubbles do
			b.y += b.speed * dt
			if b.y > cfg.topY then
				popAt(O + Vector3.new(b.x, b.y, b.z), b.size)
				place(b, true)
			end
			local wob = math.sin(t * b.drift + b.phase) * 1.5
			local pos = O + Vector3.new(b.x + wob, b.y, b.z + math.cos(t * b.drift * 0.8 + b.phase) * 1.5)
			table.insert(parts, b.body)
			table.insert(cframes, CFrame.new(pos))
			table.insert(parts, b.shine)
			table.insert(cframes, CFrame.new(pos + Vector3.new(-0.2, 0.22, 0.2) * b.size))
		end
		workspace:BulkMoveTo(parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
	end)
end

return HubBubbles
