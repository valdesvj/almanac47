#!/usr/bin/env python3
"""The C47 command reference follows the firmware on master (tools/c47ref.py, local clone of gitlab rpncalculators/c43):
- docs/reference/C47_items_master.tsv is up to date with the clone (skipped without a clone),
- the item numbers tools/rejig47_atext.py writes (ATEXT, GRFNT) are those of the table,
- every C47 program listing is made of commands of the table that are allowed in programs (tools/c47check.py).
  python3 tests/test_c47ref.py"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import c47ref, c47check, rejig47_atext


def main():
    c43 = c47ref.c43_dir()
    if os.path.isdir(os.path.join(c43, 'src', 'c47')):
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'c47ref.py'), '--check', c43], capture_output=True, text=True)
        assert r.returncode == 0, 'reference table out of date: run python3 tools/c47ref.py (%s)' % r.stdout.strip()
        print('table:', r.stdout.strip())
    else:
        print('no C47 source clone at %s: table not compared' % c43)
    rows = {r['catalog_name']: r for r in c47ref.load()}
    for name, by in (('ATEXT', rejig47_atext.ATEXT), ('GRFNT', rejig47_atext.GRFNT)):
        n = int(rows[name]['opcode'])
        assert (str(128 + (n >> 8)), str(n & 255)) == by, '%s is item %d on master, rejig47_atext writes %s' % (name, n, by)
    if not c47ref.rejig_path():
        print('no rejig: listings not checked'); return
    files = sorted(f for g in c47check.DEFAULT for f in __import__('glob').glob(os.path.join(ROOT, g))
                   if not c47check.SKIP.search(f) and c47check.is_program(f))
    bad, used = c47check.check(files)
    assert not bad, '\n'.join(bad)
    print('%d listings, %d commands: all C47 commands allowed in programs on master' % (len(files), len(used)))
    print('ok')


if __name__ == '__main__':
    main()
