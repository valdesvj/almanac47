#!/usr/bin/env python3
"""build_navfull.py - the smallest set of C47 programs for the almanac screens.

Writes plain-text files (convert each with tools/rejig47_atext.py, or a rejig that knows ATEXT
and GRFNT, to FILE.p47). Needs a C47 firmware with ATEXT and GRFNT.

  Text on the screens: the C47's ATEXT command in GRFNT 21 (the standard font, one column
  narrower per character) and the tinyFont (GRFNT 10) on the charts: PTXS and the number
  printers (tools/atext_common.py). NAV sets GRFNT 21 after the inputs and 20 again on the way
  out. The only drawn font left is the body symbols of glyphs47 (PSYB 12 rows in the tables,
  PSYS 7 rows on the charts). The views are programs/atext/t21/ (genviews_atx.py, mode t21).

  Program labels: only NAV keeps its name; every other label is N01, N02 ... on the calculator
  (build/NAVFULL_LABELS.txt lists them; build/dev/ has the named versions used by the tests).
  NAVFULL.txt  everything that must stay on the calculator for ALMF, HALMV, ALMT and HORZ
               (menu NAV, the three screens, the text almanac, Sun, stars, Moon, planets, sight
               reduction, sunrise/twilight, Moon phase, star order and names,
               the table lookup TGET, the ATEXT text routines and the symbols)
  NAVFULL_NOTBL.txt  the same without the almanac tables: no TGET, no table hooks in
               SUNA/MOON/PLAN/BODY, no "T" letter (the "X" letter stays). Use it when
               memory is short and you do not load TBL. Load NAVFULL OR NAVFULL_NOTBL.
  NAVINIT_FULL.txt  one program INIT: builds the matrices of MATA MATST MATM MATP (VSOP87,
               2000-2050) - the builders are LBL 01-04 inside INIT
  NAVINIT_FAST.txt  one program INIT: MATN MATST MATM MATF (fitted series for a few years:
               faster, smaller). Load ONE of them, XEQ "INIT" once, then delete INIT
               (GTO "INIT", CLP) - the matrices it built stay. Zero elements are not stored (NEWMAT
               starts with zeros).
  TBL_1.txt, TBL_5.txt  almanac tables for 1 and 5 years (from 1 Oct 2026): load ONE, XEQ "TBL"
               once, then delete (build/dev/TBL_4M.txt: the 4-month table of the tests)

Menu NAV (graphic, KEY?: key the number; every view waits for + to come back; key 9 takes a
picture of the screen with SNAP, in the menu and in every view):
1 ALMANAC (ALMF), 2 CHART (HALMV), 3 TEXT (ALMR: the page into the registers, NAV ends),
4 SKY (HORZ, info line per body without end), 5 SPLIT (HALMH: chart on top, the table below
to the bottom of the screen), 6 ANIM (HANIM: the Sun and the Moon moving on the horizon chart,
24 frames 0.5 h apart, 1 s each), 7 ALLSKY (the whole sky: horizon across the middle, over /
under the horizon), 8 INFO. The warning line is in the menu and INFO (not on the views).
Not included: ALMS (the old 5 SMALL), HORZS, HPLT, HALM, ALM (manual table method), SNAM,
SUNSD and the font demos.

  python3 tools/build_navfull.py            -> build/NAVFULL.txt, NAVFULL_NOTBL.txt, NAVINIT_FULL.txt, NAVINIT_FAST.txt, TBL_1.txt, TBL_5.txt
"""
import os, re, shutil, sys
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generators'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generators', 'atext')]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(ROOT, 'programs')
OUT = os.path.join(ROOT, 'build')

KEEP = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'HALMH', 'STXT', 'SUNA', 'STAR', 'MOON', 'PLAN', 'CHZ', 'SUNRISE', 'PHAS',
        'SBRT', 'SNMU', 'TGET', 'PTXS', 'PTXT', 'HANIM', 'ALLSKY', 'WPLS', 'CACHE']
INIT = ['MATA', 'MATST', 'MATM', 'MATP']
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'
TXT_TABLES = True          # NAVTXT reads the almanac tables (TBL) when they are loaded
# the C47 builds: the small AGRAPH font (PTXT) gives way to the glyphs47 symbols
KEEP21 = KEEP[:KEEP.index('PTXT')] + ['PSYB', 'PSYS'] + KEEP[KEEP.index('PTXT') + 1:]
T21_VIEWS = ('ALMF', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')     # programs/atext/t21/


def read(name):
    with open(os.path.join(PROG, name + '.txt'), encoding='utf-8') as fh:
        return [l.rstrip('\n') for l in fh if l.strip()]


def strings(lines):
    return ''.join(l.strip('"') for l in lines if l.startswith('"'))


def trim_font(lines, keep):
    """Drop the glyph routines (LBL code >= 33 ... RTN) whose character is not in keep."""
    out, skip = [], False
    for l in lines:
        m = re.fullmatch(r'LBL (\d+)', l)
        if m and int(m.group(1)) >= 33:
            skip = chr(int(m.group(1))) not in keep
        if not skip:
            out.append(l)
        if skip and l == 'RTN':
            skip = False
    return out


def nav_min(lines):
    """NAV: the graphic menu (tools/generators/gennav.py), 1-9 views, 0 end; no INIT option."""
    assert lines[0] == 'LBL "NAV"' and 'KEY? 39' in lines and 'MATA' not in '\n'.join(lines)
    return lines


def compact(lines):
    """Drop '0' + 'STOEL' pairs: a new matrix is full of zeros already."""
    out, i = [], 0
    while i < len(lines):
        if lines[i] == '0' and i + 1 < len(lines) and lines[i + 1] == 'STOEL':
            i += 2
            continue
        out.append(lines[i]); i += 1
    return out


def cut(s, old, new='', count=1):
    """Replace an exact block; fail loudly if the source changed."""
    assert s.count(old) == count, 'no-tables: block not found %r' % old[:60]
    return s.replace(old, new)


def no_tables(progs):
    """Programs without the almanac tables (TBL/TGET): the calculator always uses the
    series. Removes TGET, the table hooks in SUNA, MOON, PLAN, BODY (flags 10 and 11)
    and the "T" letter of the screens. The "X" letter (flag 12, date outside the FAST
    period) stays. The Python version keeps the tables option."""
    p = {n: '\n'.join(L) + '\n' for n, L in progs.items() if n != 'TGET'}
    import gencache
    p['CACHE'] = '\n'.join(gencache.program(False)) + '\n'          # no flag 11 (table Moon)
    # SUNA: table override after the series, and SUNG goes straight to SUNF
    p['SUNA'] = cut(p['SUNA'], 'FS? 10\nXEQ 45\n')
    p['SUNA'] = cut(p['SUNA'], 'LBL 45\nRCL 70\n0\nXEQ "TGET"\nX<0?\nRTN\nSTO 81\nR↓\nSTO 77\nRCL 70\n6\nXEQ "TGET"\nX<0?\nRTN\nSTO 80\nRTN\n')
    p['SUNA'] = cut(p['SUNA'], 'LBL "SUNG"\nFC? 10\nGTO "SUNF"\nSTO 70\n0\nXEQ "TGET"\nX≥0?\nRTN\nRCL 70\n', 'LBL "SUNG"\n')
    # MOON: table lookup and the flag 11 (values from the tables)
    p['MOON'] = cut(p['MOON'], 'FC? 10\nGTO 22\nRCL 70\n5\nXEQ "TGET"\nX<0?\nGTO 22\nSF 11\nRTN\nLBL 22\nCF 11\n', 'LBL 22\n')
    # PLAN: table lookup in PLN2, and PLN3 no longer diverts to PLN2
    s = p['PLAN']
    i = s.index('LBL "PLN2"\nSTO 09\nFC? 10\n') + len('LBL "PLN2"\nSTO 09\n')
    j = s.index('LBL 33\n', i)
    assert 'XEQ "TGET"' in s[i:j] and s[i:j].endswith('LBL 32\nRCL 34\nSTO 09\n')
    p['PLAN'] = cut(s[:i] + s[j:], 'LBL "PLN3"\nFS? 10\nGTO "PLN2"\n', 'LBL "PLN3"\n')
    # BODY: Moon distance from the tables and its "T" letter
    # screens: "T" letter (FS? 11 XEQ 29, LBL 29 "T" ...)
    for n in ('ALMF', 'ALMT', 'HALMV', 'HALMH', 'HORZ', 'HANIM', 'ALLSKY'):
        p[n] = cut(p[n], 'FS? 11\nXEQ 29\n')
        p[n] = re.sub(r'LBL 29\n"T"\n(STO \d+\n)?RTN\n', '', p[n], count=1)
    s = ''.join(p.values())
    for bad in ('TGET', 'FS? 10', 'FC? 10', 'FS? 11', 'SF 11', 'CF 11'):
        assert bad not in s, 'no-tables: %s left' % bad
    return {n: v.rstrip('\n').split('\n') for n, v in p.items()}


LABEL_OPS = ('LBL', 'XEQ', 'GTO')

# what every program label does (NAVFULL_LABELS.txt); FONT = text-drawing routine
LABEL_TEXT = {
 'NAV':   'graphic menu (KEY?): asks DATE UTC LAT LON, key 1-7 a view, 8 INFO, 9 SNAP, 0 ends (the only named program; INFO page inside)',
 'CSUN':  'Sun from the cache (matrix ALMC); computes the whole sky (CALC) only for a new time or place',
 'CMOO':  'Moon from the cache',
 'CPLN':  'planet from the cache',
 'CSTR':  'star R82 from the cache',
 'CPHA':  'Moon phase from the cache',
 'CNTA':  'nautical twilight am from the cache (the five sun times: computed once per date and place)',
 'CRIS':  'sunrise from the cache',
 'CTRN':  'meridian passage from the cache',
 'CSET':  'sunset from the cache',
 'CNTP':  'nautical twilight pm from the cache',
 'CALC':  'computes Sun, Moon, planets (GHA Dec Hc Zn) into matrix ALMC; stars marked to compute when asked',
 'CSQK':  'star from the cache: over the horizon test (computes the star the first time: SQK, STR2, HCZ)',
 'CHCZ':  'Hc Zn from the cache for the body just read (else the real HCZ)',
 'CEQQ':  'celestial equator of the charts: start (replay from matrix ALMQ, or compute and record)',
 'CEQR':  'celestial equator of the charts: next dot (from ALMQ, or HCZR and record)',
 'WPLS':  'every view holds its screen here (KEY?): + back to the menu, up / down arrow one hour later / earlier',
 'ALMF':  'view 1 ALMANAC: GHA, Dec, Hc, Zn table of Sun, Moon, planets, stars; twilight, rise/set, Moon',
 'HALMV': 'view 2 CHART: horizon chart left, Hc/Zn of 10 bodies right (no ARIES, no Moon line)',
 'ALMR':  'view 3 TEXT: the almanac page as text in R50-R76 (and the stack and lettered registers); NAV ends in REGS',
 'HORZ':  'view 4 SKY: horizon chart, info line per body every 3 s (+ back to the menu, arrows one hour)',
 'ALMS':  'short almanac (Sun, Moon, 1 planet, 3 stars; not in the NAV menu)',
 'HALMH': 'view 5 SPLIT: horizon chart on top, the bodies below (8 rows)',
 'HANIM': 'view 6 ANIM: the Sun and the Moon moving on the whole-sky chart (24 frames)',
 'ALLSKY':'view 7 ALLSKY: whole sky, over the horizon above, under the horizon below',
 'SDM':   'text: degrees and minutes "ddd°mm.m\'" as a string',
 'SNS':   'text: latitude with N / S',
 'SEW':   'text: longitude with E / W',
 'SZN':   'text: azimuth "ddd.d°"',
 'SHM':   'text: time "hh:mm" (--:-- when no event)',
 'SF1':   'text: number with one decimal',
 'SINT':  'text: whole number',
 'SDAT':  'text: date "dd-mm-yyyy" from a Julian Date',
 'SUNA':  'Sun: VSOP87 series (matrices VL VB VR), nutation, aberration -> GHA, Dec, GHA Aries',
 'SUNG':  'Sun GHA/Dec for the sunrise iterations (tables if loaded, else SUNF)',
 'SUNF':  'Sun, low-precision formula (0.01 deg) for sunrise/twilight',
 'SER':   'sum of one series matrix with the matrix functions (COS, DOT)',
 'SERT':  'the time vectors SV1 SV2 used by SER',
 'NUT':   'nutation in longitude and obliquity (matrix NU)',
 'STAR':  'star: SUNA, then STR2',
 'STR2':  'star GHA/Dec: catalogue ST, precession, aberration, nutation (after SUNA)',
 'SQK':   'star, quick sin(Hc) from the catalogue (to skip stars below the horizon)',
 'MOON':  'Moon: SUNA, then MOO2',
 'MOO2':  'Moon GHA, Dec, HP, SD: Meeus series (matrices ML MB MCL MCB) after SUNA',
 'MOOQ':  'Moon, quick low-precision formula (BODY list, ANIM)',
 'PLAN':  'planet: SUNA, then PLN2',
 'PLN2':  'planet GHA/Dec/SHA/HP: VSOP87 series with light-time, after SUNA',
 'PLN3':  'planet for the screens: quick position first, full series only if it can be above the horizon',
 'PLNQ':  'planet, quick position from mean elements (BODY list)',
 'CHZ':   'sight reduction with all inputs: Dec, GHA, lat, lon -> Hc, Zn',
 'HCZ':   'sight reduction: Y = Dec, X = GHA -> Hc (R96), Zn (R97), sin Hc ("SHC")',
 'HCZ0':  'sight reduction for Dec 0 (equator points)',
 'HCZQ':  'celestial equator: start of the dot-by-dot rotation',
 'HCZR':  'celestial equator: next point by rotation (no trig)',
 'HCZI':  'keeps sin/cos of the latitude for HCZ',
 'DHA':   'inverse: from Hc and Zn back to Dec and GHA (star identification)',
 'RISE':  'sunrise time UT (SUNRISE program)',
 'SET':   'sunset time UT',
 'NTWA':  'nautical twilight, morning, UT',
 'NTWP':  'nautical twilight, evening, UT',
 'CTWA':  'civil twilight, morning, UT',
 'CTWP':  'civil twilight, evening, UT',
 'TRAN':  'meridian passage of the Sun, UT',
 'PHAS':  'Moon phase: SUNA, then PHA2',
 'PHA2':  'Moon phase after SUNA: illumination % and age in days',
 'SBRT':  'star number by brightness rank (1st brightest ... 58th)',
 'SNMU':  'star name from its number',
 'TGET':  'almanac tables (TBL): Chebyshev lookup (not in NAVFULL_NOTBL)',
 'CWID':  'pixel width of a character in the PROMPT font (to align the BODY pages)',
 'PTXS':  'TEXT: ATEXT in GRFNT 21 (Didier\'s N03 trick) - Z row of the base line, Y column, X text',
 'PINS':  'TEXT: whole number (one ATEXT)',
 'PF1S':  'TEXT: number with one decimal',
 'PHMS':  'TEXT: hh:mm from hours',
 'PDMS':  'TEXT: degrees and minutes "ddd mm.m" with sign',
 'PZNS':  'TEXT: azimuth "ddd.d"',
 'PDTS':  'TEXT: date "dd-mm-yyyy" from a Julian Date',
 'PTTY':  'TEXT in the tinyFont (GRFNT 10, the charts) - Z row of the base line, Y column, X text',
 'PTNT':  'TEXT: whole number in the tinyFont',
 'PHLS':  'horizontal line (X = length in pixels)',
 'PSYB':  'SYMBOL of a body, 12 rows (glyphs47, AGRAPH; the tables, the Moon phases) - Z row, Y column, X symbol',
 'PSYS':  'SYMBOL of a body, 7 rows (glyphs47, AGRAPH; the charts) - Z row, Y column, X symbol',
}


NAVINIT_TEXT = """NAVINIT_FULL / NAVINIT_FAST - labels
=====================================
Each file is ONE program, INIT. XEQ "INIT" builds the matrices the navigation programs read,
then shows MATRICES READY. After that delete it (GTO "INIT", CLP): the matrices stay.
No font routines in these files.

NAVINIT_FULL (VSOP87 series, valid 2000-2050, about 5,700 numbers)
  INIT     runs LBL 01-04, then MATRICES READY: FULL 2000-2050
  LBL 01   (MATA)  Earth series VL VB VR (for the Sun) and the nutation series NU
  LBL 02   (MATST) star catalogue ST: 58 stars, RA, Dec, proper motion
  LBL 03   (MATM)  Moon series ML (longitude, distance) and MB (latitude) - Meeus ch. 47 -
                   and MCL MCB, extra terms fitted to JPL DE421
  LBL 04   (MATP)  planet series: Earth EEL EEB EER, Venus VN.., Mars MA.., Jupiter JU..,
                   Saturn SA.. (L, B, R each)

NAVINIT_FAST (fitted series, valid %(period)s only, about 3,100 numbers, faster)
  INIT     runs LBL 01-04, then MATRICES READY: FAST %(period)s
  LBL 01   (MATN)  nutation series NU
  LBL 02   (MATST) star catalogue ST (same as FULL)
  LBL 03   (MATM)  Moon series ML MB MCL MCB (same as FULL)
  LBL 04   (MATF)  fitted Earth and planet series VL VB VR, EEL EEB EER, VN.. MA.. JU.. SA..
                   (outside %(period)s the screens show X)

Matrix names are variables, not program labels: they keep their names in every build.
"""


def label_map(lines, keep=('NAV',)):
    """Every global label except NAV -> N01, N02 ... in the order they appear."""
    m = {}
    for l in lines:
        g = re.fullmatch(r'LBL "(.+)"', l)
        if g and g.group(1) not in keep and g.group(1) not in m:
            m[g.group(1)] = 'N%02d' % (len(m) + 1)
    return m


LABELS = os.path.join(ROOT, 'tools', 'labels')


def fixed_map(name, lines, keep=('NAV',)):
    """The short labels of one build from its fixed map tools/labels/<name>.map (one line
    'N01 SUNA' per routine). A routine not in the map yet gets the next free number and is
    added to the file; numbers are never reused, so the N.. labels stay the same from one
    version to the next. Returns {long name: short label} for the labels in lines, in order."""
    path = os.path.join(LABELS, name + '.map')
    m = {}
    if os.path.exists(path):
        for l in open(path, encoding='utf-8'):
            l = l.split('#')[0].split()
            if len(l) == 2:
                m[l[1]] = l[0]
    present = []
    for l in lines:
        g = re.fullmatch(r'LBL "(.+)"', l)
        if g and g.group(1) not in keep and g.group(1) not in present:
            present.append(g.group(1))
    new = [n for n in present if n not in m]
    top = max([int(v[1:]) for v in m.values()] or [0])
    for n in new:
        top += 1
        m[n] = 'N%02d' % top
    if new or not os.path.exists(path):
        os.makedirs(LABELS, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('# %s: fixed short labels (short label, original name in programs/ and build/.../src/).\n'
                     '# Read by the build: a new routine gets the next free number, numbers are never\n'
                     '# reused, so the labels stay the same from one version to the next.\n' % name)
            fh.write(''.join('%s %s\n' % (v, k) for k, v in sorted(m.items(), key=lambda kv: int(kv[1][1:]))))
    return {k: m[k] for k in sorted(present, key=lambda k: int(m[k][1:]))}


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')


def rename(lines, m):
    """LBL / XEQ / GTO "name" -> the N.. label (variables in STO, RCL, INDEX, INPUT stay)."""
    out = []
    for l in lines:
        g = re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l)
        if g and g.group(2) in m:
            l = '%s "%s"' % (g.group(1), m[g.group(2)])
        elif g and g.group(2) != 'NAV' and g.group(1) != 'LBL':
            raise ValueError('call to a label that is not in NAVFULL: %s' % l)
        out.append(l)
    return out


def rename_keep(lines, m, keep):
    """rename() for another program set: keep = the label(s) that keep their name."""
    keep = (keep,) if isinstance(keep, str) else tuple(keep)
    out = []
    for l in lines:
        g = re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l)
        if g and g.group(2) in m:
            l = '%s "%s"' % (g.group(1), m[g.group(2)])
        elif g and g.group(2) not in keep:
            raise ValueError('call to a label that is not in the file: %s' % l)
        out.append(l)
    return out


def closure(progs, roots):
    """Programs needed for the labels in roots (following XEQ / GTO "name")."""
    owner = {}
    for n, L in progs.items():
        for l in L:
            g = re.fullmatch(r'LBL "(.+)"', l)
            if g:
                owner[g.group(1)] = n
    need, todo = set(), list(roots)
    while todo:
        lab = todo.pop()
        n = owner.get(lab)
        if n is None or n in need:
            continue
        need.add(n)
        for l in progs[n]:
            g = re.fullmatch(r'(?:XEQ|GTO) "(.+)"', l)
            if g:
                todo.append(g.group(1))
    return need


def calls(lines):
    return [g.group(1) for l in lines for g in [re.fullmatch(r'(?:XEQ|GTO) "(.+)"', l)] if g]


def almr(lines):
    """ALMR: ALMT with every text line stored in a register (R50, R51 ...; R79 = next) instead of
    PROMPT pages: no drawing, the page is read in the register browser. Returns after one page."""
    s = '\n'.join(lines) + '\n'
    s = s.replace('LBL "ALMT"\n', 'LBL "ALMR"\n', 1)
    s = s.replace('LBL 01\n', 'LBL 01\n50\nSTO 79\n', 1)
    assert s.count('400\nXEQ 89\n0\nSTO 43\n') == 4
    s = s.replace('400\nXEQ 89\n0\nSTO 43\n', 'XEQ 91\n" "\nSTO 20\n8\nSTO 43\n')    # line 1 of a page: its own register (no "" string)
    assert s.count('LBL 91\nPROMPT 20\nRTN\n') == 1 and s.count('STO 20\nXEQ 91\nRTN\n') == 1
    s = s.replace('LBL 91\nPROMPT 20\nRTN\n', 'LBL 91\nRCL 20\nSTO IND 79\n1\nSTO+ 79\nRTN\n')
    # the register browser has no 400 px PROMPT line: no pixel widths (CWID) and no padding to
    # pixel columns - one space between the columns
    for a, b in (('LBL 87\nαLENG 44\nX=0?\nGTO 88\nα→𝑥 44\nXEQ "CWID"\nSTO+ 43\nGTO 87\n', 'LBL 87\n'),
                 ('LBL 67\nαLENG 44\nX=0?\nRTN\nα→𝑥 44\nXEQ "CWID"\nSTO+ 43\nGTO 67\n', 'LBL 67\nRTN\n'),
                 ('LBL 73\nRCL 43\n8\n+\nRCL 28\nX<Y?\nRTN\n" "\nXEQ 90\n8\nSTO+ 43\nGTO 73\n', 'LBL 73\n" "\nXEQ 90\nRTN\n')):
        assert s.count(a) == 1, a[:20]
        s = s.replace(a, b)
    assert 'CWID' not in s
    return s.rstrip('\n').split('\n')


def read21(name):
    with open(os.path.join(PROG, 'atext', 't21', name + '.txt'), encoding='utf-8') as fh:
        return [l.rstrip('\n') for l in fh if l.strip()]


def programs21(progs):
    """The programs of the C47 builds from the processed programs of build(): the views of
    programs/atext/t21/ (the sky cache swapped in, not in HANIM), PTXS and the number printers with ATEXT
    (atext_common; R49 holds the text of a number), PTTY / PTNT in the tinyFont, and the body
    symbols PSYB / PSYS (glyphs47). No AGRAPH font: PTXT is left out, PTXS gives only PHLS."""
    import gencache, navopt, glyphs47
    import atext_common as AC
    q = {n: v for n, v in progs.items() if n not in ('PTXT', 'ALMS')}
    for n in T21_VIEWS:
        q[n] = gencache.swap(read21(n)) if n in gencache.VIEWS else read21(n)      # HANIM computes its own times
    q['PTXS'] = AC.printers(navopt.pdts(navopt.phls(navopt.fonts(read('PTXS')))), '49', True, 21)
    q['PSYB'] = glyphs47.program('PSYB', glyphs47.BIG, ws=16)
    q['PSYS'] = glyphs47.program('PSYS', glyphs47.SMALL)
    return q


def top21(L):
    """The top line of a menu NAV (date, UT, DR) at the columns of the T21 header."""
    import genviews_atx as V
    V.mode(True, 't21')
    T = V.top_x()
    V.mode()
    s = '\n' + '\n'.join(map(str, L)) + '\n'
    for a, b in (((206, 80), (206, T['time'])), ((206, 116, '"UT"'), (206, T['UT'], '"UT"')),
                 ((206, 150, '"DR"'), (206, T['DR'], '"DR"')), ((206, 174), (206, T['N'])), ((206, 176), (206, T['lat'])),
                 ((206, 244), (206, T['E'])), ((206, 246), (206, T['lon']))):
        a = '\n' + '\n'.join(map(str, a)) + '\n'; b = '\n' + '\n'.join(map(str, b)) + '\n'
        assert a in s, a
        s = s.replace(a, b)
    return s.strip('\n').split('\n')


def grfnt21(L, back='LBL 08'):
    """GRFNT 21 for the whole run, after the inputs (XEQ 20), and 20 again on the way out (back:
    the label or line after which NAV ends; the menu NAV: LBL 08, used by 0 END and TEXT)."""
    L = list(L)
    k = L.index('XEQ 20') + 1
    L[k:k] = ['21', 'GRFNT', 'DROP']
    k = L.index(back) + 1
    L[k:k] = ['20', 'GRFNT', 'DROP']
    return L


def nav21(inp, items=None, autoinit=False):
    """NAV (gennav) for the T21 views: the top line of the menu, the SINKING box text centred for
    GRFNT 21, GRFNT 21 while NAV runs."""
    import gennav, genviews_atx as V
    L = top21(gennav.program(inp, items or gennav.ALL, autoinit))
    k = L.index('"%s"' % gennav.BUSY)
    V.mode(True, 't21')
    L[k - 1] = str(110 + (180 - V.width(gennav.BUSY)) // 2)
    V.mode()
    return grfnt21(L)


def build():
    progs = {n: read(n) for n in KEEP + INIT + ['NAV']}
    progs['ALMT'] = almr(progs['ALMT'])          # TEXT view: ALMR, the page into registers (no PROMPT)
    # the views read the sky from matrix ALMC (CACHE): computed once per time and place
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'generators'))
    import gencache
    progs['CACHE'] = gencache.program(True)
    import navopt                                  # faster fonts, lines, dates and number text (tools/navopt.py)
    progs['PTXS'] = navopt.pdts(navopt.phls(navopt.fonts(progs['PTXS'])))
    progs['PTXT'] = navopt.fonts(progs['PTXT'])
    progs['STXT'] = navopt.stxt(progs['STXT'])
    for n in gencache.VIEWS:
        if n in progs:
            progs[n] = gencache.swap(progs[n])
    # characters the big font must draw: every string in the screens and the star names,
    # plus what the number routines print (digits, sign, point, colon, space)
    big = set(strings(progs['NAV']) + strings(progs['ALMF']) + strings(progs['HALMV']) + strings(progs['HORZ']) + strings(progs['HALMH']) + strings(progs['SNMU']) + strings(progs['ALLSKY'])
              + '0123456789-.: %')
    # small font: warning, T/S/X, chart axis letters and altitude marks
    small = set(WARNING + 'TSX NEWZHC-.0123456789' + strings(progs['ALLSKY']))
    progs['PTXS'] = trim_font(progs['PTXS'], big)
    progs['PTXT'] = trim_font(progs['PTXT'], small)
    nav_min(progs['NAV'])
    # the C47 builds: the T21 views, ATEXT text, the glyphs47 symbols (progs keeps the AGRAPH
    # programs: build_free42 / build_dm42 start from them)
    import gennav
    inp = gennav.inputs()
    p21 = programs21(progs)
    nav = nav21(inp)
    full = nav + [l for n in KEEP21 for l in p21[n]]
    assert not {'PTXT', 'PTNS', 'PSYM'} & set(calls(full)), 'an AGRAPH font is still called'
    import json
    period = json.load(open(os.path.join(ROOT, 'python', 'native', 'fast_series.json')))['period']
    # matrix builders, compacted: NEWMAT starts with zeros, so "0 STOEL" is dropped (J+ stays)
    mata = compact(read('MATA'))
    k = mata.index('STO "NU"') - 4                    # NU (nutation) block: rows ENTER cols NEWMAT
    matn = ['LBL "MATN"'] + mata[k:]                  # NU only, for FAST (MATF builds VL VB VR)
    def init_prog(title, names, bodies, valid):
        """ONE program with one name, INIT: the matrix builders become LBL 01-04 inside it,
        so after XEQ "INIT" only INIT has to be deleted (CLP)."""
        out = (['LBL "INIT"'] + ['XEQ %02d' % (k + 1) for k in range(len(names))] + gencache.NEWMAT
               + ['"%s"' % valid, 'STO "VAL"', '"MATRICES READY: %s"' % title, 'RTN'])      # VAL: shown by the NAV menu
        for k, (n, b) in enumerate(zip(names, bodies)):
            assert b[0] == 'LBL "%s"' % n and b[-1] == 'END', n
            assert not any(l.startswith(('XEQ', 'GTO', 'LBL')) for l in b[1:]), n     # no labels or calls inside
            body = b[1:-1]
            if body and body[-1] == 'RTN':
                body = body[:-1]
            out += ['LBL %02d' % (k + 1)] + [l for l in body if l != '"FAST SERIES %s"' % period] + ['RTN']
        return out + ['END']
    init_full = init_prog('FULL 2000-2050', ['MATA', 'MATST', 'MATM', 'MATP'],
                          [mata, compact(read('MATST')), compact(read('MATM')), compact(read('MATP'))], '2000-2050')
    init_fast = init_prog('FAST ' + period, ['MATN', 'MATST', 'MATM', 'MATF'],
                          [matn, compact(read('MATST')), compact(read('MATM')), compact(read('MATF'))], period)
    init = init_full
    os.makedirs(OUT, exist_ok=True)
    old = os.path.join(OUT, 'NAVINIT.txt')
    if os.path.exists(old):
        os.remove(old)
    nt = no_tables(p21)
    notbl = nav + [l for n in KEEP21 if n != 'TGET' for l in nt[n]]
    # build/        the files to load (short N01... labels from tools/labels/*.map)
    # build/dev/    other builds, also with short labels
    # build/dev/src/  every build with the original names (development, tests)
    dev = os.path.join(OUT, 'dev')
    src = os.path.join(dev, 'src')
    for name, L in (('NAVFULL', full), ('NAVFULL_NOTBL', notbl)):
        write(os.path.join(src, name + '.txt'), L)
    mapping = fixed_map('NAVFULL', full)
    with open(os.path.join(OUT, 'NAVFULL_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVFULL / NAVFULL_NOTBL - program labels\n'
                 '==========================================\n'
                 'Label on the calculator, original name (sources, build/dev/, documentation), what it does.\n'
                 'Only NAV keeps its name. TEXT = a text routine (ATEXT, GRFNT 21 or the tinyFont), SYMBOL =\n'
                 'a body symbol drawn with AGRAPH (glyphs47): Z = row of the base line (0 = bottom), Y = column,\n'
                 'X = text, number or symbol; returns Y = row, X = next column. Needs a C47 firmware with\n'
                 'ATEXT and GRFNT. The numbers missing here belong to routines of older versions.\n\n')
        fh.write('NAV     NAV     %s\n' % LABEL_TEXT['NAV'])
        fh.write('\n'.join('%s     %-7s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in mapping.items()) + '\n')
        fh.write('\nNAVFULL_NOTBL (build/dev/) has no TGET; its labels are the same (%s is simply missing there).\n' % mapping['TGET'])
    with open(os.path.join(OUT, 'NAVINIT_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write(NAVINIT_TEXT % {'period': period})
    for path, L in ((os.path.join(OUT, 'NAVFULL.txt'), rename(full, mapping)),
                    (os.path.join(dev, 'NAVFULL_NOTBL.txt'), rename(notbl, mapping)),
                    (os.path.join(OUT, 'NAVINIT_FULL.txt'), init_full), (os.path.join(OUT, 'NAVINIT_FAST.txt'), init_fast)):
        write(path, L)
    tables(dev)
    # ---- NAV + INIT in one file (the first NAV builds the matrices and deletes INIT), no tables:
    #      NAVALL_FAST (all views) and NAVCOMP_FAST (compact: 1 ALMANAC 2 CHART 4 SKY 9 ALLSKY)
    nav_all = nav21(inp, autoinit=True)
    nav_comp = nav21(inp, gennav.COMPACT, autoinit=True)
    need = closure(nt, [c for c in calls(nav_comp) if c != 'INIT'])
    comp = nav_comp + [l for n in KEEP21 if n in need and n != 'TGET' for l in nt[n]]
    allf = nav_all + [l for n in KEEP21 if n != 'TGET' for l in nt[n]]
    extra = {}
    # NAV + programs in one file, INIT in its own (NAVINIT_FAST or NAVINIT_FULL): one file of
    # 15-19 thousand lines gave "invalid data" in rejig. NAV runs INIT once and deletes it.
    for name, L in (('NAVALL', allf), ('NAVCOMP', comp)):
        write(os.path.join(src, name + '.txt'), L)
        m = fixed_map(name, L, keep=('NAV', 'INIT'))
        write(os.path.join(dev, name + '.txt'), rename_keep(L, m, ('NAV', 'INIT')))
        with open(os.path.join(dev, name + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; load NAVINIT_FAST or NAVINIT_FULL too:\n'
                     'the first NAV runs INIT, flag 81 remembers it; then delete INIT by hand; CF 81 before loading INIT again)\n\n' % name)
            fh.write('NAV     NAV     %s\nINIT    INIT    (NAVINIT file) builds the matrices; run by the first NAV, then delete it\n' % LABEL_TEXT['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
        extra[name] = (L, sorted(need) if 'COMP' in name else None)
    # ---- text only (no drawing): NAV asks the position, ALMR writes the page into R50 ... ;
    #      then lines 1-26 also go to the stack and the lettered registers (REGS shows them in
    #      order from X). NAVTXT_FAST = NAV + the programs ALMR needs + INIT.
    #      NAVTXT reads the almanac tables too (TGET): after XEQ "TBL" (flag 10), inside the table
    #      period, the Sun, the Moon and the planets come from the tables, else from the series.
    ntt = dict(progs) if TXT_TABLES else dict(nt)
    navtxt = ['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04',
              ] + gencache.NEWMAT + ['0', 'STO "DH"', 'XEQ 20'] + gennav.text_steps(5)
    navtxt += ['REGS', 'RTN'] + inp + ['END']                         # open the register browser
    needt = closure(ntt, ['ALMR'])
    txt = navtxt + [l for n in KEEP if n in needt for l in ntt[n]]
    L = txt
    write(os.path.join(src, 'NAVTXT.txt'), L)
    m = fixed_map('NAVTXT', L, keep=('NAV', 'INIT'))
    write(os.path.join(OUT, 'NAVTXT.txt'), rename_keep(L, m, ('NAV', 'INIT')))
    with open(os.path.join(OUT, 'NAVTXT_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVTXT - program labels (NAV keeps its name; load NAVINIT_FAST or NAVINIT_FULL too:\n'
                 'the first NAV runs INIT, flag 81 remembers it; then delete INIT by hand; CF 81 before loading INIT again).\n'
                 'With TBL run (flag 10) and the date inside the table period, the page comes from the tables.\n\n')
        fh.write('NAV     NAV     text only: asks DATE UTC LAT LON, the almanac page into R50 ..., the stack and the\n'
                 '                lettered registers, then REGS\nINIT    INIT    (NAVINIT file) builds the matrices; run by the first NAV, then delete it\n')
        fh.write('\n'.join('%s     %-7s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
    extra['NAVTXT'] = (L, sorted(needt))
    return full, init_full, init_fast, progs, nav, notbl, extra, p21


# the almanac tables: TBL_1 (1 year) and TBL_5 (5 years) from the JPL coefficients in
# tools/almanac/ (c47_almanac_generator.py); build/dev/TBL_4M = programs/TBL.txt (the tests)
TABLES_CSV = os.path.join(ROOT, 'tools', 'almanac', 'tables_2026-10_2031-09.csv')
TABLES = (('TBL_1', '2026-10-01', '2027-09-30'), ('TBL_5', '2026-10-01', '2031-09-30'))


def tables(dev):
    import datetime, io, contextlib
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'almanac'))
    import tab2c47
    shutil.copy(os.path.join(PROG, 'TBL.txt'), os.path.join(dev, 'TBL_4M.txt'))
    if os.path.exists(os.path.join(OUT, 'TBL.txt')):
        os.remove(os.path.join(OUT, 'TBL.txt'))
    if not os.path.exists(TABLES_CSV):
        return
    t = tab2c47.read_csv(TABLES_CSV)
    for name, a, b in TABLES:
        with contextlib.redirect_stderr(io.StringIO()):
            L = tab2c47.program(t, datetime.date.fromisoformat(a), datetime.date.fromisoformat(b), 'TBL')
        write(os.path.join(OUT, name + '.txt'), L)


def size(lines):
    return len(lines), len('\n'.join(lines).encode('utf-8'))


if __name__ == '__main__':
    full, init, init_fast, progs, nav, notbl, extra, p21 = build()
    print('%-9s %7s %8s' % ('program', 'lines', 'bytes'))
    for n in ['NAV'] + KEEP21:
        print('%-9s %7d %8d' % ((n,) + size(nav if n == 'NAV' else p21[n])))
    print('%-9s %7d %8d   <- stays on the calculator' % (('NAVFULL',) + size(full)))
    print('%-13s %7d %8d   <- or this one: the same without the tables (TBL/TGET)' % (('NAVFULL_NOTBL',) + size(notbl)))
    print('%-12s %7d %8d   <- FULL: load, XEQ INIT, delete' % (('NAVINIT_FULL',) + size(init)))
    print('%-12s %7d %8d   <- FAST: load, XEQ INIT, delete' % (('NAVINIT_FAST',) + size(init_fast)))
    for n, (L, need) in extra.items():
        print('%-13s %7d %8d   <- + NAVINIT_FAST (NAV runs INIT once)%s' % ((n,) + size(L) + (': ' + ' '.join(need) if need else '',)))
    print('written to', OUT)
