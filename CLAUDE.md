# BubblePop (working name)

A Roblox simulator for kids 8-14: pop bubble wrap for coins, upgrade your bag, tools and pop speed, snowball. The owner is not a programmer: plain language, short replies, decide sensible defaults. Follow the owner's playbook (the `roblox-game-starter` skill) and copy foundations from `~/Documents/StealAFish` rather than rebuilding them.

## Decided (owner)

- 2026-11-25 GAME LOOP: you join into a small lobby hub (third person) with 4 pads. Standing on a pad makes a lobby (up to 4 players); the pad owner picks a chapter and a room, then the group teleports into that popping room. EVERY RUN STARTS FRESH: coins, bag and upgrades reset each run (they are run-only, not saved). Monetisation = game passes + Robux "skip" items (e.g. buy upgrade levels instantly inside a run). What ends a run and what carries over between runs: still to decide with the owner.

- 2026-11-24: Hub world (third person) with 4 pads; stepping on one starts a session for a group of up to 4. Popping rooms are LOCKED FIRST PERSON, aim with a centre crosshair, held tool in view.
- Room: bubble wrap on floor and walls, plain ceiling.
- 2026-11-25: Players collect PLASTIC SCRAPS: each pop puts a scrap in the bag (rare bubbles drop gold / crystal / rainbow scraps worth more); the recycler buys plastic. Scraps fly into the bag on pop and out to the recycler on sell.
- 2026-11-25: Walking does NOT pop floor wrap at first. A "Spiky Boots" upgrade (shop) unlocks popping by walking (floor pops then drop scraps). Not built yet: owner is finding a UI template for the shop first. Until then the current walk-popping stays in the test build.
- 2026-11-25: Room size "small" (Config/Room.lua `SIZE`): bubbles 5/6 size, 60 x 60 room, 660 bubbles per wall (60 across x 11 up), one ceiling light. Look 4 "Clear+" is the starting look. Default pop sound: Tiny; squeeze and pop still being auditioned (K and 1-9 in game).
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
- Bubble variants (2026-11-25): `Config/Variants.lua` (Gold 1/200 = 5 coins, Diamond 1/2000 = 25, Rainbow 1/20000 = 100; normal = 1), pure `Rules/Variants.lua` + `tests/variant_tests.luau`. Server rolls every bubble's variant at start and again on each regrow; a pop puts the bubble's coin value in the bag; BubbleChanged carries the variant per entry, GetPopped returns { popped, variantIds, variantKinds }. Client: glow ring + glitter, rainbow colour cycle, rare pop burst + chime (Sfx `rarePop`), floating "+N", COINS counter.
- Bag + selling (2026-11-25): `Config/Bag.lua` (start 25, sellReach), pure `Rules/Bag.lua` + `tests/bag_tests.luau`. Pops go into the bag (count + value); a full bag blocks click and stomp pops (server refuses; client `BagState` stops early, unconfirmed pops expire after 1 s). Walking within sellReach of the recycler sells: coins += bag value (`leaderstats.Coins`), `Sold` remote -> HUD "SOLD n bubbles +x coins". Player attributes BagCount / BagValue / BagCapacity drive the HUD bag bar and BAG FULL message.
- Upgrades (2026-11-25): `Config/Upgrades.lua` (Bigger Bag 10 levels, Pop Speed 8, Better Tool 7: 1-13 bubbles per press = aimed one + nearest neighbours on the same surface, server checks count/surface/spread via PopRules.extraOk; Spiky Boots 4: level 1 = no boots, walking doesn't pop), pure `Rules/Upgrades.lua` + `tests/upgrade_tests.luau`. Server `BuyUpgrade` remote checks coins and levels (player attributes Upg_<kind>), sets BagCapacity / PopTime / StompRadius; per-player pop settings for the pop checks. `TestCoins` (+1000) works only in Studio. Client: Popper uses PopTime, Stomp uses StompRadius. `Controllers/Shop.lua` is a TEMPORARY panel (B / SHOP button) until the owner's UI template.
- Not yet: real shop UI, multi-pop/tools, Robux passes (Auto-Sell etc.), hub, pads, saves (coins and upgrades reset on rejoin).

## Build and test

```bash
python3 tools/build_place.py      # checks + tests, writes BubblePop.rbxlx
tools/studio_reload.sh            # build, close Studio, open the new build (closes ALL Studio windows)
python3 tools/pop_check.py        # reload + play test + hold click 3 s + report pops and errors
```

All code lives in `src/`; anything changed only in Studio is lost on the next build. Never `open BubblePop.rbxlx` while Studio is open.

Art: `tools/blender/build_bubblewrap.py` (background Blender only: `/Applications/Blender.app/Contents/MacOS/Blender -b -P ...`), outputs in `art/bubblewrap/`, previews in `art/previews/`.
