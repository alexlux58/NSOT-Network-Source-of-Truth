#!/usr/bin/env bash
set -euo pipefail

# Verify Setup Script
# Checks that both NetBox and Nautobot are running correctly

cd "$(dirname "$0")"

# Check for help flag
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      cat << 'EOF'
Setup Verification Script

USAGE:
    ./verify-setup.sh

DESCRIPTION:
    Verifies that both NetBox and Nautobot are running correctly
    and accessible. Performs comprehensive health checks.

CHECKS:
    - Container status and health
    - Database connectivity
    - Web interface accessibility
    - Environment variables

EXAMPLES:
    ./verify-setup.sh        # Run all verification checks
    ./verify-setup.sh --help # Show this help

NOTES:
    - Requires services to be running
    - Provides detailed status report
    - Suggests fixes for common issues
EOF
      exit 0
      ;;
  esac
done

echo "🔍 Verifying Unified NetBox and Nautobot Setup..."
echo ""

# Check if docker compose is available
if ! command -v docker &>/dev/null || ! docker compose version &>/dev/null; then
  echo "❌ Docker Compose is not available"
  exit 1
fi

# Check container status
echo "📊 Container Status:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Health Checks:"

# Check NetBox
echo "  NetBox:"
if docker compose ps netbox | grep -q "healthy"; then
  echo "    ✅ NetBox is healthy"
else
  echo "    ❌ NetBox is not healthy"
  echo "    💡 Try: docker compose logs netbox"
fi

# Check Nautobot
echo "  Nautobot:"
if docker compose ps nautobot | grep -q "healthy"; then
  echo "    ✅ Nautobot is healthy"
else
  echo "    ❌ Nautobot is not healthy"
  echo "    💡 Try: docker compose logs nautobot"
fi

echo ""
echo "🗄️  Database Connectivity:"

# Test database connections
if ./test-db-connections.sh >/dev/null 2>&1; then
  echo "  ✅ All database connections successful"
else
  echo "  ❌ Database connection issues detected"
  echo "  💡 Run: ./test-db-connections.sh for details"
fi

echo ""
echo "🌐 Web Interface Accessibility:"

# Check NetBox
if curl -s -f http://localhost:8080/login/ >/dev/null 2>&1; then
  echo "  ✅ NetBox web interface accessible at http://192.168.5.9:8080"
else
  echo "  ❌ NetBox web interface not accessible"
  echo "  💡 Check if NetBox container is running and healthy"
fi

# Check Nautobot
if curl -s -f http://localhost:8081/ >/dev/null 2>&1; then
  echo "  ✅ Nautobot web interface accessible at http://192.168.5.9:8081"
else
  echo "  ❌ Nautobot web interface not accessible"
  echo "  💡 Check if Nautobot container is running and healthy"
fi

echo ""
echo "⚙️  Environment Configuration:"

# Test Nautobot environment
if ./test-nautobot-env.sh >/dev/null 2>&1; then
  echo "  ✅ Nautobot environment variables configured correctly"
else
  echo "  ❌ Nautobot environment configuration issues"
  echo "  💡 Run: ./test-nautobot-env.sh for details"
fi

echo ""
echo "📋 Summary:"

# Count healthy services
HEALTHY_COUNT=$(docker compose ps --format "{{.Status}}" | grep -c "healthy" || true)
TOTAL_COUNT=$(docker compose ps --format "{{.Name}}" | wc -l)

if [[ $HEALTHY_COUNT -eq $TOTAL_COUNT ]]; then
  echo "🎉 All services are running and healthy!"
  echo ""
  echo "🌐 Access URLs:"
  echo "   NetBox:   http://192.168.5.9:8080"
  echo "   Nautobot: http://192.168.5.9:8081"
  echo ""
  echo "📊 Monitor with:"
  echo "   docker compose logs -f"
else
  echo "⚠️  Some services are not healthy ($HEALTHY_COUNT/$TOTAL_COUNT)"
  echo ""
  echo "🔧 Troubleshooting:"
  echo "   ./cleanup.sh --db && ./start.sh --clean"
  echo "   docker compose logs [service-name]"
fi
