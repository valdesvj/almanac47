P=[]
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y,x,s): a(y,x,'"%s"'%s,'XEQ "PTXB"')
def num(y,x,reg,fn,pre=''):
    a(y,x,'RCL %s'%reg)
    if pre: a(pre)
    a('XEQ "%s"'%fn)
X0=206
a('LBL "HALMV"','STO 12','R↓','STO 11','R↓','STO 10')
# events first (SUNRISE uses R90-99); Moon phase (PHA2) right after SUNA
for reg,lab in ((13,'NTWA'),(14,'RISE'),(15,'TRAN'),(16,'SET'),(17,'NTWP')):
    a('XEQ 26','XEQ "%s"'%lab,'STO %d'%reg)
a('RCL 10','STO 90','RCL 11','STO 91','RCL 12','STO 92','XEQ "HCZI"','CLLCD')
# divider
a('0','-201','PIXEL')
# horizon line y=14, x 18..196
a('14','18','179','XEQ "PHL"')
# vertical axis x=17
a('14.214','STO 47','LBL 12','RCL 47','IP','17','PIXEL','ISG 47','GTO 12')
for y in (80,147,214): a(y,15,'PIXEL',y,16,'PIXEL')
for y,v in ((77,30),(144,60),(211,90)): a(y,2,v,'XEQ "PINB"')
xs=[16,60,105,149,192]
a('0','STO 44','RCL 11','X<0?','GTO 23')
for x,l in zip(xs,'NESWN'): txt(3,x,l)
a('GTO 24','LBL 23','180','STO 44')
for x,l in zip(xs,'SWNES'): txt(3,x,l)
a('LBL 24')
# sun
a('RCL 10','XEQ "SUNA"','STO 45','R↓','STO 46','R↓','STO 48','RCL 73','15.99383','X<>Y','÷','STO 29')
a('XEQ "PHA2"','STO 18','X<>Y','STO 19')          # Moon phase from the SUNA just run
# equator
a('0','3','XEQ "HCZQ"','0','STO 47','LBL 14','XEQ 51','RCL 96','1E-4','X<Y?','XEQ 15','3','STO+ 47','357','RCL 47','X≤Y?','GTO 14')
# right side header lines
txt(230,X0,'DR')
a('"N"','STO 43','RCL 11','X<0?','XEQ 22'); a(230,X0+18,'RCL 43','XEQ "PTXB"'); a(230,X0+18,'RCL 11','ABS','XEQ "PDM"')
a('"E"','STO 43','RCL 12','X<0?','XEQ 27'); a(230,X0+78,'RCL 43','XEQ "PTXB"'); a(230,X0+84,'RCL 12','ABS','XEQ "PDM"')
num(220,X0,10,'PDAT'); a(220,X0+66,'RCL 10','0.5','+','1','MOD','24','×','XEQ "PHM"'); txt(220,X0+102,'UT')
txt(210,X0,'ARIES'); num(210,X0+36,48,'PDM'); txt(210,X0+102,'SUN SD'); num(210,X0+144,29,'PF1')
txt(200,X0,'SUN GHA'); num(200,X0+48,45,'PDM')
a('"N"','STO 43','RCL 46','X<0?','XEQ 22'); a(200,X0+108,'RCL 43','XEQ "PTXB"'); a(200,X0+108,'RCL 46','ABS','XEQ "PDM"')
txt(188,X0+30,'BODY'); txt(188,X0+132,'HC'); txt(188,X0+168,'ZN')
a('178','STO 40')
a('RCL 46','RCL 45','XEQ 52','RCL 96','X>0?','XEQ 16')
a('RCL 40',X0,'"@"','XEQ "PTXB"','RCL 40',X0+30,'"SUN"','XEQ "PTXB"','XEQ 60')
a('1','STO 41')
# Moon, if above the horizon
a('XEQ "MOO2"','STO 45','R↓','STO 46','R↓','STO 21','R↓','STO 22','RCL 46','RCL 45','XEQ 52','RCL 96','X>0?','XEQ 61')
# planets above the horizon
a('1.004','STO 42','LBL 62','RCL 42','IP','XEQ "PLN3"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ 52','RCL 96','X>0?','XEQ 63','ISG 42','GTO 62')
# brightest stars higher than 10 deg until the table has 10 rows
a('1.058','STO 42','LBL 17','10','RCL 41','X≥Y?','GTO 19','RCL 42','IP','XEQ "SBRT"','STO 82','XEQ "SQK"','0.15643','X>Y?','GTO 18','XEQ "STR2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ 52',
  '10','RCL 96','X≤Y?','GTO 18',
  'XEQ 57','RCL 40',X0,'"*"','XEQ "PTXB"','RCL 40',X0+12,'RCL 82','XEQ "PINB"',
  'RCL 82','XEQ "SNMU"','STO 43','RCL 40',X0+30,'RCL 43','XEQ "PTXB"','XEQ 60',
  '1','STO+ 41','LBL 18','ISG 42','GTO 17','LBL 19')
# events
def hline(y):
    a(y,'204','196','XEQ "PHL"')
hline(86)
txt(76,X0,'SUN UT'); txt(76,X0+93,'AM'); txt(76,X0+135,'PM')
txt(66,X0,'NAUT TWI'); num(66,X0+84,13,'PHM'); num(66,X0+126,17,'PHM')
txt(56,X0,'RISE/SET'); num(56,X0+84,14,'PHM'); num(56,X0+126,16,'PHM')
txt(46,X0,'MER PASS'); num(46,X0+105,15,'PHM')
hline(39)
a('"WAXING"','STO 43','RCL 19','14.765','X<Y?','XEQ 28','RCL 18','99.5','X≤Y?','XEQ 25','RCL 18','0.5','X>Y?','XEQ 30')
a(29,X0,'"MOON "','XEQ "PTXB"','RCL 18','XEQ "PINB"','"% "','XEQ "PTXB"','RCL 43','XEQ "PTXB"','" AGE "','XEQ "PTXB"','RCL 19','XEQ "PF1"')
a(19,X0,'"MOON HP "','XEQ "PTXB"','RCL 21','XEQ "PF1"','" SD "','XEQ "PTXB"','RCL 22','XEQ "PF1"')
a(8,X0+24,'"DOES NOT REPLACE THE NAUTICAL ALMANAC"','XEQ "PTXT"')
a('"S"','STO 43','FS? 11','XEQ 29','FS? 12','XEQ 65',8,392,'RCL 43','XEQ "PTXT"')   # T = tables, S = series
a('3','STO 37','LBL 20','PAUSE 99','DSE 37','GTO 20','RTN')
# subroutines
a('LBL 26','RCL 10','0.5','-','IP','0.5','+','RCL 11','RCL 12','RTN')
a('LBL 29','"T"','STO 43','RTN','LBL 65','"X"','STO 43','RTN')
a('LBL 25','"FULL"','STO 43','RTN','LBL 30','"NEW"','STO 43','RTN')
a('LBL 28','"WANING"','STO 43','RTN','LBL 22','"S"','STO 43','RTN','LBL 27','"W"','STO 43','RTN')
a('LBL 15','RCL 99','RCL 98','PIXEL','RTN')
a('LBL 16','RCL 99','3','-','RCL 98','5','-','"@"','XEQ "PTXB"','RTN')
a('LBL 51','XEQ "HCZR"','GTO 49')
a('LBL 52','XEQ "HCZ"','LBL 49','RCL 97','RCL+ 44','360','MOD','178','×','360','÷','18','+','IP','STO 98',
  'RCL 96','200','×','90','÷','14','+','IP','STO 99','RTN')
a('LBL 57','RCL 99','3','-','RCL 98','3','-','"*"','XEQ "PTXB"','RCL 98','6','+','STO 43','187','RCL 43','X>Y?','XEQ 21',
  'RCL 99','3','-','RCL 43','RCL 82','XEQ "PINB"','RTN','LBL 21','22','STO- 43','RTN')
a('LBL 60','RCL 40',X0+90,'RCL 96','XEQ "PDM"','RCL 40',X0+150,'RCL 97','XEQ "PZN"','RCL 96','X<0?','XEQ 64','10','STO- 40','RTN')
a('LBL 64','RCL 40','1','-',X0+90,'54','XEQ "PHL"','RTN')
a('LBL 61','RCL 99','3','-','RCL 98','3','-','"("','XEQ "PTXB"','RCL 40',X0,'"("','XEQ "PTXB"','RCL 40',X0+30,'"MOON"','XEQ "PTXB"','XEQ 60','1','STO+ 41','RTN')
a('LBL 63','RCL 42','IP','70','+','STO 43','RCL 99','3','-','RCL 98','3','-','XEQ IND 43','XEQ "PTXB"',
  'RCL 40',X0,'XEQ IND 43','XEQ "PTXB"','RCL 42','IP','81','+','STO 43','RCL 40',X0+30,'XEQ IND 43','XEQ "PTXB"','XEQ 60','1','STO+ 41','RTN')
for lab,t in ((71,'<'),(72,'>'),(73,'='),(74,'?'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%t,'RTN')
a('END')
open('/home/claude/HALMV.txt','w').write('\n'.join(P)+'\n')
print(len(P))
