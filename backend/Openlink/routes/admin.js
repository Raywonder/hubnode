/**
 * OpenLink Admin API Routes
 * Service management, monitoring, and control
 */

const express = require('express');
const router = express.Router();
const { exec } = require('child_process');
const util = require('util');
const fs = require('fs').promises;
const execPromise = util.promisify(exec);

/**
 * Restart OpenLink backend service
 * POST /api/openlink/admin/restart
 */
router.post('/restart', async (req, res) => {
    try {
        const { service } = req.body;
        
        let command;
        switch (service) {
            case 'openlink':
                command = 'systemctl restart openlink-backend';
                break;
            case 'hubnode':
                command = 'systemctl restart hubnode-backend';
                break;
            case 'both':
                command = 'systemctl restart openlink-backend hubnode-backend';
                break;
            default:
                return res.status(400).json({ error: 'Invalid service specified' });
        }

        await execPromise(command);

        res.json({
            success: true,
            message: `Service ${service} restarted successfully`
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get service status
 * GET /api/openlink/admin/status
 */
router.get('/status', async (req, res) => {
    try {
        const services = ['openlink-backend', 'hubnode-backend', 'pdns', 'nginx'];
        const status = {};

        for (const service of services) {
            try {
                const { stdout } = await execPromise(`systemctl is-active ${service}`);
                status[service] = stdout.trim();
            } catch (error) {
                status[service] = 'inactive';
            }
        }

        res.json({ status });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get service logs
 * GET /api/openlink/admin/logs/:service
 */
router.get('/logs/:service', async (req, res) => {
    try {
        const { service } = req.params;
        const { lines = 50 } = req.query;

        let logFile;
        switch (service) {
            case 'openlink':
                logFile = '/var/log/openlink-backend.log';
                break;
            case 'hubnode':
                logFile = '/var/log/hubnode-backend.log';
                break;
            case 'openlink-error':
                logFile = '/var/log/openlink-backend.error.log';
                break;
            case 'hubnode-error':
                logFile = '/var/log/hubnode-backend.error.log';
                break;
            default:
                return res.status(400).json({ error: 'Invalid service' });
        }

        const { stdout } = await execPromise(`tail -n ${lines} ${logFile}`);

        res.json({
            service,
            lines: stdout.split('\n').filter(line => line.trim())
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Reload DNS server
 * POST /api/openlink/admin/dns/reload
 */
router.post('/dns/reload', async (req, res) => {
    try {
        await execPromise('/usr/local/cpanel/scripts/restartsrv_pdns');

        res.json({
            success: true,
            message: 'DNS server reloaded successfully'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Get system stats
 * GET /api/openlink/admin/stats/system
 */
router.get('/stats/system', async (req, res) => {
    try {
        // Get memory usage
        const { stdout: memInfo } = await execPromise('free -m');
        const memLines = memInfo.split('\n')[1].split(/\s+/);
        
        // Get disk usage
        const { stdout: diskInfo } = await execPromise('df -h /home');
        const diskLines = diskInfo.split('\n')[1].split(/\s+/);

        // Get CPU load
        const { stdout: loadAvg } = await execPromise('uptime');
        const loadMatch = loadAvg.match(/load average: ([\d.]+), ([\d.]+), ([\d.]+)/);

        // Count DynDNS records
        const dyndnsData = await fs.readFile('/home/devinecr/apps/hubnode/data/dyndns-records.json', 'utf8');
        const dyndnsRecords = JSON.parse(dyndnsData);

        // Count accounts
        const accountsData = await fs.readFile('/home/devinecr/shared/accounts-database.json', 'utf8');
        const accountsDb = JSON.parse(accountsData);

        res.json({
            memory: {
                total: parseInt(memLines[1]),
                used: parseInt(memLines[2]),
                free: parseInt(memLines[3]),
                unit: 'MB'
            },
            disk: {
                total: diskLines[1],
                used: diskLines[2],
                available: diskLines[3],
                percent: diskLines[4]
            },
            load: loadMatch ? {
                '1min': parseFloat(loadMatch[1]),
                '5min': parseFloat(loadMatch[2]),
                '15min': parseFloat(loadMatch[3])
            } : null,
            dyndns: {
                totalRecords: dyndnsRecords.length,
                uniqueUsers: [...new Set(dyndnsRecords.map(r => r.userId))].length
            },
            accounts: {
                total: accountsDb.accounts?.length || 0,
                max: 20,
                active: accountsDb.accounts?.filter(a => a.status === 'active').length || 0
            }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Clear service logs
 * POST /api/openlink/admin/logs/clear
 */
router.post('/logs/clear', async (req, res) => {
    try {
        const { service } = req.body;

        let logFile;
        switch (service) {
            case 'openlink':
                logFile = '/var/log/openlink-backend.log';
                break;
            case 'hubnode':
                logFile = '/var/log/hubnode-backend.log';
                break;
            case 'all':
                await execPromise('truncate -s 0 /var/log/openlink-backend*.log /var/log/hubnode-backend*.log');
                return res.json({ success: true, message: 'All logs cleared' });
            default:
                return res.status(400).json({ error: 'Invalid service' });
        }

        await execPromise(`truncate -s 0 ${logFile}`);

        res.json({
            success: true,
            message: `Logs cleared for ${service}`
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Backup databases
 * POST /api/openlink/admin/backup
 */
router.post('/backup', async (req, res) => {
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupDir = `/home/devinecr/backups/openlink-${timestamp}`;

        await execPromise(`mkdir -p ${backupDir}`);
        await execPromise(`cp /home/devinecr/shared/accounts-database.json ${backupDir}/`);
        await execPromise(`cp /home/devinecr/apps/hubnode/data/dyndns-records.json ${backupDir}/`);

        res.json({
            success: true,
            message: 'Backup created successfully',
            location: backupDir
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
