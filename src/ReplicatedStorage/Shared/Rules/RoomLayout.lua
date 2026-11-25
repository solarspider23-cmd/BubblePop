--!strict
-- Pure layout of every bubble in the room (no Roblox services, tested in tests/).
-- Server and clients build the same list from Config/Room, so a bubble is just its id.
--
-- Bubble: { id, surface, sheet, x, y, z (base centre, on the sheet's top), nx, ny, nz (out of the
-- sheet, into the room), rx, ry, rz (sideways along the sheet) }
-- Sheet:  { x, y, z (centre), nx.., rx.., size, thickness }

export type Bubble = {
	id: number,
	surface: string,
	sheet: number,
	x: number, y: number, z: number,
	nx: number, ny: number, nz: number,
	rx: number, ry: number, rz: number,
}
export type Sheet = {
	surface: string,
	x: number, y: number, z: number,
	nx: number, ny: number, nz: number,
	rx: number, ry: number, rz: number,
	size: number,
	thickness: number,
}

local RoomLayout = {}

local function v(x: number, y: number, z: number)
	return { x = x, y = y, z = z }
end

function RoomLayout.new(room: any)
	local S, n, sp, t = room.sheetSize, room.perSheet, room.spacing, room.sheetThickness
	assert(math.abs(n * sp - S) < 1e-6, "perSheet * spacing must equal sheetSize")
	local half = room.floorSheets * S / 2
	local y0 = room.floorY
	local height = room.wallRows * S
	local margin = (S - (n - 1) * sp) / 2

	-- origin = corner of the bubble plane (sheet top), right/up = tangents, normal = into the room
	local surfaces = {
		{ name = "floor", origin = v(-half, y0 + t, -half), right = v(1, 0, 0), up = v(0, 0, 1), normal = v(0, 1, 0), cols = room.floorSheets, rows = room.floorSheets },
		{ name = "north", origin = v(-half, y0, -half + t), right = v(1, 0, 0), up = v(0, 1, 0), normal = v(0, 0, 1), cols = room.floorSheets, rows = room.wallRows },
		{ name = "south", origin = v(half, y0, half - t), right = v(-1, 0, 0), up = v(0, 1, 0), normal = v(0, 0, -1), cols = room.floorSheets, rows = room.wallRows },
		{ name = "west", origin = v(-half + t, y0, half), right = v(0, 0, -1), up = v(0, 1, 0), normal = v(1, 0, 0), cols = room.floorSheets, rows = room.wallRows },
		{ name = "east", origin = v(half - t, y0, -half), right = v(0, 0, 1), up = v(0, 1, 0), normal = v(-1, 0, 0), cols = room.floorSheets, rows = room.wallRows },
	}

	local bubbles: { Bubble } = {}
	local sheets: { Sheet } = {}
	local floorGrid: { [number]: { [number]: number } } = {}

	for _, s in surfaces do
		local o, r, u, nn = s.origin, s.right, s.up, s.normal
		local function at(a: number, b: number, off: number)
			return o.x + r.x * a + u.x * b + nn.x * off, o.y + r.y * a + u.y * b + nn.y * off, o.z + r.z * a + u.z * b + nn.z * off
		end
		for row = 0, s.rows - 1 do
			for col = 0, s.cols - 1 do
				local cx, cy, cz = at(col * S + S / 2, row * S + S / 2, -t / 2)
				table.insert(sheets, {
					surface = s.name, x = cx, y = cy, z = cz,
					nx = nn.x, ny = nn.y, nz = nn.z, rx = r.x, ry = r.y, rz = r.z,
					size = S, thickness = t,
				})
				local sheetIndex = #sheets
				for j = 0, n - 1 do
					for i = 0, n - 1 do
						local x, y, z = at(col * S + margin + i * sp, row * S + margin + j * sp, 0)
						local id = #bubbles + 1
						bubbles[id] = {
							id = id, surface = s.name, sheet = sheetIndex, x = x, y = y, z = z,
							nx = nn.x, ny = nn.y, nz = nn.z, rx = r.x, ry = r.y, rz = r.z,
						}
						if s.name == "floor" then
							local gi, gj = col * n + i, row * n + j
							floorGrid[gi] = floorGrid[gi] or {}
							floorGrid[gi][gj] = id
						end
					end
				end
			end
		end
	end

	local layout = {
		bubbles = bubbles,
		sheets = sheets,
		half = half,
		height = height,
		floorY = y0,
	}

	-- Ids of floor bubbles whose centre is within `radius` (sideways) of x, z
	function layout.floorNear(x: number, z: number, radius: number): { number }
		local out = {}
		local fo = surfaces[1].origin
		local gi0 = math.floor((x - fo.x - margin - radius) / sp)
		local gi1 = math.ceil((x - fo.x - margin + radius) / sp)
		local gj0 = math.floor((z - fo.z - margin - radius) / sp)
		local gj1 = math.ceil((z - fo.z - margin + radius) / sp)
		for gi = gi0, gi1 do
			local col = floorGrid[gi]
			if col then
				for gj = gj0, gj1 do
					local id = col[gj]
					if id then
						local b = bubbles[id]
						local dx, dz = b.x - x, b.z - z
						if dx * dx + dz * dz <= radius * radius then
							table.insert(out, id)
						end
					end
				end
			end
		end
		return out
	end

	return layout
end

return RoomLayout
