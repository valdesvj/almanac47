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
    present = {l[5:-1] for l in L if l.startswith('LBL "')}
    assert sorted(done) == sorted(p for p, _ in SWEEPS if p in present), 'navhopt: sweeps found: %s' % done
    return out


def inputs(L):
    """NAV, the inputs (LBL 20): at each INPUT a clean stack, the value in X and in Y only the format of that
    input (the stack had 999 from the start of NAV, the long text of all four formats, cut on the screen, and
    the inputs before). The date format follows the calculator (YMD, DMY: LBL 97, MDY: LBL 98)."""
    for old, new in (('DATE YYYY.MMDD', 'DATE YYYY.MMDD'), ('DATE DD.MMYYYY', 'DATE DD.MMYYYY'), ('DATE MM.DDYYYY', 'DATE MM.DDYYYY')):
        L = cut(L, ['"%s  UT HH.MMSS  LAT DD.MMm  LON DDD.MMm  S W -"' % old], ['"%s"' % new])
    old = ['AVIEW 38', 'INPUT "DATE"', 'INPUT "UTC"', 'INPUT "LAT"', 'INPUT "LON"']
    new = ['CLSTK', 'RCL 38', 'INPUT "DATE"', 'CLSTK', '"UT HH.MMSS"', 'INPUT "UTC"',
           'CLSTK', '"LAT DD.MMm  S -"', 'INPUT "LAT"', 'CLSTK', '"LON DDD.MMm  W -"', 'INPUT "LON"', 'CLSTK']
    return cut(L, old, new)


def blk(s):
    return s.split('|')


def cut(L, old, new):
    s = '\n' + '\n'.join(L) + '\n'
    o = '\n' + '\n'.join(old) + '\n'
    assert s.count(o) == 1, 'navhopt: block not found once: %r' % old[:8]
    return [l for l in s.replace(o, '\n' + '\n'.join(new) + '\n').strip('\n').split('\n') if l]


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


def moon_regs(P, local=False):
    """MOONFAST_R31 / _LOCR (C47): the registers of MOON47 renumbered (tools/regalloc.py) from R00, the phase
    table (R54..R61 in MOON47, addressed with RCL / STO IND: 54 + phase) right after them, and the globals
    saved at the start in local registers of the main level and restored before the end (CLSTK):
    every register is as it was. local=True: values private to one routine in its own LocR as well."""
    import regalloc
    t = [i for i in range(len(P) - 2) if P[i:i + 3] == ['54', '+', 'STO 39']]
    assert len(t) == 2, 'navhopt: the phase table base not found twice'
    P = list(P)
    for i in t:
        P[i] = '@TABLE'
    out, k, nloc = regalloc.plan(P, table=True, local=local)
    n = k + 8                                                  # globals R00 .. R(k-1), the table R(k) .. R(k+7)
    out = [str(k) if l == '@TABLE' else l for l in out]
    i = out.index('LBL "MOON47"') + 1
    m = int(out.pop(i)[5:]) if out[i].startswith('LocR ') else 0
    save = ['LocR %d' % (m + n)] + [x for j in range(n) for x in ('RCL %02d' % j, 'STO R.%02d' % (m + j))]
    out[i:i] = save
    end = out.index('CLSTK')
    out[end:end] = [x for j in range(n) for x in ('RCL R.%02d' % (m + j), 'STO %02d' % j)]
    assert out.count('CLSTK') == 1 and m + n <= 99
    return out, n, nloc


FRESH = ('NAV', 'ALMF', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')     # no register value comes into these


def nav_regs(L):
    """NAVFULL_RSAVE (C47, long names): the registers renumbered from R00 (tools/regalloc.py; NAV and the six
    views read no register they have not written: test_navhopt checks it), saved in local registers of NAV
    at the start and restored when NAV ends (before its last CLSTK: after XEQ 08 in NAVFULL, after SSIZE4 in
    NAVLITTLE)."""
    import regalloc
    out, k, _ = regalloc.plan(L, FRESH, local=False, roots=[L.index('LBL "NAV"')])
    i = out.index('LBL "NAV"') + 1
    out[i:i] = ['LocR %d' % k] + [x for j in range(k) for x in ('RCL %02d' % j, 'STO R.%02d' % j)]
    e = out.index('END', i)
    ends = [j for j in range(i, e) if out[j] == 'CLSTK' and out[j - 1] in ('XEQ 08', 'SSIZE4')]
    assert len(ends) == 1, 'navhopt: the end of NAV (XEQ 08 or SSIZE4, CLSTK) not found once'
    j = ends[0]
    out[j:j] = [x for r in range(k) for x in ('RCL R.%02d' % r, 'STO %02d' % r)]
    return out


# MOONFAST_LOCR: the phase table (R54..R61 by RCL / STO IND: local registers cannot be addressed indirectly)
# in the matrix M7P (4 x 2: the time and the type of each phase), made with M7T and set to 0 at the end
MOON_TABLE = [
    (blk('RCL 05|IP|54|+|STO 39|RCL 44|STO IND 39|4|STO+ 39|RCL 37|STO IND 39'),
     blk('INDEX "M7P"|RCL 05|IP|1|+|1|STOIJ|RCL 44|STOEL|J+|RCL 37|STOEL')),
    (blk('RCL 05|IP|54|+|STO 39|RCL IND 39|STO 44|4|STO+ 39|RCL IND 39|STO 37'),
     blk('INDEX "M7P"|RCL 05|IP|1|+|1|STOIJ|RCLEL|STO 44|J+|RCLEL|STO 37')),
    (blk('STO "M7V"|INDEX "M7W"'), blk('STO "M7V"|4|ENTER|2|NEWMAT|STO "M7P"|INDEX "M7W"')),
    (blk('STO "M7V"|CLSTK'), blk('STO "M7V"|STO "M7P"|CLSTK')),
]


def moon_table(P):
    for old, new in MOON_TABLE:
        P = cut(P, old, new)
    assert not any(' IND ' in l and not l.startswith(('XEQ IND', 'GTO IND')) for l in P)
    return P


def moon_locr(P):
    """MOONFAST_LOCR (C47): MOONFAST_HOPT with no numbered global register: every value in local registers
    (LocR) of the level that uses it. The values that went from one routine to another in registers now go
    on the stack or stay on one level:
      phase table   the matrix M7P (moon_table)
      LBL 29        its own copy of LBL 41 (the Moon: it needs R11 R22 R41 of it), the other 2 calls stay
      LBL 35        (R27 = -R27) written at its 2 calls, after the test: T? GTO a, GTO b, LBL a, ..., LBL b
      LBL 50        the row of M7T as a 4th argument on the stack (no counter R21 between the 20 calls)
      LBL 76 / 81   the row (R40) as one more argument on the stack; LBL 79 calls LBL 81 (no falling in)
      GRMOD         takes X (STO r GRMOD r -> GRMOD: rejig writes GRMOD r as GRMOD and the number r)
      M7TX          LBL 05 written in each printer; LBL 06 / 07 / 08 give the text back in X and LBL 07 takes
                    it in Y (no R49 between levels); LBL 17 takes the number in X
      M7SY          XEQ IND 32 -> GTO IND 32, each glyph ends with GTO 01 (one level)
    then the routines called once run on the level of their caller (regalloc.inline_once) and the
    registers get their local numbers (regalloc.plan); one stays global: the key of KEY? (the C47 gives an
    error for KEY? with a local register), R00, saved at the start and restored at the end."""
    import regalloc
    P = moon_table(P)
    i = P.index('LBL 41'); body = P[i + 1:P.index('RTN', i)]
    assert not any(l.startswith(('LBL', 'GTO', 'XEQ', 'RTN')) for l in body)
    P = cut(P, blk('LBL 29|RCL 06|XEQ 41'), blk('LBL 29|RCL 06') + body)
    k = 0
    free = [n for n in range(100) if 'LBL %02d' % n not in P[:P.index('END')]]
    for t, inv in (('X<Y?', 'X≥Y?'), ('X≠0?', 'X=0?')):
        a = '%02d' % free[k]; k += 1
        P = cut(P, [t, 'XEQ 35'], [inv, 'GTO ' + a, '1', 'CHS', 'STO× 27', 'LBL ' + a])
    P = cut(P, blk('LBL 35|1|CHS|STO× 27|RTN'), [])
    i = P.index('LBL 51'); j = P.index('RTN', i)
    assert P[i:j].count('STO 21') == 1
    a = P.index('STO 21', i)
    assert P[a - 1] == '1'
    terms = P[a + 1:j]
    out, row, cur = [], 1, []
    for l in terms:
        cur.append(l)
        if l == 'XEQ 50':
            out += [str(row)] + cur; cur = []; row += 1
    assert not cur and row == 21
    P = P[:a - 1] + out + P[j:]
    P = cut(P, blk('LBL 50|STO 43|R↓|STO 42|R↓|STO 44'), blk('LBL 50|STO 43|R↓|STO 42|R↓|STO 44|R↓|STO 21'))
    P = cut(P, blk('RCL 43|STOEL|1|STO+ 21|RTN'), blk('RCL 43|STOEL|RTN'))
    P = [x for l in P for x in (['RCL 40', 'XEQ 76'] if l == 'XEQ 76' else [l])]
    P = cut(P, blk('LBL 76|STO 45'), blk('LBL 76|STO 98|R↓|STO 45'))
    P = cut(P, blk('GTO 79|120|RCL 44|+|120|RCL 45|+|XEQ 81|120|RCL 45|-|120|RCL 44|-|XEQ 81|RTN|LBL 79|120|RCL 45|-|120|RCL 45|+|LBL 81|STO 47|R↓|STO 46'),
               blk('GTO 79|RCL 98|120|RCL 44|+|120|RCL 45|+|XEQ 81|RCL 98|120|RCL 45|-|120|RCL 44|-|XEQ 81|RTN|LBL 79|RCL 98|120|RCL 45|-|120|RCL 45|+|XEQ 81|RTN|LBL 81|STO 47|R↓|STO 46|R↓|STO 97'))
    P = cut(P, blk('RCL 46|RCL 40|80|+|AGRAPH 48'), blk('RCL 46|RCL 97|80|+|AGRAPH 48'))
    # LBL 11 (the clock line) reads the time zone R03 of the main level: on the stack, in R96 inside
    P = [x for l in P for x in (['RCL 03', 'XEQ 11'] if l == 'XEQ 11' else [l])]
    i = P.index('LBL 11')
    F = regalloc.Flow(P)
    for j in F.body(i):
        if P[j] == 'RCL 03':
            P[j] = 'RCL 96'
    P[i + 1:i + 1] = ['STO 96', 'DROP']
    out = []
    for l in P:
        if l.startswith('GRMOD ') and out[-1] == 'STO ' + l[6:]:
            out[-1] = 'GRMOD'
        else:
            out.append(l)
    P = out
    assert not any(l.startswith('GRMOD ') for l in P)
    P = cut(P, blk('LBL 05|STO 34|R↓|STO 30|R↓|STO 31|RTN'), [])
    P = [x for l in P for x in (blk('STO 34|R↓|STO 30|R↓|STO 31') if l == 'XEQ 05' else [l])]
    P = cut(P, blk('LBL 06|48|+|STO 32|XEQ IND 32|STO 49|RTN'), blk('LBL 06|CLα 32|αIP 32|RCL 32|RTN'))
    i = P.index('LBL 48', P.index('LBL "M7TX"'))                 # the digit table "0" .. "9": no longer used
    assert P[i:i + 30] == [x for d in range(10) for x in ('LBL %d' % (48 + d), '"%d"' % d, 'RTN')]
    P = P[:i] + P[i + 30:]
    P = cut(P, blk('LBL 07|STO 33|10|÷|IP|αIP 49|RCL 33|10|MOD|αIP 49|RTN'),
            blk('LBL 07|STO 33|R↓|STO 49|RCL 33|10|÷|IP|αIP 49|RCL 33|10|MOD|αIP 49|RCL 49|RTN'))
    P = [x for l in P for x in ({'XEQ 06': ['XEQ 06', 'STO 49'], 'XEQ 07': ['RCL 49', 'X<>Y', 'XEQ 07', 'STO 49'],
                                 'XEQ 08': ['XEQ 08', 'STO 49'], 'XEQ 17': ['RCL 34', 'XEQ 17']}.get(l, [l]))]
    i, j = P.index('LBL 08'), P.index('LBL "M7IN"')
    P = P[:i] + [x for l in P[i:j] for x in (['RCL 49', 'RTN'] if l == 'RTN' else [l])] + P[j:]
    P = cut(P, blk('LBL 17|RCL 34|X<0?'), blk('LBL 17|X<0?'))
    i = P.index('LBL "M7SY"'); j = P.index('END', i)
    seg = P[i:j]
    a = seg.index('XEQ IND 32'); assert seg[a + 1] == 'GTO 01'
    seg[a] = 'GTO IND 32'
    g = seg.index('LBL 48')
    seg = seg[:g] + ['GTO 01' if l == 'RTN' else l for l in seg[g:]]
    P = P[:i] + seg + P[j:]
    P, n = regalloc.move_once(P)
    P, n = regalloc.inline_once(P)
    out, k, nloc = regalloc.plan(P, local=True)
    assert k <= 1, 'navhopt: MOONFAST_LOCR still has %d global registers' % k     # 1: the key (KEY? needs a global)
    if k:                                                    # saved in a local register of MOON47, restored at the end
        i = out.index('LBL "MOON47"') + 1
        m = int(out.pop(i)[5:]) if out[i].startswith('LocR ') else 0
        out[i:i] = ['LocR %d' % (m + k)] + [x for j in range(k) for x in ('RCL %02d' % j, 'STO R.%02d' % (m + j))]
        e = out.index('CLSTK')
        out[e:e] = [x for j in range(k) for x in ('RCL R.%02d' % (m + j), 'STO %02d' % j)]
    out, nlab = merge(out)
    return out, nloc, k


NAV_HIDE = ('NUT', 'PLN2', 'PLNQ', 'HCZ0', 'CTWA', 'CTWP', 'CALC')    # used only inside their own program


def hide(L, names):
    """Global labels used only inside their program -> a free numeric label of it (XEQ / GTO "name" -> nn)."""
    import regalloc
    out = list(L)
    for a, b in regalloc.programs(L):
        used = {int(l[4:]) for l in L[a:b] if re.fullmatch(r'LBL \d\d', l)}
        free = [n for n in range(100) if n not in used]
        for i in range(a, b):
            g = re.fullmatch(r'LBL "(.+)"', L[i])
            if g and g.group(1) in names:
                n = '%02d' % free.pop(0)
                for j in range(a, b):
                    if out[j] in ('LBL "%s"' % g.group(1), 'XEQ "%s"' % g.group(1), 'GTO "%s"' % g.group(1)):
                        out[j] = out[j][:4] + n
    for n in names:
        assert not any(l.endswith('"%s"' % n) and l.startswith(('XEQ', 'GTO', 'LBL')) for l in out), 'hide: %s used outside' % n
    return out



# The helpers called from other programs, hidden behind one visible dispatch entry per program
# (program: (dispatch entry, names)); TGET (alone in its program) goes into the program of SUNA first.
# Kept visible (called directly): the ones a view calls in its loops, CEQR (about 90 calls per view),
# HCZR (55), HCZ (20), CHCZ (16): a dispatched call costs 4 steps more.
NAV_DISPATCH = {'SUNA': ('SUNX', ('SUNG', 'SUNF', 'SER', 'SERT', 'TGET')),
                'STAR': ('STAX', ('STR2', 'SQK')),
                'MOON': ('MOOX', ('MOO2', 'MOOQ')),
                'PLAN': ('PLAX', ('PLN3',)),
                'CHZ': ('CHZX', ('HCZQ', 'HCZI')),
                'PHAS': ('PHAX', ('PHA2',)),
                'CSUN': ('CACH', ('CSUN', 'CMOO', 'CPLN', 'CSTR', 'CSQK', 'CPHA', 'CNTA', 'CRIS', 'CTRN',
                                  'CSET', 'CNTP', 'CEQQ'))}


def append(L, src, dst):
    """Program src (one global label) at the end of program dst with numeric labels: its labels get free
    numbers of dst; a table src reaches with k + / STO r / XEQ IND r keeps its order (a free run, k changed)."""
    import regalloc
    progs = [L[a:b + 1] for a, b in regalloc.programs(L)]
    S = next(p for p in progs if p[0] == 'LBL "%s"' % src)
    D = next(p for p in progs if p[0] == 'LBL "%s"' % dst)
    F = regalloc.Flow(S)
    used = {int(l[4:]) for l in D if re.fullmatch(r'LBL \d\d', l)}
    free = [n for n in range(100) if n not in used]
    m, S = {}, list(S)
    for i, l in enumerate(S):
        if l.startswith(('XEQ IND', 'GTO IND')):
            run = sorted(int(S[t][4:]) for t in F.calls.get(i, F.succ[i]))
            j = i
            while S[j] != 'STO ' + l[8:]:
                j -= 1
            assert S[j - 1] == '+' and S[j - 2].isdigit() and run == list(range(run[0], run[-1] + 1))
            k = next(x for x in free if all(x + d in free for d in range(len(run))))
            for d, n in enumerate(run):
                m[n] = k + d; free.remove(k + d)
            S[j - 2] = str(k + int(S[j - 2]) - run[0])
            S[i] = '@TABLE %02d %02d\n' % (k, k + len(run) - 1) + S[i]      # for regalloc; taken out at the end
    for l in S:
        g = re.fullmatch(r'LBL (\d\d)', l)
        if g and int(g.group(1)) not in m:
            m[int(g.group(1))] = free.pop(0)
    S = [x for l in S for x in l.split('\n')]
    body = []
    for l in S[:-1]:
        g = re.fullmatch(r'(LBL|GTO|XEQ) (\d\d)', l)
        body.append('%s %02d' % (g.group(1), m[int(g.group(2))]) if g else l)
    D = D[:-1] + ([] if D[-2] == 'RTN' or D[-2].startswith('GTO ') else ['RTN']) + body + \
        ([] if body[-1] == 'RTN' or body[-1].startswith('GTO ') else ['RTN']) + ['END']
    out = []
    for p in progs:
        out += D if p[0] == 'LBL "%s"' % dst else [] if p is S or p[0] == 'LBL "%s"' % src else p
    return out


def dispatch(L, table=NAV_DISPATCH):
    """The names of table hidden: in their program a numeric label (XEQ / GTO "name" -> nn); one visible entry
    per program, LBL "entry" / GTO IND X, and one stub per name, LBL s / DROP / GTO nn. A call from another
    program: s / XEQ "entry" (the stub drops s: the routine finds the stack of the caller); after a test it
    goes through a stub of the caller (XEQ t or GTO t; LBL t / s / GTO "entry")."""
    import regalloc
    L = append(L, 'TGET', 'SUNA')
    progs = [L[a:b + 1] for a, b in regalloc.programs(L)]
    sel = {}                                                  # name -> (entry, selector)
    new = []
    for P in progs:
        first = P[0][5:-1]
        if first not in table:
            new.append(P); continue
        entry, names = table[first]
        used = {int(l[4:]) for l in P if re.fullmatch(r'LBL \d\d', l)}
        free = [n for n in range(100) if n not in used]
        num = {}
        for n in names:
            num[n] = '%02d' % free.pop(0)
        P = [('%s %s' % (l[:3], num[l[5:-1]]) if re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l) and l[5:-1] in num else l)
             for l in P]
        stubs = []
        for n in names:
            s = '%02d' % free.pop(0)
            sel[n] = (entry, s)
            stubs += ['LBL ' + s, 'DROP', 'GTO ' + num[n]]
        P = P[:-1] + ([] if P[-2] == 'RTN' or P[-2].startswith('GTO ') else ['RTN']) + \
            ['LBL "%s"' % entry, 'GTO IND X'] + stubs + ['END']
        new.append(P)
    out = []
    for P in new:
        Q, tramp = [], {}
        used = {int(l[4:]) for l in P if re.fullmatch(r'LBL \d\d', l)}
        free = [n for n in range(100) if n not in used]
        for i, l in enumerate(P):
            g = re.fullmatch(r'(XEQ|GTO) "(.+)"', l)
            if g and g.group(2) in sel:
                entry, s = sel[g.group(2)]
                if regalloc.SKIP.match(P[i - 1]) and not P[i - 1].startswith(('LBL', '"')):
                    if g.group(2) not in tramp:
                        tramp[g.group(2)] = '%02d' % free.pop(0)
                    Q.append('%s %s' % (g.group(1), tramp[g.group(2)]))
                else:
                    assert P[i - 1] not in ('ENTER', 'CLX'), 'dispatch: no stack lift before %s' % l
                    Q += [s, '%s "%s"' % (g.group(1), entry)]
            else:
                Q.append(l)
        if tramp:
            Q = Q[:-1] + ([] if Q[-2] == 'RTN' or Q[-2].startswith('GTO ') else ['RTN'])
            for n, t in tramp.items():
                entry, s = sel[n]
                Q += ['LBL ' + t, s, 'GTO "%s"' % entry]
            Q.append('END')
        out += Q
    for n in sel:
        assert not any(l in ('LBL "%s"' % n, 'XEQ "%s"' % n, 'GTO "%s"' % n) for l in out), n
    return out

# routines called many times per view (simulator): their values stay global, no LocR on each call
NAV_HOT = ('CEQR', 'HCZR', 'HCZ', 'PSYS', 'PDMS', 'PTXS:07')


def nav_locr(L):
    """NAVFULL_LOCR (C47, long names): the labels of NAV_HIDE numeric; the values of each subroutine level in
    its own local registers (regalloc.plan, local=True); the registers still global (values that go from one
    program to another: engine results, the cache, the inputs) renumbered from R00, saved in local registers of
    NAV at the start and restored when NAV ends (0: before CLSTK)."""
    import regalloc
    L = hide(L, NAV_HIDE)
    L = dispatch(L)
    hot = []
    for h in NAV_HOT:
        prog, _, lab = h.partition(':')
        i = L.index('LBL "%s"' % prog)
        hot.append(L.index('LBL ' + lab, i) if lab else i)
    out, k, nloc = regalloc.plan(L, FRESH, local=True, roots=[L.index('LBL "NAV"')], hot=hot)
    i = out.index('LBL "NAV"') + 1
    m = int(out.pop(i)[5:]) if out[i].startswith('LocR ') else 0
    assert m + k <= 99
    out[i:i] = ['LocR %d' % (m + k)] + [x for j in range(k) for x in ('RCL %02d' % j, 'STO R.%02d' % (m + j))]
    ends = [j for j in range(i, len(out)) if out[j] == 'CLSTK' and out[j - 1] == 'XEQ 08']
    assert len(ends) == 1, 'navhopt: the end of NAV (XEQ 08, CLSTK) not found once'
    j = ends[0]
    out[j:j] = [x for r in range(k) for x in ('RCL R.%02d' % (m + r), 'STO %02d' % r)]
    return [l for l in out if not l.startswith('@')], k, nloc

def merge(L, main='MOON47'):
    """One program: the other programs appended to the first with numeric labels (their global labels and
    numeric labels get new numbers; XEQ "name" -> XEQ nn), so the catalog shows only LBL "main". The labels
    are numbered again from 00, except the tables the first program reaches with k + x / XEQ IND (they keep
    their numbers); a table reached with GTO IND after α→𝑥 (M7SY: labels = character codes) gets a free run
    of labels and the shift is added after α→𝑥."""
    import regalloc
    progs = [L[a:b + 1] for a, b in regalloc.programs(L)]
    assert progs[0][0] == 'LBL "%s"' % main
    F = regalloc.Flow(L)                                   # program 0 comes first: the same line numbers
    fixed = set()
    for i, l in enumerate(progs[0]):
        if l.startswith(('XEQ IND', 'GTO IND')):
            j = i
            while not progs[0][j].startswith('STO ' + l[8:]):
                j -= 1
            assert progs[0][j - 1] == '+' and progs[0][j - 2].isdigit(), 'merge: a table without its offset: %s' % l
            fixed |= {int(progs[0][t][4:]) for t in F.calls.get(i, F.succ[i])}
    free = [n for n in range(100) if n not in fixed]
    runs = []                                                # the α→𝑥 tables of the other programs: placed first
    for P in progs[1:]:
        if any(P[i].startswith('α→𝑥') and P[i + 2].startswith('GTO IND') for i in range(len(P) - 2)):
            nums = sorted(int(l[4:]) for l in P if re.fullmatch(r'LBL \d\d', l) and int(l[4:]) >= 48)
            runs.append(nums)
    tabmap = []
    for run in runs:
        need = run[-1] - run[0] + 1
        gaps, cur = [], []
        for n in free:
            if cur and n != cur[-1] + 1:
                gaps.append(cur); cur = []
            cur.append(n)
        gaps.append(cur)
        g = max(gaps, key=len)
        assert len(g) >= need, 'merge: no run of %d free labels' % need
        k = g[0]
        tabmap.append({n: k + n - run[0] for n in run})
        for x in range(k, k + need):
            free.remove(x)

    def renum(P, m):
        out = []
        for l in P:
            g = re.fullmatch(r'(LBL|GTO|XEQ) (\d\d)', l)
            out.append('%s %02d' % (g.group(1), m[int(g.group(2))]) if g else l)
        return out
    m0 = {}
    for l in progs[0]:
        g = re.fullmatch(r'LBL (\d\d)', l)
        if g:
            n = int(g.group(1))
            m0[n] = n if n in fixed else free.pop(0)
    out = renum(progs[0][:-1], m0)
    if out[-1] != 'RTN' and not out[-1].startswith('GTO '):
        out.append('RTN')
    names, t = {}, 0
    for P in progs[1:]:
        tab = [i for i in range(len(P) - 2) if P[i].startswith('α→𝑥') and P[i + 2].startswith('GTO IND')]
        m = {}
        if tab:
            m = dict(tabmap[t]); t += 1
            d = next(iter(m.values())) - next(iter(m))
            for i in reversed(tab):
                P = P[:i + 1] + ([str(abs(d)), '+' if d > 0 else '-'] if d else []) + P[i + 1:]
        for l in P:
            g = re.fullmatch(r'LBL (\d\d)', l)
            if g and int(g.group(1)) not in m:
                m[int(g.group(1))] = free.pop(0)
        Q = []
        for l in renum(P[:-1], m):
            h = re.fullmatch(r'LBL "(.+)"', l)
            if h:
                names[h.group(1)] = '%02d' % free.pop(0); l = 'LBL ' + names[h.group(1)]
            Q.append(l)
        if Q[-1] != 'RTN' and not Q[-1].startswith('GTO '):
            Q.append('RTN')
        out += Q
    out = [('%s %s' % (l[:3], names[l[5:-1]]) if re.fullmatch(r'(XEQ|GTO) "(.+)"', l) and l[5:-1] in names else l)
           for l in out] + ['END']
    labels = [l for l in out if l.startswith('LBL ')]
    assert len(labels) == len(set(labels)) and sum(1 for l in labels if l[4] != '"') <= 100
    return out, len(labels) - 1


def f42_inputs(L):
    """Free42 NAV (NAVFULL, NAVLITTLE): at each INPUT a clear stack and only the format of that input in Y,
    as on the C47 (the stack had what NAV and the inputs before left on it)."""
    old = ['CLA', 'XSTR "Y.MMDD H.MMSS D.MMm"', 'AVIEW', 'INPUT "DATE"', 'INPUT "UTC"', 'INPUT "LAT"', 'INPUT "LON"']
    new = ['CLST', 'XSTR "DATE Y.MMDD"', 'INPUT "DATE"', 'CLST', 'XSTR "UT H.MMSS"', 'INPUT "UTC"',
           'CLST', 'XSTR "LAT D.MMm  S -"', 'INPUT "LAT"', 'CLST', 'XSTR "LON D.MMm  W -"', 'INPUT "LON"', 'CLST']
    return cut(L, old, new)


def f42_regs(L):
    """Free42 NAV: the registers renumbered from R00 (regalloc), SIZE k instead of SIZE 100, and the user's
    registers kept: RCL "REGS" (the whole register matrix, its size = the user's SIZE) into "NBAK" before
    SIZE k, back into REGS when NAV ends (STO "REGS" gives the SIZE back too), NBAK deleted. Flag 25 guards
    both: no REGS (SIZE 0) or no NBAK does not stop NAV."""
    import regalloc
    out, k, _ = regalloc.plan(L, FRESH, local=False, roots=[L.index('LBL "NAV"')])
    i = out.index('LBL "NAV"')
    e = out.index('END', i)
    s = [j for j in range(i, e) if out[j] == 'SIZE 100']
    assert len(s) == 1, 'navhopt: SIZE 100 not found once in NAV'
    out[s[0]:s[0] + 1] = ['SF 25', 'RCL "REGS"', 'FS?C 25', 'STO "NBAK"', 'CLX', 'SIZE %d' % max(k, 1)]
    e = out.index('END', i)
    ends = [j for j in range(i, e) if out[j] == 'CLST' and out[j + 1] in ('CLD', 'RTN') and not out[j - 1].startswith('INPUT')]
    assert len(ends) == 1, 'navhopt: the end of the Free42 NAV (CLST, CLD / RTN) not found once'
    j = ends[0]
    out[j:j] = ['SF 25', 'RCL "NBAK"', 'FS?C 25', 'STO "REGS"', 'SF 25', 'CLV "NBAK"', 'CF 25']
    return out, k
