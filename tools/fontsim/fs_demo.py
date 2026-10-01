from fontsim import *
p = set()
for fid, t, y, x in ((10, '10 tiny Ag19', 210, 2), (20, '20 standard Ag19', 186, 2), (21, '21 compressed Ag19', 162, 2),
                     (22, '22 bold Ag19', 138, 2), (23, '23 enlarged Ag19', 102, 2),
                     (30, '30 Ag19', 184, 210), (31, '31 Ag19', 156, 210), (32, '32 Ag19', 136, 210),
                     (40, '40 Ag19', 100, 210), (41, '41 Ag19', 72, 210)):
    draw(p, x, y, t, fid)
save(p, 'fs/grfnts_sim.png')
