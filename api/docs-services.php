<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Services Manager API Documentation - HubNode</title>
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
            line-height: 1.5;
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

        .warning {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }

        .warning strong {
            color: #721c24;
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

        .section-category {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin: 30px 0 20px 0;
            font-weight: 600;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to API Dashboard</a>

        <div class="header">
            <h1>⚙️ Services Manager API Documentation</h1>
            <p>System Service Control and Docker Management</p>
        </div>

        <div class="content">
            <h2>Overview</h2>
            <p>The Services Manager API provides control over system services, Docker containers, and server management. It supports operations for Docker containers, Jellyfin media server, Icecast streaming servers, and TeamTalk voice servers.</p>

            <h2>Authentication</h2>
            <p>Most endpoints require authentication using the X-User header to identify the requesting user:</p>

            <div class="code-block">X-User: your-username</div>

            <div class="note">
                <strong>User Permissions:</strong> Admin users have full access to all operations. General users have read-only access and limited control over their own services.
            </div>

            <h2>Base Path</h2>
            <p>All Services Manager endpoints are prefixed with:</p>
            <div class="code-block">/api/services</div>

            <div class="section-category">🖥️ System Status</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/health</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Check if the Services Manager API is healthy.</p>
                    <p><strong>Authentication:</strong> None required</p>
                    <p><strong>Response Example:</strong></p>
                    <div class="code-block">{
  "service": "services-manager-api",
  "status": "healthy",
  "timestamp": "2025-10-03T14:00:00.000000"
}</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/system/status</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get comprehensive system status including load average, disk usage, and service states.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Response Example:</strong></p>
                    <div class="code-block">{
  "load_average": "up 2 days, 4:37, 1 user, load average: 1.23, 1.24, 1.12",
  "disk_usage": "Filesystem Size Used Avail Use% Mounted on...",
  "services": {
    "nginx": {"status": "active", "active": true},
    "mysql": {"status": "active", "active": true},
    "postgresql": {"status": "active", "active": true}
  },
  "timestamp": "2025-10-03T14:00:00.000000"
}</div>
                </div>
            </div>

            <div class="section-category">🐳 Docker Container Management</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/docker/containers/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List all Docker containers with detailed information.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Response:</strong> Array of container objects with ID, name, status, ports, and resource usage</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/docker/containers/&lt;name&gt;/stats</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get detailed statistics for a specific container.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>name</code> (path) - Container name or ID</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -H "X-User: admin" \
  "https://api.devinecreations.net/api/services/docker/containers/mattermost/stats"</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/docker/containers/&lt;name&gt;/logs</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Retrieve container logs.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>name</code> (path) - Container name or ID</li>
                        <li><code>tail</code> (query, optional) - Number of lines to retrieve (default: 100)</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/docker/containers/&lt;name&gt;/start</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Start a stopped container.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                    <div class="warning">
                        <strong>Admin Only:</strong> This operation requires administrator privileges.
                    </div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/docker/containers/&lt;name&gt;/stop</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Stop a running container.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/docker/containers/&lt;name&gt;/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart a container.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -X POST \
  -H "X-User: admin" \
  "https://api.devinecreations.net/api/services/docker/containers/mattermost/restart"</div>
                </div>
            </div>

            <div class="section-category">🎬 Jellyfin Media Server</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/jellyfin/status</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get Jellyfin server status.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Response:</strong> Server status, version, and uptime information</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/jellyfin/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart the Jellyfin media server.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                </div>
            </div>

            <div class="section-category">📻 Icecast Streaming Servers</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/icecast/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List all Icecast streaming server instances.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/icecast/&lt;user&gt;/status</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get status of user-specific Icecast server.</p>
                    <p><strong>Authentication:</strong> Recommended (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>user</code> (path) - Username owning the Icecast instance</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/icecast/&lt;user&gt;/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart user's Icecast server.</p>
                    <p><strong>Authentication:</strong> Required (admin or owner)</p>
                </div>
            </div>

            <div class="section-category">🎙️ TeamTalk Voice Servers</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/teamtalk/servers/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List all TeamTalk voice server instances.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/teamtalk/servers/&lt;name&gt;/status</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Get status of specific TeamTalk server.</p>
                    <p><strong>Authentication:</strong> Recommended</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>name</code> (path) - Server instance name</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/services/teamtalk/servers/&lt;name&gt;/logs</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Retrieve TeamTalk server logs.</p>
                    <p><strong>Authentication:</strong> Required (admin)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>name</code> (path) - Server instance name</li>
                        <li><code>lines</code> (query, optional) - Number of log lines (default: 50)</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/teamtalk/servers/&lt;name&gt;/start</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Start a TeamTalk server instance.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/teamtalk/servers/&lt;name&gt;/stop</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Stop a running TeamTalk server.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/teamtalk/servers/&lt;name&gt;/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart a TeamTalk server instance.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -X POST \
  -H "X-User: admin" \
  "https://api.devinecreations.net/api/services/teamtalk/servers/main/restart"</div>
                </div>
            </div>

            <div class="section-category">🔧 System Administration</div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/fix-permissions/&lt;username&gt;</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Fix file permissions for a user's home directory and web files.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>username</code> (path) - Username to fix permissions for</li>
                    </ul>
                    <div class="note">
                        <strong>Note:</strong> This operation may take several minutes for large directories.
                    </div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/fix-permissions/composr</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Fix permissions specifically for Composr CMS installations.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/services/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart the Services Manager API itself.</p>
                    <p><strong>Authentication:</strong> Required (admin only)</p>
                    <div class="warning">
                        <strong>Warning:</strong> This will briefly interrupt API service while restarting.
                    </div>
                </div>
            </div>

            <h2>User Permissions</h2>
            <p>The Services Manager API has two permission levels:</p>

            <h3>Admin Users</h3>
            <p>Full access to all operations including:</p>
            <ul>
                <li>Starting, stopping, and restarting services</li>
                <li>Fixing file permissions</li>
                <li>Managing Docker containers</li>
                <li>Accessing all user services</li>
            </ul>

            <h3>General Users</h3>
            <p>Limited access including:</p>
            <ul>
                <li>Read-only access to status endpoints</li>
                <li>Control over their own services (e.g., own Icecast server)</li>
                <li>Viewing system status and container lists</li>
            </ul>

            <h2>Error Responses</h2>
            <table>
                <thead>
                    <tr>
                        <th>Status Code</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>400</td>
                        <td>Bad Request - Missing or invalid parameters</td>
                    </tr>
                    <tr>
                        <td>403</td>
                        <td>Forbidden - Insufficient permissions for operation</td>
                    </tr>
                    <tr>
                        <td>404</td>
                        <td>Not Found - Service or container doesn't exist</td>
                    </tr>
                    <tr>
                        <td>500</td>
                        <td>Internal Server Error - Operation failed</td>
                    </tr>
                </tbody>
            </table>

            <h2>Best Practices</h2>
            <ul>
                <li>Always include the <code>X-User</code> header to ensure proper permission checking</li>
                <li>Check service status before attempting start/stop operations</li>
                <li>Use container logs to troubleshoot issues before restarting</li>
                <li>Monitor system resources when managing multiple services</li>
            </ul>

            <h2>Support</h2>
            <p>For permission escalation, service configuration, or technical support, contact your system administrator.</p>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <a href="/" class="back-link">← Back to API Dashboard</a>
        </div>
    </div>
</body>
</html>
