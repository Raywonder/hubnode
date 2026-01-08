#!/bin/bash
# Start Service Monitor API

API_DIR="/home/devinecr/apps/hubnode/clients/api_monitor"
cd "$API_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start the API
echo "Starting Service Monitor API on port 5003..."
nohup python3 service_monitor.py > api_monitor.log 2>&1 &

echo "Service Monitor API started"
echo "Access at: http://localhost:5003"
echo "Log file: $API_DIR/api_monitor.log"
