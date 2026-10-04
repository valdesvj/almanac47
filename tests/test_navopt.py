#!/usr/bin/env python3
"""test_navopt.py - DEV: NAVFULL_OPT (tools/build_navopt.py: Horner, n-vectors, HCZ by n-vectors) against
the release NAVFULL, both built now from programs/ in the same way.

  C47 (python/c47sim.py)  every routine of the engine (SUNA, SUNF, NUT through SUNA, STR2 for the 58
                          stars, MOON, MOOQ, PLAN 1-4, PLN3, PLNQ, PHAS, RISE ... TRAN, CHZ, DHA) at random
                          dates 2000-2050 and places: the largest difference; then every view (ALMF HALMV
                          ALMR HORZ HALMH HANIM ALLSKY) pixel for pixel, the TEXT page register by register,
                          with the FULL and the FAST series and with the tables (TBL_4M); steps and trig.
  Free42 (tools/f42/f42run, --f42)  the views through the NAV menu, pixel for pixel, and the routines.
  Statistics: program steps, bytes (.p47 / .raw), registers and variables, steps and trig run.

  python3 tests/test_navopt.py [N] [--f42] [--quick]
"""
import collections, datetime, math, os, random, re, subprocess, sys, tempfile
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tools', 'generators'),
                os.path.join(ROOT, 'tests')]
import c47sim                                                        # noqa: E402
import build_navopt as N                                             # noqa: E402

ENGINE = ('SUNA', 'STAR', 'MOON', 'PLAN', 'CHZ')
VIEWS = ('ALMF', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')     # TEXT (ALMR) is not in the dev menu
TRIG = {'SIN', 'COS', 'TAN', 'ASIN', 'ACOS', '→POL', '→REC'}
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')


def split(L):
    progs, cur = [], []
    for l in L:
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def load(L, init='FULL', tables=False):
    tmp = tempfile.mkdtemp(); files = []
    src = open(os.path.join(ROOT, 'build', 'NAVINIT_%s.txt' % init), encoding='utf-8').read().split('\n')
    tb = open(os.path.join(ROOT, 'build', 'dev', 'TBL_4M.txt'), encoding='utf-8').read().split('\n') if tables else []
    for i, pr in enumerate(split([l for l in src + L + tb if l.strip()])):
        f = os.path.join(tmp, 'p%d.txt' % i); open(f, 'w', encoding='utf-8').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82); c.grfnt = 21
    c.run('INIT', maxsteps=10 ** 7)
    if tables:
        c.run('TBL', maxsteps=10 ** 8)
    c.tally = collections.Counter()

    def count(op, x):
        if op in TRIG:
            c.tally['trig'] += len(x.flat()) if isinstance(x, c47sim.Mat) else 1
    c.count = count
    return c


def call(c, label, args=(), regs=None):
    for k, v in (regs or {}).items():
        c.rset(c.regkey(str(k)), D(repr(v)))
    c.s = [D(0)] * 4; c.lift = True
    for v in args:
        c.push(D(repr(v)))
    s0 = c.steps
    c.run(label, maxsteps=10 ** 7)
    c.tally[label] += c.steps - s0
    return [float(v) if not isinstance(v, (str, tuple, c47sim.Mat)) else v for v in c.s]


# what each output is (default: an angle in degrees, compared in arcmin)
UNIT = {'RISE': 'hours', 'SET': 'hours', 'NTWA': 'hours', 'NTWP': 'hours', 'TRAN': 'hours', 'PHAS': 'number', 'SQK': 'number',
        ('MOON', 2): 'number', ('MOON', 3): 'number', ('PLAN', 3): 'number', ('SUNA R73 R74 R76', 0): 'number'}


def adiff(a, b):
    """Difference in arcmin of two angles in degrees (mod 360)."""
    return abs((a - b + 180) % 360 - 180) * 60


def engine(n, seed=47):
    """Every routine of the engine, release against optimized: the largest difference per output."""
    full_o, full_n = REF[0], OPT[0]
    worst = collections.defaultdict(float)
    tallies = []
    for init in ('FULL', 'FAST'):
        o, p = load(full_o, init), load(full_n, init)
        rnd = random.Random(seed)
        period = (2000, 2050) if init == 'FULL' else (2026, 2027)
        for k in range(n):
            y = rnd.randint(*period); d0 = datetime.date(y, 1, 1) + datetime.timedelta(days=rnd.randint(0, 364))
            j = (d0 - datetime.date(2000, 1, 1)).days + 2451544.5 + rnd.random()
            la, lo = rnd.uniform(-70, 70), rnd.uniform(-180, 180)
            dec, gha, hc, zn = rnd.uniform(-89, 89), rnd.uniform(0, 360), rnd.uniform(-5, 85), rnd.uniform(0, 360)
            out = {}
            for c, tag in ((o, 'o'), (p, 'n')):
                r = {}
                c.rset('91', D(repr(la))); c.rset('92', D(repr(lo)))
                call(c, 'HCZI')
                r['SUNA'] = call(c, 'SUNA', [j])[:3]
                r['SUNA R73 R74 R76'] = [float(c.rget(x)) for x in ('73', '74', '76')]
                for s in range(1, 59):
                    r['STR2 %d' % s] = call(c, 'STR2', regs={82: s})[:3]
                r['SQK'] = [call(c, 'SQK', [s])[0] for s in (1, 20, 58)]
                r['MOOQ'] = call(c, 'MOOQ')[:2]
                for pl in range(1, 5):
                    call(c, 'SUNA', [j])
                    r['PLN3 %d' % pl] = call(c, 'PLN3', [pl])[:2]
                    r['PLNQ %d' % pl] = call(c, 'PLNQ', [pl])[:2]
                    r['PLAN %d' % pl] = call(c, 'PLAN', [j, pl])
                r['MOON'] = call(c, 'MOON', [j])
                r['PHAS'] = call(c, 'PHAS', [j])[:2]
                r['SUNF'] = call(c, 'SUNF', [j])[:2]
                noon = math.floor(j - 0.5) + 0.5
                for ev in ('RISE', 'SET', 'NTWA', 'NTWP', 'TRAN'):
                    r[ev] = call(c, ev, [noon, la, lo])[:1]
                r['CHZ'] = call(c, 'CHZ', [la, lo, dec, gha])[:2]
                r['HCZ0'] = call(c, 'HCZ0', [gha])[:2]
                r['DHA'] = call(c, 'DHA', [la, lo, hc, zn])[:3]
                out[tag] = r
            for key in out['o']:
                a, b = out['o'][key], out['n'][key]
                name = key.split(' ')[0] if key[:4] in ('STR2', 'PLN3', 'PLNQ', 'PLAN') else key
                for i, (x, z) in enumerate(zip(a, b)):
                    if isinstance(x, float):
                        u = UNIT.get((name, i), UNIT.get(name, 'angle'))
                        v = adiff(x, z) if u == 'angle' else abs(x - z) * (60 if u == 'hours' else 1)
                        worst['%s [%d]' % (name, i)] = max(worst['%s [%d]' % (name, i)], v)
        tallies.append((init, o.tally, p.tally))
    return worst, tallies


def view(c, name, j, la, lo):
    c.steps = 0; c.pix = []; c.frames = []; c.msgs = []; c.s = [D(0)] * 4; c.lift = True; c.keys = []
    c.tally['trig'] = 0
    for v in (j, la, lo):
        c.push(D(repr(v)))
    try:
        c.run(name, maxsteps=10 ** 7)
    except StopIteration:
        pass
    pix = frozenset((x, y) for y, x in c.pix)
    text = {k: v for k, v in c.reg.items() if isinstance(v, str)} if name == 'ALMR' else {}
    return pix, [frozenset(f) for f in c.frames], text, c.steps, c.tally['trig']


def views(n, seed=7):
    rows = []
    bad = 0
    for init, tables in (('FULL', False), ('FAST', False), ('FULL', True)):
        o, p = load(REF[0], init, tables), load(OPT[0], init, tables)
        rnd = random.Random(seed)
        for k in range(n):
            if tables:
                d0 = datetime.date(2026, 9, 27) + datetime.timedelta(days=rnd.randint(0, 120))
            elif init == 'FAST':
                d0 = datetime.date(2026, 1, 1) + datetime.timedelta(days=rnd.randint(0, 700))
            else:
                d0 = datetime.date(rnd.randint(2000, 2050), 1, 1) + datetime.timedelta(days=rnd.randint(0, 364))
            j = (d0 - datetime.date(2000, 1, 1)).days + 2451544.5 + rnd.randint(0, 95) / 96
            la, lo = round(rnd.uniform(-72, 72), 2), round(rnd.uniform(-180, 180), 2)
            for v in VIEWS:
                a, b = view(o, v, j, la, lo), view(p, v, j, la, lo)
                same = a[0] == b[0] and a[1] == b[1] and a[2] == b[2]
                bad += not same
                rows.append((init + (' T' if tables else ''), d0.isoformat(), la, lo, v, same, len(a[0] ^ b[0]), a[3], b[3], a[4], b[4]))
                if not same:
                    print('DIFFERENT %s %s %s %.2f %.2f %s: %d pixels' % (init, tables, d0, la, lo, v, len(a[0] ^ b[0])))
    return rows, bad


# ---------------------------------------------------------------- statistics of the programs
def programs(L):
    out, cur = {}, None
    for l in L:
        g = re.fullmatch(r'LBL "(.+)"', l)
        if g:
            cur = g.group(1)
        if cur:
            out.setdefault(cur, []).append(l)
    return out


def regs(L):
    """Numbered registers and named variables a listing uses (STO RCL INDEX ..., not labels)."""
    num, var = set(), set()
    for l in L:
        m = re.fullmatch(r'(?:STO|RCL|ISG|DSE|INPUT|VIEW|STO[+\-×÷]|RCL[+\-×÷]|INDEX|X<>|x<>|[A-Za-z→]+) (?:IND )?(\d\d)', l)
        if m and not l.startswith(('LBL', 'GTO', 'XEQ', 'FS', 'FC', 'SF', 'CF', 'PAUSE', 'KEY', 'GRMOD', 'AGRAPH', 'ATEXT', 'WSIZE', 'SIZE', 'TONE', 'FIX', 'SCI', 'ENG', 'PROMPT', 'AVIEW', 'αLENG', 'α→𝑥', 'αIP', 'x→α')):
            num.add(int(m.group(1)))
        elif re.fullmatch(r'(?:PAUSE|AGRAPH|ATEXT|PROMPT|AVIEW|αLENG|α→𝑥|αIP|x→α) (\d\d)', l):
            num.add(int(l.split()[-1]))
        m = re.fullmatch(r'(?:STO|RCL|INDEX|STO[+\-×÷]|RCL[+\-×÷]|INPUT) "(.+)"', l)
        if m:
            var.add(m.group(1))
    return num, var


def engine_part(L):
    """The engine routines of a NAVFULL listing: from LBL "SUNA" ... (programs SUNA STAR MOON PLAN CHZ)."""
    P = programs(L)
    names = {'SUNA': ['SUNA', 'SUNG', 'SUNF', 'SER', 'SERT', 'NUT'], 'STAR': ['STAR', 'STR2', 'SQK'],
             'MOON': ['MOON', 'MOO2', 'MOOQ'], 'PLAN': ['PLAN', 'PLN2', 'PLN3', 'PLNQ'],
             'CHZ': ['CHZ', 'HCZ', 'HCZ0', 'HCZQ', 'HCZR', 'HCZI', 'DHA']}
    return {n: [l for r in rs for l in P.get(r, [])] for n, rs in names.items()}


def stats():
    print('\n== Programs (C47 NAVFULL, steps = lines without LBL/END; bytes = the .p47 program)')
    eo, en = engine_part(REF[0]), engine_part(OPT[0])
    print('%-8s %7s %7s %6s   %-26s %-26s' % ('program', 'steps', 'opt', 'diff', 'registers', 'registers opt'))
    to = tn = 0
    for n in ENGINE:
        so = sum(1 for l in eo[n] if not l.startswith('LBL ') and l != 'END')
        sn = sum(1 for l in en[n] if not l.startswith('LBL ') and l != 'END')
        to += so; tn += sn
        ro, vo = regs(eo[n]); rn, vn = regs(en[n])
        print('%-8s %7d %7d %+6d   %3d R + %2d var             %3d R + %2d var' % (n, so, sn, sn - so, len(ro), len(vo), len(rn), len(vn)))
    print('%-8s %7d %7d %+6d' % ('engine', to, tn, tn - to))
    ro, vo = regs(sum(eo.values(), [])); rn, vn = regs(sum(en.values(), []))
    print('engine registers: %d -> %d   (gone: %s; new: %s)' % (len(ro), len(rn), ' '.join('R%02d' % r for r in sorted(ro - rn)) or '-',
                                                             ' '.join('R%02d' % r for r in sorted(rn - ro)) or '-'))
    print('engine variables: %d -> %d   (gone: %s; new: %s)' % (len(vo), len(vn), ' '.join(sorted(vo - vn)) or '-', ' '.join(sorted(vn - vo)) or '-'))
    ao, avo = regs(REF[0]); an, avn = regs(OPT[0])
    print('NAVFULL registers %d -> %d, variables %d -> %d (gone %s)' % (len(ao), len(an), len(avo), len(avn), ' '.join('R%02d' % r for r in sorted(ao - an)) or '-'))
    lo = sum(1 for l in REF[1] if l != 'END'); ln = sum(1 for l in OPT[1] if l != 'END')
    print('NAVFULL steps %d -> %d (%+d)' % (lo, ln, ln - lo))
    t = tempfile.mkdtemp()
    for tag, L in (('ref', REF[1]), ('opt', OPT[1])):
        open(os.path.join(t, tag + '.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    a, b = N.p47(os.path.join(t, 'ref.txt')), N.p47(os.path.join(t, 'opt.txt'))
    if a:
        print('NAVFULL bytes (.p47 program) %d -> %d (%+d)' % (a, b, b - a))
    return t


# ---------------------------------------------------------------- Free42 (tools/f42/f42run)
KEY = {1: 29, 2: 30, 5: 25, 7: 19}                    # release menu keys: ALMANAC CHART SPLIT ALLSKY
KEY_DEV = {1: 29, 2: 30, 5: 24, 7: 26}                # the same views in the dev menu: 1 2 4 6


def f42_views(nav, date, utc, lat, lon, keys=KEY):
    t = tempfile.mkdtemp()
    with open(os.path.join(t, 'nav.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(nav) + '\n')
    cmd = ['paste %s/build/free42/NAVINIT_FULL.txt' % ROOT, 'paste %s/nav.txt' % t, 'xeq INIT', 'xeq NAV',
           'num ' + date, 'num ' + utc, 'num ' + lat, 'num ' + lon]
    for v, k in keys.items():
        cmd += ['key %d' % k, 'shot %s/v%d.pbm' % (t, v), 'key 37']
    cmd += ['key 34', 'stack']                                      # 0: NAV ends
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=3600)
    out = {'stack': [l[3:] for l in r.stdout.split('\n') if re.fullmatch(r'[XYZT]: .*', l)]}
    for v in KEY:
        rows = open('%s/v%d.pbm' % (t, v)).read().split('\n')[2:242]
        out[v] = frozenset((x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == '1')
    return out


def f42_engine(named, calls):
    """Run each call (label, args) of the named Free42 listing; the stack X Y Z T in ALL display mode."""
    t = tempfile.mkdtemp()
    with open(os.path.join(t, 'nav.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(named) + '\n')
    helper = []
    for k, (lab, args, regs) in enumerate(calls):
        helper += ['LBL "T%d"' % k, 'SIZE 100', 'ALL', 'DEG'] + ['%s\nSTO %s' % (repr(v), r) for r, v in regs.items()] \
                  + [repr(a) for a in args] + ['XEQ "%s"' % lab, 'END']
    with open(os.path.join(t, 'h.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(helper) + '\n')
    cmd = ['paste %s/build/free42/NAVINIT_FULL.txt' % ROOT, 'paste %s/nav.txt' % t, 'paste %s/h.txt' % t, 'xeq INIT']
    for k in range(len(calls)):
        cmd += ['xeq T%d' % k, 'stack']
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=3600)
    vals, cur = [], []
    for l in r.stdout.split('\n'):
        m = re.fullmatch(r'([XYZT]): (.*)', l)
        if m:
            try:
                cur.append(float(m.group(2).replace(',', '').replace('ᴇ', 'e').replace('E', 'e')))
            except ValueError:
                cur.append(m.group(2))
            if m.group(1) == 'T':
                vals.append(cur); cur = []
    return vals


def free42(n, seed=42):
    if not os.path.exists(F42):
        print('\n== Free42: no tools/f42/f42run (sh tools/f42/setup.sh)')
        return 0
    ref, opt = N.free42(False), N.free42(True)
    rnd = random.Random(seed)
    bad = 0
    print('\n== Free42 (f42run, binary doubles): NAV menu views 1 2 5 7, pixel for pixel')
    for k in range(n):
        d0 = datetime.date(2026, 1, 1) + datetime.timedelta(days=rnd.randint(0, 9000))
        date, utc = '%04d.%02d%02d' % (d0.year, d0.month, d0.day), '%02d.%02d' % (rnd.randint(0, 23), rnd.randint(0, 59))
        lat, lon = '%.2f' % rnd.uniform(-65, 65), '%.2f' % rnd.uniform(-179, 179)
        a, b = f42_views(ref[0], date, utc, lat, lon), f42_views(opt[0], date, utc, lat, lon, KEY_DEV)
        diff = {v: len(a[v] ^ b[v]) for v in KEY}
        clear = b['stack'] == ['0.0000'] * 4
        bad += any(diff.values()) or not clear
        print('  %s %s %6s %7s  %s  %s; stack after NAV (dev) %s' % (date, utc, lat, lon, diff,
              'OK' if not any(diff.values()) else 'DIFFERENT', 'clear' if clear else b['stack']))
    calls = []
    for k in range(n):
        j = 2451545 + rnd.uniform(0, 18000); la, lo = rnd.uniform(-70, 70), rnd.uniform(-180, 180)
        calls += [('SUNA', [j], {}), ('MOON', [j], {}), ('SUNF', [j], {}), ('PHAS', [j], {})]
        calls += [('PLAN', [j, p], {}) for p in range(1, 5)] + [('STAR', [j, s], {}) for s in (1, 13, 37, 58)]
        calls += [('CHZ', [la, lo, rnd.uniform(-80, 80), rnd.uniform(0, 360)], {}), ('RISE', [math.floor(j - 0.5) + 0.5, la, lo], {}),
                  ('DHA', [la, lo, rnd.uniform(0, 80), rnd.uniform(0, 360)], {})]
    va, vb = f42_engine(ref[1], calls), f42_engine(opt[1], calls)
    worst = collections.defaultdict(float)
    nout = {'SUNA': 3, 'MOON': 4, 'PLAN': 4, 'STAR': 3, 'SUNF': 2, 'PHAS': 2, 'CHZ': 2, 'RISE': 1, 'DHA': 3}
    for (lab, args, _), x, y in zip(calls, va, vb):
        for i, (p, q) in enumerate(list(zip(x, y))[:nout[lab]]):
            if isinstance(p, float) and isinstance(q, float):
                u = UNIT.get((lab, i), UNIT.get(lab, 'angle'))
                v = adiff(p, q) if u == 'angle' else abs(p - q) * (60 if u == 'hours' else 1)
                worst['%s [%d]' % (lab, i)] = max(worst['%s [%d]' % (lab, i)], v)
    print('== Free42 routines (%d calls, ALL display: 12 digits): the largest difference (arcmin; RISE: minutes)' % len(calls))
    for k in sorted(worst):
        flag = worst[k] > 1e-6
        bad += flag
        print('  %-10s %.1e%s' % (k, worst[k], '  <--' if flag else ''))
    if len(va) != len(calls) or len(vb) != len(calls):
        print('  missing results: %d %d of %d' % (len(va), len(vb), len(calls))); bad += 1
    return bad


def moon47(n=4):
    """MOON47_OPT against MOON47: the page pixel for pixel in the simulator (north and south), steps run;
    program steps, bytes, registers."""
    import build_moon47 as M, moon47_opt, test_moon47_c47 as T47, moon47 as M47
    ref, opt = M.build()[0], moon47_opt.build(M)[0]
    t = tempfile.mkdtemp(); paths = {}
    for tag, L in (('ref', ref), ('opt', opt)):
        paths[tag] = os.path.join(t, 'MOON47_%s.txt' % tag)
        open(paths[tag], 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    rnd = random.Random(470); bad = 0; steps = [0, 0]; trig = [0, 0]
    print('\n== MOON47 (C47 simulator): the page and the view from the south, pixel for pixel')
    for k in range(n):
        j = M47.julian(rnd.randint(2000, 2050), rnd.randint(1, 12), rnd.randint(1, 28), rnd.uniform(0, 24))
        res = []
        for i, tag in enumerate(('ref', 'opt')):
            T47.PROG = paths[tag]
            frames, c = T47.run(j)
            res.append(frames); steps[i] += c.steps
            if tag == 'opt' and not all(x == 0 for x in c.s):
                print('  MOON47_OPT: stack not clear at the end: %s' % c.s); bad += 1
        diff = [len(a ^ b) for a, b in zip(*res)]
        bad += any(diff) or len(res[0]) != len(res[1])
        print('  JD %.4f  diff %s  %s' % (j, diff, 'OK' if not any(diff) else 'DIFFERENT'))
    lo = sum(1 for l in ref if not l.startswith('LBL ') and l != 'END'); ln = sum(1 for l in opt if not l.startswith('LBL ') and l != 'END')
    ro, vo = regs(ref); rn, vn = regs(opt)
    print('  program steps %d -> %d (%+d); registers %d -> %d; variables %d -> %d (%s, set to 0 at the end)'
          % (lo, ln, ln - lo, len(ro), len(rn), len(vo), len(vn), ' '.join(sorted(vn - vo))))
    print('  steps run for %d pages %d -> %d (%+.0f %%)' % (n, steps[0], steps[1], 100.0 * (steps[1] - steps[0]) / steps[0]))
    a, b = N.p47(paths['ref']), N.p47(paths['opt'])
    if a:
        print('  bytes (.p47 program) %d -> %d (%+d)' % (a, b, b - a))
    if os.path.exists(F42):
        fa = os.path.join(t, 'f_ref.txt'); fb = os.path.join(t, 'f_opt.txt')
        open(fa, 'w', encoding='utf-8').write('\n'.join(M.build_f42()) + '\n')
        open(fb, 'w', encoding='utf-8').write('\n'.join(moon47_opt.build(M)[1]) + '\n')
        print('  Free42 .raw %d -> %d bytes (%+d)' % (N.raw(fa), N.raw(fb), N.raw(fb) - N.raw(fa)))
    return bad


def nav_menu():
    """The dev NAV in the simulator: the menu without 3 TEXT, key 3 does nothing, 1 ALMANAC the same screen
    as the release, 0 ends; NAVINIT (dev) leaves only its message on the stack."""
    bad = 0
    shots = []
    for L, keys in ((REF[0], [72, 85, 82]), (OPT[0], [72, 85, 82])):   # 1 ALMANAC, + menu, 0 end
        c = load(L)
        for k, v in (('DATE', '2026.1004'), ('UTC', '9.30'), ('LAT', '25.20'), ('LON', '55.12')):
            c.reg[k] = D(v)
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []
        c.keys = keys
        c.run('NAV', maxsteps=10 ** 8)
        shots.append([frozenset(f) for f in c.frames])
        stack = [x for x in c.s]
    print('\n== NAV menu (C47 simulator): release %d frames, dev %d frames (menu, view, menu)' % (len(shots[0]), len(shots[1])))
    same_view = len(shots[1]) == len(shots[0]) and shots[1][1] == shots[0][1]
    print('  dev: menu 1-7 without TEXT; 1 ALMANAC the same screen as the release: %s'
          % ('OK' if same_view else 'DIFFERENT'))
    bad += not same_view
    clear = all(x == 0 for x in stack)
    bad += not clear
    print('  dev: stack after NAV (0 END) %s' % ('clear' if clear else stack))
    for kind in ('FULL', 'FAST'):
        L = [l for l in open(os.path.join(ROOT, 'build', 'dev', 'opt', 'NAVINIT_%s.txt' % kind), encoding='utf-8').read().split('\n') if l]
        t = tempfile.mkdtemp(); f = os.path.join(t, 'i.txt'); open(f, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        c = c47sim.load([f]); c.s = [D(7), D(8), D(9), D(10)]; c.run('INIT', maxsteps=10 ** 7)
        ok = isinstance(c.s[0], str) and c.s[0].startswith('MATRICES READY') and all(x == 0 for x in c.s[1:])
        bad += not ok
        print('  NAVINIT_%s (dev): stack after INIT %s  %s' % (kind, [str(x) for x in c.s], 'OK' if ok else 'NOT CLEAN'))
    return bad


def main():
    global REF, OPT
    n = int(next((a for a in sys.argv[1:] if a.isdigit()), '6'))
    REF, OPT = N.c47(False), N.c47(True)
    worst, tallies = engine(n)
    print('== Engine, C47 simulator, %d dates x FULL and FAST: the largest difference (angles: arcmin; times: minutes;\n   HP SD: arcmin; R73: au; PHAS: %% and days; SQK: sin)' % n)
    bad = 0
    for k in sorted(worst):
        flag = worst[k] > 1e-6
        bad += flag
        print('  %-14s %.1e%s' % (k, worst[k], '  <-- ' if flag else ''))
    print('\n  steps run (all dates)          release      opt')
    for init, a, b in tallies:
        for k in sorted(a):
            if k != 'trig' and a[k] > 0:
                print('  %-4s %-14s %12d %8d  %+5.0f %%' % (init, k, a[k], b[k], 100.0 * (b[k] - a[k]) / a[k]))
        print('  %-4s %-14s %12d %8d  %+5.0f %%' % (init, 'trig functions', a['trig'], b['trig'], 100.0 * (b['trig'] - a['trig']) / a['trig']))
    if '--quick' not in sys.argv:
        rows, vbad = views(max(2, n // 2))
        bad += vbad
        print('\n== Views, C47 simulator: %d screens, %d different' % (len(rows), vbad))
        agg = collections.defaultdict(lambda: [0, 0, 0, 0])
        for r in rows:
            g = agg[r[4]]; g[0] += r[7]; g[1] += r[8]; g[2] += r[9]; g[3] += r[10]
        print('  view       steps release      opt          trig release      opt')
        for v in VIEWS:
            g = agg[v]
            print('  %-7s %14d %8d %+4.0f %%  %12d %8d %+4.0f %%' % (v, g[0], g[1], 100.0 * (g[1] - g[0]) / g[0], g[2], g[3],
                                                             100.0 * (g[3] - g[2]) / max(g[2], 1)))
    bad += nav_menu()
    t = stats()
    if os.path.exists(F42):
        fr, fo = N.free42(False)[0], N.free42(True)[0]
        a, b = os.path.join(t, 'f_ref.txt'), os.path.join(t, 'f_opt.txt')
        open(a, 'w', encoding='utf-8').write('\n'.join(fr) + '\n'); open(b, 'w', encoding='utf-8').write('\n'.join(fo) + '\n')
        ra, rb = N.raw(a), N.raw(b)
        print('Free42 NAVFULL steps %d -> %d (%+d), .raw %d -> %d bytes (%+d)' % (len(fr), len(fo), len(fo) - len(fr), ra, rb, rb - ra))
    bad += moon47()
    if '--f42' in sys.argv:
        bad += free42(max(2, n // 2))
    print('\n%d differences' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
