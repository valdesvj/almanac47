"""run.py - run almview.py / skyview.py on a PC with the kandinsky / ion stand-ins.

  python3 python/numworks/pc_shim/run.py alm "2026 9 26 14:57 25_20 55_12" docs/NUMWORKS_alm.png
  python3 python/numworks/pc_shim/run.py sky "2026 9 23 03:00 30 0" out.png [KEY_RIGHT ...]

The answers are year, month, day, UT, lat, lon ('_' = space, so 25_20 is 25 deg 20').
Keys after the PNG name are pressed before the picture is taken.
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
import builtins
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [here, os.path.dirname(here), os.path.dirname(os.path.dirname(here))]
import ion          # noqa: E402  (the stand-ins, found first on the path)

view, answers, png = sys.argv[1], sys.argv[2].split(), sys.argv[3]
ion.script = sys.argv[4:] + ['SHOT:' + png, 'KEY_BACK']
answers = [a.replace('_', ' ') for a in answers]


def _input(prompt=''):
    a = answers.pop(0)
    print(prompt + a)
    return a


builtins.input = _input
__import__('almview' if view == 'alm' else 'skyview')
print('saved', png)
