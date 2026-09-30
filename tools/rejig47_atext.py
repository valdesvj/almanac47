#!/usr/bin/env python3
"""rejig47_atext.py - .txt -> .p47 for programs with ATEXT, with a rejig that does not know ATEXT.

ATEXT is C47 item 1340, two bytes in a .p47 file: 133 60 (as AGRAPH, item 1409, is 133 129).
Each ATEXT step is written as KTYP (133 221, the same kind of register argument, not used by
these programs), converted with rejig, and the two bytes of every KTYP are set to 133 60.
The number of KTYP found in the .p47 must be the number of ATEXT steps, or nothing is written.
A rejig that knows ATEXT (the patched one) gives the same file directly.

  python3 tools/rejig47_atext.py FILE.txt [...]     -> FILE.p47 next to each FILE.txt
  REJIG=/path/to/rejig to choose the rejig (default /home/claude/rejig/rejig or rejig on PATH)
"""
import os, re, shutil, subprocess, sys, tempfile

PLACE, ATEXT = ('133', '221'), ('133', '60')


def rejig():
    r = os.environ.get('REJIG') or ('/home/claude/rejig/rejig' if os.path.exists('/home/claude/rejig/rejig')
                                    else shutil.which('rejig'))
    if not r:
        raise SystemExit('rejig not found (set REJIG)')
    return r


def convert(path):
    L = open(path, encoding='utf-8').read().split('\n')
    n = sum(1 for l in L if re.fullmatch(r'ATEXT .+', l))
    assert not any(re.fullmatch(r'KTYP .+', l) for l in L), 'KTYP already in ' + path
    t = tempfile.mkdtemp()
    src = os.path.join(t, 'in.txt'); dst = os.path.join(t, 'out.p47')
    open(src, 'w', encoding='utf-8').write('\n'.join(re.sub(r'^ATEXT ', 'KTYP ', l) for l in L))
    subprocess.run([rejig(), src, '-o', dst], check=True)
    B = open(dst, encoding='ascii').read().split('\n')
    k = B.index('PROGRAM')
    at = [i for i in range(k + 2, len(B) - 1) if (B[i], B[i + 1]) == PLACE]
    assert len(at) == n, '%s: %d ATEXT steps but %d KTYP in the .p47' % (path, n, len(at))
    for i in at:
        B[i], B[i + 1] = ATEXT
    out = os.path.splitext(path)[0] + '.p47'
    open(out, 'w', encoding='ascii').write('\n'.join(B))
    return out, n


if __name__ == '__main__':
    for p in sys.argv[1:]:
        out, n = convert(p)
        print('%s: %d ATEXT, %d bytes' % (out, n, os.path.getsize(out)))
