#!/usr/bin/env node
/**
 * Audio Portrait Development MCP Server
 * Provides tools for building, testing, and deploying Audio Portrait
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

class AudioPortraitMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'audio-portrait-dev',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupRequestHandlers();
  }

  setupRequestHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'build_audio_portrait',
            description: 'Build Audio Portrait for specified platform',
            inputSchema: {
              type: 'object',
              properties: {
                platform: {
                  type: 'string',
                  enum: ['mac', 'windows', 'linux', 'all'],
                  description: 'Platform to build for'
                },
                project_path: {
                  type: 'string',
                  description: 'Path to Audio Portrait project directory'
                }
              },
              required: ['platform', 'project_path']
            }
          },
          {
            name: 'test_license_api',
            description: 'Test Audio Portrait license validation API',
            inputSchema: {
              type: 'object',
              properties: {
                license_key: {
                  type: 'string',
                  description: 'License key to test (optional)'
                },
                app_version: {
                  type: 'string',
                  description: 'App version to test with',
                  default: '0.1.0'
                }
              }
            }
          },
          {
            name: 'upload_build',
            description: 'Upload built Audio Portrait files to server',
            inputSchema: {
              type: 'object',
              properties: {
                file_path: {
                  type: 'string',
                  description: 'Path to file to upload'
                },
                destination: {
                  type: 'string',
                  enum: ['server', 'copyparty'],
                  description: 'Upload destination'
                }
              },
              required: ['file_path', 'destination']
            }
          },
          {
            name: 'check_api_health',
            description: 'Check health of all Audio Portrait API endpoints',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          },
          {
            name: 'generate_license',
            description: 'Generate test license via UFM License Manager',
            inputSchema: {
              type: 'object',
              properties: {
                license_type: {
                  type: 'string',
                  enum: ['trial', 'professional', 'enterprise'],
                  description: 'Type of license to generate'
                },
                client_email: {
                  type: 'string',
                  description: 'Client email for license generation'
                }
              },
              required: ['license_type']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'build_audio_portrait':
          return await this.buildAudioPortrait(args);
        case 'test_license_api':
          return await this.testLicenseAPI(args);
        case 'upload_build':
          return await this.uploadBuild(args);
        case 'check_api_health':
          return await this.checkAPIHealth();
        case 'generate_license':
          return await this.generateLicense(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  setupToolHandlers() {
    // Tool implementation methods will be defined here
  }

  async buildAudioPortrait(args) {
    const { platform, project_path } = args;
    
    try {
      const buildCmd = platform === 'all' ? 'npm run build' : `npm run build:${platform}`;
      const { stdout, stderr } = await execAsync(`cd "${project_path}" && ${buildCmd}`);
      
      return {
        content: [
          {
            type: 'text',
            text: `Audio Portrait build completed for ${platform}:\n\nSTDOUT:\n${stdout}\n\nSTDERR:\n${stderr}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Build failed: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async testLicenseAPI(args) {
    const { license_key = 'TEST-12345678-87654321', app_version = '0.1.0' } = args;
    
    try {
      const url = `https://api.devinecreations.net/api/audio-portrait/license/validate?license_key=${license_key}&app_version=${app_version}&platform=darwin`;
      const { stdout } = await execAsync(`curl -s "${url}"`);
      
      const response = JSON.parse(stdout);
      
      return {
        content: [
          {
            type: 'text',
            text: `License API Test Result:\n${JSON.stringify(response, null, 2)}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `License API test failed: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async uploadBuild(args) {
    const { file_path, destination } = args;
    
    try {
      let uploadCmd;
      
      if (destination === 'server') {
        uploadCmd = `scp "${file_path}" devinecr@64.20.46.178:/home/devinecr/apps/hubnode/api/audio-portrait/uploads/`;
      } else if (destination === 'copyparty') {
        uploadCmd = `curl -u "audioportrait:audio-portrait-api-2025" -F "file=@${file_path}" https://files.devinecreations.net/audio-portrait/`;
      }
      
      const { stdout, stderr } = await execAsync(uploadCmd);
      
      return {
        content: [
          {
            type: 'text',
            text: `Upload completed to ${destination}:\n\nSTDOUT:\n${stdout}\n\nSTDERR:\n${stderr}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Upload failed: ${error.message}`
          }
        ],
        isError: true
      };
    }
  }

  async checkAPIHealth() {
    const endpoints = [
      'https://api.devinecreations.net/api/audio-portrait/health',
      'https://api.devinecreations.net/api/audio-portrait/version',
      'https://api.devinecreations.net/api/audio-portrait/config'
    ];
    
    const results = [];
    
    for (const endpoint of endpoints) {
      try {
        const { stdout } = await execAsync(`curl -s -w "HTTP_CODE:%{http_code}" "${endpoint}"`);
        results.push(`${endpoint}: ${stdout}`);
      } catch (error) {
        results.push(`${endpoint}: ERROR - ${error.message}`);
      }
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `API Health Check Results:\n\n${results.join('\n\n')}`
        }
      ]
    };
  }

  async generateLicense(args) {
    const { license_type, client_email = 'test@example.com' } = args;
    
    return {
      content: [
        {
          type: 'text',
          text: `License generation would create a ${license_type} license for ${client_email}.\n\nNote: This requires access to WHMCS UFM License Manager admin interface.\nManual steps:\n1. Go to UFM License Manager in WHMCS\n2. Generate new license for AUDIO_PORTRAIT product\n3. Set type: ${license_type}\n4. Assign to client: ${client_email}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Audio Portrait MCP Server running on stdio');
  }
}

const server = new AudioPortraitMCPServer();
server.run().catch(console.error);

module.exports = AudioPortraitMCPServer;