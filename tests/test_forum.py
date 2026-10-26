#!/usr/bin/env python3
"""tests/test_forum.py - the files for the forum and the C47's PROGRAMS folder (tools/build_p47.py's list): their
steps (the '@' lines, the comments after ';' and the indentation taken away) are exactly those of the plain listing,
so rejig gives the same .p47; no line starts with ';' or '#' (rejig would make it a REM step); the header: Index,
Author, Version, Source, then the narrative of tools/forum/NAME.txt (What it is, How to use it, What it changes on
your calculator, Programs and labels) before the first step. C64FX (written by hand) against tests/C64FX.txt
without its REM lines.
  python3 tools/build_forum.py && python3 tools/build_release_v221.py && python3 tests/test_forum.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_p47                                                 # noqa: E402
FAIL = []


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAIL.append(what)


for name, (forum, plain) in build_p47.PROGRAMS.items():
    print('==', name, forum)
    lines = open(os.path.join(ROOT, forum), encoding='utf-8').read().split('\n')
    if plain is None and name == 'C64FX':
        plain = 'tests/C64FX.txt'
    want = [s.strip() for s in open(os.path.join(ROOT, plain), encoding='utf-8').read().split('\n')
            if s.strip() and not s.strip().startswith('REM')]
    body = [ln for ln in lines if ln.strip() and not ln.startswith('@')]
    first = lines.index(body[0])
    head = [ln for ln in lines[:first] if ln.startswith('@')]
    check(all(not ln.lstrip().startswith((';', '#')) for ln in body), 'no line starts with ; or # (no REM steps)')
    check(all(ln.startswith('@') or not ln.lstrip().startswith('@') for ln in lines), "the '@' lines start in column 1")
    steps = [ln.split(';', 1)[0].strip() for ln in body]
    check(steps == want, 'the steps are those of %s (%d)' % (plain, len(want)))
    for f in ('Index', 'Author', 'Version', 'Source'):
        check(any(re.match(r'@ %s: +\S' % f, h) for h in head), '@ %s:' % f)
    for part in ('What it is', 'How to use it', 'What it changes on your calculator', 'Programs and labels'):
        check(any(h.startswith('@ ---- %s ----' % part) for h in head), 'the narrative before the steps: %s' % part)
print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
