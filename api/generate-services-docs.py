#!/usr/bin/env python3
"""
Auto-generate Services Manager API documentation from services-manager.py
"""

import re
import ast
from datetime import datetime
from pathlib import Path

def parse_services_routes(api_file):
    """Parse services-manager.py to extract routes"""

    with open(api_file, 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    routes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            route_info = None
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr') and decorator.func.attr == 'route':
                        if decorator.args:
                            route_path = decorator.args[0].value if isinstance(decorator.args[0], ast.Constant) else None

                            methods = ['GET']
                            for keyword in decorator.keywords:
                                if keyword.arg == 'methods':
                                    if isinstance(keyword.value, ast.List):
                                        methods = [m.value for m in keyword.value.elts if isinstance(m, ast.Constant)]

                            route_info = {
                                'path': route_path,
                                'methods': methods,
                                'function': node.name,
                                'docstring': ast.get_docstring(node) or '',
                            }

            if route_info:
                docstring = route_info['docstring']
                if docstring:
                    lines = docstring.strip().split('\n')
                    if lines:
                        route_info['description'] = lines[0].strip()
                routes.append(route_info)

    return routes

def generate_html(routes, output_file):
    """Generate HTML documentation"""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Services Manager API Documentation</title>
    <meta http-equiv="refresh" content="300">
    <link rel="stylesheet" href="/static/docs-style.css">
</head>
<body>
    <div class="container">
        <a href="/" class="back-btn">← Back to API Dashboard</a>

        <div class="header">
            <h1>⚙️ Services Manager API</h1>
            <p>Auto-generated API Reference</p>
        </div>

        <div class="update-info">
            🔄 Last updated: {timestamp} UTC<br>
            Auto-refreshes every 5 minutes • Updates every 1 minute
        </div>

        <div class="card">
            <h2>Base URLs</h2>
            <ul style="margin-left: 20px; color: #666;">
                <li><code>https://api.devinecreations.net/api/services</code></li>
                <li><code>https://api.devine-creations.com/api/services</code></li>
                <li><code>https://api.tetoeehoward.com/api/services</code></li>
                <li><code>https://api.tappedin.fm/api/services</code></li>
            </ul>

            <h2>System Service Control</h2>
            <p>Docker container management, Jellyfin, Icecast, TeamTalk servers, and permission fixes.</p>
        </div>

        <div class="card">
            <h2>Available Endpoints</h2>
'''

    for route in sorted(routes, key=lambda x: x['path']):
        methods_html = ' '.join([f'<span class="method {m.lower()}">{m}</span>' for m in route['methods']])

        html += f'''
            <div class="endpoint">
                <div>
                    {methods_html}
                    <span class="path">{route['path']}</span>
                </div>
'''

        if route.get('description'):
            html += f'''
                <div class="description">
                    <strong>Description:</strong> {route['description']}
                </div>
'''

        html += '''
            </div>
'''

    html += '''
        </div>

        <div style="text-align: center; color: white; margin-top: 40px; opacity: 0.8;">
            <p>Auto-generated from services-manager.py</p>
        </div>
    </div>
</body>
</html>
'''

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"Services docs generated: {output_file}")
    print(f"Timestamp: {timestamp}")
    print(f"Total endpoints: {len(routes)}")

if __name__ == '__main__':
    script_dir = Path(__file__).parent
    api_file = script_dir / 'services-manager.py'
    output_file = script_dir / 'docs-services-auto.html'

    routes = parse_services_routes(api_file)
    generate_html(routes, output_file)
