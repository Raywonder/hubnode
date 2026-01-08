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
