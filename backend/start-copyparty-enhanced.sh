#!/bin/bash
# Enhanced CopyParty Hub Node Startup Script with Complete Upload Management
# Includes all Composr uploads, WordPress uploads, and file management directories

echo "Starting Enhanced CopyParty Hub Node with full upload integration..."

# Create necessary directories
mkdir -p uploads downloads temp logs data

# Start CopyParty with comprehensive multi-domain and upload path configuration
python3 copyparty-sfx.py \
    -i 0.0.0.0 \
    -p 3923 \
    --name "CopyParty Complete File Management System" \
    \
    `# === COMPOSR UPLOADS - Public Downloads ===` \
    -v /home/dom/public_html/uploads:/composr-raywonderis/uploads:rwm \
    -v /home/dom/public_html/uploads/website_specific:/composr-raywonderis/website_specific:rwm \
    -v /home/dom/public_html/uploads/website_specific/apps:/composr-raywonderis/website_specific/apps:rwm \
    -v /home/dom/public_html/uploads/website_specific/apps/audio-portrait:/composr-raywonderis/apps/audio-portrait:rwm \
    -v /home/dom/public_html/uploads/filedump:/composr-raywonderis/filedump:rwm \
    -v /home/dom/public_html/uploads/attachments:/composr-raywonderis/attachments:rwm \
    -v /home/dom/public_html/uploads/galleries:/composr-raywonderis/galleries:rwm \
    \
    -v /home/devinecr/devinecreations.net/uploads:/composr-devinecreations/uploads:rwm \
    -v /home/devinecr/devinecreations.net/uploads/website_specific:/composr-devinecreations/website_specific:rwm \
    -v /home/devinecr/devinecreations.net/uploads/filedump:/composr-devinecreations/filedump:rwm \
    -v /home/devinecr/devinecreations.net/uploads/attachments:/composr-devinecreations/attachments:rwm \
    -v /home/devinecr/devinecreations.net/uploads/galleries:/composr-devinecreations/galleries:rwm \
    -v /home/devinecr/devinecreations.net/uploads/website_specific/apps:/composr-devinecreations/website_specific/apps:rwm \
    -v /home/devinecr/devinecreations.net/uploads/website_specific/apps/audio-portrait:/composr-devinecreations/apps/audio-portrait:rwm \
    \
    `# === WHMCS FRONTEND (devinecr public_html) ===` \
    -v /home/devinecr/public_html:/whmcs-devinecr:rwm \
    \
    `# === WORDPRESS UPLOADS ===` \
    -v /home/tappedin/public_html/wp-content/uploads:/wp-tappedin/uploads:rwm \
    -v /home/tappedin/public_html/wp-content/uploads/podcast-submissions:/wp-tappedin/podcast-submissions:rwm \
    -v /home/tetoeehoward/public_html/wp-content/uploads:/wp-tetoeehoward/uploads:rwm \
    -v /home/wharper/public_html/wp-content/uploads:/wp-walterharper/uploads:rwm \
    \
    `# === APPLICATION DIRECTORIES ===` \
    -v /home/tappedin/apps:/apps-tappedin:rwm \
    -v /home/devinecr/apps:/apps-devinecr:rwm \
    -v /home/dom/apps:/apps-dom:rwm \
    \
    `# === HUBNODE PROJECT DIRECTORIES ===` \
    -v /home/devinecr/apps/hubnode/clients:/hubnode-clients:rwm \
    -v /home/devinecr/apps/hubnode/api:/hubnode-api:rwm \
    -v /home/devinecr/apps/hubnode/backend:/hubnode-backend:rwm \
    \
    `# === SPECIAL PROJECT UPLOADS ===` \
    -v /home/devinecr/apps/hubnode/api/audio-portrait/uploads:/audio-portrait-dist:rwm \
    -v /home/tappedin/apps/audio-portrait:/audio-portrait-dev:rwm \
    \
    `# === SHARED & COMMON DIRECTORIES ===` \
    -v /home/devinecr/shared:/shared:rwm \
    -v /home/devinecr/downloads:/downloads-devinecr:rwm \
    -v /home/devinecr/Downloads:/Downloads-devinecr:rwm \
    -v /home/devinecr/attachments:/attachments-devinecr:rwm \
    -v /home/devinecr/Attachments:/Attachments-devinecr:rwm \
    \
    `# === INCOMING/STAGING DIRECTORIES ===` \
    -v /home/dom/public_html/uploads/incoming:/incoming-raywonderis:rwm \
    -v /home/devinecr/devinecreations.net/uploads/incoming:/incoming-devinecreations:rwm \
    -v /home/tappedin/public_html/wp-content/uploads/incoming:/incoming-tappedin:rwm \
    \
    `# === ROOT ACCESS FOR ADMINS (Optional) ===` \
    -v /home/tappedin:/root-tappedin:rwm \
    -v /home/devinecr:/root-devinecr:rwm \
    -v /home/dom:/root-dom:rwm \
    -v /home/tetoeehoward:/root-tetoeehoward:rwm \
    -v /home/wharper:/root-wharper:rwm \
    \
    `# === USER AUTHENTICATION ===` \
    -a admin:hub-node-api-2024 \
    -a tappedin:tappedin-uploads-2024 \
    -a dom:composr-import-2024 \
    -a devinecr:devinecreat-files-2024 \
    -a tetoeehoward:tetoee-files-2024 \
    -a wharper:walter-files-2024 \
    -a audioportrait:audio-portrait-api-2025 \
    -a composer:composr-manage-2025 \
    -a wordpress:wp-manage-2025 \
    -a public:public-download-2025:r \
    \
    `# === CONFIGURATION OPTIONS ===` \
    --doctitle "CopyParty Complete File Management" \
    -lo ./logs/copyparty.txt \
    --hist 100 \
    --th-covers 1920x1080 \
    --ih \
    --no-robots \
    --dotpart \
    --hardlink \
    --stats \
    $@

echo "Enhanced CopyParty Hub Node stopped."