#!/usr/bin/env python3
"""test_web.py - the web app's engine (web/nav.js, in node) against the Python (python/nav.py, python/moon47.py).

Random dates 1950-2100 and places: the Sun (GHA, Dec, GHA Aries, SD), all 58 stars (GHA, Dec, SHA), the events
(nautical / civil twilight, rise, set, meridian passage), the Moon phase (nav.py), Hc / Zn, the ALMANAC page's
strings (the same text), and MOON47's page (lit, age, HP, SD, the next phases).
  python3 tests/test_web.py      (needs node; runs tools/make_web_data.py first)"""
import json, os, random, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import nav, moon47           # noqa: E402

FAIL = []


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what), flush=True)
    if not ok:
        FAIL.append(what)


JS = r"""
require(process.argv[2] + '/data/navdata.js'); require(process.argv[2] + '/nav.js');
const q = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = q.map(([j, lat, lon]) => {
  const s = NAV.sun(j);
  const stars = []; for (let n = 1; n <= 58; n++) stars.push(NAV.star(j, n, s));
  const j0 = Math.trunc(j - 0.5) + 0.5;
  const ev = {}; for (const k of Object.keys(NAV.EVENTS)) ev[k] = NAV.event(j0, lat, lon, k);
  return {sun: [s.gha, s.dec, s.aries, s.sd], stars, ev, phase: NAV.phase(j), hcz: NAV.hcz(lat, lon, s.dec, s.gha),
          alm: NAV.almanac(j, lat, lon), moon: NAV.moonPage(j)};
});
process.stdout.write(JSON.stringify(out));
"""


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def main():
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'make_web_data.py')], check=True, capture_output=True)
    rnd = random.Random(47)
    cases = [(nav.jd(rnd.randint(1950, 2100), rnd.randint(1, 12), rnd.randint(1, 28), rnd.uniform(0, 24)),
              rnd.uniform(-70, 70), rnd.uniform(-180, 180)) for _ in range(150)]
    js = os.path.join(ROOT, 'web', '_t.js')
    open(js, 'w').write(JS)
    try:
        r = subprocess.run(['node', js, os.path.join(ROOT, 'web')], input=json.dumps(cases), capture_output=True,
                           text=True, check=True)
    finally:
        os.remove(js)
    out = json.loads(r.stdout)
    ws = wst = we = wp = wh = wm = 0
    same_alm, nev = 0, 0
    for (j, lat, lon), g in zip(cases, out):
        s = nav.sun(j)
        ws = max(ws, adiff(s['gha'], g['sun'][0]), abs(s['dec'] - g['sun'][1]), adiff(s['aries'], g['sun'][2]),
                 abs(s['sd'] - g['sun'][3]))
        for n in range(1, 59):
            a = nav.star(j, n, s)
            b = g['stars'][n - 1]
            wst = max(wst, adiff(a[0], b[0]), abs(a[1] - b[1]), adiff(a[2], b[2]))
        j0 = int(j - 0.5) + 0.5
        for k in nav.EVENTS:
            a, b = nav.event(j0, lat, lon, k), g['ev'][k]
            nev += 1
            if (a is None) != (b is None):
                we = 99
            elif a is not None:
                we = max(we, abs(a - b) * 3600)
        k, age = nav.phase(j)
        wp = max(wp, abs(k - g['phase'][0]), abs(age - g['phase'][1]))
        h = nav.hcz(lat, lon, s['dec'], s['gha'])
        wh = max(wh, abs(h[0] - g['hcz'][0]), adiff(h[1], g['hcz'][1]))
        head, tab, foot = nav.almanac(j, lat, lon)
        ga = g['alm']
        same_alm += (list(head) == ga[0] and [list(t[:6]) for t in tab] == [t[:6] for t in ga[1]] and foot == ga[2])
        p = moon47.page(j)
        m = g['moon']
        wm = max(wm, abs(p['lit'] - m['lit']), abs(p['age'] - m['age']), abs(p['hp'] - m['hp']), abs(p['sd'] - m['sd']),
                 max(abs(a[0] - b[0]) * 1440 for a, b in zip(p['next'], m['next'])))
    print('%d random dates 1950-2100 and places' % len(cases))
    check(ws < 1e-9, 'the Sun: GHA, Dec, GHA Aries, SD within %.1g' % ws)
    check(wst < 1e-9, 'the 58 stars: GHA, Dec, SHA within %.1g degree' % wst)
    check(we < 1e-3, '%d events (twilights, rise, set, meridian passage) within %.1g s' % (nev, we))
    check(wp < 1e-6 and wh < 1e-9, 'the Moon phase within %.1g; Hc / Zn within %.1g' % (wp, wh))
    check(same_alm == len(cases), 'the ALMANAC page: the same text %d / %d' % (same_alm, len(cases)))
    check(wm < 1e-6, 'MOON47: lit, age, HP, SD and the next phases (minutes) within %.1g' % wm)
    print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
