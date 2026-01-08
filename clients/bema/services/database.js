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
