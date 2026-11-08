#!/usr/bin/env python3
"""build_next_f42.py - the next version for Free42 (DM42 / DM42n with the stock firmware, Free42 / Plus42): NAVFULL,
NAVLITTLE and MOON47 of v2.2.1 (build/free42/ with your stack kept, build_release_v221.f42_stack) and the UT / LT
switch of the next version (ALMA47, MOON47 of programs_struct/next/):

  +/-   every time shown in UT or in local time, LT = UT + the variable TZ; the switch is the variable TZLT (0 UT,
        1 LT), kept between runs. NAV makes TZ and TZLT 0 when they are missing. In LT the header shows the date and
        the time + TZ and LT for UT; rise, set, twilights and meridian passage + TZ (mod 24 h).
        NAVFULL: +/- on the menu redraws it, on a view (or INFO) redraws the view. NAVLITTLE: +/- redraws ALMANAC.

  The patch, on the v2.1.0 listings (short labels, build/free42/*_LABELS.txt):
  KM     the Free42 key +/- (15) gives the C47 code 43
  WPLS   returns on 43 too (as on +, the arrows); NAVFULL's SKY (its own KEY? loop, KQ) too
  NAV    0 into TZ / TZLT when they are missing (flag 25), LBL 87: flag 93 set in LT, LTH = the shift in hours (TZ in
         LT, else 0), LTD = in days; LBL 86 switches TZLT, then LBL 87; on 43 the menu (LBL 84) or the view (LBL 83)
         again. LTH, LTD and flag 93 go at the end.
  PHMS   adds LTH (mod 24) to every time that is not 99 (no event)
  header PDTS gets the date + LTD; FC? 93 "UT", FS? 93 "LT"

  build/dev/next/free42/NAVFULL.txt, NAVLITTLE.txt, MOON47.txt (+ .raw with tools/f42/f42run)

  python3 tools/build_next_f42.py
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import build_release_v221 as R                                               # noqa: E402

SRC = os.path.join(ROOT, 'build', 'free42')
OUT = os.path.join(ROOT, 'build', 'dev', 'next', 'free42')
LTFLAG = 93


def labels(name):
    """long name -> label on the calculator, from build/free42/<name>_LABELS.txt"""
    m = {}
    for l in open(os.path.join(SRC, name + '_LABELS.txt'), encoding='utf-8'):
        p = l.split()
        if len(p) >= 2 and re.fullmatch(r'N\d\d', p[0]):
            m[p[1]] = p[0]
    return m


class Patch:
    def __init__(self, L):
        self.s = '\n' + '\n'.join(L) + '\n'

    def sub(self, a, b, n=1, after=None):
        a = '\n' + '\n'.join(a) + '\n'
        b = '\n' + '\n'.join(b) + '\n'
        start = 0 if after is None else self.s.index('\n' + after + '\n')
        head, tail = self.s[:start], self.s[start:]
        c = tail.count(a)
        if c != n:
            raise SystemExit('build_next_f42: %d x %r (%d expected)' % (c, a, n))
        self.s = head + tail.replace(a, b)

    def lines(self):
        return self.s.strip('\n').split('\n')


def common(P, m, key_reg):
    """KM, WPLS, PHMS and NAV's start / end / LBL 83-87 (both builds)."""
    km, wp, phms = m['KM'], m['WPLS'], m['PHMS']
    k = re.search(r'\nLBL "%s"\nFUNC 11\nSTO ("\w+")\n' % km, P.s)       # its variable (KK, renamed in some builds)
    v = k.group(1)
    P.s = P.s[:k.end()] + 'RCL %s\n15\nX=Y?\nGTO 16\n' % v + P.s[k.end():]
    e = P.s.index('\nLBL 15\n', k.end())
    e = P.s.index('\nRTN\n', e) + 5
    assert '\nLBL 16\n' not in P.s[k.start():P.s.index('\nEND\n', k.end())]
    P.s = P.s[:e] + 'LBL 16\n43\nRTN\n' + P.s[e:]
    w = re.search(r'\nLBL "%s"\n(?:XEQ "\w+"\n)?LBL 01\nGETKEY\nXEQ "%s"\nSTO (\d+)\n' % (wp, km), P.s).group(1)
    P.sub(['RCL ' + w, '61', 'X=Y?', 'RTN'], ['RCL ' + w, '61', 'X=Y?', 'RTN', 'RCL ' + w, '43', 'X=Y?', 'RTN'],
          after='LBL "%s"' % wp)
    mt = re.search(r'\nLBL "%s"\nXEQ 05\nRCL (\d+)\n98\nX<Y\?\nGTO 07\n' % phms, P.s)
    r = mt.group(1)
    P.s = P.s[:mt.end()] + '\n'.join(['RCL ' + r, 'RCL+ "LTH"', '24', 'MOD', 'STO ' + r]) + '\n' + P.s[mt.end():]
    size = re.search(r'\nLBL "NAV"\n(?:.*\n)*?(SIZE \d+)\n', P.s).group(1)       # NAVFULL SIZE 100, NAVLITTLE SIZE 38
    P.sub([size], [size, '0', 'SF 25', 'RCL "TZ"', 'CF 25', 'STO "TZ"', 'CLX', 'SF 25', 'RCL "TZLT"', 'CF 25',
                         'STO "TZLT"', 'XEQ 87'], after='LBL "NAV"')
    nav = P.s[P.s.index('\nLBL "NAV"\n'):]
    nav = nav[:nav.index('\nEND\n')]
    for k in (83, 84, 86, 87):
        assert '\nLBL %d\n' % k not in nav, k
    return w


def sub_routines(view):
    return ['LBL 84', 'XEQ 86', 'GTO 01', 'LBL 83', 'XEQ 86', 'GTO %s' % view,
            'LBL 86', '1', 'RCL "TZLT"', '-', 'STO "TZLT"',
            'LBL 87', 'CF %d' % LTFLAG, 'RCL "TZLT"', 'X≠0?', 'SF %d' % LTFLAG, 'RCL "TZ"', 'FC? %d' % LTFLAG, 'CLX',
            'STO "LTH"', '24', '÷', 'STO "LTD"', 'RTN']


def header(P, date_steps, pdts):
    P.sub(date_steps + ['XEQ "%s"' % pdts], date_steps + ['RCL+ "LTD"', 'XEQ "%s"' % pdts])
    P.sub(['XSTR "UT"'], ['FC? %d' % LTFLAG, 'XSTR "UT"', 'FS? %d' % LTFLAG, 'XSTR "LT"'])


def navfull(L):
    m = labels('NAVFULL')
    P = Patch(L)
    common(P, m, None)
    key = re.search(r'\nLBL 02\nGETKEY\nXEQ "%s"\nSTO (\d+)\n' % m['KM'], P.s).group(1)
    P.sub(['LBL 02', 'GETKEY', 'XEQ "%s"' % m['KM'], 'STO ' + key],
          ['LBL 02', 'GETKEY', 'XEQ "%s"' % m['KM'], 'STO ' + key, 'RCL ' + key, '43', 'X=Y?', 'GTO 84'])
    P.sub(['LBL 05', 'RCL ' + key, '51'], ['LBL 05', 'RCL ' + key, '43', 'X=Y?', 'GTO 83', 'RCL ' + key, '51'])
    P.sub(['CLV "Q3"'], ['CLV "Q3"', 'CLV "LTH"', 'CLV "LTD"', 'CF %d' % LTFLAG])
    P.sub(['LBL 22', '1', 'STO+ "W6"'], sub_routines('03') + ['LBL 22', '1', 'STO+ "W6"'])
    P.sub(['XEQ "%s"' % m['KQ'], 'GTO 46', 'RCL ' + key, '85', 'X=Y?', 'RTN'],             # SKY: its own key loop
          ['XEQ "%s"' % m['KQ'], 'GTO 46', 'RCL ' + key, '85', 'X=Y?', 'RTN', 'RCL ' + key, '43', 'X=Y?', 'RTN'])
    header(P, ['RCL "H0"', '2', 'RCL "H1"'], m['PDTS'])
    return P.lines()


def navlittle(L):
    m = labels('NAVLITTLE')
    P = Patch(L)
    common(P, m, None)
    i = P.s.index('\nLBL "NAV"\n')
    a = '\nXEQ "%s"\nRCL 00\n51\nX=Y?\nGTO 06\n' % m['ALMF']
    assert P.s.count(a) == 1
    P.s = P.s.replace(a, '\nXEQ "%s"\nRCL 00\n43\nX=Y?\nGTO 83\nRCL 00\n51\nX=Y?\nGTO 06\n' % m['ALMF'])
    P.sub(['CLV "V3"'], ['CLV "V3"', 'CLV "LTH"', 'CLV "LTD"', 'CF %d' % LTFLAG])
    P.sub(['LBL 06', '1', 'STO+ "V7"'], sub_routines('01')[3:] + ['LBL 06', '1', 'STO+ "V7"'])
    d = re.search(r'\n(RCL \d+)\n2\n(RCL \d+)\nXEQ "%s"\n' % m['PDTS'], P.s[P.s.index('\nLBL "%s"\n' % m['ALMF']):])
    header(P, [d.group(1), '2', d.group(2)], m['PDTS'])
    return P.lines()


def write(name, L):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.txt')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    return path


def main():
    out = {}
    for name, fn in (('NAVFULL', navfull), ('NAVLITTLE', navlittle), ('MOON47', None)):
        L = R.lines(os.path.join(SRC, name + '.txt'))
        L = fn(L) if fn else L                    # MOON47: build/free42/ has the switch (tools/build_moon47.py)
        out[name] = R.f42_stack(L, 'MOON47' if name == 'MOON47' else 'NAV')
        path = write(name, out[name])
        print('  build/dev/next/free42/%s.txt: %d steps' % (name, len(out[name])))
        if os.path.exists(R.F42RUN):
            subprocess.run([R.F42RUN], input='paste %s\nexport %s\n' % (path, path[:-4] + '.raw'), text=True,
                           capture_output=True, timeout=600, check=True)
    return out


if __name__ == '__main__':
    main()
