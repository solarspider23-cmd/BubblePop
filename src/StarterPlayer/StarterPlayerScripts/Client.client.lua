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
local Sounds = require(ReplicatedStorage.Shared.Config.Sounds)
local Room = require(ReplicatedStorage.Shared.Config.Room)

local player = Players.LocalPlayer
local remotes = ReplicatedStorage:WaitForChild("Remotes")

BubbleView.build()

-- listen first, then ask for the current state, so nothing is missed in between
local BubbleChanged = remotes:WaitForChild("BubbleChanged") :: RemoteEvent
BubbleChanged.OnClientEvent:Connect(function(changes, by)
	if type(changes) == "table" and type(by) == "table" then
		BubbleView.apply(changes, by, player.UserId)
	end
end)
local ok, list = pcall(function()
	return (remotes:WaitForChild("GetPopped") :: RemoteFunction):InvokeServer()
end)
if ok and type(list) == "table" then
	for _, id in list do
		BubbleView.pop(id, "quiet")
	end
end

player.CameraMode = Enum.CameraMode.LockFirstPerson -- popping is always first person
UserInputService.MouseIconEnabled = false -- the Hud draws its own crosshair
Popper.start(remotes)
Stomp.start(remotes)

-- Test-room switches: L = look, 1-6 = pop sound
local lookIndex = #(Room.looks or {}) -- start on the newest look
BubbleView.setLook(lookIndex)
local keys = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five, Enum.KeyCode.Six }
UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
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
			Sfx.override("stompPop", { id = opt.id, pitch = (opt.pitch or 1) * 0.85 })
			Sfx.override("otherPop", opt)
			Hud.toast("Pop sound " .. i .. ": " .. opt.name)
			Sfx.play("pop")
		end
	end
end)
