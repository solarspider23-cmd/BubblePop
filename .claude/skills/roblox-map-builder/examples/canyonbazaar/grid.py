# py grid.py out.png img1 img2 ... : 3-column grid of studio shots with labels (system Python + PIL)
import sys, os
from PIL import Image, ImageDraw
out, ims = sys.argv[1], sys.argv[2:]
c = 520; cols = 3; rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (c * cols, c * rows), (20, 20, 28)); D = ImageDraw.Draw(S)
for i, p in enumerate(ims):
    S.paste(Image.open(p).convert('RGB').resize((c, c)), ((i % cols) * c, (i // cols) * c))
    D.text(((i % cols) * c + 8, (i // cols) * c + 6), os.path.basename(p), fill=(255, 255, 255))
S.save(out); print(out)
