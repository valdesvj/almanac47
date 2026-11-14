#!/usr/bin/env python3
"""build_release_v230.py - Almanac 47 v2.3.0 "Local Time": v2.2.1 with every time in UT or in local time on +/-
(all builds) and, on the C47 / R47, the header of NAV47's top bar. One script for every build, from the next
version (tools/build_next.py, tools/build_next_f42.py: build/dev/next/):

  build/v2.3.0/c47/      C47 / R47 (and the DM42n with the C47 firmware): ALMA47 and MOON47 of programs_struct/next/,
                         ALMA47_LABELS.txt, QUICKSTART.txt, p47u/ (the rejig sources with the '@' header and the
                         comments); NAVINIT_FAST / NAVINIT_FULL: v2.2.0's (build/c47/)
  build/v2.3.0/dm42/     the old DM42 with the C47 firmware (64 KiB): NAVLITTLE (the program ALMA47, the stack kept,
                         UT / LT on +/-), MOON47, README_DM42.txt; NAVINIT_LITTLE: v2.2.0's (build/c47/dm42/)
  build/v2.3.0/free42/   Free42 (DM42 / DM42n with the stock firmware, Free42 / Plus42): NAVFULL, NAVLITTLE, MOON47
                         of v2.2.1 with UT / LT on +/- (the Free42 key +/-); README_F42.txt; the .raw files
                         (tools/f42/f42run); NAVINIT_*, TBL_1, TBL_5: v2.1.0's (build/free42/)

UT / LT: LT = UT + the variable TZ (hours, east +); +/- on the menu or a view switches every time shown (the header,
rise, set, twilights, meridian passage, MOON47's next phases); the switch is the variable TZLT (0 UT, 1 LT), kept
between runs. DATE and UTC are still asked in UT.

With rejig (~/.local/bin/rejig): the .p47 files (rejig --validate=r47 for the C47 / R47). With the manuals built
(python3 tools/generators/build_manual.py and build_port_manuals.py -> build/manuals/): the zips in build/v2.3.0/
  Almanac47_C47_R47_v2.3.0.zip, Almanac47_DM42_C47firmware_v2.3.0.zip, Almanac47_Free42_DM42_v2.3.0.zip
(the .p47 and the zips are not in git).

  python3 tools/build_release_v230.py
"""
import os, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'python')]
import build_release_c47 as R                                                 # noqa: E402
import build_next as NX                                                       # noqa: E402
import build_next_f42 as NF                                                   # noqa: E402

VERSION = '2.3.0'
NAME = 'Local Time'
PREV = os.path.join(ROOT, 'build', 'v2.2.1')                    # the texts this release starts from
OUT = os.path.join(ROOT, 'build', 'v' + VERSION)
C47, DM42, F42 = (os.path.join(OUT, d) for d in ('c47', 'dm42', 'free42'))
MANUAL = os.path.join(ROOT, 'build', 'manuals', 'C47_Nav_User_Manual.pdf')
MANUAL_F42 = os.path.join(ROOT, 'build', 'manuals', 'Almanac47_Free42_Manual.pdf')
NOTES = 'RELEASE_NOTES_v%s.md' % VERSION


def lines(f):
    return [l.rstrip('\n') for l in open(f, encoding='utf-8') if l.strip()]


def write(path, L):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


def replace(text, pairs, what):
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('build_release_v230 %s: %r not found once' % (what, old[:60]))
        text = text.replace(old, new)
    return text


def note(readme, text):
    """a v2.3.0 paragraph after the title of a README (the title: up to the first blank line)"""
    head, sep, rest = readme.partition('\n\n')
    return head + '\n\n' + text + '\n' + rest if sep else readme + '\n' + text


def c47():
    NX.main()                                                       # build/dev/next/: ALMA47, MOON47, *.p47u, dm42/
    import build_struct_src as B
    L = B.build_next()                                              # LBL "NAV" ...: the labels file reads that
    A = ['LBL "ALMA47"'] + L[1:]
    assert A == lines(os.path.join(NX.OUT, 'ALMA47.txt')), 'ALMA47 is build/dev/next/ALMA47.txt'
    write(os.path.join(C47, 'ALMA47.txt'), A)
    write(os.path.join(C47, 'MOON47.txt'), lines(os.path.join(NX.OUT, 'MOON47.txt')))
    lab = R.labels_file(L)
    lab[0] = lab[0].replace('v%s "%s"' % (R.VERSION, R.NAME), 'v%s "%s"' % (VERSION, NAME))
    write(os.path.join(C47, 'ALMA47_LABELS.txt'), lab)
    os.makedirs(os.path.join(C47, 'p47u'), exist_ok=True)
    for name in ('ALMA47', 'MOON47'):
        shutil.copyfile(os.path.join(NX.OUT, name + '.p47u'), os.path.join(C47, 'p47u', name + '.p47u'))


UTLT = ('          +/- (the change-sign key) on the menu or a view: every time in UT or in local time,\n'
        '          LT = UT + TZ. Your time zone first: e.g. 3 STO "TZ" (UTC+3), -5 STO "TZ" (UTC-5), 5.5 for\n'
        '          UTC+5:30. The header shows UT or LT; rise, set, twilights and meridian passage follow it. The\n'
        '          choice is kept in the variable TZLT (0 UT, 1 LT) between runs. DATE and UTC are asked in UT.')


def quickstart():
    """QUICKSTART.txt of v2.3.0: v2.2.1's with UT / LT on +/-, the new header, the version and the zips."""
    q = open(os.path.join(PREV, 'c47', 'QUICKSTART.txt'), encoding='utf-8').read()
    q = replace(q, (
        ('Almanac 47 v2.2.1 - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
         '==============================================================================',
         'Almanac 47 v2.3.0 "Local Time" - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
         '========================================================================================='),
        ('Almanac47_Free42_DM42_v2.2.1.zip - the programs of v2.1.0, now keeping your stack (README_F42.txt).',
         'Almanac47_Free42_DM42_v2.3.0.zip - the programs of v2.1.0, keeping your stack, with UT / LT on +/-\n'
         '(README_F42.txt).'),
        ('Almanac47_DM42_C47firmware_v2.2.1.zip', 'Almanac47_DM42_C47firmware_v2.3.0.zip'),
        ('The almanac tables (TBL) of earlier versions are not part of v2.2.x.',
         'The almanac tables (TBL) of earlier versions are not part of v2.2 / v2.3.'),
        ('          one hour later / earlier, 9 SNAP (a screenshot). On the menu the arrows change the hour too.\n',
         '          one hour later / earlier, 9 SNAP (a screenshot). On the menu the arrows change the hour too.\n'
         + UTLT + '\n'
         '          The header of each view: the date and time on the left, the view\'s name in the middle,\n'
         '          the position (your DR) on the right; T or S at the end (tables or series), as before.\n'),
        ('WHAT IS NEW IN v2.2.1:', 'WHAT IS NEW IN v2.3.0 "Local Time": +/- shows every time in UT or in local time (ALMA47 and\n'
         '  MOON47; the variables TZ and TZLT), and a new header on every view: date and time, the view\'s name,\n'
         '  the position. The rest as v2.2.1. On the menu 0 ends ALMA47 as before; MOON47\'s south view is on 0 now.\n\n'
         'WHAT WAS NEW IN v2.2.1:'),
        ('MEMORY (program bytes, measured with rejig): ALMA47 27.2 KB, MOON47 4.5 KB; NAVINIT while loaded:',
         'MEMORY (program bytes, rejig): ALMA47 about 27.6 KB, MOON47 about 4.6 KB; NAVINIT while loaded:'),
        ('  +/- turns the picture to the view from the south, any other key ends. Your stack and LASTx come\n',
         '  0 turns the picture to the view from the south, +/- shows the header and the next phases in UT or\n'
         '  LT (LT = UT + TZ, as ALMA47), any other key ends. Your stack and LASTx come\n')), 'QUICKSTART')
    return q.rstrip('\n').split('\n')


def dm42():
    d = os.path.join(NX.OUT, 'dm42')
    write(os.path.join(DM42, 'NAVLITTLE.txt'), lines(os.path.join(d, 'ALMA47.txt')))
    write(os.path.join(DM42, 'MOON47.txt'), lines(os.path.join(d, 'MOON47.txt')))
    readme = open(os.path.join(PREV, 'dm42', 'README_DM42.txt'), encoding='utf-8').read()
    readme = readme.replace('ALMANAC 47 v2.2.0 "Struct on Attack" LITTLE', 'ALMANAC 47 v2.3.0 "Local Time" LITTLE', 1)
    readme = note(readme, 'v2.3.0: +/- shows the times in UT or in local time, LT = UT + the variable TZ (e.g. 3 STO "TZ"\n'
                          'for UTC+3); the choice is kept in TZLT. In ALMA47 (NAVLITTLE) +/- redraws ALMANAC; in MOON47\n'
                          '+/- switches and 0 turns to the view from the south. DATE and UTC are asked in UT.')
    open(os.path.join(DM42, 'README_DM42.txt'), 'w', encoding='utf-8').write(readme)


def free42():
    NF.main()                                                       # build/dev/next/free42/: the .txt and the .raw
    for name in ('NAVFULL', 'NAVLITTLE', 'MOON47'):
        for ext in ('.txt', '.raw'):
            src = os.path.join(NF.OUT, name + ext)
            if os.path.exists(src):
                os.makedirs(F42, exist_ok=True)
                shutil.copyfile(src, os.path.join(F42, name + ext))
    readme = open(os.path.join(PREV, 'free42', 'README_F42.txt'), encoding='utf-8').read()
    readme = note(readme, 'v2.3.0: the key +/- shows every time in UT or in local time, LT = UT + the variable TZ\n'
                          '(e.g. 3 STO "TZ" for UTC+3); the choice is the variable TZLT (0 UT, 1 LT), kept. NAVFULL: +/-\n'
                          'on the menu or a view; NAVLITTLE: +/- redraws ALMANAC; MOON47: +/- switches, 0 the south.\n'
                          'In LT the header shows the date and time + TZ and LT; rise, set, twilights and meridian\n'
                          'passage + TZ. DATE and UT are asked in UT.')
    open(os.path.join(F42, 'README_F42.txt'), 'w', encoding='utf-8').write(readme)


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
        'Almanac47_Free42_DM42_v%s.zip' % VERSION: ('Almanac47_Free42', MANUAL_F42, [
            (j(f, n), n) for n in ('NAVFULL.raw', 'NAVFULL.txt', 'NAVLITTLE.raw', 'NAVLITTLE.txt', 'MOON47.raw', 'MOON47.txt',
                                   'README_F42.txt')] +
            [(j(f0, n), n) for n in ('NAVINIT_FULL.raw', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.raw', 'NAVINIT_FAST.txt',
                                     'NAVINIT_LITTLE.raw', 'NAVINIT_LITTLE.txt', 'TBL_1.raw', 'TBL_5.raw',
                                     'NAVFULL_LABELS.txt', 'NAVLITTLE_LABELS.txt')])}
    common = [(j(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md', NOTES)]
    for zname, (folder, manual, entries) in files.items():
        z_ = j(OUT, zname)
        entries = entries + common + [(manual, os.path.basename(manual))]
        with zipfile.ZipFile(z_, 'w', zipfile.ZIP_DEFLATED) as z:
            for src, n in entries:
                z.write(src, '%s/%s' % (folder, n))
        print('  %s: %d files' % (os.path.relpath(z_, ROOT), len(entries)))


def main():
    c47()
    write(os.path.join(C47, 'QUICKSTART.txt'), quickstart())
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
    if not rejig or not os.path.exists(MANUAL) or not os.path.exists(MANUAL_F42):
        print('  no zips: %s' % ('rejig missing' if not rejig else 'build the manuals first (tools/generators/build_manual.py '
                                 'and build_port_manuals.py)'))
        return
    zips()


if __name__ == '__main__':
    main()
