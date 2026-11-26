# BubblePop art review: the candy lobby (batches A to D)

Written 2026-11-26 by the art director. Reviewed against `docs/art_plan.md` section 4 and the art direction.

How it was checked: I opened the preview pictures, read every `bounds.json`, measured the textures, and
checked the fits with numbers (gumball piles against the globe and jar, pads against the machine, island
against the glass dome). I did not run Blender or Studio, so nothing here has been seen in the game yet.
The "Clean Pop Plaza" set in `art/hub_clean/` is not part of this review.

## Short version

- **26 models reviewed: 16 ACCEPT, 9 ACCEPT WITH NOTE, 1 REJECT** (the clouds).
- Nothing needs rebuilding before upload. The notes are small polish jobs.
- The one real problem is a **layout** problem, not an art problem: the two middle play pads and their
  signs run into the gumball machine's round stage. Moving the pads 5 studs forward fixes it.
- The four batches match each other: same red, same toy gold, same cream, same glossy candy finish.
- Whole lobby: **about 134,000 triangles** (target under 150,000) and **11 texture sets** (limit 12).

---

## 1. Verdict for each model

### Batch A: the machine (`art/hub_machine/`)

| Model | Verdict | Reason |
|---|---|---|
| Gumball machine (`Hub_Machine`) | **ACCEPT WITH NOTE** | The landmark works: reads instantly as a thumbnail, right size (28 x 28 x 47), beaded gold collar, butterfly knob, chute with flap. 11,224 triangles (limit 12,000). Notes: the red body has a slightly dented, wrinkled look on its shoulder just under the neck, and the white knob wings look a little angular close up. |
| Logo banner (`Hub_Banner`) | **ACCEPT WITH NOTE** | Puffy red pill, white rim, brackets that reach into the neck, clean flat face for the words. 1,304 triangles. Notes: the two gold end bolts look angular close up; and from the front the banner hides the gold beaded collar and the bottom of the globe (this is where the old banner hung too, and there is no room lower down, so it stays). |
| Low-detail gumball (`Hub_GumballLo`) | **ACCEPT** | 300 triangles, looks the same as the full gumball from normal distance in all 8 colours, reuses the existing gumball textures. |
| Globe gumball pile (`GumballPile_Globe.json` + core) | **ACCEPT** | 103 balls, none overlap, all inside the glass (checked: the furthest ball edge is 13.92 from the centre, the glass is at 14). Looks full and neat. The lowest 9 balls sink into the gold floor of the collar, which looks like the pile carrying on down into the machine. |
| Jar gumball pile (`GumballPile_Jar.json` + core) | **ACCEPT WITH NOTE** | 21 balls, none overlap, they fit inside the new jar (checked). Note: the plan asked for about 40, but only about 21 balls of that size really fit without overlapping, so 21 is right. It looks a little sparse and the dark core shows in the gaps. Judge it in the game. |

### Batch B: the plaza kit (`art/hub_plaza/`)

| Model | Verdict | Reason |
|---|---|---|
| Play pad (`Hub_Pad`) | **ACCEPT** | Jelly-sweet top with a bubble pattern, glow ring in a groove, white rim, gold corner studs. All 4 colours look right. Still looks finished with the fancy effects off. 586 triangles. It is slightly bigger than asked (13.5 x 10.5), which leaves a half-stud gap between pads: fine. |
| Pad sign (`Hub_PadSign`) | **ACCEPT WITH NOTE** | Good puffy coloured frame and a clean 8 x 3 text face. Note: the two legs are thin (0.6 across, six-sided) and look spindly next to everything else. |
| Spawn pad (`Hub_SpawnPad`) | **ACCEPT WITH NOTE** | Red rim, white disc, gold star: reads well. Note: the line where the red rim meets the white disc is ragged and the star edge is soft when you look straight down at it. |
| Fence post + glowing cap (`Fence_Post`, `Fence_PostGlow`) | **ACCEPT** | Fat candy-cane post, even stripes, gumdrop cap. Stripes are a little soft very close up (small texture, as planned); fine at normal distance. |
| Fence rail (`Fence_Rail`) | **ACCEPT** | White over mint, ends disappear into the posts, exact length. Only 32 triangles. |
| Fence corner (`Fence_Corner`) | **ACCEPT** | Taller, fatter post with a cup on top; a 2.4-stud gumball sits neatly in it (checked). |
| How-to-play board (`Hub_Board`) | **ACCEPT WITH NOTE** | Puffy red frame, candy-cane legs with gold clips, "!" badge, mint lollipop as the hero detail. The 13 x 9 text face is correct. Notes: with legs and lollipop it is 17.9 wide and 15 tall overall (the frame itself is the asked size), so check it has room where it stands; the lollipop's stick looks thin. |
| Floor tile (`Ground_Tile`) | **ACCEPT** | Exact size, flat top, thin groove between tiles, both colours right. 26 triangles. |
| Kerb and kerb corner (`Ground_Kerb`, `Ground_KerbBand`, corners) | **ACCEPT** | Rounded white lip with a red band underneath, like a cake board. Lines up with the tiles in the preview. |

### Batch C: the candy corner (`art/hub_candy/`)

| Model | Verdict | Reason |
|---|---|---|
| Candy booth (`Hub_Booth`) | **ACCEPT** | The best of the medium props: puffy striped awning, thick window frame, gold band, white base. Pink, mint and lemon all look right. 2,884 triangles. |
| Topper: shopping bag | **ACCEPT** | Clear from a distance. |
| Topper: star ticket | **ACCEPT** | Clear from a distance. |
| Topper: crystal | **ACCEPT WITH NOTE** | The helper made a crystal instead of the gift box in the brief. I agree with that change: the gift chest already says "free gift", and crystals are the game's second currency. Its flat facets are on purpose (it is a crystal). Recolour it later if the crystal currency ends up a different colour. |
| Booth pad (`Hub_BoothPad`) | **ACCEPT WITH NOTE** | Right size. Note: the glowing ring looks many-sided instead of round, and it is a paper-thin sheet rather than a solid piece. |
| Gift chest (`Hub_Chest`) | **ACCEPT** | Fat red chest, gold bands, star lock, bow on the lid, and it looks right open (full of gold coins). Lid is separate with its hinge written down. Slightly deeper than asked because of the lock and bow: fine. |
| Gumball pit (`Hub_Pit`) | **ACCEPT** | One continuous inflatable ring with candy stripes, quilted mint floor, a 5-stud entrance with a ramp. 2,398 triangles. |
| Gumball jar (`Hub_Jar`) | **ACCEPT WITH NOTE** | Right size, bulging glass with a thick rim, ridged red lid, stepped gold and white base. Note: the white shine on the glass is a thin sliver (0.6 wide) with a pointed end. The machine's shine is a fat rounded shape; they should match. |

### Batch D: the sky island (`art/hub_island/`)

| Model | Verdict | Reason |
|---|---|---|
| Island (`Hub_Island`: rim + underside) | **ACCEPT** | Reads as a slice of cake straight away: grass lip, pink frosting with sprinkles, fat drips of different lengths, smooth chocolate tiers down to a rounded tip. 7,896 triangles (limit 8,000). |
| Lollipop trees (swirl, ball, heart) | **ACCEPT** | Chunky heads, fatter sticks, frosting dollop at the foot, white shine piece. One model tints cleanly to all 8 colours. 476 to 672 triangles each. |
| Cloud puffs (`Cloud_A`, `B`, `C`) | **REJECT** | Their outlines are angular. Scaled up to 40 to 80 studs for the cloud floor they look like lumpy rocks, not clouds (see `hub_island_scene_low.png`). The round ball clouds the game has now look softer and cost nothing extra. This is the brief's fault (the triangle limit was too tight for something that big), not the helper's. Keep the current ball clouds. |
| Grass dressing (gumdrop, wrapped sweet, cupcake) | **ACCEPT** | Simple, chunky, tint cleanly, share the lollipop textures. Good filler for the empty grass ring. |

---

## 2. Consistency across the four batches

- **Colours match.** I measured the textures: every batch uses the same machine red (`#E62D46`), the same toy
  gold (`#FFC83C`) and the same cream. Batches B and C look paler and more pastel in their preview pictures,
  but that is only the preview lighting; the files themselves agree.
- **Gloss matches.** All sets are a glossy candy shell (roughness about 0.2 to 0.3) with matte areas where the
  plan asked for them (awning, frosting, chocolate, pit floor).
- **Softness matches**, with two exceptions already noted: the pad sign's thin legs and the jar's thin shine.
- **Scale is right** next to the 5-stud player block in every beauty shot: fence at waist height, booth
  window at head height, chest about player height, machine towering.
- **Fits checked with numbers:**
  - Globe pile inside the globe: fits. Jar pile inside the new jar: fits (ball edges reach 2.86, the glass
    inside is 2.88 or more; pile top is 1.3 below the lid).
  - Banner on the machine: the backing clears the globe and collar by about 1 stud; brackets reach the neck.
  - Corner gumball on the fence corner: sits 0.36 into the cup.
  - Pad and pad sign: sign stands 0.2 behind the pad. Four in a row fit at the 14-stud spacing.
  - Island rim and the grass part: the lip starts under the grass at radius 94, rolls over the edge at 99 and
    its highest point is half a stud above the grass. The glass dome lands on that highest point, so the
    frosting and drips are outside the glass. That is fine and hides the join.
  - **Pads against the machine stage: does NOT fit** (see fix 1).

---

## 3. Fix list (in priority order)

Only things a kid or the owner would notice.

1. **Middle pads and signs collide with the machine's stage (layout, no art work).** The stage's front edge
   is at z = -31. The pads' back edge is at z = -33, and the pad signs stand at z = -34, so pads 2 and 3 and
   their signs are partly buried in the stage. (The old pads overlapped it slightly too; the new signs make
   it obvious.) **Fix: move the four pads from z = -28 to z = -23 in `Config/Hub.lua`.** Signs then clear the
   stage by 1.7 studs. There is plenty of room towards the spawn.
2. **Clouds: keep the current round ball clouds.** Do not upload `Hub_Cloud`. If we want modelled clouds
   later, redo them with about 600 triangles each and use them only for the 14 near clouds.
3. **Pad sign legs: make them fatter** (about 1 stud across, round, with a chunkier foot). Helper B, small job.
   Fine to upload as it is and swap later.
4. **Jar shine: make it a fat rounded pill** (about 1.2 wide, rounded ends) to match the machine. Helper C,
   small job.
5. **Machine body shoulder:** look at it in the game first. If the dented look under the neck shows, helper A
   smooths that band. Do not hold the upload for it.
6. **Polish, only if time:** rounder glow ring on the booth pad; cleaner red/white line and star on the
   spawn pad; rounder gold bolts on the banner and knob wings on the machine.

---

## 4. Integration notes for placing them in Roblox

### Rules for every model

- **Facing:** every model's front points along its own -Z (Roblox "look" direction). So
  `CFrame.lookAt(position, target)` turns the front towards the target. **Check this on the machine first**
  (first upload); if it comes in back to front, add a half turn for every model.
- **Position:** Roblox places a mesh by the middle of its box, not by the model's origin. Each mesh goes at
  `model origin + its "center" from the bounds file` (turned with the model).
- **Collisions:** all meshes `CanCollide = false`. Keep the simple invisible parts for walking and bumping
  (stage disc, pad boxes, booth boxes, chest box, pit wall blocks with the 5-stud gap and a 0.3 floor slab).
- **Material:** textured pieces are SmoothPlastic with the model's look file (colour + normal + roughness).
  No metal anywhere; the gold is toy plastic.
- **Tinting:** set both `MeshPart.Color` and `SurfaceAppearance.Color`, the same way the gumball works.
- **Shadows off** for: glass, shine, glow pieces, gumballs in the globe and jar, tiles, fence posts and
  rails, booth pads, the island underside.
- Keep the old part-built version as the fallback if a model fails to load.

### Decisions I have made on things the helpers left open

| Question | Decision |
|---|---|
| Glass see-through level (helpers said 0.6, 0.65 and 0.7) | **Glass material, transparency 0.6, colour 235, 248, 255** for both the globe and the jar. Adjust once in Studio if the gumballs look milky, and keep both the same. |
| Shine pieces: SmoothPlastic or Neon | **SmoothPlastic, white, transparency 0.15.** Not Neon (it blows out). |
| Third booth topper: gift or crystal | **Crystal.** Booth 1 (pink) = Shop = bag. Booth 2 (mint) = Passes = star ticket. Booth 3 (lemon) = Crystals = crystal. |
| Topper size | They are 3 studs tall as briefed, which is small on an 11-stud booth. **Scale toppers 1.5x** at the mount point (0, 11, 0 on the booth). |
| Gumball on fence corners | Use the **low-detail gumball**, 2.4 across, centre 5.34 above the floor, one colour per corner (red, blue, amber, green). |
| Gumballs in the pit | Keep the full-detail gumball (players kick these). |
| Clouds | Keep the ball clouds (see fix 2). |
| Globe balls that sink into the collar floor | Keep all 103. |
| Scripts are named `hub_<batch>_*.py`, not `build_hub_*.py` | Fine. No change. |
| Island and lollipop normal maps are a higher-quality file type than the plan asked for | Fine: the existing gumball's is the same type and uploaded without trouble. |

### Model by model

**Gumball machine.** Origin at hub (0, 0, -45), front towards the spawn. Remove the old machine parts.
Knob spins about a front-to-back line through (0, 7.9, -9.0) from the machine origin; flap swings outward
about a left-to-right line through (0, 4.55, -9.35). Set these as the pieces' pivots.

**Globe gumballs.** Low-detail gumball at size 3.8. Positions in `GumballPile_Globe.json` are measured from
(0, 29, 0) above the machine origin, in the machine's own directions (turn them with the machine). Use the
colour number given for each ball (it keeps touching balls different colours). Put `GumballCore_Globe` at
the same point: colour 143, 43, 88, no texture.

**Banner.** Origin at (0, 12.9, -10.56) from the machine origin, same facing. Red body 230, 45, 70; white
trim 255, 252, 250; gold bolts 255, 200, 60; all SmoothPlastic. The BUBBLE POP text goes on a 37.5 x 7
invisible part at (0, 4.6, -3.94) from the banner origin.

**Play pads.** At the pad positions (after fix 1: z = -23), front towards the spawn. `Pad_Tint` = the pad
colour. `Pad_Glow` = Neon in the darker version: red 180, 20, 45; blue 20, 90, 190; yellow 190, 125, 0;
green 25, 140, 45. The walkable top is 0.45 high (no jump needed). Keep the invisible 12 x 9 standing part.

**Pad signs.** 5.9 studs **behind** each pad centre, on the machine side (in hub terms: pad z minus 5.9),
facing the spawn. `PadSign_Tint` = the pad colour. Text on an 8 x 3 invisible part, centre 5 studs up,
0.16 in front of the sign's middle. Remove the floating label.

**Spawn pad.** At (0, 0, 34), star point towards the pads.

**Fence.** Fence line 55 from the centre. Each side: 13 posts (with glow caps) at steps of 7.857, corner
posts at the ends, 14 rails between. Posts: turn so their own X runs along the fence. Corner: rail holes are
on its -X and +Z sides; turn in quarter turns. Caps: Neon 190, 30, 90.

**Board.** Origin at (-46, 0, -20), turned to face (0, 4) as today. Text on a 13 x 9 invisible part, centre
6.5 up, 0.25 in front. "!" on a 2 x 2 part at (6.6, 12.1, -0.84).

**Tiles and kerb.** Tiles replace the 64 tile parts one for one; put each tile's origin 0.2 below the plaza
floor so its top is at 0. Colours 255, 248, 252 and 255, 214, 230. Kerb: 8 pieces per side, outside the
slab edge, origin at grass height (plaza floor minus 3), plus 4 corners at the slab corners. Kerb white
255, 252, 250, band red 230, 45, 70. Keep the Plaza slab for walking; remove PlazaTrim.

**Booths.** At (44, -15), (44, 4), (44, 23), front towards the plaza middle. `Booth_Tint` = pink
`#FF69AA`, mint `#46CDA5`, lemon `#F5B928`. Booth pad centred 9.75 in front of the booth centre; pad glow
Neon: pink `#BE1E5A`, mint `#1E9C78`, lemon `#C88C0A`.

**Chest.** At (-24, 0, 40) facing (-14, 20) as today. Lid opens about the line along the back top edge of
the body, through (0, 3.5, 2.0), up to about 105 degrees, swinging backwards. Glow disc: Neon `#C89614`,
transparency 0.35. Light and sparkles at (0, 2.02, -2.3).

**Pit.** Centre at (-38, 0, 16). Turn it so the entrance and ramp point towards the plaza middle (+X).
Inside floor is 0.3 high. The 7 kickable gumballs and the sign stay.

**Jar.** At (-26, 0, -6), shine towards the plaza. Jar gumballs: low-detail gumball at size 1.6, positions
from `GumballPile_Jar.json` measured from (0, 3.2, 0) above the jar origin. `GumballCore_Jar` at the same
point, colour 143, 43, 88.

**Island.** The bounds file treats the grass surface as height 0; the grass is at hub height -3, so lower
every centre by 3. Keep the flat Grass part. Remove the Frosting part and the six IslandRock parts. The rim
casts shadows, the underside does not.

**Lollipops.** Replace the 26 part-built lollipops at the same spots and sizes (0.8 to 1.4). Mix the three
shapes about evenly. Each one is three pieces scaled together: `_Tint` head (a gumball colour), `_Body`
(no tint), `_Shine` (white, as above). Give each a random turn.

**Grass dressing.** About 24 pieces (8 of each) scattered on the grass ring: outside the fence and no more
than 92 studs from the centre, so they stay clear of the rim. Tint with the gumball colours. Small random
turn and size (0.8 to 1.3).

**Things to look for in the first Studio check:** dark fringes at the edges of the pad, fence and board
textures from a distance (those three texture sheets are half empty and black); the machine body shoulder;
whether the jar pile looks full enough; the glass level.

---

## 5. Triangle and texture totals

### Triangles (whole lobby, everything on screen at once)

| Item | Count | Triangles |
|---|---|---|
| Gumball machine | 1 | 11,224 |
| Logo banner | 1 | 1,304 |
| Globe gumballs (low detail) | 103 x 300 | 30,900 |
| Globe and jar cores | 2 | 302 |
| Gumball jar | 1 | 1,968 |
| Jar gumballs (low detail) | 21 x 300 | 6,300 |
| Gumball pit | 1 | 2,398 |
| Pit gumballs (full detail) | 7 x 1,452 | 10,164 |
| Play pads | 4 x 586 | 2,344 |
| Pad signs | 4 x 396 | 1,584 |
| Spawn pad | 1 | 286 |
| Fence posts with caps | 52 x 262 | 13,624 |
| Fence corners with gumballs | 4 x 604 | 2,416 |
| Fence rails | 56 x 32 | 1,792 |
| How-to-play board | 1 | 1,432 |
| Floor tiles | 64 x 26 | 1,664 |
| Kerb and corners | 32 + 4 | 1,208 |
| Candy booths | 3 x 2,884 | 8,652 |
| Booth toppers | 3 | 1,106 |
| Booth pads | 3 x 286 | 858 |
| Gift chest | 1 | 2,190 |
| Island | 1 | 7,896 |
| Lollipop trees | 26 | about 14,140 |
| Grass dressing | 24 | about 8,050 |
| Clouds | ball parts, as today | 0 new |
| **Total** | | **about 133,800** |

- **Target: under 150,000. Hard limit: 200,000. Result: about 134,000. Inside the target.**
- With the modelled clouds it would have been about 168,000 (over the target), which is another reason to
  keep the ball clouds.
- For comparison, the gumballs alone were about 228,000 before. They are now about 47,000.
- Not counted: the glass dome panels, floating soap bubbles, ball clouds and players, which are all simple
  shapes and the same as today.
- Every single model is inside its own budget from the plan.

### Textures

| Size | Sets |
|---|---|
| 1024 | Gumball (existing), Machine, Island |
| 512 | Pad (shared by pad, pad sign, spawn pad), Board, Booth (shared with toppers), Chest, Pit, Jar, Lollipop (shared with dressing) |
| 256 | Fence |

- **11 texture sets. Limit: 12. Inside the budget, with one to spare.**
- Sizes are as planned. No see-through textures, no text in any texture, no metal maps on the new models.
- Banner, tiles, kerb, booth pads and all glow, glass and shine pieces use no texture at all.
