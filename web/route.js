// route.js - passage planning, as NAV47's ROUTE (github.com/valdesvj/nav47.pg5, src/route.c): waypoints, the course
// and distance of each leg and the total, rhumb line (Mercator sailing with the meridional parts of the WGS84
// spheroid, Bowditch) or great circle (initial course); speed and ETD give the ETAs. The chart: GSHHG's coastline
// (data/coast.js, the full resolution of the Gulf, as GMT draws it), the ports, the oil and gas fields, and your
// platforms from a file (kept in this browser only) with their 500 m zones; a leg through a zone is flagged.
(function () {
  'use strict';
  const A = globalThis.A47, C = globalThis.COAST;
  if (!A) return;
  const { S, store, p2, mod } = A;
  const D2R = Math.PI / 180, R2D = 180 / Math.PI;

  // ---- NAV47 route.c ----
  const merParts = lat => { const s = Math.sin(lat * D2R); return 7915.7045 * Math.log10(Math.tan((45 + lat / 2) * D2R)) - 23.0133 * s - 0.0514 * s * s * s; };
  const dlonMin = (a, b) => { let d = (b - a) % 360; if (d > 180) d -= 360; if (d < -180) d += 360; return d * 60; };
  function legRL(la1, lo1, la2, lo2) {
    const dl = (la2 - la1) * 60, dlo = dlonMin(lo1, lo2);
    if (Math.abs(dl) < 1e-6) return [dlo > 0 ? 90 : dlo < 0 ? 270 : 0, Math.abs(dlo) * Math.cos(la1 * D2R)];
    const c = Math.atan2(dlo, merParts(la2) - merParts(la1));
    return [mod(c * R2D, 360), Math.abs(dl / Math.cos(c))];
  }
  function legGC(la1, lo1, la2, lo2) {
    const p1 = la1 * D2R, q2 = la2 * D2R, dlo = dlonMin(lo1, lo2) / 60 * D2R;
    const a = Math.sin((q2 - p1) / 2), b = Math.sin(dlo / 2);
    const h = a * a + Math.cos(p1) * Math.cos(q2) * b * b;
    const c = Math.atan2(Math.sin(dlo) * Math.cos(q2), Math.cos(p1) * Math.sin(q2) - Math.sin(p1) * Math.cos(q2) * Math.cos(dlo));
    return [mod(c * R2D, 360), 2 * Math.asin(Math.sqrt(Math.min(1, h))) * R2D * 60];
  }
  // points along a great circle (for drawing)
  function gcPoints(la1, lo1, la2, lo2, n) {
    const v = (la, lo) => [Math.cos(la * D2R) * Math.cos(lo * D2R), Math.cos(la * D2R) * Math.sin(lo * D2R), Math.sin(la * D2R)];
    const a = v(la1, lo1), b = v(la2, lo2);
    const w = Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2])));
    const out = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n, s = Math.sin(w) || 1;
      const k1 = w ? Math.sin((1 - t) * w) / s : 1 - t, k2 = w ? Math.sin(t * w) / s : t;
      const x = k1 * a[0] + k2 * b[0], y = k1 * a[1] + k2 * b[1], z = k1 * a[2] + k2 * b[2];
      let lo = Math.atan2(y, x) * R2D;
      if (out.length) { const pl = out[out.length - 1][1]; while (lo - pl > 180) lo -= 360; while (lo - pl < -180) lo += 360; }
      out.push([Math.atan2(z, Math.hypot(x, y)) * R2D, lo]);
    }
    return out;
  }

  // ---- places: public positions (approximate); your own files give the exact ones by the same name ----
  // ports: approximate public positions of the towns / terminals; fields: the field centres of the Global Energy
  // Monitor wiki (gem.wiki), WGS 84 - only to find your way on the chart, not the platforms
  const PORTS = [['Ras Tanura', 26.643, 50.160], ['Jubail', 27.012, 49.658], ['Abu Ali', 27.330, 49.550],
    ['Tanajib', 27.790, 48.880], ['Dammam', 26.450, 50.100], ['Al Khobar', 26.280, 50.210], ['Manama', 26.225, 50.585],
    ['Kuwait', 29.375, 47.980], ['Doha', 25.290, 51.535]];
  const FIELDS = [['Safaniya', 28.28, 48.75], ['Zuluf', 28.611, 49.059], ['Marjan', 28.4389, 49.6746], ['Manifa', 27.7159, 48.9834],
    ['Hasbah', 28.1477, 49.9194], ['Karan', 27.7233, 49.8257], ['Berri', 27.1145, 49.6389], ['Abu Safah', 26.79, 50.4312]];

  // ---- state ----
  const R = Object.assign({ gc: false, sog: 10, wps: [], mode: 'split', radius: 500, view: null, layers: { ports: 1, fields: 1, plats: 1, zones: 1 } },
    store.get('route') || {});
  let plats = loadPlats();                // [{name, lat, lon, kind}] from your files, this browser only
  let cur = 0, cv = null, last = null, drag = null, addMode = false;
  const save = () => store.set('route', R);
  function loadPlats() { try { return JSON.parse(localStorage.getItem('a47.platforms')) || []; } catch (e) { return []; } }
  function savePlats() { try { localStorage.setItem('a47.platforms', JSON.stringify(plats)); } catch (e) { /* no storage */ } }

  const fpos = (v, ns) => {
    const a = Math.abs(v), d = Math.floor(a + 1e-9), m = (a - d) * 60;
    const mm = m.toFixed(2) === '60.00' ? [d + 1, 0] : [d, m];
    return `${String(mm[0]).padStart(ns === 'NS' ? 2 : 3, '0')}°${mm[1].toFixed(2).padStart(5, '0')}′${v < 0 ? ns[1] : ns[0]}`;
  };

  // ---- the legs and their dangers ----
  function legs() {
    const out = []; let cum = 0;
    R.wps.forEach((w, i) => {
      if (!i) { out.push({ crs: null, nm: 0, cum: 0 }); return; }
      const p = R.wps[i - 1];
      const [crs, nm] = (R.gc ? legGC : legRL)(p.lat, p.lon, w.lat, w.lon);
      cum += nm;
      out.push({ crs, nm, cum, danger: dangers(p, w) });
    });
    return out;
  }
  // platforms closer to the leg than the zone (flat earth round the platform, nm)
  function dangers(a, b) {
    const r = R.radius / 1852, hits = [];
    for (const q of plats) {
      const k = Math.cos(q.lat * D2R);
      const ax = dlonMin(q.lon, a.lon) * k, ay = (a.lat - q.lat) * 60, bx = dlonMin(q.lon, b.lon) * k, by = (b.lat - q.lat) * 60;
      const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy;
      const t = L ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / L)) : 0;
      const d = Math.hypot(ax + t * dx, ay + t * dy);
      if (d < r) hits.push({ q, d, lat: a.lat + t * (b.lat - a.lat), lon: a.lon + t * dlonMin(a.lon, b.lon) / 60 });
    }
    return hits;
  }

  // ---- your files: platforms (CSV / text / KML / GPX / GeoJSON / tide47's private.js) and routes ----
  function parsePlaces(text, fname) {
    const out = [];
    const add = (name, lat, lon, kind) => { if (isFinite(lat) && isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180) out.push({ name: String(name || '').trim() || 'P' + (out.length + 1), lat, lon, kind: kind || 'platform' }); };
    const m = /T47PRIVATE\s*=\s*(\[[\s\S]*?\]);/.exec(text);
    if (m) { try { for (const s of JSON.parse(m[1])) add(s.name, +s.lat, +s.lon, 'station'); } catch (e) { /* not JSON */ } return out; }
    if (/<kml|<Placemark/i.test(text)) {
      for (const pm of text.split(/<Placemark/i).slice(1)) {
        const n = /<name>([\s\S]*?)<\/name>/i.exec(pm), c = /<coordinates>\s*([-\d.]+)\s*,\s*([-\d.]+)/i.exec(pm);
        if (c) add(n && n[1].replace(/<!\[CDATA\[|\]\]>/g, ''), +c[2], +c[1]);
      }
      return out;
    }
    if (/<gpx/i.test(text)) {
      const re = /<(?:wpt|rtept)[^>]*lat="([-\d.]+)"[^>]*lon="([-\d.]+)"[^>]*>([\s\S]*?)<\/(?:wpt|rtept)>/gi; let g;
      while ((g = re.exec(text))) { const n = /<name>([\s\S]*?)<\/name>/i.exec(g[3]); add(n && n[1], +g[1], +g[2]); }
      return out;
    }
    if (/^\s*[{[]/.test(text)) {
      try {
        const j = JSON.parse(text);
        for (const f of j.features || (Array.isArray(j) ? j : [])) {
          if (f.geometry && f.geometry.type === 'Point') add(f.properties && (f.properties.name || f.properties.Name), f.geometry.coordinates[1], f.geometry.coordinates[0]);
          else if (f.lat !== undefined) add(f.name, +f.lat, +f.lon);
        }
        return out;
      } catch (e) { /* not JSON: lines */ }
    }
    for (let ln of text.split(/\r?\n/)) {
      ln = ln.replace(/#.*$/, '').trim();
      if (!ln || /^(name|platform|id)\b/i.test(ln)) continue;
      const f = ln.split(/\s*[,;\t]\s*/);
      let name = '', pos = null;
      if (f.length >= 3) {
        const nums = f.filter(x => /^[-+]?\d+(\.\d+)?$/.test(x));
        if (nums.length >= 2 && f.length - nums.length >= 1) {          // name, lat, lon (decimal) in any order
          const iLat = f.indexOf(nums[0]);
          pos = [+nums[0], +nums[1]]; name = f.filter((x, k) => k !== iLat && k !== f.indexOf(nums[1])).join(' ');
        }
      }
      if (!pos) {                                                      // degrees and minutes anywhere: 27 12.3N 049 42.1E
        const dm = /(\d{1,2})[\s°]+(\d{1,2}(?:\.\d+)?)\s*['′]?\s*([NS])[\s,;]*(\d{1,3})[\s°]+(\d{1,2}(?:\.\d+)?)\s*['′]?\s*([EW])/i.exec(ln);
        if (dm) {
          const la = (+dm[1] + dm[2] / 60) * (/s/i.test(dm[3]) ? -1 : 1), lo = (+dm[4] + dm[5] / 60) * (/w/i.test(dm[6]) ? -1 : 1);
          pos = [la, lo]; name = (ln.slice(0, dm.index) + ' ' + ln.slice(dm.index + dm[0].length)).replace(/[,;\t]/g, ' ').trim();
        }
      }
      if (!pos) {                                                      // name then a position (any form parsePos reads)
        const k = ln.search(/[-+]?\d/);
        const p = k >= 0 && A.parsePos(ln.slice(k).replace(/[,;\t]/g, ' '));
        if (p) { pos = p; name = ln.slice(0, k).replace(/[,;\t]+$/, ''); }
        else {
          const k2 = ln.search(/[A-Za-z][^NSEWnsew\d]/);
          const p2_ = k2 > 0 && A.parsePos(ln.slice(0, k2).replace(/[,;\t]/g, ' '));
          if (p2_) { pos = p2_; name = ln.slice(k2); }
        }
      }
      if (pos) add(name.replace(/^["']|["']$/g, ''), pos[0], pos[1]);
    }
    return out;
  }
  function routeText() {
    return 'NAV47 ROUTE 1\n' + (R.gc ? 'GC' : 'RL') + '\n' + R.wps.map(w => `${w.lat.toFixed(6)} ${w.lon.toFixed(6)}${w.name ? ' ' + w.name : ''}`).join('\n') + '\n';
  }
  function readRoute(text) {
    const ls = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    if (/^NAV47 ROUTE/.test(ls[0] || '')) {
      R.gc = ls[1] === 'GC';
      R.wps = ls.slice(2).map(l => { const f = l.split(/\s+/); return { lat: +f[0], lon: +f[1], name: f.slice(2).join(' ') }; }).filter(w => isFinite(w.lat) && isFinite(w.lon));
    } else {
      R.wps = parsePlaces(text).map(p => ({ lat: p.lat, lon: p.lon, name: p.name }));
    }
    cur = 0; R.view = null; save();
  }
  function download(name, text, type) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: type || 'text/plain' })); a.download = name; a.click();
  }

  // ---- the chart ----
  let landG = null, landW = null, landR = null;
  function decode(arr, q) { const o = new Float64Array(arr.length); let x = 0, y = 0; for (let i = 0; i < arr.length; i += 2) { x += arr[i]; y += arr[i + 1]; o[i] = x / q; o[i + 1] = y / q; } return o; }
  function coast() {
    if (!landG && C) {
      landG = C.gulf.polys.map(p => decode(p, C.gulf.q)); landW = C.world.lines.map(p => decode(p, C.world.q));
      landR = C.region ? C.region.polys.map(p => decode(p, C.region.q)) : [];
    }
  }
  const mer = lat => Math.log(Math.tan(Math.PI / 4 + Math.max(-85, Math.min(85, lat)) * D2R / 2)) * R2D;
  const imer = y => (2 * Math.atan(Math.exp(y * D2R)) - Math.PI / 2) * R2D;

  function fit(W, H) {
    const pts = R.wps.length ? R.wps : [{ lat: S.pos[0], lon: S.pos[1] }];
    let la0 = Math.min(...pts.map(p => p.lat)), la1 = Math.max(...pts.map(p => p.lat));
    let lo0 = Math.min(...pts.map(p => p.lon)), lo1 = Math.max(...pts.map(p => p.lon));
    if (pts.length < 2) { la0 -= 0.6; la1 += 0.6; lo0 -= 0.8; lo1 += 0.8; }
    const pad = 0.15, dy = mer(la1) - mer(la0) || 0.5, dx = lo1 - lo0 || 0.5;
    const k = Math.min(W / (dx * (1 + 2 * pad)), H / (dy * (1 + 2 * pad)));
    return { lon: (lo0 + lo1) / 2, y: (mer(la0) + mer(la1)) / 2, k: Math.min(k, 4000) };
  }

  const THEMES = {
    modern: { sea: '#dfeaf3', land: '#ece4cf', coast: '#6c6a5c', grid: 'rgba(40,70,100,.18)', text: '#1b2129', soft: '#5d6875', route: '#c0392b',
      wp: '#c0392b', port: '#1f5f99', field: '#7a5c00', plat: '#1b2129', zone: 'rgba(192,57,43,.55)', font: 'system-ui, sans-serif' },
    dark: { sea: '#122030', land: '#2d3440', coast: '#8b95a3', grid: 'rgba(160,190,220,.16)', text: '#e7ebf0', soft: '#98a2af', route: '#ff7b6b',
      wp: '#ff7b6b', port: '#6db0ec', field: '#f0b43c', plat: '#e7ebf0', zone: 'rgba(255,123,107,.6)', font: 'system-ui, sans-serif' },
    vintage: { sea: '#ecdfb8', land: '#dcc89a', coast: '#3b2a17', grid: 'rgba(80,50,20,.22)', text: '#2a1c0e', soft: '#5f4528', route: '#8b1e10',
      wp: '#8b1e10', port: '#2a1c0e', field: '#5c3a12', plat: '#2a1c0e', zone: 'rgba(139,30,16,.7)', font: '"IM Fell English", "Iowan Old Style", Palatino, Georgia, serif' },
    calc: { sea: '#d9dcd2', land: '#c3c7bb', coast: '#1c1f1c', grid: 'rgba(28,31,28,.18)', text: '#1c1f1c', soft: '#3b403b', route: '#1c1f1c',
      wp: '#1c1f1c', port: '#1c1f1c', field: '#1c1f1c', plat: '#1c1f1c', zone: 'rgba(28,31,28,.8)', font: 'ui-monospace, "DejaVu Sans Mono", monospace' },
  };
  function theme() {
    if (S.style === 'vintage') return THEMES.vintage;
    if (S.style === 'calc') return THEMES.calc;
    return matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? THEMES.dark : THEMES.modern;
  }

  // the vintage chart's paper, made once
  let paper = null;
  function paperPattern(cx) {
    if (paper) return cx.createPattern(paper, 'repeat');
    paper = document.createElement('canvas'); paper.width = paper.height = 256;
    const g = paper.getContext('2d'), im = g.createImageData(256, 256);
    let s = 47;
    const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < im.data.length; i += 4) {
      const n = (rnd() + rnd() + rnd()) / 3, v = 226 + (n - 0.5) * 26;
      im.data[i] = v + 10; im.data[i + 1] = v; im.data[i + 2] = v - 34; im.data[i + 3] = 255;
    }
    g.putImageData(im, 0, 0);
    for (let i = 0; i < 40; i++) {                        // fibres and stains
      g.strokeStyle = `rgba(120,80,30,${0.03 + rnd() * 0.05})`; g.lineWidth = 0.6;
      g.beginPath(); const x = rnd() * 256, y = rnd() * 256; g.moveTo(x, y); g.quadraticCurveTo(x + rnd() * 40 - 20, y + rnd() * 40 - 20, x + rnd() * 60 - 30, y + rnd() * 60 - 30); g.stroke();
    }
    return cx.createPattern(paper, 'repeat');
  }

  // sea monsters of the old charts (ink drawings), at sea, as the cartographers put them where nobody had been
  const MONSTER_KINDS = ['serpent', 'whale', 'kraken', 'ship'];
  function drawMonster(cx, kind, x, y, s, flip, col) {
    cx.save(); cx.translate(x, y); cx.scale(flip ? -s : s, s);
    cx.strokeStyle = col; cx.fillStyle = col; cx.lineWidth = 1.6 / s; cx.lineJoin = cx.lineCap = 'round';
    const P = d => { const p = new Path2D(d); cx.stroke(p); return p; };
    if (kind === 'serpent') {
      P('M-70 6 Q-60 -22 -48 4 Q-38 22 -28 4 Q-18 -26 -6 2 Q4 22 14 4 Q24 -24 36 0');            // the humps
      P('M-66 10 Q-60 -14 -50 8 M-30 8 Q-18 -18 -8 6 M12 8 Q24 -16 34 4');                       // the belly lines
      for (const [a, b] of [[-58, -12], [-54, -15], [-16, -16], [-12, -17], [24, -15], [28, -14]]) P(`M${a} ${b + 4} l3 -7 l3 7`);   // spines
      P('M36 0 Q44 -14 56 -14 Q66 -14 70 -6 Q62 -4 58 0 Q64 4 70 8 Q60 10 52 4 Q44 6 36 0 Z');  // the head, jaws open
      cx.beginPath(); cx.arc(56, -9, 1.6, 0, 7); cx.fill();
      P('M70 -6 q6 -3 9 -10 M70 8 q6 3 8 10');                                                   // the forked tongue
      P('M-70 6 q-8 -2 -12 -10 q4 6 -2 12');                                                     // the tail
      for (let i = -90; i <= 80; i += 20) P(`M${i} 26 q5 -4 10 0 q5 4 10 0`);                    // the waves
    } else if (kind === 'whale') {
      P('M-50 6 Q-46 -18 -10 -20 Q22 -22 40 -8 Q50 0 44 8 Q20 18 -20 14 Q-40 12 -50 6 Z');
      P('M-50 6 Q-62 -4 -70 -12 Q-64 2 -72 8 Q-60 8 -50 6');                                      // the flukes
      P('M30 4 Q20 10 4 8');                                                                       // the mouth
      cx.beginPath(); cx.arc(28, -6, 1.6, 0, 7); cx.fill();
      P('M10 -21 q-2 -12 -10 -18 M10 -21 q2 -14 10 -20 M10 -21 q0 -14 0 -22');                    // the spout
      for (let i = -80; i <= 60; i += 20) P(`M${i} 22 q5 -4 10 0 q5 4 10 0`);
    } else if (kind === 'kraken') {
      P('M-18 0 Q-22 -34 0 -38 Q22 -34 18 0 Z');                                                   // the head
      cx.beginPath(); cx.arc(-7, -12, 2, 0, 7); cx.arc(7, -12, 2, 0, 7); cx.fill();
      for (const [a, b, c] of [[-16, -46, 14], [-8, -30, 30], [0, -10, 36], [8, 14, 30], [16, 40, 12]]) {
        P(`M${a} 0 Q${a + b / 3} 22 ${b} 18 Q${b + (b < 0 ? -10 : 10)} 12 ${b + (b < 0 ? -6 : 6)} ${c - 30}`);
      }
      for (let i = -70; i <= 60; i += 20) P(`M${i} 30 q5 -4 10 0 q5 4 10 0`);
    } else if (kind === 'ship') {
      P('M-34 6 Q0 18 34 6 L28 -2 L-30 -2 Z');                                                     // the hull
      P('M-8 -2 L-8 -44 M12 -2 L12 -36 M-24 -2 L-24 -26');                                          // the masts
      P('M-8 -40 Q4 -30 -8 -18 M12 -34 Q22 -26 12 -14 M-24 -24 Q-16 -18 -24 -10');                 // the sails
      P('M-8 -44 l8 3 l-8 3');                                                                     // the pennant
      for (let i = -50; i <= 40; i += 20) P(`M${i} 14 q5 -4 10 0 q5 4 10 0`);
    }
    cx.restore();
  }
  function compassRose(cx, x, y, r, T, vint) {
    cx.save(); cx.translate(x, y);
    if (vint) {                                            // the rhumb lines across the chart, as on a portolan
      cx.strokeStyle = 'rgba(110,60,20,.16)'; cx.lineWidth = 0.7;
      for (let i = 0; i < 32; i++) { const a = i * Math.PI / 16; cx.beginPath(); cx.moveTo(0, 0); cx.lineTo(Math.sin(a) * 3000, -Math.cos(a) * 3000); cx.stroke(); }
    }
    cx.lineWidth = 1; cx.strokeStyle = T.coast;
    for (const rr of [r, r * 0.92, r * 0.42]) { cx.beginPath(); cx.arc(0, 0, rr, 0, 7); cx.stroke(); }
    for (let i = 0; i < 360; i += 10) { const a = i * D2R, l = i % 30 ? 0.95 : 0.9; cx.beginPath(); cx.moveTo(Math.sin(a) * r * l, -Math.cos(a) * r * l); cx.lineTo(Math.sin(a) * r * 0.92, -Math.cos(a) * r * 0.92); cx.stroke(); }
    const point = (a, len, w, dark) => {
      const s = Math.sin(a), c = Math.cos(a), ps = Math.sin(a + Math.PI / 2), pc = Math.cos(a + Math.PI / 2);
      cx.beginPath(); cx.moveTo(0, 0); cx.lineTo(s * len, -c * len); cx.lineTo(ps * w, -pc * w); cx.closePath();
      cx.fillStyle = dark ? T.coast : (vint ? '#efe2bf' : '#fff'); cx.fill(); cx.stroke();
      cx.beginPath(); cx.moveTo(0, 0); cx.lineTo(s * len, -c * len); cx.lineTo(-ps * w, pc * w); cx.closePath();
      cx.fillStyle = dark ? (vint ? '#efe2bf' : '#fff') : T.coast; cx.fill(); cx.stroke();
    };
    for (let i = 0; i < 8; i++) point(i * Math.PI / 4 + Math.PI / 8, r * 0.5, r * 0.05, i % 2);
    for (let i = 0; i < 4; i++) point(i * Math.PI / 2 + Math.PI / 4, r * 0.62, r * 0.08, 0);
    for (let i = 0; i < 4; i++) point(i * Math.PI / 2, r * 0.88, r * 0.1, 1);
    cx.fillStyle = T.text; cx.font = `${vint ? 'italic ' : ''}700 ${Math.round(r * 0.2)}px ${T.font}`; cx.textAlign = 'center'; cx.textBaseline = 'middle';
    if (vint) {                                            // the fleur-de-lis at north
      cx.save(); cx.translate(0, -r * 1.08); cx.scale(r / 60, r / 60); cx.fillStyle = T.route;
      cx.fill(new Path2D('M0 -14 C4 -8 6 -2 0 6 C-6 -2 -4 -8 0 -14 Z M0 2 C8 -6 14 -2 10 4 C8 0 4 2 2 6 Z M0 2 C-8 -6 -14 -2 -10 4 C-8 0 -4 2 -2 6 Z M-6 6 H6 V8 H-6 Z'));
      cx.restore();
    } else cx.fillText('N', 0, -r * 1.12);
    cx.restore();
  }

  function draw() {
    if (!cv) return;
    coast();
    const T = theme(), vint = S.style === 'vintage', calc = S.style === 'calc';
    const dpr = window.devicePixelRatio || 1;
    const W = cv.clientWidth, H = cv.clientHeight;
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const cx = cv.getContext('2d');
    cx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!R.view) { R.view = fit(W, H); }
    const V = R.view;
    const X = lon => W / 2 + (lon - V.lon) * V.k, Y = lat => H / 2 - (mer(lat) - V.y) * V.k;
    const LON = x => V.lon + (x - W / 2) / V.k, LAT = y => imer(V.y - (y - H / 2) / V.k);
    last = { X, Y, LON, LAT, W, H };
    // the sea
    cx.fillStyle = vint ? paperPattern(cx) : T.sea; cx.fillRect(0, 0, W, H);
    if (vint) {
      const g = cx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.3, W / 2, H / 2, Math.max(W, H) * 0.75);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(110,70,20,.35)'); cx.fillStyle = g; cx.fillRect(0, 0, W, H);
    }
    // the land: the world (low resolution) outside the Gulf box, the Gulf (full) inside
    // the land as a filled path, and its shore as a stroked one (without the edges of the data's box)
    const onEdge = (lo, la, b) => b && (Math.abs(lo - b[0]) < 1e-6 || Math.abs(lo - b[1]) < 1e-6 || Math.abs(la - b[2]) < 1e-6 || Math.abs(la - b[3]) < 1e-6);
    const path = (arr, closed, box) => {
      const p = new Path2D(), sh = new Path2D();
      let pl = arr[0], pe = false, px = 0, py = 0;
      for (let i = 0; i < arr.length; i += 2) {
        let lo = arr[i]; while (lo - pl > 180) lo -= 360; while (lo - pl < -180) lo += 360; pl = lo;
        const x = X(lo), y = Y(arr[i + 1]), e = onEdge(arr[i], arr[i + 1], box);
        i ? p.lineTo(x, y) : p.moveTo(x, y);
        if (i && !(e && pe)) { sh.moveTo(px, py); sh.lineTo(x, y); }
        pe = e; px = x; py = y;
      }
      if (closed) p.closePath();
      p.shore = sh;
      return p;
    };
    const gb = C ? C.gulf.box : [0, 0, 0, 0], rb = C && C.region ? C.region.box : gb;
    const rect = b => { const p = new Path2D(); p.rect(X(b[0]), Y(b[3]), X(b[1]) - X(b[0]), Y(b[2]) - Y(b[3])); return p; };
    const boxPath = rect(gb), regPath = rect(rb);
    const polys = [], lands = [];
    if (landW) {                                       // the world, lines, outside the region
      cx.save();
      const out = new Path2D(); out.rect(0, 0, W, H); out.addPath(regPath); cx.clip(out, 'evenodd');
      for (const a of landW) {
        const closed = Math.abs(a[0] - a[a.length - 2]) < 1e-6 && Math.abs(a[1] - a[a.length - 1]) < 1e-6;
        polys.push([path(a, closed), closed]);
      }
      paintLand(cx, polys, T, vint, calc);
      for (const [pp, c] of polys) if (c) lands.push([pp, 'w']);
      cx.restore();
      polys.length = 0;
    }
    if (landR && landR.length) {                       // the region (intermediate), filled, outside the Gulf
      cx.save();
      const out = new Path2D(); out.addPath(regPath); out.addPath(boxPath); cx.clip(out, 'evenodd');
      for (const a of landR) polys.push([path(a, true, rb), true, a]);
      paintLand(cx, polys, T, vint, calc);
      for (const [pp] of polys) lands.push([pp, 'r']);
      cx.restore();
      polys.length = 0;
    }
    if (landG) {
      cx.save(); cx.clip(boxPath);
      for (const a of landG) polys.push([path(a, true, gb), true, a]);
      paintLand(cx, polys, T, vint, calc);
      for (const [pp] of polys) lands.push([pp, 'g']);
      cx.restore();
    }
    // the graticule
    const span = (W / V.k);
    const stepDeg = [1 / 60, 2 / 60, 5 / 60, 10 / 60, 15 / 60, 0.5, 1, 2, 5, 10, 15, 30].find(s => span / s <= 9) || 30;
    cx.strokeStyle = T.grid; cx.lineWidth = 1; cx.fillStyle = T.soft; cx.font = `${vint ? 'italic ' : ''}11px ${T.font}`;
    const lab = (v, ns) => { const a = Math.abs(v), d = Math.floor(a + 1e-9), m = Math.round((a - d) * 60); return `${d}°${m ? p2(m) + '′' : ''}${v < 0 ? ns[1] : v > 0 ? ns[0] : ''}`; };
    for (let lo = Math.floor(LON(0) / stepDeg) * stepDeg; lo <= LON(W); lo += stepDeg) {
      const x = X(lo); cx.beginPath(); cx.moveTo(x, 0); cx.lineTo(x, H); cx.stroke();
      cx.textAlign = 'center'; cx.fillText(lab(((lo + 540) % 360) - 180, 'EW'), x, H - 6);
    }
    for (let la = Math.floor(LAT(H) / stepDeg) * stepDeg; la <= LAT(0); la += stepDeg) {
      const y = Y(la); cx.beginPath(); cx.moveTo(0, y); cx.lineTo(W, y); cx.stroke();
      cx.textAlign = 'left'; cx.fillText(lab(la, 'NS'), 4, y - 3);
    }
    // the decorations of the old chart
    if (vint) {
      compassRose(cx, W - 92, 118, 58, T, true);
      // the monsters: in open water, away from the land, the route, the platforms and the ornaments
      const within = (b, x, y) => { const lo = LON(x), la = LAT(y); return lo >= b[0] && lo <= b[1] && la >= b[2] && la <= b[3]; };
      const layer = (x, y) => within(gb, x, y) ? 'g' : within(rb, x, y) ? 'r' : 'w';
      const land = (x, y) => lands.some(([pp, g]) => g === layer(x, y) && cx.isPointInPath(pp, x * dpr, y * dpr, 'evenodd'));
      const busy = [[W - 92, 118, 110], [147, 54, 150]];
      R.wps.forEach(w => busy.push([X(w.lon), Y(w.lat), 70]));
      for (let i = 1; i < R.wps.length; i++) for (let t = 0.1; t < 1; t += 0.1) {
        const a = R.wps[i - 1], b = R.wps[i]; busy.push([X(a.lon + t * dlonMin(a.lon, b.lon) / 60), Y(a.lat + t * (b.lat - a.lat)), 55]);
      }
      plats.forEach(q => busy.push([X(q.lon), Y(q.lat), 45]));
      FIELDS.forEach(([, la, lo]) => busy.push([X(lo), Y(la), 50]));
      const picked = [];
      for (let gy = 0; gy < 7 && picked.length < 3; gy++) for (let gx = 0; gx < 9 && picked.length < 3; gx++) {
        const x = W * (0.12 + 0.76 * ((gx * 5 + gy * 3) % 9) / 8), y = H * (0.18 + 0.66 * ((gy * 4 + gx) % 7) / 6);
        if (busy.some(([bx, by, r]) => Math.hypot(bx - x, by - y) < r) || picked.some(([px, py]) => Math.hypot(px - x, py - y) < 220)) continue;
        if ([[0, 0], [-75, 0], [75, 0], [0, -35], [0, 35], [-50, 25], [50, -25]].some(([dx, dy]) => land(x + dx, y + dy))) continue;
        picked.push([x, y]);
      }
      picked.forEach(([x, y], k) => drawMonster(cx, MONSTER_KINDS[(k + Math.round(V.lon * 7)) % 4 < 0 ? 0 : (k + Math.abs(Math.round(V.lon * 7))) % 4], x, y, 0.8, k % 2, 'rgba(60,35,15,.82)'));
    } else if (!calc) compassRose(cx, W - 60, H - 70, 36, T, false);
    // the places
    const label = (t, x, y, col, opt) => {
      cx.fillStyle = col; cx.font = opt.font; cx.textAlign = opt.align || 'left'; cx.textBaseline = 'middle';
      if (!vint && !calc) { cx.lineWidth = 3; cx.strokeStyle = T.sea; cx.strokeText(t, x, y); }
      cx.fillText(t, x, y);
    };
    if (R.layers.fields) for (const [n, la, lo] of FIELDS) {
      const x = X(lo), y = Y(la); if (x < -50 || x > W + 50 || y < -20 || y > H + 20) continue;
      cx.strokeStyle = T.field; cx.setLineDash([3, 3]); cx.lineWidth = 1; cx.beginPath(); cx.arc(x, y, Math.max(10, 0.08 * V.k), 0, 7); cx.stroke(); cx.setLineDash([]);
      label(vint ? n + ' Field' : n.toUpperCase(), x, y, T.field, { font: `${vint ? 'italic ' : ''}600 ${vint ? 14 : 11}px ${T.font}`, align: 'center' });
    }
    if (R.layers.ports) for (const [n, la, lo] of placesPorts()) {
      const x = X(lo), y = Y(la); if (x < -50 || x > W + 50 || y < -20 || y > H + 20) continue;
      cx.fillStyle = T.port; cx.beginPath(); cx.arc(x, y, 3.5, 0, 7); cx.fill();
      if (vint) { cx.strokeStyle = T.port; cx.beginPath(); cx.moveTo(x, y - 4); cx.lineTo(x, y - 12); cx.moveTo(x - 4, y - 9); cx.lineTo(x + 4, y - 9); cx.stroke(); }
      label(n, x - 7, y, T.port, { font: `${vint ? 'italic ' : ''}700 ${vint ? 15 : 12}px ${T.font}`, align: 'right' });
    }
    // your platforms and their zones
    const zr = R.radius / 1852 / 60;              // degrees of latitude
    if (R.layers.plats) for (const q of plats) {
      const x = X(q.lon), y = Y(q.lat); if (x < -30 || x > W + 30 || y < -30 || y > H + 30) continue;
      const rp = Math.abs(Y(q.lat + zr) - y);
      if (R.layers.zones) {
        cx.strokeStyle = T.zone; cx.lineWidth = 1; cx.setLineDash(vint ? [2, 2] : []); cx.beginPath(); cx.arc(x, y, Math.max(rp, 2.5), 0, 7); cx.stroke(); cx.setLineDash([]);
        if (rp > 4) { cx.fillStyle = T.zone.replace(/[\d.]+\)$/, '0.08)'); cx.fill(); }
      }
      cx.fillStyle = T.plat;
      if (q.kind === 'station') { cx.beginPath(); cx.moveTo(x, y - 4); cx.lineTo(x + 4, y + 3); cx.lineTo(x - 4, y + 3); cx.closePath(); cx.fill(); }
      else cx.fillRect(x - 2, y - 2, 4, 4);
      if (V.k > 260 || q.kind === 'station') label(q.name, x + 6, y, T.plat, { font: `${vint ? 'italic ' : ''}${q.kind === 'station' ? 700 : 400} ${vint ? 12 : 10}px ${T.font}` });
    }
    // the route
    const L = legs();
    for (let i = 1; i < R.wps.length; i++) {
      const a = R.wps[i - 1], b = R.wps[i];
      cx.strokeStyle = T.route; cx.lineWidth = vint ? 2 : 2.2; cx.setLineDash(vint ? [7, 4] : []);
      cx.beginPath();
      if (R.gc) gcPoints(a.lat, a.lon, b.lat, b.lon, 48).forEach(([la, lo], k) => k ? cx.lineTo(X(lo), Y(la)) : cx.moveTo(X(lo), Y(la)));
      else { cx.moveTo(X(a.lon), Y(a.lat)); let lo = a.lon + dlonMin(a.lon, b.lon) / 60; cx.lineTo(X(lo), Y(b.lat)); }
      cx.stroke();
      // the course on the leg
      const mx = (X(a.lon) + X(a.lon + dlonMin(a.lon, b.lon) / 60)) / 2, my = (Y(a.lat) + Y(b.lat)) / 2;
      if (Math.hypot(X(b.lon) - X(a.lon), Y(b.lat) - Y(a.lat)) > 90) {
        cx.setLineDash([]);
        label(`${L[i].crs.toFixed(0).padStart(3, '0')}° ${L[i].nm.toFixed(1)}′`, mx + 6, my - 10, T.route, { font: `${vint ? 'italic ' : ''}600 11px ${T.font}` });
      }
    }
    cx.setLineDash([]);
    // the dangers: a leg through a 500 m zone
    for (let i = 1; i < L.length; i++) for (const h of L[i].danger) {
      const x = X(h.lon), y = Y(h.lat);
      if (vint) { drawMonster(cx, 'serpent', x, y - 16, 0.35, 0, T.route); label('Here be dangers', x + 10, y + 12, T.route, { font: `italic 700 12px ${T.font}` }); }
      else { cx.fillStyle = T.route; cx.font = `700 16px ${T.font}`; cx.textAlign = 'center'; cx.fillText('⚠', x, y - 10); }
    }
    R.wps.forEach((w, i) => {
      const x = X(w.lon), y = Y(w.lat);
      cx.fillStyle = i === cur ? T.route : (vint ? '#efe2bf' : calc ? T.sea : '#fff'); cx.strokeStyle = T.route; cx.lineWidth = 2;
      cx.beginPath(); cx.arc(x, y, i === cur ? 7 : 5.5, 0, 7); cx.fill(); cx.stroke();
      label(String(i + 1) + (w.name ? ' ' + w.name : ''), x + 9, y - 9, T.text, { font: `${vint ? 'italic ' : ''}700 12px ${T.font}` });
    });
    // the DR
    { const x = X(S.pos[1]), y = Y(S.pos[0]); cx.strokeStyle = T.text; cx.lineWidth = 1.5; cx.beginPath(); cx.moveTo(x, y - 8); cx.lineTo(x + 7, y + 5); cx.lineTo(x - 7, y + 5); cx.closePath(); cx.stroke(); }
    // the frame and the cartouche of the old chart
    if (vint) {
      cx.strokeStyle = T.coast; cx.lineWidth = 2; cx.strokeRect(4, 4, W - 8, H - 8); cx.lineWidth = 0.8; cx.strokeRect(10, 10, W - 20, H - 20);
      const mstep = stepDeg / 2;
      for (let lo = Math.floor(LON(10) / mstep) * mstep, k = 0; lo < LON(W - 10); lo += mstep, k++) {
        const x0 = X(lo), x1 = X(lo + mstep); if ((Math.round(lo / mstep)) % 2) { cx.fillStyle = T.coast; cx.fillRect(Math.max(10, x0), 4, Math.min(W - 10, x1) - Math.max(10, x0), 6); cx.fillRect(Math.max(10, x0), H - 10, Math.min(W - 10, x1) - Math.max(10, x0), 6); }
      }
      const cw = 250, ch = 64, x0 = 22, y0 = 22;
      cx.fillStyle = 'rgba(240,226,190,.92)'; cx.fillRect(x0, y0, cw, ch);
      cx.strokeStyle = T.coast; cx.lineWidth = 1.5; cx.strokeRect(x0, y0, cw, ch); cx.lineWidth = 0.6; cx.strokeRect(x0 + 4, y0 + 4, cw - 8, ch - 8);
      cx.fillStyle = T.text; cx.textAlign = 'center'; cx.textBaseline = 'alphabetic';
      cx.font = `italic 700 19px ${T.font}`; cx.fillText('Sinus Persicus', x0 + cw / 2, y0 + 28);
      cx.font = `italic 12px ${T.font}`; cx.fillText(`A Passage Plan · ${R.gc ? 'Great Circle' : 'Rhumb Line'}`, x0 + cw / 2, y0 + 47);
    }
    if (calc) { cx.strokeStyle = T.coast; cx.lineWidth = 2; cx.strokeRect(1, 1, W - 2, H - 2); }
    // the scale bar (nautical miles, at the centre's latitude)
    const nmPx = V.k / 60 / Math.cos(LAT(H / 2) * D2R);
    const nice = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].find(n => n * nmPx > 70) || 1000;
    const sx = 18, sy = H - 26;
    cx.strokeStyle = T.text; cx.lineWidth = 1.5; cx.beginPath(); cx.moveTo(sx, sy); cx.lineTo(sx + nice * nmPx, sy); cx.moveTo(sx, sy - 4); cx.lineTo(sx, sy + 4); cx.moveTo(sx + nice * nmPx, sy - 4); cx.lineTo(sx + nice * nmPx, sy + 4); cx.stroke();
    cx.fillStyle = T.text; cx.font = `${vint ? 'italic ' : ''}11px ${T.font}`; cx.textAlign = 'left'; cx.textBaseline = 'alphabetic';
    cx.fillText(`${nice} nm`, sx + 4, sy - 6);
    cx.fillStyle = T.soft; cx.textAlign = 'right'; cx.font = `10px ${T.font}`;
    cx.fillText(`coast: ${C ? C.src : '—'}`, W - 12, vint ? H - 14 : H - 18);
  }
  function paintLand(cx, polys, T, vint, calc) {
    if (vint) {                                            // the water lines along the coast, then the land, hatched
      const big = polys.filter(([, , a]) => !a || a.length > 40);
      for (const [w, a] of [[16, 0.06], [10, 0.09], [5, 0.14]]) { cx.lineWidth = w; cx.strokeStyle = `rgba(90,60,25,${a})`; for (const [p] of big) cx.stroke(p.shore || p); }
    }
    cx.fillStyle = T.land;
    for (const [p, closed] of polys) if (closed) cx.fill(p, 'evenodd');
    if (vint || calc) {
      if (!paintLand.hatch) {
        const h = document.createElement('canvas'); h.width = h.height = 8; const g = h.getContext('2d');
        g.strokeStyle = 'rgba(60,40,15,.28)'; g.lineWidth = 0.8; g.beginPath(); g.moveTo(0, 8); g.lineTo(8, 0); g.stroke();
        paintLand.hatch = h;
        const d = document.createElement('canvas'); d.width = d.height = 4; const e = d.getContext('2d'); e.fillStyle = 'rgba(28,31,28,.45)'; e.fillRect(0, 0, 1, 1);
        paintLand.dots = d;
      }
      cx.fillStyle = cx.createPattern(vint ? paintLand.hatch : paintLand.dots, 'repeat');
      for (const [p, closed] of polys) if (closed) cx.fill(p, 'evenodd');
    }
    cx.strokeStyle = T.coast; cx.lineWidth = vint ? 1.3 : 1;
    for (const [p] of polys) cx.stroke(p.shore || p);
  }
  // the ports: the public positions, or the exact ones of your stations of the same name
  function placesPorts() {
    return PORTS.map(([n, la, lo]) => {
      const q = plats.find(p => p.name.toLowerCase().replace(/[^a-z]/g, '').includes(n.toLowerCase().replace(/[^a-z]/g, '')));
      return q ? [n, q.lat, q.lon] : [n, la, lo];
    });
  }

  // ---- the page ----
  function table() {
    const L = legs();
    const etd = S.j, sog = Math.max(0.1, +R.sog || 10);
    const zd = A.zdOf();
    const fT = j => { const [y, m, d, h] = NAV.cal(j); return `${p2(d)}-${p2(m)} ${NAV.fhm(h)}`; };
    let h = '<div class="scroll"><table class="rt"><tr><th>WP</th><th>Name</th><th>Lat</th><th>Lon</th><th class="num">CRS</th><th class="num">DIST</th><th class="num">CUM</th><th class="num">ETA UT</th><th class="num">ETA ZT</th><th></th></tr>';
    R.wps.forEach((w, i) => {
      const l = L[i], eta = etd + l.cum / sog / 24;
      const warn = l.danger && l.danger.length ? `<span class="warn" title="${l.danger.map(d => d.q.name + ' ' + (d.d * 1852).toFixed(0) + ' m').join(', ')}">⚠ ${l.danger.length}</span>` : '';
      h += `<tr class="click${i === cur ? ' sel' : ''}" data-i="${i}"><td>${i + 1}</td><td><input class="wpn" data-i="${i}" value="${(w.name || '').replace(/"/g, '&quot;')}" placeholder="—" size="6"></td>` +
        `<td class="mono">${fpos(w.lat, 'NS')}</td><td class="mono">${fpos(w.lon, 'EW')}</td>` +
        `<td class="num mono">${l.crs === null ? '' : l.crs.toFixed(1).padStart(5, '0') + '°'}</td><td class="num mono">${i ? l.nm.toFixed(1) : ''}</td>` +
        `<td class="num mono">${i ? l.cum.toFixed(1) : ''}</td><td class="num mono">${fT(eta)}</td><td class="num mono">${fT(eta - zd / 24)}</td><td>${warn}</td></tr>`;
    });
    const tot = L.length ? L[L.length - 1].cum : 0;
    h += `</table></div><div class="meta">${R.wps.length} waypoints · <b>${tot.toFixed(1)} nm</b> · ${(tot / sog).toFixed(1)} h at ${sog} kn` +
      ` · ETD = the time at the top (${fT(etd)} UT) · ${R.gc ? 'GC: the initial course' : 'RL: Mercator sailing, WGS84 meridional parts'}</div>`;
    const dang = L.flatMap((l, i) => (l.danger || []).map(d => `leg ${i}–${i + 1}: ${d.q.name} ${(d.d * 1852).toFixed(0)} m`));
    if (dang.length) h += `<div class="warn" style="margin-top:4px">⚠ inside the ${R.radius} m zone: ${dang.join(' · ')}</div>`;
    return h;
  }

  function render(el) {
    const T = theme();
    const W = Math.round(el.getBoundingClientRect().width || 1000);
    const side = R.mode === 'split' && W > 900;
    let h = A.headCard('Route', 'passage planning') + '<div class="chips">';
    for (const [m, t] of [['split', 'Split'], ['chart', 'Chart'], ['table', 'Table']]) h += `<button class="rmode${R.mode === m ? ' on' : ''}" data-m="${m}">${t}</button>`;
    h += `<button id="rgc">${R.gc ? 'GC' : 'RL'}</button><label>SOG <input id="rsog" class="small" type="number" min="0.1" step="0.5" value="${R.sog}"> kn</label>` +
      `<button id="radd" class="${addMode ? 'on' : ''}" title="Click the chart to add a waypoint after the selected one">＋ on chart</button>` +
      '<button id="rhere" title="Add the DR (top) after the selected waypoint">＋ DR</button>' +
      '<input id="rpos" class="pos" placeholder="27 12.0N 049 42.0E" title="A position, Enter = add after the selected waypoint">' +
      '<button id="rup" title="Move the selected waypoint up">↑</button><button id="rdn" title="Move it down">↓</button>' +
      '<button id="rdel" title="Delete the selected waypoint">Delete</button><button id="rrev" title="Reverse the route">⇅</button>' +
      '<button id="rfit">Fit</button></div><div class="chips">' +
      '<label class="filebtn">Open route<input id="rload" type="file" accept=".txt,.csv,.gpx,.kml,.json,.geojson" hidden></label>' +
      '<button id="rsave">Save ROUTE.TXT</button><button id="rgpx">Save GPX</button><button id="rclr">Clear route</button>' +
      `<label class="filebtn" title="CSV / text (name, lat, lon), KML, GPX, GeoJSON, or tide47's web/data/private.js: kept in this browser only">Load platforms<input id="pload" type="file" accept=".txt,.csv,.kml,.gpx,.json,.geojson,.js" multiple hidden></label>` +
      `<label>Zone <input id="rrad" class="small" type="number" min="50" step="50" value="${R.radius}"> m</label>` +
      `<span class="chip">${plats.length} platforms</span>${plats.length ? '<button id="pclr">Forget platforms</button>' : ''}` +
      ['ports', 'fields', 'plats', 'zones'].map(k => `<label><input type="checkbox" class="rlay" data-k="${k}" ${R.layers[k] ? 'checked' : ''}> ${{ ports: 'ports', fields: 'fields', plats: 'platforms', zones: 'zones' }[k]}</label>`).join('') + '</div>';
    const H = Math.max(420, Math.min(760, Math.round(window.innerHeight * 0.68)));
    const chart = `<canvas id="rchart" style="width:100%;height:${H}px;display:block;border-radius:${S.style === 'vintage' ? 2 : 8}px;touch-action:none;cursor:${addMode ? 'crosshair' : 'grab'}"></canvas>`;
    if (R.mode === 'table') h += table();
    else if (R.mode === 'chart') h += `<div style="margin-top:8px">${chart}</div>`;
    else h += side ? `<div class="rsplit"><div>${chart}</div><div class="rtab">${table()}</div></div>` : `<div style="margin-top:8px">${chart}</div>${table()}`;
    h += '<div class="meta">Drag the chart to move it, the wheel (or +/− buttons, pinch) to zoom; drag a waypoint to move it; click a row to select. ' +
      'Coastline: GSHHG full resolution (as GMT), the Gulf; low resolution elsewhere. Ports approximate, fields the centres of gem.wiki: ' +
      'not for navigation. Your platforms stay in this browser.</div>';
    el.innerHTML = `<section class="card">${h}</section>`;
    cv = el.querySelector('#rchart');
    if (cv) { draw(); bindChart(); }
    bind(el);
  }

  function rerender() { A.render(); }
  function insert(lat, lon, name) {
    const i = R.wps.length ? cur + 1 : 0;
    R.wps.splice(i, 0, { lat, lon, name: name || '' }); cur = i; save();
  }
  function bind(el) {
    const q = id => el.querySelector('#' + id);
    el.querySelectorAll('.rmode').forEach(b => { b.onclick = () => { R.mode = b.dataset.m; save(); rerender(); }; });
    q('rgc').onclick = () => { R.gc = !R.gc; save(); rerender(); };
    q('rsog').onchange = e => { R.sog = Math.max(0.1, +e.target.value || 10); save(); rerender(); };
    q('radd').onclick = () => { addMode = !addMode; rerender(); };
    q('rhere').onclick = () => { insert(S.pos[0], S.pos[1], 'DR'); rerender(); };
    q('rpos').onkeydown = e => {
      if (e.key !== 'Enter') return;
      const p = A.parsePos(e.target.value);
      e.target.style.borderColor = p ? '' : 'var(--now)';
      if (p) { insert(p[0], p[1]); R.view = null; rerender(); }
    };
    q('rup').onclick = () => { if (cur > 0) { [R.wps[cur - 1], R.wps[cur]] = [R.wps[cur], R.wps[cur - 1]]; cur--; save(); rerender(); } };
    q('rdn').onclick = () => { if (cur < R.wps.length - 1) { [R.wps[cur + 1], R.wps[cur]] = [R.wps[cur], R.wps[cur + 1]]; cur++; save(); rerender(); } };
    q('rdel').onclick = () => { if (R.wps.length) { R.wps.splice(cur, 1); cur = Math.max(0, Math.min(cur, R.wps.length - 1)); save(); rerender(); } };
    q('rrev').onclick = () => { R.wps.reverse(); cur = R.wps.length - 1 - cur; save(); rerender(); };
    q('rfit').onclick = () => { R.view = null; save(); rerender(); };
    q('rclr').onclick = () => { if (confirmClear()) { R.wps = []; cur = 0; save(); rerender(); } };
    q('rsave').onclick = () => download('ROUTE.TXT', routeText());
    q('rgpx').onclick = () => download('route.gpx', '<?xml version="1.0"?>\n<gpx version="1.1" creator="Almanac 47"><rte><name>Route</name>\n' +
      R.wps.map((w, i) => `<rtept lat="${w.lat.toFixed(6)}" lon="${w.lon.toFixed(6)}"><name>${w.name || 'WP' + (i + 1)}</name></rtept>`).join('\n') + '\n</rte></gpx>\n', 'application/gpx+xml');
    q('rload').onchange = e => { const f = e.target.files[0]; if (f) f.text().then(t => { readRoute(t); rerender(); }); };
    q('pload').onchange = e => {
      Promise.all([...e.target.files].map(f => f.text().then(t => parsePlaces(t, f.name)))).then(ls => {
        const add = ls.flat();
        const key = p => p.name.toLowerCase() + '|' + p.lat.toFixed(5) + '|' + p.lon.toFixed(5);
        const have = new Set(plats.map(key));
        for (const p of add) if (!have.has(key(p))) { plats.push(p); have.add(key(p)); }
        savePlats(); rerender();
      });
    };
    if (q('pclr')) q('pclr').onclick = () => { plats = []; savePlats(); rerender(); };
    q('rrad').onchange = e => { R.radius = Math.max(10, +e.target.value || 500); save(); rerender(); };
    el.querySelectorAll('.rlay').forEach(c => { c.onchange = () => { R.layers[c.dataset.k] = c.checked ? 1 : 0; save(); draw(); }; });
    el.querySelectorAll('tr[data-i]').forEach(tr => { tr.onclick = e => { if (e.target.tagName === 'INPUT') return; cur = +tr.dataset.i; rerender(); }; });
    el.querySelectorAll('input.wpn').forEach(inp => { inp.onchange = () => { R.wps[+inp.dataset.i].name = inp.value.trim(); save(); draw(); }; });
  }
  function confirmClear() { return R.wps.length < 3 || window.confirm('Clear the route (' + R.wps.length + ' waypoints)?'); }

  function bindChart() {
    const pt = e => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    const hit = (x, y) => R.wps.findIndex(w => Math.hypot(last.X(w.lon) - x, last.Y(w.lat) - y) < 10);
    const zoom = (f, x, y) => {
      const V = R.view, lo = last.LON(x), my = V.y - (y - last.H / 2) / V.k;
      V.k = Math.max(2, Math.min(200000, V.k * f));
      V.lon = lo - (x - last.W / 2) / V.k; V.y = my + (y - last.H / 2) / V.k; save(); draw();
    };
    const pointers = new Map();
    cv.onpointerdown = e => {
      cv.setPointerCapture(e.pointerId); pointers.set(e.pointerId, pt(e));
      const [x, y] = pt(e);
      if (pointers.size === 2) { const [a, b] = [...pointers.values()]; drag = { pinch: Math.hypot(a[0] - b[0], a[1] - b[1]) }; return; }
      const i = hit(x, y);
      drag = i >= 0 ? { wp: i, moved: false } : { x, y, lon: R.view.lon, my: R.view.y, moved: false };
      if (i >= 0) { cur = i; draw(); }
    };
    cv.onpointermove = e => {
      if (!drag) return;
      pointers.set(e.pointerId, pt(e));
      const [x, y] = pt(e);
      if (drag.pinch) {
        if (pointers.size < 2) return;
        const [a, b] = [...pointers.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        zoom(d / drag.pinch, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); drag.pinch = d; return;
      }
      if (drag.wp !== undefined) { const w = R.wps[drag.wp]; w.lat = last.LAT(y); w.lon = last.LON(x); drag.moved = true; draw(); return; }
      if (Math.hypot(x - drag.x, y - drag.y) > 3) drag.moved = true;
      R.view.lon = drag.lon - (x - drag.x) / R.view.k; R.view.y = drag.my + (y - drag.y) / R.view.k; draw();
    };
    cv.onpointerup = e => {
      pointers.delete(e.pointerId);
      const d = drag; drag = null;
      if (!d) return;
      const [x, y] = pt(e);
      if (d.wp !== undefined) { R.wps[d.wp].lon = mod(R.wps[d.wp].lon + 180, 360) - 180; save(); rerender(); return; }
      if (!d.moved && !d.pinch && addMode) { insert(last.LAT(y), mod(last.LON(x) + 180, 360) - 180); rerender(); return; }
      save();
    };
    cv.onwheel = e => { e.preventDefault(); const [x, y] = pt(e); zoom(Math.exp(-e.deltaY * 0.0015), x, y); };
    cv.ondblclick = e => { const [x, y] = pt(e); zoom(2, x, y); };
  }

  window.addEventListener('resize', () => { if (S.view === 'route') draw(); });
  A.addView({ id: 'route', label: 'Route', render });
  A.ROUTE = { legRL, legGC, merParts, parsePlaces, readRoute, routeText, R };
})();
