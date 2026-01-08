# CopyParty Backend Hub Node

A powerful file server backend with upload/download capabilities, API integration, and hub-node functionality for distributed file operations.

## Features

### Core Functionality
- ✅ **File Upload/Download** - Resumable uploads with no size limits
- ✅ **RESTful API** - Complete API for automation and integration
- ✅ **WebDAV Support** - Standard file protocol support
- ✅ **Search & Indexing** - Fast file search capabilities
- ✅ **Thumbnail Generation** - Automatic media previews
- ✅ **Cross-Platform** - Works on Windows, Linux, macOS

### Hub Node Features
- ✅ **Cluster Mode** - Multi-node file distribution
- ✅ **Copy/Paste Integration** - Seamless clipboard operations
- ✅ **API Authentication** - Secure API access with keys
- ✅ **Docker Support** - Container deployment ready
- ✅ **Logging & Monitoring** - Comprehensive activity logs

## Quick Start

### Local Development
```bash
# Start the server
./start-copyparty.sh

# Test API functionality
python3 api-examples.py
```

### Docker Deployment (Linux)
```bash
# Build and start container
docker-compose up -d

# View logs
docker-compose logs -f copyparty-hub
```

## API Endpoints

### File Operations
- `POST /api/upload` - Upload files
- `GET /api/download/{path}` - Download files
- `GET /api/list` - List directory contents
- `DELETE /api/delete/{path}` - Delete files

### Hub Node Operations
- `GET /api/status` - Node health and statistics
- `POST /api/sync` - Sync with other nodes
- `GET /api/cluster` - Cluster status

### Copy/Paste Integration
- `POST /api/paste` - Upload clipboard content
- `GET /api/copy/{path}` - Copy file to clipboard
- `GET /api/clipboard` - Get clipboard status

## Configuration

Server runs on `http://localhost:3923` by default.

### Authentication
```python
API_KEY = "hub-node-api-2024"
# Include in requests: {"api_key": API_KEY}
```

### Directory Structure
```
copyparty-backend/
├── uploads/          # File upload storage
├── downloads/        # Download staging area
├── temp/            # Temporary file processing
├── logs/            # Server and access logs
├── data/            # Database and metadata
└── copyparty-sfx.py # Main server executable
```

## Integration Examples

### Upload File via API
```python
import requests

url = "http://localhost:3923/api/upload"
files = {"file": open("document.pdf", "rb")}
data = {"api_key": "hub-node-api-2024", "path": "/documents/"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Download File via API
```python
import requests

url = "http://localhost:3923/api/download/documents/document.pdf"
params = {"api_key": "hub-node-api-2024"}

response = requests.get(url, params=params, stream=True)
with open("downloaded_document.pdf", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
```

### Clipboard Integration
```python
# Copy text to server clipboard
requests.post("http://localhost:3923/api/paste",
              json={"content": "Hello World", "api_key": "hub-node-api-2024"})

# Retrieve clipboard content
response = requests.get("http://localhost:3923/api/clipboard",
                       params={"api_key": "hub-node-api-2024"})
print(response.json()["content"])
```

## Advanced Features

### Multi-Node Clustering
Configure multiple CopyParty instances to work together:
```bash
# Node 1
./start-copyparty.sh --cluster-node=hub-001 --cluster-peers=hub-002,hub-003

# Node 2
./start-copyparty.sh --cluster-node=hub-002 --cluster-peers=hub-001,hub-003
```

### Webhook Integration
Set up webhooks for file events:
```python
# Configure webhook endpoint
webhook_config = {
    "upload_webhook": "http://your-app.com/api/file-uploaded",
    "download_webhook": "http://your-app.com/api/file-downloaded"
}
```

## Security

### API Key Management
- Change default API key in production
- Use environment variables for sensitive data
- Enable HTTPS for production deployments

### File Access Control
```bash
# Restrict upload paths
./start-copyparty.sh --upload-whitelist="/safe-uploads/"

# Enable user authentication
./start-copyparty.sh --auth-file=users.txt
```

## Monitoring

### Health Check
```bash
curl http://localhost:3923/api/status
```

### Log Analysis
```bash
tail -f logs/copyparty.log
```

## Deployment

### Production Linux Server
```bash
# Install as systemd service
sudo cp copyparty-hub.service /etc/systemd/system/
sudo systemctl enable copyparty-hub
sudo systemctl start copyparty-hub
```

### Cloud Deployment
- AWS: Use ECS with Docker container
- Google Cloud: Deploy to Cloud Run
- Azure: Use Container Instances

## Support

- **Documentation**: [CopyParty GitHub](https://github.com/9001/copyparty)
- **API Reference**: `http://localhost:3923/api/docs`
- **Issue Tracking**: Create issues for bugs or feature requests

---

**Built for high-performance file operations and distributed hub-node architectures.**

🤖 Generated with [Claude Code](https://claude.ai/code) | Co-Authored-By: Claude <noreply@anthropic.com>