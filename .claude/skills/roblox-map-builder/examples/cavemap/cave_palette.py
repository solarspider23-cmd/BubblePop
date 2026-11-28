# Glowroot Caverns palette (pure Python: read by cave_props.py and by palette_sheet.py)
# Method: base ramps carry a VALUE STRUCTURE (cool shadow -> warm light), one dominant glow family (teal-cyan: lake,
# crystals, fungi, vines), ONE warm accent (amber: the Heart, lanterns, sunbeam), small per-grotto accents, violet only
# in the Brewery (as magenta) and nowhere in the hall. Ramps = (dark, mid, light).
BASE = {
    'rock':   ('#1a2a30', '#5b4d56', '#b9957f'),     # deep teal-slate shadow -> mauve-grey -> warm mauve-brown lit face
    'moss':   ('#1f2e26', '#57704f', '#a3b98b'),     # sage moss on ledges
    'floor':  ('#2c241e', '#6c5a47', '#ad967a'),     # readable mid-tone cave earth
    'sand':   ('#3e4644', '#8c9286', '#d4d4c0'),     # pale lake-shore silt
    'water':  ('#04343c', '#0e9ca2', '#9cf0e6'),     # turquoise lake bed / falls
    'wood':   ('#2a1a10', '#6e4a2c', '#b8854f'),     # mine timber
    'wooddk': ('#16110f', '#43322a', '#86685a'),     # old timber, Glowroot bark (lifted so the trunk reads)
    'iron':   ('#121518', '#3c424a', '#909aa4'),     # rails, straps, cages
    'canvas': ('#43382a', '#a38f68', '#ecdcb2'),     # tent, rope, sacks, paper
    'shroom': ('#0e2632', '#2a5e70', '#86c4c8'),     # fungus caps: teal-blue (dominant family)
    'stem':   ('#3e4c4c', '#9cb8b0', '#eafaf2'),     # pale fungus stems
    'crysA':  ('#3e1a06', '#c06c18', '#ffd38a'),     # amber crystal bodies (forge / camp only)
    'crysC':  ('#033640', '#159aa6', '#a6f6f0'),     # teal-cyan crystal bodies (everywhere)
    'crysV':  ('#2a0c2e', '#8c3a8e', '#f2b4e8'),     # magenta (Brewery caps + its crystals only)
    'red':    ('#3a1410', '#8a3824', '#d8805e'),     # muted rust paint on carts
}
GLOW = {   # key: (hex, emission strength in previews, role)
    'cyan':   ('#2ee6e0', 1.15, 'DOMINANT: crystals'),
    'lake':   ('#2af0dc', 2.0, 'DOMINANT: lake bed'),
    'shroom': ('#46f0cc', 2.0, 'DOMINANT: fungus gills'),
    'spot':   ('#a6fbea', 1.8, 'DOMINANT: cap spots'),
    'root':   ('#8cf0dc', 1.8, 'DOMINANT: glow-root veins, vine bulbs, glow-worms'),
    'falls':  ('#cffaff', 1.1, 'DOMINANT: falls streaks + foam'),
    'amber':  ('#ffa43a', 2.2, 'ACCENT: the Heart, spawn ring'),
    'lamp':   ('#ffbe68', 3.0, 'ACCENT: lanterns'),
    'fire':   ('#ff7a26', 3.0, 'GROTTO: Forge + Quest Camp firelight'),
    'brew':   ('#ff6fd0', 2.2, 'GROTTO: Spore Brewery magenta'),
    'violet': ('#d070ff', 2.0, 'GROTTO: Brewery crystals (only)'),
    'pale':   ('#e6f2ff', 2.4, 'GROTTO: Deep-Dive Elevator cool white'),
}
SUN = ('#ffd59a', 'ACCENT: sunbeam')
AMBIENT = ('#101422', 'Roblox Ambient (low, cool, never black)')
DISTRICT = {'Great Hollow': ('cyan', 'amber'), 'Ore Exchange': ('lamp',), 'Crystal Forge': ('fire', 'amber'),
            'Quest Camp': ('fire',), 'Deep-Dive Elevator': ('pale', 'cyan'), 'Spore Brewery': ('brew', 'violet')}
