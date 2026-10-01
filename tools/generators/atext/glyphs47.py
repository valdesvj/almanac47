"""glyphs47.py - EXPERIMENTAL body symbols for the ATEXT builds, two sizes drawn with AGRAPH:
BIG (12 rows, the cap height of the standard / compressed font 20 / 21: the tables) and
SMALL (7 rows, the tinyFont: the charts). Codes as PSYM: @ Sun, ( Moon, * star,
< Venus, > Mars, = Jupiter, ? Saturn; & the ant (BIG only): the 'A' of our
original 5 x 7 font (PTXB) inverted in its cell and doubled, 10 x 14, the ant of NAV (LBL 42) and BIGA. Rows top to bottom, '#' = pixel; the last row is the base line."""

BIG = {
    '@': ['....####....',
          '..########..',
          '.###....###.',
          '.##......##.',
          '##...##...##',
          '##..####..##',
          '##..####..##',
          '##...##...##',
          '.##......##.',
          '.###....###.',
          '..########..',
          '....####....'],
    '(': ['....####',
          '..####..',
          '.####...',
          '.###....',
          '####....',
          '###.....',
          '###.....',
          '####....',
          '.###....',
          '.####...',
          '..####..',
          '....####'],
    '*': ['.....##.....',
          '.....##.....',
          '....####....',
          '....####....',
          '############',
          '.##########.',
          '...######...',
          '...######...',
          '..########..',
          '..###..###..',
          '.###....###.',
          '.##......##.'],
    '<': ['..####..',
          '.##..##.',
          '##....##',
          '##....##',
          '.##..##.',
          '..####..',
          '...##...',
          '...##...',
          '.######.',
          '.######.',
          '...##...',
          '...##...'],    # Venus
    '>': ['.....#####',
          '.......###',
          '......##.#',
          '.....##..#',
          '..####....',
          '.##..##...',
          '##....##..',
          '##....##..',
          '##....##..',
          '##....##..',
          '.##..##...',
          '..####....'],    # Mars
    '=': ['.##.....##.',
          '##.##...##.',
          '....##..##.',
          '....##..##.',
          '...##...##.',
          '..##....##.',
          '.##.....##.',
          '###########',
          '###########',
          '........##.',
          '........##.',
          '........##.'],    # Jupiter
    '?': ['.##.......',
          '#####.....',
          '.##.......',
          '.##.......',
          '.##.###...',
          '.####.##..',
          '.##....##.',
          '.##....##.',
          '.##...##..',
          '.##..##...',
          '.##..##...',
          '.##...###.'],    # Saturn
    '&': ['##......##',
          '##......##',
          '..######..',
          '..######..',
          '..######..',
          '..######..',
          '..........',
          '..........',
          '..######..',
          '..######..',
          '..######..',
          '..######..',
          '..######..',
          '..######..'],    # the ant
}

SMALL = {
    '@': ['..###..',
          '.#...#.',
          '#.....#',
          '#..#..#',
          '#.....#',
          '.#...#.',
          '..###..'],
    '(': ['..###',
          '.##..',
          '##...',
          '##...',
          '##...',
          '.##..',
          '..###'],
    '*': ['...#...',
          '...#...',
          '#######',
          '.#####.',
          '..###..',
          '.##.##.',
          '.#...#.'],
    '<': ['.###.',
          '#...#',
          '#...#',
          '.###.',
          '..#..',
          '.###.',
          '..#..'],    # Venus
    '>': ['...###',
          '.....#',
          '.###.#',
          '#...#.',
          '#...#.',
          '#...#.',
          '.###..'],    # Mars
    '=': ['#...#.',
          '.#..#.',
          '.#..#.',
          '#...#.',
          '######',
          '....#.',
          '....#.'],    # Jupiter
    '?': ['###...',
          '.#....',
          '.#.##.',
          '.##..#',
          '.#...#',
          '.#..#.',
          '.#..##'],    # Saturn
}



def moon_phase(theta, r=5.75, n=12):
    """A Moon phase, 12 x 12: the lit part filled, the dark part as the outline (northern view:
    waxing lit on the right). theta: 0 new, 90 first quarter, 180 full, 270 last quarter."""
    import math
    c = (n - 1) / 2
    rows = []
    for y in range(n):
        dy = y - c
        row = ''
        for x in range(n):
            dx = x - c
            d = math.hypot(dx, dy)
            if d > r + 0.3:
                row += '.'
                continue
            w = math.sqrt(max(r * r - dy * dy, 0))
            ct = math.cos(math.radians(theta))
            lit = dx > w * ct if theta <= 180 else dx < -w * ct
            row += '#' if lit or d > r - 1.0 else '.'
        rows.append(row)
    return rows


# the eight phases as codes '0' ... '7' (new, waxing crescent, first quarter, waxing gibbous, full,
# waning gibbous, last quarter, waning crescent); crescents and gibbous drawn a little wider
PHASES = {str(k): moon_phase(t) for k, t in enumerate((0, 62, 90, 122, 180, 238, 270, 298))}
BIG.update(PHASES)

def columns(rows):
    """[(value, repeat)] per column, bit 0 = the last row (base line), for AGRAPH."""
    w = max(len(r) for r in rows)
    cols = []
    for c in range(w):
        v = 0
        for i, r in enumerate(reversed(rows)):
            if c < len(r) and r[c] == '#':
                v |= 1 << i
        cols.append(v)
    return cols


def program(name, glyphs, gap=2, ws=14):
    """A text routine like PSYM: Z row of the base line, Y column, X string of symbol codes."""
    P = ['LBL "%s"' % name, 'STO 33', 'R↓', 'STO 30', 'R↓', 'STO 31', 'WSIZE %d' % ws,
         'LBL 01', 'αLENG 33', 'X=0?', 'GTO 02', 'α→𝑥 33', 'STO 32', 'XEQ IND 32', 'GTO 01',
         'LBL 02', 'WSIZE 64', 'RCL 31', 'RCL 30', 'RTN']
    for ch, rows in glyphs.items():
        P += ['LBL %d' % ord(ch), 'RCL 31', 'RCL 30']
        prev = None
        for v in columns(rows):
            if v != prev:
                P += ['%s#2' % bin(v)[2:], 'R↓']
            P += ['AGRAPH D']
            prev = v
        P += [str(gap), '+', 'STO 30', 'RTN']
    return P + ['END']
