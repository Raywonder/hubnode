#!/bin/bash
#
# Start Claude Local Sync API
# Provides local endpoint for real-time bidirectional sync with CopyParty
#

cd /home/devinecr/apps/hubnode/api
source claude-sync-venv/bin/activate
nohup python3 claude-local-sync.py > /var/log/claude-sync.log 2>&1 &

echo "Claude Local Sync API started on port 3923"
echo "Health check: curl http://127.0.0.1:3923/health"
echo "Sync status: curl http://127.0.0.1:3923/sync/status"