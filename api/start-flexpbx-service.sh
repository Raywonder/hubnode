#!/bin/bash
##
# FlexPBX Service Startup Script
# Starts the FlexPBX API service on port 5018
##

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SCRIPT="$SCRIPT_DIR/flexpbx-service.py"
VENV_DIR="$SCRIPT_DIR/gateway-venv"
PORT=5018
LOGFILE="/var/log/flexpbx-service.log"

echo "================================================"
echo "FlexPBX API Service Startup"
echo "================================================"
echo ""

# Check if service is already running
if pgrep -f "flexpbx-service.py" > /dev/null; then
    echo "✓ FlexPBX service is already running"
    echo ""
    echo "To restart the service:"
    echo "  pkill -f flexpbx-service.py && $0"
    echo ""
    exit 0
fi

# Activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q flask requests

# Start service
echo "Starting FlexPBX API service on port $PORT..."
export PORT=$PORT

nohup python3 "$SERVICE_SCRIPT" >> "$LOGFILE" 2>&1 &
SERVICE_PID=$!

echo "✓ FlexPBX service started (PID: $SERVICE_PID)"
echo ""
echo "Service Details:"
echo "  - Port: $PORT"
echo "  - Base URL: http://localhost:$PORT/flexpbx"
echo "  - Logs: $LOGFILE"
echo "  - Documentation: http://localhost:$PORT/docs"
echo ""
echo "Gateway Access:"
echo "  - External: https://api.devine-creations.com/flexpbx"
echo "  - Local: http://localhost:5015/flexpbx"
echo ""
echo "To stop the service:"
echo "  pkill -f flexpbx-service.py"
echo ""
