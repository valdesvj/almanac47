#!/usr/bin/env python3
"""fastseries.py - FAST planetary series for a limited period (default 5 years).

The FULL series (VSOP87D truncated, matrices from MATA and MATP) are valid 2000-2050.
Over a few years every slow effect (periods of decades to centuries, secular terms) is
a smooth curve, so a quadratic plus the short-period terms describes each series with far
fewer terms. This script fits, for the period asked:

  Earth L B R (used by SUNA as VL VB VR and by PLAN as EEL EEB EER) and
  Venus, Mars, Jupiter, Saturn L B R

to the FULL series, and writes

  MATF.txt          C47 program: XEQ "MATF" builds the FAST matrices (same names as the
                    FULL ones, so SUNA and PLAN need no change). Run it instead of MATA/MATP.
  fast_series.json  the same coefficients for the Python version (c47pc.py --fast)

Each series matrix has a header row [number of terms, 0, 0, 0] (VL: [terms, first JD, end JD,
0]), then one row per term
(30 + power of tau, A, B, C): A * tau^power * cos(B + C tau), units 1E-8 (rad or au),
tau = Julian millennia TT from J2000 - the format of the FULL matrices.

  python3 fastseries.py 2026 5          -> MATF.txt, fast_series.json (2026-01-01 .. 2030-12-31)

The result is checked against the FULL series; check the final GHA/Dec against JPL
(tools/almanac/README.md). A new set is needed for every period.
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'python', 'native'))
import c47data as D                                   # noqa: E402

SERIES = ['EEL', 'EEB', 'EER', 'VNL', 'VNB', 'VNR', 'MAL', 'MAB', 'MAR',
          'JUL', 'JUB', 'JUR', 'SAL', 'SAB', 'SAR']
# tolerance of each fit, 1E-8 units: angles 0.02' (5.8E-6 rad), distances 1.5E-6 au
# (0.02' seen from the Earth for Venus at inferior conjunction)
TOL = {'L': 580.0, 'B': 580.0, 'R': 150.0}
# distances of the outer planets: 0.02' seen from the Earth allows more (au from the Earth)
TOL_R = {'EER': 150.0, 'VNR': 150.0, 'MAR': 200.0, 'JUR': 2000.0, 'SAR': 4000.0}


def evalser(rows, tau):
    s = np.zeros_like(tau)
    for n, A, B, C in rows:
        s += A * tau ** n * np.cos(B + C * tau)
    return s


def fit(rows, tau0, span, tol):
    tau = np.linspace(tau0, tau0 + span, 4000)
    truth = evalser(rows, tau)
    cand = sorted([(abs(A) * 0.03 ** n, C) for n, A, B, C in rows if C != 0], reverse=True)
    freqs = []
    for _, C in cand:
        if all(abs(C - f) > 1e-9 for f in freqs):
            freqs.append(C)
    x = tau
    for N in range(len(freqs) + 1):
        cols = [x ** 0, x, x ** 2]
        for C in freqs[:N]:
            cols += [np.cos(C * tau), np.sin(C * tau)]
        M = np.array(cols).T
        coef, *_ = np.linalg.lstsq(M, truth, rcond=None)
        err = float(np.max(np.abs(M @ coef - truth)))
        if err < tol:
            out = [(0, coef[0], 0.0, 0.0), (1, coef[1], 0.0, 0.0), (2, coef[2], 0.0, 0.0)]
            for k, C in enumerate(freqs[:N]):
                c, s = coef[3 + 2 * k], coef[4 + 2 * k]
                out.append((0, math.hypot(c, s), -math.atan2(s, c), C))
            return out, err
    return [(n, A, B, C) for n, A, B, C in rows], 0.0     # no gain: keep the FULL terms


def num(v):
    t = ('%.15g' % v).replace('e', 'E').replace('E+', 'E')
    return t.replace('E-0', 'E-').replace('E0', 'E')


def jd0(y):
    import c47astro
    return c47astro.jd(y, 1, 1, 0.0)


def main():
    ap = argparse.ArgumentParser(description='FAST series for a limited period')
    ap.add_argument('start', type=int, nargs='?', default=2026, help='first year (1 January)')
    ap.add_argument('years', type=int, nargs='?', default=5, help='number of years (default 5)')
    ap.add_argument('-o', '--out', default=os.path.join(ROOT, 'programs', 'MATF.txt'))
    ap.add_argument('--json', default=os.path.join(ROOT, 'python', 'native', 'fast_series.json'))
    a = ap.parse_args()
    j0 = jd0(a.start)
    j1 = jd0(a.start + a.years)
    tau0 = (j0 - 2451545.0) / 365250.0 - 0.001        # a margin of about 1 year before and after
    span = (j1 - j0) / 365250.0 + 0.002
    fitted, total_old, total_new = {}, 0, 0
    for name in SERIES:
        rows = getattr(D, name)
        new, err = fit(rows, tau0, span, TOL_R.get(name, TOL[name[-1]]))
        if len(new) >= len(rows):
            new, err = [tuple(r) for r in rows], 0.0
        fitted[name] = new
        total_old += len(rows); total_new += len(new)
        sys.stderr.write('%s %4d -> %3d terms (max %.2f E-8)\n' % (name, len(rows), len(new), err))
    fitted['VL'], fitted['VB'], fitted['VR'] = fitted['EEL'], fitted['EEB'], fitted['EER']
    sys.stderr.write('total %d -> %d terms\n' % (total_old, total_new))
    period = '%d-%d' % (a.start, a.start + a.years - 1)
    L = ['LBL "MATF"']
    for name in ['VL', 'VB', 'VR'] + SERIES:
        rows = fitted[name]
        L += [str(len(rows) + 1), 'ENTER', '4', 'NEWMAT', 'STO "%s"' % name, 'INDEX "%s"' % name,
              str(len(rows)), 'STOEL', 'J+']
        # VL header: first and last JD of the period (SUNA sets flag 12 outside it: X on the screens)
        L += ([num(j0), 'STOEL', 'J+', num(j1), 'STOEL', 'J+'] if name == 'VL' else ['0', 'STOEL', 'J+', '0', 'STOEL', 'J+'])
        L += ['0', 'STOEL', 'J+']
        vals = [v for n, A, B, C in rows for v in (30 + n, A, B, C)]
        for i, v in enumerate(vals):
            L += [num(v) if isinstance(v, float) else str(v), 'STOEL']
            if i < len(vals) - 1:
                L.append('J+')
    L += ['"FAST SERIES %s"' % period, 'RTN', 'END']
    with open(a.out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    with open(a.json, 'w') as fh:
        json.dump({'period': period, 'jd': [j0, j1], 'series': {k: [list(r) for r in v] for k, v in fitted.items()}}, fh)
    sys.stderr.write('written %s (%d lines), %s\n' % (a.out, len(L), a.json))


if __name__ == '__main__':
    main()
