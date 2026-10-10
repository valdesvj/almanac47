#!/usr/bin/env python3
"""build_struct_src.py - the C47 NAVFULL from its STRUCT source, programs_struct/ (C47 / R47 only).

programs_struct/ holds one file per program, written with the C47 STRUCT commands (IF ELSE ENDIF, DO WHILE ENDDO,
REPEAT UNTIL) indented two spaces per level, without the partner numbers, code only (no REM). No GTO of any kind: every
decision and loop is a structure, every other jump a call (XEQ) or a return; a code end shared by several branches is
a small routine they call (XEQ nn then RTN), never a copy of its steps. Same screens as build/dev/struct/18_hourglass
(tests/test_struct_src.py, pixel for pixel).

The build: the indentation goes, every program is checked as VALID checks it (tools/c47struct.py
check: closers of the right kind, nothing open at END or across RTN + LBL, a DO has its WHILE, a test before IF / WHILE
/ UNTIL, none before ELSE ENDIF DO ENDDO REPEAT), the partner numbers are written ("IF 01": the C47 checks only the last
program of a file as it loads), and the programs go into one file in ORDER. The order of the programs, and of the
routines inside each file, is the one build_struct.py layout() finds for the searches (labels, structure steps, the walk
of a return from the program's start): the busiest first. The labels are numbered 01, 02 ... in the order they appear
(the 228 that XEQ IND reaches keep their numbers), so the source and the calculator's listing match step for step.

Free42 has no STRUCT: build_free42.py keeps its own sources (programs/). The old-hardware DM42 build of the firmware
allows 10 structures of a kind per program: not for NAVLITTLE either.

The comments are not in the source: NAVFULL_COMMENTED.txt is the same listing (numbered, indented) with REM lines,
written from LABELS (each global label: its original name and what it does) and from the code itself (each local
routine: who calls it; the XEQ IND tables; the loops only RTN leaves). Only to read: without its REM lines it is
NAVFULL.txt step for step (tests/test_struct_src.py).

  python3 tools/build_struct_src.py      -> build/dev/struct_src/NAVFULL.txt (and its bytes when rejig is installed),
                                            build/dev/struct_src/NAVFULL_COMMENTED.txt
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

# the global labels: the name in the sources and the documentation (build/NAVFULL_LABELS.txt), what it does
LABELS = {
    'NAV': ('NAV', 'graphic menu (KEY?): asks DATE UTC LAT LON, keys 1-6 a view, 9 SNAP, arrows one hour, 0 ends (CLREGS CLSTK); the only named program'),
    'N01': ('ALMF', 'view 1 ALMANAC: GHA, Dec, Hc, Zn table of Sun, Moon, planets, stars; twilight, rise/set, Moon'),
    'N04': ('HORZ', 'view 3 SKY: horizon chart, the name of each body in turn every 2 s (+ back to the menu, arrows one hour)'),
    'N06': ('HALMH', 'view 2 SPLIT: horizon chart on top, the bodies below (8 rows)'),
    'N15': ('SUNA', 'Sun: VSOP87 series (matrices VL VB VR), nutation, aberration -> GHA, Dec, GHA Aries'),
    'N16': ('SUNG', 'Sun GHA/Dec for the sunrise iterations (tables if loaded, else SUNF)'),
    'N17': ('SUNF', 'Sun, low-precision formula (0.01 deg) for sunrise/twilight'),
    'N18': ('SER', 'sum of one series matrix with the matrix functions (COS, DOT)'),
    'N19': ('SERT', 'the time vectors SV1 SV2 used by SER'),
    'N25': ('MOO2', 'Moon GHA, Dec, HP, SD: Meeus series (matrices ML MB MCL MCB) after SUNA'),
    'N26': ('MOOQ', 'Moon, quick low-precision formula (BODY list, ANIM)'),
    'N28': ('PLN2', 'planet GHA/Dec/SHA/HP: VSOP87 series with light-time, after SUNA'),
    'N29': ('PLN3', 'planet for the screens: quick position first, full series only if it can be above the horizon'),
    'N32': ('HCZ', "sight reduction: Y = Dec, X = GHA -> Hc (R96), Zn (R97), sin Hc ('SHC')"),
    'N34': ('HCZQ', 'celestial equator: start of the dot-by-dot rotation'),
    'N35': ('HCZR', 'celestial equator: next point by rotation (no trig)'),
    'N36': ('HCZI', 'keeps sin/cos of the latitude for HCZ'),
    'N38': ('RISE', 'sunrise time UT (SUNRISE program)'),
    'N39': ('SET', 'sunset time UT'),
    'N40': ('NTWA', 'nautical twilight, morning, UT'),
    'N41': ('NTWP', 'nautical twilight, evening, UT'),
    'N44': ('TRAN', 'meridian passage of the Sun, UT'),
    'N46': ('PHA2', 'Moon phase after SUNA: illumination % and age in days (the new-moon search: one REPEAT, a second pass when the age is negative)'),
    'N47': ('SBRT', 'star number by brightness rank (1st brightest ... 58th)'),
    'N48': ('SNMU', 'star name from its number'),
    'N49': ('TGET', 'almanac tables (TBL): Chebyshev lookup (not in NAVFULL_NOTBL)'),
    'N50': ('PTXS', "TEXT: ATEXT in GRFNT 21 (Didier's N03 trick) - Z row of the base line, Y column, X text"),
    'N51': ('PINS', 'TEXT: whole number (one ATEXT)'),
    'N52': ('PF1S', 'TEXT: number with one decimal'),
    'N53': ('PHMS', 'TEXT: hh:mm from hours'),
    'N54': ('PDMS', "TEXT: degrees and minutes 'ddd mm.m' with sign"),
    'N55': ('PDTS', "TEXT: date 'dd-mm-yyyy' from a Julian Date"),
    'N56': ('PZNS', "TEXT: azimuth 'ddd.d'"),
    'N57': ('PHLS', 'horizontal line (X = length in pixels)'),
    'N61': ('HANIM', 'view 4 ANIM: the Sun and the Moon moving on the whole-sky chart (24 frames)'),
    'N62': ('ALLSKY', 'view 5 ALLSKY: whole sky, over the horizon above, under the horizon below'),
    'N63': ('WPLS', 'every view holds its screen here (KEY?): + back to the menu, up / down arrow one hour later / earlier'),
    'N64': ('CSUN', 'Sun from the cache (matrix ALMC); computes the whole sky (CALC) only for a new time or place'),
    'N65': ('CMOO', 'Moon from the cache'),
    'N66': ('CPLN', 'planet from the cache'),
    'N67': ('CSTR', 'star R82 from the cache'),
    'N68': ('CSQK', 'star from the cache: over the horizon test from SXH (sin Hc, no trig); its angles (CSTA) the first time a page asks'),
    'N69': ('CHCZ', 'Hc Zn from the cache for the body just read (else the real HCZ)'),
    'N70': ('CPHA', 'Moon phase from the cache'),
    'N71': ('CNTA', 'nautical twilight am from the cache (the five sun times: computed once per date and place)'),
    'N72': ('CRIS', 'sunrise from the cache'),
    'N73': ('CTRN', 'meridian passage from the cache'),
    'N74': ('CSET', 'sunset from the cache'),
    'N75': ('CNTP', 'nautical twilight pm from the cache'),
    'N77': ('CEQQ', 'celestial equator of the charts: start (replay from matrix ALMQ, or compute and record)'),
    'N78': ('CEQR', 'celestial equator of the charts: next dot (from ALMQ, or HCZR and record)'),
    'N79': ('PTTY', 'TEXT in the tinyFont (GRFNT 10, the charts) - Z row of the base line, Y column, X text'),
    'N80': ('PTNT', 'TEXT: whole number in the tinyFont'),
    'N81': ('PSYB', 'SYMBOL of a body, 12 rows (glyphs47, AGRAPH; the tables, the Moon phases) - Z row, Y column, X symbol'),
    'N82': ('PSYS', 'SYMBOL of a body, 7 rows (glyphs47, AGRAPH; the charts) - Z row, Y column, X symbol'),
    'N83': ('HDR', 'header of a view: date, UT, DR latitude N/S, longitude E/W (X row, Y time, Z lat, T lon; tools/navmat.py)'),
    'N84': ('CMN', 'compass row N E S W N of a chart (X row)'),
    'N85': ('CMS', 'compass row S W N E S of a chart, south up (X row)'),
    'N86': ('OUT1', 'steps shared by several routines (tools/navmat.py outline)'),
    'N87': ('OUT2', 'steps shared by several routines (tools/navmat.py outline)'),
    'N88': ('OUT3', 'steps shared by several routines (tools/navmat.py outline)'),
    'N89': ('OUT4', 'steps shared by several routines (tools/navmat.py outline)'),
    'N90': ('OUT5', 'steps shared by several routines (tools/navmat.py outline)'),
    'N91': ('OUT6', 'steps shared by several routines (tools/navmat.py outline)'),
    'N92': ('OUT7', 'steps shared by several routines (tools/navmat.py outline)'),
    'N93': ('OUT8', 'steps shared by several routines (tools/navmat.py outline)'),
    'N94': ('OUT9', 'steps shared by several routines (tools/navmat.py outline)'),
    'N95': ('CALC', 'the sky for a new time or place: Sun, Moon, planets into ALMC; the stars as matrices SXE SXH (58 x 3), marked to compute when a page asks'),
    'N97': ('CSTA', 'star X: GHA Dec Hc Zn from its rows of SXE / SXH (4 ->POL) into its ALMC row'),
    'N98': ('CALL', 'ALLSKY: a star without values (-98, -99) -> all 58 at once with angles on whole columns (M.PUTM)'),
}


def source(name):
    """The steps of programs_struct/NAME.txt: no indentation, no partner numbers."""
    lines = open(os.path.join(SRC, name + '.txt'), encoding='utf-8').read().split('\n')
    return C.plain([l for l in lines if l.strip()])


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
            if l.startswith('REM '):
                faults.append('%s: %s (no comments in the source: they go in NAVFULL_COMMENTED.txt)' % (name, l))
            m = re.fullmatch(r'LBL "(\w+)"', l)
            if m and m.group(1) not in LABELS:
                faults.append('%s: LBL "%s" has no entry in LABELS' % (name, m.group(1)))
        L += P
    if faults:
        raise SystemExit('build_struct_src:\n  ' + '\n  '.join(faults))
    return C.number(L)


def commented(L):
    """L (numbered) indented, with REM lines: a header per program, the name and job of each global label, the callers
    of each local routine, the XEQ IND tables, the loops only RTN leaves."""
    out = ['REM "NAVFULL (C47 / R47) in STRUCT - the commented listing of build/dev/struct_src/NAVFULL.txt"',
           'REM "built by tools/build_struct_src.py from programs_struct/ (code only); only to read"',
           'REM "without the REM lines it is NAVFULL.txt step for step. Labels: build/NAVFULL_LABELS.txt"']
    for name, P in zip(ORDER, C.split(L)):
        Q = C.plain(P)
        glob, owner = None, []                          # the global label each step belongs to
        for l in Q:
            m = re.fullmatch(r'LBL "(\w+)"', l)
            if m:
                glob = LABELS[m.group(1)][0]
            owner.append(glob)
        callers = {}
        for i, l in enumerate(Q):
            m = re.fullmatch(r'XEQ (\d\d)', l)
            if m:
                callers.setdefault(m.group(1), []).append(owner[i])
        ind = any(l.startswith('XEQ IND') for l in Q)
        out += ['', 'REM "' + '=' * 70 + '"', 'REM "program %s"' % name]
        for i, l in enumerate(C.indent(P)):
            pad = l[:len(l) - len(l.lstrip())]
            s = l.strip()
            m = re.fullmatch(r'LBL "(\w+)"', s)
            n = re.fullmatch(r'LBL (\d\d)', s)
            if m:
                out.append(l)
                out.append(pad + 'REM "%s - %s"' % (LABELS[m.group(1)][0], LABELS[m.group(1)][1].replace('"', "'")))
                continue
            if n and n.group(1) in callers:
                who = sorted(set(callers[n.group(1)]), key=callers[n.group(1)].index)
                out.append(pad + 'REM "routine %s (%s): called by %s"' % (n.group(1), owner[i],
                                                                        ', '.join('%s x%d' % (w, callers[n.group(1)].count(w)) for w in who)))
            elif n and ind:
                out.append(pad + 'REM "entry %s of the XEQ IND table (%s)"' % (n.group(1), owner[i]))
            if s.startswith('REPEAT'):
                d, j = 0, i
                while True:
                    o = C.op(Q[j])
                    d += o in C.OPENERS
                    d -= o in ('ENDIF', 'ENDDO', 'UNTIL')
                    if d == 0:
                        break
                    j += 1
                if Q[j - 2:j] == ['0', 'X≠0?']:
                    out.append(pad + 'REM "loop left only by RTN (0 X≠0? UNTIL is never true)"')
            out.append(l)
    return out


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
    g = os.path.join(OUT, 'NAVFULL_COMMENTED.txt')
    open(g, 'w', encoding='utf-8').write('\n'.join(commented(L)) + '\n')
    s = stats(L)
    print('  %s: %d steps in %d programs, %d labels, IF %d DO %d REPEAT %d, GTO %d, XEQ %d; %s bytes'
          % (f[len(ROOT) + 1:], s['steps'], s['programs'], s['labels'], s['IF'], s['DO'], s['REPEAT'], s['GTO'],
             s['XEQ'], size or '? (no rejig)'))
    print('  %s: the same with comments (only to read)' % g[len(ROOT) + 1:])


if __name__ == '__main__':
    main()
