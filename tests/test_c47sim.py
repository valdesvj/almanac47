#!/usr/bin/env python3
"""test_c47sim.py - python/c47sim.py: R-CLR, the local flags and LASTx as the C47 firmware does them.

  1. R-CLR (registers.c fnRegClr / getRegParam): X = sss.nn clears nn registers from sss, nn = 0 to the end of the
     range (R99), sss + nn below 100 (0.99 is R00-R98, 1.99 an error); the lettered range (104.04 A-D, 108.01 L) and
     the local registers (112.02 R.00-R.01); X stays; a negative X, |X| >= 1000 or a text an error
  2. the local flags .00-.31 (SF CF FS? FC? FS?C FC?C .nn, also written F.nn): in the subroutine level of the LocR,
     clear at its first LocR, kept by a second LocR, gone at its RTN; a level XEQ'd from it has none of its own until
     its LocR; without LocR an error (the firmware ignores them); the global flag of the same number untouched
  3. LASTx: LASTx (and LASTX) pushes the last X; RCL L, STO L read and write it as register L
  4. STOS / RCLS (fnStoreStack / fnRecallStack): the stack to the registers n .. n+7 (8 levels, the C47's default)
     and back, global or local (R.nn); too few registers an error; LASTx not touched

  python3 tests/test_c47sim.py
"""
import os, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python')]
import c47sim                                                        # noqa: E402

BAD = []


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def run(prog, x=0, regs=None):
    c = c47sim.Calc('\n'.join(['LBL "T"'] + prog + ['RTN', 'END']))
    c.s = [D(x), D(0), D(0), D(0)]
    for k, v in (regs or {}).items():
        c.rset(k, D(v))
    c.run('T', maxsteps=10 ** 4)
    return c


def fails(prog, x=0, regs=None):
    try:
        run(prog, x, regs)
    except ValueError:
        return True
    return False


def regclr():
    print('== R-CLR')
    R = {'%02d' % r: r + 1 for r in range(100)}
    c = run(['R-CLR'], '7.92', R)
    ok([r for r in range(100) if c.rget('%02d' % r) == 0] == list(range(7, 99)) and c.rget('99') == 100,
       '7.92: R07-R98 cleared, R00-R06 and R99 kept')
    ok(c.s[0] == D('7.92'), 'X stays as it is')
    c = run(['R-CLR'], '7', R)
    ok([r for r in range(100) if c.rget('%02d' % r) == 0] == list(range(7, 100)), '7.00: nn = 0, R07 to the end (R99)')
    c = run(['R-CLR'], '0.99', R)
    ok(c.rget('98') == 0 and c.rget('99') == 100, '0.99: R00-R98 (sss + nn = 99)')
    ok(fails(['R-CLR'], '1.99', R) and fails(['R-CLR'], '-7.92', R) and fails(['R-CLR'], '1000', R),
       '1.99 (sss + nn = 100), -7.92, 1000: out of range')
    ok(fails(['"AB"', 'R-CLR']), 'a text in X: an error')
    c = run(['STO L', 'R↓', 'STO A', 'STO D', '104.04', 'R-CLR'], '5', {'C': 3, '99': 1})
    ok(c.rget('A') == 0 and c.rget('C') == 0 and c.rget('D') == 0 and c.rget('L') == 5 and c.rget('99') == 1,
       '104.04: A B C D cleared, L and R99 kept')
    c = run(['STO L', '108.01', 'R-CLR'], '5')
    ok(c.lastx == 0, '108.01: L (LASTx) cleared')
    c = run(['LocR 03', '1', 'STO R.00', 'STO R.01', 'STO R.02', '112.02', 'R-CLR', 'RCL R.00', 'RCL R.01', 'RCL R.02'])
    ok(c.s[:3] == [1, 0, 0], '112.02: R.00 R.01 cleared, R.02 kept')
    ok(fails(['LocR 02', '112.03', 'R-CLR']) and fails(['112.01', 'R-CLR']), '112.03 with 2 local registers, 112.01 without LocR: errors')


def localflags():
    print('== local flags')
    c = run(['LocR 00', 'SF .03', '1', 'FS? .03', '2', 'FC? .03', '3', 'FS? F.03', '4'])
    ok(c.s[:3] == [4, 2, 1], 'LocR 00 gives the flags: SF .03, FS? .03 true, FC? .03 false; F.03 the same flag')
    c = run(['LocR 00', 'SF 03', 'FS? .03', '1', 'SF .04', 'FS? 04', '2', '5'])
    ok(c.s[0] == 5 and 1 not in c.s and 2 not in c.s, 'flag 03 and .03 are not the same, nor .04 and 04')
    c = run(['LocR 00', 'SF .00', 'SF .31', 'CF .00', 'FC? .00', '1', 'FS? .31', '2'])
    ok(c.s[:2] == [2, 1], 'CF .00; .31 the last one')
    ok(fails(['LocR 00', 'SF .32']), 'SF .32: an error (32 local flags)')
    c = run(['LocR 00', 'SF .05', 'FS?C .05', '1', 'FS? .05', '2', 'FC?C .05', '3', 'FS?C .05', '4'])
    ok(c.s[:2] == [3, 1], 'FS?C: true and clears it; FC?C true; FS?C now false')
    c = run(['LocR 00', 'SF .01', 'LocR 02', 'FS? .01', '1'])
    ok(c.s[0] == 1, 'a second LocR on the level keeps the flags')
    ok(fails(['SF .01']) and fails(['FS? .01', '1']), 'without LocR on the level: an error (the firmware ignores them)')
    P = ['LBL "T"', 'LocR 00', 'SF .02', 'XEQ 01', 'FS? .02', 'GTO 03', '0', 'RTN', 'LBL 03', '9', 'RTN',
         'LBL 01', 'LocR 00', 'FS? .02', '1', 'SF .02', 'SF .07', 'XEQ 02', 'RTN',
         'LBL 02', 'LocR 00', 'FS? .07', '2', 'RTN', 'END']
    c = c47sim.Calc('\n'.join(P))
    c.run('T')
    ok(c.s[0] == 9 and 1 not in c.s[1:] and 2 not in c.s[1:], 'each XEQ level its own flags, clear at its LocR; the caller\'s back after RTN')
    P = ['LBL "T"', 'XEQ 01', 'XEQ 02', 'RTN', 'LBL 01', 'LocR 00', 'SF .06', 'RTN', 'LBL 02', 'LocR 00', 'FS? .06', '1', '2', 'RTN', 'END']
    c = c47sim.Calc('\n'.join(P))
    c.run('T')
    ok(c.s[0] == 2 and c.s[1] != 1, 'gone at RTN: the next level at the same depth starts clear')
    P = ['LBL "T"', 'LocR 00', 'XEQ 01', 'RTN', 'LBL 01', 'SF .01', 'RTN', 'END']
    c = c47sim.Calc('\n'.join(P))
    try:
        c.run('T')
        ok(False, 'a level without its LocR does not use its caller\'s flags')
    except ValueError:
        ok(True, 'a level without its LocR does not use its caller\'s flags')
    c = run(['LocR 00', 'SF 05', 'FS?C 05', '1', 'FS? 05', '2', 'CF 06', 'FC?C 06', '3'])
    ok(c.s[:2] == [3, 1], 'FS?C / FC?C on a global flag too')


def lastx():
    print('== LASTx')
    c = run(['2', '+', 'LASTx'], '3')
    ok(c.s[:2] == [2, 5], 'LASTx: X of the last operation pushed (3 + 2: 2 on 5)')
    c = run(['SQRT', 'LASTX'], '16')
    ok(c.s[:2] == [16, 4], 'LASTX (old spelling) the same')
    c = run(['SQRT', 'RCL L'], '16')
    ok(c.s[:2] == [16, 4], 'RCL L reads LASTx')
    c = run(['STO L', 'R↓', 'LASTx'], '7')
    ok(c.s[0] == 7 and c.lastx == 7, 'STO L writes LASTx')
    c = run(['SQRT', 'STO L', 'R↓'], '9')
    ok(c.lastx == 3 and c.s[0] == 0, 'STO L does not change the stack')


def stos():
    print('== STOS / RCLS')
    c = run(['4', '3', '2', '1', 'STOS 90', 'CLSTK', 'RCLS 90'])
    ok(c.s[:4] == [1, 2, 3, 4], 'STOS 90, CLSTK, RCLS 90: the stack back')
    ok(c.rget('90') == 1 and c.rget('93') == 4, 'X in R90, T in R93')
    c = run(['SQRT', 'LocR 09', '4', '3', '2', '1', 'STOS R.00', 'LASTx', 'STO R.08', 'CLSTK', 'RCL R.08',
             'STO L', 'RCLS R.00'], '9')
    ok(c.s[:4] == [1, 2, 3, 4] and c.lastx == 9, 'LocR 9, STOS R.00 and LASTx in R.08: the stack and LASTx back')
    c = run(['SQRT', 'STOS 90', 'CLSTK', 'RCLS 90'], '16')
    ok(c.lastx == 16, 'STOS / RCLS do not change LASTx')
    ok(fails(['LocR 08', 'STOS R.01']) and fails(['STOS R.00']), 'STOS R.01 with 8 local registers, without LocR: errors')
    ok(fails(['STOS 93']) and fails(['RCLS 93']) and not fails(['STOS 92']), 'STOS 93 an error (R93-R100), STOS 92 not')


def main():
    regclr()
    localflags()
    lastx()
    stos()
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED: %s' % (len(BAD), '; '.join(BAD))))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
