"""check.py - the text drawn by almview / skyview (HP Prime) against nav.py's text
page and against the C47 ALMANAC screen (docs/ALMF_preview.png: 23 Sep 2026 23:30 UT,
10 N 075 30 W). Screen lines are rebuilt from the TEXTOUT_P calls (same y, by x).
Run: python3 python/hpprime/pc_shim/check.py
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [here, os.path.dirname(here), os.path.dirname(os.path.dirname(here))]
import hpprime    # noqa: E402
import hplib      # noqa: E402
import nav        # noqa: E402

hplib.busy = 1                                     # import the views without running them
import almview    # noqa: E402
import skyview    # noqa: E402


def one(s):
    return ' '.join(s.split())


def screen():
    rows = {}
    for t, x, y, f in hpprime.log:
        rows.setdefault(y, []).append((x, t))
    return [one(' '.join(t for x, t in sorted(v))) for y, v in sorted(rows.items())]


C47 = ['23-09-2026 23:30 UT', 'DR N 10 00.0', 'W 75 30.0', 'ARIES 355 19.5',
       'SUN 174 26.9 S 0 22.8 -8 52.7 271.2',
       '37 ARCTURUS 141 06.4 N 19 02.7 26 10.6 286.4',
       '49 VEGA 75 51.7 N 38 48.8 61 11.1 359.4',
       '51 ALTAIR 57 17.9 N 8 56.5 72 01.1 091.8',
       '42 ANTARES 107 33.7 S 26 29.5 42 01.7 219.8',
       '56 FOMALHAUT 10 32.1 S 29 28.7 16 06.1 124.8',
       '53 DENEB 44 44.1 N 45 22.8 45 53.3 031.1',
       'NAUT TWI 10:06 23:43', 'RISE/SET 10:51 22:57', 'MER PASS 16:54 SD 15.9',
       'MOON 92% WAXING', 'AGE 12.8 DAYS']

bad = 0
for case in ((2026, 9, 23, 23.5, 10.0, -75.5), (2026, 9, 26, 14 + 57 / 60.0, 25 + 20 / 60.0, 55.2),
             (2026, 9, 23, 3.0, 30.0, 0.0)):
    j = nav.jd(*case[:4])
    la, lo = case[4], case[5]
    hpprime.log[:] = []
    almview.draw(j, la, lo, 0)
    scr = screen()
    shown = ' | '.join(scr)
    page = nav.page(j, la, lo)
    for line in page[1:]:                          # header, Aries, bodies, footer
        if one(line) not in scr:
            if not all(p in shown for p in line.split('  ') if p.strip()):
                bad += 1
                print('page line not on screen:', line)
    for w in nav.almanac(j, la, lo)[0][:4]:        # date, UT, lat, lon of the head line
        if one(w) not in shown:
            bad += 1
            print('head not on screen:', w)
    if case[3] == 23.5:
        for w in C47:
            if w not in shown:
                bad += 1
                print('C47 value not on screen:', w)
    # horizon view: each body above the horizon, selected in turn, has its name on the
    # chart; the header and DAY / TWILIGHT / NIGHT
    rows, s = nav.bodies(j, la, lo)
    up = [r for r in rows if r[3] > 0]
    for i, r in enumerate(up):
        hpprime.log[:] = []
        skyview.draw(j, la, lo, i)
        drawn = [one(t) for t, x, y, f in hpprime.log]
        want = 'SUN' if r[0] == 0 else nav.SN[r[0] - 1].upper()
        if want not in drawn or nav.daylight(rows[0][3]) not in drawn or not drawn[0].startswith(nav.fdate(j)):
            bad += 1
            print('horizon view: missing', want, 'or header / daylight word', drawn[:3])
    print(case, 'page lines', len(page), 'bodies', len(rows), 'above the horizon', len(up), 'ok' if not bad else 'DIFFERENCES')
print('all identical' if not bad else '%d differences' % bad)
sys.exit(1 if bad else 0)
