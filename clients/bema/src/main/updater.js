// src/main/updater.js
const { app, dialog, shell } = require('electron');
const { autoUpdater } = require('electron-updater');
const fetch = require('node-fetch');
const semver = require('semver');

class BemaUpdateManager {
  constructor() {
    this.currentVersion = app.getVersion();
    this.hubNodeUrl = 'http://localhost:3002';
    this.hubNodeUrlPublic = 'https://files.devinecreations.net:3924/patchmate/';
    this.updateCheckUrl = `${this.hubNodeUrl}/api/software-updates`;
    this.updateCheckUrlPublic = `${this.hubNodeUrlPublic}api/software-updates`;
    this.lastCheckTime = null;
    this.updateCheckInterval = 24 * 60 * 60 * 1000; // 24 hours
    this.clientId = 'bema-client';
    
    // Configure auto-updater
    this.configureAutoUpdater();
    
    // Set up periodic checks
    this.setupPeriodicChecks();
  }
  
  configureAutoUpdater() {
    // Set update feed URL
    autoUpdater.setFeedURL({
      provider: 'github',
      owner: 'devinecreations',
      repo: 'bema',
      private: false
    });
    
    // Handle update events
    autoUpdater.on('checking-for-update', () => {
      this.announceToAccessibilitySystem('Checking for updates...');
      console.log('Checking for update...');
    });
    
    autoUpdater.on('update-available', (info) => {
      this.announceToAccessibilitySystem(`Update available: version ${info.version}`);
      this.showUpdateAvailableDialog(info);
    });
    
    autoUpdater.on('update-not-available', (info) => {
      this.announceToAccessibilitySystem('No updates available');
      console.log('Update not available.');
    });
    
    autoUpdater.on('error', (err) => {
      this.announceToAccessibilitySystem('Update check failed');
      console.error('Update error:', err);
      this.showUpdateErrorDialog(err);
    });
    
    autoUpdater.on('download-progress', (progressObj) => {
      const percent = Math.round(progressObj.percent);
      this.updateDownloadProgress(percent);
    });
    
    autoUpdater.on('update-downloaded', (info) => {
      this.announceToAccessibilitySystem('Update downloaded successfully');
      this.showUpdateReadyDialog(info);
    });
  }
  
  async checkForUpdates(userInitiated = false) {
    try {
      // Check if enough time has passed since last check
      if (!userInitiated && !this.shouldCheckForUpdates()) {
        return { updateAvailable: false, reason: 'Too soon since last check' };
      }
      
      this.lastCheckTime = Date.now();
      
      // Custom update check against our server
      const updateInfo = await this.checkCustomUpdateServer();
      
      if (updateInfo.updateAvailable) {
        // Use electron-updater for actual download/install
        autoUpdater.checkForUpdatesAndNotify();
      }
      
      return updateInfo;
      
    } catch (error) {
      console.error('Update check failed:', error);
      
      if (userInitiated) {
        this.showUpdateErrorDialog(error);
      }
      
      return { updateAvailable: false, error: error.message };
    }
  }
  
  async checkCustomUpdateServer() {
    const response = await fetch(this.updateCheckUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        currentVersion: this.currentVersion,
        platform: process.platform,
        arch: process.arch,
        userId: this.getUserId() // For license validation
      })
    });
    
    if (!response.ok) {
      throw new Error(`Update server responded with ${response.status}`);
    }
    
    const data = await response.json();
    
    return {
      updateAvailable: data.updateAvailable,
      latestVersion: data.latestVersion,
      downloadUrl: data.downloadUrl,
      releaseNotes: data.releaseNotes,
      accessibilityFeatures: data.accessibilityFeatures,
      isSecurityUpdate: data.isSecurityUpdate,
      downloadSize: data.downloadSize
    };
  }
  
  shouldCheckForUpdates() {
    if (!this.lastCheckTime) return true;
    return (Date.now() - this.lastCheckTime) > this.updateCheckInterval;
  }
  
  showUpdateAvailableDialog(updateInfo) {
    const options = {
      type: 'info',
      title: 'Update Available',
      message: `Softnode Media Player ${updateInfo.version} is available`,
      detail: this.formatUpdateDetails(updateInfo),
      buttons: ['Download Now', 'Download Later', 'Skip This Version'],
      defaultId: 0,
      cancelId: 1
    };
    
    dialog.showMessageBox(options).then(result => {
      switch (result.response) {
        case 0: // Download Now
          this.startUpdateDownload();
          break;
        case 1: // Download Later
          this.scheduleUpdateReminder();
          break;
        case 2: // Skip This Version
          this.skipVersion(updateInfo.version);
          break;
      }
    });
  }
  
  formatUpdateDetails(updateInfo) {
    let details = `Current version: ${this.currentVersion}
New version: ${updateInfo.version}
Download size: ${this.formatFileSize(updateInfo.downloadSize)}

What's new:
${updateInfo.releaseNotes}`;
    
    if (updateInfo.accessibilityFeatures) {
      details += `

Accessibility improvements:
${updateInfo.accessibilityFeatures}`;
    }
    
    if (updateInfo.isSecurityUpdate) {
      details += '\n\n⚠️ This update contains important security fixes.';
    }
    
    return details;
  }
  
  startUpdateDownload() {
    this.announceToAccessibilitySystem('Starting update download');
    autoUpdater.downloadUpdate();
  }
  
  updateDownloadProgress(percent) {
    // Update progress in UI and announce milestones to screen readers
    if (percent % 25 === 0) { // Announce at 25%, 50%, 75%, 100%
      this.announceToAccessibilitySystem(`Update download ${percent}% complete`);
    }
    
    // Send progress to renderer process
    if (this.mainWindow) {
      this.mainWindow.webContents.send('update-download-progress', percent);
    }
  }
  
  showUpdateReadyDialog(updateInfo) {
    const options = {
      type: 'info',
      title: 'Update Ready',
      message: 'Update has been downloaded and is ready to install',
      detail: 'The application will restart to complete the installation. Any unsaved work will be preserved.',
      buttons: ['Restart Now', 'Restart Later'],
      defaultId: 0
    };
    
    dialog.showMessageBox(options).then(result => {
      if (result.response === 0) {
        this.announceToAccessibilitySystem('Restarting application to install update');
        autoUpdater.quitAndInstall();
      } else {
        this.scheduleUpdateInstallation();
      }
    });
  }
  
  showUpdateErrorDialog(error) {
    const options = {
      type: 'error',
      title: 'Update Error',
      message: 'Failed to check for updates',
      detail: `Error: ${error.message}\n\nYou can check for updates manually at https://devinecreations.net/softhub/bema/`,
      buttons: ['OK', 'Visit Download Page']
    };
    
    dialog.showMessageBox(options).then(result => {
      if (result.response === 1) {
        shell.openExternal('https://devinecreations.net/softhub/bema/');
      }
    });
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
  
  announceToAccessibilitySystem(message) {
    // Send announcement to renderer process for screen reader output
    if (this.mainWindow) {
      this.mainWindow.webContents.send('accessibility-announcement', {
        message,
        priority: 'polite'
      });
    }
  }
  
  getUserId() {
    // Return user ID for license validation
    // This would be stored securely after license activation
    const Store = require('electron-store');
    const store = new Store({ name: 'bema-config' });
    return store.get('userId', null);
  }
  
  formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
  }
  
  scheduleUpdateReminder() {
    // Remind user about update in 24 hours
    setTimeout(() => {
      this.checkForUpdates(true);
    }, 24 * 60 * 60 * 1000);
  }
  
  skipVersion(version) {
    const Store = require('electron-store');
    const store = new Store({ name: 'bema-config' });
    store.set('skippedVersions', [...(store.get('skippedVersions', [])), version]);
  }
}

  async registerWithHubNode() {
    try {
      const response = await fetch(`${this.hubNodeUrl}/api/clients/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clientId: this.clientId,
          application: 'bema',
          version: this.currentVersion,
          platform: process.platform,
          arch: process.arch,
          capabilities: ['software-updates', 'push-notifications'],
          lastSeen: new Date().toISOString()
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Registered with HubNode:', data);
        return data;
      }
    } catch (error) {
      console.warn('Failed to register with HubNode:', error.message);
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
      console.warn('Failed to notify HubNode of status:', error.message);
    }
  }
}

module.exports = BemaUpdateManager;