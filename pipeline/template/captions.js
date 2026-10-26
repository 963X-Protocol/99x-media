// Burned-in captions: each voice chunk is split into short phrases timed by length.
// Numbers, %, ×, $ amounts and 99X are highlighted. Load after the scene's own script.
(function () {
  const base = window.renderAt;
  let SEG = null, shown = null;
  function build() {
    SEG = [];
    SCENE.chunks.forEach(ch => {
      if (!ch.text) return;
      const words = ch.text.split(' '), groups = [];
      let g = [];
      words.forEach(w => {
        g.push(w);
        const len = g.join(' ').length;
        if ((len >= 16 && /[,.?!]$/.test(w)) || len >= 30) { groups.push(g.join(' ')); g = []; }
      });
      if (g.length) groups.push(g.join(' '));
      const total = groups.reduce((a, s) => a + s.length, 0);
      let t = SCENE.lead + ch.start;
      const span = ch.end - ch.start;
      groups.forEach(s => { const d = span * s.length / total; SEG.push({ a: t, b: t + d, s }); t += d; });
    });
  }
  const hl = s => s.replace(/([−$#]?\d[\d.,]*[%×]?|99X)/g, '<b>$1</b>');
  window.renderAt = function (t) {
    base(t);
    if (!SEG) build();
    let cur = null;
    for (const s of SEG) if (t >= s.a - 0.04 && t < s.b + 0.2) cur = s;
    const el = document.getElementById('cap');
    if (cur !== shown) { el.innerHTML = cur ? `<span class="c">${hl(cur.s)}</span>` : ''; shown = cur; }
    if (cur) { const p = Math.min(1, (t - cur.a + 0.04) / 0.12); el.style.transform = `scale(${(0.92 + 0.08 * p).toFixed(3)})`; el.style.opacity = p.toFixed(3); }
  };
})();
