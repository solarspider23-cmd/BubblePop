# The Shattered Void (brief)

**Game:** void-themed sim / adventure hub: spawn, shop, upgrade, take quests, jump the stepping stones, ride the
gravity lift to a secret shard, fight in the arena, leave through the Rift Gate portal.

**Archetype:** **orbital ring**. Six obsidian shards float on ONE orbit (r ~110-140) round a singularity hanging at the
centre (0, 50, -5); a ring road of rune bridges links them (hexagon), one leg is a run of floating stepping stones, and
a gravity lift climbs 60 studs from the spawn shard to a seventh, high Starwatch shard. No ground, no sea, no clouds:
endless starry void below and around. Every station faces inward, so the singularity is in view from everywhere.

| Shard | Centre / top y / R | What is there |
|---|---|---|
| Spawn (S) | (0, 130) y 0, R 32 + north promontory | spawn dais, ruined arch over the east bridge head, overlook rune circle at the promontory tip with rails, lift pad |
| Merchant (SW) | (-110, 72) y 5, R 25 | Void Merchant (shop): crystal-canopy kiosk, wares, hanging crystal lanterns, blank sign board |
| Altar (SE) | (110, 72) y 5, R 25 | Ascension Altar (upgrades): 3-step dais, rune-channel obelisk, floating rings, 4 void braziers |
| Seer (W) | (-130, -48) y 12, R 26 | Seer's Lectern (quests): curved screen + blank board, codex lectern, floating orb |
| Rift (E) | (132, -48) y 12, R 31 | **Rift Gate** (portal, hero 2): ring of void-stone voussoirs, drifted stones, spiral rift membrane |
| Arena (N) | (0, -142) y 20, R 46 | walled arena (rim r 34, gaps W / E / S), big rune circle, 4 braziers, colonnade |
| Starwatch | (-40, 140) y 60, R 19 | top of the gravity lift: Heart Crystal (secret / reward) |

- **Hero 1:** the Singularity: black core r 22, photon ring, accretion disc of banded Neon annuli tilted 24 deg toward
  the players (white-hot -> magenta -> violet -> cyan), lensed arcs, 30 orbiting rocks, light streaks. On the spawn
  -> arena axis: spawn looks north through the promontory straight at it, arena behind.
- **Paths:** spawn -> SW -> W -> N and spawn -> SE -> (stepping stones) -> E -> N, rune paving ribbons from every
  bridge head to the station; lanterns every ~14 studs. Lift = vertical shortcut.
- **Palette:** obsidian black-indigo, dusk-violet crust, teal void moss, lilac void-stone with pale bone trim; accents
  (mostly Neon) magenta, violet, cyan, white core. Painted 1024 atlas (`void_paint.py`, built on valleylake/paint.py).
- **Look:** night void: near-black indigo sky, stars, faint violet nebula, cool lavender key + cyan rim, glow carries
  the drama, very thin violet haze.
- **Not this:** sky islands over clouds in daylight on a rising chain (Skyrise), bowls, flags / banners, text in meshes.

## Difference table
| Axis | Shattered Void | Skyrise (nearest) | Mistvale Lake | Eggstead Isle |
|---|---|---|---|---|
| Layout grammar | one orbit ring of shards round a central hero, inward-facing stations | island chain rising in a line, zone gates | bowl round a lake | 2 x 4 plot rows on a lane |
| Terrain | faceted obsidian shards with keels + stalactites, flat walkable tops, void below | rounded strata islands over clouds | flat floor + rock-tier wall | flat island in a lake |
| Traversal | rune bridges + stepping-stone jump run + gravity lift to a high shard | bridges + gates + teleports | walk | walk + plot gates |
| Scale | ~300 x 330 ring, 60 studs of lift | ~700 long, 130 high | 330 x 380 | 300 x 400 |
| Kit | void ruins, crystals, void flora, rune bridges, lift, stations, singularity | sky sim stations, resource nodes | moss rocks, timber houses | low-poly ranch + eggs |
| Look | night void, stars, nebula, neon glow | early morning, cool blue | cyan daylight | bright morning |
| Hero | black hole singularity + rift gate | golden trophy | waterfall + islet tree | cracked-egg hatchery |
