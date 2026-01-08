/**
 * OpenLink Shared Accounts Manager
 * Cross-platform authentication and account management
 * Syncs with WHMCS, cPanel, and all OpenLink domains
 */

const fs = require('fs').promises;
const crypto = require('crypto');
const path = require('path');

class AccountsManager {
    constructor() {
        this.dbPath = '/home/devinecr/shared/accounts-database.json';
        this.maxAccounts = 20;
    }

    /**
     * Load accounts database
     */
    async loadDatabase() {
        try {
            const data = await fs.readFile(this.dbPath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                return { 
                    version: "1.0.0",
                    lastUpdated: new Date().toISOString(),
                    accounts: [],
                    settings: {
                        maxAccounts: 20,
                        requireEmailVerification: true,
                        allowedDomains: [
                            "tappedin.fm",
                            "raywonderis.me", 
                            "walterharper.com",
                            "devinecreations.net",
                            "devine-creations.com"
                        ],
                        sessionTimeout: 86400
                    }
                };
            }
            throw error;
        }
    }

    /**
     * Save accounts database
     */
    async saveDatabase(db) {
        db.lastUpdated = new Date().toISOString();
        await fs.writeFile(this.dbPath, JSON.stringify(db, null, 2));
    }

    /**
     * Register new account
     */
    async registerAccount(email, username, password, metadata = {}) {
        const db = await this.loadDatabase();

        // Check account limit
        if (db.accounts.length >= this.maxAccounts) {
            throw new Error(`Maximum ${this.maxAccounts} accounts reached`);
        }

        // Check if email exists
        if (db.accounts.find(a => a.email === email)) {
            throw new Error('Email already registered');
        }

        // Check if username exists
        if (db.accounts.find(a => a.username === username)) {
            throw new Error('Username already taken');
        }

        // Generate user ID
        const userId = this.generateUserId();

        // Hash password
        const passwordHash = this.hashPassword(password);

        // Create account
        const account = {
            userId,
            email,
            username,
            passwordHash,
            createdAt: new Date().toISOString(),
            lastLogin: null,
            emailVerified: false,
            status: 'active',
            permissions: {
                dyndns: true,
                fileSharing: true,
                remoteDesktop: true,
                apiAccess: true
            },
            quota: {
                dyndnsRecords: 0,
                maxDyndnsRecords: -1, // -1 = unlimited
                storageUsed: 0,
                maxStorage: 10737418240 // 10GB default
            },
            metadata: {
                ...metadata,
                ipAddress: metadata.ipAddress || null,
                userAgent: metadata.userAgent || null
            },
            linkedAccounts: {
                whmcs: null,
                cpanel: null,
                mastodon: null,
                jellyfin: null
            }
        };

        db.accounts.push(account);
        await this.saveDatabase(db);

        // Return account without password hash
        const { passwordHash: _, ...safeAccount } = account;
        return safeAccount;
    }

    /**
     * Authenticate account
     */
    async authenticate(emailOrUsername, password) {
        const db = await this.loadDatabase();
        
        const account = db.accounts.find(
            a => a.email === emailOrUsername || a.username === emailOrUsername
        );

        if (!account) {
            throw new Error('Invalid credentials');
        }

        if (account.status !== 'active') {
            throw new Error('Account is not active');
        }

        // Verify password
        const passwordHash = this.hashPassword(password);
        if (passwordHash !== account.passwordHash) {
            throw new Error('Invalid credentials');
        }

        // Update last login
        account.lastLogin = new Date().toISOString();
        await this.saveDatabase(db);

        // Generate session token
        const sessionToken = this.generateSessionToken(account.userId);

        const { passwordHash: _, ...safeAccount } = account;
        return {
            account: safeAccount,
            sessionToken
        };
    }

    /**
     * Get account by userId
     */
    async getAccount(userId) {
        const db = await this.loadDatabase();
        const account = db.accounts.find(a => a.userId === userId);
        
        if (!account) {
            throw new Error('Account not found');
        }

        const { passwordHash: _, ...safeAccount } = account;
        return safeAccount;
    }

    /**
     * Update account
     */
    async updateAccount(userId, updates) {
        const db = await this.loadDatabase();
        const accountIndex = db.accounts.findIndex(a => a.userId === userId);

        if (accountIndex === -1) {
            throw new Error('Account not found');
        }

        // Merge updates (prevent password hash update through this method)
        delete updates.passwordHash;
        delete updates.userId;

        db.accounts[accountIndex] = {
            ...db.accounts[accountIndex],
            ...updates
        };

        await this.saveDatabase(db);
        
        const { passwordHash: _, ...safeAccount } = db.accounts[accountIndex];
        return safeAccount;
    }

    /**
     * Link account to external service
     */
    async linkAccount(userId, service, externalId) {
        const db = await this.loadDatabase();
        const account = db.accounts.find(a => a.userId === userId);

        if (!account) {
            throw new Error('Account not found');
        }

        account.linkedAccounts[service] = externalId;
        await this.saveDatabase(db);

        return account.linkedAccounts;
    }

    /**
     * Increment DynDNS record count
     */
    async incrementDynDNSCount(userId, increment = 1) {
        const db = await this.loadDatabase();
        const account = db.accounts.find(a => a.userId === userId);

        if (!account) {
            throw new Error('Account not found');
        }

        account.quota.dyndnsRecords += increment;
        
        // Check limit if not unlimited
        if (account.quota.maxDyndnsRecords !== -1 && 
            account.quota.dyndnsRecords > account.quota.maxDyndnsRecords) {
            throw new Error('DynDNS record limit exceeded');
        }

        await this.saveDatabase(db);
        return account.quota;
    }

    /**
     * List all accounts (admin only)
     */
    async listAccounts() {
        const db = await this.loadDatabase();
        return db.accounts.map(({ passwordHash, ...account }) => account);
    }

    /**
     * Get account statistics
     */
    async getStats() {
        const db = await this.loadDatabase();
        
        return {
            totalAccounts: db.accounts.length,
            maxAccounts: this.maxAccounts,
            activeAccounts: db.accounts.filter(a => a.status === 'active').length,
            verifiedAccounts: db.accounts.filter(a => a.emailVerified).length,
            totalDynDNSRecords: db.accounts.reduce((sum, a) => sum + a.quota.dyndnsRecords, 0)
        };
    }

    /**
     * Hash password (simple SHA256 - should use bcrypt in production)
     */
    hashPassword(password) {
        return crypto.createHash('sha256').update(password).digest('hex');
    }

    /**
     * Generate user ID
     */
    generateUserId() {
        return 'user_' + crypto.randomBytes(16).toString('hex');
    }

    /**
     * Generate session token
     */
    generateSessionToken(userId) {
        const payload = {
            userId,
            timestamp: Date.now()
        };
        return Buffer.from(JSON.stringify(payload)).toString('base64');
    }

    /**
     * Verify session token
     */
    verifySessionToken(token) {
        try {
            const payload = JSON.parse(Buffer.from(token, 'base64').toString());
            
            // Check if token is expired (24 hours)
            if (Date.now() - payload.timestamp > 86400000) {
                throw new Error('Session expired');
            }

            return payload.userId;
        } catch (error) {
            throw new Error('Invalid session token');
        }
    }
}

module.exports = AccountsManager;
