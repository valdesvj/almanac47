#!/usr/bin/env python3
"""test_web_calc.py - the web app's Calculator style against the PC app, pixel for pixel.

Opens web/index.html in Chromium (Playwright), picks the Calculator style, and for a few dates and places compares
the canvas of ALMANAC CHART SKY SPLIT ANIM ALLSKY MOON with python/native/c47pc.py --png (scale 3, LCD, the frame).
Needs a local Pyodide in web/pyodide/ (git-ignored; see web/README.md):
  npm pack pyodide@0.26.4 && tar xzf pyodide-0.26.4.tgz && mv package web/pyodide
  python3 tests/test_web_calc.py      (needs node and playwright)"""
import base64, io, json, os, socket, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['ALMANAC', 'CHART', 'SKY', 'SPLIT', 'ANIM', 'ALLSKY', 'MOON']
CASES = [('2026-11-07', '16:00:00', '26 30.0N 050 12.0E', 26.5, 50.2, None),
         ('2027-03-20', '03:15:30', '33 52.0S 151 12.0E', -(33 + 52 / 60), 151.2, None),
         ('2028-07-04', '23:40:00', '40 42.0N 074 00.0W', 40.7, -74.0, None),
         # UT / LT (the button, key L): LT = UT - ZD; ZD from the longitude (+5 at 74 W) or entered (-5.5)
         ('2028-07-04', '23:40:00', '40 42.0N 074 00.0W', 40.7, -74.0, ''),
         ('2027-03-20', '03:15:30', '19 04.0N 072 52.0E', 19 + 4 / 60, 72 + 52 / 60, '-5.5')]

JS = r"""
const { chromium } = require('playwright');
const [url, cases, views] = [process.argv[2], JSON.parse(process.argv[3]), JSON.parse(process.argv[4])];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1300, height: 1000 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(url); await p.evaluate(() => { localStorage.clear(); localStorage.setItem('a47.pyok', 'true'); });
  await p.reload();
  await p.selectOption('#style', 'calc'); await p.waitForSelector('#lcd', { timeout: 120000 });
  const out = [];
  for (const [d, t, pos, zd] of cases) {
    await p.fill('#pos', pos); await p.dispatchEvent('#pos', 'change');
    await p.fill('#zd', zd === null ? '' : zd); await p.dispatchEvent('#zd', 'change');
    const lt = await p.evaluate(() => A47.ltMode());
    if (lt !== (zd !== null)) await p.click('#tmode');              // LT when the case has a ZD ('' = from the longitude)
    await p.fill('#date', d); await p.fill('#time', t); await p.dispatchEvent('#time', 'change');
    const r = {};
    for (const v of views) {
      await p.click(`button[data-c="${v}"]`); await p.waitForSelector('#lcd');
      if (await p.$('#cplay.on')) await p.click('#cplay');        // stop on the first frame
      r[v] = await p.evaluate(() => document.getElementById('lcd').toDataURL('image/png'));
    }
    out.push(r);
  }
  process.stdout.write(JSON.stringify({ out, errs })); await b.close();
})();
"""


def main():
    from PIL import Image, ImageChops
    if not os.path.exists(os.path.join(ROOT, 'web', 'pyodide', 'pyodide.js')):
        print('no web/pyodide/: see the docstring'); sys.exit(2)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'make_web_data.py')], check=True, capture_output=True)
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '-b', '127.0.0.1'], cwd=os.path.join(ROOT, 'web'),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp()
    js = os.path.join(tmp, 'calc.js')
    open(js, 'w').write(JS)
    try:
        env = dict(os.environ, NODE_PATH=subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip())
        r = subprocess.run(['node', js, 'http://127.0.0.1:%d/index.html' % port, json.dumps([c[:3] + c[5:] for c in CASES]),
                            json.dumps(VIEWS)], capture_output=True, text=True, env=env, timeout=600)
    finally:
        srv.terminate()
    if r.returncode:
        print(r.stderr); sys.exit(1)
    res = json.loads(r.stdout)
    bad = list(res['errs'])
    for (d, t, _, lat, lon, zd), got in zip(CASES, res['out']):
        lt = [] if zd is None else ['--lt', '--tz', repr(-float(zd) if zd else float(round(lon / 15)))]
        for v in VIEWS:
            png = os.path.join(tmp, v + '.png')
            subprocess.run([sys.executable, os.path.join(ROOT, 'python', 'native', 'c47pc.py'), '--view', v, '--date', d,
                            '--ut', t, '--lat', repr(lat), '--lon', repr(lon), '--png', png] + lt, check=True, capture_output=True)
            a = Image.open(io.BytesIO(base64.b64decode(got[v].split(',')[1]))).convert('RGB')
            b = Image.open(png).convert('RGB')
            same = a.size == b.size and ImageChops.difference(a, b).getbbox() is None
            print('  %s  %s %s %-8s %s%s' % ('ok  ' if same else 'FAIL', d, t, v, 'identical' if same else 'differs',
                                            '' if zd is None else ' (LT)'))
            if not same:
                bad.append('%s %s %s' % (d, t, v))
    print('ALL OK' if not bad else '%d FAILED: %s' % (len(bad), bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
