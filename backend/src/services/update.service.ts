import semver from 'semver';
import path from 'path';
import fs from 'fs/promises';

interface UpdateCheckRequest {
  clientId: string;
  application: string;
  currentVersion: string;
  platform: string;
  arch: string;
  userId?: string;
}

interface UpdateInfo {
  updateAvailable: boolean;
  latestVersion?: string;
  downloadUrl?: string;
  releaseNotes?: string;
  accessibilityFeatures?: string;
  isSecurityUpdate?: boolean;
  downloadSize?: number;
  forceUpdate?: boolean;
}

interface UpdateFeedRequest {
  application: string;
  platform: string;
  arch: string;
}

interface UpdatePushRequest {
  clientId: string;
  application: string;
  version: string;
  downloadUrl: string;
  releaseNotes?: string;
  isSecurityUpdate: boolean;
  forceUpdate: boolean;
  pushedAt: string;
}

interface BroadcastUpdateRequest {
  application: string;
  version: string;
  downloadUrl: string;
  releaseNotes?: string;
  isSecurityUpdate: boolean;
  forceUpdate: boolean;
  platforms?: string[] | null;
  pushedAt: string;
}

class UpdateService {
  private updatesPath: string;
  private configPath: string;

  constructor() {
    this.updatesPath = path.join(process.cwd(), 'storage', 'updates');
    this.configPath = path.join(process.cwd(), 'storage', 'config');
    this.ensureDirectories();
  }

  private async ensureDirectories() {
    try {
      await fs.mkdir(this.updatesPath, { recursive: true });
      await fs.mkdir(this.configPath, { recursive: true });
    } catch (error) {
      console.error('Failed to create directories:', error);
    }
  }

  async checkForUpdates(request: UpdateCheckRequest): Promise<UpdateInfo> {
    try {
      // Get latest version info for the application
      const versionInfo = await this.getLatestVersionInfo(request.application, request.platform, request.arch);
      
      if (!versionInfo) {
        return {
          updateAvailable: false
        };
      }

      // Compare versions
      const currentVersion = this.normalizeVersion(request.currentVersion);
      const latestVersion = this.normalizeVersion(versionInfo.version);
      
      const updateAvailable = semver.gt(latestVersion, currentVersion);

      if (!updateAvailable) {
        return {
          updateAvailable: false,
          latestVersion: versionInfo.version
        };
      }

      // Check if client has pending updates
      const pendingUpdate = await this.getPendingUpdate(request.clientId);
      
      return {
        updateAvailable: true,
        latestVersion: versionInfo.version,
        downloadUrl: versionInfo.downloadUrl,
        releaseNotes: versionInfo.releaseNotes,
        accessibilityFeatures: versionInfo.accessibilityFeatures,
        isSecurityUpdate: versionInfo.isSecurityUpdate || false,
        downloadSize: versionInfo.downloadSize,
        forceUpdate: pendingUpdate?.forceUpdate || false
      };
    } catch (error) {
      console.error('Update check failed:', error);
      return {
        updateAvailable: false
      };
    }
  }

  async getUpdateFeed(request: UpdateFeedRequest): Promise<any> {
    try {
      const versionInfo = await this.getLatestVersionInfo(request.application, request.platform, request.arch);
      
      if (!versionInfo) {
        return {
          name: request.application,
          description: `${request.application} updates`,
          homepage: 'https://tappedin.fm',
          repository: {
            type: 'git',
            url: 'https://github.com/raywonder/bema.git'
          },
          releases: []
        };
      }

      // Format for electron-updater
      return {
        name: request.application,
        description: `${request.application} updates`,
        homepage: 'https://tappedin.fm',
        repository: {
          type: 'git',
          url: 'https://github.com/raywonder/bema.git'
        },
        releases: [
          {
            version: versionInfo.version,
            notes: versionInfo.releaseNotes || 'Bug fixes and improvements',
            pub_date: versionInfo.releaseDate || new Date().toISOString(),
            platforms: {
              [request.platform]: {
                signature: versionInfo.signature || '',
                url: versionInfo.downloadUrl
              }
            }
          }
        ]
      };
    } catch (error) {
      console.error('Failed to get update feed:', error);
      return {
        name: request.application,
        releases: []
      };
    }
  }

  async pushUpdate(request: UpdatePushRequest): Promise<any> {
    try {
      // Store the push notification for the client
      const pushPath = path.join(this.updatesPath, 'pushes', `${request.clientId}.json`);
      await fs.mkdir(path.dirname(pushPath), { recursive: true });
      
      await fs.writeFile(pushPath, JSON.stringify({
        ...request,
        createdAt: new Date().toISOString(),
        status: 'pending'
      }, null, 2));

      // Log the push
      await this.logUpdatePush({
        type: 'individual',
        clientId: request.clientId,
        application: request.application,
        version: request.version,
        timestamp: request.pushedAt
      });

      return {
        success: true,
        pushId: `${request.clientId}-${Date.now()}`,
        scheduledFor: request.pushedAt
      };
    } catch (error) {
      console.error('Failed to push update:', error);
      throw error;
    }
  }

  async broadcastUpdate(request: BroadcastUpdateRequest): Promise<any> {
    try {
      // Get all clients for the application
      const { default: ClientService } = await import('./client.service');
      const clientService = new ClientService();
      
      const clients = await clientService.getClients({
        application: request.application,
        platform: request.platforms ? undefined : undefined // Will be filtered later
      });

      let clientsNotified = 0;
      const results = [];

      for (const client of clients) {
        // Filter by platform if specified
        if (request.platforms && !request.platforms.includes(client.platform)) {
          continue;
        }

        try {
          await this.pushUpdate({
            clientId: client.clientId,
            application: request.application,
            version: request.version,
            downloadUrl: request.downloadUrl,
            releaseNotes: request.releaseNotes,
            isSecurityUpdate: request.isSecurityUpdate,
            forceUpdate: request.forceUpdate,
            pushedAt: request.pushedAt
          });

          clientsNotified++;
          results.push({
            clientId: client.clientId,
            status: 'success'
          });
        } catch (error) {
          results.push({
            clientId: client.clientId,
            status: 'failed',
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
      }

      // Log the broadcast
      await this.logUpdatePush({
        type: 'broadcast',
        application: request.application,
        version: request.version,
        clientsTargeted: clients.length,
        clientsNotified,
        platforms: request.platforms,
        timestamp: request.pushedAt
      });

      return {
        success: true,
        clientsNotified,
        totalClients: clients.length,
        results
      };
    } catch (error) {
      console.error('Failed to broadcast update:', error);
      throw error;
    }
  }

  private async getLatestVersionInfo(application: string, platform: string, arch: string): Promise<any> {
    try {
      const versionFile = path.join(this.updatesPath, 'versions', `${application}.json`);
      const content = await fs.readFile(versionFile, 'utf-8');
      const versionData = JSON.parse(content);
      
      // Find the best match for platform and arch
      const platformKey = `${platform}-${arch}`;
      
      if (versionData.platforms && versionData.platforms[platformKey]) {
        return {
          ...versionData,
          ...versionData.platforms[platformKey]
        };
      }
      
      // Fallback to generic platform
      if (versionData.platforms && versionData.platforms[platform]) {
        return {
          ...versionData,
          ...versionData.platforms[platform]
        };
      }
      
      // Return default version info
      return versionData;
    } catch (error) {
      console.warn(`No version info found for ${application}:`, error.message);
      return null;
    }
  }

  private async getPendingUpdate(clientId: string): Promise<any> {
    try {
      const pushPath = path.join(this.updatesPath, 'pushes', `${clientId}.json`);
      const content = await fs.readFile(pushPath, 'utf-8');
      const push = JSON.parse(content);
      
      if (push.status === 'pending') {
        return push;
      }
      
      return null;
    } catch (error) {
      return null; // No pending update
    }
  }

  private normalizeVersion(version: string): string {
    // Clean up version string for semver comparison
    return version.replace(/^v/, '').split('-')[0];
  }

  private async logUpdatePush(logData: any): Promise<void> {
    try {
      const logFile = path.join(this.updatesPath, 'logs', `${new Date().toISOString().split('T')[0]}.json`);
      await fs.mkdir(path.dirname(logFile), { recursive: true });
      
      let logs = [];
      try {
        const content = await fs.readFile(logFile, 'utf-8');
        logs = JSON.parse(content);
      } catch (error) {
        // File doesn't exist, start with empty array
      }
      
      logs.push({
        ...logData,
        timestamp: new Date().toISOString()
      });
      
      await fs.writeFile(logFile, JSON.stringify(logs, null, 2));
    } catch (error) {
      console.error('Failed to log update push:', error);
    }
  }
}

export { UpdateService };
export default UpdateService;