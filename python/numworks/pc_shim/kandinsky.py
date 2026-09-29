"""kandinsky.py - PC stand-in for the NumWorks kandinsky module (preview only).
Draws into a 320x222 Pillow image; save(path) writes it (2x, nearest neighbour).
draw_string uses the 10x18 cell of the calculator's large font, but the glyphs are
DejaVu Sans Mono, not the NumWorks font.
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
from PIL import Image, ImageDraw, ImageFont

W, H = 320, 222
img = Image.new('RGB', (W, H), (255, 255, 255))
_d = ImageDraw.Draw(img)
log = []                      # (text, x, y) of every draw_string, for the tests
try:
    _f = ImageFont.truetype('DejaVuSansMono.ttf', 15)
except OSError:
    try:
        _f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 15)
    except OSError:
        _f = ImageFont.load_default()


def color(r, g=None, b=None):
    if g is None:
        r, g, b = r
    return (int(r) & 255, int(g) & 255, int(b) & 255)


def _c(c):
    return color(c) if isinstance(c, (tuple, list)) else color(c >> 16, c >> 8, c)


def set_pixel(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((int(x), int(y)), _c(c))


def get_pixel(x, y):
    return img.getpixel((x, y))


def fill_rect(x, y, w, h, c):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w > 0 and h > 0:
        _d.rectangle((x, y, x + w - 1, y + h - 1), fill=_c(c))


def draw_string(s, x, y, c=(0, 0, 0), bg=(255, 255, 255)):
    log.append((s, x, y))
    for i, ch in enumerate(s):
        cx = x + 10 * i
        _d.rectangle((cx, y, cx + 9, y + 17), fill=_c(bg))
        _d.text((cx + 1, y + 1), ch, font=_f, fill=_c(c))


def save(path, scale=2):
    img.resize((W * scale, H * scale), Image.NEAREST).save(path)
