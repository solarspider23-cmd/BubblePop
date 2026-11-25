# BubblePop (working name)

A Roblox simulator for kids 8-14: pop bubble wrap for coins, upgrade your bag, tools and pop speed, snowball. The owner is not a programmer: plain language, short replies, decide sensible defaults. Follow the owner's playbook (the `roblox-game-starter` skill) and copy foundations from `~/Documents/StealAFish` rather than rebuilding them.

## Decided (owner)

- 2026-11-24: Hub world (third person) with 4 pads; stepping on one starts a session for a group of up to 4. Popping rooms are LOCKED FIRST PERSON, aim with a centre crosshair, held tool in view.
- Room: bubble wrap on floor and walls, plain ceiling.
- Popping a bubble with the tool takes a press time (starts 0.56 s, like the genre reference); the press time becomes an upgrade ("Pop Speed"). Walking over floor wrap pops instantly.
- Bag: popped bubbles fill your bag (starts at 25); a full bag blocks popping until you sell at the recycler in the middle of the hub. Coins, not cents. First bag upgrades are cheap.
- Monetisation: Auto-Sell, 2x Bag, 2x Coins, 2x Pop Speed passes, instant bag upgrade product. Bag/tool upgrades also buyable with coins.
- Art: cartoon v2 bubble wrap (bright, toon-banded textures; no outline mesh). First tool is just a basic stick (owner: quality later).
- Subagents: allowed, as many as needed (owner, 2026-11-24).

## Built so far (2026-11-24): popping prototype

- `Config/Room.lua` (room size, colours), `Config/Pop.lua` (press time, reach, aim forgiveness, stomp radius, regrow, squash feel), `Config/Sounds.lua` (ids from Roblox's licensed library only; id 0 = built-in stand-in).
- `Rules/RoomLayout.lua` (pure): every bubble's position from the config; a bubble is just its id. `Rules/PopRules.lua` (pure): server checks. Tests: `tests/pop_tests.luau`.
- Server `Main.server.lua`: builds the room and sheets, tracks popped ids, checks every pop (distance, press time, rate limits), grows bubbles back, `leaderstats.Pops`.
- Client: `BubbleView` draws bubbles locally (placeholder squashed spheres until the Blender meshes are uploaded) and plays pop / grow-back animations; `Popper` is the stick view model, press-squeeze-pop animation and hold-to-keep-popping; `Stomp` pops floor bubbles underfoot; `Hud` crosshair, counter, phone POP button.
- Real meshes in game (2026-11-24): place published (placeId 130268639532321). Server loads the uploaded models with InsertService into `ReplicatedStorage.BubbleAssets`; clients clone them (placeholders if missing). Ids in `Config/Models.lua` (Blue textures only so far).
- Not yet: coins, bag, recycler, hub, pads, upgrades, saves.

## Build and test

```bash
python3 tools/build_place.py      # checks + tests, writes BubblePop.rbxlx
tools/studio_reload.sh            # build, close Studio, open the new build (closes ALL Studio windows)
python3 tools/pop_check.py        # reload + play test + hold click 3 s + report pops and errors
```

All code lives in `src/`; anything changed only in Studio is lost on the next build. Never `open BubblePop.rbxlx` while Studio is open.

Art: `tools/blender/build_bubblewrap.py` (background Blender only: `/Applications/Blender.app/Contents/MacOS/Blender -b -P ...`), outputs in `art/bubblewrap/`, previews in `art/previews/`.
