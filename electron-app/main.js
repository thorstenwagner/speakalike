const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let splashWindow;
let pythonProcess;

const BACKEND_URL = 'http://127.0.0.1:8765';

// Prüft ob das Backend erreichbar ist
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
async function waitForBackend(maxAttempts = 60, interval = 1000) {
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
    
    // Inline HTML für Splash-Screen
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
    const pythonPath = path.join(__dirname, '..', '.conda-py311', 'python.exe');
    const scriptPath = path.join(__dirname, '..', 'backend_api.py');
    
    console.log('Starte Python Backend...');
    
    pythonProcess = spawn(pythonPath, [scriptPath], {
        cwd: path.join(__dirname, '..'),
        env: {
            ...process.env,
            PYTHONUNBUFFERED: '1'
        }
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
    
    // DevTools mit F12 öffnen
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
    
    // Splash schließen und Hauptfenster öffnen
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close();
    }
    createWindow();
});

app.on('window-all-closed', () => {
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

// IPC Handler für Datei-Dialoge
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

