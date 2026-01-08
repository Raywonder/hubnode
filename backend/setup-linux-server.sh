#!/bin/bash
# CopyParty Hub Node - Linux Server Setup Script
# Deploy to: /home/devinecr/apps/hubnode/backend/

set -e

echo "=== CopyParty Hub Node Linux Server Setup ==="
echo "Setting up backend server at: $(pwd)"

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This script is designed for Linux servers"
fi

# Create required directories
echo "Creating directory structure..."
mkdir -p uploads downloads temp logs data
mkdir -p ../clients/copyparty

# Install Python and pip if not available
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Install CopyParty
echo "Installing CopyParty..."
python3 -m pip install --user -U copyparty

# Make scripts executable
chmod +x start-copyparty.sh
chmod +x copyparty-sfx.py
chmod +x api-examples.py

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/copyparty-hubnode.service > /dev/null <<EOF
[Unit]
Description=CopyParty Hub Node Server
After=network.target

[Service]
Type=simple
User=devinecr
WorkingDirectory=/home/devinecr/apps/hubnode/backend
ExecStart=/home/devinecr/apps/hubnode/backend/start-copyparty.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
sudo chown -R devinecr:devinecr /home/devinecr/apps/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable copyparty-hubnode
sudo systemctl start copyparty-hubnode

echo "=== Setup Complete ==="
echo "CopyParty Hub Node is running on: http://$(hostname -I | awk '{print $1}'):3923"
echo "Service status: sudo systemctl status copyparty-hubnode"
echo "View logs: sudo journalctl -u copyparty-hubnode -f"
echo "Stop service: sudo systemctl stop copyparty-hubnode"

# Test server connection
sleep 5
if curl -s http://localhost:3923 > /dev/null; then
    echo "✅ Server is responding on port 3923"
else
    echo "❌ Server may not be running correctly"
fi

echo "Setup script completed successfully!"