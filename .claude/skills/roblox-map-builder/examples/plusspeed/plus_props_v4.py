# v4: original concept kit (speed / racing theme). Hero props are pixel-art silhouettes built from stepped blocks:
# outline rim stands proud, fills sit inset, glow pixels poke out as neon. General lessons, no copied pieces.
import math
import plus_props  # noqa: puts the skill scripts on sys.path
PAL = plus_props.PAL
from blocks import BlockProp
from plus_props_v3 import chamfer_block, cyl_v, ring, speed_shoe

# char -> (palette colour, value, kind) ; kind: rim (full depth) | fill (inset) | glow (neon, proud) | skip
BASE = {
    'K': ('navy', .12, 'rim'), 'W': ('snow', .98, 'fill'), 'w': ('snow', .82, 'fill'), 'G': ('stone', .45, 'fill'),
    'R': ('red', .5, 'fill'), 'r': ('red', .3, 'fill'), 'B': ('navy', .55, 'fill'), 'b': ('mint', .55, 'fill'),
    'Y': ('gold', .7, 'glow'), 'y': ('gold', .55, 'fill'), 'O': ('gold', .4, 'fill'), 'P': ('pink', .55, 'fill'),
    'M': ('mint', .7, 'glow'), 'C': ('snow', .95, 'glow'), 'F': ('fire', .6, 'glow'), 'N': ('pink', .7, 'glow'),
}

def pixel_art(P, rows, px=1.0, pos=(0, 0, 0), depth=4.0, cmap=None, yaw=0.0):
    """rows[0] is the top row. Art is centred on X at pos, bottom at pos.y, front face toward -Z (before yaw)."""
    cm = dict(BASE); cm.update(cmap or {})
    H = len(rows); W = max(len(r) for r in rows); x0, y0, z0 = pos
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for j, row in enumerate(rows):
        y = y0 + (H - 1 - j + .5) * px
        i = 0
        while i < len(row):
            ch = row[i]
            if ch not in cm: i += 1; continue
            k = i
            while k < len(row) and row[k] == ch: k += 1
            col, v, kind = cm[ch]; n = k - i
            lx = -(i + n / 2 - W / 2) * px                                     # viewer at -Z looking +Z has -X on the right
            d = depth if kind == 'rim' else (depth - .8 if kind == 'fill' else depth + .6)
            wx, wz = x0 + lx * c, z0 - lx * s
            P.b((n * px, px, d), (wx, y, wz), col, v, rot=(0, yaw, 0), mat='neon' if kind == 'glow' else 'stud')
            i = k
    return P

def raster(W, H, fn):
    """fn(x, y) -> char, x/y in -1..1 (y up); returns rows top->bottom"""
    out = []
    for j in range(H):
        y = 1 - (j + .5) / H * 2
        out.append(''.join(fn(-1 + (i + .5) / W * 2, y) for i in range(W)))
    return out

# ------------------------------------------------------------------ signature edge: race kerb lip
def kerb_lip(group_blk, x0, x1, y, z, depth=2.4, col='red', step=6.0, axis='x'):
    """alternating colour / white kerb blocks with a wedge bevel on the outer edge; group_blk(size, pos, col, v, rot, shape)"""
    L = x1 - x0; n = max(1, int(round(L / step))); st = L / n
    for i in range(n):
        c, v = (col, .55) if i % 2 == 0 else ('snow', .97)
        mid = x0 + st * (i + .5)
        if axis == 'x':
            group_blk((st, 1.0, depth), (mid, y + .5, z), c, v, (0, 0, 0), 'block')
        else:
            group_blk((depth, 1.0, st), (z, y + .5, mid), c, v, (0, 0, 0), 'block')

# ------------------------------------------------------------------ shared station plinth
def plinth(P, w, d, h=1.6, trim='red', bolt=True):
    chamfer_block(P, (w, h, d), (0, h / 2, 0), 'snow', .9, bev=.8)
    n = max(4, int(w / 4))
    for i in range(n):                                                         # kerb trim band on the front + back faces
        for sz in (-1, 1):
            P.b((w / n, .7, .5), (-w / 2 + w / n * (i + .5), .6, sz * (d / 2 + .1)), trim if i % 2 == 0 else 'snow', .55 if i % 2 == 0 else .97)
    if bolt:                                                                   # glowing bolt inlay at the front
        pixel_art(P, ['.YY', 'YY.', '.YY', 'YY.'][::1], .5, (0, .1, -d / 2 - .05), .3)
    return P

# ------------------------------------------------------------------ hero: sneaker shop
SNEAKER = [
    "..........KKKKKK..............",
    ".........KRRRRRRK.............",
    ".........KRrRRRRRK............",
    ".........KRrRWRWRRK...........",
    "........KRRrRRWRWRRK..........",
    "........KRRrRRRRWRWRKK........",
    ".......KRRRYRRRRRRRRRRKK......",
    "......KRRRYYRRRRRRRRRRRRKK....",
    ".....KRRRRRYYRRRRRRRRRRRRRKK..",
    "....KRRRRRRRYYYYYYRRRRRRRRWWK.",
    "...KWWWWWWWWWWWWWWWWWWWWWWWWWK",
    "...KGGGGGGGGGGGGGGGGGGGGGGGGGK",
    "....KKKKKKKKKKKKKKKKKKKKKKKKK.",
]

def sneaker_shop():
    P = BlockProp('SneakerShop')
    plinth(P, 40, 22)
    pixel_art(P, SNEAKER, 1.6, (0, 1.6, 2), 10)                               # the giant shoe, 48 x 21 studs
    # counter cut into the toe side: a white bar with goods on it
    chamfer_block(P, (18, 3.6, 4), (8, 3.4, -6), 'snow', .92, bev=.5)
    P.b((18.6, .5, 4.6), (8, 5.45, -6), 'red', .5)
    for k, c in enumerate(('red', 'mint', 'gold')): speed_shoe(P, (2 + k * 6, 5.7, -6), c, 20 * k)
    for x, c in ((-17, 'mint'), (-7, 'gold')):                              # mini sneakers on display posts
        chamfer_block(P, (6, 4, 6), (x, 3.6, -8), 'navy', .3, bev=.5)
        cyl_v(P, 5, .4, (x, 5.8, -8), c, .7, mat='neon')
        pixel_art(P, SNEAKER, .2, (x, 6.1, -8), 1.4, cmap={'R': (c, .55, 'fill'), 'r': (c, .35, 'fill')})
    return P

# ------------------------------------------------------------------ hero: cracked egg hatchery
def egg_rows(W=18, H=24):
    crack = {(W // 2 - 1 + (j % 4 if j % 4 < 3 else 1) - j // 7, j) for j in range(1, int(H * .7))}
    def f(x, y):
        yy = y * 1.0 + .12; r = (x / (.78 if y > 0 else .92)) ** 2 + yy ** 2
        if r > 1: return '.'
        if r > .78: return 'K'
        return 'w' if (int((x + 1) * 4) + int((y + 1) * 3)) % 5 == 0 and y < .5 else 'W'
    rows = [list(r) for r in raster(W, H, f)]
    for i, j in crack:
        if 0 <= j < H and i < W and rows[j][i] in 'Ww': rows[j][i] = 'Y'
    spots = [(4, 15, 'P'), (13, 6, 'b'), (5, 6, 'b'), (13, 17, 'P')]
    for ci, cj, ch in ((int(a * W / 18), int(b * H / 24), c) for a, b, c in spots):
        for i, j in ((ci, cj), (ci + 1, cj), (ci, cj + 1), (ci + 1, cj + 1), (ci - 1, cj), (ci, cj - 1)):
            if 0 <= j < H and 0 <= i < W and rows[j][i] in 'Ww': rows[j][i] = ch
    return [''.join(r) for r in rows]

def egg_hatchery():
    P = BlockProp('EggHatchery')
    plinth(P, 40, 24, trim='mint')
    cyl_v(P, 20, 2.2, (0, 2.7, 0), 'gold', .55)                                # nest ring
    for k in range(10):
        a = k * math.tau / 10
        P.b((3.4, 1.6, 2.2), (math.cos(a) * 9.6, 4.4, math.sin(a) * 9.6), 'wood', .55, rot=(0, -math.degrees(a), 18))
    pixel_art(P, egg_rows(), 1.4, (0, 3.4, 0), 8)                              # 25 x 34 studs egg
    for k, (x, c) in enumerate(((-15, 'P'), (15, 'b'))):                       # little eggs on podium discs
        cyl_v(P, 6, 1.2, (x, 2.2, -6), 'snow', .9)
        cyl_v(P, 6.6, .5, (x, 1.8, -6), c == 'P' and 'pink' or 'mint', .6, mat='neon')
        pixel_art(P, egg_rows(8, 10), .7, (x, 2.8, -6), 4, cmap={'Y': ('gold', .7, 'fill')})
    return P

# ------------------------------------------------------------------ hero: bolt rebirth portal
def portal_rows(N=30):
    def f(x, y):
        r = math.hypot(x, y)
        if r > 1: return '.'
        if r > .92: return 'K'
        if r > .80: a = math.atan2(y, x); return 'Y' if (a * 12 / math.tau) % 1 < .3 else 'O'
        if r > .74: return 'K'
        if r > .62: return 'B'
        if r > .52: return 'N'
        return 'P' if r > .40 else 'C'
    rows = [list(r) for r in raster(N, N, f)]
    bolt = ["....YYY", "...YYY.", "..YYY..", ".YYYYYY", "...YYY.", "..YYY..", ".YY....", "YY....."]
    oy, ox = N // 2 - 4, N // 2 - 3
    for j, row in enumerate(bolt):
        for i, ch in enumerate(row):
            if ch == 'Y': rows[oy + j][ox + i] = 'F'
    return [''.join(r) for r in rows]

def rebirth_portal():
    P = BlockProp('RebirthPortal')
    plinth(P, 40, 20, trim='pink')
    pixel_art(P, portal_rows(), 1.1, (0, 2.4, 0), 4)                           # 33-stud ring
    for sx in (-1, 1):                                                         # bolt pylons
        x = sx * 19
        chamfer_block(P, (5, 3, 5), (x, 3.1, 0), 'navy', .3, bev=.6)
        P.b((3, 16, 3), (x, 12.5, 0), 'navy', .45); P.b((3.6, 1, 3.6), (x, 9, 0), 'gold', .6); P.b((3.6, 1, 3.6), (x, 16, 0), 'gold', .6)
        P.b((3.2, 3.2, 3.2), (x, 22.6, 0), 'pink', .7, shape='ball', mat='neon'); P.b((3.8, 1, 3.8), (x, 21, 0), 'gold', .6)
    return P

# ------------------------------------------------------------------ medal wins pad
def medal_rows(N=18, face='Y'):
    def f(x, y):
        r = math.hypot(x, y)
        return '.' if r > 1 else ('K' if r > .86 else ('O' if r > .72 else 'y'))
    rows = [list(r) for r in raster(N, N, f)]
    for j in range(N):                                                         # 5-point star in the middle
        for i in range(N):
            x, y = -1 + (i + .5) / N * 2, 1 - (j + .5) / N * 2
            r, ang = math.hypot(x, y), math.atan2(y, x)
            tt = (ang - math.pi / 2) % (math.tau / 5); d = abs(tt - math.pi / 5) / (math.pi / 5)
            if r < .26 + .34 * d: rows[j][i] = face
    ribbon = ["RR....RR", ".RR..RR.", "..RRRR..", "...RR..."]
    top = [('...' + r + '...') for r in ribbon]
    return top + [''.join(r) for r in rows]

def medal_pad(col='gold', r=12.0):
    P = BlockProp('MedalPad')
    cyl_v(P, r * 2, 1.0, (0, .5, 0), 'snow', .9)
    for k in range(16):                                                        # kerb rim
        a = k * math.tau / 16
        P.b((r * .4, 1.2, 1.2), (math.cos(a) * (r - .4), .9, math.sin(a) * (r - .4)), col if k % 2 == 0 else 'snow', .6 if k % 2 == 0 else .97,
            rot=(0, -math.degrees(a) + 90, 0))
    cyl_v(P, r * 1.2, .3, (0, 1.15, 0), col, .7, mat='neon')
    cmap = {'y': (col, .55, 'fill'), 'O': (col, .35, 'fill'), 'Y': (col, .85, 'glow')}
    pixel_art(P, medal_rows(), r * .068, (0, 5, 0), 1.6, cmap)
    return P

# ------------------------------------------------------------------ landmark: START gate with giant stopwatch
def stopwatch_rows(N=34):
    def f(x, y):
        r = math.hypot(x, y)
        if r > 1: return '.'
        if r > .9: return 'K'
        if r > .82: return 'R'
        if r > .76: return 'K'
        a = math.atan2(y, x)
        if r > .62 and abs(((a * 12 / math.tau) % 1) - .5) > .42: return 'Y'      # 12 glowing tick marks
        return 'W'
    rows = [list(r) for r in raster(N, N, f)]
    c = N // 2
    for k in range(1, 12): rows[c - k][c] = 'R'                                    # minute hand up
    for k in range(1, 8): rows[c - k // 2][c + k] = 'r'                             # second hand off right
    rows[c][c] = rows[c - 1][c] = rows[c][c - 1] = rows[c - 1][c - 1] = 'K'
    crown = ["...KKKK...", "..KYYYYK..", "...KKKK...", "....KK...."]
    return [('.' * ((N - 10) // 2)) + r + ('.' * ((N - 10) // 2)) for r in crown] + [''.join(r) for r in rows]

def start_gate(w=176.0, accent='red'):
    P = BlockProp('StartGate')
    for sx in (-1, 1):                                                         # kerb-striped towers
        x = sx * (w / 2 - 8)
        chamfer_block(P, (18, 4, 18), (x, 2, 0), 'snow', .9, bev=1)
        for k in range(7):
            P.b((14, 6, 14), (x, 7 + k * 6, 0), accent if k % 2 == 0 else 'snow', .55 if k % 2 == 0 else .97)
        chamfer_block(P, (17, 3, 17), (x, 49.5, 0), 'navy', .25, bev=1)
        pixel_art(P, ['.YY', 'YY.', '.YY', 'YY.'], 2.0, (x, 52, 0), 3)         # bolt finials
    P.b((w - 2, 10, 8), (0, 46, 0), 'navy', .25)                               # beam
    for i in range(22): P.b(((w - 2) / 22, 1.2, 8.6), (-(w - 2) / 2 + (w - 2) / 22 * (i + .5), 40.6, 0), accent if i % 2 == 0 else 'snow', .55 if i % 2 == 0 else .97)
    pixel_art(P, stopwatch_rows(), 1.5, (0, 54, 0), 5)                         # 51-stud stopwatch on the beam
    for sx in (-1, 1):                                                         # side buttons
        P.b((4, 3, 4), (sx * 21, 90, 0), 'red', .5, rot=(0, 0, -sx * 40))
    return P

# ------------------------------------------------------------------ podium leaderboard
def podium_board():
    P = BlockProp('PodiumBoard')
    plinth(P, 44, 18, trim='gold')
    for x, h, c, v in ((0, 9, 'gold', .6), (-13, 6, 'stone', .7), (13, 4, 'fire', .45)):   # 1-2-3 podium steps
        chamfer_block(P, (12, h, 10), (x, 1.6 + h / 2, -2), c, v, bev=.6)
    P.put(BlockProp('n').b((2, 5, .4), (0, 6.6, -7.2), 'snow', .95), (0, 0, 0))
    P.b((34, 22, 2), (0, 25, 4), 'navy', .22)                                  # board
    for k, c in enumerate(('gold', 'stone', 'fire', 'navy', 'navy')):
        P.b((26, 2.2, .5), (2, 32 - k * 3.4, 2.7), c, .7 if k < 3 else .5, mat='neon' if k < 3 else 'stud')
        P.b((2.2, 2.2, .5), (-13, 32 - k * 3.4, 2.7), 'snow', .95)
    for sx in (-1, 1): P.b((3, 26, 3), (sx * 18.5, 14.6, 4), 'red', .5); P.b((3.6, 1, 3.6), (sx * 18.5, 22, 4), 'snow', .97)
    return P

# ------------------------------------------------------------------ stadium hoarding (icon only; any wording is a GUI)
def hoarding(icon='bolt', col='red'):
    P = BlockProp('Hoarding')
    P.b((24, 7, 1.2), (0, 3.5, .6), 'navy', .22)
    P.b((24.6, .8, 1.8), (0, 7.3, .6), col, .55); P.b((24.6, .8, 1.8), (0, -.1, .6), col, .55)
    if icon == 'bolt': pixel_art(P, ['..YY', '.YY.', 'YYYY', '.YY.', 'YY..'], 1.1, (0, .9, -.3), 1.0)
    elif icon == 'shoe': pixel_art(P, SNEAKER, .2, (0, 1.6, -.3), 1.0, cmap={'R': (col, .55, 'fill'), 'r': (col, .35, 'fill')})
    else: pixel_art(P, medal_rows(12), .42, (0, .3, -.3), 1.0)
    return P
