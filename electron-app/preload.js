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
    getMiniModeStatus: () => ipcRenderer.invoke('get-mini-mode-status'),
    setMiniHeight: (height) => ipcRenderer.invoke('set-mini-height', height),
    setOpacity: (opacity) => ipcRenderer.invoke('set-opacity', opacity),
    // Schnellzugriff-Popup
    showQuickAccessWindow: (items) => ipcRenderer.invoke('show-quick-access-window', items),
    updateQuickAccessWindow: (items) => ipcRenderer.invoke('update-quick-access-window', items),
    hideQuickAccessWindow: () => ipcRenderer.invoke('hide-quick-access-window'),
    onQuickAccessPlay: (callback) => ipcRenderer.on('quick-access-play', (event, index) => callback(index)),
    // Quick-access popup → main (from popup window)
    quickAccessPlay: (index) => ipcRenderer.send('quick-access-play', index),
    onUpdateItems: (callback) => ipcRenderer.on('update-items', (event, items) => callback(items))
});

// Backend API URL
contextBridge.exposeInMainWorld('API_URL', 'http://127.0.0.1:8765');
