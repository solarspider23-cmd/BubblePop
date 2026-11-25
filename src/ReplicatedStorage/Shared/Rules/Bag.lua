--!strict
-- Pure bag rules (tested in tests/bag_tests.luau). The server keeps one bag per player.
-- count = bubbles in the bag, value = coins they're worth when sold.
export type Bag = { count: number, value: number }

local BagRules = {}

function BagRules.new(): Bag
	return { count = 0, value = 0 }
end

function BagRules.full(bag: Bag, capacity: number): boolean
	return bag.count >= capacity
end

-- Put one popped bubble (worth `coins`) in the bag. false = the bag is full, nothing changes.
function BagRules.add(bag: Bag, coins: number, capacity: number): boolean
	if bag.count >= capacity or coins < 0 then
		return false
	end
	bag.count += 1
	bag.value += coins
	return true
end

-- Empty the bag; returns the coins it was worth.
function BagRules.sell(bag: Bag): number
	local coins = bag.value
	bag.count = 0
	bag.value = 0
	return coins
end

-- Is a point close enough to the recycler (a box centred at cx, cz) to sell?
function BagRules.nearRecycler(x: number, z: number, cx: number, cz: number, sizeX: number, sizeZ: number, reach: number): boolean
	return math.abs(x - cx) <= sizeX / 2 + reach and math.abs(z - cz) <= sizeZ / 2 + reach
end

return BagRules
