document.addEventListener("DOMContentLoaded", () => {
  //Variables

  let status = 'disconnected'; //default status, will be updated by later function to change status light color.

  //End Variables

  const buttons = document.querySelectorAll('.webbutton');
  buttons.forEach(btn => {
    // ensure keyboard focusable if HTML missed it
    if (!btn.hasAttribute('tabindex')) btn.setAttribute('tabindex', '0');
    if (!btn.hasAttribute('role')) btn.setAttribute('role', 'button');

    // Add pressed class on pointer down
    btn.addEventListener('pointerdown', (e) => {
      // primary button only
      if (e.button === undefined || e.button === 0) {
        btn.classList.add('pressed');
      }
    });

    const removePressed = () => btn.classList.remove('pressed');
    btn.addEventListener('pointerup', removePressed);
    btn.addEventListener('pointercancel', removePressed);
    btn.addEventListener('pointerleave', removePressed);
    btn.addEventListener('blur', removePressed);

    // Keyboard support: Space/Enter
    btn.addEventListener('keydown', (e) => {
      if (e.key === ' ' || e.key === 'Spacebar' || e.key === 'Enter') {
        e.preventDefault();
        btn.classList.add('pressed');
      }
    });

    btn.addEventListener('keyup', (e) => {
      if (e.key === ' ' || e.key === 'Spacebar' || e.key === 'Enter') {
        e.preventDefault();
        btn.classList.remove('pressed');
        // trigger a programmatic click so any listeners run
        try { btn.click && btn.click(); } catch (err) {}
      }
    });
  });

  // Exit button: call into main via preload bridge, fallback to window.close()
  const exitBtn = document.getElementById('exit-button');
  if (exitBtn) {
    exitBtn.addEventListener('click', () => {
      if (window.electronAPI && typeof window.electronAPI.quit === 'function') {
        window.electronAPI.quit();
      } else {
        window.close();
      }
    });
  }

  // Calibrate button: ask main to open a new calibrate window
  const calibrateBtn = document.getElementById('calibrate-button');
  if (calibrateBtn) {
    calibrateBtn.addEventListener('click', () => {
      if (window.electronAPI && typeof window.electronAPI.openCalibrate === 'function') {
        window.electronAPI.openCalibrate();
      } else {
        // fallback: try to open a new window (may be blocked in some environments)
        window.open('calibrate.html', '_blank', 'width=800,height=650');
      }
    });
  }

  // Analyze button: open the local AI data analysis chat window
  const analyzeBtn = document.getElementById('analyze-button');
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => {
      if (window.electronAPI && typeof window.electronAPI.openAnalyze === 'function') {
        window.electronAPI.openAnalyze();
      } else {
        window.open('analyze.html', '_blank', 'width=900,height=700');
      }
    });
  }

  const offloadBtn = document.getElementById('offload-button');
  if (offloadBtn) {
    offloadBtn.addEventListener('click', async () => {
      if (!window.electronAPI || typeof window.electronAPI.offloadDataFromPi !== 'function') {
        alert('Off-load API unavailable. Check preload bridge configuration.');
        return;
      }

      offloadBtn.disabled = true;

      try {
        const result = await window.electronAPI.offloadDataFromPi({
          endpoint: 'http://192.168.1.50:5000/offload'
        });
        alert(`Off-load complete. Added ${result.added} item(s). Library now has ${result.total} item(s).`);
        if (typeof loadLibraryLogs === 'function') {
          await loadLibraryLogs();
        }
      } catch (error) {
        alert(`Off-load failed: ${error.message}`);
      } finally {
        offloadBtn.disabled = false;
      }
    });
  }

  const StatusLight = document.getElementById('statuslight');
  function updateStatusLight() {
    if (!StatusLight) return;
    if (status === 'connected') {
      StatusLight.style.backgroundColor = 'green';
    } else {
      StatusLight.style.backgroundColor = 'red';
    }
  }

  // initialize
  updateStatusLight();

  // Calibration instruction updates
  const instructionText = document.getElementById('instructiontext');
  const startCalibBtn = document.getElementById('startcalibbtn') || document.getElementById('startclibbtn');
  const emptyTankBtn = document.getElementById('emptytankbtn');
  const tankHalfBtn = document.getElementById('tankhalfbtn');
  const tankFullBtn = document.getElementById('tankfullbtn');

  const setStepEnabled = (btn, enabled) => {
    if (!btn) return;
    btn.disabled = !enabled;
    btn.setAttribute('aria-disabled', String(!enabled));
  };

  // Initial state: only Start is active until calibration flow begins.
  setStepEnabled(emptyTankBtn, false);
  setStepEnabled(tankHalfBtn, false);
  setStepEnabled(tankFullBtn, false);

  if (instructionText && startCalibBtn) {
    startCalibBtn.addEventListener('click', () => {
      instructionText.textContent = 'Empty the tank, then press Empty Tank.';
      setStepEnabled(emptyTankBtn, true);
      setStepEnabled(tankHalfBtn, false);
      setStepEnabled(tankFullBtn, false);
    });
  }

  if (instructionText && emptyTankBtn) {
    emptyTankBtn.addEventListener('click', () => {
      instructionText.textContent = 'Fill the tank halfway';
      setStepEnabled(emptyTankBtn, false);
      setStepEnabled(tankHalfBtn, true);
    });
  }

  if (instructionText && tankHalfBtn) {
    tankHalfBtn.addEventListener('click', () => {
      instructionText.textContent = 'Fill the tank completely';
      setStepEnabled(tankHalfBtn, false);
      setStepEnabled(tankFullBtn, true);
    });
  }

  if (instructionText && tankFullBtn) {
    tankFullBtn.addEventListener('click', () => {
      instructionText.textContent = 'Calibration steps complete. Save your calibration settings.';
      setStepEnabled(tankFullBtn, false);
    });
  }

  // wire refresh button to re-check status and update the light
  const refreshBtn = document.getElementById('refreshbutton');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      updateStatusLight();
    });
  }

  // Listen for status updates from main process

  // --- File table + filepeek: show library logs and selected JSON entry details ---
  const fileTableBody = document.querySelector('#file-table tbody');
  const filePeek = document.getElementById('filepeek');
  const filePeekMeta = document.getElementById('filepeek_meta');
  const filePeekText = document.getElementById('filepeek_text');
  const filePeekClose = document.getElementById('filepeek_close');

  const formatBytes = (bytes) => {
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB'];
    let value = bytes;
    let unitIdx = 0;
    while (value >= 1024 && unitIdx < units.length - 1) {
      value /= 1024;
      unitIdx += 1;
    }
    return `${value.toFixed(unitIdx === 0 ? 0 : 1)} ${units[unitIdx]}`;
  };

  const formatIsoDate = (value) => {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value || '-';
    return d.toLocaleString();
  };

  const hideFilePeek = () => {
    if (!filePeek) return;
    filePeek.classList.remove('active');
  };

  const showFilePeekEntry = (entry, filename, modified) => {
    if (!filePeek || !filePeekMeta || !filePeekText) return;
    filePeekMeta.textContent = `${filename} | ${modified}`;
    filePeekText.textContent = JSON.stringify(entry, null, 2);
    filePeek.classList.add('active');
  };

  if (filePeekClose) {
    filePeekClose.addEventListener('click', hideFilePeek);
  }

  function renderFileTable(files) {
    if (!fileTableBody) return;
    fileTableBody.innerHTML = '';

    if (!Array.isArray(files) || files.length === 0) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 3;
      td.textContent = 'No logs found in json-library.json.';
      tr.appendChild(td);
      fileTableBody.appendChild(tr);
      hideFilePeek();
      return;
    }

    files.forEach((f, idx) => {
      const tr = document.createElement('tr');
      tr.classList.add('selectable');
      tr.setAttribute('role', 'row');
      tr.setAttribute('tabindex', '0');
      tr.dataset.index = idx;

      const tdName = document.createElement('td');
      tdName.textContent = f.filename;
      const tdSize = document.createElement('td');
      tdSize.textContent = f.size;
      const tdMod = document.createElement('td');
      tdMod.textContent = f.modified;

      tr.appendChild(tdName);
      tr.appendChild(tdSize);
      tr.appendChild(tdMod);

      // click / keyboard support for selection
      const selectRow = () => {
        // clear previous selection
        const prev = fileTableBody.querySelector('tr.selected');
        if (prev && prev !== tr) prev.classList.remove('selected');
        tr.classList.add('selected');
        showFilePeekEntry(f.entry, f.filename, f.modified);
      };

      tr.addEventListener('click', selectRow);
      tr.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          selectRow();
        }
      });

      fileTableBody.appendChild(tr);
    });
  }

  const loadLibraryLogs = async () => {
    if (!fileTableBody) return;

    if (!window.electronAPI || typeof window.electronAPI.getLibraryEntries !== 'function') {
      renderFileTable([]);
      return;
    }

    try {
      const result = await window.electronAPI.getLibraryEntries();
      const entries = Array.isArray(result?.entries) ? result.entries : [];
      const fileModifiedAt = result?.fileModifiedAt;

      const tableRows = entries.map((entry, idx) => {
        const text = JSON.stringify(entry);
        const bytes = new TextEncoder().encode(text).length;
        const timestamp = entry && typeof entry === 'object' ? entry.timestamp : null;

        return {
          filename: `log-${idx + 1}.json`,
          size: formatBytes(bytes),
          modified: formatIsoDate(timestamp || fileModifiedAt),
          entry
        };
      });

      renderFileTable(tableRows);
    } catch (error) {
      console.error('Failed to load library logs:', error);
      renderFileTable([]);
    }
  };

  loadLibraryLogs();
});
