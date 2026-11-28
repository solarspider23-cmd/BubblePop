# Northgate Distribution, a working warehouse (brief)

**Game:** a logistics job sim / hangout inside a real-looking distribution warehouse. Players pick orders in the rack
aisles, drive forklifts across the cross aisle, stage pallets on the dock floor, load trailers backed into the doors and
look out over the floor from the mezzanine office. **Look target: photoreal**, real Roblox materials (Concrete, Asphalt,
Metal, DiamondPlate, Cardboard, WoodPlanks, Rubber, Glass), no stylised shapes.
**Archetype:** OPEN HALL + AISLE GRID + DOCK APRON (new). One huge single-volume steel shed (no rooms, no corridor), 240 x 160,
36 high, a grid of 9 high-bay rack rows with 10-wide aisles, a cross aisle, a dock staging floor, a two-level mezzanine,
and an outdoor truck yard 4 studs below the dock floor.

| Area | Where | What |
|---|---|---|
| Spawn | west end of the cross aisle (-106, 38) facing east | personnel door, safety barriers, the whole cross aisle + crane ahead |
| Cross aisle | z 28..46, full length | forklift lane: yellow lane lines, column line with guards, crane runway overhead |
| HERO | over the cross aisle at x 0 | yellow overhead bridge crane on runways, trolley + hoist, a red shipping container hanging from a spreader |
| Rack aisles | x -116..34, z -76..24 | 8 rack rows (back-to-back double rows + one wall row), 4 beam levels, loaded pallets, wire decks, end-frame protectors |
| Bulk floor | x 44..116, z -26..24 | block-stacked wrapped pallets, IBC totes, drums, mesh stillages, forklift charging bay |
| Mezzanine | x 54..116, z -78..-36, deck y 14 | steel stair, landing, railings + kick plates, glazed site office, parts shelving; packing + conveyor + stretch wrapper under it |
| Dock staging | z 48..78 | 7 dock doors (some open), levelers, bumpers, dock lights, staged pallet lanes, pallet jacks |
| Truck yard | z 80..146 outside | asphalt at y -4, 3 trailers backed in, 1 tractor unit, yard light poles, dumpster, pallet stacks, stair up to the dock |

- **Terrain:** flat slab inside; the yard is one step (4) below the dock floor; no hills.
- **Border (simple):** the building's own clad walls + a weld-mesh fence round the yard.
- **Scale:** human scale (avatar 5.5 = 1.75 m, 1 m ~ 3.14 studs). Pallet 3.8 x 3.1, rack level pitch 4.8, trailer 43 x 8 x 12.5.
- **Palette** (`previews/palette.png`):

| Role | Ramps | Where |
|---|---|---|
| base | concrete `#4e4c47 #8a877f #c2beb4`, cladding `#4a5058 #9aa2aa #d8dde2`, steel `#3c424a #7c858f #c4ccd4`, asphalt `#1b1c1f #323438 #5a5c61` | slab, walls, structure, yard |
| support | cardboard `#5e4222 #a67a48 #d4ac78`, pallet `#4e402c #8f7a58 #c8b48c`, rubber `#0f0f11 #222226 #45454a`, paper `#8e8e8a #d8d8d2 #fafaf6`, glass `#1a2a3a #6a8aa8 #c8dcef` | goods, pallets, tyres, labels, glazing |
| accent | rack blue `#0c2450 #1c4a96 #5a86d8` (dominant), safety yellow `#6a4e00 #dcae08 #ffe46a`, beam orange `#6a2808 #d0581a #ff9a5a` | uprights, forklifts + barriers + lines, beams + crane |
| minor | red `#4a0c0e #a81c20 #ec5a58`, plastic blue `#0c2a46 #2468a6 #86bce8`, green `#14301e #2a6a40 #6aae7a` | fire kit + container, drums + IBC, trailer |
| glow | high-bay LED `#fff3dc` (dominant), skylight `#e4eeff`, beacon amber `#ff8a1a` (accent), dock stop `#ff2a2a` / go `#3aff6a` | lamps, roof lights, forklift beacons, dock signals |

- **Look:** hazy late-afternoon: warm low sun pushing beams through the open dock doors and the skylight strips, cool
  LED high-bays inside, dust in the air (Cycles volume in the photoreal pass; Atmosphere haze in Roblox).
- **Not this:** text, letters, digits or logos on any prop (labels are blank paper patches), real brands, flags, banners,
  stylised / chunky toy shapes, hills or angled cliffs.

## Difference table
| Axis | Northgate | Mic Drop | Starwatch | Inkspill | Rustleaf | Grove / Frostpeak | Sugarworks | Skyrise | +1 Speed | Moon | Riverfield | Yumori | Tidehook | Sunspire | Bloomcrest | Eggstead | Mistvale | Void | Glowroot | Maple Jct | Puffpaw | Dunes | Sugarcrest |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Layout | one hall: aisle grid + cross aisle + dock apron | rooms + corridor | helix tower | S obby | race loop | bowl | plot grid | island chain | strip | shelf rings | mirrored | terraces | ring lagoon | canyon run | round hall + wing | plot rows | valley bowl | orbital ring | cave hub | city grid | islands | radial | tile trails |
| Terrain | slab + sunken truck yard (one 4-stud step) | building floors | summit | desk top | hills | hills | plateau | floating | canyon | crater | river | terraces | seabed | canyon | flat floor | island | lake bowl | shards | cavern | flat | islands | dunes | frosting |
| Traversal | aisles at floor + stair to a mezzanine, drop from docks to the yard | room to room | spiral ramp | obby | drive | walk | walk | bridges | run | ramps | walk | walk | boardwalk | ledges | walk | walk | walk | bridges | walk | walk | bridges | roam | trails |
| Scale | 240 x 160 x 36 high-bay + 66-deep yard | 200 x 140, 16 high | 300 / 165 tall | tiny player | 860 x 460 | 440 | 300 x 560 | 700 | 144 x 2300 | 720 | ~500 | 130 x 100 | ~400 | linear | interior | island | ~400 | ring | cave | city | 560 x 620 | 1,000+ | 530 x 510 |
| Kit | logistics: pallet racking, pallets, boxes, forklifts, crane, trailers, dock doors, IBCs, drums | music gear | astronomy | stationery | motorsport | forest | candy | sky | studs | space | medieval | onsen | stilts | bazaar | lab | farm | shoji | void | fungi | facades | chibi | ruins | confection |
| Look | photoreal hazy late-afternoon sun beams + LED high-bays | night LED | aurora twilight | night lamp | overcast | noon | sunset | morning | midday | space | day | golden hour | day | dusk | interior day | day | spring | night void | underground | late morning | noon | high noon | pastel |
| Hero | overhead bridge crane carrying a shipping container | mixing console | telescope dome | desk lamp | race control | tree | dome | trophy | podium | rocket | spire | pagoda | lighthouse | Petra | chamber | hatchery | islet tree | singularity | lake | town hall | statue | pyramid | castle |

All 7 axes differ from Mic Drop Studios (the only other interior map with ceilings) and >= 6 from every other map.
