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
local Variants = require(Shared.Config.Variants)
local VariantRules = require(Shared.Rules.Variants)
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
local K = Room.bubbleScale or 1 -- room size setting: shrinks the bubble models
local INTACT_SIZE = intactTemplate and v3(Models.intact.size) * K or Vector3.new(W, H * 2, W)
local INTACT_CENTER = intactTemplate and v3(Models.intact.center) * K or Vector3.zero
BubbleView.height = intactTemplate and Models.intact.size[2] * K or H

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
local shines: { [number]: BasePart } = {}
local variantOf: { [number]: number } = {} -- rare bubbles (Config/Variants); missing = normal
local extras: { [number]: BasePart } = {} -- glow ring (+ sparkles) behind a rare bubble
local rainbowIds: { [number]: boolean } = {}

local function variantDef(id: number)
	local k = variantOf[id]
	return k and Variants.list[k] or nil
end
local applyLighting: () -> ()

-- which way is "up the bubble" for the shine spot: towards the sky on walls, a fixed corner on the floor
local shineDir: { [number]: Vector3 } = {}
for id, cf in frames do
	local up = cf:VectorToObjectSpace(Vector3.yAxis)
	local d = Vector3.new(up.X, 0, up.Z)
	shineDir[id] = d.Magnitude > 0.5 and d.Unit or Vector3.new(-0.7071, 0, -0.7071)
end

local function intactTransparency(id: number?): number
	local v = id and variantDef(id)
	if v then
		return v.transparency or 0
	end
	return look.plain and look.bubbleTransparency or Room.colors.bubbleTransparency
end

local function styleVariant(p: BasePart, id: number?)
	local v = id and variantDef(id)
	if not v then
		return
	end
	if p:IsA("MeshPart") then
		p.TextureID = ""
	end
	p.Color = color(v.color)
	p.Material = Enum.Material.Glass
	p.Reflectance = v.reflectance or 0.3
	p.CastShadow = false
end

local function styleIntact(p: BasePart, id: number?)
	if look.plain then
		if p:IsA("MeshPart") then
			p.TextureID = ""
		end
		p.Color = color(look.bubble)
		p.Material = Enum.Material[look.bubbleMaterial or "SmoothPlastic"]
		p.Reflectance = look.bubbleReflectance or 0
		p.CastShadow = look.shadows == true
	else
		p.CastShadow = false
		if p:IsA("MeshPart") and intactTemplate then
			p.TextureID = intactTemplate.TextureID
		end
		p.Color = BUBBLE_COLOR
		p.Material = Enum.Material.SmoothPlastic
		p.Reflectance = intactTemplate and 0 or 0.08
	end
	styleVariant(p, id)
end

-- Shape of an intact bubble: side = sideways scale, up = height scale (1, 1 = normal).
-- The bottom stays glued to the sheet.
local function setShape(id: number, side: number, up: number)
	local p = intact[id]
	local scale = Vector3.new(side, up, side)
	p.Size = INTACT_SIZE * scale
	p.CFrame = frames[id] * CFrame.new(INTACT_CENTER * scale)
	local sh = shines[id]
	if sh then
		local off = shineDir[id] * 0.27 * K * side
		sh.CFrame = frames[id] * CFrame.new(off.X, BubbleView.height * 0.84 * up, off.Z)
	end
end

local function newShine(id: number)
	local sh = Instance.new("Part")
	sh.Name = "Shine"
	sh.Anchored = true
	sh.CanCollide = false
	sh.CanQuery = false
	sh.CanTouch = false
	sh.CastShadow = false
	sh.Material = Enum.Material.Neon
	sh.Color = Color3.new(1, 1, 1)
	sh.Transparency = 0.15
	sh.Size = Vector3.new(0.2, 0.05, 0.2) * K
	local m = Instance.new("SpecialMesh")
	m.MeshType = Enum.MeshType.Sphere
	m.Parent = sh
	shines[id] = sh
end

-- Rare bubbles: a glowing ring on the sheet behind them, glitter, and (rainbow) changing colours
local function updateExtras(id: number)
	local v = variantDef(id)
	local want = v ~= nil and not isPopped[id]
	local ring = extras[id]
	if want and v then
		if not ring then
			ring = Instance.new("Part")
			ring.Name = "Glow"
			ring.Anchored = true
			ring.CanCollide = false
			ring.CanQuery = false
			ring.CanTouch = false
			ring.CastShadow = false
			ring.Material = Enum.Material.Neon
			ring.Shape = Enum.PartType.Cylinder
			local d = INTACT_SIZE.X * 1.22
			ring.Size = Vector3.new(0.02, d, d)
			ring.CFrame = frames[id] * CFrame.new(0, 0.015, 0) * CFrame.Angles(0, 0, math.pi / 2)
			local at = Instance.new("Attachment")
			at.Position = Vector3.new(BubbleView.height * 0.6, 0, 0) -- out from the sheet (ring's X = bubble's up)
			at.Parent = ring
			local e = Instance.new("ParticleEmitter")
			e.Name = "Sparkle"
			e.Texture = "rbxasset://textures/particles/sparkles_main.dds"
			e.Lifetime = NumberRange.new(0.4, 0.8)
			e.Speed = NumberRange.new(0.3, 0.8)
			e.SpreadAngle = Vector2.new(180, 180)
			e.LightEmission = 1
			e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.16 * K), NumberSequenceKeypoint.new(1, 0) })
			e.Parent = at
			extras[id] = ring
		end
		ring.Color = color(v.glow or v.color)
		ring.Transparency = 0.55
		local e = ring:FindFirstChild("Sparkle", true) :: ParticleEmitter
		e.Color = ColorSequence.new(color(v.sparkle or { 255, 255, 255 }))
		e.Rate = v.sparkleRate or 4
		rainbowIds[id] = v.rainbow == true or nil
		ring.Parent = folder
	elseif ring then
		ring.Parent = nil
		rainbowIds[id] = nil
	end
end

-- rainbow bubbles slowly cycle through every colour
game:GetService("RunService").Heartbeat:Connect(function()
	if next(rainbowIds) == nil then
		return
	end
	local hue = (os.clock() * 0.25) % 1
	for id in rainbowIds do
		local p = intact[id]
		if p and not isPopped[id] then
			local h = (hue + id * 0.013) % 1
			p.Color = Color3.fromHSV(h, 0.75, 1)
			local ring = extras[id]
			if ring then
				ring.Color = Color3.fromHSV((h + 0.5) % 1, 0.6, 1)
			end
		end
	end
end)

-- shine spots only on unpopped bubbles, and only in a look that has them
local function updateShine(id: number)
	local want = look.shine == true and not isPopped[id]
	if want and not shines[id] then
		newShine(id)
	end
	local sh = shines[id]
	if sh then
		sh.Parent = want and folder or nil
		if want then
			setShape(id, 1, 1)
		end
	end
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
	styleIntact(p, id)
	p.Transparency = intactTransparency(id)
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
		-- scrambled pick per bubble, so neighbours rarely match (fixed per id)
		local k = ((id * 2654435761) % 4294967296 // 7) % #poppedTemplates + 1
		local m = poppedTemplates[k]:Clone()
		m.Name = "Popped"
		m.CanQuery = false
		-- a little size and flatness variety per bubble (fixed per id)
		local r1, r2 = (id * 7919 % 101) / 100, (id * 104729 % 103) / 102
		m.Size = m.Size * K * Vector3.new(0.92 + 0.14 * r1, 0.7 + 0.6 * r2, 0.92 + 0.14 * r1)
		m:SetAttribute("Size", m.Size)
		m.CFrame = frames[id] * turn(id) * CFrame.new(v3(Models.popped[k].center) * K)
		m:SetAttribute("Texture", m.TextureID)
		m:SetAttribute("BaseColor", m.Color)
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
			tear.Size = Vector3.new(0.6, 0.03, 0.16) * K
			local m = Instance.new("SpecialMesh")
			m.MeshType = Enum.MeshType.Sphere
			m.Parent = tear
			tear.CFrame = frames[id] * turn(id) * CFrame.new(0, 0.1 * K, 0)
			tears[id] = tear
		end
		tear.Color = color(look.tear)
		tear.Parent = model.Parent
	else
		model.TextureID = model:GetAttribute("Texture") or ""
		model.Transparency = 0
		model.Color = model:GetAttribute("BaseColor") or model.Color
		if tears[id] then
			tears[id].Parent = nil
		end
	end
	-- a popped rare bubble keeps its colour, so you can see where it was
	local v = variantDef(id)
	if v then
		model.TextureID = ""
		model.Color = v.rainbow and Color3.fromHSV((id * 0.013) % 1, 0.6, 1) or color(v.color)
		model.Transparency = 0.15
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
	updateShine(id)
	updateExtras(id)
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
	local v = variantDef(id)
	if v then
		-- jackpot: a big burst in the bubble's colour, a chime and the coins it paid
		local c = v.rainbow and Color3.fromHSV(math.random(), 0.7, 1) or color(v.sparkle or v.color)
		bits.Color = ColorSequence.new(Color3.new(1, 1, 1), c)
		bits:Emit(kind == "other" and 10 or 30)
		bits.Color = ColorSequence.new(Color3.new(1, 1, 1), BUBBLE_COLOR)
		if kind ~= "other" then
			Sfx.play("rarePop")
			BubbleView.floatText(cf.Position, "+" .. VariantRules.coins(Variants, variantOf[id]), c, true)
		end
	else
		bits:Emit(kind == "other" and 4 or 9)
		if kind == "click" then
			BubbleView.floatText(cf.Position, "+" .. Variants.baseCoins, Color3.fromRGB(255, 225, 90), false)
		end
	end
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
	styleIntact(p, id)
	p.Transparency = intactTransparency(id)
	p.CanQuery = true
	updateShine(id)
	updateExtras(id)
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

-- Per-look lighting (this client only). The server's lighting is remembered as the default.
local Lighting = game:GetService("Lighting")
local defaults: { [string]: any }? = nil
local bloom = Instance.new("BloomEffect")
bloom.Name = "LookBloom"
bloom.Enabled = false
bloom.Threshold = 0.92
bloom.Size = 18
bloom.Parent = Lighting
applyLighting = function()
	local ceiling = workspace:FindFirstChild("Room") and workspace.Room:FindFirstChild("Ceiling") :: BasePart?
	if not defaults then
		defaults = {
			brightness = Lighting.Brightness,
			clockTime = Lighting.ClockTime,
			ambient = Lighting.Ambient,
			outdoor = Lighting.OutdoorAmbient,
			shadow = ceiling and ceiling.CastShadow,
		}
	end
	local d = defaults :: { [string]: any }
	local l = look.lighting or {}
	Lighting.Brightness = l.brightness or d.brightness
	Lighting.ClockTime = l.clockTime or d.clockTime
	Lighting.Ambient = l.ambient and color(l.ambient) or d.ambient
	Lighting.OutdoorAmbient = l.ambient and color(l.ambient) or d.outdoor
	bloom.Enabled = l.bloom ~= nil
	bloom.Intensity = l.bloom or 0
	if ceiling then
		-- let the sun shine in through the ceiling (it still looks solid)
		ceiling.CastShadow = if l.sunIn then false else d.shadow
	end
end

-- The glow on the bubble you're aiming at (one Highlight, moved around)
local aimGlow = Instance.new("Highlight")
aimGlow.Name = "AimGlow"
aimGlow.DepthMode = Enum.HighlightDepthMode.Occluded
local aimCfg = Room.aim or {}
aimGlow.FillColor = aimCfg.fill and color(aimCfg.fill) or Color3.new(1, 1, 1)
aimGlow.FillTransparency = aimCfg.fillTransparency or 0.7
aimGlow.OutlineColor = aimCfg.outline and color(aimCfg.outline) or Color3.new(1, 1, 1)
aimGlow.OutlineTransparency = aimCfg.outlineTransparency or 0.2
aimGlow.Enabled = false
aimGlow.Parent = folder
local aimedId: number? = nil
function BubbleView.setAim(id: number?)
	if id and isPopped[id] then
		id = nil
	end
	if id == aimedId then
		return
	end
	aimedId = id
	aimGlow.Adornee = id and intact[id] or nil
	aimGlow.Enabled = id ~= nil
end

-- Switch look: every bubble, popped bubble, sheet, wall and floor (this client only)
function BubbleView.setLook(index: number): string
	local looks = Room.looks or { { name = "Cartoon" } }
	look = looks[((index - 1) % #looks) + 1]
	for id, p in intact do
		styleIntact(p, id)
		if not isPopped[id] then
			p.Transparency = intactTransparency(id)
		end
	end
	for id, model in popped do
		if isPopped[id] then
			stylePopped(id, model)
		end
	end
	for id in intact do
		updateShine(id)
	end
	applyLighting()
	local room = workspace:FindFirstChild("Room")
	if room then
		local sheets = room:FindFirstChild("Sheets")
		if sheets then
			for _, sh in sheets:GetChildren() do
				if sh:IsA("BasePart") then
					sh.Color = color(look.sheet or Room.colors.sheet)
					sh.Transparency = look.sheetTransparency or 0
				end
			end
		end
		for _, name in { "WallN", "WallS", "WallW", "WallE" } do
			local w = room:FindFirstChild(name)
			if w and w:IsA("BasePart") then
				w.Color = color(look.wall or Room.colors.wall)
			end
		end
		for _, name in { "TrimN", "TrimS", "TrimW", "TrimE" } do
			local t = room:FindFirstChild(name)
			if t and t:IsA("BasePart") then
				t.Color = color(look.trim or look.wall or Room.colors.trim or Room.colors.wall)
			end
		end
		local floor = room:FindFirstChild("Floor")
		if floor and floor:IsA("BasePart") then
			floor.Color = color(look.floor or Room.colors.floor)
		end
	end
	return look.name
end

-- Make a bubble rare (k = Config/Variants index) or normal (k = 0)
function BubbleView.setVariant(id: number, k: number)
	if not intact[id] then
		return
	end
	local new = if Variants.list[k] then k else nil
	if variantOf[id] == new then
		return
	end
	variantOf[id] = new
	if not new then
		rainbowIds[id] = nil
	end
	if not isPopped[id] then
		local p = intact[id]
		styleIntact(p, id)
		p.Transparency = intactTransparency(id)
		updateExtras(id)
	end
end

-- "+5" floating up from a popped bubble (big = rare)
function BubbleView.floatText(at: Vector3, text: string, col: Color3, big: boolean)
	local anchor = Instance.new("Part")
	anchor.Anchored = true
	anchor.CanCollide = false
	anchor.CanQuery = false
	anchor.CanTouch = false
	anchor.Transparency = 1
	anchor.Size = Vector3.one * 0.1
	anchor.CFrame = CFrame.new(at)
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromScale(big and 3 or 1.4, big and 1.5 or 0.7)
	bb.AlwaysOnTop = true
	bb.LightInfluence = 0
	bb.Parent = anchor
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(1, 1)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.FredokaOne
	t.TextScaled = true
	t.Text = text
	t.TextColor3 = col
	local st = Instance.new("UIStroke")
	st.Thickness = big and 3 or 2
	st.Color = Color3.fromRGB(20, 30, 70)
	st.Parent = t
	t.Parent = bb
	anchor.Parent = workspace
	local rise = big and 2.2 or 1.2
	TweenService:Create(anchor, TweenInfo.new(big and 1.1 or 0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(at + Vector3.new(0, rise, 0)) }):Play()
	TweenService:Create(t, TweenInfo.new(big and 1.1 or 0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TextTransparency = 1 }):Play()
	TweenService:Create(st, TweenInfo.new(big and 1.1 or 0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 }):Play()
	game:GetService("Debris"):AddItem(anchor, big and 1.2 or 0.8)
end

-- Server sync: changes = { id (popped) or -id (grew back) }, kinds = variant per entry
function BubbleView.apply(changes: { number }, by: { number }, kinds: { number }?, myUserId: number)
	for i, c in changes do
		local k = kinds and kinds[i] or 0
		if c > 0 then
			if not isPopped[c] then
				BubbleView.setVariant(c, k)
				BubbleView.pop(c, by[i] == myUserId and "stomp" or "other")
			end
		else
			if isPopped[-c] then
				-- the variant is set as it grows back, so a new rare bubble appears
				variantOf[-c] = if Variants.list[k] then k else nil
				BubbleView.regrow(-c)
			else
				BubbleView.setVariant(-c, k)
			end
		end
	end
end

return BubbleView
