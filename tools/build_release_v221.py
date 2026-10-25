#!/usr/bin/env python3
"""build_release_v221.py - Almanac 47 v2.2.1: the v2.2.0 programs with your stack kept (the trick from the SwissMicros
forum) and, on the C47 / R47, the keys 1-8 that pick a body of the ALMANAC / SPLIT table. One script for every build:

  build/v2.2.1/c47/      C47 / R47 (and DM42n with the C47 firmware): ALMA47 and MOON47 of programs_struct/next/
                         (tools/build_next.py), ALMA47_LABELS.txt, QUICKSTART.txt, p47u/ (the rejig sources with the
                         '@' header and the comments); NAVINIT_FAST / NAVINIT_FULL: v2.2.0's (build/c47/)
  build/v2.2.1/dm42/     the old DM42 with the C47 firmware (64 KiB, at most 10 IF / DO / REPEAT a program):
                         NAVLITTLE of programs_struct/little/NAVLITTLE_221.txt (named ALMA47), NAVINIT_LITTLE: v2.2.0's,
                         MOON47 of programs_struct/next/MOON47.txt (tools/build_release_c47.moon_dm42), README_DM42.txt
  build/v2.2.1/free42/   Free42 (DM42 / DM42n with the stock firmware, Free42 / Plus42 on a PC or phone): NAVFULL (big)
                         and NAVLITTLE (tiny) and MOON47 of v2.1.0 (build/free42/) with your X Y Z T and LASTx kept;
                         README_F42.txt; the .raw files with tools/f42/f42run; NAVINIT_*, TBL_1, TBL_5: v2.1.0's

Your stack:
  C47 / R47 / DM42   LocR 9 (45 in NAVLITTLE), STOS R.00 (the 8 levels, X ... D), RCL L, STO R.08 at the start;
                     RCL R.08, STO L, RCLS R.00 at the end. The local registers go with the program's RTN.
  Free42             no STOS and no local registers: X Y Z T and LASTX in the variables S7X ... S7L at the start
                     (4-level stack, the HP-42S stack); at the end STO ST L, CLST, the four RCL, CLV of the five.

With rejig (~/.local/bin/rejig): the .p47 files (rejig --validate=r47 for the C47 / R47). With the manual built
(python3 tools/generators/build_manual.py -> build/manuals/C47_Nav_User_Manual.pdf): the zips in build/v2.2.1/
  Almanac47_C47_R47_v2.2.1.zip, Almanac47_DM42_C47firmware_v2.2.1.zip, Almanac47_Free42_DM42_v2.2.1.zip
(the .p47 and the zips are not in git).

  python3 tools/build_release_v221.py
"""
import os, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'python')]
import build_struct_src as B                                                  # noqa: E402
import build_release_c47 as R                                                 # noqa: E402
import build_next as NX                                                       # noqa: E402

VERSION = '2.2.1'
OUT = os.path.join(ROOT, 'build', 'v' + VERSION)
C47, DM42, F42 = (os.path.join(OUT, d) for d in ('c47', 'dm42', 'free42'))
MANUAL = os.path.join(ROOT, 'build', 'manuals', 'C47_Nav_User_Manual.pdf')
F42RUN = os.path.join(ROOT, 'tools', 'f42', 'f42run')
LITTLE = os.path.join(ROOT, 'programs_struct', 'little', 'NAVLITTLE_221.txt')
MOON_NEXT = os.path.join(ROOT, 'programs_struct', 'next', 'MOON47.txt')

# Free42: your X Y Z T and LASTX into named variables at the start, back at the end (in place of CLST)
F42_SAVE = ['STO "S7X"', 'R↓', 'STO "S7Y"', 'R↓', 'STO "S7Z"', 'R↓', 'STO "S7T"', 'R↓', 'LASTX', 'STO "S7L"']
F42_BACK = ['RCL "S7L"', 'STO ST L', 'CLST', 'RCL "S7T"', 'RCL "S7Z"', 'RCL "S7Y"', 'RCL "S7X"',
            'CLV "S7X"', 'CLV "S7Y"', 'CLV "S7Z"', 'CLV "S7T"', 'CLV "S7L"']


def lines(f):
    return [l.rstrip('\n') for l in open(f, encoding='utf-8') if l.strip()]


def write(path, L):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


def f42_stack(L, label):
    """A Free42 listing of v2.1.0 with your stack kept: F42_SAVE after LBL "label" (its first step), and the one end
    of the program (CLST, CLD, RTN) with F42_BACK in place of CLST. SystemExit when the listing is not as expected."""
    first = L.index('LBL "%s"' % label)
    ends = [i for i in range(len(L) - 2) if L[i:i + 3] == ['CLST', 'CLD', 'RTN']]
    if len(ends) != 1 or ends[0] < first:
        raise SystemExit('build_release_v221: %s: %d ends CLST CLD RTN (one expected)' % (label, len(ends)))
    if any(l.startswith('STO "S7') or l.startswith('RCL "S7') for l in L):
        raise SystemExit('build_release_v221: %s already uses S7*' % label)
    e = ends[0]
    return L[:first + 1] + F42_SAVE + L[first + 1:e] + F42_BACK + L[e + 1:]


def free42():
    src = os.path.join(ROOT, 'build', 'free42')
    out = {}
    for name, label in (('NAVFULL', 'NAV'), ('NAVLITTLE', 'NAV'), ('MOON47', 'MOON47')):
        out[name] = f42_stack(lines(os.path.join(src, name + '.txt')), label)
        write(os.path.join(F42, name + '.txt'), out[name])
    readme = open(os.path.join(src, 'README_F42.txt'), encoding='utf-8').read()
    note = ('\nv2.2.1: NAVFULL, NAVLITTLE and MOON47 keep your stack: X Y Z T and LASTX are as before XEQ "NAV" /\n'
            'XEQ "MOON47" when they end (saved in the variables S7X S7Y S7Z S7T S7L, deleted at the end; the HP-42S\n'
            '4-level stack). The screens and the keys are those of v2.1.0. NAVINIT_*, TBL_1, TBL_5: as v2.1.0.\n')
    head, sep, rest = readme.partition('\n\n')
    open(os.path.join(F42, 'README_F42.txt'), 'w', encoding='utf-8').write(head + '\n' + note + sep.lstrip('\n') + '\n' + rest
                                                                           if sep else readme + note)
    if not os.path.exists(F42RUN):
        print('  no tools/f42/f42run (sh tools/f42/setup.sh): Free42 .raw files not written')
        return
    for name in ('NAVFULL', 'NAVLITTLE', 'MOON47'):
        txt = os.path.join(F42, name + '.txt')
        subprocess.run([F42RUN], input='paste %s\nexport %s\n' % (txt, txt[:-4] + '.raw'), text=True, capture_output=True,
                       timeout=600, check=True)


def c47():
    L = B.build_next()
    write(os.path.join(C47, 'ALMA47.txt'), ['LBL "ALMA47"'] + L[1:])
    write(os.path.join(C47, 'MOON47.txt'), B.build_moon(B.NEXT))
    lab = R.labels_file(L)
    lab[0] = lab[0].replace('v%s "%s"' % (R.VERSION, R.NAME), 'v%s' % VERSION)
    write(os.path.join(C47, 'ALMA47_LABELS.txt'), lab)
    NX.main()                                                       # build/dev/next/*.p47u, the 2.2.1 headers
    os.makedirs(os.path.join(C47, 'p47u'), exist_ok=True)
    for name in ('ALMA47', 'MOON47'):
        shutil.copyfile(os.path.join(NX.OUT, name + '.p47u'), os.path.join(C47, 'p47u', name + '.p47u'))


def dm42():
    S, I = R.little(LITTLE)
    write(os.path.join(DM42, 'NAVLITTLE.txt'), S)
    assert I == lines(os.path.join(R.DM42, 'NAVINIT_LITTLE.txt')), 'NAVINIT_LITTLE is the one of v2.2.0'
    write(os.path.join(DM42, 'MOON47.txt'), R.moon_dm42(MOON_NEXT, 4))
    readme = open(os.path.join(ROOT, 'build', 'c47', 'dm42', 'README_DM42.txt'), encoding='utf-8').read()
    note = ('\nv2.2.1: ALMA47 (NAVLITTLE) and MOON47 keep your stack: X ... D (the 8 levels) and LASTx are as before\n'
            'XEQ when they end (LocR, STOS / RCLS, the trick from the SwissMicros forum). Screens and keys as v2.2.0.\n')
    head, sep, rest = readme.partition('\n\n')
    open(os.path.join(DM42, 'README_DM42.txt'), 'w', encoding='utf-8').write(head + '\n' + note + sep.lstrip('\n') + '\n' + rest
                                                                            if sep else readme + note)


def p47(path, validate):
    out = path[:-4] + '.p47'
    cmd = ['rejig'] + (['--validate=r47'] if validate else []) + ['-o', out, path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('rejig %s: %s' % (path, r.stderr or r.stdout))
    return os.path.getsize(out)


def zips():
    c, d, f, f0 = C47, DM42, F42, os.path.join(ROOT, 'build', 'free42')
    c0, d0, forum = os.path.join(ROOT, 'build', 'c47'), R.DM42, os.path.join(ROOT, 'build', 'forum')
    j = os.path.join
    files = {
        'Almanac47_C47_R47_v%s.zip' % VERSION: ('Almanac47_C47', MANUAL, [
            (j(c, n), n) for n in ('ALMA47.p47', 'ALMA47.txt', 'ALMA47_LABELS.txt', 'MOON47.p47', 'MOON47.txt',
                                   'QUICKSTART.txt')] +
            [(j(c0, n), n) for n in ('NAVINIT_FAST.p47', 'NAVINIT_FAST.txt', 'NAVINIT_FULL.p47', 'NAVINIT_FULL.txt')] +
            [(j(c, 'p47u', n), 'p47u/' + n) for n in ('ALMA47.p47u', 'MOON47.p47u')] +
            [(j(forum, n), 'p47u/' + n) for n in ('NAVINIT.p47u', 'NAVINIT_FULL.p47u')]),
        'Almanac47_DM42_C47firmware_v%s.zip' % VERSION: ('Almanac47_DM42_C47', MANUAL, [
            (j(d, n), n) for n in ('NAVLITTLE.p47', 'NAVLITTLE.txt', 'MOON47.p47', 'MOON47.txt', 'README_DM42.txt')] +
            [(j(d0, n), n) for n in ('NAVINIT_LITTLE.p47', 'NAVINIT_LITTLE.txt')]),
        'Almanac47_Free42_DM42_v%s.zip' % VERSION: ('Almanac47_Free42', j(ROOT, 'docs', 'Almanac47_Free42_Manual.pdf'), [
            (j(f, n), n) for n in ('NAVFULL.raw', 'NAVFULL.txt', 'NAVLITTLE.raw', 'NAVLITTLE.txt', 'MOON47.raw', 'MOON47.txt',
                                   'README_F42.txt')] +
            [(j(f0, n), n) for n in ('NAVINIT_FULL.raw', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.raw', 'NAVINIT_FAST.txt',
                                     'NAVINIT_LITTLE.raw', 'NAVINIT_LITTLE.txt', 'TBL_1.raw', 'TBL_5.raw',
                                     'NAVFULL_LABELS.txt', 'NAVLITTLE_LABELS.txt')])}
    common = [(j(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md', 'RELEASE_NOTES_v2.2.1.md')]
    for zname, (folder, manual, entries) in files.items():
        z_ = j(OUT, zname)
        entries = entries + common + [(manual, os.path.basename(manual))]
        with zipfile.ZipFile(z_, 'w', zipfile.ZIP_DEFLATED) as z:
            for src, n in entries:
                z.write(src, '%s/%s' % (folder, n))
        print('  %s: %d files' % (os.path.relpath(z_, ROOT), len(entries)))


def main():
    c47()
    shutil.copyfile(os.path.join(ROOT, 'build', 'c47', 'QUICKSTART.txt'), os.path.join(C47, 'QUICKSTART.txt'))
    dm42()
    free42()
    rejig = shutil.which('rejig')
    for d, names, validate in ((C47, ('ALMA47', 'MOON47'), True), (os.path.join(ROOT, 'build', 'c47'),
                               ('NAVINIT_FAST', 'NAVINIT_FULL'), True), (DM42, ('NAVLITTLE', 'MOON47'), False),
                               (R.DM42, ('NAVINIT_LITTLE',), False)):
        for name in names:
            path = os.path.join(d, name + '.txt')
            size = p47(path, validate) if rejig else None
            print('  %s: %d steps; .p47 %s' % (os.path.relpath(path, ROOT), len(lines(path)),
                                               '%d bytes' % size if size else '? (no rejig)'))
    for name in ('NAVFULL', 'NAVLITTLE', 'MOON47'):
        path = os.path.join(F42, name + '.txt')
        raw = path[:-4] + '.raw'
        print('  %s: %d lines; .raw %s' % (os.path.relpath(path, ROOT), len(lines(path)),
                                          '%d bytes' % os.path.getsize(raw) if os.path.exists(raw) else '?'))
    if not rejig or not os.path.exists(MANUAL):
        print('  no zips: %s' % ('rejig missing' if not rejig else 'build the manual first (tools/generators/build_manual.py)'))
        return
    zips()


if __name__ == '__main__':
    main()
