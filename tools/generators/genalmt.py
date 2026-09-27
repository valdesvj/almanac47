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
a('RCL 10','STO 90','RCL 11','STO 91','RCL 12','STO 92')
a('RCL 10','XEQ "SUNA"','STO 45','R↓','STO 46','R↓','STO 48','RCL 73','15.99383','X<>Y','÷','STO 29')
a('XEQ "PHA2"','STO 18','X<>Y','STO 19')          # Moon phase from the SUNA just run
a('10','ENTER','5','NEWMAT','STO "ALT"','0','STO 41')
# Sun (always)
a('RCL 46','RCL 45','XEQ "HCZ"','0','XEQ 40')
# Moon if above the horizon
a('XEQ "MOO2"','STO 45','R↓','STO 46','R↓','STO 21','R↓','STO 22','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 41')
# planets above the horizon
a('1.004','STO 42','LBL 16','RCL 42','IP','XEQ "PLN3"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"','RCL 96','X>0?','XEQ 42','ISG 42','GTO 16')
# brightest stars higher than 10 deg until 10 bodies
a('1.058','STO 42','LBL 17','10','RCL 41','X≥Y?','GTO 19','RCL 42','IP','XEQ "SBRT"','STO 82','XEQ "STR2"','STO 45','X<>Y','STO 46','RCL 46','RCL 45','XEQ "HCZ"',
  '10','RCL 96','X≤Y?','GTO 18','RCL 82','XEQ 40','LBL 18','ISG 42','GTO 17','LBL 19')
# ---------------- text pages: two lines per R/S in the C47 standard (proportional) font.
# PROMPT wraps at a space when the next word does not fit in 400 pixels, so line 1 is
# padded with spaces (8 px) until one more would not fit: line 2 then starts at the left
# edge. R43 = pixel width of the current line; columns are placed by pixels too.
# Widths (C47 standard font): space, digits, - / ' ° * 8 px; . : 5 px; % 13 px; letters
# 6-12 px (table in program CWID for the star names).
import json as _j
WID=_j.load(open('/tmp/cmp/stdwidth.json'))
def pxw(t): return sum(WID[c] for c in t)
def lit(t): a('"%s"'%t,'XEQ 90',str(pxw(t)),'STO+ 43')      # literal text
def num(f, corr=-3): a(f[1:].split('|')); a(str(corr),'XEQ 76')  # formatted number: 8 px per char + corr
def rjn(f, w, corr=-3): a(f[1:].split('|')); a(str(w),'XEQ 94'); a(str(corr),'XEQ 76')   # right-aligned in w chars
def pad(px): a(str(px),'XEQ 89')                     # spaces up to px pixels
def newline(): a('0','STO 43')                       # line 2: width counter from 0
def first(t): a('"%s"'%t,'STO 20',str(pxw(t)),'STO 43')   # page starts with literal text
def tm(reg): num(fmt(reg,'SHM'))                     # hh:mm or --:-- (both 37 px)
BRK=400                                              # PROMPT line width
a('LBL 01')
# page 1: date, UT, DR  |  GHA Aries, T/S
a('RCL 10','XEQ "SDAT"','STO 20','80','STO 43'); lit(' '); num(fmt('10|0.5|+|1|MOD|24|×','SHM'))
lit(' UT  DR '); a('RCL 11','XEQ 77'); num(fmt(11,'SNS'),'RCL 47'); lit('  '); a('RCL 12','XEQ 79'); num(fmt(12,'SEW'),'RCL 47'); pad(BRK)
newline(); lit('ARIES '); num(fmt(48,'SDM')); pad(390); a('"S"','FS? 11','XEQ 29','FS? 12','XEQ 65','XEQ 90','XEQ 91')   # T = tables, S = series
# one page per body: name, HC, ZN  |  GHA, DEC (columns placed by pixels)
a('1','STO 24','LBL 02','INDEX "ALT"','RCL 24','1','STOIJ','RCLEL','J+','STO 25','RCLEL','J+','STO 45','RCLEL','J+','STO 46','RCLEL','J+','STO 96','RCLEL','STO 97')
a('RCL 25','XEQ 70','XEQ 68','RCL 96','X<0?','XEQ 92'); pad(136); lit('HC'); rjn(fmt(96,'SDM'),10); lit('  ZN  '); num(fmt(97,'SZN')); pad(BRK)
newline(); pad(125); lit('GHA'); rjn(fmt(45,'SDM'),10); lit('  DEC '); a('"N"','STO 26','RCL 46','X<0?','XEQ 99','RCL 26','XEQ 90'); rjn(fmt('46|ABS','SDM'),9); a('XEQ 91')
a('1','STO+ 24','RCL 41','RCL 24','X≤Y?','GTO 02')
# Sun: twilight, rise/set  |  meridian passage, SD
first('NAUT TWI '); tm(13); lit(' '); tm(17); pad(180); lit('RISE/SET '); tm(14); lit(' '); tm(16); pad(BRK)
newline(); lit('MER PASS '); tm(15); pad(180); lit('SUN SD '); num(fmt(29,'SF1')); lit("'"); a('XEQ 91')
# Moon: %, phase, age  |  HP, SD
first('MOON '); num(fmt(18,'SINT'),0); lit('% ')
a('"WAXING"','STO 26','RCL 19','14.765','X<Y?','XEQ 27','RCL 18','99.5','X≤Y?','XEQ 20','RCL 18','0.5','X>Y?','XEQ 21','RCL 26','XEQ 86')
pad(180); lit('AGE '); num(fmt(19,'SF1')); lit(' DAYS'); pad(BRK)
newline(); lit('MOON HP '); num(fmt(21,'SF1')); lit("'"); pad(180); lit('MOON SD '); num(fmt(22,'SF1')); lit("'"); a('XEQ 91')
# warning: 3 spaces + text + 4 spaces = 44 characters (small font)
s('   DOES NOT REPLACE THE NAUTICAL ALMANAC    '); a('STO 20','XEQ 91')
a('GTO 01')
# ---------------- subroutines
a('LBL 26','RCL 10','0.5','-','IP','0.5','+','RCL 11','RCL 12','RTN')
a('LBL 27','"WANING"','STO 26','RTN')
a('LBL 29','"T"','RTN','LBL 65','"X"','RTN')
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
a('LBL 76','STO+ 43','R↓','STO 27','αLENG 27','8','×','STO+ 43','RCL 27','XEQ 90','RTN')     # append Y, width 8*len + X
a('LBL 77','X<0?','GTO 78','0','STO 47','RTN','LBL 78','-1','STO 47','RTN')                  # SNS: N -3+3, S -3+2
a('LBL 79','X<0?','GTO 72','-1','STO 47','RTN','LBL 72','1','STO 47','RTN')                  # SEW: E -3+2, W -3+4
a('LBL 86','STO 27','STO 44','LBL 87','αLENG 44','X=0?','GTO 88','α→𝑥 44','XEQ "CWID"','STO+ 43','GTO 87',
  'LBL 88','RCL 27','XEQ 90','RTN')                                                             # append X, measured with CWID
a('LBL 89','STO 28','LBL 73','RCL 43','8','+','RCL 28','X<Y?','RTN','" "','XEQ 90','8','STO+ 43','GTO 73')   # pad to X pixels
a('LBL 68','STO 20','STO 44','0','STO 43','LBL 67','αLENG 44','X=0?','RTN','α→𝑥 44','XEQ "CWID"','STO+ 43','GTO 67')   # line = X, measured with CWID
a('LBL 94','STO 28','R↓','STO 27','LBL 97','αLENG 27','RCL 28','X≤Y?','GTO 98',          # Y right-aligned in X characters
  '" "','RCL 27','+','STO 27','GTO 97','LBL 98','RCL 27','RTN')
a('LBL 92','"* "','RCL 20','+','STO 20','16','STO+ 43','RTN')                                  # mark: below the horizon
a('END')
open('/home/claude/ALMT.txt','w').write('\n'.join(P)+'\n'); print(len(P))
