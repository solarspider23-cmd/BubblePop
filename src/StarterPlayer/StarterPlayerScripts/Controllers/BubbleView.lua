-- Draws every bubble on this client and plays the press / pop / grow-back animations.
-- The server only sends which bubbles are popped; the look lives here.
-- Uses the uploaded Blender meshes (ReplicatedStorage.BubbleAssets, loaded by the server);
-- if they're missing it falls back to placeholder squashed spheres.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Room = require(Shared.Config.Room)
local Pop = require(Shared.Config.Pop)
local Models = require(Shared.Config.Models)
local RoomLayout = require(Shared.Rules.RoomLayout)
local Sfx = require(script.Parent.Sfx)

local BubbleView = {}

local layout = RoomLayout.new(Room)
BubbleView.layout = layout
local bubbles = layout.bubbles

local function color(c)
	return Color3.fromRGB(c[1], c[2], c[3])
end
local function v3(t)
	return Vector3.new(t[1], t[2], t[3])
end
local BUBBLE_COLOR = color(Room.colors.bubble)
local POPPED_COLOR = color(Room.colors.popped)
local TEAR_COLOR = color(Room.colors.tear)
local W, H, PH = Room.bubbleWidth, Room.bubbleHeight, Room.poppedHeight

-- Real meshes, if the server managed to load them
local assets = ReplicatedStorage:WaitForChild("BubbleAssets", 15)
local intactTemplate: MeshPart? = assets and assets:FindFirstChild("Intact") :: MeshPart?
local poppedTemplates: { MeshPart } = {}
if assets then
	for i = 1, #(Models.popped or {}) do
		local t = assets:FindFirstChild("Popped" .. i)
		if t then
			table.insert(poppedTemplates, t :: MeshPart)
		end
	end
end
local INTACT_SIZE = intactTemplate and v3(Models.intact.size) or Vector3.new(W, H * 2, W)
local INTACT_CENTER = intactTemplate and v3(Models.intact.center) or Vector3.zero
BubbleView.height = intactTemplate and Models.intact.size[2] or H

local folder = Instance.new("Folder")
folder.Name = "Bubbles"
BubbleView.folder = folder

local intact: { [number]: BasePart } = {}
local popped: { [number]: Instance } = {}
local isPopped: { [number]: boolean } = {}
local frames: { [number]: CFrame } = {}

-- base frame: position on the sheet, Y axis = out of the sheet
for _, b in bubbles do
	frames[b.id] = CFrame.fromMatrix(Vector3.new(b.x, b.y, b.z), Vector3.new(b.rx, b.ry, b.rz), Vector3.new(b.nx, b.ny, b.nz))
end

-- Current look (Room.looks; press L in game to switch)
local look = Room.looks and Room.looks[1] or { name = "Cartoon" }
local tears: { [number]: BasePart } = {}

local function intactTransparency(): number
	return look.plain and look.bubbleTransparency or Room.colors.bubbleTransparency
end

local function styleIntact(p: BasePart)
	if look.plain then
		if p:IsA("MeshPart") then
			p.TextureID = ""
		end
		p.Color = color(look.bubble)
		p.Material = Enum.Material[look.bubbleMaterial or "SmoothPlastic"]
		p.Reflectance = look.bubbleReflectance or 0
	else
		if p:IsA("MeshPart") and intactTemplate then
			p.TextureID = intactTemplate.TextureID
		end
		p.Color = BUBBLE_COLOR
		p.Material = Enum.Material.SmoothPlastic
		p.Reflectance = intactTemplate and 0 or 0.08
	end
end

-- Shape of an intact bubble: side = sideways scale, up = height scale (1, 1 = normal).
-- The bottom stays glued to the sheet.
local function setShape(id: number, side: number, up: number)
	local p = intact[id]
	local scale = Vector3.new(side, up, side)
	p.Size = INTACT_SIZE * scale
	p.CFrame = frames[id] * CFrame.new(INTACT_CENTER * scale)
end

local function newIntact(id: number)
	local p: BasePart
	if intactTemplate then
		p = intactTemplate:Clone()
	else
		p = Instance.new("Part")
		p.Material = Enum.Material.SmoothPlastic
		p.Color = BUBBLE_COLOR
		p.Reflectance = 0.08
		-- a sphere centred on the sheet: the half sticking out is the dome
		local m = Instance.new("SpecialMesh")
		m.MeshType = Enum.MeshType.Sphere
		m.Parent = p
	end
	p.Name = "Bubble"
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = true
	p.CastShadow = false
	styleIntact(p)
	p.Transparency = intactTransparency()
	p:SetAttribute("Id", id)
	intact[id] = p
	setShape(id, 1, 1)
	p.Parent = folder
end

-- a random-looking but fixed turn per bubble, so the wall doesn't look copy-pasted
local function turn(id: number): CFrame
	return CFrame.Angles(0, (id * 2.399) % (math.pi * 2), 0)
end

local function newPopped(id: number): Instance
	if #poppedTemplates > 0 then
		local k = (id % #poppedTemplates) + 1
		local m = poppedTemplates[k]:Clone()
		m.Name = "Popped"
		m.CanQuery = false
		-- a little size and flatness variety per bubble (fixed per id)
		local r1, r2 = (id * 7919 % 101) / 100, (id * 104729 % 103) / 102
		m.Size = m.Size * Vector3.new(0.92 + 0.14 * r1, 0.7 + 0.6 * r2, 0.92 + 0.14 * r1)
		m:SetAttribute("Size", m.Size)
		m.CFrame = frames[id] * turn(id) * CFrame.new(v3(Models.popped[k].center))
		m:SetAttribute("Texture", m.TextureID)
		m.Parent = folder
		return m
	end
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
	local tear = disc:Clone()
	tear.Name = "Tear"
	tear.Color = TEAR_COLOR
	tear.Size = Vector3.new(0.62, 0.06, 0.2)
	tear.CFrame = cf * turn(id) * CFrame.new(0, PH * 0.75, 0)
	tear.Parent = model
	model.Parent = folder
	return model
end

-- Paint a popped bubble for the current look (the plain look adds a grey tear on top)
local function stylePopped(id: number, model: Instance)
	if not model:IsA("MeshPart") then
		return
	end
	if look.plain then
		model.TextureID = ""
		model.Color = color(look.popped)
		model.Transparency = look.poppedTransparency or 0
		local tear = tears[id]
		if not tear then
			tear = Instance.new("Part")
			tear.Name = "Tear"
			tear.Anchored = true
			tear.CanCollide = false
			tear.CanQuery = false
			tear.CanTouch = false
			tear.CastShadow = false
			tear.Material = Enum.Material.SmoothPlastic
			tear.Size = Vector3.new(0.6, 0.03, 0.16)
			local m = Instance.new("SpecialMesh")
			m.MeshType = Enum.MeshType.Sphere
			m.Parent = tear
			tear.CFrame = frames[id] * turn(id) * CFrame.new(0, 0.1, 0)
			tears[id] = tear
		end
		tear.Color = color(look.tear)
		tear.Parent = model.Parent
	else
		model.TextureID = model:GetAttribute("Texture") or ""
		model.Transparency = 0
		if tears[id] then
			tears[id].Parent = nil
		end
	end
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
	if not intact[id] or isPopped[id] then
		return
	end
	local up = 1 - (1 - Pop.squashHeight) * s
	local side = 1 + (Pop.squashBulge - 1) * s + wobble
	setShape(id, side, up)
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

-- punch: the popped plastic splats out a bit bigger, then settles
local function punch(model: Instance)
	if model:IsA("MeshPart") then
		local size = model:GetAttribute("Size") :: Vector3
		model.Size = size * Vector3.new(1.3, 2.2, 1.3)
		TweenService:Create(model, POP_TWEEN, { Size = size }):Play()
	else
		local disc = model:FindFirstChild("Disc") :: BasePart
		local mesh = disc:FindFirstChildOfClass("SpecialMesh") :: SpecialMesh
		mesh.Scale = Vector3.new(1.35, 2.2, 1.35)
		TweenService:Create(mesh, POP_TWEEN, { Scale = Vector3.one }):Play()
	end
end

-- kind: "click" (your tool), "stomp" (your feet), "other" (someone else), "quiet" (joining, no fx)
function BubbleView.pop(id: number, kind: string)
	if isPopped[id] or not intact[id] then
		return
	end
	isPopped[id] = true
	local p = intact[id]
	p.Transparency = 1
	p.CanQuery = false
	setShape(id, 1, 1)
	local model = popped[id] or newPopped(id)
	popped[id] = model
	model.Parent = folder
	stylePopped(id, model)
	if kind == "quiet" then
		return
	end
	punch(model)
	local cf = frames[id] * CFrame.new(0, BubbleView.height * 0.4, 0)
	fxAt.WorldCFrame = cf
	bits:Emit(kind == "other" and 4 or 9)
	puff:Emit(kind == "other" and 1 or 2)
	if kind == "click" then
		Sfx.play("pop")
	elseif kind == "stomp" then
		Sfx.play("stompPop")
	else
		Sfx.play("otherPop", cf.Position)
	end
end

local GROW_TIME = 0.35

-- grow back: the dome swells from flat with a little overshoot
function BubbleView.regrow(id: number)
	if not isPopped[id] then
		return
	end
	isPopped[id] = nil
	local model = popped[id]
	if model then
		model.Parent = nil
	end
	if tears[id] then
		tears[id].Parent = nil
	end
	local p = intact[id]
	p.Transparency = intactTransparency()
	p.CanQuery = true
	local t0 = os.clock()
	local conn
	conn = game:GetService("RunService").Heartbeat:Connect(function()
		local a = math.clamp((os.clock() - t0) / GROW_TIME, 0, 1)
		if isPopped[id] then
			conn:Disconnect()
			return
		end
		local e = TweenService:GetValue(a, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
		setShape(id, 0.2 + 0.8 * e, 0.05 + 0.95 * e)
		if a >= 1 then
			conn:Disconnect()
		end
	end)
end

-- Switch look: every bubble, popped bubble, sheet, wall and floor (this client only)
function BubbleView.setLook(index: number): string
	local looks = Room.looks or { { name = "Cartoon" } }
	look = looks[((index - 1) % #looks) + 1]
	for id, p in intact do
		styleIntact(p)
		if not isPopped[id] then
			p.Transparency = intactTransparency()
		end
	end
	for id, model in popped do
		if isPopped[id] then
			stylePopped(id, model)
		end
	end
	local room = workspace:FindFirstChild("Room")
	if room then
		local sheets = room:FindFirstChild("Sheets")
		if sheets then
			for _, sh in sheets:GetChildren() do
				if sh:IsA("BasePart") then
					sh.Color = color(look.plain and look.sheet or Room.colors.sheet)
					sh.Transparency = look.plain and (look.sheetTransparency or 0) or 0
				end
			end
		end
		for _, name in { "WallN", "WallS", "WallW", "WallE" } do
			local w = room:FindFirstChild(name)
			if w and w:IsA("BasePart") then
				w.Color = color(look.plain and look.wall or Room.colors.wall)
			end
		end
		local floor = room:FindFirstChild("Floor")
		if floor and floor:IsA("BasePart") then
			floor.Color = color(look.plain and look.floor or Room.colors.floor)
		end
	end
	return look.name
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
