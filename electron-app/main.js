const { app, BrowserWindow, ipcMain, dialog, screen } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let splashWindow;
let quickAccessWindow;
let pythonProcess;
let isMiniMode = false;
let miniModePosition = 'top'; // 'top' oder 'bottom'
let normalWindowBounds = null;
let miniModeKeepOnTopInterval = null;

const BACKEND_URL = 'http://127.0.0.1:8765';

// Checks whether the backend is reachable
function checkBackend() {
    return new Promise((resolve) => {
        const req = http.get(`${BACKEND_URL}/api/status`, (res) => {
            resolve(res.statusCode === 200);
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1000, () => {
            req.destroy();
            resolve(false);
        });
    });
}

// Wartet bis Backend erreichbar ist
async function waitForBackend(maxAttempts = 30, interval = 500) {
    for (let i = 0; i < maxAttempts; i++) {
        const isReady = await checkBackend();
        if (isReady) {
            console.log('Backend ist bereit!');
            return true;
        }
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('status-update', `Backend wird gestartet... (${i + 1}s)`);
        }
        await new Promise(resolve => setTimeout(resolve, interval));
    }
    return false;
}

// Splash-Fenster mit Ladeanimation
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 400,
        height: 200,
        frame: false,
        transparent: false,
        alwaysOnTop: true,
        resizable: false,
        backgroundColor: '#1a1a2e',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    
    // Inline HTML for splash screen
    const splashHtml = `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    padding: 20px;
                    font-family: 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    box-sizing: border-box;
                }
                h1 {
                    margin: 0 0 10px 0;
                    font-size: 28px;
                    font-weight: 300;
                }
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid rgba(255,255,255,0.2);
                    border-top-color: #4ecca3;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 20px 0;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                #status {
                    font-size: 14px;
                    color: rgba(255,255,255,0.7);
                }
            </style>
        </head>
        <body>
            <h1>SpeakAlike</h1>
            <div class="spinner"></div>
            <div id="status">Backend wird gestartet...</div>
            <script>
                window.electronAPI.onStatusUpdate((status) => {
                    document.getElementById('status').textContent = status;
                });
            </script>
        </body>
        </html>
    `;
    
    splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml)}`);
    splashWindow.center();
}

// Python Backend starten
function startBackend() {
    let exePath, cwd;
    
    if (app.isPackaged) {
        // Production mode: bundled backend from resources/backend/
        exePath = path.join(process.resourcesPath, 'backend', 'backend_api.exe');
        cwd = path.join(process.resourcesPath, 'backend');
        
        // Copy voice models to AppData (writable) if needed
        const appDataVoiceModels = path.join(app.getPath('userData'), 'voice_models');
        if (!fs.existsSync(appDataVoiceModels)) {
            fs.mkdirSync(appDataVoiceModels, { recursive: true });
            // Bundled Voice-Modelle bei Erststart kopieren
            const bundledModels = path.join(process.resourcesPath, 'voice_models');
            if (fs.existsSync(bundledModels)) {
                const files = fs.readdirSync(bundledModels);
                for (const file of files) {
                    fs.copyFileSync(
                        path.join(bundledModels, file),
                        path.join(appDataVoiceModels, file)
                    );
                }
                console.log('Voice-Modelle nach AppData kopiert:', appDataVoiceModels);
            }
        }
    } else {
        // Entwicklungsmodus: Conda-Umgebung
        exePath = path.join(__dirname, '..', '.conda-py311', 'python.exe');
        cwd = path.join(__dirname, '..');
    }
    
    console.log('Starte Python Backend...', { exePath, cwd, packaged: app.isPackaged });
    
    const args = app.isPackaged ? [] : [path.join(__dirname, '..', 'backend_api.py')];
    
    const env = { ...process.env, PYTHONUNBUFFERED: '1' };
    if (app.isPackaged) {
        env.SPEAKALIKE_VOICE_MODELS = path.join(app.getPath('userData'), 'voice_models');
    }
    
    pythonProcess = spawn(exePath, args, {
        cwd: cwd,
        env: env
    });
    
    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
    });
    
    pythonProcess.on('close', (code) => {
        console.log(`Backend beendet mit Code ${code}`);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        minWidth: 800,
        minHeight: 600,
        title: 'SpeakAlike',
        backgroundColor: '#f5f5f5',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        autoHideMenuBar: true,
        show: false
    });

    mainWindow.loadFile('index.html');
    
    // Open DevTools with F12
    mainWindow.webContents.on('before-input-event', (event, input) => {
        if (input.key === 'F12') {
            mainWindow.webContents.toggleDevTools();
        }
    });
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.maximize();
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        if (quickAccessWindow && !quickAccessWindow.isDestroyed()) {
            quickAccessWindow.close();
            quickAccessWindow = null;
        }
        mainWindow = null;
    });
}

app.whenReady().then(async () => {
    // Splash-Fenster zeigen
    createSplashWindow();
    
    // Backend starten
    startBackend();
    
    // Warten bis Backend erreichbar ist
    const backendReady = await waitForBackend(60, 1000);
    
    if (!backendReady) {
        if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('status-update', 'Backend konnte nicht gestartet werden!');
        }
        await new Promise(resolve => setTimeout(resolve, 3000));
        app.quit();
        return;
    }
    
    // Close splash and open main window
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
    }
    createWindow();
});

app.on('window-all-closed', () => {
    // Clean up interval
    if (miniModeKeepOnTopInterval) {
        clearInterval(miniModeKeepOnTopInterval);
        miniModeKeepOnTopInterval = null;
    }
    // Backend stoppen
    if (pythonProcess) {
        pythonProcess.kill();
    }
    app.quit();
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

// IPC handlers for file dialogs
ipcMain.handle('open-file-dialog', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile', 'multiSelections'],
        filters: [
            { name: 'Audio Files', extensions: ['wav', 'mp3', 'ogg', 'flac'] }
        ],
        ...options
    });
    return result;
});

ipcMain.handle('save-file-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, {
        filters: [
            { name: 'WAV Audio', extensions: ['wav'] }
        ],
        ...options
    });
    return result;
});

ipcMain.handle('read-file-as-buffer', async (event, filePath) => {
    const fs = require('fs');
    const path = require('path');
    
    try {
        const buffer = fs.readFileSync(filePath);
        const fileName = path.basename(filePath);
        const ext = path.extname(filePath).toLowerCase();
        
        // Determine MIME type
        const mimeTypes = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.m4a': 'audio/mp4'
        };
        const mimeType = mimeTypes[ext] || 'audio/wav';
        
        return {
            data: buffer.toString('base64'),
            fileName: fileName,
            mimeType: mimeType
        };
    } catch (error) {
        console.error('Error reading file:', error);
        throw error;
    }
});

// Mini-Modus Toggle
ipcMain.handle('toggle-mini-mode', async () => {
    const display = screen.getPrimaryDisplay();
    const workArea = display.workAreaSize;
    const workAreaPos = display.workArea;
    
    if (!isMiniMode) {
        // Save whether maximised and current window size
        const wasMaximized = mainWindow.isMaximized();
        
        if (wasMaximized) {
            mainWindow.unmaximize();
            await new Promise(r => setTimeout(r, 200));
        }
        
        normalWindowBounds = mainWindow.getBounds();
        
        // Wechsle zu Mini-Modus
        const miniWidth = 850;
        const miniHeight = 120;
        const x = workAreaPos.x + Math.round((workArea.width - miniWidth) / 2);
        const y = miniModePosition === 'top' 
            ? workAreaPos.y + 5 
            : workAreaPos.y + workArea.height - miniHeight - 5;
        
        console.log('Mini-Modus - Berechnet:', { x, y, width: miniWidth, height: miniHeight, workArea, workAreaPos });
        
        // Minimum Size zuerst reduzieren
        mainWindow.setMinimumSize(200, 80);
        
        // Fenster verkleinern
        mainWindow.setSize(miniWidth, miniHeight);
        await new Promise(r => setTimeout(r, 50));
        
        // Position setzen
        mainWindow.setPosition(x, y);
        
        // Always on top
        mainWindow.setAlwaysOnTop(true, 'screen-saver');
        mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
        
        // Sichtbar machen falls versteckt
        mainWindow.show();
        mainWindow.focus();
        
        // Periodisch alwaysOnTop neu setzen, damit es bei Vollbild-Spielen bleibt
        if (miniModeKeepOnTopInterval) clearInterval(miniModeKeepOnTopInterval);
        miniModeKeepOnTopInterval = setInterval(() => {
            if (mainWindow && !mainWindow.isDestroyed() && isMiniMode) {
                mainWindow.setAlwaysOnTop(true, 'screen-saver');
            }
        }, 1000);
        
        isMiniMode = true;
        console.log('Mini-Modus aktiviert - Finale Bounds:', mainWindow.getBounds());
    } else {
        // Return to normal mode
        if (miniModeKeepOnTopInterval) {
            clearInterval(miniModeKeepOnTopInterval);
            miniModeKeepOnTopInterval = null;
        }
        mainWindow.setAlwaysOnTop(false);
        mainWindow.setVisibleOnAllWorkspaces(false);
        mainWindow.setMinimumSize(800, 600);
        
        if (normalWindowBounds) {
            mainWindow.setSize(normalWindowBounds.width, normalWindowBounds.height);
            mainWindow.setPosition(normalWindowBounds.x, normalWindowBounds.y);
        }
        
        await new Promise(r => setTimeout(r, 100));
        mainWindow.maximize();
        isMiniMode = false;
        
        // Close quick access window
        if (quickAccessWindow && !quickAccessWindow.isDestroyed()) {
            quickAccessWindow.close();
            quickAccessWindow = null;
        }
    }
    
    return isMiniMode;
});

// Change mini mode position (top/bottom)
ipcMain.handle('toggle-mini-position', async () => {
    if (!isMiniMode) return miniModePosition;
    
    const display = screen.getPrimaryDisplay();
    const workArea = display.workAreaSize;
    const workAreaPos = display.workArea;
    
    // Enforce fixed mini size so the window does not grow
    const miniWidth = 850;
    const miniHeight = 120;
    mainWindow.setSize(miniWidth, miniHeight);
    
    miniModePosition = miniModePosition === 'top' ? 'bottom' : 'top';
    const x = workAreaPos.x + Math.round((workArea.width - miniWidth) / 2);
    const y = miniModePosition === 'top' 
        ? workAreaPos.y + 5 
        : workAreaPos.y + workArea.height - miniHeight - 5;
    
    mainWindow.setPosition(x, y);

    // Schnellzugriff-Fenster repositionieren falls offen
    if (quickAccessWindow && !quickAccessWindow.isDestroyed() && quickAccessWindow.isVisible()) {
        const mainBounds = { x, y, width: miniWidth, height: miniHeight };
        const popupHeight = quickAccessWindow.getBounds().height;
        const popY = miniModePosition === 'top'
            ? y + miniHeight + 2
            : y - popupHeight - 2;
        quickAccessWindow.setPosition(x, popY);
    }
    
    return miniModePosition;
});

// Mini-Modus Status abfragen
ipcMain.handle('get-mini-mode-status', async () => {
    return { isMiniMode, position: miniModePosition };
});

// Temporarily change mini mode window height (for popup dialogs)
const MINI_HEIGHT = 120;
ipcMain.handle('set-mini-height', async (event, height) => {
    if (!isMiniMode || !mainWindow) return;
    const display = screen.getPrimaryDisplay();
    const workArea = display.workAreaSize;
    const workAreaPos = display.workArea;
    const miniWidth = 850;
    const x = workAreaPos.x + Math.round((workArea.width - miniWidth) / 2);
    if (miniModePosition === 'bottom') {
        // Bei bottom: y anpassen damit untere Kante fest bleibt
        const yBottom = workAreaPos.y + workArea.height - MINI_HEIGHT - 5;
        const yNew = yBottom - (height - MINI_HEIGHT);
        mainWindow.setPosition(x, yNew);
    }
    mainWindow.setSize(miniWidth, height);
});

ipcMain.handle('set-opacity', async (event, opacity) => {
    if (mainWindow) {
        mainWindow.setOpacity(Math.max(0.1, Math.min(1, opacity)));
    }
});

// Schnellzugriff-Popup im Mini-Modus
ipcMain.handle('show-quick-access-window', async (event, items) => {
    if (!isMiniMode || !mainWindow) return;
    
    const mainBounds = mainWindow.getBounds();
    const popupWidth = mainBounds.width;
    const itemHeight = 32;
    const popupHeight = Math.min(items.length * itemHeight + 8, 300);
    
    const x = mainBounds.x;
    const y = miniModePosition === 'top' 
        ? mainBounds.y + mainBounds.height + 2
        : mainBounds.y - popupHeight - 2;
    
    if (quickAccessWindow && !quickAccessWindow.isDestroyed()) {
        quickAccessWindow.webContents.send('update-items', items);
        quickAccessWindow.setBounds({ x, y, width: popupWidth, height: popupHeight });
        quickAccessWindow.show();
        quickAccessWindow.moveTop();
        return;
    }
    
    quickAccessWindow = new BrowserWindow({
        parent: mainWindow,
        x, y,
        width: popupWidth,
        height: popupHeight,
        frame: false,
        transparent: false,
        resizable: false,
        skipTaskbar: true,
        focusable: false,
        backgroundColor: '#2b2d31',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    
    // Gleicher Level wie mainWindow damit es davor erscheint
    quickAccessWindow.setAlwaysOnTop(true, 'screen-saver');
    quickAccessWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    quickAccessWindow.loadFile(path.join(__dirname, 'quick-access.html'));
    
    quickAccessWindow.webContents.once('did-finish-load', () => {
        quickAccessWindow.webContents.send('update-items', items);
        // Nochmal explizit nach vorne bringen nach dem Laden
        quickAccessWindow.moveTop();
    });
    
    quickAccessWindow.on('closed', () => {
        quickAccessWindow = null;
    });
});

ipcMain.handle('update-quick-access-window', async (event, items) => {
    if (quickAccessWindow && !quickAccessWindow.isDestroyed() && quickAccessWindow.isVisible()) {
        const mainBounds = mainWindow.getBounds();
        const popupWidth = mainBounds.width;
        const itemHeight = 32;
        const popupHeight = Math.min(items.length * itemHeight + 8, 300);
        const x = mainBounds.x;
        const y = miniModePosition === 'top'
            ? mainBounds.y + mainBounds.height + 2
            : mainBounds.y - popupHeight - 2;
        quickAccessWindow.webContents.send('update-items', items);
        quickAccessWindow.setBounds({ x, y, width: popupWidth, height: popupHeight });
    }
});

ipcMain.handle('hide-quick-access-window', async () => {
    if (quickAccessWindow && !quickAccessWindow.isDestroyed()) {
        quickAccessWindow.hide();
    }
});

ipcMain.on('quick-access-play', (event, index) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('quick-access-play', index);
    }
});

ipcMain.handle('show-set-picker', async (event, sets) => {
    const mainBounds = mainWindow.getBounds();
    const popupWidth = mainBounds.width;
    const itemHeight = 32;
    const popupHeight = Math.min(sets.length * itemHeight + 8, 300);
    const x = mainBounds.x;
    const y = miniModePosition === 'top'
        ? mainBounds.y + mainBounds.height + 2
        : mainBounds.y - popupHeight - 2;

    if (quickAccessWindow && !quickAccessWindow.isDestroyed()) {
        quickAccessWindow.setBounds({ x, y, width: popupWidth, height: popupHeight });
        quickAccessWindow.webContents.send('update-sets', sets);
        quickAccessWindow.show();
        quickAccessWindow.moveTop();
        return;
    }

    quickAccessWindow = new BrowserWindow({
        parent: mainWindow,
        x, y,
        width: popupWidth,
        height: popupHeight,
        frame: false,
        transparent: false,
        resizable: false,
        skipTaskbar: true,
        focusable: false,
        backgroundColor: '#2b2d31',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });
    quickAccessWindow.setAlwaysOnTop(true, 'screen-saver');
    quickAccessWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    quickAccessWindow.loadFile(path.join(__dirname, 'quick-access.html'));
    quickAccessWindow.webContents.once('did-finish-load', () => {
        quickAccessWindow.webContents.send('update-sets', sets);
        quickAccessWindow.moveTop();
    });
    quickAccessWindow.on('closed', () => {
        quickAccessWindow = null;
    });
});

ipcMain.on('set-picker-selected', (event, name) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('set-picker-selected', name);
    }
});

