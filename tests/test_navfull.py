import sys, os, random, tempfile
sys.path.insert(0,'python')
import c47sim
from c47view import Engine, jd
from decimal import Decimal as D
def split(path):
    progs=[]; cur=[]
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip(): continue
        cur.append(l)
        if l=='END': progs.append(cur); cur=[]
    return progs
def load(paths, tables, fast=False):
    paths=[('build/NAVINIT_FAST.txt' if fast else 'build/NAVINIT_FULL.txt') if p=='build/NAVINIT.txt' else p for p in paths]
    tmp=tempfile.mkdtemp(); files=[]
    for p in paths:
        for i,pr in enumerate(split(p)):
            f=os.path.join(tmp,'%s_%d.txt'%(os.path.basename(p),i)); open(f,'w').write('\n'.join(pr)+'\n'); files.append(f)
    c=c47sim.load(files)
    c.run('INIT',maxsteps=10**7)
    if tables: c.run('TBL',maxsteps=10**7)
    return c
def screen(c,view,j,la,lo):
    c.steps=0; c.pix=[]; c.frames=[]; c.msgs=[]; c.s=[D(0)]*4; c.lift=True
    for v in (j,la,lo): c.push(D(repr(v)))
    c.keys=[]
    try: c.run(view,maxsteps=10**7)
    except StopIteration: pass                      # the view waits for + (WPLS)
    return {(x,239-y) for y,x in c.pix if 0<=x<400 and 0<=y<240}, c.steps
random.seed(2); bad=0; n=0
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
    ref=Engine('programs', tables=tables)
    print('flags', sorted(mini.flags))
    for k in range(10):
        if tables:
            import datetime; d=datetime.date(2026,9,26)+datetime.timedelta(days=random.randint(0,120)); y,m,dd=d.year,d.month,d.day
        else: y,m,dd=random.choice([2025,2026,2027,2028]),random.randint(1,12),random.randint(1,28)
        j=jd(y,m,dd,random.uniform(0,24)); la=random.uniform(-65,65); lo=random.uniform(-180,180)
        for v in ('ALMF','HALMV','ALMS','HALMH'):
            a,sa=screen(mini,v,j,la,lo); b,sb=ref.screen(v,j,la,lo)
            n+=1
            if a!=b[0]: bad+=1; print('DIFF',v,(y,m,dd),la,lo)
            if k==0: print('  %s %s steps mini %d  full %d'%('T' if tables else 'S',v,sa,sb))
print('%d screens compared, %d differences'%(n,bad))
# NAV graphic menu (KEY? keycodes: 1 = 72, 2 = 73, 3 = 74, 4 = 62, 5 = 63, 6 = 64, 7 = 52, 0 = 82, + = 85)
KEYCODE={1:72,2:73,3:74,4:62,5:63,6:64,7:52,8:53,9:54,0:82}
c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.keys=[KEYCODE[1],85,KEYCODE[0]]; c.msgs=[]; c.frames=[]
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12'); c.pix=[]
c.run('NAV',maxsteps=10**7)
print('NAV menu: 1, +, 0 -> frames', len(c.frames), '(menu, item inverted, ALMF, menu), ended', c.pix==[])
# arrows: 1 (ALMF), up (one hour later), down twice (one hour earlier), +, 0
c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.keys=[KEYCODE[1],51,61,61,85,KEYCODE[0]]; c.msgs=[]; c.frames=[]; c.pix=[]
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
c.run('NAV',maxsteps=10**8)
ref=Engine('programs'); ok=[]
for f,dh in zip(c.frames[2:6],(0,1,0,-1)):
    b,_=ref.screen('ALMF',jd(2026,9,26,14+57/60+dh),25+20/60,55+12/60)
    ok.append({(x,239-y) for y,x in f if 0<=x<400 and 0<=y<240}==b[0])
print('NAV arrows: ALMF at +0 +1 0 -1 h:', ok)
# ALMT through the minimum set
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
    ref=Engine('programs', tables=tables); bad=0
    for k in range(6):
        j=jd(2026,10+k%3,3+5*k,7.5+k); la=-40+15*k; lo=-150+50*k
        mini.s=[D(0)]*4; mini.lift=True; mini.msgs=[]; mini.maxprompts=120
        for v in (j,la,lo): mini.push(D(repr(v)))
        try: mini.run('ALMT',maxsteps=10**7)
        except StopIteration: pass
        m=[str(x) for x in mini.msgs]; m=m[:m.index(m[0],1)] if m[0] in m[1:] else m
        if m!=ref.text(j,la,lo)[0]: bad+=1
    print('ALMT', 'tables' if tables else 'series', 'differences', bad, '| first line:', m[0])
c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.keys=[KEYCODE[3]]; c.answers=[]; c.msgs=[]; c.maxprompts=6
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**7)
except StopIteration: pass
print('NAV option 3:', [str(m) for m in c.msgs][:5])
# HORZ through the minimum set: every info frame of one cycle
def horz(c,j,la,lo):
    c.steps=0; c.pix=[]; c.frames=[]; c.msgs=[]; c.s=[D(0)]*4; c.lift=True; c.maxpauses=11; c.keys=[11]*20
    for v in (j,la,lo): c.push(D(repr(v)))
    try: c.run('HORZ',maxsteps=10**7)
    except StopIteration: pass
    c.maxpauses=None
    return [{(x,239-y) for y,x in f if 0<=x<400 and 0<=y<240} for f in c.frames[:int(c.rget('10'))]]
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
    ref=Engine('programs', tables=tables); bad=0
    for k in range(5):
        j=jd(2026,10+k%3,3+5*k,4.5+4*k); la=-50+25*k; lo=-150+60*k
        a=horz(mini,j,la,lo); b,_=ref.screen('HORZ',j,la,lo)
        if a!=b: bad+=1; print('HORZ DIFF',k,len(a),len(b))
    print('HORZ', 'tables' if tables else 'series', 'differences', bad, 'frames last case', len(a))
c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.keys=[KEYCODE[4],11,11,11]; c.msgs=[]; c.frames=[]; c.pix=[]; c.maxpauses=4
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**7)
except StopIteration: pass
print('NAV option 4:', [str(m) for m in c.msgs][:1], 'HORZ frames', len(c.frames), 'pixels', len(c.pix))
for opt,name in ((5,'ALMS'),(6,'HALMH')):
    c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
    c.s=[D(0)]*4; c.keys=[KEYCODE[opt],85,KEYCODE[0]]; c.msgs=[]; c.pix=[]; c.frames=[]
    c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
    ref=Engine('programs'); b,_=ref.screen(name,jd(2026,9,26,14+57/60),25+20/60,55+12/60)
    c.run('NAV',maxsteps=10**7)
    a={(x,239-y) for y,x in c.frames[2] if 0<=x<400 and 0<=y<240}     # frames: menu, item inverted (PAUSE 3), the view, menu
    print('NAV option %d (%s):'%(opt,name), 'same screen' if a==b[0] else 'DIFF', [str(m) for m in c.msgs][:1])
# option 7 BODY: first list page and a chosen star
c=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.keys=[KEYCODE[7]]; c.answers=[18,None,None]; c.msgs=[]; c.maxprompts=6
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**8)
except StopIteration: pass
print('NAV option 7 (BODY):', [str(m) for m in c.msgs][0:3])
# FAST series through INIT option 2
pass
mini=load(['build/NAVINIT.txt','build/dev/NAVFULL.txt'],False,fast=True)
ref=Engine('programs',fast=True); bad=0; n=0
for k in range(8):
    j=jd(2026+k%5,1+k,3+3*k,2.5+2*k); la=-50+14*k; lo=-170+45*k
    for v in ('ALMF','HALMV','ALMS','HALMH'):
        a,_=screen(mini,v,j,la,lo); b,_=ref.screen(v,j,la,lo); n+=1
        if a!=b[0]: bad+=1; print('FAST DIFF',v,k)
print('FAST via INIT: %d screens, %d differences'%(n,bad), [str(m) for m in mini.msgs][-1:] if mini.msgs else '')
# NAV + INIT in one file: the first NAV builds the matrices and deletes INIT (DELP), flag 81
def load_one(path):
    tmp=tempfile.mkdtemp(); files=[]
    for i,pr in enumerate(split(path)+split('build/NAVINIT_FAST.txt')):
        f=os.path.join(tmp,'p_%d.txt'%i); open(f,'w').write('\n'.join(pr)+'\n'); files.append(f)
    return c47sim.load(files)
ref=Engine('programs',fast=True)
for name,opts in (('build/NAVALL.txt',(1,2,4,5,6,9)),('build/NAVCOMP.txt',(1,2,4,9))):
    c=load_one(name)
    c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
    res=[]
    for k,opt in enumerate(opts):
        keys=[KEYCODE[3]] if 'COMP' in name and k==0 else []          # 3 is not in the compact menu: ignored
        c.s=[D(0)]*4; c.keys=keys+[KEYCODE[opt]]+([11,85] if opt==4 else [85])+[KEYCODE[0]]; c.frames=[]; c.pix=[]
        c.run('NAV',maxsteps=10**8)
        v={1:'ALMF',2:'HALMV',4:'HORZ',5:'ALMS',6:'HALMH',9:'ALLSKY'}[opt]
        b,_=ref.screen(v,jd(2026,9,26,14+57/60),25+20/60,55+12/60)
        f=c.frames[2+len(keys)]
        res.append({(x,239-y) for y,x in f if 0<=x<400 and 0<=y<240}==b[0])
    print(os.path.basename(name), 'INIT run once, flag 81:', 81 in c.flags, 'views same as FAST:', res)
# text only: NAVTXT_FAST writes the page into R50 ... (no drawing); compare with ALMT's PROMPT pages
c=load_one('build/NAVTXT.txt')
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
c.s=[D(0)]*4; c.pix=[]; c.run('NAV',maxsteps=10**8)
n=int(c.rget('79')); lines=[str(c.rget(str(r))) for r in range(50,n)]
pages,_=ref.text(jd(2026,9,26,14+57/60),25+20/60,55+12/60)
i=0; ok=True
for pg in pages:
    if pg.strip().startswith('DOES NOT'):
        ok &= lines[i]==pg; i+=1; continue
    l1,l2=lines[i],lines[i+1]; i+=2
    ok &= pg.split()==(l1+' '+l2).split()                    # same words (the line break is a register)
order=[str(c.s[k]) for k in range(4)]+[str(c.rget(r)) for r in 'IJKMNPQRSEFGHOUVW']
lett = order[:4]==lines[:4] and order[4:]==lines[9:26]
print('NAVTXT: X =', c.s[0][:30], '| lines', len(lines), '| same text as ALMT:', ok and i==len(lines), '| stack + lettered in REGS order:', lett, '| pixels', len(c.pix))
for l in lines[:4]: print('   ', l)
