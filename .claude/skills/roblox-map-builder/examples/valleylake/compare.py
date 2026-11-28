# py compare.py ref.(webp|png) render.png out.png : side by side at equal height with labels
import sys
from PIL import Image, ImageDraw
a = Image.open(sys.argv[1]).convert('RGB'); b = Image.open(sys.argv[2]).convert('RGB'); H = 640
a = a.resize((round(a.width * H / a.height), H)); b = b.resize((round(b.width * H / b.height), H))
o = Image.new('RGB', (a.width + b.width + 12, H + 34), (20, 22, 30)); o.paste(a, (0, 34)); o.paste(b, (a.width + 12, 34))
d = ImageDraw.Draw(o); d.text((10, 10), 'reference', fill=(255, 255, 255)); d.text((a.width + 22, 10), 'Mistvale Lake (Blender preview)', fill=(255, 255, 255))
o.save(sys.argv[3])
