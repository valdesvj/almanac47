# almview.py - the ALMANAC page (C47 ALMF, "vintage" view) on the NumWorks.
# Sun + brightest navigation stars: GHA, Dec, Hc, Zn; twilight, rise/set,
# meridian passage, Sun SD, Moon phase. Needs nav.py, navdata.py, nwlib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from kandinsky import fill_rect, draw_string
from nwlib import text, BK, WH, GR
import nwlib
import nav


def draw(j, la, lo, sel):
    h, tab, f = nav.almanac(j, la, lo)
    fill_rect(0, 0, 320, 222, WH)
    draw_string(h[0] + ' ' + h[1] + ' UT', 0, 1, BK, WH)
    text('DR ' + h[2], 238, 2)
    text('   ' + h[3], 238, 11)
    fill_rect(0, 20, 320, 1, BK)
    text('BODY', 24, 24)
    text('GHA', 148, 24)
    text('DEC', 208, 24)
    text('HC', 268, 24)
    text('ZN', 300, 24)
    text('ARIES', 24, 35)
    text('%8s' % h[4], 118, 35)
    y = 46
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
        y += 11
    fill_rect(0, 146, 320, 1, BK)
    text('NAUT TWI ' + f[0] + ' ' + f[1], 0, 150)
    text('RISE/SET ' + f[2] + ' ' + f[3], 0, 161)
    text('MER PASS ' + f[4] + '  SD ' + f[5], 0, 172)
    text('MOON ' + f[6] + '% ' + f[7], 172, 150)
    text('AGE ' + f[8] + ' DAYS', 172, 161)
    text('UP/DOWN 1 HOUR  OK HORIZON  BACK EXIT', 49, 192, GR)
    text('DOES NOT REPLACE THE NAUTICAL ALMANAC', 49, 210)
    return sel


if not nwlib.busy:
    nwlib.run(0)
