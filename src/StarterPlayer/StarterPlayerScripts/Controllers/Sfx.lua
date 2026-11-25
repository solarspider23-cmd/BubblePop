-- Plays sounds from Config/Sounds with a little random pitch so repeats never sound identical.
local SoundService = game:GetService("SoundService")
local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Sounds = require(ReplicatedStorage.Shared.Config.Sounds)

local Sfx = {}

local holder: BasePart? = nil
local lastPlayed: { [string]: number } = {}

local lastTake: { [string]: number } = {}

local function source(def, key: string): string
	-- several takes: pick a random one, never the same twice in a row
	if def.ids and #def.ids > 0 then
		local n = #def.ids
		local k = math.random(n)
		if n > 1 and k == lastTake[key] then
			k = k % n + 1
		end
		lastTake[key] = k
		return "rbxassetid://" .. def.ids[k]
	end
	if def.id and def.id ~= 0 then
		return "rbxassetid://" .. def.id
	end
	return def.file or ""
end

-- Sound picker (test room): replace a sound's id/pitch while playing
local overrides: { [string]: any } = {}
function Sfx.override(key: string, def)
	local base = Sounds[key]
	overrides[key] = setmetatable({ id = def.id or 0, ids = def.ids or false, pitch = def.pitch }, { __index = base })
end

-- play(key) = 2D (your own pops); play(key, position) = 3D at that spot (other players' pops)
function Sfx.play(key: string, position: Vector3?)
	local def = overrides[key] or Sounds[key]
	if not def then
		return
	end
	local id = source(def, key)
	if id == "" then
		return
	end
	local now = os.clock()
	if def.gap and now - (lastPlayed[key] or -math.huge) < def.gap then
		return -- many at once (stomping): one sound is enough
	end
	lastPlayed[key] = now
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Volume = def.volume or 0.5
	s.PlaybackSpeed = (def.pitch or 1) * (1 + (math.random() * 2 - 1) * (def.pitchVar or 0))
	if position then
		if not holder then
			local h = Instance.new("Part")
			h.Name = "SfxHolder"
			h.Anchored = true
			h.CanCollide = false
			h.CanQuery = false
			h.CanTouch = false
			h.Transparency = 1
			h.Size = Vector3.one
			h.Parent = workspace
			holder = h
		end
		local a = Instance.new("Attachment")
		a.WorldPosition = position
		a.Parent = holder
		s.RollOffMaxDistance = def.range or 60
		s.Parent = a
		Debris:AddItem(a, 3)
	else
		s.Parent = SoundService
		Debris:AddItem(s, 3)
	end
	s:Play()
end

return Sfx
