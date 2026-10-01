# nwlib.py - text, keys and the main loop of almview.py / skyview.py (NumWorks).
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from kandinsky import fill_rect, color
from ion import keydown, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_OK, KEY_EXE, KEY_BACK
from time import sleep
import nav

BK = color(0, 0, 0)
WH = color(255, 255, 255)
GR = color(140, 140, 140)
RD = color(200, 0, 0)
# 5x7 font of the C47 programs (PTXB); 7 column bytes per character, bit 6 = top row.
# '*' = star, '@' = Sun (7 columns wide, advance 8).
C = " %'-./0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ*@"
F = b'\x00\x00\x00\x00\x00\x00\x00bd\x08\x13#\x00\x00\x00\x00`\x00\x00\x00\x00\x08\x08\x08\x08\x08\x00\x00\x00\x03\x03\x00\x00\x00\x00\x02\x04\x08\x10 \x00\x00>EIQ>\x00\x00\x00!\x7f\x01\x00\x00\x00!CEI1\x00\x00BAQiF\x00\x00\x0c\x14$\x7f\x04\x00\x00rQQQN\x00\x00\x1e)II\x06\x00\x00@GHP`\x00\x006III6\x00\x000IIJ<\x00\x00\x0066\x00\x00\x00\x00?HHH?\x00\x00\x7fIII6\x00\x00>AAA"\x00\x00\x7fAA"\x1c\x00\x00\x7fIIIA\x00\x00\x7fHHH@\x00\x00>AII/\x00\x00\x7f\x08\x08\x08\x7f\x00\x00\x00A\x7fA\x00\x00\x00\x02\x01A~@\x00\x00\x7f\x08\x14"A\x00\x00\x7f\x01\x01\x01\x01\x00\x00\x7f \x18 \x7f\x00\x00\x7f\x10\x08\x04\x7f\x00\x00>AAA>\x00\x00\x7fHHH0\x00\x00>AEB=\x00\x00\x7fHLJ1\x00\x001IIIF\x00\x00@@\x7f@@\x00\x00~\x01\x01\x01~\x00\x00|\x02\x01\x02|\x00\x00~\x01\x0e\x01~\x00\x00c\x14\x08\x14c\x00\x00p\x08\x07\x08p\x00\x00CEIQa\x00\x00\x10\x1b\x1e|\x1e\x1b\x10\x1c"AIA"\x1c'


# the eight Moon phases, 7x7 columns as F (0 new ... 4 full ... 7 waning crescent; waxing lit on
# the right): the glyphs of the C47 views (tools/generators/atext/glyphs47.py) at 7 rows
MP = b'\x1c"AAA"\x1c\x1c"AAA>\x1c\x1c"AA\x7f>\x1c\x1c"\x7f\x7f\x7f>\x1c\x1c>\x7f\x7f\x7f>\x1c\x1c>\x7f\x7f\x7f"\x1c\x1c>\x7f\x7fA"\x1c\x1c>AAA"\x1c'


def cols(b, i, w, x, y, c=BK):
    """w column bytes of b from i (bit 6 = top row) at (x, y): runs of pixels as rectangles."""
    for k in range(w):
        v = b[i + k]
        r = 0
        while r < 7:
            if v >> (6 - r) & 1:
                t = r
                while r < 7 and v >> (6 - r) & 1:
                    r += 1
                fill_rect(x + k, y + t, 1, r - t, c)
            r += 1


def moon(p, x, y, c=BK):
    """Moon phase glyph p (nav.phase_index) at (x, y) = top left; returns the next x."""
    cols(MP, 7 * p, 7, x, y, c)
    return x + 8


def text(s, x, y, c=BK):
    """Small font at (x, y) = top left; returns the next x."""
    for ch in s:
        i = C.find(ch)
        w = 7 if i > 42 else 5
        if i > 0:
            cols(F, 7 * i, w, x, y, c)
        x += w + 1
    return x


def header(j, la, lo):
    """The header of every view: date, UT, DR; the line under it."""
    y, m, d, h = nav.cal(j)
    text(nav.fdate(j) + ' ' + nav.fhm(h) + ' UT  DR ' + nav.fns(la, 'NS', 0) + ' ' + nav.fns(lo, 'EW', 0), 0, 2)
    fill_rect(0, 12, 320, 1, BK)


def key():
    """Wait for one of the keys used here and for its release."""
    while 1:
        for k in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_OK, KEY_EXE, KEY_BACK):
            if keydown(k):
                while keydown(k):
                    sleep(0.02)
                return k
        sleep(0.03)


busy = 0


def run(v):
    """Ask date, UT and DR, then draw view v (0 ALMANAC, 1 HORIZON).
    UP/DOWN one hour later/earlier, OK/EXE other view, LEFT/RIGHT body (horizon), BACK exit."""
    global busy
    busy = 1
    print('ALMANAC 47 - does not')
    print('replace the Nautical Almanac')
    y, m, d = nav.ask_date()
    j0 = nav.jd(y, m, d, nav.ask_ut())
    la = nav.ask_ang('Lat (N+) d m: ')
    lo = nav.ask_ang('Lon (E+ W-) d m: ')
    import almview
    import skyview
    h = sel = 0
    try:
        while 1:
            w = skyview if v else almview
            sel = w.draw(j0 + h / 24.0, la, lo, sel)
            k = key()
            if k == KEY_UP:
                h += 1
            elif k == KEY_DOWN:
                h -= 1
            elif k == KEY_OK or k == KEY_EXE:
                v = 1 - v
            elif k == KEY_RIGHT:
                sel += 1
            elif k == KEY_LEFT:
                sel -= 1
            else:
                break
    except KeyboardInterrupt:
        pass
    busy = 0
