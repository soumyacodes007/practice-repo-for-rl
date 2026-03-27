#!/bin/bash
# Quick start script for LLM Text2SQL Failure Gym

echo "=========================================="
echo "LLM Text2SQL Failure Gym - Quick Start"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q openenv-core fastapi uvicorn requests

# Start server in background
echo ""
echo "Starting server..."
uvicorn server.app:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Run validation
echo ""
python validate.py --url http://localhost:8000

# Keep server running or kill it
echo ""
read -p "Keep server running? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Stopping server..."
    kill $SERVER_PID
else
    echo "Server running at http://localhost:8000"
    echo "Press Ctrl+C to stop"
    wait $SERVER_PID
fi
