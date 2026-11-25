-- Walking over floor wrap pops it right away (no press time). Shown at once on this
-- client, then sent to the server in small batches to be checked and counted.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Pop = require(ReplicatedStorage.Shared.Config.Pop)
local BubbleView = require(script.Parent.BubbleView)

local Stomp = {}

function Stomp.start(remotes: Folder)
	local StompRequest = remotes:WaitForChild("StompRequest") :: RemoteEvent
	local player = Players.LocalPlayer
	local layout = BubbleView.layout
	local batch: { number } = {}
	local sinceSend = 0

	RunService.Heartbeat:Connect(function(dt)
		sinceSend += dt
		local char = player.Character
		local root = char and char:FindFirstChild("HumanoidRootPart") :: BasePart?
		local hum = char and char:FindFirstChildOfClass("Humanoid")
		if root and hum and hum.Health > 0 and hum.FloorMaterial ~= Enum.Material.Air then
			local pos = root.Position
			if pos.Y - layout.floorY < 5 then
				for _, id in layout.floorNear(pos.X, pos.Z, Pop.stompRadius) do
					if BubbleView.isIntact(id) and #batch < 30 then
						BubbleView.pop(id, "stomp")
						table.insert(batch, id)
					end
				end
			end
		end
		if #batch > 0 and sinceSend >= 0.1 then
			sinceSend = 0
			StompRequest:FireServer(batch)
			batch = {}
		end
	end)
end

return Stomp
