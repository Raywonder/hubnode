# CopyParty UI Configuration

## Updated: Tue Sep 30 00:45:03 EDT 2025

### Server Details
- **Primary URL**: https://files.raywonderis.me
- **IP Fallback**: 64.20.46.178
- **Ports**: 3924 (primary), 3923 (secondary)

### Configuration Files
- `config/copyparty-server-config.json` - Universal server configuration
- `config/claude-memory-config.json` - Claude integration settings
- `config/app-settings.json` - App-specific preferences

### Admin Credentials
- **Username**: admin
- **Password**: hub-node-api-2024

### Quick Test
```bash
# Test connectivity
curl -s -I https://files.raywonderis.me/health

# Get user credentials
/home/claude-copyparty-helper.sh list

# Test admin access
curl -s -u admin:hub-node-api-2024 https://files.raywonderis.me/ | head -5
```

### Integration with Claude
This app can use Claude memory integration:
- Memory instructions: /home/CLAUDE_MEMORY_INSTRUCTIONS.md
- Connection protocol: /home/CLAUDE_CONNECTION_PROTOCOL.md
- Helper script: /home/claude-copyparty-helper.sh

### Troubleshooting
1. Check services: `systemctl status copyparty copyparty-3923`
2. Check ports: `netstat -tulnp | grep "392[34]"`
3. Test connectivity: `curl -s -I http://64.20.46.178:3924/`
