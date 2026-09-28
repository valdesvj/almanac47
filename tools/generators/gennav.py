#!/usr/bin/env python3
"""gennav.py - NAV: the menu of the navigation suite, drawn on the graphics screen.

The menu is drawn with PTXS; KEY? waits for a key (no PROMPT):
  1-9  the item is inverted for a moment (GRMOD 3, XOR box), NAV asks DATE UTC LAT LON
       (INPUT) and runs the view; every view waits for + (WPLS) and comes back here
  0    end
Keycodes (row x 10 + column, soft keys = row 1): 7 8 9 = 52-54, 4 5 6 = 62-64,
1 2 3 = 72-74, 0 = 82, + = 85; digit = (7 - row) x 3 + column - 1.
Registers: R39 keycode, R38 digit, R36/R37 while inverting (and R30-R36 in the fonts).

  python3 gennav.py      -> programs/NAV.txt, docs/NAV_menu_preview.png
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, 'python', 'native')]

ITEMS = ['ALMANAC', 'CHART', 'TEXT', 'SKY', 'SMALL', 'SPLIT', 'BODY', 'ANIM', 'ALLSKY']
VIEWS = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'ALMS', 'HALMH', 'BODY', 'HANIM', 'ALLSKY']
TOP, PITCH, XL, XR = 190, 30, 16, 206
BOX_W, BOX_H = 170, 16
TITLE = 'C47 NAV'
HINT = 'KEY A NUMBER      + BACK TO THE MENU'
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'


def place(d):
    """Base line row and column of menu item d (1-9, 0 = END)."""
    if d == 0:
        return TOP - 4 * PITCH, XR
    i = d - 1
    return (TOP - i * PITCH, XL) if i < 5 else (TOP - (i - 5) * PITCH, XR)


def inputs():
    """LBL 20 (DATE UTC LAT LON -> Z JD, Y lat, X lon), LBL 30, LBL 31: from the old NAV."""
    old = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'programs', 'NAV.txt'), encoding='utf-8')]
    i = old.index('LBL 20')
    assert old[-1] == 'END' and 'INPUT "DATE"' in old[i:]
    return old[i:-1]


def program(inp):
    P = []
    a = lambda *s: P.extend(str(x) for x in s)
    a('LBL "NAV"', 'LBL 01', 'XEQ 40')
    # wait for a key; 0 ends; a digit key 1-9 opens its view
    a('LBL 02', 'KEY? 39', 'GTO 02',
      'RCL 39', 82, 'X=Y?', 'GTO 09',
      'RCL 39', 10, '÷', 'IP', 'STO 38', 5, 'X>Y?', 'GTO 02', 'RCL 38', 7, 'X<Y?', 'GTO 02',     # row 5-7
      'RCL 39', 10, 'MOD', 'STO 37', 2, 'X>Y?', 'GTO 02', 'RCL 37', 4, 'X<Y?', 'GTO 02',        # column 2-4
      7, 'RCL- 38', 3, '×', 'RCL+ 37', 1, '-', 'STO 38',                                   # the digit
      'XEQ 41', 'PAUSE 3')
    for d in range(1, 10):
        a(d, 'RCL 38', 'X=Y?', 'GTO %d' % (9 + d))
    a('GTO 01', 'LBL 09', 'CLLCD', 'RTN')
    for d, v in enumerate(VIEWS, 1):
        a('LBL %d' % (9 + d), 'XEQ 20', 'XEQ "%s"' % v, 'GTO 01')
    # LBL 40: the menu
    a('LBL 40', 'CLLCD', 222, 2, '"%s"' % TITLE, 'XEQ "PTXS"', 216, 0, 400, 'XEQ "PHLS"')
    for d in list(range(1, 10)) + [0]:
        y, x = place(d)
        a(y, x, '"%d %s"' % (d, ITEMS[d - 1] if d else 'END'), 'XEQ "PTXS"')
    a(36, 2, '"%s"' % HINT, 'XEQ "PTXS"', 22, 0, 400, 'XEQ "PHLS"', 5, 2, '"%s"' % WARNING, 'XEQ "PTXS"', 'RTN')
    # LBL 41: invert item R38 (XOR box, GRMOD 3)
    a('LBL 41', 'WSIZE 18', 3, 'STO 32', 'GRMOD 32', '1' * BOX_H + '#2', 'STO 32',
      'RCL 38', 1, '-', 'STO 37', XL - 4, 'STO 36', 4, 'RCL 37', 'X>Y?', 'XEQ 42',
      TOP - 2, 'RCL 37', PITCH, '×', '-', 'RCL 36', BOX_W, 'STO 33', 'R↓',
      'LBL 43', 'AGRAPH 32', 'DSE 33', 'GTO 43',
      0, 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN',
      'LBL 42', 5, 'STO- 37', XR - 4, 'STO 36', 'RTN')
    return P + inp + ['END']


def preview(path):
    import c47screen as S
    from PIL import Image
    shots = []
    for hi in (None, 2):
        sc = S.Screen(S.STD)
        sc.text(222, 2, TITLE); sc.hline(216, 0, 400)
        for d in list(range(1, 10)) + [0]:
            y, x = place(d)
            sc.text(y, x, '%d %s' % (d, ITEMS[d - 1] if d else 'END'))
        sc.text(36, 2, HINT); sc.hline(22, 0, 400); sc.text(5, 2, WARNING)
        if hi:
            y, x = place(hi)
            sc.xor_box(y - 2, x - 4, BOX_W, BOX_H)
        shots.append(sc)
    im = Image.new('L', (808, 240), 120)
    for k, sc in enumerate(shots):
        for x in range(400):
            for y in range(240):
                im.putpixel((k * 408 + x, 239 - y), 20 if (x, y) in sc.pix else 220)
    im.resize((1616, 480), Image.NEAREST).save(path)
    print('widest text ends at', max(S.Screen(S.STD).text(0, 2, t) for t in (HINT, WARNING)))


if __name__ == '__main__':
    P = program(inputs())
    open(os.path.join(ROOT, 'programs', 'NAV.txt'), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    preview(os.path.join(ROOT, 'docs', 'NAV_menu_preview.png'))
    print('programs/NAV.txt', len(P), 'lines')
