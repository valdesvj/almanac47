from fontsim import *
rows = [('37 ARCTURUS', '24 59.7', '280.2'), ('56 FOMALHAUT', '10 35.9', '130.0'), ('SUN', '-11 06.4', '273.7')]
L = ['LBL "FNTCHT"', 'REM "CHART rows in GRFNT 21, 32, 10 and 20 at the x of the simulation (fontsim.py); 9 = SNAP"', 'CLLCD']
p = set(); y = 216
for fid in (21, 32, 10, 20):
    draw(p, 2, y, str(fid), 10); L += ['10', 'GRFNT', 'DROP', '"%d"' % fid, 'STO 00', 'DROP', str(y), '2', 'ATEXT 00', 'DROP', 'DROP']
    L += ['%d' % fid, 'GRFNT', 'DROP']
    for t, h, z in rows:
        zx = 398 - width(z, fid); hx = zx - 8 - width(h, fid)
        for x, s in ((190, t), (hx, h), (zx, z)):
            L += ['"%s"' % s, 'STO 00', 'DROP', str(y), str(x), 'ATEXT 00', 'DROP', 'DROP']
            draw(p, x, y, s, fid)
        y -= {21: 16, 32: 16, 10: 10, 20: 16}[fid]
    y -= 10
L += ['20', 'GRFNT', 'DROP', 'PAUSE 99', 'RTN', 'END']
open('/home/claude/C47_nav/extras/FNTCHT.txt', 'w').write('\n'.join(L) + '\n')
save(p, 'fs/fntcht_sim.png'); print(y)
