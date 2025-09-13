#!/usr/bin/env bash
set -euo pipefail

# Test Nautobot Environment Variables
cd "$(dirname "$0")"

echo "🧪 Testing Nautobot Environment Variables..."

# Check for help flag
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat << 'EOF'
Nautobot Environment Test Script

USAGE:
    ./test-nautobot-env.sh

DESCRIPTION:
    Tests that Nautobot environment variables are properly configured
    and accessible within the Nautobot container.

TESTS:
    - Database connection variables
    - Redis connection variables
    - Nautobot-specific settings

EXAMPLES:
    ./test-nautobot-env.sh        # Run all tests
    ./test-nautobot-env.sh --help # Show this help

NOTES:
    - Requires Nautobot container to be running
    - Shows environment variables as seen by Nautobot
EOF
      exit 0
      ;;
  esac
done

echo "🔍 Checking Nautobot environment variables..."

# Test database environment variables
echo "📊 Database Configuration:"
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_DB_HOST: $NAUTOBOT_DB_HOST"'
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_DB_NAME: $NAUTOBOT_DB_NAME"'
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_DB_USER: $NAUTOBOT_DB_USER"'
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_DB_PORT: $NAUTOBOT_DB_PORT"'

echo ""
echo "🔴 Redis Configuration:"
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_REDIS_HOST: $NAUTOBOT_REDIS_HOST"'
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_REDIS_PORT: $NAUTOBOT_REDIS_PORT"'

echo ""
echo "⚙️  Nautobot Settings:"
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_ALLOWED_HOSTS: $NAUTOBOT_ALLOWED_HOSTS"'
docker compose run --rm nautobot bash -c 'echo "NAUTOBOT_DEBUG: $NAUTOBOT_DEBUG"'

echo ""
echo "✅ Environment variable test complete!"
