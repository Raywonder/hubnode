import { Router, Request, Response } from 'express';
import UpdateService from '../services/update.service';
import ClientService from '../services/client.service';

const router = Router();
const updateService = new UpdateService();
const clientService = new ClientService();

/**
 * Software Update Routes for HubNode API
 * Handles software update pushes and client registration
 */

// Register a client application
router.post('/clients/register', async (req: Request, res: Response) => {
  try {
    const {
      clientId,
      application,
      version,
      platform,
      arch,
      capabilities,
      lastSeen
    } = req.body;

    if (!clientId || !application || !version) {
      return res.status(400).json({
        error: 'Missing required fields: clientId, application, version'
      });
    }

    const client = await clientService.registerClient({
      clientId,
      application,
      version,
      platform: platform || 'unknown',
      arch: arch || 'unknown',
      capabilities: capabilities || [],
      lastSeen: lastSeen || new Date().toISOString(),
      registeredAt: new Date().toISOString()
    });

    res.json({
      success: true,
      message: 'Client registered successfully',
      client
    });
  } catch (error) {
    console.error('Client registration error:', error);
    return res.status(500).json({
      error: 'Failed to register client',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Update client status
router.put('/clients/:clientId/status', async (req: Request, res: Response) => {
  try {
    const { clientId } = req.params;
    const { status, timestamp, version } = req.body;

    await clientService.updateClientStatus(clientId, {
      status,
      timestamp: timestamp || new Date().toISOString(),
      version
    });

    res.json({
      success: true,
      message: 'Client status updated'
    });
  } catch (error) {
    console.error('Client status update error:', error);
    return res.status(500).json({
      error: 'Failed to update client status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Check for software updates
router.post('/software-updates', async (req: Request, res: Response) => {
  try {
    const {
      clientId,
      application,
      currentVersion,
      platform,
      arch,
      userId
    } = req.body;

    if (!clientId || !application || !currentVersion) {
      return res.status(400).json({
        error: 'Missing required fields: clientId, application, currentVersion'
      });
    }

    // Update client's last seen time
    await clientService.updateLastSeen(clientId || '');

    const updateInfo = await updateService.checkForUpdates({
      clientId,
      application,
      currentVersion,
      platform: platform || 'unknown',
      arch: arch || 'unknown',
      userId
    });

    res.json(updateInfo);
  } catch (error) {
    console.error('Update check error:', error);
    return res.status(500).json({
      error: 'Failed to check for updates',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get update feed for electron-updater
router.get('/software-updates/feed/:application', async (req: Request, res: Response) => {
  try {
    const { application } = req.params;
    const { platform, arch } = req.query;

    const feed = await updateService.getUpdateFeed({
      application,
      platform: platform as string || 'unknown',
      arch: arch as string || 'unknown'
    });

    res.json(feed);
  } catch (error) {
    console.error('Update feed error:', error);
    return res.status(500).json({
      error: 'Failed to get update feed',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Push update to specific client
router.post('/software-updates/push', async (req: Request, res: Response) => {
  try {
    const {
      clientId,
      application,
      version,
      downloadUrl,
      releaseNotes,
      isSecurityUpdate,
      forceUpdate
    } = req.body;

    if (!clientId || !application || !version || !downloadUrl) {
      return res.status(400).json({
        error: 'Missing required fields: clientId, application, version, downloadUrl'
      });
    }

    const result = await updateService.pushUpdate({
      clientId,
      application,
      version,
      downloadUrl,
      releaseNotes,
      isSecurityUpdate: isSecurityUpdate || false,
      forceUpdate: forceUpdate || false,
      pushedAt: new Date().toISOString()
    });

    res.json({
      success: true,
      message: 'Update pushed successfully',
      result
    });
  } catch (error) {
    console.error('Update push error:', error);
    return res.status(500).json({
      error: 'Failed to push update',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Push update to all clients of an application
router.post('/software-updates/broadcast/:application', async (req: Request, res: Response) => {
  try {
    const { application } = req.params;
    const {
      version,
      downloadUrl,
      releaseNotes,
      isSecurityUpdate,
      forceUpdate,
      platforms
    } = req.body;

    if (!version || !downloadUrl) {
      return res.status(400).json({
        error: 'Missing required fields: version, downloadUrl'
      });
    }

    const result = await updateService.broadcastUpdate({
      application,
      version,
      downloadUrl,
      releaseNotes,
      isSecurityUpdate: isSecurityUpdate || false,
      forceUpdate: forceUpdate || false,
      platforms: platforms || null, // null means all platforms
      pushedAt: new Date().toISOString()
    });

    res.json({
      success: true,
      message: `Update broadcast to all ${application} clients`,
      clientsNotified: result.clientsNotified,
      result
    });
  } catch (error) {
    console.error('Update broadcast error:', error);
    return res.status(500).json({
      error: 'Failed to broadcast update',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get all registered clients
router.get('/clients', async (req: Request, res: Response) => {
  try {
    const { application, platform } = req.query;
    
    const clients = await clientService.getClients({
      application: application as string,
      platform: platform as string
    });

    res.json({
      success: true,
      clients,
      count: clients.length
    });
  } catch (error) {
    console.error('Get clients error:', error);
    return res.status(500).json({
      error: 'Failed to get clients',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Get client details
router.get('/clients/:clientId', async (req: Request, res: Response) => {
  try {
    const { clientId } = req.params;
    
    const client = await clientService.getClient(clientId);
    
    if (!client) {
      return res.status(404).json({
        error: 'Client not found'
      });
    }

    res.json({
      success: true,
      client
    });
  } catch (error) {
    console.error('Get client error:', error);
    return res.status(500).json({
      error: 'Failed to get client',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router;