const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  quit: () => ipcRenderer.send('app-quit'),
  openCalibrate: () => ipcRenderer.send('open-calibrate'),
  offloadDataFromPi: (options) => ipcRenderer.invoke('offload-data-from-pi', options)
});
