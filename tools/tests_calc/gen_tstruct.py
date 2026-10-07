#!/usr/bin/env python3
"""Write tools/tests_calc/TSTRUCT.txt: a C47 timing test for the "structure" claims (branch struct-speed-test).

The claims, from an outside analysis of Almanac 47 (Oct 2026):
  1. a global label is found faster than a local one (a symbol table);
  2. a local label is found by scanning the program from the current step, so a jump over many steps
     (or one that has to wrap past END) is slower than a jump to a label close by;
  3. a named variable (STO "V0" / RCL "V0") is much slower than a numbered or a local register.

TSTRUCT measures each one with TICKS around a loop of N passes (N = X when X > 0, else 3000). Every test runs
the same steps as its partner, so only the thing under test differs. Results in ticks (1/10 s), R21-R30:

  R21  per pass a near GTO forward and a near GTO back
  R22  the same two GTOs, each over FILL steps (forward, then back)
  R23  XEQ to a local label a few steps ahead
  R24  XEQ to a local label FILL steps ahead
  R25  XEQ to a global label (another program)
  R26  RCL 02, DROP        (numbered register)
  R27  RCL "TV0", DROP     (named variable)
  R28  RCL R.00, DROP      (local register)
  R29  STO 02              (numbered register)
  R30  STO "TV0"           (named variable)

Reading it: R22 = R21 and R24 = R23: the firmware finds a local label in a table and distance does not count
(claim 2 does not hold). R22 >> R21: it scans the steps, and keeping routines next to their callers pays.
R25 < R23: claim 1 holds. R27 against R26 / R28, R30 against R29: the price of a name (claim 3).

Run it with the real programs loaded (NAVFULL, after NAVINIT), so the label list and the variables are as large
as when NAV runs. Run it twice and take the second run (the first one may compile/scan).
The step counts never differ inside a pair, so a difference of a few ticks is noise (± 1 tick).
"""
import os

FILL = 1000                               # steps between a far jump and its label (never executed)
HERE = os.path.dirname(os.path.abspath(__file__))


def filler(n=FILL):
    return ['1'] * n                      # a number step: 1 or 2 bytes, never run


def timed(reg, body_label, body):
    """N passes of body, the time to R<reg>. body ends at the DSE/GTO back to body_label."""
    return ['RCL 03', 'STO 00', 'TICKS', 'STO 01', 'DROP', 'LBL %02d' % body_label] + body + \
           ['DSE 00', 'GTO %02d' % body_label, 'TICKS', 'RCL 01', '-', 'STO %02d' % reg, 'DROP']


def program():
    P = ['LBL "TSTRUCT"',
         'REM "Timing test, branch struct-speed-test. X = passes (X <= 0: 3000). Results in ticks R21-R30."',
         'REM "Load NAVFULL and run NAVINIT first. Run twice, keep the second results."',
         'LocR 1',
         'X>0?', 'GTO 90', 'CLX', '3000', 'LBL 90', 'STO 03', 'DROP',
         '0', 'STO 02', 'STO "TV0"', 'STO R.00', 'DROP']

    # R21: two near GTOs per pass
    P += ['RCL 03', 'STO 00', 'TICKS', 'STO 01', 'DROP',
          'LBL 11', 'DSE 00', 'GTO 51', 'GTO 61', 'LBL 51', 'GTO 11', 'LBL 61',
          'TICKS', 'RCL 01', '-', 'STO 21', 'DROP']

    # R22: the same, each GTO over FILL steps (forward to 52, back to 12)
    P += ['RCL 03', 'STO 00', 'TICKS', 'STO 01', 'DROP',
          'LBL 12', 'DSE 00', 'GTO 52', 'GTO 62'] + filler() + ['LBL 52', 'GTO 12', 'LBL 62',
          'TICKS', 'RCL 01', '-', 'STO 22', 'DROP']

    # R23: XEQ to a local label just after the loop (forward, a few steps)
    P += timed(23, 13, ['XEQ 43']) + ['GTO 63', 'LBL 43', 'RTN', 'LBL 63']
    # R24: XEQ to a local label FILL steps further on (LBL 44 at the end of the program, forward too)
    P += timed(24, 14, ['XEQ 44'])
    # R25: XEQ to a global label in another program
    P += timed(25, 15, ['XEQ "TSG"'])
    # R26-R28: RCL of a numbered register, a named variable, a local register
    P += timed(26, 16, ['RCL 02', 'DROP'])
    P += timed(27, 17, ['RCL "TV0"', 'DROP'])
    P += timed(28, 18, ['RCL R.00', 'DROP'])
    # R29-R30: STO
    P += timed(29, 19, ['STO 02'])
    P += timed(30, 20, ['STO "TV0"'])

    P += ['RCL 21', 'RTN'] + filler() + ['LBL 44', 'RTN', 'END',
          'LBL "TSG"', 'RTN', 'END']
    return P


def main():
    out = os.path.join(HERE, 'TSTRUCT.txt')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(program()) + '\n')
    print(out)


if __name__ == '__main__':
    main()
