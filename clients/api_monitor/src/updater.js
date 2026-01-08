const { app } = require('electron');
const fetch = require('node-fetch');
const { autoUpdater } = require('electron-updater');

class ApiMonitorUpdateManager {
  constructor() {
    this.currentVersion = app.getVersion();
    this.hubNodeUrl = 'http://localhost:3002';
    this.hubNodeUrlPublic = 'https://files.devinecreations.net:3924/patchmate/';
    this.updateCheckUrl = `${this.hubNodeUrl}/api/software-updates`;
    this.updateCheckUrlPublic = `${this.hubNodeUrlPublic}api/software-updates`;
    this.lastCheckTime = null;
    this.updateCheckInterval = 24 * 60 * 60 * 1000; // 24 hours
    this.clientId = 'api-monitor-client';
    this.mainWindow = null;
    
    this.configureAutoUpdater();
    this.setupPeriodicChecks();
  }
  
  configureAutoUpdater() {
    autoUpdater.setFeedURL({
      provider: 'generic',
      url: `${this.hubNodeUrl}/api/software-updates/feed/api_monitor`
    });
    
    autoUpdater.on('checking-for-update', () => {
      console.log('Checking for API Monitor updates...');
    });
    
    autoUpdater.on('update-available', (info) => {
      console.log('API Monitor update available:', info);
      if (this.mainWindow) {
        this.mainWindow.webContents.send('update-available', info);
      }
    });
    
    autoUpdater.on('update-not-available', (info) => {
      console.log('No API Monitor updates available');
    });
    
    autoUpdater.on('error', (err) => {
      console.error('API Monitor update error:', err);
    });
    
    autoUpdater.on('download-progress', (progressObj) => {
      const percent = Math.round(progressObj.percent);
      if (this.mainWindow) {
        this.mainWindow.webContents.send('download-progress', percent);
      }
    });
    
    autoUpdater.on('update-downloaded', (info) => {
      console.log('API Monitor update downloaded');
      if (this.mainWindow) {
        this.mainWindow.webContents.send('update-downloaded', info);
      }
    });
  }
  
  async checkForUpdates(userInitiated = false) {
    try {
      if (!userInitiated && !this.shouldCheckForUpdates()) {
        return { updateAvailable: false, reason: 'Too soon since last check' };
      }
      
      this.lastCheckTime = Date.now();
      
      // Register with HubNode first
      await this.registerWithHubNode();
      
      const response = await fetch(this.updateCheckUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientId: this.clientId,
          application: 'api_monitor',
          currentVersion: this.currentVersion,
          platform: process.platform,
          arch: process.arch
        })
      });
      
      if (!response.ok) {
        throw new Error(`HubNode API responded with ${response.status}`);
      }
      
      const updateInfo = await response.json();
      
      if (updateInfo.updateAvailable) {
        autoUpdater.checkForUpdatesAndNotify();
      }
      
      return updateInfo;
      
    } catch (error) {
      console.error('Update check failed:', error);
      return { updateAvailable: false, error: error.message };
    }
  }
  
  async registerWithHubNode() {
    try {
      const response = await fetch(`${this.hubNodeUrl}/api/clients/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientId: this.clientId,
          application: 'api_monitor',
          version: this.currentVersion,
          platform: process.platform,
          arch: process.arch,
          capabilities: ['software-updates', 'health-monitoring'],
          lastSeen: new Date().toISOString()
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('API Monitor registered with HubNode:', data);
        return data;
      }
    } catch (error) {
      console.warn('Failed to register API Monitor with HubNode:', error.message);
    }
  }
  
  async notifyHubNodeStatus(status) {
    try {
      await fetch(`${this.hubNodeUrl}/api/clients/${this.clientId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status,
          timestamp: new Date().toISOString(),
          version: this.currentVersion
        })
      });
    } catch (error) {
      console.warn('Failed to notify HubNode of API Monitor status:', error.message);
    }
  }
  
  shouldCheckForUpdates() {
    if (!this.lastCheckTime) return true;
    return (Date.now() - this.lastCheckTime) > this.updateCheckInterval;
  }
  
  setupPeriodicChecks() {
    // Check for updates on app startup (after 10 seconds)
    setTimeout(() => {
      this.checkForUpdates(false);
    }, 10000);
    
    // Set up periodic checks
    setInterval(() => {
      this.checkForUpdates(false);
    }, this.updateCheckInterval);
  }
}

module.exports = ApiMonitorUpdateManager;