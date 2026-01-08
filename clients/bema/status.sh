#!/bin/bash
echo "Softnode Media Player Status:"
echo "============================="
sudo systemctl status softnode-media-player --no-pager
echo ""
echo "API Health Check:"
curl -s http://localhost:3001/health 2>/dev/null || echo "API not responding"
echo ""
echo "Process Info:"
ps aux | grep "node app.js" | grep -v grep || echo "Process not found"
echo ""
echo "Log Files:"
ls -la /var/log/softnode/ 2>/dev/null || echo "No log files found"
