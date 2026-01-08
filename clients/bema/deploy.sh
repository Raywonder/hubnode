#!/bin/bash
# =============================================================================
# Softnode Media Player - Complete Installation Script
# For AlmaLinux cPanel Server under devinecr user
# Version: 1.0.0
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as devinecr user
if [ "$USER" != "devinecr" ]; then
    error "This script must be run as the devinecr user"
    exit 1
fi

log "?? Starting Softnode Media Player Complete Installation"
log "=============================================="

# =============================================================================
# STEP 1: Create Directory Structure
# =============================================================================
log "?? Creating directory structure..."

# Backend directories
mkdir -p /home/devinecr/apps/hubnode/clients/softnode-media-player/{config,services,routes,middleware,scripts,tests}

# Frontend directories with all subdirectories
mkdir -p /home/devinecr/devinecreations.net/softhub/softnode/{css,js,images,public/media,demo/media,assets,fonts}

# Additional JS subdirectories
mkdir -p /home/devinecr/devinecreations.net/softhub/softnode/js/{components,services,utils,plugins}

# Backup and temp directories
mkdir -p /home/devinecr/backups/softnode
mkdir -p /home/devinecr/temp/softnode

log "? Directory structure created"

# =============================================================================
# STEP 2: Check and Install Dependencies
# =============================================================================
log "?? Checking and installing dependencies..."

# Check Node.js installation
if ! command -v node &> /dev/null; then
    log "Installing Node.js..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo dnf install nodejs -y
else
    info "Node.js already installed: $(node --version)"
fi

# Install global packages
log "Installing global npm packages..."
npm install -g pm2 nodemon

# Check MySQL client
if ! command -v mysql &> /dev/null; then
    warn "MySQL client not found. Please install mysql client if needed."
fi

log "? Dependencies checked and installed"

# =============================================================================
# STEP 3: Create Backend Files
# =============================================================================
log "?? Creating backend application files..."

# Main app.js
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/app.js << 'EOF'
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

// Import services and middleware
const DatabaseService = require('./services/database');
const AuthService = require('./services/auth');
const MediaService = require('./services/media');
const authMiddleware = require('./middleware/auth');
const corsMiddleware = require('./middleware/cors');
const errorHandler = require('./middleware/errorHandler');

class SoftnodeMediaPlayerApp {
    constructor() {
        this.app = express();
        this.server = createServer(this.app);
        this.io = new Server(this.server, {
            cors: {
                origin: [
                    "https://devinecreations.net",
                    "https://www.devinecreations.net"
                ],
                methods: ["GET", "POST"],
                credentials: true
            }
        });
        
        this.port = process.env.PORT || 3001;
        this.services = {};
    }
    
    async initialize() {
        try {
            await this.initializeServices();
            this.setupMiddleware();
            this.setupRoutes();
            this.setupWebSocket();
            this.setupErrorHandling();
            
            console.log('Softnode Media Player backend initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            process.exit(1);
        }
    }
    
    async initializeServices() {
        // Initialize database connection
        this.services.database = new DatabaseService();
        await this.services.database.connect();
        
        // Initialize other services
        this.services.auth = new AuthService(this.services.database);
        this.services.media = new MediaService(this.services.database);
        
        console.log('Services initialized');
    }
    
    setupMiddleware() {
        // Security middleware
        this.app.use(helmet({
            crossOriginEmbedderPolicy: false,
            contentSecurityPolicy: false
        }));
        
        // CORS middleware
        this.app.use(corsMiddleware);
        
        // Compression
        this.app.use(compression());
        
        // Rate limiting
        const limiter = rateLimit({
            windowMs: 15 * 60 * 1000,
            max: 1000,
            message: 'Too many requests from this IP'
        });
        this.app.use(limiter);
        
        // Body parsing
        this.app.use(express.json({ limit: '50mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));
        
        // Request logging
        this.app.use((req, res, next) => {
            console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
            next();
        });
    }
    
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ 
                status: 'ok', 
                timestamp: new Date().toISOString(),
                version: '1.0.0',
                database: this.services.database ? 'connected' : 'disconnected'
            });
        });
        
        // Media API routes
        this.app.get('/media', async (req, res) => {
            try {
                const media = await this.services.media.getMediaLibrary(req.query);
                res.json(media);
            } catch (error) {
                res.status(500).json({ error: 'Failed to fetch media' });
            }
        });
        
        this.app.get('/media/:id', async (req, res) => {
            try {
                const media = await this.services.media.getMediaItem(req.params.id);
                if (!media) {
                    return res.status(404).json({ error: 'Media not found' });
                }
                res.json(media);
            } catch (error) {
                res.status(500).json({ error: 'Failed to fetch media item' });
            }
        });
        
        // Playlist routes
        this.app.get('/playlists', async (req, res) => {
            try {
                const playlists = await this.services.media.getPlaylists(req.query.user_id);
                res.json(playlists);
            } catch (error) {
                res.status(500).json({ error: 'Failed to fetch playlists' });
            }
        });
        
        // 404 handler
        this.app.use('*', (req, res) => {
            res.status(404).json({ error: 'Endpoint not found' });
        });
    }
    
    setupWebSocket() {
        this.io.on('connection', (socket) => {
            console.log('User connected:', socket.id);
            
            socket.on('join-room', (roomId) => {
                socket.join(roomId);
                socket.emit('joined-room', roomId);
            });
            
            socket.on('media-sync', (data) => {
                socket.to(data.roomId).emit('media-sync', data);
            });
            
            socket.on('disconnect', () => {
                console.log('User disconnected:', socket.id);
            });
        });
    }
    
    setupErrorHandling() {
        this.app.use(errorHandler);
        
        process.on('unhandledRejection', (err) => {
            console.error('Unhandled Promise Rejection:', err);
        });
        
        process.on('uncaughtException', (err) => {
            console.error('Uncaught Exception:', err);
        });
    }
    
    start() {
        this.server.listen(this.port, '127.0.0.1', () => {
            console.log(`Softnode Media Player backend running on port ${this.port}`);
        });
    }
}

// Initialize and start the application
if (require.main === module) {
    const app = new SoftnodeMediaPlayerApp();
    app.initialize().then(() => {
        app.start();
    });
}

module.exports = SoftnodeMediaPlayerApp;
EOF

# Backend package.json
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/package.json << 'EOF'
{
  "name": "softnode-media-player-backend",
  "version": "1.0.0",
  "description": "Accessible media player backend with streaming capabilities",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "dev": "nodemon app.js",
    "test": "jest",
    "pm2": "pm2 start app.js --name softnode-backend",
    "stop": "pm2 stop softnode-backend",
    "restart": "pm2 restart softnode-backend",
    "logs": "pm2 logs softnode-backend"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "compression": "^1.7.4",
    "express-rate-limit": "^6.7.0",
    "socket.io": "^4.7.2",
    "mysql2": "^3.6.0",
    "jsonwebtoken": "^9.0.2",
    "bcrypt": "^5.1.0",
    "multer": "^1.4.5-lts.1",
    "music-metadata": "^7.14.0",
    "fluent-ffmpeg": "^2.1.2",
    "uuid": "^9.0.0",
    "dotenv": "^16.3.1",
    "winston": "^3.10.0",
    "sharp": "^0.32.5"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.4",
    "supertest": "^6.3.3"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
EOF

# Environment file with actual database credentials
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/.env << 'EOF'
NODE_ENV=production
PORT=3001

# Database Configuration (cPanel Database)
DB_HOST=localhost
DB_USER=devinecr_devinecrsofthub
DB_PASSWORD=softnodeapp$
DB_NAME=devinecr_softnodeapp

# JWT Configuration
JWT_SECRET=softnode_jwt_secret_key_very_long_and_secure_2024
JWT_EXPIRE=24h
JWT_REFRESH_EXPIRE=7d

# API Configuration
API_BASE_URL=https://devinecreations.net/softhub/softnode/api
FRONTEND_URL=https://devinecreations.net/softhub/softnode

# Media Storage
MEDIA_STORAGE_PATH=/home/devinecr/devinecreations.net/softhub/softnode/public/media
MEDIA_BASE_URL=https://devinecreations.net/softhub/softnode/media

# Streaming Configuration
RTMP_SERVER_PORT=1935
STREAMING_CHUNK_SIZE=60000

# Security
CORS_ORIGINS=https://devinecreations.net,https://www.devinecreations.net
RATE_LIMIT_WINDOW=900000
RATE_LIMIT_MAX=1000

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/softnode/app.log

# Email Configuration (optional)
SMTP_HOST=mail.devinecreations.net
SMTP_PORT=587
SMTP_USER=softnode@devinecreations.net
SMTP_PASS=
EOF

log "? Backend application files created"

# =============================================================================
# STEP 4: Create Backend Services
# =============================================================================
log "?? Creating backend service files..."

# Database service
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/services/database.js << 'EOF'
const mysql = require('mysql2/promise');

class DatabaseService {
    constructor() {
        this.connection = null;
        this.config = {
            host: process.env.DB_HOST || 'localhost',
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME,
            charset: 'utf8mb4',
            timezone: 'UTC'
        };
    }
    
    async connect() {
        try {
            this.connection = await mysql.createConnection(this.config);
            console.log('Database connected successfully');
            
            // Test connection
            await this.connection.ping();
            
            // Initialize tables if they don't exist
            await this.initializeTables();
            
        } catch (error) {
            console.error('Database connection failed:', error);
            throw error;
        }
    }
    
    async initializeTables() {
        const tables = [
            `CREATE TABLE IF NOT EXISTS media_items (
                id VARCHAR(36) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                artist VARCHAR(255),
                album VARCHAR(255),
                duration INT,
                file_path VARCHAR(500),
                file_size BIGINT,
                mime_type VARCHAR(100),
                bitrate INT,
                sample_rate INT,
                metadata JSON,
                accessibility_features JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_artist (artist),
                INDEX idx_album (album),
                FULLTEXT(title, artist, album)
            )`,
            
            `CREATE TABLE IF NOT EXISTS user_playlists (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                accessibility_settings JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_public (is_public)
            )`,
            
            `CREATE TABLE IF NOT EXISTS playlist_items (
                playlist_id INT,
                media_id VARCHAR(36),
                position INT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (playlist_id, media_id),
                FOREIGN KEY (playlist_id) REFERENCES user_playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE,
                INDEX idx_position (playlist_id, position)
            )`,
            
            `CREATE TABLE IF NOT EXISTS user_activity (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(255),
                activity_type ENUM('play', 'pause', 'skip', 'like', 'share', 'comment'),
                media_id VARCHAR(36),
                session_id VARCHAR(64),
                ip_address VARCHAR(45),
                user_agent TEXT,
                accessibility_context JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON,
                INDEX idx_user_activity (user_id, timestamp),
                INDEX idx_media_activity (media_id, timestamp),
                INDEX idx_session (session_id)
            )`,
            
            `CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                accessibility_settings JSON,
                preferences JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )`
        ];
        
        for (const table of tables) {
            await this.connection.execute(table);
        }
        
        // Insert sample data
        await this.insertSampleData();
        
        console.log('Database tables initialized');
    }
    
    async insertSampleData() {
        const sampleMedia = [
            {
                id: 'demo-001',
                title: 'Accessibility Interface Demo',
                artist: 'Softnode Team',
                album: 'Demo Album',
                duration: 180,
                file_path: 'interface-demo.mp3',
                mime_type: 'audio/mpeg',
                accessibility_features: JSON.stringify({
                    hasLyrics: false,
                    hasAudioDescription: true,
                    languageCode: 'en',
                    explicit: false
                })
            },
            {
                id: 'demo-002',
                title: 'Sample Music Track',
                artist: 'Demo Artist',
                album: 'Sample Album',
                duration: 240,
                file_path: 'sample-music.mp3',
                mime_type: 'audio/mpeg',
                accessibility_features: JSON.stringify({
                    hasLyrics: false,
                    hasAudioDescription: false,
                    languageCode: 'en',
                    explicit: false
                })
            },
            {
                id: 'demo-003',
                title: 'Podcast Episode Sample',
                artist: 'Tech Talk Podcast',
                album: 'Demo Podcasts',
                duration: 300,
                file_path: 'podcast-sample.mp3',
                mime_type: 'audio/mpeg',
                accessibility_features: JSON.stringify({
                    hasLyrics: false,
                    hasAudioDescription: false,
                    languageCode: 'en',
                    explicit: false
                })
            }
        ];
        
        for (const media of sampleMedia) {
            await this.connection.execute(
                `INSERT IGNORE INTO media_items 
                 (id, title, artist, album, duration, file_path, mime_type, accessibility_features)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
                [media.id, media.title, media.artist, media.album, media.duration, 
                 media.file_path, media.mime_type, media.accessibility_features]
            );
        }
        
        // Create demo playlist
        await this.connection.execute(
            `INSERT IGNORE INTO user_playlists (id, user_id, name, description, is_public)
             VALUES (1, 'demo-user', 'Demo Playlist', 'Sample tracks for demonstration', true)`
        );
        
        // Add items to demo playlist
        const playlistItems = [
            [1, 'demo-001', 1],
            [1, 'demo-002', 2],
            [1, 'demo-003', 3]
        ];
        
        for (const item of playlistItems) {
            await this.connection.execute(
                `INSERT IGNORE INTO playlist_items (playlist_id, media_id, position)
                 VALUES (?, ?, ?)`,
                item
            );
        }
    }
    
    async query(sql, params = []) {
        try {
            const [rows] = await this.connection.execute(sql, params);
            return rows;
        } catch (error) {
            console.error('Database query error:', error);
            throw error;
        }
    }
    
    async disconnect() {
        if (this.connection) {
            await this.connection.end();
            console.log('Database disconnected');
        }
    }
}

module.exports = DatabaseService;
EOF

# Auth service
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/services/auth.js << 'EOF'
const jwt = require('jsonwebtoken');

class AuthService {
    constructor(database) {
        this.db = database;
        this.jwtSecret = process.env.JWT_SECRET;
        this.jwtExpire = process.env.JWT_EXPIRE || '24h';
    }
    
    generateToken(payload) {
        return jwt.sign(payload, this.jwtSecret, {
            expiresIn: this.jwtExpire
        });
    }
    
    verifyToken(token) {
        try {
            return jwt.verify(token, this.jwtSecret);
        } catch (error) {
            throw new Error('Invalid token');
        }
    }
    
    async createGuestSession() {
        const guestId = 'guest_' + Date.now();
        const guestPayload = {
            userId: guestId,
            username: 'Guest',
            source: 'guest',
            permissions: {
                canUpload: false,
                canCreatePlaylists: false,
                canComment: false,
                canStream: false
            }
        };
        
        return this.generateToken(guestPayload);
    }
}

module.exports = AuthService;
EOF

# Media service
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/services/media.js << 'EOF'
class MediaService {
    constructor(database) {
        this.db = database;
    }
    
    async getMediaLibrary(options = {}) {
        const { page = 1, limit = 20, search, artist, album } = options;
        const offset = (page - 1) * limit;
        
        let query = 'SELECT * FROM media_items WHERE 1=1';
        let params = [];
        
        if (search) {
            query += ' AND MATCH(title, artist, album) AGAINST (? IN BOOLEAN MODE)';
            params.push(`*${search}*`);
        }
        
        if (artist) {
            query += ' AND artist = ?';
            params.push(artist);
        }
        
        if (album) {
            query += ' AND album = ?';
            params.push(album);
        }
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
        params.push(parseInt(limit), parseInt(offset));
        
        const media = await this.db.query(query, params);
        
        // Add media URLs
        const mediaWithUrls = media.map(item => ({
            ...item,
            url: `${process.env.MEDIA_BASE_URL}/${item.file_path}`
        }));
        
        return {
            media: mediaWithUrls,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                hasMore: media.length === parseInt(limit)
            }
        };
    }
    
    async getMediaItem(id) {
        const [media] = await this.db.query(
            'SELECT * FROM media_items WHERE id = ?',
            [id]
        );
        
        if (!media) {
            return null;
        }
        
        return {
            ...media,
            url: `${process.env.MEDIA_BASE_URL}/${media.file_path}`
        };
    }
    
    async getPlaylists(userId = 'demo-user') {
        const playlists = await this.db.query(
            `SELECT p.*, COUNT(pi.media_id) as track_count
             FROM user_playlists p
             LEFT JOIN playlist_items pi ON p.id = pi.playlist_id
             WHERE p.user_id = ? OR p.is_public = true
             GROUP BY p.id
             ORDER BY p.created_at DESC`,
            [userId]
        );
        
        return { playlists };
    }
}

module.exports = MediaService;
EOF

log "? Backend service files created"

# =============================================================================
# STEP 5: Create Middleware Files
# =============================================================================
log "?? Creating middleware files..."

# CORS middleware
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/middleware/cors.js << 'EOF'
const cors = require('cors');

const corsOptions = {
    origin: function (origin, callback) {
        const allowedOrigins = [
            'https://devinecreations.net',
            'https://www.devinecreations.net'
        ];
        
        if (!origin) return callback(null, true);
        
        if (allowedOrigins.indexOf(origin) !== -1) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allowedHeaders: [
        'Origin',
        'X-Requested-With',
        'Content-Type',
        'Accept',
        'Authorization',
        'Range'
    ],
    exposedHeaders: [
        'Content-Length',
        'Content-Range',
        'Accept-Ranges'
    ]
};

module.exports = cors(corsOptions);
EOF

# Auth middleware
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/middleware/auth.js << 'EOF'
function authMiddleware(authService) {
    return async (req, res, next) => {
        try {
            const authHeader = req.headers.authorization;
            
            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                return res.status(401).json({ error: 'No token provided' });
            }
            
            const token = authHeader.substring(7);
            const decoded = authService.verifyToken(token);
            
            req.user = decoded;
            next();
        } catch (error) {
            res.status(401).json({ error: 'Invalid token' });
        }
    };
}

module.exports = authMiddleware;
EOF

# Error handler middleware
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/middleware/errorHandler.js << 'EOF'
function errorHandler(err, req, res, next) {
    console.error({
        message: err.message,
        stack: err.stack,
        url: req.url,
        method: req.method,
        ip: req.ip,
        timestamp: new Date().toISOString()
    });
    
    if (process.env.NODE_ENV === 'production') {
        res.status(500).json({
            error: 'Internal server error',
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(500).json({
            error: err.message,
            stack: err.stack,
            timestamp: new Date().toISOString()
        });
    }
}

module.exports = errorHandler;
EOF

log "? Middleware files created"

# =============================================================================
# STEP 6: Create Frontend Files
# =============================================================================
log "?? Creating frontend files..."

# Main index.html
cat > /home/devinecr/devinecreations.net/softhub/softnode/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Softnode Media Player - Accessible Audio Experience</title>
    
    <!-- SEO and Accessibility Meta Tags -->
    <meta name="description" content="Professional accessible media player with advanced screen reader support, audio editing, and streaming capabilities designed for everyone.">
    <meta name="keywords" content="accessible media player, screen reader, audio editing, NVDA, JAWS, VoiceOver, streaming">
    <meta name="author" content="Devine Creations">
    
    <!-- Open Graph -->
    <meta property="og:title" content="Softnode Media Player - Accessible Audio Experience">
    <meta property="og:description" content="Professional media player designed for accessibility with screen reader support and advanced audio features.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://devinecreations.net/softhub/softnode">
    
    <!-- Accessibility -->
    <meta name="theme-color" content="#1a202c">
    <meta name="color-scheme" content="light dark">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/accessibility.css">
    <link rel="stylesheet" href="css/player.css">
    
    <!-- High Contrast Mode -->
    <link rel="stylesheet" href="css/high-contrast.css" media="(prefers-contrast: high)">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Softnode Media Player",
        "description": "Accessible media player with professional audio editing and streaming capabilities",
        "applicationCategory": "MultimediaApplication",
        "operatingSystem": ["Windows", "macOS", "Linux"],
        "accessibilityAPI": ["ARIA", "keyboard"],
        "accessibilityControl": ["fullKeyboardControl"],
        "accessibilityFeature": ["screenReader", "keyboardNavigation", "highContrast"]
    }
    </script>
</head>
<body>
    <!-- Skip Navigation -->
    <a href="#main-content" class="skip-nav" tabindex="1">Skip to main content</a>
    <a href="#player-controls" class="skip-nav" tabindex="2">Skip to player controls</a>
    
    <!-- Accessibility Controls -->
    <div class="accessibility-toolbar" role="toolbar" aria-label="Accessibility options">
        <button id="toggle-high-contrast" aria-pressed="false" title="Toggle high contrast mode">
            <span class="sr-only">Toggle high contrast mode</span>
            ??
        </button>
        <button id="increase-font-size" title="Increase text size">
            <span class="sr-only">Increase text size</span>
            A+
        </button>
        <button id="decrease-font-size" title="Decrease text size">
            <span class="sr-only">Decrease text size</span>
            A-
        </button>
        <button id="toggle-animations" aria-pressed="true" title="Toggle animations">
            <span class="sr-only">Toggle animations</span>
            ??
        </button>
    </div>
    
    <!-- Main Application Container -->
    <div id="app" role="application" aria-label="Softnode Media Player">
        <!-- Loading Screen -->
        <div id="loading-screen" class="loading-screen" aria-live="polite">
            <div class="loading-content">
                <h1>Softnode Media Player</h1>
                <div class="loading-spinner" aria-hidden="true"></div>
                <p>Loading accessible media player...</p>
                <div class="loading-progress" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                    <div class="progress-bar"></div>
                </div>
            </div>
        </div>
        
        <!-- Main Application -->
        <main id="main-content" class="main-content" style="display: none;">
            <div class="container">
                <!-- Welcome Section -->
                <section class="welcome-section" aria-labelledby="welcome-heading">
                    <h1 id="welcome-heading">?? Welcome to Softnode Media Player</h1>
                    <p class="welcome-subtitle">Your professional accessible audio experience starts here.</p>
                    
                    <!-- Quick Actions -->
                    <div class="quick-actions">
                        <a href="demo/" class="btn btn-primary" role="button">Try Demo Version</a>
                        <button id="get-started" class="btn btn-secondary">Get Started</button>
                        <button id="load-library" class="btn btn-outline">Browse Library</button>
                    </div>
                </section>
                
                <!-- Features Section -->
                <section class="features-section" aria-labelledby="features-heading">
                    <h2 id="features-heading">Accessibility Features</h2>
                    <div class="features-grid">
                        <div class="feature-card">
                            <h3>?? Screen Reader Support</h3>
                            <p>Full NVDA, JAWS, and VoiceOver compatibility with audio cues and announcements.</p>
                        </div>
                        <div class="feature-card">
                            <h3>?? Keyboard Navigation</h3>
                            <p>Complete keyboard control with customizable shortcuts for all functions.</p>
                        </div>
                        <div class="feature-card">
                            <h3>??? Audio Controls</h3>
                            <p>Professional volume control, seeking, and chapter navigation.</p>
                        </div>
                        <div class="feature-card">
                            <h3>?? Visual Accessibility</h3>
                            <p>High contrast themes, font scaling, and motion reduction options.</p>
                        </div>
                    </div>
                </section>
                
                <!-- Media Library Section -->
                <section id="media-library" class="media-library-section" aria-labelledby="library-heading" style="display: none;">
                    <h2 id="library-heading">Media Library</h2>
                    <div class="library-controls">
                        <input type="search" id="search-input" placeholder="Search media..." aria-label="Search media library">
                        <button id="search-btn" class="btn btn-primary">Search</button>
                    </div>
                    <div class="media-grid" id="media-grid" role="grid" aria-label="Audio files">
                        <!-- Media items will be loaded here -->
                    </div>
                </section>
            </div>
        </main>
    </div>
    
    <!-- Screen Reader Announcements -->
    <div id="sr-announcements" aria-live="polite" aria-atomic="true" class="sr-only"></div>
    <div id="sr-announcements-assertive" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
    
    <!-- Error Fallback -->
    <noscript>
        <div class="error-fallback">
            <h1>JavaScript Required</h1>
            <p>Softnode Media Player requires JavaScript to function. Please enable JavaScript to continue.</p>
        </div>
    </noscript>
    
    <!-- Scripts -->
    <script>
        // Initial configuration
        window.SoftnodeConfig = {
            apiBase: '/softhub/softnode/api',
            mediaBase: '/softhub/softnode/media',
            wsBase: 'wss://devinecreations.net/softhub/softnode/ws',
            version: '1.0.0',
            accessibility: {
                announcements: true,
                keyboardNavigation: true,
                screenReaderOptimized: true
            }
        };
        
        // Accessibility preferences
        window.AccessibilityPreferences = {
            reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            highContrast: window.matchMedia('(prefers-contrast: high)').matches,
            darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches
        };
    </script>
    
    <!-- Main Application JavaScript -->
    <script src="js/utils.js"></script>
    <script src="js/accessibility.js"></script>
    <script src="js/api.js"></script>
    <script src="js/components.js"></script>
    <script src="js/main.js"></script>
</body>
</html>
EOF

# Main CSS file
cat > /home/devinecr/devinecreations.net/softhub/softnode/css/main.css << 'EOF'
/* Softnode Media Player - Main Styles */

/* CSS Custom Properties */
:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --secondary-color: #64748b;
    --accent-color: #f59e0b;
    --success-color: #10b981;
    --error-color: #ef4444;
    --warning-color: #f59e0b;
    
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #e2e8f0;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #64748b;
    
    --border-color: #e2e8f0;
    --border-focus: #3b82f6;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
    
    --font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.25rem;
    --text-2xl: 1.5rem;
    --text-3xl: 1.875rem;
    
    --spacing-1: 0.25rem;
    --spacing-2: 0.5rem;
    --spacing-3: 0.75rem;
    --spacing-4: 1rem;
    --spacing-6: 1.5rem;
    --spacing-8: 2rem;
    --spacing-12: 3rem;
    
    --z-dropdown: 1000;
    --z-sticky: 1020;
    --z-fixed: 1030;
    --z-modal: 1040;
    --z-tooltip: 1070;
    
    --transition-fast: 150ms ease-in-out;
    --transition-normal: 200ms ease-in-out;
    --transition-slow: 300ms ease-in-out;
}

/* Dark mode color scheme */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --border-color: #334155;
    }
}

/* Base styles */
* {
    box-sizing: border-box;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
}

@media (prefers-reduced-motion: reduce) {
    html {
        scroll-behavior: auto;
    }
}

body {
    margin: 0;
    padding: 0;
    font-family: var(--font-sans);
    font-size: var(--text-base);
    line-height: 1.5;
    color: var(--text-primary);
    background-color: var(--bg-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    margin: 0 0 var(--spacing-4) 0;
    font-weight: 600;
    line-height: 1.25;
    color: var(--text-primary);
}

h1 { font-size: var(--text-3xl); }
h2 { font-size: var(--text-2xl); }
h3 { font-size: var(--text-xl); }

p {
    margin: 0 0 var(--spacing-4) 0;
    color: var(--text-secondary);
}

/* Layout */
.main-content {
    min-height: 100vh;
    padding: var(--spacing-8) 0;
}

.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-4);
}

/* Components */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-2) var(--spacing-4);
    font-size: var(--text-sm);
    font-weight: 500;
    text-decoration: none;
    border: 1px solid transparent;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
    min-height: 44px;
}

.btn:focus {
    outline: 2px solid var(--border-focus);
    outline-offset: 2px;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.btn-primary:hover:not(:disabled) {
    background-color: var(--primary-hover);
    border-color: var(--primary-hover);
}

.btn-secondary {
    background-color: transparent;
    color: var(--text-primary);
    border-color: var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
    background-color: var(--bg-secondary);
}

.btn-outline {
    background-color: transparent;
    color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-outline:hover:not(:disabled) {
    background-color: var(--primary-color);
    color: white;
}

/* Loading screen */
.loading-screen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: var(--z-modal);
}

.loading-content {
    text-align: center;
    max-width: 400px;
    padding: var(--spacing-8);
}

.loading-spinner {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid var(--bg-tertiary);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
    margin: var(--spacing-4) 0;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.loading-progress {
    width: 100%;
    height: 8px;
    background-color: var(--bg-tertiary);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-top: var(--spacing-4);
}

.progress-bar {
    height: 100%;
    background-color: var(--primary-color);
    transition: width var(--transition-normal);
}

/* Welcome section */
.welcome-section {
    text-align: center;
    padding: var(--spacing-8) 0;
}

.welcome-section h1 {
    font-size: 3rem;
    margin-bottom: var(--spacing-4);
    color: var(--primary-color);
}

.welcome-subtitle {
    font-size: var(--text-lg);
    margin-bottom: var(--spacing-8);
    color: var(--text-secondary);
}

.quick-actions {
    display: flex;
    gap: var(--spacing-4);
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: var(--spacing-8);
}

/* Features section */
.features-section {
    padding: var(--spacing-8) 0;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-6);
    margin-top: var(--spacing-6);
}

.feature-card {
    background: var(--bg-secondary);
    padding: var(--spacing-6);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);
    text-align: center;
}

.feature-card h3 {
    margin-top: 0;
    color: var(--primary-color);
}

/* Media library */
.media-library-section {
    padding: var(--spacing-8) 0;
}

.library-controls {
    display: flex;
    gap: var(--spacing-2);
    margin-bottom: var(--spacing-6);
    max-width: 400px;
}

.library-controls input {
    flex: 1;
    padding: var(--spacing-2) var(--spacing-3);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
}

.library-controls input:focus {
    outline: none;
    border-color: var(--border-focus);
    box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);
}

.media-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--spacing-4);
}

.media-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.media-card:hover,
.media-card:focus {
    border-color: var(--primary-color);
    box-shadow: var(--shadow-md);
    outline: none;
}

.media-card h3 {
    margin: 0 0 var(--spacing-2) 0;
    font-size: var(--text-base);
}

.media-card p {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--text-muted);
}

/* Utility classes */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.hidden {
    display: none;
}

/* Responsive design */
@media (max-width: 768px) {
    .welcome-section h1 {
        font-size: 2rem;
    }
    
    .quick-actions {
        flex-direction: column;
        align-items: center;
    }
    
    .btn {
        width: 200px;
    }
    
    .features-grid {
        grid-template-columns: 1fr;
    }
    
    .library-controls {
        flex-direction: column;
        max-width: none;
    }
}

/* Print styles */
@media print {
    .accessibility-toolbar,
    .loading-screen {
        display: none !important;
    }
}
EOF

# Accessibility CSS
cat > /home/devinecr/devinecreations.net/softhub/softnode/css/accessibility.css << 'EOF'
/* Accessibility-specific styles */

/* Skip navigation links */
.skip-nav {
    position: absolute;
    top: -40px;
    left: 6px;
    background: var(--primary-color);
    color: white;
    padding: 8px;
    text-decoration: none;
    border-radius: var(--radius-md);
    z-index: var(--z-tooltip);
    transition: top var(--transition-fast);
}

.skip-nav:focus {
    top: 6px;
}

/* Accessibility toolbar */
.accessibility-toolbar {
    position: fixed;
    top: 0;
    right: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-top: none;
    border-right: none;
    border-radius: 0 0 0 var(--radius-lg);
    padding: var(--spacing-2);
    display: flex;
    gap: var(--spacing-1);
    z-index: var(--z-fixed);
    box-shadow: var(--shadow-md);
}

.accessibility-toolbar button {
    width: 32px;
    height: 32px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: var(--text-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
}

.accessibility-toolbar button:hover {
    background: var(--bg-tertiary);
}

.accessibility-toolbar button:focus {
    outline: 2px solid var(--border-focus);
    outline-offset: 2px;
}

.accessibility-toolbar button[aria-pressed="true"] {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* Enhanced focus indicators */
*:focus {
    outline: 2px solid var(--border-focus);
    outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --primary-color: #000080;
        --primary-hover: #000060;
        --error-color: #800000;
        --success-color: #008000;
        --border-color: #000000;
    }
    
    .btn {
        border-width: 2px;
    }
    
    *:focus {
        outline-width: 3px;
        outline-color: #FF6600;
    }
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
    
    .loading-spinner {
        animation: none;
        border-top-color: var(--primary-color);
    }
}

/* Screen reader announcements */
[aria-live] {
    position: absolute;
    left: -10000px;
    width: 1px;
    height: 1px;
    overflow: hidden;
}
EOF

# High contrast CSS
cat > /home/devinecr/devinecreations.net/softhub/softnode/css/high-contrast.css << 'EOF'
/* High contrast styles */
@media (prefers-contrast: high) {
    :root {
        --primary-color: #000080;
        --bg-primary: #ffffff;
        --bg-secondary: #f0f0f0;
        --text-primary: #000000;
        --border-color: #000000;
    }
    
    .btn {
        border-width: 2px;
        font-weight: bold;
    }
    
    .feature-card,
    .media-card {
        border-width: 2px;
    }
}
EOF

# Player CSS
cat > /home/devinecr/devinecreations.net/softhub/softnode/css/player.css << 'EOF'
/* Player component styles */
.player-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--bg-primary);
    border-top: 1px solid var(--border-color);
    padding: var(--spacing-4);
    box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
    z-index: var(--z-sticky);
}

.player-main {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
    max-width: 1200px;
    margin: 0 auto;
}

.control-btn {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--text-lg);
    transition: all var(--transition-fast);
}

.control-btn:hover {
    background: var(--primary-color);
    color: white;
}

.control-btn:focus {
    outline: 2px solid var(--border-focus);
    outline-offset: 2px;
}

.play-pause-btn {
    width: 52px;
    height: 52px;
    background: var(--primary-color);
    color: white;
    font-size: var(--text-xl);
}

.play-pause-btn:hover {
    background: var(--primary-hover);
}
EOF

log "? Frontend files created"

# =============================================================================
# STEP 7: Create JavaScript Files
# =============================================================================
log "?? Creating JavaScript files..."

# Main JavaScript
cat > /home/devinecr/devinecreations.net/softhub/softnode/js/main.js << 'EOF'
(function() {
    'use strict';
    
    let app = {
        initialized: false,
        mediaLibrary: [],
        currentTrack: null,
        config: window.SoftnodeConfig || {}
    };
    
    async function initializeApp() {
        try {
            console.log('Initializing Softnode Media Player...');
            updateLoadingProgress(20);
            
            // Initialize accessibility features
            initializeAccessibility();
            updateLoadingProgress(40);
            
            // Set up event listeners
            setupEventListeners();
            updateLoadingProgress(60);
            
            // Connect to backend
            await connectToBackend();
            updateLoadingProgress(80);
            
            // Complete initialization
            completeInitialization();
            updateLoadingProgress(100);
            
            app.initialized = true;
            announceToScreenReader('Softnode Media Player loaded and ready');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            showError('Failed to load application. Please refresh the page.');
        }
    }
    
    function initializeAccessibility() {
        // Set up keyboard shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);
        
        // Set up accessibility toolbar
        setupAccessibilityToolbar();
        
        // Apply user preferences
        applyAccessibilityPreferences();
    }
    
    function setupEventListeners() {
        // Get started button
        const getStartedBtn = document.getElementById('get-started');
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', () => {
                announceToScreenReader('Get started feature coming soon!');
            });
        }
        
        // Load library button
        const loadLibraryBtn = document.getElementById('load-library');
        if (loadLibraryBtn) {
            loadLibraryBtn.addEventListener('click', loadMediaLibrary);
        }
        
        // Search functionality
        const searchBtn = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');
        
        if (searchBtn) {
            searchBtn.addEventListener('click', performSearch);
        }
        
        if (searchInput) {
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }
    }
    
    function setupAccessibilityToolbar() {
        const contrastBtn = document.getElementById('toggle-high-contrast');
        const increaseFontBtn = document.getElementById('increase-font-size');
        const decreaseFontBtn = document.getElementById('decrease-font-size');
        const animationBtn = document.getElementById('toggle-animations');
        
        if (contrastBtn) {
            contrastBtn.addEventListener('click', toggleHighContrast);
        }
        
        if (increaseFontBtn) {
            increaseFontBtn.addEventListener('click', () => adjustFontSize(2));
        }
        
        if (decreaseFontBtn) {
            decreaseFontBtn.addEventListener('click', () => adjustFontSize(-2));
        }
        
        if (animationBtn) {
            animationBtn.addEventListener('click', toggleAnimations);
        }
    }
    
    function handleKeyboardShortcuts(event) {
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        const shortcuts = {
            'KeyL': (e) => {
                e.preventDefault();
                loadMediaLibrary();
                announceToScreenReader('Loading media library');
            },
            'KeyS': (e) => {
                if (e.ctrlKey) {
                    e.preventDefault();
                    document.getElementById('search-input')?.focus();
                    announceToScreenReader('Search focused');
                }
            },
            'Escape': (e) => {
                e.preventDefault();
                const librarySection = document.getElementById('media-library');
                if (librarySection && !librarySection.classList.contains('hidden')) {
                    librarySection.style.display = 'none';
                    announceToScreenReader('Media library closed');
                }
            }
        };
        
        if (shortcuts[event.code]) {
            shortcuts[event.code](event);
        }
    }
    
    async function connectToBackend() {
        try {
            const response = await fetch(`${app.config.apiBase}/health`);
            if (!response.ok) {
                throw new Error('Backend not available');
            }
            const data = await response.json();
            console.log('Backend connected:', data);
        } catch (error) {
            console.warn('Backend connection failed, running in offline mode');
        }
    }
    
    async function loadMediaLibrary() {
        try {
            announceToScreenReader('Loading media library...');
            
            const response = await fetch(`${app.config.apiBase}/media`);
            const data = await response.json();
            
            if (data.media) {
                app.mediaLibrary = data.media;
                renderMediaLibrary(data.media);
                showMediaLibrary();
                announceToScreenReader(`Media library loaded with ${data.media.length} items`);
            }
        } catch (error) {
            console.error('Failed to load media library:', error);
            showError('Failed to load media library');
        }
    }
    
    function renderMediaLibrary(mediaItems) {
        const mediaGrid = document.getElementById('media-grid');
        if (!mediaGrid) return;
        
        const mediaHTML = mediaItems.map(item => `
            <div class="media-card" role="gridcell" tabindex="0" data-media-id="${item.id}">
                <h3>${escapeHtml(item.title)}</h3>
                <p>by ${escapeHtml(item.artist)}</p>
                <p>${formatTime(item.duration)}</p>
            </div>
        `).join('');
        
        mediaGrid.innerHTML = mediaHTML;
        
        // Add event listeners
        mediaGrid.addEventListener('click', handleMediaCardClick);
        mediaGrid.addEventListener('keydown', handleMediaCardKeydown);
    }
    
    function showMediaLibrary() {
        const librarySection = document.getElementById('media-library');
        if (librarySection) {
            librarySection.style.display = 'block';
            librarySection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    function handleMediaCardClick(event) {
        const card = event.target.closest('.media-card');
        if (card) {
            const mediaId = card.dataset.mediaId;
            const mediaItem = app.mediaLibrary.find(item => item.id === mediaId);
            if (mediaItem) {
                announceToScreenReader(`Selected ${mediaItem.title} by ${mediaItem.artist}`);
            }
        }
    }
    
    function handleMediaCardKeydown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handleMediaCardClick(event);
        }
    }
    
    async function performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput?.value.trim();
        
        if (!query) {
            announceToScreenReader('Please enter a search term');
            return;
        }
        
        try {
            announceToScreenReader(`Searching for ${query}...`);
            
            const response = await fetch(`${app.config.apiBase}/media?search=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.media) {
                renderMediaLibrary(data.media);
                announceToScreenReader(`Found ${data.media.length} results for ${query}`);
            }
        } catch (error) {
            console.error('Search failed:', error);
            showError('Search failed');
        }
    }
    
    function toggleHighContrast() {
        document.body.classList.toggle('high-contrast');
        const isHighContrast = document.body.classList.contains('high-contrast');
        
        const btn = document.getElementById('toggle-high-contrast');
        btn.setAttribute('aria-pressed', isHighContrast);
        
        announceToScreenReader(`High contrast ${isHighContrast ? 'enabled' : 'disabled'}`);
    }
    
    function adjustFontSize(delta) {
        const currentSize = parseInt(getComputedStyle(document.documentElement).fontSize);
        const newSize = Math.max(12, Math.min(24, currentSize + delta));
        
        document.documentElement.style.fontSize = `${newSize}px`;
        announceToScreenReader(`Font size ${delta > 0 ? 'increased' : 'decreased'} to ${newSize}px`);
    }
    
    function toggleAnimations() {
        document.body.classList.toggle('no-animations');
        const animationsDisabled = document.body.classList.contains('no-animations');
        
        const btn = document.getElementById('toggle-animations');
        btn.setAttribute('aria-pressed', animationsDisabled);
        
        announceToScreenReader(`Animations ${animationsDisabled ? 'disabled' : 'enabled'}`);
    }
    
    function applyAccessibilityPreferences() {
        if (window.AccessibilityPreferences) {
            if (window.AccessibilityPreferences.reducedMotion) {
                document.body.classList.add('no-animations');
            }
            
            if (window.AccessibilityPreferences.highContrast) {
                document.body.classList.add('high-contrast');
            }
        }
    }
    
    function completeInitialization() {
        setTimeout(() => {
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
        }, 500);
    }
    
    function updateLoadingProgress(percentage) {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
    }
    
    function announceToScreenReader(message, priority = 'polite') {
        const region = priority === 'assertive' ? 
            document.getElementById('sr-announcements-assertive') :
            document.getElementById('sr-announcements');
        
        if (region) {
            region.textContent = message;
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    }
    
    function showError(message) {
        announceToScreenReader(message, 'assertive');
        console.error(message);
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        initializeApp();
    }
    
    // Export for debugging
    window.SoftnodeApp = app;
    
})();
EOF

# Utility functions
cat > /home/devinecr/devinecreations.net/softhub/softnode/js/utils.js << 'EOF'
// Utility functions for Softnode Media Player

window.SoftnodeUtils = {
    // Format time in seconds to MM:SS format
    formatTime: function(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
    
    // Escape HTML to prevent XSS
    escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Generate UUID
    generateUUID: function() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
};
EOF

# Accessibility helpers
cat > /home/devinecr/devinecreations.net/softhub/softnode/js/accessibility.js << 'EOF'
// Accessibility helper functions

window.AccessibilityHelpers = {
    // Announce message to screen readers
    announce: function(message, priority = 'polite') {
        const region = priority === 'assertive' ? 
            document.getElementById('sr-announcements-assertive') :
            document.getElementById('sr-announcements');
        
        if (region) {
            region.textContent = message;
            setTimeout(() => {
                region.textContent = '';
            }, 1000);
        }
    },
    
    // Focus management
    setFocus: function(element) {
        if (element && typeof element.focus === 'function') {
            element.focus();
        }
    },
    
    // Trap focus within a container
    trapFocus: function(container) {
        const focusableElements = container.querySelectorAll(
            'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        container.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
        
        firstElement.focus();
    }
};
EOF

# API communication
cat > /home/devinecr/devinecreations.net/softhub/softnode/js/api.js << 'EOF'
// API communication module

window.SoftnodeAPI = {
    baseURL: window.SoftnodeConfig?.apiBase || '/softhub/softnode/api',
    
    // Generic API request
    request: async function(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Get media library
    getMedia: function(params = {}) {
        const searchParams = new URLSearchParams(params);
        return this.request(`/media?${searchParams}`);
    },
    
    // Get specific media item
    getMediaItem: function(id) {
        return this.request(`/media/${id}`);
    },
    
    // Get playlists
    getPlaylists: function(userId) {
        const params = userId ? `?user_id=${userId}` : '';
        return this.request(`/playlists${params}`);
    },
    
    // Health check
    health: function() {
        return this.request('/health');
    }
};
EOF

# Components
cat > /home/devinecr/devinecreations.net/softhub/softnode/js/components.js << 'EOF'
// UI Components for Softnode Media Player

window.SoftnodeComponents = {
    // Create a media card element
    createMediaCard: function(mediaItem) {
        const card = document.createElement('div');
        card.className = 'media-card';
        card.role = 'gridcell';
        card.tabIndex = 0;
        card.dataset.mediaId = mediaItem.id;
        
        card.innerHTML = `
            <h3>${window.SoftnodeUtils.escapeHtml(mediaItem.title)}</h3>
            <p>by ${window.SoftnodeUtils.escapeHtml(mediaItem.artist)}</p>
            <p>${window.SoftnodeUtils.formatTime(mediaItem.duration)}</p>
        `;
        
        return card;
    },
    
    // Create a loading spinner
    createLoadingSpinner: function() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.setAttribute('aria-hidden', 'true');
        return spinner;
    },
    
    // Create an alert/notification
    createAlert: function(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.role = 'alert';
        alert.textContent = message;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
        
        return alert;
    }
};
EOF

log "? JavaScript files created"

# =============================================================================
# STEP 8: Create Demo Files
# =============================================================================
log "?? Creating demo version files..."

# Demo index.html
cat > /home/devinecr/devinecreations.net/softhub/softnode/demo/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Softnode Media Player - Demo Version</title>
    <meta name="description" content="Try the Softnode Media Player demo - Professional accessible media player with screen reader support.">
    
    <link rel="stylesheet" href="../css/main.css">
    <link rel="stylesheet" href="../css/accessibility.css">
    <link rel="stylesheet" href="../css/player.css">
    
    <style>
        .demo-banner {
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
            padding: var(--spacing-4);
            text-align: center;
            border-radius: var(--radius-lg);
            margin-bottom: var(--spacing-6);
            box-shadow: var(--shadow-lg);
        }
        
        .demo-banner h1 {
            margin: 0 0 var(--spacing-2) 0;
            font-size: var(--text-2xl);
        }
        
        .demo-limitations {
            background: var(--warning-color);
            color: white;
            padding: var(--spacing-3);
            border-radius: var(--radius-md);
            margin-bottom: var(--spacing-4);
            text-align: center;
        }
        
        .demo-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: var(--spacing-4);
            margin-bottom: var(--spacing-8);
        }
        
        .demo-feature {
            background: var(--bg-secondary);
            padding: var(--spacing-4);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
        }
        
        .demo-cta {
            text-align: center;
            padding: var(--spacing-8);
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <a href="#main-content" class="skip-nav">Skip to main content</a>
    
    <div class="accessibility-toolbar" role="toolbar" aria-label="Accessibility options">
        <button id="toggle-high-contrast" aria-pressed="false" title="Toggle high contrast">??</button>
        <button id="increase-font-size" title="Increase text size">A+</button>
        <button id="decrease-font-size" title="Decrease text size">A-</button>
    </div>
    
    <div id="app" role="application" aria-label="Softnode Media Player Demo">
        <main id="main-content" class="main-content">
            <div class="container">
                <div class="demo-banner">
                    <h1>?? Softnode Media Player Demo</h1>
                    <p>Experience professional accessible audio with full screen reader support</p>
                </div>
                
                <div class="demo-limitations" role="alert">
                    <strong>Demo Version:</strong> Limited to sample tracks, 5-minute sessions, and basic features only
                </div>
                
                <section class="demo-features" aria-labelledby="features-heading">
                    <h2 id="features-heading" class="sr-only">Demo Features</h2>
                    
                    <div class="demo-feature">
                        <h3>?? Screen Reader Optimized</h3>
                        <p>Full NVDA, JAWS, and VoiceOver compatibility with audio cues and keyboard navigation.</p>
                    </div>
                    
                    <div class="demo-feature">
                        <h3>?? Keyboard Shortcuts</h3>
                        <p>Complete keyboard control with customizable shortcuts for all playback functions.</p>
                    </div>
                    
                    <div class="demo-feature">
                        <h3>??? Audio Controls</h3>
                        <p>Professional volume control, seeking, and chapter navigation with audio feedback.</p>
                    </div>
                    
                    <div class="demo-feature">
                        <h3>?? High Contrast</h3>
                        <p>Multiple visual themes including high contrast and dark mode support.</p>
                    </div>
                </section>
                
                <div class="quick-actions">
                    <button id="start-demo" class="btn btn-primary">Start Demo Player</button>
                    <a href="../" class="btn btn-secondary">Get Full Version</a>
                </div>
                
                <div class="demo-cta">
                    <h2>Ready for the Full Experience?</h2>
                    <p>Get unlimited access to all features, unlimited session time, and upload your own media.</p>
                    <a href="../" class="btn btn-primary">Get Full Version</a>
                    <a href="mailto:support@devinecreations.net" class="btn btn-outline">Contact Support</a>
                </div>
            </div>
        </main>
    </div>
    
    <div id="sr-announcements" aria-live="polite" aria-atomic="true" class="sr-only"></div>
    <div id="sr-announcements-assertive" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
    
    <script>
        window.SoftnodeConfig = {
            apiBase: '/softhub/softnode/api',
            mediaBase: '/softhub/softnode/demo/media',
            version: '1.0.0-demo',
            demo: true,
            demoTimeLimit: 300
        };
        
        function announceToScreenReader(message) {
            const region = document.getElementById('sr-announcements');
            if (region) {
                region.textContent = message;
                setTimeout(() => region.textContent = '', 1000);
            }
        }
        
        document.getElementById('start-demo').addEventListener('click', () => {
            announceToScreenReader('Demo player will be available soon. This is the basic setup.');
            alert('Demo player feature will be implemented. Currently showing the basic interface.');
        });
        
        // Basic accessibility toolbar functionality
        document.getElementById('toggle-high-contrast').addEventListener('click', function() {
            document.body.classList.toggle('high-contrast');
            const isEnabled = document.body.classList.contains('high-contrast');
            this.setAttribute('aria-pressed', isEnabled);
            announceToScreenReader(`High contrast ${isEnabled ? 'enabled' : 'disabled'}`);
        });
        
        document.getElementById('increase-font-size').addEventListener('click', function() {
            const currentSize = parseInt(getComputedStyle(document.documentElement).fontSize);
            const newSize = Math.min(24, currentSize + 2);
            document.documentElement.style.fontSize = newSize + 'px';
            announceToScreenReader('Font size increased');
        });
        
        document.getElementById('decrease-font-size').addEventListener('click', function() {
            const currentSize = parseInt(getComputedStyle(document.documentElement).fontSize);
            const newSize = Math.max(12, currentSize - 2);
            document.documentElement.style.fontSize = newSize + 'px';
            announceToScreenReader('Font size decreased');
        });
    </script>
</body>
</html>
EOF

# Create README for demo media
cat > /home/devinecr/devinecreations.net/softhub/softnode/demo/media/README.txt << 'EOF'
Demo Media Files Directory
=========================

This directory should contain sample audio files for the demo version:

Required files:
- interface-demo.mp3 (3-minute accessibility guide)
- sample-music.mp3 (sample music track)
- podcast-sample.mp3 (podcast episode sample)

File requirements:
- High quality audio (128kbps or higher)
- Properly tagged with metadata
- Clear audio without background noise
- Copyright-free or licensed for use
- Accessible content (clear speech, no rapid changes)

To add files:
1. Upload audio files to this directory
2. Ensure proper file permissions (644)
3. Test playback in the demo interface

Note: These files will be publicly accessible at:
https://devinecreations.net/softhub/softnode/demo/media/
EOF

log "? Demo files created"

# =============================================================================
# STEP 9: Install Dependencies and Set Permissions
# =============================================================================
log "?? Installing backend dependencies..."

cd /home/devinecr/apps/hubnode/clients/softnode-media-player
npm install

log "?? Setting file permissions..."

# Backend permissions
find /home/devinecr/apps/hubnode/clients/softnode-media-player -type d -exec chmod 755 {} \;
find /home/devinecr/apps/hubnode/clients/softnode-media-player -type f -exec chmod 644 {} \;

# Frontend permissions
find /home/devinecr/devinecreations.net/softhub/softnode -type d -exec chmod 755 {} \;
find /home/devinecr/devinecreations.net/softhub/softnode -type f -exec chmod 644 {} \;

# Media directories need write access
chmod 775 /home/devinecr/devinecreations.net/softhub/softnode/public/media
chmod 775 /home/devinecr/devinecreations.net/softhub/softnode/demo/media

# Secure environment file
chmod 600 /home/devinecr/apps/hubnode/clients/softnode-media-player/.env

log "? Permissions set correctly"

# =============================================================================
# STEP 10: Create System Service and Utilities
# =============================================================================
log "?? Creating system service and utility scripts..."

# Create systemd service
sudo tee /etc/systemd/system/softnode-media-player.service > /dev/null << 'EOF'
[Unit]
Description=Softnode Media Player Backend
After=network.target mysql.service

[Service]
Type=simple
User=devinecr
WorkingDirectory=/home/devinecr/apps/hubnode/clients/softnode-media-player
ExecStart=/usr/bin/node app.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production
EnvironmentFile=/home/devinecr/apps/hubnode/clients/softnode-media-player/.env

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/devinecr/devinecreations.net/softhub/softnode/public/media

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/softnode
sudo chown devinecr:devinecr /var/log/softnode

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable softnode-media-player

# Create utility scripts
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/start.sh << 'EOF'
#!/bin/bash
echo "Starting Softnode Media Player..."
sudo systemctl start softnode-media-player
sudo systemctl status softnode-media-player --no-pager
EOF

cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/stop.sh << 'EOF'
#!/bin/bash
echo "Stopping Softnode Media Player..."
sudo systemctl stop softnode-media-player
echo "Service stopped."
EOF

cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/restart.sh << 'EOF'
#!/bin/bash
echo "Restarting Softnode Media Player..."
sudo systemctl restart softnode-media-player
sudo systemctl status softnode-media-player --no-pager
EOF

cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/status.sh << 'EOF'
#!/bin/bash
echo "Softnode Media Player Status:"
echo "============================="
sudo systemctl status softnode-media-player --no-pager
echo ""
echo "API Health Check:"
curl -s http://localhost:3001/health 2>/dev/null || echo "API not responding"
echo ""
echo "Process Info:"
ps aux | grep "node app.js" | grep -v grep || echo "Process not found"
echo ""
echo "Log Files:"
ls -la /var/log/softnode/ 2>/dev/null || echo "No log files found"
EOF

cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/logs.sh << 'EOF'
#!/bin/bash
echo "Viewing Softnode Media Player logs..."
echo "Press Ctrl+C to exit"
echo "=========================="
sudo journalctl -u softnode-media-player -f
EOF

# Make scripts executable
chmod +x /home/devinecr/apps/hubnode/clients/softnode-media-player/*.sh

log "? System service and utilities created"

# =============================================================================
# STEP 11: Database Setup
# =============================================================================
log "??? Setting up database..."

# Create database setup script
cat > /home/devinecr/apps/hubnode/clients/softnode-media-player/setup-database.sh << 'EOF'
#!/bin/bash
echo "Setting up Softnode Media Player database..."

# Test database connection first
mysql -h localhost -u devinecr_devinecrsofthub -p'softnodeapp$' -e "USE devinecr_softnodeapp; SELECT 1;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "? Database connection successful"
    
    # Run the application to create tables
    echo "Starting application to initialize database tables..."
    cd /home/devinecr/apps/hubnode/clients/softnode-media-player
    timeout 10s node app.js &
    
    # Wait for initialization
    sleep 5
    
    # Stop the process
    pkill -f "node app.js"
    
    echo "? Database tables initialized"
    
    # Verify tables were created
    echo "Verifying database tables..."
    mysql -h localhost -u devinecr_devinecrsofthub -p'softnodeapp$' -e "USE devinecr_softnodeapp; SHOW TABLES;"
    
else
    echo "? Database connection failed"
    echo "Please check your database credentials in the .env file"
    exit 1
fi
EOF

chmod +x /home/devinecr/apps/hubnode/clients/softnode-media-player/setup-database.sh

# Run database setup
./setup-database.sh

log "? Database setup completed"

# =============================================================================
# STEP 12: Start and Test Services
# =============================================================================
log "?? Starting and testing services..."

cd /home/devinecr/apps/hubnode/clients/softnode-media-player

# Start the service
./start.sh

# Wait for startup
sleep 3

# Test the service
echo "Testing API endpoints..."
curl -s http://localhost:3001/health | head -n 10
echo ""

# Check service status
./status.sh

log "? Services started and tested"

# =============================================================================
# FINAL SUMMARY AND INSTRUCTIONS
# =============================================================================
log ""
log "?? Softnode Media Player Installation Complete!"
log "=============================================="
log ""
log "?? Installation Summary:"
log "  ? Directory structure created"
log "  ? Backend application installed"
log "  ? Frontend files created"
log "  ? Demo version set up"
log "  ? Database configured"
log "  ? System service created"
log "  ? Permissions set correctly"
log ""
log "?? File Locations:"
log "  Backend:  /home/devinecr/apps/hubnode/clients/softnode-media-player/"
log "  Frontend: /home/devinecr/devinecreations.net/softhub/softnode/"
log "  Demo:     /home/devinecr/devinecreations.net/softhub/softnode/demo/"
log "  Logs:     /var/log/softnode/"
log ""
log "?? URLs (after nginx configuration):"
log "  Main App: https://devinecreations.net/softhub/softnode/"
log "  Demo:     https://devinecreations.net/softhub/softnode/demo/"
log "  API:      https://devinecreations.net/softhub/softnode/api/health"
log ""
log "?? Management Commands:"
log "  Start:    cd /home/devinecr/apps/hubnode/clients/softnode-media-player && ./start.sh"
log "  Stop:     cd /home/devinecr/apps/hubnode/clients/softnode-media-player && ./stop.sh"
log "  Restart:  cd /home/devinecr/apps/hubnode/clients/softnode-media-player && ./restart.sh"
log "  Status:   cd /home/devinecr/apps/hubnode/clients/softnode-media-player && ./status.sh"
log "  Logs:     cd /home/devinecr/apps/hubnode/clients/softnode-media-player && ./logs.sh"
log ""
log "??? Database Information:"
log "  Host:     localhost"
log "  Database: devinecr_softnodeapp"
log "  User:     devinecr_devinecrsofthub"
log "  Tables:   media_items, user_playlists, playlist_items, user_activity, user_profiles"
log ""
log "??  Next Steps Required:"
log "  1. Apply the nginx configuration provided earlier"
log "  2. Add sample audio files to /home/devinecr/devinecreations.net/softhub/softnode/demo/media/"
log "  3. Test the URLs in your browser"
log "  4. Review and adjust the .env file if needed"
log ""
log "?? Support:"
log "  Check logs: sudo journalctl -u softnode-media-player -f"
log "  API test:   curl http://localhost:3001/health"
log ""
log "Installation completed successfully! ??"