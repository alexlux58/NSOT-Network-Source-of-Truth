#!/bin/bash

# Start Nornir Automation Service
# This script sets up and starts the Nornir automation service

set -e

echo "Starting Nornir Automation Service..."

# Create necessary directories
mkdir -p nornir-automation/{inventory,configs,reports,logs}

# Set permissions
chmod +x nornir-automation/scripts/*.py

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Nornir automation image
echo "Building Nornir automation image..."
docker build -f Dockerfile.nornir -t nornir-automation .

# Start the service
echo "Starting Nornir automation service..."
docker compose up -d nornir-automation

# Wait for service to be ready
echo "Waiting for service to be ready..."
sleep 10

# Check if service is running
if docker compose ps nornir-automation | grep -q "Up"; then
    echo "✅ Nornir automation service is running!"
    echo "🌐 Web interface: http://localhost:8082"
    echo "📚 API documentation: http://localhost:8082/api/docs/"
    echo ""
    echo "To view logs: docker compose logs -f nornir-automation"
    echo "To stop: docker compose down nornir-automation"
else
    echo "❌ Failed to start Nornir automation service"
    echo "Check logs: docker compose logs nornir-automation"
    exit 1
fi

