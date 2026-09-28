#!/usr/bin/env python3
"""gencache.py - CACHE: compute the sky once, then every NAV view only draws.

In the NAV builds the views (ALMF ALMS HALMV HALMH HORZ ALLSKY ALMR) call these routines
instead of the ephemeris programs (build_navfull.py swaps the names):

  SUNA -> CSUN   MOO2 -> CMOO   PLN3 -> CPLN   STR2 -> CSTR   PHA2 -> CPHA
  SQK  -> CSQK   HCZ  -> CHCZ
  NTWA RISE TRAN SET NTWP -> CNTA CRIS CTRN CSET CNTP

CSUN (X = JD) looks at the key of matrix ALMC (JD, lat R91, lon R92). Same time and
place: nothing is computed. Otherwise CALC runs SUNA, PHA2, MOO2 and PLN3 1-4 (with HCZ)
into the matrix and marks the stars "not asked yet"; a star is computed (SQK, STR2, HCZ) the
first time a view asks for it (CSQK), so a new time costs what the view needs, no more.
Then CSUN puts back what SUNA would have left (rows 71-73, flag 12) and returns like SUNA.
From the cache a view does no series and no trigonometry for the bodies:
  CMOO CPLN CSTR CPHA  read the row (GHA, Dec ...) and remember it (variable KR)
  CSQK                 1 if the star was computed (over the horizon test passed), else 0
  CHCZ                 X = GHA, Y = Dec of the row just read: Hc Zn from the matrix
                       (R96 R97 and "SHC" = sin Hc, what the views read); other input: real HCZ
The sunrise times have their own key (noon JD, lat, lon): they change only with the date or
the place. So only a new time (the arrows, a new DATE UTC) or a new place computes; going
from view to view with + and a number only draws.

Native matrix commands: INDEX, STOIJ (Y row, X column, the stack stays), STOSEQ / RCLSEQ
(store / recall the element and go to the next one), J- (previous column), RCLEL, STOEL.
Rows are read Dec first then J- GHA, so the stack comes out X GHA, Y Dec with no variables.

Matrix ALMC, 71 x 4 (NAV makes it: 71 ENTER 4 NEWMAT STO "ALMC"):
   1 Sun   2 Moon   3-6 planets 1-4   7-64 stars 1-58:   GHA  Dec  Hc  Zn
                     (star: Hc -98 = not asked for yet, -99 = below the horizon test)
  65  GHA Aries, Moon HP, Moon SD, flags (1 = flag 11 table Moon, 2 = flag 12 X letter)
  66  Moon % illuminated, Moon age
  67  key: JD, lat, lon
  68  key of the sunrise times: noon JD, lat, lon
  69  naut. twilight am, sunrise, meridian passage, sunset     70  naut. twilight pm
  71-73  what SUNA leaves for the views, SQK and STR2: R73 R77 R80 R81, R54 R66 R74,
         SCTH SPI SSTH SZE SZZ
R82 is CALC's counter (it is STR2's star number anyway).
Variables KA KB KC KD KE KF KJ KR KLA KLO KX KY KZ K1-K5 (scratch; KR = row last read).

  python3 gencache.py   -> programs/CACHE.txt
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

M = '"ALMC"'
ROWS = 73
# what SUNA leaves that the views, SQK, HORZ and STR2 (stars computed later, CSQK) read
SUNREGS = ['73', '77', '80', '81', '54', '66', '74', '"SCTH"', '"SPI"', '"SSTH"', '"SZE"', '"SZZ"']
SQK_MIN = '0.15643'                   # the views' own test: a star is drawn only above it
EVENTS = [('CNTA', 'NTWA', 69, 1), ('CRIS', 'RISE', 69, 2), ('CTRN', 'TRAN', 69, 3),
          ('CSET', 'SET', 69, 4), ('CNTP', 'NTWP', 70, 1)]
SWAP = {'SUNA': 'CSUN', 'MOO2': 'CMOO', 'PLN3': 'CPLN', 'STR2': 'CSTR', 'PHA2': 'CPHA',
        'SQK': 'CSQK', 'HCZ': 'CHCZ', **{orig: new for new, orig, _, _ in EVENTS}}
VIEWS = ('ALMF', 'ALMS', 'HALMV', 'HALMH', 'HORZ', 'ALLSKY', 'ALMT')


def at(i, j):
    return ['INDEX ' + M, str(i), str(j), 'STOIJ']


def put(i, j, srcs):
    """Store registers / variables srcs in row i from column j on (STOSEQ: store and next)."""
    out = at(i, j)
    for k, s in enumerate(srcs):
        out += ['RCL ' + s, 'STOSEQ' if k < len(srcs) - 1 else 'STOEL']
    return out


def row(off):
    """X GHA, Y Dec of body R82 -> HCZ, then GHA Dec Hc Zn into row R82 + off."""
    return ['STO "KA"', 'X<>Y', 'STO "KB"', 'X<>Y', 'XEQ "HCZ"', 'INDEX ' + M, 'RCL 82', str(off), '+', '1', 'STOIJ',
            'RCL "KA"', 'STOSEQ', 'RCL "KB"', 'STOSEQ', 'RCL 96', 'STOSEQ', 'RCL 97', 'STOEL']


def program(tables=True):
    P = []
    # CSUN: X = JD -> X GHA, Y Dec, Z GHA Aries (like SUNA)
    P += ['LBL "CSUN"', 'STO "KJ"'] + at(67, 1) + [
          'RCLSEQ', 'RCL "KJ"', 'X≠Y?', 'GTO 09', 'RCLSEQ', 'RCL 91', 'X≠Y?', 'GTO 09',
          'RCLEL', 'RCL 92', 'X≠Y?', 'GTO 09', 'GTO 10',
          'LBL 09', 'RCL "KJ"', 'XEQ "CALC"',
          'LBL 10'] + at(71, 1)
    for k, r in enumerate(SUNREGS):
        P += ['RCLSEQ' if k < len(SUNREGS) - 1 else 'RCLEL', 'STO ' + r]
    P += ['CF 12', '65', '4', 'STOIJ', 'RCLEL', '2', 'X≤Y?', 'SF 12',
          '65', '1', 'STOIJ', 'RCLEL', 'STO "KC"', '1', 'STO "KR"', '2', 'STOIJ',
          'RCL "KC"', 'RCLEL', 'J-', 'RCLEL', 'RTN']
    # CMOO: X GHA, Y Dec, Z HP, T SD (+ flag 11 with the tables)
    P += ['LBL "CMOO"'] + at(65, 2) + ['RCLSEQ', 'STO "KC"', 'RCLSEQ', 'STO "KD"']
    if tables:
        P += ['CF 11', 'RCLEL', '2', 'MOD', 'X≠0?', 'SF 11']
    P += ['2', 'STO "KR"', '2', 'STOIJ', 'RCL "KD"', 'RCL "KC"', 'RCLEL', 'J-', 'RCLEL', 'RTN']
    # CPLN: X = planet 1-4 -> X GHA, Y Dec
    P += ['LBL "CPLN"', 'INDEX ' + M, '2', '+', 'STO "KR"', '2', 'STOIJ', 'RCLEL', 'J-', 'RCLEL', 'RTN']
    # CSTR: star R82 -> X GHA, Y Dec
    P += ['LBL "CSTR"', 'INDEX ' + M, 'RCL 82', '6', '+', 'STO "KR"', '2', 'STOIJ', 'RCLEL', 'J-', 'RCLEL', 'RTN']
    # CSQK: X = star (R82 too, as the views set it) -> 1 if it can be over the horizon, else 0.
    # A star is computed the first time a view asks for it (Hc -98 = not asked yet): SQK, and
    # when it passes STR2 and HCZ into its row; -99 = below. The next views only read.
    P += ['LBL "CSQK"', 'INDEX ' + M, 'STO "KA"', '6', '+', '3', 'STOIJ', 'RCLEL', '-98', 'X=Y?', 'GTO 32',
          'X<>Y', '-99', 'X=Y?', 'GTO 31', '1', 'RTN',
          'LBL 31', '0', 'RTN',
          'LBL 32', 'RCL "KA"', 'XEQ "SQK"', SQK_MIN, 'X>Y?', 'GTO 33', 'XEQ "STR2"'] + row(6) + ['1', 'RTN',
          'LBL 33', 'INDEX ' + M, 'RCL 82', '6', '+', '3', 'STOIJ', '-99', 'STOEL', '0', 'RTN']
    # CHCZ: X GHA, Y Dec of the row just read (KR) -> Hc Zn from the matrix; else the real HCZ
    P += ['LBL "CHCZ"', 'STO "KA"', 'X<>Y', 'STO "KB"', 'INDEX ' + M, 'RCL "KR"', '1', 'STOIJ',
          'RCLSEQ', 'RCL "KA"', 'X≠Y?', 'GTO 30', 'RCLSEQ', 'RCL "KB"', 'X≠Y?', 'GTO 30',
          'RCLSEQ', 'STO 96', 'SIN', 'STO "SHC"', 'RCLEL', 'STO 97', 'RCL 96', 'RTN',
          'LBL 30', 'RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"', 'RTN']
    # CPHA: X % illuminated, Y age
    P += ['LBL "CPHA"'] + at(66, 2) + ['RCLEL', 'J-', 'RCLEL', 'RTN']
    # sunrise times: Z noon JD, Y lat, X lon (as the originals); the five together, own key
    for new, orig, i, j in EVENTS:
        P += ['LBL "%s"' % new, 'XEQ 20', str(i), str(j), 'GTO 21']
    P += ['LBL 21', 'INDEX ' + M, 'STOIJ', 'RCLEL', 'RTN',
          'LBL 20', 'STO "KX"', 'R↓', 'STO "KY"', 'R↓', 'STO "KZ"'] + at(68, 1) + [
          'RCLSEQ', 'RCL "KZ"', 'X≠Y?', 'GTO 22', 'RCLSEQ', 'RCL "KY"', 'X≠Y?', 'GTO 22',
          'RCLEL', 'RCL "KX"', 'X≠Y?', 'GTO 22', 'RTN', 'LBL 22']
    for k, (new, orig, i, j) in enumerate(EVENTS):
        P += ['RCL "KZ"', 'RCL "KY"', 'RCL "KX"', 'XEQ "%s"' % orig, 'STO "K%d"' % (k + 1)]
    P += put(69, 1, ['"K%d"' % (k + 1) for k in range(5)]) + put(68, 1, ['"KZ"', '"KY"', '"KX"']) + ['RTN']
    # CALC: X = JD; lat R91, lon R92, HCZI done (as the views do before SUNA)
    P += ['LBL "CALC"', 'STO "KJ"', 'RCL 91', 'STO "KLA"', 'RCL 92', 'STO "KLO"',
          'RCL "KJ"', 'XEQ "SUNA"', 'STO "KA"', 'R↓', 'STO "KB"', 'R↓', 'STO "KC"',
          '0', 'STO "KF"', 'FS? 12', 'XEQ 81'] + put(71, 1, SUNREGS) + put(65, 1, ['"KC"'])
    P += ['XEQ "PHA2"', 'STO "KD"', 'X<>Y', 'STO "KE"'] + put(66, 1, ['"KD"', '"KE"'])
    P += ['RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"'] + put(1, 1, ['"KA"', '"KB"', '96', '97'])
    P += ['XEQ "MOO2"', 'STO "KA"', 'R↓', 'STO "KB"', 'R↓', 'STO "KC"', 'R↓', 'STO "KD"']
    if tables:
        P += ['FS? 11', 'XEQ 82']
    P += ['RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"'] + put(2, 1, ['"KA"', '"KB"', '96', '97']) + put(65, 2, ['"KC"', '"KD"', '"KF"'])

    P += ['1', 'STO 82', 'LBL 01', 'RCL 82', 'XEQ "PLN3"'] + row(2) + [
          '1', 'STO+ 82', '4', 'RCL 82', 'X≤Y?', 'GTO 01']
    # stars: not computed yet (Hc -98); CSQK computes each one when a view first asks for it
    P += ['INDEX ' + M, '7', '3', 'STOIJ', '58', 'STO 82', '-98', 'LBL 02', 'STOEL', 'I+', 'DSE 82', 'GTO 02']
    P += put(67, 1, ['"KJ"', '"KLA"', '"KLO"']) + ['RTN',
          'LBL 81', 'RCL "KF"', '2', '+', 'STO "KF"', 'RTN']
    if tables:
        P += ['LBL 82', 'RCL "KF"', '1', '+', 'STO "KF"', 'RTN']
    return P + ['END']


def swap(lines):
    """A view that reads the cache: XEQ "SUNA" -> XEQ "CSUN" ... (only these calls)."""
    out = []
    for l in lines:
        for o, n in SWAP.items():
            if l == 'XEQ "%s"' % o:
                l = 'XEQ "%s"' % n
        out.append(l)
    return out


# NAV (and INIT) make the matrix; KR = 1 so CHCZ always has a row to look at
NEWMAT = [str(ROWS), 'ENTER', '4', 'NEWMAT', 'STO ' + M, '1', 'STO "KR"']


if __name__ == '__main__':
    P = program()
    open(os.path.join(ROOT, 'programs', 'CACHE.txt'), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    print('programs/CACHE.txt', len(P), 'lines')
