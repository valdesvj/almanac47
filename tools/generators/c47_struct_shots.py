#!/usr/bin/env python3
"""c47_struct_shots.py - the pictures of the C47 manual for v2.2.0 (the STRUCT build, build/dev/struct_src/NAVFULL.txt,
which is ALMA47): docs/c47/, the same names, sizes and runs as nav_shots.py (docs/ keeps the v2.1.0 pictures of the
Free42 manual). --next: from the next version (v2.3.0: tools/build_struct_src.build_next(), the new header), and
ALMF_LT.png, ALMANAC in local time (TZ 3, TZLT 1).

  python3 tools/generators/c47_struct_shots.py [--next]
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'python'), HERE]
import nav_shots as ns

ns.NAV = os.path.join(ROOT, 'build', 'dev', 'struct_src', 'NAVFULL.txt')
ns.DOCS = os.path.join(ROOT, 'docs', 'c47')
_split = ns.split


def split(path):
    """The box at the start gets a frame of its own: its PAUSE 0 (NAV's LBL 05) becomes PAUSE 2 (nav_shots looks for
    v2.1.0's LBL 52: given here as a marker)."""
    progs = _split(path)
    if path == ns.NAV:
        nav = progs[0]
        i = nav.index('LBL 05')
        nav[nav.index('PAUSE 0', i)] = 'PAUSE 2'
    return progs


def main():
    os.makedirs(ns.DOCS, exist_ok=True)
    nxt = '--next' in sys.argv
    if nxt:
        import tempfile
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import build_struct_src as B
        ns.NAV = os.path.join(tempfile.mkdtemp(), 'NAVFULL.txt')
        open(ns.NAV, 'w', encoding='utf-8').write('\n'.join(B.build_next()) + '\n')
    grey = dict(scale=2, on=20, off=220, mode='L')
    view = dict(scale=3, on=(0, 0, 0), off=(255, 255, 255), mode='RGB')
    ns.save(ns.run(ns.MENU_CASE, [82])[0], 'NAV_menu', **grey)
    ns.save(ns.run(ns.MENU_CASE, [ns.INFO_KEY, 85, 82])[1], 'NAV_info', **grey)
    ns.split = split
    ns.save(ns.run(ns.MENU_CASE, [82])[0], 'NAV_busy_box', **grey)
    ns.split = _split
    for name, key in ns.VIEWS.items():
        if key == 74:
            ns.save(ns.run(ns.VIEW_CASE, [key], maxpauses=3, keyskip=True)[2], name, **view)
        else:
            ns.save(ns.run(ns.VIEW_CASE, [key, 85, 82])[1], name, **view)
    if nxt:                                            # ALMANAC in LT: the menu case at UTC+3
        ns.save(ns.run(ns.VIEW_CASE, [ns.VIEWS['ALMF_preview'], 85, 82], regs={'TZ': 3, 'TZLT': 1})[1], 'ALMF_LT', **view)


if __name__ == '__main__':
    main()
