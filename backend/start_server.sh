#!/bin/bash

# Start the FastAPI backend server
# This script ensures the server is accessible from other devices on the network

echo "Starting Slop Backend Server..."
echo "Server will be accessible at:"
echo "  - Local: http://localhost:8000"
echo "  - Network: http://$(hostname -I | awk '{print $1}'):8000"
echo ""

# Activate virtual environment if it exists
if [ -f "pyvenv.cfg" ]; then
    echo "Activating virtual environment..."
    source bin/activate
fi

# Start the server
echo "Starting uvicorn server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 