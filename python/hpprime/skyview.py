# skyview.py - the horizon chart (C47 HORZ) on the HP Prime, as the C47 views of Oct 2026:
# the header line (date, UT, DR) with a line under it, Hc up (sine scale) / Zn across, the
# celestial equator dotted, the Sun and the same stars as the ALMANAC page; the selected body
# (LEFT/RIGHT) has its name next to it, in red; DAY / TWILIGHT / NIGHT at the bottom.
# Needs nav.py, navdata.py, hplib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from math import sin, radians
from hplib import text, rtext, sym, header, box, BK, WH, GR, RD
import hplib
import nav

X0, CW, HY, HS = 18, 300, 208, 180        # chart: left x, width, horizon y, 90 deg height


def draw(j, la, lo, sel):
    rows, s = nav.bodies(j, la, lo)
    up = [r for r in rows if r[3] > 0]     # the bodies above the horizon can be selected
    sel %= max(len(up), 1)
    off = 180 if la < 0 else 0

    def xy(zn, sh):
        return X0 + int((zn + off) % 360.0 * CW / 360.0), HY - int(sh * HS)

    box(0, 0, 320, 240, WH)
    header(j, la, lo)
    for v in (10, 20, 30, 45, 60, 90):
        y = HY - int(sin(radians(v)) * HS)
        box(13, y, 3, 1, BK)
        rtext('%d' % v, 12, y - 5)
    for y in range(HY - HS, HY, 3):
        box(16, y, 1, 1, BK)
    box(X0, HY, CW + 1, 1, BK)
    for k in range(13):
        box(X0 + k * 25, HY + 1, 1, 3, BK)
    for k in range(5):
        c = ('SWNES' if off else 'NESWN')[k]
        text(c, X0 + k * 75 - hplib.width(c) // 2, HY + 4)
    for g in range(0, 359, 2):              # celestial equator
        hc, zn, sh = nav.hcz(la, lo, 0.0, g)
        if hc > 1e-4:
            x, y = xy(zn, sh)
            box(x, y, 2, 2, GR)
    for r in up:
        k, g, d, hc, zn, sh = r
        x, y = xy(zn, sh)
        c = RD if r == up[sel] else BK
        if k == 0:
            sym('@', x - 3, y - 3, c)
            nx = x + 6
        else:
            sym('*', x - 3, y - 3, c)
            t = '%d' % k
            if x + 5 + hplib.width(t) > 318:
                rtext(t, x - 5, y - 5, c)
                nx = 999
            else:
                nx = text(t, x + 5, y - 5, c) + 4
        if c == RD:                        # the selected body: its name next to it
            t = 'SUN' if k == 0 else nav.SN[k - 1].upper()
            ny = y - 5
            if nx + hplib.width(t) > 318:  # no room on the right: above it, to the right edge
                nx, ny = 318 - hplib.width(t), y - 17
            text(t, nx, ny, c)
    t = nav.daylight(rows[0][3])
    text(t, 160 - hplib.width(t) // 2, 225)
    return sel


if not hplib.busy:
    hplib.run(1)
