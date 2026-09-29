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


def text(s, x, y, c=BK):
    """Small font at (x, y) = top left; returns the next x."""
    for ch in s:
        i = C.find(ch)
        w = 7 if i > 42 else 5
        if i > 0:
            i *= 7
            for k in range(w):
                b = F[i + k]
                r = 0
                while r < 7:
                    if b >> (6 - r) & 1:
                        t = r
                        while r < 7 and b >> (6 - r) & 1:
                            r += 1
                        fill_rect(x + k, y + t, 1, r - t, c)
                    r += 1
        x += w + 1
    return x


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
    UP/DOWN one hour later/earlier, OK/EXE other view, LEFT/RIGHT body, BACK exit."""
    global busy
    busy = 1
    print('ALMANAC 47 - does not')
    print('replace the Nautical Almanac')
    y, m, d = nav.ask_date()
    j0 = nav.jd(y, m, d, nav.ask_ut())
    la = nav.ask_ang('Lat (N+) d m: ')
    lo = nav.ask_ang('Lon (E+ W-) d m: ')
    h = sel = 0
    try:
        while 1:
            if v:
                import skyview as w
            else:
                import almview as w
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
