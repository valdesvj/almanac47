#!/usr/bin/env python3
"""release_shots.py - the NAVFULL views for the release notes, in the LCD look of docs/MOON47.png
(c47view.render_rgb: grey-green glass, dark bezel, 3 x): docs/release/C47_<view>.png, 1236 x 756.
Same runs as nav_shots.py (build/NAVFULL.txt in the C47 simulator, DR 10 N 75 30 W), at the clock's UT
(or --date/--ut); also docs/release/C47_MOON47.png (python/moon47.py) at the same moment.

  python3 tools/generators/release_shots.py [--date YYYY-MM-DD --ut HH:MM]
"""
import argparse, datetime, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'python'), HERE]
import c47view, nav_shots as ns

OUT = os.path.join(ROOT, 'docs', 'release')
NAMES = {'ALMF_preview': 'ALMANAC', 'HALMH_preview': 'SPLIT', 'HORZ_axes_night': 'SKY',
         'ANIM_preview': 'ANIM', 'ALLSKY_preview': 'ALLSKY'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='YYYY-MM-DD UT (default: the clock)')
    ap.add_argument('--ut', help='HH:MM UT (default: the clock)')
    a = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    date = a.date or now.strftime('%Y-%m-%d')
    ut = a.ut or now.strftime('%H:%M')
    y, m, d = date.split('-'); hh, mm = ut.split(':')
    case = ('%s.%s%s' % (y, m, d), '%s.%s' % (hh, mm)) + ns.VIEW_CASE[2:]
    print('%s %s UT' % (date, ut))
    os.makedirs(OUT, exist_ok=True)
    for name, key in ns.VIEWS.items():
        if key == 74:                                  # SKY: the chart, then the first name next to its body
            fr = ns.run(case, [key], maxpauses=3, keyskip=True)[2]
        else:
            fr = ns.run(case, [key, 85, 82])[1]
        w, h, rgb = c47view.render_rgb(fr, scale=3)
        fn = os.path.join(OUT, 'C47_%s.png' % NAMES[name])
        c47view.write_png(fn, w, h, rgb)
        print(os.path.relpath(fn, ROOT))
    subprocess.run([sys.executable, os.path.join(ROOT, 'python', 'moon47.py'), '--date', date, '--ut', ut,
                    '--png', os.path.join(OUT, 'C47_MOON47.png')], check=True)


if __name__ == '__main__':
    main()
