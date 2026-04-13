"""
VandalOptics
Capstone Design Teams 1

Description:
    Flask web server to display MeasurementResults.json as a live graph.
    Auto-refreshes every 5 seconds. No frontend build step required.

Dependencies:
    flask

Usage:
    python WebContentServe.py
    Open http://localhost:5000 in your browser.

Authors:
    Capstone Team 1
"""

import json
import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

RESULTS_FILE = "MeasurementResults.json"

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VandalOptics — Volume Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;500;700&display=swap');

  :root {
    --bg:       #0a0e14;
    --surface:  #111820;
    --border:   #1e2d3d;
    --accent:   #00d4ff;
    --accent2:  #ff6b35;
    --text:     #c9d6e3;
    --muted:    #4a6070;
    --good:     #39d98a;
    --warn:     #f7b731;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Barlow', sans-serif;
    font-weight: 300;
    min-height: 100vh;
    padding: 2rem;
  }

  /* Subtle grid background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(var(--border) 1px, transparent 1px),
      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 40px 40px;
    opacity: 0.4;
    pointer-events: none;
    z-index: 0;
  }

  .content { position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; }

  header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 2.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }

  .logo {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
  }

  h1 {
    font-size: 1.9rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.02em;
  }

  .status-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
  }

  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--good);
    animation: pulse 2s infinite;
  }
  .status-dot.stale { background: var(--warn); animation: none; }
  .status-dot.error { background: #e05c5c; animation: none; }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
  }

  /* Stat cards */
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
  }

  .card.accent2::before { background: var(--accent2); }
  .card.good::before    { background: var(--good); }
  .card.warn::before    { background: var(--warn); }

  .card-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.6rem;
  }

  .card-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.8rem;
    color: #fff;
    line-height: 1;
  }

  .card-unit {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.3rem;
  }

  /* Chart panel */
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.25rem;
  }

  .panel-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--accent);
  }

  .legend {
    display: flex;
    gap: 1rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
  }

  .legend span { display: flex; align-items: center; gap: 5px; }
  .legend-dot  { width: 8px; height: 8px; border-radius: 50%; }

  .chart-wrap { position: relative; height: 260px; }

  /* Controls */
  .controls {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }

  .btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn:hover        { border-color: var(--accent); color: var(--accent); }
  .btn.active       { border-color: var(--accent); color: var(--accent); background: rgba(0,212,255,0.07); }

  /* Footer */
  footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>
<div class="content">

  <header>
    <div>
      <div class="logo">VandalOptics // Capstone Team 1</div>
      <h1>Volume Monitor</h1>
    </div>
    <div class="status-bar">
      <div class="status-dot" id="statusDot"></div>
      <span id="statusText">connecting...</span>
    </div>
  </header>

  <div class="stats">
    <div class="card good">
      <div class="card-label">Current Volume</div>
      <div class="card-value" id="statVolEst">—</div>
      <div class="card-unit">% estimated</div>
    </div>
    <div class="card accent2">
      <div class="card-label">Raw Volume</div>
      <div class="card-value" id="statVolRaw">—</div>
      <div class="card-unit">% interpolated</div>
    </div>
    <div class="card">
      <div class="card-label">Power Reading</div>
      <div class="card-value" id="statPower">—</div>
      <div class="card-unit">µW</div>
    </div>
    <div class="card warn">
      <div class="card-label">Total Samples</div>
      <div class="card-value" id="statCount">—</div>
      <div class="card-unit">measurements</div>
    </div>
  </div>

  <div class="controls">
    <button class="btn" onclick="setWindow(50)">Last 50</button>
    <button class="btn active" id="btn100" onclick="setWindow(100)">Last 100</button>
    <button class="btn" onclick="setWindow(500)">Last 500</button>
    <button class="btn" onclick="setWindow(0)">All</button>
  </div>

  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Volume % Over Time</div>
      <div class="legend">
        <span><span class="legend-dot" style="background:#39d98a"></span>estimated</span>
        <span><span class="legend-dot" style="background:#ff6b35"></span>raw</span>
      </div>
    </div>
    <div class="chart-wrap">
      <canvas id="volChart" role="img" aria-label="Volume percentage over time, showing estimated and raw values"></canvas>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">Power Reading (µW) Over Time</div>
      <div class="legend">
        <span><span class="legend-dot" style="background:#00d4ff"></span>power</span>
      </div>
    </div>
    <div class="chart-wrap">
      <canvas id="pwrChart" role="img" aria-label="Optical power in microwatts over time"></canvas>
    </div>
  </div>

  <footer>
    <span>870nm fiber optic bend sensor</span>
    <span id="footerTs">—</span>
  </footer>

</div>

<script>
  let windowSize = 100;
  let allData    = [];
  let volChart, pwrChart;

  const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: { legend: { display: false } },
    elements: { point: { radius: 0, hoverRadius: 4 } },
    scales: {
      x: {
        ticks: { color: '#4a6070', font: { family: 'Share Tech Mono', size: 10 }, maxTicksLimit: 8, maxRotation: 0 },
        grid:  { color: 'rgba(30,45,61,0.8)' },
      },
      y: {
        ticks: { color: '#4a6070', font: { family: 'Share Tech Mono', size: 10 } },
        grid:  { color: 'rgba(30,45,61,0.8)' },
      }
    }
  };

  function makeLabel(ts) {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function initCharts() {
    volChart = new Chart(document.getElementById('volChart'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'estimated',
            data: [],
            borderColor: '#39d98a',
            borderWidth: 2,
            fill: { target: 'origin', above: 'rgba(57,217,138,0.06)' },
            tension: 0.3,
          },
          {
            label: 'raw',
            data: [],
            borderColor: '#ff6b35',
            borderWidth: 1,
            borderDash: [4, 3],
            fill: false,
            tension: 0.3,
          }
        ]
      },
      options: {
        ...CHART_DEFAULTS,
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, min: 0, max: 100,
               ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } }
        }
      }
    });

    pwrChart = new Chart(document.getElementById('pwrChart'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'power',
          data: [],
          borderColor: '#00d4ff',
          borderWidth: 1.5,
          fill: { target: 'origin', above: 'rgba(0,212,255,0.05)' },
          tension: 0.2,
        }]
      },
      options: {
        ...CHART_DEFAULTS,
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y,
               ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v.toFixed(3) + ' µW' } }
        }
      }
    });
  }

  function updateCharts() {
    const slice = windowSize === 0 ? allData : allData.slice(-windowSize);
    const labels    = slice.map(d => makeLabel(d.timestamp));
    const volEst    = slice.map(d => +d.volume_est.toFixed(2));
    const volRaw    = slice.map(d => +d.volume_raw.toFixed(2));
    const power     = slice.map(d => +(d.reading * 1e6).toFixed(4));  // W → µW

    volChart.data.labels              = labels;
    volChart.data.datasets[0].data    = volEst;
    volChart.data.datasets[1].data    = volRaw;
    volChart.update('none');

    pwrChart.data.labels              = labels;
    pwrChart.data.datasets[0].data    = power;
    pwrChart.update('none');

    // Stat cards
    if (slice.length > 0) {
      const last = slice[slice.length - 1];
      document.getElementById('statVolEst').textContent = last.volume_est.toFixed(1);
      document.getElementById('statVolRaw').textContent = last.volume_raw.toFixed(1);
      document.getElementById('statPower').textContent  = (last.reading * 1e6).toFixed(4);
      document.getElementById('statCount').textContent  = allData.length;
      document.getElementById('footerTs').textContent   = 'last update: ' + makeLabel(last.timestamp);
    }
  }

  async function fetchData() {
    try {
      const res  = await fetch('/data');
      if (!res.ok) throw new Error('bad response');
      const data = await res.json();

      allData = data;
      updateCharts();

      // Status
      const dot  = document.getElementById('statusDot');
      const txt  = document.getElementById('statusText');
      if (data.length === 0) {
        dot.className = 'status-dot stale';
        txt.textContent = 'no data yet';
      } else {
        const age = Date.now() / 1000 - data[data.length - 1].timestamp;
        if (age < 60) {
          dot.className = 'status-dot';
          txt.textContent = 'live';
        } else {
          dot.className = 'status-dot stale';
          txt.textContent = `last update ${Math.round(age)}s ago`;
        }
      }
    } catch (e) {
      document.getElementById('statusDot').className = 'status-dot error';
      document.getElementById('statusText').textContent = 'read error';
    }
  }

  function setWindow(n) {
    windowSize = n;
    document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    updateCharts();
  }

  // Boot
  initCharts();
  fetchData();
  setInterval(fetchData, 5000);
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/data')
def data():
    """Return the full MeasurementResults.json as JSON."""
    if not os.path.exists(RESULTS_FILE):
        return jsonify([])
    try:
        with open(RESULTS_FILE, 'r') as f:
            records = json.load(f)
        return jsonify(records)
    except (json.JSONDecodeError, IOError):
        # File may be mid-write — return empty rather than crash
        return jsonify([])


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print(f"VandalOptics Volume Monitor")
    print(f"Serving from: {os.path.abspath(RESULTS_FILE)}")
    print(f"Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
