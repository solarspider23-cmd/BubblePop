-- +1 Speed Run: one-time setup (Studio command bar, Edit mode), AFTER File > Insert from File... > PlusSpeed.rbxmx
-- 1) the stud look: every stud part in the map uses Material Glacier + MaterialVariant "Studs"
local MaterialService = game:GetService("MaterialService")
local mv = MaterialService:FindFirstChild("Studs") or Instance.new("MaterialVariant")
mv.Name = "Studs"
mv.BaseMaterial = Enum.Material.Glacier
mv.ColorMap = "" -- set to your own uploaded stud texture id (rbxassetid://...); left empty on purpose
mv.StudsPerTile = 1
mv.Parent = MaterialService

-- 2) bright cartoon midday, light blue haze (matches the Blender previews)
local Lighting = game:GetService("Lighting")
Lighting.ClockTime = 13.5
Lighting.Brightness = 3
Lighting.Ambient = Color3.fromRGB(120, 130, 150)
Lighting.OutdoorAmbient = Color3.fromRGB(160, 180, 210)
Lighting.ColorShift_Top = Color3.fromRGB(255, 245, 230)
local atm = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
atm.Density = 0.25; atm.Haze = 0.6; atm.Glare = 0.2
atm.Color = Color3.fromRGB(215, 235, 255); atm.Decay = Color3.fromRGB(170, 200, 240)
atm.Parent = Lighting
local bloom = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
bloom.Intensity = 0.4; bloom.Size = 18; bloom.Threshold = 1.1
bloom.Parent = Lighting

-- 3) a SpawnLocation on the hub spawn pad, facing down the track (-Z)
local map = workspace:FindFirstChild("PlusSpeedMap")
if map and not workspace:FindFirstChild("PlusSpawn") then
	local s = Instance.new("SpawnLocation")
	s.Name = "PlusSpawn"; s.Anchored = true; s.Size = Vector3.new(12, 1, 12)
	s.CFrame = CFrame.new(0, 0.6, 62); s.Transparency = 1; s.CanCollide = false; s.Neutral = true
	s.Parent = workspace
end
print("[PlusSpeed] setup done")
