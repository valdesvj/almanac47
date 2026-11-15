#!/usr/bin/env python3
"""build_r47_v230.py - Almanac 47 v2.3.0 for the R47 keyboard: the same release as build/v2.3.0/c47/ with ALMA47's
arrow keys where the R47 has them.

KEY? gives the key's place (row and column, firmware: items.c KEY?), not its function. The R47 has the same keyboard
as the C47 with other functions on it (~/opt/c43 src/c47/assign.c, kbd_std_C47 and the four R47 layouts kbd_std_R47*):
the arrows are one row lower,

                C47   R47 (f g, bk fg, fg bk, fg g)
    up arrow     51    61          (51 on the R47: XEQ)
    down arrow   61    71          (71 on the C47: the shift key)

and every other key ALMA47 reads is in the same place on both: 1-8 (72-74, 62-64, 52-53), 9 SNAP (54), +/- (43),
+ (85), 0 (82), the softkeys. So the R47 ALMA47 is the C47 one with:
  - the menu and the views' +-1 hour: (56 - key) / 5 for the keys 51 / 61 -> (66 - key) / 5 for 61 / 71, and the
    'redraw' code 56 that LBL 09 (+/-) leaves in R17 -> 66 (no key has 56 on the C47 nor 66 on the R47): 8 steps 56
    -> 66 (the 9th 56 of ALMA47 is a number of the STOSEQ table at its start and stays);
  - the views that end on an arrow (WPLS, HORZ): RCL 67 (R67 = 51, also a pixel coordinate: kept) -> 61 and 61 -> 71.
MOON47 reads only +/- and 0, NAVINIT reads no key: the C47 files. The step numbers do not change: ALMA47_LABELS.txt
is the C47 one.

From build/v2.3.0/c47/ (python3 tools/build_release_v230.py first) and the C47 manual (build/manuals/):
  build/v2.3.0/r47/                   ALMA47.txt, p47u/ALMA47.p47u (the R47 keys), README_R47.txt, QUICKSTART.txt
  build/v2.3.0/r47/ALMA47.p47         with rejig --validate=r47 (not in git)
  build/v2.3.0/Almanac47_R47_v2.3.0.zip

  python3 tools/build_r47_v230.py
"""
import os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import build_release_v230 as V                                               # noqa: E402

C47 = V.C47
R47 = os.path.join(V.OUT, 'r47')
ZIP = os.path.join(V.OUT, 'Almanac47_R47_v%s.zip' % V.VERSION)
CENTRE = 8                          # the 56 of the arrow arithmetic and of LBL 09
EXITS = 2                           # RCL 17 / RCL 67 / X=Y? / RTN / RCL 17 / 61 / X=Y? / RTN
EXIT_C47 = ['RCL 17', 'RCL 67', 'X=Y?', 'RTN', 'RCL 17', '61', 'X=Y?', 'RTN']
EXIT_R47 = ['RCL 17', '61', 'X=Y?', 'RTN', 'RCL 17', '71', 'X=Y?', 'RTN']


def step(line):
    """the step of a listing or p47u line: no indent, no '; comment'"""
    return line.split(';')[0].strip()


def r47(L):
    """the C47 ALMA47 (a listing or a p47u: one step a line, '@' / blank lines kept) with the R47 arrows"""
    L = list(L)
    S = [step(l) if l.strip() and not l.startswith('@') else None for l in L]

    def put(i, new):
        L[i] = L[i].replace(S[i], new, 1)
        S[i] = new
    centre = [i for i, s in enumerate(S) if s == '56' and not (i + 1 < len(S) and S[i + 1] == 'STOSEQ')]
    exits = [i for i in range(len(S) - 7) if S[i:i + 8] == EXIT_C47]
    if len(centre) != CENTRE or len(exits) != EXITS:
        raise SystemExit('build_r47_v230: %d steps 56 (want %d), %d arrow exits (want %d): the C47 ALMA47 changed, check '
                         'its keys again' % (len(centre), CENTRE, len(exits), EXITS))
    for i in centre:
        put(i, '66')
    for i in exits:
        for k, (old, new) in enumerate(zip(EXIT_C47, EXIT_R47)):
            if old != new:
                put(i + k, new)
    return L


def lines(f):
    return open(f, encoding='utf-8').read().rstrip('\n').split('\n')


def write(path, L):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


README = """ALMANAC 47 v2.3.0 "Local Time" - R47 KEYBOARD
=============================================

The same release as Almanac47_C47_R47_v2.3.0.zip, with ALMA47 reading the arrow keys where the R47 has
them. The programs read a key by its place on the keyboard, and the R47 has its up and down arrows one row
lower than the C47 (the C47 build on an R47: XEQ is "one hour later" and the up arrow "one hour earlier").
Here, as the R47 keyboard says:

  up arrow     one hour later (the menu and every view)      C47 build: the 5th row, R47: the 6th row
  down arrow   one hour earlier                              C47 build: the 6th row, R47: the 7th row

The rest is the C47 build's, key for key: the numbers 1-8, 9 SNAP, + menu, +/- UT / local time, 0 ends,
the softkeys. MOON47 and NAVINIT read no arrow: they are the C47 files. Any of the four R47 layouts
(f g, bk fg, fg bk, fg g) has the arrows in these places.

Load ALMA47.p47 of this folder, NAVINIT_FAST.p47 (or NAVINIT_FULL.p47) and, if you like, MOON47.p47, as in
QUICKSTART.txt. The manual (C47_Nav_User_Manual.pdf) is the C47 one: its keys are named by their function
(up / down arrow), so it reads the same on the R47.
"""


def quickstart():
    q = open(os.path.join(C47, 'QUICKSTART.txt'), encoding='utf-8').read()
    head = ('Almanac 47 v2.3.0 "Local Time" - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
            '=========================================================================================\n')
    new = ('Almanac 47 v2.3.0 "Local Time" - QUICK START, R47 KEYBOARD\n'
           '===========================================================\n\n'
           'THIS FOLDER: ALMA47 with the up / down arrows of the R47 keyboard (README_R47.txt). For the C47 and\n'
           'the DM42n with the C47 firmware: Almanac47_C47_R47_v2.3.0.zip.\n')
    if q.count(head) != 1:
        raise SystemExit('build_r47_v230: the title of c47/QUICKSTART.txt changed')
    return q.replace(head, new).rstrip('\n').split('\n')


def main():
    alma = r47(lines(os.path.join(C47, 'ALMA47.txt')))
    write(os.path.join(R47, 'ALMA47.txt'), alma)
    src = r47(lines(os.path.join(C47, 'p47u', 'ALMA47.p47u')))
    src = [l.replace('@ Tested:  C47 simulator', '@ Tested:  R47 keyboard (up 61, down 71); C47 simulator', 1)
           if l.startswith('@ Tested:  C47 simulator') else l for l in src]
    write(os.path.join(R47, 'p47u', 'ALMA47.p47u'), src)
    assert [step(l) for l in src if l.strip() and not l.startswith('@')] == alma, 'p47u = the listing'
    open(os.path.join(R47, 'README_R47.txt'), 'w', encoding='utf-8').write(README)
    write(os.path.join(R47, 'QUICKSTART.txt'), quickstart())
    diff = sum(a != b for a, b in zip(alma, lines(os.path.join(C47, 'ALMA47.txt'))))
    print('  build/v2.3.0/r47/ALMA47.txt: %d steps, %d changed from the C47 one' % (len(alma), diff))
    if not shutil.which('rejig'):
        print('  no .p47, no zip: rejig missing')
        return
    print('  build/v2.3.0/r47/ALMA47.p47: %d bytes' % V.p47(os.path.join(R47, 'ALMA47.txt'), True))
    if not os.path.exists(V.MANUAL):
        print('  no zip: build the manual first (tools/generators/build_manual.py)')
        return
    j, c0, forum = os.path.join, os.path.join(ROOT, 'build', 'c47'), os.path.join(ROOT, 'build', 'forum')
    entries = ([(j(R47, n), n) for n in ('ALMA47.p47', 'ALMA47.txt', 'README_R47.txt', 'QUICKSTART.txt')] +
               [(j(C47, n), n) for n in ('ALMA47_LABELS.txt', 'MOON47.p47', 'MOON47.txt')] +
               [(j(c0, n), n) for n in ('NAVINIT_FAST.p47', 'NAVINIT_FAST.txt', 'NAVINIT_FULL.p47', 'NAVINIT_FULL.txt')] +
               [(j(R47, 'p47u', 'ALMA47.p47u'), 'p47u/ALMA47.p47u'), (j(C47, 'p47u', 'MOON47.p47u'), 'p47u/MOON47.p47u')] +
               [(j(forum, n), 'p47u/' + n) for n in ('NAVINIT.p47u', 'NAVINIT_FULL.p47u')] +
               [(j(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md', V.NOTES)] +
               [(V.MANUAL, os.path.basename(V.MANUAL))])
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for s, n in entries:
            z.write(s, 'Almanac47_R47/' + n)
    print('  %s: %d files' % (os.path.relpath(ZIP, ROOT), len(entries)))


if __name__ == '__main__':
    main()
