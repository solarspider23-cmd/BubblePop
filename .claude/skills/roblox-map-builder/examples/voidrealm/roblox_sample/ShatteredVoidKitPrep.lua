-- ShatteredVoidKitPrep: run ONCE in the Studio command bar (Edit mode) after importing the kit into ServerStorage.ShatteredVoidKit.
-- CollisionFidelity cannot be changed on an existing MeshPart, so each solid part is re-created with
-- AssetService:CreateMeshPartAsync using the fidelity its prop needs; glow parts get Box + no collision.
local AssetService = game:GetService("AssetService")
local kit = game.ServerStorage:WaitForChild("ShatteredVoidKit")
local Setup = require(game.ServerStorage:WaitForChild("ShatteredVoidSetup"))
local FID = { none = Enum.CollisionFidelity.Box, box = Enum.CollisionFidelity.Box, hull = Enum.CollisionFidelity.Hull,
	precise = Enum.CollisionFidelity.PreciseConvexDecomposition }
local done = 0
for _, model in kit:GetChildren() do
	local kind = Setup.Collision[model.Name] or "hull"
	for _, p in model:GetDescendants() do
		if p:IsA("MeshPart") then
			local want = string.find(p.Name, "_Glow_") and Enum.CollisionFidelity.Box or FID[kind]
			if p.CollisionFidelity ~= want and not pcall(function() p.CollisionFidelity = want end) then
				local ok, fresh = pcall(AssetService.CreateMeshPartAsync, AssetService, p.MeshId,
					{ CollisionFidelity = want, RenderFidelity = Enum.RenderFidelity.Automatic })
				if ok then
					p:ApplyMesh(fresh)
					done += 1
				else
					warn(model.Name, p.Name, fresh)
				end
			end
		end
	end
end
print("[ShatteredVoidKitPrep] re-meshed", done, "parts")
