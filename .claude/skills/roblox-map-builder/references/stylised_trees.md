# How to build a good stylised tree (method that worked on Mistvale Lake)

Worked code: `examples/valleylake/valley_props.py` (`Skel`, `skin_mesh`, `bark`, `roots`, `leaf_mass`,
`gnarled_tree`, `broadleaf`), turntable `examples/valleylake/turntable.py` + `turn.sh`.

## What failed first (don't do this)
- One tube for the trunk + spike roots: a stiff pipe, roots read as fins / spikes.
- Canopy = 2-3 spheres with leaf cards on a golden-spiral grid: the regular placement reads as pinecone / artichoke
  scales. Spheres side by side read as separate balls (two "lollipops"), not one crown.

## Trunk: a branching skeleton through Blender's Skin modifier
1. Build a skeleton: nodes `(position, radius)` + edges (`Skel.add`, `Skel.grow` for curved, tapering, slightly
   wobbling limbs). Hero: thick base (r ~0.13 h) -> 6 trunk nodes leaning and twisting -> 4 limbs (3 segments) that
   each split into 2 branches (2 segments) ending UNDER where the leaf masses will sit, + a top leader.
2. `skin_mesh`: Skin modifier (per-node radius, root on node 0, branch_smoothing 0.6) + Subdivision (2 for a hero,
   1 for filler trees), evaluate, read back as bmesh. Junctions come out smooth and welded.
3. Roots: 5-7 chains from the base that start ON the flare, run out low along the ground and end below it (y < 0):
   radius 0.8 -> 0.22 of the root start. On filler trees start them from the first trunk node and dip them down
   (`lift=-.6`): starting at the base node with many edges can break the skin hull (gaps).
4. `bark`: displace along the normal by noise stretched along Y (long vertical furrows), shade dark in the furrows,
   lighter on ridges and toward the top. Keep the painted wood block low-contrast: triplanar per-face texture
   projection on a smooth organic mesh shows as patchwork if the texture has strong strokes.

## Canopy: overlapping leaf MASSES, not balls
1. Put one mass on every branch tip (radius 0.13-0.26 h, varied), lifted a little and jittered.
2. Pull all mass centres ~55% toward one crown height (one canopy layer), then bridge each mass to its nearest
   neighbour with a filler where they are more than 0.7 x (r1 + r2) apart, and add one big crown core over the hub.
   This turns separate balls into ONE irregular, asymmetric silhouette while branches still show between masses.
3. Each mass (`leaf_mass`): a displaced core blob (icosphere, lump noise) shaded dark (interior shadow) + many small
   leaf cards (4-vert pointed diamonds, 2 tris, single-sided, facing out) at RANDOM spots on the blob: gaussian
   directions (few underneath), random roll, random size, pointing out and drooping. Density ~4-5 x r^2 leaves.
4. Shade per vertex: height ramp dark -> bright, the leaf tip vertex +0.16, the top of each mass brighter (lit rim),
   the underside darker. The painted leaf block of the atlas adds the brush detail.
5. Budget: hero ~25k tris = trunk 17k + canopy 7k. A Roblox MeshPart is capped at 20k tris, so split a hero tree
   into two props sharing one origin (`GnarledTree` trunk + `GnarledCanopy`, canopy collision none). Filler
   broadleaf ~3-4.6k: Subdivision 1, 3-4 limbs, 4 roots, leaf density ~0.9.

## Conifer (pine): needle-branch cards on drooping core skirts
- Failed: tiers of flat star-shaped spikes or lathe discs = "stacked flat green slabs".
- Worked (`pine` in valley_props.py, ~1k tris): a thin tapered trunk; 9 overlapping tiers, each = a dark smooth
  drooping core skirt (4-point lathe, 8 sides, tall: dr ~ 0.95 R so tiers interlock) + a ring of 8-17 long
  needle-branch cards (pointed, folded on a raised spine, drooping 20-30 deg, random angle / length / height inside
  the tier, bright tips). Bottom tier starts at ~0.2 h so a bit of trunk shows. The ragged card tips give the soft
  scalloped conifer silhouette.

## Fuller broadleaf crowns
Same merge as the hero (`merged_crown`): tip masses pulled ~45% toward one height, nearest-neighbour fillers, a crown
core 0.26 h over the hub. Never leave a lone mass on a long limb: from some side it reads as a floating canopy piece.

## Placement (the exporter's hard check fails trees inside rock or floating)
- Place foliage LAST, after every rock / wall / building (the map script defers soft props), then test each one
  against a BVH of the real solid geometry with the exporter's own test (`clip_fail` in valley_map.py: body points
  inside a closed solid, lowest point vs the surface under the trunk) at a stricter threshold (4% inside, 0.8 float).
- On failure try up to 8 jittered spots nearby, else drop it. Big tier-0 cliff rocks spill 30-40 studs into the
  valley, so a terrain-only height function happily plants trees inside them.
- Cliff-top trees: raycast down onto the solid geometry and accept only flat ledges (normal up > 0.85), stand the tree
  on the hit point. Never place on a cliff face.

## Review loop
Render a 4-angle turntable (`turn.sh <out> "gnarled_tree()"`) every round and look for: balls reading separately
from any side, scale patterns, trunk facets, roots floating or detached, the crown too small for the trunk. Six rounds
were needed for the hero, three to four for the broadleaf.
