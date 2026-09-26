import sys, random, math
sys.path.insert(0,'/home/claude/C47_nav/python/native')
import c47astro as A
from math import *
# Standish, approximate positions 1800-2050: a e I L varpi Omega, rates per century
EL={0:((1.00000261,0.01671123,-0.00001531,100.46457166,102.93768193,0.0),(0.00000562,-0.00004392,-0.01294668,35999.37244981,0.32327364,0.0)),
1:((0.72333566,0.00677672,3.39467605,181.97909950,131.60246718,76.67984255),(0.00000390,-0.00004107,-0.00078890,58517.81538729,0.00268329,-0.27769418)),
2:((1.52371034,0.09339410,1.84969142,-4.55343205,-23.94362959,49.55953891),(0.00001847,0.00007882,-0.00813131,19140.30268499,0.44441088,-0.29257343)),
3:((5.20288700,0.04838624,1.30439695,34.39644051,14.72847983,100.47390909),(-0.00011607,-0.00013253,-0.00183714,3034.74612775,0.21252668,0.20469106)),
4:((9.53667594,0.05386179,2.48599187,49.95424423,92.59887831,113.66242448),(-0.00125060,-0.00050991,0.00193609,1222.49362201,-0.41897216,-0.28867794))}
def helio(p,T):
    e0,r=EL[p]; a,e,I,L,w,O=[x+y*T for x,y in zip(e0,r)]
    M=radians((L-w)%360); E=M
    for _ in range(4): E=M+e*sin(E)          # fixed-point Kepler
    xv=a*(cos(E)-e); yv=a*sqrt(1-e*e)*sin(E)
    om=radians(w-O); O=radians(O); I=radians(I)
    x1=xv*cos(om)-yv*sin(om); y1=xv*sin(om)+yv*cos(om)
    return (x1*cos(O)-y1*cos(I)*sin(O), x1*sin(O)+y1*cos(I)*cos(O), y1*sin(I))
def quick(s,p):
    T=(s.jd-2451545.0)/36525.0
    xe,ye,ze=helio(0,T); xp,yp,zp=helio(p,T)
    x,y,z=xp-xe,yp-ye,zp-ze; dist=sqrt(x*x+y*y+z*z)
    lam=degrees(atan2(y,x))+1.3969713*T; bet=degrees(atan2(z,hypot(x,y)))
    eps=23.4393
    dec=A.dasin(A.dsin(bet)*A.dcos(eps)+A.dcos(bet)*A.dsin(eps)*A.dsin(lam))
    ra=A.datan2(A.dsin(lam)*A.dcos(eps)-A.dtan(bet)*A.dsin(eps),A.dcos(lam))
    return (s.aries-ra)%360, dec, dist
if __name__=='__main__':
    random.seed(1); mg=[0]*5; md=[0]*5; mr=[0]*5
    for k in range(3000):
        j=2451545+random.uniform(25*365.25,50*365.25); s=A.Sun(j)
        for p in (1,2,3,4):
            g,d,_,hp=A.planet(s,p); qg,qd,qr=quick(s,p)
            mg[p]=max(mg[p],abs((qg-g+180)%360-180)*math.cos(math.radians(d))); md[p]=max(md[p],abs(qd-d))
            mr[p]=max(mr[p],abs(qr-8.794/60/hp))
    for p in (1,2,3,4): print(p,'max err: along RA %.3f deg, Dec %.3f deg, dist %.4f au (%.1f s light)'%(mg[p],md[p],mr[p],mr[p]*499))
