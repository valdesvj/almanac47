// app.js - Almanac 47 on the web: the ALMANAC page, the sky, the 58 stars, the Sun's day, MOON47.
// The engine is nav.js (python/nav.py and moon47.py); Zones 47 is zones.js. Time = UT (UT1).
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const p2 = x => String(x).padStart(2, '0');
  const mod = (x, m) => ((x % m) + m) % m;
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem('a47.' + k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem('a47.' + k, JSON.stringify(v)); } catch (e) { /* no storage */ } },
  };
  const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const jdNow = () => Date.now() / 864e5 + 2440587.5;

  const S = { live: true, j: jdNow(), pos: [27.2, 49.7], posText: '27 12.0N 049 42.0E', zd: null, view: 'almanac', south: false,
    style: 'modern', cview: 'ALMANAC', skymode: 'horizon' };

  // ---- inputs ----
  function parsePos(s) {
    const t = s.toUpperCase().replace(/[°′'″"]/g, ' ').replace(/([NSEW])/g, ' $1 ').trim().split(/[\s,;]+/);
    const parts = []; let cur = [];
    for (const x of t) { if (x.length === 1 && 'NSEW'.includes(x)) { cur.push(x); parts.push(cur); cur = []; } else if (x) cur.push(x); }
    if (cur.length) parts.push(cur);
    let vals;
    if (parts.length === 1 && parts[0].length === 2) vals = parts[0].map(x => [x]);
    else if (parts.length === 1 && parts[0].length === 4) vals = [parts[0].slice(0, 2), parts[0].slice(2)];
    else vals = parts;
    if (vals.length !== 2) return null;
    const conv = p => {
      let sign = 1; const nums = [];
      for (const x of p) { if (x === 'S' || x === 'W') sign = -1; else if (x !== 'N' && x !== 'E') nums.push(parseFloat(x)); }
      if (!nums.length || nums.some(isNaN)) return NaN;
      const v = Math.abs(nums[0]) + (nums[1] || 0) / 60 + (nums[2] || 0) / 3600;
      return sign * (nums[0] < 0 || Object.is(nums[0], -0) ? -v : v);
    };
    const lat = conv(vals[0]), lon = conv(vals[1]);
    return isNaN(lat) || isNaN(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180 ? null : [lat, lon];
  }
  const zdOf = () => S.zd !== null ? S.zd : -Math.round(S.pos[1] / 15);
  const zdText = zd => zd === 0 ? '0' : (zd > 0 ? '+' : '−') + Math.abs(zd);
  const zt = ut => ut === null || ut === undefined ? null : mod(ut - zdOf(), 24);
  const latText = v => NAV.fns(v, 'NS', 0).replace(/^([NS])\s*/, '$1 ');
  const lonText = v => NAV.fns(v, 'EW', 0).replace(/^([EW])\s*/, '$1 ');
  const dm = v => NAV.fdm(v) + '′';
  // the times of the day's events: UT, or LT = the zone time of the ZD (ZT + ZD = UT), for that local day
  const ltMode = () => S.tmode === 'lt';
  const tLabel = () => ltMode() ? `LT (ZD ${zdText(zdOf())})` : 'UT';
  function dayEvent(lat, lon, k) {
    if (!ltMode()) return NAV.event(Math.trunc(S.j - 0.5) + 0.5, lat, lon, k);
    const zd = zdOf(), jl = Math.trunc(S.j - zd / 24 - 0.5) + 0.5;      // 0h of the local date, as a UT day
    for (const d of [0, -1, 1]) {
      const u = NAV.event(jl + d, lat, lon, k);
      if (u === null || u === undefined) continue;
      const t = u + 24 * d - zd;
      if (t >= 0 && t < 24) return t;
    }
    return null;
  }

  function setInputs() {
    const [y, m, d, h] = NAV.cal(S.j + 0.5 / 86400);      // to the nearest second (16:00:00, not 15:59:59)
    $('date').value = `${y}-${p2(m)}-${p2(d)}`;
    const s = Math.floor(h * 3600);
    $('time').value = `${p2(Math.floor(s / 3600) % 24)}:${p2(Math.floor(s / 60) % 60)}:${p2(s % 60)}`;
    $('live').classList.toggle('on', S.live);
    $('tmode').textContent = ltMode() ? 'Times: LT' : 'Times: UT';
    $('tmode').classList.toggle('on', ltMode());
  }

  // ---- views ----
  const VIEWS = [
    { id: 'almanac', label: 'Almanac', render: renderAlmanac },
    { id: 'sky', label: 'Sky', render: renderSky },
    { id: 'stars', label: 'Stars', render: renderStars },
    { id: 'sun', label: 'Sun', render: renderSun },
    { id: 'moon', label: 'Moon', render: renderMoon },
  ];
  function addView(v) {
    VIEWS.push(v);
    buildTabs();
  }
  const CORE = ['almanac', 'sky', 'stars', 'sun', 'moon'];
  function buildTabs() {
    const calc = S.style === 'calc' && globalThis.A47.CALC;
    let h = '';
    if (calc) {
      h = calc.VIEWS.map(c => `<button class="tab${S.view === 'calc' && S.cview === c ? ' on' : ''}" data-c="${c}" title="${calc.HINT[c]}">${c}</button>`).join('');
      h += VIEWS.filter(v => !CORE.includes(v.id)).map(v => `<button class="tab${v.id === S.view ? ' on' : ''}" data-v="${v.id}">${v.label.toUpperCase()}</button>`).join('');
    } else {
      h = VIEWS.map(v => `<button class="tab${v.id === S.view ? ' on' : ''}" data-v="${v.id}">${v.label}</button>`).join('');
    }
    $('tabs').innerHTML = h;
    $('tabs').querySelectorAll('button[data-v]').forEach(b => { b.onclick = () => { S.view = b.dataset.v; store.set(calc ? 'cview2' : 'view', S.view); buildTabs(); render(); }; });
    $('tabs').querySelectorAll('button[data-c]').forEach(b => { b.onclick = () => setCview(b.dataset.c); });
  }
  function setCview(c) { S.view = 'calc'; S.cview = c; store.set('cview', c); store.set('cview2', 'calc'); buildTabs(); render(); }
  function setStyle(st) {
    S.style = st; store.set('style', st);
    document.documentElement.dataset.style = st;
    $('style').value = st;
    if (st === 'calc') { S.view = store.get('cview2') || 'calc'; if (S.view !== 'calc' && !VIEWS.some(v => v.id === S.view && !CORE.includes(v.id))) S.view = 'calc'; }
    else { S.view = store.get('view') || 'almanac'; if (S.view === 'calc') S.view = 'almanac'; }
    buildTabs(); render();
  }

  function headCard(title, extra) {
    const [y, m, d, h] = NAV.cal(S.j);
    const wd = DAYS[mod(Math.floor(S.j + 1.5), 7)];
    const ztH = zt(h);
    return `<div class="title"><h2>${title}</h2><div class="big">${wd} ${p2(d)}-${p2(m)}-${y}</div></div>` +
      `<div class="meta">${NAV.fhm(h)} UT · ZT ${NAV.fhm(ztH)} (ZD ${zdText(zdOf())}) · DR ${latText(S.pos[0])}′ ${lonText(S.pos[1])}′${extra ? ' · ' + extra : ''}</div>`;
  }

  // ---- the Sun, the Moon, the planets and the stars, with their symbols ----
  const SYM = { SUN: '☉', MOON: '☾', VENUS: '♀', MARS: '♂', JUPITER: '♃', SATURN: '♄' };
  const symCls = n => n === 'SUN' ? 'sun' : n === 'MOON' ? 'moon' : SYM[n] ? 'pl' : 'star';
  const sym = n => `<span class="sym ${symCls(n)}">${SYM[n] || '★'}</span>`;
  // Sun, Moon, Venus, Mars, Jupiter, Saturn now: {name, g, d, hc, zn, hp}
  function solar(s) {
    s = s || NAV.sun(S.j);
    const out = [{ name: 'SUN', g: s.gha, d: s.dec, sd: s.sd }];
    const m = NAV.moonPos(S.j, s);
    out.push({ name: 'MOON', g: m[0], d: m[1], hp: m[2], sd: m[3] });
    for (const p of [1, 2, 3, 4]) { const q = NAV.planet(S.j, p, s); out.push({ name: NAV.PLANETS[p], g: q[0], d: q[1], hp: q[3] }); }
    for (const b of out) [b.hc, b.zn] = NAV.hcz(S.pos[0], S.pos[1], b.d, b.g);
    return out;
  }

  function renderAlmanac(el) {
    const [lat, lon] = S.pos;
    const [head, tab, foot] = NAV.almanac(S.j, lat, lon);
    const sun = tab[0];
    const dl = NAV.daylight(sun[6]);
    let h = headCard('Almanac', 'GHA Aries ' + head[4] + '′');
    h += `<div class="chips"><span class="chip now">${dl}</span><span class="chip">Sun Hc ${sun[4]}′ Zn ${sun[5]}°</span>` +
      `<span class="chip">Moon ${foot[6]} % ${foot[7]}, age ${foot[8]} d</span></div>`;
    h += '<div class="scroll"><table><tr><th>Body</th><th class="num">GHA</th><th class="num">Dec</th><th class="num">Hc</th><th class="num">Zn</th></tr>';
    h += `<tr><td>ARIES</td><td class="num mono">${head[4]}′</td><td></td><td></td><td></td></tr>`;
    const sol = solar();
    const row = (cls, name, label, g, d, hc, zn) => `<tr class="${cls}"><td>${sym(name)} ${label}</td><td class="num mono">${g}′</td>` +
      `<td class="num mono">${d}′</td><td class="num mono">${hc}′</td><td class="num mono">${zn}°</td></tr>`;
    tab.forEach(([k, nm, g, d, hc, zn], i) => {
      h += row('', nm, `${k ? `<span class="meta">${p2(k)}</span> ` : ''}${nm}`, g, d, hc, zn);
      if (i === 0) {
        for (const b of sol.slice(1)) {
          h += row(b.hc < 0 ? 'dim' : '', b.name, b.name + (b.name === 'MOON' ? ` <span class="meta">HP ${NAV.f1(b.hp)}′</span>` : ''),
            NAV.fdm(b.g), NAV.fns(b.d), NAV.fdm(b.hc), NAV.fzn(b.zn));
        }
      }
    });
    h += '</table></div>';
    h += `<table><tr><th>Sun, ${tLabel()}</th>` + '<th class="num">Naut twi</th><th class="num">Rise</th><th class="num">Mer pass</th><th class="num">Set</th><th class="num">Naut twi</th><th class="num">SD</th></tr>';
    const both = k => NAV.fhm(dayEvent(lat, lon, k));
    h += `<tr><td>this day</td><td class="num mono">${both('nauam')}</td><td class="num mono">${both('rise')}</td>` +
      `<td class="num mono">${both('tran')}</td><td class="num mono">${both('set')}</td><td class="num mono">${both('naupm')}</td>` +
      `<td class="num mono">${foot[5]}′</td></tr></table>`;
    h += '<div class="meta">The Sun, the Moon and the planets (grey: below the horizon), then the brightest stars more than 10° high, ' +
      'as on the C47\'s ALMANAC page. ☉ Sun · ☾ Moon · ♀ Venus · ♂ Mars · ♃ Jupiter · ♄ Saturn · ★ star.</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
  }

  function starsNow() {
    const s = NAV.sun(S.j);
    const out = [];
    for (let n = 1; n <= 58; n++) {
      const [g, d, sha] = NAV.star(S.j, n, s);
      const [hc, zn] = NAV.hcz(S.pos[0], S.pos[1], d, g);
      out.push({ n, name: NAV.SN[n - 1], g, d, sha, hc, zn, rank: NAV.BR.indexOf(n) });
    }
    return [out, s];
  }

  // The original Alma47 sky (the C47's CHART / SKY / ALLSKY): azimuth across (N E S W N; S W N E S south of the
  // equator), altitude up on the sine scale (marks at 10 20 30 45 60 90), the celestial equator dotted, the bodies
  // with their symbols and the stars with their almanac numbers. All sky: below the horizon too, mirrored.
  // the Sky tab's three ways: the horizon chart, the whole sky (ALLSKY), the dome (zenith in the centre)
  const skyModes = () => [['horizon', 'Above the horizon'], ['all', 'All sky'], ['dome', 'Dome']].map(([m, t]) =>
    `<button class="skym${S.skymode === m ? ' on' : ''}" data-m="${m}">${t}</button>`).join('');
  const bindModes = () => document.querySelectorAll('button.skym').forEach(b => {
    b.onclick = () => { S.skymode = b.dataset.m; store.set('skymode', S.skymode); render(); };
  });

  function renderSky(el) {
    if (S.skymode === 'dome') return renderDome(el);
    const [stars, s] = starsNow();
    const sol = solar(s);
    const sun = sol[0];
    const dl = NAV.daylight(sun.hc);
    const all = S.skymode === 'all';
    const W = Math.round(Math.min(1000, (el.getBoundingClientRect().width || 900) - 34));
    const L = 34, R = W - 14, T = 22, HS = Math.round((W - 48) * (all ? 0.22 : 0.4));
    const HB = T + HS, H = HB + (all ? HS : 0) + 34;
    const off = S.pos[0] < 0 ? 180 : 0;
    const X = zn => L + mod(zn + off, 360) / 360 * (R - L);
    const Y = hc => HB - Math.sin(hc * Math.PI / 180) * HS;
    const vint = S.style === 'vintage';
    const bg = vint ? 'var(--sky-night)' : dl === 'DAY' ? 'var(--sky-day)' : dl === 'TWILIGHT' ? 'var(--sky-twi)' : 'var(--sky-night)';
    const fg = vint || dl === 'DAY' ? 'var(--ink)' : '#e7ebf0';
    const night = !vint && dl !== 'DAY';
    let g = `<rect x="${L}" y="${T - 8}" width="${R - L}" height="${HS + 8}" fill="${bg}"/>`;
    if (all) g += `<rect x="${L}" y="${HB}" width="${R - L}" height="${HS}" fill="${bg}" opacity="0.55"/>`;
    // altitude marks
    for (const v of [10, 20, 30, 45, 60, 90]) {
      for (const sg of all ? [1, -1] : [1]) {
        const y = Y(v * sg);
        g += `<line x1="${L - 4}" x2="${L}" y1="${y}" y2="${y}" stroke="var(--soft)"/>` +
          `<line x1="${L}" x2="${R}" y1="${y}" y2="${y}" stroke="${fg}" stroke-opacity="0.08"/>` +
          `<text x="${L - 6}" y="${y + 4}" text-anchor="end" font-size="11" fill="var(--soft)">${v}</text>`;
      }
    }
    g += `<line x1="${L}" x2="${L}" y1="${T - 8}" y2="${HB + (all ? HS : 0)}" stroke="var(--soft)" stroke-dasharray="1 3"/>`;
    g += `<line x1="${L}" x2="${R}" y1="${HB}" y2="${HB}" stroke="var(--ink)" stroke-width="1.5"/>`;
    const cards = off ? 'SWNES' : 'NESWN';
    for (let i = 0; i <= 12; i++) {
      const x = L + i / 12 * (R - L);
      g += `<line x1="${x}" x2="${x}" y1="${HB}" y2="${HB + 5}" stroke="var(--ink)"/>`;
      if (i % 3 === 0) g += `<text x="${x}" y="${HB + (all ? HS : 0) + 18}" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">${cards[i / 3]}</text>`;
    }
    // the celestial equator, dotted
    for (let gh = 0; gh < 360; gh += 2) {
      const [hc, zn] = NAV.hcz(S.pos[0], S.pos[1], 0, gh);
      if (hc > 0 || all) g += `<circle cx="${X(zn).toFixed(1)}" cy="${Y(hc).toFixed(1)}" r="1.1" fill="${fg}" fill-opacity="0.6"/>`;
    }
    // stars: ★ by brightness, the almanac number beside
    for (const st of stars.slice().sort((a, b) => b.rank - a.rank)) {
      if (st.hc <= 0 && !all) continue;
      const x = X(st.zn), y = Y(st.hc), fs = Math.max(9, 17 - st.rank / 5);
      const op = st.hc > 0 ? 1 : 0.55;
      g += `<text x="${x.toFixed(1)}" y="${(y + fs * 0.36).toFixed(1)}" text-anchor="middle" font-size="${fs.toFixed(1)}" fill="${fg}" fill-opacity="${op}">★<title>${st.n} ${st.name}  Hc ${NAV.fdm(st.hc)}′  Zn ${NAV.fzn(st.zn)}°</title></text>`;
      const right = x > R - 30;
      g += `<text x="${(right ? x - 7 : x + 7).toFixed(1)}" y="${(y + 4).toFixed(1)}" text-anchor="${right ? 'end' : 'start'}" font-size="10" fill="${fg}" fill-opacity="${0.8 * op}">${st.n}</text>`;
    }
    // the Sun, the Moon and the planets
    for (const b of sol.slice().reverse()) {
      if (b.hc <= 0 && !all && b.name !== 'SUN') continue;
      const hc = b.name === 'SUN' && !all ? Math.max(b.hc, 0) : b.hc;
      if (b.name === 'SUN' && !all && b.hc < -1) continue;
      const x = X(b.zn), y = Y(hc);
      const col = b.name === 'SUN' ? 'var(--sun)' : b.name === 'MOON' ? (night ? '#f2efe4' : 'var(--moon)') : (night ? '#9fd0ff' : 'var(--accent)');
      const fs = b.name === 'SUN' || b.name === 'MOON' ? 22 : 17;
      g += `<text x="${x.toFixed(1)}" y="${(y + fs * 0.35).toFixed(1)}" text-anchor="middle" font-size="${fs}" font-weight="700" fill="${col}">${SYM[b.name]}<title>${b.name}  Hc ${NAV.fdm(b.hc)}′  Zn ${NAV.fzn(b.zn)}°</title></text>`;
      const right = x > R - 80;
      g += `<text x="${(right ? x - 12 : x + 12).toFixed(1)}" y="${(y + 4).toFixed(1)}" text-anchor="${right ? 'end' : 'start'}" font-size="11" font-weight="600" fill="${col}">${b.name}</text>`;
    }
    // the bodies above the horizon, as the C47's CHART lists them
    const [, tab] = NAV.almanac(S.j, S.pos[0], S.pos[1]);
    let t = '<div class="scroll"><table><tr><th>Body</th><th class="num">Hc</th><th class="num">Zn</th></tr>';
    for (const b of sol.filter(b => b.hc > 0 || b.name === 'SUN')) t += `<tr><td>${sym(b.name)} ${b.name}</td><td class="num mono">${NAV.fdm(b.hc)}′</td><td class="num mono">${NAV.fzn(b.zn)}°</td></tr>`;
    for (const [k, nm, , , hc, zn] of tab.slice(1)) t += `<tr><td>${sym(nm)} <span class="meta">${p2(k)}</span> ${nm}</td><td class="num mono">${hc}′</td><td class="num mono">${zn}°</td></tr>`;
    t += '</table></div>';
    const up = stars.filter(x => x.hc > 10).length;
    el.innerHTML = `<section class="card">${headCard('Sky', dl)}<div class="chips"><span class="chip now">${dl}</span><span class="chip">${up} stars above 10°</span>` +
      `${skyModes()}</div>` +
      `<svg viewBox="0 0 ${W} ${H}" style="margin-top:8px">${g}</svg>${t}` +
      '<div class="meta">The Alma47 sky: azimuth across, altitude up on the C47\'s sine scale, the celestial equator dotted, ' +
      'the stars with their almanac numbers. Hover a body for its Hc and Zn. All sky (the ALLSKY view): below the horizon too; Dome: the zenith in the centre.</div></section>';
    bindModes();
  }

  function renderDome(el) {
    const [stars, s] = starsNow();
    const [shc, szn] = NAV.hcz(S.pos[0], S.pos[1], s.dec, s.gha);
    const dl = NAV.daylight(shc);
    const W = Math.round(Math.min(640, (el.getBoundingClientRect().width || 640) - 34));
    const R = W / 2 - 30, c = W / 2;
    const P = (hc, zn) => { const r = R * (90 - hc) / 90, a = zn * Math.PI / 180; return [c + r * Math.sin(a), c - r * Math.cos(a)]; };
    const bg = dl === 'DAY' ? 'var(--sky-day)' : dl === 'TWILIGHT' ? 'var(--sky-twi)' : 'var(--sky-night)';
    const fg = dl === 'DAY' ? '#1b2129' : '#e7ebf0';
    let g = `<circle cx="${c}" cy="${c}" r="${R}" fill="${bg}"/>`;
    for (const a of [30, 60]) g += `<circle cx="${c}" cy="${c}" r="${R * (90 - a) / 90}" fill="none" stroke="${fg}" stroke-opacity="0.25"/>`;
    for (let z = 0; z < 360; z += 30) { const [x, y] = P(0, z); g += `<line x1="${c}" y1="${c}" x2="${x}" y2="${y}" stroke="${fg}" stroke-opacity="0.12"/>`; }
    [['N', 0], ['E', 90], ['S', 180], ['W', 270]].forEach(([t, z]) => {
      const a = z * Math.PI / 180, x = c + (R + 16) * Math.sin(a), y = c - (R + 16) * Math.cos(a);
      g += `<text x="${x}" y="${y + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="var(--soft)">${t}</text>`;
    });
    for (const st of stars.filter(x => x.hc > 0).sort((a, b) => b.rank - a.rank)) {
      const [x, y] = P(st.hc, st.zn);
      const rr = Math.max(1.6, 5 - st.rank / 13);
      g += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rr.toFixed(1)}" fill="${fg}"><title>${st.n} ${st.name}  Hc ${NAV.fdm(st.hc)}′  Zn ${NAV.fzn(st.zn)}°</title></circle>`;
      const right = x > c + R * 0.55;
      if (st.rank < 24) g += `<text x="${(right ? x - rr - 3 : x + rr + 3).toFixed(1)}" y="${(y + 4).toFixed(1)}" text-anchor="${right ? 'end' : 'start'}" font-size="11" fill="${fg}" fill-opacity="0.85">${st.name}</text>`;
    }
    if (shc > -1) {
      const [x, y] = P(Math.max(shc, 0), szn);
      g += `<circle cx="${x}" cy="${y}" r="9" fill="var(--sun)"/><text x="${x + 12}" y="${y + 4}" font-size="12" font-weight="700" fill="${fg}">SUN</text>`;
    }
    for (const b of solar(s).slice(1)) {
      if (b.hc <= 0) continue;
      const [x, y] = P(b.hc, b.zn);
      const col = b.name === 'MOON' ? (dl === 'DAY' ? 'var(--moon)' : '#f2efe4') : (dl === 'DAY' ? 'var(--accent)' : '#9fd0ff');
      g += `<text x="${x.toFixed(1)}" y="${(y + 7).toFixed(1)}" text-anchor="middle" font-size="${b.name === 'MOON' ? 22 : 18}" font-weight="700" fill="${col}">${SYM[b.name]}<title>${b.name}  Hc ${NAV.fdm(b.hc)}′  Zn ${NAV.fzn(b.zn)}°</title></text>` +
        `<text x="${(x + 12).toFixed(1)}" y="${(y + 4).toFixed(1)}" font-size="11" font-weight="600" fill="${col}">${b.name}</text>`;
    }
    g += `<circle cx="${c}" cy="${c}" r="${R}" fill="none" stroke="var(--soft)"/>`;
    const up = stars.filter(x => x.hc > 10).length;
    el.innerHTML = `<section class="card">${headCard('Sky', dl)}<div class="chips"><span class="chip">${up} stars above 10°</span>` +
      `<span class="chip">Sun Hc ${NAV.fdm(shc)}′ Zn ${NAV.fzn(szn)}°</span>${skyModes()}</div>` +
      `<svg viewBox="0 0 ${W} ${W}" style="max-width:${W}px;margin:8px auto 0">${g}</svg>` +
      '<div class="meta">The sky from the DR: the zenith at the centre, the horizon round the edge, north up (rings at 30° and 60°). Hover a star for its Hc and Zn.</div></section>';
    bindModes();
  }


  let sortKey = 'rank', sortDir = 1;
  function renderStars(el) {
    const [stars] = starsNow();
    const key = { n: x => x.n, name: x => x.name, sha: x => x.sha, gha: x => x.g, dec: x => x.d, hc: x => -x.hc, zn: x => x.zn, rank: x => x.rank }[sortKey];
    stars.sort((a, b) => { const A = key(a), B = key(b); return (A < B ? -1 : A > B ? 1 : 0) * sortDir; });
    const th = (k, t, cls) => `<th class="${cls || ''}" data-k="${k}" style="cursor:pointer">${t}${sortKey === k ? (sortDir > 0 ? ' ▴' : ' ▾') : ''}</th>`;
    let h = headCard('The 58 stars') + '<div class="scroll"><table><tr>' + th('n', 'No') + th('name', 'Star') + th('sha', 'SHA', 'num') + th('gha', 'GHA', 'num') +
      th('dec', 'Dec', 'num') + th('hc', 'Hc', 'num') + th('zn', 'Zn', 'num') + th('rank', 'Bright', 'num') + '</tr>';
    for (const s of stars) {
      h += `<tr class="${s.hc < 0 ? 'dim' : ''}"><td>${s.n === 58 ? '—' : s.n}</td><td>${sym(s.name)} ${s.name}</td><td class="num mono">${NAV.fdm(s.sha)}′</td>` +
        `<td class="num mono">${NAV.fdm(s.g)}′</td><td class="num mono">${NAV.fns(s.d)}′</td><td class="num mono">${NAV.fdm(s.hc)}′</td>` +
        `<td class="num mono">${NAV.fzn(s.zn)}°</td><td class="num">${s.rank + 1}</td></tr>`;
    }
    h += '</table></div><div class="meta">The 57 navigational stars and Polaris (58). Below the horizon: grey. Click a heading to sort.</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
    el.querySelectorAll('th[data-k]').forEach(t => { t.onclick = () => { if (sortKey === t.dataset.k) sortDir = -sortDir; else { sortKey = t.dataset.k; sortDir = 1; } renderStars(el); }; });
  }

  function renderSun(el) {
    const [lat, lon] = S.pos;
    const s = NAV.sun(S.j);
    const [hc, zn] = NAV.hcz(lat, lon, s.dec, s.gha);
    const rows = [['nauam', 'Nautical twilight (morning)'], ['civam', 'Civil twilight (morning)'], ['rise', 'Sunrise'],
      ['tran', 'Meridian passage'], ['set', 'Sunset'], ['civpm', 'Civil twilight (evening)'], ['naupm', 'Nautical twilight (evening)']];
    let h = headCard('Sun') + `<div class="chips"><span class="chip now">${NAV.daylight(hc)}</span></div>`;
    h += '<div class="two"><table><tr><th>Now</th><th class="num"></th></tr>' +
      `<tr><td>GHA</td><td class="num mono">${dm(s.gha)}</td></tr><tr><td>Dec</td><td class="num mono">${NAV.fns(s.dec)}′</td></tr>` +
      `<tr><td>SD</td><td class="num mono">${NAV.f1(s.sd)}′</td></tr><tr><td>Hc</td><td class="num mono">${dm(hc)}</td></tr>` +
      `<tr><td>Zn</td><td class="num mono">${NAV.fzn(zn)}°</td></tr><tr><td>GHA Aries</td><td class="num mono">${dm(s.aries)}</td></tr></table>`;
    h += `<table><tr><th>This day</th><th class="num">${tLabel()}</th></tr>`;
    for (const [k, t] of rows) h += `<tr><td>${t}</td><td class="num mono">${NAV.fhm(dayEvent(lat, lon, k))}</td></tr>`;
    h += '</table></div><div class="meta">Rise and set: the upper limb on the horizon (−50′); civil −6°, nautical −12°. --:-- = none this day.</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
  }

  function moonDisc(lit, age, south, r) {
    const k = lit / 100, c = r + 4, side = ((age < NAV.LUN / 2) !== south) ? 1 : -1;
    const rx = r * Math.abs(1 - 2 * k);
    const sw1 = side > 0 ? 1 : 0, sw2 = k < 0.5 ? (side > 0 ? 0 : 1) : (side > 0 ? 1 : 0);
    const path = `M${c} ${c - r}A${r} ${r} 0 0 ${sw1} ${c} ${c + r}A${rx.toFixed(2)} ${r} 0 0 ${sw2} ${c} ${c - r}Z`;
    return `<svg viewBox="0 0 ${2 * c} ${2 * c}" style="max-width:${2 * c}px;margin:0 auto"><circle cx="${c}" cy="${c}" r="${r}" fill="var(--sky-night)" stroke="var(--soft)"/>` +
      (k > 0.003 ? `<path d="${path}" fill="#f2efe4"/>` : '') + '</svg>';
  }

  function renderMoon(el) {
    const p = NAV.moonPage(S.j);
    let h = headCard('Moon') + '<div class="two"><div>' + moonDisc(p.lit, p.age, S.south, 110) +
      `<div style="text-align:center;margin-top:6px"><button id="south">${S.south ? 'Southern view' : 'Northern view'}</button></div></div><div>`;
    h += `<div class="big">${p.name}</div><table><tr><td>Lit</td><td class="num mono">${p.lit.toFixed(0)} %</td></tr>` +
      `<tr><td>Age</td><td class="num mono">${p.age.toFixed(1)} days</td></tr><tr><td>HP</td><td class="num mono">${p.hp.toFixed(1)}′</td></tr>` +
      `<tr><td>SD</td><td class="num mono">${p.sd.toFixed(1)}′</td></tr></table>`;
    const mo = solar()[1];
    h += `<table><tr><th>${sym('MOON')} Now</th><th class="num"></th></tr><tr><td>GHA</td><td class="num mono">${dm(mo.g)}</td></tr>` +
      `<tr><td>Dec</td><td class="num mono">${NAV.fns(mo.d)}′</td></tr><tr><td>Hc</td><td class="num mono">${dm(mo.hc)}</td></tr>` +
      `<tr><td>Zn</td><td class="num mono">${NAV.fzn(mo.zn)}°</td></tr></table>`;
    h += `<table><tr><th>Next</th><th class="num">${tLabel()}</th></tr>`;
    for (const [t, name] of p.next) {
      const [, m, d, hh] = NAV.cal(ltMode() ? t - zdOf() / 24 : t);
      h += `<tr><td>${name}</td><td class="num mono">${p2(d)}-${p2(m)} ${NAV.fhm(hh)}</td></tr>`;
    }
    h += '</table></div></div><div class="meta">MOON47: 20 terms of Meeus ch. 47; the phase does not depend on the place. HP and SD for the altitude corrections. ' +
      'GHA, Dec, Hc and Zn: the full Moon of the C47 (Meeus 47 + the DE421 terms).</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
    $('south').onclick = () => { S.south = !S.south; store.set('south', S.south); render(); };
  }

  // ---- the loop ----
  function render() {
    if (S.live) S.j = jdNow();
    setInputs();
    const el = $('views');
    el.classList.toggle('wide', S.view === 'route');
    if (S.style === 'calc' && S.view === 'calc' && globalThis.A47.CALC) return globalThis.A47.CALC.render(el, S);
    const v = VIEWS.find(x => x.id === S.view) || VIEWS[0];
    v.render(el, S);
  }

  function bind() {
    // Now: back to the clock (a second press stops it); the time ticks every second, the view follows
    $('live').onclick = () => { S.live = !S.live; S.j = jdNow(); render(); };
    const fromInputs = () => {
      const [y, m, d] = $('date').value.split('-').map(Number);
      const [hh, mm, ss] = ($('time').value || '0:0:0').split(':').map(Number);
      if (!y) return;
      S.live = false; S.j = NAV.jd(y, m, d, hh + (mm || 0) / 60 + (ss || 0) / 3600); render();
    };
    $('date').onchange = fromInputs; $('time').onchange = fromInputs;
    $('minus').onclick = () => { S.live = false; S.j -= 1 / 24; render(); };
    $('plus').onclick = () => { S.live = false; S.j += 1 / 24; render(); };
    $('pos').onchange = () => {
      const p = parsePos($('pos').value);
      $('pos').style.borderColor = p ? '' : 'var(--now)';
      if (p) { S.pos = p; S.posText = $('pos').value; store.set('pos', S.posText); render(); }
    };
    $('zd').onchange = () => {
      const t = $('zd').value.trim().replace('−', '-');
      S.zd = t === '' ? null : Math.round(parseFloat(t) * 4) / 4;
      if (S.zd !== null && isNaN(S.zd)) S.zd = null;
      store.set('zd', S.zd); render();
    };
    $('style').onchange = () => setStyle($('style').value);
    $('tmode').onclick = () => { S.tmode = ltMode() ? 'ut' : 'lt'; store.set('tmode', S.tmode); render(); };
    document.addEventListener('keydown', e => {
      if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
      if (e.key === '+' || e.key === '=') { S.live = false; S.j += 1 / 24; render(); }
      else if (e.key === '-') { S.live = false; S.j -= 1 / 24; render(); }
    });
    let rt = null;
    window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(render, 150); });
    let ticks = 0;
    setInterval(() => {
      if (!S.live) return;
      S.j = jdNow();
      const busy = document.activeElement && $('views').contains(document.activeElement) &&
        /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
      const every = S.style === 'calc' && S.view === 'calc' ? 10 : 5;         // the views every 5 s (the C47 screens 10 s)
      if (++ticks % every === 0 && !busy && S.view !== 'route') render();
      else if (!['date', 'time'].includes(document.activeElement && document.activeElement.id)) setInputs();
    }, 1000);
  }

  // ---- start ----
  const pos = store.get('pos');
  if (pos && parsePos(pos)) { S.pos = parsePos(pos); S.posText = pos; }
  $('pos').value = S.posText;
  S.zd = store.get('zd'); if (S.zd !== null && S.zd !== undefined) $('zd').value = S.zd; else S.zd = null;
  S.south = !!store.get('south');
  S.tmode = store.get('tmode') === 'lt' ? 'lt' : 'ut';
  S.skymode = ['horizon', 'all', 'dome'].includes(store.get('skymode')) ? store.get('skymode') : 'horizon';
  S.cview = store.get('cview') || 'ALMANAC';
  globalThis.A47 = { S, addView, render, store, headCard, p2, mod, zdOf, zdText, DAYS, setStyle, setCview, SYM, sym, parsePos };
  bind();
  // calc.js and zones.js add themselves, then the style and the first render
  setTimeout(() => setStyle(['modern', 'vintage', 'calc'].includes(store.get('style')) ? store.get('style') : 'modern'), 0);
})();
