# Audio Portrait App SSH Configuration

## SSH Public Key Access Setup

### For Client Applications:

1. **Generate SSH Key Pair** (on client machine):
```bash
ssh-keygen -t ed25519 -C "audio-portrait-client" -f ~/.ssh/audio_portrait_key
```

2. **Copy Public Key** to server:
```bash
ssh-copy-id -i ~/.ssh/audio_portrait_key.pub devinecr@64.20.46.178
```

### Server Configuration:

The audio-portrait app can access files via:
- **CopyParty Interface**: https://files.devinecreations.net/audio-portrait/
- **Direct SSH**: `devinecr@64.20.46.178:/home/devinecr/apps/hubnode/api/audio-portrait/uploads/`
- **API Upload**: POST to `/api/audio-portrait/upload`

### Authentication Details:

- **CopyParty Username**: `audioportrait`
- **CopyParty Password**: `audio-portrait-api-2025`
- **SSH User**: `devinecr`
- **Upload Directory**: `/home/devinecr/apps/hubnode/api/audio-portrait/uploads/`

### Client Integration Example:

```python
import requests

# Upload file via API
def upload_file(file_path):
    url = "https://api.devinecreations.net/api/audio-portrait/upload"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    return response.json()

# Check for updates
def check_updates(current_version, platform):
    url = f"https://api.devinecreations.net/api/audio-portrait/version"
    params = {
        'client_version': current_version,
        'platform': platform
    }
    response = requests.get(url, params=params)
    return response.json()
```

### Security Notes:

- SSH keys should be stored securely on client machines
- CopyParty access is limited to the `/audio-portrait/` directory
- All uploads are logged with timestamps and file hashes
- API endpoints include CORS support for web-based clients