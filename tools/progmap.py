#!/usr/bin/env python3
"""progmap.py - PROGRAM_MAP.txt: every program file in programs/ with its global labels, the
global labels it calls and its steps; then the N-label map of the NAV files (build/).

  python3 tools/progmap.py
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(ROOT, 'programs')


def main():
    rows = []
    for f in sorted(os.listdir(PROG)):
        if not f.endswith('.txt') or f.startswith(('COPYING', 'LICENSE')):
            continue
        L = [l.strip() for l in open(os.path.join(PROG, f), encoding='utf-8') if l.strip()]
        labels = [m.group(1) for l in L for m in [re.fullmatch(r'LBL "(.+)"', l)] if m]
        calls = sorted({m.group(1) for l in L for m in [re.fullmatch(r'(?:XEQ|GTO) "(.+)"', l)] if m} - set(labels))
        rows.append((f[:-4], ', '.join(labels), ', '.join(calls) or '-', len(L)))
    out = ['C47 NAV - PROGRAM MAP (global labels and calls)', '',
           'FILE      GLOBAL LABELS                          CALLS                                            STEPS',
           '-' * 104]
    for f, lab, cal, n in rows:
        out.append('%-9s %-38s %-48s %d' % (f, lab, cal, n))
    out += ['', 'Folders:',
            '  programs/      programs to load (no comments)',
            '  programs_rem/  same programs with REM comment lines (try one file with the converter first)',
            '  listings/      numbered listings with comments per subroutine, for reading and debugging',
            '                 (step numbers = line numbers of the plain programs)',
            '  build/         the files for the calculator: NAVFULL, NAVFULL_NOTBL, NAVALL, NAVCOMP, NAVTXT,',
            '                 NAVINIT_FULL, NAVINIT_FAST, TBL (python3 tools/build_navfull.py)',
            '',
            'LABELS IN THE NAV FILES',
            '  In the build/ files only NAV (and INIT) keep their names; every other global label is',
            '  N01, N02 ... The map for NAVFULL / NAVFULL_NOTBL (fonts included) follows; NAVALL, NAVCOMP',
            '  and NAVTXT have their own numbering in build/<file>_LABELS.txt.', '']
    out += ['  ' + l for l in open(os.path.join(ROOT, 'build', 'NAVFULL_LABELS.txt'), encoding='utf-8').read().split('\n')
            if re.match(r'(NAV|N\d\d)\s', l)]
    open(os.path.join(ROOT, 'PROGRAM_MAP.txt'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('PROGRAM_MAP.txt', len(rows), 'programs')


if __name__ == '__main__':
    main()
