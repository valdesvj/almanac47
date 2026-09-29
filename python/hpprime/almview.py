# almview.py - the ALMANAC page (C47 ALMF, "vintage" view) on the HP Prime.
# Sun + brightest navigation stars: GHA, Dec, Hc, Zn; twilight, rise/set,
# meridian passage, Sun SD, Moon phase. Needs nav.py, navdata.py, hplib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from hplib import text, rtext, sym, box, BK, WH, GR
import hplib
import nav


def dm(s, xr, y, c=BK):
    """'174 26.9' with the minutes right-aligned at xr and the degrees 4 px before
    them (the Prime's space is narrow)."""
    i = s.rfind(' ')
    x = rtext(s[i + 1:], xr, y, c) - hplib.width(s[i + 1:])
    rtext(s[:i].strip(), x - 4, y, c)


def draw(j, la, lo, sel):
    h, tab, f = nav.almanac(j, la, lo)
    box(0, 0, 320, 240, WH)
    text(h[0] + '  ' + h[1] + ' UT', 1, 0, BK, 4)
    rtext('DR ' + h[2], 318, 0)
    rtext(h[3], 318, 10)
    box(0, 22, 320, 1, BK)
    text('BODY', 25, 25)
    rtext('GHA', 170, 25)
    rtext('DEC', 230, 25)
    rtext('HC', 284, 25)
    rtext('ZN', 318, 25)
    text('ARIES', 25, 37)
    dm(h[4], 170, 37)
    y = 49
    for k, nm, g, d, hc, zn, x in tab:
        if k:
            sym('*', 1, y + 2)
            rtext('%d' % k, 22, y)
        else:
            sym('@', 1, y + 2)
        text(nm, 25, y)
        dm(g, 170, y)
        text(d[0], 180, y)
        dm(d[1:], 230, y)
        if x < 0:                          # below the horizon: Hc inverted
            box(236, y, 51, 12, BK)
            dm(hc, 284, y, WH)
        else:
            dm(hc, 284, y)
        rtext(zn, 318, y)
        y += 12
    box(0, 159, 320, 1, BK)
    text('NAUT TWI  ' + f[0] + '  ' + f[1], 1, 163)
    text('RISE/SET  ' + f[2] + '  ' + f[3], 1, 175)
    text('MER PASS  ' + f[4] + '   SD ' + f[5], 1, 187)
    text('MOON ' + f[6] + '% ' + f[7], 176, 163)
    text('AGE ' + f[8] + ' DAYS', 176, 175)
    t = 'UP/DOWN 1 HOUR   ENTER HORIZON   ESC EXIT'
    rtext(t, 160 + hplib.width(t) // 2, 205, GR)
    t = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'
    rtext(t, 160 + hplib.width(t) // 2, 225)
    return sel


if not hplib.busy:
    hplib.run(0)
