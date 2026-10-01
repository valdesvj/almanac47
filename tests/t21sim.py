"""t21sim.py - the NAVFULL views run in the simulator (NAV with keys, as on the calculator),
for tests/test_parity21.py: frames as sets of (x, row) with row 0 at the top."""
import os, sys, tempfile, json
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim

NAV = os.path.join(ROOT, 'build', 'NAVFULL.txt')
INIT = os.path.join(ROOT, 'build', 'NAVINIT_FULL.txt')      # the full series, as the native default
KEYS = {'ALMANAC': 72, 'CHART': 73, 'SKY': 62, 'SPLIT': 63, 'ANIM': 64, 'ALLSKY': 52}


def _split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def c47in(y, m, d, h, lat, lon):
    """The NAV inputs: YYYY.MMDD, HH.MMSS, DD.MMmm, DDD.MMmm (rounded to the second / 0.01')."""
    def dms(v):
        a = abs(v); dd = int(a); mm = round((a - dd) * 60, 2)
        if mm >= 60: dd, mm = dd + 1, 0
        s = '%d.%05.2f' % (dd, mm)
        s = s.replace('.', '', 1).replace('.', '') if False else '%d.%s' % (dd, ('%05.2f' % mm).replace('.', ''))
        return ('-' if v < 0 else '') + s
    hh = int(h); mi = int(round((h - hh) * 60))
    if mi == 60: hh, mi = hh + 1, 0
    return '%04d.%02d%02d' % (y, m, d), '%d.%02d' % (hh, mi), dms(lat), dms(lon)


def frames(view, case, keyskip=False, maxpauses=None):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(_split(INIT) + _split(NAV)):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    for k, v in zip(('DATE', 'UTC', 'LAT', 'LON'), c47in(*case)):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []
    c.keys = [KEYS[view]] if keyskip else [KEYS[view], 85, 82]
    c.keyskip = keyskip; c.maxpauses = maxpauses
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    out = [{(x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400} for f in c.frames]
    return out[1:] if keyskip else out[1:-1]      # without the menu (and the menu after +)


def little_programs():
    """The C47 reference of Free42 NAVLITTLE: the C47 NAVLITTLE (build/dm42/NAVLITTLE.txt: NAV with
    no menu, GRFNT 21, the T21 ALMANAC view with the Sun, the stars and the Moon line). A list of
    programs (lists of lines)."""
    return _split(os.path.join(ROOT, 'build', 'dm42', 'NAVLITTLE.txt'))
