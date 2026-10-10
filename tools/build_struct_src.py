#!/usr/bin/env python3
"""build_struct_src.py - the C47 NAVFULL from its STRUCT source, programs_struct/ (C47 / R47 only).

programs_struct/ holds one file per program, written with the C47 STRUCT commands (IF ELSE ENDIF, DO WHILE ENDDO,
REPEAT UNTIL) indented two spaces per level, without the partner numbers, with REM lines. No GTO of any kind: every
decision and loop is a structure, every other jump a call (XEQ) or a return; a code end shared by several branches is
a small routine they call (XEQ nn then RTN), never a copy of its steps. Same screens as build/dev/struct/18_hourglass
(tests/test_struct_src.py, pixel for pixel).

The build: the REM lines and the indentation go, every program is checked as VALID checks it (tools/c47struct.py
check: closers of the right kind, nothing open at END or across RTN + LBL, a DO has its WHILE, a test before IF / WHILE
/ UNTIL, none before ELSE ENDIF DO ENDDO REPEAT), the partner numbers are written ("IF 01": the C47 checks only the last
program of a file as it loads), and the programs go into one file in ORDER. The order of the programs, and of the
routines inside each file, is the one build_struct.py layout() finds for the searches (labels, structure steps, the walk
of a return from the program's start): the busiest first. The labels are numbered 01, 02 ... in the order they appear
(the 228 that XEQ IND reaches keep their numbers), so the source and the calculator's listing match step for step.

Free42 has no STRUCT: build_free42.py keeps its own sources (programs/). The old-hardware DM42 build of the firmware
allows 10 structures of a kind per program: not for NAVLITTLE either.

  python3 tools/build_struct_src.py      -> build/dev/struct_src/NAVFULL.txt (and its bytes when rejig is installed)
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import c47struct as C                                                         # noqa: E402

SRC = os.path.join(ROOT, 'programs_struct')
OUT = os.path.join(ROOT, 'build', 'dev', 'struct_src')
ORDER = ['NAV', 'CALC', 'PTXS', 'HANIM', 'OUT7', 'PSYS', 'ALLSKY', 'CSUN', 'HCZ', 'HDR', 'PLN2', 'SUNA', 'MOO2', 'HORZ', 'PSYB',
         'RISE', 'HALMH', 'CSTA', 'ALMF', 'SBRT', 'OUT8', 'SNMU', 'PHA2', 'WPLS', 'CMN', 'OUT5', 'OUT6', 'OUT1', 'OUT2',
         'OUT3', 'OUT4', 'TGET', 'CMS', 'OUT9']


def source(name):
    """The steps of programs_struct/NAME.txt: no REM, no indentation, no partner numbers."""
    lines = open(os.path.join(SRC, name + '.txt'), encoding='utf-8').read().split('\n')
    return C.plain([l for l in lines if l.strip() and not l.strip().startswith('REM ')])


def build():
    """The listing (numbered), or SystemExit with the faults."""
    left = sorted(set(f[:-4] for f in os.listdir(SRC) if f.endswith('.txt') and f != 'README.txt') - set(ORDER))
    if left:
        raise SystemExit('build_struct_src: %s not in ORDER' % ', '.join(left))
    L, faults = [], []
    for name in ORDER:
        P = source(name)
        progs = C.split(P)
        if len(progs) != 1:
            faults.append('%s: %d programs (one END a file)' % (name, len(progs)))
        for f in C.check(P):
            faults.append('%s: %s' % (name, f))
        for l in P:
            if l.startswith('GTO'):
                faults.append('%s: %s (no GTO in the source)' % (name, l))
        L += P
    if faults:
        raise SystemExit('build_struct_src:\n  ' + '\n  '.join(faults))
    return C.number(L)


def stats(L):
    P = C.plain(L)
    return {'steps': len(P), 'programs': len(C.split(P)), 'labels': sum(1 for l in P if l.startswith('LBL ')),
            'IF': sum(1 for l in P if l == 'IF'), 'DO': sum(1 for l in P if l == 'DO'),
            'REPEAT': sum(1 for l in P if l == 'REPEAT'), 'GTO': sum(1 for l in P if l.startswith('GTO')),
            'XEQ': sum(1 for l in P if l.startswith('XEQ'))}


def main():
    L = build()
    os.makedirs(OUT, exist_ok=True)
    f = os.path.join(OUT, 'NAVFULL.txt')
    open(f, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    try:
        import build_navopt as N
        size = N.p47(f)
    except Exception:
        size = None
    s = stats(L)
    print('  %s: %d steps in %d programs, %d labels, IF %d DO %d REPEAT %d, GTO %d, XEQ %d; %s bytes'
          % (f[len(ROOT) + 1:], s['steps'], s['programs'], s['labels'], s['IF'], s['DO'], s['REPEAT'], s['GTO'],
             s['XEQ'], size or '? (no rejig)'))


if __name__ == '__main__':
    main()
