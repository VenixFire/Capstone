"""
VandalOptics
Capstone Design Teams 1

Description:
    Flask web server to display MeasurementResults as live graphs.
    Auto-refreshes every 5 seconds. No frontend build step required.
    Reads result files from the path specified in DeviceDescription.json.

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
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DeviceData"))


def get_results_dir() -> str:
    return os.path.join(BASE_DIR, "MeasurementResults")


def get_calibrations_dir() -> str:
    return os.path.join(BASE_DIR, "Calibrations")


def get_logs_dir() -> str:
    return os.path.join(BASE_DIR, "Logs")


def get_device_description_path() -> str:
    return os.path.join(BASE_DIR, "DeviceDescription.json")


def load_device_description() -> dict:
    path = get_device_description_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_device_description(data: dict) -> None:
    with open(get_device_description_path(), "w") as f:
        json.dump(data, f, indent=2)


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Volume Monitor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>

<h1>Volume Monitor</h1>
<p><a href="/settings">Device settings</a></p>
<hr>

<p>
  File:
  <select id="fileSelect" onchange="onFileChange()">
    <option value="">Loading...</option>
  </select>
  &nbsp;|&nbsp;
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

<br><br>

<b>Power reading (W) over time</b><br>
<canvas id="pwrChart" width="900" height="250" role="img" aria-label="Power reading in watts over time"></canvas>

<hr>

<script>
  let windowSize = 100;
  let allData = [];
  let volChart, pwrChart;
  let currentFile = '';

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

    pwrChart = new Chart(document.getElementById('pwrChart'), {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'power (W)',
            data: [],
            borderColor: 'green',
            borderWidth: 1,
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
          y: { ticks: { callback: v => v.toExponential(2) } }
        }
      }
    });
  }

  function updateCharts() {
    const slice = windowSize === 0 ? allData : allData.slice(-windowSize);
    const labels = slice.map(d => makeLabel(d.timestamp));

    volChart.data.labels           = labels;
    volChart.data.datasets[0].data = slice.map(d => +d.volume_est.toFixed(2));
    volChart.data.datasets[1].data = slice.map(d => +d.volume_raw.toFixed(2));
    volChart.update('none');

    pwrChart.data.labels           = labels;
    pwrChart.data.datasets[0].data = slice.map(d => d.reading);
    pwrChart.update('none');

    if (slice.length > 0) {
      const last = slice[slice.length - 1];
      document.getElementById('statVolEst').textContent = last.volume_est.toFixed(1);
      document.getElementById('statCount').textContent  = allData.length;
      document.getElementById('footerTs').textContent   = makeLabel(last.timestamp);
    }
  }

  async function loadFiles() {
    try {
      const res   = await fetch('/files');
      const files = await res.json();
      const sel   = document.getElementById('fileSelect');
      sel.innerHTML = '';
      if (files.length === 0) {
        sel.innerHTML = '<option value="">No result files found</option>';
        return;
      }
      files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f;
        opt.textContent = f;
        sel.appendChild(opt);
      });
      currentFile = files[0];
    } catch (e) {
      console.error('Failed to load file list', e);
    }
  }

  function onFileChange() {
    currentFile = document.getElementById('fileSelect').value;
    allData = [];
    updateCharts();
    fetchData();
  }

  async function fetchData() {
    if (!currentFile) return;
    try {
      const res = await fetch('/data?file=' + encodeURIComponent(currentFile));
      allData = await res.json();
      updateCharts();

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
    updateCharts();
  }

  (async () => {
    initCharts();
    await loadFiles();
    await fetchData();
    setInterval(fetchData, 5000);
  })();
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


def list_json_files(directory: str):
    """Return a sorted list of .json filenames in a directory."""
    if not os.path.isdir(directory):
        return jsonify([])
    names = sorted(f for f in os.listdir(directory) if f.endswith('.json'))
    return jsonify(names)


def serve_json_file(directory: str, filename: str):
    """Return a single .json file from a directory as JSON."""
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    # Prevent path traversal — basename only
    filename = os.path.basename(filename)
    path = os.path.join(directory, filename)

    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    try:
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, IOError) as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list/calibration')
def list_calibration():
    """Return a list of calibration file names."""
    return list_json_files(get_calibrations_dir())


@app.route('/list/measurements')
def list_measurements():
    """Return a list of measurement file names."""
    return list_json_files(get_results_dir())


@app.route('/calibration')
def calibration():
    """Return a calibration file by name. Accepts ?<filename>."""
    filename = request.query_string.decode()
    return serve_json_file(get_calibrations_dir(), filename)


@app.route('/measurement')
def measurement():
    """Return a measurement file by name. Accepts ?<filename>."""
    filename = request.query_string.decode()
    return serve_json_file(get_results_dir(), filename)


# Legacy endpoint — kept for the web UI
@app.route('/files')
def files():
    """Return a list of .json result files available in the MeasurementResults directory."""
    return list_json_files(get_results_dir())


# Legacy endpoint — kept for the web UI
@app.route('/data')
def data():
    """Return the selected result file as JSON. Accepts ?file=<filename>."""
    filename = request.args.get('file', '')
    return serve_json_file(get_results_dir(), filename)


SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Device Settings</title>
</head>
<body>

<h1>Device Settings</h1>
<p><a href="/">&#8592; Back to monitor</a></p>
<hr>

<p id="statusMsg"></p>

<table>
  <tr>
    <td><label for="deviceName">Device name</label></td>
    <td><input id="deviceName" type="text" size="40"></td>
  </tr>
  <tr>
    <td><label for="calSelect">Calibration file</label></td>
    <td>
      <select id="calSelect">
        <option value="">Loading...</option>
      </select>
    </td>
  </tr>
  <tr>
    <td><label for="resultsSelect">Results file</label></td>
    <td>
      <select id="resultsSelect">
        <option value="">Loading...</option>
      </select>
    </td>
  </tr>
  <tr>
    <td></td>
    <td><br><button onclick="saveSettings()">Save</button></td>
  </tr>
</table>

<hr>

<h2>New measurement file</h2>
<p>
  <input id="newMeasName" type="text" size="30" placeholder="filename (without .json)">
  <button onclick="createMeasurement()">Create</button>
  <span id="newMeasMsg"></span>
</p>

<hr>

<h2>Logs</h2>
<ul id="logList"><li>Loading...</li></ul>

<script>
  async function loadSettings() {
    const [settingsRes, calRes, measRes] = await Promise.all([
      fetch('/api/settings'),
      fetch('/list/calibration'),
      fetch('/list/measurements'),
    ]);

    const settings = await settingsRes.json();
    const calFiles  = await calRes.json();
    const measFiles = await measRes.json();

    document.getElementById('deviceName').value = settings.DeviceName || '';

    populateSelect('calSelect',     calFiles,  settings.CalibrationFile);
    populateSelect('resultsSelect', measFiles, settings.ResultsFile);
  }

  function populateSelect(id, files, current) {
    const sel = document.getElementById(id);
    sel.innerHTML = '';
    if (files.length === 0) {
      sel.innerHTML = '<option value="">No files found</option>';
      return;
    }
    files.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f;
      opt.textContent = f;
      if (f === current) opt.selected = true;
      sel.appendChild(opt);
    });
  }

  async function saveSettings() {
    const body = {
      DeviceName:      document.getElementById('deviceName').value.trim(),
      CalibrationFile: document.getElementById('calSelect').value,
      ResultsFile:     document.getElementById('resultsSelect').value,
    };

    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const msg = document.getElementById('statusMsg');
    if (res.ok) {
      msg.textContent = 'Settings saved.';
    } else {
      const err = await res.json();
      msg.textContent = 'Error: ' + (err.error || res.status);
    }
  }

  async function loadLogs() {
    const res  = await fetch('/list/logs');
    const logs = await res.json();
    const ul   = document.getElementById('logList');
    ul.innerHTML = '';
    if (logs.length === 0) {
      ul.innerHTML = '<li>No log files found.</li>';
      return;
    }
    logs.forEach(name => {
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href        = '/log-view?' + encodeURIComponent(name);
      a.textContent = name;
      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  async function createMeasurement() {
    const input = document.getElementById('newMeasName');
    const msg   = document.getElementById('newMeasMsg');
    let name = input.value.trim();
    if (!name) { msg.textContent = 'Enter a filename.'; return; }
    if (!name.endsWith('.json')) name += '.json';

    const res = await fetch('/api/measurement/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: name }),
    });
    const data = await res.json();
    if (res.ok) {
      msg.textContent = name + ' created.';
      input.value = '';
      // Refresh the results dropdown
      const measRes  = await fetch('/list/measurements');
      const measFiles = await measRes.json();
      const settings  = await (await fetch('/api/settings')).json();
      populateSelect('resultsSelect', measFiles, settings.ResultsFile);
    } else {
      msg.textContent = 'Error: ' + (data.error || res.status);
    }
  }

  loadSettings();
  loadLogs();
</script>
</body>
</html>
"""


@app.route('/settings')
def settings_page():
    """Render the device settings page."""
    return render_template_string(SETTINGS_HTML)


@app.route('/api/settings', methods=['GET'])
def api_settings_get():
    """Return the current DeviceDescription.json as JSON."""
    return jsonify(load_device_description())


@app.route('/api/settings', methods=['POST'])
def api_settings_post():
    """
    Update DeviceDescription.json.
    Accepts JSON body with any subset of fields; merges into existing description.
    """
    updates = request.get_json(silent=True)
    if not updates:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    desc = load_device_description()
    desc.update(updates)
    save_device_description(desc)
    return jsonify({'ok': True})


LOG_VIEW_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Log View</title>
</head>
<body>

<p><a href="/settings">&#8592; Back to settings</a></p>
<hr>

<h1 id="logTitle">Loading...</h1>
<p><button onclick="deleteLog()">Delete this log</button></p>
<pre id="logContent">Loading...</pre>

<script>
  const filename = decodeURIComponent(window.location.search.slice(1));
  document.getElementById('logTitle').textContent = filename;
  document.title = filename;

  fetch('/log?' + encodeURIComponent(filename))
    .then(res => {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.text();
    })
    .then(text => {
      document.getElementById('logContent').textContent = text || '(empty)';
    })
    .catch(err => {
      document.getElementById('logContent').textContent = 'Error loading log: ' + err.message;
    });

  async function deleteLog() {
    if (!confirm('Delete ' + filename + '?')) return;
    const res = await fetch('/api/log/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    if (res.ok) {
      window.location.href = '/settings';
    } else {
      const data = await res.json();
      alert('Error: ' + (data.error || res.status));
    }
  }
</script>
</body>
</html>
"""


@app.route('/log-view')
def log_view_page():
    """Render the log viewer page. Filename is passed as the query string."""
    return render_template_string(LOG_VIEW_HTML)


@app.route('/list/logs')
def list_logs():
    """Return a sorted list of log filenames in the Logs directory."""
    logs_dir = get_logs_dir()
    if not os.path.isdir(logs_dir):
        return jsonify([])
    names = sorted(
        (f for f in os.listdir(logs_dir) if f.endswith('.txt')),
        reverse=True
    )
    return jsonify(names)


@app.route('/log')
def log():
    """Return the plaintext content of a log file. Accepts ?<filename>."""
    filename = request.query_string.decode()
    if not filename:
        return 'No filename provided', 400

    filename = os.path.basename(filename)
    path = os.path.join(get_logs_dir(), filename)

    if not os.path.exists(path):
        return 'Log file not found', 404
    try:
        with open(path, 'r', errors='replace') as f:
            return f.read(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except IOError as e:
        return str(e), 500


@app.route('/api/measurement/create', methods=['POST'])
def api_measurement_create():
    """Create a new empty measurement JSON file in MeasurementResults."""
    body = request.get_json(silent=True)
    if not body or not body.get('filename'):
        return jsonify({'error': 'No filename provided'}), 400

    filename = os.path.basename(body['filename'])
    if not filename.endswith('.json'):
        filename += '.json'

    path = os.path.join(get_results_dir(), filename)
    os.makedirs(get_results_dir(), exist_ok=True)

    if os.path.exists(path):
        return jsonify({'error': 'File already exists'}), 409

    with open(path, 'w') as f:
        json.dump([], f)
    return jsonify({'ok': True, 'filename': filename})


@app.route('/api/log/delete', methods=['POST'])
def api_log_delete():
    """Delete a log file by name."""
    body = request.get_json(silent=True)
    if not body or not body.get('filename'):
        return jsonify({'error': 'No filename provided'}), 400

    filename = os.path.basename(body['filename'])
    path = os.path.join(get_logs_dir(), filename)

    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404

    os.remove(path)
    return jsonify({'ok': True})


if __name__ == '__main__':
    results_dir = get_results_dir()
    print(f"VandalOptics Volume Monitor")
    print(f"Serving results from: {results_dir}")
    print(f"Open http://localhost:5000 in your browser\n")
    app.run(host='0.0.0.0', port=5000, debug=False)