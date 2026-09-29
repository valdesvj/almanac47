#!/usr/bin/env python3
"""build_dm42.py - BETA builds for the C47 on the DM42 (64 KiB of program and matrix memory).

The DM42 has a quarter of the DM42n / R47 memory, too little for the Moon and planet series.
These builds keep the Sun (FULL series, valid 2000-2050) and the 58 navigation stars:

  NAVTXT_DM42     text only: NAV asks DATE UTC LAT LON, the almanac page goes into the
                  registers (R50 ..., stack and lettered registers) and NAV ends in REGS
  NAV1_DM42       no menu: the ALMANAC view straight after the inputs; up / down one hour
                  (the SINKING box while it computes), + ends; no ants
  NAVINIT_DM42    INIT: the Sun series (VL VB VR), nutation (NU) and the stars (ST)

What is left out: MOON, PLAN and PHAS (no Moon, no planets, no Moon phase), the Moon lines of
the pages, the tables (TBL), the ants, and the sky cache (CACHE, ALMC): with one view the
views call the Sun and star routines directly again (nav1_programs). NAV12 (menu 1 2 3 9,
cache with the Moon and planets marked below the horizon) is still in the script but not
written: about 72 KB as a .p47 file, too big for the DM42.

Load INIT first on its own: XEQ "INIT", delete it (GTO "INIT", CLP), then load NAV.
(If INIT is still there, the first NAV runs it: flag 81.)

  python3 tools/build_dm42.py      -> build/dm42/*.txt (+ build/dm42/dev/ with the original names)
"""
import os, sys, re, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators')]
import build_navfull as B
import gencache, gennav, navopt

OUT = os.path.join(ROOT, 'build', 'dm42')
DEV = os.path.join(OUT, 'dev')
NOTE = 'NO MOON - NO PLANETS - DM42 BETA'
VALID = '2000-2050'
ALMC = [str(gencache.ROWS), 'ENTER', '4', 'NEWMAT', 'STO "ALMC"', '1', 'STO "KR"']
ALMQ = ['120', 'ENTER', '3', 'NEWMAT', 'STO "ALMQ"', '999', 'STO "KQA3"', 'STO "KQA2"']


def seq(L, part, new, start=0):
    """Replace the exact run of lines part (first found from start) by new."""
    for i in range(start, len(L) - len(part) + 1):
        if L[i:i + len(part)] == part:
            return L[:i] + new + L[i + len(part):]
    raise ValueError('not found: %s' % part[:6])


def cache_lite():
    """CACHE without the Moon, the planets and the Moon phase: their rows get Hc -99."""
    C = gencache.program(False)
    C = seq(C, ['XEQ "PHA2"', 'STO "KD"', 'X<>Y', 'STO "KE"'] + gencache.put(66, 1, ['"KD"', '"KE"']), [])
    moon = (['XEQ "MOO2"', 'STO "KA"', 'R↓', 'STO "KB"', 'R↓', 'STO "KC"', 'R↓', 'STO "KD"',
             'RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"'] + gencache.put(2, 1, ['"KA"', '"KB"', '96', '97'])
            + gencache.put(65, 2, ['"KC"', '"KD"', '"KF"']))
    below = []
    for r in range(2, 7):                                   # 2 Moon, 3-6 planets: below the horizon
        below += gencache.at(r, 3) + ['-99', 'STOEL']
    C = seq(C, moon, gencache.put(65, 4, ['"KF"']) + below)
    planets = (['1', 'STO 82', 'LBL 01', 'RCL 82', 'XEQ "PLN3"'] + gencache.row(2)
               + ['1', 'STO+ 82', '4', 'RCL 82', 'X≤Y?', 'GTO 01'])
    C = seq(C, planets, [])
    assert not any(c in C for c in ('XEQ "MOO2"', 'XEQ "PLN3"', 'XEQ "PHA2"'))
    return C


def cut(L, first, last, new=()):
    """Lines from first (included) to last (excluded) replaced by new."""
    i = L.index(first)
    j = L.index(last, i)
    return L[:i] + list(new) + L[j:]


def no_ants(P):
    P = seq(P, ['LBL 48', str(gennav.ANTS), 'FS? 47', str(gennav.ANTS_FLAG), 'STO 49', 'XEQ 52', 'RCL 49', 'X=0?', 'RTN',
                'LBL 46', 'XEQ 47', 'PAUSE 1', 'DSE 49', 'GTO 46', 'RTN'], ['LBL 48', 'GTO 52'])
    i, j = P.index('LBL 47'), P.index('LBL 28')             # LBL 47 ant, 42 its drawing, 50 / 51 XOR on / off
    return P[:i] + P[j:]


def init_dm42():
    """INIT: MATA (Sun VL VB VR, FULL 2000-2050, and NU) and MATST (stars), as LBL 01-02.
    No NEWMAT of the cache here: NAV makes ALMC (and ALMQ) itself."""
    out = ['LBL "INIT"', 'XEQ 01', 'XEQ 02', '"%s"' % VALID, 'STO "VAL"', '"MATRICES READY: SUN STARS %s"' % VALID, 'SF 81', 'RTN']      # SF 81: NAV will not look for INIT
    for k, n in enumerate(('MATA', 'MATST')):
        b = B.compact(B.read(n))
        assert b[0] == 'LBL "%s"' % n and b[-1] == 'END'
        body = b[1:-1]
        if body and body[-1] == 'RTN':
            body = body[:-1]
        assert not any(l.startswith(('XEQ', 'GTO', 'LBL')) for l in body)
        out += ['LBL %02d' % (k + 1)] + body + ['RTN']
    return out + ['END']


def init_dm42_5y():
    """INIT for the FAST period only (fast_series.json, e.g. 2026-2030): NU (from MATA), the
    stars, and the Sun's FAST series VL VB VR (the start of MATF; the planets are left out)."""
    import json
    period = json.load(open(os.path.join(ROOT, 'python', 'native', 'fast_series.json')))['period']
    mata = B.compact(B.read('MATA'))
    nu = mata[mata.index('STO "NU"') - 4:-1]
    matf = B.compact(B.read('MATF'))
    sun = matf[1:matf.index('STO "EEL"') - 4]
    sun = [l for l in sun if l != '"FAST SERIES %s"' % period]
    st = B.compact(B.read('MATST'))[1:-1]
    out = ['LBL "INIT"', 'XEQ 01', 'XEQ 02', 'XEQ 03', '"%s"' % period, 'STO "VAL"',
           '"MATRICES READY: SUN STARS %s"' % period, 'SF 81', 'RTN']
    for k, body in enumerate((nu, st, sun)):
        if body and body[-1] == 'RTN':
            body = body[:-1]
        assert not any(l.startswith(('XEQ', 'GTO', 'LBL', 'END')) for l in body)
        out += ['LBL %02d' % (k + 1)] + body + ['RTN']
    return out + ['END']


def nav1_programs(p):
    """NAV1 has one view: no sky cache (ALMC, CACHE). ALMF calls the ephemeris directly again,
    without the Moon, the planets and the Moon phase; the chart routines of CHZ are left out."""
    q = dict(p)
    back = {'XEQ "%s"' % n: 'XEQ "%s"' % o for o, n in gencache.SWAP.items()}
    for v in ('ALMF', 'ALMT'):
        A = [back.get(l, l) for l in p[v]]
        A = seq(A, ['XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19'], [])
        i = A.index('XEQ "MOO2"')
        j = A.index('GTO 16', i) + 1
        assert 'XEQ "PLN3"' in A[i:j] and A[j] == '1.058', v
        q[v] = A[:i] + A[j:]
        assert not any(l in q[v] for l in back), v
    C = p['CHZ']
    i, j = C.index('LBL "HCZQ"'), C.index('LBL "HCZI"')
    assert C[i - 1] == 'RTN' and C[j - 1] == 'RTN'
    q['CHZ'] = C[:i] + C[j:]
    return q


def programs():
    with contextlib.redirect_stdout(io.StringIO()):
        progs = B.build()[3]                                # the processed programs (cache swaps, ALMR, navopt)
    p = B.no_tables(progs)
    p['CACHE'] = cache_lite()
    # the Moon lines of the pages: phase, age, HP, SD
    p['ALMT'] = cut(p['ALMT'], '"MOON "', '"   DOES NOT REPLACE THE NAUTICAL ALMANAC    "')    # ALMR (TEXT)
    p['ALMF'] = cut(p['ALMF'], '"WAXING"', '"S"', ['47', '196', '"NO MOON - NO PLANETS"', 'XEQ "PTXS"',
                                                    '33', '196', '"DM42 BETA"', 'XEQ "PTXS"'])
    p['HALMV'] = cut(p['HALMV'], '"WAXING"', '"S"', ['24', '176', '"NO MOON - NO PLANETS"', 'XEQ "PTXS"'])
    return p


def assemble(nav, p):
    need = B.closure(p, [c for c in B.calls(nav) if c != 'INIT'])
    assert not need & {'MOON', 'PLAN', 'PHAS', 'TGET'}, need
    q = dict(p)
    if 'PTXS' in need:
        big = set(''.join(B.strings(nav)) + ''.join(''.join(B.strings(q[n])) for n in need if n not in ('PTXS', 'PTXT'))
                  + '0123456789-.: %')
        small = set(B.WARNING + 'TSX NEWZHC-.0123456789')
        q['PTXS'] = B.trim_font(navopt.pdts(navopt.phls(navopt.fonts(B.read('PTXS')))), big)
        q['PTXT'] = B.trim_font(navopt.fonts(B.read('PTXT')), small)
    return nav + [l for n in B.KEEP if n in need for l in q[n]], sorted(need)


def main():
    p = programs()
    inp = gennav.inputs()
    # text only
    navtxt = (['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04']
              + ['0', 'STO "DH"', 'XEQ 20'] + gennav.text_steps(5) + ['REGS', 'RTN'] + inp + ['END'])
    # 1 ALMANAC 2 CHART 3 TEXT 9 INFO, no ants
    old = (gencache.NEWMAT, gennav.INFO, gennav.TITLE)
    gencache.NEWMAT = ALMC + ALMQ
    gennav.INFO = [t if 'ANTS' not in t else NOTE for t in gennav.INFO]
    gennav.TITLE = 'ALMANAC 47 BETA'
    try:
        nav12 = no_ants(gennav.program(inp, [1, 2, 3, 9], autoinit=True))
    finally:
        gencache.NEWMAT, gennav.INFO, gennav.TITLE = old
    # NAV1: no menu - the inputs, then the ALMANAC view; up / down one hour (the box while it
    # computes), + ends (screen and stack cleared, the stack size put back)
    nav1 = (['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04',
             'SSIZE#', 'STO "SSZ"', 'SSIZE8', '0', 'STO "DH"', 'XEQ 20', 'CLLCD',
             'LBL 01', 'XEQ 52', 'XEQ 21', 'XEQ "ALMF"',
             'RCL 39', str(gennav.UP), 'X=Y?', 'GTO 06', 'RCL 39', str(gennav.DOWN), 'X=Y?', 'GTO 07',
             'CLLCD', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN',
             'LBL 06', '1', 'STO+ "DH"', 'GTO 01', 'LBL 07', '1', 'STO- "DH"', 'GTO 01']
            + [str(x) for x in gennav.busy_box()] + inp + ['END'])
    os.makedirs(DEV, exist_ok=True)
    res = {}
    p1 = nav1_programs(p)
    for name, nav in (('NAVTXT_DM42', navtxt), ('NAV1_DM42', nav1)):   # NAV12 (menu 1 2 3 9): too big for the DM42
        L, need = assemble(nav, p1 if name != 'NAV12_DM42' else p)
        open(os.path.join(DEV, name + '.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        m = B.label_map(L, keep=('NAV', 'INIT'))
        open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8').write('\n'.join(B.rename_keep(L, m, ('NAV', 'INIT'))) + '\n')
        with open(os.path.join(OUT, name + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; INIT is NAVINIT_DM42)\n\n' % name)
            fh.write('NAV     NAV     %s\n' % B.LABEL_TEXT['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, B.LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
        res[name] = (L, need)
    init = init_dm42()
    open(os.path.join(OUT, 'NAVINIT_DM42.txt'), 'w', encoding='utf-8').write('\n'.join(init) + '\n')
    open(os.path.join(DEV, 'NAVINIT_DM42.txt'), 'w', encoding='utf-8').write('\n'.join(init) + '\n')
    init5 = init_dm42_5y()
    open(os.path.join(OUT, 'NAVINIT_DM42_5Y.txt'), 'w', encoding='utf-8').write('\n'.join(init5) + '\n')
    print('%-13s %7s %8s' % ('file', 'lines', 'bytes'))
    for name, (L, need) in res.items():
        print('%-13s %7d %8d   %s' % ((name,) + B.size(L) + (' '.join(need),)))
    print('%-13s %7d %8d' % (('NAVINIT_DM42',) + B.size(init)))
    print('%-13s %7d %8d' % (('NAVINIT_DM42_5Y',) + B.size(init5)))
    return res, init


if __name__ == '__main__':
    main()
