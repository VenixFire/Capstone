const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs/promises');

const DEFAULT_PI_ENDPOINT = 'http://192.168.1.50:5000/offload';
const DEFAULT_LIBRARY_FILE = 'json-library.json';
const DEFAULT_WORKSPACE_LIBRARY_PATH = path.join(__dirname, DEFAULT_LIBRARY_FILE);
const DEFAULT_OLLAMA_ENDPOINT = 'http://127.0.0.1:11434/api/chat';
const DEFAULT_OLLAMA_MODEL = 'qwen2.5:3b';

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
  const localLibraryPath = options.localLibraryPath || DEFAULT_WORKSPACE_LIBRARY_PATH;
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

async function getLibraryEntriesForUi(options = {}) {
  const localLibraryPath = options.localLibraryPath || DEFAULT_WORKSPACE_LIBRARY_PATH;
  const entries = await readLibraryEntries(localLibraryPath);

  let fileModifiedAt = null;
  try {
    const stats = await fs.stat(localLibraryPath);
    fileModifiedAt = stats.mtime.toISOString();
  } catch {
    fileModifiedAt = null;
  }

  return {
    entries,
    localLibraryPath,
    fileModifiedAt
  };
}

function summarizeEntries(entries) {
  const fieldCounts = {};
  for (const entry of entries) {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) continue;
    for (const key of Object.keys(entry)) {
      fieldCounts[key] = (fieldCounts[key] || 0) + 1;
    }
  }

  const topFields = Object.entries(fieldCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .map(([name, count]) => ({ name, count }));

  return {
    totalEntries: entries.length,
    topFields,
    sampleEntries: entries.slice(0, 25)
  };
}

function normalizeConversationHistory(history) {
  if (!Array.isArray(history)) return [];

  return history
    .filter((msg) => {
      return (
        msg &&
        typeof msg === 'object' &&
        (msg.role === 'user' || msg.role === 'assistant') &&
        typeof msg.content === 'string' &&
        msg.content.trim().length > 0
      );
    })
    .slice(-20)
    .map((msg) => ({
      role: msg.role,
      content: msg.content.trim()
    }));
}

async function askOllamaAboutLibrary(question, options = {}) {
  const model = options.model || DEFAULT_OLLAMA_MODEL;
  const endpoint = options.ollamaEndpoint || DEFAULT_OLLAMA_ENDPOINT;
  const timeoutMs = Number.isFinite(options.timeoutMs) ? options.timeoutMs : 60000;
  const localLibraryPath = options.localLibraryPath || DEFAULT_WORKSPACE_LIBRARY_PATH;
  const history = normalizeConversationHistory(options.history);

  if (!question || typeof question !== 'string' || !question.trim()) {
    throw new Error('Please enter a question for the data analysis chat.');
  }

  const entries = await readLibraryEntries(localLibraryPath);
  const summary = summarizeEntries(entries);

  const systemPrompt = [
    'You are a local data analyst assistant for an Electron app.',
    'Analyze only the provided JSON library summary and sample entries.',
    'If the user asks for exact counts that cannot be inferred from the sample alone, state limits clearly.',
    'Use prior conversation turns for follow-up context when helpful.',
    'Be concise and practical.'
  ].join(' ');

  const dataContextPrompt = [
    `Library path: ${localLibraryPath}`,
    `Total entries in library: ${summary.totalEntries}`,
    `Top fields and frequency: ${JSON.stringify(summary.topFields)}`,
    `Sample entries (up to 25): ${JSON.stringify(summary.sampleEntries)}`
  ].join('\n\n');

  const messages = [
    { role: 'system', content: systemPrompt },
    { role: 'system', content: dataContextPrompt },
    ...history,
    { role: 'user', content: question.trim() }
  ];

  let response;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model,
        stream: false,
        messages
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
  } catch (error) {
    throw new Error(`Failed to reach local Ollama service: ${error.message}`);
  }

  if (!response.ok) {
    throw new Error(`Ollama responded with HTTP ${response.status}.`);
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error('Ollama returned invalid JSON.');
  }

  const aiMessage = payload?.message?.content;
  if (!aiMessage || typeof aiMessage !== 'string') {
    throw new Error('Ollama response did not include message content.');
  }

  return {
    answer: aiMessage,
    model,
    totalEntries: summary.totalEntries,
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

ipcMain.on('open-analyze', () => {
  const analyzeWin = new BrowserWindow({
    width: 900,
    height: 700,
    resizable: true,
    maximizable: true,
    fullscreenable: false,
    frame: false,
    transparent: false,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  analyzeWin.loadFile('analyze.html');
});

ipcMain.handle('offload-data-from-pi', async (_event, options) => {
  return mergePiJsonIntoLocalLibrary(options);
});

ipcMain.handle('analyze-library-data', async (_event, question, options) => {
  return askOllamaAboutLibrary(question, options || {});
});

ipcMain.handle('get-library-entries', async (_event, options) => {
  return getLibraryEntriesForUi(options || {});
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});