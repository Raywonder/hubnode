<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CopyParty API Documentation - HubNode</title>
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

        .method.put {
            background: #ffc107;
            color: #333;
        }

        .method.delete {
            background: #dc3545;
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
            <h1>📁 CopyParty API Documentation</h1>
            <p>File Management and Sharing System</p>
        </div>

        <div class="content">
            <h2>Overview</h2>
            <p>The CopyParty Admin API provides comprehensive file management capabilities including uploads, downloads, sharing, and directory management. All operations are user-scoped and support both public and private file sharing.</p>

            <h2>Authentication</h2>
            <p>All CopyParty API endpoints require authentication using an API key:</p>

            <div class="code-block">X-API-Key: your-api-key-here</div>

            <div class="warning">
                <strong>Security Notice:</strong> Never share your API key or commit it to version control. Each user has their own API key for accessing their files.
            </div>

            <h2>Base Path</h2>
            <p>All CopyParty endpoints are prefixed with:</p>
            <div class="code-block">/api/copyparty</div>

            <div class="section-category">🔍 System Information</div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/health</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Check the health status of CopyParty instances.</p>
                    <p><strong>Authentication:</strong> None required</p>
                    <p><strong>Response Example:</strong></p>
                    <div class="code-block">{
  "status": "healthy",
  "instances": {
    "admin": {
      "url": "http://localhost:3923",
      "status": "healthy"
    },
    "public": {
      "url": "http://localhost:3924",
      "status": "healthy"
    }
  },
  "timestamp": "2025-10-03T14:00:00.000000"
}</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/volumes/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List all available file volumes and their permissions.</p>
                    <p><strong>Authentication:</strong> Required</p>
                </div>
            </div>

            <div class="section-category">📤 File Operations</div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/upload</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Upload files to user's home directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (query) - Destination path relative to user's home</li>
                        <li><code>file</code> (form-data) - File to upload</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -X POST \
  -H "X-API-Key: your-key" \
  -F "file=@document.pdf" \
  "https://api.devinecreations.net/api/copyparty/user/yourname/upload?path=/documents"</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List files and directories in user's home.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (query) - Path to list (default: user's home)</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -H "X-API-Key: your-key" \
  "https://api.devinecreations.net/api/copyparty/user/yourname/list?path=/documents"</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/download</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Download a file from user's home directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (query, required) - Path to file relative to user's home</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -H "X-API-Key: your-key" \
  "https://api.devinecreations.net/api/copyparty/user/yourname/download?path=/documents/file.pdf" \
  -o file.pdf</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method delete">DELETE</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/delete</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Delete a file or directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (query, required) - Path to delete</li>
                    </ul>
                    <div class="warning">
                        <strong>Warning:</strong> This operation is permanent and cannot be undone.
                    </div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/mkdir</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Create a new directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (query, required) - Directory path to create</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/move</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Move or rename a file or directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>source</code> (JSON, required) - Source path</li>
                        <li><code>destination</code> (JSON, required) - Destination path</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -X POST \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"source": "/old-name.txt", "destination": "/new-name.txt"}' \
  "https://api.devinecreations.net/api/copyparty/user/yourname/move"</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/copy</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Copy a file or directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>source</code> (JSON, required) - Source path</li>
                        <li><code>destination</code> (JSON, required) - Destination path</li>
                    </ul>
                </div>
            </div>

            <div class="section-category">🌐 Sharing & Permissions</div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/share/public</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Create a public share link for a file or directory.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>path</code> (JSON, required) - Path to share</li>
                        <li><code>expiry_days</code> (JSON, optional) - Number of days until link expires</li>
                    </ul>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl -X POST \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"path": "/documents/report.pdf", "expiry_days": 7}' \
  "https://api.devinecreations.net/api/copyparty/user/yourname/share/public"</div>
                    <p><strong>Response Example:</strong></p>
                    <div class="code-block">{
  "share_url": "https://api.devinecreations.net/api/copyparty/share/abc123xyz",
  "token": "abc123xyz",
  "expires": "2025-10-10T14:00:00.000000"
}</div>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/share/private</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Create a private share link (requires authentication to access).</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong> Same as public share</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/share/list</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> List all active shares created by user.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method delete">DELETE</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/share/delete</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Delete/revoke a share link.</p>
                    <p><strong>Authentication:</strong> Required (user-specific)</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>token</code> (query, required) - Share token to revoke</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method get">GET</span>
                    <span class="path">/api/copyparty/share/&lt;token&gt;</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Access a public share (no authentication needed for public shares).</p>
                    <p><strong>Authentication:</strong> None for public shares, required for private shares</p>
                    <p><strong>Example:</strong></p>
                    <div class="code-block">curl "https://api.devinecreations.net/api/copyparty/share/abc123xyz"</div>
                </div>
            </div>

            <div class="section-category">🔧 Management & Admin</div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/user/&lt;username&gt;/fix-permissions</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Fix file permissions for user's home directory.</p>
                    <p><strong>Authentication:</strong> Required (admin)</p>
                    <p><strong>Note:</strong> This operation may take time for large directories.</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/admin/scan</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Trigger a rescan of all volumes.</p>
                    <p><strong>Authentication:</strong> Required (admin)</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method post">POST</span>
                    <span class="path">/api/copyparty/restart</span>
                </div>
                <div class="description">
                    <p><strong>Description:</strong> Restart the CopyParty Admin API service.</p>
                    <p><strong>Authentication:</strong> Required (admin)</p>
                </div>
            </div>

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
                        <td>Bad Request - Missing required parameters or invalid path</td>
                    </tr>
                    <tr>
                        <td>403</td>
                        <td>Forbidden - Path outside user's home directory or insufficient permissions</td>
                    </tr>
                    <tr>
                        <td>404</td>
                        <td>Not Found - File or directory doesn't exist</td>
                    </tr>
                    <tr>
                        <td>500</td>
                        <td>Internal Server Error - Operation failed on backend</td>
                    </tr>
                </tbody>
            </table>

            <h2>Path Resolution</h2>
            <p>All paths are relative to the user's home directory. For example, if your username is "john":</p>
            <ul>
                <li><code>/documents</code> resolves to <code>/home/john/documents</code></li>
                <li><code>/</code> refers to <code>/home/john</code></li>
                <li>Paths outside user home are rejected with 403 Forbidden</li>
            </ul>

            <div class="note">
                <strong>Tip:</strong> Use <code>/api/copyparty/volumes/list</code> to see which directories you have access to.
            </div>

            <h2>File Size Limits</h2>
            <p>File upload limits are configured server-side. Contact your administrator if you need to upload larger files.</p>

            <h2>Support</h2>
            <p>For API key requests, permission issues, or technical support, contact your system administrator.</p>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <a href="/" class="back-link">← Back to API Dashboard</a>
        </div>
    </div>
</body>
</html>
