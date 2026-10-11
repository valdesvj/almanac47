"""struct_comments.py - what the numbered routines of the STRUCT NAVFULL and MOON47 do (programs_struct/).

Used by tools/build_struct_src.py (NAVFULL_COMMENTED.txt, MOON47_COMMENTED.txt) and tools/build_forum.py (the '#'
lines of the .p47u files). The global labels are described in build_struct_src.LABELS.

ROUTINES[(program, label)]   a routine (a numbered label some XEQ nn calls)
ENTRIES[program]             [(labels, text)]: the XEQ IND tables (a label reached only by XEQ IND), and the few
                             labels nothing reaches
MOON[label]                  the same for MOON47 (one program)
"""

ROUTINES = {
    # NAV: the menu
    ('NAV', '01'): 'bottom of the menu and INFO: a line and DOES NOT REPLACE THE NAUTICAL ALMANAC',
    ('NAV', '02'): 'the time in use: DATE + UTC + the hours of the arrows ("W4") as a Julian Date; LAT, LON in degrees '
                   '-> Z JD, Y lat, X lon',
    ('NAV', '03'): 'the sky for the time in use: DR into R13 R14, sin / cos lat ("V6" "W1"), Sun from the cache (CSUN: '
                   'computes the whole sky only for a new time or place), the five sun times (CNTA)',
    ('NAV', '04'): 'draws the menu: ALMANAC 47, VALID (the matrices\' period), the header, items 1-6 and 0 END, the key line',
    ('NAV', '05'): 'the SINKING....ABOUT box in the middle of the screen, shown at once (PAUSE 0)',
    ('NAV', '06'): 'the hourglass in the top bar, then the box (05). Something lives here: flag 47 ...',
    ('NAV', '07'): 'D.MMm -> decimal degrees',
    ('NAV', '08'): 'highlights the menu item just chosen (XOR, GRMOD 1)',
    ('NAV', '10'): 'DATE prompt in the D.MY date format',
    ('NAV', '11'): 'DATE prompt in the M.DY date format',
    ('NAV', '12'): 'two columns of what lives in 06',
    # CALC: the sky for a new time or place
    ('CALC', '01'): 'once: the 58 stars of the catalogue ST as unit vectors now (SXA) and their change a century (SXD, '
                    'proper motion)',
    ('CALC', '02'): 'the rotation matrix of precession and nutation for the date ("YMT")',
    ('CALC', '03'): 'one star moved by its proper motion over "YT" years -> the parts of its unit vector',
    ('CALC', '04'): 'a 3 x 3 rotation about the z axis by the angle X',
    ('CALC', '05'): 'a 3 x 3 rotation about the x axis by the angle X',
    ('CALC', '06'): 'one star\'s vector into its row ("YK") of the indexed matrix',
    # PTXS: the text routines
    ('PTXS', '01'): 'appends X as two digits (00-99) to the text in R11',
    ('PTXS', '02'): 'starts the text in R11 with the whole number X',
    ('PTXS', '05'): 'writes the text in R11 at row R10, column R01 (ATEXT in GRFNT 21) -> Y row, X next column',
    ('PTXS', '06'): 'the sign of R07: a space or "-"',
    ('PTXS', '07'): 'an azimuth of 360.0 written as 000.0',
    ('PTXS', '08'): 'appends the last digit of X',
    # HANIM: view 4 ANIM
    ('HANIM', '01'): 'the Moon at the frame\'s hour: three computed positions (matrix "AQ") interpolated',
    ('HANIM', '02'): 'the Sun (SUNF) and the Moon (a short series) at the hour X of the animation',
    ('HANIM', '03'): 'a body on the whole-sky chart: column from its Zn (R05), row from sin Hc ("V4")',
    ('HANIM', '04'): 'writes or erases the frame\'s time (XOR, GRMOD 1)',
    ('HANIM', '05'): 'the chart: horizon, altitude dots, the shared axes (OUT4), the compass row (south up for S latitudes)',
    ('HANIM', '06'): 'the time arguments of the hour R28: days and centuries from J2000, sidereal time',
    ('HANIM', '07'): 'the sky label TWILIGHT',
    ('HANIM', '08'): 'the sky label DAY',
    ('HANIM', '09'): 'an angle into -180 ... +180',
    ('HANIM', '10'): 'the sidereal angle of the frame\'s hour taken off',
    ('HANIM', '11'): 'keeps the first Sun position of the run',
    ('HANIM', '12'): 'the mark T at the top right: the tables in use',
    ('HANIM', '13'): 'the mark X at the top right: a date outside the matrices',
    ('HANIM', '14'): 'south latitude: the chart turned (south up)',
    ('HANIM', '15'): 'the Moon of the second set of interpolated values',
    ('HANIM', '16'): 'GHA of the frame\'s hour, 0-360',
    # PSYS: symbols, 7 rows
    ('PSYS', '01'): 'two columns shared by the 7-row symbols',
    ('PSYS', '02'): 'the last column of a symbol; R01 = the next column',
    ('PSYS', '03'): 'two columns shared by the 7-row symbols',
    # ALLSKY: view 5
    ('ALLSKY', '01'): 'draws the symbol of the body R22 at its place on the chart',
    ('ALLSKY', '02'): 'a body on the whole-sky chart: column from its Zn (R05), row from sin Hc ("V4")',
    ('ALLSKY', '03'): 'one text row lower',
    ('ALLSKY', '04'): 'the sky label TWILIGHT',
    ('ALLSKY', '05'): 'the sky label DAY',
    ('ALLSKY', '06'): 'the mark T at the top right: the tables in use',
    ('ALLSKY', '07'): 'the mark X at the top right: a date outside the matrices',
    ('ALLSKY', '08'): 'south latitude: the chart turned (south up)',
    # PLN2: the planets
    ('PLN2', '01'): 'PLN2: the planet from the tables (TGET) when they are loaded, else from its series (02)',
    ('PLN2', '02'): 'the planet by its VSOP87 series with light-time (the Earth from "EEL" "EEB" "EER")',
    ('PLN2', '03'): 'quick position: the mean elements of the planet (LBL 60-64) and Kepler\'s equation',
    ('PLN2', '04'): 'the Earth\'s quick position, kept for this time ("P0" "P1" "P2")',
    ('PLN2', '05'): 'ecliptic -> equatorial; the vector kept in "H7" "H8" "H9" for Hc and Zn',
    ('PLN2', '06'): 'the e-terms of aberration: the eccentricity ("U8") and the perihelion ("W5") of the Earth\'s orbit',
    ('PLN2', '07'): 'light-time: AU -> days',
    # SUNA: the Sun and the series
    ('SUNA', '01'): 'SER: one series, the sum of A cos(B + C t) for the powers of t ("H3" "H4"): cos and sin as one '
                    'complex e^x, then DOT',
    ('SUNA', '03'): 'nutation: the five arguments ("Q3") and the series NU -> nutation in longitude and obliquity',
    ('SUNA', '04'): 'precession angles ("U5" "U6" "U7") and the Earth\'s eccentricity and perihelion ("U8" "W5")',
    ('SUNA', '05'): 'the Sun and Aries from the tables (TGET) when they are loaded',
    ('SUNA', '06'): 'flag 12 set when the date is outside the period of the matrices',
    ('SUNA', '07'): 'the dot product of NU and the time vector, scaled',
    # CSUN: the cache (matrix ALMC)
    ('CSUN', '01'): 'Hc and Zn of the planet just computed from its vector ("H7" "H8" "H9"), else the real HCZ',
    ('CSUN', '02'): 'a new time or place: the Sun (SUNA) and its values into ALMC rows 65-72, then the rest of the '
                    'sky (CALC)',
    ('CSUN', '03'): 'the five sun times from ALMC rows 69-70 when date and place match, else computed (NTWA RISE '
                    'TRAN SET NTWP) and stored',
    ('CSUN', '04'): 'Hc and Zn of the Sun from its vector ("F1" "F2" "F3"), else the real HCZ',
    ('CSUN', '05'): 'Hc and Zn of the Moon from its vector ("F7" "F8" "F9"), else the real HCZ',
    ('CSUN', '06'): 'the Sun read back from ALMC: its values, the time arguments, the precession angles, flag 12',
    ('CSUN', '07'): 'Hc and Zn from an equatorial unit vector: rotated with the DR, one ->POL each (no trig)',
    ('CSUN', '08'): 'GHA Dec Hc Zn into the indexed row of ALMC',
    ('CSUN', '09'): 'date, latitude and longitude of the sun times back on the stack',
    ('CSUN', '10'): 'the real HCZ of the body in "V0" "V1"',
    ('CSUN', '11'): 'the equator of the SKY / SPLIT charts (40 dots, "U3"): computed again only for a new place',
    ('CSUN', '12'): 'the equator of the ANIM / ALLSKY charts (60 dots, "U2"): computed again only for a new place',
    ('CSUN', '13'): 'one element of ALMC (row Y, column X)',
    ('CSUN', '14'): 'the equator dots as powers of one complex rotation, a whole column at a time (M.PUTM)',
    ('CSUN', '15'): 'counts a star computed in full',
    ('CSUN', '16'): 'counts a star read from the cache',
    ('CSUN', '17'): 'ALMC indexed at row 68 (date and place of the sun times)',
    # MOO2: the Moon
    ('MOO2', '01'): 'the argument vectors of the Moon\'s series ("Q5" "Q6" "Q7", "H5" "H6")',
    ('MOO2', '02'): 'the row 1, t, t^2 into the indexed matrix',
    ('MOO2', '03'): 'the four arguments D, M, M\', F into the indexed matrix',
    # RISE: sun times
    ('RISE', '01'): 'the time of the event, by iteration on the Sun\'s hour angle (SUNG); 99 when there is none',
    ('RISE', '02'): 'Z JD, Y latitude, X longitude into R25 R14 R13',
    ('RISE', '03'): 'the same, with the altitude of sunrise and sunset (-0 50\')',
    ('RISE', '04'): '99: no event that day (midnight sun or polar night)',
    # PSYB: symbols, 12 rows
    ('PSYB', '05'): 'the next column in R06',
    # HORZ: view 3 SKY
    ('HORZ', '02'): 'a star: its symbol and its number (tinyFont) on the chart, and into the list "H1"',
    ('HORZ', '03'): 'Hc and Zn from the cache (CHCZ), then the place on the chart (04)',
    ('HORZ', '04'): 'the place on the chart: column R23 from Zn, row R24 from sin Hc',
    ('HORZ', '05'): 'the Sun\'s symbol',
    ('HORZ', '06'): 'the Moon\'s symbol, into the list',
    ('HORZ', '07'): 'the first planet above the horizon (planets 1-4 in turn): its symbol, into the list',
    ('HORZ', '08'): 'the name of the body R22 next to its symbol (SUN, MOON, a planet or a star)',
    ('HORZ', '09'): 'adds a body (code X, Zn R05, Hc R09) to the list "H1" the names go round',
    ('HORZ', '10'): 'writes or erases the name (XOR, GRMOD 1)',
    ('HORZ', '11'): 'the sky label TWILIGHT',
    ('HORZ', '12'): 'the sky label DAY',
    ('HORZ', '13'): 'the name of the Moon or a planet (codes 81-85)',
    ('HORZ', '14'): 'back to the first body of the list',
    ('HORZ', '16'): 'the name on the left of the symbol near the right edge',
    ('HORZ', '17'): 'the mark T at the top right: the tables in use',
    ('HORZ', '18'): 'the mark X at the top right: a date outside the matrices',
    ('HORZ', '19'): 'the star number on the left near the right edge',
    ('HORZ', '20'): 'row and column of the symbol for PSYS',
    # HALMH: view 2 SPLIT
    ('HALMH', '01'): 'one row of the table: GHA, N / S Dec, Hc, Zn (Hc white on black when negative); one row lower',
    ('HALMH', '02'): 'the planet: its symbol on the chart, its row in the table',
    ('HALMH', '04'): 'the stars by brightness (matrix SBR) that are above the horizon, until the rows are full',
    ('HALMH', '05'): 'Hc and Zn from the cache (CHCZ), then the place on the chart',
    ('HALMH', '06'): 'the Sun\'s symbol on the chart',
    ('HALMH', '07'): 'the Moon: its symbol on the chart, its row in the table',
    ('HALMH', '08'): 'S for a south declination',
    ('HALMH', '09'): 'the mark T at the top right: the tables in use',
    ('HALMH', '10'): 'the mark X at the top right: a date outside the matrices',
    ('HALMH', '11'): 'the symbol kept inside the right edge',
    ('HALMH', '12'): 'Hc white on black (a box in XOR)',
    ('HALMH', '13'): 'row and column of the symbol for PSYS',
    # ALMF: view 1 ALMANAC
    ('ALMF', '01'): 'one row of the table: GHA, N / S Dec, Hc, Zn (Hc white on black when negative); one row lower',
    ('ALMF', '02'): 'the name, then the row (01); counts the rows',
    ('ALMF', '03'): 'the planet\'s row: symbol, name, values',
    ('ALMF', '04'): 'the stars by brightness (matrix SBR) that are above the horizon, until the 8 rows are full',
    ('ALMF', '05'): 'the Moon\'s row',
    ('ALMF', '06'): 'the date at 0 h, latitude and longitude for the sun times',
    ('ALMF', '07'): 'S for a south declination',
    ('ALMF', '08'): 'the Moon text WANING',
    ('ALMF', '09'): 'the mark T at the top right: the tables in use',
    ('ALMF', '10'): 'the mark X at the top right: a date outside the matrices',
    ('ALMF', '11'): 'the Moon text FULL',
    ('ALMF', '12'): 'the Moon text NEW',
    ('ALMF', '13'): 'Hc white on black (a box in XOR)',
    ('ALMF', '14'): 'Hc and Zn from the cache (CHCZ)',
    # TGET: the tables
    ('TGET', '01'): 'one Chebyshev sum: the block\'s coefficients (M.GETM) DOT the polynomials ("Q2")',
    ('TGET', '02'): 'the Chebyshev polynomials T0 ... Tn at the time in the block, into "Q2"',
}
for _l in ('01', '02', '03', '04', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16'):
    ROUTINES.setdefault(('PSYB', _l), 'columns shared by the 12-row symbols')

_GONE = 'not reached: no XEQ calls it and no XEQ IND index comes to it (left by an older version)'
_RUN = 'a label no step jumps to: the steps above run into it'
_PLANETS = 'Venus, Mars, Jupiter, Saturn'
_CHARS = 'the symbols by character code: @ Sun, ( Moon, * star, < = > ? ' + _PLANETS
ENTRIES = {
    'NAV': [(('09',), _GONE)],
    'PSYS': [(('40', '42', '60', '61', '62', '63', '64'), 'XEQ IND table: ' + _CHARS),
             (('94', '95', '98'), _GONE)],
    'PSYB': [(('40', '42', '60', '61', '62', '63', '64'), 'XEQ IND table: ' + _CHARS),
             (('38',), _GONE),
             (('48', '49', '50', '51', '52', '53', '54', '55'), 'XEQ IND table: the eight Moon phases, characters 0-7')],
    'ALLSKY': [(('61', '62', '63', '71', '72', '73', '74'), 'XEQ IND table: the symbol character of a body (61-63 '
                'Sun, Moon, star; 71-74 the planets)'),
               (('24', '25'), _GONE)],
    'PLN2': [(('31',), _RUN),
             (('11', '12', '13', '14'), 'XEQ IND table: the VSOP87 series of ' + _PLANETS),
             (('60', '61', '62', '63', '64'), 'XEQ IND table: the mean elements of the Earth, ' + _PLANETS)],
    'HORZ': [(('71', '72', '73', '74'), 'XEQ IND table: the symbol characters of the planets'),
             (('81', '82', '83', '84', '85'), 'XEQ IND table: the names of the Moon and the planets'),
             (('91', '92', '93', '94'), 'XEQ IND table: a number by body code'),
             (('54', '59', '67'), _GONE),
             (('01',), 'not reached: it follows a loop only RTN leaves (CEQR, the old equator, is no longer used)'),
             (('15',), _RUN)],
    'HALMH': [(('03',), _RUN),
              (('71', '72', '73', '74'), 'XEQ IND table: the symbol characters of the planets'),
              (('82', '83', '84', '85'), 'XEQ IND table: the names of the planets'),
              (('91', '92', '93', '94'), 'XEQ IND table: a number by body code'),
              (('27',), _GONE)],
    'ALMF': [(('71', '72', '73', '74'), 'XEQ IND table: the symbol characters of the planets'),
             (('82', '83', '84', '85'), 'XEQ IND table: the names of the planets'),
             (('91', '92', '93', '94'), 'XEQ IND table: a number by body code'),
             (('48', '49', '50', '51', '52', '53', '54', '55'), 'XEQ IND table: the Moon phase symbol characters 0-7'),
             (('27',), _GONE)],
    'SNMU': [(tuple('%02d' % n for n in range(1, 59)), 'XEQ IND table: the names of the 58 stars by number')],
    'TGET': [(('20', '21', '22', '23', '24', '25', '26'), 'XEQ IND table: the table matrices TSU TVE TMA TJU TSA TMO '
              'TAR (Sun, planets, Moon, Aries)')],
}


def entry(program, label):
    """(text, labels): what a label reached only by XEQ IND is, and the labels of its table (the comment goes before
    the first of them met in the listing); None when it is not in ENTRIES."""
    for labels, text in ENTRIES.get(program, ()):
        if label in labels:
            return text, labels
    return None


MOON = {
    '01': 'one row of the disc between two columns (AGRAPH runs, 02)',
    '02': 'a run of columns of one row (AGRAPH, at most 60 a step)',
    '03': 'the disc: row by row, the edge of the Moon and the terminator from the age; turned for the south',
    '04': 'a column measured from the disc\'s centre (120)',
    '05': 'the text in R49 at row R31, column R30 (M7TX)',
    '06': 'M7IN - TEXT: whole number (|X| rounded)',
    '07': 'columns shared by the phase symbols',
    '08': 'columns shared by the phase symbols',
    '09': 'columns shared by the phase symbols',
    '10': 'columns shared by the phase symbols',
    '11': 'columns shared by the phase symbols; the next column',
    '12': 'columns shared by the phase symbols; the next column',
    '13': 'a value in minutes of arc: one decimal and \'',
    '14': 'a whole number, with a leading 0 below 10',
    '15': 'M7HM - TEXT: hh:mm from hours (--:-- when X > 98: no event)',
    '16': 'the eight phase symbols in a row, today\'s one inverted',
    '17': 'the time of day of a Julian Date as hh:mm',
    '18': 'the page: the clock line, the disc, the phase name, % lit, age, HP, SD, the next phases, the symbols',
    '19': 'M7F1 - TEXT: number with one decimal (|X|)',
    '20': 'the next four phases: symbol, date and time UT',
    '21': 'M7DT - TEXT: date dd-mm-yyyy from a Julian Date',
    '22': 'the time when the Moon\'s elongation is X degrees, from the guess Y',
    '23': 'the secant method on the elongation (3 rounds)',
    '24': 'once: the 20 terms of the Moon (Meeus ch. 47) as matrices',
    '25': 'M7TX - TEXT: Z row of the base line, Y column, X text -> Y row, X next column (ATEXT Z)',
    '26': 'ATEXT with the row moved by the font\'s base line',
    '27': 'columns shared by the phase symbols',
    '28': 'Z row, Y column, X value -> R31, R30, R34',
    '29': 'the time zone TZ as +h or +h:mm',
    '30': 'the next new Moon, first quarter, full Moon and last quarter after now',
    '31': 'now: elongation, % lit, distance, HP, SD, the last new Moon and the age, the phase number',
    '32': 'one term of the Moon\'s series into the matrices (its multipliers, the sin and cos coefficients)',
    '33': 'the Moon\'s arguments D M M\' F for a Julian Date -> its elongation from the series',
    '34': 'the terminator turned (the other half lit)',
    '35': 'today\'s phase symbol inverted (XOR)',
    '36': 'X (0-99) appended to R49 as two digits',
    '37': 'UT or LT for the clock line',
    '38': 'AS SEEN FROM THE NORTH / SOUTH',
    '39': 'the work matrices M7A M7W M7V set to the same value',
    '40': 'M7HL - horizontal line, X = length in pixels',
    '41': 'M7SY - SYMBOLS: the Moon phase glyphs of the string X (XEQ IND of each character code, 48-55)',
    '42': 'columns shared by the phase symbols',
    '43': 'columns shared by the phase symbols',
    '44': 'columns shared by the phase symbols',
    '45': 'columns shared by the phase symbols',
    '46': 'columns shared by the phase symbols',
    '47': 'the new Moon before, when the one found is after now',
    '56': 'a phase found before now: the next one, a month later',
}
MOON_TABLES = [(('48', '49', '50', '51', '52', '53', '54', '55'), 'XEQ IND table: the eight phase symbols (characters 0-7)'),
               (('60', '61', '62', '63', '64', '65', '66', '67'), 'XEQ IND table: the eight phase names'),
               (('90', '91', '92', '93', '94', '95', '96', '97'), 'XEQ IND table: the characters of the phase symbols')]

# comments inside a program's main part: (step as listed, its occurrence, lines before it, text)
BLOCKS = {
    'NAV': [
        ('1', 1, 0, 'the numbers used most, once into R43-R98: each use is then a 2-byte RCL'),
        ('SSIZE#', 1, 0, 'your stack size kept in "F0"; the 8-level stack while it runs (the fonts read register D)'),
        ('RCL 85', 1, 0, 'work variables of the run; i and i pi/180 as complex numbers ("C1" "C2") for the series'),
        ('STO+ "SBR"', 1, 1, 'the stars in order of brightness, matrix SBR (made once, kept between runs)'),
        ('STO+ "ALMC"', 1, 1, 'the sky cache ALMC, 73 x 4: GHA Dec Hc Zn of the Sun, the Moon, the planets, the stars; '
                              'the sun times (kept between runs: the same inputs show the views at once)'),
        ('"DATE YYYY.MMDD"', 1, 0, 'the four inputs: DATE in the calculator\'s date format, UTC, LAT, LON'),
        ('GRFNT', 1, 1, 'GRFNT 21; the hourglass and the box (06), the sky (03), the menu (04)'),
        ('DO 01', 1, 0, 'the key loop: one key a round; 0 ends (its key code is in R87)'),
        ('PAUSE 50', 1, 0, 'waits for a key: PAUSE 50 shows the screen, KEY? reads the key'),
        ('IF 03', 1, 3, '9 (key code 54): SNAP'),
        ('IF 04', 1, 6, 'the arrows (key codes 51 / 61): one hour later / earlier, the sky again, the menu'),
        ('IF 05', 1, 9, 'keys 1-6 by arithmetic: the row and the column of the key code (72 73 74 / 62 63 64)'),
        ('DO 03', 1, 0, 'the view, drawn again after each arrow while it is shown (+ goes back to the menu)'),
        ('"ALMANAC 47 - INFO"', 1, 1, '6 INFO'),
        ('DELITM "Q2"', 1, 1, '0: the end - the work variables deleted, your stack size back, CLREGS, CLSTK'),
    ],
}
