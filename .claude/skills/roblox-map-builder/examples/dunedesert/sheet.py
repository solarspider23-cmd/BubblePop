# py sheet.py <studio dir> <out.png> [cell]: grid of front|back pairs, 2 pairs per row
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; c = int(sys.argv[3]) if len(sys.argv) > 3 else 400
names = sorted({f.rsplit('_', 1)[0] for f in os.listdir(d) if f.endswith('_front.png')})
rows = (len(names) + 1) // 2
S = Image.new('RGB', (c * 4, c * rows), (20, 20, 28)); D = ImageDraw.Draw(S)
for i, n in enumerate(names):
    r, k0 = i // 2, (i % 2) * 2
    for k, t in enumerate(('front', 'back')):
        S.paste(Image.open(os.path.join(d, '%s_%s.png' % (n, t))).convert('RGB').resize((c, c)), ((k0 + k) * c, r * c))
    D.text((k0 * c + 8, r * c + 6), n, fill=(255, 255, 255))
S.save(out); print(out)
