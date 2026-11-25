-- Client start: draw the bubbles, sync with the server, then start the tool and stomping.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Controllers = script.Parent:WaitForChild("Controllers")
local BubbleView = require(Controllers.BubbleView)
local Popper = require(Controllers.Popper)
local Stomp = require(Controllers.Stomp)

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
