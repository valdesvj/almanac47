from fontsim import *
import c47screen as S
from c47view import jd
from c47data import STAR_NAME
from PIL import Image, ImageDraw
src = Image.open('tny/chart.png').resize((400, 240), Image.NEAREST)
base = Image.new('L', (400, 240), 235)
keep = set()
for x in range(400):
    for y in range(240):
        r = 239 - y
        if src.getpixel((x, y)) < 128 and (x < 175 or (x < 190 and 30 < r < 178)):   # chart + the body symbols
            keep.add((r, x))
al = S.Almanac(jd(2026, 9, 26, 14 + 57 / 60), 25 + 20 / 60, 55.2)
rows = al.bodies()
def fdm(v):
    a = abs(v); d = int(a); m = round((a - d) * 60, 1)
    if m >= 60: d, m = d + 1, 0
    return ('-' if v < 0 else '') + '%d %04.1f' % (d, m)
out = []
for fid, nums, label in ((20, False, 'now: 20 standard, no numbers'), (21, True, '21 compressed + numbers'),
                         (10, True, '10 tiny + numbers'), (32, True, '32 small numeric + numbers'),
                         (22, True, '22 bold + numbers')):
    p = set(keep)
    X0, NM = 176, 190
    draw(p, X0, 222, '26-09-2026 14:57 UT', 20 if fid not in (10, 32) else fid)
    draw(p, X0, 208, 'N 25 20.0 E  55 12.0', 20 if fid not in (10, 32) else fid)
    hdr = 184
    draw(p, NM, hdr, 'BODY', fid); draw(p, 398 - width('ZN', fid) - 8, hdr, 'ZN', fid); draw(p, 320, hdr, 'HC', fid)
    y = 170
    over = []
    for ident, g, d, hc, zn in rows:
        name = S.body_name(ident)
        t = ('%d %s' % (ident, name)) if (nums and ident > 0) else name
        x = draw(p, NM, y, t, fid)
        h, z = fdm(hc), '%05.1f' % zn
        zx = 398 - width(z, fid); hx = zx - 8 - width(h, fid)
        if x > hx - 3: over.append(name)
        draw(p, hx, y, h, fid); draw(p, zx, y, z, fid)
        y -= 14
    path = 'fs/chart_%d.png' % fid
    save(p, path)
    im = Image.open(path); d = ImageDraw.Draw(im)
    out.append((im, label + ('  (TOO WIDE: %s)' % ', '.join(over) if over else '')))
W = Image.new('L', (1620, 30 + 3 * 520), 255); dr = ImageDraw.Draw(W)
for i, (im, lab) in enumerate(out):
    x, y = (i % 2) * 820, (i // 2) * 520
    dr.text((x + 4, y + 4), lab, fill=0); W.paste(im, (x, y + 22))
W.save('fs/chart_fonts.png'); print([l for _, l in out])
