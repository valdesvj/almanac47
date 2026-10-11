#!/usr/bin/env python3
"""build_release_c47.py - Almanac 47 v2.2.0 "Struct on Attack", the C47 / R47-only release (the STRUCT build).

From the STRUCT source (programs_struct/, tools/build_struct_src.py) and the forum files (tools/build_forum.py):

  build/c47/ALMA47.txt          the programs that stay on the calculator: NAV of the source, its label named ALMA47
  build/c47/NAVINIT_FAST.txt    builds the FAST matrices (2026-2030): build/NAVINIT_FAST.txt, INIT named NAVINIT
  build/c47/NAVINIT_FULL.txt    builds the FULL matrices (2000-2050): build/NAVINIT_FULL.txt, INIT named NAVINIT
  build/c47/MOON47.txt          the Moon phase on its own (one program)
  build/c47/ALMA47_LABELS.txt   the global labels of ALMA47, the ones you can call yourself, the numbers in R43-R98
  build/c47/*.p47               the .txt converted by rejig: steps only, the smallest file (not in git)
  build/forum/*.p47u            the rejig sources with the '@' header and the comments after ';'
  build/c47/NAVLITTLE.txt       the old DM42 (64 KiB) with the C47 firmware: from programs_struct/little/ (STRUCT)
  build/c47/NAVINIT_LITTLE.txt  its matrices (build/dm42/NAVINIT_LITTLE.txt, INIT named NAVINIT)
  build/Almanac47_C47_R47_v2.2.0.zip   the release zip (not in git), with the manual of build/manuals/
  build/Almanac47_DM42_C47firmware_v2.2.0.zip   NAVLITTLE, its NAVINIT, MOON47 v2.1.0, build/c47/dm42/README_DM42.txt

The almanac tables (TBL) are not in this release. Free42 / DM42 stay on v2.1.0 (build/, build/free42/): Free42 has no
STRUCT. Build the manual first (python3 tools/generators/build_manual.py -> build/manuals/C47_Nav_User_Manual.pdf).

  python3 tools/build_release_c47.py
"""
import os, re, shutil, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import build_struct_src as B                                                  # noqa: E402
import build_forum as F                                                       # noqa: E402

VERSION = '2.2.0'
NAME = 'Struct on Attack'
OUT = os.path.join(ROOT, 'build', 'c47')
ZIP = os.path.join(ROOT, 'build', 'Almanac47_C47_R47_v%s.zip' % VERSION)
ZIP_DM42 = os.path.join(ROOT, 'build', 'Almanac47_DM42_C47firmware_v%s.zip' % VERSION)
FOLDER = 'Almanac47_C47'                       # the folder inside the zip (as in v2.1.0)
MANUAL = os.path.join(ROOT, 'build', 'manuals', 'C47_Nav_User_Manual.pdf')
MAIN = 'ALMA47'

# the routines of ALMA47 you can call yourself (after ALMA47 has run and was left with EXIT or R/S, not with 0:
# they read the numbers ALMA47 stores in R43-R98 at its start, the DR of the run and the matrices of NAVINIT)
CALLABLE = [
    ('N15', 'SUNA', 'X = JD (UT)', 'X GHA of the Sun, Y Dec, Z GHA of Aries'),
    ('N17', 'SUNF', 'X = JD (UT)', 'X GHA of the Sun, Y Dec (low precision, 0.01 deg)'),
    ('N25', 'MOO2', 'right after N15, same JD', "X GHA of the Moon, Y Dec, Z HP ('), T SD (')"),
    ('N28', 'PLN2', 'right after N15; X = planet 1-4 (Venus, Mars, Jupiter, Saturn)', "X GHA, Y Dec, Z SHA, T HP (')"),
    ('N29', 'PLN3', 'right after N15; X = planet 1-4', 'X GHA, Y Dec (a quick position, the full series only when the planet '
     'can be above the horizon)'),
    ('N32', 'HCZ', 'Y = Dec, X = GHA (decimal degrees)', 'X Hc, Y Zn for the DR of the last run'),
    ('N38', 'RISE', 'Z = JD at 0 h UT, Y = lat, X = lon (decimal degrees, N and E +)', 'X sunrise (UT hours; 99 = none that day)'),
    ('N39', 'SET', 'Z = JD at 0 h UT, Y = lat, X = lon (decimal degrees, N and E +)', 'X sunset (UT hours; 99 = none)'),
    ('N44', 'TRAN', 'Z = JD at 0 h UT, Y = lat, X = lon (decimal degrees, N and E +)', 'X meridian passage of the Sun (UT hours)'),
    ('N40', 'NTWA', 'Z = JD at 0 h UT, Y = lat, X = lon (decimal degrees, N and E +)', 'X nautical twilight, morning (UT hours; 99 = none)'),
    ('N41', 'NTWP', 'Z = JD at 0 h UT, Y = lat, X = lon (decimal degrees, N and E +)', 'X nautical twilight, evening (UT hours; 99 = none)'),
    ('N48', 'SNMU', 'X = star number 1-58', 'the star\'s name in ALPHA'),
]


def lines(path):
    return [l for l in open(path, encoding='utf-8').read().split('\n') if l.strip()]


def write(name, L):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')


def numbers(L):
    """The numbers NAV stores in R43-R98 at its start: {register: number}."""
    out = {}
    for i in range(1, 140):
        m = re.fullmatch(r'STO (\d\d)', L[i])
        if m and int(m.group(1)) >= 43 and m.group(1) not in out:
            out[m.group(1)] = L[i - 1]
    return out


def labels_file(L):
    """ALMA47_LABELS.txt: what each global label of ALMA47 does; the ones you can call; the numbers in R43-R98."""
    glob = [l[5:-1] for l in L if l.startswith('LBL "')]
    w = max(len(B.LABELS[g][0]) for g in glob if g != 'NAV')
    out = ['ALMA47 v%s "%s" (C47 / R47) - the program labels' % (VERSION, NAME),
           '=' * 64,
           'ALMA47 is 26 programs; only ALMA47 has a name, the others start with a numbered global label N01, N02 ...',
           '(the names do not clash with yours). The numbers are the ones of earlier versions: a missing number',
           'belongs to a routine that is gone. Inside each program the routines are local labels 01, 02 ... (the',
           'comments of ALMA47.p47u say what each one does).',
           '',
           'Routines you can call yourself',
           '------------------------------',
           'Run ALMA47 with your date, time and DR, then leave it with EXIT (or R/S), NOT with 0: 0 clears the',
           'registers (CLREGS), and these routines read the numbers ALMA47 stores in R43-R98 at its start (the table',
           'at the end), the DR of the run (R13 longitude, R14 latitude) and the matrices of NAVINIT. They use',
           'R00-R42 for their work. JD: the C47\'s Julian Date (DATE, then ⅅ→J) + UT / 24, a plain number.',
           '']
    for lab, name, inp, outp in CALLABLE:
        out.append('  XEQ "%s"  %-5s %s' % (lab, name, inp))
        out.append('  %s-> %s' % (' ' * 18, outp))
    out += ['', 'Example: run ALMA47 for 23 Sep 2026, 25 20 N 055 12 E, leave with EXIT;',
            '  2461307 XEQ "N15" -> X 1.9070 (GHA of the Sun), Y -0.1932 (Dec), Z 182.3525 (GHA of Aries)',
            '  then XEQ "N25" -> the Moon; 2461306.5 ENTER 25.333 ENTER 55.2 XEQ "N38" -> 2.13 (sunrise 02:08 UT)',
            '', 'Every global label', '------------------',
            'Label    Name%s  What it does' % (' ' * (w - 4))]
    for g in glob:
        n, what = B.LABELS[g]
        if g == 'NAV':
            out.append('ALMA47   %-*s  %s' % (w, 'NAV', what.replace('the only named program', 'the only named program '
                                                                        '(NAV in the sources)')))
        else:
            out.append('%-8s %-*s  %s' % (g, w, n, what))
    num = numbers(L)
    out += ['', 'The numbers ALMA47 stores in R43-R98 when it starts (each use is a 2-byte RCL)',
            '-' * 78]
    cells = ['R%s %-16s' % (r, v) for r, v in sorted(num.items())]
    for i in range(0, len(cells), 4):
        out.append('  ' + '  '.join(cells[i:i + 4]).rstrip())
    return out


def p47(name):
    """build/c47/NAME.p47 from the plain listing build/c47/NAME.txt (no comment of any kind, so nothing but the
    steps reaches the calculator) with rejig, validated for the R47; the program size in bytes. The same file as
    rejig makes from the commented .p47u (its ';' comments are dropped): checked."""
    src, dst = os.path.join(OUT, name + '.txt'), os.path.join(OUT, name + '.p47')
    subprocess.run(['rejig', '--validate=r47', '-o', dst, src], check=True)
    L = open(dst, encoding='ascii').read().split('\n')
    forum = os.path.join(F.OUT, {'NAVINIT_FAST': 'NAVINIT'}.get(name, name) + '.p47u')
    if os.path.exists(forum) and 'LITTLE' not in name:
        tmp = dst[:-4] + '_from_p47u.p47'
        subprocess.run(['rejig', '-o', tmp, forum], check=True)
        same = open(tmp, encoding='ascii').read() == '\n'.join(L)
        os.remove(tmp)
        assert same, '%s: the .p47u gives another .p47' % name
    assert not any(l.strip().startswith(('REM', '#', ';')) for l in lines(src)), name
    return int(L[L.index('PROGRAM') + 1])


# ---- NAVLITTLE: the old DM42 (64 KiB) with the C47 firmware, in STRUCT
DM42_MAX = 10                     # the DM42 build of the firmware: partner numbers 1-10 a series, 10 open at once


def little():
    """NAVLITTLE in STRUCT from its source programs_struct/little/NAVLITTLE.txt (made once from v2.1.0's
    build/dm42/NAVLITTLE.txt by tools/build_little_struct.py): numbered, every program VALID and within the DM42 limits,
    no GTO. INIT of build/dm42/NAVINIT_LITTLE.txt named NAVINIT. -> (ALMA47 lines, NAVINIT lines)"""
    import c47struct as C
    I = lines(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'))
    S = C.number(C.plain(lines(os.path.join(ROOT, 'programs_struct', 'little', 'NAVLITTLE.txt'))))
    assert S[0] == 'LBL "%s"' % MAIN and S.count('"NAVINIT"') == 1
    faults = []
    for P in C.split(S):
        Q = C.plain(P)
        faults += ['%s: %s' % (P[0], f) for f in C.check(Q)]
        faults += ['%s: %s' % (P[0], l) for l in Q if l.startswith('GTO')]
        for o in C.OPENERS:
            if sum(l == o for l in Q) > DM42_MAX:
                faults.append('%s: %d %s (the DM42 takes %d)' % (P[0], sum(l == o for l in Q), o, DM42_MAX))
        d = top = 0
        for l in Q:
            d += C.op(l) in C.OPENERS
            d -= C.op(l) in ('ENDIF', 'ENDDO', 'UNTIL')
            top = max(top, d)
        if top > DM42_MAX:
            faults.append('%s: %d structures open at once' % (P[0], top))
    if faults:
        raise SystemExit('build_release_c47 NAVLITTLE:\n  ' + '\n  '.join(faults))
    assert I[0] == 'LBL "INIT"' and not any('"INIT"' in l for l in I[1:])
    return S, ['LBL "NAVINIT"'] + I[1:]


def main():
    os.makedirs(OUT, exist_ok=True)
    F.main()                                                    # build/forum/*.p47u
    L = B.build()
    assert L[0] == 'LBL "NAV"'
    write('ALMA47.txt', ['LBL "ALMA47"'] + L[1:])
    for kind in ('FAST', 'FULL'):
        I = lines(os.path.join(ROOT, 'build', 'NAVINIT_%s.txt' % kind))
        write('NAVINIT_%s.txt' % kind, ['LBL "NAVINIT"'] + I[1:])
    write('MOON47.txt', B.build_moon())
    write('ALMA47_LABELS.txt', labels_file(L))
    S, I = little()
    write('NAVLITTLE.txt', S)
    write('NAVINIT_LITTLE.txt', I)
    have_rejig = shutil.which('rejig')
    for name in ('ALMA47', 'NAVINIT_FAST', 'NAVINIT_FULL', 'MOON47', 'NAVLITTLE', 'NAVINIT_LITTLE'):
        size = p47(name) if have_rejig else None
        print('  build/c47/%s.txt: %d steps; .p47 %s bytes' % (name, len(lines(os.path.join(OUT, name + '.txt'))),
                                                               size or '? (no rejig)'))
    if not have_rejig or not os.path.exists(MANUAL):
        print('  no zip: %s' % ('rejig missing' if not have_rejig else 'build the manual first (tools/generators/build_manual.py)'))
        return
    files = [(os.path.join(OUT, n), n) for n in ('ALMA47.p47', 'ALMA47.txt', 'ALMA47_LABELS.txt', 'NAVINIT_FAST.p47',
                                                 'NAVINIT_FAST.txt', 'NAVINIT_FULL.p47', 'NAVINIT_FULL.txt',
                                                 'MOON47.p47', 'MOON47.txt', 'QUICKSTART.txt')]
    files += [(os.path.join(F.OUT, n), 'p47u/' + n) for n in ('ALMA47.p47u', 'NAVINIT.p47u', 'NAVINIT_FULL.p47u',
                                                             'MOON47.p47u')]
    files += [(MANUAL, 'C47_Nav_User_Manual.pdf'), (os.path.join(ROOT, 'docs', 'OPTIMIZATIONS.md'), 'OPTIMIZATIONS.md')]
    files += [(os.path.join(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md')]
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            z.write(src, '%s/%s' % (FOLDER, arc))
    print('  %s: %d files' % (os.path.relpath(ZIP, ROOT), len(files)))
    dm = [(os.path.join(OUT, n), n) for n in ('NAVLITTLE.p47', 'NAVLITTLE.txt', 'NAVINIT_LITTLE.p47', 'NAVINIT_LITTLE.txt')]
    moon = os.path.join(tempfile.mkdtemp(), 'MOON47')          # v2.1.0's (no STRUCT: the DM42 limits)
    shutil.copy(os.path.join(ROOT, 'build', 'dm42', 'MOON47.txt'), moon + '.txt')
    subprocess.run(['rejig', '--validate=r47', '-o', moon + '.p47', moon + '.txt'], check=True)
    dm += [(moon + '.p47', 'MOON47.p47'), (moon + '.txt', 'MOON47.txt')]
    dm += [(os.path.join(OUT, 'dm42', 'README_DM42.txt'), 'README_DM42.txt'), (MANUAL, 'C47_Nav_User_Manual.pdf')]
    dm += [(os.path.join(ROOT, n), n) for n in ('LICENSE', 'NOTICE', 'AI_ASSISTANCE.md')]
    with zipfile.ZipFile(ZIP_DM42, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in dm:
            z.write(src, 'Almanac47_DM42_C47/%s' % arc)
    print('  %s: %d files' % (os.path.relpath(ZIP_DM42, ROOT), len(dm)))


if __name__ == '__main__':
    main()
