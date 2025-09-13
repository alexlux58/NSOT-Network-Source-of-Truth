#!/usr/bin/env bash
set -euo pipefail

# Test database connections for both NetBox and Nautobot
cd "$(dirname "$0")"

echo "🧪 Testing database connections..."

# Test NetBox PostgreSQL connection
echo "🔍 Testing NetBox PostgreSQL connection..."
if docker compose exec netbox-postgres pg_isready -q -t 2 -d netbox -U netbox; then
  echo "✅ NetBox PostgreSQL: Connected"
else
  echo "❌ NetBox PostgreSQL: Connection failed"
  exit 1
fi

# Test Nautobot PostgreSQL connection
echo "🔍 Testing Nautobot PostgreSQL connection..."
if docker compose exec nautobot-postgres pg_isready -q -t 2 -d nautobot -U nautobot; then
  echo "✅ Nautobot PostgreSQL: Connected"
else
  echo "❌ Nautobot PostgreSQL: Connection failed"
  exit 1
fi

# Test NetBox Django database connection
echo "🔍 Testing NetBox Django database connection..."
if docker compose run --rm netbox python3 manage.py check --database default; then
  echo "✅ NetBox Django: Database accessible"
else
  echo "❌ NetBox Django: Database connection failed"
  exit 1
fi

# Test Nautobot Django database connection
echo "🔍 Testing Nautobot Django database connection..."
if docker compose run --rm nautobot nautobot-server check --database default; then
  echo "✅ Nautobot Django: Database accessible"
else
  echo "❌ Nautobot Django: Database connection failed"
  exit 1
fi

echo "🎉 All database connections successful!"
