# Mistvale Lake (brief)

**Game:** cosy fishing / hangout hub in a hidden valley: spawn on the beach, fish off the dock, shop at the market
stalls, explore to the waterfall. Built to match a reference image (a reference overrides the
"maps must differ" rule for look + composition; the kit, layout grammar and palette are still new).

**Archetype:** **valley bowl around a lake**: a FLAT natural floor (no terraces as the stage) fully wrapped by towering
tiers of big rounded rock masses. Rim superellipse 166 x 188 round (0, 15); tiers step ~35 out / ~25 up, up to 6 tiers
(~150 high) at the back, 2 behind the camera.

| Area | What is there |
|---|---|
| centre / south-east | turquoise lake (shore radius 54-98 round (15, 35)), lily pads, reeds, the grassy islet (62, 76) with the leaning gnarled tree (hero 1) |
| west shore | wide curving pale beach, the fishing dock (spawn beside it), lantern posts, the cherry tree, big longhouse + Inn sign |
| west / north-west | the village: dark slate-blue gable-roof timber houses with shoji walls, white storehouses, lantern rope lines on tall poles |
| north-west back path | the market square: 4 stalls (stations) + crates |
| north | the stream from the waterfall cleft (48, -192) (hero 2) to the lake, footbridge, stepping stones |
| north-east | raised terrace (y 8) behind fieldstone retaining walls with a stair, houses and pines |
| east | a longhouse and a town house on the shore, trees |

- **Spawn:** west beach (-60, 1.3, 66) facing the dock; the lake, islet tree and waterfall are all in view.
- **Palette:** cool blue-grey rock, saturated moss / grass greens, pale cream sand, azure-turquoise water, dark timber,
  shoji cream, slate-blue roofs; accents = lantern red, one pink cherry, violet flowers.
- **Signature:** a SOLID wall of big carved rock masses (superellipsoid + soft-flattened cut planes, flat bedded
  bottoms, rim highlights on convex edges, moss only on top ledges) stacked on a dark painted rock backing slope, huge
  at the foot, smaller up top, grounded on the lowest point of their footprint. Everything wears ONE hand-painted-look
  1024 atlas (`paint.py`) except the trees: realistic alpha-card trees from `examples/oaktrees/gen_trees.py` (leaning
  gnarled hero oak with roots on the islet, oaks, saplings, a pink-flowering oak, blue-green firs), own textures graded for the cyan light.
- **Look:** bright cyan-blue daylight, sun high from the south-west, strong blue haze turning far tiers pale cyan,
  saturated water with glints, glowing motes, soft bloom.
- **Not this:** tiered terrace stage, upturned hip roofs, golden hour (Yumori Springs); flags / banners; text in
  geometry (station names = GUIs on the blank sign boards).

## Difference table (vs the nearest earlier map)
| Axis | Mistvale Lake | Yumori Springs |
|---|---|---|
| Layout grammar | flat bowl round a lake, organic shore paths | tiered stage on one mirrored axis |
| Terrain | flat valley floor + modelled rounded-rock cliff tiers | stepped ashlar terraces in a mountain notch |
| Traversal | walk the shore, dock, bridge, one terrace stair | climb terrace stairs |
| Scale | ~330 x 380 bowl | 132 x 100 |
| Kit | rounded moss rocks, gable timber-and-shoji houses, stalls, rope lantern lines, dock | onsen town: hip roofs, pagoda, bath pools |
| Look | cyan daylight, blue haze | golden hour, pink haze |
| Hero | waterfall + leaning islet tree | five-tier pagoda |
