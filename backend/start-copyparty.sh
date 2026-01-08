#!/bin/bash
# CopyParty Hub Node Startup Script

echo "Starting CopyParty Hub Node..."

# Create directories
mkdir -p uploads downloads temp logs data

# Start CopyParty with multi-domain configuration
python3 copyparty-sfx.py \
    -i 0.0.0.0 \
    -p 3923 \
    -v ./uploads:/:rwm \
    -v /home/tappedin/public_html/wp-content/uploads/podcast-submissions:/tappedin:rwm \
    -v /home/dom/public_html/uploads/incoming:/raywonderis:rwm \
    -v /home/devinecr/downloads:/devine-creations-downloads:rwm \
    -v /home/devinecr/attachments:/devine-creations-attachments:rwm \
    -v /home/devinecr/devinecreations.net/uploads/incoming:/devinecreations:rwm \
    -v /home/tetoeehoward/public_html:/tetoeehoward:rwm \
    -v /home/wharper/public_html/wp-content/uploads:/walterharper:rwm \
    -v /home/devinecr/shared:/shared:rwm \
    -v /home/devinecr/apps/hubnode/api/audio-portrait/uploads:/audio-portrait:rwm \
    -v /home/tappedin/apps:/tappedin-apps:rwm \
    -v /home/devinecr/apps:/devinecr-apps:rwm \
    -v /home/dom/apps:/dom-apps:rwm \
    -a admin:hub-node-api-2024 \
    -a tappedin:tappedin-uploads-2024 \
    -a dom:composr-import-2024 \
    -a devinecr:devinecreat-files-2024 \
    -a tetoeehoward:tetoee-files-2024 \
    -a wharper:walter-files-2024 \
    -a audioportrait:audio-portrait-api-2025 \
    --name "CopyParty Multi-Domain File Manager" \
    -lo ./logs/copyparty.txt \
    --hist 100 \
    --th-covers 1920x1080 \
    --ih \
    --doctitle "CopyParty Multi-Domain File Manager" \
    $@

echo "CopyParty Hub Node stopped."
