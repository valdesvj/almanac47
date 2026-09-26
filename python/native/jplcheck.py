"""jplcheck.py - online check of the calculations against JPL Horizons (PC only).

Asks the JPL Horizons service (https://ssd.jpl.nasa.gov/api/horizons.api, free, no
account) for the apparent geocentric RA and Dec of the Sun, Moon, Venus, Mars,
Jupiter and Saturn (JPL DE440/441), and for the Greenwich apparent sidereal time
(= GHA Aries). GHA = GHA Aries - RA. The same values are calculated with
c47astro.py (the methods of the C47 programs) and the differences are listed in
arcminutes.

Notes
- Needs an internet connection. The program itself works offline; this check is
  optional and only in the PC version.
- JPL reads the time as UTC; the C47 programs use UT1. The difference DUT1 (under
  0.9 s) moves every GHA by up to 0.23' but does not change Dec.
- Stars are not in the JPL planetary ephemeris and are not checked.
"""
import json, math, urllib.parse, urllib.request

import c47astro as A

URL = 'https://ssd.jpl.nasa.gov/api/horizons.api'
BODIES = [('SUN', '10', 0), ('MOON', '301', -1), ('VENUS', '299', 1), ('MARS', '499', 2),
          ('JUPITER', '599', 3), ('SATURN', '699', 4)]
AU_KM = 149597870.7


def _query(params, timeout=20):
    q = {'format': 'json', 'MAKE_EPHEM': 'YES', 'EPHEM_TYPE': 'OBSERVER', 'OBJ_DATA': 'NO',
         'CSV_FORMAT': 'YES', 'EXTRA_PREC': 'YES', 'TIME_TYPE': 'UT'}
    q.update(params)
    url = URL + '?' + urllib.parse.urlencode({k: v for k, v in q.items()}, safe="'@,")
    req = urllib.request.Request(url, headers={'User-Agent': 'C47NavPC/1.1'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode('utf-8'))
    if 'result' not in data:
        raise RuntimeError(data.get('error', 'no result from JPL'))
    return data['result']


def _table(text):
    """Header names and the first data row between $$SOE and $$EOE (CSV output)."""
    lines = text.splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.strip().startswith('$$SOE'))
    except StopIteration:
        raise RuntimeError('unexpected answer from JPL:\n' + text[-400:])
    head = None
    for l in reversed(lines[:i]):
        if 'Date' in l and ',' in l:
            head = [h.strip() for h in l.split(',')]
            break
    row = [c.strip() for c in lines[i + 1].split(',')]
    if head is None:
        raise RuntimeError('no column header in the JPL answer')
    return head, row


def _col(head, row, *keys):
    for k, h in enumerate(head):
        if all(key in h for key in keys):
            return row[k]
    raise RuntimeError('column %s not found in %s' % (keys, head))


def _hms(s):
    p = [float(x) for x in s.split()]
    while len(p) < 3:
        p.append(0.0)
    return p[0] + p[1] / 60 + p[2] / 3600


def jpl_values(j):
    """{'ARIES': gha, 'SUN': (gha, dec), ..., 'MOON': (gha, dec, hp)} from JPL at JD j (UTC)."""
    tl = "'%.9f'" % j
    head, row = _table(_query({'COMMAND': "'10'", 'CENTER': "'coord@399'", 'COORD_TYPE': 'GEODETIC',
                                'SITE_COORD': "'0,0,0'", 'TLIST': tl, 'QUANTITIES': "'7'",
                                'ANG_FORMAT': 'HMS'}))
    gast = _hms(_col(head, row, 'Sid')) * 15.0
    out = {'ARIES': gast % 360.0}
    for name, code, _ in BODIES:
        head, row = _table(_query({'COMMAND': "'%s'" % code, 'CENTER': "'500@399'", 'TLIST': tl,
                                    'QUANTITIES': "'2,20'", 'ANG_FORMAT': 'DEG'}))
        ra = float(_col(head, row, 'R.A.'))
        dec = float(_col(head, row, 'DEC'))
        gha = (gast - ra) % 360.0
        if name == 'MOON':
            dist = float(_col(head, row, 'delta')) * AU_KM
            out[name] = (gha, dec, math.degrees(math.asin(6378.14 / dist)) * 60.0)
        else:
            out[name] = (gha, dec)
    return out


def our_values(j):
    s = A.Sun(j)
    out = {'ARIES': s.aries, 'SUN': (s.gha, s.dec)}
    m = A.moon(s)
    out['MOON'] = (m[0], m[1], m[2])
    for name, _, p in BODIES[2:]:
        g = A.planet(s, p)
        out[name] = (g[0], g[1])
    return out


def _d(a, b):
    return ((a - b + 180.0) % 360.0 - 180.0) * 60.0


def compare(ours, jpl):
    """Rows (name, dGHA', dDec' or None, dHP' or None)."""
    rows = [('ARIES', _d(ours['ARIES'], jpl['ARIES']), None, None)]
    for name, _, _ in BODIES:
        o, r = ours[name], jpl[name]
        rows.append((name, _d(o[0], r[0]), (o[1] - r[1]) * 60.0,
                     (o[2] - r[2]) if name == 'MOON' else None))
    return rows


def report(j, jpl=None):
    """Text report of the check at JD j. jpl: values from jpl_values(j) (fetched if None)."""
    jpl = jpl or jpl_values(j)
    rows = compare(our_values(j), jpl)
    L = ['Check against JPL Horizons (DE440), JD %.5f' % j,
         'Differences C47 method - JPL, in arcminutes',
         '',
         'BODY        GHA      DEC      HP']
    for name, dg, dd, dh in rows:
        L.append('%-8s %7.3f  %7s  %6s' % (name, dg, '' if dd is None else '%7.3f' % dd,
                                           '' if dh is None else '%6.3f' % dh))
    worst = max(abs(dd) for _, _, dd, _ in rows if dd is not None)
    L += ['', 'Largest Dec difference %.3f\'' % worst,
          'GHA includes DUT1 (JPL uses UTC, the C47 UT1): up to 0.23\'.',
          'Stars are not checked (not in the JPL planetary ephemeris).',
          'The almanac shows 0.1\'.']
    return '\n'.join(L)
