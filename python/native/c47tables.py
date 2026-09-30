"""c47tables.py - the almanac tables (Method B) for the native Python version.

Reads a table program TBL_5.txt / TBL_1.txt / TBL.txt (written by tools/almanac/tab2c47.py, the same file
that is loaded on the C47) and evaluates it exactly like TGET does on the calculator.
"""
import os, re
from c47astro import dsin

BODY = {0: 'TSU', 1: 'TVE', 2: 'TMA', 3: 'TJU', 4: 'TSA', 5: 'TMO', 6: 'TAR'}
KIND = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 0}        # 0 GHA only, 1 + Dec, 2 + HP


class Tables:
    def __init__(self, path):
        self.path = path
        self.mats = {}
        self.period = ''
        name = None
        with open(path, encoding='utf-8') as fh:
            lines = [l.strip() for l in fh if l.strip()]
        for i, l in enumerate(lines):
            m = re.fullmatch(r'INDEX "(\w+)"', l)
            if m:
                name = m.group(1)
                rows, cols = int(lines[i - 5]), int(lines[i - 3])
                self.mats[name] = {'rows': rows, 'cols': cols, 'v': []}
            elif name and re.fullmatch(r'-?[\d.]+(E-?\d+)?', l) and lines[i + 1] == 'STOEL':
                self.mats[name]['v'].append(float(l))
            elif l.startswith('"TBL'):
                self.period = l.strip('"')
        for n, m in self.mats.items():
            v = m['v']
            if len(v) != m['rows'] * m['cols']:
                raise ValueError('%s: matrix %s incomplete' % (path, n))
            m['m'] = [v[r * m['cols']:(r + 1) * m['cols']] for r in range(m['rows'])]

    def get(self, j, body):
        """TGET. Returns (gha, dec[, hp, sd]) or None outside the table."""
        M = self.mats[BODY[body]]['m']
        j0, span, nb, nt = M[0][0], M[0][1], M[0][2], int(M[0][3])
        q = (j - j0) / span
        if q < 0:
            return None
        k = int(q)
        if nb <= k:
            return None
        x = ((j - j0) - k * span) * 2 / span - 1
        row = M[k + 1]

        def cheb(c, n):                       # c = first column (1-based), n terms
            b1 = b2 = 0.0
            for col in range(c + n - 1, c, -1):
                b1, b2 = (row[col - 1] + (x * b1) * 2) - b2, b1
            return (row[c - 1] + x * b1) - b2

        gha = cheb(1, nt) % 360
        kind = KIND[body]
        if kind == 0:
            return gha, 0.0
        dec = cheb(nt + 1, nt)
        if kind == 1:
            return gha, dec
        hp = cheb(2 * nt + 1, 4)
        sd = ((dsin(hp / 60) * 358473400) / 6378.14) / 60
        return gha, dec, hp, sd


def find(start=None):
    """The almanac tables, longest period first: TBL_5.txt, TBL_1.txt or TBL.txt next to this
    file, then ../../build/TBL_5.txt, ../../build/TBL_1.txt, ../../programs/TBL.txt (4 months).
    None if not found."""
    here = start or os.path.dirname(os.path.abspath(__file__))
    top = os.path.join(here, '..', '..')
    for p in ([os.path.join(here, n) for n in ('TBL_5.txt', 'TBL_1.txt', 'TBL.txt')] +
              [os.path.join(top, 'build', 'TBL_5.txt'), os.path.join(top, 'build', 'TBL_1.txt'),
               os.path.join(top, 'programs', 'TBL.txt')]):
        if os.path.exists(p):
            return os.path.normpath(p)
    return None
