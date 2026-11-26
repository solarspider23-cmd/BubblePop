-- Pad checks.
--   tools/bin/luau tests/lobby_tests.luau
local LobbyRules = require("../src/ReplicatedStorage/Shared/Rules/Lobby")

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

test("first to step on is the owner; join order is kept", function()
	local p = LobbyRules.newPad()
	assert(LobbyRules.update(p, { 5 }, 4))
	assert(LobbyRules.update(p, { 7, 5 }, 4))
	assert(LobbyRules.owner(p) == 5 and p.members[2] == 7)
end)

test("max 4: a fifth player isn't added", function()
	local p = LobbyRules.newPad()
	LobbyRules.update(p, { 1, 2, 3, 4, 5 }, 4)
	assert(#p.members == 4 and not table.find(p.members, 5))
end)

test("owner steps off: the next one becomes owner", function()
	local p = LobbyRules.newPad()
	LobbyRules.update(p, { 1, 2 }, 4)
	LobbyRules.update(p, { 2 }, 4)
	assert(LobbyRules.owner(p) == 2)
end)

test("no change reports false", function()
	local p = LobbyRules.newPad()
	LobbyRules.update(p, { 1, 2 }, 4)
	assert(not LobbyRules.update(p, { 2, 1 }, 4))
end)

test("countdown starts on join, fires at zero, clears when empty", function()
	local p = LobbyRules.newPad()
	assert(not LobbyRules.tick(p, 1, 10))
	assert(p.countdown == nil)
	LobbyRules.update(p, { 1 }, 4)
	assert(not LobbyRules.tick(p, 4, 10))
	assert(p.countdown == 6)
	assert(LobbyRules.tick(p, 6, 10))
	LobbyRules.update(p, {}, 4)
	LobbyRules.tick(p, 1, 10)
	assert(p.countdown == nil)
end)

print(("lobby_tests: %d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("lobby tests failed")
end
