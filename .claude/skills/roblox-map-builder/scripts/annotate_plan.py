# Part of roblox-map-builder. Proprietary, see LICENSE.md.
# Annotate a render_plan.py image: numbered markers at world points + a legend strip + an optional title.
#   python annotate_plan.py spec.json
# spec = {"img": "plan.png", "out": "plan_annotated.png", "center": [X, Z], "size": S, "title": "...",
#         "labels": [{"text": "Spawn", "x": 0, "z": 212, "color": "#ff4f9a"}, ...],
#         "arrows": [{"from": [x, z], "to": [x, z], "color": "#ffffff"}]}       (world studs, Roblox X east / Z south)
import json, sys, os
from PIL import Image, ImageDraw, ImageFont

def font(px, bold=True):
    for f in (('arialbd.ttf' if bold else 'arial.ttf'), 'DejaVuSans-Bold.ttf', 'DejaVuSans.ttf'):
        for root in ('C:/Windows/Fonts', '/usr/share/fonts/truetype/dejavu', '/Library/Fonts'):
            p = os.path.join(root, f)
            if os.path.exists(p): return ImageFont.truetype(p, px)
    return ImageFont.load_default()

def main(spec_path):
    S = json.load(open(spec_path, encoding='utf8')); base = os.path.dirname(os.path.abspath(spec_path))
    im = Image.open(os.path.join(base, S['img'])).convert('RGB'); W, H = im.size
    cx, cz = S['center']; size = S['size']
    px = lambda x, z: ((x - cx) / size * W + W / 2, (z - cz) / size * H + H / 2)
    legend_w = 520
    out = Image.new('RGB', (W + legend_w, H), (24, 22, 34)); out.paste(im, (0, 0))
    d = ImageDraw.Draw(out); f = font(30); fs = font(26, False); ft = font(40)
    for a in S.get('arrows', []):
        (x0, y0), (x1, y1) = px(*a['from']), px(*a['to'])
        d.line((x0, y0, x1, y1), fill=a.get('color', '#ffffff'), width=6)
        import math
        ang = math.atan2(y1 - y0, x1 - x0)
        for s in (2.6, -2.6):
            d.line((x1, y1, x1 - 26 * math.cos(ang + s * .2), y1 - 26 * math.sin(ang + s * .2)), fill=a.get('color', '#ffffff'), width=6)
    for i, L in enumerate(S['labels'], 1):
        x, y = px(L['x'], L['z']); col = L.get('color', '#ffd23c'); r = 26
        d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline='#111111', width=4)
        t = str(i); tw = d.textlength(t, font=f); d.text((x - tw / 2, y - 18), t, fill='#111111', font=f)
    y = 30
    if S.get('title'):
        d.text((W + 24, y), S['title'], fill='#ffffff', font=ft); y += 70
    for i, L in enumerate(S['labels'], 1):
        col = L.get('color', '#ffd23c')
        d.ellipse((W + 24, y, W + 64, y + 40), fill=col, outline='#111111', width=3)
        t = str(i); tw = d.textlength(t, font=fs); d.text((W + 44 - tw / 2, y + 6), t, fill='#111111', font=fs)
        words = L['text'].split(); line = ''; ly = y + 4
        for w in words:                                            # wrap to the legend width
            if d.textlength(line + ' ' + w, font=fs) > legend_w - 100:
                d.text((W + 78, ly), line.strip(), fill='#f2f2f2', font=fs); ly += 32; line = ''
            line += ' ' + w
        d.text((W + 78, ly), line.strip(), fill='#f2f2f2', font=fs)
        y = ly + 48
    bar = 50 if size < 900 else 100; bl = bar / size * W                       # scale bar
    d.rectangle((W + 24, H - 44, W + 24 + bl, H - 32), fill='#ffffff'); d.text((W + 34 + bl, H - 58), '%d studs   N up' % bar, fill='#cfcbe0', font=fs)
    out.save(os.path.join(base, S['out'])); print('ANNOTATED', S['out'])

if __name__ == '__main__': main(sys.argv[1])
