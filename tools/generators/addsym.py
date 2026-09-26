src=open('gen2.py').read()
exec(src[:src.index('# big font')])   # cols, aglyph, pts, F...
SYM={40:["..###..",".##....","##.....","##.....","##.....",".##....","..###.."],   # moon crescent
 60:["..###..",".#...#.",".#...#.","..###..","...#...",".#####.","...#..."],             # Venus
 62:["...####",".....##","....#.#",".###...","#...#..","#...#..",".###..."],             # Mars
 61:[".##....","#..#.#.","...#.#.","..#..#.","#######",".....#.",".....#."],             # Jupiter
 63:[".#.....","####...",".#.....",".#.##..",".##..#.",".#...#.","....#.."]}             # Saturn
L=open('/home/claude/PTXB.txt').read().rstrip('\n').split('\n')
assert L[-1]=='END'; L=L[:-1]
for code,rows in SYM.items():
    if 'LBL %02d'%code in L: continue
    L+=aglyph(code, cols(pts([r.replace('#','1') for r in rows]),7), 12)
open('/home/claude/PTXB.txt','w').write('\n'.join(L+['END'])+'\n')
print('ok', len(L))
