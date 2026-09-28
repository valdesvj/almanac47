#!/usr/bin/env python3
"""genbiga.py - BIGA: a big inverted 'A' in the middle of the C47 screen (AGRAPH + GRMOD XOR demo).

The 5x7 'A' is scaled x8 (40 x 56 pixels). A solid tile 48 x 62 is drawn first (GRMOD 0, OR),
then the 'A' is drawn over it with GRMOD 3 (XOR): the 'A' comes out white on black.
One AGRAPH draws one column of up to 62 pixels here (WSIZE 63: the literal must stay positive).

Writes extras/BIGA.txt and docs/BIGA_preview.png.
  python3 tools/generators/genbiga.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

A = ['0111111', '1001000', '1001000', '1001000', '0111111']   # columns, top bit first, bit 0 = bottom
S = 8                                  # scale
TILE_W, TILE_H, M = 48, 62, 4          # tile size, left/right margin
X0, Y0 = (400 - TILE_W) // 2, (240 - TILE_H) // 2
AX, AY = X0 + M, Y0 + (TILE_H - 7 * S) // 2


def scaled(col):
    """7-bit column -> 56-bit column (each bit repeated S times)."""
    return ''.join(b * S for b in col)


def program():
    tile = '1' * TILE_H + '#2'
    leg, mid = scaled(A[0]).lstrip('0') + '#2', scaled(A[1]) + '#2'
    return [
        'LBL "BIGA"', 'WSIZE 63', 'CLLCD',
        '0', 'STO 00', 'GRMOD 00',                       # mode 0: OR
        str(Y0), 'STO 31', str(X0), 'STO 30',
        tile, 'STO 32', str(TILE_W), 'XEQ 20',           # the black tile
        '3', 'STO 03', 'GRMOD 03',                       # mode 3: XOR
        str(AY), 'STO 31', str(AX), 'STO 30',
        leg, 'STO 32', str(S), 'XEQ 20',                 # left leg
        mid, 'STO 32', str(3 * S), 'XEQ 20',             # top bar and crossbar
        leg, 'STO 32', str(S), 'XEQ 20',                 # right leg
        '0', 'STO 00', 'GRMOD 00',                       # back to OR
        'WSIZE 64',
        '3', 'STO 34', 'LBL 01', 'PAUSE 99', 'DSE 34', 'GTO 01',
        'RTN',
        # LBL 20: draw column R32 X times, moving right
        'LBL 20', 'STO 33', 'LBL 21', 'XEQ 10', 'DSE 33', 'GTO 21', 'RTN',
        # LBL 10: one AGRAPH at row R31, column R30, then column + 1
        'LBL 10', 'RCL 31', 'RCL 30', 'AGRAPH 32', '1', 'STO+ 30', 'RTN',
        'END']


def preview(path):
    from PIL import Image
    px = [[0] * 400 for _ in range(240)]
    for x in range(X0, X0 + TILE_W):
        for y in range(Y0, Y0 + TILE_H):
            px[y][x] = 1
    for i, col in enumerate(A):
        bits = scaled(col)[::-1]                          # bit 0 first
        for k in range(S):
            x = AX + i * S + k
            for b, v in enumerate(bits):
                if v == '1':
                    px[AY + b][x] ^= 1
    im = Image.new('L', (400, 240), 220)
    for y in range(240):
        for x in range(400):
            if px[y][x]:
                im.putpixel((x, 239 - y), 20)
    im.resize((800, 480), Image.NEAREST).save(path)


if __name__ == '__main__':
    out = os.path.join(ROOT, 'extras', 'BIGA.txt')
    P = program()
    open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    preview(os.path.join(ROOT, 'docs', 'BIGA_preview.png'))
    print(out, len(P), 'lines; tile', X0, Y0, TILE_W, TILE_H, '; A at', AX, AY)
