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
