#!/usr/bin/env bash
set -euo pipefail

# Nuclear Docker Cleanup Script
# WARNING: This will remove ALL Docker containers, images, volumes, and networks
# Use this when you want to completely reset your Docker environment

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  NUCLEAR DOCKER CLEANUP ⚠️${NC}"
echo ""
echo "This script will perform a COMPLETE cleanup of your Docker environment:"
echo "  • Stop ALL running containers"
echo "  • Remove ALL containers (running and stopped)"
echo "  • Remove ALL images"
echo "  • Remove ALL unused volumes"
echo "  • Remove ALL unused networks"
echo "  • Remove ALL build cache"
echo ""
echo -e "${YELLOW}WARNING: This will delete EVERYTHING in Docker!${NC}"
echo ""

# Confirmation prompt
read -p "Are you absolutely sure you want to proceed? Type 'YES' to continue: " confirm
if [[ "$confirm" != "YES" ]]; then
    echo "❌ Aborted. No changes made."
    exit 0
fi

echo ""
echo "🚀 Starting nuclear cleanup..."

# Function to run command with error handling
run_cmd() {
    local cmd="$1"
    local description="$2"
    
    echo "🔧 $description..."
    if eval "$cmd" 2>/dev/null; then
        echo -e "✅ $description completed"
    else
        echo -e "⚠️  $description completed (some items may not have existed)"
    fi
}

# Stop all containers
run_cmd "docker stop \$(docker ps -aq) 2>/dev/null || true" "Stopping all containers"

# Remove all containers
run_cmd "docker rm \$(docker ps -aq) 2>/dev/null || true" "Removing all containers"

# Remove all images
run_cmd "docker rmi \$(docker images -aq) 2>/dev/null || true" "Removing all images"

# Remove unused volumes
run_cmd "docker volume prune -f" "Removing unused volumes"

# Remove unused networks
run_cmd "docker network prune -f" "Removing unused networks"

# Complete system cleanup
run_cmd "docker system prune -a -f --volumes" "Complete system cleanup"

echo ""
echo -e "${GREEN}🎉 Nuclear cleanup completed!${NC}"
echo ""
echo "Your Docker environment has been completely reset."
echo "All containers, images, volumes, and networks have been removed."
echo ""
echo "To start fresh with the unified setup:"
echo "  ./start.sh --clean"
echo ""
echo "Or to start individual services:"
echo "  cd ../netbox-docker && docker compose up -d"
echo "  cd ../nautobot-docker && docker compose up -d"
