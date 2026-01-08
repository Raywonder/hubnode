import path from 'path';
import fs from 'fs/promises';

interface Client {
  clientId: string;
  application: string;
  version: string;
  platform: string;
  arch: string;
  capabilities: string[];
  registeredAt: string;
  lastSeen: string;
  status?: string;
}

interface ClientFilter {
  application?: string;
  platform?: string;
}

interface ClientStatusUpdate {
  status: string;
  timestamp: string;
  version?: string;
}

class ClientService {
  private clientsPath: string;

  constructor() {
    this.clientsPath = path.join(process.cwd(), 'storage', 'clients');
    this.ensureDirectories();
  }

  private async ensureDirectories() {
    try {
      await fs.mkdir(this.clientsPath, { recursive: true });
    } catch (error) {
      console.error('Failed to create clients directory:', error);
    }
  }

  async registerClient(client: Client): Promise<Client> {
    try {
      const clientFile = path.join(this.clientsPath, `${client.clientId}.json`);
      
      // Check if client already exists
      let existingClient = null;
      try {
        const content = await fs.readFile(clientFile, 'utf-8');
        existingClient = JSON.parse(content);
      } catch (error) {
        // Client doesn't exist, which is fine
      }

      // Merge with existing data or create new
      const updatedClient = existingClient ? {
        ...existingClient,
        version: client.version,
        lastSeen: client.lastSeen,
        capabilities: client.capabilities,
        status: 'active'
      } : {
        ...client,
        status: 'active'
      };

      await fs.writeFile(clientFile, JSON.stringify(updatedClient, null, 2));
      
      // Update clients index
      await this.updateClientsIndex();
      
      console.log(`Client ${client.clientId} registered for ${client.application}`);
      return updatedClient;
    } catch (error) {
      console.error('Failed to register client:', error);
      throw error;
    }
  }

  async updateClientStatus(clientId: string, statusUpdate: ClientStatusUpdate): Promise<void> {
    try {
      const clientFile = path.join(this.clientsPath, `${clientId}.json`);
      
      const content = await fs.readFile(clientFile, 'utf-8');
      const client = JSON.parse(content);
      
      client.status = statusUpdate.status;
      client.lastSeen = statusUpdate.timestamp;
      if (statusUpdate.version) {
        client.version = statusUpdate.version;
      }

      await fs.writeFile(clientFile, JSON.stringify(client, null, 2));
      
      console.log(`Client ${clientId} status updated to ${statusUpdate.status}`);
    } catch (error) {
      console.error('Failed to update client status:', error);
      throw error;
    }
  }

  async updateLastSeen(clientId: string): Promise<void> {
    try {
      const clientFile = path.join(this.clientsPath, `${clientId}.json`);
      
      const content = await fs.readFile(clientFile, 'utf-8');
      const client = JSON.parse(content);
      
      client.lastSeen = new Date().toISOString();
      
      await fs.writeFile(clientFile, JSON.stringify(client, null, 2));
    } catch (error) {
      console.warn(`Failed to update last seen for ${clientId}:`, error.message);
    }
  }

  async getClient(clientId: string): Promise<Client | null> {
    try {
      const clientFile = path.join(this.clientsPath, `${clientId}.json`);
      const content = await fs.readFile(clientFile, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      console.warn(`Client ${clientId} not found:`, error.message);
      return null;
    }
  }

  async getClients(filter?: ClientFilter): Promise<Client[]> {
    try {
      const files = await fs.readdir(this.clientsPath);
      const jsonFiles = files.filter(file => file.endsWith('.json') && file !== 'index.json');
      
      const clients = [];
      
      for (const file of jsonFiles) {
        try {
          const content = await fs.readFile(path.join(this.clientsPath, file), 'utf-8');
          const client = JSON.parse(content);
          
          // Apply filters
          if (filter?.application && client.application !== filter.application) {
            continue;
          }
          
          if (filter?.platform && client.platform !== filter.platform) {
            continue;
          }
          
          clients.push(client);
        } catch (error) {
          console.warn(`Failed to read client file ${file}:`, error.message);
        }
      }
      
      return clients.sort((a, b) => new Date(b.lastSeen).getTime() - new Date(a.lastSeen).getTime());
    } catch (error) {
      console.error('Failed to get clients:', error);
      return [];
    }
  }

  async removeClient(clientId: string): Promise<void> {
    try {
      const clientFile = path.join(this.clientsPath, `${clientId}.json`);
      await fs.unlink(clientFile);
      
      await this.updateClientsIndex();
      
      console.log(`Client ${clientId} removed`);
    } catch (error) {
      console.error('Failed to remove client:', error);
      throw error;
    }
  }

  async getClientStats(): Promise<any> {
    try {
      const clients = await this.getClients();
      
      const stats = {
        totalClients: clients.length,
        byApplication: {} as Record<string, number>,
        byPlatform: {} as Record<string, number>,
        byStatus: {} as Record<string, number>,
        activeToday: 0,
        activeThisWeek: 0
      };
      
      const now = new Date();
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      
      for (const client of clients) {
        // Count by application
        stats.byApplication[client.application] = (stats.byApplication[client.application] || 0) + 1;
        
        // Count by platform
        stats.byPlatform[client.platform] = (stats.byPlatform[client.platform] || 0) + 1;
        
        // Count by status
        const status = client.status || 'unknown';
        stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;
        
        // Count activity
        const lastSeen = new Date(client.lastSeen);
        if (lastSeen >= todayStart) {
          stats.activeToday++;
        }
        if (lastSeen >= weekAgo) {
          stats.activeThisWeek++;
        }
      }
      
      return stats;
    } catch (error) {
      console.error('Failed to get client stats:', error);
      return {
        totalClients: 0,
        byApplication: {},
        byPlatform: {},
        byStatus: {},
        activeToday: 0,
        activeThisWeek: 0
      };
    }
  }

  private async updateClientsIndex(): Promise<void> {
    try {
      const clients = await this.getClients();
      const index = {
        lastUpdated: new Date().toISOString(),
        totalClients: clients.length,
        applications: [...new Set(clients.map(c => c.application))],
        platforms: [...new Set(clients.map(c => c.platform))]
      };
      
      const indexFile = path.join(this.clientsPath, 'index.json');
      await fs.writeFile(indexFile, JSON.stringify(index, null, 2));
    } catch (error) {
      console.warn('Failed to update clients index:', error.message);
    }
  }
}

export { ClientService };
export default ClientService;