"""check.py - the strings drawn by almview / skyview against nav.py's text page and
against the C47 ALMANAC screen (docs/ALMF_preview.png: 23 Sep 2026 23:30 UT,
10 N 075 30 W). Run: python3 python/numworks/pc_shim/check.py
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [here, os.path.dirname(here), os.path.dirname(os.path.dirname(here))]
import kandinsky  # noqa: E402
import nwlib      # noqa: E402
import nav        # noqa: E402

nwlib.busy = 1                                     # import the views without running them
import almview    # noqa: E402
import skyview    # noqa: E402

drawn = []
_text = nwlib.text


def text(s, x, y, c=nwlib.BK):
    drawn.append(s.strip())
    return _text(s, x, y, c)


almview.text = skyview.text = text

# values read off the C47 screen (Sun, Aries and the six stars it shows)
C47 = ['23-09-2026 23:30 UT', 'N 10 00.0', 'W 75 30.0', '355 19.5',
       '174 26.9', 'S  0 22.8', '-8 52.7', '271.2',
       '141 06.4', 'N 19 02.7', '26 10.6', '286.4',
       '75 51.7', 'N 38 48.8', '61 11.1', '359.4',
       '57 17.9', 'N  8 56.5', '72 01.1', '091.8',
       '107 33.7', 'S 26 29.5', '42 01.7', '219.8',
       '10 32.1', 'S 29 28.7', '16 06.1', '124.8',
       '44 44.1', 'N 45 22.8', '45 53.3', '031.1',
       'NAUT TWI 10:06 23:43', 'RISE/SET 10:51 22:57', 'MER PASS 16:54  SD 15.9',
       'MOON 92% WAXING', 'AGE 12.8 DAYS']

bad = 0
for case in ((2026, 9, 23, 23.5, 10.0, -75.5), (2026, 9, 26, 14 + 57 / 60.0, 25 + 20 / 60.0, 55.2),
             (2026, 9, 23, 3.0, 30.0, 0.0)):
    j = nav.jd(*case[:4])
    la, lo = case[4], case[5]
    del drawn[:]
    kandinsky.log[:] = []
    almview.draw(j, la, lo, 0)
    shown = ' | '.join(drawn + [s for s, x, y in kandinsky.log])
    page = nav.page(j, la, lo)
    # every value of every text line of nav.py's page must be on the screen
    for line in page[2:]:
        for w in line.replace('%', ' ').split():
            if w not in shown:
                bad += 1
                print('missing on screen:', w, 'from', line)
    if case[3] == 23.5:
        for w in C47:
            if w not in shown:
                bad += 1
                print('C47 value not on screen:', w)
    # horizon view: the top line of each body = nav values
    rows, s = nav.bodies(j, la, lo, 10)
    for i, r in enumerate(rows):
        kandinsky.log[:] = []
        skyview.draw(j, la, lo, i)
        top = kandinsky.log[-1][0]
        want = ' ZN ' + nav.f1(r[4]) + '  HC ' + ('-' if r[3] < 0 else '') + nav.f1(r[3])
        if want not in top:
            bad += 1
            print('top line', top, 'expected', want)
    print(case, 'page lines', len(page), 'bodies', len(rows), 'ok' if not bad else 'DIFFERENCES')
print('all identical' if not bad else '%d differences' % bad)
sys.exit(1 if bad else 0)
