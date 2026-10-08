#!/usr/bin/env python3
"""build_struct.py - structural optimizations of the C47 NAVFULL, one folder per step (branch struct-opt).

The release build/NAVFULL.txt is the input and is never changed; nothing in programs/ changes either. Each step is
applied on top of the one before it and written to its own folder, so every version is kept and can be measured,
loaded on the calculator or dropped on its own:

  build/dev/struct/1_tailcall/NAVFULL.txt   XEQ x followed by RTN becomes GTO x (the RTN stays: a test before the
                                            XEQ can skip to it). One RTN less per call, and its walk from the start
                                            of the program to the return step (fnReturn -> defineCurrentStep).
                                            Not in NAV or N83 or towards them: they use local registers (LocR), and
                                            a GTO shares the caller's.
  build/dev/struct/2_order/NAVFULL.txt      the programs reordered in the file (and so in the calculator's memory):
                                            GTO nn / XEQ nn search the label table from the first program in memory
                                            (fnGoto), so the programs that jump most go first. Order: numbered jumps
                                            run per label of the program, most first (counted on the pages ALMANAC,
                                            SKY, ANIM, ALLSKY in the Python simulator).

Why, and what the firmware does: tools/tests_calc/TSTRUCT_README.txt, build/dev/struct/README.txt.

  python3 tools/build_struct.py        then compare the pages and the CPU in the firmware simulator (README.txt)
"""
import collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import build_navopt as N                                                     # noqa: E402

SRC = os.path.join(ROOT, 'build', 'NAVFULL.txt')
OUT = os.path.join(ROOT, 'build', 'dev', 'struct')
TARGET = 'FULL'                   # 'FULL': build/NAVFULL.txt; 'LITTLE': build/dm42/NAVLITTLE.txt (python3 ... little)


def local_programs(L):
    """The programs with local registers (LocR, R.nn): no tail call in them or towards them (NAVFULL: NAV, N83)."""
    return {name(p) for p in split(L) if [l for l in p if l.startswith('LocR') or 'R.' in l]}
# the keys of the pages counted for the order: 1 ALMANAC, 3 SKY, 4 ANIM, 5 ALLSKY, then + back to the menu, 0 end
PAGES = ([72, 85, 82], [74, 85, 82], [62, 85, 82], [63, 85, 82])


def split(L):
    """The programs of a listing, in order: [[lines from LBL "name" to END]]."""
    progs, cur = [], []
    for l in L:
        cur.append(l)
        if l == 'END':
            progs.append(cur)
            cur = []
    assert not [l for l in cur if l.strip()], 'build_struct: lines after the last END'
    return progs


def name(prog):
    return re.fullmatch(r'LBL "(.+)"', prog[0]).group(1)


def tailcall(L):
    """XEQ x; RTN -> GTO x; RTN, outside the LocR programs and not towards them."""
    LOCAL = local_programs(L)
    out, n = [], 0
    for p in split(L):
        if name(p) not in LOCAL:
            p = list(p)
            for i in range(len(p) - 1):
                m = re.fullmatch(r'XEQ (\d\d|"(\w+)")', p[i])
                if m and p[i + 1] == 'RTN' and m.group(2) not in LOCAL:
                    p[i] = 'GTO ' + m.group(1)
                    n += 1
        out += p
    print('  1_tailcall: %d XEQ + RTN -> GTO' % n)
    return out


def hits(L):
    """How often each line of L runs on the counted pages (Python simulator; its lines are L's, labels renamed)."""
    import test_v2 as V
    from decimal import Decimal as D
    out = [0] * len(L)
    if TARGET == 'LITTLE':
        init = [l for l in open(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'), encoding='utf-8').read()
                .split('\n') if l.strip()]
        import tempfile, c47sim
        t = tempfile.mkdtemp(); files = []
        for i, pr in enumerate(V.T.split(init + L)):
            f = os.path.join(t, 'p%d.txt' % i); open(f, 'w', encoding='utf-8').write('\n'.join(pr) + '\n'); files.append(f)
        c = c47sim.load(files); c.flags.add(82); c.grfnt = 21
        c.run('INIT', maxsteps=10 ** 7)
        for k, v in V.INPUTS:
            c.reg[k] = D(v)
        h = collections.Counter()
        c.count = lambda op, x: h.update([c.at])
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = [V.K['up'], V.K['down'], V.K['down'], V.K['+']]
        c.run('NAV', maxsteps=10 ** 8)
        a = c.lines.index(L[0])                     # the listing's first program (NAV may have moved)
        assert len(c.lines) - a == len(L), 'build_struct: the simulator lines are not the listing'
        return [h[a + i] for i in range(len(L))]
    for keys in PAGES:
        c = V.T.load(L, 'FULL')
        for k, v in V.INPUTS:
            c.reg[k] = D(v)
        h = collections.Counter()
        c.count = lambda op, x: h.update([c.at])
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
        c.run('NAV', maxsteps=10 ** 8)
        a = c.lines.index(L[0])                     # the listing's first program (NAV may have moved)
        assert len(c.lines) - a == len(L), 'build_struct: the simulator lines are not the listing'
        for i in range(len(L)):
            out[i] += h[a + i]
    return out


def counts(L):
    """Numbered GTO / XEQ run per program on the counted pages."""
    jumps, h = collections.Counter(), hits(L)
    for p, a in starts(L):
        for i in range(a, a + len(p)):
            if re.fullmatch(r'(GTO|XEQ) \d\d', L[i]):
                jumps[name(p)] += h[i]
    return jumps


def starts(L):
    """[(program lines, index of its first line in L)]."""
    out, a = [], 0
    for p in split(L):
        out.append((p, a))
        a += len(p)
    return out


def order(L):
    """The programs that run the most numbered jumps per label first (each jump scans the labels before it)."""
    jumps = counts(L)
    progs = split(L)
    nlbl = {name(p): max(1, sum(l.startswith('LBL ') for l in p)) for p in progs}
    progs.sort(key=lambda p: -jumps[name(p)] / nlbl[name(p)])
    print('  2_order: ' + ' '.join('%s(%d/%d)' % (name(p), jumps[name(p)], nlbl[name(p)]) for p in progs))
    return [l for p in progs for l in p]


SKIPS = {'DSE', 'ISG', 'DSZ', 'ISZ', 'KEY?'}       # and every command ending in ?: they can skip the next step


def skips(l):
    op = l.split(' ')[0]
    return op in SKIPS or op.endswith('?')


def exits(p, i):
    """p[i] always leaves (RTN or GTO, and no test before it can skip it)."""
    return (p[i] == 'RTN' or p[i].startswith('GTO ')) and not (i > 0 and skips(p[i - 1]))


def callpos(L):
    """Inside each program, the blocks with the most calls and named entries per step first: every RTN walks from
    the start of the caller's program to the call, every XEQ "name" from the start of the program to the label.
    A block starts at a label after a step that always leaves, so it is only entered through its labels; the first
    block (the program's entry) stays first, a last block that runs into END stays last."""
    assert not [l for l in L if l.split(' ')[0] in ('SKIP', 'BACK', 'IF', 'ELSE', 'ENDIF', 'DO', 'WHILE', 'ENDDO')], \
        'build_struct: a relative jump; blocks cannot move'
    h = hits(L)
    named = collections.Counter()
    for i, l in enumerate(L):
        m = re.fullmatch(r'(?:GTO|XEQ) "(\w+)"', l)
        if m:
            named[m.group(1)] += h[i]
    out, moved = [], 0
    for p, a in starts(L):
        cuts = [0] + [i for i in range(1, len(p) - 1) if p[i].startswith('LBL ') and exits(p, i - 1)] + [len(p) - 1]
        blocks = [(cuts[k], cuts[k + 1]) for k in range(len(cuts) - 1)]

        def weight(b):
            w = sum(h[a + i] for i in range(*b) if p[i].startswith('XEQ '))
            w += 2 * sum(named[m.group(1)] for i in range(*b) for m in [re.fullmatch(r'LBL "(\w+)"', p[i])] if m)
            return w / (b[1] - b[0])
        first, last = blocks[:1], []
        mid = blocks[1:]
        if mid and not exits(p, mid[-1][1] - 1):
            last, mid = mid[-1:], mid[:-1]
        new = first + sorted(mid, key=lambda b: -weight(b)) + last
        moved += new != blocks
        out += [p[i] for b in new for i in range(*b)] + ['END']
    print('  3_callpos: blocks reordered in %d programs' % moved)
    return out


MAXBODY = 6       # steps of a routine copied into its callers
MINRUN = 20       # calls run on the counted pages before a call site is worth a copy


def inline(L):
    """XEQ of a short routine run often -> its steps. The routine: LBL, at most MAXBODY steps without a label,
    jump, END, local register or test right before its RTN; the call: no test before it (the test would skip only
    the first copied step) unless the routine is one step, not in a LocR program unless the routine is there too."""
    h = hits(L)
    LOCAL = local_programs(L)
    bodies = {}                                   # (program, label) -> steps
    for p, a in starts(L):
        for i, l in enumerate(p):
            m = re.fullmatch(r'LBL (\d\d|"\w+")', l)
            if not m:
                continue
            j = i + 1
            while j < len(p) and j - i - 1 <= MAXBODY and not re.match(r'(LBL|GTO|XEQ|RTN|END|LocR)\b', p[j]) \
                    and 'R.' not in p[j]:
                j += 1
            if j < len(p) and p[j] == 'RTN' and j > i + 1 and not skips(p[j - 1]) and j - i - 1 <= MAXBODY:
                key = (None if m.group(1).startswith('"') else name(p), m.group(1).strip('"'))
                bodies[key] = p[i + 1:j]
    out, n, grown = [], 0, 0
    for p, a in starts(L):
        for i, l in enumerate(p):
            m = re.fullmatch(r'XEQ (\d\d|"(\w+)")', l)
            body = None
            if m:
                body = bodies.get((None, m.group(2)) if m.group(2) else (name(p), m.group(1)))
            if body and h[a + i] >= MINRUN and (len(body) == 1 or not (i > 0 and skips(p[i - 1]))) \
                    and (name(p) not in LOCAL or not m.group(2)):
                out += body
                n += 1
                grown += len(body) - 1
            else:
                out.append(l)
    print('  4_inline: %d calls replaced by their steps (+%d steps)' % (n, grown))
    return out


def swap(L, old, new, times=1):
    """Replace the step sequence old by new, exactly `times` times (a check that the build still looks as expected)."""
    t = '\n' + '\n'.join(L) + '\n'
    o, n = '\n' + '\n'.join(old) + '\n', '\n' + '\n'.join(new) + '\n'
    assert t.count(o) == times, 'build_struct: %d x %s (expected %d)' % (t.count(o), old, times)
    return t.replace(o, n)[1:-1].split('\n')


SKY_STEP = 6      # deg between equator dots on SKY and ANIM (release 2: 180 dots)
CHART_STEP = 9    # on SPLIT and ALLSKY (release 3: 120 dots)
BLOCK = 10        # dots computed together by CEQQ (release 30): must divide 360 / SKY_STEP and 360 / CHART_STEP


def equator(L, sky=None, chart=None):
    """The celestial equator of the charts with fewer dots, each one POINT (3 x 3 pixels around the old 2 x 2 dot,
    which took four PIXEL): every SKY_STEP deg on SKY and ANIM, every CHART_STEP deg on SPLIT and ALLSKY. CEQQ
    computes the dots in blocks of BLOCK; the cache keys (SKY_STEP -> U2, CHART_STEP -> U3) follow. The loops
    count the dots one by one (ISG 0.nnn01), the step goes to HCZQ / CEQQ."""
    sky, chart = sky or SKY_STEP, chart or CHART_STEP
    nsky, nchart = round(360 / sky), round(360 / chart)
    assert nsky * sky == 360 and nchart * chart == 360 and nsky % BLOCK == 0 and nchart % BLOCK == 0 and sky != chart
    S, C = '%g' % sky, '%g' % chart
    isg = lambda n: '0.%03d01' % (n - 1)
    # the views: step and loop count (ANIM through HCZQ / HCZR, the others through CEQQ / CEQR)
    L = swap(L, ['RCL 46', 'RCL 44', 'XEQ "N34"', '0.35802'], ['RCL 46', S, 'XEQ "N34"', isg(nsky)])
    L = swap(L, ['RCL 46', 'RCL 44', 'XEQ "N77"', '0.35802'], ['RCL 46', S, 'XEQ "N77"', isg(nsky)])
    L = swap(L, ['RCL 46', 'RCL 51', 'XEQ "N77"', '0.35703'], ['RCL 46', C, 'XEQ "N77"', isg(nchart)], 2)
    # CEQQ (N77) and CEQR (N78): the cache for each step, its size
    L = swap(L, ['RCL "Q9"', 'RCL 51', 'X=Y?', 'GTO 43'], ['RCL "Q9"', C, 'X=Y?', 'GTO 43'])
    L = swap(L, ['RCL "Q9"', 'RCL 44', 'X=Y?', 'GTO 42'], ['RCL "Q9"', S, 'X=Y?', 'GTO 42'])
    L = swap(L, ['LBL 43', 'RCL 51', 'STO "G4"'], ['LBL 43', C, 'STO "G4"'])
    L = swap(L, ['LBL 42', 'RCL 44', 'STO "G4"'], ['LBL 42', S, 'STO "G4"'])
    L = swap(L, ['120', 'XEQ 49', 'STO "U3"'], [str(nchart), 'XEQ 49', 'STO "U3"'])
    L = swap(L, ['RCL 62', 'XEQ 49', 'STO "U2"'], [str(nsky), 'XEQ 49', 'STO "U2"'])
    L = swap(L, ['LBL "N78"', 'RCL "G4"', 'RCL 44', 'X=Y?', 'GTO 41'], ['LBL "N78"', 'RCL "G4"', S, 'X=Y?', 'GTO 41'])
    a = L.index('LBL "N77"')
    s = L.index('LBL 49', a)
    e = L.index('DELITM "W2"', s)
    assert L[e + 1] == 'RTN' and L.index('END', a) > e
    L = L[:s] + [str(BLOCK) if l == 'RCL 75' else l for l in L[s:e]] + L[e:]
    # the dots: four PIXEL -> one POINT
    four = lambda y, x: [y, x, 'PIXEL', y, x, 'RCL 43', '+', 'PIXEL', y, 'RCL 43', '+', x, 'PIXEL',
                         y, 'RCL 43', '+', x, 'RCL 43', '+', 'PIXEL']
    for y, x in (('RCL 09', 'RCL 05'), ('RCL 09', 'RCL 08'), ('RCL 08', 'RCL 23')):
        L = swap(L, four(y, x) + ['RTN'], [y, x, 'POINT', 'RTN'])
    L = swap(L, ['STO 06'] + four('RCL 06', 'RCL 23')[1:] + ['RTN'], ['STO 06', 'RCL 23', 'POINT', 'RTN'])
    print('  5_equator: SKY / ANIM every %s deg (%d dots), SPLIT / ALLSKY every %s deg (%d), POINT, blocks of %d'
          % (S, nsky, C, nchart, BLOCK))
    return L


def anim(L):
    """ANIM's frames without the 1 s wait: PAUSE 10 -> PAUSE 0 (each frame still reaches the LCD; 24 frames = 24 s
    less). The PAUSE 0 of the SINKING box and of the bar after a key stay: the C47 shows the screen only at a PAUSE
    or a key wait."""
    a = L.index('LBL "N61"')
    e = L.index('END', a)
    idx = [i for i in range(a, e) if L[i] == 'PAUSE 10']
    assert len(idx) == 1 and L.count('PAUSE 10') == 1, 'build_struct: PAUSE 10 not only in ANIM'
    print('  6_anim: ANIM PAUSE 10 -> PAUSE 0')
    return L[:idx[0]] + ['PAUSE 0'] + L[idx[0] + 1:]


AQ_VARS = ('AQ', 'AQL', 'AQP', 'AQ1', 'AQ2', 'AQ3', 'AQ4', 'AQ5', 'AQ6', 'AQK', 'AQI', 'AQD', 'AQQ')


def animq(L):
    """ANIM: the quick Sun (SUNF) and Moon (MOOQ) only at frames 0, 12 and 23, the other 21 frames interpolated.
    The three frames go into a 3 x 4 matrix AQ (rows: the frames; columns: Sun GHA - w t, Sun Dec, Moon GHA - w t,
    Moon Dec; w = 360.98564736629 deg / day in R78, t the time since frame 0, so the columns change slowly); each
    frame takes one product (Lagrange weights 1 x 3) x AQ and adds w t back. MOOQ reads T (R08) and GHA Aries (R04),
    which LBL 71 sets from the JD in R28, as each frame does before SUNF. Largest difference to computing every
    frame, 300 random 12-hour runs 2000-2050: Sun 0.000000 deg, Moon 0.0007 deg (a pixel of the chart is about
    1 deg; MOOQ itself is good to 0.3 deg). The variables AQ... are deleted when the frames are done."""
    a = L.index('LBL "N61"')
    e = L.index('END', a)
    P = L[a:e]
    assert 'RCL 70' in P and P[P.index('RCL 70') + 1] == 'STO 18', 'build_struct: ANIM frames are not R70 = 24'
    used = {l for l in P if l.startswith('LBL ')}
    assert not used & {'LBL %d' % n for n in (70, 73, 74, 75, 76, 77, 78, 79)}, 'build_struct: ANIM labels taken'
    P = swap(P, ['RCL 46', 'STO 22', 'LBL 01'], ['RCL 46', 'STO 22', 'XEQ 75', 'LBL 01'])
    P = swap(P, ['RCL 28', 'XEQ "N17"', 'XEQ "N32"'], ['XEQ 76', 'XEQ "N32"'])
    P = swap(P, ['STO 29', 'XEQ "N26"', 'XEQ "N32"'], ['STO 29', 'XEQ 77', 'XEQ "N32"'])
    i = P.index('GTO 01', P.index('LBL 68'))
    assert P[i + 1] in ('GTO "N63"', 'XEQ "N63"'), P[i - 3:i + 3]
    P = P[:i + 1] + ['DELITM "%s"' % v for v in AQ_VARS] + P[i + 1:]
    P += ['LBL 75', '3', 'ENTER', '4', 'NEWMAT', 'STO "AQ"', '1', 'STO "AQI"',
          '0', 'XEQ 79', '12', 'XEQ 79', '23', 'XEQ 79', 'RTN',
          # one of the three frames (X = 0, 12 or 23): SUNF and MOOQ, GHA - w t unwrapped against frame 0, into AQ
          'LBL 79', 'STO "AQK"', 'RCL× 20', 'RCL÷ 70', 'RCL+ 19', 'STO 28', 'XEQ 71', 'RCL 28',
          'XEQ "N17"', 'XEQ 74', 'STO "AQ1"', 'X<>Y', 'STO "AQ2"',
          'XEQ "N26"', 'XEQ 74', 'STO "AQ3"', 'X<>Y', 'STO "AQ4"',
          'RCL "AQK"', 'X=0?', 'XEQ 73',
          'RCL "AQ1"', 'RCL- "AQ5"', 'XEQ 70', 'RCL+ "AQ5"', 'STO "AQ1"',
          'RCL "AQ3"', 'RCL- "AQ6"', 'XEQ 70', 'RCL+ "AQ6"', 'STO "AQ3"',
          'INDEX "AQ"', 'RCL "AQI"', '1', 'STOIJ', 'RCL "AQ1"', 'STOSEQ', 'RCL "AQ2"', 'STOSEQ',
          'RCL "AQ3"', 'STOSEQ', 'RCL "AQ4"', 'STOSEQ', '1', 'STO+ "AQI"', 'RTN',
          'LBL 73', 'RCL "AQ1"', 'STO "AQ5"', 'RCL "AQ3"', 'STO "AQ6"', 'RTN',
          'LBL 70', 'RCL 62', '+', 'RCL 45', 'MOD', 'RCL 62', '-', 'RTN',
          'LBL 74', 'RCL "AQK"', 'RCL× 20', 'RCL÷ 70', 'RCL× 78', '-', 'RTN',
          # frame R22: the weights of the frames 0, 12, 23, one product, the Sun (X GHA, Y Dec)
          'LBL 76', '1', 'ENTER', '3', 'NEWMAT', 'STO "AQL"', 'INDEX "AQL"', '1', 'ENTER', 'STOIJ',
          'RCL 22', '12', '-', 'RCL 22', '23', '-', '×', '276', '÷', 'STOSEQ',
          'RCL 22', 'RCL 22', '23', '-', '×', '-132', '÷', 'STOSEQ',
          'RCL 22', 'RCL 22', '12', '-', '×', '253', '÷', 'STOSEQ',
          'RCL "AQL"', 'RCL "AQ"', '×', 'STO "AQP"', 'INDEX "AQP"',
          '1', 'ENTER', '2', 'STOIJ', 'RCLEL', 'STO "AQD"', '1', 'ENTER', '1', 'STOIJ', 'RCLEL', 'STO "AQQ"',
          'RCL "AQD"', 'RCL "AQQ"', 'GTO 78',
          # the Moon of the same frame
          'LBL 77', 'INDEX "AQP"', '1', 'ENTER', '4', 'STOIJ', 'RCLEL', 'STO "AQD"',
          '1', 'ENTER', '3', 'STOIJ', 'RCLEL', 'STO "AQQ"', 'RCL "AQD"', 'RCL "AQQ"',
          'LBL 78', 'RCL 22', 'RCL× 20', 'RCL÷ 70', 'RCL× 78', '+', 'RCL 45', 'MOD', 'RTN']
    print('  7_animq: ANIM Sun and Moon at 3 frames, 21 interpolated (one 1x3 x 3x4 product per frame)')
    return L[:a] + P + L[e:]


MST_TEMP = ('YSA', 'YC4', 'YG', 'YH', 'YE', 'YX1', 'YX2', 'YB1', 'YB2', 'YB3', 'YB4', 'YQ', 'YMT', 'YV', 'YR',
            'YCC', 'YSS', 'YX', 'YY', 'YZ', 'YT')         # Y...: no NAV, NAVINIT or TBL name (TBL's Saturn is "TSA")


SETUP_TEMP = ('YS50', 'YK', 'YA', 'YD', 'YPA', 'YPD', 'YT', 'YDD', 'YAA', 'YCD', 'YSZ', 'YX', 'YY')


def navinit_mstars(src, dst):
    """NAVINIT with LBL 05: the star vectors SXA (x y z 1 at J2000) and SXD (their change per century, J2000 -> J2050
    as a straight line) computed once from NAVINIT's own catalogue ST, as TSTAR's set-up (a loop of about 60 steps:
    the 464 numbers written out made NAVINIT_FULL too large to load)."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    L = [l for l in open(src, encoding='utf-8').read().split('\n') if l.strip()]
    assert L[1:5] == ['XEQ 01', 'XEQ 02', 'XEQ 03', 'XEQ 04'] and L[-1] == 'END'
    assert not {'LBL 05', 'LBL 06', 'LBL 07', 'LBL 08'} & set(L), 'build_struct: NAVINIT labels 05-08 taken'
    code = gen_tstar.vector_setup('SXA', 'SXD', (5, 6, 7, 8))
    i = code.index('RTN')                                         # the end of LBL 05: delete the set-up's variables
    code = code[:i] + ['DELITM "%s"' % v for v in SETUP_TEMP] + code[i:]
    names = set(re.findall(r'"(Y\w+)"', '\n'.join(code)))
    assert names <= set(SETUP_TEMP), names - set(SETUP_TEMP)
    L = L[:5] + ['XEQ 05'] + L[5:-1] + code + ['END']
    open(dst, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    return N.p47(dst)


def mstars(L):
    """The 58 stars at once with matrices (tools/tests_calc/TSTAR.txt, part B) in place of one by one: CALC (a new
    time or place) computes GHA, Dec, Hc, Zn of every star from NAVINIT's SXA / SXD (two products (58 x 4) x (4 x 3))
    and puts the four columns into ALMC's star rows (7-64) with M.PUTM; CSQK (over the horizon?) then compares the
    exact Hc with SQK's limit (sin Hc 0.15643, Hc 8.99974 deg) and reads the cache; SQK and STR2 no longer run for the
    views. ALLSKY keeps its own star path. Needs the NAVINIT of this folder (SXA, SXD)."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    # the stars right after the Sun (SUNA's T, obliquity, nutation, precession angles, and G2 G3 = cos / sin of
    # GHA Aries + longitude); the Moon and the planets then overwrite those registers (CSUN restores them later)
    L = swap(L, ['RCL 02', 'RCL+ 13', 'RCL 43', '→REC', 'STO "G2"', 'X<>Y', 'STO "G3"', 'XEQ "N46"'],
             ['RCL 02', 'RCL+ 13', 'RCL 43', '→REC', 'STO "G2"', 'X<>Y', 'STO "G3"', 'XEQ "N95"', 'XEQ "N46"'])
    L = swap(L, ['INDEX "ALMC"', '7', 'RCL 51', 'STOIJ', '58', 'STO 25', '-98', 'LBL 02', 'STOEL', 'I+', 'DSE 25',
                 'GTO 02'], [])
    L = swap(L, ['RCLEL', '-98', 'X=Y?', 'GTO 32', 'X<>Y', '-99', 'X=Y?', 'GTO 31', 'RCL 43', 'RTN'],
             ['RCLEL', '8.999740983204436', 'X>Y?', 'GTO 31', 'RCL 43', 'RTN'])
    P = ['LBL "N95"', 'DEG', 'XEQ 20', 'INDEX "ALMC"']
    for j in range(1, 5):
        P += ['7', 'ENTER', str(j), 'STOIJ', 'RCL "YB%d"' % j, 'M.PUTM']
    P += ['DELITM "%s"' % v for v in MST_TEMP] + ['RTN'] + gen_tstar.matrix_stars('SXA', 'SXD') + ['END']
    names = set(re.findall(r'"(Y\w+)"', '\n'.join(P)))
    assert names <= set(MST_TEMP), names - set(MST_TEMP)
    assert not re.findall(r'"T\w+"', '\n'.join(P)), 'build_struct: a T... name in N95 (TBL uses T...)'
    d = os.path.join(OUT, '8_mstars')
    os.makedirs(d, exist_ok=True)
    for init in ('NAVINIT_FULL', 'NAVINIT_FAST'):
        n = navinit_mstars(os.path.join(ROOT, 'build', init + '.txt'), os.path.join(d, init + '.txt'))
        print('  8_mstars: %s with SXA SXD, %d bytes' % (init, n))
    print('  8_mstars: stars by matrix in CALC (N95), CSQK reads the exact Hc')
    return L + P


def allsky(L):
    """ALLSKY reads its 58 stars from the cache (CSTR GHA / Dec, CHCZ Hc / Zn: the exact values step 8 computes for
    every star) in place of its own quick ones (catalogue RA / Dec, a linear precession, then the full HCZ: about 9
    trig values a star). ALLSKY calls CSUN with its own time first, so the cache is the hour on the screen (the
    arrows too). The stars move by less than 1' (nutation, aberration, the exact precession): at most a pixel."""
    a = L.index('LBL "N62"')
    e = L.index('END', a)
    P = swap(L[a:e], ['INDEX "ST"', 'RCL 21', 'IP', 'RCL 43', 'STOIJ', 'RCLEL', 'STO 22', 'J+', 'RCLEL', 'STO 05',
                      'RCL 22', 'COS', '20.0431', '×', 'RCL× 06', 'RCL+ 05', 'RCL 22', 'SIN', 'RCL 05', 'TAN', '×',
                      '20.0431', '×', '46.1244', '+', 'RCL× 06', 'RCL+ 22', 'RCL 02', 'X<>Y', '-', 'RCL 45', 'MOD',
                      'XEQ "N69"'],
             ['RCL 21', 'IP', 'STO 22', 'XEQ "N67"', 'XEQ "N69"'])
    assert 'XEQ "N64"' in P, 'build_struct: ALLSKY does not call CSUN'     # (step 3 moved its blocks: not by line)
    print('  9_allsky: ALLSKY stars from the cache (CSTR, CHCZ)')
    return L[:a] + P + L[e:]


def selfinit(L):
    """The star vectors SXA / SXD made by NAV itself, the first time (from NAVINIT's catalogue ST, as step 8's NAVINIT
    does), then kept like the cache ALMC: the release NAVINIT stays. The test: 0 STO+ "SXK" (STO+ makes a missing
    variable with 0: allocateNamedVariableOnMiss; RCL of a missing name would stop NAV); SXK = 0: make SXA SXD, SXK = 1."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    a = L.index('LBL "N95"')
    e = L.index('END', a)
    P = L[a:e]
    assert P[:3] == ['LBL "N95"', 'DEG', 'XEQ 20'] and not {'LBL 10', 'LBL 11', 'LBL 12', 'LBL 13'} & set(P)
    setup = gen_tstar.vector_setup('SXA', 'SXD', (10, 11, 12, 13))
    i = setup.index('RTN')
    setup = setup[:i] + ['DELITM "%s"' % v for v in SETUP_TEMP] + ['1', 'STO "SXK"'] + setup[i:]
    P = P[:2] + ['0', 'STO+ "SXK"', 'RCL "SXK"', 'X=0?', 'XEQ 10'] + P[2:] + setup
    print('  10_selfinit: NAV makes SXA SXD the first time (release NAVINIT)')
    return L[:a] + P + L[e:]


HYB_TEMP = ('YSA', 'YC4', 'YG', 'YH', 'YQ', 'YMT', 'YV', 'YR', 'YCC', 'YSS', 'YX', 'YY', 'YZ', 'YT')


def fill_columns(e, h):
    """The angles of all 58 stars from the matrices e (GHA frame) and h (north / east / zenith): M.GETM columns,
    ∡ of complex columns, ABS; results in YB1-YB4 (GHA, Dec, Hc, Zn). TSTAR's LBL 20 after its two products."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    ms = gen_tstar.matrix_stars('SXA', 'SXD')
    l20 = ms[:ms.index('LBL 30')]
    a = l20.index('INDEX "YE"') + 1
    b = l20.index('RTN')
    out = l20[a:b]
    i = out.index('RCL "YSA"')                       # the second product -> the matrix h
    assert out[i:i + 5] == ['RCL "YSA"', 'RCL "YH"', '×', 'STO "YE"', 'INDEX "YE"']
    out = out[:i] + ['INDEX "%s"' % h] + out[i + 5:]
    assert 'RCL "YSA"' not in out and 'YE' not in ' '.join(out)
    return out


def hybrid(L):
    """Stars: the matrices at each new time, the angles only for the stars a page asks for (fast hour arrows).
    CALC (N95): the 4 x 3 matrix (about 9 trig values) and the two products, kept as SXE (58 x 3, the stars in the
    GHA frame) and SXH (58 x 3, north / east / zenith); every star row of ALMC marked "not computed" (-98) as in the
    release. CSQK on a -98 star: the zenith component of SXH is sin Hc (no trig) against SQK's limit (R92); under it
    the star is marked -99 (LBL 33, as in the release), else N97 computes GHA Dec Hc Zn from its two rows (4 →POL)
    into the cache. ALLSKY: N98 computes any star still without values (-98 or -99) before reading it.
    The same formulas as steps 8-10 (atan2 of the same vectors): the same values."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    # CSQK: -98 -> LBL 32 (test and compute), -99 -> 0, else the exact Hc against the limit (as step 8)
    L = swap(L, ['RCLEL', '8.999740983204436', 'X>Y?', 'GTO 31', 'RCL 43', 'RTN'],
             ['RCLEL', '-98', 'X=Y?', 'GTO 32', 'X<>Y', '-99', 'X=Y?', 'GTO 31', 'X<>Y', '8.999740983204436', 'X>Y?',
              'GTO 31', 'RCL 43', 'RTN'])
    L = swap(L, ['LBL 32', 'RCL "V0"', 'XEQ "N23"', 'RCL 92', 'X>Y?', 'GTO 33', 'XEQ "N22"', 'STO "V0"', 'X<>Y',
                 'STO "V1"', 'X<>Y', 'XEQ 94', 'INDEX "ALMC"', 'RCL 22', 'RCL 93', '+', 'XEQ 90', 'RCL 43', 'RTN'],
             ['LBL 32', 'INDEX "SXH"', 'RCL "V0"', 'RCL 51', 'STOIJ', 'RCLEL', 'RCL 92', 'X>Y?', 'GTO 33',
              'RCL "V0"', 'XEQ "N97"', 'RCL 43', 'RTN'])
    # ALLSKY: every star computed before CSTR / CHCZ read it
    L = swap(L, ['RCL 21', 'IP', 'STO 22', 'XEQ "N67"', 'XEQ "N69"'],
             ['RCL 21', 'IP', 'STO 22', 'XEQ "N98"', 'XEQ "N67"', 'XEQ "N69"'])
    # N95 again: the matrices only, then the -98 marks
    a = L.index('LBL "N95"')
    e = L.index('END', a)
    old = L[a:e]
    setup = old[old.index('LBL 10'):]
    assert setup[0] == 'LBL 10' and '1' in setup and 'STO "SXK"' in setup
    ms = gen_tstar.matrix_stars('SXA', 'SXD')
    lbl30 = ms[ms.index('LBL 30'):]
    l20 = ms[:ms.index('LBL 30')]
    cut = l20.index('STO "YE"')
    l20 = l20[:cut] + ['STO "SXE"', 'RCL "YSA"', 'RCL "YH"', '×', 'STO "SXH"', 'RTN']
    P = ['LBL "N95"', 'DEG', '0', 'STO+ "SXK"', 'RCL "SXK"', 'X=0?', 'XEQ 10', 'XEQ 20',
         'INDEX "ALMC"', '7', 'RCL 51', 'STOIJ', '58', 'STO 25', '-98', 'LBL 02', 'STOEL', 'I+', 'DSE 25', 'GTO 02']
    P += ['DELITM "%s"' % v for v in HYB_TEMP] + ['RTN'] + l20 + lbl30 + setup
    names = set(re.findall(r'"(Y\w+)"', '\n'.join(P)))
    assert names <= set(HYB_TEMP) | set(SETUP_TEMP), names - set(HYB_TEMP) - set(SETUP_TEMP)
    # N97: star X -> GHA Dec Hc Zn into its ALMC row (R01 R05 R06 R07 R09: CSQK's old path used them as scratch)
    P += ['END', 'LBL "N97"', 'DEG', 'STO 07',
          'INDEX "SXE"', 'RCL 07', '1', 'STOIJ', 'RCLEL', 'STO 01', 'J+', 'RCLEL', 'STO 05', 'J+', 'RCLEL', 'STO 06',
          'INDEX "ALMC"', 'RCL 07', 'RCL 93', '+', '1', 'STOIJ',
          'RCL 05', 'RCL 01', '→POL', 'X<>Y', 'CHS', 'RCL 45', 'MOD', 'STOSEQ',          # GHA = -atan2(y, x)
          'X<>Y', 'RCL 06', 'X<>Y', '→POL', 'X<>Y', 'STOSEQ',                           # Dec = atan2(z, r)
          'INDEX "SXH"', 'RCL 07', '1', 'STOIJ', 'RCLEL', 'STO 01', 'J+', 'RCLEL', 'STO 05', 'J+', 'RCLEL', 'STO 06',
          'RCL 05', 'RCL 01', '→POL', 'X<>Y', 'RCL 45', 'MOD', 'STO 05',              # Zn = atan2(east, north)
          'X<>Y', 'RCL 06', 'X<>Y', '→POL', 'X<>Y', 'STO 09',                         # Hc = atan2(up, r)
          'INDEX "ALMC"', 'RCL 07', 'RCL 93', '+', 'RCL 51', 'STOIJ', 'RCL 09', 'STOSEQ', 'RCL 05', 'STOEL', 'RTN',
          # N98 (ALLSKY): a star without values (-98, -99; a real Hc is never under -90) -> all 58 at once (N99)
          'LBL "N98"', 'INDEX "ALMC"', 'RCL 93', '+', 'RCL 51', 'STOIJ', 'RCLEL', '-90.5', 'X>Y?',
          'GTO "N99"', 'RTN']
    # N99: GHA Dec Hc Zn of every star from SXE / SXH with ∡ on whole columns (step 10's code), into ALMC (M.PUTM)
    P += ['LBL "N99"', 'DEG', 'INDEX "SXE"'] + fill_columns('SXE', 'SXH') + ['INDEX "ALMC"']
    for j in range(1, 5):
        P += ['7', 'ENTER', str(j), 'STOIJ', 'RCL "YB%d"' % j, 'M.PUTM']
    P += ['DELITM "%s"' % v for v in ('YX1', 'YX2', 'YB1', 'YB2', 'YB3', 'YB4')] + ['RTN']
    print('  11_hybrid: stars by matrix at each time, angles only for the stars a page asks for')
    return L[:a] + P + L[e:]


def labels(L):
    """Numbered labels inside a program, names only between programs; nothing that never runs.
    1. XEQ "name" / GTO "name" towards a global label of the same program -> XEQ nn / GTO nn: a numbered label is an
       integer scan of the label table and a jump by address; a name is a text compare of every global label and a
       walk from the start of the program. The free number goes right after the global label (LBL "N18", LBL 99).
       The call level is the same either way: XEQ nn starts a new level like XEQ "name" (LocR unchanged).
    2. A numbered label that no XEQ / GTO of its program names, in a program without XEQ / GTO IND, after a step that
       always leaves: its block (to the next label or END) can never run and goes.
    3. RTN just before END: END returns like RTN (both fnReturn); never after a test (it would skip END instead)."""
    out, moved, dead, rtn = [], 0, [], 0
    for p in split(L):
        glob = {re.fullmatch(r'LBL "(.+)"', l).group(1) for l in p if l.startswith('LBL "')}
        nums = {l[4:] for l in p if re.fullmatch(r'LBL \d\d', l)}
        free = [n for n in ('%02d' % k for k in range(99, -1, -1)) if n not in nums]
        own, new = {}, []
        for l in p:
            m = re.fullmatch(r'(XEQ|GTO) "(.+)"', l)
            if m and m.group(2) in glob:
                own.setdefault(m.group(2), free.pop(0))
                l = '%s %s' % (m.group(1), own[m.group(2)])
                moved += 1
            new.append(l)
        p = []
        for l in new:
            p.append(l)
            m = re.fullmatch(r'LBL "(.+)"', l)
            if m and m.group(1) in own:
                p.append('LBL %s' % own[m.group(1)])
        if not [l for l in p if re.match(r'(XEQ|GTO) IND', l)]:
            used = {l[4:] for l in p if re.fullmatch(r'(XEQ|GTO) \d\d', l)}
            i = 1
            while i < len(p):
                if re.fullmatch(r'LBL \d\d', p[i]) and p[i][4:] not in used and exits(p, i - 1):
                    j = i + 1
                    while not (p[j].startswith('LBL ') or p[j] == 'END'):
                        j += 1
                    dead.append('%s %s (%d steps)' % (name(p), p[i], j - i))
                    del p[i:j]
                else:
                    i += 1
        if len(p) > 2 and p[-2] == 'RTN' and not skips(p[-3]):
            del p[-2]
            rtn += 1
        out += p
    print('  12_labels: %d calls by name inside their program -> numbered; dead: %s; %d RTN before END'
          % (moved, ', '.join(dead) or 'none', rtn))
    return out


def renumber(L):
    """Inside each program the numbered labels in the order they appear: 01, 02, 03 ... and every XEQ / GTO nn with
    them. In a program with XEQ / GTO IND the labels no XEQ / GTO nn names keep their numbers (the number is the data:
    a star, a digit, a character code, a body + offset) and the others skip them. Only easier to read: GTO / XEQ nn
    cost the labels before it in the table, not its number."""
    out, fixed_all = [], 0
    for p in split(L):
        nums = [l[4:] for l in p if re.fullmatch(r'LBL \d\d', l)]
        direct = {l[4:] for l in p if re.fullmatch(r'(XEQ|GTO) \d\d', l)}
        ind = [l for l in p if re.match(r'(XEQ|GTO) IND', l)]
        fixed = {n for n in nums if n not in direct} if ind else set()
        fixed_all += len(fixed)
        free = ('%02d' % k for k in range(1, 100) if '%02d' % k not in fixed)
        new = {n: (n if n in fixed else next(free)) for n in nums}
        assert len(set(new.values())) == len(nums), name(p)
        for l in p:
            m = re.fullmatch(r'(LBL|XEQ|GTO) (\d\d)', l)
            out.append('%s %s' % (m.group(1), new[m.group(2)]) if m else l)
    print('  13_renumber: labels 01, 02 ... in order in every program; %d kept for XEQ / GTO IND' % fixed_all)
    return out


def clean(L):
    """What no page can run, and the names no program calls: the program N22 / N23 (STR2, SQK: its calls left with
    step 11), N24's entry (LBL "N24" XEQ "N15": the callers use N25), and the names N20 N76 N99 (reached by their
    numbered label since step 12). A program keeps the name on its first line (N28). Then 01, 02 ... again."""
    called = set(re.findall(r'^(?:XEQ|GTO) "(N\d\d)"$', '\n'.join(L), re.M))
    out = []
    for p in split(L):
        g = [re.fullmatch(r'LBL "(.+)"', l).group(1) for l in p if l.startswith('LBL "')]
        if not called & set(g):
            assert name(p) in ('NAV', 'N22'), name(p)
            if name(p) == 'N22':
                continue
        if name(p) not in called and name(p) == 'N24':
            assert p[1:3] == ['XEQ "N15"', 'LBL "N25"']
            p = p[2:]
        p = [p[0]] + [l for l in p[1:] if not (l.startswith('LBL "') and l[5:-1] not in called)]
        out += p
    names = len([l for l in out if l.startswith('LBL "')])
    print('  14_clean: program N22 / N23 and N24 entry removed; %d global labels' % names)
    return renumber(out)


def noregs(L):
    """NAV keeps none of your registers: no LocR 99 + RCL nn STO R.nn at the start, no RCL R.nn STO nn at the end;
    CLREGS there instead, before the CLSTK of the end (as v2.2.0)."""
    i = L.index('LBL "NAV"') + 1
    k = int(re.fullmatch(r'LocR (\d+)', L[i]).group(1))
    assert L[i + 1:i + 1 + 2 * k] == [x for j in range(k) for x in ('RCL %02d' % j, 'STO R.%02d' % j)]
    L = L[:i] + L[i + 1 + 2 * k:]
    back = [x for r in range(k) for x in ('RCL R.%02d' % r, 'STO %02d' % r)]
    j = [j for j in range(len(L)) if L[j:j + 2 * k] == back]
    assert len(j) == 1 and L[j[0] + 2 * k] == 'CLSTK'
    L = L[:j[0]] + ['CLREGS'] + L[j[0] + 2 * k:]
    e = L.index('END', L.index('LBL "NAV"'))
    assert not [l for l in L[:e] if 'R.' in l or l.startswith('LocR')]
    print('  15_noregs: NAV without LocR %d and the copies (%d steps), CLREGS CLSTK at the end' % (k, 4 * k + 1))
    return L


# host program <- the programs whose every entry only the host (or the group) calls
GROUPS = (('NAV', ('N61', 'N62')), ('N64', ('N38', 'N28', 'N46', 'N95')), ('N93', ('N47',)),
          ('N89', ('N88', 'N86', 'N87')))


def group(L):
    """Each group above becomes one program: the host, then its members (END -> RTN where code ran into END). The
    members' names become numbered labels (nothing outside the group calls them) and their calls XEQ / GTO nn. The
    labels of the whole group 00, 01 ... in order; the ones XEQ / GTO IND reach keep their numbers (they must not
    meet: checked). At most 100 numbered labels a program."""
    P = {name(p): p for p in split(L)}
    order = [name(p) for p in split(L)]
    for host, members in GROUPS:
        segs = [P[host]] + [P[m] for m in members]
        inner = {re.fullmatch(r'LBL "(.+)"', l).group(1) for s in segs[1:] for l in s if l.startswith('LBL "')}
        outside = {re.fullmatch(r'(?:XEQ|GTO) "(.+)"', l).group(1) for n, p in P.items() if n != host and n not in members
                   for l in p if re.fullmatch(r'(?:XEQ|GTO) "(.+)"', l)}
        assert not inner & outside, (host, inner & outside)
        fixed, maps, keys = {}, [], []
        for k, s in enumerate(segs):
            direct = {l[4:] for l in s if re.fullmatch(r'(XEQ|GTO) \d\d', l)}
            if [l for l in s if re.match(r'(XEQ|GTO) IND', l)]:
                for l in s:
                    if re.fullmatch(r'LBL \d\d', l) and l[4:] not in direct:
                        assert l[4:] not in fixed, (host, l)
                        fixed[l[4:]] = k
        free = ('%02d' % n for n in range(100) if '%02d' % n not in fixed)
        names = {}
        for k, s in enumerate(segs):
            m = {}
            for l in s[1 if k == 0 else 0:]:
                if re.fullmatch(r'LBL \d\d', l):
                    m[l[4:]] = l[4:] if fixed.get(l[4:]) == k else next(free)
                elif k and l.startswith('LBL "'):
                    names[l[5:-1]] = next(free)
            maps.append(m)
        body = []
        for k, s in enumerate(segs):
            s = s[:-1]                                              # the END
            if not exits(s, len(s) - 1):
                s = s + ['RTN']
            for l in s:
                m = re.fullmatch(r'(LBL|XEQ|GTO) (\d\d)', l)
                n = re.fullmatch(r'(XEQ|GTO) "(.+)"', l)
                if k and l.startswith('LBL "'):
                    l = 'LBL ' + names[l[5:-1]]
                elif m:
                    l = '%s %s' % (m.group(1), maps[k][m.group(2)])
                elif n and n.group(2) in names:
                    l = '%s %s' % (n.group(1), names[n.group(2)])
                body.append(l)
        P[host] = body + ['END']
        for m in members:
            order.remove(m)
        nl = len([l for l in body if re.fullmatch(r'LBL \d\d', l)])
        assert nl <= 100, (host, nl)
        print('  16_group: %s + %s: %d steps, %d numbered labels, %d names become numbers'
              % (host, ' '.join(members), len(body) + 1, nl, len(names)))
    out = [l for n in order for l in P[n]]
    assert not set(re.findall(r'^(?:XEQ|GTO) "(.+)"$', '\n'.join(out), re.M)) - set(re.findall(r'^LBL "(.+)"$', '\n'.join(out), re.M))
    print('  16_group: %d programs, %d global labels' % (out.count('END'), len([l for l in out if l.startswith('LBL "')])))
    return out


def _prog(L, test):
    """(first line, END line) of the one program for which test(its lines) is true."""
    found = [(a, b) for a, b in ((a, L.index('END', a)) for a, l in enumerate(L) if l.startswith('LBL "')
                                 and (a == 0 or L[a - 1] == 'END')) if test(L[a:b + 1])]
    assert len(found) == 1, found
    return found[0]


def _dms(lab):
    """HDR: ' d mm.m' of X appended to the text in R.04 (no padding: the letter, a space, the degrees). R.05 =
    tenths of a minute. No XEQ: a called level does not see HDR's local registers."""
    ap = lambda: ['x→α R.04']
    return (['ABS', '600', '×', 'RCL 56', '+', 'IP', 'STO R.05', '" "'] + ap()
            + ['RCL R.05', '600', '÷', 'IP', 'αIP R.04', '" "'] + ap()
            + ['RCL R.05', '600', 'MOD', '10', '÷', 'IP', '10', 'X≤Y?', 'GTO %02d' % lab, '"0"'] + ap()
            + ['LBL %02d' % lab, 'RCL R.05', '600', 'MOD', '10', '÷', 'IP', 'αIP R.04', '"."'] + ap()
            + ['RCL R.05', '10', 'MOD', 'αIP R.04'])


def topbar(L):
    """The top bar as 'DATE TIME UT DR   N 40 24.0   W 3 42.0': DR, the latitude and the longitude one text and one
    ATEXT at column 143 (built in R.04 with x→α / αIP, no padding), three spaces before N / S and before E / W, the
    letter right before its degrees. And the sky cache kept from one run of NAV to the next: NAV makes ALMC only
    when it is missing (0 STO+ creates it as a number; a matrix stays as it is, +0) or not 73 x 4; the key in its
    row 67 (JD, lat, lon) then decides, as between two views, so the same date, time and place draw at once."""
    a, b = _prog(L, lambda p: '"DR"' in p and 'LocR 05' in p)
    P = L[a:b + 1]
    i = P.index('"DR"') - 2
    assert P[i:i + 4] == ['RCL R.00', 'RCL 60', '"DR"', 'XEQ "N50"'] and P[-1] == 'END', P[i:i + 4]
    new = (['"DR   N"', 'STO R.04', 'RCL R.02', 'X≥0?', 'GTO 01', '"DR   S"', 'STO R.04', 'LBL 01', 'RCL R.02']
           + _dms(2) + ['RCL R.03', 'X<0?', 'GTO 03', '"   E"', 'GTO 05', 'LBL 03', '"   W"', 'LBL 05', 'x→α R.04',
                       'RCL R.03']
           + _dms(4) + ['RCL R.00', 'RCL 60', 'RCL R.04', 'XEQ "N50"', 'END'])
    P = [('LocR 06' if l == 'LocR 05' else l) for l in P[:i]] + new
    L = L[:a] + P + L[b + 1:]
    old = ['73', 'ENTER', 'RCL 66', 'NEWMAT', 'STO "ALMC"']
    j = [j for j in range(len(L)) if L[j:j + 5] == old]
    assert len(j) == 1 and 'LBL 49' not in L[:L.index('END')]
    L = L[:j[0]] + ['0', 'STO+ "ALMC"', 'RCL "ALMC"', 'MATR?', '42DIM#', '×', '292', 'X=Y?', 'GTO 49'] + old \
        + ['LBL 49'] + L[j[0] + 5:]
    print('  17_topbar: HDR %d -> %d steps; NAV keeps the cache ALMC' % (b + 1 - a, len(P)))
    return L


STEPS = (('1_tailcall', tailcall), ('2_order', order), ('3_callpos', callpos), ('4_inline', inline),
         ('5_equator', equator), ('6_anim', anim), ('7_animq', animq), ('8_mstars', mstars), ('9_allsky', allsky),
         ('10_selfinit', selfinit), ('11_hybrid', hybrid), ('12_labels', labels), ('13_renumber', renumber),
         ('14_clean', clean), ('15_noregs', noregs), ('16_group', group), ('17_topbar', topbar, '15_noregs'))


def _rtn_block(L, start, prog=None):
    s = L.index(start, L.index('LBL "%s"' % prog) if prog else 0)
    j = s
    while L[j] != 'RTN':
        j += 1
    return L[s:j + 1]


def little_map(L):
    """NAVFULL -> NAVLITTLE registers and names (each build numbered its own): STR2, HCZI and the vector Hc / Zn of
    both lined up step by step; the operands that differ are the mapping (scratch registers, used two ways, left out)."""
    F = [l for l in open(SRC, encoding='utf-8').read().split('\n') if l.strip()]
    mp, bad = {}, set()
    for a, b in ((_rtn_block(F, 'LBL "N22"'), _rtn_block(L, 'LBL "N09"')), (_rtn_block(F, 'LBL "N36"'), _rtn_block(L, 'LBL "N14"')),
                 (_rtn_block(F, 'LBL 99', 'N64'), _rtn_block(L, 'LBL 99', 'N01'))):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            ox, _, ax = x.partition(' ')
            oy, _, ay = y.partition(' ')
            assert ox == oy, (x, y)
            if ax != ay:
                if mp.get(ax, ay) != ay:
                    bad.add(ax)
                mp[ax] = ay
    return {k: v for k, v in mp.items() if k not in bad}


def to_little(P, mp):
    """NAVFULL code -> NAVLITTLE: the operands of RCL / RCL+ / RCL- / RCL× / RCL÷ through the mapping (the matrix code
    only reads NAV's registers); a register or name the mapping does not know stops the build."""
    out = []
    for l in P:
        m = re.fullmatch(r'(RCL[+\-×÷]?) (\d\d|"[A-Z]\d")', l)
        if m:
            assert m.group(2) in mp, 'build_struct: no NAVLITTLE register for %s' % l
            l = '%s %s' % (m.group(1), mp[m.group(2)])
        out.append(l)
    return out


LITE_TEMP = ('YC4', 'YQ', 'YMT', 'YV', 'YR', 'YCC', 'YSS', 'YX', 'YY', 'YZ', 'YT')


def little_stars(L):
    """NAVLITTLE (no sky cache, 64 KB on the old DM42): the stars of the ALMANAC loop as in step 11, without 58-row
    matrices per time (they left a few bytes free on the 64 KB DM42). Before the loop N95 makes two 4 x 3 matrices
    for the time: SXG (the star vector -> the GHA frame) and SXH (-> north / east / zenith); SXA SXD (the star vectors,
    7.4 KB) are made by NAV the first time, from NAVINIT_LITTLE's ST. In the loop SQK becomes N96: the star's row
    (x y z 1 at T: SXA + T SXD) times SXH, the zenith component is sin Hc (no trig); STR2 + the vector Hc / Zn become
    N97: the same row times SXG, then GHA Dec Hc Zn (4 →POL) into the same registers (R17 GHA, R18 Dec, R24 Hc,
    R23 Zn, W4 sin Hc). Kept between calls: YS (the star's row, 1 x 4), YHR and YER (its horizon and GHA-frame vectors, 1 x 3)."""
    sys.path.insert(0, os.path.join(HERE, 'tests_calc'))
    import gen_tstar
    mp = little_map(L)
    T, ARIES = mp['03'], mp['02']
    a = L.index('LBL "N01"')
    e = L.index('END', a)
    P = swap(L[a:e], ['RCL 35', 'STO 15', '1.058', 'STO 16'], ['XEQ "N95"', 'RCL 35', 'STO 15', '1.058', 'STO 16'])
    P = swap(P, ['XEQ "N10"', '0.15643'], ['XEQ "N96"', '0.15643'])
    P = swap(P, ['XEQ "N09"', 'STO 17', 'X<>Y', 'STO 18', 'XEQ 96'], ['RCL 12', 'XEQ "N97"'])
    ms = to_little(gen_tstar.matrix_stars('SXA', 'SXD'), mp)
    setup = gen_tstar.vector_setup('SXA', 'SXD', (10, 11, 12, 13))
    i = setup.index('RTN')
    setup = setup[:i] + ['DELITM "%s"' % v for v in SETUP_TEMP] + ['1', 'STO "SXK"'] + setup[i:]
    S = ['LBL "N95"', 'DEG', '0', 'STO+ "SXK"', 'RCL "SXK"', 'X=0?', 'XEQ 10', 'XEQ 30',
         'RCL %s' % ARIES, 'XEQ 73', '[M]⊤', 'RCL "YC4"', 'X<>Y', '×', 'STO "SXG"',
         'XEQ 40', 'RCL "YC4"', 'X<>Y', '×', 'STO "SXH"'] + ['DELITM "%s"' % v for v in LITE_TEMP] + ['RTN']
    S += ms[ms.index('LBL 30'):] + setup + ['END']
    S += ['LBL "N96"', 'DEG', 'STO 20',                                                  # star X: its row at T
          'INDEX "SXD"', 'RCL 20', '1', 'STOIJ', '1', 'ENTER', '4', 'M.GETM', 'RCL× %s' % T, 'STO "YS"',
          'INDEX "SXA"', 'RCL 20', '1', 'STOIJ', '1', 'ENTER', '4', 'M.GETM', 'RCL "YS"', '+', 'STO "YS"',
          'RCL "SXH"', '×', 'STO "YHR"', 'INDEX "YHR"', '1', 'ENTER', '3', 'STOIJ', 'RCLEL', 'RTN',   # sin Hc
          'LBL "N97"', 'DEG', 'STO 20',
          'RCL "YS"', 'RCL "SXG"', '×', 'STO "YER"', 'INDEX "YER"',                       # x y z of the star (1 x 3)
          '1', 'ENTER', '1', 'STOIJ', 'RCLEL', 'STO 17', 'J+', 'RCLEL', 'STO 19', 'J+', 'RCLEL', 'STO 23',
          'RCL 19', 'RCL 17', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 17',             # GHA = -atan2(y, x)
          'X<>Y', 'RCL 23', 'X<>Y', '→POL', 'X<>Y', 'STO 18',                           # Dec = atan2(z, r)
          'INDEX "YHR"', '1', 'ENTER', '1', 'STOIJ', 'RCLEL', 'STO 19', 'J+', 'RCLEL', 'STO 23', 'J+', 'RCLEL', 'STO 24',
          'RCL 23', 'RCL 19', '→POL', 'X<>Y', '360', 'MOD', 'STO 23',                 # Zn = atan2(east, north)
          'X<>Y', 'RCL 24', 'X<>Y', '→POL', 'RCL 24', 'X<>Y', '÷', 'STO "W4"', 'DROP',  # sin Hc = up / length
          'STO 24', 'RTN', 'END']
    assert not re.findall(r'"T\w+"', '\n'.join(S))
    print('  5_stars: NAVLITTLE stars by matrix (4 x 3 per time), angles only for the stars the table asks for')
    assert L[-1] == 'END'
    return L[:a] + P + L[e:-1] + S


def free42(L):
    """Free42 NAVFULL with the screens of the C47 step 11: the equator every SKY_STEP deg (SKY, ANIM) and CHART_STEP deg
    (SPLIT, ALLSKY), each dot 3 x 3 pixels as the C47 POINT (x-1..x+1, y-1..y+1 around the old 2 x 2 dot at x..x+1,
    y..y+1; nine calls of the pixel routine N79 in place of four); ALLSKY's stars exact (STR2 N22 and CHCZ N68, which
    falls back to HCZ, in place of the catalogue with a linear precession), as the C47 step 9. Free42 has no frame
    wait in ANIM and computes every frame (the C47 interpolation changes no pixel): nothing to do there."""
    nsky, nchart = round(360 / SKY_STEP), round(360 / CHART_STEP)
    S, C = '%g' % SKY_STEP, '%g' % CHART_STEP
    isg = lambda n: '0.%03d01' % (n - 1)
    L = swap(L, ['0', '2', 'XEQ "N76"', '0.35802'], ['0', S, 'XEQ "N76"', isg(nsky)], 2)        # SKY, ANIM
    L = swap(L, ['0', '3', 'XEQ "N76"', '0.35703'], ['0', C, 'XEQ "N76"', isg(nchart)], 2)      # SPLIT, ALLSKY
    L = swap(L, ['RCL "U2"', '3', 'X=Y?', 'GTO 43', 'RCL "U2"', '2', 'X=Y?', 'GTO 42'],        # CEQQ: the cache rows
             ['RCL "U2"', C, 'X=Y?', 'GTO 43', 'RCL "U2"', S, 'X=Y?', 'GTO 42'])
    assert nchart <= 120 and nsky <= 180                    # ALMQ rows 1-120 and 121-300
    def dot(y, x):
        def plus(v, d):
            return [v] if d == 0 else [v, '1', '+' if d > 0 else '-']
        old = []
        for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
            old += plus(y, dy) + plus(x, dx) + ['XEQ "N79"']
        new = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                new += plus(y, dy) + plus(x, dx) + ['XEQ "N79"']
        return old, new
    old, new = dot('RCL 00', 'RCL 25')                     # SKY: the first y is still in X after STO 00
    L = swap(L, ['STO 00'] + old[1:] + ['RTN'], ['STO 00', 'DROP'] + new + ['RTN'])
    for y, x in (('RCL 09', 'RCL 25'), ('RCL 09', 'RCL 05'), ('RCL 23', 'RCL 10')):
        old, new = dot(y, x)
        L = swap(L, old + ['RTN'], new + ['RTN'])
    a = L.index('LBL "N61"')
    e = L.index('END', a)
    P = swap(L[a:e], ['INDEX "ST"', 'RCL 22', 'IP', '1', 'STOIJ', 'RCLEL', 'STO 23', 'J+', 'RCLEL', 'STO 05',
                      'RCL 23', 'COS', '20.0431', '×', 'RCL× 09', 'RCL+ 05', 'RCL 23', 'SIN', 'RCL 05', 'TAN', '×',
                      '20.0431', '×', '46.1244', '+', 'RCL× 09', 'RCL+ 23', 'RCL 06', 'X<>Y', '-', 'RCL 43', 'MOD',
                      'XEQ "N68"'],
             ['RCL 22', 'IP', 'STO 23', 'XEQ "N22"', 'XEQ "N68"'])
    # STR2 reads the Sun's state that CSUN restores; ALLSKY keeps the Sun's GHA / Dec from its CSUN call in R07 R08,
    # two of those inputs: before the stars R07 R08 saved and CSUN called again for the same time R20 (a cache hit
    # that puts STR2's inputs back), after them R07 R08 given back (nothing else CSUN writes is read before ALLSKY
    # writes it again)
    P = swap(P, ['RCL 85', 'STO 22', 'LBL 20'], ['RCL 07', 'STO "YA7"', 'RCL 08', 'STO "YA8"', 'RCL 20', 'XEQ "N63"',
                                                 'RCL 85', 'STO 22', 'LBL 20'])
    P = swap(P, ['XEQ 15', 'ISG 22', 'GTO 20'], ['XEQ 15', 'ISG 22', 'GTO 20', 'RCL "YA7"', 'STO 07', 'RCL "YA8"',
                                                 'STO 08', 'DELITM "YA7"', 'DELITM "YA8"'])
    print('  free42: equator %s / %s deg with 3 x 3 dots, ALLSKY stars exact' % (S, C))
    return L[:a] + P + L[e:]


STEPS_LITTLE = (('1_tailcall', tailcall), ('2_order', order), ('3_callpos', callpos), ('4_inline', inline),
                ('5_stars', little_stars))


def main():
    global TARGET
    if sys.argv[1:] == ['f42']:
        L = [l for l in open(os.path.join(ROOT, 'build', 'free42', 'NAVFULL.txt'), encoding='utf-8').read().split('\n') if l.strip()]
        d = os.path.join(OUT, 'free42')
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, 'NAVFULL.txt')
        open(f, 'w', encoding='utf-8').write('\n'.join(free42(L)) + '\n')
        print('  %s: %d steps, .raw %s bytes' % (f[len(ROOT) + 1:], len([l for l in open(f) if l.strip()]), N.raw(f)))
        return
    if sys.argv[1:] == ['little']:
        TARGET = 'LITTLE'
        src, out, fname, steps = os.path.join(ROOT, 'build', 'dm42', 'NAVLITTLE.txt'), os.path.join(OUT, 'dm42'), 'NAVLITTLE.txt', STEPS_LITTLE
    else:
        src, out, fname, steps = SRC, OUT, 'NAVFULL.txt', STEPS
    L = [l for l in open(src, encoding='utf-8').read().split('\n') if l.strip()]
    done = {}
    for folder, step, *base in steps:          # a third item: the step is applied to that folder, not the one before
        L = step(list(done[base[0]]) if base else L)
        done[folder] = L
        d = os.path.join(out, folder)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, fname)
        open(f, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('  %s: %d steps, %d bytes' % (f[len(ROOT) + 1:], len(L), N.p47(f)))


if __name__ == '__main__':
    main()
