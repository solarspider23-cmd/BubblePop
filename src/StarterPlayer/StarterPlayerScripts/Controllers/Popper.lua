-- The poking stick (first-person view model) and click popping.
-- Hold to poke: the stick shoots out to the bubble under the crosshair, squeezes it for
-- Pop.popTime seconds, then POP and the stick snaps back. Holding keeps popping.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Pop = require(Shared.Config.Pop)
local Room = require(Shared.Config.Room)
local BubbleView = require(script.Parent.BubbleView)
local Hud = require(script.Parent.Hud)
local Sfx = require(script.Parent.Sfx)

local Popper = {}

local player = Players.LocalPlayer
local H = Room.bubbleHeight

local GRIP_OFFSET = Vector3.new(0.95, -0.85, -1.5) -- where the hand holds it, from the camera
local REST_AIM = Vector3.new(0.05, -0.3, -10) -- the stick points at this spot while resting
local GRIP_LEN = 0.9
local REST_STICK = 1.7
local RETRACT_TIME = 0.14

local function part(name: string, size: Vector3, col: Color3, shape: Enum.MeshType?): BasePart
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = col
	p.Size = size
	if shape then
		local m = Instance.new("SpecialMesh")
		m.MeshType = shape
		m.Parent = p
	end
	return p
end

local function easeOut(x: number)
	return 1 - (1 - x) * (1 - x)
end
local function easeIn(x: number)
	return x * x
end

function Popper.start(remotes: Folder)
	local PopRequest = remotes:WaitForChild("PopRequest") :: RemoteEvent
	local camera = workspace.CurrentCamera

	local model = Instance.new("Model")
	model.Name = "PopperViewModel"
	local grip = part("Grip", Vector3.new(0.3, 0.3, GRIP_LEN), Color3.fromRGB(255, 200, 30))
	local stick = part("Stick", Vector3.new(0.09, 0.09, REST_STICK), Color3.fromRGB(205, 160, 105))
	local tip = part("Tip", Vector3.new(0.18, 0.18, 0.18), Color3.fromRGB(255, 70, 90), Enum.MeshType.Sphere)
	grip.Parent, stick.Parent, tip.Parent = model, model, model
	model.Parent = camera

	local raycast = RaycastParams.new()
	raycast.FilterType = Enum.RaycastFilterType.Include
	raycast.FilterDescendantsInstances = { BubbleView.folder }

	local holding = 0 -- number of inputs holding "poke" down
	local press: { id: number, t0: number, creaked: boolean }? = nil
	local retract: { t0: number, from: Vector3 }? = nil
	local kick = 0 -- recoil, decays to 0
	local baseFov = camera.FieldOfView

	local function isPokeInput(input: InputObject)
		return input.UserInputType == Enum.UserInputType.MouseButton1
			or input.KeyCode == Enum.KeyCode.ButtonR2
	end
	UserInputService.InputBegan:Connect(function(input, processed)
		if not processed and isPokeInput(input) then
			holding += 1
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if isPokeInput(input) then
			holding = math.max(0, holding - 1)
		end
	end)
	if Hud.popButton then
		Hud.popButton.MouseButton1Down:Connect(function()
			holding += 1
		end)
		Hud.popButton.MouseButton1Up:Connect(function()
			holding = math.max(0, holding - 1)
		end)
		Hud.popButton.MouseLeave:Connect(function()
			holding = 0
		end)
	end

	local function aimed(): number?
		local cf = camera.CFrame
		-- a fat ray, so aiming at the gap between two bubbles still picks one
		local hit = workspace:Spherecast(cf.Position, Pop.aimRadius, cf.LookVector * Pop.reach, raycast)
		local id = hit and BubbleView.idOf(hit.Instance)
		if id and BubbleView.isIntact(id) then
			return id
		end
		return nil
	end

	-- top of the bubble's dome right now (follows the squash)
	local function domeTop(id: number, squash: number): Vector3
		local y = H * (1 - (1 - Pop.squashHeight) * squash)
		return (BubbleView.frame(id) * CFrame.new(0, y, 0)).Position
	end

	local function finishPress(id: number, at: Vector3)
		press = nil
		retract = { t0 = os.clock(), from = at }
		kick = 1
		BubbleView.pop(id, "click")
		PopRequest:FireServer(id)
		Hud.kick()
		camera.FieldOfView = baseFov - 1.5
		TweenService:Create(camera, TweenInfo.new(0.15, Enum.EasingStyle.Quad), { FieldOfView = baseFov }):Play()
	end

	local bobT = 0
	RunService.RenderStepped:Connect(function(dt)
		local now = os.clock()
		local cf = camera.CFrame

		-- walking bob
		local char = player.Character
		local hum = char and char:FindFirstChildOfClass("Humanoid")
		local moving = hum and hum.MoveDirection.Magnitude > 0.1
		if moving then
			bobT += dt * 9
		end
		local bob = moving and Vector3.new(math.sin(bobT) * 0.04, math.abs(math.cos(bobT)) * 0.05, 0) or Vector3.zero
		kick = math.max(0, kick - dt * 7)

		local gripPos = cf:PointToWorldSpace(GRIP_OFFSET + bob + Vector3.new(0, 0, kick * 0.25))
		local restDir = (cf:PointToWorldSpace(REST_AIM) - gripPos).Unit
		local restTip = gripPos + restDir * (GRIP_LEN / 2 + REST_STICK)

		-- start a new press when holding and aiming at a bubble
		local target = (not press) and aimed() or nil
		Hud.setAim(target ~= nil or press ~= nil)
		if not press and holding > 0 and target and (not retract or now - retract.t0 > RETRACT_TIME * 0.5) then
			press = { id = target, t0 = now, creaked = false }
			retract = nil
		end

		local tipPos = restTip
		if press then
			local id = press.id
			if not BubbleView.isIntact(id) then
				-- someone else popped it first
				retract = { t0 = now, from = tip.Position }
				press = nil
			else
				local u = (now - press.t0) / Pop.popTime
				local rp = Pop.reachPhase
				if u < rp then
					tipPos = restTip:Lerp(domeTop(id, 0), easeOut(u / rp))
				elseif u < 1 then
					if not press.creaked then
						press.creaked = true
						Sfx.play("press")
					end
					local s = easeIn((u - rp) / (1 - rp))
					local wobble = math.sin(u * 48) * 0.035 * s
					BubbleView.setSquash(id, s, wobble)
					tipPos = domeTop(id, s)
				else
					tipPos = domeTop(id, 1)
					finishPress(id, tipPos)
				end
			end
		elseif retract then
			local a = math.clamp((now - retract.t0) / RETRACT_TIME, 0, 1)
			tipPos = retract.from:Lerp(restTip, easeOut(a))
			if a >= 1 then
				retract = nil
			end
		end

		-- place the stick from the grip to the tip
		local dir = (tipPos - gripPos)
		if dir.Magnitude < 0.01 then
			dir = restDir
		end
		local unit = dir.Unit
		grip.CFrame = CFrame.lookAt(gripPos, gripPos + unit)
		local front = gripPos + unit * (GRIP_LEN / 2)
		local len = math.max(0.1, (tipPos - front).Magnitude)
		stick.Size = Vector3.new(0.09, 0.09, len)
		stick.CFrame = CFrame.lookAt((front + tipPos) / 2, tipPos)
		tip.CFrame = CFrame.new(tipPos)
	end)
end

return Popper
