#!/usr/bin/env python3
"""navopt.py - faster drawing and text for the NAV builds (build_navfull.py applies it).

The programs in programs/ stay as they are (they are the reference the tests compare with);
the NAV files get these rewrites:

  fonts(L)   PTXS / PTXT glyphs: a column equal to the one just drawn is only AGRAPH 32
             (the pattern is still in R32 and AGRAPH moves one column on): 1 step instead of 4
  phls(L)    PHLS (horizontal line): 400 px or more is one PIXEL with a negative row
             (the C47's full-width line) instead of 400 AGRAPH
  pdts(L)    PDTS (date on the screen): J→ⅅℸ, DAY, MONTH, YEAR (the calculator's own calendar)
  stxt(L)    STXT (numbers to text): numbers appended with αIP and signs with x→α straight into
             the string in R38 (no digit-by-digit labels once the string exists); SDAT with J→ⅅℸ
"""


def fonts(L):
    out, last, drawn = [], None, False
    i = 0
    while i < len(L):
        l = L[i]
        if l.startswith('LBL'):
            last, drawn = None, False
        if l.endswith('#2') and L[i + 1:i + 4] == ['STO 32', 'R↓', 'AGRAPH 32']:
            if drawn and l == last:
                out.append('AGRAPH 32')              # same column again: R32 still holds it
            else:
                out += L[i:i + 4]
            last, drawn = l, True
            i += 4
            continue
        if l != 'AGRAPH 32':
            drawn = False                            # a gap (n +) or anything else: next column is not adjacent
        out.append(l)
        i += 1
    return out


def phls(L):
    k = L.index('LBL "PHLS"')
    assert L[k + 1:k + 7] == ['STO 34', 'R↓', 'STO 30', 'R↓', 'STO 31', 'WSIZE 8']
    L = L[:k + 6] + ['RCL 34', '400', 'X≤Y?', 'GTO 22'] + L[k + 6:]
    e = L.index('GTO 02', k)
    return L[:e + 1] + ['LBL 22', 'RCL 31', 'CHS', '0', 'PIXEL', 'GTO 02'] + L[e + 1:]


NATIVE_DATE = ['J→ⅅℸ', 'R↓', 'STO 36', 'DAY', 'STO 35', 'RCL 36', 'MONTH', 'STO 34', 'RCL 36', 'YEAR', 'STO 36']


def _date(L, label, setup, first):
    """Replace the calendar arithmetic of label (after setup) up to the first output step."""
    k = L.index('LBL "%s"' % label)
    assert L[k + 1:k + 3] == [setup, 'RCL 34'], label
    e = L.index(first[0], k)
    while L[e:e + len(first)] != first:
        e = L.index(first[0], e + 1)
    return L[:k + 3] + NATIVE_DATE + L[e:]


def pdts(L):
    return _date(L, 'PDTS', 'XEQ 05', ['RCL 35', 'XEQ 20'])


def stxt(L):
    L = _date(L, 'SDAT', 'XEQ 20', ['RCL 35', 'XEQ 09'])
    out, lab = [], None
    i = 0
    while i < len(L):
        l = L[i]
        if l.startswith('LBL '):
            lab = l
        # a sign or separator after the first piece: straight into R38
        if l.startswith('"') and L[i + 1:i + 2] == ['XEQ 02'] and lab != 'LBL 21':
            out += [l, 'x→α 38']
            i += 2
            continue
        if l == 'LBL 01':
            assert L[i:i + 7] == ['LBL 01', '50', '+', 'STO 31', 'XEQ IND 31', 'XEQ 02', 'RTN']
            out += ['LBL 01', 'STO 31', 'RCL 37', 'X=0?', 'GTO 18', 'RCL 31', 'αIP 38', 'RTN',
                    'LBL 18', 'RCL 31', '50', '+', 'STO 31', 'XEQ IND 31', 'XEQ 02', 'RTN']
            i += 7
            continue
        if l == 'LBL 06':
            assert L[i + 1] == 'STO 30'
            out += ['LBL 06', 'STO 30', 'RCL 37', 'X≠0?', 'GTO 14', 'R↓']
            i += 2
            continue
        if l == 'END':
            out += ['LBL 14', 'RCL 30', 'αIP 38', 'RTN']
        out.append(l)
        i += 1
    return out
