#!/usr/bin/env python3
"""regalloc.py - DEV: renumber the numbered registers of a C47 listing (long names) so that values never needed
at the same time share a register (tools/build_navhopt.py: NAVFULL_R31 and MOONFAST_R31 in R00-R30).

Static and conservative, over the whole listing (bit masks: bit n = Rnn, or one bit per write line):
  flow       one node per line; GTO nn / GTO "name" / GTO IND r (every numeric label of the program), the skip
             of the tests (X=Y? FS? ISG DSE KEY? ...: the next line or the one after); XEQ is a call: the
             line after it, with the summaries of the callee (XEQ IND r: every numeric label of the program).
  MUST(e)    the registers a routine writes on every path to its RTN / END (a call kills them).
  USE(e)     the registers it may read before writing them.
  liveness   per register; at RTN / END of a routine: what is live after any call of it (so its temporaries
             never take the register of a value a caller keeps across the call).
  webs       reaching definitions (into a routine from all its callers, out of it only its own writes); a
             read joins every write that reaches it: one web = one value, whatever its register number.
  conflicts  a write conflicts with every web live after it; the webs get the fewest colours (DSatur) and
             every operand the number of its web.
Registers addressed indirectly (STO IND / RCL IND) are not handled: the listing must have none.
"""
import collections, re

REG = r'(\d\d)'
READ = re.compile(r'(?:RCL|RCL[+\-×÷]|AGRAPH|GRMOD|αLENG|AVIEW|XEQ IND|GTO IND|STO IND|RCL IND) ' + REG + '$')
WRITE = re.compile(r'(?:STO|KEY\?|CLα) ' + REG + '$')
RW = re.compile(r'(?:STO[+\-×÷]|ISG|DSE|x→α|αIP|α→𝑥) ' + REG + '$')
ANY = re.compile(r'^(RCL|RCL[+\-×÷]|AGRAPH|GRMOD|αLENG|AVIEW|XEQ IND|GTO IND|STO IND|RCL IND|STO|KEY\?|CLα|STO[+\-×÷]|ISG|DSE|x→α|αIP|α→𝑥) (\d\d)$')
SKIP = re.compile(r'^(.*\?( .*)?|ISG .*|DSE .*|KEY\? .*)$')
ALL = (1 << 100) - 1


def programs(L):
    """[(start, end)] line ranges of the programs (each ends with END)."""
    out, s = [], 0
    for i, l in enumerate(L):
        if l == 'END':
            out.append((s, i)); s = i + 1
    assert s == len(L), 'regalloc: the listing must end with END'
    return out


def bits(m):
    while m:
        b = m & -m
        yield b.bit_length() - 1
        m ^= b


class Flow:
    def __init__(self, L, fresh=(), table=False):
        self.L = L
        n = len(L)
        self.prog = [0] * n
        self.local, self.glob = [], {}
        for k, (a, b) in enumerate(programs(L)):
            loc = {}
            for i in range(a, b + 1):
                self.prog[i] = k
                m = re.fullmatch(r'LBL (\d\d)', L[i])
                if m:
                    loc[m.group(1)] = i
                m = re.fullmatch(r'LBL "(.+)"', L[i])
                if m:
                    self.glob[m.group(1)] = i
            self.local.append(loc)
        self.reg = [None] * n                                 # the register operand of the line
        self.rd = [0] * n; self.wr = [0] * n
        for i, l in enumerate(L):
            assert ' IND ' not in l or l.startswith(('XEQ IND', 'GTO IND')) or table, 'regalloc: indirect register: %s' % l
            for rx, r, w in ((READ, 1, 0), (WRITE, 0, 1), (RW, 1, 1)):
                m = rx.match(l)
                if m:
                    self.reg[i] = int(m.group(1))
                    self.rd[i] = r << self.reg[i]; self.wr[i] = w << self.reg[i]
                    break
        self.calls = {}
        self.succ = [[] for _ in L]
        for i, l in enumerate(L):
            op, _, arg = l.partition(' ')
            if op in ('RTN', 'END'):
                continue
            if op == 'GTO':
                self.succ[i] = self.targets(i, arg)
                continue
            if op == 'XEQ':
                self.calls[i] = self.targets(i, arg)
            nxt = [i + 1]
            if SKIP.match(l) and not l.startswith(('LBL', '"')):
                nxt.append(i + 2)
            self.succ[i] = [j for j in nxt if j < n and self.prog[j] == self.prog[i]]
        self.preds = [[] for _ in L]
        for i in range(n):
            for j in self.succ[i]:
                self.preds[j].append(i)
        self.entries = sorted({e for t in self.calls.values() for e in t} | set(self.glob.values()))
        self.callers = collections.defaultdict(list)
        for i, t in self.calls.items():
            for e in t:
                self.callers[e].append(i)
        self.bodies = {e: self.body(e) for e in self.entries}
        self.fresh = {self.glob[f] for f in fresh if f in self.glob}     # entries where no incoming value is used
        self.owners = collections.defaultdict(list)
        for e, b in self.bodies.items():
            for i in b:
                self.owners[i].append(e)

    def targets(self, i, arg):
        loc = self.local[self.prog[i]]
        if arg.startswith('"') and arg.strip('"') in self.glob:
            e = self.glob[arg.strip('"')]                     # s / XEQ "entry" of a dispatch entry: the stub s
            if self.L[e + 1] == 'GTO IND X' and re.fullmatch(r'\d\d?', self.L[i - 1]):
                return [self.local[self.prog[e]]['%02d' % int(self.L[i - 1])]]
        if arg.startswith('IND '):
            return self.table(i, arg[4:], loc)
        if arg.startswith('"'):
            return [self.glob[arg.strip('"')]]
        return [loc[arg]]

    def table(self, i, r, loc):
        """XEQ / GTO IND r: a table of routines. r = x + k (the last STO r before, in this program): the run of
        consecutive labels from the first one >= k; r = k - x (CHS k +): the run that ends at the last one <= k;
        otherwise every label not reached by falling into it (after RTN / END / GTO)."""
        L, a = self.L, i
        if L[i - 1].startswith('@TABLE '):                    # a table moved by navhopt.append: its labels
            lo, hi = map(int, L[i - 1].split()[1:])
            return sorted(loc['%02d' % x] for x in range(lo, hi + 1))
        if r in ('X', 'Y', 'Z', 'T'):                         # a dispatch entry: the stubs after it
            return [j for j in sorted(loc.values()) if j > i]
        while a > 0 and self.prog[a - 1] == self.prog[i]:
            a -= 1
            if L[a] == 'STO ' + r:
                if L[a - 1] == '+' and re.fullmatch(r'\d+', L[a - 2]):
                    k = int(L[a - 2]); nums = sorted(int(x) for x in loc)
                    if L[a - 3] == 'CHS':
                        top = max(x for x in nums if x <= k); run = [top]
                        while run[-1] - 1 in nums:
                            run.append(run[-1] - 1)
                    else:
                        low = min(x for x in nums if x >= k); run = [low]
                        while run[-1] + 1 in nums:
                            run.append(run[-1] + 1)
                    return sorted(loc['%02d' % x] for x in run)
                break
        return [j for j in sorted(loc.values()) if L[j - 1] in ('RTN', 'END') or
                L[j - 1].startswith(('GTO ', 'LBL "')) and not SKIP.match(L[j - 2])]

    def body(self, e):
        """Lines reached from entry e without entering calls, in order."""
        seen, todo = set(), [e]
        while todo:
            i = todo.pop()
            if i not in seen:
                seen.add(i); todo += self.succ[i]
        return sorted(seen)


def must_write(F):
    """MUST per entry; F.din[e][line]: the registers written on every path from e to the line."""
    L = F.L
    F.din = {}
    must = {e: ALL for e in F.entries}
    changed = True
    while changed:
        changed = False
        for e in F.entries:
            body = F.bodies[e]
            inb = set(body)
            din = {e: 0}
            again = True
            while again:
                again = False
                for i in body:
                    if i == e:
                        continue
                    v = None
                    for p in F.preds[i]:
                        if p in inb and p in din:
                            o = din[p] | F.wr[p]
                            if p in F.calls:
                                k = ALL
                                for c in F.calls[p]:
                                    k &= must[c]
                                o |= k
                            v = o if v is None else v & o
                    if v is not None and din.get(i) != v:
                        din[i] = v; again = True
            m = ALL
            for i in body:
                if L[i] in ('RTN', 'END') and i in din:
                    m &= din[i] | F.wr[i]
            F.din[e] = din
            if m != must[e]:
                must[e] = m; changed = True
    return must


def liveness(F, must):
    """(USE per entry, live-in, live-out) per line, register masks."""
    L, n = F.L, len(F.L)
    use = {e: 0 for e in F.entries}
    lin, lout = [0] * n, [0] * n

    def solve(ret):
        changed = True
        while changed:
            changed = False
            for i in range(n - 1, -1, -1):
                out = 0
                if L[i] in ('RTN', 'END'):
                    for e in F.owners[i]:
                        out |= ret(e)
                else:
                    for j in F.succ[i]:
                        out |= lin[j]
                if i in F.calls:
                    k, u = ALL, 0
                    for e in F.calls[i]:
                        k &= must[e]; u |= use[e]
                    inn = F.rd[i] | u | (out & ~k)
                else:
                    inn = F.rd[i] | (out & ~F.wr[i])
                if i in F.fresh:
                    inn = 0
                if out != lout[i] or inn != lin[i]:
                    lout[i], lin[i] = out, inn; changed = True

    while True:                                               # USE: nothing live at RTN
        solve(lambda e: 0)
        new = {e: lin[e] for e in F.entries}
        if new == use:
            break
        use = new

    def retlive(e):
        v = 0
        for c in F.callers[e]:
            v |= lout[c]
        return v
    while True:
        before = list(lout)
        solve(retlive)
        if before == lout:
            break
    return use, lin, lout


def reaching(F, must):
    """Reaching definitions (one bit per write line): (defs, rin, rout, defs of each register)."""
    L, n = F.L, len(F.L)
    dl = [i for i in range(n) if F.wr[i]]
    did = {i: k for k, i in enumerate(dl)}
    ofreg = [0] * 100
    for i in dl:
        ofreg[F.reg[i]] |= 1 << did[i]
    pseudo = {}                                              # fresh entry -> its 100 pseudo writes (no code)
    for e in sorted(F.fresh):
        m = 0
        for r in range(100):
            k = len(dl); dl.append((e, r)); m |= 1 << k; ofreg[r] |= 1 << k
        pseudo[e] = m
    mine = {e: 0 for e in F.entries}                           # write lines a routine may execute
    changed = True
    while changed:
        changed = False
        for e in F.entries:
            m = 0
            for i in F.bodies[e]:
                if F.wr[i]:
                    m |= 1 << did[i]
                for c in F.calls.get(i, ()):
                    m |= mine[c]
            if m != mine[e]:
                mine[e] = m; changed = True
    rin, rout = [0] * n, [0] * n
    exitd = {e: 0 for e in F.entries}
    changed = True
    while changed:
        changed = False
        for i in range(n):
            v = 0
            for p in F.preds[i]:
                v |= rout[p]
            for c in F.callers.get(i, ()):
                v |= rin[c]
            if i in F.calls:
                k = ALL
                for e in F.calls[i]:
                    k &= must[e]
                kill = 0
                for r in bits(k):
                    kill |= ofreg[r]
                o = v & ~kill
                for e in F.calls[i]:
                    o |= exitd[e] & mine[e]
            elif F.wr[i]:
                o = (v & ~ofreg[F.reg[i]]) | (1 << did[i])
            else:
                o = v
            if i in pseudo:
                o = pseudo[i]
            if v != rin[i] or o != rout[i]:
                rin[i], rout[i] = v, o; changed = True
        for e in F.entries:
            x = 0
            for i in F.bodies[e]:
                if L[i] in ('RTN', 'END'):
                    x |= rin[i]
            if x != exitd[e]:
                exitd[e] = x; changed = True
    return dl, did, rin, rout, ofreg


def analyse(L, fresh=(), table=False):
    """{'webs': web of each line's operand, 'graph': conflicts between webs, 'regs': register of each web,
    'uninit': lines reading a register no write reaches, 'live': max registers live at once}."""
    F = Flow(L, fresh, table)
    must = must_write(F)
    use, lin, lout = liveness(F, must)
    dl, did, rin, rout, ofreg = reaching(F, must)
    parent = list(range(len(dl)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    uninit = []
    for i in range(len(L)):
        if F.rd[i]:
            reach = rin[i] & ofreg[F.reg[i]]
            ds = list(bits(reach))
            if not ds:
                uninit.append(i)
                continue
            for d in ds[1:]:
                union(ds[0], d)
            if F.wr[i]:
                union(ds[0], did[i])
    web = {}
    for i in range(len(L)):
        if F.wr[i]:
            web[i] = find(did[i])
        elif F.rd[i] and i not in uninit:
            web[i] = find(next(bits(rin[i] & ofreg[F.reg[i]])))
    G = collections.defaultdict(set)
    for w in set(web.values()):
        G[w]
    for i in range(len(L)):
        if not F.wr[i]:
            continue
        w = web[i]
        for r in bits(lout[i]):
            for d in bits(rout[i] & ofreg[r]):
                v = find(d)
                if v != w:
                    G[w].add(v); G[v].add(w)
    regs = {find(k): (F.reg[d] if isinstance(d, int) else d[1]) for k, d in enumerate(dl)}
    members = collections.defaultdict(set)
    for k in range(len(dl)):
        members[find(k)].add(k)
    return {'flow': F, 'webs': web, 'graph': G, 'regs': regs, 'uninit': uninit, 'members': members,
            'dl': dl, 'rin': rin, 'lin': lin,
            'live': max(bin(x).count('1') for x in lout)}


def colour(G, order=None):
    """DSatur: {node: colour 0..}."""
    col = {}
    todo = set(G)
    while todo:
        r = max(sorted(todo), key=lambda x: (len({col[n] for n in G[x] if n in col}), len(G[x])))
        bad = {col[n] for n in G[r] if n in col}
        c = 0
        while c in bad:
            c += 1
        col[r] = c; todo.discard(r)
    return col


def allocate(L, limit=None, base=0, fresh=()):
    """(renamed listing, number of registers): each web in register base + its colour."""
    A = analyse(L, fresh)
    assert not A['uninit'], 'regalloc: reads with no write before them: %s' % [(i, L[i]) for i in A['uninit']]
    col = colour(A['graph'])
    k = max(col.values()) + 1 if col else 0
    if limit is not None and k > limit:
        raise ValueError('regalloc: %d registers needed, %d allowed' % (k, limit))
    out = list(L)
    for i, w in A['webs'].items():
        g = ANY.match(L[i])
        out[i] = '%s %02d' % (g.group(1), base + col[w])
    return out, k


def reached(F, roots):
    """The lines run from the entry lines roots (bodies, and the routines they call)."""
    seen, todo, lines = set(), list(roots), set()
    while todo:
        e = todo.pop()
        if e in seen:
            continue
        seen.add(e)
        for i in F.bodies[e]:
            lines.add(i)
            todo += F.calls.get(i, [])
    return lines


def plan(L, fresh=(), table=False, local=True, keep_global=('GRMOD', 'KEY?'), roots=None, hot=()):
    """Globals in R00.. and, with local=True, the values private to one subroutine level in local registers.
    Entries (called routines) that share lines (a common tail, or a dispatch entry and the routines it jumps
    to) form one group with one numbering: LocR n after the LBL of each (each call is its own level). A web
    is local to a group when every line of it is only in bodies of that group, its entries are entered only
    by calls or from inside the group (no falling or jumping in from outside), no line is an op of keep_global and no entry reads it before writing it (no value kept
    between calls, none passed in).
    hot: entry lines of routines called very often (a LocR on each call costs time): their values stay global.
    roots: the entry lines the program is run from (default: its first label); a read no write reaches is
    allowed only in code they never reach (routines kept for the tests), and left as it is.
    Returns (listing, number of globals, {entry line: number of locals}); the LocR lines are already in."""
    A = analyse(L, fresh, table)
    F, webs, G = A['flow'], A['webs'], A['graph']
    live = reached(F, roots or [F.glob[next(iter(F.glob))]])
    bad = [(i, L[i]) for i in A['uninit'] if i in live]
    assert not bad, 'regalloc: reads with no write before them: %s' % bad
    parent = {e: e for e in F.entries}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i in range(len(L)):
        o = F.owners[i]
        for e in o[1:]:
            parent[find(e)] = find(o[0])
    groups = collections.defaultdict(list)
    for e in F.entries:
        groups[find(e)].append(e)
    lines = collections.defaultdict(list)
    for i, w in webs.items():
        lines[w].append(i)
    home = {}
    hotlines = set().union(*(F.body(e) for e in hot)) if hot else set()
    if local:
        for w, ls in lines.items():
            own = {e for i in ls for e in F.owners[i]}
            if not own:
                continue
            g = {find(e) for e in own}
            if len(g) != 1:
                continue
            g = g.pop()
            ents = groups[g]
            inside = set().union(*(F.bodies[e] for e in ents))
            if any(p not in inside for e in ents for p in F.preds[e]):
                continue
            if any(L[i].split(' ')[0] in keep_global for i in ls) or any(i in hotlines for i in ls):
                continue
            r = A['regs'][w]
            if any(F.rd[i] and not F.din[e].get(i, ALL) >> r & 1 for i in ls for e in F.owners[i]):
                continue                                       # read before written: passed in, or kept
            home[w] = g
    glob = {w: {v for v in G[w] if v not in home} for w in G if w not in home}
    gcol = colour(glob)
    k = max(gcol.values()) + 1 if gcol else 0
    lcol, nloc = {}, collections.Counter()
    for g in set(home.values()):
        sub = {w: {v for v in G[w] if home.get(v) == g} for w in home if home[w] == g}
        c = colour(sub)
        lcol.update(c)
        for e in groups[g]:                                    # LocR only as large as the code of e needs
            if L[e + 1] == 'GTO IND X':
                continue                                       # a dispatch entry: its routines have their own
            body = set(F.bodies[e])
            need = [c[w] for w in sub if any(i in body for i in lines[w])]
            if need:
                nloc[e] = max(need) + 1
    out = list(L)
    for i, w in webs.items():
        g = ANY.match(L[i])
        out[i] = '%s R.%02d' % (g.group(1), lcol[w]) if w in home else '%s %02d' % (g.group(1), gcol[w])
    res = []
    for i, l in enumerate(out):
        res.append(l)
        if nloc.get(i):
            res.append('LocR %d' % nloc[i])
    return res, k, {L[e]: n for e, n in nloc.items()}


def move_once(L):
    """Local routines called by a single XEQ nn (not after a test) whose code is one block LBL nn ... RTN that
    nothing else enters or leaves: the block replaces the XEQ (no label, no jump: the same steps minus the
    XEQ and RTN). An RTN inside the block -> GTO to a new label at its end. Repeated. (listing, routines)."""
    done = 0
    while True:
        F = Flow(L)
        sites = collections.defaultdict(list)
        for i, t in F.calls.items():
            if not L[i].startswith(('XEQ "', 'XEQ IND')):
                sites[t[0]].append(i)
        pick = None
        for e, cs in sorted(sites.items()):
            c = cs[0]
            if len(cs) != 1 or SKIP.match(L[c - 1]) and not L[c - 1].startswith(('LBL', '"')):
                continue
            body = F.bodies[e]
            r = max(body)
            if L[r] != 'RTN' or body != list(range(e, r + 1)) or not c < e and not c > r:
                continue
            if any(F.owners[i] != [e] for i in body) or any(p not in body for i in body for p in F.preds[i]):
                continue
            if any(L[e] in [L[j] for j in F.calls.get(i, [])] for i in body):
                continue
            pick = (e, c, r)
            break
        if pick is None:
            return L, done
        e, c, r = pick
        block = L[e:r + 1]
        inner = [k for k, l in enumerate(block[:-1]) if l == 'RTN']
        if not F.preds[e]:
            block = block[1:]; inner = [k - 1 for k in inner]
        if inner:
            k = F.prog[c]
            used = {int(x) for x in F.local[k]}
            lab = '%02d' % next(n for n in range(100) if n not in used)
            for j in inner:
                block[j] = 'GTO ' + lab
            block[-1] = 'LBL ' + lab
        else:
            block = block[:-1]
        if c < e:
            L = L[:c] + block + L[c + 1:e] + L[r + 1:]
        else:
            L = L[:e] + L[r + 1:c] + block + L[c + 1:]
        done += 1


def inline_once(L):
    """Local routines called by a single XEQ nn (and entered no other way) run on the level of their caller:
    XEQ nn -> GTO nn and a new LBL after it, every RTN of the routine -> GTO to that label (same steps, no new
    subroutine level, so its values can be local registers of the caller). Repeated while one is found.
    Returns (listing, number of routines)."""
    done = 0
    while True:
        F = Flow(L)
        sites = collections.defaultdict(list)
        for i, t in F.calls.items():
            if not L[i].startswith(('XEQ "', 'XEQ IND')):
                sites[t[0]].append(i)
        pick = None
        for e, cs in sorted(sites.items()):
            if len(cs) != 1 or any(p not in F.bodies[e] for p in F.preds[e]):
                continue
            body = F.bodies[e]
            rets = [i for i in body if L[i] == 'RTN']
            if not rets or any(L[i] == 'END' for i in body) or any(F.owners[i] != [e] for i in rets):
                continue
            if any(L[e] in [L[j] for j in F.calls.get(i, [])] for i in body):
                continue                                       # recursive
            pick = (e, cs[0], rets)
            break
        if pick is None:
            return L, done
        e, c, rets = pick
        k = F.prog[c]
        a, b = programs(L)[k]
        used = {int(x) for x in F.local[k]}
        free = [n for n in range(100) if n not in used]
        assert free, 'regalloc: no free label in the program'
        lab = '%02d' % free[0]
        out = list(L)
        out[c] = 'GTO ' + L[e][4:]
        for i in rets:
            out[i] = 'GTO ' + lab
        out[c + 1:c + 1] = ['LBL ' + lab]
        L = out
        done += 1
