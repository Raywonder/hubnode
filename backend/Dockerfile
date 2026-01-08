FROM python:3.9-slim

WORKDIR /app

# Install CopyParty
RUN pip install copyparty

# Copy configuration
COPY copyparty-sfx.py .
COPY start-copyparty.sh .
COPY copyparty-config.py .

# Create directories
RUN mkdir -p uploads downloads temp logs data

# Expose port
EXPOSE 3923

# Start CopyParty
CMD ["./start-copyparty.sh"]
