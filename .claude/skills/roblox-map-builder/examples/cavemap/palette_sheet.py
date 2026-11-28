# py palette_sheet.py -> previews/palette.png : swatch sheet of cave_palette.py (base ramps, glows by role, districts)
from PIL import Image, ImageDraw, ImageFont
import cave_palette as CP
W, ROW = 1500, 44
rows = len(CP.BASE) + len(CP.GLOW) + len(CP.DISTRICT) + 8
im = Image.new('RGB', (W, rows * ROW + 40), (24, 24, 30)); d = ImageDraw.Draw(im)
try: F = ImageFont.truetype('arial.ttf', 17); FB = ImageFont.truetype('arialbd.ttf', 20)
except Exception: F = FB = ImageFont.load_default()
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
NOTE = {'rock': 'value ramp: teal-slate shadow -> mauve -> warm lit face', 'moss': 'sage, ledges only', 'floor': 'readable mid-tone floor',
        'water': 'lake bed under see-through water', 'wooddk': 'Glowroot bark (lifted)', 'crysV': 'magenta: Brewery only', 'crysA': 'amber: Forge + Camp only'}
y = 16
d.text((20, y), 'GLOWROOT CAVERNS PALETTE  -  base ramps (dark / mid / light)', font=FB, fill=(235, 235, 240)); y += ROW
for k, ramp in CP.BASE.items():
    d.text((20, y + 12), k, font=F, fill=(220, 220, 225))
    for i, h in enumerate(ramp):
        d.rectangle((150 + i * 190, y + 4, 330 + i * 190, y + ROW - 4), fill=rgb(h)); d.text((158 + i * 190, y + 12), h, font=F, fill=(255, 255, 255) if sum(rgb(h)) < 380 else (20, 20, 20))
    d.text((730, y + 12), NOTE.get(k, ''), font=F, fill=(170, 170, 180)); y += ROW
y += 10; d.text((20, y), 'GLOWS (Neon)  -  1 dominant family (teal-cyan) + 1 warm accent (amber) + grotto accents', font=FB, fill=(235, 235, 240)); y += ROW
for k, (h, e, role) in CP.GLOW.items():
    d.text((20, y + 12), k, font=F, fill=(220, 220, 225))
    d.rectangle((150, y + 4, 520, y + ROW - 4), fill=rgb(h)); d.text((158, y + 12), '%s   x%.2f' % (h, e), font=F, fill=(20, 20, 20))
    d.text((540, y + 12), role, font=F, fill=(170, 170, 180)); y += ROW
for nm, (h, role) in (('sun', CP.SUN), ('ambient', CP.AMBIENT)):
    d.text((20, y + 12), nm, font=F, fill=(220, 220, 225)); d.rectangle((150, y + 4, 520, y + ROW - 4), fill=rgb(h))
    d.text((158, y + 12), h, font=F, fill=(20, 20, 20) if sum(rgb(h)) > 380 else (255, 255, 255)); d.text((540, y + 12), role, font=F, fill=(170, 170, 180)); y += ROW
y += 10; d.text((20, y), 'DISTRICT ACCENTS', font=FB, fill=(235, 235, 240)); y += ROW
for nm, keys in CP.DISTRICT.items():
    d.text((20, y + 12), nm, font=F, fill=(220, 220, 225))
    for i, k in enumerate(keys): d.rectangle((260 + i * 130, y + 4, 380 + i * 130, y + ROW - 4), fill=rgb(CP.GLOW[k][0])); d.text((266 + i * 130, y + 12), k, font=F, fill=(20, 20, 20))
    y += ROW
im = im.crop((0, 0, W, y + 20)); im.save('previews/palette.png'); print('palette.png', im.size)
