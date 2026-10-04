#!/usr/bin/env python3
"""test_navhopt.py - DEV: NAVFULL_HOPT and MOONFAST_HOPT (tools/build_navhopt.py: the counted loops on ISG)
against NAVFULL_OPT and MOON47_OPT (tools/build_navopt.py), both built now.

  C47 (python/c47sim.py)   every view (ALMF HALMV HORZ HALMH HANIM ALLSKY) pixel for pixel, with the FULL and
                           the FAST series and with the tables (TBL_4M); the NAV menu (frames, stack at the end);
                           MOON47 north and south; steps run.
  Free42 (tools/f42/f42run, --f42)  the views through the NAV menu and MOON47, pixel for pixel.
  Statistics: program steps, bytes (.p47 / .raw), registers and variables, steps run.

  python3 tests/test_navhopt.py [N] [--f42]
"""
import collections, os, random, sys, tempfile
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tools', 'generators'),
                os.path.join(ROOT, 'tests')]
import test_navopt as T                                             # noqa: E402
import build_navopt as N                                            # noqa: E402
import build_navhopt as H                                           # noqa: E402

LOOPS = ('ISG', 'DSE')


def views(opt, hopt, n):
    """(rows, differences): every view, OPT against HOPT, for n random dates and places per series."""
    rows, bad = [], 0
    import datetime
    for init, tables in (('FULL', False), ('FAST', False), ('FULL', True)):
        o, p = T.load(opt, init, tables), T.load(hopt, init, tables)
        rnd = random.Random(11)
        for k in range(n):
            if tables:
                d0 = datetime.date(2026, 9, 27) + datetime.timedelta(days=rnd.randint(0, 120))
            elif init == 'FAST':
                d0 = datetime.date(2026, 1, 1) + datetime.timedelta(days=rnd.randint(0, 700))
            else:
                d0 = datetime.date(rnd.randint(2000, 2050), 1, 1) + datetime.timedelta(days=rnd.randint(0, 364))
            j = (d0 - datetime.date(2000, 1, 1)).days + 2451544.5 + rnd.randint(0, 95) / 96
            la, lo = round(rnd.uniform(-72, 72), 2), round(rnd.uniform(-180, 180), 2)
            for v in T.VIEWS:
                a, b = T.view(o, v, j, la, lo), T.view(p, v, j, la, lo)
                same = a[0] == b[0] and a[1] == b[1]
                bad += not same
                rows.append((v, a[3], b[3]))
                if not same:
                    print('DIFFERENT %s %s %s %.2f %.2f %s: %d pixels' % (init, tables, d0, la, lo, v, len(a[0] ^ b[0])))
    return rows, bad


def nav_menu(opt, hopt):
    """NAV: 1 ALMANAC, + menu, 0 end - the same frames, the stack clear at the end."""
    out = []
    for L in (opt, hopt):
        c = T.load(L)
        for k, v in (('DATE', '2026.1004'), ('UTC', '9.30'), ('LAT', '25.20'), ('LON', '55.12')):
            c.reg[k] = D(v)
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = [72, 85, 82]
        c.run('NAV', maxsteps=10 ** 8)
        out.append(([frozenset(f) for f in c.frames], all(x == 0 for x in c.s), c.steps))
    ok = out[0][0] == out[1][0] and out[1][1]
    print('\n== NAV menu (C47 simulator): %d frames, %s; stack after NAV %s; steps %d -> %d'
          % (len(out[1][0]), 'the same' if out[0][0] == out[1][0] else 'DIFFERENT', 'clear' if out[1][1] else 'NOT CLEAR',
             out[0][2], out[1][2]))
    return not ok


def moon(opt, hopt, n):
    """MOON47 north and south in the simulator: frames, stack at the end, steps run."""
    import test_moon47_c47 as T47, moon47 as M47
    t = tempfile.mkdtemp(); paths = {}
    for tag, L in (('opt', opt), ('hopt', hopt)):
        paths[tag] = os.path.join(t, 'MOON47_%s.txt' % tag)
        open(paths[tag], 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    rnd = random.Random(471); bad = 0; steps = [0, 0]
    print('\n== MOON47 (C47 simulator): the page and the view from the south, pixel for pixel')
    for k in range(n):
        j = M47.julian(rnd.randint(2000, 2050), rnd.randint(1, 12), rnd.randint(1, 28), rnd.uniform(0, 24))
        res = []
        for i, tag in enumerate(('opt', 'hopt')):
            T47.PROG = paths[tag]
            frames, c = T47.run(j)
            res.append(frames); steps[i] += c.steps
            if tag == 'hopt' and not all(x == 0 for x in c.s):
                print('  MOONFAST_HOPT: stack not clear at the end: %s' % c.s); bad += 1
        diff = [len(a ^ b) for a, b in zip(*res)]
        bad += any(diff) or len(res[0]) != len(res[1])
        print('  JD %.4f  diff %s  %s' % (j, diff, 'OK' if not any(diff) and len(res[0]) == len(res[1]) else 'DIFFERENT'))
    return bad, steps, paths


def count(L):
    return sum(1 for l in L if not l.startswith('LBL ') and l != 'END')


def stats(opt, hopt, mo, mh, rows, msteps, mpaths):
    print('\n== Statistics, OPT -> HOPT')
    t = tempfile.mkdtemp()
    for name, a, b in (('NAVFULL', opt, hopt), ('MOON47', mo, mh)):
        ra, va = T.regs(a); rb, vb = T.regs(b)
        loops = [sum(1 for l in L if l.split(' ')[0] in LOOPS) for L in (a, b)]
        pa, pb = os.path.join(t, name + '_a.txt'), os.path.join(t, name + '_b.txt')
        for p, L in ((pa, a), (pb, b)):
            open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        ba, bb = N.p47(pa), N.p47(pb)
        print('%-8s program steps %5d -> %5d (%+d); ISG/DSE %d -> %d; registers %d -> %d; variables %d -> %d%s'
              % (name, count(a), count(b), count(b) - count(a), loops[0], loops[1], len(ra), len(rb), len(va), len(vb),
                 '; .p47 %d -> %d bytes (%+d)' % (ba, bb, bb - ba) if ba else ''))
    agg = collections.defaultdict(lambda: [0, 0])
    for v, a, b in rows:
        agg[v][0] += a; agg[v][1] += b
    print('  steps run      OPT      HOPT')
    for v in T.VIEWS:
        a, b = agg[v]
        print('  %-7s %9d %9d  %+5.1f %%' % (v, a, b, 100.0 * (b - a) / a))
    a, b = sum(x[0] for x in agg.values()), sum(x[1] for x in agg.values())
    print('  %-7s %9d %9d  %+5.1f %%' % ('views', a, b, 100.0 * (b - a) / a))
    print('  %-7s %9d %9d  %+5.1f %%' % ('MOON47', msteps[0], msteps[1], 100.0 * (msteps[1] - msteps[0]) / msteps[0]))


def free42(n):
    """Free42: NAV views 1 2 4 6 (dev menu) and MOON47 north / south, OPT against HOPT, pixel for pixel."""
    if not os.path.exists(T.F42):
        print('\n== Free42: no tools/f42/f42run (sh tools/f42/setup.sh)')
        return 0
    import datetime
    import test_moon47_f42 as F47
    (fo, _), (fh, _) = N.free42(True), H.free42()
    rnd = random.Random(43); bad = 0
    print('\n== Free42 (f42run): NAV views, OPT against HOPT, pixel for pixel')
    for k in range(n):
        d0 = datetime.date(2026, 1, 1) + datetime.timedelta(days=rnd.randint(0, 9000))
        date, utc = '%04d.%02d%02d' % (d0.year, d0.month, d0.day), '%02d.%02d' % (rnd.randint(0, 23), rnd.randint(0, 59))
        lat, lon = '%.2f' % rnd.uniform(-65, 65), '%.2f' % rnd.uniform(-179, 179)
        a, b = T.f42_views(fo, date, utc, lat, lon, T.KEY_DEV), T.f42_views(fh, date, utc, lat, lon, T.KEY_DEV)
        diff = {v: len(a[v] ^ b[v]) for v in T.KEY}
        clear = b['stack'] == ['0.0000'] * 4
        bad += any(diff.values()) or not clear
        print('  %s %s %6s %7s  %s  %s; stack after NAV %s' % (date, utc, lat, lon, diff,
              'OK' if not any(diff.values()) else 'DIFFERENT', 'clear' if clear else b['stack']))
    t = tempfile.mkdtemp()
    _, f42o = __import__('moon47_opt').build(__import__('build_moon47'))
    _, f42h = H.moon47()
    print('== Free42 MOON47, OPT against HOPT, pixel for pixel (north, south)')
    for y, m, d, hh, mi, fmt, tz in ((2026, 10, 4, 12, 0, 'YMD', None), (2027, 1, 21, 22, 30, 'MDY', -5),
                                     (2049, 3, 16, 21, 51, 'DMY', 5.5)):
        res = []
        for tag, L in (('o', f42o), ('h', f42h)):
            F47.PROG = os.path.join(t, tag + '.txt')
            open(F47.PROG, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
            res.append(F47.frames(y, m, d, hh, mi, fmt, tz)[0])
        diff = [len(a ^ b) for a, b in zip(*res)]
        bad += any(diff)
        print('  %04d-%02d-%02d %02d:%02d %s tz %-4s diff %s %s' % (y, m, d, hh, mi, fmt, tz, diff, 'OK' if not any(diff) else 'DIFFERENT'))
    return bad


def main():
    n = int(next((a for a in sys.argv[1:] if a.isdigit()), '4'))
    opt, hopt = N.c47(True)[0], H.c47()[0]
    rows, bad = views(opt, hopt, n)
    print('== Views, C47 simulator: %d screens, %d different' % (len(rows), bad))
    bad += nav_menu(opt, hopt)
    import build_moon47 as M, moon47_opt
    mo = moon47_opt.build(M)[0]
    mh = H.moon47()[0]
    mbad, msteps, mpaths = moon(mo, mh, n)
    bad += mbad
    stats(opt, hopt, mo, mh, rows, msteps, mpaths)
    if '--f42' in sys.argv:
        bad += free42(max(2, n // 2))
    print('\n%d differences' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
