#!/usr/bin/env python3
"""gencache.py - CACHE: compute the sky once, then every NAV view only draws.

In the NAV builds the views (ALMF ALMS HALMV HALMH HORZ ALLSKY ALMR) call these routines
instead of the ephemeris programs (build_navfull.py swaps the names):

  SUNA -> CSUN   MOO2 -> CMOO   PLN3 -> CPLN   STR2 -> CSTR   PHA2 -> CPHA
  NTWA RISE TRAN SET NTWP -> CNTA CRIS CTRN CSET CNTP

CSUN (X = JD) looks at the key of matrix ALMC (JD, lat R91, lon R92). Same time and
place: nothing is computed. Otherwise CALC runs the real programs once, with the same
criteria as the views (Moon and planets as PLN3 does them; a star only when SQK says it
can be over the horizon, like every view), and fills the matrix. Then CSUN puts back
what SUNA would have left (its registers, flag 12) and returns like SUNA. CMOO CPLN
CSTR CPHA only read the matrix. The sunrise times have their own key (noon JD, lat, lon):
they change only with the date or the place.

So only a new time (the arrows, a new DATE UTC) or a new place computes; going from
view to view with + and a number only draws.

Matrix ALMC, 71 x 4 (NAV makes it: 71 ENTER 4 NEWMAT STO "ALMC"):
   1 Sun   2 Moon   3-6 planets 1-4   7-64 stars 1-58:   GHA  Dec  Hc  Zn
                                                          (star not computed: Hc = -99)
  65  GHA Aries, Moon HP, Moon SD, flags (1 = flag 11 table Moon, 2 = flag 12 X letter)
  66  Moon % illuminated, Moon age
  67  key: JD, lat, lon
  68  key of the sunrise times: noon JD, lat, lon
  69  naut. twilight am, sunrise, meridian passage, sunset     70  naut. twilight pm
  71  what SUNA leaves for the views: R73 (Sun distance), R77 R81 (Sun Dec, GHA), R80 (GHA Aries)
Variables KA KB KC KD KE KF KN KI KJ KLA KLO KX KY KZ K1-K5 (scratch).

  python3 gencache.py   -> programs/CACHE.txt
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

M = '"ALMC"'
ROWS = 71
SUNREGS = [73, 77, 80, 81]            # what the views, SQK and HORZ read after SUNA (the rest is SUNA's own scratch)
SQK_MIN = '0.15643'                       # the views' own test: a star is drawn only above it
EVENTS = [('CNTA', 'NTWA', 69, 1), ('CRIS', 'RISE', 69, 2), ('CTRN', 'TRAN', 69, 3),
          ('CSET', 'SET', 69, 4), ('CNTP', 'NTWP', 70, 1)]
SWAP = {'SUNA': 'CSUN', 'MOO2': 'CMOO', 'PLN3': 'CPLN', 'STR2': 'CSTR', 'PHA2': 'CPHA',
        **{orig: new for new, orig, _, _ in EVENTS}}
VIEWS = ('ALMF', 'ALMS', 'HALMV', 'HALMH', 'HORZ', 'ALLSKY', 'ALMT')


def at(i, j):
    return ['INDEX ' + M, str(i), str(j), 'STOIJ']


def put(i, j, srcs):
    """Store the registers / variables srcs in row i from column j on."""
    out = at(i, j)
    for k, s in enumerate(srcs):
        out += (['J+'] if k else []) + ['RCL ' + s, 'STOEL']
    return out


def program(tables=True):
    P = ['LBL "CSUN"', 'STO "KJ"'] + at(67, 1) + [
         'RCLEL', 'RCL "KJ"', 'X≠Y?', 'GTO 09', 'J+', 'RCLEL', 'RCL 91', 'X≠Y?', 'GTO 09',
         'J+', 'RCLEL', 'RCL 92', 'X≠Y?', 'GTO 09', 'GTO 10',
         'LBL 09', 'RCL "KJ"', 'XEQ "CALC"',
         'LBL 10'] + at(71, 1)
    for k, r in enumerate(SUNREGS):                                   # what SUNA leaves in the registers
        P += (['J+'] if k else []) + ['RCLEL', 'STO %02d' % r]
    P += ['CF 12'] + at(65, 4) + ['RCLEL', '2', 'X≤Y?', 'SF 12']
    P += at(65, 1) + ['RCLEL', 'STO "KC"', '1', '1', 'STOIJ', 'RCLEL', 'STO "KA"', 'J+', 'RCLEL', 'STO "KB"',
                      'RCL "KC"', 'RCL "KB"', 'RCL "KA"', 'RTN']         # X GHA, Y Dec, Z GHA Aries
    # CMOO: X GHA, Y Dec, Z HP, T SD (+ flag 11 with the tables)
    P += ['LBL "CMOO"']
    if tables:
        P += ['CF 11'] + at(65, 4) + ['RCLEL', '2', 'MOD', 'X≠0?', 'SF 11']
    P += at(65, 2) + ['RCLEL', 'STO "KC"', 'J+', 'RCLEL', 'STO "KD"', '2', '1', 'STOIJ', 'RCLEL', 'STO "KA"',
                      'J+', 'RCLEL', 'STO "KB"', 'RCL "KD"', 'RCL "KC"', 'RCL "KB"', 'RCL "KA"', 'RTN']
    # CPLN: X = planet 1-4 -> X GHA, Y Dec
    P += ['LBL "CPLN"', '2', '+', 'STO "KI"', 'INDEX ' + M, 'RCL "KI"', '1', 'STOIJ', 'RCLEL', 'STO "KA"',
          'J+', 'RCLEL', 'STO "KB"', 'RCL "KB"', 'RCL "KA"', 'RTN']
    # CSTR: star R82 -> X GHA, Y Dec, Z SHA
    P += ['LBL "CSTR"', 'INDEX ' + M, 'RCL 82', '6', '+', '1', 'STOIJ', 'RCLEL', 'STO "KA"', 'J+', 'RCLEL', 'STO "KB"',
          '65', '1', 'STOIJ', 'RCL "KA"', 'RCLEL', '-', '360', 'MOD', 'RCL "KB"', 'RCL "KA"', 'RTN']
    # CPHA: X % illuminated, Y age
    P += ['LBL "CPHA"'] + at(66, 1) + ['RCLEL', 'STO "KA"', 'J+', 'RCLEL', 'STO "KB"', 'RCL "KB"', 'RCL "KA"', 'RTN']
    # sunrise times: Z noon JD, Y lat, X lon (as the originals); the five together, own key
    for new, orig, i, j in EVENTS:
        P += ['LBL "%s"' % new, 'XEQ 20', str(i), str(j), 'GTO 21']
    P += ['LBL 21', 'INDEX ' + M, 'STOIJ', 'RCLEL', 'RTN',
          'LBL 20', 'STO "KX"', 'R↓', 'STO "KY"', 'R↓', 'STO "KZ"'] + at(68, 1) + [
          'RCLEL', 'RCL "KZ"', 'X≠Y?', 'GTO 22', 'J+', 'RCLEL', 'RCL "KY"', 'X≠Y?', 'GTO 22',
          'J+', 'RCLEL', 'RCL "KX"', 'X≠Y?', 'GTO 22', 'RTN', 'LBL 22']
    for k, (new, orig, i, j) in enumerate(EVENTS):
        P += ['RCL "KZ"', 'RCL "KY"', 'RCL "KX"', 'XEQ "%s"' % orig, 'STO "K%d"' % (k + 1)]
    P += put(69, 1, ['"K%d"' % (k + 1) for k in range(5)]) + put(68, 1, ['"KZ"', '"KY"', '"KX"']) + ['RTN']
    # CALC: X = JD; lat R91, lon R92, HCZI done (as the views do before SUNA)
    P += ['LBL "CALC"', 'STO "KJ"', 'RCL 91', 'STO "KLA"', 'RCL 92', 'STO "KLO"',
          'RCL "KJ"', 'XEQ "SUNA"', 'STO "KA"', 'R↓', 'STO "KB"', 'R↓', 'STO "KC"',
          '0', 'STO "KF"', 'FS? 12', 'XEQ 81'] + put(71, 1, ['%02d' % r for r in SUNREGS])
    P += ['XEQ "PHA2"', 'STO "KD"', 'X<>Y', 'STO "KE"'] + put(66, 1, ['"KD"', '"KE"'])
    P += ['RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"'] + put(1, 1, ['"KA"', '"KB"', '96', '97']) + put(65, 1, ['"KC"'])
    P += ['XEQ "MOO2"', 'STO "KA"', 'R↓', 'STO "KB"', 'R↓', 'STO "KC"', 'R↓', 'STO "KD"']
    if tables:
        P += ['FS? 11', 'XEQ 82']
    P += ['RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"'] + put(2, 1, ['"KA"', '"KB"', '96', '97']) + put(65, 2, ['"KC"', '"KD"', '"KF"'])
    body = ['STO "KA"', 'X<>Y', 'STO "KB"', 'RCL "KB"', 'RCL "KA"', 'XEQ "HCZ"', 'INDEX ' + M, 'RCL "KN"', None, '+', '1', 'STOIJ',
            'RCL "KA"', 'STOEL', 'J+', 'RCL "KB"', 'STOEL', 'J+', 'RCL 96', 'STOEL', 'J+', 'RCL 97', 'STOEL']
    P += ['1', 'STO "KN"', 'LBL 01', 'RCL "KN"', 'XEQ "PLN3"'] + [x if x else '2' for x in body] + [
          'RCL "KN"', '1', '+', 'STO "KN"', '4', 'X≥Y?', 'GTO 01']
    P += ['1', 'STO "KN"', 'LBL 02', 'RCL "KN"', 'STO 82', 'XEQ "SQK"', SQK_MIN, 'X>Y?', 'GTO 03',
          'XEQ "STR2"'] + [x if x else '6' for x in body] + ['GTO 04',
          'LBL 03', 'INDEX ' + M, 'RCL "KN"', '6', '+', '3', 'STOIJ', '-99', 'STOEL',
          'LBL 04', 'RCL "KN"', '1', '+', 'STO "KN"', '58', 'X≥Y?', 'GTO 02']
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


NEWMAT = [str(ROWS), 'ENTER', '4', 'NEWMAT', 'STO ' + M]


if __name__ == '__main__':
    P = program()
    open(os.path.join(ROOT, 'programs', 'CACHE.txt'), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    print('programs/CACHE.txt', len(P), 'lines')
