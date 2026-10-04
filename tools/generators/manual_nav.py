# manual_nav.py - part 1 of the user manual: using NAV on the C47, the views, the program map.
# Run through build_manual.py (exec): uses its S, P, B, styles, tables, DOCS and ROOT.
import re as _re


def img(name, frac=0.49):
    return RLImage(os.path.join(DOCS, name), width=W * frac, height=W * frac * 0.6)


def pair(a, b, ca='', cb=''):
    t = Table([[img(a), img(b)], [P(ca, small), P(cb, small)]], colWidths=[W * 0.5, W * 0.5])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 1),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 1)]))
    return t


def lines(path):
    return [l.rstrip('\n') for l in open(os.path.join(ROOT, path), encoding='utf-8')]


S += [P('Almanac 47', title),
      P('Celestial navigation on the SwissMicros C47 — user manual — version 2.0.0', sub), Spacer(1, 6),
      P('Almanac 47 puts an almanac page on the C47: GHA, declination, Hc and Zn of the Sun, the Moon, the planets and '
        'the navigation stars for your DR and time, sunrise, sunset, twilight and the Moon\'s phase, with horizon charts of '
        'the sky. Everything is computed on the calculator (VSOP87, Meeus, IAU precession and nutation); optional '
        'Chebyshev tables fitted to JPL make it faster for a chosen period.'),
      P('<b>It supports, and does not replace, the Nautical Almanac.</b> Every screen says so.'),
      P('<b>Author:</b> Victor Valdes (valdes.vj@gmail.com). The programs, the PC version and this manual were written with the help of '
        'AI (Claude, by Anthropic). The results were checked against JPL Horizons and USNO data, and the screens '
        'were tested on the calculator and pixel for pixel against the PC version.', small),
      P('Copyright © 2026 Victor Valdes. Free software under the GNU General Public License v3.0 or later: you may '
        'use, share and change it under its terms. It comes with NO WARRANTY. See the files LICENSE and NOTICE.', small),
      P('Part 1 — using NAV', h1),
      P('1. What to load', h2),
      prose_tbl([
          ['File', 'What it is'],
          ['NAVFULL', 'the program NAV with all the views and the almanac tables support (TBL); it keeps your '
                      'registers (v2.0.0)'],
          ['NAVINIT_FULL', 'INIT: builds the series matrices, valid 2000–2050 (about 6 000 numbers)'],
          ['NAVINIT_FAST', 'INIT: fitted series, valid 2026–2030: smaller and faster'],
          ['TBL_1, TBL_5', 'optional almanac tables (JPL) for 1 or 5 years from 1 Oct 2026; XEQ TBL once, then '
                           'delete it. Big: meant for Free42 / Plus42 on a PC or phone; on the C47 only a short table fits'],
          ['NAVLITTLE', 'build/dm42/: for the old DM42 with the C47 firmware (64 KiB): the ALMANAC screen, '
                        'Sun and 58 stars only, with NAVINIT_LITTLE (2000–2050)']],
          [32 * mm, 148 * mm]),
      P('2. First start', h2)] + B([
      'The C47 needs a firmware with <b>ATEXT</b> and <b>GRFNT</b>: the screens write their text with ATEXT in '
      'GRFNT 21 (the tinyFont, GRFNT 10, on the charts); only the body symbols are drawn with AGRAPH.',
      'Convert each text file with <b>python3 tools/rejig47_atext.py FILE.txt</b> (runs rejig and writes the ATEXT / '
      'GRFNT steps rejig 0.34 does not know; a rejig that knows them converts directly) and load the .p47 on the C47.',
      'The file name is the version: on the calculator the programs are always NAV and INIT. Other builds '
      '(NAVFULL_NOTBL, NAVALL, NAVCOMP) are in build/dev/.',
      'Load one NAV file and one NAVINIT file. <b>XEQ "INIT"</b> once: it builds the matrices and shows MATRICES READY. '
      'Then delete INIT (GTO "INIT", DELP): the matrices stay.',
      'Optional: load TBL, XEQ "TBL" once, delete it. The screens then show T (tables) instead of S (series).',
      'NAV asks DATE in the calculator\'s date format (CLK menu: YYYY-MM-DD, DD.MM.YYYY or MM/DD/YYYY) and reads it '
      'with the C47\'s own date functions; the prompt shows which.',
      'v2.0.0 has no NAVTXT (text only) and no CHART or TEXT views; what changed inside is in docs/OPTIMIZATIONS.md.'])
S += [P('3. Starting NAV', h2),
      P('XEQ "NAV" asks four numbers, once, with INPUT (R/S keeps the value shown). At each prompt the stack is '
        'clear and Y shows only the format of that input: DATE YYYY.MMDD (DATE DD.MMYYYY or DATE MM.DDYYYY when the '
        'CLK date format is D.MY or M.DY), UT HH.MMSS, LAT DD.MMm  S -, LON DDD.MMm  W -.'),
      prose_tbl([['Input', 'Meaning', 'Example'],
                 ['DATE', 'UT date in the CLK date format: YYYY.MMDD, DD.MMYYYY or MM.DDYYYY', '2026.0926'],
                 ['UTC', 'UT, HH.MMSS (UT1; add DUT1 to UTC for full accuracy)', '14.57'],
                 ['LAT', 'latitude DD.MMm, south negative', '25.20 = 25° 20′ N'],
                 ['LON', 'longitude DDD.MMm, west negative', '55.12 = 55° 12′ E']],
                [22 * mm, 110 * mm, 48 * mm]),
      P('After LON the sky is computed (the Sun, the Moon, the planets, the stars that can be above the horizon, '
        'the sun times) and kept in the matrix ALMC. Then the menu appears, and every view only draws. '
        'While the calculator works, a box in the middle of the screen says SINKING....ABOUT (after LON, '
        'after a menu number, + and the arrows) until the new screen is drawn.'),
      img('NAV_busy_box.png', 0.6),
      P('4. The menu', h2),
      img('NAV_menu.png', 0.66),
      P('Title ALMANAC 47, the period the matrices are valid for, the date, UT and DR in use.', small),
      prose_tbl([['Key', 'On the menu', 'On a view'],
                 ['1 – 6', 'the item is highlighted and its view is drawn (6: INFO)', '—'],
                 ['9', 'SNAP (a screenshot)', 'SNAP (a screenshot)'],
                 ['+', '—', 'back to the menu'],
                 ['▲ / ▼', 'one hour later / earlier (the title shows the new time)', 'the same view one hour later / earlier'],
                 ['0', 'end of NAV: gives your registers back, clears the screen and the stack', '—'],
                 ['other keys', 'ignored', 'ignored (R/S or EXIT stop the program)']],
                [26 * mm, 77 * mm, 77 * mm]),
      P('The hours added with the arrows stay for the other views. New date or position: XEQ "NAV" again.', small),
      P('<b>Your registers are kept.</b> NAV uses R00–R45 while it runs. It copies them into its own local registers '
        'when it starts and copies them back when you leave with 0, so the values you had in your registers are there '
        'again. If you stop NAV with R/S or EXIT, they keep NAV\'s values.')]

S += [PageBreak(), P('5. The views', h2),
      P('All views: 23 Sep 2026 23:30 UT, 10° N 075° 30′ W (the menu: 26 Sep 2026 14:57 UT, 25° 20′ N 055° 12′ E). '
        'Every view starts with the same line: date, UT, DR, and T / S (tables / series) at the right.', small),
      pair('ALMF_preview.png', 'HALMH_preview.png',
           '<b>1 ALMANAC</b> (ALMF): GHA ARIES, then GHA, Dec, Hc, Zn of 8 bodies — the Sun, the Moon if it is up, '
           'the first planet above the horizon, the brightest stars higher than 10°; twilight, rise/set, meridian '
           'passage, the Moon (lit part, phase symbol, age, HP, SD).',
           '<b>2 SPLIT</b> (HALMH): the chart on top (Hc up, Zn across, the celestial equator dotted), the bodies '
           'below down to the bottom of the screen (8 rows).'),
      Spacer(1, 4),
      pair('HORZ_axes_night.png', 'ANIM_preview.png',
           '<b>3 SKY</b> (HORZ): full-screen chart of the 8 bodies; every second the name of the next one is written '
           'next to its symbol (here MOON); DAY / TWILIGHT / NIGHT at the bottom.',
           '<b>4 ANIM</b> (HANIM): the Sun and the Moon moving on the whole-sky chart over 12 hours (24 frames, '
           '1 s each, 30 min apart); the first frame.'),
      Spacer(1, 4),
      pair('ALLSKY_preview.png', 'NAV_info.png',
           '<b>5 ALLSKY</b>: the whole sky, over the horizon above, under the horizon below: every star, '
           'the Sun, the Moon and the planets; DAY / TWILIGHT / NIGHT.',
           '<b>6 INFO</b>: the repository (github.com/valdesvj/almanac47), the licence (GNU GPL v3 or later), '
           'no warranty, and the rule: always cross-check the values with the Nautical Almanac. The warning line '
           '(DOES NOT REPLACE THE NAUTICAL ALMANAC) is on the menu and on INFO only.'),
      P('<b>9 SNAP</b>, on the menu and on every view: a screenshot of the screen (SNAP), then the same screen again.'),
      P('<b>Below the horizon:</b> a body with a negative Hc (in practice the Sun) has its Hc shown white on black, '
        'as the Sun in the ALMANAC example above.')]

S += [P('6. Speed and memory', h2)] + B([
      'The sky is computed once for a time and place (matrix ALMC, 73 × 4: GHA, Dec, Hc, Zn of the Sun, the Moon, '
      'planets 1–4 and stars 1–58). Going from view to view only draws. An arrow (a new hour) computes again.',
      'The celestial equator of the charts depends only on the position: it is kept in ALMQ (300 × 3) and redrawn from there.',
      'The fonts read each column pattern from stack register D: NAV uses the 8-level stack while it runs and puts your '
      'stack size back when you leave with 0.',
      'v2.0.0 is faster and smaller than v1.1 with the same results: Horner\'s method for every polynomial, n-vectors '
      '(→POL / →REC) instead of trigonometric formula pairs, the nutation as matrix products, counted loops on ISG; '
      'the registers were renumbered from 100 to 46. NAVFULL is 31.1 KB (36.6 KB in v1.1). Details: docs/OPTIMIZATIONS.md.',
      'The C47 sends a new screen to the display only at a PAUSE, a key press or the end of the program. NAV makes a '
      'PAUSE 0 after each drawing (no wait), so every screen appears complete, at once, and the SINKING box stays until '
      'the next screen is ready. (Holding a key while a view draws makes the C47 show the drawing step by step.)',
      'Free42 on the DM42 / DM42n (build/free42) shows every drawing step at once, so the screens build up in front of '
      'you. The Free42 NAVFULL and NAVLITTLE switch this off with the DM42 variable RefLCD (0 = no update, '
      '-1 = update once, 7 = normal) and so behave like the C47.',
      'With the tables (TBL) the Sun, the Moon and the planets come from the tables inside their period and the '
      'computation is about twice as fast.',
      '<i>Something lives in NAV at the step after LBL 48. It is 0. Try 20 and press + or an arrow …</i>'])

# ---- program map: the navigation routines and their labels on the calculator (no fonts)
rows = [['Label', 'Name', 'What it does']]
for l in lines('build/NAVFULL_LABELS.txt'):
    m = _re.match(r'(NAV|N\d\d)\s+(\S+)\s+(.*)$', l)
    if m and not m.group(3).startswith(('FONT', 'TEXT', 'SYMBOL', 'horizontal line')):
        rows.append([m.group(1), m.group(2), m.group(3)])
S += [PageBreak(), P('7. Program map', h2),
      P('In the NAV files every program label except NAV is renamed N01, N02 … (so the names do not clash with your own '
        'programs). This is the map of the navigation routines in NAVFULL; the text routines (PTXS with ATEXT and its number '
        'entries, PTTY / PTNT for the tinyFont, PHLS) and the symbol routines (PSYB, PSYS) are left out. The numbers are fixed (tools/labels/NAVFULL.map): a new routine gets the next free '
        'number, so the labels stay the same from one version to the next. NAVFULL_NOTBL has the same labels without '
        'N49 (TGET). NAVLITTLE has its own numbering: see its _LABELS.txt file. The registers of NAVFULL are '
        'renumbered by the build (v2.0.0): the register lists of part 2 are those of the separate programs.'),
      prose_tbl(rows, [16 * mm, 18 * mm, 146 * mm])]

# ---- MOON47: the Moon phase on its own
S += [PageBreak(), P('8. MOON47: the Moon phase', h2),
      P('MOON47 is a separate program: the Moon\'s phase page of the PC version on the calculator, without NAV, INIT or '
        'the tables. Load build/MOON47 (convert it with rejig) and <b>XEQ "MOON47"</b>. It asks nothing: the phase does '
        'not depend on where you are, so it takes the date and time from the C47\'s clock.'),
      pair('MOON47.png', 'MOON47_south.png', '3 Oct 2026 12:00 UT, as seen from the north',
           'the same after +/-: as seen from the south')] + B([
      '<b>The page:</b> the Moon as a disc (the lit part filled), the phase name, % lit, age in days, HP and SD, the '
      'next new Moon, first quarter, full Moon and last quarter (date and time UT), and the eight phase symbols with '
      'today\'s one inverted.',
      '<b>Keys:</b> +/- turns the picture to the view from the south and back (the latitude only turns the picture); '
      'any other key ends.',
      '<b>The clock is local time.</b> If it is not set to UT, store your offset once in the variable TZ, in hours: '
      '<b>4 STO "TZ"</b> for UT+4, <b>-5 STO "TZ"</b> for UT−5. Without TZ, MOON47 creates it with 0 and takes the '
      'clock as UT: the phase times stay right, the age and % lit are then a few hours off (% lit changes at most '
      '0.45 % an hour).'
      ' The top line shows the clock: the time UT and TZ=0, or with TZ the local time LT and your '
      'offset (TZ=+4, TZ=-5, TZ=+5:30).',
      '<b>Accuracy</b> against the full series of NAV, 2000–2050: phase times and age within 4 minutes (most within 1), '
      'HP 0.03′, SD 0.01′, % lit 0.03 %. It uses the 20 largest terms of the Moon (Meeus, ch. 47), the phases by the '
      'secant method; tests/test_moon47.py checks it.',
      '<b>Memory:</b> about 5.5 KB (the program and its own copies of the text and symbol routines, M7TX and M7SY, so '
      'it does not need NAVFULL and does not clash with it). It takes registers R00–R61 and leaves your stack size as '
      'it was. Needs a firmware with ATEXT and GRFNT, like NAV.',
      'The same program runs on the old DM42 with the C47 firmware (build/dm42/MOON47). Free42 (build/free42/MOON47.raw), '
      'the NumWorks and the HP Prime have their own MOON47 with the same page: see their manuals.'])
