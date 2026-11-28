# Diorama stage look (coastal-town style guide)

How a small stylised town map built from a Blender kit reads as "designed" in Roblox. Use it for any compact hub
seen mainly from one direction (harbour, onsen village, mountain town). The numbers are starting points, not rules.

## Organising the place
- Placements live in data (JSON); one idempotent setup script tags what it made (attribute), moves replaced things
  to a `Before*` folder instead of deleting, and rebuilds cleanly on rerun.
- One MeshPart per material slot (`tree__wood`, `tree__leaf`) with fixed rules per slot: leaf / glow / water never
  collide, trunks and rocks Hull or Box, Precise only for walkable pieces. CanTouch off everywhere; set
  CollisionFidelity after parenting.
- Heavy reuse: a few dozen prop types, each set-dressing prop used several times; heroes 1-3 copies.
- Colour from a few shared swatch maps (one per material) tinted per part; glow from an emissive SurfaceAppearance
  plus tiny invisible PointLights (range ~8, brightness ~0.6, no shadows) instead of Neon everywhere.
- Mesh ground (no terrain); horizon = a few huge flat tiles (each <= 2048 studs).
- Lighting matched to a Blender target render (Future, low warm sun, light Atmosphere, gentle Bloom and Contrast),
  skybox rendered from the same Blender scene.

## Composition
- **A stage, not a field.** One small diorama (~130 x 100 walkable) seen from one beauty camera (narrow FOV ~35, low,
  from the open side). It climbs in tiers: water > quay > terrace > upper terrace > buildings. Each level is one read;
  stairs tie them together.
- **Mirrored symmetry about one axis.** Houses, lamps, benches and stairs in pairs round a central tower; a few props
  break the symmetry so it does not look stamped.
- **Frame and backdrop:** big cool-grey rocks wrap the sides and back, trees stand behind the buildings, so the eye
  stays on the centre; a flat sea tile closes the horizon.
- **Detail rhythm:** edges repeat short modules (quay blocks, railing bays, parapets, planters, lanterns). Small
  stories (boat, crane, nets, stall, crates, barrels) sit in clusters of 2-4 at stairs and jetties. Nothing is
  scattered evenly.

## Palette
- Warm near-white creams for paving and plaster, sand-coloured stone, dark brown wood, pale sage leaves.
- The ONLY saturated colours are the roofs: 3-4 accents (e.g. brick red, orange, violet, blue), each used at least
  twice. Green appears once or twice as a grass strip, not as a base colour.

## Light and mood
- A warm low sun and a pink-violet haze; blue-violet ambient and cool shadows, so the warm creams read against cool
  shade.
- Very little glow (lanterns only, emissive + a small PointLight).
- Few material slots (~10: glow, leaf, paving, plaster, rock, roof, stone, trim, water, wood), each a swatch picture
  plus an optional normal map; the per-part tint is the mesh's mean vertex colour.
