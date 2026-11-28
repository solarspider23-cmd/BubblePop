# py post_export.py : after roblox_export.py, set this map's collision per prop in roblox/GlowrootCavernsSetup.lua (+ manifest)
# and turn off the auto PointLights (the curated lights are created by GlowrootCavernsHooks from anchors.json).
# Why here and not in the exporter's COLLISION list: keeps the shared exporter untouched; the rules are this map's.
import re, json, os
RULES = [   # first match wins
    (r'^(GlowVine|GlowWorms|GlowPuddle|Stalactite|Track_|ShroomPatch|CrystalShards|BedGlow|CaveFalls|SkylightLip|GlowShroomCluster|Horizon_|Lake_Water)', 'none'),
    (r'^(Terrain_|Ground_|MineFrame|MineShop|CrystalForge|DeepLift|BrewStation|Scaffold|Glowroot|PlankBridge|RopeBridge|SpawnDais|CampTent)', 'precise'),
    (r'^(MineCart|MineLantern|RailBuffer|Crates|Barrels|QuestBoard|ToolRack|Campfire|LogSeat)', 'box'),
    (r'.*', 'hull'),   # rocks, stalagmites, geodes, crystal sprays, ore piles, giant mushrooms
]
def kind(n): return next(k for rx, k in RULES if re.search(rx, n))
p = os.path.join('roblox', 'GlowrootCavernsSetup.lua'); s = open(p, encoding='utf8').read()
m = re.search(r'M\.Collision = \{(.*?)\}', s)
names = re.findall(r'(\w+) = "\w+"', m.group(1))
s = s[:m.start(1)] + ', '.join('%s = "%s"' % (n, kind(re.sub(r'_\d+$', '', n) if n.startswith(('Terrain_', 'Ground_', 'Horizon_', 'Lake_', 'Track_')) else n)) for n in names) + s[m.end(1):]
s = re.sub(r'M\.LightKeys = \{[^}]*\}', 'M.LightKeys = {}', s)
open(p, 'w', encoding='utf8').write(s)
mp = os.path.join('roblox', 'manifest.json'); man = json.load(open(mp))
for n, v in man['props'].items(): v['collision'] = kind(n)
json.dump(man, open(mp, 'w'), indent=1)
print('collision set for', len(names), 'models;', {k: sum(1 for n in names if kind(n) == k) for k in ('none', 'box', 'hull', 'precise')})
