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
