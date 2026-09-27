#!/usr/bin/env python3
"""build_navfull.py - the smallest set of C47 programs for the almanac screens.

Writes three plain-text files (convert each with: rejig FILE.txt -o FILE.p47):

  NAVFULL.txt  everything that must stay on the calculator for ALMF, HALMV, ALMT and HORZ
               (menu NAV, the three screens, the text almanac, Sun, stars, Moon, planets, sight
               reduction, sunrise/twilight, Moon phase, star order and names,
               the table lookup TGET and the two fonts, cut down to the
               characters the screens really print)
  NAVINIT.txt  MATA, MATST, MATM, MATP and INIT: load, XEQ "INIT" once, then
               delete these programs - the matrices they build stay
  TBL.txt      (copied) almanac tables: load, XEQ "TBL" once, then delete

Menu NAV: 1 ALMANAC (ALMF), 2 CHART (HALMV), 3 TEXT (ALMT, one page per R/S),
4 SKY (HORZ, info line per body without end), 5 SMALL (ALMS: Sun, Moon, 1 planet,
3 stars), 6 SPLIT (HALMH: chart on top, the same short table below).
Not included: HORZS, HPLT, HALM, ALM (manual table method), SNAM, SUNSD and
the font demos.

  python3 tools/build_navfull.py            -> build/NAVFULL.txt, build/NAVINIT.txt, build/TBL.txt
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROG = os.path.join(ROOT, 'programs')
OUT = os.path.join(ROOT, 'build')

KEEP = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'ALMS', 'HALMH', 'STXT', 'SUNA', 'STAR', 'MOON', 'PLAN', 'CHZ', 'SUNRISE', 'PHAS',
        'SBRT', 'SNMU', 'TGET', 'CWID', 'PTXB', 'PTXT']
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
    5 SMALL (ALMS), 6 SPLIT (HALMH)."""
    s = '\n'.join(lines)
    s = s.replace('"1 ALMANAC 2 HORIZON 3 INIT 4 TEXT 5 SKY 6 SMALL 7 SPLIT 0 END"',
                  '"1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SMALL 6 SPLIT 0 END"')
    s = s.replace('3\nRCL 38\nX=Y?\nGTO 12\n4\nRCL 38\nX=Y?\nGTO 13\n5\nRCL 38\nX=Y?\nGTO 14\n'
                  '6\nRCL 38\nX=Y?\nGTO 15\n7\nRCL 38\nX=Y?\nGTO 16\n',
                  '3\nRCL 38\nX=Y?\nGTO 13\n4\nRCL 38\nX=Y?\nGTO 14\n'
                  '5\nRCL 38\nX=Y?\nGTO 15\n6\nRCL 38\nX=Y?\nGTO 16\n')
    s = re.sub(r'LBL 12\n.*?GTO 01\n', '', s, flags=re.S)
    assert 'MATA' not in s and 'XEQ "ALMT"' in s and 'GTO 16' in s and '"1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SMALL 6 SPLIT 0 END"' in s
    return s.split('\n')


def build():
    progs = {n: read(n) for n in KEEP + INIT + ['NAV']}
    # characters the big font must draw: every string in the screens and the star names,
    # plus what the number routines print (digits, sign, point, colon, space)
    big = set(strings(progs['ALMF']) + strings(progs['HALMV']) + strings(progs['HORZ']) + strings(progs['HALMH']) + strings(progs['SNMU'])
              + '0123456789-.: %')
    # small font: warning, T/S, and HORZ (axis letters, info line: names, numbers, - .)
    small = set(WARNING + 'TS NEWZHC-.0123456789' + strings(progs['HORZ']) + strings(progs['HALMH']) + strings(progs['SNMU']))
    progs['PTXB'] = trim_font(progs['PTXB'], big)
    progs['PTXT'] = trim_font(progs['PTXT'], small)
    nav = nav_min(progs['NAV'])
    full = nav + [l for n in KEEP for l in progs[n]]
    init = (['LBL "INIT"'] + ['XEQ "%s"' % n for n in INIT] + ['"MATRICES READY"', 'RTN', 'END']
            + [l for n in INIT for l in read(n)])
    os.makedirs(OUT, exist_ok=True)
    for name, L in (('NAVFULL', full), ('NAVINIT', init)):
        with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
    shutil.copy(os.path.join(PROG, 'TBL.txt'), os.path.join(OUT, 'TBL.txt'))
    return full, init, progs, nav


def size(lines):
    return len(lines), len('\n'.join(lines).encode('utf-8'))


if __name__ == '__main__':
    full, init, progs, nav = build()
    print('%-9s %7s %8s' % ('program', 'lines', 'bytes'))
    for n in ['NAV'] + KEEP:
        print('%-9s %7d %8d' % ((n,) + size(nav if n == 'NAV' else progs[n])))
    print('%-9s %7d %8d   <- stays on the calculator' % (('NAVFULL',) + size(full)))
    print('%-9s %7d %8d   <- load, XEQ INIT, delete' % (('NAVINIT',) + size(init)))
    print('written to', OUT)
