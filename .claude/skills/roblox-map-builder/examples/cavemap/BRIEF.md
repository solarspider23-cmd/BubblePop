# Glowroot Caverns (brief)

**Game:** cave / mining adventure hub: spawn in the Great Hollow, mine ore and crystal nodes, ride the rails, sell at the
Ore Exchange, upgrade at the Crystal Forge, take quests at the miners' camp, brew at the Spore Brewery, and take the
Deep-Dive Elevator down to deeper levels. **Archetype: Underground / branching rooms** (first underground map).

| Area | What is there |
|---|---|
| Great Hollow (centre, ~200 x 165, vault ~95 high) | glowing turquoise lake (lobes reaching the NW wall), islet with **The Glowroot** (hero), plank bridge from the south shore to it, sunbeam through the only opening (a slanted shaft in the vault) landing on the Glowroot heart, ceiling waterfall in the NW lobe, geodes round the shore, mining scaffold on the east wall, rail depot |
| West tunnel -> Quest Camp grotto | canvas tent, campfire with pot, log seats, quest board (blank papers) |
| East tunnel -> Ore Exchange grotto | mine-office shed with counter, ore scale, ore shelves, blank sign board; rail line 1 ends here |
| NE tunnel -> Crystal Forge grotto | ashlar kiln + chimney, anvil, crystal hopper, quench trough; rail line 2 ends here |
| North tunnel -> Lift grotto | rope bridge over a chasm, timber headframe, cage over a real shaft (Deep-Dive Elevator) |
| SW tunnel -> Spore Brewery grotto | cauldron under its own giant mushroom, jar shelf, giant glowing mushrooms |

- **Spawn:** south alcove dais (0, 60) facing north: lake, bridge, Glowroot, sunbeam, falls (left), scaffold (right), all
  five tunnel mouths framed by lit timber sets.
- **Palette** (swatch sheet `previews/palette.png`, source `cave_palette.py`; defined BEFORE the polish build):

| Role | Ramp / glow | Hex (dark / mid / light) |
|---|---|---|
| Rock (value ramp) | teal-slate shadow -> mauve -> warm lit face | #1a2a30 / #5b4d56 / #b9957f |
| Moss (ledges only) | sage | #1f2e26 / #57704f / #a3b98b |
| Floor (readable mid tone) | cave earth | #2c241e / #6c5a47 / #ad967a |
| Shore / water | silt, turquoise | #3e4644 / #8c9286 / #d4d4c0 ; #04343c / #0e9ca2 / #9cf0e6 |
| Timber / bark / iron | mine timber, Glowroot bark, iron | #6e4a2c ; #43322a ; #3c424a (mids) |
| DOMINANT glow (teal-cyan) | crystals, lake bed, fungus gills, veins, vine bulbs, glow-worms, falls | #2ee6e0, #2af0dc, #46f0cc, #a6fbea, #8cf0dc, #cffaff |
| ACCENT (amber) | the Heart, lanterns, sunbeam | #ffa43a, #ffbe68, sun #ffd59a |
| Grotto accents | Forge + Camp firelight / Elevator cool white / Brewery magenta (only violet) | #ff7a26 / #e6f2ff / #ff6fd0 + #d070ff |
| Ambient | low cool, never black | #101422 |

  Value structure: walls darker than the mid-tone floor, vault darkest but rim-toned on every rib, brightest = the Heart
  in the sunbeam and the lake. No lime, no random violet in the hall.
- **Signature:** one enclosed rock shell (voxel-remeshed union of air ellipsoids, displaced into strata ribs) + layered
  rounded rocks lining every wall foot; banded crystal columns erupting from cracked geodes; glow-root vines.
- **Look:** dark cave, colour from glow; one warm sunbeam; dusty haze; cool low ambient.
- **Not this:** obsidian shards in a void and hex shafts (Shattered Void), daylight valley bowl (Mistvale), text or
  banners in geometry, floating lumps.

## Difference table
| Axis | Glowroot Caverns | Shattered Void | Mistvale Lake | Bloomcrest |
|---|---|---|---|---|
| Layout grammar | hub cavern + 5 branching tunnels to grottos | orbital ring of shards | bowl round a lake | round hall + wing |
| Terrain | enclosed rock shell, vault, chasm, shaft | floating islands, void | flat floor, rock tiers, sky | building interior |
| Traversal | walk tunnels, rope bridge over a chasm, plank bridge, rails, elevator | bridges, jump run, lift | shore walk, dock | walk |
| Scale | ~450 x 400, vault 95 | ~400 ring | 330 x 380 | ~150 |
| Kit | layered cave rock, dripstone, geodes, glow fungi, glow vines, mine timber, rails, carts, headframe | obsidian, rune ruins | moss rocks, shoji houses | lab furniture |
| Look | dark + coloured glow + warm sunbeam | night void, violet | cyan daylight | bright interior |
| Hero | The Glowroot (root pillar vault -> islet, amber heart) under the sunbeam | black-hole singularity | waterfall + islet tree | Bloom Chamber |
