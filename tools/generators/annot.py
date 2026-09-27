# -*- coding: utf-8 -*-
import os, re, sys
sys.path.insert(0,'/home/claude')
from navdata import SN
SRC='/home/claude/C47_nav/programs'
H={}   # headers
A={}   # anchors: list of (anchor, occurrence, comment)

def glyphs(chars_extra):
    out=[]
    skip=[c for c,d in chars_extra]
    for c in range(32,91):
        ch=chr(c)
        if c in skip or c in (33,34,35,36,38,39,40,41,44,59,60,61,62,63): continue
        out.append(('LBL %02d'%c,1,"glyph '%s' (code %d)"%(ch if ch!=' ' else 'space',c)))
    for c,d in chars_extra: out.append(('LBL %02d'%c,1,d))
    return out

H['SUNA']=["SUNA - Sun GHA/Dec and GHA Aries (VSOP87D truncated, IAU1980 nutation)",
 "IN : X = JD (UT1)", "OUT: X = GHA Sun, Y = Dec Sun, Z = GHA Aries (deg)",
 "     R73 = R (au), R74 = app. longitude, R76 = true obliquity, R80 = GHA Aries",
 "     R60-R64 = D M M' F Omega (deg), R66 = dpsi (\"), R67 = deps (\")",
 "NEEDS: matrices VL VB VR NU (XEQ MATA once)", "REGS: R50-R55 R60-R67 R70-R81"]
A['SUNA']=[('LBL "SUNA"',1,'main entry'),('DEG',1,'T = Julian centuries TT (UT1+69.2s) -> R54, tau = T/10 -> R50'),
 ('RAD',1,'series in radians: L (56 terms), B (3), R (7) via SER'),('INDEX "VL"',1,'heliocentric L -> R71'),
 ('3\nSTO 55',1,'heliocentric B -> R72'),('7\nSTO 55',1,'radius vector R -> R73 (au)'),
 ('RCL 71\n57.295779513082320876798154814105',1,'geocentric longitude = L+180 -> R74, latitude = -B -> R75'),
 ('RCL 74\nRCL 54\n1.397',1,'FK5 correction of lat and lon'),('XEQ "NUT"',1,'nutation dpsi, deps (arcsec) -> R66, R67'),
 ('RCL 66\n3600\n÷\nSTO+ 74',1,'apparent longitude: + dpsi - aberration 20.4898"/R'),
 ('84381.448',1,'true obliquity eps = eps0 + deps -> R76'),('RCL 75\nSIN\nRCL 76',1,'declination -> R77'),
 ('RCL 74\nSIN\nRCL 76\nCOS',1,'right ascension (->POL) -> R78'),('RCL 70\n2451545',1,'GMST + equation of equinoxes = GHA Aries -> R80'),
 ('RCL- 78',1,'GHA Sun = GHA Aries - RA -> R81'),('RCL 80\nRCL 77\nRCL 81',1,'stack Z=Aries Y=Dec X=GHA'),
 ('LBL "SER"',1,'SER: sum A*cos(B+C*tau)*tau^k over the rows of the indexed matrix. Row 1 = header, element 1 = number of terms (R55). Column 1 holds 30+k: each term is added to R30+k, then (R32*tau + R31)*tau + R30, *1E-8'),('LBL 14',1,'FAST series (VL header holds first and end JD): outside the period set flag 12 (X on the screens)'),
 ('LBL 12',1,'loop over rows (DSE 55)'),
 ('LBL "NUT"',1,'NUT: fundamental arguments D M M\' F Omega -> R60-R64, 10-term IAU1980 nutation'),
 ('LBL 13',1,'loop over NU rows: dpsi -> R66, deps -> R67 (0.0001" units, scaled at end)')]

H['MATA']=["MATA - build matrices VL (56x4), VB (3x4), VR (7x4), NU (10x9) for SUNA","Run once. Can be deleted afterwards; never delete the matrices."]
A['MATA']=[('LBL "MATA"',1,'VL: Earth L series (k, A, B, C)'),('3\nENTER\n4\nNEWMAT',1,'VB: Earth B series'),
 ('7\nENTER\n4\nNEWMAT',1,'VR: Earth R series'),('10\nENTER\n9\nNEWMAT',1,'NU: nutation table (5 multipliers, psi A B, eps A B)')]
H['MATST']=["MATST - build star matrix ST (58x4): RA, Dec (J2000, deg), pmRA*cos(dec), pmDec (mas/yr)","Row = almanac star number (58 = Polaris). Run once."]
A['MATST']=[('LBL "MATST"',1,'create ST and fill row by row (STOEL, J+)')]

H['STAR']=["STAR - apparent GHA/Dec/SHA of navigation star","IN : Y = JD (UT1), X = star number 1-58",
 "OUT: X = GHA, Y = Dec, Z = SHA","STR2 = same without SUNA (SUNA already run for this JD; R82 = star no.)",
 "NEEDS: SUNA, matrix ST","REGS: R56-R59 R68-R69 R82-R89 (+ SUNA)"]
A['STAR']=[('LBL "STAR"',1,'save star no. -> R82, run SUNA for JD'),('LBL "STR2"',1,'entry without SUNA: read ST row R82'),
 ('RCL 54\n100',1,'proper motion: years since J2000 = 100T -> R87; RA -> R83, Dec -> R84'),
 ('RCL 54\n0.01801828',1,'IAU 2006 precession angles zeta R56, z R57, theta R58'),
 ('RCL 83\nRCL+ 56',1,'precess: Dec -> R88, RA -> R89 (mean of date)'),
 ('RCL 76\nRCL 67',1,'to ecliptic of date: mean obliquity -> R68, beta -> R57, lambda -> R56'),
 ('RCL 54\n-0.000042037',1,'annual aberration (e, perihelion) + nutation in longitude'),
 ('RCL 57\nSIN\nRCL 76',1,'back to equator (true obliquity): Dec -> R88, RA -> R89'),
 ('360\nRCL- 89',1,'SHA = 360 - RA -> R57, GHA = GHA Aries + SHA -> R59'),('RCL 57\nRCL 88\nRCL 59',1,'stack Z=SHA Y=Dec X=GHA')]

H['CHZ']=["CHZ - sight reduction","CHZ: T = lat, Z = lon (E+), Y = Dec, X = GHA -> X = Hc, Y = Zn",
 "HCZ: same with lat in R91, lon in R92 (used by the screens)","DHA: inverse. T lat, Z lon, Y Hc, X Zn -> X Dec, Y LHA, Z GHA",
 "REGS: R91 lat, R92 lon, R94 Dec, R95 LHA, R96 Hc, R97 Zn"]
A['CHZ']=[('LBL "CHZ"',1,'store lat R91, lon R92, fall into HCZ'),('LBL "HCZ"',1,'LHA = GHA + lon -> R95, Dec -> R94'),
 ('RCL 91\nSIN\nRCL 94',1,'Hc = asin(sin lat sin dec + cos lat cos dec cos LHA) -> R96'),
 ('RCL 94\nCOS\nRCL 95',1,'Zn = atan2(-cos dec sin LHA, cos lat sin dec - sin lat cos dec cos LHA) -> R97'),
 ('LBL "DHA"',1,'inverse: store lat, lon, Zn R97, Hc R96'),('RCL 91\nSIN\nRCL 96',1,'Dec = asin(sin lat sin Hc + cos lat cos Hc cos Zn) -> R94'),
 ('RCL 97\nSIN\nRCL 96',1,'LHA from atan2 -> R95'),('RCL 95\nRCL- 92',1,'GHA = LHA - lon; stack Z=GHA Y=LHA X=Dec')]

H['SUNRISE']=["SUNRISE - Sun events for one UT date at a position","IN : Z = JD at 0h UT, Y = lat (N+), X = lon (E+)",
 "XEQ RISE / SET (-0 50'), CTWA / CTWP (-6), NTWA / NTWP (-12), TRAN (meridian passage)",
 "OUT: X = UT hours (99 = no event)","NEEDS: SUNA   REGS: R90-R99"]
A['SUNRISE']=[('LBL "RISE"',1,'h0 = -0.8333 (R93), morning sign -1 (R95)'),('LBL "SET"',1,'h0 = -0.8333, evening +1'),
 ('LBL "NTWA"',1,'nautical twilight AM, h0 = -12'),('LBL "NTWP"',1,'nautical twilight PM'),('LBL "CTWA"',1,'civil twilight AM, h0 = -6'),
 ('LBL "CTWP"',1,'civil twilight PM'),('LBL "TRAN"',1,'meridian passage (sign 0)'),
 ('LBL 21',1,'store JD0 R90, lat R91, lon R92'),('LBL 20',1,'first guess t = 12 + 6*sign hours -> R94, max 10 iterations R97'),
 ('LBL 22',1,'iteration: SUNA at JD0 + t/24; GHA R98, Dec R99'),('LBL 25',1,'correction dt = (LHA target - GHA - lon) / 15, wrap +-180'),
 ('LBL 24',1,'converged (|dt| < 0.0003 h, about 1 s): X = t'),('LBL 29',1,'no event (|cos| > 1): X = 99')]

H['PHAS']=["PHAS - Moon % illuminated and age","IN : X = JD (UT1)","OUT: X = % illuminated, Y = age (days since true new moon)",
 "PHA2: same, when SUNA has just run for this JD (the screens call it right after SUNA)",
 "NEEDS: SUNA (uses D M M' F from R60-R63)","REGS: R30-R33 R51 R53 R56 R57 (scratch only)"]
A['PHAS']=[('LBL "PHAS"',1,'run SUNA for the mean lunar arguments'),('LBL "PHA2"',1,'PHA2: entry when SUNA has already run'),('180\nRCL- 60',1,'phase angle i (Meeus 48.4); cos i -> R57'),
 ('RCL 60\n360\nMOD',1,'first guess days since mean new moon = D/12.1907 -> R32; flag R31 = 0'),
 ('LBL 40',1,'arguments at new moon: M -> R53, M\' -> R51, F -> R33; true new moon correction; age -> R56'),
 ('LBL 46',1,'second try gave negative age: keep first result (R30)'),('LBL 44',1,'first pass: check age range'),
 ('LBL 41',1,'age < 0: use previous lunation (+29.53 d)'),('LBL 42',1,'age > 27: try next lunation (-29.53 d)'),
 ('LBL 43',1,'output: Y = age, X = (1 + cos i) * 50')]

H['SUNSD']=["SUNSD - Sun semi-diameter","IN : X = JD","OUT: X = SD in arcmin = 15.99383 / R (959.63\" at 1 au)","NEEDS: SUNA (R73)"]
A['SUNSD']=[('LBL "SUNSD"',1,'SUNA leaves R in R73; SD = 15.99383 / R')]

H['ALM']=["ALM - Chebyshev tables (Method B): Sun, Aries, Moon, planets","Store R01 n, R02 span (h), GHA coef R10.., Dec coef R20.., Moon HP R30-R33",
 "IN : X = t (hours since block start)","OUT: X = GHA, Y = Dec;  XEQ HP -> X = HP (arcmin)","REGS: R01-R09 R10-R33 R40-R41"]
A['ALM']=[('LBL "ALM"',1,'x = 2t/span - 1 -> R03; GHA series (base R10) -> R40, Dec (base R20) -> R41'),
 ('LBL "HP"',1,'Moon horizontal parallax: 4 terms from R30'),('LBL "CHEB"',1,'Clenshaw sum; R08 = base register, R01 = n terms'),
 ('LBL 11',1,'recurrence b_k = 2x b_k+1 - b_k+2 + c_k (RCL+ IND 06)')]

H['HORZ']=["HORZ - sky chart Hc/Zn (full screen): the same bodies as ALMF/HALMV/ALMT (Sun always; Moon and planets",
 "  above the horizon; brightest stars higher than 10 deg until 10 bodies), then an info line per object",
 "  ('MOON ZN .. HC ..', '18 SIRIUS ZN ..', PAUSE 30 each), endless: after the last the first again. R/S or EXIT stops.",
 "  The Sun below the horizon is not drawn but has its info line (HC with a minus sign).",
 "IN : Z = JD, Y = lat, X = lon (E+)",
 "Symbols (PTXB): @ Sun, ( Moon crescent, < Venus, > Mars, = Jupiter, ? Saturn, * star + number",
 "Objects are kept in matrix HZT (id, Zn, Hc): id 0 Sun, -1 Moon, -2..-5 planets, n star",
 "Screen mapping: column R98 = 20 + Zn*375/360, row R99 (from top) = 225 - Hc*200/90; C47 y = 241 - row",
 "NEEDS: SUNA STAR(STR2) CHZ MOON(MOO2) PLAN(PLN2) SBRT SNMU PTXT PTXB + matrices",
 "REGS: R10-R14, R36 R37 R42 R44 R82 R86 R90-R99 (+ SUNA, STAR, MOON, PLAN)"]
A['HORZ']=[('LBL "HORZ"',1,'store JD R90, lat R91, lon R92; clear screen'),('16\n20\n376',1,'horizon line y = 16 (PHL)'),
 ('LBL 50',1,'Hc axis x = 18, dotted every 3 px'),('15\n20\nPIXEL',1,'Zn tick marks every 30 deg'),
 ('83\n15\nPIXEL',1,'Hc ticks and labels 30 60 90 (PTNS)'),('0\nSTO 44',1,'north: letters N E S W N, offset R44 = 0'),
 ('LBL 38',1,'south latitude: S W N E S, offset R44 = 180 (chart centred on N)'),
 ('LBL 37',1,'SUNA once; object table HZT; dotted celestial equator'),('RCL 77\nRCL 81\nXEQ 52',1,'Sun: always recorded (as ALMF), drawn only above the horizon (LBL 56)'),
 ('XEQ "MOO2"',1,'Moon (MOO2 = MOON without repeating SUNA)'),('1.004',1,'planets 1-4 (PLN2 = PLAN without SUNA)'),
 ('1.058',1,'stars in order of brightness (SBRT) higher than 10 deg until 10 bodies (R10), as ALMF'),
 ('RCL 10\nX=0?',1,'info loop over the objects in HZT'),('LBL 35',1,'read id, Zn, Hc; clear top strip; name'),
 ('LBL 32',1,'Moon or planet name (LBL 81-85)'),('LBL 31',1,'text SUN'),('LBL 30',1,'ZN value HC value (PT1, minus sign by LBL 33), PAUSE 30, next; after the last the first again (LBL 34)'),
 ('LBL 40',1,'record object X = id with Zn R97, Hc R96 in HZT (count R10)'),
 ('LBL 47',1,'draw Moon symbol, record'),('LBL 48',1,'draw planet symbol (LBL 71-74), record'),('LBL 43',1,'draw star + number, record'),
 ('LBL 71',1,'planet symbols: < Venus, > Mars, = Jupiter, ? Saturn'),('LBL 81',1,'names for the info line'),
 ('LBL 55',1,'plot one pixel at row R99, column R98'),('LBL 52',1,'HCZ, then column R98 and row R99'),
 ('LBL 56',1,'sun symbol centred on the point (PTXB @)'),('LBL 57',1,'star centred on the point (PTXB *), number to the right (PTNS)'),
 ('LBL 39',1,'near the right edge: number 17 px to the left')]
H['HORZS']=["HORZS - same chart as HORZ (same bodies as ALMF) without the info line; holds it with 3 x PAUSE 99",
 "IN : Z = JD, Y = lat, X = lon","NEEDS: as HORZ"]
A['HORZS']=[a for a in A['HORZ'] if a[0] not in ('RCL 10\nX=0?','LBL 35','LBL 32','LBL 31','LBL 30','LBL 81')]
A['HORZS'][0]=('LBL "HORZS"',1,'store JD R90, lat R91, lon R92; clear screen')
A['HORZS'].append(('LBL 21',1,'hold screen: 3 x PAUSE 99 (R37)'))
H['SBRT']=["SBRT - star number by brightness","IN : X = k (1 = brightest ... 58)   OUT: X = almanac star number",
 "Order by visual magnitude: 18 Sirius, 17 Canopus, 38 Rigil Kent, 37 Arcturus, 49 Vega, 12 Capella, 11 Rigel ..."]
A['SBRT']=[('LBL "SBRT"',1,'jump to label k')]
H['HPLT']=["HPLT - Hc/Zn dot plot with the statistics plot (PLSTAT)","IN : Z = JD, Y = lat, X = lon","Clears stats, Sigma+ (x = Zn, y = Hc) for Sun and stars above horizon"]
A['HPLT']=[('LBL "HPLT"',1,'store inputs, clear statistics, Sun'),('LBL 51',1,'star loop 1-58'),('PLSTAT',1,'show plot'),
 ('LBL 50',1,'add point (Zn, Hc)'),('LBL 52',1,'HCZ; X = Zn')]

HOW=['HOW A GLYPH IS DRAWN (AGRAPH):', '  AGRAPH reg draws one column: bit 0 of the short integer in reg at (x,y), bit 1 at y+1 ... up to WSIZE bits,', '  then adds 1 to X. So each glyph does: RCL 31 (y), RCL 30 (x), then per column:', '  <mask>#2  STO 32  R-down  AGRAPH 32   (mask written top row first, e.g. 1001000#2)', '  empty columns are skipped with  n +  ; at the end  n + STO 30  stores the next x.', 'WHY WSIZE 8: alpha->x returns the character code as a short integer of the current word size;', '  with 7 bits (signed, max 63) letters (65-90) give OUT OF RANGE. 8 bits hold codes up to 127', '  and the 7-pixel columns; bit 7 is always 0 so nothing extra is drawn.']
H['PTXT']=["PTXT - draw text with AGRAPH columns, 3x5 font","IN : Z = y, Y = x, X = string   OUT: Y = y, X = next x",
 "Characters 0-9 A-Z space + - . / :  * = star  @ = sun","PTNS integer, PT1 one decimal: Z = y, Y = x, X = value -> Y = y, X = next x","Glyphs = AGRAPH columns (WSIZE 8), word size set back to 64 at the end","REGS: R30 x, R31 y, R32 code / column mask, R33 string copy, R34-R35 numbers"]+HOW
A['PTXT']=[('LBL "PTXT"',1,'store string R33, x R30, y R31'),('LBL "PTNS"',1,'PTNS: Z = y, Y = x, X = integer 0-999 -> digits'),('LBL "PT1"',1,'PT1: number with one decimal'),('LBL 13',1,'common entry: value R34, x R30, y R31, WSIZE 8'),('LBL 10',1,'draw integer R34 without leading zeros'),('LBL 11',1,'digit X -> glyph'),('LBL 14',1,'code X -> glyph'),('LBL 01',1,'loop: length 0 -> done; take first code (removed); glyph draws columns with AGRAPH and advances R30'),
 ('LBL 02',1,'return Y = y, X = next x'),('LBL 32',1,'space: advance only')]+glyphs([(42,'star symbol (5x5), extra advance'),(64,'sun symbol (5x5), extra advance')])
H['PTXB']=["PTXB - draw text with AGRAPH columns, 5x7 font; number helpers","PTXB: Z = y, Y = x, X = string -> Y = y, X = next x",
 "PINB integer | PF1 one decimal | PHM hh:mm (>=98 -> --:--) | PDM sign ddd mm.m | PZN ddd.d | PDAT JD -> DD-MM-YYYY",
 "All: Z = y, Y = x, X = value -> Y = y, X = next x","* = star (2 cells), @ = sun (2 cells), % available","Glyphs = AGRAPH columns (WSIZE 8; sun WSIZE 12); word size set back to 64 at the end","PHL: Z = y, Y = x, X = length -> horizontal line","REGS: R30 x, R31 y, R32 code / column mask, R33 string, R34-R36 number work"]+HOW
A['PTXB']=[('LBL "PTXB"',1,'store string R33, x R30, y R31'),('LBL 01',1,'loop: length 0 -> done; first code (removed); glyph draws its columns with AGRAPH, advances R30'),
 ('LBL 02',1,'common return: Y = y, X = next x'),('LBL "PHL"',1,'PHL: horizontal line, Z = y, Y = x, X = length (AGRAPH 1 px columns)'),('LBL 21',1,'line loop'),
 ('LBL 03',1,'draw character code X (glyph advances x)'),('LBL 04',1,'draw digit X (code 48+X)'),('LBL 05',1,'common entry: value R34, x R30, y R31'),
 ('LBL "PINB"',1,'PINB: rounded integer 0-999'),('LBL 06',1,'draw integer in R35 without leading zeros'),('LBL 11',1,'skip hundreds'),('LBL 12',1,'units'),
 ('LBL "PF1"',1,'PF1: integer part, point, 1 decimal'),('LBL "PHM"',1,'PHM: X >= 98 -> --:-- (SUNRISE gives 99 = no event); else minutes = hours x 60 rounded, hh = min/60 mod 24'),('LBL 07',1,'no event: --:--'),
 ('LBL "PDM"',1,'PDM: |value| x 600 rounded = tenths of arcmin -> R35; degrees -> R36; R35 = remaining tenths (0-599)'),('RCL 36\n99\nX<Y?',1,'right-align degrees: one blank cell if < 100, another if < 10 (6 STO+ 30 = one cell)'),
 ('LBL 15',1,'hundreds present'),('LBL 16',1,'sign cell (- or blank)'),('LBL 13',1,'minus'),('LBL 14',1,'draw sign'),('LBL 17',1,'tens digit'),('LBL 18',1,'units digit, space, minutes tens + units (R35/100, R35/10 mod 10), point, tenths (R35 mod 10)'),
 ('LBL "PDAT"',1,'PDAT: JD -> calendar (Meeus ch.7, Gregorian): Z = IP(JD+0.5) -> A -> B -> C -> D -> E; day R35, month R34, year R36'),('LBL 08',1,'month - 12'),('LBL 10',1,'January/February: year + 1'),('LBL 20',1,'draw 2 digits'),
 ('LBL "PZN"',1,'PZN: bearing ddd.d with leading zeros'),('LBL 19',1,'360.0 -> 000.0')]+glyphs([(42,'star symbol (7x7, HORZ), 2 cells'),(64,'sun symbol (11x11, HORZ), 2 cells'),(40,'( Moon crescent, 2 cells'),(60,'< Venus symbol, 2 cells'),(62,'> Mars symbol, 2 cells'),(61,'= Jupiter symbol, 2 cells'),(63,'? Saturn symbol, 2 cells')])

H['SNMU']=["SNMU - star name in capitals","IN : X = star number 1-58   OUT: X = name (string, no display)","REGS: R49"]
A['SNMU']=[('LBL "SNMU"',1,'jump to label = star number')]+[('LBL %02d'%i,1,'%d %s'%(i,SN[i-1])) for i in range(1,59)]
H['SNAM']=["SNAM - star name with number, shown with AVIEW 38","IN : X = star number   OUT: R38 = \"nn Name\"","REGS: R38 R49"]
A['SNAM']=[('LBL "SNAM"',1,'jump to label = star number (alphabetical list)'),('LBL 99',1,'store name in R38 and show')]

common_screen=[('LBL 26',1,'push Z = JD 0h of the UT date, Y = lat, X = lon for SUNRISE'),('LBL 28',1,'text WANING'),('LBL 22',1,'text S'),('LBL 27',1,'text W')]
H['HALMV']=["HALMV - chart left, almanac data right: Sun, Moon and planets above the horizon, then the brightest stars","IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)",
 "  higher than 10 deg until the table has 10 rows","NEEDS: SUNA STAR CHZ SUNRISE PHAS MOON PLAN SBRT SNMU PTXB + matrices","REGS: R10 JD R11 lat R12 lon R13-R17 times R18-R19 Moon phase R21 Moon HP R22 Moon SD R29 Sun SD R37 R40-R48"]
A['HALMV']=[('LBL "HALMV"',1,'store JD R10, lat R11, lon R12'),('XEQ 26',1,'sun times: NTWA R13 RISE R14 TRAN R15 SET R16 NTWP R17'),
 ('XEQ "PHA2"',1,'Moon: % R18, age R19 (PHA2 reuses this SUNA)'),('RCL 10\nSTO 90',1,'restore JD/lat/lon in R90-R92 for HCZ, clear screen'),
 ('0\n-201\nPIXEL',1,'vertical divider at x = 201 (one PIXEL, negative x)'),('14\n18\n179',1,'horizon line y = 14 (PHL)'),('14.214',1,'Hc axis x = 17'),('80\n15\nPIXEL',1,'ticks and labels 30 60 90'),
 ('0\nSTO 44',1,'compass letters; north: N E S W N'),('LBL 23',1,'south latitude: S W N E S, offset R44 = 180'),
 ('LBL 24',1,'SUNA: GHA R45, Dec R46, Aries R48; SD R29'),('0\nSTO 47\nLBL 14',1,'dotted celestial equator every 3 deg'),
 ('230\n206\n"DR"',1,'right side: DR line'),('220\n206',1,'date and UT'),('210\n206',1,'Aries and Sun SD'),('200\n206',1,'Sun GHA and Dec'),
 ('188\n236',1,'table header'),('178\nSTO 40',1,'Sun row (R40 = row y)'),('1\nSTO 41',1,'rows in the table R41 (Sun = 1)'),('XEQ "MOO2"',1,'Moon: GHA R45, Dec R46, HP R21, SD R22; row if above the horizon (LBL 61)'),
 ('1.004',1,'planets 1-4 (PLN2); row if above the horizon (LBL 63)'),('LBL 17',1,'stars by brightness (SBRT), Hc > 10 deg, until 10 rows'),('LBL 18',1,'next star'),('LBL 19',1,'bottom block: separator line (PHL)'),
 ('76\n206',1,'sun times table'),('39\n204',1,'separator, Moon line'),('3\nSTO 37',1,'hold screen 3 x PAUSE 99'),
 ('LBL 15',1,'plot equator dot'),('LBL 16',1,'sun symbol on chart'),('LBL 52',1,'HCZ; column R98 = 18 + Zn*178/360, row R99 = 14 + Hc*200/90'),
 ('LBL 57',1,'star symbol + number on chart'),('LBL 21',1,'label near right edge: 22 px left'),('8\n230',1,'warning line (PTXT small font)'),('LBL 60',1,'table row: Hc (PDM), Zn (PZN); next row -10'),('LBL 61',1,'Moon: symbol on chart and table row'),('LBL 63',1,'planet: symbol on chart (LBL 71-74) and table row with name (LBL 82-85)'),('LBL 71',1,'planet symbols < > = ?'),('LBL 82',1,'planet names'),('LBL 64',1,'Hc < 0 (body below the horizon): 54 px underline under the Hc value (PHL)')]+common_screen
H['ALMF']=["ALMF - full-page almanac screen, same table rule as HALMV (10 rows): Sun, then Moon and planets above the horizon,",
 "  then the brightest stars higher than 10 deg; GHA Dec Hc Zn; bottom line: DOES NOT REPLACE THE NAUTICAL ALMANAC","IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)","Moon HP and SD in the bottom block","NEEDS: as HALMV   REGS: as HALMV"]
A['ALMF']=[('LBL "ALMF"',1,'store JD R10, lat R11, lon R12'),('XEQ 26',1,'sun times R13-R17'),('XEQ "PHA2"',1,'Moon R18 R19 (PHA2 reuses this SUNA)'),
 ('RCL 10\nSTO 90',1,'restore R90-R92, clear screen'),('RCL 10\nXEQ "SUNA"',1,'Sun GHA R45 Dec R46 Aries R48, SD R29'),
 ('229\n4',1,'top line: date, UT, DR, Aries'),('-219\n0\nPIXEL',1,'separator (one PIXEL, negative y = full line)'),('207\n34',1,'table header'),('194\nSTO 40',1,'Sun row'),
 ('1\nSTO 41',1,'rows in the table R41 (Sun = 1)'),('XEQ "MOO2"',1,'Moon: HP R21, SD R22; row if above the horizon (LBL 61)'),('1.004',1,'planet rows if above the horizon (PLN2, LBL 63)'),('LBL 17',1,'stars by brightness (SBRT), Hc > 10 deg, until 10 rows'),('-22\n0\nPIXEL',1,'separator and the warning line'),('LBL 18',1,'next star'),
 ('LBL 19',1,'separator (one PIXEL)'),('69\n4',1,'sun times, Moon, SD, notes'),('3\nSTO 37',1,'hold screen'),
 ('LBL 60',1,'table row: GHA, N/S + Dec, Hc, Zn; next row -11'),('LBL 16',1,'planet loop'),('LBL 61',1,'Moon row'),('LBL 63',1,'planet row: symbol (LBL 71-74), name (LBL 82-85)'),('LBL 71',1,'planet symbols < > = ?'),('LBL 82',1,'planet names'),('LBL 64',1,'Hc < 0 (body below the horizon): 54 px underline under the Hc value (PHL)')]+common_screen
H['HALM']=["HALM - chart top half, table bottom half","IN : Z = JD, Y = lat, X = lon","NEEDS: SUNA STAR CHZ SNMU PTXB   REGS: R20-R28 R37 R40-R47 R90-R99"]
A['HALM']=[('LBL "HALM"',1,'store inputs, clear screen'),('0.399',1,'separator y = 118'),('20.395',1,'horizon y = 130'),('130.226',1,'Hc axis'),
 ('162\n17',1,'ticks and labels'),('0\nSTO 44',1,'compass letters (north)'),('LBL 23',1,'south'),('LBL 24',1,'SUNA; equator dots'),
 ('RCL 46\nRCL 45\nXEQ 52',1,'Sun position; table header'),('0\nSTO 41',1,'star selection'),('LBL 17',1,'star loop'),('LBL 18',1,'next star'),
 ('LBL 19',1,'hold screen'),('LBL 15',1,'equator dot'),('LBL 16',1,'sun symbol'),('LBL 52',1,'HCZ + screen mapping (top half)'),
 ('LBL 57',1,'star + number'),('LBL 21',1,'label near edge'),('LBL 60',1,'table row GHA Dec Hc Zn'),('LBL 22',1,'text S')]
H['NAV']=["NAV - start menu with prompts","1 = ALMF, 2 = HALMV, 3 = MATA + MATST + MATM + MATP, 4 = ALMT (text), 0 = end",
 "Asks DATE (YYYY.MMDD), UTC (HH.MMSS), LAT, LON (DD.MM, S/W negative)","REGS: R01-R08 R38 R39, variables DATE UTC LAT LON"]
A['NAV']=[('LBL 01',1,'menu prompt; choice -> R38'),('LBL 10',1,'1: almanac page'),('LBL 11',1,'2: horizon + data'),('LBL 12',1,'3: build all matrices (MATA, MATST, MATM, MATP)'),
 ('LBL 13',1,'4: text almanac ALMT'),('LBL 20',1,'inputs; date -> Y R01 M R02 D R03'),('RCL "UTC"',1,'time HH.MMSS -> hours R04'),('RCL 02\n3',1,'Jan/Feb -> previous year'),
 ('RCL 01\n100\n÷\nIP\nSTO 05',1,'Gregorian B -> R05; JD -> R06'),('RCL "LAT"',1,'lat, lon to degrees R07 R08; stack Z JD Y lat X lon'),
 ('LBL 30',1,'DD.MM -> degrees'),('LBL 31',1,'M = M + 12, Y = Y - 1')]
for d in ('PTDEMO','PTBDEM','PTFULL'):
    H[d]=["%s - demo screen for the pixel font"%d]; A[d]=[('LBL 21',1,'hold screen 3 x PAUSE 99')]


H['MATM']=["MATM - build Moon matrices (run once): ML 60x6 and MB 60x6 = Meeus ch.47 (ELP-2000/82 truncated),",
 "  columns D M M' F  sin-coef  cos-coef ; MCL 40x6 / MCB 15x6 = extra terms fitted to JPL DE421 2000-2050 (1E-6 deg)"]
A['MATM']=[('LBL "MATM"',1,'ML: longitude (sin, 1E-6 deg) and distance (cos, 1E-3 km) terms'),('60\nENTER\n6\nNEWMAT\nSTO "MB"',1,'MB: latitude terms (sin, 1E-6 deg; cos column 0)'),
 ('40\nENTER\n6\nNEWMAT',1,'MCL: longitude correction terms (sin and cos, 1E-6 deg)'),('15\nENTER\n6\nNEWMAT',1,'MCB: latitude correction terms')]
H['MATP']=["MATP - build planet matrices (run once): VSOP87D truncated, rows k A B C (like VL)",
 "  EEL EEB EER Earth (93 terms) | VNL VNB VNR Venus | MAL MAB MAR Mars | JUL JUB JUR Jupiter | SAL SAB SAR Saturn",
 "  MATP can be deleted after running; never delete the matrices"]
A['MATP']=[('LBL "MATP"',1,'Earth L B R for the planets (more terms than SUNA uses)')]
H['MOON']=["MOON - apparent GHA, Dec, HP and SD of the Moon","IN : X = JD (UT1)   (MOO2: no input, after SUNA)","OUT: X = GHA, Y = Dec (deg), Z = HP ('), T = SD (')",
 "Meeus ch.47 (60+60 terms) + 55 fitted terms: max 0.12', 99% < 0.07', rms 0.02' vs JPL 2000-2050",
 "NEEDS: SUNA (+VL VB VR NU), matrices ML MB MCL MCB (XEQ MATM once)","REGS: R00-R09, R35-R39 (+ SUNA)"]
A['MOON']=[('LBL "MOON"',1,'SUNA for T (R54), nutation (R66), true obliquity (R76), GHA Aries (R80)'),('LBL "MOO2"',1,'MOO2: entry when SUNA has already run for this JD'),
 ('DEG',1,"mean arguments L' R00, D R01, M R02, M' R03, F R04 (deg), E R05"),
 ('0\nSTO 06\nSTO 07\nSTO 08',1,'sums: longitude R06, distance R07, latitude R08; each matrix via LBL 20 (R35/R36 = target registers)'),
 ('RCL 54\n131.849',1,'additive terms A1 A2 A3 (Venus, Jupiter, flattening) and fitted constant + T trend'),
 ('RCL 06\n1E6',1,'lambda = L\' + sum + dpsi -> R38, beta -> R39, distance km -> R07'),
 ('RCL 39\nSIN\nRCL 76',1,'declination -> R08'),('RCL 38\nSIN\nRCL 76',1,'right ascension (->POL), GHA = GHA Aries - RA -> R06'),
 ('6378.14',1,'HP = asin(6378.14/dist) -> R05, SD = 358473400/dist/60 -> R04 (arcmin)'),
 ('LBL 20',1,'loop over matrix rows (R09 = rows): angle = dD + mM + m\'M\' + fF, E^|m|'),('LBL 21',1,'row: sin term to IND R35, cos term to IND R36')]
H['PLAN']=["PLAN - apparent GHA, Dec, SHA of Venus, Mars, Jupiter, Saturn","IN : Y = JD (UT1), X = planet 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn   (PLN2: X = planet, after SUNA)",
 "OUT: X = GHA, Y = Dec, Z = SHA (deg), T = HP (')","VSOP87D truncated, light-time (2 iterations), FK5, aberration, nutation: max 0.065' vs JPL 2000-2050",
 "PLN3 (used by the screens): quick position from mean Keplerian elements (Standish, within 0.2 deg).",
 "  Hc <= -1 deg (lat R91, lon R92): returns the quick GHA/Dec (not shown). Else the series once, light time",
 "  from the quick distance. Same values as PLN2 within 0.0002'. With the tables (flag 10) it is PLN2.",
 "NEEDS: SUNA (+VL VB VR NU; SER), CHZ (PLN3), matrices from MATP",
 "REGS: R00-R09, R34-R39 (+ SUNA); PLN3 also R30-R33 R51-R53 R56-R59 R68 R69 (scratch)"]
A['PLAN']=[('LBL "PLAN"',1,'planet no. R09; SUNA for T, tau, nutation, obliquity, GHA Aries'),('LBL "PLN2"',1,'PLN2: X = planet, SUNA already run for this JD (tau = T/10)'),('RCL 03\nX=Y?',1,'Earth already computed for this tau (R03)? then skip to LBL 28'),('INDEX "EEL"',1,'Earth heliocentric L R00, B R01, R R02 (radians, au); computed once for the four planets'),
 ('0\nSTO 08',1,'light-time iteration (2 passes): planet at tau - lt; PLN3 enters at LBL 27 with lt R08 and 1 pass R07'),('LBL "PLN3"',1,'PLN3: Earth and planet from mean elements (LBL 50, elements LBL 60-64), geocentric distance R58, RA/Dec, GHA = GHA Aries - RA, HCZ'),('LBL 26',1,'above -1 deg: full series once, light time = distance * 0.0057755183 d'),('LBL 50',1,'heliocentric x R31, y R33, z R30 of body X from mean elements; Kepler equation 4 iterations'),('LBL 60',1,'elements a e I L varpi Omega = c0 + c1 T (T = R54) -> R30 R31 R32 R33 R51 R53: 60 Earth-Moon barycentre, 61-64 planets'),('LBL 30',1,'pass: planet series (LBL 11-14), geocentric x R35, y R36, z R37, distance R34, lt R08'),
 ('RCL 36\nRCL 35\n→POL',1,'geocentric longitude R39, latitude R38 (deg)'),('RCL 39\nRCL 54\n1.397',1,'FK5 correction'),
 ('RCL 00\n57.29577951308232',1,'annual aberration (sun, e, perihelion) + nutation in longitude'),
 ('RCL 38\nSIN\nRCL 76',1,'declination R06, RA R05'),('RCL 80\nRCL- 05',1,'GHA R04, SHA R05, HP = 8.794"/D R07'),
 ('LBL 11',1,'Venus L B R -> R04 R05 R06'),('LBL 12',1,'Mars'),('LBL 13',1,'Jupiter'),('LBL 14',1,'Saturn')]


H['STXT']=["STXT - numbers to text strings (for PROMPT / AVIEW lines)","All: X = value -> X = string",
 "SDM  deg min: -8 52.7 -> \"-8°52.7'\"   SNS N/S + deg min   SEW E/W + deg min   SZN \"271.2°\"",
 "SHM  hours -> \"hh:mm\" (>= 98 -> --:--)   SF1 one decimal   SINT whole number   SDAT JD -> \"DD-MM-YYYY\"",
 "Builds the string in R38 piece by piece (R37 = 0: empty); digits from labels 50-59","REGS: R30-R39"]
A['STXT']=[('LBL "SDM"',1,'SDM: tenths of arcmin R35, degrees R36; sign, degrees, °, minutes, point, tenth, apostrophe'),
 ('LBL "SNS"',1,'SNS: "N " or "S " + SDM(|x|)'),('LBL "SEW"',1,'SEW: "E " or "W " + SDM(|x|)'),('LBL "SZN"',1,'SZN: ddd.d° with leading zeros'),
 ('LBL "SHM"',1,'SHM: hh:mm rounded to the minute'),('LBL 08',1,'no event'),('LBL "SF1"',1,'SF1: one decimal'),('LBL "SINT"',1,'SINT: whole number'),
 ('LBL "SDAT"',1,'SDAT: JD -> calendar date (Meeus ch.7)'),('LBL 20',1,'entry: value R34, empty string (R37 = 0)'),('LBL 09',1,'two digits'),
 ('LBL 06',1,'whole number 0-999 without leading zeros'),('LBL 01',1,'append digit X (label 50+X gives the digit as text)'),
 ('LBL 02',1,'append string X to R38 (first piece: R38 = X)'),('LBL 50',1,'digit strings "0" - "9"')]
H['ALMT']=["ALMT - text almanac: no drawing; one line per R/S with PROMPT, starts over after the last line, EXIT to stop",
 "IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)",
 "Lines: date + UT, DR, GHA Aries, then per body: name HC ZN / GHA DEC (Moon also HP SD),",
 "  sun times, Moon phase and age, warning. Bodies: same rule as ALMF/HALMV (10: Sun, Moon + planets above",
 "  the horizon, brightest stars > 10 deg), kept in matrix ALT (id, GHA, Dec, Hc, Zn)",
 "Two lines per R/S (PROMPT). The C47 font is proportional and PROMPT wraps at a space when the",
 "  next word does not fit in 400 px, so R43 counts the pixel width of the line and line 1 is padded",
 "  with spaces (8 px) up to 400 px: line 2 then starts at the left edge. Columns are placed by pixels.",
 "NEEDS: SUNA STAR CHZ SUNRISE PHAS MOON PLAN SBRT SNMU STXT CWID + matrices (no PTXB/PTXT)",
 "REGS: R10-R29, R40-R49, R82 (+ called programs)"]
A['ALMT']=[('LBL 92',1,'Hc < 0 (body below the horizon): line starts with "* "'),('LBL "ALMT"',1,'store JD R10, lat R11, lon R12; sun times R13-R17; Moon phase R18 R19; SUNA, Sun SD R29'),
 ('10\nENTER\n5\nNEWMAT',1,'body table ALT; Sun, Moon, planets, stars recorded with LBL 40'),
 ('LBL 01',1,'text pages: each line is built in R20 (LBL 90 appends) and shown with PROMPT 20 (LBL 91)'),
 ('1\nSTO 24',1,'body lines: name HC ZN, then GHA DEC; Moon: HP SD'),('1\nSTO+ 24',1,'next body'),
 ('"NAUT TWI "',1,'sun times, Sun SD, Moon, warning; then start over'),
 ('LBL 40',1,'record body X = id with GHA R45, Dec R46, Hc R96, Zn R97'),('LBL 70',1,'body name: 0 SUN, -1 MOON, -2..-5 planets (LBL 80-85), n = number + star name'),
 ('LBL 80',1,'names (replace with symbols here if your C47 font has them)'),('LBL 90',1,'append X to the line R20'),('LBL 91',1,'show the page (two lines) and wait for R/S'),
 ('LBL 76',1,'append formatted number Y; width 8 px per character + X (-3 for one . or :)'),
 ('LBL 77',1,'N/S letter width correction -> R47'),('LBL 79',1,'E/W letter width correction -> R47'),
 ('LBL 68',1,'line = X, width measured character by character with CWID'),
 ('LBL 86',1,'append X, width measured with CWID'),('LBL 89',1,'pad with spaces while width + 8 <= X pixels')]
H['CWID']=["CWID - pixel width of one character in the C47 standard font (PROMPT line = 400 px)",
 "IN : X = character code (space, *, 0-9, A-Z)   OUT: X = width in pixels",
 "Used by ALMT to pad line 1 so that line 2 starts at the left edge.   REGS: R49"]
A['CWID']=[('GTO IND 49',1,'jump to the label = character code')]


H['ALMS']=["ALMS - short almanac page: same layout as ALMF with Sun, Moon (if above the horizon), the first planet",
 "  above the horizon in the order Venus, Jupiter, Mars, Saturn (LBL 91-94) and the 3 brightest stars higher than 10 deg",
 "IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)   Generated by tools/generators/genf.py short",
 "NEEDS: as ALMF   REGS: as ALMF + R24 (planet loop, star count)"]
H['HALMH']=["HALMH - horizon chart on top (full width, Zn 0-360 over 375 px, Hc 90 deg = 96 px, horizon y 118),",
 "  short almanac table below (as ALMS: BODY GHA DEC HC ZN), Sun times and Moon % on one line",
 "IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)   Generated by tools/generators/genhh.py",
 "NEEDS: SUNA STAR CHZ SUNRISE PHAS MOON PLAN SBRT SNMU PTXB PTXT + matrices",
 "REGS: R10-R22 R24 R29 R37 R40-R48 R82 R90-R99"]
A['HALMH']=[('LBL 12',1,'Hc axis x = 18, dotted every 3 px'),('LBL 13',1,'celestial equator, a dot every 3 deg of GHA'),
 ('LBL 17',1,'first planet above the horizon: Venus, Jupiter, Mars, Saturn (LBL 91-94 give the planet number)'),
 ('LBL 30',1,'the 3 brightest stars higher than 10 deg (count R24)'),('LBL 52',1,'HCZ, then chart column R98 and row R99'),
 ('LBL 60',1,'table row: GHA, N/S + Dec, Hc (underlined when < 0), Zn; next row -11')]

H['BODY']=["BODY - one body at a time. IN: Z = JD (UT1), Y = lat (N+), X = lon (E+). Generated by genbody.py",
 "1 List of the bodies above the horizon (text pages, R/S = next page): 60 SUN, 61 MOON, 62 VENUS, 63 MARS,",
 "  64 JUPITER, 65 SATURN, stars by NA number, brightest first. Quick positions: Sun SUNA, Moon MOOQ, planets PLNQ",
 "  (Hc > -1 deg), stars from the catalogue without precession (Hc > 9 deg). Key a number on any page + R/S.",
 "2 Legend page: key the number + R/S (nothing or 0: the list again).",
 "3 The body in full precision (SUNA + STR2 / MOO2 / PLN2): two text pages (name, date, GHA, Dec / Hc, Zn,",
 "  SHA or SD or HP SD, T/S), R/S: horizon chart with the body and its data (3 x PAUSE 99), then the legend.",
 "NEEDS: SUNA STAR MOON PLAN CHZ SBRT SNMU STXT CWID PTXB PTXT TGET + matrices",
 "REGS: R10-R29 R37 R40-R47 R82 R90-R99"]
A['BODY']=[('LBL 01',1,'list: SUNA, then Sun, Moon (MOOQ), planets (PLNQ), stars (catalogue) above the horizon'),
 ('LBL 04',1,'legend page, key the body number'),('LBL 05',1,'check the number: 1-58 or 60-65, else the list again'),
 ('LBL 07',1,'full precision: SUNA; T when the tables cover the date (TGET body 6)'),
 ('LBL 19',1,'HCZ; text pages'),('CLLCD',1,'chart on top (Hc 90 deg = 96 px, equator a dot every 6 deg), data below'),
 ('LBL 40',1,'add entry X to the list page: width by CWID; line 1 padded to 400 px; full page shown by LBL 45')]

H['MATF']=["MATF - FAST series: builds VL VB VR and EEL ... SAR with a fitted series for a few years",
 "  (quadratic + short-period terms, tools/almanac/fastseries.py). Same matrix format as MATA/MATP:",
 "  row 1 = [terms, 0, 0, 0] (VL: [terms, first JD, end JD, 0]); rows (30+k, A, B, C).",
 "  Run instead of MATA/MATP (INIT option 2). Outside its period SUNA sets flag 12: X on the screens."]

# ---- almanac tables (Method B) and the table switch
H['TGET']=["TGET - GHA and Dec from the loaded almanac tables (program TBL)",
 "IN : Y = JD (UT1), X = body: 0 Sun, 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn, 5 Moon, 6 Aries",
 "OUT: X = GHA, Y = Dec (deg); Moon also Z = HP, T = SD (arcmin); Aries Y = 0; X = -1 outside the table",
 "NEEDS: matrices TSU TVE TMA TJU TSA TMO TAR (run TBL once)   REGS: R00-R09, R35-R39"]
A['TGET']=[('STO 00',1,'body R00, JD R01; label 20+body selects the matrix (R09 = 0 GHA only, 1 +Dec, 2 +HP)'),
 ('STOIJ',1,'header row: JD0 R03, block length (days) R04, blocks R05, terms R06'),
 ('X<0?',1,'block index k = IP((JD - JD0) / length); outside the table -> LBL 09'),
 ('STO 08',1,'x = 2 (JD - block start) / length - 1 -> R08; data row = k + 2 -> R07'),
 ('XEQ 30',1,'GHA from column 1, MOD 360 -> R35; Dec from column terms+1 -> R36'),
 ('STO 37',1,'Moon: HP (4 terms) -> R37; SD = 358473400 sin(HP) / 6378.14 / 60'),
 ('LBL 30',1,'Chebyshev sum (Clenshaw): X = first column, R02 = terms, row R07, x R08; b_k = c_k + 2x b_k+1 - b_k+2'),
 ('LBL 20',1,'matrix of each body: 20 Sun, 21-24 planets, 25 Moon, 26 Aries')]
H['TBL']=["TBL - almanac tables (Chebyshev coefficients from JPL DE421) for a limited period",
 "Written by tools/almanac/tab2c47.py. Run once: builds TSU TVE TMA TJU TSA TMO TAR and sets flag 10.",
 "Row 1 of each matrix: JD of the first block, block length (days), blocks, terms. CF 10 = use the series."]
A['TBL']=[('SF 10',1,'flag 10: tables loaded; SUNA, SUNG, MOO2 and PLN2 use them inside their period')]
A['SUNA']+=[('FS? 10',1,'tables loaded (flag 10): Sun GHA/Dec and GHA Aries from TGET when the date is covered (LBL 45)'),
 ('LBL 45',1,'Sun (body 0) -> R81 GHA, R77 Dec; Aries (body 6) -> R80; unchanged if outside the table'),
 ('LBL "SUNG"',1,'SUNG: fast Sun GHA/Dec for the SUNRISE iterations: TGET if covered, else SUNF'),('LBL "SUNF"',1,'SUNF: low-precision Sun (Astronomical Almanac): L, g, lambda = L + 1.915 sin g + 0.020 sin 2g, eps; Dec, RA; GHA = GMST - RA. Within 0.01 deg: event times within about 15 s')]
A['SUNRISE']+=[('XEQ "SUNG"',1,'SUNG = low-precision Sun SUNF, or the tables when loaded')]
A['MOON']+=[('FC? 10',1,'tables loaded and covering the date: TGET body 5, set flag 11 (T on the screens); else series, clear flag 11')]
A['PLAN']+=[('FC? 10',1,'tables loaded and covering the date: GHA/Dec from TGET, SHA = GHA - GHA Aries, HP 0; else series (LBL 33)')]
for k,y,x in (('ALMF',8,390),('HALMV',8,392)):
    A[k]+=[('"S"',1,'T = Moon and planets from the tables (flag 11), S = series: bottom right'),('LBL 29',1,'letter T')]
A['HORZ']+=[('"S"',1,'T = tables (flag 11), S = series: bottom left, small font'),('LBL 29',1,'letter T')]
A['HORZS']+=[('"S"',1,'T = tables (flag 11), S = series: bottom left, small font'),('LBL 29',1,'letter T')]
A['ALMT']+=[('"S"',1,'page 1, line 2 ends at 400 px with T (tables, flag 11) or S (series)')]
FILEMAP={'PTBDEMO':'PTBDEM'}
def process(fname):
    key=fname[:-4]; key=FILEMAP.get(key,key)
    lines=open(os.path.join(SRC,fname)).read().rstrip('\n').split('\n')
    notes={}
    for anc,occ,com in A.get(key,[]):
        seq=anc.split('\n'); n=0; found=None
        for i in range(len(lines)-len(seq)+1):
            if lines[i:i+len(seq)]==seq:
                n+=1
                if n==occ: found=i; break
        if found is None: print('  anchor not found',key,repr(anc)); continue
        notes.setdefault(found,[]).append(com)
    return key,lines,notes,H.get(key,[key])

os.makedirs('/home/claude/C47_nav/listings',exist_ok=True); os.makedirs('/home/claude/C47_nav/programs_rem',exist_ok=True)
# ---- speed (Sep 2026): trig functions cached, series and Moon with matrix functions
def _drop(k, keys):
    A[k] = [a for a in A[k] if a[0] not in keys]
_drop('SUNA', {'3\nSTO 55', '7\nSTO 55', 'LBL 12'})
A['SUNA'] += [('XEQ "SERT"',1,'vectors SV1 = [1, tau, tau^2, 0, 0], SV2 = [0, 0, 0, 1, tau] for the series'),
 ('LBL "SERT"',1,'SERT: build SV1 and SV2 from tau (R50)'),
 ('LBL 15',1,'per-page constants for STR2 (named variables): zeta, z, sin/cos theta, sin/cos mean and true obliquity, e, perihelion; PQK = -1 (PLAN Earth cache)')]
A['CHZ'] = [('LBL "CHZ"',1,'store lat R91, lon R92, HCZI, then HCZ'),
 ('LBL "HCZ"',1,'HCZ: Y = Dec, X = GHA -> Hc (R96), Zn (R97); sin/cos of the latitude from HCZI (HZS, HZC): 6 trig functions'),
 ('LBL "HCZ0"',1,'HCZ0: Dec = 0 (celestial equator): 4 trig functions'),
 ('LBL "HCZQ"',1,'HCZQ: Y = first GHA, X = step: cos/sin of LHA and of the step (EQC EQS EQCH EQSH)'),
 ('LBL "HCZR"',1,'HCZR: next equator point: Hc, Zn from EQC/EQS, then rotate LHA by the step (no COS/SIN)'),
 ('LBL "HCZI"',1,'HCZI: sin and cos of the latitude R91 -> HZS, HZC (once per screen)'),
 ('LBL "DHA"',1,'DHA: Hc, Zn -> Dec, LHA, GHA')]
A['STAR'] = [('LBL "STAR"',1,'save star no. -> R82, run SUNA for JD'),('LBL "STR2"',1,'entry after SUNA: read ST row R82'),
 ('RCL 54\n100',1,'proper motion (years since J2000 = 100T)'),
 ('RCL 83\nRCL+ "SZE"',1,'precession with the constants from SUNA (SZE, SZZ, SSTH, SCTH)'),
 ('RCL 56\nRCL× "SCE0"',1,'to the ecliptic of date (mean obliquity SSE0, SCE0)'),
 ('RCL 74\nRCL- 69',1,'annual aberration (SEK, SPI) and nutation in longitude'),
 ('RCL 56\nRCL× "SCEP"',1,'back to the equator (true obliquity SSEP, SCEP); SHA, GHA'),
 ('LBL "SQK"',1,'SQK: X = star -> sin of a quick Hc from the catalogue (no precession): screens skip stars below 9 deg')]
A['MATA'] = [('LBL "MATA"',1,'VL VB VR: Earth L B R series, rows [A (tau^0), A (tau^1), A (tau^2), B, C], row 1 = header'),
 ('NEWMAT\nSTO "NU"',1,'NU: nutation terms')]
A['MATM'] = [('LBL "MATM"',1,'ML MCL MCB: [d m mp f, sin coeff for |m| = 0 1 2, cos coeff for |m| = 0 1 2]; MB: sin only (7 columns)')]
A['MOON'] = [a for a in A['MOON'] if a[0] not in ('LBL 20', 'LBL 21')] + [
 ('XEQ 20\nRCL "ML"',1,'sums with matrix functions: angles = table x [D M M\' F ...], SIN/COS on the vector, DOT with the weights [1 E E^2]'),
 ('LBL 20',1,'vectors MA10 MS10 MC10 MA7 MS7 from D M M\' F (R01-R04) and E (R05)')]
A['PLAN'] = [a for a in A['PLAN'] if a[0] != 'INDEX "EEL"'] + [
 ('XEQ "SERT"\nRCL "EEL"',1,'Earth heliocentric L R00, B R01, R R02 (series with matrix functions)'),
 ('LBL 48',1,'Earth from mean elements, kept for the page in PQX PQY PQZ (key PQK = T)'),
 ('LBL 50',1,'heliocentric x R31, y R33, z R30 of body X from mean elements (13 trig functions)')]

for f in sorted(os.listdir(SRC)):
    if not f.endswith('.txt'): continue
    key,lines,notes,head=process(f)
    # annotated listing
    out=['; '+'='*70]+['; '+h for h in head]+['; '+'='*70]
    for i,l in enumerate(lines):
        if i in notes:
            for c in notes[i]:
                if l.startswith('LBL'): out.append(';'); 
                out.append('; ---- '+c)
        out.append('%04d  %s'%(i+1,l))
    open('/home/claude/C47_nav/listings/'+f[:-4]+'_doc.txt','w').write('\n'.join(out)+'\n')
    # REM version
    def rem(t): return 'REM "%s"'%t.replace('"',"'").replace(';',',')
    r=[]
    for i,l in enumerate(lines):
        if i==0:
            r.append(l)
            for h in head: r.append(rem(h))
            if i in notes:
                for c in notes[i]: r.append(rem(c))
            continue
        if i in notes:
            if l.startswith('LBL'):
                r.append(l)
                for c in notes[i]: r.append(rem(c))
                continue
            for c in notes[i]: r.append(rem(c))
        r.append(l)
    open('/home/claude/C47_nav/programs_rem/'+f,'w').write('\n'.join(r)+'\n')
print('done')
