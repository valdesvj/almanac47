# skyview.py - the horizon chart (C47 HORZ) on the NumWorks.
# Hc up (sine scale) / Zn across, celestial equator dotted, the Sun and the
# brightest navigation stars. Top line: the selected body (LEFT/RIGHT).
# Needs nav.py, navdata.py, nwlib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from math import sin, radians
from kandinsky import fill_rect, draw_string
from nwlib import text, BK, WH, GR, RD
import nwlib
import nav

X0, CW, HY, HS = 18, 300, 203, 170        # chart: left x, width, horizon y, 90 deg height


def draw(j, la, lo, sel):
    rows, s = nav.bodies(j, la, lo, 10)
    sel %= len(rows)
    off = 180 if la < 0 else 0

    def xy(zn, sh):
        return X0 + int((zn + off) % 360.0 * CW / 360.0), HY - int(sh * HS)

    fill_rect(0, 0, 320, 222, WH)
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
        text(('SWNES' if off else 'NESWN')[k], X0 - 2 + k * 75, HY + 6)
    for g in range(0, 359, 2):              # celestial equator
        hc, zn, sh = nav.hcz(la, lo, 0.0, g)
        if hc > 1e-4:
            x, y = xy(zn, sh)
            fill_rect(x, y, 2, 2, GR)
    i = 0
    for k, g, d, hc, zn, sh in rows:
        x, y = xy(zn, sh)
        c = RD if i == sel else BK
        if k == 0:
            if hc > 0:
                text('@', x - 3, y - 3, c)
        else:
            text('*', x - 3, y - 3, c)
            lx = x + 5
            if lx > 305:
                lx = x - 18
            text('%d' % k, lx, y - 3, c)
        if i == sel:
            t = ('SUN' if k == 0 else '%d %s' % (k, nav.SN[k - 1].upper()))
            z = '  ZN ' + nav.f1(zn) + '  HC ' + ('-' if hc < 0 else '') + nav.f1(hc)
            if len(t + z) > 32:
                t = '%d' % k
            draw_string(t + z, 0, 0, c, WH)
        i += 1
    y, m, d, h = nav.cal(j)
    text(nav.fdate(j) + ' ' + nav.fhm(h) + ' UT', 0, 21)
    t = nav.fns(la, 'NS', 0) + '  ' + nav.fns(lo, 'EW', 0)
    text(t, 320 - 6 * len(t), 21)
    return sel


if not nwlib.busy:
    nwlib.run(1)
