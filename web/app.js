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

  const S = { live: true, j: jdNow(), pos: [27.2, 49.7], posText: '27 12.0N 049 42.0E', zd: null, view: 'almanac', south: false };

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

  function setInputs() {
    const [y, m, d, h] = NAV.cal(S.j);
    $('date').value = `${y}-${p2(m)}-${p2(d)}`;
    const s = Math.floor(h * 3600 + 1e-6);
    $('time').value = `${p2(Math.floor(s / 3600) % 24)}:${p2(Math.floor(s / 60) % 60)}:${p2(s % 60)}`;
    $('live').classList.toggle('on', S.live);
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
  function buildTabs() {
    $('tabs').innerHTML = VIEWS.map(v => `<button class="tab${v.id === S.view ? ' on' : ''}" data-v="${v.id}">${v.label}</button>`).join('');
    $('tabs').querySelectorAll('button').forEach(b => { b.onclick = () => { S.view = b.dataset.v; store.set('view', S.view); buildTabs(); render(); }; });
  }

  function headCard(title, extra) {
    const [y, m, d, h] = NAV.cal(S.j);
    const wd = DAYS[mod(Math.floor(S.j + 1.5), 7)];
    const ztH = zt(h);
    return `<div class="title"><h2>${title}</h2><div class="big">${wd} ${p2(d)}-${p2(m)}-${y}</div></div>` +
      `<div class="meta">${NAV.fhm(h)} UT · ZT ${NAV.fhm(ztH)} (ZD ${zdText(zdOf())}) · DR ${latText(S.pos[0])}′ ${lonText(S.pos[1])}′${extra ? ' · ' + extra : ''}</div>`;
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
    for (const [k, nm, g, d, hc, zn] of tab) {
      h += `<tr><td>${k ? `<span class="meta">${p2(k)}</span> ` : ''}${nm}</td><td class="num mono">${g}′</td><td class="num mono">${d}′</td>` +
        `<td class="num mono">${hc}′</td><td class="num mono">${zn}°</td></tr>`;
    }
    h += '</table></div>';
    h += '<table><tr><th>Sun (UT / ZT)</th><th class="num">Naut twi</th><th class="num">Rise</th><th class="num">Mer pass</th><th class="num">Set</th><th class="num">Naut twi</th><th class="num">SD</th></tr>';
    const j0 = Math.trunc(S.j - 0.5) + 0.5;
    const ev = k => NAV.event(j0, lat, lon, k);
    const both = k => { const u = ev(k); return `${NAV.fhm(u)}<br><span class="meta">${NAV.fhm(zt(u))}</span>`; };
    h += `<tr><td>this day</td><td class="num mono">${both('nauam')}</td><td class="num mono">${both('rise')}</td>` +
      `<td class="num mono">${both('tran')}</td><td class="num mono">${both('set')}</td><td class="num mono">${both('naupm')}</td>` +
      `<td class="num mono">${foot[5]}′</td></tr></table>`;
    h += '<div class="meta">The Sun, then the brightest stars more than 10° high: the C47\'s ALMANAC page (ALMF).</div>';
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

  function renderSky(el) {
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
    g += `<circle cx="${c}" cy="${c}" r="${R}" fill="none" stroke="var(--soft)"/>`;
    const up = stars.filter(x => x.hc > 10).length;
    el.innerHTML = `<section class="card">${headCard('Sky', dl)}<div class="chips"><span class="chip">${up} stars above 10°</span>` +
      `<span class="chip">Sun Hc ${NAV.fdm(shc)}′ Zn ${NAV.fzn(szn)}°</span></div>` +
      `<svg viewBox="0 0 ${W} ${W}" style="max-width:${W}px;margin:8px auto 0">${g}</svg>` +
      '<div class="meta">The sky from the DR: the zenith at the centre, the horizon round the edge, north up (rings at 30° and 60°). Hover a star for its Hc and Zn.</div></section>';
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
      h += `<tr class="${s.hc < 0 ? 'dim' : ''}"><td>${s.n === 58 ? '—' : s.n}</td><td>${s.name}</td><td class="num mono">${NAV.fdm(s.sha)}′</td>` +
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
    const j0 = Math.trunc(S.j - 0.5) + 0.5;
    const rows = [['nauam', 'Nautical twilight (morning)'], ['civam', 'Civil twilight (morning)'], ['rise', 'Sunrise'],
      ['tran', 'Meridian passage'], ['set', 'Sunset'], ['civpm', 'Civil twilight (evening)'], ['naupm', 'Nautical twilight (evening)']];
    let h = headCard('Sun') + `<div class="chips"><span class="chip now">${NAV.daylight(hc)}</span></div>`;
    h += '<div class="two"><table><tr><th>Now</th><th class="num"></th></tr>' +
      `<tr><td>GHA</td><td class="num mono">${dm(s.gha)}</td></tr><tr><td>Dec</td><td class="num mono">${NAV.fns(s.dec)}′</td></tr>` +
      `<tr><td>SD</td><td class="num mono">${NAV.f1(s.sd)}′</td></tr><tr><td>Hc</td><td class="num mono">${dm(hc)}</td></tr>` +
      `<tr><td>Zn</td><td class="num mono">${NAV.fzn(zn)}°</td></tr><tr><td>GHA Aries</td><td class="num mono">${dm(s.aries)}</td></tr></table>`;
    h += '<table><tr><th>This day</th><th class="num">UT</th><th class="num">ZT</th></tr>';
    for (const [k, t] of rows) { const u = NAV.event(j0, lat, lon, k); h += `<tr><td>${t}</td><td class="num mono">${NAV.fhm(u)}</td><td class="num mono">${NAV.fhm(zt(u))}</td></tr>`; }
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
    h += '<table><tr><th>Next</th><th class="num">UT</th><th class="num">ZT</th></tr>';
    for (const [t, name] of p.next) {
      const [y, m, d, hh] = NAV.cal(t);
      const [y2, m2, d2] = NAV.cal(t - zdOf() / 24);
      h += `<tr><td>${name}</td><td class="num mono">${p2(d)}-${p2(m)} ${NAV.fhm(hh)}</td><td class="num mono">${p2(d2)}-${p2(m2)} ${NAV.fhm(zt(hh))}</td></tr>`;
    }
    h += '</table></div></div><div class="meta">MOON47: 20 terms of Meeus ch. 47; the phase does not depend on the place. HP and SD for the altitude corrections.</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
    $('south').onclick = () => { S.south = !S.south; store.set('south', S.south); render(); };
  }

  // ---- the loop ----
  function render() {
    if (S.live) S.j = jdNow();
    setInputs();
    const v = VIEWS.find(x => x.id === S.view) || VIEWS[0];
    const el = $('views');
    v.render(el, S);
  }

  function bind() {
    $('live').onclick = () => { S.live = !S.live; render(); };
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
    let rt = null;
    window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(render, 150); });
    setInterval(() => { if (S.live) render(); }, 15000);
  }

  // ---- start ----
  const pos = store.get('pos');
  if (pos && parsePos(pos)) { S.pos = parsePos(pos); S.posText = pos; }
  $('pos').value = S.posText;
  S.zd = store.get('zd'); if (S.zd !== null && S.zd !== undefined) $('zd').value = S.zd; else S.zd = null;
  S.south = !!store.get('south');
  S.view = store.get('view') || 'almanac';
  globalThis.A47 = { S, addView, render, store, headCard, p2, mod, zdOf, zdText, DAYS };
  buildTabs(); bind();
  // zones.js adds its view, then the first render
  setTimeout(render, 0);
})();
