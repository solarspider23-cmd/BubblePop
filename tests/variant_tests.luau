-- Bubble variant checks.
--   tools/bin/luau tests/variant_tests.luau

local VariantRules = require("../src/ReplicatedStorage/Shared/Rules/Variants")
local Variants = require("../src/ReplicatedStorage/Shared/Config/Variants")

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

test("chances add up to less than 1 (most bubbles stay normal)", function()
	local sum = 0
	for _, v in Variants.list do
		assert(v.chance > 0 and v.coins > Variants.baseCoins, v.key)
		sum += v.chance
	end
	assert(sum < 0.1, "too many rare bubbles: " .. sum)
end)

test("rarer variants are worth more", function()
	for i = 2, #Variants.list do
		assert(Variants.list[i].chance < Variants.list[i - 1].chance, "order " .. i)
		assert(Variants.list[i].coins > Variants.list[i - 1].coins, "coins " .. i)
	end
end)

test("roll edges: 0 is the rarest, just past all chances is normal", function()
	assert(VariantRules.roll(Variants, 0) == #Variants.list)
	local sum = 0
	for _, v in Variants.list do
		sum += v.chance
	end
	assert(VariantRules.roll(Variants, sum + 1e-9) == 0)
	assert(VariantRules.roll(Variants, 0.999) == 0)
end)

test("each variant comes up at about its chance", function()
	local counts = {}
	local n = 200000
	for i = 0, n - 1 do
		local k = VariantRules.roll(Variants, (i + 0.5) / n)
		counts[k] = (counts[k] or 0) + 1
	end
	for i, v in Variants.list do
		local got = (counts[i] or 0) / n
		assert(math.abs(got - v.chance) < v.chance * 0.05 + 1 / n, v.key .. " " .. got)
	end
end)

test("coins: normal gets baseCoins, variants their own", function()
	assert(VariantRules.coins(Variants, 0) == Variants.baseCoins)
	assert(VariantRules.coins(Variants, nil) == Variants.baseCoins)
	for i, v in Variants.list do
		assert(VariantRules.coins(Variants, i) == v.coins)
	end
	assert(VariantRules.coins(Variants, 99) == Variants.baseCoins)
end)

print(("variant_tests: %d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("variant tests failed")
end
