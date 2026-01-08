#!/bin/bash
# Auto-load discovered services into gateway

GATEWAY_FILE="/home/devinecr/apps/hubnode/api/unified-gateway.py"
DISCOVERED_CONFIG="/home/devinecr/apps/hubnode/api/discovered_services.json"
BACKUP_DIR="/home/devinecr/apps/hubnode/api/backups"

echo "============================================================"
echo "Loading Discovered Services into Gateway"
echo "============================================================"

# Create backup
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/unified-gateway.$(date +%Y%m%d_%H%M%S).py.bak"
cp "$GATEWAY_FILE" "$BACKUP_FILE"
echo "✓ Backup created: $BACKUP_FILE"

# Check if discovered services exist
if [ ! -f "$DISCOVERED_CONFIG" ]; then
    echo "✗ No discovered services found. Run auto-discover-services.py first."
    exit 1
fi

# Read discovered services
SERVICES=$(python3 -c "
import json
with open('$DISCOVERED_CONFIG', 'r') as f:
    config = json.load(f)
    for key, service in config['services'].items():
        print(f'{key}|{service[\"name\"]}|{service[\"url\"]}|{service[\"prefix\"]}|{service[\"health_endpoint\"]}|{service[\"description\"]}')
")

if [ -z "$SERVICES" ]; then
    echo "✗ No services to load"
    exit 1
fi

# Generate Python code for services
SERVICES_CODE="
# Auto-discovered services - Generated $(date)
DISCOVERED_SERVICES = {
"

while IFS='|' read -r key name url prefix health desc; do
    SERVICES_CODE+="    \"$key\": {
        \"name\": \"$name\",
        \"url\": \"$url\",
        \"prefix\": \"$prefix\",
        \"health_endpoint\": \"$health\",
        \"description\": \"$desc\"
    },
"
done <<< "$SERVICES"

SERVICES_CODE+="
}

# Merge with existing services
SERVICES.update(DISCOVERED_SERVICES)
"

# Add to gateway file (after SERVICES definition)
if grep -q "DISCOVERED_SERVICES" "$GATEWAY_FILE"; then
    echo "✓ Discovered services already loaded, updating..."
    # Remove old discovered services section
    sed -i '/# Auto-discovered services/,/SERVICES.update(DISCOVERED_SERVICES)/d' "$GATEWAY_FILE"
fi

# Find line after SERVICES dict ends
LINE=$(grep -n "^SERVICES = {" "$GATEWAY_FILE" | head -1 | cut -d: -f1)
if [ -z "$LINE" ]; then
    echo "✗ Could not find SERVICES definition in gateway"
    exit 1
fi

# Find the closing brace
END_LINE=$(tail -n +$LINE "$GATEWAY_FILE" | grep -n "^}" | head -1 | cut -d: -f1)
INSERT_LINE=$((LINE + END_LINE))

# Insert discovered services after SERVICES dict
sed -i "${INSERT_LINE}a\\
$SERVICES_CODE
" "$GATEWAY_FILE"

echo "✓ Discovered services loaded into gateway"
echo ""
echo "Services added:"
echo "$SERVICES" | while IFS='|' read -r key name url prefix health desc; do
    echo "  - $name ($url) -> $prefix"
done

echo ""
echo "============================================================"
echo "Restart gateway to apply changes:"
echo "  systemctl restart api-gateway"
echo "============================================================"
