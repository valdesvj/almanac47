# almview.py - the ALMANAC page (C47 ALMF) on the HP Prime, as the C47 views of Oct 2026:
# one header line (date, UT, DR) with a line under it, the Sun and the same brightest stars
# as the horizon chart (nav.NBODY bodies), GHA Dec Hc Zn; twilight, rise/set, meridian
# passage, Sun SD, Moon phase with its glyph. Needs nav.py, navdata.py, hplib.py.
# Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later.
# Supports, does not replace, the Nautical Almanac.
from hplib import text, rtext, sym, moon, header, box, BK, WH, GR
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
    header(j, la, lo)
    text('BODY', 25, 19)
    rtext('GHA', 170, 19)
    rtext('DEC', 230, 19)
    rtext('HC', 284, 19)
    rtext('ZN', 318, 19)
    text('ARIES', 25, 32)
    dm(h[4], 170, 32)
    y = 45
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
        y += 13
    box(0, 151, 320, 1, BK)
    text('NAUT TWI  ' + f[0] + '  ' + f[1], 1, 156)
    text('RISE/SET  ' + f[2] + '  ' + f[3], 1, 168)
    text('MER PASS  ' + f[4] + '   SD ' + f[5], 1, 180)
    x = text('MOON ' + f[6] + '% ', 176, 156)
    x = moon(nav.phase_index(float(f[8])), x, 158)
    text(f[7], x + 2, 156)
    text('AGE ' + f[8] + ' DAYS', 176, 168)
    t = 'UP/DOWN 1 HOUR   ENTER HORIZON   ESC EXIT'
    rtext(t, 160 + hplib.width(t) // 2, 205, GR)
    t = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'
    rtext(t, 160 + hplib.width(t) // 2, 225)
    return sel


if not hplib.busy:
    hplib.run(0)
