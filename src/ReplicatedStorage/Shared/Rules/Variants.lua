--!strict
-- Pure variant rules (tested in tests/variant_tests.luau). Variant 0 = a normal bubble;
-- 1.. = Config/Variants.list entries.
local VariantRules = {}

-- roll: u is a random number in [0, 1). The rarest variant is checked first, so each variant
-- gets exactly its own chance.
function VariantRules.roll(config: any, u: number): number
	local edge = 0
	for i = #config.list, 1, -1 do
		edge += config.list[i].chance
		if u < edge then
			return i
		end
	end
	return 0
end

-- coins for popping a bubble of this variant
function VariantRules.coins(config: any, variant: number?): number
	local v = variant and config.list[variant]
	return v and v.coins or config.baseCoins
end

return VariantRules
