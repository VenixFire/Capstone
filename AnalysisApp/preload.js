const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  quit: () => ipcRenderer.send('app-quit'),
  openCalibrate: () => ipcRenderer.send('open-calibrate'),
  openAnalyze: () => ipcRenderer.send('open-analyze'),
  offloadDataFromPi: (options) => ipcRenderer.invoke('offload-data-from-pi', options),
  analyzeLibraryData: (question, options) => ipcRenderer.invoke('analyze-library-data', question, options),
  getLibraryEntries: (options) => ipcRenderer.invoke('get-library-entries', options)
});
