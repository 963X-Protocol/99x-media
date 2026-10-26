// Deterministic timeline engine: the renderer calls window.renderAt(t) for every frame.
// Elements opt in with data-in="<time>" where time is seconds, "cN" (start of voice
// chunk N), "cNe" (end of chunk N), optionally "+0.4" / "-0.2".
// data-a: fade | up | down | left | right | scale | pop | growx | growy | type
// data-d: animation length (s). data-out: time to fade out. data-rate: chars/s for type.
window.SCENE = window.SCENE || { dur: 10, lead: 0.8, chunks: [] };

function clamp01(x) { return Math.min(1, Math.max(0, x)); }
function easeOut(x) { x = clamp01(x); return 1 - Math.pow(1 - x, 3); }
function easeBack(x) { x = clamp01(x); const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); }

function resolveTime(expr) {
  if (expr === undefined || expr === null || expr === '') return null;
  const m = String(expr).trim().match(/^c(\d+)(e?)\s*([+-]\s*[\d.]+)?$/);
  if (!m) return parseFloat(expr);
  const ch = SCENE.chunks[+m[1]];
  if (!ch) return 9999;
  const base = SCENE.lead + (m[2] ? ch.end : ch.start);
  return base + (m[3] ? parseFloat(m[3].replace(/\s/g, '')) : 0);
}

let ITEMS = null;
function prepare() {
  ITEMS = [...document.querySelectorAll('[data-in]')].map(el => ({
    el,
    t0: resolveTime(el.dataset.in),
    a: el.dataset.a || 'up',
    d: parseFloat(el.dataset.d || (el.dataset.a === 'growx' || el.dataset.a === 'growy' ? '0.7' : '0.6')),
    out: el.dataset.out ? resolveTime(el.dataset.out) : null,
    full: el.dataset.a === 'type' ? el.textContent : null,
    rate: parseFloat(el.dataset.rate || '18'),
    dist: parseFloat(el.dataset.dist || '22'),
  }));
  ITEMS.forEach(o => { if (o.full !== null) o.el.textContent = ''; });
}

window.renderAt = function (t) {
  if (!ITEMS) prepare();
  for (const o of ITEMS) {
    const raw = (t - o.t0) / o.d;
    const p = easeOut(raw);
    let op = p, tr = '';
    switch (o.a) {
      case 'fade': break;
      case 'up': tr = `translateY(${(1 - p) * o.dist}px)`; break;
      case 'down': tr = `translateY(${-(1 - p) * o.dist}px)`; break;
      case 'left': tr = `translateX(${-(1 - p) * o.dist * 1.5}px)`; break;
      case 'right': tr = `translateX(${(1 - p) * o.dist * 1.5}px)`; break;
      case 'scale': tr = `scale(${0.94 + 0.06 * p})`; break;
      case 'pop': { const q = easeBack(raw); op = clamp01(raw * 2); tr = `scale(${0.6 + 0.4 * q})`; break; }
      case 'growx': op = raw > 0 ? 1 : 0; tr = `scaleX(${p})`; break;
      case 'growy': op = raw > 0 ? 1 : 0; tr = `scaleY(${p})`; break;
      case 'type': {
        op = t >= o.t0 ? 1 : 0;
        const n = Math.max(0, Math.floor((t - o.t0) * o.rate));
        const s = o.full.slice(0, n);
        if (o.el.textContent !== s) o.el.textContent = s;
        break;
      }
    }
    if (o.out !== null) op *= 1 - easeOut((t - o.out) / 0.45);
    o.el.style.opacity = op.toFixed(4);
    if (tr) o.el.style.transform = tr;
  }
  // blinking cursors
  document.querySelectorAll('[data-blink]').forEach(el => {
    const start = resolveTime(el.dataset.blink) || 0;
    el.style.visibility = t < start ? 'hidden' : (Math.floor((t - start) * 1.8) % 2 === 0 ? 'visible' : 'hidden');
  });
  // pulsing dots
  document.querySelectorAll('[data-pulse]').forEach(el => {
    el.style.boxShadow = `0 0 0 ${(4 + 4 * Math.sin(t * 4)).toFixed(2)}px rgba(255,255,255,0.08)`;
  });
  // slow camera push
  const cam = document.getElementById('cam');
  if (cam) {
    const z = parseFloat(cam.dataset.zoom || '0.035');
    cam.style.transform = `scale(${(1 + z * t / SCENE.dur).toFixed(5)})`;
  }
  // dip to/from black
  const veil = document.getElementById('veil');
  if (veil) {
    const fi = parseFloat(document.body.dataset.fin || '0.45');
    const fo = parseFloat(document.body.dataset.fout || '0.45');
    let v = 1;
    if (fi > 0) v = Math.min(v, t / fi);
    if (fo > 0) v = Math.min(v, (SCENE.dur - t) / fo);
    veil.style.opacity = (1 - clamp01(v)).toFixed(4);
  }
};
