exec(open('manual_head.py').read())
import json
from reportlab.platypus import Image as RLImage
R = json.load(open('manual_results.json'))
OUT = '/home/claude/C47_Nav_User_Manual.pdf'
def dm(x, ns=False):
    s = ''
    if ns: s = 'S ' if x < 0 else 'N '; x = abs(x)
    else: x = x % 360
    d = int(x); m = round((x - d) * 60, 1)
    if m >= 60: d += 1; m = 0
    return "%s%d° %04.1f′" % (s, d, m)
def hms(t):
    s = int(round(t * 3600)); return '%02d:%02d:%02d' % (s // 3600 % 24, s % 3600 // 60, s % 60)
def foot(c, d):
    c.saveState(); c.setFont('DV', 7); c.setFillColor(colors.HexColor('#7a8a9a'))
    c.drawString(15 * mm, 8 * mm, 'C47 celestial navigation programs — user manual')
    c.drawRightString(A4[0] - 15 * mm, 8 * mm, 'p. %d' % d.page); c.restoreState()
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=15 * mm,
                      title='C47 celestial navigation — user manual', author='Prepared for Victorio')
doc.addPageTemplates([PageTemplate('P', [Frame(15 * mm, 15 * mm, A4[0] - 30 * mm, A4[1] - 29 * mm, id='f')], onPage=foot)])
W = 180 * mm
S = []
def section(title, purpose, how, io, example, notes=None):
    S.extend([P(title, h1), P(purpose)])
    S.append(P('How it works', h3)); S.extend(B(how))
    S.append(P('Inputs and outputs', h3)); S.append(prose_tbl(io, [30 * mm, 150 * mm]))
    S.append(P('Example with results', h3)); S.extend(example)
    if notes: S.append(P('Notes', h3)); S.extend(B(notes))

# ---- cover & overview
S += [P('C47 celestial navigation programs', title),
      P('User manual — how each program works, with worked results', sub), Spacer(1, 6),
      P('These programs give the data needed for sight reduction (GHA, SHA, declination, Hc, Zn) and for planning '
        '(sunrise, sunset, twilight, Moon phase, sky picture). They support, and do not replace, the Nautical Almanac. '
        'All results are apparent geocentric positions, as in the almanac. The time argument is UT (UT1): for a sight timed in UTC, add DUT1 (under 0.9 s).'),
      P('Overview', h2),
      prose_tbl([
          ['Program', 'What it gives', 'Input', 'Output', 'Needs'],
          ['SUNA', 'Sun and Aries', 'X = JD', 'X GHA☉, Y Dec☉, Z GHA♈', 'matrices from MATA'],
          ['MATA', 'builds Earth-orbit and nutation matrices', '—', 'VL, VB, VR, NU', 'run once'],
          ['STAR', '57 navigation stars + Polaris', 'Y = JD, X = star no.', 'X GHA, Y Dec, Z SHA', 'SUNA, matrix ST'],
          ['MATST', 'builds star catalogue matrix', '—', 'ST', 'run once'],
          ['SNAM', 'star name', 'X = star no.', 'name on screen', '—'],
          ['SUNRISE', 'rise, set, twilight, meridian passage', 'Z = JD 0h, Y = lat, X = lon', 'X = UT hours', 'SUNA'],
          ['PHAS', 'Moon phase', 'X = JD', 'X % illuminated, Y age (days)', 'SUNA'],
          ['HORZ', 'picture of the sky on the horizon', 'Z = JD, Y = lat, X = lon', 'screen drawing', 'SUNA, STAR'],
          ['ALM', 'Sun, Aries, Moon, planets from tables', 'X = t (hours in block)', 'X GHA, Y Dec (HP)', 'coefficients from the tables'],
          ['TBL', 'almanac tables for a period (JPL), sets flag 10', '—', 'matrices TSU…TAR', 'run once'],
          ['TGET', 'Sun, Aries, Moon, planets from the tables', 'Y = JD, X = body 0–6', 'X GHA, Y Dec (Z HP, T SD)', 'TBL'],
          ['CHZ', 'Hc/Zn and the inverse', 'T lat, Z lon, Y Dec, X GHA', 'X Hc, Y Zn', '—'],
          ['SUNSD', 'Sun semi-diameter', 'X = JD', 'X = SD (′)', 'SUNA'],
          ['HALMV', 'sight-planning screen: chart + data', 'Z = JD, Y = lat, X = lon', 'screen', 'see HALMV section'],
          ['ALMF', 'full-page almanac screen', 'Z = JD, Y = lat, X = lon', 'screen', 'see ALMF section'],
          ['PTXB / PTXT', 'pixel text (big / small font)', 'Z = y, Y = x, X = text', 'drawing', '—'],
      ], [20 * mm, 50 * mm, 36 * mm, 44 * mm, 30 * mm]),
      P('Conventions', h3)] + B([
      '<b>Julian Date (JD):</b> use the C47 date function (Date→J) and add UT/24. It must be a plain number: for example 23 Sep 2026 12:00 UT = <b>2461307</b>, and 0h UT that day = 2461306.5.',
      '<b>Signs:</b> latitude N +, S −; longitude E +, W −; declination negative = South.',
      '<b>Angles</b> come out in decimal degrees. Use →HMS or the d.mmm display to read degrees and minutes.',
      '<b>Setup order:</b> load SUNA, MATA, STAR, MATST, CHZ, SUNRISE, PHAS, SNMU, PTXB (and PTXT), then the screens HALMV, ALMF, HALM, HORZ. XEQ MATA; XEQ MATST. MATA and MATST can then be deleted; never delete the matrices. Then save the whole state (I/O menu, SAVEST) so one LOADST restores everything.'])

# ---- SUNA
r = R['SUNA']
section('SUNA — Sun and Aries',
    'Computes the Sun\'s GHA and declination and the GHA of Aries for any instant, with no tables. It is also the engine used by STAR, SUNRISE, PHAS and HORZ.',
    ['Time: T and τ (Julian centuries and millennia of TT since J2000; TT = UT + 69.2 s).',
     'Earth\'s heliocentric longitude L, latitude B and distance R from the VSOP87D series stored in VL, VB, VR (56 + 3 + 7 terms). The loops count rows with DSE 55.',
     'Sun = L + 180°, β = −B; FK5 correction.',
     'Nutation Δψ, Δε from the 10 largest IAU 1980 terms (matrix NU). The Moon arguments D, M, M′, F are kept in R60–R63 for PHAS.',
     'Apparent longitude λ = Sun + Δψ − 20.4898″/R (aberration). Obliquity ε = 84381.448″ − 46.815″·T + Δε.',
     'Dec = asin(sin β cos ε + cos β sin ε sin λ); RA from →POL.',
     'GHA♈ = GMST + Δψ·cos ε; GHA☉ = GHA♈ − RA (mod 360).'],
    [['Input', 'X = JD (UT1)'], ['Output', 'X = GHA☉, Y = Dec☉, Z = GHA♈ (degrees). Also R73 = Sun distance R (au): SD☉ = 15.99′ ÷ R73.'],
     ['Registers', 'R50–R55, R60–R67, R70–R81']],
    [P('23 Sep 2026, 12:00:00 UT: key <b>2461307 XEQ SUNA</b>'),
     tbl([['', 'Result', 'Deg / min', 'Almanac page'],
          ['X  GHA☉', '%.7f' % r[0], dm(r[0]), '1° 54.4′'],
          ['Y  Dec☉', '%.7f' % r[1], dm(r[1], True), 'S 0° 11.6′'],
          ['Z  GHA♈', '%.7f' % r[2], dm(r[2]), '182° 21.2′'],
          ['R73 → SD☉', '%.6f au' % R['R73'], '%.2f′' % (15.99 / R['R73']), '15.94′']],
         [30 * mm, 40 * mm, 45 * mm, 45 * mm], font=8)],
    ['Accuracy vs JPL/IAU reference 2000–2050: GHA ≤ 0.016′, Dec ≤ 0.007′, GHA♈ ≤ 0.003′. Verified on the C47.',
     'Coefficients never need updating. ΔT (69.2 s, line 4) affects the Sun by only 0.0007′ per second.'])

# ---- MATA / MATST
S += [P('MATA and MATST — setup programs', h1),
      P('They contain no calculation. Each creates matrices and fills them with coefficients, so you don\'t have to type about 590 numbers by hand. Run each once; afterwards the programs can be deleted.'),
      prose_tbl([['Program', 'Creates', 'Contents'],
                 ['MATA', 'VL 56×4, VB 3×4, VR 7×4', 'VSOP87D Earth series rows: k, A, B, C (term = A·cos(B + C·τ)·τ<super>k</super>)'],
                 ['MATA', 'NU 10×9', 'IAU 1980 nutation: multipliers of D, M, M′, F, Ω and coefficients S, S′, C, C′'],
                 ['MATST', 'ST 58×4', 'Star J2000 RA, Dec (deg) and proper motions (mas/yr), stars 1–57 in almanac order, 58 = Polaris']],
                [22 * mm, 48 * mm, 110 * mm]),
      P('Memory kept afterwards: about 5.7 KB (VL, VB, VR, NU) + 3.7 KB (ST).', small)]

# ---- STAR
s18, s58 = R['STAR18'], R['STAR58']
section('STAR — navigation stars',
    'Gives GHA, SHA and declination of any of the 57 almanac navigation stars or Polaris (58).',
    ['Runs SUNA for the instant (nutation, obliquity, Sun longitude, GHA♈). Entry STR2 skips this when SUNA has already run (used by HORZ).',
     'Reads the star\'s J2000 position and proper motion from ST and applies proper motion.',
     'Precession J2000 → date with the IAU 2006 angles ζ, z, θ.',
     'Converts to ecliptic coordinates and adds nutation Δψ and annual aberration there (accurate even for Polaris), then back with the true obliquity.',
     'SHA = 360° − RA; GHA = GHA♈ + SHA.'],
    [['Input', 'Y = JD (UT1), X = star number 1–58'], ['Output', 'X = GHA, Y = Dec, Z = SHA'], ['Registers', 'R56–R59, R68–R69, R82–R89 (plus SUNA\'s)']],
    [P('23 Sep 2026, 12:00 UT: key <b>2461307 ENTER 18 XEQ STAR</b> (Sirius), and 58 for Polaris'),
     tbl([['Star', 'GHA', 'SHA', 'Dec'],
          ['18 Sirius', dm(s18[0]), dm(s18[2]), dm(s18[1], True)],
          ['58 Polaris', dm(s58[0]), dm(s58[2]), dm(s58[1], True)]],
         [40 * mm, 45 * mm, 45 * mm, 50 * mm], font=8)],
    ['Accuracy 2025–2050: 57 stars ≤ 0.003′; Polaris ≤ 0.04′ in hour angle (tiny on the sky). Checked against USNO for 30 stars: ≤ 0.009′.',
     'Star numbers are the official almanac numbers; the list in STAR_list.txt gives them by number and alphabetically.'])

# ---- SNAM
S += [P('SNAM — star names', h1),
      P('Shows the name of a star from its number: key <b>18 XEQ SNAM</b> → display "18 Sirius". It stores the number in R49, jumps with GTO IND 49 to local label 01–58, loads the name as text and shows it with AVIEW. The stack is unchanged.'),
      P('To show the name automatically after STAR, add RCL 82 · XEQ "SNAM" · R↓ before STAR\'s last RTN.', small)]

# ---- SUNRISE
ev = R['EV10']
section('SUNRISE — rise, set, twilight, meridian passage',
    'Times of sunrise, sunset, civil and nautical twilight and meridian passage for any position, directly in UT.',
    ['Starts from a first guess (06h for morning events, 18h for evening, 12h for transit).',
     'Runs SUNA at that time, computes the hour angle at which the Sun reaches the event altitude: cos H = (sin h₀ − sin φ sin δ)/(cos φ cos δ).',
     'Corrects the time by (target LHA − actual LHA)/15 and repeats until the correction is under 0.04 s (3–4 passes).',
     'Event altitudes h₀: rise/set −0°50′ (upper limb, refraction), civil −6°, nautical −12°. If the Sun never reaches it, the result is 99.'],
    [['Input', 'Z = JD at 0h UT of the day, Y = latitude (N+), X = longitude (E+, W−)'],
     ['Labels', 'NTWA / CTWA (morning twilight), RISE, TRAN, SET, CTWP / NTWP (evening twilight)'],
     ['Output', 'X = UT in decimal hours (→HMS to read); 99 = no event'], ['Registers', 'R90–R99']],
    [P('23 Sep 2026, latitude 10° N, longitude 0°: key <b>2461306.5 ENTER 10 ENTER 0</b>, then the label'),
     tbl([['Label', 'Event', 'UT', 'Almanac page (10° N)'],
          ['NTWA', 'nautical twilight am', hms(ev['NTWA']), '05 04'],
          ['CTWA', 'civil twilight am', hms(ev['CTWA']), '05 28'],
          ['RISE', 'sunrise', hms(ev['RISE']), '05 49'],
          ['TRAN', 'meridian passage', hms(ev['TRAN']), '11 52 22'],
          ['SET', 'sunset', hms(ev['SET']), '17 56'],
          ['CTWP', 'civil twilight pm', hms(ev['CTWP']), '18 17'],
          ['NTWP', 'nautical twilight pm', hms(ev['NTWP']), '18 41']],
         [22 * mm, 55 * mm, 40 * mm, 63 * mm], font=8),
     P('Medellín (6.25° N, 75.57° W): sunrise %s UT (05:51 local), sunset %s UT (17:57 local). 89.5° N: RISE gives 99 (no sunrise).'
       % (hms(R['MEDRISE']), hms(R['MEDSET'])), small)],
    ['Checked against an exact search on the JPL/IAU reference: agrees to the second.',
     'The almanac holds the noon declination fixed for the whole day, so its times can differ by up to a minute (sunset and civil pm above). The program is the more exact one.'])

# ---- PHAS
p = R['PHAS']
section('PHAS — Moon phase',
    'Percentage of the Moon\'s disk illuminated and the age of the Moon (days since new moon), as printed in the almanac.',
    ['Runs SUNA, which leaves the mean Moon arguments D, M, M′, F in R60–R63.',
     'Phase angle i (Meeus 48.4) → illuminated fraction k = (1 + cos i)/2.',
     'Age: days since the mean new moon, corrected to the true new moon with Meeus ch. 49 terms; near new moon it checks the neighbouring lunation.'],
    [['Input', 'X = JD (UT1)'], ['Output', 'X = % illuminated, Y = age (days)'], ['Registers', 'R41–R48']],
    [P('23 Sep 2026, 12:00 UT: key <b>2461307 XEQ PHAS</b> → X = <b>%.1f %%</b> (waxing gibbous), Y = <b>%.2f days</b>. '
       '10 Oct 2026 12h: 0.0 %%, 29.36 d (new moon that evening); 11 Oct 12h: 0.8 %%, 0.84 d.' % (p[0], p[1]))],
    ['Accuracy vs JPL: illumination ≤ 0.3 %, age ≤ 2 minutes.'])

# ---- HORZ
section('HORZ — sky picture on the horizon',
    'Draws a chart of the whole sky: azimuth Zn across (N–E–S–W–N, ticks every 30°), altitude Hc up (ticks and labels at 30°, 60°, 90°), the celestial equator dotted, the Sun (☉) and every navigation star above the horizon (★ with its number).',
    ['Runs SUNA once, then STAR through entry STR2 for stars 1–58 (fast: no repeated SUNA). The celestial equator is drawn as dots every 2° of hour angle.',
     'For each object: LHA = GHA + λ; Hc = asin(sin φ sin δ + cos φ cos δ cos LHA); Zn from →POL of (−cos δ sin LHA, cos φ sin δ − sin φ cos δ cos LHA).',
     'Screen: column = 20 + Zn × 375/360; row = 225 − Hc × 200/90 (from the top; converted for the C47, which counts rows from the bottom). Only objects with Hc > 0 are drawn.',
     'Text (N E S W, 30 60 90, star numbers, the info line) is drawn with PTXT, the small AGRAPH font (PTNS for integers, PT1 for one decimal); the star and sun symbols with PTXB (* and @). Lines and dots use PHL and PIXEL.'],
    [['Input', 'Z = JD (UT1), Y = latitude (N+), X = longitude (E+)'], ['Output', 'drawing on the 400×240 screen; R96 = Hc and R97 = Zn of the last object'],
     ['Needs', 'SUNA, STAR (STR2), CHZ, PTXT, PTXB'], ['Registers', 'R90–R99, R36, R37, R42, R44, R86, R93']],
    [P('23 Sep 2026, 30° N 0° E. Night 03:00 UT: key <b>2461306.625 ENTER 30 ENTER 0 XEQ HORZ</b>; day 09:00 UT: 2461306.875. Simulated screens:'),
     RLImage('/home/claude/HORZ_axes_night.png', width=W * 0.85, height=W * 0.85 * 0.6),
     Spacer(1, 4),
     RLImage('/home/claude/HORZ_axes_day.png', width=W * 0.85, height=W * 0.85 * 0.6)],
    ['Hc and Zn agree with the reference within 0.0013′; Sun Hc/Zn match USNO (88.0833° / 264.215° vs 88.0834° / 264.214°).',
     'Stars are drawn even in daylight; they are only observable in twilight.'])


# ---- HALMV
section('HALMV — sight-planning screen (chart + almanac data)',
    'One screen for twilight star sights: on the left a picture of the sky (Hc up, Zn across) with the Sun, Moon, planets and the chosen stars; on the right the date and time, your DR, GHA Aries, the Sun\'s GHA, Dec and SD, a table of Hc and Zn (Sun, then the Moon and planets that are above the horizon, then the brightest stars, 10 rows), the day\'s sun times, and the Moon\'s phase, HP and SD.',
    ['First computes the sun times with SUNRISE (NTWA, RISE, TRAN, SET, NTWP for the UT date of the JD) and the Moon with PHAS, and keeps them in R13–R19.',
     'Runs SUNA once (Sun GHA, Dec, GHA Aries; SD = 15.994′ / R from R73), then STAR through entry STR2 for stars 1–58.',
     'Moon (MOO2) and planets (PLN2) are computed without repeating SUNA. Symbols: ☾ Moon, ♀ Venus, ♂ Mars, ♃ Jupiter, ♄ Saturn. Stars: in order of brightness (SBRT), only those higher than 10°, until the table has 10 rows.',
     'Hc and Zn: CHZ subroutine HCZ. Chart: column = 18 + Zn × 178/360, row = 14 + Hc × 200/90; the celestial equator is dotted every 3° of hour angle. South latitude: chart centred on N (S W N E S).',
     'All text and numbers are drawn with PIXEL through PTXB (5×7 font): strings with the native C47 string commands, numbers with PINB, PDM (deg + min), PZN (bearing), PHM (hh:mm), PF1 and PDAT (date from JD). Star names from SNMU. The screen is held with PAUSE.'],
    [['Input', 'Z = JD (UT1), Y = latitude (N+), X = longitude (E+)'],
     ['Screen', 'left: chart; right: DR, date + UT, Aries, Sun SD, Sun GHA/Dec, table BODY / HC / ZN, naut. twilight AM/PM, rise/set, mer pass (UT), Moon % + waxing/waning + age'],
     ['Needs', 'SUNA, STAR, CHZ, SUNRISE, PHAS, MOON, PLAN, SBRT, SNMU, PTXB + all matrices (MATA, MATST, MATM, MATP)'],
     ['Registers', 'R10–R29, R37, R40–R48 (+ those of the programs it calls)'],
     ['Time', 'about 110 000 steps']],
    [P('23 Sep 2026, 23:30 UT, DR 10° 00′ N 075° 30′ W: key <b>2461307.4792 ENTER 10 ENTER −75.5 XEQ HALMV</b>. Simulated screen:'),
     RLImage('/home/claude/HALMV_preview.png', width=W * 0.9, height=W * 0.9 * 0.6),
     Spacer(1, 4),
     P('Southern example, 33° 54′ S 018° 24′ E, 19:00 UT (chart centred on N):'),
     RLImage('/home/claude/HALMV_south_preview.png', width=W * 0.9, height=W * 0.9 * 0.6)],
    ['Sun times checked against the JPL-based reference for this position: naut. twilight 10:05:46 / 23:42:41, rise 10:51:08, set 22:57:20, mer pass 16:54:18 UT — the screen rounds to the minute as the almanac does.',
     'All times are UT for the UT date of the JD, at the DR entered; sea level, standard refraction (as the almanac). West of Greenwich an evening event after 24h UT shows as 00:xx (next UT day).',
     'Hc and Zn are computed from the DR: use them to identify stars and pre-set the sextant. Near the chart edges two star numbers may overlap; the table is always exact.',
     'Sun SD = 959.63″/R; it can differ by 0.1′ from the printed page, which gives one SD per three days.'])

# ---- ALMF
section('ALMF — full-page almanac screen',
    'The same data as HALMV without the chart, laid out like an almanac page: GHA and Dec as well as Hc and Zn, with the same 10-row rule as HALMV (Sun, then the Moon and planets above the horizon, then the brightest stars higher than 10°), the sun times, Moon phase, Moon HP and SD, and Sun SD. The last line reads DOES NOT REPLACE THE NAUTICAL ALMANAC (also on HALMV).',
    ['Same calculations and table rule as HALMV.',
     'Top line: date, UT, DR and GHA Aries. Table: symbol, number, name, GHA, Dec, Hc, Zn. Bottom left: nautical twilight and rise/set in AM/PM columns and meridian passage; bottom right: Moon % and waxing/waning, age, Sun SD.'],
    [['Input', 'Z = JD (UT1), Y = latitude (N+), X = longitude (E+)'],
     ['Needs', 'same programs as HALMV'], ['Registers', 'same as HALMV'], ['Time', 'about 100 000 steps']],
    [P('Same instant and DR as the HALMV example: key <b>2461307.4792 ENTER 10 ENTER −75.5 XEQ ALMF</b>. Simulated screen:'),
     RLImage('/home/claude/ALMF_preview.png', width=W * 0.9, height=W * 0.9 * 0.6)],
    ['GHA and Dec are the almanac values for that instant (Sun ≤ 0.02′, stars ≤ 0.003′ against JPL); read them directly for sight reduction.',
     'HALM is a third layout of the same data: chart on the top half, table (GHA, Dec, Hc, Zn) on the bottom half.'])

# ---- helpers
S += [P('Supporting programs for the screens', h2), prose_tbl([
    ['Program', 'Use', 'Stack'],
    ['PTXB', 'big 5×7 pixel font; * = star, @ = sun, also % ; entries PINB, PDM, PZN, PHM, PF1, PDAT', 'Z = y, Y = x, X = text or number → Y = y, X = next x'],
    ['PTXT', 'small 3×5 pixel font, same characters and stack', 'as PTXB'],
    ['SNMU', 'star name in capitals, returned in X (no display)', 'X = star no. → X = name'],
    ['SUNSD', 'Sun semi-diameter 15.994′ / R', 'X = JD → X = SD (′)'],
    ['CHZ / HCZ / DHA', 'Hc and Zn; inverse gives Dec, LHA, GHA', 'CHZ: T lat, Z lon, Y Dec, X GHA → X Hc, Y Zn']],
    [26 * mm, 90 * mm, 64 * mm])]

# ---- ALM
a, m = R['ALMsun'], R['ALMmoon']
section('ALM — table method (Sun, Aries, Moon, planets)',
    'Evaluates short Chebyshev polynomials whose coefficients you key in from the tables in C47_GHA_Dec_Almanac.pdf or the Excel file. It is the program for the Moon and the planets (Venus, Mars, Jupiter, Saturn).',
    ['Each table line covers a block: 8 days (192 h) for Sun, Aries and planets; 1 day (24 h) for the Moon.',
     'x = 2t/span − 1, where t = hours since the start of the block.',
     'CHEB sums the series with the Clenshaw recurrence; ALM does it for GHA (R10…) and Dec (R20…); HP does the Moon\'s horizontal parallax (R30–R33).'],
    [['Store', 'R01 = n (5, Moon 6), R02 = span (192, Moon 24), GHA coefficients R10…, Dec R20…, Moon HP R30–R33'],
     ['Input', 'X = t (hours since the block start, UT1)'], ['Output', 'X = GHA, Y = Dec; XEQ HP → horizontal parallax (arcmin)'],
     ['Registers', 'R01–R09, R10–R33, R40–R41']],
    [P('<b>Sun</b>, 23 Sep 2026 12:00 UT: block 2026-09-17, t = 6 × 24 + 12 = 156'),
     tbl([['', 'c0', 'c1', 'c2', 'c3', 'c4']] + [['GHA'] + ['%.5f' % v for v in R['ALMsun_coef'][0]], ['Dec'] + ['%.5f' % v for v in R['ALMsun_coef'][1]]],
         [14 * mm] + [33 * mm] * 5, font=7.4),
     P('Result: GHA %s, Dec %s (same as SUNA).' % (dm(a[0]), dm(a[1], True)), small),
     P('<b>Moon</b>, 23 Sep 2026 19:00 UT: block 2026-09-23, t = 19'),
     tbl([['', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5']] + [['GHA'] + ['%.5f' % v for v in R['ALMmoon_coef'][0]], ['Dec'] + ['%.5f' % v for v in R['ALMmoon_coef'][1]],
          ['HP'] + ['%.3f' % v for v in R['ALMmoon_coef'][2]] + ['', '']],
         [14 * mm] + [27.5 * mm] * 6, font=7),
     P('Result: GHA %s, Dec %s, HP %.2f′ (SD ≈ 0.2725 × HP = %.2f′).' % (dm(m[0]), dm(m[1], True), m[2], 0.2725 * m[2]), small)],
    ['Accuracy 0.002′ (HP 0.001′). Tables valid 1 Sep 2026 – 31 Dec 2027; later years with c47_almanac_generator.py.',
     'Not yet run on the C47: check RCL IND and DSE with the Sun example.'])

# ---- TBL / TGET and the T/S switch
t = R['TBL']
def trow(name, tab, ser, hp=False):
    r = [name, dm(tab[0]), dm(tab[1], True), dm(ser[0]), dm(ser[1], True),
         '%.3f′' % abs(((tab[0] - ser[0] + 180) % 360 - 180) * 60), '%.3f′' % abs((tab[1] - ser[1]) * 60)]
    return r
section('TBL and TGET — almanac tables, and the T / S switch',
    'Precise GHA and Dec for a limited period, taken from Chebyshev tables fitted to the JPL ephemeris (the same source as the printed almanac). '
    'Once the tables are loaded, the Sun, Aries, Moon and planets on every screen come from them automatically, the screens need about half the program steps, '
    'and each screen shows <b>T</b> (tables) or <b>S</b> (series). Outside the table period everything falls back to the series (SUNA, MOON, PLAN), which work for any date.',
    ['<b>Making the tables (PC):</b> tools/almanac/c47_almanac_generator.py computes apparent GHA and Dec from JPL DE421 with the IAU 2006/2000A precession-nutation (ERFA) and fits a Chebyshev polynomial to each block: 8 days (5 terms) for the Sun, Aries and planets, 1 day (6 terms, plus 4 for HP) for the Moon. The tables for 1 Sep 2026 – 31 Dec 2027 are in the Excel file.',
     '<b>Turning them into a C47 program:</b> tools/almanac/tab2c47.py START END writes TBL.txt (convert with rejit). TBL builds one matrix per body — TSU Sun, TVE Venus, TMA Mars, TJU Jupiter, TSA Saturn, TMO Moon, TAR Aries — and sets flag 10. Row 1 of each matrix holds the JD of the first block, the block length in days, the number of blocks and the number of terms; each following row holds the coefficients of one block.',
     '<b>TGET</b> finds the block for the JD, computes x = 2 (JD − block start) / length − 1 and sums the series (Clenshaw) for GHA (MOD 360), Dec and, for the Moon, HP; SD = 358473400 sin HP / 6378.14 / 60.',
     '<b>The switch (flag 10 set):</b> SUNA replaces the Sun GHA/Dec (R81, R77) and GHA Aries (R80) with the table values; the stars keep their own calculation with that GHA Aries. SUNG, used by the SUNRISE iterations, takes the Sun from the tables and skips the series. MOO2 and PLN2 call TGET first; if the date is outside the table they compute the series. MOO2 sets flag 11 when the Moon came from the tables.',
     '<b>The letter on the screens:</b> T = flag 11 (the Moon, and so everything except the stars, from the tables), S = series. ALMF and HALMV bottom right, HORZ and HORZS bottom left, ALMT at the end of the first line. On days at the edge of the period (the Moon table starts or ends one day before the 8-day blocks) the screen shows S while the Sun and planets may already come from the tables.'],
    [['TBL', 'run once: XEQ TBL → builds the matrices, sets flag 10, shows “TBL 26-09-2026 TO 31-01-2027”. The TBL program can then be deleted; the matrices stay.'],
     ['TGET in', 'Y = JD (UT1), X = body: 0 Sun, 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn, 5 Moon, 6 Aries'],
     ['TGET out', 'X = GHA, Y = Dec (degrees); Moon also Z = HP, T = SD (arcmin); Aries Y = 0. X = −1 when the date is outside the table.'],
     ['Flags', '10 = tables loaded (CF 10 = use the series only); 11 = Moon from the tables (T on the screens)'],
     ['Registers', 'TGET: R00–R09, R35–R39 (the MOON/PLAN work registers)'],
     ['Programs', 'TBL, TGET and the updated SUNA, SUNRISE, MOON, PLAN, ALMF, HALMV, HORZ, HORZS, ALMT']],
    [P('Cape Town (33° 54′ S, 18° 24′ E), 23 Nov 2026 09:00 UT, JD 2461367.875. Tables (TGET) against the series programs:'),
     tbl([['Body', 'GHA tables', 'Dec tables', 'GHA series', 'Dec series', 'ΔGHA', 'ΔDec'],
          trow('Sun', t['sun'][0], t['series']['sun']),
          trow('Moon', t['moon'][0], t['series']['moon']),
          trow('Venus', t['venus'][0], t['series']['venus'])],
         [16 * mm, 27 * mm, 27 * mm, 27 * mm, 27 * mm, 28 * mm, 28 * mm], font=7.4),
     P('Moon HP %.2f′ and SD %.2f′ from the tables (series %.2f′, %.2f′). GHA Aries %s. Outside the table (1 Mar 2027) TGET returns −1 for the Moon.' %
       (t['moon'][0][2], t['moon'][0][3], t['series']['moon'][2], t['series']['moon'][3], dm(t['aries'][0][0])), small),
     P('Program steps for the same screens, series → tables:', small),
     tbl([['Screen', 'Series', 'Tables', 'Saving']] + [[k, '{:,}'.format(v[0]), '{:,}'.format(v[1]), '%d %%' % round(100 - 100 * v[1] / v[0])] for k, v in t['steps'].items()],
         [30 * mm, 40 * mm, 40 * mm, 30 * mm], font=7.6),
     P('ALMF with the tables — note the T in the bottom right corner:'),
     RLImage('/home/claude/ALMF_tables.png', width=W * 0.9, height=W * 0.9 * 0.6)],
    ['Differences between tables and series are the series\' own error: at most about 0.005′ for the Sun, 0.02′ for the planets and 0.07′ for the Moon. On the screens this changes at most the last digit (0.1′).',
     'One TGET call takes about 265 steps (Moon 400) against 2 000–12 000 for the series; that is where the time saving comes from.',
     'The tables expire: load the next period in time (a quarter or a year per file, depending on memory). TBL for 26 Sep 2026 – 31 Jan 2027 holds 3 054 numbers, about the size of MATP.',
     'ΔT (TT − UT1) is fixed in the generator (69.2 s). One second of error moves the Moon by about 0.01′.',
     'The PC version (python/native/c47pc.py) reads the same TBL.txt and gives the same screens (box “Almanac tables”, or --tables / --series).'])

# ---- sight reduction & python & maps
S += [P('Using the results for Hc and Zn', h1)] + B([
    'GHA and Dec at the sight time (UT = UTC + DUT1): SUNA (Sun), STAR (stars), ALM (Moon, planets).',
    'LHA = GHA + λ (E +), mod 360.',
    'Hc = asin(sin φ sin δ + cos φ cos δ cos LHA).',
    'Zn = atan2(−cos δ sin LHA, cos φ sin δ − sin φ cos δ cos LHA), mod 360.',
    'Intercept = Ho − Hc, toward Zn if positive. The C47 key →HcZ may do these steps directly.',
    'For Ho you still need index error, dip, refraction, SD (☉ from R73, ☾ from ALM HP) and the almanac\'s planet corrections.'])
S += [P('Python and NumWorks version', h2),
      P('nav.py + navdata.py contain the same methods (SUNA, STAR, SUNRISE, PHAS) for a computer or a NumWorks. The menu asks for year, month, day and UT (hh:mm:ss) and computes the JD itself. '
        'Results are identical to the C47 programs (for example Sun 23 Sep 2026 12h: GHA 1° 54.4′, Dec S 0° 11.6′).')]
S += [P('Register map', h2),
      prose_tbl([['Program', 'Registers'], ['SUNA', '50–55, 60–67, 70–81'], ['STAR', '56–59, 68–69, 82–89'], ['SUNRISE, HORZ', '90–99'],
                 ['PHAS', '41–48'], ['SNAM', '49'], ['ALM', '01–09, 10–33, 40–41'], ['CHZ', '91–92, 94–97'], ['PTXB / PTXT', '30–36'],
                 ['HALMV, ALMF, HALM', '10–29, 37, 40–48 (work registers, results of SUNRISE/PHAS kept in 13–19)']], [40 * mm, 140 * mm]),
      P('C47 notes', h2)] + B([
    'The C47 does not treat →DEG and flag 77 like the HP-42S; the programs avoid both (verified on the C47 with SUNA).',
    'Memory kept on the calculator: about 12 KB (programs + matrices) of about 246 KB free.',
    'Keep the printed Nautical Almanac as the primary reference; use the calculator as support and cross-check.'])
doc.build(S)
print('ok')
