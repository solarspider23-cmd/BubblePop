--!strict
-- Number text in one place. Money is counted in whole cents (1 popped bubble = 1 cent)
-- and shown as dollars: 1 -> "$0.01", 150 -> "$1.50", 123456 -> "$1,234.56".
local Format = {}

function Format.commas(n: number): string
	local s = tostring(math.floor(math.abs(n)))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")
	return (n < 0 and "-" or "") .. out
end

-- "$1,234.56"
function Format.money(cents: number): string
	cents = math.floor(cents + 0.5)
	local neg = cents < 0
	cents = math.abs(cents)
	return (neg and "-$" or "$") .. Format.commas(cents // 100) .. ("."):rep(1) .. ("%02d"):format(cents % 100)
end

-- short, for floating "+" text: under a dollar as cents ("1¢", "10¢"), else "$1.50"
function Format.short(cents: number): string
	if math.abs(cents) < 100 then
		return math.floor(cents) .. "¢"
	end
	return Format.money(cents)
end

return Format
