#!/usr/bin/env python3
"""annotate_demo.py - extras/DEMOALM_rem.txt: DEMOALM with REM comments on every part.

Same program steps as extras/DEMOALM.txt (tools/build_demo.py); REM lines only explain:
  - DEMO, DALA, DALP: what each drawing call puts on the screen (row, column, text / value)
  - PTXS, PTXT and their PIXEL copies PTXP, PTTP: the comments of programs_rem/PTXB.txt and
    PTXT.txt carried over line by line, and a picture of every character (# = lit dot)
  - LBL 99, the dot-by-dot PIXEL routine, line by line

  python3 tools/annotate_demo.py      -> extras/DEMOALM_rem.txt
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'python')]
import build_demo
from c47fonts2 import STD
from c47font import SMALL


def R(t):
    return 'REM "%s"' % t.replace('"', "'")


# ------------------------------------------------------------------ program headers
HEAD = {
 'DEMO': ["DEMO - menu of the AGRAPH / PIXEL demo (no navigation calculations)",
          "1 AGRAPH: DALA draws the almanac page with PTXS/PTXT (one AGRAPH per glyph column)",
          "2 PIXEL : DALP draws the same page with PTXP/PTTP (one PIXEL per lit dot)",
          "0 or EXIT ends. R43 = menu text, R44 = the choice"],
 'DALA': ["DALA - the almanac page (ALMF) with fixed sample data, drawn with AGRAPH fonts",
          "Sample: Dubai N 25 12 E 55 18, 02-10-2026 18:00 UT (values as calculated by ALMF)",
          "Every call: row (Z, 0 = bottom), column (Y, 0 = left), text or value (X), XEQ font routine",
          "Rows are the base line of the text; big font capitals are 12 px high, line pitch 14",
          "R41 = TICKS at the start, then the time in seconds; R42 = pause counter"],
 'DALP': ["DALP - the same page, same calls, but every font routine is the PIXEL copy:",
          "PTXP/PTTP draw each glyph column dot by dot with PIXEL (LBL 99 in each font)",
          "Compare the time on the bottom line with option 1 (DALA)"],
 'PTXS': ["PTXS - text in the C47 status-bar font (standardFont), bold capitals 12 px, narrow",
          "PTXS: Z = y, Y = x, X = string -> Y = y, X = next x  (calls can be chained)",
          "PINS integer | PF1S one decimal | PHMS hh:mm (98 or more -> --:--) | PDMS sign ddd mm.m",
          "PZNS ddd.d | PDTS JD -> DD-MM-YYYY | PHLS horizontal line (X = length)",
          "All number routines: Z = y, Y = x, X = value -> Y = y, X = next x",
          "Glyphs = AGRAPH columns with WSIZE 14 (13 rows + sign bit); WSIZE 64 again at the end",
          "Glyph bitmaps from the C43/C47 firmware standardFont: GPL-3.0 (LICENSE-PTXS.txt)",
          "Only the characters this page uses are kept (trimmed by build_navfull.trim_font)",
          "REGS: R30 x, R31 y, R32 code / column bits, R33 string, R34-R36 number work",
          "HOW A GLYPH IS DRAWN (AGRAPH):",
          "  AGRAPH 32 draws one column: bit 0 of the short integer in R32 at (x, y), bit 1 at y+1 ...",
          "  up to WSIZE bits, then adds 1 to X. Each glyph: RCL 31 (y), RCL 30 (x), then per column",
          "  <bits>#2  STO 32  R-down  AGRAPH 32   (binary written top row first).",
          "  Empty columns are skipped with  n + ; at the end  n + STO 30  stores the next x.",
          "WHY WSIZE 14: 12-13 rows per column plus the sign bit of a short integer."],
 'PTXP': ["PTXP - PTXS with every AGRAPH replaced by XEQ 99 (dot by dot with PIXEL)",
          "Same calls and names with P: PTXP PINP PF1P PHMP PDMP PDTP PZNP PHLP",
          "Each glyph column is an ordinary number (bit 0 = bottom row) instead of a binary literal",
          "LBL 99 at the end tests the bits one by one and draws one PIXEL per lit dot"],
 'PTTP': ["PTTP - PTXT with every AGRAPH replaced by XEQ 99 (dot by dot with PIXEL)",
          "Same calls with P: PTTP, PTNP (integer), PT1P (one decimal)"],
}
NUMHEAD = {  # headers for the number routines of the P copies (the PTXS ones come from PTXB's REMs)
 'PINP': "PINP: rounded integer 0-999 (PIXEL copy of PINS)", 'PF1P': "PF1P: one decimal (PIXEL copy of PF1S)",
 'PHMP': "PHMP: hh:mm (PIXEL copy of PHMS)", 'PDMP': "PDMP: sign ddd mm.m (PIXEL copy of PDMS)",
 'PDTP': "PDTP: JD -> DD-MM-YYYY (PIXEL copy of PDTS)", 'PZNP': "PZNP: ddd.d (PIXEL copy of PZNS)",
 'PHLP': "PHLP: horizontal line (PIXEL copy of PHLS)", 'PTNP': "PTNP: integer (PIXEL copy of PTNS)",
 'PT1P': "PT1P: one decimal (PIXEL copy of PT1)"}

LBL99 = {
 'LBL 99': ["LBL 99 - one glyph column dot by dot (replaces AGRAPH 32)",
            "IN : X = column x, Y = row y (base line), R32 = the column's bits, bit 0 = row y",
            "OUT: X = x + 1, Y = y  (exactly what AGRAPH leaves), R37-R40 used"],
 'STO 38': ["R38 = x"], 'RCL 32': ["R37 = bits still to draw"],
 'LBL 98': ["loop over the bits, lowest first"],
 'X=0?': ["no bits left -> done"], '2': ["lowest bit: bits MOD 2"],
 'RCL 39': ["bit is 1: one PIXEL at row R39, column R38"],
 'LBL 96': ["drop the lowest bit: bits / 2, integer part"],
 '1': ["next row up"], 'LBL 97': ["done: Y = y (kept in R40), X = x + 1"],
}

FN_TEXT = {'PDTS': 'date from JD', 'PDTP': 'date from JD', 'PHMS': 'hh:mm from hours', 'PHMP': 'hh:mm from hours',
           'PDMS': 'ddd mm.m', 'PDMP': 'ddd mm.m', 'PZNS': 'azimuth ddd.d', 'PZNP': 'azimuth ddd.d',
           'PINS': 'whole number', 'PINP': 'whole number', 'PF1S': 'one decimal', 'PF1P': 'one decimal',
           'PHLS': 'horizontal line', 'PHLP': 'horizontal line', 'PT1': 'one decimal (small)', 'PT1P': 'one decimal (small)'}
SYMBOL = {'@': 'Sun symbol', '(': 'Moon symbol', '*': 'star symbol', '<': 'Venus symbol', '>': 'Mars symbol',
          '=': 'Jupiter symbol', '?': 'Saturn symbol'}


def shown(fn, v):
    """What a number routine prints, for the comment."""
    import c47screen as S
    try:
        x = float(v)
    except ValueError:
        return ''
    f = fn[:3]
    if f == 'PDM':
        t = int(abs(x) * 600 + 0.5); d = t // 600; t -= d * 600
        return ' -> "%s%d %02d.%d"' % ('-' if x < 0 else '', d, t // 10, t % 10)
    if f == 'PHM':
        if x > 98:
            return ' -> "--:--"'
        m = int(x * 60 + 0.5)
        return ' -> "%02d:%02d"' % (m // 60 % 24, m % 60)
    if f == 'PDT':
        d, mo, y = S.jd_to_date(x)
        return ' -> "%02d-%02d-%04d"' % (d, mo, y)
    if f == 'PZN':
        return ' -> "%05.1f"' % (int(x * 10 + 0.5) / 10)
    if f == 'PIN':
        return ' -> "%d"' % int(abs(x) + 0.5)
    if fn.startswith('PF1') or fn.startswith('PT1'):
        return ' -> "%.1f"' % (int(abs(x) * 10 + 0.5) / 10)
    if f == 'PHL':
        return ' px'
    return ''


def section(y):
    return {226: "top line: date, UT, DR position, T/S letter", 207: "column titles", 193: "ARIES row (GHA only)"}.get(y)


# ------------------------------------------------------------------ carried-over REMs
def rem_source(name):
    """programs_rem/<name>.txt -> list of (rems before, code line)."""
    out, rems = [], []
    for l in open(os.path.join(ROOT, 'programs_rem', name + '.txt'), encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        if l.startswith('REM '):
            rems.append(l)
        else:
            out.append((rems, l)); rems = []
    return out


def carry(prog, src, subst, head, glyphs, nrows, pixel, keep_head=True):
    """Comment one font program: header, carried REMs (aligned on equal code lines), glyph pictures."""
    out = [prog[0]] + [R(t) for t in head]
    k = 1                                                    # source position (skip its header REMs)
    in_glyphs = False
    for l in prog[1:]:
        m = re.fullmatch(r'LBL (\d+)', l)
        if m and int(m.group(1)) in glyphs and l != 'LBL 32' and not in_glyphs and int(m.group(1)) >= 33:
            in_glyphs = True
            out.append(R("---- GLYPHS: one label per character code, pictures: # = lit dot, top row first ----"))
            if pixel:
                out.append(R("each number below is one column (bit 0 = base line); XEQ 99 draws its dots with PIXEL"))
            else:
                out.append(R("each binary literal is one column (bit 0 = base line); AGRAPH 32 draws it in one call"))
        if m and in_glyphs and int(m.group(1)) in glyphs:
            code = int(m.group(1)); adv, _, cols = glyphs[code]
            ch = chr(code)
            out.append(l)
            out.append(R("character '%s' (code %d)%s, %d px wide" % (ch, code, ' = ' + SYMBOL[ch] if ch in SYMBOL else '', adv)))
            d = dict(cols)
            w = (max(d) + 1) if d else 0
            top = max((v.bit_length() for v in d.values()), default=0)
            for r in range(max(top, nrows) - 1, -1, -1):
                out.append(R('  ' + ''.join('#' if d.get(c, 0) >> r & 1 else '.' for c in range(w))))
            continue
        if not in_glyphs:
            key = l
            for a, b in subst:
                key = key.replace(b, a)                         # back to the source's names
            for j in range(k, min(k + 6, len(src))):
                if src[j][1] == key:
                    for r in (src[j][0] if keep_head or j > 1 else []):
                        t = r
                        for a, b in subst:
                            t = t.replace(a, b)
                        out.append(t)
                    k = j + 1
                    break
            g = re.fullmatch(r'LBL "(\w+)"', l)
            if g and g.group(1) in NUMHEAD:
                out.append(l); out.append(R(NUMHEAD[g.group(1)])); continue
        if l == 'LBL 99':
            out += [R('-' * 60)] + [R(t) for t in LBL99['LBL 99']] + [l]
            in_glyphs = False
            continue
        out.append(l)
    return out


L99 = {1: "R38 = x (the column)", 2: "X = y now", 3: "R40 = y, kept for the end", 4: "R39 = y, the row that moves up",
       5: "R37 = the column's bits still to draw", 7: "loop over the bits, lowest first",
       9: "no bits left -> this column is done", 11: "lowest bit = bits MOD 2", 13: "bit 0 -> no dot here, skip",
       15: "bit 1 -> one PIXEL at row R39, column R38", 18: "drop the lowest bit: bits / 2, integer part",
       24: "next row up", 26: "and test the next bit",
       27: "done: Y = y (R40), X = x + 1 - what AGRAPH leaves, so the glyph code goes on unchanged"}


def comment_lbl99(lines):
    """Line comments inside LBL 99, by position."""
    out, pos = [], None
    for l in lines:
        if l == 'LBL 99':
            pos = 0
        elif pos is not None:
            pos += 1
            if l == 'END':
                pos = None
            elif pos in L99:
                out.append(R(L99[pos]))
        out.append(l)
    return out


def comment_page(prog):
    """DALA / DALP: a comment for every drawing call."""
    out = [prog[0]] + [R(t) for t in HEAD[prog[0].split('"')[1]]]
    last_sec = None
    body = prog[1:]
    j = 0
    while j < len(body):
        l = body[j]
        if l == 'TICKS' and j == 0:
            out += [R("start the clock: TICKS (1/10 s) -> R41, clear the screen"), l]; j += 1; continue
        m = re.fullmatch(r'XEQ "(\w+)"', l)
        if l == 'PIXEL' or m:
            # the call's arguments are the lines just emitted: find them
            n = 2 if l == 'PIXEL' else 3
            args = out[-n:]
            del out[-n:]
            try:
                y = int(float(args[0]))
            except ValueError:
                y = None
            sec = section(y) if y is not None else None
            if y is not None and 67 <= y < 193:
                sec = "table rows: symbol, star number, name, GHA, DEC, HC, ZN (pitch 14 px)"
            elif y is not None and y < 67:
                sec = "Sun and Moon lines under the table"
            elif y is not None and y < 0:
                sec = None
            if sec and sec != last_sec:
                out.append(R('---- ' + sec + ' ----')); last_sec = sec
            if l == 'PIXEL':
                yy, xx = args
                if yy.startswith('-'):
                    out.append(R("horizontal line across the screen at row %s (PIXEL with negative row)" % yy[1:]))
                else:
                    out.append(R("one dot at row %s, column %s" % (yy, xx)))
            else:
                fn = m.group(1); yy, xx, v = args
                if fn in ('PTXS', 'PTXP', 'PTXT', 'PTTP'):
                    s = v.strip('"')
                    what = SYMBOL.get(s, 'text "%s"' % s) if len(s) == 1 else 'text "%s"' % s
                    out.append(R("row %s, column %s: %s%s" % (yy, xx, what, ' (small font)' if fn in ('PTXT', 'PTTP') else '')))
                else:
                    vv = ('%.3f' % float(v)).rstrip('0').rstrip('.') if re.fullmatch(r'-?[\d.]+(E-?\d+)?', v) else v
                    out.append(R("row %s, column %s: %s %s%s" % (yy, xx, FN_TEXT.get(fn, fn), vv, shown(fn, v))))
            out += args + [l]
            j += 1
            continue
        if l == 'TICKS' and j > 0:
            out += [R("---- bottom line: time taken and a note ----"),
                    R("TICKS now - R41 = elapsed 1/10 s, / 10 = seconds -> R41"), l]
            j += 1
            k = body.index('3', j)                       # up to the pause counter
            notes = {0: "row 1, column 100 (small font): the method name, then the seconds and a note"}
            for n, t in enumerate(body[j:k]):
                if t.startswith('XEQ "PTXT"') or t.startswith('XEQ "PTTP"'):
                    out.append(R("print the text above (small font); it returns Y = row, X = next column"))
                if t.startswith('XEQ "PT1'):
                    out.append(R("print R41 = seconds with one decimal (small font)"))
                if t == '1' and n > 0 and body[j + n + 1] == '100':
                    out.append(R(notes[0]))
                out.append(t)
            j = k
            continue
        if l == 'LBL 01':
            out += [R("keep the page on the screen: 3 x PAUSE 99 (about 30 s), R/S or EXIT ends"), l]; j += 1; continue
        out.append(l); j += 1
    # the bottom-line calls use values from the stack: their comments above say "text"; fine
    return out


def split(prog):
    progs, cur = [], []
    for l in prog:
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def main():
    out_plain, prog, _, mapping, renamed = build_demo.build()
    parts = split(prog)
    src_b, src_t = rem_source('PTXB'), rem_source('PTXT')
    SB = [('PTXB', 'PTXS'), ('PINB', 'PINS'), ('"PF1"', '"PF1S"'), ('"PHM"', '"PHMS"'), ('"PDM"', '"PDMS"'),
          ('"PDAT"', '"PDTS"'), ('"PZN"', '"PZNS"'), ('"PHL"', '"PHLS"'), ('WSIZE 8', 'WSIZE 14'), ('6 STO+ 30', '7 STO+ 30'),
          ('PF1 ', 'PF1S '), ('PHM ', 'PHMS '), ('PDM ', 'PDMS '), ('PZN ', 'PZNS '), ('PDAT ', 'PDTS '), ('PHL:', 'PHLS:')]
    SBP = [(a, b.replace('PTXS', 'PTXP').replace('PINS', 'PINP').replace('PF1S', 'PF1P').replace('PHMS', 'PHMP')
            .replace('PDMS', 'PDMP').replace('PDTS', 'PDTP').replace('PZNS', 'PZNP').replace('PHLS', 'PHLP')) for a, b in SB]
    ST = [('WSIZE 8', 'WSIZE 8')]
    SBP = SBP + [('with AGRAPH', 'with XEQ 99 (PIXEL)')]
    STP = [('PTXT', 'PTTP'), ('PTNS', 'PTNP'), ('"PT1"', '"PT1P"'), ('with AGRAPH', 'with XEQ 99 (PIXEL)')]
    res = []
    for p in parts:
        name = p[0].split('"')[1] if p[0].startswith('LBL "') else ''
        if name == 'DEMO':
            res += [p[0]] + [R(t) for t in HEAD['DEMO']] + p[1:]
        elif name in ('DALA', 'DALP'):
            res += comment_page(p)
        elif name == 'PTXS':
            res += carry(p, src_b, SB, HEAD['PTXS'], STD, 12, False, keep_head=False)
        elif name == 'PTXT':
            res += carry(p, src_t, ST, [], SMALL, 5, False)
        elif name == 'PTXP':
            res += comment_lbl99(carry(p, src_b, SBP, HEAD['PTXP'], STD, 12, True, keep_head=False))
        elif name == 'PTTP':
            res += comment_lbl99(carry(p, src_t, STP, HEAD['PTTP'], SMALL, 5, True, keep_head=False))
        else:
            res += p
    # PTXT keeps its own header REMs from programs_rem/PTXT.txt
    code = [l for l in res if not l.startswith('REM ')]
    assert code == prog, 'comments changed the program'
    # labels: N01 ... (only DEMO keeps its name); after every global label say what it is
    import build_navfull as B
    res2 = []
    for l in B.rename_keep(res, mapping, 'DEMO') if False else res:
        g = re.fullmatch(r'(LBL|XEQ|GTO) "(.+)"', l)
        if g and g.group(2) in mapping:
            res2.append('%s "%s"' % (g.group(1), mapping[g.group(2)]))
            if g.group(1) == 'LBL':
                res2.append(R('%s = %s - %s' % (mapping[g.group(2)], g.group(2), build_demo.LABEL_TEXT.get(g.group(2), ''))))
        elif g and g.group(1) in ('XEQ', 'GTO') and g.group(2) != 'DEMO':
            raise ValueError(l)
        else:
            res2.append(l)
            if l == 'LBL "DEMO"':
                res2.append(R('Labels: only DEMO keeps its name; N01 ... are the page and font routines'))
                res2.append(R('(table: DEMOALM_LABELS.txt). FONT = one of the text-drawing routines.'))
        # comments that name routines: add the new label in brackets
    res = []
    names = sorted(mapping, key=len, reverse=True)
    for l in res2:
        if l.startswith('REM ') and not re.match(r'REM "N\d\d = ', l):
            for n in names:
                l = re.sub(r'(?<![A-Z0-9])%s(?![A-Z0-9])' % n, '%s (%s)' % (n, mapping[n]), l, count=1) if n in l and '(%s)' % mapping[n] not in l else l
        res.append(l)
    out = os.path.join(ROOT, 'extras', 'DEMOALM_rem.txt')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(res) + '\n')
    code = [l for l in res if not l.startswith('REM ')]
    assert code == renamed, 'comments changed the program'
    print(out, len(res), 'lines (%d REM)' % (len(res) - len(code)))


if __name__ == '__main__':
    main()
