P=[]
def a(*xs):
    for x in xs:
        if isinstance(x,list): P.extend(x)
        else: P.extend(str(x).split('\n'))
def s(t): a('"%s"'%t)
def app(*items):       # append pieces to the line in R20
    for it in items:
        if isinstance(it,str) and it.startswith('~'): a(it[1:].split('|'))   # raw steps producing a string in X
        else: a('"%s"'%it)
        a('XEQ 90')
def fmt(reg,fn): return '~RCL %s|XEQ "%s"'%(reg,fn)
a('LBL "ALMT"','STO 12','R↓','STO 11','R↓','STO 10')
for reg,lab in ((13,'NTWA'),(14,'RISE'),(15,'TRAN'),(16,'SET'),(17,'NTWP')):
    a('XEQ 26','XEQ "%s"'%lab,'STO %d'%reg)
a('RCL 10','XEQ "PHAS"','STO 18','X<>Y','STO 19')
a('RCL 10','STO 90','RCL 11','STO 91','RCL 12','STO 92')
a('RCL 10','XEQ "SUNA"','STO 45','R↓','STO 46','R↓','STO 48','RCL 73','15.99383','X<>Y','÷','STO 29')
a('10','ENTER','5','NEWMAT','STO "ALT"','0','STO 41')
# Sun (always)
a('RCL 46','RCL 45','XEQ "HCZ"','0','XEQ 40')
# Moon if above the horizon
a('XEQ "MOO2"','STO 45','R↓','STO 46','R↓','STO 21','R↓','STO 22','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 41')
# planets above the horizon
a('1.004','STO 42','LBL 16','RCL 42','IP','XEQ "PLN2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 42','ISG 42','GTO 16')
# brightest stars higher than 10 deg until 10 bodies
a('1.058','STO 42','LBL 17','10','RCL 41','X≥Y?','GTO 19','RCL 42','IP','XEQ "SBRT"','STO 82','XEQ "STR2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"',
  '10','RCL 96','X≤Y?','GTO 18','RCL 82','XEQ 40','LBL 18','ISG 42','GTO 17','LBL 19')
# ---------------- text pages, one line per R/S, then start over (EXIT to stop)
a('LBL 01')
a(fmt(10,'SDAT')[1:].split('|')); a('STO 20'); app('  ',fmt('10|0.5|+|1|MOD|24|×','SHM'),' UT'); a('XEQ 91')
s('DR '); a('STO 20'); app(fmt(11,'SNS'),'  ',fmt(12,'SEW')); a('XEQ 91')
s('GHA ARIES '); a('STO 20'); app(fmt(48,'SDM')); a('XEQ 91')
# bodies
a('1','STO 24','LBL 02','INDEX "ALT"','RCL 24','1','STOIJ','RCLEL','J+','STO 25','RCLEL','J+','STO 45','RCLEL','J+','STO 46','RCLEL','J+','STO 96','RCLEL','STO 97')
a('RCL 25','XEQ 70','STO 20','RCL 96','X<0?','XEQ 92'); app(' HC ',fmt(96,'SDM'),' ZN ',fmt(97,'SZN')); a('XEQ 91')
s('   GHA '); a('STO 20'); app(fmt(45,'SDM'),' DEC ',fmt(46,'SNS')); a('XEQ 91')
a('RCL 25','1','+','X≠0?','GTO 03')
s('   HP '); a('STO 20'); app(fmt(21,'SF1'),"' SD ",fmt(22,'SF1'),"'"); a('XEQ 91')
a('LBL 03','1','STO+ 24','RCL 41','RCL 24','X≤Y?','GTO 02')
# sun times, moon, SD, warning
s('NAUT TWI '); a('STO 20'); app(fmt(13,'SHM'),'  ',fmt(17,'SHM'),' UT'); a('XEQ 91')
s('SUNRISE '); a('STO 20'); app(fmt(14,'SHM'),'  SUNSET ',fmt(16,'SHM')); a('XEQ 91')
s('MER PASS '); a('STO 20'); app(fmt(15,'SHM'),' UT   SUN SD ',fmt(29,'SF1'),"'"); a('XEQ 91')
s('MOON '); a('STO 20'); app(fmt(18,'SINT'),'% '); a('"WAXING"','STO 26','RCL 19','14.765','X<Y?','XEQ 27','RCL 26','XEQ 90'); app(' AGE ',fmt(19,'SF1'),' D'); a('XEQ 91')
s('DOES NOT REPLACE THE NAUTICAL ALMANAC'); a('STO 20','XEQ 91')
a('GTO 01')
# ---------------- subroutines
a('LBL 26','RCL 10','0.5','-','IP','0.5','+','RCL 11','RCL 12','RTN')
a('LBL 27','"WANING"','STO 26','RTN')
a('LBL 40','STO 25','1','STO+ 41','INDEX "ALT"','RCL 41','1','STOIJ','RCL 25','STOEL','J+','RCL 45','STOEL','J+','RCL 46','STOEL','J+','RCL 96','STOEL','J+','RCL 97','STOEL','RTN')
a('LBL 41','-1','XEQ 40','RTN')
a('LBL 42','RCL 42','IP','1','+','CHS','XEQ 40','RTN')
# name of body id X: 0 Sun, -1 Moon, -2..-5 planets, n star
a('LBL 70','X>0?','GTO 71','CHS','80','+','STO 23','XEQ IND 23','RTN',
  'LBL 71','STO 23','XEQ "SNMU"','STO 26','RCL 23','XEQ "SINT"','" "','+','RCL 26','+','RTN')
for lab,t in ((80,'SUN'),(81,'MOON'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%t,'RTN')
a('LBL 90','STO 23','RCL 20','RCL 23','+','STO 20','RTN')      # append X to the line R20
a('LBL 91','PROMPT 20','RTN')
a('LBL 92','"* "','RCL 20','+','STO 20','RTN')                                  # mark: below the horizon                                    # show line, wait for R/S
a('END')
open('/home/claude/ALMT.txt','w').write('\n'.join(P)+'\n'); print(len(P))
