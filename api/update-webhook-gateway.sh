#!/bin/bash
# Auto-update webhook manager in gateway service registry
# This script ensures the gateway always knows about the webhook service

GATEWAY_FILE="/home/devinecr/apps/hubnode/api/unified-gateway.py"

# Check if webhook service exists in gateway
if ! grep -q '"webhooks"' "$GATEWAY_FILE"; then
    echo "Adding webhook service to gateway..."

    # Create backup
    cp "$GATEWAY_FILE" "${GATEWAY_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

    # Add webhook service to SERVICES dict
    sed -i '/"copyparty-admin": {/i\    "webhooks": {\n        "name": "Webhook Manager",\n        "url": "http://localhost:5004",\n        "prefix": "/webhook",\n        "health_endpoint": "/health",\n        "description": "Webhook and external API integration"\n    },' "$GATEWAY_FILE"

    # Add route for webhook service
    cat >> "$GATEWAY_FILE" << 'EOF'

@app.route('/webhook', defaults={'path': ''})
@app.route('/webhook/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_webhooks(path):
    """Route to webhook manager"""
    return proxy_request(SERVICES["webhooks"], '/' + path if path else '/webhook/' + path)
EOF

    echo "✓ Webhook service added to gateway"
    echo "  Restart gateway to apply changes: systemctl restart api-gateway"
else
    echo "Webhook service already registered in gateway"
fi
