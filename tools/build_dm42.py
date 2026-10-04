#!/usr/bin/env python3
"""build_dm42.py - BETA builds for the C47 on the DM42 (64 KiB of program and matrix memory).

The DM42 has a quarter of the DM42n / R47 memory, too little for the Moon and planet series.
These builds keep the Sun (FULL series, valid 2000-2050) and the 58 navigation stars:

  NAVTXT_DM42     text only: NAV asks DATE UTC LAT LON, the almanac page goes into the
                  registers (R50 ..., stack and lettered registers) and NAV ends in REGS
  NAV1_DM42       no menu: the ALMANAC view straight after the inputs; up / down one hour
                  (the SINKING box while it computes), + ends; no ants
  NAVINIT_DM42    INIT: the Sun series (VL VB VR), nutation (NU) and the stars (ST)

The screens are those of NAVFULL (the T21 views of programs/atext/t21/): every text with ATEXT
in GRFNT 21 (PTXS and the number printers of atext_common), the symbols of glyphs47 (PSYB),
no AGRAPH font. Needs a C47 firmware with ATEXT and GRFNT. No Moon: the ALMANAC footer has only
the Sun's times. Free42 NAVLITTLE (build_free42.py) has the same view (little_almf).

What is left out: MOON, PLAN and PHAS (no Moon, no planets, no Moon phase), the Moon and planet
rows of the views, the tables (TBL), the ants, and the sky cache (CACHE, ALMC): with one view the
views call the Sun and star routines directly again (nav1_programs). NAV12 (menu 1 2 3 9,
cache with the Moon and planets marked below the horizon) is still in the script but not
written: about 72 KB as a .p47 file, too big for the DM42.

Load INIT first on its own: XEQ "INIT", delete it (GTO "INIT", DELP), then load NAV.
(If INIT is still there, the first NAV runs it: flag 81.)

  python3 tools/build_dm42.py      -> build/dm42/*.txt (+ build/dm42/dev/ with the original names)
"""
import os, sys, re, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators')]
import build_navfull as B
import gencache, gennav, navopt
import atext_common as AC

OUT = os.path.join(ROOT, 'build', 'dm42')
DEV = os.path.join(OUT, 'dev')
SRC = os.path.join(DEV, 'src')
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


def no_box(P):
    """No SINKING box (LBL 52-54): the previous screen stays until the new one is drawn."""
    i = P.index('LBL 52')
    j = P.index('RTN', P.index('PAUSE 0', i)) + 1
    assert P[j - 2:j] == ['PAUSE 0', 'RTN'] and 'LBL 54' in P[i:j]
    P = P[:i] + P[j:]
    out = []
    for l in P:
        if l == 'XEQ 52':
            continue
        out.append('RTN' if l == 'GTO 52' else l)
    assert not any(l.endswith(' 52') and l.startswith(('XEQ', 'GTO')) for l in out)
    return out


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


def nav1_programs(p, chart=False):
    """No sky cache (ALMC, CACHE): the views call the ephemeris directly again, without the
    Moon, the planets and the Moon phase. Without the chart (HALMV) the chart routines of CHZ
    (HCZQ, HCZR: the celestial equator) are left out too."""
    q = dict(p)
    back = {'XEQ "%s"' % n: 'XEQ "%s"' % o for o, n in gencache.SWAP.items()}
    for v in ('ALMF', 'ALMT') + (('HALMV',) if chart else ()):
        A = [back.get(l, l) for l in p[v]]
        if 'XEQ "PHA2"' in A:                              # the chart has no Moon phase any more
            A = seq(A, ['XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19'], [])
        i = A.index('XEQ "MOO2"')
        j = A.index('1.058', i)
        assert 'XEQ "PLN3"' in A[i:j] and A[j - 1].startswith('GTO '), v
        q[v] = A[:i] + A[j:]
        assert not any(l in q[v] for l in back), v
    if not chart:
        C = p['CHZ']
        i, j = C.index('LBL "HCZQ"'), C.index('LBL "HCZI"')
        assert C[i - 1] == 'RTN' and C[j - 1] == 'RTN'
        q['CHZ'] = C[:i] + C[j:]
    return q


def programs():
    with contextlib.redirect_stdout(io.StringIO()):
        progs = B.build()[3]                                # the processed programs (cache swaps, ALMR, navopt)
    # the almanac tables are read when they are loaded (TBL, flag 10): SUNA takes the Sun and
    # GHA Aries from TGET. No Moon here, so flag 11 (the T on the screens) is set by SUNA itself.
    p = dict(progs)
    s = '\n'.join(p['SUNA']) + '\n'
    for a, b in (('FS? 10\nXEQ 45\n', 'CF 11\nFS? 10\nXEQ 45\n'),
                 ('RCL 70\n6\nXEQ "TGET"\nX<0?\nRTN\nSTO 80\nRTN\n', 'RCL 70\n6\nXEQ "TGET"\nX<0?\nRTN\nSTO 80\nSF 11\nRTN\n')):
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    p['SUNA'] = s.rstrip('\n').split('\n')
    p['CACHE'] = cache_lite()
    # the Moon lines of the pages: phase, age, HP, SD
    p['ALMT'] = cut(p['ALMT'], '"MOON "', '"   DOES NOT REPLACE THE NAUTICAL ALMANAC    "')    # ALMR (TEXT)
    p['ALMF'] = cut(p['ALMF'], '"WAXING"', '"S"', ['47', '196', '"NO MOON - NO PLANETS"', 'XEQ "PTXS"',
                                                    '33', '196', '"DM42 BETA"', 'XEQ "PTXS"'])
    return p


def unused_locals(A, ind_targets=None):
    """Drop the subroutines nothing calls any more (Moon and planet rows, their names and words):
    a block LBL n ... RTN right after an RTN, whose label no XEQ / GTO uses. With an XEQ IND
    nothing is dropped, unless ind_targets lists the labels the indirect calls can reach."""
    while True:
        called = {l.split()[1] for l in A if re.fullmatch(r'(XEQ|GTO) \d+', l)} | {str(n) for n in ind_targets or ()}
        ind = ind_targets is None and any(re.fullmatch(r'(XEQ|GTO) IND \d+', l) for l in A)
        out, i, drop = [], 0, False
        while i < len(A):
            m = re.fullmatch(r'LBL (\d+)', A[i])
            if m and out and out[-1] == 'RTN' and m.group(1) not in called and not ind:
                j = A.index('RTN', i)
                i = j + 1; drop = True
                continue
            out.append(A[i]); i += 1
        if not drop:
            return out
        A = out


def little_almf():
    """The ALMANAC view of NAVLITTLE (C47 and Free42): the T21 view with the Sun and the stars only,
    no Moon (the right half of the footer, MOON / AGE in the T21 view, stays empty; no phase glyphs)."""
    A = B.read21('ALMF')
    A = cut(A, '"WAXING"', '"S"')
    A = seq(A, ['XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19'], [])
    A = cut(A, 'XEQ "MOO2"', '1.058')                  # the Moon and planet rows (LBL 35 / 36 go with them)
    assert not any(re.fullmatch(r'(XEQ|GTO) 3[56]', l) for l in A)
    A = unused_locals(A, ind_targets=())               # the phase glyphs (LBL 48-55, XEQ IND 23) go too
    assert not any(re.fullmatch(r'XEQ IND 23|LBL (4[89]|5[0-5])', l) for l in A), 'phase glyphs left'
    assert not any(l in ('XEQ "MOO2"', 'XEQ "PLN3"', 'XEQ "PHA2"', 'XEQ "PTXT"', 'XEQ "PTTY"') for l in A)
    return A


def little_halmv():
    """The CHART view of NAV12_DM42: the T21 view without the Moon and the planets."""
    H = B.read21('HALMV')
    if 'XEQ "PHA2"' in H:
        H = seq(H, ['XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19'], [])
    H = cut(H, 'XEQ "MOO2"', '1.058')                  # the Moon and planet rows (LBL 35 / 36 go with them)
    assert not any(re.fullmatch(r'(XEQ|GTO) 3[56]', l) for l in H)
    H = unused_locals(H, ind_targets=())               # the XEQ IND 43 (planet symbols, names) go with LBL 63
    assert not any(re.fullmatch(r'(XEQ|GTO) IND .+', l) for l in H), 'an indirect call is left in HALMV'
    assert not any(l in ('XEQ "MOO2"', 'XEQ "PLN3"', 'XEQ "PHA2"', 'XEQ "PTXT"', '"MOON"', '"("') for l in H)
    return H


def little_almr(A):
    """ALMR (TEXT) without what is left of the Moon and the planets: LBL 27 (WANING) and the names
    LBL 81-85 (XEQ IND 23 = 80 + body: only the Sun, 80, is listed)."""
    A = unused_locals(A, ind_targets=(80,))
    assert not any(l in ('"MOON"', '"WANING"', '"WAXING"') for l in A), 'Moon text left in ALMR'
    return A


def nav21(nav):
    """NAV of a DM42 build for the T21 views: GRFNT 21 after the inputs, 20 before it ends
    (NAVLITTLE / NAV1T: at the + key; NAV12: LBL 08), the menu's top line at the T21 columns."""
    if 'LBL 08' in nav:                                # NAV12: the menu NAV
        return B.grfnt21(B.top21(nav))
    nav = seq(nav, ['XEQ 20', 'CLLCD'], ['XEQ 20', '21', 'GRFNT', 'DROP', 'CLLCD'])
    return seq(nav, ['CLLCD', 'RCL "SSZ"'], ['20', 'GRFNT', 'DROP', 'CLLCD', 'RCL "SSZ"'])


def assemble(nav, p):
    """NAV + the programs it calls, the T21 views (ALMF and HALMV without the Moon and planets),
    the ATEXT text routines and the symbols PSYB / PSYS (only those the views draw: the Sun and the
    star). The tinyFont routines (PTTY, PTNT) only with the chart (NAV12)."""
    q = dict(p)
    if 'XEQ "ALMF"' in nav:
        nav = nav21(nav)
        q['ALMF'] = little_almf()
        q['HALMV'] = little_halmv()
    if 'ALMT' in q:                                     # ALMR (TEXT): no Moon or planet names
        q['ALMT'] = little_almr(q['ALMT'])
        tiny = 'XEQ "HALMV"' in nav                     # the chart labels in the tinyFont
        q['PTXS'] = AC.printers(navopt.pdts(navopt.phls(navopt.fonts(B.read('PTXS')))), '49', tiny, 21)
        import glyphs47
        q['PSYB'] = glyphs47.program('PSYB', glyphs47.BIG, ws=16)
        q['PSYS'] = glyphs47.program('PSYS', glyphs47.SMALL)
    need = B.closure(q, [c for c in B.calls(nav) if c != 'INIT'])
    assert not need & {'MOON', 'PLAN', 'PHAS', 'PTXT'}, need
    for f in {'PSYB', 'PSYS'} & need:                   # only the Sun and the star
        q[f] = B.trim_font(q[f], set('@*'))
    return nav + [l for n in B.KEEP21 if n in need for l in q[n]], sorted(need)


def nav1_program(inp):
    """NAV1 / NAVLITTLE: no menu - the inputs, then the ALMANAC view; up / down one hour,
    + ends (screen and stack cleared, the stack size put back). no_box() takes the box out."""
    return (['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04',
             'SSIZE#', 'STO "SSZ"', 'SSIZE8', '0', 'STO "DH"', 'XEQ 20', 'CLLCD',
             'LBL 01', 'XEQ 52', 'XEQ 21', 'XEQ "ALMF"',
             'RCL 39', str(gennav.UP), 'X=Y?', 'GTO 06', 'RCL 39', str(gennav.DOWN), 'X=Y?', 'GTO 07',
             'CLLCD', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN',
             'LBL 06', '1', 'STO+ "DH"', 'GTO 01', 'LBL 07', '1', 'STO- "DH"', 'GTO 01']
            + [str(x) for x in gennav.busy_box()] + inp + ['END'])


def builds():
    """The four DM42 builds before assembly: {name: (NAV lines, the programs it may call)}."""
    p = programs()
    inp = gennav.inputs()
    # text only
    navtxt = (['LBL "NAV"', 'FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04']
              + ['0', 'STO "DH"', 'XEQ 20'] + gennav.text_steps(5) + ['REGS', 'RTN'] + inp + ['END'])
    # NAV12: menu 1 ALMANAC 2 CHART 3 TEXT, no ants, no sky cache (LBL 28, the sky before the
    # menu, only returns: each view computes what it shows)
    old = (gencache.NEWMAT, gennav.INFO, gennav.TITLE)
    gencache.NEWMAT = []
    gennav.TITLE = 'ALMANAC 47 BETA'
    try:
        nav12 = no_ants(gennav.program(inp, [1, 2, 3], autoinit=True))
    finally:
        gencache.NEWMAT, gennav.INFO, gennav.TITLE = old
    i = nav12.index('LBL 28')
    j = nav12.index('RTN', nav12.index('GTO 29', i)) + 1
    nav12 = nav12[:i] + ['LBL 28', 'RTN'] + nav12[j:]
    # NAV1: no menu - the inputs, then the ALMANAC view; up / down one hour (the box while it
    # computes), + ends (screen and stack cleared, the stack size put back)
    nav1 = nav1_program(inp)
    # NAV1T: NAV1, and + ends with the text page of the hour on the screen (ALMR into the
    # registers, as NAVTXT) and the register browser
    k = nav1.index('CLLCD', nav1.index('XEQ "ALMF"'))
    assert nav1[k:k + 7] == ['CLLCD', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN']
    nav1t = nav1[:k] + ['CLLCD', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4'] + gennav.text_steps(5) + ['REGS', 'RTN'] + nav1[k + 7:]
    p1 = nav1_programs(p)
    p12 = nav1_programs(p, chart=True)
    nav1, nav1t, nav12 = no_box(nav1), no_box(nav1t), no_box(nav12)
    return {'NAVTXT_DM42': (navtxt, p1), 'NAVLITTLE': (nav1, p1), 'NAV1T_DM42': (nav1t, p1),
            'NAV12_DM42': (nav12, p12)}


# what the routines do in the DM42 builds (Sun and stars only); the rest as in NAVFULL
LABEL_TEXT = {
 'NAV':   'no menu: asks DATE UTC LAT LON, then the ALMANAC screen; up / down one hour, + ends',
 'ALMF':  'ALMANAC: GHA ARIES, GHA, Dec, Hc, Zn of the Sun and the stars; twilight, rise/set, meridian passage',
 'HALMV': 'CHART: horizon chart of the Sun and the stars left, their Hc / Zn right',
 'ALMR':  'TEXT: the almanac page (Sun and stars) as text in R50-R76; NAV ends in REGS',
 'PSYB':  'SYMBOL of the Sun and the star, 12 rows (glyphs47, AGRAPH) - Z row, Y column, X symbol',
 'PSYS':  'SYMBOL of the Sun and the star, 7 rows (glyphs47, AGRAPH; the chart) - Z row, Y column, X symbol',
}


def main():
    res = {}
    # build/dm42/NAVLITTLE (was NAV1_DM42) + NAVINIT_LITTLE; the other builds in dev/;
    # dev/src/ has every build with the original names; short labels from tools/labels/*.map
    for name, (nav, progs) in builds().items():
        L, need = assemble(nav, progs)
        L = B.keywait(L)                                   # keys read in a PAUSE (tools/keywait_patch.py)
        B.write(os.path.join(SRC, name + '.txt'), L)
        m = B.fixed_map(name, L, keep=('NAV', 'INIT'))
        d = OUT if name == 'NAVLITTLE' else DEV
        B.write(os.path.join(d, name + '.txt'), B.rename_keep(L, m, ('NAV', 'INIT')))
        with open(os.path.join(d, name + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; INIT is NAVINIT_LITTLE)\n\n' % name)
            text = dict(B.LABEL_TEXT, **LABEL_TEXT)
            if name == 'NAV12_DM42':
                text['NAV'] = 'graphic menu (KEY?): asks DATE UTC LAT LON, 1 ALMANAC 2 CHART 3 TEXT, 0 ends'
            elif name == 'NAVTXT_DM42':
                text['NAV'] = 'text only: asks DATE UTC LAT LON, the almanac page into R50 ..., then REGS'
            fh.write('NAV     NAV     %s\n' % text['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, text.get(k, '')) for k, v in m.items()) + '\n')
        res[name] = (L, need)
    init = init_dm42()
    B.write(os.path.join(OUT, 'NAVINIT_LITTLE.txt'), init)
    B.write(os.path.join(SRC, 'NAVINIT_LITTLE.txt'), init)
    init5 = init_dm42_5y()
    B.write(os.path.join(DEV, 'NAVINIT_DM42_5Y.txt'), init5)
    print('%-13s %7s %8s' % ('file', 'lines', 'bytes'))
    for name, (L, need) in res.items():
        print('%-13s %7d %8d   %s' % ((name,) + B.size(L) + (' '.join(need),)))
    print('%-13s %7d %8d' % (('NAVINIT_LITTLE',) + B.size(init)))
    print('%-13s %7d %8d' % (('NAVINIT_DM42_5Y',) + B.size(init5)))
    return res, init


if __name__ == '__main__':
    main()
