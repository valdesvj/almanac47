"""t21sim.py - the NAVFULL_T21 views run in the simulator (NAV with keys, as on the calculator),
for tests/test_parity21.py: frames as sets of (x, row) with row 0 at the top."""
import os, sys, tempfile, json
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim

NAV = os.path.join(ROOT, 'build', 'atext', 'NAVFULL_T21.txt')
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
    """The C47 reference of Free42 NAVLITTLE: the C47 NAVLITTLE NAV (no menu; 21 GRFNT as
    NAVFULL_T21), the C47 routines Free42 NAVLITTLE is converted from (build_free42.little_programs:
    no cache, so the Sun sets the T flag itself), the fonts and WPLS of NAVFULL_T21 and the
    NAVLITTLE ALMANAC view (build_free42.little_almf). A list of programs (lists of lines)."""
    sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tools', 'generators')]
    import build_free42 as F, build_dm42, gennav
    nav = build_dm42.no_box(build_dm42.nav1_program(gennav.inputs()))
    nav = build_dm42.seq(nav, ['XEQ 20', 'CLLCD'], ['XEQ 20', '21', 'GRFNT', 'DROP', 'CLLCD'])
    nav = build_dm42.seq(nav, ['CLLCD', 'RCL "SSZ"'], ['20', 'GRFNT', 'DROP', 'CLLCD', 'RCL "SSZ"'])
    lp = F.little_programs()
    own = {k: v for k, v in lp.items() if k not in ('NAV', 'ALMF', 'PTXS', 'PTXT', 'WPLS', 'STXT')
           and k not in F.T21_VIEWS}                     # STXT, WPLS: the Free42 versions
    own['ALMF'] = F.little_almf()
    t21 = [p for p in _split(os.path.join(ROOT, 'build', 'atext', 'src', 'NAVFULL_T21.txt'))
           if p[0] != 'LBL "NAV"' and p[0][5:-1] not in own]
    return [nav] + t21 + list(own.values())
