-- Plastic scraps: what you collect. Each of your pops throws a little scrap of plastic into
-- your bag (it flies to the bag bar on screen); selling throws them out to the recycler.
-- Client-only effect; the server keeps the real bag.
local RunService = game:GetService("RunService")

local Hud = require(script.Parent.Hud)

local Scraps = {}

local PLASTIC = Color3.fromRGB(215, 235, 250)
local MAX_IN_BAG_FX = 30 -- colours remembered for the sell effect
local camera = workspace.CurrentCamera

type Flight = {
	part: BasePart,
	from: Vector3,
	lift: Vector3,
	target: () -> Vector3,
	t0: number,
	dur: number,
	spin: CFrame,
	size: Vector3,
	done: (() -> ())?,
}
local flights: { Flight } = {}
local inBag: { Color3 } = {} -- colours of the scraps in your bag (for the sell effect)
local lastToBag = 0

local folder = Instance.new("Folder")
folder.Name = "ScrapFx"
folder.Parent = workspace

local function newScrap(col: Color3): BasePart
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Color = col
	p.Transparency = 0.1
	-- a crumpled flake: a flat, slightly bent shard
	p.Size = Vector3.new(0.3 + math.random() * 0.15, 0.06, 0.22 + math.random() * 0.1)
	p.Parent = folder
	return p
end

local function fly(col: Color3, from: Vector3, lift: Vector3, target: () -> Vector3, dur: number, delay: number, done: (() -> ())?)
	local p = newScrap(col)
	p.Transparency = 1
	table.insert(flights, {
		part = p,
		from = from,
		lift = lift,
		target = target,
		t0 = os.clock() + delay,
		dur = dur,
		spin = CFrame.Angles(math.random() * 6, math.random() * 6, math.random() * 6),
		size = p.Size,
		done = done,
	})
end

RunService.RenderStepped:Connect(function()
	local now = os.clock()
	for i = #flights, 1, -1 do
		local f = flights[i]
		local a = (now - f.t0) / f.dur
		if a >= 1 then
			f.part:Destroy()
			table.remove(flights, i)
			if f.done then
				f.done()
			end
		elseif a >= 0 then
			-- curved path: up and over, speeding up at the end
			local e = a * a * (3 - 2 * a)
			local to = f.target()
			local mid = (f.from + to) / 2 + f.lift
			local p1 = f.from:Lerp(mid, e)
			local p2 = mid:Lerp(to, e)
			local pos = p1:Lerp(p2, e)
			f.part.Transparency = 0.1
			f.part.Size = f.size * (1 - 0.55 * a)
			f.part.CFrame = CFrame.new(pos) * CFrame.Angles(a * 9, a * 7, a * 5) * f.spin
		end
	end
end)

-- where the bag bar is, as a point just in front of the camera
local function bagPoint(): Vector3
	local sp = Hud.bagScreenPoint()
	local ray = camera:ViewportPointToRay(sp.X, sp.Y)
	return ray.Origin + ray.Direction * 2.2
end

-- one of your pops: a scrap flies from the bubble into your bag
function Scraps.toBag(at: Vector3, col: Color3?)
	local c = col or PLASTIC
	table.insert(inBag, c)
	if #inBag > MAX_IN_BAG_FX then
		table.remove(inBag, 1)
	end
	local now = os.clock()
	if now - lastToBag < 0.04 then
		return -- stomping pops many at once: a few scraps are enough
	end
	lastToBag = now
	fly(c, at, Vector3.new(0, 1.2, 0), bagPoint, 0.42, 0, Hud.bagBump)
end

-- selling: the scraps fly out of your bag into the recycler
function Scraps.toRecycler(n: number)
	local room = workspace:FindFirstChild("Room")
	local rec = room and room:FindFirstChild("Recycler") :: BasePart?
	if not rec then
		return
	end
	local count = math.clamp(n, 1, 25)
	local top = rec.Position + Vector3.new(0, rec.Size.Y / 2, 0)
	for i = 1, count do
		local c = inBag[(i - 1) % math.max(1, #inBag) + 1] or PLASTIC
		local from = bagPoint()
		local spot = top + Vector3.new((math.random() - 0.5) * rec.Size.X * 0.5, -0.5, (math.random() - 0.5) * rec.Size.Z * 0.5)
		fly(c, from, Vector3.new(0, 4 + math.random() * 2, 0), function()
			return spot
		end, 0.55, (i - 1) * 0.03)
	end
	table.clear(inBag)
end

return Scraps
