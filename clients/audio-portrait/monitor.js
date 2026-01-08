/**
 * Audio Portrait Client Monitor
 * Integrates with HubNode API Monitor system
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class AudioPortraitMonitor {
    constructor() {
        this.apiBase = 'http://127.0.0.1:5001/api/audio-portrait';
        this.endpoints = {
            health: '/health',
            version: '/version',
            config: '/config',
            license: '/license/validate'
        };
        this.status = {
            healthy: true,
            lastCheck: null,
            endpoints: {},
            downloads: {}
        };
    }

    async checkHealth() {
        try {
            const response = await axios.get(`${this.apiBase}${this.endpoints.health}`, {
                timeout: 10000
            });
            
            this.status.endpoints.health = {
                status: 'healthy',
                responseTime: response.headers['x-response-time'] || 'N/A',
                timestamp: new Date().toISOString()
            };
            
            return true;
        } catch (error) {
            this.status.endpoints.health = {
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            return false;
        }
    }

    async checkVersion() {
        try {
            const response = await axios.get(`${this.apiBase}${this.endpoints.version}`, {
                timeout: 10000
            });
            
            this.status.endpoints.version = {
                status: 'healthy',
                data: response.data,
                timestamp: new Date().toISOString()
            };
            
            return response.data;
        } catch (error) {
            this.status.endpoints.version = {
                status: 'error',
                error: error.message,
                timestamp: new Date().toISOString()
            };
            return null;
        }
    }

    async checkDownloads() {
        const platforms = ['mac', 'mac-arm64', 'windows'];
        const downloadStatus = {};
        
        for (const platform of platforms) {
            try {
                const response = await axios.head(`${this.apiBase}/download/${platform}`, {
                    timeout: 10000
                });
                
                downloadStatus[platform] = {
                    status: 'available',
                    size: response.headers['content-length'] || 'unknown',
                    lastModified: response.headers['last-modified'] || 'unknown',
                    timestamp: new Date().toISOString()
                };
            } catch (error) {
                downloadStatus[platform] = {
                    status: 'error',
                    error: error.message,
                    timestamp: new Date().toISOString()
                };
            }
        }
        
        this.status.downloads = downloadStatus;
        return downloadStatus;
    }

    async runFullCheck() {
        console.log('🔍 Running Audio Portrait API check...');
        
        this.status.lastCheck = new Date().toISOString();
        
        // Check all endpoints
        const healthOk = await this.checkHealth();
        const versionData = await this.checkVersion();
        const downloadStatus = await this.checkDownloads();
        
        // Overall health
        this.status.healthy = healthOk && Object.values(this.status.downloads)
            .some(status => status.status === 'available');
        
        // Log results
        console.log(`Health: ${healthOk ? '✅' : '❌'}`);
        console.log(`Version: ${versionData ? versionData.current_version : '❌'}`);
        console.log(`Downloads: ${Object.keys(downloadStatus).length} platforms checked`);
        
        return this.status;
    }

    async exportStatus() {
        const statusFile = path.join(__dirname, 'status.json');
        fs.writeFileSync(statusFile, JSON.stringify(this.status, null, 2));
        return statusFile;
    }

    // Integration with main API monitor
    getAPIMonitorConfig() {
        return {
            name: 'Audio Portrait API',
            endpoints: [
                {
                    name: 'Health Check',
                    url: `${this.apiBase}/health`,
                    method: 'GET',
                    expectedStatus: 200
                },
                {
                    name: 'Version Check',
                    url: `${this.apiBase}/version`,
                    method: 'GET', 
                    expectedStatus: 200
                },
                {
                    name: 'Mac Download',
                    url: `${this.apiBase}/download/mac`,
                    method: 'HEAD',
                    expectedStatus: 200
                },
                {
                    name: 'Windows Download', 
                    url: `${this.apiBase}/download/windows`,
                    method: 'HEAD',
                    expectedStatus: 200
                }
            ]
        };
    }
}

// CLI interface
if (require.main === module) {
    const monitor = new AudioPortraitMonitor();
    
    (async () => {
        try {
            const status = await monitor.runFullCheck();
            const statusFile = await monitor.exportStatus();
            
            console.log('\n📊 Status Summary:');
            console.log(`Overall: ${status.healthy ? '✅ Healthy' : '❌ Issues Found'}`);
            console.log(`Status file: ${statusFile}`);
            
            // Exit with error code if unhealthy
            process.exit(status.healthy ? 0 : 1);
        } catch (error) {
            console.error('❌ Monitor failed:', error.message);
            process.exit(1);
        }
    })();
}

module.exports = AudioPortraitMonitor;