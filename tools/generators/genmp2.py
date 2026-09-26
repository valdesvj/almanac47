import json
cl0,cl1,cb0,cb1=json.load(open('mconst.json'))
cnt=json.load(open('pcounts.json'))
def f(v): return ('%.10g'%v).replace('e','E').replace('E+','E')
def horner(coefs, reg):   # coefs c0..cn, variable T in R54
    L=[f(coefs[-1])]
    for c in reversed(coefs[:-1]): L+=['RCL× 54',f(c),'+']
    return L+['STO %02d'%reg]
M=['LBL "MOON"','XEQ "SUNA"','LBL "MOO2"','DEG']
M+=horner([218.3164477,481267.88123421,-0.0015786,1/538841,-1/65194000],0)
M+=horner([297.8501921,445267.1114034,-0.0018819,1/545868,-1/113065000],1)
M+=horner([357.5291092,35999.0502909,-0.0001536,1/24490000],2)
M+=horner([134.9633964,477198.8675055,0.0087414,1/69699,-1/14712000],3)
M+=horner([93.2720950,483202.0175233,-0.0036539,-1/3526000,1/863310000],4)
M+=horner([1,-0.002516,-0.0000074],5)
for r in (0,1,2,3,4): M+=['RCL %02d'%r,'360','MOD','STO %02d'%r]
M+=['0','STO 06','STO 07','STO 08']
for name,n,s,c in (('ML',60,6,7),('MB',60,8,8),('MCL',cnt_l if False else 40,6,6),('MCB',15,8,8)):
    M+=['INDEX "%s"'%name,str(n),'STO 09',str(s),'STO 35',str(c),'STO 36','XEQ 20']
# additive terms
M+=['RCL 54','131.849','×','119.75','+','STO 39',
    'RCL 39','SIN','3958','×','RCL 00','RCL- 04','SIN','1962','×','+',
    'RCL 54','479264.29','×','53.09','+','SIN','318','×','+',
    'RCL 54',f(cl1),'×',f(cl0),'+','+','STO+ 06',
    'RCL 00','SIN','-2235','×',
    'RCL 54','481266.484','×','313.45','+','SIN','382','×','+',
    'RCL 39','RCL- 04','SIN','175','×','+',
    'RCL 39','RCL+ 04','SIN','175','×','+',
    'RCL 00','RCL- 03','SIN','127','×','+',
    'RCL 00','RCL+ 03','SIN','-115','×','+',
    'RCL 54',f(cb1),'×',f(cb0),'+','+','STO+ 08',
    # lambda, beta, distance
    'RCL 06','1E6','÷','RCL+ 00','RCL 66','3600','÷','+','STO 38',
    'RCL 08','1E6','÷','STO 39',
    'RCL 07','1000','÷','385000.56','+','STO 07',
    # declination
    'RCL 39','SIN','RCL 76','COS','×','RCL 39','COS','RCL 76','SIN','×','RCL 38','SIN','×','+','ASIN','STO 08',
    # right ascension
    'RCL 38','SIN','RCL 76','COS','×','RCL 39','TAN','RCL 76','SIN','×','-','RCL 38','COS','→POL','X<>Y',
    'RCL 80','X<>Y','-','360','+','360','MOD','STO 06',
    # HP and SD (arcmin)
    '6378.14','RCL÷ 07','ASIN','60','×','STO 05',
    '358473400','RCL÷ 07','60','÷','STO 04',
    'RCL 04','RCL 05','RCL 08','RCL 06','RTN',
    # generic loop
    'LBL 20','1','1','STOIJ',
    'LBL 21','RCLEL','J+','RCL× 01',
    'RCLEL','J+','STO 38','RCL× 02','+',
    'RCLEL','J+','RCL× 03','+',
    'RCLEL','J+','RCL× 04','+','STO 39',
    'RCL 38','ABS','RCL 05','X<>Y','Y↑X','STO 37',
    'RCLEL','J+','RCL× 37','RCL 39','SIN','×','STO+ IND 35',
    'RCLEL','J+','RCL× 37','RCL 39','COS','×','STO+ IND 36',
    'DSE 09','GTO 21','RTN','END']
open('/home/claude/MOON.txt','w').write('\n'.join(M)+'\n')
# ---------------- PLAN
P=['LBL "PLAN"','STO 09','R↓','XEQ "SUNA"','GTO 31','LBL "PLN2"','STO 09','RCL 54','10','÷','STO 50','LBL 31','RCL 50','STO 03','RAD']
for nm,reg in (('EEL',0),('EEB',1),('EER',2)):
    P+=['INDEX "%s"'%nm,str(cnt[nm]),'STO 55','XEQ "SER"','STO %02d'%reg]
P+=['0','STO 08','2','STO 07',
    'LBL 30','RCL 03','RCL 08','365250','÷','-','STO 50',
    'RCL 09','10','+','STO 39','XEQ IND 39',
    'RCL 06','RCL 05','COS','×','RCL 04','COS','×','RCL 02','RCL 01','COS','×','RCL 00','COS','×','-','STO 35',
    'RCL 06','RCL 05','COS','×','RCL 04','SIN','×','RCL 02','RCL 01','COS','×','RCL 00','SIN','×','-','STO 36',
    'RCL 06','RCL 05','SIN','×','RCL 02','RCL 01','SIN','×','-','STO 37',
    'RCL 35','X↑2','RCL 36','X↑2','+','RCL 37','X↑2','+','0.5','Y↑X','STO 34',
    '0.0057755183','×','STO 08',
    'DSE 07','GTO 30',
    'DEG',
    'RCL 36','RCL 35','→POL','STO 38','X<>Y','360','+','360','MOD','STO 39',
    'RCL 37','RCL 38','→POL','X<>Y','STO 38',
    # FK5
    'RCL 39','RCL 54','1.397','×','-','STO 35',
    'COS','RCL 35','SIN','+','RCL 38','TAN','×','0.03916','×','0.09033','-','3600','÷','STO+ 39',
    'RCL 35','COS','RCL 35','SIN','-','0.03916','×','3600','÷','STO+ 38',
    # aberration
    'RCL 00','57.29577951308232','×','180','+','STO 35',
    'RCL 54','-0.000042037','×','0.016708634','+','STO 36',
    'RCL 54','1.71946','×','102.93735','+','STO 37',
    'RCL 35','RCL- 39','COS','-20.49552','×',
    'RCL 37','RCL- 39','COS','RCL× 36','20.49552','×','+','RCL 38','COS','÷','RCL+ 66','3600','÷','STO+ 39',
    'RCL 35','RCL- 39','SIN','RCL 37','RCL- 39','SIN','RCL× 36','-','RCL 38','SIN','×','-20.49552','×','3600','÷','STO+ 38',
    # equatorial (true obliquity R76)
    'RCL 38','SIN','RCL 76','COS','×','RCL 38','COS','RCL 76','SIN','×','RCL 39','SIN','×','+','ASIN','STO 06',
    'RCL 39','SIN','RCL 76','COS','×','RCL 38','TAN','RCL 76','SIN','×','-','RCL 39','COS','→POL','X<>Y',
    '360','+','360','MOD','STO 05',
    'RCL 80','RCL- 05','360','+','360','MOD','STO 04',
    '360','RCL- 05','360','MOD','STO 05',
    '8.794','RCL÷ 34','60','÷','STO 07',
    'RCL 07','RCL 05','RCL 06','RCL 04','RTN']
for lab,pre in ((11,'VN'),(12,'MA'),(13,'JU'),(14,'SA')):
    P+=['LBL %d'%lab]
    for c,reg in (('L',4),('B',5),('R',6)):
        P+=['INDEX "%s%s"'%(pre,c),str(cnt[pre+c]),'STO 55','XEQ "SER"','STO %02d'%reg]
    P+=['RTN']
P+=['END']
open('/home/claude/PLAN.txt','w').write('\n'.join(P)+'\n')
print(len(M),len(P))
