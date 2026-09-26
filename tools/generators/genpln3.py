# genpln3.py - appends PLN3 (quick planet check) to programs/PLAN.txt. Run once on the PLAN.txt
# without PLN3 (reference; PLAN.txt already contains it). Elements: kepler_quick.py (Standish).
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from kepler_quick import EL
P=[]
def a(*x): P.extend(x)
a('LBL "PLN3"','FS? 10','GTO "PLN2"','STO 59','DEG',
  '0','XEQ 50','RCL 31','STO 56','RCL 33','STO 57','RCL 30','STO 58',
  'RCL 59','XEQ 50',
  'RCL 31','RCL- 56','STO 31','RCL 33','RCL- 57','STO 33','RCL 30','RCL- 58','STO 30',
  'RCL 31','X↑2','RCL 33','X↑2','+','RCL 30','X↑2','+','0.5','Y↑X','STO 58',
  'RCL 33','RCL 31','→POL','STO 56','X<>Y','RCL 54','1.3969713','×','+','STO 57',
  'RCL 30','RCL 56','→POL','X<>Y','STO 56',
  'RCL 56','SIN','23.4393','COS','×','RCL 56','COS','23.4393','SIN','×','RCL 57','SIN','×','+','ASIN','STO 52',
  'RCL 57','SIN','23.4393','COS','×','RCL 56','TAN','23.4393','SIN','×','-','RCL 57','COS','→POL','X<>Y',
  'RCL 80','X<>Y','-','360','MOD','STO 53',
  'RCL 52','RCL 53','XEQ "HCZ"',
  '-1','RCL 96','X>Y?','GTO 26',
  '0','0','RCL 52','RCL 53','RTN',
  'LBL 26','RCL 58','0.0057755183','×','STO 08','1','STO 07','RCL 59','STO 09','GTO 27')
# heliocentric position of body X (0 Earth-Moon barycentre, 1-4 planets): x R31, y R33, z R30
a('LBL 50','60','+','STO 52','XEQ IND 52',
  'RCL 33','RCL- 51','STO 52','STO 68')
for _ in range(4): a('RCL 68','SIN','RCL× 31','57.29577951308232','×','RCL+ 52','STO 68')
a('RCL 68','COS','RCL- 31','RCL× 30',
  'RCL 31','X↑2','1','X<>Y','-','0.5','Y↑X','RCL× 30','RCL 68','SIN','×',
  'X<>Y','→POL','STO 69','X<>Y','RCL+ 51','RCL- 53','STO 52',
  'RCL 52','SIN','RCL 32','SIN','×','RCL× 69','STO 30',
  'RCL 52','SIN','RCL 32','COS','×','STO 32',
  'RCL 52','COS','RCL 53','COS','×','RCL 32','RCL 53','SIN','×','-','RCL× 69','STO 31',
  'RCL 52','COS','RCL 53','SIN','×','RCL 32','RCL 53','COS','×','+','RCL× 69','STO 33','RTN')
def num(v):
    t=('%.12g'%v).replace('e','E').replace('E+','E')
    return t.replace('E-0','E-').replace('E0','E')
for b in range(5):
    e0,r=EL[b]; a('LBL %d'%(60+b))
    for k,reg in zip(range(6),(30,31,32,33,51,53)):
        a(num(r[k]),'RCL× 54',num(e0[k]),'+','STO %d'%reg)
    a('RTN')
s=open('/home/claude/C47_nav/programs/PLAN.txt').read()
o='LBL 28\nRAD\n0\nSTO 08\n2\nSTO 07\nLBL 30\n'; assert s.count(o)==1; s=s.replace(o,'LBL 28\nRAD\nLBL 30\n')
o='LBL 33\nRCL 54\n'; assert s.count(o)==1; s=s.replace(o,'LBL 33\n0\nSTO 08\n2\nSTO 07\nLBL 27\nRCL 54\n')
assert s.rstrip().endswith('END'); s=s.rstrip()[:-3]+'\n'.join(P)+'\nEND\n'
open('/home/claude/C47_nav/programs/PLAN.txt','w').write(s); print(len(P),'lines added')
