#!/usr/bin/env python3
"""The NAVFULL builds with N01... labels (build/) must work exactly like the named ones
(build/dev/): every NAV menu option, same screens and PROMPT texts, FULL and FAST matrices.
  python3 tests/test_labels.py"""
import os, sys, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tests')]
sys.argv = sys.argv[:1]
from test_notbl import load
from decimal import Decimal as D


def run_nav(c, option, answers_after):
    c.s = [D(0)] * 4; c.lift = True; c.msgs = []; c.frames = []; c.pix = []; c.steps = 0
    c.answers = [None] * 4 + [option] + answers_after + [0]      # DATE UTC LAT LON prompts: R/S keeps the values
    c.flags.add(82)
    c.maxprompts = len(c.answers) + 1; c.maxpauses = 30
    c.reg['DATE'] = D('2026.1002'); c.reg['UTC'] = D('18.00'); c.reg['LAT'] = D('25.12'); c.reg['LON'] = D('55.18')
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return sorted(c.pix), [sorted(f) for f in c.frames], [str(m) for m in c.msgs], c.steps


def main():
    # names that must not appear in the renamed files as labels
    for f in ('NAVFULL', 'NAVFULL_NOTBL'):
        labels = re.findall(r'^(?:LBL|XEQ|GTO) "(.+)"$', open(os.path.join(ROOT, 'build', f + '.txt'), encoding='utf-8').read(), re.M)
        other = sorted({l for l in labels if l != 'NAV' and not re.fullmatch(r'N\d\d', l)})
        assert not other, (f, other)
    bad = 0
    for init in ('NAVINIT_FULL', 'NAVINIT_FAST'):
        for f in ('NAVFULL', 'NAVFULL_NOTBL'):
            named = load(['build/%s.txt' % init, 'build/dev/%s.txt' % f])
            renamed = load(['build/%s.txt' % init, 'build/%s.txt' % f])
            for opt, extra in ((1, []), (2, []), (3, [None] * 8), (4, []), (5, []), (6, []), (7, [None, None, 60, None, None]),
                               (8, []), (9, [])):
                a, b = run_nav(named, opt, extra), run_nav(renamed, opt, extra)
                if a != b:
                    bad += 1; print('DIFF', init, f, 'option', opt)
            print('%s + %s: 9 NAV options compared' % (init, f))
    print('%d differences' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
