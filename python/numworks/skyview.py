# skyview.py - the horizon chart (C47 HORZ) on the NumWorks, as the C47 views of Oct 2026:
# the header line (date, UT, DR) with a line under it, Hc up (sine scale) / Zn across, the
# celestial equator dotted, the Sun and the same stars as the ALMANAC page; the selected body
# (LEFT/RIGHT) has its name next to it, in red; DAY / TWILIGHT / NIGHT at the bottom.
# Needs nav.py, navdata.py, nwlib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from math import sin, radians
from kandinsky import fill_rect
from nwlib import text, header, BK, WH, GR, RD
import nwlib
import nav

X0, CW, HY, HS = 18, 300, 194, 172        # chart: left x, width, horizon y, 90 deg height


def draw(j, la, lo, sel):
    rows, s = nav.bodies(j, la, lo)
    up = [r for r in rows if r[3] > 0]     # the bodies above the horizon can be selected
    sel %= max(len(up), 1)
    off = 180 if la < 0 else 0

    def xy(zn, sh):
        return X0 + int((zn + off) % 360.0 * CW / 360.0), HY - int(sh * HS)

    fill_rect(0, 0, 320, 222, WH)
    header(j, la, lo)
    for v in (10, 20, 30, 45, 60, 90):
        y = HY - int(sin(radians(v)) * HS)
        fill_rect(13, y, 3, 1, BK)
        text('%d' % v, 0, y - 3)
    for y in range(HY - HS, HY, 3):
        fill_rect(16, y, 1, 1, BK)
    fill_rect(X0, HY, CW + 1, 1, BK)
    for k in range(13):
        fill_rect(X0 + k * 25, HY + 1, 1, 3, BK)
    for k in range(5):
        text(('SWNES' if off else 'NESWN')[k], X0 - 2 + k * 75, HY + 5)
    for g in range(0, 359, 2):              # celestial equator
        hc, zn, sh = nav.hcz(la, lo, 0.0, g)
        if hc > 1e-4:
            x, y = xy(zn, sh)
            fill_rect(x, y, 2, 2, GR)
    for r in up:
        k, g, d, hc, zn, sh = r
        x, y = xy(zn, sh)
        c = RD if up and r == up[sel] else BK
        t = 'SUN' if k == 0 else nav.SN[k - 1].upper()
        if k == 0:
            text('@', x - 3, y - 3, c)
            nx = x + 6
        else:
            text('*', x - 3, y - 3, c)
            n = '%d' % k
            lx = x + 5
            if lx + 6 * len(n) > 318:
                lx = x - 5 - 6 * len(n)
            text(n, lx, y - 3, c)
            nx = lx + 6 * len(n) + 3
        if c == RD:                        # the selected body: its name next to it
            ny = y - 3
            if nx + 6 * len(t) > 318:      # no room on the right: above it, to the right edge
                nx, ny = 318 - 6 * len(t), y - 13
            text(t, nx, ny, c)
    t = nav.daylight(rows[0][3])
    text(t, 160 - 3 * len(t), 212)
    return sel


if not nwlib.busy:
    nwlib.run(1)
