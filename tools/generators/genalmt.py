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
# ---------------- text pages: two lines per R/S (line 1 padded to 44 characters, the
# width of one line of the C47 small font), laid out like the ALMF page; starts over
# after the last page (EXIT to stop)
def col(c): a(str(c),'XEQ 95')                    # pad the page R20 with spaces to column c
def rj(f, w): a(f[1:].split('|')); a(str(w),'XEQ 94','XEQ 90')   # value right-aligned in w characters
BAR='-'*22
def bar(): app(BAR, BAR)                          # 44 x '-'
L2=44                                             # line 2 starts at column 44
a('LBL 01')
# page 1: date, UT, DR  |  GHA Aries, T/S at the right end
a(fmt(10,'SDAT')[1:].split('|')); a('STO 20'); app(' ',fmt('10|0.5|+|1|MOD|24|×','SHM'),'UT DR ',fmt(11,'SNS'),' ',fmt(12,'SEW'))
col(L2); app('ARIES ',fmt(48,'SDM')); col(L2+43); a('"S"','FS? 11','XEQ 29','XEQ 90','XEQ 91')   # T = tables, S = series
# one page per body: name, Hc, Zn  |  GHA, Dec (values aligned in columns)
a('1','STO 24','LBL 02','INDEX "ALT"','RCL 24','1','STOIJ','RCLEL','J+','STO 25','RCLEL','J+','STO 45','RCLEL','J+','STO 46','RCLEL','J+','STO 96','RCLEL','STO 97')
a('RCL 25','XEQ 70','STO 20','RCL 96','X<0?','XEQ 92'); col(13); app(' HC'); rj(fmt(96,'SDM'),10); app('  ZN  ',fmt(97,'SZN'))
col(L2+13); app('GHA'); rj(fmt(45,'SDM'),10); app('  DEC '); a('"N"','STO 26','RCL 46','X<0?','XEQ 99','RCL 26','XEQ 90'); rj(fmt('46|ABS','SDM'),9); a('XEQ 91')
a('1','STO+ 24','RCL 41','RCL 24','X≤Y?','GTO 02')
# Sun: twilight, rise/set  |  meridian passage, SD
s('NAUT TWI '); a('STO 20'); app(fmt(13,'SHM'),' ',fmt(17,'SHM')); col(22); app('RISE/SET ',fmt(14,'SHM'),' ',fmt(16,'SHM'))
col(L2); app('MER PASS ',fmt(15,'SHM')); col(L2+22); app('SUN SD ',fmt(29,'SF1'),"'"); a('XEQ 91')
# Moon: %, phase, age  |  HP, SD
s('MOON '); a('STO 20'); app(fmt(18,'SINT'),'% ')
a('"WAXING"','STO 26','RCL 19','14.765','X<Y?','XEQ 27','RCL 18','99.5','X≤Y?','XEQ 20','RCL 18','0.5','X>Y?','XEQ 21','RCL 26','XEQ 90')
col(22); app('AGE ',fmt(19,'SF1'),' DAYS'); col(L2); app('MOON HP ',fmt(21,'SF1'),"'"); col(L2+22); app('MOON SD ',fmt(22,'SF1'),"'"); a('XEQ 91')
# warning, centred in 44 characters (small font)
s('   DOES NOT REPLACE THE NAUTICAL ALMANAC'); a('STO 20'); col(L2); a('XEQ 91')
a('GTO 01')
# ---------------- subroutines
a('LBL 26','RCL 10','0.5','-','IP','0.5','+','RCL 11','RCL 12','RTN')
a('LBL 27','"WANING"','STO 26','RTN')
a('LBL 29','"T"','RTN')
a('LBL 20','"FULL"','STO 26','RTN','LBL 21','"NEW"','STO 26','RTN')
a('LBL 40','STO 25','1','STO+ 41','INDEX "ALT"','RCL 41','1','STOIJ','RCL 25','STOEL','J+','RCL 45','STOEL','J+','RCL 46','STOEL','J+','RCL 96','STOEL','J+','RCL 97','STOEL','RTN')
a('LBL 41','-1','XEQ 40','RTN')
a('LBL 42','RCL 42','IP','1','+','CHS','XEQ 40','RTN')
# name of body id X: 0 Sun, -1 Moon, -2..-5 planets, n star
a('LBL 70','X>0?','GTO 71','CHS','80','+','STO 23','XEQ IND 23','RTN',
  'LBL 71','STO 23','XEQ "SNMU"','STO 26','RCL 23','XEQ "SINT"','" "','+','RCL 26','+','RTN')
for lab,t in ((80,'SUN'),(81,'MOON'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%t,'RTN')
a('LBL 90','STO 23','RCL 20','RCL 23','+','STO 20','RTN')      # append X to the line R20
a('LBL 91','PROMPT 20','RTN')
a('LBL 99','"S"','STO 26','RTN')
a('LBL 95','STO 28','LBL 96','αLENG 20','RCL 28','X≤Y?','RTN','" "','XEQ 90','GTO 96')   # pad R20 to column X
a('LBL 94','STO 28','R↓','STO 27','LBL 97','αLENG 27','RCL 28','X≤Y?','GTO 98',          # Y right-aligned in X characters
  '" "','RCL 27','+','STO 27','GTO 97','LBL 98','RCL 27','RTN')
a('LBL 92','"* "','RCL 20','+','STO 20','RTN')                                  # mark: below the horizon                                    # show line, wait for R/S
a('END')
open('/home/claude/ALMT.txt','w').write('\n'.join(P)+'\n'); print(len(P))
