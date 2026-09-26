#!/usr/bin/env python3
"""tab2c47.py - convert the Chebyshev almanac tables into a C47 program.

Reads the coefficient tables (the spreadsheet docs/C47_almanac_coefficients_*.xlsx,
or a CSV written by c47_almanac_generator.py) and writes a C47 program (plain text,
one command per line) that builds one matrix per body. Run that program once on the
calculator; TGET then gives GHA and Dec (Moon also HP and SD) for any time inside
the period.

  python3 tab2c47.py 2026-09-26 2027-01-31
  python3 tab2c47.py 2026-09-26 2027-01-31 --xlsx ../../docs/C47_almanac_coefficients_2026-2027.xlsx
  python3 tab2c47.py 2028-01-01 2028-03-31 --csv tables_2028.csv
  -> TBL.txt   (convert with: rejig TBL.txt -o TBL.p47)

Matrices built (row 1 = header: JD of first block at 0h UT1, block length in days,
number of blocks, number of terms; then one row per block):
  TSU Sun      GHA c0-c4, Dec c0-c4                         (8-day blocks)
  TVE TMA TJU TSA  Venus, Mars, Jupiter, Saturn: same layout (8-day blocks)
  TMO Moon     GHA c0-c5, Dec c0-c5, HP c0-c3               (1-day blocks)
  TAR Aries    GHA c0-c4                                    (8-day blocks)
Value = Chebyshev series in x = 2 t / span - 1 (t = time since block start);
GHA: take MOD 360; Dec in degrees; HP in arcminutes.
"""
import argparse, csv, datetime, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_XLSX = os.path.join(HERE, '..', '..', 'docs', 'C47_almanac_coefficients_2026-2027.xlsx')

# body -> (matrix name, spreadsheet sheet, generator CSV name, quantities, terms per quantity)
BODIES = [('TSU', 'Sun', 'sun', ('gha', 'dec'), 5),
          ('TVE', 'Venus', 'venus', ('gha', 'dec'), 5),
          ('TMA', 'Mars', 'mars', ('gha', 'dec'), 5),
          ('TJU', 'Jupiter', 'jupiter', ('gha', 'dec'), 5),
          ('TSA', 'Saturn', 'saturn', ('gha', 'dec'), 5),
          ('TMO', 'Moon', 'moon', ('gha', 'dec', 'hp'), 6),
          ('TAR', 'Aries', 'aries', ('gha',), 5)]
HP_TERMS = 4


def jd0(d):
    """JD at 0h UT of a date (same formula as the suite)."""
    y, m, dd = d.year, d.month, d.day
    if m <= 2:
        y -= 1; m += 12
    a = y // 100; b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + dd + b - 1524.5


def num(v):
    v = float(v)
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    s = ('%.10g' % v).replace('e', 'E').replace('E+', 'E')
    return s


def read_xlsx(path):
    import openpyxl                                    # pip install openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = {}
    for mat, sheet, _, qty, n in BODIES:
        rows = list(wb[sheet].iter_rows(values_only=True))
        head = [str(h) for h in rows[0]]
        blocks = []
        for r in rows[1:]:
            if not r or r[0] is None:
                continue
            start = datetime.date.fromisoformat(str(r[0])[:10])
            span_h = float(r[1])
            coef = []
            for q, nn in zip(qty, [n] * len(qty)):
                label = {'gha': 'GHA', 'dec': 'Dec', 'hp': 'HP'}[q]
                cnt = HP_TERMS if q == 'hp' else nn
                for k in range(cnt):
                    col = head.index('%s c%d' % (label, k))
                    coef.append(float(r[col] or 0))
            blocks.append((start, span_h, coef))
        out[mat] = blocks
    return out


def read_csv(path):
    rows = {}
    with open(path, newline='') as fh:
        for r in csv.DictReader(fh):
            rows.setdefault((r['body'], r['start_0h_UT1']), {})[r['quantity']] = r
    out = {}
    for mat, _, body, qty, n in BODIES:
        blocks = []
        for (b, start), q in sorted(rows.items()):
            if b != body:
                continue
            coef = []
            for qq in qty:
                cnt = HP_TERMS if qq == 'hp' else n
                coef += [float(q[qq].get('c%d' % k) or 0) for k in range(cnt)]
            blocks.append((datetime.date.fromisoformat(start), float(q[qty[0]]['span_h']), coef))
        out[mat] = blocks
    return out


def select(blocks, d0, d1):
    """Contiguous blocks covering the dates d0..d1 (inclusive)."""
    sel = []
    for start, span_h, coef in blocks:
        end = start + datetime.timedelta(hours=span_h)
        if end > d0 and start <= d1:
            sel.append((start, span_h, coef))
    for a, b in zip(sel, sel[1:]):
        if a[0] + datetime.timedelta(hours=a[1]) != b[0]:
            raise ValueError('gap in the table between %s and %s' % (a[0], b[0]))
    return sel


def program(tables, d0, d1, label):
    L = ['LBL "%s"' % label, 'DEG']
    count = 0
    for mat, _, _, qty, n in BODIES:
        blocks = select(tables[mat], d0, d1)
        if not blocks:
            raise ValueError('%s: no blocks for %s .. %s' % (mat, d0, d1))
        ncol = len(blocks[0][2])
        span_d = blocks[0][1] / 24.0
        L += [str(len(blocks) + 1), 'ENTER', str(ncol), 'NEWMAT', 'STO "%s"' % mat, 'INDEX "%s"' % mat]
        header = [jd0(blocks[0][0]), span_d, len(blocks), n] + [0] * (ncol - 4)
        vals = header + [v for b in blocks for v in b[2]]
        for i, v in enumerate(vals):
            L += [num(v), 'STOEL']
            if i < len(vals) - 1:
                L.append('J+')
        count += len(vals)
        last = blocks[-1][0] + datetime.timedelta(hours=blocks[-1][1])
        sys.stderr.write('%s  %2d blocks  %s .. %s  (%d numbers)\n' %
                         (mat, len(blocks), blocks[0][0], last, len(vals)))
    L += ['SF 10',                     # flag 10: tables loaded (CF 10 = use the series)
          '"TBL %s TO %s"' % (d0.strftime('%d-%m-%Y'), d1.strftime('%d-%m-%Y')), 'RTN', 'END']
    sys.stderr.write('total %d numbers, %d program lines\n' % (count, len(L)))
    return L


def main():
    ap = argparse.ArgumentParser(description='Chebyshev almanac tables -> C47 program')
    ap.add_argument('start', help='first date YYYY-MM-DD')
    ap.add_argument('end', help='last date YYYY-MM-DD')
    ap.add_argument('--xlsx', help='coefficient spreadsheet (default: the one in docs/)')
    ap.add_argument('--csv', help='CSV from c47_almanac_generator.py instead of the spreadsheet')
    ap.add_argument('--label', default='TBL', help='program label (default TBL)')
    ap.add_argument('-o', '--out', default='TBL.txt', help='output file (default TBL.txt)')
    a = ap.parse_args()
    d0, d1 = datetime.date.fromisoformat(a.start), datetime.date.fromisoformat(a.end)
    tables = read_csv(a.csv) if a.csv else read_xlsx(a.xlsx or DEFAULT_XLSX)
    L = program(tables, d0, d1, a.label)
    with open(a.out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    sys.stderr.write('written %s\n' % a.out)


if __name__ == '__main__':
    main()
