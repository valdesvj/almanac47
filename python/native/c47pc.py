#!/usr/bin/env python3
"""c47pc.py - the C47_nav screens on a PC, calculated in Python.

Stand-alone: no C47 programs and no simulator. The Sun, Moon, planets, stars,
sunrise/twilight and Moon phase are calculated in c47astro.py with the same
methods and coefficients as the calculator programs, and c47screen.py draws the
C47 screens (ALMF, HALMV, HORZ, HORZS) with the same fonts and layout.
Tested pixel for pixel against the calculator programs (75 dates and places).

Two ways to use it
  1. Window (GTK 3):      python3 c47pc.py
  2. PNG / text only:     python3 c47pc.py --view HALMV --date 2026-09-25 --ut 18:30 \
                                  --lat "25 20 N" --lon "55 12 E" --png halmv.png
     ALMT (text almanac) prints its lines:   ... --view ALMT
     HORZ info frames (one per object):      ... --view HORZ --png horz.png --all-frames
     Menu Info: Help and About (version).    --version prints the version.
     Online check against JPL Horizons:      ... --check  (menu Info as well)

Times are UT (UT1), as on the calculator. Latitude N+ / longitude E+, or
written with N S E W ("25 20.0 N", "55 12 E", "25.3333", "-75.5").
Files needed (same folder): c47pc.py c47astro.py c47screen.py c47font.py c47data.py
                            c47tables.py, jplcheck.py; optional TBL.txt (almanac tables)
PNG and text need Python 3 only; the window needs PyGObject + cairo + GTK 3
(Arch: pacman -S python-gobject python-cairo gtk3
 Debian/Ubuntu: apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0).
DOES NOT REPLACE THE NAUTICAL ALMANAC.
"""
import argparse, datetime, os, re, struct, sys, time, zlib
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c47screen
import c47tables

VERSION = '1.1'
VERSION_DATE = '2026-09-26'
PROGRAM = 'C47 Nav PC'
ABOUT = ("This program began as a set of RPN programs for the SwissMicros C47 calculator: "
         "Sun, Moon, planets and the 57 navigational stars, sight reduction, and the almanac "
         "and horizon screens drawn pixel by pixel on its display.\n\n"
         "On the calculator each screen takes about 35 seconds to draw. Here it takes a blink. "
         "For the authentic experience, count to 35 before looking.\n\n"
         "Same methods and coefficients as the calculator programs: VSOP87D (Sun, planets), "
         "Meeus 47 + corrections fitted to JPL DE421 (Moon), IAU2006 precession (stars), "
         "IAU1980 nutation. The screens are the same as on the calculator, checked pixel for pixel.\n\n"
         "Phones and computers should not be used for navigation or during operations on the bridge. "
         "If you find these programs useful, grab a DM42n or an R47, bring the calculator on board, "
         "and make good use of the sextant and the Nautical Almanac.\n\n"
         "Thanks to the developers of the C43 / C47 firmware for such an open, programmable machine, "
         "and to SwissMicros for the hardware that makes it a pleasure to use.\n\n"
         "Not affiliated with or endorsed by SwissMicros or the C43/C47 project. "
         "Names are trademarks of their owners.\n\n"
         "DOES NOT REPLACE THE NAUTICAL ALMANAC.")
HELP = """INPUT
  Date     YYYY-MM-DD (or DD-MM-YYYY), UT date
  UT       hh:mm or hh:mm:ss  (UT1; add DUT1 to UTC for full accuracy)
  Lat      25 20.0 N   or  25.3333   (S or minus for south)
  Lon      55 12.0 E   or  -75.5     (W or minus for west)
  Now UTC  fills in the current date and time and runs

VIEWS (same as on the C47)
  ALMF   full-page almanac: GHA, Dec, Hc, Zn of the Sun, the Moon and planets
         above the horizon, and the brightest stars above 10 deg (10 rows);
         twilight, sunrise/sunset, meridian passage, Sun SD, Moon phase, HP, SD
  HALMV  horizon chart on the left, Hc/Zn table and times on the right
  HORZ   full-screen horizon chart; R/S steps through the objects (name, Zn, Hc)
  HORZS  horizon chart only
  ALMT   text almanac, one page of two lines per R/S (as PROMPT on the C47)

MARKS
  Hc underlined (ALMF, HALMV) or line starting with "* " (ALMT):
  the body is below the horizon (only the Sun can be).
  Stars carry their Nautical Almanac number (1-57, 58 = Polaris).

OPTIONS
  LCD colours     grey LCD look, or black on white

KEYS
  Enter (in a field) = Run      Enter / Space elsewhere = R/S (next object or line)

SAVE
  Save PNG saves the screen shown (ALMT: the text lines as .txt).

COMMAND LINE
  python3 c47pc.py --view HALMV --date 2026-09-25 --ut 18:30 \\
          --lat "25 20 N" --lon "55 12 E" --png halmv.png
  python3 c47pc.py --view ALMT --date ... --lat ... --lon ...   (prints the lines)
  python3 c47pc.py --help    all options

ALMANAC TABLES  (T / S in the corner of every screen)
  With TBL.txt (programs/ folder, the same file loaded on the C47) the Sun,
  Aries, Moon and planets come from the Chebyshev tables (JPL) inside the
  table period, and the screens show T; outside it, or with the box off,
  they come from the series and show S. Stars always from the series.
  On the C47: XEQ "TBL" once (sets flag 10); CF 10 = use the series.
  Command line: --tables FILE, or --series to switch them off.

CHECK AGAINST JPL (link under the screen, menu Info, or --check; PC only,
  needs internet). Opens a window listing every value of the C47 method beside
  the JPL value and the difference. Compares GHA and Dec of the Sun, Moon, planets and GHA Aries with JPL
  Horizons (DE440) for the date and UT entered, in arcminutes. JPL reads the
  time as UTC and the C47 uses UT1: DUT1 (under 0.9 s) moves GHA by up to
  0.23' but not Dec. Stars are not checked.

ON BOARD
  Phones and computers should not be used for navigation or during operations
  on the bridge. If you find these programs useful, grab a DM42n or an R47,
  bring the calculator on board, and make good use of the sextant and the
  Nautical Almanac.

DOES NOT REPLACE THE NAUTICAL ALMANAC."""

W, H = 400, 240
VIEWS = ['ALMF', 'HALMV', 'HORZ', 'HORZS', 'ALMT', 'ALMS', 'HALMH']
VIEW_TEXT = {'ALMF': 'full-page almanac', 'HALMV': 'chart + almanac data',
             'HORZ': 'horizon chart + info per object', 'HORZS': 'horizon chart',
             'ALMT': 'text almanac, one line per R/S', 'ALMS': 'short almanac: Sun, Moon, 1 planet, 3 stars',
             'HALMH': 'horizon chart on top, short almanac below'}

# LCD look (SwissMicros memory LCD: pale grey glass, near-black pixels)
LCD_BG = (0xD9, 0xDC, 0xD2)
LCD_ON = (0x1C, 0x1F, 0x1C)
BEZEL = (0x2A, 0x2A, 0x2C)
PLAIN_BG, PLAIN_ON = (255, 255, 255), (0, 0, 0)


# ------------------------------------------------------------------ ALMT pages
def page_lines(p):
    """An ALMT page split as the C47 PROMPT shows it (400 px lines, proportional font)."""
    return [l.rstrip() for l in c47screen.prompt_lines(p)]


def pages_text(pages):
    """The ALMT pages as a text file: the monospace layout when there is one."""
    mono = getattr(pages, 'mono', None)
    if mono:
        return '\n\n'.join('\n'.join(l.rstrip() for l in p) for p in mono)
    return '\n\n'.join('\n'.join(page_lines(p)) for p in pages)


# ------------------------------------------------------------------ input
def jd(y, m, d, h=0.0):
    """Julian Day, same formula as the suite (NAV)."""
    return c47screen.A.jd(y, m, d, h)


def parse_angle(s, pos, neg, limit):
    """'25.3333'  '-75.5'  '25 20.0 N'  "25°20.0'N"  '55 12 E' -> decimal degrees."""
    t = s.strip().upper()
    sign = 1
    for ch in pos + neg:
        if ch in t:
            if ch in neg: sign = -1
            t = t.replace(ch, ' ')
    nums = re.findall(r'-?\d+(?:\.\d*)?', t)
    if not nums or len(nums) > 3:
        raise ValueError('cannot read "%s"' % s)
    v = [float(n) for n in nums]
    if v[0] < 0: sign, v[0] = -sign, -v[0]
    deg = v[0] + (v[1] / 60 if len(v) > 1 else 0) + (v[2] / 3600 if len(v) > 2 else 0)
    if deg > limit:
        raise ValueError('"%s" out of range' % s)
    return sign * deg


def parse_date(s):
    y, m, d = [int(x) for x in re.split(r'[-/.]', s.strip())]
    if d > 31:  # allow DD-MM-YYYY too
        y, d = d, y
    datetime.date(y, m, d)
    return y, m, d


def parse_ut(s):
    p = [float(x) for x in s.strip().split(':')] + [0, 0]
    h = p[0] + p[1] / 60 + p[2] / 3600
    if not 0 <= h < 24:
        raise ValueError('UT must be 00:00 to 23:59')
    return h


# ------------------------------------------------------------------ engine
class Engine:
    """Same interface as the simulator engine of c47view.py, native calculations.
    tables: path of TBL.txt (almanac tables) or None; use = on/off switch (flag 10)."""

    def __init__(self, tables=None):
        self.tables = c47tables.Tables(tables) if tables else None
        self.use = bool(self.tables)
        self.last = None

    def _al(self, j, lat, lon):
        self.last = c47screen.Almanac(j, lat, lon, self.tables if self.use else None)
        return self.last

    def screen(self, view, j, lat, lon):
        return c47screen.VIEWS[view](self._al(j, lat, lon)), None

    def text(self, j, lat, lon):
        return c47screen.almt(self._al(j, lat, lon)), None


# ------------------------------------------------------------------ PNG
def render_rgb(pixels, scale=3, lcd=True, bezel=True):
    """Return (width, height, bytearray RGB) of the screen."""
    bg, on = (LCD_BG, LCD_ON) if lcd else (PLAIN_BG, PLAIN_ON)
    b = (6 * scale) if bezel else 0
    gap = 1 if (lcd and scale >= 4) else 0          # tiny gap between LCD dots
    w, h = W * scale + 2 * b, H * scale + 2 * b
    buf = bytearray(bytes(BEZEL) * (w * h)) if bezel else bytearray()
    if not bezel:
        buf = bytearray(bytes(bg) * (w * h))
    else:
        row = bytes(bg) * (W * scale)
        for yy in range(H * scale):
            o = ((yy + b) * w + b) * 3
            buf[o:o + len(row)] = row
    dot = bytes(on) * (scale - gap)
    for (x, r) in pixels:
        for dy in range(scale - gap):
            o = ((b + r * scale + dy) * w + b + x * scale) * 3
            buf[o:o + len(dot)] = dot
    return w, h, buf


def write_png(fn, w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(fn, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                 + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


# ------------------------------------------------------------------ GTK window
def run_gtk(eng, args):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk, GLib

    class JplWindow(Gtk.Window):
        """Every value of the C47 method beside JPL Horizons, with the difference."""

        def __init__(self, parent):
            super().__init__(title='%s - Check against JPL' % PROGRAM)
            self.parent_win = parent
            self.set_transient_for(parent); self.set_default_size(700, 520)
            self.connect('delete-event', self.on_close)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); v.set_border_width(12); self.add(v)
            self.head = Gtk.Label(xalign=0); v.pack_start(self.head, False, False, 0)
            self.grid = Gtk.Grid(column_spacing=18, row_spacing=4)
            sw = Gtk.ScrolledWindow(); sw.set_vexpand(True); sw.add(self.grid); v.pack_start(sw, True, True, 0)
            self.notes = Gtk.Label(xalign=0); self.notes.set_line_wrap(True); v.pack_start(self.notes, False, False, 0)
            hb = Gtk.Box(spacing=6); v.pack_start(hb, False, False, 0)
            b = Gtk.Button(label='Check again (date and UT of the main window)')
            b.connect('clicked', lambda *_: parent.on_check()); hb.pack_start(b, False, False, 0)
            c = Gtk.Button(label='Close'); c.connect('clicked', lambda *_: self.on_close()); hb.pack_end(c, False, False, 0)

        def on_close(self, *_):
            self.hide(); return True

        def _cell(self, text, col, row, xalign=0.0, bold=False, mono=True):
            l = Gtk.Label(xalign=xalign)
            t = GLib.markup_escape_text(text)
            if mono:
                t = '<tt>%s</tt>' % t
            if bold:
                t = '<b>%s</b>' % t
            l.set_markup(t); self.grid.attach(l, col, row, 1, 1)

        def run_check(self, j, when):
            import threading, jplcheck
            for ch in self.grid.get_children():
                self.grid.remove(ch)
            self.head.set_markup('<b>%s</b>   JD %.5f\nAsking JPL Horizons (internet) ...' % (when, j))
            self.notes.set_text('')
            self.show_all(); self.present()
            tables = eng.tables if eng.use else None

            def work():
                try:
                    res = jplcheck.check(j, tables)
                    err = None
                except Exception as ex:
                    res, err = None, ex
                GLib.idle_add(self.show_result, j, when, res, err)

            threading.Thread(target=work, daemon=True).start()

        def show_result(self, j, when, res, err):
            if err is not None:
                self.head.set_markup('<b>%s</b>   JD %.5f\n<b>JPL check failed</b> - an internet connection is needed.' % (when, j))
                self.notes.set_text(str(err)); return False
            R, notes = res
            src = 'almanac tables' if any(r[5] == 'T' for r in R) else 'series'
            self.head.set_markup('<b>%s</b>   JD %.5f   C47 method from the %s\nJPL Horizons, ephemeris DE440 (apparent geocentric)' % (when, j, src))
            for c, (t, xa) in enumerate((('Body', 0), ('', 0), ('C47 method', 1), ('JPL Horizons', 1), ("Difference '", 1), ('Source', 0.5))):
                self._cell(t, c, 0, xa, bold=True, mono=False)
            for r, (body, q, o, jv, d, s) in enumerate(R, start=1):
                self._cell(body, 0, r); self._cell(q, 1, r)
                self._cell(o, 2, r, 1); self._cell(jv, 3, r, 1)
                self._cell('%+8.3f' % d, 4, r, 1, bold=abs(d) >= 0.1); self._cell(s, 5, r, 0.5)
            self.notes.set_text('\n'.join(notes + ['Differences of 0.1\' or more are in bold.']))
            self.grid.show_all()
            self.parent_win.status.set_text('JPL check done')
            return False

    class Win(Gtk.Window):
        def __init__(self):
            super().__init__(title='%s %s' % (PROGRAM, VERSION))
            self.scale = args.scale
            self.lcd = not args.plain
            self.frames = [set()]; self.lines = []; self.k = 0; self.view = args.view or 'HALMV'
            self.connect('destroy', Gtk.main_quit)
            self.connect('key-press-event', self.on_key)
            outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0); self.add(outer)
            mb = Gtk.MenuBar(); outer.pack_start(mb, False, False, 0)
            info = Gtk.MenuItem.new_with_mnemonic('_Info'); mb.append(info)
            menu = Gtk.Menu(); info.set_submenu(menu)
            for lbl, cb in (('_Help', self.on_help), ('_About', self.on_about), (None, None),
                            ('_Check against JPL (online)', self.on_check), (None, None), ('_Quit', Gtk.main_quit)):
                if lbl is None:
                    menu.append(Gtk.SeparatorMenuItem()); continue
                it = Gtk.MenuItem.new_with_mnemonic(lbl); it.connect('activate', lambda w, f=cb: f()); menu.append(it)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_border_width(8); outer.pack_start(box, True, True, 0)

            now = datetime.datetime.now(datetime.timezone.utc)
            g = Gtk.Grid(column_spacing=6, row_spacing=4); box.pack_start(g, False, False, 0)
            self.e_date = self._entry(g, 0, 'Date (YYYY-MM-DD)', args.date or now.strftime('%Y-%m-%d'), 11)
            self.e_ut = self._entry(g, 2, 'UT (hh:mm)', args.ut or now.strftime('%H:%M'), 6)
            self.e_lat = self._entry(g, 4, 'Lat', args.lat or '25 20.0 N', 11)
            self.e_lon = self._entry(g, 6, 'Lon', args.lon or '55 12.0 E', 11)
            b_now = Gtk.Button(label='Now UTC'); b_now.connect('clicked', self.on_now)
            g.attach(b_now, 8, 0, 1, 1)

            hb = Gtk.Box(spacing=4); box.pack_start(hb, False, False, 0)
            first = None; self.radios = {}
            for v in VIEWS:
                r = Gtk.RadioButton.new_with_label_from_widget(first, v)
                r.set_tooltip_text(VIEW_TEXT[v]); first = first or r
                hb.pack_start(r, False, False, 0); self.radios[v] = r
            self.radios[self.view].set_active(True)
            for v, r in self.radios.items():
                r.connect('toggled', self.on_view, v)
            for lbl, cb in (('Run', self.on_run), ('R/S  next', self.on_next), ('Save PNG', self.on_save)):
                b = Gtk.Button(label=lbl); b.connect('clicked', cb); hb.pack_end(b, False, False, 0)
            chk = Gtk.CheckButton(label='LCD colours'); chk.set_active(self.lcd)
            chk.connect('toggled', self.on_lcd); hb.pack_end(chk, False, False, 6)
            ct = Gtk.CheckButton(label='Almanac tables'); ct.set_active(eng.use)
            ct.set_sensitive(eng.tables is not None)
            ct.set_tooltip_text(('%s (%s)' % (eng.tables.period, eng.tables.path)) if eng.tables
                                else 'TBL.txt not found (programs/ or next to c47pc.py)')
            ct.connect('toggled', self.on_tables); hb.pack_end(ct, False, False, 6)

            self.area = Gtk.DrawingArea()
            b = 6 * self.scale
            self.area.set_size_request(W * self.scale + 2 * b, H * self.scale + 2 * b)
            self.area.connect('draw', self.on_draw)
            box.pack_start(self.area, False, False, 0)
            self.status = Gtk.Label(label='Enter date, UT and position, choose a view, press Run (or Enter).',
                                    xalign=0)
            sb = Gtk.Box(spacing=8); box.pack_start(sb, False, False, 0)
            sb.pack_start(self.status, True, True, 0)
            jl = Gtk.Label(); jl.set_markup('<a href="jpl">Check against JPL (online) \u203a</a>')
            jl.set_tooltip_text('Opens a window with every value of the C47 method beside JPL Horizons and the difference')
            jl.connect('activate-link', lambda w, uri: (self.on_check(), True)[1])
            sb.pack_end(jl, False, False, 0)
            self.show_all()
            if args.date or args.ut:
                self.on_run()

        def _entry(self, g, col, label, text, width):
            g.attach(Gtk.Label(label=label, xalign=1), col, 0, 1, 1)
            e = Gtk.Entry(); e.set_text(text); e.set_width_chars(width)
            e.connect('activate', self.on_run); g.attach(e, col + 1, 0, 1, 1)
            return e

        # --- actions
        def inputs(self):
            y, m, d = parse_date(self.e_date.get_text())
            h = parse_ut(self.e_ut.get_text())
            lat = parse_angle(self.e_lat.get_text(), 'N', 'S', 90)
            lon = parse_angle(self.e_lon.get_text(), 'E', 'WO', 180)
            return jd(y, m, d, h), lat, lon

        def on_now(self, *_):
            now = datetime.datetime.now(datetime.timezone.utc)
            self.e_date.set_text(now.strftime('%Y-%m-%d')); self.e_ut.set_text(now.strftime('%H:%M'))
            self.on_run()

        def on_view(self, radio, v):
            if radio.get_active():
                self.view = v; self.on_run()

        def on_help(self):
            d = Gtk.Dialog(title='%s - Help' % PROGRAM, transient_for=self, modal=True)
            d.add_button('Close', Gtk.ResponseType.CLOSE)
            d.set_default_size(800, 640)
            sw = Gtk.ScrolledWindow(); sw.set_vexpand(True)
            tv = Gtk.TextView(); tv.set_editable(False); tv.set_monospace(True); tv.set_left_margin(10)
            tv.set_top_margin(8); tv.get_buffer().set_text(HELP); sw.add(tv)
            d.get_content_area().pack_start(sw, True, True, 0)
            d.show_all(); d.run(); d.destroy()

        def on_check(self, *_):
            """Open (or refresh) the JPL check window for the date and UT entered."""
            try:
                y, m, d = parse_date(self.e_date.get_text()); h = parse_ut(self.e_ut.get_text())
            except Exception as ex:
                self.status.set_text('Input error: %s' % ex); return
            if getattr(self, 'jplwin', None) is None:
                self.jplwin = JplWindow(self)
            self.jplwin.run_check(jd(y, m, d, h), '%04d-%02d-%02d  %s UT' % (y, m, d, self.e_ut.get_text()))

        def on_about(self):
            d = Gtk.AboutDialog(transient_for=self, modal=True)
            d.set_program_name(PROGRAM); d.set_version('%s  (%s)' % (VERSION, VERSION_DATE))
            d.set_comments(ABOUT)
            d.run(); d.destroy()

        def on_tables(self, chk):
            eng.use = chk.get_active(); self.on_run()

        def on_lcd(self, chk):
            self.lcd = chk.get_active(); self.area.queue_draw()

        def on_run(self, *_):
            try:
                j, lat, lon = self.inputs()
            except Exception as ex:
                self.status.set_text('Input error: %s' % ex); return
            t0 = time.time()
            try:
                if self.view == 'ALMT':
                    self.lines, n = eng.text(j, lat, lon); self.frames = [set()]
                else:
                    self.frames, n = eng.screen(self.view, j, lat, lon); self.lines = []
            except Exception as ex:
                self.status.set_text('Program error: %s' % ex); return
            self.k = 0
            self.steps = n; self.secs = time.time() - t0
            self.update_status(); self.area.queue_draw()

        def update_status(self):
            extra = ''
            if self.view == 'ALMT' and self.lines:
                extra = '   page %d/%d (R/S = Enter or Space)' % (self.k + 1, len(self.lines))
            elif len(self.frames) > 1:
                extra = '   object %d/%d (R/S = Enter or Space)' % (self.k + 1, len(self.frames))
            grey = '   grey = next pages' if self.view == 'ALMT' else ''
            src = ''
            if eng.last is not None:
                src = '   %s = %s' % (eng.last.source, 'almanac tables (%s)' % eng.tables.period
                                      if eng.last.moon_t else 'series')
            self.status.set_text('%s (%.2f s)%s%s%s' % (self.view, self.secs, src, extra, grey))

        def on_next(self, *_):
            n = len(self.lines) if self.view == 'ALMT' else len(self.frames)
            if n:
                self.k = (self.k + 1) % n; self.update_status(); self.area.queue_draw()

        def on_key(self, w, ev):
            if ev.keyval in (Gdk.KEY_space, Gdk.KEY_KP_Enter) or (
                    ev.keyval == Gdk.KEY_Return and not isinstance(self.get_focus(), Gtk.Entry)):
                self.on_next(); return True
            return False

        def on_save(self, *_):
            if self.view == 'ALMT':
                dlg = Gtk.FileChooserDialog(title='Save ALMT text', parent=self,
                                            action=Gtk.FileChooserAction.SAVE)
                dlg.set_current_name('ALMT.txt')
            else:
                dlg = Gtk.FileChooserDialog(title='Save PNG', parent=self, action=Gtk.FileChooserAction.SAVE)
                dlg.set_current_name('%s.png' % self.view)
            dlg.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            dlg.set_do_overwrite_confirmation(True)
            if dlg.run() == Gtk.ResponseType.OK:
                fn = dlg.get_filename()
                if self.view == 'ALMT':
                    with open(fn, 'w', encoding='utf-8') as fh:
                        fh.write(pages_text(self.lines) + '\n')
                else:
                    write_png(fn, *render_rgb(self.frames[self.k], self.scale, self.lcd, True))
                self.status.set_text('Saved %s' % fn)
            dlg.destroy()

        # --- drawing
        def on_draw(self, area, cr):
            s = self.scale; b = 6 * s
            bg, on = (LCD_BG, LCD_ON) if self.lcd else (PLAIN_BG, PLAIN_ON)
            cr.set_source_rgb(*[v / 255 for v in BEZEL]); cr.paint()
            cr.set_source_rgb(*[v / 255 for v in bg]); cr.rectangle(b, b, W * s, H * s); cr.fill()
            cr.set_source_rgb(*[v / 255 for v in on])
            if self.view == 'ALMT':
                self.draw_text(cr, s, b); return
            gap = 1 if (self.lcd and s >= 4) else 0
            for (x, r) in self.frames[self.k]:
                cr.rectangle(b + x * s, b + r * s, s - gap, s - gap)
            cr.fill()

        def draw_text(self, cr, s, b):
            """ALMT: one page (two PROMPT lines of 400 px) per R/S. The C47 font is not
            available on the PC; each character is placed at its C47 pixel position
            (c47screen.CHAR_W), so the columns line up as on the calculator. The next
            pages are shown smaller, in grey, below."""
            if not self.lines:
                return

            def line(part, x, y, k):
                for c in part:
                    cr.move_to(x, y); cr.show_text(c); x += c47screen.CHAR_W.get(c, 8) * k

            cr.select_font_face('DejaVu Sans', 0, 1)
            k = 0.98 * s
            cr.set_font_size(13 * k)
            y = b + 18 * s
            for part in page_lines(self.lines[self.k]):
                line(part, b + 4 * s, y, k); y += 16 * s
            cr.set_source_rgba(*[v / 255 for v in LCD_ON], 0.45)
            k = 0.62 * s
            cr.set_font_size(13 * k)
            y += 6 * s
            for i in range(1, len(self.lines)):
                for part in page_lines(self.lines[(self.k + i) % len(self.lines)]):
                    if y > b + 234 * s:
                        return
                    line(part, b + 4 * s, y, k); y += 10 * s
                y += 4 * s

    Win()
    Gtk.main()


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description='C47_nav screens on the PC (native Python calculations).')
    ap.add_argument('--view', choices=VIEWS, help='ALMF HALMV HORZ HORZS ALMT ALMS HALMH (default HALMV)')
    ap.add_argument('--date', help='YYYY-MM-DD (default: today UTC)')
    ap.add_argument('--ut', help='hh:mm or hh:mm:ss UT (default: now)')
    ap.add_argument('--lat', help='e.g. "25 20.0 N" or 25.3333')
    ap.add_argument('--lon', help='e.g. "55 12.0 E" or -75.5')
    ap.add_argument('--png', help='write the screen to this PNG file (no window)')
    ap.add_argument('--all-frames', action='store_true', help='HORZ: one PNG per object (_0, _1, ...)')
    ap.add_argument('--scale', type=int, default=3, help='pixels per C47 pixel (default 3)')
    ap.add_argument('--plain', action='store_true', help='black on white instead of LCD colours')
    ap.add_argument('--no-bezel', action='store_true', help='PNG without the dark frame')
    ap.add_argument('--check', action='store_true', help='online: compare Sun, Moon, planets and Aries with JPL Horizons')
    ap.add_argument('--tables', help='almanac tables TBL.txt (default: programs/TBL.txt or next to this file)')
    ap.add_argument('--series', action='store_true', help='do not use the almanac tables (like CF 10 on the C47)')
    ap.add_argument('--body', type=int, help='BODY: list the bodies above the horizon; with a number (1-58 stars, 60 Sun, 61 Moon, 62-65 planets) also its pages and, with --png, its chart')
    ap.add_argument('--version', action='version', version='%s %s (%s)' % (PROGRAM, VERSION, VERSION_DATE))
    args = ap.parse_args()

    if args.check:
        import jplcheck
        now = datetime.datetime.now(datetime.timezone.utc)
        y, m, d = parse_date(args.date or now.strftime('%Y-%m-%d'))
        h = parse_ut(args.ut or now.strftime('%H:%M'))
        try:
            print(jplcheck.report(jd(y, m, d, h), None if args.series else (c47tables.Tables(args.tables or c47tables.find()) if (args.tables or c47tables.find()) else None)))
        except Exception as ex:
            sys.exit('JPL check failed (internet connection needed): %s' % ex)
        return

    eng = Engine(None if args.series else (args.tables or c47tables.find()))
    batch = bool(args.png) or (args.view == 'ALMT' and bool(args.lat)) or args.body is not None
    if not batch:
        try:
            run_gtk(eng, args); return
        except (ImportError, ValueError) as ex:
            print('GTK 3 window not available (%s); use --png. See the notes at the top of this file.' % ex)
            return

    now = datetime.datetime.now(datetime.timezone.utc)
    y, m, d = parse_date(args.date or now.strftime('%Y-%m-%d'))
    h = parse_ut(args.ut or now.strftime('%H:%M'))
    if not (args.lat and args.lon):
        sys.exit('give --lat and --lon')
    lat = parse_angle(args.lat, 'N', 'S', 90); lon = parse_angle(args.lon, 'E', 'WO', 180)
    j = jd(y, m, d, h)
    view = args.view or 'HALMV'
    if args.body is not None:
        al = eng._al(j, lat, lon)
        codes, pages = c47screen.body_list(al)
        print('\n\n'.join('\n'.join(page_lines(p)) for p in pages + [c47screen.body_legend()]))
        if args.body in c47screen.BODY_NAMES or 1 <= args.body <= 58:
            print()
            print('\n\n'.join('\n'.join(page_lines(p)) for p in c47screen.body_pages(al, args.body)))
            if args.png:
                write_png(args.png, *render_rgb(c47screen.body_chart(al, args.body)[0], args.scale, not args.plain, not args.no_bezel))
                print('%s written' % args.png)
        return
    if view == 'ALMT':
        lines, n = eng.text(j, lat, lon)
        print(pages_text(lines))
        if args.png:
            with open(os.path.splitext(args.png)[0] + '.txt', 'w', encoding='utf-8') as fh:
                fh.write(pages_text(lines) + '\n')
        return
    frames, n = eng.screen(view, j, lat, lon)
    if args.all_frames and len(frames) > 1:
        base, ext = os.path.splitext(args.png)
        for i, fr in enumerate(frames):
            write_png('%s_%d%s' % (base, i, ext or '.png'),
                      *render_rgb(fr, args.scale, not args.plain, not args.no_bezel))
        print('%s: %d frames written' % (view, len(frames)))
    else:
        write_png(args.png, *render_rgb(frames[0], args.scale, not args.plain, not args.no_bezel))
        print('%s written' % args.png)


if __name__ == '__main__':
    main()
