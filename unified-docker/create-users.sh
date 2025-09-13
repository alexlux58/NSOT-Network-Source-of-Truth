#!/usr/bin/env bash
set -euo pipefail

# Run from this script's dir to ensure docker compose context is correct.
cd "$(dirname "$0")"

# Ensure docker compose is available
if ! command -v docker &>/dev/null || ! docker compose version &>/dev/null; then
  echo "❌ docker compose is required. Please install Docker Desktop or Docker Engine with Compose V2."
  exit 1
fi

read -rp "Which service? (netbox/nautobot/both): " SERVICE
SERVICE="${SERVICE,,}"  # lowercase

read -rp "Enter username: " USERNAME
read -rp "Enter email: " EMAIL
read -s -rp "Enter password: " PASSWORD
echo ""

if [[ -z "${USERNAME}" || -z "${EMAIL}" || -z "${PASSWORD}" ]]; then
  echo "❌ username, email, and password are required."
  exit 1
fi

exists_netbox() {
  echo "🔎 Checking NetBox for existing user '${USERNAME}'..."
  OUT="$(docker compose run --rm -e USERNAME="$USERNAME" netbox bash -lc '
python3 - <<PY
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netbox.configuration")
django.setup()
from django.contrib.auth import get_user_model
u = os.environ.get("USERNAME","")
sys.stdout.write("1" if get_user_model().objects.filter(username=u).exists() else "0")
PY
  ' 2>/dev/null || true)"
  [[ "$OUT" == "1" ]]
}

create_netbox() {
  echo "👤 Creating NetBox superuser '${USERNAME}'..."
  docker compose run --rm \
    -e DJANGO_SUPERUSER_USERNAME="$USERNAME" \
    -e DJANGO_SUPERUSER_EMAIL="$EMAIL" \
    -e DJANGO_SUPERUSER_PASSWORD="$PASSWORD" \
    netbox python3 manage.py createsuperuser --noinput
  echo "✅ NetBox superuser created (or already present)."
}

exists_nautobot() {
  echo "🔎 Checking Nautobot for existing user '${USERNAME}'..."
  OUT="$(docker compose run --rm -e USERNAME="$USERNAME" nautobot bash -lc '
python3 - <<PY
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nautobot.core.settings")
django.setup()
from django.contrib.auth import get_user_model
u = os.environ.get("USERNAME","")
sys.stdout.write("1" if get_user_model().objects.filter(username=u).exists() else "0")
PY
  ' 2>/dev/null || true)"
  [[ "$OUT" == "1" ]]
}

create_nautobot() {
  echo "👤 Creating Nautobot superuser '${USERNAME}'..."
  docker compose run --rm \
    -e DJANGO_SUPERUSER_USERNAME="$USERNAME" \
    -e DJANGO_SUPERUSER_EMAIL="$EMAIL" \
    -e DJANGO_SUPERUSER_PASSWORD="$PASSWORD" \
    nautobot nautobot-server createsuperuser --noinput
  echo "✅ Nautobot superuser created (or already present)."
}

case "$SERVICE" in
  netbox)
    if exists_netbox; then
      echo "ℹ️ NetBox user '${USERNAME}' already exists — skipping creation."
    else
      create_netbox
    fi
    ;;
  nautobot)
    if exists_nautobot; then
      echo "ℹ️ Nautobot user '${USERNAME}' already exists — skipping creation."
    else
      create_nautobot
    fi
    ;;
  both)
    if exists_netbox; then
      echo "ℹ️ NetBox user '${USERNAME}' already exists — skipping creation."
    else
      create_netbox
    fi

    if exists_nautobot; then
      echo "ℹ️ Nautobot user '${USERNAME}' already exists — skipping creation."
    else
      create_nautobot
    fi
    ;;
  *)
    echo "❌ Invalid choice: $SERVICE (use netbox/nautobot/both)"
    exit 1
    ;;
esac

echo "🎉 Done!"
