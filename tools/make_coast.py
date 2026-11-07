#!/usr/bin/env python3
"""make_coast.py - the coastline of the web app's Route chart (web/data/coast.js), from GSHHG through GMT.

The same shoreline as GMT's coast (pscoast) draws: GSHHG 2.3.7 (Wessel and Smith, LGPL-3.0, see web/README.md).
  gulf   the full resolution (-Df) of the Arabian Gulf, 47.5-53 E, 24.5-29.6 N: GMT dumps it bin by bin; the pieces
         are joined into closed land polygons (the mainland pieces closed along the edge of the area, on the land side)
  region the intermediate resolution (-Di, from 100 km2) of 30-75 E, 5-40 N (the Middle East, the Arabian Sea), closed
         the same way, filled outside the Gulf
  world  the low resolution (-Dl, islands from 1000 km2) of the whole world, as lines, for the routes elsewhere
Coordinates: integers of 1E-5 degree (gulf) and 1E-3 degree (world), each polygon x0 y0 then the steps.
Needs GMT and the full GSHHG (Arch: gmt and gshhg-gmt; Debian / Ubuntu: gmt gmt-gshhg-full).
  python3 tools/make_coast.py"""
import json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GULF = (47.5, 53.0, 24.5, 29.6)
SEA = [(50.5, 27.5), (51.0, 28.5), (49.5, 28.0)]   # points known to be sea: the mainland pieces close on the other side
REGION = (30.0, 75.0, 5.0, 40.0)                  # the Middle East and the Arabian Sea, intermediate resolution, filled
SEA_REGION = [(65.0, 15.0), (50.5, 27.5), (38.0, 20.0), (60.0, 24.5), (32.0, 33.8), (47.0, 12.5)]


def dump(region, res, area):
    out = subprocess.run(['gmt', 'coast', '-R' + region, '-D' + res, '-W', '-M', '-A%s/1/1' % area],
                         capture_output=True, text=True, check=True).stdout
    segs, cur = [], None
    for ln in out.splitlines():
        if ln.startswith('>'):
            cur = []; segs.append(cur)
        elif ln.strip():
            x, y = ln.split()[:2]
            cur.append((float(x), float(y)))
    return [s for s in segs if len(s) > 1]


def key(p):
    return round(p[0], 5), round(p[1], 5)


def stitch(segs):
    """Join the pieces end to start into chains (closed rings or edge-to-edge lines)."""
    chains = [list(s) for s in segs]
    starts = {}
    for i, c in enumerate(chains):
        starts.setdefault(key(c[0]), []).append(i)
    alive = set(range(len(chains)))
    for i in range(len(chains)):
        if i not in alive:
            continue
        c = chains[i]
        while key(c[0]) != key(c[-1]):
            nxt = [j for j in starts.get(key(c[-1]), []) if j in alive and j != i]
            if not nxt:
                break
            j = nxt[0]
            c.extend(chains[j][1:]); alive.discard(j)
    return [chains[i] for i in sorted(alive)]


def inside(pt, poly):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def close(chain, box, sea=None):
    """Close an edge-to-edge chain along the edge of the box, round the corners, on the side of the land."""
    w, e, s, n = box
    corners = [(w, s), (e, s), (e, n), (w, n)]                 # anticlockwise

    def pos(p):                                                 # the place along the edge, anticlockwise from (w, s)
        x, y = p
        if abs(y - s) < 1e-6: return x - w
        if abs(x - e) < 1e-6: return (e - w) + (y - s)
        if abs(y - n) < 1e-6: return (e - w) + (n - s) + (e - x)
        return 2 * (e - w) + (n - s) + (n - y)
    per = 2 * ((e - w) + (n - s))
    cpos = [pos(c) for c in corners]
    a, b = pos(chain[-1]), pos(chain[0])
    best = None
    for way in (1, -1):                                         # from the end back to the start, both ways
        ring = list(chain)
        span = (b - a) % per if way > 0 else (a - b) % per
        for c, cp in sorted(zip(corners, cpos), key=lambda t: ((t[1] - a) % per) if way > 0 else ((a - t[1]) % per)):
            d = (cp - a) % per if way > 0 else (a - cp) % per
            if 0 < d < span:
                ring.append(c)
        if not any(inside(p, ring) for p in (sea or SEA)):
            best = ring
            break
    return best or list(chain)


def enc(poly, q):
    out, px, py = [], 0, 0
    for k, (x, y) in enumerate(poly):
        ix, iy = round(x * q), round(y * q)
        if k and ix == px and iy == py:
            continue
        out += [ix - px, iy - py] if k else [ix, iy]
        px, py = ix, iy
    return out


def main():
    w, e, s, n = GULF
    gulf = []
    for c in stitch(dump('%g/%g/%g/%g' % GULF, 'f', 0)):
        if key(c[0]) != key(c[-1]):
            c = close(c, GULF)
        gulf.append(enc(c, 1e5))
    region = []
    for c in stitch(dump('%g/%g/%g/%g' % REGION, 'i', 100)):
        if key(c[0]) != key(c[-1]):
            if len(c) < 10:
                continue
            c = close(c, REGION, SEA_REGION)
        region.append(enc(c, 1e4))
    world = [enc(c, 1e3) for c in stitch(dump('d', 'l', 1000))]
    ver = subprocess.run(['gmt', '--version'], capture_output=True, text=True).stdout.strip()
    path = os.path.join(ROOT, 'web', 'data', 'coast.js')
    with open(path, 'w') as fh:
        fh.write('// The coastline of the Route chart - GSHHG 2.3.7 (Wessel and Smith, LGPL-3.0) through GMT %s; '
                 'written by tools/make_coast.py; do not edit\n' % ver)
        fh.write('globalThis.COAST = %s;\n' % json.dumps(
            {'src': 'GSHHG 2.3.7 (GMT %s)' % ver, 'gulf': {'box': GULF, 'q': 1e5, 'polys': gulf},
             'region': {'box': REGION, 'q': 1e4, 'polys': region}, 'world': {'q': 1e3, 'lines': world}}, separators=(',', ':')))
    print('%s %d bytes: gulf %d polygons %d points, world %d lines %d points' % (
        os.path.relpath(path, ROOT), os.path.getsize(path), len(gulf), sum(len(p) for p in gulf) // 2,
        len(world), sum(len(p) for p in world) // 2))


if __name__ == '__main__':
    main()
