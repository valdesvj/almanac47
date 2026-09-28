#!/usr/bin/env python3
"""genmenug.py - MENUG: test of a graphic menu with KEY? (no PROMPT).

The menu is drawn with PTXS; the program waits with KEY? for a key:
  1-9  the item is inverted for a moment (GRMOD 3, XOR box), then its page opens
  0    end
  +    (on a page) back to the menu
  any other key: its keycode is shown in the title line (to check the key numbers).
The pages are dummies for this test ("PAGE n"); the NAV views come later.

Keycodes (KEY?: row x 10 + column, the soft keys are row 1):
  7 8 9 = 52 53 54   4 5 6 = 62 63 64   1 2 3 = 72 73 74   0 = 82   + = 85
  digit = (7 - row) x 3 + column - 1   for rows 5-7, columns 2-4.
Needs PTXS and PTXT. Registers R45-R51 (and R30-R36 through the fonts).

Writes extras/MENUG.txt and docs/MENUG_preview.png.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, 'python', 'native')]

ITEMS = ['ALMANAC', 'CHART', 'TEXT', 'SKY', 'SMALL', 'SPLIT', 'BODY', 'ANIM', 'ALLSKY']
TOP, PITCH, XL, XR = 180, 30, 16, 206
BOX_W, BOX_H = 170, 16


def place(d):
    """Base line row and column of menu item d (1-9, 0 = END)."""
    if d == 0:
        return TOP - 4 * PITCH, XR
    i = d - 1
    return (TOP - i * PITCH, XL) if i < 5 else (TOP - (i - 5) * PITCH, XR)


def program():
    P = []
    a = lambda *s: P.extend(str(x) for x in s)
    a('LBL "MENUG"')
    # --- LBL 01: draw the menu
    a('LBL 01', 'CLLCD', 222, 2, '"C47 NAV - MENU"', 'XEQ "PTXS"', 216, 0, 400, 'XEQ "PHLS"')
    for d in list(range(1, 10)) + [0]:
        y, x = place(d)
        a(y, x, '"%d %s"' % (d, ITEMS[d - 1] if d else 'END'), 'XEQ "PTXS"')
    a(4, 2, '"PRESS A NUMBER     + BACK TO THE MENU"', 'XEQ "PTXT"')
    # --- LBL 02: wait for a key (KEY? skips the GTO when a key was pressed)
    a('LBL 02', 'KEY? 45', 'GTO 02',
      'RCL 45', 85, 'X=Y?', 'GTO 01',                       # + on the menu: draw it again
      'RCL 45', 82, 'X=Y?', 'GTO 09',                       # 0: end
      'RCL 45', 10, '÷', 'IP', 'STO 46', 'RCL 45', 10, 'MOD', 'STO 47',
      'RCL 46', 5, 'X>Y?', 'GTO 08', 'RCL 46', 7, 'X<Y?', 'GTO 08',      # row 5-7
      'RCL 47', 2, 'X>Y?', 'GTO 08', 'RCL 47', 4, 'X<Y?', 'GTO 08',      # column 2-4
      7, 'RCL- 46', 3, '×', 'RCL+ 47', 1, '-', 'STO 48',                # the digit
      'XEQ 20', 'PAUSE 3', 'XEQ 30', 'GTO 01')
    # --- LBL 08: not a menu key: show its keycode in the title line
    a('LBL 08', 218, 0, 'CLLCDxy', 222, 2, '"KEY "', 'XEQ "PTXS"', 'RCL 45', 'XEQ "PINS"', 'GTO 02')
    a('LBL 09', 'CLLCD', 'RTN')
    # --- LBL 20: invert menu item R48 (XOR box): R51 = row, R50 = column
    a('LBL 20', 'RCL 48', 'X=0?', 'GTO 21', 1, '-', 'STO 49', XL - 4, 'STO 50',
      4, 'RCL 49', 'X>Y?', 'GTO 22', 'GTO 23',              # index 5-8: right column
      'LBL 22', 5, 'STO- 49', XR - 4, 'STO 50', 'GTO 23',
      'LBL 21', 4, 'STO 49', XR - 4, 'STO 50',
      'LBL 23', TOP - 2, 'RCL 49', PITCH, '×', '-', 'STO 51',
      'WSIZE 18', 3, 'STO 32', 'GRMOD 32', '1' * BOX_H + '#2', 'STO 32',
      'RCL 51', 'RCL 50', BOX_W, 'STO 33', 'R↓',
      'LBL 24', 'AGRAPH 32', 'DSE 33', 'GTO 24',
      0, 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN')
    # --- LBL 30: the page (a dummy for the test); + goes back
    a('LBL 30', 'CLLCD', 222, 2, '"PAGE "', 'XEQ "PTXS"', 'RCL 48', 'XEQ "PINS"', 216, 0, 400, 'XEQ "PHLS"',
      120, 110, '"THIS IS PAGE "', 'XEQ "PTXS"', 'RCL 48', 'XEQ "PINS"',
      4, 2, '"+ BACK TO THE MENU"', 'XEQ "PTXT"',
      'LBL 31', 'KEY? 45', 'GTO 31', 'RCL 45', 85, 'X≠Y?', 'GTO 31', 'RTN', 'END')
    return P


def preview(path):
    import c47screen as S
    from PIL import Image
    shots = []
    for hi in (None, 1):
        sc = S.Screen(S.STD)
        sc.text(222, 2, 'C47 NAV - MENU'); sc.hline(216, 0, 400)
        for d in list(range(1, 10)) + [0]:
            y, x = place(d)
            sc.text(y, x, '%d %s' % (d, ITEMS[d - 1] if d else 'END'))
        sc.small(4, 2, 'PRESS A NUMBER     + BACK TO THE MENU')
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


if __name__ == '__main__':
    P = program()
    out = os.path.join(ROOT, 'extras', 'MENUG.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    preview(os.path.join(ROOT, 'docs', 'MENUG_preview.png'))
    print(out, len(P), 'lines')
