#!/usr/bin/env python3
"""atext_common.py - the text routines with ATEXT for the EXPERIMENTAL builds (NAVFULL_ATX and
the DM42 _ATX builds).

PTXS and the number printers keep the stack of the AGRAPH fonts: Z row of the base line, Y column,
X text or number; they return Y row, X next column.

  PTXS   the N03 trick of Didier (dlachieze): x<>(zyxt), 4, -, x<>y, ATEXT Z; then 4 back on the
         row, so the next text follows at the returned place. The only ATEXT step of a build.
  PINS PF1S PHMS PDMS PDTS PZNS   the number as text in one register (S) and one ATEXT: the
         first digit from a small table (LBL 48-57: "0" ... "9"), then whole numbers appended with
         alpha-IP and signs / separators with x->alpha (both checked on the C47, NATTEST), so a
         number costs a few steps, not a routine per character. Same text as the AGRAPH printers
         (padding with spaces as wide as a digit; the degrees end at the 4th place).
  PHLS   the horizontal line (AGRAPH / PIXEL), unchanged.
"""
import re


def sections(P):
    """{global label: its lines up to the next global label or the first glyph routine}."""
    out, cur = {}, None
    for l in P:
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m:
            cur = m.group(1); out[cur] = []
        elif re.fullmatch(r'LBL (\d+)', l) and int(l[4:]) >= 33 and cur not in (None, 'PTXS'):
            cur = None
        if cur:
            out[cur].append(l)
    return out


def printers(font, S):
    """font: the AGRAPH font program (for PHLS); S: the register for the text (e.g. '49')."""
    ap, xa = 'αIP %s' % S, 'x→α %s' % S
    P = ['LBL "PTXS"',
         'REM "Z row of the base line, Y column, X text -> ATEXT (the N03 trick of Didier): the row 4 lower, then back"',
         'LBL 01', '⇄ zyxt', '4', '-', 'X<>Y', 'ATEXT Z', 'X<>Y', '4', '+', 'X<>Y', 'RTN',
         'REM "LBL 02: end of a number printer: the text R%s at the row R31, column R30"' % S,
         'LBL 02', 'RCL 31', 'RCL 30', 'RCL %s' % S, 'GTO 01',
         'REM "LBL 05: Z row, Y column, X number -> R31, R30, R34"',
         'LBL 05', 'STO 34', 'R↓', 'STO 30', 'R↓', 'STO 31', 'RTN',
         'REM "LBL 06: the text starts with the digit X; LBL 07: two digits of X appended"',
         'LBL 06', '48', '+', 'STO 32', 'XEQ IND 32', 'STO %s' % S, 'RTN',
         'LBL 07', 'STO 33', '10', '÷', 'IP', ap, 'RCL 33', '10', 'MOD', ap, 'RTN',
         'REM "LBL 08: the text starts with the whole number X (0-999)"',
         'LBL 08', 'STO 35', '10', 'RCL 35', 'X<Y?', 'GTO 11', '100', 'RCL 35', 'X<Y?', 'GTO 12',
         'RCL 35', '100', '÷', 'IP', 'XEQ 06', 'RCL 35', '100', 'MOD', 'XEQ 07', 'RTN',
         'LBL 12', 'RCL 35', '10', '÷', 'IP', 'XEQ 06', 'RCL 35', '10', 'MOD', ap, 'RTN',
         'LBL 11', 'RCL 35', 'XEQ 06', 'RTN',
         # PINS: whole number, no padding
         'LBL "PINS"', 'XEQ 05', 'RCL 34', 'ABS', '0.5', '+', 'IP', 'XEQ 08', 'GTO 02',
         # PF1S: d.d
         'LBL "PF1S"', 'XEQ 05', 'RCL 34', 'ABS', '10', '×', '0.5', '+', 'IP', 'STO 36', '10', '÷', 'IP', 'XEQ 08',
         '"."', xa, 'RCL 36', '10', 'MOD', ap, 'GTO 02',
         # PHMS: hh:mm, or --:-- (no event)
         'LBL "PHMS"', 'XEQ 05', 'RCL 34', '98', 'X<Y?', 'GTO 13', 'RCL 34', '60', '×', '0.5', '+', 'IP', 'STO 36',
         '60', '÷', 'IP', '24', 'MOD', 'STO 35', '10', '÷', 'IP', 'XEQ 06', 'RCL 35', '10', 'MOD', ap,
         '":"', xa, 'RCL 36', '60', 'MOD', 'XEQ 07', 'GTO 02',
         'LBL 13', '"--:--"', 'STO %s' % S, 'GTO 02',
         # PDMS: pads (degrees < 100, < 10), sign, degrees, ' ', minutes, '.', tenths
         'LBL "PDMS"', 'XEQ 05', 'RCL 34', 'ABS', '600', '×', '0.5', '+', 'IP', 'STO 35', '600', '÷', 'IP', 'STO 36',
         '600', '×', 'STO- 35',
         '99', 'RCL 36', 'X>Y?', 'GTO 14', '" "', 'STO %s' % S, '9', 'RCL 36', 'X>Y?', 'GTO 15', '" "', xa,
         'LBL 15', 'XEQ 17', xa, 'GTO 16',
         'LBL 14', 'XEQ 17', 'STO %s' % S,
         'LBL 16', 'RCL 36', ap, '" "', xa, 'RCL 35', '10', '÷', 'IP', 'XEQ 07', '"."', xa, 'RCL 35', '10', 'MOD', ap, 'GTO 02',
         'LBL 17', 'RCL 34', 'X<0?', 'GTO 18', '" "', 'RTN', 'LBL 18', '"-"', 'RTN',
         # PDTS: DD-MM-YYYY
         'LBL "PDTS"', 'XEQ 05', 'RCL 34', 'J→ⅅℸ', 'R↓', 'STO 36', 'DAY', 'STO 35', 'RCL 36', 'MONTH', 'STO 34',
         'RCL 36', 'YEAR', 'STO 36', 'RCL 35', '10', '÷', 'IP', 'XEQ 06', 'RCL 35', '10', 'MOD', ap,
         '"-"', xa, 'RCL 34', 'XEQ 07', '"-"', xa, 'RCL 36', '100', '÷', 'IP', 'XEQ 07', 'RCL 36', '100', 'MOD', 'XEQ 07', 'GTO 02',
         # PZNS: ddd.d (360.0 -> 000.0)
         'LBL "PZNS"', 'XEQ 05', 'RCL 34', '10', '×', '0.5', '+', 'IP', 'STO 35', '3600', 'X≤Y?', 'XEQ 19',
         'RCL 35', '1000', '÷', 'IP', 'XEQ 06', 'RCL 35', '10', '÷', 'IP', '100', 'MOD', 'XEQ 07',
         '"."', xa, 'RCL 35', '10', 'MOD', ap, 'GTO 02',
         'LBL 19', '0', 'STO 35', 'RTN']
    h = [('GTO 25' if l == 'GTO 02' else l) for l in sections(font)['PHLS']]      # the line: AGRAPH / PIXEL
    P += h + ['LBL 25', 'WSIZE 64', 'RCL 31', 'RCL 30', 'RTN']
    for d in range(10):
        P += ['LBL %d' % (48 + d), '"%d"' % d, 'RTN']
    labs = [l for l in P if re.fullmatch(r'LBL \d+', l)]
    assert len(labs) == len(set(labs)), 'a local label twice in PTXS'
    return P + ['END']


def symbols(font, keep, name='PSYM'):
    """The AGRAPH glyphs of keep only (the symbols), as the text routine name."""
    import build_navfull as B
    i = font.index('LBL "PINS"')
    k = next(n for n in range(font.index('LBL "PHLS"'), len(font))
             if re.fullmatch(r'LBL (\d+)', font[n]) and int(font[n][4:]) >= 33)
    P = [('LBL "%s"' % name if l == 'LBL "PTXS"' else l) for l in font[:i] + font[k:]]
    return B.trim_font(P, set(keep))
