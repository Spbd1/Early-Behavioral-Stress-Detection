const state = { payload: null };

const EMPTY_PAYLOAD = {
  schema_version: 'dashboard.v1',
  label: 'Experimental dashboard: no data payload found.',
  system: {
    label: 'Experimental dashboard: no data payload found.',
    claim_guardrail: 'BSI values are research signals and are not recession predictions.',
    experimental: true
  },
  locations: { countries: [], regions: {}, cities: {} },
  geo_metadata: { reliability_notes: [] },
  warnings: {
    data_quality: ['Run scripts/build_frontend_data.py or start the API server.'],
    drift: [],
    geo_reliability: ['No generated geo reliability metadata is available.']
  },
  quality_warnings: ['Run scripts/build_frontend_data.py or start the API server.'],
  drift_warnings: [],
  geo_reliability_warnings: ['No generated geo reliability metadata is available.'],
  bsi: [],
  posterior: [],
  alerts: [],
  top_signals: [],
  geo_comparison: [],
  report: {},
  reports: { export_filename: 'experimental-behavioral-stress-report.json' },
  static_mode: { supported: true, data_file: 'dashboard.json', requires_backend: false }
};

async function loadPayload() {
  const sources = ['/api/dashboard.json', 'dashboard.json'];
  for (let i = 0; i < sources.length; i += 1) {
    try {
      const response = await fetch(sources[i], { cache: 'no-store' });
      if (response.ok) return normalizePayload(await response.json());
    } catch (error) { /* Try the static fallback. */ }
  }
  return normalizePayload(EMPTY_PAYLOAD);
}

function normalizePayload(payload) {
  const normalized = Object.assign({}, EMPTY_PAYLOAD, payload || {});
  normalized.locations = normalized.locations || EMPTY_PAYLOAD.locations;
  normalized.warnings = normalized.warnings || {};
  normalized.quality_warnings = normalized.quality_warnings || normalized.warnings.data_quality || [];
  normalized.drift_warnings = normalized.drift_warnings || normalized.warnings.drift || [];
  normalized.geo_reliability_warnings = normalized.geo_reliability_warnings || normalized.warnings.geo_reliability || [];
  normalized.report = normalized.report || (normalized.reports && normalized.reports.primary) || {};
  normalized.reports = normalized.reports || { primary: normalized.report, export_filename: EMPTY_PAYLOAD.reports.export_filename };
  normalized.system = normalized.system || EMPTY_PAYLOAD.system;
  return normalized;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendOption(select, value) {
  const option = document.createElement('option');
  option.textContent = value;
  option.value = value;
  select.appendChild(option);
}

function populateSelectors(payload) {
  const country = document.getElementById('country');
  const region = document.getElementById('region');
  const city = document.getElementById('city');
  clearChildren(country);
  (payload.locations.countries || []).forEach(item => appendOption(country, item));
  function updateRegions() {
    const regions = payload.locations.regions[country.value] || [];
    clearChildren(region);
    regions.forEach(item => appendOption(region, item));
    updateCities();
  }
  function updateCities() {
    const cities = payload.locations.cities[region.value] || ['All metros'];
    clearChildren(city);
    cities.forEach(item => appendOption(city, item));
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
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.width = canvas.clientWidth * ratio;
  const height = canvas.height = 220 * ratio;
  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = '#d8deea'; ctx.lineWidth = 1;
  for (let i = 0; i < 5; i += 1) { const y = 20 + i * (height - 40) / 4; ctx.beginPath(); ctx.moveTo(30, y); ctx.lineTo(width - 10, y); ctx.stroke(); }
  series.forEach((points, idx) => {
    ctx.strokeStyle = colors[idx % colors.length]; ctx.lineWidth = 2.5 * ratio; ctx.beginPath();
    points.forEach((value, i) => {
      const x = 30 + (i / Math.max(points.length - 1, 1)) * (width - 45);
      const y = height - 25 - (Number(value) / 100) * (height - 50);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
  ctx.fillStyle = '#5d6b82'; ctx.font = `${12 * ratio}px sans-serif`;
  ctx.fillText(labels[0] || '', 30, height - 5);
  ctx.fillText(labels[labels.length - 1] || '', width - 130, height - 5);
}

function renderList(id, rows, emptyMessage) {
  const list = document.getElementById(id);
  clearChildren(list);
  const values = rows && rows.length ? rows : [emptyMessage];
  values.forEach(value => {
    const li = document.createElement('li');
    li.textContent = value;
    list.appendChild(li);
  });
}

function renderAlerts(alerts) {
  const list = document.getElementById('alerts');
  clearChildren(list);
  if (!alerts || !alerts.length) {
    const li = document.createElement('li');
    li.textContent = 'No alerts available.';
    list.appendChild(li);
    return;
  }
  alerts.forEach(alert => {
    const li = document.createElement('li');
    li.className = alert.level || 'none';
    li.textContent = `${alert.date}: ${alert.level} — ${alert.message}`;
    list.appendChild(li);
  });
}

function renderSignals(signals) {
  const table = document.getElementById('signals');
  clearChildren(table);
  const header = table.insertRow();
  header.insertCell().textContent = 'Signal';
  header.insertCell().textContent = 'Contribution';
  (signals || []).forEach(signal => {
    const row = table.insertRow();
    row.insertCell().textContent = signal.signal;
    row.insertCell().textContent = signal.contribution;
  });
}

function renderGeoTable(rows) {
  const table = document.getElementById('geo-table');
  clearChildren(table);
  const header = table.insertRow();
  ['Country', 'Region', 'City', 'BSI', 'Reliability', 'Warnings'].forEach(label => { header.insertCell().textContent = label; });
  (rows || []).forEach(geo => {
    const row = table.insertRow();
    row.insertCell().textContent = geo.country;
    row.insertCell().textContent = geo.region;
    row.insertCell().textContent = geo.city;
    row.insertCell().textContent = geo.bsi;
    row.insertCell().textContent = geo.reliability_score;
    row.insertCell().textContent = (geo.warnings || []).join(' ');
  });
}

function render() {
  const payload = state.payload;
  const guardrail = payload.system && payload.system.claim_guardrail ? ` ${payload.system.claim_guardrail}` : '';
  setText('experiment-label', `${payload.label}${guardrail}`);
  const bsi = seriesWindow(payload.bsi || []);
  drawLineChart('bsi-chart', bsi.map(x => x.date), [bsi.map(x => x.value)], ['#3155d4']);
  const posteriorRows = seriesWindow(payload.posterior || []);
  const stateKeys = Object.keys(posteriorRows[0] || {}).filter(key => key.indexOf('state_') === 0);
  drawLineChart('posterior-chart', posteriorRows.map(row => row.date || Object.values(row)[0]), stateKeys.map(key => posteriorRows.map(row => Number(row[key]) * 100)), ['#3155d4', '#16a34a', '#b42318', '#a15c00']);
  renderAlerts(payload.alerts || []);
  renderSignals(payload.top_signals || []);
  renderList('quality', payload.quality_warnings || [], 'No blocking synthetic data warnings.');
  renderList('drift', payload.drift_warnings || [], 'No drift warnings emitted.');
  renderList('geo-warnings', payload.geo_reliability_warnings || [], 'No geo reliability warnings emitted.');
  renderGeoTable(payload.geo_comparison || []);
  setText('report', JSON.stringify(payload.report || {}, null, 2));
}

document.getElementById('export-report').addEventListener('click', () => {
  const filename = (state.payload.reports && state.payload.reports.export_filename) || 'experimental-behavioral-stress-report.json';
  const blob = new Blob([JSON.stringify(state.payload.report || state.payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

loadPayload().then(payload => { state.payload = payload; populateSelectors(payload); render(); window.addEventListener('resize', render); });
