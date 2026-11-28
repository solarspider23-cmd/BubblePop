# py post.py in.png out.png : soft bloom (threshold + two blurs) + mild vibrance, the preview stand-in for Roblox Bloom
import sys, numpy as np
from PIL import Image, ImageFilter
im = Image.open(sys.argv[1]).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
lum = a @ np.array([.3, .59, .11]); m = np.clip((lum - .72) / .28, 0, 1)[..., None] * a
mi = Image.fromarray((m * 255).astype(np.uint8))
b = (np.asarray(mi.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) * .5 + np.asarray(mi.filter(ImageFilter.GaussianBlur(24))).astype(np.float32) * .6) / 255
o = np.clip(a + b * .75, 0, 1)
o = np.clip((o - .5) * 1.08 + .52, 0, 1); g = o.mean(axis=2, keepdims=True); o = np.clip(g + (o - g) * 1.15, 0, 1)
Image.fromarray((o * 255).astype(np.uint8)).save(sys.argv[2])
