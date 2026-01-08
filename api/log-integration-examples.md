# User Log Collection Integration Guide

This document shows how to integrate log collection into app installers and applications.

## API Endpoints

**Base URL**: `https://api.devinecreations.net/`

### Submit Log Files
```
POST /api/logs/submit
Content-Type: multipart/form-data

Parameters:
- app_name (required): Name of the application
- app_version: Version of the application  
- user_id: Anonymous user identifier
- log_type: Type of log (crash, error, debug, install, etc.)
- system_info: JSON string with system information
- log_file: Log file to upload (max 10MB)
- log_data: Text log data (alternative to file)
```

### Log Usage Events
```
POST /api/stats/event
Content-Type: application/json

Body:
{
  "app_name": "Audio Portrait",
  "app_version": "0.2.0", 
  "event_type": "app_start",
  "event_data": {
    "platform": "windows",
    "first_run": false
  },
  "user_id": "anon_12345"
}
```

## Integration Examples

### JavaScript (Electron Apps)
```javascript
// Log collection module
class LogCollector {
    constructor(appName, appVersion) {
        this.appName = appName;
        this.appVersion = appVersion;
        this.apiBase = 'https://api.devinecreations.net';
        this.userId = this.getOrCreateUserId();
    }
    
    getOrCreateUserId() {
        // Get or create anonymous user ID
        const stored = localStorage.getItem('user_id');
        if (stored) return stored;
        
        const userId = 'anon_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
        return userId;
    }
    
    async submitLog(logType, logData) {
        try {
            const formData = new FormData();
            formData.append('app_name', this.appName);
            formData.append('app_version', this.appVersion);
            formData.append('user_id', this.userId);
            formData.append('log_type', logType);
            formData.append('log_data', logData);
            formData.append('system_info', JSON.stringify({
                platform: process.platform,
                arch: process.arch,
                node_version: process.version
            }));
            
            const response = await fetch(`${this.apiBase}/api/logs/submit`, {
                method: 'POST',
                body: formData
            });
            
            return await response.json();
        } catch (error) {
            console.error('Failed to submit log:', error);
        }
    }
    
    async logEvent(eventType, eventData = {}) {
        try {
            const response = await fetch(`${this.apiBase}/api/stats/event`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    app_name: this.appName,
                    app_version: this.appVersion,
                    event_type: eventType,
                    event_data: eventData,
                    user_id: this.userId
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Failed to log event:', error);
        }
    }
}

// Usage in app
const logger = new LogCollector('Audio Portrait', '0.2.0');

// Log app start
logger.logEvent('app_start', {
    platform: process.platform,
    first_run: !localStorage.getItem('has_run_before')
});

// Log errors
process.on('uncaughtException', (error) => {
    logger.submitLog('crash', error.stack);
});

// Log feature usage
document.getElementById('export-button').addEventListener('click', () => {
    logger.logEvent('feature_used', {feature: 'export'});
});
```

### Python (Desktop Apps)
```python
import requests
import json
import uuid
import platform
import os

class LogCollector:
    def __init__(self, app_name, app_version):
        self.app_name = app_name
        self.app_version = app_version
        self.api_base = 'https://api.devinecreations.net'
        self.user_id = self._get_user_id()
    
    def _get_user_id(self):
        # Try to get existing user ID
        config_file = os.path.expanduser('~/.app_user_id')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return f.read().strip()
        
        # Create new anonymous ID
        user_id = f"anon_{uuid.uuid4().hex[:8]}"
        with open(config_file, 'w') as f:
            f.write(user_id)
        return user_id
    
    def submit_log(self, log_type, log_data):
        try:
            data = {
                'app_name': self.app_name,
                'app_version': self.app_version,
                'user_id': self.user_id,
                'log_type': log_type,
                'log_data': log_data,
                'system_info': json.dumps({
                    'platform': platform.system(),
                    'version': platform.version(),
                    'architecture': platform.architecture()[0]
                })
            }
            
            response = requests.post(f'{self.api_base}/api/logs/submit', data=data)
            return response.json()
        except Exception as e:
            print(f"Failed to submit log: {e}")
    
    def log_event(self, event_type, event_data=None):
        try:
            data = {
                'app_name': self.app_name,
                'app_version': self.app_version,
                'event_type': event_type,
                'event_data': event_data or {},
                'user_id': self.user_id
            }
            
            response = requests.post(
                f'{self.api_base}/api/stats/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            print(f"Failed to log event: {e}")

# Usage
logger = LogCollector('PatchMate', '1.0.0')

# Log app start
logger.log_event('app_start', {
    'platform': platform.system(),
    'python_version': platform.python_version()
})

# Log errors
import sys
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.submit_log('crash', ''.join(traceback.format_exception(
        exc_type, exc_value, exc_traceback
    )))

sys.excepthook = handle_exception
```

### Windows Installer (NSIS)
```nsis
; Log installation events
Function SendInstallLog
    ; Create temporary log file
    FileOpen $0 "$TEMP\install_log.txt" w
    FileWrite $0 "Installation started$\r$\n"
    FileWrite $0 "Version: ${APP_VERSION}$\r$\n"
    FileWrite $0 "Target: $INSTDIR$\r$\n"
    FileWrite $0 "User: $USERNAME$\r$\n"
    FileClose $0
    
    ; Send log via curl (if available)
    ExecWait 'curl -X POST -F "app_name=${APP_NAME}" -F "app_version=${APP_VERSION}" -F "log_type=install" -F "log_file=@$TEMP\install_log.txt" https://api.devinecreations.net/api/logs/submit'
    
    ; Clean up
    Delete "$TEMP\install_log.txt"
FunctionEnd

; Call during installation
Section "MainSection"
    ; ... installation code ...
    Call SendInstallLog
SectionEnd
```

### macOS Installer (Shell Script)
```bash
#!/bin/bash
# App installer with logging

APP_NAME="Audio Portrait"
APP_VERSION="0.2.0"
API_BASE="https://api.devinecreations.net"

# Generate anonymous user ID
USER_ID_FILE="$HOME/.app_user_id"
if [ ! -f "$USER_ID_FILE" ]; then
    echo "anon_$(openssl rand -hex 4)" > "$USER_ID_FILE"
fi
USER_ID=$(cat "$USER_ID_FILE")

# Log installation start
curl -X POST "$API_BASE/api/stats/event" \
    -H "Content-Type: application/json" \
    -d "{
        \"app_name\": \"$APP_NAME\",
        \"app_version\": \"$APP_VERSION\", 
        \"event_type\": \"install_start\",
        \"event_data\": {
            \"platform\": \"$(uname)\",
            \"arch\": \"$(uname -m)\"
        },
        \"user_id\": \"$USER_ID\"
    }"

# ... installation logic ...

# Log successful installation
curl -X POST "$API_BASE/api/stats/event" \
    -H "Content-Type: application/json" \
    -d "{
        \"app_name\": \"$APP_NAME\",
        \"app_version\": \"$APP_VERSION\",
        \"event_type\": \"install_complete\", 
        \"user_id\": \"$USER_ID\"
    }"
```

## Privacy Considerations

1. **Anonymous by Default**: All logging uses anonymous user IDs
2. **No Personal Data**: System info only includes platform/architecture
3. **Opt-out Mechanism**: Users can disable logging via settings
4. **Local Storage**: User preferences stored locally only
5. **Minimal Data**: Only essential debugging information collected

## Event Types to Track

### Installation Events
- `install_start`: Installation began
- `install_complete`: Installation finished successfully
- `install_error`: Installation failed
- `uninstall`: App was uninstalled

### Usage Events  
- `app_start`: Application launched
- `app_exit`: Application closed
- `feature_used`: Specific feature utilized
- `error_occurred`: Non-fatal error happened
- `performance_metric`: Timing or performance data

### Crash Events
- `crash`: Application crashed
- `hang`: Application became unresponsive
- `exception`: Unhandled exception occurred

This system helps developers understand how their applications are being used and identify issues in the wild while respecting user privacy.