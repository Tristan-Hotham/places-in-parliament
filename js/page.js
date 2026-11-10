/* Which places get Parliament's attention? UK towns and cities on a plain MapLibre base map (OpenFreeMap Positron),
 * sized by Commons "in <place>" mentions in the chosen decade and coloured by the change in their share of mentions
 * (1980 to 2025 against 1910 to 1944), whether they gave their name to a seat, or nation; by-election towns as rings,
 * disasters as gold triangles; and a place explorer with the monthly series since 1909.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB', { maximumFractionDigits: 1 });
  const DIV = ['#2F6A9E', '#8FB0CF', '#C9C2B4', '#E3A58F', '#B4442E'];
  const NAT = { England: '#B4442E', Scotland: '#2F6A9E', Wales: '#5E7F4F', 'Northern Ireland': '#C98A2B' };
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  let map = null, D = null, M = null, mode = qs.get('mode') || 'lr', dec = 12, timer = null, cur = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  const ym = k => { const y = 1909 + Math.floor(k / 12); return `${MON[k % 12]} ${y}`; };
  const mi = s => { const [y, m] = s.split('-').map(Number); return (y - 1909) * 12 + m - 1; };

  // ---------------------------------------------------------------- map
  function colorExpr() {
    if (mode === 'seat') return ['case', ['==', ['get', 'seat'], 1], '#B4442E', '#9C9384'];
    if (mode === 'nat') return ['match', ['get', 'nat'], 'England', NAT.England, 'Scotland', NAT.Scotland, 'Wales', NAT.Wales, NAT['Northern Ireland']];
    return ['case', ['==', ['get', 'haslr'], 0], '#BDB6A8', ['interpolate', ['linear'], ['get', 'lr'], -3, DIV[0], -1.5, DIV[1], 0, DIV[2], 1.5, DIV[3], 3, DIV[4]]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBar'), e = document.getElementById('keyEnds');
    if (mode === 'seat') { t.textContent = 'Named in a Commons seat (any time since 1910)'; b.style.background = 'linear-gradient(90deg,#9C9384 50%,#B4442E 50%)'; e.innerHTML = '<span>never</span><span>at some time</span>'; }
    else if (mode === 'nat') { t.textContent = 'Nation'; b.style.background = `linear-gradient(90deg,${NAT.England} 25%,${NAT.Scotland} 25% 50%,${NAT.Wales} 50% 75%,${NAT['Northern Ireland']} 75%)`; e.innerHTML = '<span>England</span><span>Scotland</span><span>Wales</span><span>N. Ireland</span>'; }
    else { t.textContent = 'Share of mentions, 1980 to 2025 vs 1910 to 1944'; b.style.background = `linear-gradient(90deg,${DIV.join(',')})`; e.innerHTML = '<span>1/8</span><span>same</span><span>8x</span>'; }
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function radius() {
    const s = ['get', 'r' + dec];
    return ['interpolate', ['linear'], ['zoom'], 4, ['+', 2.2, ['*', small ? 0.75 : 0.95, s]], 8, ['+', 4, ['*', 1.5, s]], 13, ['+', 7, ['*', 2.2, s]]];
  }
  function setDec(i) {
    dec = i;
    document.getElementById('dy').value = i; document.getElementById('dyLab').textContent = D.decades[i];
    if (!map) return;
    map.setPaintProperty('pts', 'circle-radius', radius());
    map.setFilter('pts', ['>', ['get', 'r' + dec], 0]);
    map.setFilter('zpts', ['==', ['get', 'r' + dec], 0]);
  }
  function refresh() { map.setPaintProperty('pts', 'circle-color', colorExpr()); key(); }
  function decBars(p) {
    const w = 270, h = 50, n = 12, bw = w / n, v = p.d.slice(0, 12).map((x, i) => x / D.dec_tot[i]), mx = Math.max(...v, 1e-9);
    let s = `<svg class="spark" width="${w}" height="${h + 14}" viewBox="0 0 ${w} ${h + 14}" role="img" aria-label="Share of all town mentions by decade for ${esc(p.n)}">`;
    v.forEach((x, i) => { const bh = Math.max(x ? 2 : 0, h * x / mx); s += `<rect x="${(i * bw + 1).toFixed(1)}" y="${(h - bh).toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${bh.toFixed(1)}" fill="${i === dec ? '#2B2119' : '#B4442E'}"><title>${D.decades[i]}: ${(100 * x).toFixed(2)}%</title></rect>`; });
    return s + `<text x="1" y="${h + 12}" font-size="10" fill="#6E604E">1910s</text><text x="${w}" y="${h + 12}" font-size="10" text-anchor="end" fill="#6E604E">2020s</text></svg>`;
  }
  function popup(i, ll) {
    const p = D.p[i];
    let h = `<b class="t">${esc(p.n)}</b><div class="nt">${esc(p.nat)}${p.pop ? ', population ' + fmt(p.pop) + ' (modern)' : ''}</div><table>`;
    h += `<tr><td>"in ${esc(p.n)}"</td><td><b>${fmt(p.d[12])}</b> Commons speeches, ${D.decades[12]}</td></tr>`;
    if (dec < 12) h += `<tr><td>${D.decades[dec]}</td><td>${fmt(p.d[dec])} (${(100 * p.d[dec] / D.dec_tot[dec]).toFixed(2)}% of all town mentions)</td></tr>`;
    if (p.lr != null) h += `<tr><td>Share change</td><td>${p.lr >= 0 ? (2 ** p.lr).toFixed(1) + ' times' : 'down to ' + (2 ** p.lr).toFixed(2)} (1980 to 2025 vs 1910 to 1944)</td></tr>`;
    h += `<tr><td>Seat name</td><td>${p.seat ? 'named in a Commons seat at some time since 1910' : 'never part of a seat name'}</td></tr></table>`;
    h += decBars(p);
    if (p.by) h += `<p class="nt">By-elections: ${p.by.map(b => esc(b[1]) + ' ' + b[0].slice(0, 4) + (b[2] ? ' (changed hands)' : '')).join('; ')}</p>`;
    if (p.ds) h += `<p class="nt">Disasters: ${p.ds.map(d => esc(d[1]) + ' ' + d[0].slice(0, 4) + (d[3] > 0 ? ` (${d[3]} km away)` : '')).join('; ')}</p>`;
    h += `<p class="nt"><a href="#explore" data-ex="${i}">Chart every month since 1909</a>. Source: Hansard (Open Parliament Licence v3.0); counts of speeches saying "in ${esc(p.n)}".</p>`;
    const pu = new maplibregl.Popup({ maxWidth: '330px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
    const a = pu.getElement().querySelector('[data-ex]'); if (a) a.addEventListener('click', e => { e.preventDefault(); explore(i); document.getElementById('explore').scrollIntoView({ behavior: 'smooth' }); });
  }
  function tri() {
    const s = 28, c = document.createElement('canvas'); c.width = c.height = s; const g = c.getContext('2d');
    g.beginPath(); g.moveTo(s / 2, 3); g.lineTo(s - 3, s - 4); g.lineTo(3, s - 4); g.closePath(); g.fillStyle = '#C98A2B'; g.fill(); g.lineWidth = 2.5; g.strokeStyle = '#fff'; g.stroke();
    return g.getImageData(0, 0, s, s);
  }
  function setup() {
    const feats = D.p.map((p, i) => {
      const pr = { i, n: p.n, nat: p.nat, seat: p.seat, lr: p.lr ?? 0, haslr: p.lr == null ? 0 : 1, sz: p.d[12] };
      p.d.forEach((x, j) => { pr['r' + j] = x > 0 ? Math.sqrt(1000 * x / D.dec_tot[j]) : 0; });
      return { type: 'Feature', properties: pr, geometry: { type: 'Point', coordinates: [p.lo, p.la] } };
    }).sort((a, b) => b.properties.sz - a.properties.sz);
    map.addSource('p', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Hansard: Open Parliament Licence v3.0' });
    const bf = [], df = [];
    D.p.forEach((p, i) => {
      if (p.by && p.by.some(b => b[3] === 1)) bf.push({ type: 'Feature', properties: { i, k: p.by.filter(b => b[3] === 1).length }, geometry: { type: 'Point', coordinates: [p.lo, p.la] } });
      (p.ds || []).forEach(d => df.push({ type: 'Feature', properties: { i, e: d[1], y: d[0].slice(0, 4) }, geometry: { type: 'Point', coordinates: [p.lo, p.la] } }));
    });
    map.addSource('by', { type: 'geojson', data: { type: 'FeatureCollection', features: bf } });
    map.addSource('ds', { type: 'geojson', data: { type: 'FeatureCollection', features: df }, attribution: 'By-elections and disasters: Wikipedia lists (CC BY-SA 4.0)' });
    map.addImage('tri', tri(), { pixelRatio: 2 });
    map.addLayer({ id: 'zpts', type: 'circle', source: 'p', layout: { visibility: 'none' }, filter: ['==', ['get', 'r12'], 0], paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 2, 10, 4], 'circle-color': '#fff', 'circle-stroke-color': '#9C9384', 'circle-stroke-width': 1 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'p', paint: { 'circle-radius': radius(), 'circle-color': colorExpr(), 'circle-stroke-color': '#fff', 'circle-stroke-width': 1, 'circle-opacity': 0.92 } });
    map.addLayer({ id: 'bys', type: 'circle', source: 'by', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 4.5, 9, 8, 13, 12], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#2F6A9E', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 4, 1.3, 10, 2.2] } });
    map.addLayer({ id: 'dss', type: 'symbol', source: 'ds', layout: { 'icon-image': 'tri', 'icon-size': ['interpolate', ['linear'], ['zoom'], 4, 0.75, 10, 1.2], 'icon-allow-overlap': true, 'icon-offset': [0, -9] } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'p', minzoom: 7, layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['pts', 'zpts', 'bys', 'dss'].forEach(l => { map.on('click', l, e => { const f = e.features[0]; const p = D.p[f.properties.i]; popup(f.properties.i, [p.lo, p.la]); }); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    [['lyP', ['pts']], ['lyZ', ['zpts']], ['lyB', ['bys']], ['lyD', ['dss']], ['lyL', ['lbl']]].forEach(([id, ls]) => document.getElementById(id).addEventListener('change', e => vis(ls, e.target.checked)));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && !['lbl', 'dss'].includes(l.id)).map(l => l.id);
    document.getElementById('lyM').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    const dy = document.getElementById('dy'), play = document.getElementById('play');
    dy.addEventListener('input', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; } setDec(+dy.value); });
    play.addEventListener('click', () => {
      if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; return; }
      let i = dec >= 11 ? 0 : dec; setDec(i); play.textContent = 'Pause';
      timer = setInterval(() => { i += 1; setDec(i); if (i >= 11) { clearInterval(timer); timer = null; play.textContent = 'Play'; } }, 1100);
    });
    refresh(); setDec(12);
  }
  function go(i) {
    const p = D.p[i]; fold(true);
    map.flyTo({ center: [p.lo, p.la], zoom: small ? 9 : 9.5, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.3 : 0.22))] });
    map.once('moveend', () => popup(i, [p.lo, p.la]));
  }
  function searchBox(inp, sug, onPick) {
    let items = [], k = -1;
    const idx = D.p.map((p, i) => ({ t: p.n, nn: norm(p.n), i, s: p.nat })).sort((a, b) => D.p[b.i].d[12] - D.p[a.i].d[12]);
    const show = () => { const v = norm(inp.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 3 && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; inp.value = it.t; sug.style.display = 'none'; onPick(it.i); };
    inp.addEventListener('input', show);
    inp.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    inp.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  // ---------------------------------------------------------------- place explorer
  const svg = document.getElementById('exChart'), tip = document.getElementById('eTip');
  function series(t) {
    const a = M.p[t] || [], y = new Float64Array(M.nm); let k = -1;
    for (let j = 0; j < a.length; j += 2) { k += a[j]; y[k] = a[j + 1]; }
    return y;
  }
  function draw() {
    if (!M || cur == null) return;
    const p = D.p[cur], ys = series(p.n), res = document.querySelector('input[name=eres]:checked').value, share = document.getElementById('eShare').checked;
    let pts = [];
    if (res === 'y') { for (let y = 0; y * 12 < M.nm; y++) { let s = 0, tt = 0; for (let m = y * 12; m < Math.min(M.nm, y * 12 + 12); m++) { s += ys[m]; tt += M.tot[m]; } pts.push({ k: y * 12, v: share ? (tt ? 100 * s / tt : 0) : s, lab: `${1909 + y}${1909 + y === 1909 || 1909 + y === 2026 ? ' (part year)' : ''}`, raw: s }); } }
    else { for (let m = 0; m < M.nm; m++) pts.push({ k: m, v: share ? (M.tot[m] ? 100 * ys[m] / M.tot[m] : 0) : ys[m], lab: ym(m), raw: ys[m] }); }
    const W = 700, H = 260, L = 46, R = 10, T = 14, B = 34, mx = Math.max(...pts.map(x => x.v), share ? 0.01 : 1);
    const X = k => L + (W - L - R) * k / M.nm, Yv = v => H - B - (H - B - T) * v / mx, bw = Math.max(0.6, (W - L - R) * (res === 'y' ? 12 : 1) / M.nm - (res === 'y' ? 1 : 0));
    let s = '';
    const ticks = 4; for (let i = 0; i <= ticks; i++) { const v = mx * i / ticks, y = Yv(v); s += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="var(--rule)" stroke-width="1"/><text x="${L - 6}" y="${y + 4}" font-size="11" text-anchor="end" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${share ? v.toFixed(v < 1 ? 2 : 1) + '%' : (v >= 10 ? Math.round(v) : v.toFixed(1))}</text>`; }
    for (let y = 1910; y <= 2020; y += 10) { const x = X((y - 1909) * 12); s += `<text x="${x}" y="${H - B + 16}" font-size="11" text-anchor="middle" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${y}</text>`; }
    pts.forEach(q => { if (q.v > 0) s += `<rect x="${X(q.k).toFixed(1)}" y="${Yv(q.v).toFixed(1)}" width="${bw.toFixed(2)}" height="${(H - B - Yv(q.v)).toFixed(1)}" fill="#B4442E"/>`; });
    (p.by || []).forEach(b => { const x = X(mi(b[0])); s += `<line x1="${x}" x2="${x}" y1="${H - B}" y2="${H - B + 6}" stroke="#2F6A9E" stroke-width="2.4"/><line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="#2F6A9E" stroke-width="0.8" stroke-dasharray="2 3" opacity=".7"/>`; });
    (p.ds || []).forEach(d => { const x = X(mi(d[0])); s += `<path d="M${x - 5} ${H - B + 9} L${x + 5} ${H - B + 9} L${x} ${H - B + 1} Z" fill="#C98A2B" stroke="#fff" stroke-width="1"/><line x1="${x}" x2="${x}" y1="${T}" y2="${H - B}" stroke="#C98A2B" stroke-width="0.8" stroke-dasharray="2 3" opacity=".8"/>`; });
    s += `<line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="var(--muted)"/>`;
    svg.innerHTML = s;
    svg.onpointermove = e => { const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) * W / r.width, k = (x - L) / (W - L - R) * M.nm; if (k < 0 || k >= M.nm) { tip.style.display = 'none'; return; }
      const q = res === 'y' ? pts[Math.floor(k / 12)] : pts[Math.floor(k)]; if (!q) return;
      tip.style.display = 'block'; tip.textContent = `${q.lab}: ${fmt(q.raw)} speech${q.raw === 1 ? '' : 'es'}${share ? ` (${q.v.toFixed(2)}%)` : ''}`;
      tip.style.left = Math.min(r.width - 170, Math.max(0, e.clientX - r.left - 60)) + 'px'; tip.style.top = '0px'; };
    svg.onpointerleave = () => { tip.style.display = 'none'; };
    document.getElementById('eName').textContent = p.n;
    let tot = 0, pk = 0, pkY = 0; for (let y = 1; y < 117; y++) { let s2 = 0; for (let m = y * 12; m < y * 12 + 12 && m < M.nm; m++) s2 += ys[m]; tot += s2; if (s2 > pk) { pk = s2; pkY = 1909 + y; } }
    document.getElementById('eSub').textContent = `${p.nat}. ${fmt(p.d[12])} Commons speeches said "in ${p.n}" from ${D.decades[12]}${pk ? `; busiest year ${pkY} (${fmt(pk)})` : ''}.`;
    const ev = [];
    (p.by || []).forEach(b => ev.push(`<span style="color:#2F6A9E">●</span> ${b[0].slice(0, 4)} ${esc(b[1])} by-election${b[2] ? ' (seat changed hands)' : ''}`));
    (p.ds || []).forEach(d => ev.push(`<span style="color:#C98A2B">▲</span> ${d[0].slice(0, 4)} ${esc(d[1])}${d[2] ? `, ${d[2]} deaths` : ''}${d[3] > 0 ? ` (${d[3]} km away)` : ''}`));
    document.getElementById('eEv').innerHTML = ev.length ? ev.join('<br>') : 'No by-election in a seat named after it, and no disaster from the list near it.';
  }
  function explore(i) {
    cur = i; document.getElementById('eq').value = D.p[i].n;
    if (M) { draw(); return; }
    document.getElementById('eSub').textContent = 'Loading the monthly counts...';
    fetch('data/monthly.json').then(r => r.json()).then(m => { M = m; draw(); }).catch(e => { document.getElementById('eSub').textContent = 'Could not load the monthly counts.'; console.error(e); });
  }
  document.querySelectorAll('input[name=eres]').forEach(r => r.addEventListener('change', draw));
  document.getElementById('eShare').addEventListener('change', draw);

  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    searchBox(document.getElementById('eq'), document.getElementById('esug'), i => explore(i));
    const start = D.p.findIndex(p => p.n === (qs.get('place') || 'Jarrow'));
    const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { explore(cur != null ? cur : Math.max(0, start)); io.disconnect(); } }, { rootMargin: '300px' });
    io.observe(document.getElementById('ex'));
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-8.3, 49.9], [1.9, 58.8]], fitBoundsOptions: { padding: small ? { top: 10, bottom: 60, left: 10, right: 10 } : { top: 40, bottom: 70, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); searchBox(document.getElementById('q'), document.getElementById('sug'), i => go(i));
  }).catch(e => { const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + (e && e.message || e); console.error(e); });
})();
