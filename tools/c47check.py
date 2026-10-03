#!/usr/bin/env python3
"""c47check.py - check C47 program listings (.txt) against the command table of the firmware on master.

rejig reads each listing (so every name must be one rejig knows; ATEXT and GRFNT go in the way
tools/rejig47_atext.py writes them) and writes it back in its own names. Each command is then looked up
by its item number in docs/reference/C47_items_master.tsv (tools/c47ref.py, from the local clone of
gitlab rpncalculators/c43): it must exist on master and be allowed in programs. Commands that master
has renamed since this rejig (TICKS -> TICKS#) are listed as notes.

  python3 tools/c47check.py [FILE.txt ...]     default: the C47 builds and programs of this repository
                                               exit 1 if a step is not a C47 command
"""
import glob, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c47ref                                                   # noqa: E402

ROOT = os.path.join(HERE, '..')
DEFAULT = ['build/*.txt', 'build/dm42/*.txt', 'build/dm42/dev/*.txt', 'build/dev/*.txt', 'programs/*.txt',
           'programs/atext/*.txt', 'programs/atext/*/*.txt']
SKIP = re.compile(r'_LABELS\.txt$|README|LICENSE|COPYING|NOTICE|PROGRAM_MAP')
LITERAL = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)([Eᴇ][-+]?\d+)?|[0-9A-Fa-f]+(#\d+|[₀-₉]+)|⊦?[\"‘“'].*")


def canonical(path):
    """The steps of a listing in rejig's own names (rejig utf8 -> utf8). ATEXT / GRFNT, which this rejig
    does not know, go in as KTYP / CLMENU (as in tools/rejig47_atext.py) and come back as ATEXT / GRFNT."""
    src = open(path, encoding='utf-8').read().split('\n')
    assert not any(re.fullmatch(r'\s*(KTYP .+|CLMENU)\s*', l) for l in src), 'KTYP or CLMENU already in ' + path
    t = tempfile.mkdtemp()
    a, b = os.path.join(t, 'in.txt'), os.path.join(t, 'out.txt')
    open(a, 'w', encoding='utf-8').write('\n'.join(
        'CLMENU' if l.strip() == 'GRFNT' else re.sub(r'^(\s*)ATEXT ', r'\1KTYP ', l) for l in src))
    r = subprocess.run([c47ref.rejig_path(), '-q', '-f', 'utf8', '-t', 'utf8', a, '-o', b],
                       capture_output=True, text=True)
    if r.returncode:
        raise ValueError('rejig: ' + r.stderr.strip().split('\n')[-1])
    for ln in open(b, encoding='utf-8'):
        ln = ln.strip()
        if ln and not ln.startswith('#'):                     # rejig keeps the # comments
            yield 'GRFNT' if ln == 'CLMENU' else re.sub(r'^KTYP ', 'ATEXT ', ln)


def is_program(path):
    for ln in open(path, encoding='utf-8', errors='replace'):
        if ln.strip():
            return ln.strip().startswith('LBL')
    return False


def check(files):
    rows = c47ref.load()
    by_rejig = {r['rejig_name']: r for r in rows if r['rejig_name']}
    for name in ('ATEXT', 'GRFNT'):
        by_rejig[name] = next(r for r in rows if r['catalog_name'] == name)
    longest = max(map(len, by_rejig))
    bad, used = [], {}
    for f in files:
        try:
            steps = list(canonical(f))
        except ValueError as e:
            bad.append('%s: %s' % (os.path.relpath(f, ROOT), e))
            continue
        for ln in steps:
            if LITERAL.fullmatch(ln):
                continue
            op = next((ln[:k] for k in range(min(len(ln), longest), 0, -1)
                       if ln[:k] in by_rejig and (k == len(ln) or ln[k] == ' ')), None)
            if op is None:
                bad.append('%s: %s  (rejig wrote a name that is not in the table)' % (os.path.relpath(f, ROOT), ln))
                continue
            r = by_rejig[op]
            used.setdefault(r['opcode'], [op, r, 0])[2] += 1
            if r['programmable'] == 'PTP_DISABLED':
                bad.append('%s: %s  (item %s: not programmable on master)' % (os.path.relpath(f, ROOT), ln, r['opcode']))
    return bad, used


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(f for g in DEFAULT for f in glob.glob(os.path.join(ROOT, g)) if not SKIP.search(f) and is_program(f))
    bad, used = check(files)
    print('%d files, %d different commands used; table: %s' % (
        len(files), len(used), open(c47ref.OUT, encoding='utf-8').read().split('\n')[1][10:]))
    for op, r, n in sorted(used.values(), key=lambda u: u[0]):
        if r['catalog_name'].isascii() and op.isascii() and op != r['catalog_name']:
            print('  note: %s (item %s, %d steps) is %s on master' % (op, r['opcode'], n, r['catalog_name']))
    for b in bad:
        print('  ' + b)
    sys.exit(1 if bad else 0)
