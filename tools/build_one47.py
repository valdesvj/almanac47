#!/usr/bin/env python3
"""build_one47.py - DEV: ALMA47 for the C47 / R47 as ONE program with local labels (branch dev-alma47-local).

v2.3.0's ALMA47 is 26 programs: ALMA47 and 25 more that start with a numbered global label N01, N02 ... (tools/
build_struct_src.py build_next, programs_struct/next/). Here they are one program, as tools/local_labels.py makes it:

  global labels   only LBL "ALMA47"; each other global label is a local label with the routine's original name:
                  LBL "N15" / XEQ "N15" -> LBL :SUNA: / XEQ :SUNA: (build_struct_src.LABELS: N15 = SUNA ...)
  inner labels    the 01-99 of each old program renumbered for the one program (a number can serve several routines
                  when no jump can land on the wrong one: the C47 looks for a local label first after the jump, then
                  from the start of the program). Labels reached by XEQ IND keep their number; the ones above their
                  XEQ IND (PLN3's planet table 11-13) are moved to the end of their routine.
  END             each inner END is an RTN (none after an RTN).

  build/dev/one/ALMA47.txt          the program
  build/dev/one/ALMA47_LABELS.txt   every local label: its original name and global label (N15 ...), what it does,
                                    and for each numbered label the routine it belongs to
  build/dev/one/ALMA47.p47          with rejig (not in git)

The C47 firmware is slower with one big program (every RTN and every jump to a :name: walks the program from its
start, DEVELOPMENT notes of v2.2.0's withdrawal): tests/test_one47.py compares the screens and the CPU time with
v2.3.0's 26 programs in the firmware simulator.

  python3 tools/build_one47.py
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import build_struct_src as B                                                  # noqa: E402
import local_labels as LL                                                     # noqa: E402
import c47struct as C                                                         # noqa: E402

OUT = os.path.join(ROOT, 'build', 'dev', 'one')
MAIN = 'ALMA47'


def names():
    """N.. -> the routine's original name (build_struct_src.LABELS), all different and at most 7 characters."""
    N = {g: n for g, (n, _) in B.LABELS.items() if g != 'NAV'}
    assert len(set(N.values())) == len(N) and all(len(n) <= 7 for n in N.values())
    return N


def listing():
    L = B.build_next()
    M = LL.convert(L, keep={'NAV'}, names=names())
    M = ['LBL "%s"' % MAIN if l == 'LBL "NAV"' else l for l in M]
    assert not C.check(M), C.check(M)[:5]
    return M


def owners(M):
    """For each step of M the routine (local :name: or ALMA47) it belongs to: the last named label above it."""
    own, cur = [], MAIN
    for l in M:
        m = re.fullmatch(r'LBL (?::(\S+):|"(\S+)")', l)
        if m:
            cur = m.group(1) or m.group(2)
        own.append(cur)
    return own


def labels_file(M):
    N = names()
    back = {n: g for g, n in N.items()}
    used = {re.fullmatch(r'LBL :(\S+):', l).group(1) for l in M if re.fullmatch(r'LBL :(\S+):', l)}
    step = {l[4:]: i + 1 for i, l in enumerate(M) if l.startswith('LBL ')}
    w = max(len(n) for n in used)
    out = ['ALMA47 (one program, local labels) - DEV build of v2.3.0 (tools/build_one47.py)',
           '=' * 78,
           'ALMA47 is ONE program: its only global label is ALMA47. Every routine is a local label with its',
           'original name (:SUNA:, :MOO2: ...); v2.3.0 (26 programs) called it by a numbered global label (N15 ...),',
           'given here next to it. A local label can only be called from inside ALMA47: XEQ :SUNA: from the keyboard',
           'or from another program is "no local label". The numbered labels 01-99 are inside the routines; a number',
           'can stand in several routines (the C47 finds the first one after the jump, else the first in the program).',
           '',
           'Local label%s  v2.3.0   Step  What it does' % (' ' * (w - 9)),
           '-' * 78]
    for l in M:
        m = re.fullmatch(r'LBL :(\S+):', l)
        if m:
            n = m.group(1)
            out.append(':%s:%s  %-7s %5d  %s' % (n, ' ' * (w - len(n)), back[n], step[l[4:]], B.LABELS[back[n]][1]))
    out += ['', 'Numbered labels: the routine each one is in (step)', '-' * 78]
    own = owners(M)
    by = {}
    for i, l in enumerate(M):
        m = re.fullmatch(r'LBL (\d\d|[A-La-l])', l)
        if m:
            by.setdefault(own[i], []).append('%s (%d)' % (m.group(1), i + 1))
    for r in [MAIN] + [n for n in (re.fullmatch(r'LBL :(\S+):', l) for l in M) if n for n in [n.group(1)]]:
        if r in by:
            out.append('%-*s  %s' % (w + 2, r if r == MAIN else ':%s:' % r, ', '.join(by[r])))
    return out


def write(path, L):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


def main():
    M = listing()
    write(os.path.join(OUT, 'ALMA47.txt'), M)
    write(os.path.join(OUT, 'ALMA47_LABELS.txt'), labels_file(M))
    nlab = sum(1 for l in M if l.startswith('LBL '))
    print('build/dev/one/ALMA47.txt: %d steps, %d labels (%d named), one END' %
          (len(M), nlab, sum(1 for l in M if l.startswith('LBL :'))))
    if shutil.which('rejig'):
        f = os.path.join(OUT, 'ALMA47.txt')
        r = subprocess.run(['rejig', '--validate=r47', '-o', f[:-4] + '.p47', f], capture_output=True, text=True)
        print('rejig:', 'ALMA47.p47' if r.returncode == 0 else (r.stdout + r.stderr)[-500:])


if __name__ == '__main__':
    main()
