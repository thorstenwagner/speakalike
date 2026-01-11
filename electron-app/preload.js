const { contextBridge, ipcRenderer } = require('electron');

// API für Renderer-Prozess
contextBridge.exposeInMainWorld('electronAPI', {
    openFileDialog: (options) => ipcRenderer.invoke('open-file-dialog', options),
    saveFileDialog: (options) => ipcRenderer.invoke('save-file-dialog', options),
    readFileAsBuffer: (filePath) => ipcRenderer.invoke('read-file-as-buffer', filePath),
    onStatusUpdate: (callback) => ipcRenderer.on('status-update', (event, status) => callback(status)),
    // Mini-Modus
    toggleMiniMode: () => ipcRenderer.invoke('toggle-mini-mode'),
    toggleMiniPosition: () => ipcRenderer.invoke('toggle-mini-position'),
    getMiniModeStatus: () => ipcRenderer.invoke('get-mini-mode-status')
});

// Backend API URL
contextBridge.exposeInMainWorld('API_URL', 'http://127.0.0.1:8765');
