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

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Volume Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>

<h1>Volume Monitor</h1>
<hr>

<p>
  Current volume: <b id="statVolEst">--</b>%
  &nbsp;|&nbsp;
  Status: <span id="statusText">connecting...</span>
  &nbsp;|&nbsp;
  Samples: <span id="statCount">--</span>
  &nbsp;|&nbsp;
  Last update: <span id="footerTs">--</span>
</p>

<hr>

Show last:
<a href="#" onclick="setWindow(50);return false;">50</a> |
<a href="#" onclick="setWindow(100);return false;">100</a> |
<a href="#" onclick="setWindow(500);return false;">500</a> |
<a href="#" onclick="setWindow(0);return false;">all</a>

<br><br>

<b>Volume % over time</b><br>
<canvas id="volChart" width="900" height="300" role="img" aria-label="Volume percentage over time"></canvas>

<hr>

<script>
  let windowSize = 100;
  let allData = [];
  let volChart;

  function makeLabel(ts) {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function initChart() {
    volChart = new Chart(document.getElementById('volChart'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'estimated %',
            data: [],
            borderColor: 'blue',
            borderWidth: 1,
            fill: false,
            tension: 0,
            pointRadius: 0,
          },
          {
            label: 'raw %',
            data: [],
            borderColor: 'red',
            borderWidth: 1,
            borderDash: [4, 3],
            fill: false,
            tension: 0,
            pointRadius: 0,
          }
        ]
      },
      options: {
        responsive: false,
        animation: false,
        plugins: { legend: { display: true } },
        scales: {
          x: { ticks: { maxTicksLimit: 8, maxRotation: 0 } },
          y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }
        }
      }
    });
  }

  function updateChart() {
    const slice = windowSize === 0 ? allData : allData.slice(-windowSize);
    volChart.data.labels           = slice.map(d => makeLabel(d.timestamp));
    volChart.data.datasets[0].data = slice.map(d => +d.volume_est.toFixed(2));
    volChart.data.datasets[1].data = slice.map(d => +d.volume_raw.toFixed(2));
    volChart.update('none');

    if (slice.length > 0) {
      const last = slice[slice.length - 1];
      document.getElementById('statVolEst').textContent = last.volume_est.toFixed(1);
      document.getElementById('statCount').textContent  = allData.length;
      document.getElementById('footerTs').textContent   = makeLabel(last.timestamp);
    }
  }

  async function fetchData() {
    try {
      const res  = await fetch('/data');
      allData = await res.json();
      updateChart();

      const age = allData.length
        ? Date.now() / 1000 - allData[allData.length - 1].timestamp
        : null;

      document.getElementById('statusText').textContent =
        allData.length === 0 ? 'no data yet' :
        age < 60             ? 'live' :
                               `stale (${Math.round(age)}s ago)`;
    } catch (e) {
      document.getElementById('statusText').textContent = 'error';
    }
  }

  function setWindow(n) {
    windowSize = n;
    updateChart();
  }

  initChart();
  fetchData();
  setInterval(fetchData, 5000);
</script>
</body>
</html>
"""


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


if __name__ == '__main__':
    print(f"VandalOptics Volume Monitor")
    print(f"Serving from: {os.path.abspath(RESULTS_FILE)}")
    print(f"Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=False)