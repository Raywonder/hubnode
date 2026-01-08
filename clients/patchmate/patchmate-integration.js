#!/usr/bin/env node

/**
 * PatchMate Integration with HubNode API System
 * Provides server sync and client update management for PatchMate
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const axios = require('axios').default;

class PatchMateHubIntegration {
  constructor(config = {}) {
    this.config = {
      port: config.port || 3002,
      hubNodeEndpoint: config.hubNodeEndpoint || 'http://localhost:3000',
      apiMonitorEndpoint: config.apiMonitorEndpoint || 'http://localhost:3001',
      patchMateDataPath: config.patchMateDataPath || path.join(__dirname, '../../patchmate-deployment'),
      ...config
    };
    
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.clients = new Map();
    this.patches = new Map();
    this.deviceConfigs = new Map();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        service: 'PatchMate Hub Integration'
      });
    });

    // Client registration and sync
    this.app.post('/api/clients/register', (req, res) => {
      const { clientId, deviceInfo, patchLibrary } = req.body;
      
      this.clients.set(clientId, {
        deviceInfo,
        patchLibrary,
        lastSync: new Date().toISOString(),
        connected: true
      });

      // Notify API monitor of new client
      this.notifyApiMonitor('client_registered', { clientId, deviceInfo });

      res.json({
        success: true,
        clientId,
        serverPatches: Array.from(this.patches.values()),
        deviceConfigs: Array.from(this.deviceConfigs.values())
      });
    });

    // Patch sync endpoints
    this.app.get('/api/patches', (req, res) => {
      res.json({
        patches: Array.from(this.patches.values()),
        totalCount: this.patches.size,
        lastUpdated: this.getLastPatchUpdate()
      });
    });

    this.app.post('/api/patches/upload', (req, res) => {
      const { patchData, metadata, clientId } = req.body;
      const patchId = this.generatePatchId(patchData);
      
      const patch = {
        id: patchId,
        data: patchData,
        metadata: {
          ...metadata,
          uploadedBy: clientId,
          uploadedAt: new Date().toISOString()
        }
      };

      this.patches.set(patchId, patch);
      
      // Sync to other clients
      this.broadcastPatchUpdate(patch);

      res.json({
        success: true,
        patchId,
        patch
      });
    });

    // Device configuration management
    this.app.get('/api/devices/:deviceId/config', (req, res) => {
      const { deviceId } = req.params;
      const config = this.deviceConfigs.get(deviceId);
      
      if (!config) {
        return res.status(404).json({ error: 'Device configuration not found' });
      }

      res.json(config);
    });

    this.app.put('/api/devices/:deviceId/config', (req, res) => {
      const { deviceId } = req.params;
      const { configuration } = req.body;
      
      const deviceConfig = {
        deviceId,
        configuration,
        lastUpdated: new Date().toISOString()
      };

      this.deviceConfigs.set(deviceId, deviceConfig);
      
      // Broadcast to connected clients using this device
      this.broadcastDeviceConfigUpdate(deviceId, deviceConfig);

      res.json({
        success: true,
        deviceConfig
      });
    });

    // Update management for PatchMate clients
    this.app.get('/api/updates/check/:platform/:arch', (req, res) => {
      const { platform, arch } = req.params;
      const currentVersion = req.query.version;
      
      const updateInfo = this.getUpdateInfo(platform, arch, currentVersion);
      
      res.json({
        hasUpdate: updateInfo.hasUpdate,
        latestVersion: updateInfo.version,
        downloadUrl: updateInfo.downloadUrl,
        releaseNotes: updateInfo.releaseNotes,
        mandatory: updateInfo.mandatory || false
      });
    });

    // Integration with HubNode main API
    this.app.post('/api/hubnode/sync', (req, res) => {
      this.syncWithHubNode()
        .then(result => res.json({ success: true, result }))
        .catch(error => res.status(500).json({ error: error.message }));
    });
  }

  generatePatchId(patchData) {
    return crypto.createHash('sha256')
      .update(JSON.stringify(patchData))
      .digest('hex')
      .substring(0, 16);
  }

  getLastPatchUpdate() {
    let lastUpdate = null;
    for (const patch of this.patches.values()) {
      const patchDate = new Date(patch.metadata.uploadedAt);
      if (!lastUpdate || patchDate > lastUpdate) {
        lastUpdate = patchDate;
      }
    }
    return lastUpdate ? lastUpdate.toISOString() : null;
  }

  broadcastPatchUpdate(patch) {
    // Broadcast patch update to all connected clients
    // In a real implementation, this would use WebSockets or Server-Sent Events
    console.log(`Broadcasting patch update: ${patch.id} to ${this.clients.size} clients`);
  }

  broadcastDeviceConfigUpdate(deviceId, config) {
    // Broadcast device config update to relevant clients
    console.log(`Broadcasting device config update for ${deviceId} to connected clients`);
  }

  getUpdateInfo(platform, arch, currentVersion) {
    // Load update configuration from PatchMate deployment
    const updateConfigPath = path.join(this.config.patchMateDataPath, 'api', 'update-server.js');
    
    // Default update info - in production this would check actual versions
    return {
      hasUpdate: false,
      version: '1.0.0',
      downloadUrl: null,
      releaseNotes: 'No updates available',
      mandatory: false
    };
  }

  async syncWithHubNode() {
    try {
      // Sync client data with main HubNode API
      const response = await axios.post(`${this.config.hubNodeEndpoint}/api/clients/patchmate/sync`, {
        clients: Array.from(this.clients.entries()),
        patches: Array.from(this.patches.entries()),
        deviceConfigs: Array.from(this.deviceConfigs.entries())
      });

      return response.data;
    } catch (error) {
      console.error('Failed to sync with HubNode:', error.message);
      throw error;
    }
  }

  async notifyApiMonitor(event, data) {
    try {
      await axios.post(`${this.config.apiMonitorEndpoint}/api/events`, {
        service: 'patchmate',
        event,
        data,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to notify API monitor:', error.message);
    }
  }

  start() {
    this.app.listen(this.config.port, () => {
      console.log(`🎵 PatchMate Hub Integration running on port ${this.config.port}`);
      console.log(`📡 HubNode endpoint: ${this.config.hubNodeEndpoint}`);
      console.log(`📊 API Monitor endpoint: ${this.config.apiMonitorEndpoint}`);
      
      // Register with API monitor
      this.notifyApiMonitor('service_started', {
        port: this.config.port,
        endpoints: [
          '/health',
          '/api/clients/register',
          '/api/patches',
          '/api/devices/:deviceId/config',
          '/api/updates/check/:platform/:arch'
        ]
      });
    });
  }
}

// Export for use as module or run directly
if (require.main === module) {
  const integration = new PatchMateHubIntegration();
  integration.start();
}

module.exports = PatchMateHubIntegration;