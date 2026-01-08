/**
 * OpenLink Dynamic DNS API Routes
 */

const express = require('express');
const router = express.Router();
const DynDNSManager = require('../dyndns-manager');

const dyndns = new DynDNSManager();

/**
 * Create or update dynamic DNS record
 * POST /api/openlink/dyndns/create
 */
router.post('/create', async (req, res) => {
    try {
        const { userId, subdomain, domain, externalIP } = req.body;

        if (!userId || !subdomain || !domain) {
            return res.status(400).json({ 
                error: 'Missing required fields: userId, subdomain, domain' 
            });
        }

        // Use provided IP or auto-detect
        const ip = externalIP || await dyndns.getClientIP(req);

        const result = await dyndns.createDynamicRecord(userId, subdomain, domain, ip);
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Update dynamic DNS record IP
 * PUT /api/openlink/dyndns/update
 */
router.put('/update', async (req, res) => {
    try {
        const { userId, subdomain, domain, newIP } = req.body;

        if (!userId || !subdomain || !domain) {
            return res.status(400).json({ 
                error: 'Missing required fields' 
            });
        }

        // Use provided IP or auto-detect
        const ip = newIP || await dyndns.getClientIP(req);

        const result = await dyndns.updateDynamicRecord(userId, subdomain, domain, ip);
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Delete dynamic DNS record
 * DELETE /api/openlink/dyndns/:subdomain/:domain
 */
router.delete('/:subdomain/:domain', async (req, res) => {
    try {
        const { subdomain, domain } = req.params;
        const { userId } = req.body;

        if (!userId) {
            return res.status(400).json({ error: 'userId required' });
        }

        const result = await dyndns.deleteDynamicRecord(userId, subdomain, domain);
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * List user's dynamic DNS records
 * GET /api/openlink/dyndns/list/:userId
 */
router.get('/list/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const records = await dyndns.listUserRecords(userId);
        
        res.json({ records });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get client's external IP
 * GET /api/openlink/dyndns/myip
 */
router.get('/myip', async (req, res) => {
    try {
        const ip = await dyndns.getClientIP(req);
        res.json({ ip });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Update IP via simple GET (for legacy clients)
 * GET /api/openlink/dyndns/update/:userId/:subdomain/:domain
 */
router.get('/update/:userId/:subdomain/:domain', async (req, res) => {
    try {
        const { userId, subdomain, domain } = req.params;
        const ip = await dyndns.getClientIP(req);

        const result = await dyndns.updateDynamicRecord(userId, subdomain, domain, ip);
        
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
