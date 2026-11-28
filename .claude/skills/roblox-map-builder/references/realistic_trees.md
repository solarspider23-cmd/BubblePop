# Realistic alpha-card trees (opt-in exception)

The skill's default is "no alpha cards, palette strip only" (`stylised_trees.md`). Use this method ONLY when semi-realistic trees
are requested (for example to match a reference that uses alpha cards). It is an exception, not the new default.

Worked code: `examples/oaktrees/gen_trees.py` (+ README.md there).
One headless Blender run builds geometry, textures, GLBs and turntable contact sheets for 4 trees in ~15 s.

## Structure (classic Studio-style oak: three MeshParts)
- 3 MeshParts per tree, one origin (trunk base): `Trunk` (solid bark tubes, SurfaceAppearance AlphaMode Overlay),
  `Branches` (crossed twig cards, AlphaMode Transparency), `Leaves` (leaf-cluster cards, AlphaMode Transparency).
- Import the combined `<Tree>.glb` (parts stay aligned); per-part GLBs are for re-imports.
- Cards double-sided (glTF doubleSided; check DoubleSided after import), no collision on cards.

## What made it read right
- Skeleton: recursive levels (trunk, 4-7 limbs, secondary, tertiary), droop + phototropism + wander, and EVERY branch
  length fitted inside a lumpy ellipsoid crown envelope: the envelope sets the silhouette, so a new species = a new
  envelope + level table.
- Leaves: folded quads (4 tris), spacing ~0.4 studs along outer branches + 4 at tips, size 2.8-4 studs on a 27-stud oak,
  normal = 0.9 outward + 0.22 up + 0.38 random (more up-bias gives streaky edge-on cards from the side), bent vertex
  normals toward the crown surface, 3D-noise gaps (`gap_t` ~ -0.2) for sky holes, no cards below the crown base (`zmin`).
- Atlas: 4 x 4 clusters on a curved stem, ~45% filler leaves so clusters are round, not feather-shaped.
- Textures in numpy inside Blender: periodic FFT noise is tileable for free (stretch fx/fy for ridges or lenticels);
  bleed colour under alpha=0 pixels.
- Density reference: OakA ~3k leaf tris + 4.5k trunk; a 20k MeshPart cap leaves plenty of room.

## Failures seen
- First pass: too few cards (170) -> bare twig skeleton. Second: 1,400 cards with per-spot doubling -> one dark blob
  hanging to the ground. Fix = crown base cut + moderate density + a short central leader to fill the dome top.

## Conifers (fir / spruce) - `kind="conifer"` in gen_trees.py (PineA tall, PineB fuller, PineC cheap background)
A conifer is NOT the broadleaf recursion with a cone envelope. Build it directly:
- Trunk: one straight tube to the very top (radius tapers to ~6%), bark `fir` (scaly grey-brown plates, reddish cracks:
  FFT noise fx 16 / fy 11 plates minus an |noise - 0.5| crack line).
- Whorls: every `dz` ~1.3-2.3 studs (shrinking toward the top), 4-6 branches each, golden-angle phase between whorls.
  Branch length = `Lmax * (1 - t)^Lexp + Lmin` (t = 0 lowest whorl .. 1 top) = the cone. Elevation -12 deg at the
  bottom to +42 deg at the top: low branches droop, the top ones point up (a flat top whorl reads frayed, like a palm).
  Branches droop + a little phototropism so tips turn up.
- Laterals: paired side sprays in the branch's horizontal plane (`branch_dir x UP`), shorter toward the tip. They get
  NO tubes (`tube_max=2`): they exist only to carry cards. Branch tubes 3 sides, 3 segments (they hide under needles).
- Needle atlas (`needle_atlas`, 4 x 4 x 256 px): a central twig with 7-9 paired laterals, the frond widest near the base
  and filling the cell edge to edge; needles = short tapered strokes on both sides of every twig every ~3 px, angled
  forward 25-70 deg, a shadowed under-layer (x0.6) then the lit top layer; new growth = the last 25% of each twig lerped to
  a lighter blue-green. Colour: dark blue-green (0.08, 0.21, 0.17) with tips (0.24, 0.42, 0.33).
- Cards (`conifer_cards`): along every branch and lateral (spacing 0.8-1.2): most lie IN the spray plane (normal = up
  rotated off the branch + 0.45 outward, up axis = branch direction, slight ridge fold), ~35% hang under the branch
  facing out of the cone (pendulous spruce curtains: they give the side view its mass), spray size bigger low down,
  tip cards and top sprays shrunk to 50-85%; bent normals toward the cone surface; 2-3 crossed narrow cards make the
  leader spike. Bare twig cards (Branches part) only on inner lower branches.
- Iteration log (turntables, 4 rounds): r1 fronds filled 40% of the cell and needles were dark grey -> a skeletal
  "dead Christmas tree"; r2 wider fronds + bigger cards + brighter needles = believable fir, but the top was frayed
  and the trunk 2.9k; r3 top sprays scaled down, slimmer spike, 3-sided branch tubes (trunk 1.9k); r4 irregular
  needle angles / lateral lengths (less fern-like), top whorls angled up.
- Costs: PineA 7.5k / PineB 7.4k (5.4k of it needle cards), PineC 3.1k. Use A/B near the camera, C for skylines.

## Hero broadleaf (OakHero) and map grades
- Lean = trunk `lean` (1.05, 0.12, 0) + `photo` 0.075 so it curves back up; `gnarl` 0.2 = trunk radius noise; crown
  envelope centred out over the lean; `spread_dir` pushes the limbs that way. Surface roots (`trunk.roots`): 8 tubes leave
  the foot outward-down, snake along a noisy floor at z ~ -0.3 and dive their tips to -0.7 (else they end in the air
  like claws). In the map, a yaw search turns the leaves' centroid toward the open water.
- Raw atlas greens are physically dark: in a saturated stylised map they read black. Grade per map (`TINTS`:
  leaf gain ~1.3-2.3 per channel + saturation 1.2-1.35, bark gain ~1.1); check in the map's own light, not on the
  turntable.

## In a map (budget)
- Kit: `GT.make_tree(species, KIT, prefix='Tree', tex=grade)` -> three meshes on one origin, each its own kit prop
  (`Tree<S>_Trunk` hull, `_Branches` / `_Leaves` collision none), placed with one matrix. Name them `Tree*` so the
  placement check treats them as foliage and skips the float test on the cards.
- They cost 5-20x the stylised trees: Mistvale Lake went from 39 + 18 stylised trees to 25 realistic ones (106k) by
  cutting cliff-shelf firs to one in four, halving undergrowth, and using PineC for every far slot; Maple Junction
  went from 37 faceted trees to 25 (49k) by planting every other sidewalk slot and using 1.6-2k StreetOak /
  StreetBirch. Scale is free: grow the hero and far firs with `s` instead of adding copies.
