#!/usr/bin/env python3
"""free42_shots.py - the Free42 screens for the Free42 manual (docs/free42/*.png), captured in
f42run (tools/f42, the Free42 core with the DM42 400 x 240 graphics): 26 Sep 2026 14:57 UT,
25 20 N 055 12 E, NAVINIT_FAST + NAVFULL (build/free42/); NAVLITTLE: F42_little.png.   python3 tools/generators/free42_shots.py"""
import os, subprocess, tempfile
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
OUT = os.path.join(ROOT, 'docs', 'free42')
KEY = {1: 29, 2: 30, 3: 31, 4: 24, 5: 25, 6: 26, 7: 19, 8: 20, 9: 21}
NAMES = {0: 'menu', 1: 'almanac', 2: 'chart', 3: 'text', 4: 'sky', 5: 'small', 6: 'split', 7: 'anim', 8: 'allsky', 9: 'info'}


def png(pbm, dst):
    L = open(pbm).read().split('\n')[2:242]
    im = Image.new('L', (400, 240), 255)
    px = im.load()
    for y, r in enumerate(L):
        for x, c in enumerate(r):
            if c == '1':
                px[x, y] = 0
    im.resize((800, 480), Image.NEAREST).save(dst)


def main():
    os.makedirs(OUT, exist_ok=True)
    t = tempfile.mkdtemp()
    cmd = ['paste %s/build/free42/NAVINIT_FAST.txt' % ROOT, 'paste %s/build/free42/NAVFULL.txt' % ROOT,
           'xeq INIT', 'xeq NAV', 'num 2026.0926', 'num 14.57', 'num 25.20', 'num 55.12', 'shot %s/v0.pbm' % t]
    for v in (1, 2, 3, 5, 6, 8, 9):
        cmd += ['key %d' % KEY[v], 'shot %s/v%d.pbm' % (t, v), 'key 37']
    cmd += ['qkey 37 3500 %s/v4.pbm' % t, 'key 24']                  # SKY: the name line changes every 3 s
    cmd += ['film %s/a' % t, 'key 19', 'stopfilm', 'shot %s/v7.pbm' % t, 'key 37']
    subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=300)
    for v, n in NAMES.items():
        if os.path.exists('%s/v%d.pbm' % (t, v)):
            png('%s/v%d.pbm' % (t, v), os.path.join(OUT, 'F42_%s.png' % n))
    # the busy box with ants (flag 97): a capture during the view change
    cmd = cmd[:3] + ['xeq ANTS97'] + cmd[3:9] + ['film %s/b 1' % t, 'key 29', 'stopfilm']
    open('%s/ants.txt' % t, 'w').write('LBL "ANTS97"\nSF 97\nEND\n')
    cmd.insert(2, 'paste %s/ants.txt' % t)
    subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=300)
    fs = sorted((f for f in os.listdir(t) if f.startswith('b_')), key=lambda f: int(f[2:-4]))
    if fs:
        png(os.path.join(t, fs[len(fs) // 2]), os.path.join(OUT, 'F42_box_ants.png'))
    # NAVLITTLE: the ALMANAC screen with the 5 x 7 font, Sun and stars only
    cmd = ['paste %s/build/free42/NAVINIT_LITTLE.txt' % ROOT, 'paste %s/build/free42/NAVLITTLE.txt' % ROOT,
           'xeq INIT', 'xeq NAV', 'num 2026.0926', 'num 14.57', 'num 25.20', 'num 55.12', 'shot %s/l.pbm' % t]
    subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=300)
    png('%s/l.pbm' % t, os.path.join(OUT, 'F42_little.png'))
    print(sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
