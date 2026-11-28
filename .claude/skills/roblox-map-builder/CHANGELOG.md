# Changelog

## 1.1.0

- **Per-map collision rules**: `collision_rules.json` next to the .blend (or `--collision <file>`) is read before the
  built-in list; map-specific rules no longer live in `roblox_export.py`.
- **Path check**: the default `--path` regex no longer matches `Trailer` (`trail(?!er)`).
- **New example `warehouse`** (Northgate Distribution): photoreal interior with a real-object kit, Roblox materials and a
  render-only Cycles pass (`wh_real.py`), budget-built rack bays, face culling with a hanging-prop exemption.
- **Cave example**: rebuilt ore heaps and cart loads (`cave_ores.py`): ore seams, set-in ore crystals, crystal druses,
  shovel + pickaxe.
- **Photoreal look** section in SKILL.md.

## 1.0.0

First release.

- **Scripted map building in headless Blender**: prop kit + layout script in Roblox space (X east, Y up, Z south,
  1 unit = 1 stud), one height function for ground and placement, paths, districts, a hero landmark, seeded scatter,
  horizon, top-down plans and preview renders.
- **Roblox export** (`scripts/roblox_export.py`): per-prop GLB MeshParts under the Roblox limits, split static
  chunks, AxisProbe orientation piece, a generated idempotent Luau setup ModuleScript (placements, collision, Neon
  glow, lighting), a KitPrep collision script, `manifest.json` and a `report.md` validator.
- **Hard budgets**: whole map, per prop, hero and static-chunk triangle budgets fail the export when exceeded.
- **Placement check**: foliage clipping into solid props or floating above the ground fails the export.
- **Look**: palette strips and palette sheets, value-structured ramps, glow families, Roblox lighting mapping, haze
  rules; optional Roblox materials per object (`--materials`); painted atlases.
- **Quality loop**: close-up prop studio renders, kit sheets, contact sheets, quality checklist and a bug gallery.
- **Trees**: stylised skinned-skeleton trees with overlapping leaf masses, and an opt-in realistic alpha-card method
  (Trunk / Branches / Leaves MeshParts with SurfaceAppearance).
- **Stud / Parts mode** (`scripts/blocks.py`): block-built props written as an `.rbxmx` of Parts.
- **Import routes**: Studio Import 3D, and a Studio-tested route through the Blender "Upload to Roblox" add-on.
- **Examples**: 19 maps (forest bowl, village, tycoon plots, sky islands, zone strip, crater, arena, diorama,
  lagoon, canyon, interior, plots, valley lake, orbital void, cave, city grid, island chain, dune sea, board-game
  trail) plus a realistic tree set, each with brief, scripts, previews and most with a sample export.
