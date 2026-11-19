#!/usr/bin/env python3
"""build_release_v240.py - Almanac 47 v2.4.0 "Here and Now": v2.3.0 with the five prompts on every build

  TZ    asked first (INPUT "TZ", R/S keeps the last one; 0 at first): the hours of the calculator's clock from UT
  DATE  the clock's date as UT (the clock - TZ, the date moved a day when UT is on another day)
  UTC   the clock's time as UT, HH.MMSS
  LAT   your last latitude; Medellin, 6 13.9 N (6.139), before any position is stored (LAT and LON 0 or missing)
  LON   your last longitude; Medellin, 75 35.4 W (-75.354)
So R/S five times = the sky now, where you are. Sources: programs_struct/next/NAV.txt (C47 / R47),
programs_struct/little/NAVLITTLE_240.txt (the old DM42 with the C47 firmware), tools/build_next_f42.py defaults()
(Free42 NAVFULL / NAVLITTLE). MOON47 as v2.3.0 (its header says 2.4.0).

The same folders and zips as v2.3.0 (tools/build_release_v230.py, whose c47(), p47() and zips() this uses), and the R47
keyboard build (tools/build_r47_v230.py r47(): the arrows 61 / 71):
  build/v2.4.0/c47/  dm42/  free42/  r47/
  build/v2.4.0/Almanac47_C47_R47_v2.4.0.zip, Almanac47_DM42_C47firmware_v2.4.0.zip, Almanac47_Free42_DM42_v2.4.0.zip,
  Almanac47_R47_v2.4.0.zip   (the .p47 and the zips are not in git; the manuals first: build_manual.py and
  build_port_manuals.py -> build/manuals/)

  python3 tools/build_release_v240.py
"""
import os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'python')]
import build_release_v230 as V                                                # noqa: E402
import build_r47_v230 as R4                                                   # noqa: E402

VERSION = '2.4.0'
NAME = 'Here and Now'
PREV = os.path.join(ROOT, 'build', 'v2.3.0')
OUT = os.path.join(ROOT, 'build', 'v' + VERSION)
C47, DM42, F42, R47 = (os.path.join(OUT, d) for d in ('c47', 'dm42', 'free42', 'r47'))
NOTES = 'RELEASE_NOTES_v%s.md' % VERSION
# v2.3.0's functions write into these
V.VERSION, V.NAME, V.PREV, V.OUT, V.C47, V.DM42, V.F42, V.NOTES = VERSION, NAME, PREV, OUT, C47, DM42, F42, NOTES

lines, write, replace, note = V.lines, V.write, V.replace, V.note

PROMPTS = ('          R/S keeps each value shown: TZ your last one (0 at first); DATE and UTC the calculator\'s\n'
           '          clock now, as UT (the clock - TZ); LAT and LON your last position (Medellin, 6 13.9 N\n'
           '          75 35.4 W, until you give your own). With TZ set: R/S five times = the sky now, here.\n'
           '          Set the calculator\'s clock (CLK menu) to your local time.\n')


def quickstart():
    """v2.3.0's QUICKSTART with the five prompts, the version and the zips."""
    q = open(os.path.join(PREV, 'c47', 'QUICKSTART.txt'), encoding='utf-8').read()
    q = replace(q, (
        ('Almanac 47 v2.3.0 "Local Time" - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
         '=========================================================================================',
         'Almanac 47 v2.4.0 "Here and Now" - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
         '==========================================================================================='),
        ('Almanac47_Free42_DM42_v2.3.0.zip - the programs of v2.1.0, keeping your stack, with UT / LT on +/-\n',
         'Almanac47_Free42_DM42_v2.4.0.zip - the programs of v2.1.0, keeping your stack, with UT / LT on +/-\n'
         'and TZ asked first '),
        ('Almanac47_DM42_C47firmware_v2.3.0.zip', 'Almanac47_DM42_C47firmware_v2.4.0.zip'),
        ('not part of v2.2 / v2.3.', 'not part of v2.2 - v2.4.'),
        ('4. RUN    XEQ "ALMA47": it asks (once) DATE, UTC, LAT, LON with INPUT (R/S keeps the value shown):\n',
         '4. RUN    XEQ "ALMA47": it asks (once) TZ, DATE, UTC, LAT, LON with INPUT (R/S keeps the value shown):\n'
         '            TZ    the hours of your clock from UT, west negative: -5 Colombia, 3 UTC+3, 5.5 India\n'),
        ('            LON   DDD.MMm, west negative, e.g. 55.18 = 55 deg 18 min E\n',
         '            LON   DDD.MMm, west negative, e.g. 55.18 = 55 deg 18 min E\n' + PROMPTS),
        ('          LT = UT + TZ. Your time zone first: e.g. 3 STO "TZ" (UTC+3), -5 STO "TZ" (UTC-5), 5.5 for\n'
         '          UTC+5:30. The header shows UT or LT;',
         '          LT = UT + TZ (the TZ of the first prompt). The header shows UT or LT;'),
        ('  Named variables and matrices are not touched (DATE, UTC, LAT, LON, the matrices).',
         '  Named variables and matrices are not touched (TZ, DATE, UTC, LAT, LON, the matrices).'),
        ('WHAT IS NEW IN v2.3.0 "Local Time":',
         'WHAT IS NEW IN v2.4.0 "Here and Now": ALMA47 asks TZ first, then offers the clock\'s date and time\n'
         '  (as UT) and your last position: R/S five times = the sky now. Before any position is stored it\n'
         '  starts at Medellin, Colombia (6 13.9 N, 75 35.4 W). The same on the old DM42 and Free42 builds.\n\n'
         'WHAT WAS NEW IN v2.3.0 "Local Time":')), 'QUICKSTART')
    return q.rstrip('\n').split('\n')


def dm42():
    d = os.path.join(V.NX.OUT, 'dm42')
    write(os.path.join(DM42, 'NAVLITTLE.txt'), lines(os.path.join(d, 'ALMA47.txt')))
    write(os.path.join(DM42, 'MOON47.txt'), lines(os.path.join(d, 'MOON47.txt')))
    readme = open(os.path.join(PREV, 'dm42', 'README_DM42.txt'), encoding='utf-8').read()
    readme = replace(readme, (('ALMANAC 47 v2.3.0 "Local Time" LITTLE', 'ALMANAC 47 v2.4.0 "Here and Now" LITTLE'),),
                     'README_DM42')
    readme = note(readme, 'v2.4.0: ALMA47 (NAVLITTLE) asks TZ first (the hours of your clock from UT, west -, R/S keeps\n'
                          'the last one), then offers the clock\'s date and time as UT and your last LAT / LON (Medellin,\n'
                          '6 13.9 N 75 35.4 W, until you give yours): R/S five times = the sky now.')
    open(os.path.join(DM42, 'README_DM42.txt'), 'w', encoding='utf-8').write(readme)


def free42():
    import shutil
    V.NF.main()                                                     # build/dev/next/free42/: the .txt and the .raw
    for name in ('NAVFULL', 'NAVLITTLE', 'MOON47'):
        for ext in ('.txt', '.raw'):
            src = os.path.join(V.NF.OUT, name + ext)
            if os.path.exists(src):
                os.makedirs(F42, exist_ok=True)
                shutil.copyfile(src, os.path.join(F42, name + ext))
    readme = open(os.path.join(PREV, 'free42', 'README_F42.txt'), encoding='utf-8').read()
    readme = readme.replace('v2.3.0 "Local Time"', 'v2.4.0 "Here and Now"', 1)
    readme = note(readme, 'v2.4.0: NAV (NAVFULL and NAVLITTLE) asks TZ first (the hours of your clock from UT, west -,\n'
                          'R/S keeps the last one), then offers the clock\'s date and time as UT (TIME - TZ, the date moved\n'
                          'a day by DATE+ when UT is on another day; given as Y.MMDD whatever your date format) and your\n'
                          'last LAT / LON (Medellin, 6 13.9 N 75 35.4 W, until you give yours): R/S five times = now.')
    open(os.path.join(F42, 'README_F42.txt'), 'w', encoding='utf-8').write(readme)


def r47():
    """The R47 keyboard build of build/v2.4.0/c47/ (the arrows one row lower), as v2.3.0's."""
    alma = R4.r47(lines(os.path.join(C47, 'ALMA47.txt')))
    write(os.path.join(R47, 'ALMA47.txt'), alma)
    src = R4.r47(lines(os.path.join(C47, 'p47u', 'ALMA47.p47u')))
    src = [l.replace('@ Tested:  C47 simulator', '@ Tested:  R47 keyboard (up 61, down 71); C47 simulator', 1)
           if l.startswith('@ Tested:  C47 simulator') else l for l in src]
    write(os.path.join(R47, 'p47u', 'ALMA47.p47u'), src)
    assert [R4.step(l) for l in src if l.strip() and not l.startswith('@')] == alma, 'p47u = the listing'
    readme = R4.README.replace('v2.3.0 "Local Time"', 'v2.4.0 "Here and Now"').replace('_v2.3.0.zip', '_v2.4.0.zip')
    readme = readme.replace('=============================================',
                            '===============================================')
    open(os.path.join(R47, 'README_R47.txt'), 'w', encoding='utf-8').write(readme)
    q = open(os.path.join(C47, 'QUICKSTART.txt'), encoding='utf-8').read()
    head = ('Almanac 47 v2.4.0 "Here and Now" - QUICK START (C47 / R47; the DM42n with the C47 firmware)\n'
            '===========================================================================================\n')
    assert q.count(head) == 1, 'the title of c47/QUICKSTART.txt'
    q = q.replace(head, 'Almanac 47 v2.4.0 "Here and Now" - QUICK START, R47 KEYBOARD\n'
                        '=============================================================\n\n'
                        'THIS FOLDER: ALMA47 with the up / down arrows of the R47 keyboard (README_R47.txt). For the C47 and\n'
                        'the DM42n with the C47 firmware: Almanac47_C47_R47_v2.4.0.zip.\n')
    write(os.path.join(R47, 'QUICKSTART.txt'), q.rstrip('\n').split('\n'))
    print('  build/v2.4.0/r47/ALMA47.txt: %d steps, %d changed from the C47 one'
          % (len(alma), sum(a != b for a, b in zip(alma, lines(os.path.join(C47, 'ALMA47.txt'))))))


def r47_zip():
    j, c0, forum = os.path.join, os.path.join(ROOT, 'build', 'c47'), os.path.join(ROOT, 'build', 'forum')
    entries = ([(j(R47, n), n) for n in ('ALMA47.p47', 'ALMA47.txt', 'README_R47.txt', 'QUICKSTART.txt')] +
               [(j(C47, n), n) for n in ('ALMA47_LABELS.txt', 'MOON47.p47', 'MOON47.txt')] +
               [(j(c0, n), n) for n in ('NAVINIT_FAST.p47', 'NAVINIT_FAST.txt', 'NAVINIT_FULL.p47', 'NAVINIT_FULL.txt')] +
               [(j(R47, 'p47u', 'ALMA47.p47u'), 'p47u/ALMA47.p47u'), (j(C47, 'p47u', 'MOON47.p47u'), 'p47u/MOON47.p47u')] +
               [(j(forum, n), 'p47u/' + n) for n in ('NAVINIT.p47u', 'NAVINIT_FULL.p47u')] +
               [(j(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md', NOTES)] +
               [(V.MANUAL, os.path.basename(V.MANUAL))])
    z_ = j(OUT, 'Almanac47_R47_v%s.zip' % VERSION)
    with zipfile.ZipFile(z_, 'w', zipfile.ZIP_DEFLATED) as z:
        for s, n in entries:
            z.write(s, 'Almanac47_R47/' + n)
    print('  %s: %d files' % (os.path.relpath(z_, ROOT), len(entries)))


def main():
    import shutil
    V.c47()
    write(os.path.join(C47, 'QUICKSTART.txt'), quickstart())
    dm42()
    free42()
    r47()
    rejig = shutil.which('rejig')
    for d, names, validate in ((C47, ('ALMA47', 'MOON47'), True), (R47, ('ALMA47',), True),
                               (os.path.join(ROOT, 'build', 'c47'), ('NAVINIT_FAST', 'NAVINIT_FULL'), True),
                               (DM42, ('NAVLITTLE', 'MOON47'), False), (V.R.DM42, ('NAVINIT_LITTLE',), False)):
        for name in names:
            path = os.path.join(d, name + '.txt')
            size = V.p47(path, validate) if rejig else None
            print('  %s: %d steps; .p47 %s' % (os.path.relpath(path, ROOT), len(lines(path)),
                                               '%d bytes' % size if size else '? (no rejig)'))
    for name in ('NAVFULL', 'NAVLITTLE', 'MOON47'):
        path = os.path.join(F42, name + '.txt')
        raw = path[:-4] + '.raw'
        print('  %s: %d lines; .raw %s' % (os.path.relpath(path, ROOT), len(lines(path)),
                                          '%d bytes' % os.path.getsize(raw) if os.path.exists(raw) else '?'))
    if not rejig or not os.path.exists(V.MANUAL) or not os.path.exists(V.MANUAL_F42) or not os.path.exists(
            os.path.join(ROOT, NOTES)):
        print('  no zips: rejig, the manuals (tools/generators/build_manual.py, build_port_manuals.py) and %s first' % NOTES)
        return
    V.zips()
    r47_zip()


if __name__ == '__main__':
    main()
