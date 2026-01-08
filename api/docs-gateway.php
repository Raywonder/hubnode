<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gateway API Documentation - HubNode</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .back-link {
            display: inline-block;
            color: white;
            text-decoration: none;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 5px;
            transition: background 0.3s;
        }

        .back-link:hover {
            background: rgba(255,255,255,0.3);
        }

        .content {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        h2 {
            color: #667eea;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        h2:first-child {
            margin-top: 0;
        }

        h3 {
            color: #764ba2;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        p {
            line-height: 1.6;
            color: #333;
            margin-bottom: 15px;
        }

        .endpoint {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }

        .method {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9em;
            margin-right: 10px;
        }

        .method.get {
            background: #28a745;
            color: white;
        }

        .method.post {
            background: #007bff;
            color: white;
        }

        .path {
            font-family: 'Courier New', monospace;
            font-size: 1.1em;
            color: #333;
        }

        .description {
            margin-top: 10px;
            color: #666;
        }

        .code-block {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        .note {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }

        .note strong {
            color: #856404;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }

        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #667eea;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #e83e8c;
        }

        ul {
            margin-left: 20px;
            margin-bottom: 15px;
        }

        li {
            margin-bottom: 8px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to API Dashboard</a>

        <div class="header">
            <h1>🌐 Gateway API Documentation</h1>
            <p>Unified API Gateway for HubNode Services</p>
        </div>

        <div class="content">
            <h2>Overview</h2>
            <p>The HubNode Unified API Gateway acts as a single entry point for all backend services. It routes requests to the appropriate service based on the path prefix and handles authentication, logging, and request forwarding.</p>

            <h2>Base URL</h2>
            <p>Access the gateway via any of these domains:</p>
            <ul>
                <li><code>https://api.devinecreations.net</code></li>
                <li><code>https://api.devine-creations.com</code></li>
                <li><code>https://api.tetoeehoward.com</code></li>
                <li><code>https://api.tappedin.fm</code></li>
            </ul>

            <h2>Authentication</h2>
            <p>Most endpoints require authentication using an API key. Include the key in your requests using one of these methods:</p>

            <h3>Header Method (Recommended)</h3>
            <div class="code-block">X-API-Key: your-api-key-here</div>

            <h3>Query Parameter Method</h3>
            <div class="code-block">?api_key=your-api-key-here</div>

            <div class="note">
                <strong>Note:</strong> Authentication requirements vary by endpoint. Service-specific operations typically require valid API keys, while public endpoints like <code>/health</code> and <code>/api/info</code> are accessible without authentication.
            </div>

            <h2>Available Services</h2>
            <p>The gateway routes requests to these backend services:</p>

            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Prefix</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>CopyParty Admin</td>
                        <td><code>/api/copyparty</code></td>
                        <td>File management and sharing operations</td>
                    </tr>
                    <tr>
                        <td>Services Manager</td>
                        <td><code>/api/services</code></td>
                        <td>System service control and Docker management</td>
                    </tr>
                    <tr>
                        <td>Audio Portrait</td>
                        <td><code>/audio-portrait</code></td>
                        <td>Audio Portrait application services</td>
                    </tr>
                    <tr>
                        <td>Logs Collector</td>
                        <td><code>/logs</code></td>
                        <td>Application logs and analytics</td>
                    </tr>
                </tbody>
            </table>

            <h2>Gateway Endpoints</h2>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Returns the API dashboard (HTML) for browser requests, or gateway information (JSON) for API clients.</p>
                    <p><strong>Authentication:</strong> None required</p>
                    <p><strong>Response:</strong> HTML page or JSON gateway info</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/health</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Check if the API gateway is online and healthy.</p>
                    <p><strong>Authentication:</strong> None required</p>
                    <p><strong>Response Example:</strong></p>
                    <div class="code-block">{
  "gateway": "online",
  "status": "healthy",
  "timestamp": "2025-10-03T14:00:00.000000",
  "uptime": "N/A"
}</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/info</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get detailed information about the gateway, available services, and endpoints.</p>
                    <p><strong>Authentication:</strong> None required</p>
                    <p><strong>Response:</strong> JSON object with gateway metadata, service list, and authentication methods</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/webhook/*</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Webhook endpoints for external integrations and callbacks.</p>
                    <p><strong>Authentication:</strong> Varies by webhook type</p>
                    <p><strong>Usage:</strong> Contact your administrator for webhook configuration</p>
                </div>
            </div>

            <h2>Request Forwarding</h2>
            <p>All requests with service-specific prefixes are automatically forwarded to the appropriate backend service. The gateway adds the following headers to forwarded requests:</p>

            <table>
                <thead>
                    <tr>
                        <th>Header</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><code>X-Real-IP</code></td>
                        <td>Original client IP address</td>
                    </tr>
                    <tr>
                        <td><code>X-Forwarded-For</code></td>
                        <td>Full proxy chain of IP addresses</td>
                    </tr>
                    <tr>
                        <td><code>X-Forwarded-Proto</code></td>
                        <td>Original protocol (http/https)</td>
                    </tr>
                    <tr>
                        <td><code>Host</code></td>
                        <td>Original hostname from request</td>
                    </tr>
                </tbody>
            </table>

            <h2>Example Usage</h2>

            <h3>Check Gateway Health</h3>
            <div class="code-block">curl https://api.devinecreations.net/health</div>

            <h3>Get Gateway Information</h3>
            <div class="code-block">curl https://api.devinecreations.net/api/info</div>

            <h3>Access CopyParty Service</h3>
            <div class="code-block">curl -H "X-API-Key: your-key" \
  https://api.devinecreations.net/api/copyparty/health</div>

            <h3>Access Services Manager</h3>
            <div class="code-block">curl -H "X-API-Key: your-key" \
  https://api.devinecreations.net/api/services/system/status</div>

            <h2>Rate Limiting & Timeouts</h2>
            <p>The gateway enforces the following limits:</p>
            <ul>
                <li><strong>Connection Timeout:</strong> 60 seconds</li>
                <li><strong>Send Timeout:</strong> 60 seconds</li>
                <li><strong>Read Timeout:</strong> 60 seconds</li>
            </ul>

            <h2>CORS Support</h2>
            <p>The gateway includes CORS headers for cross-origin requests:</p>
            <ul>
                <li><strong>Allowed Origins:</strong> * (all origins)</li>
                <li><strong>Allowed Methods:</strong> GET, POST, PUT, DELETE, OPTIONS</li>
                <li><strong>Allowed Headers:</strong> Authorization, Content-Type, X-API-Key, X-User</li>
            </ul>

            <h2>Error Responses</h2>
            <p>The gateway returns standard HTTP status codes:</p>
            <table>
                <thead>
                    <tr>
                        <th>Status Code</th>
                        <th>Meaning</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>200</td>
                        <td>Success</td>
                    </tr>
                    <tr>
                        <td>400</td>
                        <td>Bad Request - Invalid parameters</td>
                    </tr>
                    <tr>
                        <td>401</td>
                        <td>Unauthorized - Invalid or missing API key</td>
                    </tr>
                    <tr>
                        <td>403</td>
                        <td>Forbidden - Valid credentials but insufficient permissions</td>
                    </tr>
                    <tr>
                        <td>404</td>
                        <td>Not Found - Endpoint doesn't exist</td>
                    </tr>
                    <tr>
                        <td>500</td>
                        <td>Internal Server Error</td>
                    </tr>
                    <tr>
                        <td>502</td>
                        <td>Bad Gateway - Backend service unavailable</td>
                    </tr>
                    <tr>
                        <td>504</td>
                        <td>Gateway Timeout - Backend service didn't respond in time</td>
                    </tr>
                </tbody>
            </table>

            <h2>Support</h2>
            <p>For API access, authentication issues, or technical support, contact your system administrator.</p>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <a href="/" class="back-link">← Back to API Dashboard</a>
        </div>
    </div>
</body>
</html>
