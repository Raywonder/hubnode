const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectMusicFolder: () => ipcRenderer.invoke('select-music-folder'),
  getFileBuffer: (filePath) => ipcRenderer.invoke('get-file-buffer', filePath),
  
  // Jellyfin API
  jellyfinConnect: (credentials) => ipcRenderer.invoke('jellyfin-connect', credentials),
  jellyfinGetLibraries: () => ipcRenderer.invoke('jellyfin-get-libraries'),
  jellyfinGetItems: (params) => ipcRenderer.invoke('jellyfin-get-items', params),
  jellyfinGetStreamUrl: (itemId) => ipcRenderer.invoke('jellyfin-get-stream-url', itemId),
  
  // Update API
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  showDocumentation: () => ipcRenderer.invoke('show-documentation'),
  
  // Audio Device API
  getAudioDevices: () => ipcRenderer.invoke('get-audio-devices'),
  saveAudioSettings: (settings) => ipcRenderer.invoke('save-audio-settings', settings),
  loadAudioSettings: () => ipcRenderer.invoke('load-audio-settings'),
  
  onMusicFilesLoaded: (callback) => {
    ipcRenderer.on('music-files-loaded', (event, files) => callback(files));
  },
  
  onPlaybackToggle: (callback) => {
    ipcRenderer.on('playback-toggle', callback);
  },
  
  onPlaybackPrevious: (callback) => {
    ipcRenderer.on('playback-previous', callback);
  },
  
  onPlaybackNext: (callback) => {
    ipcRenderer.on('playback-next', callback);
  },
  
  onToggleTheme: (callback) => {
    ipcRenderer.on('toggle-theme', callback);
  },
  
  onShowJellyfinSetup: (callback) => {
    ipcRenderer.on('show-jellyfin-setup', callback);
  },
  
  onShowAudioSettings: (callback) => {
    ipcRenderer.on('show-audio-settings', callback);
  },
  
  onShowUrlStreaming: (callback) => {
    ipcRenderer.on('show-url-streaming', callback);
  },
  
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});