#!/bin/bash
# Start HubNode Unified API Gateway
# Auto-starts all dependent services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting HubNode Unified API Gateway..."

# Check if virtual environment exists
if [ ! -d "gateway-venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv gateway-venv
    source gateway-venv/bin/activate
    pip install flask flask-cors requests
else
    source gateway-venv/bin/activate
fi

# Start dependent services if not running
echo "Checking dependent services..."

# Service Monitor (port 5003)
if ! netstat -tln | grep -q ":5003 "; then
    echo "Starting Service Monitor API (port 5003)..."
    cd /home/devinecr/apps/hubnode/clients/api_monitor
    if [ -d "venv" ]; then
        source venv/bin/activate
        nohup python3 service_monitor.py > /tmp/service-monitor.log 2>&1 &
    fi
    cd "$SCRIPT_DIR"
fi

# User Logs Collector (port 5002)
if ! netstat -tln | grep -q ":5002 "; then
    echo "Starting User Logs Collector API (port 5002)..."
    nohup python3 "$SCRIPT_DIR/user-logs-collector.py" > /tmp/user-logs.log 2>&1 &
fi

# Audio Portrait API (port 5001)
if ! netstat -tln | grep -q ":5001 "; then
    echo "Starting Audio Portrait API (port 5001)..."
    cd "$SCRIPT_DIR/audio-portrait"
    if [ -d "venv" ]; then
        source venv/bin/activate
        nohup python3 app.py > /tmp/audio-portrait.log 2>&1 &
    fi
    cd "$SCRIPT_DIR"
fi

# Wait for services to start
sleep 2

# Start the gateway
echo "Starting API Gateway (port 5000)..."
source "$SCRIPT_DIR/gateway-venv/bin/activate"

# Check if already running
if netstat -tln | grep -q ":5000 "; then
    echo "Gateway already running on port 5000"
    PID=$(lsof -ti:5000)
    echo "Stopping existing gateway (PID: $PID)..."
    kill "$PID" 2>/dev/null
    sleep 1
fi

# Start gateway
nohup python3 "$SCRIPT_DIR/unified-gateway.py" > /var/log/api-gateway.log 2>&1 &
GATEWAY_PID=$!

echo ""
echo "✓ HubNode API Gateway started (PID: $GATEWAY_PID)"
echo ""
echo "Access URLs:"
echo "  - https://api.devinecreations.net"
echo "  - https://api.devine-creations.net"
echo "  - http://64.20.46.178:5000"
echo ""
echo "View logs: tail -f /var/log/api-gateway.log"
echo ""

# Display API keys
if [ -f "$SCRIPT_DIR/api_keys.json" ]; then
    echo "API Keys:"
    python3 -c "import json; keys=json.load(open('$SCRIPT_DIR/api_keys.json')); print('\n'.join([f'  {k}: {v[\"key\"]}' for k,v in keys.items()]))"
fi
