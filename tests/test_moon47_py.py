#!/usr/bin/env python3
"""MOON47 on the NumWorks and the HP Prime (python/numworks/moon47.py, python/hpprime/moon47.py, written by
tools/build_moon47.py) on the PC with the kandinsky / ion / hpprime stand-ins: the page runs, north then south
(OK / Enter), BACK / Esc ends, and the texts it draws are the numbers of python/moon47.py.
Previews: python3 tests/test_moon47_py.py --png DIR
  python3 tests/test_moon47_py.py"""
import builtins, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import moon47 as M47


def expected(j, south):
    p = M47.page(j, south)
    out = [M47.NAMES[p['index']], 'LIT %d%%   AGE %.1f DAYS' % (int(p['lit'] + 0.5), p['age']),
           "HP %.1f'  SD %.1f'" % (p['hp'], p['sd']), 'AS SEEN FROM THE SOUTH' if south else 'AS SEEN FROM THE NORTH']
    for t, name in p['next']:
        d, m, y, h = M47.from_julian(t + 0.5 / 1440)
        out += [name, '%02d-%02d %02d:%02d' % (d, m, int(h), int(h * 60) % 60)]
    return out


def load(path, shim):
    for k in [m for m in sys.modules if m in ('kandinsky', 'ion', 'hpprime')]:
        del sys.modules[k]
    sys.path.insert(0, shim)
    src = open(path, encoding='utf-8').read()
    assert src.rstrip().endswith('run()')
    ns = {'__name__': 'moon47_port'}
    exec(compile(src.rstrip()[:-5], path, 'exec'), ns)
    sys.path.remove(shim)
    return ns


def numworks(date, ut, png=None):
    ns = load(os.path.join(ROOT, 'python', 'numworks', 'moon47.py'), os.path.join(ROOT, 'python', 'numworks', 'pc_shim'))
    import ion, kandinsky
    shots = []
    if png:
        shots = ['SHOT:%s/NUMWORKS_moon47.png' % png, 'KEY_OK', 'SHOT:%s/NUMWORKS_moon47_south.png' % png]
    ion.script = shots or ['KEY_OK']
    ion.script.append('KEY_BACK')
    answers = list(map(str, date)) + [ut]
    builtins.input = lambda q='': answers.pop(0)
    drawn = []
    t = ns['text']
    ns['text'] = lambda s, x, y, c=ns['BK']: (drawn.append(s), t(s, x, y, c))[1]
    ns['run']()
    return drawn


def hpprime(date, time, tz, png=None):
    ns = load(os.path.join(ROOT, 'python', 'hpprime', 'moon47.py'), os.path.join(ROOT, 'python', 'hpprime', 'pc_shim'))
    import hpprime
    hpprime.clock = {'Date': date, 'Time': time}
    ns['TZ'] = tz
    hpprime.script = (['SHOT:%s/HPPRIME_moon47.png' % png, 'ENTER', 'SHOT:%s/HPPRIME_moon47_south.png' % png]
                      if png else ['ENTER'])
    del hpprime.log[:]
    ns['run']()
    return [t for t, x, y, f in hpprime.log]


def main():
    png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
    bad = 0
    for date, ut in (((2026, 10, 3), '12:00'), ((2027, 1, 22), '3:30'), ((2049, 3, 16), '21:51')):
        j = M47.julian(date[0], date[1], date[2], int(ut.split(':')[0]) + int(ut.split(':')[1]) / 60.0)
        want = expected(j, False) + expected(j, True)
        got = numworks(date, ut, png if date == (2026, 10, 3) else None)
        miss = [w for w in want if w not in got]
        bad += bool(miss)
        print('NumWorks %s %s: %s' % (date, ut, 'OK' if not miss else 'MISSING %s' % miss))
    for date, time, tz in ((2026.1003, 16.0, 4), (2027.0121, 22.30, -5), (2049.0316, 21.51, 0), (2028.0606, 1.42, 5.5)):
        y = int(date); m = int(round((date - y) * 100)); d = int(round((date - y) * 10000 - m * 100))
        h = int(time); mi = int(round((time - h) * 100))
        j = M47.julian(y, m, d, h + mi / 60.0 - tz)
        want = expected(j, False) + expected(j, True) + [
            '%02d-%02d-%04d %02d:%02d %s TZ=%s' % (d, m, y, h, mi, 'LT' if tz else 'UT', M47.tz_text(tz))]
        got = hpprime(date, time, tz, png if tz == 4 else None)
        miss = [w for w in want if w not in got]
        bad += bool(miss)
        print('HP Prime %s %05.2f TZ %+g: %s' % (date, time, tz, 'OK' if not miss else 'MISSING %s' % miss))
    print('%d failed' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
