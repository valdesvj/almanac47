#!/usr/bin/env python3
"""build_navfull.py - the smallest set of C47 programs for the almanac screens.

Writes three plain-text files (convert each with: rejig FILE.txt -o FILE.p47):

  Program labels: only NAV keeps its name; every other label is N01, N02 ... on the calculator
  (build/NAVFULL_LABELS.txt lists them; build/dev/ has the named versions used by the tests).
  NAVFULL.txt  everything that must stay on the calculator for ALMF, HALMV, ALMT and HORZ
               (menu NAV, the three screens, the text almanac, Sun, stars, Moon, planets, sight
               reduction, sunrise/twilight, Moon phase, star order and names,
               the table lookup TGET and the two fonts, cut down to the
               characters the screens really print: PTXS, the C47 status-bar
               font, for text, numbers and the bodies; PTXT, the small font, for the
               warning and the chart axes)
  NAVFULL_NOTBL.txt  the same without the almanac tables: no TGET, no table hooks in
               SUNA/MOON/PLAN/BODY, no "T" letter (the "X" letter stays). Use it when
               memory is short and you do not load TBL. Load NAVFULL OR NAVFULL_NOTBL.
  NAVINIT_FULL.txt  one program INIT: builds the matrices of MATA MATST MATM MATP (VSOP87,
               2000-2050) - the builders are LBL 01-04 inside INIT
  NAVINIT_FAST.txt  one program INIT: MATN MATST MATM MATF (fitted series for a few years:
               faster, smaller). Load ONE of them, XEQ "INIT" once, then delete INIT
               (GTO "INIT", CLP) - the matrices it built stay. Zero elements are not stored (NEWMAT
               starts with zeros).
  TBL.txt      (copied) almanac tables: load, XEQ "TBL" once, then delete

Menu NAV (graphic, KEY?: key the number; every view waits for + to come back):
1 ALMANAC (ALMF), 2 CHART (HALMV), 3 TEXT (ALMT, one page per R/S),
4 SKY (HORZ, info line per body without end), 5 SMALL (ALMS: Sun, Moon, 1 planet,
3 stars), 6 SPLIT (HALMH: chart on top, the same short table below), 7 BODY (one body:
list above the horizon, key its number, text pages, then the chart), 8 ANIM (HANIM:
the Sun and the Moon moving on the horizon chart, 24 frames 0.5 h apart, 1 s each),
9 ALLSKY (the whole sky: horizon across the middle, over / under the horizon).
Not included: HORZS, HPLT, HALM, ALM (manual table method), SNAM, SUNSD and
the font demos.

  python3 tools/build_navfull.py            -> build/NAVFULL.txt, NAVFULL_NOTBL.txt, NAVINIT_FULL.txt, NAVINIT_FAST.txt, TBL.txt
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(ROOT, 'programs')
OUT = os.path.join(ROOT, 'build')

KEEP = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'ALMS', 'HALMH', 'BODY', 'STXT', 'SUNA', 'STAR', 'MOON', 'PLAN', 'CHZ', 'SUNRISE', 'PHAS',
        'SBRT', 'SNMU', 'TGET', 'CWID', 'PTXS', 'PTXT', 'HANIM', 'ALLSKY', 'WPLS', 'CACHE']
INIT = ['MATA', 'MATST', 'MATM', 'MATP']
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'


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
    p['BODY'] = cut(p['BODY'], 'FC? 10\nGTO 15\nRCL 10\n6\nXEQ "TGET"\nX≥0?\nXEQ 59\n')
    p['BODY'] = cut(p['BODY'], 'LBL 59\n"T"\nSTO 25\nRTN\n')
    # screens: "T" letter (FS? 11 XEQ 29, LBL 29 "T" ...)
    for n in ('ALMF', 'ALMS', 'ALMT', 'HALMV', 'HALMH', 'HORZ'):
        p[n] = cut(p[n], 'FS? 11\nXEQ 29\n')
        p[n] = re.sub(r'LBL 29\n"T"\n(STO \d+\n)?RTN\n', '', p[n], count=1)
    s = ''.join(p.values())
    for bad in ('TGET', 'FS? 10', 'FC? 10', 'FS? 11', 'SF 11', 'CF 11'):
        assert bad not in s, 'no-tables: %s left' % bad
    return {n: v.rstrip('\n').split('\n') for n, v in p.items()}


LABEL_OPS = ('LBL', 'XEQ', 'GTO')

# what every program label does (NAVFULL_LABELS.txt); FONT = text-drawing routine
LABEL_TEXT = {
 'NAV':   'graphic menu (KEY?): key 1-9, asks DATE UTC LAT LON, runs the view; 0 ends (the only named program)',
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
 'HALMV': 'view 2 CHART: horizon chart left, Hc/Zn of 10 bodies right',
 'ALMR':  'view 3 TEXT: the almanac page as text in R50-R76 (and the stack and lettered registers); NAV ends in REGS',
 'HORZ':  'view 4 SKY: horizon chart, info line per body every 3 s (+ back to the menu, arrows one hour)',
 'ALMS':  'view 5 SMALL: short almanac (Sun, Moon, 1 planet, 3 stars)',
 'HALMH': 'view 6 SPLIT: horizon chart on top, short almanac below',
 'BODY':  'view 7 BODY: list above the horizon, pick one body, its pages and chart',
 'HANIM': 'view 8 ANIM: the Sun and the Moon moving on the whole-sky chart (24 frames)',
 'ALLSKY':'view 9 ALLSKY: whole sky, over the horizon above, under the horizon below',
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
 'PTXS':  'FONT big (C47 status-bar font, 12 px, AGRAPH): draw a string - Z row, Y column, X text',
 'PINS':  'FONT big: whole number',
 'PF1S':  'FONT big: number with one decimal',
 'PHMS':  'FONT big: hh:mm from hours',
 'PDMS':  'FONT big: degrees and minutes "ddd mm.m" with sign',
 'PZNS':  'FONT big: azimuth "ddd.d"',
 'PDTS':  'FONT big: date "dd-mm-yyyy" from a Julian Date',
 'PHLS':  'FONT big: horizontal line (X = length in pixels)',
 'PTXT':  'FONT small (3x5, AGRAPH): draw a string - Z row, Y column, X text',
 'PTNS':  'FONT small: whole number',
 'PT1':   'FONT small: number with one decimal',
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
        progs[n] = gencache.swap(progs[n])
    # characters the big font must draw: every string in the screens and the star names,
    # plus what the number routines print (digits, sign, point, colon, space)
    big = set(strings(progs['NAV']) + strings(progs['ALMF']) + strings(progs['HALMV']) + strings(progs['HORZ']) + strings(progs['HALMH']) + strings(progs['BODY']) + strings(progs['SNMU']) + strings(progs['ALLSKY'])
              + '0123456789-.: %')
    # small font: warning, T/S/X, chart axis letters and altitude marks
    small = set(WARNING + 'TSX NEWZHC-.0123456789' + strings(progs['ALLSKY']))
    progs['PTXS'] = trim_font(progs['PTXS'], big)
    progs['PTXT'] = trim_font(progs['PTXT'], small)
    nav = nav_min(progs['NAV'])
    full = nav + [l for n in KEEP for l in progs[n]]
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
    nt = no_tables(progs)
    notbl = nav + [l for n in KEEP if n != 'TGET' for l in nt[n]]
    # named versions (development, tests) in build/dev/; the files to load get N01... labels
    dev = os.path.join(OUT, 'dev')
    os.makedirs(dev, exist_ok=True)
    for name, L in (('NAVFULL', full), ('NAVFULL_NOTBL', notbl)):
        with open(os.path.join(dev, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
    mapping = label_map(full)
    with open(os.path.join(OUT, 'NAVFULL_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVFULL / NAVFULL_NOTBL - program labels\n'
                 '==========================================\n'
                 'Label on the calculator, original name (sources, build/dev/, documentation), what it does.\n'
                 'Only NAV keeps its name. FONT = a text-drawing routine (draws on the graphics screen with\n'
                 'AGRAPH, one call per glyph column): Z = row of the base line (0 = bottom), Y = column,\n'
                 'X = text or number; returns Y = row, X = next column. PTXS is the C47 status-bar font\n'
                 '(bold capitals 12 px, glyphs from the firmware, GPL-3.0), PTXT a small 3x5 font.\n\n')
        fh.write('NAV     NAV     %s\n' % LABEL_TEXT['NAV'])
        fh.write('\n'.join('%s     %-7s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in mapping.items()) + '\n')
        fh.write('\nNAVFULL_NOTBL has no TGET; its labels are the same (N50 is simply missing there).\n')
    with open(os.path.join(OUT, 'NAVINIT_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write(NAVINIT_TEXT % {'period': period})
    for name, L in (('NAVFULL', rename(full, mapping)), ('NAVFULL_NOTBL', rename(notbl, mapping)),
                    ('NAVINIT_FULL', init_full), ('NAVINIT_FAST', init_fast)):
        with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
    shutil.copy(os.path.join(PROG, 'TBL.txt'), os.path.join(OUT, 'TBL.txt'))
    # ---- NAV + INIT in one file (the first NAV builds the matrices and deletes INIT), no tables:
    #      NAVALL_FAST (all views) and NAVCOMP_FAST (compact: 1 ALMANAC 2 CHART 4 SKY 9 ALLSKY)
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'generators'))
    import gennav
    inp = gennav.inputs()
    nav_all = gennav.program(inp, autoinit=True)
    nav_comp = gennav.program(inp, gennav.COMPACT, autoinit=True)
    need = closure(nt, [c for c in calls(nav_comp) if c != 'INIT'])
    raw = {n: read(n) for n in need}
    bigc = set(strings(nav_comp) + ''.join(strings(raw[n]) for n in need if n not in ('PTXS', 'PTXT')) + '0123456789-.: %')
    smallc = set(WARNING + 'TSX NEWZHC-.0123456789' + (strings(raw['ALLSKY']) if 'ALLSKY' in raw else ''))
    ntc = dict(nt)
    ntc['PTXS'] = trim_font(navopt.pdts(navopt.phls(navopt.fonts(read('PTXS')))), bigc)
    ntc['PTXT'] = trim_font(navopt.fonts(read('PTXT')), smallc)
    comp = nav_comp + [l for n in KEEP if n in need and n != 'TGET' for l in ntc[n]]
    allf = nav_all + [l for n in KEEP if n != 'TGET' for l in nt[n]]
    extra = {}
    # NAV + programs in one file, INIT in its own (NAVINIT_FAST or NAVINIT_FULL): one file of
    # 15-19 thousand lines gave "invalid data" in rejig. NAV runs INIT once and deletes it.
    for f in ('NAVALL_FAST', 'NAVCOMP_FAST', 'NAVTXT_FAST'):
        for suf in ('.txt', '_LABELS.txt'):
            for d in (OUT, dev):
                if os.path.exists(os.path.join(d, f + suf)):
                    os.remove(os.path.join(d, f + suf))
    for name, L in (('NAVALL', allf), ('NAVCOMP', comp)):
        with open(os.path.join(dev, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
        m = label_map(L, keep=('NAV', 'INIT'))
        out = rename_keep(L, m, ('NAV', 'INIT'))
        with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(out) + '\n')
        with open(os.path.join(OUT, name + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; load NAVINIT_FAST or NAVINIT_FULL too:\n'
                     'the first NAV runs INIT, flag 81 remembers it; then delete INIT by hand; CF 81 before loading INIT again)\n\n' % name)
            fh.write('NAV     NAV     %s\nINIT    INIT    (NAVINIT file) builds the matrices; run by the first NAV, then delete it\n' % LABEL_TEXT['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
        extra[name] = (L, sorted(need) if 'COMP' in name else None)
    # ---- text only (no drawing): NAV asks the position, ALMR writes the page into R50 ... ;
    #      then lines 1-26 also go to the stack and the lettered registers (REGS shows them in
    #      order from X). NAVTXT_FAST = NAV + the programs ALMR needs + INIT.
    ntt = dict(nt)
    navtxt = ['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04',
              ] + gencache.NEWMAT + ['0', 'STO "DH"', 'XEQ 20'] + gennav.text_steps(5)
    navtxt += ['REGS', 'RTN'] + inp + ['END']                         # open the register browser
    needt = closure(ntt, ['ALMR'])
    txt = navtxt + [l for n in KEEP if n in needt for l in ntt[n]]
    L = txt
    with open(os.path.join(dev, 'NAVTXT.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    m = label_map(L, keep=('NAV', 'INIT'))
    with open(os.path.join(OUT, 'NAVTXT.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(rename_keep(L, m, ('NAV', 'INIT'))) + '\n')
    extra['NAVTXT'] = (L, sorted(needt))
    return full, init_full, init_fast, progs, nav, notbl, extra


def size(lines):
    return len(lines), len('\n'.join(lines).encode('utf-8'))


if __name__ == '__main__':
    full, init, init_fast, progs, nav, notbl, extra = build()
    print('%-9s %7s %8s' % ('program', 'lines', 'bytes'))
    for n in ['NAV'] + KEEP:
        print('%-9s %7d %8d' % ((n,) + size(nav if n == 'NAV' else progs[n])))
    print('%-9s %7d %8d   <- stays on the calculator' % (('NAVFULL',) + size(full)))
    print('%-13s %7d %8d   <- or this one: the same without the tables (TBL/TGET)' % (('NAVFULL_NOTBL',) + size(notbl)))
    print('%-12s %7d %8d   <- FULL: load, XEQ INIT, delete' % (('NAVINIT_FULL',) + size(init)))
    print('%-12s %7d %8d   <- FAST: load, XEQ INIT, delete' % (('NAVINIT_FAST',) + size(init_fast)))
    for n, (L, need) in extra.items():
        print('%-13s %7d %8d   <- + NAVINIT_FAST (NAV runs INIT once)%s' % ((n,) + size(L) + (': ' + ' '.join(need) if need else '',)))
    print('written to', OUT)
