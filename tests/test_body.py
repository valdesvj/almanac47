#!/usr/bin/env python3
"""BODY (one body): calculator program in the simulator vs native Python.
Compares the list pages, the legend, both result pages and the chart, pixel for pixel.
  python3 tests/test_body.py [cases] [seed] [T]"""
import os, random, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
from c47view import Engine, W, H
import c47screen as S, c47tables
from c47pc import jd

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    opt = sys.argv[3].upper() if len(sys.argv) > 3 else ''
    tables, fast = 'T' in opt, 'F' in opt
    if fast:
        import c47astro
        c47astro.use_series(os.path.join(ROOT, 'python', 'native', 'fast_series.json'))
    tb = c47tables.Tables(os.path.join(ROOT, 'programs', 'TBL.txt')) if tables else None
    E = Engine(os.path.join(ROOT, 'programs'), tables=tables, fast=fast); c = E.c
    bad = 0
    for k in range(n):
        if tables:
            d = datetime.date(2026, 9, 26) + datetime.timedelta(days=random.randint(0, 127)); y, m, dd = d.year, d.month, d.day
        else:
            y, m, dd = random.randint(2025, 2032) if fast else random.randint(2025, 2050), random.randint(1, 12), random.randint(1, 28)
        j = jd(y, m, dd, random.uniform(0, 24)); la = random.uniform(-70, 70); lo = random.uniform(-180, 180)
        al = S.Almanac(j, la, lo, tb)
        codes, pages = S.body_list(al)
        code = random.choice([60, 61, 62, 63, 64, 65, random.randint(1, 58)])
        E._start(j, la, lo); c.answers = [None] * len(pages) + [code, None, None]
        c.maxprompts = len(c.answers) + 1; c.frames = []
        try:
            c.run('BODY', maxsteps=10 ** 8)
        except StopIteration:
            pass
        got = [str(x) for x in c.msgs][:len(pages) + 4]
        want = pages + [S.body_legend()] + S.body_pages(al, code) + [S.body_legend()]
        frame = {(x, H - 1 - yy) for yy, x in c.frames[0] if 0 <= x < W and 0 <= yy < H} if c.frames else None
        ok = got == want and frame == S.body_chart(al, code)[0]
        if not ok:
            bad += 1
            print('DIFF', (y, m, dd, round(la, 3), round(lo, 3)), code)
            for a, b in zip(got, want):
                if a != b: print('  C47', repr(a)); print('  PY ', repr(b))
            if frame != S.body_chart(al, code)[0]: print('  chart differs')
    print('%d cases%s, %d differences' % (n, ' with tables' if tables else '', bad))
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
