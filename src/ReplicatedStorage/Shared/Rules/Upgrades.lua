--!strict
-- Pure upgrade rules (tested in tests/upgrade_tests.luau). Levels start at 1.
local UpgradeRules = {}

function UpgradeRules.valid(config: any, kind: any): boolean
	return type(kind) == "string" and table.find(config.order, kind) ~= nil
end

function UpgradeRules.value(config: any, kind: string, level: number): any
	local u = config[kind]
	return u.values[math.clamp(level, 1, #u.values)]
end

function UpgradeRules.maxed(config: any, kind: string, level: number): boolean
	return level >= #config[kind].values
end

-- coins for the next level, or nil when maxed
function UpgradeRules.nextCost(config: any, kind: string, level: number): number?
	local u = config[kind]
	if level >= #u.values then
		return nil
	end
	return u.costs[level + 1]
end

-- Try to buy the next level. Returns (ok, newLevel, coinsLeft).
function UpgradeRules.buy(config: any, kind: string, level: number, coins: number): (boolean, number, number)
	local cost = UpgradeRules.nextCost(config, kind, level)
	if not cost or coins < cost then
		return false, level, coins
	end
	return true, level + 1, coins - cost
end

return UpgradeRules
