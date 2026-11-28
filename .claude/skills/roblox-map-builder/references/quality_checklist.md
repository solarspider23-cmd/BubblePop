# Map quality checklist (run on every render pass)

Each item names the bug it catches and the fix that worked. Perspective shots in `screenshots/`, before/after pairs in `images/` (see `bug_gallery.md`), plans in `layout_patterns.md`.

## Placement / anchoring
- [ ] Nothing floats: look at every prop base on slopes. Fix: `place()` grounds on the min of H over the footprint ring
      (`foot()`), and geometry extends below its origin (trunks, roots, posts).
- [ ] Hero pieces sit on a level plateau, not a slope: `H` lerps to a fixed `*_Y` around them; the path ramps up.
- [ ] Constructed details are SET INTO their host, not pasted on: doorways are boolean-cut (`bool_diff` + `arch_prism`)
      with a framed tunnel and the glow set back inside. Bad: flat glow plate + boxy recess corners on the trunk.
      Good: `screenshots/map_door.jpg`.
- [ ] No overlaps: scatter checks `free()` against `PTS`; hand-placed set pieces append to `PTS`.

## Composition
- [ ] Spawn view frames the hero (`map_spawn.png`): vista corridor kept free of trees.
- [ ] Each district reads from its own camera; cameras reserved before scatter (a camera inside a pine = bug).
- [ ] Forest/wall contains the space; no hard map edge or empty sky from the overview (horizon mountains + skirt).
- [ ] Story groups at bends (odd counts), clumps not sprinkle, paths/plazas clear.

## Look
- [ ] Glow keeps its hue (crystal reads violet, not white): linearised hex, base 0.45x, facing-driven emission.
      Pale/white glow = sRGB fed into a linear input or emission too high under AgX.
- [ ] Haze adds depth without greying everything (density ~0.0005). Thick grey wash = too dense.
- [ ] Ground is not one flat green: canopy shade, path rim, trodden grass, rim darkening.
- [ ] Path edges smooth (ground grid <= 2 studs).
- [ ] Hero is the most saturated mass; ground least saturated.

## Budget (for Roblox import later)
- [ ] `previews/map_stats.json`: total tris and per-kit tris; phone target 300-600k visible. Note what to cut.

## Kit sheet (prop QA) lessons
- [ ] Frame each row automatically from its bounds; stack later rows BEHIND (-Z) so front cameras never look through
      other rows or start inside a prop. Shoot the FRONT (+Z) of buildings - doors face +Z.
- [ ] Gables / boards built with `ngon_prism` then pitched: (-90, 0, 0) puts a triangle's apex UP; (90, 0, 0) hides it
      inside the walls (cabin gables vanished this way).
- [ ] Two-slab roofs need a ridge beam + ridge cap, or the V-gap at the top shows the interior.
- [ ] Chimneys / posts run from the structure they stand on through the roof - never start mid-air.
- [ ] Openings (doors, windows) are gaps in the wall courses or boolean cuts, with the pane/glow set back inside.

## Village / buildings lessons (Frostpeak)
- [ ] Buildings face the street: door = local +Z, use `front_to(x, z, tx, tz)` toward the nearest path point; every
      building gets a level pad in `H` (lerp to h*0.2 within its footprint) so the footing never floats.
- [ ] Door-side dressing (crate, barrel, lantern) must not overlap each other or block the door: keep 1+ stud gaps and
      put the lantern on the opposite side of the door from the props.
- [ ] Slatted / tilted pieces (awnings, roofs): the tilt sign must match the stacking direction, or the slats form a
      sawtooth that reads as separate rails. Check from the side.
- [ ] Reserve camera spots with a radius larger than the biggest canopy (~14), not the trunk spacing.
- [ ] Every structure with a pitched roof (cabins, huts, well, stalls) needs a ridge cap; plain boxes read as low
      quality - give walls boards/courses, corner trims, a framed door, a window, a chimney or stovepipe.

## Tycoon / building lessons (Sugarworks)
- A door boolean on a SOLID drum leaves a flat wall in the opening: hollow the shell first (cylinder minus a smaller one),
  then cut the door. Trim bands are solid discs too: hollow + cut them, or they bar the doorway.
- Rings around a belt / arch must clear the pillars: ring radius < pillar offset - pillar half-width.
- Scan beams / lasers = thin bars, never a panel across the path (reads as a wall).
- Plots: build ONE plot function in plot-local coords (`local()`), place it N times; never hand-place per plot.
- Review camera spots against buildings too (a shot started inside a gate pillar); keep cams on roads/plazas.
- Heavy haze at sunset turns everything mauve: density ~0.00015 with a warm tint.

## Palette lessons (Sugarworks colour pass)
- Large pale floors pick up the sky: pink tiles under a blue sky read lilac. Use warm floors (butter / cream / caramel)
  under a cool sky, set the palette material matte (Specular IOR Level ~0.12, Roughness ~0.95), keep world strength ~0.55.
- Name the material of every surface (caramel cliffs, mint walkways, butter tiles): it keeps the palette on-theme.
- One saturated accent family per object, pale bases for big areas, darkest values only on small trim and asphalt.

## Roblox compatibility (run before export, then read roblox/report.md)
- [ ] Every prop: origin bottom centre (pivot), front -Z, unique name per variant, one solid mesh + glow meshes only.
- [ ] No mesh over 20,000 tris or 2,048 studs (exporter splits static meshes; props must be fixed in the kit).
- [ ] Colours only from the palette strip; UVs in 0..1; no alpha, no photo textures, no text in meshes.
- [ ] Collision kind sensible per prop (`COLLISION` regexes in roblox_export.py): decor `none`, boxes `box`,
      walkable/enterable `precise`. Check the table in report.md.
- [ ] Placed tris and part counts inside the phone budget (report.md); cut far dressing first.
- [ ] After import: AxisProbe check done, `M.YAW_FIX` set; `Build()` run twice gives one root; Studio screenshot
      compared with previews/map_spawn.png after `ApplyLook()`.

Images of the common bugs: `bug_gallery.md`.

## Sky map lessons (Skyrise)
- [ ] For floating maps the sky BELOW the horizon is visible: the sky ramp must stay blue below 0 (map from -0.5),
      or the void between islands reads beige/grey.
- [ ] High clouds and floating rocks kept away from camera spots and bridge lines (an overview started inside a cloud).
- [ ] Zone barriers are see-through bars, not solid panels; price plate + padlock face the approaching player.
- [ ] Every island underside is modelled and broken up (strata, hanging rocks, vines, crystals): it is seen from
      bridges and from the islands above.
- [ ] Walkable statics (island tops, paving, bridges) export as `precise`; path stones / lava cracks as `none`.

## Model quality (Skyrise rebuild)
- [ ] Every prop judged in `prop_studio.py` close-ups before map use (front + back, 700-900 px).
- [ ] No prop is only primitives: every part bevelled; base + body + top detail; 3+ palette colours; secondary detail.
- [ ] Joints are joints: arms meet trunks with an elbow / collar, lids sit on hinges, posts have footings and caps.
- [ ] Nothing floats or pokes through: snow caps follow the cone face, pebbles half-buried, boulders pushed out enough
      to read but still touching.
- [ ] Repeated props stay cheap: coins / leaves / planks at 8-12 sides; check total tris after each upgrade
      (coin piles went from 5.6k to ~1.5k tris without visible loss).

## Detail pass lessons (Skyrise)
- [ ] Render ground-level close-ups of every district (camera ~8-20 studs up) and look for bare ground, empty plazas
      and plain decks: that is where a map reads as cheap, not in the overview.
- [ ] Micro detail is clumped, biome-specific, off paths, collision `none`, and cheap (<350 tris each).
- [ ] Path colouring never follows ground faces (stair steps): use overlapping decal blobs.
- [ ] Re-check total tris after a detail pass (Skyrise: 485k -> 620k, trimmed to ~565k placed / 613k exported by
      lighter clouds, fewer balusters, simpler flowers).

## Stud / Parts maps (+1 Speed Run)
- [ ] Match the target game: read its Part sizes, materials and MaterialVariant (ColorMap, StudsPerTile) read-only
      first; reuse its stud texture via the setup snippet, never invent asset ids.
- [ ] Translucent veils: Roblox Transparency ~0.8; the Blender preview material must be faint (alpha ~0.12) or every
      shot looking through a gate turns into fog. Never place review cameras just behind a veil.
- [ ] Floors need contrast between checker tones (~0.2 apart in the ramp) plus lane lines, or the track reads as one flat
      colour from player height.
- [ ] Hide the outside of the canyon: outer plates up to the tier height (no grey gap beside the top tier).
- [ ] Part count: 7.6k for 2,300 studs of track + hub is comfortable; group Parts in Folders per zone so streaming can
      unload them.
- [ ] Material tokens in .rbxmx are Enum values: Glacier = 1552 (1056 is DiamondPlate - a wrong token gives the
      diamond-plate look instead of studs). Verified by inserting PlusSpeed.rbxmx into a test place (2026-11-17).
- [ ] After inserting, run the setup snippet so MaterialVariant "Studs" exists; without it Glacier shows its default look.
- [ ] No bare blocks: every Part-built prop has a plinth / trims / chamfers, round parts where things are round, framed
      panels, light fittings with cages and roofs, and real display items. Shop goods are never plain coloured cubes.
- [ ] Translucent Neon (light columns, portal discs) must render faint in the preview (blocks.mesh_blocks sends tr > 0.05
      to the clear material even for Neon) or the preview lies about the look.

## Export naming (found during the Skyrise stud skin)
- [ ] Exported MeshPart names have no `.001` suffixes (the exporter's `newobj` guarantees it; check the Setup module's
      `M.PartColor` / glow keys if you edit the exporter).
- [ ] No text built from Parts (no pixel letters, words or digits): labels are GUIs. Icons only.
- [ ] Every hero prop has a concept (one readable idea tied to the game's theme), not a checklist of parts.
- [ ] Pixel-art / shaped props face the side players see them from (check the render from the spawn / hub side).

## Crater / space lessons (Moon Sweepers)
- [ ] `pro_lib.box()` is CENTRED: a tall leg / glow strip built with `box((w, H, d))` at y = 0 sinks half its height
      below the prop (launch-tower legs, airlock glow strips). Place at `y + H / 2`.
- [ ] Lathed bowls / hoppers: end the profile by coming back down inside (`..., (r_rim, top), (r_in, top - .7), ...,
      (0, floor)`), or the last ring gets capped and hides whatever glows inside.
- [ ] A hex prism's vertex points along +X when `rot0 = 0`: use `rot0 = pi / 6` when a flat face must face +-X
      (pylon stripes poked past the edge otherwise).
- [ ] Two round windows + a bar above on a capsule read as a face: one hatch + side ports instead; check the front view.
- [ ] Pitch a window ring to the surface it sits on (cone slope `atan(dr / dy)`, sign: `90 + pitch` with pitch > 0 tips
      the normal up) and put it at the surface radius for that height, or it is buried.
- [ ] Terraces / pits with a low sun (< 30 deg) render black inside: shelves 40 wide below a 20-stud riser are fully
      shadowed. Sun >= 40 deg + a shadowless fill sun (named after the key sun; the exporter reads the first SUN), and
      riser strata >= 0.45 shade.
- [ ] Mess / collectables at map scale: give them ~1.5x their close-up size and a lighter or glowing read, or they
      vanish at 30+ studs.
- [ ] Rails along curves: quantise segment lengths (`int(L * 10)` key) to keep kit variants few; each length is a prop.
- [ ] Faces of a polar ground grid are long at large r: noise-based colour patches need a big noise scale (>= 25) and
      low contrast, or they turn into a jagged cog pattern.
- [ ] Sky objects (Earth, moons) must stay inside 2,048 studs: shrink + move closer with the same angular size.
- [ ] Blender's bundled Python has no PIL: build contact sheets with `scripts/contact_sheet.py` and system Python.


## Arena / castle lessons (Riverfield Siege)
- [ ] Ground colour per FACE with different palette columns makes sawtooth edges on slopes and shores: keep one column
      (grass) and vary the value per VERTEX; give the ground smooth normals; rocks on slopes are props.
- [ ] Roads painted on ground faces stair-step: lay them as ribbon meshes draped on H (+0.1) with noisy widths.
- [ ] An ashlar panel turned 180 mirrors its x: evaluate asymmetric opening masks at -x; test block overlap (3 points),
      not the block centre, or long blocks cover slits / windows.
- [ ] Mirrored scatter: check free() with the MIRRORED position, or the second side loses most of its props.
- [ ] A world-volume haze renders black in EEVEE: use a large haze cube (density ~0.0002).
- [ ] Triangle cuts that cost no look (Riverfield 887k -> 589k): coarser ground grid once it has smooth normals +
      per-vertex shading + ribbon roads (2.4 -> 3.0), bigger ashlar blocks (4.0 x 1.9), unbevelled merlons / slats /
      corbels, one wattle wall per trench, fewer grass tufts (props instead of ground detail), trees 120 -> 48 per side.

## Diorama / roof lessons (Yumori Springs)
- [ ] A roof lofted from the eave inward can sit BELOW the wall top at the wall line: wall tops poke through as white
      zigzags. Start the eave at the wall top (y - 0.1) or raise the skirt's inner height; check a roof close-up.
- [ ] Place() grounds on the lowest footprint point: props on a narrow islet / ledge sink into the water. Pass y=.
- [ ] One beauty camera: keep the foreground short (water, not 60 studs of flat grass), frame with crags at the
      corners, open a saddle behind the hero so the horizon peaks / sky show.
- [ ] EEVEE volumes stop at `volumetric_end` (100 by default): set it to the scene depth or steam / haze vanish.

