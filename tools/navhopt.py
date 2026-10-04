#!/usr/bin/env python3
"""navhopt.py - DEV: the counted loops of NAVFULL_OPT and MOON47_OPT on ISG (tools/build_navhopt.py applies it).

A loop counted by hand, `s STO+ r  f RCL r  X≤Y?  GTO n` (6 steps per pass), becomes `ISG r  GTO n` (2 steps)
with the control number a.fffss in r (counter a, last value fff, step ss; ISG adds ss and skips the GTO when
the counter goes past fff). A loop that reads its counter gets an IP at each read.

  NAVFULL   the five horizon / sky sweeps: HALMV LBL 14 (0..357 step 3), HORZ LBL 53 (0..358 step 2),
            HALMH LBL 13 (0..357 step 3), HANIM LBL 13 (0..358 step 2), ALLSKY LBL 13 (0..357 step 3);
            none reads its counter (CEQR walks the cache with its own pointer).
  MOON47    LBL 83 and LBL 46 (the four phases, R05 0..3), LBL 86 (the eight symbols, R05 0..7): R05 is
            read for indexing and drawing, so RCL 05 IP.
Left as they are: NAV LBL 29 and CALC LBL 01 (R82, read as an index by CSQK / STR2 / PLN3 and by STOIJ),
HANIM LBL 01 (its end is R14, computed: the control number would cost more steps than the loop saves),
MOON47 LBL 71 (R40 -62..62 is read in the inner loop LBL 82: one IP per pass of that loop).
"""
import re

SWEEPS = (('HALMV', '14'), ('HORZ', '53'), ('HALMH', '13'), ('HANIM', '13'), ('ALLSKY', '13'))


def sweep(P, lab):
    """One sweep in program P (list of lines): 0 STO r / LBL lab ... s STO+ r / f / RCL r / X≤Y? / GTO lab."""
    i = P.index('LBL ' + lab)
    j = P.index('GTO ' + lab, i)
    s, sto, f, rcl, test = P[j - 5:j]
    r = sto[5:]
    assert sto.startswith('STO+ ') and rcl == 'RCL ' + r and test == 'X≤Y?' and P[i - 2:i] == ['0', 'STO ' + r], \
        'navhopt: LBL %s is not a counted loop: %r' % (lab, P[i - 2:j + 1])
    assert not any(re.search(r'\b%s$' % r, l) for l in P[i + 1:j - 5]), 'navhopt: LBL %s reads R%s' % (lab, r)
    return P[:i - 2] + ['0.%03d%02d' % (int(f), int(s)), 'STO ' + r] + P[i:j - 5] + ['ISG ' + r] + P[j:]


def loops(L):
    """NAVFULL listing (long names; C47 or Free42) -> the five sweeps on ISG."""
    out, cur, name = [], [], None
    done = []
    for l in L:
        g = re.fullmatch(r'LBL "(.+)"', l)
        if g and name is None:
            name = g.group(1)
        cur.append(l)
        if l == 'END':
            for p, lab in SWEEPS:
                if p == name:
                    cur = sweep(cur, lab); done.append(p)
            out += cur; cur, name = [], None
    out += cur
    assert sorted(done) == sorted(p for p, _ in SWEEPS), 'navhopt: sweeps found: %s' % done
    return out


def blk(s):
    return s.split('|')


def cut(L, old, new):
    s = '\n' + '\n'.join(L) + '\n'
    o = '\n' + '\n'.join(old) + '\n'
    assert s.count(o) == 1, 'navhopt: block not found once: %r' % old[:8]
    return s.replace(o, '\n' + '\n'.join(new) + '\n').strip('\n').split('\n')


# MOON47_OPT: (old, new) blocks, R05 on ISG (0.003: 0..3 step 1; 0.007: 0..7)
MOON = [
    (blk('0|STO 05|LBL 83|RCL 38|RCL 05|+'), blk('0.003|STO 05|LBL 83|RCL 38|RCL 05|IP|+')),
    (blk('RCL 06|X<>Y|X<Y?|XEQ 84|RCL 05|54|+'), blk('RCL 06|X<>Y|X<Y?|XEQ 84|RCL 05|IP|54|+')),
    (blk('STO IND 39|1|STO+ 05|4|RCL 05|X<Y?|GTO 83'), blk('STO IND 39|ISG 05|GTO 83')),
    (blk('LBL 45|0|STO 05|LBL 46|RCL 05|54|+'), blk('LBL 45|0.003|STO 05|LBL 46|RCL 05|IP|54|+')),
    (blk('121|RCL 05|16|×'), blk('121|RCL 05|IP|16|×')),
    (blk('XEQ "M7HM"|1|STO+ 05|4|RCL 05|X<Y?|GTO 46'), blk('XEQ "M7HM"|ISG 05|GTO 46')),
    (blk('LBL 85|0|STO 05|LBL 86|26|RCL 05|29|×|168|+|RCL 05|90|+'),
     blk('LBL 85|0.007|STO 05|LBL 86|26|RCL 05|IP|29|×|168|+|RCL 05|IP|90|+')),
    (blk('XEQ "M7SY"|RCL 05|RCL 25|X=Y?|XEQ 87|1|STO+ 05|8|RCL 05|X<Y?|GTO 86'),
     blk('XEQ "M7SY"|RCL 05|IP|RCL 25|X=Y?|XEQ 87|ISG 05|GTO 86')),
    (blk('RCL 05|29|×|165|+'), blk('RCL 05|IP|29|×|165|+')),
]


def moon(P):
    """MOON47_OPT lines (C47 or Free42) -> R05 loops on ISG."""
    for old, new in MOON:
        P = cut(P, old, new)
    assert not any(re.fullmatch(r'(RCL|STO)[+\-×÷]? 05', l) and P[k + 1] != 'IP' and l != 'STO 05'
                   for k, l in enumerate(P)), 'navhopt: a read of R05 without IP'
    return P
