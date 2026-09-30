#!/usr/bin/env python3
"""build_port_manuals.py - user manuals of the other calculators (same style as the C47 manual):

  docs/Almanac47_Free42_Manual.pdf     DM42 / DM42n, stock firmware (build/free42)
  docs/Almanac47_NumWorks_Manual.pdf   NumWorks (python/numworks)
  docs/Almanac47_HPPrime_Manual.pdf    HP Prime (python/hpprime)

  python3 tools/generators/build_port_manuals.py
Screens: docs/free42/*.png (tools/generators/free42_shots.py), docs/NUMWORKS_*.png, docs/HPPRIME_*.png.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOCS = os.path.join(ROOT, 'docs')
exec(open(os.path.join(HERE, 'manual_head.py')).read())
from reportlab.platypus import Image as RLImage

W = 180 * mm
WARN = '<b>It supports, and does not replace, the Nautical Almanac.</b> Always cross-check the values.'
LIC = ('Copyright © 2026 Victor Valdes. Free software under the GNU General Public License v3.0 or later. '
       'It comes with NO WARRANTY. Written with the help of AI (Claude, by Anthropic); the results were checked '
       'against the C47 version, which was checked against JPL Horizons, USNO data and the Nautical Almanac.')


def img(path, frac=0.49, ratio=0.6):
    return RLImage(path, width=W * frac, height=W * frac * ratio)


def pair(a, b, ca='', cb='', ratio=0.6):
    t = Table([[img(a, ratio=ratio), img(b, ratio=ratio)], [P(ca, small), P(cb, small)]], colWidths=[W * 0.5, W * 0.5])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 1),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 1)]))
    return t


def make(out, title_line, story):
    def foot(c, d):
        c.saveState(); c.setFont('DV', 7); c.setFillColor(colors.HexColor('#7a8a9a'))
        c.drawString(15 * mm, 8 * mm, 'Almanac 47 — %s — Victor Valdes' % title_line)
        c.drawRightString(A4[0] - 15 * mm, 8 * mm, 'p. %d' % d.page); c.restoreState()
    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm,
                          bottomMargin=15 * mm, title='Almanac 47 — ' + title_line, author='Victor Valdes')
    doc.addPageTemplates([PageTemplate('P', [Frame(15 * mm, 15 * mm, A4[0] - 30 * mm, A4[1] - 29 * mm, id='f')], onPage=foot)])
    doc.build(story)
    print(out)


def inputs_note():
    return B(['<b>Time is UT (UT1)</b>: for a sight timed in UTC add DUT1 (under 0.9 s) — as in the almanac.',
              '<b>Signs:</b> latitude N +, S −; longitude E +, W −.'])


# ------------------------------------------------------------------ Free42 (DM42 / DM42n)
def free42():
    F = lambda n: os.path.join(DOCS, 'free42', 'F42_%s.png' % n)
    S = [P('Almanac 47 for Free42', title),
         P('SwissMicros DM42 / DM42n with the stock (Free42) firmware — user manual', sub), Spacer(1, 6),
         P('The full Almanac 47 of the C47 — the Sun, the Moon, the planets and the 58 navigation stars, 9 views — '
           'converted to Free42 3.3 with the DM42 graphics extension (the whole 400 × 240 screen). The menu, the screens '
           'and the values are the same as on the C47: in the Free42 core (SwissMicros source, release 3.3.10) each '
           'screen was compared pixel by pixel with the C47 version, and the text page line by line.'),
         P(WARN), P(LIC, small),
         P('1. What you need', h2)] + B([
        'A <b>DM42n</b> (recommended) or DM42 with the SwissMicros stock firmware (DM42 3.26 = Free42 3.3.10 or later). '
        'The DM42n has ample memory. For little memory there is NAVLITTLE: the ALMANAC screen with the Sun and the '
        '58 stars only (section 10).',
        'Free42 on a PC or phone has only the 131 × 16 HP-42S screen: NAV runs there, but you see only the top left '
        'corner of each screen. Use the calculator for the views.'])
    S += [P('2. Files (build/free42)', h2),
          prose_tbl([['File', 'What it is'],
                     ['NAVFULL.raw', 'the program NAV and its routines: all 9 views; the screen appears complete, '
                                     'at once, as on the C47'],
                     ['NAVINIT_FULL.raw', 'INIT for NAVFULL: the series matrices, valid 2000–2050'],
                     ['NAVINIT_FAST.raw', 'INIT for NAVFULL: fitted series for 2026–2030 (smaller, faster)'],
                     ['NAVLITTLE.raw', 'NAV for little memory: the ALMANAC screen, Sun and stars only (section 10)'],
                     ['NAVINIT_LITTLE.raw', 'INIT for NAVLITTLE: Sun, nutation and stars, valid 2000–2050'],
                     ['TBL_1.raw, TBL_5.raw', 'optional almanac tables (JPL) for 1 or 5 years from 1 Oct 2026 (section 11)'],
                     ['*.txt', 'the same programs as text (Free42 on a PC: Paste in PRGM mode)'],
                     ['dev/NAVFULL_DRAW.raw', 'NAVFULL with the Free42 screen update: each screen builds up as it is drawn']],
                    [45 * mm, 135 * mm]),
          P('3. Loading and first start', h2)] + B([
        'Connect the calculator by USB (it appears as a disk) and copy the .raw files into the PROGRAMS folder.',
        'The file name is the version: on the calculator the programs are always NAV and INIT.',
        'On the calculator: <b>SETUP → Load Program</b>, load NAVINIT_FULL.raw (or NAVINIT_FAST.raw).',
        '<b>XEQ "INIT"</b>: it builds the matrices and shows MATRICES READY. Then delete INIT (GTO "INIT", CLP): the '
        'matrices stay.',
        'Load NAVFULL.raw and <b>XEQ "NAV"</b>.'])
    S += [P('4. Starting NAV', h2),
          P('NAV asks four numbers with INPUT (R/S keeps the value shown); the formats are in the message line first:'),
          prose_tbl([['Input', 'Meaning', 'Example'],
                     ['DATE', 'UT date, YYYY.MMDD', '2026.0926'],
                     ['UTC', 'UT, HH.MMSS', '14.57'],
                     ['LAT', 'latitude DD.MMm, south negative', '25.20 = 25° 20′ N'],
                     ['LON', 'longitude DDD.MMm, west negative', '55.12 = 55° 12′ E']],
                    [22 * mm, 110 * mm, 48 * mm])] + inputs_note() + [
          P('Then NAV switches to the 400 × 240 graphics mode (GrMod 3), computes the sky (the SINKING....ABOUT box '
            'shows meanwhile) and draws the menu. 0 on the menu ends NAV and sets the normal screen again (GrMod 0).'),
          img(F('menu'), 0.6),
          P('5. Keys', h2),
          prose_tbl([['Key', 'On the menu', 'On a view'],
                     ['1 – 9', 'the item is highlighted and its view is drawn', '—'],
                     ['+', '—', 'back to the menu'],
                     ['▲ / ▼', 'one hour later / earlier', 'the same view one hour later / earlier'],
                     ['0', 'end of NAV (screen and stack cleared)', '—'],
                     ['R/S, EXIT', 'stop the program', 'stop the program']],
                    [26 * mm, 77 * mm, 77 * mm]),
          PageBreak(), P('6. The views', h2),
          P('26 Sep 2026 14:57 UT, 25° 20′ N 055° 12′ E, as drawn by Free42.', small),
          pair(F('almanac'), F('chart'), '<b>1 ALMANAC</b>: GHA, Dec, Hc, Zn of 10 bodies; twilight, rise/set, mer. pass, '
               'Moon phase, HP, SD. A negative Hc is white on black.', '<b>2 CHART</b>: the sky (Hc up, Zn across, the '
               'celestial equator dotted) and the Hc/Zn table.'), Spacer(1, 4),
          pair(F('text'), F('sky'), '<b>3 TEXT</b>: the almanac page as text, drawn with the small font; the lines are '
               'also in R50 … (Free42 has no register browser). + back to the menu.',
               '<b>4 SKY</b>: full-screen chart; the top line names each body in turn (3 s each).'), Spacer(1, 4),
          pair(F('small'), F('split'), '<b>5 SMALL</b>: short almanac.', '<b>6 SPLIT</b>: chart on top, short almanac below.'),
          Spacer(1, 4),
          pair(F('anim'), F('allsky'), '<b>7 ANIM</b>: the Sun and the Moon over 12 hours (24 frames, 1 s each).',
               '<b>8 ALLSKY</b>: the whole sky, over and under the horizon; DAY / TWILIGHT / NIGHT.'), Spacer(1, 4),
          pair(F('info'), F('box_ants'), '<b>9 INFO</b>: repository, licence, no warranty, cross-check.',
               'The SINKING....ABOUT box while the calculator works, with the ants (flag 97, below).'),
          PageBreak(), P('7. How the screen appears', h2),
          P('Free42 sends every drawing step to the LCD at once, so a program builds each screen up in '
            'front of you (the stars of SKY appear one by one), and the SINKING box is cleared as soon as the next view '
            'starts to draw. The C47 shows its screen only at a PAUSE, a key press or the end, so there a view appears '
            'complete, at once, and the box stays until it is ready.'),
          P('<b>NAVFULL</b> and <b>NAVLITTLE</b> do it the C47 way with the DM42 variable RefLCD: 0 STO "RefLCD" (no LCD update '
            'while NAV computes and draws), −1 STO "RefLCD" (one update) where the C47 program shows its screen, and '
            '7 (normal) when NAV ends. If you stop it with R/S or EXIT and the screen stays frozen, key '
            '<b>7 STO "RefLCD"</b>. dev/NAVFULL_DRAW keeps the Free42 way.'),
          P('8. The ants', h2),
          P('The ants live in NAV as on the C47, but they wait for <b>flag 97</b> (the HP-42S flag 47 is a system flag): '
            'SF 97 and press a view number, + or an arrow.'),
          P('9. What is different inside (the screens are the same)', h2)] + B([
        'AGRAPH draws the ALPHA register (8-pixel columns, bit 0 at the top): the fonts are strings of column bytes; '
        'the C47 drawing modes (OR, set, clear, XOR = GRMOD 0–3) are the HP-42S AGRAPH flags 34 and 35.',
        'PIXEL goes through a routine that converts the C47 coordinates (row 0 at the bottom) to the DM42 ones (row 1 at the top).',
        'Keys (GETKEY / GETKEYA) are translated to the C47 key codes; pauses use TIME; strings use XSTR, APPEND, HEAD; '
        'the date is computed (Free42 has no C47 date functions). NAV sets SIZE 100 (R00–R99).',
        'Built with tools/build_free42.py from the C47 programs; tested with tools/f42 (the Free42 core with the DM42 '
        'graphics, binary arithmetic). NAVFULL tested on a DM42n with the stock firmware by the author.'])
    S += [PageBreak(), P('10. NAVLITTLE: Sun and stars', h2),
          P('The NAVLITTLE of the old DM42 with the C47 firmware, converted the same way. It keeps the Sun and the 58 '
            'navigation stars (no Moon, no planets, no tables), draws with the 5 × 7 font of the first versions and has '
            'no box and no ants: for a calculator with little free memory. The Sun and star values are the same as in '
            'NAVFULL.'),
          img(F('little'), 0.6)] + B([
        'Load NAVINIT_LITTLE.raw, <b>XEQ "INIT"</b> (MATRICES READY: SUN STARS 2000-2050), delete INIT; load '
        'NAVLITTLE.raw, <b>XEQ "NAV"</b>. If INIT is still loaded and has not run, the first NAV runs it (flag 81).',
        'NAV asks DATE, UTC, LAT, LON as above and goes straight to the ALMANAC screen: ▲ / ▼ one hour later / '
        'earlier (the screen stays while it computes), + ends (GrMod 0, screen and stack cleared).',
        'Programs: NAVLITTLE about 10 KB, NAVINIT_LITTLE about 8 KB (.raw files), matrices 667 numbers.',
        'Tested in the Free42 core against the C47 NAVLITTLE, pixel by pixel (tests/test_f42_little.py); not yet on '
        'a real calculator.'])
    S += [P('11. Almanac tables: TBL_1 and TBL_5', h2)] + B([
        'Optional: Chebyshev coefficients fitted to JPL DE421. <b>TBL_1</b>: 1 Oct 2026 – 30 Sep 2027 (8,441 numbers, '
        'file 97 KB). <b>TBL_5</b>: 1 Oct 2026 – 30 Sep 2031 (41,882 numbers, file 481 KB).',
        'Load ONE, <b>XEQ "TBL"</b> once: it builds the matrices TSU, TVE, TMA, TJU, TSA, TMO, TAR and sets flag 10. Then '
        'delete TBL; the matrices stay (about 135 KB for 1 year, 670 KB for 5 years).',
        'NAVFULL and NAVLITTLE then take the Sun, the Moon, the planets and GHA Aries from the tables inside their period '
        '(NAVLITTLE: the Sun and Aries), and the screens show <b>T</b> instead of S. Outside the period, or after '
        '<b>CF 10</b>, the series are used. The values agree with the series to 0.1′.',
        'The tables need more memory than the C47 has: they are meant for Free42 / Plus42 on a PC or phone, or a DM42n '
        'with enough free memory.'])
    make(os.path.join(DOCS, 'Almanac47_Free42_Manual.pdf'), 'Free42 (DM42 / DM42n) — user manual', S)


# ------------------------------------------------------------------ NumWorks / HP Prime
def python_port(name, key):
    nw = name == 'NumWorks'
    pre = os.path.join(DOCS, ('NUMWORKS_' if nw else 'HPPRIME_'))
    ratio = 222 / 320 if nw else 240 / 320
    S = [P('Almanac 47 for the %s' % name, title),
         P('Python version: the ALMANAC page and the horizon chart — user manual', sub), Spacer(1, 6),
         P('Two graphic views of the C47 suite, drawn with the %s\'s own graphics module (%s): the “vintage” ALMANAC '
           'page and the horizon chart. The numbers come from nav.py and navdata.py — the same series and methods as the '
           'C47 programs (the Sun from the full VSOP87 series, valid 2000–2050, nutation, the 58 navigation stars, '
           'sunrise, twilight, Moon phase). On a PC every value on the screens was compared with the text page of nav.py '
           'and with the C47 ALMANAC screen: identical.' % (name, 'kandinsky, keys with ion' if nw else 'hpprime')),
         P('<b>The Sun and the stars only:</b> nav.py has no Moon position and no planets (the Moon phase and age are '
           'shown). The table has the Sun and the brightest stars higher than 10°, as on the C47.'),
         P(WARN), P(LIC, small),
         P('1. Files', h2)]
    if nw:
        S += [prose_tbl([['File', 'From', 'What it is'],
                         ['nav.py, navdata.py', 'python/', 'the almanac computation and data (also a text menu)'],
                         ['nwlib.py', 'python/numworks/', 'text (the C47 5×7 font), symbols, keys, main loop'],
                         ['almview.py', 'python/numworks/', 'starts on the ALMANAC page'],
                         ['skyview.py', 'python/numworks/', 'starts on the horizon chart']],
                        [38 * mm, 36 * mm, 106 * mm]),
              P('2. Copy to the calculator', h2)] + B([
            '<b>Epsilon (official):</b> on my.numworks.com create each script (Python → new script, paste the file, same '
            'name), then “Send to my calculator” with the calculator on USB (Chrome or Edge). The online simulator there '
            'runs them too.',
            '<b>Upsilon / Omega:</b> the same five files, with their web installer\'s script manager or the workshop.',
            'Open almview.py (or skyview.py) in the Python app and choose <b>Execute script</b>.'])
    else:
        S += [prose_tbl([['File', 'From', 'What it is'],
                         ['nav.py, navdata.py', 'python/', 'the almanac computation and data (also a text menu)'],
                         ['main.py', 'python/hpprime/', 'what the Python app runs: starts on the ALMANAC page'],
                         ['hplib.py', 'python/hpprime/', 'text, symbols, keys, main loop'],
                         ['almview.py, skyview.py', 'python/hpprime/', 'the two views']],
                        [38 * mm, 36 * mm, 106 * mm]),
              P('2. Copy to the calculator', h2)] + B([
            'On the calculator: Apps, select <b>Python</b>, Save it as a new app, e.g. <b>Almanac47</b> (the original '
            'Python app stays as it is).',
            'With the <b>HP Connectivity Kit</b> (calculator on USB, or the Virtual Calculator): open the new app under '
            'Application Library and drag the six .py files into it (replace its main.py). If your Kit does not accept '
            'dropped files, create each file in the app\'s Symb view with the same name and paste the text.',
            'Start the app (Apps → Almanac47). From its shell, <b>import skyview</b> starts on the horizon chart.'])
    S += [P('3. Inputs', h2),
          P('The program asks in the terminal, like the nav.py menu:'),
          prose_tbl([['Input', 'Format', 'Example'],
                     ['Year, Month, Day', 'numbers', '2026, 9, 26'],
                     ['UT', 'hh:mm or hh:mm:ss', '14:57'],
                     ['Lat, Lon', '“25 20” = 25° 20′, “25.5” = decimal degrees, “-” for S / W', '25 20, 55 12']],
                    [36 * mm, 100 * mm, 44 * mm])] + inputs_note()
    k = (('UP / DOWN', 'one hour later / earlier'), ('OK or EXE' if nw else 'ENTER', 'switch ALMANAC ↔ HORIZON'),
         ('LEFT / RIGHT', 'HORIZON: the previous / next body for the top line (shown in red)'),
         ('BACK' if nw else 'ESC', 'exit' + ('' if nw else ' (ON also stops a Python program)')))
    S += [P('4. Keys', h2), prose_tbl([['Key', 'Action']] + [list(x) for x in k], [36 * mm, 144 * mm]),
          PageBreak(), P('5. The views', h2),
          P('The previews were made on a PC with stand-ins for the %s module (the same scripts; the calculator\'s own '
            'font may make text a little wider or narrower).' % ('kandinsky' if nw else 'hpprime'), small),
          pair(pre + 'alm.png', pre + 'sky.png',
               '<b>ALMANAC</b>: date, UT, DR; GHA Aries; BODY, GHA, DEC, HC, ZN of the Sun and the stars; naut. twilight, '
               'rise/set, meridian passage, Sun SD, Moon phase and age. A negative Hc is white on black. '
               '26 Sep 2026 14:57 UT, 25° 20′ N 055° 12′ E.',
               '<b>HORIZON</b>: Hc up (sine scale), Zn across, the celestial equator dotted, the Sun and the stars with '
               'their numbers; the top line shows ZN and HC of the selected body. Same time and place.', ratio),
          Spacer(1, 4),
          pair(pre + 'sky_night.png', pre + 'alm.png',
               '<b>HORIZON</b> at night: 23 Sep 2026 03:00 UT, 30° N 0° E (the Sun below the horizon).', '', ratio),
          P('6. The text menu', h2),
          P('nav.py alone (Execute script, or <b>menu()</b> in the shell) is the text version: 1 Sun, 2 Star, 3 Rise/Set, '
            '4 Moon phase, 5 Almanac (the same page as the ALMANAC view, as text).'),
          P('7. Memory and size', h2)]
    if nw:
        S += B(['The five files are about 26 KB. The star data of navdata.py take about 15 KB of the Python heap.',
                'Epsilon 19 or later (64 KB heap) or Upsilon / Omega (about 100 KB): fine. Epsilon before 19 (32 KB heap): '
                'close to the limit — if you get MemoryError, update Epsilon or use Upsilon, and do not import other '
                'scripts in the same session.'])
    else:
        S += B(['The six files are about 26 KB; the Prime\'s Python memory is far larger than needed.',
                'Text goes through the PPL command TEXTOUT_P (font size and colour), keys through GETKEY.'])
    S += [P('8. Status', h2)] + B([
        'Not yet tried on a real %s. Checked on a PC (stand-in module) and in a MicroPython interpreter.' % name] +
        ([] if nw else ['Not sure on the real Prime: the exact pixel size of its fonts (columns may be a few pixels off) and '
                        'whether ESC reaches GETKEY in every firmware (ON always stops the program).']))
    make(os.path.join(DOCS, 'Almanac47_%s_Manual.pdf' % key), '%s — user manual' % name, S)


if __name__ == '__main__':
    free42()
    python_port('NumWorks', 'NumWorks')
    python_port('HP Prime', 'HPPrime')
