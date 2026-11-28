# Maple Junction (brief)

**Game:** town / city hub for a roleplay-sim (earn money at jobs, shop, buy a car, travel by train to other maps).
**Archetype:** CITY GRID (map_archetypes.md, first use): blocks, streets, sidewalks, a central square, building fronts as a kit.

- Size: ground x -280..400, z -268..256 (walkable street grid ~ 470 x 430, rail corridor east). Flat: roads y 0, kerb +0.6.
- Streets: Main Boulevard (E-W, z 70, 56 wide, planted median), North Street (z -96, 32), West / East Avenues (x -84 / 84, 32).
  12-stud sidewalks, zebra crossings on every junction leg + mid-block crossings on the square axis, lane lines, stop bars.
- **Spawn:** Town Square south side (0, 26), facing north. **Hero:** clock-tower Town Hall on the square's north side, tower
  top ~140, on the spawn axis behind the fountain. Second landmark: the Train Station closing the boulevard vista (east).
- Districts / stations: Town Square (fountain, 4 lawns, Job Board) | Shop Row on the boulevard south side (general store,
  cafe) + Boutique (SW) | Bank (west, faces the square) | Car Dealer (east, open display hall + lot) | Train Station
  (walk-through arch to the platform, canopies, parked 3-car commuter train) | back alley behind the shop row (dumpsters,
  fire escapes, pipes) | skyline ring of towers framing every edge.
- Palette: warm brick, cream stucco, sage clapboard, slate blue (bases); red / yellow / teal / blue accents on awnings,
  cars, signs, shutters; teal copper roofs + gold on the hero. Painted 1024 atlas: true 2D tiles for brick, stucco ashlar,
  siding, slate shingles, asphalt, paving (clipped at the tile period so they never stretch).
- Look: bright late-morning daylight, sun 48 deg from the south-east, clear blue sky, very thin cool haze.
- Not this: bowl, rim, plots, islands, ring, canyon; no sunset / night; no text, flags or banners; no hills.

| Axis | Maple Junction | Skyrise | Eggstead | Mistvale | Shattered Void | Others |
|---|---|---|---|---|---|---|
| Layout grammar | street grid: 3 x 3 blocks, square, boulevard vista to a station | island chain + bridges | 2 x 4 plot rows on a lane | bowl round a lake | orbital ring | bowl, plots, strip, crater, mirrored arena, diorama, ring lagoon, canyon run |
| Terrain | flat asphalt + kerbed blocks | floating islands | lake island | valley bowl, cliffs | void shards | hills / snow / plateau / crater / canyon |
| Traversal | walk sidewalks + crossings, cars on lanes, train travel point | bridges, gates, teleports | walk, conveyor | walk, dock | bridges, jump run, lift | walk, ramps, boats |
| Scale | ~470 x 430 walkable, towers to ~140 | 700 long, 130 high | ~300 | ~330 bowl | ring ~500 | 150-720 |
| Kit | facade generator (piers, windows, shopfronts, awnings, cornices, rooftop tanks/AC), cars, bus, train, street furniture | sky islands, sim stations | low-poly farm | painterly rock + timber | obsidian + crystal | forest, candy, space, medieval, onsen, fishing, desert |
| Look | bright daytime city, brick/cream/sage/slate | early morning | low poly noon | cyan daylight | night glow | various |
| Hero | clock-tower town hall + train station | trophy | hatchery egg | leaning tree | black hole | tree door, spire, rocket, pagoda, lighthouse, temple |
