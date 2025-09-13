#!/bin/bash

# Nautobot Initialization Helper Script
# This script runs the first-time setup for Nautobot

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

COMPOSE_CMD="docker compose"
if ! $COMPOSE_CMD version >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    echo "❌ Neither 'docker compose' nor 'docker-compose' found."
    exit 1
  fi
fi

echo "🔧 Initializing Nautobot for first-time setup..."

# Start databases first
echo "📦 Starting databases..."
$COMPOSE_CMD up -d nautobot-postgres nautobot-redis

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Fix media/static ownership
echo "🔧 Setting up media/static directories..."
$COMPOSE_CMD run --rm -u 0 nautobot bash -lc \
  'mkdir -p /opt/nautobot/media/devicetype-images /opt/nautobot/static && chown -R nautobot:nautobot /opt/nautobot'

# Run migrations
echo "🗃️ Running database migrations..."
$COMPOSE_CMD run --rm nautobot nautobot-server migrate

# Collect static files
echo "🖼️ Collecting static files..."
$COMPOSE_CMD run --rm nautobot nautobot-server collectstatic --noinput

# Create superuser
echo "👤 Creating superuser..."
$COMPOSE_CMD run --rm nautobot nautobot-server createsuperuser

echo "✅ Nautobot initialization complete!"
echo ""
echo "🚀 You can now run ./start.sh to start all services"
