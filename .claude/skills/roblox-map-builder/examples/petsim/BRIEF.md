# Puffpaw Isles (brief)

**Game:** pet-collecting simulator. Players break coin piles, chests, gift boxes and crystal clumps for money, hatch
eggs at egg stands, unlock new zones through toll gates and show their pets off in the hub. Original "Puffpaw" pet
mascot and art; no layout or art copied from an existing game. Style: HAPPY CHIBI: squashy rounded chunky shapes,
pastel-but-saturated candy colours, smooth soft bevels, toy-like proportions, sunny sky with soft clouds.
No text, letters, digits, flags or banners (labels are GUIs on hook anchors).

**Archetype:** ISLAND CHAIN in a turquoise lagoon (not built before). Four round "layer-cake" islands (grass top,
cream icing lip with drips, sponge cliff with a jam stripe) linked by chunky bridges. The chain curls clockwise round
the hub's north and east sides and climbs: hub y 5 > Meadow y 7 > Candy y 12 > Crystal y 18. A toll gate stands at
the near end of every bridge. Puffy clouds sit on the water round the whole chain as the frame.

| Where | What |
|---|---|
| Hub isle (0, 0) r ~95 | Puffpaw Fountain hero (giant chibi pet statue on a 3-tier fountain), pastel tiled plaza; Hatchery W under a rainbow arch with 3 egg stands; Pet Shop E (striped-awning kiosk); Upgrade Machine NE (giant gumball machine); Trading plaza SW (2 umbrella booths + a trade pad); Leaderboard SE (blank frame); spawn pad S |
| Gate 1 + bridge N | Meadow isle (20, -270): puff trees, daisy patches, red mushrooms, picnic set, stumps; 40 breakables (coins / gifts / chests) |
| Gate 2 + bridge E | Candy isle (270, -180): cotton-candy trees, giant lollipops, candy canes, gumdrops, a giant donut; 40 breakables |
| Gate 3 + bridge S | Crystal isle (270, 90): crystal trees, crystal spires, star lamps, glow shrooms; 40 breakables (crystals / chests) |
| Frame | picket fences + puff bushes on every rim, soft rocks and clouds on the lagoon, far clouds |

- **Spawn:** (0, 5, 70) facing north: fountain on the axis, the rainbow arch left, the shop right, Gate 1 behind.
- **Palette:** grass green / cream paving / caramel wood as base; candy pink, sky, lilac, sunny yellow, mint accents.
  Zone tint: Meadow green + red, Candy pink + mint, Crystal lilac + sky.
- **Look:** bright noon, sun 55 deg, warm white key, saturated blue sky to pale horizon, almost no haze.
- **Not this:** plot rows (Eggstead), straight strips, floating sky islands with undersides (Skyrise), text in geometry.

## Difference table
| Axis | Puffpaw Isles | Eggstead (plots) | Skyrise (sky zones) | +1 Speed (strip) | Moon Sweepers |
|---|---|---|---|---|---|
| Layout grammar | island chain curling round a central hub isle, bridges + toll gates | facing plot rows on a conveyor lane | island chain rising in the sky | one straight track | shelf rings stepping down |
| Terrain | round layer-cake islands in a lagoon (icing lip, sponge cliffs) | flat island in a lake | floating rocks, no ground | stepped block canyon | crater terraces |
| Traversal | walk + bridges + paid gates | walk + carry eggs | walk + bridges + teleports | run | ramps + airlocks |
| Scale | ~560 x 620, islands r 95-110 | 264 x 472 | ~700 long | 144 x 2300 | 720 round |
| Kit | chibi toy kit: smooth puff trees, candy, crystals, breakables | low-poly faceted farm | sky stations, nodes | Part-built studs | space junk |
| Look | candy pastel noon, glossy smooth shading | spring morning flat-shaded | cool early morning | stud midday | black sky |
| Hero | giant chibi pet statue fountain + rainbow arch | cracked egg hatchery | golden trophy | finish podium | rocket |
