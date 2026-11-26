-- Money text checks.
--   tools/bin/luau tests/format_tests.luau
local Format = require("../src/ReplicatedStorage/Shared/Format")

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
local function eq(a, b)
	assert(a == b, tostring(a) .. " ~= " .. tostring(b))
end

test("money", function()
	eq(Format.money(0), "$0.00")
	eq(Format.money(1), "$0.01")
	eq(Format.money(10), "$0.10")
	eq(Format.money(150), "$1.50")
	eq(Format.money(123456), "$1,234.56")
	eq(Format.money(100000000), "$1,000,000.00")
end)

test("short", function()
	eq(Format.short(1), "1¢")
	eq(Format.short(10), "10¢")
	eq(Format.short(99), "99¢")
	eq(Format.short(150), "$1.50")
end)

test("commas", function()
	eq(Format.commas(0), "0")
	eq(Format.commas(999), "999")
	eq(Format.commas(1000), "1,000")
	eq(Format.commas(1234567), "1,234,567")
end)

print(("format_tests: %d passed, %d failed"):format(passed, failed))
if failed > 0 then
	error("format tests failed")
end
