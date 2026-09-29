"""hpprime.py - PC stand-in for the HP Prime hpprime module (preview only).
Draws G0 (320x240) into a Pillow image. eval() understands the PPL used here:
TEXTOUT_P("text",Gn,x,y,font[,RGB(r,g,b)]) (returns the x after the text),
GETKEY (keys from `script`), WAIT(...), DIMGROB_P(...).
The Prime fonts are imitated with DejaVu Sans Condensed (font n = 8 + 2n px), so text
widths in the preview are close to, not equal to, the calculator's.
script: ['SHOT:file.png', 'UP', ...]; a SHOT saves the picture; key names UP DOWN LEFT
RIGHT ENTER ESC or GETKEY numbers; when the script is used up, ESC is pressed.
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
import re
from PIL import Image, ImageDraw, ImageFont

W, H = 320, 240
img = Image.new('RGB', (W, H), (255, 255, 255))
_d = ImageDraw.Draw(img)
log = []                      # (text, x, y, font) of every TEXTOUT_P on G0
script = []
KEYS = {'UP': 2, 'DOWN': 12, 'LEFT': 7, 'RIGHT': 8, 'ENTER': 30, 'ESC': 4}
_fonts = {}
_TX = re.compile(r'TEXTOUT_P\("(.*)",G(\d),(-?\d+),(-?\d+),(\d)(?:,RGB\((\d+),(\d+),(\d+)\))?\)$')


def _font(f):
    if f not in _fonts:
        px = 8 + 2 * f
        for name in ('DejaVuSansCondensed.ttf',
                     '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf'):
            try:
                _fonts[f] = ImageFont.truetype(name, px)
                break
            except OSError:
                pass
        else:
            _fonts[f] = ImageFont.load_default()
    return _fonts[f]


def _c(c):
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


def fillrect(g, x, y, w, h, edge, fill):
    if g == 0 and w > 0 and h > 0:
        _d.rectangle((x, y, x + w - 1, y + h - 1), fill=_c(fill), outline=_c(edge))


def rect(g, x, y, w, h, c):
    if g == 0:
        _d.rectangle((x, y, x + w - 1, y + h - 1), outline=_c(c))


def pixon(g, x, y, c):
    if g == 0 and 0 <= x < W and 0 <= y < H:
        img.putpixel((int(x), int(y)), _c(c))


def line(g, x1, y1, x2, y2, c):
    if g == 0:
        _d.line((x1, y1, x2, y2), fill=_c(c))


def textout(g, x, y, s, c):
    return eval('TEXTOUT_P("%s",G%d,%d,%d,1,RGB(%d,%d,%d))' % ((s, g, x, y) + _c(c)))


def keyboard():
    return 0


def save(path, scale=2):
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)


def eval(s):
    m = _TX.match(s)
    if m:
        t, g, x, y, f = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        col = (0, 0, 0) if m.group(6) is None else tuple(int(m.group(i)) for i in (6, 7, 8))
        fo = _font(f)
        if g == 0:
            log.append((t, x, y, f))
            _d.text((x, y), t, font=fo, fill=col)
        return x + int(round(fo.getlength(t)))
    if s == 'GETKEY':
        while script and script[0].startswith('SHOT:'):
            save(script.pop(0)[5:])
        if not script:
            return 4
        k = script.pop(0)
        return KEYS[k] if k in KEYS else int(k)
    if s.startswith('WAIT(') or s.startswith('DIMGROB_P('):
        return 0
    raise ValueError('PPL not emulated: ' + s)
