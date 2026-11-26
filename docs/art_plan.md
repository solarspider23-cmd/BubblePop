# BubblePop art plan: the lobby ("Gumball Park")

Written 2026-11-25. This is the plan the Blender helpers follow to turn the part-built lobby into real models.
It covers the lobby only. The popping room and the HUD are listed at the end as the next phase.

How to use it:

- Owner: read section 1 (the look) and "Decisions needed" at the very end. The rest is for the helpers.
- Lead: paste one brief from section 3 to each helper. Use section 4 to accept or reject what comes back.
- Helpers: read sections 1, 2 and 4 and the "Rules for every helper" box before your own brief.

All positions and sizes below are in studs and come from `src/ServerScriptService/Hub.lua` and
`src/ReplicatedStorage/Shared/Config/Hub.lua`. The plaza floor is height 0. "Front" means the side facing the
spawn point (the middle of the plaza).

---

## 1. Art direction

### The one-line pitch

**A giant vinyl toy playset sitting on a cake in the sky.** Everything looks like it was moulded from thick,
glossy candy-coloured plastic by a premium toy company: fat, rounded, clean, and readable from across the plaza
on a phone screen.

### What is wrong with the lobby today (so we know what to fix)

Looking at `hub_gumball_front.jpg`, `hub_gumball_top.jpg`, `gumball_ingame_machine.jpg` and `gumball_ingame_pit.jpg`:

- Every edge is razor sharp. Boxes read as "default Roblox parts", not as toys.
- The machine base and the booths are plain boxes; the pit is 16 flat boards with gaps at the corners.
- Lollipops are thin flat discs; the fence is thin and gets lost.
- The gumballs in the globe poke through each other.
- The chocolate underside reads as brown rock, not chocolate; the grass ring is empty.
- The glossy gumball is the only thing that looks finished. **That gumball is the quality bar: everything else
  must look like it belongs next to it.**

### Shape language

- **Round and fat.** Build from spheres, capsules, rounded boxes and lathed (spun) shapes. If a shape could be
  either thin or chunky, make it chunky.
- **Three sizes of form, and no more.** Big shape (the silhouette), medium shapes (a trim band, a window, a knob),
  small accents (bolts, a coin slot). Roughly 70% big, 25% medium, 5% small. No tiny greebles, no noise.
- **Minimum feature size: 0.4 studs.** Anything smaller disappears on a phone and just costs triangles.
- **Proportions are "squashed and friendly":** slightly wider and shorter than real life, heads and tops bigger
  than bases (big globe, big lollipop heads, puffy awnings). Slight taper on tall things so they feel stable.
- **Silhouette first.** Each model must be recognisable as a solid black shape at thumbnail size.
- **Stripes, dots and swirls are the only patterns** (candy cane stripes, awning stripes, lollipop swirls,
  sprinkle dots). Keep them big: a stripe is never thinner than 0.6 studs.

### Bevels and softness

| Model size | Edge rounding (bevel radius) |
|---|---|
| Small props (fence post, chest, pad) | 0.15 to 0.25 studs |
| Medium (booth, jar, pit, board) | 0.3 to 0.5 studs |
| Hero / huge (machine, island) | 0.6 to 1.2 studs |

- No edge is left perfectly sharp, except where two separate pieces meet (a deliberate seam line).
- Bevels are real geometry (2 to 3 segments), with smooth shading, so they still look round when a phone turns
  the fancy texture effects off.
- Where two parts meet, add a small groove or a raised lip (0.15 to 0.3 studs) so it reads as "two moulded
  pieces clipped together" instead of two shapes passing through each other.

### Palette (already in the game, from `Config/Hub.lua`)

| Role | Colour | Hex |
|---|---|---|
| Machine red (main accent) | red | `#E62D46` |
| Cream white | warm white | `#FFFCFA` |
| Stage / frosting pink | soft pink | `#FFB4D2` |
| Floor tile pink | pale pink | `#FFD6E6` |
| Mint | mint green | `#6EDCBE` |
| Lemon | yellow | `#FFC832` |
| Toy gold | warm yellow | `#FFC83C` |
| Grass | fresh green | `#7DD75A` |
| Chocolate | milk chocolate | `#6E412D` |
| Darkest allowed colour | navy plum | `#283250` |
| Glow (Neon) | deep pink | `#BE1E5A` |
| Gumballs (8) | red `#E62D3C`, blue `#2878E6`, amber `#FFAF00`, green `#32AF46`, pink `#FF78BE`, orange `#FF8C28`, purple `#965AE6`, white | |
| Booth accents (3) | pink `#FF69AA`, mint `#46CDA5`, lemon `#F5B928` | |
| Pad colours (4) | red `#E12D3C`, blue `#2878E6`, yellow `#F0B914`, green `#32AF46` | |

Rules:

- **60 / 30 / 10.** About 60% cream white and pale pink, 30% one main colour per object, 10% accent (gold or a
  contrasting candy colour). An object with five equal colours looks cheap.
- Never pure black, never pure grey. Dark areas (windows, slots, chutes) use navy plum. Shadows lean pink/purple.
- Gold is **toy gold**: glossy yellow plastic, not real metal. Real metal looks dark and dirty on phones.
- Glowing parts use a dark, saturated colour (bright Neon blows out to white in the game).

### Materials: when to use what

| Use | For |
|---|---|
| **Textured (SurfaceAppearance: colour + normal + roughness maps)** | Things the player walks right up to and that have curved, glossy surfaces: the machine, booths, chest, pit, jar base, board, lollipops, pads, island edge. |
| **Flat colour + Roblox SmoothPlastic** | Simple or far-away things: fence rails, floor tiles, clouds, the banner plaque, small trims. A well-bevelled flat-colour model beats a badly textured one. |
| **Roblox Neon (flat colour, no texture)** | Anything that glows: pad rings, fence post caps, booth pad rings, chest glow. Always a separate mesh. |
| **Roblox Glass (flat colour, see-through, no texture)** | The globe and the jar. Always a separate mesh. Never put a see-through texture on anything. |
| **Text** | Never modelled or painted into a texture. All words stay as in-game text on a flat face, so they stay sharp and can be changed. Models leave a clean flat area for the text. |

What goes into the textures:

- **Colour map:** the flat colours, plus soft shading painted in (darker in grooves and under overhangs, a slight
  top-to-bottom gradient). No painted-in sunlight, no hard shadows, no dirt, no scratches, no wood grain.
- **Normal map:** only soft, large detail (a gentle moulded seam, stitched awning ribs, sprinkle bumps). No fine
  noise. Same format as the gumball (OpenGL, Y+).
- **Roughness map:** mostly glossy candy shell (0.15 to 0.3), with matte areas for contrast (awning fabric 0.6,
  chocolate 0.45, frosting 0.5). Gloss next to matte is what makes it look expensive.
- **No metalness map** unless the brief says so (only the machine's coin mechanism).

### How much detail

- Each model gets **one "hero detail"** that someone took time over (the coin knob on the machine, the scalloped
  awning on the booth, the swirl on a lollipop, the frosting drips on the island), and is otherwise calm.
- Detail lives where the player's eyes go: at head height (3 to 8 studs up) and on the front. Backs and tops that
  nobody sees stay simple.
- Signature toy touch: **a chunky white "shine" shape** on glass and glossy round things (a rounded window-shaped
  highlight, modelled as a thin separate piece), like the highlight drawn on a cartoon bubble.

### Lighting assumptions

- The game uses Roblox "Future" lighting, daytime (clock 14:00), bright sky, with bloom. Models are seen in
  sunlight from above, with a blue sky reflecting in glossy surfaces.
- Phones on low graphics may drop the normal and roughness maps and soft shadows. **Every model must still look
  good as plain colour on its shape.** That is why bevels are real geometry and soft shading is in the colour map.
- Preview renders: bright soft studio light, pale neutral background (like `gumball_colours.png`), no dramatic
  shadows.

### What "polished" means here

1. Nothing is sharp, nothing is paper thin, nothing pokes through anything else.
2. Parts meet with a seam, a lip or a groove, the way a real toy is assembled.
3. Gloss and matte are both present and deliberate.
4. Colours are few, clean and exactly from the palette.
5. It reads instantly at thumbnail size and still rewards a close look.
6. Repeated things line up perfectly (fence posts, stripes, tiles) and stripes are evenly spaced.

### Do / Don't

| Do | Don't |
|---|---|
| Fat rounded shapes, generous bevels | Sharp boxes, thin plates, spindly sticks |
| 2 to 3 colours per object, from the palette | Rainbow everything, greys, black |
| Glossy candy shell with a few matte areas | Rust, dirt, scratches, realism, wood grain |
| One hero detail per model | Lots of tiny bolts and panels |
| Clean flat area left for in-game text | Text or logos baked into models or textures |
| Glow and glass as separate pieces | See-through or glowing textures |
| Friendly and inviting | Faces that are creepy, anything scary or grimy |

---

## 2. Technical budget (Roblox, phones first)

### Triangles

| Asset type | Triangles (each) | Notes |
|---|---|---|
| Hero (gumball machine, all pieces together) | 8,000 to 12,000 | No single mesh over 10,000 |
| Medium prop (booth, pit, jar, chest, board, banner) | 1,500 to 4,000 | |
| Small repeated prop (fence post, pad, lollipop, spawn pad) | 150 to 800 | Used many times, so keep these lean |
| Tiny repeated piece (floor tile, rail, low-detail gumball) | 30 to 320 | |
| Island (all pieces together) | 5,000 to 8,000 | It is huge but simple |
| Cloud puff | 150 to 300 | Over a hundred on screen |

**Whole-lobby target: under 150,000 triangles on screen, hard limit 200,000.**

Important finding: today the 157 gumballs (110 in the globe, 40 in the jar, 7 in the pit) use the 1,452-triangle
glossy gumball each, which is about 228,000 triangles on its own. Batch A makes a low-detail gumball
(about 300 triangles) for the globe and the jar; the pit keeps the full-detail one because players kick those.

### Textures

- **1024 maps:** only the gumball machine and the island. **512 maps** for every other textured model.
  **256** for small repeated props (fence post, spawn pad).
- One texture set per model (colour + normal + roughness), shared by all the pieces of that model.
- **At most 12 texture sets in the whole lobby.** The existing gumball set counts as one, and the low-detail
  gumball must reuse it (same layout), not add a new one.
- No see-through (alpha) textures. PNG, 8-bit, square, power-of-two sizes.
- Normal maps: OpenGL (Y+), same as `Gumball_normal.png`.

### Tinted variants (one model, recoloured in game)

Roblox can tint a textured piece with one colour (this is how the gumball works). The tint multiplies the
texture, so:

- A **tintable piece** has a neutral near-white colour map (brightness 235 to 250) with only soft shading in it.
- A **fixed-colour piece** has its real colours painted in the colour map.
- One piece cannot be half tinted and half fixed. Split the model into a `_Tint` mesh and a `_Body` mesh.
  Both can still share the same texture set.

| Model | Tinted? | Variants in game |
|---|---|---|
| Gumball (full and low detail) | yes | 8 gumball colours |
| Play pad | yes (surface + glow ring) | 4 pad colours |
| Candy booth | yes (walls + awning stripes) | 3 booth accents |
| Lollipop tree (3 shapes) | yes (candy head) | 8 gumball colours |
| Floor tile | yes (flat colour) | 2 tile colours |
| Gumball machine, banner, chest, pit, jar, board, fence, island | no | fixed colours |

### Naming

- Blender script: `tools/blender/build_hub_<asset>.py` (lower case, one script per model or closely related set).
- Output folder: `art/hub_<batch>/` (given in each brief).
- Files: `Hub_<Asset>.fbx`, `Hub_<Asset>_color.png`, `Hub_<Asset>_normal.png`, `Hub_<Asset>_roughness.png`,
  `Hub_<Asset>.blend`, `Hub_<Asset>.bounds.json`.
- Mesh (object) names inside the FBX, `<Asset>_<Zone>`:

| Zone suffix | Meaning in game |
|---|---|
| `_Body` | fixed colours from the texture |
| `_Tint` | neutral, recoloured in game |
| `_Glow` | Roblox Neon, flat colour, no texture |
| `_Glass` | Roblox Glass, see-through, no texture |
| `_Shine` | flat white highlight piece, no texture |
| a function name (`_Knob`, `_Lid`, `_Flap`) | a piece that will move, kept separate |

  At most 6 meshes per model. Fewer is better.

### Pivot, scale, axes

- **1 Blender unit = 1 stud.** Build at the real in-game size given in the brief. Stay within 10% of those sizes
  so the model drops into the same spot as the part-built version (which stays in the code as the fallback).
- Z is up in Blender. **The model stands on the origin: bottom centre of its footprint at (0, 0, 0).**
  Exception: gumballs are centred on the origin.
- Front of the model faces Blender **+Y** (this becomes "forward" in Roblox, same rule as `kit.py`).
- Apply all transforms and modifiers before export. No parenting, no armatures, no animation.
- Moving pieces: Roblox ignores Blender pivots, so write the hinge or spin point of each moving piece into the
  `bounds.json` (for example `"hinge": [x, y, z]`, in Roblox axes: X right, Y up, Z = minus Blender Y).

### FBX export settings (copy the export call from `build_gumball.py`)

- Selected meshes only, object type MESH only.
- Triangulated (`use_triangles=True`), `mesh_smooth_type="OFF"`.
- `axis_forward="-Z"`, `axis_up="Y"`, `apply_scale_options="FBX_SCALE_ALL"`.
- `path_mode="STRIP"`, `colors_type="NONE"`. No embedded textures, no cameras or lights.
- Smooth shading on, with clean normals on the bevels (weighted normals), one UV map per mesh, no faces with
  more than 4 sides before triangulating, no loose points, no inside faces nobody can see.

### Glow and glass

- Every glowing area is its own `_Glow` mesh: simple shape, flat dark-saturated colour, no texture, under 200
  triangles. It should sit in a groove or behind a rim so the glow looks built-in.
- Glass is its own `_Glass` mesh: a clean thin shell, no texture. Give the glass a visible thick rim or collar
  where it meets the body. Nothing see-through goes inside glass (Roblox draws that badly); gumballs are solid.

### Collisions and shadows (for the lead, not the helpers)

- Walkable and bump-into shapes stay simple invisible parts in code; meshes are for looks. This is why the
  footprint sizes must match.
- Small repeated props and glow/glass pieces do not cast shadows.

---

## 3. Asset list and batches

### Priority order (if time runs out, stop from the bottom)

| # | Model | Why it matters | Batch |
|---|---|---|---|
| 1 | Gumball machine (with stage) | The landmark; first thing every player sees | A |
| 2 | Logo banner | Frames the game name | A |
| 3 | Low-detail gumball + neat gumball pile | Fixes the phone triangle problem and the poking-through | A |
| 4 | Play pads | The one thing every player must use | B |
| 5 | Candy booths | Where the shop and passes will live (money) | C |
| 6 | Free-gift chest | Daily reward magnet | C |
| 7 | Candy-cane fence kit | Frames the whole plaza, repeated 56 times | B |
| 8 | Gumball pit | The lobby toy | C |
| 9 | Gumball jar | Decoration next to the pit | C |
| 10 | How-to-play board | New players read it | B |
| 11 | Lollipop trees | Fill the skyline | D |
| 12 | Island (grass lip, frosting drips, chocolate underside) | The view when you arrive and from outside | D |
| 13 | Plaza kerb, floor tile, spawn pad | The ground under everything | B |
| 14 | Cloud puffs | Background | D |
| 15 | Grass dressing (gumdrop bushes, candy rocks) | Fills the empty green ring; stretch goal | D |

Staying as plain Roblox parts for now: the glass bubble dome (see-through panels work better as parts), the
floating soap bubbles, all text and labels, the flat grass top you walk on.

### Rules for every helper (applies to all four briefs)

> - Read sections 1, 2 and 4 of `docs/art_plan.md` and look at `art/previews/gumball_colours.png` (the quality
>   bar) and `art/previews/hub_gumball_front.jpg` (what you are replacing) before you start.
> - Read `tools/blender/kit.py` and `tools/blender/build_gumball.py` for the house way of building, baking and
>   exporting. You may `import kit` for its shape helpers. **Do not edit `kit.py` or any existing script**; if
>   you need a new helper function, put it in your own script.
> - Run Blender in the background only:
>   `/Applications/Blender.app/Contents/MacOS/Blender -b -P tools/blender/build_hub_<asset>.py`.
>   The script must rebuild everything from an empty scene every time it runs.
> - Only create files in your own script names and your own `art/hub_<batch>/` folder, plus previews named
>   `art/previews/hub_<asset>_*.png`. Do not touch `src/`, Studio, other folders, uploads or git.
> - For every model deliver: the FBX, the texture PNGs (if textured), the `.blend`, a `bounds.json` (size and
>   position of each mesh, triangle count, suggested colour and Roblox material, hinge points) and four previews:
>   - `hub_<asset>_beauty.png`: three-quarter front view, 1600 x 1200, soft studio light, with a grey
>     5-stud-tall, 2-stud-wide block next to it as a "player" for scale.
>   - `hub_<asset>_turn.png`: one image with four views (front, right, back, left).
>   - `hub_<asset>_flat.png`: same as the beauty shot but with normal and roughness maps off (colour only), to
>     prove it survives low phone graphics.
>   - `hub_<asset>_thumb.png`: the beauty shot at 256 x 192, to prove it reads small.
>   - Tinted models also need `hub_<asset>_colours.png` showing every colour variant side by side.
> - Self-check before you report (and say the result of each): the script prints triangle counts per mesh and
>   they are inside the budget; overall size is within 10% of the brief; model stands on the origin, front on
>   +Y; no sharp edges; nothing thinner than 0.4 studs; nothing poking through; texture sizes right; glow, glass
>   and tint pieces are separate meshes with the right names; you opened every preview image yourself and
>   compared it with the gumball for finish.
> - Report: files made, triangle counts, anything you were unsure about. Do not upload anything.

---

### BATCH A: "The Machine" (the hero)

**Folder:** `art/hub_machine/`  **Scripts:** `build_hub_machine.py`, `build_hub_banner.py`, `build_hub_gumball_lo.py`

**A1. Gumball machine** (`Hub_Machine.fbx`, 1024 texture set, metalness map allowed for the coin mechanism only)

- Replaces in `Hub.lua` (`buildGumballMachine`): MachineStage, MachineStageEdge, MachineBase, MachineBaseTrim,
  MachineNeck, MachineCollar, CoinPlate, CoinSlot, Knob, KnobBar, Chute, ChuteFlap, Globe, GlobeShine, GlobeCap,
  GlobeKnob.
- Size: about **28 wide, 28 deep, 47 tall**. Sits at the back centre of the plaza.
  - Stage: round platform, 28 across, 1.5 high (players can step onto it; keep the top flat).
  - Body: currently an 18 wide x 16 deep x 12 tall box, from height 1.5 to 13.5. Make it a fat rounded,
    slightly tapered body (think classic gumball machine base, wider at the bottom).
  - Neck and gold collar: 20 to 22 across, height 13.5 to 16.
  - Glass globe: 28 across, centre at height 29.
  - Cap: 10 across at height about 43, with a round knob on top (top of everything at about 47).
  - Front details, at the player's eye level: coin plate 6 x 6 centred at height 8.5; turning knob 3.6 across at
    height 7.6; gumball chute opening 5 wide x 3 high at height 3.6 with a flap.
- Premium features: scalloped or beaded gold collar where glass meets body; a thick glass rim; a chunky
  butterfly-shaped turning knob (hero detail) on a round dial plate with a coin slot; a curved chute mouth with
  a hinged flap and a little tray; gold feet or a gold skirt band at the base; a moulded seam line around the
  body; sprinkle or star embossing kept very subtle; the big white window-shaped shine on the globe.
- Meshes: `Machine_Body` (stage, body, neck, collar, cap, plate, chute), `Machine_Knob` (spins), `Machine_Flap`
  (swings), `Machine_Glass` (globe shell), `Machine_Shine` (highlight). Record the knob's spin point and the
  flap's hinge in the bounds file.
- Budget: 8,000 to 12,000 triangles in total.

**A2. Logo banner** (`Hub_Banner.fbx`, flat colours, no texture)

- Replaces: LogoRim, LogoRimEnd x2, LogoEnd x2, Logo, LogoShine.
- Size: a pill-shaped plaque **44.5 long x 7 high x 1.4 thick** (red) on a white backing rim **46 x 8.5**. It
  hangs across the front of the machine, centre at height 17.5, 3 studs in front of the body.
- It must keep a **flat face 37.5 x 7** on the front: the words BUBBLE POP stay as in-game text on that face.
- Premium features: puffy rounded "inflated" edge, a raised white rim with a groove, two big round gold bolts or
  gumball studs at the ends, two chunky brackets that visibly attach it to the machine's neck (today it floats).
- Meshes: `Banner_Body` (red plaque; flat colour), `Banner_Trim` (white rim, gold bolts, brackets).
- Budget: under 1,500 triangles.

**A3. Low-detail gumball and gumball pile** (`Hub_GumballLo.fbx`, no new textures)

- A copy of the existing gumball with about **300 triangles** (the same cube-sphere method with fewer divisions),
  1 stud across, centred, using the **same texture layout** so it reuses the existing gumball maps.
- Also deliver `GumballPile_Globe.json` and `GumballPile_Jar.json`: lists of gumball centre positions that
  **do not overlap** (let them settle with Blender physics or pack them by code):
  - Globe: balls 3.8 across inside a sphere of radius 14, filled to about two thirds, **only the balls that can
    be seen from outside** (the outer layer and the top surface), about 90 balls. Positions measured from the
    globe's centre.
  - Jar: balls 1.6 across inside a cylinder 5.8 across and 7 high, about three quarters full, outer layer and
    top only, about 40 balls. Positions measured from the centre of the jar's floor.
- Add a simple `GumballCore` mesh for each (a dull, dark-pink lumpy ball / cylinder, under 200 triangles) that
  sits inside the pile so you can't see through the gaps.
- Preview: render the pile inside a glass ball with the 8 gumball colours to show it looks full and neat.

**Quality bar for Batch A:** this is the game's landmark and will be on the thumbnail. It must look like a
collectible toy. If the helper running this batch can be the higher-quality model, use it here.

---

### BATCH B: "Plaza kit" (the ground, pads, fence, board)

**Folder:** `art/hub_plaza/`  **Scripts:** `build_hub_pad.py`, `build_hub_fence.py`, `build_hub_board.py`, `build_hub_ground.py`

**B1. Play pad** (`Hub_Pad.fbx`, 512 texture set, tinted)

- Replaces (`buildPads`): PadBase, PadEdge, Pad1 to Pad4 (four copies, one model).
- Size: **12.8 wide x 9.8 deep, at most 0.6 high**. Walkable: the top must be flat and low enough to walk onto
  with no jump (bevelled ramp edge all round). The standing area is the middle 12 x 9.
- Premium features: a rounded cushion-like platform, like a big arcade button or a jelly sweet; a glowing ring
  set into a groove around the standing area; a raised white rim; four small corner studs; a subtle embossed
  footprint or bubble pattern on the top (in the normal map, not geometry).
- Meshes: `Pad_Body` (white rim/base, fixed), `Pad_Tint` (coloured top), `Pad_Glow` (ring; Neon, recoloured).
- Variants: the 4 pad colours. Budget: under 600 triangles.
- Also make **`Hub_PadSign.fbx`**: a small rounded sign post or arch at the back edge of a pad with a flat face
  **8 wide x 3 high**, its centre about 5 studs above the floor, for the "PAD 1 0/4" text (today the text
  floats in the air). Under 400 triangles, uses the pad's texture set.

**B2. Spawn pad** (`Hub_SpawnPad.fbx`, 256 texture or flat colour)

- Replaces: SpawnRing, SpawnDisc. Round, **11 across, at most 0.4 high**, flat and walkable.
- Look: a red-rimmed white disc with a star or bubble emblem embossed in the centre. Under 300 triangles.

**B3. Candy-cane fence kit** (`Hub_Fence.fbx` holding three separate models, one 256 texture set)

- Replaces (`buildPlaza`): Rail x8, Post (4 stacked striped blocks) x60, PostLight x60.
- The fence runs along all four edges of the 112 x 112 plaza (110 long per side), with a post every **7.86
  studs** (15 per side).
- `Fence_Post`: today 1.2 x 1.2 x 3.2 with a 0.8 glowing cap at height 3.6 to 4. Make it a **fat round
  candy-cane post, about 1.6 across and 3.4 tall**, red and white spiral stripes painted in the texture, a round
  base collar, and a gumdrop-shaped cap. The glowing gumdrop cap is a separate `Fence_PostGlow` mesh.
  Under 250 triangles for the post, under 80 for the glow.
- `Fence_Rail`: one straight segment **7.86 long**, with two round rails (at heights 1.2 and 2.4; top one cream
  white, lower one mint), ends designed to disappear into the posts. Flat colours. Under 100 triangles.
- `Fence_Corner`: a taller, fatter corner post (about 2.2 across, 4.5 tall) with a big gumball on top (leave the
  gumball off; the game adds the real one). Under 350 triangles.
- Premium features: stripes evenly spaced and at the same angle on every post; rails that look threaded through
  the posts.

**B4. How-to-play board** (`Hub_Board.fbx`, 512 texture set)

- Replaces (`buildLeft`): BoardFrame, Board, BoardLeg x2, Alert.
- Size: frame **14 wide x 10 high**, on legs, top edge 11.5 above the floor, about 1.5 deep. It needs a
  **flat face 13 x 9** on the front for the in-game text (centre of the face 6.5 above the floor).
- Look: a puffy red frame with rounded corners like a biscuit or a candy bar, two fat candy-cane legs with round
  feet, a round red "!" badge 3 across on the top-left corner (leave a flat disc face for the "!" text), and a
  lollipop or gumball pinned to a top corner as the hero detail.
- Budget: under 1,500 triangles.

**B5. Ground pieces** (`Hub_Ground.fbx` holding separate models, flat colours, no texture)

- `Ground_Tile`: replaces the 64 Tile parts. **14 x 14 x 0.2**, a flat tile with a small rounded edge so a thin
  groove shows between tiles. Tinted (cream and pale pink). Top must be perfectly flat. Under 60 triangles.
- `Ground_Kerb`: replaces Plaza side faces and PlazaTrim. The plaza is a slab 112 x 112 whose top is 3 studs
  above the grass. Make a straight kerb segment **14 long x 3 high x about 1.5 deep** with a rounded top lip and
  a red band along the bottom (like a cake board), plus `Ground_KerbCorner`. Under 150 triangles each.

**Quality bar for Batch B:** these pieces repeat many times, so they must be lean, line up perfectly edge to
edge, and tile with no visible gap or step. Include one preview with 4 pads in a row and a 5-post run of fence
with a corner, on a patch of tiles.

---

### BATCH C: "Candy corner" (booths, chest, pit, jar)

**Folder:** `art/hub_candy/`  **Scripts:** `build_hub_booth.py`, `build_hub_chest.py`, `build_hub_pit.py`, `build_hub_jar.py`

**C1. Candy booth** (`Hub_Booth.fbx`, 512 texture set, tinted)

- Replaces (`buildBooths`, three copies down the right side): BoothBody, BoothTrim, BoothWindow, BoothSill,
  Awning x5, RoofTop, RoofBall, BoothPadRing, BoothPad.
- Size (already includes the in-game 1.3 scale): body **11.7 wide x 9.1 deep x 7.8 high**; awning roof about
  **13 wide x 11 deep** starting at height 9; total height about **13.8**. Serving window about 7.8 wide x 3.4
  high with its sill at height 3, on the front.
- Look: a little candy shop kiosk. Rounded body with a white base band; a serving window with a thick rounded
  frame, a counter sill and a navy-plum inside; a **puffy scalloped awning with fat stripes** (hero detail);
  gold trim band under the roof; a rounded roof cap with a mount on top for a topper.
- Meshes: `Booth_Body` (white, gold, dark window; fixed), `Booth_Tint` (walls and the coloured awning stripes).
- Toppers (separate small models, `Hub_BoothTopper_<Name>.fbx`, each under 500 triangles, about 3 studs tall,
  sharing the booth texture set or flat colour): **Bag** (shop), **Ticket** with a star (passes), **Gift** box
  (third booth). They replace the gold RoofBall and tell the booths apart from a distance.
- `Hub_BoothPad.fbx`: the round pad in front of each booth, **9.1 across, at most 0.4 high**, white disc
  (`BoothPad_Body`) with a glowing ring (`BoothPad_Glow`). Under 300 triangles.
- Variants: pink, mint, lemon. Budget: booth under 4,000 triangles.

**C2. Free-gift chest** (`Hub_Chest.fbx`, 512 texture set)

- Replaces (`buildChest`): ChestBody, ChestLid, ChestBand x2, ChestBandLid x2, ChestLock, ChestGlow.
- Size: **6 wide x 4 deep x 5.8 high** (body 3.5 high, rounded lid on top). Front left of the plaza.
- Look: a fat toy treasure chest in red with toy-gold bands, rounded everywhere, corner caps, a big heart- or
  star-shaped gold lock (hero detail), and a bow or ribbon so it reads as a present.
- Meshes: `Chest_Body`, `Chest_Lid` (separate so it can open; write the hinge line at the back top edge of the
  body into the bounds file; model the inside rim and a simple gold-filled interior so it looks right open),
  `Chest_Glow` (the 10-across glowing floor disc, separate).
- Budget: under 2,500 triangles.

**C3. Gumball pit** (`Hub_Pit.fbx`, 512 texture set)

- Replaces (`buildGumballPit`): PitFloor, PitWall x16.
- Size: a ring **22 across outside, 20 inside, 3 high**; mint floor disc 20 across. Left side of the plaza.
- Look: one continuous, fat, inflatable-looking ring (like a paddling pool or a soft-play wall) with red and
  white candy stripes, a rounded top you could sit on, and **one entrance gap about 5 wide with a little ramp
  or step** so players can walk in (today they have to jump). A soft mint padded floor with a quilted pattern in
  the normal map.
- Meshes: `Pit_Body`. The walls must be solid-looking from inside and outside. Budget: under 3,000 triangles.
- The 7 kickable gumballs stay as they are (the existing glossy gumball).

**C4. Gumball jar** (`Hub_Jar.fbx`, 512 texture set)

- Replaces (`buildCandyJar`): JarBase, JarPedestal, Jar, JarLid, JarLidKnob.
- Size: gold base 8 across x 1.2 high; white pedestal 6.5 across up to height 3.2; glass jar **6.2 across from
  height 3.2 to 10.8**; red lid 6.8 across; knob on top; **total height about 12.6**.
- Look: an old-fashioned sweet-shop jar: a slightly bulging glass body with a thick rim, a chunky red screw lid
  with ridges and a ball knob, a stepped pedestal with a gold band, a white shine piece on the glass.
- Meshes: `Jar_Body` (base, pedestal, lid), `Jar_Glass`, `Jar_Shine`. Inside floor of the jar is at height 3.2
  and the inside is 5.8 across (Batch A's gumball pile is made for that space; do not make gumballs yourself).
- Budget: under 2,000 triangles.

**Quality bar for Batch C:** these are the things players stand right next to. Close-up finish matters: check
the beauty shot from a player's eye height (5 studs up, 15 studs away).

---

### BATCH D: "Sky island" (island, lollipops, clouds, grass dressing)

**Folder:** `art/hub_island/`  **Scripts:** `build_hub_island.py`, `build_hub_lollipop.py`, `build_hub_cloud.py`, `build_hub_dressing.py`

**D1. Island** (`Hub_Island.fbx`, one 1024 texture set)

- Replaces (`buildPlaza`): the edge of Grass, Frosting, IslandRock x6. (The flat grass disc you walk on stays a
  part; make your pieces fit around and under it.)
- Size: a round island **198 across** (radius 99). The walkable grass top is at height **-3** (3 below the plaza
  floor). The underside narrows to a rounded point about **58 studs below the grass**. Build it with the grass
  surface at Blender height 0 and say so in the bounds file.
- Look: **a slice of cake in the sky.** A soft rounded grass lip around the edge; a thick band of pink frosting
  just below it with **fat drips of different lengths** running down (hero detail); under that, smooth milk
  chocolate that tapers down in 3 or 4 soft rounded tiers (like scoops or an upside-down cake), ending in a
  rounded tip. A few big chocolate-chip or sprinkle shapes are fine; no rock texture.
- Meshes: `Island_Rim` (grass lip and frosting with drips), `Island_Under` (chocolate).
- Seen mostly from far away and from above, so keep shapes big. Budget: 5,000 to 8,000 triangles in total.

**D2. Lollipop trees** (`Hub_Lollipop.fbx` holding three models, one 512 texture set, tinted heads)

- Replaces (`lollipop` in `buildScenery`, 26 copies): LollyStick, Lolly, LollySwirl, LollyMiddle.
- Size at normal scale: stick 0.9 across and 9 tall, candy head **8 across**, total **15 tall** (the game scales
  each one between 0.8 and 1.4). Make the stick a bit fatter (about 1.2).
- Three shapes: `Lollipop_Swirl` (a thick disc, about 2 studs thick with a puffy rounded edge and a raised
  spiral), `Lollipop_Ball` (a round ball lollipop with a wrapper twist or bow at the neck), `Lollipop_Heart` or
  star (a shaped flat lollipop). Each has a `_Tint` head and a `_Body` stick (white, with a small mound of
  grass or a frosting dollop at the foot so it doesn't just stab into the ground).
- The swirl must work in a neutral texture: white swirl line raised in the normal map and slightly brighter in
  the colour map, so one tint colour gives a two-tone candy.
- Budget: under 700 triangles each.

**D3. Cloud puffs** (`Hub_Cloud.fbx` holding three models, flat colour, no texture)

- Replaces (`puff` in `buildScenery`): the Cloud balls (about 124 clusters of 3 to 5 balls).
- Three shapes (`Cloud_A`, `Cloud_B`, `Cloud_C`): soft clumps of merged rounded blobs with a flatter bottom,
  built about **20 wide** (the game scales them from 14 up to 80). White, matte.
- Budget: 150 to 300 triangles each. They are huge and far away: smooth shading, no small bumps.

**D4. Grass dressing (stretch goal, only after D1 to D3 pass review)** (`Hub_Dressing.fbx`, shares the lollipop texture set)

- New, replaces nothing: fills the empty grass ring between the fence and the glass.
- `Dressing_Gumdrop` (a sugar-coated gumdrop bush, about 4 across and 3 tall, tinted), `Dressing_CandyRock`
  (a wrapped sweet, about 5 long, tinted), `Dressing_Mushroom` or cupcake (about 5 tall). Under 400 triangles each.

**Quality bar for Batch D:** these make the first impression when the player arrives and looks around.
Silhouette and colour matter more than close-up detail. Include one preview of the whole island from the same
angle as `art/previews/hub_sky_island.jpg`, with a simple 112 x 112 white slab on top for the plaza.

---

### After the batches (lead's job, in this order)

1. Review each model with the checklist in section 4. Send fixes back to the same helper.
2. Upload accepted FBX files and textures (`tools/upload_model.py`, `tools/upload_textures.py`), add ids to
   `Config/Models.lua`, save a look file per textured model (like `art/GumballLook.rbxmx`).
3. Change `Hub.lua` one model at a time: use the model if it loaded, otherwise build the old parts (fallback).
4. Check in the game on a phone-sized screen at low graphics, then take new screenshots for `art/previews/`.

---

## 4. Review checklist (accept or reject)

Reject if any answer is "no".

**Look**

1. Thumbnail test: at 256 pixels wide, can you tell what it is in one second?
2. Does it look like it belongs in the same toy box as the glossy gumball?
3. Are all edges rounded, and is nothing thinner than 0.4 studs?
4. Is there exactly one hero detail, and is the rest calm?
5. Colours: only palette colours, no black or grey, 2 to 3 colours per object?
6. Is there both gloss and matte, and do parts meet with a lip, groove or seam (nothing just poking through)?
7. Does the colour-only preview (`_flat.png`) still look finished?
8. Is it friendly for an 8-year-old (nothing creepy, gritty or realistic)?

**Fit**

9. Size within 10% of the brief, and correct next to the 5-stud "player" block?
10. Stands on the origin, front on +Y, walkable tops flat?
11. Flat faces for in-game text are present, the right size and unobstructed?
12. Repeating pieces tile with no gap or step (fence, tiles, kerb)?

**Technical**

13. Triangle count inside the budget (printed by the script)?
14. Texture sizes and number of sets as in the brief; no see-through textures; no text in textures?
15. Glow, glass, tint and moving pieces are separate meshes with the right names; hinge points written down?
16. Tinted pieces are neutral near-white and look right in every colour variant?
17. The script runs from scratch in background Blender with no errors and recreates every file?
18. All files are in the batch's own folder with the right names, and nothing else was touched?

---

## 5. Next phase (not now)

### Popping room

- **Pop tools** (highest value: always on screen in first person): the starter stick and the 7 "Better Tool"
  levels as a family of toy tools (stick, roller, rake, mallet...), each clearly fancier than the last.
- **Recycler chute**: a proper floor chute model (hopper rim, glowing drain, grate, SELL sign frame), in the
  same toy style; reuse ideas from the two recycler models in `art/recycler/`.
- **Room shell**: rounded skirting and corner trims where bubble-wrap walls meet floor and ceiling, a ceiling
  light fixture, a door or hatch where players arrive, a simple ceiling pattern.
- **Rare bubbles**: diamond and rainbow bubble models (instead of glow rings on a normal bubble).
- **Scraps and bag**: plastic scrap pieces (normal, crystal, rainbow) that fly into the bag; a bag model whose
  size grows with the Bigger Bag upgrade.
- **Spiky boots**: seen at your feet and on other players.
- **Shop terminal** in the room, if the shop is opened from an object.
- **Chapter themes**: colour and trim variations of the room so later rooms feel new.

### HUD and UI polish

- One UI kit to match the toy look: rounded glossy buttons, panels and bars (9-slice images), one display font
  for titles and one clean font for numbers (see `art/previews/font_options.jpg`).
- Icon set rendered from the 3D models so UI and world match: money, crystal, bag, pop speed, tool, boots,
  timer, each pass, each Robux item.
- The shop panel on the owner's chosen template; pad START panel; room and chapter picker.
- "Juice": money counter that ticks up, bag bar that bounces when full, ROOM CLEARED banner with confetti,
  rare-pop flash, button press squash.
- Phone layout pass: thumb-reach buttons, safe areas, readable at small sizes.
- Game icon and thumbnails re-rendered with the finished machine and island.

---

## Decisions needed from the owner

Sensible defaults are already written into the briefs; say so only if you want something different.

1. **Logo:** keep BUBBLE POP as in-game text on the banner (default, quick), or have it modelled as chunky 3D
   letters later (looks more premium, more work)?
2. **What are the three booths?** Default: Shop (bag on the roof), Passes (star ticket), Free Gift / Crystals
   (gift box). The roof toppers depend on this.
3. **Should the gumball machine have a face** (a friendly mascot) or stay a plain machine? Default: no face.
4. **Island style:** "a slice of cake" with pink frosting drips and smooth milk chocolate underneath. OK?
5. **Gold:** shiny toy-plastic yellow instead of real metal gold (looks cleaner on phones). OK?
6. **Grass dressing** (gumdrop bushes, wrapped sweets on the green ring): include as a stretch goal? Default: yes.
7. **Helper quality:** use the higher-quality model for Batch A (the machine), standard for the rest? Default: yes.
