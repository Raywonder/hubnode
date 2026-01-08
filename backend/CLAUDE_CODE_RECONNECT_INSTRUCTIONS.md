# 🔄 Claude Code Local Reconnect Instructions

## ✅ CopyParty Migration Complete!

The server-side CopyParty migration to secure HTTPS domains is now complete. Here's what your local Claude Code needs to know:

## 🔧 Server Configuration Updated

### Port Changes:
- **CopyParty**: Now on port `3924` (was `3923`)
- **Claude Sync**: Still on port `3923`
- **Local Proxy**: Now on port `8081` (was `8080`, conflicted with Headscale)

### New Secure URLs:
- **files.raywonderis.me**: `https://files.raywonderis.me/`
- **files.devinecreations.net**: `https://files.devinecreations.net/`
- **files.tappedin.fm**: `https://files.tappedin.fm/`
- **files.tetoeehoward.com**: `https://files.tetoeehoward.com/`
- **files.walterharper.com**: `https://files.walterharper.com/`

## 🔗 Local Claude Connection

### Internal Access URLs:
- **Local Proxy**: `http://127.0.0.1:8081/` (no auth required)
- **Direct CopyParty**: `http://127.0.0.1:3924/` (auth required)
- **Claude Sync API**: `http://127.0.0.1:3923/` (sync status)

### WebDAV URLs for Local Mounting:
- **Local**: `http://127.0.0.1:8081/dav/`
- **External**: `https://files.raywonderis.me/dav/`

## 📋 What Changed for Local Claude:

1. **Path Resolver Updated**: Automatically uses new secure HTTPS URLs
2. **Local Proxy Port**: Changed from 8080 to 8081
3. **Domain-Specific SSL**: Each files.* subdomain has its own certificate
4. **No Port Numbers**: All external access uses standard HTTPS (443)

## 🔄 Auto-Reconnection:

Your local Claude Code should automatically:
- ✅ Use the updated path resolver configuration
- ✅ Connect to the new local proxy port (8081)
- ✅ Generate proper HTTPS URLs for files
- ✅ Map local paths to secure CopyParty paths

## 🧪 Test Connection:

To verify your local Claude connection:
```bash
# Test local proxy
curl http://127.0.0.1:8081/

# Test direct CopyParty
curl -u admin:hub-node-api-2024 http://127.0.0.1:3924/

# Test Claude sync status
curl http://127.0.0.1:3923/sync/status
```

## 📁 File Path Resolution:

Local files are now automatically mapped to secure URLs:
- `/home/dom/public_html/uploads/test.jpg` → `https://files.raywonderis.me/composr-raywonderis/uploads/test.jpg`
- `/home/devinecr/apps/hubnode/api/file.py` → `https://files.raywonderis.me/hubnode-api/file.py`
- `/home/tappedin/public_html/wp-content/uploads/audio.mp3` → `https://files.tappedin.fm/wp-tappedin/uploads/audio.mp3`

## ⚠️ Important Notes:

1. **No Action Required**: Your local Claude Code should reconnect automatically
2. **Port Numbers Removed**: All external URLs now use standard HTTPS (no :3923)
3. **SSL Certificates**: Each domain now has proper SSL validation
4. **Same Credentials**: All authentication remains unchanged

## 🛡️ Security Improvements:

- ✅ No exposed ports on external interface
- ✅ Valid SSL certificates for all domains
- ✅ Enhanced security headers (HSTS, etc.)
- ✅ Domain-based routing
- ✅ Large file upload support (2GB)

## 📞 Support:

If your local Claude Code doesn't reconnect automatically:
1. Check that it's using port 8081 for local proxy
2. Verify the path resolver configuration is updated
3. Test the connection URLs above

---
**Migration Date**: 2025-09-27 21:31 EDT  
**Status**: ✅ COMPLETE - Ready for Local Claude Reconnection