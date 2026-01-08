#!/bin/bash

# PatchMate HubNode Integration Startup Script
# This script starts the PatchMate Hub Integration service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHMATE_DIR="/home/devinecr/apps/patchmate-deployment"

echo "🎵 Starting PatchMate Hub Integration..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to the integration directory
cd "$SCRIPT_DIR"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if PatchMate deployment exists
if [ ! -d "$PATCHMATE_DIR" ]; then
    echo "⚠️  PatchMate deployment directory not found at: $PATCHMATE_DIR"
    echo "   Please ensure PatchMate is properly extracted to the expected location."
fi

# Set environment variables
export NODE_ENV=${NODE_ENV:-production}
export PORT=${PORT:-3002}
export HUBNODE_ENDPOINT=${HUBNODE_ENDPOINT:-http://localhost:5001}
export API_MONITOR_ENDPOINT=${API_MONITOR_ENDPOINT:-http://localhost:3001}
export PATCHMATE_DATA_PATH=${PATCHMATE_DATA_PATH:-$PATCHMATE_DIR}

echo "🔧 Configuration:"
echo "   - Port: $PORT"
echo "   - HubNode Endpoint: $HUBNODE_ENDPOINT"
echo "   - API Monitor Endpoint: $API_MONITOR_ENDPOINT"
echo "   - PatchMate Data Path: $PATCHMATE_DATA_PATH"
echo ""

# Start the integration service
echo "🚀 Starting PatchMate Hub Integration service..."
node patchmate-integration.js