--!strict
-- Pure checks the server runs on every pop a client asks for (tested in tests/).

local PopRules = {}

-- A bubble id from a client: must be a whole number inside the room's range.
function PopRules.validId(id: any, count: number): boolean
	return type(id) == "number" and id == id and id % 1 == 0 and id >= 1 and id <= count
end

-- Click pop: close enough, and not faster than the player's pop time allows.
function PopRules.clickOk(distance: number, sinceLastPop: number, pop: any): (boolean, string?)
	if distance > pop.reach + pop.reachSlack then
		return false, "too far"
	end
	if sinceLastPop < pop.popTime - pop.timeTolerance then
		return false, "too fast"
	end
	return true, nil
end

-- Stomp pop: a floor bubble right under the player (sideways distance and height above the floor).
function PopRules.stompOk(sideways: number, heightAboveFloor: number, pop: any): (boolean, string?)
	if sideways > pop.stompRadius + pop.stompSlack then
		return false, "too far"
	end
	if heightAboveFloor > 6 then
		return false, "not on the floor"
	end
	return true, nil
end

-- Simple token bucket: returns a function(now) -> allowed
function PopRules.rateLimiter(perSecond: number)
	local tokens, last = perSecond, -math.huge
	return function(now: number): boolean
		if last == -math.huge then
			last = now
		end
		tokens = math.min(perSecond, tokens + (now - last) * perSecond)
		last = now
		if tokens >= 1 then
			tokens -= 1
			return true
		end
		return false
	end
end

-- A bigger tool pops extra bubbles with the aimed one: they must be on the same wall/floor
-- and close to it (within `spread` bubble spacings).
function PopRules.extraOk(main: any, extra: any, spacing: number, spread: number): boolean
	if extra.surface ~= main.surface or extra.id == main.id then
		return false
	end
	local dx, dy, dz = extra.x - main.x, extra.y - main.y, extra.z - main.z
	return dx * dx + dy * dy + dz * dz <= (spacing * spread) ^ 2
end

return PopRules
