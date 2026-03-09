const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs/promises');

const DEFAULT_PI_ENDPOINT = 'http://192.168.1.50:5000/offload';
const DEFAULT_LIBRARY_FILE = 'json-library.json';

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

function normalizeToEntries(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === 'object') return [payload];
  throw new Error('Raspberry Pi response must be a JSON object or array.');
}

async function readLibraryEntries(filePath) {
  const exists = await fileExists(filePath);
  if (!exists) return [];

  const raw = await fs.readFile(filePath, 'utf8');
  if (!raw.trim()) return [];

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error('Local library file contains invalid JSON.');
  }

  if (Array.isArray(parsed)) return parsed;
  if (parsed && Array.isArray(parsed.entries)) return parsed.entries;

  throw new Error('Local library JSON must be an array or an object containing an entries array.');
}

async function mergePiJsonIntoLocalLibrary(options = {}) {
  const endpoint = options.endpoint || DEFAULT_PI_ENDPOINT;
  const localLibraryPath = options.localLibraryPath || path.join(app.getPath('userData'), DEFAULT_LIBRARY_FILE);
  const timeoutMs = Number.isFinite(options.timeoutMs) ? options.timeoutMs : 10000;

  let response;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        Accept: 'application/json'
      },
      signal: controller.signal
    });

    clearTimeout(timeoutId);
  } catch (error) {
    throw new Error(`Failed to connect to Raspberry Pi endpoint: ${error.message}`);
  }

  if (!response.ok) {
    throw new Error(`Raspberry Pi endpoint responded with HTTP ${response.status}.`);
  }

  let incomingPayload;
  try {
    incomingPayload = await response.json();
  } catch {
    throw new Error('Raspberry Pi endpoint returned non-JSON content.');
  }

  const incomingEntries = normalizeToEntries(incomingPayload);
  const existingEntries = await readLibraryEntries(localLibraryPath);
  const mergedEntries = [...existingEntries, ...incomingEntries];

  const libraryDocument = {
    entries: mergedEntries,
    updatedAt: new Date().toISOString()
  };

  await fs.mkdir(path.dirname(localLibraryPath), { recursive: true });
  await fs.writeFile(localLibraryPath, JSON.stringify(libraryDocument, null, 2), 'utf8');

  return {
    added: incomingEntries.length,
    total: mergedEntries.length,
    endpoint,
    localLibraryPath
  };
}

function createWindow() {
  const win = new BrowserWindow({
    // window size and other settings
    width: 800,
    height: 650,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    frame: false,
    transparent: false,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile('index.html');
}

app.whenReady().then(createWindow);

// IPC handler for renderer -> main quit request
ipcMain.on('app-quit', () => {
  app.quit();
});

// Create a new window for calibration on request from renderer
ipcMain.on('open-calibrate', () => {
  const calWin = new BrowserWindow({
    width: 800,
    height: 650,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    frame: false,
    transparent: false,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // load a dedicated calibration page
  calWin.loadFile('calibrate.html');
});

ipcMain.handle('offload-data-from-pi', async (_event, options) => {
  return mergePiJsonIntoLocalLibrary(options);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});