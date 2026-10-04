#!/usr/bin/env python3
"""test_navhopt.py - DEV: NAVFULL_HOPT and MOONFAST_HOPT (tools/build_navhopt.py: the counted loops on ISG)
against NAVFULL_OPT and MOON47_OPT (tools/build_navopt.py), both built now.

  C47 (python/c47sim.py)   every view (ALMF HALMV HORZ HALMH HANIM ALLSKY) pixel for pixel, with the FULL and
                           the FAST series and with the tables (TBL_4M); the NAV menu (frames, stack at the end);
                           MOON47 north and south; steps run.
  MOONFAST_R31 / _LOCR (R31: registers renumbered into R00-R30, saved and restored; LOCR: no global
                           register, all local): the page against HOPT, every register R00-R99 as before.
  NAVFULL_RSAVE / _LOCR (registers renumbered R00-R45, saved and restored / values in local registers per
                           level, R00-R32 saved and restored): every view against HOPT (FULL, FAST, tables), the
                           NAV menu with R00-R99 set to marks: the same frames, every register as before.
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


def moon_regs(hopt, n):
    """MOONFAST_R31 / _LOCR in the simulator against MOONFAST_HOPT: the frames, and R00-R99 (set to marks
    before) the same after the run; the stack clear; LocR calls."""
    import test_moon47_c47 as T47, moon47 as M47, c47sim, t21sim
    bad = 0
    print('\n== MOONFAST_R31 / _LOCR (C47 simulator): the page against HOPT, the registers kept')
    t = tempfile.mkdtemp()
    progs = {'HOPT': hopt}
    for name, local in (('R31', False), ('LOCR', True)):
        progs[name], k, nloc = H.moon_regs(local)
        print('  %-5s %s, local registers %d in %d routines'
              % (name, 'globals R00-R%02d, saved and restored' % (k - 1) if k else 'no global register',
                 sum(nloc.values()), len(nloc)))
    rnd = random.Random(472); steps = collections.Counter(); locr = collections.Counter()
    for _ in range(n):
        j = M47.julian(rnd.randint(2000, 2050), rnd.randint(1, 12), rnd.randint(1, 28), rnd.uniform(0, 24))
        res = {}
        for tag, L in progs.items():
            path = os.path.join(t, tag + '.txt'); open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
            files = []
            for i, pr in enumerate(t21sim._split(path)):
                f = os.path.join(t, '%s_%d.txt' % (tag, i)); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
            c = c47sim.load(files); c.clock = j
            marks = {'%02d' % r: D(1000 + r) + D('0.125') for r in range(100)}
            for r, v in marks.items():
                c.rset(r, v)
            c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = [43, 82]
            c.count = lambda op, x: locr.update([tag]) if op == 'LocR' else None
            c.run('MOON47', maxsteps=10 ** 8)
            res[tag] = [{(x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400} for f in c.frames]
            steps[tag] += c.steps
            if tag != 'HOPT':
                changed = [r for r in marks if c.rget(r) != marks[r]]
                clear = all(x == 0 for x in c.s)
                bad += bool(changed) or not clear
                if changed or not clear:
                    print('  %s: registers changed %s, stack %s' % (tag, changed, 'clear' if clear else c.s))
        for tag in ('R31', 'LOCR'):
            diff = [len(a ^ b) for a, b in zip(res['HOPT'], res[tag])]
            same = not any(diff) and len(res['HOPT']) == len(res[tag])
            bad += not same
            print('  JD %.4f %-4s diff %s  %s' % (j, tag, diff, 'OK, registers R00-R99 kept' if same else 'DIFFERENT'))
    for tag in ('R31', 'LOCR'):
        a, b = steps['HOPT'], steps[tag]
        print('  steps run %-4s %d -> %d (%+.1f %%); LocR run %d times' % (tag, a, b, 100.0 * (b - a) / a, locr[tag]))
    return bad


def nav_regs(hopt, n):
    """NAVFULL_RSAVE and NAVFULL_LOCR against HOPT: the views pixel for pixel (steps, LocR run), and NAV
    (1 ALMANAC, + menu, 0 end) with every register R00-R99 set to a mark before: the same frames, every
    register as before, the stack clear."""
    import datetime
    bad = 0
    var = {'RSAVE': H.c47_rsave()[0], 'LOCR': H.c47_locr()[0]}
    print('\n== NAVFULL_RSAVE / _LOCR (C47 simulator) against HOPT')
    for tag, L in var.items():
        diff, steps, locr = 0, [0, 0], 0
        for init, tables in (('FULL', False), ('FAST', False), ('FULL', True)):
            o, p = T.load(hopt, init, tables), T.load(L, init, tables)
            cnt = collections.Counter()
            p.count = lambda op, x: cnt.update(['LocR']) if op == 'LocR' else None
            rnd = random.Random(12)
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
                    if not (a[0] == b[0] and a[1] == b[1]):
                        diff += 1
                        print('  %s DIFFERENT %s %s %s %.2f %.2f: %d pixels' % (tag, init, tables, d0, la, lo, len(a[0] ^ b[0])))
                    steps[0] += a[3]; steps[1] += b[3]
            locr += cnt['LocR']
        out = []
        for LL in (hopt, L):
            c = T.load(LL)
            for k, v in (('DATE', '2026.1004'), ('UTC', '9.30'), ('LAT', '25.20'), ('LON', '55.12')):
                c.reg[k] = D(v)
            marks = {'%02d' % r: D(2000 + r) + D('0.25') for r in range(100)}
            for r, v in marks.items():
                c.rset(r, v)
            c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = [72, 85, 82]
            c.run('NAV', maxsteps=10 ** 8)
            out.append(([frozenset(f) for f in c.frames], [r for r in marks if c.rget(r) != marks[r]], all(x == 0 for x in c.s)))
        same, changed, clear = out[0][0] == out[1][0], out[1][1], out[1][2]
        bad += diff + (not same) + bool(changed) + (not clear)
        print('  %-5s views: %d screens, %d different; steps %+.1f %%; LocR run %d (%.0f per view)'
              % (tag, 3 * n * len(T.VIEWS), diff, 100.0 * (steps[1] - steps[0]) / steps[0], locr, locr / (3.0 * n * len(T.VIEWS))))
        print('  %-5s NAV menu: frames %s; registers R00-R99 %s; stack %s' % (tag, 'the same' if same else 'DIFFERENT',
              'all as before' if not changed else 'CHANGED %s' % changed, 'clear' if clear else 'NOT CLEAR'))
    return bad


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
    bad += moon_regs(mh, n)
    bad += nav_regs(hopt, n)
    if '--f42' in sys.argv:
        bad += free42(max(2, n // 2))
    print('\n%d differences' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
