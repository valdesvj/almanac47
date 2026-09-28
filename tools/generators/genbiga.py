#!/usr/bin/env python3
"""genbiga.py - BIGA: a big inverted 'A' in the middle of the C47 screen (AGRAPH + GRMOD XOR demo).

The 5x7 'A' is scaled x8 (40 x 56 pixels) and written in the middle of the screen (GRMOD 0, OR).
After 3 s its own cell is drawn solid over it with GRMOD 3 (XOR): the inverted 'A' has no outline
left and turns into a bug. One AGRAPH draws one column of 56 pixels (WSIZE 63).

Writes extras/BIGA.txt and docs/BIGA_preview.png.
  python3 tools/generators/genbiga.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

A = ['0111111', '1001000', '1001000', '1001000', '0111111']   # columns, top bit first, bit 0 = bottom
S = 8                                  # scale: 40 x 56 pixels
W, H = 5 * S, 7 * S
AX, AY = (400 - W) // 2, (240 - H) // 2


def scaled(col):
    """7-bit column -> 56-bit column (each bit repeated S times)."""
    return ''.join(b * S for b in col)


def program():
    leg, mid = scaled(A[0]).lstrip('0') + '#2', scaled(A[1]) + '#2'
    return [
        'LBL "BIGA"', 'WSIZE 63', 'CLLCD',
        '0', 'STO 00', 'GRMOD 00',                       # mode 0: OR
        str(AY), 'STO 31', str(AX), 'STO 30',
        leg, 'STO 32', str(S), 'XEQ 20',                 # write the A: left leg
        mid, 'STO 32', str(3 * S), 'XEQ 20',             # top bar and crossbar
        leg, 'STO 32', str(S), 'XEQ 20',                 # right leg
        'PAUSE 30',
        '3', 'STO 03', 'GRMOD 03',                       # mode 3: XOR
        str(AX), 'STO 30',
        '1' * H + '#2', 'STO 32', str(W), 'XEQ 20',      # invert the A's own cell: a bug
        '0', 'STO 00', 'GRMOD 00',                       # back to OR
        'WSIZE 64',
        '3', 'STO 34', 'LBL 01', 'PAUSE 99', 'DSE 34', 'GTO 01',
        'RTN',
        # LBL 20: draw column R32 X times, moving right
        'LBL 20', 'STO 33', 'LBL 21', 'XEQ 10', 'DSE 33', 'GTO 21', 'RTN',
        # LBL 10: one AGRAPH at row R31, column R30, then column + 1
        'LBL 10', 'RCL 31', 'RCL 30', 'AGRAPH 32', '1', 'STO+ 30', 'RTN',
        'END']


def frame(invert):
    from PIL import Image
    im = Image.new('L', (400, 240), 220)
    for i, col in enumerate(A):
        bits = scaled(col)[::-1]
        for k in range(S):
            for b in range(H):
                if (bits[b] == '1') != invert:
                    im.putpixel((AX + i * S + k, 239 - (AY + b)), 20)
    return im


def preview(path):
    from PIL import Image
    a, b = frame(False), frame(True)
    im = Image.new('L', (808, 240), 120)
    im.paste(a, (0, 0)); im.paste(b, (408, 0))
    im.resize((1616, 480), Image.NEAREST).save(path)


if __name__ == '__main__':
    out = os.path.join(ROOT, 'extras', 'BIGA.txt')
    P = program()
    open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    preview(os.path.join(ROOT, 'docs', 'BIGA_preview.png'))
    print(out, len(P), 'lines; A at', AX, AY)


# ---------------------------------------------------------------- BIGANT: the biggest one
# Full screen height: scale 34 -> 170 x 238 pixels. A column that tall needs several AGRAPH
# calls, one per band of 60 rows (60 60 60 58); WSIZE 63 keeps every literal positive.
BS = 34
BW, BH = 5 * BS, 7 * BS
BX, BY = (400 - BW) // 2, (240 - BH) // 2
BANDS = [(0, 60), (60, 60), (120, 60), (180, BH - 180)]
GROUPS = [(A[0], BS), (A[1], 3 * BS), (A[4], BS)]      # leg, top bar + crossbar, leg


def band_bits(col, lo, n, invert=False):
    """Bits lo .. lo+n-1 of the scaled column (bit 0 = bottom) as a binary literal, or None."""
    bits = ''.join(b * BS for b in col)[::-1][lo:lo + n]          # bit 0 first
    if invert:
        bits = '1' * n
    v = bits[::-1].lstrip('0')
    return v + '#2' if v else None


def bigant():
    P = ['LBL "BIGANT"', 'WSIZE 63', 'CLLCD', '0', 'STO 00', 'GRMOD 00']

    def layer(invert):
        for lo, n in BANDS:
            P.extend([str(BY + lo), 'STO 31', str(BX), 'STO 30'])
            groups = [(None, BW)] if invert else GROUPS
            for col, w in groups:
                lit = band_bits(col or '1' * 7, lo, n, invert)
                if lit is None:
                    P.extend([str(w), 'STO+ 30'])                    # empty: just move right
                else:
                    P.extend([lit, 'STO 32', str(w), 'XEQ 20'])
    layer(False)                                                     # write the A
    P.append('PAUSE 30')
    P.extend(['3', 'STO 03', 'GRMOD 03'])                            # XOR
    layer(True)                                                      # invert its cell: the ant
    P.extend(['0', 'STO 00', 'GRMOD 00', 'WSIZE 64',
              '3', 'STO 34', 'LBL 01', 'PAUSE 99', 'DSE 34', 'GTO 01', 'RTN',
              'LBL 20', 'STO 33', 'LBL 21', 'XEQ 10', 'DSE 33', 'GTO 21', 'RTN',
              'LBL 10', 'RCL 31', 'RCL 30', 'AGRAPH 32', '1', 'STO+ 30', 'RTN', 'END'])
    return P


def simulate(P):
    """Run BIGANT's drawing steps on a 400 x 240 bitmap (OR / XOR), to check the program."""
    scr = [[0] * 400 for _ in range(240)]
    R, mode, x = {}, 0, []
    i = 0
    while P[i] != 'RTN':
        l = P[i]
        if l.startswith('STO '):
            R[l[4:]] = x[-1]
        elif l == 'STO+ 30':
            R['30'] += x[-1]
        elif l.startswith('GRMOD'):
            mode = R[l[6:]]
        elif l == 'XEQ 20':
            for _ in range(x[-1]):
                c, y = R['30'], R['31']
                v = R['32']
                for b in range(63):
                    if v >> b & 1 and 0 <= y + b < 240 and 0 <= c < 400:
                        scr[y + b][c] = scr[y + b][c] ^ 1 if mode == 3 else 1
                R['30'] += 1
        elif l.endswith('#2'):
            x.append(int(l[:-2], 2))
        elif l.lstrip('-').isdigit():
            x.append(int(l))
        elif l == 'PAUSE 30':
            snap = [r[:] for r in scr]
        i += 1
    return snap, scr


def bigant_preview(path, P):
    from PIL import Image
    a, b = simulate(P)
    im = Image.new('L', (808, 240), 120)
    for off, s in ((0, a), (408, b)):
        for y in range(240):
            for x in range(400):
                im.putpixel((off + x, 239 - y), 20 if s[y][x] else 220)
    im.resize((1616, 480), Image.NEAREST).save(path)


if __name__ == '__main__':
    P = bigant()
    out = os.path.join(ROOT, 'extras', 'BIGANT.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    bigant_preview(os.path.join(ROOT, 'docs', 'BIGANT_preview.png'), P)
    print(out, len(P), 'lines; A', BW, 'x', BH, 'at', BX, BY)
