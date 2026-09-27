#!/usr/bin/env python3
"""build_navfull.py - the smallest set of C47 programs for the almanac screens.

Writes three plain-text files (convert each with: rejig FILE.txt -o FILE.p47):

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
  NAVINIT_FULL.txt  MATA MATST MATM MATP + INIT (VSOP87, 2000-2050)
  NAVINIT_FAST.txt  MATN MATST MATM MATF + INIT (fitted series for a few years: faster,
               smaller). Load ONE of them, XEQ "INIT" once, then delete the programs -
               the matrices they build stay. Zero elements are not stored (NEWMAT
               starts with zeros).
  TBL.txt      (copied) almanac tables: load, XEQ "TBL" once, then delete

Menu NAV: 1 ALMANAC (ALMF), 2 CHART (HALMV), 3 TEXT (ALMT, one page per R/S),
4 SKY (HORZ, info line per body without end), 5 SMALL (ALMS: Sun, Moon, 1 planet,
3 stars), 6 SPLIT (HALMH: chart on top, the same short table below), 7 BODY (one body:
list above the horizon, key its number, text pages, then the chart).
Not included: HORZS, HPLT, HALM, ALM (manual table method), SNAM, SUNSD and
the font demos.

  python3 tools/build_navfull.py            -> build/NAVFULL.txt, NAVFULL_NOTBL.txt, NAVINIT_FULL.txt, NAVINIT_FAST.txt, TBL.txt
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(ROOT, 'programs')
OUT = os.path.join(ROOT, 'build')

KEEP = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'ALMS', 'HALMH', 'BODY', 'STXT', 'SUNA', 'STAR', 'MOON', 'PLAN', 'CHZ', 'SUNRISE', 'PHAS',
        'SBRT', 'SNMU', 'TGET', 'CWID', 'PTXS', 'PTXT']
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
    """NAV menu: 1 ALMANAC (ALMF), 2 CHART (HALMV), 3 TEXT (ALMT), 4 SKY (HORZ),
    5 SMALL (ALMS), 6 SPLIT (HALMH), 7 BODY (one body)."""
    s = '\n'.join(lines)
    s = s.replace('"1 ALMANAC 2 HORIZON 3 INIT 4 TEXT 5 SKY 6 SMALL 7 SPLIT 8 BODY 0 END"',
                  '"1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SMALL 6 SPLIT 7 BODY 0 END"')
    s = s.replace('3\nRCL 38\nX=Y?\nGTO 12\n4\nRCL 38\nX=Y?\nGTO 13\n5\nRCL 38\nX=Y?\nGTO 14\n'
                  '6\nRCL 38\nX=Y?\nGTO 15\n7\nRCL 38\nX=Y?\nGTO 16\n8\nRCL 38\nX=Y?\nGTO 17\n',
                  '3\nRCL 38\nX=Y?\nGTO 13\n4\nRCL 38\nX=Y?\nGTO 14\n'
                  '5\nRCL 38\nX=Y?\nGTO 15\n6\nRCL 38\nX=Y?\nGTO 16\n7\nRCL 38\nX=Y?\nGTO 17\n')
    s = re.sub(r'LBL 12\n.*?GTO 01\n', '', s, flags=re.S)
    assert 'MATA' not in s and 'XEQ "ALMT"' in s and 'GTO 17' in s and '"1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SMALL 6 SPLIT 7 BODY 0 END"' in s
    return s.split('\n')


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


def build():
    progs = {n: read(n) for n in KEEP + INIT + ['NAV']}
    # characters the big font must draw: every string in the screens and the star names,
    # plus what the number routines print (digits, sign, point, colon, space)
    big = set(strings(progs['ALMF']) + strings(progs['HALMV']) + strings(progs['HORZ']) + strings(progs['HALMH']) + strings(progs['BODY']) + strings(progs['SNMU'])
              + '0123456789-.: %')
    # small font: warning, T/S/X, chart axis letters and altitude marks
    small = set(WARNING + 'TSX NEWZHC-.0123456789')
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
    def init_prog(title, names, bodies):
        return (['LBL "INIT"'] + ['XEQ "%s"' % n for n in names] + ['"MATRICES READY: %s"' % title, 'RTN', 'END']
                + [l for b in bodies for l in b])
    init_full = init_prog('FULL 2000-2050', ['MATA', 'MATST', 'MATM', 'MATP'],
                          [mata, compact(read('MATST')), compact(read('MATM')), compact(read('MATP'))])
    init_fast = init_prog('FAST ' + period, ['MATN', 'MATST', 'MATM', 'MATF'],
                          [matn, compact(read('MATST')), compact(read('MATM')), compact(read('MATF'))])
    init = init_full
    os.makedirs(OUT, exist_ok=True)
    old = os.path.join(OUT, 'NAVINIT.txt')
    if os.path.exists(old):
        os.remove(old)
    nt = no_tables(progs)
    notbl = nav + [l for n in KEEP if n != 'TGET' for l in nt[n]]
    for name, L in (('NAVFULL', full), ('NAVFULL_NOTBL', notbl), ('NAVINIT_FULL', init_full), ('NAVINIT_FAST', init_fast)):
        with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
    shutil.copy(os.path.join(PROG, 'TBL.txt'), os.path.join(OUT, 'TBL.txt'))
    return full, init_full, init_fast, progs, nav, notbl


def size(lines):
    return len(lines), len('\n'.join(lines).encode('utf-8'))


if __name__ == '__main__':
    full, init, init_fast, progs, nav, notbl = build()
    print('%-9s %7s %8s' % ('program', 'lines', 'bytes'))
    for n in ['NAV'] + KEEP:
        print('%-9s %7d %8d' % ((n,) + size(nav if n == 'NAV' else progs[n])))
    print('%-9s %7d %8d   <- stays on the calculator' % (('NAVFULL',) + size(full)))
    print('%-13s %7d %8d   <- or this one: the same without the tables (TBL/TGET)' % (('NAVFULL_NOTBL',) + size(notbl)))
    print('%-12s %7d %8d   <- FULL: load, XEQ INIT, delete' % (('NAVINIT_FULL',) + size(init)))
    print('%-12s %7d %8d   <- FAST: load, XEQ INIT, delete' % (('NAVINIT_FAST',) + size(init_fast)))
    print('written to', OUT)
