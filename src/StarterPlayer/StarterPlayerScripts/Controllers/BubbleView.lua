-- Draws every bubble on this client and plays the press / pop / grow-back animations.
-- The server only sends which bubbles are popped; the look lives here.
-- Placeholder shapes for now (squashed spheres); the Blender meshes slot in later.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Room = require(Shared.Config.Room)
local Pop = require(Shared.Config.Pop)
local RoomLayout = require(Shared.Rules.RoomLayout)
local Sfx = require(script.Parent.Sfx)

local BubbleView = {}

local layout = RoomLayout.new(Room)
BubbleView.layout = layout
local bubbles = layout.bubbles

local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local BUBBLE_COLOR = color(Room.colors.bubble)
local POPPED_COLOR = color(Room.colors.popped)
local TEAR_COLOR = color(Room.colors.tear)
local W, H, PH = Room.bubbleWidth, Room.bubbleHeight, Room.poppedHeight

local folder = Instance.new("Folder")
folder.Name = "Bubbles"
BubbleView.folder = folder

local intact: { [number]: BasePart } = {}
local meshes: { [number]: SpecialMesh } = {}
local popped: { [number]: Model } = {}
local isPopped: { [number]: boolean } = {}
local frames: { [number]: CFrame } = {}

-- base frame: position on the sheet, Y axis = out of the sheet
for _, b in bubbles do
	frames[b.id] = CFrame.fromMatrix(Vector3.new(b.x, b.y, b.z), Vector3.new(b.rx, b.ry, b.rz), Vector3.new(b.nx, b.ny, b.nz))
end

local function newIntact(id: number)
	local p = Instance.new("Part")
	p.Name = "Bubble"
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = true
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = BUBBLE_COLOR
	p.Transparency = Room.colors.bubbleTransparency
	p.Reflectance = 0.08
	-- a sphere centred on the sheet: the half sticking out is the dome
	p.Size = Vector3.new(W, H * 2, W)
	p.CFrame = frames[id]
	local m = Instance.new("SpecialMesh")
	m.MeshType = Enum.MeshType.Sphere
	m.Parent = p
	p:SetAttribute("Id", id)
	p.Parent = folder
	intact[id] = p
	meshes[id] = m
end

local function newPopped(id: number): Model
	local model = Instance.new("Model")
	model.Name = "Popped"
	local cf = frames[id]
	local disc = Instance.new("Part")
	disc.Name = "Disc"
	disc.Anchored = true
	disc.CanCollide = false
	disc.CanTouch = false
	disc.CanQuery = false
	disc.CastShadow = false
	disc.Material = Enum.Material.SmoothPlastic
	disc.Color = POPPED_COLOR
	disc.Size = Vector3.new(W * 1.06, PH * 2, W * 1.06)
	disc.CFrame = cf
	local dm = Instance.new("SpecialMesh")
	dm.MeshType = Enum.MeshType.Sphere
	dm.Parent = disc
	disc.Parent = model
	-- the dark tear, turned a random way so the wall doesn't look copy-pasted
	local tear = disc:Clone()
	tear.Name = "Tear"
	tear.Color = TEAR_COLOR
	tear.Size = Vector3.new(0.62, 0.06, 0.2)
	tear.CFrame = cf * CFrame.Angles(0, (id * 2.399) % math.pi, 0) * CFrame.new(0, PH * 0.75, 0)
	tear.Parent = model
	model.Parent = folder
	return model
end

function BubbleView.build()
	for _, b in bubbles do
		newIntact(b.id)
	end
	folder.Parent = workspace
end

function BubbleView.isIntact(id: number): boolean
	return intact[id] ~= nil and not isPopped[id]
end

function BubbleView.idOf(part: Instance?): number?
	local id = part and part:GetAttribute("Id")
	return type(id) == "number" and id or nil
end

function BubbleView.frame(id: number): CFrame
	return frames[id]
end

-- During a press: squash 0 = full bubble, 1 = fully pressed. wobble adds a jiggle.
function BubbleView.setSquash(id: number, s: number, wobble: number)
	local m = meshes[id]
	if not m or isPopped[id] then
		return
	end
	local y = 1 - (1 - Pop.squashHeight) * s
	local side = 1 + (Pop.squashBulge - 1) * s + wobble
	m.Scale = Vector3.new(side, y, side)
end

-- Burst particles (one emitter, moved to each pop)
local fxPart = Instance.new("Part")
fxPart.Name = "PopFx"
fxPart.Anchored = true
fxPart.CanCollide = false
fxPart.CanQuery = false
fxPart.CanTouch = false
fxPart.Transparency = 1
fxPart.Size = Vector3.one
local fxAt = Instance.new("Attachment")
fxAt.Parent = fxPart
local bits = Instance.new("ParticleEmitter")
bits.Texture = "rbxasset://textures/particles/sparkles_main.dds"
bits.Enabled = false
bits.Lifetime = NumberRange.new(0.2, 0.4)
bits.Speed = NumberRange.new(6, 11)
bits.SpreadAngle = Vector2.new(75, 75)
bits.Drag = 8
bits.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
bits.Color = ColorSequence.new(Color3.new(1, 1, 1), BUBBLE_COLOR)
bits.LightEmission = 0.6
bits.EmissionDirection = Enum.NormalId.Top
bits.Parent = fxAt
local puff = Instance.new("ParticleEmitter")
puff.Texture = "rbxasset://textures/particles/smoke_main.dds"
puff.Enabled = false
puff.Lifetime = NumberRange.new(0.15, 0.25)
puff.Speed = NumberRange.new(1.5, 3)
puff.SpreadAngle = Vector2.new(60, 60)
puff.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 1.2) })
puff.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1) })
puff.Color = ColorSequence.new(Color3.new(1, 1, 1))
puff.EmissionDirection = Enum.NormalId.Top
puff.Parent = fxAt
fxPart.Parent = workspace

local POP_TWEEN = TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out)

-- kind: "click" (your tool), "stomp" (your feet), "other" (someone else), "quiet" (joining, no fx)
function BubbleView.pop(id: number, kind: string)
	if isPopped[id] or not intact[id] then
		return
	end
	isPopped[id] = true
	local p = intact[id]
	p.Transparency = 1
	p.CanQuery = false
	meshes[id].Scale = Vector3.one
	local model = popped[id] or newPopped(id)
	popped[id] = model
	model.Parent = folder
	if kind == "quiet" then
		return
	end
	-- punch: the popped plastic splats out a bit bigger, then settles
	local disc = model:FindFirstChild("Disc") :: BasePart
	local mesh = disc:FindFirstChildOfClass("SpecialMesh") :: SpecialMesh
	mesh.Scale = Vector3.new(1.35, 2.2, 1.35)
	TweenService:Create(mesh, POP_TWEEN, { Scale = Vector3.one }):Play()
	local cf = frames[id] * CFrame.new(0, H * 0.4, 0)
	fxAt.WorldCFrame = cf
	local n = kind == "other" and 4 or 9
	bits:Emit(n)
	puff:Emit(kind == "other" and 1 or 2)
	if kind == "click" then
		Sfx.play("pop")
	elseif kind == "stomp" then
		Sfx.play("stompPop")
	else
		Sfx.play("otherPop", cf.Position)
	end
end

local GROW_TWEEN = TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out)

function BubbleView.regrow(id: number)
	if not isPopped[id] then
		return
	end
	isPopped[id] = nil
	local model = popped[id]
	if model then
		model.Parent = nil
	end
	local p, m = intact[id], meshes[id]
	p.Transparency = Room.colors.bubbleTransparency
	p.CanQuery = true
	m.Scale = Vector3.new(0.2, 0.05, 0.2)
	TweenService:Create(m, GROW_TWEEN, { Scale = Vector3.one }):Play()
end

-- Server sync: changes = { id (popped) or -id (grew back) }
function BubbleView.apply(changes: { number }, by: { number }, myUserId: number)
	for i, c in changes do
		if c > 0 then
			if not isPopped[c] then
				BubbleView.pop(c, by[i] == myUserId and "stomp" or "other")
			end
		else
			BubbleView.regrow(-c)
		end
	end
end

return BubbleView
