<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HubNode API Management</title>
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
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }

        .card p {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }

        .endpoint-list {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }

        .endpoint {
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }

        .endpoint:last-child {
            border-bottom: none;
        }

        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 10px;
            min-width: 60px;
            text-align: center;
        }

        .method.get {
            background: #28a745;
            color: white;
        }

        .method.post {
            background: #007bff;
            color: white;
        }

        .method.put {
            background: #ffc107;
            color: #333;
        }

        .method.delete {
            background: #dc3545;
            color: white;
        }

        .path {
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #333;
        }

        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: background 0.3s ease;
        }

        .btn:hover {
            background: #5568d3;
        }

        .status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
        }

        .status.online {
            background: #d4edda;
            color: #155724;
        }

        .status.offline {
            background: #f8d7da;
            color: #721c24;
        }

        .api-key-info {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }

        .api-key-info strong {
            color: #856404;
        }

        .domain-info {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }

        .domain-info h3 {
            margin-bottom: 10px;
        }

        .domain-list {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .domain-badge {
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 HubNode API</h1>
            <p>Unified API Gateway for Service Management</p>
        </div>

        <?php
        // Get current domain
        $current_domain = $_SERVER['HTTP_HOST'];
        ?>

        <div class="domain-info">
            <h3>API Endpoint</h3>
            <div class="domain-list">
                <div class="domain-badge"><?php echo htmlspecialchars($current_domain); ?></div>
            </div>
        </div>

        <?php
        // Check API health
        $api_status = @file_get_contents('http://127.0.0.1:5015/health');
        $copyparty_status = @file_get_contents('http://127.0.0.1:5016/api/copyparty/health');
        $services_status = @file_get_contents('http://127.0.0.1:5017/api/services/health');
        ?>

        <div class="grid">
            <!-- Unified API Gateway -->
            <div class="card">
                <h2>🔗 Unified API Gateway</h2>
                <p>Main API gateway routing to all services</p>
                <div style="margin-bottom: 15px;">
                    Status: <span class="status <?php echo $api_status ? 'online' : 'offline'; ?>">
                        <?php echo $api_status ? 'Online' : 'Offline'; ?>
                    </span>
                </div>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/health</span>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/info</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/webhook/*</span>
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <a href="/api/info" class="btn" target="_blank">View API Info</a>
                </div>
            </div>

            <!-- CopyParty Admin API -->
            <div class="card">
                <h2>📁 CopyParty Admin</h2>
                <p>File management and sharing system with user-specific operations</p>
                <div style="margin-bottom: 15px;">
                    Status: <span class="status <?php echo $copyparty_status ? 'online' : 'offline'; ?>">
                        <?php echo $copyparty_status ? 'Online' : 'Offline'; ?>
                    </span>
                </div>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/upload</span>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/list</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/share/public</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/mkdir</span>
                    </div>
                </div>
                <div class="api-key-info">
                    <strong>⚠️ Authentication Required:</strong> X-API-Key header needed for all operations
                </div>
            </div>

            <!-- Services Manager API -->
            <div class="card">
                <h2>⚙️ Services Manager</h2>
                <p>System service control, Docker, and permission management</p>
                <div style="margin-bottom: 15px;">
                    Status: <span class="status <?php echo $services_status ? 'online' : 'offline'; ?>">
                        <?php echo $services_status ? 'Online' : 'Offline'; ?>
                    </span>
                </div>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/services/status</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/docker/&lt;action&gt;</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/fix-permissions/&lt;user&gt;</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/jellyfin/&lt;action&gt;</span>
                    </div>
                </div>
            </div>

            <!-- File Operations -->
            <div class="card">
                <h2>📤 File Operations</h2>
                <p>User-specific file and folder management</p>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/upload</span>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/download</span>
                    </div>
                    <div class="endpoint">
                        <span class="method put">PUT</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/update</span>
                    </div>
                    <div class="endpoint">
                        <span class="method delete">DELETE</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/delete</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/move</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/copy</span>
                    </div>
                </div>
                <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                    Replace &lt;user&gt; with your username in the endpoint paths
                </p>
            </div>

            <!-- Public Sharing -->
            <div class="card">
                <h2>🌐 Public Sharing</h2>
                <p>Create and manage public/private file shares with tokens</p>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/share/public</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/share/private</span>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/share/list</span>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/copyparty/share/&lt;token&gt;</span>
                    </div>
                    <div class="endpoint">
                        <span class="method delete">DELETE</span>
                        <span class="path">/api/copyparty/user/&lt;user&gt;/share/delete</span>
                    </div>
                </div>
                <p style="margin-top: 15px; color: #666; font-size: 0.9em;">
                    Public share links require no authentication and support expiration dates
                </p>
            </div>

            <!-- Docker Management -->
            <div class="card">
                <h2>🐳 Docker Management</h2>
                <p>Control Docker containers and services</p>
                <div class="endpoint-list">
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="path">/api/services/docker/status</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/docker/start</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/docker/stop</span>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="path">/api/services/docker/restart</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="card" style="background: rgba(255,255,255,0.95);">
            <h2>📚 API Documentation</h2>
            <p>For detailed API documentation, authentication methods, and examples:</p>
            <div style="margin-top: 20px;">
                <a href="/docs-copyparty.php" class="btn" target="_blank" style="margin-right: 10px;">CopyParty API Docs</a>
                <a href="/docs-services.php" class="btn" target="_blank" style="margin-right: 10px;">Services API Docs</a>
                <a href="/docs-gateway.php" class="btn" target="_blank">Gateway API Docs</a>
            </div>
        </div>

        <div style="text-align: center; color: white; margin-top: 40px; opacity: 0.8;">
            <p>HubNode API Gateway • Powered by Flask & Nginx</p>
        </div>
    </div>
</body>
</html>
