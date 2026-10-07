"""local_labels.py - a C47 listing made of several programs (LBL "NAME" ... END) turned into ONE program
whose labels are all local except the entry (NAV, MOON47): no routine in the calculator's program menus.

  routines        LBL "SUNA" / XEQ "SUNA" -> LBL :SUNA: / XEQ :SUNA: (names, or the N.. of the map files)
  inner labels    the 00-99 of each old program, renumbered for the merged program: the C47 looks for a
                  local label (number, letter or :name:) first after the GTO / XEQ, then from the start of
                  the program (lblGtoXeq.c fnGoto, manage.c findNamedLabelWithDuplicate), so one number can
                  serve several routines when no jump would land on the wrong one. 00-99, then A-L, a-l.
                  Labels of a program with XEQ IND / GTO IND keep their number (the number is computed).
                  Labels nothing jumps to are dropped.
  END             an END inside the listing becomes RTN (dropped after RTN or GTO).
  registers       (nav=True) NAV no longer saves R00.. in LocR at the start and puts them back at the end:
                  it clears the global registers (CLREGS) when it ends instead.

  Used by tools/build_v2.py (build/NAVFULL.txt: the routine names, :SUNA:) and tools/build_moon47.py
  (build/MOON47.txt: :M7TX: ...); tests/test_local_labels.py checks them.
"""
import re

LETTERS = [chr(c) for c in range(ord('A'), ord('L') + 1)] + [chr(c) for c in range(ord('a'), ord('l') + 1)]
CANDIDATES = ['%02d' % n for n in range(100)] + LETTERS
JUMP = re.compile(r'(LBL|GTO|XEQ) (\d\d|[A-La-l])$')


def is_test(l):
    return l.endswith('?') or bool(re.match(r'(x|𝑥)[=≠<>≤≥]\? ', l)) or l.startswith(('FS?', 'FC?', 'KEY?'))


def forward_dispatch(L):
    """A program that ends with its entry LBL "X" ... GTO IND nn after the table of labels (SBRT, SNMU):
    the entry moved to the start of the program, so the indirect jump goes forward (two such tables with
    the same numbers in one program: a backward jump would find the first table)."""
    L = list(L)
    starts = [0] + [i + 1 for i, l in enumerate(L) if l == 'END'][:-1]
    for s in reversed(starts):
        e = L.index('END', s)
        if not L[e - 1].startswith('GTO IND '):
            continue
        g = max(i for i in range(s, e) if L[i].startswith('LBL "'))
        if g == s or not (L[g - 1] == 'RTN' or L[g - 1].startswith('GTO ')) or is_test(L[g - 2]):
            continue
        L[s:e] = L[g:e] + L[s:g]
    return L


def merge(L):
    """The programs of L as one: the inner END -> RTN (none after an unconditional RTN / GTO)."""
    out = []
    ends = [i for i, l in enumerate(L) if l == 'END']
    last = ends[-1]
    prog = []
    p = 0
    for i, l in enumerate(L):
        if l == 'END' and i != last:
            prev, prev2 = out[-1], (out[-2] if len(out) > 1 else '')
            if (prev == 'RTN' or prev.startswith('GTO ')) and not is_test(prev2):
                p += 1
                continue
            l = 'RTN'
            out.append(l); prog.append(p); p += 1
            continue
        out.append(l); prog.append(p)
    return out, prog


def resolve(pos, cands):
    """The firmware's choice among the label positions cands (sorted): the first after pos, else the first."""
    for c in cands:
        if c > pos:
            return c
    return cands[0] if cands else None


def renumber(L, prog):
    """The inner (numeric / letter) labels of the old programs prog[i] renumbered for one program."""
    inst = {}                      # (prog, label) -> [positions]
    for i, l in enumerate(L):
        m = JUMP.match(l)
        if m and m.group(1) == 'LBL':
            inst.setdefault((prog[i], m.group(2)), []).append(i)
    ind = {prog[i] for i, l in enumerate(L) if re.match(r'(XEQ|GTO) IND ', l)}
    refs = {}                      # label position -> [positions of the jumps that land there]
    for i, l in enumerate(L):
        m = JUMP.match(l)
        if m and m.group(1) != 'LBL':
            c = inst.get((prog[i], m.group(2)))
            assert c, 'no LBL %s for %s at %d' % (m.group(2), l, i)
            refs.setdefault(resolve(i, c), []).append(i)
    num = {t: lab for (p, lab), c in inst.items() for t in c}
    # the labels an indirect jump can reach (they keep their number): the dispatch tables are the numbers
    # of the program that no GTO / XEQ names. A jump whose number is "base +" (a number or a constant
    # register: NAV's "90 STO 71") reaches the run of them from the base; another one (a character code, a
    # number given by the caller) any of them, or the label numbers the program stores in its register.
    const = {L[i][4:]: int(L[i - 1]) for i in range(1, len(L)) if L[i].startswith('STO ') and L[i - 1].isdigit()
             and sum(1 for l in L if l == L[i]) == 1}
    pinned = set()
    for p in ind:
        direct = {JUMP.match(L[i]).group(2) for i in range(len(L)) if prog[i] == p and JUMP.match(L[i])
                  and not L[i].startswith('LBL')}
        free = sorted(int(lab) for (q, lab) in inst if q == p and lab not in direct and lab.isdigit())
        for i, l in enumerate(L):
            if prog[i] != p or not re.match(r'(XEQ|GTO) IND ', l):
                continue
            r = l.split()[-1]
            w = max(j for j in range(i) if L[j] == 'STO ' + r)
            base = None
            if L[w - 1] == '+' and L[w - 2].isdigit():
                base = int(L[w - 2])
            elif L[w - 1] == '+' and L[w - 2].startswith('RCL ') and L[w - 2][4:] in const:
                base = const[L[w - 2][4:]]
            lits = sorted({int(L[j - 1]) for j in range(len(L)) if prog[j] == p and L[j] == 'STO ' + r
                           and L[j - 1].isdigit() and int(L[j - 1]) in free})
            if base is None and lits:          # the label numbers stored in r ("62 STO 22", ALLSKY)
                reach = lits
            elif base is None:
                reach = free
            else:
                reach = []
                for f in free:
                    if f >= base and (not reach or f == reach[-1] + 1):
                        reach.append(f)
                    elif reach:
                        break
            assert reach, 'no table for %s at %d' % (l, i)
            for f in reach:
                t = resolve(i, inst[(p, '%02d' % f)])
                pinned.add(t)
                refs.setdefault(t, []).append(i)
    labels = sorted(t for c in inst.values() for t in c if t in refs or t in pinned)
    n = len(L)

    def zone(t):
        """Positions where another label with t's number must not be."""
        f = [(p + 1, t - 1) for p in refs.get(t, []) if p < t]
        back = [p for p in refs.get(t, []) if p > t]
        if back:
            f += [(0, t - 1), (max(back) + 1, n)]
        return f

    Z = {t: zone(t) for t in labels}

    def clash(a, b):
        return any(x <= b <= y for x, y in Z[a]) or any(x <= a <= y for x, y in Z[b])

    new, by = {}, {}
    for t in sorted(pinned):
        k = num[t]
        assert not any(clash(t, u) for u in by.get(k, [])), 'pinned labels clash: %s at %d' % (k, t)
        new[t] = k; by.setdefault(k, []).append(t)
    named = 0
    for t in labels:
        if t in new:
            continue
        for k in [num[t]] + CANDIDATES:
            if not any(clash(t, u) for u in by.get(k, [])):
                break
        else:
            named += 1
            k = ':L%d:' % named
        new[t] = k; by.setdefault(k, []).append(t)
    out = []
    for i, l in enumerate(L):
        m = JUMP.match(l)
        if m and m.group(1) == 'LBL':
            if i in new:
                out.append('LBL ' + new[i])
            continue                                   # a label nothing reaches
        if m:
            out.append('%s %s' % (m.group(1), new[resolve(i, inst[(prog[i], m.group(2))])]))
            continue
        out.append(l)
    return out


def routines(L, names, keep):
    """LBL / XEQ / GTO "name" -> :new name: (names[name], or name itself); keep stays global."""
    out = []
    for l in L:
        g = re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l)
        if g and g.group(2) not in keep:
            k = names.get(g.group(2), g.group(2)) if names else g.group(2)
            assert len(k) <= 7, k
            l = '%s :%s:' % (g.group(1), k)
        out.append(l)
    return out


def no_save(L):
    """NAV: no LocR k + RCL nn STO R.nn at the start, no RCL R.nn STO nn at the end; CLREGS there instead."""
    i = L.index('LBL "NAV"') + 1
    k = int(re.fullmatch(r'LocR (\d+)', L[i]).group(1))
    assert L[i + 1:i + 1 + 2 * k] == [x for j in range(k) for x in ('RCL %02d' % j, 'STO R.%02d' % j)]
    L = L[:i] + L[i + 1 + 2 * k:]
    rest = [x for r in range(k) for x in ('RCL R.%02d' % r, 'STO %02d' % r)]
    j = [j for j in range(len(L)) if L[j:j + 2 * k] == rest]
    assert len(j) == 1
    j = j[0]
    return L[:j] + ['CLREGS'] + L[j + 2 * k:]


def convert(L, keep, names=None, nav=False):
    L = [l for l in L if l.strip()]
    if nav:
        L = no_save(L)
    M, prog = merge(forward_dispatch(L))
    M = renumber(M, prog)
    M = routines(M, names, keep)
    assert sum(1 for l in M if l.startswith('LBL "')) == len(keep)
    assert M.count('END') == 1 and M[-1] == 'END'
    for l in M:                                       # every jump has its label
        m = re.fullmatch(r'(?:XEQ|GTO) (:.+:|\d\d|[A-La-l])', l)
        if m:
            assert 'LBL ' + m.group(1) in M, l
    return M


def moon_exit(L):
    """MOON47 keeps no register of yours: CLREGS before the CLSTK of its end."""
    j = [i for i in range(len(L) - 1) if L[i] == 'STO "M7C"' and L[i + 1] == 'CLSTK']
    assert len(j) == 1
    return L[:j[0] + 1] + ['CLREGS'] + L[j[0] + 1:]
