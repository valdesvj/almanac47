def gen(name, info, nstars=5):
    P=[]
    def a(*xs):
        for x in xs: P.extend(str(x).split('\n'))
    def t(y,x,s): a(y,x,'"%s"'%s,'XEQ "PTXT"')
    a('LBL "%s"'%name,'STO 92','R↓','STO 91','R↓','STO 90','CLLCD')
    a('16','20','376','XEQ "PHL"')
    a('18.21603','STO 86','LBL 50','RCL 86','IP','18','PIXEL','ISG 86','GTO 50')
    for c in (20,51,82,113,145,176,207,238,270,301,332,363,395):
        for y in (15,14,13): a(y,c,'PIXEL')
    for y in (83,150,216):
        for x in (15,16,17): a(y,x,'PIXEL')
    for yb,v in ((81,30),(148,60),(214,90)): a(yb,2,v,'XEQ "PTNS"')
    xs=(19,112,206,300,394)
    a('0','STO 44','RCL 91','X<0?','GTO 38')
    for x,l in zip(xs,'NESWN'): t(7,x,l)
    a('GTO 37','LBL 38','180','STO 44')
    for x,l in zip(xs,'SWNES'): t(7,x,l)
    a('LBL 37','RCL 90','XEQ "SUNA"',
      '%d'%(6+nstars),'ENTER','3','NEWMAT','STO "HZT"','0','STO 10',
      '0','STO 86','LBL 53','0','RCL 86','XEQ 52','RCL 96','X≥0?','XEQ 55','2','STO+ 86','358','RCL 86','X≤Y?','GTO 53',
      # Sun
      'RCL 77','RCL 81','XEQ 52','RCL 96','X>0?','XEQ 46',
      # Moon
      'XEQ "MOO2"','XEQ 52','RCL 96','X>0?','XEQ 47',
      # planets 1-4
      '1.004','STO 11','LBL 45','RCL 11','IP','XEQ "PLN2"','XEQ 52','RCL 96','X>0?','XEQ 48','ISG 11','GTO 45',
      # brightest stars above the horizon
      '1.058','STO 11','0','STO 12','LBL 44','RCL 11','IP','XEQ "SBRT"','STO 82','XEQ "STR2"','XEQ 52',
      '10','RCL 96','X>Y?','XEQ 43','%d'%nstars,'RCL 12','X≥Y?','GTO 42','ISG 11','GTO 44','LBL 42')
    if info:
        a('RCL 10','X=0?','RTN','1','STO 42',
          'LBL 35','INDEX "HZT"','RCL 42','1','STOIJ','RCLEL','J+','STO 13','RCLEL','J+','STO 97','RCLEL','STO 96',
          '228','0','CLLCDxy',
          'RCL 13','X=0?','GTO 31','X<0?','GTO 32',
          'RCL 13','XEQ "SNMU"','STO 14','234','2','RCL 13','XEQ "PTNS"','" "','XEQ "PTXT"','RCL 14','XEQ "PTXT"','GTO 30',
          'LBL 32','RCL 13','CHS','80','+','STO 14','234','2','XEQ IND 14','XEQ "PTXT"','GTO 30',
          'LBL 31','234','2','"SUN"','XEQ "PTXT"',
          'LBL 30','" ZN "','XEQ "PTXT"','RCL 97','XEQ "PT1"','" HC "','XEQ "PTXT"','RCL 96','XEQ "PT1"',
          'PAUSE 30','1','STO+ 42','RCL 10','RCL 42','X>Y?','RTN','GTO 35')
    else:
        a('3','STO 37','LBL 21','PAUSE 99','DSE 37','GTO 21','RTN')
    # record object: X = id (0 Sun, -1 Moon, -2..-5 planets, n star) with Zn R97 and Hc R96
    a('LBL 40','STO 13','1','STO+ 10','INDEX "HZT"','RCL 10','1','STOIJ','RCL 13','STOEL','J+','RCL 97','STOEL','J+','RCL 96','STOEL','RTN')
    a('LBL 46','XEQ 56','0','XEQ 40','RTN')
    a('LBL 47','241','RCL- 99','3','-','RCL 98','3','-','"("','XEQ "PTXB"','-1','XEQ 40','RTN')
    a('LBL 48','RCL 11','IP','70','+','STO 14','241','RCL- 99','3','-','RCL 98','3','-','XEQ IND 14','XEQ "PTXB"',
      'RCL 11','IP','1','+','CHS','XEQ 40','RTN')
    a('LBL 43','XEQ 57','RCL 82','XEQ 40','1','STO+ 12','RTN')
    for lab,s in ((71,'<'),(72,'>'),(73,'='),(74,'?')): a('LBL %d'%lab,'"%s"'%s,'RTN')
    for lab,s in ((81,'MOON'),(82,'VENUS'),(83,'MARS'),(84,'JUPITER'),(85,'SATURN')): a('LBL %d'%lab,'"%s"'%s,'RTN')
    a('LBL 55','241','RCL- 99','RCL 98','PIXEL','RTN')
    a('LBL 52','XEQ "HCZ"','RCL 97','RCL+ 44','360','MOD','375','×','360','÷','20','+','IP','STO 98',
      '225','RCL 96','200','×','90','÷','-','IP','STO 99','RTN')
    a('LBL 56','238','RCL- 99','RCL 98','5','-','"@"','XEQ "PTXB"','RTN')
    a('LBL 57','241','RCL- 99','3','-','RCL 98','3','-','"*"','XEQ "PTXB"',
      'RCL 98','5','+','STO 36','385','RCL 36','X>Y?','XEQ 39',
      '239','RCL- 99','RCL 36','RCL 82','XEQ "PTNS"','RTN',
      'LBL 39','17','STO- 36','RTN')
    a('END')
    open('/home/claude/%s.txt'%name,'w').write('\n'.join(P)+'\n')
    return len(P)
print(gen('HORZ',True), gen('HORZS',False))
