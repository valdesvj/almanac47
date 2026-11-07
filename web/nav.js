// nav.js - Almanac 47 in JavaScript: python/nav.py (Sun, Aries, stars, sunrise / sunset / twilight, Moon phase,
// Hc / Zn) and python/moon47.py (MOON47: the phases, age, % lit, HP, SD) line for line, with the same coefficients
// (data/navdata.js, written from python/navdata.py). tests/test_web.py checks it against the Python.
// Time = UT1 (add DUT1 to UTC). Works in a browser (file://) and in node.
(function (root) {
  'use strict';
  const { VL, VB, VR, NU, ST, SN, BR } = root.NAVDATA;
  const DT = 69.2;                       // TT - UT1, seconds
  const R2D = 180 / Math.PI, D2R = Math.PI / 180;
  const sin = Math.sin, cos = Math.cos, tan = Math.tan, asin = Math.asin, acos = Math.acos, atan2 = Math.atan2;
  const mod = (x, m) => ((x % m) + m) % m;
  const pyint = x => Math.trunc(x);      // Python int(): toward zero
  const pydiv = (a, b) => Math.floor(a / b);

  function jd(y, m, d, h) {
    h = h || 0;
    if (m <= 2) { y -= 1; m += 12; }
    const a = pydiv(y, 100), b = 2 - a + pydiv(a, 4);
    return pyint(365.25 * (y + 4716)) + pyint(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24;
  }

  const GROUPS = new Map();
  function ser(rows, tau) {
    let g = GROUPS.get(rows);
    if (!g) {
      const by = {};
      let kmax = 0;
      for (const [k, A, B, C] of rows) { (by[k] = by[k] || []).push([A, B, C]); kmax = Math.max(kmax, k); }
      g = []; for (let k = 0; k <= kmax; k++) g.push(by[k] || []);
      GROUPS.set(rows, g);
    }
    let s = 0;
    for (let i = g.length - 1; i >= 0; i--) {
      let t = 0; for (const [A, B, C] of g[i]) t += A * cos(B + C * tau);
      s = s * tau + t;
    }
    return s * 1e-8;
  }

  function nut(T) {
    const a = [297.85036 + 445267.11148 * T, 357.52772 + 35999.05034 * T, 134.96298 + 477198.867398 * T,
      93.27191 + 483202.017538 * T, 125.04452 - 1934.136261 * T];
    let dp = 0, de = 0;
    for (const r of NU) {
      const x = (r[0] * a[0] + r[1] * a[1] + r[2] * a[2] + r[3] * a[3] + r[4] * a[4]) * D2R;
      dp += (r[5] + r[6] * T) * sin(x);
      de += (r[7] + r[8] * T) * cos(x);
    }
    return [dp * 1e-4, de * 1e-4, a];
  }

  // j = JD (UT1): gha, dec, aries (deg) + internals
  function sun(j) {
    const T = (j + DT / 86400 - 2451545.0) / 36525;
    const tau = T / 10;
    const L = ser(VL, tau) * R2D, B = ser(VB, tau), R = ser(VR, tau);
    let lon = mod(L + 180, 360), lat = -B * R2D;
    const Lp = (lon - 1.397 * T) * D2R;
    lat += 0.03916 * (cos(Lp) - sin(Lp)) / 3600;
    lon -= 0.09033 / 3600;
    const [dp, de, args] = nut(T);
    lon += dp / 3600 - 20.4898 / R / 3600;
    const eps = (84381.448 - 46.815 * T + de) / 3600;
    const l = lon * D2R, b = lat * D2R, e = eps * D2R;
    const dec = asin(sin(b) * cos(e) + cos(b) * sin(e) * sin(l)) * R2D;
    const ra = atan2(sin(l) * cos(e) - tan(b) * sin(e), cos(l)) * R2D;
    const d = j - 2451545.0;
    const gmst = 280.46061837 + 360.98564736629 * d + 0.000387933 * (d / 36525) ** 2;
    const aries = mod(gmst + dp / 3600 * cos(e), 360);
    return { gha: mod(aries - ra, 360), dec, aries, T, lam: lon, eps, dpsi: dp, deps: de, args, sd: 15.99383 / R };
  }

  // n = almanac star 1-57 (58 Polaris): [gha, dec, sha]
  function star(j, n, s) {
    s = s || sun(j);
    const T = s.T;
    const [a0, d0, pa, pd] = ST[n - 1];
    const t = T * 100;
    const a = a0 + pa * t / 3.6e6 / cos(d0 * D2R);
    const d = d0 + pd * t / 3.6e6;
    const ze = (2.650545 + (2306.083227 + (0.2988499 + 0.01801828 * T) * T) * T) / 3600;
    const z = (-2.650545 + (2306.077181 + (1.0927348 + 0.01826837 * T) * T) * T) / 3600;
    const th = ((2004.191903 + (-0.4294934 - 0.04182264 * T) * T) * T) / 3600;
    const az = (a + ze) * D2R, dr = d * D2R, tr = th * D2R;
    const dm = asin(sin(tr) * cos(dr) * cos(az) + cos(tr) * sin(dr));
    const am = atan2(cos(dr) * sin(az), cos(tr) * cos(dr) * cos(az) - sin(tr) * sin(dr)) + z * D2R;
    const e0 = (s.eps - s.deps / 3600) * D2R;
    let be = asin(sin(dm) * cos(e0) - cos(dm) * sin(e0) * sin(am));
    let la = atan2(sin(am) * cos(e0) + tan(dm) * sin(e0), cos(am));
    const ek = 0.016708634 - 0.000042037 * T;
    const pi = (102.93735 + 1.71946 * T) * D2R;
    const su = s.lam * D2R;
    const k = 20.49552;
    const dbe = -k * sin(be) * (sin(su - la) - ek * sin(pi - la));
    const dla = (-k * cos(su - la) + ek * k * cos(pi - la)) / cos(be) + s.dpsi;
    la += dla / 3600 * D2R;
    be += dbe / 3600 * D2R;
    const e = s.eps * D2R;
    const dec = asin(sin(be) * cos(e) + cos(be) * sin(e) * sin(la)) * R2D;
    const ra = mod(atan2(sin(la) * cos(e) - tan(be) * sin(e), cos(la)) * R2D, 360);
    const sha = mod(360 - ra, 360);
    return [mod(s.aries + sha, 360), dec, sha];
  }

  const EVENTS = { rise: [-0.8333333333, -1], set: [-0.8333333333, 1], civam: [-6, -1], civpm: [-6, 1],
    nauam: [-12, -1], naupm: [-12, 1], tran: [0, 0] };

  // j0 = JD at 0h UT, lat N+, lon E+: UT hours, or null
  function event(j0, lat, lon, kind) {
    const [h0, sg] = EVENTS[kind || 'rise'];
    let t = 12 + 6 * sg;
    for (let i = 0; i < 10; i++) {
      const s = sun(j0 + t / 24);
      let target = 0;
      if (sg) {
        const c = (sin(h0 * D2R) - sin(lat * D2R) * sin(s.dec * D2R)) / (cos(lat * D2R) * cos(s.dec * D2R));
        if (Math.abs(c) > 1) return null;
        target = sg * acos(c) * R2D;
      }
      const dt = (mod(target - s.gha - lon + 540, 360) - 180) / 15;
      t += dt;
      if (Math.abs(dt) < 1e-5) break;
    }
    return t;
  }

  // [% illuminated, age in days since the true new moon] (nav.py's phase)
  function phase(j) {
    const s = sun(j);
    const [D, M, Mp, F] = s.args;
    const r = x => x * D2R;
    const i = 180 - D - 6.289 * sin(r(Mp)) + 2.1 * sin(r(M)) - 1.274 * sin(r(2 * D - Mp)) -
      0.658 * sin(r(2 * D)) - 0.214 * sin(r(2 * Mp)) - 0.11 * sin(r(D));
    const k = (1 + cos(r(i))) * 50;
    const ageFrom = dl => {
      const mn = M - 0.98560028 * dl, mpn = Mp - 13.064993 * dl, fn = F - 13.2293505 * dl;
      const c = -0.4072 * sin(r(mpn)) + 0.17241 * sin(r(mn)) + 0.01608 * sin(r(2 * mpn)) +
        0.01039 * sin(r(2 * fn)) + 0.00739 * sin(r(mpn - mn)) - 0.00514 * sin(r(mpn + mn)) +
        0.00208 * sin(r(2 * mn)) - 0.00111 * sin(r(mpn - 2 * fn)) - 0.00057 * sin(r(mpn + 2 * fn)) +
        0.00056 * sin(r(2 * mpn + mn));
      return dl - c;
    };
    const syn = 29.530589;
    const dl = (D % 360) / 12.190749;     // Python %: D is positive here
    let age = ageFrom(dl);
    if (age < 0) age = ageFrom(dl + syn);
    else if (age > 27) { const a2 = ageFrom(dl - syn); if (a2 >= 0) age = a2; }
    return [k, age];
  }

  // Hc, Zn (deg) and sin Hc
  function hcz(lat, lon, dec, gha) {
    const la = lat * D2R, sl = sin(la), cl = cos(la);
    const de = dec * D2R, t = (gha + lon) * D2R;
    const sd = sin(de), cd = cos(de), ct = cos(t);
    let sh = sl * sd + cl * cd * ct;
    sh = Math.max(-1, Math.min(1, sh));
    const zn = atan2(-cd * sin(t), cl * sd - sl * cd * ct) * R2D;
    return [asin(sh) * R2D, mod(zn + 360, 360), sh];
  }

  const NBODY = 8;
  // ALMF / HORZ's rule: the Sun, then the brightest stars higher than hmin, n rows; row = [id, gha, dec, hc, zn, sh]
  function bodies(j, lat, lon, n, hmin) {
    n = n || NBODY; hmin = hmin === undefined ? 10 : hmin;
    const s = sun(j);
    const out = [[0, s.gha, s.dec, ...hcz(lat, lon, s.dec, s.gha)]];
    for (const k of BR) {
      if (out.length >= n) break;
      const [g, d] = star(j, k, s);
      const h = hcz(lat, lon, d, g);
      if (h[0] > hmin) out.push([k, g, d, ...h]);
    }
    return [out, s];
  }

  // JD -> [year, month, day, UT hours]
  function cal(j) {
    const z = pyint(j + 0.5), f = j + 0.5 - z;
    let a = pyint((z - 1867216.25) / 36524.25);
    a = z + 1 + a - pydiv(a, 4);
    const b = a + 1524, c = pyint((b - 122.1) / 365.25), d = pyint(365.25 * c), e = pyint((b - d) / 30.6001);
    const day = b - d - pyint(30.6001 * e);
    const m = e < 14 ? e - 1 : e - 13;
    return [m > 2 ? c - 4716 : c - 4715, m, day, f * 24];
  }

  const phaseIndex = age => pyint(age / 29.530589 * 8 + 0.5) % 8;
  const daylight = h => h > 0 ? 'DAY' : h > -12 ? 'TWILIGHT' : 'NIGHT';
  const moonword = (k, age) => k >= 99.5 ? 'FULL' : k < 0.5 ? 'NEW' : age > 14.765 ? 'WANING' : 'WAXING';

  // ---- the printers (rounding as the C47's PDM PZN PHM PF1) ----
  const p2 = x => String(x).padStart(2, '0');
  function fdm(v) {
    let t = pyint(Math.abs(v) * 600 + 0.5);
    const d = pydiv(t, 600); t -= d * 600;
    return (v < 0 ? '-' : '') + d + ' ' + p2(pydiv(t, 10)) + '.' + (t % 10);
  }
  function fns(v, p, w) {
    p = p || 'NS'; w = w === undefined ? 8 : w;
    let s = ' ' + fdm(Math.abs(v));
    while (s.length < w) s = ' ' + s;
    return (v < 0 ? p[1] : p[0]) + s;
  }
  function fzn(v) {
    let t = pyint(v * 10 + 0.5);
    if (t >= 3600) t = 0;
    return String(pydiv(t, 10)).padStart(3, '0') + '.' + (t % 10);
  }
  function fhm(h) {
    if (h === null || h === undefined || h > 98) return '--:--';
    const m = mod(pyint(h * 60 + 0.5), 1440);
    return p2(pydiv(m, 60)) + ':' + p2(m % 60);
  }
  function f1(v) { const m = pyint(Math.abs(v) * 10 + 0.5); return pydiv(m, 10) + '.' + (m % 10); }
  function fdate(j) { const [y, m, d] = cal(j); return p2(d) + '-' + p2(m) + '-' + String(y).padStart(4, '0'); }

  // the ALMANAC page (ALMF): head, rows [id, name, GHA, Dec, Hc, Zn, hc], foot
  function almanac(j, lat, lon, n) {
    const [rows, s] = bodies(j, lat, lon, n);
    const head = [fdate(j), fhm(cal(j)[3]), fns(lat, 'NS', 0), fns(lon, 'EW', 0), fdm(s.aries)];
    const tab = rows.map(([k, g, d, hc, zn]) => [k, k === 0 ? 'SUN' : SN[k - 1].toUpperCase(), fdm(g), fns(d), fdm(hc), fzn(zn), hc]);
    const j0 = pyint(j - 0.5) + 0.5;
    const foot = ['nauam', 'naupm', 'rise', 'set', 'tran'].map(e => fhm(event(j0, lat, lon, e)));
    const [k, a] = phase(j);
    foot.push(f1(s.sd), String(pyint(k + 0.5)), moonword(k, a), f1(a));
    return [head, tab, foot];
  }

  // ---- MOON47 (python/moon47.py) ----
  const TERMS = [[0, 0, 1, 0, 6288774, -20905355], [2, 0, -1, 0, 1274027, -3699111], [2, 0, 0, 0, 658314, -2955968],
    [0, 0, 2, 0, 213618, -569925], [0, 1, 0, 0, -185116, 48888], [0, 0, 0, 2, -114332, 0], [2, 0, -2, 0, 58793, 246158],
    [2, -1, -1, 0, 57066, -152138], [2, 0, 1, 0, 53322, -170733], [2, -1, 0, 0, 45758, -204586],
    [0, 1, -1, 0, -40923, -129620], [1, 0, 0, 0, -34720, 108743], [0, 1, 1, 0, -30383, 104755],
    [2, 0, 0, -2, 15327, 0], [0, 0, 1, 2, -12528, 0], [0, 0, 1, -2, 10980, 79661], [4, 0, -1, 0, 10675, 0],
    [0, 0, 3, 0, 10034, 0], [4, 0, -2, 0, 8548, 0], [2, 1, -1, 0, -7888, 0]];
  const LUN = 29.530589, RATE = 12.190749, MDT = 69.0 / 86400;
  const PHASES = [[0, 'NEW MOON'], [90, 'FIRST QUARTER'], [180, 'FULL MOON'], [270, 'LAST QUARTER']];
  const NAMES = ['NEW MOON', 'WAXING CRESCENT', 'FIRST QUARTER', 'WAXING GIBBOUS', 'FULL MOON', 'WANING GIBBOUS',
    'LAST QUARTER', 'WANING CRESCENT'];
  const sind = x => sin(x * D2R), cosd = x => cos(x * D2R);

  // [elongation 0-360, distance km, latitude deg, M deg] at JD j (UT)
  function moon(j) {
    const T = (j + MDT - 2451545.0) / 36525;
    const D = 297.8501921 + 445267.1114 * T, M = 357.5291092 + 35999.05029 * T;
    const Mp = 134.9633964 + 477198.8675 * T, F = 93.272095 + 483202.0175 * T, E = 1 - 0.002516 * T;
    let lon = 0, dist = 0;
    for (const [d, m, mp, f, cl, cr] of TERMS) {
      const a = d * D + m * M + mp * Mp + f * F, e = m ? E : 1;
      lon += cl * e * sind(a); dist += cr * e * cosd(a);
    }
    const c = (1.914602 - 0.004817 * T) * sind(M) + 0.019993 * sind(2 * M) + 0.000289 * sind(3 * M);
    return [mod(D + lon / 1e6 - c + 0.00569, 360), 385000.56 + dist / 1000, 5.128189 * sind(F), M];
  }

  function phaseTime(j, target) {
    const d = mod(target - moon(j)[0], 360);
    let t0 = j, f0 = -d, t1 = j + d / RATE;
    for (let i = 0; i < 3; i++) {
      const f1 = mod(moon(t1)[0] - target + 180, 360) - 180;
      if (f1 === f0) break;
      [t0, t1, f0] = [t1, t1 - f1 * (t1 - t0) / (f1 - f0), f1];
    }
    return t1;
  }

  // everything MOON47 shows at JD j (UT)
  function moonPage(j) {
    const [e, dist, beta, M] = moon(j);
    const psi = acos(cosd(beta) * cosd(e)) * R2D;
    const r = 149597870.7 * (1.000140 - 0.016708 * cosd(M) - 0.000141 * cosd(2 * M));
    const i = atan2(r * sind(psi), dist - r * cosd(psi)) * R2D;
    let nw = phaseTime(j - e / RATE - 1, 0);
    if (nw > j) nw = phaseTime(nw - LUN - 1, 0);
    const age = j - nw;
    const next = PHASES.map(([a, name]) => {
      let t = phaseTime(j, a);
      if (t < j) t = phaseTime(t + LUN - 2, a);
      return [t, name];
    }).sort((x, y) => x[0] - y[0]);
    return { jd: j, lit: (1 + cosd(i)) * 50, age, hp: asin(6378.14 / dist) * R2D * 60, sd: 358473400 / dist / 60,
      index: pyint(age / LUN * 8 + 0.5) % 8, next, elongation: e, name: NAMES[pyint(age / LUN * 8 + 0.5) % 8] };
  }

  // ---- the Moon and the planets of python/native/c47astro.py (MOON, PLAN), when data/astro.js is loaded
  const AD = root.ASTRODATA;
  const dsin = x => sin(mod(x, 360) * D2R), dcos = x => cos(mod(x, 360) * D2R), dtan = x => tan(mod(x, 360) * D2R);
  const horner = (c, T) => { let v = c[c.length - 1]; for (let i = c.length - 2; i >= 0; i--) v = v * T + c[i]; return v; };

  // MOON / MOO2: [gha, dec, hp', sd'] at JD j (UT); s = sun(j)
  function moonPos(j, s) {
    s = s || sun(j);
    const T = s.T;
    const Lp = mod(horner([218.3164477, 481267.8812, -0.0015786, 1.855835024E-06, -1.533883486E-08], T), 360);
    const D = mod(horner([297.8501921, 445267.1114, -0.0018819, 1.831944719E-06, -8.844469995E-09], T), 360);
    const M = mod(horner([357.5291092, 35999.05029, -0.0001536, 4.083299306E-08], T), 360);
    const Mp = mod(horner([134.9633964, 477198.8675, 0.0087414, 1.434740814E-05, -6.797172376E-08], T), 360);
    const F = mod(horner([93.272095, 483202.0175, -0.0036539, -2.836074872E-07, 1.158332465E-09], T), 360);
    const E = horner([1, -0.002516, -7.4E-06], T);
    const acc = { 6: 0, 7: 0, 8: 0 };
    for (const [tab, rs, rc] of [[AD.ML, 6, 7], [AD.MB, 8, 8], [AD.MCL, 6, 6], [AD.MCB, 8, 8]]) {
      for (const [d, m, mp, f, cs, cc] of tab) {
        const arg = d * D + m * M + mp * Mp + f * F, e = E ** Math.abs(m);
        acc[rs] += cs * e * dsin(arg);
        acc[rc] += cc * e * dcos(arg);
      }
    }
    const A1 = T * 131.849 + 119.75;
    acc[6] += dsin(A1) * 3958 + dsin(Lp - F) * 1962 + dsin(T * 479264.29 + 53.09) * 318 + (T * 367.1904613 + 56.41732779);
    acc[8] += dsin(Lp) * -2235 + dsin(T * 481266.484 + 313.45) * 382 + dsin(A1 - F) * 175 + dsin(A1 + F) * 175 +
      dsin(Lp - Mp) * 127 + dsin(Lp + Mp) * -115 + (T * 40.04748125 + -9.463218981);
    const lam = acc[6] / 1e6 + Lp + s.dpsi / 3600, bet = acc[8] / 1e6, dist = acc[7] / 1000 + 385000.56;
    const dec = asin(dsin(bet) * dcos(s.eps) + dcos(bet) * dsin(s.eps) * dsin(lam)) * R2D;
    const ra = atan2(dsin(lam) * dcos(s.eps) - dtan(bet) * dsin(s.eps), dcos(lam)) * R2D;
    return [mod(s.aries - ra + 360, 360), dec, asin(6378.14 / dist) * R2D * 60, 358473400 / dist / 60];
  }

  const PSER = { 1: ['VNL', 'VNB', 'VNR'], 2: ['MAL', 'MAB', 'MAR'], 3: ['JUL', 'JUB', 'JUR'], 4: ['SAL', 'SAB', 'SAR'] };
  const PLANETS = { 1: 'VENUS', 2: 'MARS', 3: 'JUPITER', 4: 'SATURN' };

  // PLAN: p = 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn: [gha, dec, sha, hp'] at JD j (UT)
  function planet(j, p, s) {
    s = s || sun(j);
    const T = s.T, tau = T / 10;
    const L0 = ser(AD.EEL, tau), B0 = ser(AD.EEB, tau), R0 = ser(AD.EER, tau);
    const [sl, sb, sr] = PSER[p].map(n => AD[n]);
    let lt = 0, x, y, z, dist;
    for (let k = 0; k < 2; k++) {
      const tp = tau - lt / 365250;
      const L = ser(sl, tp), B = ser(sb, tp), R = ser(sr, tp);
      x = R * cos(B) * cos(L) - R0 * cos(B0) * cos(L0);
      y = R * cos(B) * sin(L) - R0 * cos(B0) * sin(L0);
      z = R * sin(B) - R0 * sin(B0);
      dist = (x * x + y * y + z * z) ** 0.5;
      lt = dist * 0.0057755183;
    }
    let lam = mod(atan2(y, x) * R2D + 360, 360), bet = atan2(z, Math.hypot(x, y)) * R2D;
    const lp = lam - T * 1.397;                                          // FK5
    lam += ((dcos(lp) + dsin(lp)) * dtan(bet) * 0.03916 - 0.09033) / 3600;
    bet += (dcos(lp) - dsin(lp)) * 0.03916 / 3600;
    const sn = L0 * 57.29577951308232 + 180, e = T * -0.000042037 + 0.016708634, pi = T * 1.71946 + 102.93735;
    lam += ((dcos(sn - lam) * -20.49552 + dcos(pi - lam) * e * 20.49552) / dcos(bet) + s.dpsi) / 3600;   // aberration
    bet += (dsin(sn - lam) - dsin(pi - lam) * e) * dsin(bet) * -20.49552 / 3600;
    const dec = asin(dsin(bet) * dcos(s.eps) + dcos(bet) * dsin(s.eps) * dsin(lam)) * R2D;
    const ra = mod(atan2(dsin(lam) * dcos(s.eps) - dtan(bet) * dsin(s.eps), dcos(lam)) * R2D + 360, 360);
    return [mod(s.aries - ra + 360, 360), dec, mod(360 - ra, 360), 8.794 / dist / 60];
  }

  root.NAV = { jd, sun, star, event, phase, hcz, bodies, cal, almanac, phaseIndex, daylight, moonword,
    fdm, fns, fzn, fhm, f1, fdate, moon, phaseTime, moonPage, moonPos, planet, PLANETS, SN, BR, NBODY, EVENTS, NAMES, LUN };
})(typeof window !== 'undefined' ? window : globalThis);
