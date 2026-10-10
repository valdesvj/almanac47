#!/usr/bin/env python3
"""build_moon47_struct.py - MOON47 (C47 / R47 only) with the label rules of build/dev/struct (steps 12-15).

The input is build/dev/struct/moon/0_speed/MOON47.txt: build/MOON47.txt of the branch moon47-speed (59d01b4, the disc
routine first, -17 % CPU), three programs: MOON47 (the page), M7TX (the text printers M7TX M7IN M7F1 M7HM M7DT
M7HL) and M7SY (the eight Moon phase symbols). Each step goes to its own folder:

  1_labels/MOON47.txt   the three programs; the blocks no XEQ / GTO can reach removed (M7TX's LBL 14, 15, 19:
                        NAV's printers that MOON47 does not use); labels 01, 02 ... in order in each program; the
                        tables that XEQ IND reaches keep their numbers (MOON47 60-67 phase names, 90-97 symbol
                        codes; M7TX 48-57 digits; M7SY 48-55 symbols)
  2_compact/MOON47.txt  ONE program, only MOON47 global: M7TX and M7SY after the page (END -> RTN where code ran
                        into END); their seven entries are the letters a b c ...; every other label a number
                        00-99 in order, the letters after a-l (A-L) if the numbers run out; M7TX's digit table
                        moves from 48-57 to 70-79 (48 + digit -> 70 + digit) so that it does not meet M7SY's 48-55.
                        A letter label is found like a number (integer compare in the label table, jump by address).
                        MOON47 already ends with CLSTK.

  python3 tools/build_moon47_struct.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_navopt as N                                                     # noqa: E402
import build_struct as B                                                     # noqa: E402

OUT = os.path.join(ROOT, 'build', 'dev', 'struct', 'moon')
SRC = os.path.join(OUT, '0_speed', 'MOON47.txt')
TABLES = {'MOON47': {'%02d' % n for n in list(range(60, 68)) + list(range(90, 98))},
          'M7TX': {'%02d' % n for n in range(48, 58)},
          'M7SY': {'%02d' % n for n in range(48, 56)}}
LETTERS = [chr(c) for c in range(ord('a'), ord('l') + 1)] + [chr(c) for c in range(ord('A'), ord('L') + 1)]
JUMP = re.compile(r'(LBL|XEQ|GTO) (\d\d)$')


def pname(p):
    """The first global label of a program (MOON47's disc routine comes before its LBL "MOON47")."""
    return next(re.fullmatch(r'LBL "(.+)"', l).group(1) for l in p if l.startswith('LBL "'))


def tables_ok(p):
    """The labels no XEQ / GTO nn names are the tables (reached by XEQ IND) or dead blocks after an exit."""
    nums = {l[4:] for l in p if re.fullmatch(r'LBL \d\d', l)}
    direct = {l[4:] for l in p if re.fullmatch(r'(XEQ|GTO) \d\d', l)}
    return nums - direct - TABLES[pname(p)]


def labels(L):
    out = []
    for p in B.split(L):
        dead = tables_ok(p)
        i, gone = 1, []
        while i < len(p):
            if re.fullmatch(r'LBL \d\d', p[i]) and p[i][4:] in dead:
                assert B.exits(p, i - 1), (pname(p), p[i])            # only blocks nothing can run into
                j = i + 1
                while not (p[j].startswith('LBL ') or p[j] == 'END'):
                    j += 1
                gone.append('%s (%d steps)' % (p[i], j - i))
                del p[i:j]
            else:
                i += 1
        fixed = TABLES[pname(p)]
        free = ('%02d' % k for k in range(1, 100) if '%02d' % k not in fixed)
        new = {l[4:]: (l[4:] if l[4:] in fixed else next(free)) for l in p if re.fullmatch(r'LBL \d\d', l)}
        out += [('%s %s' % (m.group(1), new[m.group(2)])) if m else l for l in p for m in [JUMP.fullmatch(l)]]
        print('  1_labels: %s %d labels, removed %s' % (pname(p), len(new), ', '.join(gone) or 'nothing'))
    return out


def compact(L):
    P = B.split(L)
    assert [pname(p) for p in P] == ['MOON47', 'M7TX', 'M7SY']
    # M7TX's digit table 48-57 -> 70-79
    tx = P[1]
    k = [i for i in range(len(tx) - 3) if tx[i:i + 4] == ['48', '+', tx[i + 2], 'XEQ IND ' + tx[i + 2][4:]]
         and tx[i + 2].startswith('STO ')]
    assert len(k) == 1
    tx[k[0]] = '70'
    P[1] = [('LBL %d' % (int(l[4:]) + 22)) if re.fullmatch(r'LBL (4[89]|5\d)', l) else l for l in tx]
    fixed = TABLES['MOON47'] | TABLES['M7SY'] | {'%02d' % n for n in range(70, 80)}
    tabs = [TABLES['MOON47'], {'%02d' % n for n in range(70, 80)}, TABLES['M7SY']]
    assert not (TABLES['MOON47'] & TABLES['M7SY'])
    entries = [l[5:-1] for p in P[1:] for l in p if l.startswith('LBL "')]
    letter = dict(zip(entries, LETTERS))
    rest = iter(LETTERS[len(entries):])
    free = iter(['%02d' % n for n in range(100) if '%02d' % n not in fixed])
    body = []
    for k, p in enumerate(P):
        s = p[:-1]
        if not B.exits(s, len(s) - 1):
            s = s + ['RTN']
        new = {}
        for l in s:
            if re.fullmatch(r'LBL \d\d', l) and l[4:] not in new:
                new[l[4:]] = l[4:] if l[4:] in tabs[k] else next(free, None) or next(rest)
        for l in s:
            m = JUMP.fullmatch(l)
            n = re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l)
            if n and n.group(2) in letter:
                l = '%s %s' % (n.group(1), letter[n.group(2)])
            elif m:
                l = '%s %s' % (m.group(1), new[m.group(2)])
            body.append(l)
    out = body + ['END']
    labs = [l[4:] for l in out if l.startswith('LBL ') and not l.startswith('LBL "')]
    assert len(labs) == len(set(labs)), 'duplicate label'
    assert not [l for l in out if re.fullmatch(r'(XEQ|GTO) "(.+)"', l)], 'a call by name is left'
    used = sorted(set(labs) & set(LETTERS), key=LETTERS.index)
    print('  2_compact: one program, %d steps, %d labels (%d numbers, letters %s), entries %s'
          % (len(out), len(labs), len(labs) - len(used), ' '.join(used),
             ' '.join('%s=%s' % (e, letter[e]) for e in entries)))
    return out


def main():
    L = [l for l in open(SRC, encoding='utf-8').read().split('\n') if l.strip()]
    for folder, step in (('1_labels', labels), ('2_compact', compact)):
        L = step(L)
        d = os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, 'MOON47.txt')
        open(f, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('  %s: %d steps, %d bytes' % (f[len(ROOT) + 1:], len(L), N.p47(f)))


if __name__ == '__main__':
    main()
