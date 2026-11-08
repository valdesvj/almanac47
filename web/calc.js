// calc.js - the Calculator style: the screens of the PC app python/native/c47pc.py, pixel for pixel. The Python
// itself (web/data/pysrc.js, the almanac tables web/data/tbl.js) runs unchanged in the browser through Pyodide
// (CPython in WebAssembly): c47pc.Engine().screen(view, jd, lat, lon) gives the lit pixels of the 400 x 240 screen,
// drawn here as c47pc.render_rgb() does (scale 3, LCD colours, the dark frame).
// Pyodide comes from web/pyodide/ when the page is served over http (offline), otherwise from the jsDelivr CDN.
(function () {
  'use strict';
  const A = globalThis.A47;
  if (!A) return;
  const { S, store } = A;
  const PYO = '0.26.4', CDN = `https://cdn.jsdelivr.net/pyodide/v${PYO}/full/`;
  const W = 400, H = 240;
  const LCD_BG = [0xD9, 0xDC, 0xD2], LCD_ON = [0x1C, 0x1F, 0x1C], BEZEL = [0x2A, 0x2A, 0x2C];
  const PLAIN_BG = [255, 255, 255], PLAIN_ON = [0, 0, 0];
  const VIEWS = ['ALMANAC', 'CHART', 'TEXT', 'SKY', 'SPLIT', 'ANIM', 'ALLSKY', 'MOON'];
  const HINT = { ALMANAC: 'the almanac page (1)', CHART: 'chart and Hc / Zn (2)', TEXT: 'text almanac, one page per R/S (3)',
    SKY: 'horizon chart, the bodies named one by one (4)', SPLIT: 'chart above, almanac below (5)',
    ANIM: 'the Sun and the Moon over the day (6)', ALLSKY: 'the whole sky, 58 stars (7)', MOON: 'MOON47 (8)' };

  const opt = Object.assign({ tables: true, lcd: true, frames: 24, step: 0.5, ms: 1000, play: true }, store.get('calc') || {});
  let py = null, loading = null, failed = null, out = null, k = 0, timer = null, lastKey = '', secs = 0, CHAR_W = {};

  function script(src) {
    return new Promise((ok, ko) => {
      const s = document.createElement('script');
      s.src = src; s.onload = ok; s.onerror = () => { s.remove(); ko(new Error('cannot load ' + src)); };
      document.head.appendChild(s);
    });
  }

  async function load() {
    if (!globalThis.A47PY) await script('data/pysrc.js');
    if (!globalThis.A47TBL) await script('data/tbl.js');
    let index = CDN;
    if (!globalThis.loadPyodide) {
      if (/^https?:/.test(location.protocol)) {
        try { await script('pyodide/pyodide.js'); index = new URL('pyodide/', location.href).href; } catch (e) { /* use the CDN */ }
      }
      if (!globalThis.loadPyodide) await script(CDN + 'pyodide.js');
    }
    const p = await globalThis.loadPyodide({ indexURL: index });
    p.FS.mkdir('/a47');
    for (const [f, s] of Object.entries(globalThis.A47PY)) p.FS.writeFile('/a47/' + f, s);
    p.FS.writeFile('/a47/' + globalThis.A47TBL.name, globalThis.A47TBL.text);
    p.runPython(`
import sys
sys.path.insert(0, '/a47')
import c47pc, c47tables, c47screen
_ENG = {True: c47pc.Engine(c47tables.find('/a47')), False: c47pc.Engine(None)}

def a47_screen(view, j, lat, lon, tables, frames, step, tz=0.0, local=False):
    """The frames of a view as bytes of 400 x 240 (1 = lit), or the TEXT pages; and the status line. local: every
    time in LT = UT + tz hours (the UT / LT switch, +/- on the calculator)."""
    import c47screen21
    c47screen21.set_times(tz, local)
    eng = _ENG[bool(tables) and _ENG[True].tables is not None]
    eng.anim = {'frames': int(frames), 'step': float(step)}
    if view == 'TEXT':
        pages, n = eng.text(j, lat, lon)
        res = {'text': [c47pc.page_lines(p) for p in pages], 'file': c47pc.pages_text(pages)}
    else:
        fr, n = eng.screen(view, j, lat, lon)
        bufs = []
        for f in fr:
            b = bytearray(400 * 240)
            for x, r in f:
                b[r * 400 + x] = 1
            bufs.append(bytes(b))
        res = {'frames': bufs}
    if view == 'ANIM':
        res['src'] = 'quick positions (as HANIM)'
    elif eng.last is not None:
        res['src'] = '%s = %s' % (eng.last.source, 'almanac tables (%s)' % eng.tables.period if eng.last.moon_t else 'series')
    return res

def a47_charw():
    return dict(c47screen.CHAR_W)
`);
    CHAR_W = p.globals.get('a47_charw')().toJs({ dict_converter: Object.fromEntries });
    py = p;
  }

  function compute() {
    const view = VIEWS.includes(S.cview) ? S.cview : 'ALMANAC';
    const key = [view, S.j, S.pos[0], S.pos[1], opt.tables, opt.frames, opt.step, A.ltMode(), A.tzOf()].join();
    if (key === lastKey && out) return false;
    const t0 = performance.now();
    const r = py.globals.get('a47_screen')(view, S.j, S.pos[0], S.pos[1], opt.tables, opt.frames, opt.step, A.tzOf(), A.ltMode());
    const js = r.toJs({ dict_converter: Object.fromEntries });
    r.destroy();
    secs = (performance.now() - t0) / 1000;
    const keep = lastKey.split(',')[0] === view;            // the same view: stay on the TEXT page / SKY body / ANIM frame
    lastKey = key;
    out = { view, frames: js.frames || [new Uint8Array(W * H)], text: js.text || null, file: js.file || '', src: js.src || '' };
    const n = out.text ? out.text.length : out.frames.length;
    if (!keep || k >= n) k = 0;
    return true;
  }

  // c47pc.render_rgb(pixels, scale, lcd, bezel=True) on a canvas
  function draw(cv) {
    const s = 3, b = 6 * s, gap = opt.lcd && s >= 4 ? 1 : 0;
    const bg = opt.lcd ? LCD_BG : PLAIN_BG, on = opt.lcd ? LCD_ON : PLAIN_ON;
    cv.width = W * s + 2 * b; cv.height = H * s + 2 * b;
    const cx = cv.getContext('2d');
    cx.fillStyle = `rgb(${BEZEL})`; cx.fillRect(0, 0, cv.width, cv.height);
    cx.fillStyle = `rgb(${bg})`; cx.fillRect(b, b, W * s, H * s);
    cx.fillStyle = `rgb(${on})`;
    if (out.text) return drawText(cx, s, b, on);
    const f = out.frames[k];
    for (let r = 0; r < H; r++) {
      for (let x = 0; x < W; x++) if (f[r * W + x]) cx.fillRect(b + x * s, b + r * s, s - gap, s - gap);
    }
  }

  // c47pc draw_text: one ALMT page (two PROMPT lines), each character at its C47 pixel position; the next pages
  // smaller and grey below
  function drawText(cx, s, b, on) {
    const line = (part, x, y, kk) => { for (const c of part) { cx.fillText(c, x, y); x += (CHAR_W[c] || 8) * kk; } };
    let kk = 0.98 * s;
    cx.font = `bold ${13 * kk}px "DejaVu Sans", Verdana, sans-serif`;
    let y = b + 18 * s;
    for (const part of out.text[k]) { line(part, b + 4 * s, y, kk); y += 16 * s; }
    cx.fillStyle = `rgba(${on},0.45)`;
    kk = 0.62 * s;
    cx.font = `bold ${13 * kk}px "DejaVu Sans", Verdana, sans-serif`;
    y += 6 * s;
    for (let i = 1; i < out.text.length; i++) {
      for (const part of out.text[(k + i) % out.text.length]) {
        if (y > b + 234 * s) return;
        line(part, b + 4 * s, y, kk); y += 10 * s;
      }
      y += 4 * s;
    }
  }

  function status() {
    let extra = '';
    const n = out.text ? out.text.length : out.frames.length;
    if (out.text) extra = `   page ${k + 1}/${n} (R/S = Enter or Space)`;
    else if (out.view === 'ANIM') extra = `   frame ${k + 1}/${n}, every ${(+opt.step).toFixed(2)} h`;
    else if (n > 1) extra = `   body ${k + 1}/${n} (R/S = Enter or Space)`;
    return `${out.view} (${secs.toFixed(2)} s)   ${out.src}${extra}${out.text ? '   grey = next pages' : ''}`;
  }

  function play(el) {
    clearInterval(timer); timer = null;
    if (out && (out.view === 'ANIM' || out.view === 'SKY') && out.frames.length > 1 && opt.play) {
      const ms = out.view === 'SKY' ? 1000 : Math.max(50, +opt.ms || 1000);       // SKY: a name a second, as the C47
      timer = setInterval(() => {
        if (S.style !== 'calc' || !el.isConnected) { clearInterval(timer); timer = null; return; }
        next(el);
      }, ms);
    }
  }

  function next(el) {
    if (!out) return;
    const n = out.text ? out.text.length : out.frames.length;
    k = (k + 1) % n;
    const cv = el.querySelector('#lcd');
    if (cv) { draw(cv); el.querySelector('#cstat').textContent = status(); }
  }

  function save() {
    const a = document.createElement('a');
    if (out.text) {
      a.href = URL.createObjectURL(new Blob([out.file + '\n'], { type: 'text/plain' })); a.download = 'TEXT.txt';
    } else {
      a.href = document.getElementById('lcd').toDataURL('image/png'); a.download = out.view + '.png';
    }
    a.click();
  }

  function render(el) {
    if (!py && !loading && !failed && !store.get('pyok')) {
      // ask first: the Calculator style downloads Python
      const local = /^https?:/.test(location.protocol);
      el.innerHTML = '<section class="card lcdcard"><h2 style="margin:0 0 6px;color:#e8ebe2">Download Python?</h2>' +
        '<div>The Calculator style shows the screens of the PC app exactly, by running its own Python in the browser. ' +
        `For that it downloads Python (Pyodide ${PYO}, about 10 MB) from <b>cdn.jsdelivr.net</b>` +
        (local ? ', or from web/pyodide/ if you have put a copy there' : '') +
        '. Nothing about you is sent; your browser keeps the download for next time.</div>' +
        '<div class="chips" style="margin-top:12px"><button id="pyyes" class="on">Yes, download</button>' +
        '<button id="pyno">No, back to Modern</button>' +
        '<label><input id="pyrem" type="checkbox" checked> don\'t ask again</label></div></section>';
      el.querySelector('#pyyes').onclick = () => {
        if (el.querySelector('#pyrem').checked) store.set('pyok', true);
        loading = load().then(() => { loading = null; A.render(); },
          e => { loading = null; failed = e.message || String(e); A.render(); });
        A.render();
      };
      el.querySelector('#pyno').onclick = () => A.setStyle('modern');
      return;
    }
    if (!py) {
      el.innerHTML = `<section class="card lcdcard"><div class="meta" id="cstat">${failed
        ? `<span class="warn">Python could not be loaded: ${failed}.</span> The Calculator style needs the internet once ` +
          '(the Pyodide CDN), or Pyodide in web/pyodide/ with the page served over http (see web/README.md).'
        : 'Loading Python (Pyodide, about 10 MB the first time; then the browser keeps it)…'}</div></section>`;
      if (!loading && !failed) {
        loading = load().then(() => { loading = null; A.render(); },
          e => { loading = null; failed = e.message || String(e); A.render(); });
      }
      return;
    }
    let err = '';
    try { compute(); } catch (e) { err = String(e.message || e).split('\n').filter(Boolean).pop(); }
    if (err && !out) { el.innerHTML = `<section class="card lcdcard"><div class="warn">Program error: ${err}</div></section>`; return; }
    const v = out.view;
    let h = `<div class="lcdwrap"><canvas id="lcd" width="1236" height="756" title="${HINT[v]}"></canvas></div>`;
    h += `<div class="meta mono" id="cstat">${err ? `<span class="warn">Program error: ${err}</span>` : status()}</div>`;
    h += '<div class="chips">';
    const n = out.text ? out.text.length : out.frames.length;
    if (n > 1) h += '<button id="crs">R/S ▸</button>';
    if (v === 'ANIM' || v === 'SKY') h += `<button id="cplay" class="${opt.play ? 'on' : ''}">${opt.play ? '❚❚ Pause' : '▶ Play'}</button>`;
    if (v === 'ANIM') {
      h += `<label>Frames <input id="cfr" class="small" type="number" min="2" max="96" value="${opt.frames}"></label>` +
        `<label>Step h <input id="cst" class="small" type="number" min="0.05" max="6" step="0.05" value="${opt.step}"></label>` +
        `<label>Frame ms <input id="cms" class="small" type="number" min="50" max="5000" step="50" value="${opt.ms}"></label>`;
    }
    h += `<label><input id="ctb" type="checkbox" ${opt.tables ? 'checked' : ''}> Almanac tables</label>` +
      `<label><input id="clcd" type="checkbox" ${opt.lcd ? 'checked' : ''}> LCD colours</label>` +
      `<button id="csave">Save ${out.text ? 'TEXT' : 'PNG'}</button></div>`;
    h += `<div class="meta">${v}: ${HINT[v]}. The screens of the PC app (python/native/c47pc.py), its Python run unchanged ` +
      'in the browser (Pyodide). Keys: Space / Enter = R/S, + / − = one hour, ← → the view.</div>';
    el.innerHTML = `<section class="card lcdcard">${h}</section>`;
    draw(el.querySelector('#lcd'));
    const keep = () => store.set('calc', opt);
    const q = id => el.querySelector('#' + id);
    if (q('crs')) q('crs').onclick = () => next(el);
    if (q('cplay')) q('cplay').onclick = () => { opt.play = !opt.play; keep(); A.render(); };
    if (q('cfr')) q('cfr').onchange = e => { opt.frames = Math.max(2, Math.min(96, Math.round(+e.target.value) || 24)); keep(); A.render(); };
    if (q('cst')) q('cst').onchange = e => { opt.step = Math.max(0.05, +e.target.value || 0.5); keep(); A.render(); };
    if (q('cms')) q('cms').onchange = e => { opt.ms = Math.max(50, +e.target.value || 1000); keep(); A.render(); };
    q('ctb').onchange = e => { opt.tables = e.target.checked; keep(); A.render(); };
    q('clcd').onchange = e => { opt.lcd = e.target.checked; keep(); A.render(); };
    q('csave').onclick = save;
    play(el);
  }

  document.addEventListener('keydown', e => {
    if (S.style !== 'calc' || S.view !== 'calc' || /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
    const el = document.getElementById('views');
    if (e.key === ' ' || e.key === 'Enter') { next(el); e.preventDefault(); }
    else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const i = VIEWS.indexOf(S.cview) + (e.key === 'ArrowRight' ? 1 : -1);
      A.setCview(VIEWS[(i + VIEWS.length) % VIEWS.length]); e.preventDefault();
    }
  });

  A.CALC = { VIEWS, HINT, render, ready: () => !!py };
})();
