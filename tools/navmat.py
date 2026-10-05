#!/usr/bin/env python3
"""navmat.py - C47 NAVFULL and DM42 NAVLITTLE (C47 firmware): faster and smaller with the same calculation method as
v2.0.0 (every hour computed in full; no hour stepping). Free42 keeps its own code (build_free42.py).

Calculation (navmat.c47 / navmat.little, on the named listing before regalloc renumbers the registers):
  deg    rad→deg in place of × 57.29577… (a 34-digit number is 18 bytes)
  ceq    the celestial equator dots of the charts on whole vectors (CEQQ / CEQR; EQ2 / EQ3 replace ALMQ)
  tget   the almanac tables: T0..Tn-1 once per call, each quantity one M.GETM and a DOT (no RCLEL per coefficient)
  hcz    Hc and Zn from the body's direction vector (2 trigonometric functions instead of 6)
  margs  the Moon series' arguments (ML × MA10) once for the SIN and the COS sums
  cexp   the series' cos and sin of a vector as one complex eˣ(i A): the firmware's SIN / COS run at 75 digits,
         eˣ at 39 (cos 60° differs by 3E-34); the Sun, planet, nutation and Moon series about 3 times faster
  views  the header of every view and the compass row of the charts once each as a routine (HDR, CMN, CMS)
Size (navmat.size, after regalloc):
  strip    no REM, no code NAV cannot reach
  consts   the most used numbers in registers after the program's own, set and given back by NAV
  names    NAV's own variables named a letter and a digit (V0, V1, ...)
  outline  repeated runs of steps as subroutines
ALM_PASSES=deg,tget,... picks a subset (measurements).

What the C47 firmware does on a whole matrix, element by element (tested in the C47 simulator, master fc226bca):
SIN COS ASIN ATAN x² ABS IP FP LN eˣ CHS, M MOD r, M ÷ r, r ÷ M, M ± M, M × r (r real or complex); COMPLEX of two
real matrices (Y + i X); on a complex matrix ∡ (atan2), ABS, Re, Im, eˣ, x². Not element by element: 1/x (inverse),
√ (matrix root), M × M (matrix product). M.GETM / M.PUTM move a block out of / into the indexed matrix in one step.

Not done (measured in the C47 simulator, 2026-10-05): the 58 stars as one matrix was 14 % slower per hour; the hour
stepping of the series (branch c47-matrix) was slower on the calculator.
"""
import os
import re

import navopt_engine as E

STEPS = ((3, 120), (2, 180))           # degrees between the dots, dots in a turn


def _block(L, first, last):
    """L[i:j]: from the line first to the line last (included)."""
    i = L.index(first)
    j = L.index(last, i + 1)
    return L[i:j + 1]


def ceq_code():
    P = ['LBL "CEQQ"', 'STO "QS"', 'X<>Y', 'STO "QG"', 'X<>Y']           # Y first GHA, X step: kept on the stack
    for step, n in STEPS:
        P += ['RCL "QS"', str(step), 'X=Y?', 'GTO %d' % (40 + step)]       # 43 / 42: this step's cache check
    P += ['RTN']                                                          # (the charts use only these two steps)
    for step, n in STEPS:
        lab = 40 + step
        k = lambda s: '"KQ%s%d"' % (s, step)
        new = lab + 5                                                     # 48 / 47: compute again
        P += ['LBL %d' % lab, str(step), 'STO "KQM"', '1', 'STO "KQR"',
              'RCL 91', 'RCL ' + k('A'), 'X≠Y?', 'GTO %d' % new, 'RCL 92', 'RCL ' + k('O'), 'X≠Y?', 'GTO %d' % new,
              'RCL "QG"', 'RCL ' + k('G'), 'X≠Y?', 'GTO %d' % new, 'RTN',
              'LBL %d' % new, 'RCL 91', 'STO ' + k('A'), 'RCL 92', 'STO ' + k('O'), 'RCL "QG"', 'STO ' + k('G'),
              str(n), 'XEQ 49', 'STO "EQ%d"' % step, 'RTN']
    # LBL 49: X = n dots -> X = the n x 3 matrix [Hc, sin Hc, Zn], 30 dots at a time (little memory at once):
    # QV = [z0 w^k, k < 30] by doubling, then chunk c is QV × w^(30 c)
    P += ['LBL 49', 'STO "QN"', '30', '÷', 'STO "QK"',
          'RCL "QS"', '1', '→REC', 'X<>Y', 'COMPLEX', 'STO "QW"', 'STO "QP"',                # w, w^L
          'RCL "QG"', 'RCL+ 92', '1', '→REC', 'X<>Y', 'COMPLEX',                            # z0 = e^{i (GHA0 + λ)}
          '1', '1', 'NEWMAT', 'X<>Y', '+', 'STO "QV"', '1', 'STO "QL"',
          'LBL 44', 'RCL "QL"', '2', '×', '1', 'NEWMAT', 'ENTER', 'COMPLEX', 'STO "QT"',
          'INDEX "QT"', 'RCL "QV"', 'M.PUTM',                                               # rows 1..QL
          'RCL "QL"', '1', '+', '1', 'STOIJ', 'RCL "QV"', 'RCL× "QP"', 'M.PUTM',            # rows QL+1..2 QL: × w^QL
          'RCL "QP"', 'x²', 'STO "QP"', 'RCL "QL"', '2', '×', 'STO "QL"',
          'RCL "QT"', 'STO "QV"', '30', 'RCL "QL"', 'X<Y?', 'GTO 44',
          'INDEX "QV"', '30', '1', 'M.GETM', 'STO "QV"',                                   # the first 30
          'RCL "QS"', '30', '×', '1', '→REC', 'X<>Y', 'COMPLEX', 'STO "QP"',                # w^30
          'RCL "QN"', '3', 'NEWMAT', 'STO "QT"', '1', 'STO "QL"',
          'LBL 45', 'INDEX "QT"', 'RCL "QL"', '1', 'STOIJ', 'RCL "QV"', 'Re', 'RCL× "HZC"',
          '0.99999999999999999999999999999', '×', 'ASIN', 'M.PUTM',                       # Hc (sin Hc kept inside ±1)
          'RCL "QL"', '2', 'STOIJ', 'RCL "QV"', 'Re', 'RCL× "HZC"', 'M.PUTM',             # sin Hc
          'RCL "QL"', '3', 'STOIJ', 'RCL "QV"', 'Re', 'RCL× "HZS"', 'CHS', 'RCL "QV"', 'Im', 'COMPLEX',
          '∡', 'CHS', '360', 'MOD', 'M.PUTM',                                               # Zn
          'RCL "QV"', 'RCL× "QP"', 'STO "QV"', '30', 'STO+ "QL"',
          'RCL "QK"', '1', '-', 'STO "QK"', 'X≠0?', 'GTO 45',
          'RCL "QT"', 'DELITM "QT"', 'DELITM "QV"', 'DELITM "QW"', 'DELITM "QP"', 'RTN']
    P += ['LBL "CEQR"', 'RCL "KQM"', '2', 'X=Y?', 'GTO 41', 'INDEX "EQ3"', 'GTO 40', 'LBL 41', 'INDEX "EQ2"', 'LBL 40',
          'RCL "KQR"', '1', 'STOIJ', '+', 'STO "KQR"',
          'RCLSEQ', 'STO 96', 'RCLSEQ', 'STO "SHC"', 'RCLEL', 'STO 97', 'RCL 97', 'RCL 96', 'RTN', 'END']
    return P


def ceq(L):
    old = _block(L, 'LBL "CEQQ"', 'END')
    assert 'LBL "CEQR"' in old, 'navmat: CEQR not after CEQQ'
    L = E.cut(L, old, ceq_code())
    return E.cut(L, ['300', 'ENTER', '3', 'NEWMAT', 'STO "ALMQ"', '999', 'STO "KQA3"', 'STO "KQA2"'],
                 ['999', 'STO "KQA3"', 'STO "KQA2"'])


def _program(L, label):
    """(first, last) line indexes of the program that holds LBL label (last = its END)."""
    i = L.index(label)
    a = i
    while a > 0 and L[a - 1] != 'END':
        a -= 1
    return a, L.index('END', i)


def _free(L, label, n, taken=()):
    """n local label numbers not used in the program of label (nor in taken)."""
    a, b = _program(L, label)
    used = {int(l[4:]) for l in L[a:b] if l.startswith('LBL ') and l[4:].isdigit()} | set(taken)
    free = [k for k in range(99, 9, -1) if k not in used]
    return free[:n]


def tget(L):
    """TGET, the almanac tables (TBL): Σ c_k T_k(x) of a row of the table (Chebyshev). Before: Clenshaw, one RCLEL per
    coefficient (each copies the whole table, up to 2064 numbers). Now: TCV = [T0(x) .. Tn-1(x)] once per call
    (recurrence on a 1 x n vector), then each quantity is one M.GETM of its n coefficients and a DOT."""
    old30 = ['LBL 30', 'STO 04', 'RCL+ 02', '1', '-', 'STO 05', '0', 'STO 38', 'STO 39', 'LBL 31', 'RCL 07', 'RCL 05',
             'STOIJ', 'RCLEL', 'RCL 08', 'RCL× 38', '2', '×', '+', 'RCL- 39', 'RCL 38', 'STO 39', 'R↓', 'STO 38', '1',
             'STO- 05', 'RCL 04', 'RCL 05', 'X>Y?', 'GTO 31', 'RCL 07', 'RCL 04', 'STOIJ', 'RCLEL', 'RCL 08', 'RCL× 38',
             '+', 'RCL- 39', 'RTN']
    new30 = ['LBL 30', 'STO 04', 'RCL 00', '20', '+', 'STO 05', 'XEQ IND 05',     # the table indexed again
             'RCL 07', 'RCL 04', 'STOIJ', '1', 'RCL 02', 'M.GETM',                       # its R02 coefficients
             'INDEX "TCV"', '1', '1', 'STOIJ', 'DROP', 'DROP', '1', 'RCL 02', 'M.GETM', 'DOT', 'RTN',   # T0 .. T(R02-1)
             'LBL 29', '1', 'RCL 06', 'NEWMAT', 'STO "TCV"', 'INDEX "TCV"', '1', 'STOSEQ', 'RCL 08', 'STOSEQ',
             'RCL 06', '2', '-', 'STO 05', 'X=0?', 'RTN', '1', 'STO 39', 'RCL 08', 'STO 38',
             'LBL 28', 'RCL 38', 'RCL× 08', '2', '×', 'RCL- 39', 'RCL 38', 'STO 39', 'X<>Y', 'STO 38', 'STOSEQ',
             'DSE 05', 'GTO 28', 'RTN']
    i = L.index('LBL "TGET"')
    j = L.index('END', i)
    T = E.cut(L[i:j + 1], old30, new30)
    T = E.cut(T, ['RCL 06', 'STO 02', '1', 'XEQ 30'], ['RCL 06', 'STO 02', 'XEQ 29', '1', 'XEQ 30'])
    return L[:i] + T + L[j + 1:]


# the matrices NAV makes for these rewrites: made (as 0) when NAV starts, deleted when it ends (key 0), so a NAV
# leaves no more in memory than before (ALMC stays, as in the release; EQ2 / EQ3 replace ALMQ)
KEPT = ('TCV', 'EQ2', 'EQ3')


def tidy(L):
    """NAV: at the start (after SSIZE8) the state of the rewrites (nothing kept: 999 / 0) and their matrices as 0; at
    the end (before the last CLSTK: XEQ 08 in NAVFULL, RCL "SSZ" .. SSIZE4 in NAVLITTLE) the matrices deleted."""
    i = L.index('LBL "NAV"')
    j = L.index('END', i)
    nav = L[i:j + 1]
    used = [v for v in KEPT if 'STO "%s"' % v in L or 'RCL "%s"' % v in L]
    init = []
    if 'STO "USG"' in L:
        init += ['-1', 'STO "USG"', 'STO "UMG"', 'STO "UTG"', 'STO "UPG"']
    if used:
        init += ['0'] + ['STO "%s"' % v for v in used]
    if 'RCL× "C1"' in L or 'RCL× "C2"' in L:
        init += ['0', '1', 'COMPLEX', 'STO "C1"', '0', '𝜋', '180', '÷', 'COMPLEX', 'STO "C2"']
        used += ['C1', 'C2']
    if 'STO "EQ3"' in L:
        init += ['STO "ALMQ"', 'DELITM "ALMQ"']        # INIT makes ALMQ (300 x 3, 14 KB): no longer used
    if not init:
        return L
    if 'SIZE 100' in nav:                                     # Free42 (before navhopt.f42_regs)
        k = nav.index('SIZE 100')
        nav = nav[:k + 1] + init + nav[k + 1:]
        ends = [e for e in range(1, len(nav) - 1) if nav[e] == 'CLST' and nav[e + 1] in ('CLD', 'RTN')
                and not nav[e - 1].startswith('INPUT')]
        assert len(ends) == 1, 'navmat: the end of the Free42 NAV not found once'
        e = ends[0]
    else:
        k = nav.index('SSIZE8')
        nav = nav[:k + 1] + init + nav[k + 1:]
        ends = [e for e in range(1, len(nav)) if nav[e] == 'CLSTK' and nav[e - 1] in ('XEQ 08', 'SSIZE4')]
        assert len(ends) == 1, 'navmat: the end of NAV not found once'
        e = ends[0] - (1 if nav[ends[0] - 1] == 'XEQ 08' else 4)
        assert nav[e] in ('XEQ 08', 'RCL "SSZ"'), nav[e]
    nav = nav[:e] + ['DELITM "%s"' % v for v in used] + nav[e:]
    return L[:i] + nav + L[j + 1:]


def little(L):
    """DM42 NAVLITTLE (C47 firmware): the tables, Hc Zn from vectors, the series' COS by eˣ; no Moon, no charts."""
    for k, fn in (('deg', deg_rad), ('tget', tget), ('hcz', hcz_vec_little), ('cexp', cexp)):
        if k in PASSES:
            L = fn(L)
    return tidy(L)


def _in(L, name, old, new):
    """E.cut inside the routine LBL "name" only (up to the next LBL "...")."""
    i = L.index('LBL "%s"' % name)
    j = next(k for k in range(i + 1, len(L)) if L[k].startswith('LBL "') or L[k] == 'END')
    return L[:i] + E.cut(L[i:j], old, new) + L[j:]


def _capture(L, planets=False):
    """SUNA, MOO2 (when there), STR2 (and the planets: PLN2, PLNQ) keep the direction (U*X U*Y U*Z) and the GHA it gives (U*G)."""
    cap = lambda b, rx: ['RCL+ 76', 'X<>Y', '→REC', 'STO "U%sY"' % b, 'X<>Y', 'STO "U%sZ"' % b, 'X<>Y',
                         'RCL %s' % rx, 'STO "U%sX"' % b, '→POL']
    L = _in(L, 'SUNA', ['RCL+ 76', 'X<>Y', '→REC', 'RCL 78', '→POL'], cap('S', '78'))
    L = _in(L, 'SUNA', ['RCL- 78', '360', 'MOD', 'STO 81'], ['RCL- 78', '360', 'MOD', 'STO 81', 'STO "USG"'])
    if 'LBL "MOO2"' in L:
        L = _in(L, 'MOO2', ['RCL+ 76', 'X<>Y', '→REC', 'RCL 06', '→POL'], cap('M', '06'))
        L = _in(L, 'MOO2', ['RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 06'],
                ['RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 06', 'STO "UMG"'])
    L = _in(L, 'STR2', ['RCL+ 76', 'X<>Y', '→REC', 'RCL 85', '→POL'], cap('T', '85'))
    L = _in(L, 'STR2', ['RCL 89', 'RCL+ 80', '360', 'MOD', 'RTN'],
            ['RCL 89', 'RCL+ 80', '360', 'MOD', 'STO "UTG"', 'RTN'])
    if planets:                                # the planets: the full position (PLN2) and the quick one (PLNQ)
        L = _in(L, 'PLN2', ['RCL+ 76', 'X<>Y', '→REC', 'RCL 35', '→POL'], cap('P', '35'))
        L = _in(L, 'PLN2', ['RCL 80', 'RCL- 05', '360', 'MOD', 'STO 04'],
                ['RCL 80', 'RCL- 05', '360', 'MOD', 'STO 04', 'STO "UPG"'])
        L = _in(L, 'PLNQ', ['23.4393', '+', 'X<>Y', '→REC', 'RCL 56', '→POL'],
                ['23.4393', '+'] + cap('P', '56')[1:])
        L = _in(L, 'PLNQ', ['RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 53'],
                ['RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 53', 'STO "UPG"'])
    return L


def _hv(hv):
    """LBL hv: X x, Y y, Z z (right-ascension frame, any length: the planets' vectors are in AU) -> as HCZ: R96 Hc,
    R97 Zn, "SHC" sin Hc, X Hc. →POL(north, east) gives Zn and the horizontal length h, →POL(h, up) gives Hc and
    the length r: sin Hc = up / r. Two trigonometric functions."""
    return ['LBL %d' % hv, 'STO "VX"', 'R↓', 'STO "VY"', 'R↓', 'STO "VZ"',
            'RCL "VX"', 'RCL× "HCT"', 'RCL "VY"', 'RCL× "HST"', '+', 'STO "VM"',      # cos δ cos LHA
            'RCL× "HZC"', 'RCL "VZ"', 'RCL× "HZS"', '+', 'STO "VU"',                    # up
            'RCL "VZ"', 'RCL× "HZC"', 'RCL "VM"', 'RCL× "HZS"', '-',                    # north
            'RCL "VX"', 'RCL× "HST"', 'RCL "VY"', 'RCL× "HCT"', '-',                    # cos δ sin LHA
            'X<>Y', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 97', 'DROP',             # Zn; X h
            'RCL "VU"', 'X<>Y', '→POL', 'RCL "VU"', 'X<>Y', '÷', 'STO "SHC"', 'DROP', 'STO 96', 'RTN']


def _guard(go, fb, hv, b, gha, decgha):
    """LBL go: the kept vector of body b when its GHA is the one given (gha), else the real HCZ (decgha pushes Dec, GHA)."""
    return ['LBL %d' % go, 'RCL "U%sG"' % b] + [gha] + ['X≠Y?', 'GTO %d' % fb,
            'RCL "U%sZ"' % b, 'RCL "U%sY"' % b, 'RCL "U%sX"' % b, 'GTO %d' % hv,
            'LBL %d' % fb] + decgha + ['XEQ "HCZ"', 'RTN']


def hcz_vec_little(L):
    """NAVLITTLE: no cache; ALMF reduces the Sun and each star itself (RCL 46 RCL 45 XEQ "HCZ")."""
    L = _capture(L)
    hv, gs, fs, gt, ft = _free(L, 'LBL "ALMF"', 5)
    i = L.index('LBL "ALMF"')
    a, b = _program(L, 'LBL "ALMF"')
    seg = L[i:b]
    hz = [k for k in range(len(seg) - 2) if seg[k:k + 3] == ['RCL 46', 'RCL 45', 'XEQ "HCZ"']]
    assert len(hz) == 2, 'navmat: ALMF: the Sun and the star HCZ'
    seg[hz[1]:hz[1] + 3] = ['XEQ %d' % gt]
    seg[hz[0]:hz[0] + 3] = ['RCL 80', 'RCL+ 92', '1', '→REC', 'STO "HCT"', 'X<>Y', 'STO "HST"', 'XEQ %d' % gs]
    code = _hv(hv) + _guard(gs, fs, hv, 'S', 'RCL 45', ['RCL 46', 'RCL 45']) + \
        _guard(gt, ft, hv, 'T', 'RCL 45', ['RCL 46', 'RCL 45'])
    seg = seg[:-1] + code + seg[-1:] if seg[-1] == 'END' else seg + code
    return L[:i] + seg + L[b:]


def hcz_vec(L):
    """Hc and Zn from the body's vector: SUNA, MOO2 and STR2 turn the body into its equatorial direction (x y z,
    right-ascension frame) just before →POL gives RA and Dec; they keep it (US*, UM*, UT*) with the GHA it gives
    (USG, UMG, UTG). With θ = GHA Aries + λ (cos and sin kept by CALC: HCT HST), the meridian components are
    x cos θ + y sin θ and x sin θ - y cos θ, so Hc = ASIN and Zn = -→POL: 2 trigonometric functions instead of HCZ's
    6. When the GHA CALC received is not the kept one (the tables gave the Sun or the Moon), the real HCZ.
    The planets too: PLN2 (full position) and PLNQ (quick one) keep UP* and UPG."""
    L = _capture(L, planets=True)
    hv, *labs = _free(L, 'LBL "CALC"', 1 + 4 * 2)
    code = _hv(hv)
    calls = {}
    for k, b in enumerate('SMTP'):
        go, fb = labs[2 * k:2 * k + 2]
        calls[b] = go
        code += _guard(go, fb, hv, b, 'RCL "KA"', ['RCL "KB"', 'RCL "KA"'])
    c = L.index('LBL "CALC"')
    e = next(k for k in range(c + 1, len(L)) if L[k].startswith('LBL "'))
    calc = L[c:e]
    calc = E.cut(calc, ['XEQ "PHA2"'], ['RCL 80', 'RCL+ 92', '1', '→REC', 'STO "HCT"', 'X<>Y', 'STO "HST"', 'XEQ "PHA2"'])
    # no kept vector yet for this time (-1 is no GHA): a table answer then takes the real HCZ
    calc = E.cut(calc, ['RCL "KJ"', 'XEQ "SUNA"'], ['-1', 'STO "USG"', 'DROP', 'RCL "KJ"', 'XEQ "SUNA"'])
    calc = E.cut(calc, ['XEQ "MOO2"'], ['-1', 'STO "UMG"', 'DROP', 'XEQ "MOO2"'])
    hz = [k for k in range(len(calc) - 2) if calc[k:k + 3] == ['RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"']]
    assert len(hz) == 2, 'navmat: CALC: the Sun and the Moon HCZ'
    for k, b in zip(reversed(hz), 'MS'):
        calc[k:k + 3] = ['XEQ %d' % calls[b]]
    calc = E.cut(calc, ['RCL 82', 'XEQ "PLN3"', 'STO "KA"', 'X<>Y', 'STO "KB"', 'X<>Y', 'XEQ "HCZ"'],
                 ['-1', 'STO "UPG"', 'DROP', 'RCL 82', 'XEQ "PLN3"', 'STO "KA"', 'X<>Y', 'STO "KB"', 'X<>Y',
                  'XEQ %d' % calls['P']])
    L = L[:c] + calc + L[e:]
    L = _in(L, 'CSQK', ['XEQ "STR2"', 'STO "KA"', 'X<>Y', 'STO "KB"', 'X<>Y', 'XEQ "HCZ"'],
            ['XEQ "STR2"', 'STO "KA"', 'X<>Y', 'STO "KB"', 'X<>Y', 'XEQ %d' % calls['T']])
    a, b = _program(L, 'LBL "CALC"')
    return L[:b] + code + L[b:]


def moon_args(L):
    """MOO2: the arguments of a Moon series (ML × MA10: the series' multiples of D M M' F) were computed twice, once
    for the SIN sum and once for the COS sum; now once, kept on the stack (ENTER .. R↓). The same sums in the same
    order: the same results. ML, MCL and MCB (MB has only the SIN sum)."""
    n = 0
    for i in range(len(L) - 18, -1, -1):
        b = L[i:i + 18]
        if (b[0].startswith('RCL "M') and b[1:4] == ['RCL "MA10"', '×', 'SIN'] and b[4] == b[0] and b[6:8] == ['×', 'DOT']
                and b[8].startswith('STO+ ') and b[9:13] == [b[0], 'RCL "MA10"', '×', 'COS'] and b[13] == b[0]
                and b[15:17] == ['×', 'DOT'] and b[17].startswith('STO+ ')):
            L = L[:i] + b[:3] + ['ENTER', 'SIN'] + b[4:9] + ['R↓', 'COS'] + b[13:18] + L[i + 18:]
            n += 1
    assert n in (0, 3), 'navmat: moon_args %d' % n
    return L


def _find(L, blk):
    """The first index of the block blk in L, or -1."""
    k = len(blk)
    return next((i for i in range(len(L) - k + 1) if L[i] == blk[0] and L[i:i + k] == blk), -1)


K_HP = '56203.43862003656238339076909569247'     # 358473400 / 6378.14 (the Moon's parallax factor, deg_rad)
CX = ['RCL× "C1"', 'eˣ']          # X = A (radians) -> X = eˣ(i A) = cos A + i sin A, element by element; C1 = i
CXD = ['RCL× "C2"', 'eˣ']         # A in degrees: C2 = i π / 180 (the firmware's π; deg→rad refuses matrices)


def cexp(L):
    """The series' cos and sin of a whole vector of arguments as one complex eˣ(i A) = cos A + i sin A, then Re / Im:
    the same terms and sums. The firmware computes SIN and COS at 75 digits, eˣ at 39 (more than the 34 a number
    keeps): measured 0.69 s (COS) and 1.05 s (SIN + COS) against 0.47 s and 0.44 s for 30 vectors of 200.
    SER (VSOP87, radians: COS), NUT (degrees: SIN and later COS of NV: NV keeps eˣ), MOO2 (degrees: ML MCL MCB
    SIN and COS, MB SIN). C1 and C2 are made when NAV starts and deleted when it ends (tidy)."""
    n = 0
    old = ['RCL "SV2"', '×', 'COS']
    if _find(L, old) >= 0:
        L = E.cut(L, old, ['RCL "SV2"', '×'] + CX + ['Re']); n += 1
    old = ['RCL "NU"', 'RCL "NV"', '×', 'STO "NV"', 'SIN']
    if _find(L, old) >= 0:
        L = E.cut(L, old, ['RCL "NU"', 'RCL "NV"', '×'] + CXD + ['STO "NV"', 'Im'])
        L = E.cut(L, ['RCL "NV"', 'COS'], ['RCL "NV"', 'Re']); n += 1
    for m, a in (('ML', 'MA10'), ('MCL', 'MA10'), ('MCB', 'MA10')):
        old = ['RCL "%s"' % m, 'RCL "%s"' % a, '×', 'ENTER', 'SIN']
        i = _find(L, old)
        if i >= 0:
            j = L.index('COS', i)
            assert L[j - 1] == 'R↓' and j - i < 14, 'navmat: cexp %s' % m
            L = L[:i + 3] + CXD + ['ENTER', 'Im'] + L[i + 5:j] + ['Re'] + L[j + 1:]; n += 1
    old = ['RCL "MB"', 'RCL "MA7"', '×', 'SIN']
    if _find(L, old) >= 0:
        L = E.cut(L, old, old[:3] + CXD + ['Im']); n += 1
    assert n in (0, 2, 6), 'navmat: cexp %d' % n          # NAVLITTLE: SER and NUT only (no Moon)
    return L


def _f42(L):
    """Free42 listing (texts as XSTR "...")."""
    return any(l.startswith('XSTR "') for l in L)


def _txt(f42):
    return (lambda t: 'XSTR "%s"' % t) if f42 else (lambda t: '"%s"' % t)


def _hdr_match(L, i, txt):
    """The header block of a view at L[i] (date, UT, DR latitude N/S, longitude E/W): (row, time, lat, lon) or None."""
    r = L[i]
    if not re.fullmatch(r'\d+', r) or L[i + 1] != '2' or L[i + 3] != 'XEQ "PDTS"':
        return None
    t = L[i + 2]
    lat, lon = L[i + 24], L[i + 38]
    want = [r, '2', t, 'XEQ "PDTS"', r, '79', t, '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"',
            r, '118', txt('UT'), 'XEQ "PTXS"', r, '143', txt('DR'), 'XEQ "PTXS"', txt('N'), L[i + 23], lat, 'X<0?',
            L[i + 26],
            r, '168', 'RCL' + L[i + 23][3:], 'XEQ "PTXS"', r, '171', lat, 'ABS', 'XEQ "PDMS"',
            txt('E'), L[i + 37], lon, 'X<0?', L[i + 40], r, '238', 'RCL' + L[i + 37][3:], 'XEQ "PTXS"',
            r, '249', lon, 'ABS', 'XEQ "PDMS"']
    ok = (L[i:i + len(want)] == want and all(x.startswith('RCL ') for x in (t, lat, lon))
          and L[i + 23].startswith('STO ') and L[i + 37].startswith('STO ')
          and L[i + 26].startswith('XEQ ') and L[i + 40].startswith('XEQ '))
    return (r, t, lat, lon, len(want)) if ok else None


HDR_C47 = ['LBL "HDR"', 'LocR 05', 'STO R.00', 'R↓', 'STO R.01', 'R↓', 'STO R.02', 'R↓', 'STO R.03',
       'RCL R.00', '2', 'RCL R.01', 'XEQ "PDTS"', 'RCL R.00', '79', 'RCL R.01', '0.5', '+', '1', 'MOD', '24', '×',
       'XEQ "PHMS"', 'RCL R.00', '118', '"UT"', 'XEQ "PTXS"', 'RCL R.00', '143', '"DR"', 'XEQ "PTXS"',
       '"N"', 'STO R.04', 'RCL R.02', 'X≥0?', 'GTO 01', '"S"', 'STO R.04', 'LBL 01',
       'RCL R.00', '168', 'RCL R.04', 'XEQ "PTXS"',
       'RCL R.00', '171', 'RCL R.02', 'ABS', 'XEQ "PDMS"',
       '"E"', 'STO R.04', 'RCL R.03', 'X≥0?', 'GTO 02', '"W"', 'STO R.04', 'LBL 02',
       'RCL R.00', '238', 'RCL R.04', 'XEQ "PTXS"',
       'RCL R.00', '249', 'RCL R.03', 'ABS', 'XEQ "PDMS"', 'RTN', 'END']


def hdr(f42):
    """HDR for the C47 (local registers R.00-R.04) or Free42 (local variables H0-H4 by LSTO: no LocR there)."""
    if not f42:
        return HDR_C47
    out = []
    for l in HDR_C47:
        if l == 'LocR 05':
            continue
        m = re.fullmatch(r'(STO|RCL) R\.0(\d)', l)
        if m:
            l = ('LSTO "H%s"' if m.group(1) == 'STO' else 'RCL "H%s"') % m.group(2)
        elif l.startswith('"'):
            l = 'XSTR ' + l
        out.append(l)
    return out


COMPASS = (('CMN', 'NESWN'), ('CMS', 'SWNES'))
COLS = ('19', '112', '206', '300', '394')


def views(L):
    """Size: the blocks every view repeats, once each as a routine. The header (date, UT, DR, latitude N / S,
    longitude E / W: about 50 steps in NAV and the 5 views) -> RCL lon RCL lat RCL time row XEQ "HDR" (its own
    local registers: no XEQ inside, a called level does not see them). The compass row of the 4 charts (N E S W N, or S W N E S under the south: 20 steps) -> row
    XEQ "CMN" / "CMS": the text routines give back Y = row, so each letter is column, text, XEQ, DROP."""
    f42 = _f42(L)
    txt = _txt(f42)
    n = 0
    i = 0
    while i < len(L):
        m = _hdr_match(L, i, txt)
        if m:
            r, t, lat, lon, k = m
            L = L[:i] + [lon, lat, t, r, 'XEQ "HDR"'] + L[i + k:]
            n += 1
        i += 1
    assert n in (0, 6), 'navmat: views: %d headers' % n
    c = 0
    for name, letters in COMPASS:
        i = 0
        while i < len(L) - 20:
            r = L[i]
            want = [x for col, ch in zip(COLS, letters) for x in (r, col, txt(ch), 'XEQ "PTTY"')]
            if re.fullmatch(r'\d+', r) and L[i:i + 20] == want:
                L = L[:i] + [r, 'XEQ "%s"' % name] + L[i + 20:]
                c += 1
            i += 1
    assert c in (0, 8), 'navmat: views: %d compass rows' % c
    if n:
        L = L + hdr(f42)
    if c:
        for name, letters in COMPASS:
            L = L + ['LBL "%s"' % name] + [x for col, ch in zip(COLS, letters)
                                           for x in (col, txt(ch), 'XEQ "PTTY"', 'DROP')][:-1] + ['RTN', 'END']
    return L


def deg_rad(L):
    """The firmware's rad→deg (3 bytes) in place of × 57.29577… (20 bytes): SUNA, the planets. And the Moon's
    horizontal parallax factor 358473400 × 6378.14 ÷ as one number (358473400 / 6378.14 to 34 digits; C47 only)."""
    old = ['358473400', '×', '6378.14', '÷']
    i = -1 if _f42(L) else _find(L, old)            # Free42 keeps the digits as text: 34 of them cost more
    while i >= 0:
        L = L[:i] + [K_HP, '×'] + L[i + 4:]
        i = _find(L, old)
    for old, new in ((['57.295779513082320876798154814105', '×'], ['rad→deg']),
                     (['-57.295779513082320876798154814105', '×'], ['rad→deg', 'CHS']),
                     (['57.29577951308232', '×'], ['rad→deg'])):
        if '\n'.join(['', *old, '']) in '\n'.join(['', *L, '']):        # (NAVLITTLE has no planets)
            L = E.cut(L, old, new)
    return L


_TESTSUBS = set()          # Free42 routines that return by RTNYES / RTNNO: XEQ of them is a test (RTNNO skips a line)


def _testsubs(L):
    """The global labels whose program has RTNYES or RTNNO."""
    out, cur = set(), []
    for l in L:
        if l.startswith('LBL "'):
            cur.append(l[5:-1])
        if l in ('RTNYES', 'RTNNO'):
            out.update(cur)
        if l == 'END':
            cur = []
    return out


def _test(op, l=None):
    """A line that skips the next one: a test, DSE / ISG, or (Free42) XEQ of a routine ending in RTNYES / RTNNO."""
    if l is not None and l.startswith('XEQ "') and l[5:-1] in _TESTSUBS:
        return True
    return op.endswith('?') or op in ('DSE', 'ISG') or op.startswith(('FS?', 'FC?'))


def reach(L, entries=('NAV', 'INIT')):
    """Lines a run from NAV can reach: fall-through, GTO / XEQ (local, named, IND: every label of the program, or by
    name), both ways of a test; global labels named in a text (XEQ IND of a name) count as entries."""
    _TESTSUBS.clear()
    _TESTSUBS.update(_testsubs(L))
    prog, p = [], 0
    for l in L:
        prog.append(p)
        p += l == 'END'
    glob, loc = {}, {}
    for i, l in enumerate(L):
        if l.startswith('LBL "'):
            glob[l[5:-1]] = i
        elif l.startswith('LBL '):
            loc[(prog[i], l[4:])] = i
    texts = {l.strip('"') for l in L if l.startswith('"')}
    todo = [glob[e] for e in entries if e in glob] + [i for n, i in glob.items() if n in texts]
    seen = set()
    while todo:
        i = todo.pop()
        if i in seen or i >= len(L) or L[i] == 'END':
            continue
        seen.add(i)
        op, _, arg = L[i].partition(' ')
        go = True
        if op in ('GTO', 'XEQ'):
            if arg.startswith('IND '):
                todo += ([j for (q, n), j in loc.items() if q == prog[i]] if not arg[4:].startswith('"')
                         else list(glob.values()))
            elif arg.startswith('"'):
                todo.append(glob[arg[1:-1]])
            else:
                todo.append(loc[(prog[i], arg)])
            go = op == 'XEQ'
        if op in ('RTN', 'STOP'):
            go = False
        if go:
            todo.append(i + 1)
        if _test(op, L[i]):
            todo.append(i + 2)
    return seen


KEEP_ENTRIES = ('NAV', 'INIT')            # (DHA, the inverse of HCZ, is a separate program: programs/CHZ.txt)


def strip(L, entries=None):
    """Size: no REM (comments cost bytes on the calculator) and no code NAV can never reach (unused entries such as
    STAR, PLAN, CHZ, DHA, HCZ0, CTWA / CTWP). A line right after a test is never removed (the test skips it)."""
    r = reach(L, entries or KEEP_ENTRIES)
    out = []
    for i, l in enumerate(L):
        drop = l.startswith('REM') or (i not in r and l != 'END')
        if drop and i > 0 and _test(L[i - 1].split(' ')[0], L[i - 1]) and (i - 1) in r:
            drop = False
        if not drop:
            out.append(l)
    return out


def nbytes(l):
    """About what a step costs in a .p47 program (measured with rejig: a number of 15+ characters is a 34-digit real,
    18 bytes; shorter ones and texts: their length + 3; RCL "name": 3 + length; XEQ "N..": 6; local labels 2)."""
    if re.fullmatch(r'-?[\d.]+(E-?\d+)?', l):
        return 18 if len(l) >= 14 else len(l) + 3
    if re.fullmatch(r'[01]+#2', l):
        return len(l) + 2
    if l.startswith('"'):
        return len(l[1:-1].encode('utf-8')) + 3
    op, _, arg = l.partition(' ')
    if op in ('XEQ', 'GTO') and arg.startswith('"'):
        return 6
    if op == 'LBL' and arg.startswith('"'):
        return 5
    if arg.startswith('IND "') or arg.startswith('"'):
        return 3 + len(arg.split('"')[1].encode('utf-8')) + (1 if arg.startswith('IND') else 0)
    return 2 if arg else 1


NOGO = ('LBL', 'END', 'RTN', 'GTO', 'STOP', 'LocR', 'LSTO', 'REM')


def outline(L, name='OUT', min_save=8, max_steps=10 ** 6, log=None):
    """Size: a run of steps that comes back (3 to 60 steps) becomes a subroutine called by XEQ: a local label when
    the copies are in one program (XEQ nn, 2 bytes), else a new named program (XEQ "N..", 6 bytes). Never in a block:
    labels, RTN, GTO, END, local registers (an XEQ starts a level without them), a test as its last step, XEQ IND or
    a local XEQ when it moves to another program; a copy right after a test stays. The local bodies go before the
    program's END, after an RTN when the code before could run into END (END returns like RTN). Greedy, the best
    saving first."""
    L = list(L)
    _TESTSUBS.clear()
    _TESTSUBS.update(_testsubs(L))
    k_new = 0
    for _ in range(max_steps):
        prog, p = [], 0
        for l in L:
            prog.append(p)
            p += l == 'END'
        bad = [l.split(' ')[0] in NOGO or ' R.' in l or l.startswith('XEQ IND') or l.startswith('INPUT') for l in L]
        loc = [l.startswith(('XEQ ', 'KEY?')) and not l.startswith('XEQ "') for l in L]   # local only
        cost = [nbytes(l) for l in L]
        best = None
        for k in range(3, 61):
            seen = {}
            run_bad = 0
            for i in range(len(L) - k + 1):
                if i == 0:
                    run_bad = sum(bad[:k])
                else:
                    run_bad += bad[i + k - 1] - bad[i - 1]
                if run_bad or _test(L[i + k - 1].split(' ')[0], L[i + k - 1]) or \
                        (i and _test(L[i - 1].split(' ')[0], L[i - 1])):
                    continue
                seen.setdefault(tuple(L[i:i + k]), []).append(i)
            for blk, pos in seen.items():
                if len(pos) < 2:
                    continue
                occ, last = [], -1
                for x in pos:
                    if x >= last:
                        occ.append(x); last = x + k
                b = sum(cost[x] for x in range(occ[0], occ[0] + k))
                byp = {}
                for x in occ:
                    byp.setdefault(prog[x], []).append(x)
                for q, xs in byp.items():                     # local: the copies of one program
                    if len(xs) >= 2:
                        save = (len(xs) - 1) * b - len(xs) * 2 - 3
                        if save >= min_save and (best is None or save > best[0]):
                            best = (save, 'local', blk, xs, q)
                local_only = any(loc[x] for x in range(occ[0], occ[0] + k))
                if len(byp) >= 2 and not local_only:
                    save = (len(occ) - 1) * b - len(occ) * 6 - 8
                    if save >= min_save and (best is None or save > best[0]):
                        best = (save, 'global', blk, occ, None)
        if best is None:
            return L
        save, kind, blk, occ, q = best
        k = len(blk)
        if log is not None:
            log.append((save, kind, blk, list(occ)))
        if kind == 'local':
            a = prog.index(q)
            e = a + prog[a:].count(q) - 1                     # the END of program q
            used = {int(x[4:]) for x in L[a:e] if re.fullmatch(r'LBL \d+', x)}
            free = [n for n in range(99, 0, -1) if n not in used]
            if not free:
                bad_prog = q                                  # (no free label: skip this program next time)
                return L
            lab = free[0]
            call = ['XEQ %02d' % lab]
            body = ['LBL %02d' % lab] + list(blk) + ['RTN']
            for x in sorted(occ, reverse=True):
                L[x:x + k] = call
            e = L.index('END', a)
            # END returns like RTN: code that ran into END must not run into the new body
            ends = L[e - 1].split(' ')[0] in ('RTN', 'GTO') and not _test(L[e - 2].split(' ')[0], L[e - 2])
            L = L[:e] + ([] if ends else ['RTN']) + body + L[e:]
        else:
            k_new += 1
            g = '%s%d' % (name, k_new)
            for x in sorted(occ, reverse=True):
                L[x:x + k] = ['XEQ "%s"' % g]
            L = L + ['LBL "%s"' % g] + list(blk) + ['RTN', 'END']
    return L


# the passes in use (ALM_PASSES=deg,tget,ceq,hcz,strip,outline to try a subset)
PASSES = os.environ.get('ALM_PASSES', 'deg,tget,ceq,hcz,margs,cexp,views,strip,consts,names,outline').split(',')


def c47(L):
    """The C47 matrix rewrites, in order (applied to the named listing before the registers are renumbered)."""
    for k, fn in (('deg', deg_rad), ('ceq', ceq), ('tget', tget), ('hcz', hcz_vec), ('margs', moon_args), ('cexp', cexp), ('views', views)):
        if k in PASSES:
            L = fn(L)
    return tidy(L)


NUM = re.compile(r'-?[\d.]+(E-?\d+)?')


def consts(L, min_gain=8, top=98):
    """Size: the numbers the program writes most often (1 2 360 0 16 ...) in registers after the program's own
    (R00..Rk-1, renumbered by regalloc): NAV stores them once after it has saved your registers in its local
    registers (LocR, at most 99: R00..R98) and gives your values back at the end. RCL nn is 2 bytes, a number its
    length + 3. A number is taken when it saves min_gain bytes after its own cost (the number and STO once, 8 bytes
    of save and restore). RCL after ENTER or CLx works like a number (the firmware's ENTER keeps the stack lift
    as it is): the same stack. One line for one line: a test still skips the same step."""
    i = L.index('LBL "NAV"')
    k = int(L[i + 1].split()[1])
    assert L[i + 1] == 'LocR %d' % k and L[i + 2:i + 2 + 2 * k:2] == ['RCL %02d' % r for r in range(k)]
    save_end = i + 2 + 2 * k
    rest = L.index('RCL R.00', save_end)
    assert L[rest:rest + 2 * k:2] == ['RCL R.%02d' % r for r in range(k)] and L[rest + 2 * k] == 'CLSTK'
    zone = set(range(i, save_end)) | set(range(rest, rest + 2 * k + 1))
    for e in KEEP_ENTRIES[2:]:                     # other entries that run without NAV keep their numbers
        if 'LBL "%s"' % e in L:
            a = L.index('LBL "%s"' % e)
            zone |= set(range(a, L.index('END', a)))
            assert not any(l.startswith(('XEQ', 'GTO "')) for l in L[a:L.index('END', a)]), 'navmat: %s calls out' % e
    count = {}
    for j, l in enumerate(L):
        if j not in zone and NUM.fullmatch(l):
            count[l] = count.get(l, 0) + 1
    gain = sorted(((n * (nbytes(v) - 2) - nbytes(v) - 2 - 8, v) for v, n in count.items()), reverse=True)
    pick = [v for g, v in gain if g >= min_gain][:top + 1 - k]
    if not pick:
        return L
    reg = {v: '%02d' % (k + j) for j, v in enumerate(pick)}
    m = k + len(pick)
    out = [('RCL ' + reg[l] if j not in zone and l in reg else l) for j, l in enumerate(L)]
    out[i + 1] = 'LocR %d' % m
    restore = [x for r in range(k, m) for x in ('RCL R.%02d' % r, 'STO %02d' % r)]
    out[rest + 2 * k:rest + 2 * k] = restore
    setup = [x for v in pick for x in (v, 'STO ' + reg[v])]
    save = [x for r in range(k, m) for x in ('RCL %02d' % r, 'STO R.%02d' % r)]
    return out[:save_end] + save + setup + out[save_end:]


KEEP_NAMES = ('DATE', 'UTC', 'LAT', 'LON', 'TZ')        # the user's inputs


def names(L, external=(), letters='VWQUHGFPMB'):
    """The variables NAV makes for itself get short names of a letter and a digit, like the labels (V0 .. V9, W0 ..,
    the most used first): RCL "V1" is 5 bytes, RCL "KQO3" 7. Not renamed: the user's inputs, the matrices and
    variables that NAVINIT and the TBL programs make (external), and names already of that form."""
    ref = {}
    for l in L:
        m = re.fullmatch(r'([^"]+) (IND )?"([^"]+)"', l)
        if m and not m.group(1).startswith(('XEQ', 'GTO', 'LBL', 'XSTR')):
            ref[m.group(3)] = ref.get(m.group(3), 0) + 1
    texts = {l.split('"')[1] for l in L if (l.startswith('"') or l.startswith('XSTR "')) and l.endswith('"')}
    own = [n for n, c in sorted(ref.items(), key=lambda x: -x[1])
           if n not in external and n not in KEEP_NAMES and n not in texts and not re.fullmatch(r'[A-Z]\d+', n)]
    taken = set(ref) | set(external)
    pool = [c + str(d) for c in letters for d in range(10) if c + str(d) not in taken]
    assert len(pool) >= len(own), 'navmat: names: too few short names'
    new = dict(zip(own, pool))

    def ren(l):
        m = re.fullmatch(r'([^"]+ (IND )?)"([^"]+)"', l)
        if m and m.group(3) in new and not m.group(1).startswith(('XEQ', 'GTO', 'LBL', 'XSTR')):
            return '%s"%s"' % (m.group(1), new[m.group(3)])
        return l
    return [ren(l) for l in L]


def external_names():
    """The names NAVINIT and the TBL programs use (build/NAVINIT_*.txt, TBL_1)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = set()
    for f in ('NAVINIT_FULL.txt', 'NAVINIT_FAST.txt', 'TBL_1.txt', os.path.join('dm42', 'NAVINIT_LITTLE.txt'),
              os.path.join('free42', 'NAVINIT_FULL.txt'), os.path.join('free42', 'NAVINIT_FAST.txt'),
              os.path.join('free42', 'NAVINIT_LITTLE.txt'), os.path.join('free42', 'TBL_1.txt')):
        p = os.path.join(root, 'build', f)
        if os.path.exists(p):
            out |= set(re.findall(r'"([^"]+)"', open(p, encoding='utf-8').read()))
    return out


# Free42 names of the commands the passes insert (none of them is in a Free42 listing before)
F42_OPS = {'rad→deg': ['→DEG'], 'M.GETM': ['GETM'], 'M.PUTM': ['PUTM'], 'STOSEQ': ['STOEL', 'J+'],
           'RCLSEQ': ['RCLEL', 'J+'], 'x²': ['X↑2']}


def f42ops(L):
    out = []
    for i, l in enumerate(L):
        if l.startswith('DELITM "'):
            out.append('CLV' + l[6:])
            continue
        new = F42_OPS.get(l, [l])
        assert len(new) == 1 or not _test(L[i - 1].split(' ')[0]), 'navmat: f42ops after a test: %s' % l
        out += new
    return out


def free42(L, little=False):
    """Free42 NAVFULL (before navhopt.f42_regs): deg, tget, hcz, margs, views. Not ceq (its gain on the C47 is the
    element copies the C47 makes and Free42 does not; on Free42 it would need POLAR / RECT around COMPLEX) and not
    cexp (Free42 has no Re / Im: an extra stack level on a 4-level stack, and no measured gain on the DM42)."""
    passes = ((('deg', deg_rad), ('tget', tget), ('hcz', hcz_vec_little)) if little else
              (('deg', deg_rad), ('tget', tget), ('hcz', hcz_vec), ('margs', moon_args), ('views', views)))
    for k, fn in passes:
        if k in PASSES:
            L = fn(L)
    return f42ops(tidy(L))


def nbytes42(l):
    """About what a step costs in a Free42 .raw program (HP-42S coding: a number one byte per character and one
    more; a text 1 + length; RCL / STO 00-15 one byte, others 2; named arguments 2 + length; local XEQ 3)."""
    if re.fullmatch(r'-?[\d.]+(E-?\d+)?', l):
        return len(l) + 1
    if l.startswith('XSTR "'):
        return len(l[6:-1].encode('utf-8')) + 2
    if l.startswith('"'):
        return len(l[1:-1].encode('utf-8')) + 1
    op, _, arg = l.partition(' ')
    if op == 'LBL' and arg.startswith('"'):
        return 4 + len(arg) - 2
    if arg.startswith('"') or arg.startswith('IND "'):
        return 2 + len(arg.split('"')[1].encode('utf-8'))
    if op in ('RCL', 'STO') and arg.isdigit():
        return 1 if int(arg) < 16 else 2
    if op in ('XEQ', 'GTO') and arg.isdigit():
        return 3 if op == 'XEQ' else (1 if int(arg) < 15 else 3)
    if op == 'LBL' and arg.isdigit():
        return 1 if int(arg) < 15 else 2
    return 2 if arg else 1


def consts42(L, min_gain=4, top=99):
    """Free42: as consts, the numbers in the registers after the program's own: SIZE k -> SIZE k + m (NAV keeps
    the user's whole REGS in NBAK and STO "REGS" gives them back with the SIZE: no code for the save)."""
    i = L.index('LBL "NAV"')
    e = L.index('END', i)
    sz = [j for j in range(i, e) if re.fullmatch(r'SIZE \d+', L[j])]
    assert len(sz) == 1, 'navmat: consts42: SIZE'
    k = int(L[sz[0]].split()[1])
    back = L.index('STO "REGS"', sz[0])
    zone = set(range(i, sz[0] + 1)) | set(range(back - 3, e))
    for en in KEEP_ENTRIES[2:]:
        if 'LBL "%s"' % en in L:
            a = L.index('LBL "%s"' % en)
            zone |= set(range(a, L.index('END', a)))
    count = {}
    for j, l in enumerate(L):
        if j not in zone and NUM.fullmatch(l):
            count[l] = count.get(l, 0) + 1
    gain = sorted(((n * (nbytes42(v) - 2) - nbytes42(v) - 2, v) for v, n in count.items()), reverse=True)
    pick = [v for g, v in gain if g >= min_gain][:top + 1 - k]
    if not pick:
        return L
    reg = {v: '%02d' % (k + j) for j, v in enumerate(pick)}
    out = [('RCL ' + reg[l] if j not in zone and l in reg else l) for j, l in enumerate(L)]
    out[sz[0]] = 'SIZE %d' % (k + len(pick))
    setup = [x for v in pick for x in (v, 'STO ' + reg[v])]
    return out[:sz[0] + 1] + setup + out[sz[0] + 1:]


def size42(L):
    """Free42 size passes (after navhopt.f42_regs)."""
    global nbytes
    if 'strip' in PASSES:
        L = strip(L)
    if 'consts' in PASSES:
        L = consts42(L)
    if 'names' in PASSES:
        L = names(L, external_names() | {'REGS', 'NBAK', 'GrMod', 'RefLCD'})
    if 'outline' in PASSES:
        keep, nbytes = nbytes, nbytes42
        try:
            L = outline(L, min_save=4)
        finally:
            nbytes = keep
    return L


def shrink(L, entries, f42=False):
    """strip and outline for another program (MOON47): entries are its global labels run by the user."""
    global nbytes
    L = strip(L, entries)
    keep = nbytes
    if f42:
        nbytes = nbytes42
    try:
        return outline(L, min_save=4 if f42 else 8)
    finally:
        nbytes = keep


def size(L):
    """The size passes (after the registers are renumbered)."""
    if 'names' in PASSES:
        L = names(L, external_names())
    if 'strip' in PASSES:
        L = strip(L)
    if 'consts' in PASSES:
        L = consts(L)
    if 'outline' in PASSES:
        L = outline(L)
    return L
