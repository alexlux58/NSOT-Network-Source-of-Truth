#!/bin/bash

# Unified NetBox and Nautobot Startup Script

echo "🚀 Starting Unified NetBox and Nautobot Setup..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

# Use docker compose (newer) or docker-compose (legacy)
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Neither 'docker compose' nor 'docker-compose' is available"
    exit 1
fi

echo "📦 Building and starting services..."
export COMPOSE_PROJECT_NAME=unified-docker
$COMPOSE_CMD up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   NetBox:  http://localhost:8080"
    echo "   Nautobot: http://localhost:8081"
    echo ""
    echo "📊 To view logs: $COMPOSE_CMD logs -f"
    echo "🛑 To stop: $COMPOSE_CMD down"
    echo ""
    echo "⏳ Services are starting up... This may take a few minutes."
    echo "   Check the logs above for startup progress."
else
    echo ""
    echo "❌ Failed to start services. Check the output above for errors."
    exit 1
fi
