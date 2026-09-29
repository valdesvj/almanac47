#!/usr/bin/env python3
"""genc64.py - C64: a tribute to the 8-bit home computers, drawn on the C47 with AGRAPH.

A blocky 8 x 8 font in the C64 style (drawn here, not the Commodore character ROM), a dark
border (full-width and full-height lines with PIXEL), a 40 x 25 text screen of 320 x 200 px:

    **** ALMANAC 47 BASIC V2 ****
 64K RAM SYSTEM  38911 BASIC BYTES FREE
READY.
RUN                      <- typed letter by letter, the cursor blinking
                         <- RUN/STOP: an empty line, as on the C64
BREAK IN 47
READY.
_                        <- the cursor blinks until a key is pressed (then the screen clears)

Each glyph column is one AGRAPH (bit 0 = bottom row), as in the Almanac 47 fonts; the cursor
is an 8 x 8 block drawn with GRMOD 3 (XOR), so drawing it twice removes it.

  python3 genc64.py   -> extras/C64.txt, extras/C64_rem.txt, docs/C64_tribute.gif
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 8 x 8 glyphs, top row first; column 7 and row 7 stay empty (the gap between letters and lines)
G = {
 'A': ["   ##   ", "  ####  ", " ##  ## ", " ###### ", " ##  ## ", " ##  ## ", " ##  ## "],
 'B': [" #####  ", " ##  ## ", " ##  ## ", " #####  ", " ##  ## ", " ##  ## ", " #####  "],
 'C': ["  ####  ", " ##  ## ", " ##     ", " ##     ", " ##     ", " ##  ## ", "  ####  "],
 'D': [" ####   ", " ## ##  ", " ##  ## ", " ##  ## ", " ##  ## ", " ## ##  ", " ####   "],
 'E': [" ###### ", " ##     ", " ##     ", " ####   ", " ##     ", " ##     ", " ###### "],
 'F': [" ###### ", " ##     ", " ##     ", " ####   ", " ##     ", " ##     ", " ##     "],
 'I': ["  ####  ", "   ##   ", "   ##   ", "   ##   ", "   ##   ", "   ##   ", "  ####  "],
 'K': [" ##  ## ", " ## ##  ", " ####   ", " ###    ", " ####   ", " ## ##  ", " ##  ## "],
 'L': [" ##     ", " ##     ", " ##     ", " ##     ", " ##     ", " ##     ", " ###### "],
 'M': [" ##   ##", " ### ###", " #######", " ## # ##", " ##   ##", " ##   ##", " ##   ##"],
 'N': [" ##  ## ", " ### ## ", " ###### ", " ###### ", " ## ### ", " ##  ## ", " ##  ## "],
 'R': [" #####  ", " ##  ## ", " ##  ## ", " #####  ", " ####   ", " ## ##  ", " ##  ## "],
 'S': ["  ####  ", " ##  ## ", " ##     ", "  ####  ", "     ## ", " ##  ## ", "  ####  "],
 'T': [" ###### ", "   ##   ", "   ##   ", "   ##   ", "   ##   ", "   ##   ", "   ##   "],
 'U': [" ##  ## ", " ##  ## ", " ##  ## ", " ##  ## ", " ##  ## ", " ##  ## ", "  ####  "],
 'V': [" ##  ## ", " ##  ## ", " ##  ## ", " ##  ## ", " ##  ## ", "  ####  ", "   ##   "],
 'Y': [" ##  ## ", " ##  ## ", " ##  ## ", "  ####  ", "   ##   ", "   ##   ", "   ##   "],
 '1': ["   ##   ", "  ###   ", "   ##   ", "   ##   ", "   ##   ", "   ##   ", " ###### "],
 '2': ["  ####  ", " ##  ## ", "     ## ", "    ##  ", "  ##    ", " ##     ", " ###### "],
 '3': ["  ####  ", " ##  ## ", "     ## ", "   ###  ", "     ## ", " ##  ## ", "  ####  "],
 '4': ["     ## ", "    ### ", "   #### ", " ##  ## ", " #######", "     ## ", "     ## "],
 '6': ["  ####  ", " ##  ## ", " ##     ", " #####  ", " ##  ## ", " ##  ## ", "  ####  "],
 '7': [" ###### ", " ##  ## ", "    ##  ", "   ##   ", "   ##   ", "   ##   ", "   ##   "],
 '8': ["  ####  ", " ##  ## ", " ##  ## ", "  ####  ", " ##  ## ", " ##  ## ", "  ####  "],
 '9': ["  ####  ", " ##  ## ", " ##  ## ", "  ##### ", "     ## ", " ##  ## ", "  ####  "],
 '*': ["        ", " ##  ## ", "  ####  ", "########", "  ####  ", " ##  ## ", "        "],
 '.': ["        ", "        ", "        ", "        ", "        ", "   ##   ", "   ##   "],
}

LINES = [(1, 4, '**** ALMANAC 47 BASIC V2 ****'),
         (3, 1, '64K RAM SYSTEM  38911 BASIC BYTES FREE'),
         (5, 0, 'READY.')]
X0, YTOP = 40, 212            # text column 0 = x 40; text row r has its bottom pixel row at 212 - 8 r


def columns(ch):
    rows = G[ch] + ['        ']
    cols = []
    for c in range(8):
        v = 0
        for r in range(8):                 # r = 0 top ... 7 bottom; bit 0 = bottom
            if rows[r][c] == '#':
                v |= 1 << (7 - r)
        cols.append(v)
    return cols


def glyph(ch):
    """LBL code: draws the glyph at row R31, column R30, then R30 + 8."""
    L = ['LBL %d' % ord(ch), 'RCL 31', 'RCL 30']
    last = None
    for v in columns(ch):
        if v == last:
            L.append('AGRAPH 32')
        else:
            L += ['%s#2' % bin(v)[2:], 'STO 32', 'R↓', 'AGRAPH 32']
        last = v
    return L + ['8', 'STO+ 30', 'RTN']


def at(r, c):
    return [str(YTOP - 8 * r), str(X0 + 8 * c)]


def program(rem=False):
    R = (lambda t: ['REM "%s"' % t]) if rem else (lambda t: [])
    P = ['LBL "C64"'] + R('C64 - tribute to the 8-bit home computers: boot screen, RUN, RUN/STOP, READY.')
    P += R('The dark border: full-height columns (PIXEL with a negative x) and full-width rows (negative y)')
    P += R('Row 0 and column 0 cannot be a negative PIXEL (-0): the bottom 16 rows and column 0 are AGRAPH columns of 16 bits (WSIZE 32)')
    P += ['CLLCD', 'WSIZE 32', '0', 'STO 34', 'GRMOD 34',
          '1111111111111111#2', 'STO 32', '400', 'STO 35', '0', '0', 'LBL 04', 'AGRAPH 32', 'DSE 35', 'GTO 04',
          '16.224016', 'STO 35', 'LBL 07', 'RCL 35', 'IP', '0', 'AGRAPH 32', 'ISG 35', 'GTO 07',
          '1.039', 'STO 35', 'LBL 01', 'RCL 35', 'IP', 'CHS', '0', 'X<>Y', 'PIXEL',
          'RCL 35', 'IP', '360', '+', 'CHS', '0', 'X<>Y', 'PIXEL', 'ISG 35', 'GTO 01',
          '-360', '0', 'X<>Y', 'PIXEL',
          '16.019', 'STO 35', 'LBL 02', 'RCL 35', 'IP', 'CHS', '0', 'PIXEL', 'ISG 35', 'GTO 02',
          '220.239', 'STO 35', 'LBL 08', 'RCL 35', 'IP', 'CHS', '0', 'PIXEL', 'ISG 35', 'GTO 08']
    P += R('The boot text, all at once')
    for r, c, t in LINES:
        P += at(r, c) + ['"%s"' % t, 'XEQ 90']
    P += ['PAUSE 10'] + R('The cursor blinks under READY., then RUN is typed letter by letter')
    P += at(6, 0) + ['XEQ 94', 'XEQ 94', 'XEQ 94']
    P += at(6, 0) + ['"RUN"', 'XEQ 91', 'PAUSE 8'] + R('RUN/STOP: the break message and READY. again')
    P += at(8, 0) + ['"BREAK IN 47"', 'XEQ 90'] + at(9, 0) + ['"READY."', 'XEQ 90']
    P += R('The cursor blinks until a key is pressed (not R/S or EXIT), then the screen clears')
    P += at(10, 0) + ['STO 37', 'R↓', 'STO 38',
                     'LBL 03', 'RCL 38', 'RCL 37', 'XEQ 93', 'PAUSE 3', 'KEY? 39', 'GTO 03',
                     'CLLCD', 'WSIZE 64', 'CLSTK', 'RTN']
    P += R('LBL 90: text - Z row, Y column, X text; each character is its glyph label (the character code)')
    P += ['LBL 90', 'STO 33', 'R↓', 'STO 30', 'R↓', 'STO 31',
          'LBL 05', 'αLENG 33', 'X=0?', 'RTN', 'α→𝑥 33', 'STO 32', 'XEQ IND 32', 'GTO 05']
    P += R('LBL 91: the same, typed: one letter at a time with the cursor after it')
    P += ['LBL 91', 'STO 33', 'R↓', 'STO 30', 'R↓', 'STO 31',
          'LBL 06', 'αLENG 33', 'X=0?', 'RTN', 'α→𝑥 33', 'STO 32', 'XEQ IND 32',
          'RCL 31', 'RCL 30', 'XEQ 93', 'PAUSE 3', 'RCL 31', 'RCL 30', 'XEQ 93', 'GTO 06']
    P += R('LBL 93: the cursor, an 8 x 8 block drawn with XOR (GRMOD 3): twice = gone. Y row, X column')
    P += R('Row and column go to R35/R36 first: GRMOD may leave a number on the stack (it moved the cursor)')
    P += ['LBL 93', 'STO 36', 'R↓', 'STO 35', '3', 'STO 34', 'GRMOD 34', '11111111#2', 'STO 32', 'RCL 35', 'RCL 36',
          'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32', 'AGRAPH 32',
          '0', 'STO 34', 'GRMOD 34', 'RTN']
    P += R('LBL 94: one blink of the cursor at Y row, X column (on 0.5 s, off 0.5 s)')
    P += ['LBL 94', 'STO 37', 'R↓', 'STO 38', 'RCL 38', 'RCL 37', 'XEQ 93', 'PAUSE 5',
          'RCL 38', 'RCL 37', 'XEQ 93', 'PAUSE 5', 'RCL 38', 'RCL 37', 'RTN']
    P += ['LBL 32', '8', 'STO+ 30', 'RTN']                        # space
    for ch in sorted(G):
        P += R("glyph '%s'" % ch) + glyph(ch)
    return P + ['END']


def preview(path):
    sys.path.insert(0, os.path.join(ROOT, 'python'))
    import c47sim
    from PIL import Image
    f = os.path.join(ROOT, 'extras', 'C64.txt')
    c = c47sim.load([f]); c.keys = [72]; c.frames = []; c.pix = []
    c.run('C64', maxsteps=10 ** 7)
    ims = []
    for fr in c.frames:
        im = Image.new('P', (400, 240)); im.putpalette([0x6c, 0x5e, 0xb5, 0x35, 0x28, 0x79] + [0] * 762)
        px = im.load()
        for x in range(400):
            for y in range(240):
                px[x, y] = 0
        for y, x in fr:
            if 0 <= x < 400 and 0 <= y < 240:
                px[x, 239 - y] = 1
        ims.append(im.resize((800, 480), Image.NEAREST))
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=[400] * len(ims), loop=0)
    return len(ims)


if __name__ == '__main__':
    for rem, name in ((False, 'C64.txt'), (True, 'C64_rem.txt')):
        P = program(rem)
        open(os.path.join(ROOT, 'extras', name), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    print('extras/C64.txt', len(program()), 'lines;', preview(os.path.join(ROOT, 'docs', 'C64_tribute.gif')), 'frames')
