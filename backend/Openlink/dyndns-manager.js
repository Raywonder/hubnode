/**
 * OpenLink Dynamic DNS Manager
 * Allows users to create A records pointing to their external IPs
 * Similar to DynDNS for home network hosting
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class DynDNSManager {
    constructor() {
        this.zoneBasePath = '/var/named';
        this.allowedDomains = [
            'tappedin.fm',
            'raywonderis.me',
            'walterharper.com',
            'devinecreations.net',
            'devine-creations.com'
        ];
        this.userRecordsFile = '/home/devinecr/apps/hubnode/data/dyndns-records.json';
    }

    /**
     * Create or update A record for user's external IP
     */
    async createDynamicRecord(userId, subdomain, domain, externalIP) {
        try {
            // Validate domain is allowed
            if (!this.allowedDomains.includes(domain)) {
                throw new Error('Domain not allowed for dynamic DNS');
            }

            // Validate subdomain format
            if (!/^[a-z0-9-]+$/.test(subdomain)) {
                throw new Error('Invalid subdomain format');
            }

            // Validate IP address
            if (!this.isValidIP(externalIP)) {
                throw new Error('Invalid IP address');
            }

            // Load user records
            const userRecords = await this.loadUserRecords();
            
            // Check user limits (unlimited by default, managed by accounts system)
            // Quota enforcement handled by AccountsManager
            const userCount = userRecords.filter(r => r.userId === userId).length;

            const fullDomain = `${subdomain}.${domain}`;
            
            // Add to zone file
            await this.addToZoneFile(domain, subdomain, externalIP);

            // Store record metadata
            const record = {
                userId,
                subdomain,
                domain,
                fullDomain,
                ip: externalIP,
                createdAt: new Date().toISOString(),
                lastUpdated: new Date().toISOString()
            };

            // Update or add record
            const existingIndex = userRecords.findIndex(
                r => r.subdomain === subdomain && r.domain === domain && r.userId === userId
            );

            if (existingIndex >= 0) {
                userRecords[existingIndex] = record;
            } else {
                userRecords.push(record);
            }

            await this.saveUserRecords(userRecords);

            // Reload DNS
            await this.reloadDNS();

            return {
                success: true,
                record: fullDomain,
                ip: externalIP,
                message: `Dynamic DNS record created: ${fullDomain} → ${externalIP}`
            };

        } catch (error) {
            console.error('DynDNS creation error:', error);
            throw error;
        }
    }

    /**
     * Update existing record with new IP (for IP changes)
     */
    async updateDynamicRecord(userId, subdomain, domain, newIP) {
        try {
            const userRecords = await this.loadUserRecords();
            const record = userRecords.find(
                r => r.subdomain === subdomain && r.domain === domain && r.userId === userId
            );

            if (!record) {
                throw new Error('Dynamic DNS record not found');
            }

            if (!this.isValidIP(newIP)) {
                throw new Error('Invalid IP address');
            }

            // Update zone file
            await this.updateZoneFile(domain, subdomain, record.ip, newIP);

            // Update metadata
            record.ip = newIP;
            record.lastUpdated = new Date().toISOString();

            await this.saveUserRecords(userRecords);
            await this.reloadDNS();

            return {
                success: true,
                record: `${subdomain}.${domain}`,
                oldIP: record.ip,
                newIP: newIP,
                message: 'IP address updated successfully'
            };

        } catch (error) {
            console.error('DynDNS update error:', error);
            throw error;
        }
    }

    /**
     * Delete dynamic DNS record
     */
    async deleteDynamicRecord(userId, subdomain, domain) {
        try {
            const userRecords = await this.loadUserRecords();
            const recordIndex = userRecords.findIndex(
                r => r.subdomain === subdomain && r.domain === domain && r.userId === userId
            );

            if (recordIndex < 0) {
                throw new Error('Record not found');
            }

            const record = userRecords[recordIndex];

            // Remove from zone file
            await this.removeFromZoneFile(domain, subdomain, record.ip);

            // Remove from metadata
            userRecords.splice(recordIndex, 1);
            await this.saveUserRecords(userRecords);

            await this.reloadDNS();

            return {
                success: true,
                message: `Dynamic DNS record deleted: ${subdomain}.${domain}`
            };

        } catch (error) {
            console.error('DynDNS deletion error:', error);
            throw error;
        }
    }

    /**
     * List user's dynamic DNS records
     */
    async listUserRecords(userId) {
        const userRecords = await this.loadUserRecords();
        return userRecords.filter(r => r.userId === userId);
    }

    /**
     * Add record to DNS zone file
     */
    async addToZoneFile(domain, subdomain, ip) {
        const zoneFile = path.join(this.zoneBasePath, `${domain}.db`);
        
        // Read zone file
        const zoneContent = await fs.readFile(zoneFile, 'utf8');

        // Check if record already exists
        const recordPattern = new RegExp(`^${subdomain}\\s+14400\\s+IN\\s+A\\s+`, 'm');
        
        if (recordPattern.test(zoneContent)) {
            // Update existing record
            const updatedContent = zoneContent.replace(
                recordPattern,
                `${subdomain}\t14400\tIN\tA\t${ip} # OpenLink DynDNS\n`
            );
            await fs.writeFile(zoneFile, updatedContent);
        } else {
            // Find the right place to insert (after other A records)
            const lines = zoneContent.split('\n');
            const insertIndex = lines.findIndex(line => line.includes('# OpenLink Dynamic DNS')) || 
                               lines.findIndex(line => line.trim().startsWith('webmail'));
            
            if (insertIndex === -1) {
                // Add at end of A records section
                lines.push(`${subdomain}\t14400\tIN\tA\t${ip} # OpenLink DynDNS`);
            } else {
                lines.splice(insertIndex, 0, `${subdomain}\t14400\tIN\tA\t${ip} # OpenLink DynDNS`);
            }

            await fs.writeFile(zoneFile, lines.join('\n'));
        }

        // Increment serial number
        await this.incrementSerial(domain);
    }

    /**
     * Update record in zone file
     */
    async updateZoneFile(domain, subdomain, oldIP, newIP) {
        const zoneFile = path.join(this.zoneBasePath, `${domain}.db`);
        const zoneContent = await fs.readFile(zoneFile, 'utf8');

        const updatedContent = zoneContent.replace(
            new RegExp(`^${subdomain}\\s+14400\\s+IN\\s+A\\s+${oldIP.replace(/\./g, '\\.')}.*$`, 'm'),
            `${subdomain}\t14400\tIN\tA\t${newIP} # OpenLink DynDNS`
        );

        await fs.writeFile(zoneFile, updatedContent);
        await this.incrementSerial(domain);
    }

    /**
     * Remove record from zone file
     */
    async removeFromZoneFile(domain, subdomain, ip) {
        const zoneFile = path.join(this.zoneBasePath, `${domain}.db`);
        const zoneContent = await fs.readFile(zoneFile, 'utf8');

        const updatedContent = zoneContent.replace(
            new RegExp(`^${subdomain}\\s+14400\\s+IN\\s+A\\s+${ip.replace(/\./g, '\\.')}.*\n`, 'm'),
            ''
        );

        await fs.writeFile(zoneFile, updatedContent);
        await this.incrementSerial(domain);
    }

    /**
     * Increment DNS zone serial number
     */
    async incrementSerial(domain) {
        const zoneFile = path.join(this.zoneBasePath, `${domain}.db`);
        const zoneContent = await fs.readFile(zoneFile, 'utf8');

        const serialMatch = zoneContent.match(/(\d{10})\s*;\s*serial/i);
        if (serialMatch) {
            const oldSerial = serialMatch[1];
            const newSerial = (parseInt(oldSerial) + 1).toString();
            const updatedContent = zoneContent.replace(
                new RegExp(`${oldSerial}\\s*;\\s*serial`, 'i'),
                `${newSerial} ; serial`
            );
            await fs.writeFile(zoneFile, updatedContent);
        }
    }

    /**
     * Reload DNS server
     */
    async reloadDNS() {
        try {
            await execPromise('/usr/local/cpanel/scripts/restartsrv_pdns');
            return { success: true };
        } catch (error) {
            console.error('DNS reload error:', error);
            throw new Error('Failed to reload DNS server');
        }
    }

    /**
     * Validate IP address
     */
    isValidIP(ip) {
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }

    /**
     * Load user records from storage
     */
    async loadUserRecords() {
        try {
            const data = await fs.readFile(this.userRecordsFile, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            if (error.code === 'ENOENT') {
                return [];
            }
            throw error;
        }
    }

    /**
     * Save user records to storage
     */
    async saveUserRecords(records) {
        await fs.writeFile(
            this.userRecordsFile,
            JSON.stringify(records, null, 2)
        );
    }

    /**
     * Get client's external IP automatically
     */
    async getClientIP(req) {
        return req.headers['x-forwarded-for']?.split(',')[0].trim() || 
               req.headers['x-real-ip'] || 
               req.connection.remoteAddress;
    }
}

module.exports = DynDNSManager;
