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
      P('Celestial navigation on the SwissMicros C47 — user manual', sub), Spacer(1, 6),
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
          ['NAVFULL', 'the program NAV with all 9 views and the almanac tables support (TBL)'],
          ['NAVFULL_NOTBL', 'the same without the tables: a little smaller'],
          ['NAVALL', 'all views, NAV runs INIT by itself the first time (flag 81)'],
          ['NAVCOMP', 'compact menu: 1 ALMANAC, 2 CHART, 4 SKY, 9 ALLSKY'],
          ['NAVTXT', 'text only (no drawing): the almanac page in the registers'],
          ['NAVINIT_FULL', 'INIT: builds the series matrices, valid 2000–2050 (about 6 000 numbers)'],
          ['NAVINIT_FAST', 'INIT: fitted series for a few years only: smaller and faster'],
          ['TBL', 'optional: almanac tables (JPL) for a period; XEQ TBL once, then delete it']],
          [32 * mm, 148 * mm]),
      P('2. First start', h2)] + B([
      'Convert each text file with <b>rejig</b> (rejig FILE.txt -o FILE.p47) and load it on the C47.',
      'Load one NAV file and one NAVINIT file. <b>XEQ "INIT"</b> once: it builds the matrices and shows MATRICES READY. '
      'Then delete INIT (GTO "INIT", CLP): the matrices stay.',
      'Optional: load TBL, XEQ "TBL" once, delete it. The screens then show T (tables) instead of S (series).',
      'The calculator\'s date format (CLK menu) must be <b>YYYY-MM-DD</b>: NAV reads DATE with the C47\'s own date functions.'])
S += [P('3. Starting NAV', h2),
      P('XEQ "NAV" asks four numbers, once, with INPUT (R/S keeps the value shown). The message line shows '
        'the formats: DATE YYYY.MMDD  UT HH.MMSS  LAT DD.MMm  LON DDD.MMm  S W -.'),
      prose_tbl([['Input', 'Meaning', 'Example'],
                 ['DATE', 'UT date, YYYY.MMDD (the CLK date format must be YYYY-MM-DD)', '2026.0926'],
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
      img('NAV_menu.png', 0.8),
      P('Title ALMANAC 47, the period the matrices are valid for, the date, UT and DR in use.', small),
      prose_tbl([['Key', 'On the menu', 'On a view'],
                 ['1 – 9', 'the item is highlighted and its view is drawn', '—'],
                 ['+', '—', 'back to the menu'],
                 ['▲ / ▼', 'one hour later / earlier (the title shows the new time)', 'the same view one hour later / earlier'],
                 ['0', 'end of NAV: clears the screen and the stack', '—'],
                 ['other keys', 'ignored', 'ignored (R/S or EXIT stop the program)']],
                [26 * mm, 77 * mm, 77 * mm]),
      P('The hours added with the arrows stay for the other views. New date or position: XEQ "NAV" again.', small)]

S += [PageBreak(), P('5. The views', h2),
      P('All examples: 26 Sep 2026 14:57 UT, 25° 20′ N 055° 12′ E, unless stated.', small),
      pair('ALMF_preview.png', 'HALMV_preview.png',
           '<b>1 ALMANAC</b> (ALMF): GHA, Dec, Hc, Zn of 10 bodies — the Sun, the Moon and planets above the horizon, '
           'the brightest stars higher than 10°; twilight, rise/set, meridian passage, Moon phase, HP, SD. '
           '23 Sep 2026 23:30 UT, 10° N 075° 30′ W.',
           '<b>2 CHART</b> (HALMV): the sky on the left (Hc up, Zn across, the celestial equator dotted), '
           'the Hc/Zn table on the right. Same time and place.'),
      Spacer(1, 4),
      pair('HORZ_axes_night.png', 'ALMS_preview.png',
           '<b>4 SKY</b> (HORZ): full-screen chart; the top line names each body in turn (3 s each), UT at the top right, '
           'DR under it. 23 Sep 2026 03:00 UT, 30° N 0° E.',
           '<b>5 SMALL</b> (ALMS): short almanac: the Sun, the Moon, one planet, three stars.'),
      Spacer(1, 4),
      pair('HALMH_preview.png', 'BODY_preview.png',
           '<b>6 SPLIT</b> (HALMH): the chart on top, the short almanac below.',
           '<b>7 BODY</b>: the bodies above the horizon; key a number (stars 1–58, Sun 60, Moon 61, planets 62–65) '
           'for its data and its place on the chart. Here 49 Vega.'),
      Spacer(1, 4),
      pair('ANIM_preview.png', 'ALLSKY_preview.png',
           '<b>8 ANIM</b> (HANIM): the Sun and the Moon moving over 12 hours (24 frames, 1 s each).',
           '<b>9 ALLSKY</b>: the whole sky, over the horizon above, under the horizon below: every star, '
           'the Sun, the Moon and the planets; DAY / TWILIGHT / NIGHT.'),
      P('<b>3 TEXT</b> (ALMR): the same page as text, one line per register (R50 …, lines 1–26 also in the stack and '
        'the lettered registers). NAV ends and opens the register browser (REGS). XEQ "NAV" for the menu again.'),
      P('<b>Below the horizon:</b> a body with a negative Hc (in practice the Sun) has its Hc shown white on black, '
        'as the Sun in the ALMANAC and CHART examples above.')]

S += [P('6. Speed and memory', h2)] + B([
      'The sky is computed once for a time and place (matrix ALMC, 73 × 4: GHA, Dec, Hc, Zn of the Sun, the Moon, '
      'planets 1–4 and stars 1–58). Going from view to view only draws. An arrow (a new hour) computes again.',
      'The celestial equator of the charts depends only on the position: it is kept in ALMQ (300 × 3) and redrawn from there.',
      'The fonts read each column pattern from stack register D: NAV uses the 8-level stack while it runs and puts your '
      'stack size back when you leave with 0 or TEXT.',
      'The C47 shows a new screen at a PAUSE or a key press: NAV makes a short PAUSE after each drawing, so the screen '
      'appears at once while the program waits for a key.',
      'With the tables (TBL) the Sun, the Moon and the planets come from the tables inside their period and the '
      'computation is about twice as fast.',
      '<i>Something lives in NAV at the step after LBL 48. It is 0. Try 20 and press + or an arrow …</i>'])

# ---- program map: the navigation routines and their labels on the calculator (no fonts)
rows = [['Label', 'Name', 'What it does']]
for l in lines('build/NAVFULL_LABELS.txt'):
    m = _re.match(r'(NAV|N\d\d)\s+(\S+)\s+(.*)$', l)
    if m and not m.group(3).startswith('FONT'):
        rows.append([m.group(1), m.group(2), m.group(3)])
S += [PageBreak(), P('7. Program map', h2),
      P('In the NAV files every program label except NAV is renamed N01, N02 … (so the names do not clash with your own '
        'programs). This is the map of the navigation routines in NAVFULL; the font routines (PTXS, PTXT and their number '
        'entries, N52–N62) are left out. NAVFULL_NOTBL has the same labels without N50 (TGET). NAVALL, NAVCOMP and NAVTXT '
        'have their own numbering: see their _LABELS.txt files.'),
      prose_tbl(rows, [16 * mm, 18 * mm, 146 * mm])]
