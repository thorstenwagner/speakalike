const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

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
    
    // Nur kurz warten bis Server antwortet, TTS lädt im Hintergrund
    return new Promise(resolve => setTimeout(resolve, 2000));
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
    await startBackend();
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
