# hplib.py - text, symbols, keys and the main loop of almview.py / skyview.py
# on the HP Prime (MicroPython app, hpprime module).
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from hpprime import eval as ev, fillrect
import nav

BK = 0x000000
WH = 0xFFFFFF
GR = 0x8C8C8C
RD = 0xC80000
# the same 7x7 symbols as the C47 programs: '*' star, '@' Sun (bit 6 = top row)
SYM = {'*': b'\x10\x1b\x1e|\x1e\x1b\x10', '@': b'\x1c"AIA"\x1c'}
_w = {}


def _rgb(c):
    return 'RGB(%d,%d,%d)' % (c >> 16, c >> 8 & 255, c & 255)


def num(v):
    """A number from hpprime.eval: it may come as int, float or text ('2', '2.')"""
    return int(float(v))


def width(s, f=1):
    """Width in pixels of s in TEXTOUT_P font f (measured once per character
    on the hidden grob G9; TEXTOUT_P returns the x after the text)."""
    t = 0
    for ch in s:
        k = ch + str(f)
        if k not in _w:
            try:
                _w[k] = num(ev('TEXTOUT_P("%s",G9,0,0,%d)' % (ch.replace('"', "'"), f)))
            except Exception:
                _w[k] = 4 + 2 * f
        t += _w[k]
    return t


def text(s, x, y, c=BK, f=1):
    """TEXTOUT_P on the screen (G0), top left at (x, y); font 1 small ... 7 large."""
    ev('TEXTOUT_P("%s",G0,%d,%d,%d,%s)' % (s.replace('"', "'"), x, y, f, _rgb(c)))
    return x + width(s, f)


def rtext(s, xr, y, c=BK, f=1):
    """Text ending at xr (right-aligned)."""
    return text(s, xr - width(s, f), y, c, f)


def sym(ch, x, y, c=BK):
    """Star or Sun symbol, 7x7, top left at (x, y)."""
    b = SYM[ch]
    for k in range(7):
        r = 0
        while r < 7:
            if b[k] >> (6 - r) & 1:
                t = r
                while r < 7 and b[k] >> (6 - r) & 1:
                    r += 1
                fillrect(0, x + k, y + t, 1, r - t, c, c)
            r += 1


def box(x, y, w, h, c):
    fillrect(0, x, y, w, h, c, c)


def key():
    """Wait for UP 2, DOWN 12, LEFT 7, RIGHT 8, ENTER 30 or ESC 4 (GETKEY codes)."""
    while 1:
        try:
            k = num(ev('GETKEY'))
        except Exception:
            k = -1
        if k in (2, 12, 7, 8, 30, 4):
            return k
        ev('WAIT(0.05)')


busy = 0


def run(v):
    """Ask date, UT and DR, then draw view v (0 ALMANAC, 1 HORIZON).
    UP/DOWN one hour later/earlier, ENTER other view, LEFT/RIGHT body, ESC exit."""
    global busy
    busy = 1
    print('ALMANAC 47 - does not')
    print('replace the Nautical Almanac')
    y, m, d = nav.ask_date()
    j0 = nav.jd(y, m, d, nav.ask_ut())
    la = nav.ask_ang('Lat (N+) d m: ')
    lo = nav.ask_ang('Lon (E+ W-) d m: ')
    ev('DIMGROB_P(G9,320,30)')
    import almview
    import skyview
    h = sel = 0
    try:
        while 1:
            w = skyview if v else almview
            sel = w.draw(j0 + h / 24.0, la, lo, sel)
            k = key()
            if k == 2:
                h += 1
            elif k == 12:
                h -= 1
            elif k == 30:
                v = 1 - v
            elif k == 8:
                sel += 1
            elif k == 7:
                sel -= 1
            else:
                break
    except KeyboardInterrupt:
        pass
    except Exception as e:                 # show what went wrong instead of closing
        print('ERROR:', repr(e))
        try:
            import sys
            sys.print_exception(e)
        except Exception:
            pass
    busy = 0
