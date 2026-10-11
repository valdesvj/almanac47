# manual_nav.py - part 1 of the user manual: using ALMA47 on the C47 / R47 (v2.2.0, the STRUCT build), the views,
# the labels, MOON47.
# Run through build_manual.py (exec): uses its S, P, B, styles, tables, DOCS and ROOT.
import re as _re
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_struct_src as _B
import build_release_c47 as _R

C47DOCS = os.path.join(DOCS, 'c47')                 # the screens of v2.2.0 (tools/generators/c47_struct_shots.py)


def img(name, frac=0.49, where=None):
    return RLImage(os.path.join(where or C47DOCS, name), width=W * frac, height=W * frac * 0.6)


def pair(a, b, ca='', cb='', where=None):
    t = Table([[img(a, where=where), img(b, where=where)], [P(ca, small), P(cb, small)]], colWidths=[W * 0.5, W * 0.5])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 1),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 1)]))
    return t


def lines(path):
    return [l.rstrip('\n') for l in open(os.path.join(ROOT, path), encoding='utf-8')]


S += [P('Almanac 47', title),
      P('Celestial navigation on the SwissMicros C47 / R47 — user manual — version %s (%s)' % (_R.VERSION, _R.NAME), sub),
      Spacer(1, 6),
      P('Almanac 47 puts an almanac page on the C47: GHA, declination, Hc and Zn of the Sun, the Moon, the planets and '
        'the navigation stars for your DR and time, sunrise, sunset, twilight and the Moon\'s phase, with horizon charts of '
        'the sky. Everything is computed on the calculator (VSOP87, Meeus, IAU precession and nutation).'),
      P('<b>Version 2.2.0 is for the C47 and the R47 only.</b> It is written with the C47\'s structured programming '
        'commands — IF … ELSE … ENDIF, DO … WHILE … ENDDO, REPEAT … UNTIL — and has no GTO at all; Free42, Plus42, the '
        'DM42 and HP-42S firmware do not have these commands. It carries all the speed work done since v2.1.0: the same '
        'pages, drawn with far fewer steps (section 6). <b>Free42 / Plus42 / DM42 users: keep v2.1.0</b> and its manual '
        '(Almanac47_Free42_Manual.pdf).'),
      P('<b>It supports, and does not replace, the Nautical Almanac.</b> The menu and INFO say so.'),
      P('<b>Author:</b> Victor Valdes (valdes.vj@gmail.com). The programs, the PC version and this manual were written with the help of '
        'AI (Claude, by Anthropic). The results were checked against JPL Horizons and USNO data, and the screens '
        'were tested on the calculator and pixel for pixel against the PC version.', small),
      P('Copyright © 2026 Victor Valdes. Free software under the GNU General Public License v3.0 or later: you may '
        'use, share and change it under its terms. It comes with NO WARRANTY. See the files LICENSE and NOTICE.', small),
      P('Part 1 — using ALMA47', h1),
      P('1. What to load', h2),
      prose_tbl([
          ['File', 'What it is'],
          ['ALMA47', 'the programs that stay on the calculator: the menu and every view. On the calculator only ALMA47 '
                     'has a name; its routines are N01, N02 … (section 7)'],
          ['NAVINIT_FAST', 'the program NAVINIT: builds the matrices of a series fitted to 2026–2030 (smaller and faster)'],
          ['NAVINIT_FULL', 'the program NAVINIT: builds the matrices of the full series, valid 2000–2050 (VSOP87 and Meeus, '
                           'about twice the memory). Load NAVINIT_FAST <i>or</i> NAVINIT_FULL'],
          ['MOON47', 'the Moon phase on its own, from the clock (section 8); needs nothing else'],
          ['ALMA47_LABELS.txt', 'the labels of ALMA47 and the routines you can call yourself'],
          ['p47u/', 'the same programs as rejig sources (.p47u) with comments, for the PROGRAMS folder of the C47']],
          [32 * mm, 148 * mm]),
      P('Each comes as .p47 (load it as it is) and as .txt (the listing). The old DM42 with the C47 firmware is not '
        'part of v2.2.0: its published firmware has no STRUCT (section 9). The almanac tables (TBL) of earlier versions '
        'are not part of v2.2.0 either (they stay in the repository).', small),
      P('2. First start', h2)] + B([
      'The C47 needs a firmware with <b>ATEXT</b>, <b>GRFNT</b> and the <b>STRUCT</b> commands: 00.109.05.00a0.ALPHA '
      '(5 Oct 2026) or later. The screens write their text with ATEXT in GRFNT 21 (the tinyFont, GRFNT 10, on the '
      'charts); only the body symbols are drawn with AGRAPH. On the older firmware 00.109.04.00b0 use the v1.1.0 release.',
      'Load ALMA47.p47 and one NAVINIT file (USB disk, then READP in the I/O menu). The .p47u files convert with '
      '<b>rejig -o ALMA47.p47 ALMA47.p47u</b> (a rejig that knows the C47 STRUCT items writes their numbers, IF 01 …); '
      'their comments come after a ";" and rejig drops them, so they cost no memory.',
      '<b>XEQ "NAVINIT"</b> once: it builds the matrices and shows MATRICES READY: FAST 2026-2030 (or FULL 2000-2050). '
      'Then delete it (GTO "NAVINIT", DELP): the matrices stay. Do not use CLPALL: it deletes ALMA47 too.',
      'ALMA47 asks DATE in the calculator\'s date format (CLK menu: YYYY-MM-DD, DD.MM.YYYY or MM/DD/YYYY) and reads it '
      'with the C47\'s own date functions; the prompt shows which.',
      'What changed inside is in OPTIMIZATIONS.md (in the zip, docs/ in the repository).'])
S += [P('3. Starting ALMA47', h2),
      P('XEQ "ALMA47" asks four numbers, once, with INPUT (R/S keeps the value shown). At each prompt the stack is '
        'clear and Y shows only the format of that input: DATE YYYY.MMDD (DATE DD.MMYYYY or DATE MM.DDYYYY when the '
        'CLK date format is D.MY or M.DY), UT HH.MMSS, LAT DD.MMm  S -, LON DDD.MMm  W -.'),
      prose_tbl([['Input', 'Meaning', 'Example'],
                 ['DATE', 'UT date in the CLK date format: YYYY.MMDD, DD.MMYYYY or MM.DDYYYY', '2026.0926'],
                 ['UTC', 'UT, HH.MMSS (UT1; add DUT1 to UTC for full accuracy)', '14.57'],
                 ['LAT', 'latitude DD.MMm, south negative', '25.20 = 25° 20′ N'],
                 ['LON', 'longitude DDD.MMm, west negative', '55.12 = 55° 12′ E']],
                [22 * mm, 110 * mm, 48 * mm]),
      P('After LON the sky is computed (the Sun, the Moon, the planets, the stars, the sun times) and kept in the matrix '
        'ALMC; then the menu appears, and the views only draw. While the sky or a view is computed, the hourglass shows '
        'in the top right corner and a box in the middle of the screen says SINKING....ABOUT; the view appears when it '
        'is complete. ALMC stays between runs: with the same date, time and place the menu and the views come at once.'),
      img('NAV_busy_box.png', 0.6),
      P('4. The menu', h2),
      img('NAV_menu.png', 0.66),
      P('Title ALMANAC 47 and the period of the matrices; under it the date, UT and DR in use. Under the items, the '
        'keys: + MENU, ↑↓ ±1 HOUR and 9 SNAP.', small),
      prose_tbl([['Key', 'On the menu', 'On a view'],
                 ['1 – 6', 'the item is highlighted and its view is drawn (6: INFO)', '—'],
                 ['9', 'SNAP (a screenshot)', 'SNAP (a screenshot)'],
                 ['+', '—', 'back to the menu'],
                 ['▲ / ▼', 'one hour later / earlier (the title shows the new time)', 'the same view one hour later / earlier'],
                 ['0', 'end of ALMA47: clears the numbered registers (CLREGS), the screen and the stack', '—'],
                 ['other keys', 'ignored', 'ignored (R/S or EXIT stop the program)']],
                [26 * mm, 77 * mm, 77 * mm]),
      P('The hours added with the arrows stay for the other views. New date or position: XEQ "ALMA47" again.', small),
      P('<b>ALMA47 uses the numbered registers and the 8-level stack.</b> It uses R00–R98 while it runs (its values and '
        'its most used numbers) and the 8-level stack (the text routines need it). Leaving with 0 clears R00–R99 '
        '(CLREGS) and the stack, puts your stack size back and the standard font (GRFNT 20). <b>Save your registers '
        'first.</b> Named variables and matrices are not touched (DATE, UTC, LAT, LON and the matrices of NAVINIT stay). '
        'If you stop ALMA47 with R/S or EXIT, the registers keep its values: that is how the routines of section 7 can be '
        'called from the keyboard. Up to v2.1.0 NAV saved your registers and gave them back; since v2.2.0 it does not.')]

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
           '<b>3 SKY</b> (HORZ): full-screen chart of the 8 bodies; every 2 seconds the name of the next one is written '
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
        'as the Sun in the ALMANAC example above. <b>X</b> at the top right instead of S: the date is outside the period '
        'of the matrices (FAST: 2026–2030).')]

_n = _R.numbers(_B.build())
S += [P('6. Speed and memory', h2)] + B([
      'The sky is computed once for a time and place (matrix ALMC, 73 × 4: GHA, Dec, Hc, Zn of the Sun, the Moon, '
      'planets 1–4 and stars 1–58; the sun times). Going from view to view only draws. An arrow (a new hour) computes '
      'again. ALMC and the star order SBR stay between runs.',
      '<b>v2.2.0 (Struct on Attack)</b> has the same calculation and the same results as v2.1.0, and the same pages '
      'with the new top bar (date, UT and DR in one line) and the hourglass. It is written with the C47 STRUCT commands '
      'and is much faster. Counted in the C47 simulator, each page with its two arrows: ALMANAC 18 %, SPLIT 42 %, '
      'SKY 53 %, ANIM 54 %, ALLSKY 40 % and the menu\'s arrows 45 % fewer steps than v2.1.0; and about 85 % less of '
      'the time the C47 spends looking for labels, structure steps and the place a return goes back to. Where it comes '
      'from:',
      '— <b>no GTO:</b> every decision and loop is a structure (IF, DO, REPEAT), the key loop of the menu one DO … ENDDO, '
      'the keys 1–6 by arithmetic on the key code;',
      '— <b>the order of the code:</b> the routines used most at the start of each program, the programs in the order '
      'of their use (each RTN on the C47 walks the steps from the start of its program);',
      '— <b>drawing:</b> the horizontal lines with PIXEL line mode, the box and the highlight in GRMOD 1 with unrolled '
      'AGRAPH, the header text kept for the run, the text routines written in place where they are called most;',
      '— <b>calculation:</b> Hc and Zn with four trigonometric functions, the equator of the charts a whole column at a '
      'time (M.GETM / M.PUTM), the star order as a matrix (SBR), whole numbers into text with one αIP.',
      'ALMA47 is 27.2 KB (8 734 steps; v2.1.0\'s NAVFULL 24.2 KB): the unrolled loops and the code written in place '
      'make it bigger, for speed. MOON47 is 4.5 KB. NAVINIT while it is loaded: FAST 28.5 KB, FULL 57.8 KB; the '
      'matrices FAST about 55 KB, FULL about 95 KB.',
      '<b>Accuracy, checked in the C47 firmware itself</b> (its PC simulator) against JPL DE421 with ERFA, 20 random '
      'instants and places each for FULL (2000–2050) and FAST (2026–2030): Sun within 0.02′, Moon 0.10′, planets 0.05′, '
      'stars 0.003′, Hc and Zn 0.08′ — the same as v2.1.0.',
      'History: v2.0.0 was faster and smaller than v1.1 (Horner\'s method, n-vectors, the nutation as matrix products, '
      'counted loops); v2.1.0 (Supercharger) the cos and sin of each series as one complex eˣ, Hc and Zn from the '
      'body\'s direction vector. Details of every step: OPTIMIZATIONS.md.',
      'The C47 sends a new screen to the display only at a PAUSE, a key press or the end of the program: the '
      'SINKING box shows while a view is computed, then the complete view.',
      '<i>INFO says the ants are waiting for a flag. Something lives in ALMA47 under its LBL 06 … try flag 47, then '
      'press + or an arrow.</i>'])

# ---- the labels of ALMA47: the routines you can call, every global label, the numbers in R43-R98
_L = _B.build()
_glob = [l[5:-1] for l in _L if l.startswith('LBL "')]
S += [PageBreak(), P('7. Inside ALMA47: the labels', h2),
      P('ALMA47 is 26 programs. Only the first has a name, ALMA47; each of the others starts with a numbered global label, '
        'N01, N02 … (so the names do not clash with yours), and its routines are local labels 01, 02 … The numbers are '
        'those of earlier versions: a number missing below belongs to a routine that is gone. The comments of ALMA47.p47u '
        'say what every routine does; the source is programs_struct/ in the repository (one file per program, indented).'),
      P('Routines you can call yourself', h3),
      P('Run ALMA47 with your date, time and DR, then leave it with <b>EXIT</b> (or R/S), not with 0 — 0 clears the '
        'registers. These routines read the numbers ALMA47 stores in R43–R98 when it starts (the table at the end of '
        'this section), the DR of the run (R13 longitude, R14 latitude) and the matrices of NAVINIT; they use R00–R42 '
        'for their work. JD is the C47\'s Julian Date (the date, then ⅅ→J) + UT / 24, a plain number.'),
      prose_tbl([['Label', 'Name', 'Input', 'Output']] + [[a, b, c, d] for a, b, c, d in _R.CALLABLE],
                [14 * mm, 14 * mm, 70 * mm, 82 * mm]),
      P('Example: ALMA47 for 23 Sep 2026, 25° 20′ N 055° 12′ E, left with EXIT. <b>2461307 XEQ "N15"</b> gives '
        'X 1.9070 (GHA of the Sun, 1° 54.4′), Y −0.1932 (Dec S 0° 11.6′), Z 182.3525 (GHA of Aries); then '
        '<b>XEQ "N25"</b> the Moon. <b>2461306.5 ENTER 25.333 ENTER 55.2 XEQ "N38"</b> gives 2.13: sunrise at 02:08 UT.', small),
      P('Every global label of ALMA47', h3)]
_rows = [['Label', 'Name', 'What it does']]
for g in _glob:
    n, what = _B.LABELS[g]
    _rows.append(['ALMA47' if g == 'NAV' else g, n, what])
S += [prose_tbl(_rows, [16 * mm, 18 * mm, 146 * mm])]
_cells = [['R%s' % k, v] for k, v in sorted(_n.items())]
_k = (len(_cells) + 3) // 4
_rows = [['Reg.', 'Number'] * 4] + [sum((_cells[c * _k + r] if c * _k + r < len(_cells) else ['', ''] for c in range(4)), [])
                                        for r in range(_k)]
S += [P('The numbers in R43–R98 (stored by ALMA47 when it starts: each use is a 2-byte RCL)', h3),
      prose_tbl(_rows, [14 * mm, 31 * mm] * 4)]

# ---- MOON47: the Moon phase on its own
S += [PageBreak(), P('8. MOON47: the Moon phase', h2),
      P('MOON47 is a separate program: the Moon\'s phase page of the PC version on the calculator, without ALMA47 or '
        'NAVINIT. Load MOON47.p47 and <b>XEQ "MOON47"</b>. It asks nothing: the phase does not depend on where you are, '
        'so it takes the date and time from the C47\'s clock.'),
      pair('MOON47.png', 'MOON47_south.png', '3 Oct 2026 12:00 UT, as seen from the north',
           'the same after +/-: as seen from the south', where=DOCS)] + B([
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
      '<b>Accuracy</b> against the full series of ALMA47, 2000–2050: phase times and age within 4 minutes (most within 1), '
      'HP 0.03′, SD 0.01′, % lit 0.03 %. It uses the 20 largest terms of the Moon (Meeus, ch. 47), the phases by the '
      'secant method; tests/test_moon47.py checks it.',
      '<b>v2.2.0:</b> one program with MOON47 its only global label (the text and symbol routines are numbered labels '
      'inside it), written with the STRUCT commands, no GTO: 4.5 KB (4.8 KB before) and about 28 % less time spent '
      'looking for labels and returns. It uses the registers R03–R53 (save yours first), leaves your stack size as it '
      'was and a clear stack; its work matrices M7T, M7C, M7A, M7V, M7W are set to 0 at the end (TZ stays).',
      'Free42 (build/free42/MOON47.raw), the old DM42, the NumWorks and the HP Prime have their own MOON47 with the same '
      'page (v2.1.0): see their manuals.'])

# ---- the old DM42: not in v2.2.0 (its published firmware has no STRUCT)
S += [P('9. The old DM42 with the C47 firmware: not in v2.2.0', h2),
      P('v2.2.0 needs the STRUCT commands. The C47 firmware published for the old DM42 (64 KiB) has ATEXT and GRFNT, '
        'but not STRUCT: to fit in its flash, the only DM42 package of the release (pkg4) leaves structured programming '
        'out. The firmware sources say so (src/c47/defines.h), and the published file was checked.'),
      prose_tbl([['Firmware', 'ATEXT', 'GRFNT', 'STRUCT'],
                 ['00.109.05.00a0.ALPHA or later: C47, R47, DM42n', 'in', 'in', 'in (255 a series per program)'],
                 ['the same release, old DM42: pkg4 (the one published)', 'in', 'in', '<b>out</b>'],
                 ['old DM42 packages 1–3 (built from the sources, not published)', 'in', 'in',
                  'in, at most 10 IF, 10 DO and 10 REPEAT a program'],
                 ['00.109.04.00b0 and older', 'out', 'out', 'out']],
                [86 * mm, 18 * mm, 18 * mm, 58 * mm])] + B([
      '<b>Old DM42 users:</b> keep NAVLITTLE without STRUCT (the "DM42 with the C47 firmware" zip of v2.0.0, or '
      'build/dm42/ in the repository): the Sun and the 58 stars on the ALMANAC page; it needs ATEXT and GRFNT, so the '
      '05.00a0.ALPHA firmware or later.',
      'STRUCT versions of NAVLITTLE and MOON47 within the limit of 10 a program are ready in the repository '
      '(build/dev/struct_src/dm42/, checked pixel for pixel) for a DM42 firmware that includes STRUCT.',
      'The DM42n has the full firmware (STRUCT included) and 256 KiB: it runs ALMA47 like the C47 and the R47.'])
