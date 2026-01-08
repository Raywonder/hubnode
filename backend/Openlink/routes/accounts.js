/**
 * OpenLink Accounts API Routes
 */

const express = require('express');
const router = express.Router();
const AccountsManager = require('../accounts-manager');

const accounts = new AccountsManager();

/**
 * Register new account
 * POST /api/openlink/accounts/register
 */
router.post('/register', async (req, res) => {
    try {
        const { email, username, password, metadata } = req.body;

        if (!email || !username || !password) {
            return res.status(400).json({ 
                error: 'Missing required fields: email, username, password' 
            });
        }

        const account = await accounts.registerAccount(
            email, 
            username, 
            password,
            {
                ...metadata,
                ipAddress: req.ip,
                userAgent: req.headers['user-agent']
            }
        );

        res.json({ 
            success: true,
            account,
            message: 'Account created successfully'
        });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

/**
 * Login
 * POST /api/openlink/accounts/login
 */
router.post('/login', async (req, res) => {
    try {
        const { emailOrUsername, password } = req.body;

        if (!emailOrUsername || !password) {
            return res.status(400).json({ 
                error: 'Missing credentials' 
            });
        }

        const result = await accounts.authenticate(emailOrUsername, password);

        res.json({
            success: true,
            ...result
        });
    } catch (error) {
        res.status(401).json({ error: error.message });
    }
});

/**
 * Get account info
 * GET /api/openlink/accounts/:userId
 */
router.get('/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const account = await accounts.getAccount(userId);

        res.json({ account });
    } catch (error) {
        res.status(404).json({ error: error.message });
    }
});

/**
 * Update account
 * PUT /api/openlink/accounts/:userId
 */
router.put('/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const updates = req.body;

        const account = await accounts.updateAccount(userId, updates);

        res.json({
            success: true,
            account
        });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

/**
 * Link external account
 * POST /api/openlink/accounts/:userId/link
 */
router.post('/:userId/link', async (req, res) => {
    try {
        const { userId } = req.params;
        const { service, externalId } = req.body;

        if (!service || !externalId) {
            return res.status(400).json({ 
                error: 'Missing service or externalId' 
            });
        }

        const linkedAccounts = await accounts.linkAccount(userId, service, externalId);

        res.json({
            success: true,
            linkedAccounts
        });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

/**
 * Get account statistics (admin)
 * GET /api/openlink/accounts/admin/stats
 */
router.get('/admin/stats', async (req, res) => {
    try {
        const stats = await accounts.getStats();
        res.json({ stats });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * List all accounts (admin)
 * GET /api/openlink/accounts/admin/list
 */
router.get('/admin/list', async (req, res) => {
    try {
        const accountsList = await accounts.listAccounts();
        res.json({ accounts: accountsList });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
