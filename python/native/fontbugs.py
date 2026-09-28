#!/usr/bin/env python3
"""fontbugs.py - invert every character of the C47_nav fonts and see what creatures come out.

Each glyph is inverted inside its own box (XOR with a solid block, like ANT on the calculator):
the letter's pixels go off and the empty space around them goes on. The A becomes an ant.

Fonts: PTXT (small 3x5), PTXB (5x7), PTXS (C47 status-bar font, 12 px).
Box:   "tight" = just the glyph's own pixels' box (no margin: the most creatures),
       "cell"  = the full character cell of the font (all glyphs the same height).

  python3 fontbugs.py                      GTK window (Linux, GTK 3)
  python3 fontbugs.py --png out.png [--font PTXS] [--box cell] [--scale 4]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c47font import BIG, SMALL
from c47fonts2 import STD

FONTS = {'PTXT (small 3x5)': SMALL, 'PTXB (5x7)': BIG, 'PTXS (status bar)': STD}
SHORT = {'PTXT': 'PTXT (small 3x5)', 'PTXB': 'PTXB (5x7)', 'PTXS': 'PTXS (status bar)'}


def pixels(glyph):
    """Set of lit (x, y) of a glyph, y up from the base line."""
    adv, off, cols = glyph
    return {(c, b + off) for c, m in cols for b in range(m.bit_length()) if m >> b & 1}


def font_rows(font):
    ys = [y for g in font.values() for _, y in pixels(g)]
    return min(ys), max(ys)


def box(font, glyph, mode):
    """(x0, x1, y0, y1) inclusive: the rectangle that is inverted."""
    p = pixels(glyph)
    if not p:
        return None
    xs, ys = [x for x, _ in p], [y for _, y in p]
    if mode == 'tight':
        return min(xs), max(xs), min(ys), max(ys)
    lo, hi = font_rows(font)
    return min(xs), max(xs), lo, hi


def inverted(font, glyph, mode):
    """Lit pixels after the XOR with the solid box."""
    b = box(font, glyph, mode)
    if b is None:
        return set()
    p = pixels(glyph)
    x0, x1, y0, y1 = b
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)} - p


def layout(font, mode, scale, per_row=12):
    """Cells: (char, normal pixels, inverted pixels); returns cells and the drawing size."""
    lo, hi = font_rows(font)
    cw = max((max((x for x, _ in pixels(g)), default=0) + 1) for g in font.values())
    cells = [(chr(k), pixels(g), inverted(font, g, mode)) for k, g in sorted(font.items()) if pixels(g)]
    cell_w = (2 * cw + 6) * scale + 16
    cell_h = (hi - lo + 1) * scale + 40
    rows = (len(cells) + per_row - 1) // per_row
    return cells, (lo, hi, cw), cell_w, cell_h, per_row, rows


LABEL = {'@': 'Sun', '(': 'Moon', '*': 'star', '<': 'Venus', '>': 'Mars', '=': 'Jupiter', '?': 'Saturn'}


def draw(cr, font, mode, scale, dark=False):
    cells, (lo, hi, cw), cell_w, cell_h, per_row, rows = layout(font, mode, scale)
    bg, ink, dim = ((0.12, 0.12, 0.13), (0.93, 0.93, 0.9), (0.5, 0.5, 0.5)) if dark else \
        ((0.87, 0.87, 0.85), (0.08, 0.08, 0.08), (0.45, 0.45, 0.45))
    cr.set_source_rgb(*bg)
    cr.paint()
    cr.select_font_face('Sans')
    cr.set_font_size(11)
    for i, (ch, norm, inv) in enumerate(cells):
        x0 = 8 + (i % per_row) * cell_w
        y0 = 8 + (i // per_row) * cell_h
        base = y0 + (hi + 1) * scale + 4
        for j, pix in enumerate((norm, inv)):
            ox = x0 + j * (cw + 3) * scale
            cr.set_source_rgb(*ink)
            for x, y in pix:
                cr.rectangle(ox + x * scale, base - (y + 1) * scale, scale, scale)
            cr.fill()
        cr.set_source_rgb(*dim)
        cr.move_to(x0, y0 + cell_h - 14)
        cr.show_text("'%s'%s" % (ch, ' ' + LABEL[ch] if ch in LABEL else ''))
    return per_row * cell_w + 16, rows * cell_h + 16


def size(font, mode, scale):
    cells, _, cell_w, cell_h, per_row, rows = layout(font, mode, scale)
    return per_row * cell_w + 16, rows * cell_h + 16


def to_png(path, font, mode, scale, dark=False):
    """Same picture as the window, drawn with PIL (no GTK needed)."""
    from PIL import Image, ImageDraw
    cells, (lo, hi, cw), cell_w, cell_h, per_row, rows = layout(font, mode, scale)
    w, h = size(font, mode, scale)
    bg, ink, dim = ((31, 31, 33), (237, 237, 230), (128, 128, 128)) if dark else \
        ((222, 222, 217), (20, 20, 20), (115, 115, 115))
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im)
    for i, (ch, norm, inv) in enumerate(cells):
        x0 = 8 + (i % per_row) * cell_w
        y0 = 8 + (i // per_row) * cell_h
        base = y0 + (hi + 1) * scale + 4
        for j, pix in enumerate((norm, inv)):
            ox = x0 + j * (cw + 3) * scale
            for x, y in pix:
                X, Y = ox + x * scale, base - (y + 1) * scale
                d.rectangle([X, Y, X + scale - 1, Y + scale - 1], fill=ink)
        d.text((x0, y0 + cell_h - 24), "'%s'%s" % (ch, ' ' + LABEL[ch] if ch in LABEL else ''), fill=dim)
    im.save(path)


def gui():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk

    class Win(Gtk.Window):
        def __init__(self):
            super().__init__(title='Font bugs - every C47_nav glyph, normal and inverted')
            self.set_default_size(1100, 760)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            v.set_border_width(8)
            self.add(v)
            bar = Gtk.Box(spacing=8)
            v.pack_start(bar, False, False, 0)
            self.font = Gtk.ComboBoxText()
            for n in FONTS:
                self.font.append_text(n)
            self.font.set_active(1)
            self.box = Gtk.ComboBoxText()
            for n in ('tight', 'cell'):
                self.box.append_text(n)
            self.box.set_active(0)
            self.scale = Gtk.SpinButton.new_with_range(1, 12, 1)
            self.scale.set_value(4)
            self.dark = Gtk.CheckButton(label='Dark')
            save = Gtk.Button(label='Save PNG')
            for lab, w in (('Font', self.font), ('Box', self.box), ('Zoom', self.scale), (None, self.dark),
                           (None, save)):
                if lab:
                    bar.pack_start(Gtk.Label(label=lab), False, False, 0)
                bar.pack_start(w, False, False, 0)
            bar.pack_start(Gtk.Label(label='left: normal   right: inverted (XOR with its box)'), False, False, 12)
            self.area = Gtk.DrawingArea()
            self.area.connect('draw', self.on_draw)
            sw = Gtk.ScrolledWindow()
            sw.add(self.area)
            v.pack_start(sw, True, True, 0)
            for w, sig in ((self.font, 'changed'), (self.box, 'changed'), (self.scale, 'value-changed'),
                           (self.dark, 'toggled')):
                w.connect(sig, lambda *a: self.redraw())
            save.connect('clicked', self.on_save)
            self.redraw()

        def args(self):
            return FONTS[self.font.get_active_text()], self.box.get_active_text(), int(self.scale.get_value())

        def redraw(self):
            f, m, s = self.args()
            self.area.set_size_request(*size(f, m, s))
            self.area.queue_draw()

        def on_draw(self, w, cr):
            f, m, s = self.args()
            draw(cr, f, m, s, self.dark.get_active())

        def on_save(self, *a):
            d = Gtk.FileChooserDialog(title='Save PNG', parent=self, action=Gtk.FileChooserAction.SAVE)
            d.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            d.set_current_name('fontbugs.png')
            if d.run() == Gtk.ResponseType.OK:
                to_png(d.get_filename(), *self.args())
            d.destroy()

    w = Win()
    w.connect('destroy', Gtk.main_quit)
    w.show_all()
    Gtk.main()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--png', help='write a PNG instead of opening the window')
    ap.add_argument('--font', default='PTXB', choices=list(SHORT))
    ap.add_argument('--box', default='tight', choices=['tight', 'cell'])
    ap.add_argument('--scale', type=int, default=4)
    a = ap.parse_args()
    if a.png:
        to_png(a.png, FONTS[SHORT[a.font]], a.box, a.scale)
        print(a.png)
    else:
        gui()
