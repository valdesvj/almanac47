#!/usr/bin/env python3
"""make_web_data.py - the data files of the web app (web/): plain scripts, so web/index.html works opened as a file.

  web/data/navdata.js  python/navdata.py: VSOP87D Earth (truncated), the nutation, the 57 stars + Polaris, their
                       names and their order by brightness (globalThis.NAVDATA) - the same numbers as the C47 programs
  web/data/astro.js    python/native/c47data.py: Venus, Mars, Jupiter, Saturn and the Earth (VSOP87D truncated) and
                       the Moon (Meeus 47 + the DE421 terms) (globalThis.ASTRODATA)
  web/data/pysrc.js    the PC Python of the calculator screens (python/native/c47*.py, python/moon47.py), as text
                       (globalThis.A47PY): the Calculator style runs it unchanged in Pyodide
  web/data/tbl.js      build/TBL_5.txt, the almanac tables c47pc.py uses by default (globalThis.A47TBL)
  web/data/zones.js    Zones 47 (github.com/valdesvj/zones47): the stops and cities (python/zones.py, IANA tzdata)
                       and the dot map (python/worldmap.py) (globalThis.ZONEDATA); from a zones47 checkout, by
                       default ~/opt/zones47 (--zones DIR); without one, the committed file is kept.
  python3 tools/make_web_data.py [--zones ~/opt/zones47]"""
import importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
OUT = os.path.join(ROOT, 'web', 'data')
PYSRC = ['c47pc.py', 'c47tables.py', 'c47astro.py', 'c47screen.py', 'c47screen21.py', 'c47font.py', 'c47fonts2.py', 'c47fonts21.py', 'c47data.py']


def write(name, var, obj, note):
    path = os.path.join(OUT, name)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('// %s - written by tools/make_web_data.py; do not edit\n' % note)
        fh.write('globalThis.%s = %s;\n' % (var, json.dumps(obj, ensure_ascii=False, separators=(',', ':'))))
    print('%-22s %7d bytes' % (os.path.relpath(path, ROOT), os.path.getsize(path)))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    os.makedirs(OUT, exist_ok=True)
    import navdata as N
    write('navdata.js', 'NAVDATA', dict(VL=N.VL, VB=N.VB, VR=N.VR, NU=N.NU, ST=N.ST, SN=N.SN, BR=list(N.BR)),
          'the coefficients of python/navdata.py (VSOP87D, IAU1980 nutation, Hipparcos stars)')
    sys.path.insert(0, os.path.join(ROOT, 'python', 'native'))
    import c47data as C
    names = ['EEL', 'EEB', 'EER', 'VNL', 'VNB', 'VNR', 'MAL', 'MAB', 'MAR', 'JUL', 'JUB', 'JUR', 'SAL', 'SAB', 'SAR',
             'ML', 'MB', 'MCL', 'MCB']
    write('astro.js', 'ASTRODATA', {n: [list(r) for r in getattr(C, n)] for n in names},
          'the planets and the Moon of python/native/c47data.py (VSOP87D truncated, Meeus 47 + DE421 terms)')
    src = {f: open(os.path.join(ROOT, 'python', 'native', f), encoding='utf-8').read() for f in PYSRC}
    src['moon47.py'] = open(os.path.join(ROOT, 'python', 'moon47.py'), encoding='utf-8').read()
    write('pysrc.js', 'A47PY', src, 'the PC Python of the screens (python/native, python/moon47.py), run by Pyodide '
          'in the Calculator style')
    tbl = os.path.join(ROOT, 'build', 'TBL_5.txt')
    write('tbl.js', 'A47TBL', {'name': 'TBL_5.txt', 'text': open(tbl, encoding='utf-8').read()},
          'build/TBL_5.txt: the almanac tables (5 years) of the Calculator style, as c47pc.py finds them')
    zdir = os.path.expanduser(sys.argv[sys.argv.index('--zones') + 1] if '--zones' in sys.argv else '~/opt/zones47')
    zp, mp = os.path.join(zdir, 'python', 'zones.py'), os.path.join(zdir, 'python', 'worldmap.py')
    if os.path.exists(zp) and os.path.exists(mp):
        Z, M = load(zp, 'zones47_zones'), load(mp, 'zones47_worldmap')
        write('zones.js', 'ZONEDATA', dict(
            tzdata=Z.TZDATA, zones=[[off, col, [list(c[:4]) + [c[4]] for c in cities]] for off, col, cities in Z.ZONES],
            ncol=M.NCOL, nrow=M.NROW, cols=['%x' % c for c in M.COLS]),
              'Zones 47 (github.com/valdesvj/zones47): IANA tzdata %s, the dot map (GLOBE land mask)' % Z.TZDATA)
    else:
        print('no zones47 checkout at %s: web/data/zones.js kept as it is' % zdir)


if __name__ == '__main__':
    main()
