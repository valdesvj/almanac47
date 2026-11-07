#!/usr/bin/env python3
"""test_route.py - the web app's Route (web/route.js) against NAV47's own C (nav47.pg5 src/route.c, compiled here),
and its file reader.

Random legs (the Gulf and the world, across 180, east-west, north-south): course and distance, rhumb line and great
circle, the same to 1E-9; the platform files: CSV decimal, degrees and minutes, KML, GPX, GeoJSON, tide47's private.js.
  python3 tests/test_route.py [--nav47 ~/opt/nav47.pg5]     (needs node and a C compiler)"""
import json, os, random, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []

HARNESS = r"""
#include <stdio.h>
#include "route.h"
int main(void) {
  double a, b, c, d, crs, nm, crs2, nm2;
  while (scanf("%lf %lf %lf %lf", &a, &b, &c, &d) == 4) {
    leg_rl(a, b, c, d, &crs, &nm); leg_gc(a, b, c, d, &crs2, &nm2);
    printf("%.12f %.12f %.12f %.12f\n", crs, nm, crs2, nm2);
  }
  return 0;
}
"""

JS = r"""
globalThis.window = globalThis; globalThis.addEventListener = () => {}; globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.A47 = { S: { pos: [27, 50] }, store: { get: () => null, set: () => {} }, p2: x => String(x).padStart(2, '0'),
  mod: (x, m) => ((x % m) + m) % m, addView: () => {}, parsePos: null };
require(process.argv[2] + '/app_parsepos.js');
require(process.argv[2] + '/route.js');
const q = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const R = A47.ROUTE;
process.stdout.write(JSON.stringify({
  legs: q.legs.map(([a, b, c, d]) => [...R.legRL(a, b, c, d), ...R.legGC(a, b, c, d)]),
  files: q.files.map(t => R.parsePlaces(t).map(p => [p.name, +p.lat.toFixed(6), +p.lon.toFixed(6)])),
}));
"""

FILES = [
    ('name, lat, lon\nP-1, 27.1, 49.65\nP-2, -33.5, -70.25\n', [['P-1', 27.1, 49.65], ['P-2', -33.5, -70.25]]),
    ('P 1  27 06.00N 049 39.00E\nQ-2 33 30.0S 070 15.0W\n', [['P 1', 27.1, 49.65], ['Q-2', -33.5, -70.25]]),
    ('<kml><Placemark><name>K1</name><Point><coordinates>49.65,27.1,0</coordinates></Point></Placemark></kml>', [['K1', 27.1, 49.65]]),
    ('<gpx><wpt lat="27.1" lon="49.65"><name>G1</name></wpt></gpx>', [['G1', 27.1, 49.65]]),
    ('{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"J1"},"geometry":{"type":"Point","coordinates":[49.65,27.1]}}]}',
     [['J1', 27.1, 49.65]]),
    ('globalThis.T47PRIVATE = [{"name":"Ras Tanura","lat":26.6,"lon":50.2,"tz":3}];\nglobalThis.T47FLOW = {};', [['Ras Tanura', 26.6, 50.2]]),
]


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what), flush=True)
    if not ok:
        FAIL.append(what)


def main():
    nav47 = os.path.expanduser(sys.argv[sys.argv.index('--nav47') + 1] if '--nav47' in sys.argv else '~/opt/nav47.pg5')
    src = os.path.join(nav47, 'src')
    if not os.path.exists(os.path.join(src, 'route.c')):
        print('no nav47.pg5 at %s (--nav47 DIR)' % nav47); sys.exit(2)
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, 'h.c'), 'w').write(HARNESS)
    exe = os.path.join(tmp, 'route')
    subprocess.run(['cc', '-O2', '-I', src, os.path.join(tmp, 'h.c'), os.path.join(src, 'route.c'), '-lm', '-o', exe], check=True)
    rnd = random.Random(47)
    legs = [[rnd.uniform(24, 30), rnd.uniform(47, 56), rnd.uniform(24, 30), rnd.uniform(47, 56)] for _ in range(300)]
    legs += [[rnd.uniform(-70, 70), rnd.uniform(-180, 180), rnd.uniform(-70, 70), rnd.uniform(-180, 180)] for _ in range(300)]
    legs += [[27, 179.5, 27.2, -179.5], [27, 49, 27, 50], [27, 49, 28, 49], [-10, 10, -10, -10], [0, 0, 0, 0]]
    c = subprocess.run([exe], input='\n'.join('%r %r %r %r' % tuple(l) for l in legs), capture_output=True, text=True, check=True)
    want = [list(map(float, ln.split())) for ln in c.stdout.split('\n') if ln.strip()]
    # app.js's parsePos alone (the position reader the platform files use)
    app = open(os.path.join(ROOT, 'web', 'app.js')).read()
    a, b = app.index('  function parsePos(s) {'), app.index('  const zdOf')
    open(os.path.join(tmp, 'app_parsepos.js'), 'w').write('(function(){' + app[a:b] + '\nA47.parsePos = parsePos;})();\n')
    import shutil
    shutil.copy(os.path.join(ROOT, 'web', 'route.js'), tmp)
    js = os.path.join(tmp, 't.js')
    open(js, 'w').write(JS)
    r = subprocess.run(['node', js, tmp], input=json.dumps({'legs': legs, 'files': [f for f, _ in FILES]}),
                       capture_output=True, text=True, check=True)
    got = json.loads(r.stdout)
    adiff = lambda x, y: abs((x - y + 180) % 360 - 180)
    wc = max(max(adiff(w[0], g[0]), adiff(w[2], g[2])) for w, g in zip(want, got['legs']))
    wd = max(max(abs(w[1] - g[1]), abs(w[3] - g[3])) for w, g in zip(want, got['legs']))
    print('%d legs (the Gulf, the world, across 180, along a parallel and a meridian, nil)' % len(legs))
    check(len(want) == len(got['legs']) and wc < 1e-9, 'course RL and GC = NAV47 route.c within %.1g degree' % wc)
    check(wd < 1e-9, 'distance RL and GC = NAV47 route.c within %.1g nm' % wd)
    for (text, exp), g in zip(FILES, got['files']):
        check(g == exp, 'platform file %-48s %s' % (repr(text[:44]), g))
    print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
