#!/usr/bin/env python3
"""nav_shots.py - the pictures of the NAV screens in the C47 manual (docs/), from build/NAVFULL.txt
run in the C47 simulator (python/c47sim.py): the screens of Oct 2026, text with ATEXT in GRFNT 21.

  NAV_menu.png, NAV_info.png, NAV_busy_box.png      800 x 480, grey (2 x)
  ALMF_preview.png HALMH_preview.png HORZ_axes_night.png
  ANIM_preview.png ALLSKY_preview.png                1200 x 720, black on white (3 x)

  python3 tools/generators/nav_shots.py
"""
import os, sys, tempfile
from decimal import Decimal as D
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'python'), HERE]
import c47sim, gennav

DOCS = os.path.join(ROOT, 'docs')
NAV = os.path.join(ROOT, 'build', 'NAVFULL.txt')
INIT = os.path.join(ROOT, 'build', 'NAVINIT_FULL.txt')
MENU_CASE = ('2026.0926', '14.57', '25.20', '55.12')        # the menu, INFO and the box
VIEW_CASE = ('2026.0923', '23.30', '10.00', '-75.30')       # the views
# view: its menu key; the frames are the menu, the view, the menu again
# v2.0.0 menu: 1 ALMANAC 2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO (CHART is gone: HALMV_preview stays as it was)
VIEWS = {'ALMF_preview': 72, 'HALMH_preview': 73, 'HORZ_axes_night': 74, 'ANIM_preview': 62, 'ALLSKY_preview': 63}
INFO_KEY = 64


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def run(case, keys, box=False, maxpauses=None, keyskip=False):
    """NAV with the keys; the frames as sets of (x, row), row 0 at the top. box: the SINKING box
    makes a frame of its own (its PAUSE 0 becomes PAUSE 2). keyskip: the views run on without a key
    (SKY writes the next name every second)."""
    progs = split(INIT) + split(NAV)
    if box:
        nav = progs[len(split(INIT))]
        i = nav.index('LBL 52')
        j = nav.index('PAUSE 0', i)
        nav[j] = 'PAUSE 2'
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(progs):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    for k, v in zip(('DATE', 'UTC', 'LAT', 'LON'), case):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys); c.maxpauses = maxpauses; c.keyskip = keyskip
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return [{(x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400} for f in c.frames]


def save(frame, name, scale, on, off, mode):
    im = Image.new(mode, (400, 240), off)
    for x, r in frame:
        im.putpixel((x, r), on)
    im.resize((400 * scale, 240 * scale), Image.NEAREST).save(os.path.join(DOCS, name + '.png'))
    print('docs/%s.png' % name)


def main():
    grey = dict(scale=2, on=20, off=220, mode='L')
    view = dict(scale=3, on=(0, 0, 0), off=(255, 255, 255), mode='RGB')
    save(run(MENU_CASE, [82])[0], 'NAV_menu', **grey)
    save(run(MENU_CASE, [INFO_KEY, 85, 82])[1], 'NAV_info', **grey)
    fr = run(MENU_CASE, [gennav.DOWN, 82], box=True)   # the box at the start, the menu, the box over it (DOWN), ...
    save(fr[2], 'NAV_busy_box', **grey)
    for name, key in VIEWS.items():
        if key == 74:                                  # SKY: the chart, then the first name next to its body
            save(run(VIEW_CASE, [key], maxpauses=3, keyskip=True)[2], name, **view)
        else:
            save(run(VIEW_CASE, [key, 85, 82])[1], name, **view)


if __name__ == '__main__':
    main()
