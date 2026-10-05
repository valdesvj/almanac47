#!/usr/bin/env python3
"""release_shots.py - the NAVFULL views for the release notes, in the LCD look of docs/MOON47.png
(c47view.render_rgb: grey-green glass, dark bezel, 3 x): docs/release/C47_<view>.png, 1236 x 756.
Same runs as nav_shots.py (build/NAVFULL.txt in the C47 simulator, 23 Sep 2026 23:30 UT, 10 N 75 30 W).

  python3 tools/generators/release_shots.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'python'), HERE]
import c47view, nav_shots as ns

OUT = os.path.join(ROOT, 'docs', 'release')
NAMES = {'ALMF_preview': 'ALMANAC', 'HALMH_preview': 'SPLIT', 'HORZ_axes_night': 'SKY',
         'ANIM_preview': 'ANIM', 'ALLSKY_preview': 'ALLSKY'}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, key in ns.VIEWS.items():
        if key == 74:                                  # SKY: the chart, then the first name next to its body
            fr = ns.run(ns.VIEW_CASE, [key], maxpauses=3, keyskip=True)[2]
        else:
            fr = ns.run(ns.VIEW_CASE, [key, 85, 82])[1]
        w, h, rgb = c47view.render_rgb(fr, scale=3)
        fn = os.path.join(OUT, 'C47_%s.png' % NAMES[name])
        c47view.write_png(fn, w, h, rgb)
        print(os.path.relpath(fn, ROOT))


if __name__ == '__main__':
    main()
