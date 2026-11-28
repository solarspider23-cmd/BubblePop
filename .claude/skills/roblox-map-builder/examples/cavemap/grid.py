# py grid.py <dir> <out.png> [cols] [tag]: tile <dir>/*_<tag>.png (default front) into one sheet with names
import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3; tag = sys.argv[4] if len(sys.argv) > 4 else 'front'
fs = sorted(glob.glob(os.path.join(d, '*_%s.png' % tag))); c = 520
im = Image.new('RGB', (c * cols, c * ((len(fs) + cols - 1) // cols)), (30, 30, 40)); dr = ImageDraw.Draw(im)
for i, f in enumerate(fs):
    im.paste(Image.open(f).convert('RGB').resize((c, c)), ((i % cols) * c, (i // cols) * c)); dr.text(((i % cols) * c + 6, (i // cols) * c + 6), os.path.basename(f), fill=(255, 255, 255))
im.save(out)
