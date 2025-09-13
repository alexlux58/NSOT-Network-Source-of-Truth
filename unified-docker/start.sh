#!/usr/bin/env bash
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

CLEAN=0
for arg in "$@"; do
  case "$arg" in
    --clean) CLEAN=1 ;;
    -h|--help)
      cat << 'EOF'
Unified NetBox and Nautobot Startup Script

USAGE:
    ./start.sh [OPTIONS]

OPTIONS:
    --clean    Remove conflicting containers before starting
    -h, --help Show this help message

DESCRIPTION:
    Starts both NetBox and Nautobot with proper database wait logic
    and automatic initialization. Includes database migrations,
    static file collection, and superuser creation.

EXAMPLES:
    ./start.sh              # Regular start
    ./start.sh --clean      # Clean start (removes conflicts)

ACCESS:
    NetBox:   http://192.168.5.9:8080
    Nautobot: http://192.168.5.9:8081
EOF
      exit 0
      ;;
    *) echo "Unknown arg: $arg"; exit 1 ;;
  esac
done

echo "🚀 Starting Unified NetBox and Nautobot Setup..."
echo ""

# Optional clean-up to avoid container name collisions with other stacks
if (( CLEAN )); then
  echo "🧹 --clean requested: removing old standalone containers named 'netbox' or 'nautobot' (if any)"
  docker rm -f netbox >/dev/null 2>&1 || true
  docker rm -f nautobot >/dev/null 2>&1 || true
fi

echo "📦 Building and starting services..."
export COMPOSE_PROJECT_NAME=unified-docker
$COMPOSE_CMD up -d --build

echo ""
echo "⏳ Waiting for databases & redis to come up..."

# Wait for NetBox PostgreSQL
echo "🔍 Waiting for NetBox PostgreSQL..."
timeout 30 bash -c 'until docker compose exec netbox-postgres pg_isready -q -t 2 -d netbox -U netbox; do sleep 1; done' || {
  echo "❌ NetBox PostgreSQL not ready after 30s"
  exit 1
}

# Wait for Nautobot PostgreSQL  
echo "🔍 Waiting for Nautobot PostgreSQL..."
timeout 30 bash -c 'until docker compose exec nautobot-postgres pg_isready -q -t 2 -d nautobot -U nautobot; do sleep 1; done' || {
  echo "❌ Nautobot PostgreSQL not ready after 30s"
  exit 1
}

echo "✅ All databases are ready"

# Ensure Nautobot media/static dir ownership inside container (idempotent)
echo "🔧 Fixing Nautobot media/static ownership..."
$COMPOSE_CMD run --rm -u 0 nautobot bash -lc 'mkdir -p /opt/nautobot/media/devicetype-images /opt/nautobot/static && chown -R nautobot:nautobot /opt/nautobot'

# Run idempotent migrations & collectstatic for Nautobot
echo "🗃️ Running Nautobot migrations..."
$COMPOSE_CMD run --rm nautobot nautobot-server migrate

echo "🖼️ Collecting Nautobot static files..."
$COMPOSE_CMD run --rm nautobot nautobot-server collectstatic --noinput

# Create superuser only if missing and password provided
echo "👤 Ensuring Nautobot superuser exists (if configured)..."
NA_USER="${NAUTOBOT_SUPERUSER_NAME:-}"
NA_EMAIL="${NAUTOBOT_SUPERUSER_EMAIL:-}"
NA_PASS="${NAUTOBOT_SUPERUSER_PASSWORD:-}"

# Read from env file if not in shell env
if [[ -z "${NA_USER}" || -z "${NA_EMAIL}" ]]; then
  # shellcheck disable=SC1091
  source ./env/nautobot.env || true
  NA_USER="${NA_USER:-${NAUTOBOT_SUPERUSER_NAME:-}}"
  NA_EMAIL="${NA_EMAIL:-${NAUTOBOT_SUPERUSER_EMAIL:-}}"
  NA_PASS="${NA_PASS:-${NAUTOBOT_SUPERUSER_PASSWORD:-}}"
fi

if [[ -n "$NA_USER" && -n "$NA_EMAIL" ]]; then
  echo "🔎 Checking for user '$NA_USER'..."
  set +e
  $COMPOSE_CMD run --rm nautobot bash -lc "nautobot-server shell -c \"from users.models import User; import os,sys; sys.exit(0 if User.objects.filter(username='$NA_USER').exists() else 1)\""
  EXISTS=$?
  set -e
  if [[ $EXISTS -ne 0 ]]; then
    if [[ -n "$NA_PASS" ]]; then
      echo "➕ Creating superuser '$NA_USER'..."
      $COMPOSE_CMD run --rm -e DJANGO_SUPERUSER_USERNAME="$NA_USER" \
                             -e DJANGO_SUPERUSER_EMAIL="$NA_EMAIL" \
                             -e DJANGO_SUPERUSER_PASSWORD="$NA_PASS" \
                             nautobot nautobot-server createsuperuser --noinput || true
    else
      echo "⚠️ Superuser '$NA_USER' does not exist and no password provided. Skipping auto-create."
      echo "   You can run: $COMPOSE_CMD run --rm nautobot nautobot-server createsuperuser"
    fi
  else
    echo "✅ Superuser '$NA_USER' already exists."
  fi
else
  echo "ℹ️ Superuser auto-create not configured (missing NAUTOBOT_SUPERUSER_* in env)."
fi

# Finally ensure all long-lived services are up
echo ""
$COMPOSE_CMD up -d

echo ""
echo "✅ Services started!"
echo ""
echo "🌐 Access URLs:"
echo "   NetBox:   http://192.168.5.9:8080"
echo "   Nautobot: http://192.168.5.9:8081"
echo ""
echo "📊 Logs (follow one):"
echo "   $COMPOSE_CMD logs -f netbox"
echo "   $COMPOSE_CMD logs -f nautobot"
echo ""
echo "🛑 Stop:"
echo "   $COMPOSE_CMD down"
echo ""
echo "🧪 Healthcheck tips:"
echo "   docker ps --format '{{.Names}}: {{.Status}}'"
echo "   $COMPOSE_CMD logs -f nautobot"
echo "   $COMPOSE_CMD logs -f netbox"
echo ""