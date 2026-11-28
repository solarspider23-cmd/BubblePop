-- Client start: draw the bubbles, sync with the server, then start the tool and stomping.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Controllers = script.Parent:WaitForChild("Controllers")
local BubbleView = require(Controllers.BubbleView)
local Popper = require(Controllers.Popper)
local Stomp = require(Controllers.Stomp)
local Hud = require(Controllers.Hud)
local Sfx = require(Controllers.Sfx)
local Scraps = require(Controllers.Scraps)
local Shop = require(Controllers.Shop)
local Lobby = require(Controllers.Lobby)
local HubBubbles = require(Controllers.HubBubbles)
local HubChest = require(Controllers.HubChest)
local Sounds = require(ReplicatedStorage.Shared.Config.Sounds)
local Room = require(ReplicatedStorage.Shared.Config.Room)
local Pop = require(ReplicatedStorage.Shared.Config.Pop)

local player = Players.LocalPlayer
local remotes = ReplicatedStorage:WaitForChild("Remotes")

BubbleView.build()

-- listen first, then ask for the current state, so nothing is missed in between
local BubbleChanged = remotes:WaitForChild("BubbleChanged") :: RemoteEvent
BubbleChanged.OnClientEvent:Connect(function(changes, by, kinds)
	if type(changes) == "table" and type(by) == "table" then
		BubbleView.apply(changes, by, if type(kinds) == "table" then kinds else nil, player.UserId)
	end
end)
-- Sold at the recycler
local Sold = remotes:WaitForChild("Sold") :: RemoteEvent
Sold.OnClientEvent:Connect(function(coins, n)
	if type(coins) == "number" and type(n) == "number" then
		Hud.sold(coins, n)
		Scraps.toRecycler(n)
		Sfx.play("sell")
	end
end)

local ok, list = pcall(function()
	return (remotes:WaitForChild("GetPopped") :: RemoteFunction):InvokeServer()
end)
if ok and type(list) == "table" then
	for i, id in list.variantIds or {} do
		BubbleView.setVariant(id, list.variantKinds[i])
	end
	for _, id in list.popped or {} do
		BubbleView.pop(id, "quiet")
	end
end

Popper.start(remotes)
Stomp.start(remotes)
Shop.start(remotes)
Lobby.start(remotes) -- hub (third person) vs popping room (first person, run HUD)
HubBubbles.start()
HubChest.start() -- the free gift chest opens as you walk up (cosmetic)

-- Test-room switches: L = look, 1-9 = pop sound, K = squeeze sound, B = shop
local squeezeIndex = 1
Sfx.preload()
local lookIndex = #(Room.looks or {}) -- start on the newest look
BubbleView.setLook(lookIndex)
local keys = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five, Enum.KeyCode.Six, Enum.KeyCode.Seven, Enum.KeyCode.Eight, Enum.KeyCode.Nine }
UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	if input.KeyCode == Enum.KeyCode.K and Sounds.squeezeOptions then
		squeezeIndex = squeezeIndex % #Sounds.squeezeOptions + 1
		local opt = Sounds.squeezeOptions[squeezeIndex]
		Sfx.override("press", opt)
		Hud.toast("Squeeze sound " .. squeezeIndex .. ": " .. opt.name)
		Sfx.play("press", nil, Pop.popTime * (1 - Pop.reachPhase))
		return
	end
	if input.KeyCode == Enum.KeyCode.L then
		lookIndex += 1
		Hud.toast("Look: " .. BubbleView.setLook(lookIndex))
		return
	end
	for i, k in keys do
		local opt = Sounds.popOptions and Sounds.popOptions[i]
		if input.KeyCode == k and opt then
			Sfx.override("pop", opt)
			Sfx.override("stompPop", { id = opt.id, ids = opt.ids, pitch = (opt.pitch or 1) * 0.85 })
			Sfx.override("otherPop", opt)
			Hud.toast("Pop sound " .. i .. ": " .. opt.name)
			Sfx.play("pop")
		end
	end
end)
