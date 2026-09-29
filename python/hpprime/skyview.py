# skyview.py - the horizon chart (C47 HORZ) on the HP Prime.
# Hc up (sine scale) / Zn across, celestial equator dotted, the Sun and the
# brightest navigation stars. Top line: the selected body (LEFT/RIGHT).
# Needs nav.py, navdata.py, hplib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from math import sin, radians
from hplib import text, rtext, sym, box, BK, WH, GR, RD
import hplib
import nav

X0, CW, HY, HS = 18, 300, 216, 180        # chart: left x, width, horizon y, 90 deg height


def draw(j, la, lo, sel):
    rows, s = nav.bodies(j, la, lo, 10)
    sel %= len(rows)
    off = 180 if la < 0 else 0

    def xy(zn, sh):
        return X0 + int((zn + off) % 360.0 * CW / 360.0), HY - int(sh * HS)

    box(0, 0, 320, 240, WH)
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
        text(c, X0 + k * 75 - hplib.width(c) // 2, HY + 5)
    for g in range(0, 359, 2):              # celestial equator
        hc, zn, sh = nav.hcz(la, lo, 0.0, g)
        if hc > 1e-4:
            x, y = xy(zn, sh)
            box(x, y, 2, 2, GR)
    i = 0
    for k, g, d, hc, zn, sh in rows:
        x, y = xy(zn, sh)
        c = RD if i == sel else BK
        if k == 0:
            if hc > 0:
                sym('@', x - 3, y - 3, c)
        else:
            sym('*', x - 3, y - 3, c)
            t = '%d' % k
            if x + 5 + hplib.width(t) > 318:
                rtext(t, x - 5, y - 5, c)
            else:
                text(t, x + 5, y - 5, c)
        if i == sel:
            t = ('SUN' if k == 0 else '%d %s' % (k, nav.SN[k - 1].upper()))
            z = '   ZN ' + nav.f1(zn) + '   HC ' + ('-' if hc < 0 else '') + nav.f1(hc)
            if hplib.width(t + z, 4) > 318:
                t = '%d' % k
            text(t + z, 1, 0, c, 4)
        i += 1
    y, m, d, h = nav.cal(j)
    text(nav.fdate(j) + '  ' + nav.fhm(h) + ' UT', 1, 20)
    rtext(nav.fns(la, 'NS', 0) + '   ' + nav.fns(lo, 'EW', 0), 318, 20)
    return sel


if not hplib.busy:
    hplib.run(1)
