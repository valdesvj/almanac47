#!/usr/bin/env python3
"""build_live.py - DEV: NAVFULL v2 that shows the drawing as it goes, the way Free42 on the DM42 does.

  build/dev/live/NAVFULL_LIVE.txt (.p47)            C47 / R47: PAUSE 0 (the screen to the LCD, no wait) after every
                                                    text or symbol a view draws; the SINKING....ABOUT box only at the
                                                    start, before the menu; SKY: the next body's name every 2 s
  build/dev/live/src/NAVFULL_LIVE.txt                the same with the routine names
  build/dev/live/free42/NAVFULL_LIVE.txt (.raw)     Free42: the box only at the start (Free42 shows the drawing itself);
                                                    SKY every 2 s
  build/dev/live/free42/src/NAVFULL_LIVE.txt

The C47 sends its screen to the LCD only at a PAUSE, a key or the end of the program (programming/input.c:207,
lcd_refresh in fnPause), so a view appears only when it is finished. Not one PAUSE 0 per PIXEL: one per text and per
body symbol (star, planet, Sun, Moon). Without the box, the arrows on the menu and on a view compute with no sign on
the screen. The release files (build/, build/free42/) are not touched; the matrices: the release NAVINIT_FULL / _FAST.

  python3 tools/build_live.py
"""
import contextlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(ROOT, 'python')]
import build_navopt as N                                                     # noqa: E402
import build_v2 as V                                                         # noqa: E402
import navhopt                                                               # noqa: E402

B = N.B
OUT = os.path.join(ROOT, 'build', 'dev', 'live')
VIEWS = ('ALMF', 'HALMH', 'HORZ', 'HANIM', 'ALLSKY')
# the routines that draw a text, a number or a symbol (programs/atext/t21, glyphs47): a PAUSE 0 after each call
DRAW = ('PTXS', 'PDMS', 'PHMS', 'PDTS', 'PSYS', 'PSYB', 'PTNT', 'PTTY', 'PINS', 'PF1S', 'PZNS', 'PHLS')
SKY = '20'          # SKY: the next body's name every 2 s (the release: 50, 5 s)


def programs(L):
    """[(name, first line, END line)] of a named listing."""
    out, start, name = [], None, None
    for i, l in enumerate(L):
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m and start is None:
            start, name = i, m.group(1)
        if l == 'END' and start is not None:
            out.append((name, start, i))
            start = None
    return out


def box_at_start(L):
    """NAV: the SINKING....ABOUT box (XEQ 48) only the first time, before the menu."""
    out, prog, seen = [], None, 0
    for l in L:
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m and prog in (None, '#END'):
            prog = m.group(1)
        if prog == 'NAV' and l == 'XEQ 48':
            seen += 1
            if seen > 1:
                continue
        out.append(l)
        if l == 'END':
            prog = '#END'
    assert seen > 1, 'build_live: no XEQ 48 in NAV'
    return out


def sky_time(L, f42=False):
    """SKY (HORZ): the time per body name, SKY tenths of a second. C47: PAUSE 50 / KEY?; Free42: XEQ "TK" / 50 / +."""
    out, n, prog = list(L), 0, None
    for i, l in enumerate(L):
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m and prog in (None, '#END'):
            prog = m.group(1)
        if prog == 'HORZ':
            if not f42 and l == 'PAUSE 50' and L[i + 1].startswith('KEY? '):
                out[i] = 'PAUSE ' + SKY; n += 1
            if f42 and l == 'XEQ "TK"' and L[i + 1] == '50' and L[i + 2] == '+':
                out[i + 1] = SKY; n += 1
        if l == 'END':
            prog = '#END'
    assert n == 1, 'build_live: SKY time found %d times' % n
    return out


def live(L):
    """C47: PAUSE 0 after every drawing call in the views."""
    out, n = list(L), 0
    for name, a, b in reversed(programs(L)):
        if name in VIEWS:
            for i in range(b - 1, a, -1):
                if L[i] in ['XEQ "%s"' % d for d in DRAW]:
                    out.insert(i + 1, 'PAUSE 0')
                    n += 1
    assert n > 50, 'build_live: few drawing calls (%d)' % n
    return out


def c47():
    full, short = N.c47(True, menu=N.SPLIT2,
                        post=lambda L: live(sky_time(box_at_start(navhopt.nav_regs(navhopt.inputs(navhopt.loops(L)))))))
    B.write(os.path.join(OUT, 'NAVFULL_LIVE.txt'), short)
    B.write(os.path.join(OUT, 'src', 'NAVFULL_LIVE.txt'), full)
    return full


def free42():
    """As build_v2.free42 (NAVFULL), with the box only at the start."""
    import build_free42 as F
    F.GLYPHS['PTXS'] = V.f42_glyphs()
    menu = dict(N.SPLIT2, **N.C47_MENU)
    menu['HINT'] = V.F42_HINT
    short, named = N.free42(True, menu=menu,
                            post=lambda L: sky_time(box_at_start(navhopt.f42_regs(navhopt.f42_inputs(navhopt.loops(L)))[0]), True))
    B.write(os.path.join(OUT, 'free42', 'NAVFULL_LIVE.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'src', 'NAVFULL_LIVE.txt'), named)
    return named


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        c47()
        free42()
    for f in ('NAVFULL_LIVE.txt', os.path.join('free42', 'NAVFULL_LIVE.txt')):
        p = os.path.join(OUT, f)
        n = N.raw(p) if f.startswith('free42') else N.p47(p)
        print('%-40s %s' % (os.path.relpath(p, ROOT), n or '(no converter)'))


if __name__ == '__main__':
    main()
