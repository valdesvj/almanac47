#!/usr/bin/env python3
"""gennav.py - NAV: the menu of the navigation suite, drawn on the graphics screen.

The menu is drawn with PTXS; KEY? waits for a key (no PROMPT):
  NAV asks DATE UTC LAT LON once (INPUT), at the start; the menu title shows date and time.
  1-9  the item is inverted for a moment (GRMOD 3, XOR box) and the view runs; every
       drawn view waits (WPLS): + back to the menu, up arrow = one hour later, down
       arrow = one hour earlier (the view is drawn again; the offset stays, R"DH")
  0    end
The sky is computed once per time and place into matrix ALMC (CACHE, gencache.py); the views
only draw from it.
Compact version (build_navfull.py): items 1 2 4 9 only. With autoinit NAV and INIT share one
file: the first NAV runs INIT (flag 81 set); INIT is then deleted by hand.
Keycodes (row x 10 + column, soft keys = row 1): 7 8 9 = 52-54, 4 5 6 = 62-64,
1 2 3 = 72-74, 0 = 82, + = 85; digit = (7 - row) x 3 + column - 1.
Registers: R39 keycode, R38 digit, R36/R37 while inverting (and R30-R36 in the fonts);
variables DATE UTC LAT LON, DH (hours added by the arrows), VW (the view shown).

  python3 gennav.py      -> programs/NAV.txt, docs/NAV_menu_preview.png
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, 'python', 'native'), os.path.dirname(os.path.abspath(__file__))]
import gencache

ITEMS = ['ALMANAC', 'CHART', 'TEXT', 'SKY', 'SMALL', 'SPLIT', 'BODY', 'ANIM', 'ALLSKY']
VIEWS = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'ALMS', 'HALMH', 'BODY', 'HANIM', 'ALLSKY']
TOP, PITCH, XL, XR = 176, 28, 16, 206
BOX_W, BOX_H = 170, 16
TITLE = 'ALMANAC 47'
UP, DOWN = 51, 61                      # arrow keycodes
ANTS = 0                               # easter egg: the step after LBL 48 in NAV; 20 gives 20 ants (0.1 s each)
HINT = 'KEY A NUMBER    + MENU    UP DOWN 1 HOUR'
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'


ALL = list(range(1, 10))
COMPACT = [1, 2, 4, 9]                 # compact version: ALMANAC CHART SKY ALLSKY


def place(d, items=ALL):
    """Base line row and column of menu item d (1-9, 0 = END): two columns of 5 for the
    full menu, one column for a short one."""
    order = list(items) + [0]
    i = order.index(d)
    if len(order) <= 5:
        return TOP - i * PITCH, XL
    return (TOP - i * PITCH, XL) if i < 5 else (TOP - (i - 5) * PITCH, XR)


OLD_INPUT = 'LBL 20|INPUT "DATE"|INPUT "UTC"|INPUT "LAT"|INPUT "LON"|RCL "DATE"|10000|×|0.5|+|IP|STO 03|10000|÷|IP|STO 01|RCL 03|100|÷|IP|100|MOD|STO 02|RCL 03|100|MOD|STO 03|RCL "UTC"|10000|×|0.5|+|IP|STO 04|100|MOD|3600|÷|RCL 04|100|÷|IP|100|MOD|60|÷|+|RCL 04|10000|÷|IP|+|STO 04|RCL 02|3|X>Y?|XEQ 31|RCL 01|100|÷|IP|STO 05|2|RCL- 05|RCL 05|4|÷|IP|+|STO 05|RCL 01|4716|+|365.25|×|IP|RCL 02|1|+|30.6001|×|IP|+|RCL+ 03|RCL+ 05|1524.5|-|RCL 04|24|÷|+|STO 06|RCL "LAT"|XEQ 30|STO 07|RCL "LON"|XEQ 30|STO 08|RCL 06|RCL 07|RCL 08|RTN|LBL 30|STO 38|IP|RCL 38|FP|100|×|60|÷|+|RTN|LBL 31|1|STO- 01|12|STO+ 02|RTN'


def inputs():
    """LBL 20: INPUT DATE UTC LAT LON (once, at the start).
    LBL 21: Z JD (+ R"DH" hours from the arrow keys), Y lat, X lon from those variables; JD also in R06.
    The date with the calculator's own functions: x→ⅅ (the DATE number in the calculator's date
    format, e.g. YYYY.MMDD) and ⅅ→J (Julian day number, .0 = noon): JD of 0 h UT = JDN - 0.5."""
    L = OLD_INPUT.split('|')
    k = L.index('RCL "DATE"')
    u = L.index('RCL "UTC"'); v = L.index('STO 04', L.index('RCL 04', u + 8))       # UTC hh.mmss -> hours in R04
    hours = L[u:v + 1]
    tail = L[L.index('RCL "LAT"'):]                                                   # lat, lon, return, LBL 30
    body = (['RCL "DATE"', 'x→ⅅ', 'ⅅ→J', '0.5', '-', 'STO 06'] + hours + ['24', '÷', 'STO+ 06',
            'RCL "DH"', '24', '÷', 'STO+ 06'] + tail)
    body = body[:body.index('LBL 31')]                                                # month shift: not needed
    return L[:k] + ['RTN', 'LBL 21'] + body


LETTERED = 'IJKMNPQRSEFGHOUVW'


def text_steps(lab):
    """TEXT: the almanac page as text (ALMR) in R50 ... R76, and lines 1-26 also in the stack and
    the lettered registers in the order of the register browser: X Y Z T A B C D, L, I J K M N P Q
    R S E F G H O U V W. lab = a free local label for the loop that blanks R50-R78."""
    t = ['50.078', 'STO 49', 'LBL %d' % lab, '" "', 'STO IND 49', 'ISG 49', 'GTO %d' % lab,
         'XEQ 21', 'XEQ "ALMR"', '" "', 'RCL 58', '+']                  # line 9 -> LASTx (L)
    for k, r in enumerate(LETTERED):
        t += ['RCL %d' % (59 + k), 'STO %s' % r]                        # lines 10-26
    return t + ['RCL %d' % r for r in range(57, 49, -1)]               # lines 8 ... 1: X = line 1


def program(inp, items=ALL, autoinit=False):
    """autoinit: the first NAV runs INIT (builds the matrices); flag 81 remembers that it is done
    (CF 81 before loading a new INIT). INIT is deleted by hand (DELP in a program made the file
    fail to load: "invalid data")."""
    P = []
    a = lambda *s: P.extend(str(x) for x in s)
    a('LBL "NAV"')
    if autoinit:
        a('FS? 81', 'GTO 04', '"INIT"', 'STO 49', 'XEQ IND 49', 'SF 81', 'LBL 04')   # INIT once (by name in R49: no call to a program that is not in the file)
    a('SSIZE#', 'STO "SSZ"', 'SSIZE8')                                     # fonts read stack register D: 8-level stack (put back at the end)
    a(*gencache.NEWMAT)                                                    # the sky cache (CACHE, gencache.py): empty = computed at the first view
    a(0, 'STO "DH"', 'XEQ 20', 'XEQ 28', 'LBL 01', 'XEQ 40')                          # DATE UTC LAT LON once
    # wait for a key; 0 ends; a digit key opens its view
    # PAUSE 1: on the real C47 the screen is only sent to the display at a PAUSE (or a key), not
    # while the program waits in a KEY? loop - without it the menu stays invisible until a key
    a('PAUSE 1', 'LBL 02', 'KEY? 39', 'GTO 02',
      'RCL 39', 82, 'X=Y?', 'GTO 09',
      'RCL 39', UP, 'X=Y?', 'GTO 22', 'RCL 39', DOWN, 'X=Y?', 'GTO 23',        # arrows: the menu one hour later / earlier
      'RCL 39', 10, '÷', 'IP', 'STO 38', 5, 'X>Y?', 'GTO 26', 'RCL 38', 7, 'X<Y?', 'GTO 26',     # row 5-7
      'RCL 39', 10, 'MOD', 'STO 37', 2, 'X>Y?', 'GTO 26', 'RCL 37', 4, 'X<Y?', 'GTO 26',        # column 2-4
      7, 'RCL- 38', 3, '×', 'RCL+ 37', 1, '-', 'STO 38')                                   # the digit
    for d in items:
        a(d, 'RCL 38', 'X=Y?', 'GTO %d' % (60 + d))
    a('LBL 26', 'GTO 02')                                                   # another key: ignored, the menu stays
    a('LBL 03', 0, 'STO 39')                                                # LBL 03: (re)draw view VW
    for d in items:
        a(d, 'RCL "VW"', 'X=Y?', 'GTO %d' % (9 + d))
    a('GTO 01', 'LBL 09', 'CLLCD', 'LBL 08', 'RCL "SSZ"', 4, 'X=Y?', 'SSIZE4', 'RTN',   # LBL 08: the user's stack size back
      'LBL 22', 1, 'STO+ "DH"', 'XEQ 48', 'XEQ 28', 'GTO 01', 'LBL 23', 1, 'STO- "DH"', 'XEQ 48', 'XEQ 28', 'GTO 01')
    for d in items:
        if d == 3:                          # TEXT: the page into the registers, NAV ends in REGS
            a('LBL 12', *text_steps(24)); a('XEQ 08', 'REGS', 'RTN')
        else:
            a('LBL %d' % (9 + d), 'XEQ 21', 'XEQ "%s"' % VIEWS[d - 1], 'GTO 05')
    # LBL 6d: item d chosen: invert it for a moment, then its view
    for d in items:
        y, x = place(d, items)
        a('LBL %d' % (60 + d), y - 2, 'STO 37', x - 4, 'STO 36', 'XEQ 41', 'PAUSE 1', 'XEQ 48', d, 'STO "VW"', 'GTO 03')
    # after a view (it returns on +, up or down, R39): up one hour later, down one hour earlier, + the menu
    a('LBL 05', 'RCL 39', UP, 'X=Y?', 'GTO 06', 'RCL 39', DOWN, 'X=Y?', 'GTO 07', 'XEQ 48', 'GTO 01',
      'LBL 06', 1, 'STO+ "DH"', 'XEQ 48', 'GTO 03', 'LBL 07', 1, 'STO- "DH"', 'XEQ 48', 'GTO 03',
      # LBL 48: ants over the screen that is shown (XOR, so they show on black too), 0.1 s apart.
      # The C47 shows the screen only at a PAUSE: while the next screen is computed and drawn the
      # display keeps this one, ants included, until the new screen's PAUSE 1.
      'LBL 48', ANTS, 'X=0?', 'RTN', 'STO 49', 'LBL 46', 'XEQ 47', 'PAUSE 1', 'DSE 49', 'GTO 46', 'RTN',
      # LBL 47: one ant (10 x 14 pixels) at a random place, column by column, GRMOD 3 (XOR)
      'LBL 47', 'XEQ 50',
      'RAN#', 390, '×', 'IP', 'STO 36', 'RAN#', 180, '×', 'IP', 20, '+', 'STO 37', 'RCL 37', 'RCL 36', 'XEQ 42', 'XEQ 51', 'RTN',
      # LBL 42: one ant (10 x 14 pixels) at Y = row, X = column, column by column (GRMOD 3 set by LBL 50)
      'LBL 42',
      '11000000000000#2', 'STO 32', 'R↓', 'AGRAPH 32', 'AGRAPH 32',                    # feelers
      '00111100111111#2', 'STO 32', 'R↓', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32',        # head and body
      'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32',
      '11000000000000#2', 'STO 32', 'R↓', 'AGRAPH 32', 'AGRAPH 32', 'RTN',             # feelers
      # LBL 50: XOR drawing on (WSIZE 16 for the column literals); LBL 51: back to normal
      'LBL 50', 'WSIZE 16', 3, 'STO 32', 'GRMOD 32', 'RTN',
      'LBL 51', 0, 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN',
      # LBL 28: the sky for the time and place in use, before the menu (CACHE): Sun, Moon,
      # planets (CSUN), the sun times (CNTA) and every star (CSQK); a view then only draws
      'LBL 28', 'XEQ 21', 'STO 92', 'R↓', 'STO 91', 'R↓', 'STO 90', 'XEQ "HCZI"', 'RCL 90', 'XEQ "CSUN"',
      'RCL 90', 0.5, '-', 'IP', 0.5, '+', 'RCL 91', 'RCL 92', 'XEQ "CNTA"',
      1, 'STO 82', 'LBL 29', 'RCL 82', 'XEQ "CSQK"', 1, 'STO+ 82', 58, 'RCL 82', 'X≤Y?', 'GTO 29', 'RTN')
    # LBL 40: the menu. Title, validity of the matrices (variable VAL, set by INIT);
    # date, time and DR position in use (the arrows change the time: shown here too)
    a('LBL 40', 'XEQ 21', 'CLLCD', 224, 2, '"%s"' % TITLE, 'XEQ "PTXS"', 224, 230, '"VALID "', 'XEQ "PTXS"', 'RCL "VAL"', 'XEQ "PTXS"',
      206, 2, 'RCL 06', 'XEQ "PDTS"', 206, 80, 'RCL 06', 0.5, '+', 1, 'MOD', 24, '×', 'XEQ "PHMS"', 206, 116, '"UT"', 'XEQ "PTXS"',
      206, 150, '"DR"', 'XEQ "PTXS"',
      '"N"', 'STO 37', 'RCL 07', 'X<0?', 'XEQ 44', 206, 174, 'RCL 37', 'XEQ "PTXS"', 206, 176, 'RCL 07', 'ABS', 'XEQ "PDMS"',
      '"E"', 'STO 37', 'RCL 08', 'X<0?', 'XEQ 45', 206, 244, 'RCL 37', 'XEQ "PTXS"', 206, 246, 'RCL 08', 'ABS', 'XEQ "PDMS"',
      200, 0, 400, 'XEQ "PHLS"')
    for d in list(items) + [0]:
        y, x = place(d, items)
        a(y, x, '"%d %s"' % (d, ITEMS[d - 1] if d else 'END'), 'XEQ "PTXS"')
    a(36, 2, '"%s"' % HINT, 'XEQ "PTXS"', 22, 0, 400, 'XEQ "PHLS"', 5, 2, '"%s"' % WARNING, 'XEQ "PTXS"', 'RTN',
      'LBL 44', '"S"', 'STO 37', 'RTN', 'LBL 45', '"W"', 'STO 37', 'RTN')
    # LBL 41: XOR box (GRMOD 3) from row R37, column R36
    a('LBL 41', 'WSIZE 18', 3, 'STO 32', 'GRMOD 32', '1' * BOX_H + '#2', 'STO 32',
      'RCL 37', 'RCL 36', BOX_W, 'STO 33', 'R↓',
      'LBL 43', 'AGRAPH 32', 'DSE 33', 'GTO 43',
      0, 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN')
    return P + inp + ['END']


def preview(path, items=ALL):
    import c47screen as S
    from PIL import Image
    shots = []
    for hi in (None, items[1]):
        sc = S.Screen(S.STD)
        sc.text(224, 2, TITLE); x = sc.text(224, 230, 'VALID '); sc.text(224, x, '2026-2030')
        sc.pdat(206, 2, 2461312.25); sc.phm(206, 80, 18.0); sc.text(206, 116, 'UT'); sc.text(206, 150, 'DR')
        sc.text(206, 174, 'N'); sc.pdm(206, 176, 25.2); sc.text(206, 244, 'E'); sc.pdm(206, 246, 55.3)
        sc.hline(200, 0, 400)
        for d in list(items) + [0]:
            y, x = place(d, items)
            sc.text(y, x, '%d %s' % (d, ITEMS[d - 1] if d else 'END'))
        sc.text(36, 2, HINT); sc.hline(22, 0, 400); sc.text(5, 2, WARNING)
        if hi:
            y, x = place(hi, items)
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
    preview(os.path.join(ROOT, 'docs', 'NAV_compact_preview.png'), COMPACT)
    print('programs/NAV.txt', len(P), 'lines')
