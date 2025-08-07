const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const { autoUpdater } = require('electron-updater');
const axios = require('axios');

let mainWindow;
let isDev = process.env.NODE_ENV === 'development';

// Update checker configuration
autoUpdater.checkForUpdatesAndNotify();

// Jellyfin API client
class JellyfinAPI {
  constructor() {
    this.serverUrl = '';
    this.apiKey = '';
    this.userId = '';
    this.accessToken = '';
  }

  setServer(url) {
    this.serverUrl = url.replace(/\/$/, '');
  }

  async authenticate(username, password) {
    try {
      const response = await axios.post(`${this.serverUrl}/Users/authenticatebyname`, {
        Username: username,
        Pw: password
      }, {
        headers: {
          'X-Emby-Authorization': `MediaBrowser Client="Media Player", Device="Electron", DeviceId="media-player-${Date.now()}", Version="1.0.0"`
        }
      });

      this.accessToken = response.data.AccessToken;
      this.userId = response.data.User.Id;
      return { success: true, user: response.data.User };
    } catch (error) {
      console.error('Jellyfin authentication failed:', error);
      return { success: false, error: error.message };
    }
  }

  async getLibraries() {
    try {
      const response = await axios.get(`${this.serverUrl}/UserViews`, {
        headers: {
          'X-Emby-Authorization': `MediaBrowser Token="${this.accessToken}"`
        },
        params: { UserId: this.userId }
      });
      return response.data.Items || [];
    } catch (error) {
      console.error('Failed to get libraries:', error);
      return [];
    }
  }

  async getItems(parentId, mediaType = 'Audio') {
    try {
      const response = await axios.get(`${this.serverUrl}/Users/${this.userId}/Items`, {
        headers: {
          'X-Emby-Authorization': `MediaBrowser Token="${this.accessToken}"`
        },
        params: {
          ParentId: parentId,
          IncludeItemTypes: mediaType,
          Recursive: true,
          Fields: 'BasicSyncInfo,MediaSourceCount,Path,MediaSources',
          SortBy: 'SortName'
        }
      });
      return response.data.Items || [];
    } catch (error) {
      console.error('Failed to get items:', error);
      return [];
    }
  }

  getStreamUrl(itemId) {
    return `${this.serverUrl}/Audio/${itemId}/stream?api_key=${this.accessToken}`;
  }
}

const jellyfinAPI = new JellyfinAPI();

// Update functions
async function checkForUpdates() {
  try {
    const updateInfo = await autoUpdater.checkForUpdates();
    if (updateInfo && updateInfo.updateInfo) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Update Available',
        message: `Version ${updateInfo.updateInfo.version} is available!`,
        detail: 'The update will be downloaded in the background.',
        buttons: ['OK']
      });
    } else {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'No Updates',
        message: 'You are running the latest version.',
        buttons: ['OK']
      });
    }
  } catch (error) {
    dialog.showMessageBox(mainWindow, {
      type: 'error',
      title: 'Update Check Failed',
      message: 'Could not check for updates.',
      detail: error.message,
      buttons: ['OK']
    });
  }
}

function showDocumentation() {
  const docContent = `
# Media Player Documentation

## Features
- **Local Music Playback**: Support for MP3, FLAC, WAV, OGG, and M4A files
- **Jellyfin Integration**: Stream music and videos from your Jellyfin server
- **URL Streaming**: Play internet radio stations and streaming URLs
- **Audio Device Management**: Select and configure audio output devices
- **Automatic Updates**: Keep your media player up to date
- **Queue Management**: Organize and control your playlist
- **Themes**: Switch between dark and light themes

## Keyboard Shortcuts
- **Space**: Play/Pause
- **Ctrl+Left/Cmd+Left**: Previous track
- **Ctrl+Right/Cmd+Right**: Next track
- **Ctrl+O/Cmd+O**: Open music folder
- **Ctrl+J/Cmd+J**: Jellyfin connection
- **Ctrl+U/Cmd+U**: URL streaming
- **Ctrl+,/Cmd+,**: Audio settings
- **Ctrl+T/Cmd+T**: Toggle theme
- **F1**: Documentation

## Audio Settings
1. Go to File Menu > Audio Settings (Ctrl+,)
2. Select your preferred audio output device
3. Set default volume level
4. Settings are automatically saved

## URL Streaming Setup
1. Go to File Menu > URL Streaming (Ctrl+U)
2. Enter streaming URL (radio stations, podcasts, etc.)
3. Add optional title for easy identification
4. Choose "Add to List" or "Play Now"

## Jellyfin Setup
1. Go to File Menu > Jellyfin Connection (Ctrl+J)
2. Enter your Jellyfin server URL
3. Provide your username and password
4. Browse and stream your media library

## File Menu Options
- **Open Music Folder**: Browse local music files
- **Jellyfin Connection**: Connect to Jellyfin server  
- **URL Streaming**: Add internet streams and radio stations
- **Audio Settings**: Configure output devices and volume
- **Check for Updates**: Update the application
- **Documentation**: View this help content
- **Exit**: Close the application

## Supported Formats
**Local Audio**: MP3, FLAC, WAV, OGG, M4A
**Streaming**: M3U8, MP3 streams, AAC, OGG, Icecast/Shoutcast
**Video** (via Jellyfin): MP4, MKV, AVI, MOV, WMV

## Network Streaming
- HTTP Live Streaming (.m3u8)
- Direct audio streams (.mp3, .aac, .ogg)
- Icecast and Shoutcast radio stations
- WebM audio streams
- Custom streaming URLs with authentication

## Troubleshooting
- **Audio Issues**: Check Audio Settings for correct output device
- **Streaming Problems**: Verify internet connection and URL validity
- **Jellyfin Connection**: Ensure server is accessible and credentials are correct
- **File Permissions**: Check local file and folder access permissions
- **Network Streams**: Some streams may require specific user agents or headers
`;

  const docWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  docWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Media Player Documentation</title>
      <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; margin: 0; background: #f5f5f5; }
        .container { max-width: 700px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
        h2 { color: #007acc; margin-top: 25px; }
        pre { background: #f8f8f8; padding: 15px; border-radius: 5px; border-left: 4px solid #007acc; }
        code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
        ul { padding-left: 20px; }
        li { margin: 5px 0; }
      </style>
    </head>
    <body>
      <div class="container">
        ${docContent.replace(/\n/g, '<br>').replace(/## (.*)/g, '<h2>$1</h2>').replace(/# (.*)/g, '<h1>$1</h1>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/- \*\*(.*?)\*\*: (.*)/g, '<li><strong>$1</strong>: $2</li>')}
      </div>
    </body>
    </html>
  `));

  docWindow.setMenuBarVisibility(false);
}

async function showJellyfinConnection() {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'question',
    title: 'Jellyfin Connection',
    message: 'Connect to Jellyfin Server',
    detail: 'Would you like to set up Jellyfin connection?',
    buttons: ['Configure', 'Cancel'],
    defaultId: 0
  });

  if (result.response === 0) {
    mainWindow.webContents.send('show-jellyfin-setup');
  }
}

async function showAudioSettings() {
  mainWindow.webContents.send('show-audio-settings');
}

async function showUrlStreaming() {
  mainWindow.webContents.send('show-url-streaming');
}

// Audio device management
async function getAudioDevices() {
  try {
    // In a real implementation, you would use system APIs to get audio devices
    // For now, we'll simulate with some common device types
    return [
      { deviceId: 'default', label: 'System Default' },
      { deviceId: 'speakers', label: 'Speakers' },
      { deviceId: 'headphones', label: 'Headphones' },
      { deviceId: 'bluetooth', label: 'Bluetooth Audio' }
    ];
  } catch (error) {
    console.error('Failed to get audio devices:', error);
    return [{ deviceId: 'default', label: 'System Default' }];
  }
}

function saveAudioSettings(settings) {
  try {
    const settingsPath = path.join(require('os').homedir(), '.media-player-settings.json');
    let existingSettings = {};
    
    try {
      const data = require('fs').readFileSync(settingsPath, 'utf8');
      existingSettings = JSON.parse(data);
    } catch (e) {
      // File doesn't exist or is invalid, use empty object
    }
    
    const updatedSettings = { ...existingSettings, audio: settings };
    require('fs').writeFileSync(settingsPath, JSON.stringify(updatedSettings, null, 2));
    
    return { success: true };
  } catch (error) {
    console.error('Failed to save audio settings:', error);
    return { success: false, error: error.message };
  }
}

function loadAudioSettings() {
  try {
    const settingsPath = path.join(require('os').homedir(), '.media-player-settings.json');
    const data = require('fs').readFileSync(settingsPath, 'utf8');
    const settings = JSON.parse(data);
    return settings.audio || { defaultDevice: 'default', volume: 0.7 };
  } catch (error) {
    return { defaultDevice: 'default', volume: 0.7 };
  }
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'default',
    show: false,
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, './build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Music Folder',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            selectMusicFolder();
          }
        },
        { type: 'separator' },
        {
          label: 'Jellyfin Connection',
          accelerator: 'CmdOrCtrl+J',
          click: () => {
            showJellyfinConnection();
          }
        },
        {
          label: 'URL Streaming',
          accelerator: 'CmdOrCtrl+U',
          click: () => {
            showUrlStreaming();
          }
        },
        { type: 'separator' },
        {
          label: 'Audio Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            showAudioSettings();
          }
        },
        { type: 'separator' },
        {
          label: 'Check for Updates',
          click: () => {
            checkForUpdates();
          }
        },
        {
          label: 'Documentation',
          accelerator: 'F1',
          click: () => {
            showDocumentation();
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Playback',
      submenu: [
        {
          label: 'Play/Pause',
          accelerator: 'Space',
          click: () => {
            mainWindow.webContents.send('playback-toggle');
          }
        },
        {
          label: 'Previous',
          accelerator: 'CmdOrCtrl+Left',
          click: () => {
            mainWindow.webContents.send('playback-previous');
          }
        },
        {
          label: 'Next',
          accelerator: 'CmdOrCtrl+Right',
          click: () => {
            mainWindow.webContents.send('playback-next');
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Theme',
          accelerator: 'CmdOrCtrl+T',
          click: () => {
            mainWindow.webContents.send('toggle-theme');
          }
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

async function selectMusicFolder() {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Select Music Folder',
    defaultPath: path.join(require('os').homedir(), 'Music')
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const folderPath = result.filePaths[0];
    const musicFiles = await scanMusicFiles(folderPath);
    mainWindow.webContents.send('music-files-loaded', musicFiles);
  }
}

async function scanMusicFiles(dirPath) {
  const supportedExtensions = ['.mp3', '.flac', '.wav', '.ogg', '.m4a'];
  const musicFiles = [];
  
  // Dynamic import of music-metadata
  const { parseFile } = await import('music-metadata');

  async function scanDirectory(currentPath) {
    try {
      const entries = await fs.readdir(currentPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(currentPath, entry.name);
        
        if (entry.isDirectory()) {
          await scanDirectory(fullPath);
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase();
          if (supportedExtensions.includes(ext)) {
            try {
              const metadata = await parseFile(fullPath);
              musicFiles.push({
                path: fullPath,
                name: entry.name,
                title: metadata.common.title || path.basename(entry.name, ext),
                artist: metadata.common.artist || 'Unknown Artist',
                album: metadata.common.album || 'Unknown Album',
                duration: metadata.format.duration || 0,
                track: metadata.common.track?.no || 0,
                year: metadata.common.year || null,
                genre: metadata.common.genre?.[0] || null,
                coverArt: metadata.common.picture?.[0] || null
              });
            } catch (error) {
              console.warn(`Could not parse metadata for ${fullPath}:`, error.message);
              musicFiles.push({
                path: fullPath,
                name: entry.name,
                title: path.basename(entry.name, ext),
                artist: 'Unknown Artist',
                album: 'Unknown Album',
                duration: 0,
                track: 0,
                year: null,
                genre: null,
                coverArt: null
              });
            }
          }
        }
      }
    } catch (error) {
      console.error(`Error scanning directory ${currentPath}:`, error);
    }
  }

  await scanDirectory(dirPath);
  return musicFiles.sort((a, b) => {
    if (a.album !== b.album) return a.album.localeCompare(b.album);
    return a.track - b.track;
  });
}

// IPC Handlers
ipcMain.handle('select-music-folder', selectMusicFolder);
ipcMain.handle('get-file-buffer', async (event, filePath) => {
  try {
    const buffer = await fs.readFile(filePath);
    return buffer;
  } catch (error) {
    console.error('Error reading file:', error);
    return null;
  }
});

// Jellyfin IPC Handlers
ipcMain.handle('jellyfin-connect', async (event, { serverUrl, username, password }) => {
  jellyfinAPI.setServer(serverUrl);
  const result = await jellyfinAPI.authenticate(username, password);
  return result;
});

ipcMain.handle('jellyfin-get-libraries', async () => {
  return await jellyfinAPI.getLibraries();
});

ipcMain.handle('jellyfin-get-items', async (event, { parentId, mediaType }) => {
  return await jellyfinAPI.getItems(parentId, mediaType);
});

ipcMain.handle('jellyfin-get-stream-url', (event, itemId) => {
  return jellyfinAPI.getStreamUrl(itemId);
});

// Update IPC Handlers
ipcMain.handle('check-for-updates', () => {
  return checkForUpdates();
});

ipcMain.handle('show-documentation', () => {
  showDocumentation();
});

// Audio device IPC handlers
ipcMain.handle('get-audio-devices', () => {
  return getAudioDevices();
});

ipcMain.handle('save-audio-settings', (event, settings) => {
  return saveAudioSettings(settings);
});

ipcMain.handle('load-audio-settings', () => {
  return loadAudioSettings();
});

app.whenReady().then(() => {
  createMainWindow();
  createMenu();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});