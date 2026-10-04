#!/usr/bin/env python3
"""keywait_patch.py - the key wait of the C47 programs read in a PAUSE (C47 / R47 / DM42 with the C47 firmware).

A bare KEY? loop (PAUSE 0 / LBL n / KEY? r / GTO n) lets the PC simulator draw the stack over the screen when a key
is released; the calculator does not. With the PAUSE inside the loop (LBL n / PAUSE 50 / KEY? r / GTO n) a key ends
the PAUSE only after its release, on both, and KEY? reads it: the same code works in the simulator and on the
calculator (tests/calc_keywait/README.txt). The timed SKY line (PAUSE 0 / TICKS / n / + / STO 38 / LBL 41 /
KEY? 39 / GTO 46, the next body at LBL 62) becomes PAUSE n / KEY? 39 / GTO 62 (the same n tenths per line).
The rest of the listing is not changed.

  python3 tools/keywait_patch.py FILE.txt [...]     -> FILE.txt rewritten in place; prints what changed
"""
import re
import sys


DEAD = ['LBL 46', 'TICKS', 'RCL 38', 'X>Y?', 'GTO 41', 'GTO 62']


def patch(L, wait='50'):
    """(new lines, number of key waits changed, SKY loops changed). wait: the PAUSE of the key waits; a wait
    that already has a PAUSE (LBL n / PAUSE m / KEY? r / GTO n) gets this value too."""
    sky = dead = 0
    out, i = [], 0
    while i < len(L):
        m = re.fullmatch(r'TICKS', L[i])
        if (m and i >= 1 and L[i - 1] == 'PAUSE 0' and i + 7 < len(L) and re.fullmatch(r'\d+', L[i + 1])
                and L[i + 2:i + 7] == ['+', 'STO 38', 'LBL 41', 'KEY? 39', 'GTO 46']):
            out.pop()                                            # the PAUSE 0
            out += ['PAUSE ' + L[i + 1], 'KEY? 39', 'GTO 62']
            sky += 1
            i += 7
            continue
        if L[i:i + 6] == DEAD and sky > dead:                    # its end-of-second test (LBL 46): no longer reached
            dead += 1
            i += 6
            continue
        out.append(L[i])
        i += 1
    L, out, waits, i = out, [], 0, 0
    while i < len(L):
        if re.fullmatch(r'LBL \d+', L[i]) and i + 2 < len(L) and L[i + 1].startswith('KEY? ') and L[i + 2] == 'GTO ' + L[i][4:]:
            if out and out[-1] == 'PAUSE 0':                     # PAUSE 50 shows the screen itself
                out.pop()
            out += [L[i], 'PAUSE ' + wait, L[i + 1], L[i + 2]]
            waits += 1
            i += 3
            continue
        if (re.fullmatch(r'LBL \d+', L[i]) and i + 3 < len(L) and re.fullmatch(r'PAUSE \d+', L[i + 1])
                and L[i + 2].startswith('KEY? ') and L[i + 3] == 'GTO ' + L[i][4:]):      # already in a PAUSE
            out += [L[i], 'PAUSE ' + wait, L[i + 2], L[i + 3]]
            i += 4
            continue
        out.append(L[i])
        i += 1
    assert dead == sky, 'keywait_patch: the SKY loop is not as expected'
    return out, waits, sky


def main():
    for path in sys.argv[1:]:
        raw = open(path, encoding='utf-8').read()
        L = raw.split('\n')
        new, waits, sky = patch(L)
        open(path, 'w', encoding='utf-8').write('\n'.join(new))
        print('%s: %d key waits, %d SKY loops' % (path, waits, sky))


if __name__ == '__main__':
    main()
