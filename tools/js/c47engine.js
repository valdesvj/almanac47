/* c47engine.js - JavaScript port of c47sim.py (C47 RPN interpreter for the C47_nav suite).
   Runs the C47 program text exactly as written and keeps the 400x240 one-bit screen. */
(function (root) {
  'use strict';
  const STRQ = s => s.replace(/^"+|"+$/g, '');
  const CMPS = new Set(['X<Y?', 'X≥Y?', 'X=0?', 'X<0?', 'X>0?', 'X≤Y?', 'X≥0?', 'X>Y?', 'X=Y?', 'X≠0?', 'X≤0?']);
  const OPALIAS = { 'Y↑X': 'Y^X', 'X↑2': 'X^2', 'x²': 'X^2' };
  const toRad = d => d * Math.PI / 180, toDeg = r => r * 180 / Math.PI;
  const trunc = Math.trunc;
  function fmtNum(x) {                       // like format(Decimal.normalize(), 'f')
    if (Number.isInteger(x)) return String(x);
    let s = x.toPrecision(15);
    if (s.includes('e')) s = x.toFixed(20);
    return s.replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '');
  }
  function key(k) {                          // register key normalisation (R05 == R5)
    k = String(k);
    const t = k.replace(/^0+/, '');
    return t === '' ? '0' : t;
  }

  class Calc {
    constructor(lines, pid) {
      this.s = [0, 0, 0, 0]; this.lift = true; this.reg = {}; this.flags = new Set();
      this.deg = true; this.mats = {}; this.cur = null; this.I = 1; this.J = 1; this.lastx = 0;
      this.pix = []; this.frames = []; this.msgs = []; this.alpha = ''; this.ws = 64;
      this.steps = 0; this.maxprompts = 1e9; this.pid = pid;
      this.lines = lines; this.labels = {};
      lines.forEach((ln, i) => { if (ln.startsWith('LBL ')) this.labels[STRQ(ln.slice(4).trim())] = i; });
      this.code = lines.map(ln => this.compile(ln));
    }
    compile(ln) {
      if (/^[01]+#2$/.test(ln)) return { t: 'bin', v: parseInt(ln.slice(0, -2), 2), ln };
      if (/^-?[\d.]+(E-?\d+)?$/.test(ln)) return { t: 'num', v: parseFloat(ln) };
      if (ln.startsWith('├')) return { t: 'app', v: STRQ(ln.slice(1)) };
      if (ln.startsWith('"')) return { t: 'str', v: STRQ(ln) };
      const sp = ln.indexOf(' ');
      let op = sp < 0 ? ln : ln.slice(0, sp);
      const arg = sp < 0 ? '' : STRQ(ln.slice(sp + 1).trim());
      op = OPALIAS[op] || op;
      return { t: 'op', op, arg, ln };
    }
    push(v) { if (this.lift) this.s = [v, this.s[0], this.s[1], this.s[2]]; else this.s[0] = v; this.lift = true; }
    unary(fn) { this.lastx = this.s[0]; this.s[0] = fn(this.s[0]); this.lift = true; }
    binary(fn) { const x = this.s[0], y = this.s[1]; this.lastx = x; this.s = [fn(y, x), this.s[2], this.s[3], this.s[3]]; this.lift = true; }
    rget(k) { const v = this.reg[key(k)]; return v === undefined ? 0 : v; }
    rset(k, v) { this.reg[key(k)] = v; }
    regkey(arg) { return arg.startsWith('IND ') ? String(trunc(this.rget(arg.slice(4).trim()))) : arg; }
    indlab(n, pc) { return this.pid[pc] + '_' + n; }
    trig(fn, x) { if (this.deg) x = x % 360; return fn(this.deg ? toRad(x) : x); }
    angOut(v) { return this.deg ? toDeg(v) : v; }
    loopCounter(v) {                          // ccccc.fffii
      const cnt = trunc(v), frac = v - cnt;
      const fin = trunc(frac * 1000 + 1e-7);
      const inc = (Math.round(frac * 100000) % 100) || 1;
      return { cnt, frac, fin, inc };
    }
    run(label, maxsteps = 1e7) {
      let pc = this.labels[label] + 1; const rs = []; let n = 0;
      const S = this.s;
      for (;;) {
        if (++n > maxsteps) throw new Error('too many steps');
        this.steps++;
        const c = this.code[pc]; pc++;
        switch (c.t) {
          case 'bin':
            if (c.v >= 2 ** (this.ws - 1)) throw new Error('OUT OF RANGE literal ' + c.ln);
            this.push(c.v); continue;
          case 'num': this.push(c.v); continue;
          case 'app': this.alpha += c.v; continue;
          case 'str': this.alpha = c.v; this.push(c.v); continue;
        }
        const op = c.op, arg = c.arg; let x, y, k, v;
        switch (op) {
          case 'LBL': case 'REM': continue;
          case 'RTN': case 'END': if (rs.length) { pc = rs.pop(); continue; } return;
          case 'GTO': {
            const a = arg.startsWith('IND ') ? this.indlab(trunc(this.rget(arg.slice(4).trim())), pc - 1) : arg;
            pc = this.labels[a] + 1; continue;
          }
          case 'XEQ': {
            const a = arg.startsWith('IND ') ? this.indlab(trunc(this.rget(arg.slice(4).trim())), pc - 1) : arg;
            if (this.labels[a] === undefined) throw new Error('label not found ' + a);
            rs.push(pc); pc = this.labels[a] + 1; continue;
          }
          case 'ENTER': this.s = [this.s[0], this.s[0], this.s[1], this.s[2]]; this.lift = false; continue;
          case 'DEG': this.deg = true; continue;
          case 'RAD': this.deg = false; continue;
          case '+': this.binary((y, x) => typeof y === 'string' ? y + (typeof x === 'string' ? x : fmtNum(x)) : y + x); continue;
          case '-': this.binary((y, x) => y - x); continue;
          case '×': this.binary((y, x) => y * x); continue;
          case '÷': this.binary((y, x) => y / x); continue;
          case 'Y^X': this.binary((y, x) => Math.pow(y, x)); continue;
          case 'MOD': this.binary((y, x) => y - x * Math.floor(y / x)); continue;
          case 'ABS': this.unary(Math.abs); continue;
          case 'ACOS': this.unary(x => this.angOut(Math.acos(x))); continue;
          case 'ASIN': this.unary(x => this.angOut(Math.asin(x))); continue;
          case 'SIN': this.unary(x => this.trig(Math.sin, x)); continue;
          case 'COS': this.unary(x => this.trig(Math.cos, x)); continue;
          case 'TAN': this.unary(x => this.trig(Math.tan, x)); continue;
          case 'X^2': this.unary(x => x * x); continue;
          case '→DEG': this.unary(x => x * 180 / Math.PI); continue;
          case 'IP': this.unary(x => trunc(x)); continue;
          case 'FP': this.unary(x => x - trunc(x)); continue;
          case 'CHS': this.s[0] = -this.s[0]; continue;
          case 'LASTX': this.push(this.lastx); continue;
          case 'X<>Y': [this.s[0], this.s[1]] = [this.s[1], this.s[0]]; this.lift = true; continue;
          case 'R↓': this.s = [this.s[1], this.s[2], this.s[3], this.s[0]]; this.lift = true; continue;
          case '→POL': x = this.s[0]; y = this.s[1];
            this.s[0] = Math.hypot(x, y); this.s[1] = this.angOut(Math.atan2(y, x)); this.lift = true; continue;
          case 'CLLCD': this.pix = []; continue;
          case 'PIXEL': {
            x = trunc(this.s[0]); y = trunc(this.s[1]);
            if (x >= 0 && y >= 0) this.pix.push([y, x]);
            if (x < 0) for (let yy = 0; yy < 240; yy++) this.pix.push([yy, -x]);
            if (y < 0) for (let xx = 0; xx < 400; xx++) this.pix.push([-y, xx]);
            continue;
          }
          case 'CLLCDxy': { const y0 = trunc(this.s[1]); this.pix = this.pix.filter(p => p[0] < y0); continue; }
          case 'PAUSE': this.frames.push(this.pix.slice()); continue;
          case 'PROMPT':
            this.msgs.push(this.rget(arg));
            if (this.msgs.length > this.maxprompts) throw { stop: true };
            continue;
          case 'AVIEW': this.msgs.push(arg ? this.rget(arg) : this.alpha); continue;
          case 'CLA': this.alpha = ''; continue;
          case 'AIP': this.alpha += String(trunc(this.s[0])); continue;
          case 'FIX': this.fix = parseInt(arg, 10); continue;
          case 'ARCL': v = arg === 'ST X' ? this.s[0] : this.rget(arg); this.alpha += Number(v).toFixed(this.fix ?? 4); continue;
          case 'ISG': case 'DSE': {
            k = this.regkey(arg); const L = this.loopCounter(this.rget(k));
            const cnt = op === 'ISG' ? L.cnt + L.inc : L.cnt - L.inc;
            this.rset(k, cnt + L.frac);
            if (op === 'ISG' ? cnt > L.fin : cnt <= L.fin) pc++;
            continue;
          }
          case 'αLENG': this.push(String(this.rget(arg)).length); continue;
          case 'α→𝑥': {
            const str = String(this.rget(arg)); const cp = str.codePointAt(0);
            if (cp >= 2 ** (this.ws - 1)) throw new Error('OUT OF RANGE alpha->x');
            this.push(cp); this.rset(arg, str.slice(cp > 0xffff ? 2 : 1)); continue;
          }
          case 'αSL': this.rset(arg, String(this.rget(arg)).slice(trunc(this.s[0]))); continue;
          case 'WSIZE': this.ws = parseInt(arg, 10); continue;
          case 'AGRAPH': {
            const ws = this.ws; let val = BigInt(trunc(this.rget(arg)));
            val &= (1n << BigInt(ws)) - 1n;
            x = trunc(this.s[0]); y = trunc(this.s[1]);
            for (let i = 0; val; i++, val >>= 1n) if (val & 1n) this.pix.push([y + i, x]);
            this.s[0] = this.s[0] + 1; continue;
          }
          case 'INPUT': this.push(this.rget(arg)); continue;
          case 'STO': case 'STO+': case 'STO-': case 'STO×': case 'STO÷': {
            x = this.s[0];
            if (op === 'STO' && x && x.mat) { this.mats[arg] = Array.from({ length: x.r }, () => new Array(x.c).fill(0)); continue; }
            k = this.regkey(arg); v = this.rget(k);
            this.rset(k, op === 'STO' ? x : op === 'STO+' ? v + x : op === 'STO-' ? v - x : op === 'STO×' ? v * x : v / x);
            this.lift = true; continue;
          }
          case 'RCL': this.push(this.rget(this.regkey(arg))); continue;
          case 'RCL+': case 'RCL-': case 'RCL×': case 'RCL÷': {
            v = this.rget(this.regkey(arg)); this.lastx = this.s[0]; x = this.s[0];
            this.s[0] = op === 'RCL+' ? x + v : op === 'RCL-' ? x - v : op === 'RCL×' ? x * v : x / v;
            this.lift = true; continue;
          }
          case 'CF': this.flags.delete(parseInt(arg, 10)); continue;
          case 'FC?': if (this.flags.has(parseInt(arg, 10))) pc++; continue;
          case 'NEWMAT': this.s = [{ mat: true, r: trunc(this.s[1]), c: trunc(this.s[0]) }, this.s[2], this.s[3], this.s[3]]; this.lift = true; continue;
          case 'STOEL': this.mats[this.cur][this.I - 1][this.J - 1] = Number(this.s[0]); continue;
          case 'INDEX': this.cur = arg; this.I = this.J = 1; continue;
          case 'STOIJ': this.I = trunc(this.s[1]); this.J = trunc(this.s[0]); this.lift = true; continue;
          case 'RCLEL': this.push(this.mats[this.cur][this.I - 1][this.J - 1]); continue;
          case 'J+': {
            const m = this.mats[this.cur]; this.J++;
            if (this.J > m[0].length) { this.J = 1; this.I++; if (this.I > m.length) { this.I = 1; this.flags.add(77); } }
            continue;
          }
          case 'CLΣ': case 'PLSTAT': case 'PLTFCNS': case 'STOP': continue;
        }
        if (CMPS.has(op)) {
          x = this.s[0]; y = this.s[1];
          const ok = { 'X<Y?': x < y, 'X≥Y?': x >= y, 'X=0?': x == 0, 'X<0?': x < 0, 'X>0?': x > 0, 'X≤Y?': x <= y,
            'X≥0?': x >= 0, 'X>Y?': x > y, 'X=Y?': x === y, 'X≠0?': x != 0, 'X≤0?': x <= 0 }[op];
          if (!ok) pc++;
          continue;
        }
        throw new Error('unknown op: ' + c.ln);
      }
    }
  }

  // Load several program texts; numeric labels stay local to each program.
  function load(texts) {
    const out = [], pid = [];
    texts.forEach((txt, k) => {
      for (let ln of txt.split(/\r?\n/)) {
        ln = ln.trim();
        if (!ln || ln.startsWith('REM')) continue;
        const m = /^(LBL|GTO|XEQ) (\d+)$/.exec(ln);
        if (m) ln = m[1] + ' ' + k + '_' + parseInt(m[2], 10);
        ln = ln.split(';')[0].replace(/^\s*\d+\s+/, '').trim();
        if (!ln) continue;
        out.push(ln); pid.push(k);
      }
    });
    return new Calc(out, pid);
  }

  function jd(y, m, d, h) {
    if (m <= 2) { y -= 1; m += 12; }
    const a = Math.floor(y / 100), b = 2 - a + Math.floor(a / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24;
  }

  const FILES = ['MATA', 'MATST', 'MATM', 'MATP', 'SUNA', 'STAR', 'CHZ', 'SNMU', 'SBRT', 'MOON', 'PLAN', 'PTXB', 'PTXT',
    'SUNRISE', 'PHAS', 'STXT', 'ALMF', 'HALMV', 'HORZ', 'HORZS', 'ALMT'];

  class Engine {
    constructor(progs) {             // progs: {NAME: text}
      this.c = load(FILES.map(f => progs[f]));
      for (const m of ['MATA', 'MATST', 'MATM', 'MATP']) this.c.run(m);
    }
    start(j, lat, lon) {
      const c = this.c;
      c.steps = 0; c.pix = []; c.frames = []; c.msgs = []; c.s = [0, 0, 0, 0]; c.lift = true; c.maxprompts = 1e9;
      c.push(j); c.push(lat); c.push(lon);
    }
    screen(view, j, lat, lon) {       // -> {frames: [Set of x+400*row], steps}
      this.start(j, lat, lon);
      this.c.run(view);
      const raw = (view === 'HORZ' && this.c.frames.length) ? this.c.frames : [this.c.pix];
      const frames = raw.map(fr => {
        const s = new Set();
        for (const [y, x] of fr) if (x >= 0 && x < 400 && y >= 0 && y < 240) s.add(x + 400 * (239 - y));
        return s;
      });
      return { frames, steps: this.c.steps };
    }
    text(j, lat, lon) {
      this.start(j, lat, lon); this.c.maxprompts = 120;
      try { this.c.run('ALMT'); } catch (e) { if (!e.stop) throw e; }
      let m = this.c.msgs.map(String);
      const r = m.indexOf(m[0], 1); if (r > 0) m = m.slice(0, r);
      return { lines: m, steps: this.c.steps };
    }
  }

  root.C47 = { Engine, load, jd, FILES };
  if (typeof module !== 'undefined') module.exports = root.C47;
})(typeof window !== 'undefined' ? window : globalThis);
