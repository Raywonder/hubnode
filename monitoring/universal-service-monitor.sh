#!/bin/bash
#################################################################
# Universal Service Monitor - Auto-starts all critical services
# Monitors systemd services, custom apps, and Docker containers
#################################################################

LOG_FILE="/var/log/universal-service-monitor.log"
MAX_LOG_LINES=1000

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"

    # Keep log file size manageable
    if [ $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_LINES ]; then
        tail -n 500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

# Function to check systemd service
check_systemd_service() {
    local service=$1
    systemctl is-active --quiet "$service" && return 0 || return 1
}

# Function to start systemd service
start_systemd_service() {
    local service=$1
    log_message "⚠️  $service is down, attempting to start..."

    if systemctl start "$service"; then
        sleep 2
        if check_systemd_service "$service"; then
            log_message "✅ $service started successfully"
            return 0
        else
            log_message "❌ $service failed to start"
            return 1
        fi
    else
        log_message "❌ Failed to start $service"
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local process_name=$2
    netstat -tlnp 2>/dev/null | grep -q ":${port}.*${process_name}" && return 0 || return 1
}

# Function to start custom service
start_custom_service() {
    local name=$1
    local start_script=$2

    log_message "⚠️  $name is down, attempting to start..."

    if [ -f "$start_script" ] && [ -x "$start_script" ]; then
        nohup bash "$start_script" > "/var/log/${name}.log" 2>&1 &
        sleep 3
        log_message "✅ $name start command issued"
        return 0
    else
        log_message "❌ Start script not found or not executable: $start_script"
        return 1
    fi
}

#################################################################
# Main Monitoring Logic
#################################################################

log_message "=========================================="
log_message "Starting universal service monitor check"

SERVICES_CHECKED=0
SERVICES_STARTED=0
SERVICES_FAILED=0

#################################################################
# 1. SYSTEMD SERVICES
#################################################################

SYSTEMD_SERVICES=(
    "httpd"
    "nginx"
    "mariadb"
    "php-fpm"
    "ea-php81-php-fpm"
    "docker"
    "lfd"
    "sshd"
)

log_message "--- Checking systemd services ---"

for service in "${SYSTEMD_SERVICES[@]}"; do
    ((SERVICES_CHECKED++))

    if ! check_systemd_service "$service"; then
        if start_systemd_service "$service"; then
            ((SERVICES_STARTED++))
        else
            ((SERVICES_FAILED++))
        fi
    # Only log if quiet mode is off
    # else
    #     log_message "✓ $service is running"
    fi
done

#################################################################
# 2. COPYPARTY SERVERS (Ports 3923, 3924)
#################################################################

log_message "--- Checking CopyParty servers ---"

# Port 3923
((SERVICES_CHECKED++))
if ! check_port 3923 "python3"; then
    log_message "⚠️  CopyParty port 3923 is down, attempting to start..."
    if [ -f "/home/devinecr/scripts/start-copyparty-3923.sh" ]; then
        nohup /home/devinecr/scripts/start-copyparty-3923.sh > /var/log/copyparty-3923.log 2>&1 &
        sleep 2
        if check_port 3923 "python3"; then
            log_message "✅ CopyParty port 3923 started successfully"
            ((SERVICES_STARTED++))
        else
            log_message "❌ CopyParty port 3923 failed to start"
            ((SERVICES_FAILED++))
        fi
    else
        log_message "❌ Start script not found for CopyParty 3923"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ CopyParty port 3923 is running"
fi

# Port 3924
((SERVICES_CHECKED++))
if ! check_port 3924 "python3"; then
    log_message "⚠️  CopyParty port 3924 is down, attempting to start..."
    if [ -f "/home/devinecr/scripts/start-copyparty-3924.sh" ]; then
        nohup /home/devinecr/scripts/start-copyparty-3924.sh > /var/log/copyparty.log 2>&1 &
        sleep 2
        if check_port 3924 "python3"; then
            log_message "✅ CopyParty port 3924 started successfully"
            ((SERVICES_STARTED++))
        else
            log_message "❌ CopyParty port 3924 failed to start"
            ((SERVICES_FAILED++))
        fi
    else
        log_message "❌ Start script not found for CopyParty 3924"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ CopyParty port 3924 is running"
fi

#################################################################
# 3. AUDIO PORTRAIT API (Port 5001)
#################################################################

log_message "--- Checking Audio Portrait API ---"
((SERVICES_CHECKED++))

if ! check_port 5001 "python"; then
    log_message "⚠️  Audio Portrait API (port 5001) is down, attempting to start..."

    API_DIR="/home/devinecr/apps/hubnode/api/audio-portrait"
    if [ -d "$API_DIR" ] && [ -f "$API_DIR/app.py" ]; then
        cd "$API_DIR"
        if [ -d "venv" ]; then
            nohup ./venv/bin/python app.py > api.log 2>&1 &
            sleep 2
            if check_port 5001 "python"; then
                log_message "✅ Audio Portrait API started successfully"
                ((SERVICES_STARTED++))
            else
                log_message "❌ Audio Portrait API failed to start"
                ((SERVICES_FAILED++))
            fi
        else
            log_message "❌ Audio Portrait API venv not found"
            ((SERVICES_FAILED++))
        fi
    else
        log_message "❌ Audio Portrait API directory/files not found"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ Audio Portrait API (port 5001) is running"
fi

#################################################################
# 4. SERVICE MONITOR API (Port 5002)
#################################################################

log_message "--- Checking Service Monitor API ---"
((SERVICES_CHECKED++))

if ! check_port 5002 "python"; then
    log_message "⚠️  Service Monitor API (port 5002) is down, attempting to start..."

    API_DIR="/home/devinecr/apps/hubnode/clients/api_monitor"
    if [ -f "$API_DIR/start_monitor.sh" ]; then
        bash "$API_DIR/start_monitor.sh" > /dev/null 2>&1
        sleep 2
        if check_port 5002 "python"; then
            log_message "✅ Service Monitor API started successfully"
            ((SERVICES_STARTED++))
        else
            log_message "❌ Service Monitor API failed to start"
            ((SERVICES_FAILED++))
        fi
    else
        log_message "❌ Service Monitor API start script not found"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ Service Monitor API (port 5002) is running"
fi

#################################################################
# 5. HEADSCALE VPN SERVER (Port 8080)
#################################################################

log_message "--- Checking Headscale VPN Server ---"
((SERVICES_CHECKED++))

if ! pgrep -f "headscale serve" > /dev/null; then
    log_message "⚠️  Headscale server is down, attempting to start..."

    # Check if headscale binary exists
    if [ -f "/usr/local/bin/headscale" ]; then
        # Start headscale as systemd service if available
        if systemctl list-unit-files | grep -q "headscale.service"; then
            systemctl start headscale
            sleep 2
            if pgrep -f "headscale serve" > /dev/null; then
                log_message "✅ Headscale started successfully via systemd"
                ((SERVICES_STARTED++))
            else
                log_message "❌ Headscale failed to start"
                ((SERVICES_FAILED++))
            fi
        else
            # Start manually if no systemd service
            nohup /usr/local/bin/headscale serve > /var/log/headscale.log 2>&1 &
            sleep 2
            if pgrep -f "headscale serve" > /dev/null; then
                log_message "✅ Headscale started successfully"
                ((SERVICES_STARTED++))
            else
                log_message "❌ Headscale failed to start"
                ((SERVICES_FAILED++))
            fi
        fi
    else
        log_message "❌ Headscale binary not found at /usr/local/bin/headscale"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ Headscale VPN server is running"
    # Check if headscale API is responding (only warn on failure)
    if ! curl -s http://localhost:8080/metrics > /dev/null 2>&1; then
        log_message "⚠️  Headscale process running but API not responding"
    fi
# fi
fi

#################################################################
# 6. TAILSCALE WEB UI (Nginx serving dashboards)
#################################################################

log_message "--- Checking Tailscale Web UI ---"
((SERVICES_CHECKED++))

# Check if nginx is serving the Tailscale UI (only warn on failure)
if ! curl -sk https://localhost/api/status -H "Host: ui.tailscale.tappedin.fm" > /dev/null 2>&1; then
    log_message "⚠️  Tailscale Web UI may not be accessible"
    # No auto-fix - nginx should already be monitored above
fi

# Verify database exists (only warn if missing)
if [ ! -f "/home/devinecr/shared/vpn-settings.db" ]; then
    log_message "⚠️  VPN settings database not found, creating..."
    touch /home/devinecr/shared/vpn-settings.db
    chmod 664 /home/devinecr/shared/vpn-settings.db
    chown devinecr:nobody /home/devinecr/shared/vpn-settings.db
    log_message "✅ VPN settings database created"
fi

#################################################################
# 7. TAILSCALE EXIT NODE NAT
#################################################################

log_message "--- Checking Tailscale Exit Node Configuration ---"
((SERVICES_CHECKED++))

# Check IP forwarding
if [ "$(sysctl -n net.ipv4.ip_forward)" != "1" ]; then
    log_message "⚠️  IP forwarding disabled, enabling..."
    sysctl -w net.ipv4.ip_forward=1 > /dev/null
    log_message "✅ IP forwarding enabled"
    ((SERVICES_STARTED++))
# else
#     log_message "✓ IP forwarding is enabled"
fi

# Check NAT rules exist (only warn if missing)
if ! iptables -t nat -L POSTROUTING -n | grep -q "100.64.0.0/24"; then
    log_message "⚠️  Tailscale NAT rules missing, configuring..."
    if [ -f "/usr/local/bin/setup-exit-node.sh" ]; then
        /usr/local/bin/setup-exit-node.sh > /dev/null 2>&1
        log_message "✅ Exit node NAT configured"
        ((SERVICES_STARTED++))
    else
        log_message "⚠️  Exit node setup script not found"
    fi
fi

#################################################################
# 8. CSF FIREWALL
#################################################################

log_message "--- Checking CSF Firewall ---"
((SERVICES_CHECKED++))

if ! pgrep -f "lfd - sleeping" > /dev/null; then
    log_message "⚠️  CSF/LFD firewall is down, attempting to start..."
    csf -s > /dev/null 2>&1
    sleep 2
    if pgrep -f "lfd - sleeping" > /dev/null; then
        log_message "✅ CSF/LFD firewall started successfully"
        ((SERVICES_STARTED++))
    else
        log_message "❌ CSF/LFD firewall failed to start"
        ((SERVICES_FAILED++))
    fi
# else
#     log_message "✓ CSF/LFD firewall is running"
fi

#################################################################
# Summary
#################################################################

log_message "--- Monitor Check Summary ---"
log_message "Services Checked: $SERVICES_CHECKED"
log_message "Services Started: $SERVICES_STARTED"
log_message "Services Failed: $SERVICES_FAILED"
log_message "Universal service monitor check complete"
log_message "=========================================="
