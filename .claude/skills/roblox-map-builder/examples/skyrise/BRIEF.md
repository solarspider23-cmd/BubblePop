# Skyrise Simulator (brief)

**Game:** zone-gated simulator (collect / click resources, hatch eggs, sell, buy the next zone).
**Archetype:** floating sky islands + zone strip (map_archetypes.md). No ground plane: islands over a sea of clouds.

- Chain of 6 islands rising in height: Spawn (y 0) -> 1 Meadow (y 14) -> 2 Dune (y 34) -> 3 Frost (y 58) ->
  4 Ember (y 86) -> Summit (y 130). Bridges between them; a priced **zone gate** at the start of each bridge.
- Spawn island (r 72): paving plaza, Egg Shrine, Sell Pad, Upgrade Stand, Teleport ring (one pad per zone colour),
  lamp posts, puffy trees and flower beds on the rim. Spawn faces north up the chain.
- Each zone island (r 80-88): its own biome (trees, rocks, ground colour) + clusters of breakable resource nodes
  (coin piles, chests, crystal clusters), a teleport pad, a winding stone path.
- **Hero:** Summit island with a giant golden Trophy (cup, handles, crown, orbiting rings), the highest point,
  visible from spawn above the chain.
- Island undersides are modelled (strata, hanging rocks, roots); small floating rocks around; clouds below.
- Look: bright early morning, low sun from the east, pale mint/peach horizon to clear blue, cool thin haze.
- Not this: ground plane, bowl/rim, plots, sunset, noon.

| Axis | Skyrise | Grove | Frostpeak | Sugarworks |
|---|---|---|---|---|
| Layout grammar | island chain rising, bridges + zone gates | bowl + radial paths | bowl + street cross | 2x4 plot grid on a boulevard |
| Terrain | floating islands over clouds, no ground | rolling hills, rim | snow bowl, pond | flat plateau, cliffs to sea |
| Traversal | walk + bridges + gates + teleport pads, climbing | walk | walk | walk + plot gates |
| Scale | ~700 long, 130 studs of height | 440 square | 440 square | 300 x 560 strip |
| Kit | sky islands, simulator stations, resource nodes, 4 biomes | forest props | cabins | candy machines |
| Look | early morning, cool blue | warm noon | cold noon | sunset |
| Hero | golden Trophy on the summit | elder tree door | ice spire | Candy Exchange |
