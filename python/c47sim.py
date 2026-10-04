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
    def atext(self, text):
        """ATEXT as in the C47 source (screen.c: fnAText, _doShowString), standardFont, 20-row lines:
        X, Y are used as |X|, |Y| (Y = bottom of the glyph box). A CR glyph (U+21B5) or LF after a
        character = next line (20 rows down) at the start column; several in a row = several lines.
        A CR as the FIRST character is not a line break: it is drawn as a character (the CR glyph,
        not in our font data: drawn here as '?'). Before a character, if x > 380 and the character
        would pass x 400: next line. After the text, x > 380: next line; below the bottom: row 0.
        X and Y get the offset to the next position added (a negative X or Y grows in magnitude).
        GRMOD 0 sets the glyph pixels, 1 clears the glyph box first, 2 clears them, 3 flips them."""
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from stdfont import STD, code as stdcode
        if getattr(self, 'grfnt', 20) == 10:                 # GRFNT 10: the tinyFont, 8-row lines
            from tinyfont import TINY as STD
        LH = STD[0x41][3] + STD[0x41][4] + STD[0x41][5]       # line height = the glyph box (20 or 8)
        CP = 1 if getattr(self, 'grfnt', 20) == 21 else 0      # GRFNT 21: one column less per character (checked, FNTCHT)
        X, Y = int(self.s[0]), int(self.s[1])
        x, y = abs(X), abs(Y); x0 = x; line = y; mode = getattr(self, 'grmod', 0)
        ps = set(self.pix)
        t = str(text); i = 0
        while i < len(t):
            ch = t[i]; i += 1
            cb, cg, ca, ra, rg, rb, rows = STD.get(stdcode(ch), STD[0x3f])
            adv = cb + cg + ca - CP
            if x > 380 and x + adv > 400:
                x, line = x0, line - LH
            on = {(line + rb + rg - 1 - r, x + cb + c) for r, v in enumerate(rows) for c in range(cg) if v >> (cg - 1 - c) & 1}
            on = {p for p in on if 0 <= p[0] < 240 and 0 <= p[1] < 400}
            if mode == 1:
                ps -= {(yy, xx) for yy in range(line, line + ra + rg + rb) for xx in range(x, x + adv)}
            if mode == 2: ps -= on
            elif mode == 3: ps ^= on
            else: ps |= on
            x += adv
            while i < len(t) and t[i] in ('\u21b5', '\n'):   # CR / LF after a character
                i += 1; x, line = x0, line - LH
        nx, ny = x, line
        if nx > 380:
            nx, ny = x0, ny - LH
        if ny < 0:
            ny = 0
        self.pix = list(ps)
        self.s[0] = D(X + (x0 - nx if X < 0 else nx - x0))
        self.s[1] = D(Y + (y - ny if Y < 0 else ny - y))

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
            if getattr(self, 'count', None) is not None: self.count(op, self.s[0])     # tests: what runs (test_navopt)
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
            if op == 'CLSTK': self.s = [D(0)] * 4; continue
            if op == 'SSIZE#': self.push(D(8)); continue          # stack size (C47 default 8; modelled as 4 levels)
            if op in ('SSIZE4', 'SSIZE8'): continue
            # dates (C47 CLK functions); a date is ('D', y, m, d). x→ⅅ / ⅅ→x follow the CLK date format
            # self.datefmt: 'YMD' (YYYY.MMDD, the default), 'DMY' (DD.MMYYYY) or 'MDY' (MM.DDYYYY);
            # FS? DMY / MDY / YMD test it (the C47 system flags of the CLK date format)
            if op == 'x→ⅅ':
                self.lastx = self.s[0]; fmt = getattr(self, 'datefmt', 'YMD')
                if fmt == 'YMD':
                    v = int((self.s[0] * 10000).to_integral_value()); self.s[0] = ('D', v // 10000, v // 100 % 100, v % 100)
                else:
                    v = int((self.s[0] * 1000000).to_integral_value()); a, b, y = v // 1000000, v // 10000 % 100, v % 10000
                    self.s[0] = ('D', y, b, a) if fmt == 'DMY' else ('D', y, a, b)
                continue
            if op == 'ⅅ→x':
                _, y, m, d = self.s[0]; fmt = getattr(self, 'datefmt', 'YMD')
                self.s[0] = (D(y) + D(m) / 100 + D(d) / 10000 if fmt == 'YMD' else
                             D(d) + D(m) / 100 + D(y) / 1000000 if fmt == 'DMY' else D(m) + D(d) / 100 + D(y) / 1000000)
                continue
            if op == 'ⅅ→J':
                _, y, m, d = self.s[0]; a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
                self.s[0] = D(d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045); continue
            if op == 'J→ⅅℸ':                         # JDN (.0 = noon) -> Y date, X time (hours)
                j = self.s[0] + D('0.5'); n = int(j // 1); fr = j - n
                a = n + 32044; b = (4 * a + 3) // 146097; c = a - 146097 * b // 4
                dd = (4 * c + 3) // 1461; e = c - 1461 * dd // 4; mm = (5 * e + 2) // 153
                day = e - (153 * mm + 2) // 5 + 1; mon = mm + 3 - 12 * (mm // 10); yr = 100 * b + dd - 4800 + mm // 10
                self.lastx = self.s[0]; self.s[0] = ('D', yr, mon, day); self.lift = True; self.push(fr * 24); continue
            if op in ('DAY', 'MONTH', 'YEAR'):
                _, y, m, d = self.s[0]; self.s[0] = D({'DAY': d, 'MONTH': m, 'YEAR': y}[op]); continue
            # text: append to the string in a register (αIP: integer part of X; x→α: string X or character code X)
            if op in ('αIP', 'x→α'):
                k = self.regkey(arg); v = self.rget(k); x = self.s[0]
                if not isinstance(v, str): v = format(D(int(v)).normalize(), 'f') if op == 'αIP' else v
                if op == 'αIP': add = str(int(x))
                else: add = x if isinstance(x, str) else chr(int(x))
                self.rset(k, v + add); continue
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
            if op == 'PAUSE' and arg in ('0', '1'): continue   # PAUSE 0 / 1: display update only (no frame of its own)
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
            if op == 'GRFNT' and not arg: self.grfnt = int(self.s[0]); continue   # font of ATEXT from X (10 tiny, 20 standard); X stays
            if op == 'SNAP': self.snaps = getattr(self, 'snaps', []) + [list(self.pix)]; continue   # a picture of the screen
            if op == 'WSIZE': self.ws=int(arg); continue
            if op == 'REGS': self.regs_opened=True; continue
            if op == 'RAN#':
                import random as _r; self.push(D(repr(_r.Random(getattr(self,'seed',0)).random()))); self.seed=getattr(self,'seed',0)+1; continue
            if op == 'DELP': self.deleted=getattr(self,'deleted',[])+[arg]; continue
            if op == 'GRMOD': self.grmod=int(self.rget(arg)) if arg else int(self.s[0]); continue
            if op in ('DROP', 'DROP𝑥'): self.s = self.s[1:] + self.s[3:]; continue
            if op == 'ATEXT' and arg:
                # ATEXT r (new C47 command): the string in r in the standardFont, Y = row of the bottom of
                # the 20-row glyph box (base line 4 rows up), X = column; returns Y, X of the next character.
                # r may be a stack register: ATEXT Z (ST Z) takes the string from Z
                k = arg[3:] if arg.startswith('ST ') else arg
                self.atext(self.s['XYZT'.index(k)] if k in ('X', 'Y', 'Z', 'T') else self.rget(self.regkey(arg))); continue
            if op == '⇄':
                # stack shuffle: ⇄ zyxt puts the old z in X, y in Y, x in Z, t in T
                old = list(self.s); self.s = [old['xyzt'.index(c)] for c in arg.lower()] + old[4:]; self.lift = True; continue
            if op == 'AGRAPH' and arg:
                # AGRAPH D: the pattern pushed and rotated down by R↓ (D on the C47's 8-level stack = T here)
                v=int(self.s[3] if arg == 'D' else self.rget(arg)) & ((1<<self.ws)-1); x=int(self.s[0]); y=int(self.s[1])
                if getattr(self,'grmod',0) == 2:                  # OFF: switch the pattern's pixels off
                    off={(y+i,x) for i in range(self.ws) if v>>i & 1}
                    self.pix=[p for p in self.pix if p not in off]
                elif getattr(self,'grmod',0) == 3:                # XOR: switch every pixel of the pattern
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
            if op == '→REC':                       # Y angle, X radius -> Y = r sin, X = r cos (C47 →RECT, Free42 →REC)
                r, t = self.s[0], self.s[1]
                self.s[0] = r * self.trig(math.cos, t); self.s[1] = r * self.trig(math.sin, t); self.lift = True; continue
            if op == 'STO' and isinstance(self.s[0], Mat):
                self.mats[arg] = [list(r) for r in self.s[0].rows]; continue
            if op == 'STO' and isinstance(self.s[0], tuple) and self.s[0][0] == 'MAT':
                _, r, c = self.s[0]; self.mats[arg] = [[0.0]*c for _ in range(r)]; continue
            if op in ('STO', 'STO+', 'STO-', 'STO×', 'STO÷'):
                k = self.regkey(arg); v = self.rget(k); x = self.s[0]
                self.rset(k, {'STO': lambda: x, 'STO+': lambda: v+x, 'STO-': lambda: v-x, 'STO×': lambda: v*x, 'STO÷': lambda: v/x}[op]()); self.lift = True; continue
            if op == 'RCL' and getattr(self, 'ign1er', False):
                try:
                    self.rget(self.regkey(arg))
                except (KeyError, IndexError):
                    self.ign1er = False; continue                 # the error is ignored: nothing recalled
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
            if op in ('SF', 'CF') and arg.strip("'") == 'IGN1ER':   # ignore the next error (the C47 clears it on an error)
                self.ign1er = op == 'SF'; continue
            if op == 'SSIZE8' or op == 'SSIZE4': continue           # stack size: modelled as 4 levels
            if op == 'Date→ⅅ' or op == 'Time→ℸ':                    # the clock: self.clock, a JD of the local time
                j = D(str(getattr(self, 'clock'))) + D('0.5'); n = int(j // 1); fr = j - n
                if op == 'Time→ℸ':
                    self.push(('T', fr * 24)); continue
                a = n + 32044; b = (4 * a + 3) // 146097; c = a - 146097 * b // 4
                dd = (4 * c + 3) // 1461; e = c - 1461 * dd // 4; mm = (5 * e + 2) // 153
                self.push(('D', 100 * b + dd - 4800 + mm // 10, mm + 3 - 12 * (mm // 10), e - (153 * mm + 2) // 5 + 1)); continue
            if op == 'ⅅℸ→J':                                         # Y date, X time -> JD
                dt, tm = (self.s[1], self.s[0]) if self.s[0][0] == 'T' else (self.s[0], self.s[1])
                _, y, m, d = dt; a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
                jdn = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
                self.lastx = self.s[0]; self.s = [D(jdn) + tm[1] / 24 - D('0.5'), self.s[2], self.s[3], self.s[3]]; continue
            if op == 'SQRT': self.unary(lambda x: x.sqrt()); continue
            if op == '2ˣ': self.unary(lambda x: D(2) ** int(x) if x == int(x) else D(2 ** f(x))); continue
            if op == 'SINT': self.unary(lambda x: D(int(x))); continue   # real -> short integer (the bits stay)
            if op == 'CF': self.flags.discard(int(arg)); continue
            if op == 'SF': self.flags.add(int(arg)); continue
            if op in ('FS?', 'FC?') and arg.strip("'") in ('DMY', 'MDY', 'YMD'):   # the date-format system flags
                on = getattr(self, 'datefmt', 'YMD') == arg.strip("'")
                if on != (op == 'FS?'): pc += 1
                continue
            if op == 'FS?':
                if int(arg) not in self.flags: pc += 1
                continue
            if op == 'FC?':
                if int(arg) in self.flags: pc += 1
                continue
            if op == 'NEWMAT':
                r, c = int(self.s[1]), int(self.s[0]); self.s = [('MAT', r, c), self.s[2], self.s[3], self.s[3]]; self.lift = True; continue
            if op == 'STOEL': self.mats[self.cur][self.I-1][self.J-1] = self.s[0] if isinstance(self.s[0], D) else float(self.s[0]); continue   # real34 kept (C47 real matrix)
            if op == 'INDEX': self.cur = arg; self.I = self.J = 1; continue
            if op == 'STOIJ':
                i, j = self.s[1], self.s[0]; m = self.mats[self.cur]
                if i != int(i) or j != int(j) or not (1 <= i <= len(m) and 1 <= j <= len(m[0])):
                    raise ValueError('STOIJ (%s, %s) out of range for %s %dx%d' % (i, j, self.cur, len(m), len(m[0])))
                self.I, self.J = int(i), int(j); self.lift = True; continue
            if op == 'RCLEL':
                v = self.mats[self.cur][self.I-1][self.J-1]; self.push(v if isinstance(v, D) else D(str(float(v)))); continue
            if op in ('RCLSEQ', 'STOSEQ'):              # recall / store the element, then J+
                m = self.mats[self.cur]
                if op == 'RCLSEQ':
                    v = m[self.I-1][self.J-1]; self.push(v if isinstance(v, D) else D(str(float(v))))
                else:
                    m[self.I-1][self.J-1] = self.s[0] if isinstance(self.s[0], D) else float(self.s[0])
                self.J += 1
                if self.J > len(m[0]):
                    self.J = 1; self.I += 1
                    if self.I > len(m): self.I = 1
                continue
            if op == 'I+':
                m = self.mats[self.cur]; self.I += 1
                if self.I > len(m): self.I = 1
                continue
            if op == 'J-':
                m = self.mats[self.cur]; self.J -= 1
                if self.J < 1:
                    self.J = len(m[0]); self.I -= 1
                    if self.I < 1: self.I = len(m)
                continue
            if op == 'J+':
                m = self.mats[self.cur]; self.J += 1
                if self.J > len(m[0]):
                    self.J = 1; self.I += 1
                    if self.I > len(m): self.I = 1; self.flags.add(77)
                continue
            raise ValueError(unknown(ln))


def unknown(ln):
    """The error for a step c47sim does not run: is it a C47 command at all (table of the firmware on master)?"""
    try:
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
        import c47ref
        names = c47ref.program_names(c47ref.load())
        op = next((ln[:k] for k in range(len(ln), 0, -1) if ln[:k] in names and (k == len(ln) or ln[k] == ' ')), None)
    except (OSError, ImportError):
        return 'unknown op: ' + ln
    if op:
        return 'unknown op: %s (C47 item %s %s: not modelled in c47sim yet)' % (ln, names[op]['opcode'], names[op]['catalog_name'])
    return 'unknown op: %s (not a name in docs/reference/C47_items_master.tsv; tools/c47check.py checks a listing with rejig)' % ln


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
