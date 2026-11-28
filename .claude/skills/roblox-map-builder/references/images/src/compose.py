# Builds the labelled doc images in references/images from the raw renders in src/gallery + the example palettes.
#   py compose.py
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))
from annotate_plan import font
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.dirname(HERE); GAL = os.path.join(HERE, 'gallery')
SK = os.path.abspath(os.path.join(IMG, '..', '..'))
RED, GREEN, INK, BG = (230, 57, 70), (46, 196, 112), (24, 22, 34), (245, 243, 250)

def pill(d, x, y, text, col, f):
    w = d.textlength(text, font=f) + 36
    d.rounded_rectangle((x, y, x + w, y + 52), 26, fill=col); d.text((x + 18, y + 8), text, fill='white', font=f)
    return w

def pair(src, out, bad, good, title, halves=True, right=None):
    a = Image.open(os.path.join(GAL, src)).convert('RGB')
    if halves:
        W, H = a.size; L, R_ = a.crop((0, 0, W // 2, H)), a.crop((W // 2, 0, W, H))
    else:
        L, R_ = a, Image.open(os.path.join(GAL, right)).convert('RGB'); W, H = L.size[0] * 2, L.size[1]
    cap = 150; out_im = Image.new('RGB', (W + 24, H + cap + 70), BG)
    d = ImageDraw.Draw(out_im); ft, fp, fc = font(40), font(30), font(25, False)
    d.text((24, 16), title, fill=INK, font=ft)
    for k, (im, tag, col, text) in enumerate(((L, 'BAD', RED, bad), (R_, 'GOOD', GREEN, good))):
        x = k * (W // 2 + 24); out_im.paste(im, (x, 80))
        d.rectangle((x, 80, x + im.size[0] - 1, 80 + im.size[1] - 1), outline=col, width=6)
        pill(d, x + 16, 96, tag, col, fp)
        words = text.split(); line = ''; y = 80 + H + 14
        for w in words:
            if d.textlength(line + ' ' + w, font=fc) > im.size[0] - 20:
                d.text((x + 6, y), line.strip(), fill=INK, font=fc); y += 32; line = ''
            line += ' ' + w
        d.text((x + 6, y), line.strip(), fill=INK, font=fc)
    out_im.save(os.path.join(IMG, out)); print('->', out)

pair('door.png', 'bug_door.jpg', 'Door boolean on a SOLID drum: the cut leaves a flat wall in the opening. It reads as a painted door.',
     'Hollow the shell first (drum minus a smaller drum), then cut. Add a dark tunnel + lit back cap: a real doorway.',
     'Doorways: hollow the host before the boolean')
pair('grounding.png', 'bug_grounding.jpg', 'Placed at the CENTRE height on a slope: the downhill edge floats above the ground.',
     'Placed at the LOWEST point of its footprint minus a small sink: every edge touches or sits in the ground.',
     'Grounding: lowest footprint point, never centre height')
pair('floor.png', 'bug_floor.jpg', 'Glossy pink tiles under a blue sky: the sky tint turns them lilac-grey; the whole plot reads cold.',
     'Warm butter/cream tiles, matte (Specular ~0.12, Roughness ~0.95): stay warm under the same sky.',
     'Big pale floors pick up the sky colour')
pair('ring.png', 'bug_ring.jpg', 'Ring radius = pillar offset: the ring disappears inside the pillars; a solid scan panel blocks the belt like a wall.',
     'Ring radius < pillar offset - half pillar width; scan beams as thin bars over the belt.',
     'Clearances: rings, arches and beams around paths')
pair('haze_bad.png', 'bug_haze.jpg', 'Haze density 0.0022: everything past 100 studs turns grey-mauve, the hero vanishes.',
     'Density ~0.00015 with a warm tint: depth reads, colours survive, the hero closes the vista.',
     'Haze: thin and warm', halves=False, right='haze_good.png')

# ---- palette strip of the Sugarworks example with ramp names
names = ['white', 'cream', 'conc', 'asph', 'metal', 'pink', 'mint', 'lemon', 'grape', 'choc', 'red', 'lawn', 'cliff', 'sea', 'sky', 'orange']
pal = None
for root in (os.path.join(SK, 'examples', 'sugarworks', 'out'), os.path.join(SK, 'examples', 'sugarworks', 'roblox')):
    p = os.path.join(root, 'Grove_Palette.png')
    if os.path.exists(p): pal = Image.open(p).convert('RGB'); break
if pal:
    n = 16; cw = 110; im = Image.new('RGB', (n * cw + 40, 760), BG); d = ImageDraw.Draw(im)
    d.text((20, 14), 'Palette strip (Sugarworks): 16 columns, light (v=1) at top -> dark (v=0) at bottom', fill=INK, font=font(34))
    strip = pal.resize((n * cw, 560), Image.NEAREST)
    im.paste(strip, (20, 70))
    for i, nm in enumerate(names):
        d.text((20 + i * cw + 8, 640), nm, fill=INK, font=font(24))
    d.text((20, 690), 'Each face UV points at one column; v picks the shade (S(base, up, grad, top)).', fill=(80, 80, 96), font=font(24, False))
    im.save(os.path.join(IMG, 'palette_sugarworks.png')); print('-> palette_sugarworks.png')

# ---- axes diagram: Roblox space used by every script vs Blender storage
im = Image.new('RGB', (1500, 900), BG); d = ImageDraw.Draw(im); f, fs = font(34), font(26, False)
d.text((30, 20), 'Coordinates: scripts work in Roblox space; Blender stores it as (-x, z, y)', fill=INK, font=font(38))
def axes(ox, oy, title, ax):
    d.text((ox - 120, oy - 300), title, fill=INK, font=f)
    for (dx, dy, lab, col) in ax:
        d.line((ox, oy, ox + dx, oy + dy), fill=col, width=8)
        d.ellipse((ox + dx - 10, oy + dy - 10, ox + dx + 10, oy + dy + 10), fill=col)
        d.text((ox + dx + 14 if dx >= 0 else ox + dx - 14 - d.textlength(lab, font=fs), oy + dy + (-16 if dy <= 0 else 14)), lab, fill=col, font=fs)
axes(330, 420, 'Roblox (top view)', [(220, 0, '+X east', (230, 57, 70)), (0, 220, '+Z south', (46, 120, 220)),
                                   (0, -220, 'front = -Z (LookVector)', (46, 196, 112))])
axes(1080, 420, 'Blender (top view)', [(-220, 0, '+X = Roblox -X', (230, 57, 70)), (0, -220, '+Y = Roblox +Z', (46, 120, 220)),
                                     (0, 220, 'prop front = -Y', (46, 196, 112))])
for i, t in enumerate(['Up: Roblox +Y = Blender +Z. 1 unit = 1 stud. pro_lib.KM converts; r2b()/b2r() for points.',
                       'Prop origin = bottom centre, front = -Z. Buildings: door on +Z, turned with front_to().',
                       'After import, check AxisProbe: arrow tip must point along the model LookVector (set M.YAW_FIX).']):
    d.text((30, 760 + i * 34), t, fill=(60, 60, 76), font=fs)
im.save(os.path.join(IMG, 'axes.png')); print('-> axes.png')

# ---- pipeline diagram
steps = [('1 Brief', 'BRIEF.md\narchetype\ndifference table'), ('2 Kit', '<build>_props.py\nkit sheet QA'),
         ('3 Map', '<build>_map.py\nlayout, scatter\nlook'), ('4 Review', 'render shots\nchecklist\nplan view'),
         ('5 Export', 'roblox_export.py\nGLB + Setup.lua\nreport.md'), ('6 Studio', 'Import 3D\nKitPrep\nSetup.Build()')]
im = Image.new('RGB', (1900, 440), BG); d = ImageDraw.Draw(im)
d.text((30, 20), 'Pipeline: Blender (headless) -> files -> Roblox Studio', fill=INK, font=font(38))
cols = [(255, 79, 154), (31, 214, 180), (255, 201, 40), (138, 82, 255), (255, 138, 31), (21, 118, 184)]
for i, (h, b) in enumerate(steps):
    x = 30 + i * 310; d.rounded_rectangle((x, 110, x + 270, 400), 24, fill=cols[i])
    d.text((x + 20, 128), h, fill='white', font=font(36))
    for k, line in enumerate(b.split('\n')): d.text((x + 20, 200 + k * 44), line, fill='white', font=font(25))
    if i < len(steps) - 1: d.polygon([(x + 278, 220), (x + 302, 235), (x + 278, 250)], fill=INK)
im.save(os.path.join(IMG, 'pipeline.png')); print('-> pipeline.png')
