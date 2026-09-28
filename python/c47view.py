#!/usr/bin/env python3
"""c47view.py - the C47_nav screens on a PC, pixel for pixel.

The picture is NOT redrawn in Python: c47sim.py runs the real C47 programs
(../programs/*.txt: ALMF, HALMV, HORZ, HORZS, ALMT and everything they call)
and keeps the calculator's 400 x 240 one-bit screen. So the PC shows exactly
what the C47 shows, with the same numbers and the same AGRAPH fonts.

Two ways to use it
  1. Window (GTK 3):      python3 c47view.py
  2. PNG / text only:     python3 c47view.py --view HALMV --date 2026-09-25 --ut 18:30 \
                                  --lat "25 20 N" --lon "55 12 E" --png halmv.png
     ALMT (text almanac) prints its lines:   ... --view ALMT
     HORZ info frames (one per object):      ... --view HORZ --png horz.png --all-frames

Times are UT (UT1), as on the calculator. Latitude N+ / longitude E+, or
written with N S E W ("25 20.0 N", "55 12 E", "25.3333", "-75.5").
Needs Python 3 only; the window needs PyGObject + GTK 3
(Arch: pacman -S python-gobject python-cairo gtk3
 Debian/Ubuntu: apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0).
DOES NOT REPLACE THE NAUTICAL ALMANAC.
"""
import argparse, datetime, os, re, struct, sys, time, zlib
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c47sim

W, H = 400, 240
VIEWS = ['ALMF', 'HALMV', 'HORZ', 'HORZS', 'ALMT']
VIEW_TEXT = {'ALMF': 'full-page almanac', 'HALMV': 'chart + almanac data',
             'HORZ': 'horizon chart + info per object', 'HORZS': 'horizon chart',
             'ALMT': 'text almanac, one line per R/S'}
FILES = ['MATA', 'MATST', 'MATM', 'MATP', 'SUNA', 'STAR', 'CHZ', 'SNMU', 'SBRT', 'MOON',
         'PLAN', 'PTXB', 'PTXS', 'PTXT', 'SUNRISE', 'PHAS', 'STXT',
         'ALMF', 'HALMV', 'HORZ', 'HORZS', 'ALMT', 'TGET', 'CWID', 'ALMS', 'HALMH', 'BODY', 'HANIM', 'ALLSKY', 'MATF', 'WPLS']

# LCD look (SwissMicros memory LCD: pale grey glass, near-black pixels)
LCD_BG = (0xD9, 0xDC, 0xD2)
LCD_ON = (0x1C, 0x1F, 0x1C)
BEZEL = (0x2A, 0x2A, 0x2C)
PLAIN_BG, PLAIN_ON = (255, 255, 255), (0, 0, 0)


# ------------------------------------------------------------------ input
def jd(y, m, d, h=0.0):
    """Julian Day, same formula as the suite (NAV / nav.py)."""
    if m <= 2:
        y -= 1; m += 12
    a = y // 100; b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24.0


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
    """Loads the C47 programs once, builds the matrices (NAV option INIT) once."""

    def __init__(self, progdir=None, tables=False, fast=False):
        """tables=True also loads and runs TBL (almanac tables, flag 10), like on the C47.
        fast=True runs MATF after MATA/MATP (FAST series, as INIT option 2)."""
        progdir = progdir or os.path.join(HERE, '..', 'programs')
        files = FILES + (['TBL'] if tables else [])
        missing = [f for f in files if not os.path.exists(os.path.join(progdir, f + '.txt'))]
        if missing:
            raise FileNotFoundError('programs not found in %s: %s' % (progdir, ' '.join(missing)))
        self.c = c47sim.load([os.path.join(progdir, f + '.txt') for f in files])
        for m in ('MATA', 'MATST', 'MATM', 'MATP') + (('MATF',) if fast else ()) + (('TBL',) if tables else ()):
            self.c.run(m, maxsteps=10 ** 7)

    def _start(self, j, lat, lon):
        c = self.c
        c.steps = 0; c.pix = []; c.frames = []; c.msgs = []; c.stops = []; c.answers = []
        c.s = [D(0)] * 4; c.lift = True
        c.push(D(repr(j))); c.push(D(repr(lat))); c.push(D(repr(lon)))

    def screen(self, view, j, lat, lon):
        """Run ALMF / HALMV / HORZ / HORZS. Returns (list of frames, steps).
        A frame is a set of lit pixels (x, row) with row 0 at the top."""
        self._start(j, lat, lon)
        self.c.maxpauses = 11 if view == 'HORZ' else None    # HORZ repeats its info frames forever
        self.c.keys = [11] * 20 if view == 'HORZ' else []     # HORZ: any key (not +) shows the next body
        try:
            self.c.run(view, maxsteps=10 ** 7)
        except StopIteration:
            pass
        self.c.maxpauses = None
        if view == 'HORZ' and self.c.frames:
            self.c.frames = self.c.frames[:int(self.c.rget('10'))]   # one cycle (R10 objects)
        raw = self.c.frames if (view == 'HORZ' and self.c.frames) else [self.c.pix]
        frames = []
        for fr in raw:
            frames.append({(x, H - 1 - y) for y, x in fr if 0 <= x < W and 0 <= y < H})
        return frames, self.c.steps

    def text(self, j, lat, lon):
        """Run ALMT; returns (lines, steps). One cycle of lines, as shown by R/S."""
        self._start(j, lat, lon)
        self.c.maxprompts = 120
        try:
            self.c.run('ALMT', maxsteps=10 ** 7)
        except StopIteration:
            pass
        m = [str(x) for x in self.c.msgs]
        if m and m[0] in m[1:]:
            m = m[:m.index(m[0], 1)]
        return m, self.c.steps


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
    from gi.repository import Gtk, Gdk

    class Win(Gtk.Window):
        def __init__(self):
            super().__init__(title='C47 Nav viewer')
            self.scale = args.scale
            self.lcd = not args.plain
            self.frames = [set()]; self.lines = []; self.k = 0; self.view = args.view or 'HALMV'
            self.connect('destroy', Gtk.main_quit)
            self.connect('key-press-event', self.on_key)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_border_width(8); self.add(box)

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

            self.area = Gtk.DrawingArea()
            b = 6 * self.scale
            self.area.set_size_request(W * self.scale + 2 * b, H * self.scale + 2 * b)
            self.area.connect('draw', self.on_draw)
            box.pack_start(self.area, False, False, 0)
            self.status = Gtk.Label(label='Enter date, UT and position, choose a view, press Run (or Enter).',
                                    xalign=0)
            box.pack_start(self.status, False, False, 0)
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
                extra = '   line %d/%d (R/S = Enter or Space)' % (self.k + 1, len(self.lines))
            elif len(self.frames) > 1:
                extra = '   object %d/%d (R/S = Enter or Space)' % (self.k + 1, len(self.frames))
            if self.view == 'ALMT':
                self.status.set_text('ALMT (PC %.1f s)%s   grey = next lines' % (self.secs, extra))
            else:
                self.status.set_text('%s: %d program steps on the C47 (PC %.1f s)%s'
                                     % (self.view, self.steps, self.secs, extra))

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
                        fh.write('\n'.join(self.lines) + '\n')
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
            """ALMT: the calculator shows one PROMPT line at a time. The C47 font is
            not available on the PC, so a monospace font is used here."""
            if not self.lines:
                return
            cr.select_font_face('DejaVu Sans Mono', 0, 1)
            cr.set_font_size(11 * s)
            cr.move_to(b + 4 * s, b + 22 * s); cr.show_text(self.lines[self.k])
            cr.set_font_size(6 * s)
            prev = [self.lines[(self.k + i) % len(self.lines)] for i in range(1, 12)]
            cr.set_source_rgba(*[v / 255 for v in LCD_ON], 0.45)
            for i, t in enumerate(prev):
                cr.move_to(b + 4 * s, b + (48 + 16 * i) * s); cr.show_text(t)

    Win()
    Gtk.main()


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description='C47_nav screens on the PC (runs the real C47 programs).')
    ap.add_argument('--view', choices=VIEWS, help='ALMF HALMV HORZ HORZS ALMT (default HALMV)')
    ap.add_argument('--date', help='YYYY-MM-DD (default: today UTC)')
    ap.add_argument('--ut', help='hh:mm or hh:mm:ss UT (default: now)')
    ap.add_argument('--lat', help='e.g. "25 20.0 N" or 25.3333')
    ap.add_argument('--lon', help='e.g. "55 12.0 E" or -75.5')
    ap.add_argument('--png', help='write the screen to this PNG file (no window)')
    ap.add_argument('--all-frames', action='store_true', help='HORZ: one PNG per object (_0, _1, ...)')
    ap.add_argument('--scale', type=int, default=3, help='pixels per C47 pixel (default 3)')
    ap.add_argument('--plain', action='store_true', help='black on white instead of LCD colours')
    ap.add_argument('--no-bezel', action='store_true', help='PNG without the dark frame')
    ap.add_argument('--programs', help='folder with the C47 .txt programs (default ../programs)')
    args = ap.parse_args()

    eng = Engine(args.programs)
    batch = bool(args.png) or (args.view == 'ALMT' and bool(args.lat))
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
    if view == 'ALMT':
        lines, n = eng.text(j, lat, lon)
        print('\n'.join(lines))
        if args.png:
            with open(os.path.splitext(args.png)[0] + '.txt', 'w', encoding='utf-8') as fh:
                fh.write('\n'.join(lines) + '\n')
        return
    frames, n = eng.screen(view, j, lat, lon)
    if args.all_frames and len(frames) > 1:
        base, ext = os.path.splitext(args.png)
        for i, fr in enumerate(frames):
            write_png('%s_%d%s' % (base, i, ext or '.png'),
                      *render_rgb(fr, args.scale, not args.plain, not args.no_bezel))
        print('%s: %d frames written, %d C47 steps' % (view, len(frames), n))
    else:
        write_png(args.png, *render_rgb(frames[0], args.scale, not args.plain, not args.no_bezel))
        print('%s written, %d C47 steps' % (args.png, n))


if __name__ == '__main__':
    main()
