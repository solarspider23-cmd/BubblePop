--!strict
-- Pure pad rules (tested in tests/lobby_tests.luau). A pad holds an ordered list of members;
-- the first one is the owner (picks the room, can press Start).
export type Pad = { members: { number }, countdown: number? }

local LobbyRules = {}

function LobbyRules.newPad(): Pad
	return { members = {}, countdown = nil }
end

-- Update a pad from who is standing on it now (userIds). Keeps the join order, adds newcomers
-- at the end up to max, drops anyone who stepped off. Returns true if the members changed.
function LobbyRules.update(pad: Pad, standing: { number }, max: number): boolean
	local here: { [number]: boolean } = {}
	for _, id in standing do
		here[id] = true
	end
	local kept = {}
	local inPad: { [number]: boolean } = {}
	for _, id in pad.members do
		if here[id] then
			table.insert(kept, id)
			inPad[id] = true
		end
	end
	for _, id in standing do
		if #kept >= max then
			break
		end
		if not inPad[id] then
			table.insert(kept, id)
			inPad[id] = true
		end
	end
	local changed = #kept ~= #pad.members
	if not changed then
		for i, id in kept do
			if pad.members[i] ~= id then
				changed = true
				break
			end
		end
	end
	pad.members = kept
	return changed
end

function LobbyRules.owner(pad: Pad): number?
	return pad.members[1]
end

-- Tick the countdown. Starts it when someone joins, clears it when the pad empties.
-- Returns true when it reaches zero (time to start).
function LobbyRules.tick(pad: Pad, dt: number, full: number): boolean
	if #pad.members == 0 then
		pad.countdown = nil
		return false
	end
	pad.countdown = (pad.countdown or full) - dt
	return (pad.countdown :: number) <= 0
end

return LobbyRules
