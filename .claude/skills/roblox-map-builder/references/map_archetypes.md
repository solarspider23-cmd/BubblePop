# Map archetypes: every map must be a different game

Each new map is for a DIFFERENT game. Re-skinning an earlier map (same bowl, same rim, same centre landmark,
same kit with a new palette) is a failure even if it looks good. Before the brief, pick an archetype and fill the
difference table at the end of `BRIEF.md`.

## The axes that must change (at least 5 of 7 vs every earlier map)
1. **Layout grammar**: bowl + paths, linear course, grid, rings, stacked floors, islands, branching rooms, loop track.
2. **Terrain shape**: rolling hills, flat plots, cliffs + ledges, vertical tower, floating chunks, canyon, water-first.
3. **Traversal**: walk, obby jumps, vehicles/race, climb, swim/boat, teleport pads, ziplines.
4. **Scale + density**: tight 150-stud arena vs 1,500-stud open world; sparse vs packed.
5. **Prop kit**: NEW props written for this map. Reuse shared primitives (pro_lib), not another map's props.
6. **Look**: palette family, time of day, sky, fog, light colour (noon / sunset / night neon / overcast / underground).
7. **Hero idea**: what draws the eye and what the player does there (tree door, tower top, boss gate, shop dome).

## Archetypes (pick one, or combine two, never the last one used)
| Archetype | Game types | Layout grammar | Key build notes |
|---|---|---|---|
| Hub bowl | RNG / sim lobby | central plaza, radial paths, rim | done: Whispering Grove, Frostpeak. Avoid next. |
| Linear obby | obby, tower run | stages along a spline, checkpoints | jump gaps measured to the avatar (walk 16, jump ~7.2 h), kill floor, colour per stage |
| Vertical tower | tower climb, boss tower | floors stacked, spiral ramps | each floor a theme, inside + outside views, no rim |
| Tycoon plots (done: Sugarworks) | tycoon, grow-a, steal-a | N identical plots on a grid + shared road | plots exactly equal (fairness), spawn per plot, conveyor/door slots left empty |
| Arena | PvP, boss, minigame | one bounded space, cover, sightlines | symmetric or mirrored spawns, cover every ~20 studs, height layers |
| Island chain (done: Puffpaw Isles) | adventure, fishing, pet sims | islands linked by bridges/boats | water-first heightfield, each island one district |
| City grid (done: Maple Junction) | roleplay, heist | blocks, roads, interiors | street width 24+, building fronts as a kit (doors/windows/signs), alleys |
| Dungeon rooms | dungeon crawler | rooms + corridors graph | doorway kit, ceilings, light only from props, one-way gates |
| Race loop | racing, karting | closed track spline + infield | banked turns, run-off, track width 40+, decor outside barriers |
| Open zone strip (done: +1 Speed Run) | zone-gated sim, +1 runners / throwers | zones in a row, gates between | each zone own biome + palette, gate frames, difficulty rises along x |
| Floating sky (done: Skyrise) | sky islands, parkour, zone simulators | chunks over void, bridges | undersides modelled (seen from below), no ground plane, clouds |
| Terraced crater (done: Moon Sweepers) | zone-gated clean / collect sims | concentric shelf rings stepping DOWN to a central landmark, one ramp + gate per riser | hub outside the rim looking in, ramps spiral round the rings, rails on every lip, light the pit (sun >= 40 deg + fill) |
| Mirrored arena (done: Riverfield Siege) | team PvP, capture | two bases mirrored about a river, 3 crossing lanes | mirror via X(sg,x) / -yaw, chokepoint hero on the axis, cover every ~20 studs |
| Tiered diorama stage (done: Yumori Springs) | social lobby / hangout, menu backdrop | 3-4 flat terraces climbing away from ONE beauty camera, mirrored, hero on the axis | ~130 x 100 walkable, risers 6-8 high with ashlar + pilasters, rails on every lip, water in front of the camera, mountain walls framing, saddle behind the hero |
| Radial ring lagoon (done: Tidehook Lagoon) | fishing / water sim hub | ring boardwalk on stilts round a lagoon, spokes to a central hero, station pads + piers outside | water-first seabed seen through Glass water, rails on every deck edge with cast gaps, reef islets as the frame |
| Linear canyon run (done: Sunspire Canyon Bazaar) | adventure / sim hub, quest trail | one meandering floor walked end to end, sections in a row, side loop over ledges | stepped strata walls with a walkable first shelf, stairs + rope bridge between ledges, hero carved in the end wall on the spawn sightline |
| Orbital ring (done: Shattered Void) | void / space hub, sim lobby | shards on one orbit round a central hero, inward-facing stations, ring road | hero hangs in the middle ~50 up, disc tilted toward the players, mix bridges / jump run / lift so legs differ |
| Open radial dune sea (done: The Gilded Dunes) | open-world sim / treasure hunt | hero in the open centre, POIs on spokes, free roaming, paths as guides | cheap smooth dunes + ripple atlas, ridge ring as frame, pads flattened in `H`, richer dig tiers further out |
| Board-game trail (done: Sugarcrest Kingdom) | sim hub, candy / toy worlds | tile routes (straight spine + winding loops) with round stops at stations, one river crossed differently by each route | tiles as separate draped strips, hills fade near routes, hero on the spine axis framed by an arch from the spawn |
| Underground | mine, cave | carved caverns, tunnels | ceiling + walls everywhere, glow sources as light, no sky |

## Difference table (append to BRIEF.md)
| Axis | This map | Grove | Frostpeak | Sugarworks | Skyrise | +1 Speed | Moon Sweepers |
|---|---|---|---|---|---|---|---|
| Layout grammar | | bowl + radial paths | bowl + street cross | 2x4 plot grid on a boulevard | island chain rising, bridges + zone gates | one straight track, 8 zones in a row | shelf rings stepping down, ramp + airlock per ring |
| Terrain | | rolling hills, rim | snow bowl, pond, plateau | flat plateau, cliffs to sea | floating islands over clouds, no ground | flat track in a stepped block canyon | crater: terraces, risers, sub-craters, central peak |
| Traversal | | walk | walk | walk + plot gates/pads | walk + bridges + gates + teleports, climbing | run straight, gates, wins pads | walk + descend ramps + airlocks + jump pads |
| Scale | | 440 square | 440 square | 300 x 560 strip | ~700 long, 130 studs of height | 144 x 2300 strip | 720 round, 130 studs of descent |
| Kit | | forest props | grove kit re-skinned + cabins | candy-industrial machines | sky islands, sim stations, resource nodes, 4 biomes | Part-built stud kit (no meshes) | retro space-programme tech + lunar geology + junk |
| Look | | warm noon | cold noon | sunset, pink sky | early morning, cool blue | bright stud midday | black starry sky, hard white sun, no haze |
| Hero | | elder tree door | ice spire | Candy Exchange dome | golden Trophy on the summit | finish podium + trophy | rocket on the central peak |

If fewer than 5 rows differ from every earlier column, change the plan before writing code.
