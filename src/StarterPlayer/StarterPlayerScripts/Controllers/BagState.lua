-- What this client knows about its bag. The server decides (player attributes BagCount /
-- BagCapacity); pops sent but not confirmed yet are counted here, so a full bag stops
-- popping right away instead of popping and then putting bubbles back.
local Players = game:GetService("Players")

local BagState = {}

local player = Players.LocalPlayer
local sent: { number } = {} -- os.clock() of each pop sent but not confirmed yet
local CONFIRM_TIME = 1 -- a pop the server hasn't counted after this long was refused

local function pending(): number
	local now = os.clock()
	while sent[1] and now - sent[1] > CONFIRM_TIME do
		table.remove(sent, 1)
	end
	return #sent
end

local function count(): number
	return (player:GetAttribute("BagCount") or 0) + pending()
end

function BagState.capacity(): number
	return player:GetAttribute("BagCapacity") or 25
end

function BagState.count(): number
	return math.min(count(), BagState.capacity())
end

function BagState.hasRoom(): boolean
	return count() < BagState.capacity()
end

-- call after showing a pop that the server will count
function BagState.added()
	table.insert(sent, os.clock())
end

-- the server counted some: drop that many of the oldest unconfirmed pops
local last = player:GetAttribute("BagCount") or 0
player:GetAttributeChangedSignal("BagCount"):Connect(function()
	local now = player:GetAttribute("BagCount") or 0
	local grew = now - last
	last = now
	if grew < 0 then
		table.clear(sent) -- sold
	end
	for _ = 1, math.max(0, grew) do
		table.remove(sent, 1)
	end
end)

return BagState
