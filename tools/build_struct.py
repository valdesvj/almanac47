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


def counts(L):
    """Numbered GTO / XEQ run per program on the counted pages (Python simulator)."""
    import test_v2 as V
    from decimal import Decimal as D
    jumps = collections.Counter()
    for keys in PAGES:
        c = V.T.load(L, 'FULL')
        for k, v in V.INPUTS:
            c.reg[k] = D(v)
        hits = collections.Counter()
        c.count = lambda op, x: hits.update([c.at])
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
        c.run('NAV', maxsteps=10 ** 8)
        prog = None
        for i, l in enumerate(c.lines):                    # the simulator renames local labels: GTO 1_25
            m = re.fullmatch(r'LBL "(.+)"', l)
            if m and prog is None:
                prog = m.group(1)
            if re.fullmatch(r'(GTO|XEQ) \d+_\w+', l):
                jumps[prog] += hits[i]
            if l == 'END':
                prog = None
    return jumps


def order(L):
    """The programs that run the most numbered jumps per label first (each jump scans the labels before it)."""
    jumps = counts(L)
    progs = split(L)
    nlbl = {name(p): max(1, sum(l.startswith('LBL ') for l in p)) for p in progs}
    progs.sort(key=lambda p: -jumps[name(p)] / nlbl[name(p)])
    print('  2_order: ' + ' '.join('%s(%d/%d)' % (name(p), jumps[name(p)], nlbl[name(p)]) for p in progs))
    return [l for p in progs for l in p]


STEPS = (('1_tailcall', tailcall), ('2_order', order))


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
