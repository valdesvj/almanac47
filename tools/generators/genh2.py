import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HS = 196                                   # sine scale: pixels for sin(Hc) = 1 (horizon y 16, zenith y 212)
def gen(name, info, rows=10):
    P=[]
    def a(*xs):
        for x in xs: P.extend(str(x).split('\n'))
    def t(y,x,s): a(y,x,'"%s"'%s,'XEQ "PTXT"')
    a('LBL "%s"'%name,'STO 92','R↓','STO 91','R↓','STO 90','XEQ "HCZI"','CLLCD')
    a('16','20','376','XEQ "PHLS"')
    a('18.21203','STO 86','LBL 50','RCL 86','IP','18','PIXEL','ISG 86','GTO 50')
    for c in (20,51,82,113,145,176,207,238,270,301,332,363,395):
        for y in (15,14,13): a(y,c,'PIXEL')
    for v in (10,20,30,45,60,90):                  # altitude marks, sine scale
        y=16+int(HS*math.sin(math.radians(v)))
        for x in (15,16,17): a(y,x,'PIXEL')
        a(y-2,2,v,'XEQ "PTNS"')
    xs=(19,112,206,300,394)
    a('0','STO 44','RCL 91','X<0?','GTO 38')
    for x,l in zip(xs,'NESWN'): t(7,x,l)
    a('GTO 37','LBL 38','180','STO 44')
    for x,l in zip(xs,'SWNES'): t(7,x,l)
    a('LBL 37','RCL 90','XEQ "SUNA"',
      '%d'%rows,'ENTER','3','NEWMAT','STO "HZT"','0','STO 10',
      '0','2','XEQ "HCZQ"','0','STO 86','LBL 53','XEQ 51','RCL 96','1E-4','X<Y?','XEQ 55','2','STO+ 86','358','RCL 86','X≤Y?','GTO 53',
      # Sun: always in the list (as ALMF, HALMV, ALMT), drawn only above the horizon
      'RCL 77','RCL 81','XEQ 52','RCL 96','X>0?','XEQ 56','0','XEQ 40',
      # Moon
      'XEQ "MOO2"','XEQ 52','RCL 96','X>0?','XEQ 47',
      # planets 1-4
      '1.004','STO 11','LBL 45','RCL 11','IP','XEQ "PLN3"','XEQ 52','RCL 96','X>0?','XEQ 48','ISG 11','GTO 45',
      # brightest stars higher than 10 deg until the list has 10 bodies (same rule as ALMF)
      '1.058','STO 11','LBL 44','%d'%rows,'RCL 10','X≥Y?','GTO 42','RCL 11','IP','XEQ "SBRT"','STO 82','XEQ "SQK"','0.15643','X>Y?','GTO 36','XEQ "STR2"','XEQ 52',
      '10','RCL 96','X>Y?','XEQ 43','LBL 36','ISG 11','GTO 44','LBL 42')
    a('"S"','STO 15','FS? 11','XEQ 29','FS? 12','XEQ 65','7','2','RCL 15','XEQ "PTXT"')   # T = tables, S = series (bottom left)
    if info:
        a('RCL 10','X=0?','RTN','1','STO 42',
          'LBL 35','INDEX "HZT"','RCL 42','1','STOIJ','RCLEL','J+','STO 13','RCLEL','J+','STO 97','RCLEL','STO 96',
          '224','0','CLLCDxy',
          'RCL 13','X=0?','GTO 31','X<0?','GTO 32',
          'RCL 13','XEQ "SNMU"','STO 14','227','2','RCL 13','XEQ "PINS"','" "','XEQ "PTXS"','RCL 14','XEQ "PTXS"','GTO 30',
          'LBL 32','RCL 13','CHS','80','+','STO 14','227','2','XEQ IND 14','XEQ "PTXS"','GTO 30',
          'LBL 31','227','2','"SUN"','XEQ "PTXS"',
          'LBL 30','"  ZN "','XEQ "PTXS"','RCL 97','XEQ "PF1S"','"  HC "','XEQ "PTXS"','RCL 96','X<0?','XEQ 33','XEQ "PF1S"',
          'PAUSE 30','1','STO+ 42','RCL 10','RCL 42','X>Y?','XEQ 34','GTO 35',     # endless: after the last, the first again
          'LBL 34','1','STO 42','RTN',
          'LBL 33','R↓','"-"','XEQ "PTXS"','RCL 96','RTN')                         # minus sign (Sun below the horizon)
    else:
        a('3','STO 37','LBL 21','PAUSE 99','DSE 37','GTO 21','RTN')
    # record object: X = id (0 Sun, -1 Moon, -2..-5 planets, n star) with Zn R97 and Hc R96
    a('LBL 29','"T"','STO 15','RTN','LBL 65','"X"','STO 15','RTN')
    a('LBL 40','STO 13','1','STO+ 10','INDEX "HZT"','RCL 10','1','STOIJ','RCL 13','STOEL','J+','RCL 97','STOEL','J+','RCL 96','STOEL','RTN')
    a('LBL 47','241','RCL- 99','6','-','RCL 98','6','-','"("','XEQ "PTXS"','-1','XEQ 40','RTN')
    a('LBL 48','RCL 11','IP','70','+','STO 14','241','RCL- 99','6','-','RCL 98','6','-','XEQ IND 14','XEQ "PTXS"',
      'RCL 11','IP','1','+','CHS','XEQ 40','RTN')
    a('LBL 43','XEQ 57','RCL 82','XEQ 40','RTN')
    for lab,s in ((71,'<'),(72,'>'),(73,'='),(74,'?')): a('LBL %d'%lab,'"%s"'%s,'RTN')
    for lab,s in ((81,'MOON'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%s,'RTN')
    a('LBL 55','241','RCL- 99','RCL 98','PIXEL','RTN')
    a('LBL 51','XEQ "HCZR"','GTO 49')
    a('LBL 52','XEQ "HCZ"','LBL 49','RCL 97','RCL+ 44','360','MOD','375','×','360','÷','20','+','IP','STO 98',
      '225','RCL "SHC"',HS,'×','-','IP','STO 99','RTN')
    a('LBL 56','241','RCL- 99','6','-','RCL 98','6','-','"@"','XEQ "PTXS"','RTN')
    a('LBL 57','241','RCL- 99','6','-','RCL 98','6','-','"*"','XEQ "PTXS"',
      'RCL 98','8','+','STO 36','380','RCL 36','X>Y?','XEQ 39',
      '241','RCL- 99','6','-','RCL 36','RCL 82','XEQ "PINS"','RTN',
      'LBL 39','32','STO- 36','RTN')
    a('END')
    open(os.path.join(ROOT,'programs','%s.txt'%name),'w').write('\n'.join(P)+'\n')
    return len(P)
print(gen('HORZ',True), gen('HORZS',False))
