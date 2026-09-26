P=[]
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y,x,s): a(y,x,'"%s"'%s,'XEQ "PTXB"')
def num(y,x,reg,fn): a(y,x,'RCL %s'%reg,'XEQ "%s"'%fn)
def hline(y,lab):
    a('-%d'%y,'0','PIXEL')
GX,DX,HX,ZX=112,184,256,330
a('LBL "ALMF"','STO 12','R↓','STO 11','R↓','STO 10')
for reg,lab in ((13,'NTWA'),(14,'RISE'),(15,'TRAN'),(16,'SET'),(17,'NTWP')):
    a('XEQ 26','XEQ "%s"'%lab,'STO %d'%reg)
a('RCL 10','XEQ "PHAS"','STO 18','X<>Y','STO 19')
a('RCL 10','STO 90','RCL 11','STO 91','RCL 12','STO 92','CLLCD')
a('RCL 10','XEQ "SUNA"','STO 45','R↓','STO 46','R↓','STO 48','RCL 73','15.99383','X<>Y','÷','STO 29')
# line 1
num(229,4,10,'PDAT')
a(229,76,'RCL 10','0.5','+','1','MOD','24','×','XEQ "PHM"'); txt(229,112,'UT')
txt(229,142,'DR')
a('"N"','STO 43','RCL 11','X<0?','XEQ 22'); a(229,160,'RCL 43','XEQ "PTXB"'); a(229,160,'RCL 11','ABS','XEQ "PDM"')
a('"E"','STO 43','RCL 12','X<0?','XEQ 27'); a(229,220,'RCL 43','XEQ "PTXB"'); a(229,226,'RCL 12','ABS','XEQ "PDM"')
txt(229,292,'ARIES'); num(229,328,48,'PDM')
hline(219,31)
txt(207,34,'BODY'); txt(207,GX+36,'GHA'); txt(207,DX+36,'DEC'); txt(207,HX+42,'HC'); txt(207,ZX+18,'ZN')
a('194','STO 40','RCL 46','RCL 45','XEQ "HCZ"')
a('RCL 40','4','"@"','XEQ "PTXB"','RCL 40','34','"SUN"','XEQ "PTXB"','XEQ 60')
a('1','STO 41')
# Moon, if above the horizon
a('XEQ "MOO2"','STO 45','R↓','STO 46','R↓','STO 21','R↓','STO 22','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 61')
# planets above the horizon
a('1.004','STO 42','LBL 16','RCL 42','IP','XEQ "PLN2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 63','ISG 42','GTO 16')
# brightest stars higher than 10 deg until the table has 10 rows
a('1.058','STO 42','LBL 17','10','RCL 41','X≥Y?','GTO 19','RCL 42','IP','XEQ "SBRT"','STO 82','XEQ "STR2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"',
  '10','RCL 96','X≤Y?','GTO 18',
  'RCL 40','4','"*"','XEQ "PTXB"','RCL 40','16','RCL 82','XEQ "PINB"',
  'RCL 82','XEQ "SNMU"','STO 43','RCL 40','34','RCL 43','XEQ "PTXB"','XEQ 60',
  '1','STO+ 41','LBL 18','ISG 42','GTO 17','LBL 19')
hline(80,32)
txt(69,4,'SUN UT'); txt(69,94,'AM'); txt(69,136,'PM')
txt(69,184,'MOON'); a(69,220,'RCL 18','XEQ "PINB"','"%"','XEQ "PTXB"')
a('"WAXING"','STO 43','RCL 19','14.765','X<Y?','XEQ 28'); a(69,262,'RCL 43','XEQ "PTXB"')
txt(57,4,'NAUT TWI'); num(57,85,13,'PHM'); num(57,127,17,'PHM')
a(57,184,'"AGE "','XEQ "PTXB"','RCL 19','XEQ "PF1"','" DAYS"','XEQ "PTXB"')
txt(45,4,'RISE/SET'); num(45,85,14,'PHM'); num(45,127,16,'PHM')
a(45,184,'"SUN SD "','XEQ "PTXB"','RCL 29','XEQ "PF1"')
txt(33,4,'MER PASS'); num(33,106,15,'PHM')
a(33,184,'"MOON HP "','XEQ "PTXB"','RCL 21','XEQ "PF1"','" SD "','XEQ "PTXB"','RCL 22','XEQ "PF1"')
a('-22','0','PIXEL')
txt(8,89,'DOES NOT REPLACE THE NAUTICAL ALMANAC')
a('3','STO 37','LBL 20','PAUSE 99','DSE 37','GTO 20','RTN')
a('LBL 26','RCL 10','0.5','-','IP','0.5','+','RCL 11','RCL 12','RTN')
a('LBL 28','"WANING"','STO 43','RTN','LBL 22','"S"','STO 43','RTN','LBL 27','"W"','STO 43','RTN')
a('LBL 60','RCL 40',GX,'RCL 45','XEQ "PDM"',
  '"N"','STO 43','RCL 46','X<0?','XEQ 22','RCL 40',DX,'RCL 43','XEQ "PTXB"','RCL 40',DX,'RCL 46','ABS','XEQ "PDM"',
  'RCL 40',HX,'RCL 96','XEQ "PDM"','RCL 40',ZX,'RCL 97','XEQ "PZN"','RCL 96','X<0?','XEQ 64','11','STO- 40','RTN')
a('LBL 64','RCL 40','1','-',HX,'54','XEQ "PHL"','RTN')
a('LBL 61','RCL 40','4','"("','XEQ "PTXB"','RCL 40','34','"MOON"','XEQ "PTXB"','XEQ 60','1','STO+ 41','RTN')
a('LBL 63','RCL 42','IP','70','+','STO 43','RCL 40','4','XEQ IND 43','XEQ "PTXB"','RCL 42','IP','81','+','STO 43','RCL 40','34','XEQ IND 43','XEQ "PTXB"','XEQ 60','1','STO+ 41','RTN')
for lab,t in ((71,'<'),(72,'>'),(73,'='),(74,'?'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%t,'RTN')
a('END')
open('/home/claude/ALMF.txt','w').write('\n'.join(P)+'\n'); print(len(P))
