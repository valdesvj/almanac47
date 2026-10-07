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
LOCAL = ('NAV', 'N83')            # programs with LocR: no tail call in them or towards them
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
    for keys in PAGES:
        c = V.T.load(L, 'FULL')
        for k, v in V.INPUTS:
            c.reg[k] = D(v)
        h = collections.Counter()
        c.count = lambda op, x: h.update([c.at])
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
        c.run('NAV', maxsteps=10 ** 8)
        a = c.lines.index('LBL "NAV"')
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


STEPS = (('1_tailcall', tailcall), ('2_order', order), ('3_callpos', callpos), ('4_inline', inline),
         ('5_equator', equator), ('6_anim', anim))


def main():
    L = [l for l in open(SRC, encoding='utf-8').read().split('\n') if l.strip()]
    for folder, step in STEPS:
        L = step(L)
        d = os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, 'NAVFULL.txt')
        open(f, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('  %s: %d steps, %d bytes' % (f[len(ROOT) + 1:], len(L), N.p47(f)))


if __name__ == '__main__':
    main()
