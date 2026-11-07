// zones.js - Zones 47 on the web: ZONE47's dot map of the world in 24 columns of 15°, the official standard
// offsets (IANA tzdata, from github.com/valdesvj/zones47), each stop's cities with their local time and daylight
// saving now (the browser's own tz database through Intl), and your own zone.
(function () {
  'use strict';
  const A = globalThis.A47, Z = globalThis.ZONEDATA;
  if (!A || !Z) return;
  const { S, p2, mod } = A;
  const stops = Z.zones.slice().sort((a, b) => a[0] - b[0]);
  let cur = null, city = 0;

  const offText = h => {
    if (h === 0) return 'UTC±0';
    const a = Math.abs(h), m = Math.round((a % 1) * 60);
    return 'UTC' + (h > 0 ? '+' : '−') + Math.floor(a) + (m ? ':' + p2(m) : '');
  };
  const dateOf = j => new Date((j - 2440587.5) * 864e5);

  // the city's local time and its offset now (hours), from the browser's tz database
  function local(tz, date) {
    try {
      const f = new Intl.DateTimeFormat('en-GB', { timeZone: tz, weekday: 'short', day: '2-digit', month: 'short',
        hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZoneName: 'longOffset' });
      const parts = Object.fromEntries(f.formatToParts(date).map(p => [p.type, p.value]));
      const m = /GMT([+-])(\d{2}):?(\d{2})?/.exec(parts.timeZoneName || '');
      const off = m ? (m[1] === '-' ? -1 : 1) * (+m[2] + (+m[3] || 0) / 60) : 0;
      return { text: `${parts.weekday} ${parts.day} ${parts.month} ${parts.hour}:${parts.minute}`, off };
    } catch (e) { return null; }
  }

  function yourStop() {
    const off = -new Date().getTimezoneOffset() / 60;
    let best = 0;
    stops.forEach((z, i) => { if (Math.abs(z[0] - off) < Math.abs(stops[best][0] - off)) best = i; });
    return best;
  }

  function render(el) {
    if (cur === null) {
      cur = A.store.get('zone');
      if (cur === null || cur >= stops.length) cur = yourStop();
    }
    const [off, col, cities] = stops[cur];
    city = Math.min(city, cities.length - 1);
    const date = dateOf(S.j);
    const mine = yourStop();
    // the map
    const W = Math.round(Math.min(1060, (el.getBoundingClientRect().width || 1000) - 34));
    const dx = W / Z.ncol, dy = dx, H = Math.round(Z.nrow * dy + 34);
    let g = '';
    for (let j = 0; j < Z.ncol; j++) {
      const bits = BigInt('0x' + Z.cols[j]);
      const hi = Math.floor(j / 5) === col;
      for (let i = 0; i < Z.nrow; i++) {
        const land = (bits >> BigInt(i)) & 1n;
        const x = (j + 0.5) * dx, y = (i + 0.5) * dy;
        if (land) g += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(dx * 0.38).toFixed(2)}" fill="${hi ? 'var(--land-hi)' : 'var(--land)'}"/>`;
        else if (hi) g += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(dx * 0.16).toFixed(2)}" fill="var(--land-hi)" opacity="0.45"/>`;
      }
    }
    for (let c = 0; c < 24; c++) {
      const x = c * 5 * dx;
      g += `<line x1="${x}" x2="${x}" y1="0" y2="${Z.nrow * dy}" stroke="var(--grid)"/>`;
      const z = c - 11;                 // column 0 = UTC-11 ... 23 = UTC+12
      g += `<text x="${x + 2.5 * dx}" y="${Z.nrow * dy + 14}" text-anchor="middle" font-size="${dx > 6 ? 11 : 9}" fill="${c === col ? 'var(--accent)' : 'var(--soft)'}" font-weight="${c === col ? 700 : 400}">${z > 0 ? '+' + z : z}</text>`;
      g += `<rect x="${x}" y="0" width="${5 * dx}" height="${Z.nrow * dy + 18}" fill="transparent" data-c="${c}" style="cursor:pointer"/>`;
    }
    const mc = stops[mine][1];
    g += `<path d="M${(mc * 5 + 2.5) * dx} ${Z.nrow * dy + 18}l6 9h-12z" fill="var(--now)"><title>your zone</title></path>`;
    // the stop and its cities
    const c0 = cities[city];
    const lc = local(c0[2], date);
    const dstNow = lc && Math.abs(lc.off - off) > 0.01;
    let h = `<div class="title"><h2>${offText(off)}${off === -12 ? ' at sea' : ''}</h2><div class="big">${lc ? lc.text : ''}</div></div>`;
    h += `<div class="meta">${cities.length} ${cities.length === 1 ? 'place' : 'places'} · stop ${cur + 1} of ${stops.length} · ` +
      `your clock ${offText(-new Date().getTimezoneOffset() / 60)} (▲) · IANA tzdata ${Z.tzdata}</div>`;
    h += `<div class="chips"><button id="zw">◀ west</button><button id="ze">east ▶</button><button id="zm">your zone</button>` +
      `<span class="chip now">${c0[0]}${c0[1] ? ' ' + c0[1] : ''}${dstNow ? ' · summer time ' + offText(lc.off) : c0[4] === 'irregular' ? ' · DST varies' : c0[3] ? ' · standard time now' : ''}</span></div>`;
    h += `<svg id="zmap" viewBox="0 0 ${W} ${H}" style="margin-top:8px">${g}</svg>`;
    h += '<div class="scroll"><table><tr><th>Place</th><th></th><th>Local time</th><th class="num">Offset now</th><th>DST</th></tr>';
    cities.forEach((c, k) => {
      const l = local(c[2], date);
      const d = l && Math.abs(l.off - off) > 0.01;
      h += `<tr class="click${k === city ? ' sel' : ''}" data-k="${k}"><td>${c[0]}</td><td class="meta">${c[1]}</td>` +
        `<td class="mono">${l ? l.text : '?'}</td><td class="num mono">${l ? offText(l.off) : ''}</td>` +
        `<td>${c[4] === 'irregular' ? 'varies' : c[3] ? (d ? 'summer now' : 'winter now') : ''}</td></tr>`;
    });
    h += '</table></div><div class="meta">Keys: ← → the stop west / east, ↑ ↓ the place. Click the map\'s column to jump to its zone. ' +
      'The stops: every official standard offset (37) plus −12 at sea; the highlighted column is the offset\'s own 15° (or the city\'s longitude).</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
    const go = i => { cur = mod(i, stops.length); city = 0; A.store.set('zone', cur); render(el); };
    el.querySelector('#zw').onclick = () => go(cur - 1);
    el.querySelector('#ze').onclick = () => go(cur + 1);
    el.querySelector('#zm').onclick = () => go(yourStop());
    el.querySelectorAll('tr[data-k]').forEach(tr => { tr.onclick = () => { city = +tr.dataset.k; render(el); }; });
    el.querySelectorAll('rect[data-c]').forEach(r => {
      r.onclick = () => {
        const c = +r.dataset.c;
        const i = stops.findIndex(z => z[1] === c && Number.isInteger(z[0]));
        go(i >= 0 ? i : stops.findIndex(z => z[1] === c));
      };
    });
  }

  document.addEventListener('keydown', e => {
    if (S.view !== 'zones' || e.target.tagName === 'INPUT') return;
    const el = document.getElementById('views');
    if (e.key === 'ArrowLeft') { cur = mod(cur - 1, stops.length); city = 0; }
    else if (e.key === 'ArrowRight') { cur = mod(cur + 1, stops.length); city = 0; }
    else if (e.key === 'ArrowDown') city = Math.min(city + 1, stops[cur][2].length - 1);
    else if (e.key === 'ArrowUp') city = Math.max(city - 1, 0);
    else return;
    e.preventDefault(); A.store.set('zone', cur); render(el);
  });

  A.addView({ id: 'zones', label: 'Zones', render });
})();
