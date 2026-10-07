#!/usr/bin/env python3
"""test_local_labels.py - the one-program builds with local labels (tools/local_labels.py): build/NAVFULL.txt
against build/dev/src/NAVFULL.txt (the same code before the conversion: global names, R00-R98 saved in LocR),
build/MOON47.txt against build_moon47.release() (before the conversion).

  C47 simulator (python/c47sim.py)   every page (1 ALMANAC, SPLIT, SKY, ANIM, ALLSKY, INFO), every frame the same,
        with the FULL and the FAST series and with the tables; after NAV R00-R99 are 0 (CLREGS) and the stack clear
  C47 firmware (tests/test_fw.run)   each page key, + menu, 0 end: no error, X = 0, R00-R99 all 0
  listing                            one program, NAV the only global label, every jump has its label
  twice                              NAV run again after it ended: the same pages (its numbers are stored again at
                                     the start), DATE UTC LAT LON and the matrices kept
  MOON47                             the pages pixel for pixel, R00-R99 0 after; the firmware with and without TZ

  python3 tests/test_local_labels.py [NAV MOON]
"""
import os, re, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tests')]
import test_v2 as V                                                   # noqa: E402
import test_fw as F                                                   # noqa: E402

CASES = [('FULL', False, ('2026.1004', '9.30', '25.20', '55.12')), ('FAST', False, ('2027.0315', '3.30', '-33.54', '18.25')),
         ('FULL', True, ('2026.1020', '22.10', '60.10', '-5.00'))]


def listing(L):
    bad = []
    if L.count('END') != 1 or L[-1] != 'END':
        bad.append('not one program')
    g = [l for l in L if l.startswith('LBL "')]
    if g != ['LBL "NAV"']:
        bad.append('global labels %s' % g[:5])
    labs = {l[4:] for l in L if l.startswith('LBL ')}
    for l in L:
        m = re.fullmatch(r'(?:XEQ|GTO) (:.+:|\d\d|[A-La-l])', l)
        if m and m.group(1) not in labs:
            bad.append('no label for ' + l)
    return bad


def sim(L, ref):
    bad = 0
    for init, tables, (dt, ut, la, lo) in CASES:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        for name, (k, _) in V.PAGES.items():
            keys = [V.K[k], V.K['+'], V.K[0]]
            a, _, clear = V.session(L, keys, init, tables, inp, marks=False)
            b, _, _ = V.session(ref, keys, init, tables, inp, marks=False)
            c = V.T.load(L, init, tables)
            for kk, v in inp:
                c.reg[kk] = D(v)
            for r in range(100):
                c.rset('%02d' % r, D(7000 + r))
            c.flags.add(81); c.keys = list(keys); c.frames = []; c.pix = []
            c.run('NAV', maxsteps=10 ** 8)
            zero = all(c.rget('%02d' % r) == 0 for r in range(100))
            same = len(a) > 1 and a == b
            ok = same and clear and zero
            bad += not ok
            print('  %-4s%-2s %s %5s %6s %6s  %-7s frames %s (%d), R00-R99 %s, stack %s' % (
                init, 'T' if tables else '', dt, ut, la, lo, name, 'the same' if same else 'DIFFERENT', len(a),
                '0' if zero else 'NOT 0', 'clear' if clear else 'NOT CLEAR'))
    return bad


def twice(L, ref):
    """NAV, then NAV again in the same calculator: CLREGS cleared R00-R99, the second run must give the same pages
    (NAV stores its numbers again at the start); DATE UTC LAT LON kept, and the same variables as NAV before the
    conversion (ref) leaves (its own work matrices included)."""
    bad = 0
    for name in ('ALMANAC', 'ANIM', 'ALLSKY'):
        keys = [V.K[V.PAGES[name][0]], V.K['+'], V.K[0]]
        after = []
        for prog, n in ((L, 2), (ref, 1)):
            c = V.T.load(prog, 'FULL', False)
            for k, v in V.INPUTS:
                c.reg[k] = D(v)
            runs = []
            for _ in range(n):
                c.flags.add(81); c.s = [D(0)] * 4; c.keys = list(keys); c.frames = []; c.pix = []
                c.run('NAV', maxsteps=10 ** 8)
                runs.append([frozenset(f) for f in c.frames])
            after.append((runs, all(c.reg.get(k) == D(v) for k, v in V.INPUTS), sorted(c.mats)))
        (runs, inputs, mats), (_, _, refmats) = after
        ok = len(runs[0]) > 1 and runs[0] == runs[1] and inputs and mats == refmats
        bad += not ok
        print('  %-7s second run %s, DATE UTC LAT LON %s, matrices %s' % (
            name, 'the same pages' if runs[0] == runs[1] else 'DIFFERENT', 'kept' if inputs else 'CHANGED',
            'as before the conversion (%d)' % len(mats) if mats == refmats else 'DIFFERENT'))
    return bad


def firmware(path):
    if not os.path.exists(F.SIM):
        print('  no C47 simulator (%s): skipped' % F.SIM)
        return 0
    bad = 0
    inputs = ['2026.1004', 'STO "DATE"', '9.30', 'STO "UTC"', '25.20', 'STO "LAT"', '55.12', 'STO "LON"']
    B = os.path.join(ROOT, 'build')
    for k, name in ((72, '1 ALMANAC'), (73, '2 SPLIT'), (74, '3 SKY'), (62, '4 ANIM'), (63, '5 ALLSKY'), (64, '6 INFO'), (54, '9 SNAP')):
        vals, changed, err = F.run([os.path.join(B, 'NAVINIT_FAST.txt'), path], 'NAV', [k, 85, 82], inputs, resume=4)
        regs = {r: vals.get('R%02d' % r) for r in range(100)}
        zero = all(v == '0' for v in regs.values())
        ok = not err and vals.get('X') == '0' and zero
        bad += not ok
        print('  %-10s X=%s  R00-R99 %s  %s' % (name, vals.get('X'), 'all 0' if zero else 'NOT 0 %s' % [r for r, v in regs.items() if v != '0'][:6],
                                              err[:2] or 'no error'))
    return bad


def moon():
    """build/MOON47.txt against build_moon47.release() (before the conversion) pixel for pixel, R00-R99 0 at the
    end; the firmware without TZ and with TZ = -5."""
    import tempfile
    import test_moon47_c47 as MC
    import moon47 as M47
    import build_moon47
    path = os.path.join(ROOT, 'build', 'MOON47.txt')
    refp = os.path.join(tempfile.mkdtemp(), 'MOON47_REF.txt')
    open(refp, 'w', encoding='utf-8').write('\n'.join(build_moon47.release()[0]) + '\n')
    L = V.lines(path)
    b = [x for x in listing(L) if 'global labels' not in x]
    g = [l for l in L if l.startswith('LBL "')]
    b += [] if g == ['LBL "MOON47"'] else ['global labels %s' % g]
    print('== MOON47: the listing\n  ' + ('; '.join(b) if b else 'one program, MOON47 the only global label, every jump has its label'))
    bad = len(b)
    print('== MOON47 in the C47 simulator (python) against MOON47 before the conversion')
    for j, tz in [(M47.julian(2026, 10, 3, 12.0), None), (M47.julian(2027, 1, 22, 3.5), -5.0), (M47.julian(2029, 3, 1, 1.0), -9.5)]:
        MC.PROG = refp
        ref, _ = MC.run(j, tz)
        MC.PROG = path
        frames, c = MC.run(j, tz)
        same = len(frames) == 2 and frames == ref
        zero = all(c.rget('%02d' % r) == 0 for r in range(100))
        bad += not (same and zero)
        print('  JD %.2f tz %-5s pages %s, R00-R99 %s' % (j, tz, 'the same' if same else 'DIFFERENT', '0' if zero else 'NOT 0'))
    if os.path.exists(F.SIM):
        print('== MOON47 in the C47 firmware')
        for tz, setup in (('none', []), ('-5', ['-5', 'STO "TZ"'])):
            vals, changed, err = F.run([path], 'MOON47', [43, 82], setup, init=False, show=('TZ',))
            zero = all(vals.get('R%02d' % r) == '0' for r in range(100))
            ok = not err and vals.get('TZ') == ('0' if tz == 'none' else '-5') and zero
            bad += not ok
            print('  TZ before %-4s -> TZ %s, R00-R99 %s  %s' % (tz, vals.get('TZ'), 'all 0' if zero else 'NOT 0', err[:2] or 'no error'))
    return bad


def main(which):
    bad = 0
    if 'NAV' in which:
        path = os.path.join(ROOT, 'build', 'NAVFULL.txt')
        L = V.lines(path)
        print('== NAVFULL: the listing')
        b = listing(L)
        print('  ' + ('; '.join(b) if b else 'one program, NAV the only global label, every jump has its label'))
        bad += len(b)
        print('== NAVFULL against build/dev/src/NAVFULL.txt in the C47 simulator (python)')
        bad += sim(L, V.lines(os.path.join(ROOT, 'build', 'dev', 'src', 'NAVFULL.txt')))
        print('== NAVFULL twice in a row (python)')
        bad += twice(L, V.lines(os.path.join(ROOT, 'build', 'dev', 'src', 'NAVFULL.txt')))
        print('== NAVFULL in the C47 firmware (headless PC simulator)')
        bad += firmware(path)
    if 'MOON' in which:
        bad += moon()
    print('%d failed' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or ['NAV', 'MOON']) else 0)
