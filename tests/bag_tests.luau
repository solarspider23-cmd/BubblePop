-- Bag checks.
--   tools/bin/luau tests/bag_tests.luau

local BagRules = require("../src/ReplicatedStorage/Shared/Rules/Bag")
local Bag = require("../src/ReplicatedStorage/Shared/Config/Bag")

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

test("a new bag is empty and starts at 25", function()
	local b = BagRules.new()
	assert(b.count == 0 and b.value == 0)
	assert(Bag.startCapacity == 25)
end)

test("bubbles fill the bag until it's full, then nothing more goes in", function()
	local b = BagRules.new()
	for i = 1, 25 do
		assert(BagRules.add(b, 1, 25), "add " .. i)
	end
	assert(BagRules.full(b, 25))
	assert(not BagRules.add(b, 100, 25))
	assert(b.count == 25 and b.value == 25)
end)

test("rare bubbles add their value but take one slot", function()
	local b = BagRules.new()
	BagRules.add(b, 1, 25)
	BagRules.add(b, 5, 25)
	BagRules.add(b, 100, 25)
	assert(b.count == 3 and b.value == 106)
end)

test("selling pays the value and empties the bag; selling twice pays nothing", function()
	local b = BagRules.new()
	BagRules.add(b, 5, 25)
	BagRules.add(b, 1, 25)
	assert(BagRules.sell(b) == 6)
	assert(b.count == 0 and b.value == 0)
	assert(BagRules.sell(b) == 0)
end)

test("negative values are refused", function()
	local b = BagRules.new()
	assert(not BagRules.add(b, -5, 25))
	assert(b.count == 0)
end)

test("near the recycler", function()
	assert(BagRules.nearRecycler(0, 7, 0, 0, 10, 10, 3))
	assert(BagRules.nearRecycler(-8, 0, 0, 0, 10, 10, 3))
	assert(not BagRules.nearRecycler(0, 8.5, 0, 0, 10, 10, 3))
	assert(not BagRules.nearRecycler(9, 9, 0, 0, 10, 10, 3))
end)

print(("bag_tests: %d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("bag tests failed")
end
