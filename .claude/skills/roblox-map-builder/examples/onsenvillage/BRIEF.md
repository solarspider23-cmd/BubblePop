# Yumori Springs (brief)

**Game:** social hangout / lobby (hot-spring village): bathe, eat noodles, climb to the pagoda. One stage, made to
read from one beauty camera, following the diorama-stage style guide (`references/coastal_town_look.md`):
that look and composition, new setting.

**Archetype:** **tiered diorama stage** (new): a small stage (~132 x 100 walkable) seen from one low camera over the
water (vertical FOV 35), stacked in tiers that climb AWAY from the camera and mirrored about x = 0.

| Tier | Where (z) | Height | What is there |
|---|---|---|---|
| Pool in front + islet | z 52..66 islet, water to the camera | islet y 1.6, water 0 | spawn, two natural rock pools, stepping stones, maple |
| Stream | z 36..53 | water 0, bed -2.5 | cedar footbridge with lantern posts |
| Bath Terrace (T1) | z 14..36 | y 4.5 | two steaming pools under teal pavilions, torii at the bridge head |
| Market Terrace (T2) | z -12..14 | y 11 | persimmon-roof shops, noodle stall, sake casks, koi pond |
| Upper Terrace (T3) | z -50..-12 | y 19 | indigo inns, tall plum houses (to y 45), the five-tier pagoda on the axis |

- **Links:** footbridge (islet > T1), centre stone flight (T1 > T2), two side flights at x = +-38 (T2 > T3).
- **Spawn:** islet (0, 1.6, 60) facing -Z: the bridge, torii, centre stair and pagoda line up on one axis.
- **Hero:** five-tier bathhouse pagoda (teal copper roofs, bronze nine-ring spire), top ~y 62.
- **Frame:** grey-violet mountain walls on both sides and behind (a saddle behind the pagoda lets distant snow peaks
  show), cedars and pruned pines behind the houses, framing crags at the front corners in the water.
- **Palette:** cream plaster / paving, sand ashlar, dark cedar, pale sage foliage. Saturated colour ONLY on 4 roof
  glazes (teal: pagoda + 2 pavilions, indigo: 2 inns, plum: 2 tall houses, persimmon: 2 shops) + 3 autumn maples.
- **Signature edge detail:** cedar railing bays with bronze onion caps (giboshi) on every terrace lip, bridge and
  balcony; stone lanterns (toro) at every gap. Shared base: sand-ashlar plinth with a chamfered cap.
- **Look:** golden hour: sun 17 deg from the south-west, peach > pink > violet sky, thin pink haze, cool violet
  shadows, warm lantern glow (emissive + small PointLights), steam over the pools (preview volumes / Roblox particles).
- **Not this:** another harbour, flags / banners / pennants / noren with writing, text in meshes, studs, Parts mode,
  even scatter, more than 4 roof colours.

## Difference table
| Axis | Yumori Springs | Riverfield Siege | Moon Sweepers | Skyrise | Grove / Frostpeak |
|---|---|---|---|---|---|
| Layout grammar | tiered stage on one axis, mirrored, seen from one camera | mirrored arena, 3 lanes | shelf rings down to a peak | island chain | bowl + radial paths |
| Terrain | flat terraces with ashlar risers in a mountain notch, stream + pool | river valley, plateaus | crater terraces | floating islands | hills / snow bowl |
| Traversal | climb: bridge + 3 stair flights | walk + ramparts + wading | ramps + airlocks | bridges + gates | walk |
| Scale | 132 x 100 walkable (smallest) | 640 x 400 | 720 round | ~700 long | 440 square |
| Kit | Japanese onsen town: pagoda, inns, pools, lanterns, stalls | medieval siege | retro space junk | sim stations | forest props |
| Look | golden hour, pink haze, violet shadows | storm-break dusk | black space | cool morning | noon |
| Hero | five-tier pagoda | bridge tower | rocket | trophy | tree / spire |
