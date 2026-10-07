#!/usr/bin/env python3
"""test_fw.py - the C47 release files in the C47 firmware itself: the PC simulator built from the firmware
sources (gitlab rpncalculators/c43), headless with its Tcl script (--script). No pixels here (a SNAP inside a
running program is not reliable headless): every run must end with no error and X = 0. NAVFULL and MOON47 clear
R00-R99 when they end (CLREGS): every register 0 after (set to marks before); NAVLITTLE keeps them.

  NAVFULL    NAVINIT_FAST, the four inputs (R/S at each prompt), then each page key (1-6), + menu, 0 end
  NAVLITTLE  NAVINIT_LITTLE, the inputs, up, down, + end
  MOON47     without TZ (TZ = 0 must be created) and with TZ = -5 (kept)
The key waits (PAUSE n / KEY? r / GTO) are replaced in a test copy by SNAP and the next key from the variable
TKEY, the same in every file.

  C47SIM=/path/to/c47 python3 tests/test_fw.py      (default ~/c47sim-patched/src47/build.sim/src/c47-gtk/c47;
                                                     the program reads res/ next to it: the source folder)
"""
import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools')]
import build_navopt as N                                             # noqa: E402

SIM = os.environ.get('C47SIM', os.path.expanduser('~/c47sim-patched/src47/build.sim/src/c47-gtk/c47'))
RES = os.path.join(os.path.dirname(SIM).split('/build.sim/')[0], 'res') if '/build.sim/' in SIM else os.path.join(os.path.dirname(SIM), 'res')
ERRORS = ('rror', 'ndefined', 'ut of range', 'nvalid', 'not found')


def testcopy(src, dst):
    L = [l for l in open(src, encoding='utf-8').read().split('\n') if l]
    out, i = [], 0
    while i < len(L):
        if re.fullmatch(r'PAUSE \d+', L[i]) and i + 2 < len(L) and L[i + 1].startswith('KEY? ') and L[i + 2].startswith('GTO '):
            out += ['SNAP', 'RCL "TKEY"', '100', 'MOD', 'STO ' + L[i + 1][5:], 'RCL "TKEY"', '100', '÷', 'IP', 'STO "TKEY"',
                    'DROP', 'DROP']
            i += 3
            continue
        out.append(L[i]); i += 1
    open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')


def run(files, label, keys, setup, init=True, resume=0, show=()):
    d = tempfile.mkdtemp()
    os.symlink(RES, os.path.join(d, 'res'))
    p47 = []
    for f in files:
        dst = os.path.join(d, os.path.basename(f))
        if 'NAVINIT' in f:
            shutil.copy(f, dst)
        else:
            testcopy(f, dst)
        N.p47(dst); p47.append(dst[:-4] + '.p47')
    code = 0
    for k in reversed(keys):
        code = code * 100 + k
    helper = os.path.join(d, 'TSET.txt')
    open(helper, 'w', encoding='utf-8').write('\n'.join(['LBL "TSET"'] + setup + [str(code), 'STO "TKEY"', 'CLSTK', 'RTN', 'END']) + '\n')
    N.p47(helper)
    tcl = ['readp %s' % f for f in p47 + [helper[:-4] + '.p47']] + (['xeq INIT'] if init else []) + ['xeq TSET']
    tcl += ['reg %02d %d.25' % (r, 4000 + r) for r in range(100)] + ['xeq %s' % label] + ['press R/S'] * resume
    tcl += ['puts "X=[reg X]"'] + ['puts "%s=[var %s]"' % (v, v) for v in show] + ['puts "R%02d=[reg %02d]"' % (r, r) for r in range(100)]
    open(os.path.join(d, 't.tcl'), 'w').write('\n'.join(tcl) + '\n')
    r = subprocess.run([SIM, '--headless', '--script', 't.tcl'], cwd=d, capture_output=True, text=True, timeout=1800)
    out = [l for l in (r.stdout + r.stderr).split('\n') if l.strip() and not l.lstrip().startswith('refrsh')]
    regs = {m.group(1): m.group(2) for l in out for m in [re.match(r'R(\d\d)=(.*)', l)] if m}
    vals = {m.group(1): m.group(2) for l in out for m in [re.match(r'(\w+)=(.*)', l)] if m}
    err = [l for l in out if any(w in l for w in ERRORS) and not l.startswith(('Exported', 'Overrode', 'Cleared'))]
    changed = [k for k, v in regs.items() if '.25' not in v]
    shutil.rmtree(d, ignore_errors=True)
    return vals, changed, err


def main():
    if not os.path.exists(SIM):
        print('no C47 simulator (%s): set C47SIM' % SIM)
        return 0
    B = os.path.join(ROOT, 'build')
    inputs = ['2026.1004', 'STO "DATE"', '9.30', 'STO "UTC"', '25.20', 'STO "LAT"', '55.12', 'STO "LON"']
    bad = 0
    print('== NAVFULL in the C47 firmware (headless PC simulator): each page, + menu, 0 end')
    for k, name in ((72, '1 ALMANAC'), (73, '2 SPLIT'), (74, '3 SKY'), (62, '4 ANIM'), (63, '5 ALLSKY'), (64, '6 INFO'), (54, '9 SNAP')):
        vals, changed, err = run([os.path.join(B, 'NAVINIT_FAST.txt'), os.path.join(B, 'NAVFULL.txt')], 'NAV', [k, 85, 82], inputs, resume=4)
        zero = all(vals.get('R%02d' % r) == '0' for r in range(100))          # CLREGS when NAV ends
        ok = not err and zero and vals.get('X') == '0'
        bad += not ok
        print('  %-10s X=%s  R00-R99 %s  %s' % (name, vals.get('X'), 'all 0' if zero else 'NOT 0', err[:2] or 'no error'))
    print('== NAVLITTLE (DM42 with the C47 firmware): up, down, + end')
    vals, changed, err = run([os.path.join(B, 'dm42', 'NAVINIT_LITTLE.txt'), os.path.join(B, 'dm42', 'NAVLITTLE.txt')], 'NAV', [51, 61, 85],
                             inputs, resume=4)
    ok = not err and not changed
    bad += not ok
    print('  NAVLITTLE  X=%s  registers %s  %s' % (vals.get('X'), 'kept' if not changed else 'CHANGED %d' % len(changed), err[:2] or 'no error'))
    print('== MOON47: without TZ, with TZ = -5')
    for tz, setup in (('none', []), ('-5', ['-5', 'STO "TZ"'])):
        vals, changed, err = run([os.path.join(B, 'MOON47.txt')], 'MOON47', [43, 82], setup, init=False, show=('TZ',))
        zero = all(vals.get('R%02d' % r) == '0' for r in range(100))          # CLREGS when MOON47 ends
        ok = not err and vals.get('TZ') == ('0' if tz == 'none' else '-5') and zero
        bad += not ok
        print('  TZ before %-4s -> TZ %s, R00-R99 %s  %s' % (tz, vals.get('TZ'), 'all 0' if zero else 'NOT 0', err[:2] or 'no error'))
    print('%d failed' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
