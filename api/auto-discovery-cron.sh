#!/bin/bash
# Cron job to auto-discover and update services periodically

LOG_FILE="/var/log/api-gateway-discovery.log"
DISCOVERY_SCRIPT="/home/devinecr/apps/hubnode/api/auto-discover-services.py"
LOAD_SCRIPT="/home/devinecr/apps/hubnode/api/load-discovered-services.sh"

echo "========================================" >> "$LOG_FILE"
echo "Auto-Discovery Run: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run discovery
python3 "$DISCOVERY_SCRIPT" >> "$LOG_FILE" 2>&1

# Load services if changes detected
if [ -f "/home/devinecr/apps/hubnode/api/discovered_services.json" ]; then
    # Check if file changed in last 5 minutes
    if [ $(find /home/devinecr/apps/hubnode/api/discovered_services.json -mmin -5 2>/dev/null | wc -l) -gt 0 ]; then
        echo "Changes detected, loading services..." >> "$LOG_FILE"
        bash "$LOAD_SCRIPT" >> "$LOG_FILE" 2>&1

        # Restart gateway
        echo "Restarting gateway..." >> "$LOG_FILE"
        systemctl restart api-gateway >> "$LOG_FILE" 2>&1

        echo "✓ Gateway updated and restarted" >> "$LOG_FILE"
    else
        echo "No changes detected" >> "$LOG_FILE"
    fi
fi

echo "" >> "$LOG_FILE"
