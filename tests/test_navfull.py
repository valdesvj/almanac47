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
    tmp=tempfile.mkdtemp(); files=[]
    for p in paths:
        for i,pr in enumerate(split(p)):
            f=os.path.join(tmp,'%s_%d.txt'%(os.path.basename(p),i)); open(f,'w').write('\n'.join(pr)+'\n'); files.append(f)
    c=c47sim.load(files)
    c.answers=[2] if fast else [1]
    c.run('INIT',maxsteps=10**7)
    if tables: c.run('TBL',maxsteps=10**7)
    return c
def screen(c,view,j,la,lo):
    c.steps=0; c.pix=[]; c.frames=[]; c.msgs=[]; c.s=[D(0)]*4; c.lift=True
    for v in (j,la,lo): c.push(D(repr(v)))
    c.run(view,maxsteps=10**7)
    return {(x,239-y) for y,x in c.pix if 0<=x<400 and 0<=y<240}, c.steps
random.seed(2); bad=0; n=0
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
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
# NAV menu smoke test: choose 1 (ALMF) with inputs, then 0
c=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.answers=[1,0]; c.msgs=[]
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12'); c.pix=[]
c.run('NAV',maxsteps=10**7)
print('NAV prompts:', [str(m) for m in c.msgs][:3], 'pixels drawn', len(c.pix))
# ALMT through the minimum set
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
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
c=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.answers=[3]; c.msgs=[]; c.maxprompts=6
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**7)
except StopIteration: pass
print('NAV option 3:', [str(m) for m in c.msgs][:5])
# HORZ through the minimum set: every info frame of one cycle
def horz(c,j,la,lo):
    c.steps=0; c.pix=[]; c.frames=[]; c.msgs=[]; c.s=[D(0)]*4; c.lift=True; c.maxpauses=11
    for v in (j,la,lo): c.push(D(repr(v)))
    try: c.run('HORZ',maxsteps=10**7)
    except StopIteration: pass
    c.maxpauses=None
    return [{(x,239-y) for y,x in f if 0<=x<400 and 0<=y<240} for f in c.frames[:int(c.rget('10'))]]
for tables in (False, True):
    mini=load(['build/NAVINIT.txt','build/NAVFULL.txt']+(['build/TBL.txt'] if tables else []), tables)
    ref=Engine('programs', tables=tables); bad=0
    for k in range(5):
        j=jd(2026,10+k%3,3+5*k,4.5+4*k); la=-50+25*k; lo=-150+60*k
        a=horz(mini,j,la,lo); b,_=ref.screen('HORZ',j,la,lo)
        if a!=b: bad+=1; print('HORZ DIFF',k,len(a),len(b))
    print('HORZ', 'tables' if tables else 'series', 'differences', bad, 'frames last case', len(a))
c=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.answers=[4]; c.msgs=[]; c.frames=[]; c.pix=[]; c.maxpauses=3
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**7)
except StopIteration: pass
print('NAV option 4:', [str(m) for m in c.msgs][:1], 'HORZ frames', len(c.frames), 'pixels', len(c.pix))
for opt,name in ((5,'ALMS'),(6,'HALMH')):
    c=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False)
    c.s=[D(0)]*4; c.answers=[opt,0]; c.msgs=[]; c.pix=[]
    c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
    ref=Engine('programs'); b,_=ref.screen(name,jd(2026,9,26,14+57/60),25+20/60,55+12/60)
    c.run('NAV',maxsteps=10**7)
    a={(x,239-y) for y,x in c.pix if 0<=x<400 and 0<=y<240}
    print('NAV option %d (%s):'%(opt,name), 'same screen' if a==b[0] else 'DIFF', [str(m) for m in c.msgs][:1])
# option 7 BODY: first list page and a chosen star
c=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False)
c.s=[D(0)]*4; c.answers=[7,18,None,None]; c.msgs=[]; c.maxprompts=6
c.reg['DATE']=D('2026.0926'); c.reg['UTC']=D('14.57'); c.reg['LAT']=D('25.20'); c.reg['LON']=D('55.12')
try: c.run('NAV',maxsteps=10**8)
except StopIteration: pass
print('NAV option 7 (BODY):', [str(m) for m in c.msgs][1:4])
# FAST series through INIT option 2
pass
mini=load(['build/NAVINIT.txt','build/NAVFULL.txt'],False,fast=True)
ref=Engine('programs',fast=True); bad=0; n=0
for k in range(8):
    j=jd(2026+k%5,1+k,3+3*k,2.5+2*k); la=-50+14*k; lo=-170+45*k
    for v in ('ALMF','HALMV','ALMS','HALMH'):
        a,_=screen(mini,v,j,la,lo); b,_=ref.screen(v,j,la,lo); n+=1
        if a!=b[0]: bad+=1; print('FAST DIFF',v,k)
print('FAST via INIT: %d screens, %d differences'%(n,bad), [str(m) for m in mini.msgs][-1:] if mini.msgs else '')
