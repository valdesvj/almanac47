#!/usr/bin/env python3
"""build_free42.py - Almanac 47 for Free42 on the SwissMicros DM42 / DM42n (stock firmware).

The same programs as NAVFULL_NOTBL (all views, no almanac tables) converted from the C47 to
Free42 3.3 with the DM42 extensions:

  graphics     3 STO "GrMod": PIXEL and AGRAPH on the whole 400 x 240 screen (origin 1,1 at
               the top left; the C47 counts rows from the bottom, from 0). PIXEL goes through
               PX, which converts the coordinates (negative = whole line, as on the C47).
  AGRAPH       Free42 draws the ALPHA register, one character = one column of 8 pixels,
               bit 0 at the top. The fonts (PTXS 12 px, PTXT 3 x 5) are rebuilt as strings of
               column bytes: one or two AGRAPH per character. Boxes and lines: FBX.
  GRMOD        flags 34 and 35 (AGRAPH control of the HP-42S): CF CF = OR, CF SF = set,
               SF CF = clear, SF SF = XOR - the same four modes as GRMOD 0 1 2 3.
  keys         GETKEY / GETKEYA, codes translated to the C47 codes (KM), so the views
               keep their key tests. KEY? r -> XEQ "KQ" (skips the next step on a key).
  PAUSE n      XEQ "Wn" (waits n tenths with TIME); PAUSE 0 (C47 screen update) dropped.
  TICKS        XEQ "TK" (tenths of a second from TIME).
  strings      a C47 string goes on the stack, a Free42 "..." goes into ALPHA: every
               string is XSTR "..."; + on strings is APPEND (AD, in the text programs).
  alpha        aLENG r -> RCL r LENGTH;  a->x r -> HEAD r C->N;  AVIEW r -> CLA ARCL r AVIEW
  matrices     STOSEQ -> STOEL J+;  RCLSEQ -> RCLEL J+
  TEXT (3)     the page goes into R50 ... (as ALMR on the C47) and is drawn with the small
               font in two columns; + back to the menu (Free42 has no register browser).
  ants         flag 97 instead of flag 47 (47 is a system flag on the HP-42S / Free42).
  size         NAV sets SIZE 100 (registers R00-R99).

  NAVFULL_F42_RLCD (python3 tools/build_free42.py rlcd): the screen as on the C47. Free42
  shows every AGRAPH and PIXEL at once (the drawing builds up on the screen); the C47 shows
  its screen only at a PAUSE, when it waits for a key and at the end. With 0 STO "RefLCD" the
  DM42 does not refresh the LCD; RF (-1 STO "RefLCD") shows it once: RF is called where the
  C47 program has PAUSE 0, before every key wait and at the start of every pause (Wn). At
  the end (0 on the menu) NAV sets RefLCD 7 again (the normal refresh).

  python3 tools/build_free42.py   -> build/free42/NAVFULL_F42.txt, NAVINIT_F42_FULL.txt,
                                     NAVINIT_F42_FAST.txt (+ .raw with tools/f42 if built)
"""
import os, sys, re, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(ROOT, 'python', 'native')]
import build_navfull as B
import gencache, gennav

OUT = os.path.join(ROOT, 'build', 'free42')
TEXTPROGS = ('STXT', 'ALMT')                # programs where + may join strings
ANTFLAG = 97
TFLAG = 91                             # flag 11 of the C47 programs (values from the tables)
WAITS = set()
RLCD = [False]                         # the RLCD build: the LCD shows the screen only where the C47 does


# ------------------------------------------------------------------ helpers (program F42)
def lib():
    L = ['LBL "F42"', 'RTN']
    # PX: PIXEL with C47 coordinates (Y row from the bottom, X column from 0; negative = line)
    L += ['LBL "PX"', 'FUNC 22', 'STO "PXX"', 'X<>Y', 'STO "PXY"', 'X<>Y', 'X<0?', 'GTO 01', '1', '+', 'GTO 02', 'LBL 01', '1', '-',
          'LBL 02', 'X<>Y', 'X<0?', 'GTO 03', '240', 'X<>Y', '-', 'GTO 04',
          'LBL 03', '+/-', '240', '-', 'LBL 04', 'X<>Y', 'PIXEL', 'RCL "PXY"', 'RCL "PXX"', 'RTN']
    # KM: Free42 GETKEY code -> C47 key code (the ones the views test: digits, 0, +, up, down)
    L += ['LBL "KM"', 'FUNC 11', 'STO "KK"',
          'RCL "KK"', '18', 'X=Y?', 'GTO 11', 'RCL "KK"', '23', 'X=Y?', 'GTO 12',
          'RCL "KK"', '37', 'X=Y?', 'GTO 13', 'RCL "KK"', '34', 'X=Y?', 'GTO 14',
          'RCL "KK"', '19', '-', 'STO "KK"', 'X<0?', 'GTO 15',
          'RCL "KK"', '5', 'MOD', '3', 'X≤Y?', 'GTO 15',
          'RCL "KK"', '5', '÷', 'IP', '3', 'X≤Y?', 'GTO 15',
          'RCL "KK"', '5', '÷', 'IP', '10', '×', '52', '+', 'RCL "KK"', '5', 'MOD', '+', 'RTN',
          'LBL 11', '51', 'RTN', 'LBL 12', '61', 'RTN', 'LBL 13', '85', 'RTN', 'LBL 14', '82', 'RTN',
          'LBL 15', '0', 'RTN']
    # KQ: KEY? 39 - a key: its code in R39 and the next step skipped; no key: next step
    L += ['LBL "KQ"', 'FUNC 00', 'GETKEYA', 'X=0?', 'RTNYES', 'XEQ "KM"', 'STO 39', 'RTNNO']
    # TK: TICKS (tenths of a second)
    if RLCD[0]:
        L += ['LBL "RF"', 'FUNC 00', '-1', 'STO "RefLCD"', 'RTN']   # show the screen once (RLCD build)
    L += ['LBL "TK"', 'FUNC 01', 'TIME', '→HR', '36000', '×', 'IP', 'RTN']
    # AD: + that joins strings (APPEND) or adds numbers
    L += ['LBL "AD"', 'FUNC 21', 'STR?', 'GTO 21', '+', 'RTN', 'LBL 21', 'APPEND', 'RTN']
    # FBX: box of BW columns x BH rows, bottom row BY, left column BX (C47 coordinates),
    # in the AGRAPH mode set by flags 34 / 35; bands of 8 rows, 44 columns per AGRAPH
    L += ['LBL "FBX"', 'FUNC 00', '241', 'RCL "BY"', '-', 'RCL "BH"', '-', 'STO "BT"',
          'RCL "BH"', 'STO "BR"',
          'LBL 30', 'RCL "BR"', 'X≤0?', 'RTN', '255', 'STO "BB"', '8', 'RCL "BR"', 'X<Y?', 'XEQ 31',
          'RCL "BW"', 'STO "BC"', 'RCL "BX"', '1', '+', 'STO "BK"',
          'LBL 32', 'RCL "BC"', 'X≤0?', 'GTO 33', '44', 'X>Y?', 'X<>Y', 'STO "BN"', 'CLA',
          'LBL 34', 'RCL "BB"', 'XTOA', 'DSE "BN"', 'GTO 34',
          'RCL "BT"', 'RCL "BK"', 'AGRAPH', '44', 'STO+ "BK"', '-44', 'STO+ "BC"', 'GTO 32',
          'LBL 33', '8', 'STO+ "BT"', '-8', 'STO+ "BR"', 'GTO 30',
          'LBL 31', '2', 'RCL "BR"', 'Y↑X', '1', '-', 'STO "BB"', 'RTN']
    # CLT: CLLCDxy - clear the rows from Y (C47 row) to the top
    L += ['LBL "CLT"', 'FUNC 22', 'STO "PXX"', 'X<>Y', 'STO "BY"', '240', 'RCL "BY"', '-', 'STO "BH"',
          '0', 'STO "BX"', '400', 'STO "BW"', 'SF 34', 'CF 35', 'XEQ "FBX"', 'CF 34',
          'RCL "BY"', 'RCL "PXX"', 'RTN']
    # TPG: the text page (R50 ... R79-1) with the small font, two columns of 13 lines
    L += ['LBL "TPG"', 'CLLCD', '50', 'STO "TL"', '0', 'STO "TK"',
          'LBL 40', 'RCL "TL"', 'RCL 79', 'X≤Y?', 'GTO 41',
          'RCL "TK"', '13', 'MOD', '16', '×', '228', 'X<>Y', '-',
          'RCL "TK"', '13', '÷', 'IP', '200', '×', '2', '+',
          'RCL IND "TL"', 'XEQ "PTXT"', '1', 'STO+ "TL"', 'STO+ "TK"', 'GTO 40',
          'LBL 41', '2', '4', 'XSTR "+ MENU"', 'XEQ "PTXT"', 'RTN']
    for n in sorted(WAITS):
        L += ['LBL "W%d"' % n, 'FUNC 00'] + (['XEQ "RF"'] if RLCD[0] else []) + ['XEQ "TK"', str(n), '+', 'STO "WTE"',
              'LBL 50', 'XEQ "TK"', 'RCL "WTE"', 'X>Y?', 'GTO 50', 'RTN']
    return L + ['END']


# ------------------------------------------------------------------ fonts
def glyph_columns(lines):
    """C47 font program -> {code: (columns {offset: pattern}, advance)} by running each glyph."""
    out, i = {}, 0
    while i < len(lines):
        m = re.fullmatch(r'LBL (\d+)', lines[i])
        if not (m and int(m.group(1)) >= 32):
            i += 1
            continue
        code, x, cols, reg, pend, adv, yoff = int(m.group(1)), 0, {}, 0, None, None, 0
        i += 1
        while lines[i] != 'RTN':
            l = lines[i]
            if l.endswith('#2'):
                pend = int(l[:-2], 2)
            elif l == 'STO 32':
                reg = pend
            elif l in ('R↓', 'RCL 31', 'RCL 30'):
                pass
            elif l.startswith('AGRAPH'):
                cols[x] = cols.get(x, 0) | reg
                x += 1
            elif re.fullmatch(r'-?\d+', l):
                pend = int(l)
            elif l == '+':
                x += pend
            elif l == '-':                    # RCL 31 n -: the glyph starts n rows below the base line
                yoff -= pend
            elif l.startswith('WSIZE'):
                pass
            elif l == 'STO 30':
                adv = x
            elif l == 'STO+ 30':
                adv = pend
            else:
                raise ValueError('glyph %d: %s' % (code, l))
            i += 1
        if yoff:
            YOFF[code] = yoff
        out[code] = (cols, adv)
        i += 1
    return out


YOFF = {}                              # glyphs drawn below the base line (PTXB '@', the Sun: 2 rows)


SPLIT = {33, 45, 60, 62, 92, 124}      # first bytes of the paste aliases (<= >= != -> <- |- \\ \\x)
XBYTE = {34, 181}                      # " (end of string) and the micro sign alias: added with XTOA


def alpha_literal(bs):
    """ALPHA = these bytes. Free42 Paste turns <= -> != |- \\ ... into single characters even
    inside strings, so the string is split after those bytes and continued with append (├)."""
    out, cur = [], []
    def flush():
        if not cur:
            return
        s = ''.join('€%02x' % b for b in cur)
        if out:
            out.append('├"%s"' % s)
        elif cur[0] >= 127:                 # first byte: 7 bits only (127 = append), so append
            out.extend(['CLA', '├"%s"' % s])
        else:
            out.append('"%s"' % s)
        del cur[:]
    for b in bs:
        if b in XBYTE:
            flush()
            out.extend(([] if out else ['CLA']) + [str(b), 'XTOA'])
            continue
        cur.append(b)
        if b in SPLIT:
            flush()
    flush()
    return out


def band_bytes(cols, n, H, top):
    """Bytes of the 8-row band starting at glyph row `top` (0 = top row of the glyph)."""
    out = []
    for x in range(n):
        p, b = cols.get(x, 0), 0
        for v in range(8):
            r = top + v                       # glyph row from the top
            if r < H and p >> (H - 1 - r) & 1:
                b |= 1 << v
        out.append(b)
    return out


def agraph_code(cols, H, ft, fb, colsrc):
    """AGRAPH steps for columns {offset: pattern} (C47 bits, bit 0 = bottom) of height H."""
    if not cols:
        return []
    x0, x1 = min(cols), max(cols)
    c = {x - x0: p for x, p in cols.items()}
    n = x1 - x0 + 1
    L = []
    for top, reg in ((0, ft), (8, fb)):
        if top >= H:
            break
        bs = band_bytes(c, n, H, top)
        if not any(bs):
            continue
        L += alpha_literal(bs) + [reg] + colsrc + ([str(x0 + 1), '+'] if x0 + 1 else []) + ['AGRAPH']
    return L


# characters of the text page that the small font lacks (columns, bit 4 = top row; advance)
HPCODE = {'°': 19}                     # C->N gives the HP-42S character code
EXTRA = {'PTXT': {19: ({0: 8, 1: 20, 2: 8}, 4), ord("'"): ({0: 24}, 2),
                  ord('%'): ({0: 18, 1: 4, 2: 9}, 4)}}


def font(name, keep, src=None):
    src = B.trim_font(src, keep) if src else B.read(name)       # PTXB: only the glyphs used ('@' is 12 px high)
    YOFF.clear()
    g = glyph_columns(src)
    sh = -min(YOFF.values(), default=0)                 # rows below the base line: patterns shifted up
    if sh:
        g = {c: ({x: p << (sh + YOFF.get(c, 0)) for x, p in cols.items()}, adv) for c, (cols, adv) in g.items()}
    hp = {v: k for k, v in HPCODE.items()}
    extra = {c: v for c, v in EXTRA.get(name, {}).items() if c not in g and hp.get(c, chr(c)) in keep}
    H = max(p.bit_length() for cols, _ in g.values() for p in cols.values())
    out, i = [], 0
    while i < len(src):
        l = src[i]
        m = re.fullmatch(r'LBL (\d+)', l)
        if m and int(m.group(1)) >= 32:
            code = int(m.group(1))
            j = src.index('RTN', i)
            if code == 32 or chr(code) in keep:
                cols, adv = g[code]
                out += ['LBL %d' % code] + agraph_code(cols, H, 'RCL "FT"', 'RCL "FB"', ['RCL 30'])
                out += [str(adv), 'STO+ 30', 'RTN']
            i = j + 1
            continue
        if name == 'PTXS' and l == 'LBL "PHLS"':           # horizontal line: FBX
            j = src.index('RTN', src.index('GTO 02', i)) if False else None
            out += ['LBL "PHLS"', 'STO 34', 'R↓', 'STO 30', 'R↓', 'STO 31',
                    'RCL 31', 'STO "BY"', 'RCL 30', 'STO "BX"', 'RCL 34', 'STO "BW"', '1', 'STO "BH"',
                    'XEQ "FBX"', 'RCL 31', 'RCL 30', 'RTN']
            k = i + 1                                           # skip to the first glyph after PHLS
            while not (re.fullmatch(r'LBL (\d+)', src[k]) and int(src[k][4:]) >= 32):
                k += 1
            i = k
            continue
        if l == 'END':
            for code, (cols, adv) in sorted(extra.items()):
                out += ['LBL %d' % code] + agraph_code(cols, H, 'RCL "FT"', 'RCL "FB"', ['RCL 30'])
                out += [str(adv), 'STO+ 30', 'RTN']
        out.append(l)
        if l == 'STO 31':                                   # the row: Free42 top rows of the bands
            out += [str(241 - H + sh), 'RCL 31', '-', 'STO "FT"', '8', '+', 'STO "FB"']
        i += 1
    return out, H


# ------------------------------------------------------------------ generic conversion
def grmod(L):
    out, i = [], 0
    while i < len(L):
        if (i + 2 < len(L) and re.fullmatch(r'[0-3]', L[i]) and L[i + 1].startswith('STO ')
                and L[i + 2] == 'GRMOD ' + L[i + 1][4:]):
            m = int(L[i])
            out += ['SF 34' if m & 2 else 'CF 34', 'SF 35' if m & 1 else 'CF 35']
            i += 3
            continue
        out.append(L[i])
        i += 1
    return out


def hcbox(L):
    """LBL 64 of the views: the XOR box behind a negative Hc -> FBX."""
    out, i = [], 0
    while i < len(L):
        if L[i] == 'LBL 64' and L[i + 1] == 'WSIZE 16':
            j = L.index('RTN', i)
            blk = L[i:j + 1]
            k = blk.index('11111111111111#2')
            assert blk[k + 1] == 'STO 32'
            s = blk.index('STO 33')
            row, col, cnt = blk[k + 2:s - 2], blk[s - 2], blk[s - 1]
            out += (['LBL 64'] + row + ['STO "BY"', col, 'STO "BX"', cnt, 'STO "BW"', '14', 'STO "BH"',
                                         'SF 34', 'SF 35', 'XEQ "FBX"', 'CF 34', 'CF 35', 'RTN'])
            i = j + 1
            continue
        out.append(L[i])
        i += 1
    return out


def conv(L, name):
    L = hcbox(grmod(L))
    out = []
    for l in L:
        if l.startswith('"') and '€' not in l:          # glyph column bytes (€xx) stay ALPHA strings
            out.append('XSTR ' + l)
        elif l == '+' and name in TEXTPROGS:
            out.append('XEQ "AD"')
        elif l == 'RAN#':
            out.append('RAN')
        elif l == 'CLSTK':
            out.append('CLST')
        elif l == 'SNAP':                             # key 9: no SNAP in Free42 - print the screen (PRLCD)
            out.append('PRLCD')
        elif l.startswith('WSIZE'):
            continue
        elif l == 'PIXEL':
            out.append('XEQ "PX"')
        elif l.startswith('PAUSE '):
            n = int(l[6:])
            if n <= 1 and RLCD[0]:
                out.append('XEQ "RF"')
            elif n > 1:
                WAITS.add(n)
                out.append('XEQ "W%d"' % n)
        elif l == 'KEY? 39':
            out.append('XEQ "KQ"')
        elif l == 'TICKS':
            out.append('XEQ "TK"')
        elif l == 'CLLCDxy':
            out.append('XEQ "CLT"')
        elif l.startswith('αLENG '):
            out += ['RCL ' + l[6:], 'LENGTH']
        elif l.startswith('α→𝑥 '):
            out += ['HEAD ' + l[4:], 'C→N']
        elif l.startswith('AVIEW '):
            out += ['CLA', 'ARCL ' + l[6:], 'AVIEW']
        elif l == 'STOSEQ':
            out += ['STOEL', 'J+']
        elif l == 'RCLSEQ':
            out += ['RCLEL', 'J+']
        elif l in ('FS? 47', 'SF 47', 'CF 47'):
            out.append(l[:-2] + str(ANTFLAG))
        elif l in ('FS? 11', 'FC? 11', 'SF 11', 'CF 11'):     # flag 11 (Moon/Sun from the tables): on the
            out.append(l[:-2] + str(TFLAG))                   # HP-42S 11 is auto-execution: flag 91 instead
        else:
            out.append(l)
    bad = [l for l in out if l.endswith('#2') or l.split(' ')[0] in (
        'GRMOD', 'SSIZE#', 'SSIZE8', 'SSIZE4', 'REGS', 'KEY?', 'x→α', 'αIP', 'J→ⅅℸ', 'DAY', 'MONTH',
        'YEAR', 'x→ⅅ', 'ⅅ→J', 'STOSEQ', 'RCLSEQ', 'PAUSE', 'TICKS', 'CLLCDxy') or l.startswith('AGRAPH ')]
    assert not bad, (name, bad[:5])
    return out


# ------------------------------------------------------------------ NAV
def seq(L, part, new):
    for i in range(len(L) - len(part) + 1):
        if L[i:i + len(part)] == part:
            return L[:i] + new + L[i + len(part):]
    raise ValueError('not found: %s' % part[:5])


def inputs():
    """LBL 20: the four INPUTs; LBL 21: Z JD (+ DH hours), Y lat, X lon (arithmetic, as the
    first versions: Free42 has no C47 date functions)."""
    L = gennav.OLD_INPUT.split('|')
    body = L[L.index('RCL "DATE"'):]
    k = body.index('RCL "LAT"')
    body = body[:k] + ['RCL "DH"', '24', '÷', 'STO+ 06'] + body[k:]
    hint = '"Y.MMDD H.MMSS D.MMm"'
    return (['LBL 20', 'CLA', hint, 'AVIEW'] + ['INPUT "%s"' % v for v in ('DATE', 'UTC', 'LAT', 'LON')]
            + ['RTN', 'LBL 21'] + body)


def box_free42():
    w, h, y0, x0 = 180, 30, 105, 110
    import c47fonts2
    tw = sum(c47fonts2.STD[ord(c)][0] for c in gennav.BUSY)
    def fbx(y, x, bw, bh):
        return [str(y), 'STO "BY"', str(x), 'STO "BX"', str(bw), 'STO "BW"', str(bh), 'STO "BH"', 'XEQ "FBX"']
    return (['LBL 52', 'SF 34', 'CF 35'] + fbx(y0, x0, w, h) + ['CF 34']
            + fbx(y0, x0, 2, h) + fbx(y0, x0 + w - 2, 2, h) + fbx(y0, x0, w, 2) + fbx(y0 + h - 2, x0, w, 2)
            + [str(y0 + 9), str(x0 + (w - tw) // 2), '"%s"' % gennav.BUSY, 'XEQ "PTXS"']
            + (['XEQ "RF"'] if RLCD[0] else []) + ['RTN'])


def nav():
    P = [str(x) for x in gennav.program(gennav.inputs(), gennav.ALL)]
    i = P.index('LBL 20')
    P = P[:i] + inputs() + ['END']
    P = seq(P, ['SSIZE#', 'STO "SSZ"', 'SSIZE8'], ['SIZE 100'])
    P = seq(P, ['XEQ 20', 'CLLCD'], ['XEQ 20', '3', 'STO "GrMod"'] + (['0', 'STO "RefLCD"'] if RLCD[0] else []) + ['CLLCD'])
    P = seq(P, ['LBL 08', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4', 'RTN'], ['LBL 08', 'RTN'])
    P = seq(P, ['LBL 09', 'CLLCD', 'XEQ 08', 'CLSTK', 'RTN'], ['LBL 09', 'CLLCD', '0', 'STO "GrMod"'] + (['7', 'STO "RefLCD"'] if RLCD[0] else []) + ['CLST', 'RTN'])
    P = seq(P, ['PAUSE 0', 'LBL 02', 'KEY? 39', 'GTO 02'], (['XEQ "RF"'] if RLCD[0] else []) + ['LBL 02', 'GETKEY', 'XEQ "KM"', 'STO 39'])
    # TEXT: the page into R50 ... (ALMR) and drawn with the small font; + back to the menu
    i = P.index('LBL 12')
    j = P.index('REGS', i)
    assert P[j + 1] == 'RTN'
    P = P[:i] + ['LBL 12', '50.078', 'STO 49', 'LBL 24', '" "', 'STO IND 49', 'ISG 49', 'GTO 24',
                 'XEQ 21', 'XEQ "ALMR"', 'XEQ "TPG"', 'XEQ "WPLS"', 'GTO 05'] + P[j + 2:]
    # LBL 41: the highlighted menu item (XOR box 170 x 16)
    i = P.index('LBL 41')
    j = P.index('RTN', i)
    P = P[:i] + ['LBL 41', 'RCL 37', 'STO "BY"', 'RCL 36', 'STO "BX"', str(gennav.BOX_W), 'STO "BW"',
                 str(gennav.BOX_H), 'STO "BH"', 'SF 34', 'SF 35', 'XEQ "FBX"', 'CF 34', 'CF 35', 'RTN'] + P[j + 1:]
    # LBL 52: the SINKING box; LBL 42: one ant; LBL 50 / 51: XOR on / off
    i = P.index('LBL 52')
    j = P.index('RTN', P.index('XEQ "PTXS"', i))
    P = P[:i] + box_free42() + P[j + 1:]
    i = P.index('LBL 42')
    j = P.index('RTN', i)
    ant = {}
    for x, p in enumerate(['11000000000000'] * 2 + ['00111100111111'] * 6 + ['11000000000000'] * 2):
        ant[x] = int(p, 2)
    P = P[:i] + (['LBL 42', 'STO "AX"', 'R↓', 'STO "AY"', '227', 'RCL "AY"', '-', 'STO "AT"', '8', '+', 'STO "AB"']
                 + agraph_code(ant, 14, 'RCL "AT"', 'RCL "AB"', ['RCL "AX"']) + ['RTN']) + P[j + 1:]
    P = seq(P, ['LBL 46', 'XEQ 47', 'PAUSE 1'], ['LBL 46', 'XEQ 47', 'XEQ "W1"'])     # the ants: 0.1 s each
    WAITS.add(1)
    P = seq(P, ['LBL 50', 'WSIZE 16', '3', 'STO 32', 'GRMOD 32', 'RTN'], ['LBL 50', 'SF 34', 'SF 35', 'RTN'])
    P = seq(P, ['LBL 51', '0', 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN'], ['LBL 51', 'CF 34', 'CF 35', 'RTN'])
    return P


def wpls():
    return ['LBL "WPLS"'] + (['XEQ "RF"'] if RLCD[0] else []) + ['LBL 01', 'GETKEY', 'XEQ "KM"', 'STO 39', 'RCL 39', '85', 'X=Y?', 'RTN',
            'RCL 39', '51', 'X=Y?', 'RTN', 'RCL 39', '61', 'X=Y?', 'RTN',
            'RCL 39', '54', 'X=Y?', 'PRLCD', 'GTO 01', 'END']          # key 9: print the screen (C47: SNAP)


def programs():
    with contextlib.redirect_stdout(io.StringIO()):
        progs = B.build()[3]
    progs['STXT'] = B.read('STXT')                        # without the C47 text / date functions
    progs['PTXS'] = B.read('PTXS')
    progs['PTXT'] = B.read('PTXT')
    p = dict(progs)                                       # with the almanac tables (TGET, flag 10)
    p['WPLS'] = wpls()
    return p


# ------------------------------------------------------------------ the screens of Oct 2026 (T21)
T21_VIEWS = ('ALMF', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')
FONTS = ('PTXS', 'PTXT', 'PTTY', 'PSYB', 'PSYS')


def raw_glyphs(name, glyphs, ws, gap=2, head=None):
    """A C47 font program in the plain form glyph_columns() reads (STO 32 / AGRAPH 32 per
    column): the text routine of glyphs47.program and one routine per glyph, bit 0 = base line."""
    sys.path.insert(0, os.path.join(HERE, 'generators', 'atext'))
    import glyphs47
    P = head or glyphs47.program(name, {}, ws=ws)[:-1]
    for code, rows in glyphs:
        P += ['LBL %d' % code, 'RCL 31', 'RCL 30']
        if rows is None:                                  # a blank of `gap` columns
            P += [str(gap), 'STO+ 30', 'RTN']
            continue
        cols, lead = glyphs47.columns(rows[1]), rows[0]
        if lead:
            P += [str(lead), '+']
        for v in cols:
            P += (['%s#2' % bin(v)[2:], 'STO 32', 'R↓', 'AGRAPH 32'] if v else ['1', '+'])
        P += [str(rows[2]), '+', 'STO 30', 'RTN']
    return P + ['END']


def psym(name, big):
    """PSYB (12 rows: the body symbols and the Moon phases) / PSYS (7 rows) of glyphs47."""
    sys.path.insert(0, os.path.join(HERE, 'generators', 'atext'))
    import glyphs47
    G = glyphs47.BIG if big else glyphs47.SMALL
    return raw_glyphs(name, [(ord(c), (0, r, 2)) for c, r in G.items()], 16 if big else 8)


def ptty():
    """PTTY (text) and PTNT (whole number) in the C47 tinyFont (GRFNT 10 on the C47) as an AGRAPH
    font: the program PTXT with its names changed and the tinyFont glyphs."""
    sys.path.insert(0, os.path.join(ROOT, 'python'))
    from tinyfont import TINY
    src = B.read('PTXT')
    k = next(i for i, l in enumerate(src) if re.fullmatch(r'LBL (\d+)', l) and int(l[4:]) >= 32)
    head = [('LBL "PTTY"' if l == 'LBL "PTXT"' else 'LBL "PTNT"' if l == 'LBL "PTNS"' else l) for l in src[:k]]
    tail = src[src.index('LBL "PTNS"'):]
    tail = [('LBL "PTNT"' if l == 'LBL "PTNS"' else l) for l in tail[:tail.index('END')]]
    head = [l for l in head if l != 'END']
    gl = []
    for c in sorted(TINY):
        if c < 32 or c > 0x7e:
            continue
        cb, cg, ca, ra, rg, rb, rows = TINY[c]
        if c == 32:
            gl.append((32, None))
            continue
        bits = [''.join('#' if v >> (cg - 1 - x) & 1 else '.' for x in range(cg)) for v in rows]
        gl.append((c, (cb, bits, ca)))
    P = raw_glyphs('PTTY', gl, 8, gap=6, head=head)[:-1]
    # the number routine after the glyphs, as in PTXT
    return P + tail + ['END']


def t21_programs():
    """The programs of NAVFULL with the views of NAVFULL_T21 (programs/atext/t21/, the sky cache
    swapped in) and the AGRAPH fonts: PTXS (the C47 status-bar font: the widths of GRFNT 21),
    PTTY / PTNT (tinyFont), PSYB / PSYS (glyphs47)."""
    p = programs()
    for n in T21_VIEWS:
        with open(os.path.join(ROOT, 'programs', 'atext', 't21', n + '.txt'), encoding='utf-8') as fh:
            p[n] = gencache.swap([l.rstrip('\n') for l in fh if l.strip()])
    p['PTTY'] = ptty()
    p['PSYB'] = psym('PSYB', True)
    p['PSYS'] = psym('PSYS', False)
    return p


def nav_t21():
    """NAV of Free42 with the top line of the menu at the columns of the T21 header."""
    sys.path.insert(0, os.path.join(HERE, 'generators', 'atext'))
    import genviews_atx as V
    V.mode(True, 't21')
    T = V.top_x()
    V.mode()
    P = nav()
    s = '\n' + '\n'.join(P) + '\n'
    for a, b in (((206, 80), (206, T['time'])), ((206, 116, 'XSTR "UT"'), (206, T['UT'], 'XSTR "UT"')),
                 ((206, 116, '"UT"'), (206, T['UT'], '"UT"')),
                 ((206, 150, '"DR"'), (206, T['DR'], '"DR"')), ((206, 174), (206, T['N'])), ((206, 176), (206, T['lat'])),
                 ((206, 244), (206, T['E'])), ((206, 246), (206, T['lon']))):
        a = '\n' + '\n'.join(map(str, a)) + '\n'; b = '\n' + '\n'.join(map(str, b)) + '\n'
        s = s.replace(a, b)
    return s.strip('\n').split('\n')


def nav_little():
    """NAVLITTLE (the DM42 NAVLITTLE, was NAV1_DM42): no menu - the inputs, then the ALMANAC
    view; up / down one hour, + ends. Sun and stars only, 5 x 7 font, no box, no ants."""
    import build_dm42 as D
    P = D.no_box(D.nav1_program(gennav.inputs()))
    i = P.index('LBL 20')
    P = P[:i] + inputs() + ['END']
    P = seq(P, ['SSIZE#', 'STO "SSZ"', 'SSIZE8'], ['SIZE 100'])
    P = seq(P, ['XEQ 20', 'CLLCD'], ['XEQ 20', '3', 'STO "GrMod"'] + (['0', 'STO "RefLCD"'] if RLCD[0] else []) + ['CLLCD'])
    P = seq(P, ['CLLCD', 'RCL "SSZ"', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN'],
            ['CLLCD', '0', 'STO "GrMod"'] + (['7', 'STO "RefLCD"'] if RLCD[0] else []) + ['CLST', 'RTN'])
    return P


def assemble(N, p, big_src=None):
    """NAV N + the programs it needs (converted) + F42; returns (long names, short names, map)."""
    keep = list(B.KEEP) + ['PTTY', 'PSYB', 'PSYS']
    need = B.closure(p, [c for c in B.calls(N) if c != 'INIT'] + (['ALMR'] if 'XEQ "ALMR"' in N else [])
                     + (['PTXT'] if 'XEQ "TPG"' in N else []))       # the text page uses PTXT
    chars = set(''.join(B.strings(N)) + ''.join(''.join(B.strings(p[n])) for n in need) + '0123456789-.: %')
    progs = {}
    for n in keep:
        if n not in need:
            continue
        if n in FONTS:
            src = big_src if n == 'PTXS' and big_src else p[n] if n in ('PTTY', 'PSYB', 'PSYS') else None
            progs[n] = conv(font(n, chars, src)[0], n)
        else:
            progs[n] = conv(p[n], n)
    L = conv(N, 'NAV') + [l for n in keep if n in progs for l in progs[n]]
    lb = lib()
    if 'XEQ "TPG"' not in L:                               # the text page (small font) only with TEXT
        i = lb.index('LBL "TPG"')
        j = lb.index('RTN', lb.index('XSTR "+ MENU"', i))
        lb = lb[:i] + lb[j + 1:]
    return L + lb


def little_programs():
    import build_dm42 as D
    with contextlib.redirect_stdout(io.StringIO()):
        p = D.nav1_programs(D.programs())
    p['STXT'] = B.read('STXT')                            # without the C47 text / date functions
    p['WPLS'] = wpls()
    return p


DEV = os.path.join(OUT, 'dev')
SRC = os.path.join(DEV, 'src')


def save(name, L, d, mapname):
    """long names to dev/src/, short labels (fixed map tools/labels/<mapname>.map) to d."""
    B.write(os.path.join(SRC, name + '.txt'), L)
    m = B.fixed_map(mapname, L, keep=('NAV',))
    B.write(os.path.join(d, name + '.txt'), B.rename_keep(L, m, ('NAV',)))
    return m


def build(rlcd=False, little=False):
    RLCD[0] = rlcd
    WAITS.clear()
    if little:
        import build_dm42 as D
        L = assemble(nav_little(), little_programs(), D.ptxb_as_ptxs())
        m = save('NAVLITTLE', L, OUT, 'F42_NAVLITTLE')
        with open(os.path.join(OUT, 'NAVLITTLE_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('NAVLITTLE (Free42) - program labels (NAV keeps its name; INIT is NAVINIT_LITTLE)\n\n')
            fh.write('\n'.join('%s  %s' % (v, k) for k, v in m.items()) + '\n')
        init = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'), encoding='utf-8') if l.strip()]
        B.write(os.path.join(OUT, 'NAVINIT_LITTLE.txt'), conv(init, 'INIT'))
        return L
    full = assemble(nav_t21(), t21_programs())         # the screens of Oct 2026 (as NAVFULL_T21)
    if not rlcd:                                 # the screen builds up as it is drawn: dev/
        save('NAVFULL_DRAW', full, DEV, 'F42_NAVFULL_DRAW')
        return full
    m = save('NAVFULL', full, OUT, 'F42_NAVFULL')
    with open(os.path.join(OUT, 'NAVFULL_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVFULL (Free42) - program labels (NAV keeps its name)\n\n')
        fh.write('\n'.join('%s  %s' % (v, k) for k, v in m.items()) + '\n')
    # INIT: the same matrix builders, strings with XSTR
    for kind in ('FULL', 'FAST'):
        L = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'build', 'NAVINIT_%s.txt' % kind), encoding='utf-8') if l.strip()]
        B.write(os.path.join(OUT, 'NAVINIT_%s.txt' % kind), conv(L, 'INIT'))
    # the almanac tables: TBL_1 (1 year), TBL_5 (5 years) - the same program, strings with XSTR
    for name in ('TBL_1', 'TBL_5'):
        src = os.path.join(ROOT, 'build', name + '.txt')
        if os.path.exists(src):
            L = [l.rstrip('\n') for l in open(src, encoding='utf-8') if l.strip()]
            B.write(os.path.join(OUT, name + '.txt'), conv(L, 'TBL'))
    return full


def raw_files():
    """The .raw files (Free42 program files) with tools/f42/f42run: paste the listing, export."""
    import subprocess
    f42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
    if not os.path.exists(f42):
        print('no tools/f42/f42run (sh tools/f42/setup.sh): .raw files not written')
        return
    for name in ('NAVFULL', 'NAVLITTLE', 'NAVINIT_FULL', 'NAVINIT_FAST', 'NAVINIT_LITTLE', 'TBL_1', 'TBL_5', 'dev/NAVFULL_DRAW'):
        txt = os.path.join(OUT, name + '.txt')
        r = subprocess.run([f42], input='paste %s\nexport %s\n' % (txt, txt[:-4] + '.raw'), text=True,
                           capture_output=True, timeout=300)
        print(r.stdout.strip().split('\n')[-1])


if __name__ == '__main__':
    for rl, li, name in ((True, False, 'NAVFULL'), (False, False, 'dev/NAVFULL_DRAW'), (True, True, 'NAVLITTLE')):
        L = build(rl, li)
        print('%-17s %6d lines %7d bytes; waits %s' % (name, len(L), sum(len(l) + 1 for l in L), sorted(WAITS)))
    raw_files()
