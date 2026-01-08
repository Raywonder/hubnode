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
