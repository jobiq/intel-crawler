#!/bin/bash
# Start Xvfb in background
Xvfb :99 -screen 0 1920x1080x24 &

# 1. Build Container wither with server
# exec uvicorn main:app --host 0.0.0.0 --port 3000 // If you want to run uvicorn, uncomment this line and comment all below

# 2. Or with scraping
# Wait a moment for Xvfb to start
sleep 1

# Execute the passed command
exec "$@"
