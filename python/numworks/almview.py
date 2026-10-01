# almview.py - the ALMANAC page (C47 ALMF) on the NumWorks, as the C47 views of Oct 2026:
# one header line (date, UT, DR) with a line under it, the Sun and the same brightest stars as
# the horizon chart (nav.NBODY bodies), GHA Dec Hc Zn; twilight, rise/set, meridian passage,
# Sun SD, Moon phase with its glyph. Needs nav.py, navdata.py, nwlib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from kandinsky import fill_rect
from nwlib import text, moon, header, BK, WH, GR
import nwlib
import nav


def draw(j, la, lo, sel):
    h, tab, f = nav.almanac(j, la, lo)
    fill_rect(0, 0, 320, 222, WH)
    header(j, la, lo)
    text('BODY', 24, 17)
    text('GHA', 148, 17)
    text('DEC', 208, 17)
    text('HC', 268, 17)
    text('ZN', 300, 17)
    text('ARIES', 24, 29)
    text('%8s' % h[4], 118, 29)
    y = 41
    for k, nm, g, d, hc, zn, x in tab:
        if k:
            text('*', 0, y)
            text('%2d' % k, 9, y)
        else:
            text('@', 0, y)
        text(nm, 24, y)
        text('%8s' % g, 118, y)
        text(d, 172, y)
        if x < 0:                          # below the horizon: Hc inverted
            fill_rect(230, y - 2, 52, 11, BK)
            text('%8s' % hc, 232, y, WH)
        else:
            text('%8s' % hc, 232, y)
        text(zn, 288, y)
        y += 12
    fill_rect(0, 139, 320, 1, BK)
    text('NAUT TWI ' + f[0] + ' ' + f[1], 0, 144)
    text('RISE/SET ' + f[2] + ' ' + f[3], 0, 156)
    text('MER PASS ' + f[4] + '  SD ' + f[5], 0, 168)
    x = text('MOON ' + f[6] + '% ', 172, 144)
    x = moon(nav.phase_index(float(f[8])), x, 144)
    text(' ' + f[7], x, 144)
    text('AGE ' + f[8] + ' DAYS', 172, 156)
    text('UP/DOWN 1 HOUR  OK HORIZON  BACK EXIT', 49, 192, GR)
    text('DOES NOT REPLACE THE NAUTICAL ALMANAC', 49, 210)
    return sel


if not nwlib.busy:
    nwlib.run(0)
