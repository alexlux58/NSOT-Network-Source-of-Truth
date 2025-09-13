#!/usr/bin/env bash
set -euo pipefail

# Fix Nautobot Migration Script
# Resolves the tenancy.0003_mptt_to_tree_queries migration conflict

cd "$(dirname "$0")"

# Check for help flag
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat << 'EOF'
Nautobot Migration Fix Script

USAGE:
    ./fix-nautobot-migration.sh

DESCRIPTION:
    Fixes the Nautobot migration conflict where tenancy.0003_mptt_to_tree_queries
    tries to drop a non-existent 'level' column on fresh installations.

PROBLEM:
    Nautobot 2.3 has a migration ordering issue where:
    - Migration 0001 creates TenantGroup without MPTT fields (level, lft, rght)
    - Migration 0003 tries to drop those same fields (for upgrade scenarios)
    - On fresh DBs, the fields don't exist, causing the migration to fail

SOLUTION:
    - Fakes the problematic migration (marks it as applied without running it)
    - Runs remaining migrations normally
    - This is safe because the intended end state is already achieved

EXAMPLES:
    ./fix-nautobot-migration.sh        # Fix the migration issue
    ./fix-nautobot-migration.sh --help # Show this help

NOTES:
    - Requires Nautobot containers to be running
    - Safe for fresh installations (no data loss)
    - Fixes the "column level does not exist" error
EOF
      exit 0
      ;;
  esac
done

echo "🔧 Fixing Nautobot Migration Conflict..."
echo ""

# Check if docker compose is available
if ! command -v docker &>/dev/null || ! docker compose version &>/dev/null; then
  echo "❌ Docker Compose is not available"
  exit 1
fi

# Check if Nautobot container is running
if ! docker compose ps nautobot | grep -q "Up"; then
  echo "❌ Nautobot container is not running"
  echo "💡 Start the services first: ./start.sh"
  exit 1
fi

echo "🔍 Current migration status:"
docker compose run --rm nautobot nautobot-server showmigrations tenancy

echo ""
echo "🔧 Applying migration fix..."

# Step 1: Fake the problematic migration
echo "1️⃣ Faking migration tenancy.0003_mptt_to_tree_queries..."
if docker compose run --rm nautobot nautobot-server migrate tenancy 0003_mptt_to_tree_queries --fake; then
  echo "✅ Successfully faked migration 0003"
else
  echo "❌ Failed to fake migration 0003"
  echo "💡 Check the error above and try again"
  exit 1
fi

# Step 2: Run remaining migrations
echo ""
echo "2️⃣ Running remaining migrations..."
if docker compose run --rm nautobot nautobot-server migrate; then
  echo "✅ Successfully applied remaining migrations"
else
  echo "❌ Failed to apply remaining migrations"
  echo "💡 Check the error above and try again"
  exit 1
fi

echo ""
echo "🔍 Final migration status:"
docker compose run --rm nautobot nautobot-server showmigrations tenancy

echo ""
echo "✅ Migration fix complete!"
echo ""
echo "🔄 Restarting Nautobot services..."
docker compose restart nautobot nautobot-worker nautobot-beat

echo ""
echo "⏳ Waiting for Nautobot to become healthy..."
sleep 10

# Check if Nautobot is now healthy
if docker compose ps nautobot | grep -q "healthy"; then
  echo "🎉 Nautobot is now healthy!"
  echo ""
  echo "🌐 Access Nautobot at: http://192.168.5.9:8081"
  echo "🌐 Access NetBox at: http://192.168.5.9:8080"
  echo ""
  echo "✅ You can now run: ./verify-setup.sh"
else
  echo "⚠️  Nautobot is still not healthy"
  echo "💡 Check logs: docker compose logs nautobot"
  echo "💡 Run verification: ./verify-setup.sh"
fi
