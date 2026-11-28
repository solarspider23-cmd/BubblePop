# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Contact sheet of prop_studio close-ups (front | back per row), run with system Python + PIL (Blender has no PIL):
#   python contact_sheet.py studio studio/sheet.png [Prop1 Prop2 ...]
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; names = sys.argv[3:]
if not names: names = sorted({f.rsplit('_', 1)[0] for f in os.listdir(d) if f.endswith('_front.png')})
c = 480; S = Image.new('RGB', (c * 2, c * len(names)), (20, 20, 28)); D = ImageDraw.Draw(S)
for r, n in enumerate(names):
    for k, t in enumerate(('front', 'back')):
        S.paste(Image.open(os.path.join(d, '%s_%s.png' % (n, t))).convert('RGB').resize((c, c)), (k * c, r * c))
    D.text((8, r * c + 6), n, fill=(255, 255, 255))
S.save(out); print(out)
