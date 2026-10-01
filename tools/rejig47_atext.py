#!/usr/bin/env python3
"""rejig47_atext.py - .txt -> .p47 for programs with ATEXT and GRFNT, with a rejig that does not know them.

ATEXT is C47 item 1340, two bytes in a .p47 file: 133 60 (as AGRAPH, item 1409, is 133 129).
Each ATEXT step is written as KTYP (133 221, the same kind of register argument, not used by
these programs), converted with rejig, and the two bytes of every KTYP are set to 133 60.
The number of KTYP found in the .p47 must be the number of ATEXT steps, or nothing is written.
GRFNT (item 1342, the font of ATEXT from X: 10 tiny, 20 standard; GRFNT# 1341 is the getter) is
written as CLMENU (133 144, no argument, not used by these programs) and set to 133 62 the same way.
The item numbers are from the item table of the patched rejig (ATEXT 1340, GRFNT# 1341, GRFNT 1342).
A rejig that knows ATEXT (the patched one) gives the same file directly.

  python3 tools/rejig47_atext.py FILE.txt [...]     -> FILE.p47 next to each FILE.txt
  REJIG=/path/to/rejig to choose the rejig (default /home/claude/rejig/rejig or rejig on PATH)
"""
import os, re, shutil, subprocess, sys, tempfile

PLACE, ATEXT = ('133', '221'), ('133', '60')
PLACE_F, GRFNT = ('133', '144'), ('133', '62')


def rejig():
    r = os.environ.get('REJIG') or ('/home/claude/rejig/rejig' if os.path.exists('/home/claude/rejig/rejig')
                                    else shutil.which('rejig'))
    if not r:
        raise SystemExit('rejig not found (set REJIG)')
    return r


def convert(path):
    L = open(path, encoding='utf-8').read().split('\n')
    n = sum(1 for l in L if re.fullmatch(r'ATEXT .+', l))
    nf = sum(1 for l in L if l == 'GRFNT')
    assert not any(re.fullmatch(r'KTYP .+', l) or l == 'CLMENU' for l in L), 'KTYP or CLMENU already in ' + path
    t = tempfile.mkdtemp()
    src = os.path.join(t, 'in.txt'); dst = os.path.join(t, 'out.p47')
    open(src, 'w', encoding='utf-8').write('\n'.join('CLMENU' if l == 'GRFNT' else re.sub(r'^ATEXT ', 'KTYP ', l) for l in L))
    subprocess.run([rejig(), src, '-o', dst], check=True)
    B = open(dst, encoding='ascii').read().split('\n')
    k = B.index('PROGRAM')
    at = [i for i in range(k + 2, len(B) - 1) if (B[i], B[i + 1]) == PLACE]
    assert len(at) == n, '%s: %d ATEXT steps but %d KTYP in the .p47' % (path, n, len(at))
    for i in at:
        B[i], B[i + 1] = ATEXT
    af = [i for i in range(k + 2, len(B) - 1) if (B[i], B[i + 1]) == PLACE_F]
    assert len(af) == nf, '%s: %d GRFNT steps but %d CLMENU in the .p47' % (path, nf, len(af))
    for i in af:
        B[i], B[i + 1] = GRFNT
    out = os.path.splitext(path)[0] + '.p47'
    open(out, 'w', encoding='ascii').write('\n'.join(B))
    return out, n, nf


if __name__ == '__main__':
    for p in sys.argv[1:]:
        out, n, nf = convert(p)
        print('%s: %d ATEXT, %d GRFNT, %d bytes' % (out, n, nf, os.path.getsize(out)))
