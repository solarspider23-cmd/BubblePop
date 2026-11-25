-- Room layout and pop checks.
--   tools/bin/luau tests/pop_tests.luau

local RoomLayout = require("../src/ReplicatedStorage/Shared/Rules/RoomLayout")
local PopRules = require("../src/ReplicatedStorage/Shared/Rules/PopRules")
local Room = require("../src/ReplicatedStorage/Shared/Config/Room")
local Pop = require("../src/ReplicatedStorage/Shared/Config/Pop")

local passed, failed = 0, 0
local function test(name, fn)
	local ok, err = pcall(fn)
	if ok then
		passed += 1
	else
		failed += 1
		print("FAIL " .. name .. ": " .. tostring(err))
	end
end

local L = RoomLayout.new(Room)
local perSheet = Room.perSheet * Room.perSheet

test("bubble count matches floor (minus recycler) + 4 walls", function()
	local skipped = 0
	local clear = Room.recycler and Room.recycler.clear or 0
	for row = 0, Room.floorSheets - 1 do
		for col = 0, Room.floorSheets - 1 do
			local cx = -L.half + col * Room.sheetSize + Room.sheetSize / 2
			local cz = -L.half + row * Room.sheetSize + Room.sheetSize / 2
			if math.abs(cx) < clear / 2 and math.abs(cz) < clear / 2 then
				skipped += 1
			end
		end
	end
	local sheets = Room.floorSheets * Room.floorSheets - skipped + 4 * Room.floorSheets * Room.wallRows
	assert(#L.sheets == sheets, "sheets " .. #L.sheets)
	assert(#L.bubbles == sheets * perSheet, "bubbles " .. #L.bubbles)
end)

test("ids are 1..n in order", function()
	for i, b in L.bubbles do
		assert(b.id == i)
	end
end)

test("every bubble is inside the room and normals point inward", function()
	for _, b in L.bubbles do
		assert(math.abs(b.x) <= L.half + 1e-6 and math.abs(b.z) <= L.half + 1e-6, "outside sideways " .. b.id)
		assert(b.y >= L.floorY - 1e-6 and b.y <= L.floorY + L.height + 1e-6, "outside height " .. b.id)
		local len = math.sqrt(b.nx ^ 2 + b.ny ^ 2 + b.nz ^ 2)
		assert(math.abs(len - 1) < 1e-6)
		-- pointing toward the room's middle (or up for the floor)
		local inward = -(b.x * b.nx + b.z * b.nz) + b.ny
		assert(inward > 0, "normal points out " .. b.id)
	end
end)

test("no two bubbles in the same spot", function()
	local seen = {}
	for _, b in L.bubbles do
		local k = string.format("%.2f,%.2f,%.2f", b.x, b.y, b.z)
		assert(not seen[k], "duplicate at " .. k)
		seen[k] = true
	end
end)

test("bubbles along a wall are evenly spaced across sheet seams", function()
	local xs = {}
	for _, b in L.bubbles do
		if b.surface == "north" and math.abs(b.y - (Room.floorY + (Room.wallLift or 0) + 0.6)) < 1e-6 then
			table.insert(xs, b.x)
		end
	end
	table.sort(xs)
	assert(#xs == Room.floorSheets * Room.perSheet)
	for i = 2, #xs do
		assert(math.abs(xs[i] - xs[i - 1] - Room.spacing) < 1e-6, "gap at " .. i)
	end
end)

test("wall bubbles clear the floor bubbles at the corners", function()
	local floorTop = Room.floorY + Room.sheetThickness + Room.bubbleHeight
	for _, b in L.bubbles do
		if b.surface ~= "floor" then
			assert(b.y - Room.bubbleWidth / 2 > floorTop, "wall bubble " .. b.id .. " dips into the floor wrap")
		end
	end
end)

test("floorNear finds the bubble right underfoot and only floor bubbles", function()
	for _, b in L.bubbles do
		if b.surface == "floor" then
			local ids = L.floorNear(b.x, b.z, 0.1)
			assert(#ids == 1 and ids[1] == b.id, "missed " .. b.id)
		end
	end
	local ids = L.floorNear(0, L.half / 2, Pop.stompRadius)
	assert(#ids >= 2 and #ids <= 6, "near " .. #ids)
	assert(#L.floorNear(0, 0, 1) == 0, "no wrap under the recycler")
	for _, id in ids do
		assert(L.bubbles[id].surface == "floor")
	end
	assert(#L.floorNear(L.half + 10, 0, 1) == 0)
end)

test("validId refuses junk", function()
	local n = #L.bubbles
	assert(PopRules.validId(1, n) and PopRules.validId(n, n))
	for _, bad in { 0, n + 1, 1.5, -1, 0 / 0, math.huge, "3", nil, {} } do
		assert(not PopRules.validId(bad, n), tostring(bad))
	end
end)

test("clickOk checks distance and speed", function()
	assert(PopRules.clickOk(5, 1, Pop))
	assert(not PopRules.clickOk(Pop.reach + Pop.reachSlack + 0.1, 1, Pop))
	assert(not PopRules.clickOk(5, Pop.popTime - Pop.timeTolerance - 0.01, Pop))
	assert(PopRules.clickOk(5, Pop.popTime, Pop))
end)

test("stompOk checks sideways distance and height", function()
	assert(PopRules.stompOk(1, 3, Pop))
	assert(not PopRules.stompOk(Pop.stompRadius + Pop.stompSlack + 0.1, 3, Pop))
	assert(not PopRules.stompOk(1, 7, Pop))
end)

test("rate limiter caps bursts", function()
	local allow = PopRules.rateLimiter(10)
	local ok = 0
	for _ = 1, 50 do
		if allow(0) then
			ok += 1
		end
	end
	assert(ok == 10, "burst " .. ok)
	assert(allow(0.2)) -- refills over time
end)

print(string.format("pop_tests: %d passed, %d failed", passed, failed))
if failed > 0 then
	error("pop tests failed")
end
