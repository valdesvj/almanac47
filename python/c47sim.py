"""c47sim.py - small C47 RPN interpreter used by c47view.py.

It runs the C47 program files (.txt, one command per line) of the C47_nav
suite exactly as written and keeps the 400 x 240 one-bit screen, so the PC
picture is made by the same code as the calculator picture.
Only the commands used by the suite are implemented.
"""
from decimal import Decimal as D, getcontext
import math, re
getcontext().prec = 34

def f(x): return float(x)

class Mat:
    """A real matrix on the stack (RCL of a named matrix, results of matrix operations)."""
    def __init__(self, rows): self.rows = [[float(v) for v in r] for r in rows]
    def dims(self): return len(self.rows), len(self.rows[0])
    def mul(self, o):
        if isinstance(o, Mat):
            n, k = self.dims(); k2, m = o.dims()
            if k != k2: raise ValueError('matrix size mismatch %dx%d * %dx%d' % (n, k, k2, m))
            return Mat([[sum(self.rows[i][t] * o.rows[t][j] for t in range(k)) for j in range(m)] for i in range(n)])
        return Mat([[v * float(o) for v in r] for r in self.rows])
    def add(self, o):
        if not isinstance(o, Mat) or o.dims() != self.dims(): raise ValueError('matrix size mismatch')
        return Mat([[a + b for a, b in zip(r, q)] for r, q in zip(self.rows, o.rows)])
    def elementwise(self, fn): return Mat([[fn(v) for v in r] for r in self.rows])
    def flat(self): return [v for r in self.rows for v in r]

class Calc:
    def __init__(self, prog_text, mats=None):
        self.s = [D(0)]*4; self.lift = True; self.reg = {}; self.flags = set()
        self.deg = True; self.mats = mats or {}; self.cur = None; self.I = self.J = 1
        self.lastx = D(0)
        self.lines = []
        for ln in prog_text.splitlines():
            ln = re.sub(r'^\s*\d+\s+', '', ln.split(';')[0]).strip()
            if ln: self.lines.append(ln)
        self.labels = {}
        for i, ln in enumerate(self.lines):
            if ln.startswith('LBL '): self.labels[ln[4:].strip().strip('"')] = i
    # stack
    def push(self, v):
        if self.lift: self.s = [v] + self.s[:3]
        else: self.s[0] = v
        self.lift = True
    def unary(self, fn):
        self.lastx = self.s[0]; self.s[0] = fn(self.s[0]); self.lift = True
    def binary(self, fn):
        x, y = self.s[0], self.s[1]; self.lastx = x
        self.s = [fn(y, x), self.s[2], self.s[3], self.s[3]]; self.lift = True
    def ang_in(self, v): return math.radians(f(v)) if self.deg else f(v)
    def ang_out(self, v): return D(math.degrees(v)) if self.deg else D(v)
    def trig(self, fn, x):
        # high-precision range reduction for large degree arguments
        if self.deg: x = x % D(360)
        return D(fn(math.radians(f(x)) if self.deg else f(x)))
    def regkey(self, arg):
        if arg.startswith('IND '): return int(self.rget(arg[4:].strip()))
        return arg
    def rget(self, k):
        k = str(int(k)) if isinstance(k, int) else k
        return self.reg.get(k.lstrip('0') or '0', D(0))
    def rset(self, k, v):
        k = str(int(k)) if isinstance(k, int) else k
        self.reg[k.lstrip('0') or '0'] = v
    def indlab(self, n, pc):
        if isinstance(n, str): return n                     # XEQ IND r with a label name in r
        if hasattr(self,'pid'): return '%d_%d'%(self.pid[pc], n)
        return '%02d'%n
    def run(self, label, maxsteps=10**6):
        pc = self.labels[label] + 1; rs = []; n = 0
        while True:
            n += 1; self.steps=getattr(self,'steps',0)+1
            if n > maxsteps: raise RuntimeError('too many steps')
            ln = self.lines[pc]; pc += 1
            op, _, arg = ln.partition(' '); arg = arg.strip().strip('"')
            if re.fullmatch(r'[01]+#2', ln):
                v=int(ln[:-2],2)
                if v >= 1<<(getattr(self,'ws',64)-1): raise ValueError('OUT OF RANGE literal %s ws %d'%(ln,self.ws))
                self.push(D(v)); continue
            if re.fullmatch(r'-?[\d.]+(E-?\d+)?', ln): self.push(D(ln)); continue
            if op == 'LBL': continue
            if ln.startswith('├'): self.alpha+=ln[1:].strip('"'); continue
            if ln.startswith('"'): self.alpha=ln.strip('"'); self.push(ln.strip('"')); continue
            if op in ('RTN', 'END'):
                if rs: pc = rs.pop(); continue
                return
            if op == 'GTO':
                if arg.startswith('IND '): arg=self.indlab((lambda v: v if isinstance(v,str) else int(v))(self.rget(arg[4:].strip())),pc-1)
                pc = self.labels[arg] + 1; continue
            if op == 'XEQ':
                if arg.startswith('IND '): arg=self.indlab((lambda v: v if isinstance(v,str) else int(v))(self.rget(arg[4:].strip())),pc-1)
                rs.append(pc); pc = self.labels[arg] + 1; continue
            if isinstance(self.s[0], Mat) or (op in ('×', '+', 'DOT') and isinstance(self.s[1], Mat)):
                x, y = self.s[0], self.s[1]
                if op == '×':
                    self.binary(lambda y, x: y.mul(x) if isinstance(y, Mat) else x.mul(y)); continue
                if op == '+':
                    self.binary(lambda y, x: y.add(x)); continue
                if op == 'DOT':
                    a, b = y.flat(), x.flat()
                    if len(a) != len(b): raise ValueError('DOT size mismatch')
                    self.binary(lambda y, x: D(repr(sum(p * q for p, q in zip(a, b))))); continue
                if op in ('COS', 'SIN'):
                    fn = math.cos if op == 'COS' else math.sin
                    self.unary(lambda m: m.elementwise(lambda v: float(self.trig(fn, D(repr(v))))) ); continue
                if op == 'RCL×':
                    v = self.rget(self.regkey(arg)); self.s[0] = x.mul(v); self.lift = True; continue
                if op == 'STO' and arg.startswith('"'):
                    pass
            if op == 'ENTER': self.s = [self.s[0]] + self.s[:3]; self.lift = False; continue
            if op == 'DEG': self.deg = True; continue
            if op == 'RAD': self.deg = False; continue
            op={'Y↑X':'Y^X','X↑2':'X^2','x²':'X^2'}.get(op,op)
            if op in ('+', '-', '×', '÷', 'Y^X', 'MOD'):
                fn = {'+': lambda y, x: (y+(x if isinstance(x,str) else format(x.normalize(),'f'))) if isinstance(y,str) else y+x, '-': lambda y, x: y-x, '×': lambda y, x: y*x, '÷': lambda y, x: y/x,
                      'Y^X': lambda y, x: D(f(y)**f(x)) if x != int(x) else y**int(x),
                      'MOD': lambda y, x: y - x*(y/x).__floor__()}[op]
                self.binary(fn); continue
            if op == 'ABS': self.unary(lambda x: abs(x)); continue
            if op == 'SIGN': self.unary(lambda x: D(1) if x > 0 else (D(-1) if x < 0 else D(0))); continue
            if op == 'ACOS': self.unary(lambda x: self.ang_out(math.acos(f(x)))); continue
            if op in ('X<Y?','X≥Y?','X=0?','X<0?','X>0?','X≤Y?','X≥0?','X>Y?','X=Y?','X≤0?','X≠0?','X≠Y?'):
                x,y=self.s[0],self.s[1]
                ok={'X<Y?':lambda:x<y,'X≥Y?':lambda:x>=y,'X=0?':lambda:x==0,'X<0?':lambda:x<0,'X>0?':lambda:x>0,'X≤Y?':lambda:x<=y,'X≥0?':lambda:x>=0,'X>Y?':lambda:x>y,'X=Y?':lambda:x==y,'X≠0?':lambda:x!=0,'X≠Y?':lambda:x!=y,'X≤0?':lambda:x<=0}[op]()
                if not ok: pc+=1
                continue
            if op == 'CLLCD': self.pix=[]; self.txt=[]; continue
            if op == 'TICKS': self.push(D(int(self.steps * 0.0017))); continue   # 1/10 s, model: 0.17 ms per step
            if op == 'PIXEL':
                x,y=int(self.s[0]),int(self.s[1])
                if x>=0 and y>=0: self.pix.append((y,x))
                if x<0: self.pix.extend((yy,-x) for yy in range(240))
                if y<0: self.pix.extend((-y,xx) for xx in range(400))
                continue
            if op == 'CLA': self.alpha=''; continue
            if op == 'AIP': self.alpha+=str(int(self.s[0])); continue
            if ln.startswith('"'): self.alpha=ln.strip('"'); self.push(ln.strip('"')); continue
            if op == 'IP': self.unary(lambda x: D(int(x))); continue
            if op == 'ISG':
                k=self.regkey(arg); v=self.rget(k); cnt=int(v); frac=v-cnt; fin=int(frac*1000); inc=int(round(f(frac*100000)))%100 or 1
                cnt+=inc; self.rset(k,D(cnt)+frac)
                if cnt>fin: pc+=1
                continue
            if op == 'GETKEY': self.push(D(self.keys.pop(0))); continue
            if op == 'FIX': self.fix=int(arg); continue
            if op == 'AVIEW': self.msgs.append(self.rget(arg) if arg else self.alpha); continue
            if op == 'ARCL':
                v=float(self.s[0]) if arg=='ST X' else float(self.rget(arg)); self.alpha+=('%.'+str(getattr(self,'fix',4))+'f')%v; continue
            if ln.startswith('├'): self.alpha+=ln[1:].strip('"'); continue
            if op == 'STOP': self.stops.append(self.msgs[-1] if self.msgs else ''); continue
            if op == 'AVIEW' and arg: self.msgs.append(self.rget(arg)); continue
            if op == 'KEY?' and getattr(self,'keyskip',False) and not getattr(self,'keys',None):
                # no key pressed: the program goes on (timed loops); a frame when the screen changed
                self.frames=getattr(self,'frames',[])
                if not self.frames or self.frames[-1] != self.pix:
                    self.frames.append(list(self.pix))
                    if len(self.frames) >= (getattr(self,'maxpauses',None) or 10**9): raise StopIteration
                continue
            if op == 'KEY?':                                  # waiting for a key: this is a shown frame
                self.frames=getattr(self,'frames',[]); self.frames.append(list(self.pix))
                if not getattr(self,'keys',None) or len(self.frames) >= (getattr(self,'maxpauses',None) or 10**9): raise StopIteration
                self.rset(arg, D(self.keys.pop(0))); pc += 1; continue
            if op == 'PROMPT':
                self.msgs=getattr(self,'msgs',[]); self.msgs.append(self.rget(arg))
                ans=getattr(self,'answers',[])
                if ans:
                    v = ans.pop(0)
                    if v is not None: self.push(D(v))     # None: R/S without keying a number
                elif len(self.msgs)>getattr(self,'maxprompts',10**9): raise StopIteration
                continue
            if op == 'PAUSE':
                self.pauses=getattr(self,'pauses',0)+1; self.frames=getattr(self,'frames',[]); self.frames.append(list(self.pix))
                if len(self.frames) >= (getattr(self,'maxpauses',None) or 10**9): raise StopIteration
                continue
            if op == 'CLLCDxy':
                y0=int(self.s[1]); self.pix=[p for p in self.pix if p[0]<y0]; self.frames=getattr(self,'frames',[]); continue
            if op == 'CLΣ': self.stat=[]; continue
            if op == 'Σ+': self.stat.append((float(self.s[0]),float(self.s[1]))); continue
            if op in ('PLSTAT','PLTFCNS'): continue
            if op == '42ALENG': self.push(D(len(self.rget('K')))); continue
            if op == '42ATOX':
                k=self.rget('K'); self.push(D(ord(k[0]))); self.rset('K',k[1:]); continue
            if op == 'αLENG': self.push(D(len(self.rget(arg)))); continue
            if op == 'α→𝑥':
                k=self.rget(arg); v=ord(k[0])
                if v >= 1<<(getattr(self,'ws',64)-1): raise ValueError('OUT OF RANGE alpha->x %d ws %d'%(v,self.ws))
                self.push(D(v)); self.rset(arg,k[1:]); continue
            if op == 'αSL': self.rset(arg, self.rget(arg)[int(self.s[0]):]); continue
            if op == 'REM': continue
            if op == 'WSIZE': self.ws=int(arg); continue
            if op == 'REGS': self.regs_opened=True; continue
            if op == 'RAN#':
                import random as _r; self.push(D(repr(_r.Random(getattr(self,'seed',0)).random()))); self.seed=getattr(self,'seed',0)+1; continue
            if op == 'DELP': self.deleted=getattr(self,'deleted',[])+[arg]; continue
            if op == 'GRMOD': self.grmod=int(self.rget(arg)); continue
            if op == 'AGRAPH' and arg:
                v=int(self.rget(arg)) & ((1<<self.ws)-1); x=int(self.s[0]); y=int(self.s[1])
                if getattr(self,'grmod',0) == 3:                  # XOR: switch every pixel of the pattern
                    ps=set(self.pix)
                    for i in range(self.ws):
                        if v>>i & 1: ps ^= {(y+i,x)}
                    self.pix=list(ps)
                else:
                    for i in range(self.ws):
                        if v>>i & 1: self.pix.append((y+i,x))
                self.s[0]=self.s[0]+1; continue
            if op == 'FP': self.unary(lambda x: x-D(int(x))); continue
            if op == 'INPUT': self.push(self.rget(arg)); continue
            if op == 'CHS': self.s[0] = -self.s[0]; continue
            if op == 'SIN': self.unary(lambda x: self.trig(math.sin, x)); continue
            if op == 'COS': self.unary(lambda x: self.trig(math.cos, x)); continue
            if op == 'TAN': self.unary(lambda x: self.trig(math.tan, x)); continue
            if op == 'ASIN': self.unary(lambda x: self.ang_out(math.asin(f(x)))); continue
            if op == 'X^2': self.unary(lambda x: x*x); continue
            if op == '→DEG': self.unary(lambda x: x*D(180)/D(math.pi)); continue
            if op == 'LASTX': self.push(self.lastx); continue
            if op == 'X<>Y': self.s[0], self.s[1] = self.s[1], self.s[0]; self.lift = True; continue
            if op == 'R↓': self.s = self.s[1:] + self.s[:1]; self.lift = True; continue
            if op == '→POL':
                x, y = f(self.s[0]), f(self.s[1])
                self.s[0] = D(math.hypot(x, y)); self.s[1] = self.ang_out(math.atan2(y, x)); self.lift = True; continue
            if op == 'STO' and isinstance(self.s[0], Mat):
                self.mats[arg] = [list(r) for r in self.s[0].rows]; continue
            if op == 'STO' and isinstance(self.s[0], tuple):
                _, r, c = self.s[0]; self.mats[arg] = [[0.0]*c for _ in range(r)]; continue
            if op in ('STO', 'STO+', 'STO-', 'STO×', 'STO÷'):
                k = self.regkey(arg); v = self.rget(k); x = self.s[0]
                self.rset(k, {'STO': lambda: x, 'STO+': lambda: v+x, 'STO-': lambda: v-x, 'STO×': lambda: v*x, 'STO÷': lambda: v/x}[op]()); self.lift = True; continue
            if op == 'RCL':
                k = self.regkey(arg)
                if isinstance(k, str) and k in self.mats and k not in self.reg:
                    self.push(Mat(self.mats[k])); continue
                self.push(self.rget(k)); continue
            if op in ('RCL+', 'RCL-', 'RCL×', 'RCL÷'):
                v = self.rget(self.regkey(arg)); self.lastx = self.s[0]
                x0 = self.s[0]; self.s[0] = {'RCL+': lambda: x0+v, 'RCL-': lambda: x0-v, 'RCL×': lambda: x0*v, 'RCL÷': lambda: x0/v}[op]()
                self.lift = True; continue
            if op == 'DSE':
                k = self.regkey(arg); v = self.rget(k)
                cnt = int(v); frac = v - cnt; fin = int(frac*1000); inc = int(round(f(frac*100000))) % 100 or 1
                cnt -= inc; self.rset(k, D(cnt) + frac)
                if cnt <= fin: pc += 1
                continue
            if op == 'CF': self.flags.discard(int(arg)); continue
            if op == 'SF': self.flags.add(int(arg)); continue
            if op == 'FS?':
                if int(arg) not in self.flags: pc += 1
                continue
            if op == 'FC?':
                if int(arg) in self.flags: pc += 1
                continue
            if op == 'NEWMAT':
                r, c = int(self.s[1]), int(self.s[0]); self.s = [('MAT', r, c), self.s[2], self.s[3], self.s[3]]; self.lift = True; continue
            if op == 'STOEL': self.mats[self.cur][self.I-1][self.J-1] = float(self.s[0]); continue
            if op == 'INDEX': self.cur = arg; self.I = self.J = 1; continue
            if op == 'STOIJ':
                i, j = self.s[1], self.s[0]; m = self.mats[self.cur]
                if i != int(i) or j != int(j) or not (1 <= i <= len(m) and 1 <= j <= len(m[0])):
                    raise ValueError('STOIJ (%s, %s) out of range for %s %dx%d' % (i, j, self.cur, len(m), len(m[0])))
                self.I, self.J = int(i), int(j); self.lift = True; continue
            if op == 'RCLEL': self.push(D(str(float(self.mats[self.cur][self.I-1][self.J-1])))); continue
            if op == 'J+':
                m = self.mats[self.cur]; self.J += 1
                if self.J > len(m[0]):
                    self.J = 1; self.I += 1
                    if self.I > len(m): self.I = 1; self.flags.add(77)
                continue
            raise ValueError('unknown op: ' + ln)


def load(files):
    """Load several program files into one memory.
    Numeric labels are local to each file (like separate programs on the C47)."""
    out = []; pid = []
    for k, fn in enumerate(files):
        with open(fn, encoding='utf-8') as fh:
            for ln in fh.read().splitlines():
                ln = ln.strip()
                if not ln or ln.startswith('REM'):
                    continue
                m = re.fullmatch(r'(LBL|GTO|XEQ) (\d+)', ln)
                if m:
                    ln = '%s %d_%d' % (m.group(1), k, int(m.group(2)))
                out.append(ln); pid.append(k)
    c = Calc('\n'.join(out)); c.pid = pid
    c.pix = []; c.frames = []; c.msgs = []; c.stops = []; c.answers = []; c.alpha = ''
    return c
