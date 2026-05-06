const state = { payload: null };

async function loadPayload() {
  const sources = ['/api/dashboard.json', 'dashboard.json'];
  for (const source of sources) {
    try {
      const response = await fetch(source, { cache: 'no-store' });
      if (response.ok) return response.json();
    } catch (_) { /* Try the static fallback. */ }
  }
  return { label: 'Experimental dashboard: no data payload found.', locations: { countries: [], regions: {}, cities: {} }, bsi: [], posterior: [], alerts: [], top_signals: [], geo_comparison: [], quality_warnings: ['Run scripts/build_frontend_data.py or start the API server.'], drift_warnings: [], report: {} };
}

function populateSelectors(payload) {
  const country = document.getElementById('country');
  const region = document.getElementById('region');
  const city = document.getElementById('city');
  country.innerHTML = payload.locations.countries.map(item => `<option>${item}</option>`).join('');
  function updateRegions() {
    const regions = payload.locations.regions[country.value] || [];
    region.innerHTML = regions.map(item => `<option>${item}</option>`).join('');
    updateCities();
  }
  function updateCities() {
    const cities = payload.locations.cities[region.value] || ['All metros'];
    city.innerHTML = cities.map(item => `<option>${item}</option>`).join('');
  }
  country.addEventListener('change', () => { updateRegions(); render(); });
  region.addEventListener('change', () => { updateCities(); render(); });
  city.addEventListener('change', render);
  document.getElementById('time-range').addEventListener('change', render);
  updateRegions();
}

function seriesWindow(series) {
  const selected = document.getElementById('time-range').value;
  if (selected === 'all') return series;
  return series.slice(-Number(selected));
}

function drawLineChart(canvasId, labels, series, colors) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const width = canvas.width = canvas.clientWidth * window.devicePixelRatio;
  const height = canvas.height = 220 * window.devicePixelRatio;
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = '#d8deea'; ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) { const y = 20 + i * (height - 40) / 4; ctx.beginPath(); ctx.moveTo(30, y); ctx.lineTo(width - 10, y); ctx.stroke(); }
  series.forEach((points, idx) => {
    ctx.strokeStyle = colors[idx % colors.length]; ctx.lineWidth = 2.5 * window.devicePixelRatio; ctx.beginPath();
    points.forEach((value, i) => {
      const x = 30 + (i / Math.max(points.length - 1, 1)) * (width - 45);
      const y = height - 25 - (Number(value) / 100) * (height - 50);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
  ctx.fillStyle = '#5d6b82'; ctx.font = `${12 * window.devicePixelRatio}px sans-serif`;
  ctx.fillText(labels[0] || '', 30, height - 5);
  ctx.fillText(labels[labels.length - 1] || '', width - 130, height - 5);
}

function render() {
  const payload = state.payload;
  document.getElementById('experiment-label').textContent = payload.label;
  const bsi = seriesWindow(payload.bsi || []);
  drawLineChart('bsi-chart', bsi.map(x => x.date), [bsi.map(x => x.value)], ['#3155d4']);
  const posteriorRows = seriesWindow(payload.posterior || []);
  const stateKeys = Object.keys(posteriorRows[0] || {}).filter(key => key.startsWith('state_'));
  drawLineChart('posterior-chart', posteriorRows.map(row => Object.values(row)[0]), stateKeys.map(key => posteriorRows.map(row => Number(row[key]) * 100)), ['#3155d4', '#16a34a', '#b42318', '#a15c00']);
  document.getElementById('alerts').innerHTML = (payload.alerts || []).map(a => `<li class="${a.level}"><strong>${a.date}</strong>: ${a.level} — ${a.message}</li>`).join('') || '<li>No alerts available.</li>';
  document.getElementById('signals').innerHTML = '<tr><th>Signal</th><th>Contribution</th></tr>' + (payload.top_signals || []).map(s => `<tr><td>${s.signal}</td><td>${s.contribution}</td></tr>`).join('');
  document.getElementById('quality').innerHTML = (payload.quality_warnings || []).map(w => `<li>${w}</li>`).join('') || '<li>No blocking synthetic data warnings.</li>';
  document.getElementById('drift').innerHTML = (payload.drift_warnings || []).map(w => `<li>${w}</li>`).join('') || '<li>No drift warnings emitted.</li>';
  document.getElementById('geo-table').innerHTML = '<tr><th>Country</th><th>Region</th><th>City</th><th>BSI</th></tr>' + (payload.geo_comparison || []).map(g => `<tr><td>${g.country}</td><td>${g.region}</td><td>${g.city}</td><td>${g.bsi}</td></tr>`).join('');
  document.getElementById('report').textContent = JSON.stringify(payload.report || {}, null, 2);
}

document.getElementById('export-report').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify(state.payload.report || state.payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'experimental-behavioral-stress-report.json'; a.click(); URL.revokeObjectURL(url);
});

loadPayload().then(payload => { state.payload = payload; populateSelectors(payload); render(); window.addEventListener('resize', render); });
