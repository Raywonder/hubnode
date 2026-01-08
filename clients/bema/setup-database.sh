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
