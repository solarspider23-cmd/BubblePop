-- Upgrade checks.
--   tools/bin/luau tests/upgrade_tests.luau

local UpgradeRules = require("../src/ReplicatedStorage/Shared/Rules/Upgrades")
local Upgrades = require("../src/ReplicatedStorage/Shared/Config/Upgrades")
local Bag = require("../src/ReplicatedStorage/Shared/Config/Bag")
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

test("every upgrade has matching lists, free level 1, rising prices", function()
	for _, kind in Upgrades.order do
		local u = Upgrades[kind]
		assert(#u.values == #u.costs and #u.values >= 2, kind)
		assert(u.costs[1] == 0, kind .. " level 1 must be free")
		for i = 3, #u.costs do
			assert(u.costs[i] > u.costs[i - 1], kind .. " cost " .. i)
		end
	end
end)

test("level 1 matches the starting game", function()
	assert(Upgrades.bag.values[1] == Bag.startCapacity)
	assert(Upgrades.popSpeed.values[1] == Pop.popTime)
	assert(Upgrades.boots.values[1] == 0, "no boots: walking doesn't pop")
	assert(Upgrades.tool.values[1] == 1, "the starting stick pops one bubble")
end)

test("upgrades always get better", function()
	for i = 2, #Upgrades.bag.values do
		assert(Upgrades.bag.values[i] > Upgrades.bag.values[i - 1])
	end
	for i = 2, #Upgrades.popSpeed.values do
		assert(Upgrades.popSpeed.values[i] < Upgrades.popSpeed.values[i - 1])
	end
	for i = 2, #Upgrades.tool.values do
		assert(Upgrades.tool.values[i] > Upgrades.tool.values[i - 1])
	end
	for i = 2, #Upgrades.boots.values do
		assert(Upgrades.boots.values[i] > Upgrades.boots.values[i - 1])
	end
end)

test("first bag upgrade is cheap (about one bag's worth)", function()
	assert(Upgrades.bag.costs[2] <= Bag.startCapacity)
end)

test("buying: enough coins levels up and pays, not enough does nothing, maxed does nothing", function()
	local c2, c3 = Upgrades.bag.costs[2], Upgrades.bag.costs[3]
	local ok, lvl, left = UpgradeRules.buy(Upgrades, "bag", 1, c2 + 5)
	assert(ok and lvl == 2 and left == 5)
	ok, lvl, left = UpgradeRules.buy(Upgrades, "bag", 2, c3 - 1)
	assert(not ok and lvl == 2 and left == c3 - 1)
	local max = #Upgrades.bag.values
	ok, lvl, left = UpgradeRules.buy(Upgrades, "bag", max, 1e9)
	assert(not ok and lvl == max and left == 1e9)
	assert(UpgradeRules.nextCost(Upgrades, "bag", max) == nil)
end)

test("the biggest tool fits in its spread (13 = every bubble within 2 spacings)", function()
	local n = 0
	local r = Upgrades.tool.spread
	for x = -4, 4 do
		for y = -4, 4 do
			if x * x + y * y <= r * r then
				n += 1
			end
		end
	end
	assert(n >= Upgrades.tool.values[#Upgrades.tool.values], "spread too small: " .. n)
end)

test("only real upgrade names are accepted", function()
	assert(UpgradeRules.valid(Upgrades, "bag"))
	assert(not UpgradeRules.valid(Upgrades, "coins"))
	assert(not UpgradeRules.valid(Upgrades, 5))
	assert(not UpgradeRules.valid(Upgrades, nil))
end)

test("value clamps silly levels", function()
	assert(UpgradeRules.value(Upgrades, "bag", 0) == 25)
	assert(UpgradeRules.value(Upgrades, "bag", 999) == Upgrades.bag.values[#Upgrades.bag.values])
end)

print(("upgrade_tests: %d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("upgrade tests failed")
end
