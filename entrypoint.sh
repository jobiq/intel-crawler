#!/bin/bash
# Start Xvfb in background
Xvfb :99 -screen 0 1920x1080x24 &
exec uvicorn main:app --host 0.0.0.0 --port 3000
