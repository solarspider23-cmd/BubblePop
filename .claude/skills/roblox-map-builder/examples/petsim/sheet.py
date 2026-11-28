# grid contact sheet: py sheet.py <dir> [cols=2 props per row]  -> <dir>/sheet.png (front|back per prop)
import sys, os
from PIL import Image
d = sys.argv[1]; per = int(sys.argv[2]) if len(sys.argv) > 2 else 2
names = sorted({f.rsplit('_', 1)[0] for f in os.listdir(d) if f.endswith('_front.png')})
c = 400; rows = (len(names) + per - 1) // per
S = Image.new('RGB', (c * 2 * per, c * rows))
for i, n in enumerate(names):
    for k, t in enumerate(('front', 'back')):
        S.paste(Image.open(os.path.join(d, '%s_%s.png' % (n, t))).convert('RGB').resize((c, c)), (((i % per) * 2 + k) * c, (i // per) * c))
S.save(os.path.join(d, 'sheet.png')); print(names)
