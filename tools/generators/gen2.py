src=open('gen.py').read()
exec(src[:src.index('def glyph')])   # F, STAR, SUN, pts
def cols(p, ncol, dyoff=0):
    m=[0]*ncol
    for dy,dx in p: m[dx]|=1<<(dy+dyoff)
    return m
def aglyph(code, masks, advance, pre=None, post=None, ybase='RCL 31'):
    L=['LBL %02d'%code]
    if pre: L+=pre
    L+=ybase.split('\n')+['RCL 30']
    pend=0
    for mk in masks:
        if mk==0: pend+=1; continue
        if pend: L+=[str(pend),'+']; pend=0
        L+=['%s#2'%bin(mk)[2:],'STO 32','R↓','AGRAPH 32']
    pend+=advance-len(masks)
    L+=[str(pend),'+','STO 30']
    if post: L+=post
    return L+['RTN']
def build(name, font, rows, adv, ws, star, sun, cur):
    lines=cur.split('\n')
    num=lines[lines.index('LBL 03'):lines.index('LBL %02d'%min(ord(k) for k in font))] if name=='PTXB' else []
    head=['LBL "%s"'%name,'STO 33','R↓','STO 30','R↓','STO 31','WSIZE %d'%ws,
      'LBL 01','αLENG 33','X=0?','GTO 02','α→𝑥 33','STO 32','XEQ IND 32','GTO 01',
      'LBL 02','WSIZE 64','RCL 31','RCL 30','RTN',
      'LBL 32',str(adv),'STO+ 30','RTN']
    if num:
        i=num.index('LBL 03'); num[i:i+6]=['LBL 03','STO 32','XEQ IND 32','RTN']
        i=num.index('LBL 05'); num[i+1:i+1]=['WSIZE %d'%ws]
        num+=['LBL "PHL"','STO 34','R↓','STO 30','R↓','STO 31','WSIZE %d'%ws,'1#2','STO 32','RCL 31','RCL 30',
              'LBL 21','AGRAPH 32','DSE 34','GTO 21','GTO 02']
    g=[]
    for ch in sorted(font,key=ord):
        g+=aglyph(ord(ch), cols(pts(font[ch]),len(font[ch][0])), adv)
    g+=star; g+=sun
    return head+num+g+['END']
# big font
cur=open('/home/claude/PTXB.txt').read()
star=aglyph(42, cols([(3-r,3+c) for r,c in STAR],7), 12)
sun=aglyph(64, cols([(3-r,5+c) for r,c in SUN],11,dyoff=2), 12, pre=['WSIZE 12'], post=['WSIZE 8'], ybase='RCL 31\n2\n-')
open('/home/claude/PTXB.txt','w').write('\n'.join(build('PTXB',F,7,6,8,star,sun,cur))+'\n')
# small font: recover 3x5 bitmaps from current PTXT (dy dx XEQ 09 triples)
t=open('/home/claude/PTXT.txt').read().split('\n')
small={}; code=None
for i,l in enumerate(t):
    if l.startswith('LBL ') and l[4:].isdigit() and int(l[4:])>=32: code=int(l[4:]); small[code]=[]
    elif l=='XEQ 09' and code: small[code].append((int(t[i-2]),int(t[i-1])))
    elif l=='RTN': code=None if code not in small else code
Fs={}
for c,p in small.items():
    if c in (32,42,64): continue
    rows=['']*5
    grid=[['0']*3 for _ in range(5)]
    for dy,dx in p: grid[4-dy][dx]='1'
    Fs[chr(c)]=[''.join(r) for r in grid]
sstar=aglyph(42, cols(small[42],5), 6); ssun=aglyph(64, cols(small[64],5), 6)
open('/home/claude/PTXT.txt','w').write('\n'.join(build('PTXT',Fs,5,4,8,sstar,ssun,''))+'\n')
print(len(Fs), sorted(Fs))
